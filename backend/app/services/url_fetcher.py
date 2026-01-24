"""
URL 콘텐츠 가져오기 서비스

Unix Philosophy:
- Modularity: URL 콘텐츠 가져오기만 담당
- Separation: HTTP 요청 로직 분리
"""

from __future__ import annotations

import logging
import re
from typing import Optional
from urllib.parse import urlparse

import httpx
import trafilatura

from app.services.og_metadata import OGMetadata, extract_og_metadata

logger = logging.getLogger(__name__)

# 직접 접근 불가능한 도메인 (별도 스크래퍼 사용)
INACCESSIBLE_DOMAINS: frozenset[str] = frozenset([
    "twitter.com",
    "x.com",
    "www.twitter.com",
    "www.x.com",
    "mobile.twitter.com",
    "mobile.x.com",
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
    "www.youtu.be",
])

# GitHub blob URL 패턴
GITHUB_BLOB_PATTERN = re.compile(
    r"^https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$"
)


def is_inaccessible_url(url: str) -> bool:
    """
    접근 불가능한 URL인지 확인

    Args:
        url: 확인할 URL

    Returns:
        접근 불가능하면 True
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return domain in INACCESSIBLE_DOMAINS
    except Exception:
        return False


def convert_github_to_raw(url: str) -> Optional[str]:
    """
    GitHub blob URL을 raw URL로 변환

    Args:
        url: GitHub blob URL

    Returns:
        raw.githubusercontent.com URL 또는 None
    """
    match = GITHUB_BLOB_PATTERN.match(url)
    if match:
        owner, repo, branch, path = match.groups()
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
        logger.info(f"GitHub URL 변환: {url} -> {raw_url}")
        return raw_url
    return None


def is_github_url(url: str) -> bool:
    """GitHub URL인지 확인"""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower() in ("github.com", "www.github.com")
    except Exception:
        return False


async def fetch_url_content(
    url: str,
    max_length: int = 10000,
) -> tuple[Optional[str], Optional[OGMetadata]]:
    """
    URL에서 콘텐츠와 OG 메타데이터 가져오기

    Args:
        url: 대상 URL
        max_length: 최대 콘텐츠 길이

    Returns:
        (추출된 텍스트 콘텐츠, OG 메타데이터) 튜플
    """
    # 접근 불가능한 URL 체크
    if is_inaccessible_url(url):
        logger.info(f"Inaccessible URL: {url}")
        return None, OGMetadata(
            fetch_failed=True,
            fetch_message="이 링크는 직접 접근이 불가능합니다. 내용을 복사해서 메모에 붙여넣어 주세요.",
        )

    # GitHub blob URL -> raw URL 변환
    fetch_url = url
    is_github_raw = False
    if is_github_url(url):
        raw_url = convert_github_to_raw(url)
        if raw_url:
            fetch_url = raw_url
            is_github_raw = True

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                fetch_url,
                headers={"User-Agent": "Mozilla/5.0 Zentel/1.0"},
                follow_redirects=True,
            )
            response.raise_for_status()

            html = response.text

            # OG 메타데이터 추출 (원본 URL에서)
            og_metadata = None
            if not is_github_raw:
                og_metadata = extract_og_metadata(html, url)
            else:
                # GitHub raw는 OG 메타데이터가 없으므로 원본 URL에서 가져옴
                try:
                    og_response = await client.get(
                        url,
                        headers={"User-Agent": "Mozilla/5.0 Zentel/1.0"},
                        follow_redirects=True,
                    )
                    if og_response.status_code == 200:
                        og_metadata = extract_og_metadata(og_response.text, url)
                except Exception as e:
                    logger.warning(f"GitHub OG 메타데이터 가져오기 실패: {e}")

            # 본문 추출
            if is_github_raw:
                # GitHub raw는 이미 텍스트이므로 그대로 사용
                content = html
            else:
                # trafilatura로 본문 추출
                content = trafilatura.extract(
                    html,
                    include_comments=False,
                    include_tables=True,
                    no_fallback=False,
                )

                # trafilatura 실패 시 fallback
                if not content:
                    logger.warning(f"trafilatura 추출 실패, fallback 사용: {url}")
                    # BeautifulSoup fallback
                    try:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(html, "html.parser")
                        # script, style 제거
                        for tag in soup(["script", "style", "nav", "footer", "header"]):
                            tag.decompose()
                        content = soup.get_text(separator="\n", strip=True)
                    except Exception:
                        # 최후의 수단: HTML 그대로
                        content = html

            # 콘텐츠 길이 제한
            if content and len(content) > max_length:
                content = content[:max_length] + "..."

            logger.info(
                f"URL 콘텐츠 가져옴: {url}, length={len(content) if content else 0}, "
                f"og_title={og_metadata.title if og_metadata else None}"
            )
            return content, og_metadata

    except Exception as e:
        logger.error(f"URL 콘텐츠 가져오기 실패: {url}, error={e}")
        return None, None

"""
URL 콘텐츠 가져오기 서비스

Unix Philosophy:
- Modularity: URL 콘텐츠 가져오기만 담당
- Separation: HTTP 요청 로직 분리
- Simplicity: 단순한 로직 유지
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

# GitHub blob URL 패턴 (JS 렌더링이라 raw URL 변환 필요)
GITHUB_BLOB_PATTERN = re.compile(
    r"^https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$"
)


def is_inaccessible_url(url: str) -> bool:
    """
    접근 불가능한 URL인지 확인 (Twitter, YouTube 등)
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return domain in INACCESSIBLE_DOMAINS
    except Exception:
        return False


def convert_github_blob_to_raw(url: str) -> Optional[str]:
    """
    GitHub blob URL을 raw URL로 변환
    (GitHub은 JS 렌더링이라 raw URL로 가져와야 함)

    github.com/user/repo/blob/branch/path
    → raw.githubusercontent.com/user/repo/branch/path
    """
    match = GITHUB_BLOB_PATTERN.match(url)
    if match:
        owner, repo, branch, path = match.groups()
        return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    return None


async def fetch_url_content(
    url: str,
    max_length: int = 10000,
) -> tuple[Optional[str], Optional[OGMetadata]]:
    """
    URL에서 콘텐츠와 OG 메타데이터 가져오기

    - Twitter/YouTube: 접근 불가 (별도 스크래퍼 사용)
    - GitHub blob: raw URL로 변환 후 텍스트 그대로 사용
    - 그 외: trafilatura로 본문 추출

    Args:
        url: 대상 URL
        max_length: 최대 콘텐츠 길이

    Returns:
        (추출된 텍스트 콘텐츠, OG 메타데이터) 튜플
    """
    # Twitter/YouTube는 별도 스크래퍼 사용
    if is_inaccessible_url(url):
        logger.info(f"Inaccessible URL (별도 스크래퍼 필요): {url}")
        return None, OGMetadata(
            fetch_failed=True,
            fetch_message="이 링크는 직접 접근이 불가능합니다. 내용을 복사해서 메모에 붙여넣어 주세요.",
        )

    # GitHub blob URL은 raw URL로 변환
    fetch_url = url
    is_raw_text = False
    github_raw_url = convert_github_blob_to_raw(url)
    if github_raw_url:
        fetch_url = github_raw_url
        is_raw_text = True
        logger.info(f"GitHub blob → raw 변환: {url} → {fetch_url}")

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                fetch_url,
                headers={"User-Agent": "Mozilla/5.0 Zentel/1.0"},
                follow_redirects=True,
            )
            response.raise_for_status()

            html = response.text

            # OG 메타데이터 (원본 URL에서 가져옴)
            og_metadata = None
            if is_raw_text:
                # raw URL은 OG 없으므로 원본에서 가져옴
                try:
                    og_resp = await client.get(url, follow_redirects=True)
                    if og_resp.status_code == 200:
                        og_metadata = extract_og_metadata(og_resp.text, url)
                except Exception as e:
                    logger.warning(f"OG 메타데이터 가져오기 실패: {e}")
            else:
                og_metadata = extract_og_metadata(html, url)

            # 본문 추출
            if is_raw_text:
                # raw 텍스트는 그대로 사용
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
                    try:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(html, "html.parser")
                        for tag in soup(["script", "style", "nav", "footer", "header"]):
                            tag.decompose()
                        content = soup.get_text(separator="\n", strip=True)
                    except Exception:
                        content = html

            # 콘텐츠 길이 제한
            if content and len(content) > max_length:
                content = content[:max_length] + "..."

            logger.info(
                f"URL 콘텐츠 추출 완료: {url}, "
                f"length={len(content) if content else 0}, "
                f"is_raw={is_raw_text}"
            )
            return content, og_metadata

    except Exception as e:
        logger.error(f"URL 콘텐츠 가져오기 실패: {url}, error={e}")
        return None, None

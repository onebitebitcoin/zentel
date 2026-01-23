"""
URL 콘텐츠 가져오기 서비스

Unix Philosophy:
- Modularity: URL 콘텐츠 가져오기만 담당
- Separation: HTTP 요청 로직 분리
"""

from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import urlparse

import httpx

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

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 Zentel/1.0"},
                follow_redirects=True,
            )
            response.raise_for_status()

            html = response.text

            # OG 메타데이터 추출
            og_metadata = extract_og_metadata(html, url)

            # 콘텐츠 길이 제한
            content = html
            if len(content) > max_length:
                content = content[:max_length] + "..."

            logger.info(
                f"URL 콘텐츠 가져옴: {url}, length={len(content)}, "
                f"og_title={og_metadata.title if og_metadata else None}"
            )
            return content, og_metadata

    except Exception as e:
        logger.error(f"URL 콘텐츠 가져오기 실패: {url}, error={e}")
        return None, None

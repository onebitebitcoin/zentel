"""
URL 콘텐츠 가져오기 서비스

Unix Philosophy:
- Modularity: URL 콘텐츠 가져오기만 담당
- Separation: HTTP 요청 로직 분리
- Robustness: 정적/동적 페이지 모두 처리
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Optional
from urllib.parse import urlparse

import httpx
import trafilatura

from app.services.og_metadata import OGMetadata, extract_og_metadata
from app.services.twitter_scraper import twitter_scraper

logger = logging.getLogger(__name__)

# 최소 유효 콘텐츠 길이 (이보다 짧으면 JS 렌더링 필요로 판단)
MIN_CONTENT_LENGTH = 200

# 직접 접근 불가능한 도메인 (별도 스크래퍼 사용)
# Twitter/X는 Playwright로 처리 가능하므로 제외
INACCESSIBLE_DOMAINS: frozenset[str] = frozenset([
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
    "www.youtu.be",
])

# Twitter/X 도메인 (Playwright 필수)
TWITTER_DOMAINS: frozenset[str] = frozenset([
    "twitter.com",
    "x.com",
    "www.twitter.com",
    "www.x.com",
    "mobile.twitter.com",
    "mobile.x.com",
])

# GitHub blob URL 패턴 (JS 렌더링이라 raw URL 변환 필요)
GITHUB_BLOB_PATTERN = re.compile(
    r"^https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$"
)


def is_inaccessible_url(url: str) -> bool:
    """YouTube 등 별도 스크래퍼 필요한 URL"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return domain in INACCESSIBLE_DOMAINS
    except Exception:
        return False


def is_twitter_url(url: str) -> bool:
    """Twitter/X URL인지 확인 (Playwright 필수)"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return domain in TWITTER_DOMAINS
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


def extract_text_from_html(html: str) -> Optional[str]:
    """
    HTML에서 본문 텍스트 추출
    1차: trafilatura
    2차: BeautifulSoup fallback
    """
    # trafilatura 시도
    content = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        no_fallback=False,
    )

    if content and len(content) >= MIN_CONTENT_LENGTH:
        return content

    # BeautifulSoup fallback
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        fallback = soup.get_text(separator="\n", strip=True)
        if fallback and len(fallback) >= MIN_CONTENT_LENGTH:
            return fallback
    except Exception:
        pass

    return content  # 짧더라도 반환


async def fetch_with_playwright(
    url: str,
    wait_until: str = "networkidle",
    wait_time: float = 1.0,
) -> Optional[str]:
    """
    Playwright로 JS 렌더링 후 HTML 가져오기

    Args:
        url: 대상 URL
        wait_until: 페이지 로드 대기 조건 (networkidle, domcontentloaded, load)
        wait_time: 추가 대기 시간 (초)
    """
    try:
        from playwright.async_api import async_playwright

        logger.info(f"[Playwright] JS 렌더링 시작: {url} (wait_until={wait_until})")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            # 페이지 로드 (최대 30초)
            await page.goto(url, wait_until=wait_until, timeout=30000)

            # 동적 콘텐츠 로드 대기
            await asyncio.sleep(wait_time)

            # HTML 가져오기
            html = await page.content()

            await browser.close()

            logger.info(f"[Playwright] 렌더링 완료: {len(html):,} bytes")
            return html

    except Exception as e:
        logger.error(f"[Playwright] 렌더링 실패: {url}, error={e}")
        return None


async def fetch_url_content(
    url: str,
    max_length: int = 10000,
) -> tuple[Optional[str], Optional[OGMetadata]]:
    """
    URL에서 콘텐츠와 OG 메타데이터 가져오기

    처리 순서:
    1. YouTube → 별도 스크래퍼 필요 메시지
    2. Twitter/X → Playwright로 직접 처리
    3. GitHub blob → raw URL로 변환하여 텍스트 그대로 사용
    4. 일반 URL → trafilatura로 본문 추출
    5. 결과 부실 시 → Playwright JS 렌더링 후 재시도

    Args:
        url: 대상 URL
        max_length: 최대 콘텐츠 길이

    Returns:
        (추출된 텍스트 콘텐츠, OG 메타데이터) 튜플
    """
    # 1. YouTube는 별도 스크래퍼 필요
    if is_inaccessible_url(url):
        logger.info(f"Inaccessible URL (별도 스크래퍼 필요): {url}")
        return None, OGMetadata(
            fetch_failed=True,
            fetch_message="이 링크는 직접 접근이 불가능합니다. 내용을 복사해서 메모에 붙여넣어 주세요.",
        )

    # 2. Twitter/X URL은 Playwright로 직접 처리
    if is_twitter_url(url):
        logger.info(f"Twitter URL 감지, Playwright로 처리: {url}")
        return await _fetch_twitter_content(url, max_length)

    # 3. GitHub blob URL은 raw URL로 변환
    github_raw_url = convert_github_blob_to_raw(url)
    if github_raw_url:
        logger.info(f"GitHub blob → raw 변환: {url}")
        return await _fetch_raw_text(url, github_raw_url, max_length)

    # 4. 일반 URL 처리
    return await _fetch_html_content(url, max_length)


async def _fetch_twitter_content(
    url: str,
    max_length: int,
) -> tuple[Optional[str], Optional[OGMetadata]]:
    """
    Twitter/X URL에서 콘텐츠 가져오기 (TwitterScraper 사용)

    TwitterScraper는 다음 순서로 콘텐츠 추출:
    1. Syndication API로 메타데이터 추출
    2. Article URL이나 긴 트윗(note_tweet) 감지 시 Playwright로 전체 내용 추출
    3. 실패 시 Playwright 폴백
    """
    try:
        logger.info(f"[Twitter] TwitterScraper로 콘텐츠 추출 시작: {url}")

        result = await twitter_scraper.scrape(url)

        if not result.success:
            logger.warning(f"[Twitter] 스크래핑 실패: {result.error}")
            return None, OGMetadata(
                fetch_failed=True,
                fetch_message=f"트위터 콘텐츠를 가져오는데 실패했습니다: {result.error}",
            )

        content = result.content
        if content and len(content) > max_length:
            content = content[:max_length] + "..."

        # OG 메타데이터 생성
        og_metadata = OGMetadata(
            title=result.og_title,
            image=result.og_image,
            description=result.og_description,
        )

        logger.info(
            f"[Twitter] 추출 완료: {url}, "
            f"length={len(content) if content else 0}, "
            f"article_url={result.article_url}"
        )
        return content, og_metadata

    except Exception as e:
        logger.error(f"[Twitter] 콘텐츠 가져오기 실패: {url}, error={e}")
        return None, OGMetadata(
            fetch_failed=True,
            fetch_message=f"트위터 콘텐츠를 가져오는데 실패했습니다: {str(e)}",
        )


async def _fetch_raw_text(
    original_url: str,
    raw_url: str,
    max_length: int,
) -> tuple[Optional[str], Optional[OGMetadata]]:
    """
    Raw 텍스트 URL에서 콘텐츠 가져오기 (GitHub raw 등)
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # raw 텍스트 가져오기
            response = await client.get(
                raw_url,
                headers={"User-Agent": "Mozilla/5.0 Zentel/1.0"},
                follow_redirects=True,
            )
            response.raise_for_status()
            content = response.text

            # OG 메타데이터는 원본 URL에서 가져옴
            og_metadata = None
            try:
                og_response = await client.get(original_url, follow_redirects=True)
                if og_response.status_code == 200:
                    og_metadata = extract_og_metadata(og_response.text, original_url)
            except Exception as e:
                logger.warning(f"OG 메타데이터 가져오기 실패: {e}")

            # 콘텐츠 길이 제한
            if content and len(content) > max_length:
                content = content[:max_length] + "..."

            logger.info(
                f"Raw 텍스트 추출 완료: {original_url}, "
                f"length={len(content) if content else 0}"
            )
            return content, og_metadata

    except Exception as e:
        logger.error(f"Raw 텍스트 가져오기 실패: {original_url}, error={e}")
        return None, None


async def _fetch_html_content(
    url: str,
    max_length: int,
) -> tuple[Optional[str], Optional[OGMetadata]]:
    """
    일반 HTML 페이지에서 콘텐츠 가져오기
    정적 추출 실패 시 Playwright로 JS 렌더링
    """
    try:
        # 1단계: 일반 HTTP 요청
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 Zentel/1.0"},
                follow_redirects=True,
            )
            response.raise_for_status()
            html = response.text

        # OG 메타데이터 추출
        og_metadata = extract_og_metadata(html, url)

        # 2단계: 정적 HTML에서 본문 추출 시도
        content = extract_text_from_html(html)
        used_playwright = False

        # 3단계: 결과 부실 시 Playwright로 재시도
        if not content or len(content) < MIN_CONTENT_LENGTH:
            logger.info(
                f"정적 추출 부실 ({len(content) if content else 0}자), "
                f"Playwright 시도: {url}"
            )

            rendered_html = await fetch_with_playwright(url)
            if rendered_html:
                rendered_content = extract_text_from_html(rendered_html)
                if rendered_content and len(rendered_content) > len(content or ""):
                    content = rendered_content
                    used_playwright = True
                    # 렌더링된 HTML에서 OG 재추출
                    og_metadata = extract_og_metadata(rendered_html, url) or og_metadata

        # 콘텐츠 길이 제한
        if content and len(content) > max_length:
            content = content[:max_length] + "..."

        logger.info(
            f"URL 콘텐츠 추출 완료: {url}, "
            f"length={len(content) if content else 0}, "
            f"playwright={used_playwright}"
        )
        return content, og_metadata

    except Exception as e:
        logger.error(f"URL 콘텐츠 가져오기 실패: {url}, error={e}")
        return None, None

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
import random
import re
from typing import Awaitable, Callable, Optional
from urllib.parse import urlparse

import httpx
import trafilatura

from app.services.og_metadata import OGMetadata, extract_og_metadata
from app.services.twitter_scraper import twitter_scraper

logger = logging.getLogger(__name__)

# Progress 콜백 타입 정의
ProgressCallback = Optional[Callable[[str, str, Optional[str]], Awaitable[None]]]

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

# Cloudflare 차단 감지 패턴
CLOUDFLARE_PATTERNS = [
    "cloudflare",
    "cf-browser-verification",
    "cf_chl_opt",
    "checking your browser",
    "please wait",
    "ray id",
    "security check",
    "attention required",
    "just a moment",
]


def is_cloudflare_blocked(html: str, status_code: int) -> bool:
    """Cloudflare Bot Fight Mode 차단 여부 확인"""
    if status_code == 403:
        html_lower = html.lower()
        return any(pattern in html_lower for pattern in CLOUDFLARE_PATTERNS)
    return False


async def human_like_delay(min_sec: float = 0.5, max_sec: float = 2.0) -> None:
    """사람처럼 랜덤한 딜레이"""
    delay = random.uniform(min_sec, max_sec)
    await asyncio.sleep(delay)


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


async def fetch_with_cloudflare_bypass(
    url: str,
    progress_callback: ProgressCallback = None,
    max_retries: int = 3,
) -> tuple[Optional[str], bool]:
    """
    Cloudflare Bot Fight Mode 우회하여 HTML 가져오기

    사람처럼 행동:
    - 랜덤 딜레이
    - 마우스 움직임
    - 스크롤
    - 실제 브라우저 핑거프린트

    Args:
        url: 대상 URL
        progress_callback: 진행 상황 콜백 (step, message, detail)
        max_retries: 최대 재시도 횟수

    Returns:
        (HTML 콘텐츠, 성공 여부) 튜플
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("[Cloudflare] Playwright가 설치되지 않음")
        return None, False

    async def notify(step: str, message: str, detail: Optional[str] = None):
        if progress_callback:
            await progress_callback(step, message, detail)

    for attempt in range(max_retries):
        try:
            await notify(
                "cloudflare_bypass",
                f"Cloudflare 우회 시도 중 ({attempt + 1}/{max_retries})",
                "사람처럼 행동하는 브라우저로 접속 중..."
            )

            logger.info(
                f"[Cloudflare] 우회 시도 {attempt + 1}/{max_retries}: {url}"
            )

            async with async_playwright() as p:
                # 실제 브라우저처럼 설정 (새로운 headless 모드 사용)
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                        "--disable-web-security",
                        "--disable-features=IsolateOrigins,site-per-process",
                    ],
                    chromium_sandbox=False,
                )

                # 실제 사용자처럼 보이는 컨텍스트
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1920, "height": 1080},
                    locale="ko-KR",
                    timezone_id="Asia/Seoul",
                )

                # 봇 감지 스크립트 우회
                await context.add_init_script("""
                    // webdriver 플래그 숨기기
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });

                    // plugins 배열 채우기
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });

                    // languages 설정
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['ko-KR', 'ko', 'en-US', 'en']
                    });

                    // Chrome 객체 추가
                    window.chrome = {
                        runtime: {}
                    };
                """)

                page = await context.new_page()

                # 랜덤 딜레이 후 페이지 로드
                await human_like_delay(0.5, 1.5)

                await notify(
                    "cloudflare_loading",
                    "페이지 로딩 중...",
                    url
                )

                # 페이지 로드 (domcontentloaded로 빠르게)
                try:
                    response = await page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=30000
                    )
                    status_code = response.status if response else 0
                except Exception as goto_error:
                    logger.warning(f"[Cloudflare] goto 에러 (무시): {goto_error}")
                    status_code = 0

                logger.info(f"[Cloudflare] 초기 응답: status={status_code}")

                # Cloudflare challenge 대기 (최대 15초)
                await notify(
                    "cloudflare_waiting",
                    "Cloudflare 검증 대기 중...",
                    "브라우저가 사람인지 확인하고 있습니다"
                )

                # 사람처럼 행동하면서 대기
                last_html = ""
                last_title = ""

                for wait_round in range(5):
                    try:
                        # 랜덤 딜레이
                        await human_like_delay(1.5, 3.0)

                        # 랜덤 마우스 움직임
                        try:
                            x = random.randint(100, 800)
                            y = random.randint(100, 600)
                            await page.mouse.move(x, y)
                        except Exception:
                            pass

                        # 가끔 스크롤
                        if random.random() > 0.5:
                            try:
                                scroll_amount = random.randint(100, 300)
                                await page.mouse.wheel(0, scroll_amount)
                            except Exception:
                                pass

                        # 현재 HTML 확인
                        try:
                            html = await page.content()
                            title = await page.title()
                            last_html = html
                            last_title = title
                        except Exception as content_error:
                            logger.warning(
                                f"[Cloudflare] content 조회 에러: {content_error}"
                            )
                            break

                        # Cloudflare 통과 여부 확인
                        if not is_cloudflare_blocked(html, 403):
                            # 제목에 cloudflare 관련 내용이 없으면 성공
                            title_lower = title.lower() if title else ""
                            if "just a moment" not in title_lower and "cloudflare" not in title_lower:
                                logger.info(
                                    f"[Cloudflare] 우회 성공! "
                                    f"round={wait_round + 1}, title={title}"
                                )
                                await notify(
                                    "cloudflare_success",
                                    "Cloudflare 우회 성공!",
                                    f"페이지 로드 완료 ({len(html):,} bytes)"
                                )

                                # 최종 콘텐츠 로드 대기
                                await human_like_delay(1.0, 2.0)
                                try:
                                    html = await page.content()
                                except Exception:
                                    pass

                                await browser.close()
                                return html, True

                        logger.debug(
                            f"[Cloudflare] 아직 대기 중... "
                            f"round={wait_round + 1}, title={title}"
                        )

                    except Exception as round_error:
                        logger.warning(
                            f"[Cloudflare] round {wait_round + 1} 에러: {round_error}"
                        )
                        break

                # 5라운드 후에도 통과 못함
                try:
                    html = await page.content()
                except Exception:
                    html = last_html

                try:
                    await browser.close()
                except Exception:
                    pass

                # 마지막 시도에서 콘텐츠가 있으면 반환
                if html and len(html) > 1000 and not is_cloudflare_blocked(html, 403):
                    logger.info(f"[Cloudflare] 부분 성공: {len(html):,} bytes")
                    return html, True

                logger.warning(f"[Cloudflare] 시도 {attempt + 1} 실패, 재시도...")

        except Exception as e:
            logger.error(f"[Cloudflare] 시도 {attempt + 1} 에러: {e}")

        # 재시도 전 랜덤 대기
        if attempt < max_retries - 1:
            wait_time = random.uniform(2.0, 5.0)
            await notify(
                "cloudflare_retry",
                f"재시도 대기 중... ({wait_time:.1f}초)",
                f"시도 {attempt + 1}/{max_retries} 실패"
            )
            await asyncio.sleep(wait_time)

    # 모든 시도 실패
    await notify(
        "cloudflare_failed",
        "Cloudflare 우회 실패",
        f"{max_retries}회 시도 후 포기. 내용을 직접 복사해주세요."
    )
    logger.error(f"[Cloudflare] 최종 실패: {url}")
    return None, False


async def fetch_url_content(
    url: str,
    max_length: int = 10000,
    progress_callback: ProgressCallback = None,
) -> tuple[Optional[str], Optional[OGMetadata]]:
    """
    URL에서 콘텐츠와 OG 메타데이터 가져오기

    처리 순서:
    1. YouTube → 별도 스크래퍼 필요 메시지
    2. Twitter/X → Playwright로 직접 처리
    3. GitHub blob → raw URL로 변환하여 텍스트 그대로 사용
    4. 일반 URL → trafilatura로 본문 추출
    5. Cloudflare 차단 감지 → 사람처럼 행동하는 우회 시도
    6. 결과 부실 시 → Playwright JS 렌더링 후 재시도

    Args:
        url: 대상 URL
        max_length: 최대 콘텐츠 길이
        progress_callback: 진행 상황 콜백 (step, message, detail)

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

    # 4. 일반 URL 처리 (Cloudflare 감지 포함)
    return await _fetch_html_content(url, max_length, progress_callback)


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
    progress_callback: ProgressCallback = None,
) -> tuple[Optional[str], Optional[OGMetadata]]:
    """
    일반 HTML 페이지에서 콘텐츠 가져오기
    Cloudflare 차단 감지 시 사람처럼 행동하는 우회 시도
    정적 추출 실패 시 Playwright로 JS 렌더링
    """
    async def notify(step: str, message: str, detail: Optional[str] = None):
        if progress_callback:
            await progress_callback(step, message, detail)

    og_metadata: Optional[OGMetadata] = None
    cloudflare_detected = False

    try:
        # 1단계: 일반 HTTP 요청
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                },
                follow_redirects=True,
            )
            status_code = response.status_code
            html = response.text

        # Cloudflare 차단 감지
        if is_cloudflare_blocked(html, status_code):
            cloudflare_detected = True
            logger.warning(f"[Cloudflare] Bot Fight Mode 감지: {url}")
            await notify(
                "cloudflare_detected",
                "Cloudflare Bot Fight Mode 감지",
                "사람처럼 행동하는 브라우저로 우회 시도합니다..."
            )

            # Cloudflare 우회 시도
            bypassed_html, success = await fetch_with_cloudflare_bypass(
                url, progress_callback, max_retries=3
            )

            if success and bypassed_html:
                html = bypassed_html
                logger.info(f"[Cloudflare] 우회 성공: {url}")
            else:
                # 우회 실패
                logger.error(f"[Cloudflare] 우회 최종 실패: {url}")
                return None, OGMetadata(
                    fetch_failed=True,
                    fetch_message=(
                        "Cloudflare 보안으로 인해 콘텐츠를 가져올 수 없습니다. "
                        "기사 내용을 직접 복사해서 메모에 붙여넣어 주세요."
                    ),
                )

        # OG 메타데이터 추출
        og_metadata = extract_og_metadata(html, url)

        # 2단계: 정적 HTML에서 본문 추출 시도
        content = extract_text_from_html(html)
        used_playwright = False

        # 3단계: 결과 부실 시 Playwright로 재시도 (Cloudflare 우회 성공한 경우 스킵)
        if not cloudflare_detected and (not content or len(content) < MIN_CONTENT_LENGTH):
            logger.info(
                f"정적 추출 부실 ({len(content) if content else 0}자), "
                f"Playwright 시도: {url}"
            )

            rendered_html = await fetch_with_playwright(url)
            if rendered_html:
                # 렌더링 후에도 Cloudflare 차단 확인
                if is_cloudflare_blocked(rendered_html, 403):
                    logger.warning(f"[Cloudflare] Playwright 렌더링 후에도 차단 감지: {url}")
                    await notify(
                        "cloudflare_detected",
                        "Cloudflare Bot Fight Mode 감지",
                        "사람처럼 행동하는 브라우저로 우회 시도합니다..."
                    )

                    # Cloudflare 우회 시도
                    bypassed_html, success = await fetch_with_cloudflare_bypass(
                        url, progress_callback, max_retries=3
                    )

                    if success and bypassed_html:
                        rendered_html = bypassed_html
                    else:
                        return None, OGMetadata(
                            fetch_failed=True,
                            fetch_message=(
                                "Cloudflare 보안으로 인해 콘텐츠를 가져올 수 없습니다. "
                                "기사 내용을 직접 복사해서 메모에 붙여넣어 주세요."
                            ),
                        )

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
            f"playwright={used_playwright}, "
            f"cloudflare_bypass={cloudflare_detected}"
        )
        return content, og_metadata

    except httpx.HTTPStatusError as e:
        # HTTP 에러 (403 등)
        if e.response.status_code == 403:
            html = e.response.text
            if is_cloudflare_blocked(html, 403):
                logger.warning(f"[Cloudflare] HTTP 403 + Bot Fight Mode 감지: {url}")
                await notify(
                    "cloudflare_detected",
                    "Cloudflare Bot Fight Mode 감지",
                    "사람처럼 행동하는 브라우저로 우회 시도합니다..."
                )

                # Cloudflare 우회 시도
                bypassed_html, success = await fetch_with_cloudflare_bypass(
                    url, progress_callback, max_retries=3
                )

                if success and bypassed_html:
                    og_metadata = extract_og_metadata(bypassed_html, url)
                    content = extract_text_from_html(bypassed_html)

                    if content and len(content) > max_length:
                        content = content[:max_length] + "..."

                    logger.info(
                        f"[Cloudflare] 우회 후 추출 완료: {url}, "
                        f"length={len(content) if content else 0}"
                    )
                    return content, og_metadata
                else:
                    return None, OGMetadata(
                        fetch_failed=True,
                        fetch_message=(
                            "Cloudflare 보안으로 인해 콘텐츠를 가져올 수 없습니다. "
                            "기사 내용을 직접 복사해서 메모에 붙여넣어 주세요."
                        ),
                    )

        logger.error(f"URL 콘텐츠 가져오기 실패 (HTTP): {url}, error={e}")
        return None, None

    except Exception as e:
        logger.error(f"URL 콘텐츠 가져오기 실패: {url}, error={e}")
        return None, None

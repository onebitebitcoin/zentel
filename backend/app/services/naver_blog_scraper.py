"""
네이버 블로그 스크래핑 서비스

Unix Philosophy:
- Modularity: 네이버 블로그 스크래핑만 담당
- Simplicity: Playwright로 브라우저 열어 콘텐츠 추출
- Robustness: 봇 차단 우회 (사람처럼 행동)
"""

from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# 네이버 블로그 도메인
NAVER_BLOG_DOMAINS: frozenset[str] = frozenset([
    "blog.naver.com",
    "m.blog.naver.com",
])

# 네이버 블로그 본문 CSS 선택자 (우선순위 순)
CONTENT_SELECTORS = [
    "#postViewArea",  # 일반 블로그
    ".se-main-container",  # 스마트에디터 ONE
    ".se_component_wrap",  # 스마트에디터 2.0
    "#content-area",  # 구 버전
    ".post-view",  # 모바일
    "#viewTypeSelector",  # 대체 선택자
]

# OG 메타데이터 선택자
OG_TITLE_SELECTOR = 'meta[property="og:title"]'
OG_IMAGE_SELECTOR = 'meta[property="og:image"]'
OG_DESCRIPTION_SELECTOR = 'meta[property="og:description"]'


@dataclass
class NaverBlogScrapingResult:
    """네이버 블로그 스크래핑 결과"""

    content: str = ""
    og_title: Optional[str] = None
    og_image: Optional[str] = None
    og_description: Optional[str] = None
    success: bool = False
    error: Optional[str] = None


def is_naver_blog_url(url: str) -> bool:
    """네이버 블로그 URL인지 확인"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return domain in NAVER_BLOG_DOMAINS
    except Exception:
        return False


async def human_like_delay(min_sec: float = 0.5, max_sec: float = 2.0) -> None:
    """사람처럼 랜덤한 딜레이"""
    delay = random.uniform(min_sec, max_sec)
    await asyncio.sleep(delay)


class NaverBlogScraper:
    """
    네이버 블로그 스크래핑 서비스

    Playwright로 브라우저를 열어 네이버 블로그 콘텐츠를 추출합니다.
    - 봇 차단 우회 (사람처럼 행동)
    - 네이버 특화 CSS 선택자 사용
    - OG 메타데이터 추출
    """

    def __init__(
        self,
        timeout: int = 30000,
        headless: bool = True,
    ):
        self.timeout = timeout
        self.headless = headless

    async def scrape(self, url: str) -> NaverBlogScrapingResult:
        """
        네이버 블로그 URL에서 콘텐츠 추출

        Args:
            url: 네이버 블로그 URL

        Returns:
            NaverBlogScrapingResult
        """
        if not is_naver_blog_url(url):
            return NaverBlogScrapingResult(
                success=False,
                error="네이버 블로그 URL이 아닙니다.",
            )

        logger.info(f"[NaverBlog] 스크래핑 시작: {url}")

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("[NaverBlog] Playwright가 설치되지 않음")
            return NaverBlogScrapingResult(
                success=False,
                error="Playwright가 설치되지 않았습니다.",
            )

        try:
            async with async_playwright() as p:
                # 실제 브라우저처럼 설정
                browser = await p.chromium.launch(
                    headless=self.headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                        "--disable-web-security",
                    ],
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

                # 봇 감지 우회
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['ko-KR', 'ko', 'en-US', 'en']
                    });
                    window.chrome = { runtime: {} };
                """)

                page = await context.new_page()

                # 랜덤 딜레이 후 페이지 로드
                await human_like_delay(0.5, 1.5)

                logger.info(f"[NaverBlog] 페이지 로딩 중: {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout)

                # 네이버 블로그 로딩 대기 (iframe 로딩 등)
                await human_like_delay(2.0, 3.0)

                # 가끔 스크롤 (사람처럼 행동)
                if random.random() > 0.5:
                    try:
                        scroll_amount = random.randint(100, 500)
                        await page.mouse.wheel(0, scroll_amount)
                        await human_like_delay(0.5, 1.0)
                    except Exception:
                        pass

                # OG 메타데이터 추출 (메인 페이지에서)
                og_title = await self._extract_og_meta(page, OG_TITLE_SELECTOR)
                og_image = await self._extract_og_meta(page, OG_IMAGE_SELECTOR)
                og_description = await self._extract_og_meta(page, OG_DESCRIPTION_SELECTOR)

                # iframe 내부로 진입 시도 (네이버 블로그는 iframe 사용)
                target_frame = page
                try:
                    # mainFrame iframe 찾기
                    iframe_element = await page.query_selector('iframe#mainFrame')
                    if iframe_element:
                        frame = await iframe_element.content_frame()
                        if frame:
                            logger.info("[NaverBlog] mainFrame iframe으로 진입")
                            target_frame = frame
                            await human_like_delay(1.0, 2.0)
                except Exception as e:
                    logger.debug(f"[NaverBlog] iframe 진입 실패 (무시): {e}")

                # 본문 추출 (여러 선택자 시도) - iframe 내부에서
                content = await self._extract_content(target_frame)

                await browser.close()

                if not content:
                    logger.warning(f"[NaverBlog] 콘텐츠 추출 실패: {url}")
                    return NaverBlogScrapingResult(
                        og_title=og_title,
                        og_image=og_image,
                        og_description=og_description,
                        success=False,
                        error="네이버 블로그 콘텐츠를 추출할 수 없습니다.",
                    )

                logger.info(
                    f"[NaverBlog] 스크래핑 성공: {url}, "
                    f"length={len(content)}"
                )

                return NaverBlogScrapingResult(
                    content=content,
                    og_title=og_title,
                    og_image=og_image,
                    og_description=og_description,
                    success=True,
                )

        except Exception as e:
            logger.error(f"[NaverBlog] 스크래핑 실패: {url}, error={e}")
            return NaverBlogScrapingResult(
                success=False,
                error=f"네이버 블로그 스크래핑 실패: {str(e)}",
            )

    async def _extract_og_meta(self, page, selector: str) -> Optional[str]:
        """OG 메타데이터 추출"""
        try:
            element = await page.query_selector(selector)
            if element:
                return await element.get_attribute("content")
        except Exception as e:
            logger.debug(f"[NaverBlog] OG 메타 추출 실패: {selector}, error={e}")
        return None

    async def _extract_content(self, page) -> Optional[str]:
        """본문 추출 (여러 선택자 시도)"""
        for selector in CONTENT_SELECTORS:
            try:
                element = await page.query_selector(selector)
                if element:
                    # 텍스트 추출
                    text = await element.inner_text()
                    if text and len(text.strip()) > 100:
                        logger.info(f"[NaverBlog] 콘텐츠 추출 성공: selector={selector}")
                        return text.strip()
            except Exception as e:
                logger.debug(f"[NaverBlog] 선택자 시도 실패: {selector}, error={e}")
                continue

        # 모든 선택자 실패 시 body 전체 텍스트 추출
        try:
            body = await page.query_selector("body")
            if body:
                text = await body.inner_text()
                if text and len(text.strip()) > 100:
                    logger.info("[NaverBlog] body 전체 텍스트 추출")
                    return text.strip()
        except Exception as e:
            logger.error(f"[NaverBlog] body 추출 실패: {e}")

        return None


# 싱글톤 인스턴스
naver_blog_scraper = NaverBlogScraper()

"""
Twitter/X 스크래핑 서비스

Playwright를 사용하여 x.com의 컨텐츠를 추출합니다.
- 싱글톤 패턴으로 브라우저 인스턴스 관리
- 동시 요청 제한 (asyncio.Semaphore)
- 쿠키 기반 세션 유지
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# 동시 요청 제한
MAX_CONCURRENT_REQUESTS = 2
_semaphore: Optional[asyncio.Semaphore] = None


def _get_semaphore() -> asyncio.Semaphore:
    """Semaphore 인스턴스 반환 (Lazy initialization)"""
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    return _semaphore


@dataclass
class TwitterScrapingResult:
    """Twitter 스크래핑 결과"""

    content: str = ""
    og_title: Optional[str] = None
    og_image: Optional[str] = None
    og_description: Optional[str] = None
    success: bool = False
    error: Optional[str] = None
    elapsed_time: float = 0.0


class TwitterScraper:
    """Twitter/X 스크래핑 서비스"""

    def __init__(
        self,
        timeout: int = 30000,
        cookies_dir: Optional[str] = None,
        headless: bool = True,
    ):
        """
        초기화

        Args:
            timeout: 페이지 로딩 타임아웃 (밀리초)
            cookies_dir: 쿠키 저장 디렉토리
            headless: 헤드리스 모드 사용 여부
        """
        self.timeout = timeout
        self.headless = headless
        self.user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        # 쿠키 저장 경로 설정
        if cookies_dir is None:
            cookies_dir = os.path.join(os.path.dirname(__file__), "..", "..", "cookies")
        self.cookies_dir = Path(cookies_dir)
        self.cookies_dir.mkdir(exist_ok=True)

        # Twitter 로그인 정보 (환경 변수에서 읽기)
        self.twitter_username = os.getenv("TWITTER_USERNAME")
        self.twitter_password = os.getenv("TWITTER_PASSWORD")

    def is_twitter_url(self, url: str) -> bool:
        """
        Twitter/X URL인지 확인

        Args:
            url: 확인할 URL

        Returns:
            Twitter URL이면 True
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower() in [
                "twitter.com",
                "x.com",
                "www.twitter.com",
                "www.x.com",
                "mobile.twitter.com",
                "mobile.x.com",
            ]
        except Exception:
            return False

    async def scrape(self, url: str) -> TwitterScrapingResult:
        """
        Twitter URL의 컨텐츠를 추출

        Args:
            url: 스크래핑할 URL

        Returns:
            TwitterScrapingResult
        """
        semaphore = _get_semaphore()
        async with semaphore:
            return await self._scrape_internal(url)

    async def _scrape_internal(self, url: str) -> TwitterScrapingResult:
        """내부 스크래핑 로직"""
        start_time = time.time()
        result = TwitterScrapingResult()

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                logger.info(f"[TwitterScraper] 브라우저 시작 (headless={self.headless})")

                browser = await p.firefox.launch(headless=self.headless)

                context = await browser.new_context(
                    user_agent=self.user_agent,
                    viewport={"width": 1280, "height": 720},
                )

                # 쿠키 로드
                await self._load_cookies(context)

                page = await context.new_page()

                logger.info(f"[TwitterScraper] URL 로딩: {url}")
                await page.goto(url, timeout=self.timeout, wait_until="load")

                # 로그인 확인 및 처리
                is_logged_in = await self._check_login_status(page)
                if not is_logged_in:
                    logger.info("[TwitterScraper] 로그인 필요. 로그인 시도 중...")
                    login_success = await self._login(page)
                    if login_success:
                        logger.info("[TwitterScraper] 로그인 성공")
                        await self._save_cookies(context)
                        await page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
                    else:
                        result.error = "Twitter 로그인 실패. 환경 변수 TWITTER_USERNAME/PASSWORD를 확인하세요."
                        await browser.close()
                        result.elapsed_time = time.time() - start_time
                        return result
                else:
                    logger.info("[TwitterScraper] 이미 로그인됨")

                # 트윗 로딩 대기
                await page.wait_for_timeout(2000)

                # OG 메타데이터 추출
                og_metadata = await self._extract_og_metadata(page)
                result.og_title = og_metadata.get("title")
                result.og_image = og_metadata.get("image")
                result.og_description = og_metadata.get("description")

                # 본문 텍스트 추출
                result.content = await self._extract_tweet_content(page)

                await browser.close()
                result.success = True
                logger.info(
                    f"[TwitterScraper] 스크래핑 완료: content_length={len(result.content)}"
                )

        except Exception as e:
            logger.error(f"[TwitterScraper] 스크래핑 실패: {e}", exc_info=True)
            result.error = str(e)

        result.elapsed_time = time.time() - start_time
        return result

    async def _extract_og_metadata(self, page) -> dict:
        """OG 메타데이터 추출"""
        metadata = {}

        og_tags = {
            "title": "og:title",
            "description": "og:description",
            "image": "og:image",
        }

        for key, property_name in og_tags.items():
            try:
                element = await page.query_selector(f'meta[property="{property_name}"]')
                if element:
                    content = await element.get_attribute("content")
                    if content:
                        metadata[key] = content
            except Exception:
                pass

        # og:title이 없으면 일반 title 태그 사용
        if "title" not in metadata:
            try:
                title = await page.title()
                if title:
                    metadata["title"] = title
            except Exception:
                pass

        return metadata

    async def _extract_tweet_content(self, page) -> str:
        """트윗 본문 텍스트 추출"""
        try:
            # 트윗 텍스트 요소 찾기 (data-testid="tweetText")
            tweet_elements = await page.query_selector_all('[data-testid="tweetText"]')
            if tweet_elements:
                texts = []
                for elem in tweet_elements[:3]:  # 최대 3개만 추출
                    text = await elem.inner_text()
                    if text:
                        texts.append(text.strip())
                if texts:
                    return "\n\n".join(texts)

            # fallback: body 텍스트 추출
            text = await page.evaluate(
                """
                () => {
                    const clone = document.body.cloneNode(true);
                    const scripts = clone.querySelectorAll('script, style, noscript');
                    scripts.forEach(el => el.remove());
                    const text = clone.innerText || clone.textContent || '';
                    return text.trim();
                }
            """
            )
            return text[:5000] if text else ""  # 최대 5000자

        except Exception as e:
            logger.error(f"[TwitterScraper] 텍스트 추출 실패: {e}")
            return ""

    async def _load_cookies(self, context):
        """저장된 쿠키 로드"""
        cookies_path = self.cookies_dir / "twitter_cookies.json"
        if cookies_path.exists():
            try:
                with open(cookies_path, "r") as f:
                    cookies = json.load(f)
                await context.add_cookies(cookies)
                logger.info(f"[TwitterScraper] 쿠키 로드 성공: {cookies_path}")
            except Exception as e:
                logger.warning(f"[TwitterScraper] 쿠키 로드 실패: {e}")

    async def _save_cookies(self, context):
        """세션 쿠키 저장"""
        cookies_path = self.cookies_dir / "twitter_cookies.json"
        try:
            cookies = await context.cookies()
            with open(cookies_path, "w") as f:
                json.dump(cookies, f, indent=2)
            logger.info(f"[TwitterScraper] 쿠키 저장 성공: {cookies_path}")
        except Exception as e:
            logger.warning(f"[TwitterScraper] 쿠키 저장 실패: {e}")

    async def _check_login_status(self, page) -> bool:
        """로그인 상태 확인"""
        try:
            login_button = await page.query_selector('a[href="/login"]')
            return login_button is None
        except Exception:
            return False

    async def _login(self, page) -> bool:
        """Twitter 로그인"""
        if not self.twitter_username or not self.twitter_password:
            logger.error(
                "[TwitterScraper] TWITTER_USERNAME 또는 TWITTER_PASSWORD 환경 변수 미설정"
            )
            return False

        try:
            # 로그인 페이지로 이동
            await page.goto("https://x.com/i/flow/login", timeout=self.timeout)
            await page.wait_for_timeout(2000)

            # 이메일/사용자명 입력
            username_input = await page.wait_for_selector(
                'input[autocomplete="username"]', timeout=10000
            )
            await username_input.fill(self.twitter_username)
            await page.wait_for_timeout(500)

            # "다음" 버튼 클릭
            next_button = await page.query_selector('button:has-text("Next")')
            if not next_button:
                next_button = await page.query_selector('div[role="button"]:has-text("Next")')
            if next_button:
                await next_button.click()
                await page.wait_for_timeout(2000)

            # 비밀번호 입력
            password_input = await page.wait_for_selector(
                'input[type="password"]', timeout=10000
            )
            await password_input.fill(self.twitter_password)
            await page.wait_for_timeout(500)

            # "로그인" 버튼 클릭
            login_button = await page.query_selector(
                'button[data-testid="LoginForm_Login_Button"]'
            )
            if not login_button:
                login_button = await page.query_selector('div[role="button"]:has-text("Log in")')
            if login_button:
                await login_button.click()
                await page.wait_for_timeout(3000)

            # 로그인 성공 확인
            return await self._check_login_status(page)

        except Exception as e:
            logger.error(f"[TwitterScraper] 로그인 실패: {e}")
            return False


# 싱글톤 인스턴스
twitter_scraper = TwitterScraper()

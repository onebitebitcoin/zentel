"""
Twitter Playwright 스크래퍼

Unix Philosophy: Separation - 정책과 메커니즘 분리
- 브라우저 기반 스크래핑만 담당
- 쿠키/세션 관리
- 로그인 처리
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.utils import DEFAULT_USER_AGENT

logger = logging.getLogger(__name__)


@dataclass
class PlaywrightResult:
    """Playwright 스크래핑 결과"""

    content: str = ""
    og_title: Optional[str] = None
    og_image: Optional[str] = None
    og_description: Optional[str] = None
    success: bool = False
    error: Optional[str] = None
    elapsed_time: float = 0.0


class TwitterPlaywrightScraper:
    """Playwright 기반 Twitter 스크래퍼"""

    def __init__(
        self,
        timeout: int = 30000,
        cookies_dir: Optional[str] = None,
        headless: bool = True,
    ):
        self.timeout = timeout
        self.headless = headless
        self.user_agent = DEFAULT_USER_AGENT

        # 쿠키 저장 경로
        if cookies_dir is None:
            cookies_dir = os.path.join(os.path.dirname(__file__), "..", "..", "cookies")
        self.cookies_dir = Path(cookies_dir)
        self.cookies_dir.mkdir(exist_ok=True)

        # 로그인 정보
        self.twitter_username = os.getenv("TWITTER_USERNAME")
        self.twitter_password = os.getenv("TWITTER_PASSWORD")

    async def scrape(self, url: str) -> PlaywrightResult:
        """
        Playwright로 Twitter 콘텐츠 스크래핑

        Args:
            url: 스크래핑할 URL

        Returns:
            PlaywrightResult
        """
        import time

        start_time = time.time()
        result = PlaywrightResult()

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                logger.info(f"[Playwright] 브라우저 시작 (headless={self.headless})")

                browser = await p.chromium.launch(headless=self.headless)
                context = await browser.new_context(
                    user_agent=self.user_agent,
                    viewport={"width": 1280, "height": 720},
                )

                # 쿠키 로드
                await self._load_cookies(context)

                page = await context.new_page()

                # 로그인 확인 및 처리
                await self._ensure_logged_in(page, context)

                # 대상 URL로 이동
                logger.info(f"[Playwright] 대상 URL 로딩: {url}")
                await page.goto(url, timeout=self.timeout, wait_until="load")
                await page.wait_for_timeout(3000)

                # OG 메타데이터 추출
                og = await self._extract_og_metadata(page)
                result.og_title = og.get("title")
                result.og_image = og.get("image")
                result.og_description = og.get("description")

                # 콘텐츠 추출
                article_content = await self._extract_article_content(page)
                if article_content and len(article_content) > 200:
                    result.content = article_content
                else:
                    result.content = await self._extract_tweet_content(page)

                await browser.close()
                result.success = True
                logger.info(f"[Playwright] 완료: content_length={len(result.content)}")

        except Exception as e:
            logger.error(f"[Playwright] 실패: {e}", exc_info=True)
            result.error = str(e)

        result.elapsed_time = time.time() - start_time
        return result

    async def _ensure_logged_in(self, page, context) -> None:
        """로그인 상태 확인 및 필요시 로그인"""
        logger.info("[Playwright] X.com 홈페이지로 이동 중...")
        await page.goto("https://x.com/home", timeout=self.timeout, wait_until="load")
        await page.wait_for_timeout(2000)

        is_logged_in = await self._check_login_status(page)
        if is_logged_in:
            logger.info("[Playwright] 이미 로그인됨")
            return

        logger.info("[Playwright] 로그인 필요. 로그인 시도 중...")
        login_success = await self._login(page)
        if login_success:
            logger.info("[Playwright] 로그인 성공!")
            await self._save_cookies(context)
        else:
            logger.warning("[Playwright] 로그인 실패. 공개 콘텐츠만 추출 시도...")

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
            logger.error("[Playwright] TWITTER_USERNAME/PASSWORD 환경 변수 미설정")
            return False

        try:
            await page.goto("https://x.com/i/flow/login", timeout=self.timeout)
            await page.wait_for_timeout(3000)

            # 이메일/사용자명 입력
            username_input = await page.wait_for_selector(
                'input[autocomplete="username"]', timeout=15000
            )
            await username_input.fill(self.twitter_username)
            await page.wait_for_timeout(500)

            # "다음" 버튼 클릭
            next_button = await self._find_button(
                page, ["Next", "다음"]
            )
            if next_button:
                await next_button.click()
            else:
                await username_input.press("Enter")
            await page.wait_for_timeout(2000)

            # 비밀번호 입력
            password_input = await page.wait_for_selector(
                'input[type="password"]', timeout=15000
            )
            await password_input.fill(self.twitter_password)
            await page.wait_for_timeout(500)

            # "로그인" 버튼 클릭
            login_button = await self._find_button(
                page, ["Log in", "로그인"], data_testid="LoginForm_Login_Button"
            )
            if login_button:
                await login_button.click()
            else:
                await password_input.press("Enter")
            await page.wait_for_timeout(3000)

            return await self._check_login_status(page)

        except Exception as e:
            logger.error(f"[Playwright] 로그인 실패: {e}")
            return False

    async def _find_button(
        self, page, texts: list[str], data_testid: Optional[str] = None
    ):
        """버튼 찾기 헬퍼"""
        if data_testid:
            btn = await page.query_selector(f'button[data-testid="{data_testid}"]')
            if btn:
                return btn

        for text in texts:
            for selector in [
                f'button:has-text("{text}")',
                f'div[role="button"]:has-text("{text}")',
            ]:
                btn = await page.query_selector(selector)
                if btn:
                    return btn
        return None

    async def _load_cookies(self, context) -> None:
        """저장된 쿠키 로드"""
        cookies_path = self.cookies_dir / "twitter_cookies.json"
        if not cookies_path.exists():
            return

        try:
            with open(cookies_path) as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            logger.info(f"[Playwright] 쿠키 로드: {cookies_path}")
        except Exception as e:
            logger.warning(f"[Playwright] 쿠키 로드 실패: {e}")

    async def _save_cookies(self, context) -> None:
        """세션 쿠키 저장"""
        cookies_path = self.cookies_dir / "twitter_cookies.json"
        try:
            cookies = await context.cookies()
            with open(cookies_path, "w") as f:
                json.dump(cookies, f, indent=2)
            logger.info(f"[Playwright] 쿠키 저장: {cookies_path}")
        except Exception as e:
            logger.warning(f"[Playwright] 쿠키 저장 실패: {e}")

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

        if "title" not in metadata:
            try:
                title = await page.title()
                if title:
                    metadata["title"] = title
            except Exception:
                pass

        return metadata

    async def _extract_article_content(self, page) -> str:
        """X 아티클 본문 추출"""
        try:
            links = await page.query_selector_all('a[href*="/article/"]')
            article_url = None

            for link in links:
                href = await link.get_attribute("href")
                if href and "/article/" in href and "support.x.com" not in href:
                    article_url = f"https://x.com{href}" if href.startswith("/") else href
                    break

            if not article_url:
                return ""

            logger.info(f"[Playwright] 아티클 페이지: {article_url}")
            await page.goto(article_url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(5)

            main = await page.query_selector("main")
            if main:
                text = await main.inner_text()
                if text:
                    lines = text.strip().split("\n")
                    content_lines = [
                        line.strip()
                        for line in lines
                        if line.strip() and len(line.strip()) > 10
                    ]
                    if content_lines:
                        return "\n\n".join(content_lines)

            return ""

        except Exception as e:
            logger.warning(f"[Playwright] 아티클 추출 실패: {e}")
            return ""

    async def _extract_tweet_content(self, page) -> str:
        """트윗 본문 추출"""
        try:
            # X Notes 본문
            note_selectors = [
                '[data-testid="TextFlowRoot"]',
                '[data-testid="noteComponent"]',
                'article [data-testid="richTextComponent"]',
            ]

            for selector in note_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    texts = []
                    for elem in elements[:30]:
                        text = await elem.inner_text()
                        if text and len(text.strip()) > 5:
                            texts.append(text.strip())
                    if texts and len("\n".join(texts)) > 100:
                        return "\n\n".join(texts)

            # 일반 트윗
            tweet_elements = await page.query_selector_all('[data-testid="tweetText"]')
            if tweet_elements:
                texts = []
                for elem in tweet_elements[:5]:
                    text = await elem.inner_text()
                    if text:
                        texts.append(text.strip())
                if texts:
                    return "\n\n".join(texts)

            # 아티클 셀렉터
            article_selectors = [
                '[data-testid="article"] [dir="auto"]',
                '[role="article"] p',
                'article p',
            ]

            for selector in article_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    texts = []
                    for elem in elements[:20]:
                        text = await elem.inner_text()
                        if text and len(text) > 10:
                            texts.append(text.strip())
                    if texts:
                        return "\n\n".join(texts)

            # Fallback: main 영역 텍스트
            text = await page.evaluate(
                """
                () => {
                    const main = document.querySelector('main') ||
                                 document.querySelector('[role="main"]') ||
                                 document.body;
                    const clone = main.cloneNode(true);
                    ['script', 'style', 'noscript', 'nav', 'header', 'footer']
                        .forEach(sel => clone.querySelectorAll(sel).forEach(el => el.remove()));
                    return (clone.innerText || '').trim();
                }
            """
            )
            return text[:5000] if text else ""

        except Exception as e:
            logger.error(f"[Playwright] 텍스트 추출 실패: {e}")
            return ""

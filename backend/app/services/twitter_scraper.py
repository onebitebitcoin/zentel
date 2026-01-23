"""
Twitter/X 스크래핑 서비스

X.com의 컨텐츠를 추출합니다:
1. Syndication API로 메타데이터 추출 (screen_name, tweet_id, article_url)
2. 아티클 URL이 있으면 정규 트윗 URL로 변환
3. Playwright로 실제 콘텐츠 추출

- 동시 요청 제한 (asyncio.Semaphore)
- 쿠키 기반 세션 유지
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx

from app.utils import DEFAULT_USER_AGENT

logger = logging.getLogger(__name__)

# 동시 요청 제한
MAX_CONCURRENT_REQUESTS = 2
_semaphore: Optional[asyncio.Semaphore] = None

# 콘텐츠 최대 길이 (LLM 토큰 제한 고려)
MAX_CONTENT_LENGTH = 8000


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
    article_url: Optional[str] = None  # X 아티클 URL (있는 경우)
    screen_name: Optional[str] = None  # 작성자 screen_name (username)
    tweet_id: Optional[str] = None  # 트윗 ID


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
        self.user_agent = DEFAULT_USER_AGENT

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
            # 1. Syndication API로 메타데이터 추출
            result = await self._scrape_via_syndication(url)

            if result.success and result.content:
                # t.co 링크만 있고 아티클 URL이 있으면, 정규 트윗 URL로 접근
                article_url = result.article_url
                if article_url and result.screen_name and result.tweet_id:
                    # /i/article/ 대신 /username/status/ID 형식으로 접근
                    web_url = f"https://x.com/{result.screen_name}/status/{result.tweet_id}"
                    logger.info(f"[TwitterScraper] X 아티클 발견, 정규 트윗 URL로 접근: {web_url}")

                    article_result = await self._scrape_via_playwright(web_url)
                    if article_result.success and article_result.content:
                        if "이 페이지는 지원되지 않습니다" in article_result.content or \
                           "This page is not supported" in article_result.content:
                            # 웹에서 지원되지 않는 콘텐츠 - 아티클 URL 저장
                            result.og_description = f"X 아티클: {article_url}"
                            logger.info("[TwitterScraper] X 아티클은 앱에서만 지원됩니다")
                        else:
                            # 성공적으로 추출
                            article_result.og_title = result.og_title or article_result.og_title
                            article_result.og_description = f"아티클: {article_url}"
                            return self._truncate_content(article_result)
                return self._truncate_content(result)

            # 2. Syndication API 실패 시 Playwright 직접 사용
            logger.info("[TwitterScraper] Syndication API 실패, Playwright로 재시도...")
            return self._truncate_content(await self._scrape_via_playwright(url))

    def _truncate_content(self, result: TwitterScrapingResult) -> TwitterScrapingResult:
        """콘텐츠가 너무 길면 max까지 자름"""
        if result.content and len(result.content) > MAX_CONTENT_LENGTH:
            original_len = len(result.content)
            result.content = result.content[:MAX_CONTENT_LENGTH] + "..."
            logger.info(
                f"[TwitterScraper] 콘텐츠 truncate: {original_len} -> {MAX_CONTENT_LENGTH}"
            )
        return result

    def _extract_tweet_id(self, url: str) -> Optional[str]:
        """URL에서 트윗 ID 추출"""
        # /status/12345 형식에서 ID 추출
        match = re.search(r'/status/(\d+)', url)
        if match:
            return match.group(1)
        return None

    async def _scrape_via_syndication(self, url: str) -> TwitterScrapingResult:
        """Twitter Syndication API를 통한 메타데이터 추출"""
        start_time = time.time()
        result = TwitterScrapingResult()

        try:
            tweet_id = self._extract_tweet_id(url)
            if not tweet_id:
                logger.warning("[TwitterScraper] 트윗 ID 추출 실패")
                return result

            # Syndication API 호출
            api_url = f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&token=x"

            headers = {
                "User-Agent": self.user_agent,
                "Accept": "application/json",
            }

            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(api_url, headers=headers)

                if response.status_code == 200:
                    data = response.json()

                    # 트윗 텍스트 추출
                    result.content = data.get("text", "")

                    # 사용자 정보
                    user = data.get("user", {})
                    result.og_title = user.get("name", "")
                    result.screen_name = user.get("screen_name", "")
                    result.tweet_id = tweet_id

                    # 미디어 정보
                    media = data.get("mediaDetails", [])
                    if media and len(media) > 0:
                        result.og_image = media[0].get("media_url_https", "")

                    # t.co 링크가 있는 경우 실제 URL 확인
                    if result.content and "t.co/" in result.content:
                        tco_match = re.search(r'https://t\.co/\w+', result.content)
                        if tco_match:
                            tco_url = tco_match.group(0)
                            try:
                                redirect_response = await client.head(
                                    tco_url,
                                    follow_redirects=True,
                                    timeout=5.0
                                )
                                final_url = str(redirect_response.url)
                                logger.info(
                                    f"[TwitterScraper] t.co 리다이렉트: {tco_url} -> {final_url}"
                                )
                                result.og_description = f"링크: {final_url}"

                                # X 아티클인 경우 아티클 URL 저장
                                if "/i/article/" in final_url:
                                    result.article_url = final_url
                            except Exception as e:
                                logger.warning(f"[TwitterScraper] t.co 리다이렉트 실패: {e}")

                    result.success = bool(result.content)

                    logger.info(
                        f"[TwitterScraper] Syndication API 성공: content_length={len(result.content)}"
                    )
                else:
                    logger.warning(
                        f"[TwitterScraper] Syndication API 실패: status={response.status_code}"
                    )

        except Exception as e:
            logger.warning(f"[TwitterScraper] Syndication 실패: {e}")

        result.elapsed_time = time.time() - start_time
        return result

    async def _scrape_via_playwright(self, url: str) -> TwitterScrapingResult:
        """Playwright를 사용한 브라우저 스크래핑"""
        start_time = time.time()
        result = TwitterScrapingResult()

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                logger.info(f"[TwitterScraper] 브라우저 시작 (headless={self.headless})")

                browser = await p.chromium.launch(headless=self.headless)

                context = await browser.new_context(
                    user_agent=self.user_agent,
                    viewport={"width": 1280, "height": 720},
                )

                # 쿠키 로드
                await self._load_cookies(context)

                page = await context.new_page()

                # 1. 먼저 X.com 홈으로 이동해서 로그인 상태 확인
                logger.info("[TwitterScraper] X.com 홈페이지로 이동 중...")
                await page.goto("https://x.com/home", timeout=self.timeout, wait_until="load")
                await page.wait_for_timeout(2000)

                # 2. 로그인 확인 및 필요시 로그인
                is_logged_in = await self._check_login_status(page)
                if not is_logged_in:
                    logger.info("[TwitterScraper] 로그인 필요. 먼저 로그인 시도 중...")
                    login_success = await self._login(page)
                    if login_success:
                        logger.info("[TwitterScraper] 로그인 성공!")
                        await self._save_cookies(context)
                    else:
                        logger.warning("[TwitterScraper] 로그인 실패. 공개 콘텐츠만 추출 시도...")
                else:
                    logger.info("[TwitterScraper] 이미 로그인됨")

                # 3. 로그인 후 대상 URL로 이동
                logger.info(f"[TwitterScraper] 대상 URL 로딩: {url}")
                await page.goto(url, timeout=self.timeout, wait_until="load")
                await page.wait_for_timeout(3000)

                # 4. 콘텐츠 확인
                tweet_elements = await page.query_selector_all('[data-testid="tweetText"]')
                logger.info(f"[TwitterScraper] 트윗 요소 발견: {len(tweet_elements)}개")

                # 트윗 요소가 없으면 다른 셀렉터 시도
                if not tweet_elements:
                    await page.wait_for_timeout(3000)

                    article_selectors = [
                        '[data-testid="article"]',
                        '[role="article"]',
                        'article[data-testid]',
                        '[data-testid="cellInnerDiv"]',
                    ]

                    for selector in article_selectors:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            logger.info(f"[TwitterScraper] 아티클 요소 발견: {selector}, {len(elements)}개")
                            tweet_elements = elements
                            break

                # OG 메타데이터 추출
                og_metadata = await self._extract_og_metadata(page)
                result.og_title = og_metadata.get("title")
                result.og_image = og_metadata.get("image")
                result.og_description = og_metadata.get("description")

                # X 아티클 링크 확인 및 본문 추출
                article_content = await self._extract_article_content(page)
                if article_content and len(article_content) > 200:
                    logger.info(
                        f"[TwitterScraper] X 아티클 본문 추출 성공: {len(article_content)}자"
                    )
                    result.content = article_content
                else:
                    # 일반 트윗 본문 추출
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

    async def _extract_article_content(self, page) -> str:
        """X 아티클 본문 추출 (별도 페이지로 이동)"""
        try:
            # 아티클 링크 찾기
            links = await page.query_selector_all('a[href*="/article/"]')
            article_url = None

            for link in links:
                href = await link.get_attribute("href")
                if href and "/article/" in href and "support.x.com" not in href:
                    # 상대 경로면 절대 경로로 변환
                    if href.startswith("/"):
                        article_url = f"https://x.com{href}"
                    else:
                        article_url = href
                    break

            if not article_url:
                return ""

            logger.info(f"[TwitterScraper] X 아티클 페이지 발견: {article_url}")

            # 아티클 페이지로 이동
            await page.goto(article_url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(5)

            # main 영역에서 텍스트 추출
            main = await page.query_selector("main")
            if main:
                text = await main.inner_text()
                if text:
                    # 불필요한 부분 제거 (처음 몇 줄은 헤더)
                    lines = text.strip().split("\n")
                    # 빈 줄 제거하고 본문만 추출
                    content_lines = [
                        line.strip()
                        for line in lines
                        if line.strip() and len(line.strip()) > 10
                    ]
                    if content_lines:
                        return "\n\n".join(content_lines)

            return ""

        except Exception as e:
            logger.warning(f"[TwitterScraper] 아티클 추출 실패: {e}")
            return ""

    async def _extract_tweet_content(self, page) -> str:
        """트윗/아티클 본문 텍스트 추출"""
        try:
            # 0. X Notes/Articles (긴 형식) 본문 추출 시도
            # X Notes는 별도의 구조를 가짐
            note_selectors = [
                '[data-testid="TextFlowRoot"]',  # X Notes 본문
                '[data-testid="noteComponent"]',
                'article [data-testid="richTextComponent"]',
                '[class*="RichTextComposer"] [dir="auto"]',
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
                        logger.info(
                            f"[TwitterScraper] X Notes 텍스트 추출: {selector}, "
                            f"{len(texts)}개, total={len(''.join(texts))}자"
                        )
                        return "\n\n".join(texts)

            # 1. 트윗 텍스트 요소 찾기
            tweet_elements = await page.query_selector_all('[data-testid="tweetText"]')
            if tweet_elements:
                texts = []
                for elem in tweet_elements[:5]:
                    text = await elem.inner_text()
                    if text:
                        texts.append(text.strip())
                if texts:
                    return "\n\n".join(texts)

            # 2. 아티클 본문 셀렉터 시도
            article_selectors = [
                '[data-testid="article"] [dir="auto"]',
                '[role="article"] p',
                'article p',
                '[data-testid="cellInnerDiv"] [dir="auto"]',
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
                        logger.info(f"[TwitterScraper] 아티클 텍스트 추출: {selector}, {len(texts)}개")
                        return "\n\n".join(texts)

            # 3. fallback: 메인 콘텐츠 영역에서 텍스트 추출
            text = await page.evaluate(
                """
                () => {
                    const main = document.querySelector('main') ||
                                 document.querySelector('[role="main"]') ||
                                 document.body;

                    const clone = main.cloneNode(true);

                    const removeSelectors = [
                        'script', 'style', 'noscript', 'nav', 'header', 'footer',
                        '[role="navigation"]', '[data-testid="sidebarColumn"]',
                        '[data-testid="primaryColumn"] > div:first-child'
                    ];
                    removeSelectors.forEach(sel => {
                        clone.querySelectorAll(sel).forEach(el => el.remove());
                    });

                    const text = clone.innerText || clone.textContent || '';
                    return text.trim();
                }
            """
            )
            return text[:5000] if text else ""

        except Exception as e:
            logger.error(f"[TwitterScraper] 텍스트 추출 실패: {e}")
            return ""

    async def _load_cookies(self, context):
        """저장된 쿠키 로드"""
        cookies_path = self.cookies_dir / "twitter_cookies.json"
        if cookies_path.exists():
            try:
                with open(cookies_path) as f:
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
            await page.wait_for_timeout(3000)

            # 이메일/사용자명 입력
            username_input = await page.wait_for_selector(
                'input[autocomplete="username"]', timeout=15000
            )
            await username_input.fill(self.twitter_username)
            await page.wait_for_timeout(500)

            # "다음" 버튼 클릭 (한국어/영어 모두 지원)
            next_selectors = [
                'button:has-text("Next")',
                'button:has-text("다음")',
                'div[role="button"]:has-text("Next")',
                'div[role="button"]:has-text("다음")',
                'button[type="button"]:not([data-testid])',
            ]
            next_button = None
            for selector in next_selectors:
                next_button = await page.query_selector(selector)
                if next_button:
                    logger.info(f"[TwitterScraper] 다음 버튼 발견: {selector}")
                    break

            if next_button:
                await next_button.click()
                await page.wait_for_timeout(2000)
            else:
                await username_input.press("Enter")
                await page.wait_for_timeout(2000)

            # 비밀번호 입력
            password_input = await page.wait_for_selector(
                'input[type="password"]', timeout=15000
            )
            await password_input.fill(self.twitter_password)
            await page.wait_for_timeout(500)

            # "로그인" 버튼 클릭 (한국어/영어 모두 지원)
            login_selectors = [
                'button[data-testid="LoginForm_Login_Button"]',
                'button:has-text("Log in")',
                'button:has-text("로그인")',
                'div[role="button"]:has-text("Log in")',
                'div[role="button"]:has-text("로그인")',
            ]
            login_button = None
            for selector in login_selectors:
                login_button = await page.query_selector(selector)
                if login_button:
                    logger.info(f"[TwitterScraper] 로그인 버튼 발견: {selector}")
                    break

            if login_button:
                await login_button.click()
                await page.wait_for_timeout(3000)
            else:
                await password_input.press("Enter")
                await page.wait_for_timeout(3000)

            # 로그인 성공 확인
            return await self._check_login_status(page)

        except Exception as e:
            logger.error(f"[TwitterScraper] 로그인 실패: {e}")
            return False


# 싱글톤 인스턴스
twitter_scraper = TwitterScraper()

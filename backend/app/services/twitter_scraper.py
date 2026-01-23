"""
Twitter/X 스크래핑 서비스

여러 방법으로 x.com의 컨텐츠를 추출합니다:
1. Twitter oEmbed API (우선 시도 - 로그인 불필요)
2. Playwright 브라우저 (fallback)

- 싱글톤 패턴으로 브라우저 인스턴스 관리
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
        # 일반 User-Agent (데스크톱)
        self.user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        # 모바일 User-Agent (아티클 접근용)
        self.mobile_user_agent = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
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
            # 1. FxTwitter API 시도 (로그인 불필요, 빠름)
            result = await self._scrape_via_fxtwitter(url)
            if result.success and result.content:
                # t.co 링크만 있고 아티클 URL이 있으면 Playwright로 재시도
                article_url = result.article_url
                if article_url:
                    logger.info(f"[TwitterScraper] X 아티클 발견, Playwright로 접근: {article_url}")
                    article_result = await self._scrape_internal(article_url)
                    # 아티클 콘텐츠가 제대로 추출되었는지 확인
                    if article_result.success and article_result.content:
                        if "이 페이지는 지원되지 않습니다" in article_result.content or \
                           "This page is not supported" in article_result.content:
                            # 웹에서 지원되지 않는 콘텐츠
                            result.og_description = f"X 아티클 (앱에서만 볼 수 있음): {article_url}"
                            logger.info("[TwitterScraper] X 아티클은 앱에서만 지원됩니다")
                        else:
                            # 원본 메타데이터 유지
                            article_result.og_title = result.og_title or article_result.og_title
                            return article_result
                return result

            # 2. Syndication API 시도
            result = await self._scrape_via_syndication(url)
            if result.success and result.content:
                # t.co 링크만 있고 아티클 URL이 있으면, 정규 트윗 URL로 접근
                article_url = result.article_url
                if article_url and result.screen_name and result.tweet_id:
                    # /i/article/ 대신 /username/status/ID 형식으로 접근
                    web_url = f"https://x.com/{result.screen_name}/status/{result.tweet_id}"
                    logger.info(f"[TwitterScraper] X 아티클 발견, 정규 트윗 URL로 접근: {web_url}")

                    article_result = await self._scrape_internal(web_url)
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
                            return article_result
                return result

            # 3. oEmbed API 시도
            result = await self._scrape_via_oembed(url)
            if result.success and result.content:
                return result

            # 4. 모든 API 실패 시 Playwright 사용 (로그인 후 접근)
            logger.info("[TwitterScraper] API 실패, Playwright로 재시도...")
            return await self._scrape_internal(url)

    def _extract_tweet_id(self, url: str) -> Optional[str]:
        """URL에서 트윗 ID 추출"""
        # /status/12345 형식에서 ID 추출
        match = re.search(r'/status/(\d+)', url)
        if match:
            return match.group(1)
        return None

    async def _scrape_via_syndication(self, url: str) -> TwitterScrapingResult:
        """Twitter syndication API를 통한 컨텐츠 추출"""
        start_time = time.time()
        result = TwitterScrapingResult()

        try:
            tweet_id = self._extract_tweet_id(url)
            if not tweet_id:
                logger.warning("[TwitterScraper] 트윗 ID 추출 실패")
                return result

            # syndication API 호출
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

                    # t.co 링크만 있는 경우 실제 URL 확인
                    if result.content and "t.co/" in result.content:
                        # t.co 링크 추출
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

                                # X 아티클인 경우 아티클 URL 저장 (나중에 Playwright로 접근)
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

    async def _scrape_via_fxtwitter(self, url: str) -> TwitterScrapingResult:
        """FxTwitter API를 통한 컨텐츠 추출"""
        start_time = time.time()
        result = TwitterScrapingResult()

        try:
            tweet_id = self._extract_tweet_id(url)
            if not tweet_id:
                return result

            # FxTwitter API 호출
            api_url = f"https://api.fxtwitter.com/status/{tweet_id}"

            headers = {
                "User-Agent": self.user_agent,
            }

            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(api_url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    tweet = data.get("tweet", {})

                    result.content = tweet.get("text", "")
                    author = tweet.get("author", {})
                    result.og_title = author.get("name", "")

                    media = tweet.get("media", {})
                    photos = media.get("photos", [])
                    if photos:
                        result.og_image = photos[0].get("url", "")

                    # 내용이 t.co 링크만 있는 경우
                    logger.info(f"[TwitterScraper] content 확인: '{result.content}'")
                    if result.content and "t.co/" in result.content:
                        tco_url = result.content.strip()

                        # t.co 링크를 따라가서 실제 URL 확인
                        try:
                            redirect_response = await client.head(
                                tco_url,
                                follow_redirects=True,
                                timeout=5.0
                            )
                            final_url = str(redirect_response.url)
                            logger.info(f"[TwitterScraper] t.co 리다이렉트: {tco_url} -> {final_url}")

                            # 최종 URL 정보 추가
                            result.og_description = f"링크: {final_url}"

                            # X.com 아티클 URL인 경우 별도 처리 필요
                            if "x.com" in final_url and "/i/" in final_url:
                                result.og_description = f"X 아티클 링크: {final_url}"

                        except Exception as e:
                            logger.warning(f"[TwitterScraper] t.co 리다이렉트 실패: {e}")

                        # quote 트윗이나 카드 정보 확인
                        quote = tweet.get("quote", {})
                        if quote:
                            quote_text = quote.get("text", "")
                            quote_author = quote.get("author", {}).get("name", "")
                            if quote_text:
                                result.content = f"{result.content}\n\n[인용]\n{quote_author}: {quote_text}"

                    result.success = bool(result.content)

                    logger.info(
                        f"[TwitterScraper] FxTwitter API 성공: content_length={len(result.content)}"
                    )
                else:
                    logger.warning(
                        f"[TwitterScraper] FxTwitter API 실패: status={response.status_code}"
                    )

        except Exception as e:
            logger.warning(f"[TwitterScraper] FxTwitter 실패: {e}")

        result.elapsed_time = time.time() - start_time
        return result

    async def _scrape_via_oembed(self, url: str) -> TwitterScrapingResult:
        """Twitter oEmbed API를 통한 컨텐츠 추출"""
        start_time = time.time()
        result = TwitterScrapingResult()

        try:
            # URL 정규화 (x.com -> twitter.com)
            normalized_url = url.replace("x.com", "twitter.com")

            # oEmbed API 호출
            oembed_url = f"https://publish.twitter.com/oembed?url={normalized_url}"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(oembed_url)

                if response.status_code == 200:
                    data = response.json()

                    # HTML에서 텍스트 추출
                    html = data.get("html", "")
                    # <blockquote> 태그 내용 추출
                    text_match = re.search(
                        r'<p[^>]*>(.*?)</p>',
                        html,
                        re.DOTALL | re.IGNORECASE
                    )
                    if text_match:
                        # HTML 태그 제거
                        text = re.sub(r'<[^>]+>', '', text_match.group(1))
                        text = text.strip()
                        result.content = text

                    result.og_title = data.get("author_name", "")
                    result.success = bool(result.content)

                    logger.info(
                        f"[TwitterScraper] oEmbed 성공: content_length={len(result.content)}"
                    )
                else:
                    logger.warning(
                        f"[TwitterScraper] oEmbed API 실패: status={response.status_code}"
                    )

        except Exception as e:
            logger.warning(f"[TwitterScraper] oEmbed 실패: {e}")

        result.elapsed_time = time.time() - start_time
        return result

    async def _scrape_internal(self, url: str) -> TwitterScrapingResult:
        """내부 스크래핑 로직 - 먼저 로그인 후 URL 접근"""
        start_time = time.time()
        result = TwitterScrapingResult()

        # 아티클 URL인 경우 모바일 UA 사용
        is_article = "/i/article/" in url
        user_agent = self.mobile_user_agent if is_article else self.user_agent
        viewport = {"width": 390, "height": 844} if is_article else {"width": 1280, "height": 720}

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                logger.info(f"[TwitterScraper] 브라우저 시작 (headless={self.headless}, is_article={is_article})")

                # Chromium 사용 (Firefox는 X 아티클 미지원)
                browser = await p.chromium.launch(headless=self.headless)

                context = await browser.new_context(
                    user_agent=user_agent,
                    viewport=viewport,
                    is_mobile=is_article,
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

                # 4. 아티클/스레드 콘텐츠 확인
                tweet_elements = await page.query_selector_all('[data-testid="tweetText"]')
                logger.info(f"[TwitterScraper] 트윗 요소 발견: {len(tweet_elements)}개")

                # 아티클인 경우 추가 대기 및 다른 셀렉터 시도
                if not tweet_elements:
                    await page.wait_for_timeout(3000)

                    # 아티클 콘텐츠 셀렉터 (여러 가지 시도)
                    article_selectors = [
                        '[data-testid="article"]',
                        '[role="article"]',
                        'article[data-testid]',
                        '.r-1oszu61',  # 아티클 본문 클래스
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
        """트윗/아티클 본문 텍스트 추출"""
        try:
            # 1. 트윗 텍스트 요소 찾기 (data-testid="tweetText")
            tweet_elements = await page.query_selector_all('[data-testid="tweetText"]')
            if tweet_elements:
                texts = []
                for elem in tweet_elements[:5]:  # 최대 5개
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
                    for elem in elements[:20]:  # 최대 20개
                        text = await elem.inner_text()
                        if text and len(text) > 10:  # 짧은 텍스트 제외
                            texts.append(text.strip())
                    if texts:
                        logger.info(f"[TwitterScraper] 아티클 텍스트 추출: {selector}, {len(texts)}개")
                        return "\n\n".join(texts)

            # 3. fallback: 메인 콘텐츠 영역에서 텍스트 추출
            text = await page.evaluate(
                """
                () => {
                    // 메인 콘텐츠 영역 찾기
                    const main = document.querySelector('main') ||
                                 document.querySelector('[role="main"]') ||
                                 document.body;

                    const clone = main.cloneNode(true);

                    // 불필요한 요소 제거
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
            return text[:5000] if text else ""  # 최대 5000자

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
                'button[type="button"]:not([data-testid])',  # 일반 버튼
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
                # Enter 키로 대체
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
                # Enter 키로 대체
                await password_input.press("Enter")
                await page.wait_for_timeout(3000)

            # 로그인 성공 확인
            return await self._check_login_status(page)

        except Exception as e:
            logger.error(f"[TwitterScraper] 로그인 실패: {e}")
            return False


# 싱글톤 인스턴스
twitter_scraper = TwitterScraper()

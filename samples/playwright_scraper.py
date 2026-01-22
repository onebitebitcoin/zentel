#!/usr/bin/env python3
"""
Playwright 웹 컨텐츠 추출 샘플

동적 웹사이트의 컨텐츠를 추출하는 샘플 스크립트입니다.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# .env 파일 로드
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class PlaywrightScraper:
    """Playwright를 사용한 웹 스크래퍼"""

    def __init__(self, timeout: int = 10000, cookies_dir: str = None, headless: bool = True):
        """
        초기화

        Args:
            timeout: 페이지 로딩 타임아웃 (밀리초)
            cookies_dir: 쿠키 저장 디렉토리 (기본값: samples/)
            headless: 헤드리스 모드 사용 여부
        """
        self.timeout = timeout
        self.headless = headless
        self.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        # 쿠키 저장 경로 설정
        if cookies_dir is None:
            cookies_dir = Path(__file__).parent
        self.cookies_dir = Path(cookies_dir)
        self.cookies_dir.mkdir(exist_ok=True)

        # Twitter 로그인 정보 (환경 변수에서 읽기)
        self.twitter_username = os.getenv("TWITTER_USERNAME")
        self.twitter_password = os.getenv("TWITTER_PASSWORD")

    async def scrape(self, url: str) -> dict:
        """
        URL의 컨텐츠를 추출합니다.

        Args:
            url: 스크래핑할 URL

        Returns:
            dict: {
                "url": str,
                "og_metadata": dict,
                "content": str,
                "success": bool,
                "elapsed_time": str,
                "error": Optional[str]
            }
        """
        start_time = time.time()
        result = {
            "url": url,
            "og_metadata": {},
            "content": "",
            "success": False,
            "elapsed_time": "0s",
            "error": None,
        }

        try:
            # URL 유효성 검사
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid URL: {url}")

            # Twitter URL 확인
            is_twitter = self._is_twitter_url(url)

            async with async_playwright() as p:
                # 브라우저 시작 (Firefox 사용)
                print(f"[DEBUG] 브라우저 시작 (Firefox, headless={self.headless})...")
                browser = await p.firefox.launch(
                    headless=self.headless,
                )

                # 컨텍스트 생성 (User-Agent 설정)
                print("[DEBUG] 브라우저 컨텍스트 생성...")
                context = await browser.new_context(
                    user_agent=self.user_agent,
                    viewport={"width": 1280, "height": 720},
                )

                # Twitter URL인 경우 쿠키 로드
                if is_twitter:
                    print("[DEBUG] Twitter URL 감지. 쿠키 로드 시도...")
                    await self._load_cookies(context, "twitter_cookies.json")

                # 페이지 생성
                print("[DEBUG] 페이지 생성...")
                page = await context.new_page()

                # URL 로딩
                print(f"[DEBUG] URL 로딩 중: {url}")
                try:
                    await page.goto(url, timeout=self.timeout, wait_until="load")
                    print("[DEBUG] 페이지 로딩 완료")
                except Exception as e:
                    print(f"[ERROR] 페이지 로딩 실패: {str(e)}")
                    raise

                # Twitter인 경우 로그인 확인 및 로그인 처리
                if is_twitter:
                    is_logged_in = await self._check_twitter_login_status(page)
                    if not is_logged_in:
                        print("[INFO] Twitter 로그인 필요. 로그인 시도 중...")
                        login_success = await self._login_twitter(page)
                        if login_success:
                            print("[INFO] Twitter 로그인 성공!")
                            # 쿠키 저장
                            await self._save_cookies(context, "twitter_cookies.json")
                            # 원래 URL로 다시 이동
                            await page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
                        else:
                            result["error"] = "Twitter 로그인 실패"
                            await browser.close()
                            return result
                    else:
                        print("[INFO] 이미 Twitter에 로그인되어 있습니다.")

                    # 트윗 로딩 대기
                    await page.wait_for_timeout(2000)

                # OG 메타데이터 추출
                result["og_metadata"] = await self._extract_og_metadata(page)

                # 본문 텍스트 추출
                result["content"] = await self._extract_text_content(page)

                # 정리
                await browser.close()

                result["success"] = True

        except PlaywrightTimeout:
            result["error"] = f"Timeout: 페이지 로딩이 {self.timeout / 1000}초를 초과했습니다."
        except ValueError as e:
            result["error"] = str(e)
        except Exception as e:
            result["error"] = f"Unexpected error: {type(e).__name__}: {str(e)}"

        # 경과 시간 계산
        elapsed = time.time() - start_time
        result["elapsed_time"] = f"{elapsed:.2f}s"

        return result

    async def _extract_og_metadata(self, page) -> dict:
        """
        Open Graph 메타데이터를 추출합니다.

        Args:
            page: Playwright 페이지 객체

        Returns:
            dict: OG 메타데이터
        """
        metadata = {}

        og_tags = {
            "title": "og:title",
            "description": "og:description",
            "image": "og:image",
            "url": "og:url",
            "type": "og:type",
            "site_name": "og:site_name",
        }

        for key, property_name in og_tags.items():
            try:
                element = await page.query_selector(f'meta[property="{property_name}"]')
                if element:
                    content = await element.get_attribute("content")
                    if content:
                        metadata[key] = content
            except Exception:
                # 개별 태그 추출 실패는 무시
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

    async def _extract_text_content(self, page) -> str:
        """
        페이지의 본문 텍스트를 추출합니다.

        Args:
            page: Playwright 페이지 객체

        Returns:
            str: 본문 텍스트
        """
        try:
            # body 태그의 텍스트만 추출 (스크립트/스타일 제외)
            text = await page.evaluate("""
                () => {
                    // script, style, noscript 태그 제거
                    const clone = document.body.cloneNode(true);
                    const scripts = clone.querySelectorAll('script, style, noscript');
                    scripts.forEach(el => el.remove());

                    // 텍스트 추출 및 정리
                    const text = clone.innerText || clone.textContent || '';
                    return text.trim();
                }
            """)

            return text

        except Exception as e:
            return f"텍스트 추출 실패: {str(e)}"

    def _is_twitter_url(self, url: str) -> bool:
        """
        Twitter/X URL인지 확인합니다.

        Args:
            url: 확인할 URL

        Returns:
            bool: Twitter URL이면 True
        """
        parsed = urlparse(url)
        return parsed.netloc in ["twitter.com", "x.com", "www.twitter.com", "www.x.com"]

    async def _load_cookies(self, context, cookies_file: str):
        """
        저장된 쿠키를 로드합니다.

        Args:
            context: Playwright 컨텍스트
            cookies_file: 쿠키 파일 이름
        """
        cookies_path = self.cookies_dir / cookies_file
        if cookies_path.exists():
            try:
                with open(cookies_path, "r") as f:
                    cookies = json.load(f)
                await context.add_cookies(cookies)
                print(f"[INFO] 쿠키 로드 성공: {cookies_path}")
            except Exception as e:
                print(f"[WARNING] 쿠키 로드 실패: {str(e)}")

    async def _save_cookies(self, context, cookies_file: str):
        """
        세션 쿠키를 저장합니다.

        Args:
            context: Playwright 컨텍스트
            cookies_file: 쿠키 파일 이름
        """
        cookies_path = self.cookies_dir / cookies_file
        try:
            cookies = await context.cookies()
            with open(cookies_path, "w") as f:
                json.dump(cookies, f, indent=2)
            print(f"[INFO] 쿠키 저장 성공: {cookies_path}")
        except Exception as e:
            print(f"[WARNING] 쿠키 저장 실패: {str(e)}")

    async def _check_twitter_login_status(self, page) -> bool:
        """
        Twitter 로그인 상태를 확인합니다.

        Args:
            page: Playwright 페이지 객체

        Returns:
            bool: 로그인되어 있으면 True
        """
        try:
            # 로그인 버튼이 없으면 로그인된 상태
            login_button = await page.query_selector('a[href="/login"]')
            return login_button is None
        except Exception:
            return False

    async def _login_twitter(self, page) -> bool:
        """
        Twitter에 로그인합니다.

        Args:
            page: Playwright 페이지 객체

        Returns:
            bool: 로그인 성공 여부
        """
        if not self.twitter_username or not self.twitter_password:
            print("[ERROR] TWITTER_USERNAME 또는 TWITTER_PASSWORD 환경 변수가 설정되지 않았습니다.")
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
            login_button = await page.query_selector('button[data-testid="LoginForm_Login_Button"]')
            if not login_button:
                login_button = await page.query_selector('div[role="button"]:has-text("Log in")')
            if login_button:
                await login_button.click()
                await page.wait_for_timeout(3000)

            # 로그인 성공 확인
            is_logged_in = await self._check_twitter_login_status(page)
            return is_logged_in

        except Exception as e:
            print(f"[ERROR] 로그인 실패: {str(e)}")
            return False


async def main():
    """CLI 메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="Playwright 웹 컨텐츠 추출 샘플")
    parser.add_argument("--url", type=str, required=True, help="스크래핑할 URL")
    parser.add_argument(
        "--timeout",
        type=int,
        default=10000,
        help="타임아웃 (밀리초, 기본값: 10000)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="JSON 출력을 보기 좋게 포맷팅",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="헤드리스 모드 사용 (기본값: True)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_false",
        dest="headless",
        help="헤드리스 모드 비활성화 (디버깅용)",
    )

    args = parser.parse_args()

    # 스크래퍼 실행
    scraper = PlaywrightScraper(timeout=args.timeout, headless=args.headless)
    result = await scraper.scrape(args.url)

    # JSON 출력
    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, indent=indent))

    # 에러 발생 시 exit code 1
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())

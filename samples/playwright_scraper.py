#!/usr/bin/env python3
"""
Playwright 웹 컨텐츠 추출 샘플

동적 웹사이트의 컨텐츠를 추출하는 샘플 스크립트입니다.
"""

import asyncio
import json
import sys
import time
from urllib.parse import urlparse

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout


class PlaywrightScraper:
    """Playwright를 사용한 웹 스크래퍼"""

    def __init__(self, timeout: int = 10000):
        """
        초기화

        Args:
            timeout: 페이지 로딩 타임아웃 (밀리초)
        """
        self.timeout = timeout
        self.user_agent = "Mozilla/5.0 (compatible; Zentel/2.0; +https://zentel.app)"

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

            async with async_playwright() as p:
                # 브라우저 시작 (헤드리스 모드)
                browser = await p.chromium.launch(headless=True)

                # 컨텍스트 생성 (User-Agent 설정)
                context = await browser.new_context(user_agent=self.user_agent)

                # 페이지 생성
                page = await context.new_page()

                # URL 로딩
                await page.goto(url, timeout=self.timeout, wait_until="networkidle")

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

    args = parser.parse_args()

    # 스크래퍼 실행
    scraper = PlaywrightScraper(timeout=args.timeout)
    result = await scraper.scrape(args.url)

    # JSON 출력
    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, indent=indent))

    # 에러 발생 시 exit code 1
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())

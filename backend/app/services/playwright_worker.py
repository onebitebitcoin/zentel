#!/usr/bin/env python3
"""
Playwright 워커 스크립트 (동기 API)

별도 프로세스에서 실행되어 Twitter 콘텐츠를 스크래핑합니다.
결과는 JSON으로 stdout에 출력됩니다.

Usage:
    python playwright_worker.py <url> [timeout_ms]
"""

import json
import sys
import time


def scrape_twitter(url: str, timeout: int = 90000) -> dict:
    """Twitter URL 스크래핑 (동기 API)"""
    result = {
        "content": "",
        "og_title": None,
        "og_image": None,
        "og_description": None,
        "success": False,
        "error": None,
    }

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            # Firefox 사용 (Chromium은 X.com에서 봇 감지로 차단됨)
            browser = p.firefox.launch(headless=True)
            page = browser.new_page()

            # 대상 URL로 이동
            page.goto(url, timeout=timeout, wait_until="load")
            page.wait_for_timeout(3000)

            # OG 메타데이터 추출
            og_tags = {"title": "og:title", "description": "og:description", "image": "og:image"}
            for key, prop in og_tags.items():
                try:
                    elem = page.query_selector(f'meta[property="{prop}"]')
                    if elem:
                        content = elem.get_attribute("content")
                        if content:
                            result[f"og_{key}"] = content
                except Exception:
                    pass

            # 아티클 본문 추출 시도
            article_content = ""
            try:
                links = page.query_selector_all('a[href*="/article/"]')
                article_url = None
                for link in links:
                    href = link.get_attribute("href")
                    if href and "/article/" in href and "support.x.com" not in href:
                        article_url = f"https://x.com{href}" if href.startswith("/") else href
                        break

                if article_url:
                    page.goto(article_url, wait_until="domcontentloaded", timeout=20000)
                    time.sleep(5)

                    main = page.query_selector("main")
                    if main:
                        text = main.inner_text()
                        if text:
                            lines = [line.strip() for line in text.strip().split("\n") if line.strip() and len(line.strip()) > 10]
                            if lines:
                                article_content = "\n\n".join(lines)
            except Exception:
                pass

            if article_content and len(article_content) > 200:
                result["content"] = article_content
            else:
                # 일반 트윗 텍스트 추출
                tweet_elements = page.query_selector_all('[data-testid="tweetText"]')
                if tweet_elements:
                    texts = []
                    for elem in tweet_elements[:5]:
                        text = elem.inner_text()
                        if text:
                            texts.append(text.strip())
                    if texts:
                        result["content"] = "\n\n".join(texts)

                # Fallback: main 영역 텍스트
                if not result["content"]:
                    text = page.evaluate("""
                        () => {
                            const main = document.querySelector('main') || document.body;
                            const clone = main.cloneNode(true);
                            ['script', 'style', 'noscript', 'nav', 'header', 'footer']
                                .forEach(sel => clone.querySelectorAll(sel).forEach(el => el.remove()));
                            return (clone.innerText || '').trim();
                        }
                    """)
                    result["content"] = text[:10000] if text else ""

            browser.close()
            result["success"] = True

    except Exception as e:
        result["error"] = str(e)

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "URL required", "success": False}))
        sys.exit(1)

    url = sys.argv[1]
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 90000

    result = scrape_twitter(url, timeout)
    print(json.dumps(result, ensure_ascii=False))

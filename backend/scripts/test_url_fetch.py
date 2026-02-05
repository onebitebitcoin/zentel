"""
URL 본문 추출 테스트 스크립트

사용법:
    python scripts/test_url_fetch.py [URL]
"""

import asyncio
import re
import sys
from typing import Optional, Tuple

import httpx
import trafilatura

# 테스트 URL
DEFAULT_URL = "https://github.com/dathonohm/bips/blob/reduced-data/bip-0110.mediawiki"
MIN_CONTENT_LENGTH = 200

# GitHub blob URL 패턴
GITHUB_BLOB_PATTERN = re.compile(
    r"^https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$"
)


def convert_github_blob_to_raw(url: str) -> Optional[str]:
    """GitHub blob → raw URL 변환"""
    match = GITHUB_BLOB_PATTERN.match(url)
    if match:
        owner, repo, branch, path = match.groups()
        return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    return None


def extract_text_from_html(html: str) -> Tuple[Optional[str], str]:
    """HTML에서 본문 추출"""
    content = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        no_fallback=False,
    )

    if content and len(content) >= MIN_CONTENT_LENGTH:
        return content, "trafilatura"

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        fallback = soup.get_text(separator="\n", strip=True)
        if fallback and len(fallback) >= MIN_CONTENT_LENGTH:
            return fallback, "beautifulsoup"
    except Exception:
        pass

    return content, "trafilatura (부실)"


async def fetch_with_playwright(url: str) -> Optional[str]:
    """Playwright로 JS 렌더링"""
    try:
        from playwright.async_api import async_playwright

        print("    [Playwright] JS 렌더링 시작...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(1)
            html = await page.content()
            await browser.close()

            print(f"    [Playwright] 렌더링 완료: {len(html):,} bytes")
            return html

    except Exception as e:
        print(f"    [Playwright] 실패: {e}")
        return None


async def main():
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL

    print("=" * 70)
    print("URL 본문 추출 테스트")
    print("=" * 70)

    print("\n[1] 입력 URL")
    print(f"    {url}\n")

    # GitHub blob URL 체크
    github_raw_url = convert_github_blob_to_raw(url)

    if github_raw_url:
        # GitHub blob → raw URL
        print("[2] GitHub blob URL 감지!")
        print(f"    → raw URL: {github_raw_url}")

        print("\n[3] Raw 텍스트 가져오기...")
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(github_raw_url, follow_redirects=True)
            print(f"    - Status: {response.status_code}")
            print(f"    - Content-Type: {response.headers.get('content-type', 'N/A')}")

        content = response.text
        method = "raw 텍스트"

    else:
        # 일반 URL
        print("[2] 일반 URL → 정적 HTTP 요청...")
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 MyRottenApple/1.0"},
                follow_redirects=True,
            )
            print(f"    - Status: {response.status_code}")
            print(f"    - HTML 길이: {len(response.text):,} bytes")

        html = response.text

        print("\n[3] 정적 HTML 본문 추출...")
        content, method = extract_text_from_html(html)
        print(f"    - 방식: {method}")
        print(f"    - 추출 길이: {len(content) if content else 0} chars")

        # 결과 부실 시 Playwright
        if not content or len(content) < MIN_CONTENT_LENGTH:
            print("\n[4] 정적 추출 부실 → Playwright 시도...")
            rendered_html = await fetch_with_playwright(url)
            if rendered_html:
                rendered_content, rendered_method = extract_text_from_html(rendered_html)
                print(f"    - 렌더링 후: {rendered_method}, {len(rendered_content) if rendered_content else 0} chars")
                if rendered_content and len(rendered_content) > len(content or ""):
                    content = rendered_content
                    method = f"Playwright + {rendered_method}"
        else:
            print("\n[4] 정적 추출 충분 → Playwright 스킵")

    # 결과 출력
    print("\n[5] 최종 결과:")
    print(f"    - 방식: {method}")
    print(f"    - 길이: {len(content) if content else 0} chars")

    print("\n[6] 추출된 본문 (처음 2000자):")
    print("-" * 70)
    preview = (content[:2000] if content else "(없음)")
    print(preview)
    if content and len(content) > 2000:
        print(f"\n... (총 {len(content):,}자 중 2000자만 표시)")
    print("-" * 70)

    # 파일 저장
    output_file = "scripts/test_url_fetch_result.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"URL: {url}\n")
        f.write(f"방식: {method}\n")
        f.write(f"길이: {len(content) if content else 0} chars\n")
        f.write("=" * 70 + "\n\n")
        f.write(content or "(추출 실패)")

    print(f"\n[7] 전체 내용 저장: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())

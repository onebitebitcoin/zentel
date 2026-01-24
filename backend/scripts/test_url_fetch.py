"""
URL 본문 추출 테스트 스크립트

사용법:
    python scripts/test_url_fetch.py
"""

import asyncio
import re
import httpx
import trafilatura

TEST_URL = "https://github.com/dathonohm/bips/blob/reduced-data/bip-0110.mediawiki"

# GitHub blob URL 패턴
GITHUB_BLOB_PATTERN = re.compile(
    r"^https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$"
)


def convert_github_blob_to_raw(url: str):
    """GitHub blob → raw URL 변환"""
    match = GITHUB_BLOB_PATTERN.match(url)
    if match:
        owner, repo, branch, path = match.groups()
        return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
    return None


async def main():
    print("=" * 70)
    print("URL 본문 추출 테스트")
    print("=" * 70)

    print(f"\n[1] 입력 URL")
    print(f"    {TEST_URL}\n")

    # Step 1: GitHub blob → raw 변환
    raw_url = convert_github_blob_to_raw(TEST_URL)
    is_raw = raw_url is not None
    fetch_url = raw_url or TEST_URL

    print(f"[2] GitHub blob 감지: {is_raw}")
    if is_raw:
        print(f"    → raw URL로 변환: {fetch_url}")

    # Step 2: HTTP 요청
    print(f"\n[3] HTTP 요청...")
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            fetch_url,
            headers={"User-Agent": "Mozilla/5.0 Zentel/1.0"},
            follow_redirects=True,
        )
        print(f"    - Status: {response.status_code}")
        print(f"    - Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"    - 응답 길이: {len(response.text):,} bytes")

    text = response.text

    # Step 3: 본문 추출
    print(f"\n[4] 본문 추출...")
    if is_raw:
        # raw 텍스트는 그대로 사용
        content = text
        print(f"    - 방식: raw 텍스트 그대로 사용")
    else:
        # trafilatura 사용
        content = trafilatura.extract(
            text,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
        )
        print(f"    - 방식: trafilatura")
        if not content:
            print(f"    - trafilatura 실패, BeautifulSoup fallback")
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            content = soup.get_text(separator="\n", strip=True)

    print(f"    - 추출된 본문 길이: {len(content):,} chars")

    # Step 4: 추출된 내용 미리보기
    print(f"\n[5] 추출된 본문 (처음 3000자):")
    print("-" * 70)
    preview = content[:3000] if content else "(없음)"
    print(preview)
    if len(content) > 3000:
        print(f"\n... (총 {len(content):,}자 중 3000자만 표시)")
    print("-" * 70)

    # Step 5: 전체 내용 파일 저장
    output_file = "scripts/test_url_fetch_result.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"원본 URL: {TEST_URL}\n")
        f.write(f"변환 URL: {fetch_url}\n")
        f.write(f"본문 길이: {len(content):,} chars\n")
        f.write("=" * 70 + "\n\n")
        f.write(content or "(추출 실패)")

    print(f"\n[6] 전체 내용 저장: {output_file}")

    # Step 6: 다음 단계 설명
    print(f"\n[7] 이후 시스템 처리 과정:")
    print(f"    1. analysis_service → fetched_content에 저장")
    print(f"    2. LLM 호출 → context 추출 (1줄 요약)")
    print(f"    3. LLM 호출 → 언어감지 + 번역 + 하이라이트")
    print(f"    4. DB 저장 → 프론트엔드 렌더링")


if __name__ == "__main__":
    asyncio.run(main())

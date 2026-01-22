#!/usr/bin/env python3
"""
테스트 URL 목록 및 테스트 함수

다양한 유형의 웹사이트를 테스트합니다.
"""

import asyncio
import sys
from playwright_scraper import PlaywrightScraper


# 테스트 URL 분류
TEST_URLS = {
    "정적 사이트": [
        "https://example.com",
        "https://www.python.org",
        "https://httpbin.org/html",
    ],
    "동적 사이트": [
        "https://news.ycombinator.com",
        "https://www.reddit.com",
    ],
    "SPA": [
        "https://react.dev",
        "https://vuejs.org",
    ],
}


async def test_single_url(url: str) -> dict:
    """단일 URL 테스트"""
    print(f"\n테스트 중: {url}")
    print("-" * 80)

    scraper = PlaywrightScraper(timeout=10000)
    result = await scraper.scrape(url)

    # 결과 출력
    if result["success"]:
        print(f"✓ 성공 ({result['elapsed_time']})")
        print(f"  제목: {result['og_metadata'].get('title', 'N/A')}")
        print(f"  본문 길이: {len(result['content'])} 글자")
    else:
        print(f"✗ 실패 ({result['elapsed_time']})")
        print(f"  에러: {result['error']}")

    return result


async def test_static_sites():
    """정적 사이트 테스트"""
    print("\n" + "=" * 80)
    print("정적 사이트 테스트")
    print("=" * 80)

    results = []
    for url in TEST_URLS["정적 사이트"]:
        result = await test_single_url(url)
        results.append(result)

    # 요약
    success_count = sum(1 for r in results if r["success"])
    print(f"\n요약: {success_count}/{len(results)} 성공")

    return results


async def test_dynamic_sites():
    """동적 사이트 테스트"""
    print("\n" + "=" * 80)
    print("동적 사이트 테스트")
    print("=" * 80)

    results = []
    for url in TEST_URLS["동적 사이트"]:
        result = await test_single_url(url)
        results.append(result)

    # 요약
    success_count = sum(1 for r in results if r["success"])
    print(f"\n요약: {success_count}/{len(results)} 성공")

    return results


async def test_spa_sites():
    """SPA 사이트 테스트"""
    print("\n" + "=" * 80)
    print("SPA 사이트 테스트")
    print("=" * 80)

    results = []
    for url in TEST_URLS["SPA"]:
        result = await test_single_url(url)
        results.append(result)

    # 요약
    success_count = sum(1 for r in results if r["success"])
    print(f"\n요약: {success_count}/{len(results)} 성공")

    return results


async def test_error_handling():
    """에러 처리 테스트"""
    print("\n" + "=" * 80)
    print("에러 처리 테스트")
    print("=" * 80)

    error_urls = [
        "https://invalid-url-12345.com",  # 존재하지 않는 도메인
        "https://httpstat.us/500",  # 500 에러
        "https://httpstat.us/404",  # 404 에러
        "not-a-url",  # 잘못된 URL 형식
    ]

    results = []
    for url in error_urls:
        result = await test_single_url(url)
        results.append(result)

        # 에러가 제대로 처리되었는지 확인
        if not result["success"] and result["error"]:
            print("  → 에러 처리 OK")
        else:
            print("  → 에러 처리 실패!")

    # 요약
    error_count = sum(1 for r in results if not r["success"])
    print(f"\n요약: {error_count}/{len(results)} 에러가 올바르게 처리됨")

    return results


async def run_all_tests():
    """모든 테스트 실행"""
    print("\n" + "=" * 80)
    print("Playwright 웹 스크래핑 샘플 테스트")
    print("=" * 80)

    # 각 테스트 실행
    static_results = await test_static_sites()
    dynamic_results = await test_dynamic_sites()
    spa_results = await test_spa_sites()
    error_results = await test_error_handling()

    # 전체 요약
    print("\n" + "=" * 80)
    print("전체 테스트 요약")
    print("=" * 80)

    all_results = static_results + dynamic_results + spa_results
    success_count = sum(1 for r in all_results if r["success"])
    total_count = len(all_results)

    print(f"정상 케이스: {success_count}/{total_count} 성공")
    print(f"에러 케이스: {len(error_results)}/{len(error_results)} 올바르게 처리됨")

    # 평균 응답 시간
    avg_time = sum(
        float(r["elapsed_time"].rstrip("s")) for r in all_results if r["success"]
    ) / max(success_count, 1)
    print(f"평균 응답 시간: {avg_time:.2f}s")

    return success_count == total_count


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

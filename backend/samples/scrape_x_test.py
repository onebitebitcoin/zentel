#!/usr/bin/env python3
"""
X 스크래핑 테스트 스크립트

사용법:
    python -m samples.scrape_x_test <URL>
    python -m samples.scrape_x_test https://x.com/user/status/123456

환경변수 (선택):
    TWITTER_USERNAME: X 로그인 사용자명
    TWITTER_PASSWORD: X 로그인 비밀번호
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.twitter_scraper import TwitterScraper, TwitterScrapingResult

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def print_result(result: TwitterScrapingResult, url: str, method: str):
    """결과를 테이블 형식으로 출력"""
    print("\n" + "=" * 60)
    print("X 스크래핑 결과")
    print("=" * 60)

    # 기본 정보
    print(f"{'URL':<15}: {url}")
    print(f"{'트윗 ID':<15}: {result.tweet_id or 'N/A'}")
    print(f"{'작성자':<15}: {result.screen_name or 'N/A'}")
    print(f"{'추출 방식':<15}: {method}")
    print(f"{'소요 시간':<15}: {result.elapsed_time:.2f}초")
    print(f"{'성공 여부':<15}: {'성공' if result.success else '실패'}")

    if result.error:
        print(f"{'에러':<15}: {result.error}")

    print("-" * 60)

    # OG 메타데이터
    print("OG 메타데이터:")
    print(f"  {'title':<12}: {result.og_title or 'N/A'}")
    print(f"  {'description':<12}: {(result.og_description or 'N/A')[:100]}")
    print(f"  {'image':<12}: {result.og_image or 'N/A'}")

    if result.article_url:
        print(f"  {'article_url':<12}: {result.article_url}")

    print("-" * 60)

    # 콘텐츠
    print("콘텐츠:")
    content = result.content or ""
    print(f"  길이: {len(content)}자")

    if content:
        # 처음 500자만 출력
        preview = content[:500]
        if len(content) > 500:
            preview += "..."
        print(f"  미리보기:\n{'-' * 40}")
        for line in preview.split("\n"):
            print(f"  {line}")
        print(f"{'-' * 40}")

    print("=" * 60)


async def test_syndication_only(scraper: TwitterScraper, url: str):
    """Syndication API만 테스트"""
    logger.info("Syndication API 테스트 시작...")
    result = await scraper._scrape_via_syndication(url)
    print_result(result, url, "Syndication API")
    return result


async def test_playwright_only(scraper: TwitterScraper, url: str):
    """Playwright만 테스트"""
    logger.info("Playwright 테스트 시작...")
    result = await scraper._scrape_via_playwright(url)
    print_result(result, url, "Playwright")
    return result


async def test_full_scrape(scraper: TwitterScraper, url: str):
    """전체 스크래핑 테스트 (Syndication -> Playwright fallback)"""
    logger.info("전체 스크래핑 테스트 시작...")
    result = await scraper.scrape(url)

    # 어떤 방식으로 성공했는지 추정
    if result.success:
        if result.elapsed_time < 2.0:
            method = "Syndication API"
        else:
            method = "Playwright (fallback)"
    else:
        method = "실패"

    print_result(result, url, method)
    return result


async def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n사용법: python -m samples.scrape_x_test <URL>")
        print("\n예시:")
        print("  python -m samples.scrape_x_test https://x.com/elonmusk/status/123456")
        sys.exit(1)

    url = sys.argv[1]

    # 추가 옵션 파싱
    mode = "full"  # full, syndication, playwright
    if len(sys.argv) > 2:
        mode = sys.argv[2]

    scraper = TwitterScraper(headless=True)

    # URL 검증
    if not scraper.is_twitter_url(url):
        logger.error(f"유효한 X/Twitter URL이 아닙니다: {url}")
        sys.exit(1)

    logger.info(f"URL: {url}")
    logger.info(f"모드: {mode}")

    if mode == "syndication":
        await test_syndication_only(scraper, url)
    elif mode == "playwright":
        await test_playwright_only(scraper, url)
    else:
        # 전체 테스트
        print("\n[1/3] Syndication API 테스트")
        syn_result = await test_syndication_only(scraper, url)

        print("\n[2/3] Playwright 테스트")
        pw_result = await test_playwright_only(scraper, url)

        print("\n[3/3] 전체 스크래핑 테스트 (자동 fallback)")
        await test_full_scrape(scraper, url)

        # 비교 요약
        print("\n" + "=" * 60)
        print("비교 요약")
        print("=" * 60)
        print(f"{'방식':<20} {'성공':<8} {'콘텐츠 길이':<12} {'소요 시간':<10}")
        print("-" * 60)
        print(
            f"{'Syndication API':<20} "
            f"{'O' if syn_result.success else 'X':<8} "
            f"{len(syn_result.content or ''):<12} "
            f"{syn_result.elapsed_time:.2f}초"
        )
        print(
            f"{'Playwright':<20} "
            f"{'O' if pw_result.success else 'X':<8} "
            f"{len(pw_result.content or ''):<12} "
            f"{pw_result.elapsed_time:.2f}초"
        )
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

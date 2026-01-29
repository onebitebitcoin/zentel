"""
X 링크 스크래핑 테스트
"""
import asyncio
import logging
import sys

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Backend 경로 추가
sys.path.insert(0, 'backend')

from app.services.twitter_scraper import twitter_scraper


async def test_twitter_url(url: str):
    """Twitter URL 스크래핑 테스트"""
    print(f"\n{'='*80}")
    print(f"테스트 URL: {url}")
    print(f"{'='*80}\n")

    # Twitter URL 확인
    is_twitter = twitter_scraper.is_twitter_url(url)
    print(f"✅ Twitter URL 확인: {is_twitter}")

    if not is_twitter:
        print("❌ Twitter URL이 아닙니다.")
        return

    # 스크래핑 시작
    print("\n🔍 스크래핑 시작...\n")
    result = await twitter_scraper.scrape(url)

    # 결과 출력
    print(f"\n{'='*80}")
    print(f"결과")
    print(f"{'='*80}")
    print(f"성공: {result.success}")
    print(f"에러: {result.error}")
    print(f"경과 시간: {result.elapsed_time:.2f}초")
    print(f"콘텐츠 길이: {len(result.content)}자")
    print(f"OG 제목: {result.og_title}")
    print(f"OG 이미지: {result.og_image}")
    print(f"OG 설명: {result.og_description}")
    print(f"아티클 URL: {result.article_url}")
    print(f"스크린네임: {result.screen_name}")
    print(f"트윗 ID: {result.tweet_id}")
    print(f"\n{'='*80}")
    print(f"콘텐츠 미리보기 (처음 500자)")
    print(f"{'='*80}")
    print(result.content[:500])
    print(f"{'='*80}\n")


async def main():
    """메인 함수"""
    test_url = "https://x.com/i/status/2016556592561574118"

    try:
        await test_twitter_url(test_url)
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

"""
Twitter/X 스크래핑 서비스 (오케스트레이션)

Unix Philosophy:
- Modularity: 작은 모듈들을 조합
- Simplicity: 오케스트레이션 로직만 담당
- Composition: 다른 모듈과 연결되도록 설계
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from app.services.twitter_playwright import PlaywrightResult, TwitterPlaywrightScraper
from app.services.twitter_syndication import fetch_tweet_metadata
from app.services.twitter_url_parser import build_tweet_url, is_twitter_url

logger = logging.getLogger(__name__)

# 동시 요청 제한
MAX_CONCURRENT_REQUESTS = 2
_semaphore: Optional[asyncio.Semaphore] = None


def _get_semaphore() -> asyncio.Semaphore:
    """Semaphore 인스턴스 (Lazy initialization)"""
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
    article_url: Optional[str] = None
    screen_name: Optional[str] = None
    tweet_id: Optional[str] = None


class TwitterScraper:
    """
    Twitter/X 스크래핑 서비스

    1. Syndication API로 메타데이터 추출
    2. 실패 시 Playwright로 브라우저 스크래핑
    """

    def __init__(
        self,
        timeout: int = 30000,
        cookies_dir: Optional[str] = None,
        headless: bool = True,
    ):
        self.playwright_scraper = TwitterPlaywrightScraper(
            timeout=timeout,
            cookies_dir=cookies_dir,
            headless=headless,
        )

    def is_twitter_url(self, url: str) -> bool:
        """Twitter/X URL인지 확인"""
        return is_twitter_url(url)

    async def scrape(self, url: str) -> TwitterScrapingResult:
        """
        Twitter URL 콘텐츠 추출

        Args:
            url: 스크래핑할 URL

        Returns:
            TwitterScrapingResult
        """
        logger.info(f"[TwitterScraper] 스크래핑 시작: {url}")
        semaphore = _get_semaphore()
        async with semaphore:
            # 1단계: Syndication API 시도
            logger.info("[TwitterScraper] 1단계: Syndication API 호출")
            syndication_result = await fetch_tweet_metadata(url)
            logger.info(
                f"[TwitterScraper] Syndication 결과: success={syndication_result.success}, "
                f"content_len={len(syndication_result.content)}, "
                f"screen_name={syndication_result.screen_name}, "
                f"tweet_id={syndication_result.tweet_id}, "
                f"article_url={syndication_result.article_url}, "
                f"has_note_tweet={syndication_result.has_note_tweet}"
            )

            if syndication_result.success and syndication_result.content:
                result = self._convert_syndication_result(syndication_result)
                logger.info(f"[TwitterScraper] Syndication 성공, content: {result.content[:100]}...")

                # 아티클 URL이 있거나 긴 트윗(note_tweet)인 경우 Playwright로 전체 내용 추출
                needs_playwright = (
                    (result.article_url and result.screen_name and result.tweet_id)
                    or syndication_result.has_note_tweet
                )

                if needs_playwright and result.screen_name and result.tweet_id:
                    reason = "아티클 URL" if result.article_url else "긴 트윗(note_tweet)"
                    logger.info(f"[TwitterScraper] {reason} 감지, Playwright로 전체 내용 추출 시도")
                    full_content_result = await self._fetch_full_content(result)
                    if full_content_result:
                        logger.info(f"[TwitterScraper] 전체 내용 추출 성공: {len(full_content_result.content)}자")
                        return full_content_result
                    else:
                        logger.warning("[TwitterScraper] 전체 내용 추출 실패, Syndication 결과 사용")

                logger.info(f"[TwitterScraper] 최종 반환: {len(result.content)}자")
                return result

            # 2단계: Playwright 폴백
            logger.info("[TwitterScraper] 2단계: Syndication 실패, Playwright로 재시도...")
            playwright_result = await self.playwright_scraper.scrape(url)
            logger.info(
                f"[TwitterScraper] Playwright 결과: success={playwright_result.success}, "
                f"content_len={len(playwright_result.content)}, error={playwright_result.error}"
            )
            return self._convert_playwright_result(playwright_result)

    async def _fetch_full_content(
        self, result: TwitterScrapingResult
    ) -> Optional[TwitterScrapingResult]:
        """Playwright로 전체 콘텐츠 추출 (아티클 또는 긴 트윗)"""
        web_url = build_tweet_url(result.screen_name, result.tweet_id)
        logger.info(f"[TwitterScraper] 정규 URL로 전체 내용 추출: {web_url}")

        playwright_result = await self.playwright_scraper.scrape(web_url)

        if not playwright_result.success or not playwright_result.content:
            return None

        # 지원되지 않는 콘텐츠 체크
        unsupported_texts = ["이 페이지는 지원되지 않습니다", "This page is not supported"]
        if any(t in playwright_result.content for t in unsupported_texts):
            result.og_description = f"X 아티클: {result.article_url}"
            logger.info("[TwitterScraper] X 아티클은 앱에서만 지원됩니다")
            return None

        # 성공
        new_result = self._convert_playwright_result(playwright_result)
        new_result.og_title = result.og_title or new_result.og_title
        new_result.og_description = f"아티클: {result.article_url}"
        return new_result

    def _convert_syndication_result(self, syn_result) -> TwitterScrapingResult:
        """Syndication 결과를 공통 결과로 변환"""
        return TwitterScrapingResult(
            content=syn_result.content,
            og_title=syn_result.og_title,
            og_image=syn_result.og_image,
            og_description=syn_result.og_description,
            success=syn_result.success,
            elapsed_time=syn_result.elapsed_time,
            article_url=syn_result.article_url,
            screen_name=syn_result.screen_name,
            tweet_id=syn_result.tweet_id,
        )

    def _convert_playwright_result(self, pw_result: PlaywrightResult) -> TwitterScrapingResult:
        """Playwright 결과를 공통 결과로 변환"""
        return TwitterScrapingResult(
            content=pw_result.content,
            og_title=pw_result.og_title,
            og_image=pw_result.og_image,
            og_description=pw_result.og_description,
            success=pw_result.success,
            error=pw_result.error,
            elapsed_time=pw_result.elapsed_time,
        )


# 싱글톤 인스턴스
twitter_scraper = TwitterScraper()

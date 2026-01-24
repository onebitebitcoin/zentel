"""
Twitter Syndication API 클라이언트

Unix Philosophy: Separation - 정책과 메커니즘 분리
- Syndication API를 통한 메타데이터 추출만 담당
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Optional

import httpx

from app.services.twitter_url_parser import extract_tweet_id
from app.utils import DEFAULT_USER_AGENT

logger = logging.getLogger(__name__)


@dataclass
class SyndicationResult:
    """Syndication API 결과"""

    content: str = ""
    og_title: Optional[str] = None
    og_image: Optional[str] = None
    og_description: Optional[str] = None
    screen_name: Optional[str] = None
    tweet_id: Optional[str] = None
    article_url: Optional[str] = None
    success: bool = False
    elapsed_time: float = 0.0


async def fetch_tweet_metadata(url: str) -> SyndicationResult:
    """
    Syndication API를 통해 트윗 메타데이터 추출

    Args:
        url: Twitter URL

    Returns:
        SyndicationResult
    """
    start_time = time.time()
    result = SyndicationResult()
    logger.info(f"[Syndication] 시작: {url}")

    tweet_id = extract_tweet_id(url)
    if not tweet_id:
        logger.warning(f"[Syndication] 트윗 ID 추출 실패: {url}")
        return result

    result.tweet_id = tweet_id
    logger.info(f"[Syndication] 트윗 ID: {tweet_id}")

    try:
        api_url = f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&token=x"
        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "application/json",
        }
        logger.info(f"[Syndication] API 호출: {api_url}")

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(api_url, headers=headers)
            logger.info(f"[Syndication] API 응답: status={response.status_code}")

            if response.status_code != 200:
                logger.warning(f"[Syndication] API 실패: status={response.status_code}, body={response.text[:200]}")
                result.elapsed_time = time.time() - start_time
                return result

            data = response.json()
            logger.info(f"[Syndication] JSON 파싱 성공, keys={list(data.keys())}")

            # 트윗 텍스트
            result.content = data.get("text", "")

            # 사용자 정보
            user = data.get("user", {})
            result.og_title = user.get("name", "")
            result.screen_name = user.get("screen_name", "")

            # 미디어 정보
            media = data.get("mediaDetails", [])
            if media:
                result.og_image = media[0].get("media_url_https", "")

            # t.co 링크 리다이렉트 확인
            if result.content and "t.co/" in result.content:
                article_url = await _resolve_tco_link(client, result.content)
                if article_url:
                    result.og_description = f"링크: {article_url}"
                    if "/i/article/" in article_url:
                        result.article_url = article_url

            result.success = bool(result.content)
            logger.info(f"[Syndication] 성공: content_length={len(result.content)}")

    except Exception as e:
        logger.warning(f"[Syndication] 실패: {e}")

    result.elapsed_time = time.time() - start_time
    return result


async def _resolve_tco_link(client: httpx.AsyncClient, text: str) -> Optional[str]:
    """t.co 링크를 실제 URL로 리다이렉트"""
    tco_match = re.search(r"https://t\.co/\w+", text)
    if not tco_match:
        return None

    tco_url = tco_match.group(0)
    try:
        response = await client.head(tco_url, follow_redirects=True, timeout=5.0)
        final_url = str(response.url)
        logger.info(f"[Syndication] t.co 리다이렉트: {tco_url} -> {final_url}")
        return final_url
    except Exception as e:
        logger.warning(f"[Syndication] t.co 리다이렉트 실패: {e}")
        return None

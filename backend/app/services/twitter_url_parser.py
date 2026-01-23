"""
Twitter URL 파싱 유틸리티

Unix Philosophy: Modularity - 단순한 부분들을 깔끔한 인터페이스로 연결
- URL 검증
- 트윗 ID 추출
- URL 정규화
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

# Twitter/X 도메인 목록
TWITTER_DOMAINS = frozenset([
    "twitter.com",
    "x.com",
    "www.twitter.com",
    "www.x.com",
    "mobile.twitter.com",
    "mobile.x.com",
])


def is_twitter_url(url: str) -> bool:
    """
    Twitter/X URL인지 확인

    Args:
        url: 확인할 URL

    Returns:
        Twitter URL이면 True
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower() in TWITTER_DOMAINS
    except Exception:
        return False


def extract_tweet_id(url: str) -> str | None:
    """
    URL에서 트윗 ID 추출

    Args:
        url: Twitter URL

    Returns:
        트윗 ID 또는 None
    """
    match = re.search(r"/status/(\d+)", url)
    return match.group(1) if match else None


def build_tweet_url(screen_name: str, tweet_id: str) -> str:
    """
    정규 트윗 URL 생성

    Args:
        screen_name: 사용자 이름
        tweet_id: 트윗 ID

    Returns:
        https://x.com/{screen_name}/status/{tweet_id} 형식 URL
    """
    return f"https://x.com/{screen_name}/status/{tweet_id}"

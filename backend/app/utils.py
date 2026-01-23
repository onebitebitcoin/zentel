"""
공통 유틸리티 모듈

- ULID 생성 함수
- 시간 유틸리티
- 공통 상수
"""

from datetime import datetime, timezone

from ulid import ULID


def generate_ulid(prefix: str) -> str:
    """
    접두어가 붙은 ULID 생성

    Args:
        prefix: ULID 접두어 (예: "user", "tm", "mc")

    Returns:
        접두어_ULID 형식의 문자열
    """
    return f"{prefix}_{ULID()}"


def now_iso() -> str:
    """현재 시간을 ISO8601 형식으로 반환 (UTC)"""
    return datetime.now(timezone.utc).isoformat()


# 공통 User-Agent 상수
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

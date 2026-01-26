"""
공통 유틸리티 모듈

- ULID 생성 함수
- 시간 유틸리티
- 공통 상수
- 백그라운드 비동기 작업 유틸리티
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine

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


def run_async_in_thread(async_func: Callable[[], Coroutine[Any, Any, Any]]) -> None:
    """
    백그라운드 스레드에서 비동기 함수 실행

    FastAPI BackgroundTasks는 별도 스레드에서 실행되므로,
    새 이벤트 루프를 생성하여 비동기 함수를 실행합니다.

    Args:
        async_func: 실행할 비동기 함수 (인자 없는 코루틴 반환 함수)
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(async_func())
    finally:
        loop.close()

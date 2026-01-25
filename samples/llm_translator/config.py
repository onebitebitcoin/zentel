"""
설정 모듈

환경 변수 또는 직접 설정을 통해 API 키와 모델을 관리합니다.
"""

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional

# .env 파일 로드 시도
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv가 없으면 환경 변수만 사용


@dataclass
class Config:
    """LLM Translator 설정"""

    # OpenAI API 설정
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

    # 청크 분할 설정
    chunk_size: int = 3000  # 청크 크기 (문자)
    chunk_overlap: int = 200  # 청크 간 겹침 (문자)

    # 하이라이트 설정
    max_highlights: int = 5  # 최대 하이라이트 수
    highlight_sample_size: int = 4000  # 하이라이트 추출용 샘플 크기

    # 언어 감지 설정
    language_sample_size: int = 500  # 언어 감지용 샘플 크기

    # 출력 설정
    max_output_tokens: int = 16000  # 번역 최대 토큰

    def validate(self) -> bool:
        """설정 유효성 검사"""
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        return True


@lru_cache(maxsize=1)
def get_config() -> Config:
    """기본 설정 인스턴스 반환 (캐싱)"""
    return Config()


def create_config(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs,
) -> Config:
    """커스텀 설정 생성

    Args:
        api_key: OpenAI API 키
        model: 사용할 모델
        **kwargs: 추가 설정

    Returns:
        Config 인스턴스
    """
    config = Config()

    if api_key:
        config.api_key = api_key
    if model:
        config.model = model

    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    return config

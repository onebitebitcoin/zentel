"""
LLM Translator - 텍스트 번역 및 하이라이트 추출 모듈

다른 AI 코딩 프로젝트에서 재사용 가능한 독립적인 모듈입니다.
"""

# 상대/절대 임포트 둘 다 지원
try:
    from .translator import (
        TranslationResult,
        LLMError,
        split_into_chunks,
        merge_translations,
        detect_language,
        translate_chunk,
        extract_highlights,
        translate_and_highlight,
    )
    from .config import Config, get_config
except ImportError:
    from translator import (
        TranslationResult,
        LLMError,
        split_into_chunks,
        merge_translations,
        detect_language,
        translate_chunk,
        extract_highlights,
        translate_and_highlight,
    )
    from config import Config, get_config

__all__ = [
    # 메인 클래스
    "TranslationResult",
    "LLMError",
    # 유틸리티 함수
    "split_into_chunks",
    "merge_translations",
    # 비동기 함수
    "detect_language",
    "translate_chunk",
    "extract_highlights",
    "translate_and_highlight",
    # 설정
    "Config",
    "get_config",
]

__version__ = "1.0.0"

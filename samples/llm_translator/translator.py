"""
LLM Translator - 텍스트 번역 및 하이라이트 추출 모듈

핵심 기능:
- 긴 텍스트 청크 분할 및 병합
- 자동 언어 감지
- 한국어 번역 (비한국어 텍스트)
- 핵심 문장 하이라이트 추출
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional

from openai import OpenAI

# 상대/절대 임포트 둘 다 지원
try:
    from .config import Config, get_config
except ImportError:
    from config import Config, get_config

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """LLM API 호출 에러"""

    pass


@dataclass
class TranslationResult:
    """번역 결과 데이터 클래스"""

    language: str  # 원본 언어 코드 (ISO 639-1)
    translation: Optional[str]  # 번역/정리된 텍스트
    highlights: list[dict] = field(default_factory=list)  # 하이라이트 목록
    chunk_count: int = 1  # 처리된 청크 수

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            "language": self.language,
            "translation": self.translation,
            "highlights": self.highlights,
            "chunk_count": self.chunk_count,
        }


# ============================================================================
# OpenAI 클라이언트
# ============================================================================


@lru_cache(maxsize=1)
def _get_client(api_key: str) -> OpenAI:
    """OpenAI 클라이언트 (싱글톤)"""
    return OpenAI(api_key=api_key)


def get_client(config: Optional[Config] = None) -> OpenAI:
    """OpenAI 클라이언트 반환

    Args:
        config: 설정 객체 (None이면 기본 설정 사용)

    Returns:
        OpenAI 클라이언트
    """
    if config is None:
        config = get_config()
    config.validate()
    return _get_client(config.api_key)


# ============================================================================
# 유틸리티 함수
# ============================================================================


def get_korean_ratio(text: str) -> float:
    """
    텍스트에서 한국어 문자 비율 계산

    Args:
        text: 분석할 텍스트

    Returns:
        한국어 문자 비율 (0.0 ~ 1.0)
    """
    if not text:
        return 0.0

    korean_count = 0
    total_count = 0

    for char in text:
        # 공백, 숫자, 특수문자 제외
        if char.isspace() or char.isdigit():
            continue
        # 구두점 제외
        category = unicodedata.category(char)
        if category.startswith("P") or category.startswith("S"):
            continue

        total_count += 1
        # 한글 유니코드 범위 체크
        if "\uac00" <= char <= "\ud7a3" or "\u1100" <= char <= "\u11ff":
            korean_count += 1

    return korean_count / total_count if total_count > 0 else 0.0


def validate_translation(
    source_language: str,
    translation: Optional[str],
    original_text: str,
) -> tuple[bool, str]:
    """
    번역 결과 검증

    검증 항목:
    1. 비한국어 원문인데 번역이 없는 경우
    2. 번역 결과가 한국어가 아닌 경우
    3. 번역이 너무 짧은 경우

    Args:
        source_language: 원본 언어 코드
        translation: 번역 결과
        original_text: 원본 텍스트

    Returns:
        (검증 통과 여부, 실패 사유)
    """
    # 한국어 원문이면 번역 불필요
    if source_language == "ko":
        return True, "한국어 원문"

    # 비한국어인데 번역이 없으면 실패
    if not translation:
        return False, "번역 결과 없음"

    # 번역 결과의 한국어 비율 체크
    korean_ratio = get_korean_ratio(translation)
    if korean_ratio < 0.5:
        return False, f"한국어 비율 부족: {korean_ratio:.1%}"

    # 번역이 원문 대비 너무 짧으면 경고
    original_len = len(original_text.strip())
    translation_len = len(translation.strip())

    if original_len > 500 and translation_len < original_len * 0.1:
        logger.warning(
            f"번역이 너무 짧음: 원문 {original_len}자 -> 번역 {translation_len}자"
        )

    return True, "검증 통과"


# ============================================================================
# 청크 분할 및 병합
# ============================================================================


def split_into_chunks(
    text: str,
    chunk_size: int = 3000,
    chunk_overlap: int = 200,
) -> list[str]:
    """
    텍스트를 청크로 분할 (문장 단위, 겹침 적용)

    Args:
        text: 분할할 텍스트
        chunk_size: 청크 크기 (문자)
        chunk_overlap: 청크 간 겹침 (문자)

    Returns:
        청크 리스트
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    current_pos = 0

    while current_pos < len(text):
        # 청크 끝 위치 계산
        end_pos = min(current_pos + chunk_size, len(text))

        # 마지막 청크가 아니면 문장 경계에서 자르기
        if end_pos < len(text):
            sentence_end = -1
            search_start = max(current_pos + chunk_size // 2, current_pos)

            for i in range(end_pos - 1, search_start, -1):
                if text[i] in ".!?。！？" and i + 1 < len(text) and text[i + 1] in " \n\t":
                    sentence_end = i + 1
                    break
                if text[i] == "\n":
                    sentence_end = i + 1
                    break

            if sentence_end > current_pos:
                end_pos = sentence_end

        chunk = text[current_pos:end_pos].strip()
        if chunk:
            chunks.append(chunk)

        # 다음 청크 시작 위치 (겹침 적용)
        current_pos = max(end_pos - chunk_overlap, end_pos)
        if current_pos >= len(text):
            break

    logger.info(f"텍스트 분할: {len(text)}자 -> {len(chunks)}개 청크")
    return chunks


def merge_translations(translations: list[str]) -> str:
    """
    여러 청크의 번역 결과를 합치기 (중복 제거)

    Args:
        translations: 번역된 청크 리스트

    Returns:
        합쳐진 번역 결과
    """
    if not translations:
        return ""

    if len(translations) == 1:
        return translations[0]

    merged = translations[0]

    for i in range(1, len(translations)):
        current = translations[i]

        # 이전 번역과 현재 번역에서 겹치는 부분 찾기
        overlap_found = False

        for overlap_len in range(min(100, len(merged), len(current)), 10, -5):
            if merged[-overlap_len:] == current[:overlap_len]:
                merged += current[overlap_len:]
                overlap_found = True
                break

        if not overlap_found:
            merged += "\n\n" + current

    return merged


# ============================================================================
# LLM 호출 함수 (비동기)
# ============================================================================


async def detect_language(
    text: str,
    config: Optional[Config] = None,
) -> Optional[str]:
    """
    텍스트 언어 감지

    Args:
        text: 감지할 텍스트
        config: 설정 객체

    Returns:
        ISO 639-1 언어 코드 (예: ko, en, ja, zh)
    """
    if config is None:
        config = get_config()

    client = get_client(config)

    # 샘플 텍스트 사용
    sample_text = text[: config.language_sample_size]

    try:
        response = client.responses.create(
            model=config.model,
            instructions=(
                "텍스트의 주요 언어를 ISO 639-1 코드로 응답하세요. "
                "코드만 응답 (예: ko, en, ja, zh)"
            ),
            input=sample_text,
            max_output_tokens=100,
        )

        result = response.output_text
        if result:
            language = result.strip().lower()[:2]
            logger.info(f"언어 감지: {language}")
            return language
        return None

    except Exception as e:
        error_msg = f"언어 감지 실패: {e}"
        logger.error(error_msg, exc_info=True)
        raise LLMError(error_msg) from e


async def translate_chunk(
    chunk: str,
    chunk_index: int = 0,
    total_chunks: int = 1,
    config: Optional[Config] = None,
) -> Optional[str]:
    """
    단일 청크 번역

    Args:
        chunk: 번역할 텍스트 청크
        chunk_index: 청크 인덱스 (0부터 시작)
        total_chunks: 전체 청크 수
        config: 설정 객체

    Returns:
        번역된 텍스트
    """
    if config is None:
        config = get_config()

    client = get_client(config)

    try:
        context_msg = ""
        if chunk_index > 0:
            context_msg = (
                f"(이것은 긴 문서의 {chunk_index + 1}/{total_chunks} 부분입니다. "
                "이어지는 내용을 자연스럽게 번역하세요.)"
            )

        response = client.responses.create(
            model=config.model,
            instructions=(
                "당신은 전문 번역가이자 편집자입니다. "
                "주어진 텍스트를 한국어로 번역하고 읽기 좋게 정리하세요.\n\n"
                "번역 규칙:\n"
                "- 원문의 의미를 정확하게 전달\n"
                "- 자연스러운 한국어 표현 사용\n"
                "- 요약하지 말고 전체 내용을 번역\n"
                "- 번역 결과만 출력 (설명이나 거부 메시지 없이)\n\n"
                "정리 규칙:\n"
                "- 불필요한 특수문자, 이모지, 장식 기호 제거\n"
                "- 내용을 논리적인 문단으로 구분\n"
                "- 서술형 문장으로 자연스럽게 연결\n"
                + context_msg
            ),
            input=f"다음 텍스트를 한국어로 번역하고 정리하세요:\n\n{chunk}",
            max_output_tokens=config.max_output_tokens,
        )

        result = response.output_text
        if result:
            result = result.strip()
            logger.info(
                f"청크 {chunk_index + 1}/{total_chunks} 번역 완료: {len(result)}자"
            )
        return result

    except Exception as e:
        error_msg = f"청크 {chunk_index + 1} 번역 실패: {e}"
        logger.error(error_msg, exc_info=True)
        raise LLMError(error_msg) from e


async def format_text(
    text: str,
    config: Optional[Config] = None,
) -> Optional[str]:
    """
    텍스트를 읽기 좋게 정리 (한국어 원문용)

    Args:
        text: 정리할 텍스트
        config: 설정 객체

    Returns:
        정리된 텍스트
    """
    if config is None:
        config = get_config()

    # 텍스트가 너무 길면 청크로 분할
    if len(text) > config.chunk_size:
        chunks = split_into_chunks(text, config.chunk_size, config.chunk_overlap)
        formatted_chunks = []

        for i, chunk in enumerate(chunks):
            formatted = await _format_single_chunk(chunk, i, len(chunks), config)
            formatted_chunks.append(formatted if formatted else chunk)

        return merge_translations(formatted_chunks) if formatted_chunks else None

    return await _format_single_chunk(text, 0, 1, config)


async def _format_single_chunk(
    chunk: str,
    chunk_index: int,
    total_chunks: int,
    config: Config,
) -> Optional[str]:
    """단일 청크 텍스트 정리"""
    client = get_client(config)

    try:
        context_msg = ""
        if chunk_index > 0:
            context_msg = f"(이것은 긴 문서의 {chunk_index + 1}/{total_chunks} 부분입니다.)"

        response = client.responses.create(
            model=config.model,
            instructions=(
                "당신은 텍스트 편집자입니다. 주어진 텍스트를 읽기 좋게 정리하세요.\n\n"
                "정리 규칙:\n"
                "- 내용은 그대로 유지 (삭제하거나 요약하지 말 것)\n"
                "- 불필요한 특수문자, 이모지, 장식 기호 제거\n"
                "- 내용을 논리적인 문단으로 구분\n"
                "- 서술형 문장으로 자연스럽게 연결\n"
                "- 정리된 결과만 출력 (설명 없이)\n"
                + context_msg
            ),
            input=f"다음 텍스트를 읽기 좋게 정리하세요:\n\n{chunk}",
            max_output_tokens=config.max_output_tokens,
        )

        result = response.output_text
        if result:
            result = result.strip()
            logger.info(f"텍스트 정리 완료: {len(result)}자")
        return result

    except Exception as e:
        error_msg = f"텍스트 정리 실패: {e}"
        logger.error(error_msg, exc_info=True)
        raise LLMError(error_msg) from e


async def extract_highlights(
    text: str,
    max_count: int = 5,
    config: Optional[Config] = None,
) -> list[dict]:
    """
    텍스트에서 하이라이트 추출

    Args:
        text: 분석할 텍스트
        max_count: 최대 하이라이트 수
        config: 설정 객체

    Returns:
        하이라이트 목록
        [
            {
                "type": "claim" | "fact",
                "text": "하이라이트 텍스트",
                "start": 시작 위치,
                "end": 끝 위치,
                "reason": "선정 이유"
            }
        ]
    """
    if config is None:
        config = get_config()

    client = get_client(config)

    # 샘플 텍스트 사용
    sample_text = text[: config.highlight_sample_size]

    try:
        response = client.responses.create(
            model=config.model,
            instructions=(
                f"텍스트에서 핵심 문장을 최대 {max_count}개 추출하세요.\n\n"
                "유형:\n"
                "- claim: 핵심 주장\n"
                "- fact: 흥미로운 사실\n\n"
                "JSON 형식으로만 응답:\n"
                "```json\n"
                "[\n"
                '  {"type": "claim", "text": "원문에서 발췌한 문장", "reason": "선정 이유"}\n'
                "]\n"
                "```"
            ),
            input=sample_text,
            max_output_tokens=4000,
        )

        raw = response.output_text or ""
        raw = raw.strip()

        # 마크다운 코드 블록 제거
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)

        highlights_raw = json.loads(raw)

        highlights = []
        for item in highlights_raw:
            if not isinstance(item, dict):
                continue
            highlight_text = item.get("text", "")
            if not highlight_text:
                continue

            # 원문에서 위치 찾기
            start = text.find(highlight_text)
            if start == -1:
                short_text = highlight_text[:50]
                start = text.find(short_text)

            end = start + len(highlight_text) if start != -1 else -1

            highlights.append(
                {
                    "type": item.get("type", "fact"),
                    "text": highlight_text,
                    "start": start,
                    "end": end,
                    "reason": item.get("reason"),
                }
            )

        logger.info(f"하이라이트 추출: {len(highlights)}개")
        return highlights

    except json.JSONDecodeError as e:
        error_msg = f"하이라이트 JSON 파싱 실패: {e}"
        logger.error(error_msg, exc_info=True)
        raise LLMError(error_msg) from e
    except Exception as e:
        error_msg = f"하이라이트 추출 실패: {e}"
        logger.error(error_msg, exc_info=True)
        raise LLMError(error_msg) from e


# ============================================================================
# 메인 함수
# ============================================================================


async def translate_and_highlight(
    text: str,
    config: Optional[Config] = None,
) -> TranslationResult:
    """
    언어 감지 + 번역 + 하이라이트 추출 (메인 함수)

    긴 텍스트는 청크로 분할하여 여러 번 번역 후 결과를 합칩니다.
    한국어 텍스트는 번역 없이 정리만 수행합니다.

    Args:
        text: 분석할 텍스트
        config: 설정 객체 (None이면 기본 설정 사용)

    Returns:
        TranslationResult 객체
    """
    if config is None:
        config = get_config()

    # 텍스트가 너무 짧으면 처리하지 않음
    if len(text.strip()) < 20:
        return TranslationResult(
            language="unknown",
            translation=None,
            highlights=[],
            chunk_count=0,
        )

    # 1단계: 언어 감지
    language = await detect_language(text, config)
    if not language:
        language = "unknown"

    # 한국어면 번역 스킵, 정리 + 하이라이트만 추출
    if language == "ko":
        logger.info("한국어 감지, 정리만 수행")
        formatted_text = await format_text(text, config)
        highlights = await extract_highlights(formatted_text or text, config.max_highlights, config)

        return TranslationResult(
            language=language,
            translation=formatted_text,
            highlights=highlights,
            chunk_count=1,
        )

    # 2단계: 청크 분할 및 번역
    chunks = split_into_chunks(text, config.chunk_size, config.chunk_overlap)
    translations = []

    for i, chunk in enumerate(chunks):
        translated = await translate_chunk(chunk, i, len(chunks), config)
        if translated:
            translations.append(translated)
        else:
            translations.append(chunk)  # 번역 실패 시 원문 유지

    # 3단계: 번역 결과 합치기
    full_translation = merge_translations(translations) if translations else None

    # 4단계: 번역 검증
    if full_translation:
        is_valid, validation_msg = validate_translation(
            source_language=language,
            translation=full_translation,
            original_text=text,
        )
        if not is_valid:
            logger.warning(f"번역 검증 실패: {validation_msg}")

    # 5단계: 하이라이트 추출 (번역본 기준)
    highlight_target = full_translation if full_translation else text
    highlights = await extract_highlights(highlight_target, config.max_highlights, config)

    logger.info(
        f"translate_and_highlight 완료: language={language}, "
        f"translation_len={len(full_translation) if full_translation else 0}, "
        f"chunks={len(chunks)}, highlights={len(highlights)}"
    )

    return TranslationResult(
        language=language,
        translation=full_translation,
        highlights=highlights,
        chunk_count=len(chunks),
    )

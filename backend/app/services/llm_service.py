"""
LLM (OpenAI) 서비스

Unix Philosophy:
- Modularity: LLM API 호출만 담당
- Separation: LLM 로직 분리
- Silence: 필요한 정보만 로깅
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from functools import lru_cache
from typing import Optional

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_openai_client() -> Optional[OpenAI]:
    """OpenAI 클라이언트 (싱글톤)"""
    if settings.OPENAI_API_KEY:
        return OpenAI(api_key=settings.OPENAI_API_KEY)
    return None


def _get_korean_ratio(text: str) -> float:
    """
    텍스트에서 한국어 문자 비율 계산

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


def _validate_translation_result(
    source_language: str,
    translation: Optional[str],
    original_text: str,
) -> tuple[bool, str]:
    """
    번역 결과 검증

    검증 항목:
    1. 비한국어 원문인데 번역이 없는 경우
    2. 번역 결과가 한국어가 아닌 경우 (영어로 요약만 한 경우)
    3. 번역이 너무 짧은 경우 (요약만 한 것으로 의심)

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
    korean_ratio = _get_korean_ratio(translation)
    if korean_ratio < 0.5:
        return False, f"한국어 비율 부족: {korean_ratio:.1%}"

    # 번역이 원문 대비 너무 짧으면 경고 (요약만 했을 가능성)
    original_len = len(original_text.strip())
    translation_len = len(translation.strip())

    # 원문이 충분히 길고 (500자 이상), 번역이 원문의 10% 미만이면 의심
    if original_len > 500 and translation_len < original_len * 0.1:
        logger.warning(
            f"[LLM] 번역이 너무 짧음: 원문 {original_len}자 → 번역 {translation_len}자"
        )
        # 경고만 하고 통과 (요약 번역일 수 있음)

    return True, "검증 통과"


async def extract_context(text: str, memo_type: str) -> Optional[str]:
    """
    텍스트에서 context 추출

    Args:
        text: 분석할 텍스트
        memo_type: 메모 타입

    Returns:
        추출된 context
    """
    client = get_openai_client()
    if not client:
        logger.warning("OpenAI API key not configured")
        return None

    # 텍스트 길이 제한
    max_chars = 6000
    if len(text) > max_chars:
        text = text[:max_chars] + "..."
        logger.info(f"[LLM] 텍스트 truncate: {max_chars}자")

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "10단어 이내의 짧은 문구로 이 메모의 핵심 맥락(context)을 한 줄로 표현하세요. "
                        "마크다운 형식 없이 순수한 텍스트로만 응답하세요. "
                        "반드시 한국어로 응답하세요."
                    ),
                },
                {
                    "role": "user",
                    "content": f"다음 내용의 핵심 context를 10단어 이내로 표현해주세요:\n\n{text}",
                },
            ],
            max_tokens=50,
            temperature=0.3,
        )

        context = response.choices[0].message.content
        if context:
            context = context.strip()
            logger.info(f"[LLM] context 추출: {len(context)} chars")
            return context

        return None

    except Exception as e:
        logger.error(f"[LLM] API 호출 실패: {e}", exc_info=True)
        return None


async def match_interests(content: str, user_interests: list[str]) -> list[str]:
    """
    메모 내용과 사용자 관심사 매핑

    Args:
        content: 메모 내용
        user_interests: 사용자 관심사 목록

    Returns:
        매핑된 관심사 배열
    """
    client = get_openai_client()
    if not client:
        return []

    if not user_interests:
        return []

    try:
        interests_str = ", ".join(user_interests)

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "당신은 텍스트 분류 전문가입니다. "
                        "주어진 메모 내용이 어떤 관심사와 관련이 있는지 판단합니다. "
                        "반드시 제공된 관심사 목록에서만 선택해야 합니다. "
                        "관련된 관심사가 없으면 반드시 '없음'이라고 응답하세요. "
                        "마크다운이나 다른 형식 없이 관심사 이름만 반환하세요."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"관심사 목록: {interests_str}\n\n"
                        f"메모 내용:\n{content}\n\n"
                        "관련된 관심사를 쉼표로 구분하여 반환하세요. "
                        "명확하게 관련된 관심사가 없으면 '없음'이라고 반환하세요."
                    ),
                },
            ],
            max_tokens=100,
            temperature=0.2,
        )

        raw = response.choices[0].message.content or ""
        raw = raw.strip()

        # "없음" 체크
        if not raw or raw.lower() in ["없음", "none", "없습니다", "해당 없음"]:
            return []

        # LLM 환각 방지: 실제 관심사 목록에 있는 것만 필터링
        matched = []
        candidates = [item.strip() for item in raw.split(",")]
        user_interests_lower = {i.lower(): i for i in user_interests}

        for candidate in candidates:
            candidate_lower = candidate.lower()
            if candidate_lower in user_interests_lower:
                matched.append(user_interests_lower[candidate_lower])

        logger.info(f"[LLM] 관심사 매칭: {matched}")
        return matched

    except Exception as e:
        logger.error(f"[LLM] 관심사 매칭 실패: {e}", exc_info=True)
        return []


# 청크 분할 설정
CHUNK_SIZE = 3000  # 청크 크기 (문자)
CHUNK_OVERLAP = 200  # 청크 간 겹침 (문자) - 문장 잘림 방지


def _split_into_chunks(text: str) -> list[str]:
    """
    텍스트를 청크로 분할 (문장 단위, 겹침 적용)

    Args:
        text: 분할할 텍스트

    Returns:
        청크 리스트
    """
    if len(text) <= CHUNK_SIZE:
        return [text]

    chunks = []
    current_pos = 0

    while current_pos < len(text):
        # 청크 끝 위치 계산
        end_pos = min(current_pos + CHUNK_SIZE, len(text))

        # 마지막 청크가 아니면 문장 경계에서 자르기
        if end_pos < len(text):
            # 문장 끝 찾기 (. ! ? 다음 공백 또는 줄바꿈)
            sentence_end = -1
            for i in range(end_pos - 1, max(current_pos + CHUNK_SIZE // 2, current_pos), -1):
                if text[i] in ".!?。！？" and i + 1 < len(text) and text[i + 1] in " \n\t":
                    sentence_end = i + 1
                    break
                # 줄바꿈도 문장 경계로 처리
                if text[i] == "\n":
                    sentence_end = i + 1
                    break

            if sentence_end > current_pos:
                end_pos = sentence_end

        chunk = text[current_pos:end_pos].strip()
        if chunk:
            chunks.append(chunk)

        # 다음 청크 시작 위치 (겹침 적용)
        current_pos = max(end_pos - CHUNK_OVERLAP, end_pos)
        if current_pos >= len(text):
            break

    logger.info(f"[LLM] 텍스트 분할: {len(text)}자 → {len(chunks)}개 청크")
    return chunks


def _merge_translations(translations: list[str]) -> str:
    """
    여러 청크의 번역 결과를 합치기 (중복 제거)

    Args:
        translations: 번역된 청크 리스트

    Returns:
        합쳐진 번역 결과
    """
    if len(translations) == 1:
        return translations[0]

    merged = translations[0]

    for i in range(1, len(translations)):
        current = translations[i]

        # 이전 번역과 현재 번역에서 겹치는 부분 찾기
        # 마지막 50자와 처음 50자 비교
        overlap_found = False

        for overlap_len in range(min(100, len(merged), len(current)), 10, -5):
            if merged[-overlap_len:] == current[:overlap_len]:
                merged += current[overlap_len:]
                overlap_found = True
                break

        if not overlap_found:
            # 겹침을 찾지 못하면 줄바꿈으로 연결
            merged += "\n\n" + current

    return merged


async def _translate_chunk(
    client: OpenAI,
    chunk: str,
    chunk_index: int,
    total_chunks: int,
    detected_language: Optional[str] = None,
) -> Optional[str]:
    """
    단일 청크 번역

    Args:
        client: OpenAI 클라이언트
        chunk: 번역할 텍스트 청크
        chunk_index: 청크 인덱스
        total_chunks: 전체 청크 수
        detected_language: 이미 감지된 언어 코드

    Returns:
        번역된 텍스트
    """
    try:
        is_first = chunk_index == 0
        context_msg = ""
        if not is_first:
            context_msg = f"(이것은 긴 문서의 {chunk_index + 1}/{total_chunks} 부분입니다. 이어지는 내용을 자연스럽게 번역하세요.)"

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "당신은 전문 번역가이자 편집자입니다. "
                        "주어진 텍스트를 한국어로 번역하고 읽기 좋게 정리하세요.\n\n"
                        "번역 규칙:\n"
                        "- 원문의 의미를 정확하게 전달\n"
                        "- 자연스러운 한국어 표현 사용\n"
                        "- 요약하지 말고 전체 내용을 번역\n"
                        "- 번역 결과만 출력 (설명이나 거부 메시지 없이)\n"
                        "- '번역할 수 없습니다' 같은 거부 응답 금지\n\n"
                        "정리 규칙:\n"
                        "- 불필요한 특수문자, 이모지, 장식 기호 제거 (>, *, #, = 등)\n"
                        "- 내용을 논리적인 문단으로 구분 (문단 사이 빈 줄)\n"
                        "- 서술형 문장으로 자연스럽게 연결\n"
                        "- 리스트는 문장으로 풀어서 설명\n"
                        "- 제목/소제목은 굵게 표시하지 말고 문단 첫 문장으로 자연스럽게 통합\n"
                        + context_msg
                    ),
                },
                {"role": "user", "content": f"다음 텍스트를 한국어로 번역하고 정리하세요:\n\n{chunk}"},
            ],
            max_tokens=4000,
            temperature=0.3,
        )

        result = response.choices[0].message.content
        if result:
            result = result.strip()
            logger.info(f"[LLM] 청크 {chunk_index + 1}/{total_chunks} 번역 완료: {len(result)}자")
        return result

    except Exception as e:
        logger.error(f"[LLM] 청크 {chunk_index + 1} 번역 실패: {e}")
        return None


async def _format_text(client: OpenAI, text: str) -> Optional[str]:
    """
    텍스트를 읽기 좋게 정리 (한국어 원문용)

    Args:
        client: OpenAI 클라이언트
        text: 정리할 텍스트

    Returns:
        정리된 텍스트
    """
    # 텍스트가 너무 길면 청크로 분할
    if len(text) > CHUNK_SIZE:
        chunks = _split_into_chunks(text)
        formatted_chunks = []

        for i, chunk in enumerate(chunks):
            formatted = await _format_single_chunk(client, chunk, i, len(chunks))
            if formatted:
                formatted_chunks.append(formatted)
            else:
                formatted_chunks.append(chunk)

        return _merge_translations(formatted_chunks) if formatted_chunks else None

    return await _format_single_chunk(client, text, 0, 1)


async def _format_single_chunk(
    client: OpenAI,
    chunk: str,
    chunk_index: int,
    total_chunks: int,
) -> Optional[str]:
    """
    단일 청크 텍스트 정리

    Args:
        client: OpenAI 클라이언트
        chunk: 정리할 텍스트 청크
        chunk_index: 청크 인덱스
        total_chunks: 전체 청크 수

    Returns:
        정리된 텍스트
    """
    try:
        context_msg = ""
        if chunk_index > 0:
            context_msg = f"(이것은 긴 문서의 {chunk_index + 1}/{total_chunks} 부분입니다.)"

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "당신은 텍스트 편집자입니다. 주어진 텍스트를 읽기 좋게 정리하세요.\n\n"
                        "정리 규칙:\n"
                        "- 내용은 그대로 유지 (삭제하거나 요약하지 말 것)\n"
                        "- 불필요한 특수문자, 이모지, 장식 기호 제거 (>, *, #, = 등)\n"
                        "- 내용을 논리적인 문단으로 구분 (문단 사이 빈 줄)\n"
                        "- 서술형 문장으로 자연스럽게 연결\n"
                        "- 리스트는 문장으로 풀어서 설명\n"
                        "- 제목/소제목은 문단 첫 문장으로 자연스럽게 통합\n"
                        "- 정리된 결과만 출력 (설명 없이)\n"
                        + context_msg
                    ),
                },
                {"role": "user", "content": f"다음 텍스트를 읽기 좋게 정리하세요:\n\n{chunk}"},
            ],
            max_tokens=4000,
            temperature=0.3,
        )

        result = response.choices[0].message.content
        if result:
            result = result.strip()
            logger.info(f"[LLM] 텍스트 정리 완료: {len(result)}자")
        return result

    except Exception as e:
        logger.error(f"[LLM] 텍스트 정리 실패: {e}")
        return None


async def translate_and_highlight(
    text: str,
    max_retries: int = 2,
) -> tuple[Optional[str], Optional[str], bool, Optional[list[dict]]]:
    """
    언어 감지 + 번역 + 하이라이트 추출

    긴 텍스트는 청크로 분할하여 여러 번 번역 후 결과를 합칩니다.

    Args:
        text: 분석할 텍스트
        max_retries: 검증 실패 시 최대 재시도 횟수

    Returns:
        (언어코드, 번역본, False, 하이라이트 목록) 튜플
        - is_summary는 항상 False (요약 없이 전체 번역)
    """
    client = get_openai_client()
    if not client:
        return None, None, False, None

    if len(text.strip()) < 20:
        return None, None, False, None

    # 1단계: 언어 감지 (첫 500자로 빠르게 감지)
    sample_text = text[:500]
    language = await _detect_language(client, sample_text)

    # 한국어면 번역 스킵, 정리 + 하이라이트만 추출
    if language == "ko":
        logger.info("[LLM] 한국어 감지, 정리만 수행")
        formatted_text = await _format_text(client, text)
        highlights = await _extract_highlights(client, formatted_text or text)
        return language, formatted_text, False, highlights

    # 2단계: 청크 분할 및 번역
    chunks = _split_into_chunks(text)
    translations = []

    for i, chunk in enumerate(chunks):
        translated = await _translate_chunk(client, chunk, i, len(chunks), language)
        if translated:
            translations.append(translated)
        else:
            # 번역 실패 시 원문 유지
            translations.append(chunk)

    # 3단계: 번역 결과 합치기
    full_translation = _merge_translations(translations) if translations else None

    # 4단계: 번역 검증
    if full_translation:
        is_valid, validation_msg = _validate_translation_result(
            source_language=language or "unknown",
            translation=full_translation,
            original_text=text,
        )
        if not is_valid:
            logger.warning(f"[LLM] 번역 검증 실패: {validation_msg}")

    # 5단계: 하이라이트 추출 (번역본 기준)
    highlight_target = full_translation if full_translation else text
    highlights = await _extract_highlights(client, highlight_target)

    logger.info(
        f"[LLM] translate_and_highlight 완료: language={language}, "
        f"translation_len={len(full_translation) if full_translation else 0}, "
        f"chunks={len(chunks)}, highlights={len(highlights) if highlights else 0}"
    )

    return language, full_translation, False, highlights


async def _detect_language(client: OpenAI, text: str) -> Optional[str]:
    """
    텍스트 언어 감지

    Args:
        client: OpenAI 클라이언트
        text: 감지할 텍스트

    Returns:
        ISO 639-1 언어 코드
    """
    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "텍스트의 주요 언어를 ISO 639-1 코드로 응답하세요. "
                        "코드만 응답 (예: ko, en, ja, zh)"
                    ),
                },
                {"role": "user", "content": text},
            ],
            max_tokens=10,
            temperature=0.1,
        )

        result = response.choices[0].message.content
        if result:
            language = result.strip().lower()[:2]
            logger.info(f"[LLM] 언어 감지: {language}")
            return language
        return None

    except Exception as e:
        logger.error(f"[LLM] 언어 감지 실패: {e}")
        return None


async def _extract_highlights(
    client: OpenAI,
    text: str,
    max_highlights: int = 5,
) -> Optional[list[dict]]:
    """
    텍스트에서 하이라이트 추출

    Args:
        client: OpenAI 클라이언트
        text: 분석할 텍스트
        max_highlights: 최대 하이라이트 수

    Returns:
        하이라이트 목록
    """
    # 하이라이트 추출을 위해 텍스트 길이 제한
    sample_text = text[:4000] if len(text) > 4000 else text

    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"텍스트에서 핵심 문장을 최대 {max_highlights}개 추출하세요.\n\n"
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
                },
                {"role": "user", "content": sample_text},
            ],
            max_tokens=1500,
            temperature=0.3,
        )

        raw = response.choices[0].message.content or ""
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
                # 짧은 버전으로 재시도
                short_text = highlight_text[:50]
                start = text.find(short_text)

            end = start + len(highlight_text) if start != -1 else -1

            highlights.append({
                "type": item.get("type", "fact"),
                "text": highlight_text,
                "start": start,
                "end": end,
                "reason": item.get("reason"),
            })

        logger.info(f"[LLM] 하이라이트 추출: {len(highlights)}개")
        return highlights if highlights else None

    except json.JSONDecodeError as e:
        logger.error(f"[LLM] 하이라이트 JSON 파싱 실패: {e}")
        return None
    except Exception as e:
        logger.error(f"[LLM] 하이라이트 추출 실패: {e}")
        return None

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


async def translate_and_highlight(
    text: str,
    max_retries: int = 2,
) -> tuple[Optional[str], Optional[str], bool, Optional[list[dict]]]:
    """
    언어 감지 + 번역 + 하이라이트 추출 (검증 포함)

    Args:
        text: 분석할 텍스트
        max_retries: 검증 실패 시 최대 재시도 횟수

    Returns:
        (언어코드, 번역본, 요약여부, 하이라이트 목록) 튜플
    """
    client = get_openai_client()
    if not client:
        return None, None, False, None

    if len(text.strip()) < 20:
        return None, None, False, None

    # 텍스트 길이 제한
    max_chars = 6000
    truncated_text = text[:max_chars] if len(text) > max_chars else text

    # 재시도 루프
    for attempt in range(max_retries + 1):
        is_retry = attempt > 0
        retry_instruction = ""

        if is_retry:
            retry_instruction = (
                "\n\n[중요] 이전 응답이 검증에 실패했습니다. "
                "반드시 한국어로 번역해야 합니다. "
                "영어나 다른 언어로 응답하지 마세요."
            )

        try:
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "당신은 텍스트 분석 전문가입니다. 다음 작업을 수행하세요:\n\n"
                            "1. **언어 감지**: ISO 639-1 코드로 감지 (ko, en, ja, zh 등)\n\n"
                            "2. **번역**: \n"
                            "   - 한국어(ko)가 아닌 모든 언어는 반드시 한국어로 번역\n"
                            "   - 한국어(ko)인 경우에만 translation을 null로\n"
                            "   - 긴 글이면 핵심 내용을 요약하여 번역 (500-1500자)\n"
                            "   - [중요] 번역 결과는 반드시 한국어여야 함\n\n"
                            "3. **하이라이트 추출**: 최대 5개\n"
                            "   - claim: 핵심 주장\n"
                            "   - fact: 흥미로운 사실\n"
                            "   - 번역본(한국어)에서 문장 추출\n\n"
                            "JSON 형식으로만 응답:\n"
                            "```json\n"
                            "{\n"
                            '  "language": "en",\n'
                            '  "translation": "한국어 번역/요약 내용",\n'
                            '  "highlights": [\n'
                            '    {"type": "claim", "text": "한국어 문장", "reason": "선정 이유"}\n'
                            "  ]\n"
                            "}\n"
                            "```"
                            + retry_instruction
                        ),
                    },
                    {"role": "user", "content": truncated_text},
                ],
                max_tokens=4500,
                temperature=0.3 if not is_retry else 0.5,  # 재시도 시 temperature 증가
            )

            raw = response.choices[0].message.content or ""
            raw = raw.strip()

            # 마크다운 코드 블록 제거
            if raw.startswith("```"):
                raw = re.sub(r"^```(?:json)?\n?", "", raw)
                raw = re.sub(r"\n?```$", "", raw)

            result = json.loads(raw)

            # 언어 코드
            language = result.get("language")
            if language:
                language = language.strip().lower()[:2]

            # 번역본
            translation = result.get("translation")
            if translation:
                translation = translation.strip()

            # 번역 결과 검증
            is_valid, validation_msg = _validate_translation_result(
                source_language=language or "unknown",
                translation=translation,
                original_text=truncated_text,
            )

            if not is_valid:
                logger.warning(
                    f"[LLM] 번역 검증 실패 (시도 {attempt + 1}/{max_retries + 1}): {validation_msg}"
                )
                if attempt < max_retries:
                    continue  # 재시도
                else:
                    logger.error(f"[LLM] 번역 검증 최종 실패: {validation_msg}")
                    # 검증 실패해도 결과 반환 (None보다는 나음)

            # 하이라이트 처리
            highlights_raw = result.get("highlights", [])
            highlight_target = translation if translation else text

            highlights = []
            for item in highlights_raw:
                if not isinstance(item, dict):
                    continue
                highlight_text = item.get("text", "")
                if not highlight_text:
                    continue

                start = highlight_target.find(highlight_text)
                if start == -1:
                    short_text = highlight_text[:50]
                    start = highlight_target.find(short_text)

                end = start + len(highlight_text) if start != -1 else -1

                highlights.append({
                    "type": item.get("type", "fact"),
                    "text": highlight_text,
                    "start": start,
                    "end": end,
                    "reason": item.get("reason"),
                })

            korean_ratio = _get_korean_ratio(translation) if translation else 0

            # 요약 여부 판단: 원문이 500자 이상이고, 번역이 원문의 50% 미만이면 요약
            is_summary = False
            if translation and language != "ko":
                original_len = len(truncated_text.strip())
                translation_len = len(translation.strip())
                if original_len >= 500 and translation_len < original_len * 0.5:
                    is_summary = True

            logger.info(
                f"[LLM] translate_and_highlight: language={language}, "
                f"translation={'Yes' if translation else 'No'}, "
                f"korean_ratio={korean_ratio:.1%}, is_summary={is_summary}, "
                f"highlights={len(highlights)}, attempt={attempt + 1}"
            )

            return language, translation, is_summary, highlights if highlights else None

        except json.JSONDecodeError as e:
            logger.error(f"[LLM] JSON 파싱 실패 (시도 {attempt + 1}): {e}")
            if attempt < max_retries:
                continue
            return None, None, False, None
        except Exception as e:
            logger.error(f"[LLM] translate_and_highlight 실패: {e}", exc_info=True)
            return None, None, False, None

    return None, None, False, None

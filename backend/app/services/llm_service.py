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
) -> tuple[Optional[str], Optional[str], Optional[list[dict]]]:
    """
    언어 감지 + 번역 + 하이라이트 추출 (1회 LLM 호출)

    Args:
        text: 분석할 텍스트

    Returns:
        (언어코드, 번역본, 하이라이트 목록) 튜플
    """
    client = get_openai_client()
    if not client:
        return None, None, None

    if len(text.strip()) < 20:
        return None, None, None

    # 텍스트 길이 제한
    max_chars = 6000
    truncated_text = text[:max_chars] if len(text) > max_chars else text

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
                        "   - 한국어(ko)가 아닌 모든 언어는 한국어로 번역\n"
                        "   - 한국어(ko)인 경우 translation을 null로\n"
                        "   - 긴 글이면 핵심 내용을 요약하여 번역 (500-1500자)\n\n"
                        "3. **하이라이트 추출**: 최대 5개\n"
                        "   - claim: 핵심 주장\n"
                        "   - fact: 흥미로운 사실\n"
                        "   - 번역본(한국어)에서 문장 추출\n\n"
                        "JSON 형식으로만 응답:\n"
                        "```json\n"
                        "{\n"
                        '  "language": "en",\n'
                        '  "translation": "번역/요약 내용",\n'
                        '  "highlights": [\n'
                        '    {"type": "claim", "text": "문장", "reason": "선정 이유"}\n'
                        "  ]\n"
                        "}\n"
                        "```"
                    ),
                },
                {"role": "user", "content": truncated_text},
            ],
            max_tokens=4500,
            temperature=0.3,
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

        logger.info(
            f"[LLM] translate_and_highlight: language={language}, "
            f"translation={'Yes' if translation else 'No'}, highlights={len(highlights)}"
        )

        return language, translation, highlights if highlights else None

    except json.JSONDecodeError as e:
        logger.error(f"[LLM] JSON 파싱 실패: {e}")
        return None, None, None
    except Exception as e:
        logger.error(f"[LLM] translate_and_highlight 실패: {e}", exc_info=True)
        return None, None, None

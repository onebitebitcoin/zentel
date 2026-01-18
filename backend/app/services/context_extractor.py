"""
LLM Context 추출 서비스

메모 저장 시 OpenAI API를 사용하여 context를 추출합니다.
- EXTERNAL_SOURCE 타입: URL에서 컨텐츠를 가져와 분석
- 기타 타입: 입력된 내용을 직접 분석
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx
from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class ContextExtractor:
    """LLM을 사용한 Context 추출 서비스"""

    def __init__(self) -> None:
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> Optional[OpenAI]:
        """OpenAI 클라이언트 (Lazy initialization)"""
        if self._client is None and settings.OPENAI_API_KEY:
            self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    async def extract_context(
        self,
        content: str,
        memo_type: str,
        source_url: Optional[str] = None,
    ) -> Optional[str]:
        """
        메모에서 context 추출

        Args:
            content: 메모 내용
            memo_type: 메모 타입
            source_url: 외부 URL (EXTERNAL_SOURCE 타입일 때)

        Returns:
            추출된 context 또는 None
        """
        if not self.client:
            logger.warning("OpenAI API key not configured, skipping context extraction")
            return None

        try:
            # EXTERNAL_SOURCE 타입이고 URL이 있으면 URL 컨텐츠 가져오기
            text_to_analyze = content
            if memo_type == "EXTERNAL_SOURCE" and source_url:
                fetched_content = await self._fetch_url_content(source_url)
                if fetched_content:
                    text_to_analyze = f"URL: {source_url}\n\n{fetched_content}"

            # LLM 호출
            context = await self._call_llm(text_to_analyze, memo_type)
            return context

        except Exception as e:
            logger.error(f"Failed to extract context: {e}", exc_info=True)
            return None

    async def _fetch_url_content(self, url: str) -> Optional[str]:
        """
        URL에서 컨텐츠 가져오기

        Args:
            url: 대상 URL

        Returns:
            추출된 텍스트 컨텐츠 또는 None
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 Zentel/1.0"},
                    follow_redirects=True,
                )
                response.raise_for_status()

                # HTML에서 텍스트만 추출 (간단 처리)
                content = response.text
                # 너무 긴 컨텐츠는 잘라내기
                max_length = 10000
                if len(content) > max_length:
                    content = content[:max_length] + "..."

                logger.info(f"Fetched URL content: {url}, length={len(content)}")
                return content

        except Exception as e:
            logger.error(f"Failed to fetch URL content: {url}, error={e}")
            return None

    async def _call_llm(self, text: str, memo_type: str) -> Optional[str]:
        """
        OpenAI API 호출

        Args:
            text: 분석할 텍스트
            memo_type: 메모 타입

        Returns:
            LLM 응답 (context)
        """
        if not self.client:
            return None

        prompt = self._build_prompt(text, memo_type)

        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "당신은 메모 내용을 분석하여 핵심 컨텍스트를 추출하는 어시스턴트입니다. "
                            "간결하고 명확하게 핵심 내용을 요약해주세요. "
                            "한국어로 응답하세요."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=settings.CONTEXT_MAX_LENGTH,
                temperature=0.3,
            )

            context = response.choices[0].message.content
            if context:
                context = context.strip()
                logger.info(f"LLM context extracted: {len(context)} chars")
                return context

            return None

        except Exception as e:
            logger.error(f"LLM API call failed: {e}", exc_info=True)
            return None

    def _build_prompt(self, text: str, memo_type: str) -> str:
        """
        메모 타입별 프롬프트 생성

        Args:
            text: 분석할 텍스트
            memo_type: 메모 타입

        Returns:
            프롬프트 문자열
        """
        type_prompts = {
            "EXTERNAL_SOURCE": (
                "다음 외부 자료의 핵심 내용을 3-5문장으로 요약해주세요. "
                "주요 인사이트나 중요한 정보를 포함해주세요."
            ),
            "NEW_IDEA": (
                "다음 아이디어의 핵심을 파악하고, "
                "실현 가능성과 발전 방향을 간략히 제시해주세요."
            ),
            "NEW_GOAL": (
                "다음 목표의 핵심을 정리하고, "
                "달성을 위한 첫 단계를 제안해주세요."
            ),
            "EVOLVED_THOUGHT": (
                "다음 생각의 발전 과정을 정리하고, "
                "더 깊이 탐구할 수 있는 방향을 제시해주세요."
            ),
            "CURIOSITY": (
                "다음 호기심/궁금증의 핵심 질문을 정리하고, "
                "탐구 방향을 제안해주세요."
            ),
            "UNRESOLVED_PROBLEM": (
                "다음 문제의 핵심을 파악하고, "
                "가능한 해결 접근법을 간략히 제시해주세요."
            ),
            "EMOTION": (
                "다음 감정 기록의 핵심을 파악하고, "
                "그 감정이 전달하는 메시지를 간략히 정리해주세요."
            ),
        }

        type_prompt = type_prompts.get(memo_type, "다음 내용의 핵심을 요약해주세요.")

        return f"{type_prompt}\n\n---\n{text}\n---"


# 싱글톤 인스턴스
context_extractor = ContextExtractor()

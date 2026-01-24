"""
Context 추출 서비스 (오케스트레이션)

Unix Philosophy:
- Modularity: 작은 모듈들을 조합
- Simplicity: 오케스트레이션 로직만 담당
- Composition: 다른 모듈과 연결되도록 설계
"""

from __future__ import annotations

import logging
from typing import Optional

from app.services import llm_service
from app.services.og_metadata import OGMetadata
from app.services.url_fetcher import fetch_url_content

logger = logging.getLogger(__name__)


class ContextExtractor:
    """
    Context 추출 서비스

    - URL 콘텐츠 가져오기
    - LLM을 통한 context 추출
    - 관심사 매핑
    - 번역 및 하이라이트 추출
    """

    async def extract_context(
        self,
        content: str,
        memo_type: str,
        source_url: Optional[str] = None,
    ) -> tuple[Optional[str], Optional[OGMetadata]]:
        """
        메모에서 context 추출

        Args:
            content: 메모 내용
            memo_type: 메모 타입
            source_url: 외부 URL (EXTERNAL_SOURCE 타입일 때)

        Returns:
            (추출된 context, OG 메타데이터) 튜플
        """
        og_metadata: Optional[OGMetadata] = None

        # EXTERNAL_SOURCE 타입이면 URL 콘텐츠 가져오기
        text_to_analyze = content
        if memo_type == "EXTERNAL_SOURCE" and source_url:
            fetched_content, og_metadata = await fetch_url_content(source_url)
            if fetched_content:
                if content and content.strip():
                    text_to_analyze = (
                        f"사용자 메모: {content}\n\n"
                        f"URL: {source_url}\n\n"
                        f"URL 내용:\n{fetched_content}"
                    )
                else:
                    text_to_analyze = f"URL: {source_url}\n\n{fetched_content}"

        # LLM으로 context 추출
        context = await llm_service.extract_context(text_to_analyze, memo_type)
        return context, og_metadata

    async def match_interests(
        self,
        content: str,
        user_interests: list[str],
    ) -> list[str]:
        """
        메모 내용과 사용자 관심사 매핑

        Args:
            content: 메모 내용
            user_interests: 사용자 관심사 목록

        Returns:
            매핑된 관심사 배열
        """
        return await llm_service.match_interests(content, user_interests)

    async def translate_and_highlight(
        self, text: str
    ) -> tuple[Optional[str], Optional[str], bool, Optional[list[dict]]]:
        """
        언어 감지 + 번역 + 하이라이트 추출

        Args:
            text: 분석할 텍스트

        Returns:
            (언어코드, 번역본, 요약여부, 하이라이트 목록) 튜플
        """
        return await llm_service.translate_and_highlight(text)


# 싱글톤 인스턴스
context_extractor = ContextExtractor()

"""
LLM Context 추출 서비스

메모 저장 시 OpenAI API를 사용하여 context를 추출합니다.
- EXTERNAL_SOURCE 타입: URL에서 컨텐츠를 가져와 분석
- 기타 타입: 입력된 내용을 직접 분석
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional

import httpx
from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class OGMetadata:
    """Open Graph 메타데이터"""

    title: Optional[str] = None
    image: Optional[str] = None
    description: Optional[str] = None


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

        if not self.client:
            logger.warning("OpenAI API key not configured, skipping context extraction")
            # API 키가 없어도 OG 메타데이터는 추출 시도
            if memo_type == "EXTERNAL_SOURCE" and source_url:
                _, og_metadata = await self._fetch_url_content(source_url)
            return None, og_metadata

        try:
            # EXTERNAL_SOURCE 타입이고 URL이 있으면 URL 컨텐츠 가져오기
            text_to_analyze = content
            if memo_type == "EXTERNAL_SOURCE" and source_url:
                fetched_content, og_metadata = await self._fetch_url_content(source_url)
                if fetched_content:
                    text_to_analyze = f"URL: {source_url}\n\n{fetched_content}"

            # LLM 호출
            context = await self._call_llm(text_to_analyze, memo_type)
            return context, og_metadata

        except Exception as e:
            logger.error(f"Failed to extract context: {e}", exc_info=True)
            return None, og_metadata

    async def _fetch_url_content(
        self, url: str
    ) -> tuple[Optional[str], Optional[OGMetadata]]:
        """
        URL에서 컨텐츠와 OG 메타데이터 가져오기

        Args:
            url: 대상 URL

        Returns:
            (추출된 텍스트 컨텐츠, OG 메타데이터) 튜플
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 Zentel/1.0"},
                    follow_redirects=True,
                )
                response.raise_for_status()

                html = response.text

                # OG 메타데이터 추출
                og_metadata = self._extract_og_metadata(html, url)

                # 너무 긴 컨텐츠는 잘라내기
                max_length = 10000
                content = html
                if len(content) > max_length:
                    content = content[:max_length] + "..."

                logger.info(
                    f"Fetched URL content: {url}, length={len(content)}, "
                    f"og_title={og_metadata.title if og_metadata else None}"
                )
                return content, og_metadata

        except Exception as e:
            logger.error(f"Failed to fetch URL content: {url}, error={e}")
            return None, None

    def _extract_og_metadata(self, html: str, base_url: str) -> Optional[OGMetadata]:
        """
        HTML에서 OG 메타데이터 추출

        Args:
            html: HTML 문자열
            base_url: 기본 URL (상대 경로 해석용)

        Returns:
            OGMetadata 또는 None
        """
        try:
            og_title = self._extract_meta_content(html, "og:title")
            og_image = self._extract_meta_content(html, "og:image")
            og_description = self._extract_meta_content(html, "og:description")

            # og:title이 없으면 <title> 태그에서 추출
            if not og_title:
                title_match = re.search(
                    r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE
                )
                if title_match:
                    og_title = title_match.group(1).strip()

            # og:image 상대 경로 처리
            if og_image and not og_image.startswith(("http://", "https://")):
                from urllib.parse import urljoin

                og_image = urljoin(base_url, og_image)

            if og_title or og_image:
                return OGMetadata(
                    title=og_title, image=og_image, description=og_description
                )

            return None

        except Exception as e:
            logger.error(f"Failed to extract OG metadata: {e}")
            return None

    def _extract_meta_content(self, html: str, property_name: str) -> Optional[str]:
        """
        메타 태그에서 content 추출

        Args:
            html: HTML 문자열
            property_name: property 속성 값

        Returns:
            content 값 또는 None
        """
        # property="og:..." 또는 name="og:..." 형태 모두 처리
        patterns = [
            rf'<meta[^>]+property=["\']?{re.escape(property_name)}["\']?[^>]+content=["\']([^"\']+)["\']',
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']?{re.escape(property_name)}["\']?',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1).strip()

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
                            "10단어 이내의 짧은 문구로 이 메모의 핵심 맥락(context)을 한 줄로 표현하세요. "
                            "마크다운 형식 없이 순수한 텍스트로만 응답하세요."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=50,
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
        return f"다음 내용의 핵심 context를 10단어 이내로 표현해주세요:\n\n{text}"


# 싱글톤 인스턴스
context_extractor = ContextExtractor()

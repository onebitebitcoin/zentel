"""
비동기 AI 분석 서비스

메모 저장 후 백그라운드에서 AI 분석을 수행합니다.
- x.com URL인 경우 Playwright로 컨텐츠 추출
- LLM으로 context/facts 추출
- 관심사 매핑 (로그인 사용자)
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.temp_memo import TempMemo
from app.models.user import User
from app.services import llm_service
from app.services.context_extractor import context_extractor
from app.services.twitter_scraper import twitter_scraper
from app.services.youtube_scraper import youtube_scraper

logger = logging.getLogger(__name__)

# SSE 클라이언트 연결 관리
_sse_queues: dict[str, asyncio.Queue] = {}


def register_sse_client(client_id: str, queue: asyncio.Queue) -> None:
    """SSE 클라이언트 등록"""
    _sse_queues[client_id] = queue
    logger.info(f"[AnalysisService] SSE 클라이언트 등록: {client_id}")


def unregister_sse_client(client_id: str) -> None:
    """SSE 클라이언트 등록 해제"""
    if client_id in _sse_queues:
        del _sse_queues[client_id]
        logger.info(f"[AnalysisService] SSE 클라이언트 등록 해제: {client_id}")


async def notify_analysis_complete(memo_id: str, status: str) -> None:
    """모든 SSE 클라이언트에 분석 완료 알림"""
    event_data = {"memo_id": memo_id, "status": status}
    for client_id, queue in list(_sse_queues.items()):
        try:
            await queue.put(event_data)
        except Exception as e:
            logger.warning(f"[AnalysisService] SSE 알림 실패 (client={client_id}): {e}")


class AnalysisService:
    """비동기 AI 분석 서비스"""

    async def run_analysis(
        self,
        memo_id: str,
        db: Session,
        user_id: Optional[str] = None,
        retry_count: int = 3,
    ) -> None:
        """
        메모에 대한 AI 분석 실행

        Args:
            memo_id: 메모 ID
            db: 데이터베이스 세션
            user_id: 사용자 ID (관심사 매핑용)
            retry_count: 재시도 횟수
        """
        logger.info(f"[AnalysisService] 분석 시작: memo_id={memo_id}")

        # 상태를 'analyzing'으로 변경
        memo = db.query(TempMemo).filter(TempMemo.id == memo_id).first()
        if not memo:
            logger.error(f"[AnalysisService] 메모를 찾을 수 없음: memo_id={memo_id}")
            return

        memo.analysis_status = "analyzing"
        memo.analysis_error = None
        db.commit()

        # 재시도 간격 (초)
        retry_delays = [1, 3, 5]

        for attempt in range(retry_count):
            try:
                await self._do_analysis(memo, db, user_id)

                # 성공 - 상태를 'completed'로 변경
                memo.analysis_status = "completed"
                memo.analysis_error = None
                memo.updated_at = datetime.now(timezone.utc).isoformat()
                db.commit()

                logger.info(f"[AnalysisService] 분석 완료: memo_id={memo_id}")

                # SSE로 완료 알림
                await notify_analysis_complete(memo_id, "completed")
                return

            except Exception as e:
                logger.error(
                    f"[AnalysisService] 분석 실패 (시도 {attempt + 1}/{retry_count}): {e}",
                    exc_info=True,
                )

                if attempt < retry_count - 1:
                    # 재시도 대기
                    delay = retry_delays[attempt]
                    logger.info(f"[AnalysisService] {delay}초 후 재시도...")
                    await asyncio.sleep(delay)
                else:
                    # 최종 실패 - 상태를 'failed'로 변경
                    memo.analysis_status = "failed"
                    memo.analysis_error = str(e)
                    memo.updated_at = datetime.now(timezone.utc).isoformat()
                    db.commit()

                    logger.error(f"[AnalysisService] 분석 최종 실패: memo_id={memo_id}")

                    # SSE로 실패 알림
                    await notify_analysis_complete(memo_id, "failed")

    async def _do_analysis(
        self,
        memo: TempMemo,
        db: Session,
        user_id: Optional[str],
    ) -> None:
        """실제 분석 로직"""
        source_url = memo.source_url
        content = memo.content
        fetched_content: Optional[str] = None
        og_title: Optional[str] = None
        og_image: Optional[str] = None

        # x.com URL인 경우 Playwright로 스크래핑
        if source_url and twitter_scraper.is_twitter_url(source_url):
            logger.info(f"[AnalysisService] Twitter URL 감지, 스크래핑 시작: {source_url}")
            result = await twitter_scraper.scrape(source_url)

            if result.success:
                fetched_content = result.content
                og_title = result.og_title
                og_image = result.og_image
                logger.info(
                    f"[AnalysisService] Twitter 스크래핑 성공: "
                    f"content_length={len(fetched_content or '')}"
                )
            else:
                logger.warning(
                    f"[AnalysisService] Twitter 스크래핑 실패: {result.error}"
                )
                # 스크래핑 실패해도 계속 진행 (content만으로 분석)

        # YouTube URL인 경우 자막 스크래핑
        elif source_url and youtube_scraper.is_youtube_url(source_url):
            logger.info(f"[AnalysisService] YouTube URL 감지, 스크래핑 시작: {source_url}")
            result = await youtube_scraper.scrape(source_url)

            if result.success:
                fetched_content = result.content
                og_title = result.og_title
                og_image = result.og_image
                logger.info(
                    f"[AnalysisService] YouTube 스크래핑 성공: "
                    f"content_length={len(fetched_content or '')}, "
                    f"language={result.language}"
                )
            else:
                logger.warning(
                    f"[AnalysisService] YouTube 스크래핑 실패: {result.error}"
                )
                # 스크래핑 실패해도 계속 진행 (content만으로 분석)

        # LLM 분석 (context_extractor 사용)
        if fetched_content:
            # Twitter 컨텐츠가 있으면 합쳐서 분석
            text_to_analyze = content
            if content and content.strip():
                text_to_analyze = (
                    f"사용자 메모: {content}\n\n"
                    f"URL: {source_url}\n\n"
                    f"URL 내용:\n{fetched_content}"
                )
            else:
                text_to_analyze = f"URL: {source_url}\n\n{fetched_content}"

            # context 추출
            context = await llm_service.extract_context(
                text_to_analyze, memo.memo_type
            )

            # 결과 저장
            memo.context = context
            memo.og_title = og_title or memo.og_title
            memo.og_image = og_image or memo.og_image

        else:
            # Twitter 컨텐츠 없이 일반 분석
            context, og_metadata = await context_extractor.extract_context(
                content=content,
                memo_type=memo.memo_type,
                source_url=source_url,
            )

            memo.context = context
            if og_metadata:
                memo.og_title = og_metadata.title or memo.og_title
                memo.og_image = og_metadata.image or memo.og_image

        # 관심사 매핑 (로그인 사용자인 경우)
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.interests:
                logger.info(f"[AnalysisService] 관심사 매핑 시작: user_id={user_id}")
                interests = await context_extractor.match_interests(
                    content=content,
                    user_interests=user.interests,
                )
                memo.interests = interests if interests else None
                logger.info(f"[AnalysisService] 매핑된 관심사: {interests}")

        # 스크래핑된 컨텐츠 저장 (URL 메모용)
        if fetched_content:
            memo.fetched_content = fetched_content

        # 번역 및 하이라이트 추출
        await self._process_translation_and_highlights(memo, fetched_content)

    async def _process_translation_and_highlights(
        self,
        memo: TempMemo,
        fetched_content: Optional[str],
    ) -> None:
        """
        번역 및 하이라이트 처리 (1회 LLM 호출로 통합)

        - 한국어가 아닌 경우: 언어감지 + 번역 + 하이라이트 (번역본 기준)
        - 한국어인 경우: 언어감지 + 하이라이트 (원문 기준), 번역은 스킵
        """
        # 분석할 텍스트 결정 (스크래핑 컨텐츠 우선)
        text_to_analyze = fetched_content or memo.content

        if not text_to_analyze or len(text_to_analyze.strip()) < 20:
            logger.info("[AnalysisService] 텍스트가 너무 짧아 번역/하이라이트 스킵")
            return

        # 1회 LLM 호출로 언어감지 + 번역 + 하이라이트 처리
        logger.info("[AnalysisService] 번역/하이라이트 통합 분석 시작 (1회 LLM 호출)")
        lang, translation, is_summary, highlights = await context_extractor.translate_and_highlight(
            text_to_analyze
        )

        # 결과 저장
        memo.original_language = lang
        memo.translated_content = translation  # 한국어면 None
        memo.is_summary = is_summary  # 요약 여부
        memo.highlights = highlights

        logger.info(
            f"[AnalysisService] 번역/하이라이트 완료: "
            f"lang={lang}, "
            f"translation={'Yes' if translation else 'No'}, "
            f"is_summary={is_summary}, "
            f"highlights={len(highlights) if highlights else 0}"
        )


# 싱글톤 인스턴스
analysis_service = AnalysisService()

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


async def _broadcast_sse_event(event_data: dict, log_context: str = "SSE") -> None:
    """모든 SSE 클라이언트에 이벤트 브로드캐스트 (공통 함수)"""
    for client_id, queue in list(_sse_queues.items()):
        try:
            await queue.put(event_data)
        except Exception as e:
            logger.warning(f"[AnalysisService] {log_context} 알림 실패 (client={client_id}): {e}")


async def notify_analysis_complete(
    memo_id: str,
    status: str,
    error: Optional[str] = None,
) -> None:
    """모든 SSE 클라이언트에 분석 완료 알림"""
    event_data = {"memo_id": memo_id, "status": status, "event_type": "complete"}
    if error:
        event_data["error"] = error
    await _broadcast_sse_event(event_data, "분석 완료")


async def notify_analysis_progress(
    memo_id: str,
    step: str,
    message: str,
    detail: Optional[str] = None,
) -> None:
    """모든 SSE 클라이언트에 분석 진행 상황 알림"""
    event_data = {
        "memo_id": memo_id,
        "event_type": "progress",
        "step": step,
        "message": message,
    }
    if detail:
        event_data["detail"] = detail
    await _broadcast_sse_event(event_data, "분석 진행")


async def notify_comment_ai_response(
    memo_id: str,
    comment_id: str,
    parent_comment_id: str,
    status: str,
    error: Optional[str] = None,
) -> None:
    """모든 SSE 클라이언트에 AI 댓글 응답 알림"""
    event_data = {
        "memo_id": memo_id,
        "comment_id": comment_id,
        "parent_comment_id": parent_comment_id,
        "status": status,
        "event_type": "comment_ai_response",
    }
    if error:
        event_data["error"] = error
    await _broadcast_sse_event(event_data, "AI 댓글 응답")
    if comment_id:
        logger.info(f"[AnalysisService] AI 댓글 응답 알림 전송: {comment_id}")


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

        # 분석 시작 알림
        await notify_analysis_progress(memo_id, "start", "분석 시작")

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
                    error_msg = str(e)
                    memo.analysis_status = "failed"
                    memo.analysis_error = error_msg
                    memo.updated_at = datetime.now(timezone.utc).isoformat()
                    db.commit()

                    logger.error(f"[AnalysisService] 분석 최종 실패: memo_id={memo_id}, error={error_msg}")

                    # SSE로 실패 알림 (에러 메시지 포함)
                    await notify_analysis_complete(memo_id, "failed", error=error_msg)

    async def _fetch_external_content(
        self,
        memo: TempMemo,
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        외부 URL에서 콘텐츠 추출 (Twitter/YouTube/일반 웹페이지)

        Returns:
            (fetched_content, og_title, og_image) 튜플
        """
        source_url = memo.source_url
        if not source_url:
            return None, None, None

        fetched_content: Optional[str] = None
        og_title: Optional[str] = None
        og_image: Optional[str] = None

        # Twitter URL
        if twitter_scraper.is_twitter_url(source_url):
            logger.info(f"[AnalysisService] Twitter URL 감지, 스크래핑 시작: {source_url}")
            await notify_analysis_progress(memo.id, "scrape", "Twitter 콘텐츠 추출 중", source_url)
            result = await twitter_scraper.scrape(source_url)

            if result.success:
                fetched_content = result.content
                og_title = result.og_title
                og_image = result.og_image
                logger.info(
                    f"[AnalysisService] Twitter 스크래핑 성공: "
                    f"content_length={len(fetched_content or '')}"
                )
                await notify_analysis_progress(
                    memo.id, "scrape_done", "Twitter 콘텐츠 추출 완료",
                    f"{len(fetched_content or '')} 자"
                )
            else:
                logger.warning(f"[AnalysisService] Twitter 스크래핑 실패: {result.error}")
                await notify_analysis_progress(
                    memo.id, "scrape_failed", "Twitter 스크래핑 실패 (메모 내용으로 분석)",
                    result.error
                )

        # YouTube URL
        elif youtube_scraper.is_youtube_url(source_url):
            logger.info(f"[AnalysisService] YouTube URL 감지, 스크래핑 시작: {source_url}")
            await notify_analysis_progress(memo.id, "scrape", "YouTube 자막 추출 중", source_url)
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
                await notify_analysis_progress(
                    memo.id, "scrape_done", "YouTube 자막 추출 완료",
                    f"{len(fetched_content or '')} 자, 언어: {result.language}"
                )
            else:
                logger.warning(f"[AnalysisService] YouTube 스크래핑 실패: {result.error}")
                await notify_analysis_progress(
                    memo.id, "scrape_failed", "YouTube 자막 추출 실패 (메모 내용으로 분석)",
                    result.error
                )

        # 일반 URL (GitHub, 웹페이지 등)
        else:
            from app.services.url_fetcher import fetch_url_content
            logger.info(f"[AnalysisService] 일반 URL 감지, 콘텐츠 추출 시작: {source_url}")
            await notify_analysis_progress(memo.id, "scrape", "웹페이지 콘텐츠 추출 중", source_url)
            url_content, og_metadata = await fetch_url_content(source_url)

            if url_content:
                fetched_content = url_content
                if og_metadata:
                    og_title = og_metadata.title
                    og_image = og_metadata.image
                logger.info(
                    f"[AnalysisService] URL 콘텐츠 추출 성공: "
                    f"content_length={len(fetched_content or '')}"
                )
                await notify_analysis_progress(
                    memo.id, "scrape_done", "웹페이지 콘텐츠 추출 완료",
                    f"{len(fetched_content or '')} 자"
                )
            else:
                logger.warning(f"[AnalysisService] URL 콘텐츠 추출 실패: {source_url}")
                await notify_analysis_progress(
                    memo.id, "scrape_failed", "웹페이지 추출 실패 (메모 내용으로 분석)"
                )

        return fetched_content, og_title, og_image

    async def _extract_context_and_interests(
        self,
        memo: TempMemo,
        fetched_content: Optional[str],
        db: Session,
        user_id: Optional[str],
    ) -> tuple[Optional[str], list[str]]:
        """
        LLM으로 context와 관심사를 한 번에 추출 (LLM 호출 최적화)

        기존: extract_context (1회) + match_interests (1회) = 2회 LLM 호출
        개선: extract_context_and_interests (1회) = 1회 LLM 호출
        """
        await notify_analysis_progress(memo.id, "llm", "AI가 내용을 분석 중")

        source_url = memo.source_url
        content = memo.content

        if fetched_content:
            # URL 콘텐츠가 있으면 합쳐서 분석
            if content and content.strip():
                text_to_analyze = (
                    f"사용자 메모: {content}\n\n"
                    f"URL: {source_url}\n\n"
                    f"URL 내용:\n{fetched_content}"
                )
            else:
                text_to_analyze = f"URL: {source_url}\n\n{fetched_content}"
        else:
            # URL이 없는 일반 텍스트 메모
            text_to_analyze = content

        # 사용자 관심사 가져오기
        user_interests = None
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.interests:
                user_interests = user.interests
                logger.info(f"[AnalysisService] 관심사 매핑 포함: user_id={user_id}")

        # 통합 LLM 호출 (context + 관심사)
        context, interests = await llm_service.extract_context_and_interests(
            text_to_analyze, memo.memo_type, user_interests
        )

        await notify_analysis_progress(memo.id, "llm_done", "AI 분석 완료")

        if interests:
            await notify_analysis_progress(
                memo.id, "interests_done", "관심사 매핑 완료",
                ", ".join(interests)
            )

        return context, interests

    async def _do_analysis(
        self,
        memo: TempMemo,
        db: Session,
        user_id: Optional[str],
    ) -> None:
        """실제 분석 로직 (각 단계별 함수 조합)"""
        # 1. 외부 콘텐츠 추출
        fetched_content, og_title, og_image = await self._fetch_external_content(memo)

        # 2. LLM 분석 (context + 관심사 통합 추출 - LLM 호출 최적화)
        context, interests = await self._extract_context_and_interests(
            memo, fetched_content, db, user_id
        )
        memo.context = context
        memo.interests = interests if interests else None
        if og_title:
            memo.og_title = og_title
        if og_image:
            memo.og_image = og_image

        # 3. 스크래핑된 콘텐츠 저장
        if fetched_content:
            memo.fetched_content = fetched_content
            logger.info(
                f"[AnalysisService] fetched_content 저장: "
                f"length={len(fetched_content)}, "
                f"preview={fetched_content[:100]}..."
            )
        else:
            logger.warning(f"[AnalysisService] fetched_content 없음, source_url={memo.source_url}")

        # 4. 번역 및 하이라이트 추출 (EXTERNAL_SOURCE + URL + 스크래핑 성공 시에만)
        should_process_content = (
            memo.memo_type == "EXTERNAL_SOURCE" and
            memo.source_url and
            fetched_content
        )

        if should_process_content:
            await self._process_translation_and_highlights(memo, fetched_content)
        else:
            logger.info(
                f"[AnalysisService] 번역/하이라이트 스킵: "
                f"memo_type={memo.memo_type}, "
                f"source_url={'있음' if memo.source_url else '없음'}, "
                f"fetched_content={'있음' if fetched_content else '없음'}"
            )
            await notify_analysis_progress(
                memo.id, "translate_skip",
                "이 메모 타입은 본문 처리를 건너뜁니다"
            )

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
            await notify_analysis_progress(memo.id, "translate_skip", "텍스트가 짧아 번역 스킵")
            return

        # 1회 LLM 호출로 언어감지 + 번역 + 하이라이트 처리
        logger.info("[AnalysisService] 번역/하이라이트 통합 분석 시작 (1회 LLM 호출)")
        await notify_analysis_progress(memo.id, "translate", "번역 및 하이라이트 추출 중")
        lang, translation, is_summary, highlights = await context_extractor.translate_and_highlight(
            text_to_analyze
        )

        # 결과 저장
        memo.original_language = lang
        memo.translated_content = translation  # 한국어면 정리된 텍스트, 외국어면 번역본
        memo.is_summary = is_summary  # 요약 여부
        memo.highlights = highlights

        # display_content 결정: 번역/정리된 텍스트가 있으면 사용, 없으면 원본
        # 하이라이트는 display_content 기준으로 추출됨
        memo.display_content = translation if translation else text_to_analyze

        logger.info(
            f"[AnalysisService] 번역/하이라이트 완료: "
            f"lang={lang}, "
            f"translation={'Yes' if translation else 'No'}, "
            f"is_summary={is_summary}, "
            f"highlights={len(highlights) if highlights else 0}, "
            f"display_content_len={len(memo.display_content) if memo.display_content else 0}"
        )
        detail = f"언어: {lang}"
        if translation:
            detail += ", 번역 완료"
        if highlights:
            detail += f", 하이라이트 {len(highlights)}개"
        await notify_analysis_progress(memo.id, "translate_done", "번역/하이라이트 완료", detail)


# 싱글톤 인스턴스
analysis_service = AnalysisService()

"""
임시 메모 (Temporary Memo) API 라우터
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.core.deps import get_current_user
from app.database import get_db
from app.models.temp_memo import TempMemo
from app.models.user import User
from app.schemas.temp_memo import (
    AnalysisStatus,
    MemoCommentSummary,
    MemoType,
    TempMemoCreate,
    TempMemoListItem,
    TempMemoListResponse,
    TempMemoOut,
    TempMemoUpdate,
)
from app.services.analysis_service import (
    analysis_service,
    register_sse_client,
    unregister_sse_client,
)
from app.services.context_extractor import context_extractor
from app.services.memo_repository import comment_repository, memo_repository

logger = logging.getLogger(__name__)

# URL 추출 정규식
URL_PATTERN = re.compile(
    r"https?://[^\s<>\"')\]]+",
    re.IGNORECASE,
)

router = APIRouter(prefix="/temp-memos", tags=["temp-memos"])


def get_user_memo(db: Session, memo_id: str, user_id: str) -> TempMemo:
    """사용자 소유 메모 조회 (없거나 소유하지 않으면 404)"""
    memo = memo_repository.get_user_memo(db, memo_id, user_id)
    if not memo:
        raise HTTPException(status_code=404, detail="메모를 찾을 수 없습니다.")
    return memo


def _get_comment_summary(
    db: Session, memo_id: str
) -> tuple[int, Optional[MemoCommentSummary]]:
    """메모의 댓글 개수와 최신 댓글 요약 반환 (공통 함수)"""
    count, latest = comment_repository.get_comment_count_and_latest(db, memo_id)
    latest_summary = None
    if latest:
        latest_summary = MemoCommentSummary(
            id=latest.id,
            content=latest.content,
            created_at=latest.created_at,
        )
    return count, latest_summary


def memo_to_list_item(
    memo: TempMemo,
    comment_count: int = 0,
    latest_comment: Optional[MemoCommentSummary] = None,
    fetch_failed: bool = False,
    fetch_message: Optional[str] = None,
) -> TempMemoListItem:
    """TempMemo를 TempMemoListItem으로 변환 (본문 데이터 포함)"""
    return TempMemoListItem(
        id=memo.id,
        memo_type=memo.memo_type,
        content=memo.content,
        context=memo.context,
        summary=memo.summary,
        interests=memo.interests,
        source_url=memo.source_url,
        og_title=memo.og_title,
        og_image=memo.og_image,
        fetch_failed=fetch_failed,
        fetch_message=fetch_message,
        analysis_status=AnalysisStatus(memo.analysis_status),
        analysis_error=memo.analysis_error,
        original_language=memo.original_language,
        is_summary=memo.is_summary,
        has_display_content=bool(memo.display_content),
        # 본문 데이터 포함 (추가 API 호출 제거)
        translated_content=memo.translated_content,
        display_content=memo.display_content,
        highlights=memo.highlights,
        created_at=memo.created_at,
        updated_at=memo.updated_at,
        comment_count=comment_count,
        latest_comment=latest_comment,
    )


def memo_to_out(
    db: Session,
    memo: TempMemo,
    fetch_failed: bool = False,
    fetch_message: Optional[str] = None,
) -> TempMemoOut:
    """TempMemo를 TempMemoOut으로 변환 (댓글 정보 포함)"""
    count, latest_summary = _get_comment_summary(db, memo.id)
    return TempMemoOut(
        id=memo.id,
        memo_type=memo.memo_type,
        content=memo.content,
        context=memo.context,
        summary=memo.summary,
        interests=memo.interests,
        source_url=memo.source_url,
        og_title=memo.og_title,
        og_image=memo.og_image,
        fetch_failed=fetch_failed,
        fetch_message=fetch_message,
        analysis_status=AnalysisStatus(memo.analysis_status),
        analysis_error=memo.analysis_error,
        original_language=memo.original_language,
        translated_content=memo.translated_content,
        fetched_content=memo.fetched_content,
        display_content=memo.display_content,
        is_summary=memo.is_summary,
        highlights=memo.highlights,
        created_at=memo.created_at,
        updated_at=memo.updated_at,
        comment_count=count,
        latest_comment=latest_summary,
    )


def _run_background_analysis(
    memo_id: str,
    user_id: Optional[str],
    db_url: str,
):
    """백그라운드에서 분석 실행 (별도 스레드에서 호출)"""
    from app.database import SessionLocal
    from app.utils import run_async_in_thread

    async def _async_analysis():
        db = SessionLocal()
        try:
            await analysis_service.run_analysis(memo_id, db, user_id)
        finally:
            db.close()

    run_async_in_thread(_async_analysis)


@router.post("", response_model=TempMemoOut, status_code=201)
async def create_temp_memo(
    memo: TempMemoCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """임시 메모 생성 (AI 분석은 백그라운드에서 비동기 처리)"""
    # EXTERNAL_SOURCE 타입이면 content에서 URL 자동 추출
    source_url = memo.source_url
    if memo.memo_type == MemoType.EXTERNAL_SOURCE and not source_url:
        urls = URL_PATTERN.findall(memo.content)
        if urls:
            source_url = urls[0]
            logger.info(f"Auto-extracted URL from content: {source_url}")

    logger.info(
        f"Creating temp memo: type={memo.memo_type}, user_id={current_user.id}, "
        f"content_length={len(memo.content)}, source_url={source_url}"
    )

    # 메모 즉시 저장 (analysis_status = "pending")
    db_memo = TempMemo(
        user_id=current_user.id,
        memo_type=memo.memo_type.value,
        content=memo.content,
        source_url=source_url,
        analysis_status="pending",
    )
    db_memo = memo_repository.create(db, db_memo)

    logger.info(f"Created temp memo: id={db_memo.id}, starting background analysis")

    # 백그라운드에서 AI 분석 실행
    from app.config import settings

    background_tasks.add_task(
        _run_background_analysis,
        db_memo.id,
        current_user.id if current_user else None,
        settings.DATABASE_URL,
    )

    return memo_to_out(db, db_memo)


@router.get("", response_model=TempMemoListResponse)
async def list_temp_memos(
    type: Optional[MemoType] = Query(default=None, description="메모 타입 필터"),
    limit: int = Query(default=10, ge=1, le=100, description="가져올 개수"),
    offset: int = Query(default=0, ge=0, description="시작 위치"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """임시 메모 목록 조회 (최신순, 본인 메모만)"""
    logger.info(
        f"Listing temp memos: user_id={current_user.id}, type={type}, "
        f"limit={limit}, offset={offset}"
    )

    # Repository를 통해 조회
    memo_type_value = type.value if type else None
    db_items, total = memo_repository.list_user_memos(
        db, current_user.id, memo_type_value, limit, offset
    )

    next_offset = offset + limit if offset + limit < total else None

    # 댓글 정보 일괄 조회 (N+1 쿼리 방지: 2*N 쿼리 → 2쿼리)
    memo_ids = [memo.id for memo in db_items]
    comment_stats = comment_repository.get_comment_stats_bulk(db, memo_ids)

    # 메모 목록 변환 (본문 데이터 포함)
    items = []
    for memo in db_items:
        count, latest = comment_stats.get(memo.id, (0, None))
        latest_summary = None
        if latest:
            latest_summary = MemoCommentSummary(
                id=latest.id,
                content=latest.content,
                created_at=latest.created_at,
            )
        items.append(memo_to_list_item(memo, count, latest_summary))

    logger.info(f"Found {len(items)} memos (total: {total})")
    return TempMemoListResponse(items=items, total=total, next_offset=next_offset)


@router.get("/analysis-events")
async def analysis_events(request: Request):
    """분석 완료 이벤트를 SSE로 전송"""
    client_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()

    register_sse_client(client_id, queue)

    async def event_generator():
        try:
            while True:
                # 클라이언트 연결 확인
                if await request.is_disconnected():
                    logger.info(f"[SSE] Client disconnected: {client_id}")
                    break

                try:
                    # 5초마다 keepalive ping 전송
                    event = await asyncio.wait_for(queue.get(), timeout=5.0)
                    # 이벤트 타입에 따라 다른 SSE 이벤트명 사용
                    event_type = event.get("event_type", "complete")
                    if event_type == "progress":
                        yield {
                            "event": "analysis_progress",
                            "data": json.dumps(event),
                        }
                    elif event_type == "comment_ai_response":
                        yield {
                            "event": "comment_ai_response",
                            "data": json.dumps(event),
                        }
                    else:
                        yield {
                            "event": "analysis_complete",
                            "data": json.dumps(event),
                        }
                except asyncio.TimeoutError:
                    # keepalive ping
                    yield {"event": "ping", "data": ""}

        finally:
            unregister_sse_client(client_id)

    return EventSourceResponse(event_generator())


@router.get("/{memo_id}", response_model=TempMemoOut)
async def get_temp_memo(
    memo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """임시 메모 상세 조회 (본인 메모만)"""
    logger.info(f"Getting temp memo: id={memo_id}, user_id={current_user.id}")

    db_memo = get_user_memo(db, memo_id, current_user.id)

    return memo_to_out(db, db_memo)


@router.patch("/{memo_id}", response_model=TempMemoOut)
async def update_temp_memo(
    memo_id: str,
    memo: TempMemoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """임시 메모 수정 (본인 메모만)"""
    logger.info(f"Updating temp memo: id={memo_id}, user_id={current_user.id}")

    db_memo = get_user_memo(db, memo_id, current_user.id)

    if memo.memo_type is not None:
        db_memo.memo_type = memo.memo_type.value
    if memo.content is not None:
        db_memo.content = memo.content

    # 관심사 다시 매핑 (rematch_interests가 True인 경우)
    if memo.rematch_interests and current_user and current_user.interests:
        logger.info(f"Rematching interests for memo: {memo_id}")
        content_to_match = memo.content if memo.content else db_memo.content
        matched_interests = await context_extractor.match_interests(
            content=content_to_match,
            user_interests=current_user.interests,
        )
        db_memo.interests = matched_interests if matched_interests else None
        logger.info(f"Rematched interests: {matched_interests}")
    elif memo.interests is not None:
        # 관심사 직접 수정 (빈 배열이면 None으로 저장)
        db_memo.interests = memo.interests if memo.interests else None
        logger.info(f"Updated interests: {memo.interests}")

    db_memo.updated_at = datetime.now(timezone.utc).isoformat()

    db_memo = memo_repository.update(db, db_memo)

    logger.info(f"Updated temp memo: id={memo_id}")
    return memo_to_out(db, db_memo)


@router.delete("/{memo_id}", status_code=204)
async def delete_temp_memo(
    memo_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """임시 메모 삭제 (본인 메모만)"""
    logger.info(f"Deleting temp memo: id={memo_id}, user_id={current_user.id}")

    db_memo = get_user_memo(db, memo_id, current_user.id)

    memo_repository.delete(db, db_memo)

    logger.info(f"Deleted temp memo: id={memo_id}")
    return None


@router.post("/{memo_id}/reanalyze", response_model=TempMemoOut)
async def reanalyze_memo(
    memo_id: str,
    background_tasks: BackgroundTasks,
    force: bool = Query(default=False, description="강제 재분석 (analyzing 상태 무시)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """메모 재분석 요청 (본인 메모만)"""
    logger.info(f"Reanalyze request: memo_id={memo_id}, user_id={current_user.id}, force={force}")

    db_memo = get_user_memo(db, memo_id, current_user.id)

    # 이미 분석 중인 경우 거부 (force=true면 무시)
    if not force and db_memo.analysis_status == "analyzing":
        raise HTTPException(status_code=400, detail="이미 분석 중입니다. 강제 재분석하려면 force=true를 사용하세요.")

    # 상태를 pending으로 리셋
    db_memo.analysis_status = "pending"
    db_memo.analysis_error = None
    db.commit()
    db.refresh(db_memo)

    # 백그라운드에서 재분석 실행
    from app.config import settings

    background_tasks.add_task(
        _run_background_analysis,
        db_memo.id,
        current_user.id if current_user else None,
        settings.DATABASE_URL,
    )

    logger.info(f"Reanalyze started: memo_id={memo_id}")
    return memo_to_out(db, db_memo)

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
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.core.deps import get_current_user_optional
from app.database import get_db
from app.models.memo_comment import MemoComment
from app.models.temp_memo import TempMemo
from app.models.user import User
from app.schemas.temp_memo import (
    AnalysisStatus,
    MemoCommentSummary,
    MemoType,
    TempMemoCreate,
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

logger = logging.getLogger(__name__)

# URL 추출 정규식
URL_PATTERN = re.compile(
    r"https?://[^\s<>\"')\]]+",
    re.IGNORECASE,
)

router = APIRouter(prefix="/temp-memos", tags=["temp-memos"])


def get_memo_comment_info(db: Session, memo_id: str) -> tuple[int, MemoComment | None]:
    """메모의 댓글 개수와 최신 댓글 반환"""
    count = db.query(func.count(MemoComment.id)).filter(MemoComment.memo_id == memo_id).scalar()
    latest = (
        db.query(MemoComment)
        .filter(MemoComment.memo_id == memo_id)
        .order_by(desc(MemoComment.created_at))
        .first()
    )
    return count, latest


def memo_to_out(
    db: Session,
    memo: TempMemo,
    fetch_failed: bool = False,
    fetch_message: Optional[str] = None,
) -> TempMemoOut:
    """TempMemo를 TempMemoOut으로 변환 (댓글 정보 포함)"""
    count, latest = get_memo_comment_info(db, memo.id)
    latest_summary = None
    if latest:
        latest_summary = MemoCommentSummary(
            id=latest.id,
            content=latest.content,
            created_at=latest.created_at,
        )
    return TempMemoOut(
        id=memo.id,
        memo_type=memo.memo_type,
        content=memo.content,
        context=memo.context,
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
    import asyncio

    from app.database import SessionLocal

    async def _async_analysis():
        db = SessionLocal()
        try:
            await analysis_service.run_analysis(memo_id, db, user_id)
        finally:
            db.close()

    # 새 이벤트 루프에서 실행
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_async_analysis())
    finally:
        loop.close()


@router.post("", response_model=TempMemoOut, status_code=201)
async def create_temp_memo(
    memo: TempMemoCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
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
        f"Creating temp memo: type={memo.memo_type}, "
        f"content_length={len(memo.content)}, source_url={source_url}"
    )

    # 메모 즉시 저장 (analysis_status = "pending")
    db_memo = TempMemo(
        memo_type=memo.memo_type.value,
        content=memo.content,
        source_url=source_url,
        analysis_status="pending",
    )
    db.add(db_memo)
    db.commit()
    db.refresh(db_memo)

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
def list_temp_memos(
    type: Optional[MemoType] = Query(default=None, description="메모 타입 필터"),
    limit: int = Query(default=10, ge=1, le=100, description="가져올 개수"),
    offset: int = Query(default=0, ge=0, description="시작 위치"),
    db: Session = Depends(get_db),
):
    """임시 메모 목록 조회 (최신순)"""
    logger.info(f"Listing temp memos: type={type}, limit={limit}, offset={offset}")

    query = db.query(TempMemo)

    if type:
        query = query.filter(TempMemo.memo_type == type.value)

    total = query.count()
    db_items = query.order_by(desc(TempMemo.created_at)).offset(offset).limit(limit).all()

    next_offset = offset + limit if offset + limit < total else None

    # 댓글 정보 포함하여 변환
    items = [memo_to_out(db, memo) for memo in db_items]

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
def get_temp_memo(
    memo_id: str,
    db: Session = Depends(get_db),
):
    """임시 메모 상세 조회"""
    logger.info(f"Getting temp memo: id={memo_id}")

    db_memo = db.query(TempMemo).filter(TempMemo.id == memo_id).first()
    if not db_memo:
        logger.warning(f"Temp memo not found: id={memo_id}")
        raise HTTPException(status_code=404, detail="메모를 찾을 수 없습니다.")

    return memo_to_out(db, db_memo)


@router.patch("/{memo_id}", response_model=TempMemoOut)
async def update_temp_memo(
    memo_id: str,
    memo: TempMemoUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """임시 메모 수정"""
    logger.info(f"Updating temp memo: id={memo_id}")

    db_memo = db.query(TempMemo).filter(TempMemo.id == memo_id).first()
    if not db_memo:
        logger.warning(f"Temp memo not found: id={memo_id}")
        raise HTTPException(status_code=404, detail="메모를 찾을 수 없습니다.")

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

    db.commit()
    db.refresh(db_memo)

    logger.info(f"Updated temp memo: id={memo_id}")
    return memo_to_out(db, db_memo)


@router.delete("/{memo_id}", status_code=204)
def delete_temp_memo(
    memo_id: str,
    db: Session = Depends(get_db),
):
    """임시 메모 삭제"""
    logger.info(f"Deleting temp memo: id={memo_id}")

    db_memo = db.query(TempMemo).filter(TempMemo.id == memo_id).first()
    if not db_memo:
        logger.warning(f"Temp memo not found: id={memo_id}")
        raise HTTPException(status_code=404, detail="메모를 찾을 수 없습니다.")

    db.delete(db_memo)
    db.commit()

    logger.info(f"Deleted temp memo: id={memo_id}")
    return None


@router.post("/{memo_id}/reanalyze", response_model=TempMemoOut)
async def reanalyze_memo(
    memo_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """메모 재분석 요청"""
    logger.info(f"Reanalyze request: memo_id={memo_id}")

    db_memo = db.query(TempMemo).filter(TempMemo.id == memo_id).first()
    if not db_memo:
        logger.warning(f"Temp memo not found: id={memo_id}")
        raise HTTPException(status_code=404, detail="메모를 찾을 수 없습니다.")

    # 이미 분석 중인 경우 거부
    if db_memo.analysis_status == "analyzing":
        raise HTTPException(status_code=400, detail="이미 분석 중입니다.")

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

"""
임시 메모 (Temporary Memo) API 라우터
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_optional
from app.database import get_db
from app.models.memo_comment import MemoComment
from app.models.temp_memo import TempMemo
from app.models.user import User
from app.schemas.temp_memo import (
    MemoCommentSummary,
    MemoType,
    TempMemoCreate,
    TempMemoListResponse,
    TempMemoOut,
    TempMemoUpdate,
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
        facts=memo.facts,
        interests=memo.interests,
        source_url=memo.source_url,
        og_title=memo.og_title,
        og_image=memo.og_image,
        fetch_failed=fetch_failed,
        fetch_message=fetch_message,
        created_at=memo.created_at,
        updated_at=memo.updated_at,
        comment_count=count,
        latest_comment=latest_summary,
    )


@router.post("", response_model=TempMemoOut, status_code=201)
async def create_temp_memo(
    memo: TempMemoCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """임시 메모 생성 (LLM context 추출 포함)"""
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

    # LLM으로 context 추출 + OG 메타데이터
    context, og_metadata, facts = await context_extractor.extract_context(
        content=memo.content,
        memo_type=memo.memo_type.value,
        source_url=source_url,
    )

    if context:
        logger.info(f"Context extracted: {len(context)} chars")
    else:
        logger.info("No context extracted")

    if og_metadata:
        logger.info(f"OG metadata: title={og_metadata.title}, image={og_metadata.image}")

    if facts:
        logger.info(f"Facts extracted: {len(facts)} items")

    # 로그인 사용자의 관심사 매핑
    interests: Optional[list[str]] = None
    if current_user and current_user.interests:
        logger.info(f"Matching interests for user: {current_user.id}")
        interests = await context_extractor.match_interests(
            content=memo.content,
            user_interests=current_user.interests,
        )
        if interests:
            logger.info(f"Matched interests: {interests}")
        else:
            logger.info("No interests matched")

    db_memo = TempMemo(
        memo_type=memo.memo_type.value,
        content=memo.content,
        context=context,
        facts=facts,
        interests=interests if interests else None,
        source_url=source_url,
        og_title=og_metadata.title if og_metadata else None,
        og_image=og_metadata.image if og_metadata else None,
    )
    db.add(db_memo)
    db.commit()
    db.refresh(db_memo)

    logger.info(f"Created temp memo: id={db_memo.id}")

    # fetch_failed 정보 전달
    fetch_failed = og_metadata.fetch_failed if og_metadata else False
    fetch_message = og_metadata.fetch_message if og_metadata else None

    return memo_to_out(db, db_memo, fetch_failed=fetch_failed, fetch_message=fetch_message)


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

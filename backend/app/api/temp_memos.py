"""
임시 메모 (Temporary Memo) API 라우터
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.temp_memo import TempMemo
from app.schemas.temp_memo import (
    MemoType,
    TempMemoCreate,
    TempMemoListResponse,
    TempMemoOut,
    TempMemoUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/temp-memos", tags=["temp-memos"])


@router.post("", response_model=TempMemoOut, status_code=201)
def create_temp_memo(
    memo: TempMemoCreate,
    db: Session = Depends(get_db),
):
    """임시 메모 생성"""
    logger.info(f"Creating temp memo: type={memo.memo_type}, content_length={len(memo.content)}")

    db_memo = TempMemo(
        memo_type=memo.memo_type.value,
        content=memo.content,
    )
    db.add(db_memo)
    db.commit()
    db.refresh(db_memo)

    logger.info(f"Created temp memo: id={db_memo.id}")
    return db_memo


@router.get("", response_model=TempMemoListResponse)
def list_temp_memos(
    type: Optional[MemoType] = Query(default=None, description="메모 타입 필터"),
    limit: int = Query(default=30, ge=1, le=100, description="가져올 개수"),
    offset: int = Query(default=0, ge=0, description="시작 위치"),
    db: Session = Depends(get_db),
):
    """임시 메모 목록 조회 (최신순)"""
    logger.info(f"Listing temp memos: type={type}, limit={limit}, offset={offset}")

    query = db.query(TempMemo)

    if type:
        query = query.filter(TempMemo.memo_type == type.value)

    total = query.count()
    items = query.order_by(desc(TempMemo.created_at)).offset(offset).limit(limit).all()

    next_offset = offset + limit if offset + limit < total else None

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

    return db_memo


@router.patch("/{memo_id}", response_model=TempMemoOut)
def update_temp_memo(
    memo_id: str,
    memo: TempMemoUpdate,
    db: Session = Depends(get_db),
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

    db_memo.updated_at = datetime.now(timezone.utc).isoformat()

    db.commit()
    db.refresh(db_memo)

    logger.info(f"Updated temp memo: id={memo_id}")
    return db_memo


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

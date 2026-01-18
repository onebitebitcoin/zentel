"""
메모 댓글 (MemoComment) API 라우터
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.memo_comment import MemoComment
from app.models.temp_memo import TempMemo
from app.schemas.memo_comment import (
    MemoCommentCreate,
    MemoCommentListResponse,
    MemoCommentOut,
    MemoCommentUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/temp-memos", tags=["memo-comments"])


def get_memo_or_404(memo_id: str, db: Session) -> TempMemo:
    """메모 조회, 없으면 404"""
    memo = db.query(TempMemo).filter(TempMemo.id == memo_id).first()
    if not memo:
        logger.warning(f"Memo not found: id={memo_id}")
        raise HTTPException(status_code=404, detail="메모를 찾을 수 없습니다.")
    return memo


@router.post("/{memo_id}/comments", response_model=MemoCommentOut, status_code=201)
def create_comment(
    memo_id: str,
    comment: MemoCommentCreate,
    db: Session = Depends(get_db),
):
    """댓글 작성"""
    logger.info(f"Creating comment for memo: {memo_id}")

    # 메모 존재 확인
    get_memo_or_404(memo_id, db)

    db_comment = MemoComment(
        memo_id=memo_id,
        content=comment.content,
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)

    logger.info(f"Created comment: id={db_comment.id}")
    return db_comment


@router.get("/{memo_id}/comments", response_model=MemoCommentListResponse)
def list_comments(
    memo_id: str,
    db: Session = Depends(get_db),
):
    """댓글 목록 조회 (최신순)"""
    logger.info(f"Listing comments for memo: {memo_id}")

    # 메모 존재 확인
    get_memo_or_404(memo_id, db)

    query = db.query(MemoComment).filter(MemoComment.memo_id == memo_id)
    total = query.count()
    items = query.order_by(desc(MemoComment.created_at)).all()

    logger.info(f"Found {len(items)} comments")
    return MemoCommentListResponse(items=items, total=total)


@router.patch("/{memo_id}/comments/{comment_id}", response_model=MemoCommentOut)
def update_comment(
    memo_id: str,
    comment_id: str,
    comment: MemoCommentUpdate,
    db: Session = Depends(get_db),
):
    """댓글 수정"""
    logger.info(f"Updating comment: id={comment_id}")

    # 메모 존재 확인
    get_memo_or_404(memo_id, db)

    db_comment = (
        db.query(MemoComment)
        .filter(MemoComment.id == comment_id, MemoComment.memo_id == memo_id)
        .first()
    )
    if not db_comment:
        logger.warning(f"Comment not found: id={comment_id}")
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")

    if comment.content is not None:
        db_comment.content = comment.content

    db_comment.updated_at = datetime.now(timezone.utc).isoformat()

    db.commit()
    db.refresh(db_comment)

    logger.info(f"Updated comment: id={comment_id}")
    return db_comment


@router.delete("/{memo_id}/comments/{comment_id}", status_code=204)
def delete_comment(
    memo_id: str,
    comment_id: str,
    db: Session = Depends(get_db),
):
    """댓글 삭제"""
    logger.info(f"Deleting comment: id={comment_id}")

    # 메모 존재 확인
    get_memo_or_404(memo_id, db)

    db_comment = (
        db.query(MemoComment)
        .filter(MemoComment.id == comment_id, MemoComment.memo_id == memo_id)
        .first()
    )
    if not db_comment:
        logger.warning(f"Comment not found: id={comment_id}")
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")

    db.delete(db_comment)
    db.commit()

    logger.info(f"Deleted comment: id={comment_id}")
    return None

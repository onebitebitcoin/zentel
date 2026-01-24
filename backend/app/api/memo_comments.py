"""
메모 댓글 (MemoComment) API 라우터
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.deps import get_current_user_optional
from app.database import SessionLocal, get_db
from app.models.memo_comment import MemoComment
from app.models.temp_memo import TempMemo
from app.models.user import User
from app.schemas.memo_comment import (
    MemoCommentCreate,
    MemoCommentListResponse,
    MemoCommentOut,
    MemoCommentUpdate,
)
from app.services.analysis_service import notify_comment_ai_response
from app.services.comment_ai_service import generate_ai_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/temp-memos", tags=["memo-comments"])


def get_memo_or_404(memo_id: str, db: Session) -> TempMemo:
    """메모 조회, 없으면 404"""
    memo = db.query(TempMemo).filter(TempMemo.id == memo_id).first()
    if not memo:
        logger.warning(f"Memo not found: id={memo_id}")
        raise HTTPException(status_code=404, detail="메모를 찾을 수 없습니다.")
    return memo


def _run_ai_response_task(
    comment_id: str, memo_id: str, user_id: Optional[str] = None
) -> None:
    """백그라운드에서 AI 응답 생성 실행"""
    async def _async_task():
        db = SessionLocal()
        try:
            ai_comment = await generate_ai_response(comment_id, db, user_id)
            if ai_comment:
                await notify_comment_ai_response(
                    memo_id=memo_id,
                    comment_id=ai_comment.id,
                    parent_comment_id=comment_id,
                    status="completed",
                )
            else:
                # AI 응답 생성 실패 - DB에서 에러 메시지 조회
                user_comment = db.query(MemoComment).filter(
                    MemoComment.id == comment_id
                ).first()
                error_msg = (
                    user_comment.response_error
                    if user_comment and user_comment.response_error
                    else "AI 응답 생성 실패"
                )
                await notify_comment_ai_response(
                    memo_id=memo_id,
                    comment_id="",
                    parent_comment_id=comment_id,
                    status="failed",
                    error=error_msg,
                )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"AI 응답 생성 에러: {error_msg}", exc_info=True)
            await notify_comment_ai_response(
                memo_id=memo_id,
                comment_id="",
                parent_comment_id=comment_id,
                status="failed",
                error=error_msg,
            )
        finally:
            db.close()

    asyncio.run(_async_task())


@router.post("/{memo_id}/comments", response_model=MemoCommentOut, status_code=201)
async def create_comment(
    memo_id: str,
    comment: MemoCommentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """댓글 작성"""
    logger.info(f"Creating comment for memo: {memo_id}")

    # 메모 존재 확인
    get_memo_or_404(memo_id, db)

    db_comment = MemoComment(
        memo_id=memo_id,
        content=comment.content,
        response_status="pending",  # AI 응답 대기 상태
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)

    logger.info(f"Created comment: id={db_comment.id}")

    # 백그라운드에서 AI 응답 생성 (user_id 전달)
    user_id = current_user.id if current_user else None
    background_tasks.add_task(_run_ai_response_task, db_comment.id, memo_id, user_id)

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

    # AI 댓글은 수정 불가
    if db_comment.is_ai_response:
        raise HTTPException(status_code=403, detail="AI 댓글은 수정할 수 없습니다.")

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

    # AI 댓글은 삭제 불가
    if db_comment.is_ai_response:
        raise HTTPException(status_code=403, detail="AI 댓글은 삭제할 수 없습니다.")

    db.delete(db_comment)
    db.commit()

    logger.info(f"Deleted comment: id={comment_id}")
    return None

"""
메모 댓글 (MemoComment) API 라우터
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
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
from app.services.memo_repository import comment_repository, memo_repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/temp-memos", tags=["memo-comments"])


def get_memo_or_404(memo_id: str, db: Session) -> TempMemo:
    """메모 조회, 없으면 404"""
    memo = memo_repository.get_by_id(db, memo_id)
    if not memo:
        logger.warning(f"Memo not found: id={memo_id}")
        raise HTTPException(status_code=404, detail="메모를 찾을 수 없습니다.")
    return memo


def _run_ai_response_task(
    comment_id: str, memo_id: str, user_id: Optional[str] = None
) -> None:
    """백그라운드에서 AI 응답 생성 실행"""
    from app.utils import run_async_in_thread

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

    run_async_in_thread(_async_task)


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

    # @태그 존재 여부 확인 (예: @전문가, @비판가)
    has_mention = bool(re.search(r"@\S+", comment.content))

    db_comment = MemoComment(
        memo_id=memo_id,
        content=comment.content,
        # @태그가 있을 때만 AI 응답 대기 상태로 설정
        response_status="pending" if has_mention else None,
    )
    db_comment = comment_repository.create(db, db_comment)

    logger.info(
        f"Created comment: id={db_comment.id}, has_mention={has_mention}"
    )

    # @태그가 있을 때만 백그라운드에서 AI 응답 생성
    if has_mention:
        user_id = current_user.id if current_user else None
        background_tasks.add_task(
            _run_ai_response_task, db_comment.id, memo_id, user_id
        )

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

    items, total = comment_repository.list_memo_comments(db, memo_id)

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

    db_comment = comment_repository.get_memo_comment(db, memo_id, comment_id)
    if not db_comment:
        logger.warning(f"Comment not found: id={comment_id}")
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")

    # AI 댓글은 수정 불가
    if db_comment.is_ai_response:
        raise HTTPException(status_code=403, detail="AI 댓글은 수정할 수 없습니다.")

    if comment.content is not None:
        db_comment.content = comment.content

    db_comment.updated_at = datetime.now(timezone.utc).isoformat()

    db_comment = comment_repository.update(db, db_comment)

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

    db_comment = comment_repository.get_memo_comment(db, memo_id, comment_id)
    if not db_comment:
        logger.warning(f"Comment not found: id={comment_id}")
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")

    # AI 댓글도 삭제 가능
    comment_repository.delete(db, db_comment)

    logger.info(f"Deleted comment: id={comment_id}")
    return None

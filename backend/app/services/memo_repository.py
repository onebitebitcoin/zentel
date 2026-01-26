"""
메모 및 댓글 데이터 접근 계층 (Repository Pattern)

라우터와 데이터베이스 쿼리 로직을 분리합니다.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.memo_comment import MemoComment
from app.models.temp_memo import TempMemo

logger = logging.getLogger(__name__)


class MemoRepository:
    """임시 메모 데이터 접근 클래스"""

    @staticmethod
    def get_by_id(db: Session, memo_id: str) -> Optional[TempMemo]:
        """메모 ID로 조회"""
        return db.query(TempMemo).filter(TempMemo.id == memo_id).first()

    @staticmethod
    def get_user_memo(db: Session, memo_id: str, user_id: str) -> Optional[TempMemo]:
        """사용자 소유 메모 조회"""
        return (
            db.query(TempMemo)
            .filter(TempMemo.id == memo_id, TempMemo.user_id == user_id)
            .first()
        )

    @staticmethod
    def list_user_memos(
        db: Session,
        user_id: str,
        memo_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[list[TempMemo], int]:
        """사용자 메모 목록 조회 (최신순)"""
        query = db.query(TempMemo).filter(TempMemo.user_id == user_id)

        if memo_type:
            query = query.filter(TempMemo.memo_type == memo_type)

        total = query.count()
        items = query.order_by(desc(TempMemo.created_at)).offset(offset).limit(limit).all()

        return items, total

    @staticmethod
    def create(db: Session, memo: TempMemo) -> TempMemo:
        """메모 생성"""
        db.add(memo)
        db.commit()
        db.refresh(memo)
        return memo

    @staticmethod
    def update(db: Session, memo: TempMemo) -> TempMemo:
        """메모 업데이트"""
        db.commit()
        db.refresh(memo)
        return memo

    @staticmethod
    def delete(db: Session, memo: TempMemo) -> None:
        """메모 삭제"""
        db.delete(memo)
        db.commit()


class CommentRepository:
    """메모 댓글 데이터 접근 클래스"""

    @staticmethod
    def get_by_id(db: Session, comment_id: str) -> Optional[MemoComment]:
        """댓글 ID로 조회"""
        return db.query(MemoComment).filter(MemoComment.id == comment_id).first()

    @staticmethod
    def get_memo_comment(
        db: Session, memo_id: str, comment_id: str
    ) -> Optional[MemoComment]:
        """메모의 특정 댓글 조회"""
        return (
            db.query(MemoComment)
            .filter(MemoComment.id == comment_id, MemoComment.memo_id == memo_id)
            .first()
        )

    @staticmethod
    def list_memo_comments(
        db: Session,
        memo_id: str,
    ) -> tuple[list[MemoComment], int]:
        """메모의 댓글 목록 조회 (최신순)"""
        query = db.query(MemoComment).filter(MemoComment.memo_id == memo_id)
        total = query.count()
        items = query.order_by(desc(MemoComment.created_at)).all()
        return items, total

    @staticmethod
    def get_comment_count_and_latest(
        db: Session, memo_id: str
    ) -> tuple[int, Optional[MemoComment]]:
        """메모의 댓글 개수와 최신 댓글 반환"""
        count = (
            db.query(func.count(MemoComment.id))
            .filter(MemoComment.memo_id == memo_id)
            .scalar()
        )
        latest = (
            db.query(MemoComment)
            .filter(MemoComment.memo_id == memo_id)
            .order_by(desc(MemoComment.created_at))
            .first()
        )
        return count, latest

    @staticmethod
    def create(db: Session, comment: MemoComment) -> MemoComment:
        """댓글 생성"""
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment

    @staticmethod
    def update(db: Session, comment: MemoComment) -> MemoComment:
        """댓글 업데이트"""
        db.commit()
        db.refresh(comment)
        return comment

    @staticmethod
    def delete(db: Session, comment: MemoComment) -> None:
        """댓글 삭제"""
        db.delete(comment)
        db.commit()


# 싱글톤 인스턴스
memo_repository = MemoRepository()
comment_repository = CommentRepository()

"""
메모 및 댓글 데이터 접근 계층 (Repository Pattern)

라우터와 데이터베이스 쿼리 로직을 분리합니다.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app.models.memo_comment import MemoComment
from app.models.permanent_note import PermanentNote
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
        search: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[list[TempMemo], int]:
        """사용자 메모 목록 조회 (최신순)"""
        query = db.query(TempMemo).filter(TempMemo.user_id == user_id)

        if memo_type:
            query = query.filter(TempMemo.memo_type == memo_type)

        # 검색 조건 추가 (context, summary만)
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    TempMemo.context.ilike(pattern),
                    TempMemo.summary.ilike(pattern),
                )
            )

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
    def get_comment_stats_bulk(
        db: Session, memo_ids: list[str]
    ) -> dict[str, tuple[int, Optional[MemoComment]]]:
        """
        여러 메모의 댓글 개수와 최신 댓글을 한 번에 조회 (N+1 쿼리 방지)

        Returns:
            {memo_id: (count, latest_comment)} 딕셔너리
        """
        if not memo_ids:
            return {}

        # 1. 각 메모의 댓글 개수 조회 (1쿼리)
        count_query = (
            db.query(MemoComment.memo_id, func.count(MemoComment.id))
            .filter(MemoComment.memo_id.in_(memo_ids))
            .group_by(MemoComment.memo_id)
        )
        counts = dict(count_query.all())

        # 2. 각 메모의 최신 댓글 조회 (1쿼리)
        # 서브쿼리로 각 메모별 최신 댓글 ID 찾기
        latest_subquery = (
            db.query(
                MemoComment.memo_id,
                func.max(MemoComment.created_at).label("max_created_at"),
            )
            .filter(MemoComment.memo_id.in_(memo_ids))
            .group_by(MemoComment.memo_id)
            .subquery()
        )

        # 최신 댓글 조회
        latest_comments = (
            db.query(MemoComment)
            .join(
                latest_subquery,
                (MemoComment.memo_id == latest_subquery.c.memo_id)
                & (MemoComment.created_at == latest_subquery.c.max_created_at),
            )
            .all()
        )

        latest_by_memo = {c.memo_id: c for c in latest_comments}

        # 결과 매핑
        result = {}
        for memo_id in memo_ids:
            count = counts.get(memo_id, 0)
            latest = latest_by_memo.get(memo_id)
            result[memo_id] = (count, latest)

        return result

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


class PermanentNoteRepository:
    """영구 메모 데이터 접근 클래스"""

    @staticmethod
    def get_by_id(db: Session, note_id: str) -> Optional[PermanentNote]:
        """영구 메모 ID로 조회"""
        return db.query(PermanentNote).filter(PermanentNote.id == note_id).first()

    @staticmethod
    def get_user_note(db: Session, note_id: str, user_id: str) -> Optional[PermanentNote]:
        """사용자 소유 영구 메모 조회"""
        return (
            db.query(PermanentNote)
            .filter(PermanentNote.id == note_id, PermanentNote.user_id == user_id)
            .first()
        )

    @staticmethod
    def list_user_notes(
        db: Session,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[PermanentNote], int]:
        """사용자 영구 메모 목록 조회 (최신순)"""
        query = db.query(PermanentNote).filter(PermanentNote.user_id == user_id)

        if status:
            query = query.filter(PermanentNote.status == status)

        total = query.count()
        items = query.order_by(desc(PermanentNote.created_at)).offset(offset).limit(limit).all()

        return items, total

    @staticmethod
    def create(db: Session, note: PermanentNote) -> PermanentNote:
        """영구 메모 생성"""
        db.add(note)
        db.commit()
        db.refresh(note)
        return note

    @staticmethod
    def update(db: Session, note: PermanentNote) -> PermanentNote:
        """영구 메모 업데이트"""
        db.commit()
        db.refresh(note)
        return note

    @staticmethod
    def delete(db: Session, note: PermanentNote) -> None:
        """영구 메모 삭제"""
        db.delete(note)
        db.commit()


# 싱글톤 인스턴스
memo_repository = MemoRepository()
comment_repository = CommentRepository()
permanent_note_repository = PermanentNoteRepository()

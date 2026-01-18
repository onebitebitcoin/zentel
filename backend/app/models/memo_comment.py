"""
메모 댓글 (MemoComment) SQLAlchemy 모델
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from ulid import ULID

from app.database import Base


def generate_comment_ulid() -> str:
    """Comment ULID 생성"""
    return f"mc_{ULID()}"


def now_iso() -> str:
    """현재 시간을 ISO8601 형식으로 반환 (UTC)"""
    return datetime.now(timezone.utc).isoformat()


class MemoComment(Base):
    """메모 댓글 테이블"""

    __tablename__ = "memo_comments"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_comment_ulid)
    memo_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("temp_memos.id", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False, default=now_iso)
    updated_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        Index("idx_memo_comments_memo_id", "memo_id"),
        Index("idx_memo_comments_created_at", "created_at"),
    )

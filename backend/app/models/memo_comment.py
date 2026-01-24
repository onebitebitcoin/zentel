"""
메모 댓글 (MemoComment) SQLAlchemy 모델
"""
from __future__ import annotations

from functools import partial
from typing import Optional

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils import generate_ulid, now_iso


class MemoComment(Base):
    """메모 댓글 테이블"""

    __tablename__ = "memo_comments"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=partial(generate_ulid, "mc")
    )
    memo_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("temp_memos.id", ondelete="CASCADE"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False, default=now_iso)
    updated_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # AI 댓글 관련 필드
    is_ai_response: Mapped[bool] = mapped_column(default=False)
    parent_comment_id: Mapped[Optional[str]] = mapped_column(
        String(32),
        ForeignKey("memo_comments.id", ondelete="CASCADE"),
        nullable=True,
    )
    response_status: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True
    )  # pending | generating | completed | failed
    response_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_memo_comments_memo_id", "memo_id"),
        Index("idx_memo_comments_created_at", "created_at"),
        Index("idx_memo_comments_parent_id", "parent_comment_id"),
    )

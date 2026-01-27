"""
영구 메모 (Permanent Note) SQLAlchemy 모델
"""
from __future__ import annotations

from functools import partial
from typing import Optional

from sqlalchemy import JSON, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils import generate_ulid, now_iso


class PermanentNote(Base):
    """영구 메모 테이블"""

    __tablename__ = "permanent_notes"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=partial(generate_ulid, "pn")
    )
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="editing"
    )  # "editing" | "published"
    source_memo_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    interests: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False, default=now_iso)
    updated_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    published_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        Index("idx_permanent_notes_user_created", "user_id", "created_at"),
        Index("idx_permanent_notes_status", "status"),
    )

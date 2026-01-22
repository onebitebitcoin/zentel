"""
임시 메모 (Temporary Memo) SQLAlchemy 모델
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import JSON, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from ulid import ULID

from app.database import Base


def generate_ulid() -> str:
    """ULID 생성"""
    return f"tm_{ULID()}"


def now_iso() -> str:
    """현재 시간을 ISO8601 형식으로 반환 (UTC)"""
    return datetime.now(timezone.utc).isoformat()


class TempMemo(Base):
    """임시 메모 테이블"""

    __tablename__ = "temp_memos"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_ulid)
    memo_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    facts: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    interests: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    og_title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    og_image: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    # AI 분석 상태
    analysis_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending"
    )  # pending | analyzing | completed | failed
    analysis_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False, default=now_iso)
    updated_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        Index("idx_temp_memos_created_at", "created_at"),
        Index("idx_temp_memos_type_created", "memo_type", "created_at"),
    )

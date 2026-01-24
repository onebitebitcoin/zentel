"""
임시 메모 (Temporary Memo) SQLAlchemy 모델
"""
from __future__ import annotations

from functools import partial
from typing import Optional

from sqlalchemy import JSON, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils import generate_ulid, now_iso


class TempMemo(Base):
    """임시 메모 테이블"""

    __tablename__ = "temp_memos"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=partial(generate_ulid, "tm")
    )
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
    # 번역 및 하이라이트
    original_language: Mapped[Optional[str]] = mapped_column(
        String(16), nullable=True
    )  # "ko", "en", "ja" 등
    translated_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_summary: Mapped[bool] = mapped_column(
        default=False
    )  # True면 요약 번역 (긴 글)
    highlights: Mapped[Optional[list[dict]]] = mapped_column(
        JSON, nullable=True
    )  # 하이라이트 위치 정보
    created_at: Mapped[str] = mapped_column(String(64), nullable=False, default=now_iso)
    updated_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        Index("idx_temp_memos_created_at", "created_at"),
        Index("idx_temp_memos_type_created", "memo_type", "created_at"),
    )

"""
사용자 (User) SQLAlchemy 모델
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from ulid import ULID

from app.database import Base


def generate_user_ulid() -> str:
    """User ULID 생성"""
    return f"user_{ULID()}"


def now_iso() -> str:
    """현재 시간을 ISO8601 형식으로 반환 (UTC)"""
    return datetime.now(timezone.utc).isoformat()


class User(Base):
    """사용자 테이블"""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=generate_user_ulid)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False, default=now_iso)
    updated_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        Index("idx_users_username", "username"),
        Index("idx_users_created_at", "created_at"),
    )

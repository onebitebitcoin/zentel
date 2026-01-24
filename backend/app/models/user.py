"""
사용자 (User) SQLAlchemy 모델
"""
from __future__ import annotations

from functools import partial
from typing import Optional

from sqlalchemy import JSON, Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils import generate_ulid, now_iso


class User(Base):
    """사용자 테이블"""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(32), primary_key=True, default=partial(generate_ulid, "user")
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    interests: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    ai_personas: Mapped[Optional[list[dict]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False, default=now_iso)
    updated_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    __table_args__ = (
        Index("idx_users_username", "username"),
        Index("idx_users_created_at", "created_at"),
    )

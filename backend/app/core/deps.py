"""
인증 의존성 모듈
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.jwt import decode_token
from app.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

# Bearer 토큰 스킴
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """현재 인증된 사용자 반환"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증이 필요합니다",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        logger.warning("No credentials provided")
        raise credentials_exception

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        logger.warning("Invalid token")
        raise credentials_exception

    # 토큰 타입 확인 (access token만 허용)
    if payload.get("type") != "access":
        logger.warning(f"Invalid token type: {payload.get('type')}")
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        logger.warning("No user_id in token payload")
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        logger.warning(f"User not found: {user_id}")
        raise credentials_exception

    if not user.is_active:
        logger.warning(f"Inactive user: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자입니다",
        )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """현재 인증된 사용자 반환 (선택적 - 인증 없어도 None 반환)"""
    if credentials is None:
        return None

    token = credentials.credentials
    payload = decode_token(token)

    if payload is None or payload.get("type") != "access":
        return None

    user_id: str = payload.get("sub")
    if user_id is None:
        return None

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        return None

    return user

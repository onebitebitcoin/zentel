"""
인증 API 라우터
"""

import logging
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.cookies import delete_refresh_token_cookie, set_refresh_token_cookie
from app.core.deps import get_current_user
from app.core.jwt import create_access_token, create_refresh_token, decode_token
from app.core.security import get_password_hash, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    MessageResponse,
    PasswordChange,
    TokenResponse,
    UserLogin,
    UsernameCheckResponse,
    UserOut,
    UserRegister,
    UserUpdate,
)
from app.utils import now_iso

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """회원가입"""
    logger.info(f"Register attempt: {data.username}")

    # 사용자 이름 중복 체크
    existing_user = db.query(User).filter(User.username == data.username).first()
    if existing_user:
        logger.warning(f"Username already exists: {data.username}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 사용자 이름입니다",
        )

    # 사용자 생성
    hashed_password = get_password_hash(data.password)
    user = User(
        username=data.username,
        hashed_password=hashed_password,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"User registered successfully: {user.id}")
    return user


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, response: Response, db: Session = Depends(get_db)):
    """로그인 - 토큰 발급"""
    logger.info(f"Login attempt: {data.username}")

    # 사용자 조회
    user = db.query(User).filter(User.username == data.username.lower()).first()
    if not user:
        logger.warning(f"User not found: {data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="존재하지 않는 사용자입니다",
        )

    # 비밀번호 검증
    if not verify_password(data.password, user.hashed_password):
        logger.warning(f"Invalid password for user: {data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="비밀번호가 올바르지 않습니다",
        )

    # 비활성 사용자 체크
    if not user.is_active:
        logger.warning(f"Inactive user login attempt: {data.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자입니다",
        )

    # 토큰 생성
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})

    # Refresh Token을 httpOnly 쿠키로 설정
    set_refresh_token_cookie(response, refresh_token)

    logger.info(f"User logged in successfully: {user.id}")
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: Optional[str] = Cookie(default=None),
):
    """토큰 갱신 - httpOnly 쿠키에서 refresh_token을 읽음"""
    logger.info("Token refresh attempt")

    # 쿠키에서 Refresh Token 확인
    if not refresh_token:
        logger.warning("No refresh token in cookie")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token이 없습니다. 다시 로그인해주세요.",
        )

    # Refresh Token 검증
    payload = decode_token(refresh_token)
    if payload is None:
        logger.warning("Invalid refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다",
        )

    # 토큰 타입 확인
    if payload.get("type") != "refresh":
        logger.warning(f"Invalid token type: {payload.get('type')}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다",
        )

    # 사용자 조회
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다",
        )

    # 새 토큰 생성
    access_token = create_access_token(data={"sub": user.id})
    new_refresh_token = create_refresh_token(data={"sub": user.id})

    # 새 Refresh Token 쿠키 설정
    set_refresh_token_cookie(response, new_refresh_token)

    logger.info(f"Token refreshed for user: {user.id}")
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", response_model=MessageResponse)
def logout(response: Response, current_user: User = Depends(get_current_user)):
    """로그아웃"""
    logger.info(f"User logout: {current_user.id}")

    # Refresh Token 쿠키 삭제
    delete_refresh_token_cookie(response)

    return MessageResponse(message="로그아웃되었습니다")


@router.get("/me", response_model=UserOut)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """현재 로그인한 사용자 정보 조회"""
    logger.info(f"Get current user: {current_user.id}")
    return current_user


@router.get("/check-username", response_model=UsernameCheckResponse)
def check_username(username: str, db: Session = Depends(get_db)):
    """사용자 이름 중복 체크"""
    logger.info(f"Check username: {username}")

    # 사용자 이름 정규화
    normalized_username = username.lower()

    # 길이 체크
    if len(normalized_username) < 3:
        return UsernameCheckResponse(
            available=False,
            message="사용자 이름은 3자 이상이어야 합니다",
        )

    if len(normalized_username) > 50:
        return UsernameCheckResponse(
            available=False,
            message="사용자 이름은 50자 이하여야 합니다",
        )

    # 허용 문자 체크
    if not normalized_username.replace("_", "").isalnum():
        return UsernameCheckResponse(
            available=False,
            message="사용자 이름은 영문자, 숫자, 언더스코어만 사용 가능합니다",
        )

    # 중복 체크
    existing_user = db.query(User).filter(User.username == normalized_username).first()
    if existing_user:
        return UsernameCheckResponse(
            available=False,
            message="이미 사용 중인 사용자 이름입니다",
        )

    return UsernameCheckResponse(
        available=True,
        message="사용 가능한 사용자 이름입니다",
    )


@router.put("/password", response_model=MessageResponse)
def change_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """비밀번호 변경"""
    logger.info(f"Password change attempt: {current_user.id}")

    # 현재 비밀번호 검증
    if not verify_password(data.current_password, current_user.hashed_password):
        logger.warning(f"Invalid current password for user: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 비밀번호가 올바르지 않습니다",
        )

    # 새 비밀번호 해시
    current_user.hashed_password = get_password_hash(data.new_password)
    current_user.updated_at = now_iso()

    db.commit()

    logger.info(f"Password changed successfully: {current_user.id}")
    return MessageResponse(message="비밀번호가 변경되었습니다")


@router.put("/profile", response_model=UserOut)
def update_profile(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """프로필(관심사, AI 페르소나) 업데이트"""
    logger.info(f"Profile update: {current_user.id}")

    if data.interests is not None:
        current_user.interests = data.interests

    if data.ai_personas is not None:
        current_user.ai_personas = data.ai_personas

    current_user.updated_at = now_iso()

    db.commit()
    db.refresh(current_user)

    logger.info(f"Profile updated: {current_user.id}")
    return current_user

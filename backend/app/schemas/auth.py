"""
인증 (Auth) Pydantic 스키마
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class AIPersona(BaseModel):
    """AI 페르소나 스키마"""

    name: str = Field(min_length=1, max_length=50)
    description: Optional[str] = None


class UserRegister(BaseModel):
    """회원가입 요청 스키마"""

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=100)

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """사용자 이름은 영문자, 숫자, 언더스코어만 허용"""
        if not v.replace("_", "").isalnum():
            raise ValueError("사용자 이름은 영문자, 숫자, 언더스코어만 사용 가능합니다")
        return v.lower()


class UserLogin(BaseModel):
    """로그인 요청 스키마"""

    username: str
    password: str


class UserOut(BaseModel):
    """사용자 응답 스키마"""

    id: str
    username: str
    is_active: bool
    interests: Optional[List[str]] = None
    ai_personas: Optional[List[dict]] = None
    created_at: str
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """토큰 응답 스키마"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 초 단위


class RefreshTokenRequest(BaseModel):
    """토큰 갱신 요청 스키마"""

    refresh_token: str


class UsernameCheckResponse(BaseModel):
    """사용자 이름 중복 체크 응답"""

    available: bool
    message: str


class MessageResponse(BaseModel):
    """일반 메시지 응답"""

    message: str


class PasswordChange(BaseModel):
    """비밀번호 변경 요청 스키마"""

    current_password: str
    new_password: str = Field(min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """사용자 프로필 업데이트 스키마"""

    interests: Optional[List[str]] = None
    ai_personas: Optional[List[dict]] = None

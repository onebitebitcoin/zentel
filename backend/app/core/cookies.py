"""
쿠키 관리 헬퍼 모듈

Refresh Token 쿠키 설정/삭제 공통 로직
"""

from fastapi import Response

from app.config import settings


def set_refresh_token_cookie(response: Response, token: str) -> None:
    """
    Refresh Token을 httpOnly 쿠키로 설정

    삼성 브라우저 등 호환성을 위해 production에서는
    samesite="none" + secure=True 사용

    Args:
        response: FastAPI Response 객체
        token: Refresh Token 값
    """
    is_production = settings.ENVIRONMENT == "production"
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=is_production,
        samesite="none" if is_production else "lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )


def delete_refresh_token_cookie(response: Response) -> None:
    """
    Refresh Token 쿠키 삭제

    Args:
        response: FastAPI Response 객체
    """
    is_production = settings.ENVIRONMENT == "production"
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=is_production,
        samesite="none" if is_production else "lax",
        path="/",
    )

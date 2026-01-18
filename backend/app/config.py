"""
설정 모듈 - 12-Factor App 원칙에 따라 환경 변수로 설정 관리
"""

import os
from functools import lru_cache


class Settings:
    """애플리케이션 설정"""

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./zentel.db")

    # Application
    SECRET_KEY: str = os.getenv("SECRET_KEY", "zentel-dev-secret-key")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "DEBUG")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Server
    PORT: int = int(os.getenv("PORT", "6000"))

    # API
    API_V1_PREFIX: str = "/api/v1"

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "zentel-jwt-secret-key-dev")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


@lru_cache
def get_settings() -> Settings:
    """설정 인스턴스 반환 (캐싱)"""
    return Settings()


settings = get_settings()

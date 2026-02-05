"""
테스트 설정 및 Fixtures
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# 테스트용 인메모리 SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """테스트용 DB 세션"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """테스트 클라이언트"""
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    """테스트용 DB 세션 (직접 DB 조작 필요 시 사용)"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def authenticated_client(client):
    """인증된 테스트 클라이언트 (테스트 사용자 생성 및 로그인 포함)"""
    # 테스트 사용자 생성
    client.post(
        "/api/v1/auth/register",
        json={"username": "testmemouser", "password": "testpass123"},
    )

    # 로그인하여 토큰 획득
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "testmemouser", "password": "testpass123"},
    )
    access_token = login_response.json()["access_token"]

    # 모든 요청에 인증 헤더 추가
    client.headers["Authorization"] = f"Bearer {access_token}"

    return client

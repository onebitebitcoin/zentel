"""
Zentel - FastAPI 메인 애플리케이션
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import temp_memos_router
from app.config import settings
from app.database import init_db

# 로그 파일 초기화 (핫리로드 시)
LOG_FILE = "debug.log"
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 시 실행"""
    logger.info("Zentel 서버 시작")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database: {settings.DATABASE_URL}")

    # 데이터베이스 초기화
    init_db()
    logger.info("Database initialized")

    yield

    logger.info("Zentel 서버 종료")


app = FastAPI(
    title="Zentel API",
    description="젠텔카스텐 모바일 메모 캡처 API",
    version="0.1.0",
    lifespan=lifespan,
)

# Trailing slash redirect 비활성화
app.router.redirect_slashes = False

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(temp_memos_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


@app.get("/")
def root():
    """루트 엔드포인트"""
    return {
        "message": "Zentel API",
        "version": "0.1.0",
        "docs": "/docs",
    }

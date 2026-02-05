"""
MyRottenApple - FastAPI 메인 애플리케이션
"""

import logging
import sys
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import auth_router, memo_comments_router, permanent_notes_router, temp_memos_router
from app.config import settings
from app.database import init_db

# 프론트엔드 정적 파일 경로 (프로덕션)
STATIC_DIR = Path(__file__).parent.parent.parent / "static"

# 로그 파일 경로 (backend/debug.log)
BACKEND_DIR = Path(__file__).parent.parent
LOG_FILE = BACKEND_DIR / "debug.log"


def setup_logging():
    """환경에 따른 로깅 설정 - 모든 로그를 debug.log에 기록"""
    log_level = getattr(logging, settings.LOG_LEVEL)

    # 기존 핸들러 모두 제거
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    if settings.ENVIRONMENT == "production":
        # 운영환경: stdout만 (Railway/Docker가 수집)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                '{"time":"%(asctime)s","level":"%(levelname)s","file":"%(filename)s:%(lineno)d","message":"%(message)s"}'
            )
        )
        root_logger.addHandler(handler)
    else:
        # 개발환경: 파일 + stdout
        # 기존 로그 파일 초기화 (핫리로드 시)
        with suppress(PermissionError):
            if LOG_FILE.exists():
                LOG_FILE.unlink()

        log_format = "[%(asctime)s] [%(levelname)s] [%(name)s:%(filename)s:%(lineno)d] %(message)s"

        # 파일 핸들러
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)

        # 콘솔 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(console_handler)

    root_logger.setLevel(log_level)

    # uvicorn 로거도 같은 핸들러 사용하도록 설정
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "sqlalchemy.engine"]:
        lib_logger = logging.getLogger(logger_name)
        lib_logger.handlers.clear()
        lib_logger.propagate = True  # 루트 로거로 전파


# 로깅 설정 적용
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 시 실행"""
    logger.info("MyRottenApple 서버 시작")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database: {settings.DATABASE_URL}")

    # 데이터베이스 초기화
    init_db()
    logger.info("Database initialized")

    yield

    logger.info("MyRottenApple 서버 종료")


app = FastAPI(
    title="MyRottenApple API",
    description="MyRottenApple 모바일 메모 캡처 API",
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
app.include_router(memo_comments_router, prefix=settings.API_V1_PREFIX)
app.include_router(permanent_notes_router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


@app.get("/")
def root():
    """루트 엔드포인트 - 프로덕션에서는 SPA 서빙"""
    if settings.ENVIRONMENT == "production" and STATIC_DIR.exists():
        return FileResponse(STATIC_DIR / "index.html")
    return {
        "message": "MyRottenApple API",
        "version": "0.1.0",
        "docs": "/docs",
    }


# 프로덕션: 정적 파일 서빙 및 SPA 폴백
if STATIC_DIR.exists():
    # 정적 파일 (JS, CSS, 이미지 등)
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    # SPA 폴백: 모든 경로에서 index.html 반환
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """SPA 라우팅을 위한 폴백"""
        # API 경로는 제외
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi"):
            return {"detail": "Not Found"}

        # 정적 파일이 존재하면 반환
        file_path = STATIC_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)

        # 그 외에는 index.html 반환 (SPA 라우팅)
        return FileResponse(STATIC_DIR / "index.html")

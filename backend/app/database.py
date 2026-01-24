"""
데이터베이스 설정 모듈
"""

import logging

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

# SQLite 연결 설정
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.LOG_LEVEL == "DEBUG",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """SQLAlchemy Base 클래스"""

    pass


def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """데이터베이스 테이블 초기화 및 마이그레이션"""
    # 테이블 생성
    Base.metadata.create_all(bind=engine)

    # 마이그레이션: 기존 테이블에 새 컬럼 추가
    _run_migrations()


def _run_migrations():
    """수동 마이그레이션 실행"""
    inspector = inspect(engine)

    # temp_memos 테이블에 interests 컬럼 추가
    if "temp_memos" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("temp_memos")]
        if "interests" not in columns:
            logger.info("Migration: Adding 'interests' column to temp_memos table")
            with engine.connect() as conn:
                if settings.DATABASE_URL.startswith("sqlite"):
                    conn.execute(text("ALTER TABLE temp_memos ADD COLUMN interests TEXT"))
                else:
                    # PostgreSQL
                    conn.execute(text("ALTER TABLE temp_memos ADD COLUMN interests JSONB"))
                conn.commit()
            logger.info("Migration: 'interests' column added successfully")

        # analysis_status 컬럼 추가
        if "analysis_status" not in columns:
            logger.info("Migration: Adding 'analysis_status' column to temp_memos table")
            with engine.connect() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE temp_memos ADD COLUMN analysis_status "
                        "VARCHAR(32) NOT NULL DEFAULT 'completed'"
                    )
                )
                conn.commit()
            logger.info("Migration: 'analysis_status' column added successfully")

        # analysis_error 컬럼 추가
        if "analysis_error" not in columns:
            logger.info("Migration: Adding 'analysis_error' column to temp_memos table")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE temp_memos ADD COLUMN analysis_error TEXT"))
                conn.commit()
            logger.info("Migration: 'analysis_error' column added successfully")

        # original_language 컬럼 추가
        if "original_language" not in columns:
            logger.info(
                "Migration: Adding 'original_language' column to temp_memos table"
            )
            with engine.connect() as conn:
                conn.execute(
                    text("ALTER TABLE temp_memos ADD COLUMN original_language VARCHAR(16)")
                )
                conn.commit()
            logger.info("Migration: 'original_language' column added successfully")

        # translated_content 컬럼 추가
        if "translated_content" not in columns:
            logger.info(
                "Migration: Adding 'translated_content' column to temp_memos table"
            )
            with engine.connect() as conn:
                conn.execute(
                    text("ALTER TABLE temp_memos ADD COLUMN translated_content TEXT")
                )
                conn.commit()
            logger.info("Migration: 'translated_content' column added successfully")

        # highlights 컬럼 추가
        if "highlights" not in columns:
            logger.info("Migration: Adding 'highlights' column to temp_memos table")
            with engine.connect() as conn:
                if settings.DATABASE_URL.startswith("sqlite"):
                    conn.execute(text("ALTER TABLE temp_memos ADD COLUMN highlights TEXT"))
                else:
                    # PostgreSQL
                    conn.execute(
                        text("ALTER TABLE temp_memos ADD COLUMN highlights JSONB")
                    )
                conn.commit()
            logger.info("Migration: 'highlights' column added successfully")

        # is_summary 컬럼 추가
        if "is_summary" not in columns:
            logger.info("Migration: Adding 'is_summary' column to temp_memos table")
            with engine.connect() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE temp_memos ADD COLUMN is_summary BOOLEAN DEFAULT FALSE"
                    )
                )
                conn.commit()
            logger.info("Migration: 'is_summary' column added successfully")

        # fetched_content 컬럼 추가 (스크래핑된 원본 컨텐츠)
        if "fetched_content" not in columns:
            logger.info(
                "Migration: Adding 'fetched_content' column to temp_memos table"
            )
            with engine.connect() as conn:
                conn.execute(
                    text("ALTER TABLE temp_memos ADD COLUMN fetched_content TEXT")
                )
                conn.commit()
            logger.info("Migration: 'fetched_content' column added successfully")

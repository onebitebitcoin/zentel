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

        # display_content 컬럼 추가 (최종 표시용 콘텐츠)
        if "display_content" not in columns:
            logger.info(
                "Migration: Adding 'display_content' column to temp_memos table"
            )
            with engine.connect() as conn:
                conn.execute(
                    text("ALTER TABLE temp_memos ADD COLUMN display_content TEXT")
                )
                conn.commit()
            logger.info("Migration: 'display_content' column added successfully")

        # summary 컬럼 추가 (핵심 요약 - 최대 3문단)
        if "summary" not in columns:
            logger.info("Migration: Adding 'summary' column to temp_memos table")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE temp_memos ADD COLUMN summary TEXT"))
                conn.commit()
            logger.info("Migration: 'summary' column added successfully")

        # user_id 컬럼 추가 (사용자별 메모 분리)
        if "user_id" not in columns:
            logger.info("Migration: Adding 'user_id' column to temp_memos table")
            # 첫 번째 사용자 ID 조회 (기존 메모 할당용)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT id FROM users LIMIT 1"))
                first_user = result.fetchone()
                default_user_id = first_user[0] if first_user else None

            if default_user_id:
                with engine.connect() as conn:
                    if settings.DATABASE_URL.startswith("sqlite"):
                        # SQLite: 기본값으로 첫 번째 사용자 ID 사용
                        conn.execute(
                            text(
                                f"ALTER TABLE temp_memos ADD COLUMN user_id "
                                f"VARCHAR(32) REFERENCES users(id) ON DELETE CASCADE "
                                f"DEFAULT '{default_user_id}'"
                            )
                        )
                    else:
                        # PostgreSQL
                        conn.execute(
                            text(
                                f"ALTER TABLE temp_memos ADD COLUMN user_id "
                                f"VARCHAR(32) REFERENCES users(id) ON DELETE CASCADE "
                                f"DEFAULT '{default_user_id}'"
                            )
                        )
                    conn.commit()
                logger.info(
                    f"Migration: 'user_id' column added with default '{default_user_id}'"
                )
            else:
                logger.warning(
                    "Migration: No users found, cannot add user_id column. "
                    "Create a user first."
                )

    # memo_comments 테이블에 AI 댓글 관련 컬럼 추가
    if "memo_comments" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("memo_comments")]

        # is_ai_response 컬럼 추가
        if "is_ai_response" not in columns:
            logger.info("Migration: Adding 'is_ai_response' column to memo_comments")
            with engine.connect() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE memo_comments ADD COLUMN is_ai_response "
                        "BOOLEAN DEFAULT FALSE"
                    )
                )
                conn.commit()
            logger.info("Migration: 'is_ai_response' column added successfully")

        # parent_comment_id 컬럼 추가
        if "parent_comment_id" not in columns:
            logger.info("Migration: Adding 'parent_comment_id' column to memo_comments")
            with engine.connect() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE memo_comments ADD COLUMN parent_comment_id "
                        "VARCHAR(32) REFERENCES memo_comments(id) ON DELETE CASCADE"
                    )
                )
                conn.commit()
            logger.info("Migration: 'parent_comment_id' column added successfully")

        # response_status 컬럼 추가
        if "response_status" not in columns:
            logger.info("Migration: Adding 'response_status' column to memo_comments")
            with engine.connect() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE memo_comments ADD COLUMN response_status VARCHAR(32)"
                    )
                )
                conn.commit()
            logger.info("Migration: 'response_status' column added successfully")

        # response_error 컬럼 추가
        if "response_error" not in columns:
            logger.info("Migration: Adding 'response_error' column to memo_comments")
            with engine.connect() as conn:
                conn.execute(
                    text("ALTER TABLE memo_comments ADD COLUMN response_error TEXT")
                )
                conn.commit()
            logger.info("Migration: 'response_error' column added successfully")

        # ai_persona_name 컬럼 추가
        if "ai_persona_name" not in columns:
            logger.info("Migration: Adding 'ai_persona_name' column to memo_comments")
            with engine.connect() as conn:
                conn.execute(
                    text("ALTER TABLE memo_comments ADD COLUMN ai_persona_name VARCHAR(50)")
                )
                conn.commit()
            logger.info("Migration: 'ai_persona_name' column added successfully")

        # ai_persona_color 컬럼 추가
        if "ai_persona_color" not in columns:
            logger.info("Migration: Adding 'ai_persona_color' column to memo_comments")
            with engine.connect() as conn:
                conn.execute(
                    text("ALTER TABLE memo_comments ADD COLUMN ai_persona_color VARCHAR(16)")
                )
                conn.commit()
            logger.info("Migration: 'ai_persona_color' column added successfully")

    # users 테이블에 ai_personas 컬럼 추가
    if "users" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("users")]
        if "ai_personas" not in columns:
            logger.info("Migration: Adding 'ai_personas' column to users table")
            with engine.connect() as conn:
                if settings.DATABASE_URL.startswith("sqlite"):
                    conn.execute(text("ALTER TABLE users ADD COLUMN ai_personas TEXT"))
                else:
                    # PostgreSQL
                    conn.execute(text("ALTER TABLE users ADD COLUMN ai_personas JSONB"))
                conn.commit()
            logger.info("Migration: 'ai_personas' column added successfully")

    # permanent_notes 테이블에 analysis_result 컬럼 추가
    if "permanent_notes" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("permanent_notes")]
        if "analysis_result" not in columns:
            logger.info("Migration: Adding 'analysis_result' column to permanent_notes table")
            with engine.connect() as conn:
                if settings.DATABASE_URL.startswith("sqlite"):
                    conn.execute(text("ALTER TABLE permanent_notes ADD COLUMN analysis_result TEXT"))
                else:
                    # PostgreSQL
                    conn.execute(text("ALTER TABLE permanent_notes ADD COLUMN analysis_result JSONB"))
                conn.commit()
            logger.info("Migration: 'analysis_result' column added successfully")

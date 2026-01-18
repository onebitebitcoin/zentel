"""
temp_memos 테이블에 facts 컬럼 추가 마이그레이션
"""
from __future__ import annotations

import sys

from sqlalchemy import create_engine, inspect, text

from app.config import settings


def main() -> int:
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)

    if "temp_memos" not in inspector.get_table_names():
        print("temp_memos 테이블이 없습니다. 마이그레이션을 건너뜁니다.")
        return 0

    columns = {column["name"] for column in inspector.get_columns("temp_memos")}
    if "facts" in columns:
        print("facts 컬럼이 이미 존재합니다. 마이그레이션을 건너뜁니다.")
        return 0

    dialect = engine.dialect.name
    column_type = "JSON"
    if dialect == "sqlite":
        column_type = "JSON"

    alter_sql = f"ALTER TABLE temp_memos ADD COLUMN facts {column_type}"
    with engine.begin() as connection:
        connection.execute(text(alter_sql))

    print("facts 컬럼 추가 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())

import asyncio
import os
import re
from sqlalchemy import text
from app.database import engine, Base
# Import models for metadata registration used by Base.metadata.create_all.
from app.models.dish import Dish  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.history import MenuHistory  # noqa: F401
from app.models.chat_session import ChatSession  # noqa: F401
from app.models.standard_quota import StandardQuota  # noqa: F401


def _load_seed_sql(sql_path: str) -> list[str]:
    with open(sql_path, 'r', encoding='utf-8') as f:
        raw = f.read()

    # Remove SQLite-only statements before executing against PostgreSQL.
    cleaned = re.sub(
        r'^\s*(PRAGMA\s+foreign_keys\s*=\s*OFF;|BEGIN\s+TRANSACTION;|COMMIT;)\s*$\n?',
        '',
        raw,
        flags=re.IGNORECASE | re.MULTILINE,
    )

    statements = [s.strip() for s in cleaned.split(';') if s.strip()]
    return statements


def _extract_inserts(statements: list[str], table_name: str) -> list[str]:
    prefix = f"INSERT INTO {table_name}"
    return [f"{stmt};" for stmt in statements if stmt.startswith(prefix)]


async def _seed_table_if_empty(conn, table_name: str, statements: list[str]) -> bool:
    if not statements:
        return False

    row_count = await conn.scalar(text(f"SELECT COUNT(*) FROM {table_name}"))
    if row_count:
        return False

    for stmt in statements:
        await conn.exec_driver_sql(stmt)
    return True

async def init():
    async with engine.begin() as conn:
        # ORM owns schema creation for all application tables.
        await conn.run_sync(Base.metadata.create_all)

        sql_path = os.path.join(os.path.dirname(__file__), 'app', 'data', 'init_data.sql')
        statements = _load_seed_sql(sql_path)

        seeded_tables: list[str] = []
        if await _seed_table_if_empty(conn, 'dishes', _extract_inserts(statements, 'dishes')):
            seeded_tables.append('dishes')
        if await _seed_table_if_empty(conn, 'standard_quotas', _extract_inserts(statements, 'standard_quotas')):
            seeded_tables.append('standard_quotas')

        if seeded_tables:
            print(f"Database tables initialized. Seed data imported for: {', '.join(seeded_tables)}.")
        else:
            print("Database tables initialized. Seed data already exists, skipped.")

if __name__ == "__main__":
    asyncio.run(init())

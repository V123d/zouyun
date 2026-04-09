"""
数据库连接与会话管理
"""
import os
import sqlite3
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# 获取 data 目录的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# SQLite URL
DB_URL = os.environ.get("DATABASE_URL", f"sqlite+aiosqlite:///{os.path.join(DATA_DIR, 'app.db')}")


def _sqlite_file_path() -> Optional[str]:
    if not DB_URL.startswith("sqlite+aiosqlite:///"):
        return None
    return os.path.normpath(DB_URL.replace("sqlite+aiosqlite:///", "", 1))


def ensure_standard_quotas_meta_columns() -> None:
    """同步迁移：为 standard_quotas 增加 name/description/quota_type（在异步引擎使用前执行）"""
    path = _sqlite_file_path()
    if not path or not os.path.isfile(path):
        return
    conn = sqlite3.connect(path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='standard_quotas'")
        if not cur.fetchone():
            return
        cur.execute("PRAGMA table_info(standard_quotas)")
        cols = {row[1] for row in cur.fetchall()}
        for col, sql in [
            ("name", "ALTER TABLE standard_quotas ADD COLUMN name VARCHAR(100) DEFAULT ''"),
            ("description", "ALTER TABLE standard_quotas ADD COLUMN description VARCHAR(500) DEFAULT ''"),
            ("quota_type", "ALTER TABLE standard_quotas ADD COLUMN quota_type VARCHAR(20) DEFAULT 'ingredient'"),
        ]:
            if col not in cols:
                try:
                    cur.execute(sql)
                except sqlite3.OperationalError:
                    pass
        conn.commit()
    finally:
        conn.close()

ensure_standard_quotas_meta_columns()

engine = create_async_engine(
    DB_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in DB_URL else {}
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_db():
    """FastAPI 依赖，提供异步数据库会话"""
    async with AsyncSessionLocal() as session:
        yield session

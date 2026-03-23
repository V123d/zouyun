"""
数据库连接与会话管理
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# 获取 data 目录的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

# SQLite URL
DB_URL = os.environ.get("DATABASE_URL", f"sqlite+aiosqlite:///{os.path.join(DATA_DIR, 'app.db')}")

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

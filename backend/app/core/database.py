from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

import os
from sqlalchemy.pool import NullPool

# Base class for SQLAlchemy declarative models
class Base(DeclarativeBase):
    pass


is_test = os.environ.get("TESTING") == "1" or settings.ENVIRONMENT == "test"

connect_args = {}
if "ssl=require" in settings.DATABASE_URL or "neon.tech" in settings.DATABASE_URL:
    connect_args["ssl"] = "require"

# Engine and sessionmaker
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    future=True,
    connect_args=connect_args,
    poolclass=NullPool if is_test else None,
    pool_pre_ping=False if is_test else True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully.")

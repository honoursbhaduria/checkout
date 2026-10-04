import logging
from typing import Optional, AsyncGenerator
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)

redis_pool: Optional[aioredis.Redis] = None


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    global redis_pool
    if redis_pool is None:
        try:
            redis_pool = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                max_connections=20
            )
            # Test connection
            await redis_pool.ping()
        except Exception as e:
            logger.warning(f"Failed to connect to Redis at {settings.REDIS_URL}: {e}")
            raise
    try:
        yield redis_pool
    finally:
        pass


async def get_redis_client() -> aioredis.Redis:
    global redis_pool
    if redis_pool is None:
        redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20
        )
    return redis_pool


async def close_redis():
    global redis_pool
    if redis_pool:
        await redis_pool.aclose()
        redis_pool = None

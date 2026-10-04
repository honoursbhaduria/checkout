import logging
from typing import Optional, AsyncGenerator
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)

redis_pool: Optional[aioredis.Redis] = None


import os

def _get_redis_kwargs(max_connections: Optional[int] = None):
    kwargs = {"decode_responses": True}
    if max_connections:
        kwargs["max_connections"] = max_connections
    if settings.REDIS_URL.startswith("rediss://") or "upstash.io" in settings.REDIS_URL:
        kwargs["ssl_cert_reqs"] = None
    return kwargs

async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    if os.environ.get("TESTING") == "1" or settings.ENVIRONMENT == "test":
        client = aioredis.from_url(settings.REDIS_URL, **_get_redis_kwargs())
        try:
            yield client
        finally:
            await client.aclose()
        return

    global redis_pool
    if redis_pool is None:
        try:
            redis_pool = aioredis.from_url(
                settings.REDIS_URL,
                **_get_redis_kwargs(max_connections=20)
            )
            # Test connection
            await redis_pool.ping()
        except Exception as e:
            logger.warning(f"Failed to connect to Redis at {settings.REDIS_URL}: {e}")
            raise
    yield redis_pool


async def get_redis_client() -> aioredis.Redis:
    if os.environ.get("TESTING") == "1" or settings.ENVIRONMENT == "test":
        return aioredis.from_url(settings.REDIS_URL, **_get_redis_kwargs())
    global redis_pool
    if redis_pool is None:
        redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            **_get_redis_kwargs(max_connections=20)
        )
    return redis_pool


async def close_redis():
    global redis_pool
    if redis_pool:
        await redis_pool.aclose()
        redis_pool = None

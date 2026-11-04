from __future__ import annotations

from redis.asyncio import Redis

from oldpages_api.core.config import get_settings

_redis: Redis | None = None


def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(
            get_settings().redis_url,
            decode_responses=True,
            health_check_interval=30,
        )
    return _redis


async def check_redis() -> None:
    client = get_redis()
    pong = await client.ping()
    if pong is not True:
        raise RuntimeError("Redis ping failed")


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None

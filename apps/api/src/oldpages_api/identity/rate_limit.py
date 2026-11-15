"""Fixed-window request limits in Redis, for endpoints that send email or can be guessed at."""

from __future__ import annotations

import hashlib
import ipaddress
import logging

from oldpages_api.shared.cache import redis as redis_cache

logger = logging.getLogger(__name__)


def limit_key(scope: str, value: str) -> str:
    # Hashed so Redis never holds raw emails or IPs.
    return f"ratelimit:{scope}:{hashlib.sha256(value.encode()).hexdigest()[:32]}"


def is_public_ip(value: str | None) -> bool:
    """Private/loopback addresses are usually a proxy in front of us, shared by every user."""
    try:
        return value is not None and ipaddress.ip_address(value).is_global
    except ValueError:
        return False


async def count(key: str) -> int:
    """Hits so far in the current window (0 if Redis is down)."""
    try:
        value = await redis_cache.get_redis().get(key)
        return int(value or 0)
    except Exception:
        logger.warning("rate_limit_unavailable", extra={"key": key}, exc_info=True)
        return 0


async def allow(key: str, limit: int, window_seconds: int) -> bool:
    """Count one hit; False once `limit` hits land inside the window. Fails open without Redis."""
    try:
        client = redis_cache.get_redis()
        hits = await client.incr(key)
        if hits == 1:
            await client.expire(key, window_seconds)
        return int(hits) <= limit
    except Exception:
        logger.warning("rate_limit_unavailable", extra={"key": key}, exc_info=True)
        return True

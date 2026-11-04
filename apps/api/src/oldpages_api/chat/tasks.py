from __future__ import annotations

import json


async def publish_realtime_event(conversation_public_id: str, event_type: str, payload: dict | None = None) -> None:
    """Publish a real-time event to Redis pub/sub for WebSocket fanout."""
    from oldpages_api.shared.cache.redis import get_redis
    try:
        redis = get_redis()
        message = json.dumps({"type": event_type, "conversation_id": conversation_public_id, **(payload or {})})
        await redis.publish(f"conversation:{conversation_public_id}", message)
    except Exception:
        pass  # Never let pub/sub failure break the request


async def publish_user_event(user_public_id: str, event_type: str, payload: dict | None = None) -> None:
    """Publish a real-time event to a specific user's channel."""
    from oldpages_api.shared.cache.redis import get_redis
    try:
        redis = get_redis()
        message = json.dumps({"type": event_type, **(payload or {})})
        await redis.publish(f"user:{user_public_id}", message)
    except Exception:
        pass

from datetime import datetime, timezone

import redis.asyncio as aioredis
from fastapi import HTTPException

from backend.config import settings

_redis = None


async def _get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def rate_limit(user_id: str, max_requests: int = 10, window_seconds: int = 60):
    r = await _get_redis()
    minute = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    key = f"rate:{user_id}:{minute}"

    count = await r.incr(key)
    if count == 1:
        await r.expire(key, window_seconds)

    if count > max_requests:
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests. Limit: {max_requests} per {window_seconds}s.",
        )

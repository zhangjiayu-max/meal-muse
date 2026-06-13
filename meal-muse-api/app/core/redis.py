import redis.asyncio as redis
from app.config import get_settings

settings = get_settings()

redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    max_connections=50,
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True,
)


async def get_redis() -> redis.Redis:
    return redis_client
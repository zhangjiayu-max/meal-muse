"""Redis 缓存工具层 — 提供 get/set/delete 操作，异常不阻断业务"""

import logging
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

DEFAULT_TTL = 86400  # 24 小时


async def cache_get(key: str) -> str | None:
    """读取缓存，失败返回 None"""
    try:
        r = await get_redis()
        return await r.get(key)
    except Exception as e:
        logger.warning("cache_get 失败 key=%s: %s", key, e)
        return None


async def cache_set(key: str, value: str, ttl: int = DEFAULT_TTL) -> None:
    """写入缓存，失败静默"""
    try:
        r = await get_redis()
        await r.set(key, value, ex=ttl)
    except Exception as e:
        logger.warning("cache_set 失败 key=%s: %s", key, e)


async def cache_delete(key: str) -> None:
    """删除缓存 key，失败静默"""
    try:
        r = await get_redis()
        await r.delete(key)
    except Exception as e:
        logger.warning("cache_delete 失败 key=%s: %s", key, e)

from fastapi import APIRouter
from app.core.redis import get_redis

router = APIRouter(tags=["健康检查"])


@router.get("/health")
async def health_check():
    """服务健康检查"""
    try:
        redis = await get_redis()
        await redis.ping()
        redis_ok = True
    except Exception:
        redis_ok = False

    return {
        "status": "ok",
        "service": "MealMuse API",
        "redis": "ok" if redis_ok else "error",
    }

"""认证服务 — 从 auth.py 迁入"""

import os
import random
import logging
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

DEV_CODE = "888888"
IS_DEV = os.getenv("ENV", "dev") == "dev"


async def send_verification_code(phone: str) -> str:
    """发送验证码，返回验证码"""
    redis = await get_redis()

    if IS_DEV:
        code = DEV_CODE
    else:
        code = str(random.randint(100000, 999999))
        # TODO: 调用短信服务商 API 发送验证码
        # _send_sms(phone, code)

    await redis.setex(f"sms:code:{phone}", 300, code)
    logger.info(f"验证码已发送: phone={phone[:3]}****{phone[-4:]}")
    return code


async def verify_code(phone: str, code: str) -> bool:
    """验证验证码"""
    redis = await get_redis()
    stored_code = await redis.get(f"sms:code:{phone}")

    if stored_code and stored_code == code:
        await redis.delete(f"sms:code:{phone}")
        return True

    if IS_DEV and code == DEV_CODE:
        return True

    return False

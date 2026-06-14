"""中间件：Request ID + 访问日志"""

import uuid
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("meal_muse.access")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """为每个请求附加唯一 ID，并记录访问日志"""

    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request.state.request_id = request_id

        start = time.time()
        response = await call_next(request)
        elapsed = (time.time() - start) * 1000

        response.headers["X-Request-ID"] = request_id

        # 跳过健康检查的日志
        if request.url.path != "/api/v1/health":
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} "
                f"-> {response.status_code} ({elapsed:.0f}ms)"
            )

        return response

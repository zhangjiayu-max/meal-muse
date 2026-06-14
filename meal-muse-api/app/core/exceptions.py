"""统一异常处理"""

from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class AppException(Exception):
    """应用级异常基类"""

    def __init__(self, status_code: int, message: str, code: str = "", detail: str = ""):
        self.status_code = status_code
        self.message = message
        self.code = code
        self.detail = detail


class NotFoundError(AppException):
    def __init__(self, resource: str = "资源"):
        super().__init__(404, f"{resource}不存在", "NOT_FOUND")


class ForbiddenError(AppException):
    def __init__(self, message: str = "无权访问"):
        super().__init__(403, message, "FORBIDDEN")


class BadRequestError(AppException):
    def __init__(self, message: str, detail: str = ""):
        super().__init__(400, message, "BAD_REQUEST", detail)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "无效的认证凭据"):
        super().__init__(401, message, "UNAUTHORIZED")


class AIServiceError(AppException):
    def __init__(self, message: str = "AI 服务暂时不可用"):
        super().__init__(503, message, "AI_SERVICE_ERROR")


def register_exception_handlers(app):
    """注册全局异常处理器到 FastAPI app"""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning(f"AppException: {exc.code} - {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message, "code": exc.code, "detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "服务器内部错误", "code": "INTERNAL_ERROR"},
        )

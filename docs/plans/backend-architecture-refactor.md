# MealMuse 后端架构完善设计稿

> 版本：v1.0 | 日期：2026-06-13 | 基于项目全量扫描

---

## 1. 代码分层重构

### 1.1 目标架构

```
meal-muse-api/app/
├── main.py                  # FastAPI 入口（只注册路由和中间件）
├── config.py                # 配置（环境区分 + 类型安全）
├── api/v1/                  # 路由层（参数校验 + 调 service）
│   ├── auth.py
│   ├── diet.py
│   ├── chat.py
│   ├── meals.py
│   ├── reports.py
│   ├── menstrual.py
│   ├── family.py
│   ├── body_metrics.py
│   ├── users.py
│   └── health.py
├── services/                # 业务逻辑层
│   ├── auth_service.py      # 新增：验证码/登录/JWT 逻辑
│   ├── food_parser.py       # 新增：从 diet.py 迁入 parse_food_text
│   ├── chat_service.py      # 新增：从 chat.py 迁入 SYSTEM_PROMPT + 历史加载
│   ├── report_service.py    # 新增：从 reports.py 迁入 report 生成逻辑
│   ├── ai_service.py        # 已有，增强（重试/多模型/流式）
│   ├── context_builder.py   # 已有
│   ├── meal_plan_engine.py  # 已有
│   ├── nutrition_calculator.py # 已有
│   └── safety_guard.py      # 已有
├── repositories/            # 数据访问层（新增）
│   ├── base.py              # 泛型 CRUD 基类
│   ├── user_repo.py
│   ├── diet_repo.py
│   └── chat_repo.py
├── models/                  # ORM 模型（已有，补索引）
├── schemas/                 # Pydantic schema
│   ├── base.py              # 新增：通用 schema
│   ├── user.py              # 已有，补全
│   ├── diet.py              # 已有
│   ├── chat.py              # 已有
│   ├── meal.py              # 已有
│   ├── body.py              # 新增
│   ├── menstrual.py          # 新增
│   ├── family.py            # 新增
│   └── report.py            # 新增
└── core/                    # 基础设施
    ├── database.py          # 已有
    ├── redis.py             # 已有
    ├── security.py          # 已有
    ├── deps.py              # 已有
    ├── exceptions.py        # 新增：统一异常
    ├── logging.py           # 新增：日志配置
    └── middleware.py         # 新增：request_id + 限流
```

### 1.2 迁移映射

**从路由层抽离到 services 的逻辑**：

| 路由文件 | 迁出的逻辑 | 迁入的 service |
|----------|-----------|---------------|
| `auth.py` | 验证码生成/校验、登录逻辑 | `auth_service.py` |
| `diet.py` | `parse_food_text()` + `_simple_parse()` | `food_parser.py` |
| `chat.py` | `SYSTEM_PROMPT`、`_load_history()`、会话管理 | `chat_service.py` |
| `reports.py` | `ai_summary` 生成逻辑、营养评分计算 | `report_service.py` |
| `meals.py` | 无需迁移（已调用 meal_plan_engine） | - |

---

## 2. 通用 Schema（schemas/base.py）

```python
# app/schemas/base.py
from typing import TypeVar, Generic, List, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ErrorResponse(BaseModel):
    error: str
    detail: str = ""
    code: str = ""


class SuccessResponse(BaseModel):
    message: str
    data: Optional[dict] = None
```

---

## 3. 统一异常处理（core/exceptions.py）

```python
# app/core/exceptions.py
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class AppException(Exception):
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


class AIServiceError(AppException):
    def __init__(self, message: str = "AI 服务暂时不可用"):
        super().__init__(503, message, "AI_SERVICE_ERROR")


def register_exception_handlers(app):
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning(f"AppException: {exc.code} - {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message, "code": exc.code, "detail": exc.detail}
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": "服务器内部错误", "code": "INTERNAL_ERROR"}
        )
```

---

## 4. 日志系统（core/logging.py）

```python
# app/core/logging.py
import logging
import sys
from app.config import settings


def setup_logging():
    level = logging.DEBUG if settings.ENV == "dev" else logging.INFO
    format_str = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        if settings.ENV == "dev"
        else '{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","msg":"%(message)s"}'
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(format_str))
    handler.setLevel(level)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # 降低第三方库日志级别
    for name in ["uvicorn", "sqlalchemy.engine"]:
        logging.getLogger(name).setLevel(logging.WARNING)
```

### 4.1 Request ID 中间件

```python
# app/core/middleware.py
import uuid
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("meal_muse.access")

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request.state.request_id = request_id

        start = time.time()
        response = await call_next(request)
        elapsed = (time.time() - start) * 1000

        response.headers["X-Request-ID"] = request_id
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"-> {response.status_code} ({elapsed:.0f}ms)"
        )
        return response
```

---

## 5. AI 服务增强

### 5.1 重试机制

```python
# app/services/ai_service.py 增强
import asyncio
from typing import Optional, AsyncGenerator

class AIService:
    MAX_RETRIES = 2
    RETRY_DELAYS = [1, 3]  # 秒

    async def call_with_retry(
        self,
        messages: list,
        *,
        model: Optional[str] = None,
        response_format: Optional[dict] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> dict:
        model = model or self._select_model(messages)
        last_error = None

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                result = await self._call_openai(
                    messages, model=model, response_format=response_format,
                    temperature=temperature, max_tokens=max_tokens,
                )
                logger.info(
                    f"AI call success: model={model}, "
                    f"tokens={result['tokens']}, time={result['response_time_ms']}ms"
                )
                return result
            except Exception as e:
                last_error = e
                logger.warning(
                    f"AI call failed (attempt {attempt + 1}/{self.MAX_RETRIES + 1}): {e}"
                )
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(self.RETRY_DELAYS[attempt])

        raise AIServiceError(f"AI 服务调用失败: {last_error}")

    def _select_model(self, messages: list) -> str:
        """根据场景选择模型"""
        first_msg = messages[-1]["content"] if messages else ""
        # 食物解析用 turbo（更快更便宜）
        if len(first_msg) < 100 and any(k in first_msg for k in ["吃了", "食物", "解析"]):
            return settings.AI_FOOD_PARSE_MODEL or "qwen-turbo"
        # 餐食生成用 plus
        if any(k in first_msg for k in ["生成", "计划", "推荐"]):
            return settings.AI_MEAL_PLAN_MODEL or "qwen-plus"
        # 默认
        return settings.AI_DEFAULT_MODEL or "qwen-plus"
```

---

## 6. Repository 基类

```python
# app/repositories/base.py
from typing import TypeVar, Type, Optional, List, Generic
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: UUID) -> Optional[T]:
        return await self.db.get(self.model, id)

    async def get_list(
        self,
        *,
        filters: list = None,
        offset: int = 0,
        limit: int = 20,
        order_by: str = "created_at",
        ascending: bool = False,
    ) -> List[T]:
        query = select(self.model)
        if filters:
            for f in filters:
                query = query.where(f)
        col = getattr(self.model, order_by, self.model.created_at)
        query = query.order_by(col.asc() if ascending else col.desc())
        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(self, *, filters: list = None) -> int:
        query = select(func.count()).select_from(self.model)
        if filters:
            for f in filters:
                query = query.where(f)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def create(self, instance: T) -> T:
        self.db.add(instance)
        await self.db.flush()
        return instance

    async def update(self, instance: T) -> T:
        await self.db.flush()
        return instance

    async def soft_delete(self, instance: T) -> T:
        instance.deleted_at = datetime.now()
        await self.db.flush()
        return instance
```

---

## 7. 配置管理增强

```python
# app/config.py 重构
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # 环境
    ENV: str = Field(default="dev", description="dev / staging / prod")

    # 数据库
    DATABASE_URL: str = Field(..., description="PostgreSQL 连接串")

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # 安全
    SECRET_KEY: str = Field(..., description="JWT 签名密钥，必须通过 .env 设置")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30)

    # AI
    DASHSCOPE_API_KEY: str = Field(default="")
    AI_DEFAULT_MODEL: str = Field(default="qwen-plus")
    AI_FOOD_PARSE_MODEL: str = Field(default="qwen-turbo")
    AI_MEAL_PLAN_MODEL: str = Field(default="qwen-plus")

    # CORS
    CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000"])

    # 短信
    SMS_PROVIDER: str = Field(default="dev")  # dev / aliyun / tencent
    SMS_ACCESS_KEY: str = Field(default="")
    SMS_ACCESS_SECRET: str = Field(default="")
    SMS_SIGN_NAME: str = Field(default="MealMuse")
    SMS_TEMPLATE_CODE: str = Field(default="")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

### 7.1 .env.example

```env
# 环境
ENV=dev

# 数据库
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/meal_muse

# Redis
REDIS_URL=redis://localhost:6379/0

# 安全（生产环境必须修改）
SECRET_KEY=your-secret-key-change-this

# AI
DASHSCOPE_API_KEY=sk-xxx

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# 短信（生产环境配置）
SMS_PROVIDER=dev
```

---

## 8. 数据库索引补充

```python
# 需要添加的联合索引
# models/diet_record.py
__table_args__ = (
    Index('ix_diet_user_date', 'user_id', 'record_date'),
    Index('ix_diet_user_deleted', 'user_id', 'deleted_at'),
)

# models/ai_chat_message.py
__table_args__ = (
    Index('ix_chat_session_created', 'session_id', 'created_at'),
)
```

---

## 9. Alembic 迁移配置

```python
# alembic/env.py 关键配置
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.core.database import Base
from app.models import *  # 导入所有模型

config = context.config
config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
```

---

## 10. 执行优先级

| 序号 | 任务 | 优先级 | 依赖 |
|------|------|--------|------|
| 1 | config.py 重构 | W1 | 无 |
| 2 | exceptions.py + 全局异常处理 | W1 | 无 |
| 3 | logging.py + middleware.py | W1 | config |
| 4 | schemas/base.py 通用 schema | W1 | 无 |
| 5 | auth_service.py 抽离 | W1 | exceptions |
| 6 | food_parser.py 抽离 | W1 | exceptions |
| 7 | chat_service.py 抽离 | W1 | exceptions |
| 8 | report_service.py 抽离 | W1 | exceptions |
| 9 | schemas 补全（body/menstrual/family/report） | W1 | schemas/base |
| 10 | AI 服务增强（重试/多模型） | W2 | logging |
| 11 | Repository 层（base + diet_repo + chat_repo） | W2 | 无 |
| 12 | 数据库索引补充 | W2 | 无 |
| 13 | Alembic 配置 | W2 | models 索引 |
| 14 | .env.example 更新 | W1 | config |

---

*文档版本：v1.0 | 日期：2026-06-13*

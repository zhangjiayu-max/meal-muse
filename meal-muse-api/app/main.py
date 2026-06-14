from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import init_db, Base
# 导入所有模型，确保 metadata 注册完整
from app.models import (
    user, health_goal, diet_record, meal_plan, menstrual_cycle,
    family, body_metric, user_profile, health_condition, allergy_tag,
    exercise_record, ai_chat_message, user_favorite_food,
)  # noqa: F401
from app.api.v1 import (
    auth, users, diet, health, meals, chat,
    menstrual, family as family_api, body_metrics, reports, admin, prompts,
)
from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import RequestIDMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 初始化日志
    setup_logging()
    await init_db()
    # 自动迁移：为 user_profiles 新增画像增强字段
    from scripts.migrate_profile_v2 import check_and_migrate
    await check_and_migrate()
    yield


app = FastAPI(
    title="MealMuse API",
    description="AI 驱动的智能饮食管理助手",
    version="0.3.0",
    lifespan=lifespan,
)

# 中间件：Request ID + 访问日志
app.add_middleware(RequestIDMiddleware)

# CORS 配置：从 .env 读取，支持生产环境多域名
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理
register_exception_handlers(app)

# 路由注册
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(diet.router, prefix="/api/v1")
app.include_router(meals.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(menstrual.router, prefix="/api/v1")
app.include_router(family_api.router, prefix="/api/v1")
app.include_router(body_metrics.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(prompts.router, prefix="/api/v1")

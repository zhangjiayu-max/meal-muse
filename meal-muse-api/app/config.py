from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # 环境
    APP_NAME: str = "MealMuse"
    ENV: str = Field(default="dev", description="dev / staging / prod")
    DEBUG: bool = Field(default=True, description="开发模式（ENV=prod 时自动关闭）")

    # 数据库
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://xiaoyuer@localhost:5432/mealmuse",
        description="PostgreSQL 连接串",
    )

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # 安全
    SECRET_KEY: str = Field(
        default="CHANGE-ME-IN-PRODUCTION",
        description="JWT 签名密钥，生产环境必须通过 .env 设置固定值",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30)

    # ========== AI 多模型支持 ==========
    # 当前使用的 AI 提供商（dashscope / xiaomi / openai / custom）
    AI_PROVIDER: str = Field(default="dashscope", description="当前 AI 提供商")

    # --- 通义千问 (DashScope) ---
    DASHSCOPE_API_KEY: str = Field(default="")
    DASHSCOPE_API_URL: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    )
    DASHSCOPE_DEFAULT_MODEL: str = Field(default="qwen-plus")

    # --- 小米 AI (Xiaomi) ---
    XIAOMI_API_KEY: str = Field(default="")
    XIAOMI_API_URL: str = Field(
        default="https://api.xiaomi.com/v1/chat/completions",
        description="小米 AI API 地址（OpenAI 兼容格式）",
    )
    XIAOMI_DEFAULT_MODEL: str = Field(default="milm")

    # --- OpenAI ---
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_API_URL: str = Field(
        default="https://api.openai.com/v1/chat/completions",
    )
    OPENAI_DEFAULT_MODEL: str = Field(default="gpt-4o-mini")

    # --- 自定义 OpenAI 兼容 ---
    CUSTOM_API_KEY: str = Field(default="")
    CUSTOM_API_URL: str = Field(default="")
    CUSTOM_DEFAULT_MODEL: str = Field(default="")

    # 模型别名（按场景）
    AI_FOOD_PARSE_MODEL: str = Field(default="", description="食物解析模型名，为空则用各提供商的 default")
    AI_MEAL_PLAN_MODEL: str = Field(default="", description="餐食生成模型名，为空则用各提供商的 default")

    # ========== MCP 外部服务 ==========
    SPOONACULAR_API_KEY: str = Field(
        default="",
        description="Spoonacular API Key (免费 150 次/天)",
    )
    WEATHER_API_KEY: str = Field(
        default="",
        description="和风天气 API Key (可选，默认用 wttr.in 免费服务)",
    )
    AMAP_API_KEY: str = Field(
        default="",
        description="高德地图 Web API Key (附近餐厅搜索)",
    )

    # ========== 其他 ==========

    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="逗号分隔的允许域名",
    )

    # 短信
    SMS_PROVIDER: str = Field(default="dev", description="dev / aliyun / tencent")
    SMS_ACCESS_KEY: str = Field(default="")
    SMS_ACCESS_SECRET: str = Field(default="")
    SMS_SIGN_NAME: str = Field(default="MealMuse")
    SMS_TEMPLATE_CODE: str = Field(default="")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def AI_PROVIDERS(self) -> dict:
        """返回所有 AI 提供商的配置字典"""
        return {
            "dashscope": {
                "name": "通义千问",
                "api_key": self.DASHSCOPE_API_KEY,
                "api_url": self.DASHSCOPE_API_URL,
                "default_model": self.DASHSCOPE_DEFAULT_MODEL,
            },
            "xiaomi": {
                "name": "小米 AI",
                "api_key": self.XIAOMI_API_KEY,
                "api_url": self.XIAOMI_API_URL,
                "default_model": self.XIAOMI_DEFAULT_MODEL,
            },
            "openai": {
                "name": "OpenAI",
                "api_key": self.OPENAI_API_KEY,
                "api_url": self.OPENAI_API_URL,
                "default_model": self.OPENAI_DEFAULT_MODEL,
            },
            "custom": {
                "name": "自定义",
                "api_key": self.CUSTOM_API_KEY,
                "api_url": self.CUSTOM_API_URL,
                "default_model": self.CUSTOM_DEFAULT_MODEL,
            },
        }

    def model_post_init(self, __context):
        """生产环境自动关闭 DEBUG"""
        if self.ENV == "prod":
            self.DEBUG = False


@lru_cache
def get_settings() -> Settings:
    return Settings()

import secrets
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "MealMuse"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql+asyncpg://xiaoyuer@localhost:5432/mealmuse"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = secrets.token_urlsafe(32)  # 默认随机生成，生产环境必须通过 .env 设置固定值
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    DASHSCOPE_API_KEY: str = ""
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"  # 生产环境通过 .env 设置实际域名

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
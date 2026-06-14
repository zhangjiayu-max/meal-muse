"""数据库迁移脚本 — 为 user_profiles 表新增画像增强字段

用法: python -m scripts.migrate_profile_v2
或通过 API 启动时自动执行

新增字段:
- constitution_types JSONB  体质类型
- health_sub_goals JSONB    子目标
- preferred_ingredients JSONB 偏好食材
- cooking_frequency VARCHAR(20) 做饭频次
- takeout_preference VARCHAR(20) 外卖偏好
- family_cooking BOOLEAN    是否为家人做饭
- family_members JSONB      家庭成员
- onboarding_version INTEGER 版本号
"""

import asyncio
import logging
from sqlalchemy import text
from app.core.database import engine

logger = logging.getLogger(__name__)

MIGRATIONS = [
    {
        "name": "add_constitution_types",
        "sql": "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS constitution_types JSONB DEFAULT '[]'",
    },
    {
        "name": "add_health_sub_goals",
        "sql": "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS health_sub_goals JSONB DEFAULT '[]'",
    },
    {
        "name": "add_preferred_ingredients",
        "sql": "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS preferred_ingredients JSONB DEFAULT '[]'",
    },
    {
        "name": "add_cooking_frequency",
        "sql": "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS cooking_frequency VARCHAR(20) DEFAULT 'often'",
    },
    {
        "name": "add_takeout_preference",
        "sql": "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS takeout_preference VARCHAR(20) DEFAULT 'any'",
    },
    {
        "name": "add_family_cooking",
        "sql": "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS family_cooking BOOLEAN DEFAULT false",
    },
    {
        "name": "add_family_members",
        "sql": "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS family_members JSONB DEFAULT '[]'",
    },
    {
        "name": "add_onboarding_version",
        "sql": "ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS onboarding_version INTEGER DEFAULT 2",
    },
]


async def run_migrations():
    """执行所有迁移"""
    async with engine.begin() as conn:
        for m in MIGRATIONS:
            try:
                await conn.execute(text(m["sql"]))
                logger.info(f"Migration OK: {m['name']}")
            except Exception as e:
                logger.warning(f"Migration SKIP: {m['name']} — {e}")


async def check_and_migrate():
    """检查并执行迁移（幂等，已有字段会跳过）"""
    await run_migrations()
    logger.info("Profile v2 migration check complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(check_and_migrate())

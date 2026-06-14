"""对话服务 — 使用 Agent 架构，Prompt 集中管理，Action 自动执行"""

import json
import uuid
import logging
from datetime import date, datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.diet_record import DietRecord
from app.models.user_profile import UserProfile
from app.agents.chat_agent import ChatAgent
from app.services.context_builder import get_user_context, _get_profile, _get_allergies

logger = logging.getLogger(__name__)

# 初始化 Agent
chat_agent = ChatAgent()


async def chat_send(
    db: AsyncSession,
    current_user: User,
    content: str,
    session_id: uuid.UUID | None = None,
) -> dict:
    """发送消息给 AI（使用 Agent 架构）"""
    # 1. 获取用户上下文（给 AI 的文本）+ 结构化 profile 数据（给 MCP 路由）
    context = await get_user_context(db, current_user)

    profile_data = None
    profile = await _get_profile(db, current_user.id)
    if profile:
        allergies = await _get_allergies(db, current_user.id)
        allergy_names = [a.custom_name or a.allergen for a in allergies] if allergies else []
        profile_data = {
            "diet_type": profile.diet_type,
            "allergies": ",".join(allergy_names) if allergy_names else None,
        }

    # 2. 使用 Agent 执行对话
    result = await chat_agent.chat(
        db=db,
        user=current_user,
        user_message=content,
        session_id=session_id,
        user_context=context,
        profile_data=profile_data,
    )

    # 3. 执行 Actions
    if result.get("actions"):
        await _execute_actions(db, current_user, result["actions"])

    return result


async def _execute_actions(db: AsyncSession, user: User, actions: list[dict]) -> None:
    """执行 AI 回复中解析出的 Actions"""
    for action in actions:
        action_type = action.get("type", "")
        action_data = action.get("data", "")

        try:
            if action_type == "DIET_RECORD":
                await _execute_diet_record(db, user, action_data)
            elif action_type == "PROFILE_UPDATE":
                await _execute_profile_update(db, user, action_data)
            elif action_type == "MEAL_LINK":
                logger.info("MEAL_LINK action (暂不处理): %s", action_data)
            else:
                logger.warning("未知 action 类型: %s", action_type)
        except Exception as e:
            logger.warning("执行 action %s 失败: %s", action_type, e)


async def _execute_diet_record(db: AsyncSession, user: User, data: str) -> None:
    """解析食物文本并创建饮食记录"""
    from app.services.food_parser import parse_food_text

    # 推断餐次
    meal_type = "snack"
    data_lower = data.lower()
    for kw, mt in [("早餐", "breakfast"), ("早饭", "breakfast"), ("午餐", "lunch"), ("午饭", "lunch"),
                    ("晚餐", "dinner"), ("晚饭", "dinner"), ("加餐", "snack"), ("下午茶", "snack")]:
        if kw in data:
            meal_type = mt
            break

    # 如果没有明确餐次，按时间推断
    if meal_type == "snack":
        hour = datetime.now(timezone.utc).hour
        if 5 <= hour < 10:
            meal_type = "breakfast"
        elif 10 <= hour < 14:
            meal_type = "lunch"
        elif 16 <= hour < 21:
            meal_type = "dinner"

    # AI 解析食物
    parsed = await parse_food_text(data)

    record = DietRecord(
        user_id=user.id,
        meal_type=meal_type,
        food_text=data,
        parsed_foods=parsed.get("foods", []),
        total_calories=parsed.get("total_calories", 0),
        total_protein=parsed.get("total_protein", 0),
        total_fat=parsed.get("total_fat", 0),
        total_carbs=parsed.get("total_carbs", 0),
        total_fiber=parsed.get("total_fiber", 0),
        record_date=date.today(),
        source="chat_action",
    )
    db.add(record)
    await db.commit()
    logger.info("Action DIET_RECORD: 创建饮食记录 meal=%s cal=%s", meal_type, parsed.get("total_calories"))


async def _execute_profile_update(db: AsyncSession, user: User, data: str) -> None:
    """解析并更新用户画像字段"""
    # 解析格式: "field=value" 或 JSON
    try:
        update = json.loads(data)
    except json.JSONDecodeError:
        # 尝试 key=value 格式
        if "=" in data:
            key, _, value = data.partition("=")
            update = {"field": key.strip(), "value": value.strip()}
        else:
            logger.warning("PROFILE_UPDATE 数据格式无法解析: %s", data)
            return

    field = update.get("field", "")
    value = update.get("value", "")

    if not field:
        return

    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        logger.warning("PROFILE_UPDATE: 用户 %s 无 profile", user.id)
        return

    # 字段映射（中文标签 → 模型字段）
    field_map = {
        "体质": "constitution_types",
        "constitution_types": "constitution_types",
        "忌口": "disliked_foods",
        "disliked_foods": "disliked_foods",
        "口味": "taste_preference",
        "taste_preference": "taste_preference",
        "菜系": "cuisine_preference",
        "cuisine_preference": "cuisine_preference",
        "饮食类型": "diet_type",
        "diet_type": "diet_type",
        "偏好食材": "preferred_ingredients",
        "preferred_ingredients": "preferred_ingredients",
    }

    model_field = field_map.get(field, field)

    # 类型转换
    if model_field in ("constitution_types", "disliked_foods", "cuisine_preference", "preferred_ingredients"):
        # 列表类型字段
        if isinstance(value, str):
            value = [v.strip() for v in value.split(",") if v.strip()]

    if hasattr(profile, model_field):
        setattr(profile, model_field, value)
        await db.commit()
        # 清除画像缓存
        from app.core.cache import cache_delete
        await cache_delete(f"profile_summary:{user.id}")
        logger.info("Action PROFILE_UPDATE: %s = %s", model_field, value)
    else:
        logger.warning("PROFILE_UPDATE: 未知字段 %s", model_field)

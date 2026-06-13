"""用户上下文构建器 — 为 AI 提供完整的用户画像、健康状态、饮食历史"""

from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.models.user import User
from app.models.diet_record import DietRecord
from app.models.health_condition import HealthCondition
from app.models.allergy_tag import AllergyTag
from app.models.user_profile import UserProfile
from app.models.menstrual_cycle import MenstrualCycle
from app.models.health_goal import HealthGoal


async def get_user_context(db: AsyncSession, user: User) -> str:
    """
    构建完整的用户上下文，供 AI 使用。
    包含：基础信息、健康目标、画像偏好、疾病禁忌、过敏原、
    经期阶段、近期饮食记录。
    """
    parts: list[str] = [f"用户信息：\n- 昵称：{user.nickname}"]

    # 身高体重
    if user.height_cm:
        parts.append(f"- 身高：{user.height_cm}cm，体重：{user.current_weight or '未填写'}kg")

    # 健康目标
    goal = await _get_active_goal(db, user.id)
    if goal:
        parts.append(
            f"- 目标类型：{goal.goal_type}"
            f"{f'，目标体重：{goal.target_weight}kg' if goal.target_weight else ''}"
            f"{f'，每日热量目标：{goal.daily_calorie_target}kcal' if goal.daily_calorie_target else ''}"
        )

    # 用户画像
    profile = await _get_profile(db, user.id)
    if profile:
        info = []
        if profile.diet_type and profile.diet_type != "normal":
            info.append(f"饮食类型：{profile.diet_type}")
        if profile.cuisine_preference:
            info.append(f"偏好菜系：{'、'.join(profile.cuisine_preference)}")
        if profile.taste_preference and profile.taste_preference != "mild":
            info.append(f"口味偏好：{profile.taste_preference}")
        if profile.disliked_foods:
            info.append(f"忌口食物：{'、'.join(profile.disliked_foods)}")
        if profile.cooking_facility == "no_kitchen":
            info.append("⚠ 无厨房烹饪条件，推荐即食或外卖方案")
        if profile.meal_pattern:
            info.append(f"就餐模式：{profile.meal_pattern.replace('_', ' 餐 ')}")
        if info:
            parts.append("- 饮食偏好：" + "、".join(info))

    # 健康疾病
    conditions = await _get_health_conditions(db, user.id)
    if conditions:
        condition_str = "、".join(
            f"{c.condition_type}({c.severity})" for c in conditions
        )
        parts.append(f"- ⚠ 健康情况：{condition_str}")

    # 过敏原
    allergies = await _get_allergies(db, user.id)
    if allergies:
        allergy_str = "、".join(
            a.custom_name if a.allergen == "custom" else a.allergen for a in allergies
        )
        parts.append(f"- ⛔ 过敏原：{allergy_str}")

    # 经期阶段
    menstrual_phase = await _get_menstrual_phase(db, user.id)
    if menstrual_phase:
        parts.append(f"- 经期阶段：{menstrual_phase}")

    # 近期饮食记录
    diet_summary = await _get_diet_summary(db, user.id)
    if diet_summary:
        parts.append(diet_summary)

    # 头部提示
    header = "以下是你服务的真实用户的完整信息，请基于这些信息提供个性化建议：\n"
    return header + "\n".join(parts)


async def get_ai_prompt_context(db: AsyncSession, user: User) -> str:
    """
    返回简短的 AI prompt 上下文（用于 food parsing / meal plan 等场景）。
    比 get_user_context 更精简，只包含生成所需的关键信息。
    """
    profile = await _get_profile(db, user.id)
    allergies = await _get_allergies(db, user.id)
    conditions = await _get_health_conditions(db, user.id)

    parts: list[str] = []
    if profile:
        if profile.diet_type and profile.diet_type != "normal":
            parts.append(f"饮食类型：{profile.diet_type}")
        if profile.disliked_foods:
            parts.append(f"忌口：{'、'.join(profile.disliked_foods)}")
    if allergies:
        parts.append(f"过敏：{'、'.join(a.custom_name or a.allergen for a in allergies)}")
    if conditions:
        parts.append(f"健康情况：{'、'.join(c.condition_type for c in conditions)}")

    return "\n".join(parts) if parts else ""


# ——— 内部辅助 ———


async def _get_active_goal(db: AsyncSession, user_id: str):
    result = await db.execute(
        select(HealthGoal).where(
            HealthGoal.user_id == user_id,
            HealthGoal.status == "active",
        ).order_by(desc(HealthGoal.created_at)).limit(1)
    )
    return result.scalar_one_or_none()


async def _get_profile(db: AsyncSession, user_id: str):
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def _get_health_conditions(db: AsyncSession, user_id: str):
    result = await db.execute(
        select(HealthCondition).where(HealthCondition.user_id == user_id)
    )
    return result.scalars().all()


async def _get_allergies(db: AsyncSession, user_id: str):
    result = await db.execute(
        select(AllergyTag).where(AllergyTag.user_id == user_id)
    )
    return result.scalars().all()


async def _get_menstrual_phase(db: AsyncSession, user_id: str) -> str | None:
    """获取当前经期阶段"""
    result = await db.execute(
        select(MenstrualCycle).where(
            MenstrualCycle.user_id == user_id
        ).order_by(desc(MenstrualCycle.period_start)).limit(1)
    )
    cycle = result.scalar_one_or_none()
    if not cycle:
        return None

    today = date.today()
    if cycle.period_start and cycle.period_end and cycle.period_start <= today <= cycle.period_end:
        return "月经期（需温补驱寒、补铁）"
    if cycle.ovulation_day:
        days_from_ov = (today - cycle.ovulation_day).days
        if 0 <= days_from_ov <= 2:
            return "排卵期（推荐促排卵食物）"
        if 3 <= days_from_ov <= 10:
            return "黄体期（缓解PMS，推荐高蛋白、深色食物）"
    if cycle.period_end and today > cycle.period_end:
        cycle_day = (today - cycle.period_start).days
        if 5 <= cycle_day <= 13:
            return "卵泡期（推荐高蛋白、深色食物）"
    return None


async def _get_diet_summary(db: AsyncSession, user_id: str) -> str | None:
    """获取近期饮食总结"""
    week_ago = date.today() - timedelta(days=7)

    result = await db.execute(
        select(DietRecord).where(
            DietRecord.user_id == user_id,
            DietRecord.record_date >= week_ago,
            DietRecord.deleted_at.is_(None),
        ).order_by(desc(DietRecord.recorded_at)).limit(20)
    )
    records = result.scalars().all()
    if not records:
        return None

    total_cal = sum(r.total_calories for r in records)
    days = len(set(r.record_date for r in records)) or 1
    avg_cal = total_cal / days
    recent_foods = list(dict.fromkeys(r.food_text for r in records[:6]))[:5]

    return (
        f"- 近7天饮食：{len(records)}条记录，日均热量约{int(avg_cal)}kcal\n"
        f"- 最近食物：{'、'.join(recent_foods)}"
    )

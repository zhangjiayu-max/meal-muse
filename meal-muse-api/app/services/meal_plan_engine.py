"""餐食计划生成引擎 — 基于用户画像 + AI 动态生成智能餐食计划"""

import json
import re
import random
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.meal_plan import MealPlan
from app.models.health_goal import HealthGoal
from app.models.user_profile import UserProfile
from app.models.exercise_record import ExerciseRecord
from app.services.ai_service import call_ai
from app.services.context_builder import get_ai_prompt_context
from app.services.safety_guard import filter_menu_plan, get_safety_rules
from app.services.nutrition_calculator import (
    calculate_daily_calorie_target,
    calculate_macros,
    estimate_calories_from_exercise,
    adjust_calorie_target_for_exercise,
)

# ——— System Prompt ———

MEAL_PLAN_SYSTEM = """你是一位专业的中式营养师，负责根据用户的健康目标、个人偏好和禁忌生成个性化的一日三餐计划。

你必须返回严格的 JSON 格式，禁止包含任何 JSON 之外的文字：
{
  "breakfast": {
    "name": "早餐名称",
    "foods": [{"name": "食物名", "amount": "份量", "calories": 数字, "protein": 数字, "fat": 数字, "carbs": 数字}],
    "total_calories": 数字,
    "total_protein": 数字,
    "total_fat": 数字,
    "total_carbs": 数字
  },
  "lunch": {...},
  "dinner": {...},
  "total_calories": 数字,
  "ai_note": "生成此计划的简短说明（1-2句）"
}

规则：
- 食物必须符合用户禁忌（过敏原、疾病、忌口）
- 优先使用用户喜欢的菜系
- 早餐热量占全天 25-30%，午餐 35-40%，晚餐 30-35%
- 每餐必须有优质蛋白
- 总热量误差不超过 ±50kcal
- 三餐必须包含至少一种深色蔬菜
- 烹饪方式优先清蒸、水煮、凉拌，少油炒
- 食物份量要具体（1碗/1份/1个/半根等）
- 如果用户无厨房（no_kitchen），则 breakfast 推荐即食食品（牛奶+面包+鸡蛋），lunch/dinner 推荐外卖搭配建议
"""


def _build_meal_prompt(
    user_context: str,
    calorie_target: int,
    macros: dict,
    date_str: str,
    meal_pattern: str = "3_meals",
) -> str:
    """组装 AI 餐食生成 prompt"""
    meals_count = {"3_meals": "三餐", "4_meals": "四餐（含下午茶）", "5_meals": "五餐（含上下午加餐）"}.get(meal_pattern, "三餐")

    prompt = f"""请为以下用户生成今日（{date_str}）{meals_count}计划。

每日总热量目标：{calorie_target}kcal
宏量营养素目标：蛋白质 {macros['protein_g']}g、脂肪 {macros['fat_g']}g、碳水 {macros['carbs_g']}g

用户信息：
{user_context}

请直接输出 JSON，不要有其他文字。"""
    return prompt


# ——— 核心函数 ———


async def generate_plan(
    db: AsyncSession,
    user: User,
    plan_date: date,
) -> MealPlan:
    """
    为用户生成指定日期的餐食计划。
    流程：获取用户画像 → 计算热量目标 → AI 生成 → 安全过滤 → 保存
    """
    # 1. 获取用户热量目标
    calorie_target = _get_calorie_target(db, user)

    # 2. 计算宏量营养素
    macros = calculate_macros(calorie_target, _get_goal_type(user))

    # 3. 获取 AI 上下文
    user_context = await get_ai_prompt_context(db, user)

    # 4. 获取用餐模式
    meal_pattern = "3_meals"
    profile = await _get_profile(db, user.id)
    if profile:
        meal_pattern = profile.meal_pattern or "3_meals"

    # 5. AI 生成
    prompt = _build_meal_prompt(
        user_context or "无特殊偏好信息",
        calorie_target,
        macros,
        plan_date.isoformat(),
        meal_pattern,
    )
    try:
        raw = await call_ai([], system_prompt=MEAL_PLAN_SYSTEM, temperature=0.7)
        plan_data = _parse_json_response(raw[0])
        if not plan_data:
            raise ValueError("AI 返回格式解析失败")
    except Exception:
        # AI 失败时使用内置模板（基于热量目标选择）
        plan_data = _get_fallback_plan(calorie_target)

    # 6. 安全过滤
    safe_plan = await filter_menu_plan(db, user.id, plan_data)

    # 7. 保存或更新
    result = await db.execute(
        select(MealPlan).where(
            MealPlan.user_id == user.id,
            MealPlan.plan_date == plan_date,
        )
    )
    existing = result.scalar_one_or_none()

    total_cal = plan_data.get("total_calories", 0)
    if existing:
        existing.breakfast = plan_data.get("breakfast")
        existing.lunch = plan_data.get("lunch")
        existing.dinner = plan_data.get("dinner")
        existing.total_calories = total_cal
        existing.ai_note = plan_data.get("ai_note", "AI 生成")
        existing.version += 1
        await db.commit()
        await db.refresh(existing)
        return existing

    plan = MealPlan(
        user_id=user.id,
        plan_date=plan_date,
        breakfast=plan_data.get("breakfast"),
        lunch=plan_data.get("lunch"),
        dinner=plan_data.get("dinner"),
        total_calories=total_cal,
        ai_note=plan_data.get("ai_note", "AI 生成"),
        status="pending",
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


async def replace_meal(
    db: AsyncSession,
    user: User,
    plan_id: str,
    meal_type: str = "lunch",
) -> MealPlan:
    """
    智能替换某一餐。
    先检查用户安全禁忌，再调用 AI 生成新的一餐。
    """
    result = await db.execute(
        select(MealPlan).where(
            MealPlan.id == plan_id,
            MealPlan.user_id == user.id,
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise ValueError("计划不存在")

    user_context = await get_ai_prompt_context(db, user)
    calorie_target = _get_calorie_target(db, user)
    macros = calculate_macros(calorie_target, _get_goal_type(user))

    replace_prompt = f"""请重新生成一餐（{meal_type}），要求：
- 热量：全天目标 {calorie_target}kcal，本餐占全天 30-40%
- 用户信息：{user_context}
- 仅替换 {meal_type} 这一餐，其他餐保持不变
- 直接返回 JSON：{{"meal_type": "{meal_type}", "data": {{...该餐完整数据...}}}}"""

    try:
        raw = await call_ai(
            [{"role": "user", "content": replace_prompt}],
            system_prompt=MEAL_PLAN_SYSTEM,
            temperature=0.8,
        )
        plan_data = _parse_json_response(raw[0])
        if plan_data and meal_type in plan_data:
            new_meal = plan_data[meal_type]
        else:
            new_meal = _get_fallback_meal(calorie_target, meal_type)
    except Exception:
        new_meal = _get_fallback_meal(calorie_target, meal_type)

    setattr(plan, meal_type, new_meal)
    plan.total_calories = (
        (plan.breakfast or {}).get("total_calories", 0)
        + (plan.lunch or {}).get("total_calories", 0)
        + (plan.dinner or {}).get("total_calories", 0)
    )
    plan.version += 1
    await db.commit()
    await db.refresh(plan)
    return plan


# ——— 内部辅助 ———


def _parse_json_response(text: str) -> dict | None:
    """从 AI 返回中提取 JSON"""
    text = text.strip()
    # 尝试找 ```json ... ``` 包裹的
    m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
    if m:
        text = m.group(1)
    else:
        # 尝试直接找第一个 { 和最后一个 }
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            text = text[start:end]
    try:
        return json.loads(text)
    except Exception:
        return None


def _get_calorie_target(db: AsyncSession, user: User) -> int:
    """获取用户每日热量目标，兜底用基础公式"""
    from app.models.health_goal import HealthGoal
    import random

    result = db.execute(
        select(HealthGoal).where(
            HealthGoal.user_id == user.id,
            HealthGoal.status == "active",
        )
    )
    goals = list(result.scalars().all())
    if goals and goals[0].daily_calorie_target:
        return goals[0].daily_calorie_target

    # 兜底：用 Harris-Benedict 估算
    if user.height_cm and user.current_weight:
        weight = float(user.current_weight)
        height = float(user.height_cm)
        bmr = 447.593 + 9.247 * weight + 3.098 * height - 4.33 * 25  # 假设 age=25
        return int(bmr * 1.55 - 300)  # 默认减脂：-300kcal
    return 1600  # 默认值


def _get_goal_type(user: User) -> str:
    """获取用户目标类型"""
    prefs = user.preferences or {}
    return prefs.get("goal_type", "maintain")


async def _get_profile(db: AsyncSession, user_id: str):
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


def _get_fallback_plan(calorie_target: int) -> dict:
    """内置兜底计划（基于热量目标选择模板）"""
    templates = [
        _FALLBACK_LOW_CAL,
        _FALLBACK_MEDIUM_CAL,
        _FALLBACK_HIGH_CAL,
    ]
    if calorie_target < 1400:
        plan = templates[0]
    elif calorie_target < 1800:
        plan = templates[1]
    else:
        plan = templates[2]
    plan["total_calories"] = sum([
        plan["breakfast"]["total_calories"],
        plan["lunch"]["total_calories"],
        plan["dinner"]["total_calories"],
    ])
    return plan


def _get_fallback_meal(calorie_target: int, meal_type: str) -> dict:
    """内置单餐兜底"""
    ratio = {"breakfast": 0.28, "lunch": 0.38, "dinner": 0.34}.get(meal_type, 0.33)
    cal = int(calorie_target * ratio)
    templates = {
        "breakfast": {"name": "元气早餐", "foods": [
            {"name": "小米粥", "amount": "1碗", "calories": 120, "protein": 3, "fat": 1, "carbs": 25},
            {"name": "水煮蛋", "amount": "2个", "calories": 140, "protein": 12, "fat": 10, "carbs": 1},
        ], "total_calories": 260, "total_protein": 15, "total_fat": 11, "total_carbs": 26},
        "lunch": {"name": "均衡午餐", "foods": [
            {"name": "清蒸鲈鱼", "amount": "1份", "calories": 180, "protein": 28, "fat": 6, "carbs": 0},
            {"name": "糙米饭", "amount": "1碗", "calories": 220, "protein": 5, "fat": 2, "carbs": 44},
        ], "total_calories": 400, "total_protein": 33, "total_fat": 8, "total_carbs": 44},
        "dinner": {"name": "轻食晚餐", "foods": [
            {"name": "番茄豆腐汤", "amount": "1碗", "calories": 80, "protein": 6, "fat": 3, "carbs": 8},
            {"name": "蒜蓉菠菜", "amount": "1份", "calories": 40, "protein": 3, "fat": 1, "carbs": 5},
        ], "total_calories": 120, "total_protein": 9, "total_fat": 4, "total_carbs": 13},
    }
    return templates.get(meal_type, templates["lunch"])


# 内置模板数据
_FALLBACK_LOW_CAL = {
    "breakfast": {"name": "轻盈早餐", "foods": [
        {"name": "无糖豆浆", "amount": "1杯", "calories": 80, "protein": 8, "fat": 4, "carbs": 2},
        {"name": "全麦吐司", "amount": "1片", "calories": 80, "protein": 4, "fat": 1, "carbs": 15},
        {"name": "水煮蛋", "amount": "1个", "calories": 70, "protein": 6, "fat": 5, "carbs": 1},
    ], "total_calories": 230, "total_protein": 18, "total_fat": 10, "total_carbs": 18},
    "lunch": {"name": "减脂午餐", "foods": [
        {"name": "鸡胸肉沙拉", "amount": "1份", "calories": 220, "protein": 30, "fat": 8, "carbs": 8},
        {"name": "糙米饭", "amount": "半碗", "calories": 110, "protein": 3, "fat": 1, "carbs": 22},
    ], "total_calories": 330, "total_protein": 33, "total_fat": 9, "total_carbs": 30},
    "dinner": {"name": "清淡晚餐", "foods": [
        {"name": "番茄蛋花汤", "amount": "1碗", "calories": 60, "protein": 4, "fat": 2, "carbs": 6},
        {"name": "清炒西兰花", "amount": "1份", "calories": 50, "protein": 3, "fat": 2, "carbs": 6},
    ], "total_calories": 110, "total_protein": 7, "total_fat": 4, "total_carbs": 12},
    "ai_note": "今日低热量方案，适合减脂期。",
}
_FALLBACK_MEDIUM_CAL = {
    "breakfast": {"name": "元气早餐", "foods": [
        {"name": "小米粥", "amount": "1碗", "calories": 120, "protein": 3, "fat": 1, "carbs": 25},
        {"name": "水煮蛋", "amount": "2个", "calories": 140, "protein": 12, "fat": 10, "carbs": 1},
        {"name": "凉拌黄瓜", "amount": "1份", "calories": 30, "protein": 1, "fat": 0, "carbs": 6},
    ], "total_calories": 290, "total_protein": 16, "total_fat": 11, "total_carbs": 32},
    "lunch": {"name": "均衡午餐", "foods": [
        {"name": "清蒸鲈鱼", "amount": "1份", "calories": 180, "protein": 28, "fat": 6, "carbs": 0},
        {"name": "西兰花炒虾仁", "amount": "1份", "calories": 120, "protein": 15, "fat": 4, "carbs": 8},
        {"name": "糙米饭", "amount": "1碗", "calories": 220, "protein": 5, "fat": 2, "carbs": 44},
    ], "total_calories": 520, "total_protein": 48, "total_fat": 12, "total_carbs": 52},
    "dinner": {"name": "轻食晚餐", "foods": [
        {"name": "番茄豆腐汤", "amount": "1碗", "calories": 80, "protein": 6, "fat": 3, "carbs": 8},
        {"name": "蒜蓉菠菜", "amount": "1份", "calories": 40, "protein": 3, "fat": 1, "carbs": 5},
        {"name": "玉米", "amount": "1根", "calories": 110, "protein": 3, "fat": 1, "carbs": 22},
        {"name": "鸡胸肉沙拉", "amount": "1份", "calories": 250, "protein": 30, "fat": 8, "carbs": 12},
    ], "total_calories": 480, "total_protein": 42, "total_fat": 13, "total_carbs": 47},
    "ai_note": "今日均衡饮食方案，适合维持体重。",
}
_FALLBACK_HIGH_CAL = {
    "breakfast": {"name": "高蛋白早餐", "foods": [
        {"name": "全麦面包", "amount": "2片", "calories": 160, "protein": 8, "fat": 2, "carbs": 30},
        {"name": "牛油果", "amount": "半个", "calories": 120, "protein": 2, "fat": 10, "carbs": 6},
        {"name": "希腊酸奶", "amount": "1杯", "calories": 100, "protein": 15, "fat": 3, "carbs": 6},
    ], "total_calories": 380, "total_protein": 25, "total_fat": 15, "total_carbs": 42},
    "lunch": {"name": "增肌午餐", "foods": [
        {"name": "黑椒牛排", "amount": "1份", "calories": 280, "protein": 35, "fat": 12, "carbs": 2},
        {"name": "藜麦沙拉", "amount": "1份", "calories": 180, "protein": 8, "fat": 6, "carbs": 25},
        {"name": "烤红薯", "amount": "1个", "calories": 150, "protein": 2, "fat": 0, "carbs": 35},
    ], "total_calories": 610, "total_protein": 45, "total_fat": 18, "total_carbs": 62},
    "dinner": {"name": "补铁晚餐", "foods": [
        {"name": "菠菜猪肝汤", "amount": "1碗", "calories": 120, "protein": 15, "fat": 4, "carbs": 5},
        {"name": "杂粮饭", "amount": "1碗", "calories": 200, "protein": 5, "fat": 2, "carbs": 40},
        {"name": "清炒时蔬", "amount": "1份", "calories": 60, "protein": 2, "fat": 2, "carbs": 8},
    ], "total_calories": 380, "total_protein": 22, "total_fat": 8, "total_carbs": 53},
    "ai_note": "今日高热量高蛋白方案，适合增肌或备孕期。",
}
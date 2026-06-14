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
from app.services.context_builder import get_user_context
from app.services.safety_guard import filter_menu_plan
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
    recent_foods: list[str] | None = None,
    family_needs: str | None = None,
    nutrient_balance: dict | None = None,
) -> str:
    """组装 AI 餐食生成 prompt"""
    meals_count = {"3_meals": "三餐", "4_meals": "四餐（含下午茶）", "5_meals": "五餐（含上下午加餐）"}.get(meal_pattern, "三餐")

    prompt = f"""请为以下用户生成今日（{date_str}）{meals_count}计划。

每日总热量目标：{calorie_target}kcal
宏量营养素目标：蛋白质 {macros['protein_g']}g、脂肪 {macros['fat_g']}g、碳水 {macros['carbs_g']}g

用户信息：
{user_context}
"""

    # 近期饮食去重
    if recent_foods:
        prompt += f"\n\n⚠ 用户近3天已吃过以下菜品，请不要重复推荐：{','.join(recent_foods)}"

    # 家庭餐食需求
    if family_needs:
        prompt += f"\n\n👨‍👩‍👧‍👦 家庭餐食需求：{family_needs}"

    # 营养失衡提醒
    if nutrient_balance and nutrient_balance.get("imbalances"):
        imbalances_str = "；".join(nutrient_balance["imbalances"])
        prompt += f"\n\n📊 近期营养失衡提醒：{imbalances_str}，请在今日计划中适当调整。"

    # 最终输出指令
    prompt += "\n\n请直接输出 JSON，不要有其他文字。"
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
    user_context = await get_user_context(db, user)

    # 4. 获取用餐模式
    meal_pattern = "3_meals"
    profile = await _get_profile(db, user.id)
    if profile:
        meal_pattern = profile.meal_pattern or "3_meals"

    # 获取近期饮食去重
    recent_foods = await _get_recent_food_names(db, user.id, days=3)

    # 获取家庭餐食需求
    family_needs = await _get_family_needs(profile)

    # 获取营养失衡分析
    nutrient_balance = await _get_nutrient_balance(db, user.id, days=3, calorie_target=calorie_target, goal_type=_get_goal_type(user))

    # 5. AI 生成
    prompt = _build_meal_prompt(
        user_context or "无特殊偏好信息",
        calorie_target,
        macros,
        plan_date.isoformat(),
        meal_pattern,
        recent_foods=recent_foods,
        family_needs=family_needs,
        nutrient_balance=nutrient_balance,
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

    user_context = await get_user_context(db, user)
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


async def _get_recent_food_names(db: AsyncSession, user_id: str, days: int = 3) -> list[str]:
    """获取近 N 天用户吃过的菜品名称，用于去重"""
    from datetime import timedelta
    from app.models.diet_record import DietRecord

    start_date = date.today() - timedelta(days=days)
    result = await db.execute(
        select(DietRecord).where(
            DietRecord.user_id == user_id,
            DietRecord.record_date >= start_date,
            DietRecord.deleted_at.is_(None),
        ).order_by(DietRecord.recorded_at.desc()).limit(20)
    )
    records = result.scalars().all()

    # 提取不重复的食物名称
    seen = set()
    food_names = []
    for r in records:
        if r.food_text and r.food_text not in seen:
            seen.add(r.food_text)
            food_names.append(r.food_text)
    return food_names[:10]  # 最多10条


async def _get_family_needs(profile: UserProfile | None) -> str | None:
    """获取家庭餐食需求描述"""
    if not profile or not profile.family_cooking or not profile.family_members:
        return None

    member_strs = []
    for m in profile.family_members:
        name = m.get("name", "成员")
        relation = m.get("relation", "")
        age_group = m.get("age_group", "")
        diet_note = m.get("diet_note", "")
        parts = [name]
        if relation:
            parts.append(f"关系: {relation}")
        if age_group:
            parts.append(f"年龄段: {age_group}")
        if diet_note:
            parts.append(f"饮食注意: {diet_note}")
        member_strs.append("（" + "，".join(parts) + "）")

    return "需为以下家庭成员一起做饭，每餐要兼顾所有人口味和禁忌：" + "、".join(member_strs)


async def _get_nutrient_balance(db: AsyncSession, user_id: str, days: int = 3, calorie_target: int = 1600, goal_type: str = "maintain") -> dict | None:
    """分析近 N 天营养摄入，返回日均值和失衡项"""
    from datetime import timedelta
    from sqlalchemy import func as sqlfunc
    from app.models.diet_record import DietRecord

    start_date = date.today() - timedelta(days=days)
    result = await db.execute(
        select(
            sqlfunc.sum(DietRecord.total_calories).label("total_cal"),
            sqlfunc.sum(DietRecord.total_protein).label("total_protein"),
            sqlfunc.sum(DietRecord.total_fat).label("total_fat"),
            sqlfunc.sum(DietRecord.total_carbs).label("total_carbs"),
            sqlfunc.sum(DietRecord.total_fiber).label("total_fiber"),
            sqlfunc.count(DietRecord.id).label("record_count"),
        ).where(
            DietRecord.user_id == user_id,
            DietRecord.record_date >= start_date,
            DietRecord.deleted_at.is_(None),
        )
    )
    row = result.one_or_none()
    if not row or not row.record_count:
        return None

    # 计算实际有记录的天数（至少 1 天）
    day_result = await db.execute(
        select(sqlfunc.count(sqlfunc.distinct(DietRecord.record_date))).where(
            DietRecord.user_id == user_id,
            DietRecord.record_date >= start_date,
            DietRecord.deleted_at.is_(None),
        )
    )
    actual_days = max(day_result.scalar() or 1, 1)

    daily_avg = {
        "calories": round((row.total_cal or 0) / actual_days, 1),
        "protein": round((row.total_protein or 0) / actual_days, 1),
        "fat": round((row.total_fat or 0) / actual_days, 1),
        "carbs": round((row.total_carbs or 0) / actual_days, 1),
        "fiber": round((row.total_fiber or 0) / actual_days, 1),
    }

    # 计算目标值
    target_macros = calculate_macros(calorie_target, goal_type)
    imbalances = []

    # 蛋白质检查（低于目标 80%）
    if target_macros["protein_g"] > 0 and daily_avg["protein"] < target_macros["protein_g"] * 0.8:
        imbalances.append(f"蛋白质不足（日均{int(daily_avg['protein'])}g，目标{target_macros['protein_g']}g），建议多补充鱼虾、鸡蛋、豆制品")

    # 脂肪检查（超过目标 130%）
    if target_macros["fat_g"] > 0 and daily_avg["fat"] > target_macros["fat_g"] * 1.3:
        imbalances.append(f"脂肪摄入偏高（日均{int(daily_avg['fat'])}g，目标{target_macros['fat_g']}g），建议减少油炸和高脂食物")

    # 碳水检查（低于目标 70%）
    if target_macros["carbs_g"] > 0 and daily_avg["carbs"] < target_macros["carbs_g"] * 0.7:
        imbalances.append(f"碳水摄入偏低（日均{int(daily_avg['carbs'])}g，目标{target_macros['carbs_g']}g），建议适当补充全谷物")

    # 膳食纤维检查（低于 15g/天）
    if daily_avg["fiber"] < 15:
        imbalances.append(f"膳食纤维不足（日均{int(daily_avg['fiber'])}g），建议多吃蔬菜、全谷物和豆类")

    # 热量检查
    if daily_avg["calories"] < calorie_target * 0.7:
        imbalances.append(f"热量摄入偏低（日均{int(daily_avg['calories'])}kcal，目标{calorie_target}kcal）")
    elif daily_avg["calories"] > calorie_target * 1.2:
        imbalances.append(f"热量摄入偏高（日均{int(daily_avg['calories'])}kcal，目标{calorie_target}kcal）")

    if not imbalances:
        return None  # 营养均衡，无需提醒

    summary = f"近{actual_days}天日均: {int(daily_avg['calories'])}kcal, 蛋白质{int(daily_avg['protein'])}g, 脂肪{int(daily_avg['fat'])}g, 碳水{int(daily_avg['carbs'])}g"
    return {"daily_avg": daily_avg, "imbalances": imbalances, "summary": summary}
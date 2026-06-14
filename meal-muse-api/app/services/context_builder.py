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
from app.models.body_metric import BodyMetric
from app.models.family import Family, FamilyMember
from app.models.exercise_record import ExerciseRecord

# ——— 模块级常量 ———

CONSTITUTION_LABELS = {
    "yang_deficiency": "阳虚质(怕冷/手脚凉)",
    "yin_deficiency": "阴虚质(口干/易上火)",
    "qi_deficiency": "气虚质(乏力/气短)",
    "blood_stasis": "血瘀质(皮肤暗沉/易瘀青)",
    "phlegm_dampness": "痰湿质(体胖/痰多)",
    "damp_heat": "湿热质(面垢油光/口苦)",
    "qi_stagnation": "气郁质(情绪低落/胸闷)",
    "special_diathesis": "特禀质(过敏体质)",
    "neutral": "平和质(正常)",
}

CONSTITUTION_FOOD_MAP = {
    "yang_deficiency": "宜温补(羊肉/生姜/桂圆)，忌寒凉(西瓜/冷饮/苦瓜)",
    "yin_deficiency": "宜滋阴(银耳/百合/枸杞)，忌燥热(辣椒/羊肉/酒)",
    "qi_deficiency": "宜补气(黄芪/山药/鸡肉)，忌耗气(萝卜/薄荷)",
    "phlegm_dampness": "宜化湿(薏仁/冬瓜/白萝卜)，忌甜腻肥厚",
    "damp_heat": "宜清热(绿豆/苦瓜/薏仁)，忌辛温滋腻",
    "blood_stasis": "宜活血(山楂/黑木耳/洋葱)",
    "qi_stagnation": "宜疏肝(玫瑰花/柑橘/萝卜)",
}

SUB_GOAL_LABELS = {
    "rapid_loss": "速减", "slow_loss": "慢减", "body_shape": "塑形",
    "pregnancy_preparing": "备孕中", "early_pregnancy": "孕早期",
    "mid_pregnancy": "孕中期", "late_pregnancy": "孕晚期", "breastfeeding": "哺乳期",
    "qi_blood": "气血不足", "spleen_stomach": "脾胃调理", "kidney": "补肾",
    "liver": "护肝", "sleep": "安神助眠",
    "muscle_gain": "增肌", "body_recomp": "减脂塑形", "recovery": "运动恢复",
    "diabetes": "糖尿病管理", "hypertension": "高血压管理", "hyperlipidemia": "高血脂管理",
    "gout": "痛风管理", "stomach": "胃病管理",
}

FREQ_LABELS = {"often": "天天做", "sometimes": "3-5次/周", "rarely": "偶尔", "never": "从不"}
TAKEOUT_LABELS = {"healthy_light": "营养轻食", "home_style": "家常菜", "fast_food": "快餐", "any": "都行"}


async def get_user_context(db: AsyncSession, user: User) -> str:
    """
    构建完整的用户上下文，供 AI 使用。
    包含：基础信息、健康目标、画像偏好、疾病禁忌、过敏原、
    经期阶段、身体指标、近期饮食、近期运动。
    """
    parts: list[str] = [f"用户信息：\n- 昵称：{user.nickname}"]

    # 基础信息
    if user.age:
        parts.append(f"- 年龄：{user.age}岁")
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
        if profile.cooking_method:
            cooking_labels = {"simple": "简单烹饪", "medium": "中等厨艺", "advanced": "高级厨艺"}
            info.append(f"烹饪技能：{cooking_labels.get(profile.cooking_method, profile.cooking_method)}")
        if profile.meal_prep_time:
            prep_labels = {"none": "没时间做饭", "15min": "15分钟以内", "30min": "30分钟左右", "60min+": "1小时以上"}
            info.append(f"备餐时间：{prep_labels.get(profile.meal_prep_time, profile.meal_prep_time)}")
        if profile.meal_pattern:
            info.append(f"就餐模式：{profile.meal_pattern.replace('_', ' 餐 ')}")
        if profile.budget_level:
            budget_labels = {"low": "经济实惠", "medium": "适中", "high": "不限预算"}
            info.append(f"预算水平：{budget_labels.get(profile.budget_level, profile.budget_level)}")
        if profile.water_intake_goal:
            info.append(f"每日饮水目标：{profile.water_intake_goal}ml")

        # 新增: 体质辨识
        if profile.constitution_types:
            types_str = "、".join(CONSTITUTION_LABELS.get(t, t) for t in profile.constitution_types)
            info.append(f"体质：{types_str}")

            # 体质饮食建议
            diet_advice = [CONSTITUTION_FOOD_MAP[t] for t in profile.constitution_types if t in CONSTITUTION_FOOD_MAP]
            if diet_advice:
                info.append("体质饮食建议：" + "；".join(diet_advice))

        # 新增: 子目标
        if profile.health_sub_goals:
            sub_str = "、".join(SUB_GOAL_LABELS.get(s, s) for s in profile.health_sub_goals)
            info.append(f"细分目标：{sub_str}")

        # 新增: 偏好食材
        if profile.preferred_ingredients:
            info.append(f"偏好食材：{'、'.join(profile.preferred_ingredients)}")

        # 新增: 做饭频次
        if profile.cooking_frequency:
            info.append(f"做饭频次：{FREQ_LABELS.get(profile.cooking_frequency, profile.cooking_frequency)}")

        # 新增: 外卖偏好
        if profile.takeout_preference and profile.takeout_preference != "any":
            info.append(f"外卖偏好：{TAKEOUT_LABELS.get(profile.takeout_preference, profile.takeout_preference)}")

        # 新增: 家庭做饭
        if profile.family_cooking and profile.family_members:
            member_strs = []
            for m in profile.family_members:
                name = m.get("name", "成员")
                relation = m.get("relation", "")
                diet_note = m.get("diet_note", "")
                member_strs.append(f"{name}({relation}{('，' + diet_note) if diet_note else ''})")
            info.append(f"为家人做饭：{'、'.join(member_strs)}")

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

    # 身体指标
    body_metrics = await _get_body_metrics(db, user.id)
    if body_metrics:
        parts.append(f"- 身体指标：{body_metrics}")

    # 家庭信息
    family_context = await _get_family_context(db, user.id)
    if family_context:
        parts.append(f"- 家庭信息：{family_context}")

    # 近期饮食记录
    diet_summary = await _get_diet_summary(db, user.id)
    if diet_summary:
        parts.append(diet_summary)

    # 近期运动记录
    exercise_summary = await _get_exercise_summary(db, user.id)
    if exercise_summary:
        parts.append(exercise_summary)

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


async def get_profile_summary(db: AsyncSession, user: User) -> str:
    """
    生成 100-150 字的紧凑画像摘要，供对话/餐食计划注入。
    比 get_user_context 轻量，跳过身体指标、运动、经期等重查询。
    """
    profile = await _get_profile(db, user.id)
    if not profile:
        return ""

    segs: list[str] = []

    # 基础：性别+年龄
    gender = "女" if user.gender == "female" else "男" if user.gender == "male" else ""
    age_str = f"{user.age}岁" if user.age else ""
    if gender or age_str:
        segs.append(f"{gender}{age_str}")

    # 体质
    if profile.constitution_types:
        types_short = "、".join(CONSTITUTION_LABELS.get(t, t).split("(")[0] for t in profile.constitution_types)
        segs.append(types_short + "体质")

    # 子目标
    goal = await _get_active_goal(db, user.id)
    if profile.health_sub_goals:
        sub_str = "、".join(SUB_GOAL_LABELS.get(s, s) for s in profile.health_sub_goals[:3])
        segs.append(sub_str)

    # 饮食偏好
    diet_parts = []
    if profile.cuisine_preference:
        diet_parts.append(f"偏好{'、'.join(profile.cuisine_preference[:2])}菜")
    if profile.disliked_foods:
        diet_parts.append(f"忌{'、'.join(profile.disliked_foods[:3])}")
    if profile.diet_type and profile.diet_type != "normal":
        diet_parts.append(f"{profile.diet_type}饮食")
    segs.append("，".join(diet_parts) if diet_parts else "")

    # 烹饪
    if profile.family_cooking and profile.family_members:
        n = len(profile.family_members)
        notes = []
        for m in profile.family_members[:2]:
            note = m.get("diet_note", "")
            if note and note != "无特殊":
                notes.append(f"{m.get('name', '家人')}{note}")
        family_desc = f"为{n + 1}口人做饭"
        if notes:
            family_desc += f"({','.join(notes)})"
        segs.append(family_desc)

    # 过敏
    allergies = await _get_allergies(db, user.id)
    if allergies:
        allergy_str = "、".join(
            (a.custom_name if a.allergen == "custom" else a.allergen) for a in allergies[:4]
        )
        segs.append(f"忌{allergy_str}")

    # 健康情况
    conditions = await _get_health_conditions(db, user.id)
    if conditions:
        cond_str = "、".join(c.condition_type for c in conditions[:2])
        segs.append(cond_str)

    summary = "，".join(s for s in segs if s)
    # 截断到 150 字
    if len(summary) > 150:
        summary = summary[:147] + "..."
    return summary


async def get_cached_profile_summary(db: AsyncSession, user: User) -> str:
    """带 Redis 缓存的画像摘要，TTL 24h"""
    from app.core.cache import cache_get, cache_set

    cache_key = f"profile_summary:{user.id}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    summary = await get_profile_summary(db, user)
    if summary:
        await cache_set(cache_key, summary)
    return summary


async def _get_body_metrics(db: AsyncSession, user_id: str) -> str | None:
    """获取近 7 天身体指标趋势"""
    week_ago = date.today() - timedelta(days=7)
    result = await db.execute(
        select(BodyMetric).where(
            BodyMetric.user_id == user_id,
            BodyMetric.metric_date >= week_ago,
            BodyMetric.deleted_at.is_(None),
        ).order_by(BodyMetric.metric_date.desc()).limit(7)
    )
    metrics = result.scalars().all()
    if not metrics:
        return None

    latest = metrics[0]
    parts = []
    if latest.weight:
        # 计算趋势
        if len(metrics) >= 2:
            oldest = metrics[-1]
            diff = latest.weight - oldest.weight
            if abs(diff) < 0.5:
                trend = "稳定"
            elif diff > 0:
                trend = f"上升{diff:.1f}kg"
            else:
                trend = f"下降{abs(diff):.1f}kg"
            parts.append(f"体重{latest.weight}kg（近7天{trend}）")
        else:
            parts.append(f"体重{latest.weight}kg")
    if latest.bmi:
        parts.append(f"BMI {latest.bmi}")
    if latest.body_fat_pct:
        parts.append(f"体脂率{latest.body_fat_pct}%")
    if latest.sleep_hours:
        parts.append(f"日均睡眠{latest.sleep_hours}h")
    if latest.blood_pressure_sys and latest.blood_pressure_dia:
        parts.append(f"血压{latest.blood_pressure_sys}/{latest.blood_pressure_dia}mmHg")

    return "、".join(parts) if parts else None


async def _get_family_context(db: AsyncSession, user_id: str) -> str | None:
    """获取用户所在家庭及成员信息"""
    result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.user_id == user_id,
            FamilyMember.status == "active",
        )
    )
    my_membership = result.scalar_one_or_none()
    if not my_membership:
        return None

    family_result = await db.execute(
        select(Family).where(Family.id == my_membership.family_id)
    )
    family = family_result.scalar_one_or_none()
    if not family:
        return None

    members_result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.family_id == family.id,
            FamilyMember.status == "active",
        )
    )
    members = members_result.scalars().all()

    member_descs = []
    for m in members:
        if m.user_id == user_id:
            continue  # 跳过本人
        user_result = await db.execute(
            select(User).where(User.id == m.user_id, User.deleted_at.is_(None))
        )
        member_user = user_result.scalar_one_or_none()
        if not member_user:
            continue
        name = m.display_name or member_user.nickname or f"用户{str(member_user.id)[:8]}"
        role = m.relation or m.role
        permissions = []
        if m.can_view_diet:
            permissions.append("可看饮食")
        if m.can_view_body:
            permissions.append("可看身体数据")
        perm_str = f"（{'、'.join(permissions)}）" if permissions else ""
        member_descs.append(f"{name}（{role}）{perm_str}")

    if not member_descs:
        return None

    family_name = family.name or "未命名家庭"
    return f"用户属于\"{family_name}\"，家庭成员：{'、'.join(member_descs)}"


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


async def _get_exercise_summary(db: AsyncSession, user_id: str) -> str | None:
    """获取近期运动总结"""
    week_ago = date.today() - timedelta(days=7)

    result = await db.execute(
        select(ExerciseRecord).where(
            ExerciseRecord.user_id == user_id,
            ExerciseRecord.exercise_date >= week_ago,
            ExerciseRecord.deleted_at.is_(None),
        ).order_by(desc(ExerciseRecord.exercise_date)).limit(10)
    )
    records = result.scalars().all()
    if not records:
        return None

    total_cal = sum(r.calories_burned or 0 for r in records)
    total_min = sum(r.duration_min or 0 for r in records)
    exercise_types = list(dict.fromkeys(r.exercise_type for r in records))[:3]

    return (
        f"- 近7天运动：{len(records)}次，共{total_min}分钟，消耗约{int(total_cal)}kcal\n"
        f"- 运动类型：{'、'.join(exercise_types)}"
    )

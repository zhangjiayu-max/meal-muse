"""用户 API"""
from uuid import UUID
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.cache import cache_delete
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.allergy_tag import AllergyTag
from app.models.health_goal import HealthGoal
from app.models.health_condition import HealthCondition
from app.schemas.user import (
    UserResponse, UserUpdate, UserProfileResponse, UserProfileUpdate,
    HealthGoalResponse, HealthGoalUpdate, AllergyResponse, AllergyCreate,
    HealthConditionResponse, HealthConditionCreate, FullProfileResponse, FullProfileUpdate,
)

router = APIRouter(prefix="/users", tags=["用户"])


# --- Onboarding Schema ---

class OnboardingRequest(BaseModel):
    """Onboarding 一次性提交请求体"""
    height_cm: float = Field(..., ge=50, le=300, description="身高（厘米）")
    weight_kg: float = Field(..., ge=10, le=500, description="体重（千克）")
    age: int = Field(..., ge=1, le=150, description="年龄")
    gender: str = Field(..., pattern="^(male|female)$", description="性别：male/female")
    goals: list[str] = Field(..., min_length=1, description="如 ['weight_loss', 'fertility']")
    target_weight: float | None = Field(default=None, ge=10, le=500, description="目标体重")
    diet_type: str = Field(default="normal", description="normal/vegetarian/low_carb/keto")
    taste_pref: list[str] = Field(default=[], description="口味偏好，如 ['light', 'spicy']")
    cuisine_pref: list[str] = Field(default=[], description="偏好菜系，如 ['川菜', '粤菜']")
    allergies: list[str] = Field(default=[], description="过敏原列表")
    disliked_foods: list[str] = Field(default=[], description="忌口食物")
    cooking_method: str = Field(default="simple", description="simple/medium/advanced")
    cooking_facility: str = Field(default="full_kitchen", description="full_kitchen/no_kitchen")
    meal_prep_time: str = Field(default="30min", description="none/15min/30min/60min+")
    meal_pattern: str = Field(default="3_meals", description="3_meals/4_meals/5_meals")
    sleep_pattern: str = Field(default="early_bird", description="early_bird/night_owl")
    budget_level: str = Field(default="medium", description="low/medium/high")
    water_intake_goal: int | None = Field(default=None, description="每日饮水目标(ml)")
    constitution_types: list[str] = Field(default=[], description="体质类型")
    health_sub_goals: list[str] = Field(default=[], description="子目标，如 ['pregnancy_preparing']")
    preferred_ingredients: list[str] = Field(default=[], description="偏好食材")
    cooking_frequency: str = Field(default="often", description="often/sometimes/rarely/never")
    takeout_preference: str = Field(default="any", description="healthy_light/home_style/fast_food/any")
    family_cooking: bool = Field(default=False, description="是否为家人做饭")
    family_members: list[dict] = Field(default=[], description="家庭成员列表")


class OnboardingResponse(BaseModel):
    """Onboarding 响应体"""
    user_id: UUID
    daily_calorie_target: int
    message: str


# --- 路由 ---

@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """获取当前用户资料"""
    return UserResponse.model_validate(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    req: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新用户资料"""
    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)
    await db.commit()
    await db.refresh(current_user)
    await cache_delete(f"profile_summary:{current_user.id}")
    return UserResponse.model_validate(current_user)


@router.post("/onboarding", response_model=OnboardingResponse)
async def onboarding(
    req: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Onboarding: 一次性提交身体数据 + 健康目标 + 饮食偏好"""
    # 1. 更新 users 表身体数据
    current_user.height_cm = req.height_cm
    current_user.current_weight = req.weight_kg
    current_user.gender = req.gender
    current_user.age = req.age
    if req.target_weight:
        current_user.target_weight = req.target_weight

    # 2. 计算 daily_calorie_target（Mifflin-St Jeor 公式）
    if req.gender == "male":
        bmr = 10 * req.weight_kg + 6.25 * req.height_cm - 5 * req.age + 5
    else:
        bmr = 10 * req.weight_kg + 6.25 * req.height_cm - 5 * req.age - 161

    activity_factor = 1.55  # 中等活动量
    goal_factor = 0.85 if "weight_loss" in req.goals else 1.0
    daily_calorie_target = int(bmr * activity_factor * goal_factor)
    current_user.daily_calorie_target = daily_calorie_target

    # 3. 创建/更新 user_profiles
    try:
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == current_user.id)
        )
        profile = result.scalar_one_or_none()
        if profile:
            profile.diet_type = req.diet_type
            profile.taste_preference = ",".join(req.taste_pref) if req.taste_pref else "mild"
            profile.cuisine_preference = req.cuisine_pref if req.cuisine_pref else None
            profile.disliked_foods = req.disliked_foods if req.disliked_foods else None
            profile.cooking_method = req.cooking_method
            profile.cooking_facility = req.cooking_facility
            profile.meal_prep_time = req.meal_prep_time
            profile.meal_pattern = req.meal_pattern
            profile.sleep_pattern = req.sleep_pattern
            profile.budget_level = req.budget_level
            profile.water_intake_goal = req.water_intake_goal
            profile.constitution_types = req.constitution_types
            profile.health_sub_goals = req.health_sub_goals
            profile.preferred_ingredients = req.preferred_ingredients
            profile.cooking_frequency = req.cooking_frequency
            profile.takeout_preference = req.takeout_preference
            profile.family_cooking = req.family_cooking
            profile.family_members = req.family_members
            profile.onboarding_version = 2
        else:
            profile = UserProfile(
                user_id=current_user.id,
                diet_type=req.diet_type,
                taste_preference=",".join(req.taste_pref) if req.taste_pref else "mild",
                cuisine_preference=req.cuisine_pref if req.cuisine_pref else None,
                disliked_foods=req.disliked_foods if req.disliked_foods else None,
                cooking_method=req.cooking_method,
                cooking_facility=req.cooking_facility,
                meal_prep_time=req.meal_prep_time,
                meal_pattern=req.meal_pattern,
                sleep_pattern=req.sleep_pattern,
                budget_level=req.budget_level,
                water_intake_goal=req.water_intake_goal,
                constitution_types=req.constitution_types,
                health_sub_goals=req.health_sub_goals,
                preferred_ingredients=req.preferred_ingredients,
                cooking_frequency=req.cooking_frequency,
                takeout_preference=req.takeout_preference,
                family_cooking=req.family_cooking,
                family_members=req.family_members,
                onboarding_version=2,
            )
            db.add(profile)
    except Exception:
        pass  # UserProfile 表不存在时跳过

    # 4. 更新过敏原
    try:
        old_allergies = await db.execute(
            select(AllergyTag).where(AllergyTag.user_id == current_user.id)
        )
        for old in old_allergies.scalars().all():
            await db.delete(old)
        for allergen in req.allergies:
            tag = AllergyTag(user_id=current_user.id, allergen=allergen)
            db.add(tag)
    except Exception:
        pass  # AllergyTag 表不存在时跳过

    # 5. 创建健康目标
    try:
        for goal_type in req.goals:
            goal = HealthGoal(
                user_id=current_user.id,
                goal_type=goal_type,
                target_weight=req.target_weight,
                daily_calorie_target=daily_calorie_target,
                status="active",
            )
            db.add(goal)
    except Exception:
        pass  # HealthGoal 表不存在时跳过

    await db.commit()
    await db.refresh(current_user)
    await cache_delete(f"profile_summary:{current_user.id}")

    return OnboardingResponse(
        user_id=current_user.id,
        daily_calorie_target=daily_calorie_target,
        message="Onboarding 完成，已为你生成个性化方案",
    )


# --- 画像配置选项 ---

@router.get("/profile/options")
async def get_profile_options():
    """返回前端需要的所有选项枚举"""
    return {
        "diet_types": [
            {"key": "normal", "label": "普通饮食"},
            {"key": "vegetarian", "label": "素食"},
            {"key": "vegan", "label": "纯素"},
            {"key": "keto", "label": "生酮饮食"},
            {"key": "lowcarb", "label": "低碳水"},
            {"key": "mediterranean", "label": "地中海饮食"},
        ],
        "taste_preferences": [
            {"key": "mild", "label": "清淡"},
            {"key": "spicy_heavy", "label": "辣味"},
            {"key": "sweet", "label": "甜味"},
            {"key": "salty", "label": "咸香"},
        ],
        "cuisine_options": [
            "川菜", "粤菜", "湘菜", "鲁菜", "苏菜", "浙菜", "闽菜", "徽菜",
            "日料", "韩餐", "西餐", "东南亚菜", "东北菜", "西北菜",
        ],
        "allergy_options": [
            {"key": "seafood", "label": "海鲜"},
            {"key": "peanut", "label": "花生"},
            {"key": "dairy", "label": "乳制品"},
            {"key": "egg", "label": "鸡蛋"},
            {"key": "gluten", "label": "麸质"},
            {"key": "soy", "label": "大豆"},
            {"key": "nut", "label": "坚果"},
            {"key": "shellfish", "label": "贝类"},
            {"key": "sulfite", "label": "亚硫酸盐"},
            {"key": "custom", "label": "其他"},
        ],
        "health_goal_types": [
            {"key": "weight_loss", "label": "减脂减重", "emoji": "🔥"},
            {"key": "muscle_gain", "label": "增肌塑形", "emoji": "💪"},
            {"key": "health", "label": "养生保健", "emoji": "🧘"},
            {"key": "pregnancy", "label": "备孕调理", "emoji": "🌸"},
            {"key": "custom", "label": "自定义目标", "emoji": "🎯"},
        ],
        "health_condition_types": [
            {"key": "diabetes", "label": "糖尿病"},
            {"key": "hypertension", "label": "高血压"},
            {"key": "hyperlipidemia", "label": "高血脂"},
            {"key": "gout", "label": "痛风"},
            {"key": "ulcer", "label": "胃溃疡"},
            {"key": "kidney", "label": "肾脏疾病"},
        ],
        "cooking_methods": [
            {"key": "simple", "label": "简单（煮/微波）"},
            {"key": "medium", "label": "中等（炒/煎）"},
            {"key": "advanced", "label": "高级（烘焙/慢炖）"},
        ],
        "cooking_facilities": [
            {"key": "full_kitchen", "label": "完整厨房"},
            {"key": "no_kitchen", "label": "无厨房（外卖/即食）"},
        ],
        "meal_prep_times": [
            {"key": "none", "label": "没时间做饭"},
            {"key": "15min", "label": "15 分钟以内"},
            {"key": "30min", "label": "30 分钟左右"},
            {"key": "60min+", "label": "1 小时以上"},
        ],
        "meal_patterns": [
            {"key": "3_meals", "label": "一日三餐"},
            {"key": "4_meals", "label": "一日四餐（含加餐）"},
            {"key": "5_meals", "label": "少食多餐"},
        ],
        "sleep_patterns": [
            {"key": "early_bird", "label": "早睡早起"},
            {"key": "night_owl", "label": "晚睡晚起"},
        ],
        "budget_levels": [
            {"key": "low", "label": "经济实惠"},
            {"key": "medium", "label": "适中"},
            {"key": "high", "label": "不限预算"},
        ],
        "activity_levels": [
            {"key": "sedentary", "label": "久坐不动"},
            {"key": "light", "label": "轻度活动"},
            {"key": "moderate", "label": "中等活动"},
            {"key": "active", "label": "高度活动"},
            {"key": "very_active", "label": "极高活动"},
        ],
    }


# --- 完整画像 API ---

@router.get("/profile/full", response_model=FullProfileResponse)
async def get_full_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取完整用户画像（User + Profile + Goals + Allergies + Conditions）"""
    # 用户画像
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()

    # 健康目标
    goals_result = await db.execute(
        select(HealthGoal).where(
            HealthGoal.user_id == current_user.id,
            HealthGoal.status == "active",
        )
    )
    goals = goals_result.scalars().all()

    # 过敏原
    allergies_result = await db.execute(
        select(AllergyTag).where(AllergyTag.user_id == current_user.id)
    )
    allergies = allergies_result.scalars().all()

    # 健康疾病
    conditions_result = await db.execute(
        select(HealthCondition).where(HealthCondition.user_id == current_user.id)
    )
    conditions = conditions_result.scalars().all()

    return FullProfileResponse(
        user=UserResponse.model_validate(current_user),
        profile=UserProfileResponse.model_validate(profile) if profile else None,
        health_goals=[HealthGoalResponse.model_validate(g) for g in goals],
        allergies=[AllergyResponse.model_validate(a) for a in allergies],
        health_conditions=[HealthConditionResponse.model_validate(c) for c in conditions],
    )


@router.put("/profile/full", response_model=FullProfileResponse)
async def update_full_profile(
    req: FullProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """一次性更新完整用户画像"""
    # 1. 更新 User 基础信息
    if req.user:
        user_data = req.user.model_dump(exclude_unset=True)
        for key, value in user_data.items():
            setattr(current_user, key, value)

    # 2. 更新 UserProfile
    if req.profile:
        profile_data = req.profile.model_dump(exclude_unset=True)
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == current_user.id)
        )
        profile = result.scalar_one_or_none()
        if profile:
            for key, value in profile_data.items():
                setattr(profile, key, value)
        else:
            profile = UserProfile(user_id=current_user.id, **profile_data)
            db.add(profile)

    # 3. 更新健康目标（替换模式）
    if req.health_goals is not None:
        # 删除旧目标
        old_goals = await db.execute(
            select(HealthGoal).where(HealthGoal.user_id == current_user.id)
        )
        for old in old_goals.scalars().all():
            await db.delete(old)
        # 创建新目标
        for goal_data in req.health_goals:
            goal = HealthGoal(
                user_id=current_user.id,
                **goal_data.model_dump(exclude_unset=True),
                status="active",
            )
            db.add(goal)

    # 4. 更新过敏原（替换模式）
    if req.allergies is not None:
        old_allergies = await db.execute(
            select(AllergyTag).where(AllergyTag.user_id == current_user.id)
        )
        for old in old_allergies.scalars().all():
            await db.delete(old)
        for allergy_data in req.allergies:
            tag = AllergyTag(user_id=current_user.id, **allergy_data.model_dump())
            db.add(tag)

    # 5. 更新健康疾病（替换模式）
    if req.health_conditions is not None:
        old_conditions = await db.execute(
            select(HealthCondition).where(HealthCondition.user_id == current_user.id)
        )
        for old in old_conditions.scalars().all():
            await db.delete(old)
        for condition_data in req.health_conditions:
            condition = HealthCondition(user_id=current_user.id, **condition_data.model_dump())
            db.add(condition)

    await db.commit()
    await db.refresh(current_user)
    await cache_delete(f"profile_summary:{current_user.id}")

    # 重新查询完整数据返回
    return await get_full_profile(current_user, db)


@router.get("/profile/completeness")
async def get_profile_completeness(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户画像完整度评分"""
    # 基础信息 30%
    base_fields = {
        'nickname': current_user.nickname and current_user.nickname != "用户",
        'gender': bool(current_user.gender),
        'age': bool(current_user.age),
        'height_cm': bool(current_user.height_cm),
        'current_weight': bool(current_user.current_weight),
    }
    base_filled = sum(1 for v in base_fields.values() if v)
    base_score = int((base_filled / len(base_fields)) * 30)
    missing = [k for k, v in base_fields.items() if not v]

    # 健康目标 20%
    goals_result = await db.execute(
        select(HealthGoal).where(HealthGoal.user_id == current_user.id, HealthGoal.status == "active")
    )
    goals = goals_result.scalars().all()
    goal_score = 20 if goals else 0
    if not goals:
        missing.append("goals")

    # 饮食偏好 30%
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    diet_score = 0
    if profile:
        diet_attrs = [
            profile.diet_type and profile.diet_type != "normal",
            profile.taste_preference and profile.taste_preference != "mild",
            profile.cuisine_preference and len(profile.cuisine_preference or []) > 0,
            profile.disliked_foods and len(profile.disliked_foods or []) > 0,
            profile.constitution_types and len(profile.constitution_types or []) > 0,
            profile.preferred_ingredients and len(profile.preferred_ingredients or []) > 0,
        ]
        diet_filled = sum(1 for v in diet_attrs if v)
        diet_score = min(30, int((diet_filled / 2) * 30))

    # 烹饪条件 10%
    cook_score = 0
    if profile:
        cook_attrs = [
            profile.cooking_method is not None,
            profile.cooking_facility is not None,
            profile.meal_prep_time is not None,
        ]
        cook_filled = sum(1 for v in cook_attrs if v)
        cook_score = min(10, int((cook_filled / 2) * 10))

    # 生活方式 10%
    life_score = 0
    if profile:
        life_attrs = [
            profile.sleep_pattern is not None,
            profile.budget_level is not None,
        ]
        life_filled = sum(1 for v in life_attrs if v)
        life_score = min(10, int((life_filled / 2) * 10))

    total = min(100, base_score + goal_score + diet_score + cook_score + life_score)

    if total < 60:
        hint = "画像不完整，AI 建议可能不够精准"
    elif total < 80:
        hint = "画像基本完整，完善更多让推荐更精准"
    else:
        hint = "画像很完整，AI 正在提供最佳建议"

    return {"score": total, "missing": missing, "hint": hint}

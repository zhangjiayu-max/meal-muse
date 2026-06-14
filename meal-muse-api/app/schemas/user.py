from pydantic import BaseModel, Field
from datetime import datetime, date
from uuid import UUID


class UserRegister(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    nickname: str = Field(default="用户", max_length=50)


class UserLogin(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    code: str = Field(..., min_length=4, max_length=6, description="验证码")


class SendCodeRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")


class UserUpdate(BaseModel):
    nickname: str | None = None
    gender: str | None = None
    age: int | None = None
    birthday: date | None = None
    height_cm: float | None = None
    current_weight: float | None = None
    target_weight: float | None = None
    activity_level: str | None = None
    preferences: dict | None = None


class UserResponse(BaseModel):
    id: UUID
    phone: str | None
    nickname: str
    avatar_url: str | None
    gender: str | None
    age: int | None
    birthday: date | None
    height_cm: float | None
    current_weight: float | None
    target_weight: float | None
    activity_level: str
    preferences: dict | None
    daily_calorie_target: int | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """用户画像子表响应"""
    taste_preference: str = "mild"
    diet_type: str = "normal"
    cuisine_preference: list[str] | None = None
    disliked_foods: list[str] | None = None
    cooking_method: str = "simple"
    cooking_facility: str = "full_kitchen"
    meal_pattern: str = "3_meals"
    sleep_pattern: str = "early_bird"
    care_targets: list[str] | None = None
    budget_level: str = "medium"
    meal_prep_time: str = "30min"
    water_intake_goal: int | None = None
    constitution_types: list[str] | None = None
    health_sub_goals: list[str] | None = None
    preferred_ingredients: list[str] | None = None
    cooking_frequency: str = "often"
    takeout_preference: str = "any"
    family_cooking: bool = False
    family_members: list[dict] | None = None
    onboarding_version: int = 2

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """用户画像更新请求"""
    taste_preference: str | None = None
    diet_type: str | None = None
    cuisine_preference: list[str] | None = None
    disliked_foods: list[str] | None = None
    cooking_method: str | None = None
    cooking_facility: str | None = None
    meal_pattern: str | None = None
    sleep_pattern: str | None = None
    care_targets: list[str] | None = None
    budget_level: str | None = None
    meal_prep_time: str | None = None
    water_intake_goal: int | None = None
    constitution_types: list[str] | None = None
    health_sub_goals: list[str] | None = None
    preferred_ingredients: list[str] | None = None
    cooking_frequency: str | None = None
    takeout_preference: str | None = None
    family_cooking: bool | None = None
    family_members: list[dict] | None = None


class HealthGoalResponse(BaseModel):
    """健康目标响应"""
    id: UUID
    goal_type: str
    target_weight: float | None = None
    target_date: date | None = None
    daily_calorie_target: int | None = None
    macro_targets: dict | None = None
    special_notes: str | None = None
    status: str = "active"

    class Config:
        from_attributes = True


class HealthGoalUpdate(BaseModel):
    """健康目标更新请求"""
    goal_type: str | None = None
    target_weight: float | None = None
    target_date: date | None = None
    daily_calorie_target: int | None = None
    macro_targets: dict | None = None
    special_notes: str | None = None


class AllergyResponse(BaseModel):
    """过敏原响应"""
    id: UUID
    allergen: str
    custom_name: str | None = None
    reaction_level: str = "mild"

    class Config:
        from_attributes = True


class AllergyCreate(BaseModel):
    """过敏原创建请求"""
    allergen: str
    custom_name: str | None = None
    reaction_level: str = "mild"


class HealthConditionResponse(BaseModel):
    """健康疾病响应"""
    id: UUID
    condition_type: str
    severity: str = "mild"
    diagnosed_date: date | None = None

    class Config:
        from_attributes = True


class HealthConditionCreate(BaseModel):
    """健康疾病创建请求"""
    condition_type: str
    severity: str = "mild"
    diagnosed_date: date | None = None


class FullProfileResponse(BaseModel):
    """完整用户画像响应"""
    user: UserResponse
    profile: UserProfileResponse | None = None
    health_goals: list[HealthGoalResponse] = []
    allergies: list[AllergyResponse] = []
    health_conditions: list[HealthConditionResponse] = []


class FullProfileUpdate(BaseModel):
    """完整用户画像更新请求"""
    user: UserUpdate | None = None
    profile: UserProfileUpdate | None = None
    health_goals: list[HealthGoalUpdate] | None = None
    allergies: list[AllergyCreate] | None = None
    health_conditions: list[HealthConditionCreate] | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

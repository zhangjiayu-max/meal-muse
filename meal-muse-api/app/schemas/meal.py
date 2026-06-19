from pydantic import BaseModel, Field
from datetime import date
from uuid import UUID


class MealPlanGenerate(BaseModel):
    plan_date: date | None = None
    preferences: str | None = Field(default=None, max_length=200, description="特殊要求，如今天想吃清淡点")
    couple_plan_enabled: bool | None = None
    goal_priority: str | None = Field(default=None, max_length=30)
    meal_context: str | None = Field(default=None, max_length=100)


class FoodItem(BaseModel):
    name: str
    amount: str
    calories: int
    protein: float = 0
    fat: float = 0
    carbs: float = 0


class ServingAdviceItem(BaseModel):
    label: str | None = None
    portion: str | None = None
    calories: int | None = None
    reason: str | None = None


class ServingAdvice(BaseModel):
    primary: ServingAdviceItem | None = None
    partner: ServingAdviceItem | None = None


class MealDetail(BaseModel):
    name: str
    foods: list[FoodItem]
    total_calories: int
    total_protein: float = 0
    total_fat: float = 0
    total_carbs: float = 0
    serving_advice: ServingAdvice | dict | None = None
    reason_tags: list[str] | None = None
    personalized_reason: str | None = None


class MealPlanResponse(BaseModel):
    id: UUID
    plan_date: date
    breakfast: MealDetail | None
    lunch: MealDetail | None
    dinner: MealDetail | None
    total_calories: int
    ai_note: str | None
    status: str
    version: int
    generate_params: dict | None = None

    class Config:
        from_attributes = True

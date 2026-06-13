from pydantic import BaseModel, Field
from datetime import date
from uuid import UUID


class MealPlanGenerate(BaseModel):
    plan_date: date | None = None
    preferences: str | None = Field(default=None, max_length=200, description="特殊要求，如今天想吃清淡点")


class FoodItem(BaseModel):
    name: str
    amount: str
    calories: int
    protein: float = 0
    fat: float = 0
    carbs: float = 0


class MealDetail(BaseModel):
    name: str
    foods: list[FoodItem]
    total_calories: int
    total_protein: float = 0
    total_fat: float = 0
    total_carbs: float = 0


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

    class Config:
        from_attributes = True

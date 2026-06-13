from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class DietRecordCreate(BaseModel):
    meal_type: str = Field(..., pattern="^(breakfast|lunch|dinner|snack)$")
    food_text: str = Field(..., min_length=1, max_length=1000, description="吃了什么")
    recorded_at: datetime | None = None


class DietRecordResponse(BaseModel):
    id: UUID
    meal_type: str
    food_text: str
    parsed_foods: list | None
    total_calories: int
    total_protein: float
    total_fat: float
    total_carbs: float
    total_fiber: float
    ai_analysis: str | None
    recorded_at: datetime
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


class DailyDietSummary(BaseModel):
    date: str
    total_calories: int
    total_protein: float
    total_fat: float
    total_carbs: float
    total_fiber: float
    meal_count: int
    records: list[DietRecordResponse]

"""报告相关 schema"""
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class NutritionScore(BaseModel):
    protein: float = Field(..., ge=0, le=100, description="蛋白质评分")
    fat: float = Field(..., ge=0, le=100, description="脂肪评分")
    carbs: float = Field(..., ge=0, le=100, description="碳水评分")
    fiber: float = Field(..., ge=0, le=100, description="纤维评分")
    calorie: float = Field(..., ge=0, le=100, description="热量评分")
    overall: float = Field(..., ge=0, le=100, description="综合评分")


class MealDetail(BaseModel):
    meal_type: str = Field(..., description="餐次：breakfast/lunch/dinner/snack")
    foods: List[str] = Field(default=[], description="食物列表")
    calories: float = Field(0, description="该餐热量")


class DailyReportResponse(BaseModel):
    user_id: UUID
    report_date: date
    total_calories: float = Field(0, description="总热量")
    target_calories: float = Field(0, description="目标热量")
    protein_g: float = Field(0, description="蛋白质（克）")
    fat_g: float = Field(0, description="脂肪（克）")
    carbs_g: float = Field(0, description="碳水（克）")
    fiber_g: float = Field(0, description="纤维（克）")
    meals: List[MealDetail] = []
    score: Optional[NutritionScore] = None
    ai_comment: Optional[str] = Field(None, description="AI 评价")

    model_config = {"from_attributes": True}


class DaySummary(BaseModel):
    date: date
    total_calories: float
    target_met: bool = Field(False, description="是否达标")


class WeeklyReportResponse(BaseModel):
    user_id: UUID
    week_start: date
    week_end: date
    avg_calories: float = Field(0, description="日均热量")
    total_records: int = Field(0, description="记录天数")
    days: List[DaySummary] = []
    score: Optional[NutritionScore] = None
    trend: str = Field("stable", description="趋势：improving/stable/declining")
    ai_summary: Optional[str] = Field(None, description="AI 周总结")

    model_config = {"from_attributes": True}

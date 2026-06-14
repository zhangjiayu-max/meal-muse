from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.diet_record import DietRecord
from app.services.report_service import (
    generate_weekly_summary,
    calculate_nutrition_scores,
    generate_nutrition_summary,
)

router = APIRouter(prefix="/reports", tags=["健康报告"])


class DailyReport(BaseModel):
    date: str
    total_calories: int
    total_protein: float
    total_fat: float
    total_carbs: float
    total_fiber: float
    meal_count: int
    calorie_target: int | None
    calorie_diff: int | None
    status: str  # "达标" / "超标" / "不足"


class WeeklyReport(BaseModel):
    week_start: str
    week_end: str
    avg_daily_calories: float
    avg_daily_protein: float
    avg_daily_fat: float
    avg_daily_carbs: float
    days_recorded: int
    total_meals: int
    ai_summary: str


class NutritionRadar(BaseModel):
    protein_score: float  # 0-100
    fat_score: float
    carbs_score: float
    fiber_score: float
    calorie_score: float
    summary: str


@router.get("/daily", response_model=DailyReport)
async def get_daily_report(
    report_date: date | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """每日报告"""
    target_date = report_date or date.today()

    result = await db.execute(
        select(
            func.sum(DietRecord.total_calories),
            func.sum(DietRecord.total_protein),
            func.sum(DietRecord.total_fat),
            func.sum(DietRecord.total_carbs),
            func.sum(DietRecord.total_fiber),
            func.count(DietRecord.id),
        ).where(
            DietRecord.user_id == current_user.id,
            DietRecord.record_date == target_date,
            DietRecord.deleted_at.is_(None),
        )
    )
    row = result.one()

    total_cal = int(row[0] or 0)
    target = current_user.daily_calorie_target or 1580
    diff = total_cal - target

    if abs(diff) <= 100:
        status = "达标"
    elif diff > 100:
        status = "超标"
    else:
        status = "不足"

    return DailyReport(
        date=target_date.isoformat(),
        total_calories=total_cal,
        total_protein=float(row[1] or 0),
        total_fat=float(row[2] or 0),
        total_carbs=float(row[3] or 0),
        total_fiber=float(row[4] or 0),
        meal_count=int(row[5] or 0),
        calorie_target=target,
        calorie_diff=diff,
        status=status,
    )


@router.get("/weekly", response_model=WeeklyReport)
async def get_weekly_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """每周报告"""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    result = await db.execute(
        select(
            func.avg(DietRecord.total_calories),
            func.avg(DietRecord.total_protein),
            func.avg(DietRecord.total_fat),
            func.avg(DietRecord.total_carbs),
            func.count(DietRecord.id),
            func.count(func.distinct(DietRecord.record_date)),
        ).where(
            DietRecord.user_id == current_user.id,
            DietRecord.record_date >= week_start,
            DietRecord.record_date <= week_end,
            DietRecord.deleted_at.is_(None),
        )
    )
    row = one_or_zero(result)

    avg_cal = round(float(row[0] or 0))
    days = int(row[5] or 0)

    target = current_user.daily_calorie_target or 1580
    ai_summary = generate_weekly_summary(avg_cal, target, days)

    return WeeklyReport(
        week_start=week_start.isoformat(),
        week_end=week_end.isoformat(),
        avg_daily_calories=avg_cal,
        avg_daily_protein=round(float(row[1] or 0), 1),
        avg_daily_fat=round(float(row[2] or 0), 1),
        avg_daily_carbs=round(float(row[3] or 0), 1),
        days_recorded=days,
        total_meals=int(row[4] or 0),
        ai_summary=ai_summary,
    )


@router.get("/nutrition-radar", response_model=NutritionRadar)
async def get_nutrition_radar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """营养雷达图数据"""
    today = date.today()
    week_start = today - timedelta(days=7)

    result = await db.execute(
        select(
            func.avg(DietRecord.total_calories),
            func.avg(DietRecord.total_protein),
            func.avg(DietRecord.total_fat),
            func.avg(DietRecord.total_carbs),
            func.avg(DietRecord.total_fiber),
        ).where(
            DietRecord.user_id == current_user.id,
            DietRecord.record_date >= week_start,
            DietRecord.deleted_at.is_(None),
        )
    )
    row = result.one()

    target = current_user.daily_calorie_target or 1580

    scores = calculate_nutrition_scores(
        avg_calories=float(row[0] or 0),
        avg_protein=float(row[1] or 0),
        avg_fat=float(row[2] or 0),
        avg_carbs=float(row[3] or 0),
        avg_fiber=float(row[4] or 0),
        calorie_target=target,
    )
    summary = generate_nutrition_summary(scores)

    return NutritionRadar(
        protein_score=scores["protein_score"],
        fat_score=scores["fat_score"],
        carbs_score=scores["carbs_score"],
        fiber_score=scores["fiber_score"],
        calorie_score=scores["calorie_score"],
        summary=summary,
    )


def one_or_zero(result):
    row = result.one()
    return row

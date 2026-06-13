from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.diet_record import DietRecord

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

    # AI 生成总结
    target = current_user.daily_calorie_target or 1580
    if avg_cal > target + 100:
        summary = f"本周日均热量 {avg_cal}kcal，超出目标 {avg_cal - target}kcal。建议适当减少高热量食物，增加蔬菜摄入。"
    elif avg_cal < target - 200:
        summary = f"本周日均热量 {avg_cal}kcal，低于目标 {target - avg_cal}kcal。注意不要过度节食，保证营养均衡。"
    else:
        summary = f"本周日均热量 {avg_cal}kcal，控制良好！继续保持均衡饮食。"

    return WeeklyReport(
        week_start=week_start.isoformat(),
        week_end=week_end.isoformat(),
        avg_daily_calories=avg_cal,
        avg_daily_protein=round(float(row[1] or 0), 1),
        avg_daily_fat=round(float(row[2] or 0), 1),
        avg_daily_carbs=round(float(row[3] or 0), 1),
        days_recorded=days,
        total_meals=int(row[4] or 0),
        ai_summary=summary,
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

    # 计算各项得分 (0-100)
    cal_score = min(100, round(float(row[0] or 0) / target * 100))
    protein_score = min(100, round(float(row[1] or 0) / 60 * 100))  # 目标 60g
    fat_score = min(100, round(float(row[2] or 0) / 55 * 100))  # 目标 55g
    carbs_score = min(100, round(float(row[3] or 0) / 200 * 100))  # 目标 200g
    fiber_score = min(100, round(float(row[4] or 0) / 25 * 100))  # 目标 25g

    issues = []
    if protein_score < 70:
        issues.append("蛋白质偏低")
    if fiber_score < 70:
        issues.append("膳食纤维不足")
    if cal_score > 110:
        issues.append("热量超标")

    summary = "本周营养状况良好！" if not issues else f"需要注意：{'、'.join(issues)}。"

    return NutritionRadar(
        protein_score=protein_score,
        fat_score=fat_score,
        carbs_score=carbs_score,
        fiber_score=fiber_score,
        calorie_score=cal_score,
        summary=summary,
    )


def one_or_zero(result):
    row = result.one()
    return row

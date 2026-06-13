from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel, Field
from uuid import UUID
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.body_metric import BodyMetric

router = APIRouter(prefix="/body", tags=["身体数据"])


class BodyMetricCreate(BaseModel):
    metric_date: date | None = None
    weight: float | None = None
    body_fat_pct: float | None = None
    muscle_mass: float | None = None
    bmi: float | None = None
    waist_circum: float | None = None
    blood_pressure_sys: int | None = None
    blood_pressure_dia: int | None = None
    blood_sugar: float | None = None
    heart_rate: int | None = None
    sleep_hours: float | None = None
    water_ml: int | None = None
    steps: int | None = None
    notes: str | None = None


class BodyMetricResponse(BaseModel):
    id: UUID
    metric_date: date
    weight: float | None
    body_fat_pct: float | None
    muscle_mass: float | None
    bmi: float | None
    waist_circum: float | None
    blood_pressure_sys: int | None
    blood_pressure_dia: int | None
    blood_sugar: float | None
    heart_rate: int | None
    sleep_hours: float | None
    water_ml: int | None
    steps: int | None
    notes: str | None

    class Config:
        from_attributes = True


@router.post("/metrics", response_model=BodyMetricResponse)
async def record_body_metric(
    req: BodyMetricCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """记录身体数据"""
    metric_date = req.metric_date or date.today()

    metric = BodyMetric(
        user_id=current_user.id,
        metric_date=metric_date,
        weight=req.weight,
        body_fat_pct=req.body_fat_pct,
        muscle_mass=req.muscle_mass,
        bmi=req.bmi,
        waist_circum=req.waist_circum,
        blood_pressure_sys=req.blood_pressure_sys,
        blood_pressure_dia=req.blood_pressure_dia,
        blood_sugar=req.blood_sugar,
        heart_rate=req.heart_rate,
        sleep_hours=req.sleep_hours,
        water_ml=req.water_ml,
        steps=req.steps,
        notes=req.notes,
    )
    db.add(metric)

    # 自动更新用户体重
    if req.weight:
        current_user.current_weight = req.weight

    await db.commit()
    await db.refresh(metric)
    return BodyMetricResponse.model_validate(metric)


@router.get("/metrics", response_model=list[BodyMetricResponse])
async def list_body_metrics(
    days: int = Query(default=30, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取身体数据列表"""
    start_date = date.today() - __import__("datetime").timedelta(days=days)
    result = await db.execute(
        select(BodyMetric).where(
            BodyMetric.user_id == current_user.id,
            BodyMetric.metric_date >= start_date,
            BodyMetric.deleted_at.is_(None),
        ).order_by(desc(BodyMetric.metric_date))
    )
    metrics = result.scalars().all()
    return [BodyMetricResponse.model_validate(m) for m in metrics]


@router.get("/metrics/latest", response_model=BodyMetricResponse | None)
async def get_latest_metric(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取最新的身体数据"""
    result = await db.execute(
        select(BodyMetric).where(
            BodyMetric.user_id == current_user.id,
            BodyMetric.deleted_at.is_(None),
        ).order_by(desc(BodyMetric.metric_date)).limit(1)
    )
    metric = result.scalar_one_or_none()
    if not metric:
        return None
    return BodyMetricResponse.model_validate(metric)
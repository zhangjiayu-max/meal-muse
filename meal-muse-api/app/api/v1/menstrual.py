from datetime import date, datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.menstrual_cycle import MenstrualCycle
from app.services.menstrual_service import calculate_menstrual_phase, get_phase_diet_tip
from pydantic import BaseModel, Field

router = APIRouter(prefix="/menstrual", tags=["生理期"])


class CycleCreate(BaseModel):
    period_start: date
    period_end: date | None = None
    symptoms: list[str] = Field(default_factory=list)
    mood: str | None = None
    flow_level: str | None = None
    temperature: float | None = None
    notes: str | None = None


class CycleResponse(BaseModel):
    id: str
    period_start: date
    period_end: date | None
    cycle_length: int | None
    period_length: int | None
    ovulation_day: date | None
    fertile_window_start: date | None
    fertile_window_end: date | None
    symptoms: list[str]
    mood: str | None
    flow_level: str | None
    current_phase: str
    phase_diet_tip: dict

    class Config:
        from_attributes = True


@router.post("/records", response_model=CycleResponse)
async def create_cycle_record(
    req: CycleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """记录经期"""
    # 计算周期长度
    result = await db.execute(
        select(MenstrualCycle)
        .where(MenstrualCycle.user_id == current_user.id)
        .order_by(desc(MenstrualCycle.period_start))
        .limit(1)
    )
    last_cycle = result.scalar_one_or_none()

    cycle_length = None
    if last_cycle:
        cycle_length = (req.period_start - last_cycle.period_start).days

    period_length = None
    if req.period_end:
        period_length = (req.period_end - req.period_start).days + 1

    # 计算排卵日和易孕窗口
    cl = cycle_length or 28
    ovulation_day = req.period_start + timedelta(days=cl - 14)
    fertile_start = ovulation_day - timedelta(days=2)
    fertile_end = ovulation_day + timedelta(days=2)

    cycle = MenstrualCycle(
        user_id=current_user.id,
        period_start=req.period_start,
        period_end=req.period_end,
        cycle_length=cycle_length,
        period_length=period_length,
        ovulation_day=ovulation_day,
        fertile_window_start=fertile_start,
        fertile_window_end=fertile_end,
        symptoms=req.symptoms,
        mood=req.mood,
        flow_level=req.flow_level,
        temperature=req.temperature,
        notes=req.notes,
    )
    db.add(cycle)
    await db.commit()
    await db.refresh(cycle)

    phase, _ = calculate_menstrual_phase(
        period_start=req.period_start,
        cycle_length=cl,
        ovulation_day=ovulation_day,
        period_end=req.period_end,
    )

    return CycleResponse(
        id=str(cycle.id),
        period_start=cycle.period_start,
        period_end=cycle.period_end,
        cycle_length=cycle.cycle_length,
        period_length=cycle.period_length,
        ovulation_day=cycle.ovulation_day,
        fertile_window_start=cycle.fertile_window_start,
        fertile_window_end=cycle.fertile_window_end,
        symptoms=cycle.symptoms or [],
        mood=cycle.mood,
        flow_level=cycle.flow_level,
        current_phase=phase,
        phase_diet_tip=get_phase_diet_tip(phase),
    )


@router.get("/current", response_model=CycleResponse | None)
async def get_current_phase(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前经期阶段"""
    result = await db.execute(
        select(MenstrualCycle)
        .where(MenstrualCycle.user_id == current_user.id)
        .order_by(desc(MenstrualCycle.period_start))
        .limit(1)
    )
    cycle = result.scalar_one_or_none()
    if not cycle:
        return None

    cl = cycle.cycle_length or 28
    phase, _ = calculate_menstrual_phase(
        period_start=cycle.period_start,
        cycle_length=cl,
        ovulation_day=cycle.ovulation_day,
        period_end=cycle.period_end,
    )

    return CycleResponse(
        id=str(cycle.id),
        period_start=cycle.period_start,
        period_end=cycle.period_end,
        cycle_length=cycle.cycle_length,
        period_length=cycle.period_length,
        ovulation_day=cycle.ovulation_day,
        fertile_window_start=cycle.fertile_window_start,
        fertile_window_end=cycle.fertile_window_end,
        symptoms=cycle.symptoms or [],
        mood=cycle.mood,
        flow_level=cycle.flow_level,
        current_phase=phase,
        phase_diet_tip=get_phase_diet_tip(phase),
    )


@router.get("/records", response_model=list[CycleResponse])
async def list_cycle_records(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取经期记录列表"""
    result = await db.execute(
        select(MenstrualCycle)
        .where(MenstrualCycle.user_id == current_user.id)
        .order_by(desc(MenstrualCycle.period_start))
        .limit(12)
    )
    cycles = result.scalars().all()

    responses = []
    for cycle in cycles:
        cl = cycle.cycle_length or 28
        phase, _ = calculate_menstrual_phase(
            period_start=cycle.period_start,
            cycle_length=cl,
            ovulation_day=cycle.ovulation_day,
            period_end=cycle.period_end,
        )
        responses.append(CycleResponse(
            id=str(cycle.id),
            period_start=cycle.period_start,
            period_end=cycle.period_end,
            cycle_length=cycle.cycle_length,
            period_length=cycle.period_length,
            ovulation_day=cycle.ovulation_day,
            fertile_window_start=cycle.fertile_window_start,
            fertile_window_end=cycle.fertile_window_end,
            symptoms=cycle.symptoms or [],
            mood=cycle.mood,
            flow_level=cycle.flow_level,
            current_phase=phase,
            phase_diet_tip=get_phase_diet_tip(phase),
        ))
    return responses

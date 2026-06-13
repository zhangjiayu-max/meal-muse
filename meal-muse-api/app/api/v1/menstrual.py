from datetime import date, datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.menstrual_cycle import MenstrualCycle
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


# 经期阶段饮食建议
PHASE_DIET_TIPS = {
    "menstrual": {
        "phase_name": "月经期",
        "diet_focus": "温补驱寒，补充铁质",
        "recommended": ["红糖姜茶", "当归羊肉汤", "猪肝", "菠菜", "红枣", "桂圆"],
        "avoid": ["冰淇淋", "冷饮", "西瓜", "螃蟹"],
        "recommended_fruits": ["樱桃", "红枣", "桂圆", "榴莲"],
        "avoid_fruits": ["西瓜", "梨", "柚子"],
    },
    "follicular": {
        "phase_name": "卵泡期",
        "diet_focus": "补充优质蛋白，为排卵做准备",
        "recommended": ["鸡蛋", "鱼", "豆腐", "黑芝麻", "黑豆", "西兰花"],
        "avoid": ["油炸食品", "高糖食物"],
        "recommended_fruits": ["蓝莓", "草莓", "苹果", "牛油果"],
        "avoid_fruits": [],
    },
    "ovulation": {
        "phase_name": "排卵期",
        "diet_focus": "补充叶酸和锌，促进卵子质量",
        "recommended": ["黑豆", "豆浆", "坚果", "深海鱼", "芦笋", "菠菜"],
        "avoid": ["酒精", "咖啡过量"],
        "recommended_fruits": ["牛油果", "蓝莓", "石榴", "猕猴桃"],
        "avoid_fruits": ["冰镇水果"],
    },
    "luteal": {
        "phase_name": "黄体期",
        "diet_focus": "补充B族维生素，缓解PMS",
        "recommended": ["香蕉", "燕麦", "坚果", "菠菜", "全谷物", "红薯"],
        "avoid": ["高盐食物", "咖啡因过量", "辛辣刺激"],
        "recommended_fruits": ["香蕉", "苹果", "橙子", "樱桃"],
        "avoid_fruits": [],
    },
}


def calculate_phase(period_start: date, cycle_length: int = 28) -> tuple[str, date | None]:
    """计算当前经期阶段"""
    today = date.today()
    day_in_cycle = (today - period_start).days + 1

    if day_in_cycle < 1:
        return "unknown", None

    if day_in_cycle <= 5:
        return "menstrual", None
    elif day_in_cycle <= 13:
        return "follicular", None
    elif day_in_cycle <= 16:
        ovulation_day = period_start + timedelta(days=13)
        return "ovulation", ovulation_day
    else:
        return "luteal", None


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

    phase, _ = calculate_phase(req.period_start, cl)

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
        phase_diet_tip=PHASE_DIET_TIPS.get(phase, {}),
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
    phase, _ = calculate_phase(cycle.period_start, cl)

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
        phase_diet_tip=PHASE_DIET_TIPS.get(phase, {}),
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
        phase, _ = calculate_phase(cycle.period_start, cl)
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
            phase_diet_tip=PHASE_DIET_TIPS.get(phase, {}),
        ))
    return responses

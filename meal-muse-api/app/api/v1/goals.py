"""健康目标管理 API — 减肥/备孕/养生/增肌目标 CRUD + 自动热量计算"""

from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.models.health_goal import HealthGoal
from app.services.nutrition_calculator import (
    calculate_daily_calorie_target,
    calculate_macros,
)

router = APIRouter(prefix="/goals", tags=["健康目标"])

VALID_GOAL_TYPES = {"weight_loss", "pregnancy", "health", "muscle_gain", "custom"}


class GoalCreate(BaseModel):
    goal_type: str = Field(..., description="目标类型：weight_loss/pregnancy/health/muscle_gain/custom")
    target_weight: float | None = Field(None, ge=20, le=500, description="目标体重(kg)")
    target_date: date | None = Field(None, description="目标达成日期")
    weekly_loss_rate: float | None = Field(None, ge=0, le=2, description="周减重速率(kg/周)")
    daily_calorie_target: int | None = Field(None, ge=800, le=5000, description="每日热量目标(kcal)，不传则自动计算")
    macro_targets: dict | None = Field(None, description="宏量营养素目标，不传则自动计算")
    special_notes: str | None = None


class GoalUpdate(BaseModel):
    goal_type: str | None = None
    target_weight: float | None = Field(None, ge=20, le=500)
    target_date: date | None = None
    weekly_loss_rate: float | None = Field(None, ge=0, le=2)
    daily_calorie_target: int | None = Field(None, ge=800, le=5000)
    macro_targets: dict | None = None
    special_notes: str | None = None
    status: str | None = Field(None, pattern="^(active|paused|completed)$")


class GoalResponse(BaseModel):
    id: UUID
    user_id: UUID
    goal_type: str
    target_weight: float | None
    target_date: date | None
    weekly_loss_rate: float | None
    daily_calorie_target: int | None
    macro_targets: dict | None
    special_notes: str | None
    status: str
    created_at: object
    updated_at: object

    model_config = {"from_attributes": True}


def _auto_calc_targets(user: User, goal_type: str) -> tuple[int, dict]:
    """根据用户身体数据自动计算热量目标和宏量营养素"""
    if not (user.height_cm and user.current_weight and user.age):
        return 1600, calculate_macros(1600, goal_type)
    calorie = calculate_daily_calorie_target(
        height_cm=float(user.height_cm),
        weight_kg=float(user.current_weight),
        age=user.age,
        gender=user.gender or "female",
        activity_level=user.activity_level or "sedentary",
        goal_type=goal_type,
    )
    macros = calculate_macros(calorie, goal_type)
    return calorie, macros


@router.post("", response_model=GoalResponse)
async def create_goal(
    req: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建健康目标（新目标会自动暂停旧目标）"""
    if req.goal_type not in VALID_GOAL_TYPES:
        from app.core.exceptions import BadRequestError
        raise BadRequestError(f"无效的目标类型，可选：{', '.join(sorted(VALID_GOAL_TYPES))}")

    # 暂停旧目标
    old_result = await db.execute(
        select(HealthGoal).where(
            HealthGoal.user_id == current_user.id,
            HealthGoal.status == "active",
        )
    )
    for old in old_result.scalars().all():
        old.status = "paused"

    # 自动计算热量目标（用户未显式指定时）
    calorie_target = req.daily_calorie_target
    macro_targets = req.macro_targets
    if not calorie_target:
        calorie_target, auto_macros = _auto_calc_targets(current_user, req.goal_type)
        if not macro_targets:
            macro_targets = auto_macros

    goal = HealthGoal(
        user_id=current_user.id,
        goal_type=req.goal_type,
        target_weight=req.target_weight,
        target_date=req.target_date,
        weekly_loss_rate=req.weekly_loss_rate,
        daily_calorie_target=calorie_target,
        macro_targets=macro_targets,
        special_notes=req.special_notes,
        status="active",
    )
    db.add(goal)

    # 同步到 User.daily_calorie_target（兼容旧字段读取）
    current_user.daily_calorie_target = calorie_target

    await db.commit()
    await db.refresh(goal)
    return GoalResponse.model_validate(goal)


@router.get("", response_model=list[GoalResponse])
async def list_goals(
    status_filter: str | None = Query(None, alias="status", description="active/paused/completed"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取健康目标列表"""
    stmt = select(HealthGoal).where(HealthGoal.user_id == current_user.id)
    if status_filter:
        stmt = stmt.where(HealthGoal.status == status_filter)
    stmt = stmt.order_by(HealthGoal.created_at.desc())
    result = await db.execute(stmt)
    return [GoalResponse.model_validate(g) for g in result.scalars().all()]


@router.get("/current", response_model=GoalResponse | None)
async def get_current_goal(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前生效的健康目标"""
    result = await db.execute(
        select(HealthGoal).where(
            HealthGoal.user_id == current_user.id,
            HealthGoal.status == "active",
        ).order_by(HealthGoal.created_at.desc()).limit(1)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        return None
    return GoalResponse.model_validate(goal)


@router.patch("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: UUID,
    req: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新健康目标"""
    result = await db.execute(
        select(HealthGoal).where(
            HealthGoal.id == goal_id,
            HealthGoal.user_id == current_user.id,
        )
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise NotFoundError("健康目标不存在")

    if req.goal_type is not None and req.goal_type not in VALID_GOAL_TYPES:
        from app.core.exceptions import BadRequestError
        raise BadRequestError(f"无效的目标类型，可选：{', '.join(sorted(VALID_GOAL_TYPES))}")

    # 若改了目标类型且未显式传热量目标，重新自动计算
    new_goal_type = req.goal_type or goal.goal_type
    if req.goal_type and req.daily_calorie_target is None:
        calorie, auto_macros = _auto_calc_targets(current_user, new_goal_type)
        goal.daily_calorie_target = calorie
        if req.macro_targets is None:
            goal.macro_targets = auto_macros
        current_user.daily_calorie_target = calorie

    # 应用显式传入的字段
    for field in ("goal_type", "target_weight", "target_date", "weekly_loss_rate",
                  "daily_calorie_target", "macro_targets", "special_notes", "status"):
        val = getattr(req, field, None)
        if val is not None:
            setattr(goal, field, val)
            if field == "daily_calorie_target":
                current_user.daily_calorie_target = val

    await db.commit()
    await db.refresh(goal)
    return GoalResponse.model_validate(goal)


@router.post("/{goal_id}/recalculate", response_model=GoalResponse)
async def recalculate_goal(
    goal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """根据最新身体数据重新计算热量目标（体重变化后调用）"""
    result = await db.execute(
        select(HealthGoal).where(
            HealthGoal.id == goal_id,
            HealthGoal.user_id == current_user.id,
        )
    )
    goal = result.scalar_one_or_none()
    if not goal:
        raise NotFoundError("健康目标不存在")

    calorie, macros = _auto_calc_targets(current_user, goal.goal_type)
    goal.daily_calorie_target = calorie
    goal.macro_targets = macros
    current_user.daily_calorie_target = calorie

    await db.commit()
    await db.refresh(goal)
    return GoalResponse.model_validate(goal)

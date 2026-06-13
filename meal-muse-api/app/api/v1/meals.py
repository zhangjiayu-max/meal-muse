"""餐食计划 API — 已接入 AI 生成引擎"""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.meal_plan import MealPlan
from app.schemas.meal import MealPlanGenerate, MealPlanResponse
from app.services.meal_plan_engine import generate_plan, replace_meal

router = APIRouter(prefix="/meals", tags=["餐食计划"])


@router.post("/generate", response_model=MealPlanResponse)
async def generate_meal_plan(
    req: MealPlanGenerate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """生成今日三餐计划（基于用户画像 AI 生成）"""
    plan_date = req.plan_date or date.today()
    plan = await generate_plan(db, current_user, plan_date)
    return MealPlanResponse.model_validate(plan)


@router.get("/plan", response_model=MealPlanResponse | None)
async def get_meal_plan(
    plan_date: date | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取指定日期的餐食计划"""
    target_date = plan_date or date.today()
    result = await db.execute(
        select(MealPlan).where(
            MealPlan.user_id == current_user.id,
            MealPlan.plan_date == target_date,
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        return None
    return MealPlanResponse.model_validate(plan)


@router.post("/{plan_id}/replace", response_model=MealPlanResponse)
async def replace_single_meal(
    plan_id: UUID,
    meal_type: str = "lunch",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """智能替换某一餐（基于用户画像重新生成）"""
    try:
        plan = await replace_meal(db, current_user, str(plan_id), meal_type)
        return MealPlanResponse.model_validate(plan)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

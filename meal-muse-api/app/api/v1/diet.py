"""饮食记录 API"""

import logging
from datetime import datetime, date, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.diet_record import DietRecord
from pydantic import BaseModel, Field
from app.schemas.diet import DietRecordCreate, DietRecordResponse, DailyDietSummary
from app.services.food_parser import parse_food_text
from app.repositories.diet_repo import DietRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/diet", tags=["饮食记录"])


class DietRecordUpdate(BaseModel):
    """编辑饮食记录请求体"""
    food_text: str | None = Field(None, description="食物文本")
    meal_type: str | None = Field(None, description="餐次：breakfast/lunch/dinner/snack")


@router.post("/records", response_model=DietRecordResponse)
async def create_record(
    req: DietRecordCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建饮食记录（AI 智能解析食物营养）"""
    try:
        now = req.recorded_at or datetime.now(timezone.utc)
        parsed = await parse_food_text(req.food_text)

        record = DietRecord(
            user_id=current_user.id,
            meal_type=req.meal_type,
            food_text=req.food_text,
            parsed_foods=parsed["foods"],
            total_calories=parsed["total_calories"],
            total_protein=parsed["total_protein"],
            total_fat=parsed["total_fat"],
            total_carbs=parsed["total_carbs"],
            ai_analysis="已记录，继续加油！",
            recorded_at=now,
            record_date=now.date(),
            source="manual",
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return DietRecordResponse.model_validate(record)
    except Exception as e:
        logger.error(f"创建饮食记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"饮食记录创建失败: {str(e)}")


@router.get("/records", response_model=list[DietRecordResponse])
async def list_records(
    record_date: date | None = Query(default=None, description="按日期筛选"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取饮食记录列表"""
    query = select(DietRecord).where(
        DietRecord.user_id == current_user.id,
        DietRecord.deleted_at.is_(None),
    )
    if record_date:
        query = query.where(DietRecord.record_date == record_date)
    query = query.order_by(DietRecord.recorded_at.desc()).limit(50)

    result = await db.execute(query)
    records = result.scalars().all()
    return [DietRecordResponse.model_validate(r) for r in records]


@router.get("/today", response_model=DailyDietSummary)
async def get_today(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取今日饮食汇总"""
    today = date.today()
    result = await db.execute(
        select(DietRecord).where(
            DietRecord.user_id == current_user.id,
            DietRecord.record_date == today,
            DietRecord.deleted_at.is_(None),
        ).order_by(DietRecord.recorded_at)
    )
    records = result.scalars().all()

    return DailyDietSummary(
        date=today.isoformat(),
        total_calories=sum(r.total_calories for r in records),
        total_protein=sum(float(r.total_protein) for r in records),
        total_fat=sum(float(r.total_fat) for r in records),
        total_carbs=sum(float(r.total_carbs) for r in records),
        total_fiber=sum(float(r.total_fiber) for r in records),
        meal_count=len(records),
        records=[DietRecordResponse.model_validate(r) for r in records],
    )


@router.put("/records/{record_id}", response_model=DietRecordResponse)
async def update_record(
    record_id: UUID,
    req: DietRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """编辑饮食记录（修改食物/餐次后重新 AI 解析营养）"""
    result = await db.execute(
        select(DietRecord).where(
            DietRecord.id == record_id,
            DietRecord.user_id == current_user.id,
            DietRecord.deleted_at.is_(None),
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    if req.meal_type is not None:
        record.meal_type = req.meal_type

    if req.food_text is not None:
        record.food_text = req.food_text
        # 重新 AI 解析营养
        parsed = await parse_food_text(req.food_text)
        record.parsed_foods = parsed["foods"]
        record.total_calories = parsed["total_calories"]
        record.total_protein = parsed["total_protein"]
        record.total_fat = parsed["total_fat"]
        record.total_carbs = parsed["total_carbs"]
        record.ai_analysis = "已更新，营养数据已重新计算"

    await db.commit()
    await db.refresh(record)
    return DietRecordResponse.model_validate(record)


@router.delete("/records/{record_id}")
async def delete_record(
    record_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除饮食记录（软删除）"""
    result = await db.execute(
        select(DietRecord).where(
            DietRecord.id == record_id,
            DietRecord.user_id == current_user.id,
            DietRecord.deleted_at.is_(None),
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    record.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "已删除"}


@router.get("/recent-foods")
async def get_recent_foods(
    limit: int = Query(default=6, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户最近吃过的食物（去重），用于快捷录入"""
    diet_repo = DietRepository(db)
    foods = await diet_repo.get_recent_foods(current_user.id, limit)
    return {"foods": foods}


# ===== 常用食物管理 =====

class FavoriteFoodCreate(BaseModel):
    food_name: str = Field(..., max_length=100)
    meal_type: str | None = Field(None, description="适用餐次：breakfast/lunch/dinner/snack/any")
    category: str | None = Field(None, description="分类：主食/肉类/蔬菜/水果/饮品等")


class FavoriteFoodResponse(BaseModel):
    id: str
    food_name: str
    meal_type: str | None
    category: str | None
    use_count: int
    last_used_at: str | None

    class Config:
        from_attributes = True


@router.get("/favorites", response_model=list[FavoriteFoodResponse])
async def get_favorite_foods(
    meal_type: str | None = Query(None, description="按餐次筛选"),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户常用食物列表"""
    from app.models.user_favorite_food import UserFavoriteFood

    query = select(UserFavoriteFood).where(
        UserFavoriteFood.user_id == current_user.id,
    )
    if meal_type:
        query = query.where(
            (UserFavoriteFood.meal_type == meal_type) |
            (UserFavoriteFood.meal_type == "any") |
            (UserFavoriteFood.meal_type.is_(None))
        )
    query = query.order_by(
        UserFavoriteFood.sort_order.desc(),
        UserFavoriteFood.use_count.desc(),
    ).limit(limit)

    result = await db.execute(query)
    foods = result.scalars().all()

    return [
        FavoriteFoodResponse(
            id=str(f.id),
            food_name=f.food_name,
            meal_type=f.meal_type,
            category=f.category,
            use_count=f.use_count,
            last_used_at=f.last_used_at.isoformat() if f.last_used_at else None,
        )
        for f in foods
    ]


@router.post("/favorites", response_model=FavoriteFoodResponse)
async def add_favorite_food(
    req: FavoriteFoodCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """添加常用食物"""
    from app.models.user_favorite_food import UserFavoriteFood
    from datetime import datetime, timezone

    # 检查是否已存在
    existing = await db.execute(
        select(UserFavoriteFood).where(
            UserFavoriteFood.user_id == current_user.id,
            UserFavoriteFood.food_name == req.food_name,
        )
    )
    food = existing.scalar_one_or_none()

    if food:
        # 已存在，更新使用次数
        food.use_count += 1
        food.last_used_at = datetime.now(timezone.utc)
        if req.meal_type:
            food.meal_type = req.meal_type
        if req.category:
            food.category = req.category
    else:
        # 不存在，创建新的
        food = UserFavoriteFood(
            user_id=current_user.id,
            food_name=req.food_name,
            meal_type=req.meal_type,
            category=req.category,
            use_count=1,
            last_used_at=datetime.now(timezone.utc),
        )
        db.add(food)

    await db.commit()
    await db.refresh(food)

    return FavoriteFoodResponse(
        id=str(food.id),
        food_name=food.food_name,
        meal_type=food.meal_type,
        category=food.category,
        use_count=food.use_count,
        last_used_at=food.last_used_at.isoformat() if food.last_used_at else None,
    )


@router.delete("/favorites/{food_id}")
async def remove_favorite_food(
    food_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除常用食物"""
    from app.models.user_favorite_food import UserFavoriteFood

    result = await db.execute(
        select(UserFavoriteFood).where(
            UserFavoriteFood.id == food_id,
            UserFavoriteFood.user_id == current_user.id,
        )
    )
    food = result.scalar_one_or_none()
    if not food:
        raise HTTPException(status_code=404, detail="常用食物不存在")

    await db.delete(food)
    await db.commit()
    return {"message": "已删除"}


@router.get("/smart-suggestions")
async def get_smart_suggestions(
    meal_type: str = Query(..., description="当前餐次：breakfast/lunch/dinner/snack"),
    limit: int = Query(default=8, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """智能推荐食物（基于历史频率 + 餐次关联）"""
    from app.models.user_favorite_food import UserFavoriteFood
    from datetime import date, timedelta
    from collections import Counter

    # 每个分组的最大数量
    MAX_FAVORITES = 6
    MAX_HISTORY = 6
    MAX_DEFAULT = 8

    suggestions = []

    # 1. 获取用户收藏的常用食物（优先级最高，限制数量）
    favorites_result = await db.execute(
        select(UserFavoriteFood).where(
            UserFavoriteFood.user_id == current_user.id,
        ).order_by(
            UserFavoriteFood.sort_order.desc(),
            UserFavoriteFood.use_count.desc(),
        ).limit(MAX_FAVORITES)
    )
    favorites = favorites_result.scalars().all()
    for f in favorites:
        suggestions.append({
            "food": f.food_name,
            "source": "favorite",
            "count": f.use_count,
        })

    # 2. 获取该餐次的历史高频食物（最近 30 天，限制数量）
    week_ago = date.today() - timedelta(days=30)
    history_result = await db.execute(
        select(DietRecord.food_text).where(
            DietRecord.user_id == current_user.id,
            DietRecord.meal_type == meal_type,
            DietRecord.record_date >= week_ago,
            DietRecord.deleted_at.is_(None),
        ).order_by(DietRecord.recorded_at.desc()).limit(30)
    )
    history_records = history_result.scalars().all()

    # 解析历史食物
    food_counter = Counter()
    for food_text in history_records:
        # 简单分割（按 +、，、, 分割）
        foods = food_text.replace("，", ",").replace("、", ",").split("+")
        for food in foods:
            food = food.strip()
            if food and len(food) < 20:  # 过滤太长的（可能是整句话）
                food_counter[food] += 1

    # 添加高频历史食物（限制数量）
    for food, count in food_counter.most_common(MAX_HISTORY):
        if not any(s["food"] == food for s in suggestions):
            suggestions.append({
                "food": food,
                "source": "history",
                "count": count,
            })

    # 3. 按餐次的默认推荐（限制数量）
    default_foods = {
        "breakfast": ["小米粥", "水煮蛋", "全麦面包", "牛奶", "酸奶", "豆浆", "包子", "燕麦"],
        "lunch": ["鸡胸肉", "西兰花", "糙米饭", "番茄炒蛋", "牛肉面", "鱼香肉丝", "宫保鸡丁", "凉拌黄瓜"],
        "dinner": ["沙拉", "玉米", "红薯", "清蒸鱼", "虾仁", "豆腐", "蔬菜汤", "水果拼盘"],
        "snack": ["苹果", "香蕉", "坚果", "酸奶", "全麦饼干", "红枣"],
    }

    defaults = default_foods.get(meal_type, default_foods["lunch"])[:MAX_DEFAULT]
    for food in defaults:
        if not any(s["food"] == food for s in suggestions):
            suggestions.append({
                "food": food,
                "source": "default",
                "count": 0,
            })

    # 按来源优先级排序：favorite > history > default
    source_priority = {"favorite": 0, "history": 1, "default": 2}
    suggestions.sort(key=lambda x: (source_priority.get(x["source"], 3), -x["count"]))

    return {
        "meal_type": meal_type,
        "suggestions": suggestions[:limit],
    }

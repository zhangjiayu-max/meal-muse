"""饮食记录 API — 已接入 AI 食物解析"""

from datetime import datetime, date, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.diet_record import DietRecord
from app.schemas.diet import DietRecordCreate, DietRecordResponse, DailyDietSummary
from app.services.ai_service import call_ai_structured
from app.services.context_builder import get_ai_prompt_context

router = APIRouter(prefix="/diet", tags=["饮食记录"])

# AI 食物解析 system prompt
FOOD_PARSE_SYSTEM = """你是一个营养分析助手。用户会输入他们吃过的食物，你需要：
1. 识别出所有食物及份量
2. 估算每种食物的热量、蛋白质、脂肪、碳水

返回严格的 JSON 格式：
{
  "foods": [
    {"name": "食物名", "amount": "份量描述", "calories": 数字, "protein": 数字, "fat": 数字, "carbs": 数字}
  ],
  "total_calories": 数字,
  "total_protein": 数字,
  "total_fat": 数字,
  "total_carbs": 数字
}

注意：
- 份量参考中国饮食习惯（1碗≈200g, 1份≈150g, 1个鸡蛋≈50g等）
- 如果用户没写份量，按标准份量估算
- 只返回 JSON，不要其他文字
- 热量单位为 kcal，蛋白质/脂肪/碳水单位为 g"""


def _simple_parse(food_text: str) -> dict:
    """简单兜底解析（AI 不可用时）"""
    foods = []
    total_cal = 0
    for item in food_text.replace("，", ",").replace("、", ",").split(","):
        item = item.strip()
        if item:
            foods.append({"name": item, "amount": "1份", "calories": 200})
            total_cal += 200
    return {
        "foods": foods,
        "total_calories": total_cal,
        "total_protein": round(total_cal * 0.15 / 4, 1),
        "total_fat": round(total_cal * 0.25 / 9, 1),
        "total_carbs": round(total_cal * 0.60 / 4, 1),
    }


async def parse_food_text(food_text: str) -> dict:
    """用 AI 解析食物文本，返回营养估算"""
    try:
        import json
        raw = await call_ai_structured(
            prompt=food_text,
            system_prompt=FOOD_PARSE_SYSTEM,
        )
        # 解析 JSON
        text = raw.strip()
        import re
        m = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
        if m:
            text = m.group(1)
        else:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                text = text[start:end]

        result = json.loads(text)
        if "foods" in result and "total_calories" in result:
            return result
    except Exception:
        pass

    # Fallback
    return _simple_parse(food_text)


@router.post("/records", response_model=DietRecordResponse)
async def create_record(
    req: DietRecordCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建饮食记录（AI 智能解析食物营养）"""
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

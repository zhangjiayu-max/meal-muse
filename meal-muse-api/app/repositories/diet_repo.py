"""饮食记录数据访问层"""
from typing import List, Optional
from uuid import UUID
from datetime import date
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.diet_record import DietRecord
from .base import BaseRepository


class DietRepository(BaseRepository[DietRecord]):
    def __init__(self, db: AsyncSession):
        super().__init__(DietRecord, db)

    async def get_by_user_date(self, user_id: UUID, record_date: date) -> List[DietRecord]:
        result = await self.db.execute(
            select(DietRecord).where(
                DietRecord.user_id == user_id,
                DietRecord.record_date == record_date,
                DietRecord.deleted_at.is_(None),
            ).order_by(DietRecord.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_recent_foods(self, user_id: UUID, limit: int = 6) -> List[str]:
        """获取用户最近吃过的食物名（去重）"""
        result = await self.db.execute(
            select(DietRecord.food_text)
            .where(
                DietRecord.user_id == user_id,
                DietRecord.deleted_at.is_(None),
            )
            .order_by(DietRecord.created_at.desc())
            .limit(limit * 3)  # 多取一些去重
        )
        seen = set()
        foods = []
        for row in result.scalars().all():
            name = row.strip()
            if name and name not in seen:
                seen.add(name)
                foods.append(name)
            if len(foods) >= limit:
                break
        return foods

    async def get_daily_summary(self, user_id: UUID, record_date: date) -> dict:
        """获取当日营养汇总"""
        result = await self.db.execute(
            select(
                func.coalesce(func.sum(DietRecord.total_calories), 0).label("calories"),
                func.coalesce(func.sum(DietRecord.total_protein), 0).label("protein"),
                func.coalesce(func.sum(DietRecord.total_fat), 0).label("fat"),
                func.coalesce(func.sum(DietRecord.total_carbs), 0).label("carbs"),
                func.coalesce(func.sum(DietRecord.total_fiber), 0).label("fiber"),
                func.count(DietRecord.id).label("count"),
            ).where(
                DietRecord.user_id == user_id,
                DietRecord.record_date == record_date,
                DietRecord.deleted_at.is_(None),
            )
        )
        row = result.one()
        return {
            "calories": float(row.calories),
            "protein": float(row.protein),
            "fat": float(row.fat),
            "carbs": float(row.carbs),
            "fiber": float(row.fiber),
            "record_count": row.count,
        }

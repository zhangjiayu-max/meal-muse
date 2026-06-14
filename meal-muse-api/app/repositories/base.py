"""泛型 CRUD Repository 基类"""
from typing import TypeVar, Type, Optional, List, Generic
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: UUID) -> Optional[T]:
        return await self.db.get(self.model, id)

    async def get_list(
        self,
        *,
        filters: list = None,
        offset: int = 0,
        limit: int = 20,
        order_by: str = "created_at",
        ascending: bool = False,
    ) -> List[T]:
        query = select(self.model)
        if filters:
            for f in filters:
                query = query.where(f)
        col = getattr(self.model, order_by, self.model.created_at)
        query = query.order_by(col.asc() if ascending else col.desc())
        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(self, *, filters: list = None) -> int:
        query = select(func.count()).select_from(self.model)
        if filters:
            for f in filters:
                query = query.where(f)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def create(self, instance: T) -> T:
        self.db.add(instance)
        await self.db.flush()
        return instance

    async def update(self, instance: T) -> T:
        await self.db.flush()
        return instance

    async def soft_delete(self, instance: T) -> T:
        instance.deleted_at = datetime.now()
        await self.db.flush()
        return instance

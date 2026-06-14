"""用户数据访问层"""
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_phone(self, phone: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.phone == phone, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_openid(self, openid: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.wechat_openid == openid, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_id_active(self, id: UUID) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.id == id, User.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

"""对话数据访问层"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, distinct, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ai_chat_message import AiChatMessage
from .base import BaseRepository


class ChatRepository(BaseRepository[AiChatMessage]):
    def __init__(self, db: AsyncSession):
        super().__init__(AiChatMessage, db)

    async def get_sessions(self, user_id: UUID) -> List[dict]:
        """获取用户的会话列表（按最新消息排序）"""
        result = await self.db.execute(
            select(
                AiChatMessage.session_id,
                func.max(AiChatMessage.created_at).label("last_message_at"),
                func.count(AiChatMessage.id).label("message_count"),
            )
            .where(AiChatMessage.user_id == user_id)
            .group_by(AiChatMessage.session_id)
            .order_by(func.max(AiChatMessage.created_at).desc())
        )
        return [
            {
                "session_id": row.session_id,
                "last_message_at": row.last_message_at,
                "message_count": row.message_count,
            }
            for row in result.all()
        ]

    async def get_messages(
        self, session_id: UUID, limit: int = 50
    ) -> List[AiChatMessage]:
        """获取指定会话的消息"""
        result = await self.db.execute(
            select(AiChatMessage)
            .where(AiChatMessage.session_id == session_id)
            .order_by(AiChatMessage.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_last_messages(
        self, user_id: UUID, session_id: UUID, limit: int = 10
    ) -> List[AiChatMessage]:
        """获取最近 N 条消息（用于构建上下文）"""
        result = await self.db.execute(
            select(AiChatMessage)
            .where(
                AiChatMessage.user_id == user_id,
                AiChatMessage.session_id == session_id,
            )
            .order_by(AiChatMessage.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()  # 按时间正序
        return messages

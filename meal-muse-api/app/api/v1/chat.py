"""AI 对话 API"""

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.ai_chat_message import AiChatMessage
from app.repositories.chat_repo import ChatRepository
from app.schemas.chat import ChatMessage, ChatResponse
from app.services.chat_service import chat_send

router = APIRouter(prefix="/chat", tags=["AI 对话"])


@router.post("/send", response_model=ChatResponse)
async def send_message(
    req: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发送消息给 AI（支持多轮对话 + 历史持久化）"""
    result = await chat_send(db, current_user, req.content, req.session_id)
    return ChatResponse(**result)


@router.get("/history/{session_id}", response_model=list[ChatResponse])
async def get_chat_history(
    session_id: uuid.UUID,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取对话历史"""
    result = await db.execute(
        select(AiChatMessage).where(
            AiChatMessage.user_id == current_user.id,
            AiChatMessage.session_id == session_id,
        ).order_by(AiChatMessage.created_at).limit(limit)
    )
    messages = result.scalars().all()
    return [
        ChatResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            session_id=m.session_id,
            model_used=m.model_used,
            tokens_used=m.tokens_used,
            created_at=m.created_at,
        )
        for m in messages
    ]


@router.get("/sessions")
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的对话会话列表"""
    chat_repo = ChatRepository(db)
    sessions = await chat_repo.get_sessions(current_user.id)
    return {"sessions": [
        {
            "session_id": str(s["session_id"]),
            "last_message_at": s["last_message_at"].isoformat(),
            "message_count": s["message_count"],
        }
        for s in sessions
    ]}


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取指定会话的消息列表"""
    chat_repo = ChatRepository(db)
    messages = await chat_repo.get_messages(session_id)
    return {"messages": [
        {
            "id": str(m.id),
            "role": m.role,
            "content": m.content,
            "session_id": str(m.session_id),
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]}

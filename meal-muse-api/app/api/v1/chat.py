"""AI 对话 API — 已接入服务层 + 对话历史持久化"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.ai_chat_message import AiChatMessage
from app.schemas.chat import ChatMessage, ChatResponse
from app.services.ai_service import call_ai
from app.services.context_builder import get_user_context
from app.config import get_settings

router = APIRouter(prefix="/chat", tags=["AI 对话"])
settings = get_settings()

SYSTEM_PROMPT = """你是 MealMuse，一个专业的 AI 饮食健康助手。

你的职责：
1. 基于用户的饮食记录，提供个性化的饮食建议
2. 回答健康饮食相关问题（减肥/备孕/养生/经期饮食等）
3. 帮助用户达成健康目标

重要规则：
1. 只提供饮食和营养相关建议，不提供医疗诊断
2. 如果用户询问医疗问题，建议咨询专业医生
3. 建议要具体、可执行，避免空泛
4. 语气友好、鼓励，像一个贴心的健康伙伴
5. 回复用中文，简洁明了，适当使用 emoji
6. 如果用户有过敏原或疾病禁忌，必须提醒并避免推荐相关食物"""

# 每次对话加载的最大历史消息数
MAX_HISTORY_MESSAGES = 20


@router.post("/send", response_model=ChatResponse)
async def send_message(
    req: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发送消息给 AI（支持多轮对话 + 历史持久化）"""
    session_id = req.session_id or uuid.uuid4()

    # 1. 获取用户上下文
    context = await get_user_context(db, current_user)

    # 2. 加载历史对话
    history_messages = await _load_history(db, current_user.id, session_id)

    # 3. 组装消息
    messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n\n" + context}]
    messages.extend(history_messages)
    messages.append({"role": "user", "content": req.content})

    # 4. 调用 AI
    ai_response, tokens = await call_ai(messages)

    # 5. 持久化：保存用户消息
    user_msg = AiChatMessage(
        user_id=current_user.id,
        session_id=session_id,
        role="user",
        content=req.content,
    )
    db.add(user_msg)

    # 6. 持久化：保存 AI 回复
    model_used = "qwen-plus" if settings.DASHSCOPE_API_KEY else "builtin"
    ai_msg = AiChatMessage(
        user_id=current_user.id,
        session_id=session_id,
        role="assistant",
        content=ai_response,
        model_used=model_used,
        tokens_used=tokens,
    )
    db.add(ai_msg)
    await db.commit()

    return ChatResponse(
        id=ai_msg.id,
        role="assistant",
        content=ai_response,
        session_id=session_id,
        model_used=model_used,
        tokens_used=tokens,
        created_at=ai_msg.created_at,
    )


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


# ——— 内部辅助 ———


async def _load_history(
    db: AsyncSession, user_id: str, session_id: uuid.UUID
) -> list[dict]:
    """加载历史对话消息（最近 MAX_HISTORY_MESSAGES 条）"""
    result = await db.execute(
        select(AiChatMessage).where(
            AiChatMessage.user_id == user_id,
            AiChatMessage.session_id == session_id,
        ).order_by(desc(AiChatMessage.created_at)).limit(MAX_HISTORY_MESSAGES)
    )
    messages = list(reversed(result.scalars().all()))
    return [{"role": m.role, "content": m.content} for m in messages]

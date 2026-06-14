from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class ChatMessage(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000, description="消息内容")
    session_id: UUID | None = None


class ChatAction(BaseModel):
    type: str = Field(..., description="Action 类型: DIET_RECORD / PROFILE_UPDATE / MEAL_LINK")
    data: str = Field(..., description="Action 数据")


class ChatResponse(BaseModel):
    id: UUID
    role: str
    content: str
    session_id: UUID
    model_used: str | None
    tokens_used: int | None
    created_at: datetime
    actions: list[ChatAction] = []

    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    session_id: UUID
    messages: list[ChatResponse]
    created_at: datetime

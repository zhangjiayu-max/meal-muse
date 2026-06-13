from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID


class ChatMessage(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000, description="消息内容")
    session_id: UUID | None = None


class ChatResponse(BaseModel):
    id: UUID
    role: str
    content: str
    session_id: UUID
    model_used: str | None
    tokens_used: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    session_id: UUID
    messages: list[ChatResponse]
    created_at: datetime

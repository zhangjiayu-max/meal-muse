from pydantic import BaseModel, Field
from datetime import datetime, date
from uuid import UUID


class UserRegister(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$", description="手机号")
    nickname: str = Field(default="用户", max_length=50)


class UserLogin(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    code: str = Field(..., min_length=4, max_length=6, description="验证码")


class SendCodeRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")


class UserUpdate(BaseModel):
    nickname: str | None = None
    gender: str | None = None
    birthday: date | None = None
    height_cm: float | None = None
    current_weight: float | None = None
    target_weight: float | None = None
    activity_level: str | None = None
    preferences: dict | None = None


class UserResponse(BaseModel):
    id: UUID
    phone: str | None
    nickname: str
    avatar_url: str | None
    gender: str | None
    birthday: date | None
    height_cm: float | None
    current_weight: float | None
    target_weight: float | None
    activity_level: str
    preferences: dict | None
    daily_calorie_target: int | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

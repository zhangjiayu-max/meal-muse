"""身体指标相关 schema"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class BodyMetricCreate(BaseModel):
    height_cm: float = Field(..., ge=50, le=300, description="身高（厘米）")
    weight_kg: float = Field(..., ge=10, le=500, description="体重（千克）")
    age: int = Field(..., ge=1, le=150, description="年龄")
    gender: str = Field(..., pattern="^(male|female)$", description="性别：male/female")


class BodyMetricUpdate(BaseModel):
    height_cm: Optional[float] = Field(None, ge=50, le=300, description="身高（厘米）")
    weight_kg: Optional[float] = Field(None, ge=10, le=500, description="体重（千克）")
    age: Optional[int] = Field(None, ge=1, le=150, description="年龄")
    gender: Optional[str] = Field(None, pattern="^(male|female)$", description="性别")


class BodyMetricResponse(BaseModel):
    id: UUID
    user_id: UUID
    height_cm: float
    weight_kg: float
    age: int
    gender: str
    bmi: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

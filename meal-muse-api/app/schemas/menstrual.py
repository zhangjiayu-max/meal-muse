"""经期相关 schema"""
from datetime import date, datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class MenstrualCycleCreate(BaseModel):
    start_date: date = Field(..., description="经期开始日期")
    end_date: Optional[date] = Field(None, description="经期结束日期")
    symptoms: Optional[List[str]] = Field(default=[], description="症状列表")
    notes: Optional[str] = Field(None, max_length=500, description="备注")


class MenstrualCycleUpdate(BaseModel):
    end_date: Optional[date] = Field(None, description="经期结束日期")
    symptoms: Optional[List[str]] = Field(None, description="症状列表")
    notes: Optional[str] = Field(None, max_length=500, description="备注")


class MenstrualCycleResponse(BaseModel):
    id: UUID
    user_id: UUID
    start_date: date
    end_date: Optional[date] = None
    symptoms: List[str] = []
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MenstrualPhaseResponse(BaseModel):
    phase: str = Field(..., description="当前阶段：menstrual/follicular/ovulatory/luteal")
    day_in_cycle: int = Field(..., description="周期第几天")
    phase_description: str = Field(..., description="阶段说明")
    dietary_advice: Optional[str] = Field(None, description="饮食建议")

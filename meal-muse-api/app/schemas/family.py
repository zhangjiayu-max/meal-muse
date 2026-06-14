"""家庭共享相关 schema"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class FamilyGroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="家庭组名称")


class FamilyGroupResponse(BaseModel):
    id: UUID
    name: str
    owner_id: UUID
    member_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class FamilyMemberAdd(BaseModel):
    user_id: UUID = Field(..., description="成员用户 ID")
    relation: str = Field(..., max_length=20, description="关系：spouse/parent/child/other")


class FamilyMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    nickname: Optional[str] = None
    relation: str
    joined_at: datetime

    model_config = {"from_attributes": True}


class FamilyGroupDetail(FamilyGroupResponse):
    members: List[FamilyMemberResponse] = []

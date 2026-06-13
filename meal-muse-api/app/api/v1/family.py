import uuid
import random
import string
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.family import Family, FamilyMember

router = APIRouter(prefix="/family", tags=["家庭共享"])


class FamilyCreate(BaseModel):
    name: str = Field(..., max_length=100)


class FamilyJoin(BaseModel):
    invite_code: str


class MemberUpdate(BaseModel):
    relation: str | None = None
    display_name: str | None = None
    can_view_health: bool | None = None
    can_edit_plan: bool | None = None


class FamilyResponse(BaseModel):
    id: str
    name: str
    invite_code: str
    member_count: int
    members: list[dict]
    created_at: datetime

    class Config:
        from_attributes = True


def generate_invite_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


@router.post("/create", response_model=FamilyResponse)
async def create_family(
    req: FamilyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建家庭账户"""
    # 检查是否已有家庭
    result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.user_id == current_user.id,
            FamilyMember.status == "active",
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="你已经加入了一个家庭")

    invite_code = generate_invite_code()
    while True:
        existing = await db.execute(select(Family).where(Family.invite_code == invite_code))
        if not existing.scalar_one_or_none():
            break
        invite_code = generate_invite_code()

    family = Family(
        name=req.name,
        invite_code=invite_code,
        creator_id=current_user.id,
    )
    db.add(family)
    await db.flush()

    member = FamilyMember(
        family_id=family.id,
        user_id=current_user.id,
        role="owner",
        relation="self",
        display_name=current_user.nickname,
    )
    db.add(member)
    await db.commit()
    await db.refresh(family)

    return FamilyResponse(
        id=str(family.id),
        name=family.name,
        invite_code=family.invite_code,
        member_count=1,
        members=[{
            "user_id": str(current_user.id),
            "nickname": current_user.nickname,
            "role": "owner",
            "relation": "自己",
        }],
        created_at=family.created_at,
    )


@router.post("/join", response_model=FamilyResponse)
async def join_family(
    req: FamilyJoin,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """通过邀请码加入家庭"""
    result = await db.execute(
        select(Family).where(Family.invite_code == req.invite_code, Family.status == "active")
    )
    family = result.scalar_one_or_none()
    if not family:
        raise HTTPException(status_code=404, detail="邀请码无效")

    # 检查成员数
    members_result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.family_id == family.id,
            FamilyMember.status == "active",
        )
    )
    members = members_result.scalars().all()
    if len(members) >= family.max_members:
        raise HTTPException(status_code=400, detail="家庭成员已满")

    # 检查是否已在该家庭
    existing = [m for m in members if m.user_id == current_user.id]
    if existing:
        raise HTTPException(status_code=400, detail="你已经在该家庭中")

    member = FamilyMember(
        family_id=family.id,
        user_id=current_user.id,
        role="member",
        display_name=current_user.nickname,
    )
    db.add(member)
    await db.commit()

    # 返回家庭信息
    all_members_result = await db.execute(
        select(FamilyMember, User)
        .join(User, FamilyMember.user_id == User.id)
        .where(FamilyMember.family_id == family.id, FamilyMember.status == "active")
    )
    all_members = all_members_result.all()

    return FamilyResponse(
        id=str(family.id),
        name=family.name,
        invite_code=family.invite_code,
        member_count=len(all_members),
        members=[{
            "user_id": str(m.User.id),
            "nickname": m.User.nickname,
            "role": m.FamilyMember.role,
            "relation": m.FamilyMember.relation or "",
        } for m in all_members],
        created_at=family.created_at,
    )


@router.get("/my", response_model=FamilyResponse | None)
async def get_my_family(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取我的家庭信息"""
    result = await db.execute(
        select(FamilyMember, Family)
        .join(Family, FamilyMember.family_id == Family.id)
        .where(
            FamilyMember.user_id == current_user.id,
            FamilyMember.status == "active",
            Family.status == "active",
        )
    )
    row = result.first()
    if not row:
        return None

    family = row.Family

    members_result = await db.execute(
        select(FamilyMember, User)
        .join(User, FamilyMember.user_id == User.id)
        .where(FamilyMember.family_id == family.id, FamilyMember.status == "active")
    )
    all_members = members_result.all()

    return FamilyResponse(
        id=str(family.id),
        name=family.name,
        invite_code=family.invite_code,
        member_count=len(all_members),
        members=[{
            "user_id": str(m.User.id),
            "nickname": m.User.nickname,
            "role": m.FamilyMember.role,
            "relation": m.FamilyMember.relation or "",
        } for m in all_members],
        created_at=family.created_at,
    )


@router.delete("/members/{user_id}")
async def remove_member(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """移除家庭成员"""
    # 验证当前用户是 owner 或 admin
    result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.user_id == current_user.id,
            FamilyMember.status == "active",
        )
    )
    my_member = result.scalar_one_or_none()
    if not my_member or my_member.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="无权限")

    target_result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.family_id == my_member.family_id,
            FamilyMember.user_id == user_id,
            FamilyMember.status == "active",
        )
    )
    target = target_result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="成员不存在")

    target.status = "removed"
    await db.commit()
    return {"message": "已移除"}

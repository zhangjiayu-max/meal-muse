import uuid
import random
import string
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
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
    can_view_diet: bool | None = None
    can_view_body: bool | None = None
    can_view_menstrual: bool | None = None
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


@router.put("/members/{user_id}/privacy")
async def update_member_privacy(
    user_id: str,
    req: MemberUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新家庭成员的隐私权限"""
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

    # 更新权限
    if req.can_view_diet is not None:
        target.can_view_diet = req.can_view_diet
    if req.can_view_body is not None:
        target.can_view_body = req.can_view_body
    if req.can_view_menstrual is not None:
        target.can_view_menstrual = req.can_view_menstrual
    if req.can_view_health is not None:
        target.can_view_health = req.can_view_health
    if req.can_edit_plan is not None:
        target.can_edit_plan = req.can_edit_plan
    if req.relation is not None:
        target.relation = req.relation
    if req.display_name is not None:
        target.display_name = req.display_name

    await db.commit()
    return {"message": "权限已更新"}


@router.get("/members/{user_id}/diet")
async def get_member_diet(
    user_id: str,
    days: int = Query(default=7, le=30),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查看家庭成员的饮食记录"""
    # 验证权限
    permission = await _check_family_permission(db, current_user.id, user_id, "can_view_diet")
    if not permission:
        raise HTTPException(status_code=403, detail="无权限查看该成员的饮食记录")

    from datetime import date, timedelta
    from app.models.diet_record import DietRecord

    start_date = date.today() - timedelta(days=days)
    result = await db.execute(
        select(DietRecord).where(
            DietRecord.user_id == user_id,
            DietRecord.record_date >= start_date,
            DietRecord.deleted_at.is_(None),
        ).order_by(DietRecord.recorded_at.desc()).limit(50)
    )
    records = result.scalars().all()

    return {
        "user_id": user_id,
        "days": days,
        "records": [
            {
                "id": str(r.id),
                "meal_type": r.meal_type,
                "food_text": r.food_text,
                "total_calories": r.total_calories,
                "total_protein": float(r.total_protein) if r.total_protein else 0,
                "total_fat": float(r.total_fat) if r.total_fat else 0,
                "total_carbs": float(r.total_carbs) if r.total_carbs else 0,
                "record_date": r.record_date.isoformat(),
                "recorded_at": r.recorded_at.isoformat(),
            }
            for r in records
        ],
    }


@router.get("/members/{user_id}/body")
async def get_member_body(
    user_id: str,
    days: int = Query(default=30, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查看家庭成员的身体数据"""
    # 验证权限
    permission = await _check_family_permission(db, current_user.id, user_id, "can_view_body")
    if not permission:
        raise HTTPException(status_code=403, detail="无权限查看该成员的身体数据")

    from datetime import date, timedelta
    from app.models.body_metric import BodyMetric

    start_date = date.today() - timedelta(days=days)
    result = await db.execute(
        select(BodyMetric).where(
            BodyMetric.user_id == user_id,
            BodyMetric.metric_date >= start_date,
            BodyMetric.deleted_at.is_(None),
        ).order_by(BodyMetric.metric_date.desc()).limit(50)
    )
    metrics = result.scalars().all()

    return {
        "user_id": user_id,
        "days": days,
        "metrics": [
            {
                "id": str(m.id),
                "metric_date": m.metric_date.isoformat(),
                "weight": float(m.weight) if m.weight else None,
                "body_fat_pct": float(m.body_fat_pct) if m.body_fat_pct else None,
                "muscle_mass": float(m.muscle_mass) if m.muscle_mass else None,
                "bmi": float(m.bmi) if m.bmi else None,
                "blood_pressure_sys": m.blood_pressure_sys,
                "blood_pressure_dia": m.blood_pressure_dia,
                "blood_sugar": float(m.blood_sugar) if m.blood_sugar else None,
                "heart_rate": m.heart_rate,
                "sleep_hours": float(m.sleep_hours) if m.sleep_hours else None,
                "steps": m.steps,
            }
            for m in metrics
        ],
    }


@router.get("/members/{user_id}/menstrual")
async def get_member_menstrual(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查看家庭成员的经期状态"""
    # 验证权限
    permission = await _check_family_permission(db, current_user.id, user_id, "can_view_menstrual")
    if not permission:
        raise HTTPException(status_code=403, detail="无权限查看该成员的经期信息")

    from app.models.menstrual_cycle import MenstrualCycle

    # 获取最近的经期记录
    result = await db.execute(
        select(MenstrualCycle).where(
            MenstrualCycle.user_id == user_id,
        ).order_by(MenstrualCycle.period_start.desc()).limit(3)
    )
    cycles = result.scalars().all()

    # 计算当前阶段
    from datetime import date
    today = date.today()
    current_phase = None
    phase_tip = None

    if cycles:
        latest = cycles[0]
        if latest.period_start:
            if latest.period_end and latest.period_start <= today <= latest.period_end:
                current_phase = "menstrual"
                phase_tip = "月经期 - 需温补驱寒、补铁"
            elif latest.ovulation_day:
                days_from_ov = (today - latest.ovulation_day).days
                if 0 <= days_from_ov <= 2:
                    current_phase = "ovulation"
                    phase_tip = "排卵期 - 推荐促排卵食物"
                elif 3 <= days_from_ov <= 10:
                    current_phase = "luteal"
                    phase_tip = "黄体期 - 缓解PMS，推荐高蛋白"
            if not current_phase and latest.period_end and today > latest.period_end:
                cycle_day = (today - latest.period_start).days
                if 5 <= cycle_day <= 13:
                    current_phase = "follicular"
                    phase_tip = "卵泡期 - 推荐高蛋白、深色食物"

    return {
        "user_id": user_id,
        "current_phase": current_phase,
        "phase_tip": phase_tip,
        "cycles": [
            {
                "id": str(c.id),
                "period_start": c.period_start.isoformat() if c.period_start else None,
                "period_end": c.period_end.isoformat() if c.period_end else None,
                "cycle_length": c.cycle_length,
            }
            for c in cycles
        ],
    }


async def _check_family_permission(
    db: AsyncSession,
    viewer_id: str,
    target_user_id: str,
    permission_field: str,
) -> bool:
    """检查家庭成员权限"""
    # 查看者和被查看者是同一个人
    if str(viewer_id) == str(target_user_id):
        return True

    # 查找查看者的家庭成员信息
    viewer_result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.user_id == viewer_id,
            FamilyMember.status == "active",
        )
    )
    viewer_member = viewer_result.scalar_one_or_none()
    if not viewer_member:
        return False

    # 查找被查看者的家庭成员信息
    target_result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.family_id == viewer_member.family_id,
            FamilyMember.user_id == target_user_id,
            FamilyMember.status == "active",
        )
    )
    target_member = target_result.scalar_one_or_none()
    if not target_member:
        return False

    # 检查权限
    return getattr(target_member, permission_field, False)

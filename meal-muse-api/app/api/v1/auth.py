import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.user import SendCodeRequest, UserLogin, UserRegister, TokenResponse, UserResponse
from app.services.auth_service import send_verification_code, verify_code

router = APIRouter(prefix="/auth", tags=["认证"])

IS_DEV = os.getenv("ENV", "dev") == "dev"

DEV_PHONE = "13800000000"
DEV_NICKNAME = "开发测试用户"


@router.post("/send-code")
async def send_code(req: SendCodeRequest):
    """发送手机验证码"""
    await send_verification_code(req.phone)
    return {"message": "验证码已发送"}


@router.post("/register", response_model=TokenResponse)
async def register(req: UserRegister, db: AsyncSession = Depends(get_db)):
    """手机号注册"""
    existing = await db.execute(select(User).where(User.phone == req.phone, User.deleted_at.is_(None)))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该手机号已注册")

    user = User(phone=req.phone, nickname=req.nickname)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: UserLogin, db: AsyncSession = Depends(get_db)):
    """手机号 + 验证码登录"""
    if not await verify_code(req.phone, req.code):
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    result = await db.execute(select(User).where(User.phone == req.phone, User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()

    if not user:
        # 自动注册
        user = User(phone=req.phone, nickname=f"用户{req.phone[-4:]}")
        db.add(user)
        await db.commit()
        await db.refresh(user)

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/dev-auto-login", response_model=TokenResponse)
async def dev_auto_login(db: AsyncSession = Depends(get_db)):
    """开发环境自动登录（仅开发环境可用）"""
    if not IS_DEV:
        raise HTTPException(status_code=403, detail="仅开发环境可用")

    # 查找或创建开发用户
    result = await db.execute(select(User).where(User.phone == DEV_PHONE, User.deleted_at.is_(None)))
    user = result.scalar_one_or_none()

    if not user:
        # 创建开发用户
        user = User(
            phone=DEV_PHONE,
            nickname=DEV_NICKNAME,
            height_cm=170.0,
            current_weight=65.0,
            target_weight=60.0,
            activity_level="moderate",
            daily_calorie_target=1600,
            preferences={
                "diet_type": "balanced",
                "allergies": [],
                "dislikes": [],
                "cuisine_preferences": ["中式", "粤菜"],
            },
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )
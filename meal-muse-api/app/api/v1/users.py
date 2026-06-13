from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["用户"])


@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """获取当前用户资料"""
    return UserResponse.model_validate(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    req: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新用户资料"""
    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)
    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)

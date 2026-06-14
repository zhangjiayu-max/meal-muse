"""用户常用食物模型"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class UserFavoriteFood(Base):
    """用户常用食物"""
    __tablename__ = "user_favorite_foods"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    food_name: Mapped[str] = mapped_column(String(100))  # 食物名称
    meal_type: Mapped[str | None] = mapped_column(String(20))  # 适用餐次：breakfast/lunch/dinner/snack/any
    category: Mapped[str | None] = mapped_column(String(50))  # 分类：主食/肉类/蔬菜/水果/饮品等
    sort_order: Mapped[int] = mapped_column(Integer, default=0)  # 排序权重
    use_count: Mapped[int] = mapped_column(Integer, default=1)  # 使用次数
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # 最后使用时间
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "food_name", name="uq_user_favorite_food"),
    )

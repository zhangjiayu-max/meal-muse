import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Date, DECIMAL, Integer, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)
    wechat_openid: Mapped[str | None] = mapped_column(String(128), unique=True)
    nickname: Mapped[str] = mapped_column(String(50), default="用户")
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    gender: Mapped[str | None] = mapped_column(String(10))
    birthday: Mapped[datetime | None] = mapped_column(Date)
    height_cm: Mapped[float | None] = mapped_column(DECIMAL(5, 1))
    current_weight: Mapped[float | None] = mapped_column(DECIMAL(5, 1))
    target_weight: Mapped[float | None] = mapped_column(DECIMAL(5, 1))
    activity_level: Mapped[str] = mapped_column(String(20), default="moderate")
    preferences: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    daily_calorie_target: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="active")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

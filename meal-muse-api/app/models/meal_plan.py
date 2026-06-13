import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, Integer, Text, DateTime, Date, ForeignKey, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class MealPlan(Base):
    __tablename__ = "meal_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    plan_date: Mapped[date] = mapped_column(Date)
    breakfast: Mapped[dict | None] = mapped_column(JSONB)
    lunch: Mapped[dict | None] = mapped_column(JSONB)
    dinner: Mapped[dict | None] = mapped_column(JSONB)
    total_calories: Mapped[int] = mapped_column(Integer, default=0)
    total_protein: Mapped[float] = mapped_column(DECIMAL(8, 2), default=0)
    total_fat: Mapped[float] = mapped_column(DECIMAL(8, 2), default=0)
    total_carbs: Mapped[float] = mapped_column(DECIMAL(8, 2), default=0)
    ai_note: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    generate_params: Mapped[dict | None] = mapped_column(JSONB)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

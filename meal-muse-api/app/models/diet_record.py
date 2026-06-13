import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, Integer, Text, DateTime, Date, ForeignKey, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class DietRecord(Base):
    __tablename__ = "diet_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    meal_type: Mapped[str] = mapped_column(String(20))  # breakfast/lunch/dinner/snack
    food_text: Mapped[str] = mapped_column(Text)
    parsed_foods: Mapped[dict | None] = mapped_column(JSONB)
    total_calories: Mapped[int] = mapped_column(Integer, default=0)
    total_protein: Mapped[float] = mapped_column(DECIMAL(8, 2), default=0)
    total_fat: Mapped[float] = mapped_column(DECIMAL(8, 2), default=0)
    total_carbs: Mapped[float] = mapped_column(DECIMAL(8, 2), default=0)
    total_fiber: Mapped[float] = mapped_column(DECIMAL(8, 2), default=0)
    ai_analysis: Mapped[str | None] = mapped_column(Text)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    record_date: Mapped[date] = mapped_column(Date, index=True)
    meal_plan_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("meal_plans.id"))
    source: Mapped[str] = mapped_column(String(20), default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, Date, Integer, Text, DateTime, ForeignKey, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class HealthGoal(Base):
    __tablename__ = "health_goals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    goal_type: Mapped[str] = mapped_column(String(20))  # weight_loss/pregnancy/health/muscle_gain/custom
    target_weight: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    target_date: Mapped[date | None] = mapped_column(Date)
    weekly_loss_rate: Mapped[float | None] = mapped_column(DECIMAL(4, 2))
    daily_calorie_target: Mapped[int | None] = mapped_column(Integer)
    macro_targets: Mapped[dict | None] = mapped_column(JSONB)
    special_notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

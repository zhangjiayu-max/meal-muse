import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, Integer, Text, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ExerciseRecord(Base):
    __tablename__ = "exercise_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    exercise_date: Mapped[date] = mapped_column(Date)
    exercise_type: Mapped[str] = mapped_column(String(20))  # running/swimming/yoga/strength/walking/cycling/other
    duration_minutes: Mapped[int] = mapped_column(Integer)
    intensity: Mapped[str] = mapped_column(String(20), default="medium")  # low/medium/high
    calories_burned: Mapped[int | None] = mapped_column(Integer)  # nullable, can be auto-estimated
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

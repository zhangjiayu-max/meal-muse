import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, Integer, Text, DateTime, Date, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey
from app.core.database import Base


class MenstrualCycle(Base):
    __tablename__ = "menstrual_cycles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    period_start: Mapped[date] = mapped_column(Date, index=True)
    period_end: Mapped[date | None] = mapped_column(Date)
    cycle_length: Mapped[int | None] = mapped_column(Integer)
    period_length: Mapped[int | None] = mapped_column(Integer)
    ovulation_day: Mapped[date | None] = mapped_column(Date)
    fertile_window_start: Mapped[date | None] = mapped_column(Date)
    fertile_window_end: Mapped[date | None] = mapped_column(Date)
    symptoms: Mapped[list[str] | None] = mapped_column(ARRAY(Text), default=list)
    mood: Mapped[str | None] = mapped_column(String(20))
    flow_level: Mapped[str | None] = mapped_column(String(20))
    temperature: Mapped[float | None] = mapped_column(DECIMAL(4, 2))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

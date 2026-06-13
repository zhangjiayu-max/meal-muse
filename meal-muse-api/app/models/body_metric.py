import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, Integer, Float, Text, DateTime, Date, ForeignKey, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class BodyMetric(Base):
    __tablename__ = "body_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    metric_date: Mapped[date] = mapped_column(Date, default=date.today)
    weight: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    body_fat_pct: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    muscle_mass: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    bmi: Mapped[float | None] = mapped_column(DECIMAL(4, 2))
    waist_circum: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    blood_pressure_sys: Mapped[int | None] = mapped_column(Integer)
    blood_pressure_dia: Mapped[int | None] = mapped_column(Integer)
    blood_sugar: Mapped[float | None] = mapped_column(DECIMAL(5, 2))
    heart_rate: Mapped[int | None] = mapped_column(Integer)
    sleep_hours: Mapped[float | None] = mapped_column(DECIMAL(4, 2))
    water_ml: Mapped[int | None] = mapped_column(Integer)
    steps: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
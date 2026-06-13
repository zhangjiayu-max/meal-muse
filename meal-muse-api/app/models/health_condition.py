import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, Text, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class HealthCondition(Base):
    __tablename__ = "health_conditions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    condition_type: Mapped[str] = mapped_column(String(30))  # diabetes/hypertension/hyperlipidemia/gout/ulcer/kidney
    severity: Mapped[str] = mapped_column(String(20), default="mild")  # mild/moderate/severe
    diagnosed_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

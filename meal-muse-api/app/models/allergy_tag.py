import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class AllergyTag(Base):
    __tablename__ = "allergy_tags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    allergen: Mapped[str] = mapped_column(String(30))  # seafood/peanut/dairy/egg/gluten/soy/custom
    custom_name: Mapped[str | None] = mapped_column(String(50))  # for custom allergen
    reaction_level: Mapped[str] = mapped_column(String(20), default="mild")  # mild/moderate/severe/anaphylaxis
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

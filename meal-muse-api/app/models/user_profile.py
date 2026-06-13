import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    taste_preference: Mapped[str] = mapped_column(String(20), default="mild")  # mild/spicy_heavy/sweet/salty
    diet_type: Mapped[str] = mapped_column(String(20), default="normal")  # normal/vegetarian/vegan/keto/lowcarb/mediterranean
    cuisine_preference: Mapped[list | None] = mapped_column(JSONB, default=list)  # ["川菜", "粤菜", "日料"]
    disliked_foods: Mapped[list | None] = mapped_column(JSONB, default=list)
    cooking_method: Mapped[str] = mapped_column(String(20), default="simple")  # simple/medium/advanced
    cooking_facility: Mapped[str] = mapped_column(String(20), default="full_kitchen")  # full_kitchen/no_kitchen
    meal_pattern: Mapped[str] = mapped_column(String(20), default="3_meals")  # 3_meals/4_meals/5_meals
    sleep_pattern: Mapped[str] = mapped_column(String(20), default="early_bird")  # early_bird/night_owl
    care_targets: Mapped[list | None] = mapped_column(JSONB, default=list)  # ["elder", "baby", "none"]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

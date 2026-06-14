import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer
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
    budget_level: Mapped[str] = mapped_column(String(20), default="medium")  # low/medium/high
    meal_prep_time: Mapped[str] = mapped_column(String(20), default="30min")  # none/15min/30min/60min+
    water_intake_goal: Mapped[int | None] = mapped_column(Integer)  # 每日饮水目标(ml)

    # 新增画像增强字段
    constitution_types: Mapped[list | None] = mapped_column(JSONB, default=list)  # 体质类型 ["yang_deficiency", "qi_deficiency"]
    health_sub_goals: Mapped[list | None] = mapped_column(JSONB, default=list)  # 子目标 ["pregnancy_preparing", "early_pregnancy"]
    preferred_ingredients: Mapped[list | None] = mapped_column(JSONB, default=list)  # 偏好食材 ["鸡胸肉", "三文鱼"]
    cooking_frequency: Mapped[str] = mapped_column(String(20), default="often")  # often/sometimes/rarely/never
    takeout_preference: Mapped[str] = mapped_column(String(20), default="any")  # healthy_light/home_style/fast_food/any
    family_cooking: Mapped[bool] = mapped_column(default=False)  # 是否为家人做饭
    family_members: Mapped[list | None] = mapped_column(JSONB, default=list)  # 家庭成员 [{"name":"宝宝","relation":"child","age_group":"0-3","diet_note":"补钙"}]
    onboarding_version: Mapped[int] = mapped_column(Integer, default=2)  # 版本号

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

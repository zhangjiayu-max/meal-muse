"""add couple plan profile fields

Revision ID: 20260619_couple_plan
Revises:
Create Date: 2026-06-19
"""

from alembic import op


revision = "20260619_couple_plan"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS goal_priority VARCHAR(30) DEFAULT 'pregnancy_safe'")
    op.execute("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS partner_profile JSONB DEFAULT '{}'")
    op.execute("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS couple_plan_enabled BOOLEAN DEFAULT FALSE")


def downgrade() -> None:
    op.execute("ALTER TABLE user_profiles DROP COLUMN IF EXISTS couple_plan_enabled")
    op.execute("ALTER TABLE user_profiles DROP COLUMN IF EXISTS partner_profile")
    op.execute("ALTER TABLE user_profiles DROP COLUMN IF EXISTS goal_priority")

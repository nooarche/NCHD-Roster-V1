"""add groups and activities tables

Revision ID: 20251003_01
Revises: 
Create Date: 2025-10-03 08:10:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251003_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("rules", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )
    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("pattern", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )


def downgrade():
    op.drop_table("activities")
    op.drop_table("groups")

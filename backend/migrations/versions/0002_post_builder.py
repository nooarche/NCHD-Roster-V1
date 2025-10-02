# backend/migrations/versions/0002_post_builder.py
from alembic import op
import sqlalchemy as sa

revision = "0002_post_builder"
down_revision = "0001"   # adjust if your init revision differs
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("posts", sa.Column("site", sa.String(100), nullable=True))
    op.add_column("posts", sa.Column("grade", sa.String(32), nullable=True))
    op.add_column("posts", sa.Column("fte", sa.Float, server_default="1.0", nullable=False))
    op.add_column("posts", sa.Column("status", sa.String(32), server_default="ACTIVE_ROSTERABLE", nullable=False))
    op.add_column("posts", sa.Column("opd", sa.JSON, nullable=True))
    op.add_column("posts", sa.Column("teaching", sa.JSON, nullable=True))
    op.add_column("posts", sa.Column("supervision", sa.JSON, nullable=True))
    op.add_column("posts", sa.Column("core_hours", sa.JSON, nullable=True))
    op.add_column("posts", sa.Column("eligibility", sa.JSON, nullable=True))

    op.create_table(
        "vacancy_windows",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("post_id", sa.Integer, sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=True),
    )

def downgrade():
    op.drop_table("vacancy_windows")
    op.drop_column("posts", "eligibility")
    op.drop_column("posts", "core_hours")
    op.drop_column("posts", "supervision")
    op.drop_column("posts", "teaching")
    op.drop_column("posts", "opd")
    op.drop_column("posts", "status")
    op.drop_column("posts", "fte")
    op.drop_column("posts", "grade")
    op.drop_column("posts", "site")

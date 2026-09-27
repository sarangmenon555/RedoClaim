"""add is_preferred flag to appeals (version history selection)

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-09-27 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision: str = "f6a7b8c9d0e1"
down_revision = "e5f6a7b8c9d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Every /appeals/generate call already inserts a NEW row rather than
    # overwriting — so version history already exists implicitly as
    # multiple Appeal rows sharing (claim_id, appeal_type). This flag lets
    # the user mark which regenerated draft is the one they actually want
    # to use (for PDF export, submission tracking, etc.) without needing a
    # separate versions table.
    op.add_column("appeals", sa.Column("is_preferred", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("appeals", "is_preferred")

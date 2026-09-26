"""add patient_name and patient_relationship to claims

Revision ID: d4e5f6a7b8c9
Revises: c8d9e0f1a2b3
Create Date: 2026-09-26 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision: str = "d4e5f6a7b8c9"
down_revision = "c8d9e0f1a2b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Lets one account file/manage claims for a spouse, parent, or child
    # under a single login — a common pattern for family floater health
    # policies. NULL/blank patient_name means "the account holder
    # themselves", so this is fully backward-compatible with existing rows.
    op.add_column("claims", sa.Column("patient_name", sa.String(length=255), nullable=True))
    op.add_column("claims", sa.Column("patient_relationship", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("claims", "patient_relationship")
    op.drop_column("claims", "patient_name")

"""add network_hospitals table (crowdsourced hospital network verifier)

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-26 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None

hospital_network_status = postgresql.ENUM(
    "in_network", "delisted", "unknown", name="hospitalnetworkstatus", create_type=False
)


def upgrade() -> None:
    hospital_network_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "network_hospitals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("insurer_name", sa.String(length=255), nullable=False),
        sa.Column("hospital_name", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("status", hospital_network_status, nullable=False, server_default="unknown"),
        sa.Column("reported_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_network_hospitals_insurer_name", "network_hospitals", ["insurer_name"])
    op.create_index("ix_network_hospitals_hospital_name", "network_hospitals", ["hospital_name"])


def downgrade() -> None:
    op.drop_index("ix_network_hospitals_hospital_name", table_name="network_hospitals")
    op.drop_index("ix_network_hospitals_insurer_name", table_name="network_hospitals")
    op.drop_table("network_hospitals")
    hospital_network_status.drop(op.get_bind(), checkfirst=True)

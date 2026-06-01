"""add_motor_life_insurance_support

Revision ID: a1b2c3d4e5f6
Revises: fdbdc474a9f1
Create Date: 2026-06-01 00:00:00.000000

Adds:
  - InsuranceType.LIFE enum value
  - New DocumentType enum values for motor and life insurance documents
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'fdbdc474a9f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add LIFE to the InsuranceType enum
    op.execute("ALTER TYPE insurancetype ADD VALUE IF NOT EXISTS 'life'")

    # Add new motor insurance DocumentType values
    op.execute("ALTER TYPE documenttype ADD VALUE IF NOT EXISTS 'survey_report'")
    op.execute("ALTER TYPE documenttype ADD VALUE IF NOT EXISTS 'rc_book'")
    op.execute("ALTER TYPE documenttype ADD VALUE IF NOT EXISTS 'driving_licence'")
    op.execute("ALTER TYPE documenttype ADD VALUE IF NOT EXISTS 'fir'")
    op.execute("ALTER TYPE documenttype ADD VALUE IF NOT EXISTS 'repair_estimate'")

    # Add new life insurance DocumentType values
    op.execute("ALTER TYPE documenttype ADD VALUE IF NOT EXISTS 'death_certificate'")
    op.execute("ALTER TYPE documenttype ADD VALUE IF NOT EXISTS 'nominee_id'")
    op.execute("ALTER TYPE documenttype ADD VALUE IF NOT EXISTS 'medical_report'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values easily.
    # To fully downgrade, you would need to recreate the enum types.
    # This is intentionally left as a no-op for safety.
    pass

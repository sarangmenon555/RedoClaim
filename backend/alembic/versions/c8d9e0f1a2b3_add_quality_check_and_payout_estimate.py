"""add_quality_check_and_payout_estimate

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-09-13 00:00:00.000000

Adds:
  - documents.quality_ok — bool, whether the upload passed the local
    blur/resolution/OCR-completeness checks (quality_check.py)
  - documents.quality_issues — JSON list of human-readable quality
    warnings, e.g. "Image appears blurry", surfaced to the user right
    after upload rather than silently feeding bad input to the LLM
  - claims.payout_estimate — JSON cache of the last expected-payout
    estimate computed for this claim (payout_estimator.py), so the
    estimate persists on the claim view instead of being recomputed
    or lost on refresh
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8d9e0f1a2b3'
down_revision: Union[str, None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'documents',
        sa.Column('quality_ok', sa.Boolean(), nullable=True),
    )
    op.add_column(
        'documents',
        sa.Column('quality_issues', sa.JSON(), nullable=True),
    )
    op.add_column(
        'claims',
        sa.Column('payout_estimate', sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('claims', 'payout_estimate')
    op.drop_column('documents', 'quality_issues')
    op.drop_column('documents', 'quality_ok')

"""add_language_support

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-08-31 00:00:00.000000

Adds:
  - users.preferred_language — user's chosen UI/report language
    (en, hi, ml, ta, te, kn)
  - claims.translated_reports — JSON cache of Sarvam-translated audit
    reports keyed by language code, so repeat requests for the same
    claim/language don't re-hit the translation API
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column('preferred_language', sa.String(length=10), nullable=False, server_default='en'),
    )
    op.add_column(
        'claims',
        sa.Column('translated_reports', sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('claims', 'translated_reports')
    op.drop_column('users', 'preferred_language')

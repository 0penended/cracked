"""Remove confidence column from transaction_strategies table

Revision ID: 20251206220000
Revises: 20251206210017
Create Date: 2024-12-06 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251206220000'
down_revision = '20251206210017'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop confidence column from transaction_strategies table
    op.drop_column('transaction_strategies', 'confidence')


def downgrade() -> None:
    # Re-add confidence column (nullable for safety)
    op.add_column('transaction_strategies', sa.Column('confidence', sa.Float(), nullable=True))


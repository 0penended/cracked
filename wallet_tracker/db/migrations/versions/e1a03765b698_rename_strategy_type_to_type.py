"""rename strategy_type to type

Revision ID: e1a03765b698
Revises: abfe50f47de6
Create Date: 2024-01-15 10:35:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e1a03765b698"
down_revision = "abfe50f47de6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename strategy_type column to type
    op.alter_column("strategies", "strategy_type", new_column_name="type")


def downgrade() -> None:
    # Rename type column back to strategy_type
    op.alter_column("strategies", "type", new_column_name="strategy_type")

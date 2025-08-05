"""remove redundant name from strategies

Revision ID: abfe50f47de6
Revises: 0097fea9a403
Create Date: 2024-01-15 10:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "abfe50f47de6"
down_revision = "0097fea9a403"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove the redundant name column from strategies table
    op.drop_column("strategies", "name")


def downgrade() -> None:
    # Add back the name column (for rollback purposes)
    op.add_column("strategies", sa.Column("name", sa.String(), nullable=True))

"""convert token_ca to token_id

Revision ID: 8279a1e4697f
Revises: e3690e05cd94
Create Date: 2025-07-31 16:49:06.749195

"""

from alembic import op
import sqlalchemy as sa


revision = "8279a1e4697f"
down_revision = "e3690e05cd94"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename received_token_ca to received_token_id
    op.alter_column(
        "transactions", "received_token_ca", new_column_name="received_token_id"
    )

    # Rename spent_token_ca to spent_token_id
    op.alter_column("transactions", "spent_token_ca", new_column_name="spent_token_id")


def downgrade() -> None:
    # Rename received_token_id back to received_token_ca
    op.alter_column(
        "transactions", "received_token_id", new_column_name="received_token_ca"
    )

    # Rename spent_token_id back to spent_token_ca
    op.alter_column("transactions", "spent_token_id", new_column_name="spent_token_ca")

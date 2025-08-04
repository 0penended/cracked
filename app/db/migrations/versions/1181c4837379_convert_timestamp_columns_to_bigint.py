"""convert timestamp columns to bigint

Revision ID: 1181c4837379
Revises: ea849cacfc57
Create Date: 2025-08-03 22:54:31.445526

"""

from alembic import op
import sqlalchemy as sa


revision = "1181c4837379"
down_revision = "ea849cacfc57"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Convert timestamp columns from INTEGER to BIGINT to handle future Unix timestamps."""

    # Convert received_token_created_at from INTEGER to BIGINT
    op.alter_column(
        "transactions",
        "received_token_created_at",
        type_=sa.BigInteger(),
        existing_type=sa.Integer(),
        existing_nullable=True,
    )

    # Convert spent_token_created_at from INTEGER to BIGINT
    op.alter_column(
        "transactions",
        "spent_token_created_at",
        type_=sa.BigInteger(),
        existing_type=sa.Integer(),
        existing_nullable=True,
    )

    # Add comments to document the change
    op.execute(
        "COMMENT ON COLUMN transactions.received_token_created_at IS 'Token creation timestamp in seconds (Unix timestamp, BIGINT to handle future dates beyond 2038)'"
    )
    op.execute(
        "COMMENT ON COLUMN transactions.spent_token_created_at IS 'Token creation timestamp in seconds (Unix timestamp, BIGINT to handle future dates beyond 2038)'"
    )


def downgrade() -> None:
    """Convert timestamp columns back from BIGINT to INTEGER."""

    # Convert received_token_created_at back to INTEGER
    op.alter_column(
        "transactions",
        "received_token_created_at",
        type_=sa.Integer(),
        existing_type=sa.BigInteger(),
        existing_nullable=True,
    )

    # Convert spent_token_created_at back to INTEGER
    op.alter_column(
        "transactions",
        "spent_token_created_at",
        type_=sa.Integer(),
        existing_type=sa.BigInteger(),
        existing_nullable=True,
    )

    # Restore original comments
    op.execute(
        "COMMENT ON COLUMN transactions.received_token_created_at IS 'Token creation timestamp'"
    )
    op.execute(
        "COMMENT ON COLUMN transactions.spent_token_created_at IS 'Token creation timestamp'"
    )

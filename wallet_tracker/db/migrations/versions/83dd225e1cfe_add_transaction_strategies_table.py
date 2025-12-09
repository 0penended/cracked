"""add_transaction_strategies_table

Revision ID: 83dd225e1cfe
Revises: 1181c4837379
Create Date: 2025-08-04 15:53:42.459275

"""

from alembic import op
import sqlalchemy as sa


revision = "83dd225e1cfe"
down_revision = "1181c4837379"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create transaction_strategies table
    op.create_table(
        "transaction_strategies",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("transaction_id", sa.BigInteger(), nullable=False),
        sa.Column("strategy_type", sa.String(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("explanation", sa.String(), nullable=False),
        sa.Column("metadata", sa.String(), nullable=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["transaction_id"], ["transactions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create index on transaction_id for faster lookups
    op.create_index(
        "ix_transaction_strategies_transaction_id",
        "transaction_strategies",
        ["transaction_id"],
    )

    # Create index on strategy_type for analytics queries
    op.create_index(
        "ix_transaction_strategies_strategy_type",
        "transaction_strategies",
        ["strategy_type"],
    )

    # Create index on created_at for time-based queries
    op.create_index(
        "ix_transaction_strategies_created_at", "transaction_strategies", ["created_at"]
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(
        "ix_transaction_strategies_created_at", table_name="transaction_strategies"
    )
    op.drop_index(
        "ix_transaction_strategies_strategy_type", table_name="transaction_strategies"
    )
    op.drop_index(
        "ix_transaction_strategies_transaction_id", table_name="transaction_strategies"
    )

    # Drop table
    op.drop_table("transaction_strategies")

"""add_strategies_table

Revision ID: 0097fea9a403
Revises: 83dd225e1cfe
Create Date: 2025-08-04 16:15:42.459275

"""

from alembic import op
import sqlalchemy as sa


revision = "0097fea9a403"
down_revision = "83dd225e1cfe"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create strategies table
    op.create_table(
        "strategies",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("strategy_type", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("parameters", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create unique constraint on name to prevent duplicates
    op.create_unique_constraint("uq_strategies_name", "strategies", ["name"])

    # Create index on strategy_type for faster lookups
    op.create_index("ix_strategies_strategy_type", "strategies", ["strategy_type"])

    # Create index on is_active for filtering
    op.create_index("ix_strategies_is_active", "strategies", ["is_active"])

    # Update transaction_strategies table to use strategy_id instead of strategy_type
    # First, drop the old column
    op.drop_column("transaction_strategies", "strategy_type")

    # Add the new strategy_id column
    op.add_column(
        "transaction_strategies",
        sa.Column("strategy_id", sa.BigInteger(), nullable=False),
    )

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_transaction_strategies_strategy_id",
        "transaction_strategies",
        "strategies",
        ["strategy_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Create index on strategy_id for faster lookups
    op.create_index(
        "ix_transaction_strategies_strategy_id",
        "transaction_strategies",
        ["strategy_id"],
    )


def downgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint(
        "fk_transaction_strategies_strategy_id",
        "transaction_strategies",
        type_="foreignkey",
    )

    # Drop strategy_id column
    op.drop_column("transaction_strategies", "strategy_id")

    # Add back the old strategy_type column
    op.add_column(
        "transaction_strategies",
        sa.Column("strategy_type", sa.String(), nullable=False),
    )

    # Drop indexes
    op.drop_index(
        "ix_transaction_strategies_strategy_id", table_name="transaction_strategies"
    )
    op.drop_index("ix_strategies_is_active", table_name="strategies")
    op.drop_index("ix_strategies_strategy_type", table_name="strategies")
    op.drop_unique_constraint("uq_strategies_name", table_name="strategies")

    # Drop strategies table
    op.drop_table("strategies")

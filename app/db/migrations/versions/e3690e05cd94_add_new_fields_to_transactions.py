"""add new fields to transactions

Revision ID: e3690e05cd94
Revises: 
Create Date: 2025-07-30 22:47:19.579827

"""

from alembic import op
import sqlalchemy as sa


revision = "e3690e05cd94"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add new columns to transactions table to match UnifiedTransactionEvent."""

    # Add new columns to match UnifiedTransactionEvent
    op.add_column("transactions", sa.Column("chain", sa.Text, nullable=True))
    op.add_column("transactions", sa.Column("txn_hash", sa.Text, nullable=True))
    op.add_column("transactions", sa.Column("action", sa.Text, nullable=True))
    op.add_column(
        "transactions",
        sa.Column("received_token_volume_h24", sa.Numeric, nullable=True),
    )
    op.add_column(
        "transactions",
        sa.Column("received_token_price_change_h24", sa.Numeric, nullable=True),
    )
    op.add_column(
        "transactions", sa.Column("received_token_liquidity", sa.Numeric, nullable=True)
    )
    op.add_column(
        "transactions",
        sa.Column("received_token_created_at", sa.Integer, nullable=True),
    )
    op.add_column(
        "transactions", sa.Column("spent_token_volume_h24", sa.Numeric, nullable=True)
    )
    op.add_column(
        "transactions",
        sa.Column("spent_token_price_change_h24", sa.Numeric, nullable=True),
    )
    op.add_column(
        "transactions", sa.Column("spent_token_liquidity", sa.Numeric, nullable=True)
    )
    op.add_column(
        "transactions", sa.Column("spent_token_created_at", sa.Integer, nullable=True)
    )

    # Update existing records to set default values for new columns
    # Map existing 'type' field to 'action' field
    op.execute(
        """
        UPDATE transactions 
        SET 
            chain = 'solana',
            txn_hash = '',
            action = type,
            received_token_volume_h24 = 0,
            received_token_price_change_h24 = 0,
            received_token_liquidity = 0,
            received_token_created_at = 0,
            spent_token_volume_h24 = 0,
            spent_token_price_change_h24 = 0,
            spent_token_liquidity = 0,
            spent_token_created_at = 0
        WHERE chain IS NULL
    """
    )

    # Make new required columns NOT NULL after setting default values
    op.alter_column("transactions", "chain", nullable=False)
    op.alter_column("transactions", "txn_hash", nullable=False)
    op.alter_column("transactions", "action", nullable=False)

    # Add indexes for better query performance
    op.create_index("idx_transactions_chain", "transactions", ["chain"])
    op.create_index(
        "idx_transactions_wallet_address", "transactions", ["wallet_address"]
    )
    op.create_index("idx_transactions_action", "transactions", ["action"])
    op.create_index("idx_transactions_timestamp", "transactions", ["timestamp"])
    op.create_index("idx_transactions_txn_hash", "transactions", ["txn_hash"])

    # Add comments to document the new structure
    op.execute(
        "COMMENT ON COLUMN transactions.chain IS 'Blockchain name (e.g., solana, hyperliquid)'"
    )
    op.execute(
        "COMMENT ON COLUMN transactions.txn_hash IS 'Transaction hash from the blockchain'"
    )
    op.execute(
        "COMMENT ON COLUMN transactions.action IS 'Trade action (BUY, SELL, SWAP, OPEN_LONG, CLOSE_LONG, OPEN_SHORT, CLOSE_SHORT)'"
    )
    op.execute(
        "COMMENT ON COLUMN transactions.received_token_volume_h24 IS '24h trading volume for received token'"
    )
    op.execute(
        "COMMENT ON COLUMN transactions.received_token_price_change_h24 IS '24h price change percentage for received token'"
    )
    op.execute(
        "COMMENT ON COLUMN transactions.received_token_liquidity IS 'Liquidity/market cap for received token'"
    )
    op.execute(
        "COMMENT ON COLUMN transactions.received_token_created_at IS 'Token creation timestamp'"
    )
    op.execute(
        "COMMENT ON COLUMN transactions.spent_token_volume_h24 IS '24h trading volume for spent token'"
    )
    op.execute(
        "COMMENT ON COLUMN transactions.spent_token_price_change_h24 IS '24h price change percentage for spent token'"
    )
    op.execute(
        "COMMENT ON COLUMN transactions.spent_token_liquidity IS 'Liquidity/market cap for spent token'"
    )
    op.execute(
        "COMMENT ON COLUMN transactions.spent_token_created_at IS 'Token creation timestamp'"
    )


def downgrade() -> None:
    """Remove new columns from transactions table."""

    # Remove indexes
    op.drop_index("idx_transactions_txn_hash", "transactions")
    op.drop_index("idx_transactions_timestamp", "transactions")
    op.drop_index("idx_transactions_action", "transactions")
    op.drop_index("idx_transactions_wallet_address", "transactions")
    op.drop_index("idx_transactions_chain", "transactions")

    # Remove new columns
    op.drop_column("transactions", "spent_token_created_at")
    op.drop_column("transactions", "spent_token_liquidity")
    op.drop_column("transactions", "spent_token_price_change_h24")
    op.drop_column("transactions", "spent_token_volume_h24")
    op.drop_column("transactions", "received_token_created_at")
    op.drop_column("transactions", "received_token_liquidity")
    op.drop_column("transactions", "received_token_price_change_h24")
    op.drop_column("transactions", "received_token_volume_h24")
    op.drop_column("transactions", "action")
    op.drop_column("transactions", "txn_hash")
    op.drop_column("transactions", "chain")

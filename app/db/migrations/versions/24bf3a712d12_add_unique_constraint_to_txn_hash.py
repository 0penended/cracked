"""add_unique_constraint_to_txn_hash

Revision ID: 24bf3a712d12
Revises: e1a03765b698
Create Date: 2025-08-05 12:47:09.871754

"""

from alembic import op
import sqlalchemy as sa
import uuid


revision = "24bf3a712d12"
down_revision = "e1a03765b698"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add unique constraint to txn_hash field in transactions table."""

    # First, handle empty txn_hash values by generating unique IDs
    # Update records with empty txn_hash to have a generated unique ID
    op.execute(
        """
        UPDATE transactions 
        SET txn_hash = CONCAT('generated_', id, '_', EXTRACT(EPOCH FROM NOW())::bigint)
        WHERE txn_hash = '' OR txn_hash IS NULL
        """
    )

    # For any remaining duplicates, keep only the most recent record
    op.execute(
        """
        DELETE FROM transactions 
        WHERE id NOT IN (
            SELECT DISTINCT ON (txn_hash) id 
            FROM transactions 
            ORDER BY txn_hash, timestamp DESC
        )
        """
    )

    # Add unique constraint to txn_hash column
    op.create_unique_constraint(
        "uq_transactions_txn_hash", "transactions", ["txn_hash"]
    )

    # Add comment to document the constraint
    op.execute(
        "COMMENT ON CONSTRAINT uq_transactions_txn_hash ON transactions IS 'Ensures transaction hashes are unique across all chains'"
    )


def downgrade() -> None:
    """Remove unique constraint from txn_hash field in transactions table."""

    # Remove unique constraint
    op.drop_constraint("uq_transactions_txn_hash", "transactions", type_="unique")

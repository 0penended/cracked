"""update_transactions_table_for_unified_event

Revision ID: 84eba2d61e65
Revises: 20251206220000
Create Date: 2025-12-07 13:34:42.777229

"""
from alembic import op
import sqlalchemy as sa


revision = '84eba2d61e65'
down_revision = '20251206220000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Update transactions table to match UnifiedTransactionEvent structure."""
    conn = op.get_bind()
    
    # Get existing columns
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'transactions'
    """))
    existing_columns = {row[0] for row in result}
    
    # 1. Drop 'price' column if it exists (replaced by received_token_price, spent_token_price, transaction_value_usd)
    if 'price' in existing_columns:
        op.drop_column('transactions', 'price')
    
    # 2. Rename 'spent_token_amount' to 'spent_token_quantity' if it exists
    if 'spent_token_amount' in existing_columns and 'spent_token_quantity' not in existing_columns:
        op.alter_column('transactions', 'spent_token_amount', new_column_name='spent_token_quantity')
    
    # 3. Add 'received_token_price' if it doesn't exist
    if 'received_token_price' not in existing_columns:
        op.add_column('transactions', sa.Column('received_token_price', sa.Float(), nullable=False, server_default='0'))
    
    # 4. Add 'spent_token_price' if it doesn't exist
    if 'spent_token_price' not in existing_columns:
        op.add_column('transactions', sa.Column('spent_token_price', sa.Float(), nullable=False, server_default='0'))
    
    # 5. Add 'transaction_value_usd' if it doesn't exist
    if 'transaction_value_usd' not in existing_columns:
        op.add_column('transactions', sa.Column('transaction_value_usd', sa.Float(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Revert changes to transactions table."""
    conn = op.get_bind()
    
    # Get existing columns
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'transactions'
    """))
    existing_columns = {row[0] for row in result}
    
    # 1. Re-add 'price' column
    if 'price' not in existing_columns:
        op.add_column('transactions', sa.Column('price', sa.Float(), nullable=False, server_default='0'))
    
    # 2. Rename 'spent_token_quantity' back to 'spent_token_amount'
    if 'spent_token_quantity' in existing_columns and 'spent_token_amount' not in existing_columns:
        op.alter_column('transactions', 'spent_token_quantity', new_column_name='spent_token_amount')
    
    # 3. Drop new columns
    if 'received_token_price' in existing_columns:
        op.drop_column('transactions', 'received_token_price')
    
    if 'spent_token_price' in existing_columns:
        op.drop_column('transactions', 'spent_token_price')
    
    if 'transaction_value_usd' in existing_columns:
        op.drop_column('transactions', 'transaction_value_usd')

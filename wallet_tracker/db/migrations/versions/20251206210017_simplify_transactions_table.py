"""Simplify transactions table to match UnifiedTransactionEvent

Revision ID: YYYY_simplify_transactions
Revises: 24bf3a712d12
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251206210017'
down_revision = '24bf3a712d12'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old columns that are no longer needed
    # Using raw SQL to check existence first
    conn = op.get_bind()
    
    # Get existing columns
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'transactions'
    """))
    existing_columns = {row[0] for row in result}
    
    # Drop columns if they exist
    columns_to_drop = [
        'received_token_marketcap',
        'received_token_price',
        'received_token_volume_h24',
        'received_token_price_change_h24',
        'received_token_liquidity',
        'received_token_created_at',
        'spent_token_marketcap',
        'spent_token_price',
        'spent_token_volume_h24',
        'spent_token_price_change_h24',
        'spent_token_liquidity',
        'spent_token_created_at',
        'spent_token_quantity',
    ]
    
    for col in columns_to_drop:
        if col in existing_columns:
            op.drop_column('transactions', col)
    
    # Add new columns if they don't exist
    if 'received_token_quantity' not in existing_columns:
        op.add_column('transactions', sa.Column('received_token_quantity', sa.Float(), nullable=False, server_default='0'))
    
    if 'spent_token_amount' not in existing_columns:
        op.add_column('transactions', sa.Column('spent_token_amount', sa.Float(), nullable=False, server_default='0'))
    
    if 'price' not in existing_columns:
        op.add_column('transactions', sa.Column('price', sa.Float(), nullable=False, server_default='0'))
    
    if 'liquidation' not in existing_columns:
        op.add_column('transactions', sa.Column('liquidation', sa.Text(), nullable=True))
    
    if 'closed_pnl' not in existing_columns:
        op.add_column('transactions', sa.Column('closed_pnl', sa.Text(), nullable=True))
    
    # Ensure required columns are not null
    op.alter_column('transactions', 'received_token_symbol', nullable=False)
    op.alter_column('transactions', 'spent_token_symbol', nullable=False)


def downgrade() -> None:
    # Re-add old columns (with nullable for safety)
    op.add_column('transactions', sa.Column('received_token_marketcap', sa.Float(), nullable=True))
    op.add_column('transactions', sa.Column('received_token_price', sa.Float(), nullable=True))
    op.add_column('transactions', sa.Column('received_token_volume_h24', sa.Float(), nullable=True))
    op.add_column('transactions', sa.Column('received_token_price_change_h24', sa.Float(), nullable=True))
    op.add_column('transactions', sa.Column('received_token_liquidity', sa.Float(), nullable=True))
    op.add_column('transactions', sa.Column('received_token_created_at', sa.BigInteger(), nullable=True))
    op.add_column('transactions', sa.Column('spent_token_marketcap', sa.Float(), nullable=True))
    op.add_column('transactions', sa.Column('spent_token_price', sa.Float(), nullable=True))
    op.add_column('transactions', sa.Column('spent_token_volume_h24', sa.Float(), nullable=True))
    op.add_column('transactions', sa.Column('spent_token_price_change_h24', sa.Float(), nullable=True))
    op.add_column('transactions', sa.Column('spent_token_liquidity', sa.Float(), nullable=True))
    op.add_column('transactions', sa.Column('spent_token_created_at', sa.BigInteger(), nullable=True))
    op.add_column('transactions', sa.Column('spent_token_quantity', sa.Float(), nullable=True))
    
    # Remove new columns
    op.drop_column('transactions', 'received_token_quantity')
    op.drop_column('transactions', 'spent_token_amount')
    op.drop_column('transactions', 'price')
    op.drop_column('transactions', 'liquidation')
    op.drop_column('transactions', 'closed_pnl')


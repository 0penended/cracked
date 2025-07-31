import time

from app.db.repositories.transactions import TransactionsRepository
from app.models.domain.transactions import TransactionInDB
from app.models.schemas.transactions import TransactionInCreate


class TransactionsService:
    def __init__(self, transactions_repo: TransactionsRepository):
        self.transactions_repo = transactions_repo

    async def create_transaction(
        self,
        *,
        transaction_in: TransactionInCreate,
    ) -> TransactionInDB:
        # Use current timestamp if not provided
        timestamp = transaction_in.timestamp or int(time.time())

        transaction = await self.transactions_repo.create_transaction(
            wallet_address=transaction_in.wallet_address,
            chain=transaction_in.chain,
            txn_hash=transaction_in.txn_hash,
            action=transaction_in.action,
            timestamp=transaction_in.timestamp,
            received_token_id=transaction_in.received_token_id,
            received_token_marketcap=transaction_in.received_token_marketcap,
            received_token_price=transaction_in.received_token_price,
            received_token_quantity=transaction_in.received_token_quantity,
            received_token_symbol=transaction_in.received_token_symbol,
            received_token_volume_h24=transaction_in.received_token_volume_h24,
            received_token_price_change_h24=transaction_in.received_token_price_change_h24,
            received_token_liquidity=transaction_in.received_token_liquidity,
            received_token_created_at=transaction_in.received_token_created_at,
            spent_token_id=transaction_in.spent_token_id,
            spent_token_marketcap=transaction_in.spent_token_marketcap,
            spent_token_price=transaction_in.spent_token_price,
            spent_token_quantity=transaction_in.spent_token_quantity,
            spent_token_symbol=transaction_in.spent_token_symbol,
            spent_token_volume_h24=transaction_in.spent_token_volume_h24,
            spent_token_price_change_h24=transaction_in.spent_token_price_change_h24,
            spent_token_liquidity=transaction_in.spent_token_liquidity,
            spent_token_created_at=transaction_in.spent_token_created_at,
        )

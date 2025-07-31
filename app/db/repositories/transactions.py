from typing import Optional

from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.models.domain.transactions import TransactionInDB
from app.models.domain.blockchain import UnifiedTransactionEvent


class TransactionsRepository(BaseRepository):
    async def create_transaction(
        self,
        *,
        wallet_address: str,
        chain: str,
        txn_hash: str,
        action: str,
        timestamp: Optional[int] = None,
        received_token_ca: Optional[str] = None,
        received_token_marketcap: Optional[float] = None,
        received_token_price: Optional[float] = None,
        received_token_quantity: Optional[float] = None,
        received_token_symbol: Optional[str] = None,
        received_token_volume_h24: Optional[float] = None,
        received_token_price_change_h24: Optional[float] = None,
        received_token_liquidity: Optional[float] = None,
        received_token_created_at: Optional[int] = None,
        spent_token_ca: Optional[str] = None,
        spent_token_marketcap: Optional[float] = None,
        spent_token_price: Optional[float] = None,
        spent_token_quantity: Optional[float] = None,
        spent_token_symbol: Optional[str] = None,
        spent_token_volume_h24: Optional[float] = None,
        spent_token_price_change_h24: Optional[float] = None,
        spent_token_liquidity: Optional[float] = None,
        spent_token_created_at: Optional[int] = None,
    ) -> TransactionInDB:
        transaction = TransactionInDB(
            wallet_address=wallet_address,
            chain=chain,
            txn_hash=txn_hash,
            action=action,
            timestamp=timestamp,
            received_token_ca=received_token_ca,
            received_token_marketcap=received_token_marketcap,
            received_token_price=received_token_price,
            received_token_quantity=received_token_quantity,
            received_token_symbol=received_token_symbol,
            received_token_volume_h24=received_token_volume_h24,
            received_token_price_change_h24=received_token_price_change_h24,
            received_token_liquidity=received_token_liquidity,
            received_token_created_at=received_token_created_at,
            spent_token_ca=spent_token_ca,
            spent_token_marketcap=spent_token_marketcap,
            spent_token_price=spent_token_price,
            spent_token_quantity=spent_token_quantity,
            spent_token_symbol=spent_token_symbol,
            spent_token_volume_h24=spent_token_volume_h24,
            spent_token_price_change_h24=spent_token_price_change_h24,
            spent_token_liquidity=spent_token_liquidity,
            spent_token_created_at=spent_token_created_at,
        )

        async with self.connection.transaction():
            transaction_row = await queries.create_new_transaction(
                self.connection,
                wallet_address=transaction.wallet_address,
                chain=transaction.chain,
                txn_hash=transaction.txn_hash,
                action=transaction.action,
                timestamp=transaction.timestamp,
                received_token_ca=transaction.received_token_ca,
                received_token_marketcap=transaction.received_token_marketcap,
                received_token_price=transaction.received_token_price,
                received_token_quantity=transaction.received_token_quantity,
                received_token_symbol=transaction.received_token_symbol,
                received_token_volume_h24=transaction.received_token_volume_h24,
                received_token_price_change_h24=transaction.received_token_price_change_h24,
                received_token_liquidity=transaction.received_token_liquidity,
                received_token_created_at=transaction.received_token_created_at,
                spent_token_ca=transaction.spent_token_ca,
                spent_token_marketcap=transaction.spent_token_marketcap,
                spent_token_price=transaction.spent_token_price,
                spent_token_quantity=transaction.spent_token_quantity,
                spent_token_symbol=transaction.spent_token_symbol,
                spent_token_volume_h24=transaction.spent_token_volume_h24,
                spent_token_price_change_h24=transaction.spent_token_price_change_h24,
                spent_token_liquidity=transaction.spent_token_liquidity,
                spent_token_created_at=transaction.spent_token_created_at,
            )

        return transaction.copy(update=dict(transaction_row))

    async def create_from_unified_event(
        self, event: UnifiedTransactionEvent
    ) -> TransactionInDB:
        """Create a transaction from a UnifiedTransactionEvent."""
        return await self.create_transaction(
            wallet_address=event.wallet,
            chain=event.chain,
            txn_hash=event.tx_hash,
            action=event.action.value,
            timestamp=event.timestamp,
            received_token_ca=None,  # Not available in UnifiedTransactionEvent
            received_token_marketcap=None,  # Not available in UnifiedTransactionEvent
            received_token_price=event.recieved_price,
            received_token_quantity=event.recieved_amount,
            received_token_symbol=event.recieved_symbol,
            received_token_volume_h24=event.recieved_volume_h24,
            received_token_price_change_h24=event.recieved_price_change_h24,
            received_token_liquidity=event.recieved_liquidity,
            received_token_created_at=event.recieved_created_at,
            spent_token_ca=None,  # Not available in UnifiedTransactionEvent
            spent_token_marketcap=None,  # Not available in UnifiedTransactionEvent
            spent_token_price=event.spent_price,
            spent_token_quantity=event.spent_amount,
            spent_token_symbol=event.spent_symbol,
            spent_token_volume_h24=event.spent_volume_h24,
            spent_token_price_change_h24=event.spent_price_change_h24,
            spent_token_liquidity=event.spent_liquidity,
            spent_token_created_at=event.spent_created_at,
        )

import asyncpg
from typing import List, Optional
from loguru import logger
from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.models.domain.transactions import TransactionInDB
from app.models.domain.blockchain import UnifiedTransactionEvent


class TransactionsRepository(BaseRepository):
    async def create_transaction(
        self,
        wallet_address: str,
        chain: str,
        txn_hash: str,
        action: str,
        timestamp: int,
        received_token_id: Optional[str] = None,
        received_token_marketcap: Optional[float] = None,
        received_token_price: Optional[float] = None,
        received_token_quantity: Optional[float] = None,
        received_token_symbol: Optional[str] = None,
        received_token_volume_h24: Optional[float] = None,
        received_token_price_change_h24: Optional[float] = None,
        received_token_liquidity: Optional[float] = None,
        received_token_created_at: Optional[int] = None,
        spent_token_id: Optional[str] = None,
        spent_token_marketcap: Optional[float] = None,
        spent_token_price: Optional[float] = None,
        spent_token_quantity: Optional[float] = None,
        spent_token_symbol: Optional[str] = None,
        spent_token_volume_h24: Optional[float] = None,
        spent_token_price_change_h24: Optional[float] = None,
        spent_token_liquidity: Optional[float] = None,
        spent_token_created_at: Optional[int] = None,
    ) -> TransactionInDB:
        """Create a new transaction in the database."""
        transaction = TransactionInDB(
            action=action,
            chain=chain,
            txn_hash=txn_hash,
            received_token_created_at=received_token_created_at,
            received_token_id=received_token_id,
            received_token_liquidity=received_token_liquidity,
            received_token_marketcap=received_token_marketcap,
            received_token_price=received_token_price,
            received_token_price_change_h24=received_token_price_change_h24,
            received_token_quantity=received_token_quantity,
            received_token_symbol=received_token_symbol,
            received_token_volume_h24=received_token_volume_h24,
            spent_token_created_at=spent_token_created_at,
            spent_token_id=spent_token_id,
            spent_token_liquidity=spent_token_liquidity,
            spent_token_marketcap=spent_token_marketcap,
            spent_token_price=spent_token_price,
            spent_token_price_change_h24=spent_token_price_change_h24,
            spent_token_quantity=spent_token_quantity,
            spent_token_symbol=spent_token_symbol,
            spent_token_volume_h24=spent_token_volume_h24,
            timestamp=timestamp,
            wallet_address=wallet_address,
        )
        conn = await self.get_connection()
        try:
            async with conn.transaction():
                transaction_row = await queries.create_new_transaction(
                    conn,
                    wallet_address=transaction.wallet_address,
                    chain=transaction.chain,
                    txn_hash=transaction.txn_hash,
                    action=transaction.action,
                    timestamp=transaction.timestamp,
                    received_token_id=transaction.received_token_id,
                    received_token_marketcap=transaction.received_token_marketcap,
                    received_token_price=transaction.received_token_price,
                    received_token_quantity=transaction.received_token_quantity,
                    received_token_symbol=transaction.received_token_symbol,
                    received_token_volume_h24=transaction.received_token_volume_h24,
                    received_token_price_change_h24=transaction.received_token_price_change_h24,
                    received_token_liquidity=transaction.received_token_liquidity,
                    received_token_created_at=transaction.received_token_created_at,
                    spent_token_id=transaction.spent_token_id,
                    spent_token_marketcap=transaction.spent_token_marketcap,
                    spent_token_price=transaction.spent_token_price,
                    spent_token_quantity=transaction.spent_token_quantity,
                    spent_token_symbol=transaction.spent_token_symbol,
                    spent_token_volume_h24=transaction.spent_token_volume_h24,
                    spent_token_price_change_h24=transaction.spent_token_price_change_h24,
                    spent_token_liquidity=transaction.spent_token_liquidity,
                    spent_token_created_at=transaction.spent_token_created_at,
                )

            # Add the database ID to the transaction object
            record_dict = transaction_row[0]
            transaction.id_ = record_dict["id"]
            return transaction
        finally:
            await self.release_connection(conn)

    async def create_from_unified_event(
        self, event: UnifiedTransactionEvent
    ) -> TransactionInDB:
        """Create a transaction from a UnifiedTransactionEvent."""
        return await self.create_transaction(
            wallet_address=event.wallet_address,
            chain=event.chain,
            txn_hash=event.txn_hash,
            action=event.action.value,
            timestamp=event.timestamp,
            received_token_id=event.received_token_id,
            received_token_marketcap=event.received_token_marketcap,
            received_token_price=event.received_token_price,
            received_token_quantity=event.received_token_quantity,
            received_token_symbol=event.received_token_symbol,
            received_token_volume_h24=event.received_token_volume_h24,
            received_token_price_change_h24=event.received_token_price_change_h24,
            received_token_liquidity=event.received_token_liquidity,
            received_token_created_at=event.received_token_created_at,
            spent_token_id=event.spent_token_id,
            spent_token_marketcap=event.spent_token_marketcap,
            spent_token_price=event.spent_token_price,
            spent_token_quantity=event.spent_token_amount,
            spent_token_symbol=event.spent_token_symbol,
            spent_token_volume_h24=event.spent_token_volume_h24,
            spent_token_price_change_h24=event.spent_token_price_change_h24,
            spent_token_liquidity=event.spent_token_liquidity,
            spent_token_created_at=event.spent_token_created_at,
        )

    async def transaction_exists(self, txn_hash: str) -> bool:
        """Check if a transaction already exists in the database."""
        conn = await self.get_connection()
        try:
            result = await queries.check_transaction_exists(conn, txn_hash=txn_hash)
            # Log the actual result to debug
            # aiosql returns arrays - check if array has any elements
            exists = result is not None and len(result) > 0
            logger.info(f"Transaction {txn_hash} exists: {exists}")
            return exists
        except Exception as e:
            logger.error(f"❌ Error checking if transaction exists: {e}")
            raise
        finally:
            await self.release_connection(conn)

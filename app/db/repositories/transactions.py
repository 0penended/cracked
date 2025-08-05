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
        async with self.connection.transaction():
            print("!!!!TRANSACTION!!!!")
            print(received_token_price)
            print(spent_token_price)
            transaction_row = await queries.create_new_transaction(
                self.connection,
                wallet_address=wallet_address,
                chain=chain,
                txn_hash=txn_hash,
                action=action,
                timestamp=timestamp,
                received_token_id=received_token_id,
                received_token_marketcap=received_token_marketcap,
                received_token_price=received_token_price,
                received_token_quantity=received_token_quantity,
                received_token_symbol=received_token_symbol,
                received_token_volume_h24=received_token_volume_h24,
                received_token_price_change_h24=received_token_price_change_h24,
                received_token_liquidity=received_token_liquidity,
                received_token_created_at=received_token_created_at,
                spent_token_id=spent_token_id,
                spent_token_marketcap=spent_token_marketcap,
                spent_token_price=spent_token_price,
                spent_token_quantity=spent_token_quantity,
                spent_token_symbol=spent_token_symbol,
                spent_token_volume_h24=spent_token_volume_h24,
                spent_token_price_change_h24=spent_token_price_change_h24,
                spent_token_liquidity=spent_token_liquidity,
                spent_token_created_at=spent_token_created_at,
            )

        # Map database fields to model fields
        record_dict = transaction_row[0]
        return TransactionInDB(
            id_=record_dict["id"],
            wallet_address=record_dict["wallet_address"],
            chain=record_dict["chain"],
            txn_hash=record_dict["txn_hash"],
            action=record_dict["action"],
            timestamp=record_dict["timestamp"],
            received_token_id=record_dict.get("received_token_id"),
            received_token_marketcap=record_dict.get("received_token_marketcap"),
            received_token_price=record_dict.get("received_token_price"),
            received_token_quantity=record_dict.get("received_token_quantity"),
            received_token_symbol=record_dict.get("received_token_symbol"),
            received_token_volume_h24=record_dict.get("received_token_volume_h24"),
            received_token_price_change_h24=record_dict.get(
                "received_token_price_change_h24"
            ),
            received_token_liquidity=record_dict.get("received_token_liquidity"),
            received_token_created_at=record_dict.get("received_token_created_at"),
            spent_token_id=record_dict.get("spent_token_id"),
            spent_token_marketcap=record_dict.get("spent_token_marketcap"),
            spent_token_price=record_dict.get("spent_token_price"),
            spent_token_quantity=record_dict.get("spent_token_quantity"),
            spent_token_symbol=record_dict.get("spent_token_symbol"),
            spent_token_volume_h24=record_dict.get("spent_token_volume_h24"),
            spent_token_price_change_h24=record_dict.get(
                "spent_token_price_change_h24"
            ),
            spent_token_liquidity=record_dict.get("spent_token_liquidity"),
            spent_token_created_at=record_dict.get("spent_token_created_at"),
        )

    async def create_from_unified_event(
        self, event: UnifiedTransactionEvent
    ) -> TransactionInDB:
        """Create a transaction from a UnifiedTransactionEvent."""
        logger.info(f"💾 Creating transaction from event: {event.txn_hash}")
        logger.info(f"Event details: {event.action} on {event.chain}")
        print("!!!!EVENT!!!!")
        print(event)
        print(event.received_token_price)

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
        logger.info(f"🔍 Checking if transaction exists: {txn_hash}")
        try:
            result = await queries.check_transaction_exists(
                self.connection, txn_hash=txn_hash
            )
            # Log the actual result to debug
            logger.info(f"Raw result type: {type(result)}, value: {result}")
            # aiosql returns arrays - check if array has any elements
            exists = result is not None and len(result) > 0
            logger.info(f"Transaction {txn_hash} exists: {exists}")
            return exists
        except Exception as e:
            logger.error(f"❌ Error checking if transaction exists: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

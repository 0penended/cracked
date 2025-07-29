from typing import Optional

from app.db.queries.queries import queries
from app.db.repositories.base import BaseRepository
from app.models.domain.transactions import TransactionInDB


class TransactionsRepository(BaseRepository):
    async def create_transaction(
        self,
        *,
        wallet_address: str,
        transaction_type: str,
        timestamp: Optional[int] = None,
        received_token_ca: Optional[str] = None,
        received_token_marketcap: Optional[float] = None,
        received_token_price: Optional[float] = None,
        received_token_quantity: Optional[float] = None,
        received_token_symbol: Optional[str] = None,
        spent_token_ca: Optional[str] = None,
        spent_token_marketcap: Optional[float] = None,
        spent_token_price: Optional[float] = None,
        spent_token_quantity: Optional[float] = None,
        spent_token_symbol: Optional[str] = None,
    ) -> TransactionInDB:
        transaction = TransactionInDB(
            wallet_address=wallet_address,
            type=transaction_type,
            timestamp=timestamp,
            received_token_ca=received_token_ca,
            received_token_marketcap=received_token_marketcap,
            received_token_price=received_token_price,
            received_token_quantity=received_token_quantity,
            received_token_symbol=received_token_symbol,
            spent_token_ca=spent_token_ca,
            spent_token_marketcap=spent_token_marketcap,
            spent_token_price=spent_token_price,
            spent_token_quantity=spent_token_quantity,
            spent_token_symbol=spent_token_symbol,
        )

        async with self.connection.transaction():
            transaction_row = await queries.create_new_transaction(
                self.connection,
                wallet_address=transaction.wallet_address,
                type=transaction.type,
                timestamp=transaction.timestamp,
                received_token_ca=transaction.received_token_ca,
                received_token_marketcap=transaction.received_token_marketcap,
                received_token_price=transaction.received_token_price,
                received_token_quantity=transaction.received_token_quantity,
                received_token_symbol=transaction.received_token_symbol,
                spent_token_ca=transaction.spent_token_ca,
                spent_token_marketcap=transaction.spent_token_marketcap,
                spent_token_price=transaction.spent_token_price,
                spent_token_quantity=transaction.spent_token_quantity,
                spent_token_symbol=transaction.spent_token_symbol,
            )

        return transaction.copy(update=dict(transaction_row))
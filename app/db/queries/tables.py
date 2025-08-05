from typing import Optional

from pypika import Parameter as Query, Table


class TypedTable(Table):
    __table__ = ""

    def __init__(
        self,
        name: Optional[str] = None,
        schema: Optional[str] = None,
        alias: Optional[str] = None,
        query_cls: Optional[Query] = None,
    ) -> None:
        if name is None:
            if self.__table__:
                name = self.__table__
            else:
                name = self.__class__.__name__

        super().__init__(name, schema, alias, query_cls)


class Transactions(TypedTable):
    __table__ = "transactions"

    id: int
    wallet_address: str
    chain: str
    txn_hash: str
    action: str
    timestamp: int
    received_token_id: Optional[str]
    received_token_marketcap: Optional[float]
    received_token_price: Optional[float]
    received_token_quantity: Optional[float]
    received_token_symbol: Optional[str]
    received_token_volume_h24: Optional[float]
    received_token_price_change_h24: Optional[float]
    received_token_liquidity: Optional[float]
    received_token_created_at: Optional[int]  # BIGINT in database, int in Python
    spent_token_id: Optional[str]
    spent_token_marketcap: Optional[float]
    spent_token_price: Optional[float]
    spent_token_quantity: Optional[float]
    spent_token_symbol: Optional[str]
    spent_token_volume_h24: Optional[float]
    spent_token_price_change_h24: Optional[float]
    spent_token_liquidity: Optional[float]
    spent_token_created_at: Optional[int]  # BIGINT in database, int in Python


class Strategies(TypedTable):
    __table__ = "strategies"

    id: int
    name: str
    strategy_type: str  # Enum value from Strategy enum
    description: str
    parameters: Optional[str]  # JSON string of strategy parameters
    is_active: bool
    created_at: int  # BIGINT timestamp


class TransactionStrategies(TypedTable):
    __table__ = "transaction_strategies"

    id: int
    transaction_id: int
    strategy_id: int
    confidence: float
    explanation: str
    metadata: Optional[str]  # JSON string
    created_at: int  # BIGINT timestamp


transactions = Transactions()
strategies = Strategies()
transaction_strategies = TransactionStrategies()

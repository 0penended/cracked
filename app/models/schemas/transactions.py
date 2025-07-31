from typing import Optional

from pydantic import BaseModel

from app.models.domain.transactions import Transaction
from app.models.schemas.rwschema import RWSchema


class TransactionInCreate(BaseModel):
    wallet_address: str
    chain: str
    txn_hash: str
    action: str
    timestamp: Optional[int] = None
    received_token_id: Optional[str] = None
    received_token_marketcap: Optional[float] = None
    received_token_price: Optional[float] = None
    received_token_quantity: Optional[float] = None
    received_token_symbol: Optional[str] = None
    received_token_volume_h24: Optional[float] = None
    received_token_price_change_h24: Optional[float] = None
    received_token_liquidity: Optional[float] = None
    received_token_created_at: Optional[int] = None
    spent_token_id: Optional[str] = None
    spent_token_marketcap: Optional[float] = None
    spent_token_price: Optional[float] = None
    spent_token_quantity: Optional[float] = None
    spent_token_symbol: Optional[str] = None
    spent_token_volume_h24: Optional[float] = None
    spent_token_price_change_h24: Optional[float] = None
    spent_token_liquidity: Optional[float] = None
    spent_token_created_at: Optional[int] = None


class TransactionInUpdate(BaseModel):
    wallet_address: Optional[str] = None
    type: Optional[str] = None
    timestamp: Optional[int] = None
    received_token_id: Optional[str] = None
    received_token_marketcap: Optional[float] = None
    received_token_price: Optional[float] = None
    received_token_quantity: Optional[float] = None
    received_token_symbol: Optional[str] = None
    spent_token_id: Optional[str] = None
    spent_token_marketcap: Optional[float] = None
    spent_token_price: Optional[float] = None
    spent_token_quantity: Optional[float] = None
    spent_token_symbol: Optional[str] = None


class TransactionInResponse(RWSchema):
    transaction: Transaction


class TransactionListInResponse(RWSchema):
    transactions: list[Transaction]
    transactions_count: int

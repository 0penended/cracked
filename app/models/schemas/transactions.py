from typing import Optional

from pydantic import BaseModel

from app.models.domain.transactions import Transaction
from app.models.schemas.rwschema import RWSchema


class TransactionInCreate(RWSchema):
    wallet_address: str
    type: str
    timestamp: Optional[int] = None
    received_token_ca: Optional[str] = None
    received_token_marketcap: Optional[float] = None
    received_token_price: Optional[float] = None
    received_token_quantity: Optional[float] = None
    received_token_symbol: Optional[str] = None
    spent_token_ca: Optional[str] = None
    spent_token_marketcap: Optional[float] = None
    spent_token_price: Optional[float] = None
    spent_token_quantity: Optional[float] = None
    spent_token_symbol: Optional[str] = None


class TransactionInUpdate(BaseModel):
    wallet_address: Optional[str] = None
    type: Optional[str] = None
    timestamp: Optional[int] = None
    received_token_ca: Optional[str] = None
    received_token_marketcap: Optional[float] = None
    received_token_price: Optional[float] = None
    received_token_quantity: Optional[float] = None
    received_token_symbol: Optional[str] = None
    spent_token_ca: Optional[str] = None
    spent_token_marketcap: Optional[float] = None
    spent_token_price: Optional[float] = None
    spent_token_quantity: Optional[float] = None
    spent_token_symbol: Optional[str] = None


class TransactionInResponse(RWSchema):
    transaction: Transaction


class TransactionListInResponse(RWSchema):
    transactions: list[Transaction]
    transactions_count: int 
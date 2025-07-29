from typing import Optional

from pydantic import validator

from app.models.common import IDModelMixin
from app.models.domain.rwmodel import RWModel


class Transaction(RWModel):
    wallet_address: str
    type: str
    timestamp: int
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

    @validator('type')
    def validate_transaction_type(cls, v):
        allowed_types = ['BUY', 'SELL', 'SWAP']
        if v not in allowed_types:
            raise ValueError(f'Transaction type must be one of: {allowed_types}')
        return v


class TransactionInDB(IDModelMixin, Transaction):
    pass 
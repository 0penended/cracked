from typing import Optional

from pydantic import validator

from app.models.common import IDModelMixin
from app.models.domain.rwmodel import RWModel


class Transaction(RWModel):
    wallet_address: str
    chain: str
    txn_hash: str
    action: str
    timestamp: int
    received_token_ca: Optional[str] = None
    received_token_marketcap: Optional[float] = None
    received_token_price: Optional[float] = None
    received_token_quantity: Optional[float] = None
    received_token_symbol: Optional[str] = None
    received_token_volume_h24: Optional[float] = None
    received_token_price_change_h24: Optional[float] = None
    received_token_liquidity: Optional[float] = None
    received_token_created_at: Optional[int] = None
    spent_token_ca: Optional[str] = None
    spent_token_marketcap: Optional[float] = None
    spent_token_price: Optional[float] = None
    spent_token_quantity: Optional[float] = None
    spent_token_symbol: Optional[str] = None
    spent_token_volume_h24: Optional[float] = None
    spent_token_price_change_h24: Optional[float] = None
    spent_token_liquidity: Optional[float] = None
    spent_token_created_at: Optional[int] = None

    @validator("action")
    def validate_action(cls, v):
        allowed_actions = [
            "BUY",
            "SELL",
            "SWAP",
            "OPEN_LONG",
            "CLOSE_LONG",
            "OPEN_SHORT",
            "CLOSE_SHORT",
        ]
        if v not in allowed_actions:
            raise ValueError(f"Action must be one of: {allowed_actions}")
        return v


class TransactionInDB(IDModelMixin, Transaction):
    pass

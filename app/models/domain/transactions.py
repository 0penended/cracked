from typing import Optional, Dict, Any
import json

from pydantic import validator

from app.models.common import IDModelMixin
from app.models.domain.rwmodel import RWModel


class Transaction(RWModel):
    action: str
    chain: str
    received_token_created_at: Optional[int] = None
    received_token_id: Optional[str] = None
    received_token_liquidity: Optional[float] = None
    received_token_marketcap: Optional[float] = None
    received_token_price: Optional[float] = None
    received_token_price_change_h24: Optional[float] = None
    received_token_quantity: Optional[float] = None
    received_token_symbol: Optional[str] = None
    received_token_volume_h24: Optional[float] = None
    spent_token_created_at: Optional[int] = None
    spent_token_id: Optional[str] = None
    spent_token_liquidity: Optional[float] = None
    spent_token_marketcap: Optional[float] = None
    spent_token_price: Optional[float] = None
    spent_token_price_change_h24: Optional[float] = None
    spent_token_quantity: Optional[float] = None
    spent_token_symbol: Optional[str] = None
    spent_token_volume_h24: Optional[float] = None
    timestamp: int
    txn_hash: str
    wallet_address: str

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


class TransactionStrategy(RWModel):
    """Model for storing strategy evaluation results."""

    transaction_id: int
    strategy_id: int
    confidence: float
    explanation: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[int] = None

    @validator("confidence")
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v

    @validator("metadata", pre=True)
    def validate_metadata(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


class TransactionInDB(IDModelMixin, Transaction):
    pass


class TransactionStrategyInDB(IDModelMixin, TransactionStrategy):
    pass

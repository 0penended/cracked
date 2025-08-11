from dataclasses import dataclass
from typing import Optional
from enum import Enum


class Action(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    SWAP = "SWAP"
    OPEN_LONG = "OPEN_LONG"
    CLOSE_LONG = "CLOSE_LONG"
    OPEN_SHORT = "OPEN_SHORT"
    CLOSE_SHORT = "CLOSE_SHORT"
    LONG_TO_SHORT = "LONG_TO_SHORT"
    SHORT_TO_LONG = "SHORT_TO_LONG"
    LIQUIDATION = "LIQUIDATION"


@dataclass
class UnifiedTransactionEvent:
    """
    Unified transaction event that captures both spot and leveraged trades
    in a normalized structure.
    """

    # Core identifiers
    chain: str
    wallet_address: str  # Changed from wallet to wallet_address
    txn_hash: str  # Changed from tx_hash to txn_hash
    timestamp: int

    # Trade context
    action: Action

    # Asset acquired or traded (all required fields first)
    received_token_symbol: str
    received_token_quantity: float
    received_token_price: float  # USD price per unit
    received_token_volume_h24: float
    received_token_price_change_h24: float
    received_token_liquidity: float
    received_token_created_at: int

    # Asset spent or received (all required fields first)
    spent_token_symbol: str
    spent_token_amount: float
    spent_token_price: float  # USD price per unit
    spent_token_volume_h24: float
    spent_token_price_change_h24: float
    spent_token_liquidity: float
    spent_token_created_at: int

    # Optional fields (all default arguments at the end)
    received_token_id: Optional[str] = None  # Contract address or token ID
    received_token_marketcap: Optional[float] = None  # Market cap for received token
    spent_token_id: Optional[str] = None  # Contract address or token ID
    spent_token_marketcap: Optional[float] = None  # Market cap for spent token

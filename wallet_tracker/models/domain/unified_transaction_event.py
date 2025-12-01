from dataclasses import dataclass
from typing import Optional
from enum import Enum


class Action(str, Enum):
    """Supported transaction actions - single source of truth."""
    BUY = "BUY"
    SELL = "SELL"
    OPEN_LONG = "OPEN_LONG"
    CLOSE_LONG = "CLOSE_LONG"
    OPEN_SHORT = "OPEN_SHORT"
    CLOSE_SHORT = "CLOSE_SHORT"


# TODO: add spot buy support -- for now just track leveraged trades on HL
SUPPORTED_ACTIONS = [Action.OPEN_LONG, Action.CLOSE_LONG, Action.OPEN_SHORT, Action.CLOSE_SHORT]


@dataclass
class UnifiedTransactionEventLiquidation:
    markPx: float
    method: str
    liquidatedUser: Optional[str] = None


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
    received_token_price: float

    # Asset spent or received (all required fields first)
    spent_token_symbol: str
    spent_token_quantity: float
    spent_token_price: float

    transaction_value_usd: float

    # Optional fields (all default arguments at the end
    liquidation: Optional[UnifiedTransactionEventLiquidation] = None
    closed_pnl: Optional[str] = None
    received_token_id: Optional[str] = None  # Contract address or token ID
    spent_token_id: Optional[str] = None  # Contract address or token ID

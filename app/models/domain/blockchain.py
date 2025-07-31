from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class Action(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    SWAP = "SWAP"
    OPEN_LONG = "OPEN_LONG"
    CLOSE_LONG = "CLOSE_LONG"
    OPEN_SHORT = "OPEN_SHORT"
    CLOSE_SHORT = "CLOSE_SHORT"
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

    # Asset acquired or traded
    recieved_token_id: Optional[str] = None  # Contract address or token ID
    recieved_token_symbol: str
    recieved_token_quantity: float
    recieved_token_price: float  # USD price per unit
    recieved_token_volume_h24: float
    recieved_token_price_change_h24: float
    recieved_token_liquidity: float
    recieved_token_created_at: int

    # Asset spent or received
    spent_token_id: Optional[str] = None  # Contract address or token ID
    spent_token_symbol: str
    spent_token_amount: float
    spent_token_price: float  # USD price per unit
    spent_token_volume_h24: float
    spent_token_price_change_h24: float
    spent_token_liquidity: float
    spent_token_created_at: int


class ChainListener(ABC):
    """Abstract base class for blockchain listeners."""

    @abstractmethod
    async def subscribe_wallets(self, addresses: list[str]):
        """Subscribe to wallet events for a given addresses."""
        pass

    @abstractmethod
    async def run(self):
        """Main event loop for this chain."""
        pass


class AlertResult:
    """Result from alert evaluation."""

    def __init__(self, triggered: bool, score: float = 0.0, explanation: str = ""):
        self.triggered = triggered
        self.score = score
        self.explanation = explanation


class ModelRouter(ABC):
    """Abstract base class for ML model routers."""

    @abstractmethod
    async def should_alert(self, event: UnifiedTransactionEvent) -> AlertResult:
        """Evaluate if an event should trigger an alert based on ML model."""
        pass


class HeuristicRouter(ABC):
    """Abstract base class for heuristic-based routers."""

    @abstractmethod
    async def should_alert(self, event: UnifiedTransactionEvent) -> AlertResult:
        """Evaluate if an event should trigger an alert based on heuristics."""
        pass


class AlertRouter(ABC):
    """Abstract base class for alert routers."""

    @abstractmethod
    async def send(self, event: UnifiedTransactionEvent, results: list[AlertResult]):
        """Send alert for the given event with evaluation results."""
        pass

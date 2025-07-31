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
    wallet: str
    tx_hash: str
    timestamp: int

    # Trade context
    action: Action
    leverage: float  # 1.0 for spot trades, >1.0 for leverage

    # Asset acquired or traded
    recieved_symbol: str
    recieved_amount: float
    recieved_price: float  # USD price per unit
    recieved_volume_h24: float
    recieved_price_change_h24: float
    recieved_liquidity: float
    recieved_created_at: int

    # Asset spent or received
    spent_symbol: str
    spent_amount: float
    spent_price: float  # USD price per unit
    spent_volume_h24: float
    spent_price_change_h24: float
    spent_liquidity: float
    spent_created_at: int


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

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class UnifiedTransactionEvent:
    """Unified transaction event that normalizes data from different blockchain sources."""

    chain: str  # "solana", "hyperliquid", etc.
    wallet: str
    tx_hash: str
    timestamp: int
    symbol: Optional[str]
    action: str  # "BUY", "SELL", "SWAP", etc.
    amount: float
    price: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None  # chain-specific details if needed


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

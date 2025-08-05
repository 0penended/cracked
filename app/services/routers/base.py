from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

from app.models.domain.blockchain import UnifiedTransactionEvent
from app.models.domain.strategy import Strategy


@dataclass
class StrategyResult:
    """Result from strategy evaluation."""

    strategy_id: int  # Database ID of the strategy
    type: Strategy  # The strategy category
    confidence: float  # 0.0 to 1.0
    explanation: str
    metadata: Optional[dict] = None

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")


class TransactionStrategy(ABC):
    """Abstract base class for transaction analysis strategies."""

    def __init__(self, strategy_id: Optional[int] = None):
        self.strategy_id = strategy_id

    @property
    @abstractmethod
    def type(self) -> Strategy:
        """Return the strategy type this implementation represents."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a human-readable description for this strategy."""
        pass

    @abstractmethod
    async def evaluate(
        self, event: UnifiedTransactionEvent
    ) -> Optional[StrategyResult]:
        """
        Evaluate if the transaction matches this strategy.

        Returns:
            StrategyResult if the transaction matches this strategy, None otherwise.
        """
        pass


class AlertTrigger(ABC):
    """Abstract base class for alert triggers."""

    @abstractmethod
    def should_alert(self, strategy_results: List[StrategyResult]) -> bool:
        """
        Determine if an alert should be sent based on strategy results.

        Args:
            strategy_results: List of strategy evaluation results

        Returns:
            True if an alert should be sent, False otherwise
        """
        pass


class AlertRouter(ABC):
    """Abstract base class for alert routers."""

    @abstractmethod
    async def send(self, strategy_results: List[StrategyResult]):
        """Send alert for the given strategy evaluation results."""
        pass

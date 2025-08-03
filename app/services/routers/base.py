from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.models.domain.blockchain import UnifiedTransactionEvent


@dataclass
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
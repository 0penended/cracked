from typing import List
from app.services.routers.base import AlertTrigger, StrategyResult


class AlertTriggerStrategyMatchQuantity(AlertTrigger):
    """Alert trigger that fires when at least a specified quantity of strategies match."""

    def __init__(self, quantity: int):
        """
        Initialize the alert trigger.

        Args:
            quantity: Minimum number of strategies that must match to trigger an alert
        """
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")
        self.quantity = quantity

    def should_alert(self, strategy_results: List[StrategyResult]) -> bool:
        """
        Determine if an alert should be sent based on the number of matching strategies.

        Args:
            strategy_results: List of strategy evaluation results

        Returns:
            True if at least the specified quantity of strategies matched, False otherwise
        """
        return len(strategy_results) >= self.quantity

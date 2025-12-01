"""Simple strategy implementations."""

from wallet_tracker.services.strategies.size import large_transaction_strategy
from wallet_tracker.services.strategies.batched_wallet import BatchedWalletStrategy
from wallet_tracker.services.strategies.volume import high_volume_strategy

__all__ = [
    "large_transaction_strategy",
    "BatchedWalletStrategy",
    "high_volume_strategy",
]


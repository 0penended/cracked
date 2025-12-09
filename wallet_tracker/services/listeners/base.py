from abc import ABC, abstractmethod


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
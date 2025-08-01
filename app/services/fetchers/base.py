from abc import ABC, abstractmethod
from typing import Optional

from app.models.domain.blockchain import UnifiedTransactionEvent


class BaseTransactionFetcher(ABC):
    """Abstract base class for transaction fetchers."""

    @abstractmethod
    async def fetch_and_parse_transaction(self, identifier: str) -> Optional[UnifiedTransactionEvent]:
        """Fetch and parse a transaction from the blockchain."""
        pass 
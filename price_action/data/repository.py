"""Repository for storing and retrieving OHLCV data."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from price_action.core.models import Candle


class CandleRepository(ABC):
    """Abstract base class for candle storage."""

    @abstractmethod
    def save_candles(self, symbol: str, candles: List[Candle]) -> None:
        """Save candles to storage."""
        pass

    @abstractmethod
    def get_candles(
        self, symbol: str, timeframe: str, since: datetime
    ) -> List[Candle]:
        """Get candles from storage since a given datetime."""
        pass


class InMemoryCandleRepository(CandleRepository):
    """In-memory candle repository for v1 (no DB required)."""

    def __init__(self):
        """Initialize in-memory storage."""
        self._storage: dict[str, List[Candle]] = {}

    def save_candles(self, symbol: str, candles: List[Candle]) -> None:
        """Save candles to in-memory storage."""
        key = symbol
        if key not in self._storage:
            self._storage[key] = []
        self._storage[key].extend(candles)
        # Sort by timestamp
        self._storage[key].sort(key=lambda x: x.timestamp)

    def get_candles(
        self, symbol: str, timeframe: str, since: datetime
    ) -> List[Candle]:
        """Get candles since a given datetime."""
        key = symbol
        if key not in self._storage:
            return []
        return [c for c in self._storage[key] if c.timestamp >= since]


"""Repository for storing and retrieving OHLCV data."""

from datetime import datetime
from typing import Optional

from pa_engine.core.models import Candle


class CandleRepository:
    """
    Repository for OHLCV data storage and retrieval.
    
    For v1: in-memory storage. Can be extended to use DB later.
    """

    def __init__(self, db_session=None):
        """
        Initialize repository.
        
        Args:
            db_session: Database session (optional, for future DB integration)
        """
        self.db = db_session
        # In-memory storage for v1
        self._storage: dict[str, list[Candle]] = {}

    def save_candles(self, symbol: str, candles: list[Candle]) -> None:
        """
        Save candles for a symbol.
        
        Args:
            symbol: Trading pair symbol
            candles: List of candles to save
        """
        if symbol not in self._storage:
            self._storage[symbol] = []
        
        # Merge with existing candles, avoiding duplicates
        existing_timestamps = {c.timestamp for c in self._storage[symbol]}
        new_candles = [c for c in candles if c.timestamp not in existing_timestamps]
        self._storage[symbol].extend(new_candles)
        self._storage[symbol].sort(key=lambda x: x.timestamp)

    def get_candles(self, symbol: str, timeframe: str, since: datetime) -> list[Candle]:
        """
        Get candles for a symbol since a given timestamp.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe (for future filtering, not used in v1)
            since: Start timestamp
            
        Returns:
            List of candles since the given timestamp
        """
        if symbol not in self._storage:
            return []
        
        return [c for c in self._storage[symbol] if c.timestamp >= since]

    def get_all_candles(self, symbol: str) -> list[Candle]:
        """
        Get all stored candles for a symbol.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            List of all candles for the symbol
        """
        return self._storage.get(symbol, [])


"""Client for fetching OHLCV data from exchanges."""

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from price_action.core.models import Candle
from hyperliquid.info import Info


class OhlcvClient(ABC):
    """Abstract base class for OHLCV data clients."""

    @abstractmethod
    def fetch_recent_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> List[Candle]:
        """
        Fetches the last `limit` candles from the exchange.

        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT")
            timeframe: Timeframe string (e.g., "4h", "1d")
            limit: Number of candles to fetch

        Returns:
            List of Candle objects
        """
        pass


class HyperliquidOhlcvClient(OhlcvClient):
    """Hyperliquid OHLCV client using the Hyperliquid SDK."""

    def __init__(self, api_url: str = "https://api.hyperliquid.xyz"):
        """
        Initialize Hyperliquid client.

        Args:
            api_url: Hyperliquid API URL (default: mainnet)
        """
        self._api_url = api_url
        self.info = Info(api_url, skip_ws=True)

    def _parse_timeframe_to_ms(self, timeframe: str) -> int:
        """
        Parse timeframe string to milliseconds.

        Args:
            timeframe: Timeframe string (e.g., "1m", "15m", "1h", "4h", "1d")

        Returns:
            Milliseconds per candle

        Raises:
            ValueError: If timeframe format is invalid
        """
        timeframe = timeframe.lower().strip()

        if timeframe.endswith("m"):
            minutes = int(timeframe[:-1])
            return minutes * 60 * 1000
        elif timeframe.endswith("h"):
            hours = int(timeframe[:-1])
            return hours * 60 * 60 * 1000
        elif timeframe.endswith("d"):
            days = int(timeframe[:-1])
            return days * 24 * 60 * 60 * 1000
        else:
            raise ValueError(f"Invalid timeframe format: {timeframe}. Expected format: '1m', '15m', '1h', '4h', '1d', etc.")

    def fetch_recent_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> List[Candle]:
        """
        Fetch recent candles from Hyperliquid.

        Args:
            symbol: Trading pair symbol (e.g., "BTC", "ETH")
            timeframe: Timeframe string (e.g., "4h", "1d", "15m")
            limit: Number of candles to fetch

        Returns:
            List of Candle objects
        """
        # Calculate time range
        timeframe_ms = self._parse_timeframe_to_ms(timeframe)
        end_time_ms = int(time.time() * 1000)
        start_time_ms = end_time_ms - (limit * timeframe_ms)

        # Call Hyperliquid API using candle_snapshot method
        try:
            response = self.info.candle_snapshot(symbol, start_time_ms, end_time_ms)
        except Exception as e:
            raise RuntimeError(f"Failed to fetch candles from Hyperliquid: {e}")

        # Parse response - should be a list of candles
        if not isinstance(response, list):
            raise ValueError(f"Unexpected response format from Hyperliquid: {response}")

        candles = []
        for candle_data in response:
            # Parse Hyperliquid candle format:
            # T: end timestamp (ms)
            # t: start timestamp (ms)
            # o: open price (string)
            # h: high price (string)
            # l: low price (string)
            # c: close price (string)
            # v: volume (string)
            # s: symbol (string)
            # i: interval (string)
            # n: number of trades (integer)

            # Use start timestamp (t) for the candle timestamp
            timestamp_ms = candle_data.get("t", candle_data.get("T", 0))
            candles.append(
                Candle(
                    timestamp=datetime.fromtimestamp(timestamp_ms / 1000),
                    open=float(candle_data.get("o", 0)),
                    high=float(candle_data.get("h", 0)),
                    low=float(candle_data.get("l", 0)),
                    close=float(candle_data.get("c", 0)),
                    volume=float(candle_data.get("v", 0)),
                )
            )

        return candles


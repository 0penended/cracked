"""OHLCV data fetching from exchange APIs."""

from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime, timedelta

from pa_engine.core.models import Candle


class OhlcvClient(ABC):
    """Abstract base class for fetching candlestick data from exchanges."""

    @abstractmethod
    def fetch_recent_candles(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        limit: Optional[int] = None,
    ) -> list[Candle]:
        """
        Fetches candles from the exchange within the specified time range.

        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT" or "BTC")
            timeframe: Timeframe string (e.g., "4h", "1d")
            start_time: Start datetime (inclusive)
            end_time: End datetime (inclusive)
            limit: Optional maximum number of candles to return

        Returns:
            List of Candle objects
        """
        pass


class HyperliquidOhlcvClient(OhlcvClient):
    """Hyperliquid-specific OHLCV client using the official SDK."""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Hyperliquid OHLCV client.

        Args:
            base_url: Hyperliquid API base URL (default: mainnet)
        """
        from hyperliquid.info import Info
        from hyperliquid.utils import constants

        if base_url is None:
            base_url = constants.MAINNET_API_URL

        self.info = Info(base_url)

    def fetch_recent_candles(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        limit: Optional[int] = None,
    ) -> list[Candle]:
        """
        Fetches candles from Hyperliquid within the specified time range.

        Args:
            symbol: Coin name (e.g., "BTC", "ETH") - no "/USDT" suffix needed
            timeframe: Timeframe string (e.g., "4h", "1d")
            start_time: Start datetime (inclusive)
            end_time: End datetime (inclusive)
            limit: Optional maximum number of candles to return

        Returns:
            List of Candle objects
        """
        try:
            # Convert datetime objects to milliseconds for Hyperliquid API
            start_time_ms = int(start_time.timestamp() * 1000)
            end_time_ms = int(end_time.timestamp() * 1000)

            # Fetch candles from Hyperliquid
            candles_data = self.info.candles_snapshot(
                name=symbol,
                interval=timeframe,
                startTime=start_time_ms,
                endTime=end_time_ms,
            )

            if not candles_data:
                return []

            candles = []
            for candle_data in candles_data:
                # Hyperliquid candle format:
                # T: int, c: float string, h: float string, i: str,
                # l: float string, n: int, o: float string, s: string,
                # t: int, v: float string
                timestamp_ms = candle_data.get("t", candle_data.get("T", 0))
                candles.append(
                    Candle(
                        timestamp=datetime.fromtimestamp(timestamp_ms / 1000),
                        open=float(candle_data["o"]),
                        high=float(candle_data["h"]),
                        low=float(candle_data["l"]),
                        close=float(candle_data["c"]),
                        volume=float(candle_data["v"]),
                    )
                )

            # Sort by timestamp (oldest first)
            candles.sort(key=lambda x: x.timestamp)

            # Apply limit if specified
            if limit is not None and len(candles) > limit:
                return candles[-limit:]

            return candles

        except Exception as e:
            # Log error and return empty list
            print(f"Error fetching candles for {symbol} from Hyperliquid: {e}")
            return []

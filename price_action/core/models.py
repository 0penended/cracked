"""Core dataclasses for price action trading."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Candle:
    """OHLCV candlestick data."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class FeatureRow:
    """Feature vector for a symbol at a point in time."""

    symbol: str
    timestamp: datetime
    close: float
    ema_50: float
    ema_200: float
    rsi: float
    vol_rel_median: float
    obv: float
    obv_slope: float
    nearest_support: float
    nearest_resistance: float
    atr: float  # Average True Range for volatility measure


@dataclass
class TradeRecommendation:
    """Trade recommendation with entry, stop loss, and take profit."""

    symbol: str
    timestamp: datetime
    side: str  # "long" or "short" (long-only for now)
    entry: float
    stop_loss: float
    take_profit: float
    leverage: float
    reason: str  # Brief explanation / debug


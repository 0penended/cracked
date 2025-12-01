"""Core dataclasses for trading system."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Candle:
    """OHLCV candle data."""
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
    atr: float  # or some volatility measure
    # room for future: liq bands, macro regime, etc.


@dataclass
class TradeRecommendation:
    """Trade signal with entry, SL, TP, and leverage."""
    symbol: str
    timestamp: datetime
    side: str                # "long" or "short" (long-only now)
    entry: float
    stop_loss: float
    take_profit: float
    leverage: float
    reason: str              # brief explanation / debug


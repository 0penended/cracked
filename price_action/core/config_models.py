"""Configuration dataclasses for price action trading."""

from dataclasses import dataclass


@dataclass
class ThresholdConfig:
    """Thresholds for rule-based signal generation."""

    rsi_min: float
    rsi_max: float
    vol_rel_min: float  # volume / median_volume
    max_distance_to_support_pct: float
    obv_slope_min: float  # e.g. > 0 means rising
    require_trend: bool  # EMA50 > EMA200


@dataclass
class RiskConfig:
    """Risk management configuration."""

    account_risk_pct: float  # risk per trade (% of equity)
    sl_atr_mult: float  # SL distance in ATRs or pct
    tp_rr: float  # TP = RR * risk (e.g. 2R, 3R)
    max_leverage: float  # upper bound (e.g. 10x)
    min_leverage: float  # floor (e.g. 1x)


@dataclass
class AppConfig:
    """Main application configuration."""

    symbols: list[str]
    timeframe: str  # "4h"
    history_lookback_days: int  # e.g. 365 for DB hydration
    thresholds: ThresholdConfig
    risk: RiskConfig


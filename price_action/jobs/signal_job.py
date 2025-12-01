"""4-hour signal generation job."""

from datetime import datetime
from typing import List

from price_action.core.config_models import AppConfig
from price_action.core.models import TradeRecommendation
from price_action.data.ohlcv_client import OhlcvClient
from price_action.features.feature_builder import build_feature_from_df
from price_action.features.indicators import compute_indicators
from price_action.features.support_resistance import compute_support_resistance
from price_action.signals.policy import RuleBasedPolicy
from price_action.signals.risk import RiskManager


class SignalJob:
    """Job that runs every 4h to generate trading signals."""

    def __init__(self, cfg: AppConfig, ohlcv_client: OhlcvClient):
        """
        Initialize signal job.

        Args:
            cfg: Application configuration
            ohlcv_client: Client for fetching OHLCV data
        """
        self.cfg = cfg
        self.client = ohlcv_client
        self.policy = RuleBasedPolicy(cfg.thresholds)
        self.risk_mgr = RiskManager(cfg.risk)

    def run_once(self) -> List[TradeRecommendation]:
        """
        Run signal generation once for all configured symbols.

        Returns:
            List of trade recommendations
        """
        recommendations = []

        for symbol in self.cfg.symbols:
            try:
                # Fetch recent candles (enough for EMA200 etc.)
                candles = self.client.fetch_recent_candles(
                    symbol=symbol,
                    timeframe=self.cfg.timeframe,
                    limit=300,
                )

                if len(candles) < 220:  # Need enough for indicators
                    continue

                # Compute indicators
                df = compute_indicators(candles)
                df = compute_support_resistance(df, window=50)

                # Build feature row
                features = build_feature_from_df(symbol, df)

                if features and self.policy.should_enter_long(features):
                    trade = self.risk_mgr.build_trade(features)
                    recommendations.append(trade)

            except Exception as e:
                # Log error but continue with other symbols
                print(f"Error processing {symbol}: {e}")
                continue

        return recommendations


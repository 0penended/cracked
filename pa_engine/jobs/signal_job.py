"""Signal generation job that runs every 4h."""

from datetime import datetime, timedelta

from pa_engine.core.config_models import AppConfig
from pa_engine.core.models import TradeRecommendation
from pa_engine.data.ohlcv_client import OhlcvClient
from pa_engine.features.indicators import compute_indicators
from pa_engine.features.support_resistance import compute_support_resistance
from pa_engine.features.feature_builder import build_feature_from_df
from pa_engine.signals.policy import RuleBasedPolicy
from pa_engine.signals.risk import RiskManager


class SignalJob:
    """Job that generates trading signals for configured symbols."""

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

    def run_once(self) -> list[TradeRecommendation]:
        """
        Run signal generation once for all configured symbols.

        Returns:
            List of TradeRecommendation objects
        """
        recommendations = []

        # Use history_lookback_days from config
        end_time = datetime.now()
        start_time = end_time - timedelta(days=self.cfg.history_lookback_days)

        for symbol in self.cfg.symbols:
            candles = self.client.fetch_recent_candles(
                symbol=symbol,
                timeframe=self.cfg.timeframe,
                start_time=start_time,
                end_time=end_time,
            )

            # We need at least 220 candles for EMA200 etc.
            if len(candles) < 220:
                continue

            df = compute_indicators(candles)
            df = compute_support_resistance(df, window=50)
            features = build_feature_from_df(symbol, df)

            if features and self.policy.should_enter_long(features):
                trade = self.risk_mgr.build_trade(features)
                recommendations.append(trade)

        return recommendations

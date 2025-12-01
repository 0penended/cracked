"""Backtesting framework for trading strategies."""

from datetime import datetime
from typing import Optional

from pa_engine.core.config_models import AppConfig
from pa_engine.core.models import Candle, TradeRecommendation
from pa_engine.features.indicators import compute_indicators
from pa_engine.features.support_resistance import compute_support_resistance
from pa_engine.features.feature_builder import build_feature_from_df
from pa_engine.signals.policy import RuleBasedPolicy
from pa_engine.signals.risk import RiskManager


class Backtester:
    """
    Backtester that reuses the same policy and features logic.
    
    This allows backtesting with the exact same logic used in production.
    """

    def __init__(self, cfg: AppConfig):
        """
        Initialize backtester.
        
        Args:
            cfg: Application configuration
        """
        self.cfg = cfg
        self.policy = RuleBasedPolicy(cfg.thresholds)
        self.risk_mgr = RiskManager(cfg.risk)

    def run_backtest(
        self,
        symbol: str,
        candles: list[Candle],
        start_idx: int = 220
    ) -> list[dict]:
        """
        Run backtest on historical candles.
        
        Args:
            symbol: Trading pair symbol
            candles: Historical candle data
            start_idx: Starting index (to allow for indicator warm-up)
            
        Returns:
            List of trade results with outcomes
        """
        results = []
        
        # Process candles sequentially
        for i in range(start_idx, len(candles)):
            # Get candles up to current point
            historical_candles = candles[:i+1]
            
            # Compute features
            df = compute_indicators(historical_candles)
            df = compute_support_resistance(df, window=50)
            features = build_feature_from_df(symbol, df)
            
            if not features:
                continue
            
            # Check for signal
            if self.policy.should_enter_long(features):
                trade = self.risk_mgr.build_trade(features)
                
                # Simulate trade outcome
                outcome = self._simulate_trade(trade, candles[i:])
                
                results.append({
                    "trade": trade,
                    "outcome": outcome,
                    "features": features
                })
        
        return results

    def _simulate_trade(
        self,
        trade: TradeRecommendation,
        future_candles: list[Candle]
    ) -> dict:
        """
        Simulate a trade to see if it hits TP or SL.
        
        Args:
            trade: Trade recommendation
            future_candles: Candles after entry
            
        Returns:
            Dictionary with outcome details
        """
        entry_price = trade.entry
        sl = trade.stop_loss
        tp = trade.take_profit
        
        for candle in future_candles:
            # Check if SL was hit
            if candle.low <= sl:
                risk = entry_price - sl
                return {
                    "result": "SL",
                    "exit_price": sl,
                    "pnl": -risk,
                    "pnl_pct": -risk / entry_price,
                    "bars_held": future_candles.index(candle) + 1
                }
            
            # Check if TP was hit
            if candle.high >= tp:
                risk = entry_price - sl
                reward = tp - entry_price
                return {
                    "result": "TP",
                    "exit_price": tp,
                    "pnl": reward,
                    "pnl_pct": reward / entry_price,
                    "bars_held": future_candles.index(candle) + 1
                }
        
        # Trade still open at end of data
        last_price = future_candles[-1].close if future_candles else entry_price
        return {
            "result": "OPEN",
            "exit_price": last_price,
            "pnl": last_price - entry_price,
            "pnl_pct": (last_price - entry_price) / entry_price,
            "bars_held": len(future_candles)
        }


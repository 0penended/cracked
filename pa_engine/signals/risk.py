"""Risk management and trade sizing."""

from pa_engine.core.config_models import RiskConfig
from pa_engine.core.models import FeatureRow, TradeRecommendation


class RiskManager:
    """Risk management for trade sizing, SL, TP, and leverage."""

    def __init__(self, risk_cfg: RiskConfig):
        """
        Initialize risk manager with configuration.
        
        Args:
            risk_cfg: RiskConfig object with risk parameters
        """
        self.cfg = risk_cfg

    def build_trade(self, f: FeatureRow) -> TradeRecommendation:
        """
        Build a trade recommendation from feature row.
        
        Args:
            f: FeatureRow with computed indicators
            
        Returns:
            TradeRecommendation with entry, SL, TP, and leverage
        """
        entry = f.close

        # SL = support - x * ATR
        sl = f.nearest_support - self.cfg.sl_atr_mult * f.atr

        risk_per_unit = entry - sl
        # Simple TP = entry + RR * risk
        tp = entry + self.cfg.tp_rr * risk_per_unit

        # Leverage can be a function of volatility / distance to SL
        # For v1: just map based on ATR% or leave constant
        atr_pct = f.atr / f.close
        # Example heuristic: lower ATR -> higher leverage
        if atr_pct < 0.01:
            leverage = self.cfg.max_leverage
        elif atr_pct < 0.02:
            leverage = max(self.cfg.max_leverage * 0.5, self.cfg.min_leverage)
        else:
            leverage = self.cfg.min_leverage

        return TradeRecommendation(
            symbol=f.symbol,
            timestamp=f.timestamp,
            side="long",
            entry=entry,
            stop_loss=sl,
            take_profit=tp,
            leverage=leverage,
            reason="trend_up_rsi_pullback_obv_positive"
        )


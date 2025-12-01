"""Risk management and trade sizing."""

from price_action.core.config_models import RiskConfig
from price_action.core.models import FeatureRow, TradeRecommendation


class RiskManager:
    """Risk management for trade sizing and SL/TP calculation."""

    def __init__(self, risk_cfg: RiskConfig):
        """
        Initialize risk manager.

        Args:
            risk_cfg: Risk configuration
        """
        self.cfg = risk_cfg

    def build_trade(self, f: FeatureRow) -> TradeRecommendation:
        """
        Build trade recommendation from feature row.

        Args:
            f: FeatureRow with current market features

        Returns:
            TradeRecommendation with entry, SL, TP, and leverage
        """
        entry = f.close

        # SL = support - x * ATR
        if f.nearest_support > 0:
            sl = f.nearest_support - self.cfg.sl_atr_mult * f.atr
        else:
            # Fallback: use ATR-based SL if no support
            sl = entry - self.cfg.sl_atr_mult * f.atr

        risk_per_unit = entry - sl

        # Simple TP = entry + RR * risk
        tp = entry + self.cfg.tp_rr * risk_per_unit

        # Leverage based on volatility (ATR %)
        atr_pct = f.atr / f.close if f.close > 0 else 0.02

        # Lower ATR -> higher leverage
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
            reason="trend_up_rsi_pullback_obv_positive",
        )


"""Rule-based trading policy."""

from price_action.core.config_models import ThresholdConfig
from price_action.core.models import FeatureRow


class RuleBasedPolicy:
    """Rule-based decision engine using configurable thresholds."""

    def __init__(self, thresholds: ThresholdConfig):
        """
        Initialize policy with thresholds.

        Args:
            thresholds: Threshold configuration
        """
        self.th = thresholds

    def should_enter_long(self, f: FeatureRow) -> bool:
        """
        Determine if we should enter a long position.

        Args:
            f: FeatureRow with current market features

        Returns:
            True if all conditions are met for long entry
        """
        # Check trend requirement
        if self.th.require_trend and not (f.ema_50 > f.ema_200):
            return False

        # Check RSI range
        if not (self.th.rsi_min <= f.rsi <= self.th.rsi_max):
            return False

        # Check volume requirement
        if f.vol_rel_median < self.th.vol_rel_min:
            return False

        # Check distance to support
        if f.nearest_support > 0:
            dist_to_support_pct = (f.close - f.nearest_support) / f.close
            if dist_to_support_pct > self.th.max_distance_to_support_pct:
                return False

        # Check OBV slope
        if f.obv_slope < self.th.obv_slope_min:
            return False

        return True


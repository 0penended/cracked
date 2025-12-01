"""Rule-based trading policy."""

from pa_engine.core.config_models import ThresholdConfig
from pa_engine.core.models import FeatureRow


class RuleBasedPolicy:
    """Rule-based decision engine using configurable thresholds."""

    def __init__(self, thresholds: ThresholdConfig):
        """
        Initialize policy with threshold configuration.
        
        Args:
            thresholds: ThresholdConfig object with signal criteria
        """
        self.th = thresholds

    def should_enter_long(self, f: FeatureRow) -> bool:
        """
        Determine if a long entry signal should be generated.
        
        Args:
            f: FeatureRow with computed indicators
            
        Returns:
            True if all conditions are met for a long entry
        """
        # Check trend requirement
        if self.th.require_trend and not (f.ema_50 > f.ema_200):
            return False

        # Check RSI range
        if not (self.th.rsi_min <= f.rsi <= self.th.rsi_max):
            return False

        # Check volume relative to median
        if f.vol_rel_median < self.th.vol_rel_min:
            return False

        # Check distance to support
        dist_to_support_pct = (f.close - f.nearest_support) / f.close
        if dist_to_support_pct > self.th.max_distance_to_support_pct:
            return False

        # Check OBV slope
        if f.obv_slope < self.th.obv_slope_min:
            return False

        return True


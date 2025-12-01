"""Build FeatureRow from processed DataFrame."""

from typing import Optional
import pandas as pd

from pa_engine.core.models import FeatureRow


def build_feature_from_df(symbol: str, df: pd.DataFrame) -> Optional[FeatureRow]:
    """
    Build a FeatureRow from the last row of a processed DataFrame.
    
    Args:
        symbol: Trading pair symbol
        df: DataFrame with computed indicators
        
    Returns:
        FeatureRow object or None if DataFrame is empty or missing required columns
    """
    if df.empty:
        return None
    
    row = df.iloc[-1]
    
    # Check for required columns and NaN values
    required_cols = [
        "close", "ema_50", "ema_200", "rsi", "vol_rel_median",
        "obv", "obv_slope", "nearest_support", "nearest_resistance", "atr"
    ]
    
    for col in required_cols:
        if col not in row.index or pd.isna(row[col]):
            return None
    
    return FeatureRow(
        symbol=symbol,
        timestamp=row.name,
        close=float(row["close"]),
        ema_50=float(row["ema_50"]),
        ema_200=float(row["ema_200"]),
        rsi=float(row["rsi"]),
        vol_rel_median=float(row["vol_rel_median"]),
        obv=float(row["obv"]),
        obv_slope=float(row["obv_slope"]),
        nearest_support=float(row["nearest_support"]),
        nearest_resistance=float(row["nearest_resistance"]),
        atr=float(row["atr"]),
    )


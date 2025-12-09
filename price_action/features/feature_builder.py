"""Build FeatureRow from processed DataFrame."""

from typing import Optional

import pandas as pd

from price_action.core.models import FeatureRow


def build_feature_from_df(symbol: str, df: pd.DataFrame) -> Optional[FeatureRow]:
    """
    Build FeatureRow from the last row of processed DataFrame.

    Args:
        symbol: Trading pair symbol
        df: DataFrame with indicators and support/resistance computed

    Returns:
        FeatureRow if DataFrame is not empty, None otherwise
    """
    if df.empty:
        return None

    row = df.iloc[-1]

    return FeatureRow(
        symbol=symbol,
        timestamp=row.name,
        close=float(row["close"]),
        ema_50=float(row["ema_50"]) if pd.notna(row["ema_50"]) else 0.0,
        ema_200=float(row["ema_200"]) if pd.notna(row["ema_200"]) else 0.0,
        rsi=float(row["rsi"]) if pd.notna(row["rsi"]) else 50.0,
        vol_rel_median=float(row["vol_rel_median"]) if pd.notna(row["vol_rel_median"]) else 1.0,
        obv=float(row["obv"]) if pd.notna(row["obv"]) else 0.0,
        obv_slope=float(row["obv_slope"]) if pd.notna(row["obv_slope"]) else 0.0,
        nearest_support=float(row["nearest_support"]) if pd.notna(row["nearest_support"]) else 0.0,
        nearest_resistance=float(row["nearest_resistance"]) if pd.notna(row["nearest_resistance"]) else 0.0,
        atr=float(row["atr"]) if pd.notna(row["atr"]) else 0.0,
    )


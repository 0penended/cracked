"""Support and resistance level calculations."""

import numpy as np
import pandas as pd


def compute_support_resistance(df: pd.DataFrame, window: int = 50) -> pd.DataFrame:
    """
    Compute nearest support and resistance levels.

    For each row, find nearest support & resistance within last `window` candles.

    Args:
        df: DataFrame with OHLCV data
        window: Lookback window for finding support/resistance

    Returns:
        DataFrame with nearest_support and nearest_resistance columns added
    """
    supports = []
    resistances = []

    for idx in range(len(df)):
        sub = df.iloc[max(0, idx - window) : idx + 1]

        if sub.empty:
            supports.append(np.nan)
            resistances.append(np.nan)
            continue

        supports.append(sub["low"].min())
        resistances.append(sub["high"].max())

    df["nearest_support"] = supports
    df["nearest_resistance"] = resistances

    return df


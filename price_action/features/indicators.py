"""Technical indicator calculations."""

import pandas as pd

try:
    import pandas_ta as ta
except ImportError:
    raise ImportError("pandas_ta is required. Install with: pip install pandas-ta")


def compute_indicators(candles: list) -> pd.DataFrame:
    """
    Compute technical indicators from candles.

    Args:
        candles: List of Candle objects

    Returns:
        DataFrame with indicators added
    """
    # Convert candles to DataFrame
    data = []
    for c in candles:
        data.append(
            {
                "timestamp": c.timestamp,
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "volume": c.volume,
            }
        )

    df = pd.DataFrame(data)
    df = df.set_index("timestamp")

    # EMA indicators
    df["ema_50"] = ta.ema(df["close"], length=50)
    df["ema_200"] = ta.ema(df["close"], length=200)

    # RSI
    df["rsi"] = ta.rsi(df["close"], length=14)

    # Volume vs median over last N candles
    N = 20
    df["vol_median"] = df["volume"].rolling(N).median()
    df["vol_rel_median"] = df["volume"] / df["vol_median"]

    # OBV + slope over last K candles
    df["obv"] = ta.obv(df["close"], df["volume"])
    K = 10
    df["obv_slope"] = df["obv"] - df["obv"].shift(K)

    # ATR (for SL/TP sizing)
    df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=14)

    return df


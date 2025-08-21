from __future__ import annotations
import pandas as pd
from indicators.basic import ema


def classify(df: pd.DataFrame) -> str:
    """Return 'trend' or 'chop' based on EMA stack and volatility band heuristic."""
    close = df["c"]
    e8, e21, e55 = ema(close, 8), ema(close, 21), ema(close, 55)
    trend = (e8.iloc[-1] > e21.iloc[-1] > e55.iloc[-1]) or (e8.iloc[-1] < e21.iloc[-1] < e55.iloc[-1])
    rng = (close.rolling(20).max().iloc[-1] - close.rolling(20).min().iloc[-1]) / close.iloc[-1]
    if trend and rng > 0.03:
        return "trend"
    return "chop"

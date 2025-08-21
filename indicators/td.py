from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

@dataclass(frozen=True)
class TDState:
    flip: str  # bullish/bearish/none
    setup_type: str | None  # buy/sell
    setup_count: int
    perfected: bool
    countdown: int
    tdst_buy: float | None
    tdst_sell: float | None


def _price_flip(df: pd.DataFrame) -> str:
    """Minimal price flip: compare close vs close 4 bars earlier.

    Returns: bullish/bearish/none
    """
    if len(df) < 5:
        return "none"
    c = df["c"]
    bull = c.iloc[-1] > c.iloc[-5]
    bear = c.iloc[-1] < c.iloc[-5]
    if bull and not bear:
        return "bullish"
    if bear and not bull:
        return "bearish"
    return "none"


def compute(df: pd.DataFrame, strict_perfection: bool = True) -> TDState:
    """Minimal TD state on the last bar (stub for a full TD engine).

    Ensures index safety and avoids negative indexing.
    """
    flip = _price_flip(df)
    setup_type: str | None = None
    setup_count = 0
    perfected = False
    countdown = 0
    tdst_buy = None
    tdst_sell = None

    n = len(df)
    if n >= 10:
        c = df["c"].reset_index(drop=True)
        h = df["h"].reset_index(drop=True)
        l = df["l"].reset_index(drop=True)
        # Evaluate last up-to-9 bars without negative indices
        start = max(4, n - 9)
        if flip == "bullish":
            setup_type = "sell"
            cnt = 0
            for i in range(start, n):
                if i - 4 < 0:
                    continue
                if c.iloc[i] > c.iloc[i - 4]:
                    cnt += 1
                else:
                    cnt = 0
            setup_count = cnt
            if n >= 5:
                tdst_sell = float(h.iloc[max(0, n - 9): n - 1].max())
                perfected = (h.iloc[-2] > h.iloc[-4]) if (strict_perfection and n >= 5) else True
        elif flip == "bearish":
            setup_type = "buy"
            cnt = 0
            for i in range(start, n):
                if i - 4 < 0:
                    continue
                if c.iloc[i] < c.iloc[i - 4]:
                    cnt += 1
                else:
                    cnt = 0
            setup_count = cnt
            if n >= 5:
                tdst_buy = float(l.iloc[max(0, n - 9): n - 1].min())
                perfected = (l.iloc[-2] < l.iloc[-4]) if (strict_perfection and n >= 5) else True

    return TDState(
        flip=flip,
        setup_type=setup_type,
        setup_count=setup_count,
        perfected=perfected,
        countdown=countdown,
        tdst_buy=tdst_buy,
        tdst_sell=tdst_sell,
    )

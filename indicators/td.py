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
    # Minimal TD setup computation on last bar only
    flip = _price_flip(df)
    setup_type: str | None = None
    setup_count = 0
    perfected = False
    countdown = 0
    tdst_buy = None
    tdst_sell = None

    if len(df) >= 10:
        c = df["c"].reset_index(drop=True)
        h = df["h"].reset_index(drop=True)
        l = df["l"].reset_index(drop=True)
        # Determine setup over last 9 bars
        setup_count = 0
        if flip == "bullish":
            setup_type = "sell"
            for i in range(len(c)-9, len(c)):
                if c[i] > c[i-4]:
                    setup_count += 1
                else:
                    setup_count = 0
            tdst_sell = float(max(h[len(c)-9:len(c)-1]))
            perfected = (h.iloc[-2] > h.iloc[-4]) if strict_perfection else True
        elif flip == "bearish":
            setup_type = "buy"
            for i in range(len(c)-9, len(c)):
                if c[i] < c[i-4]:
                    setup_count += 1
                else:
                    setup_count = 0
            tdst_buy = float(min(l[len(c)-9:len(c)-1]))
            perfected = (l.iloc[-2] < l.iloc[-4]) if strict_perfection else True

    return TDState(
        flip=flip,
        setup_type=setup_type,
        setup_count=setup_count,
        perfected=perfected,
        countdown=countdown,
        tdst_buy=tdst_buy,
        tdst_sell=tdst_sell,
    )

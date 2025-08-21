from __future__ import annotations
from dataclasses import dataclass
from typing import List, Sequence
import logging
import pandas as pd

from features.store import load
from rotation.scan import RotationCandidate

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class Confirmed:
    candidate: RotationCandidate
    passed: bool
    reasons: List[str]


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _volume_x2(df: pd.DataFrame, span: int, x: float) -> bool:
    v = float(df["v"].iloc[-1])
    ema = float(_ema(df["v"], span=span).iloc[-1])
    return v >= x * ema


def _breakout(df: pd.DataFrame, lookback: int) -> bool:
    hi = float(df["h"].iloc[-lookback:-1].max())
    last = float(df["c"].iloc[-1])
    return last > hi


def apply(candidates: Sequence[RotationCandidate], *, cache: str, tf: str,
          volume_x: float, breakout_lookback: int) -> List[Confirmed]:
    out: List[Confirmed] = []
    for c in candidates:
        df = load(cache, c.symbol, tf, cols=["t", "h", "c", "v"])  # price+vol
        reasons: List[str] = []
        ok_vol = _volume_x2(df, span=20, x=volume_x)
        if ok_vol:
            reasons.append(f"vol>={volume_x}xEMA20")
        ok_brk = _breakout(df, breakout_lookback)
        if ok_brk:
            reasons.append(f"breakout>{breakout_lookback}")
        passed = ok_vol and ok_brk
        out.append(Confirmed(candidate=c, passed=passed, reasons=reasons))
    return out

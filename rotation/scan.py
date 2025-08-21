from __future__ import annotations
from dataclasses import dataclass
from typing import List, Sequence, Tuple
import logging
import pandas as pd

from features.store import load

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class RotationCandidate:
    symbol: str
    apex_asset: str
    apex_move_pct: float
    coin_move_pct: float
    correlation: float
    beta: float
    signal_strength: str  # LOW/MEDIUM/HIGH
    status: str  # e.g., LAGGING_ROTATION


def _pct_move(df: pd.DataFrame) -> float:
    if len(df) < 2:
        raise ValueError("Need >=2 rows to compute move")
    p0, p1 = float(df["c"].iloc[-2]), float(df["c"].iloc[-1])
    return (p1 / p0 - 1.0) * 100.0


def _rolling_corr_beta(coin: pd.Series, apex: pd.Series, w_corr: int, w_beta: int) -> Tuple[float, float]:
    c = coin.pct_change().dropna()
    a = apex.pct_change().dropna()
    both = pd.concat([c, a], axis=1).dropna()
    if len(both) < max(w_corr, w_beta):
        return float("nan"), float("nan")
    corr = both.iloc[-w_corr:].corr().iloc[0, 1]
    cov = both.iloc[-w_beta:, 0].cov(both.iloc[-w_beta:, 1])
    var = both.iloc[-w_beta:, 1].var()
    beta = cov / var if var != 0 else float("nan")
    return float(corr), float(beta)


def scan(apex_assets: Sequence[str], basket: Sequence[str], *, tf: str, cache: str,
         move_threshold_pct: float, alt_lag_threshold_pct: float,
         corr_min: float, beta_min: float,
         corr_window: int = 14, beta_window: int = 30) -> List[RotationCandidate]:
    """Scan for lagging rotations on the last bar of tf using cached OHLCV.

    Returns a list of RotationCandidate.
    """
    results: List[RotationCandidate] = []

    # Load apex frames
    apex_dfs = {a: load(cache, a, tf, cols=["t", "c"]) for a in apex_assets}

    for coin in basket:
        coin_df = load(cache, coin, tf, cols=["t", "c"])  # align by merge later
        for apex in apex_assets:
            a_df = apex_dfs[apex]
            merged = pd.merge_asof(coin_df.sort_values("t"), a_df.sort_values("t"), on="t", direction="nearest", suffixes=("_coin", "_apex"))
            if len(merged) < max(corr_window, beta_window) + 1:
                continue
            apex_move = _pct_move(merged[["t", "c_apex"]].rename(columns={"c_apex": "c"}))
            coin_move = _pct_move(merged[["t", "c_coin"]].rename(columns={"c_coin": "c"}))
            corr, beta = _rolling_corr_beta(merged["c_coin"], merged["c_apex"], corr_window, beta_window)

            if pd.isna(corr) or pd.isna(beta):
                continue
            if apex_move >= move_threshold_pct and coin_move <= alt_lag_threshold_pct and corr >= corr_min and beta >= beta_min:
                strength = "HIGH" if (apex_move - coin_move) >= 3.0 else ("MEDIUM" if (apex_move - coin_move) >= 1.5 else "LOW")
                results.append(RotationCandidate(
                    symbol=coin,
                    apex_asset=apex,
                    apex_move_pct=round(apex_move, 2),
                    coin_move_pct=round(coin_move, 2),
                    correlation=round(corr, 3),
                    beta=round(beta, 2),
                    signal_strength=strength,
                    status="LAGGING_ROTATION",
                ))
    return results

from __future__ import annotations
import os
import logging
import pathlib
from typing import List

import pandas as pd
from dotenv import load_dotenv

from common.logging import setup_logging
from config.loader import load_settings
from features.store import load


def _rule_entries(df: pd.DataFrame, volume_x: float, breakout_lookback: int) -> pd.Series:
    df = df.sort_values("t").copy()
    vol_ema20 = df["v"].ewm(span=20, adjust=False).mean()
    vol_ok = df["v"] >= volume_x * vol_ema20
    hi = df["h"].rolling(breakout_lookback).max().shift(1)
    brk = df["c"] > hi
    return (vol_ok & brk).fillna(False)


def _forward_returns(df: pd.DataFrame, entries: pd.Series, fwd_bars: int) -> pd.DataFrame:
    c = df["c"].reset_index(drop=True)
    t = df["t"].reset_index(drop=True)
    e = entries.reset_index(drop=True)
    rows: List[dict] = []
    for i, is_entry in enumerate(e):
        if not is_entry:
            continue
        j = i + fwd_bars
        if j >= len(c):
            break
        ret = (float(c[j]) / float(c[i]) - 1.0) * 100.0
        rows.append({"t_entry": t[i], "ret_pct": ret})
    return pd.DataFrame(rows)


def main() -> None:
    load_dotenv()
    setup_logging()
    LOG = logging.getLogger(__name__)

    cfg = load_settings(os.getenv("CONFIG_PATH", "config/config.yaml"))
    cache = os.getenv("CACHE_PATH", ".cache")

    tf = cfg.timeframes.ltf
    out_path = pathlib.Path(cache) / f"backtest_{tf}.csv"
    all_rows: List[pd.DataFrame] = []

    for sym in cfg.basket.symbols:
        try:
            df = load(cache, sym, tf, cols=["t", "h", "c", "v"])  # minimal cols
        except FileNotFoundError:
            LOG.warning("missing cache for %s %s", sym, tf)
            continue
        entries = _rule_entries(df, cfg.market_filters.volume_x, cfg.market_filters.breakout_lookback)
        trades = _forward_returns(df, entries, fwd_bars=cfg.td.cooldown_bars)
        if trades.empty:
            continue
        trades.insert(0, "symbol", sym)
        all_rows.append(trades)

    if not all_rows:
        LOG.info("no trades detected; nothing to write")
        return

    out = pd.concat(all_rows, ignore_index=True)
    out.to_csv(out_path, index=False)
    LOG.info("backtest results -> %s (%d rows)", out_path, len(out))


if __name__ == "__main__":
    main()

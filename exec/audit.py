from __future__ import annotations
import logging
import pathlib
from typing import List, Tuple
import pandas as pd

from features.store import load
from common.timeframe import tf_to_pandas_freq

LOG = logging.getLogger(__name__)


def _freq_for_tf(tf: str) -> str:
    """Map timeframe to pandas frequency alias."""
    return tf_to_pandas_freq(tf)


def _audit_df(df: pd.DataFrame, tf: str) -> Tuple[int, int]:
    """Return (missing, duplicates) counts for a single symbol/tf frame."""
    df = df.sort_values("t")
    if df.empty:
        return 0, 0
    # Count duplicates before de-duplication
    dup_count = int(len(df) - len(df.drop_duplicates(subset="t")))
    df = df.drop_duplicates(subset="t")
    rng = pd.date_range(df["t"].iloc[0], df["t"].iloc[-1], freq=_freq_for_tf(tf), tz="UTC")
    missing = len(set(rng) - set(df["t"]))
    return missing, dup_count


def run(cache: str | pathlib.Path, symbols: List[str], tfs: List[str]) -> List[Tuple[str, str, int, int]]:
    """Return audit rows: (symbol, tf, missing, duplicates)."""
    out: List[Tuple[str, str, int, int]] = []
    for s in symbols:
        for tf in tfs:
            try:
                df = load(cache, s, tf, cols=["t", "c"])
                miss, dups = _audit_df(df, tf)
                out.append((s, tf, miss, dups))
            except FileNotFoundError:
                out.append((s, tf, -1, -1))
    return out


def main() -> None:
    import os
    from common.logging import setup_logging
    from config.loader import load_settings

    setup_logging()
    cfg = load_settings(os.getenv("CONFIG_PATH", "config/config.yaml"))
    cache = os.getenv("CACHE_PATH", ".cache")
    rows = run(cache, cfg.basket.symbols, [cfg.timeframes.ltf, cfg.timeframes.htf])
    for s, tf, miss, dups in rows:
        LOG.info("AUDIT %s %s missing=%s dups=%s", s, tf, miss, dups)


if __name__ == "__main__":
    main()

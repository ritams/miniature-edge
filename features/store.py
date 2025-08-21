from __future__ import annotations
import os
import pathlib
from typing import Iterable, List, Optional
import logging

import duckdb
import pandas as pd

LOG = logging.getLogger(__name__)


def cache_dir(base: str | pathlib.Path) -> pathlib.Path:
    p = pathlib.Path(base)
    p.mkdir(parents=True, exist_ok=True)
    (p / "ohlcv").mkdir(parents=True, exist_ok=True)
    return p


def parquet_path(cache: pathlib.Path, symbol: str, tf: str) -> pathlib.Path:
    return cache / "ohlcv" / f"{symbol}_{tf}.parquet"


def write_ohlcv(cache: pathlib.Path, symbol: str, tf: str, rows: List[List[float]]) -> int:
    """Write OHLCV rows to parquet (idempotent: overwrites entire file for now)."""
    if not rows:
        LOG.warning("No rows to write for %s %s", symbol, tf)
        return 0
    df = pd.DataFrame(rows, columns=["t", "o", "h", "l", "c", "v"])  # timestamp ms
    df["t"] = pd.to_datetime(df["t"], unit="ms", utc=True)
    df = df.drop_duplicates(subset="t").sort_values("t")

    path = parquet_path(cache, symbol, tf)
    df.to_parquet(path, index=False)

    _mirror_to_duckdb(cache, symbol, tf, path)
    return len(df)


def upsert_ohlcv(cache: pathlib.Path, symbol: str, tf: str, rows: List[List[float]]) -> int:
    """Append new OHLCV rows into existing parquet, de-dup by timestamp, and write.

    If file does not exist, this behaves like write_ohlcv.
    """
    if not rows:
        return 0
    path = parquet_path(cache, symbol, tf)
    new_df = pd.DataFrame(rows, columns=["t", "o", "h", "l", "c", "v"])  # timestamp ms
    new_df["t"] = pd.to_datetime(new_df["t"], unit="ms", utc=True)
    if path.exists():
        try:
            old = pd.read_parquet(path)
        except Exception:
            old = pd.DataFrame(columns=["t", "o", "h", "l", "c", "v"])  # fallback to only new
        df = pd.concat([old, new_df], ignore_index=True)
    else:
        df = new_df
    df = df.drop_duplicates(subset="t").sort_values("t")

    # Write and optionally mirror to DuckDB
    df.to_parquet(path, index=False)
    _mirror_to_duckdb(cache, symbol, tf, path)
    return len(df)


def _mirror_enabled() -> bool:
    """Return True if DUCKDB mirroring is enabled (default True)."""
    v = os.getenv("DUCKDB_MIRROR", "1").strip().lower()
    return v in ("1", "true", "yes", "on")


def _mirror_to_duckdb(cache: pathlib.Path, symbol: str, tf: str, parquet_file: pathlib.Path) -> None:
    if not _mirror_enabled():
        return
    try:
        db_path = cache / "data.duckdb"
        with duckdb.connect(db_path.as_posix()) as con:
            con.execute("CREATE SCHEMA IF NOT EXISTS cache;")
            table = f"cache.ohlcv_{symbol.lower()}_{tf.lower()}"
            con.execute(f"DROP TABLE IF EXISTS {table};")
            con.execute(f"CREATE TABLE {table} AS SELECT * FROM read_parquet('{parquet_file.as_posix()}');")
    except Exception as e:
        LOG.warning("DuckDB mirror failed for %s %s: %r", symbol, tf, e)


def load(cache: str | pathlib.Path, symbol: str, tf: str, cols: Optional[Iterable[str]] = None) -> pd.DataFrame:
    """Load cached OHLCV as DataFrame; select columns if provided.

    Example: load(cache, "BTC", "4h", cols=["t","c"]).
    """
    path = parquet_path(pathlib.Path(cache), symbol, tf)
    if not path.exists():
        raise FileNotFoundError(f"Missing cache for {symbol} {tf}: {path}")
    df = pd.read_parquet(path)
    return df[list(cols)] if cols else df


def latest_timestamp(cache: str | pathlib.Path, symbol: str, tf: str) -> Optional[pd.Timestamp]:
    """Return latest timestamp in cache for symbol/tf, or None if missing.

    Reads only the 't' column for efficiency.
    """
    path = parquet_path(pathlib.Path(cache), symbol, tf)
    if not path.exists():
        return None
    try:
        df = pd.read_parquet(path, columns=["t"])  # type: ignore[arg-type]
    except Exception:  # corrupt or incompatible
        return None
    if df.empty:
        return None
    # Ensure tz-aware UTC
    t = pd.to_datetime(df["t"]).max()
    if t.tzinfo is None:
        t = t.tz_localize("UTC")
    return t

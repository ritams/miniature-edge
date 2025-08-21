from __future__ import annotations
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

    # Register/update in DuckDB for convenience
    db_path = cache / "data.duckdb"
    with duckdb.connect(db_path.as_posix()) as con:
        con.execute("CREATE SCHEMA IF NOT EXISTS cache;")
        table = f"cache.ohlcv_{symbol.lower()}_{tf.lower()}"
        con.execute(f"DROP TABLE IF EXISTS {table};")
        con.execute(f"CREATE TABLE {table} AS SELECT * FROM read_parquet('{path.as_posix()}');")
    return len(df)


def load(cache: str | pathlib.Path, symbol: str, tf: str, cols: Optional[Iterable[str]] = None) -> pd.DataFrame:
    """Load cached OHLCV as DataFrame; select columns if provided.

    Example: load(cache, "BTC", "4h", cols=["t","c"]).
    """
    path = parquet_path(pathlib.Path(cache), symbol, tf)
    if not path.exists():
        raise FileNotFoundError(f"Missing cache for {symbol} {tf}: {path}")
    df = pd.read_parquet(path)
    return df[list(cols)] if cols else df

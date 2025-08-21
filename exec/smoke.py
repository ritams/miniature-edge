from __future__ import annotations
import tempfile
import time
import pathlib
import pandas as pd

from common.timeframe import tf_to_seconds, tf_to_pandas_freq
from features.store import cache_dir, upsert_ohlcv, load


def _now_ms() -> int:
    return int(time.time() * 1000)


def test_timeframe_utils() -> None:
    assert tf_to_seconds("1h") == 3600
    assert tf_to_seconds("4h") == 4 * 3600
    assert tf_to_seconds("1d") == 86400
    assert tf_to_seconds("15m") == 15 * 60
    assert tf_to_pandas_freq("1h") in ("1h", "1H")
    assert tf_to_pandas_freq("4h") in ("4h", "4H")
    assert tf_to_pandas_freq("1d") == "1D"
    assert tf_to_pandas_freq("15m") in ("15min", "15T")


def test_upsert_dedup() -> None:
    with tempfile.TemporaryDirectory() as d:
        cache = cache_dir(d)
        symbol, tf = "TEST", "1h"
        ms0 = _now_ms() - 3 * 3600_000
        rows1 = [
            [ms0 + 0 * 3600_000, 1, 2, 0.5, 1.5, 100],
            [ms0 + 1 * 3600_000, 1.5, 2.5, 1.0, 2.0, 200],
            [ms0 + 2 * 3600_000, 2.0, 3.0, 1.5, 2.5, 300],
        ]
        n1 = upsert_ohlcv(cache, symbol, tf, rows1)
        assert n1 == 3
        # Upsert overlapping (duplicate last), plus one new
        rows2 = [
            [ms0 + 2 * 3600_000, 2.0, 3.0, 1.5, 2.5, 300],
            [ms0 + 3 * 3600_000, 2.5, 3.5, 2.0, 3.0, 400],
        ]
        n2 = upsert_ohlcv(cache, symbol, tf, rows2)
        assert n2 == 4
        df = load(cache, symbol, tf)
        assert len(df) == 4
        assert df["t"].is_monotonic_increasing


def test_merge_tolerance() -> None:
    # Build two frames 30 minutes apart, apply backward asof with 1h tol
    base_t = pd.to_datetime(_now_ms(), unit="ms", utc=True).floor("h")
    coin = pd.DataFrame({
        "t": [base_t, base_t + pd.Timedelta(hours=1), base_t + pd.Timedelta(hours=2)],
        "c": [10.0, 10.5, 11.0],
    })
    apex = pd.DataFrame({
        # Apex lags by 30 minutes
        "t": [base_t - pd.Timedelta(minutes=30), base_t + pd.Timedelta(minutes=30), base_t + pd.Timedelta(hours=1, minutes=30)],
        "c": [100.0, 101.0, 102.0],
    })
    tol = pd.Timedelta(seconds=tf_to_seconds("1h") // 2)
    merged = pd.merge_asof(
        coin.sort_values("t"),
        apex.sort_values("t"),
        on="t",
        direction="backward",
        tolerance=tol,
        suffixes=("_coin", "_apex"),
    )
    # Ensure both aligned series exist and have no nulls
    assert {"c_coin", "c_apex"}.issubset(set(merged.columns))
    assert merged["c_coin"].notna().all()
    assert merged["c_apex"].notna().all()


def main() -> None:
    test_timeframe_utils()
    test_upsert_dedup()
    test_merge_tolerance()
    print("SMOKE OK")


if __name__ == "__main__":
    main()

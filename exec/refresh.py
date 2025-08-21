from __future__ import annotations
import os
import logging
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

from common.logging import setup_logging
from common.timeframe import tf_to_seconds
from config.loader import load_settings
from features.store import cache_dir, latest_timestamp, upsert_ohlcv
from ingest.ccxt_client import get_exchange, fetch_ohlcv


LOG = logging.getLogger(__name__)


def _env(name: str) -> str | None:
    """Return non-empty env var or None."""
    v = os.getenv(name)
    return v if v and v.strip() else None


def _initial_since_ms(tf: str, *, lookback_bars: int) -> int:
    """Compute start timestamp (ms) for initial backfill given bars and tf."""
    secs = tf_to_seconds(tf)
    dt = datetime.now(timezone.utc) - timedelta(seconds=secs * lookback_bars)
    return int(dt.timestamp() * 1000)


def _refresh_symbol_tf(ex, cache, base: str, tf: str, *, limit: int, lookback_bars: int) -> int:
    """Incrementally refresh one symbol/tf with pagination and upsert.

    Returns number of rows after write.
    """
    last = latest_timestamp(cache, base, tf)
    since_ms = int(last.timestamp() * 1000) + 1 if last is not None else _initial_since_ms(tf, lookback_bars=lookback_bars)
    total_written = 0
    while True:
        rows = fetch_ohlcv(ex, base=base, tf=tf, since_ms=since_ms, limit=limit)
        if not rows:
            break
        total_written = upsert_ohlcv(cache, symbol=base, tf=tf, rows=rows)
        since_ms = int(rows[-1][0]) + 1
        if len(rows) < limit:
            break
    return total_written


def main() -> None:
    setup_logging()
    # Load environment variables from .env (if present)
    load_dotenv()

    config_path = os.getenv("CONFIG_PATH", "config/config.yaml")
    cache_path = os.getenv("CACHE_PATH", ".cache")

    settings = load_settings(config_path)

    ex = get_exchange(
        settings.data_sources.spot_exchange,
        api_key=_env("BINANCE_API_KEY"),
        api_secret=_env("BINANCE_API_SECRET"),
    )

    cache = cache_dir(cache_path)

    symbols = settings.basket.symbols
    timeframes = [settings.timeframes.ltf, settings.timeframes.htf]

    limit = int(os.getenv("BACKFILL_LIMIT", "1000"))
    lookback_bars = int(os.getenv("BACKFILL_LOOKBACK_BARS", str(limit)))

    LOG.info("Refreshing cache to %s for %s symbols across %s timeframes", cache, len(symbols), len(timeframes))

    for base in symbols:
        for tf in timeframes:
            n = _refresh_symbol_tf(ex, cache, base, tf, limit=limit, lookback_bars=lookback_bars)
            LOG.info("%s %s -> %s rows (post-refresh)", base, tf, n)

    LOG.info("Refresh complete")


if __name__ == "__main__":
    main()

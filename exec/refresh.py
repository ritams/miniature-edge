from __future__ import annotations
import os
import logging
from dotenv import load_dotenv

from common.logging import setup_logging
from config.loader import load_settings
from features.store import cache_dir, write_ohlcv
from ingest.ccxt_client import get_exchange, fetch_ohlcv


LOG = logging.getLogger(__name__)


def _env(name: str) -> str | None:
    v = os.getenv(name)
    return v if v and v.strip() else None


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

    LOG.info("Refreshing cache to %s for %s symbols across %s timeframes", cache, len(symbols), len(timeframes))

    total = 0
    for base in symbols:
        for tf in timeframes:
            rows = fetch_ohlcv(ex, base=base, tf=tf)
            n = write_ohlcv(cache, symbol=base, tf=tf, rows=rows)
            LOG.info("%s %s -> %s rows", base, tf, n)
            total += n

    LOG.info("Refresh complete. Total rows written: %s", total)


if __name__ == "__main__":
    main()

from __future__ import annotations
import os
import time
from typing import Any, Dict, List, Optional
import logging

import ccxt  # type: ignore


LOG = logging.getLogger(__name__)

_TIMEFRAME_MAP: Dict[str, str] = {
    "1h": "1h",
    "4h": "4h",
    "D": "1d",
    "1d": "1d",
}


def _fmt_symbol(base: str, quote: Optional[str] = None) -> str:
    q = quote if quote is not None else os.getenv("QUOTE_ASSET", "USDT")
    return f"{base}/{q}"


def get_exchange(name: str, api_key: Optional[str] = None, api_secret: Optional[str] = None) -> Any:
    """Instantiate a CCXT exchange client with sane defaults.

    For public OHLCV, keys are optional.
    """
    if not hasattr(ccxt, name):
        raise ValueError(f"Unsupported exchange: {name}")
    klass = getattr(ccxt, name)
    opts = {"enableRateLimit": True}
    if api_key and api_secret:
        opts.update({"apiKey": api_key, "secret": api_secret})
    ex = klass(opts)
    return ex


def fetch_ohlcv(
    ex: Any,
    base: str,
    tf: str,
    since_ms: Optional[int] = None,
    limit: Optional[int] = None,
    *,
    quote: Optional[str] = None,
    backfill_limit: Optional[int] = None,
) -> List[List[Any]]:
    """Fetch OHLCV rows with simple retries.

    Returns CCXT-standard rows: [timestamp, open, high, low, close, volume]
    """
    symbol = _fmt_symbol(base, quote=quote)
    ccxt_tf = _TIMEFRAME_MAP.get(tf, tf)
    attempts = 0
    last_err: Optional[Exception] = None
    while attempts < 5:
        try:
            bl = backfill_limit if backfill_limit is not None else int(os.getenv("BACKFILL_LIMIT", "1000"))
            return ex.fetch_ohlcv(symbol, timeframe=ccxt_tf, since=since_ms, limit=limit or bl)
        except Exception as e:  # retry on transient errors
            last_err = e
            attempts += 1
            sleep_s = min(2 ** attempts, 10)
            LOG.warning("fetch_ohlcv retry %s for %s %s due to %r", attempts, symbol, ccxt_tf, e)
            time.sleep(sleep_s)
    raise RuntimeError(f"Failed to fetch OHLCV for {symbol} {ccxt_tf}: {last_err}")

# miniature-edge

Personal crypto research and alerting stack: ingest OHLCV, cache, scan rotations, confirm signals, and send Telegram alerts.

## Quickstart

1. Install UV (Python package manager):
   - macOS: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Clone and enter the repo, then create a `.env` from example:
   - `cp .env.example .env`
3. Set Telegram vars in `.env` (required for alerts):
   - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
4. Optional exchange keys for higher limits: `BINANCE_API_KEY`, `BINANCE_API_SECRET`.
5. Run refresh to build or update the local cache incrementally:
   - `uv run refresh`
6. Audit cache integrity (missing bars, duplicates):
   - `uv run audit`
7. Run a scan (example scan CLI is available):
   - `uv run scan`

Notes:
- Cache is written to `.cache/ohlcv/*.parquet` and mirrored to `data.duckdb` for convenience.
- Incremental refresh paginates and upserts by timestamp; initial backfill uses `BACKFILL_LOOKBACK_BARS` bars.

## Environment variables

- CONFIG_PATH: path to YAML config (default `config/config.yaml`).
- CACHE_PATH: cache directory (default `.cache`).
- QUOTE_ASSET: quote asset for symbols (default `USDT`).
- BACKFILL_LIMIT: max rows per OHLCV call (default `1000`).
- BACKFILL_LOOKBACK_BARS: initial backfill bars when no cache (default `1000`).
- DUCKDB_MIRROR: set to `0`/`false` to skip mirroring parquet to DuckDB (default `1`).
- TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID: required to send alerts.
- BINANCE_API_KEY, BINANCE_API_SECRET: optional, for higher rate limits.

## Commands

- `uv run refresh` — Incremental OHLCV refresh for configured basket and timeframes.
- `uv run audit` — Report per-symbol timeframe gaps and duplicates.
- `uv run scan` — Rotation scan over cached data to identify lagging alts.
- `uv run alert-test` — Send a test Telegram message.
- `uv run smoke` — Local smoke tests for utils, upsert de-duplication, and time alignment.

## Design

- Minimal, modular functions; YAML config validated by Pydantic (`config/models.py`).
- Timeframe helpers in `common/timeframe.py` keep seconds/frequencies consistent.
- Cache utilities in `features/store.py` provide `upsert_ohlcv`, `latest_timestamp`, and DuckDB mirroring.

## Tuning rotation scan

- Set `apex.move_lookback_bars` (default 3) in `config/config.yaml` to compute moves over multiple LTF bars.
  Example: with `ltf: "1h"` and `move_lookback_bars: 3`, the move is measured across the last 3 hours.
  Consider pairing with thresholds like `move_threshold_pct: 2-3`, `alt_lag_threshold_pct: ~2`, `corr_min: 0.6`, `beta_min: 1.2` depending on aggressiveness.

## Safety & limits

- Refresh uses exchange rate limits (CCXT) and retries on transient errors.
- Timestamps in logs are UTC.

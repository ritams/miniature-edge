---
title: Data
level: topic
parent: memory/architecture/index.md
updated: 2025-08-20
tags: [data, quality]
---

# Data

- Sources: Binance (spot via CCXT), Hyperliquid (perps via SDK).
- Timeframes: HTF 4h, LTF 1h. Refresh cadence: 10–15m.
- Storage: Parquet + DuckDB; partition by symbol/tf/date.
- Schema: Bar, FeatureRow, SignalRecord, TradeRecord.
- Quality (M0.5):
  - Audit missing/duplicate bars per symbol/tf.
  - Align bar closes to UTC; identical boundaries across symbols.
  - NA handling and winsorization policy documented.

See also: [Backtesting](./backtesting.md) • [Methods](./methods/index.md)

Back to: [Architecture](./architecture/index.md) • [Root](./memory.md)

---
title: Ops (uv)
level: topic
parent: memory/practice/index.md
updated: 2025-08-20
tags: [ops, uv]
---

# Ops (uv)

- Env/runner: uv (no Makefile).
- CLI targets:
  - `uv run refresh` — backfill/cache and run data audits (M0+M0.5).
  - `uv run backtest` — walk-forward backtests (M1) with CSV outputs.
  - `uv run scan` — M3–M7 pipeline and alerts.
- Layout: `/ingest`, `/features`, `/signals`, `/exec`, `/tests`.
- Logging: JSON logs + run metadata (config hash, data snapshot id).

See also: [Backtesting](./backtesting.md)

Back to: [Practice](./practice/index.md) • [Root](./memory.md)

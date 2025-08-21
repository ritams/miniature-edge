---
title: TD Sequential (strict)
level: leaf
parent: memory/methods/index.md
updated: 2025-08-20
tags: [td, risk]
---

# TD Sequential (strict)

- Price flip: momentum shift that starts a Setup.
- Setup: count 1–9; Perfection if bars 8/9 exceed key highs/lows.
- Countdown: 1–13 non-consecutive after a valid setup.
- TDST: support/resistance lines from bar-1 extremes.

Settings (defaults):
- strict_perfection = true
- htf = 4h, ltf = 1h
- cooldown_bars = 6

Usage:
- If TD contributes, default SL beyond TDST; else use ATR-based stops.
- Scoring boosts perfected 9s/13s; penalizes early/incomplete setups.

See also: [Indicators](./indicators.md) • [Methods Overview](./index.md)

Back to: [Methods](./index.md) • [Architecture](../architecture/index.md) • [Root](../memory.md)

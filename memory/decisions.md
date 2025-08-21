---
title: Decisions
level: topic
parent: memory/reference/index.md
updated: 2025-08-20
tags: [decisions]
---

# Architectural & Trading Decisions

## ADR-0001 Use uv instead of Makefile
- Date: 2025-08-20
- Context: Simpler local env and script runner.
- Decision: Use uv for env, locking, and `uv run` for CLIs.
- Alternatives: Poetry+Makefile. Rejected for added indirection.

## ADR-0002 Defer Narrative (M2)
- Date: 2025-08-20
- Context: Reduce noise; validate core alpha first (M3–M7).
- Decision: Implement after core passes backtest gates.
- Alternatives: Build M2 now. Rejected due to complexity and API limits.

Back to: [Reference](./reference/index.md) • [Root](./memory.md)

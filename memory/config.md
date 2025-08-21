---
title: Config (defaults)
level: topic
parent: memory/reference/index.md
updated: 2025-08-20
tags: [config]
---

# Config (defaults)

```yaml
project:
  environment: "python+uv"
data_sources:
  spot_exchange: "binance"
  perps_venue: "hyperliquid"
timeframes:
  htf: "4h"
  ltf: "1h"
basket:
  symbols: ["BTC","ETH","SOL","LINK","ARB","OP","APT","HBAR","INJ","AVAX","MATIC","XRP","LTC","DOGE","SUI","SEI","TIA"]
costs:
  spot_fee_pct: 0.10
  spot_slippage_pct: 0.05
  perps_taker_fee_pct: 0.04
  perps_maker_fee_pct: 0.02
  include_funding: true
apex:
  move_threshold_pct: 4.0
  alt_lag_threshold_pct: 1.5
  corr_min: 0.7
  beta_min: 1.5
market_filters:
  volume_x: 2.0
  breakout_lookback: 20
td:
  strict_perfection: true
  htf: "4h"
  ltf: "1h"
  cooldown_bars: 6
risk:
  risk_per_trade_pct: 0.75
  use_tdst_stop_when_td: true
  atr_mult_tp: 1.2
```

Canonical source: [`context.md`](../context.md)

Back to: [Reference](./reference/index.md) • [Root](./memory.md)

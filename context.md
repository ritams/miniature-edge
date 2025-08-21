# Milestones (v3)

## M0 — Foundations & Data Plane

**Goal:** a reliable spine (configs, data, logging) so every later module plugs in without churn.
**Build**

* Repo layout (`/ingest`, `/features`, `/signals`, `/exec`, `/tests`), typed config (YAML → pydantic), structured logging.
* **Connectors:** CCXT + Hyperliquid (spot+perp) with retry/backoff; unify rate-limit/backfill.&#x20;
* **FeatureStore:** DuckDB/Parquet cache; canonical resampling (1h/4h/D); idempotent refresh.
* **Schemas:** `Bar`, `FeatureRow`, `SignalRecord`, `TradeRecord` (JSONL + Parquet).
  **Acceptance**
* One command (`uv run refresh`) fills the cache for BTC/ETH + starter basket and prints row counts.
* Any module can `load(symbol, tf, cols=[...])` and get identical arrays across runs.

## M0.5 — Data Quality & Integrity

**Goal:** reliable backfills and aligned series across symbols/timeframes.
**Build**

* Backfill audit: report duplicates/missing bars per `symbol/tf`; align BTC/ETH/alt basket on identical bar closes (UTC).
* Normalize timezones and bar-close semantics; enforce schema for `Bar`/`FeatureRow`.
* Data cleaning policy: NA handling, outlier winsorization rules documented.
  **Acceptance**
* Missing/duplicate bars report is generated; after backfill, missing bars ≤ 0.1% per series.
* All symbols share identical bar boundaries; repeated refresh yields identical summary stats.

## M1 — Research & Backtest Harness (new, first-class)

**Goal:** quantify each filter’s lift **before** it hits prod.
**Build**

* Vectorized walk-forward backtester (rolling splits), fee+slippage, MFE/MAE, Sharpe, DD.
* Toggle flags: `use_td`, `use_volume_x2`, `apex_move_threshold`, `corr/beta` gates; ablations.
* Plot pack: equity, hit-rate by signal type, confusion matrices by regime.
  **Acceptance**
* Given a fixed seed + config, backtest is reproducible; exports CSV of trades + summary.

## M2 — Narrative Detection Engine (Deferred)

**Goal:** structured, timestamped narrative context (not trade signals).
**Status:** Deferred until the core stack (M3–M7) is validated.
**Build**

* Ingest curated influencer tweets; extract tickers/hashtags/sentiment (pos/neg/neutral).
* Output JSON/CSV with `symbol`, `when`, `author`, `sentiment`, `confidence`.&#x20;
  **Acceptance**
* For a replayed day of tweets, ≥95% of tagged symbols appear with correct timestamps.

## M3 — Apex Rotation Scanner (ex-1.5)

**Goal:** find **lagging** alts when BTC/ETH break out.
**Build**

* Inputs: OHLCV for BTC, ETH, alt basket; 14D/30D rolling Pearson corr & beta.
* Trigger (defaults): **apex ≥ +4%** (4h/D), **alt ≤ +1.5%**, **corr ≥ 0.7**, **beta ≥ 1.5** ⇒ `LAGGING_ROTATION`.&#x20;
* Output (example):
  `{"symbol":"APT","apex_asset":"ETH","apex_move":"+5.2%","coin_move":"+1.0%","correlation":0.84,"beta":1.87,"signal_strength":"HIGH","status":"LAGGING_ROTATION"}`.&#x20;
* Starter basket persisted + historical corr/beta for smart rotation (APT, LINK, HBAR… HYPE).&#x20;
  **Acceptance**
* On a synthetic “ETH +5% day,” coins with `(corr>=0.7 & beta>=1.5 & coin<=+1.5%)` are flagged; others aren’t.

## M4 — Market Confirmation Layer

**Goal:** validate M3 candidates with **market** proof.
**Build**

* Data: spot+perp price/volume, OI, funding (from CCXT/Hyperliquid where available).
* Filters (composable): volume spikes (e.g., **×2 in 1h**), structure breakouts, OI shifts, funding flips. Apply **only** to M3 pass list.&#x20;
  **Acceptance**
* Rule composition works (e.g., “vol×2 **AND** breakout”). Module returns pass/fail + reasons.

## M5 — Technical Indicator Engine (incl. **TD Sequential**)

**Goal:** compact, testable tech stack that adds **exhaustion context** via TD.
**Build**

* Classic set: RSI, MACD, EMA stack, Fibonacci zones, volume trend; “**2-of-5 pass**” logic; retest checks; basic R\:R & SL.&#x20;
* **TD Sequential**:

  * Compute **price flips**, **Setup (1–9)** (+ optional **Perfection**), **Countdown (1–13)**, and **TDST** (bar-1 high/low) per symbol/tf.
  * Emit flags: `td.setup_type`, `td.setup_count`, `td.perfected`, `td.countdown`, `td.tdst_buy/sell`, `td.tdst_breach`.
  * Config: strict vs loose (perfection on/off, grace windows), HTF/LTF blend.
    **Acceptance**
* Unit tests with synthetic sequences verify: setup resets, perfection on 8/9, non-consecutive countdown, TDST persistence.

## M6 — Regime & Risk (new)

**Goal:** avoid fading freight trains; standardize SL sizing.
**Build**

* Regime classifier (trend vs chop): ADX/EMA-stack + volatility band heuristic.
* Risk model: if TD contributes, default **SL beyond TDST**; else structure/ATR; position size from stop distance.
  **Acceptance**
* In “trend” fixtures, TD sell fades are down-weighted/blocked; in “chop”, allowed.

## M7 — Signal Composer & Scoring

**Goal:** unify everything into a single, explainable score.
**Build**

* Inputs: (M2) narrative (when enabled), (M3) rotation context, (M4) confirmations, (M5) technicals+TD, (M6) regime/risk.
* Score blocks: `narrative_score`, `market_score`, `technical_score`, `rotation_bonus`, `td_signal` (boost perfected 9s/13s, penalize early setups).
* **Conflict resolver:** suppress when HTF and LTF TD conflict; **cool-down/hysteresis** to prevent rapid re-fires.
  **Acceptance**
* Given identical inputs, score is deterministic; “reasons” array lists every pass/fail that contributed.

## M8 — Alerts & Delivery

**Goal:** actionable alerts you can trade or ignore at a glance.
**Build**

* Rich payload: symbol/tf, score, reasons, RR, invalidation (TDST when TD contributes), status (“Waiting for retest”, etc.).
* Channels: Telegram / Discord / Notion webhooks.&#x20;
  **Acceptance**
* A sample day produces alerts that include: (a) top 3 reasons, (b) explicit invalidation, (c) link to a per-signal chart/screenshot (optional).

## M9 — Dry-Run Execution & Analytics

**Goal:** close the loop with PnL + behavior analysis.
**Build**

* Templates:

  * **Rotation swing:** limit near TDST (buy setup) with SL beyond TDST; TP = k·ATR or structure high.
  * **TD13 exhaustion:** market/limit + “Risk Level”/TDST invalidation.
* Logs: entries/exits, SL/TP, win-rate, PnL; export CSV/Notion.&#x20;
  **Acceptance**
* For any alert, you can trace the simulated trade and its PnL; batch summaries group by signal archetype.

---

# Execution Flow (wire-level)

1. **Refresh loop:** fetch OHLCV (1h/4h/D) → cache/resample (M0).
2. **M3:** compute corr/beta; when **apex ≥ +4%**, flag **laggards** (corr/beta gated).&#x20;
3. **M4:** confirm candidates (vol×2, breakout, OI/funding flips).&#x20;
4. **M5:** compute RSI/MACD/EMA/Fib/volume + **TD state**, attach TDST.&#x20;
5. **M6:** gate by regime; set default SL via TDST when TD is in-play.
6. **M7:** compose & score (narrative + market + technical + rotation + TD), resolve conflicts, apply cool-down.
7. **M8:** emit alert (score, reasons, RR, invalidation) to channels.&#x20;
8. **M9:** simulate entries/exits; write PnL & analytics.&#x20;

---

# Engineering Details (so you can start)

**Key data objects**

```json
// Feature row (per symbol/tf/bar)
{"t":"2025-08-18T12:00:00Z","symbol":"SOL","tf":"4h",
 "ret":0.012,"vol_z":1.9,"oi_chg":0.07,"funding":0.02,
 "corr_eth_14":0.81,"beta_eth_30":1.65,
 "td":{"flip":"bearish","setup_type":"buy","setup_count":7,"perfected":false,
       "countdown":0,"tdst_buy":155.8,"tdst_sell":null}}
```

**Config knobs (excerpt)**

```yaml
project:
  environment: "python+uv"   # use `uv` for env, scripts, and reproducible runs
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
  volume_x: 2.0           # last bar volume ≥ 2× EMA20
  breakout_lookback: 20   # price > 20-bar high (+0.5×ATR optional)
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

**Module APIs (minimal)**

* `features.load(symbol, tf, cols) -> DataFrame`
* `rotation.scan(apex_assets, basket, cfg) -> [RotationCandidate]`
* `confirm.apply(candidates, rules) -> [Confirmed]`
* `td.compute(df) -> df_with_td_state`
* `score.compose(context) -> ScoredSignal`
* `alerts.send(signal) -> None`
* `sim.run(signals, templates) -> TradesReport`

---


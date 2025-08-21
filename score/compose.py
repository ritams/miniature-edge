from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
import json
import pathlib
import time

from confirm.rules import Confirmed
from common.timeframe import tf_to_seconds
from features.store import load
from indicators.td import compute as td_compute


@dataclass(frozen=True)
class ScoredSignal:
    symbol: str
    tf: str
    score: float
    reasons: List[str]

def _cooldown_ok(cache: str | pathlib.Path, key: str, bars: int, tf: str) -> bool:
    """Return True if cooldown has expired and update the marker.

    Creates cache directory if missing.
    """
    cache_dir = pathlib.Path(cache)
    cache_dir.mkdir(parents=True, exist_ok=True)
    p = cache_dir / "cooldowns.json"
    try:
        data: Dict[str, int] = json.loads(p.read_text())
    except FileNotFoundError:
        data = {}
    last = data.get(key, 0)
    now = int(time.time())
    if now - last < bars * tf_to_seconds(tf):
        return False
    data[key] = now
    p.write_text(json.dumps(data))
    return True


def compose(confirmed: List[Confirmed], *, cache: str, tf: str, cooldown_bars: int, strict_perfection: bool) -> List[ScoredSignal]:
    out: List[ScoredSignal] = []
    for c in confirmed:
        if not c.passed:
            continue
        key = f"{c.candidate.symbol}:{tf}"
        if not _cooldown_ok(cache, key, cooldown_bars, tf):
            continue
        # Start with existing reasons from confirmations
        reasons: List[str] = list(c.reasons)

        # Compute TD state on last bar for this symbol/timeframe
        try:
            df = load(cache, c.candidate.symbol, tf, cols=["t", "h", "l", "c"])  # ensure price fields
            td = td_compute(df, strict_perfection=strict_perfection)
            if td.setup_type and td.setup_count > 0:
                reasons.append(f"td_{td.setup_type}_{td.setup_count}/9")
            if td.perfected:
                reasons.append("td_perfected")
            if td.tdst_buy is not None:
                reasons.append(f"tdst_buy={td.tdst_buy:.2f}")
            if td.tdst_sell is not None:
                reasons.append(f"tdst_sell={td.tdst_sell:.2f}")
        except Exception:
            # TD is optional; ignore errors
            td = None  # type: ignore

        base = 50.0
        bonus = 0.0
        if c.candidate.signal_strength == "HIGH":
            bonus += 20
        if any("breakout" in r for r in reasons):
            bonus += 15
        if any("vol>=" in r for r in reasons):
            bonus += 10

        # TD-based adjustments (lightweight heuristic)
        if td is not None:
            try:
                if getattr(td, "perfected", False) and getattr(td, "setup_count", 0) >= 8:
                    bonus += 10
                elif getattr(td, "setup_count", 0) >= 6:
                    bonus += 5
                elif getattr(td, "setup_type", None) is not None and getattr(td, "setup_count", 0) <= 2:
                    bonus -= 5
            except Exception:
                pass

        score = max(0.0, min(100.0, base + bonus))
        out.append(ScoredSignal(symbol=c.candidate.symbol, tf=tf, score=score, reasons=reasons))
    return out

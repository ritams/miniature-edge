from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
import json
import pathlib
import time

from confirm.rules import Confirmed


@dataclass(frozen=True)
class ScoredSignal:
    symbol: str
    tf: str
    score: float
    reasons: List[str]

def _tf_seconds(tf: str) -> int:
    tf = tf.lower()
    if tf.endswith('h'):
        return int(tf[:-1]) * 3600
    if tf in ('1d', 'd', '1day'):
        return 86400
    if tf.endswith('m'):
        return int(tf[:-1]) * 60
    # default to 1h if unknown
    return 3600


def _cooldown_ok(cache: str | pathlib.Path, key: str, bars: int, tf: str) -> bool:
    p = pathlib.Path(cache) / "cooldowns.json"
    try:
        data: Dict[str, int] = json.loads(p.read_text())
    except FileNotFoundError:
        data = {}
    last = data.get(key, 0)
    now = int(time.time())
    if now - last < bars * _tf_seconds(tf):
        return False
    data[key] = now
    p.write_text(json.dumps(data))
    return True


def compose(confirmed: List[Confirmed], *, cache: str, tf: str, cooldown_bars: int) -> List[ScoredSignal]:
    out: List[ScoredSignal] = []
    for c in confirmed:
        if not c.passed:
            continue
        key = f"{c.candidate.symbol}:{tf}"
        if not _cooldown_ok(cache, key, cooldown_bars, tf):
            continue
        base = 50.0
        bonus = 0.0
        if c.candidate.signal_strength == "HIGH":
            bonus += 20
        if any("breakout" in r for r in c.reasons):
            bonus += 15
        if any("vol>=" in r for r in c.reasons):
            bonus += 10
        score = min(100.0, base + bonus)
        out.append(ScoredSignal(symbol=c.candidate.symbol, tf=tf, score=score, reasons=c.reasons))
    return out

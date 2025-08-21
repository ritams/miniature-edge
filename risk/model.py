from __future__ import annotations
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class RiskResult:
    stop: float
    qty: float


def position_size(entry: float, stop: float, equity: float, risk_pct: float) -> RiskResult:
    risk_amt = equity * (risk_pct / 100.0)
    per_unit = abs(entry - stop)
    if per_unit <= 0:
        raise ValueError("Invalid stop distance")
    qty = risk_amt / per_unit
    return RiskResult(stop=stop, qty=qty)

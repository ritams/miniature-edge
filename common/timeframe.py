from __future__ import annotations
import datetime as _dt


def tf_to_seconds(tf: str) -> int:
    """Return timeframe duration in seconds.

    Supports: Xm, Xh, 1d/D. Defaults to 1h when unknown.
    """
    t = tf.strip().lower()
    if t.endswith("m") and t[:-1].isdigit():
        return int(t[:-1]) * 60
    if t.endswith("h") and t[:-1].isdigit():
        return int(t[:-1]) * 3600
    if t in ("1d", "d", "1day"):
        return 86400
    return 3600


def tf_to_pandas_freq(tf: str) -> str:
    """Return pandas frequency alias for a timeframe.

    Examples: 1h -> 1H, 4h -> 4H, 1d/D -> 1D.
    """
    t = tf.strip().lower()
    if t.endswith("m") and t[:-1].isdigit():
        return f"{int(t[:-1])}min"  # minute frequency
    if t.endswith("h") and t[:-1].isdigit():
        return f"{int(t[:-1])}h"
    if t in ("1d", "d", "1day"):
        return "1D"
    return "1H"

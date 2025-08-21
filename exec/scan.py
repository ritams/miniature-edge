from __future__ import annotations
import os
import logging
from datetime import datetime, timezone

from dotenv import load_dotenv

from common.logging import setup_logging
from config.loader import load_settings
from rotation.scan import scan as rotation_scan
from confirm.rules import apply as confirm_apply
from score.compose import compose
from alerts.telegram import send as tg_send


def main() -> None:
    load_dotenv()
    setup_logging()
    LOG = logging.getLogger(__name__)

    cfg = load_settings(os.getenv("CONFIG_PATH", "config/config.yaml"))
    cache = os.getenv("CACHE_PATH", ".cache")

    apex_assets = ["BTC", "ETH"]  # sensible default apex assets

    # Environment overrides so we can tune without touching config.yaml
    def _env_float(name: str, default: float) -> float:
        v = os.getenv(name)
        try:
            return float(v) if v is not None and v != "" else default
        except Exception:
            return default

    def _env_int(name: str, default: int) -> int:
        v = os.getenv(name)
        try:
            return int(v) if v is not None and v != "" else default
        except Exception:
            return default

    move_threshold_pct = _env_float("APEX_MOVE_THRESHOLD_PCT", cfg.apex.move_threshold_pct)
    alt_lag_threshold_pct = _env_float("APEX_ALT_LAG_THRESHOLD_PCT", cfg.apex.alt_lag_threshold_pct)
    corr_min = _env_float("APEX_CORR_MIN", cfg.apex.corr_min)
    beta_min = _env_float("APEX_BETA_MIN", cfg.apex.beta_min)
    move_lookback_bars = _env_int("APEX_MOVE_LOOKBACK_BARS", cfg.apex.move_lookback_bars)
    LOG.info(
        "scan thresholds: move>=%.2f%%, alt<=%.2f%%, corr>=%.2f, beta>=%.2f, lookback=%d bars",
        move_threshold_pct,
        alt_lag_threshold_pct,
        corr_min,
        beta_min,
        move_lookback_bars,
    )

    # 1) Rotation scan on LTF
    cands = rotation_scan(
        apex_assets,
        cfg.basket.symbols,
        tf=cfg.timeframes.ltf,
        cache=cache,
        move_threshold_pct=move_threshold_pct,
        alt_lag_threshold_pct=alt_lag_threshold_pct,
        corr_min=corr_min,
        beta_min=beta_min,
        move_lookback_bars=move_lookback_bars,
    )
    LOG.info("rotation candidates=%d", len(cands))
    if not cands:
        return

    # 2) Confirmations (volume x, breakout)
    conf = confirm_apply(
        cands,
        cache=cache,
        tf=cfg.timeframes.ltf,
        volume_x=cfg.market_filters.volume_x,
        breakout_lookback=cfg.market_filters.breakout_lookback,
    )
    passed = [x for x in conf if x.passed]
    LOG.info("confirmed=%d", len(passed))
    if not passed:
        return

    # 3) Compose + cooldown
    scored = compose(
        passed,
        cache=cache,
        tf=cfg.timeframes.ltf,
        cooldown_bars=cfg.td.cooldown_bars,
        strict_perfection=cfg.td.strict_perfection,
    )
    LOG.info("scored=%d", len(scored))

    # Quiet hours: 00-06 UTC by default
    now_utc = datetime.now(timezone.utc)
    quiet_off = os.getenv("QUIET_HOURS_OFF", "0") == "1"
    if (0 <= now_utc.hour < 6) and not quiet_off:
        LOG.info("within quiet hours (00-06 UTC); suppressing %d alerts", len(scored))
        return

    # 4) Alert via Telegram
    for s in scored:
        msg = (
            f"<b>{s.symbol}</b> {s.tf} score={s.score:.0f}\n"
            f"Reasons: {', '.join(s.reasons)}"
        )
        try:
            tg_send(msg)
            LOG.info("alert sent: %s", s.symbol)
        except Exception as e:
            LOG.exception("failed to send alert: %s", e)


if __name__ == "__main__":
    main()

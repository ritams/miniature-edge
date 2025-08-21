#!/usr/bin/env bash
# Miniature-Edge loop runner: refresh -> scan aligned to bar close
# Usage:
#   ./scripts/run_loop.sh            # runs forever
#   LOOP_ONESHOT=1 ./scripts/run_loop.sh   # run once (for testing)
#
# Env comes from .env (if present) and current shell. You can set overrides, e.g.:
#   export QUIET_HOURS_OFF=1
#   export APEX_MOVE_THRESHOLD_PCT=3.0
#   export APEX_ALT_LAG_THRESHOLD_PCT=2.5
#   export APEX_CORR_MIN=0.6
#   export APEX_BETA_MIN=1.2
#   export APEX_MOVE_LOOKBACK_BARS=3
#   ./scripts/run_loop.sh

set -euo pipefail

# Resolve project root (repo)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# Load .env if present (export all)
if [[ -f .env ]]; then
  set -o allexport
  # shellcheck disable=SC1091
  source .env
  set +o allexport
fi

# Checks
if ! command -v uv >/dev/null 2>&1; then
  echo "[ERROR] 'uv' not found in PATH. Install uv or adjust commands." >&2
  exit 1
fi

# Loop timing (defaults for 1h bars). Override via env as needed.
LOOP_BAR_SECONDS="${LOOP_BAR_SECONDS:-3600}"   # e.g., 3600 for 1h, 14400 for 4h
LOOP_OFFSET_SEC="${LOOP_OFFSET_SEC:-5}"        # extra seconds after bar close
LOOP_MIN_SLEEP_SEC="${LOOP_MIN_SLEEP_SEC:-10}" # minimum sleep to avoid tight loops

# Graceful shutdown
_running=1
trap 'echo "[INFO] Caught signal, exiting..."; _running=0' INT TERM

sleep_to_next_bar() {
  local now rem
  now=$(date -u +%s)
  rem=$(( LOOP_BAR_SECONDS - (now % LOOP_BAR_SECONDS) ))
  # Ensure non-negative and add offset
  if (( rem < 0 )); then rem=0; fi
  local total=$(( rem + LOOP_OFFSET_SEC ))
  if (( total < LOOP_MIN_SLEEP_SEC )); then
    total=$LOOP_MIN_SLEEP_SEC
  fi
  echo "[INFO] Sleeping ${total}s until next bar + offset (UTC)"
  sleep "$total"
}

run_once() {
  echo "[INFO] $(date -u +"%Y-%m-%dT%H:%M:%SZ") starting refresh"
  if ! uv run python -m exec.refresh; then
    echo "[ERROR] refresh failed" >&2
    return 1
  fi
  echo "[INFO] $(date -u +"%Y-%m-%dT%H:%M:%SZ") starting scan"
  if ! uv run python -m exec.scan; then
    echo "[ERROR] scan failed" >&2
    return 1
  fi
}

if [[ "${LOOP_ONESHOT:-0}" == "1" ]]; then
  run_once
  exit $?
fi

# Main loop
while (( _running )); do
  sleep_to_next_bar
  run_once || true
done

echo "[INFO] Loop exited"

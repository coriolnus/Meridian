#!/usr/bin/env bash
# deploy/hermes_api.sh — talk to a Meridian/Hermes agent over its HTTP API. Works against an IAP tunnel
# (http://localhost:8080) or any reachable host. Sends the shared token so authenticated endpoints accept
# the call. The API is the ONLY way in — the dashboard itself is just this API plus a UI.
#
#   BASE=http://localhost:8080 TOKEN=<MERIDIAN_DASH_TOKEN> ./deploy/hermes_api.sh status
#   ... reflect     # trigger ONE backtest-gated reflection now
#   ... skills      # skill catalog + Axis-2 recommendations
#   ... health | metrics    # unauthenticated liveness (no token needed)
set -euo pipefail
BASE="${BASE:-http://localhost:8080}"
TOKEN="${TOKEN:-}"
H=(); [ -n "$TOKEN" ] && H=(-H "x-meridian-token: ${TOKEN}")
pp(){ if command -v python3 >/dev/null; then python3 -m json.tool 2>/dev/null || cat; else cat; fi; }

case "${1:-status}" in
  status)  curl -fsS "${H[@]}" "$BASE/api/hermes" | pp ;;
  reflect) curl -fsS "${H[@]}" -X POST "$BASE/api/hermes/reflect" | pp ;;
  start)   curl -fsS "${H[@]}" -X POST "$BASE/api/hermes/start" | pp ;;
  stop)    curl -fsS "${H[@]}" -X POST "$BASE/api/hermes/stop" | pp ;;
  skills)  curl -fsS "${H[@]}" "$BASE/api/skills" | pp ;;
  health)  curl -fsS "$BASE/healthz" | pp ;;
  metrics) curl -fsS "$BASE/metrics" ;;
  *) echo "usage: $0 {status|reflect|start|stop|skills|health|metrics}"; exit 2 ;;
esac

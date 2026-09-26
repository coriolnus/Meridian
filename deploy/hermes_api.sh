#!/usr/bin/env bash
# deploy/hermes_api.sh — talk to a Meridian/Hermes agent over its HTTP API. Works against an IAP tunnel
# (http://localhost:8080) or any reachable host. Sends the shared token so authenticated endpoints accept
# the call. The API is the ONLY way in — the dashboard itself is just this API plus a UI.
#
#   BASE=http://localhost:8080 TOKEN=<MERIDIAN_DASH_TOKEN> ./deploy/hermes_api.sh status
#   ... reflect     # trigger ONE backtest-gated reflection now
#   ... skills      # skill catalog + Axis-2 recommendations
#   ... health | metrics    # unauthenticated liveness (no token needed)
#
# TOKEN NEVER ENTERS A PROCESS ARGV (TSK-226b, 2026-09-26): `-H "x-meridian-token: ${TOKEN}"` put the
# token on curl's command line, where `ps`/`/proc/<pid>/cmdline` show it to every user on the machine.
# The header is now read by curl from STDIN (`-H @-`, needs curl >= 7.55; measured on the operator Mac:
# curl 8.7.1, 2026-09-26 — the A1 curl version was NOT measured) and written by `jeton`, whose `printf`
# is a bash BUILTIN — no process is spawned, so no argv carries it.
# Output and exit codes are unchanged (tests/test_cp_rotasyon_v556.py G4a diffs old vs new form).
set -euo pipefail
BASE="${BASE:-http://localhost:8080}"
TOKEN="${TOKEN:-}"
H=(); [ -n "$TOKEN" ] && H=(-H @-)
jeton(){ if [ -n "$TOKEN" ]; then printf 'x-meridian-token: %s\n' "$TOKEN"; fi; }
pp(){ if command -v python3 >/dev/null; then python3 -m json.tool 2>/dev/null || cat; else cat; fi; }

case "${1:-status}" in
  status)  jeton | curl -fsS "${H[@]}" "$BASE/api/hermes" | pp ;;
  reflect) jeton | curl -fsS "${H[@]}" -X POST "$BASE/api/hermes/reflect" | pp ;;
  start)   jeton | curl -fsS "${H[@]}" -X POST "$BASE/api/hermes/start" | pp ;;
  stop)    jeton | curl -fsS "${H[@]}" -X POST "$BASE/api/hermes/stop" | pp ;;
  skills)  jeton | curl -fsS "${H[@]}" "$BASE/api/skills" | pp ;;
  health)  curl -fsS "$BASE/healthz" | pp ;;
  metrics) curl -fsS "$BASE/metrics" ;;
  *) echo "usage: $0 {status|reflect|start|stop|skills|health|metrics}"; exit 2 ;;
esac

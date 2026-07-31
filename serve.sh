#!/usr/bin/env bash
# serve.sh — start the Meridian dashboard locally (detached, survives this shell).
# Reach it at http://127.0.0.1:8080
# DURDURMA: `pkill -f "uvicorn meridian.api"` KULLANMA — probe havuzunu yetim bırakır.
# Elle durdurmak için: ./ops/stop-worker.sh  (süreç grubunu birlikte indirir; gerekçe o dosyada)
set -euo pipefail
cd "$(dirname "$0")"
[ -x .venv/bin/python ] || { command -v uv >/dev/null || { echo "install uv first"; exit 1; }; uv sync --extra dev; }
if launchctl print "gui/$(id -u)/com.meridian.agent" >/dev/null 2>&1; then
  echo "süpervizör (launchd) zaten yönetiyor — elle başlatma kapalı. Kaldırmak için: ./ops/supervise.sh uninstall"; exit 0
fi
# worker'ı durdur — süreç GRUBU bazlı (uvicorn + probe havuzu birlikte). Gerekçe ve mekanizma:
source ops/stop-worker.sh   # (2026-07-26 yetim sızıntısı vakasının belgesi o dosyanın başında)
stop_worker
# one-command up: seed state if empty, then advance to today (so the agent isn't stuck in the past)
# SQLite GEÇİŞİ SONRASI TUZAK KAPALI (WP-H/H9, 2026-07-31): `dbmigrate --uygula` sonrası defter
# `state/meridian.db` içindedir ve `state/trades.jsonl` `.migrated` ekiyle durur — yani tek başına
# `-s state/trades.jsonl` kontrolü DOLU bir defteri BOŞ görür ve 2022→bugün replay'i CANLI defterin
# üstüne koşardı. Koruma iki arka ucu birden ölçer.
if [ ! -s state/trades.jsonl ] && [ ! -s state/meridian.db ]; then
  echo "→ no state yet — seeding from history (2022 → today)…"
  .venv/bin/python -m meridian.run --dry-run --replay 2022-01-01:"$(date +%F)" || echo "  (seed skipped/failed — will run live cycles instead)"
fi
# auto-start the paper-advance scheduler AND the Hermes brain in-process when the app opens (local)
# Broker default = alpaca_paper (operator, 2026-07-18: "uygulama live'a geçsin" — LIVE PAPER trading on
# the connected Alpaca account). PAPER ONLY: adapters/alpaca.py hard-locks the hostname to
# paper-api.alpaca.markets — this switch can NEVER place a real-money order. Real money stays behind
# MERIDIAN_MODE=live + MERIDIAN_I_ACCEPT_RISK=true + autonomy_level>=1, all hand-set, none of them here.
# yerel sırlar (0600): MERIDIAN_DASH_TOKEN burada — parola kuruluyken betik/CLI erişimi
# x-meridian-token başlığıyla bu token üzerinden yürür (api._auth yol 2). Token .env'de durur,
# bu dosyaya yazılmaz (serve.sh 0755 — sır taşıyamaz).
[ -f .env ] && set -a && . ./.env && set +a
export MERIDIAN_BROKER="${MERIDIAN_BROKER:-alpaca_paper}"
export MERIDIAN_PARALLEL_PROBES=1   # 250-evren walk-forward'ları için süreç havuzu
export MERIDIAN_AUTOSTART_CYCLE="${MERIDIAN_AUTOSTART_CYCLE:-1}"
export CYCLE_POLL_SECONDS="${CYCLE_POLL_SECONDS:-300}"
export MERIDIAN_AUTOSTART_HERMES="${MERIDIAN_AUTOSTART_HERMES:-1}"
export HERMES_POLL_SECONDS="${HERMES_POLL_SECONDS:-300}"
.venv/bin/python -c "import subprocess,os; subprocess.Popen(['.venv/bin/python','-m','uvicorn','meridian.api:app','--host','127.0.0.1','--port','8080','--log-level','warning'], env=os.environ, stdout=open('state/dashboard.log','a'), stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)"
# kullanıcı-oturumu keepalive: sunucu çökerse 2 dk içinde diriltir (tekil örnek; detached)
nohup ./ops/keepalive.sh >/dev/null 2>&1 &
for i in $(seq 1 15); do [ "$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8080/ 2>/dev/null)" = "200" ] && { echo "✓ Meridian dashboard → http://127.0.0.1:8080"; exit 0; }; sleep 1; done
echo "server did not come up — see state/dashboard.log"; exit 1

#!/usr/bin/env bash
# deploy/verify_hermes_training.sh — run ON THE VM (cd /opt/meridian) to confirm the deployed Hermes
# agent is (a) running the SKILL-AWARE ("trained") code, (b) wired to the same state/ the dashboard
# reads, and (c) safe (paper, autonomy 0, single Hermes). Read-only: it changes nothing.
set -uo pipefail
cd "$(dirname "$0")/.." 2>/dev/null || cd /opt/meridian
PY="./.venv/bin/python"; [ -x "$PY" ] || PY="python3"
pass=0; fail=0
ok(){   printf '  \033[32m✓\033[0m %s\n' "$1"; pass=$((pass+1)); }
no(){   printf '  \033[31m✗\033[0m %s\n' "$1"; fail=$((fail+1)); }
info(){ printf '    %s\n' "$1"; }

echo "── 1. TRAINING: is the skill-aware code deployed? ─────────────────"
LIB=$("$PY" -c "from meridian import hermes; import json; print(len(json.loads(hermes.build_context()).get('skill_library',[])))" 2>/dev/null || echo 0)
if [ "${LIB:-0}" -ge 30 ]; then ok "Hermes context carries the skill library ($LIB skills)"
else no "skill_library missing/empty ($LIB) — VM code is OLD; sync the current repo (see below)"; fi
"$PY" -c "from meridian import hermes; import sys; sys.exit(0 if 'Axis-2' in hermes.SYSTEM and 'skill_recommendation' in hermes.HYP_SCHEMA['properties'] else 1)" 2>/dev/null \
  && ok "two-axis briefing + Axis-2 schema present" || no "Axis-2 self-improvement code missing (old code)"
SK=$(find skills -name SKILL.md 2>/dev/null | wc -l | tr -d ' ')
[ "${SK:-0}" -ge 30 ] && ok "skills/ folder present ($SK SKILL.md files — catalog reads these)" \
  || no "skills/ folder missing/incomplete ($SK) — catalog descriptions will be empty"

echo "── 2. BRAIN: Claude vs deterministic ─────────────────────────────"
BRAIN=$("$PY" -c "from meridian import secrets; print('claude' if (secrets.get('HERMES_API_KEY') or secrets.get('ANTHROPIC_API_KEY')) else 'deterministic')" 2>/dev/null)
if [ "$BRAIN" = "claude" ]; then ok "HERMES/ANTHROPIC key resolves → full skill reasoning (Claude)"
else no "no Claude key → free deterministic proposer only (attribution-based Axis-2)."; info "push it: PROJECT_ID=<p> deploy/push_secret.sh HERMES_API_KEY  +  export MERIDIAN_GCP_PROJECT=<p>"; fi
"$PY" -c "from meridian import secrets; import sys; sys.exit(0 if secrets.present('FMP_API_KEY') else 1)" 2>/dev/null \
  && ok "FMP_API_KEY resolves (screeners enabled)" || info "· FMP_API_KEY not set (data skills stay off — optional)"

echo "── 3. WIRING: dashboard and Hermes share ONE state/ ──────────────"
"$PY" - <<'PYEOF' 2>/dev/null && ok "state/ is writable and shared" || no "state/ problem — dashboard & Hermes may be on different dirs"
from meridian import config
p = config.STATE; assert p.exists(), p
import os; assert os.access(p, os.W_OK)
PYEOF
info "state dir: $("$PY" -c 'from meridian import config; print(config.STATE)' 2>/dev/null)"
HB=$("$PY" -c "from meridian import store; print(store.read_json('heartbeat.json',{}).get('ts','—'))" 2>/dev/null)
info "last heartbeat (worker alive?): $HB"
TR=$("$PY" -c "from meridian import store; print(len(store.read_jsonl('trades.jsonl')))" 2>/dev/null)
info "closed trades Hermes can reflect on: $TR"

echo "── 4. PROCESSES: exactly ONE Hermes, dashboard up ────────────────"
NH=$(pgrep -fc "meridian.hermes --loop" 2>/dev/null || echo 0)
if [ "${NH:-0}" = "1" ]; then ok "one standalone Hermes loop running (tmux)"
elif [ "${NH:-0}" = "0" ]; then no "no Hermes loop running — start: bash deploy/install_hermes.sh"
else no "MULTIPLE Hermes loops ($NH) — kill extras (double-reflect risk)"; fi

# ---- ÇİFT-HERMES MUHAFIZI: ARTIK SUNUCUYU ÖLÇÜYOR (K1, 2026-07-30) -------------------------
# ESKİ HÂL ÜÇ KAT KÖRDÜ ve HER KOŞULDA "autostart off" diyordu:
#   1) `TH=$(pgrep -fc "MERIDIAN_AUTOSTART_HERMES=1")` — değişken atanıyor, HİÇ OKUNMUYORDU.
#   2) `pgrep -f` argv'ye bakar; ORTAM DEĞİŞKENLERİ argv'de görünmez → desen asla eşleşemez.
#   3) `os.environ` kontrolü DOĞRULAYICININ kendi kabuğunu ölçüyordu. Sunucuda bayrak systemd
#      biriminde set (deploy/oracle-a1/meridian.service: Environment=MERIDIAN_AUTOSTART_HERMES=1),
#      yani muhafız "çift Hermes yok" derken risk tam da orada duruyordu.
# YENİ HÂL: ölçülen şey SUNUCU SÜRECİNİN KENDİ ortamı. `api.py` bu gerçeği `/api/hermes`
# `autostart` alanında da beyan ediyor; token varsa ORASI sorulur (sunucunun kendi beyanı),
# yoksa sürecin ortamı okunur. Hiçbiri olmazsa cevap "ÖLÇÜLEMEDİ" — sahte bir "off" DEĞİL.
DPID=$(pgrep -f "uvicorn meridian.api" 2>/dev/null | head -1 || true)
AUTO="unknown"
if [ -n "${MERIDIAN_DASH_TOKEN:-}" ]; then
  # Sunucunun KENDİ beyanı (süreç-içi env) — en doğrudan kanıt.
  AJ=$(curl -s -H "x-meridian-token: ${MERIDIAN_DASH_TOKEN}" \
        http://127.0.0.1:8080/api/hermes 2>/dev/null || true)
  case "$AJ" in
    *'"autostart":true'*)  AUTO="on";;
    *'"autostart":false'*) AUTO="off";;
  esac
fi
if [ "$AUTO" = "unknown" ] && [ -n "$DPID" ]; then
  # `ps eww` süreç ORTAMINI basar (macOS ve Linux'ta mevcut) — argv'nin göremediği yer.
  if ENVDUMP=$(ps eww "$DPID" 2>/dev/null); then
    case "$ENVDUMP" in
      *MERIDIAN_AUTOSTART_HERMES=1*) AUTO="on";;
      *) AUTO="off";;
    esac
  fi
fi
# ÇİFT-HERMES = İKİ KOŞULUN BİRLİKTE OLMASI. `autostart=on` TEK BAŞINA arıza DEĞİLDİR — pano
# Hermes'i kendi içinde koşturuyorsa bu DESTEKLENEN yapılandırmadır (yerel kurulum tam böyle:
# pid 8442 autostart=1 ve standalone loop yok). Risk yalnız İKİSİ birden varken doğar. Tek
# başına "on"u kırmızı yakmak, gerçek alarmları ucuzlatan bir yanlış pozitif olurdu.
case "$AUTO" in
  on)  if [ "${NH:-0}" -ge 1 ]; then
         no "ÇİFT HERMES: dashboard autostart ON (pid ${DPID:-?}) VE $NH standalone loop → double-reflect. Unset MERIDIAN_AUTOSTART_HERMES on the VM."
       else
         ok "autostart ON, standalone loop yok → tek Hermes (pano içinde) — measured on the SERVER process"
       fi;;
  off) if [ "${NH:-0}" -ge 1 ]; then
         ok "autostart off, $NH standalone loop → tek Hermes — measured on the SERVER process"
       else
         no "HİÇ Hermes yok: autostart off VE standalone loop yok — yansıma hiç koşmuyor"
       fi;;
  *)   no "double-Hermes guard could NOT measure the server (dashboard pid not found and no MERIDIAN_DASH_TOKEN) — unverified, not 'safe'";;
esac
code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/healthz 2>/dev/null || echo 000)
[ "$code" = "200" ] && ok "dashboard /healthz → 200" || no "dashboard not answering on :8080 (code $code)"

echo "── 5. SAFETY: paper only, autonomy 0 ─────────────────────────────"
"$PY" -c "from meridian import config; import sys; sys.exit(0 if config.MODE=='paper' and not config.live_enabled() and config.limits()['autonomy_level']==0 else 1)" 2>/dev/null \
  && ok "MODE=paper · live disabled · autonomy_level 0 (L0)" || no "SAFETY: live/autonomy flag set — revert to paper/L0 immediately"

echo "──────────────────────────────────────────────────────────────────"
printf "  RESULT: \033[32m%d passed\033[0m / \033[31m%d failed\033[0m\n" "$pass" "$fail"
[ "$fail" -eq 0 ] && echo "  ✓ Trained Hermes is live, wired, and safe." \
  || echo "  ✗ Fix the ✗ items above. Old code → resync repo to /opt/meridian and restart Hermes."
exit 0

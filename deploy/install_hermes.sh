#!/usr/bin/env bash
# deploy/install_hermes.sh — run LAST, on the VM (Hard Rule 2). Installs the Hermes brain deps,
# launches `python -m meridian.hermes --loop` in a detached tmux session, and loads the briefing
# into the session buffer so the operator never copy-pastes a wall of text (§7).
# Refreshes PATH in place — never asks for a terminal restart (Hard Rule 1).
set -euo pipefail
cd /opt/meridian

echo "→ installing Hermes brain deps (anthropic SDK + secret manager) — LAST, per Hard Rule 2"
# inside the container image these are already present; on a bare VM venv:
if command -v uv >/dev/null 2>&1; then uv pip install --system anthropic google-cloud-secret-manager;
else python3 -m pip install --user anthropic google-cloud-secret-manager; fi
export PATH="$HOME/.local/bin:$PATH"   # refresh in place

echo "→ launching Hermes in a detached tmux session named 'hermes'"
tmux kill-session -t hermes 2>/dev/null || true
tmux new-session -d -s hermes -c /opt/meridian \
  "MERIDIAN_MODE=paper python -m meridian.hermes --loop 2>&1 | tee -a state/hermes.log"

echo "→ loading the briefing into the tmux buffer (no operator copy-paste)"
tmux load-buffer -b hermes-brief /opt/meridian/deploy/hermes_briefing.md
# show the operator the briefing + Hermes' standby acknowledgement
sleep 2
echo "=== tmux sessions ==="; tmux ls
echo "=== Hermes standby output (first lines) ==="
tail -n 20 state/hermes.log 2>/dev/null || echo "(warming up — 'tmux attach -t hermes' to watch)"
echo
echo "✓ Hermes is up. Attach with:  tmux attach -t hermes   (detach: Ctrl-b d)"

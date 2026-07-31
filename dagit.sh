#!/usr/bin/env bash
# dagit.sh — Meridian GENEL dağıtım betiği (WP-H/H2 kapılı). Tek-seferlik gece betiklerinin
# (dagitim_gece*.sh) yerine standart yol: her dağıtım BU sırayla geçer.
#   [0] uv audit (tedarik-zinciri kapısı — kırmızıysa DAĞITIM YOK)
#   [1] rsync DRY-RUN (ne değişecek göster; yarım-iş/mtime tuzağına karşı GÖZLE onay)
#   [2] rsync (state/backups/.venv/.git HARİÇ)
#   [3] uv sync --frozen
#   [4] bakım penceresi: durdur → (varsa migrasyon argümanı) → başlat
#   [5] doğrulama: servisler active + healthz 200 + son olay yaşı
# Kullanım: ./dagit.sh            → dry-run'a kadar gider, ONAY İSTER
#           ./dagit.sh --uygula   → tam dağıtım
set -euo pipefail
KEY="$HOME/.ssh/oci-a1.key"; IP="130.61.126.87"; REPO="$HOME/AI-Trading"
SSH=(ssh -i "$KEY" -o ConnectTimeout=15 ubuntu@"$IP")
RSYNC_EXC=(--exclude '.venv' --exclude '.git' --exclude 'state' --exclude 'backups' --exclude 'scratchpad' --exclude '__pycache__')

echo "=== [0a/5] git temiz-ağaç kapısı ==="
cd "$REPO"
if [[ -n "$(git status --porcelain)" ]]; then
  if [[ "${2:-}" == "--kirli-gec" || "${1:-}" == "--kirli-gec" ]]; then
    echo "  ⚠ KİRLİ AĞAÇLA dağıtım (bilinçli --kirli-gec)"; git status --short | head -10
  else
    echo "!! Çalışma ağacı KİRLİ — önce commit'le (yarım-iş canlıya gitmesin)."
    echo "   Bilinçli istisna için: ./dagit.sh --uygula --kirli-gec"; git status --short | head -15; exit 1
  fi
fi
echo "  ✓ dağıtılacak commit: $(git rev-parse --short HEAD) — $(git log -1 --format=%s | head -c 60)"

echo "=== [0b/5] uv audit (tedarik-zinciri kapısı) ==="
uv audit --preview-features audit-command || { echo "!! AUDIT KIRMIZI — dağıtım İPTAL"; exit 1; }

echo "=== [1/5] rsync DRY-RUN ==="
rsync -azin --delete "${RSYNC_EXC[@]}" -e "ssh -i $KEY" "$REPO"/ ubuntu@"$IP":/opt/meridian/ | head -40
echo "--- (yukarısı ilk 40 satır; boşsa fark yok) ---"

if [[ "${1:-}" != "--uygula" ]]; then
  echo ">> KURU KOŞUM BİTTİ. Tam dağıtım için: ./dagit.sh --uygula"; exit 0
fi

echo "=== [2/5] rsync ==="
rsync -az --delete "${RSYNC_EXC[@]}" -e "ssh -i $KEY" "$REPO"/ ubuntu@"$IP":/opt/meridian/
echo "  ✓"

echo "=== [3/5] uv sync --frozen ==="
"${SSH[@]}" 'export PATH="$HOME/.local/bin:$PATH"; cd /opt/meridian && uv sync --frozen --extra dev -q && echo "  ✓"'

echo "=== [4/5] bakım penceresi ==="
"${SSH[@]}" 'sudo systemctl stop meridian meridian-barsarchive && echo "  ✓ durdu"'
"${SSH[@]}" 'sudo systemctl daemon-reload && sudo systemctl start meridian meridian-barsarchive && sleep 8 && systemctl is-active meridian meridian-barsarchive | tr "\n" " "; echo'

echo "=== [5/5] doğrulama ==="
"${SSH[@]}" 'curl -s -o /dev/null -w "healthz: %{http_code}\n" http://127.0.0.1:8000/healthz;
  tail -1 /opt/meridian/state/events.jsonl | head -c 200; echo'
echo "=== DAĞITIM TAMAM ==="

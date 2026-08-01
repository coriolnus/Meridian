#!/usr/bin/env bash
# dagit.sh — Meridian GENEL dağıtım betiği (WP-H/H2 kapılı). Tek-seferlik gece betiklerinin
# (dagitim_gece*.sh) yerine standart yol: her dağıtım BU sırayla geçer.
#   [0] uv audit (tedarik-zinciri kapısı — kırmızıysa DAĞITIM YOK)
#   [0c] lint-imports (mimari sözleşmeler — WP-H/H4; kırmızıysa DAĞITIM YOK)
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
RSYNC_EXC=(--exclude '.venv' --exclude '.git' --exclude 'state' --exclude 'backups' --exclude 'scratchpad' --exclude '__pycache__' --exclude '.claude' --exclude '.hypothesis' --exclude 'mutants' --exclude '.pytest_cache')

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

# [0c] MİMARİ SÖZLEŞMELER (WP-H/H4, 2026-07-31). Neden DAĞITIM kapısı: bu sözleşmelerin ihlali
# derleme hatası vermez, test kırmazsa görünmez ve canlıya SESSİZCE gider. En pahalı hâli döngüsel
# import'tur — süreç AÇILIRKEN patlar, yani arıza dağıtımdan dakikalar sonra, bakım penceresi
# kapandıktan sonra ortaya çıkar. 2 saniyelik bir kapı, o gecenin tamamını kurtarır.
# `uv run` KULLANILIR (çıplak `lint-imports` değil): dev bağımlılığı yalnız proje ortamındadır ve
# çıplak çağrı, aracın kurulu OLMADIĞI bir kabukta "command not found" ile — yani kapı hiç
# koşmadan — geçilmiş sayılırdı.
echo "=== [0c/5] lint-imports (mimari sözleşme kapısı) ==="
uv run lint-imports || {
  echo "!! MİMARİ SÖZLEŞME KIRILDI — dağıtım İPTAL."
  echo "   Sözleşmeler: pyproject.toml [tool.importlinter]. İstisna eklemek bir borç kaydıdır."
  exit 1
}

echo "=== [1/5] rsync DRY-RUN ==="
rsync -azin --delete "${RSYNC_EXC[@]}" -e "ssh -i $KEY" "$REPO"/ ubuntu@"$IP":/opt/meridian/ | head -40
echo "--- (yukarısı ilk 40 satır; boşsa fark yok) ---"

if [[ "${1:-}" != "--uygula" ]]; then
  echo ">> KURU KOŞUM BİTTİ. Tam dağıtım için: ./dagit.sh --uygula"; exit 0
fi

echo "=== [2/5] rsync ==="
rsync -az --delete "${RSYNC_EXC[@]}" -e "ssh -i $KEY" "$REPO"/ ubuntu@"$IP":/opt/meridian/
echo "  ✓"

# [3] OPERATÖR KARARI BEKLİYOR (WP-H/H5 yan etkisi, ÖLÇÜLDÜ 2026-07-31 — sessizce yapılmadı):
# H1/H4/H5 araçları `[dependency-groups] dev`e eklendi ve bu grup `uv sync`in VARSAYILAN grubudur.
# Ölçüm: `uv export --frozen --extra dev` çıktısında hypothesis + import-linter + mutmut + grimp +
# libcst + textual + setproctitle GÖRÜNÜYOR — yani aşağıdaki komut bu 7 paketi A1'e de kuruyor.
# Kurulum RİSKSİZ (hepsinin linux_aarch64 tekerleği lock'ta hazır, derleme yok) ama BEDELSİZ değil:
#   * üçü de YALNIZ yerel ölçüm ritüelinde koşar (ops/kapilar.sh, ops/haftalik_mutasyon.sh, [0c]) —
#     A1'de hiçbir yol onları import etmez;
#   * [0b] audit kapısı bu paketleri de tarar, yani `textual`daki bir CVE canlı bir dağıtımı
#     alakasız bir gerekçeyle BLOKLAYABİLİR.
# Daraltma kolu hazır ve tek kelime: komuta `--no-default-groups` eklemek A1'i bugünkü paket
# kümesine geri döndürür (pytest `--extra dev`den gelmeye devam eder). KARAR ROL-1'İN — dağıtım
# semantiğini ölçüm turu tek başına değiştirmez.
echo "=== [3/5] uv sync --frozen ==="
"${SSH[@]}" 'export PATH="$HOME/.local/bin:$PATH"; cd /opt/meridian && uv sync --frozen --no-dev -q && echo "  ✓"'

echo "=== [4/5] bakım penceresi ==="
"${SSH[@]}" 'sudo systemctl stop meridian meridian-barsarchive && echo "  ✓ durdu"'
"${SSH[@]}" 'sudo systemctl daemon-reload && sudo systemctl start meridian meridian-barsarchive && sleep 8 && systemctl is-active meridian meridian-barsarchive | tr "\n" " "; echo'

echo "=== [5/5] doğrulama ==="
"${SSH[@]}" 'curl -s -o /dev/null -w "healthz: %{http_code}\n" http://127.0.0.1:8000/healthz;
  tail -1 /opt/meridian/state/events.jsonl | head -c 200; echo'
echo "=== DAĞITIM TAMAM ==="

#!/usr/bin/env bash
# stop-worker.sh — Meridian worker'ını (uvicorn + arkasındaki probe havuzu) SÜREÇ GRUBU bazlı durdurur.
# Kullanım:  ./ops/stop-worker.sh           (elle durdurma)
#            source ops/stop-worker.sh      (serve.sh ve ops/supervise.sh böyle kullanır)
#
# NEDEN grup-kill (2026-07-26 yetim sızıntısı vakası):
# serve.sh uvicorn'u start_new_session=True ile açıyor → uvicorn kendi oturumunun ve süreç grubunun
# LİDERİ oluyor, yani PGID == uvicorn PID. MERIDIAN_PARALLEL_PROBES=1 ile kurulan multiprocessing
# havuzu (resource_tracker + 4 spawn işçisi) uvicorn'un çocuğu olarak AYNI gruba doğuyor.
# Eskiden durdurma `pkill -f "uvicorn meridian.api"` idi: bu yalnız desene uyan lideri öldürüyor,
# havuz üyeleri PPID 1'e düşüp günlerce yaşamaya devam ediyordu. 2026-07-26'da bu sızıntıdan
# ~75 yetim süreç ve 7.6 GB swap dolgusu birikti ve Redis'i boğdu. Doğru çözüm sinyali tek sürece
# değil GRUBA göndermek: kill -- -PGID.
# (Python tarafındaki atexit / ProcessPoolExecutor.shutdown savunması AYRI bir konu — burada kapsam dışı.)
stop_worker() {
  local pid pgid pgids=""
  for pid in $(pgrep -f "uvicorn meridian.api" 2>/dev/null || true); do
    pgid="$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' ')"
    if [ -n "$pgid" ] && [ "$pgid" = "$pid" ]; then
      # grup lideri → bizim detached worker'ımız; havuzuyla birlikte tüm grubu indir
      pgids="$pgids $pgid"
      kill -TERM -- "-$pgid" 2>/dev/null || true
    else
      # grup lideri DEĞİL (ör. bir kabuğun grubunda elden koşan uvicorn) — o grubu topluca
      # öldürmek çağıran terminali de vururdu; yalnız sürecin kendisini hedefle.
      kill -TERM "$pid" 2>/dev/null || true
    fi
  done
  # TERM'e düzgün kapanma şansı ver, sonra sağ kalan grup üyelerini sert indir
  for _ in 1 2 3 4 5; do
    pgrep -f "uvicorn meridian.api" >/dev/null 2>&1 || break
    sleep 1
  done
  for pgid in $pgids; do
    if pgrep -g "$pgid" >/dev/null 2>&1; then kill -KILL -- "-$pgid" 2>/dev/null || true; fi
  done
  sleep 1
  # Geçmiş sızıntı kalıntısı: uvicorn artık yok ama PPID 1'e düşmüş multiprocessing yetimleri
  # varsa (eski pkill'lerden kalanlar) onları da süpür. Ebeveyni ölmüş bir multiprocessing işçisi
  # tanım gereği yetimdir; komut satırından sahibi ayırt edilemediği için kapsam aynı kullanıcının
  # süreçleriyle sınırlı tutuluyor.
  if ! pgrep -f "uvicorn meridian.api" >/dev/null 2>&1; then
    local orphans
    orphans="$(ps -u "$(id -u)" -o pid=,ppid=,command= | awk '$2==1 && /from multiprocessing/ {print $1}')"
    if [ -n "$orphans" ]; then
      echo "→ geçmiş sızıntıdan kalan $(printf '%s\n' "$orphans" | wc -l | tr -d ' ') yetim süreç temizleniyor…"
      kill -TERM $orphans 2>/dev/null || true
      sleep 2
      kill -KILL $orphans 2>/dev/null || true
    fi
  fi
}

# doğrudan çalıştırıldıysa (source edilmediyse) hemen durdur
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  set -u
  cd "$(dirname "$0")/.."
  stop_worker
  echo "✓ worker durduruldu (süreç grubu temizlendi)"
fi

#!/usr/bin/env bash
# pull-a1-backups.sh — A1'deki state yedeklerini BU MAC'E çeker (VM-DIŞI kopya).
#
# NEDEN VAR. `deploy/oracle-a1/meridian-backup.timer` her gün `/home/ubuntu/backups/state-*.tar.gz`
# üretiyor — ama o dosyalar YEDEKLENEN MAKİNENİN KENDİSİNDE duruyor. Instance silinir/bozulur/
# Oracle kotası kapanırsa yedek de gider. "Yedeğimiz var" cümlesi, yedek yalnız kaynakla aynı
# kaderi paylaşan bir diskte duruyorken YANLIŞTIR. Bu betik o cümleyi doğru yapar: ikinci bir
# fiziksel kopya, başka bir makinede, günde bir.
#
# KURULUM (LaunchAgent, günde 1 kez — eşlik eden plist bu dizinde):
#   cp ops/com.meridian.backup-pull.plist ~/Library/LaunchAgents/
#   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.meridian.backup-pull.plist
#   launchctl enable gui/$(id -u)/com.meridian.backup-pull
#   launchctl kickstart -p gui/$(id -u)/com.meridian.backup-pull      # elle bir kez dene
# KALDIRMA:
#   launchctl bootout gui/$(id -u)/com.meridian.backup-pull
# DURUM / LOG:
#   launchctl print gui/$(id -u)/com.meridian.backup-pull | head -30
#   tail -f ~/AI-Trading/backups/a1/pull.log
#
# ELLE KOŞU:  bash ops/pull-a1-backups.sh          (ağ ister; ajan koşumlarında ÇALIŞTIRILMAZ)
#
# AĞ DIŞI HİÇBİR ŞEYE DOKUNMAZ: yalnız okur (rsync pull) ve YEREL hedef dizine yazar. A1'de hiçbir
# dosya değişmez, hiçbir servis durdurulmaz/başlatılmaz.
set -euo pipefail

A1_USER="${MERIDIAN_A1_USER:-ubuntu}"
A1_IP="${MERIDIAN_A1_IP:-130.61.126.87}"
A1_KEY="${MERIDIAN_A1_KEY:-$HOME/Documents/OCI/ssh-key-2026-07-21.key}"
A1_DIR="${MERIDIAN_A1_BACKUP_DIR:-/home/ubuntu/backups}"
DEST="${MERIDIAN_BACKUP_DEST:-$HOME/AI-Trading/backups/a1}"
RETAIN_DAYS="${MERIDIAN_BACKUP_RETAIN_DAYS:-30}"
LOG="$DEST/pull.log"

mkdir -p "$DEST"
say() { printf '%s  %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$*" | tee -a "$LOG"; }

if [ ! -r "$A1_KEY" ]; then
  # SESSİZ DEĞİL: anahtar yoksa çekim yapılamaz ve "yedek çekiliyor" sanılan bir kurulum aylarca
  # boş dönebilir. Çıkış kodu 0 DEĞİL — launchd raporunda görünür olmalı.
  say "HATA: SSH anahtarı okunamıyor: $A1_KEY (MERIDIAN_A1_KEY ile değiştirilebilir)"
  exit 2
fi

say "çekim başlıyor · $A1_USER@$A1_IP:$A1_DIR → $DEST"
# --ignore-existing: YALNIZ EKSİKLERİ çeker. Yedek arşivleri değişmez (tarih damgalı, yeniden
# yazılmaz), o yüzden var olanı tekrar indirmek boşa bant genişliğidir. Silme YOK (--delete asla):
# A1'de budanan eski bir yedek, buradaki kopyayı SİLMEMELİ — VM-dışı kopyanın var olma sebebi budur.
set +e
rsync -az --ignore-existing --partial --timeout=120 \
      -e "ssh -i '$A1_KEY' -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20" \
      "$A1_USER@$A1_IP:$A1_DIR/state-*.tar.gz" "$DEST/" >>"$LOG" 2>&1
rc=$?
set -e
if [ "$rc" -ne 0 ]; then
  # rsync 23/24 = "bazı dosyalar aktarılamadı" (ör. hiç eşleşen dosya yok). Ayırt et, ama YUTMA.
  say "UYARI: rsync çıkış kodu $rc — ayrıntı yukarıdaki log satırlarında"
fi

n=$(find "$DEST" -maxdepth 1 -name 'state-*.tar.gz' | wc -l | tr -d ' ')
son=$(find "$DEST" -maxdepth 1 -name 'state-*.tar.gz' -print0 2>/dev/null \
      | xargs -0 ls -t 2>/dev/null | head -1 || true)
say "yerel kopya: $n arşiv · en yeni: ${son:-YOK}"

# YEREL BUDAMA: 30 günden eski kopyalar silinir (A1'deki budama ayrıdır ve buraya karışmaz).
# Sürüm zinciri değil FELAKET KURTARMA kopyası tutuyoruz; sonsuz birikim diski doldurur.
eski=$(find "$DEST" -maxdepth 1 -name 'state-*.tar.gz' -mtime "+$RETAIN_DAYS" | wc -l | tr -d ' ')
if [ "$eski" -gt 0 ]; then
  find "$DEST" -maxdepth 1 -name 'state-*.tar.gz' -mtime "+$RETAIN_DAYS" -delete
  say "budama: $eski arşiv silindi (> $RETAIN_DAYS gün)"
fi

# LOG BUDAMA: son 2000 satır (dosya sonsuza kadar büyümesin; tek yazar bu betiktir)
if [ -f "$LOG" ] && [ "$(wc -l <"$LOG")" -gt 2000 ]; then
  tail -n 2000 "$LOG" >"$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi
exit "$rc"

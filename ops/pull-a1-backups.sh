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
# --- LITESTREAM REPLICA BACAĞI (WP-H/H10 aşama-1, 2026-08-02) --------------------------------------
# A1'deki dosya-replica'sı da AYNI DİSKTEdir; VM-dışı tek kopyası burasıdır.
A1_REPLICA_DIR="${MERIDIAN_A1_REPLICA_DIR:-/home/ubuntu/replica}"
REPLICA_DEST="${MERIDIAN_REPLICA_DEST:-$HOME/AI-Trading/backups/a1-replica}"
PULL_REPLICA="${MERIDIAN_PULL_REPLICA:-1}"

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

# ==================================================================================================
# İKİNCİ BACAK — LITESTREAM DOSYA-REPLICA'SI (H10 aşama-1)
# ==================================================================================================
# NEDEN AYRI BİR BACAK. Yukarıdaki tar bacağı GÜNLÜK bir fotoğraftır; A1'deki litestream replica'sı
# ise SÜREKLİ tazedir (sync-interval 10sn). Ama o replica çoğaltılan defterle AYNI blok cihazdadır
# (A1'de ikinci disk YOK — lsblk ölçümü 2026-08-02) ve VM kaybında tar'la birlikte gider.
# Bu bacak, replica'nın VM-DIŞI tek kopyasını üretir.
# DÜRÜST SINIR: bu bacağın tazeliği ÇEKİM KADANSI kadardır (LaunchAgent günde 1). Yani "RPO 10
# saniye" cümlesi YALNIZ A1 ÜZERİNDE geçerlidir; Mac kopyası için RPO ~çekim aralığıdır. Gerçek
# off-box dakika-RPO'su aşama-2'nin (OCI bucket) işidir, bu bacağın DEĞİL.
rc_rep=0
if [ "$PULL_REPLICA" != "1" ]; then
  say "replica bacağı: MERIDIAN_PULL_REPLICA=$PULL_REPLICA → BEYANLI ATLAMA (operatör kapattı)"
else
  # UZAK DİZİN VAR MI — "henüz kurulmadı" ile "kırık" AYRI ŞEYLERDİR (YASA 4: sessiz yutma yok).
  # rsync'in 23/24 kodları ikisini de aynı torbaya atardı; sonda ÖNCE sorulur.
  if ssh -i "$A1_KEY" -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20 \
         "$A1_USER@$A1_IP" "test -d '$A1_REPLICA_DIR'" 2>>"$LOG"; then
    mkdir -p "$REPLICA_DEST"
    say "replica çekimi · $A1_USER@$A1_IP:$A1_REPLICA_DIR/ → $REPLICA_DEST"
    # SİLME YOK (--delete asla) — tar bacağıyla AYNI YASA: A1'de saklama penceresi dolduğu için
    # budanan bir LTX/snapshot dosyası, buradaki kopyadan SİLİNMEMELİ. SONUÇ BEYANLI: yerel kopya
    # A1'in ÜST KÜMESİDİR; `litestream restore` geri yükleme noktasını TXID/zaman damgasına göre
    # seçer, fazlalık eski snapshot yalnız DAHA ESKİYE sarma imkânıdır. Bedeli disk büyümesidir ve
    # bu bacakta OTOMATİK BUDAMA YOKTUR — bilinçli operatör kalemi (tar bacağının 30 günlük budaması
    # buraya UYGULANMADI: orada dosya adı tarih taşır, burada taşımaz; ada bakan bir budama sessizce
    # yanlış dosyayı silerdi).
    set +e
    rsync -az --partial --timeout=120 \
          -e "ssh -i '$A1_KEY' -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20" \
          "$A1_USER@$A1_IP:$A1_REPLICA_DIR/" "$REPLICA_DEST/" >>"$LOG" 2>&1
    rc_rep=$?
    set -e
    if [ "$rc_rep" -ne 0 ]; then
      say "UYARI: replica rsync çıkış kodu $rc_rep — ayrıntı yukarıdaki log satırlarında"
    fi
    nrep=$(find "$REPLICA_DEST" -type f 2>/dev/null | wc -l | tr -d ' ')
    sonrep=$(find "$REPLICA_DEST" -type f -print0 2>/dev/null | xargs -0 ls -t 2>/dev/null | head -1 || true)
    say "yerel replica: $nrep dosya · en yeni: ${sonrep:-YOK}"
  else
    # Kurulum öncesi NORMAL durum. Sessiz geçmiyoruz ama başarısızlık da SAYMIYORUZ: H10 aşama-1
    # canlıya inmeden bu dizin yoktur ve o bir arıza değildir.
    say "replica bacağı: uzak dizin YOK ($A1_REPLICA_DIR) — litestream henüz kurulmamış (BEYANLI no-op)"
  fi
fi

# LOG BUDAMA: son 2000 satır (dosya sonsuza kadar büyümesin; tek yazar bu betiktir)
if [ -f "$LOG" ] && [ "$(wc -l <"$LOG")" -gt 2000 ]; then
  tail -n 2000 "$LOG" >"$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi
# İKİ BACAK, TEK ÇIKIŞ KODU: hangisi düşerse düşsün launchd raporunda GÖRÜNÜR. tar bacağı önceliklidir
# (o, felaket-kurtarmanın taban halkasıdır); replica bacağının hatası onu maskelemez, sıfırsa öne geçer.
if [ "$rc" -ne 0 ]; then exit "$rc"; fi
exit "$rc_rep"

#!/usr/bin/env bash
# cutover.sh — YEREL (Mac) tarafta koşar. Meridian'ı Mac'ten Oracle A1'e TEK KOMUTLA taşır.
#
#   bash deploy/oracle-a1/cutover.sh [-i <ssh-anahtarı>] <A1-IP>
#   örnek: bash deploy/oracle-a1/cutover.sh 130.61.126.87
#
# SIRA KRİTİK ve bilinçlidir:
#   1) ön kontrol (IP + ssh erişimi + uzak rsync/curl)
#   2) YEREL süreçleri DURDUR (worker + arşivci + keepalive)      ← rsync'ten ÖNCE
#   3) rsync (repo, sonra state/)                                  ← durmuş süreçten TUTARLI görüntü
#   4) uzakta deploy.sh
#   5) pano token'ı (openssl rand)
#   6) doğrulama tablosu
# 2. adım 3.'den ÖNCE olmalı: koşan bir worker state/'e yazarken alınan kopya, yarım yazılmış bir
# defterle A1'e gider (jsonl'ların ortasında kesik satır, portfolio.json ile trades.jsonl uyumsuz).
#
# BU BETİK KESME KARARINI VERMEZ, UYGULAR. Koştuğu an yerel sistem DURUR.
set -euo pipefail
cd "$(dirname "$0")/../.."   # repo kökü
REPO="$(pwd)"

# Anahtar: operatörün OCI anahtarı (2026-07-21 üretildi, 0600). -i ile başka anahtar verilebilir.
KEY="${MERIDIAN_A1_KEY:-$HOME/Documents/OCI/ssh-key-2026-07-21.key}"
while getopts ":i:" opt; do
  case "$opt" in
    i) KEY="$OPTARG" ;;
    \?) echo "bilinmeyen seçenek: -$OPTARG" >&2; exit 64 ;;
    :)  echo "-$OPTARG bir değer ister" >&2; exit 64 ;;
  esac
done
shift $((OPTIND - 1))
IP="${1:-}"

adim() { echo ""; echo "=== [$1] $2"; }
oldu()  { echo "  ✓ $1"; }
patla() { echo ""; echo "!! BAŞARISIZ — kalınan adım: $1"; echo "   $2"; exit 1; }

# --- 1) ön kontrol -------------------------------------------------------------------------------
adim 1/6 "ön kontrol"
[ -n "$IP" ] || { echo "kullanım: bash deploy/oracle-a1/cutover.sh [-i <anahtar>] <A1-IP>"; exit 64; }
[ -f "$KEY" ] || patla "1/6 ön kontrol" "ssh anahtarı yok: $KEY  (-i ile doğru yolu ver)"
SSH=(ssh -i "$KEY" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15)
echo "  hedef: ubuntu@$IP   anahtar: $KEY"
"${SSH[@]}" "ubuntu@$IP" true \
  || patla "1/6 ön kontrol" "ssh ubuntu@$IP çalışmıyor. Anahtarı/IP'yi ve Oracle güvenlik listesini (22) kontrol et."
oldu "ssh erişimi var"
# Minimal imaj pürüzü: rsync/curl önyüklü GELMEYEBİLİR. 130.61.126.87'de 2026-07-30'da ikisi de
# KURULU bulundu; kontrol yine de duruyor — yeniden kurulan bir instance'ta gerekir.
if "${SSH[@]}" "ubuntu@$IP" 'command -v rsync >/dev/null && command -v curl >/dev/null'; then
  oldu "uzakta rsync + curl var"
else
  echo "  → uzakta rsync/curl eksik, tek seferlik kuruluyor…"
  "${SSH[@]}" "ubuntu@$IP" 'sudo apt-get update -qq && sudo apt-get install -y -qq rsync curl' \
    || patla "1/6 ön kontrol" "uzakta rsync/curl kurulamadı (ağ? apt kilidi?)"
  oldu "rsync + curl kuruldu"
fi
"${SSH[@]}" "ubuntu@$IP" 'sudo mkdir -p /opt/meridian && sudo chown ubuntu:ubuntu /opt/meridian' \
  || patla "1/6 ön kontrol" "/opt/meridian oluşturulamadı (sudo yetkisi?)"
oldu "/opt/meridian hazır"

# --- 2) YEREL süreçleri durdur -------------------------------------------------------------------
adim 2/6 "YEREL süreçleri durdurma (rsync'ten ÖNCE — tutarlı state görüntüsü için)"
# worker: süreç GRUBU bazlı (uvicorn + probe havuzu). Gerekçe ops/stop-worker.sh başında.
# shellcheck source=ops/stop-worker.sh
source ops/stop-worker.sh
stop_worker
oldu "worker durduruldu (süreç grubu)"
./ops/barsarchive-run.sh stop
oldu "barsarchive durduruldu"
# keepalive: ops/keepalive.sh state/keepalive.pid'i ATOMİK sahipleniyor ve her turda kirayı
# denetliyor. Pidfile'ı silmek yeter ama örnek 60 sn'ye kadar yaşar (uyku turu) — o süre içinde
# worker'ı DİRİLTİR. O yüzden önce PID'i öldür, sonra pidfile'ı sil. PID canlılığı KOMUT KİMLİĞİYLE
# doğrulanır (bayat pidfile başka bir sürece denk gelebilir — keepalive.sh:26'daki dersin aynısı).
KAPID="$(cat state/keepalive.pid 2>/dev/null || true)"
if [ -n "$KAPID" ] && ps -o command= -p "$KAPID" 2>/dev/null | grep -q 'keepalive\.sh'; then
  kill "$KAPID" 2>/dev/null || true   # yarışta kendi kendine çıkmış olabilir; aşağıdaki doğrulama gerçeği söyler
  sleep 1
  oldu "keepalive öldürüldü (pid $KAPID)"
else
  oldu "keepalive koşmuyordu"
fi
rm -f state/keepalive.pid
# caffeinate'e DOKUNULMUYOR — o operatörün uyku-engelleyicisi, Meridian'ın parçası değil.
# Doğrula: gerçekten durdular mı? Duran sanılan bir worker rsync sırasında state'e yazardı.
sleep 2
KALAN=""
pgrep -f "uvicorn meridian.api"   >/dev/null 2>&1 && KALAN="$KALAN uvicorn"
pgrep -f "meridian\.barsarchive"  >/dev/null 2>&1 && KALAN="$KALAN barsarchive"
pgrep -f "keepalive\.sh"          >/dev/null 2>&1 && KALAN="$KALAN keepalive"
[ -z "$KALAN" ] || patla "2/6 yerel durdurma" "hâlâ koşan süreç var:$KALAN — elle indir, sonra tekrar koş."
oldu "yerelde Meridian süreci kalmadı"

# --- 3) rsync ------------------------------------------------------------------------------------
adim 3/6 "rsync → $IP"
# repo: .venv A1'de yeniden kurulur (aarch64 wheel), .git gereksiz, state AYRI geçer (aşağıda).
# --delete VAR (silinen kaynak dosyası uzakta kalmasın), --delete-excluded YOK ve olmayacak:
# o bayrak --exclude'ların KORUMASINI kaldırır, yani uzaktaki state/ ve .venv'i SİLERDİ. Sade
# --delete ile hariç tutulanlar silinmeye karşı korunur (rsync varsayılanı) — istediğimiz tam bu.
rsync -az --delete \
  --exclude '.venv' --exclude '.git' --exclude 'state' \
  -e "ssh -i $KEY -o StrictHostKeyChecking=accept-new" \
  "$REPO"/ "ubuntu@$IP:/opt/meridian/" \
  || patla "3/6 rsync repo" "repo kopyalanamadı"
oldu "repo kopyalandı (.venv/.git/state hariç)"
# state ayrı ve --delete'SİZ: A1'de bu turda üretilmiş bir dosya varsa silmeyelim; -a izinleri taşır
# (secrets/auth 0600 kalır) ama garanti aşağıda uzakta chmod ile de veriliyor.
echo "  → state/ ($(du -sh state | cut -f1)) kopyalanıyor, sürebilir…"
rsync -az \
  -e "ssh -i $KEY -o StrictHostKeyChecking=accept-new" \
  "$REPO"/state/ "ubuntu@$IP:/opt/meridian/state/" \
  || patla "3/6 rsync state" "state kopyalanamadı"
"${SSH[@]}" "ubuntu@$IP" 'chmod 700 /opt/meridian/state; for f in /opt/meridian/state/secrets.json /opt/meridian/state/auth.json; do [ -f "$f" ] && chmod 600 "$f"; done; true'
oldu "state kopyalandı, sırlar 0600"

# --- 4) uzakta kurulum ---------------------------------------------------------------------------
adim 4/6 "uzakta deploy.sh (uv sync + redis + systemd birimleri + tohum kapısı)"
"${SSH[@]}" "ubuntu@$IP" 'cd /opt/meridian && bash deploy/oracle-a1/deploy.sh' \
  || patla "4/6 uzak kurulum" "deploy.sh düştü. Uzakta koş ve çıktıyı oku: ssh -i $KEY ubuntu@$IP 'cd /opt/meridian && bash deploy/oracle-a1/deploy.sh'"
oldu "deploy.sh tamamlandı"

# --- 5) pano token'ı -----------------------------------------------------------------------------
adim 5/6 "MERIDIAN_DASH_TOKEN üretimi"
# DİKKAT (eski runbook hatası): B.3'teki sed deseni 'DEĞİŞTİR-uzun-rastgele-token' idi, oysa
# meridian.service'teki placeholder 'CHANGEME-long-random-ascii-token'. sed eşleşmeyince SESSİZCE
# 0 döner → servis bilinen bir placeholder token'la canlıya çıkardı. Desen artık dosyadan doğrulandı
# ve değişimin GERÇEKTEN olduğu aşağıda kontrol ediliyor.
"${SSH[@]}" "ubuntu@$IP" '
  set -e
  if grep -q "CHANGEME-long-random-ascii-token" /etc/systemd/system/meridian.service; then
    sudo sed -i "s/CHANGEME-long-random-ascii-token/$(openssl rand -hex 24)/" /etc/systemd/system/meridian.service
    grep -q "CHANGEME-long-random-ascii-token" /etc/systemd/system/meridian.service \
      && { echo "TOKEN DEĞİŞTİRİLEMEDİ"; exit 1; }
    echo "  token üretildi (openssl rand -hex 24)"
  else
    echo "  token zaten ayarlı (placeholder yok) — dokunulmadı"
  fi
  sudo systemctl daemon-reload
  sudo systemctl restart meridian
' || patla "5/6 token" "token ayarlanamadı — /etc/systemd/system/meridian.service'i elle kontrol et"
oldu "token ayarlandı, meridian yeniden başlatıldı"
sleep 8

# --- 6) doğrulama --------------------------------------------------------------------------------
adim 6/6 "doğrulama"
"${SSH[@]}" "ubuntu@$IP" '
  printf "%-24s %s\n" "BİRİM/UÇ" "DURUM"
  printf "%-24s %s\n" "------------------------" "----------------"
  for u in redis-server meridian meridian-barsarchive; do
    printf "%-24s %s\n" "$u" "$(systemctl is-active $u 2>&1 || true)"
  done
  printf "%-24s %s\n" "meridian-backup.timer" "$(systemctl is-active meridian-backup.timer 2>&1 || true)"
  printf "%-24s %s\n" "redis-cli ping" "$(redis-cli ping 2>&1 | head -1)"
  printf "%-24s %s\n" "GET /healthz" "$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/healthz || echo BAĞLANAMADI)"
  printf "%-24s %s\n" "GET /api/today" "$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/api/today || echo BAĞLANAMADI)"
  echo ""
  echo "(healthz 200=taze · 503=BAYAT ama süreç canlı: çöküş sonrası taze-veri çekimi ~10dk sürebilir, normal)"
' || patla "6/6 doğrulama" "doğrulama komutları koşturulamadı (ssh koptu?)"

cat <<UYARI

################################################################################
#  ⚠  YEREL WORKER DURDURULDU VE DURMALI                                       #
#                                                                              #
#  Meridian artık A1'de ($IP) koşuyor. İki kopya AYNI ANDA koşarsa AYNI Alpaca #
#  hesabına ÇİFT EMİR gider — pozisyon boyutu ikiye katlanır, iç defter ile     #
#  broker mutabakatı bozulur (MIRROR_DRIFT).                                   #
#                                                                              #
#  Yerelde ./serve.sh'ı ANCAK A1'i durdurduktan sonra çalıştır:                #
#      ssh -i $KEY ubuntu@$IP 'sudo systemctl stop meridian meridian-barsarchive'
#                                                                              #
#  PANO (port'u internete açmadan):                                            #
#      ssh -i $KEY -L 8080:127.0.0.1:8080 ubuntu@$IP                           #
#      → tarayıcı: http://localhost:8080                                       #
#                                                                              #
#  LOGLAR:                                                                     #
#      ssh -i $KEY ubuntu@$IP 'journalctl -u meridian -f'                      #
################################################################################
UYARI

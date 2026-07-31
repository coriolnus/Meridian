#!/usr/bin/env bash
# Meridian keepalive — kullanıcı-oturumu süpervizörü (launchd, ~/Documents'a TCC engeli yüzünden
# kullanılamadı; bkz. ops/com.meridian.agent.plist denemesi). serve.sh bunu otomatik başlatır.
# 60 sn'de bir healthz yoklar; üst üste 2 kez ölü bulursa serve.sh ile diriltir + obs'a yazar.
# Tekil örnek: pidfile + süreç kimliği doğrulaması. Eski muhafız salt `kill -0` idi: pidfile
# reboot'u aşıyor ve keepalive düşük PID aldığı için bayat PID reboot sonrası BAŞKA bir sürece
# denk gelebiliyordu (~%13, 2026-07-26 ölçümü) — muhafız sessizce çıkıyor, süpervizör alarmsız
# yok oluyordu. Reboot'ta otomatik başlatma yine yok — operatör ./serve.sh çalıştırır (bilinen
# sınır) — ama bayat pidfile artık o başlatmayı engellemez.
# Elle durdurmak için pidfile'ı silmek yeter: sahiplik her turda denetlenir, örnek kendini kapatır.
set -u
cd "$(dirname "$0")/.."
PIDFILE=state/keepalive.pid

# Pidfile'ı atomik sahiplen: ln(2) hedef varken başarısız olur (O_EXCL eşdeğeri; flock macOS'ta
# yok). check-then-write TOCTOU'su böylece kapanır — eşzamanlı iki serve.sh'den yalnız biri kazanır.
sahiplen() {
  local tmp; tmp=$(mktemp "$PIDFILE.XXXXXX") || return 1
  echo $$ > "$tmp"
  if ln "$tmp" "$PIDFILE" 2>/dev/null; then rm -f "$tmp"; return 0; fi
  rm -f "$tmp"; return 1
}
if ! sahiplen; then
  PID="$(cat "$PIDFILE" 2>/dev/null || true)"
  # PID canlı VE komutu gerçekten keepalive.sh ise koşan bir örnek var — çekil.
  if [ -n "$PID" ] && ps -o command= -p "$PID" 2>/dev/null | grep -q 'keepalive\.sh'; then exit 0; fi
  rm -f "$PIDFILE"     # bayat pidfile: reboot artığı ya da PID çarpışması
  sahiplen || exit 0   # yeniden dene; yarışı kaybettiysek pidfile'ı kapan örnek devam eder
fi
# Çıkışta yalnız KENDİ pidfile'ımızı sil — kaybeden bir yarışçı kazananınkini süpürmesin.
temizlik() { [ "$(cat "$PIDFILE" 2>/dev/null)" = "$$" ] && rm -f "$PIDFILE"; return 0; }
trap temizlik EXIT
trap 'exit 0' INT TERM   # sinyalde de EXIT trap'i (temizlik) koşsun
MISS=0
while true; do
  sleep 60 & wait $!   # çıplak `sleep` sinyal işlemeyi komut bitene dek geciktirir; `wait` anında keser
  # Kira denetimi: pidfile artık bizi göstermiyorsa (operatör silmiş ya da bayat-silme yarışında el
  # değiştirmiş) sessizce çekil — olası bir çift örnek böylece 60 sn içinde teke iner.
  [ "$(cat "$PIDFILE" 2>/dev/null)" = "$$" ] || exit 0
  CODE=$(curl -s -o /dev/null -w '%{http_code}' -m 5 http://127.0.0.1:8080/healthz 2>/dev/null || echo 000)
  if [ "$CODE" = "200" ] || [ "$CODE" = "503" ]; then MISS=0; continue; fi   # 503=stale ama süreç canlı
  MISS=$((MISS+1))
  if [ "$MISS" -ge 2 ]; then
    MISS=0
    ./serve.sh >/dev/null 2>&1 || true
    PYTHONPATH=. .venv/bin/python -c "from meridian import obs; obs.alarm('MECHANISM_STALE', 'sunucu ölü bulundu — keepalive yeniden başlattı', mechanism='server_process')" 2>/dev/null || true
  fi
done

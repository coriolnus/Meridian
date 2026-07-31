#!/usr/bin/env bash
# ops/barsarchive-run.sh — mrd:bars:* → state/bars_intraday/ dayanıklı arşivcisinin OPS GİRİŞİ.
#
# NEDEN BU DOSYA VAR (kopukluk avı, 2026-07-30): `meridian.barsarchive` yazılıp test edilmişti ama
# hiçbir ops katmanından ÇAĞRILMIYORDU — yani Faz 5'in kanıt birikimi (dakikalık barların TTL'den
# önce diske alınması) pratikte OPERATÖRÜN elle bir terminal açmasına bağlıydı. Redis ring'i ~2 seans
# tutar: koşmayan bir arşivci "sonra toplarız" demez, o barlar TEMELLİ yoktur.
#
# NEDEN serve.sh'ye EKLENMEDİ: arşivci panonun/worker'ın ömrüne bağlı DEĞİLDİR ve bağlı olmamalıdır.
# serve.sh her çağrışında `stop_worker` ile süreç GRUBUNU indiriyor; arşivciyi oraya asmak, panoyu
# her yeniden başlatışta bar akışını da kesmek olurdu. Ayrıca serve.sh'ye dokunmak bu turun sözüne
# aykırıydı. launchd de YOK: ~/Documents TCC engeli (bkz. ops/com.meridian.agent.plist denemesi)
# yüzünden bu depoda launchd zaten çalışmıyor — keepalive.sh'nin öğrettiği desen kullanıcı-oturumu
# içinde nohup + pidfile'dır.
#
# KULLANIM:  ./ops/barsarchive-run.sh start | stop | status | once
#   start  : arşivciyi ayrı bir süreçte başlatır (nohup, kabuk kapansa da yaşar)
#   stop   : pidfile sahibini durdurur (SIGTERM → barsarchive KeyboardInterrupt yolunda temiz kapanır)
#   status : koşuyor mu + arşiv özeti (YASA 6 tüketicisi: `--ozet`)
#   once   : tek tur koş ve çık (duman testi / cron); Redis yoksa çıkış kodu 2
set -u
cd "$(dirname "$0")/.."
PIDFILE=state/barsarchive.pid
LOGFILE=state/barsarchive.log
PY=.venv/bin/python

[ -x "$PY" ] || { echo "$PY yok — önce: uv sync --extra dev"; exit 1; }

# Pidfile'ı ATOMİK sahiplen (keepalive.sh'nin dersi): ln(2) hedef varken başarısız olur (O_EXCL
# eşdeğeri; flock macOS'ta yok) → check-then-write TOCTOU'su kapanır. Bayat pidfile reboot'u aşar ve
# düşük PID başka bir sürece denk gelebilir, o yüzden PID canlılığı KOMUT KİMLİĞİYLE doğrulanır.
kosuyor() {
  local pid; pid="$(cat "$PIDFILE" 2>/dev/null || true)"
  [ -n "$pid" ] || return 1
  ps -o command= -p "$pid" 2>/dev/null | grep -q 'meridian\.barsarchive' || return 1
  echo "$pid"; return 0
}

case "${1:-status}" in
  start)
    if PID="$(kosuyor)"; then echo "zaten koşuyor (pid $PID)"; exit 0; fi
    rm -f "$PIDFILE"                     # bayat pidfile: reboot artığı ya da PID çarpışması
    [ -f .env ] && set -a && . ./.env && set +a
    # PYTHONPATH=. → modül depo kökünden çözülür (serve.sh ile aynı sözleşme).
    PYTHONPATH=. nohup "$PY" -m meridian.barsarchive >>"$LOGFILE" 2>&1 &
    echo $! > "$PIDFILE"
    sleep 1
    if PID="$(kosuyor)"; then
      echo "barsarchive başladı (pid $PID) — günlük: $LOGFILE"
    else
      # DÜRÜST BAŞARISIZLIK: süreç 1 sn içinde ölmüşse "başladı" demek yanlış olurdu.
      rm -f "$PIDFILE"; echo "BAŞLATILAMADI — son satırlar:"; tail -5 "$LOGFILE" 2>/dev/null; exit 1
    fi
    ;;
  stop)
    if PID="$(kosuyor)"; then
      kill "$PID" 2>/dev/null || true    # SIGTERM; run() döngüsü kapanır, açık gün dosyaları close()'lanır
      sleep 1
      kosuyor >/dev/null && { sleep 2; kosuyor >/dev/null && kill -9 "$PID" 2>/dev/null || true; }
      rm -f "$PIDFILE"; echo "durduruldu (pid $PID)"
    else
      rm -f "$PIDFILE"; echo "koşmuyor"
    fi
    ;;
  once)
    [ -f .env ] && set -a && . ./.env && set +a
    PYTHONPATH=. "$PY" -m meridian.barsarchive --once; exit $?
    ;;
  status)
    if PID="$(kosuyor)"; then echo "KOŞUYOR (pid $PID)"; else echo "KOŞMUYOR"; fi
    PYTHONPATH=. "$PY" -m meridian.barsarchive --ozet --gun 5
    ;;
  *)
    echo "kullanım: $0 start|stop|status|once"; exit 64 ;;
esac

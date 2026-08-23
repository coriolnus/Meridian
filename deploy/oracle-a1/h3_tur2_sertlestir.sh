#!/usr/bin/env bash
# =================================================================================================
# h3_tur2_sertlestir.sh — H3 tur-2 uygulama adımları (bakım penceresi): tick-watchdog + fail-notify
# sertleştirme drop-in'lerinin FAZLI kurulumu / doğrulaması / geri alınması
# =================================================================================================
# SUNUCUDA (A1) KOŞAR — deploy.sh / dash_token_credential.sh ile aynı sözleşme. Otomatik ÇAĞRILMAZ:
# bakım penceresinde, operatör eliyle. dagit.sh bu dosyaları NE TAŞIR NE KURAR ([1c]/[F9] kapıları
# yalnız repo↔canlı farkını raporlar).
#
# KAPSAM — filoda sertleştirmesiz kalan İKİ birim (ölçüm 2026-08-23: altı çekirdek birim kümeyi
# birim dosyasının İÇİNDE taşıyor, bu ikisi taşımıyor):
#   * meridian-tick-watchdog.service — `User=` yok → ROOT koşar; en yetkili, en az kısıtlı birim.
#   * meridian-fail-notify.service   — birim dosyasında "BİLİNÇLİ sertleştirilmedi" bloğu var;
#     drop-in ancak oradaki ön-şart dolunca kurulur ve bu betik ön-şartı journal'dan ÖLÇER
#     ("gonderim sonucu: True" satırı) — sözle geçilmez.
#
# FAZLAR (ROADMAP H3: "NoNewPrivileges/ProtectSystem=strict/PrivateTmp/ProtectHome önce; seccomp
# EN SON ve dikkatli") — kaynak: deploy/oracle-a1/<birim>.service.d/:
#   faz 1 = 10-sertlestirme-faz1.conf (dosya-sistemi/temel küme)
#   faz 2 = 20-sertlestirme-faz2.conf (CapabilityBoundingSet= + SystemCallFilter=@system-service)
#
# H3 tur-2 uygulama adımları (bakım penceresi, birim başına — sıra bozulmaz):
#   1. ./h3_tur2_sertlestir.sh                                 → DURUM (hiçbir şey değiştirmez)
#   2. ./h3_tur2_sertlestir.sh --faz1 meridian-tick-watchdog   → kur + daemon-reload + yönerge teyidi
#   3. sudo systemctl start meridian-tick-watchdog && journalctl -u meridian-tick-watchdog -n 5
#      → "ilerleme var" / YAS / ÖLÇÜLEMEDİ satırlarından biri görünmeli; EROFS/EACCES → --geri-al.
#   4. ./h3_tur2_sertlestir.sh --faz2 meridian-tick-watchdog   → seccomp (faz 1 kuruluyken)
#   5. ./h3_tur2_sertlestir.sh --tetik-testi meridian-tick-watchdog
#      → ZORLAMALI ateşleme: meridian'ı GERÇEKTEN restart eder (yalnız bakım penceresinde).
#        Geçici eşik runtime drop-in'le kurulur/sökülür, kalıcı iz bırakmaz. Journal'da "yeniden
#        başlatılıyor" + meridian'ın yeni ActiveEnterTimestamp'ı görülmeden faz 2 YÜRÜRLÜKTE
#        SAYILMAZ (drop-in'deki dikkat kalemi: polkit UID'ye bakar, yeteneğe değil — beklenti,
#        ölçüm değil; bu adım o beklentiyi ölçüme çevirir).
#   6. fail-notify için aynı sıra (--faz1/--faz2): ön-şart journal'dan ölçülür, her fazdan sonra
#      betik test-ateşlemesini kendisi koşar; bildirimin TELEFONA düştüğünü operatör doğrular.
# GERİ ALMA: ./h3_tur2_sertlestir.sh --geri-al <birim> → iki conf da silinir + daemon-reload
#   (drop-in'in meziyeti budur: geri alma bir dosya silmek kadar ucuz; birim dosyasına dokunulmaz).
set -euo pipefail

KAYNAK="$(cd "$(dirname "$0")" && pwd)"
HEDEF=/etc/systemd/system
BIRIMLER="meridian-tick-watchdog meridian-fail-notify"
FAZ1=10-sertlestirme-faz1.conf
FAZ2=20-sertlestirme-faz2.conf

die() { echo "!! $*" >&2; exit 1; }

birim_dogrula() {
  case " $BIRIMLER " in *" ${1:-} "*) ;; *) die "bilinmeyen birim: '${1:-}' (geçerli: $BIRIMLER)";; esac
}

durum() {
  for b in $BIRIMLER; do
    echo "== $b"
    for f in "$FAZ1" "$FAZ2"; do
      if [ -f "$HEDEF/$b.service.d/$f" ]; then
        # KURULU ≠ GÜNCEL: canlıdaki kopya repodan ayrışmışsa bu da bir sürüklenmedir ([F9] sınıfı).
        if cmp -s "$HEDEF/$b.service.d/$f" "$KAYNAK/$b.service.d/$f"; then
          echo "  ✓ $f KURULU (repo ile birebir)"
        else
          echo "  ⚠ $f KURULU ama repodan AYRIK — diff'e bak, sessiz bırakma"
        fi
      else
        echo "  · $f kurulu değil"
      fi
    done
  done
}

on_sart_fail_notify() {
  # ÖN-ŞART ÖLÇÜLÜR, VARSAYILMAZ (birimdeki "NE ZAMAN SERTLEŞTİRİLİR" bloğu): journal'da en az bir
  # GERÇEK başarılı gönderim olmadan sertleştirme kurulmaz — arızası tanım gereği sessiz bir birimde
  # tek kanıt, sertleştirme ÖNCESİ çalıştığının kaydıdır.
  # `grep -q` DEĞİL (2026-08-23 canlı vakası): -q eşleşince boruyu erken kapatır, journalctl
  # SIGPIPE(141) alır ve `set -o pipefail` zinciri "başarısız" sayar — ön-şart, kanıt journal'da
  # DURURKEN ölçülemedi görünür. grep >/dev/null akışı sonuna dek tüketir; SIGPIPE doğmaz.
  journalctl -u meridian-fail-notify --no-pager 2>/dev/null | grep "gonderim sonucu: True" >/dev/null \
    || die "ÖN-ŞART ÖLÇÜLEMEDİ: journal'da başarılı gönderim yok ('gonderim sonucu: True').
   Önce kanalı kur (operatör kalemi: Telegram/webhook sırları) + elle test-ateşleme:
     sudo systemctl start meridian-fail-notify && journalctl -u meridian-fail-notify -n 8
   Bildirim telefona düştükten SONRA bu betiğe dön (birimdeki 'NE ZAMAN SERTLEŞTİRİLİR' bloğu)."
}

faz_kur() { # $1=birim $2=conf
  birim_dogrula "$1"
  [ -f "$KAYNAK/$1.service.d/$2" ] || die "kaynak yok: $KAYNAK/$1.service.d/$2"
  if [ "$2" = "$FAZ2" ] && [ ! -f "$HEDEF/$1.service.d/$FAZ1" ]; then
    die "faz 1 kurulu değil — sıra bozulmaz (seccomp EN SON): önce --faz1 $1"
  fi
  [ "$1" = meridian-fail-notify ] && on_sart_fail_notify
  sudo install -D -m 0644 "$KAYNAK/$1.service.d/$2" "$HEDEF/$1.service.d/$2"
  sudo systemctl daemon-reload
  # KURULDU ≠ YÜRÜRLÜKTE ([1c] dersi): yönergeler systemd'nin KENDİSİNDEN geri okunur.
  echo "-- systemd'nin gördüğü hâl:"
  systemctl show "$1" -p NoNewPrivileges -p ProtectSystem -p PrivateTmp -p ProtectHome \
    -p CapabilityBoundingSet -p SystemCallFilter | sed 's/^/   /'
  echo "✓ $2 → $HEDEF/$1.service.d/ (oneshot birim SONRAKİ koşumda bu kısıtlarla doğar)"
  if [ "$1" = meridian-fail-notify ]; then
    # TEST-ATEŞLEMESİ HEMEN (aynı pencere): sertleştirilmiş hâl gerçek ExecStart yolundan koşulur.
    echo "-- test-ateşlemesi (sertleştirilmiş hâlde):"
    sudo systemctl start meridian-fail-notify || true
    journalctl -u meridian-fail-notify -n 8 --no-pager | sed 's/^/   /'
    echo ">> Bildirim TELEFONA düştü mü? Düşmediyse: ./h3_tur2_sertlestir.sh --geri-al meridian-fail-notify"
  fi
}

tetik_testi() {
  [ "${1:-}" = meridian-tick-watchdog ] || die "--tetik-testi yalnız meridian-tick-watchdog içindir"
  echo "!! Bu test meridian.service'i GERÇEKTEN restart eder — yalnız bakım penceresinde."
  # Geçici eşik RUNTIME drop-in'le (kalıcı /etc'ye değil /run'a): birimin kendi reçetesi
  # ("systemctl edit ... Environment=MERIDIAN_TICK_BAYAT_S=..."), betikleşmiş ve kendini söken hâli.
  # YAS lütfu da sıfırlanır — bakım penceresinde meridian az önce doğmuştur, lütuf hükmü yutardı.
  R=/run/systemd/system/meridian-tick-watchdog.service.d
  sudo mkdir -p "$R"
  printf '[Service]\nEnvironment=MERIDIAN_TICK_BAYAT_S=1\nEnvironment=MERIDIAN_TICK_YAS_LUTUF_S=0\n' \
    | sudo tee "$R/99-tetik-testi.conf" > /dev/null
  sudo systemctl daemon-reload
  sudo systemctl start meridian-tick-watchdog || true
  # Geçici drop-in HEMEN sökülür — test artığı bir sonraki gerçek koşumu 1 sn eşiğiyle bırakamaz.
  sudo rm -f "$R/99-tetik-testi.conf"; sudo systemctl daemon-reload
  echo "-- journal (beklenen: 'yeniden başlatılıyor'):"
  journalctl -u meridian-tick-watchdog -n 6 --no-pager | sed 's/^/   /'
  echo "-- meridian yeni doğmuş olmalı (ActiveEnterTimestamp şimdiye yakın):"
  systemctl show meridian -p ActiveEnterTimestamp | sed 's/^/   /'
  echo ">> 'yeniden başlatılıyor' YOKSA seccomp/yetenek kümesi restart yolunu kırmış olabilir:"
  echo "   ./h3_tur2_sertlestir.sh --geri-al meridian-tick-watchdog  + gerekçe günlüğe."
}

geri_al() {
  birim_dogrula "$1"
  sudo rm -f "$HEDEF/$1.service.d/$FAZ1" "$HEDEF/$1.service.d/$FAZ2"
  sudo rmdir "$HEDEF/$1.service.d" 2>/dev/null || true   # başka drop-in varsa dizin kalır — doğru
  sudo systemctl daemon-reload
  echo "✓ $1 sertleştirme drop-in'leri kaldırıldı (birim dosyasına hiç dokunulmamıştı)"
  systemctl show "$1" -p NoNewPrivileges -p SystemCallFilter | sed 's/^/   /'
}

case "${1:-}" in
  "")            durum ;;
  --faz1)        faz_kur "${2:-}" "$FAZ1" ;;
  --faz2)        faz_kur "${2:-}" "$FAZ2" ;;
  --tetik-testi) tetik_testi "${2:-}" ;;
  --geri-al)     geri_al "${2:-}" ;;
  *)             die "kullanım: $0 [--faz1|--faz2|--tetik-testi|--geri-al] <birim>  (argümansız: durum)" ;;
esac

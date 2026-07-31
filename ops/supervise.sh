#!/usr/bin/env bash
# Meridian süpervizörü (launchd): çökmede otomatik yeniden başlatma + oturum açılışında başlama.
#   kur:    ./ops/supervise.sh install
#   kaldır: ./ops/supervise.sh uninstall   (sonra elle: ./serve.sh)
#
# ==============================================================================================
# EMEKLİ YOL — VARSAYILAN OLARAK KURULMAZ (K1, 2026-07-30)
# ==============================================================================================
# Bu yol BELGELİ OLARAK ÖLÜ ama kurulabilir durumdaydı ve kurulması AKTİF ZARARLIYDI. Üç sebep:
#
#  1) TCC ENGELİ: ops/keepalive.sh:2-3 kendi ağzıyla yazıyor — "launchd, ~/Documents'a TCC engeli
#     yüzünden kullanılamadı". Yol artık gerçek depoya symlink olsa da engel YOL ÜZERİNDEN aynen
#     geçerlidir. Fiilî süpervizör keepalive'dır (state/keepalive.pid canlı) ve ~/Library/
#     LaunchAgents'ta bu plist YÜKLÜ DEĞİL.
#  2) TOKEN KAYBI: `.env` yalnız MERIDIAN_DASH_TOKEN içeriyor ve onu YALNIZ serve.sh yüklüyor.
#     api.py token'ı yalnız environ'dan okur → launchd altında betik/CLI token yolu SESSİZCE ölür
#     ve her açılışta `dashboard_token_unset` uyarısı düşer. plist bir sır dosyası okuyamaz ve
#     token buraya GÖMÜLMEZ (sır repoya yazılmaz — güvenlik duruşu gevşetilmez).
#  3) KEEPALIVE'I DEVRE DIŞI BIRAKIR: serve.sh, launchd kuruluysa elle başlatmayı kilitler. Yani
#     install çalıştıran bir operatör, ÇALIŞAN süpervizörü çalışmayanla değiştirir.
#
# İki süpervizör katmanı TEKLEŞTİ: kanonik olan keepalive.sh. Bu betik ve plist geri
# alınabilirlik için duruyor (yollar da düzeltildi), ama install açık bir onay ister.
# Bilerek denemek için: MERIDIAN_FORCE_LAUNCHD=1 ./ops/supervise.sh install
# ==============================================================================================
set -euo pipefail
cd "$(dirname "$0")/.."
PLIST=~/Library/LaunchAgents/com.meridian.agent.plist
case "${1:-install}" in
  install)
    if [ "${MERIDIAN_FORCE_LAUNCHD:-0}" != "1" ]; then
      cat >&2 <<'EOF'
REDDEDİLDİ: launchd süpervizörü EMEKLİ bir yoldur (bkz. bu betiğin başındaki üç gerekçe).
Kurmak, ÇALIŞAN keepalive süpervizörünü çalışmayan bir mekanizmayla değiştirir ve panonun
API token'ını düşürür.

Kanonik süpervizör: ops/keepalive.sh — serve.sh onu kendiliğinden başlatır.
Durum kontrolü   : cat state/keepalive.pid && ps -p "$(cat state/keepalive.pid)"

Yine de denemek istiyorsan (TCC engelini ve token kaybını kabul ederek):
  MERIDIAN_FORCE_LAUNCHD=1 ./ops/supervise.sh install
EOF
      exit 2
    fi
    echo "⚠ MERIDIAN_FORCE_LAUNCHD=1 — emekli launchd yolu bilerek kuruluyor."
    echo "⚠ MERIDIAN_DASH_TOKEN launchd ortamına GEÇMEZ: betik/CLI token yolu bu kurulumda ölür."
    # elle koşan worker'ı launchd'ye devretmeden önce indir — süreç GRUBU bazlı, yoksa probe
    # havuzu yetim kalır (2026-07-26'da ~75 yetim + 7.6 GB swap; bkz. ops/stop-worker.sh).
    source ops/stop-worker.sh
    stop_worker
    cp ops/com.meridian.agent.plist "$PLIST"
    launchctl bootout "gui/$(id -u)/com.meridian.agent" 2>/dev/null || true
    launchctl bootstrap "gui/$(id -u)" "$PLIST"
    echo "✓ süpervizör kuruldu — çökmede 30 sn içinde yeniden başlar; elle durdurma: ./ops/supervise.sh uninstall";;
  uninstall)
    launchctl bootout "gui/$(id -u)/com.meridian.agent" 2>/dev/null || true
    rm -f "$PLIST"
    echo "✓ süpervizör kaldırıldı — elle başlatma: ./serve.sh";;
esac

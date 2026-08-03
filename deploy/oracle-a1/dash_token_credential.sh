#!/usr/bin/env bash
# =================================================================================================
# dash_token_credential.sh — pano token'ı: rotasyon + systemd LoadCredential geçişi (WP-H/H3 tur-3)
# =================================================================================================
# SUNUCUDA (A1) KOŞAR — `deploy.sh`/`cutover.sh` ile aynı sözleşme. Otomatik ÇAĞRILMAZ: bakım
# penceresinde, operatör eliyle. Kayıttaki hüküm buydu: "rotasyon + LoadCredential'a taşıma AYNI
# bakım penceresinde" — çünkü ikisini ayırmak, eski token'ın hâlâ geçerliyken yeni kanalın
# doğrulanmasını imkânsız kılar (hangi kanalın çalıştığı ölçülemez, yalnız varsayılır).
#
# NEDEN (kalan yüzey): sır artık 0600'lük `.dash.env`te (tur-1) ve birim dosyasında DEĞİL (tur-2).
# Kalan yüzey SÜREÇ ORTAMIDIR: `serve.sh:51` uvicorn'u `env=os.environ` ile, `hermes_composite.py`
# ajan alt süreçlerini devralınan ortamla doğurur — token her birinin `/proc/<pid>/environ`ında.
# LoadCredential sırrı ortama HİÇ koymaz. Gerekçenin tamamı: meridian.service.d/50-*.conf.
#
# KULLANIM:
#   ./dash_token_credential.sh              → DURUM (hiçbir şey değiştirmez; önce bunu koş)
#   ./dash_token_credential.sh --faz1       → rotasyon + credential kanalı EKLE (ortam kanalı KALIR)
#   ./dash_token_credential.sh --faz2       → ortam kanalını KAPAT (faz-1 + uygulama tarafı şartlı)
#   ./dash_token_credential.sh --geri-al    → her iki drop-in'i kaldır, ortam kanalına dön
set -euo pipefail

BIRIM=/etc/systemd/system/meridian.service.d
KAYNAK_DIR="$(cd "$(dirname "$0")" && pwd)/meridian.service.d"
KRED=/etc/meridian/dash_token
ENVF=/opt/meridian/.dash.env
API=http://127.0.0.1:8080

die() { echo "!! $*" >&2; exit 1; }
oldu() { echo "  ✓ $*"; }

# --- token dosyadan oku (KEY=VALUE ya da çıplak) -------------------------------------------------
_token_oku() {
  sudo sed -n 's/^MERIDIAN_DASH_TOKEN=//p;t;p' "$1" 2>/dev/null | head -1 | tr -d '\r\n'
}

# --- kimlik doğrulaması GERÇEKTEN çalışıyor mu? --------------------------------------------------
# `/healthz` YETMEZ: kimlik doğrulaması İSTEMEYEN bir uçtur, yani token yanlışken de 200 döner ve
# "yeşil" bir doğrulama hiçbir şey kanıtlamazdı. `/api/hermes` `_auth`tan geçer (token yanlışsa
# 401), yani HTTP kodunun kendisi token'ın SUNUCUDA yürürlükte olduğunun kanıtıdır.
_auth_kodu() {
  curl -s -o /dev/null -w "%{http_code}" -H "x-meridian-token: $1" "$API/api/hermes" 2>/dev/null || echo 000
}

_servis_ayakta() {
  systemctl is-active --quiet meridian || return 1
  for _ in $(seq 1 30); do
    [ "$(curl -s -o /dev/null -w '%{http_code}' "$API/healthz" 2>/dev/null || echo 000)" = "200" ] && return 0
    sleep 1
  done
  return 1
}

# =================================================================================================
durum() {
  echo "=== DURUM ==="
  echo "  systemd sürümü: $(systemctl --version | head -1)"
  echo "  credential kaynağı ($KRED): $(sudo test -s "$KRED" && sudo stat -c '%a %U:%G' "$KRED" || echo YOK)"
  echo "  ortam dosyası ($ENVF): $(sudo test -s "$ENVF" && sudo stat -c '%a %U:%G' "$ENVF" || echo YOK)"
  for f in 50-dash-credential.conf 51-dash-env-kaldir.conf; do
    echo "  drop-in $f: $([ -f "$BIRIM/$f" ] && echo KURULU || echo yok)"
  done
  echo "  LoadCredential (yürürlükte): $(systemctl show meridian -p LoadCredential --value || true)"
  echo "  servis: $(systemctl is-active meridian) · healthz: $(curl -s -o /dev/null -w '%{http_code}' "$API/healthz" 2>/dev/null || echo 000)"
}

# =================================================================================================
faz1() {
  echo "=== FAZ 1: rotasyon + LoadCredential kanalı ==="

  # LoadCredential systemd 247'de geldi. ÖLÇÜLÜR, VARSAYILMAZ: eski bir systemd'de drop-in sessizce
  # yok sayılmaz — birim "unknown directive" ile açılmayabilir ve arıza bakım penceresinin ortasında
  # çıkar. Kapı burada, değişiklikten ÖNCE.
  local sv; sv="$(systemctl --version | head -1 | awk '{print $2}')"
  [ "${sv%%.*}" -ge 247 ] 2>/dev/null || die "systemd $sv < 247 — LoadCredential YOK. Geçiş yapılamaz."
  [ -d "$KAYNAK_DIR" ] || die "drop-in kaynağı yok: $KAYNAK_DIR (depo güncel mi?)"

  # ESKİ TOKEN SAKLANIR — geri alma onsuz mümkün değil.
  local eski; eski="$(_token_oku "$ENVF")"
  [ -n "$eski" ] || echo "  · uyarı: mevcut token okunamadı ($ENVF boş/yok) — geri alma sınırlı"

  # YENİ TOKEN ASCII'DİR: `api._auth` ASCII-dışı token'ı DATA_QUALITY alarmıyla işaretler, çünkü
  # HTTP başlığında gönderilemez — "ayarlı ama kullanılamaz" bir token en kötü hâldir.
  local yeni; yeni="$(openssl rand -hex 24)"
  printf '%s' "$yeni" | LC_ALL=C grep -q '^[0-9a-f]\{48\}$' || die "üretilen token beklenen biçimde değil"

  # 1) CREDENTIAL KAYNAĞI — root:root 0400. Servis kullanıcısının okuması GEREKMEZ: dosyayı systemd
  #    PID 1 olarak, sandbox'tan ÖNCE okur. En dar izin, işi gören izindir.
  sudo install -d -m 0755 -o root -g root /etc/meridian
  printf '%s\n' "$yeni" | sudo tee "$KRED" >/dev/null
  sudo chown root:root "$KRED"; sudo chmod 0400 "$KRED"
  oldu "credential kaynağı yazıldı: $KRED (0400 root:root)"

  # 2) ORTAM KANALI DA AYNI TOKEN'A ÇEKİLİR. Faz 1'de iki kanal birden canlıdır; ayrı değerler
  #    taşırlarsa hangisinin yürürlükte olduğu ölçüme değil ŞANSA kalır — ve faz 2'nin farksal
  #    ölçümü (aşağıda) anlamını yitirir. İkisi eşitken geçiş her iki uygulama sürümünde de çalışır.
  sudo cp -p "$ENVF" "$ENVF.bak-$(date -u +%Y%m%d%H%M)" 2>/dev/null || true
  printf 'MERIDIAN_DASH_TOKEN=%s\n' "$yeni" | sudo tee "$ENVF" >/dev/null
  sudo chown ubuntu:ubuntu "$ENVF"; sudo chmod 600 "$ENVF"
  oldu "ortam kanalı aynı token'a çekildi: $ENVF (0600)"

  # 3) DROP-IN + yeniden başlat
  sudo install -d -m 0755 "$BIRIM"
  sudo cp "$KAYNAK_DIR/50-dash-credential.conf" "$BIRIM/50-dash-credential.conf"
  sudo systemctl daemon-reload
  sudo systemctl restart meridian
  if ! _servis_ayakta; then
    echo "!! servis AÇILMADI — GERİ ALINIYOR"; sudo rm -f "$BIRIM/50-dash-credential.conf"
    sudo systemctl daemon-reload; sudo systemctl restart meridian
    die "faz 1 başarısız (drop-in kaldırıldı, eski hâle dönüldü). Günlük: journalctl -u meridian -n 50"
  fi
  local kod; kod="$(_auth_kodu "$yeni")"
  [ "$kod" = "200" ] || die "yeni token ile kimlik doğrulaması BAŞARISIZ (HTTP $kod) — servis ayakta ama token yürürlükte değil"
  oldu "servis ayakta · healthz 200 · yeni token ile /api/hermes 200"
  echo
  echo ">> FAZ 1 TAMAM. YENİ TOKEN (panoya/CLI'ye gerekecek): $yeni"
  echo ">> Faz 2'ye GEÇMEDEN ÖNCE uygulama tarafı credential'ı okuyor olmalı (api.DASH_TOKEN →"
  echo "   CREDENTIALS_DIRECTORY). Hazır olduğunda: ./dash_token_credential.sh --faz2"
}

# =================================================================================================
faz2() {
  echo "=== FAZ 2: ortam kanalını kapat ==="
  [ -f "$BIRIM/50-dash-credential.conf" ] || die "faz 1 kurulu değil — önce --faz1"
  local tok; tok="$(sudo cat "$KRED" | tr -d '\r\n')"
  [ -n "$tok" ] || die "credential kaynağı boş: $KRED"

  # ---- FARKSAL ÖLÇÜM: uygulama token'ı HANGİ kanaldan okuyor? --------------------------------
  # İki kanal aynı değeri taşırken "kimlik doğrulaması çalışıyor" HİÇBİR ŞEY kanıtlamaz — ortam
  # kanalı okunuyor olsa da aynı 200 gelirdi. Tek dürüst ölçüm FARK yaratmaktır: ortam kanalına
  # SAHTE bir değer konur ve GERÇEK (credential) token'la kimlik doğrulaması denenir. 200 gelirse
  # okunan kanal credential'dır; 401 gelirse uygulama hâlâ ortamı okuyordur ve faz 2 ERKENDİR.
  # Ölçüm KENDİ ARDINI TOPLAR: sahte değer her yolda geri alınır (trap).
  echo "  · farksal ölçüm: ortam kanalına sahte değer konuyor (geçici)"
  sudo cp -p "$ENVF" "$ENVF.olcum-yedek"
  # shellcheck disable=SC2064
  trap "sudo mv -f '$ENVF.olcum-yedek' '$ENVF'; sudo systemctl restart meridian >/dev/null 2>&1 || true" EXIT
  printf 'MERIDIAN_DASH_TOKEN=%s\n' "sahte-$(openssl rand -hex 8)" | sudo tee "$ENVF" >/dev/null
  sudo chmod 600 "$ENVF"
  sudo systemctl restart meridian
  _servis_ayakta || die "ölçüm sırasında servis açılmadı"
  local kod; kod="$(_auth_kodu "$tok")"
  sudo mv -f "$ENVF.olcum-yedek" "$ENVF"; trap - EXIT
  sudo systemctl restart meridian; _servis_ayakta || die "ölçüm sonrası servis açılmadı"

  if [ "$kod" != "200" ]; then
    die "UYGULAMA HÂLÂ ORTAM KANALINI OKUYOR (sahte ortam + gerçek credential → HTTP $kod).
     Faz 2 ERKEN: önce api tarafına CREDENTIALS_DIRECTORY okuması girsin. Değişiklik YAPILMADI."
  fi
  oldu "farksal ölçüm: uygulama credential kanalını okuyor (sahte ortamla da 200)"

  sudo cp "$KAYNAK_DIR/51-dash-env-kaldir.conf" "$BIRIM/51-dash-env-kaldir.conf"
  sudo systemctl daemon-reload; sudo systemctl restart meridian
  if ! _servis_ayakta || [ "$(_auth_kodu "$tok")" != "200" ]; then
    echo "!! faz 2 doğrulanamadı — GERİ ALINIYOR"; sudo rm -f "$BIRIM/51-dash-env-kaldir.conf"
    sudo systemctl daemon-reload; sudo systemctl restart meridian
    die "faz 2 başarısız (drop-in kaldırıldı). Günlük: journalctl -u meridian -n 50"
  fi
  oldu "ortam kanalı KAPALI · credential ile 200 · token artık /proc/<pid>/environ'da DEĞİL"
  echo ">> Doğrula: sudo tr '\\0' '\\n' < /proc/\$(pgrep -f 'uvicorn meridian.api' | head -1)/environ | grep -c MERIDIAN_DASH_TOKEN   # 0 beklenir"
}

# =================================================================================================
geri_al() {
  echo "=== GERİ ALMA: ortam kanalına dön ==="
  sudo rm -f "$BIRIM/51-dash-env-kaldir.conf" "$BIRIM/50-dash-credential.conf"
  sudo rmdir "$BIRIM" 2>/dev/null || true
  sudo systemctl daemon-reload; sudo systemctl restart meridian
  _servis_ayakta && oldu "drop-in'ler kaldırıldı, servis ayakta ($ENVF yürürlükte)" \
                 || die "servis açılmadı — journalctl -u meridian -n 50"
  echo "  · $KRED SİLİNMEDİ (bilinçli: geri almanın kendisi geri alınabilir kalsın)."
}

case "${1:-}" in
  --faz1)    faz1 ;;
  --faz2)    faz2 ;;
  --geri-al) geri_al ;;
  "")        durum ;;
  *)         die "bilinmeyen argüman: $1 (--faz1 | --faz2 | --geri-al | boş=durum)" ;;
esac

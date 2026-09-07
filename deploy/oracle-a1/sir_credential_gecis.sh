#!/usr/bin/env bash
# =================================================================================================
# sir_credential_gecis.sh — motor sırlarını systemd LoadCredential kanalına taşır (TSK-064 Faz-1B)
# =================================================================================================
# SUNUCUDA (A1) KOŞAR — `deploy.sh`/`cutover.sh` ile aynı sözleşme. Otomatik ÇAĞRILMAZ: bakım
# penceresinde, operatör eliyle. `dash_token_credential.sh`in (TSK-049, pano token'ı) AD ALAN
# genelleştirilmişidir: orada tek bir sır ve tek amaçlı bir `.env` vardı, burada AYNI dosyada
# yaşayan İKİ sır + yapılandırma satırları var — bu fark faz-2'yi değiştirir (aşağıda).
#
# TANINAN ADLAR: NOUS_API_KEY · KAPI_APIKEY. Üçüncü bir ad bir YAZIM HATASIDIR ve reddedilir:
# sessizce hiçbir şey yapmak en kötü hâl olurdu, çünkü operatör "geçiş yapıldı" sanır.
#
# KULLANIM:
#   ./sir_credential_gecis.sh                    → DURUM (hiçbir şey değiştirmez; önce bunu koş)
#   ./sir_credential_gecis.sh --faz1 <ad>        → credential kanalı EKLE (ortam kanalı KALIR)
#   ./sir_credential_gecis.sh --faz2 <ad>        → farksal ölçüm + ortam satırını KAPAT
#   ./sir_credential_gecis.sh --geri-al <ad>     → ortam satırını geri yaz, drop-in'i kaldır
#   ./sir_credential_gecis.sh --faz1-hafiza      → FAZ-1A: motora TENANT credential'ı (54 drop-in)
#   ./sir_credential_gecis.sh --geri-al-hafiza   → 54 drop-in'i kaldır (vekil dosya yolunu kullanır)
#
# FAZ-1A NİYE BURADA VE NİYE YALNIZ İKİ ALT KOMUT. Hindsight'ın KENDİ geçişi (üç sır →
# `/etc/hindsight/creds/*`, `hindsight-api.service.d/50-creds.conf` + `hindsight-api-baslat.sh`)
# BAŞKA bir birime aittir ve bu betiğin sözleşmesi (`meridian` birimi, `/opt/meridian/.env`,
# `_kanit_nous`) oraya UYMAZ — genelleştirmeye zorlamak iki geçişi birbirinin rehinesi yapardı.
# Buraya YALNIZ motoru DÜŞÜREBİLECEK tek adım girdi: `54-hafiza-credential.conf` motorun birimine
# bir `LoadCredential=` satırı ekler ve kaynak dosya yoksa MOTOR HİÇ AÇILMAZ. O kapı belgeye değil
# koda yazılır (53'te olduğu gibi). Faz-2 (hindsight `.env`inden 3 satırın çıkarılması) hindsight
# tarafının işidir ve BU BETİKTE YOKTUR — burada olmayan şey, burada yapılmayacak şeydir.
#
# SIR DEĞERİ HİÇBİR YOLDA BASILMAZ VE ARGV'YE GİRMEZ. `ps` argv'yi makinedeki HERKESE gösterir;
# 2026-09-02'de bir parola tam olarak bu sınıftan (URL-gömülü, süzgeç kara-listeliydi) terminale
# düştü. Bu betikte değer YALNIZ 0600'lük geçici dosyalar üzerinden akar: `read -s` ile alınır,
# `cat` ile akıtılır; hiçbir `sed`/`awk` değişkenine, hiçbir komut satırına konmaz. Çivi:
# `tests/test_sir_credential_v439.py`.
#
# NEDEN FAZ-2 BURADA "SATIR SİLMEK": pano token'ı tek amaçlı `.dash.env`te yaşıyordu, o yüzden boş
# `EnvironmentFile=` sıfırlaması yetiyordu. `/opt/meridian/.env` ise sır DIŞINDA yapılandırma da
# taşır (NOUS_MODEL, NOUS_ENDPOINT, MERIDIAN_FMP_BASE); dosyanın okunmasını tümden kesmek onları da
# götürürdü. Faz-2 bu yüzden SATIR bazlıdır ve geri alma da satır bazlıdır.
set -euo pipefail

# TEST KANCASI — YALNIZ ÇİVİ İÇİN. Boşken (üretimdeki tek hâl) yollar mutlaktır; v439 çivisi burayı
# tmp'ye çevirip `durum` ve `--geri-al` dallarını GERÇEKTEN koşturur. Ops aracını teslim etmeden
# önce operatörün koşacağı BİÇİMDE bir kez koşmanın yolu budur (18 çivi yeşilken `--uygula`nın
# sessizce yok sayıldığı 2026-08-30 vakasının dersi).
KOK="${SIR_GECIS_KOK:-}"

BIRIM="$KOK/etc/systemd/system/meridian.service.d"
ETC="$KOK/etc/meridian"
ENVF="$KOK/opt/meridian/.env"
DASH_KRED="$KOK/etc/meridian/dash_token"
DROPIN_AD=53-nous-kapi-credential.conf
#: FAZ-1A'nın MOTOR ayağı (spec Bulgu-3): pano vekili Hindsight TENANT anahtarını okur ve o okuma
#: `secrets.credential_oku` üzerinden credential dizinine taşındı (`api._hafiza_anahtari`).
#: KAYNAK, hindsight biriminin okuduğu DOSYANIN TA KENDİSİDİR — iki yol ayrışsaydı operatör aynı
#: sırrı iki kez üretir, ikisi ilk rotasyonda sessizce ayrışırdı. Çivi: v439 I10/I11c.
HAFIZA_DROPIN_AD=54-hafiza-credential.conf
HAFIZA_KRED="$KOK/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY"
KAYNAK_DIR="$(cd "$(dirname "$0")" && pwd)/meridian.service.d"
API="${SIR_GECIS_API:-http://127.0.0.1:8080}"

#: Drop-in'deki `LoadCredential=<ad>:<kaynak>` satırlarıyla BİREBİR aynı olmak ZORUNDA — ayrışırsa
#: betik bir dosyaya yazar, birim başka bir dosyayı arar ve arıza restart anında çıkar. Çivi F2.
ADLAR="NOUS_API_KEY KAPI_APIKEY"

die() { echo "!! $*" >&2; exit 1; }
oldu() { echo "  ✓ $*"; }

_kaynak_yolu() {
  case "$1" in
    NOUS_API_KEY) echo "$KOK/etc/meridian/nous_api_key" ;;
    KAPI_APIKEY)  echo "$KOK/etc/meridian/kapi_apikey" ;;
    *) return 1 ;;
  esac
}

_ad_dogrula() {
  _kaynak_yolu "$1" >/dev/null 2>&1 || die "tanınmayan sır adı: $1 (tanınanlar: $ADLAR)"
}

# LoadCredential systemd 247'de geldi. ÖLÇÜLÜR, VARSAYILMAZ: eski bir systemd'de drop-in sessizce
# yok sayılmaz — birim "unknown directive" ile açılmayabilir ve arıza bakım penceresinin ortasında
# çıkar. Kapı burada, değişiklikten ÖNCE.
_systemd_kapisi() {
  local sv; sv="$(systemctl --version | head -1 | awk '{print $2}')"
  [ "${sv%%.*}" -ge 247 ] 2>/dev/null || die "systemd $sv < 247 — LoadCredential YOK. Geçiş yapılamaz."
}

_servis_ayakta() {
  systemctl is-active --quiet meridian || return 1
  for _ in $(seq 1 30); do
    [ "$(curl -s -o /dev/null -w '%{http_code}' "$API/healthz" 2>/dev/null || echo 000)" = "200" ] && return 0
    sleep 1
  done
  return 1
}

# --- DEĞER TAŞIMA — hepsi dosya üzerinden, hiçbiri argv üzerinden ---------------------------------
# `<kaynak dosya>`nın İLK satırını `<ad>=` önekinden arındırıp `<hedef>`e yazar. Önek toleransı
# `secrets.credential_oku` ile AYNI: operatörün `.env` satırını credential kaynağına kopyalaması
# öngörülebilir bir kazadır ve iki taraf aynı biçimi kabul eder.
_deger_dosyala() {
  local src="$1" ad="$2" hedef="$3"
  sudo sed -n "1{s/^${ad}=//;p;}" "$src" 2>/dev/null | tr -d '\r' > "$hedef"
}

# `.env` içindeki `<ad>=` satırını `<deger dosyası>`nın içeriğiyle DEĞİŞTİRİR (yoksa ekler).
# Komşu satırlara dokunmaz ve satırı ÇOĞALTMAZ: iki `<ad>=` satırı en sinsi hâl olurdu — systemd
# sonuncuyu okur, operatör ilkini düzenler ve iki değer sessizce ayrışır.
_env_satiri_yaz() {
  local ad="$1" src="$2" yeni
  yeni="$(mktemp)"; chmod 600 "$yeni"
  sudo grep -v "^${ad}=" "$ENVF" > "$yeni" 2>/dev/null || true
  printf '%s=' "$ad" >> "$yeni"          # printf KABUK BUILTIN'i — argv'ye giden bir süreç yok
  sudo cat "$src" >> "$yeni"
  sudo install -m 600 "$yeni" "$ENVF"
  sudo chown ubuntu:ubuntu "$ENVF" 2>/dev/null || true
  rm -f "$yeni"
}

_env_satiri_sil() {
  local ad="$1" yeni
  yeni="$(mktemp)"; chmod 600 "$yeni"
  sudo grep -v "^${ad}=" "$ENVF" > "$yeni" 2>/dev/null || true
  sudo install -m 600 "$yeni" "$ENVF"
  sudo chown ubuntu:ubuntu "$ENVF" 2>/dev/null || true
  rm -f "$yeni"
}

# --- KANIT: motor GERÇEKTEN iş yapıyor mu? -------------------------------------------------------
# `/healthz` YETMEZ: kimlik doğrulaması İSTEMEYEN bir uçtur ve sır tamamen yanlışken de 200 döner.
# `/api/secrets/test/nous` panonun içinden `hermes.ping_brain("nous")` çağırır — yani ölçüm
# MOTORUN KENDİ SÜRECİNDE, `_nous_headers`ın kurduğu başlıklarla yapılır. Ayrı bir python koşumu
# bunu ölçemezdi: o süreçte `$CREDENTIALS_DIRECTORY` YOKTUR ve ölçüm sessizce ortam kanalını
# ölçerdi. HTTP kodu da yetmez — uç anahtar yanlışken de 200 döner, hüküm gövdedeki `ok` alanıdır.
# Pano token'ı da argv'ye girmez: curl'e `-K` ile 0600 bir yapılandırma dosyasından verilir.
_kanit_nous() {
  local cfg cvp
  cfg="$(mktemp)"; chmod 600 "$cfg"
  {
    printf 'silent\n'
    printf 'header = "x-meridian-token: '
    sudo sed -n 's/^MERIDIAN_DASH_TOKEN=//p;t;p' "$DASH_KRED" 2>/dev/null | head -1 | tr -d '\r\n'
    printf '"\n'
    printf 'url = "%s/api/secrets/test/nous"\n' "$API"
  } > "$cfg"
  cvp="$(curl -K "$cfg" 2>/dev/null || true)"
  rm -f "$cfg"
  case "$cvp" in
    *'"ok": true'*|*'"ok":true'*) echo OK ;;
    *) echo YOK ;;
  esac
}

# KAPI_APIKEY'in ÖN KAPISI. Kapının key-auth kilidi yürürlükte DEĞİLSE yanlış anahtarla da 200
# gelir; o hâlde "motor iş yapıyor" hangi kanalın okunduğu hakkında HİÇBİR ŞEY söylemez ve farksal
# ölçüm bir tiyatrodur. Ölçülemeyen şeye "geçti" demek uydurmadır (uydurma yasağı) — betik durur.
_kapi_kilidi_olc() {
  local uc kod
  uc="$(sudo sed -n 's/^NOUS_ENDPOINT=//p' "$ENVF" 2>/dev/null | head -1 | tr -d '\r\n')"
  [ -n "$uc" ] || die "NOUS_ENDPOINT okunamadı — kapı ucu bilinmiyor, KAPI_APIKEY ölçümü YAPILAMAZ"
  kod="$(curl -s -o /dev/null -w '%{http_code}' -H 'apikey: bilerek-yanlis-anahtar' \
         "${uc%/}/models" 2>/dev/null || echo 000)"
  case "$kod" in
    401|403) oldu "kapı kilidi yürürlükte (yanlış apikey → HTTP $kod) — farksal ölçüm anlamlı" ;;
    *) die "KAPI_APIKEY ÖLÇÜLEMEZ: yanlış apikey ile HTTP $kod — kapı key-auth kilidi yürürlükte DEĞİL.
     Bu hâlde 'motor çalışıyor' hangi kanalın okunduğunu KANITLAMAZ. Önce kilit açılır
     (ops/apisix_uygula.py), sonra --faz2. Değişiklik YAPILMADI." ;;
  esac
}

# =================================================================================================
durum() {
  local k
  echo "=== DURUM (TSK-064 Faz-1B) ==="
  echo "  systemd sürümü: $(systemctl --version 2>/dev/null | head -1)"
  echo "  drop-in $DROPIN_AD: $([ -f "$BIRIM/$DROPIN_AD" ] && echo KURULU || echo yok)"
  echo "  LoadCredential (yürürlükte): $(systemctl show meridian -p LoadCredential --value 2>/dev/null || true)"
  for ad in $ADLAR; do
    k="$(_kaynak_yolu "$ad")"
    echo "  $ad"
    echo "      credential kaynağı ($k): $(sudo test -s "$k" 2>/dev/null && sudo stat -c '%a %U:%G' "$k" 2>/dev/null || echo YOK)"
    echo "      ortam kanalı ($ENVF): $(sudo grep -qs "^${ad}=" "$ENVF" && echo VAR || echo yok)"
  done
  echo "  --- Faz-1A (pano vekili, Hindsight TENANT anahtarı) ---"
  echo "  drop-in $HAFIZA_DROPIN_AD: $([ -f "$BIRIM/$HAFIZA_DROPIN_AD" ] && echo KURULU || echo yok)"
  echo "      credential kaynağı ($HAFIZA_KRED): $(sudo test -s "$HAFIZA_KRED" 2>/dev/null && sudo stat -c '%a %U:%G' "$HAFIZA_KRED" 2>/dev/null || echo YOK)"
  echo "  servis: $(systemctl is-active meridian 2>/dev/null || true) · healthz: $(curl -s -o /dev/null -w '%{http_code}' "$API/healthz" 2>/dev/null || echo 000)"
  echo "  (değerler BASILMAZ — yalnız izin/varlık.)"
}

# =================================================================================================
faz1() {
  local ad="$1" kred tmp eksik a
  _ad_dogrula "$ad"
  kred="$(_kaynak_yolu "$ad")"
  echo "=== FAZ 1: $ad → LoadCredential kanalı (ortam kanalı KALIR) ==="
  _systemd_kapisi
  [ -d "$KAYNAK_DIR" ] || die "drop-in kaynağı yok: $KAYNAK_DIR (depo güncel mi?)"

  tmp="$(mktemp)"; chmod 600 "$tmp"
  trap 'rm -f "$tmp"' EXIT

  # DEĞER OPERATÖRDEN, EKRANA YANSIMADAN. Boş bırakılırsa `.env`teki mevcut değer TAŞINIR — o hâlde
  # faz-1 tam anlamıyla hareketsizdir. Rotasyon istenirse yeni değer buraya yapıştırılır
  # (TSK-049 hükmü: rotasyon + kanal geçişi aynı pencerede; OpenRouter anahtarları operatörde
  # olduğu için burada ZORLANMAZ, beyanla ertelenebilir).
  printf '  %s için YENİ değer (boş = .env icindeki mevcut degeri tasi): ' "$ad" >&2
  read -s -r _girilen || true
  echo >&2
  if [ -n "${_girilen:-}" ]; then
    printf '%s\n' "$_girilen" > "$tmp"
    unset _girilen
  else
    _deger_dosyala "$ENVF" "$ad" "$tmp"
  fi
  [ -s "$tmp" ] || die "$ad için değer YOK (.env satırı da boş) — geçiş yapılamaz"

  # 1) CREDENTIAL KAYNAĞI — root:root 0400. Servis kullanıcısının okuması GEREKMEZ: dosyayı systemd
  #    PID 1 olarak, sandbox'tan ÖNCE okur. En dar izin, işi gören izindir.
  sudo install -d -m 0755 "$ETC"
  sudo install -m 0400 "$tmp" "$kred"
  sudo chown root:root "$kred" 2>/dev/null || true
  oldu "credential kaynağı yazıldı: $kred (0400 root:root)"

  # 2) ORTAM KANALI DA AYNI DEĞERE ÇEKİLİR. Faz 1'de iki kanal birden canlıdır; ayrı değer
  #    taşırlarsa hangisinin yürürlükte olduğu ölçüme değil ŞANSA kalır — ve faz 2'nin farksal
  #    ölçümü anlamını yitirir. İkisi eşitken geçiş her iki uygulama sürümünde de çalışır.
  sudo cp -p "$ENVF" "$ENVF.bak-$(date -u +%Y%m%d%H%M)" 2>/dev/null || true
  _env_satiri_yaz "$ad" "$tmp"
  oldu "ortam kanalı aynı değere çekildi: $ENVF (0600)"
  rm -f "$tmp"; trap - EXIT

  # 3) DROP-IN — YALNIZ İKİ KAYNAK DA HAZIRKEN. `LoadCredential=` kaynağı yoksa birim HİÇ başlamaz;
  #    tek ad için kurmak, öteki kaynak üretilene kadar motoru açılmaz hâle getirirdi.
  eksik=""
  for a in $ADLAR; do
    sudo test -s "$(_kaynak_yolu "$a")" 2>/dev/null || eksik="$eksik $a"
  done
  if [ -n "$eksik" ]; then
    echo "  · drop-in KURULMADI — kaynak dosyası eksik:$eksik"
    echo "    (LoadCredential kaynağı yoksa birim HİÇ açılmaz. Öteki ad için de --faz1 koş.)"
    return 0
  fi
  sudo install -d -m 0755 "$BIRIM"
  sudo cp "$KAYNAK_DIR/$DROPIN_AD" "$BIRIM/$DROPIN_AD"
  sudo systemctl daemon-reload
  sudo systemctl restart meridian
  if ! _servis_ayakta; then
    echo "!! servis AÇILMADI — GERİ ALINIYOR"
    sudo rm -f "$BIRIM/$DROPIN_AD"
    sudo systemctl daemon-reload; sudo systemctl restart meridian
    die "faz 1 başarısız (drop-in kaldırıldı, eski hâle dönüldü). Günlük: journalctl -u meridian -n 50"
  fi
  oldu "drop-in kuruldu · servis ayakta · iki kanal da canlı (credential ÖNCE okunur)"
  echo ">> Faz 2'ye geçmeden önce: ./sir_credential_gecis.sh --faz2 $ad (farksal ölçüm yapar)"
}

# =================================================================================================
faz2() {
  local ad="$1" kred sahte kanit
  _ad_dogrula "$ad"
  kred="$(_kaynak_yolu "$ad")"
  echo "=== FAZ 2: $ad ortam satırını kapat ==="
  [ -f "$BIRIM/$DROPIN_AD" ] || die "faz 1 kurulu değil — önce --faz1 $ad"
  sudo test -s "$kred" 2>/dev/null || die "credential kaynağı boş/yok: $kred"
  [ "$ad" != "KAPI_APIKEY" ] || _kapi_kilidi_olc

  # ---- FARKSAL ÖLÇÜM: uygulama sırrı HANGİ kanaldan okuyor? --------------------------------------
  # İki kanal aynı değeri taşırken "motor çalışıyor" HİÇBİR ŞEY kanıtlamaz — ortam kanalı okunuyor
  # olsa da aynı sonuç gelirdi. Tek dürüst ölçüm FARK yaratmaktır: ortam satırına SAHTE bir değer
  # konur ve gerçek değer YALNIZ credential'da kalır. Motor hâlâ iş yapıyorsa okunan kanal
  # credential'dır. Ölçüm KENDİ ARDINI TOPLAR: sahte değer her yolda geri alınır (trap).
  echo "  · farksal ölçüm: ortam satırına sahte değer konuyor (geçici)"
  sudo cp -p "$ENVF" "$ENVF.olcum-yedek"
  # shellcheck disable=SC2064
  trap "sudo mv -f '$ENVF.olcum-yedek' '$ENVF'; sudo systemctl restart meridian >/dev/null 2>&1 || true" EXIT
  sahte="$(mktemp)"; chmod 600 "$sahte"
  printf 'sahte-%s\n' "$(openssl rand -hex 8)" > "$sahte"
  _env_satiri_yaz "$ad" "$sahte"
  rm -f "$sahte"
  sudo systemctl restart meridian
  _servis_ayakta || die "ölçüm sırasında servis açılmadı"
  kanit="$(_kanit_nous)"
  sudo mv -f "$ENVF.olcum-yedek" "$ENVF"; trap - EXIT
  sudo systemctl restart meridian; _servis_ayakta || die "ölçüm sonrası servis açılmadı"

  [ "$kanit" = "OK" ] || die "UYGULAMA HÂLÂ ORTAM KANALINI OKUYOR (sahte ortam + gerçek credential → $kanit).
     Faz 2 ERKEN: motorun credential kanalını okuduğu (secrets._fetch sırası) sürümü dağıtılmış
     olmalı. Değişiklik YAPILMADI."
  oldu "farksal ölçüm: motor credential kanalını okuyor (sahte ortam satırıyla da iş yapıyor)"

  sudo cp -p "$ENVF" "$ENVF.bak-faz2-$ad-$(date -u +%Y%m%d%H%M)"
  _env_satiri_sil "$ad"
  sudo systemctl restart meridian
  if ! _servis_ayakta || [ "$(_kanit_nous)" != "OK" ]; then
    echo "!! faz 2 doğrulanamadı — GERİ ALINIYOR"
    geri_al "$ad"
    die "faz 2 başarısız (ortam satırı geri yazıldı). Günlük: journalctl -u meridian -n 50"
  fi
  oldu "$ad ortam kanalından ÇIKTI — artık yalnız credential'dan okunuyor"
  echo ">> Doğrula: sudo tr '\\0' '\\n' < /proc/\$(pgrep -f 'uvicorn meridian.api' | head -1)/environ | grep -c $ad   # 0 beklenir"
}

# =================================================================================================
# FAZ-1A — MOTOR AYAĞI. Yalnız drop-in kurar: kaynak dosyayı (`/etc/hindsight/creds/*`) hindsight
# tarafının geçişi üretir ve bu betik onu ÜRETMEZ — üretseydi aynı sır iki yerden doğar ve hangi
# kopyanın rotate edildiği ŞANSA kalırdı (tek-kaynak yasası).
faz1_hafiza() {
  echo "=== FAZ 1A: pano vekili → $HAFIZA_DROPIN_AD (dosya kanalı KALIR) ==="
  _systemd_kapisi
  [ -d "$KAYNAK_DIR" ] || die "drop-in kaynağı yok: $KAYNAK_DIR (depo güncel mi?)"
  [ -f "$KAYNAK_DIR/$HAFIZA_DROPIN_AD" ] || die "drop-in dosyası yok: $KAYNAK_DIR/$HAFIZA_DROPIN_AD"

  # KAPI, DEĞİŞİKLİKTEN ÖNCE. `LoadCredential=` kaynağı yoksa systemd birimi HİÇ BAŞLATMAZ — yani
  # bu tek satır MOTORU kapatır. Aşağıdaki restart'ın geri alımı var, ama hiç girmemek daha ucuz:
  # hindsight tarafı kurulmadan motora bir hindsight sırrı bağlanmaz.
  sudo test -s "$HAFIZA_KRED" 2>/dev/null || die "credential kaynağı YOK/BOŞ: $HAFIZA_KRED
     Bu satır kurulursa MOTOR HİÇ AÇILMAZ (LoadCredential kaynağı zorunludur). Önce hindsight
     tarafı: /etc/hindsight/creds/* (0400 root) + hindsight-api.service.d/50-creds.conf.
     Değişiklik YAPILMADI."

  sudo install -d -m 0755 "$BIRIM"
  sudo cp "$KAYNAK_DIR/$HAFIZA_DROPIN_AD" "$BIRIM/$HAFIZA_DROPIN_AD"
  sudo systemctl daemon-reload
  sudo systemctl restart meridian
  if ! _servis_ayakta; then
    echo "!! servis AÇILMADI — GERİ ALINIYOR"
    sudo rm -f "$BIRIM/$HAFIZA_DROPIN_AD"
    sudo systemctl daemon-reload; sudo systemctl restart meridian
    die "faz 1A başarısız (drop-in kaldırıldı, eski hâle dönüldü). Günlük: journalctl -u meridian -n 50"
  fi
  oldu "drop-in kuruldu · servis ayakta · vekil TENANT anahtarını credential kanalından okuyor"
  echo ">> Doğrula (pano): /api/hindsight gövdesinde bankalar DOLU, neden BOŞ olmalı."
  echo ">> Farksal ölçüm hindsight tarafındadır: /opt/hindsight/.env satırına SAHTE değer konup"
  echo "   pano hâlâ banka listeliyorsa okunan kanal credential'dır."
}

geri_al_hafiza() {
  echo "=== GERİ ALMA (Faz-1A): $HAFIZA_DROPIN_AD kaldırılıyor ==="
  # 53'e DOKUNULMAZ: iki drop-in ayrı yaşar ve motorun KENDİ sırlarının geçişi bu geri alımdan
  # etkilenmez. Vekil, dosya bacağına (`/opt/hindsight/.env`) düşer — kod iki kanalı da okur.
  sudo rm -f "$BIRIM/$HAFIZA_DROPIN_AD"
  sudo rmdir "$BIRIM" 2>/dev/null || true
  sudo systemctl daemon-reload
  sudo systemctl restart meridian
  _servis_ayakta || die "servis açılmadı — journalctl -u meridian -n 50"
  oldu "drop-in kaldırıldı, servis ayakta (vekil /opt/hindsight/.env bacağını kullanıyor)"
  echo "  · $HAFIZA_KRED SİLİNMEDİ (bilinçli: geri almanın kendisi geri alınabilir kalsın)."
}

# =================================================================================================
geri_al() {
  local ad="$1" kred tmp
  _ad_dogrula "$ad"
  kred="$(_kaynak_yolu "$ad")"
  echo "=== GERİ ALMA: $ad ortam kanalına dön ==="

  # 1) ORTAM SATIRINI GERİ YAZ — değer credential kaynağından okunur ve terminale HİÇ uğramaz.
  #    Faz-2 koşulmamışsa satır zaten duruyordur; `_env_satiri_yaz` onu ÇOĞALTMAZ, değiştirir.
  if sudo test -s "$kred" 2>/dev/null; then
    tmp="$(mktemp)"; chmod 600 "$tmp"
    _deger_dosyala "$kred" "$ad" "$tmp"
    if [ -s "$tmp" ]; then
      _env_satiri_yaz "$ad" "$tmp"
      oldu "$ENVF içine $ad satırı geri yazıldı (değer credential kaynağından; basılmadı)"
    else
      echo "  · uyarı: $kred okunamadı/boş — ortam satırı geri YAZILAMADI"
    fi
    rm -f "$tmp"
  else
    echo "  · uyarı: $kred yok — ortam satırı geri yazılamadı (yedek: $ENVF.bak-*)"
  fi

  # 2) DROP-IN KALDIRILIR. Drop-in İKİ adı birden taşır (tek dosya) — yani bu adım credential
  #    kanalını HER İKİ sır için kapatır. Bilerek: yarım kurulu bir birim (bir kaynağı olan, öteki
  #    olmayan) hiç açılmazdı; geri almanın da bütün olması gerekir.
  sudo rm -f "$BIRIM/$DROPIN_AD"
  sudo rmdir "$BIRIM" 2>/dev/null || true
  sudo systemctl daemon-reload
  sudo systemctl restart meridian
  if _servis_ayakta; then
    oldu "drop-in kaldırıldı, servis ayakta ($ENVF yürürlükte)"
  else
    die "servis açılmadı — journalctl -u meridian -n 50"
  fi
  echo "  · $kred SİLİNMEDİ (bilinçli: geri almanın kendisi geri alınabilir kalsın)."
}

# =================================================================================================
case "${1:-}" in
  --faz1)    [ $# -ge 2 ] || die "kullanım: --faz1 <ad> — tanınanlar: $ADLAR"; faz1 "$2" ;;
  --faz2)    [ $# -ge 2 ] || die "kullanım: --faz2 <ad> — tanınanlar: $ADLAR"; faz2 "$2" ;;
  --geri-al) [ $# -ge 2 ] || die "kullanım: --geri-al <ad> — tanınanlar: $ADLAR"; geri_al "$2" ;;
  --faz1-hafiza)    faz1_hafiza ;;
  --geri-al-hafiza) geri_al_hafiza ;;
  "")        durum ;;
  *)         die "bilinmeyen argüman: $1 (--faz1 <ad> | --faz2 <ad> | --geri-al <ad> | --faz1-hafiza | --geri-al-hafiza | boş=durum)" ;;
esac

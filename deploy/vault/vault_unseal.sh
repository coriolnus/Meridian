#!/usr/bin/env bash
# =================================================================================================
# vault_unseal.sh — Vault mührünü AÇAR (TSK-064 Faz-2). A1'de koşar; DEPODA versiyonlanır.
# =================================================================================================
# HEDEF: /opt/vault/bin/vault_unseal.sh (0750 root:root). İKİ çağıranı vardır ve ikisi de AYNI
# dosyayı koşar (tek kaynak):
#   · vault.service  → ExecStartPost=+…   (her açılışta, crash/reboot dahil)
#   · vault-unseal.service (oneshot)      → elle/tekrar
# ÜÇÜNCÜ çağıran kurulumun kendisidir: `vault_kur.sh` adım 5'te init eder, adım 6'da BU betiği
# çağırır. Üç çağıranın ÜÇÜ de aynı dosyayı koşar; ikinci bir kopya yazılmaz.
#
# SIR DİSİPLİNİ — BU DOSYANIN VAR OLMA SEBEBİ:
#   (1) Anahtar DEĞERİ argv'ye GİRMEZ. `vault operator unseal "$(cat /etc/vault/unseal.key)"`
#       biçimi anahtarı `/proc/<pid>/cmdline`e koyar ve o dosya makinedeki HER kullanıcıya
#       OKUNABİLİRDİR. Doğru biçim STDIN ve dosya yönlendirmesidir: değer çekirdeğin argüman
#       vektörüne hiç uğramaz. HANGİ komutla: `write sys/unseal key=-` — `operator unseal -`
#       DEĞİL; o komut TTY dışında stdin'i REDDEDER (aşağıda "STDIN İŞARETİ" bloğu, ölçüm 2026-09-14).
#   (2) `set -x` YOK. Açık olsaydı her komut (yönlendirme hedefleri dahil) journal'a düşerdi.
#   (3) Hiçbir `echo`/`printf` bir sır değişkeni basmaz — betik zaten hiçbir sırrı DEĞİŞKENE
#       almaz; dosyadan doğrudan stdin'e akar.
#
# BOOTSTRAP SÖZLEŞMESİ — A1 İLK KURULUMUNDA ÖLÇÜLEN ARIZA (2026-09-14 09:0xZ, Rol-1):
#   `vault.service` bu betiği `ExecStartPost=+…` ile çağırır ve ExecStartPost servis AYAĞA
#   KALKAR KALKMAZ koşar — yani `vault_kur.sh` adım 5'teki `operator init`ten ÖNCE. Betik o
#   anda koşulsuz "anahtar dosyası yok/boş → exit 2" diyordu; ExecStartPost'un sıfır olmayan
#   çıkışı BİRİMİ düşürür ve kurulum yeniden-başlama döngüsüne girer (journal:
#   `Control process exited, code=exited, status=2`). Kasa hiç init EDİLEMEZ.
#
#   Kusur çıkış kodunda değil, TEŞHİSTE idi: "anahtar yok" İKİ AYRI OLGUDUR ve tek bir kod
#   ikisini karıştırıyordu —
#     · kasa HENÜZ INIT EDİLMEMİŞ + anahtar yok → BEKLENEN bootstrap hâli. Açılacak bir mühür
#       yoktur; beklenecek bir şey de yoktur. Çıkış 0, ama SESSİZ DEĞİL: olgu adıyla basılır.
#     · kasa INIT EDİLMİŞ + anahtar yok        → GERÇEK arıza (anahtar kayıp). Çıkış 2.
#   Ayrımı yapan tek ölçüm `vault status -format=json` içindeki `initialized` alanıdır. "Anahtar
#   yoksa herhâlde init de yoktur" bir UYDURMA olurdu ve ikinci olguyu sessizce yutardı.
#   Kapı: tests/test_vault_faz2_v485.py §C6-C10 (davranış + iki mutasyon).
#
# BU BİR BEKLEYİCİ DÖNGÜSÜ DEĞİLDİR (CLAUDE.md §7). §7'nin yasakladığı şey, bir işin bitmesini
# yoklayan SÜRESİZ bekleyicidir. Buradaki döngü bir SERVİS AÇILIŞ YOKLAMASIDIR: sınırı sabittir
# (AYAKTA_DENEME), adımı 1 sn'dir ve tavana vurunca BAŞARISIZ döner — yani en kötü hâlde
# birkaç saniyede hüküm verir, sonsuza dek asılmaz. Emsal: dash_token_credential.sh içindeki
# `_servis_ayakta`. Type=notify zaten hazır olmadan buraya gelmez; bu döngü güvenlik ağıdır.
#
# ÇIKIŞ KODLARI (HÜKÜM):
#   0  mühür AÇIK (zaten açıktı ya da bu koşumda açıldı) — YA DA kasa henüz INIT EDİLMEMİŞ
#   1  API ayağa kalkmadı · durum cevabı TANINMADI · unseal başarısız → birim `failed`
#   2  kasa INIT EDİLMİŞ ama anahtar dosyası YOK/BOŞ → anahtar kayıp; ADIYLA söylenir
set -euo pipefail

ANAHTAR_YOLU=${VAULT_UNSEAL_KEY_FILE:-/etc/vault/unseal.key}
VAULT_IKILI=${VAULT_BIN:-/usr/local/bin/vault}
export VAULT_ADDR=${VAULT_ADDR:-http://127.0.0.1:8200}

# API açılış yoklaması: EN ÇOK 60 sn (60 × 1 sn). Değer burada TEK yerde durur ve çivi onu
# ADIYLA okur — kaynağa gömülü bir `60` sınırı okunamaz kılardı.
AYAKTA_DENEME=60

_bas() { echo "[vault-unseal] $*"; }

# --- API cevap veriyor mu? -----------------------------------------------------------------------
# `vault status` çıkış kodu ÜÇ HÂLİ ayırır (belgelenmiş): 0 = açık, 2 = MÜHÜRLÜ, başka = ulaşılamıyor.
# Yani "kasa mühürlü" ile "kasa yok" karışmaz — ve bu ayrım olmadan mühürlü bir kasa "ayakta
# değil" diye raporlanır, arıza yanlış yerde aranırdı. İNİT EDİLMEMİŞ kasa da 2 döner (mühürlü
# sayılır): "cevap veriyor" ile "sır verebiliyor" AYRI sorulardır, ikincisi `initialized`dır.
_durum_kodu() {
  # `|| kod=$?` ZORUNLU: `set -e` altında çıplak bir başarısız komut betiği ÖLDÜRÜR ve mühürlü
  # kasa (kod 2) tam olarak "başarısız komut"tur — yani en sık karşılaşılacak hâl betiği
  # sessizce düşürürdü.
  local kod=0
  "$VAULT_IKILI" status >/dev/null 2>&1 || kod=$?
  echo "$kod"
}

# --- kasa init edilmiş mi? -----------------------------------------------------------------------
# `jq` BİLEREK KULLANILMIYOR: bu betik bootstrap yolunda, paket kurulumundan ÖNCE de koşabilir ve
# eksik bir bağımlılık tam da açılış anında görünmez bir arıza olurdu. Boşluk/satır sonu silinip
# alan ADIYLA aranır. ÜÇÜNCÜ HÂL ("tanınmadı") bilinçlidir: `initialized` okunamazsa HÜKÜM YOKTUR
# ve yokluğu çıkış 0'la örtmek uydurma yasağının ihlali olurdu.
_init_durumu() {
  # `|| true` ZORUNLU ve `pipefail` yüzünden borunun İÇİNDE değil SONUNDA: mühürlü/init-siz kasa
  # 2 döner ve pipefail onu boruya taşır; `set -e` betiği tam da beklenen hâlde öldürürdü.
  local ham
  ham="$("$VAULT_IKILI" status -format=json 2>/dev/null | tr -d ' \n' || true)"
  case "$ham" in
    *'"initialized":true'*)  echo "evet" ;;
    *'"initialized":false'*) echo "hayir" ;;
    *)                       echo "taninmadi" ;;
  esac
}

_api_ayakta() {
  local i kod
  for ((i = 0; i < AYAKTA_DENEME; i++)); do
    kod="$(_durum_kodu)"
    # `A || B && return` YAZILMAZ: `set -e` altında liste tümüyle düştüğünde betik ölür.
    if [ "$kod" = "0" ] || [ "$kod" = "2" ]; then return 0; fi
    sleep 1
  done
  return 1
}

# =================================================================================================
# SIRA ÖNEMLİDİR: önce API, sonra `initialized`, EN SON anahtar dosyası. Ters sıra (eski hâl)
# init'ten önce koşan ExecStartPost'u düşürüyordu — ölçülen arıza, başlıktaki BOOTSTRAP bloğu.
if ! _api_ayakta; then
  _bas "API ${AYAKTA_DENEME} sn içinde cevap vermedi ($VAULT_ADDR)"
  exit 1
fi

INIT_DURUMU="$(_init_durumu)"
case "$INIT_DURUMU" in
  hayir)
    _bas "kasa henüz init edilmedi — unseal beklemiyor (kurulum yarım, exit 0)"
    exit 0   # bootstrap: açılacak mühür YOK; vault_kur.sh adım 5 init eder, adım 6 geri çağırır
    ;;
  evet) ;;
  *)
    _bas "durum cevabı TANINMADI (vault status -format=json) — mühür durumu ÖLÇÜLEMEDİ"
    exit 1
    ;;
esac

[ -s "$ANAHTAR_YOLU" ] || { _bas "anahtar dosyası yok/boş: $ANAHTAR_YOLU — kasa init EDİLMİŞ, anahtar KAYIP"; exit 2; }

if [ "$(_durum_kodu)" = "0" ]; then
  _bas "mühür zaten açık — yapılacak bir şey yok (idempotent)"
  exit 0
fi

# STDIN İŞARETİ — ÖLÇÜLEN ARIZA (A1 ilk kurulum 2026-09-14 09:5xZ, Rol-1). Tur-1/2 burada
# `operator unseal -` yazıyordu ve A1'de DÜŞTÜ: Vault CLI'de `-` "değeri stdin'den oku" işareti
# `login`, `write` ve `kv put` için VARDIR, `operator unseal` için YOKTUR — o komut anahtarı ya
# argv'den alır ya da TTY'den sorar; TTY dışında (ExecStartPost, oneshot birim) "file descriptor
# 0 is not a terminal" ile çıkış 1 verir ve `-` argümanı ANAHTAR sanılır. Aynı API ucunu
# (`PUT sys/unseal`) jenerik `write` komutu stdin'den besler; uç nokta kimlik doğrulaması
# İSTEMEZ (jetonsuz ölçüldü) ve sondaki satır sonunu tolere eder (newline'lı kopyayla ölçüldü).
# Değer hiçbir değişkene alınmaz, hiçbir argümana yazılmaz; dosyadan borulanır ve süreçle
# birlikte ölür. Çıktı /dev/null'a gider: cevap gövdesi anahtar taşımaz ama journal'ı gereksiz
# doldurur. Çivi: v485 C2 (eski biçim YASAK), C5b (mutasyon), C8 (davranış).
#
# HÜKÜM API CEVABINDAN DEĞİL, DURUMDAN: `write` çıkışı "istek kabul edildi" der, "mühür açıldı"
# demez (eşik >1 olsaydı ilk pay kabul edilir ama kasa mühürlü kalırdı). "Açıldı" ancak `status`
# 0 dönünce söylenir — çivi C11/C12.
if "$VAULT_IKILI" write sys/unseal key=- < "$ANAHTAR_YOLU" >/dev/null 2>&1 && [ "$(_durum_kodu)" = "0" ]; then
  _bas "mühür açıldı"
  exit 0
fi

_bas "unseal BAŞARISIZ — anahtar yanlış ya da kasa yeniden init edilmiş olabilir"
exit 1

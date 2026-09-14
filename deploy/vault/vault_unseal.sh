#!/usr/bin/env bash
# =================================================================================================
# vault_unseal.sh — Vault mührünü AÇAR (TSK-064 Faz-2). A1'de koşar; DEPODA versiyonlanır.
# =================================================================================================
# HEDEF: /opt/vault/bin/vault_unseal.sh (0750 root:root). İKİ çağıranı vardır ve ikisi de AYNI
# dosyayı koşar (tek kaynak):
#   · vault.service  → ExecStartPost=+…   (her açılışta, crash/reboot dahil)
#   · vault-unseal.service (oneshot)      → elle/tekrar
#
# SIR DİSİPLİNİ — BU DOSYANIN VAR OLMA SEBEBİ:
#   (1) Anahtar DEĞERİ argv'ye GİRMEZ. `vault operator unseal "$(cat /etc/vault/unseal.key)"`
#       biçimi anahtarı `/proc/<pid>/cmdline`e koyar ve o dosya makinedeki HER kullanıcıya
#       OKUNABİLİRDİR. Doğru biçim `-` (stdin) ve dosya yönlendirmesidir: değer çekirdeğin
#       argüman vektörüne hiç uğramaz.
#   (2) `set -x` YOK. Açık olsaydı her komut (yönlendirme hedefleri dahil) journal'a düşerdi.
#   (3) Hiçbir `echo`/`printf` bir sır değişkeni basmaz — betik zaten hiçbir sırrı DEĞİŞKENE
#       almaz; dosyadan doğrudan stdin'e akar.
#
# BU BİR BEKLEYİCİ DÖNGÜSÜ DEĞİLDİR (CLAUDE.md §7). §7'nin yasakladığı şey, bir işin bitmesini
# yoklayan SÜRESİZ bekleyicidir. Buradaki döngü bir SERVİS AÇILIŞ YOKLAMASIDIR: sınırı sabittir
# (AYAKTA_DENEME), adımı 1 sn'dir ve tavana vurunca BAŞARISIZ döner — yani en kötü hâlde
# birkaç saniyede hüküm verir, sonsuza dek asılmaz. Emsal: dash_token_credential.sh içindeki
# `_servis_ayakta`. Type=notify zaten hazır olmadan buraya gelmez; bu döngü güvenlik ağıdır.
#
# ÇIKIŞ KODLARI (HÜKÜM):
#   0  mühür AÇIK (zaten açıktı ya da bu koşumda açıldı)
#   1  API ayağa kalkmadı / unseal başarısız  → birim `failed`, OnFailure haber verir
#   2  anahtar dosyası YOK/BOŞ               → kurulum yarım; ADIYLA söylenir, sessizce geçilmez
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
# değil" diye raporlanır, arıza yanlış yerde aranırdı.
_durum_kodu() {
  # `|| kod=$?` ZORUNLU: `set -e` altında çıplak bir başarısız komut betiği ÖLDÜRÜR ve mühürlü
  # kasa (kod 2) tam olarak "başarısız komut"tur — yani en sık karşılaşılacak hâl betiği
  # sessizce düşürürdü.
  local kod=0
  "$VAULT_IKILI" status >/dev/null 2>&1 || kod=$?
  echo "$kod"
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
[ -s "$ANAHTAR_YOLU" ] || { _bas "anahtar dosyası yok/boş: $ANAHTAR_YOLU — kurulum yarım"; exit 2; }

if ! _api_ayakta; then
  _bas "API ${AYAKTA_DENEME} sn içinde cevap vermedi ($VAULT_ADDR)"
  exit 1
fi

if [ "$(_durum_kodu)" = "0" ]; then
  _bas "mühür zaten açık — yapılacak bir şey yok (idempotent)"
  exit 0
fi

# ANAHTAR STDIN'DEN: `-` Vault CLI'nin belgelenmiş "değeri stdin'den oku" işaretidir. Değer
# hiçbir değişkene alınmaz, hiçbir argümana yazılmaz; dosyadan borulanır ve süreçle birlikte
# ölür. Çıktı /dev/null'a gider: `operator unseal` başarıda mühür durumunu basar ve o çıktı
# anahtar taşımasa da journal'ı gereksiz doldurur; HÜKÜM çıkış kodundadır.
if "$VAULT_IKILI" operator unseal - < "$ANAHTAR_YOLU" >/dev/null 2>&1; then
  _bas "mühür açıldı"
  exit 0
fi

_bas "unseal BAŞARISIZ — anahtar yanlış ya da kasa yeniden init edilmiş olabilir"
exit 1

#!/usr/bin/env bash
# =================================================================================================
# vault_sir_koy.sh — dalga-1 sırlarını MEVCUT DOSYALARDAN Vault'a taşır (TSK-064 Faz-2)
# =================================================================================================
# KİM KOŞAR: Rol-1, bakım penceresinde, `sudo` ile (kaynak dosyalar 0400 root:root).
# Ajan bu betiği YAZAR, KOŞTURMAZ (CLAUDE.md §3).
#
# KULLANIM:
#   sudo ./vault_sir_koy.sh --kuru     → hiçbir şey yazmaz; hangi sırrın hangi yola gideceğini
#                                        ve kaynak dosyanın VAR olup olmadığını listeler
#   sudo ./vault_sir_koy.sh --uygula   → değerleri kasaya koyar ve HER BİRİNİ sha256 ile doğrular
#                                        (kimlik: /etc/vault/admin.token, stdin'den — aşağıda KİMLİK bloğu)
#
# ─────────────────────────────────────────────────────────────────────────────────────────────
# DEĞER NASIL AKAR — ÜÇ KURAL
# ─────────────────────────────────────────────────────────────────────────────────────────────
#  (1) DOSYADAN BORUYLA, DEĞİŞKENSİZ. `vault kv put <yol> value=-` değeri STDIN'den okur. Değer
#      hiçbir kabuk değişkenine, hiçbir argümana, hiçbir ortam değişkenine girmez.
#  (2) SON SATIR SONU KIRPILIR (`tr -d '\r\n'`). Kaynak dosyalar `printf '%s\n'` ile yazıldığı
#      için sondaki yeni satırı taşır; Agent şablonu ise onu YAZMAZ. Kırpmasaydık kanal
#      değişimi değeri BİR BAYT değiştirir ve doğrulama her sırda düşerdi. Tüketiciler zaten
#      sondaki yeni satırı kırpıyor (çivi: tests/test_sir_credential_v439.py A2), yani kırpılmış
#      biçim KANONİK biçimdir — bu bir kolaylık değil, kanalın sözleşmesi.
#  (3) DOĞRULAMA sha256 İLEDİR ve iki taraf da YALNIZ HASH basar. "Koydum" demek yetmez: kasadan
#      geri okunan değerin kaynakla AYNI olduğu ölçülür. Eşitlik sağlanmazsa betik DURUR —
#      yarım bir taşıma, taşımamaktan tehlikelidir (Agent yanlış değeri render ederdi).
#
# `set -x` YOKTUR ve eklenmemelidir: yönlendirme hedeflerini ve boru gövdelerini journal'a
# dökerdi.
#
# GERİ ALIM: bu betik KAYNAK DOSYALARA DOKUNMAZ. Kasaya bir kopya KOYAR, dosyayı bırakır.
# Yanlış giderse `systemctl stop vault-agent` yeter; dosyalar olduğu gibi durur (tasarım §6.4).
set -euo pipefail

KAYNAK_DIZIN="$(cd "$(dirname "$0")" && pwd)"
ENVANTER="${ENVANTER:-$KAYNAK_DIZIN/../sir_envanteri.yaml}"
VAULT_BIN="${VAULT_BIN:-/usr/local/bin/vault}"
# Kuru koşumun envanteri okuması için; A1'de sistem python3'ü yeterlidir (PyYAML kurulu).
PYTHON_BIN="${PYTHON_BIN:-python3}"
export VAULT_ADDR="${VAULT_ADDR:-http://127.0.0.1:8200}"

# KİMLİK — ÖLÇÜLEN ARIZA (A1 ilk taşıma 2026-09-14 09:55Z, Rol-1): tur-1/2 bu betik ortamdaki
# oturuma GÜVENİYORDU; `vault_kur.sh` adım 7'de açtığı kök oturumunu betiğin SONUNDA SİLER
# (doğru davranış) — yani bu betik jetonsuz koştu ve ilk `kv put` ön-uçuşu 403 verdi. Kimlik
# burada AÇIKÇA kurulur, yalnız `--uygula` yolunda (kuru koşum kasaya HİÇ dokunmaz — J3):
#   · yönetici jetonu (`/etc/vault/admin.token`, 0400 root; vault_kur.sh adım 10 yazar)
#     `login -no-print -` ile STDIN'den okunur — argv'ye ve ORTAMA girmez (`VAULT_TOKEN=$(cat …)`
#     değeri `/proc/<pid>/environ`a koyardı).
#   · oturum jeton yardımcısına (`$HOME/.vault-token`, 0600) yazılır ve ÇIKIŞTA SİLİNİR (trap):
#     kalıcı bir yönetici oturumu, sonraki her root kabuğunu yönetici yapardı.
# Çivi: v485 I13 (kaynak metin), J4 (login stdin'den, jeton argv'de yok), J6 (jeton yoksa durur).
JETON_DOSYASI="${VAULT_TOKEN_FILE:-/etc/vault/admin.token}"

# sha256 ARACI İKİ ADLA GELİR: Linux'ta `sha256sum`, macOS'ta `shasum -a 256`. Bu betik A1'de
# koşar, ama TESLİMDEN ÖNCE operatörün koşacağı BİÇİMDE bir kez koşulması gerekir (CLAUDE.md §6:
# "18 çivi yeşilken `--uygula` sessizce yok sayılıyordu"). Tek satırlık bu ayrım, betiği yerelde
# de koşulabilir kılar — yani doğrulama kolunun kendisi ölçülebilir olur.
_sha256() { if command -v sha256sum >/dev/null 2>&1; then sha256sum; else shasum -a 256; fi; }

KIP=""
die() { echo "!! $*" >&2; exit 1; }

for arg in "$@"; do
  case "$arg" in
    --kuru)   [ -n "$KIP" ] && die "çelişen kip bayrağı"; KIP=kuru ;;
    --uygula) [ -n "$KIP" ] && die "çelişen kip bayrağı"; KIP=uygula ;;
    *)        die "bilinmeyen argüman: $arg (--kuru | --uygula)" ;;
  esac
done
[ -n "$KIP" ] || { echo "KULLANIM: $0 --kuru | --uygula" >&2; exit 2; }

# LİSTE ENVANTERDEN TÜRER, BETİĞE YAZILMAZ (tek-kaynak yasası): `deploy/sir_envanteri.yaml`
# `vault_kv` bloğu hangi sırrın hangi yolda durduğunun TEK kaynağıdır. Burada ikinci bir liste
# tutsaydık, envantere eklenen bir sır bu betikte sessizce eksik kalırdı.
# Çıktı biçimi: "<vault_yolu>\t<hedef dosya>" — yalnız AD ve YOL, DEĞER YOK.
_girdiler() {
  "$PYTHON_BIN" -c '
import sys, yaml
for g in yaml.safe_load(open(sys.argv[1], encoding="utf-8"))["vault_kv"]:
    print(g["vault_yolu"], g["hedef"], sep="\t")
' "$ENVANTER"
}

[ -f "$ENVANTER" ] || die "envanter bulunamadı: $ENVANTER"

if [ "$KIP" = "uygula" ]; then
  [ -s "$JETON_DOSYASI" ] || die "yönetici jetonu yok/boş: $JETON_DOSYASI (vault_kur.sh adım 10 yazar)"
  trap 'rm -f "${HOME:-/root}/.vault-token"' EXIT
  "$VAULT_BIN" login -no-print - < "$JETON_DOSYASI" >/dev/null \
    || die "yönetici jetonuyla oturum açılamadı ($JETON_DOSYASI)"
fi

echo "== dalga-1 sır taşıması ($KIP) — kaynak: $ENVANTER"
HATA=0
while IFS=$'\t' read -r yol hedef; do
  [ -n "$yol" ] || continue
  if [ ! -s "$hedef" ]; then
    # KURU KOŞUM RAPORLAR, HÜKÜM VERMEZ. `--kuru`nun işi "bugün ne var, ne yok"u göstermektir;
    # eksik bir kaynakta çıkış 1 vermek, kuru koşumu bir KAPIYA çevirirdi ve operatör listenin
    # geri kalanını hiç göremezdi. `--uygula` kipinde AYNI hâl DURDURUCUDUR: yarım bir taşıma,
    # Agent'ın yanlış değeri render etmesi demektir.
    echo "   ✗ $yol  ← KAYNAK YOK/BOŞ: $hedef"
    # `[ … ] && HATA=1` YAZILMAZ: `set -e` altında koşul YANLIŞ olduğunda liste düşer ve betik
    # tam da kuru koşumun ortasında sessizce ölürdü (aynı sınıf tuzak vault_unseal.sh'te de var).
    if [ "$KIP" = "uygula" ]; then HATA=1; fi
    continue
  fi
  if [ "$KIP" = "kuru" ]; then
    echo "   (kuru) $yol  ← $hedef  ($(stat -c '%a %U:%G' "$hedef" 2>/dev/null || echo '?'))"
    continue
  fi

  # DEĞER BORUYLA: dosya → tr (son satır sonunu kırp) → vault kv put … value=-
  tr -d '\r\n' < "$hedef" | "$VAULT_BIN" kv put "$yol" value=- >/dev/null

  # DOĞRULAMA: iki taraf da YALNIZ hash basar.
  kasa_sha="$("$VAULT_BIN" kv get -field=value "$yol" | tr -d '\r\n' | _sha256 | cut -d' ' -f1)"
  dosya_sha="$(tr -d '\r\n' < "$hedef" | _sha256 | cut -d' ' -f1)"
  if [ "$kasa_sha" = "$dosya_sha" ]; then
    echo "   ✓ $yol  (sha256 eşleşti: ${kasa_sha:0:12}…)"
  else
    echo "   ✗ $yol  SHA256 UYUŞMADI — kasadaki değer kaynakla aynı DEĞİL"
    HATA=1
  fi
done < <(_girdiler)

if [ "$HATA" != "0" ]; then
  die "en az bir sır taşınamadı/doğrulanamadı — Agent'ı BAŞLATMA, önce yukarıdaki satırları çöz"
fi

echo
if [ "$KIP" = "kuru" ]; then
  echo ">> kuru koşum bitti, hiçbir şey yazılmadı. Uygulamak için: $0 --uygula"
else
  echo ">> tamam. SIRADAKİ: systemctl enable --now vault-agent  +  canary reçetesi (vault_kur.sh başlığı)"
fi

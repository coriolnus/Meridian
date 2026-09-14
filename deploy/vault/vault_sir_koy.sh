#!/usr/bin/env bash
# =================================================================================================
# vault_sir_koy.sh — sırları MEVCUT DOSYALARDAN Vault'a taşır (TSK-064 Faz-2, dalga-1 + dalga-2)
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
# ─────────────────────────────────────────────────────────────────────────────────────────────
# DALGA-2 (2026-09-14) — KAYNAK ARTIK BİR SATIR OLABİLİR, VE KOPYALAR ÖLÇÜLÜR
# ─────────────────────────────────────────────────────────────────────────────────────────────
# Dalga-1'de kaynak hedefin KENDİSİYDİ: `/etc/meridian/<ad>` zaten doluydu ve dosyanın TAMAMI
# değerdi. Dalga-2 sırları (`OPENROUTER_API_KEY`, bot anahtarları, pano parolası, CP anahtarları)
# çok-değişkenli `.env` dosyalarının İÇİNDE yaşıyor. Envanter girdisi bu yüzden bir `kaynak:`
# bloğu taşıyabilir:
#     kaynak: {tur: env_satiri, dosya: /opt/apisix/.env-apisix, alan: OPENROUTER_API_KEY, onek: null}
# `tur: dosya` dalga-1 davranışıdır ve `kaynak:` HİÇ YOKSA da o dal koşar (geriye uyumluluk).
# Okuma kuralları: tam BİR `^ALAN=` satırı (iki satır ARIZADIR — hangisinin geçerli olduğu
# bilinemez), sarmalayan tırnak kırpılır, `onek` jetonu (`Bearer`) soyulur. Jeton sözlüğü
# `deploy/oracle-a1/sir_rotasyon.sh` ile AYNIdır: iki yazım sessizce ayrışmasın diye envanter
# önek LİTERALİNİ değil JETONUNU taşır.
#
#  (4) KOPYA EŞİTLİĞİ KAPISI — BU TURUN EN PAHALI KAPISI. Aynı değerin on üç kopyası var ve
#      2026-09-08 rotasyonu onlardan BİRİNİ atladı: kopya dört gün eski anahtarla yaşadı, arıza
#      ancak akşam incelemesinin 401'inde göründü (TSK-181). Kasaya taşırken aynı hata DAHA
#      pahalıdır: kasa artık TEK KAYNAK olduğu için yanlış kopyadan taşınan değer BÜTÜN
#      tüketicilere yayılır. Bu yüzden `kopya_kaynaklari` listesindeki her kopyanın sha256'sı
#      REFERANS kaynağınkiyle karşılaştırılır — iki taraf da YALNIZ HASH basar.
#        · `--uygula`: ayrışma DURDURUR ve o sır kasaya HİÇ KONMAZ. "Hangisi doğru" sorusunun
#          cevabı burada yoktur ve tahmin etmek, tahmini bütün tüketicilere yaymaktır.
#        · `--kuru`  : ayrışma RAPORLANIR, hüküm VERİLMEZ (kuru koşumun sözleşmesi). Ayrışmayı
#          taşımadan ÖNCE görmek, bu kipin en değerli çıktısıdır.
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
# Çıktı biçimi (TSV): "<ad>\t<vault_yolu>\t<kaynak türü>\t<kaynak dosya>\t<alan>\t<önek>"
# — yalnız AD ve YOL, DEĞER YOK. `kaynak:` bloğu olmayan (dalga-1) girdide kaynak HEDEFİN
# KENDİSİDİR ve tür `dosya`dır; boş alanlar `-` ile yazılır (boş dizge TSV'de ayırt edilemez).
_girdiler() {
  "$PYTHON_BIN" -c '
import sys, yaml
for g in yaml.safe_load(open(sys.argv[1], encoding="utf-8"))["vault_kv"]:
    k = g.get("kaynak") or {"tur": "dosya", "dosya": g["hedef"], "alan": None, "onek": None}
    print(g["ad"], g["vault_yolu"], k["tur"], k["dosya"],
          k.get("alan") or "-", k.get("onek") or "-", sep="\t")
' "$ENVANTER"
}

# AYNI SIRRIN ÖTEKİ KOPYALARI — `kopya_kaynaklari` bloğu. Liste YİNE envanterden türer; kopya
# kümesinin kendisi de `rotasyon_kopyalari` tablosuna çivilidir (v491 A5), yani bu betik üçüncü
# bir liste tutmaz. Kopyası olmayan girdide çıktı BOŞTUR ve döngü hiç dönmez.
_kopya_kaynaklari() {
  "$PYTHON_BIN" -c '
import sys, yaml
hedef = sys.argv[2]
for g in yaml.safe_load(open(sys.argv[1], encoding="utf-8"))["vault_kv"]:
    if g["ad"] != hedef:
        continue
    for k in g.get("kopya_kaynaklari") or []:
        print(k["tur"], k["dosya"], k.get("alan") or "-", k.get("onek") or "-", sep="\t")
' "$ENVANTER" "$1"
}

# DEĞERİ STDOUT'A YAZAR — ve YALNIZ boruya. Argümanları YOL, ALAN ve ÖNEK JETONUdur; DEĞER hiçbir
# argümana, değişkene ya da ortama girmez. Çağrı yerleri bunu boruyla tüketir (`| vault kv put`,
# `| _sha256`) ve çıktı bir komut ikamesine ALINMAZ — çivi (v491 D2) bunu ölçer.
# SON SATIR SONU YAZILMAZ: Agent şablonu da yazmaz, yani kırpılmış biçim KANONİK biçimdir (yukarıda
# kural 2). BOŞ değer ARIZADIR: boş bir sır, "başarıyla taşındı" görünen bir 401 fabrikasıdır.
_deger() {
  "$PYTHON_BIN" -c '
import sys
tur, yol, alan, onek = sys.argv[1:5]
onekler = {"-": "", "Bearer": "Bearer "}
if onek not in onekler:
    sys.exit("taninmayan onek jetonu: %s" % onek)
p = onekler[onek]
with open(yol, encoding="utf-8") as fh:
    ham = fh.read()
if tur == "dosya":
    deger = ham.strip("\r\n")
elif tur == "env_satiri":
    eslesen = [x for x in ham.splitlines() if x.startswith(alan + "=")]
    if len(eslesen) != 1:
        sys.exit("%s: %s satiri %d kez var (TAM BIR satir bekleniyordu)" % (yol, alan, len(eslesen)))
    govde = eslesen[0].split("=", 1)[1].strip("\r\n")
    if len(govde) >= 2 and govde[0] == govde[-1] and govde[0] in (chr(34), chr(39)):
        govde = govde[1:-1]
    deger = govde
else:
    sys.exit("taninmayan kaynak turu: %s" % tur)
if p and deger.startswith(p):
    deger = deger[len(p):]
if not deger.strip():
    sys.exit("%s: deger BOS - tasima yapilmadi" % yol)
sys.stdout.write(deger)
' "$1" "$2" "$3" "$4"
}

# `$( )` İÇİNDE AKAN ŞEY HASH'TİR, DEĞER DEĞİL. Ayrım bu betiğin bütün sır disiplinidir: değer
# boruda kalır, karşılaştırma hash üzerinden yapılır ve iki taraf da yalnız hash basar.
_sha_of() {
  _deger "$1" "$2" "$3" "$4" | _sha256 | cut -d' ' -f1
}

[ -f "$ENVANTER" ] || die "envanter bulunamadı: $ENVANTER"

if [ "$KIP" = "uygula" ]; then
  [ -s "$JETON_DOSYASI" ] || die "yönetici jetonu yok/boş: $JETON_DOSYASI (vault_kur.sh adım 10 yazar)"
  trap 'rm -f "${HOME:-/root}/.vault-token"' EXIT
  "$VAULT_BIN" login -no-print - < "$JETON_DOSYASI" >/dev/null \
    || die "yönetici jetonuyla oturum açılamadı ($JETON_DOSYASI)"
fi

echo "== sır taşıması ($KIP) — kaynak: $ENVANTER"
HATA=0
while IFS=$'\t' read -r ad yol tur kdosya kalan konek; do
  [ -n "$yol" ] || continue
  ETIKET="$kdosya"
  [ "$kalan" = "-" ] || ETIKET="$kdosya [$kalan]"
  if [ ! -s "$kdosya" ]; then
    # KURU KOŞUM RAPORLAR, HÜKÜM VERMEZ. `--kuru`nun işi "bugün ne var, ne yok"u göstermektir;
    # eksik bir kaynakta çıkış 1 vermek, kuru koşumu bir KAPIYA çevirirdi ve operatör listenin
    # geri kalanını hiç göremezdi. `--uygula` kipinde AYNI hâl DURDURUCUDUR: yarım bir taşıma,
    # Agent'ın yanlış değeri render etmesi demektir.
    echo "   ✗ $yol  ← KAYNAK YOK/BOŞ: $ETIKET"
    # `[ … ] && HATA=1` YAZILMAZ: `set -e` altında koşul YANLIŞ olduğunda liste düşer ve betik
    # tam da kuru koşumun ortasında sessizce ölürdü (aynı sınıf tuzak vault_unseal.sh'te de var).
    if [ "$KIP" = "uygula" ]; then HATA=1; fi
    continue
  fi

  # ---- KOPYA EŞİTLİĞİ KAPISI (her iki kipte de ÖLÇÜLÜR; yalnız `--uygula` DURDURUR) -----------
  # Referans sha ÖNCE ölçülür: kaynak okunamıyorsa (çift satır, boş değer) hiçbir kopya
  # karşılaştırılamaz ve taşıma zaten yapılamaz.
  if ! REF_SHA="$(_sha_of "$tur" "$kdosya" "$kalan" "$konek")"; then
    echo "   ✗ $yol  ← KAYNAK OKUNAMADI: $ETIKET (yukarıdaki satır)"
    if [ "$KIP" = "uygula" ]; then HATA=1; fi
    continue
  fi
  AYRISAN=""
  while IFS=$'\t' read -r ktur kdos kal kon; do
    [ -n "$ktur" ] || continue
    KETIKET="$kdos"
    [ "$kal" = "-" ] || KETIKET="$kdos [$kal]"
    if [ ! -s "$kdos" ]; then
      echo "     ? kopya OKUNAMADI: $KETIKET (dosya yok/boş — eşitlik ÖLÇÜLEMEDİ)"
      AYRISAN="$AYRISAN $KETIKET"
      continue
    fi
    if ! K_SHA="$(_sha_of "$ktur" "$kdos" "$kal" "$kon")"; then
      echo "     ? kopya OKUNAMADI: $KETIKET (yukarıdaki satır — eşitlik ÖLÇÜLEMEDİ)"
      AYRISAN="$AYRISAN $KETIKET"
      continue
    fi
    if [ "$K_SHA" = "$REF_SHA" ]; then
      echo "     · kopya EŞİT: $KETIKET"
    else
      echo "     ✗ kopya AYRI: $KETIKET"
      AYRISAN="$AYRISAN $KETIKET"
    fi
  done < <(_kopya_kaynaklari "$ad")

  if [ -n "$AYRISAN" ]; then
    echo "   ✗ $yol  KOPYA AYRIŞMASI:$AYRISAN"
    echo "     HANGİSİNİN doğru olduğu buradan BİLİNEMEZ ve tahmin etmek, tahmini kasadan bütün"
    echo "     tüketicilere yaymaktır. Önce kopyaları eşitle (sir_rotasyon.sh --<alt> --esitle),"
    echo "     sonra bu betiği yeniden koş."
    if [ "$KIP" = "uygula" ]; then HATA=1; continue; fi
  fi

  if [ "$KIP" = "kuru" ]; then
    echo "   (kuru) $yol  ← $ETIKET  ($(stat -c '%a %U:%G' "$kdosya" 2>/dev/null || echo '?'))"
    continue
  fi

  # DEĞER BORUYLA: kaynak → _deger (önek/tırnak soyulur) → vault kv put … value=-
  _deger "$tur" "$kdosya" "$kalan" "$konek" | "$VAULT_BIN" kv put "$yol" value=- >/dev/null

  # DOĞRULAMA: iki taraf da YALNIZ hash basar.
  kasa_sha="$("$VAULT_BIN" kv get -field=value "$yol" | tr -d '\r\n' | _sha256 | cut -d' ' -f1)"
  if [ "$kasa_sha" = "$REF_SHA" ]; then
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

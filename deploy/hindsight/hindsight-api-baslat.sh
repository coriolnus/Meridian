#!/usr/bin/env bash
# =================================================================================================
# hindsight-api-baslat.sh — hindsight-api'nin ExecStart sarmalayıcısı (TSK-064 YOL-1 Faz-1A)
# =================================================================================================
# KOŞUM YOLU (A1): /opt/meridian/deploy/hindsight/hindsight-api-baslat.sh
# Bu yol `hindsight-api.service`in `ExecStart`ında BİREBİR yazılıdır ve ayrı bir kurulum adımı
# GEREKTİRMEZ: depo zaten `/opt/meridian`a dağıtılıyor (`dagit.sh` rsync), yani bu betik her
# dağıtımda kendiliğinden tazelenir. Emsal: `meridian-tick-watchdog.service` →
# `ExecStart=/opt/meridian/deploy/oracle-a1/tick_watchdog.sh`. Betiği ayrı bir yere KOPYALAMAK
# depo kopyası ile canlı kopyayı sessizce ayrıştırırdı ve F9 kapısı o sürüklenmeyi göremezdi.
# SIRA ÖNEMLİ: önce depo dağıtılır (betik yerine oturur), SONRA birim kurulur. Ters sırada birim
# var olmayan bir ExecStart'ı çağırır ve `203/EXEC` ile ölür.
#
# ---- NE YAPAR, NEDEN VAR -----------------------------------------------------------------------
# `$CREDENTIALS_DIRECTORY` altındaki üç sır dosyasını okur, değerleri ORTAMA koyar ve gerçek
# ikiliyi `exec` eder. Gerekliliğin tamamı `hindsight-api.service.d/50-creds.conf` şerhinde:
# hindsight-api ÜÇÜNCÜ PARTİ bir süreçtir ve sırrı `HINDSIGHT_API_*` ORTAM değişkenlerinden okur;
# kaynağına dokunamayız, o yüzden kazanım YARIMDIR (B sınıfı, spec §2) ve orada dürüstçe beyanlı.
#
# ---- ÜÇ DEĞİŞMEZ -------------------------------------------------------------------------------
# (1) DEĞER BASILMAZ. Bu betiğin çıktısı JOURNAL'dır. Yalnız AD'lar yazılır (ad sır değildir ve
#     "kanal gerçekten okundu mu" sorusunun tek yerel cevabıdır — YASA 6'nın okuyucusu bakım
#     penceresindeki operatördür). `set -x` YASAK: üç sırrı da journal'a dökerdi ve 2026-09-02'de
#     bir DATABASE_URL parolası tam bu sınıftan terminale düştü. Değer hiçbir argv'ye de girmez.
# (2) MEVCUT ORTAM BOZULMAZ — İKİ KANAL AYNI ANDA CANLI (TSK-049 hükmü). Kaynak dosyası olmayan
#     ya da BOŞ olan bir ad için hiçbir şey yapılmaz: `export AD=` ya da `unset AD` yazmak,
#     faz-1'de `EnvironmentFile`dan gelen değeri SİLERDİ — yani "hareketsiz olması gereken" faz
#     servisi düşürürdü. Boş dosya bir DEĞER değildir; sıfır ile "bilmiyorum" aynı şey değildir.
# (3) BİÇİM TOLERANSI `secrets.credential_oku` İLE AYNI: ilk BOŞ OLMAYAN satır, baştaki/sondaki
#     boşluk kırpılır, `AD=` öneki tanınır (yalnız İSTENEN adın öneki — başka bir adın öneki
#     yutulmaz, çünkü o "kaynak dosyalar karışmış" demektir ve sessizce düzeltmek arızayı gizler).
#     Kırpma en sinsi arızayı kapatır: sondaki `\n` değere yapışırsa upstream 401 verir ve arıza
#     "anahtar yanlış" gibi okunur. İki okuyucunun AYNI kuralı taşıması ayrışma çivisiyle
#     korunmuyor (biri bash, biri python) — bu yüzden davranışı ikisi de KENDİ çivisiyle ölçüyor:
#     `tests/test_sir_credential_v439.py` bölüm A (python) ve bölüm I (bu betik, gerçekten koşarak).
set -euo pipefail

#: Faz-1A'nın taşıdığı üç sır. Sıra ÖNEMSİZ, küme önemli: drop-in'in `LoadCredential=` kimlikleriyle
#: BİREBİR aynı olmak zorunda (çivi I1/I2) — ayrışırsa okunmayan sır sessizce ortamdan gelmeye
#: devam eder ve faz-2'de `.env` satırı silindiği an servis düşer.
ADLAR="HINDSIGHT_API_DATABASE_URL HINDSIGHT_API_LLM_API_KEY HINDSIGHT_API_TENANT_API_KEY"

# TEST KANCASI — YALNIZ ÇİVİ İÇİN (Faz-1B'deki `SIR_GECIS_KOK` ile aynı desen). Boşken (üretimdeki
# tek hâl) gerçek ikili koşulur; `deploy/hindsight/.env`de ya da birimin `EnvironmentFile`ında bu
# ad YOKTUR. Kanca olmadan çiviler yalnız betiğin METNİNİ okuyabilirdi — ve "üç adı ortama koyuyor"
# cümlesi metinde her zaman doğru görünür (18 çivi yeşilken `--uygula`nın sessizce yok sayıldığı
# 2026-08-30 vakasının dersi: ops aracı, operatörün koşacağı BİÇİMDE bir kez koşturulur).
HEDEF="${HINDSIGHT_API_BIN:-/opt/hindsight/venv/bin/hindsight-api}"

# `<dosya>`daki değeri stdout'a yazar; değer yoksa 1 döner. DEĞER YALNIZ BURADAN AKAR: bir
# değişkene girer, `export`a gider, hiçbir yere basılmaz.
_kred_oku() {
  local ad="$1" dosya="$2" deger
  # `awk 'NF {print; exit}'` = ilk BOŞ OLMAYAN satır — python tarafındaki `ham.strip().splitlines()[0]`
  # ile aynı sonuç (baştaki boş satırlar atlanır). Düz `head -1` olsaydı başında boş satır olan bir
  # kaynak dosya iki okuyucuda İKİ FARKLI sonuç verirdi.
  deger="$(awk 'NF {print; exit}' "$dosya" 2>/dev/null | tr -d '\r' \
           | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  case "$deger" in
    "$ad="*) deger="${deger#"$ad="}" ;;
  esac
  [ -n "$deger" ] || return 1
  printf '%s' "$deger"
}

if [ -n "${CREDENTIALS_DIRECTORY:-}" ]; then
  _yuklenen=""
  for _ad in $ADLAR; do
    _dosya="$CREDENTIALS_DIRECTORY/$_ad"
    [ -f "$_dosya" ] || continue
    # `|| continue`: okunamayan/boş kaynak ORTAMI OLDUĞU GİBİ BIRAKIR (değişmez 2). Bu bir sessiz
    # yutma değildir — atlanan ad aşağıdaki rapor satırında GÖRÜNMEZ, yani "yüklendi" listesinde
    # olmaması operatöre eksikliği ADIYLA söyler.
    _deger="$(_kred_oku "$_ad" "$_dosya")" || continue
    export "$_ad=$_deger"
    unset _deger
    _yuklenen="$_yuklenen $_ad"
  done
  # YALNIZ ADLAR (değişmez 1). Boş listede satır hiç yazılmaz: "credential kanalı var ama hiçbir
  # şey yüklenmedi" hâli sessiz kalmasın diye değil — o hâlde `_yuklenen` boştur ve aşağıdaki
  # satır ADI OLMAYAN bir rapor üretirdi; eksikliğin doğru okuyucusu systemd'nin kendisidir
  # (kaynak yoksa birim zaten açılmaz).
  [ -z "$_yuklenen" ] || \
    printf 'hindsight-api-baslat: credential kanalından yüklendi:%s\n' "$_yuklenen" >&2
fi

# `exec`: sarmalayıcı süreç KALMAZ. Aksi hâlde birimin ana süreci bu kabuk olurdu ve systemd'nin
# `Restart=on-failure` / SIGTERM hükmü hindsight-api'ye değil kabuğa uygulanırdı — kapatmada
# python süreci sahipsiz kalırdı (`meridian.service`in `KillMode` şerhinde ölçülmüş sınıf).
exec "$HEDEF" --host 127.0.0.1 --port 8888

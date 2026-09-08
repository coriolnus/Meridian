#!/usr/bin/env bash
# =================================================================================================
# sir_rotasyon.sh — A1 sırlarının ROTASYONU (DEĞER değişir, KANAL değişmez)
# =================================================================================================
# SUNUCUDA (A1) KOŞAR — `deploy.sh`/`cutover.sh`/`sir_credential_gecis.sh` ile aynı sözleşme.
# Otomatik ÇAĞRILMAZ: bakım penceresinde, operatör eliyle. KARDEŞİNDEN FARKI: `sir_credential_gecis.sh`
# bir sırrın KANALINI taşır (ortam → LoadCredential); bu betik kanala DOKUNMAZ, sırrın DEĞERİNİ
# döndürür ve o değerin BÜTÜN KOPYALARINI aynı pencerede eşitler.
#
# NİYE BİR BETİK. 2026-09-07 gecesi dört sır A1'de ELLE döndürüldü: her sırrın 2-12 kopyası var ve
# kopyalar AYRI dosyalarda yaşıyor (credential kaynağı · `.env` satırı · docker env-file · bot
# profili · LLM failover zincirinin ÜYE satırları). Elle rotasyonda kaçınılmaz tek hata "bir
# kopyayı unutmak"tır ve o hata SESSİZDİR: yeniden başlatılan birim çalışır, unutulan kopyayı
# okuyan öteki birim ilk çağrısında 401 alır.
# Betik kopya listesini SABİT taşır (`--kopyalar`), hepsini tek pencerede yazar, sonra ölçer.
#
# HAFIZA FAILOVER ZİNCİRİ — ÜYE ANAHTARI ANA ANAHTARI DEVRALMAZ. Hindsight'ın reflect ve
# konsolidasyon yüzeyleri 2026-09-06'dan beri çok-LLM failover zinciriyle koşuyor
# (EDG-2026-080/081) ve zincirin HER ÜYESİ kendi `HINDSIGHT_API_<yüzey>_LLM_<n>_API_KEY` satırını
# okur — "provider/anahtar devralınır" YALNIZ birincil model içindir. Ölçüm 2026-09-08 08:0xZ
# (A1, yalnız AD okundu): `/opt/hindsight/.env` altı üye satırı taşıyor (REFLECT _1.._3 ·
# CONSOLIDATION _1.._3) ve altısı da OPENROUTER_API_KEY değerinin birebir kopyası. Tabloda
# olmasalardı `--openrouter` creds dosyasını döndürür, üyeler ESKİ anahtarla kalır ve eski anahtar
# iptal edildiği an üyeler 401 alıp zincir SESSİZCE birincile düşerdi — yani bu betiğin var olma
# gerekçesindeki "unutulan kopya" sınıfının tam kendisi. Altısı da tabloya girdi; OPENROUTER
# artık 12 kopya (NOUS 2).
# BEYANLI KABUL: birincilin anahtarı (`/etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY`) AYRI ve
# LoadCredential kanalındadır; ÜYE satırları değeri `.env` içinde tutar, yani hafızanın bu kanalı
# B SINIFIDIR (yarım kazanım) ve öyle beyan edilir — kanalı taşımak bu betiğin işi DEĞİL
# (`sir_credential_gecis.sh`), ama değeri döndürmek işidir.
#
# KULLANIM — BETİK ROOT OLARAK KOŞAR (alt komut ZORUNLU; her biri TEK sırrı döndürür):
#   sudo ./sir_rotasyon.sh --envanter     → kopyaların VARLIĞI + birbirine EŞİTLİĞİ (yalnız bool)
#   ./sir_rotasyon.sh --kopyalar          → kopya sözleşmesi (üretim yolları; envanter çivisinin
#                                           kaynağı). TEK root İSTEMEYEN alt komut: hiçbir dosya
#                                           açmaz, yalnız gömülü tabloyu basar.
#   sudo ./sir_rotasyon.sh --kapi         → KAPI_APIKEY (kapı tüketici anahtarı `motor_meridian`)
#   sudo ./sir_rotasyon.sh --tenant       → HINDSIGHT_API_TENANT_API_KEY
#   sudo ./sir_rotasyon.sh --db           → Postgres `hindsight` rol parolası
#   sudo ./sir_rotasyon.sh --dash         → MERIDIAN_DASH_TOKEN
#   sudo ./sir_rotasyon.sh --openrouter   → OpenRouter anahtarları (operatör YAPIŞTIRIR, `read -s`)
#   ... --kuru                            → KURU KOŞUM: ne yazılacağını + hangi birimin yeniden
#                                           başlayacağını listeler, HİÇBİR ŞEY yazmaz
#
# ÖN KOŞUL — `meridian-tick-watchdog.timer` DURDURULUR (kalıcı kayıt `bakim-penceresi-tick-watchdog`).
# Timer 45 dk bayat nabızda worker'ı yeniden başlatır; bu betik meridian'ı `--openrouter`de ÜÇ kez
# yeniden başlatır ve HER restart `/healthz`i dakikalarca 503 (bayat) yapar. Timer pencerenin
# ortasında ateşlenirse ölçüm SEBEPSİZ "ölçülemedi" verir ve bunun sebebi betiğin çıktısından ASLA
# anlaşılmaz — yani teşhis edilemeyen bir arıza. Pencerenin başında ve sonunda:
#   sudo systemctl stop meridian-tick-watchdog.timer     # BAŞTA
#   sudo systemctl start meridian-tick-watchdog.timer    # SONDA
# `--kuru` bu satırı da basar (kuru koşum operatörün koşacağı İLK komuttur).
#
# TAVANI YÜKSELTMEK GEREKİRSE — DÜZ `sudo` ORTAM DEĞİŞKENİNİ DÜŞÜRÜR. sudo'nun varsayılan
# `env_reset`i `HAZIR_TAVAN_S_*`/`SIR_ROT_*`ı temizler, yani aşağıdaki "operatör tavanı ÖLÇEREK
# yükseltebilir" sözleşmesi BELGELENEN çağrı biçiminde (`sudo ./sir_rotasyon.sh …`) çalışmaz.
# Güvenli biçim (çivi bu satırı koddaki varsayılandan TÜRETEREK arar):
#   sudo env HAZIR_TAVAN_S_hindsight_api=300 ./deploy/oracle-a1/sir_rotasyon.sh --openrouter
#
# NİYE ROOT — VE NİYE BU BİR AYRINTI DEĞİL. Betik iki iş yapar: 0400 root dosyalarını YAZAR ve o
# dosyalardan türettiği kanıt GİRDİLERİNİ (curl `-K` yapılandırması, `PGPASSFILE`, SQL dosyası)
# başka bir sürece OKUTUR. İlk tur bu iki yarıyı AYRI kimliklere bölmüştü: yazan taraf
# `sudo python3` (root, 0600), okuyan taraf (`curl`, `psql`) çağıranın kimliği (ubuntu). Root'un
# yazdığı 0600 dosyayı ubuntu AÇAMAZ: `curl -K` "cannot read config" ile düşer, `_curl_kod`
# `000` döner ve HER kanıt 000 olur. Sonuç sessiz değil ama geçtir: `--kapi`/`--dash`/`--tenant`
# sırrı DÖNDÜRÜR, sonra kanıtı ölçemeyip çıkış 2 verir (bakım penceresi doğrulanmamış bir
# rotasyonla kapanır); `--openrouter` negatif kontrolde durur ve rotasyon hiç YAPILAMAZ. Kapı bu
# yüzden ÜST DÜZEYDE ve MEKANİKTİR: `id -u` 0 değilse betik ilk satırda durur. İçerideki `sudo`
# önekleri KALIR — root altında no-op'turlar ve betiği kardeşleriyle (`deploy.sh`, `cutover.sh`)
# aynı okunur biçimde tutarlar. `mod=koru`/`sahip=koru` satırları (ubuntu sahipli hermes
# profilleri, `/opt/hindsight/.key`) root altında da MEVCUT sahip ve izinle yazılır: root'un
# yazıyor olması, dosyayı root'a DEVRETMEK değildir.
#
# DEĞER ÜRETİMİ. `--kapi`/`--db`/`--dash`: `openssl rand -base64 36 | tr '+/' '-_'` → 48 karakter
# URL-güvenli. `--tenant`: `openssl rand -hex 32` → 64 hex. Üretimden SONRA uzunluk denetlenir;
# boş ya da yalnız boşluk olan değer bir ARIZADIR (bir kez ölçüldü: boş credential dosyası birimi
# sessizce yetkisiz bıraktı) ve betik durur. `--openrouter` üretmez: iki anahtarı operatör
# OpenRouter panosunda üretir ve buraya `read -s` ile yapıştırır.
#
# SIR DEĞERİ HİÇBİR YOLA BASILMAZ. Ne terminale, ne loga, ne argv'ye. Hash de basılmaz: bir
# sha256'nın ilk sekiz hanesi "değeri sızdırmayan bir kimlik" gibi görünür ama iki koşumu
# birbirine bağlayan bir izdir ve bu betikte hiçbir işi yoktur. Basılan tek şey KARAR'dır:
# "yazıldı" · "EŞİT/AYRI" · "200/401" · "ölçülemedi". Değer YALNIZ 0600 geçici dosyalar ve
# `curl -K` yapılandırma dosyaları üzerinden akar (2026-09-02 vakası: URL-gömülü parola argv'den
# terminale düştü). Kanıt: `tests/test_sir_rotasyon_v447.py`.
#
# KANIT SÖZLEŞMESİ — İKİ HÜKÜM, İKİSİ BİRDEN. Bir rotasyon "yeni anahtar 200 döndü" ile
# KANITLANMAZ: kilit yürürlükte değilse yanlış anahtar da 200 döner ve ölçüm bir tiyatrodur.
# Her alt komut İKİ ölçüm yapar: POZİTİF (yeni değer → 200 / `ok:true` / `1`) ve NEGATİF (eski ya
# da bilerek bozuk değer → 401/402 / `ok:false` / FATAL). İkisi AYRIŞMAZSA kanıt anahtara bağlı
# DEĞİLDİR; betik "ölçülemedi" der ve ÇIKIŞ 2 verir — uydurma yasağı, "geçti" demez.
# `--openrouter`de negatif kontrol YAZIMDAN ÖNCE koşar (bilerek bozuk değer, trap ile geri alınır):
# kanıt anahtara bağlı değilse operatörün TAZE anahtarı hiç yazılmaz ve boşa harcanmaz.
#
# HAZIRLIK BEKLEME — KANIT ZAMANA DA BAĞLIDIR. `systemctl restart` DÖNMESİ, birimin DİNLEDİĞİ
# anlamına gelmez. 2026-09-08 06:13Z'de `--openrouter`in ilk canlı koşumu tam buradan düştü:
# negatif kontrol üç birimi yeniden başlattı ve hemen ölçtü, meridian henüz ayakta olmadığı için
# curl `000` döndü ve betik (doğru biçimde) "ÖLÇÜM ARIZASI" deyip geri aldı — hiçbir zarar yok,
# ama rotasyon da yok. Her yeniden başlatmadan sonra birimin sağlık ucu YOKLANIR.
#
# "HAZIR" BİRİM BAŞINA TANIMLIDIR — 200 ŞARTI HER YÜZEY İÇİN DOĞRU DEĞİLDİR. İKİNCİ canlı deneme
# (2026-09-08 07:2x-07:4xZ, A1) iki AYRI kökten düştü ve ikisi de bu tanımın içindedir:
#   · meridian `/healthz` yeniden başlatmadan sonra DAKİKALARCA `503` döner; gövde
#     `{"status":"stale","heartbeat_age_seconds":…}`. Worker açılışta ağır bar tazelemesi yapar
#     ve o sırada nabız YAZILMAZ — ama API AYAKTADIR: aynı anda `/api/secrets/test/nous` cevap
#     verir. Yani meridian için hazırlık şartı "HTTP cevabı var" (`000` DEĞİL); `200` nabız
#     TAZELİĞİNİN ölçüsüdür, ayakta olmanın değil. 200 şartı koşmak, sağlıklı ama meşgul bir
#     motoru "ölü" saymaktır. `apisix` `/healthz` rotası meridian'a PROXY'dir → aynı gövde, aynı
#     hüküm. hindsight-api `/health` KENDİ sürecidir ve orada `200` gerçekten hazırlıktır.
#   · hindsight-api'nin ölçülen açılışı ~60 s'dir (07:34:18 restart → 07:35:18 "Application
#     startup complete"), yani 60 s'lik ORTAK tavan SINIRDA: ilk deneme tam oradan
#     "hazırlık bekleme aşıldı: hindsight-api … 000" ile düştü. Tavan bu yüzden birim başınadır —
#     hindsight-api 300 s, ötekiler 60 s. 300'ün gerekçesi 2026-09-08 08:07:06→08:08:45 ölçümüdür:
#     açılış 99 s, yani 180 s yalnız 1,8× paydı ve NEGATİF KONTROLDEKİ (bilerek bozuk anahtarlı)
#     açılış yolu HİÇ ölçülmedi. Dar tavanın bedeli ucuz değildir: aşım, birimleri bozuk değerle
#     bırakan kurtarma yoluna sokar (bkz. `_negatif_restart_kurtarma`).
# Kabul ölçütü ve tavan TEK yerde yaşar (`_hazir_uc` · `_hazir_tavan`); `--kuru` İKİSİNİ DE basar.
# 2 s aralıkla yoklanır (`HAZIR_BEKLE_ARALIK_S` · `HAZIR_BEKLE_TAVAN_S` ·
# `HAZIR_TAVAN_S_hindsight_api` ile ölçerek değiştirilebilir). Ölçülen açılışlar 2026-09-08:
# meridian 6-8 s (HTTP cevabı; 200 çok daha geç) · hindsight-api ~60 s (200) · apisix 5-10 s.
# Süre ÇIKTIYA BASILIR ve 200 GELMEDEN hazır sayılan birimin satırı bunu SÖYLER
# ("hazır: meridian 7 s (healthz 503 — nabız bayat, API ayakta)") — sessizce geçmek, ölçülmemiş
# bir tazeliği ölçülmüş göstermek olurdu. Tavan aşılırsa betik "hazır" demez, `ölçülemedi` der ve
# çıkış 2 verir. Sağlık ucu tanımlı OLMAYAN birim (`hindsight-cp.service`) beklenmez ve hazır
# SAYILMAZ — satır bunu söyler.
#
# GERİ-DÜŞÜŞ ZİNCİRİ — NOUS BACAĞININ İNCE YERİ. Motor sırrı TEK yerden okumaz:
# `meridian/secrets.py::_fetch` sırayla credential → süreç ortamı → `state/secrets.json` → GCP
# dener (meridian.service'te ortam basamağı ölüdür; drop-in `51-dash-env-kaldir.conf`). Yani
# credential'ı boşaltmak TEK BAŞINA hiçbir şey ölçmez: motor bir sonraki basamaktaki eski ama
# HÂLÂ GEÇERLİ kopyaya düşer, `ping_brain` ok:true döner ve negatif kontrol "kanıt anahtara bağlı
# değil" hükmüne varıp ÇIKIŞ 2 verirdi — rotasyon hiç yapılamazdı. Bu yüzden boşluk ölçümü İKİ ucu
# birden kapatır: credential kaynağı BOŞALTILIR ve motorun kendi deposundaki kopya `DELETE
# /api/secrets/<ad>` ile SİLİNİR. İkisi de yedeklidir ve trap her yolda geri koyar. Aynı gerekçe
# POZİTİF tarafta da geçerlidir: NOUS'un yeni değeri önce YALNIZ credential kaynağına yazılır,
# kanıt ölçülür, depo kopyası ANCAK ONDAN SONRA eşitlenir — yoksa pozitif kanıt da hangi kanalın
# okunduğunu söylemezdi.
#
# YEDEK. Her koşum ÖNCE `/root/sir-yedek-<UTC ts>-<alt komut>/` (0700 root) altına dokunacağı her
# dosyayı `cp -p` ile alır. Ad SANİYE taşır: aynı sırrı gün içinde iki kez döndürmek ilk yedeği
# EZMEZ. Geri alma reçetesi RUNBOOK'ta değil burada, çünkü okunacağı an bu betiğin çıktısıdır:
# `sudo cp -p <yedek>/<yol> <yol>` + ilgili birimleri yeniden başlat.
#
# YAPMADIKLARI (burada olmayan şey, burada yapılmayacak şeydir): kanal geçişi yapmaz (o
# `sir_credential_gecis.sh`); drop-in kurmaz; Vault'a dokunmaz; operatörün YEREL `.env` kopyasını
# eşitlemez (Rol-1'in işi, kapsam dışı); pano parola oturumunu etkilemez (ayrı sır).
# =================================================================================================
set -euo pipefail

# TEST KANCASI — YALNIZ ÇİVİ İÇİN. Boşken (üretimdeki tek hâl) yollar MUTLAKTIR; v447 çivisi burayı
# tmp'ye çevirip alt komutları GERÇEKTEN koşturur (PATH şimleriyle: sudo/systemctl/curl/psql/install).
# Ops aracını teslim etmeden önce operatörün koşacağı BİÇİMDE koşmanın yolu budur — 18 çivi
# yeşilken bir `--uygula` bayrağının sessizce yok sayıldığı 2026-08-30 vakasının dersi.
KOK="${SIR_ROT_KOK:-}"

#: Kanıt uçları. Hepsi loopback; testte şim curl'ü bunları tanır. Ortamdan geçilebilir olmaları
#: kanca DEĞİL sözleşmedir: A1'de portlar sabittir, çivi başka portta koşar.
API="${SIR_ROT_API:-http://127.0.0.1:8080}"
HINDSIGHT="${SIR_ROT_HINDSIGHT:-http://127.0.0.1:8888}"
#: Kapının KÖKÜ ayrı bir sabittir çünkü iki AYRI uç kullanılır: kanıt `/llm/v1/…`, hazırlık
#: yoklaması `/healthz`. Port TEK yerde yaşasın diye `KAPI_UC` kökten TÜRETİLİR — iki yere
#: yazılmış bir port sessizce ayrışırdı (tek-kaynak yasası).
KAPI_KOK="${SIR_ROT_KAPI_KOK:-http://127.0.0.1:9080}"
KAPI_UC="${SIR_ROT_KAPI:-$KAPI_KOK/llm/v1}"

#: HAZIRLIK BEKLEME penceresi. Ölçüm 2026-09-08 (A1, elle rotasyon penceresi): meridian
#: `/healthz` 6-8 s, hindsight `/health` 3-10 s, apisix `/healthz` 5-10 s. Tavan o ölçümün ~6
#: katıdır: dar tavan sağlıklı ama yavaş bir açılışı "ölçülemedi" sayar, geniş tavan bakım
#: penceresini uzatır. Ortamdan geçilebilir olmaları kanca DEĞİL sözleşmedir (uçlarla aynı
#: gerekçe): yükün yüksek olduğu bir pencerede operatör tavanı ÖLÇEREK yükseltebilir, ve çivi
#: bekleme dalını dakikalar sürmeden koşabilir.
#: TAVAN BİRİM BAŞINADIR ÇÜNKÜ AÇILIŞ SÜRELERİ BİR MERTEBE AYRIŞIYOR (ölçüm 2026-09-08 07:3xZ,
#: A1): hindsight-api `/health` 200'ü restart'tan ~60 s sonra verir — ortak 60 s tavanı SINIRDIR
#: ve ikinci canlı deneme tam oradan düştü. 300 = ölçüm + pay: aynı gün 08:07:06→08:08:45 açılışı
#: 99 s ölçüldü, yani 180 yalnız 1,8× paydı. Ötekiler (meridian · apisix) "HTTP
#: cevabı" ölçütüyle saniyeler içinde geçer; onlara da 180 vermek, gerçekten ölü bir birimi üç kat
#: uzun beklemek olurdu — geniş tavanın bedelini bakım penceresi öder.
HAZIR_BEKLE_ARALIK_S="${HAZIR_BEKLE_ARALIK_S:-2}"
HAZIR_BEKLE_TAVAN_S="${HAZIR_BEKLE_TAVAN_S:-60}"
HAZIR_TAVAN_S_hindsight_api="${HAZIR_TAVAN_S_hindsight_api:-300}"

ISLIK=""          # 0700 çalışma dizini (değer taşıyan geçici dosyalar YALNIZ burada yaşar)
YEDEK=""          # bu koşumun yedek dizini
KURU=0            # --kuru: hiçbir yazım yok
GERI_AL_LISTESI=""  # negatif kontrolün geri alacağı <yedek>|<hedef> çiftleri
#: NEGATİF KONTROLÜN BOZUK/BOŞ DEĞERLE YENİDEN BAŞLATTIĞI BİRİMLER. Dosyaları geri almak YETMEZ:
#: birim değeri AÇILIŞTA okur (apisix `$env://` çözümünü yalnız açılışta yapar, systemd
#: `LoadCredential`ı yalnız açılışta kopyalar). Trap bu kümeyi geri almadan SONRA yeniden başlatır.
NK_BIRIMLER=""

die()      { echo "!! $*" >&2; exit 1; }
olcum_yok(){ echo "!! ÖLÇÜLEMEDİ: $*" >&2; exit 2; }
oldu()     { echo "  ✓ $*"; }
adim()     { echo "-- $*"; }

# =================================================================================================
# KOPYA SÖZLEŞMESİ — bu betiğin TEK KAYNAĞI
# =================================================================================================
# Sütunlar: <alt komut> <sır kimliği> <tür> <hedef> <alan> <mod> <sahip:grup> <önek>
#   tür=dosya : hedefin TAMAMI değerdir (LoadCredential kaynağı ya da çıplak anahtar dosyası)
#   tür=env   : hedefteki `^<alan>=` satırının SAĞ TARAFI değerdir (tırnak biçimi korunur)
#   tür=url   : hedefin tamamı bir DSN'dir; YALNIZ parola alanı değişir (query korunur)
#   tür=api   : dosya değil, motorun kendi ucu (`POST <hedef>`) — dışarıdan OKUNAMAZ
#   tür=sql   : dosya değil, `ALTER ROLE <hedef> PASSWORD` (parola argv'ye GİRMEZ)
#   mod/sahip=`koru` : dosyanın MEVCUT izni ve sahibi korunur (ölçülmemiş izni uydurmaktansa koru)
#   önek=`Bearer`    : değerin başına `Bearer ` (tek boşluk) eklenir — kapının upstream başlığı
#   `-`              : alan yok
#
# YOLLAR ÜRETİM YOLLARIDIR (KOK öneki YOK). `--kopyalar` bu tabloyu AYNEN basar ve
# `deploy/sir_envanteri.yaml` ile çivilenir (v447): betikteki her `dosya`/`env`/`url` yolu
# envanterde olmak ZORUNDA. İki liste ayrışırsa rotasyon envanterin görmediği bir kopyayı yazar
# ya da envanterdeki bir kopya rotasyonsuz bayatlar — tek-kaynak yasasının tam olarak yasakladığı
# hâl. Ölçüm: 2026-09-07 22:0xZ, A1 (elle rotasyon penceresinde, yalnız AD ve YOL okundu).
_kopyalar() {
  cat <<'KOPYA_SON'
kapi KAPI_APIKEY dosya /etc/meridian/kapi_apikey - 0400 root:root -
kapi KAPI_APIKEY env /opt/apisix/.env-apisix BOT_KEY_MERIDIAN koru koru -
tenant HINDSIGHT_API_TENANT_API_KEY dosya /etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY - 0400 root:root -
tenant HINDSIGHT_API_TENANT_API_KEY dosya /opt/hindsight/.key - koru koru -
tenant HINDSIGHT_API_TENANT_API_KEY env /opt/hindsight/.env-cp HINDSIGHT_CP_DATAPLANE_API_KEY koru koru -
db HINDSIGHT_DB_PAROLA sql hindsight - - - -
db HINDSIGHT_DB_PAROLA url /etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL - koru koru -
dash MERIDIAN_DASH_TOKEN dosya /etc/meridian/dash_token - 0400 root:root -
dash MERIDIAN_DASH_TOKEN env /opt/meridian/.dash.env MERIDIAN_DASH_TOKEN koru koru -
openrouter NOUS_API_KEY dosya /etc/meridian/nous_api_key - 0400 root:root -
openrouter NOUS_API_KEY api /api/secrets/NOUS_API_KEY - - - -
openrouter OPENROUTER_API_KEY env /opt/apisix/.env-apisix OPENROUTER_API_KEY koru koru -
openrouter OPENROUTER_API_KEY env /opt/apisix/.env-apisix OPENROUTER_AUTH koru koru Bearer
openrouter OPENROUTER_API_KEY dosya /etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY - 0400 root:root -
openrouter OPENROUTER_API_KEY env /opt/hindsight/.env HINDSIGHT_API_REFLECT_LLM_1_API_KEY koru koru -
openrouter OPENROUTER_API_KEY env /opt/hindsight/.env HINDSIGHT_API_REFLECT_LLM_2_API_KEY koru koru -
openrouter OPENROUTER_API_KEY env /opt/hindsight/.env HINDSIGHT_API_REFLECT_LLM_3_API_KEY koru koru -
openrouter OPENROUTER_API_KEY env /opt/hindsight/.env HINDSIGHT_API_CONSOLIDATION_LLM_1_API_KEY koru koru -
openrouter OPENROUTER_API_KEY env /opt/hindsight/.env HINDSIGHT_API_CONSOLIDATION_LLM_2_API_KEY koru koru -
openrouter OPENROUTER_API_KEY env /opt/hindsight/.env HINDSIGHT_API_CONSOLIDATION_LLM_3_API_KEY koru koru -
openrouter OPENROUTER_API_KEY env /home/ubuntu/.hermes/profiles/bekci/.env OPENROUTER_API_KEY koru koru -
openrouter OPENROUTER_API_KEY env /home/ubuntu/.hermes/profiles/karne/.env OPENROUTER_API_KEY koru koru -
openrouter OPENROUTER_API_KEY env /home/ubuntu/.hermes/profiles/sef/.env OPENROUTER_API_KEY koru koru -
KOPYA_SON
}

#: SIR → TÜKETİCİ BİRİMLER. Rotasyon bir sırrın DEĞERİNİ okuyan birimi yeniden başlatır; okumayanı
#: DEĞİL. Ölçüm 2026-09-08 07:3xZ (A1): `--openrouter`in NOUS negatif kontrolü ÜÇ birimi birden
#: yeniden başlatıyordu, oysa `NOUS_API_KEY`i YALNIZ motor tüketir (kapı isteğin Authorization'ını
#: upstream'e geçirmez, hafıza NOUS okumaz). İki gereksiz restart demek — hindsight ~60 s açıldığı
#: için — bakım penceresinde iki uzun ve KARŞILIKSIZ bekleme demektir; üstelik ölçülmek istenen
#: sırla ilgisi olmayan iki birimi kesintiye uğratır.
#: KAYNAK: `deploy/sir_envanteri.yaml` → `rotasyon_kopyalari.kopyalar[].tuketici`. Kopya tablosu
#: BİRİM SÜTUNU TAŞIMAZ (satırın anlamı "hangi DOSYA"dır, "hangi BİRİM" değil), o yüzden harita
#: burada ayrıca yaşar ve envanterle AYRIŞMA ÇİVİSİYLE bağlanır (v447 N bölümü): türetilemeyen
#: kopya çivisiz bırakılmaz.
#: RESTART İSTEMEYEN TÜKETİCİLER BEYANLIDIR (bedel yasası — sessiz atlama, ölçülmemiş atlamadır):
#: hermes bot profilleri (bekci·karne·sef) ve `brifing/learn/sprint@` timer'lı ONESHOT'tur, yeni
#: değeri bir sonraki tetikte okur; `postgres` parolayı `ALTER ROLE` ile anında alır; motorun
#: kendi sır deposu (`/api/secrets/…`) meridian sürecinin İÇİDİR, ayrı bir birim değildir.
_sir_birimleri() {
  case "$1" in
    KAPI_APIKEY)                  echo "apisix.service meridian.service" ;;
    HINDSIGHT_API_TENANT_API_KEY) echo "hindsight-api.service hindsight-cp.service meridian.service" ;;
    HINDSIGHT_DB_PAROLA)          echo "hindsight-api.service" ;;
    MERIDIAN_DASH_TOKEN)          echo "meridian.service" ;;
    NOUS_API_KEY)                 echo "meridian.service" ;;
    OPENROUTER_API_KEY)           echo "apisix.service hindsight-api.service" ;;
    *) return 1 ;;
  esac
}

#: Yeniden başlatma SIRASI bir BAĞIMLILIK sırasıdır, alfabe değil: kapıyı (apisix) motordan ÖNCE
#: yeniden başlatmazsan motor yeni anahtarla eski kapıya konuşur ve ilk turda 401 alır.
#: `$env://` çözümünü apisix YALNIZ açılışta yapar — reload YETMEZ, RESTART gerekir. Sıra TEK
#: yerde yaşar: birim kümesi nereden gelirse gelsin (alt komutun tamamı ya da tek bir sırrın
#: tüketicileri) buradan geçer, yani "sıra" ile "küme" birbirinden bağımsız değişebilir.
_BIRIM_SIRASI="apisix.service hindsight-api.service hindsight-cp.service meridian.service"

#: Verilen birimleri bağımlılık sırasına dizer ve TEKİLLEŞTİRİR: iki sır aynı birimi tüketebilir
#: (`--openrouter`de meridian NOUS'tan, hindsight-api OPENROUTER'dan gelir) ve aynı birimi iki kez
#: yeniden başlatmak bir kesintiyi iki kez ödemektir.
_sirala() {
  local b g cikti=""
  for b in $_BIRIM_SIRASI; do
    for g in "$@"; do
      if [ "$g" = "$b" ]; then cikti="${cikti:+$cikti }$b"; break; fi
    done
  done
  [ -n "$cikti" ] || return 1
  echo "$cikti"
}

#: ALT KOMUTUN birim kümesi TÜRETİLİR: o alt komutun kopya tablosundaki sırların tüketicilerinin
#: birleşimi. Elle yazılmış ikinci bir tablo `_sir_birimleri` ile sessizce ayrışırdı (tek-kaynak
#: yasası) — ve ayrışmanın belirtisi "bir birim yeniden başlatılmadı"dır, yani hiçbir şey.
#: v447 beş alt komutun çıktısını AYNEN pinler: türetme yanlışsa çivi öter.
_birimler() {
  local alt="$1" _alt sir _rest onceki="" tuketici hepsi=""
  while read -r _alt sir _rest; do
    [ "$_alt" = "$alt" ] || continue
    [ "$sir" != "$onceki" ] || continue
    onceki="$sir"
    tuketici="$(_sir_birimleri "$sir")" \
      || die "sır $sir için tüketici birim haritası YOK (_sir_birimleri) — hangi birimin yeniden
     başlayacağı ÖLÇÜLEMEZ; kopya tablosuna sır eklenirken harita da eklenir (v447 N bölümü)."
    hepsi="$hepsi $tuketici"
  done < <(_kopyalar)
  [ -n "$hepsi" ] || return 1
  # shellcheck disable=SC2086
  _sirala $hepsi
}

#: `<birim> <credential kimliği>` — yeniden başlatmadan SONRA `/run/credentials/<birim>/<kimlik>`
#: boyutu ÖLÇÜLÜR (>1 bayt). Kimlikler drop-in'lerdeki `LoadCredential=<kimlik>:<kaynak>` ile
#: BİREBİR aynıdır; ayrışırsa betik bir dosyaya yazar, systemd başka bir kimliği arar ve arıza
#: ancak ilk gerçek çağrıda görünür. 2026-09-07: BOŞ bir credential dosyası tam bu yoldan
#: birimi sessizce yetkisiz bıraktı — o yüzden ölçüm "var mı" değil "boyutu > 1 mi".
_kredensiyeller() {
  cat <<'KRED_SON'
kapi meridian.service KAPI_APIKEY
tenant meridian.service HINDSIGHT_API_TENANT_API_KEY
tenant hindsight-api.service HINDSIGHT_API_TENANT_API_KEY
db hindsight-api.service HINDSIGHT_API_DATABASE_URL
dash meridian.service dash_token
openrouter meridian.service NOUS_API_KEY
openrouter hindsight-api.service HINDSIGHT_API_LLM_API_KEY
KRED_SON
}

#: BEYAN DIŞI KOPYA TARAMASI — bedel yasasının bu betikteki karşılığı. Kopya tablosu bir BEYANDIR;
#: beyan gerçeği kendiliğinden doğrulamaz. `--envanter` bu dosyaların hepsinde döndürülen ADLARI
#: arar ve tabloda OLMAYAN bir eşleşme bulursa bağırır: rotasyonun görmediği bir kopya, ilk
#: rotasyondan sonra sessizce ESKİ değeri taşıyan bir kopyadır (spec Bulgu-2 sınıfı).
_taranan_dosyalar() {
  cat <<'TARA_SON'
/opt/meridian/.env
/opt/meridian/.dash.env
/opt/hindsight/.env
/opt/hindsight/.env-cp
/opt/apisix/.env-apisix
/home/ubuntu/.hermes/profiles/bekci/.env
/home/ubuntu/.hermes/profiles/karne/.env
/home/ubuntu/.hermes/profiles/sef/.env
TARA_SON
}

#: MOTORUN KENDİ SIR DEPOSU. `.env` DEĞİL, JSON — `^AD=` deseni buraya KÖRDÜR ve o körlük tam
#: "rotasyon bu adı yazıyor" sanısını üretir (kalıcı kayıt 2026-09-06: Telegram/Alpaca/FMP
#: kimlikleri `.env`de değil BURADA yaşar). Kopya tablosundaki tek `api` satırı (NOUS_API_KEY)
#: bu depoya yazar; depoda duran BAŞKA bir döndürülen ad, rotasyonun yazmadığı bir kopyadır.
#: TANIM YUKARIDA, çünkü artık YALNIZ envanterin değil YEDEĞİN ve NEGATİF KONTROLÜN de girdisi.
#: KAPSAM BEYANI: bu depo `_aranan_adlar` listesiyle taranır, `.env`lerin sır-adı SÖZLÜĞÜYLE
#: DEĞİL — JSON'un anahtar uzayı `.env` alan uzayından ayrıdır ve buradaki BAŞKA sırlar (Alpaca,
#: FMP, Telegram) bu betiğin döndürdüğü sırlar değildir. Yani depoda tablonun hiç duymadığı bir
#: ADLA duran bir kopya bu taramaya GÖRÜNMEZ; sözlüğü buraya da bağlamak ayrı bir ölçüm işidir.
SECRETS_JSON="/opt/meridian/state/secrets.json"

#: `_disk_yolu <tür> <yol>` → kopyanın DİSKTEKİ karşılığı; karşılığı olmayan türde 1 döner.
#: `api` satırı bir YAZMA KANALIDIR ("dosya değil, motorun kendi ucu") ama yazdığı yer bir
#: DOSYADIR: `api.py::api_set_secret` → `secrets_mod.set` → `state/secrets.json`. Bu ayrımın
#: unutulması BLOKLAYICI bir körlük üretmişti: yedek ve negatif kontrol `dosya|env|url` süzgeciyle
#: `api` satırını atlıyor, yani motorun sır zincirindeki ÜÇÜNCÜ basamak (`_fetch`: credential →
#: ortam → `state/secrets.json`) rotasyon penceresinde DOKUNULMADAN kalıyordu (inceleme B1).
#: `sql` satırının disk karşılığı YOKTUR (Postgres rol tablosu) ve öyle kalır.
_disk_yolu() {
  case "$1" in
    dosya|env|url) printf '%s\n' "$2" ;;
    api)           printf '%s\n' "$SECRETS_JSON" ;;
    *)             return 1 ;;
  esac
}

# =================================================================================================
# ÇALIŞMA DİZİNİ + PYTHON YARDIMCISI
# =================================================================================================
# Satır değiştirme, tırnak koruma, izin koruma ve ATOMİK yazım kabuktan YAPILMAZ: `sed -i` yeni bir
# dosya yaratıp yerine koyar (mod/sahip kaybolur), tırnak biçimini görmez ve değeri argv'ye sokar.
# Yardımcı değeri YALNIZ dosyadan okur; hiçbir sır argümana girmez.
_islik_kur() {
  # ŞABLON AÇIK VERİLİR — iki sebeple. (1) Adı `sir-rot.` olur: temizlik başarısız kalırsa
  # operatör diskte kalan sır dizinini ADIYLA bulur (`_temizle` yolu zaten basar). (2) `mktemp -d`
  # ŞABLONSUZ çağrıldığında TMPDIR'i onurlandırmaz — macOS'ta ölçüldü 2026-09-08: çıktı Darwin'in
  # kullanıcı-başı dizinine düşüyor. Bu bir taşınabilirlik ayrıntısı değil, bir ÇİVİ sorunudur:
  # çalışma dizini nerede doğduğu bilinmeyen bir yere düşerse "silindi mi" çivisi hiçbir şey
  # ölçmez ve sessizce yeşil kalır (J8'in ilk turdaki hâli).
  ISLIK="$(mktemp -d "${TMPDIR:-/tmp}/sir-rot.XXXXXXXX")"
  chmod 700 "$ISLIK"
  # `_temizle` HİÇBİR ŞEY YUTMAZ (bkz. şerhi): silinemeyen bir sır dizini BAĞIRIR ve yolunu
  # basar. Trap'in tek sessiz yanı ÇIKIŞ KODUDUR — `_temizle` `return 0` ile biter, çünkü
  # koşumun hükmü rotasyonun hükmüdür; temizlik başarısızlığı onu 0'dan 1'e çeviremez.
  # (Bu şerh 2026-09-08'de koda uyduruldu: K9 düzeltmesinden sonra "bilerek yutuluyor" diyen
  # eski metin kodu ARTIK ANLATMIYORDU — işaretli bir gerekçenin koddan ayrışması ileri
  # düzeltmelerde kopyalanır ve kabukta hiçbir çivi bunu yakalamaz: `codelaw` yalnız `*.py` tarar.)
  trap '_cikis' EXIT
  cat > "$ISLIK/yardimci.py" <<'PY_SON'
"""sir_rotasyon.sh'in dosya yazma/okuma yardımcısı — DEĞER YALNIZ DOSYADAN OKUNUR.

Hiçbir işlem sır değerini stdout'a, stderr'e ya da bir argümana koymaz; basılan tek şey
KARAR'dır (EŞİT/AYRI/VAR/YOK). Bütün yazımlar aynı dizinde geçici dosya + `os.replace` ile
ATOMİKTİR: yarım yazılmış bir credential dosyası birimi açılmaz hâle getirir.
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from urllib.parse import quote, unquote, urlsplit, urlunsplit

ONEKLER = {"-": "", "Bearer": "Bearer "}


def _onek(ad: str) -> str:
    if ad not in ONEKLER:
        sys.exit(f"tanınmayan önek: {ad} (tanınanlar: {sorted(ONEKLER)})")
    return ONEKLER[ad]


def _oku(yol: str) -> str:
    with open(yol, encoding="utf-8") as fh:
        return fh.read()


def _coz(deger: str | None) -> str:
    """DSN alanının YÜZDE-ÇÖZÜMÜ. `urlsplit(...).password` çözMEZ — ölçüldü 2026-09-08:
    `urlsplit("postgresql://u:a%2Bb@h/d").password` → `'a%2Bb'`; oysa YAZAN taraf (`yaz-url`)
    `quote(..., safe='')` ile KODLAR. İki uç ayrışırsa `pgpass` parolayı KODLU yazar, libpq
    yanlış parolayı dener ve `--db`nin negatif kontrolü "eski parola FATAL" der — ölçtüğü şey
    `ALTER ROLE`un etkisi DEĞİL, betiğin kendi kodlama hatasıdır. Betiğin bütün tezinin ("kanıt
    anahtara bağlı mı") kapatmak için var olduğu sınıf. ÜRETİLEN parolanın alfabesinde
    (`[A-Za-z0-9_-]`) `quote` birim işlemdir, yani arıza YALNIZ elle konmuş ESKİ parolada
    görünür — tam da negatif kontrolün kullandığı değerde (inceleme B2, 2026-09-08).
    ÇÖZÜLEN ALAN = KODLANAN ALAN: `yaz-url` yalnız kullanıcı ve parolayı kodlar, yol/query'yi
    OLDUĞU GİBİ taşır; burada da yalnız o ikisi çözülür (simetri, tek-kaynak)."""
    return unquote(deger or "")


def _pgpass_alan(deger: str) -> str:
    """`.pgpass` alanı: ters bölü ve `:` KAÇIŞLI olmalı (libpq `PasswordFromFile`). Kaçışsız bir
    `:` alanı ikiye böler ve libpq yanlış parolayı dener — `_coz` ile aynı sınıf: ölçüm kendi
    biçimlendirme hatasını ölçer. Üretilen alfabede ikisi de yoktur; ESKİ parolada olabilir."""
    return deger.replace("\\", "\\\\").replace(":", "\\:")


def _deger_dosyadan(yol: str) -> str:
    """Değer dosyası: TEK satır, BAŞTAKİ VE SONDAKİ BOŞLUKLAR kırpılır. Boş/yalnız-boşluk ARIZADIR.

    İlk biçim yalnız `\r\n` kırpıyordu. Panodan yapıştırılan bir anahtarın sonundaki tek boşluk
    12 kopyaya AYNEN yazılır, upstream reddeder ve rotasyon kanıt aşamasında düşer — yani
    "yanlış anahtar" ile "doğru anahtar + bir boşluk" AYNI belirtiyi verir ve teşhis yanılır.
    Kırpma bir kolaylık değil ÖLÇÜMÜN ÖN ŞARTIDIR. (Operatör yolunda `read -rs` zaten IFS
    kırpması yapar; bu kapı değer dosyasının ÖTEKİ kaynaklarını da kapsar.)"""
    d = _oku(yol).strip()
    if not d.strip():
        sys.exit("değer dosyası BOŞ — yazım yapılmadı")
    return d


def _atomik_yaz(hedef: str, icerik: str, mod: str, sahip: str) -> None:
    """Mod/sahip: `koru` ise hedefin MEVCUTU okunur (os.stat), yoksa argümandan alınır."""
    d = os.path.dirname(hedef) or "."
    st = os.stat(hedef) if os.path.exists(hedef) else None
    fd, gecici = tempfile.mkstemp(dir=d, prefix=".sir-rot-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(icerik)
        if mod == "koru":
            if st is None:
                sys.exit(f"mod=koru ama dosya YOK: {hedef}")
            os.chmod(gecici, st.st_mode & 0o7777)
        else:
            os.chmod(gecici, int(mod, 8))
        if sahip == "koru":
            if st is None:
                sys.exit(f"sahip=koru ama dosya YOK: {hedef}")
            uid, gid = st.st_uid, st.st_gid
        elif sahip == "-":
            uid = gid = -1
        else:
            import grp
            import pwd
            k, _, g = sahip.partition(":")
            try:
                uid, gid = pwd.getpwnam(k).pw_uid, grp.getgrnam(g).gr_gid
            except KeyError:
                # Yasa 4 — sessiz-yutma: adı olmayan kullanıcı/grup YALNIZ çivi makinesinde olur
                # (macOS'ta `root` grubu YOKTUR, karşılığı `wheel`). A1'de `root:root` vardır ve
                # buraya hiç düşülmez; düşülürse sahiplik DEĞİŞMEZ, dosya ZATEN test kökündedir.
                uid = gid = -1
        if uid != -1:
            try:
                os.chown(gecici, uid, gid)
            except PermissionError:
                # Yasa 4 — sessiz-yutma: root DEĞİLKEN (yalnız v447 çivisi) chown yapılamaz;
                # üretimde betik sudo altında koşar ve buraya hiç düşmez. Sahiplik korunamadıysa
                # dosya ZATEN test kökündedir ve canlı bir birimi etkilemez.
                pass
        os.replace(gecici, hedef)
        gecici = ""
    finally:
        if gecici and os.path.exists(gecici):
            os.unlink(gecici)


class AlanArizasi(Exception):
    """`^<alan>=` satırı 0 ya da >1 kez var. AYRI BİR SINIFTIR, `OSError` DEĞİL: envanter iki
    dünyayı ayırt edebilsin diye. İlk tur `var`/`esit` işlemleri `SystemExit`i de yutuyordu ve
    çift satırlı bir dosya "YOK"/"OKUNAMADI" diye raporlanıyordu — yani envanterin GÖREVİ olan
    ayrışma, envanterin körlüğü yüzünden 'dosya yok' gibi okunuyordu."""

    def __init__(self, alan: str, adet: int) -> None:
        super().__init__(f"'{alan}=' satırı {adet} kez bulundu (tam 1 olmalı)")
        self.alan, self.adet = alan, adet


def _env_satiri(ham: str, alan: str) -> int:
    """`^<alan>=` satırının İNDEKSİ. 0 ya da >1 eşleşme bir ARIZADIR: sıfırsa yazım hedefsizdir,
    birden çoksa systemd/docker SONUNCUyu okur, operatör İLKİNİ düzenler ve iki değer sessizce
    ayrışır. Bu yüzden burada durulur — `sir_credential_gecis.sh`in `grep -v` deseni bu hâli
    görmüyordu."""
    satirlar = ham.splitlines(keepends=True)
    desen = re.compile(r"^" + re.escape(alan) + r"=")
    bulunan = [i for i, s in enumerate(satirlar) if desen.match(s)]
    if len(bulunan) != 1:
        raise AlanArizasi(alan, len(bulunan))
    return bulunan[0]


def _env_satiri_yazim(ham: str, alan: str) -> int:
    """Yazım yolunda arıza DURDURUR (envanterde ise raporlanır — iki farklı doğru cevap)."""
    try:
        return _env_satiri(ham, alan)
    except AlanArizasi as ariza:
        sys.exit(f"{ariza} — yazım YAPILMADI")


def _tirnak_ve_son(sag: str) -> tuple[str, str]:
    son = sag[len(sag.rstrip("\r\n")):]
    govde = sag.rstrip("\r\n")
    tirnak = govde[0] if len(govde) >= 2 and govde[0] == govde[-1] and govde[0] in "\"'" else ""
    return tirnak, son


def _cikar(tur: str, hedef: str, alan: str, onek: str) -> str:
    """Bir kopyanın ETKİN sır değeri (önek ve tırnak soyulmuş). Yalnız karşılaştırma/kanıt için."""
    p = _onek(onek)
    if tur == "dosya":
        ham = _oku(hedef).strip("\r\n")
    elif tur == "env":
        satirlar = _oku(hedef).splitlines()
        idx = _env_satiri(_oku(hedef), alan)
        govde = satirlar[idx].split("=", 1)[1]
        tirnak, _ = _tirnak_ve_son(govde)
        ham = govde.strip("\r\n")
        if tirnak:
            ham = ham[1:-1]
    elif tur == "url":
        ham = _coz(urlsplit(_oku(hedef).strip("\r\n")).password)
    else:
        sys.exit(f"okunamayan tür: {tur}")
    return ham[len(p):] if p and ham.startswith(p) else ham


def main(argv: list[str]) -> None:
    op = argv[1]
    if op == "yaz-dosya":            # <hedef> <deger> <mod> <sahip> <onek>
        hedef, dgr, mod, sahip, onek = argv[2:7]
        _atomik_yaz(hedef, _onek(onek) + _deger_dosyadan(dgr) + "\n", mod, sahip)
    elif op == "yaz-env":            # <hedef> <alan> <deger> <mod> <sahip> <onek>
        hedef, alan, dgr, mod, sahip, onek = argv[2:8]
        ham = _oku(hedef)
        satirlar = ham.splitlines(keepends=True)
        idx = _env_satiri_yazim(ham, alan)
        tirnak, son = _tirnak_ve_son(satirlar[idx].split("=", 1)[1])
        satirlar[idx] = f"{alan}={tirnak}{_onek(onek)}{_deger_dosyadan(dgr)}{tirnak}{son}"
        _atomik_yaz(hedef, "".join(satirlar), mod, sahip)
    elif op == "yaz-url":            # <hedef> <deger> <mod> <sahip>
        hedef, dgr, mod, sahip = argv[2:6]
        p = urlsplit(_oku(hedef).strip("\r\n"))
        if not p.username:
            sys.exit(f"DSN'de kullanıcı yok: {hedef} — parola değiştirilemez")
        yer = p.hostname or ""
        if p.port:
            yer += f":{p.port}"
        netloc = f"{quote(p.username, safe='')}:{quote(_deger_dosyadan(dgr), safe='')}@{yer}"
        _atomik_yaz(hedef, urlunsplit((p.scheme, netloc, p.path, p.query, p.fragment)) + "\n",
                    mod, sahip)
    elif op == "cikar":              # <tur> <hedef> <alan> <onek> <cikti>
        tur, hedef, alan, onek, cikti = argv[2:7]
        _atomik_yaz(cikti, _cikar(tur, hedef, alan, onek) + "\n", "0600", "-")
    elif op == "esit":               # <tur1> <h1> <a1> <o1> <tur2> <h2> <a2> <o2>
        try:
            a = _cikar(*argv[2:6])
            b = _cikar(*argv[6:10])
        except AlanArizasi as ariza:
            # ÇİFT SATIR "OKUNAMADI" DEĞİLDİR: biri dosyanın yokluğu, öteki envanterin tam da
            # aramaya geldiği ayrışma hâli. İkisini aynı kelimeye toplamak bulguyu siler.
            print(f"ÇİFT SATIR ({ariza.adet})" if ariza.adet > 1 else "ALAN YOK")
            return
        except OSError:
            print("OKUNAMADI")
            return
        print("EŞİT" if a == b and a else "AYRI")
    elif op == "json-govde":         # <cikti> <alan> <deger dosyasi> — JSON gövde, KAÇIŞLI
        # Gövde `printf '{"value": "' + değer + '"}'` ile kurulamaz: değeri OPERATÖR yapıştırır
        # (`--openrouter`) ve içindeki bir çift tırnak ya da ters bölü BOZUK JSON üretir →
        # motor 400 → `die "motor API yazımı başarısız (HTTP 400)"`. Sessiz değil ama teşhisi
        # YANILTICI: hata anahtarda değil, gövdeyi kuran kodda. `json.dumps` kaçışı yapar ve
        # değer yine YALNIZ dosyadan okunur (argv'ye girmez).
        cikti, alan, dgr = argv[2:5]
        _atomik_yaz(cikti, json.dumps({alan: _deger_dosyadan(dgr)}, ensure_ascii=False) + "\n",
                    "0600", "-")
    elif op == "kanit-cfg":  # <cikti> <url> <baslik-adi> <baslik-oneki> <deger> <govde> [ek] [yontem]
        cikti, url, baslik, b_onek, dgr, govde = argv[2:8]
        ek = argv[8] if len(argv) > 8 else "-"
        yontem = argv[9] if len(argv) > 9 else "-"
        satirlar = ["silent\n", f'url = "{url}"\n', f'output = "{govde}"\n',
                    'write-out = "%{http_code}"\n']
        if yontem != "-":
            satirlar.append(f'request = "{yontem}"\n')      # curl `-X`: cfg dosyasındaki karşılığı
        if baslik != "-":
            # `Authorization: Bearer <deger>` iki parçadır: başlık ADI ve değerin ÖNEKİ. Öneki
            # başlık adına yapıştırmak `authorization-bearer:` gibi var olmayan bir başlık üretirdi.
            satirlar.append(f'header = "{baslik}: {_onek(b_onek)}{_deger_dosyadan(dgr)}"\n')
        if ek != "-":
            satirlar.append('header = "content-type: application/json"\n')
            satirlar.append(f'data-binary = "@{ek}"\n')
        _atomik_yaz(cikti, "".join(satirlar), "0600", "-")
    elif op == "pgpass":             # <cikti> <url-dosyasi>
        cikti, kaynak = argv[2:4]
        p = urlsplit(_oku(kaynak).strip("\r\n"))
        _atomik_yaz(cikti, f"{p.hostname}:{p.port or 5432}:{p.path.lstrip('/')}:"
                           f"{_pgpass_alan(_coz(p.username))}:"
                           f"{_pgpass_alan(_coz(p.password))}\n", "0600", "-")
    elif op == "sql-uret":           # <cikti> <rol> <deger>
        cikti, rol, dgr = argv[2:5]
        d = _deger_dosyadan(dgr)
        if not re.fullmatch(r"[A-Za-z0-9_-]+", d):
            sys.exit("parola SQL literaline uygun değil (yalnız [A-Za-z0-9_-]) — yazım YAPILMADI")
        _atomik_yaz(cikti, f"ALTER ROLE {rol} PASSWORD '{d}';\n", "0600", "-")
    elif op == "var":                # <tur> <hedef> <alan>
        tur, hedef, alan = argv[2:5]
        try:
            print("VAR" if _cikar(tur, hedef, alan, "-") else "BOŞ")
        except AlanArizasi as ariza:
            print(f"ÇİFT SATIR ({ariza.adet})" if ariza.adet > 1 else "ALAN YOK")
        except OSError:
            print("YOK")
    elif op == "bosalt":             # <hedef> <mod> <sahip> — negatif kontrolün BOŞ değeri
        # `yaz-dosya` boş değeri REDDEDER (`_deger_dosyadan`) ve haklıdır: boş bir credential
        # 2026-09-07'de bir birimi sessizce yetkisiz bıraktı. Ama NOUS'un negatif kontrolü tam da
        # BOŞLUĞU ölçer (bkz. `_negatif_kontrol` şerhi) — o yüzden AYRI, ADI ÜSTÜNDE bir işlem:
        # kaza eseri çağrılamaz, mod/sahip yine korunur, geri alma trap'e bağlıdır.
        hedef, mod, sahip = argv[2:5]
        _atomik_yaz(hedef, "", mod, sahip)
    elif op == "dsn-uc":             # <dsn dosyasi> → "<host> <port> <user> <db>" (PAROLA YOK)
        # Kanıt bağlantısı DSN'den türetilir; bu satır o türetmenin TEK yeridir. Parola BASILMAZ
        # ve basılamaz: buradan çıkan dört alan argv'ye girer, parola ise yalnız PGPASSFILE'a.
        p = urlsplit(_oku(argv[2]).strip("\r\n"))
        if not (p.hostname and p.username and p.path.lstrip("/")):
            sys.exit(f"DSN eksik (host/user/db): {argv[2]}")
        # Kullanıcı adı `pgpass` ile AYNI çözümü görür: ikisi ayrışırsa `psql -U <kodlu>` ile
        # `pgpass`teki <çözülmüş> eşleşmez ve libpq parolayı SESSİZCE bulamaz.
        print(f"{p.hostname} {p.port or 5432} {_coz(p.username)} {p.path.lstrip('/')}")
    elif op == "json-ad-var":        # <hedef> <ad> → JSON'un ÜST DÜZEY anahtarları arasında mı
        # Motorun kendi sır deposu bir `.env` değil bir JSON'dur; `^AD=` deseni onu GÖREMEZ.
        # Yalnız ADLAR okunur — değer ne basılır ne de karşılaştırılır.
        hedef, ad = argv[2:4]
        try:
            veri = json.loads(_oku(hedef))
        except (OSError, ValueError):
            print("OKUNAMADI")
            return
        print("VAR" if isinstance(veri, dict) and ad in veri else "YOK")
    elif op == "alanlar":            # <hedef> → dosyadaki `^AD=` ALAN ADLARI (DEĞER BASILMAZ)
        # Beyan dışı taramanın DÖRDÜNCÜ kaynağı. Tablodan türeyen ad listesi yalnız BİLİNEN adları
        # görür; dosyanın KENDİ alan adlarını okumak, tablonun hiç duymadığı bir kopyayı da
        # görünür kılar (2026-09-08: hafıza failover üyeleri tam bu körlükte yaşıyordu).
        # `=` işaretinin YALNIZ SOLU basılır; sağ taraf hiçbir çıktıya girmez.
        try:
            ham = _oku(argv[2])
        except OSError:
            # sessiz-yutma: dosya YOKLUĞU burada bir bulgu DEĞİLDİR — çağıran (`_beyan_disi_tara`)
            # varlığı ZATEN `test -f` ile ölçtü ve yokluğu ORADA beyan eder. Boş liste dönmek
            # "taranacak alan yok" demektir, bir hatayı gizlemek değil.
            return
        gorulen = set()
        for satir in ham.splitlines():
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=", satir)
            if m and m.group(1) not in gorulen:
                gorulen.add(m.group(1))
                print(m.group(1))
    elif op == "alan-var":           # <hedef> <alan>  → dosyada `^alan=` var mı (bool)
        hedef, alan = argv[2:4]
        try:
            ham = _oku(hedef)
        except OSError:
            print("YOK")
            return
        print("VAR" if re.search(r"^" + re.escape(alan) + r"=", ham, flags=re.M) else "YOK")
    else:
        sys.exit(f"bilinmeyen işlem: {op}")


if __name__ == "__main__":
    main(sys.argv)
PY_SON
  chmod 600 "$ISLIK/yardimci.py"
}

# Çalışma dizini SIR TAŞIR (yeni değer, eski değer, pgpass, curl cfg). Silinememesi bir ARIZADIR
# ve BAĞIRIR: ilk turda buradaki `2>/dev/null || true` kazancı (ikinci trap ateşinde gürültüsüz
# çıkış) ölçülmüş, BEDELİ (0700 bir sır dizininin diskte kalması) ölçülmemişti — bedel yasasının
# tam olarak yasakladığı hâl. Ateşin ikincisi artık `-e` kapısıyla ayrılıyor, hata YUTULMUYOR.
# Trap içinden çıkış kodu DEĞİŞTİRİLMEZ (`return 0`): koşumun hükmü rotasyonun hükmüdür.
_temizle() {
  [ -n "$ISLIK" ] || return 0
  [ -e "$ISLIK" ] || return 0
  rm -rf "$ISLIK" || echo "!! ÇALIŞMA DİZİNİ SİLİNEMEDİ: $ISLIK
     Bu dizin sır taşır (0700). ELLE sil: sudo rm -rf $ISLIK" >&2
  return 0
}

# GERİ ALMA REÇETESİ HER YOLDA BASILIR — başarıda DA arızada DA. İlk biçimde reçete her alt
# komutun SON satırıydı, yani YALNIZ başarıda basılıyordu ve tam da en çok gerektiği hâlde
# susuyordu: taze anahtar kopyalara YAZILDIKTAN sonra kanıt aşamasında durulursa (yapıştırmada
# bir boşluk → upstream RET → çıkış 2) ekranda geri alma yolu YOKTU. Yedek dizininin YOLU daha
# önce basılmıştır, ama "yol basıldı" ile "ne yapacağı yazıldı" AYNI ŞEY DEĞİLDİR.
# `$YEDEK` boşken (kuru koşum · `--envanter` · yedek alınmadan düşen koşum) HİÇBİR ŞEY basılmaz:
# olmayan bir yedeği göstermek, olmayan bir güvence vermek olurdu.
_geri_alma_recetesi() {
  [ -n "$YEDEK" ] || return 0
  local birimler
  # sessiz-yutma: `_birimler` bilinmeyen bir alt komutta `die` eder ve o hata METNİ burada hükme
  # GİRMEZ — burası çıkış YOLUDUR, hüküm çoktan verilmiştir ve reçetenin susması, hükümden daha
  # pahalıya mal olurdu. Yutulan tek şey stderr metnidir; ÖLÇÜLEMEDİ hâli sessiz DEĞİL, görünür
  # bir dizgeyle beyan edilir (aşağıdaki `(birim listesi ölçülemedi)`).
  birimler="$(_birimler "$ALT" 2>/dev/null || echo '(birim listesi ölçülemedi)')"
  echo ">> GERİ ALMA (bu koşum YEDEK aldı — başarıda da arızada da geçerli):
     sudo cp -p $YEDEK/<yol> /<yol>   (yedek ağacı üretim yollarını AYNEN taşır)
     sonra yeniden başlat: $birimler" >&2
  return 0
}

# ÇIKIŞ YOLU TEK FONKSİYONDUR. `trap 'birinci; ikinci' EXIT` içinde `birinci` `exit` ederse
# `ikinci` HİÇ KOŞMAZ (bash EXIT-trap semantiği, ölçüldü 2026-09-08) — iki iş yan yana yazıldığı
# an, ikincisi birincinin arıza yoluna REHİN olur.
_cikis() {
  _geri_alma_recetesi
  _temizle
}

# `sudo python3` — yardımcı root olarak koşar (0400 credential dosyalarını okur/yazar).
py() { sudo python3 "$ISLIK/yardimci.py" "$@"; }

# `_curl_kod <cfg>` → ÜÇ HANELİ HTTP kodu; ulaşılamama `000`.
# İlk tur her çağrı yerinde `curl -K "$cfg" || echo 000` yazıyordu ve bu, operatörün canlıda
# GÖRECEĞİ metni bozuyordu: gerçek curl bağlanamasa BİLE `-w '%{http_code}'` çıktısını (`000`)
# basar VE 7 ile düşer, yani `|| echo 000` İKİNCİ bir `000` ekler. Yerel ölçüm 2026-09-08
# (gerçek curl, kapalı port): çıktı `000000`. Dallanma bozulmuyordu (`"000000" != "200"`) ama
# çivinin pinlediği dizge (`OLCULEMEDI(http=000)`) canlıda HİÇ görülmeyecekti — şim ile gerçeğin
# ayrışması (inceleme B3). Normalize: rakam dışını at, SON ÜÇ haneyi al, boşsa `000`.
_curl_kod() {
  local ham
  ham="$(curl -K "$1" 2>/dev/null || true)"   # sessiz-yutma: curl'ün ÇIKIŞ KODU burada hüküm
  # DEĞİLDİR — hüküm HTTP kodudur ve "ulaşılamadı" onun `000` değeriyle ifade edilir; çağıran
  # `case`/`[ = 200 ]` ile ayırır. Çıkış kodunu hükme katmak aynı bilgiyi iki kez saymaktır.
  ham="$(printf '%s' "$ham" | tr -dc '0-9')"
  ham="${ham: -3}"
  printf '%s\n' "${ham:-000}"
}

# =================================================================================================
# YEDEK
# =================================================================================================
# Ad SANİYE + alt komut taşır: aynı sırrı gün içinde iki kez döndürmek ilk yedeği EZMEZ. Dizin
# 0700 root: yedek de sır taşır ve bir yedek dosyası, kaynağından daha gevşek izinliyse rotasyonun
# kazandığını yedek geri verir.
_yedek_al() {
  local alt="$1" yol hedef aday
  # SIRA: aday → YARAT → ata. `YEDEK` globaldir ve `_geri_alma_recetesi`nin TEK kapısıdır
  # (`[ -n "$YEDEK" ]`), yani atama "yedek ALINDI" beyanıdır. Atamayı `install -d`den ÖNCE
  # yapmak o beyanı yalana çevirirdi: dizin doğmadan (disk dolu · yetki · aynı saniyede ikinci
  # koşum) düşen bir koşumda EXIT trap ">> GERİ ALMA (bu koşum YEDEK aldı…)" basar ve operatör
  # VAR OLMAYAN bir dizinden geri koymaya çalışır — reçetenin kendi şerhinin yasakladığı hâl.
  # Ölçüldü (inceleme D7/Y2, 2026-09-08): `install` şimi düşürüldü → dizin HİÇ doğmadı, reçete
  # YİNE basıldı, çıkış 1. Çivi: `test_P14`.
  aday="$KOK/root/sir-yedek-$(date -u +%Y%m%dT%H%M%SZ)-$alt"
  [ ! -e "$aday" ] || die "yedek dizini ZATEN VAR: $aday (aynı saniyede ikinci koşum?)"
  # `install -o <kullanıcı> -g <grup>` — İKİ AYRI BAYRAK. Tek `-o root:root` HATA verir
  # (ölçüldü 2026-09-07: `install: invalid user`), ve o hata `set -e` altında pencereyi yakar.
  sudo install -d -m 0700 -o root -g root "$aday"
  YEDEK="$aday"
  while read -r _alt _sir tur yol alan _mod _sahip _onek; do
    [ "$_alt" = "$alt" ] || continue
    # `api` satırının disk karşılığı da YEDEKLENİR (bkz. `_disk_yolu`): negatif kontrol o kopyayı
    # SİLER ve geri alma ancak yedekten yapılabilir. Yedek geri almanın ÖN KOŞULUDUR — motor ölü
    # ya da yetki reddediyorsa `POST` ile geri koymak da mümkün olmaz, dosya geri yazımı olur.
    yol="$(_disk_yolu "$tur" "$yol")" || continue
    hedef="$KOK$yol"
    if sudo test -e "$hedef"; then
      sudo install -d -m 0700 -o root -g root "$YEDEK$(dirname "$yol")"
      sudo cp -p "$hedef" "$YEDEK$yol"
      oldu "yedek: $yol"
    else
      echo "  · yedek ATLANDI (dosya yok): $yol"
    fi
  done < <(_kopyalar)
  echo "  yedek dizini: $YEDEK"
}

# `/root` altını ubuntu kabuğunda `ls $YEDEK_KOK/sir-yedek-*` ile listelemek ÇALIŞMAZ: glob
# ubuntu'nun kabuğunda, yani /root'u OKUYAMAYAN süreçte açılır ve boş döner (ölçüldü). Glob
# root'un kabuğunda açılmalı — `sudo sh -c '...'`.
_yedekleri_listele() {
  sudo sh -c "ls -1d '$KOK/root'/sir-yedek-* 2>/dev/null" || true   # sessiz-yutma: hiç yedek
  # yoksa `ls` 2 döner; "yedek yok" bir ARIZA DEĞİLDİR (ilk koşum) ve raporu kesmemeli.
}

# =================================================================================================
# DEĞER ÜRETİMİ
# =================================================================================================
# Uzunluk ÜRETİMDEN SONRA denetlenir: `openssl` bir konteyner/PATH kazasıyla boş çıktı verirse
# boş bir credential dosyası yazılır ve birim sessizce YETKİSİZ kalır (2026-09-07 vakası).
_uret() {
  local sinif="$1" hedef_uz cikti
  cikti="$ISLIK/yeni"
  case "$sinif" in
    b64) openssl rand -base64 36 | tr '+/' '-_' | tr -d '\r\n' > "$cikti"; hedef_uz=48 ;;
    hex) openssl rand -hex 32 | tr -d '\r\n' > "$cikti"; hedef_uz=64 ;;
    *) die "bilinmeyen değer sınıfı: $sinif" ;;
  esac
  printf '\n' >> "$cikti"
  chmod 600 "$cikti"
  local uz; uz="$(tr -d '\r\n' < "$cikti" | wc -c | tr -d ' ')"
  [ "$uz" = "$hedef_uz" ] || die "üretilen değer $uz karakter (beklenen $hedef_uz) — yazım YAPILMADI"
  grep -q '[^[:space:]]' "$cikti" || die "üretilen değer boş/boşluk — yazım YAPILMADI"
  oldu "yeni değer üretildi ($sinif, $hedef_uz karakter; DEĞER BASILMAZ)"
}

# Operatörden değer alır (ekrana yansımaz). Boş bırakılırsa o bacak ATLANIR — `--openrouter`
# iki anahtarı ayrı ayrı sorar ve tek anahtarı iki role de vermek operatörün seçimidir.
_oku_gizli() {
  local etiket="$1" cikti="$2" girilen=""
  printf '  %s (boş = bu bacağı atla): ' "$etiket" >&2
  read -rs girilen || true   # sessiz-yutma: stdin kapalıysa (çivi) boş değer = bacak atlanır
  echo >&2
  : > "$cikti"; chmod 600 "$cikti"
  if [ -n "$girilen" ]; then printf '%s\n' "$girilen" > "$cikti"; fi
  unset girilen
  # `2>/dev/null` KALKTI (D7 DÜŞÜK-9): dosya iki satır yukarıda `: > "$cikti"` ile ZATEN
  # yaratılıyor, yani yönlendirme ÖLÜ koddu — işaretsiz bir kaçış, gerçek bir kaçış gibi okunur.
  grep -q '[^[:space:]]' "$cikti"
}

# =================================================================================================
# YAZIM
# =================================================================================================
# Bir alt komutun TÜM kopyalarını (isteğe bağlı: yalnız verilen sır kimliğininkileri) yazar.
# `_yaz <alt> [yalnız-sır] [değer dosyası] [tür süzgeci]`. TÜR SÜZGECİ İKİ YERDE kullanılır:
#   (1) `bozuk` negatif kontrolü — `sql` (ALTER ROLE) GERİ ALINAMAZ bir kanaldır; bilerek bozuk
#       bir parolayı oraya yazmak "hiçbir kalıcı yazım yok" hükmünü kırardı. `api` kanalı da o
#       ölçümün dışında tutulur: bozuk bir değeri motorun deposuna YAZMAK yerine, boşluk ölçümü
#       o kopyayı SİLER ve yedekten geri koyar (`_api_sil` + `_negatif_geri_al`) — aynı sonuç,
#       yarım yazılmış bir depo riski olmadan.
#   (2) `--openrouter`in NOUS bacağı — önce YALNIZ `dosya` (credential kaynağı) yazılır ve kanıt
#       ölçülür; `api` kopyası ancak kanıttan SONRA yazılır (bkz. `openrouter`).
# Süzgeç boşken tüm türler yazılır.
# Hedef dizin YOKSA yaratılır, VARSA DOKUNULMAZ. İlk tur `install -d -m 0755` ile her koşumda
# modu DAYATIYORDU: 0700'e sıkılaştırılmış bir sır dizini (ölçülmemiş ama mümkün bir hâl) her
# rotasyonda sessizce 0755'e geriliyor, yani rotasyon güvenliği ARTIRIRKEN izni GEVŞETİYORDU —
# ve hiçbir çivi dizin modunu okumadığı için bedel görünmüyordu. Yaratma modu 0755'tir çünkü
# A1'de ölçülen hâl budur (2026-09-07: /etc/meridian ve /etc/hindsight/creds 0755 root:root;
# dosyaların kendisi 0400). Dizin YOKSA hangi modun DAYATILDIĞI basılır: sessiz bir varsayılan,
# operatörün göremediği bir karardır.
_dizin_hazirla() {
  local d="$1" yol="$2"
  if sudo test -d "$d"; then return 0; fi
  sudo install -d -m 0755 -o root -g root "$d"
  oldu "dizin YARATILDI: $(dirname "$yol") (0755 root:root — A1'de ölçülen hâl)"
}

_yaz() {
  local alt="$1" sadece_sir="${2:-}" dgr="${3:-$ISLIK/yeni}" tur_suzgeci="${4:-}"
  local _alt sir tur yol alan mod sahip onek hedef
  while read -r _alt sir tur yol alan mod sahip onek; do
    [ "$_alt" = "$alt" ] || continue
    [ -z "$sadece_sir" ] || [ "$sir" = "$sadece_sir" ] || continue
    if [ -n "$tur_suzgeci" ]; then case " $tur_suzgeci " in *" $tur "*) ;; *) continue ;; esac; fi
    hedef="$KOK$yol"
    case "$tur" in
      dosya) _dizin_hazirla "$(dirname "$hedef")" "$yol"
             # `koru` satırında ÖN-YARATMA YOK. İlk turda hedef `: | sudo tee` ile yaratılıyordu
             # ve bu, yardımcıdaki "mod=koru ama dosya YOK → dur" kapısını ÖLÜ KOD yapıyordu:
             # eksik bir `/opt/hindsight/.key` sessizce 0644 root olarak YENİDEN DOĞUYOR, yani
             # rotasyon korumaya çalıştığı izni kendi eliyle gevşetiyordu. Hedef yoksa MEVCUT
             # izin OKUNAMAZ; okunamayan izni uydurmak yerine durulur.
             case "$mod/$sahip" in
               *koru*) sudo test -e "$hedef" \
                         || die "mod/sahip=koru ama hedef YOK: $yol — mevcut izin okunamaz, yazım YAPILMADI" ;;
             esac
             # `mod`/`sahip` AÇIK olan satırlarda ön-yaratmaya GEREK de yok: `_atomik_yaz` dosyayı
             # hedef dizinde `mkstemp` + `chmod <mod>` + `os.replace` ile kendisi kurar, yani dosya
             # daha ilk anından itibaren doğru izinle var olur (0644'lük bir ara hâl hiç doğmaz).
             py yaz-dosya "$hedef" "$dgr" "$mod" "$sahip" "$onek"
             oldu "yazıldı: $yol (mod=$mod sahip=$sahip)" ;;
      env)   sudo test -f "$hedef" || die "hedef dosya YOK: $yol — yazım yapılamaz"
             py yaz-env "$hedef" "$alan" "$dgr" "$mod" "$sahip" "$onek"
             oldu "yazıldı: $yol ($alan=, tırnak biçimi korundu)" ;;
      url)   sudo test -f "$hedef" || die "hedef dosya YOK: $yol — yazım yapılamaz"
             py yaz-url "$hedef" "$dgr" "$mod" "$sahip"
             oldu "yazıldı: $yol (YALNIZ parola alanı; kullanıcı/host/port/db/query korundu)" ;;
      sql)   _sql_uygula "$yol" "$dgr" ;;
      api)   _api_yaz "$sir" "$yol" "$dgr" ;;
      *)     die "bilinmeyen kopya türü: $tur" ;;
    esac
  done < <(_kopyalar)
}

# Parola argv'ye GİRMEZ ve DOSYA YOLU postgres'e HİÇ VERİLMEZ.
#
# İlk tur `sudo chown postgres "$sql"` + `psql -f "$sql"` yazıyordu ve bu üretimde HİÇ koşamazdı:
# `$ISLIK` `mktemp -d` + `chmod 700` ile açılır ve SAHİBİ root'tur. Dosyanın sahibini postgres'e
# vermek yetmez — postgres o dosyaya ulaşmak için 0700 root dizinini TRAVERSE etmek zorundadır ve
# edemez (EACCES). `ON_ERROR_STOP` ile psql düşer, `die` ateşler ve `--db` bakım penceresinin
# ortasında durur. Çözüm dosyayı taşımak ya da izin gevşetmek DEĞİL, yolu hiç vermemektir:
# yönlendirmeyi ZATEN okuyabilen root kabuğu açar, postgres yalnız hazır bir fd görür (`-f -`).
# `chown` da böylece gereksizleşir — onunla birlikte gerekçeli `|| true` kaçışı da kalkar.
# `-q`: `ALTER ROLE` çıktısı zaten karar taşımaz, `>/dev/null` ile birlikte gürültü sıfırlanır.
_sql_uygula() {
  local rol="$1" dgr="$2" sql="$ISLIK/rol.sql"
  py sql-uret "$sql" "$rol" "$dgr"
  sudo -u postgres psql -v ON_ERROR_STOP=1 -q -f - < "$sql" >/dev/null \
    || die "ALTER ROLE başarısız — parola DEĞİŞMEDİ (SQL dosyası siliniyor)"
  sudo rm -f "$sql"
  sudo test ! -e "$sql" || die "SQL dosyası SİLİNEMEDİ: $sql"
  oldu "ALTER ROLE $rol uygulandı · SQL dosyası silindi (parola argv'ye girmedi)"
}

# Motorun kendi ucu: değer `curl -K` + `--data-binary @dosya` ile gider, argv'ye GİRMEZ.
# Gövde KAÇIŞLI kurulur (`py json-govde`): `--openrouter`de değeri OPERATÖR yapıştırır ve içindeki
# bir çift tırnak ya da ters bölü, elle kurulan gövdede BOZUK JSON üretirdi → motor 400 → teşhis
# "anahtar yazılamadı" derken hata gövdeyi kuran koddaydı (inceleme B7).
_api_yaz() {
  local ad="$1" uc="$2" dgr="$3" cfg="$ISLIK/api.cfg" govde="$ISLIK/api.json" yanit="$ISLIK/api.out" kod
  local tok="$ISLIK/tok"
  py cikar dosya "$KOK/etc/meridian/dash_token" - - "$tok"
  py json-govde "$govde" value "$dgr"
  py kanit-cfg "$cfg" "$API$uc" "x-meridian-token" "-" "$tok" "$yanit" "$govde"
  kod="$(_curl_kod "$cfg")"
  [ "$kod" = "200" ] || die "motor API yazımı başarısız (HTTP $kod): $uc ($ad)
     Rotasyon KANITLANDI ve credential kanalı yeni değeri taşıyor; başarısız olan YALNIZ motorun
     kendi deposundaki kopya. O depo \`secrets._fetch\`in ÜÇÜNCÜ basamağıdır (credential ilk), yani
     motor bugün doğru çalışır — ama depoda ESKİ değer kalır ve credential bir gün boşalırsa
     motor sessizce ona düşer. Elle eşitle: pano → sır girişi, ya da $uc."
  oldu "yazıldı: motor API $uc (değer gövde dosyasından, argv'ye girmedi)"
}

# Motorun sır deposundaki kopyayı SİLER (`DELETE <uc>`; `api.py::api_delete_secret`).
# NİYE VAR — BU TURUN BLOKLAYICISI. `secrets._fetch` sırayla credential → süreç ortamı →
# `state/secrets.json` okur ve meridian.service'te ortam basamağı ÖLÜDÜR (drop-in
# `51-dash-env-kaldir.conf` `EnvironmentFile=` listesini sıfırlar). NOUS'un negatif kontrolü
# credential'ı BOŞALTIR; depo kopyası dokunulmadan kalırsa motor ESKİ ama HÂLÂ GEÇERLİ anahtara
# düşer, `ping_brain` ok:true döner ve betik "bozuk/boş değerle de OK geldi" deyip ÇIKIŞ 2 verir:
# operatörün taze anahtarı HİÇ YAZILMAZ. Yani boşluk ölçümü, ölçmek istediği kanalı ölçmüyordu
# (inceleme B1; semptomu tur-1'in 11 numaralı bulgusuyla birebir aynı).
# GERİ ALMA yedekten DOSYA olarak yapılır (`_negatif_geri_al`), `POST` ile değil: geri alınacak an
# tam da motorun ölçülemez olduğu andır, ve o anda çalışan bir uca bağlı bir geri alma yoktur.
_api_sil() {
  local ad="$1" uc="$2" cfg="$ISLIK/api.cfg" yanit="$ISLIK/api.out" tok="$ISLIK/tok" kod
  py cikar dosya "$KOK/etc/meridian/dash_token" - - "$tok"
  py kanit-cfg "$cfg" "$API$uc" "x-meridian-token" "-" "$tok" "$yanit" "-" "DELETE"
  kod="$(_curl_kod "$cfg")"
  [ "$kod" = "200" ] || olcum_yok "motor sır deposu kopyası SİLİNEMEDİ (HTTP $kod): $uc ($ad).
     Negatif kontrol geri-düşüş kopyasını kaldıramadı; boş credential ölçümü o kopyayı ölçerdi,
     kanalı DEĞİL. Operatörün yeni anahtarı YAZILMADI (hiçbir kalıcı yazım yok)."
  oldu "silindi: motor API $uc ($ad — YALNIZ negatif kontrol süresince; yedekten geri alınır)"
}

# =================================================================================================
# YENİDEN BAŞLATMA + CREDENTIAL DENETİMİ
# =================================================================================================
# `_yeniden_baslat <alt> [birim…]` — birim kümesi VERİLMEZSE alt komutun tamamı. Verilebilir
# olması bir kolaylık değil KAPSAM sözleşmesidir: `--openrouter` iki anahtardan yalnız birini
# döndürebilir ve o turda ötekinin birimini yeniden başlatmak karşılıksız bir kesintidir.
_yeniden_baslat() {
  local alt="$1"; shift
  local birimler b
  if [ "$#" -gt 0 ]; then birimler="$*"; else birimler="$(_birimler "$alt")"; fi
  for b in $birimler; do
    adim "yeniden başlat: $b"
    sudo systemctl restart "$b" || die "$b yeniden başlamadı — journalctl -u $b -n 50"
  done
  # shellcheck disable=SC2086
  _kredensiyel_denetle "$alt" $birimler
  # shellcheck disable=SC2086
  _hazir_bekle $birimler
}

# =================================================================================================
# HAZIRLIK BEKLEME — "restart döndü" ile "birim dinliyor" AYNI ŞEY DEĞİLDİR
# =================================================================================================
# VAKA 2026-09-08 06:13Z (A1, `--openrouter`in İLK canlı koşumu): `_negatif_kontrol` üç birimi
# yeniden başlattı ve HEMEN ölçtü (`_nous_hali` → `/api/secrets/test/nous`). meridian henüz
# dinlemiyordu → curl `000` → `OLCULEMEDI(http=000)` → "ÖLÇÜM ARIZASI" → geri alma. Dosyalar
# yedekle aynı kaldı (zarar YOK) ama ROTASYON YAPILAMADI: pencere ölçüm arızasıyla kapandı.
# Betik doğru davrandı (uydurma yasağı: ulaşılamamayı "reddedildi" saymadı) — EKSİK olan tek şey
# ZAMANDI. v447 bunu göremedi çünkü `systemctl` şimi restart'ı ANINDA hazır sayıyordu; yani
# çivilerin kör olduğu kanal SAATTİ, mantık değil (§6: şim modellemiyorsa arıza ölçülemez).
#
# BEKLEME YOKLAMALIDIR AMA SINIRLIDIR. Tavan aşılırsa `olcum_yok`: betik "hazır" DEMEZ,
# ölçemediğini söyler ve çıkış 2 verir. Süre BASILIR — bir sonraki turda tavanın ölçüye uygun
# olup olmadığı tartışılabilsin diye (basılmayan bir sayı, ölçülmemiş bir sayıdır).
#
# UCU OLMAYAN BİRİM HAZIR SAYILMAZ, BEKLENMEZ: `hindsight-cp.service` bir sağlık ucu sunmuyor
# (2026-09-08 itibarıyla ölçülmedi) ve satır bunu SÖYLER. Sessizce "hazır" saymak, ölçülmemiş
# bir şeyi ölçülmüş göstermek olurdu.
# `<uç> <kabul ölçütü> <200 GELMEDEN hazır sayılınca basılacak açıklama>` — üçü de birim başına ve
# TEK yerde. Kabul ölçütü uçtan ayrı bir tabloda yaşasaydı ikisi sessizce ayrışır, betik bir ucu
# yanlış ölçütle yoklardı (tek-kaynak yasası).
_hazir_uc() {
  case "$1" in
    meridian.service)      echo "$API/healthz http nabız bayat, API ayakta" ;;
    hindsight-api.service) echo "$HINDSIGHT/health 200 -" ;;
    apisix.service)        echo "$KAPI_KOK/healthz http meridian'a proxy, kapı ayakta" ;;
    *) return 1 ;;
  esac
}

# KABUL ÖLÇÜTÜ — iki ölçüt AYNI ŞEY DEĞİLDİR ve karıştırmanın bedeli canlıda ölçüldü
# (2026-09-08 07:2x-07:4xZ):
#   200  → yüzey gerçekten 200 demeli. hindsight-api `/health` KENDİ sürecidir: 200'ün başka bir
#          anlamı yoktur, gevşetmek "ayakta" ile "cevap veriyor"u karıştırmak olurdu.
#   http → HTTP cevabı YETER (kod ne olursa olsun `000` değilse süreç dinliyordur). meridian
#          `/healthz` NABZIN tazeliğini raporlar (`503` = `{"status":"stale"}`) — açılışta ağır
#          bar tazelemesi yapan SAĞLIKLI bir motor dakikalarca 503 döner, ama API ayaktadır ve
#          `/api/secrets/test/nous` aynı anda cevap verir. `apisix` `/healthz` aynı gövdeye
#          proxy'dir, aynı ölçüte tabidir.
# `000` iki ölçütte de hazır DEĞİLDİR: curl hiç bağlanamadıysa ortada bir yüzey yoktur.
_hazir_mi() {
  case "$1" in
    200)  [ "$2" = "200" ] ;;
    http) [ "$2" != "000" ] ;;
    *) die "bilinmeyen hazırlık kabul ölçütü: $1 (yalnız '200' ve 'http' tanımlı)" ;;
  esac
}

_kabul_metni() {
  case "$1" in
    200)  echo "HTTP 200" ;;
    http) echo "HERHANGİ bir HTTP cevabı (000 değil)" ;;
    *) die "bilinmeyen hazırlık kabul ölçütü: $1" ;;
  esac
}

# Birim başına TAVAN (bkz. başlıktaki ölçüm): hindsight-api'nin 200'ü ~60 s sonra gelir ve ortak
# 60 s tavanı sınırdaydı; ötekiler "HTTP cevabı" ölçütüyle saniyeler içinde geçer.
_hazir_tavan() {
  case "$1" in
    hindsight-api.service) echo "$HAZIR_TAVAN_S_hindsight_api" ;;
    *)                     echo "$HAZIR_BEKLE_TAVAN_S" ;;
  esac
}

# `_hazir_bekle <birim…>` — kümeyi ÇAĞIRAN verir (bkz. `_yeniden_baslat`): negatif kontrol yalnız
# ölçtüğü sırrın tüketicilerini bekler, alt komutun tamamını DEĞİL.
_hazir_bekle() {
  local b satir uc kabul aciklama tavan bas kod gecen
  for b in "$@"; do
    if ! satir="$(_hazir_uc "$b")"; then
      echo "  · hazırlık yoklaması YOK: $b (sağlık ucu tanımlı değil — beklenmedi, hazır SAYILMADI)"
      continue
    fi
    uc="${satir%% *}"; satir="${satir#* }"; kabul="${satir%% *}"; aciklama="${satir#* }"
    tavan="$(_hazir_tavan "$b")"
    bas="$(date +%s)"
    while :; do
      kod="$(_kod "-" "$uc" "-" "-")"
      if _hazir_mi "$kabul" "$kod"; then break; fi
      gecen=$(( $(date +%s) - bas ))
      if [ "$gecen" -ge "$tavan" ]; then
        olcum_yok "hazırlık bekleme aşıldı: $b $uc → HTTP $kod
     ($tavan s içinde $(_kabul_metni "$kabul") gelmedi.) Birim AYAKTA DEĞİL ya da yüzeye
     ulaşılamıyor; buradan sonra ölçmek 'ulaşılamadı'yı 'anahtar reddedildi' saymak olurdu."
      fi
      sleep "$HAZIR_BEKLE_ARALIK_S"
    done
    gecen=$(( $(date +%s) - bas ))
    # 200 GELMEDEN hazır sayıldıysa satır bunu SÖYLER: kabul ölçütü gevşek OLABİLİR, ölçümün
    # beyanı gevşek OLAMAZ. "hazır: meridian 7 s" ile "hazır: meridian 7 s (healthz 503 — nabız
    # bayat, API ayakta)" aynı cümle değildir ve operatör ikincisini görmek zorundadır.
    if [ "$kod" = "200" ]; then
      oldu "hazır: ${b%.service} $gecen s"
    else
      oldu "hazır: ${b%.service} $gecen s (${uc##*/} $kod — $aciklama)"
    fi
  done
}

# `/run/credentials/<birim>/<kimlik>` boyutu > 1 mi. Dizin YOKSA bu bir ölçüm arızasıdır, "sorun
# yok" değildir: birim LoadCredential ile açılmadıysa sır ortamdan geliyordur ve rotasyon başka
# bir kanalı ölçmüş olur.
# `_kredensiyel_denetle <alt> <yeniden başlatılan birim…>` — YALNIZ yeniden başlatılan birimler
# ölçülür. Başlatılmayan birimin `/run/credentials` içeriği bu turda DEĞİŞMEDİ; onu ölçüp "dolu"
# demek, başka bir turun ölçümünü bu tura yazmaktır.
_kredensiyel_denetle() {
  local alt="$1"; shift
  local _alt birim kimlik yol boyut
  while read -r _alt birim kimlik; do
    [ "$_alt" = "$alt" ] || continue
    case " $* " in *" $birim "*) ;; *) continue ;; esac
    yol="$KOK/run/credentials/$birim/$kimlik"
    sudo test -e "$yol" || olcum_yok "credential dosyası YOK: /run/credentials/$birim/$kimlik
     ($birim LoadCredential ile açılmadı — rotasyon başka bir kanalı ölçmüş olurdu)"
    # GNU (`-c %s`) / BSD (`-f %z`) geri düşüşü — ve İKİSİ DE düşebilir (eksik/kısıtlı `stat`).
    # `|| true` OLMADAN `set -e` koşumu ÇIKIŞ 1 ile keserdi ve tasarlanan `olcum_yok` (çıkış 2)
    # hiç koşmazdı: "ölçemedim" ile "arıza" AYNI HÜKÜM DEĞİLDİR ve bu betiğin bütün sözleşmesi
    # o ayrımdır.
    boyut="$(sudo stat -c %s "$yol" 2>/dev/null || sudo stat -f %z "$yol" 2>/dev/null || true)"
    # sessiz-yutma: iki biçimin HATA METNİ hükme girmez (her sistemde biri zaten düşer); hüküm
    # ÇIKTININ BOŞ olup olmamasıdır ve tam aşağıda ölçülür.
    [ -n "$boyut" ] || olcum_yok "credential BOYUTU ÖLÇÜLEMEDİ (stat'ın GNU ve BSD biçimlerinin
     İKİSİ de düştü): /run/credentials/$birim/$kimlik — dolu mu boş mu bilinmiyor ve 'dolu'
     saymak kanıt UYDURMAK olurdu."
    [ "${boyut:-0}" -gt 1 ] || olcum_yok "credential BOŞ (boyut $boyut): /run/credentials/$birim/$kimlik"
    oldu "credential dolu: /run/credentials/$birim/$kimlik ($boyut bayt)"
  done < <(_kredensiyeller)
}

# =================================================================================================
# KANIT
# =================================================================================================
# `_kod <deger-dosyasi> <url> <baslik-adi> [govde-dosyasi]` → HTTP kodu. Değer `-K` yapılandırma
# dosyasından okunur; `-H "apikey: $deger"` yazsaydık sır `ps` ile makinedeki HERKESE görünürdü.
_kod() {
  local dgr="$1" url="$2" baslik="$3" b_onek="${4:--}" govde="${5:--}"
  local cfg="$ISLIK/kanit.cfg" out="$ISLIK/kanit.out"
  # Gövde dosyası ÇAĞRIDAN ÖNCE silinir: curl hiç bağlanamazsa (kod 000) dosyaya dokunmaz ve
  # `_govde` BİR ÖNCEKİ çağrının gövdesini okur. O gövde `"ok": true` taşıyorsa ulaşılamayan bir
  # motor "anahtar geçerli" diye ölçülürdü — ölçüm arızasının en sinsi biçimi.
  rm -f "$out"
  py kanit-cfg "$cfg" "$url" "$baslik" "$b_onek" "$dgr" "$out" "$govde"
  _curl_kod "$cfg"
}

_govde() { cat "$ISLIK/kanit.out" 2>/dev/null || true; }   # sessiz-yutma: gövde dosyası yoksa
# kanıt zaten kod üzerinden düşer; burada boş dizge doğru cevaptır.

# İKİ HÜKÜM BİRDEN. `yeni` 200 VE `eski` 401 olmalı. Yalnız biri ölçülürse kanıt anahtara bağlı
# olduğunu GÖSTERMEZ: kilit kapalıysa ikisi de 200 döner ve "rotasyon başarılı" bir tiyatrodur.
_farksal() {
  local etiket="$1" yeni="$2" eski="$3" url="$4" baslik="$5" b_onek="$6"
  local bekle_yeni="$7" bekle_eski="$8" k_yeni k_eski
  k_yeni="$(_kod "$yeni" "$url" "$baslik" "$b_onek")"
  k_eski="$(_kod "$eski" "$url" "$baslik" "$b_onek")"
  [ "$k_yeni" = "$bekle_yeni" ] \
    || olcum_yok "$etiket: YENİ değerle HTTP $k_yeni (beklenen $bekle_yeni) — rotasyon doğrulanamadı"
  case " $bekle_eski " in
    *" $k_eski "*) ;;
    *) olcum_yok "$etiket: ESKİ değerle HTTP $k_eski (beklenen $bekle_eski).
     Kilit yürürlükte DEĞİL — 'yeni anahtar 200 döndü' hangi anahtarın geçerli olduğunu
     KANITLAMAZ. Yeni değer YAZILDI ve çalışıyor; kanıt ÖLÇÜLEMEDİ." ;;
  esac
  oldu "$etiket: yeni→$k_yeni · eski→$k_eski (kanıt anahtara BAĞLI)"
}

# Motorun KENDİ sürecinden ölçüm. `/healthz` yetmez (kimlik istemez, sır yanlışken de 200);
# `/api/secrets/test/nous` motorun içinden `hermes.ping_brain("nous")` çağırır. HTTP kodu da
# yetmez — uç anahtar yanlışken de 200 döner; hüküm GÖVDEDEKİ `ok` alanıdır.
#
# ÜÇ HÂL, İKİ DEĞİL. İlk tur `OK` ve `YOK` diye ikiye bölüyordu ve `YOK` iki AYRI dünyayı
# birleştiriyordu: "anahtar reddedildi" (ok:false) ile "yüzeye hiç ulaşılamadı" (motor ölü, token
# yanlış, cfg okunamadı → kod 000/401/5xx). Negatif kontrol tam da `YOK` beklediği için ölçüm
# ARIZASINI "kanıt anahtara bağlı" diye kabul ediyordu — kanıtın kendisini uyduran bir yol.
#   OK          → HTTP 200 + `ok:true`
#   RET         → HTTP 200 + `ok:false`  (motor konuştu, anahtar REDDEDİLDİ)
#   OLCULEMEDI  → kod 200 değil, ya da gövde yok/ayrıştırılamaz
_nous_hali() {
  local tok="$ISLIK/tok" kod
  py cikar dosya "$KOK/etc/meridian/dash_token" - - "$tok"
  kod="$(_kod "$tok" "$API/api/secrets/test/nous" "x-meridian-token" "-")"
  [ "$kod" = "200" ] || { echo "OLCULEMEDI(http=$kod)"; return 0; }
  case "$(_govde)" in
    *'"ok": true'*|*'"ok":true'*) echo OK ;;
    *'"ok": false'*|*'"ok":false'*) echo RET ;;
    *) echo "OLCULEMEDI(govde-yok)" ;;
  esac
}

# =================================================================================================
# ALT KOMUTLAR
# =================================================================================================
#: NEGATİF KONTROLLÜ ALT KOMUTLAR — restart ÇARPANININ TEK KAYNAĞI. Buradaki her ad için gerçek
#: koşumda her birim ÜÇ kez yeniden başlar (negatif kontrolün BOZMA turu + GERİ ALMA turu +
#: POZİTİF tur) ve her restart'ın ardından hazırlık beklenir; ötekilerde BİR kez. Liste bir
#: KOPYADIR (asıl gerçek `_negatif_kontrol` çağrı yerleridir) ve kopya kaçınılmaz olduğu için
#: AYRIŞMA ÇİVİSİYLE bağlıdır: `test_P15` betiğin kendi kaynağındaki çağrı yerlerini sayar.
_NK_ALT_KOMUTLARI="openrouter"

# Kaç kez yeniden başlayacağı KURU RAPORDA yazılır (bedel yasası, inceleme D7/Y4): birim başına
# tek bir "tavan: 300 s" satırı okuyan operatör "en fazla 300 s" diye anlar, oysa `--openrouter`
# penceresinde ölçülen gerçek 3 × 300 s'dir (PROBE3, 2026-09-08: apisix 3 · hindsight-api 3 ·
# meridian 3 restart). Kazanç (kısa satır) ölçülüp bedeli (gizlenen bekleme) ölçülmeyen hâl.
_restart_carpani() {
  case " $_NK_ALT_KOMUTLARI " in *" $1 "*) echo 3 ;; *) echo 1 ;; esac
}

_kuru_rapor() {
  local alt="$1" _alt sir tur yol alan _m _s onek satir uc kabul onceki="" carpan tavan
  echo "=== KURU KOŞUM: --$alt (HİÇBİR ŞEY YAZILMADI) ==="
  while read -r _alt sir tur yol alan _m _s onek; do
    [ "$_alt" = "$alt" ] || continue
    case "$tur" in
      env) echo "  yazılacak: $yol  ($alan=, önek=$onek)" ;;
      api) echo "  yazılacak: motor API $yol  ($sir)" ;;
      sql) echo "  yazılacak: ALTER ROLE $yol PASSWORD (SQL dosyası, koşumdan sonra silinir)" ;;
      *)   echo "  yazılacak: $yol  ($tur, $sir)" ;;
    esac
  done < <(_kopyalar)
  echo "  yeniden başlatılacak: $(_birimler "$alt")"
  # Hangi sırrın hangi birimi tetiklediği BURADA görünür — çünkü gerçek koşumda yeniden başlayan
  # küme alt komutun tamamı DEĞİL, YAZILAN sırların tüketicileridir (`--openrouter` iki anahtardan
  # yalnız birini döndürebilir; negatif kontrol zaten tek sırrın tüketicileriyle koşar).
  echo "  sır → tüketici birimler (gerçek koşumda YALNIZ yazılan sırrınki yeniden başlar):"
  while read -r _alt sir tur yol alan _m _s onek; do
    [ "$_alt" = "$alt" ] || continue
    [ "$sir" != "$onceki" ] || continue
    onceki="$sir"
    echo "    · $sir → $(_sir_birimleri "$sir")"
  done < <(_kopyalar)
  # BEDEL YASASI: bekleme bakım penceresine SÜRE ekler ve o süre kuru raporda BEYAN EDİLİR —
  # "hangi birimler yeniden başlayacak" sorusunun cevabı artık "hangi ÖLÇÜTLE ve ne kadar
  # bekleyebilir"i de içerir. Üç sütun da `_hazir_uc`/`_hazir_tavan`tan TÜRETİLİR: ikinci bir
  # yerde yazılsaydı kuru rapor gerçekte koşacak şeyi ANLATMAZDI.
  carpan="$(_restart_carpani "$alt")"
  echo "  hazırlık beklemesi (her uç $HAZIR_BEKLE_ARALIK_S s aralıkla yoklanır; aşımda ÖLÇÜLEMEDİ).
     BEDEL: bu alt komutta her birim $carpan kez yeniden başlar ve her restart'ın ardından
     hazırlık beklenir — satırdaki tavan BİR restart içindir, en kötü hâl $carpan katıdır:"
  for _alt in $(_birimler "$alt"); do
    if satir="$(_hazir_uc "$_alt")"; then
      uc="${satir%% *}"; satir="${satir#* }"; kabul="${satir%% *}"
      tavan="$(_hazir_tavan "$_alt")"
      echo "    · ${_alt%.service} → $uc  kabul: $(_kabul_metni "$kabul")  tavan: $tavan s × $carpan restart = en kötü $((tavan * carpan)) s"
    else
      echo "    · ${_alt%.service} → (sağlık ucu YOK, beklenmez)"
    fi
  done
  # ÖN KOŞUL BURADA DA YAZILIR, ÇÜNKÜ KURU KOŞUM OPERATÖRÜN İLK KOMUTUDUR. `meridian-tick-watchdog.timer`
  # 45 dk bayat nabızda worker'ı yeniden başlatır (kalıcı kayıt); bu betik meridian'ı defalarca
  # yeniden başlatır ve her restart nabzı dakikalarca bayat bırakır. Timer pencerenin ortasında
  # ateşlenirse ölçüm SEBEPSİZ "ölçülemedi" verir — ve sebebi çıktıda GÖRÜNMEZ.
  echo "  ÖN KOŞUL: sudo systemctl stop meridian-tick-watchdog.timer (sonda geri aç)"
  # TAVAN YÜKSELTME BİÇİMİ ETKİN DEĞERDEN TÜRETİLİR: literal bir sayı basmak, operatöre KENDİ
  # ortamındaki tavanı değil bir sabiti okuturdu. Satır YALNIZ hindsight-api yeniden başlıyorsa
  # basılır — ilgisiz bir tavanı önermek kuru raporu gürültüyle doldurmaktır (bedel yasası).
  case " $(_birimler "$alt") " in
    *" hindsight-api.service "*)
      echo "  tavanı yükseltmek gerekirse (DÜZ sudo ortam değişkenini DÜŞÜRÜR):"
      echo "    sudo env HAZIR_TAVAN_S_hindsight_api=$(_hazir_tavan hindsight-api.service) ./deploy/oracle-a1/sir_rotasyon.sh --$alt" ;;
  esac
  echo "  yedek dizini: $KOK/root/sir-yedek-<UTC ts>-$alt"
}

kapi() {
  echo "=== ROTASYON: KAPI_APIKEY (kapı tüketici anahtarı) ==="
  [ "$KURU" = 0 ] || { _kuru_rapor kapi; return 0; }
  _yedek_al kapi
  py cikar dosya "$YEDEK/etc/meridian/kapi_apikey" - - "$ISLIK/eski"
  _uret b64
  _yaz kapi
  _yeniden_baslat kapi
  _farksal "kapı /models" "$ISLIK/yeni" "$ISLIK/eski" "$KAPI_UC/models" "apikey" "-" "200" "401 403"
  local _kapi_hal; _kapi_hal="$(_nous_hali)"
  [ "$_kapi_hal" = "OK" ] || olcum_yok "motor /api/secrets/test/nous → $_kapi_hal (OK bekleniyordu)
     — motor kapıya konuşamıyor ya da yüzeye ULAŞILAMADI; ikisi aynı şey DEĞİLDİR ve hüküm ikisinde de
     'geçti' olamaz."
  oldu "motor içi kanıt: /api/secrets/test/nous ok:true"
  echo ">> geri alma: sudo cp -p $YEDEK/etc/meridian/kapi_apikey /etc/meridian/kapi_apikey (+ .env-apisix) ve $(_birimler kapi) yeniden başlat"
}

tenant() {
  echo "=== ROTASYON: HINDSIGHT_API_TENANT_API_KEY ==="
  [ "$KURU" = 0 ] || { _kuru_rapor tenant; return 0; }
  _yedek_al tenant
  py cikar dosya "$YEDEK/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY" - - "$ISLIK/eski"
  _uret hex
  _yaz tenant
  _yeniden_baslat tenant
  _farksal "hindsight /banks" "$ISLIK/yeni" "$ISLIK/eski" \
           "$HINDSIGHT/v1/default/banks" "Authorization" "Bearer" "200" "401 403"
  _envanter_esitlik tenant
  echo ">> geri alma: $YEDEK altındaki üç kopyayı geri koy ve $(_birimler tenant) yeniden başlat"
}

db() {
  echo "=== ROTASYON: Postgres 'hindsight' rol parolası ==="
  [ "$KURU" = 0 ] || { _kuru_rapor db; return 0; }
  _yedek_al db
  sudo cp -p "$YEDEK/etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL" "$ISLIK/eski_url"
  _uret b64
  _yaz db
  _yeniden_baslat db
  # KANIT DSN'İN KENDİSİNE BAĞLANIR. İlk tur `psql -U hindsight -d hindsight` yazıyordu: ne host
  # ne port DSN'den geliyordu, yani libpq yerel UNIX soketine düşüyor ve ölçüm rotasyonun YAZDIĞI
  # bağlantıyı değil, tesadüfen erişilebilen BAŞKA bir yolu sınıyordu. Bağlantı parametreleri
  # artık DSN'den TÜRETİLİR (`dsn-uc`; parola BASILMAZ, o yalnız PGPASSFILE'dan akar).
  # `-w` ZORUNLU: parola bulunamazsa psql İSTEM açar ve bakım penceresi bir ölçüm değil bir ASKI
  # üretir; `-w` ile aynı hâl anında "ölçülemedi" olur.
  local host port kuser kdb
  read -r host port kuser kdb < <(py dsn-uc "$KOK/etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL")
  [ -n "$host" ] && [ -n "$port" ] && [ -n "$kuser" ] && [ -n "$kdb" ] \
    || olcum_yok "DSN'den host/port/user/db türetilemedi — kanıt YAPILAMAZ"
  oldu "kanıt ucu DSN'den türetildi: $kuser@$host:$port/$kdb (parola BASILMAZ)"
  # POZİTİF: yeni parola ile `select 1`. Parola PGPASSFILE'dan okunur — argv'ye ve PGPASSWORD
  # ortam değişkenine GİRMEZ (ortam çocuklara akar).
  py pgpass "$ISLIK/pgpass_yeni" "$KOK/etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL"
  local cikti
  cikti="$(PGPASSFILE="$ISLIK/pgpass_yeni" psql -w -tAX -h "$host" -p "$port" -U "$kuser" \
             -d "$kdb" -c 'select 1' 2>&1 || true)"
  # sessiz-yutma: psql'in HATA metni de hükme girer (aşağıda ölçülür); `|| true` olmadan
  # `set -e` negatif ölçümü hiç yapamadan koşumu keserdi.
  # HÜKÜM TAM EŞLEŞMEDİR. İlk tur `case *1*` yazıyordu ve o kalıp `127.0.0.1`, `port 5432`,
  # `line 1` gibi HER hata metnini "select 1 → 1" sayardı — yani bağlanamayan bir psql
  # "rotasyon doğrulandı" diye okunurdu. Boşluk kırpılır (psql `-tA` ile de \n bırakır).
  [ "$(printf '%s' "$cikti" | tr -d '[:space:]')" = "1" ] \
    || olcum_yok "yeni parola ile 'select 1' TAM olarak 1 döndürmedi — rotasyon doğrulanamadı"
  oldu "yeni parola: select 1 → 1"
  # NEGATİF: eski URL ile bağlantı FATAL vermeli. Vermezse parola gerçekten değişmemiştir.
  py pgpass "$ISLIK/pgpass_eski" "$ISLIK/eski_url"
  # sessiz-yutma: burada BAŞARISIZLIK BEKLENEN sonuçtur (eski parola artık geçmemeli) — çıkış
  # kodu değil, aşağıda ölçülen HATA METNİ hükümdür; `|| true` olmadan `set -e` ölçümü keserdi.
  cikti="$(PGPASSFILE="$ISLIK/pgpass_eski" psql -w -tAX -h "$host" -p "$port" -U "$kuser" \
             -d "$kdb" -c 'select 1' 2>&1 || true)"
  case "$cikti" in
    *FATAL*|*fatal*|*authentication*) oldu "eski parola: FATAL (kanıt parolaya BAĞLI)" ;;
    *) olcum_yok "ESKİ parola hâlâ bağlanıyor — ALTER ROLE etkisiz ya da kimlik doğrulama kapalı" ;;
  esac
  echo ">> geri alma: eski parolayı ALTER ROLE ile geri koy + $YEDEK altındaki DSN'i geri yaz"
}

dash() {
  echo "=== ROTASYON: MERIDIAN_DASH_TOKEN ==="
  [ "$KURU" = 0 ] || { _kuru_rapor dash; return 0; }
  _yedek_al dash
  py cikar dosya "$YEDEK/etc/meridian/dash_token" - - "$ISLIK/eski"
  _uret b64
  _yaz dash
  _yeniden_baslat dash
  _farksal "pano /api/secrets" "$ISLIK/yeni" "$ISLIK/eski" \
           "$API/api/secrets" "x-meridian-token" "-" "200" "401 403"
  echo "  · pano PAROLA oturumu ayrı bir sırdır ve ETKİLENMEDİ."
  echo "  · operatörün YEREL .env kopyası bu betiğin kapsamı DIŞINDA — Rol-1 ayrıca eşitler."
  echo ">> geri alma: sudo cp -p $YEDEK/etc/meridian/dash_token /etc/meridian/dash_token (+ .dash.env) ve meridian.service yeniden başlat"
}

# -------------------------------------------------------------------------------------------------
# NEGATİF ÖN-KONTROL — YAZIMDAN ÖNCE, GERİ ALINIR.
# `--openrouter`in kanıt yüzeyleri isteğe anahtar ALMAZ (motor kendi yapılandırdığı anahtarla
# konuşur, kapı kendi upstream anahtarını kullanır) — yani "eski anahtarla 401" ÖLÇÜLEMEZ.
# Tek dürüst yol FARK yaratmaktır: bilerek bozuk bir değer yazılır, yüzey BAŞARISIZ olmalıdır.
# Başarısız OLMUYORSA kanıt anahtara bağlı değildir ve operatörün TAZE anahtarı boşa gitmesin
# diye betik yazımdan ÖNCE durur. Ölçüm KENDİ ARDINI TOPLAR: trap her yolda geri yükler.
# HEDEF ÖNCE SİLİNİR. Credential kaynakları 0400'dür ve `cp` HEDEFİ yazmak için açar: salt-okunur
# bir dosyanın üzerine `cp` "Permission denied" verir. Bu, v447 H5'in yakaladığı GERÇEK bir
# arızaydı — `|| true` onu YUTUYORDU ve negatif kontrol bilerek bozuk değeri diskte bırakıyordu.
# `rm -f` dosyanın değil DİZİNİN yazma iznini ister; `cp -p` sonra yedeğin mod/sahibiyle geri kurar.
_negatif_geri_al() {
  local cift yedek hedef basarisiz=""
  for cift in $GERI_AL_LISTESI; do
    yedek="${cift%%|*}"; hedef="${cift#*|}"
    # HEDEF ASLA ARADAN KALDIRILMAZ. İlk biçim `rm -f "$hedef"` + `cp -p` yazıyordu ve `cp`
    # düştüğünde hedef HİÇ YOK kalıyordu. `/etc/meridian/nous_api_key` bir `LoadCredential`
    # KAYNAĞIDIR ve kaynak dosya YOKSA systemd birimi HİÇ BAŞLATMAZ (drop-in'lerin kendi şerhi):
    # yani "bozuk değer taşıyor olabilir" diye teşhis edilen hâlin gerçeği "birim bir daha
    # AÇILMIYOR" olurdu. Yeni yol yan dosyaya yazıp ATOMİK `mv` ile yerine koyar; `cp` düşerse
    # hedef ESKİ hâliyle YERİNDE durur. `rm -f` gerekmez: 0400 bir hedefin üzerine yazma izni
    # DOSYANIN değil DİZİNİNDİR ve `mv -f` onu kullanır.
    if sudo cp -p "$yedek" "$hedef.yeni" && sudo mv -f "$hedef.yeni" "$hedef"; then
      :
    else
      sudo rm -f "$hedef.yeni" || true   # sessiz-yutma: yarım kalan yan dosyanın silinememesi
      # asıl hükmü (GERİ ALMA BAŞARISIZ) DEĞİŞTİRMEZ ve o hüküm hemen aşağıda bağırılır.
      basarisiz="$basarisiz $hedef"      # sessiz-yutma DEĞİL: hata BİRİKTİRİLİR — burada durmak
      # öteki dosyaları geri alınmamış bırakırdı.
    fi
  done
  GERI_AL_LISTESI=""
  # `die` DEĞİL `return 1`: bu fonksiyon EXIT trap'in İÇİNDEN de çağrılır ve trap içinde `exit`
  # etmek, arkasından gelen TEMİZLİĞİ yutar (bkz. `_negatif_trap`). Hükmü çağıran verir.
  [ -z "$basarisiz" ] || { echo "!! GERİ ALMA BAŞARISIZ:$basarisiz
     Bu dosyalar BİLEREK BOZUK değer taşıyor OLABİLİR. Yedekten elle geri koy: $YEDEK
     Bir kaynak dosya YOKSA birim BAŞLAMAZ (LoadCredential sözleşmesi): ÖNCE dosyayı geri koy,
     SONRA yeniden başlat." >&2; return 1; }
  return 0
}

# GERİ ALMADAN SONRA YENİDEN BAŞLATMA — BLOKLAYICI bir körlüğün kapanışı (inceleme 2026-09-08).
# Negatif kontrol hedeflere BİLEREK bozuk/boş değer yazar ve birimleri O DEĞERLE yeniden başlatır.
# Hazırlık beklemesi aşılırsa (`olcum_yok`, çıkış 2) trap DOSYALARI geri alıyor ama BİRİMLERİ
# yeniden başlatmıyordu. Ölçülen hâl: `/run/credentials/meridian.service/NOUS_API_KEY` BOŞ,
# `/run/credentials/hindsight-api.service/HINDSIGHT_API_LLM_API_KEY` `sahte-…` — yani canlıda
# hafıza zinciri ve kapı bilerek bozuk anahtarla koşmaya DEVAM ediyordu (apisix `$env://`
# çözümünü yalnız açılışta yapar). Operatörün gördüğü tek cümle "hazırlık bekleme aşıldı"ydı ve
# "hiçbir kalıcı yazım yok" disiplinini bilen bir okuyucuya "bir şey olmadı" diye okunur.
# HAZIRLIK BEKLENMEZ: trap içinden ikinci bir `olcum_yok` çağırmak, ölçüm arızasını temizliğin
# önüne koymak olurdu. Restart ATILIR ve BAĞIRILARAK BEYAN EDİLİR; doğrulama operatörün bir
# sonraki komutudur.
# DOĞRULAMA İKİ SORUDUR ve ilk biçim YANLIŞ OLANI öneriyordu (inceleme D7/Y3): `--envanter`
# DOSYALARI kıyaslar, "birim ayakta mı"yı ÖLÇMEZ — ve bu dalda dosyalar ZATEN geri alınmıştır,
# yani envanter her hâlükârda EŞİT der. Bu dalın gerçek arıza sınıfı "birim açılmıyor"dur ve
# önerilen doğrulama ona YAPISAL OLARAK KÖRDÜ: yanlış bir güven üretiyordu. İki soru artık
# SIRALI basılır ve önce birim sorulur. Çivi: `test_P1`in son iki assert'ü.
_negatif_restart_kurtarma() {
  local b basarisiz=""
  [ -n "$NK_BIRIMLER" ] || return 0
  for b in $NK_BIRIMLER; do
    sudo systemctl restart "$b" || basarisiz="$basarisiz $b"   # sessiz-yutma DEĞİL: hata
    # BİRİKTİRİLİR ve aşağıda ELLE REÇETEYLE bağırılır; ilk düşen birimde durmak ötekileri
    # bilerek bozuk değerde bırakırdı.
  done
  if [ -z "$basarisiz" ]; then
    echo "!! BU BİRİMLER BİLEREK BOZUK/BOŞ DEĞERLE AÇILMIŞTI ve dosyalar geri alındıktan sonra
     yeniden başlatıldı: $NK_BIRIMLER
     (Hazırlık BEKLENMEDİ — trap içinde ölçüm yapılmaz.)
     DOĞRULAMA İKİ SORUDUR, ÖNCE BİRİNCİSİ:
       1) birim AYAKTA mı: sudo systemctl is-active $NK_BIRIMLER
                           sudo journalctl -u <birim> -n 50 --no-pager
       2) dosyalar EŞİT mi: sudo $0 --envanter
     --envanter DOSYALARI kıyaslar, birimin AÇILDIĞINA KÖRDÜR: bu dalda dosyalar zaten geri
     alınmıştır, yani tek başına yanlış bir güven üretir." >&2
  else
    echo "!! YENİDEN BAŞLATILAMADI:$basarisiz
     BU BİRİMLER HÂLÂ BİLEREK BOZUK/BOŞ DEĞERLE KOŞUYOR OLABİLİR. ELLE:
     sudo systemctl restart$basarisiz
     sonra AYAKTA mı: sudo systemctl is-active$basarisiz
                      sudo journalctl -u <birim> -n 50 --no-pager" >&2
  fi
  NK_BIRIMLER=""
  return 0
}

# TRAP GÖVDESİ TEK FONKSİYONDUR — biçim tercihi değil, ÖLÇÜLMÜŞ bir sözleşme. `trap 'a; b' EXIT`
# içinde `a` `exit` ederse `b` HİÇ KOŞMAZ ve çıkış kodu `a`nınkine döner. İlk biçim
# `trap '_negatif_geri_al; _temizle' EXIT` idi ve `_negatif_geri_al` başarısızlıkta `die`
# ediyordu, yani: (a) `_temizle` HİÇ çağrılmıyor → operatörün TAZE anahtarlarını taşıyan 0700
# çalışma dizini diskte kalıyor ve "SİLİNEMEDİ" uyarısı bile basılmıyordu (K9a'nın kapattığı
# sessizlik bu yoldan geri geliyordu); (b) "2 = ölçülemedi" sözleşmesi tam da EN KÖTÜ hâlde 1'e
# bozuluyordu. Sıra da sözleşmedir: önce dosyalar, sonra birimler, sonra temizlik.
_negatif_trap() {
  local hata=0
  _negatif_geri_al || hata=1
  _negatif_restart_kurtarma
  _cikis
  [ "$hata" = 0 ] || exit 2
  return 0
}

# `_negatif_kontrol <alt> <sır> <ölçüm fn> <yöntem>` — ölçüm fonksiyonu OK/RET/OLCULEMEDI döndürür.
# YÖNTEM iki tanedir ve seçim SIRRIN TÜKETİCİSİNE bağlıdır, keyfe değil:
#   bozuk : hedeflere `sahte-<hex>` yazılır. Tüketici değeri UPSTREAM'e taşıyorsa (OPENROUTER →
#           kapı → OpenRouter) yanlış bir değer 401/402 ile GERİ DÖNER, yani ölçülebilir.
#   bos   : hedefler BOŞALTILIR. NOUS için tek dürüst yöntem budur: motorun kapı üzerinden yaptığı
#           `ping_brain` çağrısında Authorization başlığı upstream'e GEÇMEZ (kapı kendi anahtarını
#           kullanır), yani YANLIŞ bir NOUS anahtarı 200/ok:true döndürür ve "bozuk" yöntemi
#           yapısal olarak ölçemez. BOŞ değerde ise motor çağrıyı hiç kuramaz → ok:false (RET).
#           Bu bir VARLIK kanıtıdır ve öyle BEYAN EDİLİR — değer-doğruluğu kanıtı DEĞİLDİR.
_negatif_kontrol() {
  local alt="$1" sir="$2" olcum="$3" yontem="${4:-bozuk}" _alt _sir tur yol _alan mod sahip _o
  local sahte="$ISLIK/sahte" sonuc birimler
  # KAPSAM: yalnız BU SIRRIN tüketicileri yeniden başlar. Alt komutun tamamını başlatmak, ölçümle
  # ilgisi olmayan birimleri İKİ kez (boz + geri-al) kesintiye uğratır ve her seferinde hazırlık
  # beklemesi ödetir — hindsight ~60 s açılıyor (ölçüm 2026-09-08 07:3xZ).
  birimler="$(_sir_birimleri "$sir")" || die "negatif kontrol: $sir için tüketici birim haritası YOK"
  echo "  · yeniden başlatılacak (yalnız $sir tüketicileri): $birimler"
  printf 'sahte-%s\n' "$(openssl rand -hex 8)" > "$sahte"; chmod 600 "$sahte"
  GERI_AL_LISTESI=""
  while read -r _alt _sir tur yol _alan mod sahip _o; do
    [ "$_alt" = "$alt" ] && [ "$_sir" = "$sir" ] || continue
    # `api` satırı da GERİ ALMA KÜMESİNE girer: disk karşılığı `state/secrets.json`dur ve boşluk
    # ölçümü onu SİLER (bkz. `_api_sil`). Kümeden dışarıda kalsaydı ölçüm kendi sildiği kopyayı
    # geri koyamaz, motor rotasyon sonrası bir fallback'i EKSİK kalırdı.
    yol="$(_disk_yolu "$tur" "$yol")" || continue
    sudo test -e "$KOK$yol" || continue
    sudo cp -p "$KOK$yol" "$ISLIK/nk-$(echo "$yol" | tr '/' '_')"
    GERI_AL_LISTESI="$GERI_AL_LISTESI $ISLIK/nk-$(echo "$yol" | tr '/' '_')|$KOK$yol"
  done < <(_kopyalar)
  # shellcheck disable=SC2064
  trap '_negatif_trap' EXIT
  if [ "$yontem" = bos ]; then
    while read -r _alt _sir tur yol _alan mod sahip _o; do
      [ "$_alt" = "$alt" ] && [ "$_sir" = "$sir" ] || continue
      case "$tur" in
        dosya) sudo test -e "$KOK$yol" || continue
               py bosalt "$KOK$yol" "$mod" "$sahip" ;;
        # GERİ-DÜŞÜŞ ZİNCİRİNİN İKİNCİ UCU. Credential'ı boşaltmak TEK BAŞINA hiçbir şey ölçmez:
        # `secrets._fetch` bir sonraki basamağa (motorun KENDİ deposu) düşer ve ölçüm o eski ama
        # geçerli kopyayı ölçer. İki uç AYNI pencerede kapatılır, yoksa "boş değer" hâli hiç
        # DOĞMAZ ve negatif kontrol yapısal olarak boşa geçer (inceleme B1).
        api)   _api_sil "$sir" "$yol" ;;
        env|url) die "boş-değer negatif kontrolü YALNIZ 'dosya' ve 'api' kopyası için tanımlı ($sir → $tur $yol).
     Bir `env` satırını boşaltmak dosyanın ötekilerini de etkiler; yöntem sessizce genişletilmez." ;;
      esac
    done < <(_kopyalar)
  else
    _yaz "$alt" "$sir" "$sahte" "dosya env url"
  fi
  # BU SATIRDAN SONRA BİRİMLER BİLEREK BOZUK/BOŞ DEĞERLE KOŞUYOR. Küme trap'in görebileceği bir
  # global'e YAZILIR: her çıkış yolu (hazırlık aşımı · `set -e` · `olcum_yok`) dosyaları geri
  # aldıktan SONRA bu birimleri yeniden başlatmak ZORUNDADIR — yoksa "hiçbir kalıcı yazım yok"
  # cümlesi DİSK için doğru, ÇALIŞAN SÜREÇ için yanlış olur (bkz. `_negatif_restart_kurtarma`).
  NK_BIRIMLER="$birimler"
  # shellcheck disable=SC2086
  _yeniden_baslat_sessiz $birimler
  sonuc="$($olcum)"
  # `exit 2` — geri alma başarısızlığı bir ÖLÇÜM ARIZASIDIR (çıkış 2), bir `die` (çıkış 1)
  # değil; ve `exit` EXIT trap'i ateşler, yani temizlik + kurtarma yine koşar.
  _negatif_geri_al || exit 2
  # shellcheck disable=SC2086
  _yeniden_baslat_sessiz $birimler
  NK_BIRIMLER=""
  trap '_cikis' EXIT
  case "$sonuc" in
    RET) oldu "negatif kontrol ($sir, yöntem=$yontem): → RET (kanıt anahtara BAĞLI)" ;;
    OK)  olcum_yok "negatif kontrol ($sir, yöntem=$yontem): bozuk/boş değerle de OK geldi — kanıt
     anahtara BAĞLI DEĞİL. Operatörün yeni anahtarı YAZILMADI (hiçbir kalıcı yazım yok)." ;;
    *)   olcum_yok "negatif kontrol ($sir, yöntem=$yontem): ÖLÇÜM ARIZASI → $sonuc.
     Yüzeye ulaşılamadı; bu 'anahtar reddedildi' DEĞİLDİR ve öyle sayılamaz (kanıt uydurmak
     olurdu). Operatörün yeni anahtarı YAZILMADI (hiçbir kalıcı yazım yok)." ;;
  esac
}

_yeniden_baslat_sessiz() {
  local b
  for b in "$@"; do
    sudo systemctl restart "$b" >/dev/null 2>&1 || true   # sessiz-yutma: negatif kontrol
    # SIRASINDA bozuk değerle bir birim açılmayabilir; bu beklenen hâldir ve ölçümün kendisidir.
  done
  # SESSİZ olan RESTART'tır, BEKLEME DEĞİL. Negatif kontrolün ölçümü tam da burada, restart'ın
  # HEMEN ardından yapılır (vaka 2026-09-08) — bekleme atlanırsa "bozuk değerle reddedildi" ile
  # "birim henüz ayakta değil" aynı `000`a düşer ve ikisi AYNI ŞEY DEĞİLDİR.
  _hazir_bekle "$@"
}

# Model ADI sır DEĞİLDİR ama kanıtın ön şartıdır: modelsiz bir `chat/completions` gövdesi kapıdan
# 400 döner ve "anahtar yanlış" ile "gövde yanlış" ayırt EDİLEMEZ. Kapı ÜST DÜZEYDE, ölçümden
# önce: `$( )` içinden `exit` yalnız alt kabuğu bitirir ve gerekçe kaybolurdu.
MODEL=""
_model_gerekli() {
  # sessiz-yutma: dosya YOK ya da okunamıyorsa `sed`in hata metni hükme GİRMEZ — hüküm MODEL'in
  # boş kalıp kalmadığıdır ve bir satır aşağıda `olcum_yok` ile ölçülür.
  MODEL="$(sudo sed -n 's/^NOUS_MODEL=//p' "$KOK/opt/meridian/.env" 2>/dev/null | head -1 | tr -d '\r\n"')"
  [ -n "$MODEL" ] || olcum_yok "NOUS_MODEL okunamadı (/opt/meridian/.env) — kapı kanıtı YAPILAMAZ"
}

# OPENROUTER bacağının DEĞER-DOĞRULUĞU ölçümü: kapıdan GERÇEK bir tamamlama isteği. `_nous_hali`
# ile aynı üç hâl sözlüğünü konuşur — negatif kontrol tek bir sözlük tanır, iki ayrı vokabüler
# (biri HTTP kodu, biri OK/RET) çağrı yerinde sessizce karışırdı.
#   OK          → 200 + gövdede `choices`  (anahtar upstream'de GEÇTİ)
#   RET         → 401/402                  (upstream anahtarı REDDETTİ; 402 = kredi bitti)
#   OLCULEMEDI  → 000 / 5xx / 200-ama-gövdesiz — kapının kendi arızası, anahtar hakkında hüküm YOK
_kapi_chat_hali() {
  local cfg="$ISLIK/kanit.cfg" out="$ISLIK/kanit.out" govde="$ISLIK/chat.json" tok="$ISLIK/kapi_tok" kod
  printf '{"model": "%s", "max_tokens": 8, "messages": [{"role": "user", "content": "ping"}]}\n' \
         "$MODEL" > "$govde"
  py cikar dosya "$KOK/etc/meridian/kapi_apikey" - - "$tok"
  rm -f "$out"          # bkz. `_kod` şerhi: bayat gövde ulaşılamayan bir ucu "geçti" gösterir
  py kanit-cfg "$cfg" "$KAPI_UC/chat/completions" "apikey" "-" "$tok" "$out" "$govde"
  kod="$(_curl_kod "$cfg")"
  case "$kod" in
    200) case "$(_govde)" in *choices*) echo OK ;; *) echo "OLCULEMEDI(200-govdesiz)" ;; esac ;;
    401|402) echo RET ;;
    *) echo "OLCULEMEDI(http=$kod)" ;;
  esac
}

openrouter() {
  echo "=== ROTASYON: OpenRouter anahtarları (operatör yapıştırır) ==="
  # KURU KAPISI `_oku_gizli` ÇAĞRILARININ ÜSTÜNDE. Altındayken `--openrouter --kuru` bir kuru
  # koşum DEĞİLDİ: iki gerçek anahtar istiyor, boş bırakılınca "yapacak iş yok" deyip çıkış 1
  # veriyordu — yani rotasyonun ÖN-BAKIŞI ancak taze anahtar yapıştırarak alınabiliyordu.
  # Kuru raporun değere ihtiyacı YOKTUR: 14 kopya da, birim listesi de kopya tablosundan gelir.
  [ "$KURU" = 0 ] || { _kuru_rapor openrouter; return 0; }
  local nous_var=0 or_var=0
  _oku_gizli "NOUS_API_KEY (motor)" "$ISLIK/nous" && nous_var=1 || nous_var=0
  _oku_gizli "OPENROUTER_API_KEY (kapı + hafıza + botlar)" "$ISLIK/orkey" && or_var=1 || or_var=0
  [ "$nous_var" = 1 ] || [ "$or_var" = 1 ] || die "iki anahtar da boş — yapacak iş yok"
  [ "$or_var" = 0 ] || _model_gerekli
  _yedek_al openrouter

  if [ "$nous_var" = 1 ]; then
    adim "negatif kontrol (NOUS_API_KEY) — YAZIMDAN ÖNCE"
    echo "  · KAPSAM BEYANI: NOUS için DEĞER-DOĞRULUĞU kapıdan ÖLÇÜLEMEZ — kapı isteğin"
    echo "    Authorization başlığını upstream'e geçirmez, kendi anahtarını kullanır. Yanlış bir"
    echo "    NOUS anahtarı da ok:true döndürebilir. Bu bacağın kanıtı VARLIK kanıtıdır:"
    echo "    boş değer → ok:false, gerçek değer → ok:true. Değer-doğruluğu ölçülmedi (None)."
    _negatif_kontrol openrouter NOUS_API_KEY _nous_hali bos
  fi
  if [ "$or_var" = 1 ]; then
    adim "negatif kontrol (OPENROUTER_API_KEY) — YAZIMDAN ÖNCE"
    _negatif_kontrol openrouter OPENROUTER_API_KEY _kapi_chat_hali bozuk
  fi

  # NOUS'ta ÖNCE YALNIZ `dosya` (credential kaynağı) yazılır; `api` kopyası (motorun kendi deposu)
  # kanıttan SONRA gelir. İKİ SEBEP, ikisi de sıralama süsü değil:
  #   (1) KAPSAM DÜRÜSTLÜĞÜ — depo kopyası doluyken BOŞ bir credential de ok:true üretir. Ölçüm
  #       anında deponun ESKİ değerde kalması + credential doluluğunun mekanik denetimi, "okunan
  #       kanal credential'dır" cümlesini söylenebilir kılar. İki kopya birlikte yazılsaydı bu
  #       cümle kurulamazdı — negatif kontroldeki körlüğün (inceleme B1) ayna görüntüsü.
  #   (2) GERİ ALINABİLİRLİK — kanıt aşamasında durulursa (çıkış 2) motorun deposunda YENİ bir
  #       değer bırakılmamış olur; depo, dosya kopyalarından farklı olarak yalnız uç üzerinden
  #       ya da tam-dosya geri yazımıyla düzeltilebilir.
  # Sıra: yaz → restart (+credential doluluk denetimi) → ölç → ancak sonra depoyu eşitle.
  [ "$nous_var" = 0 ] || { _yaz openrouter NOUS_API_KEY "$ISLIK/nous" "dosya"; }
  [ "$or_var" = 0 ]   || { _yaz openrouter OPENROUTER_API_KEY "$ISLIK/orkey"; }
  # POZİTİF KANIT RESTART'I DA TÜKETİCİYE BAĞLIDIR: YALNIZ yazılan sırların tüketicileri yeniden
  # başlar. Operatör tek anahtar döndürüyorsa ötekinin birimini kesintiye uğratmak karşılıksız bir
  # kesinti + karşılıksız bir hazırlık beklemesidir (ölçüm 2026-09-08 07:3xZ).
  local poz=""
  [ "$nous_var" = 0 ] || poz="$poz $(_sir_birimleri NOUS_API_KEY)"
  [ "$or_var" = 0 ]   || poz="$poz $(_sir_birimleri OPENROUTER_API_KEY)"
  # shellcheck disable=SC2086
  poz="$(_sirala $poz)"
  if [ "$or_var" = 1 ]; then
    echo "  · KAPSAM: hermes profilleri (bekci·karne·sef) yeniden BAŞLATILMAZ — timer'lı oneshot"
    echo "    birimlerdir, yeni değeri bir sonraki tetikte okurlar (dosyaları YAZILDI)."
  fi
  # shellcheck disable=SC2086
  _yeniden_baslat openrouter $poz

  if [ "$or_var" = 1 ]; then
    local hal; hal="$(_kapi_chat_hali)"
    [ "$hal" = "OK" ] || olcum_yok "kapı chat/completions → $hal (OK bekleniyordu: 200 + gövdede choices)"
    oldu "kapı kanıtı: chat/completions 200 · gövdede choices (DEĞER-DOĞRULUĞU kanıtı)"
    # `/health` ANAHTARA KÖRDÜR ve satır bunu SÖYLER. İlk tur burada LLM anahtarını dosyadan
    # çıkarıp `_kod`a veriyordu ama `/health` başlık İSTEMEZ: çıkarılan değer hiçbir yere gitmiyor,
    # yani okunmayan bir yazımdı (Yasa 6) ve satır "hafıza kanıtı" diye BASILIYORDU. Çıkarım
    # kaldırıldı; satır kendi kapsamını beyan ediyor. Hindsight'ın LLM anahtarını GERÇEKTEN
    # tüketen bir yüzey (ör. bir hafıza yazımı/özeti) ölçülmedi — açık kalem, raporda.
    local kod; kod="$(_kod "-" "$HINDSIGHT/health" "-" "-")"
    [ "$kod" = "200" ] || olcum_yok "hindsight /health → $kod (servis ayakta DEĞİL)"
    oldu "hafıza yüzeyi: /health 200 — servis ayakta; LLM anahtarı için kanıt DEĞİL (uç anahtar istemez)"
  fi
  if [ "$nous_var" = 1 ]; then
    local nhal; nhal="$(_nous_hali)"
    [ "$nhal" = "OK" ] || olcum_yok "motor /api/secrets/test/nous → $nhal (OK bekleniyordu)"
    # KAPSAM, TAM OLARAK: bu satır ne KADAR söylüyorsa o kadar. Ölçüm anında motorun depo kopyası
    # HÂLÂ ESKİ değerdedir (eşitleme bir sonraki adımda) ve credential'ın DOLU olduğu bir üstteki
    # `_kredensiyel_denetle`de ölçülmüştür; `_fetch` credential'ı ÖNCE okuduğu için okunan kanal
    # CREDENTIAL'dır. Hangi DEĞERİN geçerli olduğu buradan ölçülemez — ESKİ anahtar da ok:true
    # döndürür (kapı Authorization'ı upstream'e geçirmez; bkz. kapsam beyanı).
    oldu "motor kanıtı: /api/secrets/test/nous ok:true (VARLIK kanıtı — bkz. kapsam beyanı)
     · depo kopyası bu anda HÂLÂ ESKİ değerde, credential ise DOLU (yukarıda ölçüldü) ve önce
       okunuyor: okunan kanal CREDENTIAL'dır. Hangi DEĞERİN geçerli olduğu ölçülmedi (None)."
    # Kanıt alındı; motorun kendi deposu ŞİMDİ eşitlenir. Üç kopya (credential kaynağı ·
    # /run/credentials · state/secrets.json) ancak bu adımdan sonra aynı değeri taşır.
    _yaz openrouter NOUS_API_KEY "$ISLIK/nous" "api"
  fi
  echo ">> geri alma: $YEDEK altındaki kopyaları geri koy ve $(_birimler openrouter) yeniden başlat"
}

# =================================================================================================
# ENVANTER — DEĞER BASMADAN VARLIK + EŞİTLİK
# =================================================================================================
_envanter_esitlik() {
  local sadece="${1:-}" _alt sir tur yol alan _m _s onek
  local birinci_tur birinci_yol birinci_alan birinci_onek onceki_sir="" sonuc etiket
  while read -r _alt sir tur yol alan _m _s onek; do
    [ -z "$sadece" ] || [ "$_alt" = "$sadece" ] || continue
    case "$tur" in
      api) echo "  $sir · motor API $yol → OKUNAMADI (yazma kanalı; motor içinden ölçülür)"; continue ;;
      sql) echo "  $sir · ALTER ROLE $yol → OKUNAMADI (SQL kanalı; kanıt psql ile ölçülür)"; continue ;;
    esac
    # `${alan:+…}` ALAN YOKLUĞUNU görmez: tabloda yokluk boş dizge değil `-` ile yazılır, yani
    # `dosya`/`url` satırları operatöre `[-]` diye basılıyordu (inceleme B5). Yokluğun işareti
    # tabloda TEK ve o işaret burada da tanınmalı.
    etiket=""; [ "$alan" = "-" ] || etiket=" [$alan]"
    if [ "$sir" != "$onceki_sir" ]; then
      onceki_sir="$sir"; birinci_tur="$tur"; birinci_yol="$yol"; birinci_alan="$alan"; birinci_onek="$onek"
      echo "  $sir · $yol$etiket → $(py var "$tur" "$KOK$yol" "$alan") (referans kopya)"
      continue
    fi
    sonuc="$(py esit "$birinci_tur" "$KOK$birinci_yol" "$birinci_alan" "$birinci_onek" \
                     "$tur" "$KOK$yol" "$alan" "$onek")"
    echo "  $sir · $yol$etiket → $sonuc"
  done < <(_kopyalar)
}

# ARANAN ADLAR — kopya tablosundan TÜRETİLİR, elle yazılmaz (elle yazılan liste tablodan ayrışır).
# Üç kaynak (DÖRDÜNCÜSÜ tablodan türeMEZ ve aşağıda, `_dosya_adaylari`da yaşar): (1) sır KİMLİĞİ (`$2`) — `.env`lerde çoğu sır kendi adıyla yaşar; (2) `env` kopyanın
# ALAN adı (`$5`); (3) `dosya`/`url` kopyasının DOSYA ADI — bir `LoadCredential` kaynağı değişkenin
# ADINI taşır (`/etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY`), yani o ad bir `.env`de geçiyorsa
# beyan dışı bir kopyadır. Yalnız ALAN adlarını aramak, sırrın kendi adıyla duran kopyalarına
# KÖR kalırdı — ve tam o körlük "rotasyon bu dosyayı yazıyor" sanısını üretir.
_aranan_adlar() {
  _kopyalar | awk '
    {print $2}
    $3=="env" {print $5}
    $3=="dosya" || $3=="url" { n=split($4,a,"/"); if (a[n] ~ /^[A-Z][A-Z0-9_]*$/) print a[n] }
  ' | sort -u
}

# SIR ADI SÖZLÜĞÜ — taramanın DÖRDÜNCÜ kaynağı ve tek ELLE yazılmış parçası. Yukarıdaki üç kaynak
# tablodan TÜRER, yani yalnız BİLİNEN adları görür — ve tam bu körlük ölçüldü (2026-09-08 08:0xZ):
# `/opt/hindsight/.env`in altı failover ÜYE anahtarı hiçbir kopyanın kimliği, alanı ya da dosya adı
# değildi, dolayısıyla "tabloda olmayan kopyayı bulurum" beyanı o sınıfta BOŞTU. Aileyi (`_1_`,
# `_2_`, …) elle listelemek aynı körlüğü bir SONRAKİ üyede tekrarlardı; onun yerine dosyanın KENDİ
# alan adları okunur (`py alanlar`) ve sır ADI GİBİ görünen her alan tabloya karşı sınanır.
# SÖZLÜK BİLEREK DAR — ve bu bir KAPSAM BEYANIDIR, bir eksiklik değil: `*_KEY` (`BOT_KEY_*`,
# `APISIX_ADMIN_KEY`, `HINDSIGHT_CP_ACCESS_KEY`) ve `*_PAROLA` (`PANO_GIRIS_PAROLA`) biçimleri bu
# betiğin DÖNDÜRDÜĞÜ sırlar değildir; hepsini "beyan dışı kopya" diye bağırmak gerçek bulguyu
# gürültüde boğardı (bedel yasası). Sözlüğe uymayan bir sır adı bu taramaya GÖRÜNMEZ.
# BEDEL ÖLÇÜLDÜ, VARSAYILMADI — Rol-1, A1, 2026-09-08 (7 taranan dosya, YALNIZ ADLAR okundu):
# sözlüğün DIŞINDA kalan üçüncü-taraf adları `HINDSIGHT_CP_ACCESS_KEY` · `APISIX_ADMIN_KEY` ·
# `PANO_GIRIS_PAROLA`; HİÇBİRİ `_API_KEY`/`_TOKEN`/`_SECRET`/`_PASSWORD` sonekli DEĞİL, yani
# sözlüğün canlıdaki gürültüsü SIFIRDIR ve sözlük OLDUĞU GİBİ kalır. (İnceleme 2026-09-08 bu
# sözlüğün üçüncü-taraf anahtarlarını da bağırabileceğini işaret etmişti; ölçüm riskin BUGÜN
# gerçekleşmediğini söylüyor — "gerçekleşemez" demiyor.) Ölçüm `_taranan_dosyalar` kümesine
# BAĞLIDIR: kümeye yeni bir dosya girerse bedel YENİDEN ölçülür; sözlük ölçümsüz genişletilmez.
_SIR_ADI_SONEKLERI="_API_KEY _TOKEN _SECRET _PASSWORD"

_sir_adi_mi() {
  local s
  for s in $_SIR_ADI_SONEKLERI; do
    case "$1" in *"$s") return 0 ;; esac
  done
  return 1
}

# Bir dosyada SINANACAK adlar: tablodan türeyen üç kaynak ∪ dosyanın KENDİ sır-adı alanları.
_dosya_adaylari() {
  local a
  { _aranan_adlar
    while read -r a; do
      if _sir_adi_mi "$a"; then printf '%s\n' "$a"; fi
    done < <(py alanlar "$1")
  } | sort -u
}

# Tabloda OLMAYAN bir kopya, ilk rotasyondan sonra sessizce ESKİ değeri taşıyan bir kopyadır.
_beyan_disi_tara() {
  local dosya alan bulundu=0
  echo "  --- beyan dışı kopya taraması ---"
  while read -r dosya; do
    sudo test -f "$KOK$dosya" || continue
    while read -r alan; do
      [ "$(py alan-var "$KOK$dosya" "$alan")" = "VAR" ] || continue
      _kopyalar | awk -v d="$dosya" -v a="$alan" '$3=="env" && $4==d && $5==a {b=1} END{exit !b}' && continue
      echo "  !! BEYAN DIŞI KOPYA: $dosya [$alan] — rotasyon bu kopyayı YAZMIYOR"
      bulundu=1
    done < <(_dosya_adaylari "$KOK$dosya")
  done < <(_taranan_dosyalar)
  [ "$bulundu" = 0 ] && echo "  beyan dışı kopya YOK" || true   # sessiz-yutma: `[ ]` yanlışsa
  # `set -e` koşumu keserdi; bulgu ZATEN yukarıda basıldı ve envanter raporu bitmelidir.
}

_secrets_json_tara() {
  local ad
  echo "  --- motor sır deposu ($SECRETS_JSON) — yalnız AD, DEĞER OKUNMAZ ---"
  if ! sudo test -f "$KOK$SECRETS_JSON"; then
    echo "  · dosya YOK: $SECRETS_JSON — bu bir arıza değil, bir BOŞLUK beyanıdır (depo taranmadı)"
    return 0
  fi
  while read -r ad; do
    [ "$(py json-ad-var "$KOK$SECRETS_JSON" "$ad")" = "VAR" ] || continue
    if _kopyalar | awk -v a="$ad" '$3=="api" && $2==a {b=1} END{exit !b}'; then
      echo "  $SECRETS_JSON [$ad] → VAR (beyanlı: api kopyası bu depoya yazar)"
    else
      echo "  !! BEYAN DIŞI KOPYA: $SECRETS_JSON [$ad] — rotasyon bu kopyayı YAZMIYOR"
    fi
  done < <(_aranan_adlar)
}

envanter() {
  echo "=== SIR KOPYA ENVANTERİ (yalnız VARLIK ve EŞİTLİK; DEĞER ve HASH BASILMAZ) ==="
  _envanter_esitlik
  _beyan_disi_tara
  _secrets_json_tara
  echo "  --- yedekler (/root/sir-yedek-*) ---"
  _yedekleri_listele
}

# =================================================================================================
KURU=0
ALT=""
for _a in "$@"; do
  case "$_a" in
    --kuru) KURU=1 ;;
    --kapi|--tenant|--db|--dash|--openrouter|--envanter|--kopyalar)
      [ -z "$ALT" ] || die "iki alt komut verildi: --$ALT ve $_a — her koşum TEK sır döndürür"
      ALT="${_a#--}" ;;
    *) die "bilinmeyen argüman: $_a (--kapi | --tenant | --db | --dash | --openrouter | --envanter | --kopyalar [| --kuru])" ;;
  esac
done
[ -n "$ALT" ] || die "alt komut ZORUNLU: --kapi | --tenant | --db | --dash | --openrouter | --envanter | --kopyalar (+ --kuru)"

# `--kuru` YALNIZ ROTASYON alt komutlarında anlamlıdır. `--envanter`/`--kopyalar` bayrağı hiç
# okumaz ve `--envanter --kuru` SESSİZCE tam envanteri koşardı: kuru koşum isteyen operatör
# istediğini aldığını sanır (inceleme B6). Koşum ENGELLENMEZ (ikisi de zaten hiçbir şey yazmaz),
# ama etkisizlik SÖYLENİR — sessiz kabul, olmayan bir sözleşmeyi var gibi gösterir.
KURU_ONERILIR=0
case "$ALT" in
  kapi|tenant|db|dash|openrouter) KURU_ONERILIR=1 ;;
  *) [ "$KURU" = 0 ] || echo "!! --kuru bu alt komutta ETKİSİZDİR: --$ALT zaten hiçbir şey yazmaz." >&2 ;;
esac

# `--kopyalar` gömülü tabloyu basar: hiçbir dosya açmaz, hiçbir uca konuşmaz, hiçbir şey yazmaz —
# ve çivinin sözleşme yüzeyidir. Root kapısının ÜSTÜNDE durması bilinçlidir: kapıyı buraya da
# koymak, betiğin ne yazdığını root olmadan SORAMAMAK demek olurdu.
if [ "$ALT" = "kopyalar" ]; then _kopyalar; exit 0; fi

# =================================================================================================
# ÇAĞRI KAPISI — ROOT (bkz. başlıktaki "NİYE ROOT")
# =================================================================================================
# Kalan her alt komut 0400 root dosyaları okur/yazar VE o dosyalardan türettiği kanıt girdilerini
# (`curl -K` cfg'si, `PGPASSFILE`, SQL) başka bir sürece okutur. Yazan ile okuyan AYRI kimlik
# olduğunda hiçbir şey "izin yok" diye bağırmaz: `curl` cfg'yi açamaz, `_curl_kod` `000` döner
# ve kanıt sessizce 000 olur. Kapı bu yüzden ölçümün ÖNÜNDE: ölçüm arızasını hükme çevirmektense
# koşumu hiç başlatmamak. `--kuru` da kapının içindedir — kuru koşum gerçek koşumun ÖN-BAKIŞIDIR
# ve farklı bir kimlikle koşulan bir ön-bakış, ön-bakış değildir.
_UID="$(id -u)"
# Kuru koşum önerisi YALNIZ rotasyon alt komutlarında basılır: `--envanter --kuru` diye bir
# sözleşme YOK ve olmayan bir biçimi önermek, hata metnini yanlış bir yola sokar (inceleme B6).
_KURU_ONERI=""
[ "$KURU_ONERILIR" = 0 ] || _KURU_ONERI="   (kuru koşumda: sudo ./sir_rotasyon.sh --$ALT --kuru)"
[ "$_UID" = 0 ] || die "bu betik ROOT olarak koşar; şu an uid=$_UID.
     Doğrusu: sudo ./sir_rotasyon.sh --$ALT$_KURU_ONERI
     Sebep: kanıt girdileri (curl -K cfg · PGPASSFILE · SQL) 0600 root yazılır; onları çağıran
     kimlikle okutmak HER kanıtı 000 yapar ve rotasyon doğrulanamaz."

_islik_kur
case "$ALT" in
  kapi)       kapi ;;
  tenant)     tenant ;;
  db)         db ;;
  dash)       dash ;;
  openrouter) openrouter ;;
  envanter)   envanter ;;
esac

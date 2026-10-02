#!/usr/bin/env bash
# =================================================================================================
# sir_rotasyon.sh — A1 sırlarının ROTASYONU (DEĞER değişir, KANAL değişmez)
# =================================================================================================
# SUNUCUDA (A1) KOŞAR — `deploy.sh`/`cutover.sh`/`sir_credential_gecis.sh` ile aynı sözleşme.
# Otomatik ÇAĞRILMAZ: bakım penceresinde, operatör eliyle. KARDEŞİNDEN FARKI: `sir_credential_gecis.sh`
# bir sırrın KANALINI taşır (ortam → LoadCredential); bu betik kanala DOKUNMAZ, sırrın DEĞERİNİ
# döndürür ve o değerin BÜTÜN KOPYALARINI aynı pencerede eşitler.
#
# NİYE BİR BETİK. 2026-09-07 gecesi dört sır A1'de ELLE döndürüldü: her sırrın 1-13 kopyası var ve
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
# artık 13 kopya (NOUS 2). 2026-09-13: +1 GLOBAL `/home/ubuntu/.hermes/.env` — motorun
# `hermes._agent_call` yolu; 09-08 rotasyonu onu atladı, akşam inceleme 4 gün 401 aldı (TSK-181).
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
#   sudo ./sir_rotasyon.sh --apisix-admin → APISIX_ADMIN_KEY (kapı ADMIN API anahtarı; `--kapi`
#                                           DEĞİL: o kapının TÜKETİCİ anahtarıdır, bu kapının
#                                           YÖNETİM anahtarıdır — ayrı sır, ayrı yüzey, ayrı kopya
#                                           kümesi. TSK-064 Faz-1C, spec §3 madde 4.)
#   sudo ./sir_rotasyon.sh --cp           → HINDSIGHT_CP_ACCESS_KEY (Hindsight kontrol paneli GİRİŞ
#                                           anahtarı; TSK-226b, 2026-09-26). `--tenant` DEĞİL: CP'nin
#                                           öteki sırrı (`HINDSIGHT_CP_DATAPLANE_API_KEY`) kiracı
#                                           anahtarının kopyasıdır ve `--tenant` yazar. Kanıt CP'nin
#                                           kendi giriş ucudur (POST /api/auth/login, gövde `key`):
#                                           yeni → 200, eski → 401. Kasaya BAĞLIDIR: doğru yol
#                                           `--cp --vault` (aşağıda); eski yol uyarıyla koşar.
#   sudo ./sir_rotasyon.sh --api-sunucu   → API_SERVER_KEY (bot ağ geçidinin dinleyici anahtarı; G3b, 2026-10-01). TEK
#                                           sır, DÖRT `.env` kopyası — kök + her sohbet profili (Hermes PROFİL
#                                           kapsamı: `/p/<ad>/` isteğinin anahtarı o profilin `.env`inden okunur) — +
#                                           Telegram dinleyicisinin credential'ı; referans Agent render hedefi. Kanıt:
#                                           botlar ETKİNSE `/health/detailed` yeni → 200 · eski → 401; değilse
#                                           "KANIT: ölçülemedi — … etkin değil (<durum>)" satırı, çıkış 0. Kasaya
#                                           BAĞLIDIR: doğru yol `--api-sunucu --vault`; İLK değer RUNBOOK borusuyla.
#   sudo ./sir_rotasyon.sh --kapi-bot <sef|bekci|karne> → BOT_KEY_<AD> (bir botun KAPI tüketici anahtarı — `bot_<ad>`
#                                           key-auth; G3b Task 3, 2026-10-01). TEK bot, DÖRT kopya birlikte (operatör
#                                           K-G3b-1): Agent render hedefi `/etc/meridian/bot_key_<ad>` (REFERANS) ·
#                                           `.env-apisix` · rapor profili `.env` · sohbet profili `.env`. Ad `_SOHBET_BOTLARI`
#                                           ile TAM eşleşmeli (başka her ad hiçbir şeye dokunmadan reddedilir; liste bu
#                                           satırda belge olarak durur — ayrışma çivisi v604 C3). Kapı RESTART (`$env://`
#                                           açılışta), bot ağ geçidi yalnız ETKİNSE; motor yeniden BAŞLAMAZ. Kanıt: kapı
#                                           `/llm/v1/models` yeni → 200 · eski → 401. Kasaya BAĞLIDIR: doğru yol
#                                           `--kapi-bot <ad> --vault [--uret]`.
#   sudo ./sir_rotasyon.sh --tohumla-sohbet → bot ağ geçidinin sohbet `.env`lerinin İLK yazımı (G3b Task 4, 2026-10-01;
#                                           operatör K-G3b-2). ROTASYON DEĞİLDİR: değer üretmez, sormaz, kasaya yazmaz.
#                                           Hedef + alan kümesi KOPYA TABLOSUNDAN (`_SOHBET_KOKU` altına yazan `env`
#                                           satırları), değer her sırrın REFERANSINDAN (Agent render hedefi). YOK olan
#                                           dosyayı 0600 ubuntu:ubuntu yazar; VAR olana DOKUNMAZ (eksik alanı ADIYLA söyler
#                                           → çıkış 3, elle). Dizin ya da referans yoksa HİÇBİR ŞEY yazmaz. Restart YOK.
#                                           `--kuru` ile. SIRA: A0 site.yml (dizinler) → kasaya ilk değer + Agent render
#                                           (RUNBOOK) → BU → ilk rotasyon. Önce rotasyon koşarsa ön-denetim "hedef dosya
#                                           YOK" der ve buraya yollar.
#   sudo ./sir_rotasyon.sh --geri-al <yedek-dizini> → YEDEKTEN GERİ ALMA (TSK-261, 2026-10-01). ROTASYON DEĞİLDİR: bir
#                                           koşumun yedeğindeki (`/root/sir-yedek-<UTC ts>-<alt>/`) kopyaları üretim
#                                           yollarına geri koyar — YALNIZ o alt komutun tablo yolları (alt komut dizin
#                                           adından), bağ İZLEMEDEN (yardımcının fd-tabanlı yazım çekirdeği), mod/sahip
#                                           yedekten. Kasa yedeği (`vault/`) GİRMEZ (kasa reçetesinin işi). DOSYA BÜTÜN
#                                           DÖNER: yedekten sonra değişmiş BAŞKA alanların ADLARI basılır (değer asla).
#                                           Yazmadan ÖNCE mevcut hâli yeni bir yedeğe alır (yolu basılır — geri almanın
#                                           geri alınması o yedekten). Restart YAPMAZ, birim listesini basar. Yazımda
#                                           reddedilen hedef ADIYLA söylenir, ötekiler geri konur (çıkış 1); geri konacak
#                                           dosya YOKSA çıkış 1. Bütün geri alma reçeteleri bunu gösterir. `--kuru` ile.
#   ... --kuru                            → KURU KOŞUM: ne yazılacağını + hangi birimin yeniden
#                                           başlayacağını listeler, HİÇBİR ŞEY yazmaz
#   (koşullu birim) `_KOSULLU_BIRIMLER` YALNIZ ETKİNSE yeniden başlar; değilse "ATLANDI (etkin değil: <durum>)"
#   sudo ./sir_rotasyon.sh --<alt> --vault  → KASADAN ROTASYON (TSK-064 Faz-2 DALGA-2, 2026-09-14):
#                                           yeni değer operatörden alınır (`--uret` ile betik İÇİNDE
#                                           üretilir — aşağıda) ve ÖNCE KASAYA konur;
#                                           Agent yan dosyaları render eder, betik render'ı ÖLÇER
#                                           (kanonik tek-değer kopyasının kasadaki değere eşitlenmesi,
#                                           bekleme SINIRLI), eski kanal kopyalarını AYNI pencerede
#                                           KASADAN gelen değerle yazar (iki-kanal dönemi), tüketicileri
#                                           yeniden başlatır ve kanıtı ölçer. `--kuru` ile birleşir.
#                                           KAPSAM: yalnız envanterde `rotasyon_siri` ile kasaya BAĞLI
#                                           sırlar; bağlı olmayanlar ADIYLA beyan edilir ve eski yolla döner
#                                           — kopyası bir Agent RENDER HEDEFİYSE beyan bir UYARIDIR (eski
#                                           yolun yazımı kasadaki değerle ezilebilir; 2026-09-17'de yalnız
#                                           `--db`ydi, 2026-09-24'ten beri böyle bir sır YOK). Her kasa sırrı
#                                           AYRI sorulur; boş bırakılan o tur DÖNMEZ ve ADIYLA söylenir.
#   sudo ./sir_rotasyon.sh --<alt> --vault --uret → KASADAN ROTASYON, DEĞER BETİK İÇİNDE (TSK-226c,
#                                           2026-09-26): İSTEM YOK — değer eski yolun AYNI yöntemiyle
#                                           üretilir (`_uret`; alt komutun sınıfı `_uret_sinifi`nde, eski yol
#                                           gövdeleriyle ayrışması çivili — v557), uzunluğu denetlenir, render
#                                           hedefindeki ESKİ değerle AYNI olamaz, hiçbir yere BASILMAZ. Takma
#                                           ad, render kanıtı, eski kanal, restart, kanıt ve geri alma AYNEN —
#                                           yalnız değerin KAYNAĞI değişir. Yalnız --kapi | --tenant | --dash |
#                                           --apisix-admin | --api-sunucu | --kapi-bot <ad>; --openrouter (anahtarı sağlayıcı üretir) ve --db
#                                           (kendi dalı, bu turun kapsamı dışı) AÇIK hatayla reddedilir,
#                                           --vault'suz verilemez; --cp --vault değeri ZATEN üretir (bayrak
#                                           etkisiz, söylenir). `--kuru` ile birleşir. Hedef kullanım:
#                                           --tenant --vault --uret (Rol-1 bir isteme sır değeri GİREMEZ;
#                                           eski yolun yazımı Agent render'ıyla ezilir).
#   sudo ./sir_rotasyon.sh --db --vault   → KASADAN DB PAROLASI (TSK-064, 2026-09-24) — genel döngü DEĞİL,
#                                           kendi dalı (`vault_db_rotasyon`): kasa TAM DSN taşır, sır yalnız
#                                           PAROLA alanıdır ve ikinci hakikat noktası GERİ ALINAMAZ (`ALTER
#                                           ROLE`). Sıra: kasa → render kanıtı → ALTER ROLE → restart → kanıt;
#                                           ALTER'dan önceki her düşüş kasayı KV v2 sürümüyle geri alır.
#                                           Tasarım: docs/TASARIM-SIR-DB-KASA-2026-09-21.md. `--kuru` ile birleşir.
#   sudo ./sir_rotasyon.sh --cp --vault   → KASADAN CP ERİŞİM ANAHTARI (TSK-226b, 2026-09-26) — genel döngü
#                                           DEĞİL, kendi dalı (`vault_cp_rotasyon`): değer betik İÇİNDE
#                                           üretilir (SORULMAZ, BASILMAZ — bu sırrın döndürülme sebebi bir
#                                           GÖRÜNTÜLEME sızıntısıydı, yapıştırma bir yüzey daha açardı),
#                                           kanıtın NEGATİF ayağı ESKİ değeri KASADAN okur, geri alma reçetesi
#                                           EVREYE göredir (KV v2 sürümü). Sıra: kasa → render kanıtı → eski
#                                           kanal → restart → kanıt (CP giriş ucu). `--kuru` ile. Eski kanal
#                                           2026-09-29'dan beri YOK (`.env-cp` EMEKLİ — TSK-064 iki-kanal):
#                                           adım kopya tablosundan türer ve "YOK" der.
#                                           TAKMA AD (`ayni_deger`, Rol-1 hükmü 2026-09-14): aynı değerin
#                                           TEK kasa yolu vardır; rotasyon BİRİNCİL yola yapılır ve takma
#                                           adlar onu otomatik izler. Restart listesi kasa YOLUNDAN toplanır
#                                           (addan değil) — yani takma adın tüketicileri de kapsanır.
#   sudo ./sir_rotasyon.sh --<alt> --esitle → EŞİTLEME (TSK-181, 2026-09-13): değer ÜRETİLMEZ, SORULMAZ,
#                                           BASILMAZ; sırrın tablodaki İLK satırı (REFERANS) okunur, AYRI
#                                           düşen dosya/env/url kopyalarına yazılır (api/sql kanalları
#                                           beyanla atlanır), yedek alınır, RESTART YAPILMAZ (tüketici
#                                           birimler basılır); kanıt: envanter yeniden EŞİT + (--openrouter)
#                                           kapı chat 200. `--kuru` ile birleşir. Bkz. `esitle` şerhi.
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
# profilleri; 2026-09-29'a dek `/opt/hindsight/.key` de) root altında da MEVCUT sahip ve izinle yazılır: root'un
# yazıyor olması, dosyayı root'a DEVRETMEK değildir.
#
# DEĞER ÜRETİMİ. `--kapi`/`--db`/`--dash`/`--kapi-bot <ad>`: `openssl rand -base64 36 | tr '+/' '-_'` → 48 karakter
# URL-güvenli (bot anahtarlarının A1'deki mevcut değerleri de 48 bayt — ölçüldü 2026-09-30). `--tenant`, `--cp` ve `--api-sunucu`: `openssl rand -hex 32` → 64 hex (Hermes dinleyicisi ≥16
# karakter ve yer tutucu olmayan değer ister — Rol-1 G3b-R5; CP anahtarının biçim beklentisi
# YOK — hindsight-control-plane 0.9.2 `api/auth/login` yalnız sabit-zamanlı eşitlik kıyaslar; birim
# şerhinin 2026-09-01 üretim reçetesi de `openssl rand -hex 32`dir). Üretimden SONRA uzunluk denetlenir;
# boş ya da yalnız boşluk olan değer bir ARIZADIR (bir kez ölçüldü: boş credential dosyası birimi
# sessizce yetkisiz bıraktı) ve betik durur. `--openrouter` üretmez: iki anahtarı operatör
# OpenRouter panosunda üretir ve buraya `read -s` ile yapıştırır. `--<alt> --vault --uret` (TSK-226c)
# AYNI `_uret`i çağırır; alt komut → sınıf eşlemesi `_uret_sinifi`ndedir ve eski yol gövdeleriyle
# ayrışması çivilidir (v557 A1) — kasa yolu eski yoldan FARKLI bir değer biçimi üretemez.
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
# çıkış 2 verir. Sağlık ucu tanımlı OLMAYAN birim beklenmez ve hazır SAYILMAZ — satır bunu söyler.
# `hindsight-cp.service` 2026-09-26'ya kadar bu sınıftaydı; artık `/api/health` ucuyla beklenir (kabul
# `http` — gerekçe `_hazir_uc` şerhinde) çünkü `--cp`nin kanıtı restart'ın hemen ardından CP'ye gider.
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
# dosyayı bağ İZLEMEDEN kopyalar (yardımcının `kopyala` işlemi — mod/sahip korunur, kaynak bağsa yedek
# ALINMAZ ve rotasyon başlamaz; TSK-261). Ad SANİYE taşır: aynı sırrı gün içinde iki kez döndürmek ilk yedeği
# EZMEZ. Geri alma reçetesi RUNBOOK'ta değil burada, çünkü okunacağı an bu betiğin çıktısıdır:
# kasasız yol → `sudo ./sir_rotasyon.sh --geri-al <yedek>` + ilgili birimleri yeniden başlat. `--vault` yolu
# (TSK-064, 2026-09-26) → ÖNCE kasa: `vault kv rollback -version=<N> <yol>` (N = `kv put` ÖNCESİ
# `current_version`, her kasa yolu için ayrı kaydedilir), SONRA dosya — ters sırada Agent render'ı
# geri konan dosyayı kasadaki yeni değerle tekrar ezer. `kv rollback`un kendisi düşerse (politika · ağ ·
# mühür) YEDEK YOL üç kasa dalında da AYNIDIR (genel döngü TSK-064(b), 2026-09-27): `kv put` ÖNCESİ kasadan
# okunan ESKİ değer `<yedek>/vault/<kasa yolu>`dadır (0600 root) ve STDIN'le `vault kv put <yol> value=-` ile
# geri konur — değer argv'ye girmez. Reçete bunu her rollback satırının altında A1'de OLDUĞU GİBİ koşulacak
# TEK SATIR olarak basar (TSK-237, 2026-09-27; üç dalın ortak `_geri_koy_satiri`si):
#   sudo bash -c '<sabit gövde>' _ <VAULT_ADDR> <vault ikilisi> <yönetici jetonu> <yedek dosyası> <kasa yolu>
# Kasa ortamı betiğin KENDİSİNİNKİDİR: jeton `login -no-print -` ile STDIN'den (`VAULT_TOKEN=` yok), oturum
# geçici bir HOME'da ve çıkışta silinir; yedek sudo ile okunur ve `tr -d` ile STDIN'e borulanır; yedek yoksa
# ya da boşsa kasaya HİÇBİR ŞEY yazılmadan durur.
#
# YAPMADIKLARI (burada olmayan şey, burada yapılmayacak şeydir): kanal geçişi yapmaz (o
# `sir_credential_gecis.sh`); drop-in kurmaz; Vault'a dokunmaz; operatörün YEREL `.env` kopyasını
# eşitlemez (Rol-1'in işi, kapsam dışı); pano parola oturumunu etkilemez (ayrı sır).
# =================================================================================================
set -euo pipefail

# ÇALIŞMA DİZİNİ `/` + BETİĞİN MUTLAK DİZİNİ (TSK-262 düzeltme turu 1; inceleme K1 — DOSYA İÇİ kısmi önlem). `python3 -c`
# sys.path'in başına ÇALIŞMA DİZİNİNİ koyar: RUNBOOK biçimi `cd /opt/meridian && sudo ./deploy/oracle-a1/sir_rotasyon.sh …` ile
# ubuntu'nun yazabildiği dizindeki bir `yaml.py`/`ast.py` root olarak koşardı (inceleme sondası `cwd_sonda/`). Betik dizini ÖNCE
# mutlak (fiziksel) yola çözülür — göreli çağrıda da depo girdileri ($VAULT_ENVANTER · $VAULT_POLITIKA_URETICI) bulunur — SONRA
# `cd /`. İkinci katman: bütün yorumlayıcı çağrıları `-I` (yalıtılmış kip: ne çalışma dizini ne betik dizini ne `PYTHON*` ortamı
# sys.path'e girer; A1'de `sudo python3 -I -c "import yaml"` sistem PyYAML'ını bulur — Rol-1 ölçümü 2026-10-02). KALAN (ayrı kalem
# TSK-265): betiğin ve girdilerinin KENDİSİ ubuntu'nun yazabildiği ağaçta — A0 root sahipli kurulum yeri. Reçetelerdeki `$0`
# operatörün KENDİ kabuğunda (çağrı dizininde) koşar; değişmez. Çiviler: v613 K1a · K1b · K1c · K1d.
BETIK_DIZINI="$(cd "$(dirname "$0")" && pwd -P)" || { echo "!! betiğin dizini çözülemedi ($0) — HİÇBİR ŞEY yapılmadı" >&2; exit 1; }
cd /

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
#: KAPININ YÖNETİM YÜZEYİ — proxy'den AYRI bir PORTTUR (9180, yalnız loopback) ve bu yüzden ayrı
#: bir sabittir: `KAPI_KOK`tan türetilemez. `--apisix-admin`in kanıtı buraya gider
#: (`GET /routes` — yeni anahtar 200, eski 401): yönetim anahtarının ölçülebildiği tek yüzey.
ADMIN_KOK="${SIR_ROT_ADMIN:-http://127.0.0.1:9180/apisix/admin}"
#: KONTROL PANELİ (hindsight-control-plane, TSK-226b). Birim `HOSTNAME=localhost` ile 9999'a bağlanır ve
#: localhost 127.0.0.1'e çözülür (`ss` ile ölçüldü, A1 2026-09-01). İki uç kullanılır, ikisi de
#: KİMLİKSİZDİR (imajın middleware'i `PUBLIC_PATTERNS`): hazırlık `/api/health`, kanıt `/api/auth/login`.
#: KAYNAK ÖLÇÜMÜ (A1'de DEĞİL): vectorize-io/hindsight etiketi v0.9.2 (= imaj pini 0.9.2), okundu
#: 2026-09-26 — `hindsight-control-plane/src/middleware.ts` · `src/app/api/auth/login/route.ts` ·
#: `src/app/api/health/route.ts`.
CP_KOK="${SIR_ROT_CP:-http://127.0.0.1:9999}"
#: BOT AĞ GEÇİDİ (Hermes `api_server`, `meridian-botlar.service`; G3b 2026-09-30). Varsayılan dinleyici
#: 127.0.0.1:8642. Hazırlık ucu `GET /health` KİMLİKSİZDİR ve `{"status":"ok"}` döner — Rol-1 A1'deki Hermes
#: kaynağında ölçtü (2026-09-30). Birim YALNIZ ETKİNSE yeniden başlar (`_KOSULLU_BIRIMLER`), yani uç ancak o
#: zaman yoklanır. Telegram dinleyicisinin (`meridian-telegram.service`) sağlık ucu YOKTUR.
BOTLAR_KOK="${SIR_ROT_BOTLAR:-http://127.0.0.1:8642}"

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

#: KASA (TSK-064 Faz-2 DALGA-2). Üçü de ortamdan geçilebilir ve bu kanca DEĞİL sözleşmedir:
#: A1'de yollar sabittir, çivi başka bir kökte koşar.
VAULT_BIN="${VAULT_BIN:-/usr/local/bin/vault}"
VAULT_JETON_DOSYASI="${VAULT_TOKEN_FILE:-/etc/vault/admin.token}"
export VAULT_ADDR="${VAULT_ADDR:-http://127.0.0.1:8200}"
#: Envanter — `vault_kv` ve `vault_dosyalar` bloklarının TEK kaynağı. Betik `deploy/oracle-a1/`
#: altında yaşar, envanter bir üst dizinde (`deploy/`).
VAULT_ENVANTER="${VAULT_ENVANTER:-$BETIK_DIZINI/../sir_envanteri.yaml}"
#: Agent'ın render ARALIĞI (`RENDER_ARALIGI`) bu üreticide TEK yerde yaşar ve üretilen `agent.hcl`in
#: `static_secret_render_interval`ı oradan yazılır. Eski yolun Agent hedefi uyarısı sayıyı BURADAN
#: okur (`_render_araligi_metni`) — uyarıya elle yazılmış bir "1 dk", kadans değişince sessizce yalan
#: olurdu (TSK-064 takip (2), 2026-09-17). Ortamdan geçilebilir olması VAULT_ENVANTER ile aynı gerekçe.
VAULT_POLITIKA_URETICI="${VAULT_POLITIKA_URETICI:-$BETIK_DIZINI/../../ops/vault_politika_uret.py}"
#: YAML okuyan python — `py()` yardımcısı stdlib'le yetinir (sudo python3), bu ise PyYAML ister.
#: A1'de sistem python3'ü yeterlidir; ayrı bir kanca olması çivinin kendi yorumlayıcısını
#: verebilmesi içindir (sanal ortam dışındaki python3'te PyYAML olmayabilir). MONOTONİK saat de
#: buradan okunur (`_saat_oku`, stdlib yeter): yeni bir yorumlayıcı bağımlılığı DEĞİLDİR.
PYTHON_BIN="${PYTHON_BIN:-python3}"
#: RENDER BEKLEME — SINIRLI. Agent STATİK (KV-v2) sırları `static_secret_render_interval` ile
#: yeniden render eder ve o aralık `ops/vault_politika_uret.py::RENDER_ARALIGI`de TEK yerde
#: yaşar (bugün 1 dk). Tavan o aralığın ~1,5 katıdır: DAR tavan sağlıklı ama yavaş bir render'ı
#: "ölçülemedi" sayar, GENİŞ tavan bakım penceresini uzatır. İki sayı AYRI gerçeklerdir ("ne
#: sıklıkla yenilenir" ile "ne kadar beklerim") ve bu yüzden kopya değil komşudurlar — biri
#: ötekinden TÜRETİLMEZ, ama biri değişince öteki GÖZDEN GEÇİRİLİR.
VAULT_RENDER_TAVAN_S="${VAULT_RENDER_TAVAN_S:-90}"
VAULT_RENDER_ARALIK_S="${VAULT_RENDER_ARALIK_S:-3}"

ISLIK=""          # 0700 çalışma dizini (değer taşıyan geçici dosyalar YALNIZ burada yaşar)
YEDEK=""          # bu koşumun yedek dizini
KURU=0            # --kuru: hiçbir yazım yok
#: --uret (TSK-226c, 2026-09-26): kasa yolunun İSTEMİ yerine değer betik İÇİNDE üretilir (`_vault_uret`).
#: Okuyanlar: `vault_rotasyon` (istem noktası) · `_vault_kuru_rapor` (plan satırı) · `_deger_kaynagi_beyani`.
URET=0
GERI_AL_LISTESI=""  # negatif kontrolün geri alacağı <yedek>|<hedef> çiftleri
#: NEGATİF KONTROLÜN BOZUK/BOŞ DEĞERLE YENİDEN BAŞLATTIĞI BİRİMLER. Dosyaları geri almak YETMEZ:
#: birim değeri AÇILIŞTA okur (apisix `$env://` çözümünü yalnız açılışta yapar, systemd
#: `LoadCredential`ı yalnız açılışta kopyalar). Trap bu kümeyi geri almadan SONRA yeniden başlatır.
NK_BIRIMLER=""
#: `_api_yaz` HATA METNİNİN BAĞLAMI (TSK-064 takip (5), 2026-09-17) — YALNIZ METNİ seçer; yazım,
#: sıra ve çıkış kodu iki bağlamda da AYNIDIR. `eski`: `openrouter()` motor deposunu restart ve
#: kanıttan SONRA yazar, yani hata anında rotasyon kanıtlanmıştır. `kasa`: `vault_rotasyon` aynı
#: kopyayı eski kanal adımında, restart ve kanıttan ÖNCE yazar — orada "kanıtlandı" cümlesi YANLIŞ
#: olurdu. Ortamdan GEÇİLEMEZ (burada atanır): bağlam bir kanca değil, koşan akışın kendisidir.
YAZIM_AKISI="eski"
#: KASA YOLU `--db --vault` EVRESİ (TSK-064, 2026-09-24) — `_geri_alma_recetesi` buna bakarak DOSYA
#: kopyası reçetesi yerine kasa yolunun reçetesini basar (`_db_kasa_recetesi`): o yolda render hedefi
#: Agent'ındır, dosyayı yedekten geri koymak bir sonraki render'da EZİLİR. Boş = bu koşum o yol değil.
#: Sıra: `yedek` (yedek alındı, kasaya yazılmadı) → `kasa` (kv put denendi, ALTER yok) → `geri` (kasa
#: ESKİ DSN'e geri alındı ve ÖLÇÜLDÜ) ya da `alter` (ALTER ROLE UYGULANDI — geri alınamaz kanal).
DB_KASA_EVRE=""
DB_KASA_SURUM=""     # kv put ÖNCESİ current_version — geri almanın hedef sürümü
DB_KASA_YOL=""       # kasa yolu (envanterden)
DB_KASA_HEDEF=""     # Agent render hedefi (envanterden)
DB_ROL=""            # Postgres rolü (kopya tablosunun `sql` satırından)
DB_GERI_YONTEM=""    # kasa geri alma yolu: rollback ya da (düşerse) eski DSN kv put
#: KASA YOLU `--cp --vault` EVRESİ (TSK-226b, 2026-09-26) — `DB_KASA_EVRE`nin CP ikizi: `_geri_alma_recetesi`
#: buna bakarak dosya kopyası reçetesi yerine kasa yolunun reçetesini basar (`_cp_kasa_recetesi`).
#: Sıra: `yedek` (yedek alındı, kasaya yazılmadı) → `kasa` (kv put denendi; eski kanal YAZILMADI, CP
#: YENİDEN BAŞLATILMADI) → `yayim` (eski kanal yazımı başladı; restart + kanıt bu evrede). Boş = bu yol değil.
CP_KASA_EVRE=""
CP_KASA_SURUM=""     # kv put ÖNCESİ current_version — geri almanın hedef sürümü
CP_KASA_YOL=""       # kasa yolu (envanterden)
CP_KASA_HEDEF=""     # Agent render hedefi (envanterden)
#: KASA YOLU GENEL DÖNGÜ EVRESİ (TSK-064 takibi, 2026-09-27; TSK-226c incelemesi BULGU 1) — `DB_KASA_EVRE`/`CP_KASA_EVRE`in
#: genel döngü (`vault_rotasyon`: kapi · tenant · dash · apisix-admin · openrouter) ikizi. `_geri_alma_recetesi` buna
#: bakarak dosya reçetesinin ÖNÜNE kasa geri alımını koyar (`_genel_kasa_recetesi`). Boş = bu koşum bu yol değil.
#: Sıra: `yedek` (yedek alındı, kasaya yazılmadı) → `kasa` (en az bir `kv put` DENENDİ). Evre GERİ GİTMEZ: iki sırlı
#: turda (`--openrouter`) ikinci sırrın ön kapısı düşse de ilk sır kasadadır.
GENEL_KASA_EVRE=""
#: `<kasa yolu>\t<kv put ÖNCESİ current_version>\t<render hedefi>` satırları — put'u DENENEN her yol, yazım sırasıyla.
#: Yol buraya ESKİ değeri `$YEDEK/vault/<yol>`a yedeklendikten SONRA girer (TSK-064(b)): reçetenin yedek yol satırı türetilir.
GENEL_KASA_SATIRLARI=""
KASA_SURUM=""        # `_kasa_surumu`nun son okuması — üç dal (genel · db · cp) buradan kopyalar
RENDER_GECEN=""      # `_render_bekle`nin ölçtüğü süre (s) — çağıran basar
SAAT_MS=""           # `_saat_oku`nun son okuması (ms, MONOTONİK — yalnız iki okumanın FARKI anlamlı)
GECEN_S=""           # `_gecen_s`in ölçtüğü süre (TAM saniye, aşağı yuvarlanır)

die()      { echo "!! $*" >&2; exit 1; }
olcum_yok(){ echo "!! ÖLÇÜLEMEDİ: $*" >&2; exit 2; }
oldu()     { echo "  ✓ $*"; }
adim()     { echo "-- $*"; }

# SAAT — GEÇEN SÜRE MONOTONİK SAATTEN ÖLÇÜLÜR, DUVAR SAATİNDEN DEĞİL. Üç ölçüm yeri de buradan okur
# (`_hazir_bekle` · `_render_bekle` · pencere B) ve saat TEK satırda seçilir: iki okuma yeri iki
# ayrı saat seçebilirdi (tek-kaynak yasası). VAKA 2026-09-24 (TSK-213, Rol-1 sondası, yerel Mac):
# süreç askısı (uyku/güç) sırasında 12 s'lik sınırlı bir döngüde DUVAR saati 62,8 s, MONOTONİK
# saat 13,1 s ilerledi (iki ~25 s sıçrama). Süre `date +%s` ile ölçülürken askı "bekleme" sayılıyor,
# birim hazır olsa da tavan "aşılıyor" ve betik sahte ÖLÇÜLEMEDİ ile çıkıyordu (v447 M2 · M4 · N1).
# `time.monotonic()` askıda İLERLEMEZ (macOS `mach_absolute_time`, Linux `CLOCK_MONOTONIC`) ve saat
# ayarından (NTP adımı) etkilenmez. Canlıda (A1, sunucu VM) uyku askısı beklenmez; askı yoksa iki
# saat aynı süreyi ölçer ve gerçekten açılmayan birim yine tavanda ÖLÇÜLEMEDİ olur (v542 S4).
# Tavan kıyası ve "N s" satırı TAM saniyedir; `date +%s` farkı saniye sınırında 1 s fazla
# sayabiliyordu, burada gerçek fark aşağı yuvarlanır.
# Okunamayan saat ÖLÇÜLEMEDİ'dir — duvar saatine DÜŞÜLMEZ (düşmek arızayı geri getirmek olurdu).
# `_saat_oku [ek]` — ek, ÖLÇÜLEMEDİ satırına çağıranın bağlamını ekler (ör. ön kapıda "hiçbir şey yazılmadı").
_saat_oku() {
  SAAT_MS="$("$PYTHON_BIN" -I -c 'import time; print(int(time.monotonic() * 1000))')" \
    || olcum_yok "monotonik saat okunamadı ($PYTHON_BIN) — bekleme tavanı ve süre ölçülemez${1:+ — $1}"
}
# `_gecen_s <başlangıç SAAT_MS>` → `GECEN_S`. Çağıran `$( )` DEĞİL doğrudan çağırır: alt kabukta
# `olcum_yok` yalnız alt kabuğu bitirirdi.
_gecen_s() { _saat_oku; GECEN_S=$(( (SAAT_MS - $1) / 1000 )); }

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
#
# REFERANS KURALI — SIRA BİR SÜS DEĞİL, SÖZLEŞMEDİR. Bir sırrın tablodaki İLK satırı o sırrın
# REFERANS kopyasıdır: `_envanter_esitlik` ötekileri ona kıyaslar, `esitle` değeri ondan okur
# (ikisi de `[ "$sir" != "$onceki" ]` ile ilk görülen satırı seçer; aynı sırrın satırları bu
# yüzden BİTİŞİK durur). Rotasyon yazımı (`_yaz`), yedek, negatif kontrol ve `--vault` render
# ölçümü sıradan BAĞIMSIZDIR — hepsi pencere içinde, yeniden başlatmadan ÖNCE bütün satırları
# yazar; sıra yalnız YARIDA düşen bir koşumda hangi dosyaların yazılmış olduğunu değiştirir.
# TSK-064 (d-1), 2026-09-17 (Rol-1 A1 ölçümü `--envanter`: karşılaştırılabilen her kopya EŞİT):
#   · `dash MERIDIAN_DASH_TOKEN env /opt/meridian/.dash.env …` satırı ÇIKTI — dosya A1'de 2026-09-14
#     17:46Z operatör kararıyla SİLİNDİ (yedek /root/sir-yedek-20260914T174655Z-dash-env). Satır
#     kalsaydı `--dash` yazım sırasında "hedef dosya YOK" ile yarıda düşerdi. Dosya TARAMADA kalır
#     (`_taranan_dosyalar` şerhi): geri doğarsa rotasyonun yazmadığı bir kopyadır.
#   · `OPENROUTER_API_KEY` ve `APISIX_ADMIN_KEY`in referansı Vault Agent'ın TEKİL render hedefine
#     taşındı (aşağıdaki "REFERANS SIRASI" şerhi). `.env-apisix` satırları KOPYA olarak kalır.
# Çivi: `tests/test_sir_referans_hizasi_v520.py`.
# TSK-064 İKİ-KANAL KAPANIŞI, 2026-09-29 (Rol-1 kararı; dash-token (d-1) emsali) — ÜÇ satır ÇIKTI:
#   · `tenant … dosya /opt/hindsight/.key` — tek okuyucusu Rol-1 araçlarıydı (`deploy/hindsight/hafiza_sor.sh`
#     + `sayfa_oku.sh`); araçlar anahtarı artık `sudo -n cat <render hedefi>` borusundan okur.
#   · `tenant … env /opt/hindsight/.env-cp [HINDSIGHT_CP_DATAPLANE_API_KEY]` ve `cp … env /opt/hindsight/.env-cp
#     [HINDSIGHT_CP_ACCESS_KEY]` — hindsight-cp `51-env-cp-kaldir.conf` ile YALNIZ `.env-cp.vault`ı (Agent) okur.
#   Satırlar kalsaydı rotasyon okuyucusuz dosyaları "tazeleyip" yaşatır, operatör kaldırdıktan sonra da
#   `--tenant`/`--cp` "hedef dosya YOK" ile yarıda düşerdi. İki sırrın tablodaki TEK satırı artık REFERANS
#   render hedefidir. Satırlar envanterde SİLİNMEDİ — `rotasyon_kopyalari.emekli_kopyalar`da tarihli durur;
#   dosyaların diskte kalıp kalmadığını `--envanter` `_emekli_kopyalar` listesiyle ölçer (bedel yasası: satır
#   çıkınca `.key`i EŞİT/AYRI diye gören tek mekanizma da çıkıyordu). Çivi: tests/test_iki_kanal_kapanisi_v590.py C.
#: SOHBET BOT LİSTESİ — KABUKTAKİ TEK LİSTE (G3b Task 2, 2026-10-01; operatör 2026-09-30 "bot sayısından bağımsız
#: tasarım": kadroda 21 bot — 3 canlı + dalga 1/2/3). Bot başına her tablo satırı (`_sohbet_satirlari`) ve taranan
#: dosya (`_taranan_dosyalar`) bu iki sabitten DÖNGÜYLE türer: elle yazılan satır sayısı bot sayısıyla BÜYÜMEZ ve yeni
#: bot = bu listeye bir ad (+ A0 listesi + kadro + kapı tüketicisi + kasa girdisi). KOPYA KAÇINILMAZ: betik A1'de
#: PyYAML'sız `--kopyalar` basar ve A0 değişkenlerini okumaz → iki yönlü eşitlik çivisi v604 B9 (bu liste =
#: `deploy/ansible/roles/meridian_a1/defaults/main.yml` `sohbet_profil_adlari` [sıra dahil] = `deploy/hermes/kadro.yaml`
#: `durum: aktif`; kök = `sohbet_kok_dizini`). Envanter aynası (`rotasyon_kopyalari` · takma ad `kopya_kaynaklari`)
#: bu tablonun ÇIKTISINDAN `ops/sir_envanteri_bot_uret.py` ile üretilir (`--kontrol` çivisi v604 B12).
_SOHBET_KOKU="/home/ubuntu/.hermes-botlar"
_SOHBET_BOTLARI="sef bekci karne"

#: TABLO BORUSU — OKUYAN TAMAMINI OKUR (G3b 2026-10-01). `_kopyalar` artık iki heredoc + döngü
#: `echo`larıdır; `_kopyalar | awk '…{print; exit}'` gibi ERKEN çıkan bir okuyucu boruyu kapatır, sonraki `echo` SIGPIPE
#: alır ve `set -o pipefail` altında atama 141 ile `set -e`yi tetikler — koşum ilk satırı bulduğu an SESSİZCE ölür
#: (ölçüldü: `--api-sunucu` çıkış 141 "echo: write error: Broken pipe"; tek-`cat` tabloda yarışa bağlı gizliydi). İlk
#: eşleşme `!y {…; y=1}` ile alınır, `exit` yalnız `END` içinde. Çivi: v604 B14 (statik).
#: `_sohbet_satirlari <alt> <sır> <alan>` — her sohbet profilinin `.env`i için TEK `env` satırı (mod/sahip `koru`:
#: dosyayı tohumlama 0600 ubuntu yazar, rotasyon izni KORUR — hermes rapor profilleri emsali).
_sohbet_satirlari() {
  local b
  for b in $_SOHBET_BOTLARI; do
    echo "$1 $2 env $_SOHBET_KOKU/profiles/$b/.env $3 koru koru -"
  done
}

#: TABLO ÜÇ PARÇADIR (G3b, 2026-10-01): sabit satırlar iki heredoc'ta, bot başı satırlar `_sohbet_satirlari` döngüsünde.
#: Bir sırrın satırları yine BİTİŞİKTİR (referans kuralı — v604 B2): kiracı anahtarının sohbet kopyaları referans
#: satırının HEMEN ardından, `api-sunucu` bloğu tablonun sonunda.
#: `api-sunucu` (API_SERVER_KEY — G3b): REFERANS Agent render hedefi (`vault_kv.api_server_key.hedef`), ardından kök
#: `.env` (dinleyici açılışı) ve her sohbet profilinin `.env`i (Hermes PROFİL kapsamı — `/p/<ad>/` isteğinin anahtarı o
#: profilin `.env`inden okunur, ölçüm Rol-1 2026-09-30). Telegram dinleyicisi aynı değeri credential'dan okur (55
#: drop-in) ve onun kaynağı referans satırıdır. Kiracı anahtarının sohbet kopyası `HINDSIGHT_API_KEY` alanıdır
#: (Hermes hafıza sağlayıcısı, profil `.env`i).
_kopyalar() {
  cat <<'KOPYA_SON'
kapi KAPI_APIKEY dosya /etc/meridian/kapi_apikey - 0400 root:root -
kapi KAPI_APIKEY env /opt/apisix/.env-apisix BOT_KEY_MERIDIAN koru koru -
tenant HINDSIGHT_API_TENANT_API_KEY dosya /etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY - 0400 root:root -
KOPYA_SON
  _sohbet_satirlari tenant HINDSIGHT_API_TENANT_API_KEY HINDSIGHT_API_KEY
  cat <<'KOPYA_SON'
db HINDSIGHT_DB_PAROLA sql hindsight - - - -
db HINDSIGHT_DB_PAROLA url /etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL - koru koru -
dash MERIDIAN_DASH_TOKEN dosya /etc/meridian/dash_token - 0400 root:root -
openrouter NOUS_API_KEY dosya /etc/meridian/nous_api_key - 0400 root:root -
openrouter NOUS_API_KEY api /api/secrets/NOUS_API_KEY - - - -
openrouter OPENROUTER_API_KEY dosya /etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY - 0400 root:root -
openrouter OPENROUTER_API_KEY env /opt/apisix/.env-apisix OPENROUTER_API_KEY koru koru -
openrouter OPENROUTER_API_KEY env /opt/apisix/.env-apisix OPENROUTER_AUTH koru koru Bearer
openrouter OPENROUTER_API_KEY env /opt/hindsight/.env HINDSIGHT_API_REFLECT_LLM_1_API_KEY koru koru -
openrouter OPENROUTER_API_KEY env /opt/hindsight/.env HINDSIGHT_API_REFLECT_LLM_2_API_KEY koru koru -
openrouter OPENROUTER_API_KEY env /opt/hindsight/.env HINDSIGHT_API_REFLECT_LLM_3_API_KEY koru koru -
openrouter OPENROUTER_API_KEY env /opt/hindsight/.env HINDSIGHT_API_CONSOLIDATION_LLM_1_API_KEY koru koru -
openrouter OPENROUTER_API_KEY env /opt/hindsight/.env HINDSIGHT_API_CONSOLIDATION_LLM_2_API_KEY koru koru -
openrouter OPENROUTER_API_KEY env /opt/hindsight/.env HINDSIGHT_API_CONSOLIDATION_LLM_3_API_KEY koru koru -
openrouter OPENROUTER_API_KEY env /home/ubuntu/.hermes/profiles/bekci/.env OPENROUTER_API_KEY koru koru -
openrouter OPENROUTER_API_KEY env /home/ubuntu/.hermes/profiles/karne/.env OPENROUTER_API_KEY koru koru -
openrouter OPENROUTER_API_KEY env /home/ubuntu/.hermes/profiles/sef/.env OPENROUTER_API_KEY koru koru -
openrouter OPENROUTER_API_KEY env /home/ubuntu/.hermes/.env OPENROUTER_API_KEY koru koru -
apisix-admin APISIX_ADMIN_KEY dosya /etc/meridian/apisix_admin_key - 0400 root:root -
apisix-admin APISIX_ADMIN_KEY env /opt/apisix/.env-apisix APISIX_ADMIN_KEY koru koru -
cp HINDSIGHT_CP_ACCESS_KEY dosya /etc/meridian/hindsight_cp_access_key - 0400 root:root -
api-sunucu API_SERVER_KEY dosya /etc/meridian/api_server_key - 0400 root:root -
KOPYA_SON
  echo "api-sunucu API_SERVER_KEY env $_SOHBET_KOKU/.env API_SERVER_KEY koru koru -"
  _sohbet_satirlari api-sunucu API_SERVER_KEY API_SERVER_KEY
  # KAPI TÜKETİCİ ANAHTARLARI (G3b Task 3, 2026-10-01) — bot başına İÇ alt ad `kapi-bot-<ad>` (Rol-1 G3b-R2), bot başına
  # BİTİŞİK dört satır: REFERANS Agent render hedefi (`vault_kv.bot_key_<ad>.hedef`, G3b-R3) · kapının key-auth tüketicisi
  # (`.env-apisix`, `$env://BOT_KEY_<AD>` — açılışta çözülür) · rapor profili (timer'lı oneshot, `.env`i her koşuda okur)
  # · sohbet profili (`providers.kapi.key_env`). Döngü İÇ fonksiyona ÇIKARILMADI: v522 `_tablo_cekirdegi` `_kopyalar`ı
  # iki sabit + `_sohbet_satirlari` ile keser — yeni bir yardımcı orada sessizce eksik kalırdı. Büyük harf `tr` ile
  # (bash 3.2: `${b^^}` YOK) ve `LC_ALL=C` altında: Türkçe yerelde büyütme `i`yi `İ`ye çevirebilir — `BOT_KEY_BEKCİ`.
  local b B
  for b in $_SOHBET_BOTLARI; do
    B="$(printf '%s' "$b" | LC_ALL=C tr 'a-z' 'A-Z')"
    echo "kapi-bot-$b BOT_KEY_$B dosya /etc/meridian/bot_key_$b - 0400 root:root -"
    echo "kapi-bot-$b BOT_KEY_$B env /opt/apisix/.env-apisix BOT_KEY_$B koru koru -"
    echo "kapi-bot-$b BOT_KEY_$B env /home/ubuntu/.hermes/profiles/$b/.env BOT_KEY_$B koru koru -"
    echo "kapi-bot-$b BOT_KEY_$B env $_SOHBET_KOKU/profiles/$b/.env BOT_KEY_$B koru koru -"
  done
}

#: `--cp` SATIRLARI (TSK-226b, 2026-09-26). REFERANS Vault Agent'ın kanonik tek-değer kopyasıdır
#: (`vault_kv.hindsight_cp_access_key.hedef`; d-1 emsali — `--envanter` kasadaki değeri referans alır,
#: `--esitle` kasa değerini eski kanala taşır, tersi DEĞİL). 2026-09-29'a kadar ikinci satır `.env-cp`
#: ESKİ KANAL kopyasıydı (birimin İLK `EnvironmentFile=`ı); iki-kanal kapanışında ÇIKTI (yukarıdaki şerh) —
#: CP bugün değeri YALNIZ yan dosyadan (`.env-cp.vault`, drop-in 51 ile ZORUNLU) alır. Yan dosya TABLODA
#: YOK: onu yalnız Agent yazar (emsal `.env-apisix.vault`, `.env.vault`) ve render'ı kanonik kopyadan
#: ölçülür — rotasyonun oraya yazması Agent'la yarışmak olurdu (`--db --vault` tasarımının aynı gerekçesi).
#: SONUÇ: `--cp`nin ESKİ yolu (kasasız) yalnız kanonik kopyayı yazar ve CP onu OKUMAZ — kanıt "YENİ değerle
#: 401" der ve çıkış 2 verir (yarım rotasyon SESSİZ olamaz); eski yol KESİLMEDİ (Rol-1 kararı: tek rotasyon
#: yolu kesilmez, uyarı kapı değil), doğru yol `--cp --vault`tır.

#: EMEKLİ KOPYALAR (TSK-064 iki-kanal kapanışı, 2026-09-29) — rotasyonun ARTIK YAZMADIĞI ve hiçbir tüketicinin
#: OKUMADIĞI dosyalar. Tablodan çıktılar; ama diskte KALIRLARSA eski değeri taşıyan, sahipsiz bir sır kopyasıdırlar
#: (ilk rotasyondan sonra bayat, yine de okunabilir). `--envanter` her birinin VARLIĞINI ölçer (DEĞER okunmaz) ve
#: duruyorsa bağırır: kaldırma OPERATÖR adımıdır (yedek → kaldır — deploy/oracle-a1/RUNBOOK.md son bölüm).
#: KAYNAK: `deploy/sir_envanteri.yaml` → `rotasyon_kopyalari.emekli_kopyalar[].yol`. Kopya KAÇINILMAZ (`--envanter`
#: PyYAML'sız koşar) → ayrışma çivisi v590 C4. `.env-cp` ayrıca `_taranan_dosyalar`da KALIR (d-1 `.dash.env`
#: emsali): varlığı buradan, beyan dışı alanları oradan bağırılır — iki ayrı soru.
_emekli_kopyalar() {
  cat <<'EMEKLI_SON'
/opt/hindsight/.key
/opt/hindsight/.env-cp
EMEKLI_SON
}

#: `--apisix-admin`de REFERANS SIRASI TERSTİR (env ÖNCE, credential SONRA) ve bu bir üslup tercihi
#: değil ÖLÇÜLMÜŞ bir zorunluluktur. Öteki sırlarda ilk satır credential kaynağıdır çünkü O kaynak
#: her zaman VARDIR (kaynağı olmayan birim hiç açılmaz). Burada credential kaynağı Faz-1C elle
#: uygulanana kadar YOKTUR — ilk satıra konsaydı `--envanter`in referansı ve `--esitle`nin kaynağı
#: "YOK" olur, ikisi de daha ilk satırda dururdu. Kapının KENDİ kanalı (`.env-apisix`) ise her
#: zaman vardır ve canlıda YÜRÜRLÜKTEKİ değeri taşır (konteyner onu `--env-file` ile okur), yani
#: doğru referans odur. Yan kazanç: `--apisix-admin --esitle` tam olarak Faz-1C'nin elle adımını
#: yapar — kapının değerini credential kaynağına taşır.
#:
#: 2026-09-17 GÜNCELLEME (TSK-064 (d-1)) — YUKARIDAKİ GEREKÇE BİTTİ, SIRA DÜZELDİ. İki öncülü de
#: artık doğru değil: (1) credential kaynağı VAR — Faz-1C A1'de 2026-09-13 21:21Z'de uygulandı ve
#: dosya 2026-09-14'ten beri Vault Agent'ın TEKİL render hedefidir (`vault_kv.apisix_admin_key`);
#: (2) kapının YÜRÜRLÜKTEKİ değeri `.env-apisix`ten GELMİYOR — dalga-2 drop-in'i
#: (`apisix.service.d/50-vault-yan-dosya.conf`) `.env-apisix.vault`ı İKİNCİ `--env-file` olarak
#: verir ve docker aynı anahtarda SONRAKİNİ geçerli sayar. Aynı iki cümle `OPENROUTER_API_KEY` için
#: de geçerlidir: kapı `OPENROUTER_*`ı `.env-apisix.vault`tan, hafıza üyeleri `.env.vault`tan alır ve
#: `/etc/hindsight/creds/HINDSIGHT_API_LLM_API_KEY` o değerin Agent render'ıdır (birincil kasa yolu,
#: takma ad `openrouter_api_key` buraya çözülür). Bu yüzden İKİ sırrın referansı da tekil render
#: hedefine taşındı; `.env-apisix` satırları tabloda KOPYA olarak kalır — (d-2) asıl dosyadan
#: kaldırana kadar yaşarlar ve rotasyon onları da yazmak zorundadır.
#: BEDEL (bedel yasası): `--apisix-admin --esitle` artık Faz-1C'nin elle adımını YAPAMAZ —
#: credential kaynağı yoksa "referans kopya YOK" ile durur (o adım bir kez, 2026-09-13'te yapıldı;
#: kaynağın bugünkü sahibi Agent'tır). Yön de döndü: ayrışmada BAYAT sayılan artık `.env-apisix`tir.
#: Değerler EŞİTKEN (2026-09-17 ölçümü) davranış değişmez: eşitleme yazacak AYRI kopya bulmaz.
#: `apisix_admin()` ESKİ değeri hâlâ `.env-apisix` YEDEĞİNDEN okur — bu satır referans kuralına
#: bağlı değildir ve (d-2) satırı kaldırdığında AYRICA ele alınmalıdır (açık kalem, rapor).

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
    #: G3b (2026-10-01): bot ağ geçidi (MCP `bot_hafizasi_ara` credential'ı + profil `.env`lerindeki `HINDSIGHT_API_KEY` —
    #: Hermes hafıza sağlayıcısı açılışta okur) ve Telegram dinleyicisi (dönüş kaydı, credential) da tüketir. İkisi
    #: KOŞULLU birimdir (`_KOSULLU_BIRIMLER`): yalnız etkinse yeniden başlar.
    HINDSIGHT_API_TENANT_API_KEY) echo "hindsight-api.service hindsight-cp.service meridian.service meridian-botlar.service meridian-telegram.service" ;;
    HINDSIGHT_DB_PAROLA)          echo "hindsight-api.service" ;;
    MERIDIAN_DASH_TOKEN)          echo "meridian.service" ;;
    NOUS_API_KEY)                 echo "meridian.service" ;;
    OPENROUTER_API_KEY)           echo "apisix.service hindsight-api.service" ;;
    #: Yönetim anahtarını YALNIZ kapı tüketir: `ops/apisix_uygula.py` bir BİRİM DEĞİLDİR (operatör
    #: eliyle koşan ops aracı) ve her koşumda dosyayı yeniden okur — restart istemez. Kapı ise
    #: `${{APISIX_ADMIN_KEY}}` çözümünü YALNIZ açılışta yapar: reload yetmez, RESTART gerekir.
    APISIX_ADMIN_KEY)             echo "apisix.service" ;;
    #: CP giriş anahtarını YALNIZ kontrol paneli okur: konteyner değeri AÇILIŞTA ortamından alır
    #: (değersiz `-e AD`, TSK-226) — yan dosyanın render'ı RESTART ister (2026-09-29'dan beri tek kanal;
    #: `.env-cp` emekli). Kiracı anahtarının CP tüketicisi de AYNI yan dosyadır (DATAPLANE, takma ad).
    HINDSIGHT_CP_ACCESS_KEY)      echo "hindsight-cp.service" ;;
    #: Bot ağ geçidinin dinleyici anahtarı (G3b, 2026-10-01): Hermes onu kök ve profil `.env`lerinden AÇILIŞTA okur
    #: (restart gerekir); Telegram dinleyicisi credential'dan (`LoadCredential`, 55 drop-in). İkisi de KOŞULLU birim.
    API_SERVER_KEY)               echo "meridian-botlar.service meridian-telegram.service" ;;
    #: Bir botun KAPI tüketici anahtarı (G3b Task 3, 2026-10-01): kapı `$env://BOT_KEY_<AD>`ı YALNIZ açılışta çözer (RESTART,
    #: reload yetmez — `KAPI_APIKEY` emsali) ve bot ağ geçidi sohbet profilinin `.env`inden AÇILIŞTA okur (KOŞULLU birim).
    #: Motor bu anahtarı KULLANMAZ → `meridian.service` YOK (v604 C4). Rapor botları timer'lı oneshot'tur (beyanlı, restart
    #: yok). Telegram dinleyicisi bot anahtarı OKUMAZ (`API_SERVER_KEY` ile ağ geçidine konuşur).
    #: AÇIK DIŞLAMA — GLOB'DAN ÖNCE (G3b Task 4; Task 3 incelemesi M4): `BOT_KEY_MERIDIAN` bir BOT anahtarı DEĞİL motorun kapı
    #: anahtarıdır (`KAPI_APIKEY`ın takma adı; tüketici kapı + MOTOR) ve `--kapi` onu `KAPI_APIKEY` adıyla döndürür. Glob onu
    #: eşleseydi bir gün `rotasyon_siri: BOT_KEY_MERIDIAN` yazıldığında motor SESSİZCE yeniden başlamazdı. Harita YOK (1):
    #: çağıran "tüketici birim haritası YOK" ile durur — fail-closed. Çivi: v604 C11.
    BOT_KEY_MERIDIAN)             return 1 ;;
    BOT_KEY_*)                    echo "apisix.service meridian-botlar.service" ;;
    *) return 1 ;;
  esac
}

#: Yeniden başlatma SIRASI bir BAĞIMLILIK sırasıdır, alfabe değil: kapıyı (apisix) motordan ÖNCE
#: yeniden başlatmazsan motor yeni anahtarla eski kapıya konuşur ve ilk turda 401 alır.
#: `$env://` çözümünü apisix YALNIZ açılışta yapar — reload YETMEZ, RESTART gerekir. Sıra TEK
#: yerde yaşar: birim kümesi nereden gelirse gelsin (alt komutun tamamı ya da tek bir sırrın
#: tüketicileri) buradan geçer, yani "sıra" ile "küme" birbirinden bağımsız değişebilir.
#: 2026-09-30 (G3b): bot ağ geçidi ve Telegram dinleyicisi sona eklendi — telegram birimi
#: `After=meridian-botlar.service` taşır, botlar kapıdan ve hafızadan SONRA açılır (birim dosyalarının
#: `After=`ı; çivi v604 A1b). Listede olmayan birimi `_sirala` sessizce DÜŞÜRÜR: yeni tüketici birim buraya
#: girmeden restart kümesine giremez (v604 A1).
_BIRIM_SIRASI="apisix.service hindsight-api.service hindsight-cp.service meridian.service meridian-botlar.service meridian-telegram.service"

#: KOŞULLU BİRİMLER — YALNIZ ETKİNSE yeniden başlatılır (G3b, 2026-09-30). Bot ağ geçidi ve Telegram
#: dinleyicisi A1'de bugün ETKİN DEĞİL (birim dosyaları bile yok, `inactive` — ölçüldü 2026-09-30); canlıda
#: etkinleştirme G3c'dedir. Koşulsuz `systemctl restart` etkin olmayan bir birimi BAŞLATIRDI (etkinleştirme
#: kararını rotasyon vermiş olurdu) ve açılmayan bir birimin `/run/credentials`ı hiç doğmadığı için credential
#: denetimi `olcum_yok` (çıkış 2) verirdi. `_yeniden_baslat` bu birimleri `systemctl is-active` ile sorar;
#: etkin değilse (inactive · failed · yüklü değil) `ATLANDI (etkin değil: <durum>)` basar ve birimi restart,
#: credential ve hazırlık kümelerinden ÇIKARIR — sessiz atlama değil, DURUM ADIYLA beyan (bedel yasası).
#: Kuru rapor aynı soruyu sorar ve atlanacağı ÖNCEDEN söyler (`_kosullu_kuru_notu`). Öteki birimler için
#: `is-active` HİÇ sorulmaz: onların davranışı birebir aynıdır (v604 A14).
_KOSULLU_BIRIMLER="meridian-botlar.service meridian-telegram.service"

_kosullu_birim_mi() {
  case " $_KOSULLU_BIRIMLER " in *" $1 "*) return 0 ;; esac
  return 1
}

#: SOHBET BOTU MU — `--kapi-bot <ad>`ın TEK ad kapısı (G3b Task 3, 2026-10-01). Ad listeye KELİME KELİME, TAM eşitlikle
#: sorulur: `case " $liste "` deseni "sef bekci" gibi boşluklu bir adı da kabul ederdi; büyük harf (`BEKCI`), yol
#: karakteri (`bekci/../sef`), boş ad ve bilinmeyen bot (`yok`, `meridian`) reddedilir. Ret AYRIŞTIRMADADIR — root
#: kapısından, çalışma dizininden, kasadan ve her dosyadan ÖNCE (v604 C2).
_sohbet_botu_mu() {
  local b
  for b in $_SOHBET_BOTLARI; do
    if [ "$b" = "$1" ]; then return 0; fi
  done
  return 1
}

#: OPERATÖR BAYRAĞI — iç alt ad → komut satırı (G3b Task 3). `kapi-bot-<ad>` bir İÇ addır (Rol-1 G3b-R2); komut
#: satırındaki karşılığı İKİ jetondur (`--kapi-bot <ad>`) ve `--kapi-bot-<ad>` diye bir bayrak YOKTUR — basılsaydı
#: operatörün yapıştırdığı satır "bilinmeyen argüman" ile düşerdi. Operatöre KOMUT öneren her satır bayrağı buradan alır
#: (v604 C6). Öteki alt komutlarda `--<alt>` — davranış birebir.
_bayrak() {
  case "$1" in
    kapi-bot-*) printf -- '--kapi-bot %s\n' "${1#kapi-bot-}" ;;
    #: `--geri-al` (TSK-261) de değer ALAN bir bayraktır: önerilen satır dizini taşımazsa operatörün yapıştırdığı komut
    #: "YEDEK DİZİNİ ister" ile düşerdi.
    geri-al)    printf -- '--geri-al %s\n' "${GERI_AL_DIZINI:-<yedek-dizini>}" ;;
    *)          printf -- '--%s\n' "$1" ;;
  esac
}

#: REÇETE BİRİM LİSTESİ — koşullu birim operatöre ÇIPLAK "yeniden başlat" diye verilmez (G3b Task 2, Task 1 incelemesi M1).
#: Geri alma reçeteleri (`_geri_alma_recetesi` · `_genel_kasa_recetesi` · alt komut sonu `>> geri alma` satırları)
#: `_birimler`in TAM kümesini basıyordu; koşullu birim tüketici kümesine girdiği an operatörün yapıştıracağı satır etkin
#: OLMAYAN birimi BAŞLATIRDI — `_yeniden_baslat`ın kapattığı tehlike insan katmanında açık kalırdı. Bu yardımcı
#: koşulsuz birimleri aynen, koşullu birimleri `sudo systemctl try-restart` ile (systemd: YALNIZ koşan birimi yeniden
#: başlatır, duranı BAŞLATMAZ) yazar. Reçete basıldığı an birimin durumunu sormaz: geri alma ANI farklıdır ve
#: `try-restart` o anın durumuna uyar. `_recete_birimleri <birim…>` — ölçülemeyen liste metni ("(birim listesi
#: ölçülemedi)") koşulsuz kelime gibi AYNEN geçer. Çiviler: v604 B11 (dinamik) · B11c (her reçete satırı buradan).
_recete_birimleri() {
  local b kosulsuz="" kosullu=""
  for b in "$@"; do
    if _kosullu_birim_mi "$b"; then kosullu="${kosullu:+$kosullu }$b"; else kosulsuz="${kosulsuz:+$kosulsuz }$b"; fi
  done
  if [ -z "$kosullu" ]; then printf '%s\n' "$kosulsuz"; return 0; fi
  printf '%s(YALNIZ ETKİNSE: sudo systemctl try-restart %s)\n' "${kosulsuz:+$kosulsuz }" "$kosullu"
}

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
#: G3b (2026-10-01): bot ağ geçidi ve Telegram dinleyicisi satırları — ikisi de KOŞULLU birimdir; denetim yalnız
#: yeniden BAŞLATILAN birim için koşar (`_yeniden_baslat` süzgeci), etkin olmayanın `/run/credentials`ı sorulmaz.
#: Botlar `API_SERVER_KEY`i credential'dan OKUMAZ (Hermes profil `.env`i — PROFİL kapsamı): satırı YOK (v604 B8).
_kredensiyeller() {
  cat <<'KRED_SON'
kapi meridian.service KAPI_APIKEY
tenant meridian.service HINDSIGHT_API_TENANT_API_KEY
tenant hindsight-api.service HINDSIGHT_API_TENANT_API_KEY
db hindsight-api.service HINDSIGHT_API_DATABASE_URL
dash meridian.service dash_token
openrouter meridian.service NOUS_API_KEY
openrouter hindsight-api.service HINDSIGHT_API_LLM_API_KEY
tenant meridian-botlar.service HINDSIGHT_API_TENANT_API_KEY
tenant meridian-telegram.service HINDSIGHT_API_TENANT_API_KEY
api-sunucu meridian-telegram.service API_SERVER_KEY
KRED_SON
}

#: ONESHOT TÜKETİCİ KREDENSİYELLERİ — `_kredensiyeller()`den BİLEREK AYRI bir tablo (Rol-1 hükmü,
#: TSK-138 dilim-2 P6 kırmızısı; bkz. `deploy/oracle-a1/meridian-brifing.service.d/
#: 54-kapi-credential.conf`). `_kredensiyeller()`in ölçümü ("restart sonrası
#: `/run/credentials/<birim>/<kimlik>` boyutu > 1") `Type=oneshot` + timer-tetikli bir birime
#: UYGULANAMAZ: rotasyon penceresi böyle bir birimi YENİDEN BAŞLATMAZ (hermes profilleri ve
#: `brifing/learn/sprint@`nin `EnvironmentFile` kanalıyla ZATEN BEYANLI olan "restart istemeyen
#: tüketici" kararının LoadCredential kanalındaki karşılığı, bkz. `_sir_birimleri` şerhi) ve
#: `/run/credentials/<birim>/` yalnız o birimin KENDİ koşumu SIRASINDA var olur — rotasyon
#: penceresinde hiçbir zaman gözlenemez. Bu yüzden `_kredensiyel_denetle` bu tabloyu OKUMAZ:
#: doğrulama restart+`/run`a değil, KAYNAK dosyasına bakar (aynı dosya zaten `_kopyalar()`daki
#: `dosya`/`url` satırının hedefidir ve DEĞER ÜRETİMİ sonrası uzunluk denetiminden geçer — bkz.
#: başlıktaki "DEĞER ÜRETİMİ"). Sütunlar: <alt komut> <birim> <kimlik> <kaynak yolu> — kaynak
#: yolu BURADA (uzun ömürlü tablo taşımaz) çünkü doğrulama ONA bakar, restart'a değil.
#: `tests/test_sir_rotasyon_v447.py::test_P6_KREDENSIYEL_tablosu_DROPINLERLE_AYRISMAZ` iki tabloyu BİRLEŞTİREREK drop-in çiftleriyle iki
#: yönlü eşitler VE her çiftin doğru tabloda olduğunu birim dosyasındaki `Type=oneshot`/eşleşen
#: `.timer` VARLIĞINDAN ölçer — elle liste DEĞİL: sınıf yanlışsa çivi öter.
_oneshot_kredensiyeller() {
  cat <<'ONESHOT_KRED_SON'
kapi meridian-brifing.service KAPI_APIKEY /etc/meridian/kapi_apikey
kapi meridian-bekci.service KAPI_APIKEY /etc/meridian/kapi_apikey
kapi meridian-karne.service KAPI_APIKEY /etc/meridian/kapi_apikey
tenant meridian-defter-ozeti-retain.service HINDSIGHT_API_TENANT_API_KEY /etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY
ONESHOT_KRED_SON
}

#: `--kuru`/`--envanter` PAYLAŞTIĞI YAZICI (tek-kaynak yasası: iki basım noktası ayrı yazılsaydı
#: biri güncellenir öteki unutulurdu). `$1` BOŞSA (envanter) HER satır basılır; DOLUYSA (kuru)
#: yalnız o alt komutun satırları. `_kredensiyel_denetle`nin ÖLÇMEDİĞİ bu birimleri sessizce
#: atlamak bedel yasasının yasakladığı hâl olurdu — operatör "bu birim neden yeniden başlamadı"
#: sorusunu burada, açıkça yazılı görür.
_oneshot_yazdir() {
  local sadece="${1:-}" _alt birim kimlik _kaynak
  while read -r _alt birim kimlik _kaynak; do
    [ -z "$sadece" ] || [ "$_alt" = "$sadece" ] || continue
    echo "    · oneshot tüketici: $birim — sonraki tetikte okur"
  done < <(_oneshot_kredensiyeller)
}

#: BEYAN DIŞI KOPYA TARAMASI — bedel yasasının bu betikteki karşılığı. Kopya tablosu bir BEYANDIR;
#: beyan gerçeği kendiliğinden doğrulamaz. `--envanter` bu dosyaların hepsinde döndürülen ADLARI
#: arar ve tabloda OLMAYAN bir eşleşme bulursa bağırır: rotasyonun görmediği bir kopya, ilk
#: rotasyondan sonra sessizce ESKİ değeri taşıyan bir kopyadır (spec Bulgu-2 sınıfı).
#: `/opt/meridian/.dash.env` A1'de YOK (2026-09-14 17:46Z silindi) ve kopya tablosundan ÇIKTI
#: (TSK-064 (d-1), 2026-09-17) — ama bu listede BİLEREK KALIR: yok olan dosya `test -f` ile atlanır
#: (bedel sıfır; sözlük bedeli ölçümünün dosya kümesi değişmez), geri doğarsa içindeki pano jetonu
#: artık rotasyonun YAZMADIĞI bir kopyadır ve envanter onu BEYAN DIŞI diye bağırmak zorundadır.
#: Listeden çıkarmak o geri dönüşü SESSİZ yapardı (çivi: v520 B7/M6).
#: `/opt/hindsight/.env-cp` AYNI gerekçeyle KALIR (TSK-064 iki-kanal kapanışı, 2026-09-29): kopya tablosundan
#: çıktı ve dosya 2026-09-29 11:32Z'de A1'den KALDIRILDI (yedek `/root/sir-yedek-20260929T113217Z-ikikanal/`) —
#: yok olan dosyayı `test -f` atlar; geri doğarsa iki alanı da (sır kimliği `HINDSIGHT_CP_ACCESS_KEY` ·
#: sözlüğe uyan `HINDSIGHT_CP_DATAPLANE_API_KEY`) BEYAN DIŞI bağırılır (v590 C5).
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
/home/ubuntu/.hermes/.env
TARA_SON
  # Bot ağ geçidinin kök ve sohbet profili `.env`leri (G3b, 2026-10-01) — bot listesinden DÖNGÜYLE (`_SOHBET_BOTLARI`).
  # A1'de BUGÜN YOK (2026-09-30): yok olan dosyayı `test -f` atlar (bedel sıfır); tohumlandıktan sonra sözlük bedeli
  # İLK `--envanter`de ölçülür (alan kümesi tablodan: API_SERVER_KEY · HINDSIGHT_API_KEY · BOT_KEY_<AD>).
  local b
  echo "$_SOHBET_KOKU/.env"
  for b in $_SOHBET_BOTLARI; do echo "$_SOHBET_KOKU/profiles/$b/.env"; done
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
KARAR'dır (EŞİT/AYRI/VAR/YOK). Bütün yazımlar aynı dizinde geçici dosya + yerine koyma ile
ATOMİKTİR: yarım yazılmış bir credential dosyası birimi açılmaz hâle getirir. Yazımlar BAĞ
İZLEMEZ ve tanıtıcı tabanlıdır (`_atomik_yaz` — TSK-260; tohumlamayla ortak çekirdek). OKUMALAR da
aynı çekirdekten geçer (`_oku` — TSK-262): bağ, FIFO, soket, aygıt OKUNMAZ, adıyla reddedilir.
"""
from __future__ import annotations

import errno
import json
import os
import re
import stat
import sys
from collections import Counter
from types import SimpleNamespace
from urllib.parse import quote, unquote, urlsplit, urlunsplit

ONEKLER = {"-": "", "Bearer": "Bearer "}


def _onek(ad: str) -> str:
    if ad not in ONEKLER:
        sys.exit(f"tanınmayan önek: {ad} (tanınanlar: {sorted(ONEKLER)})")
    return ONEKLER[ad]


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


# --- BAĞ İZLEMEYEN YAZIM — TOHUMLAMA VE ROTASYONUN ORTAK ÇEKİRDEĞİ (G3b dal sonu M1 + TSK-260, CWE-59) -----------------
# SINIF. Hedef dizinlerin bir kısmı UBUNTU sahiplidir: hermes profilleri (`~/.hermes/…`), bot ağ geçidi (`~/.hermes-botlar/…`,
# A0 0700), `/opt/hindsight` (755 ubuntu — A1 ölçümü 2026-09-15, `deploy/vault/vault-agent.service` başlığı). Ubuntu kimliğinde
# koşan biri bir dizin bileşenini ya da hedefin kendisini sembolik bağa çevirirse YOL tabanlı yazım (`mkstemp(dir=…)` · yola
# `chmod`/`chown` · yola `replace`/`link`) bağı İZLER: root yazımı ağacın DIŞINA götürür (dal sonu sondası
# P1: çıkış 0, dosya `/opt/…` altında), geçici adı chown'dan önce bağa çevrilen bir ROOT dosyasının sahibini/modunu değiştirir
# ya da hedef bağın içeriğini okuyup bağı düz dosyayla ezer. Rotasyonun yazım yolu (`_atomik_yaz`) 2026-10-01'e dek tam bu
# biçimdeydi (TSK-260 — "sınıf bir örnekle kapanmaz": tohumlama 87d194b3'te kapanmıştı).
# DESEN (iki yolun TEK gövdesi — `_dizin_ac` · `_gecici_yaz` · `_gecici_dogrula` · `_yazim_kusurlari`):
#   (1) dizin zinciri GÜVEN ÇAPASINDAN aşağı bileşen bileşen `O_NOFOLLOW|O_DIRECTORY` ile açılır (openat — denetim ile kullanım
#       AYNI dosya tanıtıcısıdır) ve her bileşen tanıtıcıdan (`fstat`) ölçülür: bağ değil · dizin · grup/diğer YAZAMAZ (grup
#       yazma YALNIZ root iken ve grup sahibine ÖZELSE zararsız — `_ozel_grup_mu`) · sahibi İZİNLİ kümede (root iken);
#       `realpath` beklenen yolla aynı (ikinci katman);
#   (2) geçici dosya o tanıtıcıya göre `O_EXCL|O_NOFOLLOW` açılır, sahip ve mod DOSYA TANITICISINA (`fchown` → `fchmod`)
#       verilir — yol tabanlı chown/chmod YOK: ad yarışta bağa çevrilse de tanıtıcı AÇILAN inode'u gösterir;
#   (3) yerine koyma/bağlama ÖNCESİ geçici ad yeniden ölçülür (yarışta değiştiyse hedefe DOKUNULMAZ); yerine koyma
#       (`os.replace`, rotasyon) ya da bağlama (`os.link(follow_symlinks=False)`, tohumlama — hedef VARSA `FileExistsError`) AYNI
#       dizin tanıtıcısı içinde;
#   (4) yazım SONRASI hedef `lstat` ile ölçülür: AYNI inode · normal dosya · beklenen mod · beklenen sahip (root iken).
# İZİNLİ SAHİP KÜMESİ iki yolda farklıdır ve bu BİLİNÇLİDİR: tohumlama `{ubuntu}` ister (dizinler A0'ın ubuntu dizinleridir; root
# sahipli bir bileşen hermes'in okuyamayacağı bir ağaç demektir); rotasyon `{root, hedefin sahibi}` ister — "dizin, hedefin
# yazılacağı kullanıcı dışında kimse tarafından yazılamaz" (OpenSSH `safe_path` kuralı: her bileşen root'un ya da kullanıcının,
# grup/diğer yazamaz; Debian yamasıyla grup kullanıcıya özelse grup yazması zararsız). Ölçülen A1 hâlinin hepsi bu kurala uyar: `/etc/meridian` · `/etc/hindsight/creds` 0755 root (2026-09-07),
# `/opt/apisix` root sahipli + `.env-apisix` root (2026-09-15), `/opt/hindsight` 755 ubuntu + `.env` 600 ubuntu, hermes ve
# `.hermes-botlar` ağaçları ubuntu. Root DEĞİLKEN (yalnız çivi makinesi: dizinler test kullanıcısınındır) sahip ÖLÇÜLMEZ ve bu
# BEYANLA söylenir; bağ ve grup/diğer yazma denetimi her kimlikte koşar.


def _kok() -> str:
    """Rotasyon hedeflerinin GÜVEN ÇAPASI: betiğin `KOK`u. Kabuktaki TEST KANCASIYLA AYNI değişkendir (`SIR_ROT_KOK` — çivi onu
    tmp köke çevirir); üretimde boştur → `/` (A1'de `sudo` ortamı da sıfırlar: değişken yardımcıya hiç ulaşmaz, sonuç yine `/`)."""
    return os.path.normpath(os.path.abspath(os.environ.get("SIR_ROT_KOK") or os.sep))


def _capa(dizin: str) -> str:
    """Hedef dizinini içeren EN DERİN güvenilir çapa: (1) betiğin kökü (`_kok`); (2) yardımcının KENDİ dizini — betiğin 0700
    çalışma dizini (`_islik_kur`), bütün çalışma çıktıları (`cikar` · `kanit-cfg` · `pgpass` · `json-govde` · `sql-uret` ·
    `yaz-url <işlik>`) oraya yazılır. O dizine güvenmeyen bir denetim koştuğu kodun KENDİSİNE güvenmektedir: bu çapa yeni bir
    güven varsayımı EKLEMEZ. (Üretimde işlik `/tmp` altındadır ve `/tmp` 1777'dir — kökten yürüyen zincir orada dururdu.)
    İkisinin de dışındaki bir hedef `_dizin_ac`ta "DIŞINDA" ile reddedilir."""
    adaylar = [c for c in (_kok(), os.path.dirname(os.path.abspath(__file__)))
               if dizin == c or dizin.startswith(c.rstrip(os.sep) + os.sep)]
    return max(adaylar, key=len) if adaylar else _kok()


def _kimlik(sahip: str, grup: str) -> tuple[int, int, bool]:
    """`(uid, gid, sahip_olculur)`. Root iken ad ÇÖZÜLMEK ZORUNDADIR (yoksa ret — sahibi bilinmeyen yazım yok); root değilken
    (yalnız çivi makinesi) çözülemeyen ad `-1` olur ve sahip ÖLÇÜLMEZ."""
    import grp
    import pwd
    root = os.geteuid() == 0
    try:
        return pwd.getpwnam(sahip).pw_uid, grp.getgrnam(grup).gr_gid, root
    except KeyError:
        if root:
            sys.exit(f"sahip '{sahip}:{grup}' çözülemedi — root iken sahip ölçülmeden yazılmaz, yazım YAPILMADI")
        # Yasa 4 — sessiz-yutma: ad YALNIZ çivi makinesinde çözülemez (macOS'ta `ubuntu` yok); root değiliz, yani sahip
        # zaten ÖLÇÜLMEYECEK ve çağıranın hükmü bunu ADIYLA söyler ("sahip ÖLÇÜLMEDİ: root değil").
        return -1, -1, False


def _ozel_grup_mu(st: os.stat_result) -> bool:
    """Grup yazma biti ZARARSIZ mı: dizinin grubunun TEK üyesi dizinin sahibi mi (kullanıcıya ÖZEL grup)? Üyeler = birincil grubu
    bu olan hesaplar (`pwd` taraması) ∪ ek üyeler (`gr_mem`). Ubuntu varsayılanında `USERGROUPS_ENAB` + pam_umask kullanıcı
    oturumuna umask 002 verir (A1'de ÖLÇÜLMEDİ — varsayılan beyanı): ubuntu'nun ssh oturumunda elle açtığı bir dizin 0775
    ubuntu:ubuntu doğar ve grubun tek üyesi ubuntu'dur — "hedefin sahibi dışında kimse yazamaz" kuralını BOZMAZ. Emsal: Debian OpenSSH `secure_permissions` (StrictModes, user-private-group
    yaması). Yalnız root iken sorulur; ad/grup çözülemezse False (zararsızlık GÖSTERİLEMEDİ → ret)."""
    import grp
    import pwd
    try:
        gr = grp.getgrgid(st.st_gid)
        sahip = pwd.getpwuid(st.st_uid).pw_name
    except KeyError:
        return False
    return ({p.pw_name for p in pwd.getpwall() if p.pw_gid == st.st_gid} | set(gr.gr_mem)) == {sahip}


def _dizin_kusuru(st: os.stat_result, izinli: frozenset[int], olculur: bool) -> str | None:
    """Bir zincir bileşeninin kusuru (yoksa None). Kural: bileşeni hedefin yazılacağı kullanıcı (ve root) DIŞINDA kimse
    yazamaz — diğer-yazma her zaman ret; grup-yazma ret, YALNIZ root iken ve grup sahibine ÖZELSE (`_ozel_grup_mu`) zararsız;
    sahip `izinli` kümede (root iken — bkz. bölüm şerhi: tohumlama `{ubuntu}`, rotasyon `{root, hedefin sahibi}`). Root
    DEĞİLKEN (yalnız çivi makinesi) grup üyeliği ölçülmez ve grup-yazma KATI kuralla reddedilir."""
    if stat.S_ISLNK(st.st_mode):
        return "SEMBOLİK BAĞ (izlenmez)"
    if not stat.S_ISDIR(st.st_mode):
        return "dizin değil"
    if st.st_mode & 0o002:
        return f"grup/diğer YAZABİLİR (mod {st.st_mode & 0o7777:04o})"
    if st.st_mode & 0o020 and not (olculur and _ozel_grup_mu(st)):
        ek = "; grup yalnız sahibine özel DEĞİL" if olculur else ""
        return f"grup/diğer YAZABİLİR (mod {st.st_mode & 0o7777:04o}{ek})"
    if olculur and st.st_uid not in izinli:
        return f"sahibi uid {st.st_uid} (beklenen {' ya da '.join(str(u) for u in sorted(izinli))})"
    return None


def _dizin_ac(kok: str, dizin: str, izinli: frozenset[int], olculur: bool) -> tuple[int | None, str | None]:
    """`kok` (güven çapası — tohumlamada `_SOHBET_KOKU`, rotasyonda `_capa`) → `dizin` zincirini bağ İZLEMEDEN açar. Döner
    `(fd, None)` ya da `(None, hüküm)`: hüküm `YOK` ya da `RED: <bileşen>: <neden>`. Kökün ÜSTÜ yol ile açılır (A1: `/home/ubuntu`
    — ubuntu onu değiştiremez, `/home` root'undur; çapa `/` ise üstü yoktur ve kök tanıtıcıdan ölçülür); kök ve altı bileşen
    bileşen."""
    kok, dizin = os.path.normpath(kok), os.path.normpath(dizin)
    if not (os.path.isabs(kok) and os.path.isabs(dizin)):
        return None, "RED: yol mutlak değil"
    kok_on = kok.rstrip(os.sep) + os.sep
    if dizin != kok and not dizin.startswith(kok_on):
        return None, f"RED: {dizin}: beklenen kökün ({kok}) DIŞINDA"
    ust = os.path.dirname(kok)
    parcalar = ([os.path.basename(kok)] if kok != ust else []) + ([] if dizin == kok else dizin[len(kok_on):].split(os.sep))
    try:
        fd = os.open(ust, os.O_RDONLY | os.O_DIRECTORY)
    except FileNotFoundError:
        return None, "YOK"
    yol = ust
    try:
        if kok == ust:
            neden = _dizin_kusuru(os.fstat(fd), izinli, olculur)
            if neden:
                return None, f"RED: {kok}: {neden}"
        for p in parcalar:
            yol = os.path.join(yol, p)
            try:
                st = os.stat(p, dir_fd=fd, follow_symlinks=False)
            except FileNotFoundError:
                return None, "YOK"
            neden = _dizin_kusuru(st, izinli, olculur)
            if neden:
                return None, f"RED: {yol}: {neden}"
            try:
                yeni = os.open(p, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            except OSError as hata:
                # Denetimden SONRA bağa/dosyaya çevrildi (yarış: ELOOP/ENOTDIR) ya da kayboldu — açılmayan bileşen RED'dir.
                return None, f"RED: {yol}: açılamadı ({hata.strerror})"
            os.close(fd)
            fd = yeni
            # Denetim ile açılış arasında bileşen değiştiyse (yarış) açılan tanıtıcı yeniden ölçülür — hüküm TANITICININDIR.
            neden = _dizin_kusuru(os.fstat(fd), izinli, olculur)
            if neden:
                return None, f"RED: {yol}: {neden}"
        beklenen = os.path.join(os.path.realpath(ust), *parcalar)
        if os.path.realpath(dizin) != beklenen:
            # Yol `repr` ile (TSK-262 düzeltme turu 2, yeniden inceleme Y2a): çözülen yol bir BAĞIN hedefidir ve ADINI dizin sahibi
            # seçer — ham basıldığında yeni satır hükmü iki satıra böler (satır tabanlı denetimler — `esitle` kanıtı — bölünmüş
            # parçaları ayrı okur), ESC dizileri root operatörün terminalini boyar. `repr` tek satır + denetim karakterleri kaçışlı;
            # yol iletide KALIR (bağın nereye gittiği adli izdir — operatör `stat` ile aynı yere bakar). Çivi: v613 B4 · F4.
            return None, f"RED: {dizin}: realpath beklenen yoldan ayrışıyor ({os.path.realpath(dizin)!r})"
        acik, fd = fd, -1
        return acik, None
    finally:
        if fd != -1:
            os.close(fd)


def _gecici_sil(dfd: int, gecici: str) -> None:
    try:
        os.unlink(gecici, dir_fd=dfd)
    except FileNotFoundError:
        # Yasa 4 — sessiz-yutma: geçici ad YOKSA (yerine kondu / bağlandıktan sonra silindi ya da açılış düştü) silinecek bir
        # şey yoktur; hüküm yazım/bağ adımlarınındır, temizlik onu değiştirmez.
        pass


def _gecici_yaz(dfd: int, icerik: str | bytes, mod: int, uid: int, gid: int, olculur: bool) -> tuple[str, os.stat_result]:
    """Dizin tanıtıcısı içinde YENİ bir geçici dosya kurar (`O_EXCL|O_NOFOLLOW` — var olan bir ada/bağa AÇILMAZ), içeriği yazar,
    sahip ve modu DOSYA TANITICISINA verir: önce `fchown` (uid -1 → sahiplik değişmez), sonra `fchmod` — mod son verilir, çünkü
    Linux root'un chown'unda S_ISUID/S_ISGID'i silebilir; istenen mod TAM olarak kalsın. Döner: `(geçici ad, yazılan fstat)`.
    `bytes` içerik AYNEN (ikili) yazılır — `kopyala` (TSK-261) yedeği bayt bayt taşır, metin kipi CRLF'yi çevirirdi."""
    gecici = f".sir-rot-{os.urandom(8).hex()}"
    fd = os.open(gecici, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=dfd)
    kip = {"mode": "wb"} if isinstance(icerik, bytes) else {"mode": "w", "encoding": "utf-8"}
    try:
        with os.fdopen(fd, **kip) as fh:
            fh.write(icerik)
            fh.flush()
            if uid != -1:
                try:
                    os.fchown(fh.fileno(), uid, gid)
                except PermissionError:
                    if olculur:
                        raise
                    # Yasa 4 — sessiz-yutma: root DEĞİLKEN (yalnız çivi makinesi) başka kullanıcıya chown yapılamaz; sahip
                    # zaten ÖLÇÜLMEYECEK ve hüküm bunu ADIYLA söyler. Root iken hata YUKARI çıkar (yazım yok).
                    pass
            os.fchmod(fh.fileno(), mod)
            return gecici, os.fstat(fh.fileno())
    except BaseException:
        _gecici_sil(dfd, gecici)
        raise


def _gecici_dogrula(dfd: int, gecici: str, yazilan: os.stat_result, yol: str) -> None:
    """Yerine koyma/bağlama ÖNCESİ: geçici ad hâlâ YAZILAN inode'u mu gösteriyor (normal dosya)? Değilse ad yarışta bir bağa ya
    da başka bir dosyaya çevrilmiştir — yerine koymak o bağı/dosyayı hedefe taşırdı. Hedefe DOKUNULMAZ."""
    try:
        st = os.stat(gecici, dir_fd=dfd, follow_symlinks=False)
    except FileNotFoundError:
        st = None
    if st is None or not stat.S_ISREG(st.st_mode) or (st.st_dev, st.st_ino) != (yazilan.st_dev, yazilan.st_ino):
        sys.exit(f"geçici ad yazım sırasında DEĞİŞTİ (yarış — bağa ya da başka bir dosyaya çevrildi): {yol} — hedefe "
                 "DOKUNULMADI, yazım YAPILMADI")


def _yazim_kusurlari(dfd: int, ad: str, yazilan: os.stat_result, mod: int, uid: int, gid: int | None,
                     olculur: bool, yol: str) -> list[str]:
    """Yazım SONRASI ölçüm (`lstat`, dizin tanıtıcısı içinde): AYNI inode · normal dosya · beklenen mod · beklenen sahip (root
    iken; `gid` None → yalnız uid). Döner: kusur listesi (boş = doğrulandı).
    YOL DA ÖLÇÜLÜR (TSK-261; TSK-260 incelemesi M2): tanıtıcı tutulurken dizin YENİDEN ADLANDIRILIRSA yazım taşınan dizine iner
    ve tanıtıcıya göre ölçüm onu doğru sanar — çıkış 0, ama tüketicinin okuduğu YOLDAKİ dosya eski kalır (inceleme sondası P2).
    Bu yüzden yoldaki ad (`lstat` — ara dizinler tüketicinin gördüğü gibi izlenir, son bileşen izlenmez) YAZILAN inode olmalıdır."""
    try:
        son = os.stat(ad, dir_fd=dfd, follow_symlinks=False)
    except FileNotFoundError:
        return ["hedef YOK (yazımdan sonra kayboldu)"]
    kusur = []
    if (son.st_dev, son.st_ino) != (yazilan.st_dev, yazilan.st_ino):
        kusur.append("inode yazılan dosya DEĞİL")
    if not stat.S_ISREG(son.st_mode):
        kusur.append("normal dosya değil")
    if son.st_mode & 0o7777 != mod:
        kusur.append(f"mod {son.st_mode & 0o7777:04o} (beklenen {mod:04o})")
    if olculur and uid != -1 and (son.st_uid != uid or (gid is not None and son.st_gid != gid)):
        kusur.append(f"sahip {son.st_uid}:{son.st_gid} (beklenen {uid}:{'*' if gid is None else gid})")
    try:
        yoldaki = os.lstat(yol)
    except OSError:
        yoldaki = None
    if yoldaki is None or (yoldaki.st_dev, yoldaki.st_ino) != (yazilan.st_dev, yazilan.st_ino):
        kusur.append("YOLDAKİ dosya yazılan inode DEĞİL (dizin tanıtıcısı tutulurken dizin yeniden adlandırılmış/taşınmış "
                     "olabilir — yazım yoldan GÖRÜNMÜYOR, tüketici eski dosyayı okur)")
    return kusur


def _yeni_dosya_yaz(dfd: int, ad: str, icerik: str, mod: int, uid: int, gid: int, olculur: bool, yol: str) -> str:
    """TOHUMLAMA: dizin tanıtıcısı içinde YALNIZ YOK olan `ad`ı kurar (bağlama — hedef VARSA `FileExistsError`); sonra ölçer
    (`yol` — yoldaki inode da, `_yazim_kusurlari`). Döner: doğrulama hükmü (çıktıya basılır — değer DEĞİL)."""
    gecici, yazilan = _gecici_yaz(dfd, icerik, mod, uid, gid, olculur)
    try:
        _gecici_dogrula(dfd, gecici, yazilan, ad)
        try:
            os.link(gecici, ad, src_dir_fd=dfd, dst_dir_fd=dfd, follow_symlinks=False)
        except FileExistsError:
            sys.exit(f"hedef ZATEN VAR: {ad} — var olan dosyaya DOKUNULMAZ (yarış: denetimden sonra doğdu), yazım YAPILMADI")
    finally:
        _gecici_sil(dfd, gecici)
    kusur = _yazim_kusurlari(dfd, ad, yazilan, mod, uid, gid, olculur, yol)
    if kusur:
        sys.exit(f"yazım DOĞRULANAMADI: {ad} — {'; '.join(kusur)}. Dosya YERİNDE bırakıldı (bizim olmayabilir): elle incele")
    if olculur:
        return f"DOĞRULANDI: normal dosya, {mod:04o}, sahip {uid}:{gid}"
    return f"DOĞRULANDI: normal dosya, {mod:04o}; sahip ÖLÇÜLMEDİ (root değil — yalnız çivi makinesi)"


#: Hedefin KENDİSİ bağ — yazım bağın hedefine GİTMEZ ve bağ düz dosyayla EZİLMEZ (ESKİ yol ikisini birden yapıyordu).
_BAG_REDDI = "SEMBOLİK BAĞ (izlenmez — yazım bağın hedefine GİTMEZ, bağ ezilmez)"


def _hedef_ac(hedef: str, mod: str | int, sahip: str | tuple[int, int]) -> SimpleNamespace | str:
    """ROTASYON HEDEFİNİN TEK DENETİM GÖVDESİ — yazım (`_atomik_yaz`) ve yazım ÖNCESİ ön-denetim (`hedef-denetle` ←
    `_hedef_on_denetim`) buradan geçer; ikisi ayrışamaz. Zinciri `_capa`dan aşağı `_dizin_ac` ile açar (izinli sahipler
    `{root, hedefin sahibi}`), hedefi dizin tanıtıcısı içinde `lstat` eder: bağ ya da normal dosya değil → RED. `koru` mod/sahip
    bu `lstat`tan (bağ izlenmez); `koru` için yol ile alınan ilk `lstat` (izinli kümenin kaynağı) ile tanıtıcıdaki `lstat` AYNI
    inode olmalıdır — değilse zincir yarışta değişmiştir. Döner: açık hedef (`dfd` çağıranın kapatmasıdır) ya da RED dizgesi
    (tanıtıcı kapalı). `koru` ama hedef YOK → eski ileti ile durur ("mod=koru ama dosya YOK").
    `kopyala` (TSK-261) aynı gövdeden geçer: KAYNAK `koru koru` ile açılır; HEDEF kaynağın modu (`int`) ve sayısal sahibiyle
    (`(uid, gid)`) — eski root kopyasının `-p` ile koruduğu mod/sahibin bağ izlemeyen karşılığı."""
    yol = os.path.normpath(os.path.abspath(hedef))
    dizin, ad = os.path.split(yol)
    olculur = os.geteuid() == 0
    st0 = None
    if "koru" in (mod, sahip):
        try:
            st0 = os.lstat(yol)
        except FileNotFoundError:
            sys.exit(f"{'mod' if mod == 'koru' else 'sahip'}=koru ama dosya YOK: {hedef}")
        if stat.S_ISLNK(st0.st_mode):
            return f"RED: {yol}: hedef {_BAG_REDDI}"
    if sahip == "koru":
        uid, gid = st0.st_uid, st0.st_gid
    elif sahip == "-":
        uid = gid = -1
    elif isinstance(sahip, tuple):
        uid, gid = sahip
    else:
        k, _, g = sahip.partition(":")
        uid, gid, _ = _kimlik(k, g)
    izinli = frozenset({0, os.geteuid() if uid == -1 else uid})
    dfd, hukum = _dizin_ac(_capa(dizin), dizin, izinli, olculur)
    if dfd is None:
        return hukum if hukum.startswith("RED") else f"RED: {dizin}: dizin YOK"
    try:
        st = os.stat(ad, dir_fd=dfd, follow_symlinks=False)
    except FileNotFoundError:
        st = None
    neden = None
    if st is not None and stat.S_ISLNK(st.st_mode):
        neden = f"RED: {yol}: hedef {_BAG_REDDI}"
    elif st is not None and not stat.S_ISREG(st.st_mode):
        neden = f"RED: {yol}: hedef normal dosya değil"
    elif st0 is not None and (st is None or (st.st_dev, st.st_ino) != (st0.st_dev, st0.st_ino)):
        neden = f"RED: {yol}: hedef denetim sırasında DEĞİŞTİ (yol ile dizin tanıtıcısı ayrı dosyayı gösteriyor — yarış)"
    if neden:
        os.close(dfd)
        return neden
    if sahip == "koru":
        uid, gid = st.st_uid, st.st_gid
    bek_uid, bek_gid = (os.geteuid(), None) if sahip == "-" else (uid, gid)
    if mod == "koru":
        mod_n = st.st_mode & 0o7777
    else:
        mod_n = mod if isinstance(mod, int) else int(mod, 8)
    return SimpleNamespace(dfd=dfd, yol=yol, ad=ad, st=st, olculur=olculur, uid=uid, gid=gid, bek_uid=bek_uid,
                           bek_gid=bek_gid, mod=mod_n)


#: Okunmayan dosya türlerinin ADLARI (TSK-262) — okuma reddi bu adla basılır (`OKUNAMADI (FIFO)`); normal dosya → None.
_TUR_ADLARI = ((stat.S_ISLNK, "SEMBOLİK BAĞ"), (stat.S_ISFIFO, "FIFO"), (stat.S_ISSOCK, "SOKET"),
               (stat.S_ISCHR, "KARAKTER AYGITI"), (stat.S_ISBLK, "BLOK AYGITI"), (stat.S_ISDIR, "DİZİN"))
#: Yarış: denetlenen dosya açılışta BAŞKA bir dosya (inode) ya da denetim sırasında değişti.
_YARIS = "DEĞİŞTİ (yarış)"


def _tur_adi(mod: int) -> str | None:
    if stat.S_ISREG(mod):
        return None
    return next((ad for test, ad in _TUR_ADLARI if test(mod)), "BİLİNMEYEN TÜR")


class OkumaReddi(OSError):
    """OKUMA hedefi okunmadı (TSK-262): normal dosya DEĞİL (bağ · FIFO · soket · aygıt · dizin), zinciri reddedildi ya da
    denetimden sonra değişti. ADLIDIR — `yol` + `tur` taşır, DEĞER asla. `OSError` alt sınıfıdır: eski `except OSError` kovası
    ("OKUNAMADI") onu yine görür — ama okuma işlemleri onu ÖNCE kendi adıyla yakalar (`OKUNAMADI (<tür>)`); yakalamayan işlem
    (`cikar` · `pgpass` · `dsn-uc` · değer dosyası) `__main__`deki tek kapıda adlı iletiyle durur."""

    def __init__(self, yol: str, tur: str) -> None:
        super().__init__(f"okuma REDDİ: {yol}: {tur}")
        self.yol, self.tur = yol, tur


def _tanitictan_oku(h: SimpleNamespace, ikili: bool = False, okuma: bool = False) -> str | bytes:
    """Oku-değiştir-yaz'ın ESKİ içeriği (ve `kopyala`nın KAYNAĞI): denetlenen hedef, AYNI dizin tanıtıcısından `O_NOFOLLOW` ile
    açılır ve inode'u denetlenenle aynı olmalıdır. Metin kipi `open()` ile AYNIDIR (UTF-8, evrensel satır sonu — eski `_oku`
    davranışı); `ikili` → bayt AYNEN (`kopyala`: yedek/geri alma eski root kopyası gibi bayt-eşit olmalı).
    FIFO ASKISI YOK (TSK-261; TSK-260 incelemesi M1): denetim `lstat`ından SONRA ad bir FIFO'ya çevrilirse `O_RDONLY` açılışı
    bir yazarı SÜRESİZ bekler — root rotasyonu ortada asılır, önceki satırlar yazılmış kalır (sonda P1). Açılış `O_NONBLOCK`tur
    (normal dosyada etkisiz; FIFO'da yazarsız hemen döner), tanıtıcı `fstat` ile NORMAL DOSYA ve aynı inode diye ölçülür, ancak
    ondan sonra engelleyici kipe dönülüp okunur.
    `okuma` (TSK-262 — salt OKUMA yolu, `_oku`): ret `sys.exit` DEĞİL istisnadır — okuma işlemlerinin hüküm sözleşmesi
    (`OKUNAMADI (<tür>)` · `YOK`) korunsun: bağ/tür/yarış → `OkumaReddi`, kayboldu → `FileNotFoundError`, öteki açılış hatası
    (izin) AYNEN yukarı (eski `open()` gibi "OKUNAMADI"). Gövde TEKTİR: açılış bayrakları ve denetimler iki kipte AYNIDIR."""
    if h.st is None:
        sys.exit(f"hedef YOK: {h.yol} — eski içerik okunamaz, yazım YAPILMADI")
    try:
        fd = os.open(h.ad, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=h.dfd)
    except OSError as hata:
        if okuma and hata.errno == errno.ELOOP:
            raise OkumaReddi(h.yol, "SEMBOLİK BAĞ") from hata
        if okuma and hata.errno == errno.ENOENT:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), h.yol) from hata
        if okuma:
            raise
        sys.exit(f"hedef açılamadı ({hata.strerror}): {h.yol} — denetimden sonra bağa çevrilmiş olabilir, yazım YAPILMADI")
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            if okuma:
                raise OkumaReddi(h.yol, _tur_adi(st.st_mode))
            sys.exit(f"hedef açılışta normal dosya DEĞİL (yarış — FIFO/aygıt/dizine çevrilmiş olabilir): {h.yol} — okunmadı, "
                     "yazım YAPILMADI")
        if (st.st_dev, st.st_ino) != (h.st.st_dev, h.st.st_ino):
            if okuma:
                raise OkumaReddi(h.yol, _YARIS)
            sys.exit(f"hedef denetimden sonra DEĞİŞTİ (yarış): {h.yol} — yazım YAPILMADI")
        os.set_blocking(fd, True)
    except BaseException:
        os.close(fd)
        raise
    with os.fdopen(fd, "rb") if ikili else os.fdopen(fd, encoding="utf-8") as fh:
        return fh.read()


def _oku(yol: str) -> str:
    """OKUMA YOLUNUN TEK GÖVDESİ (TSK-262; TSK-261 incelemesi M2) — yardımcının BÜTÜN dosya okumaları (`alan-var` · `alanlar` ·
    `var`/`esit`/`cikar` · `json-ad-var` · `dsn-uc` · `pgpass` · `alan-farki` · değer dosyası) buradan geçer; çıplak `open()`
    YOK. ESKİ biçim `open(yol)` idi: bağı İZLER (root bağın HEDEFİNİ okur — içerik kıyasa/işliğe girer) ve FIFO'da bir yazarı
    SÜRESİZ bekler (ubuntu sahipli hedef dizinlerinde — hermes `.env`leri, `~/.hermes-botlar`, `/opt/meridian/state` — dosyayı
    FIFO'ya çeviren biri `--envanter`i, ön-denetimi ve rotasyonu hiç başlatmaz). YENİ: yazımın KURALI ve GÖVDESİ —
      (1) `lstat` (bağ izlenmez): YOK → `FileNotFoundError` (dosya adıyla — `esit`in REFERANS ayrımı ona bakar); normal dosya
          DEĞİL → `OkumaReddi` (tür ADIYLA: SEMBOLİK BAĞ · FIFO · SOKET · KARAKTER/BLOK AYGITI · DİZİN) — hiç AÇILMAZ;
      (2) `_hedef_ac(koru, koru)`: zincir güven çapasından aşağı bağ izlenmeden, bileşen izin/sahip kuralı (izinli
          `{root, dosyanın sahibi}`) — kural yazımınkiyle AYNIDIR, okuma için GEVŞETİLMEDİ; ret → `OkumaReddi` ("ZİNCİR: …");
      (3) `_tanitictan_oku(okuma=True)`: aynı dizin tanıtıcısından `O_NOFOLLOW|O_NONBLOCK`, `fstat` normal dosya + aynı inode.
    (1)'den geçip (2)/(3)'te düşen her hâl bir YARIŞTIR (denetimden sonra değişti) ve öyle adlanır. Değer basılmaz."""
    st0 = os.lstat(yol)
    tur = _tur_adi(st0.st_mode)
    if tur:
        raise OkumaReddi(yol, tur)
    h = _hedef_ac(yol, "koru", "koru")
    if isinstance(h, str):
        hedef_on = f"RED: {os.path.normpath(os.path.abspath(yol))}: hedef "
        zincir = h[len("RED: "):] if h.startswith("RED: ") else h
        raise OkumaReddi(yol, _YARIS if h.startswith(hedef_on) else f"ZİNCİR: {zincir}")
    try:
        return _tanitictan_oku(h, okuma=True)
    finally:
        os.close(h.dfd)


def _ayni_yol(a: str | None, b: str) -> bool:
    """İki yol AYNI dosya ADI mı (normalleştirilmiş, bağ İZLENMEDEN) — `esit`in okuma reddinde REFERANS/kopya ayrımı:
    `OkumaReddi.yol` `_oku`dan çağıranın verdiği biçimde, `_tanitictan_oku`dan (yarış) normalleştirilmiş biçimde gelir."""
    return a is not None and os.path.normpath(os.path.abspath(a)) == os.path.normpath(os.path.abspath(b))


def _atomik_yaz(hedef: str, icerik: str | bytes | Callable[[str], str], mod: str | int,
                sahip: str | tuple[int, int]) -> None:
    """ROTASYONUN TEK YAZIM GÖVDESİ — bağ İZLEMEYEN, tanıtıcı tabanlı, atomik (TSK-260). `yaz-dosya` · `yaz-env` · `yaz-url` ·
    `bosalt` ve bütün çalışma dizini çıktıları buradan geçer. ATOMİKTİR: yarım yazılmış bir credential dosyası birimi açılmaz
    hâle getirir.

    `icerik` dizge, bayt (`kopyala`) ya da `eski içerik → yeni içerik` fonksiyonudur (oku-değiştir-yaz: `yaz-env`/`yaz-url`; eski
    içerik `_tanitictan_oku` ile DENETLENEN dosyadan okunur). Mod/sahip: `koru` ise hedefin MEVCUDU (`lstat`), değilse argümandan
    (`kopyala`: kaynağın modu ve sayısal sahibi); sahip `-` → sahiplik değişmez (yazan süreç). Sıra: `_hedef_ac` → `_gecici_yaz` →
    `_gecici_dogrula` → dizin tanıtıcısı içinde yerine koyma → `_yazim_kusurlari` (tanıtıcı + YOL). Başarıda HİÇBİR ŞEY basılmaz
    (`--db`nin altın izi stdout'u pinler — v538 C7); ret ADLI iletiyle ve "yazım YAPILMADI" ile `sys.exit`tir."""
    h = _hedef_ac(hedef, mod, sahip)
    if isinstance(h, str):
        sys.exit(f"{h} — yazım YAPILMADI ({hedef})")
    try:
        if callable(icerik):
            icerik = icerik(_tanitictan_oku(h))
        gecici, yazilan = _gecici_yaz(h.dfd, icerik, h.mod, h.uid, h.gid, h.olculur)
        try:
            _gecici_dogrula(h.dfd, gecici, yazilan, h.yol)
            os.replace(gecici, h.ad, src_dir_fd=h.dfd, dst_dir_fd=h.dfd)
        finally:
            _gecici_sil(h.dfd, gecici)
        kusur = _yazim_kusurlari(h.dfd, h.ad, yazilan, h.mod, h.bek_uid, h.bek_gid, h.olculur, h.yol)
        if kusur:
            sys.exit(f"yazım DOĞRULANAMADI: {h.yol} — {'; '.join(kusur)}. Dosya YERİNDE bırakıldı (bizim olmayabilir): "
                     "elle incele")
    finally:
        os.close(h.dfd)


def _kopyala(kaynak: str, hedef: str) -> None:
    """BAĞ İZLEMEYEN KOPYA (`cp`nin mod/sahip koruyan `-p` biçiminin karşılığı) — aracın BÜTÜN kopya yollarının TEK gövdesi
    (TSK-261): yedek alma (`_yedek_al`), negatif kontrol yedeği ve GERİ ALMASI (`_negatif_kontrol` · `_negatif_geri_al`), `--db`nin
    eski DSN kopyası ve `--geri-al`. Eskiden kabuk root olarak `cp` koşuyordu ve İKİ uçta da bağ izliyordu: hedefte öngörülebilir
    `$hedef.yeni` adı (dizin sahibi onu önceden bir root dosyasına bağlarsa root o dosyayı yedeğin içeriğiyle EZER, `-p` sahibini
    verir — kök kod yürütmeye yeter), kaynakta da bağlı bir kaynak (seçilen dosyanın içeriği yedeğe, oradan ubuntu dizinine).
    KAYNAK yazımın denetim gövdesiyle açılır (`_hedef_ac` `koru koru`: zincir bağ izlenmeden, bileşen izin/sahip kuralı, kaynak
    bağ ya da normal dosya değilse RED) ve `_tanitictan_oku` ile BAYT olarak okunur (`O_NOFOLLOW|O_NONBLOCK`, fstat normal dosya +
    aynı inode). HEDEF `_atomik_yaz` ile yazılır (öngörülebilir ad YOK — geçici ad rastgele ve `O_EXCL|O_NOFOLLOW`, zincir ve
    hedef bağ izlenmez, yazım sonrası tanıtıcı + yol ölçülür); mod ve sahip KAYNAĞIN (`-p`). Zaman damgaları TAŞINMAZ (bedel:
    yedeğin mtime'ı yedek anıdır, geri konan dosyanınki geri alma anı — hiçbir okuyucu mtime'a bakmaz). Değer basılmaz."""
    k = _hedef_ac(kaynak, "koru", "koru")
    if isinstance(k, str):
        sys.exit(f"KAYNAK {k} — kaynak okunmadı, kopya YAPILMADI ({kaynak})")
    try:
        icerik = _tanitictan_oku(k, ikili=True)
    finally:
        os.close(k.dfd)
    _atomik_yaz(hedef, icerik, k.st.st_mode & 0o7777, (k.st.st_uid, k.st.st_gid))


#: ARACIN AD SÖZLEŞMESİ — bir alanın ADI olarak BASILABİLEN tek biçim (TSK-262 N1). Kabuktaki `_aranan_adlar`ın dosya adı
#: süzgeciyle AYNI desendir (iki dil, tek kural — v613 ayrışma çivisi ikisinin AYNI dizge olduğunu ölçer).
_AD_SOZLESMESI = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _tirnak_kapanir(metin: str, tirnak: str) -> bool:
    """`metin`de (açılış tırnağından SONRASI) kapanış tırnağı var mı? Çift tırnakta ters bölü bir sonraki karakteri kaçırır;
    tek tırnakta kaçış yoktur (dotenv/kabuk kuralı)."""
    if tirnak == "'":
        return "'" in metin
    kacis = False
    for c in metin:
        if kacis:
            kacis = False
        elif c == "\\":
            kacis = True
        elif c == tirnak:
            return True
    return False


def _env_atamalari(ham: str) -> tuple[list[tuple[str, str]], list[str]]:
    """Bir `.env` metninin `(ad, ham değer)` ATAMALARI ve atama OLMAYAN satırları. Tırnağı AYNI satırda kapanmayan bir değerin
    (çok satırlı PEM vb.) DEVAM SATIRLARI o atamanın DEĞERİNE eklenir — hiçbiri ad olarak görünmez (TSK-262 N1: PEM gövdesinin
    son base64 satırı `AQAB0123==` biçimindedir ve satır tabanlı `^AD=` desenine UYAR). Tırnak hiç kapanmazsa dosyanın kalanı o
    değerdir: ad kaçırmak, değer parçasını ad diye basmaktan güvenlidir (kaybedilen: kalan satırların ADLARI — o atama yine FARKLI
    görünür, "AYNI" denmez). Yalnız `alan-farki` okur."""
    atamalar: list[tuple[str, str]] = []
    diger: list[str] = []
    acik = ""
    for satir in ham.splitlines():
        if acik:
            ad, deger = atamalar[-1]
            atamalar[-1] = (ad, deger + "\n" + satir)
            if _tirnak_kapanir(satir, acik):
                acik = ""
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", satir)
        if not m:
            diger.append(satir)
            continue
        atamalar.append((m.group(1), m.group(2)))
        if m.group(2)[:1] in ("\"", "'") and not _tirnak_kapanir(m.group(2)[1:], m.group(2)[0]):
            acik = m.group(2)[0]
    return atamalar, diger


def _alan_haritasi(tur: str, ham: str) -> tuple[dict[str, list[str]], Counter]:
    """Çok anahtarlı bir kopyanın `(ad → ham değer(ler), adsız birimler)` haritası (YALNIZ kıyas için — hiçbir DEĞER çıktıya
    girmez). `env`: atamalar (`_env_atamalari` — çok satırlı değerin devamı DEĞERDİR; aynı ad birden çok kez geçerse her geçiş ayrı
    değerdir: çift satır da fark sayılır); `api`: motor deposunun (JSON) üst düzey anahtarları. Ad yalnız ARACIN AD SÖZLEŞMESİNE
    uyuyorsa (`_AD_SOZLESMESI`) haritaya girer; uymayan atama/anahtar ve atama OLMAYAN satır (yorum · `export X=…` · tırnaksız
    devam satırı) bir ADSIZ BİRİMDİR — yalnız SAYILIR (TSK-262 N1). Haritadaki bir adın BASILIP basılmayacağı ayrıca `alan-farki`da
    karara bağlanır (düzeltme turu 1, inceleme I1 — biçimden bağımsız kural)."""
    adsiz: Counter = Counter()
    harita: dict[str, list[str]] = {}
    if tur == "api":
        veri = json.loads(ham)
        if not isinstance(veri, dict):
            sys.exit("motor deposu JSON sözlüğü değil — alan farkı ÖLÇÜLEMEDİ")
        for k, v in veri.items():
            if _AD_SOZLESMESI.fullmatch(k):
                harita[k] = [json.dumps(v, sort_keys=True)]
            else:
                adsiz[json.dumps([k, v], sort_keys=True)] += 1
        return harita, adsiz
    atamalar, diger = _env_atamalari(ham)
    adsiz.update(diger)
    for ad, deger in atamalar:
        if _AD_SOZLESMESI.fullmatch(ad):
            harita.setdefault(ad, []).append(deger)
        else:
            adsiz[f"{ad}={deger}"] += 1
    return harita, adsiz


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
        # TEK okuma (TSK-262): satır listesi ve satır indeksi AYNI içerikten — iki ayrı okuma arasında dosya değişirse indeks
        # başka bir içeriğin satırını gösterirdi.
        ham_env = _oku(hedef)
        satirlar = ham_env.splitlines()
        idx = _env_satiri(ham_env, alan)
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

        # Oku-değiştir-yaz: eski içerik DENETLENEN dosyadan okunur (`_atomik_yaz` → `_tanitictan_oku`, TSK-260) — eskiden
        # `_oku(hedef)` yolu izliyordu: hedef bir bağsa içerik bağın HEDEFİNDEN okunup ubuntu dizinine yazılırdı.
        def _env_yeni(ham: str) -> str:
            satirlar = ham.splitlines(keepends=True)
            idx = _env_satiri_yazim(ham, alan)
            tirnak, son = _tirnak_ve_son(satirlar[idx].split("=", 1)[1])
            satirlar[idx] = f"{alan}={tirnak}{_onek(onek)}{_deger_dosyadan(dgr)}{tirnak}{son}"
            return "".join(satirlar)
        _atomik_yaz(hedef, _env_yeni, mod, sahip)
    elif op == "yaz-url":            # <hedef> <deger> <mod> <sahip>
        hedef, dgr, mod, sahip = argv[2:6]

        def _url_yeni(ham: str) -> str:          # oku-değiştir-yaz — `yaz-env` ile aynı gerekçe
            p = urlsplit(ham.strip("\r\n"))
            if not p.username:
                sys.exit(f"DSN'de kullanıcı yok: {hedef} — parola değiştirilemez")
            yer = p.hostname or ""
            if p.port:
                yer += f":{p.port}"
            netloc = f"{quote(p.username, safe='')}:{quote(_deger_dosyadan(dgr), safe='')}@{yer}"
            return urlunsplit((p.scheme, netloc, p.path, p.query, p.fragment)) + "\n"
        _atomik_yaz(hedef, _url_yeni, mod, sahip)
    elif op == "cikar":              # <tur> <hedef> <alan> <onek> <cikti>
        tur, hedef, alan, onek, cikti = argv[2:7]
        _atomik_yaz(cikti, _cikar(tur, hedef, alan, onek) + "\n", "0600", "-")
    elif op == "esit":               # <tur1> <h1> <a1> <o1> <tur2> <h2> <a2> <o2>
        # YOK ≠ OKUNAMADI (TSK-064 (d-1), 2026-09-17). İlk biçim her `OSError`u "OKUNAMADI"
        # sayıyordu ve A1 envanteri silinmiş `.dash.env`i o kelimeyle raporladı: triyaj "izin mi
        # bozuk?" diye yanlış soruyu sordu. Dosya YOKLUĞU (`FileNotFoundError`) ayrı bir kovadır,
        # izin/dizin arızası "OKUNAMADI" kalır. Yokluk REFERANS tarafındaysa kopya satırına "YOK"
        # basmak VAR olan kopyayı yok diye raporlamak olurdu — sebep ADIYLA söylenir.
        # OKUMA REDDİ (TSK-262 — bağ · FIFO · soket · aygıt · zincir · yarış) "OKUNAMADI (<tür>)"dır ve TARAFIYLA söylenir:
        # reddedilen REFERANSSA kopya satırına "OKUNAMADI" basmak, okunabilen kopyayı arızalı gösterirdi (YOK ile aynı gerekçe).
        try:
            a = _cikar(*argv[2:6])
            b = _cikar(*argv[6:10])
        except FileNotFoundError as yok:
            print("REFERANS YOK" if yok.filename == argv[3] else "YOK")
            return
        except OkumaReddi as ret:
            print(f"{'REFERANS ' if _ayni_yol(ret.yol, argv[3]) else ''}OKUNAMADI ({ret.tur})")
            return
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
        # `esit` ile AYNI ayrım (bkz. şerhi): ilk biçim her `OSError`u "YOK" sayıyordu, yani var
        # ama okunamayan bir referans "dosya yok" diye raporlanıyordu — `esit`in tam tersi yönde
        # aynı kovalama hatası. Yokluk "YOK", öteki `OSError`lar "OKUNAMADI".
        tur, hedef, alan = argv[2:5]
        try:
            print("VAR" if _cikar(tur, hedef, alan, "-") else "BOŞ")
        except FileNotFoundError:
            print("YOK")
        except OkumaReddi as ret:
            print(f"OKUNAMADI ({ret.tur})")      # TSK-262: bağ/FIFO/aygıt/zincir — tür ADIYLA, değer okunmadı
        except AlanArizasi as ariza:
            print(f"ÇİFT SATIR ({ariza.adet})" if ariza.adet > 1 else "ALAN YOK")
        except OSError:
            print("OKUNAMADI")
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
        except OkumaReddi as ret:
            print(f"OKUNAMADI ({ret.tur})")      # TSK-262: tür ADIYLA (çağıran `_secrets_json_tara` taramayı EKSİK der)
            return
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
        except OkumaReddi as ret:
            # TSK-262: okuma REDDİ bir yokluk DEĞİLDİR — bağ/FIFO/aygıt/zincir ADIYLA durur (stderr; stdout'a hiçbir ad
            # çıkmaz). Çağıran (`_beyan_disi_tara`) dosyayı ayrıca "TARANAMADI" diye sayar: tarama EKSİK kalır, susmaz.
            sys.exit(f"alanlar: {ret} — alan adları OKUNMADI")
        except OSError:
            # sessiz-yutma: dosya YOKLUĞU burada bir bulgu DEĞİLDİR — çağıran (`_beyan_disi_tara`)
            # varlığı ZATEN `test -e`/`-L` ile ölçtü ve yokluğu ORADA beyan eder. Boş liste dönmek
            # "taranacak alan yok" demektir, bir hatayı gizlemek değil.
            return
        gorulen = set()
        for satir in ham.splitlines():
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=", satir)
            if m and m.group(1) not in gorulen:
                gorulen.add(m.group(1))
                print(m.group(1))
    elif op == "alan-var":           # <hedef> <alan> [tek] → dosyada `^alan=` var mı (bool)
        # `tek` (G3b Task 3 — yazım öncesi ön-denetim, `_hedef_on_denetim`): kural `yaz-env`inkiyle AYNI FONKSİYONDUR
        # (`_env_satiri`: TAM 1 satır — 0 ya da >1 yazımı durdurur), yani kapıdan geçen her hedefi `yaz-env` yazabilir.
        # Çıktı: VAR | ALAN YOK | ÇİFT SATIR (n) | DOSYA YOK | OKUNAMADI. `tek`SİZ biçim (beyan dışı tarama) "EN AZ bir
        # satır" der ve DEĞİŞMEDİ: çift satır orada da bir kopyadır, `esit` onu ayrıca ÇİFT SATIR diye raporlar.
        # `dolu` (5. argüman, `tek` ile — G3b dal sonu M2; YALNIZ `--tohumla-sohbet`): TAM 1 satır VAR ama değer boş/yalnız
        # boşluk (tırnaklar soyulmuş) ise "BOŞ" — tohumlama onu EKSİK sayar. Ön-denetim `dolu` İSTEMEZ: orada değersiz satır
        # meşru yer tutucudur (rotasyon değeri yazar — v604 A16b). Değer BASILMAZ, yalnız hüküm.
        hedef, alan = argv[2:4]
        tek = argv[4:5] == ["tek"]
        dolu = tek and argv[5:6] == ["dolu"]
        try:
            ham = _oku(hedef)
        except FileNotFoundError:
            print("DOSYA YOK" if tek else "YOK")
            return
        except OkumaReddi as ret:
            # TSK-262: İKİ biçimde de tür ADIYLA — `tek` (ön-denetim: `OKUNAMADI*` → ölçülemedi, rotasyon BAŞLAMAZ) ve `tek`siz
            # (beyan dışı tarama: "YOK" demek reddedilen dosyayı taranmış gibi gösterirdi; çağıran "TARANAMADI" der).
            print(f"OKUNAMADI ({ret.tur})")
            return
        except OSError:
            print("OKUNAMADI" if tek else "YOK")
            return
        except UnicodeDecodeError:
            # `tek` (yazım kapısı — G3b Task 4, Task 3 incelemesi M2): UTF-8 dışı bayt taşıyan dosyada alan SAYILAMAZ; bu
            # bir ÖLÇÜM yokluğudur ve adıyla döner (çağıran `olcum_yok`). Eskiden traceback + çıkış 1'di. `tek`SİZ biçim
            # (beyan dışı tarama) DEĞİŞMEDİ: orada hata metni görünür kalır — "YOK" basmak dosyayı taramadan geçirirdi.
            if not tek:
                raise
            print("OKUNAMADI (UTF-8 değil)")
            return
        if tek:
            try:
                _env_satiri(ham, alan)
            except AlanArizasi as ariza:
                print(f"ÇİFT SATIR ({ariza.adet})" if ariza.adet > 1 else "ALAN YOK")
                return
            print("BOŞ" if dolu and not _cikar("env", hedef, alan, "-").strip() else "VAR")
            return
        print("VAR" if re.search(r"^" + re.escape(alan) + r"=", ham, flags=re.M) else "YOK")
    elif op == "dizin-denetle":      # <kök> <dizin> <sahip> <grup> → TAMAM[ (not)] | YOK | RED: <neden>
        # `--tohumla-sohbet`in (1) dizin kapısı (G3b dal sonu M1): `tohumla-env`in yazımda koşacağı AYNI zincir denetimi,
        # HİÇBİR yazımdan ÖNCE ve bütün hedefler için — bir dizin reddedilirse hiçbir dosya yazılmaz. Yalnız hüküm basılır.
        kok, dizin, sahip, grup = argv[2:6]
        uid, _, olculur = _kimlik(sahip, grup)
        fd, hukum = _dizin_ac(kok, dizin, frozenset({uid}), olculur)
        if fd is None:
            print(hukum)
            return
        os.close(fd)
        print("TAMAM" if olculur else "TAMAM (sahip ÖLÇÜLMEDİ: root değil — yalnız çivi makinesi)")
    elif op == "tohumla-env":        # <kök> <hedef> <mod> <sahip> <grup> (<alan> <deger dosyasi>)+ — YALNIZ YOK olan hedef
        # `--tohumla-sohbet`in (G3b Task 4) TEK yazım yolu: `.env`i SIFIRDAN kurar (`yaz-env` satırın değerini yazar, dosya
        # KURMAZ). Değer YALNIZ dosyadan (`_deger_dosyadan`: boş → dur); argv'de yalnız ALAN ADI ve dosya YOLU vardır.
        # Hedef VARSA reddeder — iki katman: önce `lexists` (okunur ileti), sonra dizin tanıtıcısı içindeki `os.link`
        # (denetim ile yazım arasındaki yarışı çekirdek kapatır). Dizin zinciri bağ İZLENMEDEN açılır ve yazım SONRASI ölçülür
        # (`_dizin_ac` · `_yeni_dosya_yaz` — dal sonu M1). Bütün denetimler YAZIMDAN ÖNCE; stdout'a yalnız doğrulama hükmü.
        kok, hedef, mod, sahip, grup = argv[2:7]
        ciftler = argv[7:]
        if not ciftler or len(ciftler) % 2:
            sys.exit("tohumla-env: <alan> <değer dosyası> ÇİFTLERİ eksik ya da tek — yazım YAPILMADI")
        if os.path.lexists(hedef):
            sys.exit(f"hedef ZATEN VAR: {hedef} — var olan dosyaya DOKUNULMAZ, yazım YAPILMADI")
        satirlar, gorulen = [], set()
        for alan, dgr in zip(ciftler[0::2], ciftler[1::2]):
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", alan) or alan in gorulen:
                sys.exit(f"tohumla-env: alan adı geçersiz ya da çift: {alan!r} — yazım YAPILMADI")
            gorulen.add(alan)
            d = _deger_dosyadan(dgr)
            if "\n" in d or "\r" in d:
                # Çok satırlı değer `.env`e İKİNCİ bir satır sokar (satır enjeksiyonu) — değer BASILMAZ, yalnız alan.
                sys.exit(f"tohumla-env: {alan} değeri TEK satır değil — yazım YAPILMADI")
            satirlar.append(f"{alan}={d}\n")
        uid, gid, olculur = _kimlik(sahip, grup)
        dfd, hukum = _dizin_ac(kok, os.path.dirname(hedef), frozenset({uid}), olculur)
        if dfd is None:
            sys.exit(f"hedef dizini {hukum} — yazım YAPILMADI ({hedef})")
        try:
            print(_yeni_dosya_yaz(dfd, os.path.basename(hedef), "".join(satirlar), int(mod, 8), uid, gid, olculur, hedef))
        finally:
            os.close(dfd)
    elif op == "kopyala":            # <kaynak> <hedef> — bağ İZLEMEYEN kopya, mod/sahip kaynağın (TSK-261)
        # Kabuğun BÜTÜN kopya yolları (yedek · negatif kontrol yedeği ve geri alması · `--db` eski DSN · `--geri-al`) buradan
        # geçer; kabukta root `cp` KALMADI (v611 F1s). Başarıda hiçbir şey basılmaz; ret adlı iletiyle (`_kopyala`).
        _kopyala(*argv[2:4])
    elif op == "alan-farki":         # <env|api> <yedek> <güncel> [hariç…] [--basilir <ad…>] [--sonek <sonek…>] → AYNI | FARKLI: …
        # `--geri-al` (TSK-261 inceleme I2): çok anahtarlı bir dosya BÜTÜN döner; yedekten sonra değişmiş BAŞKA alanların (geri
        # alınan alt komutun kendi alanları HARİÇ) ADLARI önceden söylenir. Yalnız adlar basılır; değerler yalnız kıyaslanır.
        # BASILAN AD — BİÇİMDEN BAĞIMSIZ KURAL (TSK-262 düzeltme turu 1, inceleme I1): tırnak takibi yalnız satır TAM `AD="` ile
        # başlıyorsa çalışır; `export AD="…` · `AD = "…` · baştaki boşluk · ters bölü devamı · tırnaksız çok satırda base64 devam
        # satırı (`QWER0123==`) yine `^AD=` desenine düşüyor ve "ad" diye basılıyordu (sondası `n1_sonda.log`). Bir ad YALNIZ
        #   (a) sözleşmeye uyan bir atama olarak İKİ dosyada da AYNI SAYIDA var ve değeri farklıysa (çokluk şartı: düzeltme
        #       turu 2, yeniden inceleme Y1 — aşağıdaki `basilan` şerhi), ya da
        #   (b) aracın ARANAN ADLARINDA (`--basilir` ← kabuk `_aranan_adlar`) ya da SIR-ADI SONEKLERİNDEN biriyle bitiyorsa
        #       (`--sonek` ← kabuk `_SIR_ADI_SONEKLERI`; anlam `_sir_adi_mi`ninki: son-ek eşleşmesi — v613 D7 ayrışma çivisi)
        # basılır. Gerekçe: rotasyonda değişen bir PEM parçası yalnız BİR tarafta bulunur ve base64'te `=` yalnız dolguda geçtiği için
        # iki tarafta "adı" aynı, "değeri" farklı bir parça doğmaz; aranan adların ve soneklerin hepsi `_` taşır (standart base64
        # alfabesinde yok). Kalan her fark — sözleşme dışı birim, tek taraftaki sırsız ad — YALNIZ SAYIYLA: "+ adsız N satır" (sayı
        # "AYNI" demeyi engeller). BEDEL: yedekten sonra eklenen/silinen sırsız bir ad adıyla değil sayıyla söylenir (v613 D8).
        # Sayım: adsız birimlerin çoklu küme simetrik farkı (değişen tek satır = 2) + basılmayan tek taraflı adların geçiş sayısı.
        tur, yedek, guncel = argv[2:5]
        kovalar: dict[str, set[str]] = {"--haric": set(), "--basilir": set(), "--sonek": set()}
        kova = kovalar["--haric"]
        for jeton in argv[5:]:
            if jeton in kovalar:
                kova = kovalar[jeton]
            else:
                kova.add(jeton)
        haric, basilir, sonekler = kovalar["--haric"], kovalar["--basilir"], tuple(kovalar["--sonek"])
        try:
            a, a_adsiz = _alan_haritasi(tur, _oku(yedek))
            b, b_adsiz = _alan_haritasi(tur, _oku(guncel))
        except OSError as hata:
            # Bağ · FIFO · aygıt · zincir (`OkumaReddi` — ADLI, yol + tür) ya da dosya YOK/izin: okunmadı; çağıran "ÖLÇÜLEMEDİ" der.
            sys.exit(f"{hata} — okunmadı, alan farkı ÖLÇÜLEMEDİ")
        except ValueError as hata:
            # Yasa 4 — sessiz değil: UTF-8 dışı bayt ya da bozuk JSON ADIYLA çıkıştır; çağıran "ÖLÇÜLEMEDİ" der.
            sys.exit(f"alan farkı ÖLÇÜLEMEDİ ({type(hata).__name__}) — değer basılmadı")
        fark = sorted(ad for ad in set(a) | set(b) if ad not in haric and a.get(ad) != b.get(ad))
        # Kural (a) EŞİT ÇOKLUĞA bağlıdır (düzeltme turu 2, yeniden inceleme Y1): aynı PEM son satırı yedekte bir, güncelde iki kez
        # geçince (anahtar ikinci bir değişkene kopyalandı / bir kopya silindi) parça iki tarafta da "var" ve değer LİSTESİ farklı
        # görünüyordu → AD diye basılıyordu. Eşit çoklukta base64 parçasının değerleri (yalnız dolgu `=`/`==`, satır uzunluğuyla
        # belirli) iki tarafta AYNIDIR — farklı görünemez. BEDEL: gerçek bir adın ÇİFT SATIR'a dönüşmesi (ya da tekleşmesi) adla değil
        # SAYIYLA söylenir (ön-denetim ve envanter ÇİFT SATIR'ı zaten ADIYLA raporlar — v613 D9).
        basilan = [ad for ad in fark if (ad in a and ad in b and len(a[ad]) == len(b[ad])) or ad in basilir
                   or ad.endswith(sonekler)]
        adsiz = (sum(((a_adsiz - b_adsiz) + (b_adsiz - a_adsiz)).values())
                 + sum(len(a.get(ad, [])) + len(b.get(ad, [])) for ad in fark if ad not in basilan))
        parca = [" ".join(basilan)] if basilan else []
        if adsiz:
            parca.append(f"{'+ ' if basilan else ''}adsız {adsiz} {'anahtar' if tur == 'api' else 'satır'}")
        print(f"FARKLI: {' '.join(parca)}" if parca else "AYNI")
    elif op == "hedef-denetle":      # <hedef> <mod> <sahip> → TAMAM | RED: <neden> — YAZIM YOK
        # Rotasyonun yazım ÖNCESİ ön-denetimi (`_hedef_on_denetim`, TSK-260): yazımın koşacağı AYNI gövde (`_hedef_ac` —
        # zincir bağ izlenmeden · bileşen izin/sahip · hedef bağ/normal dosya). Bağlı ya da gevşek bir hedef rotasyonu
        # YARIDA bırakmaz, hiç başlatmaz. Yalnız hüküm basılır (yol ve neden — değer DEĞİL).
        h = _hedef_ac(*argv[2:5])
        if isinstance(h, str):
            print(h)
            return
        os.close(h.dfd)
        print("TAMAM")
    else:
        sys.exit(f"bilinmeyen işlem: {op}")


if __name__ == "__main__":
    # OKUMA REDDİNİN TEK KAPISI (TSK-262): reddi kendi hüküm sözleşmesiyle yakalamayan işlem (`cikar` · `pgpass` · `dsn-uc` ·
    # değer dosyası okuyan yazımlar) burada ADLI iletiyle durur — yol + tür, değer YOK; traceback değil, çıkış 1.
    try:
        main(sys.argv)
    except OkumaReddi as ret:
        sys.exit(f"{ret} — okunmadı, işlem YAPILMADI")
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
  # KASA YOLU `--db` (TSK-064): reçete evreye göredir ve dosya kopyası ÖNERMEZ — bkz. `_db_kasa_recetesi`.
  if [ -n "$DB_KASA_EVRE" ]; then _db_kasa_recetesi; return 0; fi
  # KASA YOLU `--cp` (TSK-226b): aynı gerekçe — render hedefi ve yan dosya Agent'ındır.
  if [ -n "$CP_KASA_EVRE" ]; then _cp_kasa_recetesi; return 0; fi
  # KASA YOLU genel döngü (TSK-064 takibi): kasa geri alımı DOSYA geri alımının ÖNÜNDE — bkz. `_genel_kasa_recetesi`.
  if [ -n "$GENEL_KASA_EVRE" ]; then _genel_kasa_recetesi; return 0; fi
  local birimler
  # sessiz-yutma: `_birimler` bilinmeyen bir alt komutta `die` eder ve o hata METNİ burada hükme
  # GİRMEZ — burası çıkış YOLUDUR, hüküm çoktan verilmiştir ve reçetenin susması, hükümden daha
  # pahalıya mal olurdu. Yutulan tek şey stderr metnidir; ÖLÇÜLEMEDİ hâli sessiz DEĞİL, görünür
  # bir dizgeyle beyan edilir (aşağıdaki `(birim listesi ölçülemedi)`).
  birimler="$(_birimler "$ALT" 2>/dev/null || echo '(birim listesi ölçülemedi)')"
  # REÇETE ARACIN KENDİ GÜVENLİ YOLUNU GÖSTERİR (TSK-261): `sudo cp -p <yedek>/<yol> /<yol>` operatörün elinde root
  # olarak hedef BAĞINI izlerdi — tam da bu koşumun "DOĞRULANAMADI" ile durduğu (bağa çevrilmiş hedef) anda.
  # `--geri-al` yalnız bu alt komutun tablo yollarını, bağ İZLEMEDEN, yedeğin mod/sahibiyle geri koyar.
  # shellcheck disable=SC2086
  echo ">> GERİ ALMA (bu koşum YEDEK aldı — başarıda da arızada da geçerli):
     sudo $0 --geri-al $YEDEK   (yedekteki kopyaları üretim yollarına bağ İZLEMEDEN geri koyar; önce --kuru ile bak)
     sonra yeniden başlat: $(_recete_birimleri $birimler)" >&2
  return 0
}

# ÇIKIŞ YOLU TEK FONKSİYONDUR. `trap 'birinci; ikinci' EXIT` içinde `birinci` `exit` ederse
# `ikinci` HİÇ KOŞMAZ (bash EXIT-trap semantiği, ölçüldü 2026-09-08) — iki iş yan yana yazıldığı
# an, ikincisi birincinin arıza yoluna REHİN olur.
_cikis() {
  _yarim_yedek_isaretle
  _geri_alma_recetesi
  _temizle
}

# `sudo python3` — yardımcı root olarak koşar (0400 credential dosyalarını okur/yazar).
py() { sudo python3 -I "$ISLIK/yardimci.py" "$@"; }

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
# KAYNAK BAĞ İZLENMEDEN OKUNUR (TSK-261, CWE-59): kopya yardımcının `kopyala` işlemidir — kaynak yazımın
# denetim gövdesiyle açılır (zincir bağ izlenmeden, bileşen izin/sahip kuralı, kaynak bağ ya da normal dosya
# değilse RED) ve BAYT olarak taşınır; mod ve sahip kaynağın (eski `cp -p`nin koruduğu iki şey). Eskiden root
# `cp` KAYNAK bağını izliyordu: ubuntu `.env`ini ön-denetimden sonra bir sır dosyasına bağlarsa o dosyanın
# içeriği yedeğe, negatif kontrolün geri alması ya da reçete ile oradan ubuntu dizinine giderdi. Bağlı kaynak
# artık ADIYLA reddedilir ve rotasyon BAŞLAMAZ (hiçbir kopya yazılmadan önce). Varlık `-L` ile de sorulur:
# `test -e` bağı izler, sarkık bir bağ "dosya yok" diye sessizce ATLANIRDI. Çivi: v611 B1.
_yedek_al() {
  local alt="$1" koken="${2:-}" yol hedef aday damga
  # SIRA: aday → YARAT → KOPYALA → ata. `YEDEK` globaldir ve `_geri_alma_recetesi`nin TEK kapısıdır
  # (`[ -n "$YEDEK" ]`), yani atama "yedek ALINDI" beyanıdır. Atamayı `install -d`den ÖNCE
  # yapmak o beyanı yalana çevirirdi: dizin doğmadan (disk dolu · yetki · aynı saniyede ikinci
  # koşum) düşen bir koşumda EXIT trap ">> GERİ ALMA (bu koşum YEDEK aldı…)" basar ve operatör
  # VAR OLMAYAN bir dizinden geri koymaya çalışır — reçetenin kendi şerhinin yasakladığı hâl.
  # Ölçüldü (inceleme D7/Y2, 2026-09-08): `install` şimi düşürüldü → dizin HİÇ doğmadı, reçete
  # YİNE basıldı, çıkış 1. Çivi: `test_P14`. Aynı gerekçeyle atama artık KOPYALARDAN da sonradır
  # (TSK-261): bir kaynak reddedilirse yedek YARIMDIR ve hiçbir kopya yazılmamıştır — reçete basılmaz.
  damga="$(date -u +%Y%m%dT%H%M%SZ)"
  aday="$KOK/root/sir-yedek-$damga-$alt"
  # `.yarim` eşi de sorulur (TSK-262 N2): aynı saniyede yarıda kalmış bir koşumun işaretli dizini varken yeni yarım yedek
  # onun İÇİNE taşınırdı (`mv` var olan dizine taşır).
  if [ -e "$aday" ] || [ -e "$aday.yarim" ]; then die "yedek dizini ZATEN VAR: $aday (aynı saniyede ikinci koşum?)"; fi
  # `install -o <kullanıcı> -g <grup>` — İKİ AYRI BAYRAK. Tek `-o root:root` HATA verir
  # (ölçüldü 2026-09-07: `install: invalid user`), ve o hata `set -e` altında pencereyi yakar.
  sudo install -d -m 0700 -o root -g root "$aday"
  # YARIM YEDEK İŞARETİ (TSK-262 N2): dizin doğdu ama kopyalar bitmedi — bu andan atamaya kadar HER çıkış (adlı ret · `set -e` ·
  # sinyal) EXIT trap'inde dizini `.yarim` adına taşır (`_yarim_yedek_isaretle`): geçerli adlı yarım bir dizin `--geri-al`
  # girdisi olur, eksik dosyaları "o koşumda yoktu" diye yanlış adlandırıp SESSİZ bir yarım geri alma yapardı.
  _YEDEK_YARIM="$aday"
  # KÖKEN (TSK-262 N2) — YALNIZ `--geri-al`ın ön yedeğinde: girdi yedeğinin yolu + alt komut + UTC damga (sır YOK). Okuyanlar:
  # `_yedekleri_listele` (envanterde "ÖN YEDEK" diye ayırır) ve `geri_al` (girdi bir ön yedekse söyler). Kopyalardan ÖNCE yazılır:
  # yarıda kalan bir ön yedek de kökenini taşır. Yazım `py kopyala` (işlik → yedek; bağ izlemez) — kabukta yeni bir root yazım yolu YOK.
  if [ -n "$koken" ]; then
    printf 'tur: on-yedek\nkaynak: --geri-al %s\nalt: %s\ndamga: %s\n' "$koken" "$alt" "$damga" > "$ISLIK/koken"
    chmod 600 "$ISLIK/koken"
    py kopyala "$ISLIK/koken" "$aday/KOKEN"
  fi
  while read -r _alt _sir tur yol alan _mod _sahip _onek; do
    [ "$_alt" = "$alt" ] || continue
    # `api` satırının disk karşılığı da YEDEKLENİR (bkz. `_disk_yolu`): negatif kontrol o kopyayı
    # SİLER ve geri alma ancak yedekten yapılabilir. Yedek geri almanın ÖN KOŞULUDUR — motor ölü
    # ya da yetki reddediyorsa `POST` ile geri koymak da mümkün olmaz, dosya geri yazımı olur.
    yol="$(_disk_yolu "$tur" "$yol")" || continue
    hedef="$KOK$yol"
    if sudo test -e "$hedef" || sudo test -L "$hedef"; then
      sudo install -d -m 0700 -o root -g root "$aday$(dirname "$yol")"
      py kopyala "$hedef" "$aday$yol" \
        || die "yedek ALINAMADI: $yol — kaynak bağ İZLENMEDEN okunamadı (yardımcının adlı reddi yukarıda).
     İşlem (rotasyon / geri alma) BAŞLAMADI: hiçbir kopya yazılmadı, hiçbir birim yeniden başlatılmadı (yarım yedek: $aday —
     çıkışta '$aday.yarim' adına taşınır; --geri-al onu girdi olarak KABUL ETMEZ).
     Kaynağı değerini BASMADAN incele: sudo stat -c '%U:%G %a %F %n' $yol ve üst dizinleri"
      oldu "yedek: $yol"
    else
      echo "  · yedek ATLANDI (dosya yok): $yol"
    fi
  done < <(_kopyalar)
  _YEDEK_YARIM=""
  YEDEK="$aday"
  echo "  yedek dizini: $YEDEK"
}

#: YARIM YEDEK — `_yedek_al`ın dizini doğurduğu ama kopyaları BİTİREMEDİĞİ yol (boş = yok). Okuyan: `_yarim_yedek_isaretle`.
_YEDEK_YARIM=""

# YARIM YEDEK İŞARETİ (TSK-262 N2; TSK-261 yeniden incelemesi N2) — EXIT trap'inin İLK adımı (`_cikis`). Yarıda kalan yedek
# dizini `<ad>.yarim` adına taşınır: `--geri-al`ın girdi kalıbı (`sir-yedek-<UTC ts>-<alt>`, alt `[a-z][a-z0-9-]*`) onu
# REDDEDER ve `geri_al` ayrıca adıyla söyler. Eskiden yarım dizin GEÇERLİ adla kalıyordu: sonradan onunla `--geri-al` eksik
# dosyaları "o koşumda dosya yoktu — yedek ATLANMIŞTI" diye yanlış adlandırıp yarım geri alma yapardı. Taşıma `/root`un
# (root 0700) İÇİNDEDİR — bağ yarışı yok. Taşıma düşerse SUSMAZ: dizin adıyla "girdi olarak KULLANMA" der. Çıkış kodu değişmez.
# Çiviler: v613 E1 (`--geri-al` ön yedeği · `.yarim` girdisi reddedilir) · E2 (rotasyon yedeği).
_yarim_yedek_isaretle() {
  [ -n "${_YEDEK_YARIM:-}" ] || return 0
  if sudo mv "$_YEDEK_YARIM" "$_YEDEK_YARIM.yarim"; then
    echo "!! YARIM YEDEK: $_YEDEK_YARIM.yarim — yedek alma yarıda kaldı (dosyaları EKSİK); --geri-al bu dizini girdi olarak KABUL ETMEZ" >&2
  else
    echo "!! YARIM YEDEK İŞARETLENEMEDİ: $_YEDEK_YARIM — yedek alma yarıda kaldı (dosyaları EKSİK); bu dizini --geri-al girdisi olarak KULLANMA" >&2
  fi
  _YEDEK_YARIM=""
  return 0
}

# `/root` altını ubuntu kabuğunda `ls $YEDEK_KOK/sir-yedek-*` ile listelemek ÇALIŞMAZ: glob
# ubuntu'nun kabuğunda, yani /root'u OKUYAMAYAN süreçte açılır ve boş döner (ölçüldü). Glob
# root'un kabuğunda açılmalı — `sudo sh -c '...'`.
# ÜÇ SINIF ayrı adlanır (TSK-262 N2): rotasyon yedeği (yalnız yol — eski satır AYNEN) · `--geri-al`ın ÖN YEDEĞİ (`KOKEN` dosyası
# taşır: girdi yedeği + alt komut + damga; bir geri almadan sonra en yeni `-<alt>` yedeği odur ve geri alınmak istenen YENİ hâli
# taşır — listeden "son yedeği" seçen operatör yanılmasın) · YARIM yedek (`.yarim` — girdi DEĞİL). Ayrım KÖKEN DOSYASIYLA, ad
# deseniyle DEĞİL: ön yedek geçerli bir `--geri-al` girdisidir (geri almanın geri alınması) ve adı değişseydi girdi kalıbı iki
# biçim tanımak zorunda kalırdı; köken dizinin İÇİNDE yaşar, ad değişse de kaybolmaz. Varlık `test -f` ile — içerik OKUNMAZ.
_yedekleri_listele() {
  local d
  while read -r d; do
    [ -n "$d" ] || continue
    case "$d" in
      *.yarim) echo "$d  (YARIM — yedek alma yarıda kaldı, dosyaları EKSİK; --geri-al girdisi DEĞİL)" ;;
      *) if sudo test -f "$d/KOKEN"; then echo "$d  (ÖN YEDEK — bir --geri-al'dan ÖNCE alındı; köken: $d/KOKEN)"
         else echo "$d"; fi ;;
    esac
  done < <(sudo sh -c "ls -1d '$KOK/root'/sir-yedek-* 2>/dev/null" || true)   # sessiz-yutma: hiç yedek
  # yoksa `ls` 2 döner; "yedek yok" bir ARIZA DEĞİLDİR (ilk koşum) ve raporu kesmemeli.
}

# =================================================================================================
# DEĞER ÜRETİMİ
# =================================================================================================
# Uzunluk ÜRETİMDEN SONRA denetlenir: `openssl` bir konteyner/PATH kazasıyla boş çıktı verirse
# boş bir credential dosyası yazılır ve birim sessizce YETKİSİZ kalır (2026-09-07 vakası).
# `_uret <sınıf> [çıktı]` — çıktı verilmezse `$ISLIK/yeni` (eski yol ve `--cp --vault`); kasa yolunun
# `--uret`i (`_vault_uret`) istemin yazdığı dosyaya (`$ISLIK/vault_yeni`) üretir: değer İKİNCİ bir
# dosyaya kopyalanmaz.
_uret() {
  local sinif="$1" hedef_uz cikti
  cikti="${2:-$ISLIK/yeni}"
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

#: ESKİ YOLUN ÜRETİM SINIFI — `--<alt> --vault --uret` (TSK-226c) değeri eski yolun AYNI yöntemiyle
#: üretir. Tanım kümesi GENEL kasa döngüsünden geçen üreticilerdir: `db` (eski yol `_uret b64`) kendi
#: kasa dalındadır ve `--uret` orada kapsam dışıdır; `cp` kendi dalında ZATEN üretir; `openrouter`
#: üretmez. KOPYA KAÇINILMAZ (eski yol gövdeleri sınıfı literal taşır ve o gövdelere dokunmak bu turun
#: "`--uret` yokken davranış birebir" sözleşmesini riske atardı) → ayrışma çivisi: v557 A1 her alt
#: komutta bu tabloyu eski yol gövdesinin `_uret <sınıf>` çağrısıyla kıyaslar. Tanımsız alt komut 1 döner.
_uret_sinifi() {
  case "$1" in
    kapi|dash|apisix-admin) echo b64 ;;
    tenant) echo hex ;;
    #: `api-sunucu` (G3b, Rol-1 G3b-R5): Hermes ≥16 karakter ve yer tutucu olmayan değer ister (`has_usable_secret`) —
    #: kiracı emsali, 64 hex. AYRI kol: v557 mutasyon çapası `tenant)` satırını tek başına değiştirir.
    api-sunucu) echo hex ;;
    #: `kapi-bot-<ad>` (G3b Task 3): kapı tüketici anahtarı — `kapi` emsali b64 (48 kr; A1'deki mevcut değerler de 48 bayt,
    #: ölçüldü 2026-09-30). Bot başı İÇ alt ad ailesi TEK kolda (glob) — bot sayısıyla büyümez.
    kapi-bot-*) echo b64 ;;
    *) return 1 ;;
  esac
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

# TEK SATIR YAZIMI — `_yaz` (rotasyon: alt komutun TÜM kopyaları, yeni değer) ile `esitle` (yalnız
# AYRI satırlar, referans değer) AYNI yoldan yazar; iki yazım yolu sessizce ayrışmasın diye gövde
# TEKtir (tek-kaynak yasası, 2026-09-13). Parametreler kopya tablosunun sütunları + değer dosyası.
_yaz_satir() {
  local sir="$1" tur="$2" yol="$3" alan="$4" mod="$5" sahip="$6" onek="$7" dgr="$8" hedef
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
           # hedef dizinin TANITICISI içinde geçici dosya + `fchown`/`fchmod` + yerine koyma ile
           # kendisi kurar (TSK-260 — bağ izlenmez), yani dosya daha ilk anından itibaren doğru
           # izinle var olur (0644'lük bir ara hâl hiç doğmaz).
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
}

_yaz() {
  local alt="$1" sadece_sir="${2:-}" dgr="${3:-$ISLIK/yeni}" tur_suzgeci="${4:-}"
  local _alt sir tur yol alan mod sahip onek
  while read -r _alt sir tur yol alan mod sahip onek; do
    [ "$_alt" = "$alt" ] || continue
    [ -z "$sadece_sir" ] || [ "$sir" = "$sadece_sir" ] || continue
    if [ -n "$tur_suzgeci" ]; then case " $tur_suzgeci " in *" $tur "*) ;; *) continue ;; esac; fi
    _yaz_satir "$sir" "$tur" "$yol" "$alan" "$mod" "$sahip" "$onek" "$dgr"
  done < <(_kopyalar)
}

# YAZIM ÖNCESİ HEDEF ÖN-DENETİMİ — YARIM ROTASYON YOK (G3b, 2026-09-30).
# `_yaz_satir` bir `env`/`url` hedefini YARATAMAZ (satırın DEĞERİNİ yazar, dosyayı KURMAZ) ve yokluğu yalnız
# YAZIM ANINDA soruyordu. O ana gelindiğinde yedek alınmış, değer üretilmiş, kasa yolunda `kv put` yapılmış ve
# tabloda ÖNCEKİ satırlar YENİ değerle yazılmış olurdu; tüketiciler yeniden başlamaz — yarım rotasyon. Yeni
# sohbet `.env`leri (G3b: `--tohumla-sohbet` kurar) tabloya girdiği an bu hâl her rotasyonda doğardı.
# Artık aynı soru dağıtım kapısında, HİÇBİR yazımdan (yedek · değer üretimi · kasa · ilk satır) ÖNCE sorulur ve
# eksik her yol ADIYLA basılır. Çağrı TEK noktadadır (dağıtım bloğu, root kapısından ve `_islik_kur`dan SONRA):
# eski yol, kasa yolunun üç dalı (genel döngü · `--db` · `--cp`) ve bütün alt komutlar aynı kapıdan geçer.
# ALAN DA SORULUR (G3b Task 3, 2026-10-01; Task 2 incelemesi M1 — ölçüldü X5): dosya VAR ama `^<alan>=` satırı yoksa
# (ya da ikiyse) `yaz-env` yazımın ORTASINDA ölüyordu — referans ve önceki kopyalar YENİ değerde, alanı eksik kopya eski:
# aynı yarım rotasyon, dosya değil ALAN sınıfında. Kural `yaz-env`inkiyle AYNI fonksiyondur (yardımcının `alan-var …
# tek` kipi → `_env_satiri`, TAM 1 satır): kapıdan geçen her `env` hedefini yazım GERÇEKTEN yazabilir. Yardımcı
# `_islik_kur`un yazdığı dosyadır — kapı bu yüzden çalışma dizininden SONRA; çalışma dizini bir YAZIM değildir (0700
# geçici, çıkışta silinir — yedek, kasa, kopya değil). İleti iki sınıfı AYIRIR: dosya YOKSA `--tohumla-sohbet` (dosyayı
# kurar); alan eksik/çiftse tohumlama ÇARE DEĞİLDİR (var olan dosyaya dokunmaz) — elle düzeltme ya da operatör.
# VARLIK KAPSAMI = `_yaz_satir`ın hedefi YARATAMADIĞI türler (`env` · `url`). `dosya` satırının hedefini betik KENDİSİ
# kurar (mod/sahip açıkken): Faz-1C öncesi `--apisix-admin` (v447 R7) ve render hedefi yokken
# `--vault --uret` (v557 F2) o sözleşmeye dayanır. `dosya … koru` satırı (bugün tabloda YOK) yazım anındaki
# kendi kapısıyla durur (v447 K7c). `sql` dosya değildir; `api`nin disk karşılığı (motor deposu) YOKSA yedek ve geri
# alma ona dokunmaz. (BAĞ/İZİN kapsamı daha geniştir — aşağıda: bütün disk yolları.)
# `sudo test` DEĞİL, düz `[ -f ]`/`[ -L ]`: kapı root kapısının ARKASINDADIR (sudo no-op olurdu) ve eski `--db` yolunun
# sudo izi altın izle çivili (v538 C7) — varlık soruları o ize satır EKLEMEZ (yalnız `hedef-denetle` ekler, aşağıda).
# Kuru koşum ve `--esitle` bu kapıdan GEÇMEZ: kuru hiçbir şey yazmaz; eşitlemenin ölçüm geçişi eksik kopyayı
# ZATEN yazımdan (yedek dahil) önce "kopya YOK — eşitleme yarım kalırdı" ile durdurur ve o durdurma korunur.
# ÖLÇÜLEMEDİ ≠ ARIZA (G3b Task 4; Task 3 incelemesi M2): hedef VAR ama alanı SAYILAMIYORSA (okuma izni yok · UTF-8 dışı bayt
# · yardımcı düştü) hüküm `olcum_yok` (çıkış 2) ve yol + alan ADIYLA — eskiden UTF-8 dışı dosya python traceback'i + çıkış 1
# veriyordu, okunamayan dosya ise "alan TAM BİR satır değil … elle düzelt" diye (yanıltıcı) raporlanıyordu. Sayım iletisi
# YALNIZ gerçek sayım hatasında (ALAN YOK · ÇİFT SATIR) basılır. Kesin arıza (dosya YOK · sayım) da varsa hüküm `die`dır
# (çıkış 1 — bilinen arıza bilinmeyeni ezer) ve ölçülemeyenler aynı iletide sayılır.
# TOHUMLAMA ÖNERİSİ YOLA GÖREDİR (G3b Task 4): `--tohumla-sohbet` YALNIZ `$_SOHBET_KOKU/` altını ve YALNIZ YOK olan dosyayı
# kurar; başka bir eksik yol için o komutu önermek yanlış yola sokardı — satır bunu ADIYLA söyler.
# BAĞ / İZİN DE SORULUR (TSK-260, 2026-10-01; CWE-59): `py hedef-denetle` yazımın koşacağı AYNI gövdeyi (`_hedef_ac`) koşar —
# zincir bağ izlenmeden açılır, her bileşen bağ değil · grup/diğer yazamaz · sahibi root ya da hedefin sahibi (root iken);
# hedefin kendisi bağ ya da normal dosya değilse RED. Yazım anı ret TEK BAŞINA tablodaki ÖNCEKİ satırları yazıp o hedefte
# dururdu (yarım rotasyon, ALAN sınıfının bağ biçimi). Yol başına BİR kez; RED/ölçülemeyen yolun alanı sorulmaz.
# KAPSAM BÜTÜN DİSK YOLLARIDIR (TSK-261; TSK-260 incelemesi M3) — `env` · `url` · `dosya` · `api` (motor deposunun disk
# karşılığı, `_disk_yolu`). TSK-260'ta yalnız `env`ti ("url/dosya root dizinlerinde, yazım anı denetimi yeter"); ama eski `--db`
# yolunda tablo sırası `sql` (ALTER ROLE) → `url`dir ve url'nin yazım-anı RED'i ALTER'dan SONRA görülürdü: parola değişmiş,
# DSN eski → hindsight DB'ye bağlanamaz (geri alınamayan kanal). `api` yolu (`state/secrets.json`, dizin ubuntu 700) negatif
# kontrolün yedek + geri alma hedefidir ve `koru koru` ile sorulur (yazanı motorun kendisidir; sahibi ubuntu). `dosya` satırının
# hedefini betik KURAR (mod/sahip açıkken — v447 R7 / v557 F2): hedef YOKSA dizini varsa zincir yine sorulur (yoksa dizini
# `_dizin_hazirla` kurar), `koru` + YOK satırı yazım anındaki kendi kapısıyla durur (v447 K7c). Bağ `-L` ile AYRI sorulur:
# `-f`/`-e` bağı İZLER — sarkık bir bağ "hedef dosya YOK — --tohumla-sohbet" diye yanlış adlanıyordu (TSK-260 incelemesi M8);
# artık hedef-denetle onu ADIYLA ("SEMBOLİK BAĞ") reddeder. Bedel (bedel yasası): eski `--db` yolunun altın izine yazımdan
# ÖNCE bir `hedef-denetle` satırı girer (v538 C7 bilinçli güncellendi); ret metni ve çıkış kodu `env` hâliyle aynıdır.
# Çiviler: v604 A5 · A6 · A8 (alt komutlar × iki kip) · A9 · A10 · A11 · A16 (alan) · A16c (ölçülemedi) · C7 (`--kapi-bot`) ·
# v609 F (bağ/izin — rotasyon hiç başlamaz) · v611 E (url/dosya/api — yedek, ALTER ROLE ve istemden ÖNCE).
_hedef_on_denetim() {
  local alt="$1" _alt _sir tur yol alan _mod _sahip _onek eksik="" n=0 m=0 o=0 r=0 hal neden="" denetlenen="" atlanan=""
  while read -r _alt _sir tur yol alan _mod _sahip _onek; do
    [ "$_alt" = "$alt" ] || continue
    case "$tur" in
      env|url)
        if [ ! -f "$KOK$yol" ] && [ ! -L "$KOK$yol" ]; then
          case " $eksik " in *" $yol "*) continue ;; esac
          eksik="${eksik:+$eksik }$yol"
          n=$((n+1))
          continue
        fi ;;
      dosya)
        if [ ! -e "$KOK$yol" ] && [ ! -L "$KOK$yol" ]; then
          case "$_mod/$_sahip" in *koru*) continue ;; esac
          [ -e "$(dirname "$KOK$yol")" ] || [ -L "$(dirname "$KOK$yol")" ] || continue
        fi ;;
      api)
        yol="$(_disk_yolu api "$yol")"; _mod=koru; _sahip=koru
        [ -e "$KOK$yol" ] || [ -L "$KOK$yol" ] || continue ;;
      *) continue ;;
    esac
    case " $atlanan " in *" $yol "*) continue ;; esac
    case " $denetlenen " in
      *" $yol "*) ;;
      *) denetlenen="${denetlenen:+$denetlenen }$yol"
         # `||` ADLANDIRMADIR (aşağıdaki gibi): yardımcının düşüşü ÖLÇÜLEMEDİ satırına ve `olcum_yok`a gider.
         hal="$(py hedef-denetle "$KOK$yol" "$_mod" "$_sahip")" || hal="ÖLÇÜLEMEDİ (denetim yardımcısı düştü)"
         case "$hal" in
           TAMAM) ;;
           RED:*) echo "!! hedef REDDEDİLDİ: $yol — ${hal#RED: }" >&2
                  atlanan="${atlanan:+$atlanan }$yol"; r=$((r+1)); continue ;;
           *)     echo "!! hedef ÖLÇÜLEMEDİ: $yol — $hal" >&2
                  atlanan="${atlanan:+$atlanan }$yol"; o=$((o+1)); continue ;;
         esac ;;
    esac
    # ALAN yalnız `env` satırında sorulur (url/dosya/api'nin alanı yok — dosyanın TAMAMI değerdir).
    [ "$tur" = env ] || continue
    # `||` dalı bir YUTMA değil ADLANDIRMADIR: yardımcının düşüşü aşağıda ÖLÇÜLEMEDİ satırına ve `olcum_yok`a gider.
    hal="$(py alan-var "$KOK$yol" "$alan" tek)" || hal="ÖLÇÜLEMEDİ (yardımcı düştü)"
    case "$hal" in
      VAR) continue ;;
      OKUNAMADI*|ÖLÇÜLEMEDİ*)
        echo "!! alan ÖLÇÜLEMEDİ: $yol [$alan] — $hal (dosya VAR ama alan sayılamadı)" >&2
        o=$((o+1)); continue ;;
    esac
    echo "!! alan $hal: $yol [$alan]" >&2
    m=$((m+1))
  done < <(_kopyalar)
  [ -n "$eksik" ] || [ "$m" -gt 0 ] || [ "$o" -gt 0 ] || [ "$r" -gt 0 ] || return 0
  for yol in $eksik; do
    case "$yol" in
      "$_SOHBET_KOKU"/*) echo "!! hedef dosya YOK: $yol — kurar: sudo ./sir_rotasyon.sh --tohumla-sohbet" >&2 ;;
      *) echo "!! hedef dosya YOK: $yol — --tohumla-sohbet bu yolu KURMAZ (yalnız $_SOHBET_KOKU/ altı): dosyayı kuran adım" >&2 ;;
    esac
  done
  [ -z "$eksik" ] || neden="$n hedef dosya YOK (yukarıda) — sohbet .env'i ise önce: sudo ./sir_rotasyon.sh --tohumla-sohbet
     (YALNIZ YOK olan dosyayı kurar: dizini A0 site.yml'den, değeri referanslardan bekler; var olana dokunmaz)"
  [ "$m" = 0 ] || neden="${neden:+$neden;
     }$m hedefte alan TAM BİR satır değil (yukarıda) — --tohumla-sohbet dosyayı YALNIZ YOKSA yazar, var olan
     dosyanın eksik/çift alanını DÜZELTMEZ: elle düzelt (eksikse değersiz '<ALAN>=' satırı ekle — değeri rotasyon
     yazar; çiftse TEK satıra indir) ya da operatöre bırak"
  [ "$r" = 0 ] || neden="${neden:+$neden;
     }$r hedef REDDEDİLDİ (yukarıda — hedef sembolik bağ / normal dosya değil, ya da zincirde bağ · grup/diğer yazabilen
     dizin · sahibi ne root ne hedefin sahibi olan dizin): yazım bağı İZLEMEZ ve bu hedefi YAZAMAZDI. Değeri BASMADAN incele:
     sudo stat -c '%U:%G %a %F %n' <yol> ve üst dizinleri — dizin izinlerini A0 site.yml kurar"
  if [ -z "$eksik" ] && [ "$m" = 0 ] && [ "$r" = 0 ]; then
    olcum_yok "$(_bayrak "$alt"): $o hedefin alanı ÖLÇÜLEMEDİ (yukarıda — dosya okunamadı: izin ya da UTF-8 dışı bayt;
     ya da hedef denetim yardımcısı düştü).
     Alan sayılamadan yazım başlamaz (yazım alanı bulamayıp yarıda ölebilirdi). HİÇBİR ŞEY yazılmadı: yedek, değer üretimi, kasa ve kopya
     satırı yok. Dosyayı (değerini BASMADAN) incele: sudo stat <yol> · sudo file <yol>"
  fi
  [ "$o" = 0 ] || neden="$neden; ayrıca $o hedefin alanı ÖLÇÜLEMEDİ (yukarıda)"
  die "$(_bayrak "$alt"): $neden. HİÇBİR ŞEY yazılmadı: yedek, değer
     üretimi, kasa ve kopya satırı yok — rotasyon yarıda kalmadı, hiç başlamadı."
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
#
# ÜÇ PARÇA, İKİ ÇAĞIRAN (TSK-064 `--db --vault`, 2026-09-24): eski yol (`_sql_uygula`) üret → koş → sil
# sırasını tek nefeste yapar ve düşüşte `die` eder; kasa yolu (`vault_db_rotasyon`) ÜRETİMİ öne alır
# (operatörün parolası SQL alfabesine uymuyorsa kasaya HİÇBİR ŞEY yazılmadan durulur) ve KOŞUMUN
# düşüşünü kendisi karşılar (kasayı geri alır). Komut satırı TEK yerde (`_sql_kos`): iki kopya ALTER
# çağrısı sessizce ayrışırdı (tek-kaynak yasası). Eski yolun komut dizisi bayt bayt aynıdır (v538 Ç7).
_sql_kos() {
  local sql="$1"
  sudo -u postgres psql -v ON_ERROR_STOP=1 -q -f - < "$sql" >/dev/null
}

_sql_sil() {
  local rol="$1" sql="$2"
  sudo rm -f "$sql"
  sudo test ! -e "$sql" || die "SQL dosyası SİLİNEMEDİ: $sql"
  oldu "ALTER ROLE $rol uygulandı · SQL dosyası silindi (parola argv'ye girmedi)"
}

_sql_uygula() {
  local rol="$1" dgr="$2" sql="$ISLIK/rol.sql"
  py sql-uret "$sql" "$rol" "$dgr"
  _sql_kos "$sql" || die "ALTER ROLE başarısız — parola DEĞİŞMEDİ (SQL dosyası siliniyor)"
  _sql_sil "$rol" "$sql"
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
  # KASA AKIŞI (`YAZIM_AKISI=kasa`, TSK-064 takip (5)): bu kopya restart ve kanıttan ÖNCE yazılır,
  # yani aşağıdaki eski yol metninin "Rotasyon KANITLANDI" hükmü burada henüz DOĞRU DEĞİL. Aynı
  # `die` (çıkış 1), aynı an; yalnız metin bağlama göre. Eski yolun metni AYNEN kalır.
  [ "$kod" = "200" ] || [ "$YAZIM_AKISI" != "kasa" ] || die "motor API yazımı başarısız (HTTP $kod): $uc ($ad)
     KASA AKIŞI: kasaya yazım ve Agent render'ı ÖLÇÜLDÜ (render hedefi kasadaki yeni değerde) —
     ama tüketici YENİDEN BAŞLATMA ve uçtan uca kanıt HENÜZ KOŞMADI: koşum burada DURDU.
     YAZILAMAYAN motorun kendi deposundaki kopya (\`secrets._fetch\`in ÜÇÜNCÜ basamağı).
     Elle eşitle (pano → sır girişi, ya da $uc), sonra $(_sir_birimleri "$ad") yeniden başlat ve
     kanıtı ölç — bu noktada rotasyon DOĞRULANMADI."
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
#: KOŞULLU BİRİM (G3b, 2026-09-30): `_KOSULLU_BIRIMLER`deki birim YALNIZ ETKİNSE kümede kalır. Süzgeç restart'tan
#: ÖNCE koşar ve `birimler`i yeniden kurar: aşağıdaki restart, credential denetimi ve hazırlık beklemesi AYNI
#: süzülmüş kümeyi görür — atlanan birim için `/run/credentials` sorulmaz (yoksa açılmamış birim `olcum_yok`
#: çıkış 2 verirdi) ve sağlık ucu yoklanmaz. Karar `is-active --quiet`in ÇIKIŞ KODUdur; durum ADI ayrı bir
#: okumayla satıra yazılır (`failed` ile `inactive` operatör için aynı hâl değildir). Koşulsuz birim için
#: `is-active` HİÇ sorulmaz. Çiviler: v604 A2-A4 (fonksiyon DOĞRUDAN, sürücüyle), A14.
_yeniden_baslat() {
  local alt="$1"; shift
  local birimler b hepsi durum
  if [ "$#" -gt 0 ]; then hepsi="$*"; else hepsi="$(_birimler "$alt")"; fi
  birimler=""
  for b in $hepsi; do
    if _kosullu_birim_mi "$b" && ! sudo systemctl is-active --quiet "$b"; then
      # sessiz-yutma: `is-active` etkin OLMAYAN birimde 3 döner ve bu BEKLENEN hâldir — okunan şey çıkış
      # kodu değil DURUM ADIDIR; ad okunamazsa uydurulmaz, satır "ÖLÇÜLEMEDİ" der.
      durum="$(sudo systemctl is-active "$b" || true)"
      echo "  · ATLANDI (etkin değil: ${durum:-ÖLÇÜLEMEDİ}): $b — yeniden BAŞLATILMADI (yalnız etkinse:"
      echo "    _KOSULLU_BIRIMLER); credential ve hazırlık denetimi bu birim için İSTENMEDİ"
      continue
    fi
    birimler="${birimler:+$birimler }$b"
  done
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
# UCU OLMAYAN BİRİM HAZIR SAYILMAZ, BEKLENMEZ ve satır bunu SÖYLER. Sessizce "hazır" saymak,
# ölçülmemiş bir şeyi ölçülmüş göstermek olurdu. `hindsight-cp.service` 2026-09-08'de bu sınıftaydı
# ("sağlık ucu ölçülmedi"); 2026-09-26'da (TSK-226b) ucu KAYNAKTAN ölçüldü ve tabloya girdi (aşağıda).
# Dal bir GÜVENLİK AĞI olarak kalır: tabloya ucsuz giren yeni bir birim sessizce "hazır" sayılmaz.
# `<uç> <kabul ölçütü> <200 GELMEDEN hazır sayılınca basılacak açıklama>` — üçü de birim başına ve
# TEK yerde. Kabul ölçütü uçtan ayrı bir tabloda yaşasaydı ikisi sessizce ayrışır, betik bir ucu
# yanlış ölçütle yoklardı (tek-kaynak yasası).
_hazir_uc() {
  case "$1" in
    meridian.service)      echo "$API/healthz http nabız bayat, API ayakta" ;;
    hindsight-api.service) echo "$HINDSIGHT/health 200 -" ;;
    apisix.service)        echo "$KAPI_KOK/healthz http meridian'a proxy, kapı ayakta" ;;
    #: CP (TSK-226b): `/api/health` imajın middleware'inde KİMLİKSİZDİR ve açıldıktan sonra HER ZAMAN
    #: 200 döner (gövdede dataplane durumu) — KAYNAKTAN ölçüldü (v0.9.2), A1'de ÖLÇÜLMEDİ. A1'de ölçülen
    #: şey 127.0.0.1:9999'un HTTP cevap verdiğidir (2026-09-01), bu yüzden ölçüt `http`: ölçülmemiş bir
    #: 200 şartı, cevap veren bir CP'yi "ölü" sayabilirdi (2026-09-08 meridian dersi). Kesin hüküm
    #: hazırlıktan SONRA giriş ucunun kanıtıdır (`_cp_kanit`: yeni 200 · eski 401).
    hindsight-cp.service)  echo "$CP_KOK/api/health http CP sunucusu cevap veriyor" ;;
    #: Bot ağ geçidi (G3b): Hermes `GET /health` kimliksiz, `{"status":"ok"}` → 200 hazırlıktır (Rol-1 kaynak
    #: ölçümü, 2026-09-30; bkz. `BOTLAR_KOK`). Telegram dinleyicisinin ucu YOK → güvenlik ağı dalı.
    meridian-botlar.service) echo "$BOTLAR_KOK/health 200 -" ;;
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
    _saat_oku; bas="$SAAT_MS"     # MONOTONİK (bkz. `_saat_oku`): askı bekleme sayılmaz
    while :; do
      kod="$(_kod "-" "$uc" "-" "-")"
      if _hazir_mi "$kabul" "$kod"; then break; fi
      _gecen_s "$bas"; gecen="$GECEN_S"
      if [ "$gecen" -ge "$tavan" ]; then
        olcum_yok "hazırlık bekleme aşıldı: $b $uc → HTTP $kod
     ($tavan s içinde $(_kabul_metni "$kabul") gelmedi.) Birim AYAKTA DEĞİL ya da yüzeye
     ulaşılamıyor; buradan sonra ölçmek 'ulaşılamadı'yı 'anahtar reddedildi' saymak olurdu."
      fi
      sleep "$HAZIR_BEKLE_ARALIK_S"
    done
    _gecen_s "$bas"; gecen="$GECEN_S"
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

# DEĞER İSTEKTE NEREDE TAŞINIR (TSK-226b): varsayılan bir BAŞLIKTA (`$baslik`, önek `$b_onek`) — kapı,
# hafıza, pano, yönetim yüzeyi böyle. CP'nin giriş ucu anahtarı JSON GÖVDEDE ister (`{"key": …}`), yani
# beşinci argüman bir gövde ALAN ADIYSA değer `py json-govde` ile 0600 bir gövde dosyasına yazılır ve
# `_kod` onu `data-binary` olarak verir — başlık yok, argv'ye yine GİRMEZ. `-` = eski davranış (birebir).
_farksal_kod() {
  local dgr="$1" url="$2" baslik="$3" b_onek="$4" alan="$5"
  if [ "$alan" = "-" ]; then _kod "$dgr" "$url" "$baslik" "$b_onek"; return; fi
  py json-govde "$ISLIK/farksal.json" "$alan" "$dgr"
  _kod "-" "$url" "-" "-" "$ISLIK/farksal.json"
}

# İKİ HÜKÜM BİRDEN. `yeni` 200 VE `eski` 401 olmalı. Yalnız biri ölçülürse kanıt anahtara bağlı
# olduğunu GÖSTERMEZ: kilit kapalıysa ikisi de 200 döner ve "rotasyon başarılı" bir tiyatrodur.
# `[govde alanı]` (9.) — verilirse değer başlık yerine JSON gövdede gider (bkz. `_farksal_kod`).
_farksal() {
  local etiket="$1" yeni="$2" eski="$3" url="$4" baslik="$5" b_onek="$6"
  local bekle_yeni="$7" bekle_eski="$8" govde_alani="${9:--}" k_yeni k_eski
  k_yeni="$(_farksal_kod "$yeni" "$url" "$baslik" "$b_onek" "$govde_alani")"
  k_eski="$(_farksal_kod "$eski" "$url" "$baslik" "$b_onek" "$govde_alani")"
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

#: KURU RAPORUN KOŞULLU BİRİM NOTU (G3b, 2026-09-30) — bedel yasası: gerçek koşumda ATLANACAK birim kuru
#: raporda ÖNCEDEN görünür. Kural ve ölçüm `_yeniden_baslat`ınkiyle AYNIDIR (`_kosullu_birim_mi` +
#: `is-active`): şu anki durum ve sonucu ("→ ATLANACAK" / "→ yeniden başlar") birim başına basılır. Kümede
#: koşullu birim YOKSA hiçbir şey basılmaz (ilgisiz başlık gürültüdür). Başlık satırı "    · " ile
#: BAŞLAMAZ: kuru raporun "sır → tüketici birimler" bloğunu ayrıştıran çivi (v447 N10) o önekle sürdürür.
#: `_kosullu_kuru_notu <birim…>` — çağıran kümeyi verir (eski yol `_birimler`, kasa yolu `_sirala`).
_kosullu_kuru_notu() {
  local b var=0 durum
  for b in "$@"; do
    if _kosullu_birim_mi "$b"; then var=1; fi
  done
  [ "$var" = 1 ] || return 0
  echo "  koşullu birimler — YALNIZ ETKİNSE yeniden başlar (değilse ATLANDI satırı; credential ve hazırlık"
  echo "  denetimi o birim için istenmez):"
  for b in "$@"; do
    _kosullu_birim_mi "$b" || continue
    if sudo systemctl is-active --quiet "$b"; then
      echo "    · $b — şu an: active → yeniden başlar"
    else
      # sessiz-yutma: `is-active` etkin OLMAYAN birimde 3 döner (beklenen); hüküm DURUM ADIDIR ve okunamazsa
      # satır "ÖLÇÜLEMEDİ" der — kuru rapor bir durum UYDURMAZ.
      durum="$(sudo systemctl is-active "$b" || true)"
      echo "    · $b — şu an: ${durum:-ÖLÇÜLEMEDİ} → ATLANACAK"
    fi
  done
  return 0
}

_kuru_rapor() {
  local alt="$1" _alt sir tur yol alan _m _s onek satir uc kabul onceki="" carpan tavan
  local _ONESHOT_SATIR
  echo "=== KURU KOŞUM: $(_bayrak "$alt") (HİÇBİR ŞEY YAZILMADI) ==="
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
  # ONESHOT TÜKETİCİLER — AYRI BAŞLIK satırıyla basılır, "sır → tüketici birimler" bloğuna
  # KARIŞTIRILMAZ: N10 çivisi o bloğu "    · " önekiyle SÜRDÜRÜR sayar (satırı "sir → birimler"
  # diye ayrıştırır) ve önekli-ama-başlıksız bir oneshot satırı o ayrıştırıcıyı YANLIŞ BÖLER.
  # Bölüm YALNIZ bu alt komutta oneshot tüketici VARSA basılır (bedel yasası — ilgisiz bir
  # başlığı her alt komutta göstermek kuru raporu gürültüyle doldurmaktır).
  _ONESHOT_SATIR="$(_oneshot_yazdir "$alt")"
  if [ -n "$_ONESHOT_SATIR" ]; then
    echo "  oneshot tüketiciler (restart kümesi DIŞI — rotasyon bunları yeniden başlatmaz):"
    echo "$_ONESHOT_SATIR"
  fi
  # shellcheck disable=SC2046
  _kosullu_kuru_notu $(_birimler "$alt")
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
      echo "    sudo env HAZIR_TAVAN_S_hindsight_api=$(_hazir_tavan hindsight-api.service) ./deploy/oracle-a1/sir_rotasyon.sh $(_bayrak "$alt")" ;;
  esac
  echo "  yedek dizini: $KOK/root/sir-yedek-<UTC ts>-$alt"
}

kapi() {
  echo "=== ROTASYON: KAPI_APIKEY (kapı tüketici anahtarı) ==="
  # AGENT RENDER HEDEFİ UYARISI (TSK-064 takip (2)): kuru kapısının ÜSTÜNDE, yazımdan ÖNCE — `db()`
  # şerhinin gerekçesi. Sır kasaya BAĞLIYSA uyarı doğru yolu (`--vault`) söyler. Kapı DEĞİL.
  _agent_hedefi_uyarisi kapi
  [ "$KURU" = 0 ] || { _kuru_rapor kapi; return 0; }
  _yedek_al kapi
  py cikar dosya "$YEDEK/etc/meridian/kapi_apikey" - - "$ISLIK/eski"
  _uret b64
  _yaz kapi
  _yeniden_baslat kapi
  _kapi_kanit "$ISLIK/yeni" "$ISLIK/eski"
  echo ">> geri alma: sudo $0 --geri-al $YEDEK (kapi_apikey + .env-apisix) ve $(_recete_birimleri $(_birimler kapi)) yeniden başlat"
}

#: KAPI KANITI — eski yol (`kapi`) ve kasa yolu (`vault_rotasyon` → `_kasa_kaniti`, G3b Task 4) AYNI ölçümü koşar; gövde
#: TEK yerde (iki kopya sessizce ayrışırdı). `_kapi_kanit <yeni değer dosyası> <eski değer dosyası>`: kapı `/models` iki
#: hüküm (yeni 200 · eski 401/403) + motorun KENDİ sürecinden kapıya konuşabildiği (`/api/secrets/test/nous` ok:true).
_kapi_kanit() {
  _farksal "kapı /models" "$1" "$2" "$KAPI_UC/models" "apikey" "-" "200" "401 403"
  local _kapi_hal; _kapi_hal="$(_nous_hali)"
  [ "$_kapi_hal" = "OK" ] || olcum_yok "motor /api/secrets/test/nous → $_kapi_hal (OK bekleniyordu)
     — motor kapıya konuşamıyor ya da yüzeye ULAŞILAMADI; ikisi aynı şey DEĞİLDİR ve hüküm ikisinde de
     'geçti' olamaz."
  oldu "motor içi kanıt: /api/secrets/test/nous ok:true"
}

#: Kanıt planı — kasa yolunun kuru raporu gerçek koşumun ölçeceği yüzeyi söyler (`_kapi_bot_kanit_plani` emsali).
_kapi_kanit_plani() {
  echo "  kanıt: GET $KAPI_UC/models (apikey) — yeni → 200 · eski → 401/403; motor /api/secrets/test/nous ok:true"
}

# KAPININ YÖNETİM ANAHTARI — `--kapi` İLE KARIŞTIRILMAZ. `KAPI_APIKEY` kapının TÜKETİCİ anahtarıdır
# (`motor_meridian` key-auth); `APISIX_ADMIN_KEY` Admin API'nin (9180, loopback) YÖNETİM
# anahtarıdır. İkisini tek alt komuta toplamak, iki ayrı yüzeyin kanıtını tek pencereye sıkıştırıp
# hangisinin döndüğünü ölçülemez kılardı — ve her koşum TEK sır döndürür (bkz. `--kopyalar` şerhi).
#
# NEGATİF KONTROL YOK, ÇÜNKÜ GEREKMİYOR: kanıt yüzeyi anahtarı İSTEKTE alır (`X-API-KEY`), yani
# "eski değerle 401" DOĞRUDAN ölçülebilir (`_farksal`). `--openrouter`de negatif kontrol vardı
# çünkü orada yüzey isteğin anahtarını UPSTREAM'e taşımıyordu ve fark ancak yazımla üretilebiliyordu.
# Bir yüzey doğrudan ölçülebiliyorken bilerek bozuk değer yazmak, karşılıksız iki restart demektir.
apisix_admin() {
  echo "=== ROTASYON: APISIX_ADMIN_KEY (kapı Admin API yönetim anahtarı) ==="
  _agent_hedefi_uyarisi apisix-admin      # TSK-064 takip (2) — gerekçe `kapi()` şerhinde
  [ "$KURU" = 0 ] || { _kuru_rapor apisix-admin; return 0; }
  _yedek_al apisix-admin
  # ESKİ DEĞER YEDEKTEKİ `.env-apisix`TEN OKUNUR, credential kaynağından DEĞİL: Faz-1C elle
  # uygulanmadan önce o kaynak YOKTUR ve `py cikar` okunamayan bir dosyada durur — rotasyon, geçiş
  # penceresinin HANGİ ucunda olursak olalım koşabilmeli (aksi halde iki iş birbirinin rehinesi).
  py cikar env "$YEDEK/opt/apisix/.env-apisix" APISIX_ADMIN_KEY - "$ISLIK/eski"
  _uret b64
  _yaz apisix-admin
  _yeniden_baslat apisix-admin
  _farksal "kapı admin /routes" "$ISLIK/yeni" "$ISLIK/eski" \
           "$ADMIN_KOK/routes" "X-API-KEY" "-" "200" "401 403"
  _birimsiz_tuketici_beyani apisix-admin
  echo ">> geri alma: sudo $0 --geri-al $YEDEK (iki kopya) ve $(_recete_birimleri $(_birimler apisix-admin)) yeniden başlat"
}

#: BİRİM OLMAYAN TÜKETİCİ BEYANI — restart kümesine GİRMEYEN okuyucu ADIYLA (bedel yasası: "neden
#: yeniden başlatılmadı" sorusu çıktıda cevaplı durur). TEK yerde: eski yol (`apisix_admin`) ve kasa
#: yolu (`vault_rotasyon` + kuru rapor, TSK-064 2026-09-17) aynı cümleyi basar — iki kopya metin
#: sessizce ayrışırdı.
_birimsiz_tuketici_beyani() {
  case "$1" in
    apisix-admin)
      echo "  · ops/apisix_uygula.py yeniden başlatılmaz: birim değil, operatörün koştuğu araçtır —"
      echo "    yeni değeri bir sonraki koşumda kaynaktan okur (kanalı stderr'e bildirir)." ;;
  esac
}

tenant() {
  echo "=== ROTASYON: HINDSIGHT_API_TENANT_API_KEY ==="
  _agent_hedefi_uyarisi tenant            # TSK-064 takip (2) — gerekçe `kapi()` şerhinde
  [ "$KURU" = 0 ] || { _kuru_rapor tenant; return 0; }
  _yedek_al tenant
  py cikar dosya "$YEDEK/etc/hindsight/creds/HINDSIGHT_API_TENANT_API_KEY" - - "$ISLIK/eski"
  _uret hex
  _yaz tenant
  _yeniden_baslat tenant
  _farksal "hindsight /banks" "$ISLIK/yeni" "$ISLIK/eski" \
           "$HINDSIGHT/v1/default/banks" "Authorization" "Bearer" "200" "401 403"
  _envanter_esitlik tenant
  # Kopya SAYISI yazılmaz, tablodan okunur: 2026-09-29'a kadar "üç kopya"ydı (`.key` + `.env-cp` emekli).
  echo ">> geri alma: sudo $0 --geri-al $YEDEK ($(_kopyalar | awk '$1=="tenant"' | wc -l | tr -d ' ') kopya) ve $(_recete_birimleri $(_birimler tenant)) yeniden başlat"
}

# CP ERİŞİM ANAHTARI — ESKİ YOL (TSK-226b, 2026-09-26). `tenant()` emsali, adım adım: yedek → ESKİ değer
# → üret (`hex`, `--tenant` ile aynı sınıf) → tablodaki kopyalar (2026-09-29'a dek iki, bugün TEK: kanonik
# kopya) → restart → kanıt → envanter eşitliği.
# Sır kasaya BAĞLIDIR ve uyarı yazımdan ÖNCE `--cp --vault`u gösterir: konteyner değeri YALNIZ yan dosyadan
# (`.env-cp.vault`, drop-in 51 ile TEK ve ZORUNLU `EnvironmentFile=`) alır ve bu yolun yazdığı kanonik kopyayı
# OKUMAZ (2026-09-29'a dek yazdığı `.env-cp` de yan dosyanın gölgesinde kalıyordu) — kanıt o hâlde "YENİ
# değerle HTTP 401" der (çıkış 2): yarım rotasyon SESSİZ olamaz (v556 D7).
# ESKİ DEĞER 2026-09-29'a kadar `.env-cp` YEDEĞİNDEN okunuyordu (o dosya birimin zorunlu `EnvironmentFile=`ıydı ve
# her dünyada vardı). İki-kanal kapanışından beri CP'nin ZORUNLU tek kaynağı kasa yan dosyasıdır — yani kasa
# kurulu değilse CP hiç AÇILMAZ ve kanonik kopya CP'nin açılabildiği HER dünyada vardır. Eski değer bu yüzden
# tablonun REFERANS satırının (kanonik kopya) YEDEĞİNDEN okunur; yol tablodan türer (ikinci liste yok). Referans
# yoksa ESKİ değer uydurulmaz: yazımdan ÖNCE durulur (yedek alındı, hiçbir kopya yazılmadı).
cp_erisim() {
  local ref_yol
  echo "=== ROTASYON: HINDSIGHT_CP_ACCESS_KEY (Hindsight kontrol paneli giriş anahtarı) ==="
  _agent_hedefi_uyarisi cp                # TSK-064 takip (2) — gerekçe `kapi()` şerhinde
  [ "$KURU" = 0 ] || { _kuru_rapor cp; _cp_kanit_plani; return 0; }
  _yedek_al cp
  ref_yol="$(_kopyalar | awk '$1=="cp" && !y {print $4; y=1}')"   # erken `exit` YOK: TABLO BORUSU şerhi (`_sohbet_satirlari` üstü)
  sudo test -s "$YEDEK$ref_yol" \
    || die "--cp ESKİ değer okunamadı: referans kopya ($ref_yol) YOK/boş — kasa kurulu değilse CP zaten AÇILMAZ
     (tek kanal: .env-cp.vault). Hiçbir kopya YAZILMADI. Doğru yol: sudo $0 --cp --vault"
  py cikar dosya "$YEDEK$ref_yol" - - "$ISLIK/eski"
  _uret hex
  _yaz cp
  _yeniden_baslat cp
  _cp_kanit "$ISLIK/yeni" "$ISLIK/eski"
  _envanter_esitlik cp
  echo ">> geri alma: sudo $0 --geri-al $YEDEK ($(_kopyalar | awk '$1=="cp"' | wc -l | tr -d ' ') kopya) ve $(_recete_birimleri $(_birimler cp)) yeniden başlat"
}

#: Kanıt ucunun planı — eski yolun kuru raporu ve kasa yolunun kuru planı AYNI uçtan söz eder.
_cp_kanit_plani() {
  echo "  kanıt: POST $CP_KOK/api/auth/login gövde {\"key\": …} — yeni → 200 · eski → 401/403 (503 = konteynerde anahtar YOK; hindsight-control-plane 0.9.2 kaynağı)"
}

# CP KANITI — kontrol panelinin KENDİ giriş ucu (TSK-226b). Kaynak ölçümü (v0.9.2 `api/auth/login`):
# gövde `{"key": …}` `HINDSIGHT_CP_ACCESS_KEY` ile sabit-zamanlı kıyaslanır → eşitse 200, değilse 401;
# anahtar TANIMSIZSA 503 (değersiz `-e AD`: değişken yan dosyada yoksa konteynere HİÇ girmez); gövde
# JSON değilse 400. Anahtar İSTEKTE geldiği için "eski değerle 401" DOĞRUDAN ölçülür — negatif kontrol
# (bilerek bozuk yazım) GEREKMEZ (`apisix_admin` emsali). Değer başlıkta DEĞİL gövdededir; gövde 0600
# dosyadan `data-binary` ile gider, argv'ye GİRMEZ (`_farksal_kod`). Başarılı girişin oturum çerezi
# hiçbir yere yazılmaz (yalnız HTTP kodu ve gövde dosyası okunur).
_cp_kanit() {
  _farksal "CP /api/auth/login" "$1" "$2" "$CP_KOK/api/auth/login" "-" "-" "200" "401 403" "key"
}

# BOT AĞ GEÇİDİNİN DİNLEYİCİ ANAHTARI — ESKİ YOL `--api-sunucu` (G3b Task 2, 2026-10-01). `tenant()` emsali, adım adım:
# referans kapısı → yedek → ESKİ değer → üret (`hex`) → tablodaki kopyalar → restart (yalnız etkin koşullu birim) →
# kanıt → envanter eşitliği.
# DÖRT KOPYA, TEK SIR (Rol-1 G3b-R1). Ölçüm (Rol-1, A1 Hermes v0.19 kaynağı 2026-09-30):
# `gateway/platforms/api_server.py` `_expected_api_key` `/p/<profil>/…` isteğinin anahtarını O PROFİLİN kapsamından
# (`agent/secret_scope.py` `get_secret`) alır — çoklu kipte kapsam yetkilidir, `os.environ`a düşmez; anahtar yoksa ya da
# <16 karakterse 401 (fail-closed). Kök `.env` dinleyicinin açılışıdır (`connect()` anahtarsız açmaz); her sohbet
# profilinin `.env`i o profilin istekleridir; Telegram dinleyicisi (`meridian/bot_kanal.py::HermesTasiyici`) AYNI değeri
# credential'dan okur (55 drop-in, kaynağı referans satırı). Hepsi AYNI pencerede yazılır — biri unutulursa o bot 401.
# ESKİ DEĞER referans kopyanın (Agent render hedefi) YEDEĞİNDEN okunur. Referans YOKSA (ilk değer henüz kasada değil —
# Rol-1 G3b-R6: ilk değer RUNBOOK borusuyla konur, araçta "ilk kurulum" istisnası YOK) ESKİ değer uydurulmaz: kapı
# yedekten ÖNCE durur, HİÇBİR ŞEY yazılmaz. Sır kasaya BAĞLIDIR; uyarı yazımdan ÖNCE `--api-sunucu --vault`u gösterir.
api_sunucu() {
  local ref_yol
  echo "=== ROTASYON: API_SERVER_KEY (bot ağ geçidi dinleyici anahtarı — kök + sohbet profilleri + Telegram credential'ı) ==="
  _agent_hedefi_uyarisi api-sunucu        # TSK-064 takip (2) — gerekçe `kapi()` şerhinde
  [ "$KURU" = 0 ] || { _kuru_rapor api-sunucu; _api_sunucu_kanit_plani; return 0; }
  ref_yol="$(_kopyalar | awk '$1=="api-sunucu" && !y {print $4; y=1}')"   # erken `exit` YOK: TABLO BORUSU şerhi (`_sohbet_satirlari` üstü)
  sudo test -s "$KOK$ref_yol" \
    || die "--api-sunucu ESKİ değer okunamaz: referans kopya ($ref_yol) YOK/boş — İLK değer kasaya RUNBOOK borusuyla
     konur ve Vault Agent render eder (Rol-1 G3b-R6). HİÇBİR ŞEY yazılmadı (yedek dahil)."
  _yedek_al api-sunucu
  py cikar dosya "$YEDEK$ref_yol" - - "$ISLIK/eski"
  _uret hex
  _yaz api-sunucu
  _yeniden_baslat api-sunucu
  _api_sunucu_kanit "$ISLIK/yeni" "$ISLIK/eski"
  _envanter_esitlik api-sunucu
  echo ">> geri alma: sudo $0 --geri-al $YEDEK ($(_kopyalar | awk '$1=="api-sunucu"' | wc -l | tr -d ' ') kopya) ve $(_recete_birimleri $(_birimler api-sunucu)) yeniden başlat"
}

#: Kanıt ucunun planı — kuru rapor gerçek koşumun ölçeceği yüzeyi söyler (bedel yasası: "ölçülemedi" de önceden görünür).
_api_sunucu_kanit_plani() {
  echo "  kanıt: botlar ETKİNSE GET $BOTLAR_KOK/health/detailed (Bearer) — yeni → 200 · eski → 401/403; etkin DEĞİLSE"
  echo "         ölçülemez ve ADIYLA basılır (çıkış 0 — yeni değer birimin ilk açılışında okunur)"
}

# API SUNUCU KANITI — Hermes ağ geçidinin `GET /health/detailed` ucu Bearer İSTER (`GET /health` kimliksizdir ve yalnız
# hazırlıktır — Rol-1 kaynak ölçümü 2026-09-30). Anahtar İSTEKTE geldiği için "eski değerle 401" DOĞRUDAN ölçülür
# (`apisix_admin` emsali, negatif kontrol gerekmez); değer `curl -K` 0600 yapılandırmasından gider, argv'ye GİRMEZ (`_kod`).
# Botlar ETKİN DEĞİLSE ölçülecek yüzey yoktur: satır DURUM ADIYLA "ölçülemedi" der ve çıkış 0'dır — birim G3c'ye dek etkin
# değil ve yeni değeri İLK açılışında okur (kopyalar yazıldı, `_envanter_esitlik` eşitliği ayrıca ölçer). Telegram'ın kanıt
# ucu YOK: credential doluluğu (etkinse) `_yeniden_baslat` içinde ölçülür.
_api_sunucu_kanit() {
  local durum
  if sudo systemctl is-active --quiet meridian-botlar.service; then
    _farksal "botlar /health/detailed" "$1" "$2" "$BOTLAR_KOK/health/detailed" "Authorization" "Bearer" "200" "401 403"
    return 0
  fi
  # sessiz-yutma: `is-active` etkin OLMAYAN birimde 3 döner (beklenen); okunan şey DURUM ADIDIR ve okunamazsa satır
  # "ÖLÇÜLEMEDİ" der — kanıt satırı bir durum UYDURMAZ.
  durum="$(sudo systemctl is-active meridian-botlar.service || true)"
  echo "  KANIT: ölçülemedi — meridian-botlar.service etkin değil (${durum:-ÖLÇÜLEMEDİ}); kopyalar YAZILDI, yeni değer"
  echo "         birimin ilk açılışında okunur (değer-doğruluğu None)"
}

# BİR BOTUN KAPI TÜKETİCİ ANAHTARI — ESKİ YOL `--kapi-bot <ad>` (G3b Task 3, 2026-10-01). `kapi()` emsali, adım adım:
# referans kapısı → yedek → ESKİ değer → üret (`b64`) → tablodaki DÖRT kopya → restart (kapı; bot ağ geçidi yalnız
# ETKİNSE) → kanıt (kapı `/models`) → envanter eşitliği.
# DÖRT KOPYA BİRLİKTE (operatör K-G3b-1, 2026-09-30): kapının key-auth tüketicisi `bot_<ad>` (`.env-apisix`
# `BOT_KEY_<AD>`), rapor profili ve sohbet profili AYNI değeri taşımak ZORUNDADIR — biri eski kalırsa o yüzey kapıdan 401
# alır. REFERANS Agent render hedefidir (Rol-1 G3b-R3; emsal `--cp`/`--api-sunucu`): ESKİ değer onun YEDEĞİNDEN okunur ve
# referans yoksa uydurulmaz — kapı yedekten ÖNCE durur, HİÇBİR ŞEY yazılmaz. İÇ ALT AD `kapi-bot-<ad>` (G3b-R2): tablo
# güdümlü makine (`_birimler` · `_alt_sirlari` · `_yedek_al` · `_kuru_rapor` · `_envanter_esitlik`) süzgeçsiz doğrudur;
# gövde bot sayısıyla BÜYÜMEZ (tek fonksiyon, ad argümanla — operatör 2026-09-30 "bot sayısından bağımsız"). Ad, buraya
# gelmeden ayrıştırmada `_sohbet_botu_mu` ile doğrulanmıştır.
# NEGATİF KONTROL YOK, GEREKMİYOR: kapı anahtarı İSTEKTE alır (`apikey` başlığı) → "eski değerle 401" DOĞRUDAN ölçülür
# (`kapi()`/`apisix_admin()` emsali). Sır kasaya BAĞLIDIR; uyarı yazımdan ÖNCE `--kapi-bot <ad> --vault`ı gösterir (eski
# yolun `/etc/meridian/bot_key_<ad>` yazımı ve kapının yan dosyası `.env-apisix.vault` Agent'ındır — kasadaki ESKİ değerle
# ezilebilir; doğru yol kasa yoludur).
kapi_bot() {
  local bot="$1" alt="kapi-bot-$1" sir ref_yol
  sir="$(_alt_sirlari "$alt")"
  [ -n "$sir" ] || die "--kapi-bot $bot: kopya tablosunda satır YOK (iç alt ad $alt) — HİÇBİR ŞEY yazılmadı"
  echo "=== ROTASYON: $sir (kapı tüketici anahtarı bot_$bot — kapı + rapor profili + sohbet profili) ==="
  _agent_hedefi_uyarisi "$alt"            # TSK-064 takip (2) — gerekçe `kapi()` şerhinde
  [ "$KURU" = 0 ] || { _kuru_rapor "$alt"; _kapi_bot_kanit_plani "$bot"; return 0; }
  ref_yol="$(_kopyalar | awk -v a="$alt" '$1==a && !y {print $4; y=1}')"   # erken `exit` YOK: TABLO BORUSU şerhi
  sudo test -s "$KOK$ref_yol" \
    || die "--kapi-bot $bot ESKİ değer okunamaz: referans kopya ($ref_yol) YOK/boş — Agent render hedefidir (kasa
     secret/meridian/bot_key_$bot); önce vault-agent ve kasa. HİÇBİR ŞEY yazılmadı (yedek dahil)."
  _yedek_al "$alt"
  py cikar dosya "$YEDEK$ref_yol" - - "$ISLIK/eski"
  _uret b64
  _yaz "$alt"
  _yeniden_baslat "$alt"
  _kapi_bot_kanit "$bot" "$ISLIK/yeni" "$ISLIK/eski"
  _envanter_esitlik "$alt"
  echo ">> geri alma: sudo $0 --geri-al $YEDEK ($(_kopyalar | awk -v a="$alt" '$1==a' | wc -l | tr -d ' ') kopya) ve $(_recete_birimleri $(_birimler "$alt")) yeniden başlat"
}

#: BOT KAPI KANITI — eski yol (`kapi_bot`) ve kasa yolu (`_kasa_kaniti`, G3b Task 4) AYNI ölçüm; gövde TEK yerde.
#: `_kapi_bot_kanit <ad> <yeni değer dosyası> <eski değer dosyası>`: kapı `/models` iki hüküm + bot ağ geçidi notu.
_kapi_bot_kanit() {
  _farksal "kapı /models (bot_$1)" "$2" "$3" "$KAPI_UC/models" "apikey" "-" "200" "401 403"
  _kapi_bot_botlar_notu
}

#: Kanıt planı — kuru rapor gerçek koşumun ölçeceği yüzeyi söyler (bedel yasası; `_api_sunucu_kanit_plani` emsali).
_kapi_bot_kanit_plani() {
  echo "  kanıt: GET $KAPI_UC/models (apikey, tüketici bot_$1) — yeni → 200 · eski → 401/403; bot ağ geçidi ETKİNSE yeniden"
  echo "         başlar ve /health hazırlığı beklenir, DEĞİLSE sohbet kopyası yazılır ve ilk açılışta okunur"
}

#: BOT AĞ GEÇİDİ NOTU — kapı kanıtından SONRA. Ağ geçidi ETKİNSE yeniden başlatıldı ve `/health` hazırlığı `_yeniden_baslat`
#: içinde ÖLÇÜLDÜ (kimliksiz uç — anahtarın kendisini ölçmez); sohbet kopyasının değer-doğruluğu dosya EŞİTLİĞİDİR
#: (`_envanter_esitlik`, hemen ardından). Etkin DEĞİLSE durum ADIYLA söylenir — sessiz atlama yok (bedel yasası).
_kapi_bot_botlar_notu() {
  local durum
  if sudo systemctl is-active --quiet meridian-botlar.service; then
    echo "  · bot ağ geçidi ETKİN: yeniden başladı, /health hazırlığı yukarıda ÖLÇÜLDÜ; sohbet kopyasının değer-doğruluğu"
    echo "    dosya eşitliğidir (envanter, aşağıda)"
    return 0
  fi
  # sessiz-yutma: `is-active` etkin OLMAYAN birimde 3 döner (beklenen); okunan şey DURUM ADIDIR ve okunamazsa satır
  # "ÖLÇÜLEMEDİ" der — not bir durum UYDURMAZ.
  durum="$(sudo systemctl is-active meridian-botlar.service || true)"
  echo "  · bot ağ geçidi etkin değil (${durum:-ÖLÇÜLEMEDİ}): sohbet kopyası YAZILDI, yeni değer birimin ilk açılışında okunur"
}

db() {
  echo "=== ROTASYON: Postgres 'hindsight' rol parolası ==="
  # AGENT RENDER HEDEFİ UYARISI (TSK-064, Rol-1 kararı 2026-09-17): url kopyası Vault Agent'ın
  # render hedefidir. 2026-09-17'de sır kasaya BAĞLI DEĞİLDİ; 2026-09-24'ten beri BAĞLI ve uyarı
  # doğru yolu (`--db --vault`) gösterir. Uyarı kuru kapısının ÜSTÜNDE: kuru koşum operatörün ilk
  # komutudur. Uyarı bir KAPI DEĞİL — eski yol aynen koşar (tek rotasyon yolu kesilmez; v538 Ç7).
  _agent_hedefi_uyarisi db
  [ "$KURU" = 0 ] || { _kuru_rapor db; return 0; }
  _yedek_al db
  # Kaynak root'un 0700 yedeğidir (saldırgan yüzeyi yok); kopya yine `kopyala`dan geçer — araçta root `cp` KALMASIN
  # diye (TSK-261: sınıf bir örnekle kapanmaz; v611 F1s statik çivisi "kabukta `cp` yok" der, istisna listesi tutmaz).
  py kopyala "$YEDEK/etc/hindsight/creds/HINDSIGHT_API_DATABASE_URL" "$ISLIK/eski_url"
  _uret b64
  _yaz db
  _yeniden_baslat db
  _db_kanit "$ISLIK/eski_url"
  echo ">> geri alma: eski parolayı ALTER ROLE ile geri koy + DSN'i geri yaz: sudo $0 --geri-al $YEDEK"
}

# `--db` KANITI — eski yol (`db`) ve kasa yolu (`vault_db_rotasyon`, TSK-064 2026-09-24) AYNI ölçümü
# koşar (tasarım §3.8 "mevcut --db kanıtı aynen"); gövde TEK yerde. `$1` = ESKİ DSN dosyası (negatif
# kontrolün girdisi): eski yolda yedekten, kasa yolunda KASADAN okunan DSN. Pozitif ölçüm her iki yolda
# render hedefindeki (üretim yolu) DSN'e bağlanır.
_db_kanit() {
  local eski_url="$1"
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
  py pgpass "$ISLIK/pgpass_eski" "$eski_url"
  # sessiz-yutma: burada BAŞARISIZLIK BEKLENEN sonuçtur (eski parola artık geçmemeli) — çıkış
  # kodu değil, aşağıda ölçülen HATA METNİ hükümdür; `|| true` olmadan `set -e` ölçümü keserdi.
  cikti="$(PGPASSFILE="$ISLIK/pgpass_eski" psql -w -tAX -h "$host" -p "$port" -U "$kuser" \
             -d "$kdb" -c 'select 1' 2>&1 || true)"
  case "$cikti" in
    *FATAL*|*fatal*|*authentication*) oldu "eski parola: FATAL (kanıt parolaya BAĞLI)" ;;
    *) olcum_yok "ESKİ parola hâlâ bağlanıyor — ALTER ROLE etkisiz ya da kimlik doğrulama kapalı" ;;
  esac
}

dash() {
  echo "=== ROTASYON: MERIDIAN_DASH_TOKEN ==="
  _agent_hedefi_uyarisi dash              # TSK-064 takip (2) — gerekçe `kapi()` şerhinde
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
  # TEK KOPYA (TSK-064 (d-1), 2026-09-17): `.dash.env` 2026-09-14'te silindi ve tablodan çıktı —
  # reçete olmayan bir dosyayı geri koymayı önermez (`--geri-al` yalnız tablonun yollarını yazar).
  echo ">> geri alma: sudo $0 --geri-al $YEDEK (dash_token) ve meridian.service yeniden başlat"
}

# -------------------------------------------------------------------------------------------------
# NEGATİF ÖN-KONTROL — YAZIMDAN ÖNCE, GERİ ALINIR.
# `--openrouter`in kanıt yüzeyleri isteğe anahtar ALMAZ (motor kendi yapılandırdığı anahtarla
# konuşur, kapı kendi upstream anahtarını kullanır) — yani "eski anahtarla 401" ÖLÇÜLEMEZ.
# Tek dürüst yol FARK yaratmaktır: bilerek bozuk bir değer yazılır, yüzey BAŞARISIZ olmalıdır.
# Başarısız OLMUYORSA kanıt anahtara bağlı değildir ve operatörün TAZE anahtarı boşa gitmesin
# diye betik yazımdan ÖNCE durur. Ölçüm KENDİ ARDINI TOPLAR: trap her yolda geri yükler.
# GERİ ALMA YARDIMCININ YAZIM ÇEKİRDEĞİNDEN GEÇER (TSK-261, CWE-59 — her `--openrouter`in OLAĞAN yolu).
# İkinci biçim `sudo cp -p <yedek> "$hedef.yeni" && sudo mv -f …` yazıyordu: `.yeni` ÖNGÖRÜLEBİLİR bir addır
# ve hedef dizinlerin çoğu ubuntu'nundur (hermes profilleri · `/opt/hindsight` · `/opt/meridian/state`). Dizin
# sahibi `.yeni`yi önceden bir root dosyasına bağlarsa root `cp` bağı İZLER, o dosyayı yedeğin (yani ubuntu'nun
# kendi dosyasının) içeriğiyle EZER ve `-p` sahibini ubuntu'ya verir — `/root/.bashrc` ya da
# `/etc/profile.d/*.sh` ile kök kod yürütmeye yeter; `mv -f` ardından bağı hedefin yerine koyar. Servis kimlikleri
# NoNewPrivileges taşır, yani bu bir sandbox kaçışıdır (TSK-260 güvenlik incelemesi §6). Yeni yol `py kopyala`:
# öngörülebilir ad YOK (geçici ad rastgele, `O_EXCL|O_NOFOLLOW`), zincir ve hedef bağ izlenmez (bağsa yazım YOK
# + adlı ret), mod/sahip yedeğin (eski `-p`), yerine koyma ATOMİK, yazım sonrası tanıtıcı + yol ölçülür.
# HEDEF ASLA ARADAN KALDIRILMAZ (ilk biçimin `rm -f` + `cp` dersi — v447 P4): `/etc/meridian/nous_api_key` bir
# `LoadCredential` KAYNAĞIDIR ve kaynak YOKSA systemd birimi HİÇ BAŞLATMAZ. Yerine koyma atomiktir; yazım
# düşerse hedef ESKİ (bozuk) hâliyle YERİNDE durur ve aşağıda BAĞIRILIR. 0400 bir hedefin üzerine yazma izni
# DOSYANIN değil DİZİNİNDİR (yerine koyma onu kullanır).
_negatif_geri_al() {
  local cift yedek hedef basarisiz=""
  for cift in $GERI_AL_LISTESI; do
    yedek="${cift%%|*}"; hedef="${cift#*|}"
    # sessiz-yutma DEĞİL: hata BİRİKTİRİLİR (yardımcının adlı reddi stderr'de durur) — burada durmak öteki
    # dosyaları geri alınmamış bırakırdı; hüküm hemen aşağıda bağırılır.
    py kopyala "$yedek" "$hedef" || basarisiz="$basarisiz $hedef"
  done
  GERI_AL_LISTESI=""
  # `die` DEĞİL `return 1`: bu fonksiyon EXIT trap'in İÇİNDEN de çağrılır ve trap içinde `exit`
  # etmek, arkasından gelen TEMİZLİĞİ yutar (bkz. `_negatif_trap`). Hükmü çağıran verir.
  [ -z "$basarisiz" ] || { echo "!! GERİ ALMA BAŞARISIZ:$basarisiz
     Bu dosyalar BİLEREK BOZUK değer taşıyor OLABİLİR. Yedekten geri koy (bağ İZLEMEDEN): sudo $0 --geri-al $YEDEK
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
    sudo test -e "$KOK$yol" || sudo test -L "$KOK$yol" || continue
    # Yedek de `kopyala`dan geçer (TSK-261): kaynak bağ izlenmeden okunur — bağlı bir hedefin GÖSTERDİĞİ dosya
    # geri alma ile bu hedefe yazılmaz. Ret, hiçbir bozuk değer yazılmadan ÖNCE durdurur (trap henüz kurulmadı).
    py kopyala "$KOK$yol" "$ISLIK/nk-$(echo "$yol" | tr '/' '_')" \
      || die "negatif kontrol yedeği ALINAMADI: $yol — kaynak bağ İZLENMEDEN okunamadı (adlı ret yukarıda).
     Hiçbir bozuk değer YAZILMADI; operatörün anahtarı YAZILMADI."
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
  # TSK-064 takip (2) — gerekçe `kapi()` şerhinde. `_oku_gizli` istemlerinin de ÜSTÜNDE: operatör
  # anahtarı yapıştırmadan ÖNCE doğru yolu görür.
  _agent_hedefi_uyarisi openrouter
  # KURU KAPISI `_oku_gizli` ÇAĞRILARININ ÜSTÜNDE. Altındayken `--openrouter --kuru` bir kuru
  # koşum DEĞİLDİ: iki gerçek anahtar istiyor, boş bırakılınca "yapacak iş yok" deyip çıkış 1
  # veriyordu — yani rotasyonun ÖN-BAKIŞI ancak taze anahtar yapıştırarak alınabiliyordu.
  # Kuru raporun değere ihtiyacı YOKTUR: 15 kopya da, birim listesi de kopya tablosundan gelir.
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
  echo ">> geri alma: sudo $0 --geri-al $YEDEK ve $(_recete_birimleri $(_birimler openrouter)) yeniden başlat"
}

# =================================================================================================
# KASA ROTASYONU — `--<alt> --vault` (TSK-064 Faz-2 DALGA-2)
# =================================================================================================
# NİYE SIRA TERSİNE DÖNÜYOR. Bugünkü rotasyon kopyaları TEK TEK yazar ve "unutulan kopya" sınıfı
# tam olarak buradan doğar (TSK-181: tabloya girmemiş bir kopya dört gün eski anahtarla yaşadı).
# Kasa kanalında yazan TEKtir: değer kasaya konur, Agent onu bütün yan dosyalara render eder ve
# bu betik yalnız RENDER'I ÖLÇER. Eski kanal kopyaları iki-kanal dönemi boyunca AYNI pencerede,
# KASADAN gelen değerle yazılır — yani kasa ile eski kanal ayrışamaz.
#
# KANITLARIN SIRASI BİR TERCİH DEĞİL: render ölçülmeden eski kanal YAZILMAZ. Yazılsaydı, Agent
# render etmiyorken (kasa mühürlü · politika eksik · birim düşmüş) betik kasayı kaynak sanar ve
# ESKİ değeri bütün kopyalara dağıtırdı — rotasyonun tam tersi.
#
# JETON: `vault_sir_koy.sh` ile AYNI disiplin — `login -no-print -` ile STDIN'den, `VAULT_TOKEN=`
# YOK, `$(cat` YOK. Oturum yardımcısı `$ISLIK` (0700, çıkışta silinir) içine düşer: ayrı bir trap
# gerekmez ve kalıcı bir yönetici oturumu diskte kalmaz.
_vault() { HOME="$ISLIK" "$VAULT_BIN" "$@"; }

#: Bir alt komutun döndürdüğü sır KİMLİKLERİ — kopya tablosundan TÜRER.
_alt_sirlari() {
  _kopyalar | awk -v a="$1" '$1==a {print $2}' | sort -u
}

#: `<kv ad>\t<KASA YOLU>\t<render kanıtı hedefi>\t<rotasyon_siri>\t<birincil ad | ->` — verilen
#: sır kimliklerinden KASAYA BAĞLI olanlar. Bağ envanterde `rotasyon_siri` alanıyla kurulur ve o
#: alan `rotasyon_kopyalari` tablosuna çivilidir (v491 A5): burada üçüncü bir liste tutulmaz.
#:
#: TAKMA AD (`ayni_deger`) BURADA ÇÖZÜLÜR: rotasyon BİRİNCİL yola yapılır ve render kanıtı
#: birincilin `hedef`idir — yani takma adlar yeni değeri OTOMATİK izler. Çözülmeseydi rotasyon
#: takma adın kendi yoluna yazar, birincil eski değerde kalır ve "aynı" sanılan iki değer tam da
#: rotasyondan sonra ayrışırdı (hükmün engellediği hâl). Aynı yola çözülen iki satır TEK kez
#: basılır: operatörden aynı değeri iki kez istemek, ikinci girişte yazım hatası riskidir.
_vault_kv_satirlari() {
  "$PYTHON_BIN" -I -c '
import sys, yaml
istenen = set(sys.argv[2:])
kv = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))["vault_kv"]
indeks = {g["ad"]: g for g in kv}
gorulen = set()
for g in kv:
    if g.get("rotasyon_siri") not in istenen:
        continue
    birincil = g.get("ayni_deger")
    if birincil is not None and birincil not in indeks:
        sys.exit("%s: ayni_deger %s vault_kv de YOK (dangling takma ad)" % (g["ad"], birincil))
    kaynak = indeks[birincil] if birincil else g
    if kaynak["vault_yolu"] in gorulen:
        continue
    gorulen.add(kaynak["vault_yolu"])
    print(g["ad"], kaynak["vault_yolu"], kaynak["hedef"], g["rotasyon_siri"],
          birincil or "-", sep="\t")
' "$VAULT_ENVANTER" "$@"
}

#: `<yan dosya yolu>\t<yeniden başlatılacak birim ya da `-`>` — verilen KASA YOLUNU taşıyan yan
#: dosyalar. Restart listesi ELLE yazılmaz: hangi dosyanın hangi birimi ilgilendirdiği envanterin
#: `vault_dosyalar.yeniden_baslat` alanında yaşar.
#:
#: SORGU ADA DEĞİL YOLA GÖREDİR ve fark hükümdür: `secret/meridian/kapi_apikey` yolunu hem
#: `kapi_apikey` hem takma adı `bot_key_meridian` taşır, ve kapının yan dosyası satırını TAKMA
#: ADLA yazar. Ada göre sorsaydık `--kapi --vault` rotasyonu kapıyı yeniden başlatmazdı: yan
#: dosya yeni değere döner, konteyner eski değeri ortamında tutar ve bot 401 alır.
#: İKİNCİ KİP `alan` (G3b Task 4 — Task 3 incelemesi M1): `<yan dosya>\t<alan>\t<önek | ->` — o kasa yolunu taşıyan HER
#: satır (`_yan_render_bekle` restart'tan ÖNCE bunları kasadaki yeni değere kıyaslar; kuru plan basar). Aynı sorgu, aynı
#: yol çözümü: alan kipi dosya kipinin süzgecinin İÇİNDEDİR (v491 T10 mutasyonu ikisini birden ısırır).
_vault_yan_dosyalari() {
  "$PYTHON_BIN" -I -c '
import sys, yaml
hedef_yol, kip = sys.argv[2], sys.argv[3]
veri = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))
indeks = {g["ad"]: g for g in veri["vault_kv"]}
def coz(ad):
    g = indeks[ad]
    b = g.get("ayni_deger")
    return indeks[b]["vault_yolu"] if b else g["vault_yolu"]
for d in veri["vault_dosyalar"]:
    if any(coz(x["sir"]) == hedef_yol for x in d["satirlar"]):
        if kip != "alan":
            print(d["yol"], d.get("yeniden_baslat") or "-", sep="\t")
            continue
        for x in d["satirlar"]:
            if coz(x["sir"]) == hedef_yol:
                print(d["yol"], x["alan"], x.get("onek") or "-", sep="\t")
' "$VAULT_ENVANTER" "$1" "${2:-dosya}"
}

#: Bir kasa sırrının YENİDEN BAŞLATILACAK birimleri — gerçek koşum (`vault_rotasyon`) ile kuru
#: rapor AYNI yardımcıdan okur (tek-kaynak yasası). İki kaynağın BİRLEŞİMİDİR: (1) kasa YOLUNU
#: taşıyan yan dosyaların `yeniden_baslat` birimi, (2) sırrın `_sir_birimleri` tüketicileri.
#: (2) yan dosyası OLMAYAN dalga-1 sırlarının TEK kaynağıdır: `dash_token`/`nous_api_key` hiçbir yan
#: dosyada yaşamaz, onları `LoadCredential` ile okuyan meridian.service'tir. TSK-064 (2026-09-17)
#: öncesi kuru rapor YALNIZ (1)'i basıyordu — bağlanan `--dash --vault --kuru` planında hiçbir birim
#: görünmezdi (bedel yasası: gerçek koşumun yapacağı restart planda GÖRÜNMELİ).
_vault_tuketici_birimleri() {
  local yol="$1" sir="$2" yd yb birimler="" tuk
  while IFS=$'\t' read -r yd yb; do
    [ "$yb" = "-" ] || birimler="$birimler $yb"
  done < <(_vault_yan_dosyalari "$yol")
  tuk="$(_sir_birimleri "$sir")" \
    || die "sır $sir için tüketici birim haritası YOK (_sir_birimleri) — hangi birimin yeniden
     başlayacağı ÖLÇÜLEMEZ; kasaya bağlanan sır haritaya da eklenir (v447 N bölümü)."
  echo "$birimler $tuk"
}

#: VAULT AGENT RENDER HEDEFİNE YAZAN KOPYALAR (TSK-064, Rol-1 kararı 2026-09-17; takip (2) aynı gün).
#: `<sır>\t<kopya yolu>\t<kasa yolu>\t<vault_kv adı>\t<BAGLI|BAGSIZ>\t<alt komut>`: alt komutun
#: `dosya`/`url` kopyalarından yolu bir `vault_kv.hedef` OLANLAR; beşinci sütun sırrın bir
#: `rotasyon_siri` ile kasaya bağlı olup olmadığıdır (takma adın bağı da sayılır).
#: NİYE: Agent bu dosyaları `static_secret_render_interval` aralığıyla kasadan yeniden render eder;
#: eski yolun oraya yazdığı değer kasadaki ESKİ değerle EZİLEBİLİR — rotasyon sessizce geri alınır
#: (hipotez, A1'de ÖLÇÜLMEDİ; ROADMAP TSK-064 14:2xZ). Liste ENVANTERDEN türer: "hangi dosya render
#: hedefi" ve "hangi sır bağlı" gerçekleri `vault_kv`de TEK yerde yaşar, burada ikinci liste YOKTUR.
#: TEK TESPİT YOLU: eski yolun uyarısı (`_agent_hedefi_uyarisi`, iki sınıf) ve kasa kipinin kapsam
#: beyanı (`_bagsiz_agent_hedefleri`, yalnız BAGSIZ) bu tablodan okur. 2026-09-17'de BAGSIZ tek satır
#: `--db`nin url kopyasıydı; 2026-09-24'ten (TSK-064 `--db --vault`) beri BAGSIZ satır YOK — BAGLI
#: satırlar `--kapi`/`--tenant`/`--dash`/`--openrouter`/`--apisix-admin`in credential kaynakları ve
#: `--db`nin url kopyasıdır. BAGSIZ dalı ileride bağsız bir sır için DURUR (v522 A7 sahte envanterle ölçer).
_agent_hedefleri() {
  _kopyalar | awk -v a="$1" '$1==a && ($3=="dosya" || $3=="url") {print $2 "\t" $4 "\t" $1}' \
    | "$PYTHON_BIN" -I -c '
import sys, yaml
kv = yaml.safe_load(open(sys.argv[1], encoding="utf-8"))["vault_kv"]
bagli = {g["rotasyon_siri"] for g in kv if g.get("rotasyon_siri")}
hedefler = {g["hedef"]: g for g in kv if g.get("hedef")}
for satir in sys.stdin:
    sir, yol, alt = satir.rstrip("\n").split("\t")
    if yol not in hedefler:
        continue
    print(sir, yol, hedefler[yol]["vault_yolu"], hedefler[yol]["ad"],
          "BAGLI" if sir in bagli else "BAGSIZ", alt, sep="\t")
' "$VAULT_ENVANTER"
}

#: Kasa kipinin kapsam beyanı YALNIZ bağsız satırları okur: bağlı sırrın doğru yolu zaten
#: `--<alt> --vault`tır ve beyanda görünmez. Süzgeç `_agent_hedefleri`nin üzerindedir — ikinci bir
#: tarama yok (tek tespit yolu).
_bagsiz_agent_hedefleri() {
  local tablo
  tablo="$(_agent_hedefleri "$1")" || return 1
  printf '%s\n' "$tablo" | awk -F'\t' '$5=="BAGSIZ"'
}

#: Agent'ın STATİK sır render aralığı — `VAULT_POLITIKA_URETICI` içindeki `RENDER_ARALIGI` atamasının
#: LİTERALİ okunur, UYDURULMAZ. Modül ÇALIŞTIRILMAZ (`ast`): ops aracının içe aktarımı yan etki ve
#: bağımlılık (PyYAML) taşır, bir uyarı metni için gereksiz. Okunamazsa sayı yerine ÖLÇÜLEMEDİ yazılır
#: — "1 dk" demek, okunmamış bir sayıyı okunmuş göstermek olurdu (uydurma yasağı).
_render_araligi_metni() {
  local aralik
  # sessiz-yutma: python'un hata metni (dosya yok · atama biçimi değişti) hükme GİRMEZ — hüküm
  # aralığın okunup okunamadığıdır ve else dalında "ÖLÇÜLEMEDİ" diye ADIYLA basılır.
  if aralik="$("$PYTHON_BIN" -I -c '
import ast, sys
for d in ast.parse(open(sys.argv[1], encoding="utf-8").read()).body:
    if (isinstance(d, ast.Assign) and len(d.targets) == 1
            and getattr(d.targets[0], "id", None) == "RENDER_ARALIGI"
            and isinstance(d.value, ast.Constant) and isinstance(d.value.value, str)):
        print(d.value.value)
        sys.exit(0)
sys.exit(1)
' "$VAULT_POLITIKA_URETICI" 2>/dev/null)" && [ -n "$aralik" ]; then
    echo "$aralik (ops/vault_politika_uret.py::RENDER_ARALIGI → agent.hcl static_secret_render_interval)"
  else
    echo "ÖLÇÜLEMEDİ — RENDER_ARALIGI okunamadı: $VAULT_POLITIKA_URETICI (sayı uydurulmaz)"
  fi
}

#: `_agent_hedefi_bas <tablo> [sır]` — `_agent_hedefleri` satırlarını UYARI olarak basar (`$2`
#: verilirse YALNIZ o sırrınkini). Metin TEK yerde: başlık, kasa yolu ve "ezilebilir" cümlesi iki
#: sınıfta ORTAK, yalnız çare satırları sınıfa göre ayrılır.
#:   BAGSIZ (2026-09-24'e kadar eski yol `--db`; kasa kipinin kapsam beyanı): "ÖNCE" DEĞİL "AYNI pencerede" yazar ve bu
#:     ölçülmüş bir düzeltmedir: eski yol değeri betik İÇİNDE üretir ve BASMAZ (`_uret`), yani kasa
#:     rotasyondan önce güncellenemez; yazım ↔ kasa ↔ render sırası bu betikte TASARLANMADI.
#:   BAGLI (eski yol, TSK-064 takip (2)): sır kasaya bağlı olduğu için çare TASARLANMIŞTIR — kasadan
#:     rotasyon (`--<alt> --vault`). Render aralığı `_render_araligi_metni`nden okunur.
_agent_hedefi_bas() {
  local tablo="$1" secilen="${2:-}" sir yol kasa ad bag alt aralik=""
  while IFS=$'\t' read -r sir yol kasa ad bag alt; do
    [ -n "$sir" ] || continue
    [ -z "$secilen" ] || [ "$sir" = "$secilen" ] || continue
    if [ "$bag" = "BAGLI" ]; then
      echo "  !! UYARI — VAULT AGENT RENDER HEDEFİ, sır kasaya BAĞLI (bu ESKİ yol): $sir → $yol"
    else
      echo "  !! UYARI — VAULT AGENT RENDER HEDEFİ, kasaya BAĞLI DEĞİL: $sir → $yol"
    fi
    echo "     kasa yolu: $kasa (vault_kv.$ad)"
    echo "     Eski yolun yazımı kasadaki ESKİ değerle EZİLEBİLİR (Agent render aralığında; A1'de"
    echo "     ÖLÇÜLMEDİ). Eski yol YİNE DE KOŞAR — uyarı, kapı değil."
    if [ "$bag" = "BAGLI" ]; then
      [ -n "$aralik" ] || aralik="$(_render_araligi_metni)"
      echo "     Vault Agent bu dosyayı kasadan render eder — aralık: $aralik"
      echo "     Bu sır kasaya BAĞLI — kasa yolunu kullanın: sudo $0 $(_bayrak "$alt") --vault"
    else
      echo "     Kasadaki değer rotasyonla AYNI pencerede elle güncellenmeli (değer STDIN'den, BASILMADAN:"
      echo "     vault kv put $kasa value=-) ve render ölçülmeli (dosya kasadaki yeni değere eşit mi)."
      echo "     Sıra (yazım ↔ kasa ↔ render) bu betikte TASARLANMADI."
    fi
  done <<< "$tablo"
  return 0
}

#: ESKİ YOLUN UYARISI — yazım yapan HER eski yol alt komutu (`db()` 2026-09-17; `kapi`/`tenant`/
#: `dash`/`openrouter`/`apisix_admin` TSK-064 takip (2) aynı gün), kuru kapısının ÜSTÜNDE. Tarama
#: YAPILAMAZSA (PyYAML yok · envanter yok) bu da ADIYLA söylenir ve koşum DURMAZ: uyarı eski yolu
#: KESMEZ (Rol-1 kararı — tek rotasyon yolu kesilmez). Kasa kipi aynı taramada fail-closed'dır
#: (`_vault_kapsam_beyani`): orada PyYAML zaten ön koşuldur.
_agent_hedefi_uyarisi() {
  local alt="$1" tablo
  # sessiz-yutma: python'un hata metni (PyYAML yok · envanter okunamıyor) hükme GİRMEZ — hüküm
  # taramanın yapılıp yapılamadığıdır ve bir satır aşağıda "UYARI ÖLÇÜLEMEDİ" diye ADIYLA basılır.
  if ! tablo="$(_agent_hedefleri "$alt" 2>/dev/null)"; then
    echo "  !! UYARI ÖLÇÜLEMEDİ — Vault Agent render hedefi taraması yapılamadı ($PYTHON_BIN + PyYAML · $VAULT_ENVANTER)."
    echo "     $(_bayrak "$alt") kopyalarından biri Agent'ın render hedefi OLABİLİR: eski yol yazımı kasadaki değerle ezilebilir."
    return 0
  fi
  _agent_hedefi_bas "$tablo"
}

#: KAPSAM BEYANI — alt komutun kasaya BAĞLI OLMAYAN sırları ADIYLA basılır. Bedel yasası: kazanç
#: (kasadan tek kaynak) sayıldı, kayıp (bu tur dönMEYEN anahtar) da sayılmalı. Sessiz kalsaydı
#: operatör "rotasyon bitti" sanır ve öteki anahtar sessizce eski değerde kalırdı.
#: İKİ DAL (TSK-064, 2026-09-17): sırrın kopyası bir Agent RENDER HEDEFİYSE "eski yolla döner"
#: cümlesi YANLIŞ bir güvencedir (yazım ezilebilir) → UYARI basılır; değilse eski metin KALIR.
_vault_kapsam_beyani() {
  local alt="$1" bagli="$2" sir tablo
  tablo="$(_bagsiz_agent_hedefleri "$alt")" \
    || olcum_yok "Vault Agent render hedefi taraması yapılamadı ($VAULT_ENVANTER) — kapsam beyanı
     'eski yolla döner' diyemez: kopya bir render hedefiyse o güvence YANLIŞ olurdu."
  for sir in $(_alt_sirlari "$alt"); do
    printf '%s\n' "$bagli" | awk -v k="$sir" '$4==k{b=1} END{exit !b}' && continue
    if printf '%s\n' "$tablo" | awk -F'\t' -v k="$sir" '$1==k{b=1} END{exit !b}'; then
      _agent_hedefi_bas "$tablo" "$sir"
    else
      echo "  · KAPSAM DIŞI (kasaya bağlı DEĞİL): $sir — eski yolla döner: sudo $0 $(_bayrak "$alt")"
    fi
  done
}

#: DEĞER KAYNAĞI BEYANI (TSK-064 takip (4), 2026-09-17). Kasa yolu yeni değeri operatörden İSTER; eski
#: yol bu alt komutlarda değeri betik İÇİNDE üretir (`_uret`). Beyan olmasaydı eski yola alışmış
#: operatör istemi "üretilecek değerin onayı" sanıp zayıf ya da boş bir değer girebilirdi. Değer de
#: ÖRNEK değer de BASILMAZ. Liste eski yolun `_uret` çağıran alt komutlarıdır (`openrouter` YOK: eski
#: yol da değeri operatörden alır); betiğin kendi fonksiyon gövdeleriyle AYRIŞMA ÇİVİSİ bağlar
#: (v522 — `_uret` çağıran küme ↔ bu küme). Kuru rapor ve gerçek koşumun istem noktası aynı satırı basar.
#: `cp` YOK (TSK-226b) ve bu bilinçlidir: `--cp --vault` genel döngüye girmez, kendi dalında değeri eski
#: yol gibi betik İÇİNDE üretir — iki yolun değer kaynağı AYNI, beyan edilecek fark yok (v556 A4).
#: `--uret` (TSK-226c, 2026-09-26): kasa yolu da değeri betik İÇİNDE üretir → beyan "sizden İSTER" DEMEZ
#: (yalan beyan olurdu), kaynağı söyler. `db` listede kalır: `--db --vault --uret` ayrıştırmada reddedilir,
#: yani `URET=1` iken buraya hiç ulaşmaz. `${URET:-0}`: fonksiyon çivilerde betikten KESİLİP koşar (v522 B3).
#: `_deger_kaynagi_beyani <alt> [bayrak]` — bayrak operatörün yazacağı biçimdir (`_bayrak`; G3b Task 3: `kapi-bot-<ad>` →
#: `--kapi-bot <ad>`); verilmezse `--<alt>` (fonksiyon çivilerde TEK BAŞINA kesilip koşar — v522 B3 · v557 A2 · v556).
_deger_kaynagi_beyani() {
  local bayrak="${2:---$1}"
  case "$1" in
    kapi|tenant|db|dash|apisix-admin|api-sunucu|kapi-bot-*)
      if [ "${URET:-0}" = 1 ]; then
        echo "  · DEĞER KAYNAĞI: betik İÇİNDE üretilir (--uret) — eski yol (sudo $0 $bayrak) ile AYNI yöntem; SORULMAZ, hiçbir yere BASILMAZ."
      else
        echo "  · DEĞER KAYNAĞI: bu yol değeri ÜRETMEZ, sizden İSTER — eski yol (sudo $0 $bayrak) değeri"
        echo "    betik İÇİNDE üretir. Güçlü rastgele bir değer girin (ekrana yansımaz, hiçbir yere BASILMAZ)."
      fi ;;
  esac
}

#: `--uret` — KASA YOLUNUN İSTEM NOKTASININ YERİNE (TSK-226c, 2026-09-26). `_vault_uret <alt> <sır> <render
#: hedefi>` → `$ISLIK/vault_yeni` (istemin yazacağı dosyanın AYNISI: döngünün geri kalanı değerin nereden
#: geldiğini bilmez ve bilmemeli). NİYE: kasa yolu değeri operatörden ister; komutları koşan Rol-1 bir yapay
#: zekâ oturumudur ve bir isteme sır değeri GİREMEZ, eski yol ise kasaya bağlı sırda Agent render'ıyla ezilir.
#: ÜÇ KAPI, üçü de kasaya yazımdan ÖNCE (düşüş = HİÇBİR ŞEY yazılmadı, yedek bile alınmadı):
#:   (1) sınıf eski yolla AYNI (`_uret_sinifi` — ayrışma çivisi v557 A1); (2) uzunluk/boşluk `_uret`in kendi
#:   denetimi; (3) ESKİ DEĞERLE AYNI OLAMAZ — kıyas render hedefinin KANONİK kopyasıyladır, çünkü bu döngünün
#:   kanıtı o dosyanın YENİ değere eşitlenmesidir: hedef zaten "yeni" değeri taşısaydı render ölçümü Agent hiç
#:   çalışmasa da geçerdi (tiyatro). Hedef YOKSA ESKİ değer okunamaz — kıyas UYDURULMAZ, ADIYLA atlanır; boş
#:   hedef render kanıtını sahte geçiremez (kanıt BİREBİR eşitliktir). Değer hiçbir yere BASILMAZ.
_vault_uret() {
  local alt="$1" sir="$2" hedef="$3" sinif hal
  sinif="$(_uret_sinifi "$alt")" \
    || die "--uret: --$alt için üretim sınıfı YOK (_uret_sinifi) — kasaya YAZILMADI: $sir"
  _uret "$sinif" "$ISLIK/vault_yeni"
  hal="$(py esit dosya "$KOK$hedef" - - dosya "$ISLIK/vault_yeni" - -)" \
    || die "ESKİ değer kıyası ÖLÇÜLEMEDİ (yardımcı düştü): $hedef — kasaya YAZILMADI: $sir"
  case "$hal" in
    AYRI) oldu "yeni değer render hedefindeki ESKİ değerden AYRI: $hedef (DEĞER BASILMAZ)" ;;
    "REFERANS YOK")
      echo "  · ESKİ değer kıyası YAPILAMADI: render hedefi YOK ($hedef) — çakışma ölçülemez, 'AYRI' denmez;"
      echo "    render kanıtı yine hedefin YENİ değere BİREBİR eşitlenmesidir (boş hedef onu sahte geçiremez)." ;;
    EŞİT) die "üretilen değer render hedefindeki ESKİ değerle AYNI: $hedef — rotasyon değil ve render kanıtı
     Agent çalışmasa da geçerdi. Kasaya YAZILMADI: $sir (yedek alınmadı). Üretimi (openssl) denetle." ;;
    *) die "ESKİ değer kıyası ÖLÇÜLEMEDİ ($hal): $hedef — kasaya YAZILMADI: $sir" ;;
  esac
}

#: Kuru planın `  değer:` satırının METNİ (TSK-226c). `--uret` iken değer SORULMAZ — "AYRI sorulur" satırı
#: orada yalan olurdu; sınıf gerçek koşumun okuduğu tablodan (`_uret_sinifi`) basılır. Ayrı fonksiyondur ki
#: rapordaki satır sırası (`_birimsiz_tuketici_beyani` → `değer:` → `_deger_kaynagi_beyani`) DEĞİŞMESİN —
#: mutasyon çivileri o bitişikliği çapa olarak kullanır (v521 M9 · v522 M6).
_kuru_deger_metni() {
  if [ "$URET" = 1 ]; then
    echo "betik İÇİNDE üretilir — eski yolun AYNI yöntemi (_uret $(_uret_sinifi "$1")), uzunluk denetlenir; SORULMAZ, BASILMAZ; render hedefindeki ESKİ değerle AYNI olamaz"
  else
    echo "her kasa sırrı AYRI sorulur (ekrana yansımaz); boş bırakılan sır bu tur DÖNMEZ ve ADIYLA söylenir"
  fi
}

_vault_kuru_rapor() {
  local alt="$1" bagli="$2" ad yol hedef sir birincil yd yb hepsi=""
  echo "=== KURU KOŞUM: $(_bayrak "$alt") --vault (HİÇBİR ŞEY YAZILMADI, KASAYA DOKUNULMADI) ==="
  _vault_kapsam_beyani "$alt" "$bagli"
  # Döngü ALT KABUKTA DEĞİL (here-string): restart planı döngüden SONRA basılır ve boru ile
  # beslenen bir `while` `hepsi`yi alt kabukta bırakırdı.
  while IFS=$'\t' read -r ad yol hedef sir birincil; do
    [ -n "$ad" ] || continue
    echo "  kasaya yazılacak : $yol   ($sir → $ad)"
    # Gerçek koşumun `_kasa_surumu`su (TSK-064 takibi): plan da söyler — kuru koşum kasaya DOKUNMAZ, sürümü okumaz.
    echo "  kasa sürümü      : ÖNCE current_version kaydedilir — geri alma: vault kv rollback -version=<o sürüm> $yol (DOSYA geri alımından ÖNCE; okunamaz/geçersizse bu yol YAZILMAZ)"
    # Gerçek koşumun ESKİ değer yedeği (TSK-064(b)) — `--db`/`--cp` kuru planlarının "ESKİ değer yedeğe" adımının ikizi.
    echo "  ESKİ değer yedeği: yedeklenir — kv put ÖNCESİ KASADAN okunur → $KOK/root/sir-yedek-<UTC ts>-$alt/vault/$yol (0600); rollback düşerse STDIN'le: vault kv put $yol value=- (değer BASILMAZ; okunamazsa bu yol YAZILMAZ)"
    [ "$birincil" = "-" ] \
      || echo "  TAKMA AD         : $ad → $birincil   (yol ve render kanıtı BİRİNCİLİNDİR; takma adın tüketicileri onu izler)"
    echo "  render kanıtı    : $hedef   (kanonik tek-değer kopyası — sha DEĞİL, BİREBİR kıyas)"
    while IFS=$'\t' read -r yd yb; do
      echo "    · yan dosya: $yd   (yeniden başlat: $yb)"
    done < <(_vault_yan_dosyalari "$yol")
    # Gerçek koşumun restart ÖNCESİ yan dosya ölçümü (G3b Task 4, `_yan_render_bekle`) — bedel yasası: planda görünür.
    if _kasa_kaniti "$alt" var; then
      echo "  yan dosya render kanıtı: restart'tan ÖNCE her alan kasadaki yeni değere BİREBİR (tavan $VAULT_RENDER_TAVAN_S s; aşımda ÖLÇÜLEMEDİ — eski kanal YAZILMAZ, restart YOK):"
      _yan_alan_plani "$yol"
    fi
    echo "  eski kanal (iki-kanal dönemi) AYNI pencerede kasadan gelen değerle yazılır:"
    _kopyalar | awk -v a="$alt" -v k="$sir" '$1==a && $2==k {printf "    · %s %s\n", $4, ($5=="-"?"":"["$5"]")}'
    hepsi="$hepsi $(_vault_tuketici_birimleri "$yol" "$sir")"
  done <<< "$bagli"
  # shellcheck disable=SC2086
  echo "  yeniden başlatılacak: $(_sirala $hepsi)   (değeri VERİLEN sırların tüketicileri — boş bırakılan sırrınki başlamaz)"
  # shellcheck disable=SC2046,SC2086
  _kosullu_kuru_notu $(_sirala $hepsi)
  _birimsiz_tuketici_beyani "$alt"
  echo "  değer: $(_kuru_deger_metni "$alt")"
  _deger_kaynagi_beyani "$alt" "$(_bayrak "$alt")"
  echo "  render bekleme tavanı: $VAULT_RENDER_TAVAN_S s (yoklama aralığı $VAULT_RENDER_ARALIK_S s; aşımda ÖLÇÜLEMEDİ, eski kanal YAZILMAZ)"
  # Restart SONRASI tüketici kanıtı (G3b Task 4) — kanıtı olmayan alt komutta satır YOK (gerçek koşum "ÖLÇÜLMEDİ (None)" der).
  if _kasa_kaniti "$alt" var; then _kasa_kaniti "$alt" plan; fi
  echo "  ÖN KOŞUL: sudo systemctl stop meridian-tick-watchdog.timer (sonda geri aç)"
  echo "  ÖN KOŞUL: kasa AÇIK (mühürsüz) ve vault-agent AYAKTA olmalı — yoksa render gelmez"
  echo "  yedek dizini: $KOK/root/sir-yedek-<UTC ts>-$alt"
}

#: KASA OTURUMU — genel döngü ve `--db` dalı AYNI kapıdan geçer (tek-kaynak). Jeton STDIN'den
#: (`login -no-print -`), `VAULT_TOKEN=` YOK; oturum yardımcısı `$ISLIK`e düşer (bkz. `_vault`).
_vault_oturum() {
  [ -s "$VAULT_JETON_DOSYASI" ] || die "yönetici jetonu yok/boş: $VAULT_JETON_DOSYASI
     (vault_kur.sh adım 10 yazar) — kasaya HİÇBİR ŞEY yazılmadı"
  _vault login -no-print - < "$VAULT_JETON_DOSYASI" >/dev/null \
    || die "yönetici jetonuyla oturum açılamadı ($VAULT_JETON_DOSYASI)"
}

#: KASA SÜRÜMÜ — `kv put` ÖNCESİ `current_version`, yani geri almanın HEDEFİ (`vault kv rollback -version=<o>`).
#: TEK YER (TSK-064 takibi, 2026-09-27): genel döngü, `--db` ve `--cp` dalları aynı kapıdan geçer — üç kopya
#: sessizce ayrışırdı (tek-kaynak yasası; iki dalın bu tura kadarki satır içi bloğu v561 E1'de iz kıyaslı).
#: `_kasa_surumu <kasa yolu> <yazılmadı metni>` → `KASA_SURUM` (global). `$(…)` DEĞİL: alt kabuktaki `die`
#: yalnız alt kabuğu öldürür ve hüküm çağıranın `set -e` bağlamına kalırdı. Okunamazsa ya da geçersizse
#: (boş · sayı değil · 0) `die` — bu yol için kasaya HİÇBİR ŞEY yazılmadan. Metin ÇAĞIRANINDIR: tek sırlı
#: dallar "HİÇBİR ŞEY yazılmadı" der; genel döngünün ikinci sırrında ilk sır ZATEN kasadadır (yalan olurdu).
#: YOL YOKSA (meta yok → ilk yazım): gerçek Vault `kv metadata get`te 2 ile düşer (stdout boş) → `pipefail` →
#: okunamadı; meta var ama sürüm yoksa `current_version` 0 → geçersiz. İkisi de DURUR: geri alma hedefi
#: olmayan bir yazım rotasyon değil BAĞLAMADIR (`deploy/vault/vault_sir_koy.sh`in işi).
_kasa_surumu() {
  local yol="$1" yazilmadi="$2"
  KASA_SURUM="$(_vault kv metadata get -format=json "$yol" \
    | "$PYTHON_BIN" -I -c 'import json, sys; print(int(json.load(sys.stdin)["data"]["current_version"]))')" \
    || die "kasa sürümü okunamadı ($yol) — geri alma hedefi bilinmeden kasaya YAZILMAZ ($yazilmadi)"
  case "$KASA_SURUM" in
    ''|*[!0-9]*|0) die "kasa sürümü geçersiz: '$KASA_SURUM' ($yol) — kasaya $yazilmadi" ;;
  esac
  oldu "kasa sürümü (yazım ÖNCESİ): $KASA_SURUM — geri alma: vault kv rollback -version=$KASA_SURUM"
}

#: RENDER BEKLEME — TEK YER (TSK-064 `--db --vault` ile genel döngüden ÇIKARILDI, 2026-09-24: DB dalı
#: render'ı İKİ kez bekler — yeni DSN, ve ALTER düşerse geri alınan ESKİ DSN). `_render_bekle <hedef>
#: <beklenen kanon dosyası>`: hedefin kanonik kopyası beklenene BİREBİR (sha DEĞİL, `cmp`) eşit olana
#: kadar yoklar, tavan `VAULT_RENDER_TAVAN_S`. 0 = ölçüldü (süre `RENDER_GECEN`de), 1 = tavan aşıldı —
#: HÜKMÜ ÇAĞIRAN verir (genel döngü `olcum_yok`, DB dalı önce kasayı geri alır).
#: `py cikar` düşüşü AÇIKÇA `die`dır: fonksiyon `if !` içinden çağrılır ve orada `set -e` SUSAR — satır
#: içeride kalsaydı okunamayan hedef sessizce "henüz render yok" sayılıp tavana kadar yoklanırdı
#: (döngü genel akışın içindeyken aynı düşüş çıkış 1 veriyordu; davranış korunur).
_render_bekle() {
  local hedef="$1" beklenen="$2" bas
  _saat_oku; bas="$SAAT_MS"       # MONOTONİK (bkz. `_saat_oku`): askı bekleme sayılmaz
  while :; do
    if sudo test -s "$KOK$hedef"; then
      py cikar dosya "$KOK$hedef" - - "$ISLIK/vault_render_kanon" \
        || die "render hedefi OKUNAMADI: $hedef (kanonik kopya çıkarılamadı) — render ölçülemez"
      if sudo cmp -s "$beklenen" "$ISLIK/vault_render_kanon"; then break; fi
    fi
    _gecen_s "$bas"; RENDER_GECEN="$GECEN_S"
    [ "$RENDER_GECEN" -lt "$VAULT_RENDER_TAVAN_S" ] || return 1
    sleep "$VAULT_RENDER_ARALIK_S"
  done
  _gecen_s "$bas"; RENDER_GECEN="$GECEN_S"
}

#: KASA YOLUNUN TÜKETİCİ KANITI (G3b Task 4 — Task 3 incelemesi M1, Rol-1 0. madde). Genel döngü 2026-10-01'e dek bu alt
#: komutlarda "değer-doğruluğu ÖLÇÜLMEDİ (None)" basıp geçiyordu: render KANONİK kopyada ölçülüyor, ama kapı değeri docker'ın
#: İKİNCİ `--env-file`ından (`.env-apisix.vault`, Agent yazar) alır ve aynı anahtarda o KAZANIR — yan dosya render'ı aynı turda
#: geride kalırsa kapı ESKİ anahtarla açılır, bot 401 alır ve hiçbir satır söylemezdi. Bu alt komutlarda artık iki ölçüm:
#: (1) restart'tan ÖNCE yan dosya alanları kasadaki yeni değere BİREBİR (`_yan_render_bekle`), (2) restart'tan SONRA eski
#: yolun AYNI kanıtı (`_farksal` — yeni 200 · eski 401; ESKİ değer yazım ÖNCESİ KASADAN okunan yedektir). Ölçülemezse
#: `olcum_yok` (çıkış 2) — sessiz başarı yok. Botlar etkin değilken `--api-sunucu` kanıtı Task 2 davranışıyla "ölçülemedi —
#: birim etkin değil" der (çıkış 0; yeni değer ilk açılışta okunur).
#: KAPSAM BEYANI (bedel yasası): aynı sınıfın öteki üyeleri — `--tenant` (`.env-cp.vault` DATAPLANE), `--apisix-admin` ve
#: `--openrouter` (`.env-apisix.vault` · `.env.vault`) — yan dosya ölçümüne BU TURDA girmedi (operatör brief'i üç alt komutu
#: adlandırdı; o yolların çivi dünyaları yan dosya render'ı modellemiyor). `--openrouter`in kendi kanıtı (kapı chat) vardır.
#: TEK LİSTE: `_kasa_kaniti <alt> var|plan|kos [yeni] [eski]` — `var` üyelik (yan dosya ölçümü ve kanıt aynı kümeye bakar),
#: `plan` kuru satırı, `kos` kanıt. Üyelik dışı alt komut 1 döner. Yalnız TEK sırlı alt komutlar (kanıt son sırrın kanonuna
#: ve yedeğine bakar).
_kasa_kaniti() {
  local alt="$1" kip="$2"
  case "$alt" in
    kapi|api-sunucu|kapi-bot-*) ;;
    *) return 1 ;;
  esac
  case "$kip" in
    var) return 0 ;;
    plan|kos) ;;
    *) die "_kasa_kaniti: bilinmeyen kip '$kip' (var | plan | kos)" ;;
  esac
  case "$alt" in
    kapi)       if [ "$kip" = plan ]; then _kapi_kanit_plani; else _kapi_kanit "$3" "$4"; fi ;;
    api-sunucu) if [ "$kip" = plan ]; then _api_sunucu_kanit_plani; else _api_sunucu_kanit "$3" "$4"; fi ;;
    kapi-bot-*) if [ "$kip" = plan ]; then _kapi_bot_kanit_plani "${alt#kapi-bot-}"
                else _kapi_bot_kanit "${alt#kapi-bot-}" "$3" "$4"; fi ;;
  esac
}

#: YAN DOSYA RENDER BEKLEME — restart'tan ÖNCE (G3b Task 4). `_yan_render_bekle <kasa yolu> <yeni kanon dosyası>`: kasa
#: yolunu taşıyan HER yan dosya alanı (`_vault_yan_dosyalari <yol> alan` — envanter `vault_dosyalar`, takma ad çözülmüş)
#: kasadaki yeni değere BİREBİR olana kadar yoklanır (`py esit` — önek soyulur, DEĞER BASILMAZ). Tavan ve aralık kanonik
#: render'ınkiyle AYNI sabitlerdir (`VAULT_RENDER_TAVAN_S` / `_ARALIK_S`; Agent aynı turda yazar), süre TEK pencerede
#: ölçülür. Aşılırsa `olcum_yok`: ESKİ KANAL YAZILMAZ ve HİÇBİR birim yeniden BAŞLATILMAZ — kapının eski anahtarla açılması
#: tam da önlenen hâldir; kasa YENİ değerdedir ve geri alma reçetesi (`_genel_kasa_recetesi`) onu söyler. Yan dosyası
#: OLMAYAN yol (`api_server_key` — Hermes `.env.vault` okumaz) ADIYLA söylenir.
#: Okunamayan envanter de `olcum_yok`tur: hangi dosyanın beklendiği bilinmeden restart edilmez. Çivi: v604 C10/C10b.
_yan_render_bekle() {
  local yol="$1" kanon="$2" satirlar yd alan onek bas hal bekleyen
  satirlar="$(_vault_yan_dosyalari "$yol" alan)" \
    || olcum_yok "yan dosya taraması yapılamadı ($VAULT_ENVANTER) — kapının hangi dosyadan okuduğu bilinmeden
     restart edilmez. ESKİ KANAL YAZILMADI, birim YENİDEN BAŞLATILMADI."
  if [ -z "$satirlar" ]; then
    echo "  · yan dosya YOK ($yol): bu kasa yolunu taşıyan Agent yan dosyası yok — tüketici kanonik kopyadan ya da eski"
    echo "    kanaldan okur (ölçülecek ikinci render yok)"
    return 0
  fi
  adim "yan dosya render bekle: $yol (restart'tan ÖNCE — tavan $VAULT_RENDER_TAVAN_S s)"
  _saat_oku; bas="$SAAT_MS"       # MONOTONİK (bkz. `_saat_oku`)
  while :; do
    bekleyen=""
    while IFS=$'\t' read -r yd alan onek; do
      [ -n "$yd" ] || continue
      hal="$(py esit dosya "$kanon" - - env "$KOK$yd" "$alan" "$onek")" \
        || die "yan dosya kıyası ÖLÇÜLEMEDİ (yardımcı düştü): $yd [$alan]"
      [ "$hal" = "EŞİT" ] || bekleyen="${bekleyen:+$bekleyen · }$yd [$alan] → $hal"
    done <<< "$satirlar"
    [ -n "$bekleyen" ] || break
    _gecen_s "$bas"
    [ "$GECEN_S" -lt "$VAULT_RENDER_TAVAN_S" ] || olcum_yok "yan dosya render bekleme aşıldı ($VAULT_RENDER_TAVAN_S s): $bekleyen
     Kanonik kopya kasadaki YENİ değerde ama yan dosya DEĞİL: kapı (docker'ın İKİNCİ --env-file'ı aynı anahtarda KAZANIR)
     yeniden başlasaydı ESKİ anahtarla açılırdı ve tüketici 401 alırdı. ESKİ KANAL YAZILMADI, birim YENİDEN BAŞLATILMADI;
     kasa YENİ değerde — geri alma reçetesi aşağıda. Bak: systemctl status vault-agent · journalctl -u vault-agent -n 50 --no-pager"
    sleep "$VAULT_RENDER_ARALIK_S"
  done
  _gecen_s "$bas"
  while IFS=$'\t' read -r yd alan onek; do
    [ -n "$yd" ] || continue
    oldu "yan dosya render ÖLÇÜLDÜ: $yd [$alan] ($GECEN_S s) — kasadaki yeni değerle BİREBİR (DEĞER BASILMAZ)"
  done <<< "$satirlar"
}

#: Kuru planın yan dosya alanları — gerçek koşumun `_yan_render_bekle`siyle AYNI sorgu (iki liste yok).
_yan_alan_plani() {
  local satirlar yd alan onek
  satirlar="$(_vault_yan_dosyalari "$1" alan)" \
    || olcum_yok "yan dosya taraması yapılamadı ($VAULT_ENVANTER) — kuru plan yan dosya ölçümünü SÖYLEYEMEZ"
  if [ -z "$satirlar" ]; then
    echo "    · yan dosya YOK — bu kasa yolunu taşıyan Agent yan dosyası yok (ölçülecek ikinci render yok)"
    return 0
  fi
  while IFS=$'\t' read -r yd alan onek; do
    [ -n "$yd" ] || continue
    echo "    · $yd [$alan]"
  done <<< "$satirlar"
}

#: KANAL BEYANI — genel döngünün SON satırı (TSK-064 iki-kanal kapanışı, 2026-09-29). `_kanal_beyani <alt> <render
#: hedefleri>`: alt komutun kopya tablosunda render hedefi OLMAYAN bir satır (asıl dosyadaki sır satırı · motor
#: deposu) varsa iki kanal AÇIKTIR ve eski metin basılır; yoksa "TEK KANAL" — `--tenant` 2026-09-29'dan beri
#: (`.key` + `.env-cp` emekli), `--dash` 2026-09-17'den beri (d-1) böyledir ve sabit "İKİ KANAL AÇIK" satırı orada
#: YALAN olurdu. Tablodan türer (v590 C10).
#: HERMES `.env` KOPYALARI KAPATILACAK ESKİ KANAL DEĞİLDİR (G3b, 2026-10-01): hermes-agent `.env.vault` OKUMAZ (ölçüldü
#: 2026-09-15) ve kasadan beslenmesinin TEK yolu bu döngünün `.env`e yazmasıdır — C sınıfında iki-kanal KALICIDIR
#: (envanter `vault_dosyalar` HERMES şerhi). Kiracı anahtarının sohbet kopyaları ve `api-sunucu`nun dört `.env` kopyası bu
#: sınıftadır; onları "kapatılacak asıl dosya satırı" saymak `--tenant`e YALAN bir "İKİ KANAL AÇIK — kapatma adımı"
#: bastırırdı. Sayılmazlar ama SUSULMAZ: TEK KANAL satırının altında sayıyla, KALICI diye söylenirler (bedel yasası).
#: Sınıf yolla tanınır: rapor kökü `/home/ubuntu/.hermes/` ve sohbet kökü `$_SOHBET_KOKU/` (v604 B13).
_kanal_beyani() {
  local alt="$1" hedefler="$2" n m sayim
  sayim="$(_kopyalar | awk -v a="$alt" -v h="$hedefler" -v s="$_SOHBET_KOKU/" '
    BEGIN { k = split(h, x, " "); for (i = 1; i <= k; i++) H[x[i]] = 1 }
    $1 == a && !($4 in H) {
      if (index($4, "/home/ubuntu/.hermes/") == 1 || (s != "/" && index($4, s) == 1)) m++
      else c++
    }
    END { print c + 0, m + 0 }')"
  n="${sayim%% *}"; m="${sayim##* }"
  if [ "$n" -gt 0 ]; then
    echo ">> İKİ KANAL AÇIK: asıl dosyalardaki sır satırları DOKUNULMADAN duruyor. Kapatma AYRI bir"
    echo "   adımdır (≥2 gece sonra, yedekli) — geri alım: systemctl stop vault-agent + drop-in kaldır."
  else
    echo ">> TEK KANAL: --$alt kopyalarının HEPSİ Agent render hedefi; kapatılacak eski kanal YOK."
    echo "   Emekli kopyaların diskte kalıp kalmadığını --envanter ölçer."
    [ "$m" = 0 ] || echo "   hermes .env kopyası ($m) KALICI rotasyon kanalıdır (C sınıfı — hermes .env.vault OKUMAZ); kapatılmaz."
  fi
}

vault_rotasyon() {
  local alt="$1" bagli ad yol hedef sir birincil poz="" donen="" yazilmadi hedefler="" kanit_yol=""
  echo "=== ROTASYON (KASADAN): $(_bayrak "$alt") --vault ==="
  bagli="$(_vault_kv_satirlari $(_alt_sirlari "$alt"))"
  # BAĞSIZ ALT KOMUT (TSK-064, 2026-09-17; `--db` 2026-09-24'ten beri BAĞLI — bugün böyle bir alt
  # komut YOK): düz "eski yolla döndür" cümlesi, kopya bir Agent render hedefiyse YANLIŞ bir
  # güvencedir. Kapsam beyanı ÖNCE basılır (uyarı ya da eski metin, sırra göre), sonra durulur —
  # kasaya HİÇBİR ŞEY yazılmaz.
  if [ -z "$bagli" ]; then
    _vault_kapsam_beyani "$alt" ""
    die "--vault: $(_bayrak "$alt") alt komutunun kasaya BAĞLI sırrı YOK
     (envanterde hiçbir vault_kv girdisi bu alt komutun sırlarını rotasyon_siri ile göstermiyor).
     Eski yol: sudo $0 $(_bayrak "$alt") — önce yukarıdaki kapsam beyanını oku (UYARI varsa kasa AYNI
     pencerede elle güncellenir). Kasaya HİÇBİR ŞEY yazılmadı."
  fi
  # `--db` AYRI DALDIR (TSK-064, tasarım §3): kasa TAM DSN taşır ama rotasyonun sırrı yalnız PAROLA
  # alanıdır ve parolanın ikinci hakikat noktası GERİ ALINAMAZ bir kanaldır (`ALTER ROLE`). Genel
  # döngünün "değeri kasaya koy → render → eski kanalı yaz" sırası orada YANLIŞ olurdu.
  if [ "$alt" = db ]; then vault_db_rotasyon "$bagli"; return 0; fi
  # `--cp` DA AYRI DALDIR (TSK-226b): değer üretilir (sorulmaz), kanıtın negatif ayağı ESKİ değeri kasadan
  # ister, geri alma evreye göredir — gerekçe `vault_cp_rotasyon` şerhinde.
  if [ "$alt" = cp ]; then vault_cp_rotasyon "$bagli"; return 0; fi
  [ "$KURU" = 0 ] || { _vault_kuru_rapor "$alt" "$bagli"; return 0; }
  _vault_kapsam_beyani "$alt" "$bagli"

  _vault_oturum

  # SATIRLAR DOSYADAN, fd 3 ÜZERİNDEN okunur: `_oku_gizli` STDIN'den `read -rs` yapar ve döngüyü
  # bir süreç ikamesine bağlasaydık operatörün yapıştırdığı değer değil TABLO okunurdu.
  _vault_kv_satirlari $(_alt_sirlari "$alt") > "$ISLIK/vault_kv.tsv"
  while IFS=$'\t' read -r ad yol hedef sir birincil <&3; do
    [ -n "$ad" ] || continue
    adim "kasa sırrı: $sir → $yol"
    [ "$birincil" = "-" ] \
      || echo "  TAKMA AD: $ad → $birincil — rotasyon BİRİNCİL yola yapılır, takma adın yan dosya alanları onu otomatik izler"
    # BOŞ DEĞER = BU SIR BU TUR DÖNMEZ (TSK-064, 2026-09-17). `nous_api_key` bağlanınca
    # `--openrouter --vault` İLK KEZ iki sırlı döngü koşar. Eskiden boş değer `die` ediyordu: ikinci
    # sırda "kasaya HİÇBİR ŞEY yazılmadı" YANLIŞ olurdu (ilk sır kasada), yalnız OPENROUTER'ı döndürmek
    # imkânsızlaşırdı ve `_oku_gizli`nin kendi istemi ("boş = bu bacağı atla") yalan söylerdi. Eski
    # yolun `openrouter()` sözleşmesiyle AYNI: her anahtar ayrı sorulur, hiçbiri verilmezse durulur.
    _deger_kaynagi_beyani "$alt" "$(_bayrak "$alt")"   # istemden HEMEN önce (TSK-064 takip (4))
    # `--uret` (TSK-226c): istem YOK — değer eski yolun yöntemiyle AYNI dosyaya üretilir (`_vault_uret`).
    # Buradan sonrası (yedek · kanon · kasa · render · eski kanal · restart · kanıt) iki kipte BİREBİR (v557 C3).
    if [ "$URET" = 1 ]; then
      _vault_uret "$alt" "$sir" "$hedef"
    elif ! _oku_gizli "$sir (KASAYA konacak)" "$ISLIK/vault_yeni"; then
      echo "  · ATLANDI: $sir — değer boş; kasaya YAZILMADI ve bu tur DÖNMEDİ (yürürlükteki değer kalır)"
      continue
    fi
    donen="$donen $sir"
    # EVRE yedekten ÖNCE (`--db`/`--cp` emsali; TSK-064 takibi): `_yedek_al` yarıda düşerse reçete dosya kopyası
    # değil "GEREKMEZ" der; YEDEK atanmadan düşerse reçete zaten basılmaz. Evre GERİ GİTMEZ (ikinci sır `kasa`yı korur).
    [ -n "$GENEL_KASA_EVRE" ] || GENEL_KASA_EVRE=yedek
    [ -n "$YEDEK" ] || _yedek_al "$alt"
    # KANONİK BİÇİM: sondaki yeni satır kırpılır. Agent şablonu da onu yazmaz, yani kırpılmış
    # biçim kanaldaki KANONİK biçimdir (vault_sir_koy.sh kural 2 ile AYNI sözleşme).
    py cikar dosya "$ISLIK/vault_yeni" - - "$ISLIK/vault_yeni_kanon"

    # KASA SÜRÜMÜ ÖNCE (TSK-064 takibi; TSK-226c incelemesi BULGU 1): geri almanın hedefi yazımdan ÖNCE kaydedilir —
    # kaydedilmeseydi reçete yalnız dosya önerir ve Agent geri konan dosyayı bir sonraki render'da kasadaki YENİ
    # değerle EZERDİ. Okunamazsa BU yol yazılmaz; bu turda ÖNCE yazılan yol varsa "HİÇBİR ŞEY" demek yalan olurdu.
    yazilmadi="HİÇBİR ŞEY yazılmadı"
    [ -z "$GENEL_KASA_SATIRLARI" ] || yazilmadi="bu sır YAZILMADI; bu turda ÖNCE yazılan kasa yolu VAR — reçete aşağıda"
    _kasa_surumu "$yol" "$yazilmadi"
    # ESKİ DEĞER YEDEĞİ (TSK-064(b), 2026-09-27) — `--db`/`--cp` dallarının AYNI yöntemi (ayrışma çivisi v567 A1).
    # `kv rollback`un KENDİSİ düşerse (politika · ağ · mühür) geri almanın tek girdisi yazım ÖNCESİ KASA değeridir.
    # KASADAN okunur, render hedefinden DEĞİL: Agent geride kaldıysa ikisi ayrışır ve doğru olan kasadakidir.
    # Sürüm kapısından SONRA: yol yoksa (ilk yazım) o kapı ZATEN durdurur ve hata metni değişmez. Satır + evreden
    # ÖNCE: okunamazsa bu yol reçeteye girmez ve kasaya YAZILMAZ (yedeksiz güvence YOK). Değer BASILMAZ, argv'ye
    # GİRMEZ: kv get çıktısı 0600 dosyaya yönlenir, `py cikar` yalnız dosya YOLU alır.
    ( umask 077; _vault kv get -field=value "$yol" > "$ISLIK/vault_eski_ham" ) \
      || die "ESKİ değer kasadan okunamadı ($yol) — rollback düşerse geri konacak yedek olmadan kasaya YAZILMAZ ($yazilmadi)"
    sudo install -d -m 0700 -o root -g root "$YEDEK/vault/$(dirname "$yol")"
    py cikar dosya "$ISLIK/vault_eski_ham" - - "$YEDEK/vault/$yol"
    oldu "yedek: ESKİ değer (KASADAN) → $YEDEK/vault/$yol (0600 — geri almanın girdisi)"
    # Satır + evre yazımdan ÖNCE (`--db`/`--cp` emsali): put düşse bile kasaya ulaşmış OLABİLİR — reçete bu yolu da
    # geri alır. Ulaşmadıysa `rollback -version=<o sürüm>` aynı değeri yeni sürüm yazar: zararsız.
    GENEL_KASA_SATIRLARI="$GENEL_KASA_SATIRLARI$yol"$'\t'"$KASA_SURUM"$'\t'"$hedef"$'\n'
    GENEL_KASA_EVRE=kasa

    tr -d '\r\n' < "$ISLIK/vault_yeni" | _vault kv put "$yol" value=- >/dev/null \
      || die "kasaya yazılamadı: $yol"
    oldu "kasaya yazıldı: $yol (DEĞER BASILMAZ)"

    adim "render bekle: $hedef (tavan $VAULT_RENDER_TAVAN_S s)"
    if ! _render_bekle "$hedef" "$ISLIK/vault_yeni_kanon"; then
      # İKİ SIRLI TUR (TSK-064, 2026-09-17): bu sırdan ÖNCE dönen sır kasada ve eski kanalda YENİ
      # değerdedir ama tüketicisi YENİDEN BAŞLATILMADI (restart döngüden sonra gelir). Sessiz
      # kalsaydı operatör "hiçbir şey olmadı" sanardı; hâl ADIYLA basılır, geri alma yedektedir.
      [ "$donen" = " $sir" ] || echo "!! BU TURDA ÖNCE DÖNEN SIR:${donen% "$sir"}— kasada ve eski kanalda YENİ değerde;
     tüketicileri YENİDEN BAŞLATILMADI (yedek: $YEDEK)." >&2
      olcum_yok "render bekleme aşıldı: $hedef ($VAULT_RENDER_TAVAN_S s içinde kasadaki yeni
     değere eşitlenmedi). Agent render ETMİYOR olabilir: kasa mühürlü · politika eksik · birim
     düşmüş. ESKİ KANAL YAZILMADI — kasadan gelmeyen bir değeri yaymak, kasayı kaynak sanıp ESKİ
     değeri bütün tüketicilere dağıtmak olurdu.
     Bak: systemctl status vault-agent · journalctl -u vault-agent -n 50 --no-pager"
    fi
    oldu "render ÖLÇÜLDÜ: $hedef ($RENDER_GECEN s) — kanonik kopya kasadaki değerle BİREBİR"
    hedefler="$hedefler $hedef"
    # YAN DOSYA RENDER'I — tüketici kanıtı olan alt komutlarda eski kanaldan ve restart'tan ÖNCE (G3b Task 4; gerekçe
    # `_kasa_kaniti` şerhinde). Kanıtın ESKİ ayağı bu yolun yedeğidir (`$YEDEK/vault/<yol>`, yukarıda alındı).
    if _kasa_kaniti "$alt" var; then
      _yan_render_bekle "$yol" "$ISLIK/vault_yeni_kanon"
      kanit_yol="$yol"
    fi
    # `--uret`: değeri operatör GÖRMEDİ — nerede durduğu söylenir (ör. `--dash`ın pano jetonunu elle eşitleyen
    # okur oradan alır); değerin kendisi BASILMAZ.
    [ "$URET" = 0 ] \
      || echo "  · --uret: yeni değer hiçbir yere BASILMADI — kasadadır ($yol) ve render hedefindedir ($hedef)."

    adim "eski kanal (iki-kanal dönemi): kopyalar KASADAN gelen değerle yazılır"
    # `api` kopyası (NOUS) burada restart ve kanıttan ÖNCE yazılır: `_api_yaz` hata metni bunu
    # söylesin (TSK-064 takip (5)). Yalnız METİN bağlamıdır — yazım ve sıra aynen.
    YAZIM_AKISI=kasa
    _yaz "$alt" "$sir" "$ISLIK/vault_render_kanon"

    # RESTART LİSTESİ KASA YOLUNDAN TOPLANIR, ADDAN DEĞİL: aynı yola çözülen her ad (birincil +
    # takma adları) o yolun tüketicilerini getirir. Ada göre sorsaydık takma adın yan dosyasını
    # taşıyan birim listeye HİÇ girmezdi. Kuru rapor AYNI yardımcıdan okur.
    poz="$poz $(_vault_tuketici_birimleri "$yol" "$sir")"
  done 3< "$ISLIK/vault_kv.tsv"
  [ -n "$donen" ] || die "değer boş — yapacak iş yok (kasaya HİÇBİR ŞEY yazılmadı)"

  # shellcheck disable=SC2086
  poz="$(_sirala $poz)"
  # shellcheck disable=SC2086
  _yeniden_baslat "$alt" $poz
  _birimsiz_tuketici_beyani "$alt"

  case "$alt" in
    openrouter)
      # KANITLAR DÖNEN SIRRA BAĞLIDIR (eski yolun `openrouter()` sözleşmesi): dönmeyen OPENROUTER için
      # kapı kanıtını "kanıt" diye basmak, ölçülmeyen bir rotasyonu ölçülmüş göstermek olurdu.
      case " $donen " in
        *" OPENROUTER_API_KEY "*)
          _model_gerekli
          local hal; hal="$(_kapi_chat_hali)"
          [ "$hal" = "OK" ] || olcum_yok "kapı chat/completions → $hal (OK bekleniyordu: 200 + gövdede choices)"
          oldu "kapı kanıtı: chat/completions 200 · gövdede choices (DEĞER-DOĞRULUĞU kanıtı)"
          local kod; kod="$(_kod "-" "$HINDSIGHT/health" "-" "-")"
          [ "$kod" = "200" ] || olcum_yok "hindsight /health → $kod (servis ayakta DEĞİL)"
          oldu "hafıza yüzeyi: /health 200 — servis ayakta; LLM anahtarı için kanıt DEĞİL (uç anahtar istemez)" ;;
      esac
      # NOUS (TSK-064, 2026-09-17): eski yoldaki VARLIK kanıtının AYNISI. Kapsam FARKI beyanlıdır: kasa
      # yolunda motor deposu (`api` kopyası) eski kanal yazımında, restart'tan ÖNCE yazılır — yani
      # ok:true hangi kanalın okunduğunu SÖYLEMEZ; credential doluluğu `_yeniden_baslat`ta ayrıca ölçüldü.
      case " $donen " in
        *" NOUS_API_KEY "*)
          local nhal; nhal="$(_nous_hali)"
          [ "$nhal" = "OK" ] || olcum_yok "motor /api/secrets/test/nous → $nhal (OK bekleniyordu; --vault NOUS varlık kanıtı)"
          oldu "motor kanıtı: /api/secrets/test/nous ok:true (VARLIK kanıtı — değer-doğruluğu ÖLÇÜLMEDİ, None)" ;;
      esac ;;
    *)
      # TÜKETİCİ KANITI (G3b Task 4): eski yolun AYNI ölçümü — YENİ = kasadaki değerin kanonu, ESKİ = yazım ÖNCESİ kasa
      # değerinin yedeği. Kanıtı olmayan alt komutta eski satır AYNEN (kapsam beyanı `_kasa_kaniti` şerhinde).
      if _kasa_kaniti "$alt" var; then
        adim "kanıt (tüketici): $(_bayrak "$alt") — YENİ değer (kasa) · ESKİ değer (yazım ÖNCESİ kasa yedeği)"
        _kasa_kaniti "$alt" kos "$ISLIK/vault_yeni_kanon" "$YEDEK/vault/$kanit_yol"
      else
        echo "  değer-doğruluğu bu alt komutta ÖLÇÜLMEDİ (None) — kanıt yüzeyi rotasyon yolundadır."
      fi ;;
  esac

  adim "kanıt: envanter eşitlik ölçümü ($(_bayrak "$alt"))"
  _envanter_esitlik "$alt"
  _kanal_beyani "$alt" "$hedefler"
}

#: ROLLBACK DÜŞERSE — YEDEKTEN GERİ KOYMA SATIRI (TSK-237, 2026-09-27). Üç kasa reçetesinin (`_genel_kasa_recetesi` ·
#: `_db_kasa_recetesi` · `_cp_kasa_recetesi`) "rollback düşerse" satırının TEK kaynağı: biçim burada yaşar, reçeteler
#: yalnız bu yardımcıyı çağırır (ayrışma çivisi v568 A1). `_geri_koy_satiri <ad: değer|DSN> <kasa yolu>` → tek satır.
#: NİYE TEK SATIR: yedek 0600 root'tur. Eski satır yolu ve yöntemi yalnız ANLATIYORDU ("STDIN'le: vault kv put …");
#: operatör dosyayı sudo ile okuyup boruya vermeyi ve kasa oturumunu KENDİSİ kurmak zorundaydı — arıza anında yarım
#: kalan reçete, sırrı elle taşıtır. Satır artık A1'de olduğu gibi yapıştırılıp koşulan TEK komuttur (`): `dan sonrası).
#: ORTAM BETİĞİN KENDİSİDİR (uydurma yok): `VAULT_ADDR` (global `export`) · `$VAULT_BIN` (`_vault`) · yönetici jetonu
#: `$VAULT_JETON_DOSYASI`dan `login -no-print -` ile STDIN'den (`_vault_oturum`; `VAULT_TOKEN=` YOK) · oturum yardımcısı
#: geçici bir HOME'a düşer ve trap onu siler (`_vault`un `HOME="$ISLIK"` disiplini — kalıcı yönetici oturumu kalmaz).
#: Değer yedekten `tr -d` ile STDIN'e BORULANIR (`_db_kasa_geri_al`ın yöntemi) — argv'ye GİRMEZ; yedek root 0600 kalır
#: ve `sudo` ile okunur. Değişken parçalar `bash -c`nin KONUMSAL argümanlarıdır (`printf %q`): gövde SABİTTİR ve tek
#: tırnak taşımaz. Yedek yoksa/boşsa YAZIMDAN ÖNCE durur: boru eksik dosyada `tr`ı düşürür ama `kv put` boş STDIN'i yine
#: okur ve kasaya BOŞ değer yazardı (pipefail yalnız çıkış kodunu düzeltir, yazımı geri almaz).
_geri_koy_satiri() {
  local govde='set -euo pipefail; test -s "$4" || { echo "yedek yok/boş: $4" >&2; exit 1; }; '
  govde+='export VAULT_ADDR="$1"; h="$(mktemp -d "${TMPDIR:-/tmp}/sir-geri.XXXXXXXX")"; trap "rm -rf \"$h\"" EXIT; '
  govde+='HOME="$h" "$2" login -no-print - < "$3" > /dev/null; '
  govde+='tr -d "\r\n" < "$4" | HOME="$h" "$2" kv put "$5" value=- > /dev/null; '
  govde+='echo "kasa geri kondu: $5 (yedekteki ESKİ değer, yeni sürüm)"'
  printf "        düşerse (TEK SATIR, root — yedekteki ESKİ %s STDIN'le kasaya; değer argv'ye GİRMEZ): sudo bash -c '%s' _ %q %q %q %q %q\n" \
    "$1" "$govde" "$VAULT_ADDR" "$VAULT_BIN" "$VAULT_JETON_DOSYASI" "$YEDEK/vault/$2" "$2"
}

#: GERİ ALMA REÇETESİ — genel kasa döngüsü (TSK-064 takibi, 2026-09-27; `_db_kasa_recetesi`/`_cp_kasa_recetesi`nin
#: ikizi). NİYE KASA ÖNCE: render hedefi ve yan dosyalar Agent'ındır — kasa YENİ değerdeyken yedekten geri konan
#: dosyayı Agent bir sonraki render'da (`RENDER_ARALIGI`) YENİ değerle EZER; yalnız dosya öneren reçete YANLIŞ
#: güvence verirdi (TSK-226c incelemesi BULGU 1). Eski kanal kopyaları (iki-kanal dönemi) betiğin yazdığı
#: dosyalardır, Agent'ın DEĞİL: onlar yedekten geri konur — kasadan SONRA. Hedef sürüm yazım ÖNCESİ ölçülen
#: `current_version`dır (`_kasa_surumu`); put'u DENENEN her yol listelenir. Değer BASILMAZ.
#: ROLLBACK DÜŞERSE (TSK-064(b), 2026-09-27; db/cp emsali): her rollback satırını o yolun YEDEK YOLU izler — yazım
#: ÖNCESİ kasa değeri `$YEDEK/vault/<yol>`dadır ve STDIN'le `kv put` edilir (argv'de değer YOK); satır TSK-237'den beri
#: üç dalın ortak `_geri_koy_satiri`nin bastığı TEK SATIR komuttur. Satır yalnız yedeği
#: ALINMIŞ yol için vardır: `GENEL_KASA_SATIRLARI`na yol yedekten SONRA girer (`vault_rotasyon`).
_genel_kasa_recetesi() {
  local birimler yol surum hedef hedefler=""
  # sessiz-yutma: `_birimler` bilinmeyen alt komutta `die` eder ve o hata METNİ burada hükme GİRMEZ — burası
  # çıkış yoludur (`_geri_alma_recetesi` şerhi); ÖLÇÜLEMEDİ hâli görünür bir dizgeyle beyan edilir, susmaz.
  birimler="$(_birimler "$ALT" 2>/dev/null || echo '(birim listesi ölçülemedi)')"
  case "$GENEL_KASA_EVRE" in
    yedek)
      echo ">> GERİ ALMA ($(_bayrak "$ALT") --vault): GEREKMEZ — kasaya YAZILMADI, eski kanal YAZILMADI, birim YENİDEN BAŞLATILMADI (yedek: $YEDEK)." >&2 ;;
    kasa)
      {
        echo ">> GERİ ALMA ($(_bayrak "$ALT") --vault — kasaya YENİ değer yazıldı ya da yazımı DENENDİ; başarıda da arızada da geçerli; sıra: ÖNCE kasa, SONRA dosya):"
        echo "     1) kasa (yönetici jetonuyla) — dosyadan ÖNCE: kasa YENİ değerdeyken geri konan dosyayı Agent bir sonraki render'da EZER"
        while IFS=$'\t' read -r yol surum hedef; do
          [ -n "$yol" ] || continue
          echo "        vault kv rollback -version=$surum $yol"
          _geri_koy_satiri değer "$yol"
          hedefler="$hedefler $hedef"
        done <<< "$GENEL_KASA_SATIRLARI"
        echo "     2) render: kasadaki ESKİ değere BİREBİR olana kadar bekle:$hedefler"
        echo "     3) eski kanal: sudo $0 --geri-al $YEDEK   (yedekteki kopyaları bağ İZLEMEDEN geri koyar; render hedefi 1–2 ile kasadan döner)"
        # shellcheck disable=SC2086
        echo "     4) sonra yeniden başlat: $(_recete_birimleri $birimler)"
      } >&2 ;;
  esac
  return 0
}

# =================================================================================================
# KASADAN DB PAROLASI — `--db --vault` (TSK-064; tasarım docs/TASARIM-SIR-DB-KASA-2026-09-21.md)
# =================================================================================================
# NİYE AYRI DAL. Kasa TAM DSN taşır (`secret/meridian/HINDSIGHT_API_DATABASE_URL` → Agent render'ı →
# hindsight-api `LoadCredential`), rotasyonun sırrı ise yalnız PAROLA alanıdır (`HINDSIGHT_DB_PAROLA`)
# ve parolanın İKİNCİ hakikat noktası Postgres rolüdür (`ALTER ROLE` — GERİ ALINAMAZ). İkisi aynı anda
# değişemez; aradaki pencerenin YÖNÜ sonucu belirler (tasarım §2):
#   A) ALTER önce, kasa sonra → render bitene kadar dosyada ESKİ, DB'de YENİ parola; pencere ≥ render
#      aralığıdır ve betiğin kontrolünde DEĞİLDİR. REDDEDİLDİ.
#   B) kasa → render KANITI → ALTER → restart → kanıt. Pencere (dosya YENİ, DB ESKİ) render kanıtı ile
#      ALTER arasındadır ve betiğin kendi kontrolündedir. SEÇİLDİ (Rol-1, değişmez).
# ALTER'dan ÖNCEKİ her adım KV v2 sürümüyle GERİ ALINIR; ALTER restart'ın hemen önündedir. Eski yolun
# (`db`) iki kopyası AYNEN kalır: `url` kopyasını bu yolda Agent yazar (render hedefine elle yazmak
# Agent'la yarışmaktır), `sql` kopyasını betik koşar (`_sql_kos`).
#
# GERİ ALMA YÖNTEMİ — `vault kv rollback -version=<kv put ÖNCESİ current_version>`. Seçim politikadan
# OKUNDU (depodaki üretilmiş `deploy/vault/policies/meridian-admin.hcl`, 2026-09-24; A1'de ÖLÇÜLMEDİ):
# `secret/data/meridian/*` create/read/update + `secret/metadata/meridian/*` read. `rollback` ayrı bir
# yetenek değil, bu üçünün BİLEŞİMİDİR (meta oku → eski sürümü oku → yeni sürüm olarak yaz). Canlıda
# düşerse (politika farklı · sürüm silinmiş) YEDEK YOL ESKİ DSN'i STDIN'den `kv put` eder — tasarım
# §5'in "izin yoksa" yolu: aynı etki, sürüm +1. Hangisi koştuysa ADIYLA basılır; ikisi de düşerse betik
# BAĞIRIR (kasa YENİ, DB ESKİ: hindsight-api bir sonraki restart'ta bağlanamaz).
# "GERİ ALINDI" BEYANI ÖLÇÜLMEDEN BASILMAZ: geri almadan sonra kasadaki değer okunur ve ESKİ DSN'e
# BİREBİR kıyaslanır.
#
# ÖLÇÜLMEYENLER (tasarım §5 — uydurma yasağı): pencere B'nin süresi (koşumda BASILIR, ilk canlı koşum
# belgeye yazar) · hindsight-api havuzunun parola değişince davranışı (bu yüzden restart ZORUNLU).

#: Kasayı ESKİ DSN'e döndürür ve ÖLÇER. 0 = kasadaki değer ESKİ DSN'e BİREBİR (evre `geri`); 1 = iki
#: yol da düştü ya da ölçüm tutmadı — çağıran BAĞIRIR ve evre `kasa` kalır (reçete o hâli anlatır).
_db_kasa_geri_al() {
  if _vault kv rollback -version="$DB_KASA_SURUM" "$DB_KASA_YOL" >/dev/null; then
    DB_GERI_YONTEM="vault kv rollback -version=$DB_KASA_SURUM"
  else
    echo "!! kv rollback DÜŞTÜ ($DB_KASA_YOL -version=$DB_KASA_SURUM) — YEDEK YOL: ESKİ DSN STDIN'le kv put" >&2
    tr -d '\r\n' < "$ISLIK/db_eski_dsn" | _vault kv put "$DB_KASA_YOL" value=- >/dev/null || return 1
    DB_GERI_YONTEM="ESKİ DSN kv put — rollback düştü"
  fi
  ( umask 077; _vault kv get -field=value "$DB_KASA_YOL" > "$ISLIK/db_kasa_simdi" ) || return 1
  py cikar dosya "$ISLIK/db_kasa_simdi" - - "$ISLIK/db_kasa_simdi_kanon" || return 1
  sudo cmp -s "$ISLIK/db_eski_dsn" "$ISLIK/db_kasa_simdi_kanon" || return 1
  DB_KASA_EVRE=geri
  oldu "kasa ESKİ DSN'e geri alındı ($DB_GERI_YONTEM) — kasadaki değer ölçüldü, ESKİ DSN'e BİREBİR"
}

#: Render hedefi ŞU AN beklenen kanona BİREBİR mi — TEK ölçüm, bekleme YOK (geri almadan sonra
#: "dosya hangi DSN'de" sorusunun cevabı; beklemek Agent düşükken tavanı ikinci kez ödemek olurdu).
_render_simdi_esit() {
  sudo test -s "$KOK$1" || return 1
  py cikar dosya "$KOK$1" - - "$ISLIK/vault_render_kanon" || return 1
  sudo cmp -s "$2" "$ISLIK/vault_render_kanon"
}

#: GERİ ALMA REÇETESİ — kasa yolu `--db` (TSK-064). `_geri_alma_recetesi` evre boş değilse BUNU basar:
#: render hedefi Agent'ındır, "yedekten dosyayı geri koy" bir sonraki render'da EZİLİR ve DB rolünü de
#: geri almaz. Adımlar ileri yolun AYNI sırasıdır (kasa → render → ALTER → restart); değer BASILMAZ.
_db_kasa_recetesi() {
  local birim; birim="$(_sir_birimleri HINDSIGHT_DB_PAROLA || echo '(birim listesi ölçülemedi)')"
  case "$DB_KASA_EVRE" in
    yedek)
      echo ">> GERİ ALMA (--db --vault): GEREKMEZ — kasaya YAZILMADI, ALTER ROLE KOŞMADI (yedek: $YEDEK)." >&2 ;;
    kasa)
      echo ">> GERİ ALMA (--db --vault): kasaya YENİ DSN yazıldı ya da yazımı DENENDİ; ALTER ROLE KOŞMADI — DB ESKİ parolada.
     1) kasa: vault kv rollback -version=$DB_KASA_SURUM $DB_KASA_YOL   (yönetici jetonuyla)
$(_geri_koy_satiri DSN "$DB_KASA_YOL")
     2) render hedefi ($DB_KASA_HEDEF) ESKİ DSN'e dönene kadar $birim YENİDEN BAŞLATILMAMALI (dosya YENİ, DB ESKİ)." >&2 ;;
    geri)
      echo ">> GERİ ALMA (--db --vault): kasa ESKİ DSN'e GERİ ALINDI ($DB_GERI_YONTEM; kasadaki değer ölçüldü) ve
     ALTER ROLE UYGULANMADI — DB ESKİ parolada. Ek adım GEREKMEZ; $birim ancak render hedefi
     ($DB_KASA_HEDEF) ESKİ DSN'de iken yeniden başlatılır (yedek: $YEDEK)." >&2 ;;
    alter)
      echo ">> GERİ ALMA (--db --vault — ALTER ROLE UYGULANDI; başarıda da arızada da geçerli; sıra ileri yolun AYNISI):
     1) kasa: vault kv rollback -version=$DB_KASA_SURUM $DB_KASA_YOL   (yönetici jetonuyla)
$(_geri_koy_satiri DSN "$DB_KASA_YOL")
     2) render: $DB_KASA_HEDEF kasadaki ESKİ DSN'e BİREBİR olana kadar bekle
     3) ALTER ROLE $DB_ROL PASSWORD <yedekteki ESKİ DSN'in parolası> — SQL dosyası 0600 + psql -f - (parola argv'ye GİRMEZ)
     4) sudo systemctl restart $birim" >&2 ;;
  esac
  return 0
}

_vault_db_kuru_rapor() {
  local ad="$1" sir="$2" birimler="$3" b satir uc kabul hazirlik=""
  for b in $birimler; do
    if satir="$(_hazir_uc "$b")"; then
      uc="${satir%% *}"; satir="${satir#* }"; kabul="${satir%% *}"
      hazirlik="$hazirlik · hazırlık ${b%.service}: $uc kabul $(_kabul_metni "$kabul"), tavan $(_hazir_tavan "$b") s"
    else
      hazirlik="$hazirlik · ${b%.service}: sağlık ucu YOK, beklenmez"
    fi
  done
  echo "=== KURU KOŞUM: --db --vault (HİÇBİR ŞEY YAZILMADI, KASAYA DOKUNULMADI, ALTER ROLE KOŞMADI) ==="
  echo "  SIRA (tasarım B): kasa → render kanıtı → ALTER ROLE → restart → kanıt — geri alınamayan ALTER restart'ın hemen önünde"
  echo "  1. ön kontrol: kasa oturumu; ESKİ DSN KASADAN okunur (render dosyasından DEĞİL): $DB_KASA_YOL"
  echo "  2. yeni parola: $sir operatörden (ekrana yansımaz; yalnız [A-Za-z0-9_-], ESKİ parolayla AYNI olamaz); boş → bu tur DÖNMEZ, yapacak iş yok → durur"
  _deger_kaynagi_beyani db
  echo "  3. yeni DSN: ESKİ DSN'in YALNIZ parola alanı değişir (kullanıcı/host/port/db/query korunur); ESKİ DSN yedeğe 0600: $KOK/root/sir-yedek-<UTC ts>-db/vault/$DB_KASA_YOL"
  echo "  4. kasaya yazılacak: $DB_KASA_YOL ($sir → $ad); ÖNCE current_version kaydedilir — geri alma: vault kv rollback -version=<o sürüm> (düşerse ESKİ DSN kv put)"
  echo "  5. render kanıtı: $DB_KASA_HEDEF kanonik kopyası kasadaki YENİ DSN'e BİREBİR (tavan $VAULT_RENDER_TAVAN_S s, aralık $VAULT_RENDER_ARALIK_S s) — aşımda ALTER ROLE KOŞMAZ, kasa geri alınır, ÖLÇÜLEMEDİ"
  echo "  6. ALTER ROLE $DB_ROL PASSWORD (SQL dosyası 0600, psql -f -, sonra silinir; parola argv'ye girmez) — düşerse kasa geri alınır, ESKİ DSN render'ı beklenir, durur"
  # shellcheck disable=SC2086
  echo "  7. yeniden başlatılacak: $(_sirala $birimler) — credential doluluğu$hazirlik"
  echo "  8. kanıt: yeni parola select 1 → 1 (uç DSN'den türetilir, PGPASSFILE) · ESKİ parola FATAL (negatif kontrol); düşerse kasa yolunun geri alma reçetesi basılır"
  echo "  ÖN KOŞUL: sudo systemctl stop meridian-tick-watchdog.timer (sonda geri aç)"
  echo "  ÖN KOŞUL: kasa AÇIK (mühürsüz) ve vault-agent AYAKTA olmalı — yoksa render gelmez"
  echo "  yedek dizini: $KOK/root/sir-yedek-<UTC ts>-db"
}

vault_db_rotasyon() {
  local bagli="$1" ad yol hedef sir birincil url_yol birimler uc t_kanit sql="$ISLIK/rol.sql"
  IFS=$'\t' read -r ad yol hedef sir birincil <<< "$bagli"
  # HİZA KAPISI (fail-closed): bağ TEK satır ve takma adsız; kopya tablosunun `url` satırı render
  # hedefinin KENDİSİ; `sql` satırı rolü taşır. v538 Ç6 bunu statik ölçer — burada tekrar, çünkü
  # ayrışma kasaya yazılmış bir DSN'in YANLIŞ dosyada beklenmesi demektir.
  DB_ROL="$(_kopyalar | awk '$1=="db" && $3=="sql" {print $4}')"
  url_yol="$(_kopyalar | awk '$1=="db" && $3=="url" {print $4}')"
  { [ "$(printf '%s\n' "$bagli" | awk 'NF' | wc -l | tr -d ' ')" = 1 ] && [ "$birincil" = "-" ] \
      && [ -n "$DB_ROL" ] && [ "$url_yol" = "$hedef" ]; } \
    || die "--db --vault: envanter ↔ kopya tablosu AYRIŞTI (bağ TEK satır ve takma adsız olmalı; sql rolü
     '$DB_ROL' · url kopyası '$url_yol' · render hedefi '$hedef') — kasaya HİÇBİR ŞEY yazılmadı"
  DB_KASA_YOL="$yol"; DB_KASA_HEDEF="$hedef"
  # Restart listesi gerçek koşum ile kuru planda AYNI yardımcıdan (genel döngüyle tek kaynak).
  birimler="$(_vault_tuketici_birimleri "$yol" "$sir")"
  [ "$KURU" = 0 ] || { _vault_db_kuru_rapor "$ad" "$sir" "$birimler"; return 0; }

  # ---- 1. ÖN KONTROL ----------------------------------------------------------------------------
  adim "1/8 ön kontrol: kasa oturumu + ESKİ DSN KASADAN ($yol — render dosyasından DEĞİL)"
  _vault_oturum
  ( umask 077; _vault kv get -field=value "$yol" > "$ISLIK/db_eski_ham" ) \
    || die "ESKİ DSN kasadan okunamadı: $yol (kasa mühürlü? yol yok?) — kasaya HİÇBİR ŞEY yazılmadı"
  py cikar dosya "$ISLIK/db_eski_ham" - - "$ISLIK/db_eski_dsn"
  uc="$(py dsn-uc "$ISLIK/db_eski_dsn")" \
    || die "kasadaki DSN çözümlenemedi (host/kullanıcı/db) — kasaya HİÇBİR ŞEY yazılmadı"
  oldu "ESKİ DSN kasadan okundu (DEĞER BASILMAZ)"
  # BİLGİ, KAPI DEĞİL: hedef kasadaki DSN'den ayrışıksa Agent kasayı izlemiyor ya da hedef elle yazılmış.
  # Koşum sürer (render adım 5'te ÖLÇÜLÜR) — ama bedel ADIYLA: negatif kontrolün "eski parola FATAL"
  # hükmü bu hâlde ESKİ DSN'in ZATEN geçersiz olmasından da gelebilir.
  if _render_simdi_esit "$hedef" "$ISLIK/db_eski_dsn"; then
    oldu "render hedefi kasadaki ESKİ DSN'e EŞİT: $hedef"
  else
    echo "  !! render hedefi kasadaki ESKİ DSN'e EŞİT DEĞİL (ya da yok): $hedef — Agent kasayı izlemiyor olabilir.
     Devam edilir (render adım 5'te ÖLÇÜLÜR); negatif kontrol ('eski parola FATAL') bu koşumda ZAYIFTIR."
  fi

  # ---- 2. YENİ PAROLA (operatörden — bu yol değeri ÜRETMEZ) ------------------------------------
  adim "2/8 yeni parola: operatörden ($sir)"
  _deger_kaynagi_beyani db
  if ! _oku_gizli "$sir (yeni Postgres parolası — KASADAKİ DSN'e konacak)" "$ISLIK/db_parola"; then
    echo "  · ATLANDI: $sir — değer boş; kasaya YAZILMADI ve bu tur DÖNMEDİ (yürürlükteki parola kalır)"
    die "değer boş — yapacak iş yok (kasaya HİÇBİR ŞEY yazılmadı)"
  fi
  # SQL literali ÖNCE üretilir: alfabe dışı bir parola kasaya yazıldıktan SONRA ALTER'da düşseydi
  # koşum geri alma yoluna girerdi — kapı yazımın ÖNÜNDE.
  py sql-uret "$sql" "$DB_ROL" "$ISLIK/db_parola" \
    || die "yeni parola SQL literaline uygun değil (yalnız [A-Za-z0-9_-]) — kasaya HİÇBİR ŞEY yazılmadı"
  [ "$(py esit url "$ISLIK/db_eski_dsn" - - dosya "$ISLIK/db_parola" - -)" = "AYRI" ] \
    || die "yeni parola ESKİ parolayla AYNI (ya da kıyaslanamadı) — rotasyon değil ve negatif kontrol
     ('eski parola FATAL') ölçülemezdi; kasaya HİÇBİR ŞEY yazılmadı."
  # SAAT ÖN KAPISI (inceleme 2026-09-24): kasa yazımından SONRAKİ ilk saat okuması render beklemesidir;
  # orada düşen saat `olcum_yok` ile ÇIKAR ve kasa kendiliğinden geri ALINMAZ (render tavanı aşımı
  # geri alır, bu yol yalnız el reçetesi basar). Saat burada, hiçbir şey yazılmadan bir kez okunur.
  _saat_oku "kasaya HİÇBİR ŞEY yazılmadı (saat ön kapısı)"

  # ---- 3. YENİ DSN + YEDEK -------------------------------------------------------------------------
  adim "3/8 yeni DSN: ESKİ DSN'in YALNIZ parola alanı değişir; ESKİ DSN yedeğe"
  # Evre yedekten ÖNCE: `_yedek_al` yarıda düşerse reçete dosya kopyası değil "GEREKMEZ" der (hiçbir
  # şey yazılmadı); YEDEK atanmadan düşerse reçete zaten basılmaz (`_geri_alma_recetesi` kapısı).
  DB_KASA_EVRE=yedek
  # `_yedek_al db` yedek dizinini ($YEDEK) kurar ve render hedefinin DİSK kopyasını da alır. Geri
  # almanın girdisi O DEĞİL, aşağıdaki KASA kopyasıdır ($YEDEK/vault/…): Agent geride kaldıysa (adım 1
  # bilgi dalı) ikisi AYRIŞIR ve doğru olan kasa kopyasıdır. Disk kopyası yalnız operatörün elle
  # incelemesi içindir — "Agent o an ne render etmişti" sorusunun kanıtı (inceleme 2026-09-24 KÜÇÜK-1).
  _yedek_al db
  sudo install -d -m 0700 -o root -g root "$YEDEK/vault/$(dirname "$yol")"
  py cikar dosya "$ISLIK/db_eski_dsn" - - "$YEDEK/vault/$yol"
  oldu "yedek: ESKİ DSN (KASADAN) → $YEDEK/vault/$yol (0600 — geri almanın girdisi)"
  py cikar dosya "$ISLIK/db_eski_dsn" - - "$ISLIK/db_yeni_dsn"
  py yaz-url "$ISLIK/db_yeni_dsn" "$ISLIK/db_parola" 0600 -
  [ "$(py dsn-uc "$ISLIK/db_yeni_dsn")" = "$uc" ] \
    || die "yeni DSN'in host/port/kullanıcı/db alanı ESKİ DSN'den AYRIŞTI — kasaya HİÇBİR ŞEY yazılmadı"
  oldu "yeni DSN kuruldu: YALNIZ parola alanı değişti (kullanıcı/host/port/db/query korundu; DEĞER BASILMAZ)"

  # ---- 4. KASA (ÖNCE sürüm kaydı — geri almanın hedefi) -------------------------------------------
  adim "4/8 kasaya yaz: $yol"
  _kasa_surumu "$yol" "HİÇBİR ŞEY yazılmadı"
  DB_KASA_SURUM="$KASA_SURUM"
  # Evre yazımdan ÖNCE `kasa`: put düşse bile kasaya ulaşmış OLABİLİR; reçete bu belirsizliği söyler.
  DB_KASA_EVRE=kasa
  tr -d '\r\n' < "$ISLIK/db_yeni_dsn" | _vault kv put "$yol" value=- >/dev/null \
    || die "kasaya yazılamadı: $yol — ALTER ROLE KOŞMADI, DB'ye DOKUNULMADI (reçete aşağıda)"
  oldu "kasaya yazıldı: $yol (yeni sürüm; DEĞER BASILMAZ)"

  # ---- 5. RENDER KANITI — ALTER bu ölçümden ÖNCE KOŞAMAZ -------------------------------------------
  adim "5/8 render kanıtı: $hedef kasadaki YENİ DSN'e BİREBİR (tavan $VAULT_RENDER_TAVAN_S s)"
  if ! _render_bekle "$hedef" "$ISLIK/db_yeni_dsn"; then
    echo "!! render bekleme aşıldı ($VAULT_RENDER_TAVAN_S s) — ALTER ROLE KOŞMADI; kasa ESKİ DSN'e geri alınıyor" >&2
    _db_kasa_geri_al || die "KASA GERİ ALINAMADI: $yol YENİ DSN'de kaldı (rollback ve yedek yol düştü ya da
     ölçüm tutmadı). ALTER ROLE KOŞMADI — DB ESKİ parolada. Render gelirse dosya YENİ, DB ESKİ olur:
     $(_sir_birimleri "$sir") YENİDEN BAŞLATILMAMALI. Reçete aşağıda."
    _render_simdi_esit "$hedef" "$ISLIK/db_eski_dsn" \
      || echo "!! render hedefi ŞU AN ESKİ DSN'e EŞİT DEĞİL ($hedef) — Agent geri render edene kadar
     $(_sir_birimleri "$sir") YENİDEN BAŞLATILMAMALI (dosya YENİ, DB ESKİ)." >&2
    olcum_yok "render bekleme aşıldı: $hedef ($VAULT_RENDER_TAVAN_S s içinde kasadaki YENİ DSN'e
     eşitlenmedi). ALTER ROLE KOŞMADI — DB'ye DOKUNULMADI; kasa ESKİ DSN'e geri alındı ($DB_GERI_YONTEM).
     Agent render ETMİYOR olabilir: kasa mühürlü · politika eksik · birim düşmüş.
     Bak: systemctl status vault-agent · journalctl -u vault-agent -n 50 --no-pager"
  fi
  _saat_oku; t_kanit="$SAAT_MS"
  oldu "render ÖLÇÜLDÜ: $hedef ($RENDER_GECEN s) — kanonik kopya kasadaki YENİ DSN'le BİREBİR"

  # ---- 6. ALTER ROLE — GERİ ALINAMAZ KANAL, restart'ın hemen önünde -------------------------------
  adim "6/8 ALTER ROLE $DB_ROL (geri alınamaz kanal — restart'ın hemen önünde)"
  if ! _sql_kos "$sql"; then
    sudo rm -f "$sql"
    _db_kasa_geri_al || die "ALTER ROLE başarısız — parola DEĞİŞMEDİ; KASA GERİ ALINAMADI: $yol YENİ DSN'de
     kaldı (rollback ve yedek yol düştü ya da ölçüm tutmadı). Render gelirse dosya YENİ, DB ESKİ olur:
     $(_sir_birimleri "$sir") YENİDEN BAŞLATILMAMALI. Reçete aşağıda."
    if _render_bekle "$hedef" "$ISLIK/db_eski_dsn"; then
      oldu "render ESKİ DSN'e döndü: $hedef ($RENDER_GECEN s)"
    else
      echo "!! render hedefi $VAULT_RENDER_TAVAN_S s içinde ESKİ DSN'e DÖNMEDİ ($hedef) — Agent geri render
     edene kadar $(_sir_birimleri "$sir") YENİDEN BAŞLATILMAMALI (dosya YENİ, DB ESKİ)." >&2
    fi
    die "ALTER ROLE başarısız — parola DEĞİŞMEDİ, kasa geri alındı ($DB_GERI_YONTEM)"
  fi
  DB_KASA_EVRE=alter
  _sql_sil "$DB_ROL" "$sql"
  _gecen_s "$t_kanit"
  oldu "pencere B (render kanıtı → ALTER ROLE): $GECEN_S s — ÖLÇÜLDÜ (tasarım §5; ilk canlı koşum belgeye yazar)"

  # ---- 7. RESTART (ZORUNLU — havuzun parola değişimine davranışı ÖLÇÜLMEDİ) ------------------------
  adim "7/8 tüketici yeniden başlat"
  # shellcheck disable=SC2086
  _yeniden_baslat db $(_sirala $birimler)

  # ---- 8. KANIT (eski `--db` kanıtı AYNEN; negatif kontrolün girdisi KASADAN okunan ESKİ DSN) ------
  adim "8/8 kanıt: yeni parola bağlanır · ESKİ parola bağlanAMAZ"
  _db_kanit "$ISLIK/db_eski_dsn"
  oldu "--db --vault: kasa · render · ALTER ROLE · restart · kanıt — beşi de ÖLÇÜLDÜ"
}

# =================================================================================================
# KASADAN CP ERİŞİM ANAHTARI — `--cp --vault` (TSK-226b, 2026-09-26)
# =================================================================================================
# EMSAL `--tenant --vault` (genel döngü `vault_rotasyon`): kasa-önce yazım · render ölçümü · eski kanal
# kopyalarının KASADAN gelen değerle yazılması · tüketicinin yeniden başlatılması · envanter kanıtı. Aynı
# sıra, aynı yardımcılar (`_vault_oturum` · `_render_bekle` · `_yaz` · `_yeniden_baslat` ·
# `_envanter_esitlik`). NİYE YİNE DE AYRI DAL — üç fark, üçü de bu sırrın kendi gerçeğinden:
#   (1) DEĞER ÜRETİLİR, SORULMAZ. Genel döngü değeri operatörden ister (`_oku_gizli`). Bu sırrın döndürülme
#       sebebi bir GÖRÜNTÜLEME sızıntısıdır (TSK-226: root `docker run` argv'si + bir tanımlama çıktısı) ve
#       yeni değeri bir terminalden/panodan geçirmek aynı sınıfa bir yüzey daha açardı. `_uret hex` —
#       `--tenant`in eski yoluyla aynı sınıf, uzunluk denetimli. Değer hiçbir yere BASILMAZ; CP'ye girişte
#       operatör onu kasadan ya da render hedefinden kendisi okur (bu betiğin işi değil).
#   (2) KANITIN NEGATİF AYAĞI ESKİ DEĞERİ İSTER. CP'nin giriş ucu anahtarı İSTEKTE alır, yani "eski anahtar
#       401" DOĞRUDAN ölçülür (`_cp_kanit`) — genel döngü eski değeri tutmaz ve kanıtı "ÖLÇÜLMEDİ (None)"
#       diye beyan eder. ESKİ değer KASADAN okunur (render dosyasından DEĞİL; `--db --vault` emsali): kasa
#       canlıyken konteynerin etkin değeri yan dosyanın render'ıdır, yani sızan değer de odur.
#   (3) GERİ ALMA EVREYE GÖREDİR. Genel döngünün reçetesi 2026-09-26'da yalnız "yedekten dosyayı geri koy"du ve
#       Agent o dosyayı bir sonraki render'da EZERDİ (TSK-064 takibi 2026-09-27: genel döngü de artık sürümü kaydeder
#       ve kasayı dosyadan ÖNCE geri alır — `_genel_kasa_recetesi`). Buradaki reçete ayrıca eski kanalı ve CP'nin
#       restart'ını EVREYE göre söyler; KV v2 sürümüyle kurulur (`_cp_kasa_recetesi`).
# SIRA: kasa → render kanıtı → eski kanal → restart → kanıt. Render ölçülmeden eski kanal YAZILMAZ ve CP
# YENİDEN BAŞLATILMAZ (genel döngünün ilkesi: kasayı kaynak sanıp ESKİ değeri yaymamak). OTOMATİK GERİ ALMA
# YOK (DB dalından farkı): burada geri alınamaz bir kanal (ALTER ROLE) yoktur; render aşımında konteyner
# ESKİ değerle koşmaya devam eder ve reçete evreyi adıyla söyler.
# YAN DOSYAYA YAZILMAZ: `.env-cp.vault` Agent'ındır ve kanonik kopyayla AYNI şablon turunda render edilir
# (tek aralık, `RENDER_ARALIGI`); kanonik kopyanın render'ı ölçülür, yan dosya kanıtın pozitif ayağında
# (konteyner yeni değeri aldı mı) dolaylı ölçülür.
# ESKİ KANAL YOK (TSK-064 iki-kanal kapanışı, 2026-09-29): `.env-cp` satırı kopya tablosundan çıktı ve CP onu
# okumaz (drop-in 51). Adım 6 ve reçetenin 3. satırı SİLİNMEDİ — kopya tablosundan TÜRER ve bugün "YOK" der:
# numaralı plan (1-8) değişmez, tabloya bir env satırı geri girerse davranış kendiliğinden geri gelir (v590 C8).

#: `_cp_eski_kanal_yok` — kopya tablosunda `cp` env satırı yoksa 0 döner. Adım 6, kuru plan ve reçete AYNI
#: sorudan okur (tek kaynak: üç yerde üç ayrı awk sessizce ayrışırdı).
_cp_eski_kanal_yok() {
  ! _kopyalar | awk '$1=="cp" && $3=="env" {b=1} END{exit !b}'
}
CP_ESKI_KANAL_YOK_METNI="YOK — kopya tablosunda cp env satırı yok (TSK-064 iki-kanal kapanışı 2026-09-29: .env-cp EMEKLİ, CP değeri YALNIZ .env-cp.vault'tan alır)"

#: GERİ ALMA REÇETESİ — kasa yolu `--cp` (`_db_kasa_recetesi`nin ikizi). Değer BASILMAZ; eski kanal yolu
#: kopya tablosundan TÜRETİLİR (ikinci liste yok).
_cp_kasa_recetesi() {
  local birim eski_kanal
  birim="$(_sir_birimleri HINDSIGHT_CP_ACCESS_KEY || echo '(birim listesi ölçülemedi)')"
  # Reçete aracın kendi geri alma yolunu gösterir (TSK-261 — root `cp` hedef bağını izlerdi).
  eski_kanal="$(_kopyalar | awk -v y="$YEDEK" -v b="$0" '$1=="cp" && $3=="env" && !g {printf "sudo %s --geri-al %s", b, y; g=1}')"
  [ -n "$eski_kanal" ] || eski_kanal="$CP_ESKI_KANAL_YOK_METNI — geri konacak dosya yok"
  case "$CP_KASA_EVRE" in
    yedek)
      echo ">> GERİ ALMA (--cp --vault): GEREKMEZ — kasaya YAZILMADI, eski kanal YAZILMADI, $birim YENİDEN BAŞLATILMADI (yedek: $YEDEK)." >&2 ;;
    kasa)
      echo ">> GERİ ALMA (--cp --vault): kasaya YENİ değer yazıldı ya da yazımı DENENDİ; eski kanal YAZILMADI, $birim YENİDEN BAŞLATILMADI (konteyner ESKİ değerde).
     1) kasa: vault kv rollback -version=$CP_KASA_SURUM $CP_KASA_YOL   (yönetici jetonuyla)
$(_geri_koy_satiri değer "$CP_KASA_YOL")
     2) render hedefi ($CP_KASA_HEDEF) kasadaki ESKİ değere dönene kadar $birim YENİDEN BAŞLATILMAMALI (yan dosya YENİ değeri taşıyabilir)." >&2 ;;
    yayim)
      echo ">> GERİ ALMA (--cp --vault — yayım evresi (eski kanal → restart) BAŞLADI; başarıda da arızada da geçerli; sıra ileri yolun AYNISI):
     1) kasa: vault kv rollback -version=$CP_KASA_SURUM $CP_KASA_YOL   (yönetici jetonuyla)
$(_geri_koy_satiri değer "$CP_KASA_YOL")
     2) render: $CP_KASA_HEDEF kasadaki ESKİ değere BİREBİR olana kadar bekle
     3) eski kanal: $eski_kanal
     4) sudo systemctl restart $birim" >&2 ;;
  esac
  return 0
}

_vault_cp_kuru_rapor() {
  local ad="$1" sir="$2" birimler="$3" b satir uc kabul hazirlik="" yd yb
  # TEKİLLEŞTİRİLİR: küme iki kaynağın birleşimidir (yan dosyanın `yeniden_baslat`ı + `_sir_birimleri`) ve
  # CP ikisinde de görünür — ham liste hazırlık satırını İKİ kez basardı (gerçek koşum `_sirala` ile bir kez).
  # shellcheck disable=SC2086
  for b in $(_sirala $birimler); do
    if satir="$(_hazir_uc "$b")"; then
      uc="${satir%% *}"; satir="${satir#* }"; kabul="${satir%% *}"
      hazirlik="$hazirlik · hazırlık ${b%.service}: $uc kabul $(_kabul_metni "$kabul"), tavan $(_hazir_tavan "$b") s"
    else
      hazirlik="$hazirlik · ${b%.service}: sağlık ucu YOK, beklenmez"
    fi
  done
  echo "=== KURU KOŞUM: --cp --vault (HİÇBİR ŞEY YAZILMADI, KASAYA DOKUNULMADI) ==="
  echo "  SIRA: kasa → render kanıtı → eski kanal → restart → kanıt (--tenant --vault akışı; değer üretilir, ESKİ değer kasadan, geri alma evreye göre)"
  echo "  1. ön kontrol: kasa oturumu; ESKİ değer KASADAN okunur (render dosyasından DEĞİL): $CP_KASA_YOL"
  echo "  2. yeni değer: betik İÇİNDE üretilir (openssl rand -hex 32 → 64 karakter, uzunluk denetlenir) — SORULMAZ, BASILMAZ; ESKİ değerle AYNI olamaz"
  echo "  3. yedek: ESKİ değer (KASADAN) 0600 → $KOK/root/sir-yedek-<UTC ts>-cp/vault/$CP_KASA_YOL + kopya tablosundaki dosyalar"
  echo "  4. kasaya yazılacak: $CP_KASA_YOL ($sir → $ad); ÖNCE current_version kaydedilir — geri alma: vault kv rollback -version=<o sürüm>"
  echo "  5. render kanıtı: $CP_KASA_HEDEF kanonik kopyası kasadaki YENİ değere BİREBİR (tavan $VAULT_RENDER_TAVAN_S s, aralık $VAULT_RENDER_ARALIK_S s) — aşımda eski kanal YAZILMAZ, CP YENİDEN BAŞLATILMAZ, ÖLÇÜLEMEDİ"
  while IFS=$'\t' read -r yd yb; do
    echo "    · yan dosya: $yd   (Agent render eder — rotasyon YAZMAZ; yeniden başlat: $yb)"
  done < <(_vault_yan_dosyalari "$CP_KASA_YOL")
  if _cp_eski_kanal_yok; then
    echo "  6. eski kanal: $CP_ESKI_KANAL_YOK_METNI"
  else
    echo "  6. eski kanal (iki-kanal dönemi) AYNI pencerede kasadan gelen değerle yazılır: $(_kopyalar | awk '$1=="cp" && $3=="env" {printf "%s [%s] ", $4, $5}')"
  fi
  # shellcheck disable=SC2086
  echo "  7. yeniden başlatılacak: $(_sirala $birimler)$hazirlik"
  echo "  8. kanıt: POST $CP_KOK/api/auth/login gövde {\"key\": …} — YENİ → 200 · ESKİ → 401/403 (503 = konteynerde anahtar YOK) + envanter eşitliği (--cp)"
  echo "  ÖN KOŞUL: kasa AÇIK (mühürsüz) ve vault-agent AYAKTA olmalı — yoksa render gelmez"
  echo "  yedek dizini: $KOK/root/sir-yedek-<UTC ts>-cp"
}

vault_cp_rotasyon() {
  local bagli="$1" ad yol hedef sir birincil ref_tur ref_yol birimler
  IFS=$'\t' read -r ad yol hedef sir birincil <<< "$bagli"
  # HİZA KAPISI (fail-closed; `--db --vault` emsali): bağ TEK satır ve takma adsız; kopya tablosunun
  # REFERANSI (ilk `cp` satırı) render hedefinin KENDİSİ. Ayrışma, kasaya yazılmış bir değerin YANLIŞ
  # dosyada beklenmesi demektir. v556 A1/A2 aynı hizayı statik ölçer.
  read -r ref_tur ref_yol <<< "$(_kopyalar | awk '$1=="cp" && !y {print $3, $4; y=1}')"
  { [ "$(printf '%s\n' "$bagli" | awk 'NF' | wc -l | tr -d ' ')" = 1 ] && [ "$birincil" = "-" ] \
      && [ "$ref_tur" = dosya ] && [ "$ref_yol" = "$hedef" ]; } \
    || die "--cp --vault: envanter ↔ kopya tablosu AYRIŞTI (bağ TEK satır ve takma adsız olmalı; referans
     '$ref_tur $ref_yol' · render hedefi '$hedef') — kasaya HİÇBİR ŞEY yazılmadı"
  CP_KASA_YOL="$yol"; CP_KASA_HEDEF="$hedef"
  # Restart listesi gerçek koşum ile kuru planda AYNI yardımcıdan (genel döngüyle tek kaynak).
  birimler="$(_vault_tuketici_birimleri "$yol" "$sir")"
  [ "$KURU" = 0 ] || { _vault_cp_kuru_rapor "$ad" "$sir" "$birimler"; return 0; }

  # ---- 1. ÖN KONTROL ----------------------------------------------------------------------------
  adim "1/8 ön kontrol: kasa oturumu + ESKİ değer KASADAN ($yol — render dosyasından DEĞİL)"
  _vault_oturum
  ( umask 077; _vault kv get -field=value "$yol" > "$ISLIK/cp_eski_ham" ) \
    || die "ESKİ değer kasadan okunamadı: $yol (kasa mühürlü? yol yok?) — kasaya HİÇBİR ŞEY yazılmadı"
  py cikar dosya "$ISLIK/cp_eski_ham" - - "$ISLIK/eski"
  grep -q '[^[:space:]]' "$ISLIK/eski" \
    || die "kasadaki ESKİ değer BOŞ: $yol — kanıtın negatif ayağı ölçülemez; kasaya HİÇBİR ŞEY yazılmadı"
  oldu "ESKİ değer kasadan okundu (DEĞER BASILMAZ)"
  # BİLGİ, KAPI DEĞİL (`--db --vault` emsali): hedef kasadaki değerden ayrışıksa Agent kasayı izlemiyor ya da
  # hedef elle yazılmış — render adım 5'te ÖLÇÜLÜR.
  if _render_simdi_esit "$hedef" "$ISLIK/eski"; then
    oldu "render hedefi kasadaki ESKİ değere EŞİT: $hedef"
  else
    echo "  !! render hedefi kasadaki ESKİ değere EŞİT DEĞİL (ya da yok): $hedef — Agent kasayı izlemiyor olabilir.
     Devam edilir (render adım 5'te ÖLÇÜLÜR)."
  fi

  # ---- 2. YENİ DEĞER (betik İÇİNDE — sorulmaz, basılmaz) -----------------------------------------
  adim "2/8 yeni değer: betik İÇİNDE üretilir (--tenant ile aynı sınıf; SORULMAZ, BASILMAZ)"
  _uret hex
  py cikar dosya "$ISLIK/yeni" - - "$ISLIK/yeni_kanon"
  [ "$(py esit dosya "$ISLIK/eski" - - dosya "$ISLIK/yeni" - -)" = "AYRI" ] \
    || die "yeni değer ESKİ değerle AYNI (ya da kıyaslanamadı) — rotasyon değil ve kanıtın negatif ayağı
     ölçülemezdi; kasaya HİÇBİR ŞEY yazılmadı."
  # SAAT ÖN KAPISI (`--db --vault` emsali): kasa yazımından SONRAKİ ilk saat okuması render beklemesidir;
  # orada düşen saat `olcum_yok` ile çıkar. Saat burada, hiçbir şey yazılmadan bir kez okunur.
  _saat_oku "kasaya HİÇBİR ŞEY yazılmadı (saat ön kapısı)"

  # ---- 3. YEDEK ------------------------------------------------------------------------------------
  adim "3/8 yedek: ESKİ değer (KASADAN) + kopya tablosundaki dosyalar"
  # Evre yedekten ÖNCE: `_yedek_al` yarıda düşerse reçete "GEREKMEZ" der; YEDEK atanmadan düşerse reçete
  # zaten basılmaz (`_geri_alma_recetesi` kapısı).
  CP_KASA_EVRE=yedek
  _yedek_al cp
  sudo install -d -m 0700 -o root -g root "$YEDEK/vault/$(dirname "$yol")"
  py cikar dosya "$ISLIK/eski" - - "$YEDEK/vault/$yol"
  oldu "yedek: ESKİ değer (KASADAN) → $YEDEK/vault/$yol (0600 — geri almanın girdisi)"

  # ---- 4. KASA (ÖNCE sürüm kaydı — geri almanın hedefi) ---------------------------------------------
  adim "4/8 kasaya yaz: $yol"
  _kasa_surumu "$yol" "HİÇBİR ŞEY yazılmadı"
  CP_KASA_SURUM="$KASA_SURUM"
  # Evre yazımdan ÖNCE `kasa`: put düşse bile kasaya ulaşmış OLABİLİR; reçete bu belirsizliği söyler.
  CP_KASA_EVRE=kasa
  tr -d '\r\n' < "$ISLIK/yeni" | _vault kv put "$yol" value=- >/dev/null \
    || die "kasaya yazılamadı: $yol — eski kanal YAZILMADI, CP YENİDEN BAŞLATILMADI (reçete aşağıda)"
  oldu "kasaya yazıldı: $yol (yeni sürüm; DEĞER BASILMAZ)"

  # ---- 5. RENDER KANITI — eski kanal ve restart bu ölçümden ÖNCE KOŞAMAZ -----------------------------
  adim "5/8 render kanıtı: $hedef kasadaki YENİ değere BİREBİR (tavan $VAULT_RENDER_TAVAN_S s)"
  _render_bekle "$hedef" "$ISLIK/yeni_kanon" \
    || olcum_yok "render bekleme aşıldı: $hedef ($VAULT_RENDER_TAVAN_S s içinde kasadaki YENİ değere
     eşitlenmedi). ESKİ KANAL YAZILMADI, CP YENİDEN BAŞLATILMADI — konteyner ESKİ değerle koşuyor, kasa
     YENİ değerde (evreli reçete aşağıda). Agent render ETMİYOR olabilir: kasa mühürlü · politika eksik ·
     birim düşmüş. Bak: systemctl status vault-agent · journalctl -u vault-agent -n 50 --no-pager"
  oldu "render ÖLÇÜLDÜ: $hedef ($RENDER_GECEN s) — kanonik kopya kasadaki YENİ değerle BİREBİR"

  # ---- 6. ESKİ KANAL (iki-kanal dönemi; 2026-09-29'dan beri YOK — tablodan türer) -------------------
  # Evre adımın içeriğinden BAĞIMSIZ `yayim`: reçetenin bu evredeki işi restart'ı da kapsar (adım 7).
  CP_KASA_EVRE=yayim
  if _cp_eski_kanal_yok; then
    adim "6/8 eski kanal: $CP_ESKI_KANAL_YOK_METNI"
  else
    adim "6/8 eski kanal (iki-kanal dönemi): kopyalar KASADAN gelen değerle yazılır"
    # YALNIZ `env` satırları: `dosya` satırı render hedefinin kendisidir — Agent'ındır ve az önce ÖLÇÜLDÜ.
    _yaz cp "$sir" "$ISLIK/vault_render_kanon" "env"
  fi

  # ---- 7. RESTART ---------------------------------------------------------------------------------
  adim "7/8 tüketici yeniden başlat"
  # shellcheck disable=SC2086
  _yeniden_baslat cp $(_sirala $birimler)

  # ---- 8. KANIT (CP giriş ucu; negatif ayağın girdisi KASADAN okunan ESKİ değer) --------------------
  adim "8/8 kanıt: CP giriş ucu — YENİ değer 200 · ESKİ değer 401"
  _cp_kanit "$ISLIK/yeni" "$ISLIK/eski"
  _envanter_esitlik cp
  oldu "--cp --vault: kasa · render · eski kanal · restart · kanıt — beşi de ÖLÇÜLDÜ"
  echo "  · yeni değer hiçbir yere BASILMADI; CP girişi için kasadadır ($yol) ve render hedefindedir ($hedef, 0400 root)."
}

# =================================================================================================
# ENVANTER — DEĞER BASMADAN VARLIK + EŞİTLİK
# =================================================================================================
#: BEYANLI KANAL SATIRI — `_kanal_satiri <tur> <sır> <yol>`: `api` (motor API) ve `sql` (ALTER ROLE) kopyaları dosyadan
#: OKUNAMAZ; envanter onları bu TAM satırla beyan eder. TEK KAYNAK (TSK-262 düzeltme turu 2, yeniden inceleme Y2b):
#: `_envanter_esitlik` satırı BUNUNLA basar, `esitle` kanıtı muafiyeti YALNIZ tablonun api/sql satırlarından BUNUNLA kurulan
#: tam satırla tanır — alt dizge ile değil (saldırganın seçtiği bir yol metni ` · motor API ` taşıyınca okunamayan bir kopya
#: satırı muaf sayılıyordu). Başka tür → 1 (çağıran yalnız api/sql için çağırır).
_kanal_satiri() {
  case "$1" in
    api) printf '  %s · motor API %s → OKUNAMADI (yazma kanalı; motor içinden ölçülür)\n' "$2" "$3" ;;
    sql) printf '  %s · ALTER ROLE %s → OKUNAMADI (SQL kanalı; kanıt psql ile ölçülür)\n' "$2" "$3" ;;
    *) return 1 ;;
  esac
}

#: `_beyanli_kanal_satirlari <alt>` — bu alt komutun tablodaki api/sql satırlarının BEKLENEN envanter satırları (`_kanal_satiri`
#: ile, tablodan). Okuyan: `esitle` kanıtının tam satır muafiyeti.
_beyanli_kanal_satirlari() {
  local _a _sr _t _y _r
  while read -r _a _sr _t _y _r; do
    [ "$_a" = "$1" ] || continue
    case "$_t" in
      api|sql) _kanal_satiri "$_t" "$_sr" "$_y" ;;
    esac
  done < <(_kopyalar)
}

_envanter_esitlik() {
  local sadece="${1:-}" _alt sir tur yol alan _m _s onek
  local birinci_tur birinci_yol birinci_alan birinci_onek onceki_sir="" sonuc etiket
  while read -r _alt sir tur yol alan _m _s onek; do
    [ -z "$sadece" ] || [ "$_alt" = "$sadece" ] || continue
    case "$tur" in
      api|sql) _kanal_satiri "$tur" "$sir" "$yol"; continue ;;
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
# `APISIX_ADMIN_KEY`, `HINDSIGHT_CP_ACCESS_KEY`) ve `*_PAROLA` (`PANO_GIRIS_PAROLA`) biçimleri
# sözlüğe UYMAZ; hepsini "beyan dışı kopya" diye bağırmak gerçek bulguyu gürültüde boğardı
# (bedel yasası). Sözlüğe uymayan bir sır adı bu taramaya GÖRÜNMEZ.
# 2026-09-13 DÜZELTME (TSK-064 Faz-1C): `APISIX_ADMIN_KEY` ARTIK bu betiğin döndürdüğü bir sırdır
# (`--apisix-admin`) — ama SÖZLÜK YİNE DE GENİŞLEMEZ ve genişlemesine GEREK de yoktur: tabloya
# girdiği an `_aranan_adlar`ın BİRİNCİ kaynağı (sır KİMLİĞİ) onu zaten görür. Sözlük yalnız
# tablonun HİÇ DUYMADIĞI adlar içindir; tabloya giren her ad ondan bağımsız olarak taranır.
# Yani buradaki "uymuyor" cümlesi bir kapsam boşluğu DEĞİL, iki kaynağın iş bölümüdür.
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
# OKUNAMAYAN DOSYA SUSMAZ (TSK-262): yardımcı bağ · FIFO · aygıt · zincir reddinde `OKUNAMADI (<tür>)` der (okuma yolu bağ
# İZLEMEZ, FIFO'da ASKIDA KALMAZ). Dosya "TARANAMADI" diye BİR kez adlanır ve son satır "YOK" DEMEZ — taranmamış bir dosyayı
# taranmış gibi göstermek "beyan dışı kopya yok" güvencesini uydururdu. Varlık `-e`/`-L` ile sorulur: `test -f` FIFO'yu ve
# sarkık bağı "yok" sayıp SESSİZCE atlıyordu.
_beyan_disi_tara() {
  local dosya alan hal bulundu=0 taranamadi=0
  echo "  --- beyan dışı kopya taraması ---"
  while read -r dosya; do
    sudo test -e "$KOK$dosya" || sudo test -L "$KOK$dosya" || continue
    while read -r alan; do
      # `||` `set -e`e karşı: eski biçim (`[ "$(py …)" = VAR ]`) yardımcının düşüşünde (UTF-8 dışı bayt — `tek`siz biçim
      # traceback'i GÖRÜNÜR bırakır) taramayı sürdürüyordu; atama biçimi koşumu keserdi. Düşüş eskisi gibi bu adı atlar.
      hal="$(py alan-var "$KOK$dosya" "$alan")" || hal="ÖLÇÜLEMEDİ (yardımcı düştü)"
      case "$hal" in
        VAR) ;;
        "OKUNAMADI ("*)
          echo "  !! TARANAMADI: $dosya — $hal (okunmadı: bağ İZLENMEZ, FIFO/aygıt AÇILMAZ; beyan dışı kopya bu dosyada ÖLÇÜLMEDİ)"
          taranamadi=$((taranamadi+1)); break ;;
        *) continue ;;
      esac
      _kopyalar | awk -v d="$dosya" -v a="$alan" '$3=="env" && $4==d && $5==a {b=1} END{exit !b}' && continue
      echo "  !! BEYAN DIŞI KOPYA: $dosya [$alan] — rotasyon bu kopyayı YAZMIYOR"
      bulundu=1
    done < <(_dosya_adaylari "$KOK$dosya")
  done < <(_taranan_dosyalar)
  if [ "$taranamadi" != 0 ]; then
    echo "  !! beyan dışı kopya taraması EKSİK: $taranamadi dosya TARANAMADI (yukarıda) — 'YOK' denemez"
  elif [ "$bulundu" = 0 ]; then
    echo "  beyan dışı kopya YOK"
  fi
}

_secrets_json_tara() {
  local ad hal
  echo "  --- motor sır deposu ($SECRETS_JSON) — yalnız AD, DEĞER OKUNMAZ ---"
  if ! sudo test -e "$KOK$SECRETS_JSON" && ! sudo test -L "$KOK$SECRETS_JSON"; then
    echo "  · dosya YOK: $SECRETS_JSON — bu bir arıza değil, bir BOŞLUK beyanıdır (depo taranmadı)"
    return 0
  fi
  while read -r ad; do
    hal="$(py json-ad-var "$KOK$SECRETS_JSON" "$ad")" || hal="ÖLÇÜLEMEDİ (yardımcı düştü)"   # `set -e` — `_beyan_disi_tara` gibi
    case "$hal" in
      VAR) ;;
      # TSK-262 — okuma REDDİ (bağ · FIFO · aygıt · zincir) susmaz: depo BİR kez "TARANAMADI" diye adlanır (bkz. `_beyan_disi_tara`).
      "OKUNAMADI ("*) echo "  !! TARANAMADI: $SECRETS_JSON — $hal (okunmadı; depodaki adlar ÖLÇÜLMEDİ)"; return 0 ;;
      *) continue ;;
    esac
    if _kopyalar | awk -v a="$ad" '$3=="api" && $2==a {b=1} END{exit !b}'; then
      echo "  $SECRETS_JSON [$ad] → VAR (beyanlı: api kopyası bu depoya yazar)"
    else
      echo "  !! BEYAN DIŞI KOPYA: $SECRETS_JSON [$ad] — rotasyon bu kopyayı YAZMIYOR"
    fi
  done < <(_aranan_adlar)
}

# EMEKLİ KOPYA DENETİMİ (TSK-064 iki-kanal kapanışı, 2026-09-29) — `_emekli_kopyalar` şerhi. Yalnız VARLIK
# (`test -e`): dosya AÇILMAZ, değer okunmaz. Bulgu bir ARIZA değil bir İŞ'tir (operatörün kaldırma adımı) ve
# envanterin çıkış kodunu DEĞİŞTİRMEZ — `_beyan_disi_tara` ile aynı sözleşme: rapor biter, bulgu adıyla basılır.
_emekli_denetle() {
  local y
  echo "  --- emekli kopyalar (rotasyon YAZMAZ, okuyucusu YOK — yalnız VARLIK, DEĞER OKUNMAZ) ---"
  while read -r y; do
    [ -n "$y" ] || continue
    if sudo test -e "$KOK$y"; then
      echo "  !! EMEKLİ KOPYA HÂLÂ VAR: $y — rotasyon YAZMIYOR, okuyucusu YOK; yedekle + kaldır (deploy/oracle-a1/RUNBOOK.md son bölüm)"
    else
      echo "  emekli kopya: $y → YOK (kaldırılmış)"
    fi
  done < <(_emekli_kopyalar)
}

envanter() {
  echo "=== SIR KOPYA ENVANTERİ (yalnız VARLIK ve EŞİTLİK; DEĞER ve HASH BASILMAZ) ==="
  _envanter_esitlik
  echo "  --- oneshot tüketiciler (restart kümesi DIŞI — sonraki tetikte okur) ---"
  local _oneshot_satir
  _oneshot_satir="$(_oneshot_yazdir)"
  # `_beyan_disi_tara`daki "YOK" satırıyla AYNI kalıp: tablo BUGÜN boş olabilir (henüz hiçbir
  # oneshot LoadCredential drop-in'i yok) ve bu bir arıza değil, bir DURUM beyanıdır.
  if [ -n "$_oneshot_satir" ]; then echo "$_oneshot_satir"; else echo "  oneshot tüketici YOK"; fi
  _beyan_disi_tara
  _emekli_denetle
  _secrets_json_tara
  echo "  --- yedekler (/root/sir-yedek-*) ---"
  _yedekleri_listele
}

# =================================================================================================
# EŞİTLEME — AYRI DÜŞMÜŞ KOPYAYI REFERANSA TAŞI (`--<alt> --esitle`; TSK-181, 2026-09-13)
# =================================================================================================
# NİYE VAR. Rotasyon YALNIZ yeni değerle yazar (`--openrouter` iki anahtarı operatörden ister).
# 09-08 rotasyonu GLOBAL `/home/ubuntu/.hermes/.env` kopyasını ATLADI (tabloda yoktu); kopya
# 09-13'te tabloya girdi ama "var olan referansı bu kopyaya taşı" işi için yol YOKTU: ya operatör
# yeni bir anahtar üretip 15 kopyayı yeniden döndürecek (karşılıksız rotasyon + eski anahtar
# iptali), ya da biri değeri ELLE kopyalayacaktı — ve Rol-1 A1'de sır DEĞERİ taşıyan hiçbir komut
# koşamaz (sınıflandırıcı üç kez kapattı; kalıcı kayıt `loadcredential-kanali`). Bu betik koşar,
# komut değer taşımaz. Eşitleme, betiğin var olma gerekçesindeki "unutulan kopya" sınıfının
# ONARIMIDIR: değer ne üretilir, ne sorulur, ne basılır — referans kopyadan (sırrın tablodaki İLK
# satırı) OKUNUR, AYRI olanlara YAZILIR, envanter yeniden ölçülür.
# KAPSAM: `dosya`/`env`/`url` kopyaları. `api` (motor deposu) ve `sql` (ALTER ROLE) kanalları
# okunamaz → karşılaştırılamaz → BEYANLA atlanır (o kanalların değeri rotasyon yoluyla yazılır).
# RESTART YOK: tablo hangi DOSYANIN hangi BİRİM tarafından okunduğunu bilmez (satır = dosya, birim
# değil); sırrın tüketici birimleri BASILIR, yeniden başlatma kararı operatörün/Rol-1'in. Bugünkü
# vakada tüketici hermes CLI'dır (timer'sız, her çağrıda dosyayı okur — restart gerekmez).
# KANIT: (1) `_envanter_esitlik <alt>` → AYRI satır KALMAMALI (kalırsa çıkış 2). (2) `--openrouter`
# için kapı `chat/completions` 200+choices: referansın UPSTREAM'de geçerli olduğu — kapı referans
# kopyayı okur; referans geçersizse eşitleme KÖTÜ bir değeri yaymıştır ve çıkış 2 + geri alma
# reçetesi (yedek alındı) bunu SÖYLER. Diğer alt komutlarda değer-doğruluğu eşitlemeyle ÖLÇÜLMEZ
# (None) ve satır bunu beyan eder — kanıt yüzeyi rotasyon yolundadır.
# İKİ GEÇİŞ: ilk geçiş yalnız ÖLÇER (kuru koşum burada biter), ikinci geçiş yalnız AYRI'yı yazar.
esitle() {
  local alt="$1" _alt sir tur yol alan mod sahip onek etiket sonuc onceki=""
  local ref_tur ref_yol ref_alan ref_onek n_ayri=0 n_esit=0 n_atlanan=0 sirlar=""
  echo "=== EŞİTLEME: $(_bayrak "$alt") (referans kopya → AYRI kopyalar; DEĞER üretilmez, sorulmaz, BASILMAZ) ==="
  while read -r _alt sir tur yol alan mod sahip onek; do
    [ "$_alt" = "$alt" ] || continue
    etiket=""; [ "$alan" = "-" ] || etiket=" [$alan]"
    if [ "$sir" != "$onceki" ]; then
      onceki="$sir"
      case "$tur" in api|sql) die "referans kopya okunamayan kanalda: $sir ($tur) — tablo sırası bozuk" ;; esac
      sonuc="$(py var "$tur" "$KOK$yol" "$alan")"
      [ "$sonuc" = "VAR" ] || die "referans kopya $sonuc: $yol$etiket ($sir) — eşitleme KAYNAĞI yok, yazım YAPILMADI"
      ref_tur="$tur"; ref_yol="$yol"; ref_alan="$alan"; ref_onek="$onek"
      echo "  $sir · $yol$etiket → REFERANS"
      continue
    fi
    case "$tur" in
      api|sql) echo "  $sir · $yol → ATLANDI ($tur kanalı okunamaz; eşitleme kapsam dışı — rotasyon yolu yazar)"
               n_atlanan=$((n_atlanan+1)); continue ;;
    esac
    sonuc="$(py esit "$ref_tur" "$KOK$ref_yol" "$ref_alan" "$ref_onek" "$tur" "$KOK$yol" "$alan" "$onek")"
    case "$sonuc" in
      "EŞİT") n_esit=$((n_esit+1)); echo "  $sir · $yol$etiket → EŞİT (dokunulmaz)" ;;
      AYRI)   n_ayri=$((n_ayri+1)); echo "  $sir · $yol$etiket → AYRI → YAZILACAK"
              case " $sirlar " in *" $sir "*) ;; *) sirlar="$sirlar $sir" ;; esac ;;
      *)      die "kopya $sonuc: $yol$etiket ($sir) — eşitleme yarım kalırdı, yazım YAPILMADI" ;;
    esac
  done < <(_kopyalar)
  echo "  ölçüm: $n_esit eşit · $n_ayri ayrı · $n_atlanan kapsam dışı"
  if [ "$n_ayri" = 0 ]; then
    oldu "AYRI kopya YOK — yapacak iş yok (yedek alınmadı, hiçbir şey yazılmadı)"; return 0
  fi
  if [ "$KURU" != 0 ]; then
    echo "  KURU KOŞUM: $n_ayri kopya yazılırdı — HİÇBİR ŞEY YAZILMADI"; return 0
  fi
  _yedek_al "$alt"
  # 2. GEÇİŞ — yazım: YALNIZ AYRI satırlar. Değer referanstan işlik dosyasına çıkarılır (0600 root,
  # argv'ye girmez) ve satır `_yaz_satir` ile rotasyonla AYNI yoldan yazılır.
  onceki=""
  while read -r _alt sir tur yol alan mod sahip onek; do
    [ "$_alt" = "$alt" ] || continue
    if [ "$sir" != "$onceki" ]; then
      onceki="$sir"; ref_tur="$tur"; ref_yol="$yol"; ref_alan="$alan"; ref_onek="$onek"
      py cikar "$ref_tur" "$KOK$ref_yol" "$ref_alan" "$ref_onek" "$ISLIK/ref_$sir"
      continue
    fi
    case "$tur" in api|sql) continue ;; esac
    sonuc="$(py esit "$ref_tur" "$KOK$ref_yol" "$ref_alan" "$ref_onek" "$tur" "$KOK$yol" "$alan" "$onek")"
    [ "$sonuc" = "AYRI" ] || continue
    _yaz_satir "$sir" "$tur" "$yol" "$alan" "$mod" "$sahip" "$onek" "$ISLIK/ref_$sir"
  done < <(_kopyalar)
  adim "kanıt 1: envanter yeniden ölçümü ($(_bayrak "$alt"))"
  local rapor; rapor="$(_envanter_esitlik "$alt")"
  echo "$rapor"
  if printf '%s\n' "$rapor" | grep -q "→ AYRI"; then
    olcum_yok "eşitleme sonrası hâlâ AYRI kopya var (yukarıda) — yedek: $YEDEK"
  fi
  # "AYRI YOK" ≠ "EŞİT" (TSK-262 düzeltme turu 1, inceleme M3): kanıt yalnız `→ AYRI` arıyordu; okunamayan bir kopya (`OKUNAMADI
  # (<tür>)` — ikinci geçişten önce FIFO/bağa çevrilmiş, hiç YAZILMAMIŞ) ya da referansı okunamayan kopyalar (`REFERANS OKUNAMADI`)
  # "EŞİT" sayılıyor ve araç YANLIŞ BAŞARI beyan ediyordu (çıkış 0). Şimdi referans satırı `VAR`, öteki her kopya satırı `EŞİT`
  # olmalıdır; değilse ÖLÇÜLEMEDİ (çıkış 2 — aracın ölçülemedi sınıfı). Beyanlı kanallar (`motor API` · `ALTER ROLE`) eşitlemenin
  # kapsamı DIŞIDIR ve `_envanter_esitlik` onları "OKUNAMADI (… kanalı …)" diye BEYANLA basar — sayılmaz. Çivi: v613 F3.
  # MUAFİYET TAM SATIRDIR (düzeltme turu 2, yeniden inceleme Y2b): eskiden ` · motor API ` / ` · ALTER ROLE ` satırın HERHANGİ
  # bir yerinde aranıyordu; okunamayan bir kopyanın hükmüne giren saldırgan yol metni (ZİNCİR realpath iletisi) bu dizgeyi taşıyınca
  # satır muaf, kanıt "EŞİT" oluyordu (v613 F4). Beklenen beyanlı satırlar TABLODAN (`_kopyalar` — bu alt komutun api/sql satırları)
  # ve envanterin KENDİ biçimleyicisiyle (`_kanal_satiri`) kurulur; satır ancak BİREBİR eşitse muaftır (`grep -xF`).
  local _s olcemeyen=0 kanallar
  kanallar="$(_beyanli_kanal_satirlari "$alt")"
  while IFS= read -r _s; do
    case "$_s" in
      ""|*" → VAR (referans kopya)"|*" → EŞİT") continue ;;
    esac
    if [ -n "$kanallar" ] && printf '%s\n' "$kanallar" | grep -qxF -- "$_s"; then continue; fi
    olcemeyen=$((olcemeyen+1))
  done <<< "$rapor"
  [ "$olcemeyen" = 0 ] || olcum_yok "eşitleme sonrası $olcemeyen satır EŞİT DEĞİL ve AYRI da değil (yukarıda — okunamadı / yok /
     referans okunamadı): kopyalar EŞİT DENEMEZ — yeniden ölç: sudo $0 --envanter; yedek: $YEDEK"
  oldu "envanter: $(_bayrak "$alt") kopyaları EŞİT"
  echo "  yeniden başlatma YAPILMADI (eşitleme sözleşmesi). Yazılan sırların tüketici birimleri:"
  # shellcheck disable=SC2046
  for sir in $sirlar; do echo "    · $sir → $(_recete_birimleri $(_sir_birimleri "$sir"))"; done
  echo "    (yazılan kopya bir birimin okuduğu dosyaysa o birim yeniden başlatılmalı; timer'lı oneshot ve"
  echo "     hermes CLI sonraki çağrıda okur — TSK-181 vakası: /home/ubuntu/.hermes/.env → hermes CLI, restart yok)"
  case "$alt" in
    openrouter)
      adim "kanıt 2: referans değer upstream'de geçerli mi (kapı chat/completions)"
      _model_gerekli
      local hal; hal="$(_kapi_chat_hali)"
      [ "$hal" = "OK" ] || olcum_yok "kapı chat/completions → $hal (OK bekleniyordu) — REFERANS upstream'de geçersiz olabilir; eşitleme KÖTÜ bir değeri yaymış olabilir, yedekten geri al (bağ İZLEMEDEN): sudo $0 --geri-al $YEDEK"
      oldu "kapı kanıtı: chat/completions 200 · gövdede choices (referans değer upstream'de GEÇERLİ)" ;;
    *) echo "  değer-doğruluğu bu alt komutta eşitlemeyle ÖLÇÜLMEZ (None) — kanıt yüzeyi rotasyon yolundadır ($(_bayrak "$alt"))." ;;
  esac
}

# =================================================================================================
# TOHUMLAMA — BOT AĞ GEÇİDİNİN SOHBET `.env`LERİNİN İLK YAZIMI (`--tohumla-sohbet`; G3b Task 4, 2026-10-01)
# =================================================================================================
# NİYE VAR. `_yaz_satir env` bir `.env` KURAMAZ (satırın DEĞERİNİ yazar) ve ön-denetim (`_hedef_on_denetim`) hedef yokken
# her rotasyonu yazımdan ÖNCE durdurur. Sohbet `.env`leri A1'de BUGÜN YOK (ölçüldü 2026-09-30): A0 dizinleri kurar ama `.env`e
# dokunmaz (v601). İlk dosyayı kuran tek yol budur — operatör kararı K-G3b-2 "araç oluştursun": YOKSA oluşturur, VARSA
# dokunmaz; değer ekrana, argv'ye ya da log'a düşmez. ROTASYON DEĞİLDİR: değer üretmez, sormaz, kasaya yazmaz, eşitlemez
# (`--vault`/`--esitle`/`--uret` ile ayrıştırmada reddedilir).
# KÜME TABLODAN TÜRER — ikinci liste YOK (tek-kaynak; v604 D9): hedefler = `_kopyalar`ın `$_SOHBET_KOKU/` altına yazan `env`
# satırları; her hedefin alanları = o yola yazan satırların alanları; her alanın değeri = sırrının tablodaki REFERANS satırı
# (İLK satır — `esitle` emsali), `py cikar` ile 0600 işlik dosyasına çıkarılır ve yardımcıya YALNIZ YOLU verilir. Tabloya
# yeni bir sohbet satırı girdiği an tohumlama onu da yazar.
# SIRA (operatör reçetesi, deploy/oracle-a1/RUNBOOK.md G3b): A0 site.yml (dizinler, 0700 ubuntu) → kasaya ilk değer + Agent
# render (referanslar) → BU → ilk rotasyon.
# KAPILAR, hepsi HİÇBİR yazımdan ÖNCE: (0) tablo biçimi (önek yok · referans sohbet kökünün DIŞINDA · aynı alana tek satır);
# (1) her hedef DİZİNİ VAR ve GÜVENLİ — `py dizin-denetle`: zincir `$_SOHBET_KOKU`dan aşağı bağ İZLENMEDEN açılır, her bileşen
# bağ değil · dizin · grup/diğer yazamaz · sahibi ubuntu (root iken) · realpath beklenen yol (dal sonu M1, CWE-59); YOK ya da
# RED → DUR: araç dizin AÇMAZ (`_dizin_hazirla` root sahipli açardı, hermes evinde yanlış; dizin A0'ın işidir) ve bağı izleyip
# ağacın DIŞINA yazmaz; (2) her REFERANS VAR — yoksa ya da BOŞsa DUR (değer uydurulmaz; ilk değer RUNBOOK borusuyla kasaya,
# Agent render eder); (3) her referans TEK satırlık dolu bir değer (yalnız boşluk/çok satır `.env`e yazılamaz — v604 D4).
# YAZIM: YOK olan hedef `py tohumla-env` ile — 0600 ubuntu:ubuntu, `KEY=değer` satırları; zincir yazım anında YENİDEN bağ
# izlenmeden açılır, geçici dosya dizin tanıtıcısına göre `O_EXCL|O_NOFOLLOW`, sahip/mod tanıtıcıya (`fchown`/`fchmod`),
# `os.link(follow_symlinks=False)` (hedef VARSA reddeder: yarışı İKİNCİ katman kapatır), sonra `lstat` ile AYNI inode · normal
# dosya · 0600 · sahip (root iken) ÖLÇÜLÜR ve hüküm satıra yazılır. VAR olan hedefe DOKUNULMAZ (içerik, mtime, mod, sahip);
# eksik / değersiz (BOŞ — dal sonu M2) / çift alanı ADIYLA söylenir ve YAZILMAZ — var olan dosyayı düzeltmek operatörün elidir
# (rotasyon da o dosyayı ön-denetimde durdurur). Sembolik bağ ya da normal olmayan hedef OKUNMAZ, sebebiyle ÖLÇÜLEMEDİ (M4).
# Özet `yazıldı N · dokunulmadı M · eksik alanlı K` (K ⊆ M); K > 0 → çıkış 3 (operatör reçetesi elle inceleme ister);
# ÖLÇÜLEMEYEN VAR hedef → çıkış 2 (sebep hedef başına).
# RESTART YOK: birimler etkin değil (G3c) ve tohumlanan değer referansla AYNIDIR. YEDEK YOK: yazılan her dosya YOKTU.
# Çiviler: v604 D1–D11.
_tohum_plani() {
  # `<hedef>\t<alan>\t<sır>\t<ref tür>\t<ref yol>\t<ref alan>\t<ref önek>\t<önek>\t<alt>` — referans sırrın İLK satırı
  # (satırlar BİTİŞİK — REFERANS KURALI). awk tablonun TAMAMINI okur (erken çıkış YOK — TABLO BORUSU şerhi).
  _kopyalar | awk -v k="$_SOHBET_KOKU/" '
    $2 != s { s = $2; rt = $3; ry = $4; ra = $5; ro = $8 }
    $3 == "env" && index($4, k) == 1 { print $4 "\t" $5 "\t" $2 "\t" rt "\t" ry "\t" ra "\t" ro "\t" $8 "\t" $1 }'
}

tohumla_sohbet() {
  local plan hedefler refs yol alan sir rt ry ra ro onek _alt d dizinler="" hal etiket alanlar
  local eksik cift bos okunamaz sorun dizin_yok="" dizin_red="" ref_yok="" n=0 m=0 k=0 o=0 elle="" olcemedi="" dogrulama
  echo "=== TOHUMLAMA: --tohumla-sohbet (sohbet .env'leri — alan kümesi KOPYA TABLOSUNDAN; DEĞER BASILMAZ) ==="
  [ "$KURU" = 0 ] || echo "  KURU KOŞUM — HİÇBİR ŞEY YAZILMAZ (dosya, dizin, yedek)"
  plan="$(_tohum_plani)"
  [ -n "$plan" ] || die "tohumlama planı BOŞ: kopya tablosunda $_SOHBET_KOKU/ altına yazan env satırı YOK — HİÇBİR ŞEY yazılmadı"
  # (0) BİÇİM — bugünkü tablo bu biçimdedir; değişirse araç SESSİZCE yanlış yazmaz, durur.
  while IFS=$'\t' read -r yol alan sir rt ry ra ro onek _alt; do
    [ "$onek" = "-" ] || die "tohumlama önekli satırı desteklemez: $yol [$alan] önek=$onek — tablo değişti, araç güncellenmeli. HİÇBİR ŞEY yazılmadı"
    case "$ry" in
      "$_SOHBET_KOKU"/*) die "referans sohbet kökünün İÇİNDE: $sir → $ry — tohumlama kendi hedefinden okuyamaz (tablo sırası bozuk). HİÇBİR ŞEY yazılmadı" ;;
    esac
    case "$rt" in dosya|env|url) ;; *) die "referans okunamayan kanalda: $sir ($rt) — HİÇBİR ŞEY yazılmadı" ;; esac
  done <<< "$plan"
  cift="$(printf '%s\n' "$plan" | awk -F'\t' 'g[$1 FS $2]++ {print $1 " [" $2 "]"}')"
  [ -z "$cift" ] || die "aynı hedefin aynı alanına İKİ tablo satırı yazıyor: $cift — tablo bozuk. HİÇBİR ŞEY yazılmadı"
  hedefler="$(printf '%s\n' "$plan" | awk -F'\t' '!g[$1]++ {print $1}')"
  refs="$(printf '%s\n' "$plan" | awk -F'\t' '!g[$3]++ {print $3 "\t" $4 "\t" $5 "\t" $6 "\t" $7}')"

  # (1) DİZİNLER — araç dizin AÇMAZ ve dizin bağı İZLEMEZ (G3b dal sonu M1, CWE-59): zincir KÖKTEN (`$_SOHBET_KOKU`) aşağı
  # `py dizin-denetle` ile — yazımın (`tohumla-env`) koşacağı AYNI denetim (bağ değil · dizin · grup/diğer yazamaz · sahip
  # ubuntu [root iken] · realpath beklenen yol). Biri YOK ya da RED ise HİÇBİR dosya yazılmaz.
  for yol in $hedefler; do
    d="$(dirname "$yol")"
    case " $dizinler " in *" $d "*) continue ;; esac
    dizinler="${dizinler:+$dizinler }$d"
    # `||` ADLANDIRMADIR: yardımcının düşüşü RED olarak aşağıda durdurur.
    hal="$(py dizin-denetle "$KOK$_SOHBET_KOKU" "$KOK$d" ubuntu ubuntu)" || hal="RED: denetim yardımcısı düştü"
    case "$hal" in
      TAMAM) echo "  dizin: $d → VAR (bağ yok · grup/diğer yazamaz · sahip ubuntu)" ;;
      TAMAM*) etiket="${hal#TAMAM (}"; echo "  dizin: $d → VAR (bağ yok · grup/diğer yazamaz · ${etiket%)})" ;;
      YOK)    echo "  dizin: $d → YOK"; dizin_yok="${dizin_yok:+$dizin_yok }$d" ;;
      *)      echo "  dizin: $d → REDDEDİLDİ (${hal#RED: })"; dizin_red="$dizin_red!! dizin REDDEDİLDİ: $d — ${hal#RED: }"$'\n' ;;
    esac
  done
  if [ -n "$dizin_yok$dizin_red" ] && [ "$KURU" = 0 ]; then
    for d in $dizin_yok; do echo "!! dizin YOK: $d" >&2; done
    printf '%s' "$dizin_red" >&2
    die "--tohumla-sohbet: hedef dizini YOK ya da REDDEDİLDİ (yukarıda) — YOK ise önce A0 site.yml (.hermes-botlar dizinlerini
     0700 ubuntu kurar); REDDEDİLDİ ise dizini elle incele (sembolik bağ · izin · sahip — A0 site.yml düzeltir, bağı İZLEMEZ).
     Araç dizin AÇMAZ ve bağ İZLEMEZ: hedef ağacın dışına yazmak / root sahipli dizin yanlış olurdu. HİÇBİR ŞEY yazılmadı."
  fi

  # (2) REFERANSLAR — değer okunmaz, yalnız VAR/YOK (`py var`).
  while IFS=$'\t' read -r sir rt ry ra ro; do
    etiket=""; [ "$ra" = "-" ] || etiket=" [$ra]"
    # `||` bir YUTMA değil ADLANDIRMADIR: yardımcının düşüşü VAR olmayan referans olarak aşağıda durdurur.
    hal="$(py var "$rt" "$KOK$ry" "$ra")" || hal="ÖLÇÜLEMEDİ (yardımcı düştü)"
    echo "  referans: $sir · $ry$etiket → $hal"
    [ "$hal" = "VAR" ] || ref_yok="$ref_yok!! referans $hal: $ry$etiket ($sir)"$'\n'
  done <<< "$refs"
  if [ -n "$ref_yok" ] && [ "$KURU" = 0 ]; then
    printf '%s' "$ref_yok" >&2
    die "--tohumla-sohbet: referans YOK/boş (yukarıda) — önce kasaya değer + Vault Agent render (RUNBOOK: ilk değer
     borusu); değer UYDURULMAZ. HİÇBİR ŞEY yazılmadı."
  fi

  # (3) DEĞERLER — işliğe (0700) çıkarılır, TEK satır + dolu olmaları YAZIMDAN ÖNCE ölçülür. Kuru koşum değer okumaz.
  if [ "$KURU" = 0 ]; then
    while IFS=$'\t' read -r sir rt ry ra ro; do
      py cikar "$rt" "$KOK$ry" "$ra" "$ro" "$ISLIK/ref_$sir"
      sudo awk 'NF { d++ } END { exit !(NR == 1 && d == 1) }' "$ISLIK/ref_$sir" \
        || die "referans TEK satırlık dolu bir değer değil: $ry ($sir) — .env'e yazılamaz (boş değer ya da satır
     enjeksiyonu). HİÇBİR ŞEY yazılmadı (DEĞER BASILMAZ)."
    done <<< "$refs"
  fi

  # (4) HEDEFLER — YOK olan yazılır, VAR olana dokunulmaz.
  for yol in $hedefler; do
    alanlar="$(printf '%s\n' "$plan" | awk -F'\t' -v h="$yol" '$1 == h {printf "%s%s", (n++ ? " " : ""), $2}')"
    if sudo test -e "$KOK$yol" || sudo test -L "$KOK$yol"; then
      m=$((m+1)); eksik=""; cift=""; bos=""; okunamaz=""
      # SEMBOLİK BAĞ ya da NORMAL DOSYA DEĞİL (G3b dal sonu M4): içerik OKUNMAZ (bağ izlenmez) ve sebep ADIYLA söylenir —
      # sarkık bir bağ eskiden alan okumasında "DOSYA YOK" verip son iletide "izin ya da UTF-8" diye yanlış adlanıyordu.
      if sudo test -L "$KOK$yol"; then
        if sudo test -e "$KOK$yol"; then okunamaz="SEMBOLİK BAĞ (izlenmez — hedefi okunmadı)"
        else okunamaz="SEMBOLİK BAĞ (sarkık — hedefi YOK; izlenmez)"; fi
      elif ! sudo test -f "$KOK$yol"; then
        okunamaz="normal dosya değil"
      else
        for alan in $alanlar; do
          # `||` ADLANDIRMADIR (yukarıdaki gibi): düşüş ÖLÇÜLEMEDİ kovasına gider. `dolu`: değersiz/boşluk alan EKSİKtir (M2).
          hal="$(py alan-var "$KOK$yol" "$alan" tek dolu)" || hal="ÖLÇÜLEMEDİ (yardımcı düştü)"
          _alt="$(printf '%s\n' "$plan" | awk -F'\t' -v h="$yol" -v a="$alan" '$1 == h && $2 == a {print $9}')"
          case "$hal" in
            VAR) ;;
            "ALAN YOK") eksik="${eksik:+$eksik, }$alan"
                        elle="$elle     $yol: değersiz '$alan=' satırı ekle → sudo ./sir_rotasyon.sh $(_bayrak "$_alt") --esitle"$'\n' ;;
            BOŞ) bos="${bos:+$bos, }$alan"
                 elle="$elle     $yol: '$alan=' satırı DEĞERSİZ — değeri referanstan: sudo ./sir_rotasyon.sh $(_bayrak "$_alt") --esitle"$'\n' ;;
            "ÇİFT SATIR"*) cift="${cift:+$cift, }$alan"
                           elle="$elle     $yol: '$alan=' satırlarını TEK satıra indir"$'\n' ;;
            *) okunamaz="${okunamaz:+$okunamaz, }$alan ($hal)" ;;
          esac
        done
      fi
      sorun=""
      [ -z "$eksik" ] || sorun="eksik: $eksik"
      [ -z "$bos" ] || sorun="${sorun:+$sorun · }boş: $bos"
      [ -z "$cift" ] || sorun="${sorun:+$sorun · }çift: $cift"
      [ -z "$okunamaz" ] || sorun="${sorun:+$sorun · }ÖLÇÜLEMEDİ: $okunamaz"
      [ -z "$eksik$bos$cift" ] || k=$((k+1))
      if [ -n "$okunamaz" ]; then o=$((o+1)); olcemedi="$olcemedi     $yol: $okunamaz"$'\n'; fi
      if [ -z "$sorun" ]; then sorun="alanlar tam"; fi
      if [ "$KURU" = 0 ]; then
        echo "  hedef: $yol → VAR ($sorun) — dokunulmadı"
      else
        echo "  hedef: $yol → VAR ($sorun) — dokunulmayacak"
      fi
      continue
    fi
    n=$((n+1))
    if [ "$KURU" != 0 ]; then
      echo "  hedef: $yol → YOK — yazılacak alanlar: $alanlar (0600 ubuntu:ubuntu)"
      continue
    fi
    # Argümanlar YALNIZ alan ADI ve değer dosyasının YOLU — değer argv'ye GİRMEZ (v604 D7).
    set --
    for alan in $alanlar; do
      sir="$(printf '%s\n' "$plan" | awk -F'\t' -v h="$yol" -v a="$alan" '$1 == h && $2 == a {print $3}')"
      set -- "$@" "$alan" "$ISLIK/ref_$sir"
    done
    # Kök: zincir denetimi yazım anında YENİDEN koşar (ikinci katman — (1)'den beri değişmiş olabilir). stdout = doğrulama hükmü.
    dogrulama="$(py tohumla-env "$KOK$_SOHBET_KOKU" "$KOK$yol" 0600 ubuntu ubuntu "$@")"
    oldu "yazıldı: $yol (0600 ubuntu:ubuntu istendi; $dogrulama; alanlar: $alanlar — değer referanstan, BASILMADI)"
  done

  if [ "$KURU" != 0 ]; then
    echo "  plan: yazılacak $n · dokunulmayacak $m · eksik alanlı $k"
    [ -z "$dizin_yok$dizin_red$ref_yok" ] || echo "  !! GERÇEK KOŞUM DURUR (HİÇBİR ŞEY yazmadan): yukarıdaki dizin YOK/REDDEDİLDİ ya da referans satırları — önce A0 site.yml / kasa + Agent render"
    return 0
  fi
  echo "  özet: yazıldı $n · dokunulmadı $m · eksik alanlı $k"
  echo "  yeniden başlatma YOK: tohumlanan değer referansla AYNI; birimler G3c'de etkinleşir ve ilk açılışta okur."
  echo "  sonraki: sudo ./sir_rotasyon.sh --envanter (sohbet kopyaları → EŞİT olmalı)"
  if [ "$k" -gt 0 ]; then
    echo "!! $k hedefte EKSİK/BOŞ/ÇİFT alan — dosyaya DOKUNULMADI; elle düzelt (eksik/çift alanda rotasyon ön-denetimde durur;
     BOŞ alanı --esitle ya da rotasyon doldurur — o zamana dek tüketici 401 alır):" >&2
    printf '%s' "$elle" >&2
    if [ "$o" != 0 ]; then echo "!! ayrıca $o hedef ÖLÇÜLEMEDİ:" >&2; printf '%s' "$olcemedi" >&2; fi
    exit 3
  fi
  # Sebep hedef başına, ADIYLA (G3b dal sonu M4) — tek bir genel cümle (eskiden "izin ya da UTF-8") sarkık bağı yanlış adlandırırdı.
  [ "$o" = 0 ] || olcum_yok "$o hedef ÖLÇÜLEMEDİ — dosyaya DOKUNULMADI; hedef başına sebep:
${olcemedi%$'\n'}"
}

# =================================================================================================
# YEDEKTEN GERİ ALMA — `--geri-al <yedek-dizini>` (TSK-261, 2026-10-01)
# =================================================================================================
# NİYE VAR. Bütün geri alma reçeteleri operatöre `sudo cp -p <yedek>/<yol> /<yol>` basıyordu: root `cp` HEDEF bağını izler
# (öngörülebilir bir yan ad bile gerekmez — hedefin kendisi ya da bir üst dizini bağsa yazım ağacın dışına gider). Reçetenin
# en çok okunduğu an da tam o andır: yazım sonrası ölçüm "DOĞRULANAMADI" ile durmuş (hedef yarışta bağa çevrilmiş) bir koşum.
# Reçete artık aracın KENDİ yolunu gösterir: yedekteki her kopya yardımcının `kopyala` işlemiyle (rotasyonun yazım çekirdeği —
# zincir ve hedef bağ izlenmez, geçici ad rastgele, mod/sahip yedekten, yerine koyma atomik, yazım sonrası ölçüm) geri konur.
# ÖLÇÜLEN SEÇENEKLER (en az dokunan): (a) `install -m -o -g` reçetesi — yol tabanlıdır (zincirdeki bağı izler) ve genel `<yol>`
# reçetesi dosya başına modu/sahibi bilemez; (b) kendi kendine yeten bir python satırı — çekirdeğin KOPYASI olurdu (tek-kaynak);
# (c) yardımcıyı yedeğe bırakmak — kodun bayat ikinci kopyası + dosya başına elle adım. Alt komut çekirdeğe yeni bir şey
# EKLEMEZ (`kopyala` zaten yedek ve negatif kontrol geri alması için vardır); ayrıştırma + bu gövde kadardır.
# KAPSAM — İZİN LİSTESİ, DİZİN TARAMASI DEĞİL: dizin adı `sir-yedek-<UTC ts>-<alt>` olmalı ve `<alt>` kopya tablosunda
# bulunmalıdır; geri konan yollar YALNIZ o alt komutun tablo satırlarının disk karşılıklarıdır (`_disk_yolu`) — yedekte başka
# bir dosya olsa da yazılmaz. Kasa yedeği (`vault/`) tabloda olmadığından girmez (kasa reçetesi: `kv rollback` / STDIN `kv put`).
# Dizin yedek kökünün (`$KOK/root`) DOĞRUDAN çocuğu olmalı ve bağ olmamalı. Dosyanın kendisi `kopyala`da ölçülür.
# DAVRANIŞ: restart YOK (eski reçetenin ikinci satırı gibi birim listesi basılır — geri almanın zamanını operatör seçer).
# ÖNCE YEDEK (inceleme I2, 2026-10-02): kuru OLMAYAN koşum yazmaya başlamadan önce mevcut hâli `_yedek_al <alt>` ile alır — aracın
# "her koşum ÖNCE dokunacağı her dosyayı yedekler" değişmezi. Gerekçe ölçüldü (inceleme sondası S2): yedek BÜTÜN dosyadır ve
# çok anahtarlı kopyalar (`.env-apisix` · `/opt/hindsight/.env` · hermes `.env`leri · motor deposu `state/secrets.json`) geri
# alındığında, yedekten SONRA başka bir rotasyonun yazdığı alanlar da eskiye döner (`--kapi` yedeği `--openrouter`ın yeni
# anahtarını siler; iptal edilmiş bir anahtar sessizce geri gelir). Ön yedek bunu geri alınabilir yapar: yolu stdout'a basılır
# (`_yedek_al`ın "yedek dizini:" satırı) ve çıkış reçetesi (`_geri_alma_recetesi`, `YEDEK` dolu) "geri almanın geri alınmasını"
# gösterir. Ön yedeğin kaynağı reddedilirse (hedef bağ — `kopyala` bağ izlemez) HİÇBİR dosya geri konmaz (`_yedek_al` durur).
# BÜTÜN DOSYA UYARISI: geri konacak her çok anahtarlı dosya için (`env` · `api`) yedek ile mevcut hâl yardımcının `alan-farki`
# işlemiyle kıyaslanır ve yedekten sonra değişmiş BAŞKA alanların (geri alınan alt komutun kendi alanları hariç) ADLARI basılır —
# `--kuru`da ÖNCEDEN, gerçek koşumda yazımla birlikte. Değer basılmaz.
# SIFIR DOSYA BAŞARI DEĞİLDİR (inceleme M5): yedekte alt komutun hiçbir tablo yolu yoksa (yanlış dizin) çıkış 1 + "geri konacak
# dosya YOK" — ön yedek alınmadan, kuru koşumda da. "geri alma tamam: 0 dosya" + çıkış 0, birimleri boşuna yeniden başlatan bir
# operatöre/otomasyona "geri alındı" demekti (uydurma yasağı).
# Bir hedef YAZIM anında reddedilirse (ön yedekten sonra bağa çevrilmiş · gevşek dizin · yedekte okunamayan dosya) o dosya ADIYLA
# söylenir ve ÖTEKİLER yine geri konur (`_negatif_geri_al` emsali: ilk retten durmak öteki kopyaları yeni değerde bırakırdı);
# sonda çıkış 1. Değer BASILMAZ.
# Çiviler: v611 F2 (bayt/mod eşit · kuru · restart yok · ön yedek) · F3 (ret biçimleri) · F4a/F4b (bağlı hedef: yedek alınamaz /
# yarışta adıyla, ötekiler geri konur) · F6 (bütün dosya uyarısı + geri almanın geri alınması) · F7 (motor deposu) · F8 (sıfır dosya).
geri_al() {
  local dizin="${1%/}" ad alt _alt _sir tur yol _alan _mod _sahip _onek n=0 basarisiz="" gorulen="" plan="" not_satiri
  [ "$(dirname "$dizin")" = "$KOK/root" ] \
    || die "--geri-al: '$dizin' bir yedek dizini DEĞİL — $KOK/root/sir-yedek-<UTC ts>-<alt> biçiminde, yedek kökünün
     DOĞRUDAN çocuğu olmalı (koşumun bastığı 'yedek dizini:' satırındaki yol). HİÇBİR ŞEY yazılmadı."
  ad="${dizin##*/}"
  # YARIM yedek (TSK-262 N2 — `_yarim_yedek_isaretle`): yedek alma yarıda kalmıştı, dosyaları EKSİK; geri alma onu "o koşumda
  # yoktu" diye yanlış okurdu. Ad kalıbı da reddeder (alt `[a-z][a-z0-9-]*` — nokta yok); bu satır sebebi ADIYLA söyler.
  case "$ad" in
    *.yarim) die "--geri-al: '$ad' YARIM bir yedek (yedek alma yarıda kaldı — dosyaları EKSİK) — girdi olarak KABUL EDİLMEZ.
     Tam bir yedek dizini ver (envanterin yedek listesi). HİÇBİR ŞEY yazılmadı." ;;
  esac
  alt="$(printf '%s\n' "$ad" | sed -n 's/^sir-yedek-[0-9]\{8\}T[0-9]\{6\}Z-\([a-z][a-z0-9-]*\)$/\1/p')"
  [ -n "$alt" ] || die "--geri-al: '$ad' bir yedek dizini adı DEĞİL (sir-yedek-<UTC ts>-<alt>). HİÇBİR ŞEY yazılmadı."
  _kopyalar | awk -v a="$alt" '$1==a {b=1} END{exit !b}' \
    || die "--geri-al: yedeğin alt komutu ($alt) kopya tablosunda YOK — hangi yolların geri konacağı bilinmez. HİÇBİR ŞEY yazılmadı."
  if sudo test -L "$dizin"; then die "--geri-al: yedek dizini SEMBOLİK BAĞ ($dizin) — izlenmez. HİÇBİR ŞEY yazılmadı."; fi
  sudo test -d "$dizin" || die "--geri-al: yedek dizini YOK: $dizin. HİÇBİR ŞEY yazılmadı."
  echo "=== GERİ ALMA: $dizin → $(_bayrak "$alt") kopyaları (bağ İZLENMEZ; mod/sahip yedekten; DEĞER BASILMAZ) ==="
  [ "$KURU" = 0 ] || echo "  KURU KOŞUM — HİÇBİR ŞEY YAZILMAZ (ön yedek dahil)"
  # KÖKEN (TSK-262 N2): girdi bir ÖN YEDEKSE (önceki bir --geri-al'ın aldığı) bu koşum o geri almayı GERİ ALIR — operatör bilsin.
  if sudo test -f "$dizin/KOKEN"; then
    echo "  köken: girdi bir ÖN YEDEK ($dizin/KOKEN) — bu koşum önceki bir --geri-al'ı GERİ ALIR (o geri almadan önceki hâle döner)"
  fi
  # PLAN — yedekte bulunan tablo yolları; yazım ve ön yedek bundan SONRA.
  while read -r _alt _sir tur yol _alan _mod _sahip _onek; do
    [ "$_alt" = "$alt" ] || continue
    yol="$(_disk_yolu "$tur" "$yol")" || continue
    case " $gorulen " in *" $yol "*) continue ;; esac
    gorulen="${gorulen:+$gorulen }$yol"
    if ! sudo test -e "$dizin$yol" && ! sudo test -L "$dizin$yol"; then
      echo "  · yedekte YOK (o koşumda dosya yoktu — yedek ATLANMIŞTI): $yol"
      continue
    fi
    plan="${plan:+$plan }$yol"
  done < <(_kopyalar)
  [ -n "$plan" ] || die "--geri-al: yedekte $(_bayrak "$alt") alt komutunun HİÇBİR tablo yolu yok — geri konacak dosya YOK
     (yanlış yedek dizini?). '0 dosya geri kondu' bir başarı DEĞİLDİR. HİÇBİR ŞEY yazılmadı (ön yedek dahil)."
  # Çıkış reçetesi (`_geri_alma_recetesi`, `$ALT`ı okur) geri alınan alt komutun BİRİMLERİNİ bassın: ön yedekle geri almanın geri
  # alınması "sudo $0 --geri-al <ön yedek>" + o birimlerin yeniden başlatılmasıdır.
  ALT="$alt"
  if [ "$KURU" = 0 ]; then
    adim "ÖNCE mevcut hâl yedeklenir (geri almanın geri alınması bu yedekten)"
    _yedek_al "$alt" "$dizin"
  else
    echo "  (gerçek koşum ÖNCE mevcut hâli yedekler: $KOK/root/sir-yedek-<UTC ts>-$alt — geri almanın geri alınması o yedekten)"
  fi
  for yol in $plan; do
    not_satiri="$(_butun_dosya_notu "$alt" "$yol" "$dizin")"
    if [ "$KURU" != 0 ]; then
      echo "  geri konacak: $yol"
      [ -z "$not_satiri" ] || echo "$not_satiri"
      continue
    fi
    # `||` ADLANDIRMADIR (yutma değil): yardımcının adlı reddi stderr'de durur, yol biriktirilir ve sonda bağırılır.
    if py kopyala "$dizin$yol" "$KOK$yol"; then
      oldu "geri kondu: $yol"
      [ -z "$not_satiri" ] || echo "$not_satiri"
      n=$((n+1))
    else
      echo "!! geri KONAMADI: $yol (yardımcının adlı reddi yukarıda)" >&2
      basarisiz="${basarisiz:+$basarisiz }$yol"
    fi
  done
  echo "  sonra yeniden başlat: $(_recete_birimleri $(_birimler "$alt"))"
  [ "$KURU" = 0 ] || return 0
  [ -z "$basarisiz" ] || die "--geri-al: $n dosya geri kondu, şunlar KONAMADI: $basarisiz — hedef bağ ya da zincir/izin
     kuralına aykırı olabilir (yardımcının adlı reddi yukarıda). Değeri BASMADAN incele: sudo stat -c '%U:%G %a %F %n' <yol>"
  oldu "geri alma tamam: $n dosya (birimleri yukarıdaki satırla yeniden başlat)"
}

#: BÜTÜN DOSYA NOTU — `_butun_dosya_notu <alt> <yol> <yedek dizini>` → tek satır (ya da tek değerli türde hiçbir şey). Çok
#: anahtarlı kopya (`env` · `api`) BÜTÜN döner: yedekten sonra değişmiş BAŞKA alanlar söylenir — alt komutun kendi
#: alanları (tablodaki `env` alanları · `api` satırının sır kimliği = depo anahtarı) hariç. Değer basılmaz (`alan-farki`); ad YALNIZ
#: iki tarafta da AYNI SAYIDA varsa ya da aranan ad / sır-adı sonekiyse basılır, öteki farklar SAYIYLA (TSK-262 düzeltme turları
#: 1–2, inceleme I1 · Y1).
#: `dosya`/`url` kopyası tek değerdir ("başka alan" yok). Kıyas ölçülemezse bunu ADIYLA söyler — uyarı susmaz.
_butun_dosya_notu() {
  local alt="$1" yol="$2" dizin="$3" _alt sir tur y d _alan _m _s _o ilk="" haric="" hal
  while read -r _alt sir tur y _alan _m _s _o; do
    [ "$_alt" = "$alt" ] || continue
    d="$(_disk_yolu "$tur" "$y")" || continue
    [ "$d" = "$yol" ] || continue
    [ -n "$ilk" ] || ilk="$tur"
    case "$tur" in env) haric="$haric $_alan" ;; api) haric="$haric $sir" ;; esac
  done < <(_kopyalar)
  case "$ilk" in env|api) ;; *) return 0 ;; esac
  if ! sudo test -e "$KOK$yol" && ! sudo test -L "$KOK$yol"; then
    echo "    · hedef şu an YOK — yedekteki dosya bütün olarak kurulur"; return 0
  fi
  # `||` ADLANDIRMADIR: yardımcının düşüşü (bağ · UTF-8/JSON değil) aşağıda "ÖLÇÜLEMEDİ" satırına gider, uyarı susmaz.
  # BASILABİLİR ADLAR TEK KAYNAKTAN (TSK-262 düzeltme turu 1, inceleme I1): tablonun aranan adları (`_aranan_adlar`) ve sır-adı
  # sonekleri (`_SIR_ADI_SONEKLERI` — `_sir_adi_mi`nin listesi) yardımcıya argüman olarak geçer; yardımcı kopya tutmaz.
  # shellcheck disable=SC2086,SC2046
  hal="$(py alan-farki "$ilk" "$dizin$yol" "$KOK$yol" $haric --basilir $(_aranan_adlar) --sonek $_SIR_ADI_SONEKLERI)" \
    || hal="ÖLÇÜLEMEDİ"
  case "$hal" in
    AYNI) echo "    · DOSYANIN TAMAMI yedekteki hâline döner; yedekten sonra değişmiş başka alan YOK" ;;
    FARKLI:*) echo "    !! DOSYANIN TAMAMI döner — yedekten sonra değişmiş BAŞKA alanlar da ESKİYE döner:${hal#FARKLI:} (değer basılmaz; o sırlar için sonra kendi rotasyonu ya da --esitle gerekebilir)" ;;
    *) echo "    !! DOSYANIN TAMAMI döner — BAŞKA alanların farkı ÖLÇÜLEMEDİ (yukarıda): öteki alanlar da yedekteki hâline döner" ;;
  esac
}

# =================================================================================================
KURU=0
ESITLE=0
VAULT_KIP=0
URET=0
ALT=""
GERI_AL_DIZINI=""   # `--geri-al <yedek-dizini>` (TSK-261) — okuyan: `geri_al` · `_bayrak`
#: İKİ JETONLU BAYRAK (G3b Task 3, 2026-10-01): `--kapi-bot <ad>` değer ALIR, `for _a in "$@"` onu göremezdi → `while`/`shift`.
#: Öteki bayrakların davranışı BİREBİR (tek jeton, aynı `case`). Ad, bayraktan SONRAKİ jetondur — ne olursa olsun
#: (`--kuru` bile): ad gibi görünmeyen bir jetonu "ad yok" sayıp bayrak diye tüketmek `--kapi-bot --kuru`yu kuru koşuma
#: çevirirdi. Ad `_sohbet_botu_mu` ile TAM eşitlikle doğrulanır; geçersiz ad root kapısından, çalışma dizininden, kasadan ve
#: her dosyadan ÖNCE burada durur (v604 C2). İç alt ad `kapi-bot-<ad>` (Rol-1 G3b-R2).
while [ "$#" -gt 0 ]; do
  _a="$1"; shift
  case "$_a" in
    --kuru) KURU=1 ;;
    --esitle) ESITLE=1 ;;
    --vault) VAULT_KIP=1 ;;
    --uret) URET=1 ;;
    --kapi|--tenant|--db|--dash|--openrouter|--apisix-admin|--cp|--api-sunucu|--tohumla-sohbet|--envanter|--kopyalar)
      [ -z "$ALT" ] || die "iki alt komut verildi: $(_bayrak "$ALT") ve $_a — her koşum TEK sır döndürür"
      ALT="${_a#--}" ;;
    --kapi-bot)
      [ "$#" -gt 0 ] || die "--kapi-bot bot ADI ister: --kapi-bot <$(echo $_SOHBET_BOTLARI | tr ' ' '|')> — HİÇBİR ŞEY yazılmadı"
      _bot="$1"; shift
      _sohbet_botu_mu "$_bot" || die "--kapi-bot: geçersiz bot adı '$_bot' — geçerli adlar (TAM eşleşme, küçük harf): $_SOHBET_BOTLARI.
     Liste kabuktaki TEK sabittir (_SOHBET_BOTLARI = A0 sohbet_profil_adlari). HİÇBİR ŞEY yazılmadı."
      [ -z "$ALT" ] || die "iki alt komut verildi: $(_bayrak "$ALT") ve --kapi-bot $_bot — her koşum TEK sır döndürür"
      ALT="kapi-bot-$_bot" ;;
    #: `--geri-al <yedek-dizini>` (TSK-261) — `--kapi-bot` gibi SONRAKİ jetonu değer olarak alır (ne olursa olsun); dizin
    #: `geri_al`da doğrulanır (yedek kökünün çocuğu · ad biçimi · alt komut tabloda · bağ değil).
    --geri-al)
      [ "$#" -gt 0 ] || die "--geri-al YEDEK DİZİNİ ister: --geri-al /root/sir-yedek-<UTC ts>-<alt> (koşumun 'yedek dizini:'
     satırındaki yol) — HİÇBİR ŞEY yazılmadı"
      GERI_AL_DIZINI="$1"; shift
      [ -z "$ALT" ] || die "iki alt komut verildi: $(_bayrak "$ALT") ve --geri-al — geri alma bir rotasyonla birlikte koşmaz"
      ALT="geri-al" ;;
    *) die "bilinmeyen argüman: $_a (--kapi | --tenant | --db | --dash | --openrouter | --apisix-admin | --cp | --api-sunucu | --kapi-bot <ad> | --tohumla-sohbet | --geri-al <yedek-dizini> | --envanter | --kopyalar [| --kuru | --esitle | --vault | --uret])" ;;
  esac
done
[ -n "$ALT" ] || die "alt komut ZORUNLU: --kapi | --tenant | --db | --dash | --openrouter | --apisix-admin | --cp | --api-sunucu | --kapi-bot <ad> | --tohumla-sohbet | --geri-al <yedek-dizini> | --envanter | --kopyalar (+ --kuru)"

# `--kuru` YALNIZ ROTASYON alt komutlarında anlamlıdır. `--envanter`/`--kopyalar` bayrağı hiç
# okumaz ve `--envanter --kuru` SESSİZCE tam envanteri koşardı: kuru koşum isteyen operatör
# istediğini aldığını sanır (inceleme B6). Koşum ENGELLENMEZ (ikisi de zaten hiçbir şey yazmaz),
# ama etkisizlik SÖYLENİR — sessiz kabul, olmayan bir sözleşmeyi var gibi gösterir.
KURU_ONERILIR=0
case "$ALT" in
  kapi|tenant|db|dash|openrouter|apisix-admin|cp|api-sunucu|kapi-bot-*|tohumla-sohbet|geri-al) KURU_ONERILIR=1 ;;
  *) [ "$KURU" = 0 ] || echo "!! --kuru bu alt komutta ETKİSİZDİR: --$ALT zaten hiçbir şey yazmaz." >&2 ;;
esac
#: GERİ ALMA BİR ROTASYON DEĞİLDİR (TSK-261): değer üretmez, sormaz, kasaya yazmaz, eşitlemez — tohumlamanın gerekçesiyle AÇIK
#: ret, root kapısından ve her dosyadan ÖNCE (`KURU_ONERILIR` kümesinde: kuru koşum anlamlıdır).
if [ "$ALT" = "geri-al" ] && { [ "$ESITLE" = 1 ] || [ "$VAULT_KIP" = 1 ] || [ "$URET" = 1 ]; }; then
  die "--geri-al --esitle / --vault / --uret ile verilemez: geri alma yedekteki dosyaları yerine koyar — değer üretmez,
     kasaya yazmaz, eşitlemez (kasa geri alımı reçetenin kendi satırıdır). Doğrusu: sudo ./sir_rotasyon.sh --geri-al <yedek-dizini> [--kuru].
     HİÇBİR ŞEY yazılmadı."
fi
#: TOHUMLAMA BİR ROTASYON DEĞİLDİR (G3b Task 4): değer üretmez, sormaz, kasaya yazmaz, eşitlemez. `KURU_ONERILIR`
#: kümesindedir (kuru koşum anlamlıdır), ama `--esitle`/`--vault` kapıları o kümeye bakar — sessiz kabul yerine AÇIK ret,
#: root kapısından, çalışma dizininden ve her dosyadan ÖNCE (v604 D11).
if [ "$ALT" = "tohumla-sohbet" ] && { [ "$ESITLE" = 1 ] || [ "$VAULT_KIP" = 1 ] || [ "$URET" = 1 ]; }; then
  die "--tohumla-sohbet --esitle / --vault / --uret ile verilemez: tohumlama değer üretmez, sormaz, kasaya yazmaz ve
     eşitlemez — YALNIZ YOK olan sohbet .env'ini referanslardan kurar. Doğrusu: sudo ./sir_rotasyon.sh --tohumla-sohbet [--kuru].
     HİÇBİR ŞEY yazılmadı."
fi
# `--esitle` YALNIZ rotasyon alt komutlarıyla anlamlıdır: neyi eşitleyeceği kopya tablosunun
# alt komut sütunundan gelir; `--envanter --esitle` ne ölçer ne yazar — sessiz kabul yerine dur.
[ "$ESITLE" = 0 ] || [ "$KURU_ONERILIR" = 1 ] \
  || die "--esitle yalnız rotasyon alt komutlarıyla: --kapi | --tenant | --db | --dash | --openrouter | --apisix-admin | --cp | --api-sunucu | --kapi-bot <ad> (+ --esitle [--kuru]); --$ALT ile anlamsız"
# `--vault` de YALNIZ rotasyon alt komutlarıyla anlamlıdır ve `--esitle` ile BİRLİKTE VERİLEMEZ:
# ikisi zıt yönlerdir. `--esitle` mevcut REFERANS kopyayı ötekilere taşır (değer üretilmez),
# `--vault` YENİ bir değeri kasaya koyup oradan yayar. Sessizce biri ötekini yutarsa operatör
# "eşitledim" sanarken taze bir anahtar yazılmış olurdu.
[ "$VAULT_KIP" = 0 ] || [ "$KURU_ONERILIR" = 1 ] \
  || die "--vault yalnız rotasyon alt komutlarıyla: --kapi | --tenant | --db | --dash | --openrouter | --apisix-admin | --cp | --api-sunucu | --kapi-bot <ad> (+ --vault [--kuru]); --$ALT ile anlamsız"
[ "$VAULT_KIP" = 0 ] || [ "$ESITLE" = 0 ] \
  || die "--vault ile --esitle birlikte verilemez: biri KASADAN yeni değer yayar, öteki mevcut referansı kopyalara taşır"
# `--uret` (TSK-226c, 2026-09-26) YALNIZ `--vault` ile ve YALNIZ genel kasa döngüsünün üreticileriyle anlamlıdır
# (`_uret_sinifi` tanım kümesi). Kapılar ROOT kapısının ve `_islik_kur`un ÜSTÜNDE: yanlış birleşim hiçbir
# istem açmadan, hiçbir dosyaya ve kasaya dokunmadan durur (v557 E1). Sessiz kabul, operatöre "üretildi"
# sandırıp istemi (ya da eski yolun Agent'la ezilen yazımını) koşturmak olurdu.
if [ "$URET" = 1 ]; then
  if [ "$VAULT_KIP" = 0 ]; then
    # Öneri YALNIZ geçerli bir biçim varsa basılır (`--envanter --vault --uret` diye bir sözleşme YOK —
    # olmayan biçimi önermek hata metnini yanlış yola sokar; `_KURU_ONERI` emsali, inceleme B6).
    _URET_ONERI=""
    _uret_sinifi "$ALT" >/dev/null && _URET_ONERI=" Doğrusu: sudo $0 $(_bayrak "$ALT") --vault --uret."
    die "--uret yalnız --vault ile anlamlıdır: kasa yolunun istemi yerine değeri betik İÇİNDE üretir (eski yol
     değeri ZATEN üretir ama kasaya bağlı sırda yazımı Agent render'ıyla ezilir).$_URET_ONERI HİÇBİR ŞEY yazılmadı."
  fi
  case "$ALT" in
    openrouter) die "--uret --openrouter ile verilemez: OpenRouter ve NOUS anahtarlarını betik ÜRETEMEZ — sağlayıcı
     panosunda üretilir ve kasa yolu istemle alır (sudo $0 --openrouter --vault). HİÇBİR ŞEY yazılmadı." ;;
    db) die "--db --vault --uret bu turun kapsamı DIŞI (TSK-226c): DB dalı (vault_db_rotasyon) parolayı istemle alır
     ve ikinci hakikat noktası (ALTER ROLE) GERİ ALINAMAZ — üretim o dalda tasarlanmadı. Kasa yolu:
     sudo $0 --db --vault (istemle). HİÇBİR ŞEY yazılmadı." ;;
    cp) echo "!! --uret bu yolda ETKİSİZDİR: --cp --vault değeri ZATEN betik İÇİNDE üretir (vault_cp_rotasyon, TSK-226b)." >&2 ;;
    *) _uret_sinifi "$ALT" >/dev/null \
         || die "--uret: $(_bayrak "$ALT") için üretim sınıfı YOK (_uret_sinifi) — HİÇBİR ŞEY yazılmadı." ;;
  esac
fi

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
[ "$KURU_ONERILIR" = 0 ] || _KURU_ONERI="   (kuru koşumda: sudo ./sir_rotasyon.sh $(_bayrak "$ALT") --kuru)"
[ "$_UID" = 0 ] || die "bu betik ROOT olarak koşar; şu an uid=$_UID.
     Doğrusu: sudo ./sir_rotasyon.sh $(_bayrak "$ALT")$_KURU_ONERI
     Sebep: kanıt girdileri (curl -K cfg · PGPASSFILE · SQL) 0600 root yazılır; onları çağıran
     kimlikle okutmak HER kanıtı 000 yapar ve rotasyon doğrulanamaz."

_islik_kur
# YAZIM ÖNCESİ HEDEF ÖN-DENETİMİ (G3b) — bütün yazım yollarının (kasa dalı · eski yol alt komutları) ÖNÜNDE,
# TEK nokta; kuru koşum ve eşitleme hariç (gerekçe `_hedef_on_denetim` şerhinde). Çalışma dizininden SONRA (G3b Task 3):
# alan denetimi gömülü yardımcıyı (`yaz-env`in kuralı) ister; çalışma dizini bir yazım DEĞİLDİR (v604 A10).
if [ "$KURU" = 0 ] && [ "$ESITLE" = 0 ] && [ "$KURU_ONERILIR" = 1 ]; then _hedef_on_denetim "$ALT"; fi
if [ "$VAULT_KIP" = 1 ]; then vault_rotasyon "$ALT"; exit 0; fi
if [ "$ESITLE" = 1 ]; then esitle "$ALT"; exit 0; fi
case "$ALT" in
  kapi)       kapi ;;
  tenant)     tenant ;;
  db)         db ;;
  dash)       dash ;;
  openrouter) openrouter ;;
  apisix-admin) apisix_admin ;;
  cp)         cp_erisim ;;
  api-sunucu) api_sunucu ;;
  kapi-bot-*) kapi_bot "${ALT#kapi-bot-}" ;;
  #: G3b Task 4 — ön-denetim bu alt komutta BOŞ geçer (tabloda `tohumla-sohbet` satırı yok); kendi kapıları `tohumla_sohbet`te.
  tohumla-sohbet) tohumla_sohbet ;;
  #: TSK-261 — ön-denetim burada da BOŞ geçer (tabloda `geri-al` satırı yok); her dosya `kopyala`da yazım anında ölçülür ve
  #: reddedilen ADIYLA söylenir, ötekiler geri konur (`geri_al` şerhi).
  geri-al)    geri_al "$GERI_AL_DIZINI" ;;
  envanter)   envanter ;;
esac

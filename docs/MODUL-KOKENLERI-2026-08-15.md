# MODÜL KÖKENLERİ — 2026-08-15

**Ne bu:** 2026-08-15 turunda modül başlık docstring'leri 'ne yapar'a odaklanacak şekilde
yeniden yazıldı; WP/tur/kart/tarih köken etiketleri koddan çıkarıldı. Bu dosya, o günkü
başlık docstring'lerinin DEĞİŞTİRİLMEDEN ÖNCEKİ tam metinlerinin arşividir — 'hangi WP'de,
ne zaman, hangi kartla yapıldı' sorusunun cevabı artık burada ve git tarihçesindedir.

**Okuyucu (YASA 6):** köken arayan operatör + denetim yapan roller. Kod açıklaması 'ne
yapar'ı anlatır; köken burada durur. (Mekanizma dersleri — mezar taşları, YANLIŞLANDI
düzeltmeleri — koddan ÇIKARILMADI; onlar tarihçe değil, yaşayan uyarıdır.)

---

## `meridian/__init__.py`

```text
Meridian — kapalı-bar swing paper-trading motoru + Hermes öğrenme döngüsü.

Katman haritası ve her modülün görevi: docs/MODUL-ENVANTERI-2026-08-15.md
(katman sınırlarını pyproject.toml [tool.importlinter] sözleşmeleri mühürler).
```

## `meridian/agent_telemetry.py`

```text
agent_telemetry.py — AJAN ÇAĞRI TELEMETRİSİ + HAM İZ DEFTERİ (D3 modül 1 ve 2, 2026-08-07).

Kaynak: `docs/PATTERN-ETUDU-2026-08-06.md` C2-1 (S) ve C2-2 (M) · `docs/TASARIM-YONU-2026-08-07.md` §4.

NEDEN VAR — İKİ ÖLÇÜLMÜŞ KÖRLÜK, TEK MODÜL:

  (1) SÜRE TÜRETİLEMEZ. Bugünkü `agent_call` olayı model/deneme/boş/araç taşıyor ama SÜRE
      TAŞIMIYOR. Canlı defterde 2026-08-04T01:14'te iki satır var (attempt=1 @01:14:07,
      attempt=2 @01:14:17) ve aradaki 10 sn'yi ancak ÇIKARSAyabilirsiniz — o farkın içinde
      bütçe bekleyişi, skill senkronu ve iki ayrı süreç doğuşu da vardır. "Gece koşusu neden
      40 dk sürdü, hangi çağrı takıldı" sorusu bu yüzden cevapsızdı. Süre ÖLÇÜM ANINDA yazılır;
      sonradan türetilen bir süre, ölçülmemiş bir süredir (UYDURMA YASAĞI).

  (2) HAM ÇIKTI 200 KARAKTERDE KESİLİYORDU. v193'te `agent_call_empty` olayına eklenen
      `ham_stdout`/`ham_stderr` alanları TEK SATIRLIK olay alanlarıdır ve 200 karakterde
      biter. Bir Python traceback'i ya da bir sağlayıcı hata gövdesi oraya sığmaz — yani
      "boş yanıt, neden bilinmiyor" hâli 200 karakterin ötesinde hâlâ mümkündü. Tam iz AYRI
      bir deftere iner, çünkü `events.jsonl` canlıda zaten ~11 MB (ölçüldü: 2026-08-04
      yedeği, 11.190.074 bayt) ve onu ham izlerle beslemek okunabilir tek defteri öldürürdü.

MASKELEME TEK KAYNAKTIR. Sır desenleri (`_GIZLI_DESENLER` + `_JETON_RE`) ve `maskele()` gövdesi
`hermes._ham_ozet`ten BURAYA TAŞINDI; `hermes._ham_ozet` artık bu modüle DELEGE eden ince bir
sarmalayıcıdır (tarihsel ad ve v193 sözleşmesi korunur). İkinci bir maskeleme uygulaması YASAK:
iki kopya sessizce ayrışır ve ayrışan taraf sızdırır. `sirlari_maskele` ile `maskele` ayrı
işlerdir ve bu bilinçlidir — birincisi YALNIZ sır desenlerini uygular (metnin biçimine dokunmaz,
`ops/vaka_sabitle.py` fikstür dondururken onu kullanır), ikincisi defter-alanı biçimini de
uygular (ANSI sök + satırları katla + kırp).

DEFTERLER (ikisi de append-only JSONL, mevcut `store` desenine uyar; yeni biçim İCAT EDİLMEDİ):
  * `agent_calls.jsonl`  — çağrı başına KÜÇÜK telemetri satırı (süre/deneme/araç/sonuç sınıfı).
  * `agent_traces.jsonl` — çağrı başına BÜYÜK ham iz satırı (sır-maskeli stdout+stderr).
İkisi `iz_id` ile birleşir; `iz_id` ayrıca `spend.jsonl` satırının `note` alanına konabilir
(bugün konmuyor — HTTP bacağının kendi muhasebesi var, bkz. `tasiyici` alanı).

TAVANLAR ÇİVİLİDİR (C2-2'nin "budama kuralı doğuşta yazılmalı" şartı). Sayılar aşağıdaki
sabitlerde yaşar ve `tests/test_ajan_telemetri_v197.py` onları test eder:
  * ham iz: akış başına {IZ_AKIS_TAVANI_KR} karakter (maskeleme SONRASI, kırpma BEYANLI),
  * ham iz defteri: son {IZ_SATIR_TAVANI} satır (halkasal budama),
  * telemetri defteri: son {CAGRI_SATIR_TAVANI} satır,
  * türetilen en kötü hâl: ~{IZ_SATIR_TAVANI} × (2×{IZ_AKIS_TAVANI_KR} + ~600 üstbilgi) ≈ 5 MB.
TAVAN ÖLÇÜLDÜ (2026-08-07, yerel; halka tam dolu + iki akış da tavanda): ham iz defteri
4.887.600 bayt, telemetri defteri 144.460 bayt — yani türetilen 4,98 MB üst sınırı GERÇEKTEN
üst sınırdır, dilek değil. Ölçüm koşumu `tests/test_ajan_telemetri_v197.py` içinde küçültülmüş
sabitlerle tekrarlanır (tam ölçekli koşum bir testin işi değil, bir kez yapılmış bir ölçümdür).

YASA 6 (okuyucusuz yazım yok):
  * `agent_calls.jsonl` — DIŞ okuyucusu `hermes.integrations_status()` (satırları KENDİ okur,
    yorumu `ozet()`e verir) → `/api/hermes` → pano. Bu yüzden `codelaw.DECLARED_SINKS`te
    muafiyeti YOKTUR ve olmamalıdır.
  * `agent_traces.jsonl` — ham satırlar bilerek panoya TAŞINMAZ (5 MB'lık ham izi HTTP'ye
    koymak hem maliyet hem sızıntı yüzeyidir). Tüketicisi `iz_oku()` (teşhis) ve
    `ops/vaka_sabitle.py` (fikstür dondurucusu, `meridian/` DIŞINDA → statik graf göremez);
    DOLULUK durumu `ozet()["iz"]` ile aynı pano yolundan çıkar. Muafiyeti `DECLARED_SINKS`te
    gerekçesiyle beyanlıdır.

PANO NOTU (D3-UI dalgasına devir): bugün bu özet `/api/hermes` gövdesinde AKIYOR ama panoda
ÇİZİLMİYOR — `meridian/web/*` bu turun dokunma yasağındaydı. Kart (④ Öğrenme yüzeyi,
`TASARIM-YONU` §3) D3-UI dalgasının işidir; veri hazır bekliyor.
```

## `meridian/analytics.py`

```text
analytics.py — read-model computations over state/ for the dashboard. Pure reads; no mutation.
Everything the dashboard shows is derived here from real state, never fixtures.
```

## `meridian/api.py`

```text
api.py — FastAPI read-model over state/ + a tiny write surface (HALT / resume / approvals).
The dashboard NEVER talks to the broker directly; it reads state and posts operator intents.
Single-operator: reach it over an IAP tunnel (no inbound firewall on the VM). Optional shared-token
gate for local use. Research system. Paper mode. Not financial advice.
```

## `meridian/arming.py`

```text
arming.py — Silahlanma Değerlendiricisi (#3): uyuyan→ölç→silahla döngüsünün eksik son halkası.

Uyuyan kurulumlar karşı-olgusal defterde ileriye dönük ölçülür (küme SABİT DEĞİL: `_dormant_setups()`
motor listesinden ARMED_SETUPS'ı düşerek TÜRETİR — 2026-08-11 exhaustion_hammer, 2026-08-12
momentum_burst operatör onayıyla silahlandı ve kümeden çıktı, bugün geriye episodic_pivot kalır); bu
modül o kanıt YAZILI eşiği geçtiğinde KAPI ölçÜMÜNÜ otomatik koşar: incumbent (mevcut silahlı set)
vs aday (aynı parametreler + kurulum silahlı) üretim pencerelerinde walk edilir ve karar TAMAMEN
mevcut yasaya bırakılır (_gate_eval: blok-bootstrap + K-ceza + fold çoğunluğu + kuyruk vetosu).

SİLAHLANMA OTOMATİK DEĞİLDİR: kapı GEÇSE bile ARMED_SETUPS değişmez — sonuç panele/deftere
"silahlanmaya hazır (P=…)" olarak düşer ve operatör onayı beklenir (canlı davranış değişikliği
bilinçli bir insan kararıdır; momentum_burst emsali). Kapı kalırsa ölçülen sayılar dürüstçe kalır.

Ölçüm kanalı: params["entry.armed_extra"] — scan_entry bu listedeki kurulumları da silahlı sayar;
paramlar üzerinden aktığı için canlı döngüyle YARIŞMAZ (global ARMED_SETUPS'a dokunulmaz).
```

## `meridian/auth.py`

```text
auth.py — operatör kimliği: parola doğrulama + imzalı oturum çerezi.

NEDEN VAR (2026-07-28, Oracle Cloud dağıtımı öncesi): pano bugüne kadar YALNIZ `--host 127.0.0.1`
bağlanmasıyla korunuyordu. `MERIDIAN_DASH_TOKEN` hiçbir yerde ayarlı değildi, dolayısıyla
`api._auth` 51 uçta çağrılıyor ama hepsinde anında dönüyordu — fiilen kimlik doğrulaması yoktu.
Genel bir IP'ye çıkıldığı an bu, hesap durumunu okuyan ve HALT/DEVAM/Flatten/mutasyon tetikleyen
bir yüzeyin yetkisiz açılması demektir.

TASARIM KARARLARI ve GEREKÇELERİ

* **Parola diskte asla düz durmaz.** `hashlib.scrypt` (stdlib; yeni bağımlılık yok) ile
  tuzlanmış türetme. Parametreler RFC 7914'ün etkileşimli-giriş profilinden: n=2^15, r=8, p=1.
  Doğrulama `hmac.compare_digest` ile sabit zamanlı — `!=` ilk uyumsuz baytta kısa devre yapar
  ve hash'i bayt bayt kurtarmaya izin verir (CWE-208).

* **Oturum ÇEREZDE, localStorage'da DEĞİL.** Eski akış token'ı `localStorage`'a yazıyordu; orası
  JavaScript'e açıktır, yani tek bir XSS kalıcı erişim demektir. Çerez `HttpOnly` olduğunda JS
  onu okuyamaz. `SameSite=Strict` çapraz-site istek sahteciliğini (CSRF) kapatır — HALT ve
  Flatten gibi tek POST'la iş gören uçlar için bu teorik bir kaygı değildir.

* **Oturum durumsuz ve İMZALI.** `<exp>.<nonce>.<hmac>` — sunucu tarafında oturum tablosu yok,
  yani yeniden başlatma oturumları düşürmez ama imza anahtarı değişirse HEPSİ düşer. Anahtar
  diskte (0600) tutulur; yoksa üretilir.

* **URL'de token YOK.** Eski `_auth` `?token=` kabul ediyordu ve indirme bağlantıları token'ı
  oraya koyuyordu. URL'ler sunucu loglarına, tarayıcı geçmişine ve `Referer` başlığına düşer.
  Çerez tabanlı oturum indirmelerde de çalışır, çünkü tarayıcı onu kendiliğinden gönderir.

* **Kaba kuvvet sınırlanır.** IP başına kayan pencere; eşiği aşınca kilit. Sayaç süreç-içidir:
  tek süreçli dağıtımda yeterli, yatay ölçeklenirse paylaşımlı bir depoya taşınmalıdır (bu
  dosyada başka bir iddiada bulunulmuyor).
```

## `meridian/auth_cli.py`

```text
auth_cli.py — operatör parolasını kabuktan yönet.

    .venv/bin/python -m meridian.auth_cli set        # parola belirle / değiştir
    .venv/bin/python -m meridian.auth_cli status     # kurulu mu, dosya izni doğru mu
    .venv/bin/python -m meridian.auth_cli logout-all # imza anahtarını döndür → tüm oturumlar düşer

NEDEN KABUKTAN: `POST /api/setup-password` yalnız parola HENÜZ KURULU DEĞİLKEN çalışır. Kurulduktan
sonra parolayı değiştirmenin tek yolu buradan geçer, yani state/auth.json'a erişim gerekir — ki o da
sunucuya erişim demektir. Web üzerinden "parolamı unuttum" akışı BİLEREK yoktur: tek operatörlü bir
sistemde o akış, saldırgan için ikinci bir giriş kapısından başka bir şey değildir.

Parola ekrana YAZILMAZ (getpass) ve kabuk geçmişine düşmez — argüman olarak da alınmaz.
```

## `meridian/backtest.py`

```text
backtest.py — walk-forward out-of-sample engine. THE learning gate. Replays through the exact
same strategy.py + broker.py used live, so backtest numbers are honest (§4).

Event ordering per trading day D (no look-ahead — decisions use bars <= D, executions at D+1 open):
  1. OPEN(D):   execute time-stop/regime-flip exits flagged at D-1 close; fill entries armed at D-1 close
  2. INTRADAY(D): gap-aware touch exits (stop/trail/target) for all open positions, using levels set <= D-1
  3. CLOSE(D):  update trailing stops; recompute regime; scan + rank new entry signals; arm for D+1
```

## `meridian/bararchive.py`

```text
bararchive.py — Faz 5 KANIT KATMANININ İLK TAŞI: dakikalık bar çerçevelerinin kalıcı arşivi.

NEDEN ŞİMDİ: intraday hattı (hotstate → mrd:bars) UÇUCUDUR ve bilerek öyledir — Redis ring'i ~2
seans tutar, TTL sonrası bar yoktur. Bu, sıcak okuma için doğru; ama "dakika-hassas icra EOD icradan
gerçekten daha mı iyi?" sorusu ancak GEÇMİŞ dakikalık çerçeveler biriktikten SONRA cevaplanabilir.
Bugün başlamayan bir birikim, üç ay sonra da üç aylık olmaz. Arşiv bu yüzden ölçümden ÖNCE açılır.

TÜKETİCİSİ BUGÜN YOK VE BU BİLİNÇLİDİR. Tüketici GELECEK "dakika-hassas icra vs EOD" ölçüm
raporudur. Bunu yazmak, YASA 6'nın (üretilip tüketilmeyen artefakt) bilerek verilmiş bir cevabıdır:
ihlal, kimsenin OKUMADIĞI bir dosyayı kimsenin BİLMEDEN bırakmasıdır — kararın kendisi değil.

CODELAW BULGUSU (2026-07-27, ölçüldü — varsayılmadı): `codelaw.artifact_graph` bir yazma/okuma
çağrısının İLK ARGÜMANINI yalnız üç biçimde çözer: dize sabiti, modül/global sabit adı, ya da bir
attribute. Buradaki hedef ad TARİHLİDİR ve f-string ile kurulur (`intraday_bars/2026-07-27.jsonl`),
yani `ast.JoinedStr`dir → statik graf onu ÇÖZEMEZ ve `artifacts` sözlüğüne HİÇ girmez; bunun yerine
`unresolved` listesine yazılır (tarayıcı kendi körlüğünü gizlemez — tests/test_codelaw_v59.py'deki
`test_dinamik_adli_artefaktlar_unresolved_olarak_raporlanir` bu davranışı çiviler).
SONUÇ: `DECLARED_SINKS`'e bir satır EKLENEMEZ (anahtarlar `unread` artefakt adlarıyla eşleşir; tarihli
ad hiç artefakt olarak görünmediği için yazılan satır ölü bir muafiyet olurdu — üstelik `stale_sinks`
ihlali doğururdu) ve GEREKMEZ (graf zaten "ihlal" demiyor, "göremiyorum" diyor ve bunu raporluyor).
`codelaw.report()["ok"]` bu yüzden True kalır: `ok`, `unresolved` sayısına DEĞİL, `violations` ve
`unscanned` listelerine bakar.

WATCHDOG'A BAĞLANMADI (ilmek-1'deki v102 kararının aynısı): `DERIVED_SOURCES` (türev bayatlığı) ve
benzeri haritalara bir satır eklemek, seans-dışı her gün ve her hafta sonu SAHTE bayat alarmı
üretirdi — çünkü arşiv yalnız NY seansında (13:30-20:00 UTC) büyür ve akşamdan ertesi açılışa kadar
"kaynak ilerledi, türev ilerlemedi" görünür. Gürültüyle susturulmuş bir dedektör, dedektör değildir.
```

## `meridian/barclock.py`

```text
barclock.py — Intraday LOOK-AHEAD saati (Faz 4). TEK ortak zaman kaynağı + kapanmış-bar admissibility
+ NY seans kapıları. (Faz 2'de K6 ile ertelenmişti; intraday-tüketici fazının BİRİNCİ görevi.)

LOOK-AHEAD YASASININ intraday hâli (Faz 2 look-ahead adverserinin verdiği KESİN kural): bir dakikalık bar
bir karara ancak `close_ts = parse_utc(t) + 60s` VE `karar_anı >= close_ts` iken girer. `t` dakika
BAŞLANGICI olduğundan bara `t` anında değil `t+60s` (dakika KAPANIŞI) sonrasında güvenilir — aksi hâlde
60 sn erken kabul = look-ahead deler. İki damga da BU modülden gelir (tek saat); aksi "aynı zaman iki
kaynak" ayrışmasıdır (bu kod tabanının baskın kusuru).

FAIL-CLOSED: damgasız/biçimsiz bar admissible DEĞİL — bilinmeyen tazelik 'kabul etme' demektir.

Saat ENJEKTE edilebilir (set_clock): testler gerçek zamandan bağımsız admissibility doğrular.
```

## `meridian/barfeed.py`

```text
barfeed.py — DAYANIKLI bar-tetiği tüketicisi (Faz 3, 2026-07-23).

marketstream her dakikalık frame'i `hotstate.ingest_bars` ile yazarken `mrd:barfeed` akışına tek bir
"yeni bar geldi" olayı da XADD eder. BU modül o akışı bir CONSUMER-GROUP ile (XREADGROUP + ACK) okur ve
kayıtlı bir geri-çağrıyı (Faz 4 intraday_cycle buraya bağlanır) uyandırır.

NEDEN consumer-group (bare pub/sub DEĞİL): pub/sub fire-and-forget'tir — tüketici o an düşükse mesaj
KAYBOLUR. Consumer-group teslim edilen ama ACK'lenmemiş olayları tutar; süreç/görev bir an yeniden
başlarsa tetik DÜŞMEZ, son ACK'ten devam eder. "Yeni bar → karar uyandır" kancasının dayanıklı hâli.

NEDEN THREAD (asyncio DEĞİL): redis-py senkron; XREADGROUP block=Nms çağrısı thread'i bloklar. asyncio
görevinde koşarsa uvicorn event-loop'unu (marketstream/mirror/API dahil) dondururdu. Bu yüzden ayrı bir
daemon thread'de koşar — event-loop'a dokunmaz.

Faz 3 KAPSAMI: dayanıklı tetik mekanizması + görünürlük (events_read/lag). Kayıtlı geri-çağrı yoksa
olaylar yalnız SAYILIR ve ACK'lenir (mekanizmanın çalıştığının kanıtı, panoda görünür). Faz 4 gerçek
intraday_cycle'ı `register()` ile bağlar.
```

## `meridian/barrepair.py`

```text
barrepair.py — DİSKTEKİ bar defterlerinden HAYALET SEANS satırlarını temizleyen onarım aracı.

NEDEN AYRI BİR ARAÇ VAR (ve neden kapının kendisi yetmiyor):
`adapters.data.sanitize_bars` kapısı 2026-07-30'da takvim doğrulaması kazandı — o günden sonra
hiçbir hayalet satır belleğe GİREMEZ. Ama diskte ZATEN duran satırlar ancak o sembol yeniden
yazıldığında temizlenir; yazım da yalnız kaynak yeni bir bar verdiğinde olur. Yani düzeltmesiz
bırakılırsa: emekli/bayat semboller hayaleti sonsuza dek taşır, ve `state/bars` üzerinden ÜRETİLMİŞ
artefaktlar (component_ic, cf defterleri, eşik eğrileri) hangi tabandan çıktığı belirsiz kalır.
Bu araç migrasyon adımıdır: bir kez koşar, defterleri kapının bugünkü yasasıyla hizalar.

ÖLÇÜLMÜŞ TABAN (2026-07-30, 259 dosya / 1.344.334 satır — sayım, tahmin değil):
  2025-05-26 (Memorial Day, kapalı) → 258 dosya: 199 birebir kopya, 52 yakın kopya,
                                       7 bölünme-düzeltilmemiş ham fiyat (BKNG ×25 … DD ×0,333)
  2018-11-22 (Thanksgiving, kapalı) → 184 dosya: 169 düz bar (hacim 0), 15 ham fiyat
  Toplam 442 hayalet satır. Geçerli seanslarda izole düzeltilmemiş satır: 3 (CHD/EL/PINS).

İKİ KURAL, İKİSİ DE BİLEREK:
  1. KURU KOŞU VARSAYILANDIR. `--uygula` verilmeden hiçbir bayt yazılmaz; araç yalnız RAPOR basar.
     Veri silen bir aracın varsayılanının yazmak olması, bu depoda yaşanmış hata sınıfıdır.
  2. YAZIM SANCTIONED YOLDAN GEÇER. Satır silmek dosyayı KÜÇÜLTÜR ve `watchdog.determinism_report`
     küçülmeyi haklı olarak "SESSİZ BAR MUTASYONU" sayar — wf-revizyonu bumplanmadıkça. Bu yüzden
     `data._bump_wf_rev()` İLK YAZIMDAN ÖNCE çağrılır (bugünkü veri turunun `_changed_rows` →
     `_bump_wf_rev` deseninin aynısı). Erken bump zararsızdır (yalnız önbelleklenmiş walk-forward'ları
     geçersizler); GEÇ bump ölümcüldür — süreç yazımın ortasında ölürse defterler küçülmüş, revizyon
     sabit kalır ve dedektör haklı olarak alarm basar.

CANLI WORKER KOŞARKEN KOŞMA: `store` kilidi SÜREÇ-İÇİDİR (bu depoda belgeli). Araç, canlı süreci
görürse `--uygula`yı REDDEDER (`--zorla` ile ezilir). Yazımın kendisi atomiktir (`data._write_bars`
→ mkstemp + os.replace), yani okuyucu asla yarım dosya görmez; reddin sebebi yarım dosya değil,
aynı defteri iki sürecin AYNI ANDA yeniden yazmasıdır.

İKİNCİ MOD — `--integrity-tara` (2026-07-31, hayalet-round-2): satır SİLEN onarımın YANINDA, satır
SİLMEYEN bir envanter. Ölçüldü ki kapıdan geçen ikinci bir kusur sınıfı var ve o sınıf tek satır
değil DÖNEMdir: 60 sembolde 97 çözülmemiş ölçek/kimlik kırılması (CHTR ×1158, AVGO ×162, PINS'in
kuruş "geçmişi", GOOGL ×2,6, RTX ×3,8, ABT/DD/HON spinoff'ları, TDG'nin bozuk kesiti). Bu satırlar
SİLİNMEZ — yeni ölçeğin İLK barıdır ve silmek geçmişi delik yapar; kırılmadan ÖNCEKİ dönem
`state/bars_integrity.json` defterinde "ölçüm için güvensiz" damgalanır ve ölçüm yolları
(`component_ic`, `cf_backfill`) o dönemi DEFTERDEN öğrenip dışlar. Yazım yine SANCTIONED yoldan:
defter ölçüm evrenini daraltır, bu yüzden wf-revizyonu bumplanır.

KULLANIM:
    python -m meridian.barrepair                     # kuru koşu — tam envanter
    python -m meridian.barrepair --json              # aynı rapor, makine-okunur
    python -m meridian.barrepair --sembol BKNG,ORLY  # yalnız bu semboller
    python -m meridian.barrepair --uygula            # YAZAR (worker durdurulmuş olmalı)
    python -m meridian.barrepair --integrity-tara    # kırılma envanteri (satır SİLMEZ)
    python -m meridian.barrepair --integrity-tara --uygula   # bars_integrity.json YAZAR (TAM evren)
```

## `meridian/barsarchive.py`

```text
barsarchive.py — `mrd:bars:{T}` akışlarının DAYANIKLI disk arşivi (Faz 5 ham maddesi, 2026-07-29).

NE YAPAR: `mrd:bars:*` Redis Stream'lerini KENDİ consumer-group'uyla okur ve her kapanmış dakikalık
barı `state/bars_intraday/YYYY-MM-DD.jsonl` içine BİR SATIR olarak düşürür. Diske yazım fsync'lenip
BAŞARILI olduktan SONRA XACK atar — arada çökerse giriş PEL'de kalır, yeniden teslim edilir ve
(ticker,t) tekilleştirmesi çift satırı düşürür. Yani en-az-bir-kez teslim + idempotent yazım =
pratikte tam-bir-kez arşiv.

NEDEN ŞİMDİ: `mrd:bars` bir RING'tir — `BARS_MAXLEN=900`, `BARS_TTL_S=172800` (~2 seans). TTL sonrası
o dakika YOKTUR. "Dakika-hassas icra EOD icradan gerçekten daha mı iyi?" sorusu ancak GEÇMİŞ dakikalık
çerçeveler birikmişse cevaplanabilir; birikim bugün başlamazsa üç ay sonra üç aylık olmaz. Arşiv bu
yüzden ölçümden ÖNCE açılır — veri birikimi bileşik getirir, ölçüm sonradan gelir.

--------------------------------------------------------------------------------------------------
CONSUMER-GROUP İZOLASYON KANITI (varsayım değil, Redis semantiği + bu depodaki olgular)
--------------------------------------------------------------------------------------------------
1) FARKLI ANAHTAR. `barfeed.py`'nin grubu (`GROUP = "meridian-intraday"`) `mrd:barfeed` anahtarı
   üzerindedir (hotstate.BARFEED). BU modülün grubu (`GROUP = "archive"`) `mrd:bars:{TICKER}`
   anahtarları üzerindedir. Ortak anahtar YOK → ortak PEL, ortak last-delivered-id YOK. barfeed'in
   ACK'ine dokunmak yapısal olarak imkânsızdır: bu modül `mrd:barfeed`e HİÇ komut göndermez.
2) AYNI ANAHTARDA OLSAYDI BİLE İZOLE OLURDU. Redis'te consumer-group durumu (last-delivered-id +
   PEL) GRUP BAŞINADIR. Bir grubun XREADGROUP/XACK'i başka bir grubun teslim konumunu ilerletmez;
   XADD her gruba bağımsız teslim eder. Yeni grup eklemek mevcut tüketicileri ETKİLEMEZ.
3) MEVCUT `mrd:bars` OKUYUCULARI GRUP KULLANMIYOR. `hotstate.read_bars` XREVRANGE, `hotstate.bars_len`
   XLEN kullanır — ikisi de grup-farkında DEĞİLDİR: ne PEL'e yazarlar ne ondan okurlar. Bu modülün
   grubu onların gördüğü veriyi değiştirmez (XREADGROUP giriş SİLMEZ; ring'i yalnız MAXLEN budar).
4) YAZMA YOK. Bu modül `mrd:*` altında YALNIZ üç komut çalıştırır: SCAN (keşif), XGROUP CREATE
   (yalnız kendi grubu), XREADGROUP/XACK (yalnız kendi grubu). Hiçbir XADD/DEL/EXPIRE yoktur —
   canlı worker'ın yazdığı akışa dokunmaz.

BAŞLANGIÇ KONUMU `id="0"` (barfeed'in `"$"`inden BİLEREK FARKLI): barfeed bir TETİKTİR, geçmişi
replay etmek yanlış olurdu ("60 dakika önceki bar için şimdi karar uyandır" saçmadır). Bu ise bir
ARŞİVDİR: ilk koşuda ring'de HÂLÂ duran ~2 seansı da diske almak, kaybedilecek kanıtı kurtarır.
Tekilleştirme zaten çift satırı imkânsız kıldığı için replay bedelsizdir.

--------------------------------------------------------------------------------------------------
YAZAR TEKLİĞİ — `state/bars_intraday/`
--------------------------------------------------------------------------------------------------
Bu dizine YALNIZ bu modül yazar. Depoda başka hiçbir modül `bars_intraday` adını üretmez
(tests/test_barsarchive_v116.py bunu her koşuda kaynak taramasıyla ÇİVİLER — iddia değil, test).
Dizin YENİDİR; mevcut hiçbir okuyucunun beklentisini değiştirmez.

KOMŞU MODÜLLE İLİŞKİ — `bararchive.py` (DİKKAT: ad bir harf farkla benzer, kasıtlı DEĞİL, devralındı):
`bararchive.py` AYRI ve DAHA ESKİ bir yoldur: `hotstate.ingest_bars` içinden SATIR-İÇİ çağrılır ve
`state/intraday_bars/` altına ÇERÇEVE-şekilli satırlar (`{ts, bars:{ticker:bar}}`) yazar. İkisi aynı
olguyu farklı yollardan saklar ve BİLEREK yan yana durur, çünkü dayanıklılıkları farklıdır:
  - `bararchive` yazımı BİR KEZ dener; istisnayı yutup False döner (ingest'i düşürmemek için doğru
    karardır) — ama o çerçeve o an yazılamazsa TEMELLİ kaybolur. Yeniden deneme yoktur.
  - BU modül Redis ring'ini kaynak alır: yazım başarısızsa ACK ATMAZ, giriş PEL'de kalır ve sonraki
    turda yeniden denenir. Arşivci saatlerce düşse bile ring'de duran (~2 seans) her şeyi kurtarır.
İki arşivin BİRLEŞTİRİLMESİ (ya da `bararchive`ın emekliye ayrılması) bir MİMARİ karardır ve Rol 1'e
aittir; bu tur onu ALMAZ ve `bararchive.py`/`hotstate.py` dosyalarına DOKUNMAZ. Sapma raporlanmıştır.

--------------------------------------------------------------------------------------------------
YASA 6 (üretilip tüketilmeyen artefakt) — BUGÜNKÜ TÜKETİCİ
--------------------------------------------------------------------------------------------------
Bugünkü tüketici `python -m meridian.barsarchive --ozet` (gün/satır/sembol istatistiği) ve
tests/test_barsarchive_v116.py'dir. api/pano bağlantısı BU TURA ALINMADI ve bu bir ihmal değil
BEYANDIR: `api.py` ve `web/app.js` şu anda PARALEL bir ajanın (G2 skor turu) yüzeyindedir; aynı
dosyaya iki yazar = çakışma. Bağlantı SONRAKİ tura ertelendi. YASA 6'nın yasakladığı şey kimsenin
BİLMEDEN bıraktığı okunmayan artefakttır; bilinen, ölçülebilen ve CLI'dan okunan bir artefakt değil.

CODELAW: yazım `store.*` üzerinden DEĞİL, doğrudan `open()`+`fsync` ile yapılır (ACK'ten önce
dayanıklılık gerekir; `store.append_jsonl` fsync ETMEZ). Bu yüzden `codelaw.artifact_graph`'ın
WRITE_CALLS tarayıcısı burada bir artefakt GÖRMEZ — `DECLARED_SINKS`'e satır eklenmez ve gerekmez
(zaten tarihli f-string ad `unresolved`a düşerdi; bkz. bararchive.py'deki 2026-07-27 ölçümü).

SEANS DIŞI: akış boştur. Bekleme SUNUCU TARAFINDA yapılır (XREADGROUP BLOCK) — istemci meşgul döngü
kurmaz. Hiç `mrd:bars:*` anahtarı yoksa XREADGROUP'a verilecek akış da yoktur; o durumda ucuz bir
`idle_s` uykusu vardır (varsayılan 5 sn) ve Redis'e tur başına yalnız bir SCAN gider.
```

## `meridian/baseline.py`

```text
baseline.py — EBEVEYN SÜRÜMÜN TABANINI GERÇEKTEN ÖLÇ (2026-07-26).

Neden var: `rollback.evaluate_outcomes` bugün `no_parent_score` ile açık duruyor. v4'ün ebeveyni
v3'ün karnede ne satırı ne skoru var (re-seed kanıtı yeniden üretir, ata satırı yalnız KARARI taşır
ve skor alanı bilerek boştur — bkz. `run._ancestor_from_history`). Taban yoksa delta yoktur; delta
yoksa hiçbir hipotez terminale ulaşmaz ve kalibrasyon n=0 kalır.

Bu modül tabanı UYDURMAZ, ÖLÇER: ebeveynin `state/history/vNNNN.yaml` anlık görüntüsündeki
parametreleri, adayın geçtiği kapının GÖRDÜĞÜ walk-forward'ın BİREBİR aynısından geçirir
(`reflect._submit_locked` ile aynı düzen: aynı bar seti, aynı pencereler, aynı fold/ambargo).

ÜÇ AYRI ŞEY, ÜÇ AYRI KARAR:
  1. ÖLÇMEK — her zaman yapılır, hiçbir yere yazmaz.
  2. HÜKÜM — ölçüm KARŞILAŞTIRILABİLİR mi? Bir sayının var olması, onun ebeveyn tabanı olarak
     kullanılabileceği anlamına gelmez (aşağıdaki `verdict`).
  3. YAYINLAMAK — karneye yazmak AYRI bir bayrak ister (`publish=True`). Ölçmek yayınlamak değildir;
     yayınlanan taban, canlı sürümün otomatik geri alınmasına yol açabilecek bir KARAR girdisidir.
```

## `meridian/broker.py`

```text
broker.py — the paper broker. Realistic frictions or the agent learns a fantasy (Hard Rule 7).

Contract (§4):
  entry  = next bar OPEN + slippage
  exit   = on stop / target / trail / time-stop / regime-flip
  writes one JSON line per CLOSED trade.

This simulator is driven bar-by-bar by backtest.py and by the live loop (against real bars).
No clock reads, no network — it only knows the bars it is handed.
```

## `meridian/cf_backfill.py`

```text
cf_backfill.py — karşı-olgusal defteri TÜM TARİHE koşturarak doldurur (2026-07-21).

KÖK NEDEN: counterfactual.collect/advance YALNIZ canlı daily_cycle'da çağrılıyor; 2022→bugün replay'i
90 gerçek işlem üretti ama SIFIR karşı-olgusal kanıt — kanıt motoru hiç tarihin üstünden geçmemiş.
Bu modül o boşluğu kapatır: her tarihi seansta daily_cycle'ın P2 (tarama) + P3 (plan+kapı) BLOKLARINI
BİREBİR AYNI CANLI FONKSİYONLARLA (regime.build_regime_json, config.resolve_params, strategy.scan_all,
guard.classify_gate, counterfactual.collect/advance) yeniden koşar — P4/P5 (dolum/kalibrasyon) YÜKÜ
OLMADAN. Sonuç: yüzlerce simüle aday sonucu, bir gecede, tarihten.

DÜRÜSTLÜK:
  • İleri-yönlü sim — cf.advance her satırı yalnız KENDİ giriş-sonrası barlarıyla çözer (look-ahead yok).
  • SIFIR kapı yetkisi — cf yalnız ölçüm besler (skor kalibrasyonu, skill katkısı, near-miss, fidelity);
    hiçbir kararı/kapıyı etkilemez (counterfactual.py yasası).
  • Portföy-BAĞIMSIZ kapı — gate'e düz portföy verilir (0 pozisyon): cf, PER-ADAY seçim kalitesini ölçer,
    o günkü tesadüfi holdinglerin ısı/korelasyon durumunu değil. Bu bilinçli ve dürüst bir seçimdir.
Yeniden mekanizma DEĞİL — mevcut motoru tasarlandığı derinlikte çalıştırma.
```

## `meridian/codelaw.py`

```text
codelaw.py — İKİ STATİK YASA (2026-07-21).

NEDEN VAR: 2026-07-21'de tek günde on üç hata çıktı ve **hiçbiri istisna fırlatmadı**. Denetim
iki YAPISAL taşıyıcı buldu; bu modül ikisini de kaynak koddan, çalışma zamanına hiç dokunmadan
ölçer:

  (4) SESSİZ YUTMA. `except Exception: pass` gerçek bir kusuru sessiz bir MİKTAR DEĞİŞİMİNE
      çevirir. En kötü örneği sessiz-hata dedektörünün KENDİ içindeydi: `starved.append(...)`
      satırı `starved` tanımlanmadan önce duruyordu ve çıplak bir `except Exception: pass`
      `NameError`'ı yutuyordu — yani sessiz hataları bulmak için var olan dedektör sessizce
      başarısız oluyordu. Kaçış yolu vardır ama AÇIK olmak zorundadır: `# sessiz-yutma: <gerekçe>`.
      "Üşendim"i "karar verdim ve nedenini yazdım"a çevirir; bütün mesele bu.

  (6) ÜRETİLİP TÜKETİLMEYEN ARTEFAKT. Yedi desenli bütünlük raporu diske yazıldı, API'den
      servis edildi — ve **hiçbir pano paneli okumadı**. Aynı şekilde `gate_checks` yalnız canlı
      motorda üretildiği için panonun karar-ağacı tablosu 144 satırın 144'ünde boştu. Kimsenin
      okumadığı bir artefakt, üretilmemiş artefakttan ayırt edilemez.

Bu modül SAF DENETİMDİR: durum değiştirmez, karar vermez, diske yazmaz. Yalnız "şu satırda sinyal
üretmeyen bir yakalayıcı var" ve "şu defteri kimse okumuyor" der.

v214 (2026-08-08) — BEKÇİNİN KENDİ ÜZERİNE İKİ EK. İkisi de aynı cümlenin sonucudur: *bir bekçinin
kendi körlüğünü bilmemesi, bekçiliğin tersidir.*
  (a) GÖREMEDİĞİNİ SAY. `artifact_graph` artık her `store` okuma/yazma çağrısını ya çözer ya da
      ADLANDIRILMIŞ bir `unresolved` kovasına yazar (`unresolved_by_reason`), ve gördüğü her
      erişim biçimini sayar (`access_patterns`). Eskiden iki sınıf HİÇBİR SAYACA girmiyordu:
      çıplak-ad çağrısı (`read_json(...)`) ve konumsal argümansız çağrı.
  (b) BEYANIN KENDİSİNİ DENETLE. `declared_claims()` bir muafiyet metninin "üretimde okuyucusu
      yok" iddiasını FONKSİYON-ÇAĞRI düzeyinde sınar. `stale_sinks` bunu yapısal olarak
      yapamıyordu: tetikleyicisi `unread` bayrağıdır ve okuma yazarla aynı modüldeyse bayrak
      hiç düşmez — `sieve.json` beyanı tam bu delikte 6 ay bayat kaldı.
```

## `meridian/component_ic.py`

```text
component_ic.py — BİLEŞEN IC'si: skorun DÖRT HAM PARÇASINDAN hangisi tahmin gücü taşıyor?
(Kârlılık Programı Aşama 1.2, 2026-07-28)

CEVAPLADIĞI SORU. `score_calibration` tek bir soru sorar: 0-100 bileşik skor sonucu öngörüyor mu?
Canlı cevap "hayır" (gerçek katman IC 0.049, gürültüden ayrılmıyor). Ama bileşik skor DÖRT ayrı
büyüklüğün ağırlıklı toplamıdır ve o toplam, içindeki bir sinyali diğer üçünün gürültüsüyle
söndürebilir. "Skorun IC'si sıfır" ile "skorun hiçbir parçası bilgi taşımıyor" AYNI CÜMLE DEĞİLDİR
— ve ikisini ayırmadan ağırlıkları (entry.w_*) hangi yöne çevireceğimizi bilemeyiz. Bu modül dört
parçayı ayrı ayrı, üç ufukta ve katman etiketli ölçer.

SIFIR YETKİ. Hiçbir kapıya, hiçbir karara, hiçbir silahlanmaya girmez — yalnız rapor yazar
(`state/component_ic.json`) ve pano/evidence_pack onu okur. Bir bileşenin IC'si yüksek çıksa bile
ağırlığı ancak olasılıksal kapıdan geçen bir hipotezle değişebilir.

--- ÜÇ TASARIM KARARI, ÜÇÜ DE ÖLÇÜMÜ DEĞİŞTİRDİĞİ İÇİN BURADA YAZILI ---

(1) BİLEŞENLER DEFTERDE YOK, BARLARDAN YENİDEN HESAPLANIR. Denetlendi: `tt`, `vr`, `proximity_pct`
    hiçbir deftere ALAN olarak yazılmıyor — yalnız `candidates.jsonl`in `notes` metninde
    ("prox=1.2% vr=2.1 tt=0.83") ve orada da 313 satırın 13'ünde (replay yazıcısı `notes`u düşürüyor).
    Bir string'i regex'le ayrıştırıp istatistik kurmak, ölçümü metin biçimine bağımlı yapardı.
    Bunun yerine bileşenler `meridian.indicators`ın AYNI fonksiyonlarıyla bardan yeniden üretilir —
    yani ölçümün kaynağı, canlı skorun kaynağıyla aynı koddur (tek yasa, tek uygulama).
    Göstergelerin hepsi nedensel (causal) yuvarlanan pencerelerdir ve en uzun pencere 252 bar; canlı
    yol 340 barlık kuyrukta hesapladığı için TAM SERİDE hesaplanan değer aynı barda BİREBİR aynıdır.

(2) İLERİ GETİRİ SABİT UFUKTA VE YÜZDE — R DEĞİL. Defterdeki `r_multiple` işlemin KENDİ çıkışında
    ölçülür; çıkış süresi işlemden işleme değişir (canlı defterde 1 ile 15 bar arası). Değişken
    ufuklu bir getiriyle bileşen IC'si ölçmek, sinyalin gücünü çıkış kuralının davranışıyla
    KARIŞTIRIR — ki bu turun asıl sorusu tam da o ikisini ayırmak. Ufuk sabitlenir (5/10/20 bar) ve
    getiri sinyal barının kapanışından ölçülür: `close[t+h]/close[t] - 1`. Bu, sinyalin ÖNGÖRÜ
    içeriğidir; icra (giriş kayması, stop, trail) ölçümün dışında kalır ve orası ayrı bir sorudur.
    R'ye bölmek ayrıca satır başına farklı bir ölçekleyiciyle bölmek demekti — Spearman monoton
    dönüşüme dayanıklıdır ama satır-başına-farklı bir bölen monoton dönüşüm DEĞİLDİR.

(3) HAVUZ KATMANI TEKİLLEŞTİRİLİR. Alınmış (taken) bir cf satırı ile ona karşılık gelen gerçek
    işlem AYNI (ticker, tarih) gözlemidir; bileşen değeri de ileri getirisi de bardan geldiği için
    İKİSİ BİREBİR AYNI çifti üretir. `score_calibration`ın havuzu bunları iki kez sayar (orada
    y ekseni farklı: gerçek çıkış R'si ile sim çıkış R'si gerçekten iki ayrı ölçümdür). Burada ise
    aynı sayıyı iki kez saymak paydayı şişiren düpedüz bir yalan olurdu — havuz (ticker, tarih)
    anahtarında tekilleştirilir, gerçek katman önceliklidir.

(4) CF KATMANI BU TABLODA SADAKAT SORUSUNDAN BAĞIMSIZDIR (2026-07-29, Aşama 1.4'ün karar girdisi).
    Bu, deponun her yerinde geçerli olan "cf sayıları simülasyondur, hüküm taşıyamaz" kuralının
    GEREKÇELİ ve DAR bir istisnasıdır; gerekçe yazılı olmazsa istisna sessizce genelleşir.
    cf defterinin bilinen kusuru ÇIKIŞ tarafındadır: `cf.advance` yalnız stop/target/time_stop
    simüle eder (trail/breakeven/chandelier/giveback/regime_flip/scale_out ve komisyon/ADV/impact
    YOK — bkz. `analytics.CF_EXIT_FIDELITY_NOTE`). Bu kusur, cf satırının `r_multiple`ını —
    yani ÇIKIŞTA ölçülen her büyüklüğü — kirletir. Bu modülün y ekseni ise `r_multiple` DEĞİL:
    ileri getiri, sinyal barının kapanışından BAR SERİSİNDEN hesaplanır (`close[t+h]/close[t]-1`).
    Yani cf satırından alınan tek şey GİRİŞ ANIdır (ticker + tarih); geri kalan her şey barlardan
    gelir ve o barlar gerçek işlemlerinkiyle AYNI barlardır. Bir çıkış kuralının simüle edilip
    edilmemesi, giriş barından 5/10/20 bar sonraki fiyatı DEĞİŞTİRMEZ.
    Bunun bedeli n≈95 → n≈2100'dür: gerçek katmanda her hücrenin güven aralığı ±0.20 genişliğinde
    ve HİÇBİR hücre anlamlı değil; cf katmanında aralık ~±0.043'e iner. Aşama 1.4'ün ("hiçbir
    bileşen anlamlı IC taşımıyorsa tez revizyonu") cevaplanabilir olması için gereken örneklem
    yalnız buradan gelebilir — gerçek defter aylarca 100'ün altında kalacak.
    SINIR: cf katmanı hâlâ ALINMAMIŞ hipotetik girişlerdir (seçim yanlılığı sorusu ayrı ve açık
    durur) ve bu yüzden tabloda AYRI SATIR olarak, "sim" etiketiyle görünür — gerçek katmanla
    aynı kefeye konmaz, yalnız yanında durur.

(5) TABLO ARTIK YEDİ BİLEŞENLİ (G2, 2026-07-29). Başlıktaki "dört parça" 1.4 karar kapısının
    girdisiydi; kapı "ağırlık ayarı değil YENİDEN İNŞA" hükmünü verdi ve üç yeni aday (rvol20,
    mom12_1, rmom) buraya eklendi. Eski dördü SİLİNMEDİ: bir çekirdeğin diğerinden iyi olduğu
    ancak ikisi aynı popülasyonda, aynı ufuklarda ve aynı CI disiplininde yan yana durursa
    söylenebilir. Yeni satırların ölçek beyanı (ham seri mi, skora giren dönüşüm mü) COMPONENTS
    tanımının yanında ve çıktının `yeni_bilesen_notu` alanında yazılıdır.

(6) EMPİRİK-BAYES SÜTUNU PARALELDİR, YERİNE GEÇMEZ (WP-M 2C, 2026-08-01). Çıktıya `eb` alanı
    eklendi: her hücrenin ham IC'sinin yanında, o katmanın ortak ortalamasına küçültülmüş ikizi
    (`eb_ic`) ve küçültme katsayısı (`shrink_katsayisi`). `tablo` sözlüğü BİT-BİT AYNI kalır;
    bugünün okuyucuları (beyin `compact_lines`, pano, `yeniden_uret` farkı) ham `ic` okumaya
    devam eder. Gerekçe, σ yasası ve beyan edilen sınır `_eb_blok`un üstündeki blokta.
```

## `meridian/config.py`

```text
Central config + path resolution. Loads the immutable goal.yaml/bounds.yaml and the
mutable strategy.yaml. Nothing here talks to a broker or the network.
```

## `meridian/counterfactual.py`

```text
counterfactual.py — Karşı-olgusal defter (öneri #1). Motorun ANA darboğazı kanıt bant genişliği:
tarayıcı her gün ~50 ticker için tam plan kuruyor ama yalnız alınan 1-2 işlem etiket üretiyor. Bu modül
alınmayan her tam-şekilli adayı — NO_GO/REVIEW kalanları, slot yetmeyenleri VE uyuyan kurulumların
ateşlemelerini (küme ARMED_SETUPS'tan TÜRER; momentum_burst 2026-08-12'de silahlandı, bugün uyuyan
olarak episodic_pivot/pead/canslim kalır) — simüle bracket ile sonuna kadar izleyip ayrı bir
deftere yazar: girer miydi, stop mu hedef mi, kaç R, MFE/MAE.

YASA AYNASI: giriş, motorun birebir yasasıyla simüle edilir (bir SONRAKİ seans açılışı; boşluk
korumaları MAX_ENTRY_GAP_PCT ve stop-altı açılış; slipaj fiyatın içinde). Çıkış ise STATİK bracket'tır:
sert stop / hedef (stop-önce muhafazakârlığı, broker._touch_exit ile aynı sıra) + zaman stopu.
Trail / scale-out / rejim-dönüşü çıkışları BİLEREK yok — amaç seçilim kalitesini ölçmek, birebir
P&L kopyası değil; bu sapma dürüstçe burada belgelidir.

SIFIR YETKİ: bu defter hiçbir kapı kararına kanıt OLAMAZ (seçilim yanlılığı + doldurma gerçekçiliği
eksik). Yalnız gölge katmanları besler: gölge modelin eğitim seti, uyuyan kurulumların silahlanma
ölçümü, skor kalibrasyonu (analytics). Yetkisizlik test-zorlamalıdır (test_evidence_v4).
```

## `meridian/dataset.py`

```text
dataset.py — shared loader + backtest windows for the replay universe. One place so reflect.py
and run.py evaluate on identical data/splits. Warmup year (2021) precedes the IS window so the
252-day trend template is valid from the first tradable day.
```

## `meridian/dbmigrate.py`

```text
dbmigrate.py — DOSYA DEFTERİ → SQLite, PARİTE KANITIYLA (WP-H/H9, Kademe A4).

NE YAPAR. Altı varlığı (`trades.jsonl`, `trade_plans.jsonl`, `scoreboard.json`, `portfolio.json`,
`equity_curve.json`, `shadow_books.json`) `state/meridian.db`ye taşır. İLERİ YÖNLÜ ve İDEMPOTENT:
ikinci koşu hiçbir şeyi tekrarlamaz, aynı raporu üretir.

KURU KOŞU VARSAYILANDIR. Veri taşıyan bir aracın varsayılanı yazmak olamaz (`barrepair` /
`ledgerstamp` ile aynı kural). `--uygula` olmadan tek bayt yazılmaz; kuru koşu ne taşınacağını
SAYAR ve KAYNAK PARİTE-DİGESTİNİ basar.

PARİTE KANITI ZORUNLUDUR — İDDİA DEĞİL ÖLÇÜM. Her varlık için:

    JSON kaynak → DB'ye yaz → DB'den TEKRAR oku → yeniden serileştir → normalize digest

İki digest EŞİT DEĞİLSE migrasyon BAŞARISIZ sayılır ve TAMAMI geri alınır (altı varlık TEK
transaction'dadır — yarısı taşınmış bir defter, taşınmamış bir defterden daha tehlikelidir).
Digest anahtar sırasına duyarsızdır (`sort_keys`) ama DEĞERE ve TİPE duyarlıdır: SQLite'ın tip
afinitesi bir int'i float'a çevirseydi (60 → 60.0) bu ölçüm onu YAKALAR. Bu yüzden `storage`
tip uyuşmazlığında alanı ayrıca `extra_json`a yazar ve okumada `extra_json` kazanır.

KAYNAK DOSYALAR SİLİNMEZ. Taşıma sonrası aynı dizinde `.migrated` son-ekiyle bırakılır. Silmek,
geri dönüşü olan bir adımı geri dönüşü olmayan bir adıma çevirirdi. (Adı değiştirilir, çünkü aynı
anda İKİ okunabilir gerçek kaynağı bırakmak, hangisinin doğru olduğunu belirsizleştirirdi.)

GERİ DÖNÜŞ KOLU `--geri-al`DIR, `MERIDIAN_DB=off` DEĞİL (C5, 2026-08-02 — bu başlık eskiden anahtarı
"acil anahtar" diye anıyor ve dosyaların DURMASINI yeterli sayıyordu; YANLIŞTI). Dosyalar `.migrated`
ADIYLA duruyor, yani anahtarı tek başına çeken operatör altı defteri BOŞ okur (kanonik ad yok →
çağıranın varsayılanı) ve ilk yazımda AYRIŞIK ikinci bir kitap doğar. `--geri-al` bu adımı bir kola
indirir: DB kenara alınır (`meridian.db.rolledback-<ts>`), arşivler ASIL adlarına döner, ve DB ile
dosya satır sayıları YAN YANA raporlanır.

GERİ-AL VERİ SİLMEZ, YALNIZ YENİDEN ADLANDIRIR. Üç şey birden korunur ve üçü de rapora yazılır:
(1) DB dosyası (`.rolledback-<ts>`) — migrasyondan SONRA yazılanların TEK kopyası ondadır, o yüzden
kenarda tutulur ve fark (`db_n − dosya_n`) operatörün önüne basılır; (2) `.migrated` arşivi asıl
adına döner; (3) kanonik adda ZATEN bir dosya varsa (anahtar çekiliyken doğmuş ayrışık kitap) o da
silinmez, `.ayrisik-<ts>` ekiyle kenara alınır. Hüküm tek cümledir: geri-al'dan sonra defterler
DOSYADAN, migrasyon ÖNCESİ hâliyle okunur; başka her şey kenarda, adıyla durur.

CANLI WORKER KOŞARKEN YAZMA. `ledgerstamp`/`barrepair` ile AYNI desen ve AYNI ölçüm fonksiyonu:
canlı süreç görülürse `--uygula` VE `--geri-al` REDDEDİLİR (`--zorla` ile ezilir).

KULLANIM:
    python -m meridian.dbmigrate                 # kuru koşu — sayım + parite digestleri
    python -m meridian.dbmigrate --json          # aynı rapor, makine-okunur
    python -m meridian.dbmigrate --uygula        # TAŞI (worker durdurulmuş olmalı)
    python -m meridian.dbmigrate --durum         # yalnız DB durumu (şema sürümü, varlık sayaçları)
    python -m meridian.dbmigrate --geri-al       # GERİ DÖN: DB kenara, arşivler asıl adına
```

## `meridian/earnings.py`

```text
earnings.py — the earnings blackout. A swing-momentum entry taken right into an earnings print
is a coin flip on a gap, not an edge (Hard Rule 7: no fantasy fills). If state/earnings.csv exists
(rows: ticker,date  — one scheduled report date per line, YYYY-MM-DD), a plan whose date falls within
BLACKOUT_DAYS *before* the next scheduled report is not armed. No CSV -> no-op, so the gate is present
and testable now and simply activates the day an earnings feed (FMP) writes the file. Deterministic,
network-free: it only reads the file it is handed.
```

## `meridian/faz5_cikis.py`

```text
faz5_cikis.py — FAZ-5 ÇIKIŞ ÖLÇÜMÜ: dakika-hassas icranın CI'lı kazancı (kart EXE-2026-002).

NEDEN VAR. `health.faz6_kilitleri`nin ÜÇÜNCÜ kilidi (`faz5_cikisi`) bugüne kadar SABİT `False` /
`olculemedi` yazıyordu ve gerekçesi kendi kodunda duruyordu: "Faz-5 çıkış ölçümünü (dakika-hassas
icranın CI'lı kazancı) ÜRETEN kod yok". Merdivendeki dört kapalı kilidin üçü KANIT eksikliğinden
kapalıdır (edge 1/5, sonuç 0/4, DSR 1e-06) ve kodla açılamaz — kârlı işlem geçmişi ister. Bu kilit
TEK istisnaydı: kapalı olma sebebi ÖLÇÜMÜN YOKLUĞUydu. Bu modül o ölçümü üretir. Kilit bundan sonra
da kapalı kalabilir, ama gerekçesi "üreten kod yok"tan ÖLÇÜLMÜŞ bir cümleye döner ("örneklem 4/20"
gibi) — ve ikincisi zamanla kendiliğinden dolar, birincisi dolmaz.

NEDEN AYRI MODÜL, `analytics.py` DEĞİL (üç ölçülmüş sebep, bir tercih değil):
  1. `tests/test_wpm_sasi_v173::test_A_analytics_KENDI_bootstrapini_DEVRETMEDI` AST seviyesinde
     çivileniyor: `analytics.py` `olcum_araclari`yı import ETMEZ. Gerekçe yayımlanmış sayıların
     korunmasıdır (`analytics._blok_bootstrap_ci`, CIRCULAR blok=5 İŞLEM, `result_verdict`in
     tabanı). Bu ölçüm bir bootstrap ister; analytics'e konsaydı ya çivi kırılırdı ya da analytics
     içinde ÜÇÜNCÜ bir bootstrap gövdesi doğardı — ikisi de o testin engellediği sınıf.
  2. OKUDUĞU DEFTER FARKLI. `edge_verdict`/`result_verdict` KAPANMIŞ İŞLEM defterini okur
     (trades + kalibrasyon) ve "kenar var mı / para var mı" sorusuna R ve DOLAR biriminde cevap
     verir. Bu ölçüm 4b GÖLGE defterini okur ve "dakika-hassas GİRİŞ, EOD zamanlamasına göre ne
     kazandırırdı" sorusuna BPS biriminde cevap verir. Ortak tek şey hükmün tüketicisidir
     (Faz-6 zinciri), gövdesi değil.
  3. `health.faz6_kilitleri` üç hesabı ZATEN geç-import ile alıyor (`analytics`, `validation`,
     `dataset`). Dördüncüsü aynı desenle gelir; `analytics` içine konsaydı 4.173 satırlık dosyanın
     ithal maliyeti hiç değişmezdi ama kartın ölçümü onun yayımlanmış yüzeyine karışırdı.
Modülün adı kilidin adıyla AYNI (`faz5_cikisi` ↔ `faz5_cikis.py`): kilidi panoda gören okuyucu,
sayının hangi dosyadan geldiğini aramak zorunda kalmasın.

EŞİKLER KARTTAN GELİR VE KOD BUNLARI DEĞİŞTİREMEZ (`research/cards/EXE-2026-002-faz5-cikis-
olcumu.yaml`, ölçümden ÖNCE donduruldu): n_min = 20 · %95 · TARİH-KÜMELİ bootstrap 10.000 ·
kazanç E3 maliyet bandının ÜSTÜNDE. `kill_criteria` dokunulmazdır. Ölçüm sonucu hoşa gitmediğinde
değişecek olan şey eşik değil, hükümdür.

METODOLOJİK SINIR (kartta yazılı, burada YUMUŞATILMAZ). 4b'nin `sim_fill`i GÖZLENMİŞ bir dolum
DEĞİLDİR: `max(bar_open, entry_trigger)` kuralıyla ÜRETİLMİŞ bir modeldir; iç EOD dolumu da bir
simülasyondur. Yani BİRİNCİL karşılaştırma MODEL-MODEL'dir ve ölçtüğü şey ZAMANLAMA etkisidir,
gerçek icra kalitesi değil. İkisi de AYNI maliyet modelini taşır, fark yalnız zamanlamadan gelir.
Gerçek Alpaca dolumlarıyla kıyas AYRI bir satırdır (`gerceklik_capasi`), hüküm VERMEZ ve
`hukme_girmez: True` ile damgalanır — bir modeli gerçekle kıyaslamak modeli KAYIRIR.

BU MODÜL SAF OKUMADIR: hiçbir dosyaya yazmaz, hiçbir bayrağı çevirmez, hiçbir emir yolu açmaz.
```

## `meridian/guard.py`

```text
guard.py — the real constraint layer. An instruction to an LLM is a suggestion; a validator is
a constraint (Hard Rule 6). Every rule stated to Hermes is enforced here.

Two surfaces:
  validate_change(proposal, ...) — static validation of a parameter hypothesis (no backtest)
  check_trade(plan, portfolio, regime, goal) — runtime risk-envelope check for a would-be entry
Every rejection carries a machine-readable reason and is written back by memory.py.
```

## `meridian/health.py`

```text
health.py — heartbeat, stale-data detection, kill-switch, circuit-breaker state. A silent agent
is an unmonitored agent (§9). The kill-switch is a file: touch state/HALT and new entries stop
within one bar (§0/§11).
```

## `meridian/hermes.py`

```text
hermes.py — the brain. Reads state, forms ONE single-variable hypothesis with Claude, and
submits it through the SAME guarded pipeline the deterministic proposer uses (guard -> backtest
gate -> version bump -> memory). Hermes never edits strategy.yaml by hand; the engine decides what
ships. Every constraint stated to Hermes here is ALSO enforced in guard.py (Hard Rule 6) — this
prompt is a suggestion, guard.py is the law.

Runs on the VM in a detached tmux session (installed LAST, §7). Falls back to the deterministic
proposer when HERMES_API_KEY is absent, so the loop is never dead.
```

## `meridian/hermes_composite.py`

```text
hermes_composite.py — BİLEŞİK ÖNERİ YOLU (Hermes paketi H3 + H4, 2026-07-30).

SORUN. Tek-değişken yasası (`goal.one_variable_only`) kapının temel disiplinidir ve KALKMAYACAK:
iki düğmeyi birlikte oynatıp iyileşme görmek, hangisinin işe yaradığını ÖLÇMEZ. Ama yasanın bir yan
etkisi vardı: hermes bir bileşik fikir ürettiğinde (ör. "stop_mode=1 İLE stop_buffer_atr=0.4 birlikte
anlamlı") o fikir guard'da REDDEDİLİP ÇÖPE gidiyordu. Fikrin kendisi bilgiydi; kaybı ölçülmemiş bir
kayıptı.

ÇÖZÜM (H3). Bileşik öneri guard'ı ATLAMAZ ve canlıya GİTMEZ — bir KUYRUĞA yazılır
(`state/composite_queue.jsonl`, ledgers sözleşmeli). Kuyruk, `prescreen --composite` yolunun (2026-07-30
sadeleştirme turunda inen resmî bileşik ölçüm yolu) girdisidir. Yani bileşik fikir tek-değişken
yasasını gevşetmez; ÖLÇÜLMEK üzere sıraya girer ve ship yolu yine kapı + operatördür.

ÇÖZÜM (H4). Kuyruk kendi kendine boşalmazsa yine kopuk kablodur. Gece döngüsü kuyruğa bakar ve
HAFTALIK YOKLAMA BÜTÇESİ içinde (WEEKLY_PROBE_BUDGET = 3) prescreen'i AYRI BİR ARKA PLAN SÜRECİNE
spawn eder — gece döngüsünü BLOKLAMAZ (`ops/barsarchive-run.sh` nohup deseni). Bütçe neden var:
her ölçüm bir DENEMEDİR ve aşınma defterine/DSR'ye N olarak girer; sınırsız otomatik yoklama,
deflasyonu kendi eliyle şişirip her adayı imkânsızlaştırır. Bütçe sayacı bu yüzden aşınma defteriyle
AYNI dili konuşur: her ölçüm `k_probes` beyanıyla kaydedilir.

HALKANIN KAPANIŞI (C14, 2026-08-02). "Sonucu deftere yazar" cümlesinin KARŞILIĞI 2026-08-02'ye kadar
KODDA YOKTU: `spawn_pending` satırı `measuring` damgalıyor, prescreen sonucu yalnız `--workdir`e
yazıyor ve kimse geri okumuyordu — yani `measured` yazan tek bir üretim yolu yoktu, `n_olculen`
yapısal olarak hep 0'dı ve ölmüş bir süreç sonsuza dek "ÖLÇÜLÜYOR" görünüyordu (nous_eval._akibet
beyne her hafta aynı yalanı taşıyordu). İKİ KABLO ÇEKİLDİ:
  (a) KİMLİK TAŞIMASI — `spawn_pending` alt sürece `--queue-id <id>` geçirir; prescreen ölçüm
      bitişinde AYNI kimliğe `mark(id, "measured", result=özet)` yazar (bkz. prescreen.kuyruk_geri_yaz).
  (b) ÖLÜ SÜREÇ TOPLAMA — `reap_measuring()` her gece kancasında (spawn_pending'in İLK adımı)
      'measuring' satırların pid'ini yoklar; ölmüş süreç `measure_failed` damgasını alır. Sessiz
      asılı satır YOKTUR: ne damgalanabilen ne damgalanamayan hâl sessizdir.

YASALAR: bu modül KARAR VERMEZ. Kuyruğa yazar, bütçeyi sayar, süreci başlatır, sonucun defterdeki
kimliğini taşır ve ölmüş ölçümü damgalar. `passes` semantiğine, tek-değişken yasasına ve kapı
eşiklerine DOKUNMAZ.
```

## `meridian/hermes_runtime.py`

```text
hermes_runtime.py — in-process supervisor for the Hermes reflection brain, for LOCAL running. On app
open (serve.sh sets MERIDIAN_AUTOSTART_HERMES=1) a daemon thread runs a standby loop: it watches the
heartbeat and reflects when `reflection_every` new trades have closed and the system is healthy (not
halted, not stale). The operator can also trigger one cycle on demand via reflect_now(). Every
reflection goes through reflect.submit → the backtest gate decides; the brain only proposes. A single
reflection lock guarantees the standby loop and a manual trigger never run two reflections at once.
Status mirrors to state/hermes_status.json for the dashboard's Hermes section.
```

## `meridian/hotstate.py`

```text
hotstate.py — Redis SICAK-DURUM katmanı (intraday, 2026-07-23, operatör mimari isteği).

NEDEN: intraday (dakikalık bar) için son fiyatlar / açık pozisyonlar / emirler saniyeler içinde,
defalarca okunur. Bunları her seferinde JSON dosyadan okuyup parse etmek (counterfactuals 4.9M değil
ama portfolio/heartbeat her tick) EOD kadansında sorun değildi; dakikalık döngüde I/O darboğazı olur.
Redis in-memory bu okumaları ~ms'e indirir.

İKİ SIKI İLKE — bu kod tabanının dürüstlük/denetlenebilirlik kimliğini korur:

  1. REDIS UÇUCUDUR, KALICI GERÇEK DEĞİL. İşlemler, kararlar, cf, hipotezler HÂLÂ store.py JSON/JSONL
     defterlerinde yaşar — 7 katmanlı bütünlük/provenance dedektörü onları okur, grep'lenir, denetlenir.
     Redis yalnız TÜREV/UÇUCU tutar: son fiyat, pozisyon/emir SICAK KOPYASI, hesaplama cache. Redis
     tamamen silinse bile hiçbir kalıcı gerçek kaybolmaz — kaynak dosyadır, Redis hızlı okuma katmanı.

  2. GRACEFUL DEGRADATION. Redis yoksa/çökse sistem DURMAZ: her okuma None döner (çağıran dosyaya
     düşer), her yazma sessizce no-op'lar ama bir kez olay yazar. `mirror_stream`'in "sahte güvenli-
     başarısızlık değil, görünür başarısızlık" dersi: down durumu health()'te ve panoda görünür.

Anahtar şeması (hepsi `mrd:` önekli, TTL'li — bayat sıcak veri birikmesin):
  mrd:price:{TICKER}   → hash {price, ts}          (son işlem/bar fiyatı; yazan: ingest_bars)
  mrd:pos              → hash {TICKER: json}        (açık pozisyon sıcak kopyası)

`mrd:ord` (açık emir sıcak kopyası) BEYANI KALDIRILDI (kopukluk avı, 2026-07-30): şema burada
yazılıydı ama bu anahtara yazan/okuyan TEK BİR fonksiyon bile yoktu — yani belge, var olmayan bir
katmanı var gibi gösteriyordu. Ölü bir şema beyanı yalnız fazlalık değildir: sonraki okuyucuyu
"emirler zaten sıcak katmanda" diye yanlış yönlendirir. Açık emirlerin gerçek kaynağı
`broker_reconcile.json` + `mirror_stream`'dir. Emir sıcak kopyası gerçekten gerekirse şema o gün,
yazan fonksiyonuyla birlikte gelir.

YALNIZ-YAZILIR KATMAN KARARI (aynı tur): `mrd:price` ve `mrd:pos`ın PRODÜKSİYONDA HİÇBİR OKUYUCUSU
yok — `get_price`/`get_positions` yalnız testlerden çağrılıyor (statik tarama: 2026-07-30). EOD
döngüsündeki iki yazım noktası (loop._save_broker → cache_positions, loop.daily_cycle → set_prices)
bu yüzden DEVRE DIŞI bırakıldı; gerekçe ve geri açma yolu loop.py'deki iki yorumda. Fonksiyonlar
BURADA KALIR (silinmedi): 4b/pano tüketicisi geldiği gün kanca tek satırdır. `mrd:price`ın intraday
yazıcısı (`ingest_bars`) DEĞİŞMEDİ — kapanmış bar → sıcak fiyat TEK yazma yolu hâlâ oradadır.
```

## `meridian/indicators.py`

```text
Pure technical indicators over closed OHLCV bars. No I/O, no clock. numpy/pandas only.
Every function here is deterministic and used identically in live and backtest paths.
```

## `meridian/integrity_registry.py`

```text
integrity_registry.py — BİLEŞEN × DESEN kapsam kaydı (2026-07-21).

Sorun: "gözden kaçan çok fazla eksiklik olabilir" — ve haklı. Bugün bulunan 8 sessiz hatanın 8'i de
mevcut testlerden geçti. Çözüm her modüle özel test icat etmek DEĞİL; çünkü hatalar bileşen değişse de
DESEN olarak tekrar ediyor. Bu kayıt, 50 modülü 6 değişmez-deseniyle çaprazlar:

  ÜRETKENLİK  — çıktı üretiyor mu?                (cf defteri ömrü boyunca boştu)
  KORUNUM     — giren kayıtlı terminale ulaşıyor mu? (silahlı plan kayıtsız buharlaştı)
  DETERMİNİZM — aynı girdi aynı sonucu mu veriyor?   (havuz işçileri barları yeniden yazıyordu)
  TUTARLILIK  — türev kaynağından taze mi?           (gölge model 7115 satırı görmedi)
  MONOTONLUK  — ileri-only nicelik geri gidiyor mu?  (kitap geriye sardı)
  SAHİPLİK    — yazan, sahibi olmadığı alanı eziyor mu? (nabız ezilmesi)

BU KAYDIN AMACI: bilinmeyen yüzeyi SONLU ve GÖRÜNÜR kılmak. "Nereye bakmadık?" sorusunun cevabı
artık bir tahmin değil, bir tablo. Dürüstlük kuralı: bir hücre ancak GERÇEK bir kontrol/test varsa
'covered' işaretlenir — iyi niyet 'covered' saymaz.
```

## `meridian/intraday_cycle.py`

```text
intraday_cycle.py — Faz 4 KAPANMIŞ-BAR TÜKETİCİSİ (GÖZLEM-MODU / Faz 4a).

barfeed her yeni-bar olayında `on_barfeed_event`i uyandırır. GÖZLEM-MODU (SIFIR YETKİ): admissible
(kapanmış) dakikalık barlarda GÜNÜN TÜM PLANLARININ TETİK-GEÇİŞİNİ ölçer ve `intraday_decisions.jsonl`e
3 damgalı (decision_as_of / bar_t / close_ts) yazar. Emir GÖNDERMEZ, CANLI DEFTERİ fill ETMEZ,
portfolio.json'a DOKUNMAZ.

TÜM PLANLAR (sadeleştirme turu, 2026-07-30): gözlem katmanı bugüne dek YALNIZ `portfolio.json.armed`
listesindeki planları izliyordu. Canlıdaki ölçüm sonucu: son EOD turunda 10 plan üretildi, 0'ı
silahlandı, açık pozisyon yok → izlenen ticker sayısı SIFIR, yani aç bir intraday yığını hiçbir kanıt
biriktirmiyordu. Faz 5/6'nın ("dakika-hassas icra EOD'ye ne katardı?") kanıt tabanı silahlanma
kuraklığına rehin kalıyordu. Artık ilgi kümesi GÜNÜN PLAN ÜRETİMİNİN TAMAMIdır (en son EOD turunun
`trade_plans.jsonl` satırları) ∪ açık pozisyonlar ∪ silahlı planlar.

YETKİ FARKI KAYBOLMADI — SATIRDA ETİKET OLARAK DURUR: `eod_armed` alanının anlamı BİREBİR aynıdır
("bu plan portfolio.json.armed içinde mi"), yanına `plan_source` ("armed" / "planned") eklendi.
Silahsız bir planın tetik geçişini ÖLÇMEK, onu silahlandırmak değildir: bu dosya hâlâ hiçbir emir
göndermez ve INTRADAY_ARM bayrağına dokunmaz.

4B GÖLGE ARTIK İKİ KOLLU (kart EXE-2026-003, v217 — 2026-08-09). 2026-07-30'da gölge kancası
BİLEREK yalnız SİLAHLI planda çalışıyordu; gerekçe `vs_eod` eşleştirmesinin sulanmamasıydı ve o
gerekçe kalkmadı, ÇÖZÜLDÜ: yeni kol (`kol: planli`) AYRI BİR DEFTERE yazıyor
(`intraday_shadow.PLANLI_ORDERS_FILE`), silahli kolun defteri ve onu okuyan iki ölçüm (`vs_eod`,
`faz5_cikis`/EXE-2026-002) bayt düzeyinde DEĞİŞMEDİ. Yeni kolun `store.append_jsonl` çağrısı bu
dosyadadır; hesabı gölge katmanı yapar (gerekçe kancanın yanında yazılı).

GÖLGE KATMANI (Faz 4b, 2026-07-27): tetik KESİLDİĞİNDE `intraday_shadow.record` çağrılır ve o anın
TAM icra kararı (kapılar + boyutlandırma + emir niyeti) hesaplanıp kendi defterine yazılır. Sıfır
yetki cümlesi gölgeyi de kapsar: gölge boyutlandırmayı KOPYA bir PaperBroker üzerinde simüle eder
ve nesneyi atar — canlı defter fill EDİLMEZ, emir gönderilmez, INTRADAY_ARM bayrağına dokunulmaz.
Kanca bilerek minimaldir: look-ahead mantığı (admissible bar + as_of) burada zaten çözülmüştür ve
gölge onu İKİNCİ kez yazmaz, hazır üçlüyü (plan, bar, as_of) devralır.

NEDEN GÖZLEM-ÖNCE (Faz 4 tasarım sentezi): (1) mrd:bars öğrenmeye/backtest'e girmez → dakikalık kararın
OOS kanıtı YOK; (2) strateji GÜNLÜK-kalibre (252-bar ısınma, haftalık resample, time_stop_days) → ham
dakikalık barda 'karar' KATEGORİ HATASIDIR; (3) otonom intraday silahlanma yeni ve SONUÇLU (arming.py:
'silahlanma otomatik değildir'). Gerçek silahlanma (Faz 4b) YALNIZ operatörün elle açtığı
state/INTRADAY_ARM bayrağı + EOD ile BİREBİR aynı güvenlik kapılarıyla açılır.

FAZ 4B GÖNDERİM BACAĞI ARTIK VAR (İCRA turu, operatör onayı 2026-08-11 — P-2026-08-07-VLO vakası):
`_faz4b` yalnız INTRADAY_ARM açıkken, SİLAHLI kolun gölge satırı `would_submit` dediyse ve plan
icra-uygunsa ((setup ARMED_SETUPS'ta VE kapı GO) YA DA operatör-onaylı) GERÇEK bracket emrini TEK
KAPIDAN (loop.mirror_submit_ve_kalicilastir → mirror_submit_armed) gönderir. "EOD ile BİREBİR aynı
güvenlik kapıları" sözü İKİ katmanda tutulur, kopya yazılmadan: (1) gölge satırı o ANIN kapılarını
üretimin kendi fonksiyonlarıyla yeniden ölçer (halt/breaker/veri/size_mult/pozisyon/slot —
intraday_shadow._gates) ve `would_submit` değilse 4b HİÇ denemez; (2) tek kapı gönderim anında
HALT + E1-v2 yasası + de-risk çarpanı + dedup + E2 satırını EOD yoluyla AYNI gövdeden uygular.
INTRADAY_ARM kapalıyken davranış gözlem-moduyla BİREBİR aynıdır (4b hiç çağrılmaz).

TETİK-GEÇİŞ ÖLÇÜMÜ kategori hatası DEĞİLDİR: dakikalık barın high'ı bir EŞİĞİ (entry_trigger) geçti mi —
strateji GİRDİSİ değil, eşik kontrolü. 'Dakika-hassas icra EOD next-open'a kıyasla ne kazandırırdı'yı
ölçer; gösterge HESAPLAMAZ.

LOOK-AHEAD (bkz. barclock): karar anı `as_of=barclock.now()` olay başına TEK kez; yalnız admissible
(kapanmış) barlar; girdi DEĞERLENDİRİLEN admissible barın OHLC'sinden, ASLA sıcak fiyattan (get_price);
her satır 3 damgalı → `as_of >= close_ts` sonradan denetlenebilir.
```

## `meridian/intraday_shadow.py`

```text
intraday_shadow.py — FAZ 4B GÖLGE MODU (2026-07-27). SIFIR YETKİ, TAM KARAR.

Faz 4a "tetik kesildi mi?"yi ölçüyordu. Cevaplayamadığı soru şuydu: **kesildiğinde NE OLURDU?**
Bir eşik geçişi tek başına bir karar değildir — kapılar, boyutlandırma, likidite tavanı ve gap
korumaları bir emri tamamen iptal edebilir. "Tetik 14 kez kesildi" cümlesi, o 14 geçişin kaçının
gerçek bir emre dönüşeceğini SÖYLEMEZ; Faz 4b'yi bu kanıt olmadan açmak, ölçülmemiş bir yetkiyi
açmak olurdu.

BU MODÜL EMİR GÖNDERMEZ. Tek yazdığı kendi defteridir (`intraday_shadow_orders.jsonl`).
Canlı defteri (portfolio.json) OKUR, asla YAZMAZ; broker'ı KOPYA bir nesne üzerinde çalıştırır ve
nesneyi atar. `state/INTRADAY_ARM` (gerçek icra bayrağı) ile HİÇBİR İLİŞKİSİ yoktur — bayrak kapalı
olsa da gölge ölçer, çünkü ölçüm yetki değildir.

NEDEN KOPYA BROKER, "boyutlandırmayı yeniden yaz" DEĞİL: qty/risk hesabı gap koruması, ADV tavanı,
katılım etkisi ve notional tavanını içerir (broker.fill_entry). İkinci bir kopya yazmak, iki hesabın
zamanla AYRIŞMASI demekti — ve ayrıştığı gün gölge defteri EOD'yi değil KENDİNİ ölçüyor olurdu.
Aynı fonksiyon çağrılır; sonuç okunur; nesne atılır.

SİM FİYAT SÖZLEŞMESİ (satıra da yazılır): `sim_price = max(bar_open, entry_trigger)`.
Bar tetiğin ÜSTÜNDE açıldıysa açılışı ödersin; altında açtıysa tetikte dolarsın. Bar İÇİ sıralama
OHLC'den bilinemez, o yüzden sözleşme bilinçli olarak muhafazakârdır (asla tetikten ucuza dolmaz).

loop.py'ye SIFIR TEMAS: canlı EOD motoru bu turda hiç değişmedi. `_load_broker` DESENİ burada
yeniden kurulur (fonksiyon import edilmez) ki gölge katmanı canlı hattın çağrı grafiğine girmesin.

İKİ KOL (kart EXE-2026-003, v217 — 2026-08-09). Bugüne dek yalnız SİLAHLANMIŞ planlar gölge dolumu
yazıyordu (6 seansta 4 satır). Tetiği kesilen ama silahlanmamış GO/REVIEW planları da ölçülüyor;
`kol: planli`. İki kolun DOLUM KURALI BİREBİR AYNIDIR ve bu YAPISALDIR, bir söz değil: iki kol da
`_satir()`in TEK gövdesinden çıkar, yani `sim_price = max(bar_open, entry_trigger)` ikinci kez
yazılmaz (ayrı iki gövde, ayrıştığı gün kol karşılaştırmasını anlamsız kılardı).

NEDEN AYRI DEFTER, "aynı deftere `kol` alanı" DEĞİL — ÖLÇÜLDÜ, TERCİH EDİLMEDİ. `faz5_cikis`
(EXE-2026-002 kilidi) `intraday_shadow_orders.jsonl`i HİÇBİR kol süzgeci olmadan okur
(`health.py:162` → `cikis_olcumu(rows=_golge)`); evreni "sim_fill üretmiş her satır"dır.
Silahlanmamış bir plan iç EOD defterinde HİÇ DOLMAZ, yani her planli satır `eod_yok` sınıfına
düşerdi: bugünkü 4 satırlık deftere 2 planli satır eklemek eşleşmeme oranını %33'e çıkarır ve
KILL#4'ü ateşlerdi (kilit "ölçüldü — örneklem yetersiz"ten "ölçülemedi"ye GERİLERDİ). Kartın
kill#3'ü bunu zaten yasaklıyor: "silahli kolun şemasında/sayımında HERHANGİ bir fark → geri alınır".
Bu yüzden silahli kolun deftere yazdığı satır BAYT DÜZEYİNDE değişmedi — `kol` alanı bile
EKLENMEDİ; silahli kolun etiketi OKUMA ANINDA basılır (`kollar()`), planli satır ise kendi
defterinde etiketini TAŞIR (tek başına okunan bir satır kendi kolunu söyleyebilmeli).

YAZAN KİM: planli defterin `store.append_jsonl` çağrısı `intraday_cycle`dadır, burada DEĞİL. Bu da
bir tercih değil, yürürlükteki bir çivinin sonucudur: `test_intraday_shadow_v105.py`
(`test_statik_hicbir_emir_yolu_yok`) bu dosyadaki HER `append_jsonl` hedefinin `ORDERS_FILE` olmasını
şart koşuyor — "gölge modülünün TEK bir lağımı vardır" yasası. Nüfus kararını zaten `intraday_cycle`
veriyor (hangi plan izleniyor, hangi kol); ikinci defter de o kararın yanında yaşıyor. Bu modül
planli satırı HESAPLAR (`planli_satir`) ve defteri OKUR (tekilleştirme + ikincil hat); yazım
`intraday_cycle`, okuma burası — statik artefakt grafiği de gerçek bir dış tüketici görür.
```

## `meridian/ledgers.py`

```text
ledgers.py — DEFTER SÖZLEŞMESİ (2026-07-21).

NEDEN VAR: 2026-07-21'de tek günde yedi hata çıktı ve altısı aynı kökten geliyordu — **her defteri
2-3 modül yazıyor, 5-8 modül okuyor, ve arada yazılı bir anlaşma yok.** Somut sonuçlar:

  * `trades.jsonl` satırlarında `setup`/`score` YOKTU (eski şemayla tohumlanmış defter, güncel kod)
    → skor kalibrasyonu ve gölge model 90 gerçek işlemin 90'ını da SESSİZCE eledi ("gerçek 0").
  * `plan_id` iki şemadaydı: backtest `P00140`, canlı döngü `P-{tarih}-{ticker}`
    → `cf_fidelity` — simülasyonun gerçeğe uyup uymadığını ölçen TEK mekanizma — hiç kurulamadı.
  * cf satırları `r_multiple_expected`'i `rr_expected` diye YENİDEN ADLANDIRIYORDU
    → yaması olan tüketici çalıştı, olmayan sessizce satır eledi.
  * `gate_checks` yalnız canlı döngüde üretiliyordu → panonun karar-ağacı tablosu 144/144 boştu.

Hiçbiri istisna fırlatmadı: `.get()` None döner, satır atlanır, sayı küçülür, kimse fark etmez.
800 testin hiçbiri yakalamadı çünkü testler KENDİ fixture'larını üretiyor — gerçek defterle
konuşmuyorlar.

SÖZLEŞME NE YAPAR: her defter için (a) zorunlu alanlar, (b) İZİNLİ yazarlar, (c) birleştirme
anahtarı ve formatı, (d) kanonik ad ↔ beyan edilmiş takma adlar. Üç yerden doğrulanır:
  1. üretici testleri — modül GERÇEK bir satır üretir, sözleşmeye uyar mı?
  2. statik tarama    — beyan edilmemiş bir yazar belirdi mi?
  3. canlı dedektör   — diskteki satırlar sözleşmeye uyuyor mu? (watchdog.parity_report)

Sözleşme KARAR VERMEZ; yalnız "bu defter söz verdiği şeyi taşımıyor" der.
```

## `meridian/ledgerstamp.py`

```text
ledgerstamp.py — İŞLEM DEFTERİNİN KAYNAK DAMGASI (denetim bulgusu BT-1'in kapanışı).

NEDEN VAR. `state/trades.jsonl` iki AYRI yazardan besleniyor ve satırlar birbirinden ayırt
edilemiyordu:

  * İLERİ YOL — `loop._persist_trade` → `store.append_jsonl`: canlı kâğıt döngünün gerçekten
    kapattığı işlem. Bu satır GERÇEK KANITTIR.
  * TOHUM YOLU — `run.replay_seed` → `store.write_jsonl` (deftere TEK toplu yazım): geçmiş barlar
    üzerinde `backtest.replay` koşturularak ÜRETİLMİŞ satırlar. Bu satır bir SİMÜLASYONDUR ve
    üstelik BUGÜNKÜ evrenle koşturulduğu için survivorship taşır.

Damga olmadan `learning_scorecard`, skor kalibrasyonu ve alfa/beta ölçümü 95 satırın tamamını
"canlı defter" sanıyordu — yani sistemin kendi hakkındaki en temel sayısı (gerçek canlı n) hiçbir
yerde YOKTU. Bu modül üç şey yapar: (1) ileri yolun damgasını sağlar, (2) mevcut satırları
KANITA dayanarak geriye dönük damgalar, (3) okuyucuların damgayı ayrıştırabileceği tek sayaç
yüzeyini verir.

TOHUM SINIRI UYDURULMAZ, ÖLÇÜLÜR — VE ARTIK EĞRİNİN SON NOKTASINDAN OKUNMAZ (WP2-D bacak-1,
2026-08-14). Eski okuma şu iki satıra dayanıyordu:

    run.py:203   store.write_jsonl("trades.jsonl", res.trades)      # defterin TAMAMI
    run.py:204   store.write_json("equity_curve.json", {...})       # HEMEN ardından

ve "eğriyi üretimde başka hiçbir yol yazmaz" varsayımı üzerinde duruyordu. O VARSAYIM İKİ KEZ
ÖLDÜ: (1) `sermaye.uygula` eğri zarfına reset işareti yazıyor (2026-08-01), (2) `loop.daily_cycle`
artık her seans sonunda eğriye NOKTA ekliyor (bacak-2, aşağıdaki yazar). Son noktadan okunan bir
sınır, kadanslı yazarın eklediği her noktayla BUGÜNE kayardı ve bundan sonraki HER canlı satır
`replay_seed` diye damgalanırdı — köken defterinin aktif olarak bozulması. Üstelik tehlike zaten
gerçekleşmişti: tohum 2026-08-13'te yenilendi, eğri 2026-07-20'de duruyordu, yani sınır YANLIŞTI.

SINIR ARTIK DONMUŞ KANITTAN OKUNUR, sırayla:
  * YOL-1 `reset_isareti` — eğri zarfındaki SON reset işaretinin `egri_son_nokta` alanı. İşaret
    bir kez yazılır ve bir daha yeniden yazılmaz; eğriye nokta eklemek onu KIPIRDATMAZ.
  * YOL-2 `trades.kaynak` — kartın yazılı yedek çaresi (EDG-2026-036:178): `replay_seed` damgalı
    satırların EN GEÇ `ts_close`u. İşaret yoksa ya da alanı okunamıyorsa bu yol konuşur.
  * YOL-3 `yok` — hiçbiri ölçülemezse `replay_end` None'dır ve TÜM satırlar `belirsiz` kalır.
    "Sınır 0" ya da "bugün" gibi bir varsayılan UYDURULMAZ.
Hangi yolun konuştuğu `kaynak` alanında BEYAN EDİLİR; iki yol aynı sayıyı verse bile okuyucu
hangisine baktığını görür (`yollar` alanı ikisini yan yana taşır).

TOPLU YAZIM İMZASI (mtime çifti) İKİNCİL VE ARTIK ZAYIFTIR: eğrinin kadanslı bir yazarı olduğu
için iki dosyanın mtime'ı "defter o yazımdan beri hiç eklenmedi" KANITI değildir. Alan yine
ölçülür ve taşınır (sınıflandırıcının çelişki kuralı onu okur) ama SINIRI belirlemez. AYIRT
EDİLEMEYENE İSİM TAKMAK, ölçümü tam da BT-1'in şikâyet ettiği yere geri götürürdü.

CANLI WORKER KOŞARKEN YAZMA: migrasyon CLI'si canlı süreç görürse `--uygula`yı REDDEDER
(`--zorla` ile ezilir) — `barrepair` ile AYNI desen ve AYNI ölçüm fonksiyonu (iki kopya = iki
farklı "canlı" tanımı). Bu kural, `store.file_lock` 2026-07-31'de SÜREÇLER ARASI olduktan sonra
da GEÇERLİDİR ve gerekçesi değişti: kilit artık yarışı önler, ama defteri iki farklı NİYETLE
yeniden yazmayı önlemez — canlı döngü satır eklerken migrasyonun defteri toptan yeniden yazması
teknik olarak güvenli, operasyonel olarak yine yanlıştır.

KULLANIM:
    python -m meridian.ledgerstamp                 # kuru koşu — sınıflandırma raporu
    python -m meridian.ledgerstamp --json          # aynı rapor, makine-okunur
    python -m meridian.ledgerstamp --uygula        # YAZAR (worker durdurulmuş olmalı)
```

## `meridian/loop.py`

```text
loop.py — the live forward paper cycle. Runs once per trading day after the close: builds the
regime, manages open positions on the new bar, screens + plans + guards new entries, arms them for
the next session's open, and writes a heartbeat. Portfolio state persists in state/portfolio.json so
learning survives restarts. strategy.yaml is hot-reloaded on mtime change — no redeploy for a
parameter change (§4). Uses the SAME strategy.py / broker.py as the backtest, so live and simulated
behavior cannot diverge.
```

## `meridian/marketstream.py`

```text
marketstream.py — PİYASA-VERİSİ dinleyicisi: Alpaca dakikalık KAPANMIŞ bar akışı → mrd:bars (Faz 2).

mirror_stream (yürütme) trade_updates taşır; BU katman AYRI bir hosttan (stream.data.alpaca.markets)
dakikalık kapanmış barları dinler ve `hotstate.ingest_bars` ile Redis Stream'e (mrd:bars) + sıcak
fiyata yazar. Reconnect/backoff/nabız/down-reassert YASASI `streamhealth.run_stream`ten gelir — KOPYA
YOK (mirror ile AYNI nesne). Bu modülde yalnız emre-özgü olan var: data URL, batched-array parse,
`b`→ingest.

LOOK-AHEAD (yapısal): abonelik YALNIZ `bars` kanalıdır. Yalnız `T=="b"` (dakika kapanınca gelen
TAMAMLANMIŞ bar) ingest edilir; `u`(düzeltme)/`d`(forming günlük)/`t`/`q` ASLA. Forming/partial fiyat
mrd:price'a/mrd:bars'a yazılmaz. Bar `t` = dakika BAŞLANGICI; close_ts = t+60s (hotstate sözleşmesi).
mrd:bars backtest/recompute'a ASLA girmez — kalıcı öğrenme kaynağı yine EOD immutable dosya barları.

SAĞLIK UÇUCU (disk YOK, K5): marketstream emir tutmaz, yalnız telemetri; okuyan tek yer aynı süreçteki
API. Disk bayrağı olmadığından "ölü dinleyici diskte yeşil bırakır" alt-sınıfı YAPISAL olarak yok.
Tazelik yasası yine geçerli: görev ölürse `checked_at` donar → `ok` False.

TEK SAHİP (406): iex hesap başına TEK data bağlantısına izin verir; ikincisi 406. `start()` idempotent
singleton — çift bağlantı yapısal önlenir.
```

## `meridian/marketview.py`

```text
marketview.py — İZLENEN EVRENİN TEK BAKIŞTA OKUNAN GÖRÜNTÜSÜ (2026-07-27).

Pano bugüne kadar yalnız KARARA girmiş sembolleri gösteriyordu: aday, plan, pozisyon. Oysa motorun
izlediği evren `state/bars/*.csv` ve operatörün "bugün neyi izliyorum?" sorusunun panoda hiçbir
cevabı yoktu — evrenin varlığı yalnız bir dizindeki DOSYA SAYISIYDI. Kapının elediği 250 sembol,
elenmedikleri için değil, hiç GÖRÜNMEDİKLERİ için yoktu.

BU BİR FİYAT SERVİSİ DEĞİLDİR. Gövdedeki her sayı EOD (kapanmış günlük) bardan türer; canlı fiyat
İDDİA EDİLMEZ. En taze bar hangi seanstansa `as_of` odur ve ondan geride kalan satırlar `stale_n`
ile ADIYLA sayılır: bayat bir kapanışı taze gibi göstermek, panonun okura yalan söylemesidir.

SEANS İÇİ KOLON (2026-07-27) BU ÇİZGİYİ BOZMAZ, DARALTIR. `intraday_close` YALNIZ silahlı
sembollerde doludur — çünkü dakikalık bar akışı (barfeed) yalnız onları izler — ve değeri sıcak
fiyat değil, KAPANMIŞ dakikalık barın kapanışıdır. İzlenmeyen bir sembole fiyat yazmak, ölçülmemiş
bir şeyi ölçülmüş göstermekti; kapanmamış barın "kapanışını" yazmak look-ahead'i panoya taşımaktı.
Bugün silahlı plan sıfır olduğu için kolon baştan sona "—"dır: bu bir arıza değil, DOĞRU cevap.

ÖLÇÜLEMEYEN None KALIR (UYDURMA YASAĞI). 21 barı olmayan bir sembolün 20 günlük değişimi YOKTUR;
oraya 0.0 yazmak "değişmedi" diye okunur. Her pencere kendi asgari bar sayısını ister, yoksa alan
None döner ve pano onu "—" olarak gösterir.
```

## `meridian/mcp_server.py`

```text
mcp_server.py — Meridian'ın SALT-OKUNUR durumunu yerel hermes-agent'a MCP aracı olarak açar.

Neden: evidence_pack'i prompt'a tıkıştırmak yerine (ne koyacağımızı biz tahmin ediyoruz), ajan bir
adayı düşünürken İHTİYACI OLAN veriyi kendisi sorgular — kalibrasyonlar, near-miss karnesi, rejim,
cf özeti, öz-değerlendirme. Bağımsız, bağımlılıksız bir stdio JSON-RPC (MCP) sunucusu: satır-ayrımlı
JSON-RPC 2.0 konuşur; hermes `~/.hermes/config.yaml` içindeki mcp_servers kaydıyla başlatır.

YETKİ SINIRI — MUTLAK: yalnız getter'lar. Hiçbir araç state yazmaz, emir vermez, kapıya dokunmaz.
Kapı yasası bozulamaz çünkü sunucu yalnızca okur. Her araç savunmacı: hata metne dönüşür, döngü ölmez.
```

## `meridian/memory.py`

```text
memory.py — the thing that makes it actually learn. Records every hypothesis with its full
lifecycle, closes the loop by writing the realized score delta back onto the hypothesis once
min_sample trades have run under a version, and distills lessons.md into blunt reusable lines.

hypothesis schema (§4):
  {id, ts, version_from, version_to, variable, old, new, rationale, predicted_direction,
   confidence, regime, status, predicted_delta?, realized_delta?, backtest?}
status ∈ {proposed, rejected_by_guard, rejected_by_backtest, live, promoted, rolled_back}
```

## `meridian/mirror_stream.py`

```text
mirror_stream.py — Olay-güdümlü YÜRÜTME-DURUMU katmanı (operatör mimari isteği, 2026-07-19).

Alpaca `trade_updates` WebSocket akışını dinler ve ayna emirlerinin YEREL DURUM MAKİNESİNİ anlık
besler: dolum/kısmi-dolum/ret/iptal artık bir sonraki döngünün uzlaştırmasını (300 sn+) beklemez.

FAZ 2 REFACTOR (2026-07-23): bayatlık/nabız/backoff/down-reassert/reconnect YASASI `streamhealth`e
ÇIKARILDI — mirror onu İÇE AKTARIR (aynı nesne), marketstream de aynı yasayı tüketir. `next_backoff`,
`set_stream`, `touch`, reconnect döngüsü artık TEK yerde; "aynı yasa iki uygulama, sessiz ayrışma"
kusuru (54→2 down) YAPISAL olarak imkânsız. Bu modülde YALNIZ emre-özgü olan kalır: emir durum makinesi
(`apply`/`pending_symbols`), paper host-kilidi (`_url`), devre-kesici (`_maybe_cancel_entries`) ve
`mirror_orders.json` kalıcılığı (yürütme gerçeği restart-güvenli olmalı). Davranış BİREBİR aynı —
mevcut v33/v68/v72 testleri sıfır düzenlemeyle geçer (davranış-koruma kanıtı).

SINIR ÇİZGİLERİ (bilinçli):
  * KARAR HATTI DOKUNULMAZ — sinyaller kapalı-bar EOD yasasıyla üretilir; bu katman yalnız YÜRÜTME
    durumunu taşır. bars/quotes akışına bilerek abone OLUNMAZ (o Faz 2 marketstream'in işidir; karar
    hattına ASLA sızmaz — look-ahead yasası).
  * Zamanlayıcı poll'u KALIR — akış koptuğunda uzlaştırma güvenlik ağıdır (kemer + pantolon askısı).
  * Hostname-kilitli PAPER akışı — gerçek-para stream'ine bu modülden çıkış yoktur.
  * Kopuş devre-kesicisi KORUMA BACAKLARINI ASLA iptal etmez; görünürlük sağlar (stream_ok=false → amber).
    İstenirse YALNIZ dolmamış GİRİŞ emirlerinin iptali MERIDIAN_WS_DISCONNECT_CANCEL_ENTRIES=1 ile
    açılır (varsayılan KAPALI).
```

## `meridian/mutation.py`

```text
mutation.py — MUTASYON KOŞUMU: dedektörlerin NEYİ GÖREMEDİĞİNİ ölçer (2026-07-22).

NEDEN VAR: 2026-07-21'de tek günde on üç hata çıktı ve HİÇBİRİ istisna fırlatmadı. Ardından yedi
bütünlük dedektörü (watchdog) ve yazılı bir defter sözleşmesi (ledgers) eklendi. Ama şu soru hiç
sorulmadı: **bu dedektörler hangi bozulma sınıflarını GERÇEKTEN yakalar?**

Gelecekteki hataları sayamayız. Yapabileceğimiz tek dürüst ölçüm şudur: bilinen bozulma sınıflarını
TEK TEK, kontrollü biçimde üretip dedektör bataryasının kırmızıya dönüp dönmediğine bakmak. Bu,
mutasyon testinin KODA değil VERİ SÖZLEŞMELERİNE uygulanmış hâlidir — çünkü 2026-07-21'in hataları
kod hatası değil, şema/kayıt hatalarıydı.

ÇIKTI BİR KÖRLÜK HARİTASIDIR. Düşük bir kapsama sayısı burada BAŞARISIZLIK DEĞİL, en değerli
bulgudur: her MISSED satırı, sistemin bugün göremediği bir hata sınıfının adıdır. Sayıyı yukarı
çekmek için mutasyonu zayıflatmak, ölçümün kendisini yalana çevirir.

TASARIM KARARLARI (hepsi acıyla öğrenilmiş):
  * TEMEL DURUM ÖNCE TEMİZ OLMALI. Kirli bir temel durumda her mutasyon "yakalandı" görünür ve
    kapsama sayısı yalan söyler. run() bunu ölçer ve temel kirliyse DÜRÜSTÇE patlar.
  * Dedektörlerin üçü DURUMLUDUR (determinizm/monotonluk/sahiplik önceki anlık görüntüyle kıyaslar).
    Bu yüzden batarya temel durumda İKİ KEZ koşturulur: birincisi görüntüyü yazar, ikincisi gerçek
    temel durumu ölçer. Mutasyon kopyası bu görüntüleri de taşır — yani "defter kısaldı" gibi
    ihlaller ancak böyle görülebilir.
  * KOŞUM DEFTERLERE `store.*` İLE YAZMAZ. Yazsaydı `ledgers.declared_writers()` bu modülü beyan
    edilmemiş bir yazar sayar, `ledger_writers` satırı kırmızıya döner ve TEMEL DURUM kirlenirdi:
    dedektörü ölçen araç, dedektörün ölçtüğü şeyi bozmuş olurdu. Dosyalar doğrudan yazılır.
  * CANLI `state/` DİZİNİNE ASLA DOKUNMAZ (aşağıdaki _assert_not_live her yolda çağrılır).

Kullanım:  python -m meridian.mutation        (ya da: from meridian.mutation import run)
```

## `meridian/notify.py`

```text
notify.py — push a short message to the operator (Telegram or a generic webhook). stdlib only.
No-op when no channel is configured, so it is always safe to call. Never sends secrets or PII.
Wired to the alarm events: circuit-breaker trips, rollbacks, HALT, new plans, fills.

Config (env or Secret Manager): TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID, and/or MERIDIAN_WEBHOOK_URL.
```

## `meridian/nous_eval.py`

```text
nous_eval.py — NOUS SİSTEM-DEĞERLENDİRME KATMANI (ROADMAP §3.2, 2026-07-30).

OPERATÖR YÖNÜ: "bütün mekanizmaları değerlendirip güncellenmesi gerekenleri nous bulmalı; sistem
kısıtlı alanda kalmadan sürekli kendini geliştirmeli."

SORUN. Hermes bugüne kadar TEK bir soruyu soruyordu: "hangi STRATEJİ PARAMETRESİNİ oynatayım?" —
bounds.yaml'daki 14 düğmenin içinde, 15 gündür aynı ailelerde dönerek (H2'nin ölçtüğü kör nokta).
Ama sistemin iyileştirilebilir yüzeyi bounds.yaml'dan ÇOK büyük: kapı kalibrasyonu, veto dağılımı,
skill atıfları, ölçülmeyen mekanizmalar, kopuk kablolar, boş defterler, dolmamış tabanlar. Bunların
hiçbiri bir "hipotez" biçimine sığmıyordu ve bu yüzden hiç önerilmiyordu. Sistem, kendi kısıtlı
alanının içinde optimize ediyordu.

ÇÖZÜM — DÖRT KATMAN (tasarım ROADMAP §3.2'de):
  A) TELEMETRİ PAKETİ (`analytics.system_telemetry`) — 12 bölüm, hepsi MEVCUT üreticilerden. Yeni
     ölçüm İCAT EDİLMEZ; "ölçülemedi" dürüstçe taşınır.
  B) MEKANİZMA DEĞERLENDİRMESİ (bu modül) — paket + görev şablonu, hermes'in YERLEŞİK beyin
     zinciriyle (`hermes.chain_text`). Çıktı ZORUNLU ALANLI bir şemadır ve KANIT ATIFI olmayan
     öneri DÜŞÜRÜLÜR. Düşme sayısı ve nedeni kaydedilir — kalite kapısı sessiz çalışmaz.
  C) KÖPRÜ — `sekil="parametre"` olan, bounds-içi ve guard-doğrulanabilir öneriler otomatik
     `composite_queue`ya düşer. AYRI BÜTÇE AÇILMAZ: H4'ün 3/hafta yoklama bütçesine tabidir; bütçe
     doluysa öneri SIRADAKİ HAFTAYA DEVREDER ve devir GÖRÜNÜR (sessiz kuyruk = kuyruk değil çöplük).
  D) ANAYASAL KORUMA — çekirdek HAKKINDAKİ öneri (kapı yasaları, guard, PROTECTED, risk vetoları)
     YALNIZ rapora gider. Kuyruk yolu YAPISAL olarak imkânsızdır: kuyruğa yazan TEK fonksiyon
     `_kuyruga_yaz`tır, ilk satırı şekil denetimidir, ve çekirdek-şekilli bir deneme SESSİZCE
     DÜŞMEZ — `CekirdekIhlali` fırlatır ve AUTHORITY_CHANGE alarmı basar.

OTOMATİK YÖNLENDİRME BORUSU (v192, 2026-08-06): haftalık koşunun SONUNDA `boru()` üç şeklin
ÜÇÜNÜ DE bir yola bağlar — (a) parametre → Katman C'nin composite kuyruğu (yeni yol AÇILMADI,
mevcut köprünün sonucu okunur), (b) tasarim → FİŞ (`nous_fisler.json` + `nous_oneri_fisi` olayı;
otomatik uygulama yolu YOK, görünür operatör kalemi VAR), (c) cekirdek_hakkinda → sade
`nous_oneri_red_anayasal` olayı. Katman D'nin sözü DEĞİŞMEDİ: kuyruk yolu hâlâ yapısal olarak
kapalıdır, boru `hermes_composite.enqueue`ı ÇAĞIRMAZ ve (c) sınıfında `CekirdekIhlali`
FIRLATILMAZ — o istisna köprünün yanlış yönlendirmesinin (bir KOD HATASININ) işaretidir, anayasanın
normal işleyişinin değil.

YASA: HÂKİM KENDİ YASASINI YAZAMAZ. Bu modül hiçbir şeyi UYGULAMAZ. En fazla yaptığı şey, bir
parametre demetini ÖLÇÜM SIRASINA sokmaktır — ship yolu yine kapı + operatördür ve tek-değişken
yasası kaldırılmamıştır. Çekirdek hakkında KONUŞABİLİR (ve konuşması istenir: kör nokta oradadır),
ama çekirdeği DEĞİŞTİREMEZ.

ŞEKİL SINIFLANDIRMASI BEYNİN BEYANINA GÜVENMEZ: `sekil` alanı modelin kendi etiketidir ve model
çekirdek hakkındaki bir öneriyi "parametre" diye etiketlerse kuyruğa sızardı. Bu yüzden şekil
KODDA YENİDEN TÜRETİLİR (`sekil_sinifla`) ve çekirdek işareti bulunursa etiket EZİLİR. Yön bilinçli
olarak MUHAFAZAKÂRDIR: fazla-sınıflandırma bir kuyruk kaydını kaçırtır (maliyet: bir hafta gecikme),
az-sınıflandırma anayasayı deler (maliyet: geri dönüşsüz).
```

## `meridian/obs.py`

```text
obs.py — structured JSON logging + the ALARM_ tokens the notification chain keys on.

A silent agent is an unmonitored agent (§9). Every notable event emits ONE JSON line to stdout
(captured by systemd/launchd) AND a mirrored row in `state/events.jsonl`.

JETONLARIN GERÇEK TÜKETİCİSİ (K1, 2026-07-30 düzeltmesi): bu docstring eskiden jetonların "Cloud
Monitoring log-based metrics fire" için basıldığını söylüyordu. O beyan bayattı ve yanlış güven
üretiyordu: deploy/monitoring.sh gcloud/gce_instance'a bağlıdır, fiilî işletim ise yerel
keepalive + Oracle A1 systemd — yani GCP tüketicisi bu kurulumda var OLAMAZ. Üstelik o betiğin
filtresi 11 jetondan yalnız 3'ünü tanıyordu.
BUGÜNÜN GERÇEK ZİNCİRİ, sırayla:
  1. `_maybe_notify` → `notify.send` (Telegram/webhook; jeton başına 6 sa susturma penceresi),
  2. `notify.inbox` → panonun YEREL alarm gelen kutusu (ACK'lenmemiş olanları imzaya göre gruplar),
  3. `watchdog.parity_report` → teslim edilemeyen alarm sayacı (`notify_undelivered.json`).
Kanal yapılandırılmamışsa 1 sessiz no-op olur; 2 ve 3 yine çalışır — "alarm yazıldı" ile "alarm
ULAŞTI" ayrı şeylerdir ve ikincisini yalnız ACK kanıtlar.
deploy/monitoring.sh yaşamaya devam ediyor (GCP'ye dönülürse) ama artık filtresini bu dosyadaki
NOTIFY_TOKENS'tan TÜRETİYOR — elle liste, yeni jeton eklendikçe sessizce eskiyordu.
```

## `meridian/olcum_araclari.py`

```text
olcum_araclari.py — ÖLÇÜM ŞABLONLARININ ORTAK YARDIMCILARI (WP-M, 2026-08-01/02).

BU DOSYADAKİ ARAÇLAR (hepsi İLERİYE dönük standart, hiçbiri hüküm vermez):
  * `temiz_taban`        — olay-penceresi DIŞI havuz tabanı + kirlilik oranı   (2026-08-01)
  * `olay_disi_kiyas`    — GÜN BAZINDA temiz evren tabanı + taban-fazlası      (2026-08-02)
  * `blok_bootstrap_ci`  — örtüşen-blok (moving block) güven aralığı           (2026-08-02)
  * `eb_kucult`          — empirik-Bayes/James-Stein küçültme (SE tabanlı)     (2026-08-02)
  * `kod_surumu_damgasi` — rapor hangi kod hâliyle üretildi (git HEAD + sürüm) (2026-08-02)

NEDEN VAR — KIYAS KİRLENMESİ (EAP'nin yan bulgusu, kart-adayı). Olay-çalışması ölçümlerinde
"olayın getirisi" tek başına bir bulgu değildir; taban (aynı gün evrenin geri kalanı) ondan
çıkarılır. EAP ölçümünde bu tabanın KENDİSİ kirliydi: olay penceresinin içindeki bir günde
evrenin %64-74'ü de KENDİ olay penceresindeydi. Yani "olay - evren medyanı" farkı, olayı olayla
kıyaslıyordu ve fark sistematik olarak SIKIŞIYORDU. Hiçbir test kırılmaz, hiçbir istisna atılmaz;
yalnız her etki olduğundan küçük görünür — bu deponun en sevmediği hata sınıfı ("hata değil,
miktar değişimi").

NE YAPAR. `temiz_taban` tabandan olay-penceresi-İÇİ satırları düşürür ve KAÇ TANESİNİ düşürdüğünü
raporlar. Kirlilik oranı çıktının birinci sınıf alanıdır: temizlenmiş bir taban "temiz" diye
sunulup ne kadar kirli olduğu söylenmezse, okuyucu düzeltmenin büyüklüğünü göremez.

NE YAPMAZ — GEÇMİŞE DÖNÜK DÜZELTME YOK. Bu modül İLERİYE dönük bir standarttır. Bugün
`research/`de duran ölçüm betikleri TARİHE aittir ve kendi kartlarının hükmünü taşırlar; onları
bu fonksiyonla yeniden yazmak, hükümleri sessizce değiştirmek olurdu. Kullanım kuralı
`docs/olcum_standartlari.md`de yazılıdır.

SAF YAPRAK: hiçbir `meridian` modülünü import etmez, hiçbir dosyaya yazmaz, ağa çıkmaz. Ölçüm
şablonlarının bir kum havuzundan da çağırabilmesi için böyle. TEK BEYANLI İSTİSNA:
`kod_surumu_damgasi` YALNIZ-OKUMA bir `git` alt süreci koşar (yazmaz, ağa çıkmaz, git yoksa
None + neden döner).

GERİYE DÖNÜK HÜKÜM YOK — bu dosyaya bir araç eklenmesi, o araç olmadan verilmiş HİÇBİR kart
hükmünü geçersizleştirmez. Eski bir hükmü tazelemek yeni bir ön-kayıt kartı gerektirir
(`docs/olcum_standartlari.md`, "İLERİYE DÖNÜKLÜK ŞERHİ").
```

## `meridian/oos_erosion.py`

```text
oos_erosion.py — OOS AŞINMA DEFTERİ: aynı sınav kâğıdı kaç kez soruldu?
(Kârlılık Programı Aşama 2.2, 2026-07-28)

NEDEN VAR. Bir out-of-sample penceresi "dokunulmamış" olduğu SÜRECE kanıt taşır. Her kapı
değerlendirmesi o pencereye bir soru daha sorar ve her soru onu biraz daha in-sample yapar — kimse
parametreye elle dokunmasa bile, çünkü seçilim zaten "o pencerede iyi görüneni" seçmektir. Canlı
defterde bugüne kadar ~38 hipotez AYNI pencerelere sorulmuş; hiçbiri sayılmamış. Sayılmayan bir
aşınma, kapı hükümlerini sessizce değersizleştirir: kapı hâlâ "OOS'ta kazandı" der, ama o OOS
artık kimsenin görmediği bir sınav değildir.

NE YAPAR. Pencere geometrisinin (IS/OOS/holdout + fold sınırları + ambargo) parmak izini alır ve o
parmak izine ÖMÜR BOYU sorulan soru sayısını tutar. Eşik aşılınca kapıya ek marj bindirir.

--- ÜÇ BEYAN, ÜÇÜ DE KODDA DURUR ---

(1) RETRO DAMGA YASAĞI. Geçmiş ~38 sorgu geriye dönük damgalanMAZ. O sorguların hangi pencere
    geometrisiyle koştuğunu bugün bilmiyoruz (pencereler bu arada değişti) ve tahmin edilmiş bir
    sayacı gerçek sayaç gibi sunmak, tam olarak bu modülün önlemek için var olduğu şeydir. Sayaç
    BUGÜNDEN başlar; bu, aşınmanın olmadığı değil ÖLÇÜLMEDİĞİ anlamına gelir ve rapor bunu söyler.

(2) SANDBOX SAYMAZ — BİLİNÇLİ. `config.STATE` yönlendirilmiş her ölçüm (test, sprint kumu, ön-eleme
    koşusu) sayacı KENDİ kopyasına yazar; resmî defter dokunulmadan kalır. Bu bir kaçak değil,
    tasarımın kendisidir: resmî sayaç yalnız RESMÎ kapı değerlendirmelerini sayar. Ön-elemenin
    çoklu-test yükü ayrı bir kanaldan, `k_probes` beyanıyla taşınır (probgate'in kazananın-laneti
    cezası). İki yükü tek sayaca toplamak, aynı cezayı iki kez kesmek olurdu.

(3) SAYAÇ CEZALANDIRIR, ENGELLEMEZ. Eşik aşımı kapıyı kapatmaz; geçme çıtasını yükseltir. Bir
    pencereyi yakmanın doğru cevabı "artık soru sorma" değil, "artık daha büyük bir fark iste"dir.
```

## `meridian/oos_pipeline.py`

```text
oos_pipeline.py — 70/30 OOS bölümleme + teyit yürüyüşü (karar mekanizması v3, Component 2).

OOS penceresi KRONOLOJİK ikiye bölünür: Search-OOS (%70, arama adayları burada yarışır) ve
Confirm-OOS (%30, aramanın ASLA dokunmadığı teyit dilimi). Aramanın kazananı ne kadar parlarsa
parlasın, teyit diliminde P(ΔS>0) ≥ 0.70 veremezse REDDEDİLİR — kazananın-laneti burada ölür.
Deftere yazılan predicted_delta, arama dilimindeki şişkin sayı değil, teyit dilimindeki sapmasız
ortalama farktır (dürüst kalibrasyon).

Not: buradaki 'Confirm-OOS', insana-raporlanan donmuş 2026 HOLDOUT penceresiyle AYRI şeydir —
o pencere hâlâ hiçbir kararı etkilemez.
```

## `meridian/prescreen.py`

```text
prescreen.py — HİPOTEZ ÖN-ELEMESİ: adayları KAPININ KENDİ YASASIYLA ölç, canlıya dokunma.
(Kârlılık Programı Aşama 2.6, 2026-07-29 — scratchpad'deki `onelem.py` deseninin kalıcılaştırılması)

NE İŞE YARAR. Bir hipotezi canlı döngüye sokmadan önce "kapıdan geçer mi?" sorusunun cevabı bugün
yalnız P5 turunu bekleyerek ya da elle bir script yazarak alınabiliyordu. Elle yazılan script her
seferinde biraz farklı oluyordu (farklı pencere, farklı k_probes, farklı fold) — yani ÖLÇÜM ARACININ
KENDİSİ turdan tura değişiyordu ve iki turun sonucu kıyaslanamıyordu. Bu modül o aracı sabitler.

ÜÇ SIKI KURAL — ÜÇÜ DE ÖLÇÜMÜN GEÇERLİLİĞİ İÇİN:

(1) CANLI STATE'E TEK BAYT YAZILMAZ. Canlı worker koşarken `walk_forward`/`reflect` yolundaki her
    yazım (`inc_cache.json`, `events.jsonl`, `sieve.json`, `score_calibration.json` ...) canlı
    deftere düşerdi. Çözüm: canlı `state/` çalışma dizinine KOPYALANIR ve `config.STATE/HISTORY/BARS`
    kopyaya çevrilir. `store._state()` config.STATE'i ÇAĞRI ANINDA okuduğu için bütün yazımlar
    kopyaya iner. Koşu sonunda canlı state'in mtime PARMAK İZİ karşılaştırılır ve rapora yazılır —
    "dokunmadım" bir iddia değil, ÖLÇÜLMÜŞ bir olgu olsun diye.

(2) KAPININ YASASI KOPYALANMAZ, ÇAĞRILIR. Pencereler `reflect._default_windows()`, parametreler
    `reflect.params_of`, ölçüm `backtest.walk_forward`, hüküm `reflect._gate_eval`. İkinci bir kapı
    yasası yazmak, ön-elemenin GEÇTİ dediği bir adayın canlı kapıda KALMASI (ya da tersi) demekti.

(3) `k_probes` DENENEN ADAY SAYISIDIR — ölçülen değil. `--resume` ile yarıda kalan bir koşu devam
    ettiğinde, daha önce ölçülmüş adaylar atlanır ama k_probes DEĞİŞMEZ. Kazananın-laneti cezası
    "bu turda kaç kapı yoklaması yaptık"a göredir; bir süreç kazası yüzünden cezayı düşürmek,
    istatistiksel çıtayı kazara gevşetmek olurdu (ve tam olarak böyle bir gevşetme fark edilmez).

KULLANIM:
    .venv/bin/python -m meridian.prescreen         --candidates 'entry.min_score=80,exit.breakeven_r=0.5'         --workdir /tmp/prescreen-001
    .venv/bin/python -m meridian.prescreen --candidates '...' --workdir /tmp/prescreen-001 --resume

Her aday TEK DEĞİŞKENdir (`knob=deger`), virgül ayraçlı liste AYRI adaylar demektir — birleşik bir
değişiklik değil. Tek değişken disiplini burada da geçerlidir: iki düğmeyi birlikte çeviren bir
ölçüm, hangisinin işe yaradığını söyleyemez.

BİLEŞİK ADAYLAR (`--composite`, 2026-07-30 — sadeleştirme turu ③). Tek-değişken disiplini bir ÖLÇÜM
kuralıdır, bir yasak değil: bazı hipotezler ancak iki düğme BİRLİKTE çevrildiğinde anlam taşır
(ör. "geniş stop + breakeven kapalı" ya da "hacim tabanını gevşet ↔ rvol tabanı koy" TAKASI). Bu
ölçüm bugüne dek scratchpad'de elle yazılan `g3a_bilesik.py` betiğiyle yapılıyordu — yani ölçüm aracı
yine turdan tura değişiyordu (modül başlığının çözdüğü sorunun aynısı, bir kat aşağıda). Artık kalıcı:

    .venv/bin/python -m meridian.prescreen         --composite 'stop_loss_atr_mult=3.0;exit.breakeven_r=0.0|entry.min_volume_ratio=1.0;entry.min_rvol=1.5'         --workdir /tmp/prescreen-bilesik

`|` ADAYLARI, `;` bir adayın DÜĞMELERİNİ ayırır. ÜÇ KURAL BİLEŞİKTE DE AYNEN GEÇERLİ:
  (1) Doğrulama DÜĞME DÜZEYİNDEdir: `guard.validate_change` her düğme için AYRI çağrılır (aralık +
      adım + tip). Bileşik olmak bir düğmeyi bounds dışına çıkarma ruhsatı değildir; bir düğme
      reddedilirse ADAYIN TAMAMI reddedilir ve hangi düğme yüzünden olduğu rapora yazılır.
  (2) `k_probes` YİNE ADAY SAYISIDIR — düğme sayısı değil. Bir bileşik aday kapıya BİR yoklama
      gönderir; düğme başına saymak kazananın-laneti cezasını sahte biçimde ŞİŞİRİRDİ.
  (3) Satır `bilesik=True` + `knobs={...}` taşır. Bir bileşik sonucu tek-değişkenli bir sonuç gibi
      okunursa "hangi düğme işe yaradı?" sorusunun cevabı YOK sanılır — oysa cevap "bu ölçüm onu
      sormadı"dır ve bunun satırda yazılı olması gerekir.

KUYRUK GERİ-YAZIMI (`--queue-id`, C14, 2026-08-02) — KURAL (1)'İN TEK ADLANDIRILMIŞ DELİĞİ.
`hermes_composite.spawn_pending` bu modülü ayrı bir süreçte başlatır ve satırı `measuring` damgalar;
ölçüm bitişini AYNI satıra yazacak olan da bu süreçtir (kimlik `--queue-id` ile taşınır). Yani bu
yol canlı state'e TEK BİR defterde, TEK BİR satır yazar: `composite_queue.jsonl`. Delik ADLIDIR ve
sınırları kodda dar tutulur:
  * Yazım `run()`un DIŞINDADIR (yalnız `main`). `run()` hâlâ canlı state'e sıfır bayt yazar ve
    `canli_state_degisen_dosyalar` kanıtı ONUN kapsamını ölçer — yani "ölçüm canlıya dokunmadı"
    iddiası bozulmaz, çünkü geri-yazım ölçüm BİTTİKTEN ve parmak izi alındıktan SONRA olur.
  * Yazan taraf `config.STATE`i CANLIYA geri çevirir, yazar, sonra sandbox'a geri döner: aksi hâlde
    damga sandbox kopyasındaki kuyruğa düşer ve HİÇ KİMSE onu okumazdı (halka yine açık kalırdı).
  * Kuyruk satırı yazılmadan ölçüm yapmak, C14'ün ta kendisiydi: `measured` yazan üretim yolu YOKTU,
    `n_olculen` yapısal olarak 0'dı ve ölmüş süreçler sonsuza dek "ÖLÇÜLÜYOR" görünüyordu.
```

## `meridian/probgate.py`

```text
probgate.py — Eşleştirilmiş Olasılıksal Kapı (karar mekanizması v3, Component 1).

Nokta-eşik (+0.02) yerine BLOK-BOOTSTRAP ile P(ΔS>0): incumbent ve aday, AYNI yeniden-örneklenmiş
takvim bloklarında skorlanır — ortak işlemlerin gürültüsü farkta birbirini söndürür, testin gücü
noktasal karşılaştırmanın çok üstüne çıkar. v2 dersinin kurumsallaşması: arama +0.059 gösterip canlı
−0.036 gerçekleşmişti; kazananın-laneti (winner's curse) artık K-probe cezası ve teyit yürüyüşüyle
(oos_pipeline) yapısal olarak bastırılır.

ΔS ARTIK PARADIR (**PARA-v3**, 2026-07-30 — yasanın yeniden tasarımı). Bu modülün MEKANİZMASI
değişmedi (blok-bootstrap, P(ΔS>0), K-cezası, aşınma marjı, teyit yürüyüşü aynen); değişen tek şey
ΔS'in TANIMIdır:

    ESKİ:  ΔS = bileşik skor farkı  (0,5·ret_c + 0,3·dd_c + 0,2·sharpe_c)
    YENİ:  ΔS = `shadowlaw.ret_c_v3` farkı — YALNIZ para terimi, çarpıtmasız

Gerekçe ÖLÇÜLDÜ (3a E raporu + 3b gölge ölçümü): eski ΔS'in varyansının %82'si düşüş, %17,7'si
Sharpe, %0,3'ü paraydı ve düşüş/Sharpe HEM burada HEM ayrı sert vetolarda sayılıyordu — ÇİFT SAYIM.
Şimdi skorda yalnız para var; düşüş ve kuyruk `reflect`teki vetolarda (biri bu turda EKLENDİ:
düşüş vetosu) GÜÇLENEREK duruyor. Tam gerekçe ve ölçüm kaydı: `shadowlaw` modül beyanı.

Yasa değişmez: bu modül YALNIZCA ölçer; ship kararının sahibi reflect.submit'tir ve fold-çoğunluğu +
kuyruk vetosu aynen yürürlüktedir.
```

## `meridian/provenance.py`

```text
provenance.py — ANAHTAR KÖKEN TAKİBİ: baskın kusur sınıfının GENEL biçimi (2026-07-22).

Bu hafta bulunan sessiz hataların hepsi tek bir cümleye indirgeniyordu:

    "aynı yasanın iki uygulaması var ve sessizce ayrışmış."

Veri biçiminde bu şu demek: bir modül `{"dormant_setup": ...}` yazar, başka modül `.get("dormant")`
okur. İstisna YOKTUR. Okuma None döner, dal `continue` ile atlanır, sayaç sessizce küçülür ve
7139 satırın hepsi yanlış etiketle deftere geçer. 1257 test bunu göremez, çünkü her test KENDİ
fikstürünü kurar: üretici ile tüketicinin beklentisini aynı el yazar, dolayısıyla ayrışamazlar.

TEK TEK yakalamak çözüm değil — her yeni alanda yeni bir parite testi yazmayı gerektirir ve
unutulan ilk alanda sınıf geri döner. Bu modül sınıfı YAPISAL olarak ölçer:

    Uygulamanın KENDİ koşusunu sonda olarak kullan.

`store.read_json/read_jsonl` sonuçları izlenen sözlüklerle sarılır. Her `.get(k)` ve `d[k]`
çağrısı (artefakt, anahtar, isabet/ıska) olarak kaydedilir. Koşu bitince:

    okunan ∧ hiçbir satırda YOK  →  SÜRÜKLENME (tüketici, üreticinin yazmadığı alanı istiyor)
    yazılan ∧ hiç OKUNMAYAN      →  ölü alan (üretilip tüketilmeyen kanıt)

KURT MASALI YASAĞI burada da geçerlidir — üç koruma:
  1. Yalnız BOŞ OLMAYAN artefaktlar yargılanır. Boş defterde her anahtar "yok"tur; bu sürüklenme
     değil kanıt yokluğudur.
  2. Varsayılanlı okuma (`.get(k, x)`) tasarımca isteğe bağlıdır — ayrı sayılır, ihlal sayılmaz.
  3. `OPSIYONEL` listesi GEREKÇE ister. Gerekçesiz muafiyet, muafiyet değil sessizliktir.

Dedektör kendi tabanını YAZMAZ: her şey süreç-içi bellekte birikir, rapor salt-okunurdur.
Varsayılan KAPALI; test oturumu ve günlük döngü açar (bkz. tests/conftest.py, cli).
```

## `meridian/recompute.py`

```text
recompute.py — AYNI SORUYU İKİ YOLDAN CEVAPLA (2026-07-22).

NEDEN VAR: 2026-07-21'de çıkan on üç hatanın hiçbiri istisna fırlatmadı. Hepsi aynı biçimde
davrandı — bir satır sessizce elendi, bir sayı küçüldü, kimse fark etmedi. Böyle bir hatayı
yakalayan tek şey, **aynı büyüklüğü birbirinden BAĞIMSIZ iki yoldan hesaplayıp karşılaştırmaktı**:
canlı döngü "aday: 0" diyordu, aynı önbellek barları doğrudan tarandığında 25 seansta 43 sinyal
çıkıyordu. Fark, hatanın kendisiydi (motor evrenin %18'inde karar veriyordu).

TASARIM KURALI (ihlal edilirse modül değersizleşir): iki yol GERÇEKTEN bağımsız olmalı. Aynı
fonksiyonu iki kez çağırmak hiçbir şey kanıtlamaz; sayıyı üreten muhasebe ile sayıyı taşıyan
defteri karşılaştırmak kanıtlar. Her denetim aşağıda "A yolu" ve "B yolu" diye açıkça yazılır.

Modül KARAR VERMEZ, düzeltmez, hiçbir şey yazmaz — yalnız "iki cevap tutmuyor" der.
```

## `meridian/reflect.py`

```text
reflect.py — the reflection entrypoint. Routes a hypothesis through the honest pipeline:
    guard.validate_change  ->  backtest OOS gate  ->  version bump + snapshot  ->  memory write-back

Two sources of hypotheses, same pipeline:
  * deterministic fallback proposer (--auto): proves the whole loop before an LLM is anywhere near it
  * Hermes (--hermes --hypothesis '<json>'): the brain proposes; the engine validates and gates

The engine — not the LLM — decides what ships. An instruction is a suggestion; the gate is the law.
```

## `meridian/regime.py`

```text
regime.py — tags every trade (trend_up | trend_down | chop | high_vol) and builds the P1
regime.json artifact. With no FMP breadth feed, signals are derived from the index (SPY) itself
and labeled index-derived — an honest proxy, not faked breadth. exposure_budget_pct is a HARD cap
on new risk enforced in guard.py; if 0, no new positions that day.
```

## `meridian/regime_trigger.py`

```text
regime_trigger.py — Ertelenmiş Rejim Bütçe Tetikleyicisi (karar mekanizması v3, Component 4).

Mevcut statik duruş ("chop → %0") KİLİTLİ kalır — chop'ta yalnız 8 gerçekleşmiş işlem varken dinamik
kenar-bütçelemesi süs olur. Bu modül karar VERMEZ: rejim başına kapanmış işlem sayısını sayar ve
N ≥ 30 eşiği aşıldığında karne API'sine bir tetikleyici bayrağı fırlatır (+ bir kez obs.log) —
dinamik bootstrap/edge bütçelemesine geçişin "artık kanıt var" sinyali. Geçişin kendisi ayrı ve
bilinçli bir tasarım kararıdır.
```

## `meridian/rollback.py`

```text
rollback.py — automatic, no human in the loop. Once min_sample trades have run under the
current version, if it underperforms its parent by more than goal.rollback_if_worse_by, revert
strategy.yaml to the parent snapshot and mark the shipping hypothesis rolled_back. The agent does
not get to argue with the rollback — it only explains, afterward, why it thinks the change failed.
```

## `meridian/run.py`

```text
run.py — entrypoint (TOHUMLAMA + TEK ATIŞ). 24/7 KADANS BURADA DEĞİL: `scheduler.advance_once`.

  python -m meridian.run --dry-run --replay 2023-01-01:2024-12-31   # seed state from real history
  python -m meridian.run --once                                     # one live paper daily cycle
  MERIDIAN_AUTOSTART_CYCLE=1 uvicorn meridian.api:app               # 24/7 kadans (süreç-içi zamanlayıcı)

The replay writes REAL state (trades, equity, regime, candidates, plans, scoreboard) so the
dashboard and the reflection loop have genuine data — not fixtures. Research system. Paper mode.

KALICI KURAL — İki kadans yasası tek depoda yaşayamaz (C3, 2026-08-02).
`worker()` 24/7 kadansın İKİNCİ bir uygulamasıydı ve ÜRETİMDE HİÇ KOŞMUYORDU: canlı ve yerel
başlatma yollarının HEPSİ uvicorn + süreç-içi `scheduler.start()`tir (`deploy/oracle-a1/
meridian.service`, `ops/com.meridian.agent.plist`, `serve.sh`); `meridian.run` yalnız `--replay`
tohumu için çağrılıyordu. Koşmayan bir yol DÜZELTME BASKISI ÜRETMEZ — bu yüzden zamanlayıcıda
adıyla düzeltilmiş ÜÇ kusuru son gününe kadar taşıdı:
  (a) SEANS TANIMI: takvim indeksinden `sessions[-1]` okuyordu, yani BUGÜNÜN seansını GECE
      YARISINDAN itibaren "kapanmış" sayıyordu. `scheduler._last_closed_session` tam bu hatayı
      `market_close <= now` filtresiyle "audit #12" diye düzeltilmiş ilan ediyor.
  (b) VERİ YOLU: `dataset.load(use_cache=False)` çağırıyordu, `load_live()` DEĞİL — o yolda ne
      Finviz keşfi ne aynı-akşam Alpaca bacağı vardır (aynı-akşam kapısı `session=` yalnız
      `load_live` üzerinden verilir).
  (c) İLERLEME: `daily_cycle` dönüşü hiç sorgulanmadan `last_processed` yazılıyordu — kapsama
      kapısı `noop`/`waiting_for_universe`/`refused_regressive` dönse bile o seans bir daha
      denenmiyordu; sık/seyrek merdiven, `_repair_once_per_session` ve çoklu-seans yetişme
      döngüsü bu yolda YOKTU.
Seans-sonrası kadansların HİÇBİRİ (öğrenme, Y4, haftalık üçlü, arming, selfreview, yetim süpürme,
nous, sprint, earnings, intraday gap) burada yoktu. Dördüncü bir yama kusuru kapatırdı, SINIFI
kapatmazdı: sınıf "ikinci bir kadans uygulamasının var olması"dır. O yüzden hüküm EMEKLİLİKtir.

GERİ ALINABİLİRLİK. Gövde silindi ama KAYBOLMADI: bu turdan önceki her sürüm tam metni taşır
(`git show 8aaf05e:meridian/run.py`). Kadansın kendisi zaten `scheduler.py`de yaşıyor ve orada
DÜZELTİLMİŞ hâliyle koşuyor — yani geri alınacak bir yetenek değil, yalnız bir kopya emekli oldu.
`worker()` adı yaşamaya devam eder ama artık YÖNLENDİRİR (bkz. gövdesindeki gerekçe).
YAN ETKİ (beyan, kapsam DIŞI): `obs.ALARM_HEARTBEAT_STALE` jetonunun depodaki TEK üreticisi bu
döngüydü; jeton bugün üreticisiz kaldı. Üretimde zaten hiç ateşlenemiyordu (asılı-tick koruması
`meridian-tick-watchdog.timer`dır) — jetonun yeni bir üreticiye bağlanması ayrı bir bulgudur.
```

## `meridian/scheduler.py`

```text
scheduler.py — the local paper-advance loop. On a laptop there is no systemd worker, so nothing
calls loop.daily_cycle: within ~15 min the heartbeat goes stale, /healthz 503s, and hermes_runtime
stops reflecting — the "self-improving local agent" silently freezes. This daemon thread (started by
the dashboard when MERIDIAN_AUTOSTART_CYCLE=1) polls the XNYS calendar and runs ONE daily cycle each
time a new session has closed — the same job run.worker does on the VM, but in-process and stoppable.
Dedupes on portfolio last_date; respects HALT; never advances on a non-session day.
```

## `meridian/score.py`

```text
score.py — composite performance score in [-1, +1] from realized return vs target, drawdown
vs max, and Sharpe vs min. Returns None (NOT 0.0) when there are fewer than goal.min_sample closed
trades: an unknown score must never be mistaken for a mediocre one (§4). The absolute value is a
heuristic; what matters is that incumbent and candidate are scored by the identical function so the
backtest gate compares like with like.
```

## `meridian/secrets.py`

```text
secrets.py — Secret Manager, a local 0600 store, or nothing (Hard Rule 5). Reads a secret from,
in order:
  1) process env,
  2) a local operator store  (state/secrets.json, chmod 0600, gitignored)  ← app-entered keys land here,
  3) GCP Secret Manager      (if google-cloud-secret-manager + MERIDIAN_GCP_PROJECT set).
Env still wins, so nothing an env var sets can be silently overridden by the file. The local store
exists so the single operator can paste keys through the dashboard on a local L0 box; on the VM the
keys belong in Secret Manager (source 3) and the file is never copied there.

Never logs a value. Only the operator (source 1/2) or Secret Manager (source 3) ever holds it, and
status()/mask() only ever expose a masked hint (last 4 chars). Writes are whitelisted (ALLOWED) so a
dashboard POST can only ever set a KNOWN key name — never an arbitrary env-like variable.
```

## `meridian/selfreview.py`

```text
selfreview.py — Haftalık Öz-Değerlendirme (#2) + Çelişki Dedektörü (#3).

v3→v10 telemetrisi dört panele dağılmıştı; sentezi operatör kafasında yapıyordu. Bu modül sentezi
SİSTEME verir: haftada bir (ve istendiğinde) tüm kalibrasyon/defter/bekçi sinyallerini tek raporda
toplar, kural-tabanlı bir DİKKAT listesi çıkarır ve katmanların birbiriyle ÇELİŞTİĞİ yerleri
listeler (her çelişki ya öğrenme fırsatı ya hata işareti). Rapor ayrıca ajanın kanıt paketine girer.

Rapor ayrıca DANIŞMA KATMANI MEKANİZMALARININ SAĞLIK DEFTERİdir (mechanisms): bir mekanizma çıktı
üretemiyorsa bu, boş bir rapordan ayırt edilebilir biçimde burada durur (aşağıdaki MECH_KEY notu).

Yalnız OKUR ve yazar (state/self_review.json) — hiçbir karara dokunmaz.
```

## `meridian/sermaye.py`

```text
sermaye.py — ANTRENMAN TOHUMUNUN CANLI SERMAYEDEN AYRIŞTIRILMASI (BT-1'in nakit ayağı).

NEDEN VAR. BT-1 defterin KÖKENİNİ ayırdı (`ledgerstamp`: live_paper / replay_seed / belirsiz) ama
NAKDİ ayırmadı. Ölçülen hâl (2026-08-01, canlı state):

    portfolio.json  cash = 94.457,91$   realized_pnl = −5.542,09$   positions = {}
    trades.jsonl    95 satır, ledgerstamp 95/95 = replay_seed      canlı-kâğıt işlem = 0

Yani kitaptaki 5.542,09$'lık kayıp GERÇEK bir zarar DEĞİL: `run.replay_seed`in geçmiş barlar
üzerinde koşturduğu bir SİMÜLASYONUN çıktısı (üstelik bugünkü evrenle, survivorship'li). Pano bu
sayıya "Sermaye" diyordu ve iki ayrı yalan söylüyordu:

  1. GÖSTERİM: operatör "sistem 5.542$ kaybetti" diye okuyor; gerçekte canlı-kâğıt çağ hiç işlem
     yapmadı. Kaybın kendisi bir antrenman artefaktıdır.
  2. DAVRANIŞ (asıl zararlı olan): boyutlandırma tabanı `broker.equity()` = start_equity +
     realized_pnl'dir. `loop._load_broker` her turda `PaperBroker(START_EQUITY, …)` kurar ve
     üstüne diskten `realized_pnl`i basar — yani antrenman zararı, GERÇEK-CANLI çağın pozisyon
     boyutlarını her gün kısıyordu. `peak_equity` = 102.520,45$ ise aynı simülasyonun tepesidir ve
     de-risk rampası düşüşü ORADAN ölçer: canlı çağ, hiç yaşamadığı bir düşüşün cezasıyla başlardı.

ÖLÇÜLEN İNCE NOKTA — NAKDİ RESETLEMEK TEK BAŞINA HİÇBİR ŞEY YAPMAZDI. `broker.equity()` `cash`i
OKUMAZ (`PaperBroker.equity`: `eq = self.start_equity + self.realized_pnl` — ÇAPA SEMBOLDÜR;
burada "broker.py:263" yazıyordu, o satır bugün de-risk rampasına ait: A17 çürüme sınıfı, 2026-08-14
ölçümüyle düzeltildi). Yalnız `cash`i 100.000'e
çekmek panoyu düzeltir, boyutlandırmayı DÜZELTMEZ — kozmetik bir yama olurdu. Bu yüzden reset
kitabın DÖRT alanına birden dokunur ve dördünün de gerekçesi ayrı yazılıdır (aşağıda `_yeni_kitap`).

DEFTERLERE DOKUNULMAZ. `trades.jsonl` yerinde kalır: antrenman satırları öğrenmenin (kalibrasyon,
atribüsyon, shadow_model) girdisidir ve silinmeleri ölçüm zeminini yok ederdi. `equity_curve.json`
noktaları da SİLİNMEZ — eğrinin tarihi korunur, kırılma noktası BEYAN edilir (`reset_isaretleri`).

NEDEN EĞRİYE YENİ NOKTA EKLENMİYOR (ölçülmüş yan etki). `points`e bir nokta eklemek cazip: eğri
kırılmayı kendi çizerdi. Ama `ledgerstamp.seed_boundary()` tohum penceresinin sınırını EĞRİNİN SON
NOKTASININ TARİHİNDEN okur (ledgerstamp.py:149, tek yazar run.py:171). Reset günü bir nokta
eklenseydi tohum sınırı bugüne kayar ve bundan sonraki HER canlı satır `replay_seed` diye
damgalanırdı — yani bu turun kapattığı kusuru, tam da onu kapatan araç geri açardı. İşaret ayrı bir
zarf anahtarında durur; `points` dokunulmaz kalır.

  ↑ ÜSTTEKİ GEREKÇE YANLIŞLANDI (2026-08-14, v245-D; paragraf tarihçe için duruyor). İKİ
  DAYANAĞI DA ÖLDÜ: (1) `ledgerstamp.seed_boundary()` sınırı artık eğrinin son noktasından
  OKUMUYOR — sıra (a) son reset işaretinin DONMUŞ `egri_son_nokta` alanı, (b) yedek yol
  `trades.jsonl` `replay_seed` damgalarının en geç `ts_close`u; güncel son nokta rapora yalnız
  bilgi olarak girer ve "sınırı BELİRLEMEZ" diye beyanlıdır. (2) "tek yazar run.py" varsayımı
  da yok: `loop._persist_equity_point` her seans sonunda eğriye TEK nokta ekliyor (kadanslı
  yazar, bacak-2) — üstelik bu modülün kendisi de aynı zarfa reset İŞARETİ yazıyor (aşağıda,
  `uygula`). KARAR DEĞİŞMEDİ, GEREKÇESİ DEĞİŞTİ: reset günü `points`e nokta EKLENMEZ, çünkü
  (i) bu modülün işi nakit tabanını ayrıştırmaktır, eğrinin tarihini yeniden yazmak değil, ve
  (ii) o günün noktasını zaten kadanslı yazar seans sonunda kendi koyar — buradan ikinci bir
  nokta koymak aynı günü iki yazarlı hâle getirirdi (`_persist_equity_point` günde tek nokta
  değişmezini korur). Sınır artık işaretin DONMUŞ alanından okunduğu için eğriye nokta eklenmesi
  onu kaydırmaz; yani eski paragrafın korktuğu felaket yolu yapısal olarak kapalıdır.

MUTABAKAT KİMLİĞİ KIRILMAZ, BEYANLI HÂLE GETİRİLİR. Reset üç `recompute` kimliğini birden bozar
(`realized_pnl`, `cash_identity`, `equity_curve_tail`) — çünkü kitap yeni bir tabana taşındı,
defter ise eski tabanı taşıyor. Kimlikleri susturmak yerine OFSET beyan edilir: kitapta
`sermaye_resetleri` listesi durur, `ofset()` toplamı verir ve `recompute` GEÇMİŞTEN türeyen tarafa
(defter toplamı / eğri sonu) o ofseti ekler. Böylece kimlik ölçmeye devam eder: resetten SONRA
kaybolan ya da iki kez sayılan bir işlem yine yakalanır.

TEPE SERMAYE AFFI. `peak_equity` 102.520,45 → 100.000 bir GERİLEMEDİR ve `watchdog.
monotonicity_report` bunu haklı olarak bayraklar. Sessizce geçmek ("persist tabanı yutar") ya da
bayrağı kırmızı bırakmak (kurt masalı) yerine depoda zaten kurulu üçüncü yol kullanılır:
`watchdog.grant_amnesty` — YAZILI, tam eşleşmeli, gerekçeli af (re-seed'in 129→95 küçülmesinde
operatörün kullandığı yolun aynısı).

KURU KOŞU VARSAYILANDIR ve CANLI WORKER KOŞARKEN YAZILMAZ — `barrepair`/`ledgerstamp`/`dbmigrate`
ile AYNI desen ve AYNI ölçüm fonksiyonu (iki kopya = iki farklı "canlı" tanımı).

İDEMPOTENT. İkinci `--uygula` hiçbir bayt yazmaz ve `zaten_ayrisik` der. Ayrışıklığın kanıtı
kitaptaki `sermaye_resetleri` kaydıdır — nakdin 100.000 olması DEĞİL (canlı çağ kâr ederse nakit
100.000'den ayrılır ama ayrışıklık sürer).

KULLANIM:
    python -m meridian.sermaye --durum      # köken ölçümü (hiçbir bayt yazılmaz)
    python -m meridian.sermaye              # KURU KOŞU — ne yazılacağı, satır satır
    python -m meridian.sermaye --json       # aynı rapor, makine-okunur
    python -m meridian.sermaye --uygula     # AYRIŞTIR (worker DURDURULMUŞ olmalı)
    python -m meridian.sermaye --uygula --gerekce "…"   # ≥20 karakter, olaya yazılır
```

## `meridian/shadow_lifecycle.py`

```text
shadow_lifecycle.py — GÖLGE-v2 YAŞAM-DÖNGÜSÜ MOTORU (2026-07-30). SIFIR YETKİ, KENDİ KÂĞIT DEFTERİ.

NE DEĞİŞTİ. `shadow_variants` (v1) bir GİRİŞ-KARARI anlık görüntüsüdür: "bugün hangi varyant neyi
silahlandırırdı". Pozisyon taşımaz, fill görmez, çıkış görmez. Bu sınır iki bedel doğurmuştu ve
ikisi de yazılıydı: (a) ÇIKIŞ düğmeli kollar (V3/V6/V7) kontrol koluyla KARAR-ÖZDEŞ çıkıyor,
ölçüm kazancı sıfır olduğu için defterden ÇIKARILDILAR; (b) "bu varyant PARA kazandırır mıydı"
sorusu gölge katmanında hiç sorulamıyordu — yalnız `backtest.walk_forward` (geçmişe bakan, pencere
tüketen) yanıtlıyordu. Bu modül o eksik katmandır: **varyant başına kalıcı kâğıt defteri** —
fill → yönetim → çıkış → mark, her gün, canlı akışın taze barlarıyla.

YASALAR ÇAĞRILIR, KOPYALANMAZ — VE BURADA BU DAHA DA KRİTİKTİR. v1'de kopyalanacak şey kapı
hükmüydü; v2'de kopyalanacak şey İCRA yasasının TAMAMI olurdu (gap koruması, likidite tavanı,
notional tavanı, kısmi satış sırası, bar-içi muhafazakârlık, komisyon/kayma muhasebesi). Onlarca
satırlık bir kopya, ilk düzeltmede sessizce çatallanır ve defter zamanla stratejiyi değil KENDİNİ
ölçmeye başlardı. Bu yüzden:
  * FILL / KISMİ SATIŞ / DOKUNUŞ ÇIKIŞI / KAPANIŞ SATIRI  → `broker.PaperBroker`ın TA KENDİSİ.
    Her varyantın kitabı bir `PaperBroker` örneğidir; diskteki JSON yalnız o nesnenin serileşmiş
    hâlidir (`dataclasses.fields(Position)` ile — Position'a yarın eklenen alan kendiliğinden taşınır).
  * TRAIL / BREAKEVEN / CHANDELIER / GIVEBACK / TIME-STOP / ERKEN İTLAF → `strategy.manage_position`.
  * LİKİDİTE (ADV) → `backtest._adv`.  KISMA/TAVAN → `broker.derisk_mult` / `broker.max_positions_at`.
  * TARAMA + KAPI → `shadow_variants._signals` / `._judge` (onlar da `strategy.scan_all` /
    `guard.classify_gate` çağırır). İkinci bir tarama ya da ikinci bir kapı YOKTUR.
KOPYALANAN TEK ŞEY SÜRÜCÜDÜR (`step()`in faz sırası) ve kaynağı ADIYLA yazılıdır: `backtest.replay`
satır 182-351 — OPEN(D) bekleyen çıkışlar+fill, INTRADAY(D) scale_out+dokunuş, CLOSE(D) yönetim+arm.
Sıra bir "yasa" değil bir OLAY DÜZENİDİR ve ileri-dönüklüğü olmayan tek düzendir; onu çağırmanın yolu
yok (replay kendi takvimini ve kendi brokerını kurar), o yüzden burada tek yardımcıya çıkarıldı.

KİMLİK AYRIKLIĞI. Kapanan her işlem `SV-` önekli bir kimlik taşır (`SV-<varyant>-<tarih>-<ticker>`)
ve satırdaki `plan_id` de `SV-` öneklidir (`shadow_variants._plan_of`). `ledgers.PLAN_ID_RE`
(`^P-\d{4}-\d{2}-\d{2}-`) ile ASLA eşleşmez: canlı defterin eşleştirmeleri (trades.plan_id,
cf_fidelity) hayali bir planla eşleşmeye çalışmaz. v1'in gerekçesi aynen geçerlidir, burada bir de
İŞLEM satırı ürettiğimiz için daha yüksek bedellidir.

ÇOKLU KARŞILAŞTIRMA — İKİ SORU, İKİ PAYDA (bu turun BİLİNÇLİ tasarım sapması, ROADMAP §7'de yazılı).
v1 defteri KARAR ayrışmasını ölçer; orada V3/V6 kontrol koluyla karar-özdeştir (bu YAPISAL bir olgu
ve `tests/test_sadelestirme_v123.py` ile çakılıdır — çıkış düğmeleri `scan_all`/`classify_gate`
yolunda HİÇ okunmaz). Bu yüzden `shadow_variants.VARIANTS` DEĞİŞMEDİ ve `k_variants` 4 kaldı:
karar sorusunun paydasını karar-özdeş kollarla şişirmek, gerçekten ayrışan kolların (V1/V2/V4)
cezasını sıfır ölçüm kazancı karşılığında artırmak olurdu — 2026-07-30'da tam bu gerekçeyle
temizlenmişti. PARA sorusunun paydası ise BAŞKADIR: kitapta V3/V6 gerçekten ayrışır. O yüzden
`k_lifecycle` (= `len(arms())`) ayrı bir alandır, kitap ve işlem satırlarında taşınır ve karnede
yazılır. Tek bir sayıya indirgemek, iki farklı çoklu-karşılaştırma ailesini birbirine karıştırmak
olurdu; iki sayı tutmak onları AYIRT EDİLEBİLİR kılar.

NO-OP KOL YASAĞI (E4 tuzağı). `exit.scale_out_r` üretim varsayılanı ZATEN 2.0'dır — onu 2.0'a
"ayarlayan" bir kol hiçbir şeyi değiştirmez ama paydayı büyütür ve defterine yazacağı sıfır ayrışma
bir ÖLÇÜM değil bir KURGU olur. `noop_arms()` her kolun ETKİN parametre sözlüğünü kontrol kolununkiyle
OKUNAN anahtar düzeyinde karşılaştırır; farkı boş olan kol turdan DÜŞÜRÜLÜR (sessizce değil: obs.warn
+ kitap satırında `dropped_arms`). Kural testle çakılıdır.

SIFIR YETKİ. Yazdığı iki dosya vardır: `shadow_books.json` ve `shadow_trades.jsonl`. Canlı
`portfolio.json`a, `trades.jsonl`a, `trade_plans.jsonl`a, aynaya (Alpaca) ve strategy.yaml'a HİÇBİR
yol çıkmaz. Bu defterden ship yolu YOKTUR — canlıya geçiş yalnız OOS kapısından (prescreen/reflect)
geçer; buradaki para sayıları bir KANIT HIZLANDIRICISIDIR, bir onay değil.
```

## `meridian/shadow_model.py`

```text
shadow_model.py — Gölge Sonuç-Modeli (karar mekanizması v3, Component 3).

Saf-numpy, rejim-koşullu lojistik regresyon: P(kazanç | plan özellikleri). YETKİSİ YOKTUR —
kapı kararlarını kesemez/reddedemez; ürettiği olasılık Adaylar arayüzüne yalnızca KANIT olarak
basılır ve Brier skoru kalibre olduğunu kanıtlayana kadar gölgede kalır (skill-gölgeleme felsefesinin
aynısı). scikit-learn bilinçli olarak YOK: n≈111 örneklemde basitlik = dürüstlük.

SPEC DÜZELTMESİ (sızıntı): şartnamede özellik olarak 'r_multiple' yazıyordu — o GERÇEKLEŞEN sonuçtur
ve etiket (win = r_multiple>0) ondan türetilir; özellik olarak kullanmak modele cevabı göstermek olur.
Doğrusu plandaki r_multiple_expected (hedeflenen R:R) — burada o kullanılır. İşlem satırları plan
özelliklerini taşımadığından geçmiş veriler plan_id→trade_plans join'iyle beslenir (kapsama 90/90);
broker artık yeni kapanışlara özellikleri damgalar, join zamanla gereksizleşir.
```

## `meridian/shadow_variants.py`

```text
shadow_variants.py — 2.4 GÖLGE-VARYANT PORTFÖYLERİ (2026-07-30). SIFIR YETKİ, KENDİ DEFTERİ.

SORUN. Kârlılık programının kanıt hızı bugün TEK bir parametre kümesine bağlı: canlı strateji her gün
BİR karar akışı üretiyor, o akış da ayda ~10-20 satır kanıt biriktiriyor. Bir düğmenin (ör. `min_rvol`)
işe yarayıp yaramadığını sormanın iki yolu vardı: (a) OOS replay'i (`prescreen`/`walk_forward`) — geçmiş
barlar üzerinde, güçlü ama GEÇMİŞE bakar ve pencereleri tükenir; (b) canlıya ship edip beklemek — yavaş
ve sonuçlu. Arada bir katman yoktu: **aynı günün aynı aday akışına farklı parametrelerle KÂĞIT karar
uygulayıp defter tutmak.** Bu modül o katmandır — kanıt hızı çarpanı, risk çarpanı değil.

DESEN 4B'DEN GENELLENDİ. `intraday_shadow` seans içinde "tetik kesildiğinde ne olurdu?"yu KOPYA bir
broker/kitap üzerinde ölçüp kendi defterine yazıyor. Buradaki genelleme aynı üç kurala uyar:
  1. KANUN ÇAĞRILIR, KOPYALANMAZ. Tarama `strategy.scan_all`, kapı `guard.classify_gate`, karartma
     `earnings.in_blackout`, kısma `broker.derisk_mult`/`max_positions_at` — hepsi ÜRETİMİN kendi
     fonksiyonları. İkinci bir kopya yazmak, varyant defterinin zamanla stratejiyi değil KENDİNİ
     ölçmeye başlaması demekti (4b'nin yazılı dersi).
  2. KİTAP KOPYADIR, SALT OKUNUR. Canlı `PaperBroker` nesnesine erişilmez; `loop` bir PROJEKSİYON
     geçirir (pozisyon sayısı/sektörü/size_r + sermaye + zirve). Hiçbir yazım yolu (`_save_broker`,
     `fill_entry`) çağrılmaz.
  3. TEK YAZDIĞI KENDİ DEFTERİDİR (`state/shadow_variants.jsonl`). canlı strategy.yaml'a, guard'a,
     kapıya, `portfolio.json`a ve hipotez defterine HİÇBİR yol çıkmaz.

BEYAN — BUNLAR ÖLÇÜMDÜR, SHIP DEĞİL. `VARIANTS` sözlüğündeki her giriş bir YOKLAMADIR. `prescreen`in
`k_probes` disiplininin kardeşi: her satır `k_variants` taşır (o gün kaç varyant koştu). Sonradan "en
iyi varyant" seçmek ÇOKLU KARŞILAŞTIRMADIR; paydayı satıra yazmayan bir defter, kazananın-lanetini
görünmez kılar. Bir varyantın canlıya geçişi YALNIZ OOS kapısından (prescreen/reflect) geçerek olur —
bu defterden ship yolu YOKTUR ve olmamalıdır.

ÖLÇÜLEN ŞEY: KARAR, henüz PORTFÖY DEĞİL (v1 sınırı, bilerek ve yazılı). Her EOD turunda her varyant
için "hangi adaylar sinyal üretti, kapı ne dedi, hangi set silahlanırdı, geometri (stop/hedef/R) ne
olurdu" ölçülür. Varyantların KENDİ pozisyon ömürleri (fill → yönetim → çıkış → mark) İZLENMEZ: bunun
için ikinci bir yaşam-döngüsü motoru gerekirdi ve o motorun canlıdan sürüklenmesi tam olarak 4b'nin
reddettiği hatadır. Çok günlü P&L sorusunun aracı ZATEN var ve kapının yasasını çağırıyor:
`backtest.walk_forward` (→ `prescreen`). Bu defterin işi onun ölçemediğini ölçmektir — CANLI günün
gerçek akışında kararın nasıl AYRIŞTIĞINI, her gün, taze.

ÇIKIŞ DÜĞMELİ KOL BU SETTE YOKTUR (2026-07-30 kararı) — v1 SINIRININ DOĞRUDAN SONUCU. Bir eksiklik
değil bir ELEME: ÇIKIŞ düğmeleri v1'in ölçtüğü GİRİŞ yolunda HİÇ OKUNMAZ. Ölçüldü, varsayılmadı —
`exit.early_kill_pivot` yalnız `strategy.early_kill_pivot_exit` içinde okunur, o da yalnız
`manage_position`dan çağrılır; `exit.scale_out_frac`/`_r` yalnız `broker.scale_out`, yani FILL
ömründe. Böyle bir kol kontrol kolu (V5) ile KARAR-ÖZDEŞ olur: defterine yazacağı ayrışma sıfırı bir
ÖLÇÜM değil bir KURGU olur ve "erken itlafın/kısmi kâr almanın etkisi yok" diye okunmaya açık kalır.
ÜSTELİK BEDELLİ — her karar-özdeş kol `k_variants` paydasını büyütür, yani GERÇEKTEN ayrışan kolların
(V1/V2/V4) çoklu-karşılaştırma cezasını SIFIR ölçüm kazancı karşılığında artırır. Bu yüzden
`LIFECYCLE_KNOBS_V2` düğmelerinden birini taşıyan kol v1 setine ALINMAZ; kural yazılı bir konvansiyon
değil, testle ÇAKILMIŞ bir kısıttır (`tests/test_sadelestirme_v123.py`). Bu düğmelerin çok günlü P&L
sorusu ZATEN yanıtlanabilir ve aracı bellidir: `backtest.walk_forward` (→ `prescreen`). Gölge-v2
yaşam-döngüsü motoru geldiğinde kısıt kalkar ve eleme gerekçesiyle birlikte kollar geri eklenir.

GÖLGE-v2 GELDİ (2026-07-30) — AMA BU DEFTERİN SINIRI DEĞİŞMEDİ. `meridian/shadow_lifecycle.py`
artık fill → yönetim → çıkış → mark izleyen KALICI bir kâğıt kitabı tutar ve çıkarılan çıkış kolları
(V3/V6) ORADA geri geldi. Bu modülün `VARIANTS` seti BİLEREK aynı kaldı: burada ölçülen soru hâlâ
KARARIN ayrışmasıdır ve o soruda çıkış düğmeleri hâlâ karar-özdeştir (yukarıdaki yapısal gerekçe ve
`tests/test_sadelestirme_v123.py` çivisi aynen geçerli). İki soru, iki payda: `k_variants` (karar,
bu defter) ve `k_lifecycle` (para, kitap defteri). Tek bir sayıya indirgemek, karar-özdeş kolları
karar sorusunun paydasına geri sokmak — yani 2026-07-30'da tam bu gerekçeyle yapılan temizliği geri
almak — olurdu. Bu modül kitabın DIŞ OKUYUCUSUDUR (`--karne`), yazarı değil.

NÜFUS NEDEN TAM: kanca `candidates` ∪ `near_miss` ticker'larını geçirir. `near_miss` taraması
`strategy.relax_for_near_miss` ile koşar (hacim ≤1.0 = bounds tabanı, RS ≤55, skor ≤50, proximity
×1.5) — yani GEVŞETİLMİŞ eşiklerin ürettiği küme, buradaki her varyantın üretebileceği kümenin
ÜST KÜMESİDİR. V4 gibi bir düğmeyi GEVŞETEN varyant bile bu yüzden eksiksiz ölçülür; canlı akışı tek
başına süzmek onu sessizce kör bırakırdı (canlı `candidates` bir ALT kümedir).
```

## `meridian/shadowlaw.py`

```text
shadowlaw.py — BÜYÜKLÜK YASASI **PARA-v3**: yeni yasanın tanımı + ESKİ YASANIN GÖLGESİ.

TERS GÖLGELEME (2026-07-30, operatör onayı "1 numaradan başla"). Bu dosya 3b'de "v2 gölge yasası"
idi: karar eski bileşik skordaydı, v2 kayda geçiyordu. Yasa yeniden tasarlandıktan sonra yön TERSİNE
döndü — **karar PARA-v3'te, ESKİ YASA kayda geçiyor.** Modülün makinesi aynı makinedir (tek
`score_detail` çağrısından iki yasa türetmek); yalnız hangisinin hüküm verdiği değişti.

NEDEN DEĞİŞTİ — ÖLÇÜLMÜŞ ZİNCİR (uydurma yok, üçü de bu depoda ölçüldü):

  (1) 3a E RAPORU: kapının gerçek karar değişkeni `P(ΔS>0) ≥ 1 − 0,20/K` ve ΔS varyansının
      **%82'si düşüş, %17,7'si Sharpe, %0,3'ü PARA** terimiydi. Yani "büyüklük kapısı" fiilen bir
      düşüş+düzgünlük kapısıydı; kârın kapı kararına katkısı üç binde üçtü.
  (2) 3b GÖLGE-YASA ÖLÇÜMÜ (v2 rötuşu): ret_c'nin ÖLÇEĞİNİ düzeltmek PARA payını %0,3 → %3,2
      yaptı; hedef ≥%40 TUTMADI, üç ağırlık denemesi de tutmadı (bkz. `MEASURED_V2`,
      `V2_WEIGHT_TRIALS`, `WHY_40_UNREACHABLE` — o ölçüm kaydı SİLİNMEDİ, v3'ün GEREKÇESİDİR).
  (3) KÖK NEDEN: ölçek değil ÇİFT-SAYIM. σ(dd_c)=0,4182 ve σ(sharpe_c)=0,2917, σ(ret_c)≈0,015-0,050
      iken — çünkü dd ve Sharpe'ın PAYDALARI (maks düşüş %8, 2·min_sharpe=2,4) kendi gerçekleşen
      dağılımlarına göre DAR. Ve bu iki bacak HEM skorun varyansında HEM ayrı sert kapılarda
      sayılıyordu (kuyruk vetosu + 3A kuyruk ölçütü + maks düşüş ölçütü). PARA tek uygulanan bacaktı.

YENİ YASA — TEK TERİM, ÇARPITMASIZ:

    ΔS_v3 = ret_c_v3(aday) − ret_c_v3(incumbent)        ← kapının KARAR değişkeni

    ret_c_v3 = kıs( pencere_bileşik_getirisi / hedef_pencere )
    hedef_pencere = (1 + %25)^(span/365) − 1            ← yıllık %25'in pencere-eşlenik karşılığı

30-GÜNE İNDİRGEME YOK. Eski yasa payı `(1+R)^(30/span) − 1` yazıyordu; 1274 günlük bir defterde üs
30/1274 = 0,0235'tir, yani yeniden-örneklemenin ürettiği getiri oynaklığının ~%98'ini SÖNDÜRÜR
(ölçüldü: σ(ret_c_eski) = 0,0151). v3'te pay HAM bileşik getiridir ve payda sabittir, dolayısıyla
ret_c_v3 getiride DOĞRUSALDIR — ölçülen σ 0,0356, yani eski terimin 2,36 katı oynaklık. Aynı
ölçek ailesinden (`ANNUAL_TARGET_RETURN`) ama çarpıtmasız.

dd_c ve sharpe_c SKORDAN ÇIKTI. Kaybolmadılar — GÜÇLENEREK vetolara taşındılar (`reflect`):
fold-çoğunluğu + VaR/CVaR kuyruk vetosu (`TAIL_MARGIN_R`) + **düşüş vetosu** (`DD_VETO_MARGIN`,
bu turda EKLENDİ) + aşınma marjı + 3A kuyruk ölçütü. Sharpe hiçbir yerde AYRICA sayılmaz: fold
çoğunluğu (pencere-pencere tutarlılık), kuyruk vetosu (dağılımın sol ucu) ve DSR (deneme-düzeltmeli
Sharpe) onu üç ayrı açıdan zaten kapsıyor. Çift-sayım biter, koruma bitmez.

ANNUAL_TARGET_RETURN = %25 NEDEN: literatürdeki en iyi belgelenmiş uzun-vadeli momentum/kırılım
programlarının net bandı yıllık %15-30'dur; bu depoda ayrıca 3A kuyruk ölçütü (maks düşüş ≤ %8) ve
ısı tavanı gibi risk kısıtları AYNI ANDA yürürlüktedir, yani hedef yalnız getiriyle değil
düşüş-bütçesiyle de tutarlı olmak zorundadır. %25/yıl, %8 düşüş bütçesiyle Calmar ≈ 3 demektir —
iddialı ama uydurma değil. Eski yasanın aylık %7 hedefi yılda %125'e denk geliyordu (gerçekçi bir
programın 2-3 katı): payda şişince pay küçülür ve terim ikinci kez ezilirdi.

BU MODÜL HÜKÜM VERMEZ. Hükmü `reflect.submit` verir, ölçümü `probgate` yapar; burada yasanın
TANIMI, ölçülmüş sabitleri ve eski yasanın gölge hesabı durur.
```

## `meridian/sieve.py`

```text
sieve.py — ELEME MUHASEBESİ (2026-07-21'in doğrudan çıktısı).

NEDEN VAR: 2026-07-21'de bir günde on üç hata çıktı ve HİÇBİRİ istisna fırlatmadı. Hepsi birebir
aynı şekilde davrandı: `.get()` None döndü → satır çıplak bir `continue` ile atlandı → bir sayı
sessizce küçüldü → kimse fark etmedi. Somut örnekler:

  * `trades.jsonl` satırlarında `setup`/`score` YOKTU (eski şemayla tohumlanmış defter) → 90 GERÇEK
    işlemin 90'ı da skor kalibrasyonundan ve gölge model eğitiminden elendi. Panoda "gerçek 0 /
    simüle 241" yazıyordu; harmanlanmış TEK sayı (241) bunu gizledi.
  * cf satırları `r_multiple_expected`'i `rr_expected` diye yeniden adlandırıyordu → yaması olan
    tüketici çalıştı, olmayan her satırı sessizce eledi.
  * Çözülmüş cf satırlarının %70'i `regime: "?"` taşıyordu, buna rağmen bir öneri üreteci o kanıttan
    `knob@rejim` tavsiyesi çıkarıyordu.

NE YAPAR: her sessiz `continue`yi SAYILI ve GEREKÇELİ bir elemeye çevirir. Amaç tek bir cümlede:
**"0 satır çıktı" bir daha asla "zaten satır yoktu" ile karıştırılamasın.**

ÇEKİRDEK FİKİR — NEDEN SINIFLANDIRMASI (modülün asıl değeri budur):
  `sema:*`    VERİ SÖZLEŞMESİ nedeni — eksik alan, yanlış anahtar biçimi, takma ad uyuşmazlığı,
              çözülemeyen değer. Bu bir HATADIR; birinin kodu/defteri düzeltmesi gerekir.
  `piyasa:*`  MEŞRU iş filtresi — skor eşiğin altında, yanlış rejim, girilmemiş plan, kazanç
              ambargosu. Bu BİLGİDİR; sistemin çalıştığının kanıtıdır.
Sınıfsız bir neden REDDEDİLİR (ValueError). "Neden elendi?" sorusunun cevapsız kalması, bu modülün
var olma sebebinin ta kendisidir — cevapsızlığa geri dönüş yolu kapalı olmalı.

DEDEKTÖRÜN KURT MASALI ANLATMAMASI: yalnız `sema:` elemeleri ihlal üretir. `piyasa:` elemeleri ne
kadar büyük olursa olsun ihlal DEĞİLDİR — aksi hâlde operatör uyarıyı görmezden gelmeyi öğrenir.

SIFIR YETKİ: burada hiçbir şey karar vermez, hiçbir işlem/portföy durumuna dokunmaz. Yalnız sayar
ve rapor eder.
```

## `meridian/skill_evolve.py`

```text
skill_evolve.py — Skill Revizyon Döngüsü v1 (#5): içerik evriminin güvenli ilk adımı.

Karne artık cf hızında doluyor (skill başına gerçek+sim katkı) ama karnesi kötü skill'in İÇERİĞİ
sonsuza dek aynı kalıyordu. Bu modül döngüyü TASLAK-DÜZEYİNDE kapatır: ölçülmüş-zayıf bir skill için
ajan — katkı verisi, çıkış-verimliliği ve derslerle temellendirilmiş — revize SKILL.md TASLAĞI yazar.

SINIRLAR (v1, bilinçli mütevazı):
  * OTOMATİK HİÇBİR ŞEY DEĞİŞMEZ: taslak yan dosyaya yazılır (SKILL.md.v2-draft), Skiller sayfasında
    görünür; operatör ONAYLARSA yürürlüğe girer (eski sürüm arşivlenir), REDDEDERSE silinir.
  * Korunan skill'ler (kapı, devre kesici…) ve çekirdek üçlü ASLA aday olmaz.
  * Haftada en fazla BİR taslak (ajan bütçesi + operatör dikkati şişmesin).
  * Uygulama tarihi kayda geçer — karne ileride sürüm-öncesi/sonrası kıyaslanabilsin.
```

## `meridian/skill_gorus.py`

```text
skill_gorus.py — GÖRÜŞ DEFTERİ v1 (ön-kayıt kartı EDG-2026-019, 2026-08-09).

NEDEN VAR — KISIR DÖNGÜNÜN GÖLGE TARAFTAN KIRILMASI. Aktif skill kümesinin aday seçimine ölçülebilir
bir katkısı olup olmadığı BİLİNMİYOR, çünkü skill'ler üretimde hiç koşmuyor ve Eksen-2 (doğru
olarak) kanıtsız öneri üretmeyi reddediyor. "Ölçmek için koşmalı, koşturmak için ölçmeli" döngüsü.
Bu katman döngüyü İCRAYA DOKUNMADAN kırar: skill'ler yapılandırılmış GÖRÜŞ yazar, yüzey başına bir
ÇÖZÜCÜ o görüşü GERÇEKLEŞEN sonuçla puanlar, hüküm yüzey-başına kanıtla operatöre gider.

NE YAPMAZ — VE BU BİR SÖZLEŞMEDİR.
  * HİÇBİR TERFİ OTOMATİK DEĞİL. FDR-sağkalanlar yalnız Eksen-2 teşhisine ve rapora düşer;
    bu modül kayıt defterine, bayrağa, eşiğe, plana, emre DOKUNMAZ. (2026-08-06 Eksen-2 kararının
    devamı: motor-içi bayrak yazımı yasağı.)
  * İLERİ-BAKIŞ YOK. Görüş satırı YALNIZ t ve öncesi veriyi taşır (skor plan anındadır); sonuç
    defterde DEĞİL, çözücünün ayrıca okuduğu SONUÇ defterlerindedir. İkisini tek satırda
    birleştirmek, görüşün içine cevabı yazmak olurdu.
  * EŞİK İCAT ETMEZ. Bütün eşikler karttan gelir ve ölçümden ÖNCE donduruldu (aşağıda `KART_*`).

DAVRANIŞSAL TÜKETİCİ İLK GÜNDEN (uyuyan-yol dersi: önden bağlı arkadan bağsız yüzey İNŞA EDİLMEZ).
Defterin iki okuyucusu bu turda BAĞLANDI ve ikisi de bu modülün DIŞINDADIR:
  1. `api._eksen2_gorus()` → `/api/skills` yükünde `gorus_defteri` alanı (pano/operatör yüzeyi),
  2. `scheduler._learning_cadence` → kadansın kendi çıktısında `gorus` bloğu (öğrenme defteri).
```

## `meridian/skills.py`

```text
skills.py — the pipeline runner. Skills are bound into five DETERMINISTIC pipelines (§3), each
with a fixed trigger, fixed inputs, and a fixed output artifact — this is what makes the agent
auditable. Every run appends to pipeline_runs.jsonl; nothing the agent does is invisible.

At L0 the engine's deterministic core (regime.py, strategy.py) produces the pipeline artifacts.
The Claude skills are the brain's toolkit: LLM-driven skills are invoked by Hermes during
reflection/research; FMP-`req` skills enrich candidates once a key is present. Disabled skills are
recorded as skipped-with-reason, never faked.

2026-07-30 SKILL DENETİMİ: 68 klasörden 37'si `skills/_emekli/` altına ARŞİVLENDİ (22 emekli +
15 birleştirilen; silme yok, geri alınabilir) — geride 31 canlı SKILL.md kaldı. Arşivlenenlerin
kayıtları `retired: true` ile duruyor (kayıt silinmedi: dürüst envanter + geri dönüş yolu) ve
PIPELINES zincirlerinden çıkarıldı, çünkü zincirde durup her koşuda 'declared_not_run' yazılmak
"çalışıyor" izlenimi üretiyordu. Katalog taraması `_` ile başlayan dizinleri atlar.
```

## `meridian/spend.py`

```text
spend.py — the Hermes cost ledger + budget guard. A self-improving agent that calls an LLM every
few closed trades can quietly run up a bill; this makes the spend explicit and bounded. Every real
Claude call appends its token usage and estimated USD to state/spend.jsonl, and before a call
over_budget() refuses once the month's spend hits the budget (Hermes then falls back to the free
deterministic proposer — the loop keeps learning, just without paid inference). Nothing here needs a
key to build; it simply activates when Hermes runs. Prices are env-overridable for when they change.
```

## `meridian/sprint.py`

```text
sprint.py — the 'öğrenme antrenmanı' (learning sprint) CONTROL SURFACE.

TETİK: OTOMATİK KADANS + operatör override (2026-07-30, operatör mandası "elle tetik beklemeden tam
fonksiyonlu"). Başlığı 2026-07-30 öncesinde "Operator-triggered" diyordu ve bu ÖLÇÜLEBİLİR bir kusur
üretiyordu: son sprint 2026-07-22'de koştu, sekiz gün önce, çünkü kimse düğmeye basmadı — döngüyü
DAKİKALARDA kapatabilen tek mekanizma, operatörün hafızasına asılıydı. Kadans `maybe_start()`tedir;
pano/CLI düğmesi (`start()`) OVERRIDE olarak aynen durur ve hiçbir kapıya uğramaz.

Why it exists: the live loop is trade-starved — a shipped v2 would take ~1.5 years of live paper to accrue
min_sample trades, so the reflect→outcome loop never closes. The sprint closes it in MINUTES on historical
FORWARD data, honestly:

  * It runs in a SEPARATE OS SUBPROCESS with its own MERIDIAN_ROOT (a sandbox under state/sprint/<id>).
    The live paper book, ledgers, scoreboard, and the running scheduler/Hermes are NEVER touched — there is
    no rewind and nothing to restore.
  * Selection and measurement use DISJOINT calendar windows: the coordinate-descent search selects a v2
    through the UNCHANGED OOS gate on data ≤ CUTOFF; the realized_delta is then measured ONLY on trades from
    the strictly-later eval window. No look-ahead leakage.
  * v1 and v2 are each walked forward over the SAME eval window from an identically-reset FLAT book, so the
    market regime is common-mode and cancels — the delta reflects the parameter change, not a regime gap.
  * The result is a clearly-labeled TRAINING calibration point. It is NEVER merged into live calibration(),
    the real-money autonomy ladder, or the live proposer. To close the LIVE loop for real, the discovered
    candidate must still clear the PRODUCTION gate and accrue production trades — the sprint de-risks
    discovery, it never bypasses the law.
```

## `meridian/sprint_run.py`

```text
sprint_run.py — the CHILD process of a learning sprint (launched by sprint.start()).

Invoked as `python -m meridian.sprint_run <sbroot> <cfg-json>` with MERIDIAN_ROOT pointed at the sandbox, so
every config/store read-write lands in the sandbox — the live book is untouched. Three phases:

  A. v1 FORWARD BASELINE — walk daily_cycle over the eval window from a flat book (parent=None, so the
     unmodified evaluate_outcomes no-ops). Produces the honest same-window v1 trade sample.
  B. SEARCH + SHIP — reflect.search_and_submit through the UNCHANGED gate on the DISJOINT select window.
     Ships v2 (parent=v1) or reports no_clearing_candidate.
  C. v2 FORWARD CANDIDATE — reset to a flat book, walk the SAME eval window. daily_cycle tags v2 trades and
     calls evaluate_outcomes; when v2 clears min_sample the loop closes with a leakage-free realized_delta.

Progress is copied to the LIVE sprint_status.json ($MERIDIAN_SPRINT_STATUS) every few sessions so the
dashboard shows a live bar.
```

## `meridian/storage.py`

```text
storage.py — DEFTER ÇEKİRDEĞİNİN SQLite ARKA UCU (WP-H/H9, Kademe A).

NEDEN VAR. Bugüne kadar altı defter dosyaydı (JSON/JSONL) ve `store.py` onları atomik yazıyordu.
Atomiklik TEK bir yazım için doğruydu ama şu iki sınıf açıktı:

  * OKU-DEĞİŞTİR-YAZ yarışı SÜREÇLER ARASINDA: `store.file_lock` bir `threading.RLock`tur, yani
    YALNIZ aynı süreçte anlam taşır. Canlı worker + pano API + sprint AYNI dosyaya yazabiliyordu;
    kaybeden yazım hiçbir yerde görünmüyordu (bu depoda belgeli tehlike sınıfı).
  * JSONL EKLEME ATOMİK DEĞİLDİ: çökme ya da disk dolması yarım satır bırakır; `store.read_jsonl`
    o satırı sessizce eler (`jsonl_rows_skipped` uyarısı bunu SAYAR ama kaybı geri getirmez).

SQLite ikisini de YAPISAL olarak kapatır: tek transaction + WAL + süreçler-arası kilit çekirdeğin
kendisindedir. Kazanç ŞEMA DEĞİL, ATOMİKLİK + SÜREÇLER-ARASI KİLİTtir — bu yüzden tekil-belgeler
(scoreboard/portfolio/shadow_books) tek-satır-belge tablosudur; aşırı-normalizasyon yapılmadı.

DIŞ İMZALAR DEĞİŞMEZ. Bu modülü uygulama kodu DOĞRUDAN çağırmaz; `store.py` altı defter adını
buraya yönlendirir ve çağıranlar bugünkü dict/list yapılarını almaya devam eder. Bu bir DEPOLAMA
migrasyonudur, davranış migrasyonu DEĞİL.

ANAHTARLAMA KAPISI (`active`). DB YOKSA her şey eskisi gibi dosyadan okur/yazar. DB `dbmigrate`
ile DOĞDUĞU an altı defter DB'ye geçer. Yani kod dağıtımı ile veri geçişi AYRI iki olaydır:
Rol-1 bakım penceresinde `python -m meridian.dbmigrate --uygula` koşana kadar davranış birebir
bugünküdür.

`MERIDIAN_DB=off` TEK BAŞINA GERİ DÖNÜŞ DEĞİLDİR (C5, 2026-08-02 — bu satır eskiden onu "acil geri
dönüş anahtarı" ilan ediyordu ve YANLIŞTI). Migrasyondan sonra kaynak dosyalar `.migrated` ADIYLA
durur; `store._path` kanonik ada bakar, bulamaz ve çağıranın VARSAYILANINA düşer. Yani anahtarı tek
başına çeken operatör "eski hâle döndüm" sanırken altı defteri BOŞ okur ve ilk yazımda AYRIŞIK
ikinci bir kitap doğar (`last_id` sıfırlanır → kimlik çakışması). Bugünkü sözleşme İKİ parçalıdır:
  * GERİ DÖNÜŞ KOLU: `python -m meridian.dbmigrate --geri-al` — DB'yi kenara alır, `.migrated`
    arşivlerini ASIL adlarına döndürür, DB ile dosya satır sayılarını rapor eder. Veri SİLMEZ.
  * ANAHTAR (`MERIDIAN_DB=off`): kolun ÇEKİLDİĞİNİ varsaymaz, ÖLÇER. Anahtar açıkken DB dosyası
    dururken kaynaklar hâlâ `.migrated` ise `active()` süreç başına BİR KEZ `obs.warn` basar
    (`db_off_kaynaklar_arsivde`) — sessizce boş varsayılana düşmek bu bulgunun kendisiydi.

YOL ÇAĞRI ANINDA ÇÖZÜLÜR. `config.STATE` ölçüm sandbox'larında (testler, sprint, mutasyon)
değiştirilir; modül yükleme anında yol dondurmak o sandbox'ları KIRAR — bu yüzden `db_path()`
her çağrıda `config.STATE`i okur ve bağlantı havuzu YOLA göre anahtarlanır.

TİP KORUMA (parite sözleşmesi). Tipli kolonlar sorgulanabilirlik içindir; DOĞRULUK kaynağı
değildir. Bir alanın Python tipi kolonun beklediğinden farklıysa (ör. `score` int beklenirken
float gelirse) alan AYRICA `extra_json`a yazılır ve okumada `extra_json` KAZANIR. Böylece
SQLite'ın tip afinitesi (60 → 60.0 dönüşümü) sessizce veriyi değiştiremez: parite digesti
`dbmigrate`de bunu ölçer ve eşleşmezse migrasyon BAŞARISIZ sayılır.
```

## `meridian/store.py`

```text
store.py — state persistence helpers. Atomic JSON writes, JSONL append, and numpy sanitization
so nothing on disk carries np.float64 (which breaks json). state/ is the only mutable directory.

WP-H/H9 (2026-07-31) — İKİ SERTLEŞTİRME + BİR YÖNLENDİRME, DIŞ İMZA DEĞİŞMEDEN:

  (B1) ATOMİK YAZIM ARTIK DAYANIKLI: mkstemp + write + **fsync** + os.replace + dizin fsync.
       `os.replace` yer değiştirmenin ATOMİK olduğunu garanti eder ama VERİNİN diske indiğini
       etmez — güç kesintisi/panic sonrası dosya var ama SIFIR baytlık olabilirdi. fsync o sınıfı
       kapatır. Dizin fsync'i yer değiştirmenin kendisini kalıcı kılar (en iyi çaba: bazı dosya
       sistemlerinde dizin fd'si fsync kabul etmez).

  (B2) `file_lock` ARTIK SÜREÇLER ARASI: `fcntl.flock` + `state/.locks/<ad>.lock`. Eski hâli
       `threading.RLock`ti, yani YALNIZ aynı süreçte anlam taşıyordu; canlı worker + pano API +
       sprint aynı dosyaya yazabiliyordu ve kaybeden yazım hiçbir yerde görünmüyordu. API AYNI
       (`with store.file_lock(ad):`), yeniden girişli (RLock) davranış AYNI — tüm mevcut
       çağıranlar bedavaya sertleşir.

  (A3) ALTI DEFTER SQLite'a YÖNLENDİRİLİR: `meridian/storage.py` DB dosyası VARSA (yani Rol-1
       bakım penceresinde `dbmigrate --uygula` koşulduysa) `trades.jsonl`, `trade_plans.jsonl`,
       `scoreboard.json`, `portfolio.json`, `equity_curve.json`, `shadow_books.json` okuma/yazması
       DB'ye gider. DB YOKSA davranış BİREBİR bugünküdür. Çağıranlar aynı dict/list yapılarını
       almaya devam eder: bu bir DEPOLAMA migrasyonudur, davranış migrasyonu DEĞİL.
```

## `meridian/strategy.py`

```text
strategy.py — PURE. No I/O, no clock reads, no network. Index -1 is ALWAYS a closed bar.
The exact same functions run in live trading and in the backtest. If they ever diverge,
every backtest number becomes a lie (§4). Signal logic only; fill mechanics live in broker.py.

The core edge is a swing-momentum breakout computed directly from OHLCV — self-contained so it
runs with or without FMP screeners. When FMP is present, screeners feed *extra* live candidates;
they never define the entry logic here.
```

## `meridian/streamhealth.py`

```text
streamhealth.py — WS DİNLEYİCİLERİNİN ORTAK YASASI (2026-07-23, Faz 2).

TEK KAYNAK: bayatlık/nabız/backoff/down-reassert/reconnect disiplini burada YAŞAR ve hem
`mirror_stream` (yürütme: trade_updates) hem `marketstream` (piyasa verisi: dakikalık bar) onu
İÇE AKTARARAK kullanır — `mirror_stream.next_backoff IS streamhealth.next_backoff` (aynı nesne).

NEDEN AYRI MODÜL (operatör mandası — ERADİKASYON, hafifletme değil): bu kod tabanının baskın kusuru
"aynı yasanın İKİ uygulaması, sessizce ayrışmış"tır. mirror_stream'in 54→2 `down` kusuru (kopuş saati
her turda sıfırlanıyordu) tam da bu DURUMSAL yasada yaşadı. İkinci bir akış (marketstream) o yasayı
KOPYALASAYDI, en riskli kodu korumasız ikiye bölerdik. Ayrıştırma divergence'ı YAPISAL olarak imkânsız
kılar: iki tanım yok, tek nesne var. `test_streamhealth_parity_v84` bunu kimlik (`is`) + AST-yokluk
ile kilitler (kopya yeniden-girerse tarayıcı işaretler).

SINIR: store/disk BİLMEZ. Kalıcılık, StreamHealth'e enjekte edilen `persist` geri-çağrısıyla gelir —
mirror'da `write_json` (yürütme gerçeği restart-güvenli olmalı; loop.py `pending_symbols`'ı süreç-DIŞI
okur), market'ta `no-op` (piyasa verisi UÇUCU; okuyan tek yer aynı süreçteki API). Disk-vs-bellek farkı
TEK parametre; yasa hâlâ tek.
```

## `meridian/threshold_curve.py`

```text
threshold_curve.py — MIN_SCORE EŞİK EĞRİSİ: kapıyı yükseltmek kâr getirir mi?
(Kârlılık Programı Aşama 1.3, 2026-07-29)

CEVAPLADIĞI SORU. `entry.min_score` canlıda 60. Bu sayı bir ÖLÇÜMDEN değil, ilk günkü bir
varsayımdan geliyor. "Yükseltsek daha az ama daha iyi işlem mi alırız?" sorusunun bugüne kadarki
tek kanıtı, 95 işlemin skor dilimlerine bakılarak yapılmış bir çıkarımdı (skor 70-80 dilimi
-0.285R, >=80 dilimi +0.066R) — ve o çıkarım TAM REPLAY'de TUTMADI: 2026-07-28 Aşama 0 turunda
H2 (min_score 60→80) OOS'u Δ-0.095 KÖTÜLEŞTİRDİ (P=0.089, ÇÜRÜDÜ). Bu modül o çelişkinin
kalıcı ölçüm yüzeyidir: dilim istatistiği ile eşik taraması aynı panoda yan yana durur.

DİLİM İSTATİSTİĞİ NEDEN REPLAY'İ YANLIŞLAMAZ (ve tersi). İkisi FARKLI SORULAR sorar:
  * eşik eğrisi (bu modül): "eşiği yükseltseydik, GEÇEN adayların ortalama ileri getirisi ne olurdu?"
    — yalnız SEÇİM etkisini ölçer, sabit ufukta, çıkış kuralından bağımsız.
  * tam replay (backtest.walk_forward): "eşiği yükseltseydik SİSTEM ne yapardı?" — daha az aday,
    farklı pozisyon sırası, farklı sermaye kullanımı, farklı eşzamanlılık, farklı çıkışlar.
Bir eşik, seçim kalitesini artırıp sistem sonucunu kötüleştirebilir (ör. en iyi adayları alırken
portföyü boş bırakmak, ya da kalan adayların hepsini aynı rejimde toplamak). Bu yüzden buradaki
eğri BİR KARAR DEĞİL, bir hipotez kaynağıdır; kapı hâlâ tek hakemdir (replay + olasılıksal kapı).
Çıktının `capraz_not` alanı bu uyarıyı sayının YANINDA taşır.

ÖLÇÜM TANIMI. x ekseni: aday skoru (`score`, hem `trades.jsonl` hem cf defterinde ALAN olarak var —
canlı dosyadan doğrulandı). y ekseni İKİ TANE ve ikisi de ayrı raporlanır:
  * `ileri_getiri` — sinyal barından 5/10/20 bar sonraki yüzde getiri, BARLARDAN
    (`component_ic.forward_returns`, tek tanım). Çıkış kuralından ve cf sadakat kusurundan
    BAĞIMSIZDIR: cf satırından yalnız giriş anı alınır (bkz. component_ic modül başlığı, karar 4).
  * `gerceklesen_r` — defterdeki `r_multiple`. Gerçek katmanda bu CANLI çıkışın sonucudur; cf
    katmanında SİMÜLE edilmiş çıkışın (sadakat kusuru burayı KİRLETİR — etiketi alanın yanında).
Roadmap 1.3 "kâr/işlem eğrisi" der; kâr/işlem tam olarak `gerceklesen_r`dir, ama tek başına
bırakılırsa cf tarafında sadakat kusurunu taşır — bu yüzden ikisi birlikte verilir.

KATMANLAR AYRI SATIR. gerçek (n≈95) ile cf (n≈2100) asla havuzlanmaz: 22:1 oranıyla cf, gerçeği
boğar ve raporlanan eğri fiilen cf'in eğrisi olur (`score_calibration`ın yıllarca yaptığı hata).
```

## `meridian/trend_shadow.py`

```text
trend_shadow.py — UZUN-UFUK TREND KOLU · CANLI PARALEL GÖLGE-KİTAP (WP-K, 2026-07-31).

NE: EDG-2026-009'un HÜKÜMLÜ incumbent kolunu (chandelier çıkış × full_251 × N=10) canlı barlar
üzerinde SANAL bir defterde ileri yürütür. Ölçüm DEĞİL — ölçülmüş bir hükmün canlı-birikimi.
Kartın ölçüm şasisine (backtest/dataset/score/shadowlaw) HİÇ dokunmaz.

SIFIR YETKİ — YAPISAL, BEYAN DEĞİL: bu modül broker/alpaca/emir yolunu IMPORT BİLE ETMEZ.
Tek yan etkisi kendi defterine (`trend_book.json`) yazmaktır; portföy, plan, karne, silahlanma ve
strateji dosyalarının hiçbirine dokunmaz. Çivisi tests/test_trend_shadow_v144.py'de AST ile
kurulmuştur: yarın eklenecek bir `from .broker import ...` satırı orada kırmızı yakar.

ŞASİ BİREBİRLİĞİ (kaynak: scratchpad/trend_kolu/engine.py — SALT-OKUNUR referans; hüküm koşumu
scratchpad/trend_rafine/poskontrol.py: `engine.run_arm(panel, uni, 10, sizing="rebalance", elig=ELIG)`):
  FRICTION_BPS=10   ATR_LEN=22   CHANDELIER_K=3.5   N=10   12-1 momentum   ay-sonu kararı,
  ERTESİ SEANS AÇILIŞI icrası, her ay 1/N'e denkleştirme. Sabitler aşağıda satır referanslarıyla.

CANLI ÇEVİRİNİN ÜÇ AÇIK FARKI (sessiz değil — okuyan bilsin):
  1. SERMAYE 100k (şaside 1M). Boyutlandırma 1/N ve tüm muhasebe oransal olduğundan getiri
     serisini değiştirmez; yalnız defterdeki dolar rakamları ölçeklenir.
  2. UYGUNLUK (elig) katmanı: şasi ölçüm-içi L1-L5 katmanını kullanıyordu (integrity.py — TARİHSEL
     bar temizliği: ölçek/kimlik kırılması karartması, 300 temiz bar, 63g medyan dolar hacmi).
     Canlıda bunun karşılığı deponun KENDİ bütünlük defteridir (`adapters.data.bars_integrity` →
     `guvenli_baslangic`); ikinci bir kopya yazmak aynı yasanın iki sürümünü doğururdu. L5 (dolar
     hacmi) canlıda YENİDEN KURULMADI — şasi onu "mega-cap evreninde bağlayıcı değil" diye
     beyan etmişti ve yeniden yazmak, ölçülmemiş bir eşiği canlıya sokmak olurdu.
  3. KİTAP GEÇMİŞSİZ DOĞAR: ilk koşumda pozisyon yok, nakit 100k. Bu bir geri-doldurma değil;
     ilk giriş ilk AY-SONUNDA olur. Kitabın eğrisi ancak ileriye doğru birikir.

PIT ŞERHİ KİTABIN İÇİNDE TAŞINIR (`pit_serh` alanı): defteri okuyan herkes yanlılık beyanını
rakamla aynı anda görür. Şerhi rakamdan ayırmak, +13,1p/yıl'ı şerhsiz okutmanın en kolay yoludur.

TAKVİM KAPISI FAIL-CLOSED: "bugün ay-sonu mu?" sorusunu XNYS takvimi (adapters.data'nın süreç-içi
tek takvimi) cevaplar. Takvim yoksa CEVAP YOKTUR ve o gün KARAR ALINMAZ (uydurma ay-sonu yerine
sessizlik değil, OLAYLI sessizlik). Ay-sonunu barlardan "o ayın en son barı" diye türetmek canlıda
YANLIŞ olurdu: ayın 12'sinde de "şimdiye kadarki en son bar" o aya aittir.
```

## `meridian/validation.py`

```text
validation.py — Y1 DOĞRULAMA ÜÇLÜSÜ: DSR/PSR + PBO/CSCV + aday getiri defteri
(Hafta 3a turu, 2026-07-30 · ROADMAP §3.1 "Y1 doğrulama üçlüsü")

NEDEN VAR. Kapı bugün TEK bir soruya cevap veriyor: "bu aday, bu pencerede incumbent'ı yeterince
büyük bir farkla geçti mi?" Sormadığı soru şu: **kaç aday denedik de bu geçti?** 289 sorgu sorulmuş
bir pencerede en iyi görüneni seçmek, bir kenar bulmak değil bir maksimum seçmektir — ve rastgele
sayılardan oluşan 289 adayın en iyisi de "OOS'ta kazandı" der. Aşınma defteri (Aşama 2.2) bu yükü
SAYIYOR ve marja çeviriyor, ama marj bir SEZGİdir: "kaç denemeden sonra bu Sharpe şaşırtıcı olmayı
bırakır?" sorusunun istatistiği ayrıdır ve adı DSR'dir (Bailey & López de Prado, 2014).

ÜÇ PARÇA:

  D1 ADAY GETİRİ DEFTERİ (`validation_ledger.jsonl`) — her RESMÎ kapı değerlendirmesinde adayın
     işlem-getiri serisi (tarih + R) kalıcı olarak saklanır. PBO'nun ham maddesi budur: PBO, N
     adayın AYNI zaman ızgarasındaki getirilerini ister ve o ızgara ancak seriler saklanırsa kurulur.
     Bugüne kadar seriler `walk_forward`ın dönüş sözlüğünde doğup istek sonunda ölüyordu.

  D2 DSR/PSR — adayın Sharpe'ı, DENEME SAYISINA ve dağılımının çarpıklık/basıklığına göre
     düzeltilir. `deflated_sharpe` ÖLÇER, hüküm vermez.

  D3 PBO/CSCV — "bu seçim yöntemi, in-sample'da en iyiyi seçtiğinde out-of-sample'da medyanın
     altına düşme olasılığı nedir?" Defterde ≥8 aday (PBO_MIN_ADAY) birikmeden HESAPLANAMAZ ve o hâlde
     dürüstçe OLCULEMEDI döner (uydurma yasağı: az veriyle üretilmiş bir PBO, ölçüm değil süstür).

--- SERT KAPI (DSR HARD-GATE TURU, 2026-07-30 — operatör onaylı MOD-FARKINDALIKLI tasarım) ---

D2/D3 ARTIK SALT ADVISORY DEĞİL. `_gate_eval`in `passes` hükmü DEĞİŞMEDİ (DSR hâlâ o satırın
ALTINDA üretilir ve ona dokunamaz); değişen yer SHIP YOLUDUR (`reflect._submit_locked`) ve kural
`dsr_kapi`/`pbo_kapi` ile TEK YERDE yazılıdır — iki tüketici (ship yolu + Faz-6 kilit zinciri) aynı
eşiği iki kez tanımlarsa iki farklı kapı doğar. Kural matrisi:

  KÂĞIT MODU (bugünkü durum: MERIDIAN_MODE=paper)
    * DSR  — BLOKLAMAZ. Ship kaydına damga: `dsr` + `dsr_dusuk` + `dsr_durum`. GEREKÇE: kâğıt
      evrimi ÖLÇÜM ARACIDIR; ana defterin öğrenme hızını istatistiksel bir uyarıyla kısmak,
      kanıt üretim hızını kanıt olmadan düşürmek olurdu. Damga o uyarıyı KAYDEDER, susturmaz.
    * PBO  — ÖLÇÜLEBİLİYORSA SERT (paper dahil). Bu bir ADAY testi değil SÜREÇ testidir: PBO
      "bu SEÇİM YÖNTEMİ aşırı-uydurulmuş mu?" diye sorar ve aşırı-uydurulmuş bir süreçten çıkan
      aday kâğıda bile inmemeli — kâğıt defter o adayın kanıtı olarak birikir ve süreç bozuksa
      biriken şey kanıt değil gürültüdür.

  GERÇEK-PARA BAĞLAMI (MERIDIAN_MODE=live + MERIDIAN_I_ACCEPT_RISK=true zinciri; bugün KAPALI)
    * İKİSİ DE SERT ve FAIL-CLOSED: ölçülemeyen DSR ya da ölçülemeyen PBO da RET. "Kanıt yoksa
      gerçek para kapısı kapalı" — UYDURMA YASAĞI'nın kapı hâli. Ölçülemeyen bir kontrolü
      "geçti" saymak, yapılmamış bir testin sonucunu uydurmaktır ve tam bu modül onu yasaklar.

UYGULANAMAYAN KONTROL VETO OLAMAZ (kâğıt tarafın simetrik kuralı): PBO taban dolmadan
(<PBO_MIN_ADAY aday, TEK pencere-ızgarası) hükümsüzdür ve kâğıtta veto etmez. Havuzlama YASAK —
iki `pencere_id` iki sınav kâğıdıdır (ledgers sözleşmesi; R1 düzeltmesi).

--- ÜÇ BEYAN ---

(1) SANDBOX SAYMAZ. `config.STATE` yönlendirilmiş her ölçüm (test, sprint kumu, ön-eleme) kendi
    kopyasına yazar; resmî defter dokunulmaz. Aşınma defterinin (oos_erosion) beyanı (2) ile birebir
    aynı gerekçe — resmî defter yalnız RESMÎ kapı değerlendirmelerini görür.

(2) RETRO DAMGA YOK. Geçmiş 19 kapı kaydı geriye dönük seri üretilerek deftere işlenMEZ: o
    adayların işlem serileri hiçbir yerde saklanmadı (kapı kaydı yalnız `oos_score` taşıyor) ve
    yeniden koşularak "geçmişte de ölçmüştük" gibi sunulması, tam olarak bu modülün önlemek için
    var olduğu şeydir. Defter BUGÜNDEN sayar.

(3) DENEME-SAHRE VARYANSI İKİ KAYNAKTAN GELİR VE HANGİSİ OLDUĞU ÇIKTIDA YAZAR. DSR formülü
    E[max SR] için denemelerin Sharpe'larının VARYANSINI ister. Defterde yeterli kayıt varsa o
    varyans ÖLÇÜLÜR (`varyans_kaynagi: "deneme_defteri"`); yoksa sıfır-beceri null dağılımının
    analitik yaklaşımına düşülür (`varyans_kaynagi: "sifir_beceri_null"`). İkisi AYNI sayı değildir
    ve hangisinin kullanıldığını gizlemek, düzeltmenin kendisini uydurma yapardı.
```

## `meridian/validation_report.py`

```text
validation_report.py — "hangi mekanizma/edge KANITLANIYOR?" (2026-07-21).

cf-tarih bootstrap sonrası dolu karşı-olgusal defter üzerinden, sistemin sinyallerini/edge'ini TEK
tabloda dürüstçe raporlar: temel edge, skor kalibrasyonu, ekran/kurulum katkısı, rejim edge'i, eşik
karnesi (near-miss) ve cf↔gerçek sadakati. SALT-OKUMA analiz — hiçbir karar/kapı etkilenmez; her satır
n ve anlamlılık taşır (yetersiz örneklemde 'kanıt yok' der, uydurmaz).
```

## `meridian/versioning.py`

```text
versioning.py — strategy.yaml version bumps, immutable history snapshots, and the scoreboard.
A parameter change is a version bump + a state/history/vNNNN.yaml snapshot + a hot-reloadable
strategy.yaml. No redeploy for a parameter change (§5); deploy.sh is for code only.
```

## `meridian/watchdog.py`

```text
watchdog.py — Mekanizma Bekçisi (#1): 15+ periyodik dişlinin canlılık nabzı.

Panel bugüne dek VERİNİN tazeliğini gösteriyordu; MEKANİZMANIN kendisi sessizce durduğunda kimse
görmüyordu (canlı örnek: ısınma kadansı anomalisi günlerce 'not edildi' kaldı). Her mekanizma
koştuğunda `beat(ad)` damgalar; `report()` beklenen pencereyle karşılaştırır ve gecikenleri listeler.
Pencereler takvim-gerçekçi: seans-bağımlı işler hafta sonunu tolere eder (4 gün), haftalıklar 9 gün.

Yalnız GÖZLEM: bekçi hiçbir mekanizmayı yeniden başlatmaz, hiçbir kararı etkilemez — amber satır
üretir, teşhisi operatöre/paneline bırakır.
```

## `meridian/adapters/__init__.py`

```text
meridian.adapters — dış dünya kenar katmanı (veri sağlayıcılar + Alpaca broker).

Yasa: adapters yukarı-yön import etmez — kenar katman motoru tanımaz
(pyproject.toml [tool.importlinter] sözleşme 1; bilinçli istisnalar orada listeli).
```

## `meridian/adapters/alpaca.py`

```text
adapters/alpaca.py — Alpaca broker adapter. PAPER by default. The LIVE path is refused unless
BOTH env flags are hand-set (MERIDIAN_MODE=live AND MERIDIAN_I_ACCEPT_RISK=true) AND goal.limits
.autonomy_level >= 1 (enforced in guard.py). alpaca-py is imported lazily so the engine runs at L0
without it installed. PnL/fills that count are ALWAYS the internal broker.py simulator's; this module
is the MIRROR. But note: with MERIDIAN_BROKER=alpaca_paper (serve.sh's default, and what runs today)
the mirror path IS live every cycle — submit_plan() is called from loop.py on every armed plan. The
old docstring claimed this module "is only reached once the live path is enabled"; that was false and
hid the fact that a mirror failure can drop a real armed plan (audit 2026-07-21).

YAZILI VARSAYIMLAR (denetim 2026-07-21 — her biri artık bir kontrol ya da testle bağlı):
  A1 read-only uçlar (account/positions/orders) HİÇBİR ZAMAN istisna fırlatmaz; hata durumunda
     None/[] döner. Bu yüzden çağıranın try/except'i ÖLÜ KOD'dur ve "broker ulaşılamıyor" ile
     "hiç emir yok" ayırt edilemez → `transport()` sağlık kaydı bu ayrımı taşır. Çağıran, boş
     listeye bakıp mutabakat kararı vermeden ÖNCE transport()["ok"] kontrol etmelidir.
  A2 client_order_id == iç plan kimliği ve ENGINE_COID_PREFIX ile başlar. Mutabakat "motor yetimi"
     tespitini bu önekle yapar; önek kayarsa yetimler sessizce 'external' altında saklanır.
  A3 Bu hesap YALNIZ motora ait DEĞİL — operatörün kendi pozisyonları (bugün: NVDA) ve elle
     girdiği emirler aynı kağıt hesapta. Motor SAHİBİ OLMADIĞI emri iptal edemez / pozisyonu
     düzleştiremez (cancel_open_entries önek süzgeci + close_all onay jetonu).
  A4 Koruma (stop) asla gevşetilmez: replace_order_stop yalnız YUKARI. Eskiden bunu yalnız çağıran
     katman garanti ediyordu; artık sınırın kendisi reddediyor.
```

## `meridian/adapters/constituents.py`

```text
adapters/constituents.py — point-in-time S&P 500 üyeliği (#36).

DENETİM 2026-07-21 (dönüşümlü tur 3) — bu modül hakkında DÜRÜST DURUM:
  * Hiçbir üretim yolu bunu ÇAĞIRMIYORDU. `current()`/`as_of()` yalnız testlerden çağrılıyor; canlı
    evren elle bakımlı `data.REPLAY_UNIVERSE`. Yani #49/#52/#53 denetimlerinde düzeltilen üç gerçek
    hata, hiçbir zaman koşmayan bir kodda düzeltilmişti. (Desen 1: koşuyor mu değil, ÜRETİYOR mu.)
  * Wikipedia yolu bu kurulumda ÇALIŞAMAZ: (a) `pandas.read_html` lxml/bs4/html5lib ister — üçü de
    kurulu değil; (b) Wikipedia bu User-Agent'a **403** dönüyor (bot politikası). İkisi de
    `except: return None` ile yutuluyordu, dolayısıyla modül sessizce hep bayat önbelleği döndürürdü.

BU BEYAN 2026-08-13'TE YENİDEN ÖLÇÜLDÜ — YARISI ÇÜRÜMÜŞTÜ (v238 arıza turu):
  * (a) ARTIK YANLIŞ. lxml 6.1.1 KURULU ve `pyproject.toml`da ANA bağımlılık (satır 29). Ayrıştırıcı
    yokluğu 2026-07 kökü olarak GEÇMİŞTE kaldı; beyan güncellenmediği için canlıdaki gerçek arıza
    aylarca "eski, bilinen bir sınır" sanıldı. ÖLÇÜLEN GERÇEK KÖK BAŞKAYDI: pandas 3.0.3'te
    `read_html` ham HTML DİZGESİ kabul etmiyor — dizgeyi dosya-yolu sanıyor ve canlı
    `state/universe_drift.json` `reason: "FileNotFoundError: [Errno 2] ... <!DOCTYPE html>..."`
    yazıyordu. Yerelde birebir üretildi (pandas 3.0.3): ham dizge → FileNotFoundError,
    `io.StringIO(...)` → parse OK. Düzeltme `_fetch_tables` içinde, gerekçesiyle.
  * (b) HÂLÂ DOĞRU. 2026-08-13 ölçümü: `GET` + `User-Agent: Meridian/1.0` → **HTTP 403**, gövde 141
    bayt. Yani StringIO düzeltmesinden SONRA da bu kurulumda Wikipedia'dan üyelik listesi GELMEZ;
    değişen şey, gelen HTML'in artık ayrıştırılabilir olması (kaynak açılırsa/UA değişirse yol
    çalışır) ve `health()`in artık DOĞRU nedeni yazması (`HTTP 403`, uydurma bir dosya-yolu hatası
    değil). Zincirdeki birincil kaynak FMP'dir; Wikipedia en iyi-çaba ikincil olarak KALIR.
  * Diskteki ÜRETİM önbelleği TEST VERİSİYDİ: {"as_of": "2099-01-01", "current":
    ["AAPL","MSFT","NVDA"], changes:[{removed:"nan"}]} — bir test koşusu gerçek state klasörüne
    sızmıştı (2026-07-18). Bir tüketici olsaydı S&P 500 diye ÜÇ sembol alacaktı ve `as_of()` uydurma
    bir tarihsel üyelik üretecekti. Karantina: state/quarantine/.

BU YÜZDEN artık: (1) kaynak zinciri FMP'yi (anahtarlı, zaten kullanımda) birincil yapar, Wikipedia
en iyi-çaba ikincildir; (2) her okuma/yazım MAKULLUK KAPISINDAN geçer — 400'den az sembol S&P 500
değildir, reddedilir; (3) başarısızlık SESSİZ değildir: `health()` + watchdog üretkenlik dedektörü;
(4) `universe_drift()` gerçek bir tüketicidir — elle bakımlı evrendeki ölü isimleri söyler.

HONEST LIMIT (değişmedi): bu, üyelik survivorship'ini düzeltir; gerçekten yanlılıksız bir backtest
delisted isimlerin BARLARINI da ister ve ücretsiz kaynaklar onu taşımaz. PIT iskelesi, bias-free
evren değil.
```

## `meridian/adapters/data.py`

```text
adapters/data.py — real daily OHLCV, no API key. Primary: Cboe delayed_quotes historical
(clean full-history JSON, split-adjusted). Fallback: Nasdaq historical API. Cached to state/bars/.

Adds: validate_bars() — an integrity gate so a single unadjusted split can't inject fake gaps that
poison the backtest (Hard Rule 7); incremental cache (fetch only when the cache is stale, then merge);
and exponential backoff on transient fetch errors.
```

## `meridian/adapters/edgar_shares.py`

```text
edgar_shares.py — EDGAR AS-OF DOLAŞIMDAKİ HİSSE SAYIMI: SALT-OKUNUR VERİ KÖPRÜSÜ.

NE VAR BURADA. `research/edgar_facts/shares_outstanding.csv.gz` (SEC XBRL companyfacts,
161.856 satır · 258 sembol) deponun içinde STATİK bir dosyadır ve aylık olarak
`research/edgar_facts/betikler/` ile tazelenir. Bu modül o dosyayı OKUR ve tek bir soruyu
cevaplar: "t gününde bu sembolün dolaşımdaki hisse sayısı — O GÜN BİLİNEBİLEN hâliyle — kaçtı?"
Yazma yolu YOKTUR: ne bu dosyaya ne state'e tek bayt yazılır (canlı worker koşarken state'e
yazım bu depoda yasak, ve bu modül canlı tarama yolunda çağrılır).

NEDEN GEREKLİ. EDG-2026-016 hükmü (2026-08-01, SUCCESS): turnover21 = medyan21(hacim) /
as_of_shares(t) kesitsel olarak MONOTON bilgi taşıyor — üst %20 dilim evren-fazlası @20 +0,65%
CI[+0,34,+1,01], rvol20+mom21 kontrolünden sonra ARTIK üç yöntemle birden sağ, maliyet-sonrası
net +0,55%. Ölçüm `wp2_olcum/ortak.py` altyapısıyla yapıldı; ölçülmüş yolu canlı motora
bağlamanın önkoşulu, PAYDANIN (hisse sayımı) canlı yolda da AYNI kurallarla okunmasıdır.

--- AS-OF/ETİKET/TEMİZLİK KURALLARI: ÖLÇÜMLE BİREBİR (ortak.build_hisse'den port) -------------
Aşağıdaki altı kural ölçüm turunun kodundan BİREBİR alınmıştır. Sayıların ölçümdekiyle aynı
çıkması bunlara bağlıdır; birinin "sadeleştirilmesi" canlı payda ile ölçülmüş paydayı sessizce
ayırırdı (ve EDG-016'nın kanıtı canlıda geçerli olmaktan çıkardı):

  (1) PIT: t gününde bilinen küme `filed <= t`'dir. `end <= t` filtresi PIT DEĞİLDİR ve geleceği
      sızdırır (README'nin GOOGL 20:1 örneği: aynı `end`, iki `filed`, iki değer).
  (2) ETİKET: yalnız ANLIK iki etiket — dei:EntityCommonStockSharesOutstanding (kapak sayfası,
      medyan 7g gecikme) ve us-gaap:CommonStockSharesOutstanding (bilanço, ~36g). `...Issued`
      KULLANILMAZ (hazine farkı), ağırlıklı-ortalama serileri SEVİYE olarak KULLANILMAZ (yalnız
      bölünme yeniden-beyanının KANITI olarak okunur, bkz. `_split_olaylari`).
  (3) BİRİNCİL ETİKET: dei'de en az 8 farklı `filed` varsa dei; yoksa us-gaap; o da yoksa dei.
      Birincilde 200 günden uzun boşluk varsa o boşluğa ÖTEKİ etiketten kayıt eklenir (yedek).
  (4) BÖLÜNME/GÜNCEL BAZ: bir dosyalamada bildirilen sayı O GÜNKÜ hisse birimindedir; bar hacmi
      ise güncel bazda split-düzeltilmiştir. İkisini bölmek için hisse sayımı güncel baza çevrilir:
      shares(t) = val(f_t) × B_son / B(f_t). Bölünme takvimi EDGAR'ın KENDİ geriye-dönük yeniden
      beyanından türetilir (bar serisinden okunamaz — bar zaten düzeltilmiş).
  (5) BAYATLIK BEKÇİSİ: son dosyalama t'den 200 günden eskiyse as-of değer YOKTUR (None + neden).
      Ölçümde 27 sembolde işledi (SCHW 1006, V 4007, NKE 2934 hücre...).
  (6) ÖLÇEK-HATASI PENCERESİ: açıklanamayan >=5× sıçrama 6 dosyalama içinde ~1/oran ile geri
      dönüyorsa aradaki kayıtlar GEÇERSİZDİR (None + neden).

BURADA OLMAYAN TEK BEKÇİ — VE NEREDE OLDUĞU. Ölçümün FİZİKSEL DEVİR BEKÇİSİ (medyan-21g hacim
dolaşımdaki hissenin tamamını aşamaz → devir>1 imkânsız) bu modülde DEĞİL, `indicators.turnover21`
içindedir. Sebebi yapısal: bekçi hisse sayımına DEĞİL, hacimle kurulan ORANA bakar; burada
uygulamak bu modüle bar verisi taşımak olurdu. Fark yazılı olsun: ölçümde bekçi bir KAYDIN
geçerlilik penceresini toptan geçersiz kılar (pencere medyanı üzerinden), canlı yolda ise NOKTASAL
çalışır (yalnız devir>1 çıkan barda None). Noktasal biçim aynı imkânsızlığı aynı yönde eler; farkı
şudur ki penceredeki "temiz" günleri ayakta bırakır — yani daha az agresiftir ve hiçbir uydurma
değeri ölçüme sokmaz.

FAIL-OPEN BEYANI (bu modülün SÖZLEŞMESİ). Dosya yoksa, okunamıyorsa, sembolün serisi yoksa,
seri bayatsa ya da kayıt geçersizse → dönen değer None'dur ve NEDENİ adıyla verilir. None'un
ANLAMI "sıfır hisse" değil "ÖLÇÜLEMEDİ"dir; çağıran taraf bunu 0 gibi kullanamaz (skor tarafındaki
karşılığı ve gerekçesi `strategy.evaluate_entry`in turnover bloğunda yazılıdır). Her çağrı
`okuma_raporu()` sayaçlarına düşer; sayaçların tüketicisi `component_ic.json`in `turnover_kaynak`
alanı ve gecelik `component_ic` olayıdır (YASA 6: okuyucusuz yazım yok).

OLAY MI SAYAÇ MI — AYRIM BİLİNÇLİ VE ÖLÇÜLDÜ. Bu modül SKOR yolundan, sembol döngüsünün içinden
çağrılır ve `obs.warn` bir DEFTER YAZIMIdır. Kapsam-dışı sembol başına uyarı atmak, saf skor
hesabını canlı `events.jsonl`a yazan bir G/Ç yoluna çevirirdi — ölçüldü: eklendiği anda sentetik
sembollü mevcut testler canlı deftere yazmaya başladı ve sızıntı bekçisi kırmızıya döndü. Bu yüzden
SEMBOL düzeyi olgular SAYILIR ve ADIYLA raporlanır (`okuma_raporu().kapsam_disi_sembol`), KAYNAK
düzeyi olgular (dosya yok / okunamadı) UYARIR — onlar süreç başına bir kezdir ve gerçekten alarmdır.
```

## `meridian/adapters/finviz.py`

```text
adapters/finviz.py — Finviz'i OTONOM ADAY KAYNAĞI yapar (2026-07-23).

Rol: EVRENİ GENİŞLETMEK, karar vermek DEĞİL. Finviz "bugün momentum/kırılım ekranında olanlar"ı
döndürür; bu ticker'ların barları FMP zincirinden çekilir ve Meridian'ın KENDİ vcp/pullback/momentum
yasası + kapısı yine karar verir. Finviz burada yalnız "hangi hisselere bakılsın" listesini büyütür.
Bu izolasyon bilinçlidir: Finviz kırılgandır (public scraping, 1 haftalık Elite trial), ama kırılganlığı
karar mantığına SIZAMAZ — yalnız evrenin genişliğini etkiler.

DÜRÜST BOZUNMA (bu kod tabanının ana yasası): `discover()` HER ZAMAN bir kaynak etiketiyle döner.
Elite token varsa CSV export (ToS-uygun, stdlib parse); yoksa/süresi dolmuşsa public HTML (httpx +
regex, bs4 yok); o da olmazsa BOŞ + `reason`. Boş dönüş asla sessiz değildir — evren REPLAY_UNIVERSE'e
düşer, olay kaydedilir, sağlık ve seam görünür olur. "Aday bulunamadı" ile "Finviz'e ulaşılamadı"
ASLA aynı görünmez.

GİZLİLİK: token yalnız `auth` sorgu parametresinde gider; httpx'in hata metni TAM URL'i taşıdığından
(fmp.py'nin öğrettiği ders) hata mesajları KAYNAĞINDA maskelenir — token asla loglanmaz, panoya
son-4 dışında hiç çıkmaz.
```

## `meridian/adapters/fmp.py`

```text
adapters/fmp.py — Financial Modeling Prep (STABLE API). Enriches live candidates (fundamentals,
quotes, constituents, earnings) when FMP_API_KEY is present. Without a key it reports unavailable and
the FMP-`req` skills stay disabled — no faked data (Hard Rule 7).

Stable API contract (per FMP docs):
  base    https://financialmodelingprep.com/stable
  auth    every request takes ?apikey=<KEY>   (passed as a query param, never in the path/logs)
  style   query params, e.g. /quote?symbol=AAPL , /profile?symbol=AAPL , /search-name?query=apple
```

## `meridian/adapters/insider.py`

```text
adapters/insider.py — Form 4 (içeriden işlem) verisi: FMP insider-trading uçları (ROADMAP §3.4 Y4).

ROL: EVRENE BİR ONAY/TILT KATMANI HAZIRLAMAK, karar vermek DEĞİL. Bu adaptör yalnız ölçer ve yazar;
`insider_signals.json` bugün HİÇBİR üretim tüketicisine bağlı değildir (aşağıda "YASA 6" notu).

--------------------------------------------------------------------------------------------------
UÇLAR ve MALİYET (FMP stable; anahtar `?apikey=` sorgu parametresinde — adapters/fmp.py zinciriyle
AYNI: rotasyon, kota bloğu, maskeleme, günlük muhasebe hepsi ORADAN gelir, burada TEKRAR EDİLMEZ)

  1. `insider-trading/latest?page=P&limit=L`   — PİYASA GENELİ en yeni Form 4 dosyalamaları.
     Maliyet EVREN BOYUNDAN BAĞIMSIZ: 250 sembol için 250 istek DEĞİL, "yeni dosyalama akışı"nda
     kaç sayfa varsa o kadar istek. Bu, `data.nasdaq_earnings_window`ın kazanç takviminde kullandığı
     ile AYNI kaçış: sembol-başına sorgu FMP'nin ~250/gün ücretsiz kotasının TAMAMINI yakar.
  2. `insider-trading/search?symbol=X&page=P&limit=L` — SEMBOL BAŞINA geçmiş. Yalnız `--gecmis`
     yolundan, TAVANLI çağrılır (sınıflamanın 3 yıllık penceresini derinleştirmek için).
     >>> CANLI ÖLÇÜM (2026-07-29): bu uç MEVCUT ÜCRETSİZ PLANDA **HTTP 402 Payment Required**
     döner (üç sembolde de aynı yanıt; `/latest` aynı anahtarla 200 veriyordu, yani kota değil
     PLAN sınırı). SONUCU AÇIKÇA SÖYLEMEK GEREKİR: 3 yıllık sınıflama penceresi bugün ancak
     `/latest` akışının GÜNLÜK BİRİKTİRİLMESİYLE dolar — yani sınıflama, defter o derinliğe
     ulaşana kadar `siniflanamadi` döndürmeye DEVAM EDER ve bu bir kusur değil, ölçülmüş bir
     kapsam gerçeğidir. Alternatif: FMP planını yükseltmek. `--gecmis` yolu kaldırılmadı çünkü
     402 dürüstçe raporlanıyor ve plan yükselince ÇALIŞIR hâlde.

  ARTIMLI DELTA — "TEK TOPLU TARAMA" DEĞİL. `--fetch` her koşuda akışı BAŞTAN taramaz: defterdeki
  su işareti (`watermark.en_yeni_filing` + görülen satır anahtarları) aşıldığı anda sayfalama DURUR.
    * SOĞUK ilk koşu 30 günü doldurmak için ~150 sayfa isteyebilir → `--sayfa-tavani` (varsayılan 40)
      onu böler; operatör birkaç güne yayar. Yarım kalması DÜRÜSTTÜR: rapor `tavana_carpti=True` der.
    * SICAK günlük koşu yalnız yeni dosyalamaları görür → tipik olarak 3-8 istek/gün.
  Her koşu GERÇEK çağrı sayısını döndürür ve deftere yazar (`cagri.son_tur`): kota etkisi tahmin
  değil ÖLÇÜM olsun.

--------------------------------------------------------------------------------------------------
RUTİN vs FIRSATÇI (Cohen–Malloy–Pomorski 2012 BASİTLEŞTİRMESİ)

  Gerekçe: Form 4 akışının büyük kısmı TAKVİMSEL gürültüdür — aynı yönetici her yıl aynı ayda
  (vesting/10b5-1 planı/yıllık ödül penceresi) işlem yapar ve bu işlemler GELECEK GETİRİ HAKKINDA
  bilgi taşımaz. CMP'nin bulgusu: bu "rutin" işlemler ayıklandığında GERİYE KALAN "fırsatçı"
  işlemler anlamlı öngörü taşır. Yani sinyal, işlemin VARLIĞINDA değil, TAKVİM DIŞILIĞINDA.

  BURADAKİ BASİTLEŞTİRME (özgün makale 3 ardışık yıl + ayrı bir sınıflandırma penceresi kullanır):
    RUTİN     : aynı KİŞİ + aynı SEMBOL, işlemin takvim ayında ÖNCEKİ 3 YILIN HER BİRİNDE de
                işlem yapmış.
    FIRSATÇI  : geçmiş penceresi KAPSANIYOR ama yukarıdaki koşul sağlanmıyor.
    SINIFLANAMADI : defterin o sembol için gördüğü en eski işlem, gereken 3 yıllık pencerenin
                başlangıcından SONRA ise. Yani "o yıllarda işlem yok" değil, "O YILLARA BAKAMIYORUZ".

  BU AYRIM BU DOSYANIN EN ÖNEMLİ SATIRI (UYDURMA YASAĞI). Veri yokluğunu "rutin değil → fırsatçı"
  diye okumak, taze bir defterdeki HER işlemi fırsatçı ilan ederdi: sinyal %100 dolu görünür, hiçbir
  testi kırmaz ve tamamen uydurmadır. Kapsam yoksa cevap SINIFLANAMADI'dır; özet dosyası bu sayıyı
  AYRI alanda gösterir ki defter sığken bunun görülmemesi imkânsız olsun.

  YÖN de aynı disiplinle okunur: Form 4'te "iktisap" (acquisition) ile "AÇIK PİYASA ALIMI" AYNI ŞEY
  DEĞİLDİR. Dosyalamaların çoğu ödül (A-Award), opsiyon icrası (M-Exempt), vergi stopajı (F-InKind)
  ya da bağıştır (G-Gift) — bunların hiçbiri "yönetici cebinden para verip hisse aldı" demek değil.
  Sinyal YALNIZ işlem kodu P (P-Purchase) ve S (P-Sale/S-Sale) satırlarından üretilir; gerisi
  `diger`, tanınmayan kod `bilinmiyor` olarak AYRI sayılır ve nete GİRMEZ.

--------------------------------------------------------------------------------------------------
YAZAR TEKLİĞİ (paralel-yazar güvenliği)

  Bu modül state'e İKİ dosya yazar ve İKİSİNİN DE TEK YAZARI bu dosyanın CLI'ıdır:
      state/insider_trades.json    ham defter (artımlı; su işareti burada)
      state/insider_signals.json   sembol-başına özet skor
  Canlı worker (meridian.run / loop.daily_cycle) bu dosyalara DOKUNMAZ — ne okur ne yazar. Yazım
  `store.write_json` ile ATOMİKtir (mkstemp + os.replace), yani bir okur yarım dosya göremez.
  `store.file_lock` 2026-07-31'den beri SÜREÇLER ARASIdır (fcntl.flock); burada zaten yeterliydi
  (tek yazar tek süreçtir, CLI) — sertleşme bedavaya geldi. Bu iki
  dosya YENİ olduğu için, canlı worker koşarken bu CLI'ı çalıştırmak güvenlidir — çakışacak bir
  yazar yok. (fmp_usage.json muhasebesi ORTAKtır; oraya yazan zaten adapters/fmp.py'dir ve atomiktir.)

YASA 6 (tüketici zorunluluğu) — BEYANLI ERTELEME: bu turda ölçülen tek tüketici CLI + testlerdir.
  loop/api/counterfactual bağlantısı BİLİNÇLİ olarak SONRAKİ tura ertelendi; sebebi, sınıflamanın
  anlamlı olabilmesi için defterin önce 3 yıllık kapsama ULAŞMASI gerekmesi. Bugün bağlanan bir
  tüketici, `siniflanamadi` ile dolu bir dosyayı sinyal sanardı. Kapsam metriği (`kapsam` bloğu)
  tam da o bağlantının ne zaman yapılabileceğini söylemek için yazılır.

CANLI DOĞRULAMA DURUMU (2026-07-29): FMP'nin insider uçlarının ALAN ADLARI bu turda CANLI
  doğrulanamadı — her iki FMP anahtarı da o gün kota-bloklu (HTTP 429 "Limit Reach") idi. Alan
  eşlemesi FMP stable sözleşmesine göre yazıldı ve TAKMA-AD haritası ile toleranslı okunur; ama
  tolerans sessiz olmaz: eşlenemeyen ham alan adları `alan_teshis.eslesmeyen_alanlar` altında
  deftere YAZILIR ve ilk canlı koşuda gözle görülür. Sağlayıcı şeması kaydıysa sonuç sıfır dolu bir
  sinyal değil, adıyla görünen bir teşhis olur.
```

## `meridian/adapters/macro.py`

```text
adapters/macro.py — EMEKLİ MODÜL (ÇIKARILDI 2026-07-30, temizlik turu).

NE VARDI: `snapshot()` (SPY serisinden türetilmiş makro/rejim anlık görüntüsü) ve `status()`
(sağlayıcı künyesi). İkisi de 2026-07-21 tur-5 denetiminde "ÜRETİM TÜKETİCİSİ YOK — skill yüzeyi
iskelesi" diye YAZILI olarak işaretlenmişti; bu tur o teşhisi kapattı.

ÇAĞIRAN TARAMASI (2026-07-30, meridian/ + tests/ + ops/ + deploy/ + skills/): `meridian` paketinde
bu modülü içe aktaran TEK bir satır yok (`from . import macro` / `import macro` → 0 eşleşme).
Tek tüketici `tests/test_macro_news_audit_v20.py` ve `tests/test_gaps_final_v52.py`'nin
determinizm satırıydı — ikisi de bu turda güncellendi. `skills/` altındaki `macro.get(...)`
eşleşmeleri BAŞKA betiklerin kendi yerel sözlükleridir, bu modül değil.

NEDEN SARMALAYICI DEĞİL DE ÖLÜ: canlı rejim sınıflaması `regime.classify` ile DOĞRUDAN döngüde
yapılıyor (loop.py) ve `snapshot()` yalnız aynı fonksiyonu SPY barlarıyla bir kez daha çağırıp
sözlüğe sarıyordu. İkinci bir "rejim gerçeği" üreten, hiç okunmayan bir yol.

GERİ-AL: modül gövdesi tekti — `WINDOW_START = "2023-01-01"` sabiti, `snapshot(index_bars=None)`
(bars yoksa `data.load_bars(data.INDEX_SYMBOL, WINDOW_START, dataset.fetch_end())` ile yükler,
sonra `regime.classify` + `regime.distribution_days` + `regime.follow_through` sonuçlarını
`{"available": True, "source": "index-derived (SPY)", ...}` sözlüğünde döndürürdü) ve
`status()` (sabit künye sözlüğü). Dosya SİLİNMEDİ ki geri-al notu adresinde dursun; içe
aktarılması hâlâ hatasızdır ve hiçbir ad sunmaz.
```

## `meridian/adapters/massive.py`

```text
adapters/massive.py — Massive (massive.com) EOD bar sağlayıcısı.

NEDEN VAR: bugün 250 sembollük BİR bar tazelemesi, SEMBOL BAŞINA bir FMP isteği atıyor ve ücretsiz
katmanın günlük kotasının TAMAMINI yakıyor (canlı kanıt: state/fmp_usage.json, 2026-07-27'de
`calls_today: 251` ile "Limit Reach"). Massive'in **grouped daily** ucu TÜM ABD piyasasının o güne ait
EOD barlarını TEK çağrıda döndürür — yani artımlı günlük tazeleme N istekten 1 isteğe iner.

ROL AYRIMI (Rol 1 kararı):
  * Massive → GÜNLÜK ARTIMLI tazeleme (önbellekte zaten geçmişi olan sembollerin SON barı) +
    çapraz doğrulama. Ücretsiz katman: 5 çağrı/dk, ~2 yıl geçmiş, EOD.
  * FMP     → DERİN geçmiş backfill (2021+; walk-forward bunu ister) ve Massive düşerse yedek.
  * Alpaca  → dakikalık; bu modül ona hiç dokunmaz.

UÇLAR — DOKÜMANDAN DOĞRULANDI (2026-07-29, massive.com/docs endpoint sayfaları):
  grouped daily   GET {BASE}/v2/aggs/grouped/locale/us/market/stocks/{YYYY-MM-DD}
                      ?adjusted=true&include_otc=false
  custom bars     GET {BASE}/v2/aggs/ticker/{ticker}/range/{mult}/{timespan}/{from}/{to}
  all tickers     GET {BASE}/v3/reference/tickers
NOT: massive.com/llms.txt bu uçları `/rest/stocks/aggregates/daily-market-summary` gibi adlarla
listeler — bunlar DOKÜMAN SAYFASI yollarıdır, istek yolları değil. İstek yolları yukarıdaki gibidir
(her uç sayfasındaki literal "GET https://api.massive.com/..." satırından alındı).

ALAN EŞLEMESİ (results[] → bizim CSV şeması date,open,high,low,close,volume):
    T  → (ticker; satırın kimliği, sütun değil)      o → open      h → high
    l  → low            c → close        v → volume   t → date (unix ms, ET seansına çevrilir)
    vw → **ATILIR** (CSV şemasında vwap sütunu YOK — state/bars/*.csv başlığı doğrulandı)
    n  → **ATILIR** (işlem sayısı; şemada yok)     otc → ATILIR (include_otc=false zaten)

ANAHTAR YOKSA: her uç None döner (BOŞ LİSTE DEĞİL — "istek atılamadı" ile "sağlayıcı sıfır satır
döndürdü" ayrı şeylerdir; data.py'deki HATA≠BOŞ disiplininin aynısı) ve yokluk BİR KEZ obs'a kaydedilir
(YASA 4: yokluk kaydedilir, sessiz değil). Zincir FMP ile aynen sürer.

YAZIM ZİNCİRİNE GİRİŞ ÖLÇÜME BAĞLIDIR — ve ölçüm YAPILDI (ayrıntı: BASELINE):
  * Rol 1, iki ayrı tarihte (25 ve 12 sembol; arada temettü ex-tarihi geçen KO/PEP/O/VZ/MO dahil):
    maksimum sapma %0.000.
  * Rol 2 (bu ajan) BAĞIMSIZ tekrar, TÜM önbellek evreni (251 sembol, 2026-07-28): maksimum sapma
    **%0.081**, %0.1 toleransını aşan 0/251. Yani "sıfır sapma" DOĞRU DEĞİL — küçük örneklemin
    yuvarlamasıydı; gerçek iyi huylu gürültü tabanı ~%0.08. Sapmalar DAĞINIK, çarpımsal değil:
    bölünme 2x/4x, temettü %1–15 SABİT kayma üretirdi, bu ise venue/consolidated close farkı.
  * Hacim ekseni de ölçüldü (brief istemiyordu, ama bar yazan kaynak hacmi de yazar): 239/251
    birebir aynı, medyan oran 1.000 → sistematik hacim kırılması YOK.
Hüküm: iki kaynak AYNI ayarlama politikasında (yalnız bölünme-düzeltmeli) → kapı AÇIK. Yerel
`--dogrula` koşulursa hüküm ONUN olur ve "uyumsuz" derse kapı kapanır; taban yerel kanıtı ezemez.

Anahtar YOKSA hiçbir şey değişmez: uçlar None döner, zincir FMP→Cboe→Nasdaq olarak aynen sürer.
Bugün worker'da anahtar yoktur (Claude eklentisinin anahtarı worker'a AKMAZ) — yani bu modül
panoya `MASSIVE_API_KEY` girilene kadar çalışma zamanında HİÇBİR davranışı değiştirmez.
```

## `meridian/adapters/news.py`

```text
adapters/news.py — EMEKLİ MODÜL (ÇIKARILDI 2026-07-30, temizlik turu).

NE VARDI: `stock_news(symbols, limit)` (FMP `/news/stock` akışı), `status()` (dürüst sağlayıcı
durumu), `available()` ve `MAX_SYMBOLS`. `status()`ün kendi docstring'i 2026-07-21'de zaten
"bu modülün de üretim tüketicisi yok — skill yüzeyi" diyordu.

ÇAĞIRAN TARAMASI (2026-07-30, meridian/ + tests/ + ops/ + deploy/): `meridian` paketinde bu
modülü içe aktaran TEK bir satır yok. Tüketiciler yalnız `tests/test_macro_news_audit_v20.py` ve
`tests/test_review_backlog_v98.py`'nin sessiz-yutma satırlarıydı — ikisi de bu turda güncellendi.
`skills/canslim-screener/references/fmp_api_endpoints.md`'deki `stock_news` geçişi bir FMP
DOKÜMANTASYON satırıdır, bu fonksiyonun çağrısı değil.

NEDEN ÜÇÜ BİRDEN: `stock_news` gidince `available()` ve `MAX_SYMBOLS` de çağıransız kalırdı —
"ölü mekanizma sıfır" hedefi (§ hedef sözleşmesi md.1) yarım bir emeklilikle sağlanmaz. Haber
skilleri geri istenirse zincir FMP anahtarı üzerinden yeniden kurulur; kırpma/uyarı dersleri
aşağıda yazılı kalıyor ki aynı tuzaklar ikinci kez kurulmasın.

GERİ-AL (ve o zaman KORUNMASI gereken üç ders):
  * `stock_news`: `fmp._get("news/stock", {"symbols": ",".join(symbols[:20]), "limit": limit})`;
    anahtar TEK yerde (adapters/fmp.py) kalır, burada TEKRAR EDİLMEZ.
  * SESSİZ KIRPMA YASAĞI: uç nokta pratikte 20 sembol alıyor. 250 sembol isteyen çağıran 20
    tanesini alıp "haber yok" sanıyordu → kırpma `obs.warn("news_symbols_truncated", asked=…,
    sent=…)` ile KAYDA GEÇMELİ.
  * "HABER YOK" ≠ "HABER ALINAMADI": ağ/sağlayıcı hatasında `[]` dönmek DOĞRU davranıştır (çağıran
    boş akışla yaşayabilir) ama sessiz olması değil → `obs.warn("news_fetch_failed", …)`.
    `status()` de "anahtar var mı" değil "kaynak üretiyor mu" (`fmp.health()["ok"]`) demeliydi.
```

## `meridian/adapters/shortinterest.py`

```text
adapters/shortinterest.py — FINRA Equity Short Interest (ROADMAP §3.4 Y4, "kaçınma filtresi" ayağı).

ROL: ölçmek ve yazmak. Bu adaptör bugün HİÇBİR üretim kararına bağlı değildir (aşağıda "YASA 6").

--------------------------------------------------------------------------------------------------
UÇ ve MALİYET — ANAHTARSIZ, ÜCRETSİZ, KOTASIZ (FMP'den TAMAMEN AYRI)

  POST https://api.finra.org/data/group/otcMarket/name/consolidatedShortInterest
       Accept: application/json
       gövde: {"limit":N,
               "compareFilters":[{"fieldName":"settlementDate","fieldValue":"YYYY-MM-DD",
                                  "compareType":"GTE"}],
               "domainFilters":[{"fieldName":"symbolCode","values":[...]}]}

  CANLI DOĞRULANDI (2026-07-29): uç anahtarsız 200 döner; `domainFilters` sembol listesiyle
  filtreler; `compareFilters` GTE ile tarih penceresi daraltılır. ALAN ADLARI canlı yanıttan
  ALINDI (tahmin DEĞİL): symbolCode, issueName, marketClassCode, settlementDate,
  currentShortPositionQuantity, previousShortPositionQuantity, averageDailyVolumeQuantity,
  daysToCoverQuantity, changePercent, changePreviousNumber, stockSplitFlag, revisionFlag,
  accountingYearMonthNumber, issuerServicesGroupExchangeCode.
  NOT: `sortFields` bu uçta REDDEDİLİR ("Sorting is allowed only if all partition keys are specified
  in EQUAL CompareFilter") — bu yüzden "son yayın" sunucuda sıralanarak değil, pencere çekilip
  YEREL max(settlementDate) ile bulunur. Bir varsayım değil, sağlayıcının söylediği sınır.

  MALİYET: evren `parca` (varsayılan 125) sembolluk dilimlere bölünür → 250 sembol için 2 istek.
  Ücretsiz ve kotasız olduğundan FMP bütçesine SIFIR etkisi vardır. FMP'ye TEK dokunuş, isteğe bağlı
  `--float-cek` yoludur (aşağıda) ve varsayılan olarak KAPALIDIR.

--------------------------------------------------------------------------------------------------
BAYATLIK GÖRÜNÜR OLMALI

  FINRA kısa pozisyonu ayda İKİ KEZ yayımlar (ayın 15'i ve son iş günü mutabakat tarihleri) ve
  yayın mutabakat tarihinden ~9 İŞ GÜNÜ SONRA gelir. Yani bu veri EN İYİ İHTİMALLE ~9 iş günü,
  en kötü ihtimalle ~3 hafta eskidir. Bir "kaçınma filtresi" 3 haftalık veriyle bugünü filtrelemeye
  kalkarsa, filtrelediğini sandığı riski çoktan kaçırmış olabilir.

  Bu yüzden bayatlık dosyanın İÇİNDEDİR ve türetilmesi okura bırakılmaz: `yayin` bloğu mutabakat
  tarihini, takvim/iş günü gecikmesini ve `bayat_mi` bayrağını taşır. Okuyan taraf tarihi kendi
  hesaplamak zorunda kalırsa er ya da geç hesaplamaz.

--------------------------------------------------------------------------------------------------
TÜRETİLEN ALANLAR ve NEDEN İKİ AYRI "gün kapatma"

  gun_kapatma_meridian = kısa pozisyon / ADV20(bar önbelleği)   ← BİZİM ölçümümüz
  gun_kapatma_finra    = FINRA'nın `daysToCoverQuantity` alanı  ← SAĞLAYICININ ölçümü

  İkisi AYNI ŞEY DEĞİLDİR: FINRA kendi `averageDailyVolumeQuantity` tanımını kullanır (mutabakat
  dönemine ait), biz bar önbelleğindeki SON 20 SEANSIN ortalamasını kullanırız. Birini diğerinin
  yerine yazmak, iki farklı ölçümü tek isim altında birleştirip farkı görünmez kılardı. İkisi de
  yazılır; ayrıştıkları yerde soru sorulabilsin.

  ADV20 bar önbelleğinden OKUNUR (adapters/data.py `_cache_path` deseni) — AĞ ÇAĞRISI YOK, yazım
  YOK. Önbellek yoksa alan None'dır ve `adv20_kaynak` sebebi söyler; 0 ya da tahmin YAZILMAZ.

  si_yuzde_float: float/sharesOutstanding gerektirir ve bu depoda BÖYLE BİR KAYNAK YOKTUR (arandı).
  FMP `profile` ucundan gelebilir ama SEMBOL BAŞINA 1 istektir: 250 sembol = günlük FMP kotasının
  TAMAMI. Bu yüzden varsayılan davranış "alan None"dır ve `--float-cek N` ile TAVANLI, KALICI
  ÖNBELLEKLİ (`short_interest_float.json`) olarak azar azar doldurulur. Bilinmeyen float için
  UYDURMA YOK: None kalır, `float_kaynak` null olur.

--------------------------------------------------------------------------------------------------
YAZAR TEKLİĞİ (paralel-yazar güvenliği)

  state/short_interest.json         özet — TEK YAZAR: bu dosyanın CLI'ı
  state/short_interest_float.json   float önbelleği — TEK YAZAR: bu dosyanın CLI'ı
  Canlı worker (meridian.run / loop) bu dosyalara DOKUNMAZ. `store.write_json` atomiktir
  (mkstemp + os.replace + fsync), yani okur yarım dosya göremez; `store.file_lock` 2026-07-31'den
  beri süreçler arasıdır (fcntl.flock) ve tek
  yazar zaten tek süreç olduğu için yeterlidir. Dosyalar YENİ olduğundan canlı worker koşarken bu
  CLI'ı çalıştırmak güvenlidir.

YASA 6 (tüketici zorunluluğu) — BEYANLI ERTELEME: bu turda ölçülen tek tüketici CLI + testlerdir.
  loop/api/counterfactual bağlantısı bilinçli olarak SONRAKİ tura ertelendi. Sebep: "filtreli vs
  filtresiz" karşılaştırması karşı-olgusal defterde ölçülmeden bir kaçınma filtresi kapıya
  bağlanırsa, hiç ölçülmemiş bir kısıt canlı stratejiyi daraltmış olur.
```

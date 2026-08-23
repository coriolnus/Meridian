# TASARIM — Dakika-hassas icra ölçümü / intraday dolum sözleşmesi ailesi (WP1-B "13", 2026-08-23)

**Ne bu belge:** Dakika-barı dolum yasasının ve ona giden aşamalı ölçüm yolunun TASARIMI. Kod,
kart ve hüküm İÇERMEZ — kart-adayı parametreler ÖNERİDİR, kart yazımı Rol-1'in. Her iddia
dosya:satır çapalı; ölçülemeyenler §5'te None+neden ile beyanlı.

**Girdiler:** `docs/TASARIM-23E-23F-13-2026-08-22.md` (arşiv envanteri) · bugün canlıya inen
pencere-1345 uygulaması (EXE-2026-009 + K2) · EDG-2026-047 (measured, pencere kanıtı) ·
EDG-2026-045 (measured, stop-slip + karma-yuvarlama) · kod: `barclock.py`, `intraday_cycle.py`,
`loop.py`, `broker.py`, `backtest.py`, `barsarchive.py`, `bararchive.py`, `intraday_shadow.py`.

---

## 1 · MEVCUT DURUM

### 1.1 Intraday verinin bugünkü tüketicileri

| katman | modül / yol | ne yapar | çapa |
|---|---|---|---|
| yazar (dakika satırı) | `barsarchive.BarsArchiver` → `state/bars_intraday/*.jsonl` | Redis `mrd:bars:*` → fsync→XACK, (ticker,t) tekilleştirme; şema hotstate'ten türer (`o,h,l,c,v,vw,n,t`) | `barsarchive.py:1-30`, `:78` |
| yazar (çerçeve) | `bararchive.archive_frame` → `state/intraday_bars/*.jsonl` | hotstate içi tek-deneme çerçeve arşivi; 120 takvim-günü retention | `bararchive.py:37-38`, `:65-84` |
| sıcak yol (arşivi OKUMAZ) | `intraday_cycle` → `hotstate.read_bars` (lookback 390, stale 120 s) | tetik-geçiş gözlemi + 4b gölge; **bugünden itibaren** sabah kancası `_pencere_gonderim` | `intraday_cycle.py:42-43`, `:240`, `:201-231` |
| sıcak yol (gölge dolum yasası) | `intraday_shadow` | dakika-çözünürlükte TEK mevcut dolum sözleşmesi: `sim_price = max(bar_open, entry_trigger)` | `intraday_shadow.py:279`, `:370` |
| arşiv tüketicisi (koşan kod) | **YOK** — beyanlı `gelecek_tuketici`; devir şartı: okuyan ölçüm geldiği gün satır kalkar, gerçek tüketici yazılır | `codelaw.py:590-607` |
| arşiv tüketicisi (araştırma) | EDG-2026-047 ölçümü — canlıdan ssh-stdin salt-okuma çekim (repo `state/`ini okumadı; yerel kopya bayattı) | `research/olcumler/edg047_yakin_pencere_2026-08-23/CEKIM_ENVANTERI.json` |
| tanılama | `barsarchive` CLI `summary`/`gap_scan` | `barsarchive.py:726-755` |

Arşiv kapsamı (047 çekimi, damga 2026-08-22T23:42:38Z): **20 seans** (2026-07-27→08-21),
**1.358.129 satır**, 252 tekil ticker, açılış-verili seans **19/20** (2026-07-28 arşivi 13:55'te
başlamış), ticker-başına medyan ~294/390 dakika (~%75 kapsam; boş dakika = işlemsiz dakika)
(`edg047_.../sonuc.json`, `TASARIM-23E-...md §1.3`).

### 1.2 Replay'in dakika-körlüğünün TAM sınırı — 1Day'den gelen varsayımlar

Veri tabanı ve tek çekim yolu 1Day'dir: `state/bars/*.csv` günlük şema; API yolu
`adapters/alpaca.py:1476,1492` (`timeframe=1Day`); haftalık onay bile günlükten yeniden-örnekleme
(`indicators.py:290-293`). Bu tabandan üç varsayım ailesi doğar:

**(a) Dolum modeli (giriş).** Emir "ertesi seans açılışı"nda dolar:
`backtest.py:332` → `broker.fill_entry(..., per[t].loc[d,"open"], ...)`;
`base_fill = next_open * (1+slip)` (`broker.py:614`) + katılım-etkisi. Limit tavanı: açılış
limitin üstündeyse ret (`EV_MISSED_LIMIT`), TEK istisna 23c `bar_low` parametresi — günlük low
limite dokunduysa limitten dolum (`broker.py:594`, varsayılan kapalı: `backtest.py:61,333`).
Körlük: günlük low dokunuşun **NE ZAMAN** olduğunu söylemez (stoptan önce mi, kapanışa saniye
kala mı) — 23c bu yüzden A/B bayraklı ve bit-özdeşlik kill'li.

**(b) Stop tetiği (çıkış).** `_touch_exit` iki kademe (`broker.py:667-702`): kademe-1 açılış
(sıra kesin, gerçek fiyat); kademe-2 bar-içi — high/low sırası OHLC'den bilinemez → **stop-önce
muhafazakârlık**, dolum TAM `eff_stop`ta (`broker.py:691-699`) = sıfır stop-slip varsayımı.
EDG-2026-045 hükmü: bu varsayım P&L'i ANLAMLI şişiriyor (10 bps hücresi ΔP&L −5.697
CI[−7.604,−4.004]; üç hücrede de CI<0) — şerh EDG-040 bandına ve replay hükümlerine düşülü
(`EDG-2026-045-stop-slip.yaml verdict`). Aynı-gün hem stop hem hedef dokunan bar bugün TAM stop
zararı yazılır — belirsizlik penceresi 390 dakikadır.

**(c) Pencere.** Replayde gönderim ANI kavramı yok: `gap_at_submit=None` beyanı "bu motorda
gönderim anı YOK" (`broker.py:520`, `:544`); dolum daima açılıştır. Canlı ise BUGÜNDEN itibaren
1345 rejiminde: tetik sabiti `ENTRY_WINDOW_ET_MIN = 9*60+45` (`barclock.py:144`), pencere yasası
tek kapının içinde (`loop.py:698-707`), pencere-öncesi olaylar karar üretmez
(`intraday_cycle.py:172-176`), ertelenen gönderimi sabah kancası aynı tek kapıdan atar
(`intraday_cycle.py:184-190`, `:201-231`), tek muafiyet İŞ-2-EOD mutabakat kemeri
(`loop.py:1552-1558`, `pencere_muaf=True`). **Sonuç: 2026-08-23 itibarıyla YENİ ve yapısal bir
canlı↔replay boşluğu doğdu** — replay 1330-açılış dolumunu modellerken canlı ≥13:45'te icra
ediyor. Boşluğun beyanlı hakemi EDG-042 K1'in pencere alt-bant kıyası (`EXE-2026-009 hakem_kurali`;
E2 `pencere` damgası `loop.py:1470`, kaynak `barclock.pencere_rejimi`, `barclock.py:150-153`).

**(d) Diğer günlük türevler.** MFE/MAE su işaretleri günlük high/low'dan (`broker.py:687-690`);
`bars_held` gün sayar; scale-out günlük barla çağrılır (`backtest.py:363`) ve aynı-bar trail
kusuru günlük çözünürlüğün ürünüdür (ROADMAP 13 / `TASARIM-23E-...md §3.3-2`).

---

## 2 · DOLUM SÖZLEŞMESİ TASARIMI — dakika-barı dolum yasası

**P1 — Veri parametresi, mod bayrağı DEĞİL.** 23c emsali aynen (`broker.py:585-591` gerekçesi):
dakika yasası `fill_entry`/`_touch_exit`e opsiyonel dakika-bar dizisi olarak girer; dizi
verilmeyen çağrı bugünkü günlük yasayla **bit-özdeş** koşar (A-kolu kill, edg032c tabanı).
Canlı yol bu parametreyi yapısal olarak geçemez (karar anında gelecek dakikalar bilinmez) —
canlı davranış değişmezliği disiplin sözü değil olgu kalır.

**P2 — Zaman-sıralı tarama; dakika-içi muhafazakârlık aynen.** Günün belirsizliği 390 dakikadan
1 dakikaya iner; bir dakikanın İÇİNDE sıra yine bilinemez → iki-kademe yasası dakikaya taşınır:
dakika açılışı kesin sıra, dakika-içi stop-önce. `intraday_shadow`un mevcut sözleşmesi
(`max(bar_open, entry_trigger)`, `intraday_shadow.py:279`) bu ailenin giriş-tarafı özel halidir;
iki yasa AYRIŞMAMALI — tek gövde hedeflenir.

**P3 — Üç emir tipinin dakika-çözünürlükte yeniden ifadesi:**
- *Marketable-limit giriş (E1):* gönderim dakikası t0 = ET-dakikası ≥ `ENTRY_WINDOW_ET_MIN` olan
  ilk bar (sabit barclock'tan okunur — ikiz-değer `EQUIVALENT_TRUTHS` tuzağı, `barclock.py:139-142`).
  t0 barında `o ≤ limit` → dolum `o`dan (slip/etki bileşenleri mevcut yasadan devralınır,
  `broker.py:614+`); değilse emir DİNLER: t>t0 için `l ≤ limit` olan İLK dakikada limitten dolum
  (23c'nin zaman-sıralı hali — "dokunuş ne zaman" körlüğü kapanır); hiç dokunmazsa `missed_limit`.
- *Stop çıkışı:* pozisyon-sonrası ilk `o ≤ eff_stop` dakikası → `stop_gap`, dolum `o` (gerçek
  fiyat, kademe-1 dürüstlüğü korunur); yoksa ilk `l ≤ eff_stop` dakikası → dolum `eff_stop`.
  Dakika yasası stop-slip sorusunu ÇÖZMEZ (dakika barı işlem-düzeyi kaymayı vermez) — 045'in
  ek-slip kanalı sözleşmede AYRI parametre olarak yaşamaya devam eder; gerçek bant 042-K3'ten.
- *Hedef:* simetrik; aynı-GÜN farklı-DAKİKA stop+hedef çakışmaları artık gerçek sırasıyla çözülür —
  günlük stop-önce muhafazakârlığının maliyeti böylece ölçülebilir bir sınıf olur (§3-A2).

**P4 — Yuvarlama beyanı (045 dersi).** Motorda KARMA yuvarlama ölçüldü: bar-fiyat yollarında
`np.float64.__round__`, plan-alanı yollarında Python `round` (`EDG-2026-045-...yaml verdict`).
Dakika yasası, dakika-bar fiyatlarının bar-fiyat yolunu izlediğini AÇIK yazar ve öz-sınaması
(1e-9) bu modeli kullanır — alet gevşetilmez, tamamlanır (040-kill#2 emsal zinciri).

**P5 — Pencere/damga tutarlılığı.** Dakika yasasının t0'ı ile canlının tetiği AYNI sabitten
türediği için replay dakika-modu, bugün doğan 1330/1345 boşluğunun beyanlı kapatıcısıdır; E2
`pencere` damgası (kart sözleşmesi: rejimi söyler, gerçekleşen pencereyi değil — `loop.py:1465-1470`)
kıyas anahtarı olarak kalır. DST: sabit ET-dakikadır, "13:45 UTC" EDT ifadesidir (`barclock.py:142-144`).

**P6 — Eksik-dakika yasası.** Bar yokluğu = fiyat keşfi yok = dolum olayı YOK (emir dinlemeye
devam eder); dolum ASLA enterpolasyonla yazılmaz (UYDURMA YASAĞI). Seans-içi kesinti
(`gap_scan`, `barsarchive.py:7-8`) seans-düzeyi geçerlilik kapısıdır: 2026-07-28 tipi
arşiv-başlangıç kesintili seans o ölçümde adıyla düşer. Bar aralığı sözleşmesi 047'den donuk:
`[başlangıç,60sn)` (`edg047_.../sonuc.json pencere_tanimi`).

**P7 — Determinizm.** Arşiv satırları geliş sırasıyla dosyalanır (ticker'lar arası serpiştirme);
okuyucu sözleşmesi: ticker başına `t`-sıralama + savunmacı (ticker,t) tekilleştirme (yazar zaten
tekilleştirir, `barsarchive.py:16-17`, `:149`; yarım-satır kalıntısı beyanlı, `:123`). Feed şerhi:
akış IEX (`marketstream.py:37`); IEX↔konsolide ölçüt hatası −36,8…+16,2 bps (ARASTIRMA §B.6,
`TASARIM-23E-...md §1.3`) ölçülen etkilerle aynı mertebe — her hüküm paydasına yazılır.

---

## 3 · AŞAMALI YOL (ölçüm ← altyapı; kart-adayı parametreler ÖNERİ, kart Rol-1'in)

**A1 — E2 ↔ dakika-bar dolum-doğrulaması.** *Altyapı: YOK — arşiv + E2 defteri yeter (047/exe007
salt-okuma çekim deseni).* Soru: arşiv, icra zemini olarak güvenilir mi? Her E2 ayna dolumu
(gerçek Alpaca fiyatı) kendi dolum dakikasının barıyla eşlenir: fiyat ∈ [l,h] mi, dakika-açılışa
bps farkı ne, `pencere` rejimine göre dağılım. EDG-042 K1 ile çift-sayım değil: 042 friksiyonu
ölçer, A1 arşivin o anı YAKALAYIP yakalamadığını. Kart-adayı: tek hücre (K+=1), Ö1 betimleyici
başlar — E2 bugün 30 satır/13 dolum (`TASARIM-23E-...md §2.3`); hükümlü eşiğe 042-K1 emsali
önerilir (n≥30 dolum ∧ ≥10 seans, `EDG-2026-042-...yaml:71`). Kill adayları: eşlenemeyen dolum
adıyla raporlanır (sessiz düşürme geçersiz kılar) · saat-dilimi yoğunluk-sıçrama kapısı 047'den
aynen · canlı state'e tek bayt yazım geçersiz.

**A2 — Stop-tetik dakika-testi.** *Altyapı: A1'in eşleme aleti.* Arşiv penceresine düşen replay
işlemlerinde kademe-2 stop dolumları (`fill=eff_stop`) dakika verisiyle yeniden çözülür:
ilk-dokunuş dakikası, P3 stop yasasıyla dolum farkı (R/bps dağılımı), aynı-gün stop+hedef
çakışmalarının gerçek sıralama sayımı. Kart-adayı: tek hücre (K+=1); kill adayları: kesişim
küçükse (047-L2 emsali n=23<30 → yalnız sayı beyanı) betimleyici damga · **okuma kuralı: bu ölçüm
tek başına EDG-040/045 hükümlerini revize edemez** (045'in Ö2/042-K3 okuma kuralı aynen devralınır).

**A3 — Replay dakika-modu.** *Altyapı: §2 sözleşmesinin motora girişi — motor değişikliği = kart +
yeniden ölçüm; tüm karneler yeniden koşar uyarısı geçerli (ARASTIRMA §C.2, `TASARIM-23E-...md §1.4`).*
Ön-şartlar: A1 arşiv-güvenilirlik sinyali + A2'nin fark büyüklüğü (fark küçükse A3'ün maliyeti
gerekçesizdir — bu da bir sonuçtur). Kart-adayı parametreler: taban(günlük yasa, edg032c) +
{dakika-1330, dakika-1345} (K+=2); kill adayları: A-kolu bit-özdeşlik (dakika verisi verilmeyen
koşum ≡ taban) · yuvarlama öz-sınaması 1e-9 (P4) · **hibrit dönem beyanı**: 2022-01-07→2026-07-26
günlük-yasa, 2026-07-27→ dakika-yasa — iki rejim TEK karnede birleştirilmez, ayrı raporlanır.

Sıra gerekçesi: §C.2'nin "önce ölçüm-altyapısı, sonra pencere grid'i" beyanı korunur; her aşama
bir sonrakinin aletini doğrular ve A3 pahalı adımı ancak A1+A2 sinyal verirse alınır.

---

## 4 · AÇIK SORULAR / RİSKLER (Rol-1 / operatör)

1. **Derinlik:** 20 seans, tek dönem (2026 yazı); replay defteri 2022'den — geçmişe dakika verisi
   depoda YOK; A3 hükümleri yalnız ileri pencerede geçerli (047 beyanlı-sınır 1 aynen).
2. **Retention asimetrisi:** `intraday_bars` 120 günde budanır (`bararchive.py:38,65-84`);
   `bars_intraday`de retention KODU YOK (tarama: prune/cutoff/KEEP eşleşmesi yok, 2026-08-23) —
   korpus derinliği için iyi, disk için tavansız (~186 MB/20 seans ≈ 9,3 MB/seans → ~2,3 GB/yıl;
   047 çekiminde gzip ~%85 küçülttü). Operatör kararı: kota/sıkıştırma/olduğu-gibi.
3. **Feed:** IEX korpusu mu, konsolide (Massive) mi — §B.6 hata bandı etkiyle aynı mertebe;
   konsolide yol dış kaynak + PIT + bütçe (23E Açık Soru 2 aynen devreder).
4. **Determinizm:** serpiştirilmiş yazım sırası, yarım-satır kalıntıları, seans-içi kesintiler
   (19/20 açılış-verili) → P6/P7 okuyucu sözleşmesi karta kill olarak girmeli mi?
5. **Örneklem:** E2 13 dolum — A1 uzunca betimleyici kalır; hükümlü eşik beyanı (042-K1 emsali mi,
   başka mı) Rol-1'in.
6. **Boşluğun ömrü:** bugün doğan 1330-replay/1345-canlı boşluğu A3'e kadar açık — replay
   karnelerine "pencere şerhi" düşülür mü, biçimi ne (042 hakemi zaten izliyor)? Rol-1 kararı.
7. **Devir şartı:** A1 arşivi okuduğu gün `codelaw.py:590-607` beyanı sökülüp gerçek tüketici
   yazılmalı — ölçüm briefine açık madde olarak girmeli.

## 5 · ÖLÇÜLEMEYENLER (None + neden)

- **Sinyal-koşullu sürüklenme:** None — koşulsuz örneklem koşullu soruyu cevaplamaz (ARASTIRMA
  §C.2 kill beyanı; 23E §1.2). A1+A2 tam bu altyapıyı kurar.
- **Gerçek stop-slip bandı:** None — EDG-042 K3 kovası bugün n=0 ölçülebilir
  (`EDG-2026-042-...yaml:115` ara-koşum); 045 şerhi bant gelene dek geçerli.
- **Dakika-yasası ↔ günlük-yasa karne farkının büyüklüğü:** None — A2/A3 koşulmadı; bu belgenin
  önerdiği ölçümün kendisi.
- **249 vs 251/252 ticker farkının kimliği:** None — hangi sembollerin arşiv dışı kaldığı bu
  turda sayılmadı (047 arşiv-geneli 252 tekil ölçtü; canlı evren 251 — kesişim/fark listesi
  çıkarılmadı).

---

*Yazan: tasarım ajanı, 2026-08-23. Tek çıktı bu dosyadır; kod/kart/state değişikliği yok, git yok.*

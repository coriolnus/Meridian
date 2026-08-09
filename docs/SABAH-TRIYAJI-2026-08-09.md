# SABAH TRİYAJI — 2026-08-09

**Yazan:** bağlam-sahibi triyaj ajanı (depoyu biliyor; devir tatbikatının aksine kör değil).
**Okuyucu (YASA 6):** Rol-1 (dalga önceliklendirmesi + operatör soruları) + bir sonraki mühendis.
**Ölçüm penceresi:** 2026-08-09 ~08:20–08:55 UTC, A1 canlı (`ubuntu@130.61.126.87`), salt-okunur.
**Girdi:** devir tatbikatı (`docs/DEVIR-TATBIKATI-2026-08-09.md`, 01:20–02:10 UTC) + gece WP-N
dalgası + 3 dağıtım (son `c8d7f94`). Bu belge o kalemleri **dağıtımlardan SONRA** yeniden ölçer.

**Sınır beyanı:** git komutu koşulmadı (stash/diff/status DAHİL — gece iki ajan git-stash koşup
hasar verdiği için); dağıtım yapılmadı; `serve.sh` koşulmadı; broker'a emir gönderilmedi/iptal
edilmedi (yalnız salt-okur `positions()`/`orders()` GET); tam suite koşulmadı; `meridian/` ve
`tests/` altında HİÇBİR dosyaya dokunulmadı; canlı state'e YAZILMADI. Ölçüm betikleri yerelde
yazılıp `ssh … python -` ile stdin'den beslendi. Bu, depoda yazılan **TEK** dosyadır.

---

## 0. DRILL'DEN BU YANA NE DEĞİŞTİ (dağıtımların denetimi)

Devir tatbikatı 01:20–02:10 UTC'de koştu; **02:34:03 UTC'de servis yeniden başladı** (gece
dağıtımı canlıda). En önemli değişim tatbikatın **Risk 1'i (çıplak pozisyonlar)**:

- **v220 CANLI ve DOĞRULANDI (artefakttan).** `alpaca.py` yerel↔canlı md5 **BİREBİR**
  (`549b78e6871f7920672977400e85fddf`). Süpürücü `cancel_open_entries` (alpaca.py:481–487) artık
  `coid_sinifi` ile **iki kemer** uyguluyor: AİLE kemeri (`P-KORUMA-` öneki, `KORUMA_COID_ONEK`
  alpaca.py:381/407) + YÖN kemeri (long-only motorda satış-yönlü emir giriş olamaz, alpaca.py:410).
  Koruma sınıfı emir `kept`e `sinif:koruma` gerekçesiyle düşer — **süpürülmez.** Tatbikatın kök
  bulgusu (koruma OCO'su "dolmamış giriş" sanılıp iptal ediliyor) **yapısal olarak kapandı.**
- **Şu an broker'da 4 açık koruma OCO'su var** (`P-KORUMA-20260809-0835-{NUE,EMR,BKNG,AMGN}`,
  submit 08:35:44Z, status accepted/held). Tatbikat "0 açık emir / 5 çıplak pozisyon" görmüştü;
  o hâl artık yok. Olay zinciri: `koruma_kur_istegi → koruma_oco_gonderildi(adet=25) → koruma_kur_ozet`.
- **AÇIK KALAN (bkz. §4):** fixli süpürücü GERÇEK bir EOD süpürmesinde HİÇ koşmadı (piyasa
  Cuma'dan beri kapalı). Mantık doğrulandı; davranış Pazartesi 13:30 UTC sonrası ilk kez sınanır.

Tatbikatın **Risk 2'si (teslim edilmemiş alarm)** ve **Risk 3'ü (systemd exit-143)** DEĞİŞMEDİ —
kanal hâlâ boş, `SuccessExitStatus=` hâlâ boş. Aşağıdaki 13 kalem bu triyajın kapsamı.

**HÜKÜM: 13 kalemin 13'ü GERÇEK (canlı/kod kanıtlı); 0'ı çürüdü. Kapsamdaki P1 = 0** —
tatbikatın tek gerçek sermaye-P1'i (çıplak pozisyon) v220 ile kapandı ve pozisyonlar şu an korumalı.
`Kalem 1` (systemd) **kanal-açılışında-P1**'dir (aşağıda).

---

## (i) ÖNCELİKLENDİRİLMİŞ TABLO

| # | Kalem | Gerçek mi? (kanıt) | Şiddet | Tür | Önerilen kapama | Zaten ölçülü? |
|---|---|---|---|---|---|---|
| 1 | systemd exit-143 her restart'ta OnFailure | **EVET** — `SuccessExitStatus=` boş (canlı); NRestarts=0 (elle restart) | **P2** (kanal-açılışında P1) | kod-güvenli (birim dosyası; bakım penceresi) | `SuccessExitStatus=143` **ya da** SIGTERM'i 0'la yakala; elle test-ateşle | drill Risk 3 ✓ + bu turda yeniden |
| 2 | sprint 2 gündür ölü, pano "%53 koşuyor" | **EVET** — pid 96924 ölü, progress 281/527, dosya yaşı 42,6 sa; `should_run.gecen_gun=1` ölü sprintin `started_at`ından | **P2** | kod-güvenli | `sprint_child_orphaned` olayı (ölü pid + terminal-olmayan faz) + tetik hesabından ölü `started_at`ı düş | drill Risk 4 ✓ + yeniden |
| 3 | hipotez 7 gün 0/51 + gölge n_live=1<30 | **EVET** — `hypotheses.jsonl` yaşı 166 sa; `terfi.n_live=1, promote_min_n=30`; `gece_tavani=0`; agent streak 17 | **P2** | karışık: LLM kota = operatör/dış · "learning_stalled" göstergesi = kod-güvenli | türev gösterge: 7 günde yeni hipotez + dolgu = 0 → `learning_stalled` (sev-2) | drill Risk 5 ✓ + yeniden |
| 4 | E2 iç-motor bacağı totolojik (~5,04 bps = slippage_bps) | **EVET** — iç bps 5,007–5,104 (ort 5,037); `broker.py:443` `next_open*(1+slip)`, `slippage_bps:5` | **P2** | kod-güvenli | iç `fill_vs_resmi_acilis_bps` → None+beyan; ayna yorumu n<20 iken basılmasın | drill Risk 6 ✓; **E1 grid (EXE-2026-001) KAPSAMIYOR** (o limit-bacağı + E3 bandı) |
| 5 | iç↔ayna %49 boyut + aynada ADV kapısı yok | **EVET** — iç 54/64/43/33 vs ayna 25/37/22/22 (canlı); `alpaca.py:534-536` ADV yok vs `broker.py:448-456` | operatör (melez) + **P3** kod-güvenli (SB-1 makbuz) | operatör-kararı + kod-güvenli | operatör: fark kapansın mı; kod: SB-1 boyut makbuzu payda-beyanlı | drill Risk 7 / ROADMAP WP-S ✓ |
| 6 | halka-açık karne 96 der, gerçek canlı 1 (−450$) | **EVET** — `/api/public/summary.closed_trades=96`, `live/seed` anahtarı YOK; `sermaye_resetleri.tohum=95/canli=0`; realized −450,38 | **P2** (dışa bakan yüzey) | kod-güvenli | özete `closed_trades_live`+`closed_trades_seed` + `score` payda-beyanı | drill Risk 8 ✓ + yeniden |
| 7 | lxml yok · FMP 402 · finviz kapalı | **EVET** — `universe_drift.status=unknown (ImportError lxml)`; `integrity.production.starved: fmp_source 402`; `finviz_unavailable` 3.682 olay | lxml **P2** · FMP/finviz operatör | karışık: lxml=kurulum+kod-güvenli · FMP=operatör | lxml'i canlıya ekle → `universe_drift=unknown` KENDİSİ alarm olsun | drill Risk 9 ✓ + yeniden |
| 8 | E2 defterinde kilitsiz oku-değiştir-yaz | **EVET** — `store.append_jsonl` dosya dalı kilitsiz (store.py:374); `loop.py:79-81`+`1863-1892` read→write dış kilitsiz; `loop.py:1892` "atomik" yorumu yanıltıcı | **P3** (E2 = 9 satır, gizli) | kod-güvenli | E2 iki oku-değiştir-yaz bloğunu `file_lock(ENTRY_LEDGER)`e al; yanıltıcı yorumu düzelt | drill Risk 10 ✓ + yeniden |
| 9 | `should_run(now=)` gün bacağını taşımıyor (seam) | **EVET** — `sprint.py:399-401` `gun`u `dt.datetime.now(utc)`tan hesaplıyor, enjekte `now`u yok sayıyor | **P3** (test-seam) | kod-güvenli / ölçüm-borcu | `now`u gün hesabına da geçir | ZATEN ÖLÇÜLÜ (v159 yorumu); kodda teyit |
| 10 | pano `opCancelOpen` yeni `siniflar` alanını göstermiyor | **EVET** — v220 `siniflar` üretiyor (alpaca.py:469); `app.js:3390` yalnız `cancelled`/`kept` sayısı; app.js'te `siniflar`/`SINIF` = 0 referans | **P3** (YASA-6, küçük) | kod-güvenli | `opCancelOpen` sonucunda `siniflar`(giris/koruma/yabanci)+`foreign`+`kept.neden` bas (N5 app.js turu) | **YENİ** — v220 gece getirdi; bu turda ölçüldü |
| 11 | kill#2 (40 seans kuruma) + emeklilik 3-pencere sayaçları yazılmadı | **EVET (beyanlı borç)** — `EDG-2026-019` `status: registered`, "ölçüm kodu HENÜZ YAZILMADI"; ilgili state dosyaları YOK | **P3** (bugün etki 0; ön şarta bağlı) | ölçüm-borcu | EDG-2026-019 ölçüm kodu (Ç3 katalog düzeltmesi ön şart) + EXE-2026-002-R1 kill#4 daraltması ayrı tur | ZATEN BELGELİ (kartlar + ROADMAP WP-S2) |
| 12 | skills.py mezar-taşı (shadow hayalet) cümlesi bayat | **EVET** — `skills/_emekli/shadow/` YOK; `skills.py` `envanter()` docstring hâlâ present-tense "da sayar" diye anıyor | **P3** (doküman-hijyeni) | kod-güvenli / doküman | docstring örneğini güncelle/kaldır (dir artık yok) | **YENİ** — bu turda ölçüldü (dir gitmiş) |
| 13 | ajan-git yasağını MEKANİK kılan kapı yok | **EVET** — aktif `.git/hooks` yok, `.pre-commit-config` yok, shim yok; `dagit.sh` yalnız DAĞITIMI kapıyor; yasak yalnız CLAUDE.md sözleşmesi | **P2** (gece GERÇEK hasar: 2 ajan stash + hayalet süpürme) | süreç/araç-katmanı (operatör + araç kararı) | operatör kararı: git-shim / wrapper (NOT: `git stash`ın pre-stash kancası YOK — kapı ancak PATH-shim'le mekanikleşir) | kısmen (hasar biliniyor; kapı yokluğu bu turda teyit) |

---

## (ii) DALGAYA HAZIR (kod-güvenli · ölçülmüş · tanımlı — sıralı)

Ucuzluk × değer × başkasını-açma sırasıyla. **Dosya-ayrıklık** notu her satırda (tur ayrıklığı
sözleşmesi): aynı dosyaya dokunan kalemler tek brief'te birleştirilmeli.

1. **Kalem 1 — systemd `SuccessExitStatus=143`.** En ucuz; **N1 bildirim kanalının güvenilirliğini
   KAPI'lar** (kanal item 1 düzeltilmeden açılırsa her restart "FAILED" bildirir). Birim dosyası →
   bakım penceresi + elle test-ateşleme ("kurulu ≠ çalışır" doktrini). *Dosya: meridian.service.*
2. **Kalem 12 — skills.py docstring.** Bir cümle; hayalet dir gitti. *Dosya: skills.py (tekil).*
3. **Kalem 6 — public summary tohum/canlı ayrımı.** Dışa bakan dürüstlük; iki alan + payda beyanı.
   *Dosya: api.py (+ olası analytics).*
4. **Kalem 4 — E2 iç-motor totolojisi.** İç bacak None+beyan; ayna yorumu n<20'de sussun.
   *Dosya: loop.py (yazım) + analytics.py (özet yorumu).*
5. **Kalem 2 + Kalem 9 (BİRLİKTE) — sprint gün-hesabı.** İkisi de `sprint.py`nin gün bacağına
   dokunur: `sprint_child_orphaned` olayı + ölü `started_at`ı tetikten düş (2) + `now`u gün
   hesabına geçir (9). Tek brief. *Dosya: sprint.py (+ orphan olayı watchdog'a girerse watchdog.py).*
6. **Kalem 8 — E2 kilit.** İki oku-değiştir-yaz bloğu `file_lock(ENTRY_LEDGER)` + yanıltıcı yorum.
   *Dosya: loop.py (Kalem 4 ile AYNI dosya → tek loop.py brief'inde birleştir).*
7. **Kalem 10 — app.js `siniflar`.** N5 app.js turunun parçası (EV_TR koruma çevirileri zaten var).
   *Dosya: app.js.*
8. **Kalem 3 (kod bacağı) — `learning_stalled` türev göstergesi.** LLM-kota bacağı operatör; ama
   "durdu" göstergesi kod-güvenli. *Dosya: watchdog.py / analytics.py.*
9. **Kalem 7 (kod bacağı) — `universe_drift=unknown` alarm olsun.** "Ölçemedim" ≠ "sapma yok".
   (lxml kurulumu ayrı dağıtım kalemi.) *Dosya: analytics.py / watchdog.py.*
10. **Kalem 5 (kod bacağı) — SB-1 boyut makbuzu.** Melez KARARI operatör; ayrışmayı tek sayı+payda
    olarak sürekli ölçmek kod-güvenli. *Dosya: broker.py / analytics.py.*

**Dalgaya hazır DEĞİL:** Kalem 11 (EDG-2026-019 ölçüm kodu yazılmadı — kart-güdümlü, N2/skill
rotasyonu veri beslemeden sayaçlar dolmaz) · Kalem 13 (mekanik git-kapısı = araç/süreç kararı) ·
Kalemlerin operatör bacakları (aşağıda).

---

## (iii) OPERATÖR SORULARI (kod değil, hüküm)

1. **Bildirim kanalı token (N1).** `TELEGRAM_BOT_TOKEN`+`CHAT_ID` / `MERIDIAN_WEBHOOK_URL` boş →
   fail-notify her koşuda NO-OP. Teslim edilmemiş sev-1 (tüm zaman): korumasiz 40 · MIRROR_DRIFT 34
   · NAKED_POSITION 8. **BAĞ:** Kalem 1 (exit-143) kanal AÇILMADAN düzeltilmeli. **Soru:** token
   girilecek mi, ve Kalem 1 ile aynı pencerede mi?
2. **Melez pozisyon (WP-S).** İç 54/64/43/33 vs ayna 25/37/22/22 (~%49). Fark kapatılsın mı?
   (Kod tarafı: aynada ADV/likidite kapısı da yok — bugün ayna küçük olduğu için zarar görünmüyor.)
3. **Uyuyan yol (`dormant_setup`).** 32 plan / 0 işlem / 1 GO. (a) icraya bağla · (b) tavsiye kalsın
   kapı GO vermesin · (c) geri al? (Gözlemlenebilirlik tarafı otonom yapılabilir.)
4. **N4 bakım penceresi (cf çıkış-sadakati).** Saatler sürer + state'e yazar → canlı worker
   durdurulmalı. En pahalı/en değerli kalem; %96 skor havuzundaki +0,039R iyimserliği kapatır.
   **Soru:** pencere ne zaman?
5. **Massive/FMP plan.** FMP 402 → temel/kazanç/insider/haber katmanı ölü; rejim maruziyet bütçesi
   %60 tek-kaynaktan (SPY türevi). **Soru:** FMP planı yükselt mi, Massive'e mi geç?
6. **Sektör/ısı tavanı değeri.** Canlı: `heat_hard_r:5.0` · `heat_review_r:3.5` ·
   `max_sector_exposure_pct:40`. **Soru:** değer değişecek mi? (ROADMAP hükmü: ısı tavanı ailesi
   "vol'ü düşürür ama parayı da düşürür" → ERTELENMİŞTİ; bu bir karşı-kanıt olarak okunmalı.)
7. **Skill terfi/emeklilik.** Terfi (vcp) / emeklilik (momentum-burst) ADAYLARI operatör kararıdır
   (motor-içi otomatik bayrak yasağı, 2026-08-06 hükmü). **UYARI:** promptta anılan figürler
   (vcp +0,116R / momentum-burst −0,114R) **canlı state'te YENİDEN-ÜRETİLEMEDİ** — `eksen2.uretilen=0`,
   eşik-aşan tek skill `pullback-screener` (n_cf=21, cf_avg_r=−0,968, MOTOR-İÇİ, aday değil).
   EDG-2026-019 ölçüm kodu yazılmadan bu R-figürleri doğrulanamaz (bkz. §4).

---

## (iv) ÖLÇÜLEMEYENLER (dürüst boşluklar — adıyla)

- **v220 korumasının GERÇEK EOD süpürmesinde sağ kalması.** Kod + md5 doğrulandı; ama süpürücü
  fixli koddan (02:34 restart) sonra HİÇ koşmadı — piyasa Cuma'dan beri kapalı. İlk davranışsal
  kanıt Pazartesi 13:30 UTC sonrası. (Mantık doğru; idempotans çivisi commit mesajında beyanlı.)
- **08:35 P-KORUMA OCO'larını KİM kurdu** (otomatik kadans mı, operatör mü). `koruma_kur_istegi`
  olayında `onay_verildi` bayrağı VAR (app.js:1161 çevirisi bunu okuyor) ama değerini yakalamadım;
  olayların `kaynak` alanı null. Kesinleştirmek için o bayrağın değeri okunmalı.
- **Skill terfi/emeklilik R-figürleri (vcp +0,116R / momentum-burst −0,114R).** Canlı `eksen2`de
  üretilmiyor; EDG-2026-019 ölçüm kodu yazılmadı. Kart evidence_refs vcp-screener'ı `avg_r=0,0`
  diye anıyor — promptun +0,116R'si ile uyuşmuyor, uydurmuyorum: ölçülemedi.
- **İç↔ayna %49 farkının ÜRETEN hesabı.** Yalnız farkı doğruladım (drill'le birebir); üreten
  boyutlama zincirini ayrıştırmadım.
- **Neden ayna 08-05, iç motor 08-06 doldu** (aynı planlar, farklı gün). Drill'le aynı boşluk.
- **Tam test suite durumu.** Tek-otoriter kural gereği koşmadım. Son referans 4133/0 @ `4dbe688`
  (08-03, 6 gün önce). Commit `7f91178` "otoriter suitenin üç kırmızısı kapandı" diyor — ben
  DOĞRULAMADIM (kapanış iddiası, artefakttan sınanmadı).
- **`shadow_model.json` ham dosyası.** `n_live`/`promote_min_n` ham dosyada null; gerçek değerler
  API'de (`ogrenme.antrenman.terfi`) — ölçüldü ama ham dosya boş bir gölge (okuyucu API katmanı).

---

## EK — KANIT DEFTERİ (yük taşıyan canlı değerler, 2026-08-09 ~08:50 UTC)

- **Birimler:** meridian (active, start 02:34:03Z) · barsarchive · litestream · tick-watchdog.timer
  · backup.timer. `SuccessExitStatus=` boş · NRestarts=0.
- **Sprint:** `sprint_status.json` pid 96924 (ÖLÜ), phase baseline, 281/527, updated 08-07T14:15:30,
  yaş 42,6 sa; `sprint_runs.jsonl` YOK; `should_run` → şu an `saat_dilimi_disinda`, pencere içinde
  `tetik_yok(gun=1<7, taze=0<5)`; `watchdog.sprint_cadence` eşiği 9 gün (watchdog.py:58) → ~08-16'ya
  dek sessiz. Orphan dedektörü (watchdog.py:1062) ARTEFAKT içindir, sprint-çocuğu için DEĞİL.
- **Öğrenme:** hyp 51 (donuk 08-02T10:36, 166 sa); `terfi{n_live:1, promote_min_n:30, promoted:false}`;
  `dolgu_kuyrugu{gorussuz:405, gece_tavani:0}`; `brain_cooldown` agent streak 17 / gemini rate_limit;
  hermes reflections 1, son_result `no_clearing_candidate`. Zincir: claude cred=false → nous/gemini
  (ikisi de `gemini-3.5-flash`, `same_model_ids:[[gemini,nous]]` — yedeklilik iddiası ÖLÇÜLMÜYOR).
- **E2 (`entry_execution.jsonl`, 9 satır):** iç bps {5.038, 5.022, 5.007, 5.012, 5.104}; ayna bps
  {16.1, 54.6, 134.5, 15.0}; `icra.slipaj.ayna.fill_vs_limit_bps.ort=−271` yorumu "tavan gevşetilebilir"
  n=4 üstünde basıyor. `pessimistic_band_v2.ampirik_bps` hâlâ n=0.
- **Sermaye/karne:** DB trades=96, portfolio realized_pnl −450,38, `sermaye_resetleri` tohum=95/canli=0;
  `/api/public/summary` closed_trades=96, live/seed anahtarı YOK, score −0,0089.
- **Üretim kontrolleri:** `universe_drift.status=unknown (lxml ImportError)`, universe 251;
  `integrity.production` ok 9/10, starved: fmp_source(402)+llm_calibration; `finviz_unavailable` 3.682.
- **Pozisyonlar:** iç NUE54/EMR64/BKNG43/AMGN33; ayna NUE25/EMR37/BKNG22/AMGN22 (+NVDA1 motor-dışı);
  broker açık emir 4 (P-KORUMA-…-0835, accepted/held); eski P-KORUMA-…-1623 canceled (08-07T20:32).

# KARŞIT · MERCEK 2 — ÖLÇÜM BAĞLAMI TUZAĞI (2026-08-24)

Kapsam: `.../ogrenme_kurakligi_2026-08-24/TESHIS.md` teşhisinin BAĞLAM geçerliliği.
Bu tur SALT OKUMA: canlıya yazılmadı, birim restart edilmedi, kod değiştirilmedi, git koşulmadı.
Ölçüm zamanı: 2026-08-24T00:19–00:35Z (canlı: ubuntu@130.61.126.87:/opt/meridian).

## HÜKÜM
Birincil hüküm (SINIF a — yapısal erişilmezlik) BAĞIMSIZ KANITLA AYAKTA; ama teşhisin üç
destekleyici zinciri bağlam hatası taşıyor ve biri (SINIF c ÇÜRÜTÜLDÜ) manşet düzeyinde geçersiz.

## A) CANLI mı YEREL mi — ve hangisi "canlı"?
Ölçüldü (sha256 ilk 16 + mtime, yerel vs /opt/meridian):

| dosya | yerel | canlı disk | aynı mı |
|---|---|---|---|
| probgate.py | c99ef4e16173a15e 08-23T17:53:43 | c99ef4e16173a15e 08-23 14:53:43Z | AYNI |
| reflect.py | b36f1e55a841ad1c 08-24T00:06:24 | b36f1e55a841ad1c 08-23 21:06:24Z | AYNI |
| hermes_runtime.py | 79575145cfa9d3b9 | 79575145cfa9d3b9 | AYNI |
| sprint_run.py / analytics.py / shadow_model.py | — | — | AYNI |
| **hermes.py** | 8683b67abebff896 **314262 B** 08-24T02:59:37 | f2834ff41c758527 **313644 B** | **FARKLI** |

`hermes.py` farkı ÖLÇÜLDÜ (canlı kopya çekilip diff): tek hunk, satır ~4193, WP7-40 yorum bloğu
(nous_eval künye beyanı). Kod değişikliği YOK. Sonuç: (a) riski GERÇEK (yereli bu tur bir başka
ajan 02:59'da değiştirmiş, TEŞHİS 03:15'te yazılmış) ama teşhisin alıntıladığı `hermes.py:1811`
merdiven bölgesi ETKİLENMEMİŞ; yalnız 4193'ten SONRAKİ satır numaraları canlıya göre +7 kaymış.

## A2) ASIL BAĞLAM HATASI: "canlı disk" ≠ "koşan süreç"
`meridian-learn` ExecMainStartTimestamp = **2026-08-16 23:27:06Z**, NRestarts=0, MainPID 305928,
ExecStart `/opt/meridian/.venv/bin/python -m meridian.learn_run`, WorkingDirectory /opt/meridian
(hepsi bu turda yeniden ölçüldü). Ama diskteki probgate/reflect/hermes/analytics **08-23'te**,
hermes_runtime **08-23 21:06**'da değişmiş. Yani teşhisin `sed -n` ile okuduğu KOD, saat başı koşan
SÜRECİN kodu DEĞİL. TEŞHİS bunu yalnız `hermes_runtime` için (§3.4) fark etti, formül/K/iz
iddialarına genellemedi.

İki bağımsız kanıtla iddialar KURTARILDI (uydurma değil, ölçüm):
1. `meridian/__pycache__/probgate.cpython-312.pyc` — pyc başlığı: kaynak mtime 2026-08-16T20:13:01,
   **kaynak boyu 32785 B** (bugünkü disk 33417 B ⇒ içerik gerçekten değişmiş). Bu pyc 08-16
   21:59'da derlendi, süreç 23:27'de başladı ⇒ **süreçteki probgate = bu pyc**. `marshal` ile
   açıldı (çalıştırılmadı): modül float sabitleri `[0.8, 0.999, 0.7]`, isimler `P_BASE/P_CEIL/
   P_CONFIRM`, `PairedProbabilisticGate.p_required_for` bytecode'u birebir
   `min(P_CEIL, 1 − max(1e-6, (1−p_base) − _meta_extra_p())/max(1,int(k)))`.
   ⇒ **Koşan süreçte P_BASE=0,80 ve formül bugünküyle AYNI.** Teşhisin eşik iddiası bağlam-geçerli.
2. `state/validation_ledger.jsonl` SON SATIR (koşan süreç yazdı): `ts 2026-08-21T20:45:37`,
   `gate_law "probabilistic"`, **`k_probes: 8`** — aynı koşumda `evaluated=2`.
   ⇒ **K = PLANLANAN sonda** iddiası, disk kodundan değil sürecin KENDİ defterinden doğrulandı.

Kurtarılamayan: koşan `reflect.py`nin 08-16 hâli hiçbir yerde yok (reflect pyc 08-23 22:03'te
üstüne yazıldı, backups/ altında kaynak kopya yok, git yasak). `sprint_run.py:118` iz süzgeci ve
`reflect.py:2016-2032` plan mantığı alıntıları CANLI DİSK kodudur, 08-21 koşumunu üreten kod değil.

## B) Pencere yeterli miydi?
`journalctl` HİÇ kullanılmamış; sayımlar `state/events.jsonl`dan. O dosya **döndürülmüyor**:
tek dosya, 22.289.965 B, ilk satır `2026-07-14T09:36:31`, son satır `2026-08-24T00:19:18`.
`state/` altında events arşivi/rotasyon dosyası yok. ⇒ (b) tuzağı YOK, pencere tam.
Tek kusur tazelik: teşhis 153 koşum sayarken 154'üncüsü **2026-08-24T00:16:24**'te aynı sayılarla
(`evaluated 40, cleared 0`) basıldı; `warmup_scale.json.son.at` da 00:16:24. Kalıp sürüyor.

## C) 20260821 sprinti — donmuş anlık görüntü mü?
`state/sprint_status.json` mtime 2026-08-22 06:00:40, `phase: done`. Daha yeni sprint YOK
(`state/sprint/`: 20260813-171532, 20260813-202316, 20260814-220214, 20260821-220656).
SEBEBİ ÖLÇÜLDÜ — teşhiste hiç geçmeyen bir olay: `sprint_cadence_skip` her ~5 dk basılıyor,
`sebep: "tetik_yok(gun=2<7, taze=0<5)"`, `gecen_gun: 2`, `taze_hipotez: 0`
(2026-08-24T00:19:18 dahil, 08-21 18-23 penceresinde 50 kez). ⇒ Sprint kanalı HAFTALIK kadanslı ve
tetiği yok; 20260821 GÜNCEL durumdur, bayat anlık görüntü değil. (c) tuzağı YOK.

## D) `warmup_sprint` ≠ `hermes_search` ≠ `meridian-sprint@` — VE BULGU TAŞINMIŞ
Üç mekanizma ölçüldü:
- **warmup** (`hermes_runtime._warmup_sprint`): saat başı, `reflect.coordinate_descent_search(...,
  record_session=False)`, budget 10×çarpan 1, `tavan_dk 300`, canlı veri, ship yetkisi YOK.
- **ship araması** (`hermes_search_*`): birim ortamı `HERMES_SEARCH_BUDGET=8`,
  `MERIDIAN_SEARCH_MAX_MIN=60` (systemd Environment'tan ölçüldü — "operatör override" bu),
  canlı veri, `incumbent_oos 0,2687`.
- **sprint** (`meridian-sprint@20260821-220656`): AYRI KUM HAVUZU
  (`MERIDIAN_SPRINT_SBROOT=/opt/meridian/state/sprint/20260821-220656`, conf `{"k_max":2,"budget":6}`),
  `eval_start 2024-07-01`, `cutoff 2024-06-30`, kum havuzu defterinde **538 `daily_cycle`** ve
  `DATA_QUALITY GERİLEME: book_date 2026-08-21 → 2024-07-01 · trades 893 → 0 · strategy_version 5 → 1
  · hypotheses 60 → 0 · peak_equity 107288 → 100000` ⇒ **2024-07-01'den başlayan, v1'i sıfırdan
  kuran 538 günlük TARİHSEL TEKRAR**. `incumbent_oos 0,409` bu dilimin incumbent'ıdır.

**HATA:** TEŞHİS §2(c), sprintin `note`u olan *"bu veri diliminde v1 yerel-optimal"* hükmünü,
canlı ship kanalının 2026-08-21T19:57:21 sondasıyla (`entry.w_turnover 0,15`,
candidate_oos 0,2823 > incumbent_oos 0,2687) çürütüyor. Bu sonda sprint BAŞLAMADAN (22:07)
2,5 saat ÖNCE, BAŞKA bir veri diliminde, BAŞKA bir incumbent'a karşı ölçüldü. Sprintin cümlesi
zaten "bu veri diliminde" diye kapsamlanmış. ⇒ **(c) ÇÜRÜTÜLDÜ hükmü bağlam-geçersiz.**
Ayakta kalan daha zayıf ifade: *canlı ship kanalında incumbent'ı nokta-tahminde geçen bir aday
reddedildi ve gerekçesi defterde yok.*

## E) TEŞHİSTE OLMAYAN, BU TURDA ÖLÇÜLEN ÜÇ ŞEY
1. **Paralel ön-dolum havuzu 2026-08-12'den beri ÖLÜ.** `arama_havuzu_zaman_asimi` 44 olay
   (08-12:5, 08-13:8, 08-14:8, 08-15:8, 08-16:9, 08-17:5, 08-21:1), HEPSİNDE **`biten: 0`**,
   `atalet_sn 1800`, `yer probe_prefill` — "işçiler öldürüldü, kalanlar SIRALI hesaplanır".
   Sonuncusu **2026-08-21T19:14:01, `bekleyen: 8`** — yani o aramanın 8 sondasının TAMAMI TAZEYDİ.
   ⇒ TEŞHİS §3.5'in zinciri ("`parallel_probes_prefilled` 08-12'den beri yok ⇒ her şey önbellekte")
   YANLIŞ ÇIKARIM: `parallel_probes_prefilled` yalnız BAŞARI dalında basılıyor (reflect.py:1772),
   atalet dalı bunun yerine `arama_havuzu_zaman_asimi` basıyor (reflect.py:1777). Aynı sessizliği
   ölü havuz da üretir. (Isınma için "hepsi önbellekte" sonucu yine de ayakta: 08-17→08-24 arası
   ~154 koşumda SIFIR havuz ataleti + koşum ≤79 sn.)
2. **Kapıyı geçmiş sonda VAR: 6 tane** — hepsi 2026-07-20/21, `total=10`; üçünde
   candidate_oos 0,1918–0,2119 vs incumbent_oos **0,0996**. Bugünkü formülde K=10 → 0,98;
   eski formülde (`min(0.95, p_base+0.01·(K−1))` = 0,89) geçebilirlerdi. Formülün NE ZAMAN
   değiştiği bu turda ÖLÇÜLEMEDİ (git yasak; en geç 2026-08-02'de yürürlükte —
   `docs/SISTEM-DENETIMI-2026-08-02.md:667`). ⇒ "hiçbir ölçüm eşiği geçmedi" cümlesi ÇAĞ-KARIŞIMI
   riski taşıyor: geçenler var, ama başka bir kapı rejiminde.
3. **Kanıt tabanı Ağustos öncesi.** `hermes_search_probe`: 999 olay, iki skorlu 387, cand>inc 141
   (%36,43 — A merceğiyle birebir doğrulandı) AMA iki skorlu sondaların 378'i 07-14…07-31,
   yalnız **9'u 08-01 sonrası**. `arming_measured`ın son satırı **2026-08-10** (`p_required 0,8`).
   Ayrıca incumbent 0,0996 → 0,2687'ye çıkmış. ⇒ %36,4 "kazanma" oranı ŞANS ÜSTÜ değil ALTI
   (<%50) ve eski rejime ait; (c)'yi çürütmek için değil, desteklemek için okunabilir.

## F) DEĞİŞMEYENLER (karşıt ölçüm iddiaları DOĞRULADI)
- `neden_dagilim` yokluğu süreç bayatlığını KANITLIYOR: `obs._emit` alanları OLDUĞU GİBİ yazıyor,
  None/boş süzgeci YOK (meridian/obs.py:86-99) ⇒ kod koşsaydı `neden_dagilim: {}` bile görünürdü.
- Merdiven ölü: `warmup_budget_scaled` yalnız 2 olay (08-08 06:45 çarpan 1→2, 08-08 14:19
  sure_tavani 2→1); o günden beri `carpan 1 / duvar 1`.
- `gate_calibration.json`: `extra_p 0.0`, `n_measured 1`, `durum "kurak"` ⇒ eşik saf `1 − 0,20/K`.
- 179 `hermes_search_start` / 60 `hermes_search_done` (yeniden sayıldı, aynı).
- Ship kanalının 6 sondasının `MERIDIAN_SEARCH_MAX_MIN` yüzünden atlanıp K'da sayılması: kod
  (reflect.py:1957 yorumu + :2034 `_max_min`) ve `evaluated=2 / k_probes=8` ile TUTARLI; ayrıca
  `search_sure_tavani_kesildi` 08-21'de BASILMADI (tek örneği 08-08, `tavan_dk 300`) — yani kesinti
  değil, taze-hesap atlaması. Yine de "6" doğrudan bir sayaçtan okunmadı, ÇIKARIMDIR.

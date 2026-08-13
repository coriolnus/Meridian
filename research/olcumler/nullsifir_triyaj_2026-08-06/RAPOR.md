# `?? 0` / `|| 0` TRİYAJI — 2026-08-06 (v196 / KALEM 3)

**Rol:** acil düzeltme turu, KALEM 3. **Girdi:** `docs/BASELINE-2026-08-06.md` §B.1 / bulgu **T2**
(ciddiyet 4). **Kapsam:** `meridian/web/app.js` — tur sözleşmesinde yazılabilir tek render dosyası.

Bu belge bir ÖLÇÜM + bir SINIFLANDIRMA + uygulanan düzeltmelerin kaydıdır. Sınıflandırma ELLE
yapıldı ve her satırın gerekçesi yazılıdır; tablo bir betikten üretildi (satır numaraları
**düzeltmelerden SONRAKİ** dosyadan okundu — bir okuyucu tabloyu bugünkü dosyada doğrulayabilir).

---

## 0. YÖNTEM — ayırıcı tek cümlede

Sayım **eşleşme** başınadır (satır başına değil), `0.5` gibi ondalıklar dışlanır (`0(?![\d.])`),
`//` ile başlayan yorum satırları sayılmaz. Baseline'ın ölçtüğü küme birebir yeniden üretildi.

**(a) YALAN SÖYLEYENLER** — ifadenin operandı **sunucudan gelen bir alan** VE sonuç bir **okuma
olarak DOM'a yazılıyor** (ya da yazılan bir cümleyi/hükmü belirliyor). Burada `undefined` "uç bu
alanı hiç göndermedi" demektir (şema eski, mekanizma kapalı, alt sistem düşmüş) ve `?? 0` onu
kendinden emin bir **"0"**a çevirir. PRODUCT.md § Honesty-of-absence'ın tarif ettiği ihlal budur.

**(b) GÜVENLİ** — sıfır **yerel olarak üretilmiş** bir şeyden geliyor (biriktirici tohumu, dizi
boyu, payda, çubuk genişliği, SVG koordinatı) ya da ifade yalnız bir **koşul kapısında** yaşayıp
DOM'a hiç ulaşmıyor. Bu yerlerde `undefined` "ölçülmedi" anlamına GELEMEZ, çünkü değer bu dosyada
kuruluyor. `app.js`in kendi yorumu (eski 2125) bu meşru kullanımı zaten beyan ediyordu; ölçülen
eksik meşruiyetin yokluğu değil, **ayrımın mekanik bir zorlayıcısının olmayışıydı**.

**Karşı-kanıt kayda geçer:** jenerik biçimleyici katmanı ZATEN dürüst — `trn()` null/NaN'da `—`,
`money()` null'da `—`, `onk()` ön-eki bile bastırıyor. Kaçak, biçimleyiciye GİRMEDEN önce `?? 0`
ile kapatılan alanlardadır. Bu yüzden (a) düzeltmelerinin çoğu bir EKLEME değil bir SİLMEdir.

## 1. SAYIM

| Ölçüm | Sayı |
|---|---|
| `app.js` toplam eşleşme (düzeltme ÖNCESİ) | **211** |
| — **(a) yalan söyleyenler** | **167** |
| — **(b) güvenli** | **44** |
| Bu turda DÜZELTİLEN (a) | **30** |
| **KUYRUKTA KALAN (a)** | **137** |
| `app.js` kalan eşleşme (düzeltme SONRASI) | **192** |

**KUYRUK ÖDEMESİ — v207 (2026-08-07), 4 satır.** Eksen-2 kartının dört `?? 0`ı
(`app.js:5185 #0`, `5186 #0`, `5186 #1`, `5187 #0` — kuyruk tablosunda **ÖDENDİ (v207)** olarak
işaretli) o turda kaldırıldı: satır `.ozet-serit` hücrelerine taşındı ve yokluk artık `ölçülemedi`
diye ADIYLA yazılıyor, hücre `ÖLÇÜLEMEDİ` rozetine düşüyor. Bu yüzden v207 SONRASI dosya **177**
ölçtü (dalga-2 EKLENTİSİ aşağıda: bugünkü dosya **192**). Üstteki **211 / 167 / 44 / 30 / 137**
sayıları 2026-08-06 triyajının DONMUŞ anlık görüntüsüdür ve değişmez (bir ölçüm kaydı sonradan
yeniden yazılmaz); ödenen/eklenen her satır buraya EKLENEREK sayılır.
**Kuyrukta bugün kalan (a): 137 − 4 = 133.**

**DALGA-2 EKLENTİSİ — v-dalga2 (2026-08-09), +15 satır, HEPSİ (b).** Dalga-2 (01ba684 + ff55a18)
süpürücü ailesine 15 yeni `?? 0` guard'ı ekledi (olay çekmecesi EV_TR `app.js:1179-1187` + iptal
tuşu sınıf dökümü `app.js:3439`); dosya **177 → 192** ölçtü. On beşi de ELLE (b) SINIFLANDI —
körce tavan yükseltme DEĞİL. Gerekçe: hepsi ÜRETİCİ-GARANTİLİ bölümleme sayaçlarıdır, YASA-6 ile
uçtan doğrulandı — `alpaca.py:487-491` (`giris`/`koruma`/`yabanci`/`cancelled`), `api.py:2045`
(`cancelled`/`kept`), `loop.py:280-281` (`cancelled`/`kept`/`foreign`) HER olayda koşulsuz
`int(...)`/`len(...)` basar ve boş kova KAYNAKTA 0'a düşer (ÖLÇÜLMÜŞ sıfır — bu deponun §5'te zaten
(b) saydığı "biriktirici tohumu / bölümleme" deseni). Hiçbiri liveness/manşet ölçülemedi-dalına
sızmadı (manşet `!= null` üçlemesi kullanır, `?? 0` DEĞİL; landing `olculenSatiri` de öyle).
`opCancelOpen`inki AYRICA v225 (`test_dalga2_kucukler_v225.py:190`) tarafından ZORUNLU kılınır —
kaldırmak o testi kırardı. Satır satır §7'de. Frozen **211 / 167 / 44 / 30 / 137** DEĞİŞMEZ; bu 15
AYRI bir ölçüm turudur. **Bugün toplam (b): 44 + 15 = 59.** `NULLSIFIR_TAVAN` 181 → 192 (v196,
beyanlı).

**Kapsam dışı ama beyan edilir** (bu turda yazılabilir değil, düzeltilmedi — toplam depo 215):
`landing.js:47` ×2 (`hypotheses_total`/`hypotheses_shipped` → landing metnine), `landing.js:66`
(`d.score || 0`, renk seçimi), `palette.js:188` (yerel sayaç artışı — **(b)**).
`index.html` · `theme.js` · `workflow.js` · `landing.html` · `workflow.html` · `runbook.html`: **0**.

Baseline'ın "DOM'a yazılan 162" tahmini ile bu turun **(a) = 167**'sı arasındaki fark yöntemseldir:
baseline `${` sayısıyla mekanik ölçtü ve bir **büyüklük mertebesi** olduğunu beyan etti; buradaki
sayı tek tek okunmuş 211 çağrı yerinden geliyor ve iddiayı-belirleyen (DOM'a doğrudan yazılmayan
ama basılan cümleyi seçen) yerleri de (a)'ya alıyor.

## 2. SIRALAMA — hangi 30, neden

(a) sınıfı 30'dan büyük olduğu için tur sözleşmesi gereği **en kritik 30 eşleşme** düzeltildi.
Kriter uydurulmadı, üç kademede beyan edildi:

- **Kademe 1 — para ve risk birimi (3 eşleşme).** Yanlış okunması doğrudan bir para/risk yargısı
  üretir. `$0 harcandı` ile `harcama ölçülmedi` aynı ekranda aynı görünüyordu; `0.00R` ölçülmemiş
  bir işlemi *sonuçlanmış ve nötr* diye okutuyordu.
- **Kademe 2 — ölçülmemişten üretilen güvenli-taraf iddiası (10 eşleşme).** En sinsi sınıf: bir
  DEDEKTÖR hiç ölçmediği hâlde temiz rapor veriyor ("boşluk yok" · "liste temiz" · "bekleyen yok"
  · "bayat yok" · "defterde hipotez yok"), üstelik bazıları YEŞİL. Bir alarmın sessizliği ile bir
  ölçümün yokluğu aynı piksele düşüyordu.
- **Kademe 3 — icra/ayna kartı, dürüst biçimleyici devre dışı (17 eşleşme).** `trn(x ?? 0)` deseni:
  biçimleyici null'da zaten `—` basıyor, `?? 0` onu **bilerek** iptal ediyor. Kart icra
  gerçekliğinin masasıdır (gönderim · ret · dolum · kill ölçütü · iki motor mutabakatı) ve
  düzeltmenin yarıçapı sıfıra yakındır — dört karakterlik bir silme.

Düzeltilmeyen (a)'lar **sessizce kısaltılmadı**: tamamı §4'te satır satır listelidir.

## 3. DÜZELTİLEN 30

| # | kademe | satır (ölçüm anı) | ifade | ÖNCE → SONRA |
|---|---|---|---|---|
| 1 | 1 | `app.js:6052` #0 | `|| 0` | `t.r == null ? "—" : isr(t.r, trn(t.r, 2)) + "R"` |
| 2 | 1 | `app.js:6052` #1 | `|| 0` | `t.r == null ? "—" : isr(t.r, trn(t.r, 2)) + "R"` |
| 3 | 1 | `app.js:6810` #0 | `?? 0` | `${money(sp.spent_usd)}` — `money()` null'da '—' |
| 4 | 2 | `app.js:1499` #1 | `|| 0` | `taze = m.stale_n == null ? null : n - m.stale_n`; oran ve pay '—', üçüncü hâl "bayat sayısı ÖLÇÜLMEDİ" |
| 5 | 2 | `app.js:3723` #0 | `?? 0` | null → "hipotez sayısı ÖLÇÜLMEDİ — halkanın boş kalma gerekçesi bilinmiyor" |
| 6 | 2 | `app.js:4815` #0 | `|| 0` | null → "sapma sayısı ÖLÇÜLMEDİ — bu satır 'liste temiz' DEMEZ"; `pos` rengi `n_stale === 0` şartına bağlandı |
| 7 | 2 | `app.js:5263` #0 | `?? 0` | `const n = g.bosluk_sayisi` (üç hâl: null / 0 / >0) |
| 8 | 2 | `app.js:5270` #0 | `?? 0` | null → "boşluk sayısı ÖLÇÜLMEDİ — bu satır 'boşluk yok' DEMEZ", renk `mut` |
| 9 | 2 | `app.js:5270` #1 | `?? 0` | null → "boşluk sayısı ÖLÇÜLMEDİ — bu satır 'boşluk yok' DEMEZ", renk `mut` |
| 10 | 2 | `app.js:5270` #2 | `?? 0` | null → "boşluk sayısı ÖLÇÜLMEDİ — bu satır 'boşluk yok' DEMEZ", renk `mut` |
| 11 | 2 | `app.js:6565` #0 | `|| 0` | `const pend = it.backfill_pending` |
| 12 | 2 | `app.js:6598` #0 | `|| 0` | `trn(pend)` + üçüncü hâl "kuyruk ÖLÇÜLMEDİ" |
| 13 | 2 | `app.js:6628` #0 | `|| 0` | `const pend = it.backfill_pending`; kart `trn(pend)` basıyor |
| 14 | 3 | `app.js:3319` #0 | `?? 0` | `trn(slp2.n_defter)` |
| 15 | 3 | `app.js:3334` #0 | `|| 0` | `stopN` çıplak; satır üç hâlli (`— ölçülmedi (alan yükte yok)`) |
| 16 | 3 | `app.js:3354` #0 | `?? 0` | `trn(ay.n)` |
| 17 | 3 | `app.js:3356` #0 | `?? 0` | `trn(ay.n)` |
| 18 | 3 | `app.js:3362` #0 | `?? 0` | `trn(dl.n_dolan)` |
| 19 | 3 | `app.js:3372` #0 | `?? 0` | `trn(ic.n)` |
| 20 | 3 | `app.js:3377` #0 | `?? 0` | `trn(mt.ayrisan_n)` |
| 21 | 3 | `app.js:3379` #0 | `?? 0` | `(mt.ortak_plan_n && mt.ayrisan_n != null) ? … : null` — paysız çubuk çizilmez |
| 22 | 3 | `app.js:3387` #0 | `?? 0` | `trn(slp2.n)` · `trn(slp2.n_defter)` |
| 23 | 3 | `app.js:3387` #1 | `?? 0` | `trn(slp2.n)` · `trn(slp2.n_defter)` |
| 24 | 3 | `app.js:3390` #0 | `?? 0` | `trn(ay.n)` |
| 25 | 3 | `app.js:3397` #0 | `?? 0` | `trn(dl.n_dolan)` |
| 26 | 3 | `app.js:3403` #0 | `?? 0` | `trn(ic.n)` |
| 27 | 3 | `app.js:3409` #0 | `?? 0` | `trn(ic.kacan_limit_n)` · `trn(ic.gap_veto_n)` · `trn(ic.n_dolan)` |
| 28 | 3 | `app.js:3409` #1 | `?? 0` | `trn(ic.kacan_limit_n)` · `trn(ic.gap_veto_n)` · `trn(ic.n_dolan)` |
| 29 | 3 | `app.js:3409` #2 | `?? 0` | `trn(ic.kacan_limit_n)` · `trn(ic.gap_veto_n)` · `trn(ic.n_dolan)` |
| 30 | 3 | `app.js:3414` #0 | `?? 0` | `trn(mt.ortak_plan_n)` |

**Yan etki, beyanlı:** `stopN` (kademe 3) düzeltilince satırın KENDİ dalı da üç hâlli yapıldı —
aksi hâlde değer `—` basarken metin "· ölçüt karşılandı" demeye devam ederdi. Aynı gerekçeyle
`4815`, `5270`, `1499` ve `6598`de renk/cümle dalları düzeltmenin parçasıdır. Bunlar YENİ
eşleşme değildir; düzeltilen ifadenin sonucudur ve sayım 30'da kalır.

## 4. KUYRUK — düzeltilmeyen (a) sınıfı, 137 eşleşme

Satır numaraları **bugünkü** (düzeltme sonrası) `app.js`ten.

| dosya:satır | ifade | sınıf | gerekçe | bağlam |
|---|---|---|---|---|
| `app.js:1014` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `daily_cycle: e => `Günlük döngü işledi — ${e.date \|\| ""} · ${e.candidates ?? 0} aday, ${e.armed ?? 0} silahlı`,` |
| `app.js:1014` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `daily_cycle: e => `Günlük döngü işledi — ${e.date \|\| ""} · ${e.candidates ?? 0} aday, ${e.armed ?? 0} silahlı`,` |
| `app.js:1020` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `hermes_search_done: e => `Hermes arama bitti — ${e.evaluated ?? 0} aday, ${e.cleared ?? 0} kapıyı geçti`,` |
| `app.js:1020` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `hermes_search_done: e => `Hermes arama bitti — ${e.evaluated ?? 0} aday, ${e.cleared ?? 0} kapıyı geçti`,` |
| `app.js:1112` #0 | `|| 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `const head = `<p class="hint" style="margin-top:0">${a.pending \|\| 0} okunmamış alarm · ${kanal}${` |
| `app.js:2965` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<b style="color:var(--tx)">${src.bars ?? 0}</b> bars CSV${src.finviz_extra` |
| `app.js:3077` #0 | `?? 0` | a | ORAN payı/paydası — eksik alan 'sapma yok' oranı üretiyor | `const d = pct - (taban[alan] ?? 0);` |
| `app.js:3079` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `Math.round(taban[alan] ?? 0)} · ${n} sembol">${d > 0 ? "+" : d < 0 ? "−" : "±"}${` |
| `app.js:3191` #0 | `|| 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<span class="mono-num">${r.plans_n \|\| 0}${r.last_plan_date` |
| `app.js:3277` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Force-sync (bu tur)</span><b>strip ${fs.stripped ?? 0} · PATCH ${fs.trail_patched ?? 0}${fs.t…` |
| `app.js:3277` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Force-sync (bu tur)</span><b>strip ${fs.stripped ?? 0} · PATCH ${fs.trail_patched ?? 0}${fs.t…` |
| `app.js:3549` #0 | `?? 0` | a | `trn()` null'da zaten '—' basıyor; `?? 0` DÜRÜST BİÇİMLEYİCİYİ devre dışı bırakıyor | `<div class="srow"><span>Pencerede dolan satır</span><b class="mono-num">${trn(kb.n_dolan ?? 0)}</b></div>` |
| `app.js:3554` #0 | `?? 0` | a | `trn()` null'da zaten '—' basıyor; `?? 0` DÜRÜST BİÇİMLEYİCİYİ devre dışı bırakıyor | `<b class="mono-num">ölçülmüş dolum ${trn(kb.n_olculen ?? 0)} / asgari ${trn(kb.min_n)}</b></div>`` |
| `app.js:3556` #0 | `?? 0` | a | `trn()` null'da zaten '—' basıyor; `?? 0` DÜRÜST BİÇİMLEYİCİYİ devre dışı bırakıyor | `<b class="mono-num">${trn(amp, 2)} bps · n=${trn(kb.n_olculen ?? 0)}</b></div>` |
| `app.js:3590` #0 | `?? 0` | a | `trn()` null'da zaten '—' basıyor; `?? 0` DÜRÜST BİÇİMLEYİCİYİ devre dışı bırakıyor | `<b class="mono-num">${trn(gg.n ?? 0)} · ${trn(gg.n_olculemeyen ?? 0)}</b></div>` |
| `app.js:3590` #1 | `?? 0` | a | `trn()` null'da zaten '—' basıyor; `?? 0` DÜRÜST BİÇİMLEYİCİYİ devre dışı bırakıyor | `<b class="mono-num">${trn(gg.n ?? 0)} · ${trn(gg.n_olculemeyen ?? 0)}</b></div>` |
| `app.js:3604` #0 | `?? 0` | a | `trn()` null'da zaten '—' basıyor; `?? 0` DÜRÜST BİÇİMLEYİCİYİ devre dışı bırakıyor | `<span class="mono-num num">${trn(c.n ?? 0)}</span>` |
| `app.js:3626` #0 | `?? 0` | a | `trn()` null'da zaten '—' basıyor; `?? 0` DÜRÜST BİÇİMLEYİCİYİ devre dışı bırakıyor | `<b class="mono-num">ölçülebilen ${trn(gg.n_olculebilir ?? 0)} · <span class="mut">ölçülemeyen` |
| `app.js:3627` #0 | `?? 0` | a | `trn()` null'da zaten '—' basıyor; `?? 0` DÜRÜST BİÇİMLEYİCİYİ devre dışı bırakıyor | `${trn(gg.n_olculemeyen ?? 0)}</span> · defterde ${trn(gg.n ?? 0)}</b></div>` |
| `app.js:3627` #1 | `?? 0` | a | `trn()` null'da zaten '—' basıyor; `?? 0` DÜRÜST BİÇİMLEYİCİYİ devre dışı bırakıyor | `${trn(gg.n_olculemeyen ?? 0)}</span> · defterde ${trn(gg.n ?? 0)}</b></div>` |
| `app.js:3741` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `let det = m.status === "insufficient_cf" ? `cf ${m.n ?? 0}/30${m.avg_r != null ? " · ort " + m.avg_r + "R" : ""}`` |
| `app.js:3821` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow" style="margin-top:10px"><span>Kapı meta-kalibrasyonu</span><b>${gc2.extra_p ? `<span class="warn">e…` |
| `app.js:3853` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<span class="cap"><b>Isınma termometresi</b><br>sprint döngüsü ${wu.ticks ?? 0}/${wu.every ?? "—"} poll` |
| `app.js:3869` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `${(() => { const ac = ml.agent_calls \|\| {}; const used = ac.day ?? 0, cap = ac.rpd_limit ?? "—";` |
| `app.js:3930` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `const nr = sc2.n_real ?? 0;` |
| `app.js:3949` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | ``KARIŞIK KÖKEN: ${sc2.n_real ?? 0} gerçek + ${sc2.n_cf ?? 0} sim satır tek sayıya `` |
| `app.js:3949` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | ``KARIŞIK KÖKEN: ${sc2.n_real ?? 0} gerçek + ${sc2.n_cf ?? 0} sim satır tek sayıya `` |
| `app.js:3953` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<span class="mut">(sim ağırlıklı, ${sc2.n_real ?? 0} gerçek / ${sc2.n_cf ?? 0} sim)</span></b></div>`;` |
| `app.js:3953` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<span class="mut">(sim ağırlıklı, ${sc2.n_real ?? 0} gerçek / ${sc2.n_cf ?? 0} sim)</span></b></div>`;` |
| `app.js:4050` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<span class="mono-num num">n=${v.n ?? 0}</span>` |
| `app.js:4160` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `${(k.n ?? 0) < (es.n_min ?? 40) ? `<b class="warn">n=${k.n ?? 0} &lt; ${es.n_min} — hüküm OLCULEMEDI.</b>` : ""}</p>`;` |
| `app.js:4214` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `· izlenen pencere ${er.n_pencere ?? 0}</span></b></div>` |
| `app.js:4226` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `izlenen pencere sayısı ${er.n_pencere ?? 0}.</p>` |
| `app.js:4277` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `· n=${tv.canli_n ?? 0}</span>`` |
| `app.js:4316` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `(${dd.n_gun ?? 0} gün) — KÖTÜ olan okunur</span>`}</b></div>` |
| `app.js:4344` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<span class="mut">· ${h.n_pozisyon ?? 0} pozisyon · özsermaye ${money(h.ozsermaye)}</span></b></div>` |
| `app.js:4412` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<b class="${f.hepsi_acik ? "pos" : "warn"}">${f.n_acik ?? 0}/${f.n_kilit ?? 5} açık</b></div>` |
| `app.js:4420` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<p class="hint">${esc(v.n_trials_beyan \|\| "")} · defter ${(v.defter \|\| {}).n_kayit ?? 0} kayıt` |
| `app.js:4455` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<b class="${(s.iraksayan_kayit \|\| 0) > 0 ? "warn" : "mut"}">${s.golge_kayit_sayisi ?? 0} kayıt ·` |
| `app.js:4456` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `${s.iraksayan_kayit ?? 0} ıraksama` |
| `app.js:4457` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<span class="mut">· geçiş öncesi ${s.gecis_oncesi_kayit ?? 0} kayıt (v3 hükmü` |
| `app.js:4498` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `: `n=${pb.n ?? 0} — BANT ÖLÇÜLEMEDİ`}</b></div>` |
| `app.js:4513` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<b class="mut">${q.n_bekleyen ?? 0} bekleyen · ${q.n_olculen ?? 0} ölçülen ·` |
| `app.js:4513` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<b class="mut">${q.n_bekleyen ?? 0} bekleyen · ${q.n_olculen ?? 0} ölçülen ·` |
| `app.js:4518` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Kazananların acısı <span class="mut">(n=${(mp.kazananlar \|\| {}).n ?? 0})</span></span>` |
| `app.js:4520` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Kaybedenlerin acısı <span class="mut">(n=${(mp.kaybedenler \|\| {}).n ?? 0})</span></span>` |
| `app.js:4549` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<td class="num">${v.signal_n ?? 0} / ${v.would_arm_n ?? 0}</td>` |
| `app.js:4549` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<td class="num">${v.signal_n ?? 0} / ${v.would_arm_n ?? 0}</td>` |
| `app.js:4550` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<td class="num ${(sv.kumulatif_ayrisma \|\| {})[k] ? "warn" : "mut"}">${(sv.kumulatif_ayrisma \|\| {})[k] ?? 0}</td>` |
| `app.js:4596` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<b>${p.n_son_hafta ?? 0} öneri <span class="mut">· defterde toplam ${p.n ?? 0}</span></b></div>` |
| `app.js:4596` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<b>${p.n_son_hafta ?? 0} öneri <span class="mut">· defterde toplam ${p.n ?? 0}</span></b></div>` |
| `app.js:4599` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `${p.n_dusen ?? 0} düştü</b></div>` |
| `app.js:4623` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `: `<p class="hint"><b>Fiş kuyruğu:</b> ${fis.n_acik ?? 0} açık / ${fis.n ?? 0} toplam${` |
| `app.js:4623` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `: `<p class="hint"><b>Fiş kuyruğu:</b> ${fis.n_acik ?? 0} açık / ${fis.n ?? 0} toplam${` |
| `app.js:4786` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Açık pozisyon / kapanan işlem</span><b>${tk.pozisyon ?? 0} pozisyon ·` |
| `app.js:4787` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<span class="mut">${tk.kapanan ?? 0} kapandı · ${tk.gun ?? 0} gün eğri</span></b></div>` |
| `app.js:4787` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<span class="mut">${tk.kapanan ?? 0} kapandı · ${tk.gun ?? 0} gün eğri</span></b></div>` |
| `app.js:4818` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `${huni("doğan hipotez", dw.n_hypotheses ?? 0, "accent", "arama katmanının ürettiği her aday")}` |
| `app.js:4820` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `${huni("ship", dw.shipped ?? 0, "green", `canlıya çıkan sürüm (${SHIP_ST.join("/")})`)}` |
| `app.js:4821` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `${huni("ölçülen", dw.measured ?? 0, "violet", `arama tahmini (predicted_delta_search) ize düşmüş satır${dw.legacy_shi…` |
| `app.js:4837` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `${bf2.events_read ?? 0} olay · ${bf2.frames_seen ?? 0} bar${bf2.pending ? ` · <span class="warn">${bf2.pending} bekle…` |
| `app.js:4837` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `${bf2.events_read ?? 0} olay · ${bf2.frames_seen ?? 0} bar${bf2.pending ? ` · <span class="warn">${bf2.pending} bekle…` |
| `app.js:4839` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `? `${iq2.armed_plans} plan izleniyor · ${iq2.watched ?? 0} sembol`` |
| `app.js:4841` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Bugünkü karar / toplam</span><b>${dec2.today ?? 0} bugün · ${dec2.total ?? 0} toplam · ${dec2…` |
| `app.js:4841` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Bugünkü karar / toplam</span><b>${dec2.today ?? 0} bugün · ${dec2.total ?? 0} toplam · ${dec2…` |
| `app.js:4841` #2 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Bugünkü karar / toplam</span><b>${dec2.today ?? 0} bugün · ${dec2.total ?? 0} toplam · ${dec2…` |
| `app.js:4872` #0 | `|| 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<span class="cap"><b>8 adımlı sabır sayacı</b><br>EOD yayını gecikirse tazeleme bayrağı sıcak tutulur; ${pl.refetch_m…` |
| `app.js:4887` #0 | `|| 0` | a | ORAN payı/paydası — eksik alan 'sapma yok' oranı üretiyor | `const oran = Math.round(100 * (fu.fails \|\| 0) / fu.calls);` |
| `app.js:4895` #0 | `|| 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `return `<div class="srow"><span>FMP kota (bugün)</span><b class="${fu.blocked_at ? "warn" : ""}">${fu.calls} çağrı · …` |
| `app.js:4915` #0 | `|| 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<b class="${bad ? "warn" : "pos"}">${mx.compared} bar · ${mx.tickers} sembol · ${mx.mismatches \|\| 0} uyuşmazlık${` |
| `app.js:4927` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `ls.source ? ` · son kaynak ${esc(String(ls.source))} (n=${ls.n ?? 0})` : ""}${` |
| `app.js:4929` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Karşı-olgusal defter</span><b class="${lg.cf_cap && lg.cf_open > lg.cf_cap * 0.8 ? "warn" : "…` |
| `app.js:4929` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Karşı-olgusal defter</span><b class="${lg.cf_cap && lg.cf_open > lg.cf_cap * 0.8 ? "warn" : "…` |
| `app.js:4929` #2 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Karşı-olgusal defter</span><b class="${lg.cf_cap && lg.cf_open > lg.cf_cap * 0.8 ? "warn" : "…` |
| `app.js:4977` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `: k === "production" ? `${v.ok ?? 0}/${v.total ?? 0} mekanizma üretiyor${(v.starved \|\| []).length ? ` · AÇ: ${v.sta…` |
| `app.js:4977` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `: k === "production" ? `${v.ok ?? 0}/${v.total ?? 0} mekanizma üretiyor${(v.starved \|\| []).length ? ` · AÇ: ${v.sta…` |
| `app.js:4978` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `: k === "conservation" ? `${v.plans ?? 0} plan → ${v.traded ?? 0} işlem · ${v.no_fill ?? 0} dolmadı${_say(v.unexplain…` |
| `app.js:4978` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `: k === "conservation" ? `${v.plans ?? 0} plan → ${v.traded ?? 0} işlem · ${v.no_fill ?? 0} dolmadı${_say(v.unexplain…` |
| `app.js:4978` #2 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `: k === "conservation" ? `${v.plans ?? 0} plan → ${v.traded ?? 0} işlem · ${v.no_fill ?? 0} dolmadı${_say(v.unexplain…` |
| `app.js:4979` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `: k === "determinism" ? `${v.appended ?? 0} salt-ekleme defteri doğrulandı${v.shrunk ? ` · ${v.shrunk} defter KISALDI…` |
| `app.js:4980` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `: k === "coherence" ? `${v.ok ?? 0}/${v.total ?? 0} kalibrasyon taze${(v.stale \|\| []).length ? ` · BAYAT: ${v.stale…` |
| `app.js:4980` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `: k === "coherence" ? `${v.ok ?? 0}/${v.total ?? 0} kalibrasyon taze${(v.stale \|\| []).length ? ` · BAYAT: ${v.stale…` |
| `app.js:4981` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `: k === "monotonicity" ? `${v.tracked ?? 0} sayaç izleniyor${(v.regressions \|\| []).length ? ` · GERİLEME: ${v.regre…` |
| `app.js:5037` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<h3 class="t" style="margin-top:16px">Eleme muhasebesi · ${sv.n_stages ?? 0} aşama</h3>` |
| `app.js:5052` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `${cov.cells_applicable ? `<div class="srow" style="margin-top:12px"><span>Denetim kapsamı (${cov.components} bileşen …` |
| `app.js:5065` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Akan bar / abone sembol</span><b>${mkt.bars_seen ?? 0} bar · ${mkt.subscribed ?? 0} sembol</b…` |
| `app.js:5065` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Akan bar / abone sembol</span><b>${mkt.bars_seen ?? 0} bar · ${mkt.subscribed ?? 0} sembol</b…` |
| `app.js:5071` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Okuma / yazma / hata</span><b>${hs.reads ?? 0} okuma · ${hs.writes ?? 0} yazma${hs.fails ? ` …` |
| `app.js:5071` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Okuma / yazma / hata</span><b>${hs.reads ?? 0} okuma · ${hs.writes ?? 0} yazma${hs.fails ? ` …` |
| `app.js:5162` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `} · n ${sf.n ?? "—"}${sf.n_real != null ? ` (gerçek ${sf.n_real} · cf ${sf.n_cf ?? 0})` : ""}${` |
| `app.js:5170` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `an2.n_real != null ? ` (gerçek ${an2.n_real} · cf ${an2.n_cf ?? 0})` : ""}${` |
| `app.js:5176` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `terfi.n_live ?? 0}/${terfi.promote_min_n ?? "—"}${terfi.live_brier != null ? ` · Brier canlı ${trn(terfi.live_brier, …` |
| `app.js:5178` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `${kq ? `<div class="srow"><span>Kanıt dolgusu kuyruğu</span><b>${kq.dolgulanabilir_gun ?? 0} gün · ${` |
| `app.js:5179` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `kq.dolgulanabilir_satir ?? 0} satır dolgulanabilir · gece tavanı ${kq.gece_tavani ?? "—"}${` |
| `app.js:5185` #0 | `?? 0` | a | **ÖDENDİ (v207)** — sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `${ex ? `<div class="srow"><span>Eksen-2 üreteci</span><b>${ex.uretilen ?? 0} üretildi · ${` |
| `app.js:5186` #0 | `?? 0` | a | **ÖDENDİ (v207)** — sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `ex.kaydedilen ?? 0} kaydedildi · ${ex.bekleyen_toplam ?? 0} bekleyen · ${` |
| `app.js:5186` #1 | `?? 0` | a | **ÖDENDİ (v207)** — sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `ex.kaydedilen ?? 0} kaydedildi · ${ex.bekleyen_toplam ?? 0} bekleyen · ${` |
| `app.js:5187` #0 | `?? 0` | a | **ÖDENDİ (v207)** — sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `ex.otomatik_uygulanan ?? 0} otomatik uygulandı</b></div>` |
| `app.js:5394` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>İzlenen sembol / işlenen olay</span><b>${iq.watched ?? 0} sembol · ${iq.events_handled ?? 0} …` |
| `app.js:5394` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>İzlenen sembol / işlenen olay</span><b>${iq.watched ?? 0} sembol · ${iq.events_handled ?? 0} …` |
| `app.js:5395` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Yazılan ölçüm / tetik-geçişi</span><b>${iq.decisions_written ?? 0} ölçüm · ${dec.fired ?? 0} …` |
| `app.js:5395` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Yazılan ölçüm / tetik-geçişi</span><b>${iq.decisions_written ?? 0} ölçüm · ${dec.fired ?? 0} …` |
| `app.js:5395` #2 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Yazılan ölçüm / tetik-geçişi</span><b>${iq.decisions_written ?? 0} ölçüm · ${dec.fired ?? 0} …` |
| `app.js:5396` #0 | `|| 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `${(sk.session \|\| sk.halt \|\| sk.stale \|\| sk.no_bars) ? `<div class="srow"><span>Atlanan</span><b class="mut">sea…` |
| `app.js:5396` #1 | `|| 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `${(sk.session \|\| sk.halt \|\| sk.stale \|\| sk.no_bars) ? `<div class="srow"><span>Atlanan</span><b class="mut">sea…` |
| `app.js:5396` #2 | `|| 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `${(sk.session \|\| sk.halt \|\| sk.stale \|\| sk.no_bars) ? `<div class="srow"><span>Atlanan</span><b class="mut">sea…` |
| `app.js:5396` #3 | `|| 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `${(sk.session \|\| sk.halt \|\| sk.stale \|\| sk.no_bars) ? `<div class="srow"><span>Atlanan</span><b class="mut">sea…` |
| `app.js:5408` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<span class="chain mut">${esc((r.bar_t \|\| "").slice(11, 16))} UTC · ${r.admissible_bars ?? 0} bar${r.last_close != …` |
| `app.js:5411` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `const s2 = `<div class="card rise"><h2 class="t">Son intraday ölçümleri · ${dec.total ?? 0} toplam</h2>` |
| `app.js:5418` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Akan bar / abone</span><b>${mkt.bars_seen ?? 0} bar · ${mkt.subscribed ?? 0} sembol</b></div>` |
| `app.js:5418` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Akan bar / abone</span><b>${mkt.bars_seen ?? 0} bar · ${mkt.subscribed ?? 0} sembol</b></div>` |
| `app.js:5427` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Okunan olay / bar</span><b>${bf.events_read ?? 0} olay · ${bf.frames_seen ?? 0} bar</b></div>` |
| `app.js:5427` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Okunan olay / bar</span><b>${bf.events_read ?? 0} olay · ${bf.frames_seen ?? 0} bar</b></div>` |
| `app.js:5428` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Bekleyen (lag) / düşen bayat</span><b class="${bf.pending > 50 ? "warn" : ""}">${bf.pending ?…` |
| `app.js:5428` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Bekleyen (lag) / düşen bayat</span><b class="${bf.pending > 50 ? "warn" : ""}">${bf.pending ?…` |
| `app.js:5430` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow" style="margin-top:8px"><span>Redis sıcak katman</span><b class="${hsOk ? "pos" : (hs.ok === false ?…` |
| `app.js:5541` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Bugün · gönderilecekti / bloklandı</span><b>${sh.today_n ?? 0} satır · <span class="pos">${sh…` |
| `app.js:5541` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Bugün · gönderilecekti / bloklandı</span><b>${sh.today_n ?? 0} satır · <span class="pos">${sh…` |
| `app.js:5541` #2 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Bugün · gönderilecekti / bloklandı</span><b>${sh.today_n ?? 0} satır · <span class="pos">${sh…` |
| `app.js:5542` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Defter toplamı</span><b>${sh.total ?? 0} gölge kararı</b></div>` |
| `app.js:5551` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Eşleşen çift / eşleşmeyen</span><b>${ve.n_paired ?? 0} · <span class="mut">${ve.n_unpaired ??…` |
| `app.js:5551` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="srow"><span>Eşleşen çift / eşleşmeyen</span><b>${ve.n_paired ?? 0} · <span class="mut">${ve.n_unpaired ??…` |
| `app.js:5694` #0 | `|| 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<span class="mono-num mut">${s.n_cf \|\| 0}</span>` |
| `app.js:6285` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="card rise"><h2 class="t">Son işlemler · tek tek hesap (${d.n_trades ?? 0} toplam)</h2>` |
| `app.js:6329` #0 | `||0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<p class="hint" style="margin-top:8px">Kalibrasyon: ${L.calibration?.n\|\|0} sonuç · isabet ${L.calibration?.hit_rate…` |
| `app.js:6372` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `? `<span class="mut">— ayna hiç dolmadı (n=${slip.n ?? 0})</span>`` |
| `app.js:6413` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<br>SPY-veto adayı: <b>${veto.n ?? 0}/${veto.decision_n ?? "—"}</b> gözlem` |
| `app.js:6415` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `· SPY'ı geçen ${veto.beat ?? 0} · geçemeyen ${veto.lost ?? 0}` |
| `app.js:6415` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `· SPY'ı geçen ${veto.beat ?? 0} · geçemeyen ${veto.lost ?? 0}` |
| `app.js:6544` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `const n = v.n ?? 0, thr = v.threshold ?? "—", ready = !!v.ready;` |
| `app.js:6676` #0 | `|| 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `? `${esc(SPRINT_PHASE_TR[sp.phase] \|\| sp.phase \|\| "çalışıyor")}${sp.total ? ` · ${sp.progress \|\| 0}/${sp.total}…` |
| `app.js:6763` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `: `${L.outcomes_measured ?? 0} sonuç ölçüldü; terfi sonucun TUTMASINI ister`)),` |
| `app.js:6798` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `+ `${eksen2.uretilen ?? 0} öneri üretti (${eksen2.kaydedilen ?? 0} kaydedildi, ${eksen2.bekleyen_toplam ?? 0} bekleye…` |
| `app.js:6798` #1 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `+ `${eksen2.uretilen ?? 0} öneri üretti (${eksen2.kaydedilen ?? 0} kaydedildi, ${eksen2.bekleyen_toplam ?? 0} bekleye…` |
| `app.js:6798` #2 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `+ `${eksen2.uretilen ?? 0} öneri üretti (${eksen2.kaydedilen ?? 0} kaydedildi, ${eksen2.bekleyen_toplam ?? 0} bekleye…` |
| `app.js:6907` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<div class="r"><span>Çağrı sayısı</span><b>${sp.calls_this_month ?? 0}</b></div>` |
| `app.js:7326` #0 | `?? 0` | a | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | `<span class="tx3" style="font-weight:400">(${f.n_acik ?? 0}/${f.n_kilit ?? 5} açık)</span></h3>` |

**Kuyruktan iki not (sessiz kalmasın):**

- `app.js` gölge-kitap kartında (`tk.pozisyon`/`tk.kapanan`/`tk.gun`) üç (a) eşleşmesi var ve o
  kart bu turda KALEM 2 için ZATEN düzenlendi. Bilerek dokunulmadı: 30'luk bütçe kademe
  kriterine göre dağıtıldı ve bu üçü hiçbir kademeye girmiyor. Kaynakları (`trend_shadow.ozet`)
  alanları her zaman yazıyor, yani bugün ulaşılamaz dal — ama şema değişirse yalan söyler.
- `?? 0` dışında AYNI SINIFTAN iki komşu bulgu ölçüldü ve bu turun kapsamına girmedi:
  `f.n_kilit ?? 5` (iki yerde — **uydurma bir varsayılan**, `5` ölçülmemiş bir kilit sayısı) ve
  `es.n_min ?? 40`. İkisi de `?? 0` değil, o yüzden 211'in içinde değiller; adları burada dursun.

## 5. (b) SINIFI — 44 eşleşme, düzeltilmedi ve düzeltilmemeli

| dosya:satır | ifade | sınıf | gerekçe | bağlam |
|---|---|---|---|---|
| `app.js:727` #0 | `|| 0` | b | null dalı ZATEN üstte ayrı ele alınmış; `||` yalnız NaN'a karşı kalıyor | `const inboxN = today.inbox_count == null ? null : (Number(today.inbox_count) \|\| 0);` |
| `app.js:728` #0 | `|| 0` | b | null dalı ZATEN üstte ayrı ele alınmış; `||` yalnız NaN'a karşı kalıyor | `const planN = today.pending_count == null ? null : (Number(today.pending_count) \|\| 0);` |
| `app.js:953` #0 | `|| 0` | b | yalnız koşul kapısı; sıfır DOM'a hiç ulaşmıyor | `if ((t.pending_count \|\| 0) > 0 && t.autonomy_level >= 1) acts.push([`${t.pending_count} onay bekliyor`, "portfoy#on…` |
| `app.js:1477` #0 | `|| 0` | b | null dalı ZATEN üstte ayrı ele alınmış; `||` yalnız NaN'a karşı kalıyor | `const onayN = t.inbox_count == null ? null : (Number(t.inbox_count) \|\| 0);` |
| `app.js:1549` #0 | `|| 0` | b | yalnız koşul kapısı; sıfır DOM'a hiç ulaşmıyor | `const n = m.n \|\| 0, taze = m.stale_n == null ? null : n - m.stale_n;` |
| `app.js:2110` #0 | `|| 0` | b | yerel biriktirici tohumu — anahtar yoksa 'o kovada 0 satır' ÖLÇÜLMÜŞ gerçektir | `const vc = {}; plans.forEach(p => vc[p.gate_verdict] = (vc[p.gate_verdict] \|\| 0) + 1);` |
| `app.js:2114` #0 | `|| 0` | b | yerel biriktirici tohumu — anahtar yoksa 'o kovada 0 satır' ÖLÇÜLMÜŞ gerçektir | `rc[key] = (rc[key] \|\| 0) + 1;` |
| `app.js:2118` #0 | `|| 0` | b | yerel biriktirici tohumu — anahtar yoksa 'o kovada 0 satır' ÖLÇÜLMÜŞ gerçektir | `(d.candidates \|\| []).forEach(c => bySkill[c.source_skill] = (bySkill[c.source_skill] \|\| 0) + 1);` |
| `app.js:2174` #0 | `|| 0` | b | yerel biriktirici tohumu — anahtar yoksa 'o kovada 0 satır' ÖLÇÜLMÜŞ gerçektir | `sPlan.forEach(p => svc[p.gate_verdict] = (svc[p.gate_verdict] \|\| 0) + 1);` |
| `app.js:2197` #0 | `?? 0` | b | yerel biriktirici tohumu — anahtar yoksa 'o kovada 0 satır' ÖLÇÜLMÜŞ gerçektir | `h("Kapıdan geçen · GO", svc.GO ?? 0, ""),` |
| `app.js:2198` #0 | `?? 0` | b | yerel biriktirici tohumu — anahtar yoksa 'o kovada 0 satır' ÖLÇÜLMÜŞ gerçektir | `h("İncelemeye düşen", svc.REVIEW ?? 0, ""),` |
| `app.js:2199` #0 | `?? 0` | b | yerel biriktirici tohumu — anahtar yoksa 'o kovada 0 satır' ÖLÇÜLMÜŞ gerçektir | `h("Elenen · NO_GO", svc.NO_GO ?? 0, "warn"),` |
| `app.js:2225` #0 | `|| 0` | b | yerel biriktirici tohumu — anahtar yoksa 'o kovada 0 satır' ÖLÇÜLMÜŞ gerçektir | `<span class="ok">GO</span> ....... ${vc.GO \|\| 0}` |
| `app.js:2226` #0 | `|| 0` | b | yerel biriktirici tohumu — anahtar yoksa 'o kovada 0 satır' ÖLÇÜLMÜŞ gerçektir | `<span class="w">REVIEW</span> ... ${vc.REVIEW \|\| 0}` |
| `app.js:2227` #0 | `|| 0` | b | yerel biriktirici tohumu — anahtar yoksa 'o kovada 0 satır' ÖLÇÜLMÜŞ gerçektir | `<span class="no">NO_GO</span> .... ${vc.NO_GO \|\| 0}</div></div>` |
| `app.js:2499` #0 | `?? 0` | b | yalnız koşul kapısı; sıfır DOM'a hiç ulaşmıyor | `const kalan = (s.n_sapma ?? 0) - (s.sapmalar \|\| []).length;` |
| `app.js:3033` #0 | `|| 0` | b | yalnız koşul kapısı; sıfır DOM'a hiç ulaşmıyor | `["planlı", r => (r.plans_n \|\| 0) > 0],` |
| `app.js:3243` #0 | `|| 0` | b | aritmetik/geometri (payda · çubuk genişliği · SVG koordinatı) — bir okuma değil | `const mx = Math.max(a \|\| 0, b \|\| 0) \|\| 1;` |
| `app.js:3243` #1 | `|| 0` | b | aritmetik/geometri (payda · çubuk genişliği · SVG koordinatı) — bir okuma değil | `const mx = Math.max(a \|\| 0, b \|\| 0) \|\| 1;` |
| `app.js:3247` #0 | `|| 0` | b | aritmetik/geometri (payda · çubuk genişliği · SVG koordinatı) — bir okuma değil | `<span class="tb">iç&nbsp;HWM <span class="bar"><i style="width:${(100 * (a \|\| 0) / mx).toFixed(1)}%"></i></span><b …` |
| `app.js:3248` #0 | `|| 0` | b | aritmetik/geometri (payda · çubuk genişliği · SVG koordinatı) — bir okuma değil | `<span class="tb">PATCH&nbsp;&nbsp; <span class="bar"><i style="width:${(100 * (b \|\| 0) / mx).toFixed(1)}%;backgroun…` |
| `app.js:3544` #0 | `|| 0` | b | yalnız koşul kapısı; sıfır DOM'a hiç ulaşmıyor | `${(yr.ampirik_n \|\| 0) > 0 ? `<div class="srow"><span>Dosyadaki ampirik değer</span>` |
| `app.js:3785` #0 | `|| 0` | b | aritmetik/geometri (payda · çubuk genişliği · SVG koordinatı) — bir okuma değil | `const thermoPct = wu.every ? Math.round(100 * (wu.ticks \|\| 0) / wu.every) : 0;` |
| `app.js:3852` #0 | `|| 0` | b | aritmetik/geometri (payda · çubuk genişliği · SVG koordinatı) — bir okuma değil | `<span class="tube"><i style="--fill:${(Number(thermoPct) \|\| 0) / 100}"></i></span>` |
| `app.js:4047` #0 | `|| 0` | b | sıralama karşılaştırıcısı — sonuç ekrana çıkmıyor | `.sort((a, b) => (b[1].n \|\| 0) - (a[1].n \|\| 0))` |
| `app.js:4047` #1 | `|| 0` | b | sıralama karşılaştırıcısı — sonuç ekrana çıkmıyor | `.sort((a, b) => (b[1].n \|\| 0) - (a[1].n \|\| 0))` |
| `app.js:4052` #0 | `?? 0` | b | kapı, ama başarısızlık yönü SUSTURMAYA doğru (iddia üretmiyor) | `<span class="chain">kazanç ${v.win_rate != null ? pctf(v.win_rate, 1) : "—"}${(v.n ?? 0) < 20` |
| `app.js:4160` #0 | `?? 0` | b | kapı, ama başarısızlık yönü SUSTURMAYA doğru (iddia üretmiyor) | `${(k.n ?? 0) < (es.n_min ?? 40) ? `<b class="warn">n=${k.n ?? 0} &lt; ${es.n_min} — hüküm OLCULEMEDI.</b>` : ""}</p>`;` |
| `app.js:4444` #0 | `|| 0` | b | kapı, ama başarısızlık yönü SUSTURMAYA doğru (iddia üretmiyor) | `<b class="${(s.para_payi_v3 \|\| 0) >= 0.999 ? "pos" : "neg"}">eski ${pctf(pay1.para, 1)}` |
| `app.js:4455` #0 | `|| 0` | b | yalnız koşul kapısı; sıfır DOM'a hiç ulaşmıyor | `<b class="${(s.iraksayan_kayit \|\| 0) > 0 ? "warn" : "mut"}">${s.golge_kayit_sayisi ?? 0} kayıt ·` |
| `app.js:4691` #0 | `|| 0` | b | yalnız koşul kapısı; sıfır DOM'a hiç ulaşmıyor | `<b class="${(hr.oran \|\| 0) >= 1 ? "neg" : "mut"}">${hr.en_cok_sorgu ?? "—"} / ${hr.limit ?? "—"} sorgu` |
| `app.js:4811` #0 | `|| 0` | b | yerel biriktirici tohumu — anahtar yoksa 'o kovada 0 satır' ÖLÇÜLMÜŞ gerçektir | `const topla = ks => ks.reduce((s, k) => s + (byst[k] \|\| 0), 0);` |
| `app.js:4812` #0 | `|| 0` | b | aritmetik/geometri (payda · çubuk genişliği · SVG koordinatı) — bir okuma değil | `const maxN = Math.max(1, dw.n_hypotheses \|\| 0);` |
| `app.js:4913` #0 | `|| 0` | b | yalnız koşul kapısı; sıfır DOM'a hiç ulaşmıyor | `const bad = (mx.mismatches \|\| 0) > 0;` |
| `app.js:4951` #0 | `|| 0` | b | yalnız koşul kapısı; sıfır DOM'a hiç ulaşmıyor | `: v.ok !== false && !(v.regressions \|\| []).length && !(v.shrunk \|\| 0);` |
| `app.js:5705` #0 | `|| 0` | b | aritmetik/geometri (payda · çubuk genişliği · SVG koordinatı) — bir okuma değil | `const dots = (pts \|\| []).map(p => `<circle cx="${sx(p.predicted \|\| 0)}" cy="${sy(p.realized \|\| 0)}" r="5" fill=…` |
| `app.js:5705` #1 | `|| 0` | b | aritmetik/geometri (payda · çubuk genişliği · SVG koordinatı) — bir okuma değil | `const dots = (pts \|\| []).map(p => `<circle cx="${sx(p.predicted \|\| 0)}" cy="${sy(p.realized \|\| 0)}" r="5" fill=…` |
| `app.js:5971` #0 | `|| 0` | b | yerel biriktirici tohumu — anahtar yoksa 'o kovada 0 satır' ÖLÇÜLMÜŞ gerçektir | `${pdRow("GO · REVIEW · NO_GO", `${vc.GO \|\| 0} · ${vc.REVIEW \|\| 0} · ${vc.NO_GO \|\| 0}`)}` |
| `app.js:5971` #1 | `|| 0` | b | yerel biriktirici tohumu — anahtar yoksa 'o kovada 0 satır' ÖLÇÜLMÜŞ gerçektir | `${pdRow("GO · REVIEW · NO_GO", `${vc.GO \|\| 0} · ${vc.REVIEW \|\| 0} · ${vc.NO_GO \|\| 0}`)}` |
| `app.js:5971` #2 | `|| 0` | b | yerel biriktirici tohumu — anahtar yoksa 'o kovada 0 satır' ÖLÇÜLMÜŞ gerçektir | `${pdRow("GO · REVIEW · NO_GO", `${vc.GO \|\| 0} · ${vc.REVIEW \|\| 0} · ${vc.NO_GO \|\| 0}`)}` |
| `app.js:6373` #0 | `?? 0` | b | kapı, ama başarısızlık yönü SUSTURMAYA doğru (iddia üretmiyor) | `: `<b class="${Math.abs(slip.measured_bps) > (slip.assumed_bps ?? 0) ? "warn" : "pos"}">${esc(String(slip.measured_bp…` |
| `app.js:6567` #0 | `|| 0` | b | aritmetik/geometri (payda · çubuk genişliği · SVG koordinatı) — bir okuma değil | `const total = sp.total \|\| 0, prog = sp.progress \|\| 0, pct = total ? Math.min(100, Math.round(prog / total * 100))…` |
| `app.js:6567` #1 | `|| 0` | b | aritmetik/geometri (payda · çubuk genişliği · SVG koordinatı) — bir okuma değil | `const total = sp.total \|\| 0, prog = sp.progress \|\| 0, pct = total ? Math.min(100, Math.round(prog / total * 100))…` |
| `app.js:6750` #0 | `|| 0` | b | yerel biriktirici tohumu — anahtar yoksa 'o kovada 0 satır' ÖLÇÜLMÜŞ gerçektir | `const nHyp = Object.values(sc).reduce((a, b) => a + (Number(b) \|\| 0), 0);` |

**(b) içinde ayrıca kaydedilen bir sınır (ÖLÇÜLDÜ, bu triyajın kapsamında DEĞİL):**
kalibrasyon saçılımının nokta koordinatları (`sx(p.predicted || 0)` / `sy(p.realized || 0)`)
bu ayırıcıya göre (b)'dir — bir sayı OKUMASI basmıyor, bir koordinat hesaplıyor. Ama ölçülmemiş
bir tahmin/sonuç çifti için grafiğe **başlangıç noktasına oturan gerçek görünümlü bir nokta**
çizilir. Bu ayrı bir kusur sınıfıdır (uydurma VERİ NOKTASI, uydurma SAYI değil) ve bu turda
düzeltilmedi — sessizce (b)'ye gömülmesin diye adıyla yazıldı.

## 6. ÖLÇÜLEMEYENLER

| # | Ölçülemeyen | Neden |
|---|---|---|
| Ö1 | Düzeltmelerin ÇALIŞAN DOM'daki etkisi | Uygulamayı yerelde YÜKLEMEK yasak: `app.js` `localStorage.meridian_api`yi okur ve yükleme canlı A1 ucuna gidebilir. Doğrulama bu yüzden YAPISALdır — şablon dilimleri Node'da fikstürle koşturulur (`tests/test_acil_dogruluk_v196.py`), artı `node --check` ve kapsam testleri. |
| Ö2 | Kuyruktaki 137 (a)'nın canlıda KAÇININ fiilen `undefined` gördüğü | Canlı state okunmadı (canlı worker koşuyor olabilir; state'e dokunulmadı). Sınıflandırma KOD YOLU üzerinden yapıldı, gözlenen sıklık üzerinden değil — yani kuyruk bir risk listesidir, bir arıza listesi değil. |

## 7. DALGA-2 EKİ — 15 yeni (b), v-dalga2 (2026-08-09)

Dalga-2'nin (01ba684 + ff55a18) `app.js`e eklediği 15 `?? 0` guard'ının satır-satır sınıflandırması.
Sınıf sütunu **`b-d2`** = "(b), dalga-2 turu" — 2026-08-06 sayımının DONMUŞ tablolarına (§4/§5)
karışmasın diye AYRI imle yazıldı; bu 15 satır o sayımın parçası değildir. Hepsi süpürücü/iptal
ailesinden; yokluk anlamı "uç bu alanı hiç göndermedi" DEĞİL, "o kovada ölçülmüş sıfır"dır —
üretici bölümlemeyi HER olayda basar ve boş kovayı KAYNAKTA 0'a düşürür (YASA-6, uçtan doğrulandı).

| dosya:satır | ifade | sınıf | gerekçe | üretici (YASA-6) |
|---|---|---|---|---|
| `app.js:1179` #0 | `?? 0` | b-d2 | sınıf-dökümü olayı: iptal edilen giriş SAYACI; olay ancak süpürme koşunca doğar (sayım yapılmıştır) | `alpaca.py:491` `cancelled=len(...)` |
| `app.js:1180` #0 | `?? 0` | b-d2 | bölümleme kovası `giris` — boş kova = ölçülmüş 0 | `alpaca.py:488` `giris=int(...)` |
| `app.js:1180` #1 | `?? 0` | b-d2 | bölümleme kovası `koruma` — boş kova = ölçülmüş 0 | `alpaca.py:489` `koruma=int(...)` |
| `app.js:1180` #2 | `?? 0` | b-d2 | bölümleme kovası `yabanci` — boş kova = ölçülmüş 0 | `alpaca.py:490` `yabanci=int(...)` |
| `app.js:1182` #0 | `?? 0` | b-d2 | cancel-open (pano tuşu) olayı: iptal SAYACI | `api.py:2045` `cancelled=len(...)` |
| `app.js:1182` #1 | `?? 0` | b-d2 | cancel-open olayı: korunan SAYACI | `api.py:2046` `kept=len(...)` |
| `app.js:1184` #0 | `?? 0` | b-d2 | bayat-kadans süpürücüsü: iptal SAYACI | `loop.py:280` `cancelled=len(...)` |
| `app.js:1185` #0 | `?? 0` | b-d2 | bayat-kadans: korunan SAYACI | `loop.py:280` `kept=len(...)` |
| `app.js:1185` #1 | `?? 0` | b-d2 | bayat-kadans: yabancı SAYACI (operatör emri, dokunulmadı) | `loop.py:281` `foreign=len(...)` |
| `app.js:1186` #0 | `?? 0` | b-d2 | HALT/breaker süpürücüsü: iptal SAYACI | `loop.py:280` `cancelled=len(...)` |
| `app.js:1187` #0 | `?? 0` | b-d2 | HALT/breaker: korunan SAYACI | `loop.py:280` `kept=len(...)` |
| `app.js:1187` #1 | `?? 0` | b-d2 | HALT/breaker: yabancı SAYACI | `loop.py:281` `foreign=len(...)` |
| `app.js:3439` #0 | `?? 0` | b-d2 | `opCancelOpen` sınıf dökümü `giris` — TAZE API yanıtı, `siniflar` hep başlatılı; v225:190 ZORUNLU | `alpaca.py:523,536` |
| `app.js:3439` #1 | `?? 0` | b-d2 | `opCancelOpen` sınıf dökümü `koruma` — a.g. | `alpaca.py:523,536` |
| `app.js:3439` #2 | `?? 0` | b-d2 | `opCancelOpen` sınıf dökümü `yabanci` — a.g. | `alpaca.py:523,536` |

**Karşı-kanıt / `daily_cycle` ayrımı (kayda geçer, sessiz kalmasın):** §4 kuyruğundaki
`daily_cycle`/`hermes_search_done` olay çevirileri (`app.js:1014`/`1020`) YAPISAL olarak aynı görünür
ama (a) sınıfındadır. Fark üreticidedir: bu 15 süpürücü guard'ı TEK bir bölümleme fonksiyonunun
ürünüdür (olayın var olması = sayımın yapılmış olması) ve kovalar + toplam HER SEFERİNDE birlikte
basılır; `daily_cycle` alanları ise aşama-koşulludur. Sınır yine de dürüstçe dursun: bu 15 için tek
gözlemlenmemiş `undefined` yolu v220 ÖNCESİ eski `obs.log` olaylarının replay'idir — canlı akış değil.

**Landing (kapsam dışı, `app.js` sayımına GİRMEZ):** `landing.js:36` `(d.score || 0)` bir RENK
kapısıdır (DOM'a sayı basmaz) → (b); dalga-2'de eski `ölçülen` satırından yeni `olculenSatiri()`
fonksiyonuna TAŞINDI, yeni bir guard değil (§1'deki eski `landing.js:66` kaydının yeni yeri).
v196 tavanı yalnız `app.js` ölçer; landing bu teste girmez, sayım değişmez.


---

## 8. v239 EKİ — 2 yeni **(a)**, EKLENDİĞİ TURDA ÖDENDİ (2026-08-13)

v239 `app.js`e sekizinci bütünlük deseninin (`divergence` / değer-eşitliği) özet satırını ekledi
ve çırçır **192 → 194**'e ÇIKTI (otoriter suite `test_nullsifir_sayisi_CIRCIRI_asmiyor` ile düştü).
Sınıf sütunu **`a-v239`** — §4/§5'in DONMUŞ tablolarına karışmasın diye ayrı imle yazıldı
(§7'nin `b-d2` emsali); bu iki satır 2026-08-06 sayımının parçası DEĞİLDİR.

| dosya:satır | ifade | sınıf | gerekçe | hüküm |
|---|---|---|---|---|
| `app.js:6089` #0 | `?? 0` (`v.esit`) | a-v239 | sunucu alanı doğrudan DOM'a — yokluk 'ölçülmedi', basılan 0 'ölçtük, sıfır çıktı' der | **ÖDENDİ (v239 düzeltme turu)** → `trn(v.esit)` |
| `app.js:6089` #1 | `?? 0` (`v.total`) | a-v239 | a.g.; ayrıca `total` = `len(EQUIVALENT_TRUTHS)` olduğu için **hiçbir zaman 0 olamaz** — basılan 0 imkânsız bir olguyu iddia eder | **ÖDENDİ (v239 düzeltme turu)** → `trn(v.total)` |

**KÖK: DESEN DEĞİL KUSUR KOPYALANDI.** Yeni satır iki kardeşinden (`production` → `app.js:4977`,
`coherence` → `app.js:4980`) biçim aldı; ama tam o iki kardeş §4 kuyruğunda **(a)** olarak
işaretlidir ve aynı gerekçeyle kaldırılmayı bekler. Yani "mevcut koda benzet" kuralı, kaldırma
kuyruğundaki bir kusuru ÇOĞALTTI. Çırçırın yakaladığı şey buydu ve doğru cevap tavanı yükseltmek
değil, satırı ekleyen turun borcu ödemesidir.

**NEDEN İKİ YÖNLÜ UYDURMA:** `"0/0 olgu eşit"` ölçülmemiş bir turu hem "kıyas yapıldı" hem
"hiçbir olgu eşit değil" diye okutur. Üstelik bu satıra gelinebilmesi için `_patOlculemedi(v)`
dalının ZATEN elenmiş olması gerekir — yani dosyanın kendi dürüst mekanizması (`ÖLÇÜLEMEDİ`
rozeti + `_patOlcumYok`) devredeyken, `?? 0` onun arkasından ikinci ve sessiz bir hüküm veriyordu.

**DÜZELTME BİÇİMİ — SİLME, EKLEME DEĞİL** (§0'ın "çoğu bir EKLEME değil bir SİLMEdir" kaydı):
guard kaldırıldı ve değer jenerik dürüst biçimleyiciye (`trn()`, `app.js:275` — null/NaN'da `—`)
bağlandı. Üretici tarafı ayrıca doğrulandı (YASA-6): `watchdog.divergence_report()` `esit`+`total`
alanlarını HER dönüşte basar ve `INTEGRITY_SKELETON` (`watchdog.py:1297`) yedeği de ikisini taşır —
yani guard zaten ölü savunmaydı; tek işlevi, gerçekleşmesi hâlinde YALAN söylemekti.

**SAYIM SONRASI:** `app.js` = **192** eşleşme (v239 öncesiyle aynı) — §1 tablosundaki
"kalan eşleşme" satırı DEĞİŞMEZ ve `NULLSIFIR_TAVAN` 192'de KALIR. Kuyrukta kalan (a): **133**
(v239 iki tane ekleyip aynı turda ikisini de ödediği için kuyruk büyümedi).

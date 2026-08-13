# ARAŞTIRMA — SLİPAJI REPLAY VARSAYIMINA YAKLAŞTIRMA (PF maksimizasyonu)

**Tarih:** 2026-08-13 · **Rol:** araştırma/tasarım ajanı (kod YAZILMADI, git YOK, canlıya SALT-OKUMA)
**Operatör talimatı:** "slipajı nasıl replay varsayımına yaklaştırabiliriz onu araştır, PF değerini
maksimize etmemiz gerekiyor."
**Girdi ölçüm:** EDG-2026-037 (`research/olcumler/edg037_tca_2026-08-13/sonuc.json`)
**Bu belge bir HÜKÜM DEĞİLDİR.** Kart açmaz, eşik değiştirmez, kod önermez — ölçüm + tasarım
seçenekleri + kart taslakları üretir. Hükmü Rol-1 işler.

---

## 0. YÖNETİCİ ÖZETİ — altı cümle

1. **Emir tipi teşhis edildi: giriş bacağı `type=limit` (bracket, `tif=day`, `extended_hours=false`),
   stop DEĞİL.** Yani girişte "stop tetiklenince market'e dönüp fiyat kovalama" mekaniği YOKTUR;
   kovalama riski **çıkış** bacağındadır (koruma OCO'sunun stop bacağı `type=stop` = tetiklenince
   market) ve orası **henüz hiç ölçülmemiştir** (n=0).
2. **Limit tavanı fiilen YOK.** Canlı `goal.yaml execution_v2` = `limit_atr_mult: 100.0` /
   `limit_pct_cap: 0.04`; dört dolumun dördünde limit tetiğin **tam %4 üstünde** ve dolumlar limitin
   **213–406 bps ALTINDA** gerçekleşti (`fill_vs_limit_bps`). Tavan hiçbir emirde bağlamadı.
3. **`gap_at_submit` bir gap ölçmüyor — totoloji.** 7/7 kurulumda `entry_trigger = sinyal barı
   kapanışı` (`strategy.py:509,571,623,678,784,862,989`) ve referans fiyat da aynı kapanış
   (`loop.py:1802`) → `rp >= t` daima doğru. Canlı defter: 9/9 `true`. Sonuç: **`stop_limit` dalı
   canlıda ÖLÜ KOD**, `gap_behavior: cancel` bir filtre değil **kapatma düğmesidir**.
4. **Slipajın kaynağı ayrıştırıldı:** likidite/emir-boyutu **elendi** (katılım ~1e-5…8e-4 → etki
   ≤0,8 bps), stop-mekaniği **elendi** (emir limit), **açılış ilk dakikasının fiyat sapması KALDI.**
   Dört dolumun dördü de konsolide **13:30–13:31 dakika barının fiyat bandının İÇİNDE** (damgaları
   13:32–13:33 olmasına rağmen); o bandın genişliği 45 / 98 / 100 / **184** bps ve BKNG–AMGN farkını
   (134 vs 15 bps) açıklayan değişken **tam olarak bu banttır**.
5. **ÖLÇÜT KRİZİ (en önemli bulgu):** EDG-037'nin paydası `resmi_acilis` = Alpaca **IEX** günlük bar
   açılışıdır; konsolide (SIP) 13:30 açılışına göre **−36,8 / −27,7 / 0,0 / +16,2 bps** sapıyor —
   yani **ölçütün hatası, ölçülen büyüklükle aynı mertebede.** Konsolide açılışla yeniden hesapta
   medyan 35,4 → **29,0 bps**, "4/4 aleyhte" → **3/4** (NUE **−20,7 bps**, yani LEHTE), ilk-dakika
   orta-noktasına göre medyan **21,0** ve **2/4**.
6. **Dürüstlük kalemi (kaçan işlem):** limit tavanının kaçırdığı işlemler 2026-08-03 E1 grid'inde
   **sistematik KAZANANDI** (a kolu: 38 kaçan, ort +0,2265R, %60,5 pozitif; net **−7.202$**) — ama o
   ölçüm **eski paketle** ve **replay'in tek-atış açılış modeliyle** yapıldı. Bugünkü 885-işlemlik
   defterde aynı kesim **ters işaretli** çıkıyor (100 bps tavan: 152 işlem düşer, düşenlerin net
   P&L'i **−1.613$**, defter 20.685$ → 22.298$, PF 1,1119 → **1,1451**). **İki ölçüm ÇELİŞİYOR ve
   çelişkinin kaynağı bilinen bir model kusurudur** (§C.1'de).

---

## 1. KÜNYE — ne ölçüldü, neyle, nereden

| Kanıt | Kaynak | Nasıl |
|---|---|---|
| Emir tipi/TIF/`extended_hours`/zaman damgaları | Alpaca `/v2/orders` (n=8, `nested=true`, 2026-08-04..09) | canlı A1, SALT-OKUMA |
| E2 icra defteri (10 satır: 4 ayna + 6 iç) | `state/entry_execution.jsonl` | canlı A1, SALT-OKUMA |
| Ayna emir yaşam döngüsü (31 emir) | `state/mirror_orders.json` | canlı A1, SALT-OKUMA |
| Açık pozisyon + açık emir | Alpaca `/v2/positions`, `/v2/orders?status=open` | canlı A1, SALT-OKUMA |
| **Konsolide dakika barları** 2026-08-06 | Massive `/v2/aggs/.../1/minute` (NUE/EMR/BKNG/AMGN) | dış veri |
| **15-dk pencere dağılımı** (n=401 sembol-seans, 2026-02-02..08-06) | Massive `/v2/aggs/.../15/minute` | dış veri |
| Replay defteri (885 işlem) + günlük barlar | `edg032_final_paket_2026-08-12/islemler_cmb.json` + `state/bars/*.csv` | yerel artefakt |
| E1 icra grid'i (7 kol) | `research/olcumler/e1_grid_2026-08-03/sonuc_e1.json` | yerel artefakt |
| PF duyarlılık eğrisi | EDG-037 `d_fark_ve_pf_etkisi.duyarlilik_egrisi_pf` | yerel artefakt |

**Kod referansları (okundu, dokunulmadı):** `meridian/broker.py:94-211,447-561,657-704` ·
`meridian/adapters/alpaca.py:322-375,809-844,979-1042` · `meridian/loop.py:690-770,1362-1400,
1798-1810,2228-2310` · `meridian/backtest.py:216-248` · `meridian/scheduler.py:254-284` ·
`state/goal.yaml:55-95`.

---

## [A] MEVCUT İCRA YOLU — varsayım yok, koddan + canlıdan

### A.1 Emir yapısı (Alpaca kaydından DOĞRULANDI)

Motor girişi **tek bir bracket BUY** olarak gönderiyor (`alpaca.submit_bracket`, gövde
`alpaca.py:342-354`):

```
POST /v2/orders
  side=buy · order_class=bracket · time_in_force=<entry_law.tif>
  type = "limit"      (gap dalı → limit_price = entry_limit)          ← CANLIDA HEP BU
       | "stop_limit" (normal dal → stop_price=tetik, limit_price=entry_limit)
       | "stop"       (geriye-dönük yol; yeni çağıran girmez)
  take_profit = {limit_price: profit_target}     ← koruma bacağı 1 (LİMİT)
  stop_loss   = {stop_price:  stop}              ← koruma bacağı 2 (STOP = tetiklenince MARKET)
  client_order_id = plan_id                      ← mutabakat birleştirme anahtarı
```

**`extended_hours` alanı gövdeye HİÇ konmuyor** (tüm depoda tek eşleşme yok) → Alpaca varsayılanı
`false`; canlı kayıt bunu teyit ediyor (`"extended_hours": false`, 8/8 emir). Yani emir **yalnız
09:30–16:00 ET normal seansta** icra edilebilir.

**Ölçülen dört giriş emri (Alpaca ham kaydı):**

| plan | type | order_class | tif | ext_hrs | limit | created_at | submitted_at | **filled_at** | filled_avg |
|---|---|---|---|---|---|---|---|---|---|
| P-2026-08-05-NUE | limit | bracket | **day** | false | 285,55 | 08-05 22:10:00Z | **08-06 08:00:27Z** | **08-06 13:33:07,913Z** | 273,9512 |
| P-2026-08-05-EMR | limit | bracket | **day** | false | 168,65 | 08-05 22:10:00Z | **08-06 08:00:26Z** | **08-06 13:32:20,944Z** | 164,76 |
| P-2026-08-05-BKNG | limit | bracket | **day** | false | 215,31 | 08-05 22:10:01Z | **08-06 08:00:27Z** | **08-06 13:32:06,873Z** | 210,24 |
| P-2026-08-05-AMGN-momentum_burst | limit | bracket | **day** | false | 424,04 | 08-06 10:32:46Z | 08-06 10:32:46Z | **08-06 13:32:28,154Z** | 415,0073 |

**Dördü de `type=limit`.** `stop` ya da `stop_limit` gönderilmiş TEK emir yok. → **Giriş tarafında
"stop tetiklendi, market'e döndü, fiyat kovalandı" mekaniği YOKTUR.** (Operatörün [B](ii) hipotezi
girişte elendi; çıkışta geçerli — §B.4.)

### A.2 Emirler ne zaman gidiyor, neden açılışta doluyor

Zincir, ölçülen damgalarla:

```
20:00Z  seans kapanır
20:16Z  scheduler._leg_ready açılır (SAME_EVENING_DELAY_MIN=16, scheduler.py:254)
22:10Z  loop.daily_cycle → alpaca.submit_plan → POST /v2/orders   (created_at)
        ⤷ Alpaca emri KUYRUĞA alır (piyasa kapalı)
08:00Z  Alpaca emri piyasaya BIRAKIR (submitted_at = 08:00:2x, üçü de aynı saniye)
        ⤷ ama extended_hours=false → pre-market'te icra EDİLEMEZ
13:30Z  açılış — emir artık icra edilebilir
13:32–13:33Z  DOLDU (dördü de, 14–61 saniye arayla, seri kuyruk deseni)
```

**"Neden açılışta doluyor" sorusunun cevabı üç kelepçenin bileşimidir:** (i) emir seans dışında
üretiliyor, (ii) `extended_hours=false` onu açılışa kadar bekletiyor, (iii) limit tavanı 400 bps
olduğu için emir açılışta **marketable** (limit ≫ piyasa) → ilk fırsatta doluyor.
AMGN farklı bir kapıdan geldi (E2 defterinde `kaynak: "pano"`, gönderim 10:32Z — yani pre-market'te,
diğer üçünden 12 saat sonra) ama **aynı üç kelepçeye** takıldığı için o da 13:32'de doldu.
**Kanıt değeri:** gönderim saatini 22:10Z'den 10:32Z'ye kaydırmak dolum anını DEĞİŞTİRMEDİ →
dolum anını belirleyen şey gönderim saati değil, **`extended_hours=false` + marketable `limit`
bileşimidir.**

### A.3 TIF — ölçülen değer `day`, yürürlükteki yasa `gtc`

E2 defteri dört emir için de **`tif: day`, `law: E1-v1`** yazıyor. Bu 2026-08-07'deki E1-v2
düzeltmesinden ÖNCEsidir; ölçülen sonuç da kayıtta: dört bracket'ın **take-profit bacağı 20:00–20:02Z
`expired`**, kardeş **stop bacağı `canceled`** — dört pozisyon o gece çıplak kaldı. Bugünkü yasa
`ENTRY_TIF_ALLOWED = ("gtc",)` ile bunu yapısal olarak yasaklıyor (`broker.py:96-102`), ve canlı
koruma OCO'ları bugün `tif=gtc` (doğrulandı, §A.5).
**Bu bir slipaj kalemi değil, ölçüm penceresini kapatan bir kalemdir:** çıkış bacağı hiç dolmadığı
için round-trip friksiyonun yarısı **hâlâ ölçülemedi**.

### A.4 `gap_at_submit` NE DEMEK — ve neden bir gap ölçmüyor

Tanım tek yerde (`broker.entry_order_decision`, `broker.py:194`):
`gap = (ref_price is None) or (trigger > 0 and ref_price >= trigger)`

Yazan: canlı yolda `loop.py:1798-1810` (`_ref = per[ticker].loc[d,"close"]`, yani **sinyal barının
kapanışı**) ve gölge yolda `intraday_shadow.py:345`. Replay onu **hiç geçirmiyor**
(`backtest.py:232-236` argüman listesi) → replayde daima `None`.

**Totoloji kanıtı:** `strategy.py`de yedi kurulumun yedisi de `entry_trigger=float(c)` yazıyor —
c = sinyal barının kapanışı (satır 509 breakout_vcp, 571 pullback, 623 momentum_burst, 678
episodic_pivot, 784 exhaustion_hammer, 862 pead, 989 canslim). Referans fiyat da aynı kapanış.
Yani `rp >= t` ⇔ `close >= close` ⇔ **daima doğru** (tek kaçış: `as_plan()`in 4 haneye
yuvarlaması, `strategy.py:314`, mikroskobik).

**Canlı doğrulama:** E2 defteri 10 satır → `gap_at_submit`: **true 9 · None 1 · false 0.**

Üç sonuç:
- **`mode="stop_limit"` dalı canlıda hiç çalışmıyor** — `submit_bracket`in `stop_limit` kolu ölü kod.
- **`gap_behavior: cancel`** bir "gap günü filtresi" değil, **her emri veto eden kapatma düğmesidir**.
- `entry_order_decision`in gap dalına düşme gerekçesi (buy-stop'un "stop price must be greater than
  current price" ile reddedilmesi — 95/95 vakası) **hâlâ geçerlidir**; kusur davranışta değil,
  **alanın ADINDA ve okunuşundadır**: rapor yüzeyleri `gap_at_submit=true`yu "o gün gap vardı"
  diye okuyabilir, oysa alan "tetik = kapanış" diyor.

### A.5 Ayna vs iç motor — iki ayrı defter, iki ayrı fiyat

E2 defteri iki motoru yan yana yazıyor:

| plan | ayna qty | ayna fill | iç qty | iç fill | resmî açılış (IEX) | ayna bps | iç bps |
|---|---|---|---|---|---|---|---|
| NUE | 25 | 273,9512 | 54 | 273,6478 | 273,51 | +16,13 | +5,04 |
| EMR | 37 | 164,76 | 64 | 163,9473 | 163,865 | +54,62 | +5,02 |
| BKNG | 22 | 210,24 | 43 | 207,5539 | 207,45 | +134,49 | +5,01 |
| AMGN | 22 | 415,0073 | 33 | 414,5927 | 414,385 | +15,02 | +5,01 |

İç motorun bps'i **totolojidir** (defter bunu kendi beyan ediyor: `fill_vs_resmi_acilis_beyan`) —
`base_fill = açılış × (1+5/1e4)` olduğu için tanım gereği 5,0 çıkar. Kalan 0,01–0,04 bps
`IMPACT_COEF × katılım` payıdır ve **bu, likidite modelinin canlı kalibrasyonunu geriye türetmemizi
sağlar** (§B.3).
**Adet farkı (25 vs 54 …) bir slipaj kalemi değildir:** ayna Alpaca paper hesabının özkaynağıyla,
iç motor kendi kitabıyla boyutlanıyor. Ama PF'e etkisi vardır — ölçülen dolum, kitabın taşıdığı
pozisyonun **yarısı kadar** hisseyi temsil ediyor.

**Bugünkü koruma durumu (canlı, 2026-08-13):** 4 motor pozisyonu açık (+1 operatör NVDA'sı) ve
dördünün de `P-KORUMA-20260809-0835-*` OCO'su **`status=new`, `tif=gtc`** — yani korumalar bugün
ayakta. Çıkış bacağı **hâlâ dolmadı**: EDG-037'nin n=0'ı bugün de n=0.

---

## [B] SLİPAJIN KAYNAĞI — dört hipotez, üçü elendi

### B.1 (iv) GAP — elendi (yanlış soru)

`gap_at_submit` §A.4'te totoloji çıktı. Doğru soru "bar tetiğin ÜSTÜNDE mi açtı?"dır ve bu
**ölçülebilir**: tetik = sinyal barı kapanışı olduğu için `gap = açılış/önceki_kapanış − 1`.

**885 replay işleminin tamamında ölçüldü** (`state/bars/*.csv`, eşleşme 885/885, eksik 0):

| büyüklük | medyan | ort | p10 | p25 | p75 | p90 | p95 | min | maks |
|---|---|---|---|---|---|---|---|---|---|
| gap (bps) | **+1,44** | +5,08 | −135,4 | −60,5 | +66,1 | +145,2 | +213,6 | −755,1 | **+394,3** |

**Gap yukarı oranı %51,07 (452/885).** Yani gap ne sistematik ne aleyhte — **simetrik gürültü**.
(Yan teyit: maksimum gap 394,3 bps ve `MAX_ENTRY_GAP_PCT = %4 = 400 bps` — dış zarf gözlenen
dağılımın tam kenarında bağlıyor, yani zarf çalışıyor ama fiilen hiçbir işlemi kesmiyor.)

### B.2 (ii) STOP-TETİK MEKANİĞİ — girişte elendi, çıkışta AÇIK

Giriş emri `type=limit` (§A.1, 4/4 canlı kayıt) → tetik-sonrası market dönüşü yok, fiyat kovalanmıyor.
**Ama koruma OCO'sunun stop bacağı `type=stop`, `limit_price=null`** (`alpaca.py:1022-1024`;
canlı kayıtta `{"type":"stop","stop_price":"257.4","limit_price":null}`). Stop emri tetiklenince
**market emrine döner** ve dolum fiyatı **tavansızdır**. Tetikleyen olay tanımı gereği hızlı ve
aleyhte bir harekettir → **çıkış slipajının beklenen dağılımı girişinkinden KÖTÜdür.**
Replay bunu **modellemiyor**: `_touch_exit` bar-içi stop dokunuşunda çıkışı `eff_stop` (tam stop
fiyatı) kabul ediyor, `close_position` ondan yalnız 5 bps düşüyor (`broker.py:596,669`).
**n=0 → sayı UYDURULMAZ.** Bu, PF hesabının ölçülmemiş yarısıdır ve §C.6'nın konusudur.

### B.3 (iii) EMİR BOYUTU / LİKİDİTE — SAYIYLA elendi

İç motorun kendi dolumundan katılımı geri türetiyoruz (`fill = base_fill × (1 + IMPACT_COEF ×
katılım)`, `broker.py:528`, `IMPACT_COEF=0.10`):

| sym | iç fill / base | ⇒ katılım | ⇒ zımnî ADV (hisse) | qty (ayna) | etki (bps) |
|---|---|---|---|---|---|
| NUE | 1,0000040 | ~4,0e-5 | ~1,3M | 25 | ~0,04 |
| EMR | 1,0000024 | ~2,4e-5 | ~2,7M | 37 | ~0,02 |
| BKNG | 1,0000010 | ~1,0e-5 | ~4,3M | 22 | ~0,01 |
| AMGN | 1,0000012 | ~1,2e-5 | ~2,8M | 22 | ~0,01 |

**Kötümser çapraz kontrol:** Alpaca IEX günlük hacimleriyle (ki bunlar konsolidenin küçük bir
dilimidir, yani ADV'yi **aşağı** saptırır) ADV20 = NUE 70.973 · EMR 150.906 · BKNG 304.500 ·
AMGN 95.042 → en kötü katılım NUE'de **7,6e-4**, etki **0,76 bps**.
**Her iki uçta da etki ≤0,8 bps.** ADV_CAP_PCT (%2) hiçbir emirde bağlamadı (2%×70.973 = 1.419
hisse vs sipariş 25). → **Boyut/likidite, 15–134 bps'lik farkı AÇIKLAYAMAZ. ELENDİ.**

### B.4 (i) AÇILIŞ MİKROYAPISI — kalan tek açıklama, ve KANITI var

**Bulgu 1 — dört dolumun dördü de açılış DAKİKASININ bandında.** Konsolide (SIP) 13:30:00–13:31:00Z
dakika barı:

| sym | 13:30 bar o/h/l/c | bandın genişliği | dolum | banda düşüyor mu | dolum damgası |
|---|---|---|---|---|---|
| NUE | 274,52 / 274,74 / 273,50 / 273,50 | **45,2 bps** | 273,9512 | ✔ | 13:33:07 |
| EMR | 164,32 / 164,85 / 163,24 / 163,615 | **98,0 bps** | 164,76 | ✔ | 13:32:20 |
| BKNG | 207,45 / 210,81 / 207,00 / 210,24 | **183,7 bps** | 210,24 (= bar kapanışı, birebir) | ✔ | 13:32:06 |
| AMGN | 413,715 / 417,14 / 413,00 / 416,74 | **100,1 bps** | 415,0073 | ✔ | 13:32:28 |

Damgalar 13:32–13:33 olmasına rağmen **fiyatların dördü de ilk dakikanın bandına oturuyor**;
NUE'de dolum, damga anındaki konsolide fiyatın (≈271,0) **109 bps ÜSTÜNDE**. Yani Alpaca paper
motoru fiyatı ~ilk dakikadan alıyor, damgayı 2–3 dk gecikmeli basıyor.
**Bu bir mikroyapı bulgusu değil, bir SİMÜLASYON bulgusudur** ve §B.6'nın konusu.

**Bulgu 2 — BKNG (134 bps) ile AMGN (15 bps) farkını AÇIKLAYAN DEĞİŞKEN: ilk dakikanın bandı ve
dolumun o bandın neresine düştüğü.**

| sym | bant | dolumun bant içindeki yeri | bps vs bant orta-noktası |
|---|---|---|---|
| BKNG | 183,7 bps (en geniş) | **tepeye yakın** (bar kapanışı = tavan bölgesi) | **+63,9** |
| EMR | 98,0 bps | üst yarı | +43,6 |
| AMGN | 100,1 bps | **tam orta** | **−1,5** |
| NUE | 45,2 bps (en dar) | alt yarı | −6,2 |

Fark **iki çarpandan** oluşuyor: (a) bandın genişliği — BKNG'nin bandı AMGN'ninkinin 1,8 katı;
(b) bant içindeki konum — BKNG tepede, AMGN ortada. İkisi çarpılınca 134 vs 15 bps çıkıyor.
**"Spread" bu farkı açıklamaz** (dördü de large-cap; efektif spread ~birkaç bps mertebesinde);
açıklayan şey **ilk dakikadaki FİYAT SAPMASI**dır.

**Bulgu 3 — bant genişliği ilk 15 dakikadan sonra YARIYA iniyor (n=401 sembol-seans, 2026-02-02..08-06,
NUE/EMR/BKNG/AMGN, konsolide 15-dk barlar):**

| pencere (UTC) | ortalama menzil (bps, açılışa göre) | ortalama hacim | VWAP − açılış (bps) |
|---|---|---|---|
| 13:30–13:45 | **146,7** | 186.234 | +5,5 |
| 13:45–14:00 | **84,9** (−42%) | 111.142 | +8,9 |
| 14:00–14:15 | **74,3** (−49%) | 104.252 | +13,8 |
| 14:15–14:30 | **63,6** (−57%) | — | — |

Yani **beklemek dağılımı yarıya indiriyor** (bu, ölçülmüş ve sağlam), **ama ortalama fiyat yukarı
sürükleniyor** — koşulsuz örneklemde 15 dk beklemenin bedeli ≈ **+3,4 bps**, 30 dk ≈ **+8,3 bps**
(alıcı aleyhine). Bu ikisi **zıt yönde** çalışır ve net etki bizim sinyalimize **koşulludur**;
koşulsuz örneklem onu cevaplamaz (§C.2'nin kill kriteri budur).

### B.5 SLİPAJIN AYRIŞTIRILMASI — özet tablo

| bileşen | ölçüldü mü | katkı | dayanak |
|---|---|---|---|
| emir boyutu / likidite etkisi | **EVET** | **≤0,8 bps** | §B.3, iki uçlu ADV |
| stop-tetik kovalaması (giriş) | **EVET** | **0** (emir `limit`) | §A.1, 4/4 Alpaca kaydı |
| gap (bar tetik üstünde açtı) | **EVET** | simetrik, medyan +1,4 bps | §B.1, n=885 |
| **açılış ilk-dakika sapması** | **EVET** | **bant 45–184 bps; artığın tamamı** | §B.4, konsolide dakika barı |
| ölçüt hatası (IEX vs konsolide) | **EVET** | **−36,8…+16,2 bps** | §B.6 |
| çıkış bacağı (stop→market) | **HAYIR (n=0)** | **ÖLÇÜLEMEDİ** | §B.2 |

### B.6 ÖLÇÜT KRİZİ — paydanın hatası ölçülen büyüklükle aynı mertebede

`loop._patch_entry_slippage` (`loop.py:2290-2299`) paydayı `opens` haritasından alıyor; o harita
`per[ticker].loc[d,"open"]` (`loop.py:1998`) — yani **Alpaca `DATA_FEED="iex"` günlük barının
açılışı** (`alpaca.py:1092,1431`). IEX konsolide hacmin küçük bir dilimidir; "IEX'in ilk basımı" ≠
"resmî açılış müzayedesi basımı".

| sym | `resmi_acilis` (IEX) | konsolide 13:30 açılışı | **ölçüt hatası** |
|---|---|---|---|
| NUE | 273,51 | 274,52 | **−36,8 bps** |
| EMR | 163,865 | 164,32 | **−27,7 bps** |
| BKNG | 207,45 | 207,45 | 0,0 bps |
| AMGN | 414,385 | 413,715 | **+16,2 bps** |

**EDG-037'nin başlığı ölçüte göre değişiyor:**

| payda | medyan | ort | notional-ağırlıklı | **aleyhte n/4** | PF (simetrik, EDG-037 eğrisi) |
|---|---|---|---|---|---|
| IEX açılış (**yürürlükteki**) | 35,38 | 55,06 | 45,04 | **4/4** | 0,802 |
| konsolide 13:30 açılışı | **29,01** | 42,95 | 34,78 | **3/4** | 0,858 |
| konsolide ilk-dk VWAP | 23,98 | 36,26 | 28,40 | 3/4 | 0,903 |
| konsolide ilk-dk orta-nokta | **21,04** | 24,96 | 18,93 | **2/4** | 0,932 |

*(Ağırlık künyesi: burada notional = **fill × qty**; EDG-037 aynı sütunu **referans fiyat × qty** ile
kuruyor ve 44,849 diyor. Fark 0,19 bps — aynı sayının iki künyesi, çelişki değil.)*

**Bu, EDG-037'yi çürütmez — istatistiksel gücünü zaten kartın kendisi beyan etmişti:** t-CI95
**[−65,5 ; +175,7]** (sıfırı İÇERİYOR), işaret testi p=0,0625. Konsolide ölçütle NUE işaret
değiştirdiğinde işaret testi 3/4 → p=0,25'e düşer. **Yani "slipaj 35 bps'tir" cümlesi n=4'te
kurulamaz; kurulabilen tek cümle "bant 45–184 bps genişliğinde ve biz onun içinde rastgele bir
yere düşüyoruz"dur.**

---

## [C] AZALTMA SEÇENEKLERİ — yedi aday, her biri için mekanizma · bedel · ölçülebilirlik

> **Her seçenekte "dolmayan emir de bir maliyettir" kalemi ayrı satır olarak yazılmıştır.**
> Ölçülemeyen yerde "ölçülemedi + neden" yazar; sayı uydurulmaz.

### C.0 ÖNCE KAPATILMASI GEREKEN ÜÇ MODEL KUSURU (seçenek değil, ön koşul)

Aşağıdaki seçeneklerin **hiçbiri** bugünkü replay motorunda dürüstçe ölçülemez; önce şunlar
kapanmalı, yoksa her ölçüm kendi kusurunu ölçer:

**K1 — Replay dinlenen limiti modellemiyor (tek-atış açılış).** `broker.fill_entry` limiti YALNIZ
`next_open`a karşı sınıyor (`broker.py:505`); açılış limitin üstündeyse `entry_missed_limit` ve işlem
**tamamen kaybolur**. Gerçekte emir `day`/`gtc` ile **seans boyunca dinlenir** ve fiyat geri gelirse
dolar. **Kanıt (2026-08-06, konsolide tape):** 100 bps tavanla EMR/BKNG/AMGN'nin limit fiyatı aynı
seans içinde **dörtte dördünde işlem gördü** → dinlenen limit dolma FIRSATI buldu:

| sym | tetik | %1 limit | gerçek dolum | seans en düşüğü | limit dokunuldu mu | tavanın tavan-üstü tasarrufu |
|---|---|---|---|---|---|---|
| NUE | 274,57 | 277,3157 | 273,9512 | 270,15 | tavan bağlamadı | 0,00 bps |
| EMR | 162,16 | 163,7816 | 164,76 | 156,085 | **evet** | **≥59,74 bps** |
| BKNG | 207,03 | 209,1003 | 210,24 | 205,825 | **evet** | **≥54,50 bps** |
| AMGN | 407,73 | 411,8073 | 415,0073 | 401,23 | **evet** | **≥77,71 bps** |

Notional-ağırlıklı üst-sınır tasarruf = **49,65 bps** (payda: Σ fill×qty = 26.700,34 $).
**ŞERH:** "limit fiyatı işlem gördü" ≠ "emrimiz
dolardı" — kuyruk önceliği/paper motorunun davranışı simüle EDİLMEDİ. Bu satır bir **fırsat kanıtı**,
bir dolum iddiası değil. Ama K1 kapanmadan yapılan her limit-tavanı ölçümü **kaçan işlem maliyetini
SİSTEMATİK OLARAK ABARTIR**, ve 2026-08-03 E1 grid hükmü tam olarak o abartılmış maliyetle verilmiştir.

**K2 — Replay'de gün-içi zaman yok.** Veri katmanı **yalnız `timeframe=1Day`** çekiyor
(`alpaca.py:1431`); dakika barı yolu depoda YOK. → "13:45'te gir", "ilk N dakikadan kaçın",
"VWAP/TWAP penceresi" seçeneklerinin **hiçbiri bugünkü replayde modellenemez** (canlı-only).

**K3 — Ölçüt IEX.** §B.6. Payda konsolideye taşınmadan hiçbir "iyileşti/kötüleşti" cümlesi
kurulamaz; 37 bps'lik ölçüt hatası, hedeflenen iyileşmeden büyüktür.

---

### C.1 · Limit tavanını gerçekten BAĞLAYICI yap (`limit_pct_cap` 0,04 → 0,005…0,015)

**Nasıl çalışır.** `entry_law` limiti `tetik + min(mult·ATR14, pct_cap·tetik)`. Bugün
`mult=100`/`cap=%4` → tavan 400 bps, dört dolumun dördü tavanın 213–406 bps ALTINDA kaldı, yani
tavan **hiçbir şey yapmadı**. Cap'i 50–150 bps'e indirmek, ödenen fiyata **gerçek bir çatı** koyar.

**Slipajı hangi mekanizmayla düşürür.** Çatının üstündeki her dolum ya olmaz ya da fiyat geri
gelince **çatıda/altında** olur. §C.0-K1 tablosunda 2026-08-06'da üst-sınır tasarruf ≈49 bps.

**KARŞILIĞINDA NE KAYBEDERİZ — iki ölçüm, ZIT işaret. Bu çelişki bu belgenin en önemli kalemi.**

*(a) 2026-08-03 E1 grid'i (yol-bağımlı, tam replay, ESKİ paket):*

| kol | tavan | çağrı | dolan | **dolmama** | `entry_missed_limit` | net $ | PF | kaçanların 10-gün ileri R'si |
|---|---|---|---|---|---|---|---|---|
| a | min(0,25·ATR, %0,5) | 124 | 81 | **%34,7** | 38 | **−7.202** | 0,707 | **ort +0,2265 · %60,5 pozitif** |
| b | min(0,5·ATR, %1,0) | 176 | 147 | %16,5 | 23 | **−1.182** | 0,965 | ort +0,2577 · %52,2 pozitif |
| c | min(1,0·ATR, %1,5) | 199 | 180 | %9,6 | 12 | **−2.878** | 0,926 | ort −0,0848 · %41,7 pozitif |
| ref | **limitsiz** | 168 | 164 | %2,4 | 0 | **+2.957** | **1,083** | — |

→ **Monoton ve net: tavan sıktıkça para kaybediyor; kaçan dolumlar sistematik KAZANAN.** Operatörün
2026-08-03 kararı (`goal.yaml:69-78`) tam olarak bu tabloya dayanıyor ve **o tabloya göre doğrudur.**

*(b) Bugünkü 885-işlemlik defterde aynı kesim (yol-BAĞIMSIZ, birinci-derece; benimsenen paket):*

| tavan | kaybolan işlem | kaybolanların P&L'i | kalan defter P&L | **PF** |
|---|---|---|---|---|
| — (bugün, 400 bps) | 0 | — | 20.685 $ | **1,1119** |
| 300 bps | 18 (%2,0) | **+1.586 $** (kazanan) | 19.099 $ | 1,1047 |
| 200 bps | 49 (%5,5) | −230 $ | 20.915 $ | 1,1195 |
| **150 bps** | 84 (%9,5) | **−4.177 $** | **24.862 $** | 1,1496 |
| **100 bps** | 152 (%17,2) | **−1.613 $** | 22.298 $ | **1,1451** |
| 75 bps | 207 (%23,4) | −3.736 $ | 24.420 $ | 1,1752 |
| **50 bps** | 272 (%30,7) | −2.474 $ | 23.159 $ | **1,1817** |
| 25 bps | 365 (%41,2) | **+5.985 $** (kazanan) | 14.700 $ | 1,1306 |
| 10 bps | 411 (%46,4) | **+8.441 $** (kazanan) | 12.244 $ | 1,1173 |

→ Bu defterde **50–150 bps bandı PF'i yükseltiyor**, ≤25 bps kazananları kesiyor, ≥300 bps atıl.

**ÇELİŞKİ NEREDEN GELİYOR — üç aday, ikisi bilinen kusur:**
1. **K1 (dinlenen limit modellenmiyor)** — (a) kaçan işlemi TAMAMEN siliyor, oysa gerçekte çoğu
   sonra doluyordu. Bu, (a)'nın "kaçan maliyeti"ni **abartır**.
2. **Yol bağımlılığı** — (a) her kolu baştan koşuyor (slot/ısı/özkaynak yolu değişir); (b) yalnız
   gerçekleşmiş satırları siliyor, **boşalan slotu YENİDEN DOLDURMUYOR**. Bu, (b)'yi **iyimser**
   yapar. (a) bu tuzağı kendi raporunda beyan etmiş: *"yol-bağımlı: eşleşmeyen kaçan planlar o kolda
   slot/ısı/eş-anlılık nedeniyle hiç açılmamış olabilir"*.
3. **Farklı paket/pencere** — (a): 124–199 işlem, slot5/1,0R, 2026-08-03 stratejisi. (b): 885 işlem,
   slot20/0,5R, benimsenen paket, 2022-01-07…2026-07-24.
   **Ayrıca (b) SEÇİM SONRASI bir kesimdir:** gap büyüklüğü, paketi seçen aramanın değişkeni
   DEĞİLDİ; kesimin monoton olmaması (10/25 kötü → 50/150 iyi → 300 nötr) **gürültüye oturma
   şüphesini büyütür.** (b) bir bulgu değil, **bir hipotezdir.**

**Replayde nasıl modellenir.** Bugün: **yanlı** (K1). K1 kapanırsa: tam modellenebilir — `fill_entry`e
"bar-içi limit dokunuşu" dalı (`low <= limit` → dolum `limit`te, muhafazakâr) eklenirse günlük barla
bile birinci-derece doğru olur.

**Gerekli kart.** İki aşama: (1) K1 düzeltmesinin **kendisi** bir kart (mevcut defteri değiştirir →
tüm karneler yeniden koşar); (2) sonra `limit_pct_cap` grid'i **yeniden** ölçülür.

---

### C.2 · Açılışın ilk N dakikasından kaçın (13:45+ giriş / VWAP-TWAP penceresi)

**Nasıl çalışır.** Emir açılışta değil, T+N dakikada (ya da N dakikalık TWAP dilimleriyle) gönderilir.
Teknik olarak bugün de mümkün: emir `extended_hours=false` ve `gtc` olduğu için **gönderim saatini
kaydırmak yeterlidir** (yeni emir tipi gerekmez) — `daily_cycle`ın gönderim adımı gün-içi bir
tetiğe bağlanır.

**Slipajı hangi mekanizmayla düşürür.** §B.4-Bulgu-3: dolumun düşebileceği bandın genişliği
13:30–13:45'te 146,7 bps, 13:45–14:00'da **84,9 bps (−%42)**, 14:00–14:15'te 74,3 bps (−%49).
Yani **kötü tarafa düşme riskinin ÖLÇEĞİ yarıya iner.** Hacim aynı pencerede 186k→111k'ya iner —
%40 düşüş, ama emir boyutumuz ADV'nin ~1e-5'i olduğu için (§B.3) **likidite kısıtı hiçbir dilimde
bağlamaz.**

**KARŞILIĞINDA NE KAYBEDERİZ.**
- **Sürüklenme bedeli (ÖLÇÜLDÜ, koşulsuz):** ortalama VWAP açılışa göre +5,5 → +8,9 → +13,8 bps.
  15 dk beklemek alıcıya ≈ **+3,4 bps**, 30 dk ≈ **+8,3 bps**. PF eğrisinde 3,4 bps/bacak
  simetrik ≈ **−0,042 PF**. Yani **dağılım daralması PF'e bedava gelmez.**
- **Sinyal-koşullu sürüklenme (ÖLÇÜLEMEDİ):** biz momentum/breakout isimleri alıyoruz; koşullu
  sürüklenme koşulsuzdan büyük olabilir. **Koşulsuz örneklem bu soruyu CEVAPLAMAZ.**
- **Kaçan işlem:** bu seçenekte **doğrudan kaçan işlem yok** (emir yine gönderiliyor, yalnız geç).
  Dolaylı risk: gün içinde `MAX_ENTRY_GAP_PCT`/limit tavanını aşan bir fiyat, geç gönderimde emri
  **gönderilemez** kılabilir → o gün kaçar. Bugünkü 400 bps tavanla bu neredeyse hiç olmaz.
- **Anekdot (n=4, TEK seans, çıkarım DEĞİL):** 2026-08-06'da 13:45 açılışına göre dolumlarımız
  NUE +52,3 · EMR +115,4 · **BKNG −63,8** · AMGN +98,6 bps → medyan **+75,5 bps** (yani beklemek
  medyanda 75 bps kazandırırdı, ama BKNG'de 64 bps kaybettirirdi). **n=4/1 seans: hiçbir hüküm
  taşımaz.**

**Replayde nasıl modellenir.** **MODELLENEMEZ (K2).** Depoda dakika barı yolu yok
(`timeframe=1Day` tek yol). Ölçüm ya (a) yeni bir dakika-barı arşivi + `fill` sözleşmesinin
genişletilmesini gerektirir (büyük iş, tüm karneleri yeniden koşturur), ya da (b) **canlı A/B**
olur — ki paper hesapta tek kol koşabildiğimiz için A/B da yapısal olarak zordur.

**Gerekli kart.** Önce **ölçüm altyapısı kartı** (dakika barı arşivi + gün-içi dolum sözleşmesi),
sonra pencere grid'i. Bu, buradaki en pahalı ama **etkisi en büyük** kalemdir.

---

### C.3 · `gap_behavior: cancel` (gap gününde girişi iptal et)

**Nasıl çalışır.** `entry_order_decision` gap dalında emri hiç göndermez; iç motor da
`fill_entry`de aynı vetoyu uygular (`broker.py:493`).

**Slipajı hangi mekanizmayla düşürür.** Teorik olarak "kötü açılışlarda hiç girme".

**KARŞILIĞINDA NE KAYBEDERİZ — ÖLÇÜLDÜ, YIKICI:**
- **Yürürlükteki tanımla (`rp >= trigger`, §A.4 totolojisi): emirlerin %100'ü veto edilir.**
  Canlı defter 9/9 `true`. Bu bir filtre değil, motoru kapatmaktır.
- **Anlamlı tanımla ("bar tetiğin üstünde açtı"): 885 işlemin 452'si (%51,1) kaybolur** ve
  kaybolanların net P&L'i **+11.233 $** (kazanan) → defter 20.685 $ → **9.452 $**. Yıkıcı.
- E1 grid'i bunu **hiç ölçemedi**: `_cnl` kolları `_mkt` kollarıyla **birebir aynı digest** verdi
  (`entry_gap_veto_reddi: 0`, `gap_at_submit_none: 124/176/199`) çünkü replay `gap_at_submit`
  geçirmiyor (`backtest.py:232-236`). Yani **grid'in yarısı boş koştu.**

**Replayde nasıl modellenir.** Bugün **hiç** (argüman geçilmiyor). Geçirilse bile totoloji yüzünden
tek anlamlı tanım "açılış > tetik"tir ve o zaten §B.1'de ölçüldü.

**Hüküm önerisi: KAVRAMEN ELE — dosyayı kapat.** Ayrıca **`gap_at_submit` alanının ADI yanıltıcıdır**
ve rapor yüzeylerinde "gap vardı" diye okunma riski taşır; bu bir görünürlük borcudur.

---

### C.4 · Stop-limit dalını canlıda GERÇEKTEN çalıştır (tetik teyidi + tavan)

**Nasıl çalışır.** Bugün `mode` daima `marketable_limit` (§A.4) → `stop_limit` kolu ölü.
`entry_trigger`ı sinyal barı kapanışından **ayırmak** (ör. `kapanış × (1+ε)` ya da pivot üstü)
gap tanımını gerçek yapar ve emirlerin bir kısmı **stop-limit** olarak gider: fiyat tetiği
yukarı kırmadan girilmez, kırınca **limit tavanıyla** girilir.

**Slipajı hangi mekanizmayla düşürür.** İki koruma birden: (a) fiyat teyidi olmadan alım yok —
açılışta aşağı açan barlarda hiç girilmez; (b) tetik-üstü dolumun tavanı limittir.

**KARŞILIĞINDA NE KAYBEDERİZ.**
- **Kaçan işlem: BÜYÜK ve ölçülmedi.** Tetiği kapanışın üstüne taşımak, "aşağı açıp gün içinde
  toparlayan" barları tamamen dışarıda bırakır. §B.1'deki dağılıma göre işlemlerin **%48,9'u
  tetiğin ALTINDA açıyor** — ε>0 ile bunların hepsi risk altına girer.
- **Alpaca reddi riski geri gelir:** 95/95 red vakasının kökü tam olarak buydu (`broker.py:44-49`).
  ε çok küçükse red, çok büyükse kaçan işlem. **Bu bir ayar değil, bir eğridir.**

**Replayde nasıl modellenir.** `entry_trigger` bir **strateji** alanıdır (`strategy.py`), icra yasası
değil → replay onu doğal olarak modeller (dolum yine açılışta sınanır). **K1 yine bağlar:** stop
tetiklenmesi gün içinde olabilir, replay bunu göremez.

**Gerekli kart.** `entry_trigger` ofset grid'i (ε ∈ {0, 0,25·ATR, 0,5·ATR, pivot}) — ama bu bir
**strateji** kartıdır, icra kartı değil; K sayımına girer ve kill-list'i vardır.

---

### C.5 · ADV/katılım kısıtını sıkılaştır

**Nasıl çalışır.** `ADV_CAP_PCT` (%2) ve `IMPACT_COEF` (0,10) daraltılır.

**Slipajı hangi mekanizmayla düşürür.** Teoride büyük emri parçalar.

**KARŞILIĞINDA NE KAYBEDERİZ.** Ölçmeye gerek kalmadan: **bu kaldıraç bizde ÖLÜ.** §B.3'te
katılım 1e-5…8e-4 ölçüldü; %2 tavanı 25 hisselik bir emirde 1.419 hissede duruyor.
**Sıkılaştırma slipajı 0,8 bps'ten fazla düşüremez** ama pozisyon boyutunu keserek **P&L'i
doğrudan küçültür.**

**Replayde nasıl modellenir.** Tam modellenir (`broker.py:520-528` zaten var).

**Hüküm önerisi: ÖNCELİK YOK.** Ölçülen etki, hedeflenen 9,5 bps başabaşın onda biri.
*(Ama §B.3'ün yan bulgusu kalemdir: canlı ADV kaynağı IEX günlük hacmiyse gerçek ADV'yi ~20–50x
küçük gösteriyor; bugün zararsız çünkü tavan bağlamıyor — pozisyon büyürse bağlar.)*

---

### C.6 · ÇIKIŞ bacağını stop-market'ten stop-limit'e taşı (ölçülmemiş yarı)

**Nasıl çalışır.** `submit_protective_oco` bugün `stop_loss: {stop_price: sl}` gönderiyor
(`alpaca.py:1024`) → tetiklenince **market**. Alpaca `stop_limit` bacağını da destekler
(`{stop_price, limit_price}`).

**Slipajı hangi mekanizmayla düşürür.** Stop tetiklenmesi tanımı gereği **hızlı ve aleyhte** bir
harekette olur; market dönüşü orada **tavansızdır**. Limit koymak tavanı geri getirir.

**KARŞILIĞINDA NE KAYBEDERİZ — ve bu SEÇENEKLERİN EN TEHLİKELİSİDİR.**
- **Dolmayan stop = korumasız pozisyon.** Fiyat limitin altından geçip giderse stop **dolmaz** ve
  pozisyon açık kalır — kayıp 1R ile sınırlı olmaktan çıkar. Bu, "kaçan işlem" değil **kaçan
  KORUMA**dır ve zarar dağılımının kuyruğunu açar.
- Depo bu sınıfı zaten bir kez yaşadı: `tif=day` dört pozisyonu bir gece çıplak bıraktı
  (`broker.py:63-71`). Aynı sınıf, farklı aracı.

**Replayde nasıl modellenir.** Bugünkü replay stop çıkışını `eff_stop`ta dolmuş kabul ediyor
(`broker.py:596`) → **gerçek stop slipajı SIFIR varsayılıyor.** Stop-limit'i modellemek için
"limitin altına düşen bar → dolum YOK, pozisyon devam" dalı gerekir; bu **çıkış sözleşmesini
değiştirir** ve tüm karneleri yeniden koşturur.

**Gerekli kart.** İki ayrı kart: (1) **çıkış slipajı ÖLÇÜM kartı** (canlı; n≥10 gerçek çıkış
dolumu birikene kadar hüküm yok — bugün n=0); (2) ondan sonra stop-limit tasarım kartı.

---

### C.7 · Pasif limit + kaçırma toleransı (tetiğin ALTINA limit)

**Nasıl çalışır.** Limit `tetik + offset` yerine `tetik − offset` (ya da önceki kapanışın altına)
konur; yalnız fiyat bize gelirse dolarız.

**Slipajı hangi mekanizmayla düşürür.** Beklenen slipaj **negatife** döner (alış limitin altında ya
da limitte).

**KARŞILIĞINDA NE KAYBEDERİZ.**
- **Ters seçilim (adverse selection) — bu seçeneğin ÖZ kusuru:** pasif limit **yalnız fiyat aleyhte
  dönerse** dolar. Yani dolanlar sistematik olarak **kaybedenlerdir**; kaçanlar **kazananlardır**.
  §C.1(a)'nın "kaçanlar sistematik kazanan" bulgusu bunun **doğrudan kanıtıdır** ve pasif limit
  o etkiyi **azami** yapar.
- **Kaçan işlem oranı:** §B.1 dağılımıyla üst-sınır tahmin: tetiğin altında açan barlar %48,9;
  pasif limit tetiğin X bps altındaysa dolum oranı bundan da düşer. **Tam sayı ölçülmedi**
  (dolum "açılış ≤ limit" değil "gün-içi düşük ≤ limit" ile belirlenir → K1/K2 bağlar).

**Replayde nasıl modellenir.** Bugün **modellenemez** (K1: bar-içi dokunuş yok). K1 kapanırsa
günlük `low` ile birinci-derece modellenebilir.

**Hüküm önerisi: DÜŞÜK ÖNCELİK** — mekanizması stratejinin momentum tezinin tersine çalışıyor.

---

## [D] ÖNCELİK SIRALI ÖNERİ TABLOSU

Etki = PF'e beklenen katkı · Maliyet = kaybedilen işlem/koruma · Zorluk = ölçüm işi.

| # | Seçenek | Beklenen etki (bps/bacak) | Kaçan-işlem maliyeti | Ölçüm zorluğu | Öncelik |
|---|---|---|---|---|---|
| 1 | **K3: ölçütü konsolideye taşı** | **0 (fiyat değişmez)** — ama ölçülen sayı 35,4→29,0 (medyan) ve 4/4→3/4 | **YOK** | **DÜŞÜK** (payda kaynağı değişir) | **1 — hemen** |
| 2 | **K1: replayde dinlenen limit** | 0 (fiyat değişmez) — ama C.1/C.7'nin ölçümünü DOĞRU yapar | YOK | ORTA (dolum sözleşmesi + tüm karneler) | **2** |
| 3 | **C.6a: çıkış slipajı ÖLÇÜM kartı** | ölçülemedi (n=0) — **friksiyonun yarısı** | YOK (salt ölçüm) | DÜŞÜK (bekleme + defter) | **3** |
| 4 | **C.1: `limit_pct_cap` 50–150 bps** | üst-sınır **−49,65 bps** (n=4, 1 seans) | **ÇELİŞKİLİ**: (a) −7,2k$ · (b) +1,6…4,2k$ | ORTA (K1 sonrası) | **4** |
| 5 | **C.2: 13:45+ / TWAP penceresi** | dağılım **−%42**; sürüklenme **+3,4 bps** | doğrudan yok | **YÜKSEK** (K2: dakika barı altyapısı) | **5 — en pahalı, en büyük** |
| 6 | C.4: `entry_trigger` ofseti (stop-limit dalını dirilt) | ölçülemedi | **BÜYÜK** (%48,9 tetik-altı açılış risk altında) | ORTA (strateji kartı, K sayımı) | 6 |
| 7 | C.6b: koruma stop→stop_limit | ölçülemedi | **KAÇAN KORUMA** (kuyruk riski) | YÜKSEK | 7 — C.6a'sız YASAK |
| 8 | C.7: pasif limit | negatif slipaj | **ters seçilim** (kanıtlı) | ORTA | 8 |
| 9 | C.5: ADV/katılım sıkılaştırma | **≤0,8 bps** | boyut kaybı | DÜŞÜK | **YOK** |
| 10 | C.3: `gap_behavior: cancel` | — | **%51 işlem / +11,2k$** (ya da %100) | — | **ELE** |

**PF bağlamı (EDG-037 eğrisi, simetrik):** başabaş **9,49 bps/bacak**. Bugünkü en iyimser ölçüt
(ilk-dk orta-nokta) bile medyan **21,0 bps** diyor → **PF 0,93**. Yani **hiçbir tek seçenek tek
başına yetmiyor**; 1+2+3 (ölçüm altyapısı) olmadan 4/5'in hükmü kurulamaz.

---

## [E] ROL-1'İN AÇMASI GEREKEN KARTLARIN TASLAK BAŞLIKLARI

1. **`TCA-2026-001` — Slipaj ölçütünün konsolideye taşınması (IEX → SIP açılışı).**
   Hipotez: `resmi_acilis` payda hatası ±37 bps mertebesinde ve EDG-037'nin işaretini değiştiriyor.
   Kill: konsolide açılış 4/4 satırda IEX'ten ≤5 bps farklıysa kart düşer.
   Ürün: yeniden hesaplanmış EDG-037 tablosu + payda künyesi. K += 0 (betimsel).

2. **`EXE-2026-005` — Dinlenen limit dolumu (replay `fill_entry` bar-içi dalı).**
   Hipotez: bugünkü tek-atış açılış modeli, limit tavanının kaçan-işlem maliyetini abartıyor.
   Kill: `low <= limit` dalı 885 defterinde dolum sayısını %2'den az değiştiriyorsa kart düşer.
   **ŞART:** bu kart mevcut tüm karneleri geçersiz kılar; benimsenen paket yeniden koşulmalıdır.

3. **`EXE-2026-006` — Çıkış bacağı gerçek friksiyonu (n≥10 dolum kapısı).**
   Hipotez: stop-market çıkışların slipajı giriş slipajından büyüktür.
   Kill: 10 gerçek çıkış dolumu birikmeden **hüküm yok**; kart açık bekler.
   Bugünkü sayaç: **n=0** (24 satış emri, 0 dolum).

4. **`EXE-2026-007` — `limit_pct_cap` grid'inin YENİDEN ölçümü (EXE-2026-005 sonrası).**
   Grid: {0,005 · 0,01 · 0,015 · 0,02 · 0,04}. K çarpılarak sayılır.
   Kill: dolmama oranı >%40 (EXE-2026-001'in kill'i korunur) · PF iyileşmesi CI-0 içindeyse düşer.
   **Ön-kayıt şartı:** 2026-08-12 defterindeki yol-bağımsız kesim (§C.1b) bir HİPOTEZDİR, kanıt
   değildir; kart onu ön-kayıtlı olarak sınamalıdır.

5. **`EXE-2026-008` — Gün-içi giriş penceresi ölçüm ALTYAPISI (dakika barı arşivi).**
   Ürün: 885 defterinin (ticker, tarih) çiftleri için konsolide dakika barları + `fill`
   sözleşmesinin gün-içi genişletmesi. Bu kart bir HÜKÜM üretmez, **bir yetenek** üretir.
   Kill: arşiv kapsaması <%90 ise pencere kartı açılmaz.

6. **`EXE-2026-009` — Giriş penceresi grid'i (13:30 / 13:45 / 14:00 / TWAP-3×5dk).**
   EXE-2026-008'e bağımlı. Hipotez: dağılım daralması (−%42, ölçüldü) sürüklenme bedelini
   (+3,4 bps, ölçüldü) aşar.
   Kill: koşullu sürüklenme koşulsuzun 2 katından büyükse (yani sinyalimiz sabahın hareketiyle
   aynı yöne bakıyorsa) kart düşer.

7. **`OBS-2026-00x` — `gap_at_submit` adlandırma/görünürlük borcu.**
   Alan bir gap ölçmüyor (totoloji, §A.4) ama pano/rapor yüzeyleri onu gap sanabilir.
   Ürün: doküman + (Rol-1 uygun görürse) alan adının/beyanının düzeltilmesi. Ölçüm kartı değil.

---

## [F] ÖLÇÜLEMEYENLER — açıkça

| Ne | Neden ölçülemedi |
|---|---|
| **Çıkış slipajı** | n=0. Motorun gönderdiği 24 satış emrinin 0'ı doldu (12 canceled · 4 expired · 4 held · 4 new). Round-trip friksiyonun yarısı boş. |
| **Slipajın gerçek düzeyi** | n=4 · t-CI95 [−65,5 ; +175,7] sıfırı içeriyor · işaret testi p=0,0625 (konsolide ölçütle 3/4 → p=0,25). "35 bps" bir nokta tahmini değil, bir örneklem artefaktı olabilir. |
| **Gün-içi pencere etkisi (koşullu)** | K2: depoda dakika barı yolu yok (`timeframe=1Day`). Koşulsuz 15-dk ölçümü (n=401) yapıldı ama **bizim sinyalimize koşullu değil.** |
| **Gap-vetosunun replaydeki etkisi** | `backtest.py:232-236` `gap_at_submit` geçirmiyor → E1 grid'inin `_cnl` kolları `_mkt` ile birebir aynı digest verdi (grid'in yarısı boş koştu). |
| **Limit tavanının gerçek kaçan-işlem maliyeti** | K1: replay dinlenen limiti modellemiyor → (a) abartıyor, (b) yol-bağımsızlığı yüzünden iyimser. **İki ölçüm zıt işaretli ve ikisi de kusurlu.** |
| **Alpaca paper dolum motorunun davranışı** | Kapalı kutu. Dolum damgaları 13:32–13:33, fiyatlar 13:30–13:31 bandında (NUE'de damga anındaki piyasadan 109 bps yukarıda). Gerçek-para icrasında bu gecikme **olmayabilir de, daha kötü de olabilir.** |
| **Ayna/iç motor adet farkının PF'e etkisi** | Ayna 25/37/22/22 · iç 54/64/43/33. İki farklı özkaynak tabanı; hangisinin "gerçek" defter olduğu bu kartın kapsamı dışı. |

---

## [G] TEK CÜMLELİK HÜKÜM ÖNERİSİ (Rol-1'e)

**Slipajı replay varsayımına yaklaştırmanın önünde bugün bir İCRA sorunu değil, bir ÖLÇÜM sorunu
duruyor:** ölçüt yanlış feed'den (±37 bps), örneklem n=4 (CI sıfırı içeriyor), friksiyonun yarısı
(çıkış) hiç ölçülmemiş ve replay motoru kaçan-işlem maliyetini yapısal olarak abartıyor.
**Bu dört kalem kapanmadan alınacak her icra kararı — limit tavanı dahil — ölçülmemiş bir yetkidir.**
Kapandıktan sonra en büyük tek kaldıraç, ölçülmüş olarak, **açılışın ilk 15 dakikasının 146,7 bps'lik
bandından çıkmaktır** (ikinci pencerede 84,9 bps, −%42) — bedeli koşulsuz **+3,4 bps** sürüklenme,
ve koşullu bedeli **henüz ölçülmemiştir.**

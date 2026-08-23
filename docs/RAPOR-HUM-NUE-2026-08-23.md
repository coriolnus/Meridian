# TEŞHİS — T00101/HUM ve T00098/NUE tutarsızlıkları (2026-08-23)

**Kalem:** operatör E-kod partisi [7]. **Tür:** SALT-OKUMA canlı teşhis. **KOD DÜZELTMESİ
YAPILMADI** — her iki bulgunun kök nedeni adlandırıldı ve düzeltme ÖNERİSİ yazıldı; uygulama
kararı Rol-1'de.

## 0. Künye

| | |
|---|---|
| Kaynak | A1 canlı, `/opt/meridian/state/` — `meridian.db` (`mode=ro`), `mirror_orders.json`, `entry_execution.jsonl`, `events.jsonl`, `portfolio` belgesi |
| Yazım | YOK |
| Ölçüm anı | `2026-08-23T20:31+00:00` |

**Ortak arka plan (ikisini de anlamak için gerekli):** sistem AYNI planı iki motorda yürütür —
`ic` (iç paper defteri, GÜNLÜK bar üzerinde simüle eder) ve `ayna` (Alpaca paper, gerçek emir).
`trades` satırının `ts_open`/`ts_close`/`exit`/`qty` alanları **iç motorun** hükmüdür; ayna
gerçeği satıra ancak `alpaca_fill_price` + `mirror_divergence` YAMASI olarak girer. İki bulgu da
bu yamanın sınırlarında yaşıyor.

---

## 1. T00101 / HUM — `ts_close` 2026-08-19, broker 2026-08-17

### 1.1 Ölçülen kanıt

**Defter (`trades`, seq 891):**

```
id=T00101  plan_id=P-2026-08-14-HUM  ticker=HUM  kaynak=live_paper
ts_open=2026-08-17  ts_close=2026-08-19  bars_held=2  exit_reason=stop
entry=387.035  exit=380.0992  qty=57
extra_json: {"alpaca_fill_price": 380.0, "mirror_divergence": 0.00026}
```

**Broker (`mirror_orders.json`, HUM):**

| coid | yön | statü | adet | fiyat | `updated` (UTC) |
|---|---|---|---|---|---|
| `P-2026-08-14-HUM` | buy | filled | 43 | 385,175116 | **2026-08-17T13:36:52** |
| `5b69f3c1-…` | sell | canceled | 0/43 | — | 2026-08-17T13:37:24 |
| `6aadbb7a-…` | sell | **filled** | 43 | **380** | **2026-08-17T13:37:47** |

Yani **broker pozisyonu 17 Ağustos sabahı, girişten 55 saniye sonra kapatmıştır** (koruma bacağı
dolmuş; plan stop'u 380,2893, dolum 380). Defter ise pozisyonu 08-18 ve 08-19 boyunca AÇIK
saymış ve 08-19'un günlük barında stop'a çarptırmıştır (`bars_held=2`).

**Olay defteri bu ayrışmayı GÖRDÜ ve BAĞIRDI:**

* `2026-08-17T20:39:52` — `MIRROR_DRIFT` · *"ayna pozisyonu kayıp: HUM içeride açık, Alpaca'da ne
  pozisyon ne emir var"* · `drift_sinifi="split_brain"`, `local_qty=57`
* `2026-08-17T20:45:24` — `ONAYLI_PLAN_GONDERILMEDI` · *"…iç motor doldurdu, Alpaca'da NE EMİR NE
  POZİSYON var (gönderim izi VAR)"* — **bu alarmın metni yanıltıcıdır**: emir gönderilmişti ve
  DOLMUŞTU; broker'da hiçbir şey görünmemesinin sebebi pozisyonun 7 saat önce KAPANMIŞ olmasıydı.
* `2026-08-19T20:33:10` — `mirror_exit_fill_patched` · `kaynak="bacak"`, `alpaca_fill=380.0`,
  `sim=380.0992`, `divergence=0.00026`

### 1.2 Kök neden

Çıkış dolum-yaması **FİYATI taşır, ZAMANI taşımaz.** 08-19'da koşan yama, 08-17'de gerçekleşmiş
bir dolumun fiyatını 08-19 tarihli bir satıra yazdı ve satırın zaman alanlarına dokunmadı. Yamanın
kendisi doğru çalıştı (sapma %0,026 — fiyatlar neredeyse birebir); **yanlış olan şey, satırın
"ne zaman" sorusuna hâlâ İÇ MOTORUN cevabını vermesi.**

İkinci katman: satır ayrıca **adet** ve **giriş fiyatı** bakımından da ayrık (iç 57 @ 387,035 ↔
broker 43 @ 385,175116). Bu, HUM'a özgü değil — canlı defterin bilinen `makbuzsuz_boyut` sınıfıdır
(`broker_reconcile.json` 2026-08-21: EMR 64↔37, BKNG 43↔22, AMGN 33↔22).

### 1.3 Etkisi

* `bars_held=2` **YANLIŞTIR**; gerçek tutuş 55 saniyedir. Elde-tutma süresine bakan her ölçüm
  (exit-efficiency, time_stop kalibrasyonu, rejim-içi süre analizi) bu satırda 2 gün fazla sayar.
* `r_multiple = −1,017` fiyat bakımından doğru sayılabilir (380 ≈ 380,0992) ama **yolu** yanlıştır:
  iç motorda 08-18/08-19 boyunca açık kalan bir risk, gerçekte hiç taşınmadı. `mae_r=2,187`
  (08-18–19 barlarından) gerçekleşmemiş bir maruziyeti ölçüyor.
* Portföy ısısı/korelasyon kapıları 08-18 ve 08-19'da var olmayan bir HUM pozisyonuyla hesaplandı.

---

## 2. T00098 / NUE — `alpaca_fill_price` yamasız

### 2.1 Ölçülen kanıt

**Defter (`trades`, seq 888):**

```
id=T00098  plan_id=P-2026-08-05-NUE  ticker=NUE  kaynak=live_paper
ts_open=2026-08-06  ts_close=2026-08-19  exit_reason=stop
entry=273.6478  exit=257.2746  qty=54
extra_json: {"skill_chain": [...]}        ← alpaca_fill_price YOK, mirror_divergence YOK
```

**Broker (`mirror_orders.json`, NUE) — ÇIKIŞ GERÇEKLEŞMİŞTİR:**

| coid | yön | statü | adet | fiyat | `updated` (UTC) |
|---|---|---|---|---|---|
| `P-2026-08-05-NUE` (giriş bracket parent) | buy | filled | 25 | 273,9512 | 2026-08-06T13:33:08 |
| `8796e3f6-…` (parent'ın bacağı) | sell | **expired** | 0/25 | — | 2026-08-06T20:02:06 |
| `2af95ccb-…` (parent'ın bacağı) | sell | **canceled** | 0/25 | — | 2026-08-06T20:02:06 |
| `P-KORUMA-20260809-0835-NUE` | sell | canceled | 0/25 | — | 2026-08-19T17:45:58 |
| `f57885f7-…` (o korumanın OCO kardeşi) | sell | **filled** | **25** | **256,7632** | **2026-08-19T17:46:01** |

**Yama kuyruğu (canlı `portfolio` belgesi → `exit_fill_pending`) — kayıt HÂLÂ AÇIK:**

```json
"P-2026-08-05-NUE": {"ticker": "NUE", "kaynak": "bacak", "order_id": null,
                     "reason": "stop", "since": "2026-08-19", "tries": 3,
                     "son_neden": "bracket bacağında dolum fiyatı yok (bacak henüz dolmadı / iptal)"}
```

### 2.2 Kök neden — kesin ve tek cümlelik

`_exit_fill_yamasi`'nin **"bacak" kolu, dolumu YALNIZ GİRİŞ BRACKET'ININ parent'ında arar**
(`by_coid[plan_id]` → `alpaca.exit_fill_price(parent)` → `parent["legs"]`). NUE'nin girişteki
koruma bacakları **2026-08-06T20:02'de ölmüştür** (biri `expired`, biri `canceled`); pozisyonu
gerçekten kapatan emir, **08-09'da AYRI bir emir olarak yeniden gönderilen** koruma OCO'sunun
(`P-KORUMA-20260809-0835-NUE`, olay: `koruma_oco_gonderildi`, `onaylayan="pano-oturumu"`)
kardeş bacağıdır. Bu emir, giriş parent'ının `legs` listesinde YOKTUR — dolayısıyla yama onu
hiçbir turda göremez ve her turda aynı dürüst nedeni yazıp `tries`'ı artırır.

Karşılaştırma HUM ile kanıtlıyor: HUM'un dolan satış emri, girişin ÖZGÜN bracket'ının bacağıydı
(giriş 13:36:52, çıkış 13:37:47 — koruma yeniden gönderilmeye vakit kalmadan) ve yama BAŞARILI
oldu. Yani ayrışma emrin türünde değil, **hangi emrin bacaklarına bakıldığındadır.**

Pencere sorunu DEĞİL (elenmiş varsayım): `broker_reconcile.json → emir_penceresi` =
`{"kapsandi": true, "en_eski": "2026-07-14", "hedef": "2026-08-19", "n_emir": 28}` — ölçüm anında
pencere hedefi kapsıyordu; sorun aramanın YERİDİR, derinliği değil.

### 2.3 Etkisi ve yaygınlığı

* Kuyruk `tries=3`, tavan `EXIT_FILL_MAX_TRIES=5`. **İki tur sonra VAZGEÇİŞ'e düşecek**: satıra
  `alpaca_fill_beyan` (dürüst "ÖLÇÜLEMEDİ") yazılacak, `alpaca_fill_price` hiç açılmayacak. Yani
  bugün "eksik" olan şey, iki tur sonra "kalıcı olarak ölçülemedi" damgası alacak — oysa gerçek
  dolum broker'da apaçık duruyor.
* Ölçülmeyen sapma: iç `exit=257,2746` ↔ broker `256,7632` → **%0,199 (≈20 bps)**. Bu, alarm
  eşiğinin (`loop.MIRROR_DRIFT_TOL = 0,005` = %0,5) ALTINDADIR — yani yama koşsaydı alarm
  üretmezdi ama `alpaca_fill_price`/`mirror_divergence` alanları DOLARDI. Kaybedilen şey bir
  alarm değil, cf↔gerçek sadakat ölçümünün girdisidir.
* **Kapsam ölçüldü:** `kaynak="live_paper"` 8 kapalı işlemin **3'ünde** `alpaca_fill_price` yok:

  | Yamalı (5) | Yamasız (3) |
  |---|---|
  | T00099 MRK · T00100 MRNA · T00101 HUM · T00102 MRVL · T00103 LLY | **T00096 ALL** (08-07) · **T00097 VLO** (08-10–11) · **T00098 NUE** (08-06–19) |

  Yani cf↔gerçek sadakat yüzeyi canlı işlemlerin **%37,5**'ini görmüyor. (ALL ve VLO bu raporun
  kapsamı dışında — aynı sınıfa mı düştükleri ölçülmedi, bu bir AÇIK KALEMdir.)

---

## 3. Düzeltme önerileri (UYGULANMADI — karar Rol-1'de)

### Ö1 — Çıkış yamasına KORUMA-EMRİ KOLU (NUE sınıfını kapatır)

Kuyruk kaydı bugün yalnız `plan_id` biliyor. Koruma OCO'su gönderilirken kimliği ZATEN üretiliyor
ve olaya yazılıyor (`koruma_oco_gonderildi.plan_id = "P-KORUMA-YYYYMMDD-HHMM-TICKER"`). Öneri:
o kimliği kuyruk kaydına da düşürmek (`exit_fill_pending[pid]["koruma_coid"]`, liste hâlinde —
koruma birden çok kez yeniden gönderilebilir) ve "bacak" kolunun arama sırasını
`giriş parent → kayıtlı koruma coid'leri` yapmak. Bu, ad-tahminine (`P-KORUMA-*-{TICKER}`
desen taraması) dayanmayan, KAYITLI kimliğe dayanan bir bağdır.

*İkinci en iyi (kayıt yoksa, geriye dönük vakalar için):* pencerede aynı sembolün SATIŞ yönlü,
`filled`, `updated ≥ ts_open` olan emirlerini tarayıp TEK aday varsa onu kullanmak; **birden çok
aday varsa ölçülemedi demek** (uydurma eşleme yasağı).

### Ö2 — `dolum_ts`i çıkış yamasında OKUYUCUYA bağlamak (HUM sınıfını görünür kılar)

E-kod [5] ile `_exit_fill_yamasi` artık `dolum_ts` yazıyor ama okuyucusu henüz yok. Öneri: ayna
dolum zamanı ile `ts_close` arasındaki fark ≥ 1 işlem günü ise adlı bir sapma üretmek (ör.
`drift_sinifi="zaman_ayrismasi"`), böylece HUM vakası `mirror_exit_fill_patched` olayının içinde
sessizce geçmek yerine kendi adıyla defterlenir. **Not:** bu bir GÖRÜNÜRLÜK önerisidir —
`ts_close`u broker zamanına ÇEKMEK ayrı ve çok daha ağır bir karardır (iç motorun P&L/bar
muhasebesini yeniden yazar) ve bu raporda ÖNERİLMEZ.

### Ö3 — `ONAYLI_PLAN_GONDERILMEDI` alarmının metnini ayrıştırmak

Alarm 08-17'de "Alpaca'da NE EMİR NE POZİSYON var" dedi; gerçek "pozisyon AÇILDI ve AYNI GÜN
KAPANDI" idi. İki hâl aynı gözlemi (şu an boş) üretiyor ama TAMAMEN farklı iş kalemleri:
biri gönderim arızası (VLO sınıfı), diğeri normal bir kapanış. Öneri: alarmdan önce sembolün
KAPALI emir geçmişine bakıp "hiç emir yok" ile "emir var, terminal" hâllerini ayırmak.

### Ö4 — Kapsam kalemi: ALL (T00096) ve VLO (T00097)

Bu iki yamasız satırın NUE ile aynı sınıfa mı düştüğü ÖLÇÜLMEDİ. Ö1 uygulanırsa geriye dönük
yamalanıp yamalanmadıkları tek başına bir doğrulama olur.

## 4. Ne YAPILMADI

* Hiçbir kod düzeltmesi yapılmadı (brief: teşhis + öneri).
* Canlıda hiçbir dosya yazılmadı; `exit_fill_pending` kuyruğuna dokunulmadı — NUE kaydı `tries=3`
  ile yerinde duruyor.
* HUM/NUE satırlarının `ts_close`/`qty`/`entry` alanlarına dokunulmadı.

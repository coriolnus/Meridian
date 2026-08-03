# WP-D KALEM 1 — BULGU-1 (hayalet-satır hacim-şartı kaçağı) BAĞIMSIZ TEYİDİ

**Tarih:** 2026-08-03 · **Rol:** ölçüm ajanı (WP-D turu) · **Hüküm sahibi:** Rol-1
**Cevaplanan ROADMAP satırı:** §WP-D "DOĞRULANACAK (EDG-009 yan gözlemi): 2026-07-30 BULGU-1 …
depo kapısı GILD/CMCSA/DLTR/UNP satırlarını kendisi karantinaya alıyor **görünüyor**; Rol-1
bağımsız teyidi bekliyor."

## HÜKÜM: TEYİT TAM — kaçak KAPALI, karantina-genişletme kalemi KAPANMA ÖNERİSİYLE geliyor

Dört vakanın dördü de bugünkü depo kapısında **KARANTİNAYA** düşüyor; ESKİ (2026-07-30 öncesi)
kural dördünü de **KAÇIRIYOR**. Evren geneli yeniden üretimde bugünkü kural gerçek sınıfın
**13/13'ünü** yakalıyor, eski kural **3/13**.

### Ölçüm disiplini notu
Bu bir **kart gerektiren ölçüm değildir**: hipotez yok, eşik yok, K'ya sayılmaz, strateji-edge
iddiası yok. Yapılan iş, halihazırda SEVK EDİLMİŞ bir kapının (`data._unadjusted_mask`) iddia
edilen davranışını, ESKİ kuralı yeniden inşa edip yan yana koyarak **yeniden üretmektir**
(determinizm/teyit sınıfı). Eşikler ölçümden okunmadı, koddaki sabitlerden alındı.

### Salt-okunurluk beyanı
`MERIDIAN_ROOT` kum havuzuna (`scratchpad/wpd_sandbox`) alındı; `obs.warn` ve `store` yazımları
oraya düştü. Yerel bar arşivi (`state/bars/*.csv`) **yalnız pandas ile okundu**, hiçbir üretim
dosyası değiştirilmedi. Canlı sisteme (A1) hiç dokunulmadı.

---

## 1. Vaka teyidi — BULGU-1'in adını verdiği dört satır

**Komut**
```
cd <sandbox> && /Users/erdemozturk/AI-Trading/.venv/bin/python teyit1.py
```
(betik: `teyit1.py`, ham çıktı: `sonuc_vakalar.json`)

| sembol | tarih | r (kapanış oranı) | ertesi bar geri (back) | drr = \|r·back−1\| | kademe | ESKİ kural | YENİ kural | `sanitize_bars` hükmü |
|---|---|---|---|---|---|---|---|---|
| GILD  | 2013-12-18 | 2,1005 | 0,4989 | 0,0479 | 1 (strict) | **kaçırdı** | yakaladı | **KARANTİNA** |
| CMCSA | 2013-12-18 | 2,0502 | 0,5051 | 0,0355 | 1 (strict) | **kaçırdı** | yakaladı | **KARANTİNA** |
| DLTR  | 2012-06-26 | 2,0263 | 0,4819 | 0,0236 | 1 (strict) | **kaçırdı** | yakaladı | **KARANTİNA** |
| UNP   | 2014-06-06 | 2,0152 | 0,5060 | 0,0197 | 1 (strict) | **kaçırdı** | yakaladı | **KARANTİNA** |

**HANGİ KURAL, NEDEN.** Dördü de `_unadjusted_mask`in **KADEME 1**'inden geçiyor
(`drr < UNADJ_STRICT_REVERT_TOL = 0,05` → fiyat kanıtı TEK BAŞINA hüküm). Eski kuralın vetosu
tam da burada ısırıyordu: hacim TERS-ORANLI imzası (`|r·(v/v₋₁)−1| < 0,10`) hiçbirinde YOK —
ölçülen değerler 0,5356 (GILD) · 0,7286 (CMCSA) · 0,4600 (DLTR) · 0,1838 (UNP). Sağlayıcı ham
fiyatı **düzeltilmiş hacimle** eşleştirdiği için hacim "tutarlı" görünüyor ve satır geçiyordu.

**Satırlar HÂLÂ DİSKTE** (`state/bars/gild.csv` vb.) — kapı bellek-içi çalışır, disk ancak bir
sonraki yazımda ya da `barrepair --uygula` ile temizlenir (belgeli davranış). Yani teyit
"satır silinmiş" değil, "**kapı satırı adjudike ediyor**" iddiasını sınadı ve doğruladı.

**Defterle karışmıyor:** `bars_integrity` güvenli başlangıçları GILD/CMCSA `2006-01-04`,
UNP `2006-10-25`, DLTR `None`. Yani 2012-2014 tarihli bu satırları düşüren şey **DÖNEM dışlaması
değil, KARANTİNA kuralıdır** — iki mekanizma birbirini maskelemiyor.

**Yan gözlem (kusur değil, davranış):** çıktıda CMCSA için `bar_unadjusted_row_quarantined`
olayı YOK. Sebep belgeli: olay **tarih başına BİR kez** atılır (`_QUAR_EVENTED`), GILD aynı
2013-12-18 tarihini önce yakmış. Sayaç (`ghost_report`) yine ikisini de sayıyor.

---

## 2. Evren geneli yeniden üretim — sınıfın genişliği

**Komut**
```
cd <sandbox> && /Users/erdemozturk/AI-Trading/.venv/bin/python teyit1b.py
```
(betik: `teyit1b.py`, ham çıktı: `sonuc_evren.json`)

Yerel arşivin tamamı, **takvim kapısı uygulandıktan sonra** (BULGU-1 ölçümü "geçerli-seans satırı"
üzerindeydi):

| ölçüm | teyit koşusu (2026-08-03) | `data.py` docstring'inin iddiası (2026-07-31) |
|---|---|---|
| defter | 259 | 259 |
| ham satır | 1.344.332 | — |
| geçerli-seans satırı | **1.343.892** | 1.343.892 ✅ |
| (a) \|r−1\| > %35 | **216** | 216 ✅ |
| (a&b) sıçra-ve-geri-dön = gerçek hayalet sınıfı | **13** | 13 ✅ |
| (a&b&c) ESKİ kuralın karantinaya aldığı | **3** | 3 ✅ |
| YENİ kuralın karantinaya aldığı | **13** | — |

- **Eski kuralın kaçırdığı: 10/13 = %76,9.** Bu, docstring'in "%77" rakamını birebir yeniden üretir.
- **Yeni kuralın kaçırdığı: 0/13 = %0.**
- **Yeni kural eski kuralın ÜST KÜMESİ:** eskinin yakalayıp yeninin kaçırdığı satır **0**.
- **Yanlış-pozitif:** (a) havuzundaki 203 geri-DÖNMEYEN kalıcı-adım satırının **0'ı** damgalandı
  (13 = 13, yani yeni kural sınıfın dışına taşmadı). Kalıcı dikişler satır olarak değil,
  `bars_integrity` defterinde DÖNEM olarak damgalanıyor — tasarım gereği.

**Eski kuralın kaçırdığı 10 satır (tamamı):**

| sembol | tarih | r | drr |
|---|---|---|---|
| ALB | 2006-10-30 | 0,5154 | 0,0311 |
| AVGO | 2008-06-12 | 2,0000 | 0,0000 |
| CMCSA | 2013-12-18 | 2,0502 | 0,0355 |
| DLTR | 2012-06-26 | 2,0263 | 0,0236 |
| GILD | 2013-12-18 | 2,1005 | 0,0479 |
| PINS | 2013-08-02 | 0,5758 | 0,0303 |
| TDG | 2011-12-01 | 1,6563 | 0,0625 |
| TDG | 2011-12-09 | 1,7378 | 0,0854 |
| TDG | 2013-12-18 | 0,5985 | 0,0310 |
| UNP | 2014-06-06 | 2,0152 | 0,0197 |

BULGU-1'in adını verdiği dördü bu listede; kalan altısı aynı sınıfın o gün sayılmamış üyeleri.

---

## 3. ROADMAP metniyle bir SAYI UYUŞMAZLIĞI (düzeltme önerisi)

ROADMAP §WP-D ve mühendislik günlüğü satır 527 kaçağı **"%29"** diye anıyor
("gerçek hayalet sınıfının %29'unu kaçırıyor (10 kaçak …)"). İki ölçüm de — 2026-07-31 tarihli
üretim docstring'i ve bugünkü bağımsız koşu — aynı paydada **%76,9** (10/13) veriyor. Kaçak
satır SAYISI (10) her iki metinde de aynı; yanlış olan yalnız **pay**. Öneri: ROADMAP/günlük
metninde "%29" → **"%77 (10/13)"**. (Hüküm Rol-1'de; bu ajan doküman/hüküm satırına dokunmadı.)

---

## 4. KAPANIŞ ÖNERİSİ (Rol-1'e)

1. **§WP-D "DOĞRULANACAK (EDG-009 yan gözlemi)" maddesi → KAPANIR.** Teyit bağımsız, tam ve
   üretilebilir; kanıt bu dizinde (betik + ham JSON + bu rapor).
2. **"Karantina hacim-şartı genişletmesi (GILD-sınıfı %29 kaçak)" kalemi → KAPANIR.**
   Genişletme 2026-07-31'de zaten sevk edilmiş (`_unadjusted_mask` yeniden tasarımı: hacim şartı
   VETO değil ZAYIFLATICI, iki kademeli); bu tur **yama uygulamadı** çünkü uygulanacak bir kaçak
   kalmamış. Ölçülen kalan kaçak: **0/13**.
3. **Metin düzeltmesi:** yukarıdaki %29 → %77 (10/13).
4. **AÇIK KALAN (bu kalemin kapsamı dışı, ayrı bilet):** karantinaya alınan 13 satır DİSKTE
   duruyor; türetilmiş artefaktların (component_ic / cf / eşik eğrileri) temiz tabanla yeniden
   üretimi WP-D'nin ayrı maddesidir ve bu teyitle kapanmaz.

## Yeniden üretim
```
mkdir -p <sandbox>/state
cp state/bars_integrity.json <sandbox>/state/
cp research/olcumler/wpd_bulgu1_teyit/teyit1.py  <sandbox>/
cp research/olcumler/wpd_bulgu1_teyit/teyit1b.py <sandbox>/
cd <sandbox> && /Users/erdemozturk/AI-Trading/.venv/bin/python teyit1.py
cd <sandbox> && /Users/erdemozturk/AI-Trading/.venv/bin/python teyit1b.py
```
Betikler `MERIDIAN_ROOT`u kendi dizinlerine sabitler; üretim `state/`ine yazmazlar.

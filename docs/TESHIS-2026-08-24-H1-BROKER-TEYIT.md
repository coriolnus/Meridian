# TEŞHİS — H1 `broker_teyit` damgası: **ARIZA YOK, KOŞMA FIRSATI YOK**

**Tarih:** 2026-08-24 · **Rol:** Rol-1 · **Kalem:** H1 (`docs/ACIK-KALEMLER-DOGRULANMIS-2026-08-24.md`
§2.1 — "en değerli grup"un birinci sırası, `Ö-54`/K2-K3'ün önündeki tek engel diye kayıtlı)
**Sonuç:** kalem **iş İSTEMİYOR**; bir reconcile turu bekliyor. Kod DEĞİŞTİRİLMEDİ.

## 1 · Tahtanın sorusu

> "Teşhis: `EXE-2026-007`/`Ö-52` dağıtıldığı hâlde damga neden defterde yok?" (boyut: **orta**)

Soru bir arıza varsayıyordu. Yoktu.

## 2 · Ölçüm — iki tarih yan yana konunca kalem çözülüyor

| olgu | değer | kaynak |
|---|---|---|
| `_defter_teyit_yamasi` ağaca girdi | **2026-08-22** | `git log -S` → `55d72b3` |
| SON reconcile koşumu | **2026-08-21 20:32:30Z** | canlı `state/broker_reconcile.json` (`updated`) |

**Damga kodu, son reconcile'dan BİR GÜN SONRA doğdu.** Aradaki 08-22/08-23 hafta sonu (seans yok),
08-24 Pazartesi ise bu ölçüm yapılırken henüz açılmamıştı (12:20Z; açılış 13:30Z).

Doğrulayıcı üç kontrol (canlı, salt-okuma):
* `_defter_teyit_yamasi` canlı `loop.py`de **VAR** (tanım + çağrı = 2 eşleşme), `teyit_stamp` da var.
* `defter_teyit_yamasi_dusdu` uyarısı 7 günde **0** — yani yama düşmedi, hiç çağrılmadı.
* `broker_reconcile.json` `emir_penceresi` taşıyor ama `defter_teyit` anahtarı **yok**; ikisi de
  aynı reconcile turunda yazılır, yani o tur damga kodundan ÖNCEKİ sürümle koşmuş.

## 3 · Elenen hipotezler (sırayla, hepsi ölçümle)

1. ~~"Yazım yolu kanonik değil (JSONL yazıyor ama defter SQLite)"~~ — `store.read_jsonl`/
   `write_jsonl` `db_backed(name)` ile DB'ye yönleniyor; yol sağlam.
2. ~~"Satırlar `kaynak` damgası taşımıyor, `teyit_of` kapsam_disi diyor ve sessizce atlanıyor"~~ —
   canlı defterde **8 satır `live_paper`** damgalı; koruma cümlesi atlamıyor.
3. ~~"Yama bir istisnayla düşüyor"~~ — 7 günde sıfır `defter_teyit_yamasi_dusdu`.
4. ✅ **"Kod dağıtıldı ama reconcile o günden beri hiç koşmadı."**

## 4 · SINANABİLİR ÖNGÖRÜ (bir sonraki reconcile turundan sonra)

Sekiz `live_paper` satırın hepsi damga için UYGUN — ölçüldü:

| ticker | ts_open | plan_id |
|---|---|---|
| ALL · VLO · NUE · MRK · MRNA · HUM · MRVL · LLY | 2026-08-06 … 2026-08-20 | sekizinde de VAR |

Pencere `en_eski: 2026-07-14`, `kapsandi: True` → sekizi de pencerenin İÇİNDE ve `plan_id`
taşıyor. Yamanın üç dalından ikisi (plan_id yok · pencere kırpık) **hiçbirinde tetiklenmez**.

**Öngörü:** bir sonraki tam reconcile turundan sonra
1. `broker_reconcile.json` bir `defter_teyit` anahtarı taşır,
2. sayaçların toplamı **8**'dir,
3. sekiz satırın `broker_teyit` alanı `teyitli` ya da `karsiliksiz` olur — **hiçbiri
   `olculemedi` DEĞİL**.

Öngörü tutmazsa bu teşhis DÜŞER ve (4)'ün yerine gerçek bir arıza aranmalıdır.

## 5 · Tahtaya etkisi

H1 "orta boy hazır iş" ve "`Ö-54` K2/K3'ün önündeki tek engel" diye kayıtlıydı. **Boyutu
sıfır**: yazılacak kod yok, koşulacak betik yok. `EDG-2026-042` K2/K3'ün ölçülebilir n'i
0'dan **8'e kadar** çıkacak — ama kaçının `teyitli` çıkacağı ÖLÇÜLMEMİŞTİR ve buraya bir sayı
yazmak uydurma olurdu (kartın kill kriteri: teyitsiz satır kıyasa girmez).

**YAPILMADI (bilinçli):** reconcile ELLE tetiklenmedi. Canlı sistemde bir turu zorlamak, o turun
kendi kadansını (B7b) ve emir penceresi sayfalamasını atlatır; kalem zaten kendiliğinden
çözülüyor ve beklemenin bedeli bir seans.

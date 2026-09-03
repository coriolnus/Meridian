# PLAN (H2) — 23c dinlenen limit sadakati ölçümü

**Kart (H1):** `research/cards/EXE-2026-005-dinlenen-limit.yaml` · status `registered` (eşikler DONDU)
**Aşama:** H1 → **H2 (bu belge)** → H3. Kod H3'te yazılır; bu belge onun sözleşmesidir.
**Rol:** ölçüm ajanı karta DOKUNMAZ; hükmü Rol-1 işler.

## 0 · Ön-koşullar — ÖLÇÜLDÜ (2026-08-17)

| şart | kaynak | durum |
|---|---|---|
| temiz ağaç (EDG-033 dersi) | `git status` | ✅ temiz |
| A kolu tabanı mevcut | `research/olcumler/edg032b_tamsatir_2026-08-13` | ✅ var |
| `low` alanı erişilebilir | `backtest.py::replay` çağrısı `per[t].loc[d, "open"]` geçiyor → **tam bar satırı elde** | ✅ ek veri ÇEKİLMEYECEK |

## 1 · Tek gerçek risk: dolum kuralının İKİ YERE düşmesi

Kart bunu **kill kriteri** yapıyor: *"dolum kuralı İKİ yerde uygulanırsa (canlı ↔ replay ayrışması)
geçersiz."* Ölçülen durum bu riski somutlaştırıyor:

`next_open` **adı** yalnız `broker.py`'de geçiyor — ama `fill_entry`'nin **ALTI çağıranı** var:

| çağıran | ne geçiyor | sınıf |
|---|---|---|
| `backtest.py::replay` | `per[t].loc[d, "open"]` | **REPLAY — kartın konusu** |
| `loop.py:1407` | `_open` | **CANLI — DOKUNULMAZ** |
| `shadow_lifecycle.py::step` | `bar["open"]` | gölge |
| `intraday_shadow.py:343` | `sim_price` | gölge (gün-içi) |
| `mutation.py:223` | `px` | mutasyon taraması |

Yani "tek yüzey" bugün **fonksiyon düzeyinde** doğru, **çağrı düzeyinde** değil.

### KARAR: kural `fill_entry` İÇİNDE tek yerde yaşar, davranışı ÇAĞIRAN seçer

`fill_entry`ye opsiyonel bir `bar_low: float | None = None` parametresi eklenir. Kural TEK yerde
(`fill_entry` gövdesi) uygulanır:

```
bar_low verilmemişse  → BUGÜNKÜ davranış, BİT-ÖZDEŞ (yalnız açılışta sına)
bar_low verilmişse    → dinlenen limit: low <= limit ise limit fiyatından dolar
```

**Neden `if replay:` bayrağı DEĞİL:** bir "mod" bayrağı motorun içine iki davranış gömer ve
hangisinin koştuğu çağrı yığınına bağlı olur — kartın yasakladığı ayrışmanın tam tanımı. Parametre
ise **veri**dir: `bar_low` yoksa kural uygulanamaz, çünkü bilgi yoktur. Canlı yol (`loop.py`)
parametreyi GEÇMEZ ve bu bir tercih değil bir OLGUdur — canlıda "bugünün low'u" karar anında
bilinmez. Böylece canlı davranışın değişmezliği **yapısal** olur, disiplinle korunan bir söz değil.

**DOKUNULMAYACAK ÇAĞIRANLAR (5/6):** `loop.py` · `shadow_lifecycle.py` · `intraday_shadow.py` ·
`mutation.py` — hiçbiri `bar_low` geçmez, hiçbirinin davranışı değişmez. **Tek değişen çağıran
`backtest.py::replay`.**

## 2 · İki kol

| kol | çağrı | beklenti |
|---|---|---|
| **A — ŞASİ KONTROLÜ** | `bar_low` GEÇİLMEZ | `edg032b` ile **BİT-ÖZDEŞ**. Değilse **ÖLÇÜM DURUR** (kart kill kriteri: şasi bozuk, hüküm verilmez). K'ya hücre olarak SAYILMAZ. |
| **B — DİNLENEN LİMİT** | `bar_low` geçilir | ölçülecek kol |

## 3 · Uygulama sırası (H3 — TEST ÖNCE)

HAT'ın H3 kapısı: **çivi önce.** Sıra bağlayıcıdır:

1. **Çivi yaz, KIRMIZI gör:** (a) `bar_low=None` → bugünkü davranış bit-özdeş; (b) `low <= limit` →
   limit fiyatından dolar; (c) **`low > limit` → DOLMAZ** (kart: "bar aralığının DIŞINDA dolum
   uydurma dolumdur" — kill kriteri); (d) canlı çağıranların hiçbiri `bar_low` geçmiyor (kaynak
   taraması, `test_ogrenme_birimi_ayrimi_v249` desenindeki gibi).
2. `fill_entry`ye `bar_low` ekle → çiviler YEŞİL.
3. `backtest.py::replay` içindeki çağrıyı tek satırda `bar_low` geçecek şekilde bayrakla (A/B).
4. **A kolunu koş → `edg032b` ile bit-özdeşlik SINA. Geçmezse DUR.**
5. B kolunu koş.

## 4 · Ölçülecek üç ürün (kartın lafzı — değiştirilemez)

- **Ö1 ABARTININ BÜYÜKLÜĞÜ:** bugünkü kuralın "kaçtı" dediği işlemlerin **yüzde kaçı** dinlenen
  limitle doluyor. → `EXE-2026-001-R2`nin K1 şerhinin gücü budur.
- **Ö2 İŞARET SINAMASI:** o işlemlerin ort-R'si POZİTİF mi? (E1 grid "kaçanlar sistematik KAZANAN"
  demişti.) CI ile raporlanır.
- **Ö3 PORTFÖY ETKİSİ:** ΔP&L + CI (eşlenik ay-kümeli bootstrap **B=5000, seed 20260812**) +
  **yan-kanal ayrıştırması** (dolan işlemler slot/ısı tükettiği için hangi işlemler yerinden oldu —
  EDG-030/039 deseni: etki TOPLAMSAL DEĞİLDİR) → sente kapanmalı.

**Ö1 > %20 ise:** `EXE-2026-001-R2` K1 şerhi KALKMAZ, hüküm yeniden ölçülmek üzere AÇILIR (ayrı kart).

## 5 · Bu kart bir TERCİH yapmaz

Kartın ölçümden ÖNCE yazılmış en önemli cümlesi ve H3'te unutulmaması gereken:

> *"B kolu bir SADAKAT düzeltmesidir… **ΔP&L NEGATİF çıksa bile sadakat düzeltmesi GEÇERLİDİR.**"*

Yani sonuç kötü çıkarsa kural geri alınmaz — gerçek bir limit emri gün boyu dinler, replay bunu
yansıtmalıdır.

## 6 · Beyanlı sınırlar (kartın `beyanlı_sinirlar`ından — raporda AYNEN yer alır)

1. **Günlük bar sırayı söylemez.** Aynı gün hem stop hem limit dokunmuşsa hangisi önce ÖLÇÜLEMEZ →
   kötümser tarafa yazılır (`broker.py`nin kendi "bar içi — sıra bilinemez, stop önce" emsali).
   **Bu ölçüm bile hâlâ bir ALT SINIRDIR.**
2. 23d'yi (bar-içi stop `eff_stop`ta dolmuş sayılıyor, stop slipajı SIFIR) **ÇÖZMEZ**. 23c kapanınca
   asimetrinin yarısı kapanır ve kalan yarı DAHA görünür olur.
3. 23e (gün-içi pencere) bugünkü replayde MODELLENEMEZ (`timeframe=1Day` tek yol) — kapsam DIŞI.

## 7 · Neden bu turda H3'e geçilmedi

Ön-koşullar ölçüldü, kanonik yüzey bulundu, kill riski (altı çağıran) somutlaştı ve çözümü yazıldı.
H3 iki tam replay koşumu + bit-özdeşlik doğrulaması ister; yarım bırakılırsa motorda **ikinci bir
dolum yolu** kalır — kartın kendi kill kriteri. Plan bu yüzden H2'de kapatıldı ve icra ayrık bir
tura bırakıldı.

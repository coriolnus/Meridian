# ⑤ RETIRED_SYMBOLS çapraz-doğrulama — üç bağımsız kaynak (2026-08-09, Rol-1)

**Amaç:** EDG-2026-021 delist tespitini bir **vekille** (yerel üyelik-dosyası kaybolması) yapmıştı.
Bu tur o vekili **gerçeğe** taşır: `RETIRED_SYMBOLS` beyanı, yerel SP500 üyelik dosyası ve
**bağımsız bir delist otoritesi** (Massive `delisted_utc`) üç ayrı kaynakta karşılaştırılır.
Bu bir **olgu-denetimi** (kart gerekmez, keşif hükmü — `docs/KESIF-WP-QC-2026-08-09.md:129`);
bir emeklilik kararını çelişki AÇARSA ROADMAP'e yazılır (açmadı — aşağıda).

## Üç kaynak

- **Kaynak-1 — beyan:** `RETIRED_SYMBOLS` (`meridian/adapters/data.py:2606`), 8 kalem, delist tarihi + neden.
- **Kaynak-2 — yerel vekil (kanıtla-doğrulandı):** `research/pit_universe/sp500_uyelik_tarihi.csv`
  (2.718 satır, 1996→2026-06-30). Her sembolün üyelikte SON görülme tarihi delist gününden ÖNCE mi.
- **Kaynak-3 — bağımsız otorite:** Massive `/v3/reference/tickers?ticker=X&active=false` → `delisted_utc`.
  Vekil DEĞİL; borsa delist tarihinin kendisi.

## Mutabakat tablosu

| sembol | RETIRED delist (beyan) | yerel üyelik son görülme | Massive `delisted_utc` | mutabakat |
|---|---|---|---|---|
| ANSS | 2025-07-18 | 2025-07-09 | 2025-07-18 | **3/3** ✓ |
| DFS  | 2025-05-19 | 2025-03-24 | 2025-05-19 | **3/3** ✓ |
| FI   | 2025-11-11 | 2025-11-04 | 2025-11-11 | **3/3** ✓ |
| HES  | 2025-07-21 | 2025-07-18 | 2025-07-21 | **3/3** ✓ |
| IPG  | 2025-11-28 | 2025-11-11 | 2025-11-28 | **3/3** ✓ |
| K    | 2025-12-12 | 2025-11-28 | 2025-12-12 | **3/3** ✓ |
| PARA | 2025-08-08 | 2025-07-23 | *(0 kayıt)* | **2/3** — Massive boşluk |
| WBA  | 2025-08-29 | 2025-08-08 | 2025-08-29 | **3/3** ✓ |

**Okuma:**
- **Massive delist otoritesi 7/8'i RETIRED beyanıyla BİREBİR doğruladı** (gün-güne aynı). Vekil → gerçek taşındı.
- **Yerel üyelik 8/8 tutarlı:** her sembol delist gününden birkaç gün-hafta ÖNCE üyelikten düşmüş (beklenen).
- **Sembol-değişimi yerelde de görünür:** FISV, FI'nin son satırından (2025-11-04) sonra 2025-11-11 satırında
  beliriyor; PSKY, PARA sonrası. Yani sembol-devir otoritesi yalnız QC'de değil, yerel üyelikte de var.
- **PARA — tek boşluk (dürüstçe):** Massive `active=false` ile 0 kayıt döndü. Muhtemel neden PARA→PSKY
  (Skydance birleşmesi) devrinde Massive'in kaydı halefe taşıması. **ÖLÇÜLEMEDİ (Massive'de) — "doğrulandı"
  denmez.** Yerel üyelik (07-23 son < 08-08 delist) + RETIRED beyanı tutarlı; üçüncü otorite eksik.

## Hüküm

- **Hiçbir emeklilik kararı ÇELİŞMEDİ** — çakışma-istisnası (Security Master tarih/neden çelişkisi) TETİKLENMEDİ.
  8 kararın 7'si üç bağımsız kaynakta birebir; PARA ikisinde tutarlı (üçüncüde boşluk, çelişki değil).
- EDG-021'in vekil-tespiti bu turda **gerçek delist otoritesine (Massive) 7/8 oturdu.**

## Kalan tek adım — OPERATÖR (QC hesabı: FREE, Fat Apricot Koala)

**1-hücrelik QC Security Master fizibilite sondası** (keşif `docs/KESIF-WP-QC-2026-08-09.md:125-128`):
FREE planda `Delisting` olayı / Security Master delist-otoritesi sorgulanıyor mu? Evetse ⑤ trivial olarak
kapanır (8 sembol deterministik) **ve PARA'nın üçüncü-kaynak boşluğu da QC'de kapatılır.** Massive zaten
7/8'i bağımsızca doğruladığı için bu sonda artık bir *teyit*, bir *bilinmeyen* değil.

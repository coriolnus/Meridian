# TSK-020 [UYGULA-3] — bars→Parquet arşivi + DuckDB okuma yüzeyi — uygulama planı

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. Steps use checkbox syntax.

**Goal:** `state/bars/*.csv` canlı önbelleğini DEĞİŞTİRMEDEN, ay/sembol bölümlü tipli Parquet arşivi (`ops/bar_arsivle.py`) ve DuckDB okuma
yüzeyi (`ops/bar_sorgu.py`) kurmak — strangler; canlı okuma yolu (3.3) BU PLANIN DIŞI (ayrı kart/karar).

**Spec:** `docs/TASARIM-BARS-PARQUET-DUCKDB-2026-09-06.md` §3.1–3.2, §4, §6 (S2+S3). Operatör: "konsolide plana otonom devam" (2026-09-07 13:1xZ);
§5-1 sıra sorusu bu yetkiyle çözüldü (şimdi), §5-2 → 3.3 ayrı kart (Rol-1 hükmü).

## Global Constraints
- pyarrow YOK (yerel + A1 ölçüldü 2026-09-07): Parquet yazımı/okuması DuckDB ile (`COPY … TO … (FORMAT PARQUET)` / `read_parquet`) — `ops/olay_sikistir.py`
  hangi mekanizmayı kullanıyorsa AYNISI; yeni bağımlılık EKLENMEZ.
- `meridian/` dosyalarına DOKUNULMAZ; yalnız `ops/` + `tests/`. `sanitize_bars`, takvim kapısı vb. `meridian.adapters.data`dan İTHAL edilir, kopyalanmaz.
- Değişmezler (spec §3.1): CSV SİLİNMEZ · ay bazında parquet satır == sanitize sonrası CSV satırı, fark → rc 5 · varsayılan KURU, `--uygula` yazar ·
  idempotent (manifest sha eşitse atlar; `--zorla` yeniden yazar) · worker koşarken güvenli (CSV yalnız okunur; hedef dizin `state/barlar/`, yazım
  önce geçici dosya sonra rename) · manifest `state/barlar/manifest.json` {sembol: {ay: {sha256, satir}}} + üretim damgası (utc, araç sürümü).
- Şema: date DATE · open/high/low/close DOUBLE · volume BIGINT · `kaynak` VARCHAR · `ayarlama_olcegi` DOUBLE. CSV'de olmayan sütun UYDURULMAZ:
  ölçülüp yoksa NULL + manifest'e `eksik_sutunlar` beyanı + raporda neden.
- CLAUDE.md: Yasa 4/6, çapa yasağı (`dosya.py:NNN` yok), `except` işaretli, pytest dışı betik koşumu YOK (obs canlı deftere yazar; çiviler `sandbox_state`
  + geçici dizin), `-q` verilmez, seri koşum, git yok (ajan).

## Task 1 — `ops/bar_arsivle.py` (+ `tests/test_bar_arsivle_v435.py`)
CLI: `[--kaynak-dizin state/bars] [--hedef state/barlar] [--sembol S ...] [--ay AAAA-AA] [--uygula] [--zorla] [--json]`; rc 0 ok · 5 satır-sayısı farkı ·
2 kullanım hatası · 1 girdi yok. Adımlar: (1) CSV oku → `sanitize_bars(df, ticker)` → ay parçala; (2) her (sembol, ay) için parquet (geçici → rename);
(3) doğrulama: parquet'i DuckDB ile geri oku, satır sayısı + date min/max + close toplamı CSV(sanitize) ile eşit; (4) manifest güncelle (sha256 dosya
içeriği); (5) rapor stdout (tablo) / `--json`. Kuru koşumda 1 bayt yazılmaz. Çiviler: kırmızı-önce; kuru/uygula ayrımı; satır farkı rc 5 (mutasyon:
doğrulamayı gevşet → kırmızı); idempotent (ikinci koşum "atlandı"); `--zorla`; eksik sütun beyanı; CSV dokunulmazlığı (mtime/sha eşit); manifest şeması.

## Task 2 — `ops/bar_sorgu.py` (+ `tests/test_bar_sorgu_v436.py`)
CLI: `[--dizin state/barlar] --sorgu {kapsam,dikis,bosluk} [--sembol S] [--ay AAAA-AA] [--sql "SELECT …"] [--n N] [--json]`. DuckDB bellek içi,
`read_parquet('<dizin>/*/*.parquet', hive_partitioning=false)` görünümü `barlar` (+ `sembol` sütunu dosya adından/filename). `kapsam`: sembol × ilk/son
gün × satır · `dikis`: `ayarlama_olcegi` bir önceki güne göre değişen günler (sütun NULL ise "ölçülemedi" beyanı) · `bosluk`: takvim kapısına göre eksik
seans (takvim `meridian.adapters.data`nın kullandığı fonksiyondan İTHAL; hangi fonksiyon olduğu ÖLÇÜLÜR, raporda yazılır) · `--sql`: YALNIZ tek SELECT
muhafızı `ops/olay_sorgu.py`den İTHAL (kopya değil). TSK-159/EDG-082 sorusu örnek olarak README/docstring'e: "as_of(t) üyeleri içinde barı olmayanlar".
Çiviler: her alt komut için sentetik parquet (Task-1 aracıyla üretilmiş fixture) · SELECT-dışı reddi (mutasyon) · boş dizin → rc 1 + açıklama · `--json`.

## Rapor
`.superpowers/sdd/2026-09-07-uygula3/task1-report.md` (iki görev tek rapor). Dönüş: durum, değişen dosyalar, tek satır test özeti, kaygılar.

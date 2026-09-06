# TASARIM — Günlük bar deposu: CSV-per-sembol → Parquet (ay/sembol bölümlü) + DuckDB okuma yüzeyi (TSK-020 UYGULA-3)

**Tarih:** 2026-09-06 · **Rol-1 tasarımı (H1)** · **Kod YOK — operatör sıra onayı bekler (TSK-020 sırası 4→3→1→9; 4 kapandı)** ·
**Ref:** TSK-020 [UYGULA-2] (olay defteri parquet + `ops/olay_sorgu.py` DuckDB emsali), TSK-137 (defter rotasyonu), EDG-066 tick arşivi
(zaten Parquet), `meridian/adapters/data.py` (`load_bars`/`load_many`/`sanitize_bars`/`measurement_bars`), TSK-159 (replay yeniden oynatım).

---

## 1 · Ölçülen zemin

| Ne | Değer (2026-09-06) |
|---|---|
| Depo | `state/bars/<sembol>.csv`, sembol başına tek dosya; A1 ve yerel 260 dosya / 60 MB |
| Yazıcı | `data.load_bars` — önbelleği HER ZAMAN okur, taze değilse kaynak zincirinden çeker ve tarihe göre BİRLEŞTİRİR (körce ezmez); `sanitize_bars` okuma yolunda onarır (`bar_cache_repaired` uyarısı) |
| Okuyucular | `dataset.py` (3 çağrı — canlı/eğitim veri seti), `analytics.py` (3), `api.py` (1); replay `bars` sözlüğünü çağırandan alır (`_per` = `df.set_index("date")`) |
| Debi | ~98k satır/gün sınıfı (küçük-veri rejimi — TimescaleDB gerekçesiz, karar 2026-08-31) |
| Bütünlük katmanları | takvim kapısı, düzeltilmemiş-satır karantinası, `bars_integrity`/`safe_start`, kaynak sabitleme + dikiş koruması — hepsi `sanitize_bars` boğazında, DEPO BİÇİMİNDEN BAĞIMSIZ |
| Tick arşivi | `/opt/veri/tick/{islem,kotasyon_1s}` gün parquet'leri (40 G) — Parquet zaten filoda; okuyucu DuckDB |
| Emsal | `ops/olay_sikistir.py` (jsonl → ay parquet, iki katman doğrulama, manifest, `--kirp/--zorla/--kuru`) + `ops/olay_sorgu.py` (yalnız-SELECT muhafızı, bellek içi bağlantı) |

**Neden şimdi değil, neden hiç:** CSV deposu bugün çalışıyor; 60 MB'lık veri için "performans" gerekçesi yok. Gerçek gerekçeler:
(a) `read_csv` + `sanitize_bars` her okumada onarım koşturuyor — biçim tipsiz (tarih parse, NaN 'nan' vakası, sütun sırası);
(b) PIT/replay soruları ("2024-06-24'te hangi sembollerin barı vardı", "dikiş nerede") sembol-dosyası biçiminde SQL'siz cevaplanamıyor;
(c) tick arşiviyle aynı okuma yüzeyi (DuckDB) — iki biçim, iki alet yerine bir.

## 2 · Reddedilenler
- **TimescaleDB/Postgres:** debi küçük, PIT'e ters (satır güncellenir, tarihçe silinir), yeni daemon + yedek hikâyesi (karar 2026-08-31).
- **Tek büyük Parquet:** ay/sembol bölümlemesi olmadan artımlı yazım = her gün tüm dosyayı yeniden yazmak.
- **Canlı okuma yolunu DEĞİŞTİRMEK:** `load_bars` sözleşmesi (birleştirme, onarım, kaynak zinciri) korunur; Parquet ARŞİV+okuma yüzeyidir, canlı önbellek CSV kalır (strangler — TSK-132/UIUX kuralının aynısı: iki biçim BİR süre birlikte, tek-kaynak ayrışma çivisiyle).

## 3 · Tasarım (strangler, üç adım)

### 3.1 Arşiv üretici — `ops/bar_arsivle.py` (olay_sikistir emsali)
- Girdi: `state/bars/*.csv` → `sanitize_bars` boğazından geçirilmiş çerçeve (onarım BİR kez, arşivde temiz).
- Çıktı: `state/barlar/AAAA-AA/<sembol>.parquet` (ay/sembol; tipli: date DATE, o/h/l/c DOUBLE, volume BIGINT, `kaynak` VARCHAR,
  `ayarlama_olcegi` DOUBLE — dikiş koruması sütunu) + `state/barlar/manifest.json` {sembol: {ay: sha256, satır}}.
- Değişmezler: CSV SİLİNMEZ (canlı önbellek); parquet'teki satır sayısı == sanitize sonrası CSV satırı (ay bazında doğrulama, FARK → rc 5);
  `--kuru/--uygula`; worker koşarken salt okuma güvenli (CSV'yi yalnız okur); idempotent (manifest sha eşitse atlar).
- Yasa 6 okuyucusu ilk günden: `ops/bar_sorgu.py`.

### 3.2 Okuma yüzeyi — `ops/bar_sorgu.py` (olay_sorgu emsali)
- DuckDB bellek içi, `read_parquet('state/barlar/*/*.parquet')` görünümü `barlar`; alt komutlar: `kapsam` (sembol × ilk/son gün × satır),
  `dikis` (ayarlama ölçeği değişen günler), `bosluk` (takvim kapısına göre eksik seans), `--sql` (yalnız-SELECT muhafızı aynen).
- TSK-159/EDG-082 tüketicisi: "as_of(t) üyeleri içinde barı olmayanlar" sorusu tek SQL (survivorship kapsama ölçümü).

### 3.3 Canlı yol (opsiyonel, ayrı karar) — `data.load_many` arşivden okuma
- `load_many(..., kaynak="arsiv")` bayrağı: parquet varsa oradan yükler (tipli, onarımsız), yoksa CSV. Varsayılan CSV (birebir davranış çivisi).
  Fark çivisi: aynı sembol/ay için parquet ↔ CSV(sanitize) byte-eşit (tek-kaynak yasası). Bu adım canlı davranışa dokunduğu için ayrı kart/onay.

## 4 · Bedel
| Bedel | Ölçüm |
|---|---|
| Disk | ~60 MB CSV → ~15–20 MB parquet (tahmin DEĞİL, arşivde ölçülür; olay defterinde ~50× görüldü ama barlar zaten yoğun) |
| İki biçim aynı anda | manifest + fark çivisi; CSV kaynak, parquet türev (kopya değil: türetme + ayrışma çivisi) |
| Yeni bağımlılık | DuckDB zaten var (olay_sorgu); pyarrow venv'de mi ölçülür |
| Bakım penceresi | gerekmez (salt okuma) |

## 5 · Operatör kararları
1. UYGULA-3 sırası: şimdi mi (TSK-159 ölçümü bar kapsama sorusunu SQL ile sorabilir), yoksa 1 (SQLite) ve 9'dan sonra mı?
2. 3.3 canlı okuma yolu bu kalemin parçası mı, ayrı kart mı (öneri: ayrı).

## 6 · Uygulama sırası (onay sonrası)
S1 kart yok (ölçüm değil, altyapı; ROADMAP kalemi yeter) → S2 `ops/bar_arsivle.py` + çiviler (ajan, TDD; olay_sikistir kalıbı) → S3 `ops/bar_sorgu.py`
(aynı ajan ya da ikinci) → S4 A1'de ilk arşiv + kapsam raporu (Rol-1) → S5 3.3 ayrı karar.

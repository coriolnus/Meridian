# EDG-2026-062 — PIT arşiv bağlaması: uygulama planı

> **Ajan işçiler için:** ZORUNLU ALT-SKILL: superpowers:subagent-driven-development.

**Hedef:** Tarihsel yolda (backtest.replay + cf_backfill) kazanç çapası `days_since_report`u
EDGAR 8-K arşivinden (filed damgası, muhafazakâr `filed <= seans-1` görünürlükle) çözmek —
canlı yola DOKUNMADAN. İki `pitlaw.BILINEN_IHLALLER` kaydı korumalı-zincir beyanına taşınır.

**Spec:** `research/cards/EDG-2026-062-pit-arsiv-baglamasi.yaml` (ön-kayıt, eşikler donuk) +
`meridian/pitlaw.py` beyan defterleri. Kill-list ve pozitif kontrol karttan bağlayıcıdır.

**Mimari:** Yeni `meridian/earnings_pit.py` modülü arşiv CSV'sini okur ve üç-durumlu cevap verir
(`bool | None`). Dikiş `strategy.py`nin iki evaluate fonksiyonunda **param-idiomu** ile açılır
(`entry.armed_extra` emsali: "param üzerinden aktığı için canlı döngüyle yarışmaz"). Tarihsel
çağıranlar (`backtest.py`, `cf_backfill.py`) parametreyi set eder; param yoksa canlı yol AYNEN.

## Ölçülmüş girdi gerçekleri (2026-08-31, plan yazımında)

- Arşiv: `research/edgar_facts/earnings_8k_tarihleri.csv` — 17.535 satır · 258 sembol ·
  sütunlar `symbol,cik,filed,report_date,acceptance,items,accn` · filed 2010-01-07→2026-07-31.
- `report_date` %100 dolu; `filed >= report_date` her satırda (0 negatif); %90,8 aynı gün.
- Çağrı yerleri: `strategy.py::evaluate_episodic_pivot` (max_days=2) ve
  `strategy.py::evaluate_pead` (max_days=watch_days, varsayılan 35) — ikisi de
  `from . import earnings as earn` + `earn.days_since_report(ticker, last_date, ...)`.
- Tarihsel çağıranlar: `backtest.py` (~435: `strat.scan_entry(sub.tail(340), eff, ...)`;
  earnings_gate sayaçları `_eg`, emsal `olculemedi_replay` ~518) ·
  `cf_backfill.py` (~82-83: `strat.scan_all(tail, eff, ...)` ve `strat.scan_all(tail, rx, ...)`;
  sayaç emsali `eg["olculemedi_cf"]` ~139).
- `arming._kanit_durumu` ufku YALNIZ canlı takvimden okur (`takvim_ufku()` ~2026-07-20→);
  `arsiv_yok` dalı defter (2022-01-03→) ile kıyaslar.
- Alınmış vNNN: …v340, v341, v342, v343. Bu plan v344, v345, v346 alır — **oluşturmadan önce
  çakışma grep'i zorunlu** (aynı gün üç çakışma vakası yaşandı).

## Global Constraints (tümü ölçülmüş vakalı — ihlal turu yaktı)

- Ajan GİT KOMUTU KOŞMAZ (salt-okunur dahil). Commit'leri Rol-1 atar.
- pytest DIŞINDA `meridian.obs`a ulaşabilecek hiçbir şey koşturma; davranış görmek istiyorsan
  `sandbox_state` fixture'lı çivi yaz. `monkeypatch.undo()` YASAK.
- KANONİK KOŞUM: `.venv/bin/python -m pytest tests/<dosya>` — `-q` verme.
- Satır-numaralı çapa yazma (`dosya.py:123`) — sembol çapası kullan.
- Yeşilden sonra HER çivinin hedeflediği dalı mutasyonla ısırdığını göster (bir turda 4 çivi
  yanlış sebeple yeşildi).
- `except`/fallback yalnız işaretli: `# sessiz-yutma: <≥20 karakter gerekçe>` (Yasa 4).
- Ölçülemeyen değer `None` + neden — sıfır/False ile "bilmiyorum" AYNI ŞEY DEĞİLDİR. Bu kartın
  bütün konusu bu ayrımdır.
- KİLL-LIST (karttan, dokunulamaz): canlı `days_since_report` gövdesi DEĞİŞMEZ · kısmi bağlama
  yasak · davranış değişimi raporsuz kalamaz (True sayısı raporlanır; bugünkü ölçüm: replay'de 0).
- Kart dosyasına ajan DOKUNMAZ; ölçüm hükmü Rol-1'in.

### Task 1: `meridian/earnings_pit.py` + `tests/test_earnings_pit_v344.py`

**Arayüz (sonraki görevler buna bağlı):**

```python
ARSIV_YOLU: Path  # <repo>/research/edgar_facts/earnings_8k_tarihleri.csv — modül sabiti,
                  # test enjeksiyonu monkeypatch.setattr(earnings_pit, "ARSIV_YOLU", tmp) + clear_cache()

def _arsiv_yukle() -> dict[str, list[tuple[str, str]]]:
    """SYM -> [(report_date, filed), ...]. mtime-önbellekli (earnings._load emsali).
    Biçimsiz satır SESSİZCE DÜŞMEZ: modül-içi `_dusen_satir` sayacına eklenir (Yasa 6 okuyucusu:
    arsiv_ufku() `dusen` alanında gösterir)."""

def clear_cache() -> None: ...

def arsiv_ufku() -> dict:
    """{"ilk","son","n_tarih","n_sembol","dusen","neden"} — filed sütunu üzerinden;
    boş arşivde ilk=son=None + neden (takvim_ufku emsali)."""

def days_since_report_pit(ticker: str, on_date: str, max_days: int = 2) -> bool | None:
    """ÜÇ DURUM:
    None  → ÖLÇÜLEMEDİ: on_date biçimsiz · arşiv boş · on_date > filed-max VEYA < filed-min
            (ufuk sözleşmesi: asla 'rapor yok' sayılmaz) · sembol arşivde HİÇ yok (kapsam dışı).
    True  → ∃ satır: 0 <= (on_date - report_date).days <= max_days VE filed <= on_date - 1 gün
            (muhafazakâr görünürlük: EŞİT seans günü DAHİL DEĞİL — karttan).
    False → sembol arşivde VAR, ufuk içinde, eşleşen satır yok ("rapor yok" ÖLÇÜLDÜ).
    Her çağrı sayaç günceller."""

def sayac_oku() -> dict:   # {"true": n, "false": n, "olculemedi": n}
def sayac_sifirla() -> None
```

TDD adımları (her biri kırmızı doğar): gerçek repo CSV'siyle ufuk/yükleme; sentetik tmp CSV ile
üç durumun her dalı — özellikle **geç dosyalama** (report_date=R, filed=R+5: on_date=R+1 →
False; on_date=R+6..R+35, pead penceresi → True) ve **filed==on_date → False** (eşit gün dahil
değil); biçimsiz satır `dusen`e düşer, sıfır sayılmaz; sayaç üçlüsü. Modül `meridian.obs`a
ULAŞMAZ (import zinciri temiz tutulur — çivi: `sys.modules` üzerinden obs'un yüklenmediği
doğrulanır ya da import'lar incelenir).

### Task 2: `strategy.py` dikişi + `tests/test_pit_baglama_yolu_v345.py` (bölüm 1)

`evaluate_episodic_pivot` çapa bloğu ŞU biçime gelir (evaluate_pead'de watch_days ile aynı):

```python
    if not last_date:
        return None
    if params.get("earnings.pit_arsiv"):
        from . import earnings_pit
        if not earnings_pit.days_since_report_pit(ticker, last_date, max_days=2):
            return None    # False VE None: çapa yok/ölçülemedi → kurulum yok (ayrım earnings_pit sayacında)
    elif not earn.days_since_report(ticker, last_date, max_days=2):
        return None        # CANLI YOL — GÖVDE AYNEN (kill-list: canlı days_since_report değişmez)
```

Çiviler: (1) param YOKKEN `earnings_pit` HİÇ çağrılmaz — monkeypatch ile `days_since_report_pit`
raise eder, canlı-yol scan patlamaz; (2) param VARKEN canlı `earn.days_since_report` HİÇ
çağrılmaz (simetrik mutasyon); (3) param varken None cevap kurulumu düşürür AMA sayaçta
`olculemedi` artar (False'tan ayrık). `earnings.days_since_report` gövdesinin değişmediği
Görev 4'ün pitlaw çivisiyle ayrıca bağlanır.

### Task 3: `backtest.py` + `cf_backfill.py` bağlaması (v345 bölüm 2)

- `backtest.replay`: `eff` kurulduğu yerde `eff["earnings.pit_arsiv"] = True`; koşum başında
  `earnings_pit.sayac_sifirla()`; sonuç sözlüğünün earnings_gate bloğuna
  `"pit_arsiv": earnings_pit.sayac_oku()` (kill-list 4: davranış raporu — True sayısı görünür).
- `cf_backfill`: `eff` VE `rx` scan_all çağrılarının ikisi de parametreyi görür (tek dict'e
  koyup ikisine akıt); `eg`ye aynı sayaç bloğu.
- Çiviler: replay sonucu `pit_arsiv` bloğu taşır; cf çıktısında sayaç var; parametrenin İKİ
  scan_all çağrısına da ulaştığı ölçülür (biri unutulursa kırmızı).

### Task 4: pitlaw beyan taşıması + arming ufku

- İki kayıt `BILINEN_IHLALLER`den SİLİNİR ve `PIT_KORUMALI_ZINCIRLER`e TAŞINIR — gerekçe metni:
  zincir statik olarak görünür kalır ama `params.get("earnings.pit_arsiv")` sevki tarihsel
  çağrıyı arşive yönlendirir; **"koruma kalkarsa bu kayıt ÇÜRÜR ve çivi öter — beyan, sevkin
  kendisine bağlıdır"** (shadow_lifecycle emsal metni birebir sınıf).
- Sevk-çürümesi çivisi: `strategy.py` kaynağında iki evaluate fonksiyonunun çapa bloğunda
  `earnings.pit_arsiv` sevkinin VARLIĞI mekanik doğrulanır (mevcut `if pit:` koruması v341/v342'de
  nasıl bağlandıysa AYNI usul — önce onu oku, biçimi kopyala).
- `arming._kanit_durumu`: YALNIZ `arsiv_yok` dalı arşiv-farkındalığı kazanır —
  `earnings_pit.arsiv_ufku()["ilk"]` defter başlangıcını kapsıyorsa (`arsiv_ilk <= defter_ilk`)
  dal `insufficient_cf`e düşer; cümle arşivi adıyla anar. `takvim_bos` dalı DEĞİŞMEZ (canlı
  takvim boşluğu bugün-çözülür ayrı arıza sınıfıdır).
- Mevcut çivi güncellemeleri: `test_pit_yasasi_v341.py` (BILINEN iterasyonları, korumalı-zincir
  denetimi), `test_arming_pit_kapisi_v301.py` (hüküm dönüşü). CANLI_TABAN 5 KALIR — dokunulmaz.

### Task 5: Yol-tutarlı pozitif kontrol — `tests/test_pit_baglama_pk_v346.py`

Karttan, üç dal da GERÇEK CSV satırıyla (sentetik değil), TAM yoldan
(`scan_all(param'lı) → evaluate_pead → days_since_report_pit`):
1. Arşivden gerçek bir (sembol, report_date) seç; PEAD koşullarını sağlayan sentetik BAR
   serisi kur (barlar sentetik olabilir — YOL gerçek, çapa verisi gerçek); scan_all
   `{"earnings.pit_arsiv": True, ...}` ile PEAD sinyali ÜRETİR (True dalı).
2. Aynı sembolün pencere-dışı günü (report_date - 10 gün) → sinyal YOK ve sayaçta `false` arttı.
3. Filed-max ötesi gün (2026-08-15 gibi arşiv-sonrası) → sinyal YOK ve sayaçta `olculemedi`
   arttı (False'la KARIŞMADI).
Tek-enstrümanlı PK portföy-yolu hatalarına kördür (vaka 2026-08-25) — bu yüzden PK scan_all
üzerinden kurulur, doğrudan `days_since_report_pit` çağrısıyla DEĞİL.

## Görevler sonrası — Rol-1'de kalan (ajanlara verilmez)

Kart düzeltme şerhi (hipotezdeki "taban 5→3" defter-adı karışıklığı; gerçek: BILINEN 2→0,
CANLI_TABAN 5 kalır) · kapsama/tutarlılık ölçümü (canlı takvim A1'den çekilir — yerel state
kirli) · hüküm kart + K defterine AYNI turda · tam suite (motor kaynağı değişti, §8) · commit/push.

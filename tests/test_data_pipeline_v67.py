"""test_data_pipeline_v67.py — VERİ HATTI: SESSİZCE SEMBOL VE SEANS KAYBI (2026-07-22).

Canlı olay defterindeki dört gerçek hata, tek tek köküne kadar sürüldü:

  160x session_bar_never_published {"session":"2026-07-15","latest_bar":"2026-07-13"}
  154x warmup_coverage_short       {"ticker":"KVUE","first_bar":"2023-05-04"}
   28x index_bars_invalid          {"issues":["empty"]}
   18x bar_sources_all_empty       {"ticker":"ROST","tried":"cboe,nasdaq"}

BULGULAR (ayrıntı nihai raporda):
  1. `bar_sources_all_empty` HATA ile BOŞ'u ayırt etmiyordu. Her kol `except Exception:
     df = pd.DataFrame()` ile boşluğa çevriliyordu; olay "hiçbir kaynak veri vermedi" diyordu ve
     operatör bunu "sembol borsadan düşmüş" diye okuyordu. Canlı kanıt aksini söylüyor: evren
     sırasında ARDIŞIK 18 sembol (SNAP…ROST) 48 dakikalık tek bir pencerede TAM BİRER KEZ bu olayı
     bastı ve on sekizinin de diskteki geçmişi 2026-07-21'e kadar sapasağlam. Sebep sembol değil,
     o penceredeki istek kısıtlamasıydı.
  2. `index_bars_invalid ["empty"]` — corporate-action sıfırlaması CSV'yi `cp.unlink()` ile SİLİP
     yeni hâli ~40 satır sonra yazıyordu. Aradaki pencerede önbellek DİSKTE YOKTU; o anda okuyan
     süreç (havuz işçisi / ikinci bir load_bars) `cp.exists()==False` görüyor, kaynaklar da
     kısıtlıysa BOŞ seri dönüyordu. SPY'de bunun karşılığı doğrudan "endeks boş".
  3. `dataset.load` bozuk endeksi UYARIP devam ediyordu ve elinde iyi kopya yoksa BOŞ endeksi
     süreç-içi önbelleğe ÇİVİLİYORDU: tek bir geçici kesinti, süreç ömrü boyunca sessiz bir
     yanlış duruma dönüşüyordu. Endeks rejim sınıflamasının TEK dayanağı — bu bir DURDURUCU.
  4. `warmup_coverage_short` en ciddisiydi: motor ısınması dolmayan barlarda gösterge HESAPLIYORDU.
     `trend_template` koşulları `pd.concat(...).astype(float)` ile birleştiriyordu ve pandas'ta
     NaN karşılaştırması False üretir — yani "200 günlük ortalama HENÜZ YOK" sessizce "koşul
     sağlanmadı" oluyordu. Genç sembol (KVUE ilk bar 2023-05-04) "veri yok" değil "trend zayıf"
     diye PUANLANIYORDU: uydurulmuş sayı, gerçek ölçüm kılığında.
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import pytest

from meridian import config, indicators as ind, store, strategy as strat
from meridian.adapters import data


@pytest.fixture(autouse=True)
def _pipeline_sandbox(sandbox_state, monkeypatch):
    """Her test kum havuzunda. Süreç-içi aynalar da temizlenir: bunlar modül düzeyinde global ve
    testler arası sızıntı, geçen bir testi vakumlu hâle getirir."""
    monkeypatch.setattr(config, "BARS", sandbox_state / "bars")
    monkeypatch.setattr(data.time, "sleep", lambda *_: None)
    data._LAST_SOURCE.clear()
    data._NO_DATA.clear()
    data._SEAMS.clear()
    data._WARMUP_WARNED.clear()
    data._BAR_WARNED.clear()
    from meridian import dataset as _ds
    _ds._cache.clear()
    yield sandbox_state
    data._LAST_SOURCE.clear()
    data._NO_DATA.clear()
    data._SEAMS.clear()
    data._WARMUP_WARNED.clear()
    _ds._cache.clear()


def _bars(dates, close):
    return pd.DataFrame({"date": pd.to_datetime(dates), "open": close,
                         "high": [c * 1.01 for c in close], "low": [c * 0.99 for c in close],
                         "close": close, "volume": [1_000_000.0] * len(dates)})


def _events(name: str) -> list[dict]:
    """Olayı ADIYLA bul — İKİ İMZAYI birden tanır (K1, 2026-07-30).

    `obs.alarm` olay adını "<JETON> <mesaj>"a çevirir, yani bir olay `warn`dan `alarm`a
    yükseltildiğinde `event == "<ad>"` süzgeci SESSİZCE hiçbir şey bulamaz — ve test "olay hiç
    atılmadı" diye okur. Bu tam olarak `failed_broker_rejection` tuzağıydı (watchdog süzgeci hiç
    yayınlanmayan bir olay adını bekliyordu). Yükseltilen olaylar makine-okunur adı `kind`
    alanında taşır; yardımcı ikisine de bakar."""
    return [e for e in store.read_jsonl("events.jsonl")
            if e.get("event") == name or e.get("kind") == name]


def _no_fmp(monkeypatch):
    from meridian.adapters import fmp
    monkeypatch.setattr(fmp, "available", lambda: False)


# =================================================================================================
# 1) bar_sources_all_empty — "istek patladı" ile "sembol yok" AYNI OLAY DEĞİLDİR
# =================================================================================================
def test_source_error_is_not_reported_as_an_empty_symbol(monkeypatch):
    """CANLI İMZA: bar_sources_all_empty {"ticker":"ROST","tried":"cboe,nasdaq"}.

    Kanıt ROST'un ölü OLMADIĞINI söylüyor (diskte 2026-07-21'e kadar bar var). Kaynaklar 429
    verdiğinde olay, sembolü ölü göstermemeli — aksi hâlde operatör sağlam bir ismi evrenden siler."""
    _no_fmp(monkeypatch)

    def _boom(*a, **k):
        raise data.FetchError("HTTP 429", 3)

    monkeypatch.setattr(data, "_fetch_cboe", _boom)
    monkeypatch.setattr(data, "_fetch_nasdaq", _boom)

    assert data.fetch("ROST", "2026-07-01", "2026-07-22").empty
    ev = _events("bar_sources_all_empty")[-1]
    assert ev["ticker"] == "ROST"
    assert ev["tried"] == "cboe,nasdaq"                       # canlı imza korundu
    assert ev["verdict"] == "source_error", "istek hatası 'sembol yok' diye raporlanıyor"
    assert "HTTP 429" in ev["outcomes"], "hangi kaynak NEDEN düştü kayıtta yok"
    assert ev["streak"] == 0, "ağ arızası ölü-sembol sayacını artırmış"
    assert "ÇIKARMA" in ev["detail"]


def test_a_cleanly_empty_symbol_is_flagged_for_universe_maintenance(monkeypatch):
    """POZİTİF KONTROL / karşı-durum: her kaynak DÜZGÜN cevap verip sıfır satır dönerse bu GERÇEKTEN
    evren bakımı adayıdır ve ISRAR ederse operatör uyandırılır (elle bakımlı evren, tek kanıtla
    silinmez)."""
    _no_fmp(monkeypatch)
    monkeypatch.setattr(data, "_fetch_cboe", lambda *a, **k: pd.DataFrame())
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda *a, **k: pd.DataFrame())

    for _ in range(data.NO_DATA_CONFIRM_STREAK):
        data.fetch("ZZZZ", "2026-07-01", "2026-07-22")

    ev = _events("bar_sources_all_empty")[-1]
    assert ev["verdict"] == "symbol_unknown" and ev["errored"] == ""
    assert ev["streak"] == data.NO_DATA_CONFIRM_STREAK
    rep = data.no_data_report()
    assert rep["confirmed_no_data"] == ["ZZZZ"], "ısrarlı verisiz sembol bakım listesine düşmedi"
    alarms = [e for e in store.read_jsonl("events.jsonl") if "DATA_QUALITY" in str(e.get("event"))]
    assert any("ZZZZ" in str(a) for a in alarms), "operatöre hiçbir kanal üzerinden söylenmedi"


def test_the_dead_symbol_counter_resets_when_the_symbol_returns(monkeypatch):
    """Sıfırlamayan sayaç okunmaz hâle gelir: bir kez arızalanan her sembol sonsuza dek listede kalır."""
    _no_fmp(monkeypatch)
    monkeypatch.setattr(data, "_fetch_cboe", lambda *a, **k: pd.DataFrame())
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda *a, **k: pd.DataFrame())
    data.fetch("ROST", "2026-07-01", "2026-07-22")
    data.fetch("ROST", "2026-07-01", "2026-07-22")
    assert data.no_data_report()["suspect"] == ["ROST"]

    good = _bars(["2026-07-20", "2026-07-21", "2026-07-22"], [100.0, 101.0, 102.0])
    monkeypatch.setattr(data, "_fetch_cboe", lambda *a, **k: good.copy())
    assert not data.fetch("ROST", "2026-07-01", "2026-07-22").empty
    assert data.no_data_report()["tracked"] == 0, "sembol yine veri verdi ama sayaç sıfırlanmadı"


def test_the_no_data_ledger_reaches_the_universe_maintenance_report(monkeypatch):
    """ÜRETİLEN KANIT TÜKETİLMELİ. Evren bakımının resmî raporu (constituents.universe_drift, günde
    bir loop._universe_drift_check tarafından çağrılır) bu kurulumda "unknown" dönüyor: üyelik
    kaynağı yok (canlı state/universe_drift.json → reason "HTTP 403"). O hâlde bile ısrarla verisiz
    kalan semboller RAPORDA görünmeli, yoksa defter yazılıp hiç okunmayan bir sayaç olur."""
    from meridian.adapters import constituents
    monkeypatch.setattr(constituents, "current", lambda **k: [])       # üyelik kaynağı yok (canlı hâl)
    _no_fmp(monkeypatch)
    monkeypatch.setattr(data, "_fetch_cboe", lambda *a, **k: pd.DataFrame())
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda *a, **k: pd.DataFrame())
    for _ in range(data.NO_DATA_CONFIRM_STREAK):
        data.fetch("ZZZZ", "2026-07-01", "2026-07-22")

    rep = constituents.universe_drift()
    assert rep["status"] == "unknown"                                  # dürüst: üyelik bilinmiyor
    assert rep["no_data"] == ["ZZZZ"] and rep["n_no_data"] == 1, \
        "verisiz-sembol kanıtı evren bakımı raporuna hiç ulaşmıyor"


def test_a_mixed_outcome_still_counts_as_source_error(monkeypatch):
    """Bir kaynak patlar, diğeri temiz-boş dönerse hüküm YİNE 'hüküm yok'tur: temiz-boş cevabı
    tek başına 'sembol yok' kanıtı değildir, çünkü patlayan kol o sembolü taşıyor olabilir."""
    _no_fmp(monkeypatch)
    monkeypatch.setattr(data, "_fetch_cboe", lambda *a, **k: pd.DataFrame())

    def _boom(*a, **k):
        raise data.FetchError("ConnectTimeout", 3)

    monkeypatch.setattr(data, "_fetch_nasdaq", _boom)
    data.fetch("LUV", "2026-07-01", "2026-07-22")
    ev = _events("bar_sources_all_empty")[-1]
    assert ev["verdict"] == "source_error" and ev["errored"] == "nasdaq"


def test_fetch_errors_never_carry_a_url(monkeypatch):
    """FMP isteği anahtarı SORGU PARAMETRESİNDE taşır ve httpx'in hata metni tam URL'i içerir.
    O metin bulguya girerse anahtar diske düşer (daha önce bir kez sızdı)."""
    import httpx

    def _fake_get(url, **k):
        raise httpx.ConnectError("connection failed to https://example.test/secret?apikey=ABC123")

    monkeypatch.setattr(data.httpx, "get", _fake_get)
    with pytest.raises(data.FetchError) as ei:
        data._get_json("https://example.test/secret?apikey=ABC123", 1.0, attempts=1)
    assert "ABC123" not in str(ei.value) and "http" not in str(ei.value).lower()
    assert ei.value.reason == "ConnectError"


# =================================================================================================
# 2) index_bars_invalid — boş endeks SERT DURUŞTUR
# =================================================================================================
def test_empty_index_is_a_hard_stop_not_a_warning(monkeypatch):
    """CANLI İMZA: index_bars_invalid {"issues":["empty"]} 28 kez, sonra devam.

    Endeks rejim sınıflamasının (regime.classify → ind.atr(index_bars)) ve seans seçiminin TEK
    dayanağıdır. Boş endeksle devam etmek 'veri yok' demek değil, bilinmeyen bir rejimi UYDURMAKTIR."""
    from meridian import dataset as ds
    monkeypatch.setattr(ds.data, "load_bars", lambda *a, **k: pd.DataFrame())
    monkeypatch.setattr(ds.data, "load_many", lambda *a, **k: {"AAPL": _bars(["2026-07-21"], [1.0])})

    with pytest.raises(ds.IndexUnavailable):
        ds.load(use_cache=False)

    assert not ds._cache, "BOZUK endeks süreç-içi önbelleğe çivilendi — kesinti kalıcı hâle gelir"
    ev = _events("index_bars_invalid")[-1]
    assert ev["action"] == "SERT DURUŞ"
    assert [i["code"] for i in ev["issues"]] == ["empty"]
    assert all(isinstance(i, dict) for i in ev["issues"]), \
        "bulgu şekli tüketiciye göre değişiyor (eski kod boş seride DİZGİ listesi üretiyordu)"


def test_a_hard_invalid_index_is_also_a_hard_stop(monkeypatch):
    """Boş DEĞİL ama SERT bozuk (yinelenen tarih / negatif fiyat) endeks de geçmemeli — eski kod
    yalnız `len(index)==0` durumunu ayrıca ele alıyordu, sert bulgular yalnız uyarıya düşüyordu."""
    from meridian import dataset as ds
    bad = _bars(["2026-07-20", "2026-07-20"], [100.0, 101.0])          # duplicate_dates = hard
    monkeypatch.setattr(ds.data, "load_bars", lambda *a, **k: bad)
    monkeypatch.setattr(ds.data, "load_many", lambda *a, **k: {"AAPL": bad})
    with pytest.raises(ds.IndexUnavailable):
        ds.load(use_cache=False)
    assert "duplicate_dates" in _events("index_bars_invalid")[-1]["codes"]


def test_a_transient_outage_falls_back_to_the_last_good_index(monkeypatch):
    """POZİTİF KONTROL: elde İYİ bir kopya varsa geçici kesinti motoru durdurmaz — sert duruş
    yalnız 'hiç iyi endeks yok' hâlinde geçerlidir."""
    from meridian import dataset as ds
    good = _bars(pd.bdate_range("2026-01-01", periods=80).astype(str).tolist(),
                 list(np.linspace(100.0, 120.0, 80)))
    monkeypatch.setattr(ds.data, "load_bars", lambda *a, **k: good.copy())
    monkeypatch.setattr(ds.data, "load_many", lambda *a, **k: {"AAPL": good.copy()})
    bars0, idx0 = ds.load(use_cache=False)
    assert len(idx0) == 80 and not _events("index_bars_invalid")   # sağlıklı tur SESSİZ

    monkeypatch.setattr(ds.data, "load_bars", lambda *a, **k: pd.DataFrame())
    bars1, idx1 = ds.load(use_cache=False)
    assert len(idx1) == 80, "son iyi kopyaya düşmedi"
    assert _events("index_bars_invalid")[-1]["action"] == "son iyi kopya kullanıldı"


def test_corporate_action_reset_never_leaves_the_cache_missing(monkeypatch):
    """index_bars_invalid'in ASIL kökü: sıfırlama yolu CSV'yi siliyor, yenisini ~40 satır sonra
    yazıyordu. Yazım o aralıkta düşerse (ya da başka bir süreç o anda okursa) geçmiş YOK olur.
    Yazımı patlatıp diskin hâlâ ESKİ barları taşıdığını iddia ediyoruz."""
    _no_fmp(monkeypatch)
    dates = ["2026-07-01", "2026-07-02", "2026-07-06"]
    data._write_bars(_bars(dates, [400.0, 401.0, 402.0]), data._cache_path("SPY"))
    data._pin_source("SPY", "cboe")
    cp = data._cache_path("SPY")
    before = cp.read_text()

    # bölünme sonrası TAM yeniden düzeltilmiş seri: örtüşen tarihlerde >%25 sapma → corp-action
    split = _bars(dates + ["2026-07-07"], [40.0, 40.1, 40.2, 40.3])
    monkeypatch.setattr(data, "_fetch_cboe", lambda *a, **k: split.copy())
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda *a, **k: pd.DataFrame())

    def _write_dies(df, path):
        raise OSError("disk full")

    monkeypatch.setattr(data, "_write_bars", _write_dies)
    with pytest.raises(OSError):
        data.load_bars("SPY", "2026-07-01", "2026-07-08", use_cache=False)

    assert cp.exists(), "önbellek dosyası YOK OLDU — eşzamanlı okuyucu boş endeks görür"
    assert cp.read_text() == before, "geçmiş kalıcı olarak kayboldu"


def test_corporate_action_reset_still_rewrites_on_the_happy_path(monkeypatch):
    """POZİTİF KONTROL: silmeyi kaldırmak sıfırlamayı ETKİSİZLEŞTİRMEMELİ — bayat ölçekli geçmiş
    yine TAMAMEN taze seriyle değişmeli (iki düzeltme ölçeği asla eklenmemeli)."""
    _no_fmp(monkeypatch)
    dates = ["2026-07-01", "2026-07-02", "2026-07-06"]
    data._write_bars(_bars(dates, [400.0, 401.0, 402.0]), data._cache_path("SPY"))
    split = _bars(dates + ["2026-07-07"], [40.0, 40.1, 40.2, 40.3])
    monkeypatch.setattr(data, "_fetch_cboe", lambda *a, **k: split.copy())
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda *a, **k: pd.DataFrame())

    data.load_bars("SPY", "2026-07-01", "2026-07-08", use_cache=False)
    disk = pd.read_csv(data._cache_path("SPY"), parse_dates=["date"])
    assert len(disk) == 4 and float(disk["close"].max()) < 100.0, "bayat ölçekli barlar hayatta kaldı"
    assert _events("corporate_action_cache_reset"), "sıfırlama kaydı yok"


def test_load_bars_has_no_unlink_of_the_cache():
    """Yol bir daha açılmasın: önbellek dosyası ATOMİK olarak DEĞİŞTİRİLİR, asla önce silinmez."""
    import inspect
    # YORUM SATIRLARI HARİÇ: kaldırılan satırın NEDENİ kodda anlatılıyor ve metni geçiyor.
    src = "\n".join(ln for ln in inspect.getsource(data.load_bars).splitlines()
                    if not ln.lstrip().startswith("#"))
    assert "unlink()" not in src, "önbellek silme penceresi geri geldi (boş endeks sınıfı)"


# =================================================================================================
# 3) warmup_coverage_short — ISINMASI DOLMAYAN BARDA GÖSTERGE HESAPLANMAZ
# =================================================================================================
def test_trend_template_is_undefined_before_warmup_not_zero():
    """EN CİDDİ BULGU. `close > sma50` gibi bir koşul, sma50 NaN iken pandas'ta False üretir; eski
    kod bunu 'koşul sağlanmadı' diye 0 puanlıyordu. 'Bilmiyorum' ile 'hayır' aynı sayıya
    çöktüğünde motor, veri yokluğunu ZAYIF TREND diye ölçer."""
    from tests.conftest import make_bars
    bars = make_bars(320, seed=11, trend=0.0008)
    tt = ind.trend_template(bars)

    assert tt.iloc[:ind.TREND_TEMPLATE_WARMUP - 1].isna().all(), \
        "ısınma dolmadan sayı üretiliyor — uydurulmuş değer gerçek ölçüm kılığında"
    assert tt.iloc[ind.TREND_TEMPLATE_WARMUP - 1:].notna().any(), \
        "ısınma dolduktan SONRA da NaN — gösterge ölü (pozitif kontrol)"
    v = tt.dropna()
    assert len(v) and 0.0 <= float(v.min()) and float(v.max()) <= 1.0


def test_trend_template_warmup_matches_its_longest_window():
    """Eşik keyfî bir sabit değil, göstergenin EN UZUN penceresidir.

    DÜZELTİLDİ (2026-07-22, sinyal-matematiği turu): bu test 219/220 bekliyordu ve gerekçesi
    "en uzun pencere 200g ortalama + 20 barlık eğim"di. Bu YANLIŞ MATEMATİĞİ KAYIT ALTINA ALIYORDU:
    şablonun 5. ve 6. koşulu 52 HAFTALIK yüksek/düşük üzerinedir ve o pencere 252 bardır (>220).
    52w serileri min_periods=100 ile kurulduğu için 220-251 bar arasında şablon sayı üretiyor,
    o sayı da "52 haftalık" diye raporlanıyordu. Gerçek kanıt: KVUE 2024-03-19 → 2024-05-02
    (32 seans). Doğru eşik 252'dir; test artık gerçek en uzun pencereyi bekliyor."""
    from tests.conftest import make_bars
    bars = make_bars(400, seed=4)
    tt = ind.trend_template(bars)
    first = int(np.argmax(tt.notna().to_numpy()))
    assert first == ind.TREND_TEMPLATE_WARMUP - 1 == 251


def test_a_young_symbol_produces_no_signal_instead_of_a_wrong_one():
    """UÇTAN UCA: KVUE gibi genç bir sembol (canlıda ilk bar 2023-05-04, istenen 2021-01-01) artık
    'zayıf trend' diye PUANLANMIYOR, dürüstçe DIŞLANIYOR. Dört kurulumun `pd.isna(tt)` koruması
    zaten vardı — eksik olan, göstergenin bilmediğini söylemesiydi."""
    from tests.conftest import make_bars
    full = make_bars(320, seed=11, trend=0.0009, breakout_at=250)
    young = full.iloc[-150:].reset_index(drop=True)          # 150 bar < 252 ısınma

    assert pd.isna(ind.trend_template(young).iloc[-1])
    assert strat.scan_all(young, config.bounds() and {}, 95, ticker="KVUE") == {}, \
        "ısınması dolmamış sembol sinyal üretti"
    # POZİTİF KONTROL: aynı veri tam geçmişiyle taranınca motor GERÇEKTEN çalışıyor —
    # yoksa yukarıdaki boşluk 'her şey boş' yüzünden de geçerdi (vakumlu test).
    assert ind.trend_template(full).iloc[-1] > 0.0


def test_warmup_event_says_whether_indicators_are_trustworthy(monkeypatch):
    """CANLI İMZA: warmup_coverage_short {"ticker":"KVUE","first_bar":"2023-05-04",
    "wanted_start":"2021-01-01"} — üretilip HİÇ tüketilmeyen bir bulguydu. Artık asıl soruyu
    cevaplıyor: bu sembolde gösterge güvenilir mi?"""
    _no_fmp(monkeypatch)
    dates = pd.bdate_range("2023-05-04", periods=120).astype(str).tolist()
    data._write_bars(_bars(dates, list(np.linspace(20.0, 25.0, 120))), data._cache_path("KVUE"))

    end = str((dt.date.fromisoformat(dates[-1])))
    data.load_bars("KVUE", "2021-01-01", end, use_cache=True)
    ev = _events("warmup_coverage_short")[-1]
    assert ev["ticker"] == "KVUE" and ev["first_bar"] == "2023-05-04"
    assert ev["wanted_start"] == "2021-01-01"
    assert ev["bars"] == 120 and ev["warmup_needed"] == ind.TREND_TEMPLATE_WARMUP
    assert ev["indicators_trustworthy"] is False

    data._WARMUP_WARNED.clear()
    long_dates = pd.bdate_range("2023-05-04", periods=300).astype(str).tolist()
    data._write_bars(_bars(long_dates, list(np.linspace(20.0, 25.0, 300))), data._cache_path("KVUE"))
    data.load_bars("KVUE", "2021-01-01", long_dates[-1], use_cache=True)
    assert _events("warmup_coverage_short")[-1]["indicators_trustworthy"] is True   # pozitif kontrol


# =================================================================================================
# 4) session_bar_never_published — pes etmek DÜRÜST ve GÖRÜNÜR olmalı
# =================================================================================================
def _scheduler_stub(monkeypatch, coverage_bars: dict, index: pd.DataFrame):
    from meridian import dataset as ds, health, loop, reflect, scheduler, watchdog
    monkeypatch.setattr(scheduler, "_last_closed_session", lambda: "2026-07-15")
    monkeypatch.setattr(health, "halted", lambda: False)
    monkeypatch.setattr(ds, "load", lambda use_cache=True: (coverage_bars, index))
    monkeypatch.setattr(watchdog, "beat", lambda *a, **k: None)
    monkeypatch.setattr(watchdog, "check_and_alarm", lambda *a, **k: None)
    monkeypatch.setattr(reflect, "clear_wf_caches", lambda *a, **k: None)
    monkeypatch.setattr(loop, "daily_cycle", lambda *a, **k: {"status": "noop", "date": "2026-07-13"})
    # ONARIM GEÇİDİ BU DOSYANIN KONUSU DEĞİL (2026-07-30): seans başına bir kez koşan geçit ağ
    # yolları içerir; burada ölçülen şey MERDİVENDİR. Taklit edilmezse test ölçtüğü şeyi değil,
    # komşu bir mekanizmanın ortamını ölçerdi.
    monkeypatch.setattr(scheduler, "_repair_once_per_session", lambda s: None)
    # YENİ MERDİVEN ALANLARI DA SIFIRLANIR: `_state` modül düzeyindedir ve önceki testten kalan bir
    # `refetch_chase`, bu testin kurmadığı bir kovalamayı miras alırdı (sıra bağımlı suite).
    scheduler._state.update({"last_refetch_session": None, "refetch_attempts": 0,
                             "last_processed": None, "cycles": 0, "refetch_chase": None,
                             "refetch_sparse_attempts": 0, "refetch_next_at": None,
                             "refetch_latest_bar": None, "last_repair_session": None})
    return scheduler


def test_giving_up_on_a_session_is_loud_and_bounded(monkeypatch):
    """CANLI İMZA: session_bar_never_published {"session":"2026-07-15","latest_bar":"2026-07-13"}.

    SINIRIN BİRİMİ DEĞİŞTİ — DENEME DEĞİL, ZAMAN (2026-07-30 merdiveni). Eski yasa 8. denemede
    (≈40 dk) pes ediyordu ve ürettiği alarm SAHTEYDİ: zincirin en taze kolu (Massive grouped,
    ücretsiz katman) T+1 yayınlıyor, yani barın 40 dakikada gelmesi YAPISAL olarak imkânsızdı.
    Canlıda 164 satır birikmişti, hepsi aynı imza — ve sahte alarm gerçek alarmı okunmaz yapar.

    'Loud and bounded' AYNEN korunuyor: (a) sık faz dolunca PES EDİLMEZ ama sessiz de kalınmaz,
    (b) terminal atlama bir SONRAKİ SEANSIN KAPANIŞINDA ilan edilir, (c) tek kez, (d) ölçüyle."""
    stale = _bars(["2026-07-10", "2026-07-13"], [100.0, 101.0])
    sched = _scheduler_stub(monkeypatch, {f"T{i}": stale.copy() for i in range(10)}, stale)

    for _ in range(12):                # sık faz (8) dolar; kalanlar seyrek fazın zamanını bekler
        sched.advance_once()

    assert not _events("session_bar_never_published"), \
        "son tarih dolmadan pes edildi — 164 sahte alarmın yasası geri geldi"
    assert _events("session_bar_retry_sparse"), \
        "sık fazın kapanışı SESSİZ — pes edilmiyor olması, kayıt tutulmaması demek değildir"
    assert sched._state["refetch_chase"] == "2026-07-15", "kovalama sürmüyor"
    assert sched._state["last_refetch_session"] == "2026-07-15", "bayrak yanmadı (poll'ler cache-only olmalı)"

    # SON TARİH DOLDU: bir sonraki seans kapandı, öncekinin barı hâlâ yok — İŞTE BU gerçek arızadır
    monkeypatch.setattr(sched, "_last_closed_session", lambda: "2026-07-16")
    sched.advance_once()
    sched.advance_once()                                  # tekrar ilan edilmemeli

    ev = _events("session_bar_never_published")
    assert len(ev) == 1, f"pes etme kaydı {len(ev)} kez atıldı — sınırlı sabır sızdırıyor"
    e = ev[0]
    assert e["session"] == "2026-07-15" and e["latest_bar"] == "2026-07-13"
    assert e["universe_coverage"] == 0.0 and e["required"] > 0, "ÖLÇÜ yok, yalnız hikâye var"
    assert "ATLAYACAK" in e["detail"], "motorun seansı atlayacağı söylenmiyor"


def test_a_session_that_does_arrive_never_reports_give_up(monkeypatch):
    """POZİTİF KONTROL: bar GELDİĞİNDE pes etme olayı HİÇ atılmamalı, yoksa yukarıdaki '1 kez'
    iddiası her koşulda sağlanır ve testi vakumlu yapar."""
    fresh = _bars(["2026-07-14", "2026-07-15"], [100.0, 101.0])
    sched = _scheduler_stub(monkeypatch, {f"T{i}": fresh.copy() for i in range(10)}, fresh)
    for _ in range(3):
        sched.advance_once()
    assert not _events("session_bar_never_published")
    assert sched._state["last_refetch_session"] == "2026-07-15"


def test_the_retry_cap_survives_a_restart(monkeypatch):
    """DÜZELTİLDİ (2026-07-22). Bu test önce SINIRI kilitliyordu: sayaç yalnız süreç belleğindeydi,
    `scheduler_status.json` yazılıyor ama geri OKUNMUYORDU. Canlı kanıt: 08:32 yeniden başlatmasından
    sonra dosyada `last_refetch_session: null, cycles: 0`, oysa TEK seans (2026-07-15) için 159 pes
    etme kaydı vardı. Her yeniden başlatma, 8 denemelik (250 sembol × 3 kaynak) önbellek-baypas
    süpürmesini sıfırdan yakıyordu — ve aynı pencerede 18 sembol 429 yiyordu. İki hata aynı olayın
    iki ucuydu. Artık `_rehydrate()` kalıcı sayaçları geri yükler; test yön değiştirdi."""
    from meridian import scheduler
    # `_state` modül düzeyinde: aynı dosyadaki önceki testler `cycles`i artırmış olabilir.
    scheduler._state.update({"last_refetch_session": None, "refetch_attempts": 0, "cycles": 0,
                             "last_tick": None})
    store.write_json(scheduler.STATUS_FILE, {"last_refetch_session": "2026-07-15",
                                             "refetch_attempts": 8, "cycles": 99,
                                             "last_tick": "2026-07-15T20:00:00+00:00"})
    got = scheduler._rehydrate()
    assert scheduler._state["last_refetch_session"] == "2026-07-15", "tavan yeniden yakılıyor"
    assert scheduler._state["refetch_attempts"] == 8
    # CANLILIK bilgisi taşınMAZ: `cycles`/`last_tick` o sürecin nabzıdır, önceki sürecinki değil.
    assert "cycles" not in got and "last_tick" not in got
    assert scheduler._state["cycles"] == 0, "önceki sürecin tur sayısı devralınamaz"


def test_rehydrate_is_wired_into_start():
    """Kurtarma yalnız çağrılırsa işe yarar — `start()` onu gerçekten çağırmalı."""
    import inspect
    from meridian import scheduler
    assert "_rehydrate()" in inspect.getsource(scheduler.start)


def test_rehydrate_tolerates_a_missing_or_broken_status_file(sandbox_state):
    """Taze kurulumda dosya yok; bozuk dosya da kurtarmayı düşürmemeli (muhafazakâr: tavan sıfırdan
    başlar, bu güvenli taraftır — ama sessizce çökmez)."""
    from meridian import scheduler
    scheduler._state.update({"last_refetch_session": None, "refetch_attempts": 0})
    assert scheduler._rehydrate() == {}
    store.write_json(scheduler.STATUS_FILE, ["bozuk", "liste"])
    assert scheduler._rehydrate() == {}

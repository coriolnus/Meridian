"""v139 — SIP BACAĞI TASARIM DÜZELTMESİ: konsolide feed YALNIZ GEÇMİŞ SEANSLAR İÇİN.

ÖLÇÜLMÜŞ KÖK NEDEN (canlı, 2026-07-30 21:14Z, gerçek ücretsiz paper anahtarı):
    feed=sip + session=BUGÜN → HTTP 403 {"subscription does not permit querying recent SIP data"}
    feed=sip + session=DÜN   → HTTP 200, konsolide
Rol 1'in 2026-07-29 öğleden-sonra sondası DÜNÜ sorduğu için 200 almıştı; yani v133'ün dayandığı
"kapanış+16 dk'da BUGÜNÜN konsolide barı gelir" iddiası HİÇ SINANMAMIŞTI. Gerçek sınır bir saat
penceresi değil bir TAKVİM GÜNÜ penceresidir (geç basımlar ve düzeltmeler bugünün barını gün boyu
"recent" tutuyor). Eski davranışın canlı bedeli: her akşam bir boşa 403, ardından 6 saatlik abonelik
soğuması — yani o akşam sip fiilen ölü, defterde de SAHTE bir "abonelik reddetti" satırı. (Yedek IEX
katmanı doğru şekilde devreye girdi ve kalibre hacimlerle çalıştı; kaybedilen şey konsolide bardı.)

BU DOSYA DÖRT YASAYI ÇİVİLER:
  1. ATLAMA   — hedef seans BUGÜNÜN takvim günüyse sip basamağı HİÇ denenmez; olay basılır
                (`alpaca_sip_skipped_current_session`, BİLGİ düzeyi) ve doğrudan iex'e geçilir.
  2. BİRİNCİL — hedef seans GEÇMİŞSE sip yine BİRİNCİLDİR (gecikmeli kovalama / onarım geçidi).
  3. DÜZELTİCİ— ertesi günün koşusunda dünün IEX satırları KONSOLİDE sip barıyla değiştirilir;
                massive grouped NİHAİ otorite kalır (sıra: iex → sip → massive) ve ıraksama defteri
                İKİ kaynağı da AYRI ölçer.
  4. SOĞUMA   — bugünkü-seans atlaması soğuma YAZMAZ (koşul, arıza değil); GEÇMİŞ seansta alınan
                gerçek 403 hâlâ 6 saatlik abonelik soğumasıdır.

TAKVİM GÜNÜ HER TESTTE SABİTLENİR: duvar saatine bağlı bir sip testi, bu dosyanın bir gün yeşil
bir gün kırmızı olması demekti — yani düzelttiğimiz "kodda örtük zaman varsayımı" sınıfının test
tarafındaki ikizi.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest

from meridian import store

TODAY = "2026-07-30"          # sabitlenmiş ET takvim günü
SESSION = "2026-07-29"        # GEÇMİŞ seans (dün)


@pytest.fixture(autouse=True)
def _reset_module_state():
    """Bacak/defter süreç-içi önbellekleri modül düzeyindedir (v133'ün aynı dersi, yeni yüzey)."""
    from meridian.adapters import alpaca, data
    _dicts = (data._ALPACA_MEMO, data._ALPACA_ASKED, data._ALPACA_PENDING, data._LAST_SOURCE,
              alpaca._DATA_FAIL_AT, alpaca._DATA_COOLDOWN, alpaca._DATA_LAST_FAIL)

    def _sifirla():
        for d in _dicts:
            d.clear()
        alpaca._DATA_TRANSPORT.clear()
        alpaca._DATA_TRANSPORT.update({"ok": None, "calls": 0, "fails": 0, "last_status": None,
                                       "last_error": "", "at": None})
        data._SE = {}
        data._SE_PENDING_EVENT.clear()
        data._BAR_WARNED.clear()

    _sifirla()
    data._SE_DIRTY = 0
    data._XCHECK = {}
    data._SEAMS = {}
    data._NO_DATA = {}
    yield
    _sifirla()


class _Resp:
    def __init__(self, payload, status=200):
        self._p, self.status_code = payload, status

    def json(self):
        return self._p

    @property
    def text(self):
        import json
        return json.dumps(self._p)


def _events(name: str) -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl")
            if e.get("event") == name or e.get("kind") == name]


def _keys(monkeypatch, today: str = TODAY):
    from meridian.adapters import alpaca
    monkeypatch.setattr(alpaca.secrets, "present", lambda n: True)
    monkeypatch.setattr(alpaca.secrets, "get", lambda n: "x")
    monkeypatch.setattr(alpaca, "market_calendar_day", lambda: today)


def _router(monkeypatch, sip=None, iex=None, sip_status=200):
    """`/v2/stocks/bars` (sip) ile `/v2/stocks/snapshots` (iex) çağrılarını AYRI AYRI kaydet."""
    from meridian.adapters import alpaca
    seen = {"sip": [], "iex": []}

    def _get(url, params=None, headers=None, timeout=None):
        if url.endswith("/v2/stocks/bars"):
            seen["sip"].append(dict(params or {}))
            return _Resp(sip if sip is not None else {"bars": {}, "next_page_token": None},
                         status=sip_status)
        seen["iex"].append(dict(params or {}))
        return _Resp(iex if iex is not None else {})

    monkeypatch.setattr(alpaca.httpx, "get", _get)
    return seen


def _sip_payload(session: str, close: float, volume: float, sym: str = "AAA") -> dict:
    return {"bars": {sym: [{"t": f"{session}T04:00:00Z", "o": close, "h": close, "l": close,
                            "c": close, "v": volume}]}, "next_page_token": None}


def _iex_payload(session: str, close: float, volume: float, sym: str = "AAA") -> dict:
    return {sym: {"dailyBar": {"t": f"{session}T04:00:00Z", "o": close, "h": close, "l": close,
                               "c": close, "v": volume}}}


# ==================================================================================================
# 1) ATLAMA — bugünün seansı için sip HİÇ sorulmaz
# ==================================================================================================
def test_the_current_session_never_asks_sip(sandbox_state, monkeypatch):
    """CANLI BULGUNUN ÇİVİSİ: hedef seans BUGÜNÜN takvim günüyse konsolide uca TEK bir istek bile
    gitmez. Eski davranış her akşam garantili bir 403 yakıyordu."""
    from meridian.adapters import alpaca
    _keys(monkeypatch, today=SESSION)                     # hedef seans == BUGÜN
    seen = _router(monkeypatch, iex=_iex_payload(SESSION, 10.0, 5_000.0))
    res = alpaca.same_evening_bars(["AAA"], SESSION)
    assert seen["sip"] == [], "bugünün seansı için sip'e istek gitti — garantili 403 yakılıyor"
    assert seen["iex"] and seen["iex"][0]["feed"] == "iex"
    assert res["source"] == "alpaca_iex" and res["bars"]["AAA"]["volume"] == 5_000.0
    assert "sip bugünün seansı için atlandı" in res["detail"]


def test_the_skip_is_announced_not_silent(sandbox_state, monkeypatch):
    """SESSİZ DEĞİL (yasa 4) ama UYARI DA DEĞİL: her akşam tekrarlayan, kimsenin yapabileceği bir
    şey olmayan bir `warn` gerçek uyarıları okunmaz yapardı. Olay BİLGİ düzeyindedir ve neden
    atlandığını KENDİSİ söyler."""
    from meridian.adapters import alpaca
    _keys(monkeypatch, today=SESSION)
    _router(monkeypatch, iex=_iex_payload(SESSION, 10.0, 5_000.0))
    alpaca.same_evening_bars(["AAA", "BBB"], SESSION)
    ev = _events("alpaca_sip_skipped_current_session")
    assert len(ev) == 1, "bilinçli atlama defterde görünmüyor"
    assert ev[0]["level"] == "info", "koşul ARIZA gibi raporlandı"
    assert ev[0]["session"] == SESSION and ev[0]["today_et"] == SESSION
    assert ev[0]["feed"] == "sip" and ev[0]["asked"] == 2 and ev[0]["caller"] == "same_evening"
    assert ev[0]["cooldown_written"] is False


def test_the_skip_is_not_read_as_a_subscription_refusal(sandbox_state, monkeypatch):
    """ATLAMA, DEFTERDE SAHTE BİR YETKİ HİKÂYESİ BIRAKMAZ: sip hiç sorulmadığı için ortada bir
    'abonelik reddetti' olayı da olamaz."""
    from meridian.adapters import alpaca
    _keys(monkeypatch, today=SESSION)
    _router(monkeypatch, iex=_iex_payload(SESSION, 10.0, 5_000.0))
    alpaca.same_evening_bars(["AAA"], SESSION)
    assert _events("alpaca_sip_rejected") == []
    assert _events("alpaca_data_failed") == [], "atlama bir ARIZA olarak kaydedildi"


def test_sip_allowed_is_the_single_law(sandbox_state, monkeypatch):
    """Kural TEK YERDE durur: geçmiş → sorulur, bugün/gelecek → sorulmaz, takvim günü BİLİNMİYORSA
    → sorulmaz (kapalı taraf güvenli taraf; scheduler._leg_ready'nin aynı disiplini)."""
    from meridian.adapters import alpaca
    monkeypatch.setattr(alpaca, "market_calendar_day", lambda: TODAY)
    assert alpaca.sip_allowed("2026-07-29") is True
    assert alpaca.sip_allowed(TODAY) is False
    assert alpaca.sip_allowed("2026-07-31") is False
    assert alpaca.sip_allowed(None) is False
    monkeypatch.setattr(alpaca, "market_calendar_day", lambda: "")
    assert alpaca.sip_allowed("2026-07-29") is False, "takvim günü çözülemedi ama sip yine soruldu"


def test_the_calendar_day_is_eastern_not_utc(sandbox_state):
    """ET SEÇİMİ KEYFİ DEĞİL: seans tarihleri ET'dir ve UTC kullanmak 20:00 ET'den sonra (= ertesi
    gün UTC) bugünün seansını 'geçmiş' sayıp kaçındığımız 403'ü akşamın ikinci yarısında geri
    getirirdi. ET, UTC'nin ASLA ilerisinde olmaz — iddia bu yüzden saatten bağımsız sınanabilir."""
    from zoneinfo import ZoneInfo
    from meridian.adapters import alpaca
    got = alpaca.market_calendar_day()
    assert got == str(dt.datetime.now(ZoneInfo("America/New_York")).date())
    assert got <= str(dt.datetime.now(dt.timezone.utc).date())


# ==================================================================================================
# 2) BİRİNCİL — geçmiş seansta sip yine ilk basamak
# ==================================================================================================
def test_a_past_session_still_prefers_consolidated_sip(sandbox_state, monkeypatch):
    """Gecikmeli kovalama / onarım yolunda hedef seans GEÇMİŞTİR — orada sip BİRİNCİL kalır ve
    yedek katmana (iex) hiç inilmez."""
    from meridian.adapters import alpaca
    _keys(monkeypatch, today=TODAY)
    seen = _router(monkeypatch, sip=_sip_payload(SESSION, 10.0, 9_000_000.0))
    res = alpaca.same_evening_bars(["AAA"], SESSION)
    assert res["source"] == "alpaca_sip" and res["bars"]["AAA"]["volume"] == 9_000_000.0
    assert seen["sip"] and seen["sip"][0]["feed"] == "sip"
    assert seen["iex"] == [], "sip verdiği hâlde yedek katmana inildi"
    assert _events("alpaca_sip_skipped_current_session") == []


def test_sip_session_bars_refuses_today_and_serves_the_past(sandbox_state, monkeypatch):
    """Düzelticinin uç fonksiyonu: BUGÜN sorulursa HİÇ ağa çıkmaz (None + olay), geçmiş sorulursa
    konsolide barı verir. None = HÜKÜM YOK; {} = soruldu, eşleşen bar yok."""
    from meridian.adapters import alpaca
    _keys(monkeypatch, today=TODAY)
    seen = _router(monkeypatch, sip=_sip_payload(SESSION, 12.5, 8_000_000.0))
    assert alpaca.sip_session_bars(["AAA"], TODAY) is None
    assert seen["sip"] == [], "bugün için konsolide uca istek gitti"
    ev = _events("alpaca_sip_skipped_current_session")
    assert ev and ev[-1]["caller"] == "sip_correction"
    got = alpaca.sip_session_bars(["AAA"], SESSION)
    assert got and got["AAA"]["close"] == 12.5 and got["AAA"]["volume"] == 8_000_000.0
    assert _events("alpaca_sip_session")[-1]["matched"] == 1


# ==================================================================================================
# 3) SOĞUMA AYRIMI — koşul ≠ arıza
# ==================================================================================================
def test_the_current_session_skip_writes_no_cooldown(sandbox_state, monkeypatch):
    """ATLAMA SOĞUMA YAZMAZ. Yazsaydı, koşuldan doğan bir atlama 6 saat boyunca GERÇEK bir sip
    sorgusunu (geçmiş seans için) da bloklardı — yani düzeltme kendi düzelticisini kilitlerdi."""
    from meridian.adapters import alpaca
    _keys(monkeypatch, today=SESSION)
    _router(monkeypatch, iex=_iex_payload(SESSION, 10.0, 5_000.0))
    alpaca.same_evening_bars(["AAA"], SESSION)
    assert "bars:sip" not in alpaca._DATA_COOLDOWN
    assert "bars:sip" not in alpaca._DATA_FAIL_AT
    assert alpaca._DATA_LAST_FAIL == {}


def test_a_real_refusal_on_a_past_session_still_cools_down_six_hours(sandbox_state, monkeypatch):
    """GERÇEK YETKİ ARIZASI AYNEN KALIR: geçmiş bir seansta 403 almak 'recent SIP' koşuluyla
    açıklanamaz — geri çekilmeyle çözülmez, 6 saatlik soğumayı hak eder ve HAM metniyle duyurulur."""
    from meridian.adapters import alpaca
    _keys(monkeypatch, today=TODAY)
    _router(monkeypatch, sip={"message": "subscription does not permit querying recent SIP data"},
            sip_status=403, iex=_iex_payload(SESSION, 10.0, 5_000.0))
    res = alpaca.same_evening_bars(["AAA"], SESSION)
    assert res["source"] == "alpaca_iex"
    assert alpaca._DATA_COOLDOWN["bars:sip"] == alpaca.SIP_REJECT_COOLDOWN_S
    ev = _events("alpaca_sip_rejected")
    assert ev and ev[-1]["session"] == SESSION and "subscription" in ev[-1]["body"]
    assert "gerçek yetki arızası" in ev[-1]["detail"]


# ==================================================================================================
# 4) SIP DÜZELTİCİ — ikinci konsolide kaynak, massive'den ÖNCE
# ==================================================================================================
def _bars(dates, close=100.0, volume=1_000_000.0):
    return pd.DataFrame({"date": pd.to_datetime(list(dates)),
                         "open": [close] * len(dates), "high": [close * 1.01] * len(dates),
                         "low": [close * 0.99] * len(dates), "close": [close] * len(dates),
                         "volume": [volume] * len(dates)})


def _seed_cache(ticker: str, last: str, n: int = 220, close: float = 100.0,
                volume: float = 1_000_000.0) -> pd.DataFrame:
    from meridian.adapters import data
    dates = pd.bdate_range(end=pd.Timestamp(last), periods=n)
    df = _bars([str(d.date()) for d in dates], close=close, volume=volume)
    cp = data._cache_path(ticker)
    cp.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cp, index=False)
    return df


def _seed_provisional(ticker="AAA", session=SESSION, iex_close=10.0, iex_volume=5_000.0,
                      written_volume=100_000.0, ratio=20.0):
    """AKŞAMIN GERÇEK ÇIKTISI: diskte IEX değerlerini taşıyan bir satır + defterde geçici damga."""
    from meridian.adapters import data
    _seed_cache(ticker, session, n=220)
    cp = data._cache_path(ticker)
    df = pd.read_csv(cp, parse_dates=["date"])
    i = df.index[df["date"] == pd.Timestamp(session)][0]
    df.loc[i, ["open", "high", "low", "close", "volume"]] = [iex_close, iex_close, iex_close,
                                                             iex_close, written_volume]
    df.to_csv(cp, index=False)
    data._set_volume_ratio(ticker, [ratio], "bootstrap")
    data._note_provisional(ticker, {session: {
        "source": data.ALPACA_SOURCE, "close": iex_close, "iex_volume": iex_volume,
        "volume": written_volume, "ratio": ratio, "volume_scaled": True, "at": "2026-07-29T20:20:00+00:00"}})
    return cp


def _sip_env(monkeypatch, close=10.4, volume=120_000.0, session=SESSION, today=TODAY):
    from meridian.adapters import alpaca
    monkeypatch.setattr(alpaca, "data_available", lambda: True)
    _keys(monkeypatch, today=today)
    return _router(monkeypatch, sip=_sip_payload(session, close, volume))


def test_the_corrector_replaces_yesterdays_iex_row_with_the_consolidated_bar(sandbox_state, monkeypatch):
    """DÜZELTİCİNİN İŞİ: dünün temsilî satırı KONSOLİDE değerlerle değişir ve hacim HAM yazılır
    (sip zaten tüm piyasadır — ölçekleme sorusu yok)."""
    from meridian.adapters import data
    cp = _seed_provisional()
    _sip_env(monkeypatch, close=10.4, volume=120_000.0)
    rep = data.sip_correct_provisional()
    assert rep["targets"] == 1 and rep["corrected"] == 1
    assert rep["sessions"][SESSION]["verdict"] == "corrected"
    row = pd.read_csv(cp, parse_dates=["date"])
    got = row[row["date"] == pd.Timestamp(SESSION)].iloc[0]
    assert float(got["close"]) == 10.4 and float(got["volume"]) == 120_000.0
    ev = _events("alpaca_sip_correction")
    assert ev and ev[-1]["session"] == SESSION and ev[-1]["symbols"] == 1
    assert ev[-1]["max_dev_pct"] == pytest.approx(4.0, abs=1e-6)     # |10,4-10|/10 = %4


def test_massive_remains_the_final_authority(sandbox_state, monkeypatch):
    """SIRA: iex → sip → massive. Sip düzelticisi geçici damgayı KALDIRMAZ — kaldırsaydı nihai
    otorite hiç ölçemez ve iki konsolide kaynağın uyuşup uyuşmadığı sonsuza dek bilinmezdi."""
    from meridian.adapters import data, fmp, massive
    _seed_provisional()
    _sip_env(monkeypatch, close=10.4, volume=120_000.0)
    data.sip_correct_provisional()
    assert data._provisional_dates("AAA") == {SESSION}, "geçici damga erken kalktı"
    assert data._se()["provisional"]["AAA"][SESSION]["source"] == data.ALPACA_SIP_SOURCE
    # --- NİHAİ OTORİTE: massive grouped 07-29'u yayınladı ---
    monkeypatch.setattr(fmp, "available", lambda: False)
    monkeypatch.setattr(data, "_fetch_cboe", lambda t, to: pd.DataFrame())
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda t, s, e, to: pd.DataFrame())
    monkeypatch.setattr(massive, "available", lambda: True)
    monkeypatch.setattr(massive, "write_enabled", lambda: True)
    monkeypatch.setattr(massive, "covers", lambda s: False)
    monkeypatch.setattr(massive, "latest_bar", lambda t, end=None: {
        "date": SESSION, "open": 10.5, "high": 10.5, "low": 10.5, "close": 10.5, "volume": 125_000.0})
    monkeypatch.setattr(data, "_massive_crosscheck", lambda *a, **k: None)
    out = data.load_bars("AAA", "2021-01-01", "2026-07-30", use_cache=False)
    data.flush_same_evening()
    row = out[out["date"] == pd.Timestamp(SESSION)].iloc[0]
    assert float(row["close"]) == 10.5 and float(row["volume"]) == 125_000.0
    assert data._provisional_dates("AAA") == set(), "nihai otoriteden sonra damga kalkmadı"


def test_the_ledger_measures_both_sources_separately(sandbox_state, monkeypatch):
    """"İki kaynağı da ölçer" TEK ORTALAMA DEMEK DEĞİLDİR: iex↔sip farkı (temsilî↔konsolide) ile
    sip↔massive farkı (iki konsolide kaynak) aynı büyüklük değildir; tek sayıda eritilirse ikisi de
    okunamaz hâle gelir ve 'sip massive ile uyuşuyor mu?' sorusu cevapsız kalır."""
    from meridian.adapters import data, fmp, massive
    _seed_provisional()
    _sip_env(monkeypatch, close=10.4, volume=120_000.0)
    data.sip_correct_provisional()
    rep1 = data.upgrade_divergence()
    assert set(rep1["by_source"]) == {"alpaca_sip"}
    assert rep1["by_source"]["alpaca_sip"]["max_dev_pct"] == pytest.approx(4.0, abs=1e-6)
    monkeypatch.setattr(fmp, "available", lambda: False)
    monkeypatch.setattr(data, "_fetch_cboe", lambda t, to: pd.DataFrame())
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda t, s, e, to: pd.DataFrame())
    monkeypatch.setattr(massive, "available", lambda: True)
    monkeypatch.setattr(massive, "write_enabled", lambda: True)
    monkeypatch.setattr(massive, "covers", lambda s: False)
    monkeypatch.setattr(massive, "latest_bar", lambda t, end=None: {
        "date": SESSION, "open": 10.4, "high": 10.4, "low": 10.4, "close": 10.4, "volume": 125_000.0})
    monkeypatch.setattr(data, "_massive_crosscheck", lambda *a, **k: None)
    data.load_bars("AAA", "2021-01-01", "2026-07-30", use_cache=False)
    data.flush_same_evening()
    rep2 = data.upgrade_divergence()
    assert set(rep2["by_source"]) == {"alpaca_sip", "massive"}
    # sip ile massive AYNI kapanışı verdi → ikinci fark 0; ilk fark %4 olarak DURUYOR
    assert rep2["by_source"]["massive"]["max_dev_pct"] == pytest.approx(0.0, abs=1e-9)
    assert rep2["by_source"]["alpaca_sip"]["max_dev_pct"] == pytest.approx(4.0, abs=1e-6)
    assert rep2["sessions"] == 1 and rep2["symbols"] == 2      # iki düzeltme, tek seans


def test_the_corrector_recalibrates_the_volume_ratio_from_a_real_pair(sandbox_state, monkeypatch):
    """Konsolide/IEX oranı ancak iki hacim YAN YANA olduğunda ölçülebilir — sip bunu massive'den
    bir tur önce sağlar. Eski tasarımda o ölçüm YALNIZ massive'e bağlıydı ve grouped gecikince
    yedek katman bütün gece kör kalıyordu."""
    from meridian.adapters import data
    _seed_provisional(iex_volume=5_000.0, ratio=20.0)
    _sip_env(monkeypatch, close=10.4, volume=120_000.0)
    data.sip_correct_provisional()
    row = data._se()["volume_ratio"]["AAA"]
    assert row["source"] == "sip_correction"
    assert 24.0 in row["samples"] and 20.0 in row["samples"]       # 120.000 / 5.000
    assert data._volume_ratio("AAA") == 22.0                      # medyan(20, 24)


def test_the_same_iex_volume_is_never_counted_twice(sandbox_state, monkeypatch):
    """UYDURMA YASAĞININ İNCE HÂLİ: aynı IEX hacmini önce sip'le sonra massive'le eşleştirmek, TEK
    bir gerçeği iki BAĞIMSIZ örnek gibi saymak olurdu — medyanı sahte bir güvenle daraltırdı.
    Ölçüm TÜKETİLİR: `iex_volume` defterden düşer ve nihai otorite yalnız FİYAT farkını ölçer."""
    from meridian.adapters import data, fmp, massive
    _seed_provisional(iex_volume=5_000.0, ratio=20.0)
    _sip_env(monkeypatch, close=10.4, volume=120_000.0)
    data.sip_correct_provisional()
    assert data._se()["provisional"]["AAA"][SESSION]["iex_volume"] is None
    n0 = len(data._se()["volume_ratio"]["AAA"]["samples"])
    monkeypatch.setattr(fmp, "available", lambda: False)
    monkeypatch.setattr(data, "_fetch_cboe", lambda t, to: pd.DataFrame())
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda t, s, e, to: pd.DataFrame())
    monkeypatch.setattr(massive, "available", lambda: True)
    monkeypatch.setattr(massive, "write_enabled", lambda: True)
    monkeypatch.setattr(massive, "covers", lambda s: False)
    monkeypatch.setattr(massive, "latest_bar", lambda t, end=None: {
        "date": SESSION, "open": 10.5, "high": 10.5, "low": 10.5, "close": 10.5, "volume": 125_000.0})
    monkeypatch.setattr(data, "_massive_crosscheck", lambda *a, **k: None)
    data.load_bars("AAA", "2021-01-01", "2026-07-30", use_cache=False)
    data.flush_same_evening()
    row = data._se()["volume_ratio"]["AAA"]
    assert len(row["samples"]) == n0 and row["source"] == "sip_correction"
    assert 25.0 not in row["samples"], "125.000/5.000 ikinci kez örnek sayıldı"


def test_the_corrector_never_touches_the_current_session(sandbox_state, monkeypatch):
    """Düzelticinin kendisi de aynı yasaya tabidir: BUGÜNÜN geçici satırı için sip'e HİÇ sorulmaz —
    yoksa düzeltici, düzeltmeye çalıştığı 403'ü kendisi üretirdi."""
    from meridian.adapters import data
    _seed_provisional(session=TODAY)
    seen = _sip_env(monkeypatch, session=TODAY, today=TODAY)
    rep = data.sip_correct_provisional()
    assert rep["targets"] == 0 and rep["corrected"] == 0 and rep["asked_sessions"] == 0
    assert seen["sip"] == []
    assert data._se()["provisional"]["AAA"][TODAY]["source"] == data.ALPACA_SOURCE


def test_the_corrector_never_creates_a_row(sandbox_state, monkeypatch):
    """`_overwrite_bar` YALNIZ var olanı değiştirir, yeni tarih AÇMAZ (delik doldurma onarım
    geçidinin işidir). İkisi tek fonksiyona sıkışsaydı bacak geçmiş kurabilir hâle gelirdi."""
    from meridian.adapters import data
    _seed_cache("AAA", "2026-07-28", n=220)
    before = pd.read_csv(data._cache_path("AAA"))
    assert data._overwrite_bar("AAA", {"date": SESSION, "open": 1.0, "high": 1.0, "low": 1.0,
                                       "close": 9.9, "volume": 7.0}) is False
    after = pd.read_csv(data._cache_path("AAA"))
    assert len(after) == len(before) and str(after["date"].max())[:10] == "2026-07-28"


def test_a_correction_is_not_a_silent_bar_mutation(sandbox_state, monkeypatch):
    """EN KRİTİK NOKTA (v133'ün aynı yasası, yeni yazıcı): sip düzelticisi GEÇMİŞİ değiştirir, bu
    yüzden wf revizyonunu BUMPLAR ve watchdog `rev_bumped` görüp mutasyonu sessiz saymaz."""
    from meridian import watchdog
    from meridian.adapters import data
    _seed_provisional()
    watchdog.determinism_report(persist=True)                     # TABAN: düzeltme ÖNCESİ
    rev0 = int(store.read_json("wf_cache_rev.json", {}).get("rev", 0))
    _sip_env(monkeypatch, close=10.4, volume=120_000.0)
    assert data.sip_correct_provisional()["corrected"] == 1
    rep = watchdog.determinism_report()
    assert rep["ok"] is True, f"sip düzeltmesi SESSİZ MUTASYON sayıldı: {rep}"
    assert rep["rev_bumped"] is True
    assert int(store.read_json("wf_cache_rev.json", {}).get("rev", 0)) > rev0


def test_no_answer_is_not_a_correction(sandbox_state, monkeypatch):
    """HÜKÜM YOK ≠ DÜZELTİLDİ: uç cevap vermezse satır TEMSİLÎ kalır, damga durur ve massive nihai
    otorite olarak beklemeye devam eder (uydurma konsolide değer yazılmaz)."""
    from meridian.adapters import alpaca, data
    cp = _seed_provisional()
    monkeypatch.setattr(alpaca, "data_available", lambda: True)
    _keys(monkeypatch, today=TODAY)
    _router(monkeypatch, sip={"message": "rate limit"}, sip_status=429)
    rep = data.sip_correct_provisional()
    assert rep["corrected"] == 0 and rep["sessions"][SESSION]["verdict"] == "no_answer"
    row = pd.read_csv(cp, parse_dates=["date"])
    got = row[row["date"] == pd.Timestamp(SESSION)].iloc[0]
    assert float(got["close"]) == 10.0                             # temsilî değer YERİNDE
    assert data._se()["provisional"]["AAA"][SESSION]["source"] == data.ALPACA_SOURCE


def test_a_corrected_row_is_never_asked_twice(sandbox_state, monkeypatch):
    """Sip'e taşınmış bir satır ikinci koşuda yeniden SORULMAZ — yoksa her seans başına aynı evren
    için boşuna bir çağrı turu daha yakılırdı."""
    from meridian.adapters import data
    _seed_provisional()
    seen = _sip_env(monkeypatch, close=10.4, volume=120_000.0)
    data.sip_correct_provisional()
    n = len(seen["sip"])
    rep2 = data.sip_correct_provisional()
    assert rep2["targets"] == 0 and len(seen["sip"]) == n


# ==================================================================================================
# 5) KABLOLAMA + YASA 6 — düzeltici bir kadansa bağlı ve ölçümün DIŞ okuyucusu var
# ==================================================================================================
def test_the_corrector_runs_in_the_once_per_session_repair_cadence(sandbox_state, monkeypatch):
    """ÖLÜ MEKANİZMA SIFIR: düzeltici bir üretim kadansına KABLOLUDUR ve massive yollarından ÖNCE
    koşar (sıra kodda görünür: önce elimizdekini düzelt, sonra deliği kapat)."""
    from meridian import scheduler
    from meridian.adapters import data as _da
    order = []
    monkeypatch.setattr(_da, "sip_correct_provisional",
                        lambda *a, **k: (order.append("sip"), {"corrected": 2})[1])
    monkeypatch.setattr(_da, "repair_coverage", lambda *a, **k: (order.append("repair"), {})[1])
    monkeypatch.setattr(_da, "volume_calibration_stale", lambda: False)
    scheduler._repair_once_per_session(SESSION)
    assert order == ["sip", "repair"], f"kadans sırası bozuk: {order}"
    assert scheduler._state["last_sip_correction"] == {"corrected": 2}


def test_a_failing_corrector_is_loud(sandbox_state, monkeypatch):
    """YASA 4: düzeltici düşerse dünün satırları TEMSİLÎ kalır ve konsolideye dönmeleri yeniden TEK
    kaynağa (massive) bağlanır — bu turun kök nedeninin ta kendisi. Sessiz kalamaz."""
    from meridian import scheduler
    from meridian.adapters import data as _da

    def _boom(*a, **k):
        raise RuntimeError("uç düştü")

    monkeypatch.setattr(_da, "sip_correct_provisional", _boom)
    monkeypatch.setattr(_da, "repair_coverage", lambda *a, **k: {})
    monkeypatch.setattr(_da, "volume_calibration_stale", lambda: False)
    scheduler._repair_once_per_session(SESSION)
    ev = _events("sip_correction_failed")
    assert ev and "RuntimeError" in ev[-1]["error"]


def test_the_per_source_breakdown_has_an_external_reader(sandbox_state, monkeypatch):
    """YASA 6: ölçümü `adapters/data.py` yazar, `scheduler.status()` DIŞARIDAN okur → /api/hermes
    `scheduler` + /api/scheduler → pano. Okuyucusu olmayan bir ölçüm, üretilip tüketilmeyen kanıttır."""
    from meridian import scheduler
    from meridian.adapters import data
    monkeypatch.setattr(scheduler, "_last_closed_session", lambda: SESSION)
    assert scheduler.status()["bar_upgrade"]["by_source"] == {}     # ölçüm yok → boş, uydurma yok
    _seed_provisional()
    _sip_env(monkeypatch, close=10.4, volume=120_000.0)
    data.sip_correct_provisional()
    st = scheduler.status()["bar_upgrade"]
    assert st["last_session"] == SESSION
    assert st["by_source"]["alpaca_sip"]["max_dev_pct"] == pytest.approx(4.0, abs=1e-6)
    assert store.read_json(data.SAME_EVENING_FILE, None) is not None    # defter GERÇEKTEN diskte

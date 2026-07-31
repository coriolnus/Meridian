"""v133 — AYNI-AKŞAM BACAĞI (Alpaca sip → iex) + T+1 DÜZELTME + ONARIM GEÇİDİ + MERDİVEN.

Ölçülmüş kök neden (Rol 1): bar zincirinin en taze kolu (Massive grouped, ücretsiz katman) T+1
yayınlıyor — state/massive_grouped_last.json: date 07-28, fetched_at 07-29 21:15Z. Kapanış sonrası
40 dakikalık pencerede yalnız cboe/nasdaq kısmileri geliyor; 07-29 barı ertesi gün hâlâ 259 sembolün
44'ünde (kapsama 0,172). Zamanlayıcı 8×300 sn sonra seansı KALICI atlıyor ve her seans için sahte bir
"SEANS ATLANDI" alarmı üretiyordu (164 tarihsel satır, tek imza).

Bu dosya dört yasayı çiviler:
  1. BACAK   — yalnız canlı yolda, yalnız açık kalan seans için; zincir seansı verdiyse DEVREYE
                GİRMEZ. İki basamak (konsolide sip → temsilî iex), hangisi servis etti damgada.
  2. DÜZELTME — T+1'de otoriter kaynak geçici barı EZER; bu, watchdog'un determinizm kontrolüne
                "sessiz bar mutasyonu" olarak YAKALANMAZ (wf revizyonu bumplanır) ve ıraksama ÖLÇÜLÜR.
  3. HACİM   — yalnız yedek basamakta (iex) hacim konsolide DEĞİLDİR; ölçülmüş oranla ölçeklenir,
                oran yoksa UYDURULMAZ. Konsolide basamaklarda hacim ham yazılır.
  4. MERDİVEN — sık faz aynen, sonra seyrek faz; terminal atlama YALNIZ bir sonraki seans kapanınca.

⚠ v139 DÜZELTMESİ (2026-07-30, canlı ölçüm): 1. yasanın "iki basamak" cümlesi HEDEF SEANSA GÖRE
koşulludur. Konsolide (sip) basamak yalnız GEÇMİŞ takvim günleri için denenir; bugünün seansı için
sip garantili 403 döndüğü için basamak BİLİNÇLİ atlanır ve aynı akşamı iex servis eder. Buradaki
sip testleri artık takvim gününü SABİTLİYOR (`_keys(..., today=...)`); yeni yasanın kendi dosyası
`tests/test_sip_gecmis_seans_v139.py`.

NOT (Rol 1'e): `tests/test_data_pipeline_v67.py::test_giving_up_on_a_session_is_loud_and_bounded`
ESKİ yasayı çiviliyor ("8. denemede pes et ve alarm at"). Yeni yasa o alarmı son tarihe erteliyor;
o testin yerini aşağıdaki `test_terminal_skip_only_when_the_next_session_closes` alır.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest

from meridian import store


# ---------------------------------------------------------------- ortak yardımcılar
@pytest.fixture(autouse=True)
def _reset_module_state():
    """Bacak/defter süreç-içi önbellekleri modül düzeyindedir — testler arası taşınırsa bir test
    kendi kurmadığı bir defterle 'geçiyor' görünür (conftest'in aynı dersi, yeni yüzey)."""
    from meridian.adapters import alpaca, data
    _dicts = (data._ALPACA_MEMO, data._ALPACA_ASKED, data._ALPACA_PENDING, data._LAST_SOURCE,
              alpaca._DATA_FAIL_AT, alpaca._DATA_COOLDOWN, alpaca._DATA_LAST_FAIL)

    def _sifirla():
        for d in _dicts:
            d.clear()
        # TAŞIMA SAĞLIK KAYITLARI DA MODÜL GLOBALİDİR (2026-07-30, tam suite bulgusu): bu dosya
        # "veri ucu TİCARET taşıma kaydını kirletmiyor" diye ölçüyor ve o ölçüm MUTLAK sayaçlara
        # bakıyor. Komşu alpaca testleri (account/orders/submit mock'ları) `_TRANSPORT["calls"]`i
        # 39'a çıkarınca test TEK BAŞINA yeşil, PAKET İÇİNDE kırmızı oluyordu — yani ölçülen şey
        # dedektör değil, sıra. Sözlükler YERİNDE temizlenir (clear+update): yeni bir dict atamak
        # `transport()`/`data_transport()` dışındaki modül referanslarını koparır ve sıfırlama
        # hiçbir şeye dokunmamış olurdu (conftest'in `fmp._HEALTH` dersinin aynısı). Literaller
        # alpaca.py'deki başlangıç değerleridir.
        alpaca._TRANSPORT.clear()
        alpaca._TRANSPORT.update({"ok": True, "error": "", "at": None, "calls": 0, "fails": 0,
                                  "consecutive_fails": 0})
        alpaca._DATA_TRANSPORT.clear()
        alpaca._DATA_TRANSPORT.update({"ok": None, "calls": 0, "fails": 0, "last_status": None,
                                       "last_error": "", "at": None})
        data._SE = {}
        data._SE_PENDING_EVENT.clear()

    _sifirla()
    data._SE_DIRTY = 0
    data._XCHECK = {}
    data._SEAMS = {}
    data._NO_DATA = {}
    yield
    _sifirla()          # kendi kirimizi de bırakmayız: sızıntı iki yönlü ölçülür


def _bars(dates, close=100.0, volume=1_000_000.0):
    return pd.DataFrame({"date": pd.to_datetime(list(dates)),
                         "open": [close] * len(dates), "high": [close * 1.01] * len(dates),
                         "low": [close * 0.99] * len(dates), "close": [close] * len(dates),
                         "volume": [volume] * len(dates)})


def _seed_cache(ticker: str, last: str, n: int = 220, close: float = 100.0,
                volume: float = 1_000_000.0):
    """Diske GERÇEK bir önbellek yaz: bacak yalnız geçmişi olan sembolde çalışır (incremental_ok)."""
    from meridian.adapters import data
    dates = pd.bdate_range(end=pd.Timestamp(last), periods=n)
    df = _bars([str(d.date()) for d in dates], close=close, volume=volume)
    cp = data._cache_path(ticker)
    cp.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(cp, index=False)
    return df


def _events(name: str) -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl")
            if e.get("event") == name or e.get("kind") == name]


class _Resp:
    def __init__(self, payload, status=200):
        self._p, self.status_code = payload, status

    def json(self):
        return self._p

    @property
    def text(self):
        import json
        return json.dumps(self._p)


# ==================================================================================================
# 1) ALPACA VERİ UCU — ayrıştırma, çoklu sembol, sayfalama, hata
# ==================================================================================================
def test_snapshot_request_shape_is_the_documented_one(sandbox_state, monkeypatch):
    """Uç, başlıklar ve feed AÇIKÇA gönderilir — varsayılana yaslanmak, aboneliği değişen bir
    hesapta sessizce BAŞKA bir veri katmanına geçmek olurdu."""
    from meridian.adapters import alpaca
    seen = {}

    def _get(url, params=None, headers=None, timeout=None):
        seen.update(url=url, params=params, headers=headers)
        return _Resp({"AAPL": {"dailyBar": {"t": "2026-07-29T04:00:00Z", "o": 1, "h": 2, "l": 1,
                                            "c": 1.5, "v": 10}}})

    monkeypatch.setattr(alpaca.httpx, "get", _get)
    monkeypatch.setattr(alpaca.secrets, "present", lambda n: True)
    monkeypatch.setattr(alpaca.secrets, "get", lambda n: "K" if "KEY" in n else "S")
    got = alpaca.snapshots(["AAPL"])
    assert got and "AAPL" in got
    assert seen["url"] == "https://data.alpaca.markets/v2/stocks/snapshots"
    assert seen["params"]["symbols"] == "AAPL" and seen["params"]["feed"] == "iex"
    assert seen["headers"]["APCA-API-KEY-ID"] == "K" and seen["headers"]["APCA-API-SECRET-KEY"] == "S"
    # TİCARET UCU KİRLENMEDİ: veri isteği broker taşıma sağlığına yazmaz (mutabakat o bayrağa bakıyor)
    assert alpaca.transport()["calls"] == 0 and alpaca.data_transport()["calls"] == 1


def test_multi_symbol_requests_are_chunked(sandbox_state, monkeypatch):
    from meridian.adapters import alpaca
    calls = []

    def _get(url, params=None, headers=None, timeout=None):
        calls.append(params["symbols"].split(","))
        return _Resp({s: {"dailyBar": {"t": "2026-07-29T04:00:00Z", "c": 5.0, "v": 1}}
                      for s in params["symbols"].split(",")})

    monkeypatch.setattr(alpaca.httpx, "get", _get)
    monkeypatch.setattr(alpaca.secrets, "present", lambda n: True)
    monkeypatch.setattr(alpaca.secrets, "get", lambda n: "x")
    syms = [f"T{i:03d}" for i in range(259)]
    got = alpaca.snapshots(syms)
    assert len(calls) == 3 and max(len(c) for c in calls) <= alpaca.DATA_CHUNK
    assert len(got) == 259


def test_a_bar_from_another_session_is_never_counted(sandbox_state, monkeypatch):
    """SEANS İÇİ ÇAĞRIDA kısmî bar döner ve tarihi bugündür. Hedef seansı tutmayan bar 'gelmedi'
    sayılır — uydurma yok, eksik kalır (kapsama düşer, kapı muhafazakâr tarafta durur)."""
    from meridian.adapters import alpaca
    monkeypatch.setattr(alpaca.secrets, "present", lambda n: True)
    monkeypatch.setattr(alpaca.secrets, "get", lambda n: "x")
    monkeypatch.setattr(alpaca.httpx, "get", lambda *a, **k: _Resp({
        "AAA": {"dailyBar": {"t": "2026-07-29T04:00:00Z", "c": 10.0, "v": 3}},
        "BBB": {"dailyBar": {"t": "2026-07-28T04:00:00Z", "c": 20.0, "v": 4}},   # ÖNCEKİ seans
        "CCC": {"dailyBar": {}}}))                                                # damgasız
    got = alpaca.session_bars(["AAA", "BBB", "CCC"], "2026-07-29")
    assert set(got) == {"AAA"} and got["AAA"]["close"] == 10.0
    ev = _events("alpaca_session_bars")[-1]
    assert ev["matched"] == 1 and ev["other_session"] == 1


def test_daily_bars_follows_pagination(sandbox_state, monkeypatch):
    """Kalibrasyon bootstrap'ı sayfalamayı İZLER; izlemezse örneklem sessizce yarım kalırdı."""
    from meridian.adapters import alpaca
    pages = [{"bars": {"AAA": [{"t": "2026-07-27T04:00:00Z", "c": 1.0, "v": 10}]},
              "next_page_token": "p2"},
             {"bars": {"AAA": [{"t": "2026-07-28T04:00:00Z", "c": 2.0, "v": 20}]},
              "next_page_token": None}]
    seen = []

    def _get(url, params=None, headers=None, timeout=None):
        seen.append(params.get("page_token"))
        return _Resp(pages[len(seen) - 1])

    monkeypatch.setattr(alpaca.httpx, "get", _get)
    monkeypatch.setattr(alpaca.secrets, "present", lambda n: True)
    monkeypatch.setattr(alpaca.secrets, "get", lambda n: "x")
    got = alpaca.daily_bars(["AAA"], "2026-07-01", "2026-07-29")
    assert [b["date"] for b in got["AAA"]] == ["2026-07-27", "2026-07-28"]
    assert seen == [None, "p2"]
    # ölçek: zincirin geri kalanı BÖLÜNME düzeltmelidir; ham ölçek iki ayrı ayarlamayı birbirine eklerdi
    assert pages and alpaca.DATA_MAX_PAGES > 1


def test_a_failed_leg_is_loud_and_then_cools_down(sandbox_state, monkeypatch):
    """429 SESSİZCE YUTULMAZ ve 259 sembollük tur aynı düşmüş ucu 259 kez denemez."""
    from meridian.adapters import alpaca
    n = {"calls": 0}

    def _get(url, params=None, headers=None, timeout=None):
        n["calls"] += 1
        return _Resp({"message": "rate limit"}, status=429)

    monkeypatch.setattr(alpaca.httpx, "get", _get)
    monkeypatch.setattr(alpaca.secrets, "present", lambda n_: True)
    monkeypatch.setattr(alpaca.secrets, "get", lambda n_: "x")
    assert alpaca.snapshots(["AAA"]) is None            # None = HÜKÜM YOK (boş sonuç DEĞİL)
    assert alpaca.snapshots(["AAA"]) is None
    assert n["calls"] == 1, "soğuma penceresi yok — sağlayıcı dövülüyor"
    ev = _events("alpaca_data_failed")
    assert ev and ev[-1]["reason"] == "HTTP 429" and ev[-1]["leg"] == "snapshots:iex"
    assert alpaca.data_transport()["ok"] is False


def _keys(monkeypatch, today: str = "2026-07-30"):
    """Anahtarlar + TAKVİM GÜNÜ SABİTLENİR (v139 tasarım düzeltmesi).

    Sabitleme şart: sip basamağı artık hedef seansın BUGÜN olup olmadığına bakıyor ve duvar saatine
    bağlı bir test, bu dosyanın 2026-07-29'da yeşil, 2026-07-30'da kırmızı olması demekti — yani
    tam da bu turda avladığımız 'kodda örtük zaman varsayımı' sınıfının test tarafındaki ikizi."""
    from meridian.adapters import alpaca
    monkeypatch.setattr(alpaca.secrets, "present", lambda n: True)
    monkeypatch.setattr(alpaca.secrets, "get", lambda n: "x")
    monkeypatch.setattr(alpaca, "market_calendar_day", lambda: today)


def test_the_primary_layer_is_consolidated_sip_for_a_past_session(sandbox_state, monkeypatch):
    """BİRİNCİL — AMA GEÇMİŞ SEANS İÇİN (v139'da daraltıldı; eski ad 'aynı akşam da birincil'
    iddiasını taşıyordu ve o iddia canlıda çürüdü). Damga `alpaca_sip`, hacim ÖLÇEKLENMEZ — bu barın
    hacmi zaten tüm piyasadır."""
    from meridian.adapters import alpaca
    seen = []
    _keys(monkeypatch, today="2026-07-30")          # hedef 07-29 → GEÇMİŞ takvim günü
    monkeypatch.setattr(alpaca.httpx, "get", lambda url, params=None, headers=None, timeout=None:
                        (seen.append((url, params)),
                         _Resp({"bars": {"AAA": [{"t": "2026-07-29T04:00:00Z", "o": 1.0, "h": 1.0,
                                                  "l": 1.0, "c": 10.0, "v": 9_000_000.0}]},
                                "next_page_token": None}))[1])
    res = alpaca.same_evening_bars(["AAA"], "2026-07-29")
    assert res["source"] == "alpaca_sip" and res["bars"]["AAA"]["volume"] == 9_000_000.0
    url, params = seen[0]
    assert url.endswith("/v2/stocks/bars") and params["feed"] == "sip"
    assert params["timeframe"] == "1Day" and params["start"] == params["end"] == "2026-07-29"
    assert params["adjustment"] == "split"                 # zincirin geri kalanıyla AYNI ölçek
    assert _events("alpaca_same_evening")[-1]["source"] == "alpaca_sip"


def test_a_sip_refusal_falls_back_to_iex_and_says_so(sandbox_state, monkeypatch):
    """YEDEK KATMAN: sip GEÇMİŞ bir seansta abonelik tarafından reddedilirse HAM hata metniyle
    kaydedilir ve iex snapshot + hacim kalibrasyonu yoluna düşülür. v139 notu: bu satır artık
    GERÇEKTEN bir yetki bulgusudur — 'recent SIP' koşulundan doğan 403 buraya HİÇ gelmez, çünkü
    bugünün seansı için sip zaten sorulmuyor (bkz. v139 dosyası)."""
    from meridian.adapters import alpaca
    _keys(monkeypatch, today="2026-07-30")          # hedef 07-29 → GEÇMİŞ; 403 koşul değil ARIZA

    def _get(url, params=None, headers=None, timeout=None):
        if url.endswith("/v2/stocks/bars"):
            return _Resp({"message": "subscription does not permit querying recent SIP data"},
                         status=403)
        return _Resp({"AAA": {"dailyBar": {"t": "2026-07-29T04:00:00Z", "c": 10.0, "v": 5_000.0}}})

    monkeypatch.setattr(alpaca.httpx, "get", _get)
    res = alpaca.same_evening_bars(["AAA"], "2026-07-29")
    assert res["source"] == "alpaca_iex" and res["bars"]["AAA"]["volume"] == 5_000.0
    ev = _events("alpaca_sip_rejected")
    assert ev and ev[-1]["feed"] == "sip" and "subscription" in ev[-1]["body"]
    # ABONELİK REDDİ GEÇİCİ DEĞİLDİR: kısa soğuma her turda boşa bir çağrı yakardı
    assert alpaca._DATA_COOLDOWN["bars:sip"] == alpaca.SIP_REJECT_COOLDOWN_S


def test_a_bad_request_is_not_read_as_a_subscription_refusal(sandbox_state, monkeypatch):
    """ÖLÇÜLMÜŞ TUZAK (Rol 1, canlı): `feed=delayed_sip` bu uçta HTTP 400 {"invalid feed"} döner.
    400'ü "abonelik reddetti" saymak defterde SAHTE bir yetki hikâyesi ve 6 saatlik yanlış soğuma
    üretirdi. 400 geçici arıza gibi ele alınır ve `alpaca_sip_rejected` ATILMAZ."""
    from meridian.adapters import alpaca
    _keys(monkeypatch, today="2026-07-30")

    def _get(url, params=None, headers=None, timeout=None):
        if url.endswith("/v2/stocks/bars"):
            return _Resp({"message": "invalid feed: delayed_sip"}, status=400)
        return _Resp({"AAA": {"dailyBar": {"t": "2026-07-29T04:00:00Z", "c": 10.0, "v": 5_000.0}}})

    monkeypatch.setattr(alpaca.httpx, "get", _get)
    res = alpaca.same_evening_bars(["AAA"], "2026-07-29")
    assert res["source"] == "alpaca_iex"                      # düşüş yine olur (veri lazım)
    assert _events("alpaca_sip_rejected") == [], "400 abonelik reddi sanıldı"
    assert alpaca._DATA_COOLDOWN["bars:sip"] == alpaca.DATA_FAIL_COOLDOWN_S
    assert _events("alpaca_data_failed"), "arıza sessizce yutuldu"


def test_no_layer_no_claim(sandbox_state, monkeypatch):
    """Hiçbir katman veremediyse kaynak damgası None — 'veri yok' ile 'bar üretildi' karışmaz."""
    from meridian.adapters import alpaca
    _keys(monkeypatch, today="2026-07-30")
    monkeypatch.setattr(alpaca.httpx, "get",
                        lambda *a, **k: _Resp({"bars": {}, "next_page_token": None}))
    res = alpaca.same_evening_bars(["AAA"], "2026-07-29")
    assert res["source"] is None and res["bars"] == {}


# ==================================================================================================
# 2) ZİNCİRDEKİ KONUM — yalnız canlı yol, yalnız açık kalan seans
# ==================================================================================================
def _chain_env(monkeypatch, cboe_dates=("2026-07-28",), leg_bar=None, leg_calls=None,
               leg_source="alpaca_sip"):
    """Massive/FMP kapalı, Cboe bir seans GERİDE — yani zincir güncel seansı veremiyor."""
    from meridian.adapters import alpaca, data, fmp, massive
    monkeypatch.setattr(massive, "available", lambda: False)
    monkeypatch.setattr(massive, "write_enabled", lambda: False)
    monkeypatch.setattr(fmp, "available", lambda: False)
    monkeypatch.setattr(data, "_fetch_cboe", lambda t, to: _bars(cboe_dates))
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda t, s, e, to: pd.DataFrame())
    monkeypatch.setattr(alpaca, "data_available", lambda: True)

    def _leg(syms, session, timeout=30.0):
        if leg_calls is not None:
            leg_calls.append((tuple(syms), session))
        if not leg_bar:
            return {"source": None, "bars": {}, "detail": "yok"}
        c = float(leg_bar["close"])
        full = {"open": c, "high": c, "low": c, **leg_bar, "date": session}
        return {"source": leg_source, "bars": {s.upper(): dict(full) for s in syms}}

    monkeypatch.setattr(alpaca, "same_evening_bars", _leg)


def test_the_leg_fills_the_open_session_on_the_live_path(sandbox_state, monkeypatch):
    from meridian.adapters import data
    calls = []
    _chain_env(monkeypatch, leg_bar={"open": 9.9, "high": 10.2, "low": 9.8, "close": 10.0,
                                     "volume": 5_000.0}, leg_calls=calls)
    with data.live_session_leg("2026-07-29"):
        got = data.fetch("AAA", "2021-01-01", "2026-07-29", incremental_ok=True)
    assert str(got["date"].max().date()) == "2026-07-29"
    # BİRİNCİL KATMAN: konsolide (sip) — damga tahmin edilmez, çağrının söylediği ad kullanılır
    assert data._LAST_SOURCE["AAA"] == data.ALPACA_SIP_SOURCE == "alpaca_sip"
    # EVREN TEK GRUPTA SORULUR: 259 sembol için sembol-başına istek atmak kotayı yakardı
    assert calls and len(calls[0][0]) > 100 and "AAA" in calls[0][0]


def test_the_replay_path_never_sees_the_leg(sandbox_state, monkeypatch):
    """`dataset.load` (replay/karantina) bacağı GÖRMEZ: bugünün temsilî barı 2023 replay'ine sızarsa
    bu, look-ahead karantinasının ta kendisidir."""
    from meridian.adapters import data
    calls = []
    _chain_env(monkeypatch, leg_bar={"close": 10.0, "volume": 5_000.0}, leg_calls=calls)
    got = data.fetch("AAA", "2021-01-01", "2026-07-29", incremental_ok=True)   # kapı AÇIK DEĞİL
    assert calls == [], "bacak canlı kapı olmadan çalıştı"
    assert str(got["date"].max().date()) == "2026-07-28"
    assert data._LAST_SOURCE["AAA"] == "cboe"


def test_the_leg_stands_down_when_the_chain_already_has_the_session(sandbox_state, monkeypatch):
    """KONSOLİDE VERİ KAZANIR: zincir seansı verdiyse temsilî IEX barına hiç ihtiyaç yoktur."""
    from meridian.adapters import data
    calls = []
    _chain_env(monkeypatch, cboe_dates=("2026-07-28", "2026-07-29"),
               leg_bar={"close": 10.0, "volume": 5_000.0}, leg_calls=calls)
    with data.live_session_leg("2026-07-29"):
        got = data.fetch("AAA", "2021-01-01", "2026-07-29", incremental_ok=True)
    assert calls == [] and data._LAST_SOURCE["AAA"] == "cboe" and len(got) == 2


def test_the_leg_stands_down_without_history(sandbox_state, monkeypatch):
    """Tek bar bir GEÇMİŞ kuramaz (massive kolunun aynı disiplini) — derin backfill zincirin işidir."""
    from meridian.adapters import data
    calls = []
    _chain_env(monkeypatch, leg_bar={"close": 10.0, "volume": 5_000.0}, leg_calls=calls)
    with data.live_session_leg("2026-07-29"):
        data.fetch("AAA", "2021-01-01", "2026-07-29", incremental_ok=False)
    assert calls == []


def test_the_leg_never_writes_into_history(sandbox_state, monkeypatch):
    """Bacak yalnız önbelleğin son barından SONRASINI yazar: temsilî bir bar KONSOLİDE bir barı ezemez."""
    from meridian.adapters import data
    _seed_cache("AAA", "2026-07-29", n=220, close=100.0)          # 07-29 zaten KONSOLİDE olarak var
    _chain_env(monkeypatch, leg_bar={"close": 55.0, "volume": 5_000.0})
    with data.live_session_leg("2026-07-29"):
        out = data.load_bars("AAA", "2021-01-01", "2026-07-29", use_cache=False)
    assert float(out[out["date"] == pd.Timestamp("2026-07-29")]["close"].iloc[0]) == 100.0


# ==================================================================================================
# 3) HACİM — IEX hacmi konsolide DEĞİLDİR
# ==================================================================================================
def test_iex_volume_is_scaled_by_the_measured_ratio(sandbox_state, monkeypatch):
    from meridian.adapters import data
    _seed_cache("AAA", "2026-07-28")
    _chain_env(monkeypatch, leg_bar={"close": 10.0, "volume": 5_000.0}, leg_source="alpaca_iex")
    data._set_volume_ratio("AAA", [20.0, 20.0, 20.0], "bootstrap")
    with data.live_session_leg("2026-07-29"):
        out = data.load_bars("AAA", "2021-01-01", "2026-07-29", use_cache=False)
    row = out[out["date"] == pd.Timestamp("2026-07-29")].iloc[0]
    assert float(row["volume"]) == 100_000.0, "IEX hacmi ölçeklenmedi — rvol sessizce 0'a çökerdi"
    prov = data._se()["provisional"]["AAA"]["2026-07-29"]
    assert prov["volume_scaled"] is True and prov["iex_volume"] == 5_000.0 and prov["ratio"] == 20.0


def test_an_unmeasured_ratio_never_fabricates_a_volume(sandbox_state, monkeypatch):
    """Oran ölçülmemişse hacim UYDURULMAZ. Fiyat barı sayılır (kapsama deliği kapanır), hacim 0
    yazılır — hacim türevleri o barda muhafazakâr tarafta kapanır ve damga bunu SÖYLER."""
    from meridian.adapters import data
    _seed_cache("AAA", "2026-07-28")
    _chain_env(monkeypatch, leg_bar={"close": 10.0, "volume": 5_000.0}, leg_source="alpaca_iex")
    with data.live_session_leg("2026-07-29"):
        out = data.load_bars("AAA", "2021-01-01", "2026-07-29", use_cache=False)
    row = out[out["date"] == pd.Timestamp("2026-07-29")].iloc[0]
    assert float(row["close"]) == 10.0 and float(row["volume"]) == 0.0
    assert data._se()["provisional"]["AAA"]["2026-07-29"]["volume_scaled"] is False
    assert data._volume_ratio("AAA") is None


def test_volume_calibration_measures_the_ratio_from_overlapping_days(sandbox_state, monkeypatch):
    from meridian.adapters import alpaca, data
    _seed_cache("AAA", "2026-07-28", n=220, volume=1_000_000.0)
    iex = [{"date": str(d.date()), "close": 1.0, "volume": 50_000.0}
           for d in pd.bdate_range(end=pd.Timestamp("2026-07-28"), periods=10)]
    monkeypatch.setattr(alpaca, "data_available", lambda: True)
    monkeypatch.setattr(alpaca, "daily_bars", lambda s, a, b, **k: {"AAA": iex})
    rep = data.calibrate_volume(["AAA"])
    assert rep["calibrated"] == 1 and rep["unmeasured"] == []
    assert data._volume_ratio("AAA") == 20.0
    # ÖLÇÜLEMEYEN SEMBOL: oran YOK (None), varsayılan oran uydurulmuyor
    rep2 = data.calibrate_volume(["BBB"])
    assert rep2["unmeasured"] == ["BBB"] and data._volume_ratio("BBB") is None
    assert _events("alpaca_volume_calibrated")


def test_calibration_is_stale_when_never_measured(sandbox_state):
    from meridian.adapters import data
    assert data.volume_calibration_stale() is True
    data._set_volume_ratio("AAA", [12.0], "bootstrap")
    assert data.volume_calibration_stale() is False


# ==================================================================================================
# 4) T+1 OTORİTER DÜZELTME — determinizm kontrolüyle bütünleşme + ÖLÇÜM
# ==================================================================================================
def _t1_upgrade(sandbox_state, monkeypatch, iex_close=10.0, real_close=10.4, real_vol=120_000.0):
    """Bir seansı önce IEX ile yaz, ertesi gün Massive grouped ile DÜZELT."""
    from meridian.adapters import data, massive
    _seed_cache("AAA", "2026-07-28")
    _chain_env(monkeypatch, leg_bar={"close": iex_close, "volume": 5_000.0},
               leg_source="alpaca_iex")     # YEDEK katman: hacim oranı ölçümü buradan doğar
    data._set_volume_ratio("AAA", [20.0], "bootstrap")
    with data.live_session_leg("2026-07-29"):
        data.load_bars("AAA", "2021-01-01", "2026-07-29", use_cache=False)
    data.flush_same_evening()
    assert "2026-07-29" in data._provisional_dates("AAA")
    # --- ertesi gün: grouped 07-29'u YAYINLADI ---
    monkeypatch.setattr(massive, "available", lambda: True)
    monkeypatch.setattr(massive, "write_enabled", lambda: True)
    monkeypatch.setattr(massive, "covers", lambda s: False)
    monkeypatch.setattr(massive, "latest_bar", lambda t, end=None: {
        "date": "2026-07-29", "open": real_close, "high": real_close, "low": real_close,
        "close": real_close, "volume": real_vol})
    monkeypatch.setattr(data, "_massive_crosscheck", lambda *a, **k: None)
    out = data.load_bars("AAA", "2021-01-01", "2026-07-30", use_cache=False)
    data.flush_same_evening()
    return out


def test_the_authoritative_source_overwrites_the_provisional_bar(sandbox_state, monkeypatch):
    from meridian.adapters import data
    out = _t1_upgrade(sandbox_state, monkeypatch)
    row = out[out["date"] == pd.Timestamp("2026-07-29")].iloc[0]
    assert float(row["close"]) == 10.4 and float(row["volume"]) == 120_000.0
    assert data._provisional_dates("AAA") == set(), "geçici damga kalkmadı — bar iki kez düzeltilirdi"


def test_the_correction_is_not_a_silent_bar_mutation(sandbox_state, monkeypatch):
    """EN KRİTİK NOKTA: watchdog'un `SESSİZ BAR MUTASYONU` dedektörü bu üstüne-yazmayı ihlal
    saymamalı. Mekanizma UYDURULMADI — mevcut SANCTIONED yol kullanıldı: geçmiş değiştiğinde
    `_bump_wf_rev()` çalışır, dedektör `rev_bumped` görür ve küçülme/yeniden-yazım affedilir."""
    from meridian import watchdog
    from meridian.adapters import data
    _seed_cache("AAA", "2026-07-28")
    watchdog.determinism_report(persist=True)                     # TABAN: düzeltme ÖNCESİ
    rev0 = int(store.read_json("wf_cache_rev.json", {}).get("rev", 0))
    _t1_upgrade(sandbox_state, monkeypatch, iex_close=10.0, real_close=10.4)
    rep = watchdog.determinism_report()
    assert rep["ok"] is True, f"düzeltme SESSİZ MUTASYON sayıldı: {rep}"
    assert rep["rev_bumped"] is True
    assert int(store.read_json("wf_cache_rev.json", {}).get("rev", 0)) > rev0
    assert data is not None


def test_the_divergence_is_measured_not_assumed(sandbox_state, monkeypatch):
    """IEX ↔ konsolide farkı VARSAYILMAZ: her düzeltme turunda ortalama/maks sapma ve ölçülen
    hacim oranı deftere BİRİKİR; olay seans başına TEK satırdır (sembol başına değil)."""
    from meridian.adapters import data
    _t1_upgrade(sandbox_state, monkeypatch, iex_close=10.0, real_close=10.4, real_vol=120_000.0)
    rep = data.upgrade_divergence()
    assert rep["last_session"] == "2026-07-29" and rep["symbols"] == 1
    assert rep["max_dev_pct"] == pytest.approx(4.0, abs=1e-6)     # |10.4-10|/10 = %4
    assert rep["mean_dev_pct"] == pytest.approx(4.0, abs=1e-6)
    assert rep["max_dev_ticker"] == "AAA"
    assert rep["mean_volume_ratio"] == pytest.approx(24.0, abs=1e-6)   # 120.000 / 5.000
    ev = _events("bar_source_upgrade")
    assert len(ev) == 1 and ev[0]["session"] == "2026-07-29" and ev[0]["symbols"] == 1
    assert ev[0]["max_dev_pct"] == pytest.approx(4.0, abs=1e-6)


def test_an_unmeasured_divergence_is_none_not_zero(sandbox_state):
    """UYDURMA YASAĞI: 'sapma yok' ile 'hiç ölçülmedi' aynı sayı ile söylenemez."""
    from meridian.adapters import data
    rep = data.upgrade_divergence({})
    assert rep["mean_dev_pct"] is None and rep["max_dev_pct"] is None and rep["symbols"] is None


def test_the_t1_upgrade_recalibrates_the_volume_ratio(sandbox_state, monkeypatch):
    """(c) SÜREKLİ YENİDEN KALİBRASYON: gerçek konsolide/IEX oranı ancak düzeltme anında ölçülebilir."""
    from meridian.adapters import data
    _t1_upgrade(sandbox_state, monkeypatch, real_vol=120_000.0)
    row = data._se()["volume_ratio"]["AAA"]
    assert row["source"] == "t1_upgrade" and 20.0 in row["samples"] and 24.0 in row["samples"]
    assert data._volume_ratio("AAA") == 22.0                      # medyan(20, 24)


# ==================================================================================================
# 5) ONARIM GEÇİDİ
# ==================================================================================================
def test_the_repair_gate_closes_a_missing_session(sandbox_state, monkeypatch):
    """Canlı delik: 07-29 barı 259 sembolün 44'ünde. Geçit son K seansı tarar ve eksik seansı
    grouped anlık görüntüsünden kapatır — eksik seans başına EN ÇOK bir çağrı."""
    from meridian.adapters import data, massive
    for t in ("AAA", "BBB", "CCC"):
        _seed_cache(t, "2026-07-28", n=210)
    _seed_cache("DDD", "2026-07-29", n=210)                       # bu sembolde seans VAR
    snap_calls = []

    def _snap(date=None, **k):
        snap_calls.append(date)
        return {t: {"date": date, "open": 5.0, "high": 5.0, "low": 5.0, "close": 5.0,
                    "volume": 111.0} for t in ("AAA", "BBB", "CCC")}

    monkeypatch.setattr(massive, "snapshot", _snap)
    monkeypatch.setattr(massive, "last_session", lambda end=None, back=0:
                        str((pd.Timestamp("2026-07-29") - pd.tseries.offsets.BDay(back)).date()))
    rep = data.repair_coverage(["AAA", "BBB", "CCC", "DDD"], sessions=2)
    assert rep["coverage"]["2026-07-29"] == 0.25
    assert rep["repaired"]["2026-07-29"] == 3 and rep["grouped_calls"] == 1
    got = pd.read_csv(data._cache_path("AAA"), parse_dates=["date"])
    assert str(got["date"].max().date()) == "2026-07-29" and float(got["close"].iloc[-1]) == 5.0
    assert _events("bar_coverage_repaired")


def test_the_repair_gate_spends_nothing_when_coverage_is_fine(sandbox_state, monkeypatch):
    from meridian.adapters import data, massive
    for t in ("AAA", "BBB"):
        _seed_cache(t, "2026-07-29", n=210)
    monkeypatch.setattr(massive, "last_session", lambda end=None, back=0:
                        str((pd.Timestamp("2026-07-29") - pd.tseries.offsets.BDay(back)).date()))
    monkeypatch.setattr(massive, "snapshot",
                        lambda *a, **k: pytest.fail("kapsama tamken grouped çağrısı yakıldı"))
    rep = data.repair_coverage(["AAA", "BBB"], sessions=1)
    assert rep["grouped_calls"] == 0 and rep["coverage"]["2026-07-29"] == 1.0


def test_filling_an_interior_hole_bumps_the_wf_revision(sandbox_state, monkeypatch):
    """Determinizm yasası 'dosya büyümesi zararsızdır' derken SONA eklemeyi kastediyor. Ortadaki bir
    deliğin dolması GEÇMİŞ pencerelerin sonucunu değiştirir — önbelleklenmiş walk-forward'lar artık
    başka bir seriye aittir."""
    from meridian.adapters import data
    _seed_cache("AAA", "2026-07-29", n=210)
    df = pd.read_csv(data._cache_path("AAA"), parse_dates=["date"])
    hole = str(df["date"].iloc[-3].date())
    df.drop(df.index[-3]).to_csv(data._cache_path("AAA"), index=False)
    rev0 = int(store.read_json("wf_cache_rev.json", {}).get("rev", 0))
    # ONARIM BARININ FİYATI KOMŞULARIYLA AYNI ÖLÇEKTE OLMALI (2026-07-31, hayalet-round-2): eskiden
    # burada `close=1.0` vardı — 100$'lık bir seride %99 düşüp ertesi bar geri dönen tek satır, yani
    # karantina kuralının TAM imzası. Kural o gün hacim şartı yüzünden onu kaçırıyordu; şart
    # gevşeyince (bkz. v141) kapı bu barı haklı olarak DÜŞÜRDÜ ve delik dolmadı. Bu testin konusu
    # ONARIM BARININ FİYAT MAKULLÜĞÜ DEĞİL, wf-revizyonunun bumplanmasıdır; fikstür ölçeğe uydu.
    assert data._merge_repair_bar("AAA", {"date": hole, "open": 100.0, "high": 100.5, "low": 99.5,
                                          "close": 100.0, "volume": 9.0}) is True
    assert int(store.read_json("wf_cache_rev.json", {}).get("rev", 0)) > rev0


# ==================================================================================================
# 6) YENİDEN-DENEME MERDİVENİ
# ==================================================================================================
def _sched_env(monkeypatch, coverage: dict, index: pd.DataFrame, session="2026-07-29"):
    from meridian import dataset as ds, health, loop, reflect, scheduler, watchdog
    monkeypatch.setattr(scheduler, "_last_closed_session", lambda: session)
    monkeypatch.setattr(health, "halted", lambda: False)
    monkeypatch.setattr(ds, "load_live", lambda use_cache=True, session=None: (coverage, index))
    monkeypatch.setattr(watchdog, "beat", lambda *a, **k: None)
    monkeypatch.setattr(watchdog, "check_and_alarm", lambda *a, **k: None)
    monkeypatch.setattr(reflect, "clear_wf_caches", lambda *a, **k: None)
    monkeypatch.setattr(loop, "daily_cycle", lambda *a, **k: {"status": "noop", "date": "2026-07-28"})
    monkeypatch.setattr(scheduler, "_repair_once_per_session", lambda s: None)
    scheduler._state.update({"last_refetch_session": None, "refetch_attempts": 0,
                             "refetch_chase": None, "refetch_sparse_attempts": 0,
                             "refetch_next_at": None, "last_processed": None, "cycles": 0,
                             "last_repair_session": None})
    return scheduler


def test_the_dense_phase_stops_polling_but_never_declares_a_skip(sandbox_state, monkeypatch):
    """ESKİ YASA burada 'kalıcı atlama + alarm' diyordu ve 164 SAHTE alarm tam buradan doğdu.
    Sık faz bütçesi (8) ve pano halkasının anlamı KORUNUR; değişen tek şey, bütçenin bitmesinin
    artık 'pes etmek' anlamına GELMEMESİDİR."""
    stale = _bars(["2026-07-27", "2026-07-28"])
    sched = _sched_env(monkeypatch, {f"T{i}": stale.copy() for i in range(10)}, stale)
    for _ in range(12):
        sched.advance_once()
    assert _events("session_bar_never_published") == [], "son tarih dolmadan pes edildi"
    assert sched._state["refetch_attempts"] == sched.DENSE_ATTEMPTS
    assert sched._state["last_refetch_session"] == "2026-07-29"    # sık faz bayrağı yandı
    assert sched._state["refetch_chase"] == "2026-07-29"           # AMA kovalama sürüyor
    assert _events("session_bar_retry_sparse"), "seyrek faza geçiş kaydı yok"


def test_the_sparse_phase_catches_a_late_bar(sandbox_state, monkeypatch):
    """Bar sık fazdan SONRA geldiğinde merdiven onu yakalar: seans ATLANMAZ ve olay bunu söyler."""
    stale = _bars(["2026-07-27", "2026-07-28"])
    late = _bars(["2026-07-28", "2026-07-29"])
    feed = {"bars": {f"T{i}": stale.copy() for i in range(10)}, "index": stale}
    from meridian import dataset as ds
    sched = _sched_env(monkeypatch, feed["bars"], stale)
    monkeypatch.setattr(ds, "load_live",
                        lambda use_cache=True, session=None: (feed["bars"], feed["index"]))
    for _ in range(9):
        sched.advance_once()
    assert sched._state["last_refetch_session"] == "2026-07-29"
    # bar GELDİ ve seyrek denemenin zamanı doldu
    feed["bars"] = {f"T{i}": late.copy() for i in range(10)}
    feed["index"] = late
    sched._state["refetch_next_at"] = (dt.datetime.now(dt.timezone.utc)
                                       - dt.timedelta(minutes=1)).isoformat(timespec="seconds")
    sched.advance_once()
    assert sched._state["refetch_chase"] is None, "kovalama kapanmadı"
    assert sched._state["refetch_attempts"] == 0
    assert _events("session_bar_arrived_late"), "geç gelen bar sessizce kabul edildi"
    assert _events("session_bar_never_published") == []


def test_the_sparse_phase_does_not_hammer_the_provider(sandbox_state, monkeypatch):
    """Seyrek faz 30-60 dakikada BİR dener; her poll'de ağa çıkmak eski 250×3 süpürmesini geri getirirdi."""
    stale = _bars(["2026-07-27", "2026-07-28"])
    seen = []
    from meridian import dataset as ds
    sched = _sched_env(monkeypatch, {f"T{i}": stale.copy() for i in range(10)}, stale)
    monkeypatch.setattr(ds, "load_live", lambda use_cache=True, session=None:
                        (seen.append(use_cache), ({f"T{i}": stale.copy() for i in range(10)},
                                                  stale))[1])
    for _ in range(8):
        sched.advance_once()
    n_net = seen.count(False)
    for _ in range(5):
        sched.advance_once()
    assert seen.count(False) == n_net, "seyrek fazda her poll ağa çıkıyor"
    nxt = dt.datetime.fromisoformat(sched._state["refetch_next_at"])
    gap = (nxt - dt.datetime.now(dt.timezone.utc)).total_seconds()
    assert sched.SPARSE_BASE_S * 0.9 <= gap <= sched.SPARSE_MAX_S + 60


def test_terminal_skip_only_when_the_next_session_closes(sandbox_state, monkeypatch):
    """SON TARİH: alarm YALNIZ bir sonraki seans kapandığında ve YALNIZ bir kez. İmza korunur —
    watchdog parite dedektörü `session_bar_never_published` + `session` + `universe_coverage` okuyor."""
    stale = _bars(["2026-07-27", "2026-07-28"])
    sched = _sched_env(monkeypatch, {f"T{i}": stale.copy() for i in range(10)}, stale)
    for _ in range(9):
        sched.advance_once()
    assert _events("session_bar_never_published") == []
    monkeypatch.setattr(sched, "_last_closed_session", lambda: "2026-07-30")   # SONRAKİ seans kapandı
    sched.advance_once()
    sched.advance_once()
    ev = _events("session_bar_never_published")
    assert len(ev) == 1, f"terminal atlama {len(ev)} kez ilan edildi"
    assert ev[0]["session"] == "2026-07-29" and ev[0]["universe_coverage"] == 0.0
    assert ev[0]["required"] > 0 and "ATLAYACAK" in ev[0]["detail"]
    assert ev[0]["alarm"] == "DATA_QUALITY", "alarm seviyesi düştü — notify zinciri devreye girmez"


def test_the_repair_gate_runs_once_per_session(sandbox_state, monkeypatch):
    from meridian import scheduler
    stale = _bars(["2026-07-27", "2026-07-28"])
    sched = _sched_env(monkeypatch, {f"T{i}": stale.copy() for i in range(10)}, stale)
    ran = []
    monkeypatch.setattr(scheduler, "_repair_once_per_session",
                        lambda s: (ran.append(s), sched._state.update(last_repair_session=s))[0])
    for _ in range(6):
        sched.advance_once()
    assert ran == ["2026-07-29"], f"onarım geçidi {len(ran)} kez koştu (ağ maliyeti seans başına bir kez)"


# ==================================================================================================
# 7) YASA 6 — üretilen ölçümün DIŞ tüketicisi
# ==================================================================================================
def test_the_divergence_ledger_has_an_external_reader(sandbox_state, monkeypatch):
    """Defteri `adapters/data.py` yazar; `scheduler.status()` DIŞARIDAN okur → /api/hermes
    `scheduler` ve /api/scheduler üzerinden panoya çıkar. Okuyucusu olmayan bir ölçüm, üretilip
    tüketilmeyen kanıttır."""
    from meridian import scheduler
    from meridian.adapters import data
    monkeypatch.setattr(scheduler, "_last_closed_session", lambda: "2026-07-29")
    st = scheduler.status()
    assert st["bar_upgrade"]["mean_dev_pct"] is None                   # ölçüm yok → None
    _t1_upgrade(sandbox_state, monkeypatch, iex_close=10.0, real_close=10.4)
    st2 = scheduler.status()
    assert st2["bar_upgrade"]["last_session"] == "2026-07-29"
    assert st2["bar_upgrade"]["max_dev_pct"] == pytest.approx(4.0, abs=1e-6)
    assert store.read_json(data.SAME_EVENING_FILE, None) is not None   # defter GERÇEKTEN diskte

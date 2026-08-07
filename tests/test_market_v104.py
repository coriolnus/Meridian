"""test_market_v104.py — PANO "PİYASA" SEKMESİ: İZLENEN EVREN GÖRÜNÜR MÜ? (2026-07-27)

Bu turun sınıfı YASA 6'nın ters yüzü: pano bugüne kadar yalnız KARARA girmiş sembolleri
gösteriyordu (aday, plan, pozisyon). Motor 260 sembolün barını her gün tazeliyor ve o evrenin
panoda hiçbir izi yoktu — kanıt üretiliyor, tüketilmiyordu. Yeni yüzeyin taşıması gereken üç söz:

  1. ÖLÇÜLEMEYEN None KALIR. 5 barlık bir sembolün 20 günlük değişimi YOKTUR; 0.0 yazmak
     "değişmedi" diye okunur ve boşluk bir ölçüm gibi görünür.
  2. BAYAT BAR ADIYLA SAYILIR. Bir sembolün barı evrenin `as_of`undan geride kaldığında eski
     kapanışı taze gibi göstermek panonun okura yalan söylemesidir → `stale_n`.
  3. ÜRETİLEN HER ALANIN TÜKETİCİSİ VAR. Uçtan çıkıp panoda hiç çizilmeyen bir alan, üretilmemiş
     alandan ayırt edilemez — burada statik olarak ölçülür (aşağıdaki YASA 6 testi).

Önbellek testi de bir DAVRANIŞ testidir, mikro-optimizasyon değil: pano 15 saniyede bir tazelenir
ve her tazelemede 260 CSV'yi yeniden ayrıştırmak, sekmeyi açık bırakan operatöre sürekli disk
maliyeti çıkarırdı.
"""
from __future__ import annotations

import datetime as dt
import os
import pathlib
import re

import pytest
from fastapi.testclient import TestClient

from meridian import api, barclock, earnings, hotstate, marketview, store

APP_JS = pathlib.Path("meridian/web/app.js")
INDEX_HTML = pathlib.Path("meridian/web/index.html")
API_SRC = pathlib.Path("meridian/api.py")


def _bars(state, ticker: str, n: int, last_date: str, taban: float = 100.0) -> pathlib.Path:
    """Deterministik EOD CSV — üretimin kolon şemasıyla birebir (date,open,high,low,close,volume).
    Kapanış monoton artar: 52 haftalık zirve son bardır, yani `dist_52w_high_pct` == 0."""
    import pandas as pd
    dates = pd.bdate_range(end=last_date, periods=n).strftime("%Y-%m-%d").tolist()
    satirlar = ["date,open,high,low,close,volume"]
    for i, d in enumerate(dates):
        c = taban + i
        satirlar.append(f"{d},{c},{c + 1},{c - 1},{c},{1_000_000 + i}")
    p = state / "bars" / f"{ticker}.csv"
    p.write_text("\n".join(satirlar) + "\n")
    return p


# =================================================================================================
# 1) Yetki sınırı — uç hesap durumu kadar korunur
# =================================================================================================
def test_market_ucu_tokensiz_reddedilir_tokenla_gecer(sandbox_state, monkeypatch):
    """/api/market izlenen evreni (pozisyon/silahlanma izi dâhil) döndürür; yetkisiz açık kalırsa
    ajanın neyi izlediği ve nerede pozisyonda olduğu dışarıdan okunabilirdi."""
    monkeypatch.setattr(api, "DASH_TOKEN", "T0KEN")
    c = TestClient(api.app)

    assert c.get("/api/market").status_code in (401, 403)

    r = c.get("/api/market", headers={"x-meridian-token": "T0KEN"})
    assert r.status_code == 200
    assert set(r.json()) == {"as_of", "n", "stale_n", "retired_n", "source", "intraday",
                             "regime", "rows"}


# =================================================================================================
# 2) Pencereler + as_of + bayatlık
# =================================================================================================
def test_kisa_gecmis_olcum_UYDURMAZ_uzun_gecmis_olcer(sandbox_state):
    marketview.clear_cache()
    _bars(sandbox_state, "uzun", 300, "2026-07-24")
    _bars(sandbox_state, "kisa", 5, "2026-07-20")

    out = marketview.build()
    r = {x["ticker"]: x for x in out["rows"]}

    kisa = r["KISA"]
    assert kisa["chg1_pct"] is not None, "2 bar 1 günlük değişime yeter"
    assert kisa["chg20_pct"] is None, "5 barla 20 günlük değişim ÖLÇÜLEMEZ"
    assert kisa["dist_52w_high_pct"] is None, "5 barla 52 haftalık zirve ÖLÇÜLEMEZ"
    assert kisa["adv20_usd"] is None, "5 barla 20 günlük ADV ÖLÇÜLEMEZ"
    assert len(kisa["spark"]) == 5, "spark eldeki kadar olur, doldurulmaz"

    uzun = r["UZUN"]
    for alan in ("chg1_pct", "chg20_pct", "dist_52w_high_pct", "adv20_usd"):
        assert isinstance(uzun[alan], float), f"{alan} 300 barla ölçülmeliydi"
    assert uzun["dist_52w_high_pct"] == pytest.approx(0.0), "son bar zirveyse uzaklık sıfırdır"
    assert len(uzun["spark"]) == 60, "spark son 60 kapanışla sınırlı"

    assert out["as_of"] == "2026-07-24"
    assert out["n"] == 2
    assert out["stale_n"] == 1, "barı as_of'tan eski olan sembol ADIYLA sayılmalı"
    assert kisa["last_date"] == "2026-07-20"


def test_bos_evren_uydurma_as_of_uretmez(sandbox_state):
    marketview.clear_cache()
    out = marketview.build()
    assert out["as_of"] is None and out["n"] == 0 and out["stale_n"] == 0


# =================================================================================================
# 3) Süreç-içi önbellek — aynı mtime'da CSV yeniden okunmaz
# =================================================================================================
def test_onbellek_ayni_mtime_de_okumaz_degisince_okur(sandbox_state, monkeypatch):
    marketview.clear_cache()
    p = _bars(sandbox_state, "aaa", 40, "2026-07-24")
    sayac = {"n": 0}
    asil = marketview._read_csv

    def sayan(path):
        sayac["n"] += 1
        return asil(path)

    monkeypatch.setattr(marketview, "_read_csv", sayan)

    marketview.build()
    assert sayac["n"] == 1, "ilk çağrı dosyayı okur"
    marketview.build()
    assert sayac["n"] == 1, "mtime değişmediği hâlde CSV yeniden okundu"

    st = p.stat()
    os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))
    marketview.build()
    assert sayac["n"] == 2, "mtime değiştiğinde önbellek BAYAT kalmamalı"
    marketview.clear_cache()


# =================================================================================================
# 4) YASA 6 — üretilen her satır alanının panoda bir tüketicisi var
# =================================================================================================
def test_yasa6_satir_alanlarinin_hepsi_panoda_ciziliyor(sandbox_state):
    """Uçtan çıkıp hiçbir yerde çizilmeyen bir alan, üretilmemiş alandan ayırt edilemez. Statik
    kanıt: her alan adı app.js kaynağında geçiyor mu?"""
    marketview.clear_cache()
    _bars(sandbox_state, "aaa", 30, "2026-07-24")
    satir = marketview.build()["rows"][0]
    src = APP_JS.read_text()

    eksik = [k for k in satir if k not in src]
    assert not eksik, f"pano bu alanları hiç tüketmiyor: {eksik}"


def test_ust_duzey_alanlarin_da_tuketicisi_var(sandbox_state):
    marketview.clear_cache()
    out = marketview.build()
    src = APP_JS.read_text()
    for k in out:
        assert k in src, f"üst düzey alan '{k}' panoda hiç okunmuyor"
    for k in out["source"]:
        assert k in src, f"source.{k} panoda hiç okunmuyor"
    for k in out["intraday"]:
        assert k in src, f"intraday.{k} panoda hiç okunmuyor"


# =================================================================================================
# 5) Statik kablolama — sekme gerçekten var ve yetki isteniyor
# =================================================================================================
def test_statik_sekme_kablolari():
    """ÇİVİ TAŞINDI (S2R-1, 2026-08-02): Piyasa artık kendi başına bir SEKME değil, "Veri Sağlığı"
    alan sayfasının altında bir BÖLÜM. Ölçtüğümüz şey değişmedi — evren yüzeyi erişilebilir mi,
    çizen bir render'ı ve bir kabı var mı, ucu yetkili mi? Eklenen tek şart: eski `#market`
    yer imi KIRILMAMALI, yani alias'ı olmalı. Alias olmasaydı bu tur, kaydedilmiş bir bağlantıyı
    sessizce ölü bağa çevirirdi."""
    js = APP_JS.read_text()
    # ÇİVİ TAŞINDI (D2-b, 2026-08-07): "Veri Sağlığı" yüzeyi ③ Sağlık'la BİRLEŞTİ (TASK ③'ün
    # ölçülen yolu iki sayfaya yayılıyordu). Ölçülen şey değişmedi: evren yüzeyi erişilebilir mi?
    assert '["saglik", "Sağlık"]' in js, "VIEWS'te Sağlık yüzeyi yok"
    assert re.search(r"const ROUTE_ALIAS = \{.*?\bmarket: \"saglik\"", js, re.S), \
        "eski #market yer imi yeni evine yönlenmiyor"
    assert "RENDER.market" in js and "RAIL_ICON" in js and "veri:" in js
    assert 'id="page-market"' in INDEX_HTML.read_text(), "index.html'de bölüm kabı yok"

    blok = next(b for b in re.split(r"\n(?=@app\.)", API_SRC.read_text()) if '"/api/market"' in b)
    assert "_auth(request)" in blok, "/api/market yetkisiz açık"


def test_klavye_haritasi_VIEWS_ten_turer():
    """Yeni sekme eklenirken elle güncellenen ikinci bir liste OLMAMALI (2026-07-27 dersi:
    iki liste kayınca yardım paneli var olmayan kısayolları belgeliyordu).

    ÇİVİ TAŞINDI (S2R-1): açıklama satırı artık `market`in değil, evi olan `veri` sayfasının."""
    js = APP_JS.read_text()
    assert "const PAGE_MAP = VIEWS.map(" in js
    assert "saglik:" in js.split("const PAGE_DESC = {")[1].split("};")[0], "PAGE_DESC.saglik yok"


# =================================================================================================
# 6) finviz ekstrası — keşfedildi ≠ ölçülüyor
# =================================================================================================
def test_finviz_ekstrasi_satir_uretir_ama_bar_alanlari_None(sandbox_state):
    marketview.clear_cache()
    _bars(sandbox_state, "aaa", 30, "2026-07-24")
    store.write_json("finviz_universe.json",
                     {"tickers": ["ZZZ", "AAA"], "n": 2, "reason": "deneme gerekçesi"})

    out = marketview.build()
    r = {x["ticker"]: x for x in out["rows"]}

    assert r["ZZZ"]["source"] == "finviz"
    for alan in ("last_date", "close", "chg1_pct", "chg20_pct", "dist_52w_high_pct", "adv20_usd"):
        assert r["ZZZ"][alan] is None, f"barı olmayan sembolde {alan} uydurulmuş"
    assert r["ZZZ"]["spark"] == []
    assert r["AAA"]["source"] == "bars", "bars'ta olan sembol finviz ekstrası SAYILMAZ"
    assert out["source"] == {"bars": 1, "finviz_extra": 1, "finviz_reason": "deneme gerekçesi"}
    assert out["stale_n"] == 0, "barı olmayan satır 'bayat' değildir — ölçülmemiştir"


# =================================================================================================
# 7) Defter bağlamı satıra işleniyor (pozisyon · silahlı · plan · kazanç)
# =================================================================================================
def test_defter_baglami_satira_islenir(sandbox_state):
    marketview.clear_cache()
    earnings.clear_cache()
    _bars(sandbox_state, "aaa", 30, "2026-07-24")
    _bars(sandbox_state, "bbb", 30, "2026-07-24")
    store.write_json("portfolio.json", {"positions": {"AAA": {"qty": 10}},
                                        "armed": [{"ticker": "BBB", "id": "P-1"}]})
    store.write_jsonl("trade_plans.jsonl", [{"ticker": "AAA", "date": "2026-07-20"},
                                            {"ticker": "AAA", "date": "2026-07-23"},
                                            {"ticker": "BBB", "date": "2026-07-24"}])
    (sandbox_state / "earnings.csv").write_text(
        "ticker,date\nAAA,2026-06-01\nAAA,2026-07-30\nBBB,2026-01-05\n")

    r = {x["ticker"]: x for x in marketview.build()["rows"]}

    assert r["AAA"]["position"] is True and r["AAA"]["armed"] is False
    assert r["BBB"]["armed"] is True and r["BBB"]["position"] is False
    assert r["AAA"]["plans_n"] == 2 and r["AAA"]["last_plan_date"] == "2026-07-23"
    assert r["BBB"]["plans_n"] == 1 and r["BBB"]["last_plan_date"] == "2026-07-24"
    # as_of (2026-07-24) sonrası İLK rapor gelir; geçmiş rapor bu kolonda YAZILMAZ — kolonun
    # cevapladığı soru "önümde bilanço riski var mı?"dır, geçmişle geleceği tek hücrede karıştırmaz.
    assert r["AAA"]["earnings_date"] == "2026-07-30"
    assert r["BBB"]["earnings_date"] is None
    earnings.clear_cache()


# =================================================================================================
# 8) SEANS İÇİ ÖLÇÜM — yalnız silahlı, yalnız KAPANMIŞ bar, yalnız TAZE
# =================================================================================================
_SIMDI = dt.datetime(2026, 7, 27, 15, 40, 0, tzinfo=dt.timezone.utc)


def _bar(dakika_once: float, close: float = 250.0) -> dict:
    """Başlangıç damgası `dakika_once` dakika geriye olan dakikalık bar (t = dakikanın BAŞI)."""
    t = _SIMDI - dt.timedelta(minutes=dakika_once)
    return {"t": t.strftime("%Y-%m-%dT%H:%M:00Z"), "o": close, "h": close, "l": close,
            "c": close, "v": 1000.0}


@pytest.fixture
def sabit_saat(monkeypatch):
    monkeypatch.setattr(barclock, "now", lambda: _SIMDI)
    yield _SIMDI


def _armed_sandbox(state, *tickers):
    marketview.clear_cache()
    for t in tickers:
        _bars(state, t.lower(), 30, "2026-07-24")
    store.write_json("portfolio.json", {"positions": {}, "armed": [{"ticker": t} for t in tickers]})


def test_silahsiz_satirda_bar_VARKEN_BILE_seans_ici_None(sandbox_state, sabit_saat, monkeypatch):
    """DİSİPLİN: barfeed yalnız silahlı sembolleri izler. İzlenmeyen bir sembol için sıcak katmana
    gitmek hem 260 gereksiz Redis çağrısı hem de olmayan bir ölçümü varmış gibi sunmaktır. Bunu
    'değer None' diye ölçmek YETMEZ — çağrının HİÇ yapılmadığı kanıtlanır."""
    marketview.clear_cache()
    _bars(sandbox_state, "aaa", 30, "2026-07-24")          # silahlı DEĞİL
    cagrilar = []
    monkeypatch.setattr(hotstate, "read_bars",
                        lambda t, n=100: cagrilar.append(t) or [_bar(2.0, 999.0)])

    out = marketview.build()

    assert cagrilar == [], f"silahsız sembol için sıcak katmana gidildi: {cagrilar}"
    satir = out["rows"][0]
    assert satir["armed"] is False
    assert satir["intraday_close"] is None and satir["intraday_ts"] is None
    assert out["intraday"] == {"tracked_n": 0, "measured_n": 0,
                               "reason": "silahlı plan yok", "stale_tol_s": marketview.STALE_TOL_S}


def test_silahli_taze_kapanmis_bar_olculur(sandbox_state, sabit_saat, monkeypatch):
    _armed_sandbox(sandbox_state, "BBB")
    # 2 dakika önce BAŞLAYAN bar 1 dk önce KAPANDI → hem admissible hem taze (<120 sn).
    monkeypatch.setattr(hotstate, "read_bars", lambda t, n=100: [_bar(9.0, 100.0), _bar(2.0, 251.5)])

    out = marketview.build()
    r = {x["ticker"]: x for x in out["rows"]}["BBB"]

    assert r["armed"] is True
    assert r["intraday_close"] == 251.5, "en YENİ kapanmış barın kapanışı alınmalı"
    assert r["intraday_ts"] == _bar(2.0)["t"]
    assert out["intraday"]["tracked_n"] == 1 and out["intraday"]["measured_n"] == 1
    assert out["intraday"]["reason"] == "", "ölçüm varken gerekçe yazılmaz"


def test_kapanmamis_bar_KULLANILMAZ(sandbox_state, sabit_saat, monkeypatch):
    """Look-ahead kapısı panoya da uygulanır: içinde bulunulan dakikanın barı KAPANMAMIŞTIR ve
    onun 'kapanışı' diye bir şey yoktur. Elde yalnız o varsa ölçüm yoktur."""
    _armed_sandbox(sandbox_state, "CCC")
    # dakika_once=0 → t = ŞİMDİnin dakikası; o bar 60 sn SONRA kapanacak, henüz kapanmadı.
    monkeypatch.setattr(hotstate, "read_bars", lambda t, n=100: [_bar(0.0, 999.0)])

    out = marketview.build()
    r = {x["ticker"]: x for x in out["rows"]}["CCC"]

    assert r["intraday_close"] is None and r["intraday_ts"] is None
    assert out["intraday"]["reason"].startswith("bar akışı bayat")


def test_bayat_kapanmis_bar_TAZE_gibi_gosterilmez(sandbox_state, sabit_saat, monkeypatch):
    """Akış koptuğunda son kapanmış bar diskte durur. Onu 'seans içi' diye göstermek, operatöre
    eski bir fiyatı canlı gibi sunardı — sessiz ve tam da bu deponun kovaladığı yalan türü."""
    _armed_sandbox(sandbox_state, "DDD")
    monkeypatch.setattr(hotstate, "read_bars", lambda t, n=100: [_bar(30.0, 240.0)])   # 29 dk bayat

    out = marketview.build()
    r = {x["ticker"]: x for x in out["rows"]}["DDD"]

    assert r["intraday_close"] is None and r["intraday_ts"] is None
    assert out["intraday"]["tracked_n"] == 1 and out["intraday"]["measured_n"] == 0
    assert out["intraday"]["reason"] == (
        f"bar akışı bayat — en yeni kapanmış bar {marketview.STALE_TOL_S} sn'den eski")


def test_redis_yokken_patlamaz_ve_sebebi_AYRI_yazilir(sandbox_state, sabit_saat, monkeypatch):
    """read_bars None = sıcak katman hiç okunamıyor. Bu 'bayat akış'tan FARKLI bir arızadır
    (biri altyapı, diğeri bağlantı) ve aynı cümleye indirilirse operatör yanlış yerde arar."""
    _armed_sandbox(sandbox_state, "EEE")
    monkeypatch.setattr(hotstate, "read_bars", lambda t, n=100: None)

    out = marketview.build()
    r = {x["ticker"]: x for x in out["rows"]}["EEE"]

    assert r["intraday_close"] is None and r["intraday_ts"] is None
    assert out["intraday"]["reason"] == "bar akışı yok — sıcak katman (Redis) okunamıyor"


def test_tazelik_esigi_intraday_cycle_ile_AYNI_kaynaktan_gelir():
    """İki ayrı '120' iki ayrı yasa demektir: pano 'taze' derken motorun 'bayat' dediği bir barı
    gösterebilirdi. Eşik tek yerde tanımlanır, marketview onu import eder."""
    from meridian import intraday_cycle
    assert marketview.STALE_TOL_S is intraday_cycle.STALE_TOL_S
    assert "STALE_TOL_S = " not in pathlib.Path("meridian/marketview.py").read_text(), \
        "eşik marketview'de YENİDEN tanımlanmış — tek kaynak bozuldu"


def test_okunamayan_csv_sembolu_evrenden_DUSURMEZ(sandbox_state):
    """"İzleniyor ama barı okunamadı" bir sinyaldir; sembolü sessizce listeden silmek onu görünmez
    kılardı. Satır kalır, alanları dürüstçe None olur."""
    marketview.clear_cache()
    (sandbox_state / "bars" / "bozuk.csv").write_text("bu bir csv değil\n")

    out = marketview.build()

    assert out["n"] == 1
    assert out["rows"][0]["ticker"] == "BOZUK" and out["rows"][0]["close"] is None
    marketview.clear_cache()

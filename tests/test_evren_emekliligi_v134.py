"""test_evren_emekliligi_v134.py — SEMBOL EMEKLİLİĞİ: ÖLÜ İSİM GERİ GİREMEZ, BAYAT SAYILMAZ (2026-07-30).

Sekiz sembol (ANSS, DFS, FI, HES, IPG, K, PARA, WBA) delist oldu ve evrenden ELLE çıkarıldı.
Çıkarmak, işin YARISIYDI ve kalan yarısı sessizdi:

  1. `state/bars/*.csv` kalıntıları duruyor (replay determinizmi için BİLEREK silinmiyor) ve diski
     sayan her yüzey — pano "Piyasa" sekmesi — onları sonsuza dek "bayat" gösteriyordu. Son barları
     delist gününde donmuş; o gün ASLA gelmeyecek. Yani `stale_n` hiç düşmeyen bir tabana oturmuştu
     ve gerçek bayatlık (bar hattı BUGÜN durdu) o gürültünün içinde görünmez olurdu.
  2. Finviz keşfi evren DIŞINDAN sembol getirir. Üçüncü taraf bir ekranın bayat listesi ölü bir ismi
     yeniden önerirse hiçbir kapı onu durdurmuyordu: barı çekilmeye çalışılır, tarama evrenine
     girer ve motor artık işlem görmeyen bir sembol hakkında karar üretirdi.
  3. Evren bakımı raporu "hangi isimler öldü" diye soruyordu ama "ölü bir isim geri mi girdi" diye
     SORMUYORDU — oysa asıl sessiz hata sınıfı budur (elle düzenleme, kopyala-yapıştır).

Bu turun sözü: emeklilik hükmü TEK YERDE (`data.RETIRED_SYMBOLS`) yazılıdır, CANLI yüzeyleri
etkiler ve BAR ZİNCİRİNE DOKUNMAZ. Geçmiş geri alınmaz, bugün etiketlenir.
"""
from __future__ import annotations

import pathlib

import pandas as pd

from meridian import dataset, marketview, store
from meridian.adapters import constituents, data, finviz
from tests.conftest import make_bars


def _events(name: str) -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl")
            if e.get("event") == name or e.get("kind") == name]


def _csv(state, ticker: str, last_date: str, n: int = 30) -> pathlib.Path:
    """Üretimin EOD kolon şemasıyla birebir CSV (date,open,high,low,close,volume)."""
    dates = pd.bdate_range(end=last_date, periods=n).strftime("%Y-%m-%d").tolist()
    satirlar = ["date,open,high,low,close,volume"]
    for i, d in enumerate(dates):
        c = 100.0 + i
        satirlar.append(f"{d},{c},{c + 1},{c - 1},{c},{1_000_000 + i}")
    p = state / "bars" / f"{ticker}.csv"
    p.write_text("\n".join(satirlar) + "\n")
    return p


# =================================================================================================
# a) Defterin KENDİSİ — hüküm ile evren birbirini yalanlamaz
# =================================================================================================
def test_emekli_evrenle_kesismez():
    """Emeklilik defteri ile tarama evreni AYNI ANDA doğru olamaz: bir sembol ya taranır ya emeklidir.
    Kesişim boş değilse birinin hükmü diğerini sessizce geçersiz kılıyor demektir."""
    kesisim = set(data.RETIRED_SYMBOLS) & set(data.REPLAY_UNIVERSE)
    assert not kesisim, f"emekli sembol tarama evrenine geri girmiş: {sorted(kesisim)}"

    # Endeks emekli OLAMAZ: rejim sınıflaması ve seans seçimi tek başına ona dayanır — emekli
    # damgalanmış bir endeks, panonun bayatlık ölçümünü sessizce kör ederdi.
    assert not data.is_retired(data.INDEX_SYMBOL)

    assert len(data.RETIRED_SYMBOLS) == 8, "defter elle bakımlıdır; sayı değiştiyse gerekçesi de yazılmalı"
    assert set(data.RETIRED_SYMBOLS) == {"ANSS", "DFS", "FI", "HES", "IPG", "K", "PARA", "WBA"}
    for t, gerekce in data.RETIRED_SYMBOLS.items():
        assert gerekce.strip(), f"{t} gerekçesiz emekli edilmiş — hüküm gerekçesiz yazılmaz"

    # Tek kapı büyük/küçük harf ayırt etmez: her tüketici kendi normalizasyonunu yaparsa defter
    # aynı sembol için iki farklı cevap verir.
    assert data.is_retired("anss") and data.is_retired("ANSS")
    assert not data.is_retired("") and not data.is_retired(None) and not data.is_retired("AAPL")


def test_halef_ile_emekli_ayni_anda_dogru(sandbox_state):
    """FISV (2026-07-30, operatör kararı) evrene alındı — ama FI emekli KALIR. Bu bir çelişki değil:
    emeklilik hükmü ŞİRKETE değil SEMBOL KİMLİĞİNE verilir. FI'nin bar hattı 2025-11-11'de gerçekten
    bitti; sağlayıcı FISV'yi yeni kimlik olarak servis ediyor ve FI dönemini geriye BİRLEŞTİRMİYOR.
    Halefi evrene alıp emekliyi de silseydik, ölü bir sembolün bar hattı yeniden açılır ve pano onu
    sonsuza dek 'bayat' göstermeye geri dönerdi."""
    assert "FISV" in data.REPLAY_UNIVERSE and not data.is_retired("FISV")
    assert "FI" in data.RETIRED_SYMBOLS and data.is_retired("FI")
    assert "FI" not in data.REPLAY_UNIVERSE, "emekli kimlik halefiyle birlikte evrene geri giremez"
    # Defter, halefin evrende olduğunu YAZAR — gerekçe canlı kararı yalanlarsa hüküm okunmaz olur.
    assert "FISV" in data.RETIRED_SYMBOLS["FI"]


# =================================================================================================
# b) Kapsama paydası — emekliler YAPISAL olarak sayılamaz
# =================================================================================================
def test_kapsama_paydasi_emekli_saymaz(sandbox_state, monkeypatch):
    """`loop`un universe_coverage paydası (`_n_uni = len(per)`, per=bars) `dataset.load`un döndürdüğü
    SÖZLÜKTEN türer, elle yazılmış bir sayıdan değil. Yani payda ancak `load_many`ye SORULAN
    sembolleri sayabilir. Burada çivilenen şey tam olarak budur: istenen liste REPLAY_UNIVERSE'ün
    kendisidir ve içinde emekli sembol YOKTUR — payda emeklileri yapısal olarak sayamaz."""
    dataset._cache.clear()
    istenen: list = []
    index_df = make_bars(n=300)

    def sahte_load_many(tickers, start, end, use_cache=True, **k):
        istenen.extend(tickers)
        return {t: make_bars(n=300) for t in tickers[:2]}     # ağ YOK; içerik bu testin konusu değil

    monkeypatch.setattr(data, "load_bars", lambda t, s, e, **k: index_df.copy())
    monkeypatch.setattr(data, "load_many", sahte_load_many)

    dataset.load(use_cache=False)

    assert istenen == list(data.REPLAY_UNIVERSE), "replay yolu evreni olduğu gibi sormalı"
    emekli_istenen = [t for t in istenen if data.is_retired(t)]
    assert not emekli_istenen, f"emekli sembol bar hattına sorulmuş: {emekli_istenen}"
    dataset._cache.clear()


# =================================================================================================
# c) Pano — emekli satır DURUR ama bayatlık ölçümüne GİRMEZ
# =================================================================================================
def test_marketview_emekli_bayat_sayilmaz(sandbox_state):
    """Emekli sembolün CSV'si silinmez (replay determinizmi), bu yüzden satırı da silinmez. Ama
    bayatlığı ölçmek yerine ETİKETLENİR: delist gününden sonra bar yok, "geride kalması" bir arıza
    değil kesin sonuçtur."""
    marketview.clear_cache()
    _csv(sandbox_state, "anss", "2025-07-18")        # emekli — son barı delist gününde donmuş
    _csv(sandbox_state, "aapl", "2026-07-24")        # taze — evrenin as_of'u
    _csv(sandbox_state, "msft", "2026-07-23")        # GERÇEKTEN bayat: bir gün geride

    out = marketview.build()
    r = {x["ticker"]: x for x in out["rows"]}

    assert out["as_of"] == "2026-07-24"
    assert r["ANSS"]["retired"] is True
    assert r["AAPL"]["retired"] is False and r["MSFT"]["retired"] is False
    assert r["ANSS"]["last_date"] == "2025-07-18", "bar geçmişi GERÇEK — etiket onu silmez"
    assert out["stale_n"] == 1, "yalnız MSFT bayat; emekli ANSS sayıma girmemeli"
    assert out["retired_n"] == 1, "bars'ta CSV'si olan emekli sembol adıyla sayılmalı"
    marketview.clear_cache()


def test_marketview_emekli_yalniz_bars_ta_varsa_sayilir(sandbox_state):
    """`retired_n` DİSKİ sayar, defteri değil: defterde adı geçip CSV'si olmayan yedi sembol panoda
    hiçbir satır üretmiyor demektir — onları saymak, olmayan satırlar hakkında sayı üretmek olurdu."""
    marketview.clear_cache()
    _csv(sandbox_state, "aapl", "2026-07-24")
    out = marketview.build()
    assert out["retired_n"] == 0 and out["stale_n"] == 0
    marketview.clear_cache()


# =================================================================================================
# d) Finviz keşfi — emekli sembol evrene GERİ GİREMEZ, eleme SESSİZ olmaz
# =================================================================================================
def test_finviz_emekli_geri_giremez(sandbox_state, monkeypatch):
    """Keşif kaynağı üçüncü taraftır ve bayat olabilir. Elenen sembol kadar önemli olan şey, elemenin
    GÖRÜLEBİLİR olmasıdır: sessiz bir filtre, keşif kaynağının ölü isim servis ettiğini kimseye
    söylemez ve sorun kaynağında hiç düzelmez."""
    dataset._cache.clear()
    index_df = make_bars(n=300)
    istenen: list = []

    # TSK-116 düzeltme turu 1 (2026-09-03): `_load_live_inner` artık `load(..., universe=...)`
    # çağırıyor — sahte fonksiyon yeni imzayı kabul etmeli (tek satır, sahiplik: dataset.py'yi
    # değiştiren turun sorumluluğu, davranış İDDİASI değişmedi).
    monkeypatch.setattr(dataset, "load", lambda use_cache=True, universe=None: ({}, index_df.copy()))
    monkeypatch.setattr(finviz, "discover_universe", lambda **k: ["ANSS", "NVDA"])

    def sahte_load_many(tickers, start, end, use_cache=True, **k):
        istenen.extend(tickers)
        return {t: make_bars(n=300) for t in tickers}

    monkeypatch.setattr(data, "load_many", sahte_load_many)

    bars, _ = dataset.load_live()

    assert "ANSS" not in istenen, "delist olmuş sembol bar hattına sorulmuş"
    assert istenen == ["NVDA"], "yaşayan keşif sembolü elenmemeli"
    assert "ANSS" not in bars and "NVDA" in bars

    ev = _events("retired_symbol_rediscovered")
    assert ev, "emekli sembol SESSİZCE elendi — keşif kaynağının bayatlığı görünmez kaldı"
    assert "ANSS" in str(ev[-1].get("tickers")) and "NVDA" not in str(ev[-1].get("tickers"))
    dataset._cache.clear()


# =================================================================================================
# e) Bakım raporu — "ölü isim geri mi girdi?" sorusu artık SORULUYOR
# =================================================================================================
def test_sapma_raporu_emeklilik_bekcisi_tasir(sandbox_state, monkeypatch):
    """Rapor iki dalda da (üyelik kaynağı var/yok) aynı bekçiyi taşımalı: kaynak yokken de ölü isim
    evrene geri girebilir ve o hâlde 'unknown' cevabı soruyu CEVAPSIZ değil GÖRÜNMEZ kılardı."""
    monkeypatch.setattr(constituents, "current", lambda *a, **k: [])
    d = constituents.universe_drift()
    assert d["status"] == "unknown"
    assert d["retired_n"] == len(data.RETIRED_SYMBOLS) == 8
    assert d["retired_in_universe"] == [], "evrende emekli sembol var — biri ölü ismi geri koymuş"

    uyeler = [t for t in data.REPLAY_UNIVERSE] + [f"X{i}" for i in range(300)]
    monkeypatch.setattr(constituents, "current", lambda *a, **k: uyeler)
    d = constituents.universe_drift()
    assert d["status"] == "ok"
    assert d["retired_n"] == 8 and d["retired_in_universe"] == []


def test_sapma_raporu_geri_giren_olu_ismi_GORUNUR_kilar(sandbox_state, monkeypatch):
    """Bekçinin değeri ancak ihlalde ölçülür: evrene ölü bir isim SOKULDUĞUNDA rapor susarsa,
    bekçi hiç yokmuş gibidir."""
    monkeypatch.setattr(data, "REPLAY_UNIVERSE", [*data.REPLAY_UNIVERSE, "PARA"])
    monkeypatch.setattr(constituents, "current", lambda *a, **k: [])
    assert constituents.universe_drift()["retired_in_universe"] == ["PARA"]


# =================================================================================================
# f) Verisiz-sembol defteri — emekliye İKİNCİ kez "bakım adayı" denmez
# =================================================================================================
def test_no_data_raporu_emekliyi_bakim_adayi_saymaz(sandbox_state, monkeypatch):
    """Hükmü verilmiş bir sembolün veri vermemesi bir BULGU değil, beklenen sonuçtur. Onu her turda
    yeniden 'evren bakımı adayı' diye listelemek, kapanmış bir dosyayı sonsuza dek açık tutmaktır —
    ama defterden SİLMEK de olmaz: ölü bir sembolün hâlâ fetch edilmesi ayrı ve gerçek bir bulgudur."""
    monkeypatch.setattr(data, "_NO_DATA", {
        "PARA": {"verdict": "symbol_unknown", "streak": data.NO_DATA_CONFIRM_STREAK},
        "ZZZZ": {"verdict": "symbol_unknown", "streak": data.NO_DATA_CONFIRM_STREAK},
        "YYYY": {"verdict": "symbol_unknown", "streak": 1},
        "ANSS": {"verdict": "symbol_unknown", "streak": 2},
    })
    rep = data.no_data_report()
    assert rep["confirmed_no_data"] == ["ZZZZ"], "emekli sembol bakım adayı olarak İKİNCİ kez işaretlendi"
    assert rep["suspect"] == ["YYYY"]
    assert rep["retired"] == ["ANSS", "PARA"], "emekli kayıt defterden silinmemeli, ayrı durmalı"
    assert rep["tracked"] == 4, "izlenen kayıt sayısı DÜRÜST kalır — eleme sayımı değiştirmez"

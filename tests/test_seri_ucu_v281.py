"""test_seri_ucu_v281.py — PANODA GRAFİK ÇİZİLECEKSE ARKASINDA SERİ OLMALI (2026-08-24)

Operatör "bütün hisseler için canlı grafikler" istedi (KARAR-2026-08-24-B §5.2/Y1). Pano satır-içi
kıvılcım grafiği çizecek ama dayanacağı uç YOKTU: `/api/market` bar ÖZETİ döndürüyordu (son kapanış,
1g/20g değişim…), SERİ değil. Bu tur o seriyi ekler ve eklerken üç yalanı yapısal olarak yasaklar:

  1. BOŞ DİZİ BİR SERİ DEĞİLDİR. Barı olmayan sembole `[]` dönmek, kıvılcım grafiğinde DÜZ ÇİZGİ
     çizdirir — okuyucu "fiyat hiç kıpırdamamış" diye okur. Ölçüm yoksa `seri: null` ve YANINDA
     nedeni (`seri_yok_nedeni`) yazar (UYDURMA YASAĞI).
  2. DOLGU YOK. 40 seansı olmayan sembolde eksik uçlar interpole EDİLMEZ; `n` gerçek sayıdır.
  3. VARSAYILAN YÜK DEĞİŞMEZ. Seri `?seri=1` ile İSTENİR. Her `/api/market` çağrısına 260 sembol ×
     40 kapanış eklemek, seriyi hiç çizmeyen mevcut tüketicilere sessiz bir vergi olurdu.

Ayrıca tek sembolün DERİN serisi (`/api/bars/{ticker}`) aday çekmecesi için eklenir: tavanlı
(`n≤500`) ve tavan uygulandığında bunu SÖYLEYEN (`kirpildi`) bir uç. Bilinmeyen sembol 404 DEĞİL,
açıklamalı bir yanıt döner — pano onu "ölçülemedi" diye çizebilsin diye; 404 alan bir çekmece
"sunucu bozuk" ile "bu sembolün barı yok"u ayırt edemezdi.

Önbellek testi bir DAVRANIŞ testidir: seri hesabı `_bar_core`ın mtime anahtarlı önbelleğine
KOŞMAZSA, pano 15 saniyede bir tazelenirken 260 CSV her turda yeniden ayrıştırılırdı.

CANLI STATE'E YAZILMAZ: her test `sandbox_state` içinde koşar.
"""
from __future__ import annotations

import pathlib

import pytest
from fastapi.testclient import TestClient

from meridian import api, marketview, store

TOKEN = "T0KEN"


def _bars(state, ticker: str, n: int, last_date: str, taban: float = 100.0) -> pathlib.Path:
    """Deterministik EOD CSV — üretimin kolon şemasıyla birebir (date,open,high,low,close,volume).
    Kapanış her barda 1 artar, yani beklenen seri elle hesaplanabilir (uydurma değil, türetme)."""
    import pandas as pd
    dates = pd.bdate_range(end=last_date, periods=n).strftime("%Y-%m-%d").tolist()
    satirlar = ["date,open,high,low,close,volume"]
    for i, d in enumerate(dates):
        c = taban + i
        satirlar.append(f"{d},{c},{c + 1},{c - 1},{c},{1_000_000 + i}")
    p = state / "bars" / f"{ticker}.csv"
    p.write_text("\n".join(satirlar) + "\n")
    return p


def _beklenen(state, ticker: str) -> tuple[list[float], list[str]]:
    """CSV'nin KENDİSİNDEN okunan gerçek (kapanışlar, tarihler) — testin beklentisi üretim koduna
    değil diske dayanır."""
    import pandas as pd
    df = pd.read_csv(state / "bars" / f"{ticker}.csv")
    return [float(x) for x in df["close"]], [str(x)[:10] for x in df["date"]]


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api, "DASH_TOKEN", TOKEN)
    marketview.clear_cache()
    yield TestClient(api.app)
    marketview.clear_cache()


def _get(c: TestClient, yol: str):
    return c.get(yol, headers={"x-meridian-token": TOKEN})


# =================================================================================================
# 1) Varsayılan yük DEĞİŞMEZ — seri İSTENİR
# =================================================================================================
def test_seri_istenmeden_yukte_seri_ANAHTARI_YOK(sandbox_state, client):
    """Mevcut tüketiciler kırılmaz: parametre verilmeyen çağrı bugünkü yükün BİREBİR aynısıdır."""
    _bars(sandbox_state, "aaa", 60, "2026-07-24")

    r = _get(client, "/api/market")
    assert r.status_code == 200
    j = r.json()

    assert set(j) == {"as_of", "n", "stale_n", "retired_n", "source", "intraday", "regime", "rows"}
    satir = j["rows"][0]
    assert "seri" not in satir, "istenmemiş seri yüke sızdı — varsayılan yük büyüdü"
    assert "seri_yok_nedeni" not in satir


def test_seri_ucu_yetki_ister(sandbox_state, client):
    """Evrenin fiyat serisi de evrenin kendisi kadar korunur (bkz. /api/market yetki çivisi)."""
    assert client.get("/api/market?seri=1").status_code in (401, 403)
    assert client.get("/api/bars/AAA").status_code in (401, 403)


# =================================================================================================
# 2) `?seri=1` — kapanışlar CSV ile BİREBİR
# =================================================================================================
def test_seri_kapanislari_CSV_ile_birebir_eslesir(sandbox_state, client):
    _bars(sandbox_state, "aaa", 60, "2026-07-24")
    kapanislar, tarihler = _beklenen(sandbox_state, "aaa")

    j = _get(client, "/api/market?seri=1").json()
    s = j["rows"][0]["seri"]

    assert s["kapanis"] == kapanislar[-marketview._SERI_BARS:], "seri CSV'nin son kapanışları DEĞİL"
    assert s["n"] == marketview._SERI_BARS
    assert len(s["kapanis"]) == s["n"], "n ile dizi uzunluğu ayrışırsa n bir beyan değil süstür"
    assert s["son_tarih"] == tarihler[-1] == j["as_of"]
    assert s["ilk_tarih"] == tarihler[-marketview._SERI_BARS]
    assert j["rows"][0]["seri_yok_nedeni"] is None, "seri VARKEN neden yazılmaz"


def test_seri_bir_kiviliCim_icin_yeterince_uzun_ve_bilincli_sabit():
    """Sabit adlandırılmış olmalı: kaynakta çıplak bir `40` görürsek onu kimse gerekçeli
    değiştiremez."""
    assert marketview._SERI_BARS == 40
    src = pathlib.Path("meridian/marketview.py").read_text()
    assert "_SERI_BARS = 40" in src


# =================================================================================================
# 3) BOŞ DİZİ ASLA — barı olmayan sembol nedeniyle birlikte susar
# =================================================================================================
def test_barsiz_sembolde_seri_None_ve_neden_DOLU(sandbox_state, client):
    """finviz keşfi bars'ta olmayan bir sembol getirir. `[]` dönmek kıvılcımda DÜZ ÇİZGİ çizdirir —
    'fiyat kıpırdamadı' diye okunur ve bu bir yalandır."""
    _bars(sandbox_state, "aaa", 60, "2026-07-24")
    store.write_json("finviz_universe.json", {"tickers": ["ZZZ"], "n": 1, "reason": "deneme"})

    r = {x["ticker"]: x for x in _get(client, "/api/market?seri=1").json()["rows"]}

    assert r["ZZZ"]["source"] == "finviz"
    assert r["ZZZ"]["seri"] is None, "barı olmayan sembole seri UYDURULDU"
    assert r["ZZZ"]["seri"] != [], "boş dizi düz çizgi çizdirir — bu bir yalandır"
    assert len(r["ZZZ"]["seri_yok_nedeni"] or "") >= 10, "boşluğun nedeni yazılmamış"


def test_her_satirda_seri_ile_neden_BIRBIRINI_TAMAMLAR(sandbox_state, client):
    """DEĞİŞMEZ (satır satır, istisnasız): seri VARSA neden None, seri YOKSA neden DOLU. Nedensiz
    bir `null` panoya "çizemedim" ile "çizecek bir şey yok"u aynı boşlukla anlattırırdı."""
    _bars(sandbox_state, "aaa", 60, "2026-07-24")
    _bars(sandbox_state, "kisa", 3, "2026-07-24")
    (sandbox_state / "bars" / "bozuk.csv").write_text("bu bir csv değil\n")
    store.write_json("finviz_universe.json", {"tickers": ["ZZZ"], "n": 1, "reason": "deneme"})

    satirlar = _get(client, "/api/market?seri=1").json()["rows"]

    assert len(satirlar) == 4
    for s in satirlar:
        var = s["seri"] is not None
        assert var != (s["seri_yok_nedeni"] is not None), \
            f"{s['ticker']}: seri ve neden aynı anda dolu/boş — beyan tutarsız"
        if not var:
            assert s["seri_yok_nedeni"].strip(), f"{s['ticker']}: nedensiz null"


def test_okunamayan_csv_seriyi_SESSIZCE_yutmaz(sandbox_state, client):
    """YASA 4: okunamayan dosya işaretlenir ve nedeni gerekçeli yazılır — `null` sessizliği değil."""
    (sandbox_state / "bars" / "bozuk.csv").write_text("bu bir csv değil\n")

    r = {x["ticker"]: x for x in _get(client, "/api/market?seri=1").json()["rows"]}

    assert r["BOZUK"]["seri"] is None
    assert len(r["BOZUK"]["seri_yok_nedeni"] or "") >= 20, "sessiz-yutma gerekçesi ≥20 karakter olmalı"


# =================================================================================================
# 4) DOLGU YOK — kısa geçmiş kadarını verir, `n` gerçek sayıdır
# =================================================================================================
def test_kirk_bardan_az_gecmis_DOLDURULMAZ(sandbox_state, client):
    _bars(sandbox_state, "kisa", 7, "2026-07-24")
    kapanislar, tarihler = _beklenen(sandbox_state, "kisa")

    s = _get(client, "/api/market?seri=1").json()["rows"][0]["seri"]

    assert s["n"] == 7, "n gerçek bar sayısı olmalı"
    assert s["kapanis"] == kapanislar, "eldeki kadarı verilir; interpolasyon/dolgu YAPILMAZ"
    assert s["ilk_tarih"] == tarihler[0] and s["son_tarih"] == tarihler[-1]
    assert None not in s["kapanis"], "dolgu için None enjekte edilmiş"


# =================================================================================================
# 5) ÖNBELLEK — seri `_bar_core`ın mtime anahtarlı gözünden geçer
# =================================================================================================
def test_seri_hesabi_bar_core_onbellegini_kullanir(sandbox_state, monkeypatch):
    """Pano 15 sn'de bir tazelenir; seri ayrı bir okuma yolu açsaydı her turda 260 CSV yeniden
    ayrıştırılırdı."""
    marketview.clear_cache()
    _bars(sandbox_state, "aaa", 60, "2026-07-24")
    sayac = {"n": 0}
    asil = marketview._read_csv
    monkeypatch.setattr(marketview, "_read_csv", lambda p: (sayac.__setitem__("n", sayac["n"] + 1),
                                                            asil(p))[1])

    ilk = marketview.build(seri=True)
    assert sayac["n"] == 1, "ilk çağrı dosyayı okur"
    ikinci = marketview.build(seri=True)
    assert sayac["n"] == 1, "aynı mtime'da CSV YENİDEN okundu — seri önbelleği atlıyor"
    assert ilk["rows"][0]["seri"] == ikinci["rows"][0]["seri"]

    # Aynı önbellek gözü: seri istenmeyen çağrı da ek okuma yapmaz.
    marketview.build()
    assert sayac["n"] == 1
    marketview.clear_cache()


# =================================================================================================
# 6) /api/bars/{ticker} — derin seri, tavanlı ve tavanı BEYAN EDEN
# =================================================================================================
def test_derin_seri_varsayilan_120_bar_ve_OHLCV_tasir(sandbox_state, client):
    _bars(sandbox_state, "aaa", 600, "2026-07-24")
    kapanislar, tarihler = _beklenen(sandbox_state, "aaa")

    j = _get(client, "/api/bars/AAA").json()

    assert j["ticker"] == "AAA" and j["neden"] is None
    assert j["n"] == 120 and len(j["bar"]) == 120, "varsayılan derinlik 120 bar"
    assert j["kirpildi"] is False, "tavan uygulanmadıysa kırpma BEYAN EDİLMEZ"
    assert j["as_of"] == tarihler[-1]
    assert [b["c"] for b in j["bar"]] == kapanislar[-120:]
    assert set(j["bar"][0]) == {"t", "o", "h", "l", "c", "v"}
    b = j["bar"][-1]
    assert b["h"] == b["c"] + 1 and b["l"] == b["c"] - 1 and b["v"] is not None


def test_derin_seri_tavani_uygular_ve_KIRPILDIGINI_soyler(sandbox_state, client):
    """Tavansız bir uç, tek istekle 5600 barlık bir CSV'yi tele koyardı. Tavan sessiz olamaz:
    pano 900 istedi, 500 aldı — bunu bilmezse eksik grafiği tam sanar."""
    _bars(sandbox_state, "aaa", 600, "2026-07-24")

    j = _get(client, "/api/bars/AAA?n=900").json()

    assert j["n"] == marketview.BAR_UCU_TAVAN == 500
    assert len(j["bar"]) == 500
    assert j["kirpildi"] is True, "tavan uygulandı ama söylenmedi"
    assert j["istenen_n"] == 900


def test_derin_seri_dosyada_olandan_fazlasini_UYDURMAZ(sandbox_state, client):
    _bars(sandbox_state, "kisa", 12, "2026-07-24")

    j = _get(client, "/api/bars/KISA?n=400").json()

    assert j["n"] == 12 and len(j["bar"]) == 12, "olmayan bar üretilmiş"
    assert j["kirpildi"] is False, "tavan aşılmadı — kırpma beyanı yanlış yerde"


def test_bilinmeyen_sembol_404_DEGIL_aciklamali_yanit(sandbox_state, client):
    """404, pano için 'sunucu bozuk' ile 'bu sembolün barı yok'u aynı sessizliğe indirirdi."""
    r = _get(client, "/api/bars/YOKBOYLE")

    assert r.status_code == 200, "bilinmeyen sembol hata değil, ÖLÇÜLEMEZ bir sorudur"
    j = r.json()
    assert j["ticker"] == "YOKBOYLE" and j["bar"] is None and j["n"] == 0
    assert j["neden"] == "bar dosyası yok"


@pytest.mark.parametrize("kotu", ["%2e%2e", "AA%20B", "%2e%2e%2fgoal.yaml", "cok-uzun-bir-sembol"])
def test_derin_seri_gecersiz_ad_patlamaz_ve_dizin_gezmez(sandbox_state, client, kotu):
    """Yol parametresi diskte dosya adına çevriliyor: ad kapalı bir izin listesinden geçmezse
    uç bir dizin gezintisi yüzeyi olurdu. Düşmanca ad 500 DE vermez — nedenli boşluk döner."""
    (sandbox_state / "goal.yaml").write_text("sizinti: olmamali\n")

    r = _get(client, f"/api/bars/{kotu}")

    # Yönlendirici bazı biçimleri hiç eşleştirmez (404) — ikisi de kabul; sızıntı OLMAMALI.
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        j = r.json()
        assert j["bar"] is None and len(j["neden"]) >= 10
        assert "sizinti" not in r.text


def test_derin_seri_gecerli_nokta_sembolu_reddetmez(sandbox_state, client):
    """Kapı SIKI ama körü körüne değil: `BRK.B` gerçek bir sembol adıdır ve dosyası
    `brk-b.csv`dir — desen onu elemez."""
    _bars(sandbox_state, "brk-b", 30, "2026-07-24")

    j = _get(client, "/api/bars/BRK.B").json()

    assert j["ticker"] == "BRK.B" and j["n"] == 30 and j["neden"] is None


def test_derin_seri_gecersiz_n_sessizce_yeniden_yorumlanmaz(sandbox_state, client):
    _bars(sandbox_state, "aaa", 60, "2026-07-24")
    assert _get(client, "/api/bars/AAA?n=0").status_code == 400
    assert _get(client, "/api/bars/AAA?n=-5").status_code == 400

"""test_shortinterest_v117.py — FINRA KISA POZİSYON ADAPTÖRÜ (ROADMAP §5.4 Y4, 2026-07-29).

Tasarım sözleşmesi (meridian/adapters/shortinterest.py):
  1. BAYATLIK GÖRÜNÜR — yayın tarihi ve gecikme damgası dosyanın İÇİNDE. FINRA ayda iki kez,
     ~9 iş günü gecikmeli yayımlar; bu veri hiçbir zaman 'bugün' değildir ve okurun bunu kendi
     hesaplaması gerekirse er ya da geç hesaplamaz.
  2. SON YAYIN YEREL BULUNUR — uç `sortFields`i reddediyor (canlı doğrulandı), o yüzden pencere
     çekilip max(settlementDate) alınır. Eski yayın satırları özete SIZMAMALI.
  3. İKİ AYRI GÜN-KAPATMA — bizim ADV20'miz ile FINRA'nın kendi ADV'si AYNI ŞEY DEĞİL; ikisi de
     ayrı alanda yazılır ki ayrıştıkları yerde soru sorulabilsin.
  4. UYDURMA YASAĞI — bar önbelleği yoksa ADV None, float bilinmiyorsa SI%%float None. 0 YAZILMAZ.
  5. FMP KOTASINA SIFIR ETKİ — FINRA yolu anahtarsız/ücretsiz; FMP'ye tek dokunuş isteğe bağlı
     `--float-cek` yoludur ve varsayılan KAPALIDIR.

TESTLERDE CANLI ÇAĞRI YOKTUR: `httpx.post` her testte yamalanır.
"""
from __future__ import annotations

import datetime as dt

import httpx
import pytest

from meridian.adapters import shortinterest as si


def _satir(sym="AAPL", settle="2026-06-30", kisa=1_000_000, onceki=900_000,
           adv_finra=500_000, dtc=2.0):
    """FINRA consolidatedShortInterest satırı — alan adları CANLI yanıttan alındı (2026-07-29)."""
    return {"symbolCode": sym, "issueName": f"{sym} Inc.", "marketClassCode": "NNM",
            "settlementDate": settle, "currentShortPositionQuantity": kisa,
            "previousShortPositionQuantity": onceki, "averageDailyVolumeQuantity": adv_finra,
            "daysToCoverQuantity": dtc, "changePercent": 11.11, "changePreviousNumber": 100_000,
            "stockSplitFlag": None, "revisionFlag": None, "accountingYearMonthNumber": 20260630,
            "issuerServicesGroupExchangeCode": "R"}


def _kur_http(monkeypatch, cevap):
    """`httpx.post`u yamalar; GÖVDELERİ ve ÇAĞRI SAYISINI toplar."""
    kayit = {"n": 0, "govdeler": []}

    def _post(url, json=None, timeout=None, headers=None):
        kayit["n"] += 1
        kayit["govdeler"].append(json)
        if callable(cevap):
            return cevap(json)
        return httpx.Response(200, json=cevap, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", _post)
    return kayit


def _bar_yaz(sandbox_state, ticker: str, hacimler: list[float], son="2026-07-28"):
    """Bar önbelleğine gerçek biçimde CSV yazar (data._cache_path deseni)."""
    from meridian.adapters import data
    cp = data._cache_path(ticker)
    cp.parent.mkdir(parents=True, exist_ok=True)
    d0 = dt.date.fromisoformat(son) - dt.timedelta(days=len(hacimler) - 1)
    satirlar = ["date,open,high,low,close,volume"]
    for i, v in enumerate(hacimler):
        satirlar.append(f"{(d0 + dt.timedelta(days=i)).isoformat()},10,11,9,10.5,{v}")
    cp.write_text("\n".join(satirlar) + "\n")
    return cp


@pytest.fixture(autouse=True)
def _kucuk_evren(monkeypatch):
    monkeypatch.setattr(si, "_universe", lambda: ["AAPL", "MSFT", "NVDA"])


@pytest.fixture(autouse=True)
def _reset_health():
    si._HEALTH.update({"ok": None, "calls": 0, "fails": 0, "last_status": None,
                       "last_error": "", "at": None, "rows": 0})
    yield


# ================================================================== 1) İSTEK ŞEKLİ + MALİYET
def test_istek_govdesi_domain_ve_compare_filtre_tasir(sandbox_state, monkeypatch):
    """Sunucu-tarafı filtre olmadan tüm ABD evreni çekilir; `domainFilters` maliyeti evrene bağlar."""
    k = _kur_http(monkeypatch, [_satir()])
    si.fetch(gun_geri=60, parca=125)
    g = k["govdeler"][0]
    assert g["domainFilters"][0]["fieldName"] == "symbolCode"
    assert set(g["domainFilters"][0]["values"]) == {"AAPL", "MSFT", "NVDA"}
    cf = g["compareFilters"][0]
    assert cf["fieldName"] == "settlementDate" and cf["compareType"] == "GTE"
    esik = (dt.date.today() - dt.timedelta(days=60)).isoformat()
    assert cf["fieldValue"] == esik


def test_evren_dilimlenir_ve_cagri_sayisi_olculur(sandbox_state, monkeypatch):
    """Maliyet TAHMİN değil ÖLÇÜM: 3 sembol / 1'lik dilim = 3 istek."""
    k = _kur_http(monkeypatch, [])
    r = si.fetch(gun_geri=60, parca=1)
    assert k["n"] == 3 and r["cagri"] == 3 and r["dilim"] == 3


def test_finra_yolu_fmp_kotasina_dokunmaz(sandbox_state, monkeypatch):
    """FINRA ücretsiz/anahtarsızdır. Bu yol FMP'ye giderse günlük 250 kotası boşuna yanardı."""
    from meridian.adapters import fmp
    monkeypatch.setattr(fmp, "_get", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("shortinterest.fetch FMP'ye gitti — kota etkisi sözleşmesi kırıldı")))
    _kur_http(monkeypatch, [_satir()])
    si.fetch(gun_geri=60)


# ================================================================== 2) SON YAYIN + BAYATLIK
def test_yalniz_en_son_mutabakat_tarihi_ozete_girer(sandbox_state):
    """Uç sıralamayı reddediyor → pencere çekiliyor. Eski yayın sızarsa rakamlar haftalarca eskir."""
    satirlar = [_satir("AAPL", "2026-06-15", kisa=111), _satir("AAPL", "2026-06-30", kisa=222),
                _satir("MSFT", "2026-06-15", kisa=333)]
    d = si.ozet(satirlar, bugun=dt.date(2026, 7, 10), yaz=False)
    assert d["yayin"]["settlement_date"] == "2026-06-30"
    assert d["yayin"]["onceki_settlement_date"] == "2026-06-15"
    assert d["semboller"]["AAPL"]["kisa_pozisyon"] == 222
    assert "MSFT" not in d["semboller"], "eski yayının satırı özete sızdı"


def test_bayatlik_damgasi_dosyanin_icindedir(sandbox_state):
    d = si.ozet([_satir(settle="2026-06-30")], bugun=dt.date(2026, 7, 10), yaz=False)
    y = d["yayin"]
    assert y["gecikme_gun"] == 10
    assert y["gecikme_isgunu_tatilsiz"] == 8
    assert y["bayat_mi"] is False
    assert y["beklenen_yayin_gecikmesi_isgunu"] == si.YAYIN_GECIKME_ISGUNU


def test_esik_asilinca_bayat_bayragi_kalkar(sandbox_state):
    d = si.ozet([_satir(settle="2026-06-30")], bugun=dt.date(2026, 8, 1), yaz=False)
    assert d["yayin"]["gecikme_gun"] == 32 and d["yayin"]["bayat_mi"] is True


def test_hic_satir_yoksa_tarih_uydurulmaz(sandbox_state):
    d = si.ozet([], bugun=dt.date(2026, 7, 10), yaz=False)
    assert d["yayin"]["settlement_date"] is None and d["yayin"]["gecikme_gun"] is None
    assert d["semboller"] == {}


# ================================================================== 3) İKİ AYRI GÜN-KAPATMA
def test_gun_kapatma_bizim_adv20_ile_finranin_adv_si_ayri_yazilir(sandbox_state):
    _bar_yaz(sandbox_state, "AAPL", [100_000.0] * 25)     # ADV20 = 100_000
    d = si.ozet([_satir("AAPL", "2026-06-30", kisa=500_000, adv_finra=250_000, dtc=2.0)],
                bugun=dt.date(2026, 7, 10), yaz=False)
    e = d["semboller"]["AAPL"]
    assert e["gun_kapatma_meridian"] == 5.0        # 500k / 100k (bizim ADV20)
    assert e["gun_kapatma_finra"] == 2.0           # sağlayıcının kendi ölçümü — DEĞİŞTİRİLMEZ
    assert e["adv_finra"] == 250_000
    assert e["adv20_kaynak"] == "bar_onbellek_20"


def test_bar_onbellegi_yoksa_adv_none_kalir_sifir_degil(sandbox_state):
    """0 yazılsaydı gün-kapatma sonsuza giderdi ya da 0 görünürdü — ikisi de ölçülmemiş bir sayı."""
    d = si.ozet([_satir("AAPL", "2026-06-30")], bugun=dt.date(2026, 7, 10), yaz=False)
    e = d["semboller"]["AAPL"]
    assert e["adv20_bar_onbellek"] is None and e["gun_kapatma_meridian"] is None
    assert e["adv20_kaynak"] == "bar_onbellegi_yok"
    assert d["kapsam"]["adv20_olcelemeyen_n"] == 1


def test_kismi_pencere_tam_pencere_gibi_sunulmaz(sandbox_state):
    _bar_yaz(sandbox_state, "AAPL", [100_000.0] * 5)
    d = si.ozet([_satir("AAPL", "2026-06-30")], bugun=dt.date(2026, 7, 10), yaz=False)
    assert d["semboller"]["AAPL"]["adv20_kaynak"] == "kismi_5_seans"


def test_adv20_bar_onbellegine_yazmaz(sandbox_state):
    """OKUMA-ONLY sözleşmesi: bar defterini kirletirse canlı worker'ın verisini bozardı."""
    cp = _bar_yaz(sandbox_state, "AAPL", [100_000.0] * 25)
    once = cp.stat().st_mtime_ns, cp.read_text()
    si.adv20("AAPL")
    assert (cp.stat().st_mtime_ns, cp.read_text()) == once


# ================================================================== 4) SI % FLOAT
def test_float_bilinmiyorsa_si_yuzde_float_none(sandbox_state):
    d = si.ozet([_satir("AAPL", "2026-06-30", kisa=1_000_000)], bugun=dt.date(2026, 7, 10), yaz=False)
    e = d["semboller"]["AAPL"]
    assert e["float"] is None and e["si_yuzde_float"] is None and e["float_kaynak"] is None
    assert d["kapsam"]["float_bilinen_n"] == 0


def test_float_onbellekteyse_si_yuzde_float_hesaplanir(sandbox_state):
    from meridian import store
    store.write_json(si.FLOAT_FILE, {"surum": 1, "guncellendi": None, "semboller": {
        "AAPL": {"float": 10_000_000.0, "sharesOutstanding": 12_000_000.0,
                 "cekildi": None, "kaynak": "fmp_profile"}}})
    d = si.ozet([_satir("AAPL", "2026-06-30", kisa=1_000_000)], bugun=dt.date(2026, 7, 10), yaz=False)
    e = d["semboller"]["AAPL"]
    assert e["si_yuzde_float"] == 10.0 and e["float_kaynak"] == "fmp_profile"


def test_float_cek_kota_blokluysa_istek_atmaz(sandbox_state, monkeypatch):
    from meridian.adapters import fmp
    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(fmp, "quota_blocked", lambda: True)
    monkeypatch.setattr(fmp, "profile", lambda s: (_ for _ in ()).throw(
        AssertionError("kota blokluyken FMP profile çağrıldı")))
    r = si.float_cek(["AAPL", "MSFT"], tavan=5)
    assert r["cagri"] == 0 and "kota" in (r["hata"] or "")


def test_float_cek_tavani_asmaz_ve_onbellegi_tekrar_cekmez(sandbox_state, monkeypatch):
    """Sembol başına 1 FMP isteği: tavansız 250 sembol günlük kotanın TAMAMIDIR."""
    from meridian.adapters import fmp
    sayac = {"n": 0}

    def _profile(s):
        sayac["n"] += 1
        return {"symbol": s, "floatShares": 1_000_000, "sharesOutstanding": 2_000_000}
    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(fmp, "quota_blocked", lambda: False)
    monkeypatch.setattr(fmp, "profile", _profile)
    r1 = si.float_cek(["AAPL", "MSFT", "NVDA"], tavan=2)
    assert sayac["n"] == 2 and r1["yeni"] == 2
    r2 = si.float_cek(["AAPL", "MSFT", "NVDA"], tavan=2)
    assert r2["atlanan"] == 2 and sayac["n"] == 3      # yalnız NVDA yeni çekildi


def test_float_alani_gelmezse_sahte_kayit_yazilmaz(sandbox_state, monkeypatch):
    from meridian.adapters import fmp
    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(fmp, "quota_blocked", lambda: False)
    monkeypatch.setattr(fmp, "profile", lambda s: {"symbol": s})     # float/shares YOK
    r = si.float_cek(["AAPL"], tavan=2)
    assert r["yeni"] == 0 and (si.float_onbellek().get("semboller") or {}) == {}


# ================================================================== 5) DÜRÜST BOZUNMA (YASA 4)
def test_http_hatasi_sessiz_bos_donmez(sandbox_state, monkeypatch):
    def _post(url, json=None, timeout=None, headers=None):
        return httpx.Response(503, text="down", request=httpx.Request("POST", url))
    monkeypatch.setattr(httpx, "post", _post)
    r = si.fetch(gun_geri=60)
    assert r["hata"] and "HTTPStatusError" in r["hata"]
    assert si.health()["fails"] == 1 and si.health()["last_status"] == 503


def test_hata_ozet_dosyasina_da_yazilir(sandbox_state, monkeypatch):
    from meridian import store
    _kur_http(monkeypatch, [])
    si.ozet([], cagri=0, hata="ConnectTimeout", bugun=dt.date(2026, 7, 10))
    assert store.read_json(si.SIGNAL_FILE)["hata"] == "ConnectTimeout"


def test_ozet_ag_cagrisi_yapmaz(sandbox_state, monkeypatch):
    def _patla(*a, **k):
        raise AssertionError("ozet() ağa gitti — saf hesap sözleşmesi kırıldı")
    monkeypatch.setattr(httpx, "post", _patla)
    monkeypatch.setattr(httpx, "get", _patla)
    si.ozet([_satir()], bugun=dt.date(2026, 7, 10), yaz=False)


def test_eksik_semboller_adiyla_raporlanir(sandbox_state):
    """'Kapsam daraldı' sessiz olmaz: hangi sembolün verisi gelmediği görünür."""
    d = si.ozet([_satir("AAPL", "2026-06-30")], bugun=dt.date(2026, 7, 10), yaz=False)
    assert d["kapsam"]["eslesen_n"] == 1 and d["kapsam"]["eksik_n"] == 2
    assert set(d["kapsam"]["eksik_ornek"]) == {"MSFT", "NVDA"}


# ================================================================== 6) CLI = YASA 6 TÜKETİCİSİ
def test_cli_argumansiz_yardim_basar_ve_2_doner():
    assert si.main([]) == 2


def test_cli_fetch_dosyayi_yazar(sandbox_state, monkeypatch, capsys):
    from meridian import store
    _kur_http(monkeypatch, [_satir("AAPL", "2026-06-30")])
    assert si.main(["--fetch", "--parca", "10"]) == 0
    d = store.read_json(si.SIGNAL_FILE)
    assert d["yayin"]["settlement_date"] == "2026-06-30"
    assert d["kaynak"]["anahtar_gerekli_mi"] is False
    assert "yayin" in capsys.readouterr().out


def test_cli_fetch_hatada_1_doner(sandbox_state, monkeypatch, capsys):
    def _post(url, json=None, timeout=None, headers=None):
        return httpx.Response(503, text="down", request=httpx.Request("POST", url))
    monkeypatch.setattr(httpx, "post", _post)
    assert si.main(["--fetch"]) == 1


def test_cli_ozet_fetch_yoksa_ag_a_gitmez(sandbox_state, monkeypatch, capsys):
    def _patla(*a, **k):
        raise AssertionError("--ozet ağa gitti")
    monkeypatch.setattr(httpx, "post", _patla)
    assert si.main(["--ozet"]) == 1        # dosya yok → hata, ama İSTEK ATILMADI
    assert "önce --fetch" in capsys.readouterr().out


# ================================================================== 7) YAZAR TEKLİĞİ
def test_bu_iki_dosyanin_tek_yazari_bu_adaptordur():
    """Yazar tekliği: canlı worker koşarken bu CLI'ı çalıştırmak ancak bu koşul tutarsa güvenlidir.
    Ölçüm GERÇEK yazım çağrısına bakar, "adı metinde geçiyor"a değil — gerekçe için bkz.
    tests/test_insider_v117.py `yazar_dosyalari`."""
    from tests.test_insider_v117 import yazar_dosyalari
    for dosya in (si.SIGNAL_FILE, si.FLOAT_FILE):
        yazanlar = yazar_dosyalari(dosya)
        assert yazanlar == {"shortinterest.py"}, (
            f"{dosya} yazarları beklenenden farklı: {sorted(yazanlar)} — atomik yazım "
            f"kayıp-güncellemeyi ÖNLEMEZ, yalnız yarım dosyayı önler")

"""v118 — Massive (massive.com) EOD adaptörü + bar zinciri kablolaması.

AĞ YOK: httpx her testte mock'lanır ve mock'lanmayan her çağrı ÇÖKER (`_izole` ağ bekçisi).
DİKKAT — bu artık kritik: operatör 2026-07-29'da CANLI `state/secrets.json`a MASSIVE_API_KEY girdi.
Yani "anahtar yok, o yüzden ağa çıkamayız" GÜVENCESİ ARTIK YOK; testleri sağlayıcıdan uzak tutan iki
şey `sandbox_state` (sırları tmp dizine yönlendirir) ve ağ bekçisidir. Biri düşerse suite gerçek
istek atar, 5/dk kotasını yer ve canlı defterleri ezer (test_audit_fixes'te tam bunu yaşadık).

Çivilenen şeyler:
  * alan eşlemesi (T/o/h/l/c/v/vw/t/n → date,open,high,low,close,volume; vw ve n ATILIR)
  * anahtarsız DÜRÜST devre dışılık: None (boş liste DEĞİL) + zincir aynen sürer
  * uç yolları + Bearer başlığı (anahtar sorgu parametresinde GİTMEZ)
  * 429/5xx üstel geri çekilme ve 5/dk token-bucket
  * yazım kapısı ÖLÇÜME bağlı: ölçüm yoksa/uyumsuzsa/bayatsa YALNIZ-ALARM
  * çapraz-kaynak uyuşmazlık ALARMI (karantina YOK)
  * artımlı kaynağın geçmişi bozamayacağı (sıfırlama, sahiplik, dikiş defteri)
"""
import datetime as dt
import json

import pandas as pd
import pytest

from meridian import secrets
from meridian.adapters import data, massive


class _Resp:
    def __init__(self, payload, status=200):
        self._p, self.status_code = payload, status
        self.text = json.dumps(payload) if isinstance(payload, (dict, list)) else str(payload)

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx
            raise httpx.HTTPStatusError("err", request=None, response=self)

    def json(self):
        return self._p


# grouped results[] satırının GERÇEK biçimi (massive.com/docs endpoint sayfasından).
# `t` = seans KAPANIŞININ unix ms'i. CANLI ÖLÇÜLDÜ (2026-07-29): 2026-07-28 barı için
# t=1785268800000 = 20:00Z = 16:00 ET. İlk yazımda "seans başlangıcı 04:00Z" varsayılmıştı — YANLIŞTI;
# sabit artık gerçek sözleşmeden türetiliyor, yoksa test yanlış varsayımı doğrulardı.
def _ms(gun: str) -> int:
    return int(dt.datetime.fromisoformat(f"{gun}T20:00:00+00:00").timestamp() * 1000)


T_2807, T_2907 = _ms("2026-07-28"), _ms("2026-07-29")
ROW_AAPL = {"T": "AAPL", "o": 340.03, "h": 342.89, "l": 335.60, "c": 340.24,
            "v": 39235541, "vw": 339.88, "t": T_2807, "n": 512345}
ROW_MSFT = {"T": "MSFT", "o": 500.0, "h": 510.0, "l": 499.0, "c": 505.5,
            "v": 12345678, "vw": 504.2, "t": T_2807, "n": 220011}


@pytest.fixture(autouse=True)
def _izole(sandbox_state, monkeypatch):
    """Her test kum havuzunda ve TEMİZ modül-globalleriyle koşar. Bu adaptörün durumu (anlık görüntü
    memosu, token-bucket, sağlık kaydı) modül-globalidir; sıfırlanmazsa testler SIRA BAĞIMLI olur —
    bu depoda daha önce tam olarak bu sınıf hata yaşandı (conftest _clear_module_caches yorumları)."""
    massive.reset_cache()
    massive._CALLS.clear()
    massive._HEALTH.update({"ok": None, "calls": 0, "fails": 0, "last_status": None,
                            "last_error": "", "at": None, "rate_waits": 0, "retries": 0})
    monkeypatch.setattr(massive, "_NO_KEY_LOGGED", False)
    monkeypatch.setattr(data, "_MASSIVE_MODE_LOGGED", False)
    monkeypatch.setattr(data, "_XCHECK", {})
    monkeypatch.setattr(data, "_XCHECK_DIRTY", 0)
    monkeypatch.setattr(data, "_SEAMS", {})
    # SAAT + UYKU SAHTE VE BAĞLI (2026-07-29): `_sleep`i sadece no-op yapmak YETMİYOR — `_throttle`
    # kovayı `_now()` ile boşaltır, yani uyku zamanı ilerletmezse döngü GERÇEK saati bekleyerek
    # meşgul-döner ve test 60 saniye asılır (bu dosyada tam bunu yaşadık: iki test 120 sn sürdü).
    # Uykuyu sahte saati İLERLETEN bir fonksiyona bağlamak hem anında hem deterministik yapar.
    saat = {"t": 0.0}
    monkeypatch.setattr(massive, "_now", lambda: saat["t"])
    monkeypatch.setattr(massive, "_sleep", lambda s: saat.__setitem__("t", saat["t"] + float(s)))
    # AĞ BEKÇİSİ: mock'lamayı unutan bir test SESSİZCE sağlayıcıya gitmesin. Varsayılan httpx
    # patlayıcıdır; HTTP isteyen testler `_mock_http` ile üzerine yazar.
    def _agsiz(*a, **k):
        raise AssertionError("test AĞA çıktı — httpx mock'lanmamış")
    monkeypatch.setattr(massive.httpx, "get", _agsiz)
    # NOT: ağ bekçisi sayesinde custom-bars kolu mock'lanmamış testlerde KENDİLİĞİNDEN boş döner
    # (istek patlar → MassiveError → None → boş çerçeve), yani zincire girse de sonucu değiştirmez.
    # Onu ölçen testler `data._fetch_massive_hist`i ya da http'yi açıkça yamalar.
    data._LAST_SOURCE.clear()
    secrets.clear_cache()
    yield
    massive.reset_cache()
    massive._CALLS.clear()
    data._LAST_SOURCE.clear()
    secrets.clear_cache()


def _anahtar(monkeypatch, val="massive_test_key_1234"):
    monkeypatch.setenv(massive.KEY_NAME, val)
    secrets.clear_cache()


def _mock_http(monkeypatch, payload, cap=None, status=200):
    def fake_get(url, params=None, headers=None, timeout=None):
        if cap is not None:
            cap["url"], cap["params"], cap["headers"] = url, params, headers
            cap["n"] = cap.get("n", 0) + 1
        return _Resp(payload, status)
    monkeypatch.setattr(massive.httpx, "get", fake_get)


# ------------------------------------------------------------------ alan eşlemesi
def test_alan_eslemesi_vw_ve_n_atilir():
    """T/o/h/l/c/v/t → şemamız; vw (VWAP) ve n (işlem sayısı) CSV şemasında YOK, atılır.
    Bu çivinin sebebi: fazladan bir sütun sessizce eklenirse `_write_bars` onu diske yazar ve
    `pd.read_csv(...)[COLS]` okumayan her tüketici şemayı farklı görür."""
    bar = massive.to_bar(ROW_AAPL, date="2026-07-28")
    assert set(bar) == {"date", "open", "high", "low", "close", "volume"}
    assert "vwap" not in bar and "n" not in bar and "T" not in bar
    assert (bar["open"], bar["high"], bar["low"], bar["close"]) == (340.03, 342.89, 335.60, 340.24)
    assert bar["volume"] == 39235541.0
    assert str(pd.Timestamp(bar["date"]).date()) == "2026-07-28"


def test_to_frame_cikti_semasi_bars_csv_ile_ayni():
    df = massive.to_frame([ROW_AAPL, ROW_MSFT], date="2026-07-28")
    assert list(df.columns) == data.COLS         # data.COLS = diskteki CSV başlığı
    assert len(df) == 2


def test_fetch_massive_hist_alanlari_semaya_cevirir(monkeypatch):
    """custom-bars kolunun UÇTAN UCA eşlemesi: ham results[] → COLS şemasında çerçeve."""
    _anahtar(monkeypatch)
    _mock_http(monkeypatch, {"results": [ROW_AAPL, dict(ROW_MSFT, t=1785384000000)]})
    df = data._fetch_massive_hist("AAPL", "2026-07-01", "2026-07-29")
    assert list(df.columns) == data.COLS and len(df) == 2
    assert df["close"].tolist() == [340.24, 505.5]


def test_eksik_alan_none_kapanissiz_satir_dusurulur():
    kismi = dict(ROW_AAPL); kismi.pop("v")
    bar = massive.to_bar(kismi, date="2026-07-28")
    assert bar["volume"] is None                 # eksik alan None — uydurulmaz
    assert bar["close"] == 340.24
    kapanissiz = dict(ROW_AAPL); kapanissiz["c"] = None
    assert massive.to_bar(kapanissiz, date="2026-07-28") is None   # kapanışsız bar bar değildir


def test_zaman_damgasi_et_seansina_cevrilir():
    """t = seans KAPANIŞI (16:00 ET). Yaz (20:00Z) ve kış (21:00Z) damgaları doğru SEANS gününü
    vermeli. GERÇEK canlı değer de çivilenir: sağlayıcı sözleşmeyi değiştirirse test söyler."""
    assert T_2807 == 1785268800000                             # canlı yanıttan doğrulanan değer
    assert str(massive.bar_date(T_2807).date()) == "2026-07-28"
    kis = int(dt.datetime(2026, 1, 5, 21, 0, tzinfo=dt.timezone.utc).timestamp() * 1000)
    assert str(massive.bar_date(kis).date()) == "2026-01-05"    # kış: 21:00Z = 16:00 ET
    # 20:00 ET'ye (= ertesi gün 00:00Z) taşınsa ham UTC tarihi KAYARDI; açık çeviri kaymaz.
    gece = int(dt.datetime(2026, 7, 29, 0, 0, tzinfo=dt.timezone.utc).timestamp() * 1000)
    assert str(massive.bar_date(gece).date()) == "2026-07-28"


# ------------------------------------------------------------------ anahtarsız dürüstlük
def test_anahtarsiz_uclar_none_doner_bos_liste_degil(monkeypatch):
    """None = 'soramadık'; [] = 'sorduk, sıfır satır'. İkisini birbirine karıştırmak, bu depoda
    HATA≠BOŞ olarak adlandırılan ve canlıda 18 sembolü yanlışlıkla 'ölü' gösteren sınıftır."""
    monkeypatch.delenv(massive.KEY_NAME, raising=False)
    secrets.clear_cache()
    def patlat(*a, **k):
        raise AssertionError("anahtar yokken AĞA ÇIKILDI")
    monkeypatch.setattr(massive.httpx, "get", patlat)
    assert massive.grouped_daily("2026-07-28") is None
    assert massive.custom_bars("AAPL", "2026-06-01", "2026-07-28") is None
    assert massive.all_tickers() is None
    assert massive.available() is False
    assert massive.mode() == "kapali_anahtar_yok"


def test_anahtarsizlik_bir_kez_kaydedilir_yasa4(monkeypatch):
    """YASA 4: yokluk KAYDEDİLİR, sessiz değil — ama 250 sembollük turda 250 kez değil."""
    monkeypatch.delenv(massive.KEY_NAME, raising=False)
    secrets.clear_cache()
    kayit = []
    import meridian.obs as obs
    monkeypatch.setattr(obs, "log", lambda e, **f: kayit.append(e))
    for _ in range(5):
        massive.grouped_daily("2026-07-28")
    assert kayit.count("massive_disabled_no_key") == 1


def test_anahtarsizken_zincir_degismez_fmp_aynen_calisir(monkeypatch):
    """Anahtar yokken bu iş HİÇBİR davranışı değiştirmemeli: zincir FMP→Cboe→Nasdaq olarak kalır."""
    monkeypatch.delenv(massive.KEY_NAME, raising=False)
    secrets.clear_cache()
    cagrilar = []
    monkeypatch.setattr(data, "_fetch_fmp", lambda t, s, e, to: cagrilar.append("fmp") or _bars(3))
    monkeypatch.setattr(data, "_fetch_cboe", lambda t, to: pd.DataFrame())
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda t, s, e, to: pd.DataFrame())
    monkeypatch.setenv("FMP_API_KEY", "x")
    out = data.fetch("AAPL", "2026-07-01", "2026-07-28", incremental_ok=True)
    assert cagrilar == ["fmp"] and not out.empty
    assert data._LAST_SOURCE.get("AAPL") == "fmp"


def _bars(n, son="2026-07-28", fiyat=100.0):
    tarih = pd.bdate_range(end=pd.Timestamp(son), periods=n)
    return pd.DataFrame({"date": tarih, "open": fiyat, "high": fiyat + 1,
                         "low": fiyat - 1, "close": fiyat, "volume": 1_000_000.0})


# ------------------------------------------------------------------ uç yolu + auth
def test_grouped_uc_yolu_ve_bearer_basligi(monkeypatch):
    """Yol doküman sayfasındaki literal istek URL'i; anahtar BAŞLIKTA gider. Sorgu parametresinde
    gitseydi her httpx hata metni ve her ara-vekil logu anahtarı taşırdı."""
    _anahtar(monkeypatch)
    cap = {}
    _mock_http(monkeypatch, {"results": [ROW_AAPL]}, cap)
    rows = massive.grouped_daily("2026-07-28")
    assert cap["url"] == "https://api.massive.com/v2/aggs/grouped/locale/us/market/stocks/2026-07-28"
    assert cap["headers"]["Authorization"] == "Bearer massive_test_key_1234"
    assert cap["params"] == {"adjusted": "true", "include_otc": "false"}
    assert "massive_test_key_1234" not in json.dumps(cap["params"])     # anahtar URL'e SIZMAZ
    assert rows and rows[0]["T"] == "AAPL"


def test_custom_bars_ve_all_tickers_yollari(monkeypatch):
    _anahtar(monkeypatch)
    cap = {}
    _mock_http(monkeypatch, {"results": [ROW_AAPL]}, cap)
    massive.custom_bars("aapl", "2026-06-01", "2026-07-28")
    assert cap["url"] == "https://api.massive.com/v2/aggs/ticker/AAPL/range/1/day/2026-06-01/2026-07-28"
    _mock_http(monkeypatch, {"results": [{"ticker": "AAPL"}]}, cap)
    massive.all_tickers()
    assert cap["url"] == "https://api.massive.com/v3/reference/tickers"


def test_gun_bos_ise_bos_liste_istek_patlarsa_none(monkeypatch):
    _anahtar(monkeypatch)
    _mock_http(monkeypatch, {"results": []})                  # tatil: düzgün cevap, sıfır satır
    assert massive.grouped_daily("2026-07-04") == []
    _mock_http(monkeypatch, {}, status=500)                   # sağlayıcı arızası
    assert massive.grouped_daily("2026-07-28") is None


# ------------------------------------------------------------------ 429 / hız sınırı
def test_429_ustel_geri_cekilme_sonra_durust_hata(monkeypatch):
    _anahtar(monkeypatch)
    uykular = []
    monkeypatch.setattr(massive, "_sleep", lambda s: uykular.append(s))
    _mock_http(monkeypatch, {"error": "rate"}, status=429)
    with pytest.raises(massive.MassiveError) as ei:
        massive._get("/v2/aggs/grouped/locale/us/market/stocks/2026-07-28")
    assert ei.value.reason == "HTTP 429" and ei.value.status == 429
    assert uykular == [2.0, 4.0, 8.0]                 # BACKOFF_BASE_S * 2**n, MAX_RETRY-1 kez
    assert massive.health()["retries"] == 3


def test_401_geri_cekilmez_hemen_dusulur(monkeypatch):
    """Yanlış anahtar geri çekilmeyle düzelmez; 4 kez denemek yalnız zaman kaybettirir."""
    _anahtar(monkeypatch)
    uykular = []
    monkeypatch.setattr(massive, "_sleep", lambda s: uykular.append(s))
    _mock_http(monkeypatch, {"error": "unauthorized"}, status=401)
    with pytest.raises(massive.MassiveError) as ei:
        massive._get("/v2/aggs/grouped/locale/us/market/stocks/2026-07-28")
    assert ei.value.status == 401 and uykular == []


def test_token_bucket_dakikada_bes(monkeypatch):
    saat = {"t": 0.0}
    uykular = []
    monkeypatch.setattr(massive, "_now", lambda: saat["t"])
    monkeypatch.setattr(massive, "_sleep", lambda s: (uykular.append(s), saat.__setitem__("t", saat["t"] + s)))
    massive._CALLS.clear()
    for _ in range(massive.RATE_PER_MIN):
        massive._throttle()
    assert uykular == []                       # ilk 5 serbest
    massive._throttle()                        # 6.'sı pencerenin dolmasını BEKLER
    assert uykular and uykular[0] == pytest.approx(massive.RATE_WINDOW_S, abs=0.05)


# ------------------------------------------------------------------ tek çağrı disiplini
def test_anlik_goruntu_tum_evren_icin_TEK_grouped_cagrisi(monkeypatch):
    """Bu modülün VARLIK SEBEBİ. 250 sembolün son barı için sağlayıcıya 1 kez gidilir."""
    _anahtar(monkeypatch)
    cap = {}
    _mock_http(monkeypatch, {"results": [ROW_AAPL, ROW_MSFT]}, cap)
    for _ in range(250):
        massive.bar_for("AAPL", "2026-07-28")
        massive.bar_for("MSFT", "2026-07-28")
    assert cap["n"] == 1
    assert massive.bar_for("AAPL", "2026-07-28")["close"] == 340.24


def test_anlik_goruntu_diskten_okunur_yeni_surec_cagri_atmaz(monkeypatch):
    """Zamanlayıcı ve API AYRI süreçlerdir; disk önbelleği olmasaydı her süreç bir çağrı harcardı."""
    _anahtar(monkeypatch)
    cap = {}
    _mock_http(monkeypatch, {"results": [ROW_AAPL]}, cap)
    massive.snapshot("2026-07-28")
    assert cap["n"] == 1
    massive.reset_cache()                       # "yeni süreç": bellek memosu yok, disk var
    snap = massive.snapshot("2026-07-28")
    assert cap["n"] == 1 and snap["AAPL"]["close"] == 340.24


def test_basarisiz_grouped_TICKER_BASINA_TEKRARLANMAZ(monkeypatch):
    """`bar_for` ticker başına çağrılır. Başarısızlık hatırlanmazsa 250 sembollük tur, düşmüş grouped
    çağrısını 250 KEZ dener (her biri 4 tekrar + üstel bekleme + 5/dk kovası) — bir dakikalık arıza
    tazelemeyi saatlerce bloke ederdi. Soğuma penceresi bunu tek denemeye indirir."""
    _anahtar(monkeypatch)
    cagri = {"n": 0}
    def fake_get(url, params=None, headers=None, timeout=None):
        cagri["n"] += 1
        return _Resp({}, status=500)
    monkeypatch.setattr(massive.httpx, "get", fake_get)
    for _ in range(250):
        assert massive.bar_for("AAPL", "2026-07-28") is None
    assert cagri["n"] == massive.MAX_RETRY      # 250 tur değil, TEK denemenin tekrarları kadar


def test_soguma_dolunca_yeniden_denenir(monkeypatch):
    """Soğuma kalıcı bir kapatma DEĞİL: sağlayıcı düzelince kaynak geri gelmeli."""
    _anahtar(monkeypatch)
    saat = {"t": 0.0}
    monkeypatch.setattr(massive, "_now", lambda: saat["t"])
    _mock_http(monkeypatch, {}, status=500)
    assert massive.bar_for("AAPL", "2026-07-28") is None
    saat["t"] = massive.FAIL_COOLDOWN_S + 1
    cap = {}
    _mock_http(monkeypatch, {"results": [ROW_AAPL]}, cap)
    assert massive.bar_for("AAPL", "2026-07-28")["close"] == 340.24
    assert cap["n"] == 1


def test_gun_ici_tazeleme_DUNUN_barini_bulur(monkeypatch):
    """CANLI BULGUDAN DOĞAN ÇİVİ. Artımlı kol kesin bir gün isterse (`end`=bugün, EOD henüz yok)
    boş döner ve zincir Cboe'ye düşer — canlı defterde 250 ticker'ın hepsi `source=cboe` çıkmıştı,
    yani kota tasarrufu HİÇ devreye girmemişti. `latest_bar` eldeki en taze barı bulmalı."""
    _anahtar(monkeypatch)
    istenen = []
    def fake_get(url, params=None, headers=None, timeout=None):
        g = url.rsplit("/", 1)[-1]
        istenen.append(g)
        # bugünün (29'unun) EOD'si YOK; dünün (28'inin) var
        return _Resp({"results": [] if g == "2026-07-29" else [ROW_AAPL]})
    monkeypatch.setattr(massive.httpx, "get", fake_get)
    bar = massive.latest_bar("AAPL", end="2026-07-29")
    assert istenen[:2] == ["2026-07-29", "2026-07-28"]      # geriye yürüdü
    assert bar and bar["close"] == 340.24 and bar["date"] == "2026-07-28"


def test_artimli_kol_gun_ici_de_FMPye_dusmez(monkeypatch):
    """Aynı bulgunun zincir tarafı: bugünün EOD'si yokken de artımlı kol çalışmalı, FMP'ye değil."""
    _anahtar(monkeypatch)
    _cache_yaz("AAPL", n=250, son="2026-07-27")
    monkeypatch.setenv("FMP_API_KEY", "x")
    fmp_cagri = []
    monkeypatch.setattr(data, "_fetch_fmp", lambda t, s, e, to: fmp_cagri.append(t) or _bars(250))
    def fake_get(url, params=None, headers=None, timeout=None):
        g = url.rsplit("/", 1)[-1]
        return _Resp({"results": [] if g == "2026-07-29" else [ROW_AAPL]})
    monkeypatch.setattr(massive.httpx, "get", fake_get)
    out = data.fetch("AAPL", "2026-01-01", "2026-07-29", incremental_ok=True)
    assert fmp_cagri == [] and data._LAST_SOURCE.get("AAPL") == "massive"
    assert str(pd.Timestamp(out["date"].iloc[-1]).date()) == "2026-07-28"


def test_tatil_gununde_bir_onceki_seansa_yurunur(monkeypatch):
    _anahtar(monkeypatch)
    gunler = []
    def fake_get(url, params=None, headers=None, timeout=None):
        gunler.append(url.rsplit("/", 1)[-1])
        return _Resp({"results": [] if len(gunler) == 1 else [ROW_AAPL]})
    monkeypatch.setattr(massive.httpx, "get", fake_get)
    snap = massive.snapshot()                   # tarih verilmedi → son seanstan geriye yürür
    assert len(gunler) == 2 and snap.get("AAPL")


# ------------------------------------------------------------------ yazım kapısı (ölçüm → karar)
def test_kapi_rol1_taban_olcumune_dayanir(monkeypatch):
    """Kapı AÇIK ama "öylesine" değil: dayanağı Rol 1'in 2026-07-29 ölçümüdür ve bu dayanak
    okunabilir olmalı — operatör "neden yazım modundayız" sorusunu tahminle cevaplamamalı."""
    _anahtar(monkeypatch)
    assert massive.write_enabled() is True and massive.mode() == "yazim"
    b = massive.verify_basis()
    assert b["basis"] == "rol1_taban" and b["verdict"] == "uyumlu"
    assert massive.BASELINE["comparisons"][1]["max_abs_dev_pct"] == 0.0   # temettü ex-tarihli kıyas


def test_anahtar_yoksa_kapi_her_halukarda_kapali(monkeypatch):
    monkeypatch.delenv(massive.KEY_NAME, raising=False)
    secrets.clear_cache()
    assert massive.write_enabled() is False       # kapı açık olsa da çağıracak uç yok


def _olcum_yaz(verdict="uyumlu", samples=200, yas_gun=0):
    from meridian import store
    at = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=yas_gun)
    store.write_json(massive.VERIFY_FILE, {"verdict": verdict, "samples": samples,
                                           "checked_at": at.isoformat(timespec="seconds")})


def test_yerel_olcum_tabani_EZER(monkeypatch):
    """En taze kanıt kazanır. Yerel `--dogrula` bu makinenin GERÇEK önbelleğiyle ölçer; taban ölçümü
    onu geçersiz kılamaz. Aksi hâlde kapı, çürütülmüş bir kanıtla açık kalırdı."""
    _anahtar(monkeypatch)
    _olcum_yaz("uyumsuz", 200)
    assert massive.write_enabled() is False          # ölçek uyuşmuyor → zincir KARIŞTIRILMAZ
    assert massive.verify_basis()["basis"] == "yerel_olcum"
    _olcum_yaz("uyumlu", 200)
    assert massive.write_enabled() is True and massive.mode() == "yazim"


def test_bayatlik_CELISKI_DEGIL_kapiyi_kapatmaz(monkeypatch):
    """ZAMAN BOMBASI ÇİVİSİ. İlk yazımda bayat ölçüm kapıyı kapatıyordu: 30 gün sonra yazım modu
    kendiliğinden kapanır, zincir sembol-başına FMP'ye döner ve kota yağmuru hiçbir şey değişmemiş
    gibi geri gelirdi — sebebini kimse bilmeden. Ölçümün ESKİMESİ, ölçeklerin AYRIŞTIĞININ kanıtı
    değil. Zayıf/eksik onaylar da çürütme değildir; SADECE 'uyumsuz' kapatır ve o YAŞTAN BAĞIMSIZDIR."""
    _anahtar(monkeypatch)
    uyarilar = []
    import meridian.obs as obs
    monkeypatch.setattr(obs, "warn", lambda e, **f: uyarilar.append(e))

    _olcum_yaz("uyumlu", 200, yas_gun=massive.VERIFY_MAX_AGE_DAYS + 1)
    assert massive.write_enabled() is True            # kapı AÇIK kaldı (tabana dönüldü)
    assert "massive_verify_stale" in uyarilar         # ama yenileme GEREKTİĞİ söylendi

    _olcum_yaz("uyumlu", massive.VERIFY_MIN_SAMPLES - 1)
    assert massive.write_enabled() is True            # zayıf onay da çürütme değil → taban

    _olcum_yaz("uyumsuz", 200, yas_gun=massive.VERIFY_MAX_AGE_DAYS + 99)
    assert massive.write_enabled() is False           # ÇÜRÜTME yaştan BAĞIMSIZ olarak kapatır


def test_compare_yuvarlama_payini_hesaba_katar():
    """CSV kapanışları yuvarlanmış olabilir; yarım cent, ucuz hissede %0.1'i tek başına aşar.
    Yuvarlama payı hesaba katılmasaydı ölçüm SAHTE uyuşmazlıkla 'uyumsuz' hükmü verirdi."""
    ref = {"2026-07-27": 0.38, "2026-07-28": 0.39}
    mas = {"2026-07-27": 0.3843, "2026-07-28": 0.3861}     # yarım centin içinde
    c = massive.compare(ref, mas)
    assert c["samples"] == 2 and c["mismatches"] == 0
    pahali = massive.compare({"2026-07-28": 740.0}, {"2026-07-28": 742.5})   # %0.34 → gerçek sapma
    assert pahali["mismatches"] == 1


def test_verify_uyumsuzlukta_hukum_yazar_ve_kapi_kapali_kalir(monkeypatch):
    _anahtar(monkeypatch)
    monkeypatch.setattr(massive, "_massive_closes",
                        lambda s, a, b: {f"2026-05-{d:02d}": 100.0 * 1.5 for d in range(1, 31)})
    monkeypatch.setattr(massive, "_cache_closes",
                        lambda s, a: {f"2026-05-{d:02d}": 100.0 for d in range(1, 31)})
    out = massive.verify(symbols=["AAPL", "MSFT"], days=60)
    assert out["verdict"] == "uyumsuz" and out["mismatch_pct"] == 1.0
    assert massive.write_enabled() is False
    from meridian import store
    assert store.read_json(massive.VERIFY_FILE, {})["verdict"] == "uyumsuz"


def test_verify_yetersiz_orneklemde_uyumlu_demez(monkeypatch):
    _anahtar(monkeypatch)
    monkeypatch.setattr(massive, "_massive_closes", lambda s, a, b: {"2026-05-01": 100.0})
    monkeypatch.setattr(massive, "_cache_closes", lambda s, a: {"2026-05-01": 100.0})
    out = massive.verify(symbols=["AAPL"], days=60)
    assert out["verdict"] == "yetersiz_orneklem"       # 1 bar, "mükemmel uyum" demek DEĞİLDİR
    # ...ama "uyumlu diyemem" ile "uyumsuz" AYNI ŞEY DEĞİL: zayıf bir ölçüm tabanı çürütmez,
    # yalnız onaylayamaz. Kapıyı kapatan tek hüküm "uyumsuz"tur (bkz. bayatlık çivisi).
    assert massive.verify_basis()["basis"] == "yerel_olcum"
    assert massive.write_enabled() is True


def test_verify_anahtarsiz_olculemedi_der(monkeypatch):
    monkeypatch.delenv(massive.KEY_NAME, raising=False)
    secrets.clear_cache()
    out = massive.verify(symbols=["AAPL"], write=False)
    assert out["verdict"] == "olculemedi" and out["samples"] == 0


# ------------------------------------------------------------------ zincir: yalnız-alarm modu
def _cache_yaz(ticker, n=250, son="2026-07-28", fiyat=100.0):
    df = _bars(n, son=son, fiyat=fiyat)
    data._write_bars(df, data._cache_path(ticker))
    return df


def test_yalniz_alarm_modunda_massive_zincire_GIRMEZ(monkeypatch):
    """Ölçüm ÇÜRÜTÜLMÜŞSE barları hâlâ FMP/Cboe yazar — Massive tek satır bile yazmaz."""
    _anahtar(monkeypatch)
    _olcum_yaz("uyumsuz", 200)                # yerel ölçüm tabanı ezdi → yalnız-alarm
    _cache_yaz("AAPL")
    monkeypatch.setattr(data, "_fetch_massive", lambda *a, **k: pytest.fail("massive zincire girdi"))
    monkeypatch.setattr(data, "_fetch_cboe", lambda t, to: _bars(250))
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda t, s, e, to: pd.DataFrame())
    monkeypatch.setattr(massive, "bar_for", lambda t, d: None)
    monkeypatch.setattr(massive, "latest_bar", lambda t, end=None: None)
    out = data.fetch("AAPL", "2026-01-01", "2026-07-28", incremental_ok=True)
    assert not out.empty and data._LAST_SOURCE.get("AAPL") == "cboe"


def test_uyusmazlik_alarmi_basar_ama_karantina_yok(monkeypatch):
    """v1 kararı: uyuşmazlık ALARM'dır. Hangi tarafın haklı olduğunu bilmeden barı atmak,
    teşhisi olmayan bir tedavi olurdu.

    SEVİYE DÜZELTMESİ (K1, 2026-07-30): bu testin adı ve v1 kararı ilk günden "ALARM" diyordu ama
    kod `obs.warn` basıyordu — ve `notify.py:84` alarm-olmayan her satırı eler, yani uyuşmazlık
    bildirim/inbox/telefon zincirine HİÇ giremiyordu. Test artık gerçek seviyeyi çiviliyor:
    DATA_QUALITY jetonu + makine-okunur `kind` adı (obs.alarm olay adını değiştirdiği için ad
    `kind` alanında yaşar — `failed_broker_rejection` tuzağının tekrarlanmaması için)."""
    _anahtar(monkeypatch)
    _olcum_yaz("uyumsuz", 200)
    alarmlar = []
    import meridian.obs as obs
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **f: alarmlar.append((tok, msg, f)))
    monkeypatch.setattr(data, "_fetch_cboe", lambda t, to: _bars(250, fiyat=100.0))
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda t, s, e, to: pd.DataFrame())
    monkeypatch.setattr(massive, "bar_for",
                        lambda t, d: {"date": d, "open": 1, "high": 1, "low": 1,
                                      "close": 105.0, "volume": 1})     # %5 sapma
    out = data.fetch("AAPL", "2026-01-01", "2026-07-28")
    olay = [f for tok, _m, f in alarmlar
            if tok == obs.ALARM_DATA_QUALITY and f.get("kind") == "bar_kaynak_uyusmazligi"]
    assert olay and olay[0]["ticker"] == "AAPL"
    assert olay[0]["source"] == "cboe" and olay[0]["dev_pct"] == pytest.approx(5.0, abs=0.01)
    assert len(out) == 250 and out["close"].iloc[-1] == 100.0    # BAR DEĞİŞMEDİ — karantina yok


def test_tolerans_icindeki_fark_alarm_uretmez(monkeypatch):
    _anahtar(monkeypatch)
    _olcum_yaz("uyumsuz", 200)
    uyarilar = []
    import meridian.obs as obs
    monkeypatch.setattr(obs, "warn", lambda e, **f: uyarilar.append(e))
    # SEVİYE DÜZELTMESİ (K1): uyuşmazlık artık DATA_QUALITY alarmı — tolerans İÇİNDEKİ farkın
    # alarm üretmediği de aynı kanaldan doğrulanmalı, yoksa test sessizce anlamsızlaşırdı.
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **f: uyarilar.append(f.get("kind") or tok))
    monkeypatch.setattr(data, "_fetch_cboe", lambda t, to: _bars(250, fiyat=100.0))
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda t, s, e, to: pd.DataFrame())
    monkeypatch.setattr(massive, "bar_for",
                        lambda t, d: {"date": d, "close": 100.05, "open": 1, "high": 1,
                                      "low": 1, "volume": 1})           # %0.05 < %0.1
    data.fetch("AAPL", "2026-01-01", "2026-07-28")
    assert "bar_kaynak_uyusmazligi" not in uyarilar
    assert data.crosscheck_report()["compared"] == 1        # ölçüm YİNE DE birikir


def test_alarm_esigi_olculen_gurultu_tabaninin_USTUNDE():
    """Eşik keyfi değil ÖLÇÜLMÜŞ: 251 sembolde iyi huylu sapma tabanı ~%0.08. Eşik onun hemen
    üstünde olsaydı (ilk yazımdaki %0.1) ilk oynak gün yanlış alarm üretir ve yanlış alarmlar gerçek
    alarmları okunmaz yapardı. Gerçek arıza sınıfı %1 üstündedir."""
    gurultu = max(c["max_abs_dev_pct"] for c in massive.BASELINE["comparisons"]) / 100.0
    assert gurultu == pytest.approx(0.00081, abs=1e-5)
    assert data.MASSIVE_TOL > gurultu * 3          # gürültüden belirgin uzak
    assert data.MASSIVE_TOL < 0.01                 # ama gerçek arızayı (>%1) yine yakalar
    assert massive.VERIFY_TOL < data.MASSIVE_TOL   # ölçek HÜKMÜ daha sıkı eşikle verilir


def test_crosscheck_defteri_olcumu_biriktirir(monkeypatch):
    """Alarm basmak tek başına yeterli değil: kaç bar kıyaslandı, kaçı saptı — karar bu sayılardan
    çıkar (üretilip tüketilmeyen kanıt bırakma disiplini)."""
    _anahtar(monkeypatch)
    _olcum_yaz("uyumsuz", 200)
    monkeypatch.setattr(data, "_fetch_cboe", lambda t, to: _bars(250, fiyat=100.0))
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda t, s, e, to: pd.DataFrame())
    import meridian.obs as obs
    monkeypatch.setattr(obs, "warn", lambda e, **f: None)
    monkeypatch.setattr(massive, "bar_for",
                        lambda t, d: {"date": d, "close": 110.0, "open": 1, "high": 1,
                                      "low": 1, "volume": 1})
    for t in ("AAPL", "MSFT", "NVDA"):
        data.fetch(t, "2026-01-01", "2026-07-28")
    r = data.crosscheck_report()
    assert r["tickers"] == 3 and r["compared"] == 3 and r["mismatches"] == 3
    assert r["max_dev"] == pytest.approx(0.10, abs=0.001)


# ------------------------------------------------------------------ zincir: yazım modu
def test_yazim_modunda_FMP_HIC_CAGRILMAZ(monkeypatch):
    """KOTA TASARRUFUNUN ÇİVİSİ: geçmişi olan bir sembolde artımlı bar Massive'den gelince o sembol
    için FMP'ye tek istek bile atılmaz. Bugün bu yol sembol başına 1 FMP isteği harcıyor ve 250
    sembol günlük kotanın tamamını yakıyor."""
    _anahtar(monkeypatch)
    _olcum_yaz("uyumlu", 200)
    monkeypatch.setenv("FMP_API_KEY", "x")
    fmp_cagri = []
    monkeypatch.setattr(data, "_fetch_fmp", lambda t, s, e, to: fmp_cagri.append(t) or _bars(250))
    monkeypatch.setattr(data, "_fetch_cboe", lambda t, to: pytest.fail("cboe'ye düşülmemeliydi"))
    monkeypatch.setattr(massive, "latest_bar",
                        lambda t, end=None: {"date": "2026-07-28", "open": 1.0, "high": 2.0,
                                             "low": 0.5, "close": 1.5, "volume": 10.0})
    out = data.fetch("AAPL", "2026-01-01", "2026-07-28", incremental_ok=True)
    assert fmp_cagri == []                                  # ← tasarruf burada
    assert data._LAST_SOURCE.get("AAPL") == "massive" and len(out) == 1


# ------------------------------------------------------------------ sembol-başına yakın dönem
def test_yakin_donem_penceresinde_massive_FMPden_ONCE_gelir(monkeypatch):
    """Kota tahsis politikası (2026-07-29): FMP kotası bilgi katmanına ayrıldı. Tek sembolün yakın
    dönem penceresini isteyen çağrılar artık Massive custom-bars ile karşılanır, FMP'ye düşülmez."""
    _anahtar(monkeypatch)
    monkeypatch.setenv("FMP_API_KEY", "x")
    fmp_cagri = []
    monkeypatch.setattr(data, "_fetch_fmp", lambda t, s, e, to: fmp_cagri.append(t) or _bars(100))
    monkeypatch.setattr(data, "_fetch_massive_hist", lambda t, s, e, to: _bars(120))
    monkeypatch.setattr(data, "_fetch_cboe", lambda t, to: pytest.fail("cboe'ye düşülmemeliydi"))
    monkeypatch.setattr(massive, "bar_for", lambda t, d: None)
    monkeypatch.setattr(massive, "latest_bar", lambda t, end=None: None)
    yakin = str((dt.date.today() - dt.timedelta(days=120)))
    out = data.fetch("AAPL", yakin, "2026-07-28")
    assert fmp_cagri == [] and not out.empty
    assert data._LAST_SOURCE.get("AAPL") == "massive_hist"


def test_derin_tarih_massiveye_HIC_SORULMAZ(monkeypatch):
    """2 yıldan eski başlangıç: Massive orada yarım seri döndürür. Yarım seri, boş dönüşten çok daha
    tehlikelidir — sessizce kısa bir geçmiş yazılır ve walk-forward ısınmasız barlarla koşar.
    Üretimdeki toplu yol (dataset.FETCH_START=2021-01-01) tam olarak bu sınıfa girer."""
    _anahtar(monkeypatch)
    monkeypatch.setenv("FMP_API_KEY", "x")
    monkeypatch.setattr(data, "_fetch_massive_hist",
                        lambda t, s, e, to: pytest.fail("derin tarih Massive'e soruldu"))
    monkeypatch.setattr(data, "_fetch_fmp", lambda t, s, e, to: _bars(500))
    monkeypatch.setattr(massive, "bar_for", lambda t, d: None)
    monkeypatch.setattr(massive, "latest_bar", lambda t, end=None: None)
    out = data.fetch("AAPL", "2021-01-01", "2026-07-28")
    assert not out.empty and data._LAST_SOURCE.get("AAPL") == "fmp"


def test_covers_iki_yil_sinirini_paylı_uygular():
    assert massive.covers(str(dt.date.today() - dt.timedelta(days=30))) is True
    assert massive.covers("2021-01-01") is False               # dataset.FETCH_START → daima FMP
    sinirda = dt.date.today() - dt.timedelta(days=365 * massive.HISTORY_YEARS - 5)
    assert massive.covers(str(sinirda)) is False               # sınıra fazla yakın → sorma


def test_massive_hist_normal_kaynak_gibi_sahiplenir(monkeypatch):
    """Grouped kolu (tek bar) geçmişi sahiplenemez ama custom-bars kolu GERÇEK geçmiş taşır —
    o yüzden normal bir kaynak gibi davranmalı, yoksa hiçbir zaman sahibi olmayan bir geçmiş kalırdı."""
    _anahtar(monkeypatch)
    monkeypatch.setattr(data, "_fetch_massive_hist", lambda t, s, e, to: _bars(300))
    monkeypatch.setattr(data, "_fetch_cboe", lambda t, to: pd.DataFrame())
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda t, s, e, to: pd.DataFrame())
    monkeypatch.setattr(massive, "bar_for", lambda t, d: None)
    monkeypatch.setattr(massive, "latest_bar", lambda t, end=None: None)
    yakin = str((dt.date.today() - dt.timedelta(days=200)))
    data.load_bars("TSLA", yakin, "2026-07-28", use_cache=False, polite_delay=0)
    assert data._bar_source("TSLA") == "massive_hist"           # sahiplendi (grouped kolu sahiplenmezdi)


def test_gecmissiz_sembolde_artimli_kol_devreye_girmez(monkeypatch):
    """Tek bar bir GEÇMİŞ kuramaz: 200 bardan az önbelleği olan sembol derin backfill (FMP) ister."""
    _anahtar(monkeypatch)
    _olcum_yaz("uyumlu", 200)
    _cache_yaz("ZZZ", n=10)                                  # kısa önbellek
    monkeypatch.setattr(data, "_fetch_massive", lambda *a, **k: pytest.fail("artımlı kol açıldı"))
    monkeypatch.setattr(data, "_fetch_cboe", lambda t, to: _bars(300))
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda t, s, e, to: pd.DataFrame())
    monkeypatch.setattr(massive, "bar_for", lambda t, d: None)
    monkeypatch.setattr(massive, "latest_bar", lambda t, end=None: None)
    out = data.load_bars("ZZZ", "2026-01-01", "2026-07-28", use_cache=False, polite_delay=0)
    assert not out.empty


# ------------------------------------------------------------------ artımlı kaynak geçmişi bozamaz
def test_artimli_bar_gecmisi_TEK_SATIRA_indiremez(monkeypatch):
    """EN TEHLİKELİ YOL. Kurumsal-aksiyon sıfırlaması `fetched`in TAM geçmiş olduğunu varsayar ve
    önbelleği atıp yerine onu yazar. Massive TEK bar döndürür — koruma olmasaydı bir bölünme şüphesi
    sembolün 250 barlık geçmişini 1 satıra indirirdi (ve corp_reset istisnası satır-kaybı korumasını
    da devre dışı bırakırdı)."""
    _anahtar(monkeypatch)
    _olcum_yaz("uyumlu", 200)
    _cache_yaz("AAPL", n=250, fiyat=100.0)
    # Massive barı önbellekten %90 sapmalı → _corporate_action TETİKLENİR
    monkeypatch.setattr(massive, "latest_bar",
                        lambda t, end=None: {"date": "2026-07-29", "open": 10.0, "high": 10.0,
                                             "low": 10.0, "close": 10.0, "volume": 1.0})
    monkeypatch.setattr(massive, "bar_for",
                        lambda t, d: {"date": d, "open": 10.0, "high": 10.0,
                                      "low": 10.0, "close": 10.0, "volume": 1.0})
    derin = _bars(251, son="2026-07-29", fiyat=100.0)
    monkeypatch.setattr(data, "_fetch_cboe", lambda t, to: derin)
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda t, s, e, to: pd.DataFrame())
    monkeypatch.setattr(data, "_fetch_fmp", lambda t, s, e, to: pd.DataFrame())
    out = data.load_bars("AAPL", "2026-01-01", "2026-07-29", use_cache=False, polite_delay=0)
    # ASIL ÇİVİ DİSKTE: load_bars istenen PENCEREYİ döndürür (burada ~150 iş günü), önbelleğin
    # tamamını değil — koruma başarısız olsaydı diskte 1 satır kalırdı.
    diskte = pd.read_csv(data._cache_path("AAPL"))
    assert len(diskte) >= 250, "artımlı tek bar geçmişi sildi"
    assert len(out) > 100                    # pencere dolu döndü, tek bara inmedi


def test_massive_dikis_defterini_kirletmez(monkeypatch):
    """Dikiş defteri ANOMALİ sayar. Massive tasarımı gereği yalnız ekler; canlı dağılımda geçmişin
    sahibi cboe(192)+nasdaq(59) olduğu için Massive açıldığı gün HER sembol 'dikişli' görünür ve
    defter okunmaz hâle gelirdi. Ekleme-yalnız KISITI yine de uygulanmalı."""
    _anahtar(monkeypatch)
    _olcum_yaz("uyumlu", 200)
    _cache_yaz("AAPL", n=250, fiyat=100.0)
    data._pin_source("AAPL", "cboe")
    monkeypatch.setattr(massive, "latest_bar",
                        lambda t, end=None: {"date": "2026-07-29", "open": 100.0, "high": 101.0,
                                             "low": 99.0, "close": 100.5, "volume": 5.0})
    monkeypatch.setattr(data, "_fetch_cboe", lambda t, to: pd.DataFrame())
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda t, s, e, to: pd.DataFrame())
    out = data.load_bars("AAPL", "2026-01-01", "2026-07-29", use_cache=False, polite_delay=0)
    assert data.seam_report()["tickers"] == 0            # anomali defteri temiz
    diskte = pd.read_csv(data._cache_path("AAPL"))       # (out istenen PENCEREdir, önbelleğin tamamı değil)
    assert len(diskte) == 251                             # ama bar EKLENDİ: 250 + 1
    assert float(diskte["close"].iloc[-1]) == 100.5       # eklenen bar Massive'in barı
    assert data._bar_source("AAPL") == "cboe"             # sahiplik DEVREDİLMEDİ


def test_massive_gecmis_sahipligini_almaz(monkeypatch):
    """Sabitleme 'bu geçmişi kim yazdı' sorusudur. Massive tek bar ekler; sahipliği ona vermek,
    gerçek sahip geri geldiğinde onu 'yabancı kaynak' sayıp geçmişi uzatmasını engellerdi."""
    _anahtar(monkeypatch)
    _olcum_yaz("uyumlu", 200)
    _cache_yaz("NVDA", n=250, fiyat=50.0)                 # bars_source kaydı YOK (pinned is None)
    monkeypatch.setattr(massive, "latest_bar",
                        lambda t, end=None: {"date": "2026-07-29", "open": 50.0, "high": 51.0,
                                             "low": 49.0, "close": 50.2, "volume": 5.0})
    monkeypatch.setattr(data, "_fetch_cboe", lambda t, to: pd.DataFrame())
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda t, s, e, to: pd.DataFrame())
    data.load_bars("NVDA", "2026-01-01", "2026-07-29", use_cache=False, polite_delay=0)
    assert data._bar_source("NVDA") is None               # Massive sahiplenmedi


# ------------------------------------------------------------------ sır kaydı
def test_massive_anahtari_panodan_girilebilir():
    """Pano yalnız ALLOWED içindeki adları yazabilir; liste kaydı olmadan operatör anahtarı
    hiçbir zaman giremezdi (NOUS_FALLBACK_MODEL'de tam olarak bu yaşandı)."""
    assert massive.KEY_NAME in secrets.ALLOWED
    secrets.set(massive.KEY_NAME, "abc12345678")
    assert secrets.get(massive.KEY_NAME) == "abc12345678"
    assert secrets.status()[massive.KEY_NAME]["set"] is True
    assert "abc12345678" not in str(secrets.status())      # değer ASLA sızmaz
    secrets.delete(massive.KEY_NAME)


def test_ping_anahtari_sizdirmaz_ve_hata_sinifini_ayirir(monkeypatch):
    """Pano Test düğmesinin sözleşmesi: yalnız {ok, detail}, ASLA anahtar. 401 ile 429 ayrı
    söylenmeli — "anahtar geçersiz" ile "biraz bekle" operatör için tamamen farklı iki eylemdir."""
    _anahtar(monkeypatch)
    _mock_http(monkeypatch, {"results": [{"ticker": "AAPL"}]})
    r = massive.ping()
    assert r["ok"] is True and "AAPL" in r["detail"]
    assert "massive_test_key_1234" not in str(r)
    _mock_http(monkeypatch, {}, status=401)
    assert massive.ping() == {"ok": False, "detail": "anahtar geçersiz/yetkisiz"}
    _mock_http(monkeypatch, {}, status=429)
    assert massive.ping()["ok"] is False and "5/dk" in massive.ping()["detail"]
    monkeypatch.delenv(massive.KEY_NAME, raising=False)
    secrets.clear_cache()
    assert massive.ping()["detail"].startswith(massive.KEY_NAME)


def test_pano_test_dugmesi_VAR_OLAN_uca_baglanir(monkeypatch):
    """YENİ uç yazılmadı: `/api/secrets/test/massive` mevcut dala eklendi. Dal GERÇEKTEN çağrılıyor
    mu diye davranışsal test — metin araması, dalın yanlış fonksiyonu çağırdığını yakalamaz.
    Bilinmeyen sağlayıcı HTTP 400 döndürdüğü için bu kablolama olmadan düğme ÖLÜ olurdu."""
    from meridian import api
    monkeypatch.setattr(api, "_auth", lambda r: None)
    monkeypatch.setattr(massive, "ping", lambda: {"ok": True, "detail": "nisan"})
    assert api.api_test_secret("massive", request=None) == {"ok": True, "detail": "nisan"}
    with pytest.raises(Exception):                      # bilinmeyen sağlayıcı hâlâ reddedilir
        api.api_test_secret("bilinmeyen_saglayici", request=None)


def test_pano_alani_ve_test_dugmesi_bagli():
    """Alan listede TEK olmalı ve 4. eleman (sağlayıcı) Test düğmesini çıkarır. Dürüstlük çivisi:
    metin, anahtar yokken hiçbir şeyin bozulmadığını SÖYLEMELİ — operatör bunu bilmeli."""
    src = open("meridian/web/app.js").read()
    satir = [s for s in src.splitlines() if s.strip().startswith('["MASSIVE_API_KEY"')]
    assert len(satir) == 1, "MASSIVE_API_KEY alanı listede yok ya da çoğaldı"
    assert satir[0].rstrip().endswith('"massive"],'), "Test düğmesi sağlayıcıya bağlanmamış"
    assert "TEK ÇAĞRILIK" in satir[0] and "FMP→Cboe→Nasdaq ile aynen sürer" in satir[0]
    assert massive.KEY_NAME in secrets.ALLOWED          # izin listesi olmadan alan kaydedilemezdi


def test_status_ozeti_modu_ve_dayanagi_bildirir(monkeypatch):
    """Pano/teşhis, HANGİ modda olduğumuzu VE bunun hangi kanıta dayandığını okuyabilmeli."""
    _anahtar(monkeypatch)
    s = massive.status()
    assert s["available"] is True and s["write_enabled"] is True
    assert s["mode"] == "yazim" and s["rate_limit"] == "5/dk"
    assert s["basis"]["basis"] == "rol1_taban"
    _olcum_yaz("uyumsuz", 200)
    s2 = massive.status()
    assert s2["mode"] == "yalniz_alarm" and s2["basis"]["basis"] == "yerel_olcum"

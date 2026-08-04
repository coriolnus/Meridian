"""v186 — DÖNGÜ NABZI (asılı-tick bekçisi yanlış-pozitifi) + MASSIVE 401/403 GÜN-İÇİ YETKİ KAPISI.

KAPATILAN İKİ CANLI KUSUR (ikisi de ÖLÇÜLDÜ, varsayılmadı):

  (1) NABIZ — A1 canlı, 2026-08-03 20:00→23:30 UTC: `deploy/oracle-a1/tick_watchdog.sh` (eşik
      2700 sn) Pazartesi EOD döngüsünü ÜÇ kez öldürdü ve aday kararları HİÇ üretilmedi. Döngü asılı
      DEĞİLDİ: 408 sembollük bar süpürmesi + 367 satırlık onarım kuyruğu + kazanç takvimi tazelemesi
      meşru-uzun bir işti. Kusur `scheduler_status.updated`ın yalnız döngü BİTERKEN yazılmasıydı:
      bekçinin okuduğu sinyal "ilerleme" değil "bitiş"ti.

  (2) 403 — state/events.jsonl, 2026-07-29 21:15:12Z → 23:51:08Z: AYNI seans (date=2026-07-30) için
      24 kez `massive_grouped_failed reason="HTTP 403"`, ardışık damgalar arası ~300 sn = tam olarak
      `massive.FAIL_COOLDOWN_S`. 403 bir plan/yetki hükmüdür; aynı anahtarla atılan ikinci istek
      tanımı gereği aynı cevabı alır — yani 24 çağrının 23'ü boşunaydı.

BU DOSYANIN ÇİVİLEDİĞİ ŞEY, DÜZELTMENİN KENDİSİ KADAR ONUN SINIRLARIDIR: nabız YALNIZ ilerleyen
döngünün KENDİ iş parçacığından atar (yoksa bekçi ölü bir zamanlayıcıyı ayakta sanardı) ve kısa
döngüde HİÇ fazladan yazım yapmaz; yetki kapısı YALNIZ 401/403'ü bağlar (429/5xx eskisi gibi
yeniden denenir) ve YALNIZ reddedilen YOLU bağlar (403 tarihe bağlıdır — taze seansın reddi eski
seansın onarımını kapatamaz).

AĞ YOK: httpx her testte mock'lanır; mock'lanmayan çağrı `_izole` bekçisiyle çöker.
"""
import json
import threading

import pandas as pd
import pytest

from meridian import scheduler, secrets, store
from meridian.adapters import data, massive


# ================================================================================ ortak düzenek
class _Saat:
    """Monotonik sahte saat. GERÇEK `time.monotonic` kullanmak, 30 saniyelik kısmayı ölçmek için
    testi 30 saniye BEKLETİRDİ — ve beklemeyle geçen bir test, ölçtüğünü sandığı şeyi ölçmez."""

    def __init__(self):
        self.t = 0.0

    def monotonic(self):
        return self.t

    def ilerlet(self, sn):
        self.t += float(sn)


class _Resp:
    def __init__(self, payload, status=200):
        self._p, self.status_code = payload, status
        self.text = json.dumps(payload)

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx
            raise httpx.HTTPStatusError("err", request=None, response=self)

    def json(self):
        return self._p


@pytest.fixture(autouse=True)
def _izole(sandbox_state, monkeypatch):
    """Kum havuzu + TEMİZ modül-globalleri. Nabız sahipliği ve yetki defteri modül-globalidir;
    sıfırlanmazsa testler SIRA BAĞIMLI olur (bu depoda yaşanmış sınıf — conftest gerekçeleri)."""
    monkeypatch.setattr(scheduler, "_nabiz_sahibi", None)
    monkeypatch.setattr(scheduler, "_nabiz_son", 0.0)
    monkeypatch.setattr(scheduler, "_nabiz_sayac", 0)
    massive.reset_cache()
    massive._CALLS.clear()
    massive._HEALTH.update({"ok": None, "calls": 0, "fails": 0, "last_status": None,
                            "last_error": "", "at": None, "rate_waits": 0, "retries": 0})
    monkeypatch.setattr(massive, "_NO_KEY_LOGGED", False)
    saat_ms = {"t": 0.0}
    monkeypatch.setattr(massive, "_now", lambda: saat_ms["t"])
    monkeypatch.setattr(massive, "_sleep", lambda s: saat_ms.__setitem__("t", saat_ms["t"] + float(s)))

    def _agsiz(*a, **k):
        raise AssertionError("test AĞA çıktı — httpx mock'lanmamış")
    monkeypatch.setattr(massive.httpx, "get", _agsiz)
    secrets.clear_cache()
    yield
    massive.reset_cache()
    massive._CALLS.clear()
    secrets.clear_cache()


def _durum() -> dict:
    return store.read_json(scheduler.STATUS_FILE, {}) or {}


def _saat_kur(monkeypatch) -> _Saat:
    saat = _Saat()
    monkeypatch.setattr(scheduler, "time", saat)
    return saat


# ================================================================ İŞ 1 — NABIZ: sahiplik sınırı
def test_dongu_kosmuyorken_nabiz_hicbir_sey_yazmaz(monkeypatch):
    """EN ÖNEMLİ SINIR. `data.load_many` üzerinden geçen yollar yalnız zamanlayıcı değil: replay
    tohumu, sprint alt süreçleri, havuz işçileri, danışma iş parçacıkları. Bunlardan biri canlı
    durum damgasını tazeleyebilseydi bekçi ÖLÜ bir zamanlayıcıyı ayakta sanardı — düzeltme,
    kapatmak istediği körlüğün daha kötüsünü üretirdi."""
    _saat_kur(monkeypatch)
    assert scheduler._nabiz_sahibi is None
    assert scheduler.nabiz("olmayan_dongu") is False
    assert _durum() == {}, "koşan döngü yokken durum dosyasına YAZILMAMALI"


def test_baska_is_parcacigi_nabiz_atamaz(monkeypatch):
    """Sahiplik SÜREÇ değil İŞ PARÇACIĞI düzeyindedir: döngü ana iş parçacığındayken, aynı süreçte
    koşan bir yan iplik (danışma katmanı, havuz) ilerleme iddia edemez."""
    saat = _saat_kur(monkeypatch)
    scheduler._nabiz_sahiplen()
    saat.ilerlet(scheduler.NABIZ_MIN_ARA_S + 1)
    sonuc = {}

    def _yan():
        sonuc["yazdi"] = scheduler.nabiz("yan_iplik")
    t = threading.Thread(target=_yan)
    t.start()
    t.join(timeout=5)
    scheduler._nabiz_birak()
    assert sonuc["yazdi"] is False
    assert _durum() == {}


def test_dongu_bitince_sahiplik_birakilir(monkeypatch):
    saat = _saat_kur(monkeypatch)
    scheduler._nabiz_sahiplen()
    scheduler._nabiz_birak()
    saat.ilerlet(10_000)
    assert scheduler.nabiz("dongu_sonrasi") is False
    assert _durum() == {}


def test_advance_once_istisnada_bile_sahipligi_birakir(monkeypatch):
    """`finally` sözleşmesi: döngü patlarsa sahiplik ASILI kalırsa, o iş parçacığı bir daha ne
    yaparsa yapsın (HTTP isteği sunmak dahil) canlı damgayı tazelemeye devam ederdi."""
    _saat_kur(monkeypatch)

    def _patla():
        raise RuntimeError("takvim ölçülemedi")
    monkeypatch.setattr(scheduler, "_last_closed_session", _patla)
    monkeypatch.setattr(scheduler.health, "halted", lambda: False)
    with pytest.raises(RuntimeError):
        scheduler.advance_once()
    assert scheduler._nabiz_sahibi is None


# ============================================================== İŞ 1 — NABIZ: kısma ve tazeleme
def test_kisa_dongude_davranis_degismez_fazladan_yazim_yok(monkeypatch):
    """REGRESYON KAPISI: poll'lerin ezici çoğunluğu saniyeler sürer (canlı ölçüm: poll aralığı
    medyan 300 sn, işin kendisi çok daha kısa). Nabız o turlarda TEK bir fazladan yazım bile
    yapmamalı — aksi hâlde 5 dakikada bir koşan bir kadans, disk yazımını sessizce çoğaltırdı."""
    saat = _saat_kur(monkeypatch)
    scheduler._nabiz_sahiplen()
    for _ in range(500):                       # 500 yineleme, ama saat İLERLEMİYOR (kısa iş)
        assert scheduler.nabiz("bar_yukleme") is False
    saat.ilerlet(scheduler.NABIZ_MIN_ARA_S - 0.01)
    assert scheduler.nabiz("bar_yukleme") is False
    scheduler._nabiz_birak()
    assert _durum() == {}


def test_uzun_supurmede_nabiz_mevcut_tick_alanini_tazeler(monkeypatch):
    """Nabız YENİ BİR BİÇİM İCAT ETMEZ: bekçinin okuduğu alanın (`scheduler_status.updated`) ta
    kendisini yazar. Aşama etiketi yalnız teşhis içindir."""
    saat = _saat_kur(monkeypatch)
    scheduler._nabiz_sahiplen()
    saat.ilerlet(scheduler.NABIZ_MIN_ARA_S + 0.01)
    assert scheduler.nabiz("bar_yukleme", 42, 408) is True
    d = _durum()
    scheduler._nabiz_birak()
    assert d.get("updated"), "bekçinin okuduğu alan yazılmalı"
    assert d["nabiz"]["asama"] == "bar_yukleme 42/408"
    assert d["nabiz"]["tur_ici"] == 1


def test_nabiz_persist_dusse_bile_firlatmaz(monkeypatch):
    """Nabız bir TELEMETRİ yazımıdır. Diski dolduran bir makinede döngüyü DÜŞÜRMESİ, düzelttiği
    kusurdan çok daha pahalı olurdu — ama sessiz de kalmaz (YASA 4)."""
    saat = _saat_kur(monkeypatch)
    olaylar = []
    from meridian import obs
    monkeypatch.setattr(obs, "warn", lambda e, **f: olaylar.append(e))

    def _patla(*a, **k):
        raise OSError("disk dolu")
    monkeypatch.setattr(scheduler, "_persist", _patla)
    scheduler._nabiz_sahiplen()
    saat.ilerlet(scheduler.NABIZ_MIN_ARA_S + 1)
    assert scheduler.nabiz("bar_yukleme") is False
    scheduler._nabiz_birak()
    assert "tick_nabzi_yazilamadi" in olaylar


# ================================================== İŞ 1 — NABIZ: gerçek süpürme yollarına bağlı
def _sahte_uzun_supurme(monkeypatch, saat, sn_per_sembol=20.0):
    """Her sembolü `sn_per_sembol` saniye süren bir çekime çevir (canlıdaki FMP tek-tek çekimlerinin
    sahtesi). Bar üretilmez: `load_many` onları 'unavailable' sayar, bizim ölçtüğümüz DÖNGÜNÜN
    KENDİSİDİR, sonucu değil."""
    def _yavas(t, s, e, use_cache=True, polite_delay=0.1):
        saat.ilerlet(sn_per_sembol)
        return pd.DataFrame()
    monkeypatch.setattr(data, "load_bars", _yavas)


def test_sahte_uzun_supurmede_nabiz_en_az_bir_kez_atilir(monkeypatch):
    """UÇTAN UCA: `load_many` GERÇEK üretim yoludur; yalnız saat ve tek-sembol çekimi sahtedir.

    ÖLÇÜLEN ŞEY NABIZ SAYISI DEĞİL, EN BÜYÜK SESSİZLİKTİR: bekçiyi ilgilendiren tek büyüklük
    "damga kaç saniyedir tazelenmedi"dir. Sayıyı çivilemek kısma sabitini dondururdu; boşluğu
    çivilemek SÖZLEŞMEYİ çiviler."""
    saat = _saat_kur(monkeypatch)
    _sahte_uzun_supurme(monkeypatch, saat, sn_per_sembol=20.0)
    damgalar = []
    _orj_persist = scheduler._persist
    monkeypatch.setattr(scheduler, "_persist",
                        lambda: (damgalar.append(saat.t), _orj_persist())[1])
    scheduler._nabiz_sahiplen()
    data.load_many([f"T{i}" for i in range(40)], "2020-01-01", "2026-08-03")
    d = _durum()
    scheduler._nabiz_birak()
    assert d.get("updated"), "uzun süpürme boyunca tick damgası HİÇ tazelenmedi"
    assert d["nabiz"]["asama"].startswith("bar_yukleme")
    # 40 sembol × 20 sn = 800 sn süpürme — bekçinin 2700 sn eşiğinin altında ama sınıfı aynı;
    # canlıdaki 408 sembol aynı oranla 2 saati aşar (ve 2026-08-03'te tam olarak öyle oldu).
    assert saat.t >= 800
    sinirlar = [0.0] + damgalar + [saat.t]
    en_buyuk_bosluk = max(b - a for a, b in zip(sinirlar, sinirlar[1:]))
    # Tavan: bir sembolün süresi + kısma penceresi. Bekçi eşiğinin (2700 sn) çok altında kalması,
    # nabzın kusuru GERÇEKTEN kapattığının ölçüsüdür.
    assert en_buyuk_bosluk <= 20.0 + scheduler.NABIZ_MIN_ARA_S
    assert d["nabiz"]["tur_ici"] == len(damgalar) >= 10


def test_ayni_supurme_dongu_kosmuyorken_sessizdir(monkeypatch):
    """AYNI kod yolu, TEK fark sahiplik: replay/sprint/havuz bu satırlardan geçer ve canlı damgaya
    dokunamaz. Bu testin ikizi olmadan yukarıdaki test, kapıyı değil yalnız kabloyu ölçerdi."""
    saat = _saat_kur(monkeypatch)
    _sahte_uzun_supurme(monkeypatch, saat)
    data.load_many([f"T{i}" for i in range(40)], "2020-01-01", "2026-08-03")
    assert _durum() == {}


def test_kazanc_takvimi_penceresi_gun_basina_nabiz_atar(monkeypatch):
    """(c) precycle'ın uzun adımı: gün başına bir HTTP + nezaket beklemesi."""
    saat = _saat_kur(monkeypatch)
    monkeypatch.setattr(data.time, "sleep", lambda s: None)

    def _yavas_get(url, timeout, attempts=3):
        saat.ilerlet(40.0)
        return _Resp({"data": {"rows": [{"symbol": "AAPL", "time": "time-pre-market"}]}})
    monkeypatch.setattr(data, "_get_json", _yavas_get)
    scheduler._nabiz_sahiplen()
    out = data.nasdaq_earnings_window("2026-08-03", "2026-08-14", polite_delay=0.0)
    d = _durum()
    scheduler._nabiz_birak()
    assert out.get("AAPL"), "üretim davranışı değişmemeli (satırlar yine toplanır)"
    assert d.get("updated") and d["nabiz"]["asama"].startswith("kazanc_takvimi:gun")


def test_onarim_ve_kalibrasyon_dongulerinde_nabiz_var(monkeypatch):
    """(a) onarım/hayalet-tur süpürmesi: `repair_coverage` evren boyu CSV okur ve eksik seansta
    sembol başına CSV YENİDEN YAZAR."""
    saat = _saat_kur(monkeypatch)
    for i in range(30):
        (data._config.BARS / f"t{i}.csv").write_text(
            "date,open,high,low,close,volume\n2026-07-30,1,1,1,1,100\n")

    _orj = pd.read_csv

    def _yavas_csv(*a, **k):
        saat.ilerlet(5.0)
        return _orj(*a, **k)
    monkeypatch.setattr(pd, "read_csv", _yavas_csv)
    monkeypatch.setattr(massive, "snapshot", lambda d: {})
    monkeypatch.setattr(massive, "last_session", lambda back=0: "2026-07-31")
    scheduler._nabiz_sahiplen()
    data.repair_coverage(tickers=[f"T{i}" for i in range(30)], sessions=1)
    d = _durum()
    scheduler._nabiz_birak()
    assert d.get("updated") and d["nabiz"]["asama"].startswith("onarim:")


# ============================================== İŞ 2 — MASSIVE 401/403: gün-içi yetki kapısı
def _anahtar(monkeypatch, val="massive_test_key_1234"):
    monkeypatch.setenv(massive.KEY_NAME, val)
    secrets.clear_cache()


def _http(monkeypatch, karar):
    """`karar(url) -> _Resp`. Çağrılan URL'leri kaydeder — ölçtüğümüz şey AĞA KAÇ KEZ ÇIKILDIĞIdır."""
    cagrilar = []

    def fake_get(url, params=None, headers=None, timeout=None):
        cagrilar.append({"url": url, "timeout": timeout})
        return karar(url)
    monkeypatch.setattr(massive.httpx, "get", fake_get)
    return cagrilar


def test_403_ayni_gun_icinde_ikinci_kez_sorulmaz(monkeypatch):
    """KUSURUN KENDİSİ: eski hâlde ikinci çağrı ağa çıkar ve aynı 403'ü alırdı (canlıda 24 kez)."""
    _anahtar(monkeypatch)
    cagrilar = _http(monkeypatch, lambda u: _Resp({"error": "not entitled"}, status=403))
    assert massive.grouped_daily("2026-07-30") is None
    assert len(cagrilar) == 1
    assert massive.grouped_daily("2026-07-30") is None
    assert len(cagrilar) == 1, "403 alan seans AYNI GÜN içinde YENİDEN sorulmamalı"
    assert massive.grouped_daily("2026-07-30") is None
    assert len(cagrilar) == 1


def test_403_yalnizca_reddedilen_yolu_baglar_eski_seans_hala_sorulur(monkeypatch):
    """403 bu sağlayıcıda TARİHE bağlıdır (ücretsiz katman taze seansları vermez). Kapıyı uç
    ailesine kilitlemek, tek bir taze seansın reddi yüzünden ONARIM GEÇİDİNİ de kapatırdı —
    yani gürültü düzeltmesi çalışan bir yolu öldürürdü."""
    _anahtar(monkeypatch)
    cagrilar = _http(monkeypatch, lambda u: (_Resp({}, status=403) if "2026-07-30" in u
                                             else _Resp({"results": [{"T": "AAPL", "c": 1.0}]})))
    assert massive.grouped_daily("2026-07-30") is None
    assert massive.grouped_daily("2026-07-30") is None          # kapı: ağa çıkmaz
    assert massive.grouped_daily("2026-07-24") == [{"T": "AAPL", "c": 1.0}]
    assert [c["url"].rsplit("/", 1)[-1] for c in cagrilar] == ["2026-07-30", "2026-07-24"]


def test_403_gerekceli_olay_gunde_bir_kez_geri_kalan_tekillesir(monkeypatch):
    """YASA 4 tekilleştirmesi: reddin gerekçesi TAM olarak bir kez yazılır (uç ailesi başına, gün
    başına). Eski hâl aynı reddi çağrı başına basıyordu — 24 satır, hepsi aynı cümle."""
    _anahtar(monkeypatch)
    _http(monkeypatch, lambda u: _Resp({}, status=403))
    olaylar = []
    from meridian import obs
    monkeypatch.setattr(obs, "warn", lambda e, **f: olaylar.append((e, f)))
    for _ in range(5):
        massive.grouped_daily("2026-07-30")
    massive.grouped_daily("2026-07-29")          # AYNI aile, BAŞKA yol → ikinci gerekçe satırı YOK
    adlar = [e for e, _ in olaylar]
    assert adlar.count("massive_yetki_reddi") == 1
    # `massive_grouped_failed` yalnız GERÇEKTEN atılan istekler için (iki farklı tarih = iki istek);
    # kapının reddettiği çağrılar bu satırı TEKRARLAMAZ.
    assert adlar.count("massive_grouped_failed") == 2
    gerekce = next(f for e, f in olaylar if e == "massive_yetki_reddi")
    assert gerekce["status"] == 403 and len(gerekce["detail"]) >= 20


def test_429_ve_5xx_eskisi_gibi_yeniden_denenir(monkeypatch):
    """KAPI YALNIZ 401/403'Ü BAĞLAR. 429 kota/hız, 5xx sağlayıcı arızasıdır — ikisi de GEÇİCİdir ve
    geri çekilmeyle çözülebilir. Bunları da bağlasaydık, bir dakikalık bir kota darboğazı tüm günü
    karartırdı."""
    _anahtar(monkeypatch)
    for kod in (429, 503):
        massive.reset_cache()
        cagrilar = _http(monkeypatch, lambda u, k=kod: _Resp({}, status=k))
        assert massive.grouped_daily("2026-07-30") is None
        assert len(cagrilar) == massive.MAX_RETRY
        n0 = len(cagrilar)
        assert massive.grouped_daily("2026-07-30") is None
        assert len(cagrilar) == n0 + massive.MAX_RETRY, f"HTTP {kod} gün-içi kapıya TAKILMAMALI"


def test_403_sonrasi_bar_zinciri_yedege_duser(monkeypatch):
    """Kapının AMACI budur: massive susar, zincir (fmp → cboe → nasdaq → aynı-akşam IEX bacağı)
    aynen sürer. Canlıda 2026-08-03'te 252/253 bar IEX'ten geldi — davranış BURADA çivileniyor."""
    _anahtar(monkeypatch)
    _http(monkeypatch, lambda u: _Resp({}, status=403))
    monkeypatch.setattr(massive, "write_enabled", lambda: True)
    monkeypatch.setattr(massive, "covers", lambda s: False)
    monkeypatch.setattr(data, "_fetch_fmp", lambda t, s, e, to: pd.DataFrame())
    # 2026-07-06'dan itibaren 30 iş günü: aradaki TEK tatil (4 Temmuz, Cuma 07-03 gözlemli) dışarıda
    # kalır — hayalet-seans kapısı satır düşürmesin diye (o kapı bu testin konusu değil).
    idx = pd.bdate_range("2026-07-06", periods=30)
    cboe = pd.DataFrame({"date": idx, "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0,
                         "volume": 100.0})
    monkeypatch.setattr(data, "_fetch_cboe", lambda t, to: cboe)
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda t, s, e, to: pd.DataFrame())
    df = data.fetch("AAPL", "2026-07-06", str(idx[-1].date()), incremental_ok=True)
    assert len(df) == 30 and data._LAST_SOURCE.get("AAPL") == "cboe"


def test_ping_kapiyi_atlar_ve_basarida_defteri_siler(monkeypatch):
    """Operatörün elle yolu. "Test et" düğmesi ÖLÇÜM ister; kapıdan cevap vermek, istek atmadan
    "ölçtüm" demek olurdu — ve tam da planı DÜZELTTİKTEN sonra basılan düğme düzelmeyi göremezdi."""
    _anahtar(monkeypatch)
    durum = {"kod": 403}
    cagrilar = _http(monkeypatch, lambda u: (_Resp({}, status=403) if durum["kod"] == 403
                                             else _Resp({"results": [{"ticker": "AAPL"}]})))
    assert massive.grouped_daily("2026-07-30") is None
    assert massive.grouped_daily("2026-07-30") is None
    n0 = len(cagrilar)
    assert massive.ping() == {"ok": False, "detail": "anahtar geçersiz/yetkisiz"}
    assert len(cagrilar) == n0 + 1, "elle ölçüm kapıya TAKILMAMALI (gerçekten istek atmalı)"
    durum["kod"] = 200
    assert massive.ping()["ok"] is True
    assert massive._yetki_reddi_var("/v2/aggs/grouped/locale/us/market/stocks/2026-07-30") is None
    assert massive.grouped_daily("2026-07-30") is not None      # defter silindi → yol yeniden açık


def test_yeni_seans_kovalamasi_kapiyi_bir_kez_yeniden_olcer(monkeypatch):
    """`reset_cache()` üretimde `scheduler.advance_once`ın "yeni seans kovalaması başlıyor" dalından
    (seans başına bir kez) çağrılır — "günde bir kez dene" yasasının seans sınırındaki ikizi."""
    _anahtar(monkeypatch)
    cagrilar = _http(monkeypatch, lambda u: _Resp({}, status=403))
    massive.grouped_daily("2026-07-30")
    massive.grouped_daily("2026-07-30")
    assert len(cagrilar) == 1
    massive.reset_cache()
    massive.grouped_daily("2026-07-30")
    assert len(cagrilar) == 2


def test_kapi_atilmamis_istegi_basarisiz_cagri_diye_saymaz(monkeypatch):
    """UYDURMA YASAĞI: ağa çıkmamış bir istek `calls`/`fails` sayaçlarına giremez — yoksa pano
    hata oranını hiç yapılmamış çağrılarla hesaplardı. İzin kaldığı yer `last_error` (dış okuyucusu
    var: api._saglayici_satiri → pano 'son_hata')."""
    _anahtar(monkeypatch)
    _http(monkeypatch, lambda u: _Resp({}, status=403))
    massive.grouped_daily("2026-07-30")
    h0 = massive.health()
    massive.grouped_daily("2026-07-30")
    massive.grouped_daily("2026-07-30")
    h1 = massive.health()
    assert (h1["calls"], h1["fails"]) == (h0["calls"], h0["fails"])
    assert "yetki reddi" in h1["last_error"] and "2026-07-30" not in h1["last_error"]


def test_her_massive_istegi_timeout_tasir(monkeypatch):
    """İŞ 2'nin ikinci maddesi: zaman aşımsız bir HTTP çağrısı, 403 gürültüsünden çok daha sinsi bir
    asılma kaynağıdır (bekçi onu HAKLI olarak öldürürdü ama sebep hiçbir yerde yazmazdı)."""
    _anahtar(monkeypatch)
    cagrilar = _http(monkeypatch, lambda u: _Resp({"results": []}))
    massive.grouped_daily("2026-07-30")
    massive.custom_bars("AAPL", "2026-07-01", "2026-07-30")
    massive.all_tickers()
    massive.ping()
    assert cagrilar and all(c["timeout"] for c in cagrilar)

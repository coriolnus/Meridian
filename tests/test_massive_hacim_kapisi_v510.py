"""v510 — TSK-194: SAĞLAYICI UYUM KAPISININ HACİM EKSENİ.

NUMARA SEÇİMİ (iki adımda, ve ikincisi bir ders): bu worktree'de `ls tests/ | grep -E 'v50[0-9]'`
alınmış en büyük numarayı v508 gösterdi (`test_ag_kapisi_raporu_v508.py`), yani v509 BOŞ görünüyordu.
BOŞ DEĞİLDİ: v509'u aynı turda PARALEL bir worktree aldı (`test_ansible_a0_docker_grubu_v509.py`,
main'e inecek) ve ayrı bir çalışma ağacından bu GÖRÜNMEZ — `ls` yalnız kendi ağacını ölçer.
Numara bu depoda KİMLİKTİR: çakışma merge'de iki dosyayı karşı karşıya getirir ve az-çapalı taraf
taşınır. Rol-1 uyardı, dosya v510'a alındı (2026-09-16).

KÖR NOKTA (Rol-1 ölçtü, TSK-192'nin kök nedeni):
  * Yazım kapısı `massive.write_enabled` → `massive.verify_state` → `state/massive_verify.json`
    hükmünü okuyor; o hükmü `massive.verify` yazıyor.
  * `verify` TEK EKSEN ölçüyordu: FİYAT. Kıyas yalnız kapanış üzerindendi (`massive.compare` +
    `massive._tol_for`), hacim hiçbir kıyasa girmiyordu.
  * Sonuç: sağlayıcının KESİRLİ hacmi kapıdan "uyumlu" hükmüyle geçti ve 2026-07-29'da canlı bar
    defterine düştü (`state/bars/ea.csv` → `3569440.107552`). TSK-192 YAZIM tarafını kapattı
    (`data._hacim_tam_sayi` + tur sonu duyuru), ama KAPI hâlâ kördü: hacim ekseninde başka bir
    sapma (ölçek, birim, sıfır, eksik alan) da aynı sessizlikle geçerdi.

BU DOSYA NE ÇİVİLER (brief'in K1–K5'i + üç ek sözleşme):
  K1 — kesirli hacimli sağlayıcı yanıtı kapıyı KAPATIR (`VERIFY_VOL_FRAC_MAX` şartı).
  K2 — hacmi ölçek olarak sapmış (×1000) yanıt kapıyı KAPATIR (`VERIFY_VOL_MAX_MISMATCH` şartı).
  K3 — fiyatı ve hacmi uyumlu yanıt YANLIŞ POZİTİF üretmez: kapı açık kalır.
  K4 — hüküm yapısında DÜŞÜREN EKSEN okunabilir (`failed_axes` + `axes`), ve panoya çıkan iki
       yüzeyde (`massive.verify_basis`, `massive.status`) de görünür.
  K5 — hacim alanı EKSİK gelen yanıt "ölçülemedi"dir; sessizce "uyumlu" SAYILMAZ.
  E1 — ÖLÇÜ BİRİMİ AYRIMI: hacim kıyası fiyatın yuvarlama payından (`massive._tol_for` /
       `massive.ROUND_EPS`) GEÇMEZ; eşikler ayrı sabitlerdir ve hüküm dosyasında BEYANLIDIR.
  E2 — BEDEL: ikinci eksen ikinci İSTEK demek değildir — sembol başına hâlâ TEK çağrı
       (`massive._ham_barlar` tur memosu), ve memo tur dışına taşmaz.
  E3 — TABAN BEYANI: `massive.BASELINE` hacmin yalnız ÖLÇEĞİNİ kapsar, TAM SAYI şartını kapsamaz;
       kapsanmayan eksen için taban değeri UYDURULMAZ, yokluğu adıyla görünür.

AĞ YOK: `_izole` bekçisi mock'lanmamış her `httpx` çağrısını düşürür; `sandbox_state` sırları ve
`state/` yazımını tmp dizine yönlendirir. İkisi de v118'in aynı gerekçesiyle burada.
"""
import ast
import datetime as dt
import inspect
import textwrap

import pandas as pd
import pytest

from meridian import secrets, store
from meridian.adapters import data, massive


class _Resp:
    def __init__(self, payload, status=200):
        self._p, self.status_code = payload, status

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx
            raise httpx.HTTPStatusError("err", request=None, response=self)

    def json(self):
        return self._p


def _ms(gun: str) -> int:
    """Seans KAPANIŞININ unix ms'i (20:00Z = 16:00 ET yazın). Sözleşme v118'de canlı ölçülmüştü;
    burada ondan TÜRETİLİR, yeniden varsayılmaz."""
    return int(dt.datetime.fromisoformat(f"{gun}T20:00:00+00:00").timestamp() * 1000)


@pytest.fixture(autouse=True)
def _izole(sandbox_state, monkeypatch):
    """Temiz modül-globalleri + sahte saat + AĞ BEKÇİSİ (v118 ile aynı gerekçe: bu adaptörün durumu
    modül-globalidir ve sıfırlanmazsa testler sıra bağımlı olur; canlı `state/secrets.json`da
    GERÇEK bir MASSIVE_API_KEY var, yani "anahtar yok" güvencesi YOK)."""
    massive.reset_cache()
    massive._CALLS.clear()
    massive._HEALTH.update({"ok": None, "calls": 0, "fails": 0, "last_status": None,
                            "last_error": "", "at": None, "rate_waits": 0, "retries": 0})
    monkeypatch.setattr(massive, "_NO_KEY_LOGGED", False)
    saat = {"t": 0.0}
    monkeypatch.setattr(massive, "_now", lambda: saat["t"])
    monkeypatch.setattr(massive, "_sleep", lambda s: saat.__setitem__("t", saat["t"] + float(s)))

    def _agsiz(*a, **k):
        raise AssertionError("test AĞA çıktı — httpx mock'lanmamış")
    monkeypatch.setattr(massive.httpx, "get", _agsiz)
    secrets.clear_cache()
    yield
    massive.reset_cache()
    massive._CALLS.clear()
    secrets.clear_cache()


def _anahtar(monkeypatch, val="massive_test_key_1234"):
    monkeypatch.setenv(massive.KEY_NAME, val)
    secrets.clear_cache()


# ---------------------------------------------------------------- sahte sağlayıcı + yerel önbellek
GUN_SAYISI = 60          # `VERIFY_MIN_SAMPLES` (50) üstünde kalsın: örneklem yetersizliği hükmü
                         # eksen hükmünün ÖNÜNE geçerse çiviler yanlış sebeple yeşil olurdu
PENCERE_GUN = 200        # `verify(days=...)`: 60 İŞ günü ~84 takvim günü geriye gider


def _is_gunleri(n: int = GUN_SAYISI) -> list[str]:
    """Bugünle biten son `n` iş günü (ISO). `verify` penceresini BUGÜNDEN türettiği için sabit
    tarih yazmak çiviyi bir gün sessizce pencere dışına düşürürdü."""
    return [str(d.date()) for d in pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)]


def _satir(gun: str, close: float = 100.0, volume=1_000_000.0) -> dict:
    """Ham Massive `results[]` satırı. `volume=None` → `v` alanı HİÇ YOK (K5'in sahtesi)."""
    r = {"o": close, "h": close + 1.0, "l": close - 1.0, "c": close, "t": _ms(gun)}
    if volume is not None:
        r["v"] = volume
    return r


def _mock_saglayici(monkeypatch, satirlar: list[dict], cap: dict | None = None):
    """`custom_bars` ucunu sahteler. GERÇEK AĞ ÇAĞRISI YOK — `_izole` bekçisinin üstüne yazar."""
    def fake_get(url, params=None, headers=None, timeout=None):
        if cap is not None:
            cap["n"] = cap.get("n", 0) + 1
            cap.setdefault("urls", []).append(url)
        return _Resp({"results": satirlar})
    monkeypatch.setattr(massive.httpx, "get", fake_get)


def _cache_yaz(ticker: str, gunler: list[str], close: float = 100.0, volume: float = 1_000_000.0):
    """Yerel bar önbelleği (kıyasın REFERANS tarafı). Hacim TAM SAYI yazılır — TSK-192'den beri
    `data._write_bars` zaten bunu zorluyor, yani referans tarafı sözleşmeye uygun."""
    df = pd.DataFrame({"date": pd.to_datetime(gunler), "open": close, "high": close + 1.0,
                       "low": close - 1.0, "close": close, "volume": volume})
    data._write_bars(df, data._cache_path(ticker))


def _kur(monkeypatch, *, saglayici_close=100.0, saglayici_volume=1_000_000.0,
         kesirli_gun: int | None = None, cap=None) -> list[str]:
    """AAPL için yerel önbellek + sahte sağlayıcı yanıtı kurar; kullanılan günleri döndürür.
    `kesirli_gun` verilirse O GÜNÜN sağlayıcı hacmine kesir eklenir (TSK-192'nin canlı imzası)."""
    gunler = _is_gunleri()
    _cache_yaz("AAPL", gunler)
    satirlar = []
    for i, g in enumerate(gunler):
        hacim = saglayici_volume
        if kesirli_gun is not None and i == kesirli_gun and hacim is not None:
            hacim = hacim + 0.107552        # canlı vakadaki kesir (state/bars/ea.csv, 2026-07-29)
        satirlar.append(_satir(g, close=saglayici_close, volume=hacim))
    _mock_saglayici(monkeypatch, satirlar, cap)
    return gunler


# ====================================================================== K1 — TAM SAYI ŞARTI
def test_K1_kesirli_hacim_kapiyi_KAPATIR(monkeypatch):
    """TSK-192'NİN TAM SINIFI. Kesir BÜYÜKLÜK olarak görünmez (1.000.000 → 1.000.000,107552; bağıl
    fark ~1e-7, her toleransın altında) — bu yüzden tam sayı şartı BAĞIL FARKTAN AYRI bir şarttır.
    Kapı yalnız bağıl farka baksaydı bu yanıt yine "uyumlu" derdi; kör nokta tam buydu."""
    _anahtar(monkeypatch)
    _kur(monkeypatch, kesirli_gun=3)
    out = massive.verify(symbols=["AAPL"], days=PENCERE_GUN)

    assert out["axes"]["fiyat"]["verdict"] == "uyumlu"        # FİYAT tarafı temiz…
    assert out["axes"]["hacim"]["verdict"] == "uyumsuz"       # …düşüren HACİM
    assert out["verdict"] == "uyumsuz" and out["failed_axes"] == ["hacim"]
    assert out["volume_fractional"] == 1 and out["volume_provider_bars"] == GUN_SAYISI
    assert "1000000.107552" in str(out["volume_fractional_example"])
    # kesir bağıl farkta GÖRÜNMÜYOR — şartın ayrı olmasının kanıtı
    assert out["volume_mismatches"] == 0
    assert massive.write_enabled() is False                   # yazım kapalı: zincir yedeklere döner
    assert store.read_json(massive.VERIFY_FILE, {})["failed_axes"] == ["hacim"]


def test_K1b_kesirli_hacim_ADIYLA_duyurulur_YASA4(monkeypatch):
    """YASA 4: düşüş sessiz olamaz. Fiyat ekseni tek başına ölçülürken bu sınıfın hiçbir olayı
    yoktu — kesir kapıdan geçti ve kimse bir şey görmedi."""
    _anahtar(monkeypatch)
    _kur(monkeypatch, kesirli_gun=0)
    olaylar = []
    import meridian.obs as obs
    monkeypatch.setattr(obs, "warn", lambda e, **f: olaylar.append((e, f)))
    massive.verify(symbols=["AAPL"], days=PENCERE_GUN)
    adlar = [e for e, _ in olaylar]
    assert "massive_hacim_uyumsuz" in adlar
    alan = dict(olaylar[adlar.index("massive_hacim_uyumsuz")][1])
    assert alan["fractional"] == 1 and alan["provider_bars"] == GUN_SAYISI
    assert alan["thresholds"]["vol_frac_max"] == massive.VERIFY_VOL_FRAC_MAX
    assert "KESİRLİ" in alan["reason"]


def test_K1c_uyumlu_turda_hacim_olayi_BASILMAZ(monkeypatch):
    """Bedel yasasının diğer yüzü: yeni olay her turda ötmemeli, yoksa gürültü sinyali gömer."""
    _anahtar(monkeypatch)
    _kur(monkeypatch)
    olaylar = []
    import meridian.obs as obs
    monkeypatch.setattr(obs, "warn", lambda e, **f: olaylar.append(e))
    massive.verify(symbols=["AAPL"], days=PENCERE_GUN)
    assert "massive_hacim_uyumsuz" not in olaylar


# ====================================================================== K2 — ÖLÇEK SAPMASI
def test_K2_hacim_olcegi_1000_kat_sapinca_kapi_KAPANIR(monkeypatch):
    """Birim/ölçek kırılması (lot↔adet, bin↔bir): fiyat ekseni bunu GÖRMEZ, çünkü kapanışlar aynı
    kalır. Kapının ikinci hacim şartı tam bu sınıf içindir."""
    _anahtar(monkeypatch)
    _kur(monkeypatch, saglayici_volume=1_000_000_000.0)       # ×1000, ama TAM SAYI
    out = massive.verify(symbols=["AAPL"], days=PENCERE_GUN)

    assert out["axes"]["fiyat"]["verdict"] == "uyumlu"
    assert out["axes"]["hacim"]["verdict"] == "uyumsuz"
    assert out["volume_fractional"] == 0                      # tam sayı şartı GEÇTİ…
    assert out["volume_mismatch_pct"] == 1.0                  # …düşüren BAĞIL FARK
    assert out["verdict"] == "uyumsuz" and out["failed_axes"] == ["hacim"]
    assert massive.write_enabled() is False


# ====================================================================== K3 — YANLIŞ POZİTİF YOK
def test_K3_uyumlu_fiyat_ve_hacim_kapiyi_ACIK_BIRAKIR(monkeypatch):
    """Yeni eksen çalışan bir kolu kapatmamalı: aynı kapanış + aynı TAM SAYI hacim = "uyumlu"."""
    _anahtar(monkeypatch)
    _kur(monkeypatch)
    out = massive.verify(symbols=["AAPL"], days=PENCERE_GUN)

    assert out["axes"]["fiyat"]["verdict"] == "uyumlu"
    assert out["axes"]["hacim"]["verdict"] == "uyumlu"
    assert out["verdict"] == "uyumlu" and out["failed_axes"] == []
    assert out["volume_samples"] == GUN_SAYISI and out["volume_mismatches"] == 0
    assert out["volume_fractional"] == 0 and out["volume_unmeasured"] == 0
    assert massive.write_enabled() is True and massive.mode() == "yazim"


# ====================================================================== K4 — DÜŞÜREN EKSEN OKUNUR
@pytest.mark.parametrize("close,volume,bekleyen", [
    (150.0, 1_000_000.0, ["fiyat"]),                 # yalnız fiyat ölçeği sapmış
    (100.0, 1_000_000_000.0, ["hacim"]),             # yalnız hacim ölçeği sapmış
    (150.0, 1_000_000_000.0, ["fiyat", "hacim"]),    # ikisi birden
])
def test_K4_hukum_yapisinda_DUSUREN_EKSEN_okunabilir(monkeypatch, close, volume, bekleyen):
    """"uyumsuz" tek başına tanı koydurmaz: operatör fiyatın mı hacmin mi düştüğünü TAHMİN
    ETMEK ZORUNDA KALMAMALI. Eksen hükümleri ayrı ayrı yazılır, düşürenler adıyla listelenir."""
    _anahtar(monkeypatch)
    _kur(monkeypatch, saglayici_close=close, saglayici_volume=volume)
    out = massive.verify(symbols=["AAPL"], days=PENCERE_GUN)

    assert out["verdict"] == "uyumsuz"
    assert out["failed_axes"] == bekleyen
    for ad in ("fiyat", "hacim"):
        bekleniyor = "uyumsuz" if ad in bekleyen else "uyumlu"
        assert out["axes"][ad]["verdict"] == bekleniyor
        assert len(out["axes"][ad]["reason"]) >= 20          # gerekçesiz hüküm tanı koydurmaz
    for ad in bekleyen:                                      # birleşik gerekçe ekseni ADIYLA taşır
        assert ad.upper() in out["reason"]
    # diskteki hüküm + panoya çıkan iki yüzey aynı ekseni gösterir (YASA 6: alanın okuyucusu var)
    assert store.read_json(massive.VERIFY_FILE, {})["failed_axes"] == bekleyen
    assert massive.verify_basis()["failed_axes"] == bekleyen
    assert massive.status()["verify"]["failed_axes"] == bekleyen


# ====================================================================== K5 — EKSİK ALAN
def test_K5_hacim_alani_EKSIK_gelince_OLCULEMEDI_der(monkeypatch):
    """"Ölçemedim" ile "uyumlu" AYNI ŞEY DEĞİL (uydurma yasağı). Sağlayıcı `v` alanını hiç
    vermezse hacim ekseni ÖLÇÜLEMEZ: bu bir çürütme değildir (kapı tabana döner) ama sessiz bir
    ONAY da değildir — hüküm bunu adıyla söyler."""
    _anahtar(monkeypatch)
    _kur(monkeypatch, saglayici_volume=None)                  # `v` alanı YOK
    out = massive.verify(symbols=["AAPL"], days=PENCERE_GUN)

    assert out["axes"]["fiyat"]["verdict"] == "uyumlu"
    assert out["axes"]["hacim"]["verdict"] == "olculemedi"
    assert out["volume_provider_bars"] == 0
    assert out["volume_unmeasured"] == GUN_SAYISI
    assert out["verdict"] == "olculemedi"                     # SESSİZCE "uyumlu" OLMADI
    assert out["failed_axes"] == []                           # …ama çürütme de değil
    assert massive.write_enabled() is True                    # kapı tabana döner (davranış korunur)


def test_K5b_sifir_hacim_ile_okunamayan_hacim_AYNI_SEY_DEGIL():
    """Sıfır bir ÖLÇÜMDÜR ("o gün işlem yok"), eksik alan ölçümsüzlüktür. `compare_hacim` ikisini
    ayrı kovalarda sayar; aynı kovaya koymak, hiç ölçmediğimiz barları "mutabık" diye sayardı."""
    h = massive.compare_hacim({"2026-09-01": 0.0, "2026-09-02": 0.0},
                              {"2026-09-01": 0.0, "2026-09-02": None})
    assert h["provider_bars"] == 1 and h["unmeasured"] == 1
    assert h["samples"] == 1 and h["mismatches"] == 0         # 0↔0 mutabık
    dolu = massive.compare_hacim({"2026-09-01": 0.0}, {"2026-09-01": 5_000.0})
    assert dolu["samples"] == 1 and dolu["mismatches"] == 1   # yerel sıfır, sağlayıcı dolu → SAPMA


# ====================================================================== E1 — ÖLÇÜ BİRİMİ AYRIMI
def test_E1_hacim_kiyasi_FIYATIN_YUVARLAMA_PAYINDAN_gecmez():
    """ÖLÇÜ BİRİMİ TUZAĞI. Fiyat toleransı bara özgü genişler (`massive._tol_for`, `ROUND_EPS` =
    yarım cent) çünkü CSV kapanışı yuvarlanmış olabilir. Hacimde yuvarlama payı ANLAMSIZDIR: hacim
    bir SAYIMdır. İki ekseni aynı sabite bağlamak, fiyat için doğru olan payı hacme taşırdı."""
    # KOD taranır, DÜZYAZI DEĞİL: docstring ve yorumlar `_tol_for`dan neden geçilmediğini ANLATIR;
    # dizge araması onları da yakalasaydı çivi kendi gerekçesine takılırdı (`ast.unparse` gövdeyi
    # yorumsuz/docstring'siz verir).
    agac = ast.parse(textwrap.dedent(inspect.getsource(massive.compare_hacim)))
    fn = agac.body[0]
    if ast.get_docstring(fn) is not None:
        fn.body = fn.body[1:]
    kod = ast.unparse(fn)
    assert "_tol_for" not in kod and "ROUND_EPS" not in kod
    assert massive.VERIFY_VOL_TOL != massive.VERIFY_TOL
    assert massive.VERIFY_VOL_MAX_MISMATCH != massive.VERIFY_MAX_MISMATCH
    assert massive.VERIFY_VOL_FRAC_MAX == 0.0                 # "biraz kesirli" diye bir şey yok


def test_E1b_esikler_HUKUM_DOSYASINDA_beyanlidir(monkeypatch):
    """Eşik koda gömülü kalırsa hükmü okuyan kişi HANGİ eşikle düştüğünü bilemez; ölçüm dosyası
    kendi eşiklerini taşır (kart disiplininin kod tarafı)."""
    _anahtar(monkeypatch)
    _kur(monkeypatch)
    out = massive.verify(symbols=["AAPL"], days=PENCERE_GUN)
    esik = out["thresholds"]
    assert esik["vol_tol"] == massive.VERIFY_VOL_TOL
    assert esik["vol_frac_max"] == massive.VERIFY_VOL_FRAC_MAX
    assert esik["vol_max_mismatch"] == massive.VERIFY_VOL_MAX_MISMATCH
    assert esik["max_mismatch"] == massive.VERIFY_MAX_MISMATCH       # fiyat eşiği YERİNDE kaldı


# ====================================================================== E2 — BEDEL: TEK İSTEK
def test_E2_ikinci_eksen_IKINCI_ISTEK_DEGIL(monkeypatch):
    """BEDEL YASASI. Hacim eksenini ayrı bir çekimle ölçmek sembol başına ikinci bir sağlayıcı
    isteği demekti — ücretsiz katman 5 istek/dk ve bu modülün VARLIK SEBEBİ kota kurtarmak.
    İki eksen AYNI barlardan türer: sembol başına TEK çağrı."""
    _anahtar(monkeypatch)
    cap = {}
    _kur(monkeypatch, cap=cap)
    massive.verify(symbols=["AAPL"], days=PENCERE_GUN)
    assert cap["n"] == 1


def test_E2b_tur_memosu_tur_DISINA_tasmaz(monkeypatch):
    """Memo bir ÖNBELLEK DEĞİL: iki eksenin aynı barları görmesi için var. Tur dışına taşısaydı
    bir sonraki `--dogrula` bayat barlarla ölçer ve bunu kimse göremezdi."""
    _anahtar(monkeypatch)
    _kur(monkeypatch)
    massive.verify(symbols=["AAPL"], days=PENCERE_GUN)
    assert massive._HAM_MEMO == {}
    massive._HAM_MEMO[("X", "a", "b")] = []
    massive.reset_cache()
    assert massive._HAM_MEMO == {}


# ====================================================================== E3 — TABAN BEYANI
def test_E3_taban_HACIM_TAM_SAYI_eksenini_kapsamadigini_BEYAN_EDER(monkeypatch):
    """Taban ölçümü (`massive.BASELINE`) hacmi ÖLÇEK olarak ölçmüştü (medyan oran 1.000), tam sayı
    olup olmadığını HİÇ SORMAMIŞTI — ve sormadığı ölçülebiliyor: TSK-192'nin kesirli hacmi tam bu
    tabanın gününde canlı defterdeydi. Kapsanmayan eksen için taban değeri UYDURULMAZ; yokluğu
    adıyla görünür, yoksa "taban uyumlu dedi" cümlesi ölçülmemiş bir ekseni de onaylar."""
    _anahtar(monkeypatch)
    vc = massive.BASELINE["volume_check"]
    assert vc["integrality_measured"] is False and vc["axis"] == "olcek"
    assert "TAM SAYI" in vc["note"]
    b = massive.verify_basis()
    assert b["basis"] == "rol1_taban"
    assert b["uncovered_axes"] == ["hacim_tam_sayi"]
    assert "hacim_tam_sayi" not in b["covers_axes"]
    # TABAN İÇİN SAYI UYDURULMAMIŞ: tam sayı ekseninin taban oranı diye bir alan YOKTUR
    assert "fractional_pct" not in vc and "fractional" not in vc

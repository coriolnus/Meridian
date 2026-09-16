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

TUR 2 — EKSEN İKİYE AYRILDI (Rol-1 kararı 2026-09-16; tur 1'in bildirdiği concern kabul edildi):
  Tur 1 tam sayı şartını KAPATMA ekseni yaptı (`VERIFY_VOL_FRAC_MAX = 0.0`, tek kesirli bar kapıyı
  kapatır). Bunun canlı sonucu ölçüldü ve kabul edilemezdi: sağlayıcının kesirli oranı YÜKSEK
  (canlı anlık görüntüde 12.404 sembolün 11.085'i, TSK-192 ölçümü) ve haftalık kol `verify`i
  OTOMATİK koşuyor — yani yazım modu kendiliğinden ve sürekli kapanır, bar zinciri sembol-BAŞINA
  yedeklere döner ve ücretsiz kota evren büyüklüğünün ALTINDADIR (FMP 250 çağrı/gün ↔ 251 sembol).
  Karar, ÜÇ ÖLÇÜME dayanıyor: (1) TSK-192 yazım tarafını kapattı ve canlıda koşuyor — kesirli hacim
  artık bütünlük değil KAYNAK KALİTESİ sorunu; (2) kapatmanın bedeli ölçülmüş kota yağmuru;
  (3) ölçek/birim sapması AYRI bir sınıftır — hacim R'sine, likidite kapılarına ve RVOL'a girer.
  Sonuç: TAM SAYI = ALARM ekseni (duyurur, KAPATMAZ) · ÖLÇEK = KAPATMA ekseni (tur 1 davranışı).
  EŞİK DEĞERLERİ DEĞİŞMEDİ; değişen şey her eşiğin YETKİSİ.

BU DOSYA NE ÇİVİLER (brief'in K1–K5'i + üç ek sözleşme + tur 2'nin K6–K8'i):
  K1 — [MEZAR TAŞI, tur 2'de TERS ÇEVRİLDİ] kesirli hacim kapıyı artık KAPATMAZ. Çivi silinmedi,
       çünkü silinen bir çivi geri dönen bir davranıştır: ters hüküm burada ADIYLA duruyor.
  K2 — hacmi ölçek olarak sapmış (×1000) yanıt kapıyı KAPATIR (`VERIFY_VOL_MAX_MISMATCH` şartı).
  K3 — fiyatı ve hacmi uyumlu yanıt YANLIŞ POZİTİF üretmez: kapı açık kalır.
  K4 — hüküm yapısında DÜŞÜREN EKSEN okunabilir (`failed_axes` + `axes`), ve panoya çıkan iki
       yüzeyde (`massive.verify_basis`, `massive.status`) de görünür.
  K5 — hacim alanı EKSİK gelen yanıt "ölçülemedi"dir; sessizce "uyumlu" SAYILMAZ.
  K6 — ALARM EKSENİ: yalnız kesirli hacim (ölçek uyumlu) → hüküm "uyumlu", yazım AÇIK, AMA ihlal
       olayı basılır ve hükmün YAPISINDA görünür (`alarm_axes`/`alarms`/`reason` + pano yüzeyleri).
  K7 — KAPATMA EKSENİ: ölçek sapması → hüküm "uyumsuz", yazım KAPALI (tur 1 davranışı korunur),
       ve tam sayı ekseni bu kapanışa KATKI VERMEZ.
  K8 — İKİSİ BİRDEN: kapatma ekseni baskın (hüküm "uyumsuz") ama İKİ eksen de ayrı ayrı okunur.
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


# ================================================== K1 — MEZAR TAŞI: TAM SAYI ŞARTI KAPATMIYOR
def test_K1_MEZAR_TASI_kesirli_hacim_kapiyi_ARTIK_KAPATMAZ(monkeypatch):
    """TERS ÇEVRİLMİŞ HÜKÜM (tur 1 → tur 2). Bu çivi turda 1 `..._kapiyi_KAPATIR` adıyla ve TERS
    iddiayla duruyordu; Rol-1 kararıyla tam sayı şartı ALARM eksenine alındı. Çiviyi SİLMEK yerine
    ters hükmü burada donduruyoruz: silinen bir çivi geri dönen bir davranıştır, ve bu özel geri
    dönüşün bedeli ölçülmüş (kesirli oran sağlayıcıda %89, haftalık kol `verify`i otomatik koşar →
    yazım modu kendiliğinden kapanır ve kota yağmuru geri gelir).

    ÖLÇÜMÜN KENDİSİ DEĞİŞMEDİ: kesir BÜYÜKLÜK olarak hâlâ görünmez (1.000.000 → 1.000.000,107552;
    bağıl fark ~1e-7, her toleransın altında), yani tam sayı şartı BAĞIL FARKTAN AYRI bir şart
    olmaya devam ediyor ve sayılıyor. Değişen tek şey İHLALİN SONUCU."""
    _anahtar(monkeypatch)
    _kur(monkeypatch, kesirli_gun=3)
    out = massive.verify(symbols=["AAPL"], days=PENCERE_GUN)

    # ÖLÇÜM YERİNDE: kesir sayıldı, örneği hükümde duruyor
    assert out["volume_fractional"] == 1 and out["volume_provider_bars"] == GUN_SAYISI
    assert "1000000.107552" in str(out["volume_fractional_example"])
    assert out["volume_mismatches"] == 0       # kesir bağıl farkta GÖRÜNMÜYOR (şartın ayrı olma kanıtı)
    # HÜKÜM TERS: kapı AÇIK kalır, düşen eksen YOK
    assert out["axes"]["hacim"]["verdict"] == "uyumlu"
    assert out["verdict"] == "uyumlu" and out["failed_axes"] == []
    assert massive.write_enabled() is True
    assert store.read_json(massive.VERIFY_FILE, {})["failed_axes"] == []


def test_K1b_kesirli_hacim_ADIYLA_duyurulur_YASA4(monkeypatch):
    """YASA 4: ihlal sessiz olamaz — ve kapı kapanmadığı için duyuru artık TEK kanıttır. Tur 2'de
    olay ADI değişti (`massive_hacim_uyumsuz` → `massive_hacim_tam_sayi_ihlali`): eski olayın
    gövdesi "kapı kapandı, zincir yedeklere döndü" diye bir SONUÇ beyan ediyor ve bu cümle tam sayı
    ihlalinde YANLIŞ olurdu. Gerçekleşmemiş bir sonucu duyuran alarm, kanalın tamamına olan güveni
    aşındırır; ayrıca iki olayın operatör cevabı da farklıdır (biri acil, öteki değil)."""
    _anahtar(monkeypatch)
    _kur(monkeypatch, kesirli_gun=0)
    olaylar = []
    import meridian.obs as obs
    monkeypatch.setattr(obs, "warn", lambda e, **f: olaylar.append((e, f)))
    massive.verify(symbols=["AAPL"], days=PENCERE_GUN)
    adlar = [e for e, _ in olaylar]
    assert "massive_hacim_tam_sayi_ihlali" in adlar
    # KAPATMA olayı BASILMADI — çünkü kapanan bir şey yok (iki şiddet tek ada çökmemeli)
    assert "massive_hacim_uyumsuz" not in adlar
    alan = dict(olaylar[adlar.index("massive_hacim_tam_sayi_ihlali")][1])
    assert alan["fractional"] == 1 and alan["provider_bars"] == GUN_SAYISI
    assert alan["thresholds"]["vol_frac_max"] == massive.VERIFY_VOL_FRAC_MAX
    assert "KESİRLİ" in alan["reason"]
    # olayın KENDİSİ eksenin yetkisini ve turun hükmünü söyler: okuyucu hüküm dosyasını açmadan
    # "bu alarm kapattı mı?" (hayır, hiçbir zaman) ile "kapı kapandı mı?" (bu turda hayır)
    # sorularını AYRI AYRI cevaplayabilmeli
    assert alan["closes_gate"] is False and alan["verdict"] == "uyumlu"


def test_K1c_uyumlu_turda_hacim_olayi_BASILMAZ(monkeypatch):
    """Bedel yasasının diğer yüzü: yeni olay her turda ötmemeli, yoksa gürültü sinyali gömer.
    İKİ olay adı da sağlıklı turda SESSİZDİR."""
    _anahtar(monkeypatch)
    _kur(monkeypatch)
    olaylar = []
    import meridian.obs as obs
    monkeypatch.setattr(obs, "warn", lambda e, **f: olaylar.append(e))
    massive.verify(symbols=["AAPL"], days=PENCERE_GUN)
    assert "massive_hacim_uyumsuz" not in olaylar
    assert "massive_hacim_tam_sayi_ihlali" not in olaylar


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


# ============================================ K6 — ALARM EKSENİ: DUYURUR, KAPATMAZ (TUR 2)
def _olay_yakala(monkeypatch) -> list:
    """`obs.warn` çağrılarını (ad, alanlar) olarak toplar. Üç tur-2 çivisi de olay ADLARINI ayrı
    ayrı sorar; tek bir yardımcı, üç yerde farklı yazılmış yakalamanın sessizce ayrışmasını önler."""
    olaylar: list = []
    import meridian.obs as obs
    monkeypatch.setattr(obs, "warn", lambda e, **f: olaylar.append((e, f)))
    return olaylar


def test_K6_yalniz_kesirli_hacim_kapiyi_ACIK_BIRAKIR_ama_ALARM_uretir(monkeypatch):
    """TUR 2'NİN ÇEKİRDEĞİ. Ölçek uyumlu, yalnız tam sayı şartı ihlal: hüküm "uyumlu" ve yazım
    AÇIK kalır — çünkü bütünlük yazım tarafında korunuyor (TSK-192) ve kapatmanın bedeli ölçülmüş
    kota yağmurudur. Ama ihlal ÖRTÜLMEZ: ayrı bir eksen sözlüğünde, ayrı bir listede ve hüküm
    satırının kendisinde durur.

    OKUYUCU TESTİ: "uyumlu" ile "uyumlu, ama hacim tam sayı değil" birbirinden AYIRT EDİLEBİLMELİ.
    Bu çivi tam olarak o ayrımı ölçer — `verdict` tek başına yetmez, `alarms` boş mu dolu mu
    sorusu cevaplanabilir olmalı."""
    _anahtar(monkeypatch)
    _kur(monkeypatch, kesirli_gun=7)                          # ölçek AYNI, yalnız bir bar kesirli
    olaylar = _olay_yakala(monkeypatch)
    out = massive.verify(symbols=["AAPL"], days=PENCERE_GUN)

    # (1) KAPI AÇIK — kapatma eksenlerinin ikisi de temiz
    assert out["axes"]["fiyat"]["verdict"] == "uyumlu"
    assert out["axes"]["hacim"]["verdict"] == "uyumlu"
    assert out["verdict"] == "uyumlu" and out["failed_axes"] == []
    assert massive.write_enabled() is True and massive.mode() == "yazim"
    # (2) İHLAL GÖRÜNÜR — ayrı eksen sözlüğü + ayrı liste
    assert out["alarms"] == ["hacim_tam_sayi"]
    assert out["alarm_axes"]["hacim_tam_sayi"]["verdict"] == "ihlal"
    assert len(out["alarm_axes"]["hacim_tam_sayi"]["reason"]) >= 20
    assert "hacim_tam_sayi" not in out["axes"]                # ALARM ekseni kapı kümesine SIZMAZ
    # (3) HÜKÜM SATIRINDA da okunur: pano/haftalık özet `reason`u aynen basar
    assert "ALARM" in out["reason"] and "HACIM_TAM_SAYI" in out["reason"]
    assert "KAPANMADI" in out["reason"]
    # (4) OLAY BASILDI (YASA 4) — ve KAPATMA olayı basılmadı
    adlar = [e for e, _ in olaylar]
    assert "massive_hacim_tam_sayi_ihlali" in adlar and "massive_hacim_uyumsuz" not in adlar
    # (5) DİSK + PANO YÜZEYLERİ aynı ayrımı taşır (YASA 6: alanın okuyucusu var)
    diskte = store.read_json(massive.VERIFY_FILE, {})
    assert diskte["alarms"] == ["hacim_tam_sayi"] and diskte["failed_axes"] == []
    assert massive.verify_basis()["alarms"] == ["hacim_tam_sayi"]
    assert massive.status()["verify"]["alarms"] == ["hacim_tam_sayi"]
    assert massive.status()["verify"]["failed_axes"] == []    # iki alan AYRI: biri dolu, öteki boş
    assert massive.status()["write_enabled"] is True


def test_K6b_TABAN_alarm_icin_SAYI_UYDURMAZ(monkeypatch):
    """Yerel ölçüm YOKKEN `verify_basis` tabana döner. Taban tam sayı eksenini hiç sormamıştı
    (`BASELINE["volume_check"]["integrality_measured"] is False`), o yüzden `alarms` alanı BOŞ LİSTE
    olamaz: `[]` "ölçtüm, alarm yok" demektir ve bu uydurma olurdu. `None` = "bilmiyorum"."""
    _anahtar(monkeypatch)
    b = massive.verify_basis()
    assert b["basis"] == "rol1_taban"
    assert b["alarms"] is None                                # sıfır ile "bilmiyorum" AYNI DEĞİL


# ============================================ K7 — KAPATMA EKSENİ: TUR 1 DAVRANIŞI KORUNUR
def test_K7_olcek_sapmasi_kapiyi_KAPATIR_tam_sayi_KATKI_VERMEZ(monkeypatch):
    """Rolleri ayırmak KAPATMA eksenini zayıflatmamalı. Ölçek/birim sapması (lot↔adet, bin↔bir)
    hacim R'sine, likidite kapılarına ve RVOL sinyallerine GİRER — orada bozuk veri kararı doğrudan
    etkiler, yani yazım DURMALIDIR. Tur 1 davranışı burada aynen çivilidir.

    AYRICA: bu turda sağlayıcı hacmi TAM SAYI, yani kapanışın sebebi tek başına ölçektir. Alarm
    ekseninin kapanışa katkısı olmadığı ölçülür — aksi hâlde "ayrıldı" iddiası kanıtsız kalırdı."""
    _anahtar(monkeypatch)
    _kur(monkeypatch, saglayici_volume=1_000_000_000.0)       # ×1000, ama TAM SAYI
    olaylar = _olay_yakala(monkeypatch)
    out = massive.verify(symbols=["AAPL"], days=PENCERE_GUN)

    assert out["axes"]["hacim"]["verdict"] == "uyumsuz"
    assert out["verdict"] == "uyumsuz" and out["failed_axes"] == ["hacim"]
    assert massive.write_enabled() is False                   # zincir yedeklere döner
    assert out["volume_mismatch_pct"] == 1.0                  # düşüren şey BAĞIL FARK
    # ALARM ekseni bu kapanışa KATKI VERMEDİ
    assert out["volume_fractional"] == 0
    assert out["alarms"] == [] and out["alarm_axes"]["hacim_tam_sayi"]["verdict"] == "uyumlu"
    assert "ALARM" not in out["reason"]
    adlar = [e for e, _ in olaylar]
    assert "massive_hacim_uyumsuz" in adlar and "massive_hacim_tam_sayi_ihlali" not in adlar
    # kapatma olayı hâlâ KAPANMA sonucunu beyan eder (alarm olayından ayıran tam bu cümledir)
    alan = dict(olaylar[adlar.index("massive_hacim_uyumsuz")][1])
    assert "KAPANIR" in alan["detail"]


# ============================================ K8 — İKİSİ BİRDEN: KAPATMA BASKIN, İKİSİ DE OKUNUR
def test_K8_iki_eksen_birden_KAPATMA_baskin_ama_IKISI_DE_okunur(monkeypatch):
    """En kötü hâl: sağlayıcı hem ölçeği kırmış hem kesirli veriyor. Kapatma ekseni BASKINdır
    (hüküm "uyumsuz", yazım kapalı) — bir çürütme, bir alarmla yıkanamaz. Ama alarm da YUTULMAZ:
    kapanışın gölgesinde kalırsa kaynak kalitesi sinyali sessizce kaybolur ve ölçek düzeltildiği
    gün kesir kimsenin haberi olmadan geri döner."""
    _anahtar(monkeypatch)
    _kur(monkeypatch, saglayici_volume=1_000_000_000.0, kesirli_gun=5)
    olaylar = _olay_yakala(monkeypatch)
    out = massive.verify(symbols=["AAPL"], days=PENCERE_GUN)

    # KAPATMA BASKIN
    assert out["verdict"] == "uyumsuz" and out["failed_axes"] == ["hacim"]
    assert massive.write_enabled() is False
    # ALARM DA DURUYOR — ayrı listede, ayrı hükümle
    assert out["alarms"] == ["hacim_tam_sayi"]
    assert out["alarm_axes"]["hacim_tam_sayi"]["verdict"] == "ihlal"
    assert out["volume_fractional"] == 1
    # TEK SATIRDA İKİ EKSEN: önce düşüren, sonra alarm — okuyucu ikisini de görür
    assert "HACIM:" in out["reason"] and "HACIM_TAM_SAYI:" in out["reason"]
    assert out["reason"].index("HACIM:") < out["reason"].index("ALARM")
    # İKİ OLAY DA BASILDI (biri kapanışı, öteki kaynak kalitesini duyurur)
    adlar = [e for e, _ in olaylar]
    assert "massive_hacim_uyumsuz" in adlar and "massive_hacim_tam_sayi_ihlali" in adlar
    # alarm olayı KENDİ yetkisini ("kapatmam") turun hükmünden ("kapandı") AYRI söyler
    alan = dict(olaylar[adlar.index("massive_hacim_tam_sayi_ihlali")][1])
    assert alan["closes_gate"] is False and alan["verdict"] == "uyumsuz"
    # disk + pano: iki alan da dolu ve AYRI
    diskte = store.read_json(massive.VERIFY_FILE, {})
    assert diskte["failed_axes"] == ["hacim"] and diskte["alarms"] == ["hacim_tam_sayi"]
    assert massive.status()["verify"]["failed_axes"] == ["hacim"]
    assert massive.status()["verify"]["alarms"] == ["hacim_tam_sayi"]


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

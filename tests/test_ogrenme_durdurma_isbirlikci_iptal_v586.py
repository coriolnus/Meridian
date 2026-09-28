"""test_ogrenme_durdurma_isbirlikci_iptal_v586.py — öğrenme süreci durdurması uzun hesapta TAKILMAZ (TSK-246).

VAKA (Rol-1 ölçümü, A1 journal, 2026-09-28). Dağıtım #80'in `meridian-learn` durdurması:
10:15:27Z `learn_run_durdurma_istegi` (dur bayrağı kondu) ve AYNI SANİYEDE `incumbent_prefill_pool_failed`
BrokenProcessPool → 10:17:27Z `stop-sigterm timed out` → SIGKILL. Zincir:
  * `KillMode=control-group` SIGTERM'i havuz işçilerine de yollar → havuz kırılır;
  * `reflect.prefill_incumbents` havuz istisnasında eksikleri SIRALI yola düşürür — her biri TAM bir
    walk-forward (kod şerhinin kendi ölçümü: 2 iş için 5065 sn);
  * sıralı döngü dur bayrağına BAKMIYORDU → 120 sn `TimeoutStopSec` dolar → SIGKILL. Birim şerhinin
    "stop() yalnız bayrak koyar … 120 sn yeterli tampon" iddiası bu ölçümle çürüdü.
Zarar o gün yoktu (defterler bütün) ama sınıf açıktı: SIGKILL yarım yazımı çekirdeğe bırakır.

ÇÖZÜM: İŞBİRLİKÇİ İPTAL. Uzun hesap yolları çağırandan ENJEKTE edilen bir `durdurma` yüklemini (argümansız,
bool döner — `canlilik` kancasının deseni) KONTROL NOKTALARINDA okur: havuz bekleyişinin her kuantumunda
(`DURDURMA_KONTROL_SN`), sıralı incumbent döngüsünün her adımında, aramanın incumbent yürüyüşünden önce ve
sondalar arasında. Durunca: kısmi ilerleme diske iner, havuz öldürülür, beyanlı olayla çıkılır. `reflect`
`hermes_runtime`i TANIMAZ — yüklem enjekte edilir (import grafiği değişmez).

SINIR (beyan): TEK bir walk-forward bölünemez (`coordinate_descent_search` "TAVAN KONTROLÜ SONDALAR ARASINDA"
gerekçesi aynen). Hermes ipliğinin KENDİSİ bir walk-forward hesaplarken gelen SIGTERM o hesabın bitişini
bekler — bu çivi o fazı iddia ETMEZ; kapsanan: havuz bekleyişi + iki walk-forward ARASI her nokta.

CANLI STATE'E YAZILMAZ: her state testi `sandbox_state` içinde; hiçbir test gerçek işçi SÜRECİ başlatmaz
(havuz sahte-future/iş parçacığı ile — v236 deseni).
"""
from __future__ import annotations

import ast
import concurrent.futures as cf
import shutil
import signal
import threading
import time
from concurrent.futures.process import BrokenProcessPool
from pathlib import Path

import pytest

from meridian import config, hermes, hermes_runtime, learn_run, reflect, store
from tests import wf_fixtures as wf

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def seeded_sandbox(sandbox_state):
    """sandbox_state + goal.yaml/bounds.yaml (test_warmup_tavani_v143 ile AYNI desen)."""
    repo_state = REPO / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo_state / f, sandbox_state / f)
    config.goal.cache_clear()
    config.bounds.cache_clear()
    return sandbox_state


def _olaylar(ad: str) -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl") if e.get("event") == ad]


_DUZ = [(30, 0.2), (30, 0.2), (30, 0.2)]


def _yuruyus_sayaci(monkeypatch) -> dict:
    """Sahte walk-forward: her çağrıyı SAYAR (bir çağrı = bir TAM walk-forward'ın bedeli — canlıda 2279-3185 sn, `reflect.HAVUZ_IS_SURESI_OLCULEN_SN` tablosu)."""
    sayac = {"n": 0}

    def _wf(params, bars, index, goal, *a, **kw):
        sayac["n"] += 1
        return wf.wf_from_scores(0.10, folds=_DUZ, holdout=0.10)

    monkeypatch.setattr(reflect.backtest, "walk_forward", _wf)
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
    reflect.clear_wf_caches()
    reflect._PROBE_CACHE.clear()
    return sayac


class _KirikHavuz:
    """SIGTERM'in işçileri öldürdüğü havuz (KillMode=control-group): her iş BrokenProcessPool ile düşer."""
    olusanlar: list = []

    def __init__(self, *a, **k):
        self._processes = {}
        self.kapanislar = []
        _KirikHavuz.olusanlar.append(self)

    def submit(self, fn, j):
        f = cf.Future()
        f.set_exception(BrokenProcessPool("işçiler SIGTERM ile öldü (benzetim)"))
        return f

    def shutdown(self, wait=True, cancel_futures=False):
        self.kapanislar.append((wait, cancel_futures))


class _AsiliHavuz:
    """Sağlıklı ama UZUN hesap koşan havuz: ilk `hemen` iş anında biter, kalanı hiç bitmez (walk-forward
    saatler sürer — testte sonsuz). Kapanış çağrıları kaydedilir."""
    olusanlar: list = []
    hemen = 0
    kuruldu = threading.Event()

    def __init__(self, *a, **k):
        self._processes = {}
        self.kapanislar = []
        self._n = 0
        _AsiliHavuz.olusanlar.append(self)
        _AsiliHavuz.kuruldu.set()

    def submit(self, fn, j):
        f = cf.Future()
        self._n += 1
        if self._n <= _AsiliHavuz.hemen:
            f.set_result((j["key"], wf.wf_from_scores(0.10, folds=_DUZ, holdout=0.10)))
        return f

    def shutdown(self, wait=True, cancel_futures=False):
        self.kapanislar.append((wait, cancel_futures))


def _havuz_kur(monkeypatch, sinif, *, hemen: int = 0):
    sinif.olusanlar = []
    if sinif is _AsiliHavuz:
        _AsiliHavuz.hemen = hemen
        _AsiliHavuz.kuruldu = threading.Event()
    monkeypatch.setattr("concurrent.futures.ProcessPoolExecutor", sinif)
    monkeypatch.setenv("MERIDIAN_PARALLEL_PROBES", "1")


# =================================================================================================
# A) HAVUZ BEKLEYİŞİ — `_havuz_sonuclari` kuantumunda bayrak okunur
# =================================================================================================
def test_havuz_bekleyisinde_bayrak_DURDURMA_ISTEGI_firlatir(monkeypatch):
    """ASIL ÇİVİ (havuz bacağı). İş 3 sn sürer, nabız kuantumu 60 sn (canlı değer): bayrak 0,1 sn'de
    kurulur. Yüklem okunmasaydı YA DA bekleyiş nabız kuantumunda (60 sn) kalsaydı jeneratör işi bitirip
    normal dönerdi — iki mutasyon da bu çiviyi kırmızıya çevirir."""
    monkeypatch.setattr(reflect, "HAVUZ_NABIZ_SN", 60.0)
    monkeypatch.setattr(reflect, "HAVUZ_ATALET_SN", 100.0)
    monkeypatch.setattr(reflect, "DURDURMA_KONTROL_SN", 0.02)
    monkeypatch.setattr(reflect, "_pool_probe_job", lambda j: (time.sleep(3.0), (j["key"], {"v": 1}))[1])
    bayrak = threading.Event()
    threading.Timer(0.1, bayrak.set).start()
    ex = cf.ThreadPoolExecutor(max_workers=1)
    try:
        t0 = time.monotonic()
        with pytest.raises(reflect._DurdurmaIstegi) as z:
            list(reflect._havuz_sonuclari(ex, [{"key": "k1"}], durdurma=bayrak.is_set))
        gecen = time.monotonic() - t0
    finally:
        ex.shutdown(wait=True)
    assert gecen < 1.0, f"bayrak {gecen:.2f} sn'de görüldü — kontrol kuantumu 0,02 sn"
    assert z.value.biten == 0 and z.value.bekleyen == 1, (z.value.biten, z.value.bekleyen)


def test_kisa_kuantum_NABZI_cogaltmaz(monkeypatch):
    """BEDEL YASASI: durdurma kuantumu (kısa) bekleyişi sık uyandırır ama NABIZ kadansı değişmemeli —
    nabız bir disk yazımıdır (`_kalp_tazele` + `watchdog.beat`) ve her kuantumda atılsaydı 12 kat
    artardı. 0,5 sn'lik bekleyişte nabız 0,1 sn'de bir → ~5 vuruş; kuantum başına atılsa ~25 olurdu."""
    monkeypatch.setattr(reflect, "HAVUZ_NABIZ_SN", 0.1)
    monkeypatch.setattr(reflect, "HAVUZ_ATALET_SN", 100.0)
    monkeypatch.setattr(reflect, "DURDURMA_KONTROL_SN", 0.02)
    monkeypatch.setattr(reflect, "_pool_probe_job", lambda j: (time.sleep(0.5), (j["key"], {"v": 1}))[1])
    vurus = []
    ex = cf.ThreadPoolExecutor(max_workers=1)
    try:
        sonuc = list(reflect._havuz_sonuclari(ex, [{"key": "k1"}], canlilik=lambda: vurus.append(1),
                                              durdurma=lambda: False))
    finally:
        ex.shutdown(wait=True)
    assert len(sonuc) == 1, "bayrak kurulu değilken sonuç kayboldu"
    assert 2 <= len(vurus) <= 8, (
        f"{len(vurus)} nabız — 0,5 sn / 0,1 sn ≈ 5 beklenir; kısa durdurma kuantumu nabzı çoğaltmamalı")


# =================================================================================================
# B) INCUMBENT ÖN-HESABI — sıralı yol + havuz yolu
# =================================================================================================
def test_sirali_yolda_bayrak_ILK_kontrol_noktasinda_cikar(seeded_sandbox, monkeypatch):
    """Sıralı bacak: bayrak kuruluyken TEK walk-forward bile başlamaz; beyanlı olay düşer."""
    sayac = _yuruyus_sayaci(monkeypatch)
    monkeypatch.delenv("MERIDIAN_PARALLEL_PROBES", raising=False)
    out = reflect.prefill_incumbents(None, None, [None, "chop", "trend_up"], durdurma=lambda: True)
    assert sayac["n"] == 0, f"bayrak kuruluyken {sayac['n']} tam walk-forward koştu (canlıda her biri 2279-3185 sn)"
    assert out["computed"] == 0 and out["durduruldu"] == "sirali", out
    olay = _olaylar("incumbent_prefill_durduruldu")
    assert olay and olay[-1]["asama"] == "sirali" and olay[-1]["kalan"] == 3, olay
    assert len(str(olay[-1].get("detail", ""))) >= 20, "olay gerekçesiz (YASA 4)"


def test_OLAY_TEKRARI_havuz_kirilinca_bayrak_varsa_sirali_yola_DUSULMEZ(seeded_sandbox, monkeypatch):
    """2026-09-28 10:15:27Z'nin sentetik tekrarı: SIGTERM işçileri öldürür → BrokenProcessPool → eski kod
    eksikleri SIRALI yola düşürüyordu. Artık bayrak okunur, sıralı hesap başlamaz.
    SIRA GERÇEKTEKİ GİBİ: bayrak havuz bekleyişi SIRASINDA kurulur (ilk kontrol noktası onu görmez);
    bekleyiş kırık işlerle uyanır, `f.result()` BrokenProcessPool fırlatır → genel istisna dalı → sıralı
    döngünün kontrol noktası. (Bayrak bekleyişten ÖNCE kuruluysa "havuz" dalı yakalar — o yol ayrı çivide.)"""
    sayac = _yuruyus_sayaci(monkeypatch)
    _havuz_kur(monkeypatch, _KirikHavuz)
    okuma = {"n": 0}

    def _bekleyis_sirasinda_kurulan_bayrak() -> bool:
        okuma["n"] += 1
        return okuma["n"] > 1                     # ilk okuma (bekleyiş öncesi) False, sonrası True

    out = reflect.prefill_incumbents(None, None, [None, "chop", "trend_up"],
                                     durdurma=_bekleyis_sirasinda_kurulan_bayrak)
    assert sayac["n"] == 0, f"kırık havuzdan sonra {sayac['n']} SIRALI walk-forward koştu — olayın kendisi"
    assert out["durduruldu"] == "sirali", out
    assert _olaylar("incumbent_prefill_pool_failed"), "havuz arızası beyanı (tarihçe serisi) düşmedi"
    assert _KirikHavuz.olusanlar and (False, True) in _KirikHavuz.olusanlar[0].kapanislar


def test_havuz_bekleyisinde_bayrak_havuz_OLDURULUR_kismi_sonuc_DISKE_iner(seeded_sandbox, monkeypatch):
    """Havuz bacağı: ilk iş bitmiş, ikisi sürüyor; bayrak kurulunca havuz BLOKE ETMEDEN kapatılır, biten
    incumbent diske iner (yeniden başlatmada bedava), sıralı yola DÜŞÜLMEZ, olay sayımlarıyla düşer."""
    sayac = _yuruyus_sayaci(monkeypatch)
    _havuz_kur(monkeypatch, _AsiliHavuz, hemen=1)
    monkeypatch.setattr(reflect, "DURDURMA_KONTROL_SN", 0.02)
    monkeypatch.setattr(reflect, "HAVUZ_ATALET_SN", 30.0)
    t0 = time.monotonic()
    out = reflect.prefill_incumbents(None, None, [None, "chop", "trend_up"],
                                     durdurma=lambda: len(reflect._INC_CACHE) >= 1)
    assert time.monotonic() - t0 < 5.0, "havuz bekleyişi bayrağı görmedi (atalet tavanına kadar bekledi)"
    assert sayac["n"] == 0, f"havuz durdurulduktan sonra {sayac['n']} sıralı walk-forward koştu"
    assert out["computed"] == 1 and out["durduruldu"] == "havuz", out
    assert (False, True) in _AsiliHavuz.olusanlar[0].kapanislar, "havuz bloke etmeden kapatılmadı"
    disk = store.read_json(reflect.INC_DISK_FILE, {}) or {}
    assert len(disk.get("entries") or {}) == 1, "biten incumbent diske inmedi — kısmi ilerleme kayboldu"
    olay = _olaylar("arama_havuzu_durduruldu")
    assert olay and olay[-1]["yer"] == "incumbent_prefill", olay
    assert olay[-1]["biten"] == 1 and olay[-1]["bekleyen"] == 2, olay


def test_POZITIF_KONTROL_bayrak_kurulu_degilken_prefill_birebir(seeded_sandbox, monkeypatch):
    """Yüklem VERİLİP hiç kurulmazsa sonuç yüklemsiz çağrıyla BİREBİR: aynı hesap sayısı, aynı önbellek
    anahtarları. Kırık havuzda bugünkü davranış (eksikler sıralı yolda hesaplanır) aynen korunur."""
    sayac = _yuruyus_sayaci(monkeypatch)
    monkeypatch.delenv("MERIDIAN_PARALLEL_PROBES", raising=False)
    yuklemsiz = reflect.prefill_incumbents(None, None, [None, "chop", "trend_up"])
    anahtar0, n0 = set(reflect._INC_CACHE), sayac["n"]
    reflect.clear_wf_caches(); sayac["n"] = 0
    yuklemli = reflect.prefill_incumbents(None, None, [None, "chop", "trend_up"], durdurma=lambda: False)
    assert (yuklemli["computed"], yuklemli["cached"]) == (yuklemsiz["computed"], yuklemsiz["cached"]) == (3, 0)
    assert sayac["n"] == n0 == 3 and set(reflect._INC_CACHE) == anahtar0
    assert yuklemli["durduruldu"] is None
    # kırık havuz + bayrak YOK → bugünkü yedek yol: eksikler sıralı hesaplanır
    reflect.clear_wf_caches(); sayac["n"] = 0
    _havuz_kur(monkeypatch, _KirikHavuz)
    out = reflect.prefill_incumbents(None, None, [None, "chop", "trend_up"], durdurma=lambda: False)
    assert sayac["n"] == 3 and out["computed"] == 3 and out["durduruldu"] is None, out


# =================================================================================================
# C) KOORDİNAT ARAMASI — incumbent öncesi + sondalar arası + sonda ön-doldurma havuzu
# =================================================================================================
def test_arama_girisinde_bayrak_incumbent_yuruyusu_BASLAMAZ(seeded_sandbox, monkeypatch):
    """Aramanın EN pahalı tek adımı incumbent walk-forward'ıdır: bayrak kuruluysa o da başlamaz."""
    sayac = _yuruyus_sayaci(monkeypatch)
    monkeypatch.delenv("MERIDIAN_PARALLEL_PROBES", raising=False)
    res = reflect.coordinate_descent_search(None, None, config.goal(), windows=None, k_max=1, budget=3,
                                            durdurma=lambda: True)
    assert sayac["n"] == 0, f"bayrak kuruluyken {sayac['n']} walk-forward koştu"
    assert res["kesildi"] is True and res["sebep"] == reflect.DURDURMA_SEBEBI
    assert res["evaluated"] == 0 and res["best"] is None
    olay = _olaylar("search_durdurma_istegiyle_kesildi")
    assert olay and len(str(olay[-1].get("detail", ""))) >= 20, olay


def test_sondalar_arasinda_bayrak_ILK_kontrol_noktasinda_kesilir(seeded_sandbox, monkeypatch):
    """Sonda döngüsü: incumbent + 1 sonda bittikten sonra bayrak kurulur → ikinci sonda başlamaz. K sayımı
    muhasebesi (v143) durdurmada da tutar: kalan + değerlendirilen + atlanan = planlanan."""
    sayac = _yuruyus_sayaci(monkeypatch)
    monkeypatch.delenv("MERIDIAN_PARALLEL_PROBES", raising=False)
    res = reflect.coordinate_descent_search(None, None, config.goal(), windows=None, k_max=1, budget=3,
                                            durdurma=lambda: sayac["n"] >= 2)
    assert res["planlanan_sonda"] == 3, "stub üç sonda planlamadı — çivi ölçüm yapamaz"
    assert res["evaluated"] == 1 and sayac["n"] == 2, (res["evaluated"], sayac["n"])
    assert res["kesildi"] is True and res["sebep"] == reflect.DURDURMA_SEBEBI
    assert res["kalan_sonda"] + res["evaluated"] + res["skipped_wallclock"] == res["planlanan_sonda"]


def test_POZITIF_KONTROL_bayrak_kurulu_degilken_arama_birebir(seeded_sandbox, monkeypatch):
    """Yüklem verilip hiç kurulmazsa sonuç yüklemsiz aramayla BİREBİR (v143 tavansız-yol ölçütü)."""
    _yuruyus_sayaci(monkeypatch)
    monkeypatch.delenv("MERIDIAN_PARALLEL_PROBES", raising=False)
    yuklemsiz = reflect.coordinate_descent_search(None, None, config.goal(), windows=None, k_max=1, budget=3)
    reflect.clear_wf_caches(); reflect._PROBE_CACHE.clear()
    yuklemli = reflect.coordinate_descent_search(None, None, config.goal(), windows=None, k_max=1, budget=3,
                                                 durdurma=lambda: False)
    assert yuklemli["kesildi"] is False and "sebep" not in yuklemli and "kalan_sonda" not in yuklemli
    for alan in ("evaluated", "cleared", "planlanan_sonda", "incumbent_oos", "best", "trace"):
        assert yuklemli[alan] == yuklemsiz[alan], f"kurulmamış yüklem {alan} alanını değiştirdi"


def test_sonda_on_doldurma_havuzu_bayragi_GORUR(seeded_sandbox, monkeypatch):
    """Arama yüklemi sonda ön-doldurma havuzuna GEÇİRİR: incumbent yürüdükten sonra kurulan bayrakta
    asılı havuz atalet tavanını (burada 30 sn) beklemez; havuz öldürülür, olay `probe_prefill` der."""
    sayac = _yuruyus_sayaci(monkeypatch)
    _havuz_kur(monkeypatch, _AsiliHavuz, hemen=0)
    monkeypatch.setattr(reflect, "DURDURMA_KONTROL_SN", 0.02)
    monkeypatch.setattr(reflect, "HAVUZ_ATALET_SN", 30.0)
    t0 = time.monotonic()
    res = reflect.coordinate_descent_search(None, None, config.goal(), windows=None, k_max=1, budget=3,
                                            durdurma=lambda: sayac["n"] >= 1)
    assert time.monotonic() - t0 < 5.0, "sonda havuzu bayrağı görmedi (atalet tavanına kadar bekledi)"
    assert sayac["n"] == 1 and res["evaluated"] == 0, (sayac["n"], res["evaluated"])
    assert res["sebep"] == reflect.DURDURMA_SEBEBI
    olay = _olaylar("arama_havuzu_durduruldu")
    assert olay and olay[-1]["yer"] == "probe_prefill", olay
    assert (False, True) in _AsiliHavuz.olusanlar[0].kapanislar


# =================================================================================================
# D) ISINMA + SÜREÇ DURDURMASI — uçtan uca
# =================================================================================================
def _isinma_ortami(monkeypatch):
    sayac = _yuruyus_sayaci(monkeypatch)
    geri_besleme = []
    monkeypatch.setattr(hermes, "warmup_budget_feedback", lambda res: geri_besleme.append(res))
    bayrak = threading.Event()
    monkeypatch.setattr(hermes_runtime, "_stop", bayrak)
    return sayac, geri_besleme, bayrak


def test_isinma_dur_bayragini_iki_asamaya_GECIRIR_ve_merdivene_ISLEMEZ(seeded_sandbox, monkeypatch):
    """Bayrak kuruluyken ısınma: ön-hesap ve arama walk-forward BAŞLATMAZ; DURDURMA bir ölçüm değildir,
    bütçe merdivenine İŞLENMEZ (işlenseydi `kesildi` "süre tavanı" sayılır, çarpan yarıya iner ve sahte
    bir duvar çakılırdı — `hermes.warmup_budget_feedback`in kesildi dalı)."""
    sayac, geri_besleme, bayrak = _isinma_ortami(monkeypatch)
    monkeypatch.delenv("MERIDIAN_PARALLEL_PROBES", raising=False)
    bayrak.set()
    hermes_runtime._warmup_sprint()
    assert sayac["n"] == 0, f"dur bayrağı kuruluyken ısınma {sayac['n']} walk-forward koştu"
    assert geri_besleme == [], "durdurulan ısınma bütçe merdivenine işlendi — sahte süre-tavanı duvarı"
    lw = hermes_runtime._state.get("last_warmup") or {}
    assert lw.get("sebep") == reflect.DURDURMA_SEBEBI and "error" not in lw, lw
    olay = _olaylar("warmup_sprint")
    assert olay and olay[-1].get("durduruldu") is True, olay


def test_POZITIF_KONTROL_bayraksiz_isinma_merdivene_ISLENIR(seeded_sandbox, monkeypatch):
    """Bayrak kurulmadıkça ısınma bugünkü gibi: walk-forward koşar, sonuç merdivene işlenir."""
    sayac, geri_besleme, _bayrak = _isinma_ortami(monkeypatch)
    monkeypatch.delenv("MERIDIAN_PARALLEL_PROBES", raising=False)
    monkeypatch.setenv("HERMES_WARMUP_BUDGET", "3")
    hermes_runtime._warmup_sprint()
    assert sayac["n"] >= 2 and len(geri_besleme) == 1, (sayac["n"], geri_besleme)
    assert (hermes_runtime._state.get("last_warmup") or {}).get("sebep") is None


def test_SIGTERM_kancasi_bayragi_OLAY_YAZIMINDAN_ONCE_kurar(sandbox_state, monkeypatch):
    """YARIŞ DARALTMA: systemd SIGTERM'i önce ana sürece, hemen ardından havuz işçilerine yollar (systemd
    öldürme sırası — kaynak okuması, A1'de ölçülmedi). Kanca
    önce olay yazarsa (disk G/Ç) havuz kırılması bayraktan ÖNCE görülebilir ve hermes ipliği bayrak
    kurulmadan sıralı yola girer. Bayrak kancanın İLK işidir."""
    bayrak = threading.Event()
    monkeypatch.setattr(hermes_runtime, "_stop", bayrak)
    goruldu = []
    monkeypatch.setattr(learn_run.obs, "log", lambda ad, **k: goruldu.append((ad, bayrak.is_set())))
    learn_run._isaret(signal.SIGTERM, None)
    assert bayrak.is_set()
    assert goruldu and goruldu[0] == ("learn_run_durdurma_istegi", True), (
        f"olay bayraktan ÖNCE yazıldı: {goruldu}")


def test_OLCUM_sigtermden_isinma_inisine_sure_30_sn_ALTINDA(seeded_sandbox, monkeypatch):
    """HEDEF ÖLÇÜMÜ (brief §3): gerçek `DURDURMA_KONTROL_SN` ile, uzun hesap koşan (asılı) bir incumbent
    havuzunun ortasında SIGTERM kancası tetiklenir; ısınma ipliğinin inişi ölçülür. Tavan 120 sn
    (`TimeoutStopSec`), hedef ≤30 sn; beklenen ≈ bir kontrol kuantumu."""
    sayac, geri_besleme, bayrak = _isinma_ortami(monkeypatch)
    _havuz_kur(monkeypatch, _AsiliHavuz, hemen=0)
    # Atalet tavanı küçültülür YALNIZ çivi kırmızıyken ipliğin ömrünü sınırlamak için (bayrak okunmasa
    # iplik ~9555 sn asılı kalırdı); ölçülen yol (bayrak → iniş) bu değere bağlı değildir.
    monkeypatch.setattr(reflect, "HAVUZ_ATALET_SN", 20.0)
    store.write_json("regime.json", {"regime": "chop"})         # iki eksik varyant → HAVUZ yolu
    iplik = threading.Thread(target=hermes_runtime._warmup_sprint, name="isinma-olcum", daemon=True)
    iplik.start()
    assert _AsiliHavuz.kuruldu.wait(10), "ısınma incumbent havuzunu kurmadı — ölçüm zemini yok"
    t0 = time.monotonic()
    learn_run._isaret(signal.SIGTERM, None)
    iplik.join(timeout=40)
    gecen = time.monotonic() - t0
    assert not iplik.is_alive(), "ısınma ipliği 40 sn'de inmedi"
    assert gecen <= reflect.DURDURMA_KONTROL_SN + 2.0, f"iniş {gecen:.2f} sn — beklenen ≈ bir kontrol kuantumu"
    assert gecen <= 30.0, f"iniş {gecen:.2f} sn — hedef ≤30 sn (TimeoutStopSec 120)"
    assert sayac["n"] == 0 and geri_besleme == [], (sayac["n"], geri_besleme)
    print(f"\n[v586 ÖLÇÜM] SIGTERM kancası → ısınma inişi: {gecen:.2f} sn "
          f"(DURDURMA_KONTROL_SN={reflect.DURDURMA_KONTROL_SN})")


# =================================================================================================
# E) SÖZLEŞME — yüklem ENJEKTE edilir, reflect hermes_runtime'ı tanımaz
# =================================================================================================
def test_reflect_hermes_runtimei_IMPORT_ETMEZ():
    """Bayrağa erişim import grafiğini DEĞİŞTİRMEZ: `reflect` → `hermes_runtime` kenarı (fonksiyon-içi
    dahil — import-linter onu da sayar) yoktur; yüklem çağırandan gelir (`canlilik` deseni)."""
    agac = ast.parse((REPO / "meridian" / "reflect.py").read_text(encoding="utf-8"))
    kenarlar = []
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.ImportFrom):
            adlar = [a.name for a in dugum.names]
            if (dugum.module or "").endswith("hermes_runtime") or "hermes_runtime" in adlar:
                kenarlar.append(dugum.lineno)
        elif isinstance(dugum, ast.Import):
            if any(a.name.endswith("hermes_runtime") for a in dugum.names):
                kenarlar.append(dugum.lineno)
    assert kenarlar == [], f"reflect hermes_runtime'ı içe aktarıyor (satırlar {kenarlar})"


def test_isinma_iki_cagriya_da_YUKLEMI_gecirir():
    """Yapısal çivi (v302'nin `canlilik` çivisinin ikizi): ısınmanın iki uzun çağrısı da dur yüklemini
    AYRI AYRI geçirir — biri sökülünce öbürünün varlığı çiviyi susturmasın."""
    import inspect
    import re
    src = inspect.getsource(hermes_runtime._warmup_sprint)
    m = re.search(r"reflect\.prefill_incumbents\((.*?)\)", src, re.S)
    assert m and "durdurma=" in m.group(1), "ön-hesap çağrısı dur yüklemini GEÇİRMİYOR"
    m2 = re.search(r"reflect\.coordinate_descent_search\((.*?)record_session", src, re.S)
    assert m2 and "durdurma=" in m2.group(1), "arama çağrısı dur yüklemini GEÇİRMİYOR"

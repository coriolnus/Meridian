"""MERIDIAN_ROOT ORTAM SIZINTISI BEKÇİSİNİN ÇİVİLERİ — `tests/conftest.py::_kok_sizinti_bekcisi`.

VAKA (2026-09-29, tam suite f3d21402, `-n 4 --dist worksteal`, iki kırmızı). Ölçüm betiği
`research/olcumler/edg091_r_paydasi/olc.py::kos` `os.environ["MERIDIAN_ROOT"]`u KALICI yazar —
komut satırı için doğru, çünkü süreç biter. `tests/test_edg091_r_paydasi_v479.py` onu SÜREÇ
İÇİNDE çağırıyordu: xdist işçisinin ortamı, test bitince silinen sahte bir köke işaret ederek
kaldı. Aynı işçide sonra koşan `spawn` testleri (`tests/test_is_istek_v594.py`) çocukta
`kadro_yukle()` ile o kökün altında olmayan bir `deploy/hermes/kadro.yaml` aradı; ana test 120 sn
kuyruk bekleyip `Empty` ile düştü. Kırmızı KURBANDA görünür, sızdıran YEŞİLDİR — sonuç sıraya
ve işçi dağılımına bağlıdır, yani "bugün geçti" hiçbir şey kanıtlamaz.

NE ÇİVİLER:
  K1 saf yüklem `_kok_sizinti_denetle`: eşitlikte None; her farkta (değişti · doğdu · silindi ·
     boş dizge ≠ tanımsız) mesaj. Mesaj önce/sonra değerini ve `monkeypatch.setenv` yolunu taşır.
  K2 söküm eylemi `_kok_sizinti_sokum`: sızıntı yoksa hiçbir şeye dokunmaz; varsa ESKİ değeri
     geri koyar (önce tanımsızsa SİLER) ve testi düğüm kimliğiyle KIRMIZI yapar. Geri yükleme
     kırmızıdan ÖNCE olur: bekçinin işi yalnız sızdıranı adlandırmak değil, sonraki testleri
     kirli kökten korumaktır.
  K3 bekçi AUTOUSE'dur ve bu testte etkindir (yoksa K4 boşuna yeşil olurdu).
  K4 SIRA: bekçi `monkeypatch`ten ÖNCE kurulur, SONRA sökülür. `monkeypatch.setenv/delenv` ile
     yapılan değişiklik monkeypatch sökümünde geri alınır ve bekçiye TAKILMAZ. Sıra tersse
     aşağıdaki iki davranış çivisi SÖKÜMDE kırmızıya döner (mutasyonla gösterildi).
  K5 UÇTAN UCA (inceleme I-1, 2026-09-30): K1–K4 bekçinin PARÇALARINI çiviler; fikstür gövdesi
     `yield`den sonra `_kok_sizinti_sokum`u çağırmayı bıraksa dördü de yeşil kalırdı. K5 deponun
     GERÇEK `tests/conftest.py`sini bir ALT OTURUMDA yükler (`-p tests.conftest`) ve bekçinin
     sökümde gerçekten ateşlediğini, geri yüklediğini ve monkeypatch'i serbest bıraktığını ölçer.
  K6 TOPLAMA ZAMANI (TSK-255 (a)): modül İÇE AKTARILIRKEN kökü yazan modül, toplama raporu kırmızı
     ve düğüm kimliğiyle düşer; kök hemen geri yüklenir, sonraki modül temiz kökle içe aktarılır.
  K7 OTURUM DÜZEYİ (TSK-255 (a)): toplama kancası (hiçbir toplayıcının içinde değil) ve modül
     kapsamlı fikstürün sökümü — ikisi de fonksiyon bekçisine görünmez; oturum sonu denetimi geri
     yükler, raporlar, çıkışı kırmızıya çeker. Düz oturumda VE xdist altında (kayıt işçiden
     kontrolcüye workeroutput ile taşınır; otoriter suite `-n 4` koşar).
  K8 ALT OTURUM ORTAM SÜZGECİ (TSK-255 (b), yeniden inceleme N-1): alt oturumlar
     `MERIDIAN_PROVENANCE*` ve `PYTEST_*` değişkenlerini devralmaz; K5 bunu uçtan uca da ölçer.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

from tests.conftest import _KOK_ORTAM_ADI, _kok_sizinti_denetle, _kok_sizinti_sokum

AD = "MERIDIAN_ROOT"
BEKCI = "_kok_sizinti_bekcisi"
KOK = pathlib.Path(__file__).resolve().parents[1]


# ==================================================================================================
# K1 — SAF YÜKLEM
# ==================================================================================================
def test_k1_bekcinin_izledigi_ad_meridian_root():
    assert _KOK_ORTAM_ADI == AD


@pytest.mark.parametrize("deger", [None, "", "/bir/kok"])
def test_k1_esitlikte_mesaj_yok(deger):
    assert _kok_sizinti_denetle(deger, deger) is None


@pytest.mark.parametrize("once,sonra", [
    ("/eski/kok", "/yeni/kok"),      # değişti
    (None, "/sizan/kok"),            # test doğurdu
    ("/eski/kok", None),             # test sildi
    ("", None),                      # boş dizge TANIMSIZ DEĞİLDİR
    (None, ""),
])
def test_k1_her_farkta_mesaj_ve_yol(once, sonra):
    mesaj = _kok_sizinti_denetle(once, sonra)
    assert isinstance(mesaj, str) and mesaj
    assert AD in mesaj
    assert "monkeypatch.setenv" in mesaj
    for deger in (once, sonra):
        if deger is None:
            assert "(tanımsız)" in mesaj
        else:
            assert repr(deger) in mesaj


# ==================================================================================================
# K2 — SÖKÜM EYLEMİ: GERİ YÜKLE, SONRA KIRMIZI
# ==================================================================================================
def test_k2_sizinti_yoksa_dokunmaz():
    ortam = {AD: "/ayni", "BASKA": "x"}
    assert _kok_sizinti_sokum("/ayni", "t.py::a", ortam) is None
    assert ortam == {AD: "/ayni", "BASKA": "x"}
    bos: dict[str, str] = {"BASKA": "x"}
    assert _kok_sizinti_sokum(None, "t.py::a", bos) is None
    assert bos == {"BASKA": "x"}


def test_k2_once_tanimsizsa_siler_ve_dusurur():
    ortam = {AD: "/sizan/kok", "BASKA": "x"}
    with pytest.raises(pytest.fail.Exception) as e:
        _kok_sizinti_sokum(None, "tests/test_ornek.py::test_sizdiran", ortam)
    assert AD not in ortam and ortam["BASKA"] == "x"
    assert "tests/test_ornek.py::test_sizdiran" in str(e.value)
    assert "/sizan/kok" in str(e.value)


def test_k2_once_tanimliysa_eski_degeri_koyar_ve_dusurur():
    ortam = {AD: "/sizan/kok"}
    with pytest.raises(pytest.fail.Exception) as e:
        _kok_sizinti_sokum("/eski/kok", "t.py::b", ortam)
    assert ortam[AD] == "/eski/kok"
    assert "t.py::b" in str(e.value)
    silinmis: dict[str, str] = {}
    with pytest.raises(pytest.fail.Exception):
        _kok_sizinti_sokum("/eski/kok", "t.py::c", silinmis)
    assert silinmis == {AD: "/eski/kok"}


def test_k2_varsayilan_ortam_os_environ(monkeypatch):
    """Üçüncü argüman verilmezse GERÇEK süreç ortamı ölçülür (bekçinin çağırdığı biçim)."""
    monkeypatch.setenv(AD, "/gecici/kok")
    assert _kok_sizinti_sokum("/gecici/kok", "t.py::d") is None
    with pytest.raises(pytest.fail.Exception):
        _kok_sizinti_sokum("/baska/kok", "t.py::e")
    assert os.environ[AD] == "/baska/kok"   # geri yüklendi; monkeypatch sökümü tanımsıza döndürür


# ==================================================================================================
# K3 — AUTOUSE VE ETKİN
# ==================================================================================================
def test_k3_bekci_autouse_ve_bu_testte_etkin(request):
    assert BEKCI in request.fixturenames


# ==================================================================================================
# K4 — SIRA: BEKÇİ MONKEYPATCH'TEN ÖNCE KURULUR, SONRA SÖKÜLÜR
# ==================================================================================================
def test_k4_bekci_monkeypatchten_once_kurulur(request, monkeypatch):
    adlar = request.fixturenames
    assert adlar.index(BEKCI) < adlar.index("monkeypatch"), adlar


def test_k4_monkeypatch_setenv_bekciye_takilmaz(monkeypatch, tmp_path):
    """Sıra tersse (monkeypatch bekçiden önce kurulursa) bu test SÖKÜMDE kırmızıdır."""
    monkeypatch.setenv(AD, str(tmp_path / "gecici_kok"))
    assert os.environ[AD] == str(tmp_path / "gecici_kok")


@pytest.fixture(scope="module")
def _modul_kapsamli_kok():
    """Bekçiden ÖNCE kurulan (daha geniş kapsam) bir kök. Silme yönünün çivisi ancak test başında
    değer VARKEN ısırır: süreçte tanımsızsa (yerel koşumların olağanı) "sildi" ile "dokunmadı"
    bekçiye aynı görünür ve yanlış sıra sessizce yeşil kalırdı (M5 mutasyonunda ölçüldü)."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv(AD, "/modul/kapsamli/kok")
        yield "/modul/kapsamli/kok"


def test_k4_monkeypatch_delenv_bekciye_takilmaz(_modul_kapsamli_kok, monkeypatch):
    """Sıra tersse bekçi 'silindi' görür ve bu test SÖKÜMDE kırmızıdır."""
    assert os.environ[AD] == _modul_kapsamli_kok
    monkeypatch.delenv(AD)
    assert AD not in os.environ


# ==================================================================================================
# K5 — UÇTAN UCA: GERÇEK conftest ALT OTURUMDA, BEKÇİ SÖKÜMDE GERÇEKTEN ATEŞLER
# ==================================================================================================
# NEDEN ALT SÜREÇ, `pytester` DEĞİL (pytest 9.1.1'de ÖLÇÜLDÜ, 2026-09-30): test modülündeki
# `pytest_plugins = ["pytester"]` kabul ediliyor ama kayıt OTURUM GENELİDİR — komşu bir modül de
# `pytester` fikstürünü ve eklentisini görüyor. "Yalnız v595 için" açılamaz; 15k testlik xdist
# suite'inde v595'i toplayan her işçiye eklenti kaydolurdu. Süreç-içi `pytester` koşumu da ağır
# conftest'i aynı süreçte İKİNCİ kez yüklerdi (soket/hermes/open kancaları üst üste). Düz alt süreç
# ikisinden de uzak: conftest KOPYALANMAZ, ithal edilir (`-p tests.conftest`).
#
# ALT OTURUMUN ORTAMI: `PYTHONPATH` = BU dosyanın deposu (worktree'de de aynı ağacın conftest'i ve
# `meridian`ı yüklenir; venv ana checkout'a kuruludur). `MERIDIAN_ROOT` = geçici sanal kök: alt
# oturumun `config.STATE`i ve oturum-sonu `.locks` budaması oraya gider — xdist suite'i koşarken
# gerçek `state/.locks` budanmaz (o kanca xdist işçisinde bilerek koşmaz; alt oturum işçi değildir).
# `PYTHONDONTWRITEBYTECODE=1`: alt oturum `tests/` altına pyc bırakmaz. `PYTEST_*` değişkenleri
# (xdist işçi kimliği, `PYTEST_ADDOPTS`) alt oturuma taşınmaz. `MERIDIAN_PROVENANCE*` de taşınmaz
# (TSK-255 (b), yeniden inceleme N-1): üst oturum köken kipindeyse (`MERIDIAN_PROVENANCE=1`, elle
# ölçüm) alt oturum da o kipe girip sonda `docs/provenance_report.json`u GÖRELİ yola (cwd = tmp,
# orada `docs/` yok → INTERNALERROR, K5 yanlış teşhisli kırmızı) ya da mutlak `..._OUT`a (operatörün
# raporunu çocuğun boş iziyle EZER) yazardı. Süzgeç K8'de çivili.
_SUZULEN_ONEKLER = ("PYTEST_", "MERIDIAN_PROVENANCE")
_YER_SANAL_KOK = "__SANAL_KOK__"
_YER_GOZLEM = "__GOZLEM__"


def _alt_oturum_ortami(ust, sanal_kok: str) -> dict[str, str]:
    """Alt oturumun ortamı: üst ortamdan miras, `_SUZULEN_ONEKLER` hariç; kök sanal köke çevrilir."""
    ortam = {k: v for k, v in ust.items() if not k.startswith(_SUZULEN_ONEKLER)}
    ortam.update(PYTHONPATH=str(KOK), MERIDIAN_ROOT=sanal_kok, PYTHONDONTWRITEBYTECODE="1")
    return ortam


def _alt_oturum_kos(tmp_path, dosyalar: dict[str, str], *ek_arg: str, eklenti: bool = True):
    """Deponun GERÇEK conftest'iyle bir alt oturum koşar — `eklenti=True` ise `-p tests.conftest`
    (küresel eklenti), değilse conftest'i `dosyalar` içindeki bir `conftest.py` yükler. `dosyalar`
    ad → kaynak; kaynaktaki `__SANAL_KOK__` sanal kökün, `__GOZLEM__` gözlem dizininin repr'ine çevrilir.
    Dönüş: (CompletedProcess, sanal kök, gözlem dizini, JUnit testcase sözlüğü ad → öğe, kuyruk)."""
    sanal_kok = tmp_path / "sanal_kok"
    (sanal_kok / "state").mkdir(parents=True)
    gozlem = tmp_path / "gozlem"
    gozlem.mkdir()
    oturum = tmp_path / "oturum"
    oturum.mkdir()
    ini = oturum / "pytest.ini"
    ini.write_text("[pytest]\n", encoding="utf-8")
    for ad, kaynak in dosyalar.items():
        (oturum / ad).write_text(kaynak.replace(_YER_SANAL_KOK, repr(str(sanal_kok)))
                                 .replace(_YER_GOZLEM, repr(str(gozlem))), encoding="utf-8")
    rapor = tmp_path / "sonuc.xml"
    kosum = subprocess.run(
        [sys.executable, "-m", "pytest", *(("-p", "tests.conftest") if eklenti else ()),
         "-p", "no:cacheprovider",
         "--rootdir", str(oturum), "-c", str(ini), f"--junitxml={rapor}", *ek_arg, str(oturum)],
        cwd=oturum, env=_alt_oturum_ortami(os.environ, str(sanal_kok)),
        capture_output=True, text=True, timeout=180)
    kuyruk = (kosum.stdout + kosum.stderr)[-4000:]
    sonuc = ({tc.get("name"): tc for tc in ET.parse(rapor).getroot().iter("testcase")}
             if rapor.exists() else {})
    return kosum, str(sanal_kok), gozlem, sonuc, kuyruk


def _temiz(tc) -> bool:
    return not (tc.findall("error") or tc.findall("failure") or tc.findall("skipped"))


_ALT_TESTLER = ("test_a_dogrudan_yazan_sizdirir", "test_b_monkeypatch_ile_yazan_temiz",
                "test_c_sonraki_test_geri_yuklenmis_kok_gorur")
_K5_KAYNAK = (
    "import os\n\n\n"
    f"def {_ALT_TESTLER[0]}():\n"
    "    os.environ['MERIDIAN_ROOT'] = '/tmp/x'\n\n\n"
    f"def {_ALT_TESTLER[1]}(monkeypatch):\n"
    "    monkeypatch.setenv('MERIDIAN_ROOT', '/tmp/x')\n\n\n"
    f"def {_ALT_TESTLER[2]}():\n"
    f"    assert os.environ.get('MERIDIAN_ROOT') == {_YER_SANAL_KOK}\n"
)


def test_k5_gercek_conftest_alt_oturumda_bekci_sokumde_atesler(tmp_path, monkeypatch):
    """Sızdıran (a) sökümde KIRMIZI + bekçinin mesajı; monkeypatch'li (b) YEŞİL; sonraki test (c)
    geri yüklenmiş kökü görür; üst sürecin ortamı değişmez. Bekçi gövdesinden `_kok_sizinti_sokum`
    çağrısı silinirse (a) yeşile, (c) kırmızıya döner (mutasyonla gösterildi).
    Üst süreç KÖKEN KİPİNDE koşar (`MERIDIAN_PROVENANCE=1`, `..._OUT` = tmp dosyası): alt oturum o
    kipe GİRMEMELİ — girerse sonda rapor dosyasını yazar ve bu test onu görür (K8'in uçtan ucu)."""
    koken_raporu = tmp_path / "koken_raporu.json"
    monkeypatch.setenv("MERIDIAN_PROVENANCE", "1")
    monkeypatch.setenv("MERIDIAN_PROVENANCE_OUT", str(koken_raporu))
    once = os.environ.get(AD)
    kosum, _sanal, _g, sonuc, kuyruk = _alt_oturum_kos(
        tmp_path, {"test_alt_oturum.py": _K5_KAYNAK})

    # 1 = test kırmızısı. 2/3/4 alt oturumun KENDİSİNİN bozuk olduğu demektir (kullanım/iç hata):
    # o durumda "bekçi ateşledi" hükmü verilemez.
    assert kosum.returncode == 1, kuyruk
    assert os.environ.get(AD) == once
    assert not koken_raporu.exists(), "alt oturum üstün köken kipini devraldı (MERIDIAN_PROVENANCE*)"
    assert set(sonuc) == set(_ALT_TESTLER), kuyruk

    sizdiran = sonuc[_ALT_TESTLER[0]]
    hatalar = sizdiran.findall("error")
    assert len(hatalar) == 1 and not sizdiran.findall("failure"), kuyruk
    mesaj = hatalar[0].get("message", "")
    assert mesaj.startswith("failed on teardown"), mesaj
    assert "ORTAM SIZINTISI" in mesaj and _ALT_TESTLER[0] in mesaj and "'/tmp/x'" in mesaj, mesaj
    for ad in _ALT_TESTLER[1:]:
        tc = sonuc[ad]
        assert not (tc.findall("error") or tc.findall("failure") or tc.findall("skipped")), (ad, kuyruk)


# ==================================================================================================
# K6 — TOPLAMA ZAMANI: MODÜL İÇE AKTARILIRKEN YAZAN MODÜL ADIYLA KIRMIZI, KÖK HEMEN GERİ YÜKLENİR
# ==================================================================================================
# Fonksiyon bekçisi anlık görüntüsünü İLK testten önce alır; modül düzeyinde (içe aktarımda) yazılan
# kök o görüntüye "başlangıç" diye girer ve hiçbir test onu göremez. `pytest_make_collect_report`
# sarmalayıcısı her toplayıcının ÖNCESİNİ/SONRASINI ölçer: değişiklik toplayıcının toplama raporunu
# KIRMIZIYA çevirir (düğüm kimliği = modül yolu), kökü o anda geri yükler — sonraki modül temiz kökle
# içe aktarılır. `--continue-on-collection-errors` yalnız "sonraki modül temiz kökü gördü" ölçümü
# içindir; bayraksız oturumda aynı kırmızı toplama raporu pytest'in olağan "N error during
# collection" kesintisidir.
# İKİ KAYIT KİPİ (pytest 9.1.1'de ÖLÇÜLDÜ, 2026-09-30): `-p tests.conftest` kancaları KÜRESEL kaydeder
# (Session ve kök dizin toplayıcısı da sarılır). Gerçek suite'te ise `tests/conftest.py` bir CONFTEST
# eklentisidir ve toplama kancaları YOLA BAĞLIDIR (`Session.gethookproxy`: yalnız kendi dizini
# altındaki toplayıcılar). `conftest` kipi aynı kancaları alt oturumun kendi `conftest.py`sinden
# (ithal, kopya DEĞİL) kaydeder — yani suite'in gerçek kayıt biçimini ölçer.
_K6_CONFTEST_KANCALARI = (
    "from tests.conftest import (  # noqa: F401 — ithal: kancalar conftest eklentisi olarak kaydolur\n"
    "    pytest_collection_finish, pytest_make_collect_report, pytest_sessionfinish,\n"
    "    pytest_sessionstart, pytest_terminal_summary)\n")
_K6_SIZDIRAN = "test_a_toplamada_sizdirir"
_K6_SONRAKI = "test_b_geri_yuklenmis_kok_gorur"
_K6_DOSYALAR = {
    f"{_K6_SIZDIRAN}.py": (
        "import os\n\n"
        "os.environ['MERIDIAN_ROOT'] = '/tmp/toplama'\n\n\n"
        "def test_a_hic_kosmaz():\n"
        "    pass\n"),
    "test_b_sonraki_modul.py": (
        "import os\n\n"
        "TOPLAMADA = os.environ.get('MERIDIAN_ROOT')\n\n\n"
        f"def {_K6_SONRAKI}():\n"
        f"    assert TOPLAMADA == {_YER_SANAL_KOK}\n"
        f"    assert os.environ.get('MERIDIAN_ROOT') == {_YER_SANAL_KOK}\n"),
}


@pytest.mark.parametrize("kip", ["eklenti", "conftest"])
def test_k6_toplamada_sizdiran_modul_adiyla_kirmizi_ve_kok_geri_yuklenir(tmp_path, kip):
    dosyalar = dict(_K6_DOSYALAR)
    if kip == "conftest":
        dosyalar["conftest.py"] = _K6_CONFTEST_KANCALARI
    kosum, _sanal, _g, sonuc, kuyruk = _alt_oturum_kos(
        tmp_path, dosyalar, "--continue-on-collection-errors", eklenti=(kip == "eklenti"))

    assert kosum.returncode == 1, kuyruk
    # Sızdıran modülün testi TOPLANMADI (rapor kırmızı → çocuk düğüm yok); sonraki modül koştu.
    assert set(sonuc) == {_K6_SIZDIRAN, _K6_SONRAKI}, kuyruk
    hatalar = sonuc[_K6_SIZDIRAN].findall("error")
    assert len(hatalar) == 1 and hatalar[0].get("message") == "collection failure", kuyruk
    metin = hatalar[0].text or ""
    assert "ORTAM SIZINTISI" in metin and f"{_K6_SIZDIRAN}.py" in metin, metin
    assert "'/tmp/toplama'" in metin, metin
    # Sonraki modül İÇE AKTARILIRKEN de, testinde de sanal kökü gördü: geri yükleme toplayıcının
    # hemen ardından yapıldı. Oturum-sonu denetimi aynı sızıntıyı İKİNCİ kez saymaz.
    assert _temiz(sonuc[_K6_SONRAKI]), kuyruk
    assert "ERROR ORTAM SIZINTISI" not in kosum.stdout, kuyruk


# ==================================================================================================
# K7 — OTURUM DÜZEYİ: TOPLAMA KANCASI + MODÜL FİKSTÜRÜ SÖKÜMÜ → GERİ YÜKLE, ÇIKIŞI KIRMIZIYA ÇEK
# ==================================================================================================
# İki kör nokta, tek alt oturumda: (1) `pytest_collection_modifyitems` HİÇBİR toplayıcının içinde
# değildir — K6'nın sarmalayıcısı onu görmez; `pytest_collection_finish` oturum-başı anlık görüntüyle
# kıyaslar (hangi kanca olduğu bilinemez, mesaj bunu söyler). (2) Modül kapsamlı fikstürün SÖKÜMÜ
# fonksiyon bekçisinin sökümünden SONRA koşar; yazdığı kök sonraki testin "önce"sine girer.
# `pytest_sessionfinish` oturum-başı görüntüyle kıyaslar. Testlerin HEPSİ yeşildir: çıkış 1'i
# yalnız oturum denetimi verir. Gözlem: alt oturumun `pytest_unconfigure`i (sessionfinish'ten SONRA
# koşar) kökü dosyaya yazar — geri yüklemenin kanıtı.
_K7_TEST = "test_c_kanca_yazimi_geri_yuklenmis_gorur"
_K7_DOSYALAR = {
    "conftest.py": (
        "import os\n"
        "import pathlib\n\n\n"
        "def pytest_collection_modifyitems(items):\n"
        "    os.environ['MERIDIAN_ROOT'] = '/tmp/kanca'\n\n\n"
        "def pytest_unconfigure(config):\n"
        "    rol = 'isci' if hasattr(config, 'workerinput') else 'ana'\n"
        f"    (pathlib.Path({_YER_GOZLEM}) / rol).write_text(\n"
        "        os.environ.get('MERIDIAN_ROOT') or '(tanımsız)', encoding='utf-8')\n"),
    "test_c_fikstur_sokumde_yazar.py": (
        "import os\n\n"
        "import pytest\n\n\n"
        "@pytest.fixture(scope='module')\n"
        "def _sokumde_yazar():\n"
        "    yield\n"
        "    os.environ['MERIDIAN_ROOT'] = '/tmp/fikstur'\n\n\n"
        f"def {_K7_TEST}(_sokumde_yazar):\n"
        f"    assert os.environ.get('MERIDIAN_ROOT') == {_YER_SANAL_KOK}\n"),
}


def _k7_satirlari(stdout: str) -> dict[str, list[str]]:
    satirlar = [s for s in stdout.splitlines() if s.startswith("ERROR ORTAM SIZINTISI — ")]
    return {
        "hepsi": satirlar,
        "toplama": [s for s in satirlar
                    if s.startswith("ERROR ORTAM SIZINTISI — toplama sonu:") and "'/tmp/kanca'" in s],
        "oturum": [s for s in satirlar
                   if s.startswith("ERROR ORTAM SIZINTISI — oturum sonu:") and "'/tmp/fikstur'" in s],
    }


def test_k7_toplama_kancasi_ve_fikstur_sokumu_oturumu_kirmizi_yapar_ve_geri_yuklenir(tmp_path):
    kosum, sanal, gozlem, sonuc, kuyruk = _alt_oturum_kos(tmp_path, _K7_DOSYALAR)

    assert kosum.returncode == 1, kuyruk
    assert set(sonuc) == {_K7_TEST} and _temiz(sonuc[_K7_TEST]), kuyruk   # toplama sonu geri yükledi
    assert "KÖK ORTAM SIZINTISI" in kosum.stdout, kuyruk
    s = _k7_satirlari(kosum.stdout)
    assert len(s["hepsi"]) == 2 and len(s["toplama"]) == 1 and len(s["oturum"]) == 1, kuyruk
    assert "bilinemez" in s["toplama"][0] and "bilinemez" in s["oturum"][0], s["hepsi"]
    assert (gozlem / "ana").read_text(encoding="utf-8") == sanal       # oturum sonu geri yükledi


def test_k7_xdist_iscisindeki_sizinti_kontrolcuyu_kirmizi_yapar(tmp_path):
    """Otoriter suite `-n 4` koşar: işçinin oturum sonu denetimi kendi çıkış kodunu değiştirse bile
    kontrolcü onu OKUMAZ (xdist işçi çıkış kodunu yalnız kesinti için sorar). Kayıt workeroutput ile
    kontrolcüye taşınır; kontrolcü basar ve çıkışı kırmızıya çeker."""
    kosum, sanal, gozlem, sonuc, kuyruk = _alt_oturum_kos(tmp_path, _K7_DOSYALAR, "-n", "1")

    assert kosum.returncode == 1, kuyruk
    assert set(sonuc) == {_K7_TEST} and _temiz(sonuc[_K7_TEST]), kuyruk
    s = _k7_satirlari(kosum.stdout)
    assert len(s["hepsi"]) == 2 and len(s["toplama"]) == 1 and len(s["oturum"]) == 1, kuyruk
    assert all("[xdist işçisi gw0]" in satir for satir in s["hepsi"]), s["hepsi"]
    assert (gozlem / "isci").read_text(encoding="utf-8") == sanal


# ==================================================================================================
# K8 — ALT OTURUM ORTAM SÜZGECİ (yeniden inceleme N-1)
# ==================================================================================================
def test_k8_alt_oturum_ortami_koken_ve_pytest_degiskenlerini_suzer():
    ust = {"MERIDIAN_PROVENANCE": "1", "MERIDIAN_PROVENANCE_OUT": "/depo/docs/provenance_report.json",
           "PYTEST_XDIST_WORKER": "gw0", "PYTEST_ADDOPTS": "-x", "MERIDIAN_ROOT": "/ust/kok",
           "PATH": "/usr/bin", "MERIDIAN_DB": "off"}
    kopya = dict(ust)
    ortam = _alt_oturum_ortami(ust, "/sanal/kok")
    assert not [k for k in ortam if k.startswith(("MERIDIAN_PROVENANCE", "PYTEST_"))], sorted(ortam)
    assert ortam["PATH"] == "/usr/bin" and ortam["MERIDIAN_DB"] == "off"
    assert ortam["MERIDIAN_ROOT"] == "/sanal/kok"
    assert ortam["PYTHONPATH"] == str(KOK) and ortam["PYTHONDONTWRITEBYTECODE"] == "1"
    assert ust == kopya                                        # üst sözlüğe dokunulmaz

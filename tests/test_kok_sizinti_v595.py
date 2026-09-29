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
# (xdist işçi kimliği, `PYTEST_ADDOPTS`) alt oturuma taşınmaz.
_ALT_TESTLER = ("test_a_dogrudan_yazan_sizdirir", "test_b_monkeypatch_ile_yazan_temiz",
                "test_c_sonraki_test_geri_yuklenmis_kok_gorur")


def _alt_oturum_kaynagi(sanal_kok: str) -> str:
    return (
        "import os\n\n\n"
        f"def {_ALT_TESTLER[0]}():\n"
        "    os.environ['MERIDIAN_ROOT'] = '/tmp/x'\n\n\n"
        f"def {_ALT_TESTLER[1]}(monkeypatch):\n"
        "    monkeypatch.setenv('MERIDIAN_ROOT', '/tmp/x')\n\n\n"
        f"def {_ALT_TESTLER[2]}():\n"
        f"    assert os.environ.get('MERIDIAN_ROOT') == {sanal_kok!r}\n"
    )


def test_k5_gercek_conftest_alt_oturumda_bekci_sokumde_atesler(tmp_path):
    """Sızdıran (a) sökümde KIRMIZI + bekçinin mesajı; monkeypatch'li (b) YEŞİL; sonraki test (c)
    geri yüklenmiş kökü görür; üst sürecin ortamı değişmez. Bekçi gövdesinden `_kok_sizinti_sokum`
    çağrısı silinirse (a) yeşile, (c) kırmızıya döner (mutasyonla gösterildi)."""
    once = os.environ.get(AD)
    sanal_kok = tmp_path / "sanal_kok"
    (sanal_kok / "state").mkdir(parents=True)
    oturum = tmp_path / "oturum"
    oturum.mkdir()
    ini = oturum / "pytest.ini"
    ini.write_text("[pytest]\n", encoding="utf-8")
    dosya = oturum / "test_alt_oturum.py"
    dosya.write_text(_alt_oturum_kaynagi(str(sanal_kok)), encoding="utf-8")
    rapor = tmp_path / "sonuc.xml"
    ortam = {k: v for k, v in os.environ.items() if not k.startswith("PYTEST_")}
    ortam.update(PYTHONPATH=str(KOK), MERIDIAN_ROOT=str(sanal_kok), PYTHONDONTWRITEBYTECODE="1")

    kosum = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "tests.conftest", "-p", "no:cacheprovider",
         "--rootdir", str(oturum), "-c", str(ini), f"--junitxml={rapor}", str(dosya)],
        cwd=oturum, env=ortam, capture_output=True, text=True, timeout=180)
    kuyruk = (kosum.stdout + kosum.stderr)[-3000:]

    # 1 = test kırmızısı. 2/3/4 alt oturumun KENDİSİNİN bozuk olduğu demektir (kullanım/iç hata):
    # o durumda "bekçi ateşledi" hükmü verilemez.
    assert kosum.returncode == 1, kuyruk
    assert os.environ.get(AD) == once
    sonuc = {tc.get("name"): tc for tc in ET.parse(rapor).getroot().iter("testcase")}
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

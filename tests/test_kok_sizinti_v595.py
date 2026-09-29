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
"""
from __future__ import annotations

import os

import pytest

from tests.conftest import _KOK_ORTAM_ADI, _kok_sizinti_denetle, _kok_sizinti_sokum

AD = "MERIDIAN_ROOT"
BEKCI = "_kok_sizinti_bekcisi"


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

"""EDG-2026-056 dedektörünün DAVRANIŞ testleri (kapsam testi — otoriter suite'e girmez:
pyproject testpaths=["tests"]). Donuk tanım dosyasındaki kuralın kodda birebir yaşadığını sınar."""
from __future__ import annotations
import pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import tara  # noqa: E402


def _seri(kapanislar, hacimler):
    t = [f"2020-01-{i + 1:02d}" for i in range(len(kapanislar))]
    return t, kapanislar, hacimler


def test_temiz_2ye1_bolunme_hacim_teyitli_YAKALANIR():
    t, c, v = _seri([100.0, 100.0, 50.0, 50.0], [1e6, 1e6, 2e6, 1e6])
    ad = tara.adaylar("T", t, c, v, tara.TANIM)
    assert [a["tarih"] for a in ad] == ["2020-01-03"], ad
    assert abs(ad[0]["r"] - 2.0) < 1e-9 and ad[0]["eslesen_oran"] == "2:1"


def test_hacim_teyidi_YOKSA_aday_degil():
    # fiyat tam 2:1 ama hacim sabit -> vr/r = 0.5 < 1/1.5 -> teyit yok (kart kill: hacim atlanamaz)
    t, c, v = _seri([100.0, 100.0, 50.0, 50.0], [1e6, 1e6, 1e6, 1e6])
    assert tara.adaylar("T", t, c, v, tara.TANIM) == []


def test_oran_tolerans_disindaysa_aday_degil():
    # r = 100/48.9 = 2.045 -> |r/2 - 1| = %2.25 > %2
    t, c, v = _seri([100.0, 100.0, 48.9, 48.9], [1e6, 1e6, 2.05e6, 1e6])
    assert tara.adaylar("T", t, c, v, tara.TANIM) == []


def test_kucuk_hareket_aday_degil():
    t, c, v = _seri([100.0, 100.0, 98.5, 98.5], [1e6, 1e6, 1e6, 1e6])
    assert tara.adaylar("T", t, c, v, tara.TANIM) == []


def test_ters_bolunme_1e2_yakalanir():
    t, c, v = _seri([50.0, 50.0, 100.0, 100.0], [2e6, 2e6, 1e6, 1e6])
    ad = tara.adaylar("T", t, c, v, tara.TANIM)
    assert [a["eslesen_oran"] for a in ad] == ["1:2"], ad


def test_sifir_hacim_teyit_edilemez_ve_SAYILIR():
    t, c, v = _seri([100.0, 100.0, 50.0, 50.0], [1e6, 0.0, 2e6, 1e6])
    ad = tara.adaylar("T", t, c, v, tara.TANIM)
    assert ad == []
    assert tara.SAYAC["hacim_olculemedi"] >= 1


def test_donuk_tanim_dosyasi_kodla_ayni():
    assert tara.TANIM["fiyat_tolerans_rel"] == 0.02
    assert tara.TANIM["hacim_teyidi"]["F_birincil"] == 1.5

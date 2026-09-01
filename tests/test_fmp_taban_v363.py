"""v363 — FMP taban adresi env'den okunur (TSK-089 Faz 2, kapı yönlendirmesi).

NEDEN ÇİVİ: `BASE` sabit kaldığı sürece FMP trafiği kapıdan (APISIX) geçirilemez; env'e
açmak yönlendirmeyi dağıtımda yapılabilir kılar. Üç şeyi birden çivileriz:
  1. env YOKKEN varsayılan davranış DEĞİŞMEZ (yönlendirme opt-in'dir, sessiz sapma yok),
  2. env varken sondaki `/` KIRPILIR (f"{BASE}/..." bitiştirmesi çift-bölü üretirdi),
  3. tüketim noktası TEK'tir — ikinci bir bitiştirme noktası doğarsa (kırpma sözleşmesi
     orada tekrarlanmadan) çivi öter. Çapa SEMBOL (`BASE`) ve KAYNAK METNİ desenidir,
     satır numarası değil (CLAUDE.md §2: satır kayar, çapa çürür).

Modül yeniden yükleme (importlib.reload) kullanılır çünkü BASE modül düzeyinde bir kez
hesaplanır. Her test sonunda modül ORİJİNAL env ile yeniden yüklenip bırakılır — başka
testler kirlenmesin. `monkeypatch.undo()` KULLANILMAZ (autouse fixture'ları da geri alır).
"""
from __future__ import annotations

import importlib
import os
import pathlib

import pytest

from meridian.adapters import fmp as _fmp

ENV_ADI = "MERIDIAN_FMP_BASE"
VARSAYILAN = "https://financialmodelingprep.com/stable"
KAYNAK = pathlib.Path(_fmp.__file__)


@pytest.fixture()
def temiz_birak():
    """Test bitince modülü ORİJİNAL env ile yeniden yükler.

    monkeypatch'e GÜVENMEZ: fixture sökümü LIFO'dur ve monkeypatch bizden sonra sökülür,
    yani biz yeniden yüklerken env hâlâ yamalı olabilirdi. Bu yüzden orijinal değeri
    burada kendimiz tutup os.environ üzerinden geri koyuyoruz.
    """
    orijinal = os.environ.get(ENV_ADI)
    yield
    if orijinal is None:
        os.environ.pop(ENV_ADI, None)
    else:
        os.environ[ENV_ADI] = orijinal
    importlib.reload(_fmp)


def test_env_yokken_varsayilan_taban_degismez(monkeypatch, temiz_birak):
    """Yönlendirme OPT-IN: env yoksa canlı davranış bugünküyle bayt-özdeş."""
    monkeypatch.delenv(ENV_ADI, raising=False)
    modul = importlib.reload(_fmp)
    assert modul.BASE == VARSAYILAN


def test_env_varken_taban_yonlendirilir_ve_sondaki_bolu_kirpilir(monkeypatch, temiz_birak):
    """Sondaki `/` kırpılır — yoksa f"{BASE}/quote" çift-bölü ("//quote") üretir."""
    monkeypatch.setenv(ENV_ADI, "http://127.0.0.1:9080/fmp/")
    modul = importlib.reload(_fmp)
    assert modul.BASE == "http://127.0.0.1:9080/fmp"


def test_taban_tuketim_noktasi_tektir():
    """Kırpma sözleşmesi tek yerde tutulur: `f"{BASE}/` deseni kaynakta TAM 1 kez geçer.

    İkinci bir bitiştirme noktası doğarsa bu çivi öter — o nokta kırpma/yönlendirme
    sözleşmesini sessizce ıskalayabilir.
    """
    metin = KAYNAK.read_text(encoding="utf-8")
    assert metin.count('f"{BASE}/') == 1, (
        f'fmp.py içinde f"{{BASE}}/ deseni {metin.count(chr(102) + chr(34) + "{BASE}/")} kez '
        "geçiyor — tüketim noktası TEK olmalı (kırpma sözleşmesi tek yerde)."
    )

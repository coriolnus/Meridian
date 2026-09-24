"""test_denetci_yedek_rota_v537.py — denetçi üst-akım arızasında TEK yedek-rota çağrısı (TSK-196 D2).

VAKA (A1, 2026-09-14→09-22): 7 `*_denetci_ustakim_hatasi` olayı / 5 koşum, hepsi rota `hizli`,
Nvidia "Service temporarily overloaded" 502/503 HTTP 200 gövdesinde — kapının `fallback_strategy`
bunu görmez. 5 s sonraki tek yeniden deneme 3/5 kurtardı; 2 koşumda denetim düştü. Politika:
aşırı yükte bekleme uzar (D1, v486 B5/B5b) ve ikinci düşüşte TEK çağrı `danisma` rotasına gider (D2).
"""
from __future__ import annotations

import pytest

from ops import denetci_rota
from tests.test_denetci_rota_reasoning_v486 import (  # tek-kaynak: sahte kapı/zaman/rota fikstürleri
    ONEK, _jetonlu, _kapiyi_bagla, _olcum, _ustakim_govdesi, rota, zaman)  # noqa: F401
from tests.test_soul_denetimi_v385 import _olaylar


def test_Y1_iki_dususten_sonra_yedek_rota_KURTARIR(rota, monkeypatch, zaman):
    kapi = _kapiyi_bagla(monkeypatch, _ustakim_govdesi(kod=503), _ustakim_govdesi(kod=503),
                         _jetonlu("YEDEKTEN METİN"))
    assert rota.cagir("soru") == "YEDEKTEN METİN"
    assert len(kapi.cagrilar) == 3, kapi.urller
    assert kapi.urller[0].endswith("/llm/hizli/v1/chat/completions"), kapi.urller
    assert kapi.urller[1] == kapi.urller[0], "yeniden deneme AYNI rotaya gider"
    assert kapi.urller[2].endswith("/llm/v1/chat/completions"), kapi.urller
    olcum = _olcum()[-1]
    assert (olcum.get("rota"), olcum.get("yeniden_deneme")) == ("danisma", 2), olcum


def test_Y2_yedege_gecis_ADIYLA_olay_yazar(rota, monkeypatch, zaman):
    _kapiyi_bagla(monkeypatch, _ustakim_govdesi(kod=503), _ustakim_govdesi(kod=502), _jetonlu("METİN"))
    rota.cagir("soru")
    gecis = _olaylar(f"{ONEK}_denetci_rota_yedege_gecti")
    assert len(gecis) == 1, gecis
    assert (gecis[0].get("rota"), gecis[0].get("yedek"), gecis[0].get("kod")) == ("hizli", "danisma", 502)


def test_Y3_ilk_yeniden_deneme_kurtarirsa_yedege_GECILMEZ(rota, monkeypatch, zaman):
    kapi = _kapiyi_bagla(monkeypatch, _ustakim_govdesi(kod=503), _jetonlu("METİN"))
    assert rota.cagir("soru") == "METİN"
    assert len(kapi.cagrilar) == 2
    assert not _olaylar(f"{ONEK}_denetci_rota_yedege_gecti")


def test_Y4_yapilandirilmis_rota_zaten_yedekse_ucuncu_cagri_YOK(rota, monkeypatch, zaman):
    monkeypatch.setenv(denetci_rota.DENETIM_ROTA_ENV, denetci_rota.YEDEK_DENETIM_ROTASI)
    kapi = _kapiyi_bagla(monkeypatch, _ustakim_govdesi(kod=503), _ustakim_govdesi(kod=503))
    with pytest.raises(RuntimeError) as hata:
        rota.cagir("soru")
    assert len(kapi.cagrilar) == 2, kapi.urller
    assert "yeniden deneme de düştü" in str(hata.value)
    assert not _olaylar(f"{ONEK}_denetci_rota_yedege_gecti")


def test_Y5_yedek_de_duserse_hata_ADIYLA_ve_bekleme_tek(rota, monkeypatch, zaman):
    _kapiyi_bagla(monkeypatch, _ustakim_govdesi(kod=503), _ustakim_govdesi(kod=503), _ustakim_govdesi(kod=503))
    with pytest.raises(RuntimeError) as hata:
        rota.cagir("soru")
    assert "yedek rota da düştü" in str(hata.value) and "danisma" in str(hata.value)
    assert zaman.uykular == [denetci_rota.USTAKIM_ASIRI_YUK_BEKLEME_SN], "yedeğe geçişte İKİNCİ bekleme yok"


def test_Y6_bekleme_sinifi_kod_bicimine_duyarsiz():
    assert denetci_rota.ustakim_bekleme_sn({"code": 503}) == denetci_rota.USTAKIM_ASIRI_YUK_BEKLEME_SN
    assert denetci_rota.ustakim_bekleme_sn({"code": "502"}) == denetci_rota.USTAKIM_ASIRI_YUK_BEKLEME_SN
    assert denetci_rota.ustakim_bekleme_sn({"code": 429}) == denetci_rota.USTAKIM_YENIDEN_DENEME_SN
    assert denetci_rota.ustakim_bekleme_sn({}) == denetci_rota.USTAKIM_YENIDEN_DENEME_SN

"""test_edg067_dilim_v366.py — EDG-067 süpürme dilimleyicisinin saf çekirdeği (2026-09-02).

VAKA: tek-chunk 35K-token belgeler Nvidia free ucunda boyut-sınıfı reddi yiyor (5/5 ölçüldü,
2026-09-01); korpusta 9 dev (60KB+, tepe 224KB) var ve ana koşum onları hiç geçiremeyecek.
Donuk korpus betiği (manifest_uret.py) DEĞİŞMEZ (kart artefaktı) — süpürme, ROADMAP %237
emsalindeki kimlik şemasıyla devleri bölüm sınırlarından dilimler.

SÖZLEŞME (dilimle):
  * Girdi metin `^## ` başlıklarından bölünür; ardışık bölümler ESİK baytı aşmadan tek dilimde
    toplanır (açgözlü paketleme — dilim sayısı gereksiz şişmez).
  * Tek başına eşiği aşan bölüm boş satır (paragraf) sınırından zorla bölünür — hiçbir dilim
    esnek tavanı (esik*1.5) aşamaz.
  * KAYIPSIZLIK: dilimlerin birleşimi == girdi (bayt bayt). Kayıp dilimleme sessiz veri
    kaybıdır — Yasa 6'nın ingest hâli.
  * Kimlik: `{yol}%23dilim-{i}` (1-tabanlı) + her dilim ilk bölüm başlığını üstveri olarak taşır.
  * Başlıksız (frontmatter/önsöz) baş kısım ilk dilime gider; `## ` İÇERİK satırı olarak
    (kod bloğu içinde) geçen metin başlık sayılmaz — fence içi bölünme yasak.
"""
from __future__ import annotations

import pathlib

from tests.conftest import betikten_modul_yukle

_yol = pathlib.Path(__file__).resolve().parent.parent / \
    "research/olcumler/edg067_hindsight_faz1/dilim_sup.py"
dilim_sup = betikten_modul_yukle(_yol, "dilim_sup")


def _birlestir(dilimler):
    return "".join(d["metin"] for d in dilimler)


def test_kucuk_metin_tek_dilim():
    m = "# Baslik\n\ngovde\n\n## A\n\niçerik\n"
    d = dilim_sup.dilimle(m, esik=10_000)
    assert len(d) == 1
    assert _birlestir(d) == m
    assert d[0]["bolum"] == "A" or d[0]["bolum"] == ""  # tek dilimde ilk başlık ya da önsöz


def test_bolum_sinirlarindan_boler_ve_kayipsiz():
    bolumler = [f"## Bolum{i}\n\n" + ("x" * 4000) + "\n\n" for i in range(6)]
    m = "onsoz\n\n" + "".join(bolumler)
    d = dilim_sup.dilimle(m, esik=10_000)
    assert len(d) >= 3, [len(x["metin"]) for x in d]
    assert _birlestir(d) == m
    # her dilim (zorla bölünme yokken) `## ` ile ya da önsözle başlar
    assert d[0]["metin"].startswith("onsoz")
    for x in d[1:]:
        assert x["metin"].startswith("## "), x["metin"][:40]
    # esnek tavan: hiçbir dilim esik*1.5'i aşmaz
    assert all(len(x["metin"].encode()) <= 15_000 for x in d)


def test_dev_tek_bolum_paragraftan_zorla_bolunur():
    m = "## Tek\n\n" + "\n\n".join("p" * 3000 for _ in range(8)) + "\n"
    d = dilim_sup.dilimle(m, esik=10_000)
    assert len(d) >= 2
    assert _birlestir(d) == m
    assert all(len(x["metin"].encode()) <= 15_000 for x in d)


def test_fence_icindeki_basliga_bolunmez():
    m = "## Gercek\n\n" + "önce\n\n```\n## sahte baslik\n```\n\nsonra\n\n" + \
        "## Ikinci\n\n" + "y" * 9000 + "\n"
    d = dilim_sup.dilimle(m, esik=10_000)
    assert _birlestir(d) == m
    for x in d:
        govde = x["metin"]
        if govde.startswith("## sahte"):
            raise AssertionError("fence içi başlıktan bölünmüş")


def test_kimlik_semasi_roadmap_emsali():
    kimlikler = dilim_sup.dilim_kimlikleri("docs/BUYUK.md", 3)
    assert kimlikler == ["docs/BUYUK.md%23dilim-1",
                        "docs/BUYUK.md%23dilim-2",
                        "docs/BUYUK.md%23dilim-3"]

"""v337 · TAHTA HİJYENİ — `ROADMAP.md` §2'de kapalı ya da işaretsiz satır duramaz.

ÖLÇÜLEN BORÇ (2026-08-30 bakım turu): §2 TAHTA'nın açık bölümleri (H0/H1/H2/DİK DURUM) 48 satır
taşıyordu ve bunların **25'i kapalı, 18'i işaretsizdi** — yani tahtaya bakan bir tur satırların
yarısından fazlasını boşuna okuyordu. Bedeli soyut değil: 2026-08-24 denetimi "tahtanın bakım
borcu 27 satır" dedi ve **o gece iki ajan turu zaten kapalı kalemlere gitti**. Borç altı gün
ödenmedi çünkü her tur satırı taşımak yerine üstüne "bu satır bayat" banner'ı ekledi; banner'lar
üst üste bindi (2026-08-13 · 08-22 · 08-23 · 08-24) ve tahtanın kendisi okunmaz hâle geldi.

BU DOSYA NEYİ ÇİVİLER
---------------------
A. **KAPALI SATIR TAHTADA DURAMAZ.** §2'nin H0/H1/H2/DİK DURUM tablolarında `durum == "kapali"`
   ayrıştırılan satır bulunamaz. Kapanan satır AYNI turda `§8.T TAHTA ARŞİVİ`ne taşınır
   (SİLİNMEZ — §0: *tarihçe-koru, silme yok*).

B. **İŞARETSİZ SATIR DA DURAMAZ.** `belirsiz` "açık" DEĞİLDİR; ucun kendi sözleşmesinin cümlesi
   budur (`api._roadmap_ayristir` → `durum_kapsam`). Bir tahta satırı hangi durumda olduğunu
   SÖYLEMEK zorundadır: rozet alanında `AÇIK` / `BLOKE` / `ASKIDA` / kapanış imi. Bu ayak olmadan
   A ayağı tek başına kandırılabilirdi — kapalı satırı işaretsiz bırakmak testi yeşil yapardı.

C. **KAPI BOŞA DÜŞEMEZ (yanlış-yeşil kapatması).** Bölüm başlıkları değişirse ya da §2 bir gün
   tablo taşımaz olursa yukarıdaki iki iddia "hiçbir satır bulamadım" diye SESSİZCE geçerdi.
   Çivi önce **tahtanın var olduğunu** ölçer: en az üç açık alt bölüm ve en az on satır.

D. **ARŞİV GERÇEKTEN VAR.** Taşınan satırlar bir yere gitmiş olmalı: `§8.T` başlığı belgede
   bulunmalı ve içinde kapalı satırlar DURMALI (arşivin işi zaten onları taşımaktır).

E. **NEGATİF KONTROL (çivi ısırıyor mu).** Aynı yardımcı, sentetik bir tahtaya karşı koşulur:
   kapalı bir satır + işaretsiz bir satır konur ve yardımcı ikisini de YAKALAMAK zorundadır.
   Yeşil bir çivinin doğru sebeple yeşil olduğu ancak böyle gösterilir (CLAUDE.md §6).
"""
import pathlib

import pytest

from meridian import api, config

ACIK_BOLUM_ONEKLERI = ("H0 —", "H1 —", "H2 —", "DİK DURUM")


def _yuk(metin: str) -> dict:
    return api._roadmap_ayristir(metin, yol="sanal.md", bayt=len(metin.encode()),
                                 mtime=None, tam=True)


def _gez(bolum: dict):
    yield bolum
    for alt in bolum["alt_bolumler"]:
        yield from _gez(alt)


def _tahta_satirlari(yuk: dict) -> list[tuple[str, dict]]:
    """§2'nin AÇIK alt bölümlerindeki tablo satırları — (alt bölüm başlığı, satır)."""
    bulunan = []
    for kok in yuk["bolumler"]:
        if (kok.get("no") or "") != "§2":
            continue
        for b in _gez(kok):
            bas = (b.get("ham_baslik") or b.get("baslik") or "").lstrip("# ").strip()
            if not bas.startswith(ACIK_BOLUM_ONEKLERI):
                continue
            for t in b["tablolar"]:
                for s in t["satirlar"]:
                    bulunan.append((bas, s))
    return bulunan


def _ilk_hucre(s: dict) -> str:
    return (s["hucreler"][0] if s["hucreler"] else "")[:100]


@pytest.fixture(scope="module")
def tahta():
    metin = (pathlib.Path(config.ROOT) / "ROADMAP.md").read_text(encoding="utf-8")
    return _tahta_satirlari(_yuk(metin))


def test_c_kapi_bosa_dusmuyor_tahta_gercekten_var(tahta):
    """Önce ölç: aşağıdaki iki iddia BOŞ bir kümede de geçerdi."""
    bolumler = {b for b, _ in tahta}
    assert len(bolumler) >= 3, f"§2'nin açık alt bölümleri bulunamadı — başlıklar değişmiş olabilir: {bolumler}"
    assert len(tahta) >= 10, f"tahtada yalnız {len(tahta)} satır bulundu; ayrıştırma kopmuş olabilir"


def test_a_tahtada_kapali_satir_yok(tahta):
    kapali = [(b, _ilk_hucre(s)) for b, s in tahta if s["durum"] == "kapali"]
    assert not kapali, (
        "§2 TAHTA'da KAPALI satır var — kapanan kalem tahtada durmaz, AYNI turda `§8.T TAHTA "
        "ARŞİVİ`ne taşınır (silinmez). Satırın üstüne 'bu satır bayat' notu düşmek TAŞIMA "
        "DEĞİLDİR; bu deponun ölçülmüş `Ö-49 bayat-beyan` sınıfıdır ve tur harcatır.\n"
        + "\n".join(f"  · [{b}] {h}" for b, h in kapali))


def test_b_tahtada_isaretsiz_satir_yok(tahta):
    isaretsiz = [(b, _ilk_hucre(s)) for b, s in tahta if s["durum"] == "belirsiz"]
    assert not isaretsiz, (
        "§2 TAHTA'da İŞARETSİZ satır var. `belirsiz` 'açık' DEĞİLDİR — ucun kendi sözleşmesi "
        "böyle der; işaretsiz bırakmak durumu ÖLÇMEDEN tahtaya yazmaktır. Satır rozet alanında "
        "`AÇIK` / `BLOKE` / `ASKIDA` taşımalı.\n"
        + "\n".join(f"  · [{b}] {h}" for b, h in isaretsiz))


def test_d_tasinanlar_arsivde_duruyor():
    metin = (pathlib.Path(config.ROOT) / "ROADMAP.md").read_text(encoding="utf-8")
    assert "### §8.T — TAHTA ARŞİVİ" in metin, "tahtadan çıkan satırların gideceği arşiv bölümü yok"
    ars = metin.split("### §8.T — TAHTA ARŞİVİ", 1)[1]
    yuk = _yuk("# k\n\n## §8 ARŞİV\n\n### §8.T — TAHTA ARŞİVİ" + ars)
    kapali = sum(1 for kok in yuk["bolumler"] for b in _gez(kok)
                 for t in b["tablolar"] for s in t["satirlar"] if s["durum"] == "kapali")
    assert kapali >= 20, f"§8.T'de yalnız {kapali} kapalı satır var — taşıma yapılmamış olabilir"


def test_e_negatif_kontrol_civi_gercekten_isiriyor():
    """Kasıtlı kırmızı: yardımcı, kapalı VE işaretsiz satırı yakalamak zorunda."""
    sentetik = (
        "# k\n\n## §2 TAHTA\n\n"
        "#### H0 — TASARIM ARTEFAKTI YOK\n\n"
        "| kalem | WP | not |\n|---|---|---|\n"
        "| ~~`X` bir kalem~~ **H6 ✅ KAPANDI 2026-01-01** | WP1 | tarihçe |\n"
        "| `Y` rozetsiz kalem | WP1 | gerekçe düzyazısı |\n"
        "| **AÇIK** `Z` düzgün kalem | WP1 | gerekçe |\n"
    )
    satirlar = _tahta_satirlari(_yuk(sentetik))
    durumlar = [s["durum"] for _b, s in satirlar]
    assert durumlar == ["kapali", "belirsiz", "acik"], durumlar

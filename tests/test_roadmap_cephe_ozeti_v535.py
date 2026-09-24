"""test_roadmap_cephe_ozeti_v535.py — ROADMAP cephe bağı ve §3 CEPHE ÖZETİ ayrışma çivileri (TSK-216).

VAKA (2026-09-24): açık 55 TSK'nın 43'ünde cephe (PRG) bağı yoktu — 2026-09-01 madde standardı
(`docs/TASARIM-ROADMAP-STANDART-2026-09-01.md`, v351) TSK'ya cephe alanı koymadı ve yeni işin tamamı
cephesiz birikti; §3 özet tablosu 2026-08-13'ten beri elle tutuluyor ve bayattı. Düzeltme iki parça:
  (a) her açık kalem cephesini BEYAN eder — başlık biçiminde `  Ref: PRG-NN · …`, §2 tahta satırında
      `(WP: WPn)`; bu dosya beyanı ZORLAR (cephesiz yeni kalem doğduğu gün kırmızı);
  (b) §3'teki cephe özeti `ops/roadmap_cephe_ozeti.py` ile kalemlerden TÜRETİLİR; bu dosya diskteki
      bloğun üretici çıktısıyla AYNI olduğunu ölçer (tek-kaynak yasası: elle düzenleme ayrışır).
"""
from __future__ import annotations

import pathlib

from tests.conftest import betikten_modul_yukle

KOK = pathlib.Path(__file__).resolve().parents[1]
BETIK = KOK / "ops" / "roadmap_cephe_ozeti.py"
ROADMAP = KOK / "ROADMAP.md"


def _mod():
    return betikten_modul_yukle(BETIK, "roadmap_cephe_ozeti_v535")


#: Sentetik yol haritası — iki yüzey (başlık + tahta), kapalı kalem, `(bkz.)` satırı, arşiv bölümü.
SENTETIK = """\
## §0 SÖZLEŞME

## §2 TAHTA

| id | ad | durum |
|---|---|---|
| TSK-901 | tahta kalemi (WP: WP1) | GATED(örneklem) |
| TSK-902 | etiketsiz tahta kalemi | QUEUED |
| TSK-901 | (bkz. TSK-901 — kayıt satırı) (WP: WP3) | ACTIVE |
| TSK-903 | kapanmış tahta kalemi (WP: WP1) | DONE(2026-09-01) |
| TSK-905 | (bkz. TSK-905 — başka bir kalemin kayıt satırı, tek başına) | ACTIVE |

## §3 CEPHELER

<!-- CEPHE-OZETI:BASLA -->
bayat içerik
<!-- CEPHE-OZETI:BITIR -->

### PRG-01 — İcra ve Friksiyon 🔴
### PRG-02 — Sermaye ve Koruma 🔴 **[2026-09-24: YENİDEN AÇILDI]**
### PRG-03 — Öğrenme Döngüsü _(not)_

## §4 ÖNERİ HAVUZU

- **[TSK-910] bağlı kalem** — status: ACTIVE · born: 2026-09-24 · owner: rol1 · size: S · trigger: —
  What: iş
  Ref: PRG-02 · kaynak
- **[TSK-911] cephesiz kalem** — status: QUEUED · born: 2026-09-24 · owner: rol1 · size: S · trigger: —
  What: iş, metinde PRG-01 geçer ama beyan değildir
  Ref: kaynak · PRG-01 ortada
- **[TSK-912] tanımsız cepheli kalem** — status: GATED(sayaç) · born: 2026-09-24 · owner: rol1 · size: S · trigger: sayaç dolunca
  Ref: PRG-99 · kaynak
- **[TSK-913] kapanmış cephesiz kalem** — status: DONE(2026-09-20) · born: 2026-09-01 · owner: rol1 · size: S · trigger: —
  Ref: kaynak
- **[TSK-914] Ref'siz kalem** — status: OPERATOR · born: 2026-09-24 · owner: rol1 · size: S · trigger: —
  What: iş

## §6 KARTLAR

- **[TSK-920] §6'da cephesiz** — status: ACTIVE · born: 2026-09-24 · owner: rol1 · size: S · trigger: —

## §8 ARŞİV

**[TSK-930] arşivde cephesiz** — status: ACTIVE · born: 2026-09-24 · owner: rol1 · size: S · trigger: —
- **[TSK-931] arşivde liste imli** — status: ACTIVE · born: 2026-09-24 · owner: rol1 · size: S · trigger: —
"""


# ---------------------------------------------------------------------------------------------
# GERÇEK DOSYA
# ---------------------------------------------------------------------------------------------

def test_T1_gercek_roadmap_her_acik_kalem_tanimli_cepheye_bagli():
    """(a) Beyan zorlaması. Pozitif kontrol: açık kalem sayısı 50'nin altına düşerse ayrıştırıcı
    çürümüş olabilir — boş liste 'ihlal yok' demek değildir (2026-09-24: 56 açık kalem)."""
    m = _mod()
    metin = ROADMAP.read_text(encoding="utf-8")
    assert len(m.acik_kalemler(metin)) >= 50, "açık kalem sayımı çöktü — ayrıştırıcı ROADMAP biçimini kaçırıyor"
    assert m.ihlaller(metin) == []


def test_T2_gercek_roadmap_ozet_blogu_ureticiyle_AYNI():
    """(b) Ayrışma çivisi. Kırmızıysa: `python ops/roadmap_cephe_ozeti.py --yaz` (elle düzenleme yok)."""
    m = _mod()
    metin = ROADMAP.read_text(encoding="utf-8")
    blok = m.blok_icerigi(metin)
    assert blok is not None, "ROADMAP §3'te CEPHE-OZETI blok işaretleri yok"
    assert blok == m.ozet_tablosu(metin)


def test_T3_gercek_roadmap_cephe_adlari_on_bes_ve_ada_rozet_girmez():
    m = _mod()
    adlar = m.cephe_adlari(ROADMAP.read_text(encoding="utf-8"))
    assert len(adlar) >= 15
    assert adlar["PRG-02"] == "Sermaye ve Koruma"
    assert all(not any(k.strip() in ad for k in m.AD_KESICILER) for ad in adlar.values()), adlar


# ---------------------------------------------------------------------------------------------
# SENTETİK — davranış
# ---------------------------------------------------------------------------------------------

def test_T4_iki_yuzey_sayilir_kapali_bkz_ve_taranmayan_bolumler_elenir():
    m = _mod()
    kalemler = {k["tsk"]: k for k in m.acik_kalemler(SENTETIK)}
    assert sorted(kalemler) == ["TSK-901", "TSK-902", "TSK-910", "TSK-911", "TSK-912", "TSK-914"]
    assert kalemler["TSK-901"]["yuzey"] == "tahta" and kalemler["TSK-901"]["cephe"] == "PRG-01"
    assert kalemler["TSK-901"]["durum"] == "GATED", "(bkz.) satırı ilk kaydın durumunu ezmemeli"
    assert kalemler["TSK-902"]["cephe"] is None
    assert kalemler["TSK-910"]["cephe"] == "PRG-02"
    assert kalemler["TSK-912"]["durum"] == "GATED"


def test_T5_cephe_yalniz_Ref_BASINDAN_okunur_metin_anistirmasi_sayilmaz():
    m = _mod()
    kalemler = {k["tsk"]: k for k in m.acik_kalemler(SENTETIK)}
    assert kalemler["TSK-911"]["cephe"] is None
    assert kalemler["TSK-914"]["cephe"] is None


def test_T6_ihlaller_cephesiz_ve_tanimsiz_cepheyi_ADIYLA_soyler():
    m = _mod()
    sorunlar = m.ihlaller(SENTETIK)
    assert len(sorunlar) == 4, sorunlar
    metin = "\n".join(sorunlar)
    for tsk in ("TSK-902", "TSK-911", "TSK-912", "TSK-914"):
        assert tsk in metin
    assert "PRG-99" in metin and "tanımlı bir" in metin
    assert "(WP: WPn)" in metin and "Ref:" in metin


def test_T7_ozet_tablosu_sayimlari_ve_kalemsiz_cephe_satiri():
    m = _mod()
    satirlar = {s.split(" | ")[0]: s for s in m.ozet_tablosu(SENTETIK).splitlines() if s.startswith("| ")}
    assert satirlar["| PRG-01 İcra ve Friksiyon"].startswith("| PRG-01 İcra ve Friksiyon | 1 | 0 | 0 | 1 | 0 | 0 | TSK-901 |")
    assert satirlar["| PRG-02 Sermaye ve Koruma"].startswith("| PRG-02 Sermaye ve Koruma | 1 | 1 |")
    assert satirlar["| PRG-03 Öğrenme Döngüsü"] == "| PRG-03 Öğrenme Döngüsü | 0 | 0 | 0 | 0 | 0 | 0 | — |"
    assert satirlar["| _cephesiz / tanımsız cephe_"].startswith("| _cephesiz / tanımsız cephe_ | 4 |")
    assert satirlar["| **Toplam**"] == "| **Toplam** | 6 | 1 | 2 | 2 | 1 | 0 | — |"


def test_T8_cli_denetle_bayat_blogu_yakalar_yaz_onarir(tmp_path, capsys):
    m = _mod()
    baglanmis = SENTETIK.replace("  Ref: kaynak · PRG-01 ortada", "  Ref: PRG-01 · kaynak") \
                        .replace("  Ref: PRG-99 · kaynak", "  Ref: PRG-03 · kaynak") \
                        .replace("| TSK-902 | etiketsiz tahta kalemi |", "| TSK-902 | etiketli tahta kalemi (WP: WP2) |") \
                        .replace("  What: iş\n\n## §6", "  What: iş\n  Ref: PRG-02 · kaynak\n\n## §6")
    p = tmp_path / "ROADMAP.md"
    p.write_text(baglanmis, encoding="utf-8")
    assert m.ihlaller(baglanmis) == []
    assert m.main(["--denetle", "--dosya", str(p)]) == 1
    assert "BAYAT" in capsys.readouterr().out
    assert m.main(["--yaz", "--dosya", str(p)]) == 0
    assert m.main(["--denetle", "--dosya", str(p)]) == 0
    metin = p.read_text(encoding="utf-8")
    assert "bayat içerik" not in metin and metin.count(m.BLOK_BASLA) == 1 and metin.count(m.BLOK_BITIR) == 1


def test_T9_cli_denetle_cephesiz_kalemde_de_kirmizi(tmp_path, capsys):
    m = _mod()
    p = tmp_path / "ROADMAP.md"
    p.write_text(m.blogu_yaz(SENTETIK), encoding="utf-8")
    assert m.main(["--denetle", "--dosya", str(p)]) == 1
    cikti = capsys.readouterr().out
    assert "TSK-911" in cikti and "BAYAT" not in cikti


def test_T10_isaretsiz_dosyada_yaz_ACIKCA_duser(tmp_path):
    m = _mod()
    metin = SENTETIK.replace(m.BLOK_BASLA, "").replace(m.BLOK_BITIR, "")
    assert m.blok_icerigi(metin) is None
    try:
        m.blogu_yaz(metin)
    except ValueError as e:
        assert "işaretleri yok" in str(e)
    else:
        raise AssertionError("işaretsiz dosyada blogu_yaz sessizce geçti")

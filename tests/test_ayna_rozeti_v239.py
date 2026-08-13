"""v239 KALEM 1 — AYNA ROZETİ YANLIŞ ALANI OKUYORDU (denetim §3.1).

ÖLÇÜLEN KUSUR (canlı, 2026-08-12T22:01Z): `heartbeat.mirror_drift` **FİYAT** sapmasını ölçer
(`loop.MIRROR_DRIFT_TOL` — iç sim dolumu ↔ gerçek Alpaca dolumu); **ADET** sapması
(`position_drift` = `missing_on_alpaca` ∪ `qty_drift`) yalnız `broker_reconcile.json`a yazılıyordu
ve NABIZDA O ANAHTAR HİÇ YOKTU. Panonun HESAP rozeti nabzı okuduğu için `mirror_drift=False`
görüp "ayna uyumlu" (yeşil) yazarken 4/4 pozisyon ~2 kat ayrıktı — aynı ekranın eylem şeridi ise
"Alpaca aynasında sapma var" diyordu.

BU DOSYA İKİ TARAFI DA ÇİVİLER:
  (A) YAYAN TARAF — `loop.ayna_sapma_alanlari` üç alanı da üretir ve **ölçülmediğinde `None`**
      yazar (False DEĞİL: "ölçmedik" ile "ölçtük, temiz" aynı sayıyla anlatılamaz).
  (B) TÜKETİCİ — `app.js`in `aynaRozeti` fonksiyonu İKİ boyutu da okur ve *fiyat-uyumlu ∧
      adet-ayrık* hâlinde "ayna uyumlu" YAZAMAZ. Doğruluk tablosu gerçekten koşturulur (node
      varsa); node yoksa yapısal çiviler yine geçerlidir.

REGRESYON KARŞITI: (B)'nin doğruluk tablosu "sapma varken uyumlu yazma" yasağının YANINDA
"sapma yokken de uyumlu yaz" pozitif kontrolünü taşır — yoksa rozeti sabit "sapma" yapmak testi
yeşil bırakırdı.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from meridian import loop

REPO = Path(__file__).resolve().parent.parent
APPJS = (REPO / "meridian" / "web" / "app.js").read_text()


# ============================== (A) YAYAN TARAF: NABIZ ALANLARI ==============================

def test_a1_mutabakat_kosmadiysa_iki_boyut_da_None_dur():
    """ÖLÇÜLMEDİ ≠ TEMİZ. `checked` False (atlandı/düştü) → `False` yazmak uydurma olurdu."""
    for mirror in (None, {}, {"checked": False, "drift": [], "positions": {}}):
        alan = loop.ayna_sapma_alanlari(mirror)
        assert alan["mirror_checked"] is False
        assert alan["mirror_drift"] is None, f"ölçülmeyen fiyat sapması uyduruldu: {mirror!r}"
        assert alan["position_drift"] is None, f"ölçülmeyen adet sapması uyduruldu: {mirror!r}"


def test_a1b_ayna_YOK_ile_ayna_OKUNAMADI_ayri_siniflardir():
    """Dahili brokerde kıyaslanacak ayna HİÇ YOKTUR; kimlik/erişim yokluğu ise gerçekten
    ölçülemeyen bir olgudur. İkisini tek sınıfa katlamak, hiç var olmayan bir arızayı sonsuza
    dek amber basmak olurdu (bu panonun kendi 'kalıcı uyarı = uyarı yokluğu' kuralı)."""
    yok = loop.ayna_sapma_alanlari({"checked": False, "skip_sinifi": "ayna_yok"})
    assert yok["mirror_skip_sinifi"] == "ayna_yok"
    okunamadi = loop.ayna_sapma_alanlari({"checked": False, "skip_sinifi": "olculemedi"})
    assert okunamadi["mirror_skip_sinifi"] == "olculemedi"
    # ÖLÇÜLEN turda sınıf YOKTUR — atlanmış bir turun özelliğini taze tura taşımak bayat olurdu.
    olculdu = loop.ayna_sapma_alanlari({"checked": True, "drift": [], "positions": {},
                                        "skip_sinifi": "ayna_yok"})
    assert olculdu["mirror_skip_sinifi"] is None


def test_a2_adet_sapmasi_nabza_dusuyor_fiyat_temizken():
    """CANLI GEOMETRİ: fiyat sapması YOK, adet sapması VAR (4/4 pozisyon ~2 kat ayrık).
    Eski kod bu hâlde nabza yalnız `mirror_drift=False` yazıyordu ve rozet yeşil yanıyordu."""
    mirror = {"checked": True, "drift": [],
              "positions": {"missing_on_alpaca": [],
                            "qty_drift": [{"ticker": "NUE", "local_qty": 54, "alpaca_qty": 25}],
                            "external": []}}
    alan = loop.ayna_sapma_alanlari(mirror)
    assert alan == {"mirror_checked": True, "mirror_skip_sinifi": None,
                    "mirror_drift": False, "position_drift": True}


def test_a3_eksik_pozisyon_da_adet_sapmasidir_ve_temiz_tur_temiz_kalir():
    eksik = {"checked": True, "drift": [],
             "positions": {"missing_on_alpaca": ["EMR"], "qty_drift": []}}
    assert loop.ayna_sapma_alanlari(eksik)["position_drift"] is True
    temiz = {"checked": True, "drift": [],
             "positions": {"missing_on_alpaca": [], "qty_drift": []}}
    # POZİTİF KONTROL: temiz tur GERÇEKTEN temiz okunmalı, yoksa alanı sabit True yapmak yeterdi.
    assert loop.ayna_sapma_alanlari(temiz) == {"mirror_checked": True, "mirror_skip_sinifi": None,
                                               "mirror_drift": False, "position_drift": False}
    fiyat = {"checked": True, "drift": [{"ticker": "BKNG"}], "positions": {}}
    assert loop.ayna_sapma_alanlari(fiyat)["mirror_drift"] is True


def test_a4_gunluk_tur_nabza_bu_alanlari_yaziyor():
    """Yardımcı doğru olsa bile ÇAĞRILMIYORSA nabız yine eksik kalır — bağ çivilenir."""
    src = (REPO / "meridian" / "loop.py").read_text()
    kod = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#"))
    assert "**ayna_sapma_alanlari(mirror)" in kod, (
        "daily_cycle nabza ayna alanlarını yaymıyor — rozet yine tek boyut okur")
    assert "mirror_drift=bool(mirror.get(\"drift\"))" not in kod, (
        "eski tek-boyutlu (ve ölçülmediğinde False uyduran) yazım geri gelmiş")


# ============================== (B) TÜKETİCİ: PANO ROZETİ ==============================

def test_b1_rozet_artik_tek_alan_okumuyor():
    """MEZAR TAŞI: `hb.mirror_drift ? "sapma" : "ayna uyumlu"` biçimi geri gelemez."""
    kod = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))
    assert 'hb.mirror_drift ? "sapma" : "ayna uyumlu"' not in kod, (
        "HESAP rozeti yeniden YALNIZ fiyat sapmasına bakıyor (denetim §3.1 nüksetti)")
    assert "function aynaRozeti(hb)" in kod, "iki boyutlu rozet yardımcısı kaybolmuş"
    # "ayna uyumlu" ibaresi TEK bir yerde doğabilmeli: iki boyutun da temiz olduğu son dal.
    n = kod.count('"ayna uyumlu"')
    assert n == 1, f'"ayna uyumlu" {n} yerde üretiliyor — ikinci (kapısız) bir yol açılmış'


def test_b2_rozet_her_iki_alani_da_okuyor():
    govde = re.search(r"function aynaRozeti\(hb\) \{(.*?)\n\}", APPJS, re.S)
    assert govde, "aynaRozeti gövdesi bulunamadı"
    g = govde.group(1)
    for alan in ("hb.mirror_drift", "hb.position_drift", "hb.mirror_checked"):
        assert alan in g, f"rozet {alan} alanını okumuyor"


NODE = shutil.which("node")

# Doğruluk tablosu: nabız alanları → beklenen (sınıf, metnin "uyumlu" olup olmadığı).
# `undefined` = alan HİÇ YOK (dağıtım öncesi yazılmış eski nabız) — "temiz" sayılamaz.
DOGRULUK = [
    ({"mirror_checked": True, "mirror_drift": False, "position_drift": False}, "pos", True),
    ({"mirror_checked": True, "mirror_drift": False, "position_drift": True}, "neg", False),
    ({"mirror_checked": True, "mirror_drift": True, "position_drift": False}, "neg", False),
    ({"mirror_checked": True, "mirror_drift": True, "position_drift": True}, "neg", False),
    ({"mirror_checked": False, "mirror_drift": None, "position_drift": None,
      "mirror_skip_sinifi": "olculemedi"}, "warn", False),
    ({}, "warn", False),                                    # eski nabız: iki alan da yok
    ({"mirror_drift": False}, "warn", False),               # eski nabız: yalnız fiyat ölçülmüş
    # DAHİLİ BROKER: ayna YOK — nötr, ne yeşil ne amber (kalıcı uyarı üretmez).
    ({"mirror_checked": False, "mirror_drift": None, "position_drift": None,
      "mirror_skip_sinifi": "ayna_yok"}, "", False),
    # SAPMA ÖLÇÜLDÜYSE ATLAMA SINIFI ONU BASTIRAMAZ (öncelik sırası çivilenir).
    ({"mirror_checked": True, "mirror_drift": False, "position_drift": True,
      "mirror_skip_sinifi": "ayna_yok"}, "neg", False),
]


@pytest.mark.skipif(NODE is None, reason="node yok — yapısal çiviler (b1/b2) yine koşuyor")
@pytest.mark.parametrize("hb,sinif,uyumlu", DOGRULUK)
def test_b3_rozet_dogruluk_tablosu(hb, sinif, uyumlu):
    """FONKSİYONUN KENDİSİ KOŞTURULUR. Kaynak-metin çivisi "kod değişti mi"yi ölçer; bu test
    "kod ne diyor"u ölçer — asıl iddia (fiyat-uyumlu ∧ adet-ayrık → 'ayna uyumlu' YAZILAMAZ)
    ancak burada kanıtlanır."""
    govde = re.search(r"(function aynaRozeti\(hb\) \{.*?\n\})", APPJS, re.S)
    assert govde, "aynaRozeti gövdesi bulunamadı"
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
        fh.write(govde.group(1) + f"\nconsole.log(JSON.stringify(aynaRozeti({json.dumps(hb)})));\n")
        yol = fh.name
    try:
        r = subprocess.run([NODE, yol], capture_output=True, text=True, timeout=30)
    finally:
        Path(yol).unlink(missing_ok=True)
    assert r.returncode == 0, f"aynaRozeti koşmadı: {r.stderr[:400]}"
    out = json.loads(r.stdout.strip())
    assert out["sinif"] == sinif, f"{hb} → {out}"
    assert ("uyumlu" in out["metin"] and out["metin"] == "ayna uyumlu") is uyumlu, (
        f"{hb} → {out['metin']!r}: fiyat-uyumlu ∧ adet-ayrık hâlinde 'ayna uyumlu' YAZILAMAZ")
    assert out["baslik"], "künye (title) boş — operatör hangi boyutun saptığını okuyamaz"

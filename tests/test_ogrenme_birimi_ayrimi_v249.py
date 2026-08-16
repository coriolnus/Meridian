"""Öğrenme döngüsünün API sürecinden ayrılması — birim/bayrak çivileri (ROADMAP §2-50).

NEDEN ÇİVİ: ayrımın tamamı İKİ systemd birimindeki bayrakların karşıtlığına dayanıyor. Bir gün
biri `meridian.service`teki bayrağı "düzeltmek" için 1 yaparsa ölçülen arıza (GIL çekişmesi, pano
2,6-14,0 sn) sessizce geri gelir — test kırmazsa kimse görmez. Arama düğmelerinin İKİ birimde
EŞİT olması da aynı sınıf: `reflect_now` API sürecinde kaldığı için düğmeler iki yerde durmak
zorunda, ve ayrışırlarsa bekleme döngüsü ile elle tetikleme farklı bütçelerle koşar.
"""

import pathlib
import re

import pytest

BIRIM = pathlib.Path(__file__).resolve().parents[1] / "deploy" / "oracle-a1"
ANA = BIRIM / "meridian.service"
OGRENME = BIRIM / "meridian-learn.service"

# İki birimde de bulunması ve EŞİT olması gereken arama düğmeleri.
ORTAK_DUGMELER = ("MERIDIAN_PARALLEL_PROBES", "MERIDIAN_SEARCH_MAX_MIN",
                  "HERMES_SEARCH_BUDGET", "MERIDIAN_BROKER")


def _env(yol: pathlib.Path) -> dict[str, str]:
    """Birim dosyasındaki `Environment=AD=DEĞER` satırlarını sözlüğe çevirir (yorumlar hariç)."""
    out: dict[str, str] = {}
    for satir in yol.read_text(encoding="utf-8").splitlines():
        s = satir.strip()
        if s.startswith("#") or not s.startswith("Environment="):
            continue
        m = re.match(r"Environment=([A-Z0-9_]+)=(.*)$", s)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def test_iki_birim_de_var():
    assert ANA.exists(), "meridian.service yok"
    assert OGRENME.exists(), "meridian-learn.service yok — §2-50 ayrımı birimsiz kalamaz"


def test_ogrenme_bayragi_karsit():
    """Ana birim döngüyü KOŞTURMAZ, öğrenme birimi KOŞTURUR. Karşıtlık ayrımın kendisidir."""
    assert _env(ANA).get("MERIDIAN_AUTOSTART_HERMES") == "0", (
        "meridian.service öğrenme döngüsünü koşturuyor — §2-50 ayrımı bozuldu, GIL çekişmesi geri geldi")
    assert _env(OGRENME).get("MERIDIAN_AUTOSTART_HERMES") == "1", (
        "meridian-learn.service döngüyü koşturmuyor — öğrenme HİÇBİR yerde koşmaz")


@pytest.mark.parametrize("ad", ORTAK_DUGMELER)
def test_arama_dugmeleri_iki_birimde_esit(ad):
    """`reflect_now` API sürecinde kaldığı için bu düğmeler iki yerde durur; DEĞERLERİ ayrışamaz."""
    a, o = _env(ANA).get(ad), _env(OGRENME).get(ad)
    assert a is not None, f"{ad} meridian.service'te yok"
    assert o is not None, f"{ad} meridian-learn.service'te yok"
    assert a == o, (f"{ad} birimler arasında AYRIŞTI: ana={a!r} öğrenme={o!r} — bekleme döngüsü ile "
                    f"elle tetikleme farklı bütçelerle koşar")


def test_ogrenme_birimi_cpu_tavani_degil_agirlik_kullanir():
    """`CPUQuota` bir TAVANDIR ve boştaki çekirdekleri de yasaklardı — ayrımın bütün amacı onları
    öğrenmeye AÇMAKTI. Ağırlık (`CPUWeight`) çekişmede panoyu öne alır, boşta kısıtlamaz."""
    metin = "\n".join(s for s in OGRENME.read_text(encoding="utf-8").splitlines()
                      if not s.strip().startswith("#"))
    assert "CPUWeight=" in metin, "CPUWeight yok — çekişmede pano önceliği yazılı değil"
    assert "CPUQuota=" not in metin, "CPUQuota TAVANDIR: boş çekirdekleri de yasaklar, amacı bozar"


def test_ogrenme_birimi_giris_noktasi_gercek():
    """`ExecStart`ın işaret ettiği modül GERÇEKTEN var ve `main()` taşıyor (çapa çürümesi yasası)."""
    metin = OGRENME.read_text(encoding="utf-8")
    assert "-m meridian.learn_run" in metin, "ExecStart learn_run'ı çağırmıyor"
    from meridian import learn_run
    assert callable(learn_run.main)


def test_search_progress_uc_degerli_okuyucu():
    """Emniyet kalemi: "ölçülemedi" ile "arama yok" AYRI cevaplar olmalı. Birleşirlerse sprint
    kapısı boş sözlüğü "meşgul değil" okur ve koşan aramanın üstüne antrenman başlatır."""
    from meridian import hermes
    assert callable(hermes.search_progress_oku)
    bos = hermes.search_progress_oku(ayni_surec=True)      # bellekteki sözlük testte boştur
    assert bos["durum"] in {"yok", "kosuyor"}, bos
    # Diskte dosya YOKKEN okuma "olculemedi" demeli — "yok" DEMEMELİ.
    from unittest import mock
    with mock.patch.object(hermes.store, "read_json", return_value=None):
        assert hermes.search_progress_oku()["durum"] == "olculemedi"
    # Damgasız `running=True`nın yaşı bilinemez → ölçülemedi.
    with mock.patch.object(hermes.store, "read_json", return_value={"running": True}):
        assert hermes.search_progress_oku()["durum"] == "olculemedi"
    # Damgalı ve koşan → kosuyor.
    from meridian import memory
    with mock.patch.object(hermes.store, "read_json",
                           return_value={"running": True, "updated_at": memory.now_iso()}):
        o = hermes.search_progress_oku()
        assert o["durum"] == "kosuyor" and o["yas_s"] is not None


def test_temizleme_kapidan_gecer():
    """Çıplak `SEARCH_PROGRESS.clear()` kapıyı atlardı ve disk aynası `running=True` DONARDI —
    sprint kapısı sonsuza dek kapalı kalırdı. Kaynakta çıplak clear() KALMAMALI."""
    kaynak = (pathlib.Path(__file__).resolve().parents[1] / "meridian")
    suclular = []
    for py in kaynak.rglob("*.py"):
        for i, satir in enumerate(py.read_text(encoding="utf-8").splitlines(), 1):
            s = satir.strip()
            if s == "SEARCH_PROGRESS.clear()" and py.name != "hermes.py":
                suclular.append(f"{py.name}:{i}")
    assert not suclular, f"kapıyı atlayan çıplak clear(): {suclular}"

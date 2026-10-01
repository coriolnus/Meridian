"""v591 — konuşan filo kadro listesi (spec 2026-09-29 §2.2/§3.1): tek kaynak + doğrulama + sorgu."""
import re
from pathlib import Path

import pytest
import yaml

from meridian import config, kadro

ROOT = config.ROOT
BEKLENEN_21 = {"sef", "bekci", "karne", "kod", "karar", "ayna", "olay", "kacan", "veri", "butce", "yol",
               "nobet", "denetci", "civici", "devir", "derleyici", "olcum", "tasarimci", "yabanci", "piyasa",
               "hipotez"}


def _yaz(tmp_path, botlar):
    p = tmp_path / "kadro.yaml"
    p.write_text(yaml.safe_dump({"botlar": botlar}, allow_unicode=True), encoding="utf-8")
    return p


def _gecerli(ad="sef", **k):
    b = {"ad": ad, "rol": "r", "dalga": "canli", "durum": "aktif", "araclar": ["pano_ozeti"],
         "zamanli_is": None, "imza": None, "hafiza": "kendi", "gunluk_tavan": None,
         "gunluk_tavan_neden": "olculmedi"}
    b.update(k)
    return b


def test_kadro_21_bot_ve_adlar_birebir():
    assert {b.ad for b in kadro.kadro_yukle()} == BEKLENEN_21


def test_aktif_botlar_profil_dizinleriyle_birebir():
    profiller = {p.name for p in (ROOT / "deploy/hermes/profiles").iterdir() if p.is_dir()}
    assert {b.ad for b in kadro.aktif_botlar()} == profiller


def test_dalgalar_operator_kararina_esit():
    k = kadro.kadro_yukle()
    dalga = lambda d: {b.ad for b in k if b.dalga == d}
    assert dalga("canli") == {"sef", "bekci", "karne"}
    assert dalga("1") == {"kod", "karar", "ayna", "olay"}
    assert dalga("2") == {"kacan", "veri", "butce", "yol", "nobet", "denetci"}
    assert dalga("kilitli") == {"hipotez"}
    assert len(dalga("3")) == 7


def test_hepsi_hafizasi_yalniz_sef():
    assert {b.ad for b in kadro.kadro_yukle() if b.hafiza == "hepsi"} == {"sef"}


def test_imza_rapor_basligi_onekidir():
    for b in kadro.aktif_botlar():
        if b.zamanli_is is None:
            continue
        betik = {"sef": "ops/sef_brifingi.py", "bekci": "ops/bekci_brifingi.py",
                 "karne": "ops/karne_brifingi.py"}[b.ad]
        m = re.search(r'^BASLIK = "(.+)"$', (ROOT / betik).read_text(encoding="utf-8"), re.M)
        assert m and m.group(1).startswith(b.imza), (b.ad, b.imza)


def test_zamanli_is_birimi_depoda_var():
    for b in kadro.aktif_botlar():
        if b.zamanli_is:
            assert (ROOT / "deploy/oracle-a1" / f"{b.zamanli_is}.service").is_file(), b.zamanli_is


def test_araclar_bilinen_kumede():
    from meridian import mcp_server, sohbet
    bilinen = set(sohbet.ARACLAR) | {t["name"] for t in mcp_server.TOOLS} | set(kadro.PLANLI_ARACLAR)
    for b in kadro.kadro_yukle():
        assert set(b.araclar) <= bilinen, (b.ad, set(b.araclar) - bilinen)


def test_gunluk_tavan_olculmeden_null_ve_nedenli():
    for b in kadro.kadro_yukle():
        assert b.gunluk_tavan is None and b.gunluk_tavan_neden, b.ad


def test_imzadan_bot_rapor_ilk_satiri():
    assert kadro.imzadan_bot("🔭 Meridian bekçi\n3 kalem").ad == "bekci"
    assert kadro.imzadan_bot("🧭 Meridian brifing — HAM (sıralama katmanı devrede değil)\n…").ad == "sef"
    assert kadro.imzadan_bot("📊 Meridian karne\nGEÇTİ").ad == "karne"
    assert kadro.imzadan_bot("başka bir mesaj\n🔭 Meridian bekçi") is None
    assert kadro.imzadan_bot("") is None


def test_bot_bul_harf_duyarsiz():
    assert kadro.bot_bul("BEKCI").ad == "bekci"
    assert kadro.bot_bul("yok") is None


# TUR 3 (Görev 2 son inceleme, Türkçe harf): operatör "@bekçi"/"@şef" yazar — rapor başlığı da
# "bekçi" der. `.lower()` tek başına yetmez: "İ".lower() = "i" + BİRLEŞTİRİCİ NOKTA (U+0307).
@pytest.mark.parametrize("yazim,ad", [
    ("şef", "sef"), ("bekçi", "bekci"), ("DENETCİ", "denetci"), ("BEKÇİ", "bekci"),
    ("BÜTÇE", "butce"), ("nöbet", "nobet"), ("ÖLÇÜM", "olcum"), ("ciVİci", "civici"),
])
def test_bot_bul_turkce_harfleri_katlar(yazim, ad):
    assert kadro.ad_katla(yazim) == ad and "̇" not in kadro.ad_katla(yazim)
    assert kadro.bot_bul(yazim).ad == ad


@pytest.mark.parametrize("ad", ["bekçi", "bot2", "iki kelime", "a-b"])
def test_dogrulama_ad_yalniz_ascii_kucuk_harf_ve_alt_cizgi(tmp_path, ad):
    # Telegram yönlendirme desenleri (`bot_kanal._SOHBET_IMZA`) adın [a-z_] olduğunu
    # varsayar; kadro bu varsayımı ZORLAR — aksi hâlde o botun cevabına yanıt sessizce @sef'e düşerdi.
    with pytest.raises(ValueError, match=r"'ad'=.* yalnız \[a-z_\]"):
        kadro.kadro_yukle(_yaz(tmp_path, [_gecerli(ad=ad)]))


@pytest.mark.parametrize("bozuk,alan", [
    ({"durum": "belki"}, "durum"),
    ({"dalga": "9"}, "dalga"),
    ({"hafiza": "ortak"}, "hafiza"),
    ({"araclar": []}, "araclar"),
])
def test_dogrulama_hatali_alani_adlandirir(tmp_path, bozuk, alan):
    with pytest.raises(ValueError, match=alan):
        kadro.kadro_yukle(_yaz(tmp_path, [_gecerli(**bozuk)]))


def test_dogrulama_tekrarlanan_ad(tmp_path):
    with pytest.raises(ValueError, match="tekrar"):
        kadro.kadro_yukle(_yaz(tmp_path, [_gecerli(), _gecerli()]))


def test_dogrulama_null_tavan_nedensiz(tmp_path):
    with pytest.raises(ValueError, match="gunluk_tavan_neden"):
        kadro.kadro_yukle(_yaz(tmp_path, [_gecerli(gunluk_tavan_neden=None)]))


# ---- Tip doğrulaması (uygulayıcı eki, brief'in "sessiz varsayılan YOK" sözleşmesinin kalanı) ----
# `araclar: pano_ozeti` (liste değil dizge) tuple()'a girse harf harf araç adı olurdu; `gunluk_tavan: "5"`
# ya da `true` Bot'un `int | None` tipini sessizce bozardı — kota karşılaştırması ileride dizgeyle koşardı.
@pytest.mark.parametrize("bozuk,alan", [
    ({"araclar": "pano_ozeti"}, "araclar"),
    ({"araclar": ["pano_ozeti", 3]}, "araclar"),
    ({"gunluk_tavan": "5"}, "gunluk_tavan"),
    ({"gunluk_tavan": True}, "gunluk_tavan"),
])
def test_dogrulama_tip_bozuklugunu_adlandirir(tmp_path, bozuk, alan):
    with pytest.raises(ValueError, match=alan):
        kadro.kadro_yukle(_yaz(tmp_path, [_gecerli(**bozuk)]))


def test_dogrulama_esleme_olmayan_satir(tmp_path):
    with pytest.raises(ValueError, match="eşleme"):
        kadro.kadro_yukle(_yaz(tmp_path, ["sef"]))


def test_olculmus_tavan_nedensiz_yuklenir(tmp_path):
    (b,) = kadro.kadro_yukle(_yaz(tmp_path, [_gecerli(gunluk_tavan=40, gunluk_tavan_neden=None)]))
    assert b.gunluk_tavan == 40 and b.gunluk_tavan_neden is None

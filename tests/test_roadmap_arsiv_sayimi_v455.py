"""v455 · §8 ARŞİV MADDELERİ PANODA SAYILIR — liste imsiz arşiv grameri.

ÖLÇÜLEN ARIZA (2026-09-08). O gün 107 kapanmış TSK maddesi `§2 TAHTA` ve `§4 ÖNERİ HAVUZU`ndan
`§8 ARŞİV`e taşındı (`### §8.T.2` / `### §8.H.2` alt bölümleri; aynı gün `§8.K` ve "OPERATÖR
BLOKLARINDAN ARŞİVE" bloğu da doğdu). Taşıma sırasında satır biçimi BİLİNÇLİ olarak değişti:
§8'de arşiv maddesi LİSTE İMSİZ yazılır —

    **[TSK-046] Başlık** — status: DONE(2026-09-03 · …) · born: … · owner: … · size: … · trigger: —

çünkü `tests/test_roadmap_standart_v351.py::test_r13_bolum_muafiyeti_*` §8'de `- **[` biçimini
YASAKLAR (muaf bölüm; yaşayan bölüm gramerinin oraya sızması yanlış-pozitif kaynağıdır).

Bedeli tek cümlede: `/api/roadmap` ayrıştırıcısı maddeyi YALNIZ `- `/`* ` işaretli satırdan
tanıyordu, dolayısıyla 107 kalem taşındığı anda PANODAN KAYBOLDU — §2 66→52, §4 127→36 düşerken
§8 72'de KALDI. Operatörün gördüğü şey "tablo hâlâ güncel değil"di: kapanan iş ne açık kovada ne
kapalı kovada; hiçbir yerde. Bu, ayrıştırıcının sessizce yarısını düşürmesinin (v287'nin
"madde sayısı dosyadakiyle tutarlı" çivisinin) arşiv tarafındaki kardeşidir.

BU DOSYA NEYİ ÇİVİLER
---------------------
A. **§8'DE LİSTE İMSİZ ŞEMA SATIRI MADDEDİR.** `**[KİMLİK] Ad** — status: …` satırı §8 içinde
   madde olarak sayılır, `section` alanı §8'dir, `kaynak` "madde"dir.
B. **§8 DIŞINDA SAYILMAZ.** Yaşayan bölümlerde (§2/§4/§5/§6) madde `- **[` ile başlar
   (v351 sözleşmesi); liste imsiz satırın orada madde sayılması iki grameri birleştirir ve
   v351'in muafiyet süzgeciyle sessizce çelişirdi.
C. **GERÇEK DOSYA: TAŞIMA GÖRÜNÜYOR.** §8 en az 107 arşiv maddesi taşır (2026-09-08 taşımasının
   ALT SINIRI — belge büyür, sayı pinlenmez) ve §2/§4'te DONE/DROPPED madde KALMAMIŞTIR.
D. **KOVA EŞLEMESİ UYDURULMAZ.** DONE/DROPPED → "kapalı"; sözlük dışı bir status "belirsiz" +
   `status_neden` verir. Arşiv maddesi ayrıcalıklı değildir: kapalı sayılması `status`
   alanından GELİR, "§8'de duruyor" olmasından değil.
E. **GÖVDE KATLANIR, DÜZYAZI ROZETİ HÜKÜM DEĞİLDİR.** Arşiv maddesinin `What:`/`Why:`/`Ref:`
   satırları maddeye katlanır; gövdedeki ✅/KAPANDI düzyazısı şemalı satırın durumunu EZMEZ
   (2026-09-01 göçünün kuralı: durum beyan edildiği ALANDAN okunur).
F. **§8'DEKİ BULLET MADDESİ HÂLÂ MADDEDİR.** Yeni gramer eskisini emekli ETMEZ — §8'de
   tarihçe bullet'ları var ve onların sayımı düşerse taşıma kazancı sessizce geri alınırdı.

KAPSAM DIŞI, BİLEREK (bedel yasası — kaybedileni de ölç): `**[TSK-134] … --tx*, --line* …**`
satırı ADINDA `*` taşıdığı için ŞEMA GRAMERİNE UYMUYOR ve arşiv maddesi sayılmıyor. Bu, bu
turun kaybı DEĞİL: aynı kör nokta bullet gramerinde de var (`api._ROADMAP_SEMA_BASLIK` ve
`v351.MADDE_SATIRI_DESENI` ikisi de `[^*]*`) — grameri burada genişletmek iki dosyayı
ayrıştırırdı. Ölçüldü 2026-09-08: §8'de 118 liste imsiz `**[` satırı var, 111'i şemaya uyuyor
(6'sı 2026-08-30'un `B-*` düzyazı arşiv blokları, 1'i TSK-134).
"""
import pathlib
import re

import pytest

from meridian import api, config

KOK = pathlib.Path(config.ROOT)

# Sentetik gövde: `§8` başlığı + liste imsiz arşiv maddeleri. Alan SIRASI şemanın kendisidir
# (status · born · owner · size · trigger) — sıra bozulursa uç bunu `sema_ihlal` sayar.
ARSIV_BASI = "# T\n\n## §8 ARŞİV — tamamlanan işler\n\n"


def _sentetik(metin: str) -> dict:
    return api._roadmap_ayristir(metin, yol="sanal.md", bayt=len(metin.encode()),
                                 mtime=None, tam=True)


def _yuk() -> dict:
    metin = (KOK / "ROADMAP.md").read_text(encoding="utf-8")
    return api._roadmap_ayristir(metin, yol="sanal.md", bayt=len(metin.encode()),
                                 mtime=None, tam=True)


def _gez(b: dict):
    yield b
    for a in b["alt_bolumler"]:
        yield from _gez(a)


def _bolum(yuk: dict, no: str) -> dict:
    eslesen = [k for k in yuk["bolumler"] if (k.get("no") or "") == no]
    assert len(eslesen) == 1, f"belgede tek bir {no} kök bölümü bulunamadı: {len(eslesen)}"
    return eslesen[0]


def _maddeler(kok: dict) -> list:
    return [m for b in _gez(kok) for m in b["maddeler"]]


# ==================================================================================================
# A — §8'de liste imsiz şema satırı MADDEDİR
# ==================================================================================================

def test_a_sentetik_arsiv_maddeleri_kapali_kovaya_dusuyor():
    """Üç liste imsiz DONE/DROPPED satırı → 3 madde, üçü de `kapali`, `section` §8."""
    metin = ARSIV_BASI + (
        "**[TSK-901] Birinci arşiv kalemi** — status: DONE(2026-09-03 · v900) · "
        "born: 2026-09-01 · owner: rol1 · size: M · trigger: —\n"
        "\n"
        "**[TSK-902] İkinci arşiv kalemi** — status: DONE(2026-09-04) · "
        "born: 2026-09-02 · owner: rol1 · size: S · trigger: —\n"
        "\n"
        "**[TSK-903] Üçüncü arşiv kalemi** — status: DROPPED(2026-09-05 · gereksiz) · "
        "born: 2026-09-02 · owner: agent · size: L · trigger: —\n"
    )
    yuk = _sentetik(metin)
    b = yuk["bolumler"][0]

    assert b["madde_n"] == 3, (
        f"§8'deki liste imsiz arşiv maddeleri sayılmadı: madde_n={b['madde_n']} "
        "— 2026-09-08 taşımasının 107 kalemi panodan bu yüzden kaybolmuştu")
    assert yuk["sayim"]["madde_n"] == 3
    assert yuk["sayim"]["durum"]["kapali"] == 3, (
        f"kova eşlemesi bozuk: {yuk['sayim']['durum']}")

    for m in b["maddeler"]:
        assert m["sema"] is not None, f"arşiv maddesine şema atanmadı: {m['baslik']!r}"
        assert m["sema"]["section"] == "§8", m["sema"]["section"]
        assert m["sema"]["kaynak"] == "madde", m["sema"]["kaynak"]
        assert m["durum"] == "kapali", (m["baslik"], m["durum"])
        assert m["sema"]["sinif"] == "KAPALI"
    assert [m["sema"]["id"] for m in b["maddeler"]] == ["TSK-901", "TSK-902", "TSK-903"]
    assert yuk["sayim"]["sema"]["ihlal_n"] == 0, "sağlam arşiv satırı BOZULMA sayıldı"
    assert yuk["sayim"]["sema"]["muaf_tarihce"] == 0, "şemalı arşiv satırı tarihçe sayıldı"


def test_a2_arsiv_maddesi_alt_bolumde_de_taniniyor():
    """Gerçek dosyada arşiv maddeleri `### §8.T.2` ALT bölümünde yaşıyor — kök bölüm gövdesinde
    değil. Alt bölüm `§8` numarasını başlığından değil KÖKünden devralır."""
    metin = ARSIV_BASI + (
        "### §8.T.2 — TAHTA ARŞİVİ (2026-09-08)\n\n"
        "**[TSK-904] Alt bölümdeki arşiv kalemi** — status: DONE(2026-09-06) · "
        "born: 2026-09-01 · owner: rol1 · size: S · trigger: —\n"
    )
    yuk = _sentetik(metin)
    alt = yuk["bolumler"][0]["alt_bolumler"][0]
    assert alt["madde_n"] == 1, f"alt bölümde arşiv maddesi sayılmadı: {alt['madde_n']}"
    assert alt["maddeler"][0]["sema"]["section"] == "§8"
    assert yuk["bolumler"][0]["madde_n_toplam"] == 1


# ==================================================================================================
# B — §8 DIŞINDA liste imsiz satır madde SAYILMAZ
# ==================================================================================================

@pytest.mark.parametrize("bolum", ["## §2 TAHTA", "## §4 ÖNERİ HAVUZU", "## §6 KANIT/KARTLAR"])
def test_b_yasayan_bolumde_liste_imsiz_satir_madde_degil(bolum):
    """Yaşayan bölümlerde madde `- **[` ile BAŞLAR (v351 sözleşmesi). Liste imsiz satırı orada
    da madde saymak iki grameri birleştirir ve v351'in bölüm muafiyetiyle çelişirdi."""
    metin = (f"# T\n\n{bolum}\n\n"
             "**[TSK-905] Liste imsiz satır** — status: DONE(2026-09-06) · "
             "born: 2026-09-01 · owner: rol1 · size: S · trigger: —\n")
    yuk = _sentetik(metin)
    assert yuk["sayim"]["madde_n"] == 0, (
        f"{bolum} içinde liste imsiz satır madde sayıldı — arşiv grameri §8'e ÖZGÜdür")
    assert yuk["bolumler"][0]["madde_n"] == 0


def test_b2_yasayan_bolumdeki_bullet_maddesi_etkilenmedi():
    """Karşı yön: aynı satır `- ` ile yazıldığında §4'te MADDEdir — gerileme çivisi."""
    metin = ("# T\n\n## §4 ÖNERİ HAVUZU\n\n"
             "- **[TSK-906] Bullet madde** — status: QUEUED · born: 2026-09-01 · "
             "owner: rol1 · size: S · trigger: —\n")
    m = _sentetik(metin)["bolumler"][0]["maddeler"][0]
    assert m["sema"]["id"] == "TSK-906" and m["durum"] == "acik"


# ==================================================================================================
# C — GERÇEK DOSYA: 2026-09-08 taşıması panoda görünüyor
# ==================================================================================================

def test_c_gercek_roadmap_section8_arsiv_maddelerini_tasiyor():
    """ALT SINIR çivisi (pin DEĞİL): 2026-09-08'de 107 kapanmış TSK maddesi §8'e taşındı.

    Sayı ARTAR (arşiv büyür), azalmaz — düşerse ya taşıma geri alınmış ya gramer kaymıştır;
    ikisi de sessizce geçmemeli."""
    yuk = _yuk()
    s8 = _bolum(yuk, "§8")
    arsiv = [m for m in _maddeler(s8)
             if m["sema"] is not None and m["sema"]["status"] in ("DONE", "DROPPED")]
    assert len(arsiv) >= 107, (
        f"§8'de yalnız {len(arsiv)} şemalı arşiv maddesi ölçüldü; 2026-09-08 taşıması 107 kalem "
        "getirmişti — ayrıştırıcı liste imsiz arşiv gramerini tanımıyor olabilir")
    assert s8["madde_n_toplam"] >= 107


def test_c2_gercek_roadmap_yasayan_bolumlerde_kapanmis_madde_kalmadi():
    """Taşımanın ÖTEKİ yarısı: §2/§4'te DONE/DROPPED bullet maddesi kalmamalı. Kalsaydı ya
    taşıma yarım, ya arşiv maddesi ÇİFT sayılıyor olurdu."""
    yuk = _yuk()
    for no in ("§2", "§4"):
        kapanmis = [m["sema"]["id"] for m in _maddeler(_bolum(yuk, no))
                    if m["sema"] is not None and m["sema"]["status"] in ("DONE", "DROPPED")]
        assert kapanmis == [], f"{no} hâlâ kapanmış madde taşıyor: {kapanmis}"


def test_c3_gercek_roadmap_arsiv_kimlikleri_yasayan_bolumlerde_MUKERRER_DEGIL():
    """Aynı kalem hem §8'de hem yaşayan bölümde madde olarak sayılırsa tahta ÇİFT sayar."""
    yuk = _yuk()
    yerler: dict[str, set[str]] = {}
    for kok in yuk["bolumler"]:
        no = kok.get("no")
        for m in _maddeler(kok):
            if m["sema"] is not None and m["sema"]["id"]:
                yerler.setdefault(m["sema"]["id"], set()).add(no or "?")
    cift = {k: sorted(v) for k, v in yerler.items() if "§8" in v and len(v) > 1}
    assert not cift, f"arşiv kimliği yaşayan bölümde de madde olarak sayılıyor: {cift}"


def test_c4_gercek_roadmap_muhasebe_kapaniyor():
    """v343/F'nin arşiv tarafındaki karşılığı: şemalı + muaf = toplam madde; üçüncü sessiz
    kova yok ve §8 arşiv maddeleri `ihlal_n`i yükseltmiyor."""
    yuk = _yuk()
    sema = yuk["sayim"]["sema"]
    assert sema["madde_n"] + sema["muaf_tarihce"] == yuk["sayim"]["madde_n"]
    assert sema["ihlal_n"] == 0, (
        "arşiv satırı şema BİÇİMİNDE olup alanları tutmuyor — bu tarihçe değil bozulmadır")


# ==================================================================================================
# D — KOVA EŞLEMESİ UYDURULMAZ
# ==================================================================================================

def test_d_arsivde_sozluk_disi_status_UYDURULMUYOR():
    """"§8'de duruyor" kapalı yapmaz: kova `status` alanından gelir."""
    metin = ARSIV_BASI + ("**[TSK-907] Tanınmayan durum** — status: YOLDA · "
                          "born: 2026-09-01 · owner: rol1 · size: S · trigger: —\n")
    m = _sentetik(metin)["bolumler"][0]["maddeler"][0]
    assert m["durum"] == "belirsiz", m["durum"]
    assert m["sema"]["status"] is None
    assert "sözlüğünde yok" in (m["sema"]["status_neden"] or "")
    assert m["sema"]["sinif"] is None, "status yokken üst sınıf uyduruldu"


@pytest.mark.parametrize("govde, bekleniyor", [
    ("status: ACTIVE · born: 2026-09-01 · owner: rol1 · size: S · trigger: —", "acik"),
    ("status: GATED(operatör) · born: 2026-09-01 · owner: rol1 · size: S · trigger: onay", "askida"),
    ("status: OPERATOR · born: 2026-09-01 · owner: operator · size: S · trigger: —", "bloke"),
    ("status: DONE(2026-09-01·v351) · born: 2026-08-01 · owner: rol1 · size: S · trigger: —",
     "kapali"),
    ("status: DROPPED(2026-09-01·gereksiz) · born: 2026-08-01 · owner: rol1 · size: S · "
     "trigger: —", "kapali"),
])
def test_d2_arsiv_maddesi_sozlugun_HER_degerini_ayni_kovaya_dusuruyor(govde, bekleniyor):
    """Arşiv maddesi ayrı bir sözlük TAŞIMAZ — bullet maddesiyle AYNI eşlemeyi kullanır
    (tek-kaynak yasası: ikinci bir sözlük sessizce ayrışırdı)."""
    metin = ARSIV_BASI + f"**[TSK-908] Sınama** — {govde}\n"
    assert _sentetik(metin)["bolumler"][0]["maddeler"][0]["durum"] == bekleniyor


def test_d3_alan_sirasi_bozuk_arsiv_satiri_IHLAL_sayilir():
    """Şema BİÇİMİNDE olup alanları tutmayan arşiv satırı sessizce "tarihçe" olmaz."""
    metin = ARSIV_BASI + ("**[TSK-909] Bozuk sıra** — born: 2026-09-01 · status: DONE · "
                          "owner: rol1 · size: S · trigger: —\n")
    yuk = _sentetik(metin)
    assert yuk["sayim"]["sema"]["ihlal_n"] == 1, yuk["sayim"]["sema"]
    assert yuk["bolumler"][0]["sema_ihlal"][0]["bolum"] == "§8"


# ==================================================================================================
# E — GÖVDE KATLANIR, DÜZYAZI ROZETİ HÜKÜM DEĞİLDİR
# ==================================================================================================

def test_e_arsiv_maddesinin_govdesi_katlaniyor():
    """`What:`/`Why:`/`Ref:` satırları maddeye katlanır (bitişik satır kuralı), boş satır
    maddeyi KAPATIR — iki arşiv kalemi tek maddeye yapışmaz."""
    metin = ARSIV_BASI + (
        "**[TSK-910] Birinci** — status: DONE(2026-09-06) · born: 2026-09-01 · "
        "owner: rol1 · size: S · trigger: —\n"
        "  What: gövde satırı bir\n"
        "  Why: gövde satırı iki\n"
        "\n"
        "**[TSK-911] İkinci** — status: DONE(2026-09-06) · born: 2026-09-01 · "
        "owner: rol1 · size: S · trigger: —\n"
    )
    maddeler = _sentetik(metin)["bolumler"][0]["maddeler"]
    assert len(maddeler) == 2, [m["baslik"] for m in maddeler]
    assert "gövde satırı bir" in maddeler[0]["ham"] and "gövde satırı iki" in maddeler[0]["ham"]
    assert "gövde satırı" not in maddeler[1]["ham"]
    assert maddeler[0]["baslik"] == "[TSK-910] Birinci"


def test_e2_govdedeki_duzyazi_rozeti_semali_durumu_EZMIYOR():
    """2026-09-01 göçünün kuralı arşivde de geçerli: durum beyan edildiği ALANDAN okunur."""
    metin = ARSIV_BASI + (
        "**[TSK-912] Açık kalan arşiv notu** — status: OPERATOR · born: 2026-09-01 · "
        "owner: operator · size: S · trigger: operatör onayı\n"
        "  What: ✅ KAPANDI diye yazan bir tarihçe cümlesi gövdede duruyor.\n"
    )
    m = _sentetik(metin)["bolumler"][0]["maddeler"][0]
    assert m["durum"] == "bloke", (
        f"gövdedeki düzyazı rozeti şemalı durumu ezdi: {m['durum']} / {m['durum_kanit']}")


# ==================================================================================================
# F — §8'deki BULLET maddeleri hâlâ madde (gerileme çivisi)
# ==================================================================================================

def test_f_section8_bullet_maddeleri_hala_sayiliyor():
    """Yeni gramer eskisini emekli ETMEZ: §8'in rozet-düzyazılı tarihçe bullet'ları durur."""
    metin = ARSIV_BASI + (
        "- **✅ KAPANDI 2026-01-01** — eski tarihçe satırı\n"
        "- **BLOKE:** dış bağımlılık\n"
        "\n"
        "**[TSK-913] Yeni arşiv kalemi** — status: DONE(2026-09-06) · born: 2026-09-01 · "
        "owner: rol1 · size: S · trigger: —\n"
    )
    yuk = _sentetik(metin)
    b = yuk["bolumler"][0]
    assert b["madde_n"] == 3, [m["baslik"] for m in b["maddeler"]]
    assert [m["durum"] for m in b["maddeler"]] == ["kapali", "bloke", "kapali"]
    assert [m["sema"] is None for m in b["maddeler"]] == [True, True, False]
    assert yuk["sayim"]["sema"]["muaf_tarihce"] == 2, "tarihçe bullet'ı sayacı değişti"


def test_f2_gercek_roadmap_section8_bullet_tarihcesi_kaybolmadi():
    """Gerçek dosyada §8 HEM tarihçe bullet'ı HEM arşiv maddesi taşır; biri sıfırlanırsa
    ya belge ya ayrıştırıcı değişmiştir."""
    s8 = _bolum(_yuk(), "§8")
    maddeler = _maddeler(s8)
    tarihce = [m for m in maddeler if m["sema"] is None]
    semali = [m for m in maddeler if m["sema"] is not None]
    assert tarihce, "§8'de hiç düzyazı/tarihçe maddesi kalmadı"
    assert semali, "§8'de hiç şemalı arşiv maddesi yok"


# ==================================================================================================
# Gramer TEK KAYNAK — arşiv tanıması bullet şemasıyla AYNI deseni kullanır
# ==================================================================================================

def test_gramer_tek_kaynak_arsiv_bullet_ile_ayni_deseni_kullaniyor():
    """İkinci bir başlık grameri yazılsaydı sessizce ayrışırdı (tek-kaynak yasası).

    Bu çivi doğrudan sözleşmeyi ölçer: aynı gövde bullet olarak da liste imsiz olarak da
    AYNI şema sözlüğünü üretmeli — yalnız `section` bölümden gelir."""
    govde = ("status: DONE(2026-09-06 · v455) · born: 2026-09-01 · owner: rol1 · "
             "size: M-L · trigger: —")
    bullet = _sentetik(f"# T\n\n## §4 HAVUZ\n\n- **[TSK-914] Aynı kalem** — {govde}\n")
    arsiv = _sentetik(ARSIV_BASI + f"**[TSK-914] Aynı kalem** — {govde}\n")
    a = bullet["bolumler"][0]["maddeler"][0]["sema"]
    b = arsiv["bolumler"][0]["maddeler"][0]["sema"]
    assert {k: v for k, v in a.items() if k != "section"} == \
           {k: v for k, v in b.items() if k != "section"}, (a, b)
    assert (a["section"], b["section"]) == ("§4", "§8")


def test_arsiv_grameri_govdede_BEYAN_ediliyor():
    """Tüketici §8'in ne zaman madde saydığını EZBERDEN bilemez — sözleşme gövdede taşınır."""
    yuk = _sentetik(ARSIV_BASI + "**[TSK-915] X** — status: DONE(2026-09-06) · "
                                 "born: 2026-09-01 · owner: rol1 · size: S · trigger: —\n")
    kapsam = yuk["durum_kapsam"] + " " + yuk["sema_kapsam"]
    # "§8" ve "arşiv" TEK BAŞINA yetmez: ikisi de eski muafiyet cümlesinde zaten geçiyordu ve
    # çivi yanlış nedenle yeşil kalırdı. Aranan şey YENİ kuralın kendisidir.
    # BÜYÜK/KÜÇÜK HARF KATLANMASI YOK: Türkçe `İ`.lower() birleşik nokta üretir ("i̇") ve
    # aranan dizge sessizce eşleşmez — beyan metni OLDUĞU GİBİ aranır.
    for parca in ("§8", "LİSTE İMSİZ", "- **["):
        assert parca in kapsam, (
            f"§8 arşiv maddesi kuralı gövdede beyan edilmiyor (eksik: {parca!r})")


def test_arsiv_maddesi_ozette_de_yasiyor():
    """`?ozet=1` gövdeleri söker, MADDEYİ sökmez — özet tahtayı çizmenin tek girdisidir."""
    yuk = _sentetik(ARSIV_BASI + "**[TSK-916] X** — status: DONE(2026-09-06) · "
                                 "born: 2026-09-01 · owner: rol1 · size: S · trigger: —\n")
    ozet = api._roadmap_ozetle(yuk["bolumler"])
    assert ozet[0]["maddeler"][0]["sema"]["id"] == "TSK-916"
    assert ozet[0]["maddeler"][0]["durum"] == "kapali"


def test_kod_blogu_icindeki_arsiv_satiri_madde_sayilmaz():
    """Kod çiti içindeki örnek satır BELGE DEĞİL — sayılırsa dokümantasyon tahtayı şişirir."""
    metin = ARSIV_BASI + ("```\n"
                          "**[TSK-917] Örnek** — status: DONE(2026-09-06) · born: 2026-09-01 · "
                          "owner: rol1 · size: S · trigger: —\n"
                          "```\n")
    assert _sentetik(metin)["sayim"]["madde_n"] == 0


def test_arsiv_deseni_bullet_deseniyle_AYNI_sabitten_geliyor():
    """Kaynak taraması: uç ikinci bir `\\*\\*\\[` regex'i TANIMLAMAMALI."""
    kaynak = (KOK / "meridian/api.py").read_text(encoding="utf-8")
    tanim = re.findall(r"^_ROADMAP_\w*\s*=\s*re\.compile\(\s*r?\"\^\\\*\\\*\\\[",
                       kaynak, re.M)
    assert len(tanim) == 1, (
        f"`**[` başlık grameri {len(tanim)} kez tanımlanmış — arşiv tanıması "
        "`_ROADMAP_SEMA_BASLIK`i YENİDEN KULLANMALI, kopyalamamalı")

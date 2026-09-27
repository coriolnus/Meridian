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

F. **TABLO BÖLÜNMESİ SESSİZ OLAMAZ (TSK-232, 2026-09-27 — SINIF ÇİVİSİ).** Markdown tablosu, satırları
   arasına `|` ile başlamayan bir satır girdiği yerde BİTER; `api._roadmap_ayristir` alttaki satırları
   başlıksız/ayraçsız bir parça olarak tablodan ÇIKARIR (TSK-235 sonrası her durumda sayılı olarak `tablo_atlanan`a
   yazar — önceden bloğun başında bir başlık+ayraç çifti daha varsa HİÇ kaydetmeden düşürüyordu). VAKA (2026-09-26): TSK-065'in tarihli notu DİK DURUM
   tablosunun satır ARASINA yazıldı ve tahta 13 satırdan 9'a indi — TSK-084/051/085/063 ayrıştırmadan
   düştü; A ve B o dört satırı hiç görmedi, yalnız C'nin "en az 10 satır" tabanı ŞANSLA yakaladı
   (düzeltme 3fd54764). C bir taban çivisidir, sınıf çivisi DEĞİL: 13 satırlık tahtada 3 satırlık bir
   bölünme onu geçerdi. Bu ayak HAM METNİ ayrıştırıcıdan BAĞIMSIZ sayar: §2 açık bölümlerinde `|` ile
   başlayan her satır (ayraç ve başlık satırları hariç) ayrıştırılmış bir tablo satırına karşılık gelmek
   zorundadır; eşitsizlikte DÜŞEN satırlar numarası ve metniyle basılır.

G. **F'NİN NEGATİF KONTROLÜ.** Sentetik 3 satırlık tablo + araya bir not satırı → yardımcı düşen iki
   satırı ADIYLA yakalar; aynı tablo boş satırla bölündüğünde (ayrıştırıcının bilerek tolere ettiği
   biçim) yanlış alarm VERMEZ. Ayrıca GERÇEK tahtaya aynı not satırı enjekte edilir (yol-tutarlı pozitif
   kontrol: sentetik tablo gerçek belgenin yapısından ayrışırsa çivi yine gerçek yapıda ısırır).
"""
import pathlib
import re

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


# =================================================================================================
# F/G — TABLO BÖLÜNMESİ (TSK-232): ham `|` satırı ↔ ayrıştırılmış tablo satırı EŞLEŞMESİ
# =================================================================================================
#: Başlık satırı deseni — ham sayım AYRIŞTIRICIDAN BAĞIMSIZ yürür (ortak körlük olmasın diye
#: `api._ROADMAP_BASLIK` ithal EDİLMEZ; aynı markdown kuralının ikinci, bağımsız okumasıdır).
_HAM_BASLIK = re.compile(r"^(#{1,6})\s+(.*)$")
#: §2 kök başlığı: `§2` ardından RAKAM gelmez (`§20` §2 değildir).
_HAM_KOK_2 = re.compile(r"^§2(?![0-9∞])")


def _ham_ayrac_mi(satir: str) -> bool:
    """Markdown tablo ayraç satırı: yalnız `|`, `-`, `:` ve boşluk; en az bir `-`."""
    k = satir.strip()
    return bool(k) and set(k) <= set("|-: \t") and "-" in k


def _ham_tahta_satirlari(metin: str) -> dict[int, str]:
    """HAM SAYIM: §2'nin açık alt bölümlerinde `|` ile başlayan, ayraç ve başlık OLMAYAN satırlar
    (satır no → metin). Kod çiti (```) içi atlanır. Başlık satırı = bir ayraç satırından önceki son
    boş-olmayan satır `|` ile başlıyorsa o satır. Satırın hangi bölüme ait olduğu, kendisinden önceki
    en yakın başlıktır (ayrıştırıcının tabloyu etkin bölüme bağlamasıyla aynı kural); `#` (seviye 1)
    başlıkları bölüm değiştirmez."""
    beklenen: dict[int, str] = {}
    cit = False
    kok2 = False
    aktif = ""
    onceki_tablo: int | None = None     # son boş-olmayan satır `|` ile başlıyorsa onun numarası
    for i, l in enumerate(metin.split("\n"), 1):
        if l.lstrip().startswith("```"):
            cit, onceki_tablo = not cit, None
            continue
        if cit or not l.strip():
            continue
        hb = _HAM_BASLIK.match(l)
        if hb:
            onceki_tablo = None
            if len(hb.group(1)) == 1:
                continue
            bas = hb.group(2).strip()
            if len(hb.group(1)) == 2:
                kok2 = bool(_HAM_KOK_2.match(bas))
            aktif = bas if kok2 else ""
            continue
        if not l.strip().startswith("|"):
            onceki_tablo = None
            continue
        if not aktif.startswith(ACIK_BOLUM_ONEKLERI):
            onceki_tablo = i
            continue
        if _ham_ayrac_mi(l):
            if onceki_tablo is not None:
                beklenen.pop(onceki_tablo, None)     # ayraçtan önceki `|` satırı BAŞLIKTIR
            onceki_tablo = None
            continue
        beklenen[i] = l.strip()
        onceki_tablo = i
    return beklenen


def _bolunme_farki(metin: str) -> dict:
    """Ham sayım ↔ ayrıştırıcı sayımı. `dusen`: ham metinde tablo satırı olup ayrıştırılmış tabloya
    GİRMEYEN satırlar (sessiz kayıp); `fazla`: ayrıştırılmış olup ham sayımda olmayanlar (olmamalı)."""
    ham = _ham_tahta_satirlari(metin)
    ayr = {s["satir"] for _b, s in _tahta_satirlari(_yuk(metin))}
    return {"ham_n": len(ham), "ayr_n": len(ayr),
            "dusen": sorted(set(ham) - ayr), "fazla": sorted(ayr - set(ham)), "ham": ham}


def _fark_mesaji(f: dict) -> str:
    return (f"ham `|` satırı {f['ham_n']} ↔ ayrıştırılmış tablo satırı {f['ayr_n']}\n"
            + "".join(f"  · DÜŞEN satır {n}: {f['ham'][n][:100]}\n" for n in f["dusen"])
            + "".join(f"  · FAZLA satır {n}\n" for n in f["fazla"]))


def test_f_tahta_tablosu_bolunmemis_ham_ve_ayristirici_sayimi_ESIT():
    """TSK-232 SINIF ÇİVİSİ: §2 açık bölümlerindeki her ham tablo satırı ayrıştırılmış bir satıra
    karşılık gelir. Kırmızıysa: tablo satırlarının ARASINA düzyazı/not/madde satırı girmiş —
    notu tablonun ALTINA taşı (3fd54764 emsali), satırı silme."""
    metin = (pathlib.Path(config.ROOT) / "ROADMAP.md").read_text(encoding="utf-8")
    f = _bolunme_farki(metin)
    assert f["ham_n"] >= 10, f"ham sayım boş ya da çok az ({f['ham_n']}) — sayım körleşmiş olabilir"
    assert not f["dusen"] and not f["fazla"], (
        "§2 TAHTA tablosu BÖLÜNMÜŞ — aşağıdaki satırlar ayrıştırıcıdan SESSİZCE düşüyor "
        "(tahta/uç/tetik taraması onları görmez):\n" + _fark_mesaji(f))


_SENTETIK_BASI = (
    "# k\n\n## §2 TAHTA\n\n"
    "#### DİK DURUM — aşamada ilerleyemez\n\n"
    "| id | name | status | owner | size | trigger |\n"
    "|---|---|---|---|---|---|\n")
_SATIR = "| TSK-9{n} | kalem {n} (WP: WP1) | GATED(kapı) | rol1 | S | tetik |\n"


def test_g_negatif_kontrol_araya_not_satiri_DUSEN_satirlari_yakalar():
    """Kasıtlı kırmızı: 3 satırlık tablonun 1. satırından sonra bir not satırı → 2. ve 3. satır
    ayrıştırıcıdan düşer ve yardımcı İKİSİNİ de satır numarasıyla yakalar."""
    sentetik = (_SENTETIK_BASI + _SATIR.format(n=1)
                + "  Not (TSK-91): tarihli not tablonun ARASINA yazıldı.\n"
                + _SATIR.format(n=2) + _SATIR.format(n=3))
    f = _bolunme_farki(sentetik)
    assert f["ham_n"] == 3 and f["ayr_n"] == 1, _fark_mesaji(f)
    assert [f["ham"][n].split("|")[1].strip() for n in f["dusen"]] == ["TSK-92", "TSK-93"], _fark_mesaji(f)


def test_g_negatif_kontrol_parca_ARDINDAN_yeni_tablo_gelse_de_yakalar():
    """Bölünen parçanın ardından (yalnız boş satırla) YENİ bir tablo başlığı gelirse parça yeni tablonun
    başlığından ÖNCEKİ satırlar olur — TSK-235 sonrası `tablo_atlanan`a sayılı düşer (tabloda değil); ham sayım yakalar."""
    sentetik = (_SENTETIK_BASI + _SATIR.format(n=1)
                + "Not: araya düşen düzyazı.\n"
                + _SATIR.format(n=2) + "\n"
                + "| id | name | status | owner | size | trigger |\n|---|---|---|---|---|---|\n"
                + _SATIR.format(n=4))
    f = _bolunme_farki(sentetik)
    assert [f["ham"][n].split("|")[1].strip() for n in f["dusen"]] == ["TSK-92"], _fark_mesaji(f)


def test_g_bos_satir_BOLMEZ_yanlis_alarm_yok():
    """Ayrıştırıcı tablo satırları arasındaki BOŞ satırı bilerek tolere eder (`api._roadmap_ayristir`
    şerhi, 2026-08-25 ölçümü); ham sayım da onu kesinti saymamalı — yanlış alarm yasanın en pahalı
    arızasıdır."""
    sentetik = (_SENTETIK_BASI + _SATIR.format(n=1) + "\n"
                + _SATIR.format(n=2) + "\n\n" + _SATIR.format(n=3))
    f = _bolunme_farki(sentetik)
    assert f["ham_n"] == 3 and f["ayr_n"] == 3 and not f["dusen"], _fark_mesaji(f)


def test_g_gercek_tahtaya_enjekte_not_satiri_YAKALANIR():
    """Yol-tutarlı pozitif kontrol: GERÇEK ROADMAP'in ilk ≥3 satırlı açık tablosunda 1. satırdan
    sonra bir not satırı enjekte edilir (dosyaya DEĞİL, bellekteki kopyaya); o tablonun geri kalan
    satırlarının TAMAMI düşen olarak yakalanmalı."""
    metin = (pathlib.Path(config.ROOT) / "ROADMAP.md").read_text(encoding="utf-8")
    tablolar = [t for kok in _yuk(metin)["bolumler"] if (kok.get("no") or "") == "§2"
                for b in _gez(kok)
                if (b.get("ham_baslik") or "").lstrip("# ").strip().startswith(ACIK_BOLUM_ONEKLERI)
                for t in b["tablolar"] if t["satir_n"] >= 3]
    assert tablolar, "gerçek tahtada ≥3 satırlı açık tablo yok — pozitif kontrol kurulamıyor"
    hedef = tablolar[0]
    satirlar = metin.split("\n")
    ilk = hedef["satirlar"][0]["satir"]          # 1 tabanlı: enjeksiyon bu satırın HEMEN ardına
    enjekte = "\n".join(satirlar[:ilk] + ["  Not (TSK-232): enjekte edilmiş not satırı."]
                        + satirlar[ilk:])
    f = _bolunme_farki(enjekte)
    beklenen = [s["satir"] + 1 for s in hedef["satirlar"][1:]]
    assert f["dusen"] == beklenen, _fark_mesaji(f)

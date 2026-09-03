"""test_pano_komsu_kopyalar_v403.py — Bildiri×3 · BayatSerit/YukleniyorIskeleti×2 ·
Olculemedi×13 KOMŞU KOPYALARININ TEK KAYNAĞA İNDİĞİNİN BEKÇİSİ (TSK-121, 2026-09-03).

ÖLÇÜM (Explore keşfi, `.superpowers/sdd/2026-09-03-tsk121/kesif.md`): TSK-113 `Kapi` kopyalarını
7'den 1'e indirirken üç komşu sınıfı KAPSAM DIŞI bırakmıştı ve kendi şerhinde bunu yazmıştı
(`parcalar/kapi.tsx`: "Bildiri/BayatSerit kopyaları ogrenme/analiz/ajan'da — o ayrı bir kalem").
Ölçülen kopyalar: `Bildiri` 3 tanım (markup birebir, prop imzası ayrı — ajan `{govde,uyari}`
vs analiz/ogrenme `{metin,tonu}`), `BayatSerit`/`YukleniyorIskeleti` ikişer (analiz≡ogrenme,
byte-birebir), `Olculemedi` ON BİR düz tanım + `OlculemediHucre` iki tanım (analiz≡ogrenme,
birebir) = 13. Olculemedi'nin gövdeleri GERÇEKTEN ayrışıyor (ikon/tooltip/prop-tipi farklı) —
TSK-113'ün aksine düz paylaşım YETMEZ, kabuk enjeksiyonu (`olculemediKur`) şart.

ÇARE: `ui/src/pano/parcalar/bildiri.tsx` (düz paylaşılan `Bildiri`), `parcalar/bayat.tsx` (düz
paylaşılan `BayatSerit`/`YukleniyorIskeleti`), `parcalar/olculemedi.tsx` (`olculemediKur(aile, ek)`
— TSK-113'ün `kapiKur(kabuk)` deseninin aynısı: KARAR/gövde tek yerde, ÇAĞRI YERİ kendi ailesini
seçer). Ölçülen altı aile — `satir` (kuyruk≡sistem; kimlik/yetki aynı ailenin maxW/altçizgi
varyantı), `hucre` (analiz≡ogrenme'nin hem blok-biçimli `Olculemedi`si hem `OlculemediHucre`si —
ikisi de aynı iki dosyanın ürünü, `bicim` ek'iyle ayrılır), `kpi` (bugun, KPI başlığı stili),
`span` (ajan tek-span-altçizgi · FlattenKapisi tek-span-italik-önekli — ikisi de TEK <span>
ama farklı stil), `ikonlu` (kanban, Info ikonlu), `tooltip` (portfoy, Radix `Tooltip`, `kisa`
STRİNG idi → `kisaMetin`e taşındı, `kisa` artık HER AİLEDE boolean).

ÇİVİNİN SINIFI VE ZAYIFLIĞI AÇIKÇA YAZILI (v286/v288/v314/v323/v324/v373/v378/v380/v381/v384
ailesinin kurulu cevabı): bu dosya TSX'i METİN olarak okur; ölçtüğü şey davranış DEĞİL,
davranışı üreten satırın varlığı ve biçimidir. Zayıflık MUTASYONLA telafi edilir — üç mutasyon
denendi ve raporda tablolanır: (1) bir yüzeye yerel `function Olculemedi` geri koymak
`test_OLCULEMEDI_tanimi_PANO_GENELINDE_TAM_BIR`i kırmalı, (2) kabuk tablosundan `tooltip`
ailesini düşürmek `test_KABUK_AILE_ADLARI_sabit_listeyle_ESIT`i kırmalı, (3) `test_arayuz_dili_
v323.py`nin HAFIZA filtresini geri koymak o dosyanın pano-geneline kalibre edilmiş `okunan >=`
tabanını kırmalı (bu üçüncü mutasyon BURADA değil, o dosyanın kendi ölçümünde doğrulanır).
"""
from __future__ import annotations

import pathlib
import re

from tests.test_pano_bayat_govde_v381 import kopyalari_bul, soy

KOK = pathlib.Path(__file__).resolve().parents[1]
PANO = KOK / "ui/src/pano"

BILDIRI = PANO / "parcalar/bildiri.tsx"
BAYAT = PANO / "parcalar/bayat.tsx"
OLCULEMEDI = PANO / "parcalar/olculemedi.tsx"

AJAN_ORTAK = PANO / "yuzeyler/ajan/ortak.tsx"
#: `PortfoyYuzey.tsx` `yuzeyler/portfoy/` ALTINDA DEĞİL (üst dizindeki ana yüzey dosyası) —
#: ilk taramada kaçmıştı, `npm run kontrol` üç `kisa=` string çağrısını (+ iki `kisa={ifade}`
#: çağrısını) TS hatası olarak yakaladı (ölçüm günü). Kapsam bu yüzden dört dosyaya çıktı.
PORTFOY_DOSYALARI = (
    PANO / "yuzeyler/portfoy/MutabakatMasasi.tsx",
    PANO / "yuzeyler/portfoy/SeansIciEmir.tsx",
    PANO / "yuzeyler/portfoy/PozisyonTablosu.tsx",
    PANO / "yuzeyler/PortfoyYuzey.tsx",
)


def test_olculen_dosyalar_YERINDE():
    """KÖRLÜK ALARMI: yol bayatlarsa aşağıdaki her tarama sessizce boş/az döner ve çivi
    "temiz" der. Dosya varlığı ve asgari boyut AYRI ölçülür."""
    for p in (BILDIRI, BAYAT, OLCULEMEDI, AJAN_ORTAK, *PORTFOY_DOSYALARI):
        assert p.is_file(), f"ölçülecek dosya yok: {p}"
        assert len(p.read_text(encoding="utf-8")) > 150, f"dosya beklenmedik biçimde küçük: {p}"


# ============================================================================
# (1) TEK TANIM — Bildiri / BayatSerit / YukleniyorIskeleti / Olculemedi / OlculemediHucre
# ============================================================================

_BILDIRI_TANIM = re.compile(r"function Bildiri\(")
_BAYATSERIT_TANIM = re.compile(r"function BayatSerit\(")
_ISKELET_TANIM = re.compile(r"function YukleniyorIskeleti\(")
_OLCULEMEDI_TANIM = re.compile(r"function Olculemedi\(")
_OLCULEMEDI_HUCRE_TANIM = re.compile(r"function OlculemediHucre\(")


def test_BILDIRI_tanimi_PANO_GENELINDE_TAM_BIR():
    bulunan = [p.relative_to(KOK).as_posix() for p in kopyalari_bul(_BILDIRI_TANIM)]
    assert bulunan == ["ui/src/pano/parcalar/bildiri.tsx"], (
        f"`function Bildiri(` tanımı tek kaynakta değil: {bulunan}")


def test_BAYATSERIT_tanimi_PANO_GENELINDE_TAM_BIR():
    bulunan = [p.relative_to(KOK).as_posix() for p in kopyalari_bul(_BAYATSERIT_TANIM)]
    assert bulunan == ["ui/src/pano/parcalar/bayat.tsx"], (
        f"`function BayatSerit(` tanımı tek kaynakta değil: {bulunan}")


def test_YUKLENIYOR_ISKELETI_tanimi_PANO_GENELINDE_TAM_BIR():
    bulunan = [p.relative_to(KOK).as_posix() for p in kopyalari_bul(_ISKELET_TANIM)]
    assert bulunan == ["ui/src/pano/parcalar/bayat.tsx"], (
        f"`function YukleniyorIskeleti(` tanımı tek kaynakta değil: {bulunan}")


def test_OLCULEMEDI_tanimi_PANO_GENELINDE_TAM_BIR():
    """MUTASYON-1: herhangi bir yüzeye yerel `function Olculemedi(...) {` geri koymak bu
    testi kırmalı — `olculemediKur` iç kapatması TEK yerde (`parcalar/olculemedi.tsx`)
    tutulduğu sürece tarama tam 1 döner."""
    bulunan = [p.relative_to(KOK).as_posix() for p in kopyalari_bul(_OLCULEMEDI_TANIM)]
    assert bulunan == ["ui/src/pano/parcalar/olculemedi.tsx"], (
        f"`function Olculemedi(` tanımı tek kaynakta değil (beklenen: parcalar/olculemedi.tsx): {bulunan}")


def test_OLCULEMEDI_HUCRE_tanimi_SIFIR():
    """`OlculemediHucre` artık yerel `function` DEĞİL — `olculemediKur("hucre", {bicim:
    "satirici", ...})` bağıdır (`const OlculemediHucre = ...`). Tarama SIFIR dönmeli."""
    bulunan = [p.relative_to(KOK).as_posix() for p in kopyalari_bul(_OLCULEMEDI_HUCRE_TANIM)]
    assert bulunan == [], f"`function OlculemediHucre(` hâlâ yerel bir yüzeyde: {bulunan}"


def test_TANIM_TARAYICILARI_sessizce_bos_DEGIL():
    """POZİTİF KONTROL (v314 disiplini): beş desen de sentetik bir tanımı YAKALAMALI, aksi
    hâlde yukarıdaki "tam 1"/"sıfır" cümleleri regex'in kırılmasıyla aynı görünürdü."""
    assert _BILDIRI_TANIM.search("function Bildiri({ ikon }) {")
    assert not _BILDIRI_TANIM.search("function BildiriKarti({ ikon }) {")
    assert _BAYATSERIT_TANIM.search("function BayatSerit({ hata }) {")
    assert _ISKELET_TANIM.search("export function YukleniyorIskeleti({ yukseklik }) {")
    assert _OLCULEMEDI_TANIM.search("  return function Olculemedi(o) {")
    assert not _OLCULEMEDI_TANIM.search("function OlculemediHucre(o) {")
    assert _OLCULEMEDI_HUCRE_TANIM.search("function OlculemediHucre({ neden }) {")


# ============================================================================
# (2) OLCULEMEDI KABUK TABLOSU — ölçülen altı aile, SABİT LİSTE
# ============================================================================

_AILE_LISTESI = ("satir", "hucre", "kpi", "span", "ikonlu", "tooltip")


def _kabuk_aileleri() -> list[str]:
    s = soy(OLCULEMEDI)
    m = re.search(r"const KABUK[^{]*=\s*\{(.*?)\n\};", s, re.S)
    assert m, "KABUK tablosu okunamadı — desen bayat ya da tablo taşındı"
    return re.findall(r"^\s*(\w+):", m.group(1), re.M)


def test_KABUK_AILE_ADLARI_sabit_listeyle_ESIT():
    """MUTASYON-2: kabuk tablosundan `tooltip` (ya da başka bir aile) satırını düşürmek bu
    testi kırmalı — yeni bir aile sessizce doğduğunda ya da biri sessizce kaybolduğunda
    ölçülen küme sabit listeden ayrışır."""
    ailer = _kabuk_aileleri()
    assert ailer == list(_AILE_LISTESI), (
        f"KABUK tablosunun aile kümesi değişti: {ailer} (beklenen: {list(_AILE_LISTESI)})")


def test_KABUK_TARAYICISI_sessizce_bos_DEGIL():
    """POZİTİF KONTROL: sentetik bir tabloda altı anahtarı da bulabilmeli."""
    ornek = (
        "export const KABUK: Record<OlculemediAilesi, Cizici> = {\n"
        "  satir: (o, ek) => 1,\n"
        "  hucre: (o, ek) => 2,\n"
        "  kpi: (o) => 3,\n"
        "  span: (o, ek) => 4,\n"
        "  ikonlu: (o) => 5,\n"
        "  tooltip: (o) => 6,\n"
        "};\n"
    )
    m = re.search(r"const KABUK[^{]*=\s*\{(.*?)\n\};", ornek, re.S)
    assert m and re.findall(r"^\s*(\w+):", m.group(1), re.M) == list(_AILE_LISTESI)


# ============================================================================
# (3) BEDEL — çağrı yeri prop eşlemeleri (satiye §4 bedel yasası)
# ============================================================================

def test_AJAN_BILDIRI_CAGRISI_metin_tonu_KULLANIYOR():
    """Ajan yüzeyinin eski `{govde, uyari}` imzası ortak `Bildiri`nin `{metin, tonu}`
    sözleşmesine ÇAĞRI YERİNDE eşlenmeli — bileşenin kendisi artık burada tanımlı değil."""
    s = soy(AJAN_ORTAK)
    assert "function Bildiri(" not in s, "ajan hâlâ kendi Bildiri tanımını taşıyor"
    assert re.search(r'tonu="notr"', s), "oturum dalı `tonu=\"notr\"`e eşlenmemiş"
    assert re.search(r'tonu="uyari"', s), "bos dalı `tonu=\"uyari\"`ya eşlenmemiş"
    assert "govde=" not in s, "eski `govde=` prop'u çağrı yerinde hâlâ duruyor"
    assert not re.search(r"\buyari=", s), "eski `uyari=` prop'u çağrı yerinde hâlâ duruyor"


def test_PORTFOY_CAGRI_YERLERI_kisaMetin_KULLANIYOR():
    """Ortak `Olculemedi`de `kisa` artık HER AİLEDE boolean (kısaltma bayrağı) — portföyün
    eski `kisa: string` (kısa ETİKET metni) `kisaMetin`e taşındı. `tooltip` ailesi (yalnız
    portföy) `kisa` BOOLEAN'ını hiç kullanmaz — bu dört dosyada `kisa=` (dizge YA DA ifade)
    SIFIR, `kisaMetin=` DOLU olmalı. Ölçüm (2026-09-03, TSK-121, `PortfoyYuzey.tsx` dahil dört
    dosya): 28 dizge-değerli (`kisaMetin="…"`) + 2 ifade-değerli (`kisaMetin={…}`, yalnız
    `PortfoyYuzey.tsx`) = 30 çağrı taşındı; burada yalnız dizge-değerli olan ölçülür (ifade
    formu regex'le güvenilir sayılamaz — kapsam beyanlı)."""
    toplam_kisa_metin = 0
    kirli: list[str] = []
    for p in PORTFOY_DOSYALARI:
        s = soy(p)
        # `\bkisa=` "kisaMetin=" İÇİNDE eşleşmez ("kisa" sonrası "Metin" gelir, "=" gelmez) —
        # ayrı bir hariç-tutma gerekmiyor, POZİTİF KONTROL aşağıdaki testte.
        if re.search(r"\bkisa=", s):
            kirli.append(p.relative_to(KOK).as_posix())
        toplam_kisa_metin += len(re.findall(r'\bkisaMetin="', s))
    assert kirli == [], f"eski `kisa=` (boolean/dizge/ifade) çağrısı hâlâ duruyor: {kirli}"
    # TABAN: 2026-09-03 ölçümü 28 dizge-değerli çağrıydı (+2 ifade-değerli, burada ölçülmüyor);
    # tam sayı DEĞİL çünkü çağrı silmek meşru bir iştir.
    assert toplam_kisa_metin >= 25, (
        f"portföy yüzeylerinde yalnız {toplam_kisa_metin} `kisaMetin=\"…\"` çağrısı okundu (2026-09-03: 28)")


def test_KISA_DESENI_kisaMetin_ile_KARISMIYOR():
    """POZİTİF KONTROL (v314 disiplini): `\\bkisa=` `kisaMetin=`in İÇİNDE yanlışlıkla
    eşleşmemeli — eşleşseydi yukarıdaki 'temiz' hükmü hiçbir zaman kirli döndüremezdi."""
    assert re.search(r"\bkisa=", 'kisa="ayna yok"')
    assert re.search(r"\bkisa=", "kisa={x}")
    assert not re.search(r"\bkisa=", 'kisaMetin="ayna yok"')
    assert not re.search(r"\bkisa=", "kisaMetin={x}")

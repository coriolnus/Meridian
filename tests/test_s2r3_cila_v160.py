"""v160 — S2R-3 (cila): bekçi dürüstlük yüzeyi · gölge bölünmesi · palet kapsamı · blok ritmi.

BU DOSYANIN ÖLÇTÜĞÜ KUSUR SINIFI: **cilanın sessiz geri alınması.** S2R-1 kabuğu, S2R-2 göçü
kurdu; S2R-3'ün işi ölçülebilir SÖZLEŞMELER bırakmak. Cila turlarının kendine özgü riski şudur:
yaptıkları iş "görsel" sanıldığı için testsiz bırakılır ve bir sonraki tur onları farkında olmadan
geri alır (bir satır içi `style="margin-top:18px"`, bir `t-no` çipi, palete eklenmeyen bir bölüm).

DÖRT AYRI ARIZA SINIFI ÇİVİLENİR:

  A) ÖLÇÜLEMEYENİ TEMİZ SAYMAK (denetim C21/C22'nin pano ayağı). watchdog düşen bir dedektörü
     `_DEDEKTOR_BOS` İSKELETİYLE döndürür — yani `starved: []`, `stale: []`, `lost: []`. Panonun
     `_patOK`'u iki değerliydi ve o boş listeleri "bulgu yok" diye okuyup satırı YEŞİL basıyordu:
     ölçülemeyen bir hüküm, ölçülmüş bir temizlik kılığında. Ters yön de yanlıştı (determinism
     fail-closed KIRMIZI basılıyordu). Test ÜRETİCİNİN KENDİ İSKELETİNİ okur (import ile), elle
     yazılmış bir taklidini değil — üretici/tüketici paritesi ancak böyle ölçülür.
  B) YARIM BÖLÜNME. Gölge-varyant portföyleri bir kart gövdesinden çıkarılıp `golge` bölümüne
     taşındı. Bir kart gövdesini bölerken en olası kayıp, alt bloğun okuduğu alanların bir
     kısmının taşınmamasıdır (YASA-6, HTTP→DOM katmanı — statik Python grafı bunu göremez).
  C) HARİTASI OLMAYAN ODA. Palet yirmi bölümün beşine gidebiliyordu; kalan on beşin adı orada
     hiç geçmiyordu. Bir kez boş dönen arama bir daha denenmez.
  D) İKİ YERDE TUTULAN RİTİM. Kural CSS'te yazılıydı, app.js otuz bir kaba satır içi marj
     basıyordu ve satır içi stil kuralı HER ZAMAN yener — sözleşme fiilen yoktu.

TESTLER KAYNAĞA BAKAR ve saf çekirdekleri NODE İLE KOŞTURUR (repo deseni: v139/v151/v152/v156).
Tarayıcı ve yerel sunucu YOK (CLAUDE.md §5).
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

SRC = pathlib.Path(__file__).resolve().parents[1]
WEB = SRC / "meridian" / "web"
APPJS = (WEB / "app.js").read_text()
INDEX = (WEB / "index.html").read_text()
PALET_YOL = WEB / "palette.js"
PALET = PALET_YOL.read_text()
CSP_TEST = (SRC / "tests" / "test_web_csp_uyum.py").read_text()
CSS = re.search(r"<style>(.*?)</style>", INDEX, re.S).group(1)

NODE = shutil.which("node")

# Yorum satırları çıkarılmış hâl (v154/v155/v156 deseni): bir kuralın GEREKÇESİNİ anlatan yorum,
# o kuralın ihlali sanılmamalı — "artık t-no kullanmıyoruz" cümlesi tam da aranan dizgiyi içerir.
KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))


def _govde(bas: str, son: str, kaynak: str = APPJS) -> str:
    i = kaynak.index(bas)
    return kaynak[i:kaynak.index(son, i)]


def _node(betik: str):
    if not NODE:
        pytest.skip("node bulunamadı — saf çekirdek testleri koşulamıyor (ÖLÇÜLMEDİ)")
    r = subprocess.run([NODE, "-e", betik], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"node hatası:\n{r.stderr}"
    return json.loads(r.stdout)


# =================================================================================================
# 1) BEKÇİ DÜRÜSTLÜK YÜZEYİ — ÜÇÜNCÜ DURUM (denetim C21/C22 pano ayağı)
# =================================================================================================
# Hüküm fonksiyonları `opParcalar()`ın İÇİNDE yaşıyor (yerel `ig`/`d` bağlamına yakın durmaları
# doğru). Node'da koşturmak için dilim SÖKÜLÜR: dilimin sınırları iki çıpaya bağlı ve çıpalardan
# biri kayarsa test AÇIKÇA kırılır — sessizce boş bir dilim ölçmez.
_PAT_BAS = "  const _say = x => Array.isArray(x)"
_PAT_SON = "  const patRows = Object.keys(PAT_TR)"


def _pat_dilimi() -> str:
    dilim = _govde(_PAT_BAS, _PAT_SON)
    for ad in ("_say", "_patOK", "_patOlculemedi", "_patDurum", "_patOlcumYok", "_patNote",
               "PAT_CIP"):
        assert f"const {ad}" in dilim, f"{ad} hüküm diliminde yok — bekçi yüzeyi yeniden yazılmış"
    return dilim


def _pat_calistir(ifade: str):
    """Hüküm dilimini Node'da kur ve `ifade`yi değerlendir. Kaynağa DEĞİL, davranışa bakar."""
    return _node(
        "(function(){\n" + _pat_dilimi() +
        "\nconst _out = (" + ifade + ");\n"
        "process.stdout.write(JSON.stringify(_out === undefined ? null : _out));\n})();"
    )


def _dedektor_bos() -> dict:
    """ÜRETİCİNİN KENDİ İSKELETİ. Elle kopyalanan bir taklit, tam da ölçmek istediğimiz
    üretici/tüketici sapmasını gizlerdi: iskelet değişirse bu test onunla birlikte değişmeli."""
    sys.path.insert(0, str(SRC))
    from meridian import watchdog
    return dict(watchdog._DEDEKTOR_BOS)


def _dusen(ad: str) -> dict:
    """watchdog.integrity_report._tut()'un düşen dedektör için ÜRETTİĞİ sözlüğün birebir kopyası
    (kaynak: watchdog.py `_tut` except dalı)."""
    return {**_dedektor_bos().get(ad, {}), "ok": False, "dedektor_dustu": True,
            "olculemedi": True, "error": "OSError: [Errno 2] No such file"}


DESENLER = ["production", "conservation", "determinism", "coherence", "monotonicity",
            "ownership", "parity"]


def test_dusen_dedektor_YEDI_desende_de_UCUNCU_duruma_duser():
    """A sınıfının doğrudan kapısı. Yalıtım iskeleti BOŞ listeler döndürdüğü için eski iki
    değerli hüküm üç desende (üretkenlik/korunum/tutarlılık) YEŞİL basıyordu."""
    yukler = {ad: _dusen(ad) for ad in DESENLER}
    sonuc = _pat_calistir(
        "Object.fromEntries(Object.entries(%s).map(([k, v]) => [k, _patDurum(k, v)]))"
        % json.dumps(yukler))
    for ad in DESENLER:
        assert sonuc[ad] == "olculemedi", (
            f"{ad}: düşen dedektör '{sonuc[ad]}' basıyor — ölçülemeyen hüküm ne temiz ne ihlaldir")


def test_TEST_KENDINI_KANITLAR_eski_iki_degerli_hukum_YESIL_derdi():
    """Kıramayan bir test yeşil veren bir süstür. Üç desende eski `_patOK` DÜŞEN dedektöre
    `true` (yani 'temiz') diyor olmalı — demiyorsa bu dosya var olmayan bir arızayı ölçüyor."""
    yukler = {ad: _dusen(ad) for ad in ("production", "conservation", "coherence")}
    eski = _pat_calistir(
        "Object.fromEntries(Object.entries(%s).map(([k, v]) => [k, _patOK(k, v)]))"
        % json.dumps(yukler))
    assert all(eski.values()), (
        "eski iki değerli hüküm artık düşen dedektöre 'temiz' DEMİYOR — ya iskelet değişti ya da "
        f"bu test ölçtüğünü sandığı şeyi ölçmüyor: {eski}")


def test_determinism_fail_closed_KIRMIZI_basilmaz():
    """C22: bar dizini okunamadığında `{"ok": False, "olculemedi": True}` döner. Eski son dal
    `v.ok !== false` diye baktığı için bunu İHLAL basardı — watchdog'un kendi cümlesiyle,
    "ölçülemeyen bir hükmü ihlal diye anlatmak da bir uydurmadır"."""
    yuk = {"ok": False, "olculemedi": True, "error": "PermissionError: bars/",
           "detail": "bar dizini okunamadı — ÖLÇÜLEMEDİ ('temiz' DEĞİL)"}
    assert _pat_calistir('_patDurum("determinism", %s)' % json.dumps(yuk)) == "olculemedi"
    assert _pat_calistir('_patDurum("determinism", %s)' % json.dumps(
        {"ok": True, "appended": 61})) == "temiz"


def test_olculmus_hukumler_DEGISMEDI():
    """Cila bir davranış değişikliği DEĞİL: ölçülmüş temizlik yeşil, ölçülmüş ihlal kırmızı
    kalır. Üçüncü durumu eklerken ilk ikisini kaydırmak, arızayı büyütmek olurdu."""
    ornek = {
        ("production", "temiz"):  {"ok": 17, "total": 17, "starved": [], "waiting": []},
        ("production", "ihlal"):  {"ok": 16, "total": 17, "starved": [{"name": "breadth"}]},
        ("conservation", "temiz"): {"plans": 9, "traded": 4, "no_fill": 5, "unexplained": 0},
        ("conservation", "ihlal"): {"plans": 9, "traded": 4, "no_fill": 0, "unexplained": 5},
        ("coherence", "temiz"):   {"ok": 3, "total": 3, "stale": []},
        ("coherence", "ihlal"):   {"ok": 2, "total": 3, "stale": [{"artifact": "cal", "behind_h": 30}]},
        ("ownership", "temiz"):   {"ok": True, "lost": []},
        ("ownership", "ihlal"):   {"ok": True, "lost": [{"file": "a.json", "field": "b"}]},
        ("monotonicity", "temiz"): {"ok": True, "tracked": 12, "regressions": []},
        ("monotonicity", "ihlal"): {"ok": True, "tracked": 12,
                                    "regressions": [{"field": "n", "was": 9, "now": 7}]},
        ("parity", "temiz"):      {"rows": [{"check": "a", "ok": True}], "ok": True},
        ("parity", "ihlal"):      {"rows": [{"check": "a", "ok": False}], "ok": False},
    }
    istek = [[k, v] for (k, _), v in ornek.items()]
    beklenen = [b for (_, b) in ornek]
    olculen = _pat_calistir("%s.map(([k, v]) => _patDurum(k, v))" % json.dumps(istek))
    assert olculen == beklenen, dict(zip([k for k, _ in ornek], zip(olculen, beklenen)))


def test_olculemedi_satiri_MAKINE_OKUNUR_ad_tasir():
    """Operatörün panoda okuduğu ad ile obs günlüğünde (`integrity_detector_failed`) ve alarm
    katmanında greplediği ad AYNI olmalı. Yalnız Türkçe bir cümle yazmak panoyu günlükten
    koparırdı: 'ölçülemedi' diye grep atacak kimse yok."""
    metin = _pat_calistir('_patNote("production", %s)' % json.dumps(_dusen("production")))
    for jeton in ("olculemedi", "detector_failed"):
        assert jeton in metin, f"bekçi ayrıntı satırında '{jeton}' geçmiyor: {metin!r}"
    assert "ÖLÇÜLEMEDİ" in metin, "satır Türkçe hükmü de söylemeli — jeton tek başına okunmaz"
    assert "OSError" in metin, "hata metni yutulmuş — YASA 4"
    # Yalnız `olculemedi` taşıyan (dedektör yalıtımı devrede DEĞİL) hâl `detector_failed` DEMEZ:
    # olmayan bir yalıtım olayını rapor etmek uydurma olurdu.
    sade = _pat_calistir('_patNote("determinism", %s)'
                         % json.dumps({"ok": False, "olculemedi": True, "error": "PermissionError"}))
    assert "olculemedi" in sade and "detector_failed" not in sade


def test_UCUNCU_DURUM_ne_yesil_ne_kirmizi_ve_YENI_RENK_ICAT_ETMEZ():
    """Nötr kanal UYDURULMADI: `t-vi` bu panoda zaten 'ölçüm yok / hüküm yok' demek (sağlayıcı
    kartı 'çağrı yok', defter sözleşmesi 'boş', trend kitabı 'DOĞMADI'). İkinci bir nötr renk,
    üç ay sonra 'hangi gri neydi?' sorusunu doğururdu."""
    cip = _pat_calistir("PAT_CIP")
    assert set(cip) == {"temiz", "ihlal", "olculemedi"}, f"üç durum yok: {sorted(cip)}"
    assert cip["temiz"][1] == "t-go" and cip["ihlal"][1] == "t-no"
    assert cip["olculemedi"][1] not in ("t-go", "t-no"), "ölçülemedi yeşil ya da kırmızı basıyor"
    assert cip["olculemedi"][1] == "t-vi", (
        "nötr kanal `t-vi` değil — panoda ikinci bir 'hüküm yok' rengi doğmuş")
    # ve o çip GERÇEKTEN tanımlı bir sınıf olmalı (uydurulmuş bir sınıf sessizce stilsiz kalır)
    assert ".t-vi{" in CSS


def test_URETICI_TUKETICI_ALAN_ADLARI_ayni():
    """Arızanın kökü bir ALAN ADI sapmasıydı: watchdog iki yeni alan yazıyordu, pano ikisini de
    bilmiyordu. Bağ iki yönlü çivilenir — biri yeniden adlandırılırsa test söyler."""
    wd = (SRC / "meridian" / "watchdog.py").read_text()
    for alan in ("dedektor_dustu", "olculemedi"):
        assert alan in wd, f"watchdog artık '{alan}' üretmiyor — panonun okuması öksüz kaldı"
        assert alan in KOD, f"pano '{alan}' alanını okumuyor — düşen dedektör yeşil görünür"


def test_kac_dedektorun_olcemedigi_BASLIKTA_gorunur():
    """Yedi satırın içinde tek bir nötr çipi kaçırmak kolaydır; 'yedi desen temiz' izlenimi tam
    da bu kaçışla doğar. Sayı kartın başlığında da durur."""
    s5 = _govde('const s5 = `<div class="card rise"><h2 class="t">Bölüm 5', "\n  // ------")
    assert "patOlcumsuz" in s5, "ölçülemeyen dedektör sayısı kart başlığında görünmüyor"
    assert "const patOlcumsuz" in KOD


def test_saglayici_karti_da_OLCULEMEDIYI_kirmizi_basmaz():
    """Aynı kusur sınıfı ikinci bir kartta yaşıyordu: sağlık OKUMASININ düşmesi sağlayıcının
    ARIZALI olduğu anlamına gelmez ve o hüküm zaten ayrı bir satırda (`SON ÇAĞRI BAŞARISIZ`)
    yaşıyor. Aynı turda aynı dille kapandı."""
    sag = _govde("const sSag = (() => {", "\n  // ---------- ")
    m = re.search(r'if \(p\.olculemedi\).*?_chip\("ÖLÇÜLEMEDİ", "(t-\w+)"\)', sag, re.S)
    assert m, "sağlayıcı kartının ölçülemedi satırı bulunamadı"
    assert m.group(1) == "t-vi", f"sağlayıcı ölçülemedi çipi '{m.group(1)}' — nötr olmalı"


# =================================================================================================
# 2) GÖLGE BÖLÜNMESİ (ADR içerik borcu #1) — OKUYUCU KORUNUMU
# =================================================================================================
# `shadow_variants`ın panoda okunan HER alanı. Kart gövdesi bölünürken en olası kayıp, alt
# bloğun okuduğu alanların bir kısmının taşınmamasıdır ve arka uç onları üretmeye devam eder.
SV_ALANLARI = ["sv.n_satir", "sv.son_karar", "sv.kumulatif_ayrisma", "sv.k_variants",
               "sv.rol", "sv.durum"]


def test_golge_varyant_kendi_kartina_cikti_ve_golge_bolumune_indi():
    """S2R-2'nin beyanlı borcu: blok Hermes karnesi kartının bir ALT BAŞLIĞIYDI, çünkü göç
    sözleşmesi 'bölüm taşı, kart gövdesi yeniden yazma'ydı. Cila turunun işi o gövdeyi bölmekti."""
    assert "const sGolgeVaryant = (() => {" in APPJS, "gölge-varyant kartı ayrıştırılmamış"
    hermes_kart = _govde("  const sHermes = (() => {", "\n  // ---------- GÖLGE-VARYANT")
    assert "Gölge-varyant portföyleri" not in hermes_kart, \
        "gölge-varyant başlığı hâlâ Hermes karnesi kartının içinde"
    assert "shadow_variants" not in hermes_kart, \
        "Hermes karnesi hâlâ shadow_variants okuyor — bölünme yarım"
    golge = _govde("RENDER.golge = async () => {", "\n};")
    assert "p.sGolgeVaryant" in golge, "gölge bölümü varyant kartını yazmıyor"
    assert "p.sTrend" in golge, "canlı gölge-kitap gölge bölümünden düşmüş"


def test_shadow_variants_ALAN_OKUMALARI_BIREBIR_korundu():
    """Kusur B. Başlığı taşıyıp gövdenin bir alanını düşürmek, o alanı arka uçta öksüz bırakır
    ve codelaw'ın GÖREMEDİĞİ HTTP→DOM katmanında olur."""
    kart = _govde("  const sGolgeVaryant = (() => {", "\n  // ---------- ")
    for alan in SV_ALANLARI:
        assert alan in kart, f"{alan} taşınmamış — arka uç alanı öksüz kalır (YASA-6)"
    # ÇOKLU-KARŞILAŞTIRMA PAYDASI TABLOYLA AYNI KARTTA: şerh rakamdan ayrılamaz.
    assert "ÇOKLU-KARŞILAŞTIRMA PAYDASI" in kart and "k_variants" in kart


def test_iki_hal_AYRI_cumle_kalir():
    """`sv` yoksa kart hiç doğmaz (uç servis etmiyor); `n_satir` sıfırsa kart DOĞAR ve
    `sv.durum`u yazar. 'defter boş' ile 'ölçüm yok' bu panoda asla aynı ekran değildir."""
    kart = _govde("  const sGolgeVaryant = (() => {", "\n  // ---------- ")
    assert re.search(r"if \(!sv\) return \"\";", kart), "ölçüm yok hâli boş kart uyduruyor"
    assert "sv.durum" in kart, "defter boş hâlinde arka ucun kendi cümlesi basılmıyor"


def test_golge_altyazisi_ARTIK_baska_sayfaya_yollamiyor():
    """S2R-2'de altyazı 'öteki gölge kol Karne bölümünde' diyordu ve bu DÜRÜSTTÜ ama bir borç
    beyanıydı. Borç ödendiğine göre cümle de kalkmalı: ödenmiş bir borcu anlatan altyazı,
    okuru var olmayan bir yere gönderir."""
    golge = _govde("RENDER.golge = async () => {", "\n};")
    for kalinti in ("Hermes karnesi kartının içinde", "yukarıdaki Karne bölümü",
                    "bu tur ayrıştırılmadı"):
        assert kalinti not in golge, f"gölge altyazısında ödenmiş borç beyanı duruyor: {kalinti}"


def test_ozdegerlendirme_KENDI_KARTINDA_ve_OGRENMEDE_kaldi():
    """ADR içerik borcu #2 — hüküm: YERİNDE KALIR (gerekçe ADR Ek C'de, ölçüldü).
    `selfreview._attention()` sekiz kural ailesinin altısı öğrenme katmanının hükmüdür; iki
    sağlık satırının Gözetim'de zaten evi var (MECHANISM_STALE alarmı → gelen kutusu).
    Ama kart AYRIŞTIRILDI: bir DİKKAT listesi, 'MLOps & Hermes' başlıklı bir tesisat kartının
    dip başlığı olamaz."""
    assert "const sOzDeg = (() => {" in APPJS, "öz-değerlendirme kendi kartına ayrılmamış"
    s3 = _govde('  const s3 = `<div class="card rise"><h2 class="t">Bölüm 3', "\n  // ----------")
    assert "selfreview_summary" not in s3, "öz-değerlendirme hâlâ MLOps kartının içinde"
    hermes = _govde("RENDER.hermes = async () => {", "\n};")
    assert "op.sOzDeg" in hermes, "öz-değerlendirme kartı Öğrenme'de çizilmiyor"
    gozetim = _govde("RENDER.operasyon = async () => {", "\n// ---- PORTFÖY")
    assert "sOzDeg" not in gozetim, \
        "kart Gözetim'e de konmuş — 'aynı soruya iki yerden cevap' operatörün asıl şikâyetiydi"
    # Kart, sağlık yarısının nerede yaşadığını EKRANDAN söyler (okur 'burada mı, orada mı?' diye
    # sormak zorunda kalmasın).
    kart = _govde("  const sOzDeg = (() => {", "\n  // ---------- ")
    assert "MECHANISM_STALE" in kart and "gelen kutusu" in kart


def test_yeni_iki_parca_bir_EVE_dustu():
    """v156'nın 'her parça bir eve düşmeli' kuralı iki yeni anahtar için de geçerli: üretilip
    hiçbir sayfaya konmayan bir parça, kartı silmekle aynı sonucu verir ama kodda VARMIŞ durur."""
    ret = re.search(r"return \{ alarm: alarmButce\(d\.alarm_butcesi\),(.*?)\};", APPJS, re.S)
    assert ret and "sGolgeVaryant" in ret.group(1) and "sOzDeg" in ret.group(1)
    tuketiciler = APPJS[APPJS.index("RENDER.mutabakat = async () => {"):]
    for k in ("sGolgeVaryant", "sOzDeg"):
        assert re.search(r"\bp?o?p?\.%s\b" % k, tuketiciler), f"{k} hiçbir sayfada yazılmıyor"


# =================================================================================================
# 3) PALET — YİRMİ BÖLÜMÜN YİRMİSİ (kusur C)
# =================================================================================================
def _alan_bolumleri() -> dict[str, list[str]]:
    blok = re.search(r"const ALAN_BOLUMLERI = \{(.*?)\n\};", APPJS, re.S)
    assert blok, "ALAN_BOLUMLERI tanımlı değil"
    return {alan: re.findall(r'"(\w+)"', liste)
            for alan, liste in re.findall(r"^\s*(\w+):\s*\[([^\]]*)\]", blok.group(1), re.M)}


def _palet_bolumleri():
    return _node(
        "const P = require(%s);\n"
        "process.stdout.write(JSON.stringify([P.BOLUMLER, P.SAYFA_ADI]));" % json.dumps(str(PALET_YOL)))


def test_palet_bolum_tablosu_ALAN_BOLUMLERI_ile_BIREBIR():
    """Palet bir bilgi mimarisi haritasıdır. Eksik bir oda, haritanın kendisine olan güveni
    bitirir. SIRA da iddianın parçası: paletdeki sıra sayfadaki OKUMA sırasıdır."""
    bolumler, sayfa_adi = _palet_bolumleri()
    beklenen = [(b, alan) for alan, bl in _alan_bolumleri().items() for b in bl]
    olculen = [(r[0], r[1]) for r in bolumler]
    assert olculen == beklenen, (
        "palet bölüm tablosu ALAN_BOLUMLERI'nden ayrışmış:\n"
        f"  palet: {olculen}\n  app.js: {beklenen}")
    assert len(olculen) == 20, f"yirmi bölüm beklenirken {len(olculen)}"
    assert set(sayfa_adi) == set(_alan_bolumleri()), "sayfa adları eşlemesi ayrışmış"


def test_sekiz_yeni_bolumun_HEPSI_palette():
    """İş emrinin açık maddesi: S2R-2'de doğan sekiz bölümün hepsi `<sayfa>#<bölüm>` gezinme
    komutu almalı. Beşi vardı; mutabakat, golge ve bilesenic yoktu."""
    yeni = {"veriboru", "kapilar", "mutabakat", "intraemir",
            "karne", "golge", "bilesenic", "mudahale"}
    palet_ids = {r[0] for r in _palet_bolumleri()[0]}
    assert yeni <= palet_ids, f"palette olmayan yeni bölüm: {sorted(yeni - palet_ids)}"


def test_her_palet_capasi_GERCEK_bir_kap_ve_GERCEK_bir_capa():
    """Uydurulmuş çapa, ölü bağdan pahalıdır (v154 dersi): operatör gider, bulamaz, bir daha
    aramaz. İki taraf da doğrulanır — DOM kabı (index.html) ve başlık çapası (bolumBasHTML)."""
    capalar = set(re.findall(r'bolumBasHTML\("(\w+)"', APPJS))
    for bid, sayfa, ad, anahtarlar in _palet_bolumleri()[0]:
        assert f'id="page-{bid}"' in INDEX, f"{bid}: #page-{bid} kabı index.html'de yok"
        assert bid in capalar, f"{bid}: bolumBasHTML çapası üretilmiyor — `#{bid}` boşa gider"
        assert f'id="page-{sayfa}"' in INDEX, f"{sayfa}: alan sayfası kabı yok"
        assert ad.strip() and anahtarlar, f"{bid}: adı ya da anahtar kelimesi boş"


def test_TURKCE_KATLAMAYLA_yirmi_bolumun_HEPSI_bulunur():
    """`katla()` ö/ü/ş/ğ/ç/İ/ı'yı düzler. İddia BEYAN edilmez, gerçek `bulanikSkor` ile ÖLÇÜLÜR:
    her bölüm kendi id'siyle (aksansız, klavyeden yazılabilir) bulunabilmeli."""
    sonuc = _node(
        "const P = require(%s);\n"
        "const out = {};\n"
        "P.BOLUMLER.forEach(function (r) {\n"
        "  const komut = { ad: r[2], anahtarlar: r[3].concat(['bolum', r[0]]), altyazi: '' };\n"
        "  out[r[0]] = P.komutSkoru(komut, r[0]) !== null;\n"
        "});\n"
        "process.stdout.write(JSON.stringify(out));" % json.dumps(str(PALET_YOL)))
    bulunmayan = sorted(k for k, v in sonuc.items() if not v)
    assert not bulunmayan, f"palet aramasında bulunamayan bölüm: {bulunmayan}"
    # Ve aksanlı yazım da aynı satırı bulmalı — operatör "gölge" yazar, "golge" değil.
    for sorgu in ("gölge", "GÖLGE", "mutabakat", "Öğrenme"):
        assert _node("const P = require(%s);\nprocess.stdout.write(JSON.stringify(P.katla(%s)))"
                     % (json.dumps(str(PALET_YOL)), json.dumps(sorgu))) == \
            _node("const P = require(%s);\nprocess.stdout.write(JSON.stringify(P.katla(%s)))"
                  % (json.dumps(str(PALET_YOL)), json.dumps(sorgu.lower())))


def test_kisayol_paneli_BOLUM_CAPASINI_anlatiyor():
    """`?` haritası panonun tek keşif yüzeyi. Yirmi bölüme ⌘K ile gidilebildiği orada yazmıyorsa
    özellik fiilen yok: kimse denemez (Nielsen İ6 — hatırlamaya zorlama)."""
    panel = _govde('ov.innerHTML = `<div class="kbd-panel">', "\n  ov.addEventListener")
    assert "yirmi bölüm" in panel, "kısayol panelinde bölüm kapsamı yazılı değil"
    assert "portfoy#mutabakat" in panel, "bölüm çapası biçimi örneklenmemiş"


# =================================================================================================
# 4) CSP YÜZEY LİSTESİ TAM (virgül-bitişme vakasının dersi)
# =================================================================================================
def test_csp_yuzey_listesi_web_dizinini_EKSIKSIZ_kapsar():
    """2026-08-01'de bu listede bir VİRGÜL eksikti; Python iki dizgiyi bitiştirdi, iki yüzey
    HİÇ sınanmadı ve var olmayan bitişik ad `pytest.skip` ile SESSİZCE atlandı — koruma yeşil
    görünüyordu. Listenin AÇIK kalması doğru (sözleşme okunabilir olmalı), ama tam olduğu
    ölçülmeli: yeni bir .js/.html eklenip listeye yazılmazsa CSP'si hiç sınanmaz."""
    m = re.search(r"YUZEYLER = \[(.*?)\n\]", CSP_TEST, re.S)
    assert m, "test_web_csp_uyum.py içinde YUZEYLER listesi bulunamadı"
    listelenen = set(re.findall(r'"([\w.-]+)"', m.group(1)))
    gercek = {p.name for p in WEB.iterdir()
              if p.is_file() and p.suffix in (".js", ".html")}
    assert gercek <= listelenen, (
        f"CSP taramasının DIŞINDA kalan tarayıcı dosyası: {sorted(gercek - listelenen)} — "
        "test_web_csp_uyum.py'deki YUZEYLER listesine ekle")
    assert listelenen <= gercek, (
        f"listede olup dizinde olmayan ad: {sorted(listelenen - gercek)} — bitişmiş ya da "
        "silinmiş bir giriş `pytest.skip` ile SESSİZCE atlanır")
    assert {"app.js", "palette.js", "theme.js"} <= listelenen


def test_yeni_yuzeylerde_satir_ici_olay_yok():
    """S2R-3'ün dokunduğu iki yeni kart ve palet tablosu da `script-src 'self'` altında."""
    for bas in ("const sGolgeVaryant = (() => {", "const sOzDeg = (() => {"):
        parca = _govde(bas, "\n  // ---------- ")
        assert not re.search(r'\son[a-z]+\s*=\s*["\']', parca), f"{bas}: satır içi olay özniteliği"
    assert not re.search(r'\son[a-z]+\s*=\s*["\']', _govde("var BOLUMLER = [", "\n  var CEKIRDEK", PALET))


# =================================================================================================
# 5) BLOK RİTMİ — TEK ÖLÇÜ, JETON TABANLI (kusur D)
# =================================================================================================
# Bölüm bloğu olarak yazılan kap sınıfları. `.hero-grid` ve `.eylem-serit` BİLEREK yok: ikisi de
# bir kartın İÇ yerleşim sarmalayıcısı (ve `.eylem-serit`in satır içi `display:grid` bildirimi
# `[style*="grid"] > .card` seçicisinin fiilen dayanağı — kaldırılamaz).
BLOK_KAPLARI = ("card rise", "card", "g2 rise", "g2", "mrow rise", "mrow", "hero rise", "hero")


def test_blok_kaplarinda_SATIR_ICI_margin_YOK():
    """Ritim iki yerde tutulamaz: satır içi stil kuralı HER ZAMAN yener. Otuz bir kap ölçüldü;
    marj değerleri 10/14/16/18/20/22 arasında geziniyordu — okuyucu bu farkı 'burada bir
    hiyerarşi var' diye okuyordu, yoktu."""
    kacaklar = re.findall(
        r'class="(?:%s)" style="[^"]*margin-top' % "|".join(re.escape(k) for k in BLOK_KAPLARI),
        APPJS)
    assert not kacaklar, (
        f"{len(kacaklar)} blok kabı hâlâ satır içi margin-top taşıyor: {sorted(set(kacaklar))} — "
        "ritim CSS'te (S2R-3 · BLOK RİTMİ), satır içinde değil")


def test_UC_OLCU_ve_yalniz_UCU_jetondan_gelir():
    """Üç ölçü, üçü de jeton: blok arası --s4, başlık altı --s5, bölüm arası --s12+--s10."""
    # Dilim, başlık YORUMUNUN AÇILIŞINDAN başlar — ortasından başlasaydı `/* … */` eşleşmesi
    # bozulur ve yorum düzyazısı "bildirim" sanılırdı (ilk denemede tam bu oldu).
    i = CSS.rindex("/*", 0, CSS.index("S2R-3 · BLOK RİTMİ"))
    blok = CSS[i:CSS.index("/* ---- GENEL BAKIŞ", i)]
    # GEREKÇE KURAL SANILMAZ: bu blok kararını yorumda anlatıyor ve o düzyazıda ölçülmüş px
    # sayıları geçiyor ("20px ile 44px arası"). Lint yalnız BİLDİRİMLERE bakar.
    kurallar = re.sub(r"/\*.*?\*/", "", blok, flags=re.S)
    ham = re.findall(r"(?:margin|padding|gap|inset)[a-z-]*\s*:\s*[^;}]*?\b\d+px", kurallar)
    assert not ham, f"S2R-3 ritim bloğunda ham boşluk değeri: {ham}"
    assert not re.search(r"(#[0-9a-fA-F]{3,8}|rgba?\()", kurallar), "ritim bloğunda jeton dışı renk"
    assert "margin-top:var(--s4)" in blok.replace(" ", ""), "blok arası ölçüsü --s4 değil"
    assert ".bolum-bas + :is(" in blok, "başlık altı kuralı yok — ilk blok kendi marjını taşır"
    # ÖLÇÜ BLOĞUN KENDİSİNDE: ilk deneme kardeş seçici (`X + Y`) idi ve bir kartın ÖNÜNDE
    # her zaman başka bir blok olmadığı için (Piyasa'da `<p class="hint">`i izliyor) SESSİZCE
    # yarım koşuyordu — kart metne yapışıyordu ve hiçbir test kırmızı vermiyordu.
    assert re.search(r"^:is\([^)]*\)\{margin-top:var\(--s4\)\}", blok, re.M), \
        "blok ölçüsü kardeş seçiciye bağlı — önünde blok olmayan kart marjsız kalır"
    assert re.search(r":is\([^)]*grid[^)]*\)\s*>\s*\n?\s*:is\([^)]*\)\{margin-top:0\}", blok), \
        "ızgara ÇOCUĞU sıfırlaması yok — ızgaranın ilk kutusu tek başına 16px aşağı kayar"
    for ic_sarmalayici in (".hero-grid", ".eylem-serit"):
        govde = re.search(r"^:is\(([^)]*)\)\{margin-top:var\(--s4\)\}", blok, re.M).group(1)
        assert ic_sarmalayici[1:] not in govde, \
            f"{ic_sarmalayici} blok ailesinde — kartın İÇİNE boşluk enjekte eder"
    # Bölüm arası ölçüsü tek yerde ve DEĞİŞMEDİ (cila turu bölüm ritmini yeniden değerlemedi).
    assert ".alan-bolum + .alan-bolum{margin-top:var(--s12);padding-top:var(--s10)" in CSS
    # Başlık altı ölçüsü de tek yerde.
    assert ".bolum-bas{margin-bottom:var(--s5)}" in CSS


def test_AYNI_BILDIRIM_IKI_YERDE_YAZILMAZ():
    """KAYNAK SIRASINA BAĞLI SESSİZ KAYBEDEN. Bu tur `.mrow`un marjını önce S2R-3 bloğunda
    yeniden bildirdi; blok stylesheet'te YUKARIDA olduğu için aynı özgüllükteki eski bildirim
    (aşağıda, `--s8`) kazanıyordu — ölçü değişmemiş oluyordu ve hiçbir şey kırmızı vermiyordu.
    Kural: ritim ailesinin her sınıfı için marj bildirimi TEK bir kuralda yaşar."""
    kurallar = re.findall(r"([^{}]+)\{([^{}]*)\}", re.sub(r"/\*.*?\*/", "", CSS, flags=re.S))
    for sinif, olcu in (("mrow", "--s4"), ("gloss", "--s4"), ("detay-kat", "--s4")):
        sahipler = [(s.strip(), g) for s, g in kurallar
                    if re.fullmatch(rf"\.{re.escape(sinif)}", s.strip())
                    and re.search(r"\bmargin(-top)?\s*:", g)]
        assert len(sahipler) == 1, (
            f".{sinif}: marj {len(sahipler)} ayrı kuralda bildirilmiş — kazanan kaynak sırasına "
            f"bağlı ve gözle görülmez: {[s for s, _ in sahipler]}")
        assert olcu in sahipler[0][1], f".{sinif}: marj {olcu} değil → {sahipler[0][1]!r}"
    # Ve `.mrow`un KENDİ kuralında eski değerin kalıntısı yok.
    mrow = next(g for s, g in kurallar if s.strip() == ".mrow" and "display:grid" in g)
    assert "var(--s8)" not in mrow, ".mrow hâlâ --s8 marjı taşıyor — blok ritmi tek ölçüye inmemiş"


def test_IZGARA_SIFIRLAYICILARI_yenilmedi():
    """2026-07-28'de ölçülmüş bir arıza: yığın marjı ızgara kardeşlerine vuruyordu ve üç kutu
    259/275/275'te kayıktı. S2R-3'ün taban kuralı (0,1,0) özgüllükte tutuluyor ki HEM eski
    sıfırlayıcılar (0,3,0) HEM yeni ızgara-çocuğu sıfırlaması (0,2,0) onu yensin."""
    for sifirlayici in (".g2 > .card + .card", ".hero-grid > .card + .card",
                        ".eylem-serit > .card + .card", '[style*="grid"] > .card + .card'):
        assert sifirlayici in CSS, f"ızgara sıfırlayıcısı düşmüş: {sifirlayici}"
    ritim = re.search(r"^:is\(([^)]*)\)\{margin-top:var\(--s4\)\}", CSS, re.M)
    assert ritim, "S2R-3 taban ritim kuralı beklenen biçimde değil (tek, atasız :is())"
    assert ">" not in ritim.group(0) and "+" not in ritim.group(0), (
        "taban kurala birleştirici girmiş — özgüllüğü yükselir ve ızgara sıfırlayıcılarını "
        "yenmeye başlar (2026-07-28 arızası geri gelir)")
    aile = {s.strip() for s in ritim.group(1).split(",")}
    assert aile == {".card", ".g2", ".mrow", ".hero", ".gloss", ".detay-kat"}, \
        f"blok ailesi değişmiş: {sorted(aile)}"


def test_DETAY_KATMANINDA_cift_cerceve_YOK():
    """Altı detay katmanının beşi çerçevesiz gövde taşıyor; biri (`p.sIntra`) tam bir `.card`
    alıyor — katlanmış bir bölmenin İÇİNDE ikinci bir kutu, yani bu turun kaldırmaya çalıştığı
    'katman katman kutu' hissinin ta kendisi. Kart JS'te bölünmedi (tek tüketici, tek üretici);
    çerçeve CSS'te eritildi — içerik durur, kutu düşer."""
    kural = re.search(r"\.detay-kat \.dk-govde > \.card\{([^}]*)\}", CSS)
    assert kural, "detay katmanındaki kart çerçevesi eritilmemiş"
    for bildirim in ("background:none", "border:none", "padding:0"):
        assert bildirim in kural.group(1), f"çerçeve tam erimemiş: {bildirim} yok"
    # Ve o kart GERÇEKTEN oraya düşüyor (kural boşa yazılmadı).
    assert 'detayKatmani("Intraday · Faz 4a gözlem özeti"' in APPJS
    assert "p.sIntra" in APPJS


def test_OGRENME_ilk_bolum_siniri_var():
    """Yedi bölümlü sayfada ilk sınırın eksik olması, geri kalan altı sınırın ritmini de
    yalanlar: Karne, eylem şeridinin düğmelerine yapışık başlıyordu."""
    assert "#ogrenme-eylem + .alan-bolum{" in CSS, "Öğrenme'nin ilk bölüm sınırı yok"


# `class="card"` (rise'sız) BEŞ yerde kullanılır ve BEŞİ de bir IZGARA ÇOCUĞUDUR — yani kart
# içinde kart değil, yan yana kart. Gerekçe listede durur; listeye giren yeni bir satır gerekçe
# yazmayı GEREKTİRİR (YASA 4 deseni, test_tasarim_token_v153'ün IZIN_VERILEN'i ile aynı sözleşme).
IZGARA_KARTLARI = {
    "Piyasa havasına göre kırılım": "karne · `.g2` ikizinin sol kutusu",
    "Hangi araç ne kadar isabetli": "karne · `.g2` ikizinin sağ kutusu",
    "Durum": "hermes · `.g2` ikizinin sol kutusu",
    "Harcama (bu ay)": "hermes · `.g2` ikizinin sağ kutusu",
    "${baslik}": "eylemKutu() · `.eylem-serit` üçlüsünün tek kutusu (subgrid satırlarını paylaşır)",
}


def test_kart_icinde_kart_YOK():
    """'Katman katman kutu' hissi bu turun kaldırmaya çalıştığı şeyin ta kendisiydi. `.card`
    iç içe HİÇ kullanılmaz; `rise`sız hâli yalnız ızgara çocuklarında ve her biri gerekçeli."""
    siniflar = re.findall(r'class="(card[^"]*)"', APPJS)
    assert set(siniflar) <= {"card rise", "card", "card rise in"}, \
        f"tanınmayan kart sınıfı kombinasyonu: {sorted(set(siniflar))}"
    bulunan = set()
    for m in re.finditer(r'<div class="card">\s*\n?\s*<h2 class="t"[^>]*>([^<]*)', APPJS):
        bulunan.add(m.group(1).strip())
    assert bulunan == set(IZGARA_KARTLARI), (
        "ızgara kartları listesi kaynaktan ayrışmış — yeni bir `class=\"card\"` gerekçesiz "
        f"eklenmiş ya da biri düşmüş: {sorted(bulunan ^ set(IZGARA_KARTLARI))}")
    for baslik, gerekce in IZGARA_KARTLARI.items():
        assert len(gerekce) >= 20, f"{baslik}: gerekçe {len(gerekce)} karakter (≥20 gerekli)"
    # Ve ızgara kapları GERÇEKTEN kaynakta: kart-yan-yana iddiasının şartı.
    assert 'class="g2 rise"' in APPJS and "eylem-serit" in INDEX

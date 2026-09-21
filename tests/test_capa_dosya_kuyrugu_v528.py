"""test_capa_dosya_kuyrugu_v528.py — TSK-211: İKİ PARÇALI DOSYA KUYRUĞU SEMBOL DEĞİLDİR.

VAKA (ölçüldü 2026-09-21, iki ayrı tur): TSK-209 tur 1 ve tur 2'de iki ayrı implementer düzyazıya
`auth.json.tmp` ve `secrets.bak.json` yazdı. `codelaw.capa_uyusmasi`nın `modül.sembol` taraması
bu DOSYA ADLARINI çürük çapa saydı (tur 1'de 4 kırmızı). İmplementerler adları yol önekli biçime
çevirerek geçti — yani dedektör, yazarı METNİ EĞMEYE zorladı. Yanlış alarm yasanın en pahalı
arızasıdır: susturulan bekçi, olmayan bekçiden beterdir; ama yazarını kendi düzyazısını
çarpıtmaya zorlayan bekçi de aynı sınıftandır.

BU DOSYANIN BAŞLIĞI KENDİ KANITIDIR: yukarıdaki iki ad EĞİLMEDEN yazılmıştır ve üçüncü besleme
`tests/` altını da tarar. Düzeltme olmadan bu docstring CANLI ağaçta iki `curuyen` kaydı
üretirdi; `test_CANLI_AGACTA_BU_DOSYA_CURUK_CAPA_URETMEZ` tam olarak bunu ölçer.

ÖLÇÜLEN MEKANİZMA (`test_DESEN_KUYRUGU_...` birebir ölçer): `_MODUL_CAPA_DESENI` sembol parçasını
NOKTALI okur — `Sinif.metot` çapalarını tanımak için ZORUNLU, yani kök deseni daraltmakla
kapatılamaz. Bir dosya adının kuyruğu iki parçalıysa ilk parça "modül", KALANI "sembol" olur ve
eski muafiyet (KAPSAM SINIRI 3) yalnız TEK parçalı sembole bakıyordu:
    modül parçası depoda TEK `.py` olarak çözülür        → KAPSAM SINIRI 2 geçilir,
    iki parçalı kuyruk `_CAPA_UZANTILARI` kümesinde YOK  → KAPSAM SINIRI 3 geçilir,
    hedef modülün AST adları arasında da yok             → `curuyen` / `sembol_yok`.

DÜZELTME (dar): kuyruk parçalarından HERHANGİ biri `_CAPA_UZANTILARI`ndaysa eşleşme bir DOSYA
ADIDIR, çapa değildir. Tek parçalı hâl bu kuralın ÖZEL DURUMUDUR — eski davranış aynen korunur.

BEDEL (burada ayrıca ölçülür): gerçek çürük çapa HÂLÂ ısırmalı. Muafiyet "noktalı kuyruk = dosya
adı" diye GENİŞ yazılsaydı sınıf-nitelikli çürük bir çapa sessizce affedilirdi — o mutasyonu
`test_GERCEK_CURUK_CAPA_SINIF_NITELIKLI_KUYRUKTA_DA_ISIRIR` ısırır.

YOL ÖNEKLİ BİÇİM (`state/auth.json`) HER ZAMAN temizdi ve öyle kalır: desen backtick'in HEMEN
ardından modül adı ister, yol ayracı taşıyan bir ad eşleşmeye HİÇ giremez. İmplementerların
bulduğu "kaçış yolu" buydu ve regresyon çivisi onu ölçer.
"""
from __future__ import annotations

import pathlib

from meridian import codelaw

_HEDEF_AUTH = "def oturum_ac():\n    return 1\n"
_HEDEF_SECRETS = "def sir_oku():\n    return 2\n"
_HEDEF_STORE = (
    "def var_olan():\n"
    "    return 3\n"
    "\n"
    "class Depo:\n"
    "    def var_olan_metot(self):\n"
    "        return 4\n"
)


def _sentetik_kok(tmp_path, dosyalar: dict[str, str]) -> str:
    for ad, govde in dosyalar.items():
        (tmp_path / ad).write_text(govde, encoding="utf-8")
    return str(tmp_path)


def _tara(kok: str, metin: str) -> dict:
    """Sentetik kökte TEK metni `modül.sembol` biçimiyle tarar (üçüncü beslemenin çekirdeği)."""
    return codelaw.capa_uyusmasi([("kaynak", metin)], py_kokler=(kok,), modul_bicimi=True)


# ---------------------------------------------------------------------------
# (a) MEKANİZMA — desenin kuyruğu NASIL böldüğü (ölçüm; düzeltmeden bağımsız, desen DEĞİŞMEZ)
# ---------------------------------------------------------------------------

def test_DESEN_KUYRUGU_ILK_PARCAYI_MODUL_KALANI_SEMBOL_OKUR():
    m = codelaw._MODUL_CAPA_DESENI.search("yedek `auth.json.tmp` yazıldı")
    assert m is not None, "desen iki parçalı kuyruğu HİÇ eşleştirmiyor — vaka yanlış okunmuş"
    assert (m.group(1), m.group(2)) == ("auth", "json.tmp"), m.groups()
    m2 = codelaw._MODUL_CAPA_DESENI.search("kopya `secrets.bak.json` üretildi")
    assert m2 is not None, "ikinci vaka biçimi eşleşmiyor"
    assert (m2.group(1), m2.group(2)) == ("secrets", "bak.json"), m2.groups()


# ---------------------------------------------------------------------------
# (b) YENİDEN ÜRETİM ÇİVİLERİ — düzeltmeden ÖNCE KIRMIZI
# ---------------------------------------------------------------------------

def test_GECICI_DOSYA_KUYRUGU_CURUYENE_DUSMEZ(tmp_path):
    """Sentetik kökte modül parçası TEK `.py` olarak çözülür (KAPSAM SINIRI 2 geçilir) ve iki
    parçalı kuyruk eski muafiyete takılmaz → düzeltmeden önce `curuyen`/`sembol_yok`. Kuyruğun
    SON parçası uzantıdır."""
    kok = _sentetik_kok(tmp_path, {"auth.py": _HEDEF_AUTH})
    r = _tara(kok, "yedek alındı: `auth.json.tmp` diske yazıldı")
    assert r["curuyen"] == [], (
        f"geçici dosya adı ÇÜRÜK ÇAPA sayıldı — yazar metni eğmeye zorlanıyor: {r['curuyen']}")
    assert r["cozulen"] == [], r["cozulen"]


def test_YEDEK_DOSYA_KUYRUGU_CURUYENE_DUSMEZ(tmp_path):
    """İkinci vaka biçimi: kuyruğun SON parçası uzantı, ORTA parçası değil. Muafiyet yalnız son
    parçaya ya da yalnız ilk parçaya bakarsa iki vakadan biri kaçar — kural HERHANGİ bir parçaya
    bakar."""
    kok = _sentetik_kok(tmp_path, {"secrets.py": _HEDEF_SECRETS})
    r = _tara(kok, "kopya: `secrets.bak.json` üretildi")
    assert r["curuyen"] == [], f"yedek dosya adı ÇÜRÜK ÇAPA sayıldı: {r['curuyen']}"
    assert r["cozulen"] == [], r["cozulen"]


# ---------------------------------------------------------------------------
# (c) BEDEL — gerçek çürük çapa HÂLÂ ısırır (muafiyet GENİŞ yazılırsa bu bölüm öter)
# ---------------------------------------------------------------------------

def test_GERCEK_CURUK_CAPA_HALA_ISIRIR(tmp_path):
    """Pozitif kontrol: uzantı taşımayan tek parçalı sembol çürükse hüküm DEĞİŞMEDEN kurulur."""
    kok = _sentetik_kok(tmp_path, {"store.py": _HEDEF_STORE})
    r = _tara(kok, "bkz. `store.yok_fonksiyon` çağrısı")
    assert [(c["capa"], c["neden"]) for c in r["curuyen"]] == [
        ("store.yok_fonksiyon", "sembol_yok")], r


def test_GERCEK_CURUK_CAPA_SINIF_NITELIKLI_KUYRUKTA_DA_ISIRIR(tmp_path):
    """MUTASYON KAPISI: muafiyet "noktalı kuyruk = dosya adı" diye geniş yazılırsa bu çivi öter.
    Kuyruk iki parçalıdır ama HİÇBİR parçası uzantı değildir — çapadır ve çürüktür."""
    kok = _sentetik_kok(tmp_path, {"store.py": _HEDEF_STORE})
    r = _tara(kok, "bkz. `store.Depo.olmayan_metot` çağrısı")
    assert [(c["capa"], c["neden"]) for c in r["curuyen"]] == [
        ("store.Depo.olmayan_metot", "sembol_yok")], r


def test_SAGLAM_SINIF_NITELIKLI_CAPA_COZULMEYE_DEVAM_EDER(tmp_path):
    """Kazanç tarafının regresyonu: var olan sınıf-nitelikli çapa hâlâ `cozulen`e düşer —
    muafiyet onu da susturmuş olsaydı yasa o yüzeyde KÖR olurdu (sessizce)."""
    kok = _sentetik_kok(tmp_path, {"store.py": _HEDEF_STORE})
    r = _tara(kok, "bkz. `store.Depo.var_olan_metot` çağrısı")
    assert [c["sembol"] for c in r["cozulen"]] == ["Depo.var_olan_metot"], r
    assert r["curuyen"] == [], r


# ---------------------------------------------------------------------------
# (d) REGRESYON — önce de sonra da temiz olan iki yol
# ---------------------------------------------------------------------------

def test_YOL_ONEKLI_AD_ESLESMEYE_HIC_GIRMEZ(tmp_path):
    """İmplementerların bulduğu KAÇIŞ: yol öneki. Desen backtick'in HEMEN ardından modül adı
    ister; yol ayracı taşıyan ad eşleşmeye hiç giremez — üç kovanın da BOŞ kalması bunu ölçer
    (düzeltmeden önce de sonra da yeşil)."""
    kok = _sentetik_kok(tmp_path, {"auth.py": _HEDEF_AUTH})
    r = _tara(kok, "yedek: `state/auth.json.tmp` ve `state/auth.json`")
    assert r == {"cozulen": [], "curuyen": [], "cozulemeyen": []}, r


def test_TEK_PARCALI_UZANTI_MUAFIYETI_REGRESYONU(tmp_path):
    """Eski muafiyet (2026-09-02, 11 yanlış çürüme) AYNEN korunur: tek parçalı uzantı kuyruğu
    yeni kuralın ÖZEL DURUMUDUR, ayrı bir dal değil."""
    kok = _sentetik_kok(tmp_path, {"secrets.py": _HEDEF_SECRETS})
    r = _tara(kok, "dosya `secrets.json` okunur")
    assert r == {"cozulen": [], "curuyen": [], "cozulemeyen": []}, r


# ---------------------------------------------------------------------------
# (e) CANLI AĞAÇ — bu dosyanın KENDİ düzyazısı çürük sayılmaz
# ---------------------------------------------------------------------------

def test_CANLI_AGACTA_BU_DOSYA_CURUK_CAPA_URETMEZ():
    """Başlık docstring'i vakayı adları EĞMEDEN anlatır; üçüncü besleme `tests/` altını da tarar.
    Düzeltme olmadan bu dosya iki `curuyen` kaydı üretir — çivi, yasanın yazarını çarpıtmaya
    zorlamadığını CANLI ağaçta ölçer."""
    y = codelaw.report()["yorum_sembol_capalari"]
    assert y is not None, "yorum_sembol_capalari ÖLÇÜLMEDİ (None) — canlı kökte hesaplanmalıydı"
    bu_dosya = pathlib.Path(__file__).name
    bizim = [c for c in y["curuyen"] if pathlib.Path(c["kaynak"]).name == bu_dosya]
    assert bizim == [], f"bu dosyanın düzyazısı çürük çapa sayıldı: {bizim}"

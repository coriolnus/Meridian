"""v573 — SATIR ÇAPASI YASASI, DEVAM BİÇİMİ (TSK-241, 2026-09-27).

Varlık yasağı ailesinin BEŞİNCİ üyesi. Önceki dördü çapayı DOSYA ADINA BİTİŞİK biçimde tanır (ad + uzantı + iki
nokta + sayı): `tests/test_kovab_dilim_v382.py::test_meridian_kaynaginda_MUAFIYETSIZ_satir_capasi_YOK` (kök
`meridian/*.py`), `tests/test_tests_ops_satir_capasi_v401.py::test_tests_ops_kaynaginda_MUAFIYETSIZ_satir_capasi_YOK`
(`tests/`+`ops/`), `tests/test_birim_capa_taramasi_v563.py::test_deploy_birim_dosyalarinda_MUAFIYETSIZ_satir_capasi_YOK`
(birim dosyaları) ve `tests/test_capa_pydisi_hedef_v571.py::test_YASAK_yuzeyde_meridian_SATIR_capasi_YOK` (`.py` dışı
hedefler + `.py` olmayan kaynaklar). Aynı dosyayı SÜREN DEVAM biçimi — dosya adı önce (ya da önceki satırda, ya da
"bu dosyanın" deyişiyle) anılır, satır numarası ondan AYRI durur — yalnız v563'ün birim şerhlerinde aranıyordu;
motorun kendi yorumlarında HİÇBİR çivinin görüş alanında değildi (TSK-239 kaygı K6). İki alt biçim:
  (a) AYRIK: boşluk/parantez/virgül/noktalı virgül/orta nokta/backtick/eğik çizgi ardından yalın iki nokta + sayı
      (+ tire + sayı aralığı);
  (b) KUYRUK: bitişik bir çapanın HEMEN ardından eğik çizgi ya da virgül + yalın sayı (bitişik kısım v571'indir,
      kuyruk buradadır — iki desen aynı metni iki kez saymaz, ayrıklık çivili).

TUR BAŞI ÖLÇÜM (2026-09-27, taban 839f3e2e; bu dosyanın deseni, v571'in gezgini ve yüzey sınıflayıcısıyla — pytest
içi yoklama, depo dışı):
  * 1.201 taranan dosya (262'si `ui/src`), işaretsiz 39 devam çapası — motor (`meridian/*.py`) 15: loop 8 · watchdog
    5 · api 2, hepsi şerh ya da docstring; pano (`meridian/web`) 2: index.html · landing.html; `tests/` 15: 12 şerh/
    docstring (v271'in üç halkalı dizisi dahil) + 3 v563 fikstür eşleşmesi (iki satırda); `deploy/` 2: ikisi de PORT
    (yanlış pozitif); kuyruk biçimi 5: litestream `db.go` (4 eğik çizgi, 1 virgül — harici). Codelaw işaretini ZATEN
    taşıyan satırlarda 27 eşleşme daha (muaf, sayılır).
  * Motordaki 15'in 13'ü CANLI GÖSTERİCİ, 2'si bayat bir çapayı DERS olarak alıntılar. 13 göstericinin 13'ü de
    bugün YANLIŞ satırı gösteriyordu (hedef satır 2026-09-27'de okundu); yazıldıkları commit'te bir kısmı doğruydu
    (`eq_now`, `MIRROR_DRIFT_TOL`, sermaye uyarısı — commit'teki hedef satır okundu): doğruluk sözleşme değil
    şanstı. Panonun 2'si canlı gösterici, ikisi de yanlış satırda. `tests/`teki 12 şerh çapasının 4'ü canlı
    gösterici (iki yerde, ikisi de yanlış satır), 8'i tarihçe/ders alıntısı.
  * Hepsi bu turda çevrildi: canlı göstericiler SEMBOL (`dosya.py::ad` ya da backtick içinde modül + nokta + ad) ya
    da BAŞLIK/ALINTI çapasına (aşağıdaki E bölümü); ders alıntıları codelaw'ın mezar taşı işaretiyle beyanlı (v382
    sınıf (b) emsali — çevrilirse ders ölür); v563'ün iki işaretsiz fikstür satırı sentetik işaret aldı.
    `IZINLI_DEVAM` kaydı bugün BOŞ: izinli yüzeyde DOĞRU kalan devam çapası yoktu.

YANLIŞ POZİTİF ÖLÇÜMÜ (bedel yasası — ölçüldü 2026-09-27, aynı yüzeyler):
  * v563'ün deseni köşeli parantezi de öncül sayar; köşeli parantez ardından iki nokta + sayı Python/Jinja DİLİMİdir
    (`s[:10]` biçimi) ve taranan yüzeylerde 1.016 eşleşme verir (meridian 523 · tests 396 · ops 93 · deploy 4) —
    1.016'sının 1.016'sı kapalı dilim. Bu dosya köşeli parantezi öncülden ÇIKARIR (ölçülen kayıp 0 gerçek çapa) —
    çıkarım ayrışma çivisiyle sınırlanmıştır: v563'ün gördüğü, köşeli parantezle başlamayan HER eşleşmeyi bu desen
    de görür.
  * Saat (`13:30`), adres:port (`127.0.0.1:8080`), oran (`22:1`), IPv6 (`[::1]:8080`), sürüm dizgesi: öncül karakter
    ad/sayı olduğu için desen onları hiç görmez (0 eşleşme). Boşlukla ayrılmış PORT görür: 2 örnek (deploy) —
    `YANLIS_POZITIF` beyanında gerekçeli, SAYILIR.
  * `.py` kaynağı yorum+docstring ile SINIRLANMAZ, ham satır taranır (v382/v401 emsali: kod dizgesindeki çapa da
    çapadır — codelaw beyan metinleri birer kod dizgesidir). Köşeli parantez çıkarımından sonra kod satırında kalan
    işaretsiz eşleşme: 3, hepsi v563 fikstürü (sentetik işaret aldı).

SÖZLEŞME (v571 ile aynı iki yüzey sınıfı, v571'in sınıflayıcısından türetilir):
  * YASAK yüzey (`meridian/**`): işaretsiz her devam çapası KIRMIZI — doğru olsa bile.
  * İZİNLİ yüzey: devam çapası hedefini ADIYLA taşımadığı için hedef `IZINLI_DEVAM` kaydında AÇIKÇA yazılır ve
    hedefin o satır(lar)ı beyan edilen metni taşımak ZORUNDADIR. Beyansız → kırmızı; metni tutmayan → kırmızı;
    kaynakta bulunmayan kayıt (bayat) → kırmızı. Aynı satırda önceki bitişik çapası HARİCİ uzantılı (v571
    `_HARICI_UZANTILAR`) olan devam çapası harici sayılır: hüküm almaz, SAYILIR.
  * `YANLIS_POZITIF` (her yüzeyde): çapa OLMAYAN eşleşme (port) — gerekçeli, sayılır, bayatı kırmızı.
  * Muafiyet: codelaw'ın iki işareti (mezar taşı · sentetik), v571 üzerinden (tek kaynak).

NEDEN AYRI ÇİVİ (v571'e ek değil): (1) çapa metni hedefi TAŞIMAZ — v571'in kayıt anahtarı dosya adını çapanın
kendisinden çözer, burada hedef kayıtta açıkça yazılmak zorunda (farklı kayıt şeması); (2) desen ailesi farklı ve
v571'in eşleşmeleriyle AYRIK (çivili) — v571'e katmak onun sayımlarını ve ayrışma çivilerini birlikte değiştirirdi;
(3) motor değişmez (v563/v571 emsali: test tarafı çivi, `codelaw.report()["ok"]`e yeni hüküm eklenmez).

BÖLÜŞÜM: birim dosyaları v563'ündür (devam biçimini şerhte zaten arar); `docs/*.md` bitişik `.py` çapaları codelaw
docs dünyasınındır ama DEVAM biçimi orada da görünmez — bu dosya yaşayan `docs/`u tarar. Pano derleme paketi
(`meridian/web/pano-assets/`) üretilmiştir (v572 sınıfı); `ui/src` BURADA taranır (codelaw tsx dünyası devam
biçimini görmez; ölçülen 0). Düzyazı "satır + sayı" biçimi (codelaw `_TEXT_SATIR_DESENI`) ve "ve + sayı" bağlacı
KAPSAM DIŞI: dil-bağımlı, çoğu veri satırı anlamında (TSK-239 K6b ölçümü) — ayrı kalem.
"""
from __future__ import annotations

import pathlib
import re
from collections import Counter

import pytest

from meridian import codelaw
from tests.test_birim_capa_taramasi_v563 import _DEVAM_CAPA_DESENI as _V563_DEVAM_DESENI
from tests.test_capa_pydisi_hedef_v571 import (
    BEYANLI_ATLANAN as _V571_ATLANAN,
    REPO,
    _DESEN_HEPSI,
    _HARICI_UZANTILAR,
    _atlanan_sinif as _v571_atlanan_sinif,
    _depo_metinleri_onbellekli,
    _muafiyetler,
    _yuzey,
)
from tests.test_sembol_capa_pydisi_v572 import BEYANLI_ATLANAN as _V572_ATLANAN, _PANO_DERLEME_ONEKI

# =================================================================================================
# DESEN — v563'ün devam deseninden türetilmiş öncül kümesi (köşeli parantez ÇIKAR, eğik çizgi EKLENİR)
# =================================================================================================

#: (a) AYRIK devam: öncül karakter boşluk · parantez · virgül · noktalı virgül · orta nokta · backtick · eğik çizgi.
#: v563 kümesinden farkı İKİ karakter ve ikisi de ölçümle: köşeli parantez ÇIKTI (dilim sözdizimi — modül belgesi),
#: eğik çizgi EKLENDİ (bir devam çapası dizisinde ikinci ve sonraki halka: ilk halkadan sonra eğik çizgi gelir).
_AYRIK_DESENI = re.compile(r"(?<=[\s(,;·`/]):(\d+)(?:-(\d+))?")

#: (b) KUYRUK halkası: bitişik çapanın ya da önceki halkanın HEMEN ardından eğik çizgi/virgül + yalın sayı. Boşluklu
#: virgül KAPSAM DIŞI — düzyazıda sayım anlamına gelir ("… , 3 kez"); ölçülen boşluklu kuyruk taranan yüzeylerde 0.
_KUYRUK_HALKASI = re.compile(r"[/,](\d+)(?:-(\d+))?(?!\w)")

#: ÖN SÜZGEÇ (yalnız hız): her devam çapası iki nokta + rakam taşır (kuyruk da bitişik bir çapanın ardındadır).
_ON_SUZGEC = re.compile(r":\d")


def _uzanti(bitisik: re.Match) -> str:
    return bitisik.group(2).rsplit(".", 1)[1]


def devam_capalari(satir: str) -> list[tuple[str, str | None]]:
    """Satırdaki devam çapaları soldan sağa: (çapa metni, aynı satırda ÖNCEKİ bitişik çapanın uzantısı | None)."""
    bitisik = list(_DESEN_HEPSI.finditer(satir))
    bulunan: list[tuple[int, str, str | None]] = []
    for m in _AYRIK_DESENI.finditer(satir):
        onceki = [b for b in bitisik if b.end() <= m.start()]
        bulunan.append((m.start(), m.group(0), _uzanti(onceki[-1]) if onceki else None))
    for b in bitisik:
        konum = b.end()
        while (k := _KUYRUK_HALKASI.match(satir, konum)) is not None:
            bulunan.append((k.start(), k.group(0), _uzanti(b)))
            konum = k.end()
    return [(c, u) for _k, c, u in sorted(bulunan)]


# =================================================================================================
# YÜZEY SINIFLARI — v571'in sınıflayıcısı; `ui/src` burada taranır, pano derleme paketi atlanır (v572 sınıfı)
# =================================================================================================

BEYANLI_ATLANAN: dict[str, str] = {
    **{s: g for s, g in _V571_ATLANAN.items() if s != "ui_kaynagi"},
    "uretilmis_pano": _V572_ATLANAN["uretilmis_pano"],
}


def _atlanan_sinif(rel: str) -> str | None:
    """v571 sınıfı; farkı İKİ: `ui/src` TARANIR (codelaw tsx dünyası devam biçimini görmez; ölçülen 0, taramanın
    bugünkü bedeli yok) ve pano derleme paketi `uretilmis_pano` olarak atlanır (kaynağı `ui/src`)."""
    if rel.startswith(_PANO_DERLEME_ONEKI):
        return "uretilmis_pano"
    sinif = _v571_atlanan_sinif(rel)
    return None if sinif == "ui_kaynagi" else sinif


# =================================================================================================
# BEYANLAR — izinli yüzeyde kalan devam çapaları (bugün BOŞ) · çapa olmayan eşleşmeler
# =================================================================================================

#: (kaynak yol, çapa metni) → (hedef yol | None, hedefte ZORUNLU metin | hedef None iken gerekçe). Devam çapası
#: hedefini adıyla taşımaz; hedef burada açıkça yazılır ve her koşumda o satır(lar)da metin aranır. BUGÜN BOŞ
#: (2026-09-27): izinli yüzeydeki 11 devam çapasının canlı gösterici olan 2'si yanlış satırı gösteriyordu ve sembole
#: çevrildi, kalanı ders/tarihçe alıntısıdır (mezar taşı). Kayıt biçimi sentetik çivilerle sınanır.
IZINLI_DEVAM: dict[tuple[str, str], tuple[str | None, str]] = {}

#: (kaynak yol, çapa metni) → gerekçe. Çapa OLMAYAN eşleşme: desen boşlukla ayrılmış PORTU ayırt edemez.
YANLIS_POZITIF: dict[tuple[str, str], str] = {
    ("deploy/apisix/config.yaml", ":9443"): (
        "APISIX dış dinleme PORTU — şerh cümlesi (dış URL hangi portu taşır) iki nokta + port yazımını kullanır; "
        "satır çapası değil, hedef dosyası yok (ölçüldü 2026-09-27)"),
    ("deploy/verify_hermes_training.sh", ":8080"): (
        "pano sağlık ucunun dinleme PORTU — operatöre basılan hata iletisinin metni (iki nokta + port); satır "
        "çapası değil, betiğin çalışan satırıdır ve metni değiştirmek çıktıyı değiştirirdi (ölçüldü 2026-09-27)"),
}


def _kayit_hukmu(capa: str, hedef_yol: str, hedef_metin: str, kok: pathlib.Path) -> str | None:
    """Beyanlı devam çapasının doğrulaması: None = tutuyor, aksi hâlde çürüme nedeni."""
    m = re.fullmatch(r"[:/,](\d+)(?:-(\d+))?", capa)
    if m is None:
        return "ayristirilamaz"
    yol = kok / hedef_yol
    if not yol.is_file():
        return "hedef_yok"
    satirlar = yol.read_text(encoding="utf-8").splitlines()
    n1 = int(m.group(1))
    ust = int(m.group(2)) if m.group(2) else n1
    if n1 < 1 or ust > len(satirlar) or n1 > ust:
        return "menzil_disi"
    if hedef_metin not in "\n".join(satirlar[n1 - 1:ust]):
        return "metin_tutmuyor"
    return None


def devam_hukmu(metinler, kayit=None, yanlis_pozitif=None, kok: pathlib.Path = REPO) -> dict:
    """ÇEKİRDEK: `(rel yol, metin)` çiftleri → hüküm. Saf fonksiyon (sentetik girdiyle sınanır).

    Dönüş: `ihlal` (tür: yasak · beyansiz · curuk) · `dogrulanan` · `ornek` · `harici` · `yanlis_pozitif` · `muaf`
    sayıları · `atlanan`/`atlanan_dosya` {sınıf: sayı} · `taranan` (rel listesi) · `kullanilan_kayit` /
    `kullanilan_yp` (bayat beyan ölçümü)."""
    kayit = IZINLI_DEVAM if kayit is None else kayit
    yanlis_pozitif = YANLIS_POZITIF if yanlis_pozitif is None else yanlis_pozitif
    muaflar = _muafiyetler()
    out = {"ihlal": [], "dogrulanan": 0, "ornek": 0, "harici": 0, "yanlis_pozitif": 0, "muaf": 0,
           "atlanan": Counter(), "atlanan_dosya": Counter(), "taranan": [], "kullanilan_kayit": set(),
           "kullanilan_yp": set()}
    for rel, metin in metinler:
        sinif = _atlanan_sinif(rel)
        if sinif is not None:
            out["atlanan_dosya"][sinif] += 1
            out["atlanan"][sinif] += sum(len(devam_capalari(s)) for s in metin.splitlines() if _ON_SUZGEC.search(s))
            continue
        out["taranan"].append(rel)
        yuzey = _yuzey(rel)
        for i, satir in enumerate(metin.splitlines(), 1):
            if not _ON_SUZGEC.search(satir):
                continue
            bulunan = devam_capalari(satir)
            if not bulunan:
                continue
            if any(m in satir for m in muaflar):
                out["muaf"] += len(bulunan)
                continue
            for capa, onceki_uzanti in bulunan:
                yer = {"kaynak": rel, "satir": i, "capa": capa}
                anahtar = (rel, capa)
                if anahtar in yanlis_pozitif:
                    out["yanlis_pozitif"] += 1
                    out["kullanilan_yp"].add(anahtar)
                    continue
                if yuzey == "yasak":
                    out["ihlal"].append({**yer, "tur": "yasak"})
                    continue
                if onceki_uzanti in _HARICI_UZANTILAR:
                    out["harici"] += 1
                    continue
                if anahtar in kayit:
                    out["kullanilan_kayit"].add(anahtar)
                    hedef_yol, metin_ya_da_gerekce = kayit[anahtar]
                    if hedef_yol is None:
                        out["ornek"] += 1
                        continue
                    neden = _kayit_hukmu(capa, hedef_yol, metin_ya_da_gerekce, kok)
                    if neden is None:
                        out["dogrulanan"] += 1
                    else:
                        out["ihlal"].append({**yer, "tur": "curuk", "neden": neden})
                    continue
                out["ihlal"].append({**yer, "tur": "beyansiz"})
    return out


_ONBELLEK: dict = {}


def _depo_hukmu() -> dict:
    if "h" not in _ONBELLEK:
        metinler, _ = _depo_metinleri_onbellekli()
        _ONBELLEK["h"] = devam_hukmu(metinler)
    return _ONBELLEK["h"]


# =================================================================================================
# A) TEK KAYNAK + AYRIŞMA — işaretler codelaw'dan, öncül kümesi v563'ten; v571 ile ayrıklık
# =================================================================================================

def test_muafiyet_isaretleri_CODELAW_TEK_KAYNAGINDAN_gelir():
    assert _muafiyetler() == (codelaw._CAPA_MUAFIYETI, codelaw._CAPA_SENTETIK_ISARETI)


@pytest.mark.parametrize("oncul", [" ", "\t", "(", ",", ";", "·", "`", "[", "/"])
def test_oncul_kumesi_V563_kumesinden_TURETILIR_koseli_parantez_CIKAR_egik_cizgi_EKLENIR(oncul):
    """Ayrışma çivisi (öncül karakter başına): v563 hangi öncülü görüyorsa bu desen de görür — köşeli parantez
    HARİÇ (dilim); eğik çizgiyi v563 görmez, bu desen görür. Kopya sessizce daralırsa burası kırmızı."""
    ornek = f"x{oncul}:12"
    v563 = bool(_V563_DEVAM_DESENI.search(ornek))
    bizim = bool(_AYRIK_DESENI.search(ornek))
    beklenen = (v563 and oncul != "[") or oncul == "/"
    assert bizim == beklenen, (oncul, v563, bizim)


def test_V563_eslesmeleri_canli_korpusta_KAPSANIR_koseli_parantez_HARIC():
    """Ayrışma çivisi (canlı korpus): taranan her satırda v563 devam deseninin köşeli parantezle başlamayan HER
    eşleşmesi bu dosyanın ayrık deseninde de vardır."""
    metinler, _ = _depo_metinleri_onbellekli()
    kacan = []
    for rel, metin in metinler:
        if _atlanan_sinif(rel) is not None:
            continue
        for i, satir in enumerate(metin.splitlines(), 1):
            if not _ON_SUZGEC.search(satir):
                continue
            bizim = {m.start() for m in _AYRIK_DESENI.finditer(satir)}
            kacan.extend(f"{rel} satır {i}: {m.group(0)}" for m in _V563_DEVAM_DESENI.finditer(satir)
                         if satir[m.start() - 1] != "[" and m.start() not in bizim)
    assert not kacan, kacan[:20]


def test_devam_eslesmeleri_V571_bitisik_eslesmeleriyle_AYRIK():
    """Aynı metin iki çivide iki kez sayılmaz: hiçbir devam çapası v571'in bitişik eşleşmesinin İÇİNDE kalmaz."""
    metinler, _ = _depo_metinleri_onbellekli()
    ortusen = []
    for rel, metin in metinler:
        for i, satir in enumerate(metin.splitlines(), 1):
            if not _ON_SUZGEC.search(satir):
                continue
            araliklar = [(b.start(), b.end()) for b in _DESEN_HEPSI.finditer(satir)]
            for m in _AYRIK_DESENI.finditer(satir):
                ortusen.extend(f"{rel} satır {i}: {m.group(0)}" for a, b in araliklar if a <= m.start() < b)
    assert not ortusen, ortusen[:20]


# =================================================================================================
# B) SENTETİK — yasak kırmızı · izinli beyansız kırmızı / beyanlı doğru yeşil / kayan kırmızı · harici · yanlış pozitif
# =================================================================================================

@pytest.fixture
def sahte_kok(tmp_path):
    (tmp_path / "ops").mkdir()
    (tmp_path / "ops" / "hedef.sh").write_text("#!/bin/bash\n# başlık\nset -e\nrm -f /tmp/kilit\n", encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("kaynak,satir,beklenen", [
    ("meridian/uydurma.py", "# döngünün P3 sonu (:1640) ve pano düğmesi", [":1640"]),  # çapa-sentetik: motor fikstürü (TSK-241)
    ("meridian/uydurma.py", "# `SABIT`, bu dosyanın :25'i — iç sim dolumu", [":25"]),  # çapa-sentetik: motor fikstürü (TSK-241)
    ("meridian/uydurma.py", "#       :339 bu hatayı adıyla uyarıyordu", [":339"]),  # çapa-sentetik: satır başı fikstürü (TSK-241)
    ("meridian/uydurma.py", "(300 sn poll, uydurma.py :320/:326/:334)", [":320", ":326", ":334"]),  # çapa-sentetik: eğik çizgi dizisi (TSK-241)
    ("meridian/uydurma.py", "# üç tüketici (bu dosya :1086, `a.b`)", [":1086"]),  # çapa-sentetik: virgül sonrası (TSK-241)
    ("meridian/uydurma.py", "# `shadowlaw` kendi yorumunda (`:102` bloğu)", [":102"]),  # çapa-sentetik: backtick fikstürü (TSK-241)
    ("meridian/web/uydurma.html", "   sınıfları :377-383'te — AYNI özgüllükte", [":377-383"]),  # çapa-sentetik: aralık fikstürü (TSK-241)
    ("meridian/web/uydurma.js", "// bkz. uydurma.sh:12/14 ve uydurma.sh:34,36", ["/14", ",36"]),  # çapa-sentetik: kuyruk fikstürü (TSK-241)
])
def test_SENTETIK_YASAK_yuzeyde_devam_capasi_KIRMIZI(sahte_kok, kaynak, satir, beklenen):
    """Pozitif kontrol (motor yüzeyi): TSK-239 ölçümünün BİREBİR biçimleri. Çapa listesi parametreden gelir; dedektör
    kapatılırsa ihlal listesi boş kalır ve çivi KIRMIZI olur (mutasyon M1)."""
    h = devam_hukmu([(kaynak, satir + "\n")], kayit={}, yanlis_pozitif={}, kok=sahte_kok)
    assert [(i["tur"], i["capa"]) for i in h["ihlal"]] == [("yasak", c) for c in beklenen], h["ihlal"]


def test_SENTETIK_IZINLI_yuzeyde_BEYANSIZ_KIRMIZI_BEYANLI_DOGRU_YESIL(sahte_kok):
    satir = "# kilit ops/hedef.sh:3 değil, :4 satırında siliniyor\n"  # çapa-sentetik: izinli fikstür (TSK-241)
    beyansiz = devam_hukmu([("ops/kaynak.py", satir)], kayit={}, yanlis_pozitif={}, kok=sahte_kok)
    assert [(i["tur"], i["capa"]) for i in beyansiz["ihlal"]] == [("beyansiz", ":4")], beyansiz["ihlal"]
    kayit = {("ops/kaynak.py", ":4"): ("ops/hedef.sh", "rm -f /tmp/kilit")}
    beyanli = devam_hukmu([("ops/kaynak.py", satir)], kayit=kayit, yanlis_pozitif={}, kok=sahte_kok)
    assert beyanli["ihlal"] == [] and beyanli["dogrulanan"] == 1, beyanli
    assert beyanli["kullanilan_kayit"] == set(kayit)


def test_SENTETIK_IZINLI_kayit_YANLIS_satiri_gosterirse_KIRMIZI(sahte_kok):
    satir = "# kilit ops/hedef.sh:3 değil, :4 satırında siliniyor\n"  # çapa-sentetik: izinli fikstür (TSK-241)
    kayit = {("ops/kaynak.py", ":4"): ("ops/hedef.sh", "rm -f /tmp/kilit")}
    assert devam_hukmu([("ops/kaynak.py", satir)], kayit=kayit, yanlis_pozitif={}, kok=sahte_kok)["ihlal"] == []
    h = sahte_kok / "ops" / "hedef.sh"
    h.write_text("# yeni ilk satır\n" + h.read_text(encoding="utf-8"), encoding="utf-8")
    ihlal = devam_hukmu([("ops/kaynak.py", satir)], kayit=kayit, yanlis_pozitif={}, kok=sahte_kok)["ihlal"]
    assert [(i["tur"], i["neden"]) for i in ihlal] == [("curuk", "metin_tutmuyor")], ihlal


def test_SENTETIK_HARICI_uzantili_bitisik_ardindaki_devam_SAYILIR_hukum_ALMAZ(sahte_kok):
    satir = "# litestream tabloları (db.go:1083/1089), uydurma.go:34,36 ve uydurma.go:7 · :9\n"  # çapa-sentetik: harici fikstür (TSK-241)
    h = devam_hukmu([("deploy/x.yml", satir)], kayit={}, yanlis_pozitif={}, kok=sahte_kok)
    assert h["ihlal"] == [] and h["harici"] == 3, h


def test_SENTETIK_YANLIS_POZITIF_beyansiz_port_KIRMIZI_beyanli_SAYILIR(sahte_kok):
    """Desen boşlukla ayrılmış portu ayırt edemez (ölçülen sınır): beyansız kırmızı, beyanlı sayılır."""
    metin = [("deploy/x.sh", 'no "dashboard not answering on :8080"\n')]  # çapa-sentetik: port fikstürü (TSK-241)
    assert [i["tur"] for i in devam_hukmu(metin, kayit={}, yanlis_pozitif={}, kok=sahte_kok)["ihlal"]] == ["beyansiz"]
    yp = {("deploy/x.sh", ":8080"): "sentetik port"}
    h = devam_hukmu(metin, kayit={}, yanlis_pozitif=yp, kok=sahte_kok)
    assert h["ihlal"] == [] and h["yanlis_pozitif"] == 1 and h["kullanilan_yp"] == set(yp)


@pytest.mark.parametrize("satir", [
    "x = s[:10] + t[:1400]", "# `ts[:10]` gün dosyasını belirler", "{{ git_durum.stdout_lines[:15] | join(' | ') }}",
    "# NY seansı 13:30-20:00 UTC", "Environment=REDIS=127.0.0.1:6379", "# IPv6 [::1]:8080 ve (::1)",
    "# 2102 cf satırı 95 gerçeği 22:1 boğuyor", "# hermes-agent v0.18.2 · ansible-core 2.18.19",
    "# `hermes.py::sync_agent_skills` sembol çapası", "https://api.example.com/:id/uc", "| :--- | ---: |",
    "y = a if b else c  # dict(a=1, b= 2)", "# sürüm 3.12, ölçüm 2026-09-27T20:31Z",
])
def test_SENTETIK_YANLIS_POZITIF_uretmez(sahte_kok, satir):
    h = devam_hukmu([("ops/x.py", satir + "\n")], kayit={}, yanlis_pozitif={}, kok=sahte_kok)
    assert h["ihlal"] == [] and h["harici"] == 0, h


def test_SENTETIK_MUAFIYET_isaretleri_GECER_isaretsiz_YAKALANIR(sahte_kok):
    mezar, sentetik = _muafiyetler()
    ham = "# eski çapa ROADMAP (:503) çürümüştü"  # çapa-sentetik: muafiyet fikstürü (TSK-241)
    assert [i["tur"] for i in devam_hukmu([("meridian/x.py", ham)], kayit={}, yanlis_pozitif={},
                                            kok=sahte_kok)["ihlal"]] == ["yasak"]
    for isaret in (mezar, sentetik):
        h = devam_hukmu([("meridian/x.py", f"{ham} [{isaret}]")], kayit={}, yanlis_pozitif={}, kok=sahte_kok)
        assert h["ihlal"] == [] and h["muaf"] == 1


@pytest.mark.parametrize("rel,sinif", [
    ("MERIDIAN_ENGINEERING_LOG.md", "tarihce"),
    ("docs/TASARIM-UYDURMA-2026-09-01.md", "tarihce"),
    ("docs/RUNBOOK.md", "uretilmis"),
    ("ROADMAP.md", "rol1"),
    ("state/goal.yaml", "ssot"),
    ("skills/uydurma/SKILL.md", "skill_kutuphanesi"),
    ("deploy/oracle-a1/uydurma.service", "birim"),
    ("meridian/web/pano-assets/pano-UYDURMA.js", "uretilmis_pano"),
])
def test_SENTETIK_BEYANLI_yuzey_ATLANIR_ama_SAYILIR(sahte_kok, rel, sinif):
    metin = "bkz. ROADMAP :503 ve (:1164-1188)\n"  # çapa-sentetik: atlanan yüzey fikstürü (TSK-241)
    h = devam_hukmu([(rel, metin)], kayit={}, yanlis_pozitif={}, kok=sahte_kok)
    assert h["ihlal"] == [] and h["taranan"] == []
    assert h["atlanan"][sinif] == 2 and h["atlanan_dosya"][sinif] == 1, h["atlanan"]


def test_SENTETIK_ui_src_TARANIR_izinli_yuzey(sahte_kok):
    """v571 `ui/src`i atlar; bu dosya tarar (codelaw tsx dünyası devam biçimini görmez)."""
    h = devam_hukmu([("ui/src/Uydurma.tsx", "// satır çapası (:120) burada\n")], kayit={}, yanlis_pozitif={},  # çapa-sentetik: ui fikstürü (TSK-241)
                    kok=sahte_kok)
    assert [(i["tur"], i["capa"]) for i in h["ihlal"]] == [("beyansiz", ":120")], h["ihlal"]


# =================================================================================================
# C) KÖRLÜK ALARMI + GÖRÜNÜRLÜK — gerçek depo
# =================================================================================================

def test_KORLUK_ALARMI_taranan_dosya_ve_yuzeyler():
    """Ölçüldü 2026-09-27: 1.202 taranan dosya (262'si `ui/src`; pano paketi atlanır). Taban 900; her yüzeyden
    bir dosya adıyla zorunlu (yüzey sessizce düşmesin)."""
    h = _depo_hukmu()
    taranan = set(h["taranan"])
    assert len(taranan) >= 900, len(taranan)
    for zorunlu in ("meridian/loop.py", "meridian/watchdog.py", "meridian/web/index.html", "meridian/web/landing.html",
                    "tests/test_devam_capa_v573.py", "ops/supervise.sh", "deploy/apisix/config.yaml",
                    "deploy/oracle-a1/RUNBOOK.md", "docs/kontrast-denetimi.md", "dagit.sh", "pyproject.toml"):
        assert zorunlu in taranan, zorunlu
    assert any(r.startswith("ui/src/") for r in taranan), "ui/src taranmıyor"


def test_ATLANAN_yuzeyler_SAYILIR_ve_GEREKCELI():
    """Bedel yasası: atlanan her sınıf gerekçeli ve bugün gerçekten bir dosya atlıyor. Ölçüldü 2026-09-27 (atlanan
    devam çapası): tarihçe 1.081 · rol1 115 · ssot 5 · skill 1 · birim 0 (v563 çevirdi) — hüküm almaz, sayılır."""
    h = _depo_hukmu()
    for sinif, gerekce in BEYANLI_ATLANAN.items():
        assert len(gerekce) >= 80, sinif
        assert h["atlanan_dosya"][sinif] >= 1, f"beyanlı sınıf `{sinif}` bugün hiçbir dosyayı atlamıyor"
    for sinif in ("tarihce", "rol1", "ssot"):
        assert h["atlanan"][sinif] >= 1, (sinif, dict(h["atlanan"]))
    assert h["atlanan"]["tarihce"] >= 500


# =================================================================================================
# D) CANLI HÜKÜM — yasak yüzeyde 0 · izinli yüzeyde beyansız/çürük 0 · bayat beyan 0
# =================================================================================================

def test_YASAK_yuzeyde_meridian_DEVAM_capasi_YOK():
    ihlal = [f"{i['kaynak']} satır {i['satir']}: {i['capa']}" for i in _depo_hukmu()["ihlal"] if i["tur"] == "yasak"]
    assert not ihlal, ("motor yüzeyinde devam biçimi satır çapası — `dosya.py::ad` / backtick içinde modül + nokta + "
                       f"ad sembol çapasına ya da hedefte aranabilir bir başlık/alıntıya çevir: {ihlal}")


def test_IZINLI_yuzeyde_BEYANSIZ_devam_capasi_YOK():
    ihlal = [f"{i['kaynak']} satır {i['satir']}: {i['capa']}" for i in _depo_hukmu()["ihlal"] if i["tur"] == "beyansiz"]
    assert not ihlal, ("beyansız devam çapası — sembol/başlık çapasına çevir, ders alıntısıysa codelaw mezar taşı "
                       f"işaretini koy ya da `IZINLI_DEVAM`e hedefiyle beyan et: {ihlal}")


def test_IZINLI_yuzeyde_CURUK_kayit_YOK():
    ihlal = [f"{i['kaynak']} satır {i['satir']}: {i['capa']} ({i['neden']})" for i in _depo_hukmu()["ihlal"]
             if i["tur"] == "curuk"]
    assert not ihlal, f"beyanlı devam çapası hedefte beyan edilen metni göstermiyor: {ihlal}"


def test_BAYAT_BEYAN_YOK():
    h = _depo_hukmu()
    assert not sorted(set(IZINLI_DEVAM) - h["kullanilan_kayit"])
    assert not sorted(set(YANLIS_POZITIF) - h["kullanilan_yp"])


def test_BEYAN_kayitlari_GEREKCELI_ve_TARANAN_yuzeyde():
    for (kaynak, _capa), gerekce in YANLIS_POZITIF.items():
        assert len(gerekce) >= 60 and _atlanan_sinif(kaynak) is None, kaynak
    for (kaynak, _capa), (hedef, metin) in IZINLI_DEVAM.items():
        assert metin and (hedef is not None or len(metin) >= 60), kaynak
        assert _atlanan_sinif(kaynak) is None and _yuzey(kaynak) == "izinli", kaynak


def test_SAYIM_bugunku_dagilim():
    """Defter (2026-09-27, düzeltme sonrası): 0 doğrulanan · 0 örnek · 5 harici (litestream `db.go` kuyrukları) ·
    2 yanlış pozitif (port). YÜKSELİRSE yeni bir devam çapası beyan/kabul edilmiş demektir — bu çivi onu görünür
    kılar. Harici yolun canlı olduğu da ölçülür (alt sınır 1: hüküm dalı ölü değil)."""
    h = _depo_hukmu()
    assert h["dogrulanan"] <= 0 and h["ornek"] <= 0 and h["yanlis_pozitif"] <= 2, (
        h["dogrulanan"], h["ornek"], h["yanlis_pozitif"])
    assert 1 <= h["harici"] <= 5, h["harici"]


# =================================================================================================
# E) ÇEVRİLEN ÇAPALAR — canlı taban (doğru biçim kaynakta VAR) + yol-tutarlı çözüm
# =================================================================================================
#: (kaynak, sembol çapası, kaynakta DURMASI ZORUNLU bağlam — çapayı içerir ve BU TURUN çevirisine özgüdür; çapa
#: tek başına aranırsa kaynağın başka bir yerindeki aynı ad çiviyi boşuna yeşil tutardı). Çözüm codelaw ÜÇÜNCÜ
#: BESLEMESİNİN yolundan sınanır: `codelaw._dosya_yorum_metni` (yorum + docstring) → `codelaw.capa_uyusmasi`.
CEVRILEN_SEMBOL = [
    ("meridian/loop.py", "loop.daily_cycle", "döngünün P3 sonu (`loop.daily_cycle`)"),
    ("meridian/loop.py", "sermaye.py::_yeni_kitap", "`sermaye.py::_yeni_kitap` bu hatayı adıyla"),
    ("meridian/loop.py", "loop.MIRROR_DRIFT_TOL", "FİYAT sapmasıdır (`loop.MIRROR_DRIFT_TOL` — iç sim"),
    ("meridian/loop.py", "loop.reconcile_broker_state", "(`position_drift`, `loop.reconcile_broker_state` —"),
    ("meridian/loop.py", "loop.reconcile_broker_state", "False'tur (`loop.reconcile_broker_state` iskeleti"),
    ("meridian/watchdog.py", "watchdog.check_integrity_and_alarm",
     "üç tüketicinin (`watchdog.check_integrity_and_alarm`,"),
    ("meridian/watchdog.py", "shadowlaw.DD_VETO_MARGIN", "kendi yorumunda (`shadowlaw.DD_VETO_MARGIN` şerhi)"),
    ("meridian/watchdog.py", "watchdog.conservation_report", "(`watchdog.conservation_report`ın öğrendiği ders)"),
    ("meridian/watchdog.py", "watchdog._KORUMA_ALARMED", "aynı gerekçe: `watchdog._KORUMA_ALARMED` şerhi"),
    ("tests/test_f8_durum_sozlugu_v271.py", "watchdog.py::check_and_alarm",
     "(300 sn poll; `watchdog.py::check_and_alarm` üçünü"),
    ("tests/test_sb2_drift_sinifi_v227.py", "loop.py::_mirror_exit_sync", "`loop.py::_mirror_exit_sync`: iç defter KAPALI"),
]

#: (kaynak, kaynakta DURMASI ZORUNLU başlık/alıntı çapası — bu turun çevirisine özgü bağlamıyla, hedef yol, hedefte
#: ZORUNLU metinler).
CEVRILEN_BASLIK = [
    ("meridian/loop.py", "kümeden çıkıyor, P3-sonu çağrısı onu hiç görmüyordu", "meridian/loop.py",
     ("mirror_submit_armed(meta, dstr, eq_now=eq_now, plans=plans, halted=halted, source=\"loop\")",)),
    ("meridian/loop.py", "(yukarıdaki `eq_now = b.equity(marks_open)` satırı)", "meridian/loop.py",
     ("    eq_now = b.equity(marks_open)\n",)),
    ("meridian/loop.py", "+ iç `_skip` damgası;", "meridian/loop.py",
     ("    def _skip(reason: str, sinif: str = \"olculemedi\") -> dict:", "\"checked\": False, \"skip_reason\"")),
    ("meridian/api.py", "(bekçiler segmentinin `askida` listesi, yukarıda)", "meridian/api.py",
     ("\"askida\": [{\"ad\": a.get(\"name\"), \"neden\": a.get(\"neden\"), \"detay\": a.get(\"detay\"),",)),
    ("meridian/web/index.html", "sınıfları (yukarıdaki `.pos`/`.neg` kuralı)", "meridian/web/index.html",
     (".pos{color:var(--yon-arti)} .neg{color:var(--yon-eksi)}",)),
    ("meridian/web/landing.html", "(«ürün maketi · örnek ekran» etiketi yalnız", "meridian/web/landing.html",
     ("ürün maketi · örnek ekran · aşağıdaki sayılar ölçüm değildir",)),
]


@pytest.mark.parametrize("kaynak,capa,baglam", CEVRILEN_SEMBOL)
def test_cevrilen_SEMBOL_capasi_KAYNAKTA_duruyor(kaynak, capa, baglam):
    """Bağlamıyla: çeviri silinirse ya da ad `adX`e kayarsa kırmızı (bağlam çapayı sınır kontrollü içerir)."""
    assert re.search(re.escape(capa) + r"(?![A-Za-z0-9_])", baglam), (capa, baglam)
    assert baglam in (REPO / kaynak).read_text(encoding="utf-8"), f"{kaynak} içinde `{baglam}` yok"


def test_cevrilen_SEMBOL_capalari_UCUNCU_BESLEME_yolundan_COZULUR():
    """Yol-tutarlı pozitif kontrol: çevrilen çapalar codelaw'ın üçüncü beslemesinin ÇIKARIMINDAN (yorum + docstring)
    geçip `cozulen`e düşer. Düşmezse çapa kod dizgesine kaymış ya da çıkarım onu görmüyor demektir. (Repo geneli
    `curuyen == []` hükmü üçüncü beslemenindir — `tests/test_yorum_sembol_capasi_v402.py`; burada tekrarlanmaz.)"""
    kaynaklar = sorted({k for k, _c, _b in CEVRILEN_SEMBOL})
    kokler = tuple(str(REPO / k) for k in ("meridian", *codelaw._EK_CAPA_KOKLERI))
    h = codelaw.capa_uyusmasi([(k, codelaw._dosya_yorum_metni(REPO / k)) for k in kaynaklar], py_kokler=kokler,
                              modul_bicimi=True)
    cozulen = {(c["kaynak"], c["capa"]) for c in h["cozulen"]}
    eksik = [(k, c) for k, c, _b in CEVRILEN_SEMBOL if (k, c) not in cozulen]
    assert not eksik, eksik


@pytest.mark.parametrize("kaynak,capa,_hedef,_metinler", CEVRILEN_BASLIK)
def test_cevrilen_BASLIK_capasi_KAYNAKTA_duruyor(kaynak, capa, _hedef, _metinler):
    assert capa in (REPO / kaynak).read_text(encoding="utf-8"), f"{kaynak} içinde `{capa}` yok"


@pytest.mark.parametrize("kaynak,capa,hedef,metinler", CEVRILEN_BASLIK)
def test_cevrilen_BASLIK_capasi_HEDEFTE_gercekten_var(kaynak, capa, hedef, metinler):
    govde = (REPO / hedef).read_text(encoding="utf-8")
    eksik = [m for m in metinler if m not in govde]
    assert not eksik, f"{kaynak} çapası `{capa}` → {hedef} içinde bulunamadı: {eksik}"

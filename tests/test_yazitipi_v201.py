"""YAZI TİPİ SÖZLEŞMESİ — Recursive, KENDİ-BARINDIRILAN, CSP'si daraltılmış (D4, 2026-08-07).

NİYE VAR. Bu turda üç şey aynı anda oldu ve üçü de sessizce geri alınabilir:

  1. **Geist emekli edildi**, yerine Recursive Sans/Mono Linear geldi (hüküm ve dokuz adaylık
     havuz: `docs/YAZI-TIPI-OLCUMU-2026-08-07.md`). Bir yüzeyde `--sans`/`--mono` eski değere
     dönerse pano iki farklı yazı tipiyle çizilir ve kimse fark etmez — çünkü ikisi de "çalışır".
  2. **Yazı tipi kendi-barındırılır oldu ve CSP DARALDI.** Önce `style-src`de
     `https://fonts.googleapis.com`, `font-src`de `https://fonts.gstatic.com` vardı. İkisi de
     düştü. Bu bir maliyet değil bir SERTLEŞTİRMEdir; ve sertleştirmenin geri alınması bir
     satırlık bir iştir: biri bir yüzeye `<link href="https://fonts...">` koyar, font yüklenmez,
     "CSP'yi gevşetelim" denir ve iki dış host geri gelir. Bu dosya o yolu kapatır.
  3. **İki kesit yeniden adlandırıldı.** Ölçüm turunun ürettiği iki TTF de `nameID 1` olarak
     `Recursive Sans Linear Light` diyordu — `MONO=1` ile sabitlenmiş kesit dahil, yani ikili
     kendi hakkında yanlış beyan taşıyordu.

ÖLÇÜM ≠ BEYAN. Bu dosyadaki hiçbir iddia "öyledir" diye yazılmadı; her biri ya kaynak dosyadan
ya `research/olcumler/yazi_tipi_2026-08-07/web_fonts_build.json` (üretim kaydı) ya da
`research/olcumler/yazi_tipi_2026-08-07/tarayici/olcum_sonucu.json` (GERÇEK tarayıcı ölçümü)
üzerinden okunur. Ölçüm raporunun kendi hükmü buydu: "render tarayıcı DEĞİL … kazanan aday için
D4'te tarayıcı teyit turu ZORUNLU". Tur koşuldu ve iki hükmü DEĞİŞTİRDİ (bkz.
`test_isim_cakismasi_BLOKE_EDICI_DEGILDI` ve `test_bir_ile_l_TARAYICIDA_geistten_iyi`).

Ağ istemez, tarayıcı istemez, fontTools istemez — hepsi diskten okunur.
"""
import json
import pathlib
import re

import pytest

KOK = pathlib.Path(__file__).resolve().parents[1]
WEB = KOK / "meridian" / "web"
FONTLAR = WEB / "fonts"
CADDY = KOK / "deploy" / "Caddyfile"
DESIGN = KOK / "DESIGN.md"
OLCUM = KOK / "research" / "olcumler" / "yazi_tipi_2026-08-07"
BUILD_JSON = OLCUM / "web_fonts_build.json"
TARAYICI = OLCUM / "tarayici"

# Yazı tipi taşıyan üç yüzey. `runbook.html` BİLEREK DIŞARIDA: o sayfa D2-b'de yönlendirmeye
# çevrildi, D5'te silinecek ve zaten hiç dış font yüklemiyor (kendi `ui-sans-serif` yığınıyla
# çalışır — "ağ yokken de açılır" onun kendi sözleşmesi). Kapsam dışı olduğu BURADA yazılı ki
# "unutuldu mu" sorusu bir daha sorulmasın.
YUZEYLER = ["index.html", "landing.html", "workflow.html"]
# CDN taraması TÜM yüzeyleri kapsar — runbook dahil, çünkü oraya bir CDN linki sızarsa
# CSP daraltması onu da vurur.
TUM_YUZEYLER = YUZEYLER + ["runbook.html", "app.js", "theme.js", "landing.js",
                           "workflow.js", "palette.js"]

SANS_DOSYA = "recursive-sans-vf.woff2"
MONO_DOSYA = "recursive-mono-vf.woff2"

# Türkçe'nin ayırt edici on iki karakteri. "Muhtemelen vardır" yazılmaz — tek tek sayılır.
TURKCE = {0x0131: "ı", 0x0130: "İ", 0x015F: "ş", 0x015E: "Ş",
          0x011F: "ğ", 0x011E: "Ğ", 0x00E7: "ç", 0x00C7: "Ç",
          0x00F6: "ö", 0x00D6: "Ö", 0x00FC: "ü", 0x00DC: "Ü"}


def _oku(ad: str) -> str:
    p = WEB / ad
    assert p.is_file(), f"{ad} YOK — yüzey silinmişse bu testin kapsamı da güncellenmeli"
    return p.read_text(encoding="utf-8")


# HTML yorumu, CSS/JS blok yorumu ve JS satır yorumu. Yorumları ELEMEK bu dosyanın
# ölçüm disiplininin bir parçası: bu depoda kayıt geçmişi SİLMEZ, üstünü çizer — "bu satır
# eskiden fonts.googleapis.com'a gidiyordu" cümlesi kalıcı ve DOĞRU bir kayıttır. Sözleşme
# tarayıcının ÇALIŞTIRDIĞI metin üzerinde kurulur; yorum üzerinde kurulsaydı, testi yeşile
# çevirmenin en kolay yolu kaydı silmek olurdu.
_YORUM = re.compile(r"<!--.*?-->|/\*.*?\*/|^[ \t]*//[^\n]*$", re.S | re.M)


def _yorumsuz(kaynak: str) -> str:
    return _YORUM.sub(" ", kaynak)


@pytest.fixture(scope="module")
def build_kaydi():
    assert BUILD_JSON.is_file(), (
        f"{BUILD_JSON} YOK. Fontlar kayıtsız üretilmiş demektir: hangi kaynaktan, hangi eksen "
        "aralığıyla, hangi özellik kümesiyle sorularının cevabı kalmamış. "
        "Çözüm: research/olcumler/yazi_tipi_2026-08-07/build_web_fonts.py koş.")
    return json.loads(BUILD_JSON.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def tarayici_olcumu():
    p = TARAYICI / "olcum_sonucu.json"
    assert p.is_file(), (
        f"{p} YOK — tarayıcı teyit turunun kaydı kayıp. Ölçüm raporu §7/2 bu turu ZORUNLU "
        "ilan etmişti; kaydı olmayan bir tur koşulmamış sayılır.")
    return json.loads(p.read_text(encoding="utf-8"))


# ===================== Ç1 · DIŞ ORIGIN — CSP SERTLEŞTİRMESİ =====================

@pytest.mark.parametrize("ad", TUM_YUZEYLER)
def test_hicbir_yuzey_DIS_ORIGINDEN_yazi_tipi_cekmez(ad):
    """Google Fonts (ya da herhangi bir CDN) referansı hiçbir yüzeyde OLMAMALI.

    Bu tur öncesi üç yüzey de `fonts.googleapis.com`a `<link>` atıyordu ve `deploy/Caddyfile`
    CSP'si tam olarak bunu barındırmak için iki dış host taşıyordu — yani
    `docs/TASARIM-YONU-2026-08-07.md` §5'in "CSP dış font-host'a izin vermez" cümlesi bir
    BEYANDI, ölçüm değil. Artık ölçülüyor."""
    kaynak = _yorumsuz(_oku(ad))
    for host in ("fonts.googleapis.com", "fonts.gstatic.com", "use.typekit.net",
                 "fonts.bunny.net", "cdn.jsdelivr.net", "unpkg.com"):
        assert host not in kaynak, (
            f"{ad} içinde dış origin {host!r} var. CSP artık `font-src 'self'` ve "
            f"`style-src 'self' 'unsafe-inline'` — bu istek ÜRETİMDE BLOKLANIR ve sayfa "
            f"sistem yüzüne düşer. Çözüm CSP'yi gevşetmek DEĞİL: dosyayı "
            f"meridian/web/fonts/ altına koy ve @font-face'i yerel yolla yaz.")


@pytest.mark.parametrize("ad", TUM_YUZEYLER)
def test_hicbir_yuzey_CANLI_bildirimde_Geist_tasimaz(ad):
    """`font-family` / `@font-face src` gibi CANLI bildirimlerde Geist kalmamalı.

    DÜZ METİN ARAMASI YAPILMIYOR ve bu bilinçli: yorumlarda Geist'in ADI GEÇMEYE DEVAM EDER
    ("bu satır eskiden Geist diyordu"). Bu deponun kaydı geçmişi silmez, üstünü çizer. Test
    o yüzden yalnız tarayıcının OKUDUĞU yerlere bakar."""
    kaynak = _yorumsuz(_oku(ad))
    canli = re.findall(r"font-family\s*:\s*([^;}\n]+)", kaynak)
    canli += re.findall(r"src\s*:\s*url\([^)]*\)[^;]*", kaynak)
    kirli = [c for c in canli if "geist" in c.lower()]
    assert not kirli, f"{ad}: CANLI bildirimde Geist duruyor → {kirli}"


def test_caddyfile_CSP_dis_font_hostu_TASIMAZ():
    """`font-src` ve `style-src` hiçbir dış host taşımamalı — ve bu iki host GERİ EKLENMEMELİ.

    D4'ten ÖNCE:
        style-src 'self' 'unsafe-inline' https://fonts.googleapis.com
        font-src  'self' https://fonts.gstatic.com
    SONRA:
        style-src 'self' 'unsafe-inline'
        font-src  'self'
    """
    assert CADDY.is_file(), "deploy/Caddyfile YOK — CSP sözleşmesi ölçülemez"
    metin = CADDY.read_text(encoding="utf-8")
    m = re.search(r'Content-Security-Policy\s+"([^"]+)"', metin)
    assert m, "Caddyfile'da Content-Security-Policy başlığı bulunamadı"
    csp = m.group(1)
    yonergeler = {}
    for parca in csp.split(";"):
        parca = parca.strip()
        if parca:
            ad, *degerler = parca.split()
            yonergeler[ad] = degerler

    assert "font-src" in yonergeler, "font-src yönergesi yok — varsayılan `default-src`e düşmek BEYAN DEĞİL"
    assert yonergeler["font-src"] == ["'self'"], (
        f"font-src gevşetilmiş: {yonergeler['font-src']}. Yazı tipleri KENDİ-BARINDIRILIYOR "
        f"(/fonts/*.woff2); buraya bir host eklendiyse bir yere CDN linki geri gelmiş demektir.")

    style = yonergeler.get("style-src", [])
    dis = [k for k in style if k.startswith("http")]
    assert not dis, (
        f"style-src'de dış host: {dis}. Font CSS'i artık dışarıdan gelmiyor; bu izin ancak "
        f"bir <link rel=stylesheet> geri geldiyse gerekir.")

    # Bütün CSP'de font/stil için dış host kalmadığının ikinci, bağımsız okuması.
    for host in ("fonts.googleapis.com", "fonts.gstatic.com"):
        assert host not in csp, f"CSP'de {host} hâlâ var"


# ===================== Ç2 · @font-face SÖZLEŞMESİ =====================

FF_DESEN = re.compile(r"@font-face\s*\{(.*?)\}", re.S)


def _font_face_blogu(kaynak: str) -> list[dict]:
    bloklar = []
    for govde in FF_DESEN.findall(kaynak):
        d = {}
        for satir in govde.split(";"):
            if ":" in satir:
                k, v = satir.split(":", 1)
                d[k.strip()] = v.strip()
        bloklar.append(d)
    return bloklar


@pytest.mark.parametrize("ad", YUZEYLER)
def test_yuzey_IKI_yerel_font_face_tasir(ad):
    """Her yüzeyde tam iki `@font-face` — sans + mono — ve ikisi de YEREL yoldan."""
    bloklar = _font_face_blogu(_yorumsuz(_oku(ad)))
    assert len(bloklar) == 2, f"{ad}: {len(bloklar)} @font-face bloğu var, 2 bekleniyordu"

    aileler = [b.get("font-family", "") for b in bloklar]
    assert any("Recursive Sans" in a for a in aileler), f"{ad}: 'Recursive Sans' @font-face yok"
    assert any("Recursive Mono" in a for a in aileler), f"{ad}: 'Recursive Mono' @font-face yok"

    for b in bloklar:
        src = b.get("src", "")
        assert "url('/fonts/" in src, (
            f"{ad}: @font-face src yerel değil → {src!r}. Yol `/fonts/…` olmalı; "
            f"http(s):// bir yol CSP `font-src 'self'` tarafından bloklanır.")
        assert "format('woff2')" in src, f"{ad}: woff2 formatı bildirilmemiş → {src!r}"
        assert "http" not in src, f"{ad}: src'de mutlak URL var → {src!r}"


@pytest.mark.parametrize("ad", YUZEYLER)
def test_font_display_BLOCK_swap_DEGIL(ad):
    """`font-display` KASITLI olarak `block`; `swap` YASAK.

    Gerekçe DESIGN.md § Typography'de tam metin: `swap` yedek yüzle çizip SONRA değiştirir ve
    bu panonun her sayısı tabular mono'dur — takas anında rakam sütunu YATAY KAYAR. `optional`
    ise yavaş bir açılışta oturum boyunca yanlış yüzde bırakır. `block` yanlış çizmek yerine
    BEKLETİR; penceresi de sınırlıdır (aynı origin, ~79 KB, preload'lı, no-cache önbellekli).
    Bu test hükmü çiviler: `swap`a dönüş sessiz bir tasarım gerilemesidir."""
    for b in _font_face_blogu(_yorumsuz(_oku(ad))):
        fd = b.get("font-display")
        assert fd is not None, f"{ad}: @font-face'te font-display BİLDİRİLMEMİŞ (varsayılan `auto`)"
        assert fd == "block", (
            f"{ad}: font-display={fd!r}. `swap` rakam sütununu okuma anında kaydırır, "
            f"`optional` oturum boyunca yanlış yüzde bırakır — bkz. DESIGN.md § Typography.")


@pytest.mark.parametrize("ad", YUZEYLER)
def test_degisken_agirlik_ARALIGI_bildirilmis(ad):
    """`font-weight: 400 700` — TEK bir ağırlık değil, EKSEN ARALIĞI.

    Bu bildirim atlanırsa (ya da `normal` yazılırsa) tarayıcı değişken ekseni sürmez ve
    500/600/700 isteyen 111 kural sentetik kalınlığa düşer. Aralığın kendisi de ölçülmüş:
    dosyanın `wght` ekseni 400-700'e daraltıldı, çünkü üç yüzeydeki her `font-weight`
    bildirimi bu aralıkta (400/500/600/700) — ve daraltma 117,9 KB'ı 79,3 KB'a indirdi."""
    for b in _font_face_blogu(_yorumsuz(_oku(ad))):
        fw = b.get("font-weight")
        assert fw == "400 700", (
            f"{ad}: font-weight={fw!r}, '400 700' bekleniyordu. Aralık bildirilmezse "
            f"değişken eksen sürülmez.")


def test_uc_yuzeyin_font_bildirimleri_BIREBIR_AYNI():
    """Üç yüzey aynı iki dosyayı AYNI aile adıyla istemeli.

    Ayrışırsa iki ayrı arıza doğar ve ikisi de sessizdir: (a) tarayıcı aynı yüzü iki ayrı aile
    adı altında İKİ KEZ indirir, (b) `--sans` bir sayfada Recursive'e, ötekinde sistem yüzüne
    çözülür — yani "iki zemin, tek ürün" kuralının tipografik ihlali."""
    imzalar = {}
    for ad in YUZEYLER:
        bloklar = _font_face_blogu(_yorumsuz(_oku(ad)))
        imzalar[ad] = sorted(
            tuple(sorted((k, re.sub(r"\s+", " ", v)) for k, v in b.items())) for b in bloklar)
    referans = imzalar[YUZEYLER[0]]
    for ad in YUZEYLER[1:]:
        assert imzalar[ad] == referans, (
            f"{ad} ile {YUZEYLER[0]} @font-face bildirimleri ayrışmış:\n"
            f"  {YUZEYLER[0]}: {referans}\n  {ad}: {imzalar[ad]}")


@pytest.mark.parametrize("ad", YUZEYLER)
def test_jetonlar_RECURSIVE_ve_yedekler_KORUNDU(ad):
    """`--sans`/`--mono` Recursive'e bağlı, ve sistem yedekleri KALDI.

    Yedek yığınının kalması şart: `font-display:block` üç saniyelik bir pencere tanır ve o
    pencere dolarsa tarayıcı yedeğe düşer. Yedeksiz bir `--mono`, dosya bir gün gelmediğinde
    rakam sütununu ORANSAL bir yüze düşürür — hizanın sessizce ölmesi."""
    kaynak = _yorumsuz(_oku(ad))
    sans = re.search(r"--sans\s*:\s*([^;]+);", kaynak)
    mono = re.search(r"--mono\s*:\s*([^;]+);", kaynak)
    assert sans and mono, f"{ad}: --sans / --mono jetonu bulunamadı"
    assert sans.group(1).strip().startswith("'Recursive Sans'"), f"{ad}: --sans → {sans.group(1)!r}"
    assert mono.group(1).strip().startswith("'Recursive Mono'"), f"{ad}: --mono → {mono.group(1)!r}"
    assert "system-ui" in sans.group(1), f"{ad}: --sans sistem yedeği kaybolmuş"
    assert "ui-monospace" in mono.group(1), f"{ad}: --mono sistem yedeği kaybolmuş"


@pytest.mark.parametrize("ad", YUZEYLER)
def test_preload_crossorigin_TASIR(ad):
    """İki `preload` var ve ikisi de `crossorigin` taşıyor.

    `crossorigin` ATLANMASI klasik ve sessiz bir arızadır: font istekleri HER ZAMAN CORS
    kipindedir, öznitelik yoksa preload'ın getirdiği kopya @font-face'in isteğiyle EŞLEŞMEZ ve
    tarayıcı dosyayı İKİ KEZ indirir. `block` penceresinde bu, beklemeyi uzatır."""
    kaynak = _yorumsuz(_oku(ad))
    preloadlar = re.findall(r"<link[^>]*rel=[\"']preload[\"'][^>]*>", kaynak)
    fontlar = [p for p in preloadlar if "as=\"font\"" in p or "as='font'" in p]
    assert len(fontlar) == 2, f"{ad}: {len(fontlar)} font preload'ı var, 2 bekleniyordu"
    for p in fontlar:
        assert "crossorigin" in p, f"{ad}: preload'da crossorigin yok → çift indirme: {p}"
        assert "font/woff2" in p, f"{ad}: preload'da type=font/woff2 yok → {p}"
    for dosya in (SANS_DOSYA, MONO_DOSYA):
        assert any(dosya in p for p in fontlar), f"{ad}: {dosya} preload edilmemiş"


# ===================== Ç3 · DAĞITILAN İKİLİLER =====================

def test_woff2_dosyalari_VAR_ve_kayitla_ESLESIYOR(build_kaydi):
    """Diskteki dosya ile üretim kaydı BİRE BİR — jeton eş-kaydının font tarafındaki aynası.

    Kayıt ile artefakt ayrışabilir (biri yeniden üretilir, öteki commit'lenmez); ayrıştıklarında
    kayıt "hangi font dağıtılıyor" sorusuna YANLIŞ cevap verir ve yanlış cevabın kendisi bir
    ölçüm gibi okunur."""
    kayitlar = {k["dosya"]: k for k in build_kaydi["kesitler"]}
    assert set(kayitlar) == {SANS_DOSYA, MONO_DOSYA}, f"kayıttaki dosyalar: {sorted(kayitlar)}"
    for ad, k in kayitlar.items():
        p = FONTLAR / ad
        assert p.is_file(), f"{p} YOK — dağıtımda font eksik, üç yüzey de sistem yüzüne düşer"
        assert p.stat().st_size == k["bayt"], (
            f"{ad}: diskte {p.stat().st_size} bayt, kayıtta {k['bayt']} — "
            f"kayıt artefaktla ayrışmış (build_web_fonts.py yeniden koşulmalı)")


def test_ISIM_CAKISMASI_COZULDU(build_kaydi):
    """İki kesit AYRI aile ve AYRI postscript adı taşımalı — ve nameID 16 SİLİNMİŞ olmalı.

    Ölçüm turunun ürettiği iki TTF de `nameID 1 = 'Recursive Sans Linear Light'`,
    `postscript = 'Recursive-SansLinearLight'` diyordu; yani `MONO=1` kesiti kendine "Sans"
    diyordu. nameID 16 (typographic family) da ikisinde de `Recursive`ti — bırakılsaydı iki
    kesit o kayıt üzerinden YENİDEN birleşirdi, yani çakışma bir alt kayıttan geri gelirdi."""
    k = {x["dosya"]: x for x in build_kaydi["kesitler"]}
    sans, mono = k[SANS_DOSYA], k[MONO_DOSYA]

    assert sans["nameID1"] == "Recursive Sans", f"sans aile adı: {sans['nameID1']!r}"
    assert mono["nameID1"] == "Recursive Mono", f"mono aile adı: {mono['nameID1']!r}"
    assert sans["nameID1"] != mono["nameID1"], "iki kesit AYNI aile adını taşıyor — çakışma geri gelmiş"
    assert sans["nameID6"] != mono["nameID6"], (
        f"postscript adları çakışık: {sans['nameID6']!r} == {mono['nameID6']!r}")
    for x in (sans, mono):
        assert x["nameID16"] is None, (
            f"{x['dosya']}: nameID 16 = {x['nameID16']!r}. Typographic family kaydı iki kesiti "
            f"tek ailede yeniden birleştirir — silinmiş olmalı.")


def test_rakamlar_YAPISAL_tabular_HER_IKI_KESITTE(build_kaydi):
    """Sıfırdan dokuza tek bir advance — mono'da VE sans'ta.

    "The Tabular Rule"un yapısal dayanağı budur ve Geist'e göre asıl kazançlardan biri: Geist
    Sans'ta hizalama `tnum` bildirimine bağlıydı, burada yapıya bağlı."""
    for x in build_kaydi["kesitler"]:
        assert x["rakam_advance"] == [600], (
            f"{x['dosya']}: rakam advance kümesi {x['rakam_advance']} — tek değer (600) "
            f"bekleniyordu; hizalama artık yapısal DEĞİL.")


def test_agirlik_ekseni_400_700_ve_varsayilan_400(build_kaydi):
    """`wght` ekseni 400-700, VARSAYILAN 400.

    Varsayılan kalemi bir tuzağı kapatıyor: Recursive'in kendi `wght` varsayılanı **300**'dür
    (ölçüm raporu §7/5 bunu açık kalem olarak devretmişti). 400 tabanlı bir eksende `@font-face`
    bildirimi bir gün düşse bile yüz İNCE açılmaz."""
    assert build_kaydi["wght_aralik"] == [400, 700], f"kayıt: {build_kaydi['wght_aralik']}"
    for x in build_kaydi["kesitler"]:
        assert x["fvar"]["wght"] == [400.0, 400.0, 700.0], f"{x['dosya']}: fvar {x['fvar']}"
        assert x["usWeightClass"] == 400, f"{x['dosya']}: usWeightClass {x['usWeightClass']}"


def test_TURKCE_glif_civisi(build_kaydi):
    """On iki Türkçe karakterin HİÇBİRİ subset dışında kalmamış olmalı.

    Bu bir "muhtemelen vardır" testi değil: `build_web_fonts.py` istenen ama fontta BULUNAMAYAN
    her kod noktasını `fontta_yok` listesine yazar (uydurma yasağı — "hepsi var" demek yerine
    olmayanları sayar). Türkçe'den bir harf o listeye düşerse pano `ÖLÇÜLEMEDİ`yi tofu ile
    yazar."""
    yok = set(build_kaydi["fontta_yok"])
    eksik = {f"U+{cp:04X}": ch for cp, ch in TURKCE.items() if f"U+{cp:04X}" in yok}
    assert not eksik, f"Türkçe karakter subset dışında kalmış: {eksik}"
    # cmap sayımı da kayda giriyor: bir gün subset kümesi daraltılırsa sayı düşer ve görünür olur.
    for x in build_kaydi["kesitler"]:
        assert x["cmap"] >= 250, f"{x['dosya']}: cmap {x['cmap']} — subset beklenmedik ölçüde dar"


def test_dagitim_boyutu_BUTCEDE(build_kaydi):
    """Toplam ~79 KB. Bütçe bir SAYI değil bir KAPI: sessizce iki katına çıkmasın.

    120 KB eşiği ölçülmüş bir sınırdan geliyor: aynı kod noktası kümesiyle tam eksen (300-1000)
    117,9 KB veriyordu. Toplam oraya doğru tırmanıyorsa ya eksen daraltması ya yalın özellik
    kümesi geri alınmış demektir."""
    toplam = build_kaydi["toplam_bayt"]
    assert toplam == sum((FONTLAR / x["dosya"]).stat().st_size for x in build_kaydi["kesitler"])
    assert toplam < 120 * 1024, (
        f"font çifti {toplam/1024:.1f} KB — 120 KB kapısının üstünde. Eksen aralığı ya da "
        f"yalın özellik kümesi geri alınmış olabilir (bkz. build_web_fonts.py).")


def test_OFL_lisansi_FONTLARLA_BIRLIKTE_dagitiliyor():
    """OFL 1.1, telif kaydının ikili ile birlikte taşınmasını İSTER. Dosya orada olmalı."""
    p = FONTLAR / "OFL.txt"
    assert p.is_file(), (
        "meridian/web/fonts/OFL.txt YOK. SIL OFL 1.1 telif + izin bildiriminin kopyalarla "
        "birlikte taşınmasını şart koşar; font dosyalarını lisanssız dağıtmak ihlaldir.")
    metin = p.read_text(encoding="utf-8")
    assert "The Recursive Project Authors" in metin, "telif sahibi kaydı yok"
    assert "SIL OPEN FONT LICENSE Version 1.1" in metin, "lisans metni yok"
    # OFL §3: değiştirilmiş sürüm ise, ne yapıldığı kayda geçmeli.
    assert "Reserved Font Name" in metin, (
        "Rezerve Font Adı durumu kayda geçmemiş. Recursive'in telif kaydında RFN YOKTUR "
        "(ölçüldü) — türetmenin 'Recursive' adını koruması bu yüzden serbest; bu tespit "
        "dosyada durmazsa bir sonraki tur onu yeniden ölçmek zorunda kalır.")


# ===================== Ç4 · TARAYICI TEYİT TURU =====================

def _satir(olcum, aile):
    for s in olcum["satirlar"]:
        if s["aile"] == aile:
            return s
    raise AssertionError(f"tarayıcı ölçümünde {aile!r} satırı yok")


def test_tarayici_turu_KOSULDU_ve_kaniti_diskte():
    """Ölçüm raporunun ZORUNLU ilan ettiği tur koşuldu ve artefaktları duruyor.

    Bir tarayıcı turu "yapıldı" denebilir ama kanıtı yoksa yapılmamıştır. Bu test kanıt
    dosyalarının varlığını çiviler; içerikleri aşağıdaki testlerde okunur."""
    beklenen = ["olcum_sonucu.json", "01_isim_cakismasi.png", "02_ornek_iki_zemin.png",
                "03_ornek_1x_gercek_piksel.png", "04_yakinlastirma_6x.png",
                # 05-07: SENTETİK ÖRNEK DEĞİL, GERÇEK YÜZEYLER. Bir yazı tipi örneği "yüz
                # güzel mi"yi gösterir; asıl soru "sistemin kendi ekranında ne oluyor"dur.
                # Bu üçü meridian/web/ dosyalarının kendisinden alındı (statik sunucu + boş
                # /api/*; Meridian uygulaması YÜKLENMEDİ — CLAUDE.md §5).
                "05_pano_index_gercek_yuzey.png", "06_landing_gercek_yuzey.png",
                "07_workflow_gercek_yuzey.png",
                "ornek.html", "isim_cakismasi.html", "olcum.js", "yakinlastir.html",
                "yakinlastir.js"]
    eksik = [a for a in beklenen if not (TARAYICI / a).is_file()]
    assert not eksik, f"tarayıcı teyit artefaktları eksik: {eksik}"


def test_mono_TARAYICIDA_gercekten_mono_sans_ORANSAL(tarayici_olcumu):
    """`i` ile `M` genişliği: mono'da EŞİT, sans'ta EŞİT DEĞİL.

    Bu tek sayı "mono gerçekten yüklendi mi"yi karara bağlar. Oransal bir yüzde `i` = `M`
    İMKÂNSIZDIR; yani mono yüklenmemiş olsaydı (ya da iki aile çakışıp tek yüze düşseydi)
    bu test kırmızı verirdi — göz kararına gerek kalmadan."""
    h = tarayici_olcumu["hukum"]
    assert h["yeni_mono_gercekten_mono"] is True, "mono yüz monospace ÇIKMADI — yanlış dosya yüklenmiş"
    assert h["yeni_sans_oransal"] is True, "sans yüz oransal ÇIKMADI — mono dosya sans yerine geçmiş"
    assert h["yeni_cift_ayrisiyor_mu"] is True, "iki aile tarayıcıda AYRIŞMIYOR"
    assert h["yeni_mono_rakamlar_tekduze"] is True and h["yeni_sans_rakamlar_tekduze"] is True

    mono, sans = _satir(tarayici_olcumu, "YENI Mono"), _satir(tarayici_olcumu, "YENI Sans")
    assert mono["i_genislik"] == mono["M_genislik"], f"mono: i={mono['i_genislik']} M={mono['M_genislik']}"
    assert sans["i_genislik"] != sans["M_genislik"], f"sans: i={sans['i_genislik']} M={sans['M_genislik']}"


def test_bir_ile_l_TARAYICIDA_geistten_iyi(tarayici_olcumu):
    """`1` ile `l` — MÜREKKEPLE ölçüldü, advance ile değil, ve Geist tabanıyla yan yana.

    ÖNEMLİ DÜZELTME, KAYDA GEÇSİN. Ölçüm raporu Geist'in `1`/`l` çiftini "birebir aynı" ilan
    ederken ADVANCE GENİŞLİĞİ ve kontur sayısı okumuştu. Advance monospace bir yüzde HİÇBİR
    ŞEYİ ayıramaz — her glif 600'dür; o ölçüt başka bir soruya cevap veriyordu. Mürekkep olarak
    ölçüldüğünde Geist'in çifti de ayrışıyor (10px'te 0,92) — DESIGN.md'nin 2026-08-01 tarihli
    tarayıcı turunun zaten söylediği şey. Recursive'in 1,00'i GERÇEK bir tabana karşı gerçek bir
    iyileşmedir, bir kusurdan kurtarma değil. İddia küçüldü ama ÖLÇÜLEBİLİR oldu."""
    h = tarayici_olcumu["hukum"]
    yeni10, geist10 = h["yeni_mono_1l_10px_fark_orani"], h["geist_mono_1l_10px_fark_orani"]
    yeni28, geist28 = h["yeni_mono_1l_28px_fark_orani"], h["geist_mono_1l_28px_fark_orani"]
    assert yeni10 > geist10, f"10px'te Recursive {yeni10} ≤ Geist {geist10} — ayrım iyileşmemiş"
    assert yeni28 > geist28, f"28px'te Recursive {yeni28} ≤ Geist {geist28}"
    assert yeni10 >= 0.75, f"10px'te `1`/`l` fark oranı {yeni10} — kabul çıtasının altında"


def test_isim_cakismasi_BLOKE_EDICI_DEGILDI(tarayici_olcumu):
    """ÖLÇÜLMÜŞ DÜZELTME: çakışma self-host'u BOZMUYORDU.

    Ölçüm raporu §7/1 bunu "bloke edici" ilan etmiş ve "self-host edilirse MONO KAYBOLUR"
    demişti. Sınandı: isimleri çakışan ESKİ çift bile, iki ayrı `@font-face` ailesi altında
    yüklendiğinde İKİ AYRI YÜZE çözüldü — çünkü CSS'te bildirilen aile adı ikilinin kendi
    adını EZER.

    Kesitler yine de yeniden adlandırıldı, ve bu test o kararı bir KURTARMA değil bir
    DOĞRULUK işi olarak kayda geçiriyor: `MONO=1` kesitinin kendine "Sans Linear Light"
    demesi bir içerik yalanıdır ve `local()` eşleşmesinde, font yöneticisinde, devtools'ta
    yüzeye çıkar. Ama uygulamayı bloke etmiyordu — ve bloke etmeyen bir şeyi "bloke edici"
    diye kaydetmek, bir sonraki turda yanlış yere bütçe ayırtır."""
    assert tarayici_olcumu["hukum"]["eski_cift_ayrisiyor_mu"] is True, (
        "ölçüm bu turda TERSİNE döndü: çakışık isimli çift artık ayrışmıyor. O hâlde "
        "yeniden adlandırma GERÇEKTEN bloke ediciydi ve bu testin gerekçesi güncellenmeli.")


# ===================== Ç5 · BELGE (DESIGN.md) =====================

def test_DESIGN_md_tipografi_RECURSIVE_diyor():
    """Ön-madde jetonları ve Typography bölümü aynı yazı tipini söylemeli.

    DESIGN.md iki yerde tipografi beyan eder: dosyanın başındaki makine-okunur `typography:`
    bloğu ve `## Typography` bölümü. Biri güncellenip öteki bırakılırsa belge kendi kendisiyle
    çelişir — ve bu deponun kayıtlı kusur sınıfı tam olarak budur."""
    metin = DESIGN.read_text(encoding="utf-8")
    on_madde = metin.split("---", 2)[1]
    assert "Recursive Sans" in on_madde and "Recursive Mono" in on_madde, \
        "DESIGN.md ön-madde `typography:` bloğu hâlâ eski yazı tipini bildiriyor"
    assert "Geist" not in on_madde, "DESIGN.md ön-maddesinde Geist kalmış"

    tipo = metin.split("## Typography", 1)[1].split("\n## ", 1)[0]
    for beklenen in ("Recursive Sans Linear", "Recursive Mono Linear",
                     "SIL Open Font License 1.1", "self-hosted"):
        assert beklenen in tipo, f"DESIGN.md § Typography'de {beklenen!r} geçmiyor"
    # KAYIP KALEMİ DÜRÜSTÇE YAZILMIŞ OLMALI — kazanç tablosu tek başına bir satış metnidir.
    assert "−0.10 px" in tipo or "-0.10 px" in tipo, \
        "cap-height kaybı (−0,10px) DESIGN.md'de yazılı değil — dürüst muhasebe eksik"


def test_RAMP_RULE_dokuz_basamak_KORUNDU():
    """Rampanın dokuz basamağı bu turda DEĞİŞMEDİ. Yazı tipi değişti, ölçek değişmedi."""
    metin = DESIGN.read_text(encoding="utf-8")
    basamaklar = [int(m) for m in re.findall(r"\|\s*`font-size:\s*(\d+)px`", metin)]
    assert basamaklar == [10, 11, 12, 13, 14, 17, 20, 24, 28], f"rampa tablosu: {basamaklar}"
    kural = re.search(r"\*\*The Ramp Rule\.\*\*(.{0,220})", metin, re.S)
    assert kural and "10 · 11 · 12 · 13 · 14 · 17 · 20 · 24 · 28" in kural.group(1), \
        "The Ramp Rule metni değişmiş"


def test_TABULAR_RULE_korundu_ve_slashed_zero_YASAGI_gerekcesiyle_tasindi():
    """"The Tabular Rule" ve `slashed-zero` yasağı KALIR — gerekçesi Recursive'e taşınmış olarak.

    Yasak Geist'te "özellik yok" diye konmuştu. Recursive'de özellik VAR ama ATIL
    (`zero → zero.slash` eşliyor, iki glifin konturu aynı). Yani tuzak biçim değiştirdi, hüküm
    değişmedi — ve belgede hükmün YENİ gerekçesi duruyor olmalı, yoksa bir sonraki tur
    "özellik var, açalım" der."""
    metin = DESIGN.read_text(encoding="utf-8")
    kural = re.search(r"\*\*The Tabular Rule\.\*\*(.{0,700})", metin, re.S)
    assert kural, "The Tabular Rule kaybolmuş"
    govde = kural.group(1)
    assert "Recursive Mono" in govde, "Tabular Rule hâlâ eski yazı tipini adlandırıyor"
    assert "tabular-nums" in govde and "slashed-zero" in govde, "kuralın iki kalemi eksik"

    tipo = metin.split("## Typography", 1)[1].split("\n## ", 1)[0]
    assert "inert" in tipo.lower(), "`zero` özelliğinin ATIL olduğu kayda geçmemiş"


# ===================== Ç6 · SUNUM KAPISI (DEVREDİLEN KALEM) =====================

@pytest.mark.xfail(strict=True, reason=(
    "DEVREDİLEN, BİLİNEN AÇIK — ve VARSAYIM DEĞİL, ÖLÇÜLDÜ. TestClient ile gerçek istek "
    "atıldı (2026-08-07): `/fonts/recursive-sans-vf.woff2` → **404**, "
    "`/fonts/recursive-mono-vf.woff2` → **404**, karşılaştırma için `/theme.js` → 200. "
    "Sebep: depoda `StaticFiles` montajı BİLEREK yok (api.py:469 — montaj, WEB dizinine düşen "
    "her taslağı yayına açar), statik varlıklar AD AD yönlendirilir ve `/fonts` için böyle bir "
    "rota yazılmamış. Yani dosyayı meridian/web/fonts/ altına koymak TEK BAŞINA yetmez; rota "
    "eklenene kadar üç yüzey de sistem yüzüne düşer. `meridian/api.py` bu turun yazma sınırının "
    "DIŞINDA (brief: `meridian/*.py` YASAK), o yüzden burada ÇİVİLENİYOR, sessizce "
    "geçilmiyor. STRICT: rota eklendiği an XPASS ile kırılır ve bu bloğun gerçek bir teste "
    "dönüştürülmesini zorlar."))
def test_api_py_fonts_rotasi_TANIMLI():
    """Font dosyalarının bir SUNUM YOLU olmalı — `@font-face` yolu tek başına bir vaat değil."""
    api = (KOK / "meridian" / "api.py").read_text(encoding="utf-8")
    assert re.search(r'@app\.get\(\s*["\']/fonts/', api), (
        "api.py'de /fonts rotası yok. Önerilen biçim (depo sözleşmesine uygun, montaj YOK):\n"
        '    @app.get("/fonts/{ad}")\n'
        "    def fontlar(request: Request, ad: str):\n"
        '        if ad not in {"recursive-sans-vf.woff2", "recursive-mono-vf.woff2"}:\n'
        '            return JSONResponse({"error": "not_found"}, status_code=404)\n'
        '        return _statik(request, f"fonts/{ad}", "font/woff2")')

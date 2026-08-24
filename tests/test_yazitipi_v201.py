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

Ağ istemez, tarayıcı istemez, fontTools istemez. Neredeyse hepsi diskten okunur; TEK istisna
Ç6'daki sunum kapısıdır — o blok `TestClient` ile SÜREÇ-İÇİ (ASGI) gerçek istek atar, çünkü
"rota yazılmış" ile "doğru baytlar geliyor" iki ayrı iddiadır ve ilki ikincisini kanıtlamaz.
Süreç-içi istek hâlâ ağ değildir: sokete çıkmaz, dış bağımlılığı yoktur.
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
TARAYICI = OLCUM / "tarayici"
# 2026-08-24 · YAZI TİPİ DEVRALMA (docs/HUKUM-2026-08-24-YAZITIPI.md).
# `--sans` Inter oldu, `--mono` Recursive Mono KALDI. İki tur, iki kayıt:
#   08-07 turu → Recursive Mono'yu üretti ve HÂLÂ dağıtılan mono kesidin kaydıdır.
#   08-24 turu → Inter kesidini üretti; kaydı `yuzler[]` sarmalayıcısı taşır (iki kaynak
#                dosya, kaynak-başına cmap — bkz. o dosyanın `sema_notu`su).
# İkisi BİRLEŞTİRİLMEZ: her kesit KENDİ turunun kaydına aittir ve bir kaydı ötekine
# taşımak, hangi kesidin hangi düzenekle ölçüldüğünü silerdi. `build_kaydi` fixture'ı
# ikisini OKUR ve dağıtılan iki dosyanın kaydını tek sözlükte sunar.
OLCUM_2408 = KOK / "research" / "olcumler" / "yazi_tipi_2026-08-24"
# ÜÇÜNCÜ TUR (takip): 08-24 turu bir AÇIK KALEM bırakmıştı — dağıtım kesidi Inter'in
# `ss02`/`cv01` Il1-ayrım özelliklerini buduyordu. Bu tur kesidi onları KORUYARAK yeniden
# aldı ve AYNI düzenekle ölçtü; dağıtılan sans kesidinin kaydı ARTIK BURADADIR.
# 08-24 turunun kaydı DONMUŞ KANITTIR ve değişmedi — Geist reddi ve kalibrasyon oradan okunur.
OLCUM_SS02 = KOK / "research" / "olcumler" / "kesit_ss02cv01_2026-08-24"
BUILD_JSON = OLCUM / "web_fonts_build.json"
BUILD_JSON_2408 = OLCUM_2408 / "web_fonts_build.json"
BUILD_JSON_SANS = OLCUM_SS02 / "web_fonts_build.json"
TARAYICI_2408 = OLCUM_2408 / "tarayici"

# Yazı tipi taşıyan üç yüzey. `runbook.html` BİLEREK DIŞARIDA: o sayfa D2-b'de yönlendirmeye
# çevrildi, D5'te silinecek ve zaten hiç dış font yüklemiyor (kendi `ui-sans-serif` yığınıyla
# çalışır — "ağ yokken de açılır" onun kendi sözleşmesi). Kapsam dışı olduğu BURADA yazılı ki
# "unutuldu mu" sorusu bir daha sorulmasın.
YUZEYLER = ["index.html", "landing.html", "workflow.html"]
# CDN taraması TÜM yüzeyleri kapsar — runbook dahil, çünkü oraya bir CDN linki sızarsa
# CSP daraltması onu da vurur.
TUM_YUZEYLER = YUZEYLER + ["runbook.html", "app.js", "theme.js", "landing.js",
                           "workflow.js", "palette.js"]

SANS_DOSYA = "inter-vf.woff2"
MONO_DOSYA = "recursive-mono-vf.woff2"
SANS_AILE = "Inter"
MONO_AILE = "Recursive Mono"
# EMEKLİ AMA SİLİNMEZ: `recursive-sans-vf.woff2` dağıtımda KALIR (tarihçe-koru + eski
# önbelleklerin 404 görmemesi) ve `api.py::_FONT_DOSYALARI` onu sunmayı sürdürür. Hiçbir
# yüzey onu ARTIK İSTEMEZ; bunu `test_EMEKLI_sans_kesidi_HICBIR_YUZEYDE_istenmiyor` ölçer.
EMEKLI_SANS_DOSYA = "recursive-sans-vf.woff2"

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
    """DAĞITILAN iki kesidin üretim kaydı — her biri KENDİ turundan okunur.

    Kayıtsız bir font, "hangi kaynaktan, hangi eksen aralığıyla, hangi özellik kümesiyle"
    sorularının cevabı olmayan bir ikilidir. İki tur olduğu için iki kayıt var ve
    birleştirilmiyorlar; burada yalnız DAĞITILAN dosyaların satırları tek sözlükte
    toplanıyor. Kaynağı da taşınıyor (`_tur`) ki bir sayı tartışıldığında hangi düzeneğe
    ait olduğu belirsiz kalmasın."""
    for yol in (BUILD_JSON, BUILD_JSON_2408):
        assert yol.is_file(), (
            f"{yol} YOK. Fontlar kayıtsız üretilmiş demektir. "
            f"Çözüm: ilgili turun kesit üretici betiğini koş.")
    for yol in (BUILD_JSON_SANS,):
        assert yol.is_file(), f"{yol} YOK — dağıtılan sans kesidinin kaydı kayıp."
    eski = json.loads(BUILD_JSON.read_text(encoding="utf-8"))
    yeni = json.loads(BUILD_JSON_2408.read_text(encoding="utf-8"))
    sans_kaydi = json.loads(BUILD_JSON_SANS.read_text(encoding="utf-8"))
    kesitler = []
    for k in eski["kesitler"]:
        if k["dosya"] == MONO_DOSYA:
            kesitler.append({**k, "_tur": "2026-08-07"})
    for k in sans_kaydi["kesitler"]:
        if k["dosya"] == SANS_DOSYA:
            kesitler.append({**k, "_tur": "kesit_ss02cv01_2026-08-24",
                             "_yalin_ozellikler": sans_kaydi["yalin_ozellikler"],
                             "_sabitlenen_eksenler": sans_kaydi["sabitlenen_eksenler"],
                             "_wght_aralik": sans_kaydi["wght_aralik"]})
    return {"kesitler": kesitler,
            "toplam_bayt": sum(k["bayt"] for k in kesitler),
            "_eski": eski, "_yeni": yeni, "_sans": sans_kaydi}


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
    assert any(SANS_AILE in a for a in aileler), f"{ad}: {SANS_AILE!r} @font-face yok"
    assert any(MONO_AILE in a for a in aileler), f"{ad}: {MONO_AILE!r} @font-face yok"

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
def test_jetonlar_DAGITILAN_YUZLERE_bagli_ve_yedekler_KORUNDU(ad):
    """`--sans` Inter'e, `--mono` Recursive Mono'ya bağlı; sistem yedekleri KALDI.

    ESKİ ADI: test_jetonlar_RECURSIVE_ve_yedekler_KORUNDU (2026-08-07 → 2026-08-24). Ad,
    `--sans` Inter'e geçince gerçeğe uyduruldu — yanlış bir ad, kapsamı okumadan varsayan
    bir okuyucu üretir. İKİ AİLE TAŞIMAK BİLİNÇLİDİR ve ölçülmüştür: sans tarafında Inter,
    mono tarafında Recursive kazandı (docs/HUKUM-2026-08-24-YAZITIPI.md).

    Yedek yığınının kalması şart: `font-display:block` üç saniyelik bir pencere tanır ve o
    pencere dolarsa tarayıcı yedeğe düşer. Yedeksiz bir `--mono`, dosya bir gün gelmediğinde
    rakam sütununu ORANSAL bir yüze düşürür — hizanın sessizce ölmesi."""
    kaynak = _yorumsuz(_oku(ad))
    sans = re.search(r"--sans\s*:\s*([^;]+);", kaynak)
    mono = re.search(r"--mono\s*:\s*([^;]+);", kaynak)
    assert sans and mono, f"{ad}: --sans / --mono jetonu bulunamadı"
    assert sans.group(1).strip().startswith(f"'{SANS_AILE}'"), f"{ad}: --sans → {sans.group(1)!r}"
    assert mono.group(1).strip().startswith(f"'{MONO_AILE}'"), f"{ad}: --mono → {mono.group(1)!r}"
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

    assert sans["nameID1"] == SANS_AILE, f"sans aile adı: {sans['nameID1']!r}"
    assert mono["nameID1"] == MONO_AILE, f"mono aile adı: {mono['nameID1']!r}"
    assert sans["nameID1"] != mono["nameID1"], "iki kesit AYNI aile adını taşıyor — çakışma geri gelmiş"
    assert sans["nameID6"] != mono["nameID6"], (
        f"postscript adları çakışık: {sans['nameID6']!r} == {mono['nameID6']!r}")
    for x in (sans, mono):
        assert x["nameID16"] is None, (
            f"{x['dosya']}: nameID 16 = {x['nameID16']!r}. Typographic family kaydı iki kesiti "
            f"tek ailede yeniden birleştirir — silinmiş olmalı.")


def test_rakamlar_MONODA_YAPISAL_SANSTA_TNUM_ile_hizali(build_kaydi):
    """"The Tabular Rule"un dayanağı — ve 2026-08-24'te DEĞİŞEN yarısı.

    ESKİ ADI: test_rakamlar_YAPISAL_tabular_HER_IKI_KESITTE. Ad, hüküm değiştiği için
    değişti ve BU BİR GERİLEMEDİR — beyanlı olarak kaydediliyor:

      MONO (Recursive Mono) — DEĞİŞMEDİ. Rakam advance kümesi tek değerdir (600/1000 upem),
        yani hizalama YAPISALdır: hiçbir bildirime bağlı değil, `tnum` düşse bile durur.
        Panonun HER SAYISI bu yüzde çizilir, o yüzden asıl garanti burada.

      SANS (Inter) — ARTIK YAPISAL DEĞİL. Inter'in varsayılan rakamları ORANSALdır
        (ölçüldü: dokuz farklı advance, 833..1323 / 2048 upem) ve hizalama `tnum`
        BİLDİRİMİNE bağlıdır. Kesit `tnum`u TAŞIYOR (kayıt: `_yalin_ozellikler`) ve
        tarayıcıda uygulandığı DOĞRULANDI (08-24 turu, `tabular` bölümü:
        `tnum_acik_tekduze = True`, tek genişlik 64.844).

    BEDELİ: sans'ta rakam hizası bir CSS bildirimine bağlı hâle geldi. Bu, 2026-08-07'de
    Geist'ten kaçınma gerekçelerinden biriydi ve şimdi sans tarafında geri geldi. Kabul
    edilme sebebi ölçülmüştür (Inter her okunaklılık ölçütünde Recursive Sans'ı geçiyor) ve
    RİSKİ SINIRLIDIR: sayılar `--mono` ile çizilir. Aşağıdaki ikinci assert o sınırı çiviler
    — sans'ta rakam basan her kural `tabular-nums` bildirmek ZORUNDA."""
    k = {x["dosya"]: x for x in build_kaydi["kesitler"]}
    assert k[MONO_DOSYA]["rakam_advance"] == [600], (
        f"mono rakam advance kümesi {k[MONO_DOSYA]['rakam_advance']} — tek değer (600) "
        f"bekleniyordu; panonun sayı hizası artık YAPISAL DEĞİL.")
    sans = k[SANS_DOSYA]
    assert len(sans["rakam_advance"]) > 1, (
        "sans rakamları yapısal tabular ÇIKTI — bu bir iyileşme, ama kayıt ve bu testin "
        "gerekçesi bayatladı: hükmü güncelle.")
    assert "tnum" in sans["_yalin_ozellikler"], (
        f"sans kesidi `tnum` TAŞIMIYOR ({sans['_yalin_ozellikler']}) — rakamları oransal ve "
        f"telafisi yok; sans'ta basılan her sayı sütunu kayar.")


def test_SANSTA_basilan_her_SAYI_tabular_nums_bildiriyor():
    """Sans artık yapısal tabular DEĞİL: hizayı taşıyan tek şey `font-variant-numeric`.

    Bu test o bildirimin gerçekten YERİNDE olduğunu ölçer. Ölçüt kural gövdesidir: `--sans`
    ile çizilen ve `tabular-nums` demeyen bir sayı kuralı, Inter'de sütunu kaydırır — ve
    kayma sessizdir (hiçbir test rengi/boyu bozulmaz, yalnız rakamlar oynar)."""
    kaynak = _yorumsuz(_oku("index.html"))
    stil = kaynak[kaynak.index("<style>"):kaynak.rindex("</style>")]
    ihlal = []
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", stil):
        sec, govde = m.group(1).strip().splitlines()[-1].strip(), m.group(2)
        if sec.startswith(":root") or "var(--sans)" not in govde:
            continue
        if "tabular-nums" in govde or "font-variant-numeric" in govde:
            continue
        # Sayı basmayan sans kuralları serbest — ölçüt "rakam sözleşmesi taşıyor mu".
        if not re.search(r"tabular|--t-num|mono-num|\bnum\b", govde + sec):
            continue
        ihlal.append(sec)
    assert not ihlal, (
        f"`--sans` ile sayı basan ama `tabular-nums` bildirmeyen kural: {ihlal}. "
        f"Inter'in rakamları ORANSALdır; hizayı yalnız bu bildirim taşır.")


def test_agirlik_ekseni_400_700_ve_varsayilan_400(build_kaydi):
    """`wght` ekseni 400-700, VARSAYILAN 400.

    Varsayılan kalemi bir tuzağı kapatıyor: Recursive'in kendi `wght` varsayılanı **300**'dür
    (ölçüm raporu §7/5 bunu açık kalem olarak devretmişti). 400 tabanlı bir eksende `@font-face`
    bildirimi bir gün düşse bile yüz İNCE açılmaz."""
    assert build_kaydi["_eski"]["wght_aralik"] == [400, 700], "mono turu (08-07) kaydı"
    for x in build_kaydi["kesitler"]:
        if x["_tur"].startswith("kesit_ss02cv01"):
            assert x["_wght_aralik"] == [400, 700], f"{x['dosya']}: {x['_wght_aralik']}"
        assert x["fvar"]["wght"] == [400.0, 400.0, 700.0], f"{x['dosya']}: fvar {x['fvar']}"
        assert x["usWeightClass"] == 400, f"{x['dosya']}: usWeightClass {x['usWeightClass']}"


def test_TURKCE_glif_civisi(build_kaydi):
    """On iki Türkçe karakterin HİÇBİRİ subset dışında kalmamış olmalı.

    Bu bir "muhtemelen vardır" testi değil: `build_web_fonts.py` istenen ama fontta BULUNAMAYAN
    her kod noktasını `fontta_yok` listesine yazar (uydurma yasağı — "hepsi var" demek yerine
    olmayanları sayar). Türkçe'den bir harf o listeye düşerse pano `ÖLÇÜLEMEDİ`yi tofu ile
    yazar."""
    yok = set(build_kaydi["_eski"]["fontta_yok"])
    for y in build_kaydi["_yeni"]["yuzler"]:
        if "Inter" in y["kaynak"]:
            yok |= set(y["fontta_yok"])
    eksik = {f"U+{cp:04X}": ch for cp, ch in TURKCE.items() if f"U+{cp:04X}" in yok}
    assert not eksik, f"Türkçe karakter subset dışında kalmış: {eksik}"
    # 08-24 turunun üreticisi her kesit için AYRICA sayıyor (08-07'de o alan yoktu).
    # Alanın YOKLUĞU bir geçiş değil bir BULGU: hangi kaydın hangi şemayı taşıdığı burada
    # görünür kalsın diye `_tur` ile ayrılıyor, sessizce `get(...)` ile yutulmuyor.
    for x in build_kaydi["kesitler"]:
        if x["_tur"].startswith("kesit_ss02cv01"):
            assert x["turkce_kesitte_eksik"] == [], \
                f"{x['dosya']}: kesitte eksik Türkçe glif {x['turkce_kesitte_eksik']}"
        else:
            assert "turkce_kesitte_eksik" not in x, (
                f"{x['dosya']}: 08-07 kaydı bu alanı KAZANMIŞ — kayıt elle düzenlenmiş "
                f"olabilir; o dosya DONMUŞ KANITTIR ve değişmemeliydi.")
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


def test_OFL_lisansi_HER_IKI_AILE_ICIN_FONTLARLA_BIRLIKTE_dagitiliyor():
    """OFL 1.1 §2, telif + izin bildiriminin ikili ile BİRLİKTE taşınmasını şart koşar —
    ve 2026-08-24'ten beri dağıtılan İKİ AYRI AİLE var.

    ESKİ ADI: test_OFL_lisansi_FONTLARLA_BIRLIKTE_dagitiliyor. Tek aile varken tek bildirim
    yeterliydi; Inter geldiğinde o test YEŞİL KALIRDI ve Inter lisanssız dağıtılırdı — yani
    kapsam boşluğu, ihlali sessiz kılan şeyin ta kendisi olurdu. Kapsam artık DAĞITILAN
    DOSYALARDAN türetilir, elle sayılmaz.

    İki bildirim TEK dosyada duruyor (bölüm A / bölüm B) çünkü ikisi de OFL 1.1; ayrı dosya
    da meşru olurdu, ama tek dosya `api.py`nin rota yüzeyini genişletmiyor."""
    p = FONTLAR / "OFL.txt"
    assert p.is_file(), (
        "meridian/web/fonts/OFL.txt YOK. SIL OFL 1.1 telif + izin bildiriminin kopyalarla "
        "birlikte taşınmasını şart koşar; font dosyalarını lisanssız dağıtmak ihlaldir.")
    metin = p.read_text(encoding="utf-8")
    assert "SIL OPEN FONT LICENSE Version 1.1" in metin, "lisans metni yok"
    # HER DAĞITILAN AİLE için bir telif kaydı. Kapsam diskten okunur.
    TELIF = {"Inter": "The Inter Project Authors",
             "Recursive": "The Recursive Project Authors"}
    dagitilan = sorted(x.name for x in FONTLAR.glob("*.woff2"))
    aileler = {"Inter" if a.startswith("inter") else "Recursive" for a in dagitilan}
    assert aileler == set(TELIF), (
        f"dağıtılan aileler {sorted(aileler)} ile lisans kapsamı {sorted(TELIF)} ayrışmış — "
        f"yeni bir aile eklendiyse bildirimi de eklenmeli (diskte: {dagitilan})")
    for aile in aileler:
        assert TELIF[aile] in metin, (
            f"{aile} dağıtılıyor ama OFL.txt'te telif sahibi kaydı YOK ({TELIF[aile]!r}). "
            f"Lisanssız dağıtım OFL 1.1 §2 ihlalidir.")
    # OFL §3 / RFN: rezerve font adı durumu kayda geçmeli — İKİSİ için de.
    assert "Reserved Font Name" in metin, (
        "Rezerve Font Adı durumu kayda geçmemiş. Ne Recursive'in ne Inter'in telif kaydında "
        "RFN VARDIR (ölçüldü) — kesitlerin kendi adlarını koruması bu yüzden serbest; bu "
        "tespit dosyada durmazsa bir sonraki tur onu yeniden ölçmek zorunda kalır.")


def test_EMEKLI_sans_kesidi_HICBIR_YUZEYDE_istenmiyor():
    """`recursive-sans-vf.woff2` DAĞITIMDA kalır ama hiçbir yüzey onu İSTEMEZ.

    İki ayrı iddia ve ikisi de ayrı ayrı ölçülür: (a) dosya duruyor — silmek, eski
    önbelleklerden gelen istekleri 404'e düşürür ve tarihçe-koru ilkesini çiğner;
    (b) hiçbir `@font-face` / `preload` / jeton onu artık istemiyor — istiyorsa tarayıcı
    41 KB'ı BOŞUNA indirir ve `font-display:block` penceresini uzatır."""
    p = FONTLAR / EMEKLI_SANS_DOSYA
    assert p.is_file(), (
        f"{EMEKLI_SANS_DOSYA} SİLİNMİŞ. Emekli edildi ama dağıtımda KALIR (tarihçe-koru + "
        f"eski önbelleklerin 404 görmemesi) — `api.py::_FONT_DOSYALARI` onu hâlâ sunuyor.")
    isteyen = [ad for ad in TUM_YUZEYLER
               if EMEKLI_SANS_DOSYA in _yorumsuz(_oku(ad))]
    assert not isteyen, (
        f"emekli sans kesidi hâlâ isteniyor: {isteyen}. Dosya sunulmaya devam eder ama "
        f"hiçbir yüzey onu YÜKLEMEMELİ — boşuna indirilen 41 KB, block penceresini uzatır.")


def test_INTER_sansta_RECURSIVEI_gectigi_TARAYICIDA_olculdu():
    """Sans devralmasının GEREKÇESİ — bir tercih değil bir ölçüm (karar §9.5'in font hattı).

    2026-08-24 turu 2026-08-07 düzeneğini yeniden koştu ve DONMUŞ TABANI BİREBİR ÜRETTİ;
    kalibrasyon tutmasaydı bu sayılar kıyaslanamazdı ve devralma dayanaksız kalırdı. O
    yüzden bu test önce kalibrasyonu, sonra üstünlüğü çakar.

    Ölçüt MÜREKKEPTİR (alfa farkı), advance değil: oransal bir yüzde advance farkı `1` ile
    `l`yi ayırt etmez, yalnız kutu genişliğini söyler."""
    yeni = json.loads((TARAYICI_2408 / "olcum_sonucu.json").read_text(encoding="utf-8"))
    kal = yeni["KALIBRASYON_HUKMU"]
    for alan in ("geist_mono_0807_1l_10px", "geist_mono_0807_1l_28px"):
        beklenen, olculen = kal[alan]
        assert beklenen == olculen, (
            f"kalibrasyon TUTMADI ({alan}: taban {beklenen}, bu tur {olculen}) — düzenek "
            f"08-07'nin sayılarını yeniden üretmiyorsa kıyas ÖLÜR ve devralma dayanaksızdır.")

    inter = _satir(yeni, "INTER kesit")
    rec = _satir(json.loads((TARAYICI / "olcum_sonucu.json").read_text(encoding="utf-8")),
                 "YENI Sans")
    # `1`/`l` ve `0`/`O`, dpr=1 @28px — hükmün alıntıladığı iki sayı çifti.
    # ALAN ADLARI İKİ TURDA FARKLI ve bu bir tuzak: 08-24 turu dpr'ı ADA yazdı
    # (`raster_1_l_dpr1`), 08-07 turu yazmadı (`raster_1_l`) çünkü o turda tek dpr vardı.
    # `.get(a, b)` ile sessizce yutmak, yanlış dpr'ı doğru sanmak olurdu — ikisi ADIYLA
    # ayrılıyor ve eksikse test PATLIYOR.
    assert "raster_1_l_dpr1" in inter and "raster_1_l" in rec, (
        "tarayıcı kayıtlarının şeması beklenenden farklı — hangi dpr'ın okunduğu belirsiz")
    i_1l = inter["raster_1_l_dpr1"]["28px"]["fark_orani"]
    r_1l = rec["raster_1_l"]["28px"]["fark_orani"]
    i_0O = inter["raster_0_O_dpr1"]["28px"]["fark_orani"]
    r_0O = rec["raster_0_O"]["28px"]["fark_orani"]
    assert (i_1l, r_1l) == (0.968, 0.931), f"kayıt kaymış: 1/l {i_1l} vs {r_1l}"
    assert (i_0O, r_0O) == (0.774, 0.663), f"kayıt kaymış: 0/O {i_0O} vs {r_0O}"
    assert i_1l > r_1l and i_0O > r_0O, (
        "Inter artık Recursive Sans'ı GEÇMİYOR — devralmanın tek gerekçesi buydu; "
        "hüküm yeniden açılmalı (docs/HUKUM-2026-08-24-YAZITIPI.md).")


def test_MONONUN_KALMASI_da_olculdu_Geist_ALINMADI():
    """Devralma TEK YÖNLÜ DEĞİL: mono tarafında Recursive kazandı ve o yüzden KALDI.

    Bu testin işi bir simetri süsü değil: bir sonraki tur "sans Inter oldu, mono da Geist
    olsun, tek aile tutarlılığı" diyebilir. O öneri ÖLÇÜLDÜ ve reddedildi — sayılar burada
    dursun ki yeniden ölçülmeden geri gelmesin."""
    yeni = json.loads((TARAYICI_2408 / "olcum_sonucu.json").read_text(encoding="utf-8"))
    taban = yeni["donmus_taban"]
    rec, geist = taban["recursive_mono_1l_28px"], taban["geist_mono_1l_28px"]
    assert rec == 0.817 and geist == 0.57, f"taban kaymış: recursive {rec} · geist {geist}"
    assert rec > geist, "Geist Mono artık daha iyi — mono hükmü yeniden açılmalı"
    # Ve Geist'in kesidinde ₺ ile ✓ YOKTU: pano işaretleri yedek yüze düşerdi.
    kayit = json.loads(BUILD_JSON_2408.read_text(encoding="utf-8"))
    geist_yuz = [y for y in kayit["yuzler"] if "Geist" in y["kaynak"]][0]
    yok = set(geist_yuz["fontta_yok"])
    assert {"U+20BA", "U+2713"} & yok, (
        "Geist Mono kesidinde ₺/✓ eksikliği kayıttan kaybolmuş — reddin ikinci gerekçesi bu.")


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

    mono = _satir(tarayici_olcumu, "YENI Mono")
    assert mono["i_genislik"] == mono["M_genislik"], f"mono: i={mono['i_genislik']} M={mono['M_genislik']}"
    # SANS YARISI KENDİ TURUNDAN OKUNUR (2026-08-24). 08-07 kaydındaki "YENI Sans" artık
    # DAĞITILMAYAN yüzdür (Recursive Sans, emekli); onu ölçmeye devam etmek, gemide olmayan
    # bir dosya hakkında yeşil vermek olurdu — bu dosyanın kovaladığı kusur sınıfının ta
    # kendisi. Yukarıdaki `hukum` alanları da o turun mono yarısına aittir ve orada kalır.
    yeni = json.loads((TARAYICI_2408 / "olcum_sonucu.json").read_text(encoding="utf-8"))
    sans = _satir(yeni, "INTER kesit")
    assert sans["monospace"] is False, "sans yüz monospace ÇIKTI — mono dosya sans yerine geçmiş"
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

def test_DESIGN_md_tipografi_DAGITILAN_YUZLERI_diyor():
    """Ön-madde jetonları ve Typography bölümü aynı yazı tiplerini söylemeli.

    ESKİ ADI: test_DESIGN_md_tipografi_RECURSIVE_diyor (2026-08-07 → 2026-08-24).

    DESIGN.md iki yerde tipografi beyan eder: dosyanın başındaki makine-okunur `typography:`
    bloğu ve `## Typography` bölümü. Biri güncellenip öteki bırakılırsa belge kendi kendisiyle
    çelişir — ve bu deponun kayıtlı kusur sınıfı tam olarak budur."""
    metin = DESIGN.read_text(encoding="utf-8")
    on_madde = metin.split("---", 2)[1]
    assert f"'{SANS_AILE}'" in on_madde, \
        f"DESIGN.md ön-madde `typography:` bloğu {SANS_AILE!r} bildirmiyor — belge kendi " \
        f"makine-okunur yarısıyla çelişiyor"
    assert "Recursive Sans" not in on_madde, \
        "DESIGN.md ön-maddesi EMEKLİ sans yüzünü bildiriyor"
    assert "Geist" not in on_madde, "DESIGN.md ön-maddesinde Geist kalmış"

    tipo = metin.split("## Typography", 1)[1].split("\n## ", 1)[0]
    # İKİ AİLE, İKİ GEREKÇE — ve mono'nun NEDEN kaldığı da yazılı olmalı: bir sonraki tur
    # "tutarlılık için ikisini de değiştirelim" demesin diye ölçüm belgede durur.
    for beklenen in ("Inter", "Recursive Mono Linear", "0.968", "0.931", "0.774", "0.663",
                     "0.570", "ss02"):
        assert beklenen in tipo, f"DESIGN.md § Typography'de {beklenen!r} geçmiyor"
    # KAYIP KALEMİ DÜRÜSTÇE YAZILMIŞ OLMALI — kazanç tablosu tek başına bir satış metnidir.
    assert "−0.10 px" in tipo or "-0.10 px" in tipo, \
        "cap-height kaybı (−0,10px) DESIGN.md'de yazılı değil — dürüst muhasebe eksik"


def test_RAMP_RULE_dokuz_basamak_KORUNDU():
    """Rampanın dokuz basamağı bu turda DEĞİŞMEDİ. Yazı tipi değişti, ölçek değişmedi."""
    metin = DESIGN.read_text(encoding="utf-8")
    basamaklar = [int(m) for m in re.findall(r"\|\s*`font-size:\s*(\d+)px`", metin)]
    # 2026-08-24 · rampa DEĞİŞTİ (13 çıktı, 30 girdi) ve DOKUZ BASAMAK KORUNDU. Ölçüm ve
    # gerekçe: docs/kontrast-denetimi.md §12.3 + DESIGN.md § Type scale.
    # ~~Emekli: [10, 11, 12, 13, 14, 17, 20, 24, 28]~~
    assert basamaklar == [10, 11, 12, 14, 17, 20, 24, 28, 30], f"rampa tablosu: {basamaklar}"
    kural = re.search(r"\*\*The Ramp Rule\.\*\*(.{0,220})", metin, re.S)
    assert kural and "10 · 11 · 12 · 14 · 17 · 20 · 24 · 28 · 30" in kural.group(1), \
        "The Ramp Rule metni tablodan AYRIŞMIŞ — belge kendi kendisiyle çelişiyor"


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
    # 2026-08-24: sans yarısı YAPISAL OLMAKTAN ÇIKTI ve bu bir GERİLEMEDİR. Belge onu
    # gerileme olarak yazmak zorunda — "değişti" demek yeterli değil, çünkü aynı kusur
    # 2026-08-07'de Geist'i REDDETME gerekçesiydi ve sans tarafında geri geldi.
    assert "regression" in govde.lower(), \
        "Tabular Rule'un sans yarısındaki gerileme DÜRÜSTÇE yazılmamış"
    assert "proportional" in govde.lower(), \
        "Inter rakamlarının oransal olduğu belgede yazılı değil"
    assert "tabular-nums" in govde and "slashed-zero" in govde, "kuralın iki kalemi eksik"

    tipo = metin.split("## Typography", 1)[1].split("\n## ", 1)[0]
    assert "inert" in tipo.lower(), "`zero` özelliğinin ATIL olduğu kayda geçmemiş"


# ===================== Ç6 · SUNUM KAPISI (KAPANDI — D5, 2026-08-07) =====================
#
# BU BLOK BİR TUR BOYUNCA `xfail(strict=True)` İDİ ve gerekçesi buydu: `/fonts/*.woff2` ölçülerek
# 404 dönüyordu (karşılaştırma için `/theme.js` → 200), çünkü depoda `StaticFiles` montajı BİLEREK
# yok ve `/fonts` için ad-ad bir rota yazılmamıştı; `meridian/api.py` de o turun yazma sınırının
# DIŞINDAYDI. KATI olması bilinçliydi: rota eklendiği an XPASS ile kırılıp bu bloğun gerçek bir
# teste dönüştürülmesini zorlasın diye. Rota D5'te eklendi (`meridian/api.py`, `/fonts/{ad}` +
# literal izin listesi) ve blok aşağıda gerçek teste dönüştürüldü. Devir kaydı burada duruyor ki
# "bu neden bir xfail'di" sorusu tarihe değil, kayda sorulsun.
#
# İŞ BÖLÜMÜ: rotanın KENDİ sözleşmesi (izin listesi, dizin-dışı erişim, ETag/304, önbellek yasası)
# `tests/test_font_rotasi_v202.py`de ölçülür. Burada YALNIZ tipografi sözleşmesinin kendi sorusu
# var: bu yüzeylerin İSTEDİĞİ yüz gerçekten geliyor mu.

def test_api_py_fonts_rotasi_TANIMLI():
    """Font dosyalarının bir SUNUM YOLU olmalı — `@font-face` yolu tek başına bir vaat değil."""
    api = (KOK / "meridian" / "api.py").read_text(encoding="utf-8")
    assert re.search(r'@app\.get\(\s*["\']/fonts/', api), (
        "api.py'de /fonts rotası yok. Biçim (depo sözleşmesine uygun, montaj YOK):\n"
        '    @app.get("/fonts/{ad}")\n'
        "    def fontlar(request: Request, ad: str):\n"
        '        if ad not in {"recursive-sans-vf.woff2", "recursive-mono-vf.woff2"}:\n'
        '            return JSONResponse({"error": "not_found"}, status_code=404)\n'
        '        return _statik(request, f"fonts/{ad}", "font/woff2")')


def test_IKI_KESIT_de_GERCEKTEN_sunuluyor(sandbox_state):
    """Rotanın VARLIĞI değil, ÇALIŞTIĞI ölçülür — TestClient ile gerçek istek.

    Yukarıdaki test kaynağa bakar ve bir rotanın YAZILDIĞINI söyler. Yazılmış bir rota yanlış
    yola bağlanmış, yanlış dosyayı okuyor ya da izin listesi yüzünden kendi dosyalarını
    reddediyor olabilir — üçü de kaynakta "rota var" diye okunur. Bu turun kapattığı açığın
    ölçüsü 200'dür, `@app.get` dizesi değil.

    `sandbox_state` ZORUNLU: `TestClient(app)` uygulamayı ayağa kaldırır ve açılış yolu canlı
    `state/events.jsonl`e yazar."""
    from fastapi.testclient import TestClient

    from meridian.api import app
    with TestClient(app) as c:
        for dosya in (SANS_DOSYA, MONO_DOSYA):
            r = c.get(f"/fonts/{dosya}")
            assert r.status_code == 200, (
                f"/fonts/{dosya} → {r.status_code}. Yazı tipi kendi-barındırılıyor ve CSP "
                f"`font-src 'self'`; bu yol 200 dönmezse üç yüzey de sistem yüzüne düşer.")
            assert r.headers.get("content-type", "").split(";")[0] == "font/woff2"
            assert r.content == (FONTLAR / dosya).read_bytes(), \
                f"/fonts/{dosya}: sunulan baytlar diskteki dosya DEĞİL"

        # DİZİN-DIŞI ERİŞİM — burada YALNIZ sınıfın kapalı olduğu gösterilir; biçim biçim
        # matrisi (kodlanmış ayraç, boş bayt, harf duyarlılığı, yönlendirme hedefi)
        # tests/test_font_rotasi_v202.py'de. `OFL.txt` seçildi çünkü o dosya AYNI DİZİNDE
        # GERÇEKTEN VAR ve okunabilir: "diskte var" ile "yayında" arasındaki farkın canlı örneği.
        assert (FONTLAR / "OFL.txt").is_file(), "OFL.txt yok — bu iddia bir şey ölçmüyor"
        for kacak in ("OFL.txt", "../api.py", "..%2f..%2fapi.py"):
            assert c.get(f"/fonts/{kacak}", follow_redirects=False).status_code != 200, (
                f"/fonts/{kacak} sunuldu. Rota izin listesiyle çalışmalı: montaj YOK, yani "
                f"dizindeki her bayt yayında DEĞİL.")


# ===================== Ç7 · RAMPA İSTİSNASI (clamp) — D5, 2026-08-07 =====================
#
# NİYE VAR. `landing.html`in yön sözleşmesi bir tur boyunca "her literal font-size rampadadır,
# ARTI clamp() display basamakları" diyordu; `DESIGN.md`in Ramp Rule'u ise "dokuz boy vardır ve
# başka yok" diyordu. İki belge, iki yasa — ve aradaki fark hiçbir yerde YAZILI DEĞİLDİ. Yazılı
# olmayan bir istisna ile bir ihlal ekranda birbirinin aynısıdır: bir sonraki denetim ya çalışan
# tipografiyi siler ya kuralı sessizce genişletir. İstisna D5'te DESIGN.md § Typography'ye açıkça
# yazıldı; bu blok onu üç yerden birden çiviler (belge · yüzeyler · sınır).
#
# ÖLÇÜLDÜ, VARSAYILMADI: bu turda üç yüzeyin TAMAMI tarandı. Rampa dışına düşen HER değer bir
# `clamp()` uç noktasıdır; çıplak (sabit) tek bir rampa-dışı literal YOKTUR.

# 2026-08-24 · DUB DÖNÜŞÜMÜ (KARAR-2026-08-24-B §3): 13px rampadan DÜŞTÜ (ara basamak,
# oranı hiyerarşi değil gürültü üretiyordu — 13→14 = 1.077), 30px EKLENDİ (Dub Analytics'in
# büyük metrik basamağı). Ayrıntı ve ölçüm: tests/test_tipografi_rampa_v209.py + §12.3.
# ~~Emekli: {10, 11, 12, 13, 14, 17, 20, 24, 28}~~
RAMPA = {10, 11, 12, 14, 17, 20, 24, 28, 30}
# `clamp()` alt sınırı için taban. Bugünkü en küçük alt sınır 16px (index.html `.kk-ozet
# .pm-yield`); istisna büyük tipin küçülmesi içindir, rampanın ALTINA inmek için DEĞİL.
CLAMP_TABAN = 16


def _kok_tip(ad: str) -> dict:
    """Yüzeyin KENDİ `:root` bloğundaki tip jetonları. 2026-08-24'te index.html'in rampası
    jetonlandı (`font-size:var(--t-sub)`); aşağıdaki ölçümler BOYUTA bakar, yazılış biçimine
    değil, o yüzden jeton kaynağın kendisinden çözülür — ikinci bir kopya tutulmaz."""
    return dict(re.findall(r"--(t-[a-z0-9-]+|label-size)\s*:\s*(\d+px)", _yorumsuz(_oku(ad))))


def _font_boylari(ad: str) -> list[str]:
    tablo = _kok_tip(ad)
    ham = [v.strip() for v in re.findall(r"font-size\s*:\s*([^;}\n]+)", _yorumsuz(_oku(ad)))]
    return [re.sub(r"var\(\s*--([a-z0-9-]+)\s*\)",
                   lambda m: tablo.get(m.group(1), m.group(0)), v) for v in ham]


def test_tip_jetonu_cozucusu_CALISIYOR():
    """Çözücü sessizce boş dönerse aşağıdaki rampa çivileri hiçbir şey ölçmez: jetonlanmış
    her `font-size` "px içermiyor" diye atlanır ve rampa dışına çıkmak ÜCRETSİZ olur."""
    assert _kok_tip("index.html").get("t-body") == "14px", _kok_tip("index.html")
    boylar = _font_boylari("index.html")
    assert any(b == "14px" for b in boylar), "jetonlanmış gövde boyu çözülmedi"
    assert not [b for b in boylar if "var(--t-" in b], \
        f"çözülmeyen tip jetonu kaldı: {[b for b in boylar if 'var(--t-' in b][:3]}"


def test_DESIGN_md_clamp_ISTISNASINI_ACIKCA_yaziyor():
    """İstisna belgede AÇIK olmalı — örtük bir istisna, kayıtsız bir istisnadır."""
    tipo = DESIGN.read_text(encoding="utf-8").split("## Typography", 1)[1].split("\n## ", 1)[0]
    assert "clamp(" in tipo, (
        "DESIGN.md § Typography `clamp()` istisnasını yazmıyor. Üç yüzey de akışkan display "
        "tipi kullanıyor; belge bunu tanımıyorsa Ramp Rule ile artefakt çelişir.")
    assert re.search(r"Ramp Rule.{0,400}?exception", tipo, re.S | re.I), \
        "istisna Ramp Rule'a BAĞLANMAMIŞ — ayrı duran bir paragraf kuralı düzeltmez"


@pytest.mark.parametrize("ad", YUZEYLER)
def test_rampa_disi_her_boy_YALNIZCA_clamp_icinde(ad):
    """Çıplak rampa-dışı literal YOK. İstisna `clamp()`le sınırlıdır, kuralı yutmaz.

    Asıl korunan şey burada: "landing'de zaten 36px var" cümlesi, bir sonraki turda çıplak bir
    `15px`in gerekçesi olamasın. `clamp()` içindeki uç nokta viewport aritmetiğidir; kuralın
    dışında kalan tek şey odur."""
    for boy in _font_boylari(ad):
        disi = [int(x) for x in re.findall(r"(\d+)px", boy) if int(x) not in RAMPA]
        if not disi:
            continue
        assert boy.startswith("clamp("), (
            f"{ad}: `font-size:{boy}` rampa dışı {disi} ve `clamp()` DEĞİL. Sabit her boy "
            f"rampanın dokuz basamağından biri olmalı (DESIGN.md § Typography).")


@pytest.mark.parametrize("ad", YUZEYLER)
def test_clamp_alt_siniri_RAMPANIN_ALTINA_inmez(ad):
    """Hiçbir `clamp()` alt sınırı 16px'in altına inemez.

    İstisnanın kaçış yoluna dönüşme biçimi tam olarak budur: `clamp(9px,…)` yazıp "akışkan
    tip serbest" demek. İstisna BÜYÜK tipin küçülmesi içindir; rampanın tabanı (10px) etrafından
    dolaşmak için değil."""
    for boy in _font_boylari(ad):
        if not boy.startswith("clamp("):
            continue
        pxler = [int(x) for x in re.findall(r"(\d+)px", boy)]
        assert pxler and min(pxler) >= CLAMP_TABAN, (
            f"{ad}: `font-size:{boy}` alt sınırı {min(pxler)}px — istisnanın tabanı "
            f"{CLAMP_TABAN}px (DESIGN.md § Typography, üç sınırın üçüncüsü).")


# ===================== Ç7 · ss02/cv01 — BUDANDI, GERİ ALINDI, ÇİVİLENDİ =====================
# ÖLÇÜLEN KUSUR SINIFI: **bir özelliğin İKİ yerde birden var olması gerekmesi.** Inter'in Il1
# ayrım özellikleri (`ss02` → `I`/`l` alternatifleri, `cv01` → `1`) varsayılan-KAPALI özellikler.
# İki bağımsız koşul gerekir ve HER BİRİ tek başına sessizce düşebilir:
#   (a) özellik DOSYADA olmalı — subsetter'ın `layout_features` allowlist'i onu düşürebilir,
#       ve 2026-08-24 sabahı tam olarak bunu yapıyordu;
#   (b) CSS descriptor onu AÇMALI — açmazsa dosyadaki tablo hiç çalışmaz.
# (a) düşerse (b) sessizce etkisiz kalır; (b) düşerse (a) boşuna 728 bayt taşır. İkisi de
# ölçülür. Ölçüm ve kanıt: research/olcumler/kesit_ss02cv01_2026-08-24/.
SS02_OLCUM = OLCUM_SS02 / "sonuc.json"


@pytest.fixture(scope="module")
def ss02_olcumu():
    assert SS02_OLCUM.is_file(), (
        f"{SS02_OLCUM} YOK — takip turunun tarayıcı kaydı kayıp. Kaydı olmayan bir tur "
        f"koşulmamış sayılır ve `font-feature-settings` satırı dayanaksız kalır.")
    return json.loads(SS02_OLCUM.read_text(encoding="utf-8"))


@pytest.mark.parametrize("ad", YUZEYLER + ["runbook.html"])
def test_ss02_cv01_descriptori_DORT_YUZEYDE_de_ACIK(ad):
    """(b) yarısı: özelliği açan `font-feature-settings` sans `@font-face`inde olmalı.

    Dört yüzeyde birden, çünkü jeton takımı gibi yazı tipi bildirimi de tek gerçektir
    (v208'in font tarafındaki aynası): bir yüzeyde açık, ötekinde kapalı bir özellik,
    aynı üründe iki farklı `l` demektir."""
    for b in _font_face_blogu(_yorumsuz(_oku(ad))):
        if SANS_AILE not in b.get("font-family", ""):
            continue
        ffs = (b.get("font-feature-settings") or "").replace(" ", "").replace('"', "'")
        assert "'ss02'1" in ffs and "'cv01'1" in ffs, (
            f"{ad}: sans @font-face'inde ss02/cv01 AÇILMAMIŞ → {ffs!r}. Özellikler dosyada "
            f"VAR ama varsayılan-kapalı; descriptor olmadan hiç çizilmezler ve kesit 728 "
            f"baytı boşuna taşır.")
        return
    raise AssertionError(f"{ad}: {SANS_AILE} @font-face bloğu bulunamadı")


def test_ss02_cv01_ozellikleri_DAGITILAN_KESITTE_var(build_kaydi):
    """(a) yarısı: özellik dağıtılan ikilinin GSUB'ında olmalı.

    Bu, descriptor testinin ikizi ve onsuz anlamsız: CSS bir özelliği açabilir, dosyada
    yoksa hiçbir şey olmaz — ve hiçbir test kırmızı vermez. Budama tam da böyle bir yarım
    sözleşmeydi."""
    sans = {x["dosya"]: x for x in build_kaydi["kesitler"]}[SANS_DOSYA]
    for oz in ("ss02", "cv01"):
        assert oz in sans["gsub_ozellikleri"], (
            f"dağıtılan sans kesidinde `{oz}` YOK ({sans['gsub_ozellikleri']}) — subsetter "
            f"yeniden buduyor. `kesit_uret.py::YALIN_OZELLIKLER` listesine bak.")
        assert oz in sans["_yalin_ozellikler"], f"üretim kaydı `{oz}`u saymıyor"
    # Ve dosya GERÇEKTEN diskteki bu bayt: kayıt-artefakt ayrışması ayrı bir arıza sınıfı.
    p = FONTLAR / SANS_DOSYA
    assert p.stat().st_size == sans["bayt"], "kayıt ile diskteki kesit ayrışmış"


def test_ss02_cv01_KAZANCI_olculdu_ve_taban_YENIDEN_URETILDI(ss02_olcumu):
    """Kazanç ÖLÇÜLDÜ, varsayılmadı — ve ölçen düzenek önce kendini kanıtladı.

    KALİBRASYON ÖNCE GELİR: yeni bir klasörde koşan bir rig, donmuş tabanı yeniden
    üretmiyorsa sayıları kıyaslanamaz. Bu tur üretti (Recursive Mono 1,00/0,817 ·
    Recursive Sans 0,931/0,663 · bir önceki turun kesidi 0,968) — üçü de birebir.

    ASIL KAZANÇ `l`/`I`DE: 0,500 → 0,930. `ss02`, `I`yi serifli `I.1`e çeviriyor ve bu,
    bir alım-satım panosunda `Il1` karışmasının en pahalı yarısıdır. `1`/`l` ve `0`/`O`
    kazançları küçük ama YÖNLERİ doğru; hiçbiri gerilemedi."""
    h = ss02_olcumu["hukum"]
    # 1) Kalibrasyon — donmuş tabanla BİREBİR.
    assert [h["kalibrasyon_recursive_mono_1l_10px"], h["kalibrasyon_recursive_mono_1l_28px"]] \
        == h["kalibrasyon_donmus_taban_recursive_mono"], "mono kalibrasyonu TUTMADI"
    assert [h["kalibrasyon_recursive_sans_1l_28px"], h["kalibrasyon_recursive_sans_0O_28px"]] \
        == h["kalibrasyon_donmus_taban_recursive_sans"], "sans kalibrasyonu TUTMADI"
    assert h["kalibrasyon_eski_kesit_1l_28px"] == h["kalibrasyon_08_24_kaydindaki_eski_kesit"], \
        "önceki turun kesidi bu rigde başka bir sayı veriyor — kıyas geçersiz"
    # 2) Budama iddiası iki yönlü doğrulandı.
    assert h["yeni_kesitte_ozellik_VAR_MI"] is True, "yeni kesitte descriptor HİÇBİR ŞEY değiştirmiyor"
    assert h["eski_kesitte_ozellik_YOK_MU"] is True, "eski kesitte özellik varmış — budama iddiası yanlıştı"
    # 3) Ölçülen sayılar — kaymaları görünür olsun diye ADIYLA çivili.
    assert (h["yeni_kesit_1l_28px"], h["eski_kesit_1l_28px"]) == (0.975, 0.968)
    assert (h["yeni_kesit_0O_28px"], h["eski_kesit_0O_28px"]) == (0.795, 0.774)
    assert (h["yeni_kesit_lI_28px"], h["eski_kesit_lI_28px"]) == (0.930, 0.500)
    # 4) Hiçbir eksende gerileme yok, çıta ve biçim sözleşmesi duruyor.
    assert h["yeni_kesit_ESKISINI_geciyor_mu"] and h["yeni_kesit_RECURSIVE_SANSI_geciyor_mu"]
    assert h["cita_yeni_kesit"], "10px 1/l çıtası (0,75) düştü"
    assert h["yeni_kesit_oransal"] and h["yeni_kesit_tnum_acikken_tekduze"], \
        "kesit biçim sözleşmesini kaybetti (oransal + tnum ile tekdüze)"
    # 5) Üst sınır beyanlı: tam dosya 0,988; aradaki 0,013 KAPANMADI ve kapatılmadığı yazılı.
    assert h["ust_sinir_tam_1l_28px"] == 0.988 and h["ust_sinira_kalan_1l_28px"] == 0.013

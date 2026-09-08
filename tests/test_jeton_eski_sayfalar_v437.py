"""v437 — TSK-132 dilim-1: eski sayfaların (runbook/landing/workflow) jeton bloğu ÜRETİLİR.

NEDEN VAR. `meridian/web/tokens.json` jeton SSoT'udur; `ops/jeton_css_uret.py` ondan
`ui/src/jetonlar.css`i üretir ve `tests/test_tasarim_token_v153.py` index.html'in jeton
katmanını tokens.json'a çiviler. ÜÇ eski sayfa (runbook/landing/workflow) ise takımı ELLE
KOPYALIYORDU: `tests/test_jeton_birligi_v208.py` kopyaların index.html ile AYRIŞMADIĞINI ölçer
ama kopyanın kendisini KALDIRMAZ — yani her jeton değişikliği dört yerde elle yapılmak
zorundaydı ve v208 ancak biri unutulduktan SONRA öter. Bu dosya kopyayı ÜRETİME çevirir:
blok artık tokens.json'dan üretilir ve burada byte-eşitlik ölçülür.

ÖLÇÜLDÜ (bu tur, 2026-09-07 · üç sayfanın gündüz+gece blokları):
  · Üç sayfanın `:root` blokları BİRBİRİNİN BAYT KOPYASI (gündüz sha e5c0c3e8 · gece 53dbe55c);
    index.html yalnız yorum metninde ayrılıyor (sha ebd1fc6f/98b5d1fc).
  · Ad kümesi tokens.json ile TAM: gündüz 129/129, gece 96/96 — fazla ad YOK, eksik ad YOK.
  · Değerler de tam: 225/225 jeton tokens.json'ın çözülmüş değeriyle BİREBİR.
  Yani bu dilim GÖRÜNÜR bir palet değişikliği DEĞİL, mekanikleştirmedir: üretimden sonra
  hiçbir hex değişmez (test_HICBIR_DEGER_DEGISMEDI bunu çivi olarak tutar).

ESKI_AD_ESLEME NEDEN BOŞ. Brief "eski adlar (`--bg/--card/--tx/--accent/…`) tokens.json'da YOK"
ölçümüyle geldi; yeniden ölçüm bunu ÇÜRÜTTÜ (yukarıdaki 129/129 · 96/96). Uydurma yasağı gereği
tablo BOŞ bırakıldı — ama ÖLÜ değil: üretici, bölgede tanımlı olup tokens.json'da da tabloda da
karşılığı olmayan bir ad görürse SESSİZCE DÜŞÜRMEZ, reddeder (`jeton_css_uret.sayfa_denetimi`).
Pozitif kontrol o mekanizmayı sentetik bir sayfayla ısırtır — boş bir sözlük yüzünden ölçülmemiş
bir dal kalmasın diye.

MEDYA BLOĞU BİLEREK YOK. Brief `@media (prefers-color-scheme: dark)` + `:root:not([data-theme])`
grameri istiyordu (v412 dersi). ÖLÇÜM: bu grameri `ui/src/jetonlar.css` taşır; eski sayfaların
HİÇBİRİNDE (index.html dahil) medya bloğu yok ve v208'in `test_yuzeyde_tam_iki_root_blogu_var`
çivisi her yüzeyde TAM İKİ `:root` bloğu şart koşar — üçüncü bir `:root` o çiviyi kırardı.
Eski sayfalarda OS tercihi zaten `theme.js`in tohumladığı `data-theme` niteliğiyle gelir.

TSK-132 DİLİM-2 (2026-09-08) — BLOK'TAN LİNK'E. Dilim-1 HTML'e enjekte ediyordu: N sayfa = N
FİZİKSEL kopya (bayt-eşit, ama AYRI dosyalarda — v437'nin BAYT-EŞİTLİK çivisi ayrışmayı YAKALAR
ama kopyayı KALDIRMAZ, dilim-1'in kendi gerekçesiyle AYNI kusur sınıfı bir kademe yukarıda).
Dilim-2 `runbook.html` ve `landing.html`i `<link rel="stylesheet" href="/jetonlar.css">`e
taşıdı — TEK dosya (`meridian/web/jetonlar.css`, `ops/jeton_css_uret.py::dosya_blogu()`), N
sayfa, N link. `workflow.html` KAPSAM DIŞI bırakıldı (dilim-2 brief'i böyle tanımladı) ve HÂLÂ
blok taşıyor — bu dosyanın (a)/(d)/(e)/(f) bölümleri artık YALNIZ `workflow.html`e bakar,
`runbook.html`/`landing.html` yeni bir bölüme (g) taşındı.

`index.html` DE KAPSAM DIŞI BIRAKILDI — ÖLÇÜLEREK, brief'in "üç sayfa" varsayımının AKSİNE:
index.html'in `:root` blokları dilim-1'de HİÇ üretime alınmamıştı (bu dosyanın `SAYFALAR`ı hep
runbook/landing/workflow'du) ve kendi başına 550+ satırlık, TEK yerde duran tasarım gerekçesiyle
(DIRECTION CONTRACT, font ölçümü, gece paleti türetimi) İÇ İÇE geçmiş durumda — mekanik bir
`<link>` taşıması o gerekçeyi ya siler (bedel yasası ihlali) ya da 550 satırı yorum olarak
sayfada bırakıp değerleri jetonlar.css'e taşımak gibi çok daha büyük, AYRI bir dal gerektirir.
Karar Rol-1'e devredildi (devir brief'i, rapor: TSK132 dilim-2 raporu).

`ui/src/jetonlar.css` (panonun/Vite'ın okuduğu, `uret()`in çıktısı) İLE `meridian/web/jetonlar.css`
(bu dosyanın "dosya kipi" çıktısı, `dosya_blogu()`) KARIŞTIRILMASIN: AYNI ADI taşırlar ama FARKLI
seçici grameri üretirler (ölçüldü: eski sayfalar `theme.js`in kurduğu `data-theme="gece"` okur,
pano `data-theme="dark"`/`.dark` okur) — `ops/jeton_css_uret.py`nin DOSYA KİPİ notu ayrımı
tam anlatır.
"""
from __future__ import annotations

import importlib
import pathlib
import re
import subprocess
import sys

import pytest

KOK = pathlib.Path(__file__).resolve().parents[1]
WEB = KOK / "meridian" / "web"
URETICI = KOK / "ops" / "jeton_css_uret.py"
# BLOK SAYFALAR — dilim-1'in çözümünü (HTML'e enjekte edilmiş blok) HÂLÂ taşıyanlar.
SAYFALAR = ("workflow.html",)
# LİNK SAYFALAR — dilim-2'nin taşıdığı, `<link href="/jetonlar.css">` okuyanlar (aşağı bkz. (g)).
LINK_SAYFALAR = ("runbook.html", "landing.html")
# DOSYA — LİNK_SAYFALAR'ın PAYLAŞTIĞI, `--dosya` ile üretilen bağımsız CSS dosyası.
DOSYA = "jetonlar.css"

jcu = importlib.import_module("ops.jeton_css_uret")


def _oku(ad: str) -> str:
    return (WEB / ad).read_text(encoding="utf-8")


def _bolge(metin: str) -> str:
    i, j = jcu._sayfa_bolgesi(metin)
    return metin[i:j]


# ======================= (a) BLOK/DOSYA == ÜRETİCİ ÇIKTISI =======================

@pytest.mark.parametrize("ad", SAYFALAR)
def test_isaretli_blok_URETICI_CIKTISI_ile_BAYT_ESIT(ad):
    """AYRIŞMA ÇİVİSİ (BLOK KİPİ — yalnız workflow.html, dilim-2 kapsam dışı). Sayfadaki
    işaretli blok, üreticinin tokens.json'dan ürettiği metinle BAYT eşit olmalı. Eşit değilse
    iki şeyden biri olmuştur ve ikisi de aynı kapıya çıkar: ya tokens.json değişti ve sayfa
    yeniden üretilmedi (bayat kopya), ya da bloğa ELLE dokunuldu (bir sonraki üretim o
    düzenlemeyi sessizce siler)."""
    blok, _ = jcu.sayfa_blogu()
    assert _bolge(_oku(ad)) == blok, (
        f"{ad}: jeton bloğu üretici çıktısıyla ayrışmış — "
        f"`python ops/jeton_css_uret.py --sayfa meridian/web/{ad} --uygula` koşulmalı")


def test_DOSYA_URETICI_CIKTISI_ile_BAYT_ESIT():
    """AYRIŞMA ÇİVİSİ (LİNK KİPİ — `meridian/web/jetonlar.css`, `runbook.html`/`landing.html`in
    paylaştığı dosya). `test_isaretli_blok_URETICI_CIKTISI_ile_BAYT_ESIT`in link-kipi karşılığı:
    diskteki dosya `dosya_blogu()`nun BAYT eşiti olmalı, yoksa `meridian/web/jetonlar.css`
    tokens.json ile ayrışmış demektir."""
    css, _ = jcu.dosya_blogu()
    assert (WEB / DOSYA).read_text(encoding="utf-8") == css, (
        f"{DOSYA}: üretici çıktısıyla ayrışmış — `python ops/jeton_css_uret.py --dosya` koşulmalı")


def test_SAYFA_BLOGU_ve_DOSYA_BLOGU_AYNI_GOVDEYI_tasiyor():
    """İKİ TESLİMAT, TEK KAYNAK. `sayfa_blogu()` (HTML'e enjekte, workflow.html) ve
    `dosya_blogu()` (bağımsız dosya, jetonlar.css) AYNI `_kovalar()`tan (tokens.json) türer ve
    AYNI seçici gramerini (`:root` + `:root[data-theme="gece"]`) taşır — TEK fark başlık/işaret
    metni. Bu test o gövdenin (başlık/işaret HARİÇ) BAYT eşit olduğunu ölçer: ikisi ayrışırsa
    dilim-1 (blok) ve dilim-2 (link) yollarından biri diğerinden GERİ kalmış demektir — tam
    olarak eski `test_UC_SAYFA_ayni_blogu_tasiyor`nun koruduğu kusur sınıfı, şimdi İKİ ÜRETİM
    YOLU arasında (üç HTML kopyası arasında değil)."""
    sayfa, _ = jcu.sayfa_blogu()
    sayfa_govde = sayfa[len(jcu.SAYFA_ISARET_BAS) + 1 + len(jcu.SAYFA_BASLIK) + 1:
                        -len(jcu.SAYFA_ISARET_SON)]
    dosya, _ = jcu.dosya_blogu()
    dosya_govde = dosya[len(jcu.DOSYA_BASLIK):]
    assert sayfa_govde == dosya_govde, "sayfa_blogu() ve dosya_blogu() gövdesi ayrışmış"


def test_HICBIR_DEGER_DEGISMEDI_index_html_referansiyla():
    """BEDEL ÖLÇÜMÜ (bedel yasası). Bu dilim mekanikleştirmedir; GÖRÜNÜR bir palet değişikliği
    getirmemesi gerekir. Üretilen bloğun her jeton değeri, index.html'in (v153 ile tokens.json'a
    çivili) kendi bloklarındaki değerle aynı olmalı — aksi hâlde 'yalnız mekanikleştirme' beyanı
    yanlış olur ve sayfalar sessizce yeni bir palete geçer."""
    blok, _ = jcu.sayfa_blogu()
    index = _oku("index.html")
    yorumsuz = re.sub(r"/\*.*?\*/", " ", index, flags=re.S)

    def jetonlar(govde: str) -> dict[str, str]:
        return {m.group(1): re.sub(r"\s+", " ", m.group(2)).strip()
                for m in re.finditer(r"(--[a-zA-Z0-9-]+)\s*:\s*([^;}]+)", govde)}

    def blok_govde(metin: str, sec: str) -> str:
        i = metin.index(sec + "{")
        j = metin.index("{", i)
        return metin[j + 1:metin.index("\n}", j)]

    blok_yorumsuz = re.sub(r"/\*.*?\*/", " ", blok, flags=re.S)
    for sec in (jcu.SAYFA_GUNDUZ_SEC, jcu.SAYFA_GECE_SEC):
        uretilen = jetonlar(blok_govde(blok_yorumsuz, sec))
        referans = jetonlar(blok_govde(yorumsuz, sec))
        ayrik = sorted(k for k in set(uretilen) & set(referans) if uretilen[k] != referans[k])
        assert not ayrik, "\n".join(
            f"{sec} --{k}: üretilen={uretilen[k]!r} index.html={referans[k]!r}" for k in ayrik)
        assert set(uretilen) == set(referans), (
            f"{sec} ad kümesi index.html ile ayrışmış: "
            f"fazla={sorted(set(uretilen) - set(referans))} eksik={sorted(set(referans) - set(uretilen))}")


# ======================= (b) --kontrol BAYATLIK KAPISI =======================

def test_kontrol_GUNCEL_sayfada_SIFIR_dondurur(tmp_path):
    """DÖRT yüzey de (workflow blok kipinde, runbook/landing link kipinde) ağaçta güncelken
    `--kontrol` 0 döner — brief'in "--kontrol üç/dört sayfada temiz" gereksinimi. Bu testin
    yeşili tek başına yetmez (aşağıdaki mutasyon testleri onu ısırtır); birlikte kapıyı ölçer."""
    assert jcu.main(["--kontrol",
                     *[f"--sayfa={WEB / ad}" for ad in SAYFALAR + LINK_SAYFALAR]]) == 0


def test_DOSYA_kontrol_GUNCEL_SIFIR_dondurur():
    """`--dosya --kontrol`ün GÜNCEL dalı — `meridian/web/jetonlar.css` ağaçta güncelken 0
    döner. `test_kontrol_GUNCEL_sayfada_SIFIR_dondurur`nün dosya-kipi karşılığı."""
    assert jcu.main(["--dosya", "--kontrol"]) == 0


def test_kontrol_BAYAT_sayfayi_YAKALAR(tmp_path):
    """MUTASYON (BLOK KİPİ): bloktaki bir hex'i değiştir → `--kontrol` 1 dönmeli. Bir tazelik
    kapısı, ancak bayatlığı GERÇEKTEN gördüğü ölçülünce kapıdır (18 çivi yeşilken `--uygula`nın
    sessizce yok sayıldığı vaka, 2026-08-30). Kaynak `workflow.html` — dilim-2'den SONRA blok
    kipini taşıyan TEK sayfa (`runbook.html`/`landing.html` artık link kipinde, bkz. (g))."""
    p = tmp_path / "workflow.html"
    metin = _oku("workflow.html")
    bozuk = metin.replace("--bg: #fafafa;", "--bg: #fafaf0;", 1)
    assert bozuk != metin, "mutasyon uygulanamadı — blok biçimi değişti mi?"
    p.write_text(bozuk, encoding="utf-8")
    assert jcu.main([f"--sayfa={p}", "--kontrol"]) == 1


def test_DOSYA_kontrol_BAYAT_YAKALAR(tmp_path):
    """MUTASYON (LİNK KİPİ): `meridian/web/jetonlar.css`teki bir hex'i değiştir → `--dosya
    --kontrol` 1 dönmeli. `--cikti` ile hedefi geçici bir kopyaya YÖNLENDİRİR — gerçek dosyaya
    dokunmadan bayatlık algısı ölçülür."""
    p = tmp_path / "jetonlar.css"
    metin = (WEB / DOSYA).read_text(encoding="utf-8")
    bozuk = metin.replace("--bg: #fafafa;", "--bg: #fafaf0;", 1)
    assert bozuk != metin, "mutasyon uygulanamadı — dosya biçimi değişti mi?"
    p.write_text(bozuk, encoding="utf-8")
    assert jcu.main(["--dosya", f"--cikti={p}", "--kontrol"]) == 1


def test_kontrol_ISARETSIZ_sayfayi_BAYAT_sayar(tmp_path):
    """İşaret taşımayan (henüz taşınmamış) bir sayfa da BAYATtır: eski elle-kopya bölge
    üreticinin çıktısı DEĞİLDİR. Sessizce 'güncel' demek, taşımanın hiç yapılmadığını
    gizlerdi."""
    p = tmp_path / "eski.html"
    p.write_text(
        "<style>\n:root{\n  --bg:#fafafa;\n}\n"
        ':root[data-theme="gece"]{\n  --bg:#171717;\n}\n</style>\n', encoding="utf-8")
    assert jcu.main([f"--sayfa={p}", "--kontrol"]) == 1


# ======================= (c) EŞLEME TABLOSU =======================

def test_ESKI_AD_ESLEME_hedefleri_tokens_jsonda_VAR():
    """Tablonun her HEDEFİ gerçek bir jeton olmalı. Var olmayan bir role takma ad bağlamak,
    sayfayı `var(--yok)` ile TANIMSIZ değere düşürürdü — ve bu sessiz bir arızadır."""
    kova, _ = jcu._kovalar()
    bilinen = {ad for kutu in kova.values() for ad, _ in kutu}
    eksik = sorted(r for r in jcu.ESKI_AD_ESLEME.values() if r not in bilinen)
    assert not eksik, f"ESKI_AD_ESLEME hedefi tokens.json'da yok: {eksik}"


def test_ESLENEMEYEN_ad_SESSIZCE_DUSURULMEZ(tmp_path):
    """POZİTİF KONTROL — tablo bugün BOŞ olduğu için mekanizma sentetik olarak ısırtılır.
    Bölgede tokens.json'da karşılığı olmayan bir ad varsa üretici REDDEDER (uydurma yasağı):
    o adı okuyan kurallar tanımsıza düşeceği için sessiz düşürme kabul edilemez."""
    p = tmp_path / "eski.html"
    p.write_text(
        "<style>\n:root{\n  --bg:#fafafa; --ESKI-AD-YOK:#ff0000;\n}\n"
        ':root[data-theme="gece"]{\n  --bg:#171717;\n}\n</style>\n', encoding="utf-8")
    assert jcu.main([f"--sayfa={p}", "--uygula"]) == 2
    assert "--ESKI-AD-YOK" in p.read_text(encoding="utf-8"), \
        "reddedilen sayfa yine de yazılmış — red, yazmamak demektir"


def test_ESLEME_TAKMA_ADI_URETIR(monkeypatch):
    """Tablo dolu olsaydı ne olurdu: eski ad, rol jetonuna `var()` ile bağlanır ve İKİ temada
    da bildirilir (gece bloğunda eksik kalırsa sayfa gecede gündüz rengini miras alır —
    `--nav-bg` vakasının sınıfı)."""
    monkeypatch.setattr(jcu, "ESKI_AD_ESLEME", {"--eski-vurgu": "--accent"})
    blok, _ = jcu.sayfa_blogu()
    assert blok.count("--eski-vurgu: var(--accent);") == 2, blok[:400]


# ======================= (d) BLOK/SAYFA DIŞINDA JETON TANIMI YOK =======================

@pytest.mark.parametrize("ad", SAYFALAR)
def test_ISARETLI_BLOK_DISINDA_ham_renkli_jeton_tanimi_YOK(ad):
    """İkinci bir sözlük doğmasın: işaretli bloğun DIŞINDA `--x: #hex` tanımı olamaz. Böyle bir
    tanım üretimin kapsamı dışında kalır, yani tokens.json değiştiğinde geride kalır — tam olarak
    bu dilimin kaldırdığı kusur sınıfı. (Ham renk TAŞIMAYAN bildirimler, ör. gövdedeki
    `style="--cols:2"`, kapsam dışı: onlar palet değil yerleşim parametresi.)"""
    metin = _oku(ad)
    i, j = jcu._sayfa_bolgesi(metin)
    dis = metin[:i] + metin[j:]
    dis = re.sub(r"/\*.*?\*/", " ", re.sub(r"<!--.*?-->", " ", dis, flags=re.S), flags=re.S)
    bulunan = [m.group(0) for m in re.finditer(r"--[a-zA-Z0-9-]+\s*:\s*#[0-9a-fA-F]{3,8}\b", dis)]
    assert not bulunan, f"{ad}: işaretli blok dışında jeton tanımı {bulunan}"


@pytest.mark.parametrize("ad", LINK_SAYFALAR)
def test_LINK_SAYFADA_hicbir_yerde_ham_renkli_jeton_tanimi_YOK(ad):
    """Link kipindeki bir sayfanın ARTIK bloğu yok — üstteki testin link-kipi karşılığı SAYFANIN
    TAMAMINI tarar (hariç tutulacak bir bölge yok, çünkü tanım hiç kalmamalı): tokens.json'dan
    türeyen HİÇBİR `--x: #hex` bildirimi bu sayfada durmamalı, tümü `jetonlar.css`e taşındı."""
    dis = _oku(ad)
    dis = re.sub(r"/\*.*?\*/", " ", re.sub(r"<!--.*?-->", " ", dis, flags=re.S), flags=re.S)
    bulunan = [m.group(0) for m in re.finditer(r"--[a-zA-Z0-9-]+\s*:\s*#[0-9a-fA-F]{3,8}\b", dis)]
    assert not bulunan, f"{ad}: link kipine geçti ama HÂLÂ ham renkli jeton tanımı taşıyor {bulunan}"


# ======================= (e) KOMŞU ÇİVİLERİN SÖZLEŞMESİ =======================

def test_URETILEN_BLOK_v153_KESICISININ_bekledigi_bicimde():
    """v153'ün Ç3 ham-renk linti jeton bloklarını `":root{"` ve `':root[data-theme=\"gece\"]'`
    LİTERALLERİYLE keser (boşluklu `:root {` o kesiciyi `ValueError` ile düşürürdü, yani lint
    ölçüm yapamaz hâle gelirdi). `jetonlar.css` boşluklu biçimi kullanır ve KULLANMAYA DEVAM
    eder — bu yüzden sayfa kipi ayrı bir biçim taşır ve o fark burada çivilenir."""
    blok, _ = jcu.sayfa_blogu()
    assert ":root{" in blok and ':root[data-theme="gece"]{' in blok, blok[:300]
    assert ":root {" not in blok, "boşluklu seçici — v153'ün blok kesicisi bunu bulamaz"


def test_URETILEN_BLOK_TAM_IKI_root_kurali():
    """v208 her yüzeyde TAM İKİ `:root` bloğu ölçer (üçüncüsü = ikinci bir gerçek kaynak).
    Üretilen blok bu sayıyı değiştiremez — medya sorgusu eklemek de dahil."""
    blok, _ = jcu.sayfa_blogu()
    secililer = re.findall(r"^(:root[^{\n]*)\{", re.sub(r"/\*.*?\*/", "", blok, flags=re.S), re.M)
    assert secililer == [jcu.SAYFA_GUNDUZ_SEC, jcu.SAYFA_GECE_SEC], secililer


@pytest.mark.parametrize("ad", SAYFALAR)
def test_v208_ISARETCISI_blogun_DISINDA_kaldi(ad):
    """v208'in `test_kopya_yuzey_bu_TESTE_isaret_ediyor` çivisi her kopya yüzeyde kendi dosya
    adını arar. İşaret bloğun DIŞINDA da durmalı: blok bir gün yeniden üretilirken içindeki
    metin değişse bile sayfanın 'beni ne koruyor' kaydı kaybolmasın."""
    metin = _oku(ad)
    i, j = jcu._sayfa_bolgesi(metin)
    assert "test_jeton_birligi_v208.py" in (metin[:i] + metin[j:]), \
        f"{ad}: v208 işaretçisi YALNIZ üretilmiş bloğun içinde — üretim onu silebilir"


@pytest.mark.parametrize("ad", LINK_SAYFALAR)
def test_LINK_SAYFADA_v208_isaretcisi_VAR(ad):
    """Link kipindeki sayfanın artık `_sayfa_bolgesi`si (bloğu) yok — üstteki testin "bloğun
    dışında" koşulu anlamsızlaştı, ama İDDİA (bu takımı v208 koruyor) hâlâ geçerli: sayfa hâlâ
    `jetonlar.css`i okuyor ve o dosyanın değerleri v208'de index.html'le karşılaştırılıyor
    (bkz. tests/test_jeton_birligi_v208.py `DEGER_KARSILASTIRMA`). Basit üyelik yeter — blok
    yok, silinecek bir bölge de yok."""
    assert "test_jeton_birligi_v208.py" in _oku(ad), \
        f"{ad}: takımı neyin koruduğunu söyleyen v208 kaydı yok"


def test_JETONLAR_CSS_URETIMI_DEGISMEDI():
    """REGRESYON: sayfa kipi eklenirken `ui/src/jetonlar.css` çıktısının BAYTI değişmemeli.
    Değişseydi v395/v407/v412 kırmızıya dönerdi — ama onlar diskteki dosyayı ölçer, bu satır
    ÜRETİCİYİ ölçer: `--kontrol` 0 demek 'üretici hâlâ aynı baytı veriyor' demektir."""
    assert jcu.main(["--kontrol"]) == 0


# ======================= (f) KOMUT SATIRI SÖZLEŞMESİ =======================

def test_KOMUT_SATIRI_uygula_SESSIZCE_YOK_SAYILMIYOR(tmp_path):
    """Ops aracı, operatörün koşacağı BİÇİMDE ölçülür (vaka 2026-08-30: 18 çivi yeşilken
    `--uygula` sessizce yok sayılıyordu). Gerçek bir alt süreçte, gerçek komut satırıyla:
    kuru koşum YAZMAZ, `--uygula` YAZAR. Kaynak `workflow.html` (blok kipindeki TEK sayfa;
    `runbook.html`/`landing.html` artık link kipinde — bkz. (g))."""
    p = tmp_path / "workflow.html"
    metin = _oku("workflow.html")
    p.write_text(metin.replace("--bg: #fafafa;", "--bg: #fafaf0;", 1), encoding="utf-8")
    once = p.read_text(encoding="utf-8")

    kuru = subprocess.run([sys.executable, str(URETICI), "--sayfa", str(p)],
                          capture_output=True, text=True, cwd=str(KOK))
    assert kuru.returncode == 0, kuru.stderr
    assert p.read_text(encoding="utf-8") == once, "kuru koşum dosyayı YAZDI"
    assert "--bg" in kuru.stdout, f"kuru koşum diff basmadı: {kuru.stdout[:400]!r}"

    yaz = subprocess.run([sys.executable, str(URETICI), "--sayfa", str(p), "--uygula"],
                         capture_output=True, text=True, cwd=str(KOK))
    assert yaz.returncode == 0, yaz.stderr
    assert p.read_text(encoding="utf-8") != once, "`--uygula` sessizce yok sayıldı"
    assert _bolge(p.read_text(encoding="utf-8")) == jcu.sayfa_blogu()[0]


def test_UYGULA_SAYFASIZ_kullanim_HATASI(tmp_path):
    """`--uygula` yalnız sayfa kipinde anlamlıdır. Sayfasız verilince SESSİZCE yok saymak,
    operatöre 'yazdım' hissi verip hiçbir şey yazmamak olurdu."""
    assert jcu.main(["--uygula"]) == 2


def test_SAYFA_ve_CIKTI_birlikte_HATA(tmp_path):
    """İki hedef aynı anda verilemez: hangisinin yazıldığı sıraya kalırdı."""
    assert jcu.main([f"--sayfa={WEB / 'runbook.html'}", f"--cikti={tmp_path / 'x.css'}"]) == 2


def test_URETIM_DETERMINISTIK():
    """Damga yok: iki koşu aynı baytı verir. Aksi hâlde `--kontrol` her koşuda 'bayat' derdi."""
    assert jcu.sayfa_blogu()[0] == jcu.sayfa_blogu()[0]


def test_KULLANIM_metni_SAYFA_KIPINI_anlatiyor():
    """YASA 6 — okuyucusuz yazım yok: yeni kipin komut satırı sözleşmesi, betiği açan kişinin
    gördüğü yerde (modül docstring'inin KULLANIM bölümü) yazılı olmalı."""
    d = jcu.__doc__ or ""
    assert "--sayfa" in d and "--uygula" in d, "KULLANIM bölümü sayfa kipini anlatmıyor"


def test_KULLANIM_metni_DOSYA_KIPINI_anlatiyor():
    """YASA 6 — `--dosya`nın komut satırı sözleşmesi de modül docstring'inde yazılı olmalı."""
    d = jcu.__doc__ or ""
    assert "--dosya" in d, "KULLANIM bölümü dosya kipini anlatmıyor"


# ======================= (g) LİNK KİPİ (TSK-132 dilim-2) =======================
# `runbook.html`/`landing.html` artık `<link rel="stylesheet" href="/jetonlar.css">` okur —
# kendi bloğu yok. Aşağıdaki testler brief'in üç şartını ölçer: "blok yok + link var +
# jetonlar.css'te sayfanın kullandığı her `--jeton` tanımlı" (değişken kümesi eşitliği çivisi).

@pytest.mark.parametrize("ad", LINK_SAYFALAR)
def test_LINK_SAYFADA_isaretli_blok_YOK(ad):
    """"Blok yok" şartı. `SAYFA_ISARET_BAS` sayfada BULUNMAMALI — bulunursa dilim-2'nin
    kaldırdığı kopya geri gelmiş demektir."""
    assert jcu.SAYFA_ISARET_BAS not in _oku(ad), f"{ad}: işaretli blok GERİ GELMİŞ"


@pytest.mark.parametrize("ad", LINK_SAYFALAR)
def test_LINK_SAYFADA_kanonik_link_VAR(ad):
    """"Link var" şartı. Kanonik `<link rel="stylesheet" href="/jetonlar.css">` etiketi TAM
    bu bayt dizisiyle bulunmalı — farklı bir yol/öznitelik sırası `sayfa_baglantili_mi`yi
    (ve dolayısıyla `--kontrol`ü) sessizce YOK sayardı."""
    assert jcu.SAYFA_LINK_ETIKETI in _oku(ad), f"{ad}: kanonik <link> etiketi yok"


@pytest.mark.parametrize("ad", LINK_SAYFALAR)
def test_LINK_SAYFADA_href_SELF_ORIGIN(ad):
    """CSP ÇİVİSİ. `href` kök-göreli (`/jetonlar.css`) olmalı — mutlak bir URL (`https://…`)
    hem AYNI origin garantisini kaybettirirdi hem de CSP `style-src 'self'`in izin vermediği
    bir üçüncü-taraf isteği doğururdu (dış origin ÜRETİMDE bloklanır, sayfa ölü açılır)."""
    metin = _oku(ad)
    assert 'href="/jetonlar.css"' in metin, f"{ad}: href kök-göreli değil (self-origin şartı)"
    assert "://" not in re.search(r'<link[^>]+jetonlar\.css[^>]*>', metin).group(0), (
        f"{ad}: <link> etiketi mutlak bir URL taşıyor — CSP style-src 'self' bunu bloklar")


@pytest.mark.parametrize("ad", LINK_SAYFALAR)
def test_LINK_SAYFA_kullanilan_jetonlar_DOSYADA_TANIMLI(ad):
    """"jetonlar.css'te sayfanın kullandığı her `--jeton` tanımlı" şartı — POZİTİF hâl. Sayfanın
    KULLANDIĞI (`var(--x)`, tek-argümanlı) her ad, `dosya_blogu()`nun bildirdiği kümenin ALT
    KÜMESİ (⊆) olmalı. Boş liste = temiz; MUTASYON karşılığı aşağıda."""
    hatalar = jcu.baglanti_denetimi(_oku(ad))
    assert hatalar == [], f"{ad}: {hatalar}"


@pytest.mark.parametrize("ad", LINK_SAYFALAR)
def test_LINK_SAYFA_sayfa_baglantili_mi_DOGRU_SINIFLANDIRIR(ad):
    """Sınıflandırma mekanizmasının kendisi: gerçek bir link sayfası `sayfa_baglantili_mi` ile
    True dönmeli — bu, `_sayfa_kipi`nin onu doğru dala (yazma pasosunu atlayan "link" dalına)
    yönlendirdiğinin ön koşuludur."""
    assert jcu.sayfa_baglantili_mi(_oku(ad)) is True, f"{ad}: link kipi olarak tanınmıyor"


@pytest.mark.parametrize("ad", LINK_SAYFALAR)
def test_LINK_SAYFA_KONTROL_temiz(ad):
    """`--kontrol` üç/dört sayfada temiz — brief'in doğrudan istediği ÜÇLÜ ölçümün son ayağı:
    gerçek dosya, gerçek CLI, ağaçtaki hâliyle."""
    assert jcu.main(["--sayfa", str(WEB / ad), "--kontrol"]) == 0


# ---- MUTASYONLAR (≥3, brief'in istediği üçü BİREBİR) ----

@pytest.mark.parametrize("ad", LINK_SAYFALAR)
def test_MUTASYON_link_KALDIRILIRSA_KIRMIZI(ad, tmp_path):
    """MUTASYON 1/3: "link'i kaldır → kırmızı". Kanonik `<link>` etiketini bir kopyadan sil —
    sayfa artık ne blok kipinde ne link kipinde tanınmayan bir yüzey olur ve `--kontrol` 2
    (KULLANIM/red) dönmeli, sessizce 0 DEĞİL."""
    metin = _oku(ad)
    bozuk = metin.replace(jcu.SAYFA_LINK_ETIKETI, "", 1)
    assert bozuk != metin, "mutasyon uygulanamadı — link etiketi bulunamadı"
    p = tmp_path / ad
    p.write_text(bozuk, encoding="utf-8")
    assert jcu.main(["--sayfa", str(p), "--kontrol"]) == 2


def test_MUTASYON_jetonlar_CSS_TEN_DEGISKEN_SILINIRSE_KIRMIZI(monkeypatch):
    """MUTASYON 2/3: "jetonlar.css'ten bir değişken sil → kırmızı". `_kovalar()`ı, landing.html'in
    GERÇEKTEN okuduğu bir adı (`--accent`, tek-argümanlı `var(--accent)` — ölçüldü, grep) TAŞIMAYAN
    sahte bir kovayla değiştir: `baglanti_denetimi` bu eksikliği YAKALAMALI. Gerçek tokens.json'a
    dokunmadan (`monkeypatch` turun sonunda geri alır) `_kovalar`ın TEK çağrı noktası üzerinden
    ısırılır — `dosya_blogu()`/`baglanti_denetimi()` ikisi de bu fonksiyonu okur (tek kaynak)."""
    gercek_kovalar = jcu._kovalar

    def _eksik_kova():
        kova, atlanan = gercek_kovalar()
        kova = {k: [(ad, deger) for ad, deger in v if ad != "--accent"] for k, v in kova.items()}
        return kova, atlanan

    monkeypatch.setattr(jcu, "_kovalar", _eksik_kova)
    hatalar = jcu.baglanti_denetimi(_oku("landing.html"))
    assert hatalar and "--accent" in hatalar[0], hatalar


@pytest.mark.parametrize("ad", LINK_SAYFALAR)
def test_MUTASYON_BLOK_GERI_KONURSA_KIRMIZI(ad, tmp_path):
    """MUTASYON 3/3: "bloğu geri koy → kırmızı". `sayfa_blogu()`nun TAZE (bayt-eşit) çıktısını
    linkin YANINA (kaldırmadan) ekle — blok TAZE olduğu için eski `sayfa_denetimi`/bayatlık
    mekanizması bunu YEŞİL görürdü; asıl kontrol `sayfa_cakismasi_mi`dedir: iki kaynak (blok +
    link) AYNI ANDA var olamaz, blok ne kadar güncel olursa olsun. `--kontrol` 2 (red) dönmeli."""
    blok, _ = jcu.sayfa_blogu()
    metin = _oku(ad)
    assert jcu.SAYFA_LINK_ETIKETI in metin, "ön koşul: sayfa hâlâ link taşımalı"
    bozuk = metin + "\n<style>\n" + blok + "\n</style>\n"
    assert jcu.sayfa_cakismasi_mi(bozuk), "mutasyon çakışma üretmedi — işaretler değişti mi?"
    p = tmp_path / ad
    p.write_text(bozuk, encoding="utf-8")
    assert jcu.main(["--sayfa", str(p), "--kontrol"]) == 2

"""v208 — D5: JETON BİRLİĞİ. Dört yüzey, tek jeton takımı — ÖLÇÜLEREK.

ÖLÇÜLEN KUSUR SINIFI: **bir yorumun kendi uyardığı hatayı yaşaması.**

`meridian/web/landing.html` bir yıl boyunca şunu yazıyordu:

    "GECE ZEMİNİ — index.html ile AYNI değer takımı. Üç yüzey tek tercih okur
     (theme.js); değerler ayrışırsa operatör aynı üründe iki dünya görür.
     Bir jeton burada değişecekse ÜÇÜNDE birden değişir."

2026-08-07 ölçümü bunu ÇÜRÜTTÜ (yorumlar sıyrılmış `:root` blokları):

    index.html      gündüz 97 jeton · gece 74
    landing.html    gündüz 59        · gece 36   ┐ ikisi birbirinin AYNISI,
    workflow.html   gündüz 59        · gece 36   ┘ ikisi de index'ten AYRIK
    runbook.html    iki koşulsuz blok, 11 + 9 · KENDİ paleti

    GÜNDÜZ 13 değer ayrışmış (--bg saf beyazda kalmıştı: WP-P/P9 turu index'e
      uygulanmış, bu iki yüzeye uygulanmamıştı) · GECE 2 değer (--tx3, --violet:
      B1/B6 düzeltmeleri de gelmemişti) · ROL KATMANININ TAMAMI (40 jeton, D1)
      EKSİK · ve iki EMEKLİ jeton (--pm-pos/--pm-neg, rol katmanı öncesinin yön
      sözlüğü) YALNIZ o iki yüzeyde hayatta.

Yani yorum yazılırken uyardığı hata çoktan gerçekleşmişti. Kök neden yorumun
YANLIŞ olması değil, ÖLÇÜLMEMESİ: bir yorum kapı değildir. Bu dosya kapıdır.

NEDEN MEVCUT LİNT YETMİYORDU. `tests/test_tasarim_token_v153.py` bu depodaki
jeton disiplinini üç ayrı açıdan ölçer ama hiçbiri bu boşluğu kapatmaz:
  Ç1/Ç2/Ç4 (tokens.json eş-kaydı · tam palet · kontrast çivisi) YALNIZ
    `index.html`in jeton katmanına bakar — o dosyanın kendi yorumunda yazılı.
  Ç3 (ham renk) altı yüzeyde KURAL GÖVDESİNDEKİ ham hex'i arar. Ayrışmanın
    tamamı `:root` İÇİNDE, yani jeton bildiriminin kendisinde yaşıyordu; Ç3
    oraya bakmaz ve bakmamalı — jetonun tanımlandığı yer ham değerin MEŞRU
    yeridir. Ham-renk linti "renk jetondan mı geliyor" sorusunu ölçer;
    bu dosya "jeton HER YÜZEYDE AYNI MI" sorusunu ölçer. İkisi ayrı sorudur ve
    ilkinin yeşil olması ikincisi hakkında hiçbir şey söylemez.

YORUMLAR ÖNCE SIYRILIR — VE BU BİR TİTİZLİK DEĞİL, ÖLÇÜLMÜŞ BİR TUZAK. Bu
depoda her karar gerekçesiyle yazılır, yani `:root` bloklarının çevresinde
`--red:` / `#ffffff` gibi dizgeleri İÇEREN uzun yorumlar var. Sıyırmayan bir
ayrıştırıcı onları jeton sanar (Rol-1 bunu iki kez yaşadı). HTML yorumu
(`<!--…-->`) ve CSS yorumu (`/*…*/`) AYRI AYRI temizlenir; `test_ayristirici_
YORUMU_JETON_SANMIYOR` bu davranışın kendisini sınar, çünkü ölçüm aracının
sessizce bozulması ölçülen şeyin sessizce bozulmasıyla aynı kapıya çıkar.

REFERANS `index.html`dir. Bu dosya "hangi değer doğru" sorusunu CEVAPLAMAZ —
onun cevabı `docs/kontrast-denetimi.md` ve `index.html`in kendi bloklarındadır.
Burada ölçülen tek şey AYRIŞMA: dördü aynı mı, değilse hangi jeton.
"""
from __future__ import annotations

import pathlib
import re

import pytest

KOK = pathlib.Path(__file__).resolve().parents[1]
WEB = KOK / "meridian" / "web"
BU_TEST = pathlib.Path(__file__).name

REFERANS = "index.html"
# KOPYA YÜZEYLER — referanstan jeton takımını AYNEN alanlar. `index.html` listede yok
# çünkü o karşılaştırmanın ÖLÇÜTÜ; kendisiyle karşılaştırmak boş bir yeşil olurdu.
KOPYALAR = ["landing.html", "workflow.html", "runbook.html"]
YUZEYLER = [REFERANS] + KOPYALAR

GUNDUZ_SEC = ":root"
GECE_SEC = ':root[data-theme="gece"]'

# EMEKLİ JETONLAR — geri gelirlerse sessizce ikinci bir sözlük doğar. `--pm-pos`/`--pm-neg`
# rol katmanı ÖNCESİNİN yön sözlüğüydü; D1'de yerlerini `--yon-arti-zemin`/`--yon-eksi-zemin`
# aldı ama iki yüzeyde emekli edilmeden kaldılar (D5'te silindi). Kayıt YASAK DEĞİL: yorumda
# "eskiden --pm-pos vardı" yazmak doğru ve kalıcı bir kayıttır — yasak olan BİLDİRİM.
EMEKLI = ("pm-pos", "pm-neg")

_HTML_YORUM = re.compile(r"<!--.*?-->", re.S)
_CSS_YORUM = re.compile(r"/\*.*?\*/", re.S)
_JETON = re.compile(r"--([a-zA-Z0-9-]+)\s*:\s*([^;}]+)")


def _oku(ad: str) -> str:
    p = WEB / ad
    assert p.is_file(), (
        f"{ad} YOK. Yüzey silindiyse bu testin kapsamı da güncellenmeli — sessizce "
        f"atlanan bir yüzey, ölçülmeyen bir yüzeydir.")
    return p.read_text(encoding="utf-8")


def _yorumsuz(kaynak: str) -> str:
    """HTML ve CSS yorumları TEMİZLENİR. Bkz. modül başlığı: sıyırmayan ayrıştırıcı,
    yorum metnindeki `--red:` gibi dizgeleri jeton sayar."""
    return _CSS_YORUM.sub(" ", _HTML_YORUM.sub(" ", kaynak))


def _bloklar(kaynak: str) -> list[tuple[str, str]]:
    """Yorumsuz kaynaktaki her `:root…{ … }` bloğu (seçici, gövde) olarak döner.

    Parantez SAYARAK kapanır, ilk `}`de durmaz: `:root` bloğu içine bir gün iç içe bir yapı
    (`@supports`, `&`) girerse blok yarıda kesilirdi ve eksik jeton kümesi YANLIŞ bir yeşil
    üretirdi — ayrışmayı ölçen bir testin kendi kör noktası olamaz."""
    css = _yorumsuz(kaynak)
    out: list[tuple[str, str]] = []
    for m in re.finditer(r"(:root[^{;]*?)\s*\{", css):
        i, derinlik, j = m.end(), 1, m.end()
        while j < len(css) and derinlik:
            if css[j] == "{":
                derinlik += 1
            elif css[j] == "}":
                derinlik -= 1
            j += 1
        assert derinlik == 0, f"kapanmamış {m.group(1)!r} bloğu — CSS bozuk"
        out.append((m.group(1).strip(), css[i:j - 1]))
    return out


def _jetonlar(govde: str) -> dict[str, str]:
    """Bildirimler → {ad: değer}. Değerin İÇ BOŞLUĞU normalize edilir (biçimlendirme farkı
    bir ayrışma değildir), ama başka hiçbir şey değişmez: `#FFF` ile `#ffffff` AYRI sayılır,
    çünkü iki yüzey aynı rengi iki farklı biçimde yazıyorsa bir sonraki `grep` onları
    bulamaz ve elle senkronizasyon zaten böyle kopar."""
    return {m.group(1): re.sub(r"\s+", " ", m.group(2)).strip()
            for m in _JETON.finditer(govde)}


def _tek_blok(ad: str, sec: str) -> dict[str, str]:
    eslesen = [g for s, g in _bloklar(_oku(ad)) if s == sec]
    assert len(eslesen) == 1, (
        f"{ad}: `{sec}` bloğu {len(eslesen)} adet, 1 bekleniyordu.\n"
        f"İKİ blok = iki gerçek kaynak: hangisinin kazandığı sıraya bağlı kalır ve bir "
        f"jeton güncellemesi sessizce yalnız birine iner. TEK gündüz + TEK gece bloğu.\n"
        f"(runbook.html 2026-08-07'ye kadar İKİ koşulsuz `:root` taşıyordu — biri "
        f"`@media (prefers-color-scheme: dark)` içinde, yani operatörün tema anahtarına "
        f"hiç bağlı değildi.)")
    return _jetonlar(eslesen[0])


REF_GUNDUZ = _tek_blok(REFERANS, GUNDUZ_SEC)
REF_GECE = _tek_blok(REFERANS, GECE_SEC)


def _ayrisma_raporu(ad: str, zemin: str, ref: dict, kendi: dict) -> str:
    eksik = sorted(set(ref) - set(kendi))
    fazla = sorted(set(kendi) - set(ref))
    ayrik = sorted(k for k in set(ref) & set(kendi) if ref[k] != kendi[k])
    if not (eksik or fazla or ayrik):
        return ""
    satir = [f"{ad} · {zemin} zemini {REFERANS} ile AYRIŞMIŞ "
             f"({len(kendi)} jeton, {REFERANS}'te {len(ref)}):"]
    if eksik:
        satir.append(f"  EKSİK ({len(eksik)}) — bu jetonu okuyan bir kural {ad} üzerinde "
                     f"TANIMSIZ değere düşer: " + " ".join("--" + k for k in eksik))
    if fazla:
        satir.append(f"  FAZLA ({len(fazla)}) — {REFERANS}'te karşılığı yok, yani bu yüzeye "
                     f"özel ikinci bir sözlük: " + " ".join("--" + k for k in fazla))
    for k in ayrik:
        satir.append(f"  AYRIK --{k}: {REFERANS}={ref[k]!r}  {ad}={kendi[k]!r}")
    satir.append(f"  ÇÖZÜM: değeri {REFERANS}'ten KOPYALA. Referans o dosyadır ve bir jeton "
                 f"gerçekten değişecekse DÖRT yüzeyde birden değişir.")
    return "\n".join(satir)


# ======================= Ç1 · JETON KÜMESİ VE DEĞERLERİ =======================

@pytest.mark.parametrize("ad", KOPYALAR)
def test_gunduz_jeton_takimi_referansla_BIREBIR(ad):
    """GÜNDÜZ `:root` — ad kümesi VE değerler `index.html` ile birebir aynı.

    Ayrışmanın bedeli soyut değil: operatör aynı ürünün iki sayfasında iki farklı zemin,
    iki farklı saç teli ve iki farklı mürekkep merdiveni görür. 2026-08-07'de gündüz
    zemininde 13 değer ayrıktı ve en görünürü `--bg` idi (#ffffff ↔ #fbf9f8)."""
    rapor = _ayrisma_raporu(ad, "GÜNDÜZ", REF_GUNDUZ, _tek_blok(ad, GUNDUZ_SEC))
    assert not rapor, rapor


@pytest.mark.parametrize("ad", KOPYALAR)
def test_gece_jeton_takimi_referansla_BIREBIR(ad):
    """GECE `:root[data-theme="gece"]` — ad kümesi VE değerler birebir aynı.

    Gece zemininde eksik jeton daha sinsidir: kural ÇALIŞIR ama gündüz değerini miras alır,
    yani koyu zeminde açık zeminin rengiyle çizer. `--nav-bg` vakası (üst bar gece temasında
    beyaz kalıp HALT kırmızısını 1.27:1'e düşürmüştü) tam olarak bu sınıftı."""
    rapor = _ayrisma_raporu(ad, "GECE", REF_GECE, _tek_blok(ad, GECE_SEC))
    assert not rapor, rapor


def test_dort_yuzey_ayni_jeton_SAYISINI_tasiyor():
    """Tek bakışta okunan özet: dördü de aynı iki sayıyı vermeli.

    Yukarıdaki iki test zaten daha güçlüsünü ölçüyor; bu satır ayrışmanın BÜYÜKLÜĞÜNÜ
    tek yerde raporlar, çünkü 40 jetonluk bir eksik ile tek jetonluk bir sapma aynı
    kırmızıyı verse de aynı arıza değildir."""
    sayim = {ad: (len(_tek_blok(ad, GUNDUZ_SEC)), len(_tek_blok(ad, GECE_SEC)))
             for ad in YUZEYLER}
    beklenen = sayim[REFERANS]
    sapan = {ad: s for ad, s in sayim.items() if s != beklenen}
    assert not sapan, (
        f"jeton sayısı ayrışmış (referans {REFERANS} = gündüz {beklenen[0]} · "
        f"gece {beklenen[1]}): {sapan}")


# ======================= Ç2 · BLOK DÜZENİ VE EMEKLİ ADLAR =======================

@pytest.mark.parametrize("ad", YUZEYLER)
def test_yuzeyde_tam_iki_root_blogu_var(ad):
    """Her yüzeyde TAM İKİ `:root` bloğu: bir gündüz + bir gece, başka yok.

    Üçüncü bir blok (ya da `@media` içine saklanmış ikinci bir gündüz) demek, aynı jetonun
    iki yerde tanımlanması demektir; biri güncellenir, öteki sessizce eskir."""
    secililer = [s for s, _ in _bloklar(_oku(ad))]
    assert secililer == [GUNDUZ_SEC, GECE_SEC], (
        f"{ad}: `:root` blokları {secililer} — beklenen tam olarak "
        f"[{GUNDUZ_SEC!r}, {GECE_SEC!r}] (bu sırayla; gece bloğu gündüzü EZER).")


@pytest.mark.parametrize("ad", YUZEYLER)
def test_emekli_jetonlar_geri_gelmemis(ad):
    """`--pm-pos` / `--pm-neg` BİLDİRİMİ hiçbir yüzeyde olmamalı.

    Bu ikisi rol katmanı öncesinin yön sözlüğüydü. D1 index.html'te yerlerine
    `--yon-arti-zemin`/`--yon-eksi-zemin` koydu; landing ve workflow'da emekli edilmediler
    ve 2026-08-07'ye kadar aynı ürünün iki yüzeyi K/Z işaretini İKİ FARKLI sözlükten
    boyadı. Ölçülen şey BİLDİRİM: yorumdaki tarihsel kayıt serbesttir ve kalmalıdır."""
    kaynak = _yorumsuz(_oku(ad))
    for isim in EMEKLI:
        assert not re.search(rf"--{isim}\s*:", kaynak), (
            f"{ad}: emekli jeton `--{isim}` yeniden bildirilmiş. Yön rolü "
            f"`--yon-arti`/`--yon-eksi` (+ `-zemin`) ile taşınır.")
        assert f"var(--{isim})" not in kaynak, (
            f"{ad}: emekli jeton `--{isim}` bir kuralda okunuyor — tanımı silinmişse bu "
            f"kural TANIMSIZ değere düşer.")


# ======================= Ç3 · TAKIMIN ÇALIŞMASI İÇİN GEREKENLER =======================

@pytest.mark.parametrize("ad", YUZEYLER)
def test_gece_blogunu_kim_acacak_theme_js_YUKLU(ad):
    """`:root[data-theme="gece"]` seçicisi `theme.js` olmadan HİÇ eşleşmez.

    Bu, jeton takımını kopyalamanın sessiz bedeli olabilirdi: doğru değerler, hiç
    çalışmayan bir blok. `data-theme` niteliğini kuran tek yer `theme.js`tir; yüklenmezse
    sayfa sonsuza kadar gündüz zemininde kalır ve kimse fark etmez (renkler DOĞRUdur,
    yalnız yanlış zemindedir). runbook.html 2026-08-07'ye kadar `theme.js` yüklemiyordu ve
    gecesini `@media (prefers-color-scheme: dark)` ile çiziyordu — yani operatör panoda
    gündüzü seçtiyse bile, sistemi karanlıksa runbook karanlık açılıyordu."""
    kaynak = _yorumsuz(_oku(ad))
    assert re.search(r'<script[^>]+src=["\']/theme\.js["\']', kaynak), (
        f"{ad}: `/theme.js` yüklenmiyor ama gece bloğu `[data-theme=\"gece\"]` seçicisine "
        f"bağlı — o blok ÖLÜ. Ya betiği yükle ya da gece zeminini nasıl açtığını söyle.")


@pytest.mark.parametrize("ad", YUZEYLER)
def test_mono_jetonunun_yuzu_GERCEKTEN_yukleniyor(ad):
    """`--mono` 'Recursive Mono' diyorsa o aile `@font-face` ile TANIMLI olmalı.

    Bir jetonun değerini kopyalamak, adlandırdığı yüzü yüklemez. runbook.html 2026-08-07'ye
    kadar `--mono`yu HİÇ yüklemiyordu (kendi `ui-monospace` yığınına düşüyordu), yani
    `docs/RUNBOOK.md`nin komutları ve jeton adları panodakinden BAŞKA bir yüzle çiziliyordu.
    Değer eşitliği bu arızayı GÖRMEZ — bu yüzden ayrı bir çivi.
    (Yazı tipi sözleşmesinin tamamı `tests/test_yazitipi_v201.py`de; burada ölçülen tek şey
    `--mono` jetonu ile yüklenen aile arasındaki bağ.)"""
    kaynak = _yorumsuz(_oku(ad))
    mono = _tek_blok(ad, GUNDUZ_SEC).get("mono", "")
    aile = re.match(r"['\"]([^'\"]+)['\"]", mono)
    assert aile, f"{ad}: --mono bir aile adıyla başlamıyor: {mono!r}"
    bloklar = re.findall(r"@font-face\s*\{(.*?)\}", kaynak, re.S)
    tanimli = [b for b in bloklar if aile.group(1) in b]
    assert tanimli, (
        f"{ad}: --mono {aile.group(1)!r} diyor ama o aile için `@font-face` YOK — tarayıcı "
        f"sessizce yedeğe (ui-monospace) düşer ve sayfa başka bir yüzle çizilir.")
    for b in tanimli:
        src = re.search(r"src\s*:\s*url\(['\"]?([^'\")]+)", b)
        assert src and src.group(1).startswith("/fonts/"), (
            f"{ad}: {aile.group(1)!r} @font-face src yerel değil ({src and src.group(1)!r}). "
            f"CSP `font-src 'self'` — dış origin ÜRETİMDE bloklanır.")


# ======================= Ç4 · İDDİANIN KENDİSİ =======================

@pytest.mark.parametrize("ad", KOPYALAR)
def test_kopya_yuzey_bu_TESTE_isaret_ediyor(ad):
    """Her kopya yüzey, takımı neyin koruduğunu SÖYLEMELİ — bu dosyanın adıyla.

    YASA: bir iddia ancak onu koruyan bir test varsa yazılabilir. Bu depoda tam tersi
    yaşandı — landing.html "üçünde birden değişir" diye YAZDI, kimse ölçmedi, ve üç yüzey
    ayrıştı. İşaretçi çift yönlü bir kilittir: test silinir ya da yeniden adlandırılırsa
    yorum bayatlar ve bu satır kırmızı yanar; yorum silinirse takımın neden kopyalandığını
    okuyacak kimse kalmaz (YASA 6: okuyucusuz yazım yok)."""
    assert BU_TEST in _oku(ad), (
        f"{ad}: jeton takımının neden {REFERANS}'ten kopyalandığını ve onu neyin koruduğunu "
        f"söyleyen kayıt yok. Blok yorumunda `{BU_TEST}` geçmeli.")


def test_ayristirici_YORUMU_JETON_SANMIYOR():
    """ÖLÇÜM ARACININ KENDİ ÇİVİSİ — ve bu bir paranoya değil, iki kez yaşanmış bir vaka.

    Bu deponun yüzeylerinde `:root` bloklarının çevresi uzun gerekçelerle doludur ve o
    gerekçeler jeton adları İÇERİR ("bu satır eskiden --red:#f2555a diyordu"). Yorumları
    sıyırmayan bir ayrıştırıcı onları bildirim sanar; sonuç sahte bir AYRIK raporu ya da —
    çok daha kötüsü — sahte bir yeşildir. HTML ve CSS yorumu AYRI AYRI sınanır, çünkü
    yalnız birini temizleyen bir düzenleme tam olarak bu kapıdan geçerdi."""
    sahte = """
    <!-- burada --sahte-html:#ff0000; yazıyor ama bu bir YORUM -->
    <style>
    /* eskiden --sahte-css:#00ff00; idi */
    :root{ --gercek:#123456; /* --sahte-ic:#0000ff; */ --gercek2:2px; }
    </style>
    """
    bloklar = _bloklar(sahte)
    assert len(bloklar) == 1, f"blok sayısı {len(bloklar)}"
    assert _jetonlar(bloklar[0][1]) == {"gercek": "#123456", "gercek2": "2px"}, (
        "ayrıştırıcı yorum içindeki metni jeton saydı — bu araçla yapılan HER ölçüm şüpheli")

"""test_tasarim_dili_tutarliligi_v285.py — TEK TASARIM DİLİ, HER YÜZEYDE (2026-08-24).

NEDEN BU DOSYA VAR — operatörün cümlesi:
    "bütün UI'da tasarım dili consistent olmalının nesini anlamıyorsun ve her seferinde
     benim eksik birşeyleri göstermem gerekiyor"

Haklıydı ve teşhis bu cümlenin içindeydi: eksikler tek tek EKRAN GÖRÜNTÜSÜYLE bildiriliyordu,
yani tutarlılığın bekçisi operatörün gözüydü. Bu dosya o işi devralır. Dub dönüşümü boyunca
altı ayrı tur "şurası da eski kalmış" ile geçti; her turda bir kural düzeldi ve BİR SONRAKİ
sürüklenme yine görülmedi çünkü ölçen yoktu.

SÖZLEŞME — altı boyut, hepsi MAKETTEN (`scratch-panov2/index.html`) türetildi:
  1. PUNTO      yalnız rampa jetonları (--t-cap/body/lg/sub/h/num · --label-size) ya da clamp()
  2. YARIÇAP    yalnız --r-* jetonları (Dub: 6 · 8 · 12 · 16 · 9999 + grafik çubuğu --r-bar)
  3. AĞIRLIK    yalnız 400/500/600/700 (yüklü kesit `wght 400 700`; dışı SENTETİK olurdu)
  4. ARALIK     ≤ .06em — maketin etiket değeri .04em; .16em emekli Omega'nın imzasıydı
  5. SAÇ TELİ   TEK jeton. Maket 22 kenarın 21'inde `--ash` kullanıyor; bizde `--line` ve
                `--line-2` neredeyse yarı yarıya bölüşüyordu (60/45) — çerçevelerin farklı
                görünmesinin ÖLÇÜLEN sebebi buydu.
  6. KESİK ÇERÇEVE  yok. "geçici/taslak" jestiydi; Dub'da karşılığı yumuşak tint çiptir.

MUAFİYETLER — ihlal DEĞİL, ve her biri gerekçeli:
  · `@font-face` bloğu: `font-family:'Inter'` ve `font-weight:400 700` orada ZORUNLU sözdizimi.
  · `text-decoration: … dashed`: ANLAMSAL bir işaret (`.belirsiz` = ölçülemeyen değer),
    çerçeve değil. Kesik çerçeve yasağı KABA uygulanırsa bu anlamı da siler.
  · `clamp(...)`: rampa jetonlarını taban/tavan olarak kullanan duyarlı boy — rampanın ihlali
    değil, uygulaması.
"""
from __future__ import annotations

import collections
import pathlib
import re

import pytest

KOK = pathlib.Path(__file__).resolve().parents[1] / "meridian" / "web"
YUZEYLER = ["index.html", "landing.html", "workflow.html", "runbook.html", "app.js", "palette.js"]

RAMPA_PX = {"11px", "14px", "17px", "20px", "24px", "30px", "10px"}
PUNTO_JETON = {"var(--t-cap)", "var(--t-body)", "var(--t-lg)", "var(--t-sub)", "var(--t-h)",
               "var(--t-num)", "var(--label-size)", "inherit", "0"}
YARICAP_TAMAM = {"9999px", "0", "50%", "inherit"}
AGIRLIK = {"400", "500", "600", "700", "inherit", "normal", "bold"}
ARALIK_TAVANI_EM = 0.06


def _kod(ad: str) -> list[str]:
    """Yorumsuz gövde, SATIR NUMARASI KORUNARAK. Bir kuralın GEREKÇESİNİ anlatan yorum
    (ör. '~~.16em~~ emekliydi') o kuralın ihlali sanılmamalı — bu deponun tekrar eden tuzağı."""
    ham = (KOK / ad).read_text()
    s = re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), ham, flags=re.S)
    if ad.endswith(".html"):
        s = re.sub(r"<!--.*?-->", lambda m: re.sub(r"[^\n]", " ", m.group(0)), s, flags=re.S)
    return s.split("\n")


def _tara() -> dict[str, list[str]]:
    ihlal: dict[str, list[str]] = collections.defaultdict(list)
    for ad in YUZEYLER:
        if not (KOK / ad).exists():
            continue
        ff = 0
        for i, satir in enumerate(_kod(ad), 1):
            if "@font-face" in satir:
                ff = 6
            if ff > 0:
                ff -= 1
                continue
            for m in re.finditer(r"font-size:\s*([^;}\"']+)", satir):
                v = m.group(1).strip()
                if v.startswith("clamp(") or v in PUNTO_JETON:
                    continue
                ihlal["punto"].append(f"{ad}:{i} → {v}")
            for m in re.finditer(r"border-radius:\s*([^;}\"']+)", satir):
                v = m.group(1).strip()
                if v.startswith("var(") or v in YARICAP_TAMAM:
                    continue
                ihlal["yaricap"].append(f"{ad}:{i} → {v}")
            for m in re.finditer(r"font-weight:\s*([^;}\"']+)", satir):
                v = m.group(1).strip()
                if v not in AGIRLIK:
                    ihlal["agirlik"].append(f"{ad}:{i} → {v}")
            for m in re.finditer(r"letter-spacing:\s*(-?\.?[0-9.]+)em", satir):
                if float(m.group(1)) > ARALIK_TAVANI_EM:
                    ihlal["aralik"].append(f"{ad}:{i} → {m.group(0)}")
            if "dashed" in satir and "text-decoration" not in satir:
                ihlal["kesik"].append(f"{ad}:{i}")
            if re.search(r"1px solid var\(--line-2\)", satir):
                ihlal["sac_teli"].append(f"{ad}:{i}")
            if re.search(r"font-family:\s*(?!var\(|inherit)", satir):
                ihlal["font_ailesi"].append(f"{ad}:{i}")
    return ihlal


_IHLAL = _tara()


def _bildir(anahtar: str, cumle: str) -> None:
    v = _IHLAL.get(anahtar, [])
    assert not v, (f"{cumle}\n  {len(v)} ihlal:\n    " + "\n    ".join(v[:25])
                   + ("\n    …" if len(v) > 25 else ""))


def test_punto_yalniz_rampadan():
    """Ölçek yarıdan fazla baypas ediliyordu (165 sert punto ↔ 121 jeton kullanımı, ölçüldü
    2026-08-24). Sert bir punto rampada OLSA BİLE ihlaldir: rampa tek yerden yönetilemezse
    bir sonraki ayar 165 yeri tek tek dolaşmak demektir."""
    _bildir("punto", "PUNTO RAMPA DIŞI ya da jetona bağlı değil")


def test_yaricap_yalniz_jetondan():
    _bildir("yaricap", "YARIÇAP jetona bağlı değil (Dub rampası: 6 · 8 · 12 · 16 · 9999)")


def test_agirlik_yuklu_kesitin_icinde():
    """Yüklü kesit `wght 400 700`. Dışındaki bir ağırlık tarayıcıya SENTETİK kalın ürettirir —
    ve sentetik yüz, operatörün 'yazı tipleri farklı' dediği sınıfın ta kendisidir."""
    _bildir("agirlik", "AĞIRLIK yüklü kesidin dışında")


def test_harf_araligi_dub_bandinda():
    """`--label-track` .16em'di ve maketin değeri .04em. Dört katı genişlik, emekli Omega'nın
    'seyreltilmiş büyük harf' sesiydi ve eski dilin EN GÖRÜNÜR parçasıydı."""
    _bildir("aralik", f"HARF ARALIĞI {ARALIK_TAVANI_EM}em tavanının üstünde")


def test_TEK_sac_teli():
    """Maket 22 kenarın 21'inde tek jeton (`--ash`) kullanıyor. Bizde `--line` ve `--line-2`
    60/45 bölüşüyordu — operatörün 'çerçeveler de farklı' gözleminin ölçülen sebebi."""
    _bildir("sac_teli", "İKİNCİ SAÇ TELİ (`--line-2`) bir kenarda kullanılmış")


def test_kesik_cerceve_yok():
    """Kesik çerçeve 'geçici/taslak' jestiydi; taşıdığı şeyler (AZ ÖRNEK · SERMAYE-RESET)
    geçici değil KALICI ölçüm beyanlarıydı. Dub karşılığı yumuşak tint çiptir."""
    _bildir("kesik", "KESİK ÇERÇEVE (`dashed`) — `text-decoration` muaf")


def test_sert_font_ailesi_yok():
    """`@font-face` dışında hiçbir yerde jeton olmayan `font-family` olamaz. `<button>` ve form
    öğeleri font KALITMAZ: bir etiket kuralından `--mono` alındığında UA varsayılanına (Arial)
    düşerler — 2026-08-24'te tam bu oldu ve yedi öğe Arial'e kaçtı."""
    _bildir("font_ailesi", "SERT FONT AİLESİ (`@font-face` dışında)")


def test_dugmeler_font_kalitiyor():
    """Yukarıdaki Arial kaçağının KÖK çözümü: sıfırlayıcıda tek satır. Kural başına yama
    yapılsaydı bir sonraki düğme yine kaçardı."""
    for ad in ("index.html", "landing.html", "workflow.html", "runbook.html"):
        s = (KOK / ad).read_text()
        assert "button,input,select,textarea{font-family:inherit" in s, (
            f"{ad}: düğme/form font kalıtımı sıfırlayıcıda YOK — bir etiket kuralı mono'yu "
            f"bıraktığı an o düğme Arial'e düşer ve kimse görmez")


# ---------------------------------------------------------------------------
# 7. RENK — canlı literal YOK (D1, 2026-08-24)
# ---------------------------------------------------------------------------
_YORUM_BLOK = re.compile(r"/\*.*?\*/|<!--.*?-->", re.S)
_SATIR_YORUM = re.compile(r"^\s*//.*$", re.M)
_RENK = re.compile(r"#[0-9a-fA-F]{3,8}\b|rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+")
_JETON_BILDIRIMI = re.compile(r"--[a-z0-9-]+\s*:")


def _canli_renk_literalleri(ad: str) -> list[tuple[int, str, str]]:
    """Yorumları ve jeton BİLDİRİMLERİNİ çıkardıktan sonra kalan renk literalleri.

    Yorumlar muaf çünkü ölçüm kaydı ve üstü-çizili tarih orada yaşıyor (SİLME YOK).
    Jeton bildirim satırları muaf çünkü paletin TANIMLANDIĞI yer orasıdır — yasak,
    paletin dışında renk ÜRETMEK.
    """
    ham = (KOK / ad).read_text()
    temiz = _YORUM_BLOK.sub(lambda m: "\n" * m.group(0).count("\n"), ham)
    temiz = _SATIR_YORUM.sub("", temiz)
    return [(i, m.group(0), s.strip()[:100])
            for i, s in enumerate(temiz.split("\n"), 1)
            if not _JETON_BILDIRIMI.search(s)
            for m in _RENK.finditer(s)]


@pytest.mark.parametrize("ad", YUZEYLER)
def test_canli_renk_literali_YOK(ad):
    """Renk YALNIZ jeton katmanından gelir — kural başına hex yazılamaz.

    NEDEN: Dub dönüşümünde operatör dört ayrı turda "bu renkler neden Dub değil" dedi.
    Sürüklenmenin mekanizması hep aynıydı — bir renk jeton katmanının DIŞINDA yaşayınca
    palet güncellendiğinde geride kalıyor ve hiçbir şey fark etmiyor. Bu çivi indiğinde
    dört yüzeyin dördü de ZATEN temizdi (ölçüldü: 0/0/0/0); yani bu bir düzeltme değil,
    bir MANDAL — kazanılan temizlik geri verilemez.

    Türevler de (saç teli .35, tint .10/.08) jeton olmak zorunda: D1'de taban değişti,
    türevler eski RGB'de kaldı ve 48 türev elle yeniden türetildi. Jeton olsalardı
    tek satır yeterdi.
    """
    kacak = _canli_renk_literalleri(ad)
    assert not kacak, (
        f"{ad}: jeton katmanının DIŞINDA {len(kacak)} renk literali — palet güncellenince "
        f"bunlar geride kalır ve kimse görmez:\n" +
        "\n".join(f"    satır {i}: {d}  ← {s}" for i, d, s in kacak[:10]))


# ---------------------------------------------------------------------------
# 8. YARIM GÖÇ MANDALLARI (2026-08-24) — operatörün gözü yerine test
# ---------------------------------------------------------------------------
# Altı boyutlu denetimin hükmü: "Pano tutarsız değil, YARIM GÖÇ halinde." Aynı karar bir
# eksende uygulanıp komşu eksende uygulanmamış, aynı bileşen üç paralel uygulamada yaşamış,
# emekli gerekçeler çizilmeden yürürlükte kalmış. Aşağıdaki mandallar o mekanizmaları
# tek tek kapatır — hepsi indiği anda ZATEN geçiyordu; bunlar düzeltme değil, GERİ ALINAMAZLIK.

def _kural(metin: str, secici: str) -> str | None:
    """`secici{...}` kuralının gövdesi (ilk eşleşme)."""
    m = re.search(r"(?<=\n)" + re.escape(secici) + r"\{([^{}]*)\}", metin)
    return m.group(1) if m else None


@pytest.mark.parametrize("ad", ["index.html", "landing.html"])
def test_T1_hucre_icerigi_dikey_ORTALANMAZ(ad):
    """Çok satırlı hücrede dikey ortalama, VERİ farkını HİZA farkına çevirir.

    Ölçülen vaka (2026-08-24): bir özet şeridinde 1. ve 3. hücre `AZ ÖRNEK` rozeti alıyor,
    2. ve 4. almıyor. Izgara hücreleri eşit YÜKSEKLİĞE gerilir; içerik ortalanınca rozetli
    hücrenin başlığı yukarı, rozetsizinki aşağı kayar. Operatör bunu ekran görüntüsüyle
    "yazılar birbiri ile align olmamış" diye bildirmek zorunda kaldı.
    Maketin iki dosyasında da hücre kuralında `justify-content` SIFIR kez geçiyor.
    """
    g = _kural((KOK / ad).read_text(), ".pm-cell")
    assert g is not None, f"{ad}: .pm-cell kuralı bulunamadı"
    assert "justify-content" not in g, (
        f"{ad}: .pm-cell dikey hizalama bildiriyor — bir hücrede bir katman doğmadığında "
        f"komşusunun başlığı kıpırdar. Eşit yükseklik kaptan gelir, eşit hiza içerikten.")


@pytest.mark.parametrize("ad", ["index.html", "landing.html"])
def test_T2_etiket_deger_mesafesi_TEK_kanaldan(ad):
    """Kap `gap` verirse, marj taşıyan öğede iki değer TOPLANIR ve mesafe sessizce çatallanır.

    Ölçülen: `.pm-sectlabel` marjı (4px) + `.pm-cell` gap'i (5px) = 9px, ve bu 9 hiçbir
    jetonda yazılı değildi. Makette hiçbir hücre kabında `gap` yok; mesafe her zaman
    öğenin KENDİ `margin`ından gelir.
    """
    g = _kural((KOK / ad).read_text(), ".pm-cell")
    assert "gap:" not in g, (
        f"{ad}: .pm-cell `gap` bildiriyor — mesafe iki kanaldan gelir ve toplanır")


@pytest.mark.parametrize("ad", ["index.html", "landing.html", "workflow.html", "runbook.html"])
def test_T3_tanimsiz_jeton_YOK(ad):
    """Kullanılan her `var(--x)` aynı dosyada tanımlı olmalı. Tanımsız jeton SESSİZ düşer.

    Ölçülen vaka: `--r-md` tek yerde kullanılıyordu, dört jeton bloğunun DÖRDÜNDE de tanımı
    yoktu; yarıçap sessizce 0'a düşüyor ve 16px'lik bir kabın içinde kare köşeli ikinci
    çerçeve duruyordu. Hiçbir test görmüyordu çünkü CSS geçersiz bildirimi yutar.
    """
    ham = (KOK / ad).read_text()
    # YORUMLAR SOYULUR: Meridian yorumları maketin kurallarını BİREBİR alıntılar
    # (`.kart > h2{…color:var(--fog)…}`) ve maket jetonu bizde tanımlı değildir —
    # alıntı bir kullanım değildir. Soyulmazsa çivi kendi belge geleneğini suçlar.
    s = _YORUM_BLOK.sub("", ham)
    tanimli = set(re.findall(r"(--[a-z0-9-]+)\s*:", s))
    # ÇALIŞMA ZAMANINDA YAZILAN JETONLAR: app.js bazılarını ölçüp `setProperty` ile yazar
    # (`--navh` nav'ın gerçek yüksekliği, `--conf`/`--fill`/`--kmc` hücre doluluğu). Bunlar
    # CSS'te tanımlı DEĞİL ama tanımsız da değil — yazarı JS.
    js = (KOK / "app.js").read_text()
    tanimli |= set(re.findall(r'setProperty\(\s*"(--[a-z0-9-]+)"', js))
    tanimli |= set(re.findall(r"(--[a-z0-9-]+)\s*:\s*\$\{", js))   # satır içi style şablonu
    eksik = sorted(re.findall(r"var\(\s*(--[a-z0-9-]+)", s))
    eksik = sorted({j for j in eksik if j not in tanimli})
    assert not eksik, (
        f"{ad}: tanımsız jeton kullanılıyor — CSS geçersiz bildirimi YUTAR, kural sessizce "
        f"düşer ve hiçbir şey haber vermez: {eksik}")


def test_T4_dortlu_sayisal_band_TEK_gramerde():
    """Bugün'de iki 4'lü band emisyonda BİTİŞİK; ikisi aynı gramerde okunmalı.

    Operatör: "çerçeveler birinde oval diğerinde birleşik kare". Ölçüldü ve haklıydı —
    üst band boşluklu ızgarada çerçeveli+yuvarlak mini-kart, alt band paylaşılan kenarlı
    kapalı kap kullanıyordu. Maket 4'lü sayısal bandı TEK biçimde yazar (yedi blok kabının
    yedisinde aynı): kapalı kap + `overflow:hidden`, hücrede paylaşılan kenar, `gap:0`,
    hücrede yarıçap YOK. Boşluklu ızgarada kendi çerçevesi olan mini-kart maket sözlüğünde
    SIFIR kez geçiyor.
    """
    s = (KOK / "index.html").read_text()
    for kap, izgara, hucre in ((".durum-izgara-kap", ".durum-izgara", ".durum-kart"),
                               (".pv-para", ".pv-sekmeler", ".pv-sekme")):
        gk, gi, gh = _kural(s, kap), _kural(s, izgara), _kural(s, hucre)
        assert gk and gi and gh, f"{kap}/{izgara}/{hucre}: kural eksik"
        assert "overflow:hidden" in gk, f"{kap}: kap taşmayı kırpmıyor — paylaşılan kenar köşeden taşar"
        assert "var(--r-card)" in gk, f"{kap}: blok kap yarıçapı --r-card değil"
        assert "gap:var(--s" not in gi, f"{izgara}: boşluklu ızgara — band iki gramere ayrılır"
        assert "border-right:1px solid var(--line)" in gh, f"{hucre}: hücreler paylaşılan kenarla bölünmüyor"
        assert "border-radius:0" in gh or "border-radius" not in gh, \
            f"{hucre}: hücre kendi yarıçapını taşıyor — kapalı kabın içinde mini-kart olur"


# ÇİP = okunacak bir HÂL taşır. Tıklanan şey çip değil DÜĞMEdir ve düğmenin yarıçapı
# `--r-ctl`dir — `.halt` (cursor:pointer + transition), `.gate-btn`, `.pv-gbtn`,
# `.pd-x`, `.kscover`, `.gate-tls`, `.logo i` bu yüzden listede YOK.
CIP_KATMANI = [".statuspill", ".tag", ".st", ".lv", ".hudchip", ".gc", ".pm-thin",
               ".pillc", ".pv-damga", ".pv-rz"]
KONTROL_KATMANI = {".gate-btn", ".gate-tls", ".logo i", ".halt", ".pd-x",
                   ".kscover", ".pv-gbtn", ".pv-mgrup"}


def test_T8_cip_yaricapi_HAP_ve_r_ctl_yalniz_kontrolde():
    """Çip hap'tır (`--r-tag`), düğme değil. `--r-ctl` (8px) KONTROL katmanının yarıçapıdır.

    Yarım göçün en görünür izi buydu: karar §10.2 çipi Dub "feature pill" gramerine bağladı,
    ama `.tag`/`.st`/`.gc` düğme yarıçapında kaldı çünkü 16 satır aşağıdaki "never a soft
    pill" gerekçesi ÜSTÜ ÇİZİLMEDEN yürürlükte bırakılmıştı.
    """
    s = (KOK / "index.html").read_text()
    for c in CIP_KATMANI:
        g = _kural(s, c)
        if g is None or "border-radius" not in g:
            continue
        assert "var(--r-ctl)" not in g, f"{c}: çip düğme yarıçapı (--r-ctl) taşıyor — hap değil"
    # `--r-ctl` YALNIZ kontrol katmanında kalsın (izin listesi ölçümle sabit)
    kullanan = {m.group(1).strip() for m in
                re.finditer(r"(?<=\n)([^\n{}]+)\{[^{}]*var\(--r-ctl\)", s)}
    assert kullanan <= KONTROL_KATMANI, (
        f"--r-ctl kontrol katmanının DIŞINDA kullanılıyor: {sorted(kullanan - KONTROL_KATMANI)} — "
        f"8px düğme yarıçapıdır; okunacak bir hâl taşıyan şey hap (--r-tag) olmalı")


def test_T9_cip_agirligi_TEK_ve_aile_MIRAS_ALMAZ():
    """Vurgu RENKLE taşınır, KALINLIKLA değil — tek ağırlık (500).

    Ayrıca aile MİRAS ALINAMAZ: `.tag` aile bildirmediği için bir bağlamda mono, başka
    bağlamda sans render ediyordu. Mono bir SEMANTİKTİR (sayı ve makine dizgesi), çipin
    kelimesi değil.
    """
    s = (KOK / "index.html").read_text()
    for c in CIP_KATMANI:
        g = _kural(s, c)
        if g is None:
            continue
        m = re.search(r"font-weight:\s*(\d+)", g)
        if m:
            assert m.group(1) == "500", f"{c}: çip ağırlığı {m.group(1)} — çip katmanında tek ağırlık 500"
        assert "font-family:var(--mono)" not in g, (
            f"{c}: çip mono — mono yalnız sayı ve makine dizgesinin yüzüdür")

"""v315 · KORUMA HÜKMÜNÜN OKUYUCUSU YOK — pano NVDA'nın korumasızlığını göstermiyor.

ÖLÇÜLEN ZEMİN (canlı A1 kâğıt hesap, 2026-08-25): aynada dokuz pozisyon var, sekizinde
canlı `held` stop emri duruyor, NVDA'da HİÇ YOK. `alpaca.dashboard_view` bu turda pozisyon
başına koruma hükmü üretmeye başladı (`koruma`, `koruma_neden`) ve emir listesinin kırpma
muhasebesini de yazdı (`open_orders_kirpma`, `open_orders_neden`). BEŞ ALANIN BEŞİNİN DE
OKUYUCUSU YOKTU — hepsi yalnız `meridian/adapters/alpaca.py` içinde geçiyordu (YASA 6).

Pano yüzeyi bu boşluğu KAPATAMAZDI çünkü tek ilgili kart ("Aynadaki açık emirler") EMİRLERİ
listeler, POZİSYONLARI değil: NVDA'nın hiç canlı emri olmadığı için o kartta zaten bir satırı
yoktu. Korumasızlık, tanım gereği, emir listesinde GÖRÜNMEYEN şeydir.

BU DOSYA NEYİ ÇİVİLER
---------------------
A. ÜÇ KORUMA HÂLİ ÜÇ AYRI ÇİZİM. `korumali` / `korumasiz` / `olculemedi` dallarının
   gövdeleri ikişer ikişer FARKLI, ve ayrımı taşıyan işaretler dala özgü: yalnız
   `korumasiz` kırmızı (`variant="destructive"`), yalnız `olculemedi` `<Olculemedi>`
   bileşenine düşer, yalnız `korumali` fiyat basar. "koruma yok" ile "ölçülemedi" aynı
   rozeti ALMAZ — bu turun üç kez tekrarlanan dersi.
B. HÜKÜM DİZGELERİ GÖVDEYLE AYNI. TSX'teki üç sabit, `alpaca.py`deki
   `KORUMA_VAR/KORUMA_YOK/KORUMA_OLCULEMEDI` ile BİREBİR — dizge kayarsa üç dal da sessizce
   ölür ve ekran "hüküm tanınmadı" der. Çivi iki dosyayı birbirine bağlar.
C. KIRPMA GÖVDEDEN OKUNUR, ELLE YAZILMAZ. `tavan/canli/kirpilan/pencere_doygun` dördü de
   okunur; ve `_PANO_EMIR_TAVANI` ile `_PANO_EMIR_PENCERESI` sayıları TSX'te ARAMAZ —
   className dışında iki basamaklı hiçbir sabit sayı kalmaz. (Bayat metin "en çok 20 satır"
   diyordu; tavan artık gövdenin söylediği sayı.)
D. `pencere_doygun` OKUYUCUSU. Doygun dalı "TAM DEĞİL" cümlesini kurar — kırpılmamış bir
   listenin "hepsi bu" olduğu ancak pencere doymamışken KANITLANIR.
E. `open_orders` ÜÇ HÂLİ. `null` (okunamadı) dalı gövdenin `open_orders_neden` alanını
   OKUR; `[]` dalı ayrıdır ve "ölçülmüş olgu" der. Tipler her iki dosyada da `null`a izin
   verir — vermezse derleyici `null` dalını ölü kod sanır.
F. SATIR ÇAPASI YOK. Üç dosyada da `dosya.py:NNN` biçimi kalmaz (bu turun sözleşmesi).

ALT-DİZGE TUZAĞI: bütün çiviler YORUMLARI SİLİNMİŞ kaynak üzerinde koşar. Bu dosyanın
kapattığı kusurun gerekçeleri kaynağın kendi yorumlarında da geçiyor ("koruma YOK",
"ölçülemedi", "pencere_doygun"); yorumlu metinde arama yapmak, silinmiş bir davranışı
mezar taşı yüzünden yaşıyor sanmak olurdu.
"""
from __future__ import annotations

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[1]
UI = REPO / "ui" / "src" / "pano" / "yuzeyler"
EMIR_YOLU = UI / "portfoy" / "SeansIciEmir.tsx"
TIPLER_YOLU = UI / "portfoy" / "tipler.ts"
UCTIPLERI_YOLU = UI / "kimlik" / "uctipleri.ts"
ALPACA_YOLU = REPO / "meridian" / "adapters" / "alpaca.py"

HAM = EMIR_YOLU.read_text(encoding="utf-8")
TIPLER_HAM = TIPLER_YOLU.read_text(encoding="utf-8")
UCTIPLERI_HAM = UCTIPLERI_YOLU.read_text(encoding="utf-8")
ALPACA_HAM = ALPACA_YOLU.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# YORUM SOYUCU — çivilerin ölçtüğü metin KOD olmalı, mezar taşı değil
# ---------------------------------------------------------------------------
def _blok_yorumsuz(src: str) -> str:
    """`/* ... */` bloklarını AYNI SATIR SAYISINI koruyarak siler (JSX `{/* */}` dahil).

    Satır sayısı korunuyor ki hata mesajındaki bağlam ham dosyayla hizalı kalsın."""
    return re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), src, flags=re.DOTALL)


def _yorumsuz(src: str) -> str:
    """Blok yorumları siler, ardından SATIR BAŞI `//` yorum satırlarını atar.

    NEDEN SATIR-SONU `//` TARANMIYOR: JSX metni tırnaksız kesme işareti taşıyabiliyor;
    "dizgileri maskele sonra `//` ara" deseni kaynağı BOZAR. Bunun yerine
    `test_soyucu_hala_gecerli` satır-sonu yorumu OLMADIĞINI doğruluyor; bir gün eklenirse
    o çivi öter ve soyucu bilerek sertleştirilir."""
    return "\n".join(ln for ln in _blok_yorumsuz(src).splitlines() if not ln.lstrip().startswith("//"))


KOD = _yorumsuz(HAM)
TIPLER = _yorumsuz(TIPLER_HAM)
UCTIPLERI = _yorumsuz(UCTIPLERI_HAM)


def _classname_siz(src: str) -> str:
    """`className="…"` ve `className={…}` değerlerini siler.

    Tailwind sınıfları sayı doludur (`text-[11px]`, `gap-2`, `size-3.5`); "elle yazılı sayı
    var mı" çivisi onları sayarsa HER dosyada öter ve hiçbir şey ölçmez."""
    out: list[str] = []
    i = 0
    while True:
        m = re.search(r"className=", src[i:])
        if not m:
            out.append(src[i:])
            break
        bas = i + m.start()
        out.append(src[i:bas])
        j = i + m.end()
        if j < len(src) and src[j] == '"':
            k = src.index('"', j + 1)
            i = k + 1
        elif j < len(src) and src[j] == "{":
            d = 0
            k = j
            while k < len(src):
                if src[k] == "{":
                    d += 1
                elif src[k] == "}":
                    d -= 1
                    if d == 0:
                        break
                k += 1
            i = k + 1
        else:
            i = j
    return "".join(out)


def _kume(kaynak: str, bas: int) -> str:
    """`bas` konumundan SONRAKİ ilk `{`ten başlayıp dengeli kapanışına kadar olan dilim."""
    j = kaynak.index("{", bas)
    d = 0
    for k in range(j, len(kaynak)):
        if kaynak[k] == "{":
            d += 1
        elif kaynak[k] == "}":
            d -= 1
            if d == 0:
                return kaynak[j : k + 1]
    raise AssertionError("dengeli küme parantezi bulunamadı")


def _fonksiyon(ad: str) -> str:
    """Fonksiyonun GÖVDESİ — parametre listesi ATLANIR.

    Düz `_kume(KOD, m.end())` React bileşenlerinde YANLIŞ dilim verir: parametre
    ayrıştırması (`{ sembol, h }`) kendisi bir küme parantezidir ve gövde yerine
    imzayı döndürür (çivi o hâlde "dal bulunamadı" der, yani sessizce körleşmez —
    ama ölçtüğü şey de kod değildir)."""
    m = re.search(rf"function\s+{re.escape(ad)}\b", KOD)
    assert m, f"`function {ad}` yorumsuz kaynakta yok"
    p = KOD.index("(", m.end())
    d = 0
    for k in range(p, len(KOD)):
        if KOD[k] == "(":
            d += 1
        elif KOD[k] == ")":
            d -= 1
            if d == 0:
                return _kume(KOD, k)
    raise AssertionError(f"`{ad}` parametre listesi kapanmıyor")


def _dal(kaynak: str, kosul: str) -> str:
    """`if (<kosul>…)` dalının gövdesi (dengeli küme)."""
    i = kaynak.find(kosul)
    assert i >= 0, f"dal koşulu bulunamadı: {kosul}"
    return _kume(kaynak, i)


def _kart(baslik: str) -> str:
    """Başlığı taşıyan `<Card …> … </Card>` diliminin yorumsuz gövdesi."""
    parcalar = KOD.split("</Card>")
    esler = [p for p in parcalar if baslik in p]
    assert len(esler) == 1, f"`{baslik}` başlıklı kart {len(esler)} kez bulundu (bir kez olmalı)"
    p = esler[0]
    # `<Card` DEĞİL `<Card[\s>]`: `<CardHeader`/`<CardDescription`/`<CardContent` de `<Card`
    # ile başlıyor ve düz `rindex("<Card")` kartın BAŞLIĞINI dilimin dışında bırakıyordu —
    # açıklama satırındaki elle yazılı sayı çivisi bu yüzden sessizce yeşil ötüyordu.
    aclislar = [m.start() for m in re.finditer(r"<Card[\s>]", p)]
    assert aclislar, f"`{baslik}` için `<Card` açılışı bulunamadı"
    return p[aclislar[-1] :]


# ---------------------------------------------------------------------------
# GÖVDE SABİTLERİ — çivi TSX'i alpaca.py'ye bağlar
# ---------------------------------------------------------------------------
def _alpaca_koruma_dizgeleri() -> tuple[str, str, str]:
    m = re.search(
        r"^KORUMA_VAR,\s*KORUMA_YOK,\s*KORUMA_OLCULEMEDI\s*=\s*"
        r'"([^"]+)",\s*"([^"]+)",\s*"([^"]+)"',
        ALPACA_HAM,
        re.MULTILINE,
    )
    assert m, "alpaca.py'de `KORUMA_VAR, KORUMA_YOK, KORUMA_OLCULEMEDI` ataması bulunamadı"
    return m.group(1), m.group(2), m.group(3)


def _alpaca_sabiti(ad: str) -> str:
    m = re.search(rf"^{re.escape(ad)}\s*=\s*(\d+)", ALPACA_HAM, re.MULTILINE)
    assert m, f"alpaca.py'de `{ad}` sabiti bulunamadı"
    return m.group(1)


def _tsx_sabiti(ad: str) -> str:
    m = re.search(rf'const\s+{re.escape(ad)}\s*=\s*"([^"]+)"', KOD)
    assert m, f"SeansIciEmir.tsx'te `const {ad}` yok (yorumsuz kaynakta arandı)"
    return m.group(1)


# ===========================================================================
# A + B · ÜÇ HÂL, ÜÇ ÇİZİM — ve dizgeler gövdeyle aynı
# ===========================================================================
def test_koruma_dizgeleri_alpaca_govdesiyle_ayni():
    var, yok, olcul = _alpaca_koruma_dizgeleri()
    assert _tsx_sabiti("KORUMA_VAR") == var
    assert _tsx_sabiti("KORUMA_YOK") == yok
    assert _tsx_sabiti("KORUMA_OLCULEMEDI") == olcul


def test_uc_koruma_hali_uc_ayri_cizim():
    govde = _fonksiyon("KorumaRozeti")
    dal_var = _dal(govde, "KORUMA_VAR")
    dal_yok = _dal(govde, "KORUMA_YOK")
    dal_olcul = _dal(govde, "KORUMA_OLCULEMEDI")

    # Üç gövde İKİŞER İKİŞER farklı olmalı — aynı çizimi iki hâle vermek, ölçülmüş bir
    # olguyla bir arızayı tek cümleye indirmektir.
    assert dal_var != dal_yok
    assert dal_var != dal_olcul
    assert dal_yok != dal_olcul

    # KORUMASIZ: tek KIRMIZI dal. `Olculemedi` bileşenine DÜŞMEZ (asıl ders).
    assert 'variant="destructive"' in dal_yok
    assert "<Olculemedi" not in dal_yok
    assert "para(" not in dal_yok

    # ÖLÇÜLEMEDİ: nedenli tire. Rozet ÇİZMEZ, fiyat BASMAZ.
    assert "<Olculemedi" in dal_olcul
    assert "<Badge" not in dal_olcul
    assert 'variant="destructive"' not in dal_olcul
    assert "para(" not in dal_olcul

    # KORUMALI: stop fiyatı basılır, kırmızı DEĞİLDİR.
    assert "para(" in dal_var
    assert "<Badge" in dal_var
    assert 'variant="destructive"' not in dal_var


def test_koruma_haritasi_ve_nedeni_govdeden_okunuyor():
    kart = _kart("Pozisyon koruması")
    assert re.search(r"\bkoruma\b", kart), "koruma haritası kartta okunmuyor"
    assert re.search(r"koruma\s*===\s*null", kart), "`koruma === null` dalı yok"
    assert re.search(r"koruma\s*===\s*undefined", kart), "`koruma === undefined` dalı yok"
    # ALT-DİZE TUZAĞI: `"koruma_neden" in kart` KANIT DEĞİLDİR — alan adı bir koşulda ya da
    # bir açıklamada da geçebilir. Çivi ÇAĞRI BİÇİMİNİ ölçer: neden EKRANA basılan değerin
    # kendisi olmalı, yedeği olan sabit cümle ancak `??`/`||` ardından gelebilir.
    assert re.search(
        r"hesap\?\.koruma_neden\s*(\?\?|\|\|)", kart
    ), "`koruma_neden` ekrana basılan değer değil (yalnız adı geçiyor olabilir)"


def test_koruma_karti_pozisyon_sayar_emir_degil():
    """NVDA çivisi: kart POZİSYONLARI dolaşmalı. Emir dizisini dolaşan bir kart, hiç emri
    olmayan korumasız pozisyonu YAPISAL olarak gösteremez."""
    kart = _kart("Pozisyon koruması")
    assert "emirler" not in kart, "koruma kartı emir dizisini dolaşıyor — korumasız pozisyon görünmez"
    assert "Object.entries" in kart or "Object.keys" in kart, "koruma haritası satırlara açılmıyor"


# ===========================================================================
# C · KIRPMA GÖVDEDEN OKUNUR — elle yazılı sayı YOK
# ===========================================================================
def test_kirpma_dort_alani_da_okunuyor():
    """ALT-DİZE TUZAĞI: `.kirpilan` kartta BİR KEZ geçmesi yetmez.

    `kirpilan` hem koşulsuz muhasebe satırında hem de "tavan aşıldı" uyarısında geçiyor;
    varlık kontrolü, muhasebe satırından silinse bile uyarıdaki geçiş yüzünden yeşil öterdi
    (mutasyon M10 tam olarak buradan kaçtı). Çivi İKİ ŞEYİ ayrı ölçer: (a) her sayının
    ÇAĞRI BİÇİMİ — `<KirpmaSayisi v={kirpma.X} alan="X" />` — ve `v` ile `alan` AYNI alanı
    göstermeli (kopyala-yapıştır kayması sessiz yalan üretirdi); (b) KOŞULSUZ görünen
    muhasebe satırı `canli` ve `kirpilan` sayılarını kendi içinde taşımalı."""
    kart = _kart("Aynadaki")
    assert "open_orders_kirpma" in KOD, "`open_orders_kirpma` alanının okuyucusu yok"

    cagrilar = re.findall(r"<KirpmaSayisi\s+v=\{kirpma\.(\w+)\}\s+alan=\"(\w+)\"\s*/>", kart)
    for v_alan, beyan in cagrilar:
        assert v_alan == beyan, f"`v={{kirpma.{v_alan}}}` ile `alan=\"{beyan}\"` ayrışmış"
    okunan = {v for v, _ in cagrilar}
    for alan in ("tavan", "canli", "kirpilan", "pencere_istenen", "pencere_donen"):
        assert alan in okunan, f"`open_orders_kirpma.{alan}` ekrana yazılmıyor"

    # KOŞULSUZ MUHASEBE SATIRI — `kirpilan` sıfırken de görünen tek yer burasıdır.
    i = kart.find("Kırpma muhasebesi")
    assert i >= 0, "koşulsuz kırpma muhasebesi satırı yok"
    beyan_dilimi = kart[i : kart.index("</p>", i)]
    for alan in ("canli", "kirpilan"):
        assert re.search(
            rf"<KirpmaSayisi\s+v=\{{kirpma\.{alan}\}}", beyan_dilimi
        ), f"muhasebe satırı `{alan}` sayısını taşımıyor"

    # `pencere_doygun` bir SAYI değil bir HÜKÜM: karşılaştırma biçimiyle çivilenir.
    assert re.search(r"kirpma\.pencere_doygun\s*===", kart), "`pencere_doygun` hükmü okunmuyor"


def test_emir_karti_elle_yazili_sayi_tasimiyor():
    kart = _classname_siz(_kart("Aynadaki"))
    kalanlar = re.findall(r"(?<![\w.-])\d{2,}(?![\w.-])", kart)
    assert not kalanlar, f"emir kartında elle yazılı sayı(lar) var: {kalanlar}"
    # Gövdenin İKİ sabiti de TSX'te ARANMAZ: tavan/pencere değişince pano sessizce yalan söylerdi.
    for ad in ("_PANO_EMIR_TAVANI", "_PANO_EMIR_PENCERESI"):
        assert _alpaca_sabiti(ad) not in _classname_siz(KOD), f"`{ad}` değeri TSX'e elle yazılmış"


def test_bayat_tavan_metni_gitti():
    assert "en çok 20" not in HAM, "bayat 'en çok 20 satır' cümlesi hâlâ duruyor"
    assert "1631" not in HAM, "bayat ``alpaca.dashboard_view` emir tavanı` çapası hâlâ duruyor"


# ===========================================================================
# D · pencere_doygun okuyucusu
# ===========================================================================
def test_pencere_doygun_dali_listenin_tam_olmadigini_soyluyor():
    kart = _kart("Aynadaki")
    i = kart.find("pencere_doygun ===")
    assert i >= 0, "`pencere_doygun === …` karşılaştırması yok (varlık kontrolü kanıt değil)"
    dilim = kart[i : i + 900]
    assert "TAM DEĞİL" in dilim, "doygun dalı 'liste TAM DEĞİL' demiyor"
    assert "pencere" in dilim


# ===========================================================================
# E · open_orders üç hâli — null ≠ boş
# ===========================================================================
def test_open_orders_null_dali_gercek_nedeni_okuyor():
    """ALT-DİZE TUZAĞI: `"open_orders_neden" in dal` KANIT DEĞİLDİR.

    Alan adı aynı dalda bir KOŞULDA da geçiyor (`!hesap.open_orders_neden && …`), yani
    ekrana basılan değerden silinse bile varlık kontrolü yeşil öterdi — mutasyon M4 tam
    olarak oradan kaçtı. Çivi ÇAĞRI BİÇİMİNİ ölçer: gövdenin nedeni BİRİNCİ sıradadır,
    üst yüzeyin kendi teşhisi ancak `??`/`||` ardından yedek olarak gelir."""
    kart = _kart("Aynadaki")
    assert re.search(r"emirler\s*===\s*null", kart), "`emirler === null` dalı yok"
    assert re.search(r"emirler\.length\s*===\s*0", kart), "boş-liste dalı ayrı değil"
    assert re.search(
        r"hesap\?\.open_orders_neden\s*(\?\?|\|\|)", kart
    ), "arızanın GERÇEK nedeni (`open_orders_neden`) ekrana basılan değer değil"


def test_tipler_open_orders_null_a_izin_veriyor():
    assert re.search(
        r"open_orders\?:\s*readonly\s+BrokerEmri\[\]\s*\|\s*null;", TIPLER
    ), "portfoy/tipler.ts `open_orders` hâlâ `null` kabul etmiyor"
    assert re.search(
        r"open_orders\?:\s*AlpacaEmir\[\]\s*\|\s*null;", UCTIPLERI
    ), "kimlik/uctipleri.ts `open_orders` hâlâ `null` kabul etmiyor"


def test_yeni_alanlar_iki_tip_dosyasinda_da_var():
    for ad, kaynak in (("portfoy/tipler.ts", TIPLER), ("kimlik/uctipleri.ts", UCTIPLERI)):
        for alan in ("open_orders_neden", "open_orders_kirpma", "koruma", "koruma_neden"):
            assert re.search(rf"\b{alan}\?:", kaynak), f"{ad}: `{alan}` alanı tipte yok"


# ===========================================================================
# F · satır çapası yok + soyucu geçerliliği
# ===========================================================================
def test_satir_capasi_kalmadi():
    for yol, ham in (
        (EMIR_YOLU, HAM),
        (TIPLER_YOLU, TIPLER_HAM),
        (UCTIPLERI_YOLU, UCTIPLERI_HAM),
    ):
        capalar = re.findall(r"\b[\w/]+\.(?:py|ts|tsx|css):\d+", ham)
        capalar += re.findall(r"\.(?:py|ts|tsx)\s*\(\d+", ham)
        capalar += re.findall(r"\(\d{2,}(?:-\d+)?\)", ham)
        assert not capalar, f"{yol.name}: satır çapası kaldı → {capalar}"


def test_soyucu_hala_gecerli():
    """Soyucu satır-BAŞI `//` atıyor; satır-SONU yorum eklenirse çivi kör kalırdı."""
    for ln in _blok_yorumsuz(HAM).splitlines():
        s = ln.strip()
        if s.startswith("//"):
            continue
        assert "//" not in s or "://" in s, f"satır-sonu `//` yorumu eklenmiş: {s!r}"

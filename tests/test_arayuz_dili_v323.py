"""ARAYÜZ DİLİ: İÇ AYRINTI BİRİNCİL METİNDE OLAMAZ · v323

OPERATÖR (2026-08-26): "uygulama içinde kullanılan dilde çok fazla internal terim oldu ve
uygulama çok büyüdüğü için ben bile anlamakta zorlanıyorum. Dışardan bir göz sadece UI'ı
göreceği için buradaki açıklamaların düzelmesi lazım."

ÖLÇÜLDÜ — sorun ÜÇ AYRI sınıf ve çareleri farklı (hepsine "jargon" demek yanlış teşhis):
  A) uydurulmuş iç sözlük  ~390 geçiş (kapı 71 · defter 68 · ayna 46 · hüküm 31 · sprint 26 …)
  B) HAM İÇ AYRINTI SIZINTISI  786 geçiş  ← BU ÇİVİNİN KONUSU
       414 backtick'li alan adı · 164 uç yolu · 139 sabit/env adı · 45 null/None · 24 dosya adı
  C) dürüst-boşluk idiomu  512 geçiş (ölçülemedi 178 · yazılmamış 112 · döndürmedi 62 …)

B EN BÜYÜK VE EN KOLAY: hiçbir ürün kararı gerektirmez. `/api/session` ya da
`NOUS_DEFAULT_MODEL` gören biri "bu bitmemiş" der — bunlar geliştiricinin KENDİNE yazdığı
cümlelerdi ve ekranda duruyorlardı.

MEKANİZMA ZATEN VARDI, YANLIŞ KULLANILIYORDU: `Olculemedi({neden})` iki katmanlı bir bileşen.
Ama `neden` tek dizeydi ve iç ayrıntıyı BİRİNCİL metin olarak taşıyordu:
    neden="`day_pnl_pct` nabızda yok — günlük değişim ölçülemedi."
Sözleşme ikiye ayrılır ve sıra TERSİNE döner:
    neden="Günlük değişim henüz hesaplanmadı"      ← insan cümlesi, GÖRÜNÜR
    teknik="`day_pnl_pct` nabızda yok"             ← iç ayrıntı, üstüne gelince

DÜRÜSTLÜK DİSİPLİNİ AYNEN KORUNUR — bu çivi UYDURMA YASAĞINI GEVŞETMEZ: veri yokken hâlâ
sayı uydurulmuyor ve sebep hâlâ TAŞINIYOR. Değişen tek şey, sebebin hangi katmanda ve hangi
dille söylendiği. `teknik`i düşürmek de yasak (aşağıdaki çivi) — teşhis kaybolurdu.
"""
from __future__ import annotations

import pathlib
import re

KOK = pathlib.Path(__file__).resolve().parents[1]
PANO = KOK / "ui/src/pano"
#: TANIM TAŞINDI (TSK-121, 2026-09-03): `Olculemedi`nin on üç kopyası `parcalar/olculemedi.tsx`teki
#: TEK kabuk-enjeksiyonuna (`olculemediKur`) indi — sözleşme testleri artık O dosyayı ölçer,
#: `ogrenme/ortak.tsx` yalnız bir çağrı yeridir (`olculemediKur("hucre", …)`).
ORTAK = PANO / "parcalar/olculemedi.tsx"

#: `neden` içinde GÖRÜLMEMESİ gerekenler — kullanıcı bunları bilemez.
IC_AYRINTI = [
    (re.compile(r"`[^`]+`"),                     "backtick'li alan/kod adı"),
    (re.compile(r"/api/[A-Za-z0-9_/.]+"),        "uç yolu"),
    (re.compile(r"\b[A-Z][A-Z0-9_]{4,}\b"),      "sabit/env adı"),
    (re.compile(r"\bnull\b|\bNone\b|\bundefined\b"), "null/None/undefined"),
    (re.compile(r"\b\w+\.(py|tsx|ts|json|jsonl|yaml)\b"), "dosya adı"),
]


def _tsx() -> list[tuple[pathlib.Path, str]]:
    out = []
    for p in sorted(PANO.rglob("*.tsx")):
        s = p.read_text(encoding="utf-8", errors="ignore")
        s = re.sub(r"/\*.*?\*/", " ", s, flags=re.S)      # şerhler ölçüm dışı
        s = re.sub(r"^\s*//.*$", " ", s, flags=re.M)
        out.append((p, s))
    return out


def _neden_cagrilari() -> list[tuple[str, str]]:
    """(dosya, `neden` değeri) — yalnız DÜZ dizeler. Şablon/ifade değerleri okunamaz ve
    bu çivi onları SESSİZCE ATLAMAZ: aşağıdaki ayrı çivi sayılarını beyan eder."""
    out = []
    for p, s in _tsx():
        for m in re.finditer(r'neden="([^"\\\n]*)"', s):
            out.append((str(p.relative_to(KOK)), m.group(1)))
    return out


def test_bilesen_TEKNIK_katmanini_tasiyor():
    """Sözleşmenin kendisi: iç ayrıntının gideceği AYRI bir yer olmalı, yoksa çağrı
    yerlerinde tek dizeye sıkışmaya devam eder.
    TANIM TAŞINDI (TSK-121, 2026-09-03): `Olculemedi` artık `olculemediKur(...)`nin döndürdüğü
    kapanış — `teknik` inline destructuring'te değil, ortak `OlculemediOzellikleri` arayüzünde
    taşınır (aile gövdelerinin HEPSİ aynı arayüzü kullanır)."""
    s = ORTAK.read_text(encoding="utf-8")
    assert re.search(r"interface OlculemediOzellikleri\s*\{[^}]*readonly teknik\?:\s*string", s), (
        "`OlculemediOzellikleri` `teknik` katmanını taşımıyor — iç ayrıntı birincil metinde kalmak zorunda")


def test_TEKNIK_katmani_DUSURULMUYOR():
    """Aşırıya kaçma çivisi: `teknik` verilmişse EKRANDA bir yerde erişilebilir olmalı.
    Onu tamamen atmak, dürüstlük disiplinini (sebebi taşı) delerdi — teşhis kaybolur.
    TANIM TAŞINDI (TSK-121, 2026-09-03): en az bir aile gövdesi `o.teknik`i `title`a
    BAĞLAMALI — `teknik` katmanının hiçbir ailede kullanılmaması bu çiviyi kırar."""
    s = ORTAK.read_text(encoding="utf-8")
    assert re.search(r"title=\{[^}]*o\.teknik|\{o\.teknik\}", s), (
        "`teknik` hiçbir aile gövdesinde kullanılmıyor — verilen sebep sessizce yutuluyor")


def test_INSAN_CUMLESI_ic_ayrinti_TASIMIYOR():
    """ASIL ÇİVİ: `neden` kullanıcının okuduğu cümledir; alan adı, uç yolu, sabit adı ya da
    `null` içeremez. İç ayrıntının yeri `teknik`tir."""
    ihlal = []
    for dosya, deger in _neden_cagrilari():
        for desen, ad in IC_AYRINTI:
            if desen.search(deger):
                ihlal.append(f"{dosya}: [{ad}] {deger[:90]}")
                break
    assert not ihlal, (
        f"{len(ihlal)} `neden` iç ayrıntı taşıyor — kullanıcı bunları bilemez. "
        f"İç ayrıntıyı `teknik=` katmanına taşı.\n" + "\n".join(f"  · {x}" for x in ihlal[:25])
        + (f"\n  … ve {len(ihlal) - 25} tane daha" if len(ihlal) > 25 else ""))


def test_OLCUM_KAPSAMI_BEYANLI():
    """UYDURMA YASAĞI komşusu: bu çivi yalnız DÜZ dizeleri okuyabilir. Şablon/ifade değerli
    `neden`ler ölçüm DIŞINDADIR ve bu SESSİZ kalamaz — sayıları burada beyan edilir, yoksa
    'sıfır ihlal' cümlesi kapsamı olduğundan geniş gösterir."""
    duz = len(_neden_cagrilari())
    tum = sum(len(re.findall(r"\bneden=", s)) for _, s in _tsx())
    okunamayan = tum - duz
    assert duz > 0, "hiç `neden` okunamadı — ölçüm aracı kırılmış olabilir"
    # Kapsam oranı beyanlı: ölçülemeyen pay %35'i aşarsa çivinin hükmü zayıftır.
    assert okunamayan / tum <= 0.35, (
        f"`neden` çağrılarının {okunamayan}/{tum}'i düz dize değil (şablon/ifade) — bu çivi "
        f"onları GÖREMEZ. Kapsam bu kadar düşükken 'temiz' hükmü yanıltıcıdır.")


# ============================================================================================
# (2) SES BİRLİĞİ — aynı boşluk hâli her yüzeyde AYNI kelimeyle söylenir
# --------------------------------------------------------------------------------------------
# "DIŞARIDAN GÖZ" DENETİMİNİN BULGUSU (2026-08-26): yedi yüzeyi yedi ayrı el yazdı ve her biri
# kendi fiilini seçti. Aynı planın aynı boş alanı kuyruk yüzeyinde "kaydedilmemiş", bugün
# yüzeyinde "yazılmamış" diyordu — kullanıcı arada bir FARK olduğunu sanır. Boşluk hâlinin
# sözlüğü DÖRT kelimeyle sınırlıdır ve her biri AYRI bir olguyu anlatır (aşağıdaki yapı).
#
# SÖZLÜK ARTIK PYTHON YAPISI, DÜZ ŞERH DEĞİL (TSK-114, düzeltme turu 1, inceleme Ö-1,
# 2026-09-03): dört kelime yalnız bu şerhin içinde yazılıydı ve aşağıdaki sınıf-A deseni onları
# ELLE tekrarlıyordu — iki kopya ŞİMDİDEN ayrışmıştı (`bildirilmedi`/`hesaplanamadı`/
# `kaydedilmemiş` desende HİÇ yoktu, desendeki `yazılmamış` ise sözlükten çıkarılmıştı).
# Tek-kaynak yasası: sözcükler BURADA durur, her okuyucu (hata mesajı, sınıf-A deseni) türetir.
SES_BIRLIGI = {
    "bildirilmedi": "yanıtta alan hiç gelmedi",
    "kaydedilmemiş": "alan geldi ama kayda yazılmamış",
    "okunamadı": "ölçüm denendi ve düştü",
    "hesaplanamadı": "ölçüm denendi ve düştü (hesap tarafı)",
}
# "Henüz … yok" AYRI bir kalıptır ve sözlüğe GİRMEZ: fiil değil cümle iskeleti, ve anlattığı şey
# bir ölçüm arızası değil — olgu henüz oluşmadı, sonra oluşacak.
#
# "yazılmamış" LİSTEDEN ÇIKARILDI: "kaydedilmemiş" ile aynı şeyi anlatıyordu, iki kelime tek
# olgu için iki ayrı olgu izlenimi veriyordu.
YASAK_ESANLAMLI = {
    "yazılmamış": "kaydedilmemiş",   # ikisi aynı olgu; tek kelimede birleşti
}


def test_YASAK_ESANLAMLILAR_kullanilmiyor():
    ihlal = [f"{d}: {v[:70]}" for d, v in _neden_cagrilari()
             for k in YASAK_ESANLAMLI if k in v]
    assert not ihlal, (
        f"{len(ihlal)} `neden` eşanlamlı bir fiil kullanıyor — aynı olgu iki kelimeyle "
        f"anlatılırsa kullanıcı arada fark sanır. Standart: "
        + " · ".join(f"{k} → {v}" for k, v in YASAK_ESANLAMLI.items())
        + "\nSES BİRLİĞİ dağarcığı (tek kaynak): "
        + " · ".join(f"{k} = {v}" for k, v in SES_BIRLIGI.items())
        + "\n" + "\n".join(f"  · {x}" for x in ihlal[:12]))


def test_SONDA_NOKTA_YOK():
    """Mevcut üslup: kısa parça, sonda nokta yok. 20 metin noktayla bitiyordu ve aynı
    listede noktasızlarla yan yana duruyordu — göze çarpan, anlamı olmayan bir ayrışma."""
    ihlal = [f"{d}: {v[:70]}" for d, v in _neden_cagrilari() if v.rstrip().endswith(".")]
    assert not ihlal, (
        f"{len(ihlal)} `neden` noktayla bitiyor — üslup ayrışması:\n"
        + "\n".join(f"  · {x}" for x in ihlal[:12]))


# --- SÖZLÜK TABLOSUNUN KENDİSİ ÇİVİLENİR (2026-08-26, ikinci tur) --------------
# `docs/ARAYUZ-SOZLUGU.md` "bu tablo tek kaynaktır ve TESTLE BAĞLIDIR" diye bitiyordu.
# BAĞLI DEĞİLDİ. Belgeyi yazan bendim ve tutmayan bir garanti beyan ettim — YASA 6'nın
# tersi: okuyucusu olan ama ölçüsü olmayan bir cümle.
#
# İKİ KÖR NOKTA, TEK SEBEP — bir uzantı filtresi:
#   · yukarıdaki `_tsx()` yalnız `PANO.rglob("*.tsx")` okuyor
#   · kenar çubuğu KAYDI `ui/src/pano/alanlar.ts` — bir `.ts`
# Sonuç ölçüldü: A turu 102 etiket çevirdi ama gezinme metnine HİÇ dokunmadı. Gövde
# "Danışma" yazarken menü "Hermes" diyordu; kaydın `soru:` alanları hâlâ "Yansıma
# hattı ne durumda" diyordu. Ve aynı kör nokta yüzünden suite bunu YEŞİL geçti.
#
# KAPSAM SINIRI, bilerek: bu çivi KAYIT dosyasını (`alanlar.ts`) bağlar. Orası
# gezinmenin tek kaynağı ve kullanıcının İLK okuduğu metin — yüzey gövdelerindeki
# serbest metin bu çivinin konusu değil (onu insan gözü ve bu tablo yürütür).
SOZLUK_KAYIT = KOK / "ui/src/pano/alanlar.ts"
DEGISEN_TERIMLER = [
    "sprint", "hermes", "beyin", "yansıma", "kadans", "silahl", "hüküm", "hükm",
    "gölge", "kova", "ufuk", "bacak", "tohum", "ısınma", "çırpınma",
    "karşı-olgusal", "kat kazanım", "üçüncü hâl", "açık kalem", "eksen-2",
]


def _kayit_gorunur_metinler() -> list[tuple[int, str, str]]:
    """(satır, alan, değer) — kayıttaki KULLANICI METNİ alanları.

    `kimlik:` BİLEREK DIŞARIDA: o bir DOM çapasıdır, kullanıcı metni değil. Onu
    çevirmek derin bağı sessizce kırar — bu tam olarak yapıldı ve v288'i kırmızıya
    düşürdü (`kimlik="antrenman turu"`). Biçimini ayrı bir çivi bekler: v324.
    """
    out = []
    for no, satir in enumerate(SOZLUK_KAYIT.read_text(encoding="utf-8").splitlines(), 1):
        for m in re.finditer(r'\b(baslik|soru)\s*:\s*"([^"\\\n]*)"', satir):
            out.append((no, m.group(1), m.group(2)))
    return out


def test_KAYIT_ayristiricisi_bayat_degil():
    n = len(_kayit_gorunur_metinler())
    assert n >= 40, f"kayıt ayrıştırıcısı yalnız {n} görünür metin gördü — desen bayat"


def test_SOZLUK_DEGISEN_TERIMLERI_gezinmede_YOK():
    ihlal = [f"alanlar.ts:{no} {alan}=\"{v}\"  ← '{t}'"
             for no, alan, v in _kayit_gorunur_metinler()
             for t in DEGISEN_TERIMLER if t in v.lower()]
    assert not ihlal, (
        f"gezinme metninde {len(ihlal)} ESKİ İÇ TERİM duruyor:\n"
        + "\n".join(f"  · {x}" for x in ihlal)
        + "\n`docs/ARAYUZ-SOZLUGU.md` tablosundaki karşılığını kullan. "
          "`kimlik:` alanına DOKUNMA — o çapadır (v324)."
    )


# ============================================================================
# ÇAĞRI YERİ KAPSAMASI (TSK-114, 2026-09-03)
# ----------------------------------------------------------------------------
# ÖLÇÜLEN BOŞLUK: yukarıdaki `teknik` çivileri yalnız `Olculemedi` BİLEŞENİNİ ölçüyordu
# (`export function Olculemedi(...teknik`, `title=|{teknik}`). Bir ÇAĞRI YERİNDEN `teknik=`
# düşürmek sessizce geçiyordu — TSK-109 turunda mutasyon denendi ve 8 çivi yeşil kaldı
# (2026-09-03 gece; bu dilimde yeniden ölçüldü: `Reflect.tsx`ten `teknik=` silindi, v323
# "8 passed" dedi). "Çivi yeşili kanıt değildir" (CLAUDE.md §6): bileşenin `teknik` alanını
# TAŞIMASI, çağrı yerlerinin onu VERMESİ demek değildir.
#
# KAPSAM GENİŞLEDİ — PANO GENELİ (TSK-121, 2026-09-03): ilk yazımda kapsam hafıza yüzeyiyle
# SINIRLIYDI (`ui/src/pano/yuzeyler/hafiza/**.tsx`, ölçüm günü 192 çağrı) çünkü `Olculemedi`nin
# ON ÜÇ kopyası vardı ve geniş bir çivi başka yüzeylerin kalemlerini bu dosyada kırardı. TSK-121
# on üç kopyayı `parcalar/olculemedi.tsx`teki TEK kabuk-enjeksiyonuna indirdi — kök zaten
# `PANO = KOK/"ui/src/pano"` (aşağıdaki `_tsx()`) olduğundan kapsamı hafızaya daraltan tek şey
# `_hafiza_cagrilari()`nin FİLTRESİYDİ; filtre kalktı. Ölçüm (2026-09-03, TSK-121 dilimi):
# pano geneli 565 çağrı, 565'i okunuyor (0 kaçak), 39'u saf-ifade `neden` (sınıf-A kuralının
# dışında, `SAF_IFADE_TAVANI` ile beyanlı), sınıf-A ihlali (ölçülen alan yokluğu + `teknik` yok)
# BİR taneydi (`kanban/Huni.tsx` — TSK-121 turunda `teknik=` eklenerek düzeltildi, bu genişleme
# olmasa görünmeyecek bir ölçülmüş boşluktu). `_hafiza_cagrilari()` ADI KORUNDU (yeniden adlandırma
# bu dilimin kapsamı değil) ama artık PANO GENELİNİ tarar.
# ============================================================================

#: Çağrı başı: `Olculemedi`, `OlculemediHucre`, `OlculemediBlok` — ama `OlculemediHali` DEĞİL
#: (ayrı bileşen; `\b` ile sayıldığında ham sayımı şişiriyordu, ölçüldü).
_CAGRI_BASI = re.compile(r"<Olculemedi(?:Hucre|Blok)?(?![A-Za-z0-9_])")

# `neden`i ÖLÇÜLEN BİR ALANIN yokluğunu bildiren sınıf — teşhis `teknik`e borçludur.
#
# FİİLLER TÜRETİLİR, ELLE YAZILMAZ (düzeltme turu 1, inceleme Ö-1, 2026-09-03): ilk yazımda
# desen `gelmedi|okunamadı|okunmadı|dönmedi|yazılmamış` idi ve dosyanın KENDİ ilan ettiği SES
# BİRLİĞİ sözlüğüyle ayrışmıştı — `bildirilmedi` (15 çağrı), `hesaplanamadı`, `kaydedilmemiş`
# kuralın DIŞINDA kalıyordu. Kaynak artık `SES_BIRLIGI`; ona sözlükte olmayan üç YOKLUK fiili
# eklenir (`gelmedi`/`okunmadı`/`dönmedi`: sözlük yokluğun ADINI standartlaştırır, bunlar
# yokluğun KENDİSİNİ bildirir).
#
# `yazılmamış` DESENDEN DÜŞTÜ ve bu bir kapsam kaybı DEĞİL: `YASAK_ESANLAMLI` onu zaten
# yasaklıyor — yeşil bir ağaçta hiçbir `neden` o kelimeyi taşıyamaz, yani desendeki dal ÖLÜYDÜ
# ve kuralın kapsamını olduğundan geniş gösteriyordu. Aşağıdaki filtre aynı zamanda yarın
# sözlüğe yasaklı bir eşanlamlı girerse onu da eler (ölü dal bir daha doğmaz).
_EK_YOKLUK_FIILLERI = ("gelmedi", "okunmadı", "dönmedi")
_SINIF_A_FIILLERI = tuple(
    f for f in (*SES_BIRLIGI, *_EK_YOKLUK_FIILLERI) if f not in YASAK_ESANLAMLI)
_SINIF_A = re.compile("|".join(re.escape(f) for f in _SINIF_A_FIILLERI))


def _acilis_etiketleri(s: str) -> tuple[list[str], list[str]]:
    """(okunan açılış etiketleri, okunamayanlar). JSX'i regex'le kesmek YETMEZ: prop değerleri
    `atlanan > 0` gibi `>` ve İÇ İÇE ŞABLON (`` `…${`…`}…` ``) taşıyor — düz regex ilk `>`de
    kesiyor ve çağrıyı SESSİZCE kaçırıyordu (ölçüldü: pano genelinde 4 kaçak). Bu yüzden
    süslü/tırnak/şablon bağlamı YIĞINLA izlenir ve kapanmayan etiket AYRICA sayılır — kaçak,
    'ihlal yok' diye okunamaz (körlük alarmı)."""
    tam: list[str] = []
    kirik: list[str] = []
    for m in _CAGRI_BASI.finditer(s):
        i = m.end()
        yigin: list[str] = []
        while i < len(s):
            c = s[i]
            ust = yigin[-1] if yigin else None
            if ust in ("'", '"'):
                if c == "\\":
                    i += 2
                    continue
                if c == ust:
                    yigin.pop()
            elif ust == "`":
                if c == "\\":
                    i += 2
                    continue
                if c == "`":
                    yigin.pop()
                elif c == "$" and s[i + 1:i + 2] == "{":
                    yigin.append("{")
                    i += 2
                    continue
            else:
                if c in "\"'`":
                    yigin.append(c)
                elif c == "{":
                    yigin.append("{")
                elif c == "}":
                    if yigin and yigin[-1] == "{":
                        yigin.pop()
                elif c == ">" and not yigin:
                    tam.append(s[m.start():i + 1])
                    break
            i += 1
        else:
            kirik.append(s[m.start():m.start() + 200])
    return tam, kirik


def _hafiza_cagrilari() -> list[tuple[str, str]]:
    """AD KORUNDU, KAPSAM GENİŞLEDİ (TSK-121, 2026-09-03): `HAFIZA not in p.parents` filtresi
    kalktı — `_tsx()` zaten `PANO.rglob("*.tsx")` (pano geneli) döndüğünden bu fonksiyon artık
    PANO GENELİNİ tarar. İsim değişmedi: yeniden adlandırma bu dilimin kapsamı değil ve mevcut
    dört çağıran (aşağıdaki testler) hâlâ aynı adı kullanıyor."""
    out = []
    for p, s in _tsx():
        tam, _ = _acilis_etiketleri(s)
        out.extend((str(p.relative_to(KOK)), c) for c in tam)
    return out


# ----------------------------------------------------------------------------
# `neden` DEĞERİNİN STATİK METNİ — düz dize DE şablon DA okunur (Ö-1, 2026-09-03)
# ----------------------------------------------------------------------------
# İlk yazımda sınıf-A kuralı YALNIZ `neden="…"` (çift tırnaklı düz dize) üzerinde koşuyordu.
# Ama hafıza yüzeyinin `neden`lerinin bir kısmı süslü bloktur: `` neden={`${ne} okunamadı`} ``
# (`parcalar.tsx`, `Yapilandirma.tsx`) ya da `neden={x ? "A gelmedi" : "A ölçülemedi"}`
# (`Belgeler.tsx`). Bunların STATİK metni ekranda birebir görünür ve sınıf-A anlamını TAŞIR;
# kural onları görmezse "192/192 taşıyor" cümlesi KURALIN değil TARAYICININ kapsamını anlatır.
# Etiket okuyucusu zaten süslü/tırnak/şablon bağlamını yığınla izliyor — aynı yürüyüş burada
# `neden` DEĞERİ için tekrarlanır ve `${…}` içleri ATILIR (orada bir değişken var, sözcük değil).
_NEDEN_ANAHTARI = re.compile(r"\bneden=")


def _susluyu_al(s: str, i: int) -> str:
    """`s[i] == "{"` iken eşleşen kapanışa kadarki İÇ metin. Tırnak/şablon duyarlı: bir dizenin
    içindeki `}` bloğu kapatmaz (düz sayaç `neden={x ? "}" : y}` gibi bir değerde kayardı)."""
    yigin = ["{"]
    j = i + 1
    while j < len(s):
        c = s[j]
        ust = yigin[-1]
        if ust in ("'", '"'):
            if c == "\\":
                j += 2
                continue
            if c == ust:
                yigin.pop()
        elif ust == "`":
            if c == "\\":
                j += 2
                continue
            if c == "`":
                yigin.pop()
            elif c == "$" and s[j + 1:j + 2] == "{":
                yigin.append("{")
                j += 2
                continue
        else:                       # süslü blok içi
            if c in "\"'`":
                yigin.append(c)
            elif c == "{":
                yigin.append("{")
            elif c == "}":
                yigin.pop()
                if not yigin:
                    return s[i + 1:j]
        j += 1
    return s[i + 1:]                # kapanmadı: etiket tarayıcısı bunu zaten kaçak sayar


def _statik_metin(ifade: str) -> str:
    """Bir JSX ifadesinin EKRANDA GÖRÜNEBİLEN sabit metni: dize/şablon sabitleri toplanır,
    `${…}` ve ifade düzeyindeki tanımlayıcılar ATILIR. `${…}` İÇİNDEKİ dizeler toplanır —
    `x ? "A gelmedi" : "B"` üçlüsünde iki dal da ekranda görünebilir."""
    parcalar: list[str] = []
    yigin: list[str] = []
    j = 0
    while j < len(ifade):
        c = ifade[j]
        ust = yigin[-1] if yigin else None
        if ust in ("'", '"'):
            if c == "\\":
                j += 2
                continue
            if c == ust:
                yigin.pop()
            else:
                parcalar.append(c)
        elif ust == "`":
            if c == "\\":
                j += 2
                continue
            if c == "`":
                yigin.pop()
            elif c == "$" and ifade[j + 1:j + 2] == "{":
                yigin.append("{")
                j += 2
                continue
            else:
                parcalar.append(c)
        else:                       # ifade düzeyi ya da `${…}` içi — sabit metin DEĞİL
            if c in "\"'`":
                yigin.append(c)
            elif c == "{":
                yigin.append("{")
            elif c == "}" and ust == "{":
                yigin.pop()
        j += 1
    return "".join(parcalar)


_HARF = re.compile(r"[^\W\d_]", re.UNICODE)


def _neden_statik(cagri: str) -> str | None:
    """Çağrının `neden` değerinin STATİK metni; `None` = statik olarak SINIFLANDIRILAMAZ
    (`neden` hiç yok, ya da saf ifade: `neden={zarf.neden}` gibi tek harf sabit taşımıyor).
    `None` sayısı ayrıca BEYAN EDİLİR — okunamayan bir çağrı 'ihlalsiz' sayılamaz."""
    m = _NEDEN_ANAHTARI.search(cagri)
    if m is None:
        return None
    i = m.end()
    if cagri[i:i + 1] == '"':
        son = cagri.find('"', i + 1)
        deger = cagri[i + 1:son] if son != -1 else ""
    elif cagri[i:i + 1] == "{":
        deger = _statik_metin(_susluyu_al(cagri, i))
    else:
        deger = ""
    return deger if _HARF.search(deger) else None


#: SAF-İFADE `neden` TAVANI (düzeltme turu 1, inceleme Ö-1, 2026-09-03). `test_OLCUM_KAPSAMI_
#: BEYANLI` emsali: kural yalnız STATİK metni okuyabilir; `neden={zarf.neden}` gibi saf ifade
#: değerleri sınıflandırılamaz ve bu SESSİZ kalamaz.
#: TAVANI BRIEF DEĞİL ÖLÇÜM SÖYLER. KAPSAM PANO GENELİNE GENİŞLEDİ (TSK-121, 2026-09-03) —
#: eski ölçüm (hafıza yüzeyi) 192 çağrının 1'ini saf-ifade buluyordu, tavan 3'tü. YENİ ölçüm
#: (pano geneli): 565 çağrının 39'u saf-ifade (`neden={x}` gibi türetilen değerler — çoğu
#: `Deger`/`OlculemediHucre` sarmalayıcılarının kendi `neden`i taşıyan çağrı yerleri, elle
#: örneklendi). Tavan 45: ölçüm günü sayısı + küçük pay. Pay TAM SAYI değil çünkü yeni bir
#: saf-ifade çağrısı meşru olabilir; ama aşılırsa kuralın kapsamı sessizce daralıyordur ve
#: tavan YENİ bir ölçümle güncellenmelidir (sonucu görüp eşiği yükseltmek DEĞİL).
SAF_IFADE_TAVANI = 45


def test_CAGRI_TARAYICISI_HIC_KACAK_BIRAKMIYOR():
    """KÖRLÜK ALARMI — aşağıdaki üç çivinin hükmü bu satıra dayanır: tarayıcı bir çağrıyı
    okuyamazsa o çağrı 'ihlalsiz' sayılır ve 'sıfır ihlal' cümlesi bir okuma YOKLUĞU olur.
    Ham sayım ile okunan sayım EŞİT olmalı (kapsam PANO GENELİ, TSK-121, 2026-09-03: 565/565,
    0 kaçak).

    `ham == okunan` İDDİASI TOTOLOJİYE YAKINDIR ve öyle okunmasın (inceleme K-4, düzeltme
    turu 1, 2026-09-03): `kacak == 0` geçtikten sonra her eşleşme ya `tam` ya `kirik` listesine
    düştüğü için iddia zaten sağlanır. Yine de DURUYOR çünkü aynı sayının İKİ YOLDAN ölçümüdür
    (`findall` sayımı ↔ yığın yürüyüşünün ürettiği liste); ikisi ayrışırsa yürüyüşte bir eşleşme
    sessizce yutulmuş demektir. Bir GÜVENCE değil, bir tutarlılık ölçüsü.

    SAF İFADE `neden`ler AYRICA BEYAN EDİLİR (Ö-1): statik metni olmayan değerler sınıf-A
    kuralının DIŞINDADIR; sayıları burada tavanla ölçülür, yoksa "her çağrı kuralda" cümlesi
    kapsamı olduğundan geniş gösterir."""
    ham = okunan = kacak = 0
    kacaklar: list[str] = []
    for p, s in _tsx():
        ham += len(_CAGRI_BASI.findall(s))
        tam, kirik = _acilis_etiketleri(s)
        okunan += len(tam)
        kacak += len(kirik)
        kacaklar.extend(f"{p.name}: {' '.join(k.split())[:110]}" for k in kirik)
    assert kacak == 0, f"{kacak} çağrı etiketi kapanmadan okundu:\n" + "\n".join(kacaklar[:10])
    assert ham == okunan, f"tarayıcı {ham} çağrının {okunan}'ini okudu — hüküm eksik kapsamda"
    # TABAN: KAPSAM PANO GENELİNE GENİŞLEDİ (TSK-121, 2026-09-03) — eski taban (hafıza yüzeyi,
    # 192 çağrı) >= 150'ydi. YENİ ölçüm 565 çağrı; taban >= 500'e kalibre edildi. Taban, tarama
    # kırılıp BOŞ dönerse "temiz" demesin diye var (ya da HAFIZA filtresi GERİ KONURSA — pano
    # geneli 565'ten hafıza-yalnız ~192'ye düşer ve bu satır öter); tam sayı DEĞİL çünkü çağrı
    # silmek meşru bir iştir.
    assert okunan >= 500, f"pano genelinde yalnız {okunan} çağrı okundu (2026-09-03: 565)"

    cagrilar = _hafiza_cagrilari()
    saf = [f"{d}: {' '.join(c.split())[:110]}"
           for d, c in cagrilar if _neden_statik(c) is None]
    kural_kapsami = len(cagrilar) - len(saf)
    assert len(saf) <= SAF_IFADE_TAVANI, (
        f"sınıf-A kuralının DIŞINDA kalan saf-ifade `neden` sayısı {len(saf)} "
        f"(tavan {SAF_IFADE_TAVANI}; kural kapsamı {kural_kapsami}/{len(cagrilar)}). "
        f"Kapsam bu kadar düşükken 'her çağrı kuralda' hükmü yanıltıcıdır — ya değeri statik "
        f"metne çevir ya da tavanı YENİ bir ölçümle güncelle:\n"
        + "\n".join(f"  · {x}" for x in saf[:12]))


def test_HER_CAGRI_NEDEN_tasiyor():
    """(b) `neden` ZORUNLU: nedensiz bir "ölçülemedi" rozeti, boş hücrenin süslü hâlidir —
    kullanıcı neyin neden yok olduğunu öğrenemez (dürüst-boşluk idiomunun tam tersi)."""
    ihlal = [f"{d}: {' '.join(c.split())[:110]}"
             for d, c in _hafiza_cagrilari() if not re.search(r"\bneden=", c)]
    assert not ihlal, f"{len(ihlal)} çağrı `neden` taşımıyor:\n" + "\n".join(ihlal[:15])


def test_OLCULEN_ALAN_ADINI_ANAN_NEDEN_TEKNIK_tasiyor():
    """(a) ASIL ÇİVİ (TSK-114): `neden`i "… gelmedi / okunamadı / dönmedi" diyen çağrı, hangi
    alanın gelmediğini `teknik`te SÖYLEMEK zorundadır. Bu sınıf `teknik`siz kalırsa ekranda
    "bir şey gelmedi" yazar ve teşhis kaybolur — v323'ün kapattığı sızıntının aynadaki hâli:
    iç ayrıntıyı birincil metinden çıkarmak, onu ATMAK değildir.

    KAPSAM (düzeltme turu 1, inceleme Ö-1, 2026-09-03): fiiller SES BİRLİĞİ sözlüğünden türer
    ve kural `neden`in STATİK metnini okur — düz dize DE süslü/şablon değer DE. Sınıflandırılamayan
    saf ifadelerin sayısı `test_CAGRI_TARAYICISI_HIC_KACAK_BIRAKMIYOR`ta tavanla beyan edilir."""
    ihlal = []
    for d, c in _hafiza_cagrilari():
        statik = _neden_statik(c)
        if statik is not None and _SINIF_A.search(statik) and not re.search(r"\bteknik=", c):
            ihlal.append(f"{d}: {' '.join(c.split())[:130]}")
    assert not ihlal, (
        f"{len(ihlal)} çağrı ölçülen alanın yokluğunu bildiriyor ama `teknik` vermiyor — "
        f"teşhis ekranda hiçbir katmanda yok:\n" + "\n".join(ihlal[:15]))


def test_TEKNIK_VERILMISKEN_NEDEN_IC_AYRINTI_TASIMIYOR():
    """(c) İki katmanın SIRASI: `teknik` doldurulmuşken `neden` hâlâ backtick'li alan adı ya da
    uç yolu taşıyorsa katmanlar ayrılmamış, ÇOĞALTILMIŞ demektir. (Üstteki dosya-geneli çivi
    aynı kuralı ölçer; buradaki çağrı-yeri hâli ihlali ÇAĞRIYLA birlikte raporlar.)"""
    ihlal = []
    for d, c in _hafiza_cagrilari():
        if not re.search(r"\bteknik=", c):
            continue
        m = re.search(r'neden="([^"\\\n]*)"', c)
        if m is None:
            continue
        for desen, ad in IC_AYRINTI:
            if desen.search(m.group(1)):
                ihlal.append(f"{d}: [{ad}] {m.group(1)[:90]}")
                break
    assert not ihlal, (
        f"{len(ihlal)} `neden` iç ayrıntı taşıyor (üstelik `teknik` doluyken):\n"
        + "\n".join(ihlal[:15]))


def test_CAGRI_TARAYICISI_sessizce_bos_DEGIL():
    """POZİTİF KONTROL (v314 disiplini): tarayıcı sentetik ihlalleri YAKALAMALI. Yoksa
    yukarıdaki üç "ihlal yok" cümlesi, regex'in kırılmasıyla aynı görünürdü."""
    tam, kirik = _acilis_etiketleri(
        '<Olculemedi neden="Kapsam sayısı gelmedi" kisa />'
        '<OlculemediHucre neden={`x${a > 0 ? `${a} satır` : ""}`} teknik="y" />'
        '<Olculemedi neden="`alan` yok" teknik="z" />')
    assert kirik == [] and len(tam) == 3, f"tarayıcı üç çağrıyı okuyamadı: {len(tam)}/{len(kirik)}"
    assert _SINIF_A.search(_neden_statik(tam[0]) or "") and not re.search(r"\bteknik=", tam[0]), \
        "sınıf-A + `teknik` yok deseni yakalanmıyor"
    assert re.search(r"\bteknik=", tam[1]), "iç içe şablonlu çağrıda `teknik` kaybediliyor"
    m = re.search(r'neden="([^"\\\n]*)"', tam[2])
    assert m and IC_AYRINTI[0][0].search(m.group(1)), "backtick'li `neden` yakalanmıyor"
    # `OlculemediHali` AYRI bir bileşendir ve bu tarayıcının konusu değildir.
    assert _acilis_etiketleri('<OlculemediHali a={a} />')[0] == []


def test_NEDEN_DEGERI_OKUYUCUSU_sessizce_bos_DEGIL():
    """POZİTİF KONTROL (Ö-1, 2026-09-03): `neden` değer okuyucusu ÜÇ biçimi de ayırt etmeli.
    Yoksa "saf ifade sayısı tavanın altında" cümlesi, okuyucunun her şeyi saf ifade sanmasıyla
    (ya da hiçbir şeyi) aynı görünürdü — ve sınıf-A kuralı sessizce boşalırdı."""
    duz, = _acilis_etiketleri('<Olculemedi neden="Kapsam sayısı gelmedi" />')[0]
    sablon, = _acilis_etiketleri('<Olculemedi neden={`${ne} okunamadı`} teknik={z} />')[0]
    ucluk, = _acilis_etiketleri('<Olculemedi neden={x ? "Başlık gelmedi" : "Başlık yok"} />')[0]
    saf, = _acilis_etiketleri('<Olculemedi neden={zarf.neden} teknik={z} />')[0]
    nedensiz, = _acilis_etiketleri('<Olculemedi kisa />')[0]

    assert _neden_statik(duz) == "Kapsam sayısı gelmedi"
    assert _neden_statik(sablon) == " okunamadı", "şablonun `${…}` dışı sabiti okunmuyor"
    assert _neden_statik(ucluk) == "Başlık gelmediBaşlık yok", "üçlünün iki dalı da okunmalı"
    assert _neden_statik(saf) is None, "saf ifade statik sanılıyor — kapsam şişer"
    assert _neden_statik(nedensiz) is None
    # Sınıf-A fiilleri SES BİRLİĞİ'nden TÜRER: sözlük fiilleri desende OLMALI, `yazılmamış` OLMAMALI.
    for fiil in SES_BIRLIGI:
        assert _SINIF_A.search(f"alan {fiil}"), f"SES BİRLİĞİ fiili sınıf-A desenine girmemiş: {fiil}"
    assert not _SINIF_A.search("alan yazılmamış"), \
        "`yazılmamış` desende — YASAK_ESANLAMLI ile ölü dal, kapsamı olduğundan geniş gösterir"

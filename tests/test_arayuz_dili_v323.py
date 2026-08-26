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
ORTAK = PANO / "yuzeyler/ogrenme/ortak.tsx"

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
    yerlerinde tek dizeye sıkışmaya devam eder."""
    s = ORTAK.read_text(encoding="utf-8")
    assert re.search(r"export function Olculemedi\([^)]*teknik", s, re.S), (
        "`Olculemedi` `teknik` katmanını taşımıyor — iç ayrıntı birincil metinde kalmak zorunda")


def test_TEKNIK_katmani_DUSURULMUYOR():
    """Aşırıya kaçma çivisi: `teknik` verilmişse EKRANDA bir yerde erişilebilir olmalı.
    Onu tamamen atmak, dürüstlük disiplinini (sebebi taşı) delerdi — teşhis kaybolur."""
    s = ORTAK.read_text(encoding="utf-8")
    govde = s[s.index("export function Olculemedi"):][:1200]
    assert "teknik" in govde and re.search(r"title=|{teknik}", govde), (
        "`teknik` bileşende kullanılmıyor — verilen sebep sessizce yutuluyor")


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
# sözlüğü DÖRT kelimeyle sınırlıdır ve her biri AYRI bir olguyu anlatır:
#     bildirilmedi   → yanıtta alan hiç gelmedi
#     kaydedilmemiş  → alan geldi ama kayda yazılmamış
#     okunamadı / hesaplanamadı → ölçüm denendi ve düştü
#     "Henüz … yok" → olgu henüz oluşmadı, sonra oluşacak
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

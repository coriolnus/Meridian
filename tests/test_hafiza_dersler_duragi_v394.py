"""test_hafiza_dersler_duragi_v394.py — [TSK-118] ⌘K "Meridian dersleri" = DOKUZUNCU HAFIZA
GÖRÜNÜMÜNÜN BEKÇİSİ (2026-09-03, operatör K8: "dokuzuncu nav durağı aç").

NUMARA ÇAKIŞMASI TARANDI (2026-09-03, brief kalemi): `ls tests | grep v394` BOŞ döndü
(v393 TSK-116'nındır — adaptörler/canlı evren katmanı, bu dilimle dosya-ayrık). v394 alındı.

TETİK: ROADMAP [TSK-118]. Bilgi Tabanı'nın "Meridian dersleri" sekmesi (`?sekme=dersler`)
ölçülmüş bir palet sınırına takılıyordu — PARK-1 (`komutlar.ts`): palet KENAR ÇUBUĞU
AĞACINDAN türer (`gezinme.ts` ← `alanlar.ts::YUZEYLER`) ve bir sekmeye inen madde eklemek,
kayıt sözlüğünün SAYMADIĞI bir kimlik eklemek olurdu (Rol-1 hükmü: sayaçlara dokunulmaz).
TSK-118 bu sınırı madde eklemeden, KAYNAĞI DEĞİŞTİREREK çözdü: dersler artık gerçek bir
bölüm (`hafiza-dersler`, `alanlar.ts::YUZEYLER.memory.bolumler`, 9. kayıt; 42→43 bölüm) —
"taşı, çoğaltma" (TSK-124 dersi): `MeridianDersleri.tsx` bileşeni Bilgi Tabanı'ndan ÇIKTI,
yeni görünümün gövdesi (`Dersler.tsx`) onu tek yerden çiziyor.

ÇİVİNİN SINIFI VE ZAYIFLIĞI AÇIKÇA YAZILI (v286/v288/v312/v378/v388 ailesinin kurulu
cevabı — "depoda `ui/` için test çatısı yok" bir engel değil, bu ailenin çözdüğü problem):
bu dosya TS/TSX'i METİN olarak okur. Ölçtüğü şey davranış DEĞİL, davranışı üreten satırın
VARLIĞIDIR. Zayıflık üç manuel mutasyonla telafi edildi (rapora yazılı): köprüyü kaldırmak,
Bilgi Tabanı'na sekmeyi geri koymak, palet anahtarını geri taşımak — üçü de bu dosyadaki
ilgili çiviyi ısırdı.
"""
from __future__ import annotations

import pathlib
import re

KOK = pathlib.Path(__file__).resolve().parents[1]
PANO = KOK / "ui/src/pano"
HAFIZA = PANO / "yuzeyler/hafiza"

ALANLAR = PANO / "alanlar.ts"
KOMUTLAR = PANO / "komutlar.ts"
GORUNUMLER = HAFIZA / "gorunumler.ts"
HAFIZA_YUZEYI = HAFIZA / "HafizaYuzey.tsx"
BILGI = HAFIZA / "BilgiTabani.tsx"
DERSLER_GORUNUMU = HAFIZA / "Dersler.tsx"
MERIDIAN_DERSLERI = HAFIZA / "MeridianDersleri.tsx"
SOHBET = PANO / "yuzeyler/ajan/SohbetHatti.tsx"

_YORUM = re.compile(r"/\*.*?\*/|(?<![:'\"])//[^\n]*", re.S)


def soy(p: pathlib.Path) -> str:
    """Şerhleri söker. Meridian'ın belge geleneği kararın gerekçesini yazarken YASAKLANAN
    ŞEYİ ALINTILAR; soymadan ölçen çivi kendi şerhini ihlal sanır (v286'nın `_soy` dersi)."""
    return _YORUM.sub(" ", p.read_text(encoding="utf-8"))


def test_olculen_dosyalar_YERINDE():
    """KÖRLÜK ALARMI: yol bayatlarsa aşağıdaki her `in` kontrolü sessizce boş metin okur ve
    çivi "temiz" der. Dosya varlığı ayrı ölçülür ki 'sıfır ihlal' bir okuma yokluğu olmasın."""
    for p in (ALANLAR, KOMUTLAR, GORUNUMLER, HAFIZA_YUZEYI, BILGI, DERSLER_GORUNUMU,
              MERIDIAN_DERSLERI, SOHBET):
        assert p.is_file(), f"ölçülecek dosya yok: {p}"
        assert len(p.read_text(encoding="utf-8")) > 200, f"dosya beklenmedik biçimde küçük: {p}"


def test_YORUM_SOKUCUSU_kendisi_olculuyor():
    """POZİTİF KONTROL (v378/v388 K6 emsali): sökücü çalışmıyorsa aşağıdaki VARLIK ve YOKLUK
    iddialarının hepsi sessizce yalan söyler."""
    ornek = 'const a = "IZ";\n// IZ\n/* IZ */\n{/* IZ */}\nconst b = `IZ`;\n'
    soyulmus = _YORUM.sub(" ", ornek)
    assert soyulmus.count("IZ") == 2, soyulmus
    kod = 'const re = /ab/g;\nif (a < b) { x(); }\nconst t = `${a}/${b}`;\n'
    assert _YORUM.sub(" ", kod) == kod, "sökücü bilinen bir kod bloğunu yiyor"


# ============================================================================
# (D2) KAYIT — 9. BÖLÜM, TEK KAYNAK (`alanlar.ts` ↔ `gorunumler.ts` ↔ `HafizaYuzey.tsx`)
# ============================================================================

def _memory_bolumler_kimlikleri() -> list[str]:
    # SINIR HAM METİNDE ARANIR (soy() DEĞİL): sınır işareti kendisi bir `//` yorumu
    # (`// ---- SAYFALAR`) ve `soy()` onu da söker — sökülmüş metinde arandığında
    # desen kendi ölçtüğü şeyi yok ederdi. Yalnız YAKALANAN blok soyulur (kimlik
    # bir yorumda "geçiyor olması" onun KULLANILDIĞI anlamına gelmez, v286 dersi).
    ham = ALANLAR.read_text(encoding="utf-8")
    m = re.search(r"\n  memory:\s*\{(.*?)\n  \},\n\n  // ---- SAYFALAR", ham, re.S)
    assert m, "YUZEYLER.memory bloğu okunamadı — desen bayat"
    return re.findall(r'kimlik:\s*"(hafiza-[a-z]+)"', soy_metin(m.group(1)))


def soy_metin(metin: str) -> str:
    return _YORUM.sub(" ", metin)


def test_hafiza_KAYITTA_dokuz_bolum_VAR():
    kimlikler = _memory_bolumler_kimlikleri()
    assert kimlikler.count("hafiza-dersler") == 1, "hafiza-dersler kaydı yok ya da tekil değil"
    assert len(kimlikler) == 9, f"YUZEYLER.memory.bolumler dokuz değil: {len(kimlikler)} ({kimlikler})"


def test_dersler_kaydinin_BASLIK_VE_SORUSU():
    a = soy(ALANLAR)
    m = re.search(r'\{\s*kimlik:\s*"hafiza-dersler",\s*baslik:\s*"([^"]+)",\s*soru:\s*"([^"]+)"', a)
    assert m, "hafiza-dersler kaydı beklenen biçimde okunamadı"
    assert m.group(1) == "Meridian dersleri", f"başlık {m.group(1)!r}"
    assert m.group(2), "soru boş"


def test_gorunum_LISTESINDE_dokuz_kimlik_dogru_SIRAYLA():
    g = soy(GORUNUMLER)
    m = re.search(r"HAFIZA_GORUNUMLERI\s*=\s*\[(.*?)\]\s*as const", g, re.S)
    assert m, "HAFIZA_GORUNUMLERI dizisi okunamadı — desen bayat"
    kimlikler = re.findall(r'"(hafiza-[a-z]+)"', m.group(1))
    assert kimlikler == [
        "hafiza-anasayfa", "hafiza-bellekler", "hafiza-bilgi", "hafiza-recall",
        "hafiza-reflect", "hafiza-belgeler", "hafiza-varliklar", "hafiza-yapilandirma",
        "hafiza-dersler",
    ], f"sıra ya da küme bozuk: {kimlikler}"


def test_govde_TABLOSUNDA_dersler_govdesi_VAR():
    """`HafizaYuzey.tsx::GOVDELER` dokuz görünümü eşlemeli — biri düşerse `Record<...>` tipi
    derlemeyi kırar (dosyanın kendi disiplini), ama ad yanlışsa derleme geçer, ekran sessiz
    kalır. Bu çivi adı da ölçüyor."""
    s = soy(HAFIZA_YUZEYI)
    assert '"hafiza-dersler": Dersler,' in s, "GOVDELER tablosunda hafiza-dersler görünümü yok"
    assert 'import { Dersler } from "./Dersler";' in s, "Dersler görünüm gövdesi içe aktarılmıyor"


def test_dersler_govdesinin_EKRAN_CAPASI_VAR():
    """v288 parite deseni (BİLEŞİK biçim): `BolumKart` `id={\\`bolum-${kimlik}\\`}` üretir ve
    regex bunu GÖREMEZ — v288'in kendi çözümü çağrı yerindeki `kimlik="..."` literalini
    okumaktır. O yüzden bu propun LİTERAL (değişken değil) yazılması zorunlu."""
    s = soy(DERSLER_GORUNUMU)
    assert 'kimlik="hafiza-dersler"' in s, "BolumKart çağrısı kimlik propunu literal taşımıyor"


# ============================================================================
# (D1) TAŞI, ÇOĞALTMA — BİLEŞEN TEK YERDEN İTHAL EDİLİR (TSK-124 dersi)
# ============================================================================

def test_bilesen_TEK_YERDEN_import_ediliyor():
    assert 'from "./MeridianDersleri"' not in soy(BILGI), \
        "BilgiTabani.tsx hâlâ MeridianDersleri'ni içe aktarıyor — iki yerden erişim kopya riski"
    assert 'from "./MeridianDersleri"' in soy(DERSLER_GORUNUMU), \
        "Dersler.tsx (görünüm gövdesi) MeridianDersleri'ni içe aktarmıyor"


def test_bilgi_tabaninda_DERSLER_SEKMESI_yok():
    s = soy(BILGI)
    assert 'value="dersler"' not in s, "Bilgi Tabanı hâlâ üçüncü bir 'dersler' sekme değeri taşıyor"
    assert "Meridian dersleri" not in s, "Bilgi Tabanı hâlâ 'Meridian dersleri' metnini basıyor"
    tetikleyiciler = re.findall(r"<TabsTrigger", s)
    assert len(tetikleyiciler) == 2, f"Bilgi Tabanı iki değil {len(tetikleyiciler)} sekme taşıyor"


def test_bilgi_sekmeleri_LISTESI_ikiye_dustu():
    g = soy(GORUNUMLER)
    assert 'HAFIZA_BILGI_SEKMELERI = ["sayfalar", "modeller"] as const' in g, \
        "sekme listesi hâlâ üç değer taşıyor (ya da desen bayat)"


# ============================================================================
# (D3) KÖPRÜ — ESKİ SEKME ADRESİ (`?sekme=dersler`) YENİ GÖRÜNÜME ÇÖZÜLÜR
# ============================================================================

def test_gorunumCoz_ESKI_SEKME_ADRESINI_kopruluyor():
    """`ESKI_GORUNUM_ADRESLERI` yalnız BÖLÜM dizgelerini eşliyor; eski sekme adresi bölüm+sorgu
    BİLEŞİMİ olduğu için `gorunumCoz` kendi köprüsünü taşımalı — yoksa `hafiza-bilgi?sekme=
    dersler` yazan eski bir bağ (sohbet geçmişi, operatör yer imi) sessizce 'sayfalar'a düşer."""
    g = soy(GORUNUMLER)
    assert 'if (bolum === "hafiza-bilgi" && sorgu?.[SEKME_SORGU_ADI] === "dersler") ' \
           'return "hafiza-dersler";' in g, \
        "eski sekme adresi (`hafiza-bilgi?sekme=dersler`) yeni görünüme çözülmüyor"


def test_HafizaYuzey_sorguyu_KOPRUYE_TASIYOR():
    s = soy(HAFIZA_YUZEYI)
    assert re.search(r"gorunumCoz\(\s*bolum\s*,\s*sorgu\s*\)", s), \
        "gorunumCoz çağrısı sorguyu almıyor — köprü hiç tetiklenmez (sorgu okunmadan geçer)"


def test_hafiza_TAKMA_ADI_DOGRUDAN_GORUNUME_bagli():
    """`#hafiza` yer imi artık doğrudan görünüme bağlı — köprüden AYRI bir giriş kapısı
    (`ROTA_TAKMA_ADLARI` bölüm dizgesi taşır, sorgu bileşimi değil)."""
    a = soy(ALANLAR)
    assert 'hafiza: { yuzey: "memory", bolum: "hafiza-dersler" }' in a, \
        "`#hafiza` yer imi hâlâ eski sekme adresine (ya da başka bir hedefe) bağlı"


def test_sohbet_baginin_ADRESI_gorunume_gidiyor():
    s = soy(SOHBET)
    assert "#/dashboard/memory/hafiza-dersler" in s, \
        "sohbet hattındaki ders bağı hâlâ eski (sekmeli) adrese gidiyor"
    assert "sekme=dersler" not in s, \
        "sohbet hattı hâlâ emekli sekme adresini üretiyor — köprü YALNIZ eski bağlar için var"


# ============================================================================
# (D4) PALET — ANAHTARLAR TAŞINDI, PARK-1 GÜNCELLENDİ (SESKMEYE DEĞİL GÖRÜNÜME)
# ============================================================================

def _bolum_ek(kimlik: str) -> list[str]:
    """`BOLUM_EK` tablosundan bir bölümün anahtar listesi. Tablo TEK kaynak (v388 deseni);
    ayrı bir kopya yazsaydık çivi kendi kopyasını doğrulardı."""
    s = soy(KOMUTLAR)
    blok = re.search(r"const BOLUM_EK[^=]*=\s*\{(.*?)\n\};", s, re.S)
    assert blok, "BOLUM_EK tablosu okunamadı — desen bayat"
    satir = re.search(rf'"{re.escape(kimlik)}":\s*\[(.*?)\]', blok.group(1), re.S)
    assert satir, f"{kimlik} satırı BOLUM_EK'te yok"
    return re.findall(r'"([^"]+)"', satir.group(1))


def test_palet_anahtarlari_DERSLER_govdesine_tasindi():
    hedef = _bolum_ek("hafiza-dersler")
    for k in ("ders", "lesson", "lessons.md", "damitim"):
        assert k in hedef, f"palet anahtarı hafiza-dersler'e taşınmamış: {k!r}"
    kaynak = _bolum_ek("hafiza-bilgi")
    for k in ("ders", "lesson", "lessons.md", "damitim"):
        assert k not in kaynak, f"palet anahtarı hâlâ hafiza-bilgi'de duruyor: {k!r} (kopya risk)"


def test_PARK1_beyani_TERSINE_CEVRILMEDI_GUNCELLENDI():
    """PARK-1'in ilkesi ("palet sekmeye değil görünüme iner") TSK-118'de BOZULMADI — dersler
    sekme olmaktan çıktığı için aynı ilkeyle çelişmeden gerçek bir kayda kavuştu. Şerh bunu
    künyeli anlatmalı, yoksa bir sonraki okuyucu ilkenin ihlal edildiğini sanır."""
    k = KOMUTLAR.read_text(encoding="utf-8")
    assert "PALET SEKMEYE DEĞİL GÖRÜNÜME İNER" in k, \
        "paletin sekmeye inmemesi beyansız — sessiz bir eksik ölçülmüş bir sınır gibi görünür"
    assert "TSK-118" in k, "TSK-118 künyesi PARK-1 civarında yok — güncellemenin tarihi kayıp"


# ============================================================================
# (MERIDIANDERSLERI.tsx) ÇAĞRILDIĞI YER GÜNCEL — EKRANDAKİ METİN "SEKME" DEMİYOR
# ============================================================================

def test_dersler_bileseni_kendini_SEKME_diye_TANITMIYOR():
    """Operatör-yüzü metin de doğru olmalı: bileşen artık bir sekme değil, kendi görünümü.
    Ekranda 'Bu sekme üst yüzeyde yok' demeye devam etmek, taşımadan sonra ekranı kendi
    adresiyle çelişen bir cümleyle bırakırdı (bu dosyanın kendi 'kendini yalanlama' sınıfı)."""
    soyulmus = soy(MERIDIAN_DERSLERI)
    assert "Bu sekme üst yüzeyde yok" not in soyulmus, \
        "bileşen kendini hâlâ bir sekme olarak tanıtıyor (ekranda VE şerhte)"

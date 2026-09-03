"""test_kovab_b12_v384.py — `Kapi<T>` ÜÇ/DÖRT HÂL KAPISININ TEK KAYNAĞI (TSK-113, 2026-09-03).

NUMARA ÇAKIŞMASI TARANDI (2026-09-03, KOVA B B-12 dilimi): `ls tests | grep v384` boş döndü ve
deponun tamamında (`.git`/`node_modules` hariç) `v384` dizgesi HİÇ geçmiyordu — v384 BOŞTU. Bu
dosya numarayı alan ilk yazımdır.

ÖLÇÜM (dilim başı, Rol-1 + ajan doğrulaması): yedi dosya kendi `Kapi<T>` tanımını taşıyordu —
`yuzeyler/{sistem,kuyruk,kimlik,yetki}/parcalar.tsx` + `yuzeyler/{ogrenme,ajan,analiz}/ortak.tsx`
(36/35/36/34/40/57/40 satır, dört ayrı md5 gövde; ogrenme ≡ analiz). Gövdeler İKİ DAVRANIŞ
AİLESİNE ayrıldı ve ayrım kozmetik DEĞİLDİ:

  * A ailesi (sistem/kuyruk/kimlik/yetki) — `Alert` kabuğu, etiket `yol`; `hata !== null` VERİYİ
    EZER (bayat gövde HİÇ çizilmez); iskelet `veri === null` ile.
  * B ailesi (ogrenme/analiz/ajan) — `Bildiri` kabuğu, etiket `ad`; `hata` yalnız VERİ YOKKEN
    kart olur, veri varken BAYAT ŞERİDİ olur; iskelet `veri === null && yukleniyor` ile.

Yani "yedi kopya" tek bir gövdenin yedi kez yazılması değildi: iki ayrı durum makinesi + dört ayrı
metin kümesiydi. Tek kaynağa indirirken EKRAN DEĞİŞMEZ kuralı bu yüzden kabuk (`KapiKabugu`)
enjeksiyonuyla korundu — KARAR tek yerde, ÇİZİM yüzeyde. İki durum makinesi tek sıraya, TEK
BEYANLI ayrımla indi: `kabuk.bayat === null` ⇒ bu yüzeyin bayat şeridi YOKTUR ⇒ hata veriyi ezer.
Ayrım uydurma bir bayrak değil, kabuğun kendi eksikliğinden TÜRETİLİR.

BEYANLI BEDEL: `kuyruk`un `Kapi`si artık `iskelet?` prop'unu da kabul eder (eski gövdesinde yoktu)
ve A ailesinin dördü de aynı bağı paylaşır — prop yüzeyi genişledi, çizim değişmedi.

ÇİVİNİN SINIFI VE ZAYIFLIĞI (v286/v288/v314/v323/v324/v373/v378/v380/v381 ailesi): TSX METİN
olarak okunur; ölçülen şey davranış değil, davranışı üreten satırın varlığı ve biçimidir.
v381'deki "≥7" sayımı bu dilimde "== 1"e çevrildi ve orada gerekçesi yazılı.

İTHAL EDİLEN VE KASITLI OLARAK EDİLMEYEN (düzeltme turu 1, inceleme K-3, 2026-09-03 — önceki
cümle "tarayıcı İTHAL EDİLİR (kopyalanmaz)" diyordu ve dosyanın kendisiyle çelişiyordu):
  * `ESKI_KOPYALAR` listesi ve `soy()` v381'den İTHAL edilir — tek kaynak,
  * `_kapi_kopyalarini_bul()` de ithal edilir ve `test_v381_tarayicisi_da_TEK_dosya_goruyor`ta
    KULLANILIR,
  * ama `test_kapi_tanimi_PANO_GENELINDE_TAM_BIR` taramayı BİLEREK yeniden yazar: ölçülen şey
    orada "tanım tam 1 mi" DEĞİL, "aynı gerçeği ölçen İKİ BAĞIMSIZ tarayıcı hemfikir mi"dir.
    Tek tarayıcının sessizce kırılması iki testi birden yeşile boyardı; ayrışırlarsa hangisinin
    haklı olduğu soruşturulur. Bu bir kopya DEĞİL, kasıtlı ikinci ölçümdür ve maliyeti beyanlı:
    desen iki yerde durur, ikisi de `function Kapi<` dizgesine bakar.
"""
from __future__ import annotations

import pathlib
import re

# TEK KAYNAK: yardımcı DA liste DE v381'de yaşıyor, buraya kopyalanmaz (düzeltme turu 1,
# inceleme Ö-4, 2026-09-03 — liste v381'in çare-taramasının kapsamına girdiği için evi orası).
from tests.test_pano_bayat_govde_v381 import ESKI_KOPYALAR, _kapi_kopyalarini_bul, soy

KOK = pathlib.Path(__file__).resolve().parents[1]
PANO = KOK / "ui/src/pano"
ORTAK = PANO / "parcalar/kapi.tsx"


def test_olculen_dosyalar_YERINDE():
    """KÖRLÜK ALARMI (v380/v381 kalıbı): yol bayatlarsa aşağıdaki her `in` kontrolü sessizce boş
    metin okur ve çivi "temiz" der. Dosya varlığı ve asgari boyut AYRI ölçülür."""
    assert ORTAK.is_file(), f"ortak Kapi modülü yok: {ORTAK}"
    assert len(ORTAK.read_text(encoding="utf-8")) > 800, "ortak modül beklenmedik biçimde küçük"
    for yol in ESKI_KOPYALAR:
        p = PANO / yol
        assert p.is_file(), f"ölçülecek dosya yok: {p}"
        assert len(p.read_text(encoding="utf-8")) > 200, f"dosya beklenmedik biçimde küçük: {p}"


# ============================================================================
# (1) TEK TANIM
# ============================================================================

def test_kapi_tanimi_PANO_GENELINDE_TAM_BIR():
    """`ui/src/pano/**` içinde `function Kapi<` tanımı TAM 1 olmalı. Tarama `yuzeyler/` ile
    sınırlı DEĞİL: tanım artık `parcalar/` altında yaşıyor ve dar bir tarama onu göremeyip
    "kopya yok" derdi — kendi körlüğünü ölçemeyen çivi sessizdir."""
    bulunan = sorted(
        p.relative_to(PANO).as_posix()
        for p in PANO.rglob("*.tsx")
        if re.search(r"function Kapi<", soy(p))
    )
    assert bulunan == ["parcalar/kapi.tsx"], (
        f"`function Kapi<` tanımı tam 1 değil (beklenen: parcalar/kapi.tsx): {bulunan}"
    )


def test_v381_tarayicisi_da_TEK_dosya_goruyor():
    """Aynı gerçeği ölçen İKİ tarayıcı ayrışmasın (tek-kaynak yasası): v381'in yardımcısı
    ithal edilir, kopyalanmaz; ikisi de aynı tek dosyayı görmeli."""
    kopyalar = [p.relative_to(PANO).as_posix() for p in _kapi_kopyalarini_bul()]
    assert kopyalar == ["parcalar/kapi.tsx"], f"v381 tarayıcısı tek kaynağı görmüyor: {kopyalar}"


def test_TARAYICI_sessizce_bos_DEGIL():
    """POZİTİF KONTROL (v314 disiplini): tarama deseni sentetik bir kopyayı YAKALAMALI, aksi
    hâlde "tam 1" cümlesi regex'in kırılmasıyla aynı görünürdü."""
    desen = re.compile(r"function Kapi<")
    assert desen.search("export function Kapi<T>({ durum }) {")
    assert desen.search("  return function Kapi<T>(o) {")
    assert not desen.search("export function KapiTablosu({ ozet }) {")
    assert not desen.search("export const Kapi = kapiKur(yolKabugu());")


# ============================================================================
# (2) YEDİ ESKİ DOSYA — TANIM SÖKÜLDÜ, `Kapi` HÂLÂ DIŞA AKTARILIYOR
# ============================================================================

def test_yedi_dosya_KENDI_TANIMINI_TASIMIYOR():
    kirli = [y for y in ESKI_KOPYALAR if re.search(r"function Kapi<", soy(PANO / y))]
    assert kirli == [], f"eski kopya geri gelmiş: {kirli}"


def test_yedi_dosya_ORTAK_MODULU_ICE_AKTARIYOR():
    """Tanımı sökmek yetmez — yüzey ortak modüle BAĞLANMIŞ olmalı. Bağlanmadan silinseydi
    `Kapi` dışa aktarımı kaybolur ve 48 tüketicinin import yolu kırılırdı."""
    eksik = [y for y in ESKI_KOPYALAR if "parcalar/kapi" not in soy(PANO / y)]
    assert eksik == [], f"ortak `Kapi` modülünü içe aktarmayan yüzey: {eksik}"


def test_yedi_dosya_KAPIYI_DISA_AKTARIYOR():
    """Tüketicilerin import YOLU değişmedi (re-export kabul, tek kaynak = tek TANIM):
    her yüzey dosyası hâlâ `Kapi` adını dışa aktarmalı."""
    disari = re.compile(r"export\s+(?:const\s+Kapi\b|\{[^}]*\bKapi\b[^}]*\}\s*from)")
    eksik = [y for y in ESKI_KOPYALAR if not disari.search(soy(PANO / y))]
    assert eksik == [], f"`Kapi` dışa aktarımı kaybolmuş: {eksik}"


# ============================================================================
# (3) ORTAK MODÜLÜN SÖZLEŞMESİ — İKİ AİLE, TEK SIRA
# ============================================================================

def test_ortak_modul_KABUK_enjeksiyonu_tasiyor():
    s = soy(ORTAK)
    for iz in ("KapiKabugu", "kapiKur", "yolKabugu"):
        assert iz in s, f"ortak modülde `{iz}` yok — kabuk enjeksiyonu kurulmamış"


def test_bayat_ayrimi_KABUGUN_EKSIKLIGINDEN_turetilir():
    """A ve B ailelerinin TEK davranış ayrımı beyanlı ve TÜRETİLMİŞ olmalı: bayat şeridi
    çizemeyen kabukta hata veriyi ezer. Elle bir `aile: "A" | "B"` bayrağı olsaydı iki gerçek
    (kabuk + bayrak) sessizce ayrışabilirdi."""
    s = soy(ORTAK)
    assert re.search(r"kabuk\.bayat\s*!==\s*null", s), \
        "bayat politikası kabuğun kendisinden türetilmiyor"
    assert re.search(r"durum\.veri\s*===\s*null\s*\)", s), "`veri === null` dalı yok"
    assert "durum.oturumDustu" in s, "401 dalı yok — 401 `hata`dan AYRI çare ister"
    assert "durum.yukleniyor" in s, "B ailesinin iskelet/boş ayrımı (`yukleniyor`) yok"


def test_A_ailesi_401_metni_EKLENEBILIR_ama_govde_TEK():
    """`kimlik` yüzeyi 401 cümlesine "(Giriş yüzeyi)" ekliyordu — bu fark bir KOPYA gerekçesi
    değil, bir PARAMETREdir. Ek metin kabuk kurucusundan gelmeli."""
    s = soy(ORTAK)
    assert "oturumEki" in s, "A ailesinin 401 eki parametreye çevrilmemiş"
    assert "(Giriş yüzeyi)" in soy(PANO / "yuzeyler/kimlik/parcalar.tsx"), \
        "kimlik yüzeyinin 401 eki kaybolmuş — ekran DEĞİŞTİ"


def test_Durum_sozlesmesi_DEGISMEDI():
    """TSK-110'un sözleşmesi: `Durum<T>` arayüzü SABİT. Kapı tek kaynağa inerken alan eklemek
    48 tüketiciyi ve v381'in tüm ölçümünü sessizce kaydırırdı."""
    s = soy(PANO / "veri.ts")
    m = re.search(r"export interface Durum<T>\s*\{(.*?)\n\}", s, re.S)
    assert m, "Durum<T> arayüzü veri.ts'te bulunamadı"
    alanlar = sorted(re.findall(r"readonly\s+(\w+)\s*[:?]", m.group(1)))
    assert alanlar == ["hata", "oturumDustu", "tazele", "veri", "yukleniyor", "zaman"], \
        f"Durum<T> alan kümesi değişmiş: {alanlar}"

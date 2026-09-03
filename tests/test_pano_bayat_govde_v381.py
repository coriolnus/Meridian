"""test_pano_bayat_govde_v381.py — `useApi` YOL-BAĞLI OKUMA SÖZLEŞMESİNİN BEKÇİSİ (2026-09-03).

TSK-110: TSK-108 T3 incelemesi (M-7) ÖLÇTÜ — çekmece/kapı yeniden açılınca (yol A→B) `useApi`
ESKİ yolun gövdesini/hatasını yeni başlığın altında taşıyordu. Kök neden tüketici hatası DEĞİL:
`veri.ts::useApi` `veri`/`hata` durumlarını `yol`dan BAĞIMSIZ tutuyordu — dönüş hangi yola ait
olduğunu bilmiyordu. Çare TEK KAYNAK, TEK DOSYA: `Durum<T>` ARAYÜZÜ SABİT kalır (hiçbir tüketici
ve hiçbir `Kapi` kopyası dokunulmaz), iç durum yol-bağlı KAYDA döner (`okuma`/`hataKaydi`, ikisi de
`yol` taşır) ve dönüş yol EŞİTLİĞİYLE TÜRETİLİR — efekte sıfırlama DEĞİL (sıfırlama bir kare bayat
gövde çizdirirdi, TSK-112 anahtar dersiyle aynı sınıf).

NUMARA ÇAKIŞMASI TARANDI (2026-09-03): alınmış son numara v380 idi (`test_hafiza_varlik_paneli_v380.py`,
bu turda ayrıca commit'lenmemiş; `git status --porcelain` ile görüldü); `ls tests | grep v381` boş
döndü, deponun kalanında da yalnız bu dosyanın kendi tarama notunda geçiyor. v381 BOŞTU.

ÇİVİNİN SINIFI VE ZAYIFLIĞI AÇIKÇA YAZILI: bu dosya TSX/TS'i METİN olarak okur (v286/v288/v314/
v323/v324/v373/v378/v380 ailesinin kurulu cevabı — "depoda `ui/` için test çatısı yok" bir engel
değil, bu ailenin çözdüğü problemdir). Ölçtüğü şey davranış DEĞİL, davranışı üreten satırın
varlığı ve biçimidir. Zayıflığı mutasyonla telafi edilir (rapora yazılan tablo): eşitliği kaldırmak,
efekte `setOkuma(null)` eklemek, `hata`yı yolsuz bırakmak, `Durum<T>`e alan eklemek — dördü de en
az bir çiviyi kırmalı.

DÜZELTME TURU 1 (inceleme `task-110-review.md`, 2026-09-03):
- Önemli-1: ilk turun ELLE YAZILMIŞ "beş `Kapi` kopyası" listesi EKSİKTİ — `kimlik/parcalar.tsx` ve
  `yetki/parcalar.tsx` (`function Kapi<` tanımı taşıyorlar) taramaya HİÇ girmiyordu. Liste artık ELLE
  YAZILMAZ: `_kapi_kopyalarini_bul()` `ui/src/pano/**/*.tsx` içinde `function Kapi<` tanımı
  taşıyan HER dosyayı tarar; ayrıca sayının == 1 olduğu AYRI bir testte ölçülür ki tarama kırılıp
  boş/az dönerse "hiçbiri çare kurmamış" testi anlamsızca YEŞİL kalmasın (körlük alarmı).
  (Kapsam `yuzeyler/**`→`pano/**` ve eşik ≥7→==1 TSK-113'te değişti; gerekçe
  `_kapi_kopyalarini_bul` ile `test_kapi_kopya_sayisi_TAM_BIR_olculuyor` docstring'lerinde.)
- Önemli-2: `yukleniyor` artık TÜRETİLİYOR (`yukleniyorDurumu || (yol !== null && guncel === null &&
  hata === null && !oturumDustu)`) — yol değiştiği ANDA, efekt henüz koşmadan, "bu yol için ne okuma
  ne hata var" durumu render sırasında hesaplanır; yalnız efekt-state'e güvenmek bir kare
  "veri=null + yukleniyor=false + hata=null" görünmesine (iskelet VE yükleniyor göstergesi birlikte
  kapanmasına) yol açardı.
- Küçük: `test_hataKaydi_null_YALNIZ_basari_dalinda` adı yeniden adlandırıldı — `setHataKaydi(null)`
  AYRICA oturum-düşme (401) dalında da KASITLI çağrılıyor; isim artık bunu söylüyor.
- Küçük-2: tek-slot kayıt (yol-başına ayrı önbellek DEĞİL) niteliği `veri.ts` şerhine açıkça yazıldı.
"""
from __future__ import annotations

import pathlib
import re

KOK = pathlib.Path(__file__).resolve().parents[1]
PANO = KOK / "ui/src/pano"
VERI = PANO / "veri.ts"

_YORUM = re.compile(r"/\*.*?\*/|(?<![:'\"])//[^\n]*", re.S)


def soy(p: pathlib.Path) -> str:
    """Şerhleri söker. Meridian'ın belge geleneği kararın gerekçesini yazarken YASAKLANAN
    ŞEYİ ALINTILAR; soymadan ölçen çivi kendi şerhini ihlal sanır (v286'nın `_soy` dersi)."""
    return _YORUM.sub(" ", p.read_text(encoding="utf-8"))


_KAPI_TANIM = re.compile(r"function Kapi<")


def _kapi_kopyalarini_bul() -> tuple[pathlib.Path, ...]:
    """`ui/src/pano/**/*.tsx` içinde `function Kapi<` tanımı taşıyan HER dosya —
    ELLE YAZILMIŞ bir liste DEĞİL (düzeltme turu 1, inceleme Önemli-1, 2026-09-03): ilk turun
    elle yazılmış 5'lik listesi `kimlik/parcalar.tsx` ve `yetki/parcalar.tsx`'i kaçırmıştı —
    ikisi de kendi `Kapi<T>` tanımını taşıyor ama listeye HİÇ girmemişti. Bu tarama yeni bir
    kopya doğduğunda da OTOMATİK yakalar; sayı ayrıca `test_kapi_kopya_sayisi_TAM_BIR_olculuyor`
    ile ölçülür ki tarama kırılıp boş/az dönmesi "hiçbiri çare kurmamış" testini anlamsızca
    YEŞİL bırakmasın.

    KAPSAM GENİŞLEDİ (TSK-113, 2026-09-03): tarama `yuzeyler/` ile SINIRLIYDI. Tek kaynağa
    inildiğinde tanım `parcalar/kapi.tsx`e taşındı — dar tarama onu göremez ve "kopya yok"
    derdi; yani çivi tam işini bitirdiği gün kör olurdu. Kapsam `pano/**`."""
    return tuple(sorted(
        p for p in PANO.rglob("*.tsx")
        if _KAPI_TANIM.search(soy(p))
    ))


#: TSK-113 ÖNCESİ kendi `Kapi<T>` tanımını taşıyan yedi yüzey (PANO-göreli). ELLE YAZILI OLMASI
#: KASITLI: bu liste "kimin tanımı SÖKÜLDÜ" TARİHİNİ taşır, "bugün kimde tanım var" sorusunu
#: DEĞİL — ikincisini `_kapi_kopyalarini_bul()` dinamik yanıtlar. Buraya v384'ten TAŞINDI
#: (düzeltme turu 1, inceleme Ö-4, 2026-09-03): yardımcının evi burasıdır, v384 ithal eder.
ESKI_KOPYALAR = (
    "yuzeyler/sistem/parcalar.tsx",
    "yuzeyler/kuyruk/parcalar.tsx",
    "yuzeyler/kimlik/parcalar.tsx",
    "yuzeyler/yetki/parcalar.tsx",
    "yuzeyler/ogrenme/ortak.tsx",
    "yuzeyler/ajan/ortak.tsx",
    "yuzeyler/analiz/ortak.tsx",
)


def _kapi_yuzeyleri() -> tuple[pathlib.Path, ...]:
    """Bayatlık-çaresi taramasının KAPSAMI: bugünkü tek kaynak + TSK-113 öncesi yedi yüzey.

    BEDEL YASASI (§4; düzeltme turu 1, inceleme Ö-4, 2026-09-03): TSK-113 yedi tanımı bire
    indirince `_kapi_kopyalarini_bul()` tek dosya döndürmeye başladı ve aşağıdaki çare-taraması
    SESSİZCE 7 dosyadan 1'e daraldı — yani çivi tam işini bitirdiği gün kapsamının altısını
    kaybetti. Kayıp ÖLÇÜLDÜ: yedi yüzeyden birine `sonYol` deseni eklemek hiçbir çiviyi
    ötürtmüyordu (2026-09-03). Yüzeyler artık tanımı taşımıyor ama hâlâ `Kapi`yi bağlıyor ve
    çizen taraf ONLAR: birinin yarın kendi bayatlık çaresini kurması TSK-110'un tam kapattığı
    sınıftır. Kapsam bu yüzden İKİ kaynağın birleşimidir (dinamik + tarihsel)."""
    yollar = list(_kapi_kopyalarini_bul()) + [PANO / y for y in ESKI_KOPYALAR]
    return tuple(dict.fromkeys(yollar))   # sıra korunur, yinelenen düşer


def test_olculen_dosyalar_YERINDE():
    """KÖRLÜK ALARMI: yol bayatlarsa aşağıdaki her `in` kontrolü sessizce boş metin okur ve
    çivi "temiz" der. Dosya varlığı ayrı ölçülür ki 'sıfır ihlal' bir okuma yokluğu olmasın.
    Kapsam `_kapi_yuzeyleri()`tir (dinamik tek kaynak + yedi tarihsel yüzey, Ö-4)."""
    for p in (VERI, *_kapi_yuzeyleri()):
        assert p.is_file(), f"ölçülecek dosya yok: {p}"
        assert len(p.read_text(encoding="utf-8")) > 200, f"dosya beklenmedik biçimde küçük: {p}"


# ============================================================================
# (1) İÇ DURUM — okuma/hata KAYDI `yol` TAŞIR (tek atomik kayıt)
# ============================================================================

def test_okuma_kaydi_yolu_veriyi_zamani_TEK_KAYITTA_tasir():
    """`veri` ve `zaman` ayrı `useState` yerine TEK kayıtta olmalı — ayrı tutulsalar biri
    güncellenip diğeri bir kare geriden gelebilir (TSK-108 T3 M-7 sınıfı)."""
    s = soy(VERI)
    assert re.search(
        r"readonly\s+yol:\s*string;\s*readonly\s+veri:\s*T;\s*readonly\s+zaman:\s*Date",
        s,
    ), "okuma kaydı yol/veri/zaman'ı tek kayıtta taşımıyor"


def test_hata_kaydi_yolu_tasir():
    s = soy(VERI)
    assert re.search(r"readonly\s+yol:\s*string;\s*readonly\s+metin:\s*string", s), \
        "hata kaydı yol'u taşımıyor"


# ============================================================================
# (2) DÖNÜŞ — YOL EŞİTLİĞİYLE TÜRETİLİR (efekte sıfırlama DEĞİL)
# ============================================================================

def test_guncel_veri_yol_esitligiyle_turetiliyor():
    s = soy(VERI)
    assert "okuma !== null && okuma.yol === yol" in s, \
        "güncel veri yol eşitliğiyle türetilmiyor — bayat gövde yeni yolun altında çizilebilir"


def test_guncel_hata_yol_esitligiyle_turetiliyor():
    s = soy(VERI)
    assert "hataKaydi !== null && hataKaydi.yol === yol" in s, \
        "güncel hata yol eşitliğiyle türetilmiyor — eski yolun hatası yeni yolun altında çizilebilir"


def test_efektte_SIFIRLAMA_yok_setOkuma_null_HIC_YOK():
    """TÜRETİM ile SIFIRLAMA ayrı çare: yol değişince `setOkuma(null)` çağırmak bir kare
    bayat gövde çizdirir (boyama → sonra efekt), türetim ise render sırasında anında düşer.
    Bu yüzden `setOkuma(null)` dosyada HİÇ olmamalı — yalnız türetilmiş `guncel` yol
    eşleşmediğinde `null` olur."""
    s = soy(VERI)
    assert "setOkuma(null)" not in s, \
        "efekt veriyi sıfırlıyor — türetim yerine sıfırlama bir kare bayat gövde çizdirir"


def test_hataKaydi_null_basari_VE_oturum_dalinda_temizlenir():
    """`setHataKaydi(null)` İKİ dalda çağrılır ve İKİSİ de KASITLI (düzeltme turu 1, inceleme
    Küçük, 2026-09-03 — ilk turun ismi yalnız 'başarı' diyordu, gerçek kapsamdan dardı):
    (a) başarı dalı — yeni okumanın hatası olmadığını işaretler; (b) oturum-düşme (401,
    `OturumHatasi`) dalı — 401'de ekranda AYNI ANDA hem eski 'okunamadı' metni hem 'oturum
    düştü' gösterilmesin diye eski hata silinir. Ağ/sunucu HATASI dalında ise `hataKaydi`
    YOLLA birlikte SET edilir, silinmez (asıl ölçülen fark BURADA)."""
    s = soy(VERI)
    assert s.count("setHataKaydi(null)") == 2, (
        "setHataKaydi(null) iki dal dışında bir yerde çağrılıyor ya da eksik "
        "(başarı + oturum düşmesi KASITLI olarak ikisi de temizler)"
    )
    assert re.search(r"OturumHatasi\)\s*\{\s*setOturumDustu\(true\);\s*setHataKaydi\(null\);", s), \
        "oturum düşmesi dalı hataKaydi'yi temizlemiyor"
    # hata (ağ/sunucu) dalında hataKaydi yol taşıyan bir nesneyle SET edilmeli, null ile DEĞİL.
    assert re.search(r"setHataKaydi\(\{\s*yol,\s*metin", s), \
        "hata dalı hataKaydi'yi yol taşıyan kayıtla set etmiyor"


def test_yukleniyor_TEK_KAREDE_TURETILIYOR():
    """Önemli-2 (düzeltme turu 1, inceleme, 2026-09-03): `yol` değiştiği ANDA efekt henüz
    koşmamıştır (efekt render'dan SONRA çalışır) — yalnız efekt-state'e güvenmek bir kare
    'veri=null (doğru) + yukleniyor=false (henüz güncellenmemiş) + hata=null' görünmesine yol
    açar. `yukleniyorDurumu || (bu yol için ne okuma ne hata var)` türetimi bu kareyi kapatır."""
    s = soy(VERI)
    assert re.search(
        r"yukleniyorDurumu\s*\|\|\s*\(\s*yol\s*!==\s*null\s*&&\s*guncel\s*===\s*null\s*&&\s*"
        r"hata\s*===\s*null\s*&&\s*!oturumDustu\s*\)",
        s,
    ), "yukleniyor tek karede türetilmiyor — yol değişince bir kare 'boş+yüklenmiyor' görünebilir"


# ============================================================================
# (3) ARAYÜZ SABİT — `Durum<T>` altı alan, ne fazla ne eksik
# ============================================================================

def test_durum_arayuzu_ALTI_ALAN_ne_fazla_ne_eksik():
    t = soy(VERI)
    bas = t.find("export interface Durum<T>")
    assert bas != -1, "Durum<T> arayüzü yok"
    govde = t[bas : t.index("\n}", bas)]
    alanlar = re.findall(r"readonly\s+(\w+)\s*[:?]", govde)
    assert alanlar == ["veri", "yukleniyor", "hata", "oturumDustu", "zaman", "tazele"], (
        f"Durum<T> alan kümesi değişti (arayüz SABİT kalmalıydı, hiçbir tüketici dokunulmadı): {alanlar}"
    )


# ============================================================================
# (4) `Kapi` KOPYALARI — KENDİ ÇARESİNİ KURMAMIŞ (sözleşme TEK kaynakta)
# ============================================================================

_KOPYA_CARE_IMZASI = re.compile(r"\byol\s*===|\bsonYol\b|\boncekiYol\b")


def test_kapi_kopya_sayisi_TAM_BIR_olculuyor():
    """KÖRLÜK ALARMI: tarama boş/az dönerse aşağıdaki 'hiçbiri çare kurmamış' testi anlamsızca
    geçer. Sayı ayrıca ölçülür (inceleme Önemli-1, düzeltme turu 1, 2026-09-03: elle yazılmış
    liste 5 iken gerçek sayı 7'ydi — `kimlik/parcalar.tsx` ve `yetki/parcalar.tsx` kaçmıştı).

    SAYI 7'DEN 1'E İNDİ (TSK-113, 2026-09-03) ve eşik "≥7"den "==1"e çevrildi. Neden ≥ değil ==:
    burada ölçülen şey artık "tarama çalışıyor mu" DEĞİL, "tek kaynak korunuyor mu"dur — sekizinci
    bir kopya doğduğunda `>=` sessiz kalırdı. Alt sınır (boş dönmüyor) `== 1` içinde zaten var.
    `function Kapi<` yerine `export const Kapi = kapiKur(...)` bağları KOPYA DEĞİLDİR: karar
    taşımazlar, yalnız kabuk bağlarlar (çivisi `tests/test_kovab_b12_v384.py`)."""
    kopyalar = _kapi_kopyalarini_bul()
    assert [p.relative_to(KOK).as_posix() for p in kopyalar] == ["ui/src/pano/parcalar/kapi.tsx"], (
        f"`Kapi<T>` tanımı tek kaynakta değil (tarama kırık ya da kopya doğmuş): "
        f"{[p.relative_to(KOK).as_posix() for p in kopyalar]}"
    )


def test_kapi_kopyalari_KENDI_bayatlik_caresini_kurmamis():
    """KAPSAM `_kapi_yuzeyleri()` (Ö-4, düzeltme turu 1, 2026-09-03): tek kaynak + TSK-113
    öncesi yedi yüzey. Yalnız dinamik taramaya bağlansaydı kapsam 7 dosyadan 1'e SESSİZCE
    daralırdı — bedel yasası, kapsam daraltan değişikliğin ne KAYBETTİĞİNİ de ölçmesini ister."""
    kirli = []
    for p in _kapi_yuzeyleri():
        if _KOPYA_CARE_IMZASI.search(soy(p)):
            kirli.append(p.relative_to(KOK).as_posix())
    assert kirli == [], (
        f"Kapi yüzeyleri kendi bayatlık çaresini kurmuş — sözleşme veri.ts dışına sızdı: {kirli}"
    )


def test_KOPYA_TARAYICISI_sessizce_bos_DEGIL():
    """POZİTİF KONTROL (v314 disiplini): sentetik bir "kopya çare" verilir ve tarayıcının
    onu YAKALAMASI beklenir — yoksa "kopya yok" cümlesi taramanın boş dönmesiyle aynı görünürdü."""
    assert _KOPYA_CARE_IMZASI.search("if (sonYol !== yol) { ... }")
    assert _KOPYA_CARE_IMZASI.search("const oncekiYol = useRef(yol);")
    assert _KOPYA_CARE_IMZASI.search("if (yol === kayitYol) return children(veri);")
    assert not _KOPYA_CARE_IMZASI.search("if (acik) return children(veri);")


# ============================================================================
# (5) KENDİ KÖRLÜĞÜ — ölçülen dizgeler dosyada en az bir kez geçiyor
# ============================================================================

def test_olculen_dizgeler_VERI_TS_te_GECIYOR():
    """Tarayıcının kendi körlüğü: yol bayatlarsa ya da regex kırılırsa yukarıdaki testler
    yanlış pozitif "temiz" verebilir. Burada ham `in` ile ayrıca doğrulanır."""
    s = soy(VERI)
    for iz in (
        "okuma.yol === yol",
        "hataKaydi.yol === yol",
        "setHataKaydi(null)",
        "yukleniyorDurumu || (yol !== null && guncel === null && hata === null && !oturumDustu)",
    ):
        assert iz in s, f"ölçülen dizge veri.ts'te yok: {iz!r}"
    assert "setOkuma(null)" not in s

"""/api/infra SATIR ALANLARININ PANO OKUYUCUSU — YASA 6 çivisi (v316, 2026-08-25)

NE ÖLÇÜLÜYOR. `/api/infra` bir bileşen satırında `beklenen`, `beklenen_neden` ve
`servis_turu_neden` yayınlıyordu; panoda HİÇBİRİNİN okuyucusu yoktu (`Bilesenler.tsx`
bu üç alana hiç dokunmuyordu, `uctipleri.ts` ise yalnız TİP beyanıdır — beyan okuyucu
DEĞİLDİR). YASA 6: okuyucusuz alan yazılmaz. Üç alan da artık ekranda iş görüyor:

  1. BEKLENEN ile ÖLÇÜLEN AYRI GÖSTERİLİR. "Kurulu olmalı mıydı" sorusunun kaynağı
     DİSKTİR (`deploy/<host>/`, otorite `dagit.sh`); "kurulu mu" sorusununki systemd
     (`LoadState`). İkisini tek hücrede toplamak, operatörün 2026-08-25'te sorduğu
     "neden kurulu değil, inaktif ve ölçülemedi gözüküyor" sorusunun ta kendisiydi.
  2. KANITSIZ SAĞLIK İDDİASI YOK. Rozetin yeşil/sessiz tonu bir İDDİADIR ve iddia
     ancak KANITI ölçüldüyse kurulur: `sirada_timer` / `ariza_yok_onfailure` tonu
     `Type=oneshot` ÖLÇÜLMÜŞ olmasına, `envanter_gurultusu`nun sessizliği ise
     `beklenen === false` ölçümüne dayanır. Kanıt yoksa ton `dikkat`e düşer —
     gürültüyü susturayım derken sinyali susturmak kusuru ikiye katlardı.
  3. BOŞ BAĞ LİSTESİ BİR CEVAP DEĞİLDİR. `tetikleyen_timerlar`/`onfailure_kaynaklari`
     satır sözlüğünde `[]` ile başlatılır ve şablon / bütçe aşımı / `systemctl` hatası
     dallarında `[]` olarak GÖVDEYE GİDER (o dallarda `_neden` eşleri yoktur). Ucun
     kendi şerhi de bunu söylüyor (`api.py::_systemd_liste`: boş liste "bağ yok"
     DEĞİL "bu çıktıda bağ görünmedi" demektir). Pano boş listeyi bir olumsuzluk
     KANITI gibi çizemez.

NEDEN ÖLÇÜM DAVRANIŞ ÜZERİNDE, "dize dosyada geçiyor mu" ÜZERİNDE DEĞİL. Alt-dize
tuzağı bu turda üç kez yakalandı: bir alan adının yorumda geçmesi okunduğunu KANITLAMAZ.
Bu yüzden karar veren üç saf işlev TSX kaynağından SÖKÜLÜP esbuild ile çevriliyor ve
node'da GERÇEKTEN KOŞTURULUYOR — dönen hüküm ölçülüyor. Kaynak-biçimi çivileri yalnız
o işlevlerin EKRANA BAĞLI olduğunu (öksüz kalmadığını) sınamak için var; onlarda da
yorumlar önce soyuluyor.

SÖK/ÇEVİR/KOŞTUR HATTI ARTIK `tests/conftest.py`TE (2026-09-01). Hat burada doğdu, sonra
v354'e KOPYALANDI ve kopya "ithal ediliyor" diye beyan edildi — beyanla gerçeğin ayrıştığı
nokta. Tek-kaynak yasası gereği ayrıştırıcı tek yere taşındı; bu dosya davranışını
DEĞİŞTİRMEDEN oradan alıyor.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from tests.conftest import (
    ESBUILD_YOLU as ESBUILD,          # araç yolu da tek kaynaktan: ikinci bir sabit ayrışırdı
    tsx_islev_cagir,
    tsx_islev_govdesi,
    tsx_saf_islevleri_cevir,
    tsx_yorumlari_soy,
)

KOK = Path(__file__).resolve().parent.parent
SISTEM = KOK / "ui" / "src" / "pano" / "yuzeyler" / "sistem"
BILESENLER = SISTEM / "Bilesenler.tsx"
UCTIPLERI = SISTEM / "uctipleri.ts"

pytestmark = pytest.mark.skipif(not BILESENLER.exists(), reason="ui/ yok — pano kaynağı bu ağaçta değil")

# Davranış ölçümü node+esbuild ister; ikisi de yoksa ölçüm YAPILAMAZ (uydurulmaz, atlanır).
_ARAC_YOK = shutil.which("node") is None or not ESBUILD.exists()
arac_gerek = pytest.mark.skipif(_ARAC_YOK, reason="node/esbuild yok — TSX davranışı bu ağaçta koşturulamaz")

OKUYUCULAR = ("beklentiOku", "kuruluOku", "kanitKapisi", "baglarOku")


def _kaynak() -> str:
    return tsx_yorumlari_soy(BILESENLER.read_text(encoding="utf-8"))


def _govde(metin: str, imza: str) -> str:
    return tsx_islev_govdesi(metin, imza)


_CEVRILMIS: str | None = None


def _cevir() -> str:
    """Dört saf okuyucuyu TSX'ten söküp esbuild ile JS'e çevirir (bir kez)."""
    global _CEVRILMIS
    if _CEVRILMIS is None:
        _CEVRILMIS = tsx_saf_islevleri_cevir(_kaynak(), OKUYUCULAR)
    return _CEVRILMIS


def _cagir(ad: str, *argumanlar) -> object:
    """Sökülen okuyucuyu node'da GERÇEKTEN çağırır ve dönen hükmü verir."""
    return tsx_islev_cagir(_cevir(), ad, *argumanlar)


# --- POZİTİF KONTROL: ölçüm hattının kendisi çalışıyor mu ------------------

@arac_gerek
def test_olcum_hatti_GERCEKTEN_KOSUYOR():
    """Sıfır bulgunun anlamı olması için hattın çalıştığı kanıtlanmalı (test_codelaw_v59
    disiplini): sökme + esbuild + node zincirinin bir yerinde sessizce boş dönseydi
    aşağıdaki davranış çivilerinin hepsi anlamsız yeşil olurdu."""
    assert "function beklentiOku" in _cevir() and "function kanitKapisi" in _cevir()
    assert _cagir("beklentiOku", {"beklenen": True, "beklenen_neden": "X"})["hal"] == "kurulmali"


# --- 1) BEKLENEN vs ÖLÇÜLEN ------------------------------------------------

@arac_gerek
def test_beklenen_UC_DEGERLIDIR_ve_ucu_de_AYRIDIR():
    assert _cagir("beklentiOku", {"beklenen": True, "beklenen_neden": "a"})["hal"] == "kurulmali"
    assert _cagir("beklentiOku", {"beklenen": False, "beklenen_neden": "b"})["hal"] == "beklenmiyor"
    # Alan HİÇ gelmediyse hüküm KURULMAZ — `false` varsaymak "kurulması beklenmiyor"
    # diye okunur ve gerçek bir eksiği envanter gürültüsü sayardı.
    assert _cagir("beklentiOku", {})["hal"] == "olculemedi"
    assert _cagir("beklentiOku", {"beklenen": None})["hal"] == "olculemedi"


@arac_gerek
def test_beklenen_neden_UCTAN_AYNEN_TASINIR():
    """`beklenen_neden` ucun GEREKÇESİDİR (hem `true` hem `false` dalında dolu gelir);
    pano onu yeniden yazmaz, taşır — yoksa ekrandaki hükmün dayanağı kaybolur."""
    gerekce = "`deploy/<host>/` altında birim dosyası var ve `dagit.sh` bu dizini canlıyla kıyaslıyor"
    assert _cagir("beklentiOku", {"beklenen": True, "beklenen_neden": gerekce})["neden"] == gerekce
    # Gerekçe gelmediyse UYDURULMAZ ama BOŞ da bırakılmaz: neden yazılmadığı söylenir.
    bos = _cagir("beklentiOku", {"beklenen": True})
    assert bos["neden"] and gerekce not in bos["neden"]


@arac_gerek
def test_kurulu_OLCULEN_TARAFTIR_ve_ucuncu_hali_vardir():
    assert _cagir("kuruluOku", {"kurulu": True})["hal"] == "kurulu"
    assert _cagir("kuruluOku", {"kurulu": False, "kurulu_neden": "LoadState=not-found"})["hal"] == "kurulu_degil"
    assert _cagir("kuruluOku", {"kurulu": None, "kurulu_neden": "ŞABLON"})["hal"] == "olculemedi"
    assert _cagir("kuruluOku", {})["hal"] == "olculemedi"


# --- 2) KANITSIZ SAĞLIK İDDİASI YOK ---------------------------------------

@arac_gerek
def test_ONESHOT_OLCULMEDEN_YESIL_IDDIA_KURULMAZ():
    """`sirada_timer` / `ariza_yok_onfailure` tonu `Type=oneshot` ölçümüne dayanır.
    `servis_turu` gelmediyse (şablon / bütçe aşımı / `systemctl` hatası — üçünde de
    `servis_turu_neden` doludur) 'sağlıklı bekleyiş' bir ÖLÇÜM değil VARSAYIMdır."""
    neden = "`Type` alanı çıktıda yok/boş"
    for sinif in ("sirada_timer", "ariza_yok_onfailure"):
        k = _cagir("kanitKapisi", {"servis_turu": None, "servis_turu_neden": neden}, sinif, "iyi")
        assert k["ton"] != "iyi", f"{sinif}: kanıtsız yeşil iddia kuruldu"
        assert k["eksik"] and neden in k["eksik"], f"{sinif}: eksik kanıt gerekçesi taşınmıyor"


@arac_gerek
def test_KANIT_TAMSA_TON_DUSURULMEZ():
    """Ters yön (gürültü çivisi): kanıt ölçüldüyse kapı hiçbir şeyi değiştirmez —
    yoksa kapı, sustur(a)madığı her satırı amber'e boyayıp tabloyu okunamaz yapardı."""
    k = _cagir("kanitKapisi", {"servis_turu": "oneshot"}, "sirada_timer", "iyi")
    assert k == {"ton": "iyi", "eksik": None}
    g = _cagir("kanitKapisi", {"beklenen": False, "beklenen_neden": "kökte duran eski kopya"},
               "envanter_gurultusu", "notr")
    assert g == {"ton": "notr", "eksik": None}


@arac_gerek
def test_envanter_SESSIZLIGI_beklenen_FALSE_OLMADAN_KURULMAZ():
    """`envanter_gurultusu`nun `notr` tonu "eksik DEĞİL" der; bu iddia TAMAMEN
    `beklenen === false` ölçümüne dayanır. Ölçüm yoksa satır susturulamaz."""
    k = _cagir("kanitKapisi", {}, "envanter_gurultusu", "notr")
    assert k["ton"] == "dikkat" and k["eksik"]


@arac_gerek
def test_kosuyor_HAM_DURUMLA_KIYASLANIR():
    """`kosuyor` yeşili `ActiveState=active` ölçümüne dayanır; uç sınıfı bildirip ham
    durumu bildirmediyse (ya da ikisi ayrıştıysa) yeşil iddia edilemez."""
    assert _cagir("kanitKapisi", {"durum": "active"}, "kosuyor", "iyi") == {"ton": "iyi", "eksik": None}
    kirik = _cagir("kanitKapisi", {"durum": "inactive"}, "kosuyor", "iyi")
    assert kirik["ton"] != "iyi" and kirik["eksik"]


# --- 3) BOŞ BAĞ LİSTESİ BİR CEVAP DEĞİLDİR --------------------------------

@arac_gerek
def test_BOS_BAG_LISTESI_BAG_YOK_DIYE_OKUNMAZ():
    """Şablon / bütçe aşımı / `systemctl` hatası satırlarında iki liste de `[]` gider
    ve `_neden` eşleri YOKTUR. `[]`i "bağ görülmedi" diye çizmek, hiç sorulmamış bir
    soruya olumsuz cevap uydurmaktır."""
    b = _cagir("baglarOku", {"tetikleyen_timerlar": [], "onfailure_kaynaklari": [],
                             "servis_turu": None, "servis_turu_neden": "ŞABLON birim (`@`)"})
    assert b["olculdu"] is False
    assert b["neden"] and "ŞABLON" in b["neden"]
    # Alanlar HİÇ gelmediğinde de aynı hüküm.
    assert _cagir("baglarOku", {})["olculdu"] is False


@arac_gerek
def test_DOLU_BAG_LISTESI_OLCULMUS_SAYILIR():
    b = _cagir("baglarOku", {"tetikleyen_timerlar": ["meridian-backup.timer"],
                             "onfailure_kaynaklari": []})
    assert b["olculdu"] is True and b["neden"] is None
    assert b["timerlar"] == ["meridian-backup.timer"]
    o = _cagir("baglarOku", {"tetikleyen_timerlar": [],
                             "onfailure_kaynaklari": ["meridian-worker.service"]})
    assert o["olculdu"] is True and o["onfailure"] == ["meridian-worker.service"]


# --- 4) OKUYUCULAR ÖKSÜZ DEĞİL: ekrana bağlılar ---------------------------

def test_kapi_ROZETIN_TONUNU_GERCEKTEN_BELIRLIYOR():
    """Kapı öksüz kalırsa (hesaplanır ama kullanılmazsa) yukarıdaki davranış çivileri
    yeşil kalır ve ekran yine kanıtsız yeşil basar. Rozet tonu KAPIDAN okunmalı."""
    g = _govde(_kaynak(), "function durumRozeti(")
    assert re.search(r"\bkanitKapisi\s*\(\s*b\s*,", g), "durumRozeti kapıyı çağırmıyor"
    assert re.search(r"TON_METNI\[\s*kapi\.ton\s*\]", g), "rozet rengi kapıdan gelmiyor"
    assert re.search(r"TON_NOKTASI\[\s*kapi\.ton\s*\]", g), "rozet noktası kapıdan gelmiyor"
    assert not re.search(r"TON_(METNI|NOKTASI)\[\s*k\.ton\s*\]", g), (
        "ton hâlâ ham sınıftan okunuyor — kapı devre dışı")
    assert re.search(r"kapi\.eksik", g), "eksik kanıt rozette hiç görünmüyor"


def test_BEKLENEN_ve_OLCULEN_TABLODA_AYRI_HUCREDE():
    """Üç okuyucunun da bir JSX tüketicisi olmalı; yoksa YASA 6 boşluğu kapanmaz."""
    ham = _kaynak()
    hucre = _govde(ham, "function BeklentiHucresi(")
    for ad in ("beklentiOku", "kuruluOku", "baglarOku"):
        assert re.search(rf"\b{ad}\s*\(\s*b\s*\)", hucre), f"`{ad}` hücrede çağrılmıyor"
    assert re.search(r"<BeklentiHucresi\b[^>]*\bb=\{b\}", ham), "hücre tabloya bağlanmamış"
    # Sütun başlığı da olmalı: başlıksız hücre tabloyu kaydırır.
    assert re.search(r"<TableHead[^>]*>\s*Beklenti", ham), "sütun başlığı yok"


# Hangi alan HANGİ İŞLEVDE okunmalı. "Dosyada bir yerde geçiyor" YETMEZ: alan üç ayrı yerde
# okunuyor ve birini sökmek ötekilerin gölgesinde sessizce geçerdi (mutasyonla ölçüldü — dosya
# geneline bakan ilk sürüm `servis_turu_neden`in rozetten sökülmesini KAÇIRDI).
OKUYUCU_HARITASI = (
    ("beklentiOku", ("beklenen", "beklenen_neden")),
    ("kanitKapisi", ("beklenen", "servis_turu_neden")),
    ("baglarOku", ("tetikleyen_timerlar", "onfailure_kaynaklari", "servis_turu_neden")),
    ("durumRozeti", ("servis_turu_neden",)),
)


def test_UC_ALANIN_UI_OKUYUCUSU_VAR():
    """YASA 6'nın kendisi: `/api/infra` bu alanları yayınlıyorsa panoda OKUNUYOR olmalı.
    Ölçüm ÖZELLİK ERİŞİMİNİ, üstelik BELİRLİ BİR İŞLEVİN GÖVDESİNDE arar — alan adının bir
    yorumda geçmesi okuyucu değildir (yorumlar soyuldu) ve tip beyanı da okuyucu değildir
    (`uctipleri.ts` ölçüme hiç girmiyor)."""
    ham = _kaynak()
    for islev, alanlar in OKUYUCU_HARITASI:
        g = _govde(ham, f"function {islev}(")
        for alan in alanlar:
            assert re.search(rf"\bb\.{alan}\b", g), f"`{alan}` `{islev}` içinde okunmuyor (YASA 6)"


def test_SATIR_CAPASI_YOK_bu_iki_dosyada():
    """Çapa yasası: `dosya.py:NNN` ilk düzenlemede bayatlar. Bu iki dosyadaki çapalar
    sembole çevrildi; yenisi eklenemez."""
    for p in (BILESENLER, UCTIPLERI):
        bulunan = re.findall(r"[A-Za-z_][A-Za-z0-9_]*\.(?:py|ts|tsx|sh):\d+", p.read_text(encoding="utf-8"))
        assert bulunan == [], f"{p.name}: satır çapası kaldı → {bulunan}"


# ---------------------------------------------------------------------------
# ÇAPA YASASI — bu kalemin İKİNCİ yarısı (`meridian/watchdog.py`)
# ---------------------------------------------------------------------------
# NEDEN BURADA. Depo geneli çivi `test_codelaw_kor_nokta_v214::test_satir_capalari_CURUK_DEGIL`
# ZATEN var ve otoritedir; ama o AĞACIN TAMAMINI ölçer, yani başka dosyalardaki bir çürük çapa
# yüzünden kırmızıyken bu kalemin düzeltmesi geri alınsa hüküm DEĞİŞMEZ — mutasyon kanıtı
# körelir. Aşağıdaki çivi aynı ölçüyü `watchdog.py` KAPSAMINA daraltır: bu dosyaya bir satır
# çapası geri gelirse test tek başına öter.

def test_watchdog_CAPALARI_SEMBOLE_CEVRILDI():
    """`watchdog.py`de `dosya.py:NNN` biçiminde satır çapası kalmadı.

    ÖLÇÜLEN BAYATLIK (2026-08-25): `gap_h` okuyucularını gösteren iki çapa ile plan üretecini
    gösteren çapa BOŞ SATIRA düşmüştü; `broker` de-risk tabanını gösteren çapa ise ilgisiz bir
    sabiti işaret ediyordu. Bu testin metni onları SAYIYLA alıntılamaz — bayat bir numarayı
    "ders" diye yazmak, kovalanan sınıfın yeni bir örneğini üretmek olurdu. Doğru tepki numarayı
    GÜNCELLEMEK değil SEMBOLE çevirmektir: numara ilk düzenlemede yine bayatlar."""
    kaynak = (KOK / "meridian" / "watchdog.py").read_text(encoding="utf-8")
    bulunan = re.findall(r"[A-Za-z_][A-Za-z0-9_]*\.(?:py|ts|tsx|sh|yaml):\d+", kaynak)
    assert bulunan == [], f"watchdog.py: satır çapası kaldı → {bulunan}"
    # Sembol çapaları GERÇEKTEN VAR OLMALI: `api.py::yok_boyle_bir_sey` yazmak, bayat satır
    # numarasından daha iyi değildir (ikisi de okuyucuyu boşluğa gönderir).
    for dosya, sembol in (("api.py", "_sessiz_hat"), ("selfreview.py", "build"),
                          ("loop.py", "daily_cycle"), ("cf_backfill.py", "_plans_for_session")):
        assert f"{dosya}::{sembol}" in kaynak, f"`{dosya}::{sembol}` çapası kaybolmuş"
        hedef = (KOK / "meridian" / dosya).read_text(encoding="utf-8")
        assert re.search(rf"^def {re.escape(sembol)}\(", hedef, flags=re.M), (
            f"`{dosya}` içinde `{sembol}` diye bir işlev YOK — çapa boşluğa işaret ediyor")

"""v343 · YOL HARİTASI YÜZEYİ TABLO SATIRLARINI OKUR — üretilen alanın okuyucusu olmalı.

KİMLİK KAYDI (numara KİMLİKTİR — CLAUDE.md): bu dosya **v338 olarak doğdu** ve `main`de aynı numarayı
taşıyan `tests/test_karne_brifingi_v338.py` ile çakıştı (birleşme 2026-08-31). Kural gereği AZ ÇAPALI
taraf taşınır: bu dosyanın tek atfı kendi başlığıydı, karşı tarafınki @karne teslimatına bağlıydı →
bu dosya v341'e taşındı. v338 kimliği karne çivisinindir ve yeniden kullanılmaz.
İKİNCİ TAŞIMA (2026-08-31, aynı gün): v341 de çakıştı — paralel oturumun PIT-yasası çivisi
`tests/test_pit_yasasi_v341.py` aynı numarayla indi ve 5 dış atıf taşıyor (CLAUDE.md §4 +
devir dokümanı); bu dosyanın dış atfı yine yalnız kendi başlığı → az-çapalı taraf olarak
v343'e taşındı (v342 `test_pit_sinif_turetimi_v342.py`de dolu). v341 kimliği PIT çivisinindir.

ÖLÇÜLEN ARIZA (2026-08-31): `/api/roadmap` ucu belgeyi İKİ BİRİMde ayrıştırıyor — düzyazı
`maddeler` ve markdown `tablolar[].satirlar[]` — ve ikisini de gövdede gönderiyor. Pano yüzeyi
(`ui/src/pano/yuzeyler/kanban/roadmap.ts`) açıldığı günden beri YALNIZ birincisini okuyordu.

Bedeli tek cümlede: **`§2 TAHTA` tamamen tablodur** ve panonun "Bölüm başına madde" grafiğinde
**0** olarak çiziliyordu — yani belgenin AKTİF KALEM tahtası, operatörün baktığı yüzeyde BOŞ bir
satırdı; grafiği `§7 KARAR GÜNLÜĞÜ`nün yüzlerce düzyazı maddesi dolduruyordu. Ölçüm (2026-08-31,
aynı ayrıştırıcı): 450 madde ÇİZİLİYOR, 188 tablo satırı ÇİZİLMİYOR.

Bu ucun kusuru DEĞİLDİ: gövde alanları zaten taşıyordu, okuyucusu yoktu — **YASA 6'nın kuzeni**
(üretilen her alanın dış tüketicisi olmalı). Bu dosya o sınıfı yüzey tarafında kapatır.

BU DOSYA NEYİ ÇİVİLER
---------------------
A. **OKUYUCU VAR.** `roadmap.ts` `tablolar` / `satirlar` dallarını ve `sayim.tablo_*` sayaçlarını
   gerçekten okur; `YolHaritasi.tsx` tablo satırlarını çizer.
B. **ÜRETİLEN HER TABLO ALANININ OKUYUCUSU VAR — ve liste ELLE YAZILMADI.** Beklenen alan kümesi
   gerçek `ROADMAP.md` ayrıştırılarak ÜRETİLİR (tek-kaynak: uç büyürse çivi kendiliğinden büyür).
   Okunmayan alan ihlaldir; meşru istisna **BEYANLA** olur — `OKUNMAYAN_ALANLAR`, gerekçesiyle.
C. **İKİ SAYIM TOPLANMAZ.** Ucun kendi şerhi "iki sayımı toplamak kalemleri çift saymak olurdu"
   der. Yüzey iki birimi ayrı sayar ve ayrı çizer; bunu ekranda da söyler.
D. **ÖNCÜL 2026-09-01'DE ÇÜRÜDÜ, KAYIT GÜNCELLENDİ.** Yazıldığı gün `§2 TAHTA`nın düzyazı
   maddesi YOK, yalnız tablo satırı VARdı. TSK/PRG madde-şeması göçünde (FAZ B,
   `docs/TASARIM-ROADMAP-STANDART-2026-09-01.md`) İCRA SIRASI paragrafı §2'nin altına sıralı
   TSK madde listesi olarak taşındı — artık §2 HEM düzyazı madde HEM tablo satırı taşıyor.
   Asıl çivi (tablo dalı okunmazsa tahtanın yarısı panoda BOŞ görünür) hâlâ geçerli: satır
   sayısı > 0 şartı kalıyor; madde sayısı > 0 şartı yeni öncülü ölçer (0'a dönerse göç geri
   alınmış olabilir — bu da sessizce geçmemeli).
"""
import pathlib

import pytest

from meridian import api, config

KOK = pathlib.Path(config.ROOT)
OKUYUCU = KOK / "ui/src/pano/yuzeyler/kanban/roadmap.ts"
YUZEY = KOK / "ui/src/pano/yuzeyler/kanban/YolHaritasi.tsx"

# BEYAN EDİLMİŞ OKUNMAYANLAR — her biri gerekçesiyle. Boş bırakmak YASAK sayılmaz; gerekçesiz
# bırakmak sayılır (testin kendisi gerekçenin uzunluğunu ölçüyor).
OKUNMAYAN_ALANLAR: dict[str, str] = {
    "hucre_uzunluk": (
        "hücre başına karakter uzunluğu listesi. Kartın ihtiyacı olan tek bilgi 'kırpıldı mı' ve "
        "onu `hucre_kirpildi` zaten taşıyor; uzunluk listesini basmak kartı sayı çöplüğüne çevirirdi."
    ),
    "durum_kanitlari": (
        "hücre başına (sütun, durum, eşleşen kelime) üçlüsü. Satır rozetinin gerekçesi kartta "
        "`durum_neden` ile veriliyor; sütun sütun kanıt bir kart yüzeyine sığmaz ve kırpılırsa "
        "kanıt olmaktan çıkar. Gerekirse ayrı bir 'satır incele' yüzeyinin işi."
    ),
    "satir_n": "tablonun kendi satır sayısı — pano listeyi zaten sayıyor, ikinci sayaç ayrışırdı.",
    "tablo_n": "belgedeki tablo SAYISI; yüzey satır düzeyinde çalışıyor, tablo düzeyinde değil.",
    "tablo_satir_n_toplam": (
        "bölüm başına uç beyanı. Pano kendi düzleştirmesini BELGE düzeyinde `sayim.tablo_satir_n` "
        "ile karşılaştırıyor (ayrışma uyarısı oradan doğuyor); bölüm başına ikinci bir karşılaştırma "
        "aynı gerçeği iki yerden okurdu."
    ),
}


def _yuk() -> dict:
    metin = (KOK / "ROADMAP.md").read_text(encoding="utf-8")
    return api._roadmap_ayristir(metin, yol="sanal.md", bayt=len(metin.encode()),
                                 mtime=None, tam=True)


def _gez(b: dict):
    yield b
    for a in b["alt_bolumler"]:
        yield from _gez(a)


@pytest.fixture(scope="module")
def kaynaklar() -> str:
    assert OKUYUCU.exists(), f"yüzey okuyucusu yok: {OKUYUCU}"
    assert YUZEY.exists(), f"yüzey bileşeni yok: {YUZEY}"
    return OKUYUCU.read_text(encoding="utf-8") + "\n" + YUZEY.read_text(encoding="utf-8")


def test_a_yuzey_tablo_dallarini_okuyor(kaynaklar: str):
    for anahtar in ('["tablolar"]', '["satirlar"]', '["tablo_durum"]', '["tablo_satir_n"]'):
        assert anahtar in kaynaklar, (
            f"yüzey `{anahtar}` alanını hiç okumuyor — uç onu üretiyor ve okuyucusu yoksa "
            "üretilmemiş sayılır (YASA 6 kuzeni). Bu tam olarak `§2 TAHTA`yı panoda BOŞ gösteren "
            "arızanın kendisidir."
        )
    assert "TabloSatiriKarti" in kaynaklar, "tablo satırları okunuyor ama ÇİZİLMİYOR — okuyucu yüzey değildir"


def test_b_uretilen_her_tablo_alani_ya_okunuyor_ya_beyanli(kaynaklar: str):
    """Beklenen alan kümesi ELLE YAZILMADI: gerçek belgeden ÜRETİLİYOR."""
    yuk = _yuk()
    alanlar: set[str] = set()
    for kok in yuk["bolumler"]:
        for b in _gez(kok):
            for t in b["tablolar"]:
                alanlar |= set(t.keys())
                for r in t["satirlar"]:
                    alanlar |= set(r.keys())
    alanlar |= {k for k in yuk["sayim"] if k.startswith("tablo")}
    alanlar |= {k for kok in yuk["bolumler"] for k in kok if k.startswith("tablo")}
    alanlar -= {"satirlar", "tablolar", "basliklar"}   # kap alanları; A ayağı onları ölçüyor

    assert alanlar, "ayrıştırıcıdan hiç tablo alanı çıkmadı — kapı boşa düşüyor olabilir"
    ihlal = [a for a in sorted(alanlar) if f'["{a}"]' not in kaynaklar and a not in OKUNMAYAN_ALANLAR]
    assert not ihlal, (
        "uç bu tablo alanlarını üretiyor ama yüzey ne OKUYOR ne de okumadığını BEYAN ediyor: "
        f"{ihlal}. Ya `roadmap.ts`te oku, ya `OKUNMAYAN_ALANLAR`a gerekçesiyle yaz."
    )
    bos = [a for a, neden in OKUNMAYAN_ALANLAR.items() if len(neden) < 20]
    assert not bos, f"beyan gerekçesiz: {bos} (≥20 karakter gerekçe şart — YASA 4 deseni)"
    olu = [a for a in OKUNMAYAN_ALANLAR if a not in alanlar]
    assert not olu, f"beyan edilen alan ucun gövdesinde YOK — beyan bayatlamış: {olu}"


def test_c_iki_sayim_toplanmiyor(kaynaklar: str):
    """Madde ile tablo satırı ayrı BİRİMdir; toplamak kalemleri çift saymak olurdu (ucun şerhi)."""
    assert "bizimTabloN" in kaynaklar and "bizimN" in kaynaklar, "iki sayaç ayrı taşınmıyor"
    assert "TOPLANMAZ" in kaynaklar, (
        "iki birimin toplanmadığı ekranda/kaynakta SÖYLENMİYOR — okuyan onları toplayacaktır"
    )


def test_d_onculun_2026_09_01_govdesi():
    """`§2 TAHTA` artık HEM düzyazı TSK maddesi HEM tablo satırı taşıyor (2026-09-01 göçü)."""
    yuk = _yuk()
    tahta = [k for k in yuk["bolumler"] if (k.get("no") or "") == "§2"]
    assert len(tahta) == 1, "belgede `§2` kök bölümü bulunamadı — numaralandırma değişmiş olabilir"
    madde = sum(len(b["maddeler"]) for b in _gez(tahta[0]))
    satir = sum(len(t["satirlar"]) for b in _gez(tahta[0]) for t in b["tablolar"])
    assert satir > 0, "`§2 TAHTA`da hiç tablo satırı yok — tahta tablo olmaktan çıkmışsa bu çivinin gerekçesi de değişmeli"
    assert madde > 0, (
        "`§2 TAHTA` hiç düzyazı madde taşımıyor — 2026-09-01 göçünde buraya taşınan İCRA SIRASI "
        "TSK listesi kaybolmuş ya da başka bölüme geri taşınmış olabilir; kayıt yeniden gözden "
        "geçirilmeli, sessizce geçmemeli."
    )

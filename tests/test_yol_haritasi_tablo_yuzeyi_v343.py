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

FAZ D GENİŞLETMESİ (2026-09-01) — ALAN AYRIŞTIRMASI
---------------------------------------------------
`docs/TASARIM-ROADMAP-STANDART-2026-09-01.md` §5 ucun `maddeler[]`/tablo satırlarını
YAPILANDIRILMIŞ döndürmesini şart koşuyor (`sema.{id,name,status,owner,size,trigger,section}`).
Bu dosya o yeni alanların da OKUYUCUSUNU çiviler (aynı YASA 6 kuzeni: `sema` üretilip
okunmuyorsa üretilmemiş sayılır) ve ÜÇ ölçülmüş sınıfı ayrı ayrı bağlar:

E. **ŞEMA GERÇEK DOSYADA VAR VE SÖZLÜKTE.** `status` donuk sözlükten, `sinif` iki üst gruptan.
F. **MUHASEBE KAPANIYOR.** `sema` + `muaf_tarihce` = toplam madde. Bir kalem sessizce
   düşemez: "şemalı" ile "tarihçe" ikisi de SAYILIR, üçüncü bir sessiz kova yoktur.
G. **v351 İLE AYRIŞMA ÇİVİSİ.** Gramer İKİ yerde yaşıyor (uçta `meridian/api.py`, zorlama
   çivisinde `tests/test_roadmap_standart_v351.py`) — biri üretim kodudur, öteki testtir ve
   üretim kodu testten ithal EDEMEZ. Kopya kaçınılmazdı; CLAUDE.md §4 tek-kaynak yasasının
   izin verdiği yol da bu: **kopya + ayrışma çivisi**. Aşağıdaki test ikisini GERÇEK dosyanın
   her başlık satırında karşılaştırır — sessizce ayrışamazlar.
H. **v337'NİN KIRMIZISI GERİLEME ÇİVİSİ OLDU.** Şema tablosunda düzyazı sütunları rozet alanı
   DEĞİLDİR; `trigger` hücresinde "…boyunca KAPALI" geçen AÇIK bir kalem kapalı sayılamaz.

ÖLÇÜLEN TABAN (2026-09-01, aynı ayrıştırıcı): 95 şemalı madde + 26 şemalı `§2` tablo satırı =
121 kayıt · `muaf_tarihce` 432 (§7/§8 düzyazısı — operatör onaylı muafiyet) · `ihlal_n` 0 ·
status ACTIVE 3 · QUEUED 32 · INTERIM 1 · GATED 18 · OPERATOR 15 · DONE 49 · DROPPED 0 ·
ölçülemedi 3 (`(bkz. …)` ATIF satırları) → üst sınıf AÇIK 69 / KAPALI 49. Bu sayılar aşağıdaki
testlerde PİN DEĞİLDİR (belge büyür); kaydın kendisi tarih taşır, iddialar oran/muhasebe
üzerinden kurulur — pinli sayı her göç turunda kırmızı verir ve hiçbir şey öğretmezdi.
"""
import pathlib
import re

import pytest

from meridian import api, config
from tests.test_roadmap_standart_v351 import (
    CIPLAK_STATUS_SOZLUGU,
    KART_ALAN_SIRASI,
    MADDE_SATIRI_DESENI,
    PARANTEZLI_STATUS_ANAHTARLARI,
    TSK_ALAN_SIRASI,
    _alan_anahtarlari_ve_sozlugu,
)

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


# ==================================================================================================
# FAZ D — ŞEMA ALANLARI (`sema`), spec §5
# ==================================================================================================

# BEYAN EDİLMİŞ OKUNMAYAN ŞEMA ALANLARI — `OKUNMAYAN_ALANLAR` ile aynı sözleşme: boş bırakmak
# serbest, GEREKÇESİZ bırakmak yasak. Bugün boş; bir alan eklenip yüzeye bağlanmazsa buraya
# gerekçesiyle yazılır ya da okunur — üçüncü seçenek yok.
OKUNMAYAN_SEMA_ALANLARI: dict[str, str] = {}


def _sema_kayitlari(yuk: dict) -> list[dict]:
    """Belgedeki TÜM şema sözlükleri (madde + tablo satırı), düzleştirilmiş."""
    out = []
    for kok in yuk["bolumler"]:
        for b in _gez(kok):
            out += [m["sema"] for m in b["maddeler"] if m["sema"] is not None]
            out += [r["sema"] for t in b["tablolar"] for r in t["satirlar"]
                    if r["sema"] is not None]
    return out


def test_e_sema_gercek_dosyada_var_ve_sozlukte():
    """Uç şema alanlarını GERÇEKTEN üretiyor ve donuk sözlüğün DIŞINA çıkmıyor.

    KAPI BOŞA DÜŞEMEZ: önce şema kaydı SAYISI ölçülür — sıfır olsaydı aşağıdaki iddiaların
    hepsi boş kümede sessizce geçerdi (v337/C ayağının aynı dersi)."""
    kayitlar = _sema_kayitlari(_yuk())
    assert len(kayitlar) >= 50, (
        f"belgede yalnız {len(kayitlar)} şema kaydı ayrıştırıldı — 2026-09-01 göçü geri alınmış "
        "ya da başlık grameri kaymış olabilir; bu sayı sessizce düşmemeli")

    sozluk = set(api._ROADMAP_STATUS_DURUM)
    for s in kayitlar:
        if s["status"] is None:
            assert isinstance(s["status_neden"], str) and s["status_neden"].strip(), (
                f"[{s['id']}] `status` ölçülemedi ama NEDENİ yazılmadı — uydurma yasağının "
                "kardeşi: sessiz None, ölçülmemiş bir hükmü ölçülmüş gibi gösterir")
            assert s["sinif"] is None, f"[{s['id']}] status yokken üst sınıf UYDURULDU: {s['sinif']}"
        else:
            assert s["status"] in sozluk, f"[{s['id']}] status sözlük dışı: {s['status']!r}"
            assert s["sinif"] in ("AÇIK", "KAPALI"), f"[{s['id']}] üst sınıf tanınmadı: {s['sinif']}"
        assert s["kaynak"] in ("madde", "tablo")
        assert s["id"], "şema kaydı kimliksiz — kimlik başlık gramerinin ZORUNLU parçası"


def test_f_muaf_tarihce_olculuyor_ve_muhasebe_kapaniyor():
    """`muaf_tarihce` §7/§8 GERÇEĞİdir (>0) ve muhasebe kapanır: şemalı + muaf = tüm madde.

    Üçüncü bir sessiz kova olsaydı ("ne şemalı ne muaf") kalemler sayaçlar arasında
    kaybolurdu — bu depoda sessiz düşürme YASA 4 ihlalidir."""
    yuk = _yuk()
    sema = yuk["sayim"]["sema"]
    assert sema["muaf_tarihce"] > 0, (
        "`muaf_tarihce` sıfır — §7 KARAR GÜNLÜĞÜ ve §8 ARŞİV düzyazı maddeleri hâlâ orada "
        "(operatör onaylı muafiyet, spec §3); sıfır ölçmek ayrıştırıcının onları şemalı "
        "sandığı ya da hiç görmediği anlamına gelir")
    assert sema["madde_n"] + sema["muaf_tarihce"] == yuk["sayim"]["madde_n"], (
        f"muhasebe kapanmıyor: şemalı {sema['madde_n']} + muaf {sema['muaf_tarihce']} != "
        f"toplam {yuk['sayim']['madde_n']}")
    assert sema["ihlal_n"] == 0, (
        "şema BİÇİMİNDE olup alanları tutmayan madde var — bu tarihçe DEĞİL, bozulmadır; "
        "bölüm gövdesindeki `sema_ihlal` listesine bakılmalı")
    assert sum(sema["status"].values()) + sema["sinif"]["olculemedi"] == \
        sema["madde_n"] + sema["tablo_satir_n"], "status sayacı kayıt sayısıyla tutmuyor"


def test_f2_madde_kimlikleri_tekil_tablo_satirlari_ATIF_tasiyabilir():
    """Bullet maddelerinde kimlik TEKİLDİR (v351/r09 kuralının uç tarafındaki karşılığı).

    TABLO satırlarında AYNI kimlik birden çok kez görünebilir ve bu bir ihlal DEĞİLDİR —
    ölçüldü (2026-09-01): `TSK-069` hem `H1` hem `H0` tablosunda var, ikincisi `(bkz. …)`
    ATIF kaydıdır. İkisini aynı kurala sokmak, belgenin bilinçli desenini ihlal sayardı."""
    kayitlar = _sema_kayitlari(_yuk())
    adlar: dict[str, set[str]] = {}
    for s in kayitlar:
        if s["kaynak"] == "madde":
            adlar.setdefault(s["id"], set()).add(s["name"] or "")
    cakisan = {k: sorted(v) for k, v in adlar.items() if len(v) > 1}
    assert not cakisan, f"aynı kimlik farklı adlara bağlı (bullet maddeleri): {cakisan}"

    atif = [s for s in kayitlar if s["kaynak"] == "tablo" and s["status"] is None]
    assert atif, ("§2 tablosunda hiç ATIF satırı bulunamadı — desen kaybolduysa bu testin "
                  "gerekçesi de değişmeli; sessizce geçmemeli")


def test_g_section_alani_bolumun_KENDISINDEN_geliyor():
    """`section` uydurulmaz: maddenin bulunduğu KÖK bölümün numarasıdır."""
    yuk = _yuk()
    bulunan = set()
    for kok in yuk["bolumler"]:
        no = kok.get("no")
        for b in _gez(kok):
            for s in ([m["sema"] for m in b["maddeler"]] +
                      [r["sema"] for t in b["tablolar"] for r in t["satirlar"]]):
                if s is not None:
                    assert s["section"] == no, (
                        f"[{s['id']}] `section`={s['section']!r} ama kalem {no!r} altında bulundu")
                    bulunan.add(no)
    assert bulunan == {"§2", "§4", "§5", "§6"}, (
        f"şema taşıyan bölümler ölçümle uyuşmuyor: {sorted(x or '?' for x in bulunan)} "
        "— 2026-09-01 göçü §2/§4/§5/§6'yı çevirmişti (spec §3 kapsamı)")


def test_h_sema_alanlarinin_hepsinin_OKUYUCUSU_var(kaynaklar: str):
    """YASA 6 KUZENİ, şema tarafı — beklenen alan kümesi ELLE YAZILMADI, gerçek belgeden ÜRETİLDİ.

    `sema` üretilip yüzeyde okunmuyorsa `§2 TAHTA`nın panoda boş görünmesiyle AYNI arıza
    sınıfıdır; tek fark, bu kez alanların kendisi kaybolurdu."""
    yuk = _yuk()
    alanlar = {k for s in _sema_kayitlari(yuk) for k in s}
    alanlar |= set(yuk["sayim"]["sema"])
    assert alanlar, "hiç şema alanı çıkmadı — kapı boşa düşüyor olabilir"
    ihlal = [a for a in sorted(alanlar)
             if f'["{a}"]' not in kaynaklar and a not in OKUNMAYAN_SEMA_ALANLARI]
    assert not ihlal, (
        "uç bu ŞEMA alanlarını üretiyor ama yüzey ne OKUYOR ne de okumadığını BEYAN ediyor: "
        f"{ihlal}. Ya `roadmap.ts`te oku, ya `OKUNMAYAN_SEMA_ALANLARI`na gerekçesiyle yaz.")
    bos = [a for a, neden in OKUNMAYAN_SEMA_ALANLARI.items() if len(neden) < 20]
    assert not bos, f"beyan gerekçesiz: {bos} (≥20 karakter gerekçe şart — YASA 4 deseni)"
    olu = [a for a in OKUNMAYAN_SEMA_ALANLARI if a not in alanlar]
    assert not olu, f"beyan edilen alan ucun gövdesinde YOK — beyan bayatlamış: {olu}"


def test_i_ucun_grameri_v351_civisiyle_AYRISMIYOR():
    """AYRIŞMA ÇİVİSİ (CLAUDE.md §4 tek-kaynak): aynı gramer iki yerde yaşıyor.

    Üretim kodu (`meridian/api.py`) bir TEST modülünden ithal EDEMEZ, o yüzden kopya
    kaçınılmaz — yasanın izin verdiği yol kopyayı ayrışma çivisiyle bağlamaktır. Üç eksende
    karşılaştırılır: (1) alan sırası demetleri, (2) status sözlüğü, (3) GERÇEK dosyanın HER
    başlık satırında alan bölme sonucu (parantez derinliği tuzağı buradadır)."""
    assert api._ROADMAP_SEMA_ALANLARI == TSK_ALAN_SIRASI
    assert api._ROADMAP_KART_ALANLARI == KART_ALAN_SIRASI
    assert set(api._ROADMAP_STATUS_DURUM) == CIPLAK_STATUS_SOZLUGU | PARANTEZLI_STATUS_ANAHTARLARI

    metin = (KOK / "ROADMAP.md").read_text(encoding="utf-8")
    olculen = 0
    for satir in metin.splitlines():
        m = MADDE_SATIRI_DESENI.match(satir)
        if not m:
            continue
        olculen += 1
        beklenen = _alan_anahtarlari_ve_sozlugu(m.group(3))
        assert api._roadmap_alanlari(m.group(3)) == beklenen, (
            f"ucun alan bölmesi v351 çivisinden AYRIŞTI: {satir[:120]!r}")
    assert olculen >= 50, f"yalnız {olculen} başlık satırı karşılaştırıldı — kapsam çürümüş"


# --- MUTASYON KANITI: her çivinin ısırdığı dal ayrı ayrı gösterilir (CLAUDE.md §6) ---------------

def _sentetik(metin: str) -> dict:
    return api._roadmap_ayristir(metin, yol="sanal.md", bayt=len(metin.encode()),
                                 mtime=None, tam=True)


SEMA_TABLO_BASI = "# T\n\n## §2 SINAMA\n\n| id | name | status | owner | size | trigger |\n|---|---|---|---|---|---|\n"


def test_j_mutasyon_duzyazi_sutunu_ROZET_ALANI_DEGIL():
    """GERİLEME ÇİVİSİ — v337'nin 2026-09-01 kırmızısının ta kendisi.

    `TSK-062`nin tetiği "…learn program boyunca KAPALI" diyor, `TSK-077`nin adı "…2026-08-24
    elemesinde KAPANDI" diyor; ikisi de AÇIK kalemdi ve eski tarayıcı ikisini de tahtada
    "kapalı" gösteriyordu. Şema tablosunda rozet YALNIZ `status` sütunundadır."""
    metin = SEMA_TABLO_BASI + (
        "| TSK-900 | 12 alt-madde 2026-08-24 elemesinde KAPANDI | QUEUED | rol1 | M | — |\n"
        "| TSK-901 | kilit çifti | GATED(learn program boyunca KAPALI) | rol1 | M | learn açılışı |\n")
    satirlar = _sentetik(metin)["bolumler"][0]["tablolar"][0]["satirlar"]
    assert [s["durum"] for s in satirlar] == ["acik", "askida"], (
        f"düzyazı sütunu rozet alanına sızdı: {[s['durum'] for s in satirlar]}")
    assert satirlar[0]["hucre_durum"] == ["belirsiz", "belirsiz", "acik",
                                          "belirsiz", "belirsiz", "belirsiz"]


def test_j2_mutasyon_ESKI_SOZLUK_semasiz_tabloda_HALA_isiriyor():
    """BEDEL ÖLÇÜMÜ: daraltmanın bedeli, şemasız tabloların eski yolla ölçülmesini KAYBETMEK
    olurdu. Kaybedilmedi — §8.T tahta arşivi hâlâ rozet-düzyazısıyla yazılmıştır."""
    metin = ("# T\n\n## §8 ARŞİV\n\n| kalem | wp | not |\n|---|---|---|\n"
             "| ~~`X`~~ **✅ KAPANDI 2026-01-01** | WP1 | tarihçe |\n"
             "| **BLOKE:** dış bağımlılık | WP2 | gerekçe |\n")
    satirlar = _sentetik(metin)["bolumler"][0]["tablolar"][0]["satirlar"]
    assert [s["durum"] for s in satirlar] == ["kapali", "bloke"]
    assert all(s["sema"] is None for s in satirlar), "şemasız tabloya şema atandı"


def test_j3_mutasyon_ATIF_satiri_belirsiz_DEGIL():
    metin = SEMA_TABLO_BASI + "| TSK-902 | (bkz. TSK-902) | (bkz. TSK-902) | rol1 | — | — |\n"
    r = _sentetik(metin)["bolumler"][0]["tablolar"][0]["satirlar"][0]
    assert r["durum"] == "atif", r["durum"]
    assert r["sema"]["status"] is None and "ATIF" in r["sema"]["status_neden"]
    assert r["sema"]["sinif"] is None


def test_j4_mutasyon_sozluk_disi_status_UYDURULMUYOR():
    metin = SEMA_TABLO_BASI + "| TSK-903 | bir kalem | YOLDA | rol1 | M | — |\n"
    r = _sentetik(metin)["bolumler"][0]["tablolar"][0]["satirlar"][0]
    assert r["durum"] == "belirsiz"
    assert r["sema"]["status"] is None
    assert "sözlüğünde yok" in (r["sema"]["status_neden"] or "")


@pytest.mark.parametrize("govde, bekleniyor", [
    ("status: ACTIVE · born: 2026-09-01 · owner: rol1 · size: S · trigger: —", "acik"),
    ("status: QUEUED · born: 2026-09-01 · owner: rol1 · size: S · trigger: —", "acik"),
    ("status: INTERIM · born: 2026-09-01 · owner: rol1 · size: S · trigger: —", "acik"),
    ("status: GATED(operatör) · born: 2026-09-01 · owner: rol1 · size: S · trigger: onay", "askida"),
    ("status: OPERATOR · born: 2026-09-01 · owner: operator · size: S · trigger: —", "bloke"),
    ("status: DONE(2026-09-01·v351) · born: 2026-08-01 · owner: rol1 · size: S · trigger: —", "kapali"),
    ("status: DROPPED(2026-09-01·gereksiz) · born: 2026-08-01 · owner: rol1 · size: S · trigger: —",
     "kapali"),
])
def test_k_mutasyon_yeni_sozlugun_HER_degeri_kovaya_dusuyor(govde, bekleniyor):
    """Yeni sözlüğün YEDİ değeri de tanınıyor — biri düşerse tahta o kalemi işaretsiz gösterir."""
    metin = f"# T\n\n## §4 SINAMA\n\n- **[TSK-904] test** — {govde}\n"
    m = _sentetik(metin)["bolumler"][0]["maddeler"][0]
    assert m["durum"] == bekleniyor, f"{govde} → {m['durum']}"
    assert m["sema"]["status_detay"] is None or "(" not in m["sema"]["status"]


def test_l_mutasyon_sema_BICIMINDE_bozuk_madde_MUAF_sayilmiyor():
    """Şema biçiminde olup alanları tutmayan satır TARİHÇE değil BOZULMAdır ve ayrı sayılır."""
    bozuk = "# T\n\n## §4 SINAMA\n\n- **[TSK-905] test** — status: ACTIVE · owner: rol1\n"
    yuk = _sentetik(bozuk)
    b = yuk["bolumler"][0]
    assert b["maddeler"][0]["sema"] is None
    assert yuk["sayim"]["sema"]["ihlal_n"] == 1 and yuk["sayim"]["sema"]["muaf_tarihce"] == 1
    assert b["sema_ihlal"][0]["neden"].strip()

    duzyazi = "# T\n\n## §7 GÜNLÜK\n\n- 2026-08-30: bir karar satırı, şema biçiminde DEĞİL\n"
    yuk2 = _sentetik(duzyazi)
    assert yuk2["sayim"]["sema"]["ihlal_n"] == 0, "düzyazı satırı BOZULMA sayıldı — muafiyet silindi"
    assert yuk2["sayim"]["sema"]["muaf_tarihce"] == 1
    assert "sema_ihlal" not in yuk2["bolumler"][0]


def test_m_ozet_sema_alanini_SOKMEZ():
    """`?ozet=1` madde GÖVDESİNİ söker; şema gövdenin özetidir ve sökülürse dinamik tahta
    özet yolunda BOŞ çizilirdi (bu dosyanın kovaladığı arızanın aynısı, yeni alanda)."""
    yuk = _yuk()
    ozet = api._roadmap_ozetle(yuk["bolumler"])
    sayi = 0
    for kok in ozet:
        for b in _gez(kok):
            for m in b["maddeler"]:
                assert "sema" in m, "özet madde `sema` alanını düşürdü"
                sayi += m["sema"] is not None
            for t in b["tablolar"]:
                for r in t["satirlar"]:
                    assert "sema" in r, "özet tablo satırı `sema` alanını düşürdü"
                    sayi += r["sema"] is not None
    assert sayi >= 50, f"özette yalnız {sayi} şema kaydı kaldı"

"""test_takvim_bombasi_v526.py — TAKVİMLE ÇÜRÜYEN TEST SABİTLERİ için MEKANİK dedektör (TSK-210).

`tests/` altında kendi başına koşan bir TARAMA ÇİVİSİDİR; emsalleri
`test_tests_ops_satir_capasi_v401.py` ve `test_yorum_sembol_capasi_v402.py`. `codelaw`e
DOKUNMAZ (Rol-1 kararı 1) ve `meridian`i İMPORT ETMEZ — yalnız stdlib `ast`/`re` ile KAYNAK
METNİ okur. İmport etmemek bilinçli: bu çivi 700'e yakın dosyayı tarar ve yan etkisiz kalmalıdır.

VAKA (ölçüldü 2026-09-21, suite #71): `test_e2_seyrelme_kovasi_v477.py` modül düzeyinde
`GUN = "2026-09-13"` literali taşıyordu ve testler `analytics.py::entry_execution_summary`in
VARSAYILAN 7 günlük penceresini sınıyordu. Pencere `analytics.py::_entry_rows` içinde
`cutoff = bugün - days` ile hesaplanır ve satırlar `date >= cutoff` ile süzülür; ÜST SINIR
YOKTUR. Literal yazıldığı günden 7 gün sonra pencereden DÜŞTÜ: test 09-13→09-20 arası yeşil
kaldı, 09-21'de (8. gün) `assert (0 == 1)` ile kırmızıya döndü. KOD DEĞİŞMEDİ, yalnız takvim
ilerledi — yani sekiz günlük yeşil hiçbir şey kanıtlamıyordu ve kırmızısı bir regresyon değildi.

SINIFIN TANIMI (Rol-1 kararı 2) — (a) VE (b) birlikte:
  (a) test dosyasında MODÜL DÜZEYİ literal tarih sabiti (`^[A-Z_][A-Z0-9_]* *= *"20\\d\\d-…"`;
      `_` önekli adlar DAHİL — canlı örnekleri `_BUGUN`/`_SEANS`/`_PENCERE`), VE
  (b) AYNI dosyada BUGÜNE-GÖRELİ PENCERE TÜKETİMİ.
Literal TEK BAŞINA suç DEĞİLDİR: `test_mutabakat_bayatligi_v325.py`nin Cuma/Pazartesi çifti gibi
PİNLENMİŞ senaryolar meşrudur, ve "çok eski olmak" iddiası taşıyan literaller (`2020-01-01`)
ÇÜRÜMEZ — zamanla ancak GÜÇLENİRLER.

(b) İKİ KOLDAN ÖLÇÜLÜR:
  b1 ÜRETİM KOLU (asıl kol, v477'nin sınıfı) — dosya, `meridian/` içinde BUGÜNE-GÖRELİ pencere
     türeten bir fonksiyonu çağırıyor. Liste ELLE SABİTLENMEZ: `_uretim_ciftleri` her koşumda
     `meridian/` ağacını AST ile TARAR (Rol-1 kararı 2'nin "TEK yerde, ölçülerek" şartı). Yeni
     bir `bugün - timedelta` fonksiyonu doğduğu gün liste KENDİLİĞİNDEN büyür; ayrışma çivisi
     `test_6_…` sentetik bir ağaçta bunu ÖLÇER.
  b2 KENDİ-PENCERE KOLU — dosya pencereyi KENDİ hesaplıyor VE onu bir KARŞILAŞTIRMA SINIRI
     olarak kullanıyor (`ast.Compare` operandı). "Sınır olarak kullanmak" şartı Rol-1 kararı
     5'in gereğidir: tarih ÜRETEN ama pencere TÜKETMEYEN takvim yardımcıları (`_hafta_ici`,
     `_dun` gibi `return bugün - 1` döndüren fonksiyonlar) KIRMIZI OLMAMALI. Yardımcının
     gövdesinde karşılaştırma yoktur; bomba şeklinde (`cutoff = bugün - 7` … `assert GUN >=
     cutoff`) vardır. Kapsam FONKSİYON-YERELDİR: dönüş değeri üzerinden fonksiyon sınırını
     aşan bir veri akışı İZLENMEZ (izlenseydi her yardımcı kullanımı kırmızı olurdu).

KAÇIŞ BEYANLA (Rol-1 kararı 3): sabitin KENDİ satırında `# takvim-bagimsiz: <≥20 karakter
gerekçe>`. Gerekçesiz ya da 20 karakterden kısa gerekçeli kaçış YOKTUR — Yasa 4'ün
`sessiz-yutma` işaretiyle aynı disiplin: muafiyet OKUNABİLİR bir cümle bırakır.

ÖLÇÜLMÜŞ ZEMİN (bu turda, 2026-09-21, bu dosyanın kendi yardımcılarıyla):
  · `tests/` altında modül düzeyi `20\\d\\d` literali taşıyan 29 dosya (2026 taşıyan 21).
  · `meridian/` altında bugüne-göreli pencere türeten 23 NİTELİKLİ (modül, fonksiyon) çifti;
    bunların 11'i TOHUM (gövdesinde doğrudan `bugün - timedelta`), 12'si aynı modül içinden
    tohumu çağıran sarmalayıcı (örn. `analytics.py::entry_execution_summary` →
    `analytics.py::_entry_rows`).
  · (a)∧(b) tutan dosya: SIFIR — çivi bugün YEŞİL, ama ölçülerek (hüküm tablosu devir raporunda).
  · TARİHSEL POZİTİF KONTROL: v477'nin DÜZELTME ÖNCESİ metni (git blob `89138db9^`) bu
    dedektörden KIRMIZI geçer — `GUN="2026-09-13"` + `analytics.entry_execution_summary`
    vuruşu. Yani çivi, yakalamak için var olduğu bombayı GERÇEKTEN yakalıyor. İskeleti
    `test_7_TARIHSEL_PK_…`te sentetik olarak donduruldu (gerçek blob'a bağlanmadı: `.git` her
    koşum ortamında yoktur — A1'de `/opt/meridian` git'siz kurulur).

YANLIŞ-POZİTİF BEDELİ ÖLÇÜLDÜ (Rol-1 kararı 5 + bedel yasası): b2'yi "karşılaştırma sınırı"
yerine "dosyada `bugün - timedelta` GEÇİYOR" diye GEVŞEK tanımlasaydık, bugün TEK bir dosya
fazladan kırmızı olurdu: `test_geridolum_ileri_dolum_v483.py`. O dosyanın literalleri
(`PENCERE_ONCESI`/`PENCERE_BASI`) DONUK bir üretim sabitine (`ILERI_PENCERE_BASI`, sürücü
`deploy/oracle-a1/` altında) pinlidir ve tezgâhın saati SAHTEDİR; `bugün - 1` ise AYRI bir
testin yardımcısıdır. Yani gevşek kol sahte alarm üretirdi. Bu bedel `test_8_…`te sayıyla
çivilenmiştir ki tarafsız kalsın: büyürse GÖRÜLÜR.

AÇIK KALAN (Rol-1'e): Rol-1 kararı 2 b-kolunu "doğrudan `date.today()`/`datetime.now()`
çağrısı" diye de okumaya açıktı; kararı 5 ise tarih üreten yardımcıların kırmızı olmamasını
şart koşuyordu. İkisi `test_geridolum_ileri_dolum_v483.py`te ÇARPIŞIYOR. Bu dosya kararı 5'i
(daha özel şartı) uyguladı ve gevşek kolun farkını ölçülü bıraktı; hüküm Rol-1'indir.

KAYIP AÇIK — BU ÇİVİNİN BİLİNÇLİ KÖR NOKTALARI (Rol-1 direktifi, tur 2, 2026-09-21). Beyan
BURADA yaşar, devir raporunda DEĞİL: rapor scratchpad'dedir ve kaybolduğu gün beyan da
kaybolurdu. Bir tarayıcının ne GÖRMEDİĞİ, ne gördüğü kadar sözleşmedir.

KÖR NOKTA 1 — TOHUM DESENİ BİÇİME BAĞLI. `_pencere_ifadesi` yalnız `<bugün> - <süre>`
çıkarmasını tanır. Pencereyi BAŞKA türlü hesaplayan bir üretim fonksiyonu (`relativedelta`,
ay/çeyrek aritmetiği, gün alanını değiştirerek ay başına inen biçimler) tohum listesine GİRMEZ
ve yasa o yüzeyde KÖRDÜR — çivi, bilinen vokabülerle konuşulmadığında ÖTMEZ.
  BEDEL ÖLÇÜLDÜ (2026-09-21): `meridian/` altında `relativedelta` kullanımı 0, `monthrange` ve
  gün/ay alanını değiştiren biçim 0. Kör nokta bugün BOŞ — ama bu "yok" değil "HENÜZ DOĞMADI"
  demektir; boşluk bir güvence değil, bir sayaç durumudur.
  YENİDEN ÖLÇÜM TETİĞİ: `meridian/` altında ilk `relativedelta` (ya da ay/çeyrek aritmetiğiyle
  pencere kuran ilk fonksiyon) doğduğu GÜN tohum deseni genişletilir ve bu iki sayı yeniden
  ölçülür. Genişletmeden ÖNCE `test_5d`/`test_5f`in koruduğu çıkarma ve yön şartlarının ne
  kaybettiği de sayılır — gevşeyen desen yanlış alarm üretir (bedel yasası, iki yönlü).

KÖR NOKTA 2 — KAPANIŞ AYNI MODÜLLE SINIRLI. `_uretim_ciftleri` tohumu yalnız AYNI dosyadaki
çağıranlara yayar; BAŞKA bir modüldeki sarmalayıcı listeye girmez.
  BEDEL ÖLÇÜLDÜ (2026-09-21): bugün YEDİ üretim fonksiyonu bu boşlukta duruyor (dokuz çağrı
  kenarı) — `analytics.coverage_breakage_counters`, `api.api_diagnostics`, `api.api_selfreview`,
  `api.summary`, `hermes.integrations_status`, `loop.daily_cycle`, `scheduler.advance_once`.
  CANLI BEDELİ SIFIR: literal taşıyan 29 dosyanın HİÇBİRİ bu yedi yüzeyden birini çağırmıyor,
  yani boşluk bugün hiçbir bombayı gizlemiyor.
  NEDEN GENİŞLETİLMEDİ — TERCİH DEĞİL, ÖLÇÜM: isim-tabanlı geçişli kapanış bu turda denendi ve
  1731 ADA PATLADI; takma ad çözümü olmayan çıplak ad eşleşmesi (`main`/`fetch`/`build`/`ozet`
  gibi adlar yüzünden) 100'DEN FAZLA test dosyasını sahte kırmızı yaptı. İki alternatif de
  ölçülerek reddedildi.
  YENİDEN ÖLÇÜM TETİĞİ: yukarıdaki yedi yüzeyden biri literal taşıyan bir test dosyasından
  çağrıldığı gün (ya da liste büyüdüğünde). O zaman yazılacak şey NİTELİKLİ modüller-arası
  kapanıştır — import çözümüyle, İSİMLE DEĞİL — ve patlama sayısı yeniden ölçülür.

ÖLÇÜLMEDİ (dürüst boşluk, uydurma yasağı): `meridian/` DIŞINDAKİ pencere üreticileri. `ops/`
ve `deploy/` altındaki sürücüler HİÇ taranmıyor; bir test dosyası oradan pencere tüketirse bu
çivi GÖRMEZ. Kaç böyle yüzey olduğu bu turda ölçülmedi — kapsam genişletmesi ayrı bir turun işi.

SAYI DÜZELTMESİ (Rol-1'in hatası, tur 1'de ölçülerek bulundu): brief "`tests/` altında 19 dosya
modül düzeyi literal taşıyor" diyordu. O sayı `^[A-Z_]+ = "2026-…"` DAR deseniyle ölçülmüştü ve
ad içinde RAKAM taşıyan sabitleri (`D0`/`D1`) ile 2026 dışı yılları kaçırıyordu. Bu dosyanın
sevk edilen deseniyle gerçek sayı 29'dur (2026 taşıyan 21). Hüküm değişmedi: 29'un da hepsi yeşil.
"""
from __future__ import annotations

import ast
import functools
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[1]
MERIDIAN = REPO / "meridian"
TESTLER = REPO / "tests"

#: (a) — MODÜL DÜZEYİ literal tarih sabiti. `^` + `re.M`: girintili (fonksiyon içi) atamalar ve
#: çağrı içi anahtar sözcükler (`date="2020-01-01"`) BİLEREK dışarıdadır — bomba sınıfı, dosyanın
#: TAMAMINI besleyen modül düzeyi sabittir. `[A-Z_][A-Z0-9_]*`: `_` önekli ve rakam taşıyan adlar
#: dahil (canlı örnekler: `_BUGUN`, `D0`, `GHOST_2025`).
_LITERAL_DESENI = re.compile(r'^(?P<ad>[A-Z_][A-Z0-9_]*) *= *"(?P<tarih>20\d\d-\d\d-\d\d)"', re.M)

#: "Bugün" kaynakları. `utcnow` da sayılır: emekli olsa da metinde durduğu sürece pencere üretir.
_BUGUN_CAGRILARI = frozenset({"today", "now", "utcnow"})

#: (Rol-1 kararı 3) Kaçış işareti ve asgari gerekçe uzunluğu — TEK KAYNAK burasıdır.
_BEYAN_ISARETI = "takvim-bagimsiz"
_BEYAN_ASGARI_GEREKCE = 20
_BEYAN_DESENI = re.compile(r"#\s*" + _BEYAN_ISARETI + r"\s*:\s*(?P<gerekce>.*)$")


# =================================================================================================
# ÇEKİRDEK — AST yardımcıları
# =================================================================================================

def _son_ad(dugum: ast.AST) -> str | None:
    """`f`, `x.f`, `a.b.f` → hepsi için `f`. Çağrı hedefinin SON adı; modül takma adı burada
    değil `_meridian_takma_adlari`de çözülür."""
    if isinstance(dugum, ast.Name):
        return dugum.id
    if isinstance(dugum, ast.Attribute):
        return dugum.attr
    return None


def _cagri_adlari(dugum: ast.AST) -> set[str]:
    return {a for c in ast.walk(dugum) if isinstance(c, ast.Call)
            if (a := _son_ad(c.func)) is not None}


def _pencere_ifadesi(dugum: ast.AST) -> bool:
    """BUGÜNE-GÖRELİ PENCERE ifadesi mi: `<bugün çağrısı> - <timedelta çağrısı>`.

    Çıkarma (`ast.Sub`) ŞARTTIR: `şimdi < kapanış + timedelta(...)` gibi İLERİ bir eşik
    (`scheduler.py::_leg_ready`) pencere DEĞİLDİR, gecikmedir — onu saymak yanlış alarmdı."""
    if not (isinstance(dugum, ast.BinOp) and isinstance(dugum.op, ast.Sub)):
        return False
    return bool(_cagri_adlari(dugum.left) & _BUGUN_CAGRILARI) and \
        "timedelta" in _cagri_adlari(dugum.right)


def _kapsamlar(agac: ast.AST):
    """Dosyayı KAPSAMLARA böler: modül gövdesi + her `def`/`class` AYRI kapsam. İç içe
    fonksiyonlar dış kapsama SIZMAZ — b2 kolunun fonksiyon-yerelliği buradan gelir."""
    yigin: list[ast.AST] = [agac]
    while yigin:
        kok = yigin.pop()
        govde: list[ast.AST] = []

        def gez(dugum: ast.AST) -> None:
            for cocuk in ast.iter_child_nodes(dugum):
                if isinstance(cocuk, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    yigin.append(cocuk)
                    continue
                govde.append(cocuk)
                gez(cocuk)

        gez(kok)
        yield govde


# =================================================================================================
# b1 — ÜRETİM KOLU: `meridian/` ağacından ÖLÇÜLEN (modül, fonksiyon) çiftleri
# =================================================================================================

@functools.lru_cache(maxsize=8)
def _uretim_ciftleri(kok: pathlib.Path) -> frozenset[tuple[str, str]]:
    """`kok` altındaki her `.py` için: gövdesinde bugüne-göreli pencere ifadesi olan fonksiyonlar
    (TOHUM) + AYNI MODÜL içinden onları çağıranlar (sabit noktaya kadar).

    NEDEN NİTELİKLİ (modül, fonksiyon) ve NEDEN AYNI MODÜL:
      · Çıplak ADLA eşleştirmek felakettir: `main`/`fetch`/`build`/`ozet` gibi adlar üretimde de
        `ops/` tarafında da vardır; ham ad eşleşmesi bu turda 100'den fazla test dosyasını
        SAHTE kırmızıya çevirdi (ölçüldü 2026-09-21). Çağrı, dosyanın `meridian` import'undan
        çözülen TAKMA AD üzerinden eşleşir.
      · Modüller ARASI geçişli kapanış da felakettir: isimle kurulan çağrı çizgesi aynı adlı
        farklı fonksiyonları birleştirir ve kapanış 1731 ada patladı (aynı ölçüm). Aynı modül
        içinde kalmak `analytics.py::entry_execution_summary` → `analytics.py::_entry_rows`
        sarmalayıcısını (v477'nin GERÇEK yolu) yakalamaya YETER.

    KÖK PARAMETRELİDİR: liste elle sabitlenmediği için bayatlayamaz, ve sentetik bir ağaçla
    ölçülebilir (`test_6_…` ayrışma çivisi)."""
    ciftler: set[tuple[str, str]] = set()
    for yol in sorted(kok.rglob("*.py")):
        try:
            agac = ast.parse(yol.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            # sessiz-yutma: taranan ağaçta ayrıştırılamayan dosya bu yasanın konusu değildir;
            # sözdizimi hatasını asıl suite zaten import anında kırmızı yapar
            continue
        fonksiyonlar = [(d.name, d) for d in ast.walk(agac)
                        if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef))]
        kume = {ad for ad, d in fonksiyonlar
                if any(_pencere_ifadesi(a) for a in ast.walk(d))}
        degisti = True
        while degisti:
            degisti = False
            for ad, d in fonksiyonlar:
                if ad not in kume and (_cagri_adlari(d) & kume):
                    kume.add(ad)
                    degisti = True
        ciftler |= {(yol.stem, ad) for ad in kume}
    return frozenset(ciftler)


def _meridian_takma_adlari(agac: ast.AST) -> tuple[dict[str, str], dict[str, str]]:
    """Dosyanın `meridian` import'larını çözer.

    Döner: (modül takma adı → modül adı, çıplak ad → modül adı). `from meridian import analytics
    as an` → `{"an": "analytics"}`; `from meridian.adapters import insider` →
    `{"insider": "insider"}`; `from meridian.analytics import entry_execution_summary` →
    çıplak ad tablosuna."""
    modul_alias: dict[str, str] = {}
    ciplak: dict[str, str] = {}
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.ImportFrom) and dugum.module:
            parcalar = dugum.module.split(".")
            if parcalar[0] != "meridian":
                continue
            for ad in dugum.names:
                yerel = ad.asname or ad.name
                if len(parcalar) == 1:          # from meridian import <modül>
                    modul_alias[yerel] = ad.name
                else:                            # from meridian.<paket>.<modül> import <ad>
                    ciplak[yerel] = parcalar[-1]
                    modul_alias[yerel] = ad.name
        elif isinstance(dugum, ast.Import):
            for ad in dugum.names:
                if ad.name.startswith("meridian."):
                    modul_alias[ad.asname or ad.name.split(".")[-1]] = ad.name.split(".")[-1]
    return modul_alias, ciplak


def _uretim_tuketimi(kaynak: str, ciftler: frozenset[tuple[str, str]]) -> list[str]:
    """b1: dosyanın ÇAĞIRDIĞI, ölçülmüş bugüne-göreli pencere fonksiyonları (`modül.fonksiyon`,
    sıralı). Boş liste "bu dosya üretim penceresi tüketmiyor" demektir."""
    agac = ast.parse(kaynak)
    modul_alias, ciplak = _meridian_takma_adlari(agac)
    vurus: set[str] = set()
    for dugum in ast.walk(agac):
        if not isinstance(dugum, ast.Call):
            continue
        hedef = dugum.func
        if isinstance(hedef, ast.Attribute) and isinstance(hedef.value, ast.Name):
            modul = modul_alias.get(hedef.value.id)
            if modul and (modul, hedef.attr) in ciftler:
                vurus.add(f"{modul}.{hedef.attr}")
        elif isinstance(hedef, ast.Name):
            modul = ciplak.get(hedef.id)
            if modul and (modul, hedef.id) in ciftler:
                vurus.add(f"{modul}.{hedef.id}")
    return sorted(vurus)


# =================================================================================================
# b2 — KENDİ-PENCERE KOLU: pencere KARŞILAŞTIRMA SINIRI olarak kullanılıyor mu
# =================================================================================================

def _kendi_pencere_tuketimi(kaynak: str) -> bool:
    """Dosya kendi hesapladığı bugüne-göreli pencereyi bir SINIR olarak mı kullanıyor?

    ŞART: pencere ifadesi (ya da ondan atanan ad) AYNI KAPSAMDA bir `ast.Compare` içinde
    geçmeli. Bu, Rol-1 kararı 5'in "tarih ÜRETEN ama pencere TÜKETMEYEN yardımcılar kırmızı
    olmamalı" şartının mekanik karşılığıdır: `return bugün - 1` döndüren bir yardımcının
    gövdesinde karşılaştırma YOKTUR, `assert GUN >= cutoff` yazan bir bombada VARDIR."""
    agac = ast.parse(kaynak)
    for govde in _kapsamlar(agac):
        pencere_adlari: set[str] = set()
        for dugum in govde:
            if isinstance(dugum, ast.Assign) and any(_pencere_ifadesi(a)
                                                     for a in ast.walk(dugum.value)):
                pencere_adlari |= {h.id for h in dugum.targets if isinstance(h, ast.Name)}
        for dugum in govde:
            for alt in ast.walk(dugum):
                if not isinstance(alt, ast.Compare):
                    continue
                icerik = list(ast.walk(alt))
                if any(_pencere_ifadesi(x) for x in icerik):
                    return True
                if any(isinstance(x, ast.Name) and x.id in pencere_adlari for x in icerik):
                    return True
    return False


def _gevsek_pencere_tuketimi(kaynak: str) -> bool:
    """b2'nin GEVŞEK okunuşu (Rol-1 kararı 2'nin lafzı): dosyada bugüne-göreli pencere ifadesi
    GEÇİYOR mu — sınır olarak kullanılsın ya da kullanılmasın. Hüküm ÜRETMEZ; yalnız
    `test_8_…`in ölçtüğü BEDELİ hesaplar (bedel yasası: dar kola geçmenin ne kazandırdığı değil,
    ne kaybettirdiği de sayılır)."""
    return any(_pencere_ifadesi(d) for d in ast.walk(ast.parse(kaynak)))


# =================================================================================================
# HÜKÜM
# =================================================================================================

def _literaller(kaynak: str) -> list[tuple[int, str, str, str]]:
    """(satır no, ad, tarih, satırın TAM metni) — beyan aynı satırda aranacağı için metin de döner."""
    satirlar = kaynak.splitlines()
    bulunan = []
    for eslesme in _LITERAL_DESENI.finditer(kaynak):
        no = kaynak.count("\n", 0, eslesme.start()) + 1
        bulunan.append((no, eslesme.group("ad"), eslesme.group("tarih"), satirlar[no - 1]))
    return bulunan


def _beyan_gecerli(satir: str) -> bool:
    """`# takvim-bagimsiz: <≥20 karakter>` — işaret VAR ama gerekçe kısa/boşsa kaçış YOKTUR."""
    eslesme = _BEYAN_DESENI.search(satir)
    return bool(eslesme) and len(eslesme.group("gerekce").strip()) >= _BEYAN_ASGARI_GEREKCE


def _takvim_bombalari(kaynak: str, ciftler: frozenset[tuple[str, str]]) -> list[str]:
    """(a)∧(b) hükmü. Tüketim yoksa literal masumdur ve HİÇ bakılmaz (pinlenmiş senaryolar)."""
    literaller = _literaller(kaynak)
    if not literaller:
        return []
    tuketim = _uretim_tuketimi(kaynak, ciftler)
    kendi = _kendi_pencere_tuketimi(kaynak)
    if not tuketim and not kendi:
        return []
    neden = ", ".join(tuketim) if tuketim else "dosyanın kendi bugüne-göreli penceresi"
    return [f"{ad}={tarih} (satır {no}) — bugüne-göreli pencere tüketimi: {neden}"
            for no, ad, tarih, satir in literaller if not _beyan_gecerli(satir)]


# =================================================================================================
# SENTETİK FİKSTÜRLER — v477'nin sınıfının İSKELETİ
# =================================================================================================

_IMPORT = "from meridian import analytics as an\n"
_LITERAL = 'GUN = "2026-09-13"'
_CAGRI = "\n\ndef test_x():\n    return an.entry_execution_summary()\n"


def _ciftler() -> frozenset[tuple[str, str]]:
    return _uretim_ciftleri(MERIDIAN)


# =================================================================================================
# 1-4 — DEDEKTÖRÜN DÖRT KÖŞESİ (brief maddeleri 1-4)
# =================================================================================================

def test_1_literal_ARTI_uretim_cagrisi_KIRMIZI():
    """v477'nin sınıfı: modül düzeyi literal + varsayılan pencereli üretim çağrısı. Pozitif
    kontrol — sıfır iddiası ancak dedektör GERÇEKTEN ısırıyorsa anlamlıdır."""
    bulgu = _takvim_bombalari(_IMPORT + _LITERAL + _CAGRI, _ciftler())
    assert len(bulgu) == 1, bulgu
    assert "GUN=2026-09-13" in bulgu[0] and "analytics.entry_execution_summary" in bulgu[0]


def test_2a_BEYAN_20_KARAKTERLIK_GEREKCEYLE_YESIL():
    """Kaçış BEYANLA (Rol-1 kararı 3): tam 20 karakterlik gerekçe SINIRDA geçer."""
    gerekce = "x" * _BEYAN_ASGARI_GEREKCE
    kaynak = _IMPORT + _LITERAL + f"  # {_BEYAN_ISARETI}: {gerekce}" + _CAGRI
    assert _takvim_bombalari(kaynak, _ciftler()) == []


def test_2b_BEYAN_19_KARAKTERLIK_GEREKCEYLE_KIRMIZI():
    """19 karakter kaçış SAYILMAZ — eşik `_BEYAN_ASGARI_GEREKCE`den TÜRETİLİR, elle 19/20
    yazılmaz (eşik değişirse bu çivi onunla birlikte kayar, sessizce ayrışmaz)."""
    gerekce = "x" * (_BEYAN_ASGARI_GEREKCE - 1)
    kaynak = _IMPORT + _LITERAL + f"  # {_BEYAN_ISARETI}: {gerekce}" + _CAGRI
    assert len(_takvim_bombalari(kaynak, _ciftler())) == 1


def test_2c_ISARETSIZ_YORUM_kacis_SAYILMAZ():
    """Uzun ama İŞARETSİZ bir yorum kaçış değildir — aksi hâlde her açıklamalı satır muaf
    olurdu ve yasa kendini kapatırdı."""
    kaynak = _IMPORT + _LITERAL + "  # bu gayet uzun ama isaretsiz bir yorumdur" + _CAGRI
    assert len(_takvim_bombalari(kaynak, _ciftler())) == 1


def test_3_literal_VAR_tuketim_YOK_YESIL():
    """YANLIŞ-POZİTİF ÇİVİSİ: literal tek başına suç DEĞİLDİR (pinlenmiş senaryolar)."""
    assert _takvim_bombalari(_LITERAL + "\n", _ciftler()) == []


def test_4_literal_YOK_tuketim_VAR_YESIL():
    """Simetrik köşe: pencere tüketen ama literal taşımayan dosya temizdir."""
    assert _takvim_bombalari(_IMPORT + _CAGRI, _ciftler()) == []


def test_4b_GIRINTILI_literal_MODUL_DUZEYI_DEGILDIR():
    """Fonksiyon içi sabit ve çağrı içi anahtar sözcük (v477'de kalan `2020-01-01` böyledir)
    kapsam DIŞIDIR: bomba sınıfı dosyanın TAMAMINI besleyen modül düzeyi sabittir."""
    kaynak = _IMPORT + "\n\ndef test_y():\n    GUN = \"2026-09-13\"\n" \
                       "    return an.entry_execution_summary(), GUN\n"
    assert _takvim_bombalari(kaynak, _ciftler()) == []


def test_4c_ALT_CIZGI_ONEKLI_ve_RAKAMLI_adlar_GORULUR():
    """Canlı ağaçta `_BUGUN`, `_SEANS`, `D0`, `GHOST_2025` var — desen bunları GÖRMELİ, aksi
    hâlde yasa kendi kapsamında kör kalırdı (Rol-1 kararı 2: `_` önekli adlar dahil)."""
    adlar = {ad for _, ad, _, _ in _literaller(
        '_BUGUN = "2026-09-14"\nD0 = "2026-07-29"\nGHOST_2025 = "2025-05-26"\n')}
    assert adlar == {"_BUGUN", "D0", "GHOST_2025"}


# =================================================================================================
# b2 KOLU — SINIR KULLANIMI vs YARDIMCI (Rol-1 kararı 5)
# =================================================================================================

def test_5a_KENDI_PENCERESI_SINIR_OLARAK_kullanilinca_KIRMIZI():
    """Üretim çağrısı OLMADAN da bomba kurulabilir: dosya pencereyi kendi hesaplar ve literali
    ona karşı süzer."""
    kaynak = ('import datetime as dt\nGUN = "2026-09-13"\n\n'
              "def test_z():\n"
              "    kesim = (dt.date.today() - dt.timedelta(days=7)).isoformat()\n"
              "    assert GUN >= kesim\n")
    assert _kendi_pencere_tuketimi(kaynak) is True
    assert len(_takvim_bombalari(kaynak, _ciftler())) == 1


def test_5b_TAKVIM_YARDIMCISI_pencere_TUKETMEZ_YESIL():
    """Rol-1 kararı 5'in tam şartı: `return bugün - 1` döndüren bir yardımcı tarih ÜRETİR,
    pencere TÜKETMEZ. Aynı dosyada pinlenmiş literaller bulunsa bile kırmızı OLMAMALI."""
    kaynak = ('import datetime as dt\nPENCERE_BASI = "2026-09-04"\n\n'
              "def _dun():\n"
              "    return (dt.date.today() - dt.timedelta(days=1)).isoformat()\n\n"
              "def test_z():\n"
              "    assert PENCERE_BASI == PENCERE_BASI\n")
    assert _kendi_pencere_tuketimi(kaynak) is False
    assert _takvim_bombalari(kaynak, _ciftler()) == []


def test_5c_YARDIMCININ_DONUSU_KAPSAM_DISINDA_kalir():
    """Fonksiyon-yerellik çivisi: yardımcının DÖNÜŞÜ başka bir kapsamda karşılaştırmaya girse
    bile pencere ifadesi O kapsamda değildir. Veri akışını fonksiyon sınırı boyunca izleseydik
    her yardımcı kullanımı kırmızı olur, yasa gürültüye boğulurdu."""
    kaynak = ('import datetime as dt\nGUN = "2026-09-13"\n\n'
              "def _dun():\n"
              "    return (dt.date.today() - dt.timedelta(days=1)).isoformat()\n\n"
              "def test_z():\n"
              "    assert GUN != _dun()\n")
    assert _kendi_pencere_tuketimi(kaynak) is False


def test_5f_YON_SARTI_bugun_SOLDA_timedelta_SAGDA_olmali():
    """`_pencere_ifadesi` YÖN de arar: çıkarmanın SOLUNDA bugün, SAĞINDA süre. Yön şartı
    kalkıp "ifadenin herhangi bir yerinde ikisi de geçiyor" denseydi, dıştaki çıkarma İÇTEKİ
    pencereyi ikinci kez (ve yanlış sınırla) sayardı. Mutasyon turunda ölçüldü: yön şartı ancak
    BU biçimde yük taşır (2026-09-21)."""
    dis = ast.parse("dt.timedelta(days=7) - (dt.datetime.now(dt.timezone.utc) - baz)").body[0]
    assert _pencere_ifadesi(dis.value) is False
    ic = ast.parse("dt.date.today() - dt.timedelta(days=7)").body[0]
    assert _pencere_ifadesi(ic.value) is True


def test_5e_KAPSAM_AYRIMI_AYRI_FONKSIYONLARI_BIRLESTIRMEZ():
    """`_kapsamlar` neden var: yerel değişken adları (`kesim`, `cutoff`, `g`) dosya içinde
    TEKRARLANIR. Kapsamlar birleştirilseydi, bir yardımcıdaki `kesim = bugün - 7` ile BAŞKA bir
    testteki `assert GUN >= kesim` sessizce EŞLEŞİR ve sahte alarm üretirdi. İki `kesim` AYRI
    değişkendir; çivi bunu ölçer."""
    kaynak = ('import datetime as dt\nGUN = "2026-09-13"\nSABIT = "2026-09-01"\n\n'
              "def _yardimci():\n"
              "    kesim = dt.date.today() - dt.timedelta(days=7)\n"
              "    return kesim.isoformat()\n\n"
              "def test_z():\n"
              "    kesim = SABIT\n"
              "    assert GUN >= kesim\n")
    assert _kendi_pencere_tuketimi(kaynak) is False
    assert _takvim_bombalari(kaynak, _ciftler()) == []


def test_5d_ILERI_ESIK_pencere_DEGILDIR():
    """`şimdi < kapanış + timedelta(...)` bir GECİKME eşiğidir (canlı örnek
    `scheduler.py::_leg_ready`), bugüne-göreli pencere DEĞİL. Çıkarma şartı olmasaydı bu ve
    benzeri onlarca satır sahte alarm üretirdi."""
    kaynak = ("import datetime as dt\n"
              "def _hazir(kapanis):\n"
              "    return dt.datetime.now(dt.timezone.utc) < kapanis + dt.timedelta(minutes=30)\n")
    assert _kendi_pencere_tuketimi(kaynak) is False


# =================================================================================================
# 6 — AYRIŞMA ÇİVİSİ: ÜRETİM LİSTESİ ÖLÇÜLÜR, SABİTLENMEZ (Rol-1 kararı 2)
# =================================================================================================

def test_6a_URETIM_LISTESI_SENTETIK_AGACTA_YENI_FONKSIYONU_GORUR(tmp_path):
    """Liste elle sabitlenseydi, üretimde yeni bir `bugün - timedelta` fonksiyonu doğduğu gün
    BAYATLARDI ve yasa o yüzeyde KÖR kalırdı. Burada sentetik bir `meridian/` ağacı kurulur ve
    listenin onu KENDİLİĞİNDEN gördüğü ölçülür — sarmalayıcısıyla birlikte."""
    sahte = tmp_path / "meridian"
    sahte.mkdir()
    (sahte / "yeni_modul.py").write_text(
        "import datetime as dt\n\n"
        "def yeni_pencere(gun=7):\n"
        "    return (dt.date.today() - dt.timedelta(days=gun)).isoformat()\n\n"
        "def sarmalayici():\n"
        "    return yeni_pencere()\n",
        encoding="utf-8")
    ciftler = _uretim_ciftleri(sahte)
    assert ("yeni_modul", "yeni_pencere") in ciftler, ciftler
    assert ("yeni_modul", "sarmalayici") in ciftler, \
        "aynı modüldeki sarmalayıcı kaçtı — v477'nin GERÇEK yolu tam buydu"


def test_6b_LISTE_SABITLENMIS_DEGIL_KOKE_GORE_DEGISIR(tmp_path):
    """Ayrışma çivisinin ikinci yarısı: fonksiyon KÖKE bakıyor mu, yoksa sabit bir küme mi
    döndürüyor? Sentetik kökün sonucu canlı kökünkinden FARKLI olmalı."""
    sahte = tmp_path / "meridian"
    sahte.mkdir()
    (sahte / "yalniz.py").write_text(
        "import datetime as dt\n"
        "def tek(): return dt.date.today() - dt.timedelta(days=1)\n", encoding="utf-8")
    assert _uretim_ciftleri(sahte) == frozenset({("yalniz", "tek")})
    assert _uretim_ciftleri(sahte) != _ciftler()


def test_6c_SARMALAYICI_BASKA_MODULDEN_GECISMEZ(tmp_path):
    """Kapanışın SINIRI da sözleşmedir: modüller arası isim-tabanlı geçiş bu turda 1731 ada
    patladı (ölçüldü 2026-09-21) ve `main`/`fetch` gibi adlar yüzlerce dosyayı sahte kırmızı
    yapardı. Sınır burada ADIYLA çivilenir — gevşetilirse bu çivi öter."""
    sahte = tmp_path / "meridian"
    sahte.mkdir()
    (sahte / "kaynak.py").write_text(
        "import datetime as dt\n"
        "def tohum(): return dt.date.today() - dt.timedelta(days=1)\n", encoding="utf-8")
    (sahte / "baska.py").write_text("from .kaynak import tohum\ndef disari(): return tohum()\n",
                                    encoding="utf-8")
    ciftler = _uretim_ciftleri(sahte)
    assert ("kaynak", "tohum") in ciftler
    assert ("baska", "disari") not in ciftler


# =================================================================================================
# 7 — TARİHSEL POZİTİF KONTROL + CANLI ÜRETİM LİSTESİNİN KÖRLÜK ALARMI
# =================================================================================================

def test_7a_v477_DUZELTME_ONCESI_ISKELETI_YAKALANIR():
    """Çivi, VAR OLMA SEBEBİ olan bombayı yakalıyor mu? v477'nin düzeltme öncesi metni (git
    blob `89138db9^`) bu turda ÖLÇÜLDÜ ve kırmızı geçti; iskeleti burada donduruldu — gerçek
    blob'a bağlanmadı, çünkü `.git` her koşum ortamında yoktur (A1 kurulumu git'sizdir) ve
    çivinin "koşamadım"ı "temiz" ile karışmamalı."""
    iskelet = ("from meridian import analytics as an\n"
               'GUN = "2026-09-13"\n\n'
               "def test_a5(sandbox_state):\n"
               "    dar = an.entry_execution_summary()['seyrelme']\n"
               "    assert dar['n'] == 1\n")
    bulgu = _takvim_bombalari(iskelet, _ciftler())
    assert len(bulgu) == 1 and "analytics.entry_execution_summary" in bulgu[0], bulgu


def test_7b_CANLI_URETIM_LISTESI_BILINEN_TOHUMLARI_TASIR():
    """KÖRLÜK ALARMI (v401'in `TARAMA_SESSIZCE_BOS_DEGIL` emsali): "0 ihlal" cümlesi ancak liste
    GERÇEKTEN doluysa anlamlıdır. Yanlış kök ya da bozuk desen boş küme döndürür ve tarama
    ebediyen yeşil kalırdı. Bu beş çift bugün ölçüldü (2026-09-21) ve hepsi TOHUM/sarmalayıcı
    olarak canlıdır; biri kaybolursa desen daralmış demektir."""
    ciftler = _ciftler()
    for beklenen in (("analytics", "_entry_rows"), ("analytics", "entry_execution_summary"),
                     ("watchdog", "events_since"), ("selfreview", "_week_ago_iso"),
                     ("api", "api_digest_weekly")):
        assert beklenen in ciftler, f"{beklenen} listeden düştü — desen daraldı mı? {sorted(ciftler)}"
    assert len(ciftler) >= 15, f"üretim listesi beklenenden küçük ({len(ciftler)}) — körlük"


def test_7c_TARAMA_TABANI_asiliyor():
    """İkinci körlük alarmı: tarama `tests/` kökünü gerçekten buluyor mu? Taban 400 — bugün
    ölçülen 595 dosya (2026-09-21), geniş pay bırakıldı ki silinen testler çırçır üretmesin."""
    dosyalar = list(TESTLER.rglob("*.py"))
    assert len(dosyalar) >= 400, f"taranan dosya sayısı düşük ({len(dosyalar)}) — yanlış kök?"
    assert any(y.name == "test_takvim_bombasi_v526.py" for y in dosyalar), "öz-tarama yok"


# =================================================================================================
# 8 — CANLI HÜKÜM + YANLIŞ-POZİTİF BEDELİ (Rol-1 kararları 4 ve 5)
# =================================================================================================

def test_8a_GERCEK_tests_agacinda_BEYANSIZ_TAKVIM_BOMBASI_YOK():
    """TSK-210'un asıl hükmü. Bugün (2026-09-21) ÖLÇÜLDÜ: modül düzeyi `20\\d\\d` literali
    taşıyan 29 dosyanın HİÇBİRİ bugüne-göreli pencere tüketmiyor → sıfır ihlal. Bu sıfır BORÇ
    YOKLUĞUdur; dosya dosya hüküm tablosu devir raporundadır."""
    ciftler = _ciftler()
    ihlal = []
    for yol in sorted(TESTLER.rglob("*.py")):
        try:
            kaynak = yol.read_text(encoding="utf-8")
        except UnicodeDecodeError:  # sessiz-yutma: metin olmayan dosya bu yasanın konusu değil
            continue
        ihlal += [f"{yol.relative_to(REPO)} → {b}" for b in _takvim_bombalari(kaynak, ciftler)]
    assert not ihlal, (
        "BEYANSIZ takvim bombası: literal sabit bugüne-göreli bir pencereye karşı süzülüyor — "
        "yeşili takvim taşır, kod değil. Çözüm: sabiti üretim kapısının SAATİNDEN türet ya da "
        f"satıra `# {_BEYAN_ISARETI}: <≥{_BEYAN_ASGARI_GEREKCE} karakter gerekçe>` yaz. {ihlal}")


def test_8b_GEVSEK_KOLUN_BEDELI_OLCULDU_ve_SAYIYLA_DURUYOR():
    """BEDEL YASASI. Dar kol (karşılaştırma sınırı şartı) gürültüyü azaltır; ne KAYBETTİĞİ de
    sayılır. Gevşek kol ("dosyada `bugün - timedelta` geçiyor") bugün TEK dosyayı fazladan
    işaretler ve o işaret SAHTEDİR (gerekçe bu dosyanın başlığında, ölçüldü 2026-09-21).

    Küme BÜYÜRSE bu çivi öter: yeni bir sınır vakası doğmuştur ve Rol-1 hükmetmelidir — sessizce
    birikmesin diye sayıyla duruyor."""
    ciftler = _ciftler()
    fazladan = set()
    for yol in sorted(TESTLER.rglob("*.py")):
        kaynak = yol.read_text(encoding="utf-8")
        if not _literaller(kaynak) or _uretim_tuketimi(kaynak, ciftler):
            continue
        if _gevsek_pencere_tuketimi(kaynak) and not _kendi_pencere_tuketimi(kaynak):
            fazladan.add(yol.name)
    assert fazladan == {"test_geridolum_ileri_dolum_v483.py"}, (
        "gevşek/dar kol farkı değişti — yeni bir sınır vakası doğmuş olabilir; ÖLÇ ve Rol-1'e "
        f"taşı (bugünkü ölçüm 2026-09-21: tek dosya): {sorted(fazladan)}")


def test_8c_v483_YARDIMCISI_KIRMIZI_DEGIL_CANLI_OLCUM():
    """Rol-1 kararı 5'in CANLI karşılığı (sentetik değil): gerçek dosya taranır ve temiz çıkar.
    Sentetik çivi (`test_5b_…`) deseni ölçer, bu çivi GERÇEĞİ — ikisi ayrı sorudur."""
    yol = TESTLER / "test_geridolum_ileri_dolum_v483.py"
    assert yol.exists(), "kararı 5'in kanıt dosyası kayboldu — çivi ölçemez"
    kaynak = yol.read_text(encoding="utf-8")
    assert _literaller(kaynak), "dosya artık literal taşımıyor — bu çivi anlamını yitirdi"
    assert _takvim_bombalari(kaynak, _ciftler()) == []

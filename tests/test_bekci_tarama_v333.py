"""BEKÇİ TESPİT KATMANI — deterministik, LLM'siz, kendi kapsamını beyan eden — v331 (2026-08-30)

NEDEN BU ÇİVİLER VAR — brifingle gelen ÖLÇÜM (A1, 2026-08-30). Son 3 günün 1645 olayının 1580'i
`info`. Zinciri (`duvar=1` → warmup 40'ın 0'ını geçiriyor → `taze_hipotez` kalıcı 0 → sprint
yalnız 7 günlük zaman aşımıyla ateşliyor) bulmak ALTI elle ölçüm aldı ve halkalarının hiçbirini
hiçbir kod OKUMUYOR. `warmup_merdiven_kilitli.ardisik` canlıda 93'e çıkmış bir sayaçtır ve
OKUYUCUSU YOKTUR.

BU DOSYA CANLI DEFTERİ GÖREMEZ. Yerel `state/events.jsonl`in son 3 gününde 5 satır var ve
`sprint_cadence_skip` / `warmup_merdiven_kilitli` / `ardisik` yerelde HİÇ YOK. Fikstür canlının
ŞEKLİNİ (alan adları ve `sebep` biçimleri yayımcı KAYNAK KODUNDAN okunarak) taklit eder,
DEĞERLERİNİ değil. Yani bu çiviler kuralı sınar, canlı davranışı DEĞİL.

ASIL TUZAK: `sprint_cadence_skip` 3 günde 845 kez düştü ve "alarm" diye raporlanacaktı. 554'ü
`saat_dilimi_disinda` (NORMAL), 95'i `zaten_kosuyor` (NORMAL); yalnız 191 `tetik_yok(...)` kaydı
DURUM sinyaliydi. SIKLIK TEK BAŞINA ARIZA DEĞİLDİR ve ayrım YAPISAL olmak zorundadır (isim
listesi çürür).

DÜZELTME DALGASI (denetim, 2026-08-30) — üç yapısal bulgu ve bu dosyanın onlara karşı çivileri:
  1. KİMLİK ≠ DEĞER. `sebep` ölçümü İÇİNDE taşıyor (`tetik_yok(gun=4<7, …)`), yani `gun` her
     arttığında kalem adı değişiyor ve aynı takılı durum her gün sıfırdan bildiriliyordu.
  2. KERTİK ASİMETRİSİ. Tekdüze artan bir bayatlık sayacı grubu SESSİZCE iyi huylu sayıyordu —
     üstelik `ardisik` özel-durum olarak tanınırken, aynı semantikteki `gecen_gun` kör edici
     kalıyordu. Deponun kendi belgelediği `mesgul:canli_arama` vakası bu yüzden görünmezdi.
  3. `duran`ın `deger`i pencereye bağlı istatistik taşıyordu (`ornek`, `medyan`), yani her
     taramada değişiyor ve tekrar bastırma bu sınıf için hiç ateşlenemiyordu.


SÜRÜM NUMARASI v331 → v333 (2026-08-30): bu dosya v331 olarak yazıldı, ama aynı
pencerede uzaktan gelen `tests/test_spend_defter_duzeltmesi_v331.py` de v331 aldı.
vNNN bu depoda bir KİMLİKTİR — şerhlerde çapa olarak kullanılır — ve iki dosyanın aynı
numarayı taşıması o çapaları ikircikli yapar. Taşınan taraf DAHA AZ ÇAPALI olandır:
ötekine mühendislik günlüğü, üretilmiş RUNBOOK ve kendi betiği atıf yapıyordu (üç),
buna yalnız plan belgesi (bir). Numara sessizce kaymaz, kaydı burada durur.
"""

import datetime as dt
import importlib.util
import json
import pathlib
import re

import pytest

KOK = pathlib.Path(__file__).resolve().parent.parent
BETIK = KOK / "ops/bekci_tarama.py"

UTC = dt.timezone.utc
TABAN = dt.datetime(2026, 8, 27, 0, 0, 0, tzinfo=UTC)


def _yukle():
    """`ops/` betiğini `sys.modules`e KAYIT OLMADAN yükler (bu depodaki ops-testi kalıbı).

    KAYNAKTAN DERLENİR, `exec_module` İLE DEĞİL — ölçülmüş tuzak (2026-08-30, bu dosya
    yazılırken yaşandı). Depo kalıbı `spec.loader.exec_module(mod)`dur ve o, `SourceFileLoader`
    üzerinden `ops/__pycache__/*.pyc`i KULLANIR. CPython'ın `.pyc` geçerlilik kontrolü kaynağın
    (mtime-SANİYE, boyut) İKİLİSİNE bakar ve mtime SANİYE çözünürlüklüdür — yani tuzak "boyut
    aynı" ile değil, **"boyut aynı VE düzenleme ile geri yükleme AYNI SANİYE içinde oldu"** ile
    ateşlenir. Asıl tetikleyici HIZdır; boyut tek başına güvence DEĞİLDİR. Somut vaka: bir
    mutasyon turunda `DURAN_MIN_ORNEK = 5 → 2` yapıldı (boyut aynı), saniyeler içinde kaynak
    geri yüklendi, `diff` "özdeş" dedi — ve çivi hâlâ MUTASYONA UĞRAMIŞ modülü ölçtü.

    Bu, deponun en pahalı sınıfıdır: ölçüm aracı SESSİZCE YANLIŞ ŞEYİ ölçer ve sonuç doğru
    görünür. Kaynağı okuyup `compile` etmek bayt-kodu yolunu tamamen devre dışı bırakır.
    (Aynı `exec_module` kalıbı depodaki ~15 test dosyasında daha var — o genel kırılganlık
    BİLEREK bu görevin kapsamı dışında, ayrı bir kalem olarak devredildi.)"""
    assert BETIK.exists(), f"{BETIK} YOK — Görev 1 teslim edilmemiş"
    spec = importlib.util.spec_from_file_location("bekci_tarama", BETIK)
    mod = importlib.util.module_from_spec(spec)
    exec(compile(BETIK.read_text(encoding="utf-8"), str(BETIK), "exec"), mod.__dict__)
    return mod


def _ts(saat: float) -> str:
    """Taban zamandan `saat` saat sonrası — ISO-8601, UTC. Sentetik defterin TEK saat kaynağı.

    TAM SANİYEYE YUVARLANIR: `40 * 1.8` kayan noktada 72.00000000000001 verir ve mikrosaniyelik
    bir kalıntı SINIRDA bir çiviyi rastgele kırmızıya çevirirdi. Fikstürün kırılganlığı, ölçtüğü
    şeyin kırılganlığıyla karıştırılmamalı."""
    return (TABAN + dt.timedelta(seconds=round(saat * 3600))).isoformat()


def _satir(saat: float, olay: str, seviye: str = "info", **alanlar) -> str:
    return json.dumps({"ts": _ts(saat), "level": seviye, "event": olay, **alanlar},
                      ensure_ascii=False)


def _yaz(yol: pathlib.Path, satirlar, bozuk_bayt=False) -> pathlib.Path:
    """Defteri BAYT olarak yazar — geçersiz UTF-8 satırı ancak böyle üretilebilir."""
    govde = "\n".join(satirlar).encode("utf-8")
    if bozuk_bayt:
        govde += b'\n{"ts": "x", "event": "\xff\xfe bozuk"}'
    yol.write_bytes(govde + b"\n")
    return yol


def _defter_kur(tmp_path, ad="sentetik_events.jsonl") -> pathlib.Path:
    """SENTETİK DEFTER — canlının ŞEKLİNİ taklit eder, DEĞERLERİNİ değil.

    Yerel `state/events.jsonl` BİLEREK kullanılmaz: makineye bağlı bir çivi hiçbir şey
    kanıtlamaz, yerel kopya bayat, ve canlı deftere karşı eşik ayarlamak ölçümü ölçülene
    uydurmaktır.

    HER OLAY TEK BİR KAPIYI SINAR. Bu, düzeltme dalgasının dersi: ilk turda iki kapı komşu
    kapılar tarafından maskelendiği için ÇİVİSİZ kalmıştı. Pencere 0→72. saat; defterin son
    kaydı 72. saattedir ve `simdi` duvar saatinden değil DEFTERDEN gelir."""
    s: list[str] = []

    # (1) NABIZ — defterin saatini sona kadar diri tutar; DURAN'ın negatif kontrolü.
    for i in range(73):
        s.append(_satir(i, "nabiz", yuk=i % 3))

    # (2) İYİ HUYLU YÜKSEK FREKANS — canlı `saat_dilimi_disinda`nın analoğu. `taze_hipotez`
    #     donuk ama `gecen_gun` 0→5 sayıp SIFIRLANIYOR: sistem tur atıyor, yani dünya
    #     kondisyonun İÇİNDEN geçiyor. Sıklık sıralaması yapan bir araç bunu ilk sıraya koyardı.
    for i in range(41):
        s.append(_satir(i * 1.8, "pencere_kontrolu", sebep="saat_dilimi_disinda",
                        gecen_gun=i % 6, taze_hipotez=0, arama_bayat=False))

    # (3) KİMLİK ≠ DEĞER (bulgu 1) — sebep ölçümü İÇİNDE taşıyor ve `gun` 3→4→5 yürüyor.
    #     Üç farklı ham sebep, TEK kalem olmalı; ve `gecen_gun` KERTİK olduğu için (bulgu 2)
    #     grup elenmemeli.
    for i in range(12):
        g = 3 + i // 4
        s.append(_satir(61 + i, "sprint_cadence_skip",
                        sebep=f"tetik_yok(gun={g}<7, taze=0<5)",
                        gecen_gun=g, taze_hipotez=0,
                        # Bayrak yaşı TAZELENDİKÇE SIFIRLANIR: yükselir, düşer, yine yükselir.
                        # Tekdüze artsaydı KERTİK olurdu — saat değil, süre sayacı.
                        arama_bayrak_yasi_sa=[0.03, 0.14, 0.25, 0.08, 0.19, 0.30,
                                              0.05, 0.16, 0.27, 0.11, 0.22, 0.33][i]))

    # (4) KERTİK SINIFI (bulgu 2) — deponun kendi belgelediği `mesgul:canli_arama` vakasının
    #     şekli: sebep DEĞER GÖMMÜYOR, `gecen_gun` yürüyor ve HİÇ sıfırlanmıyor. İlk sürüm bunu
    #     "iyi huylu" sayıp eliyordu.
    for i in range(12):
        s.append(_satir(61 + i, "mesgul_dongu", sebep="canli_arama",
                        gecen_gun=4 + i // 4, taze_hipotez=0, yetim=True))

    # (5) KERTİK SIFIRLANIRSA İLERLEMEDİR — `kalan_gun` `[bekliyor]` grubunun İÇİNDE tekdüze
    #     artıyor ama OLAY düzeyinde `[yenilendi]` dalı onu sıfırlıyor. Sayaç sistemin malıdır,
    #     onu raporlayan dalın değil: sıfırlanma başka dalda görünür.
    for i in range(15):
        s.append(_satir(42 + i * 2, "kota_yenileme", sebep="bekliyor",
                        kalan_gun=1 + i // 5, kaynak="fmp"))
    for saat in (47, 57, 67):
        s.append(_satir(saat, "kota_yenileme", sebep="yenilendi", kalan_gun=0, kaynak="fmp"))

    # (6) SAYAÇ YOLU — `evaluated` 40/39 OYNAK; türetilmiş kural bu grubu elerdi.
    for i in range(10):
        s.append(_satir(63 + i, "warmup_merdiven_kilitli", carpan=1, duvar=1, budget=10,
                        k_max=2, cleared=0, evaluated=40 - (i % 2), ardisik=84 + i))

    # (7) SAYAÇ EŞİĞİ — `ardisik` son değeri 2, yani geçici bir kilit. "93 turdur takılı" gibi
    #     raporlanmamalı. (Bu kapının ilk turda ısıran çivisi YOKTU.)
    for i in range(8):
        s.append(_satir(65 + i, "gecici_kilit", ardisik=1 + i % 3, kapsam="x"))

    # (8) KÜÇÜK n'DE SAAT — 9 kayıt, yuvarlanmış bir yaş alanı bir kez tekrar ediyor (8 benzersiz
    #     / 9). Salt oran kuralı 0,889 < 0,9 der ve grubu OYNAK sayıp gerçek takılı durumu
    #     sessizce öldürürdü.
    for i, yas in enumerate([0.11, 0.11, 0.13, 0.12, 0.15, 0.14, 0.17, 0.16, 0.18]):
        s.append(_satir(62 + i, "kucuk_grup", sebep="bekleme", yas_sa=yas, durum="bekliyor"))

    # (8b) MANDAL — bir bayrak TAM BİR KEZ dönüp donuyor (false→true), kalan her şey donuk.
    #      `oynak` toleranssız bir AND olsaydı bu tek geçiş 191 kayıtlık bir sinyali elerdi
    #      (denetim: "tek seferlik bir alan geçişi grubu öldürüyor"). Dünya bir kez kıpırdadı ve
    #      DURDU — bu, takılılığı çürütmez.
    for i in range(10):
        s.append(_satir(62 + i, "mandal_olay", sebep="bayat", arama_bayat=i >= 4, durum="asili"))

    # (8c) SERBEST_AKAN_ORAN'ın DEĞERİ — 20 kayıt, 18 benzersiz (tam oranın üstünde).
    #      `kucuk_grup` `n-1` kolunu çiviler, bu grup ORAN kolunu: oran 0,9'un ÜSTÜNE çekilirse
    #      alan artık saat sayılmaz ve grup elenir. İlk turda eşiklerin yalnız VARLIĞI bağlıydı.
    for i, olcum in enumerate([1.0, 3.0, 2.0, 5.0, 4.0, 7.0, 6.0, 9.0, 8.0, 11.0,
                               10.0, 13.0, 12.0, 15.0, 14.0, 17.0, 16.0, 19.0, 1.0, 3.0]):
        s.append(_satir(52 + i, "oran_grubu", sebep="bekleme", olcum=olcum, durum="x"))

    # (9) DURAN — 2 saatlik ritim, 40. saatte susuyor. Sessizlik 32 sa.
    for i in range(21):
        s.append(_satir(i * 2, "gunluk_ozet", kapsam="portfoy", adet=i % 5))

    # (10) DURAN DEĞİL — 5. madde (kendi geçmişi). Ritim 4 sa, düzensizlik 36/4 = 9 (TAVANIN
    #      ALTINDA, yani hüküm kurulur), sessizlik 16 sa > 3×4 — ilk dört kapıyı GEÇER.
    #      Elenmesinin TEK sebebi kendi geçmişindeki 36 saatlik boşluktur.
    for saat in (0, 4, 8, 12, 48, 52, 56):
        s.append(_satir(saat, "seyrek_is", faz="bakim", adim=saat % 3))

    # (11) DÜZENLİLİK TAVANI — düzensizlik 24/2 = 12, tavanın (10) HEMEN ÜSTÜNDE. (10) ile
    #      birlikte tavanın DEĞERİNİ (9, 12) aralığına çivileler; ilk turda tavan [9, 36000)
    #      arasında herhangi bir yere konabiliyordu.
    for saat in (0, 2, 4, 6, 30, 32, 34, 36):
        s.append(_satir(saat, "bakim_penceresi", bolge="a", adim=saat % 3))

    # (12) DURAN_KAT — sessizlik (22 sa) kendi en uzun boşluğunu (10 sa) AŞIYOR ama olağan
    #      aralığın 3 katına (30 sa) ULAŞMIYOR. Bu kapının ilk turda ısıran çivisi YOKTU.
    for i in range(6):
        s.append(_satir(i * 10, "esik_bandi", tip="a", adim=i % 3))

    # (13) MEDYAN = 0 — altı kayıt AYNI SANİYEDE. İlk sürümün ASIL arızasının koruması buydu ve
    #      hiçbir fikstür onu tetiklemiyordu; gerçek defterde tek bir saniyede 120 kayıt var.
    for _ in range(6):
        s.append(_satir(30, "ayni_saniye", faz="toplu"))

    # (14) ÖLÇÜLEMEDİ — dört ayrı sınıf, hiçbiri SIFIR SAYILMAZ.
    s.append("{bu satir JSON degil")
    s.append(json.dumps({"ts": _ts(5), "level": "info", "detay": "olay alani yok"}))
    s.append(json.dumps({"ts": "dun", "level": "info", "event": "zamansiz_olay"}))

    # (15) ÖLÇÜLEMEDİ — sık tekrar eden ama HİÇ DURUM ALANI TAŞIMAYAN olay.
    for i in range(8):
        s.append(_satir(65 + i, "bos_nabiz"))

    # (16) GÖZLEM SÜRESİ — 30 kayıt 29 saniyede, sonra sessiz. Düzgün aralıklı patlama KUSURSUZ
    #      DÜZENLİDİR, yani tavan bunu göremez; eleyen şey KANIT kuralıdır.
    for i in range(30):
        s.append(_satir(20 + i / 3600.0, "patlama_dizisi", kod=500))

    # (17) DÜZENSİZ RİTİM, UZUN GÖZLEM — gözlem 40 sa (kanıt kuralı elemez) ama seri bir
    #      dakikalık patlama + 10'ar saatlik seyrek kayıt; medyan seriyi TEMSİL ETMEZ.
    for i in range(40):
        s.append(_satir(10 + i / 3600.0, "serpinti", adim=i % 4))
    for saat in (20, 30, 40, 50):
        s.append(_satir(saat, "serpinti", adim=saat % 4))

    return _yaz(tmp_path / ad, s, bozuk_bayt=True)


def _defter_uzun_kur(tmp_path) -> pathlib.Path:
    """52 GÜNLÜK DEFTER — GÜNLÜK ve HAFTALIK kadansın erişilebilirliğini sınar (bulgu 4).

    `gun=3` varsayılanında `DURAN_MIN_ORNEK=5`, kadansı ~18 saatten uzun HER İŞİ yapısal olarak
    hükümsüz kılıyordu: gecelik yedekleme, günlük özet, haftalık bakım — bir bekçinin EN DEĞERLİ
    "durdu" sinyalleri hiç erişilemezdi."""
    s: list[str] = []
    g = 24.0
    for i in range(209):                       # 6 saatte bir nabız, 52. güne kadar
        s.append(_satir(i * 6, "nabiz", yuk=i % 3))
    for d in range(40):                        # GÜNLÜK iş: 39. günde susuyor (13 gün sessiz)
        s.append(_satir(d * g + 2, "gecelik_yedek", hedef="db", adim=d % 4))
    for d in range(0, 29, 7):                  # HAFTALIK iş: 28. günde susuyor (24 gün sessiz)
        s.append(_satir(d * g + 5, "haftalik_bakim", kapsam="disk", adim=d % 3))
    for d in range(53):                        # DURAN DEĞİL: sona kadar gelen günlük iş
        s.append(_satir(d * g + 9, "gunluk_saglam", hedef="cache", adim=d % 4))
    return _yaz(tmp_path / "uzun_events.jsonl", s)


def _defter_canli_sekil_kur(tmp_path) -> pathlib.Path:
    """CANLININ GERÇEK ŞEKLİ — TEK olay adı, İKİ `sebep` dalı (dal denetimi H1, 2026-08-30).

    Bu fikstür `_defter_kur`dan AYRI durur ve gerekçesi ölçülmüş bir tuzaktır: `_defter_kur`
    tek bir canlı olayı iki sentetik ada bölüyor, böylece `_sifirlanan_alanlar`ın OLAY DÜZEYİNDE
    çalışması hiç sınanmıyordu. Burada iki dal AYNI `event` adını taşır — canlıda öyledir.

    ZAMAN YERLEŞİMİ HÜKMÜ TAŞIR:
      · İYİ HUYLU DAL (`saat_dilimi_disinda`) 0-57. günlerde, `gecen_gun` HAFTALIK sıfırlanır.
        Sıfırlamaların hepsi TAKILI penceresinin (son 3 gün) DIŞINDADIR — canlıda da öyledir,
        çünkü taban tetiği en sık 7 GÜNDE BİR ateşler.
      · HEDEF DAL (`tetik_yok(gun=N<7, taze=0<5)`) yalnız SON 3 GÜNDEDİR ve `gecen_gun` orada
        yürür, hiç sıfırlanmaz.
    Kanıt 60 günden toplanırsa hedef dal `oynak` diye elenir; kendi açıklığından toplanırsa
    KERTİK olur ve TAKILI kalır."""
    s: list[str] = []
    g = 24.0
    for i in range(62 * 4):                    # 6 saatte bir nabız: geniş pencere DOLU
        s.append(_satir(i * 6, "nabiz", yuk=i % 3))
    for gun in range(58):                      # İYİ HUYLU DAL — haftalık sıfırlama, dar pencerenin DIŞINDA
        s.append(_satir(gun * g + 1, "sprint_cadence_skip", sebep="saat_dilimi_disinda",
                        gecen_gun=gun % 7, taze_hipotez=0))
    for i in range(12):                        # HEDEF DAL — son 3 günde, kertik
        gd = 3 + i // 4
        s.append(_satir(59 * g + i * 2, "sprint_cadence_skip",
                        sebep=f"tetik_yok(gun={gd}<7, taze=0<5)",
                        gecen_gun=gd, taze_hipotez=0))
    return _yaz(tmp_path / "canli_sekil.jsonl", s)


@pytest.fixture
def mod():
    return _yukle()


@pytest.fixture
def sonuc(tmp_path, mod):
    return mod.tara(gun=3, defter=_defter_kur(tmp_path))


def _adlar(kalemler):
    return [k["ad"] for k in kalemler]


def _bul(kalemler, parca):
    return [k for k in kalemler if parca in k["ad"]]


def _neden(kalemler, neden):
    return [k for k in kalemler if k["kanit"].get("neden") == neden]


def _ayrinti(sonuc):
    """HÜKÜM KURULAMADI kalemlerinin TEKİL hâli.

    NEDEN AYRI BİR ANAHTAR (dal denetimi H2, 2026-08-30): teslim edilen `olculemedi` listesi
    artık `kadans_olculemedi` / `donuk_alan_yok` sınıflarını TEK bir toplu kaleme indiriyor —
    yoksa kararlı durumda operatöre her gün ~73 arıza-olmayan satır giderdi. Sınıflandırmanın
    KENDİSİ ölçülmeye devam etmeli, o yüzden tekil kalemler `olculemedi_ayrinti`de durur.

    BU YARDIMCI OLMADAN ÇİVİLER YANLIŞ SEBEPLE YEŞİL OLURDU: `_bul(sonuc["olculemedi"], "x")
    == []` iddiası, toplu kalem `x` adını hiç taşımadığı için TRİVİYAL doğrudur."""
    return sonuc["olculemedi_ayrinti"]


# ---- ARAYÜZ ------------------------------------------------------------------------------------

def test_ARAYUZ_UC_SINIFI_ve_ALTI_ALANI_TASIR(sonuc):
    """Görev 2 bu şekle bağlanır; şekil kayarsa brifing sessizce boş teslim eder.

    ADI DEĞİŞTİ ("BEŞ ALAN" → "ALTI ALAN", 2026-08-30): arayüze `kimlik` eklendi (dal denetimi
    M6 — bir olgu sınıf değiştirince bastırma anahtarı da değişiyor ve aynı olgu iki kez "YENİ"
    diye duyuruluyordu). Adı olduğu gibi bırakmak, bu turda ONARDIĞIMIZ sınıfın (beyan kendi
    dosyasına karşı bayat) çiviye vurmuş hâli olurdu."""
    assert set(sonuc) >= {"takili", "duran", "olculemedi", "olculemedi_ayrinti"}, sonuc.keys()
    for sinif in ("takili", "duran", "olculemedi", "olculemedi_ayrinti"):
        for kalem in sonuc[sinif]:
            assert set(kalem) >= {"ad", "deger", "ilk_gorulme", "son_gorulme", "kanit",
                                  "kimlik"}, f"{sinif} kaleminde arayüz alanı eksik: {kalem}"
            assert isinstance(kalem["kimlik"], str) and kalem["kimlik"], kalem


# ---- BULGU 1: KİMLİK ≠ DEĞER -------------------------------------------------------------------

def test_KALIP_OLCUMU_ADDAN_CIKARIR_ESIGI_BIRAKIR(mod):
    """Atama konumundaki sayı ÖLÇÜMDÜR ve kimlikten çıkar; karşılaştırmanın sağ tarafı EŞİKTİR
    ve KALIR — eşiğin değişmesi gerçekten başka bir durumdur."""
    assert mod._kalip("tetik_yok(gun=4<7, taze=0<5)") == "tetik_yok(gun=<N><7, taze=<N><5)"


def test_KALIP_OLCUM_OLMAYAN_SAYIYA_DOKUNMAZ(mod):
    """Bütün sayıları silen bir kural `http_502` ile `http_503`ü ya da `strategy_version 4` ile
    `3`ü birleştirirdi — bunlar AYRI durumlardır. Kural BİÇİMdir, liste değil."""
    for metin in ("http_502", "mesgul:canli_arama", "GERİLEME: strategy_version 4 → 3"):
        assert mod._kalip(metin) == metin, metin


def test_AYNI_DURUM_GUN_DEGISINCE_YENI_KALEM_DOGURMAZ(sonuc):
    """ASIL BULGU 1. Fikstürde `gun` 3→4→5 yürüyor, yani ÜÇ ham sebep var. Tek kalem olmalı;
    yoksa aynı takılı durum her gün sıfırdan bildirilir ve Global Constraint ("aynı takılı
    durumu her gün tekrar etme") tanımı gereği ihlal edilir."""
    kalem = _bul(sonuc["takili"], "tetik_yok")
    assert len(kalem) == 1, f"kimlik ölçümle birlikte kayıyor: {_adlar(sonuc['takili'])}"
    assert kalem[0]["ad"] == "sprint_cadence_skip[tetik_yok(gun=<N><7, taze=<N><5)]"
    assert kalem[0]["kanit"]["sebep_ham_benzersiz"] == 3, kalem[0]["kanit"]
    assert kalem[0]["kanit"]["tekrar"] == 12, "üç ham sebep TEK grupta toplanmalı"


def test_DEGER_GUN_YURURKEN_DEGISMEZ(sonuc):
    """`deger` tekrar bastırmanın anahtarıdır. Yürüyen `gun` ona GİRMEMELİ; girseydi ad
    sabitlense bile bastırma yine her gün bozulurdu."""
    kalem = _bul(sonuc["takili"], "tetik_yok")[0]
    assert kalem["deger"] == {"taze_hipotez": 0}, kalem["deger"]
    assert "gecen_gun" not in kalem["deger"] and "arama_bayrak_yasi_sa" not in kalem["deger"]
    assert kalem["kanit"]["sebep_ham_ornekleri"], "ham sebep KANITTA durmalı"


# ---- BULGU 2: KERTİK SINIFI --------------------------------------------------------------------

def test_KERTIK_SAYAC_TAKILI_DURUMU_ELEMEZ(tmp_path, mod):
    """ASIL BULGU 2 — ve BU ÇİVİ BİR KEZ YANLIŞ SEBEPLE YEŞİLDİ (dal denetimi H1/M2, 2026-08-30).

    ESKİ FİKSTÜR NEYİ KAÇIRIYORDU: tek canlı olay adını (`sprint_cadence_skip`) İKİ SENTETİK
    ADA bölüyordu (`mesgul_dongu` vs `pencere_kontrolu`). `_sifirlanan_alanlar` OLAY DÜZEYİNDE
    çalışır; iki ayrı adda iyi huylu dalın sıfırlaması takılı dalın kertik hakkına DOKUNAMAZ.
    Yani çivi, adını taşıdığı arızanın tam da ayırt edici özelliğini modellememişti ve arızanın
    İÇİNDEN yeşil geçiyordu. Bu, bu projede yanlış sebeple yeşil yakalanan DÖRDÜNCÜ çividir.

    CANLININ GERÇEK ŞEKLİ (yayımcı kaynağından ÇIKARILAN, bu makinede doğrulanamayan): TEK olay
    adı, İKİ `sebep` dalı. `sprint_cadence_skip.gecen_gun` haftalık taban tetiğiyle
    (`meridian/sprint.py`) DÜZENLİ SIFIRLANIR — ama sıfırlama, TAKILI hükmünün 3 günlük
    penceresinin DIŞINDA kalır. Kanıt 60 günlük en geniş pencereden toplanırsa alan kalıcı
    olarak "sıfırlanan" olur, KERTİK olamaz ve dalın var oluş gerekçesi `oynak` diye elenir.

    HÜKÜM KENDİ AÇIKLIĞININ KANITINA BAĞLIDIR — çivinin ölçtüğü kural budur."""
    yol = _defter_canli_sekil_kur(tmp_path)
    r = mod.tara(gun=3, duran_gun=60, defter=yol)
    kalem = _bul(r["takili"], "tetik_yok")
    assert len(kalem) == 1, (
        "kertik taşıyan takılı durum CANLI ŞEKİL altında elendi (kanıt penceresi hükmün "
        f"penceresinden geniş): {_adlar(r['takili'])} · elenen oynak: "
        f"{r['kapsam']['oynak_deger_ornek']}")
    assert "gecen_gun" in kalem[0]["kanit"]["kertik_alanlar"], kalem[0]["kanit"]
    assert kalem[0]["kanit"]["kertik_alanlar"]["gecen_gun"]["artis"] == 2


def test_KERTIK_HUKMU_KENDI_PENCERESININ_KANITINA_BAGLANIR(tmp_path, mod):
    """H1'in MEKANİK yarısı: iki açıklığın sıfırlama kümesi AYRIŞIYOR mu, ve hüküm HANGİSİNE
    bağlı? Fikstür bunu ölçmezse üstteki çivi yine "bir şekilde yeşil" olabilir.

    Dar pencere (hükmün kendi açıklığı) sıfırlama GÖRMEZ; geniş pencere ~8 sıfırlama görür.
    İkisi ayrışmıyorsa fikstür arızayı hiç kurmamıştır ve çivi kendini geçersiz sayar."""
    yol = _defter_canli_sekil_kur(tmp_path)
    simdi = mod._son_zaman(yol)
    genis, _, _, _, _ = mod._oku(yol, simdi - dt.timedelta(days=60), simdi)
    dar = [k for k in genis if k.an >= simdi - dt.timedelta(days=3)]
    s_genis = mod._sifirlanan_alanlar(genis)
    s_dar = mod._sifirlanan_alanlar(dar)
    assert "gecen_gun" in s_genis.get("sprint_cadence_skip", set()), (
        f"fikstür geniş pencerede sıfırlama KURMUYOR — çivi arızayı ölçmüyor: {s_genis}")
    assert "gecen_gun" not in s_dar.get("sprint_cadence_skip", set()), (
        f"fikstür dar pencereye de sıfırlama sızdırmış — iki açıklık ayrışmıyor: {s_dar}")


def test_KERTIK_DEGERE_KARISMAZ(sonuc):
    """Her tur artan sayaç `deger`e girerse bastırma her gün bozulur — bekçi, tam da önlemek
    için var olduğu günlük tekrarın kaynağı olur. Sayaç KANITA girer, DEĞERE değil."""
    kalem = _bul(sonuc["takili"], "mesgul_dongu")[0]
    assert kalem["deger"] == {"taze_hipotez": 0, "yetim": True}, kalem["deger"]


def test_SIFIRLANAN_SAYAC_ILERLEMEDIR_KERTIK_DEGILDIR(sonuc):
    """`kalan_gun` `[bekliyor]` grubunun İÇİNDE tekdüze artıyor ama OLAY düzeyinde `[yenilendi]`
    dalı onu sıfırlıyor: sistem tur atıyor. Sayaç SİSTEMİN malıdır, onu o an raporlayan dalın
    değil — sıfırlanmayı yalnız grubun içinde arasaydık ilerleme kanıtı komşu dalda kalırdı."""
    assert _bul(sonuc["takili"], "kota_yenileme") == [], _adlar(sonuc["takili"])
    assert "kota_yenileme[bekliyor]" in sonuc["kapsam"]["oynak_deger_ornek"], sonuc["kapsam"]


def test_IYI_HUYLU_TEKRAR_LISTEYE_GIRMEZ(sonuc):
    """ASIL TUZAK. Canlı `saat_dilimi_disinda`nın analoğu: `taze_hipotez` donuk ama `gecen_gun`
    sayıp SIFIRLANIYOR. Bu çivi düşerse araç bir SIKLIK SAYACIdır ve canlıda ilk raporu 554
    kayıtlık normal bir pencere kontrolünü alarma çevirir."""
    assert _bul(sonuc["takili"], "pencere_kontrolu") == [], _adlar(sonuc["takili"])


def test_IYI_HUYLU_AYIKLAMA_ADIYLA_GORUNUR(sonuc):
    """Görünmez bir eleme, elle yazılmış bir yoksayma listesinden daha tehlikelidir: okuyucu onu
    denetleyemez bile. Sayı görünürdür, DENETLENEBİLİR olan ADdır."""
    assert "pencere_kontrolu[saat_dilimi_disinda]" in sonuc["kapsam"]["oynak_deger_ornek"]
    assert sonuc["kapsam"]["oynak_deger_grup"] >= 2, sonuc["kapsam"]
    assert sonuc["kapsam"]["esik_alti_ornek"], "eşik altı elenenler de ADIYLA sayılmalı"


def test_IYI_HUYLU_AYIRIM_ADA_DEGIL_OLCUME_DAYANIR(tmp_path, mod):
    """Ayrım YAPISAL mı, gizli bir isim listesi mi? Aynı sebep adı, bu kez ölçümü DONUK verilir —
    araç onu TAKILI görmelidir. Ad değişmedi, ÖLÇÜM değişti; hüküm de değişmeli."""
    yol = _yaz(tmp_path / "e.jsonl", [
        _satir(i, "pencere_kontrolu", sebep="saat_dilimi_disinda", gecen_gun=4, taze_hipotez=0)
        for i in range(12)])
    assert _bul(mod.tara(gun=3, defter=yol)["takili"], "saat_dilimi_disinda"), (
        "sebep adına göre eleme yapılıyor — yapısal ayrım yok")


# ---- TAKILI: SINIF SINIRLARI -------------------------------------------------------------------

def test_TAKILI_TAM_LISTE(sonuc):
    """`duran` için tam liste iddiası vardı, `takili` için YOKTU — yani yeni bir yanlış pozitif
    ekleyen mutasyon sessizce geçerdi. Sıra da sözleşmedir: en bayat kalem başta."""
    assert _adlar(sonuc["takili"]) == [
        "warmup_merdiven_kilitli",
        "oran_grubu[bekleme]",
        "mesgul_dongu[canli_arama]",
        "sprint_cadence_skip[tetik_yok(gun=<N><7, taze=<N><5)]",
        "mandal_olay[bayat]",
        "kucuk_grup[bekleme]",
    ], _adlar(sonuc["takili"])


def test_TEK_SEFERLIK_GECIS_GRUBU_OLDURMEZ(sonuc):
    """`oynak` toleranssız bir AND olsaydı, 3 gün önce BİR KEZ dönüp donan bir bayrak
    (`arama_bayat` false→true) 191 kayıtlık asıl sinyali sessizce elerdi (denetim bulgusu).
    Mandal, dünyanın bir kez kıpırdayıp DURDUĞUNU söyler — takılılığı çürütmez, pekiştirir.
    Son değeri `deger`e girer: bayrak yeniden dönerse bu GERÇEKTEN yeni bir durumdur."""
    kalem = _bul(sonuc["takili"], "mandal_olay")
    assert len(kalem) == 1, f"tek geçiş grubu öldürdü: {_adlar(sonuc['takili'])}"
    assert kalem[0]["kanit"]["mandal_alanlar"] == {"arama_bayat": True}, kalem[0]["kanit"]
    # MANDALIN DEĞERİ `deger`E GİRMEZ (dal denetimi M4 — ÖLÇÜLDÜ, aşağıdaki
    # `test_MANDAL_DEGERI_DURUM_KIMLIGINE_GIRMEZ` çivisi sayıyı taşıyor): pencere içinde
    # KIPIRDAMIŞ bir alan, durağanlığın kimliği olamaz. Mandalın kendisi `kanit`te durur.
    assert kalem[0]["deger"] == {"durum": "asili"}, kalem[0]["deger"]


def test_SERBEST_AKAN_ORANIN_DEGERI_CIVILI(sonuc):
    """Eşiğin VARLIĞI değil DEĞERİ bağlanmalı. 20 kayıtta 18 benzersiz değer tam oranın
    üstündedir; oran 0,9'un üstüne çekilirse alan saat sayılmaz ve grup sessizce elenir."""
    kalem = _bul(sonuc["takili"], "oran_grubu")
    assert len(kalem) == 1 and kalem[0]["kanit"]["serbest_akan_alanlar"] == ["olcum"], (
        _adlar(sonuc["takili"]))


def test_TAKILI_SAAT_ALANI_HAREKET_SANILMAZ(sonuc):
    """`arama_bayrak_yasi_sa` her kayıtta farklıdır — bir SAATtir. Ayıklanmazsa grup "değeri
    değişiyor" diye elenir ve canlıdaki 191 kayıtlık ASIL sinyal görülmez. Ayıklama da gizli
    kalamaz: hangi alanın saat sayıldığı KANITTA yazılıdır."""
    kalem = _bul(sonuc["takili"], "tetik_yok")[0]
    assert kalem["kanit"]["serbest_akan_alanlar"] == ["arama_bayrak_yasi_sa"], kalem["kanit"]


def test_KUCUK_GRUPTA_SAAT_YINE_SAAT_SAYILIR(sonuc):
    """n=9'da 8 benzersiz değer salt oranla 0,889 < 0,9 kalır ve yuvarlanmış bir saat tek bir
    tekrar yaptığı için OYNAK sayılıp gerçek takılı grubu sessizce öldürürdü."""
    kalem = _bul(sonuc["takili"], "kucuk_grup")
    assert len(kalem) == 1, f"küçük n'de saat kaçtı: {_adlar(sonuc['takili'])}"
    assert kalem[0]["kanit"]["serbest_akan_alanlar"] == ["yas_sa"], kalem[0]["kanit"]


def test_TAKILI_SAYAC_YOLU_OYNAK_ALANA_RAGMEN_BULUR(sonuc):
    """`evaluated` 40/39 oynar; türetilmiş kural bu grubu elerdi. `ardisik` YAYIMCININ kendi
    kesintisizlik hükmüdür ve üstündür."""
    kalem = _bul(sonuc["takili"], "warmup_merdiven_kilitli")
    assert len(kalem) == 1 and kalem[0]["kanit"]["kaynak"] == "ardisik"
    assert kalem[0]["kanit"]["ardisik_son"] == 93, kalem[0]["kanit"]
    assert "ardisik" not in (kalem[0]["deger"] or {}), "sayaç DEĞERE giremez"


def test_SAYAC_ESIGI_GECICI_KILIDI_TAKILI_SAYMAZ(sonuc):
    """`ardisik` son değeri 2 olan geçici bir kilit "93 turdur takılı" gibi raporlanmamalı.
    (Bu kapının ilk turda ısıran çivisi YOKTU: eşiği kaldırmak hiçbir çiviyi kırmıyordu.)"""
    assert _bul(sonuc["takili"], "gecici_kilit") == [], _adlar(sonuc["takili"])
    assert "gecici_kilit" in sonuc["kapsam"]["esik_alti_ornek"], sonuc["kapsam"]


def test_ANLIK_PATLAMA_SUREGELEN_SAYILMAZ(sonuc):
    """Konu SÜREGELEN durumdur. Saniyeler içinde 30 kez tekrarlayan bir dizi donuktur ama
    süregelen değildir; süre tabanı olmadan sınıf "tekrarlayan her satır" olur."""
    assert _bul(sonuc["takili"], "patlama_dizisi") == [], _adlar(sonuc["takili"])


def test_TAKILI_KOR_NOKTALARINI_BEYAN_EDER(mod):
    """`_duran_tara` kör noktalarını sayarken `_takili_tara` TEK BİR TANE beyan etmiyordu. Tek
    taraflı dürüstlük dürüstlük değildir: sabit yüklü sağlıklı bir nabız bu kuralda YANLIŞ
    POZİTİFTİR ve okuyucu bunu araçtan öğrenmeli, denetimden değil."""
    d = mod._takili_tara.__doc__
    assert "KÖR NOKTA" in d, "takılı sınıfı kör nokta listesi taşımıyor"
    for jeton in ("NABIZ", "KERTİK RESIDÜELİ", "n=1"):
        assert jeton in d, f"beyan edilmemiş kör nokta: {jeton}"


# ---- BULGU 3 + DURAN ---------------------------------------------------------------------------

def test_DURAN_DEGERI_PENCEREYE_BAGLI_OLAMAZ(sonuc):
    """ASIL BULGU 3. `ornek` ve `medyan` pencere kaydıkça değişir; `deger`de dururlarsa "yalnız
    DEĞERİ değişince tekrar söyle" kuralı bu sınıf için TANIMI GEREĞİ her gün ateşlenir —
    `takili` tarafında özenle kaçınılan hatanın birebir aynısı."""
    kalem = _bul(sonuc["duran"], "gunluk_ozet")[0]
    assert kalem["deger"] == {"durum": "sessiz"}, kalem["deger"]
    assert kalem["kanit"]["ornek"] == 21 and kalem["kanit"]["olagan_aralik_saat"] == 2.0


def test_DURAN_DEGERI_PENCERE_KAYINCA_AYNI_KALIR(tmp_path, mod):
    """Bulgu 3'ün MEKANİK kanıtı: aynı durum iki farklı açıklıkta taranır. `kanit` değişebilir
    (ölçüm), `deger` DEĞİŞEMEZ (kimlik) — yoksa bastırma hiç ateşlenemez."""
    defter = _defter_kur(tmp_path)
    a = _bul(mod.tara(gun=3, duran_gun=60, defter=defter)["duran"], "gunluk_ozet")[0]
    b = _bul(mod.tara(gun=3, duran_gun=2, defter=defter)["duran"], "gunluk_ozet")
    assert a["deger"] == {"durum": "sessiz"}
    if b:                       # dar pencerede kalem hâlâ çıkıyorsa DEĞERİ aynı olmalı
        assert b[0]["deger"] == a["deger"], (a["deger"], b[0]["deger"])
        assert b[0]["kanit"]["ornek"] != a["kanit"]["ornek"], "fikstür açıklığı ayırmıyor"


def test_DURAN_SUSAN_OLAYI_BULUR(sonuc):
    """YOKLUK, VARLIKTAN ZOR GÖRÜLÜR. Ritim defterin kendi şeklinden ölçülür; hiçbir kural
    listesi bunu ÖNCEDEN bilemez. Tam liste iddiası: yeni bir yanlış pozitif sessizce geçemez."""
    assert _adlar(sonuc["duran"]) == ["gunluk_ozet"], _adlar(sonuc["duran"])
    kanit = sonuc["duran"][0]["kanit"]
    assert kanit["sessizlik_saat"] == pytest.approx(32.0, abs=0.01)
    assert kanit["medyan_aralik_saat"] == pytest.approx(2.0, abs=0.01)
    assert sonuc["duran"][0]["son_gorulme"] == _ts(40)


def test_DURAN_HALA_GELEN_OLAYI_SUCLAMAZ(sonuc):
    """Sona kadar tıkırdayan `nabiz` duran değildir — yoksa sınıf her taramada tüm defteri sayar."""
    assert _bul(sonuc["duran"], "nabiz") == [], _adlar(sonuc["duran"])


def test_DURAN_OLAYIN_KENDI_GECMISINE_GORE_OLCULUR(sonuc):
    """`seyrek_is` 16 saattir sessiz (olağanının 4 katı) ve düzensizliği 9 — ilk DÖRT kapıyı
    geçiyor. Kendi geçmişinde 36 saatlik bir boşluk olduğu için elenir; sabit bir eşik bunu her
    taramada bağırırdı."""
    assert _bul(sonuc["duran"], "seyrek_is") == [], _adlar(sonuc["duran"])
    assert _bul(_ayrinti(sonuc), "seyrek_is") == [], (
        "seyrek_is DÜZENLİ bir seridir (düzensizlik 9 < tavan); hüküm kurulabilmeliydi")


def test_DURAN_KAT_GURULTU_TABANINI_KORUR(sonuc):
    """`esik_bandi` sessizliği (22 sa) kendi en uzun boşluğunu (10 sa) AŞIYOR ama olağan
    aralığın 3 katına (30 sa) ulaşmıyor — bir tur gecikmiş olabilir, durmuş değil.
    (Bu kapının ilk turda ısıran çivisi YOKTU: `DURAN_KAT=0` yapmak 28 çiviyi de yeşil
    bırakıyordu.)"""
    assert _bul(sonuc["duran"], "esik_bandi") == [], _adlar(sonuc["duran"])
    assert _bul(_ayrinti(sonuc), "esik_bandi") == [], "hüküm kurulabilir bir seri"


def test_DURAN_PATLAMAYA_RITIM_DEMEZ(sonuc):
    """ÖLÇÜLMÜŞ ARIZA (yerel defter, 27.887 satır): ilk sürüm 64 kalem üretiyordu, çoğu patlama
    artefaktıydı ve "olağan aralık 0,0 saat" diye raporlanıyordu.

    İLK ONARIM YETMEDİ ve asıl ders budur: düzensizlik tavanı kondu, çivi HÂLÂ kırmızıydı —
    çünkü DÜZGÜN ARALIKLI bir patlama KUSURSUZ DÜZENLİDİR. Kusur ritimde değil KANITTAydı."""
    assert _bul(sonuc["duran"], "patlama_dizisi") == [], _adlar(sonuc["duran"])
    kalem = _bul(_ayrinti(sonuc), "patlama_dizisi")
    assert len(kalem) == 1 and kalem[0]["kanit"]["alt_neden"] == "gozlem_suresi_yetersiz"
    assert kalem[0]["kanit"]["duzensizlik"] == 1.0, (
        "düzgün aralıklı patlama KUSURSUZ DÜZENLİDİR — tavan bu sınıfı göremez")
    assert kalem[0]["deger"] is None


def test_DURAN_TEMSIL_ETMEYEN_MEDYANA_GUVENMEZ(sonuc):
    """`serpinti` 40 saat gözlendi (kanıt kuralı elemez) ama bir dakikalık patlama + seyrek
    kayıtlardan oluşuyor; medyan seriyi TEMSİL ETMEZ. Gerçek defterde bu madde devre dışı
    bırakılınca DURAN 1 yerine 21 kalem üretiyor (ölçüldü)."""
    assert _bul(sonuc["duran"], "serpinti") == [], _adlar(sonuc["duran"])
    kalem = _bul(_ayrinti(sonuc), "serpinti")
    assert len(kalem) == 1 and kalem[0]["kanit"]["alt_neden"] == "duzensiz_ritim"
    assert kalem[0]["kanit"]["duzensizlik"] > kalem[0]["kanit"]["tavan"]


def test_DUZENLILIK_TAVANI_DEGERI_CIVILI(sonuc):
    """Tavanın DEĞERİ bağlanmalı, yalnız varlığı değil: ilk turda [9, 36000) arasında herhangi
    bir sayı 28 çiviyi de yeşil bırakıyordu. `bakim_penceresi` (12) elenmeli, `seyrek_is` (9)
    HÜKÜM ALMALI — ikisi birlikte tavanı (9, 12] aralığına çiviler."""
    kalem = _bul(_ayrinti(sonuc), "bakim_penceresi")
    assert len(kalem) == 1 and kalem[0]["kanit"]["alt_neden"] == "duzensiz_ritim", (
        _adlar(_ayrinti(sonuc)))
    assert kalem[0]["kanit"]["duzensizlik"] == 12.0, kalem[0]["kanit"]
    assert _bul(sonuc["duran"], "bakim_penceresi") == []


def test_MEDYAN_SIFIR_DALI_TETIKLENIR(sonuc):
    """İlk sürümün ASIL arızasının koruması buydu ve HİÇBİR fikstür onu tetiklemiyordu — oysa
    gerçek defterde tek bir saniyede 120 kayıt var, yani dal canlıda sıkça ulaşılabilir."""
    kalem = _bul(_ayrinti(sonuc), "ayni_saniye")
    assert len(kalem) == 1, _adlar(_ayrinti(sonuc))
    assert kalem[0]["kanit"]["alt_neden"] == "medyan_aralik_sifir", kalem[0]["kanit"]
    assert kalem[0]["deger"] is None


def test_DURAN_ORNEK_KITLIGINDA_HUKUM_VERMEZ(tmp_path, mod):
    """4 örnek, 15 saatlik gözlem, 43 saatlik sessizlik: örnek sayısı DIŞINDAKİ her kapıyı
    geçer. Böylece çivi YALNIZ örnek kıtlığını sınar — komşu bir kapı maskelerse boşa döner."""
    yol = _yaz(tmp_path / "e.jsonl",
               [_satir(i * 5, "yeni_olay", faz="a") for i in range(4)]
               + [_satir(i, "nabiz", yuk=i % 3) for i in range(59)])
    r = mod.tara(gun=3, defter=yol)
    assert _bul(r["duran"], "yeni_olay") == [], r["duran"]
    assert "yeni_olay" in r["kapsam"]["duran_ornek_kitligi_ornek"], r["kapsam"]


# ---- BULGU 4: GÜNLÜK / HAFTALIK KADANS ERİŞİLEBİLİR --------------------------------------------

def test_DURMUS_GUNLUK_IS_URETIM_ACIKLIGINDA_YAKALANIR(tmp_path, mod):
    """GERİ ÇAĞIRMA ÇİVİSİ (bulgu 4+5). Altı kapının hepsi YALNIZ AZALTIR; "28k satırda 1 kalem"
    bir KESİNLİK argümanıdır ve kapıların yalnız YANLIŞ kalemleri sildiğine dair kanıt değildir.
    Bu çivi tersini sınar: bilinen-durmuş bir iş bütün kapılardan SAĞ ÇIKIYOR mu?

    Ve tam olarak ÜRETİM AÇIKLIĞINDA (`gun=3`) sorulur: gecelik yedekleme sessizce durursa bu
    bot tam da onun için vardır."""
    r = mod.tara(gun=3, defter=_defter_uzun_kur(tmp_path))
    assert "gecelik_yedek" in _adlar(r["duran"]), _adlar(r["duran"])
    assert "haftalik_bakim" in _adlar(r["duran"]), _adlar(r["duran"])
    assert "gunluk_saglam" not in _adlar(r["duran"]), "hâlâ gelen iş suçlanmamalı"


def test_DURAN_KENDI_PENCERESI_OLMASA_GUNLUK_IS_GORUNMEZ(tmp_path, mod):
    """Bulgu 4'ün mekanik kanıtı: DURAN `gun`u kullansaydı 3 günlük pencerede günlük bir işin
    yalnız 3 örneği olurdu ve kadansı ~18 saatten uzun HİÇBİR iş hüküm alamazdı."""
    r = mod.tara(gun=3, duran_gun=3, defter=_defter_uzun_kur(tmp_path))
    assert _bul(r["duran"], "gecelik_yedek") == [], (
        "dar pencerede günlük iş hüküm ALMAMALI — ayrı pencere bu yüzden var")


# ---- ÖLÇÜLEMEDİ --------------------------------------------------------------------------------

def test_OLCULEMEDI_BOZUK_SATIRI_YUTMAZ(sonuc):
    """Ayrıştırılamayan satır SESSİZCE KAYBOLURSA defterin bir parçası hiç ölçülmemiş olur ve
    "0 bulgu" sahte bir sıfırdır. UYDURMA YASAĞI: ölçülemeyen None + NEDEN."""
    kalem = _neden(sonuc["olculemedi"], "ayristirilamayan_satir")
    assert len(kalem) == 1, _adlar(sonuc["olculemedi"])
    assert kalem[0]["deger"] is None and kalem[0]["kanit"]["adet"] == 1
    assert kalem[0]["kanit"]["ilk_satir"] > 0, "hangi satır olduğu söylenmeli"


def test_OLCULEMEDI_BOZUK_BAYTI_DEGERE_CEVIRMEZ(sonuc):
    """`errors="replace"` bozuk baytı sessizce U+FFFD'ye çevirirdi: satır yine ayrışır ve YANLIŞ
    bir değer hiçbir kusur kaydı bırakmadan ölçüme girerdi. `except` içermediği için YASA-4
    çivisinin bile göremeyeceği bir sessiz yutma."""
    assert len(_neden(sonuc["olculemedi"], "bozuk_bayt")) == 1, _adlar(sonuc["olculemedi"])


def test_OLCULEMEDI_EKSIK_ALANLARI_AYRI_AYRI_SAYAR(sonuc):
    """Üç arıza tek kovaya atılırsa okuyucu hangisini onaracağını bilemez."""
    nedenler = {k["kanit"]["neden"] for k in sonuc["olculemedi"]}
    assert {"ayristirilamayan_satir", "olay_alani_yok", "zaman_damgasi_ayristirilamadi",
            "bozuk_bayt"} <= nedenler, nedenler


def test_OLCULEMEDI_DEGERSIZ_TEKRARI_DURAGAN_SAYMAZ(sonuc):
    """`bos_nabiz` 8 kez tekrar eder ve HİÇ durum alanı taşımaz. "Değeri değişmiyor" burada boş
    bir doğrudur — durağanlık UYDURULMUŞ olurdu."""
    assert _bul(sonuc["takili"], "bos_nabiz") == [], sonuc["takili"]
    kalem = _bul(_ayrinti(sonuc), "bos_nabiz")
    assert len(kalem) == 1 and kalem[0]["kanit"]["neden"] == "donuk_alan_yok"
    assert kalem[0]["deger"] is None


def test_OLCULEMEDI_ZAMANI_UYDURMAZ(sonuc):
    """Sahte bir zaman, bu aracın üretebileceği en tehlikeli şey olurdu — sıralama ve tekrar
    bastırma ona bakıyor."""
    kalem = _neden(sonuc["olculemedi"], "ayristirilamayan_satir")[0]
    assert kalem["ilk_gorulme"] is None and kalem["son_gorulme"] is None


# ---- BULGU 8: SAHTE SIFIR YOK ------------------------------------------------------------------

def test_ZAMAN_EKSENI_YOKSA_KAPSAM_SIFIR_UYDURMAZ(tmp_path, mod):
    """İlk sürüm altı `kapsam` alanını LİTERAL SIFIR döndürüyor, beyan da onları ölçülmüş bir
    cümle gibi basıyordu: *"0 grup: 0 eşik altı, 0 değeri oynadığı için elendi"*. Dosyanın kendi
    yasakladığı sahte sıfırın birebir örneği — üstelik EN ÇOK güvenilmesi gereken cümlede."""
    yol = _yaz(tmp_path / "e.jsonl",
               [json.dumps({"ts": "dun", "event": f"o{i}"}) for i in range(4)])
    r = mod.tara(gun=3, defter=yol)
    k = r["kapsam"]
    for alan in ("grup_sayisi", "olay_sayisi", "esik_alti_grup", "oynak_deger_grup",
                 "pencere_ici", "pencere_disi"):
        assert k[alan] is None, f"{alan} ölçülmedi ama {k[alan]!r} döndü"
    assert _neden(r["olculemedi"], "zaman_ekseni_yok"), r["olculemedi"]
    beyan = mod.kapsam_beyani(r)
    assert "0 eşik altı" not in beyan and "?" in beyan, beyan


def test_PENCERE_BOS_AMA_DEFTER_DOLU_SESSIZ_KALMAZ(tmp_path, mod):
    """Tek bir ileri tarihli damga `simdi`yi öne iter, pencere boşalır ve üç liste de boş döner.
    `defter_yok` için konan dürüstlük kapısı buraya da konmalı — yoksa dolu bir defter "temiz"
    diye okunur."""
    yol = _yaz(tmp_path / "e.jsonl",
               [_satir(i, "nabiz", yuk=i % 3) for i in range(10)]
               + [json.dumps({"ts": "2099-01-01T00:00:00+00:00", "event": "ileri_tarih"})])
    r = mod.tara(gun=3, defter=yol)
    assert r["takili"] == [] and r["duran"] == []
    assert _neden(r["olculemedi"], "pencere_bos"), _adlar(r["olculemedi"])


def test_DEFTER_YOKSA_SESSIZ_SIFIR_DONMEZ(tmp_path, mod):
    """Defter yoksa üç boş liste dönmek "arıza yok" diye okunur; varsayılan deftere sessizce
    düşmek de aynı yalanın başka hâlidir."""
    r = mod.tara(gun=3, defter=tmp_path / "olmayan.jsonl")
    assert r["takili"] == [] and r["duran"] == []
    assert [k["kanit"]["neden"] for k in r["olculemedi"]] == ["defter_yok"], r["olculemedi"]
    assert r["olculemedi"][0]["deger"] is None


# ---- KAPSAM / BAĞIMSIZLIK / CLI ----------------------------------------------------------------

def test_TARAMA_MAKINENIN_GERCEK_STATE_DIZININE_BAGLI_DEGIL(tmp_path, mod):
    """Çiviler makinenin canlı defterine bağlıysa hiçbir şey kanıtlamazlar; ayrıca canlı defter
    OPERATÖRE SUNULAN KANITTIR ve test onu ne okumak ne kirletmek zorundadır."""
    defter = _defter_kur(tmp_path)
    r = mod.tara(gun=3, defter=defter)
    assert r["kapsam"]["defter"] == str(defter)
    assert r["kapsam"]["okunan_satir"] == len(defter.read_bytes().splitlines())
    assert str(mod.VARSAYILAN_DEFTER) != str(defter)


def test_KAPSAM_HER_SONUCLA_BIRLIKTE_BEYAN_EDILIR(sonuc, mod):
    """`ops/olcum.py` fix round 4 dersi: araç TAMLIK İDDİA ETMEZ, kapsamını BEYAN EDER. İki
    pencere de beyanda görünmeli — okuyucu hangi sınıfın hangi açıklıkta ölçüldüğünü bilmeli."""
    k = sonuc["kapsam"]
    assert k["gun"] == 3 and k["duran_gun"] == mod.DURAN_VARSAYILAN_GUN
    assert k["okunan_satir"] > 0 and k["simdi_kaynagi"] == "defterin_son_kaydi"
    beyan = mod.kapsam_beyani(sonuc)
    assert "son 3 gün" in beyan and "BU KAPSAMIN DIŞI GÖRÜLMEDİ" in beyan, beyan
    assert f"son {mod.DURAN_VARSAYILAN_GUN} gün" in beyan, beyan


def test_KAPSAM_BEYANI_TARAMAYLA_BIRLIKTE_HAREKET_EDER(tmp_path, mod):
    """Beyan elle yazılmış olsaydı tarama değişince yerinde kalırdı ("mekanizma düzeltildi,
    İDDİA eski kaldı"). Beyan SONUÇTAN türetilir."""
    defter = _defter_kur(tmp_path)
    b1 = mod.kapsam_beyani(mod.tara(gun=3, defter=defter))
    b2 = mod.kapsam_beyani(mod.tara(gun=1, defter=defter))
    assert b1 != b2 and "son 1 gün" in b2


def test_PENCERE_DISI_KAYIT_SESSIZCE_DUSMEZ(tmp_path, mod):
    """Pencere dışı kayıtlar SAYILIR. Sayılmazsa "12 kayıt" cümlesi, defterde 3000 kayıt varken
    de aynı görünür ve okuyucu pencerenin ne kadarını kestiğini bilemez."""
    yol = _yaz(tmp_path / "e.jsonl",
               [_satir(-2000, "eski_olay", a=1)] + [_satir(i, "nabiz", yuk=i % 3)
                                                    for i in range(10)])
    assert mod.tara(gun=3, defter=yol)["kapsam"]["pencere_disi"] == 1


def test_BULGUSUZ_KOSUM_HATA_DEGILDIR(tmp_path, mod, capsys):
    """`main()` boş sonuçta 1 dönüyordu; bunu koşturacak bir birim sağlıklı HER günü BAŞARISIZ
    koşum olarak raporlardı — bekçinin kendisi gürültü kaynağı olurdu. 0 = ölçüm YAPILDI,
    2 = ölçüm YAPILAMADI."""
    yol = _yaz(tmp_path / "e.jsonl", [_satir(i, "nabiz", yuk=i % 3) for i in range(10)])
    assert mod.main(["--defter", str(yol)]) == 0
    assert mod.main(["--defter", str(tmp_path / "yok.jsonl")]) == 2
    assert "BULGU YOK" in capsys.readouterr().out


def test_GECERSIZ_PENCERE_SESSIZCE_BOS_DONMEZ(tmp_path, mod):
    """`--gun 0` sessizce boş bir pencere kurar ve "arıza yok" gibi okunurdu.

    `--defter` BİLEREK VERİLİR (dal denetimi L4): çivi eskiden yol vermiyordu ve canlı yerel
    deftere yalnız argparse ÖNCE düştüğü için dokunmuyordu. Kapı mutasyona uğrasaydı test
    operatöre sunulan defteri OKURDU — koruma, ölçtüğü kapının kendisine bağlıydı."""
    yol = _yaz(tmp_path / "e.jsonl", [_satir(i, "nabiz", yuk=i % 3) for i in range(10)])
    with pytest.raises(SystemExit):
        mod.main(["--gun", "0", "--defter", str(yol)])
    with pytest.raises(SystemExit):
        mod.main(["--duran-gun", "0", "--defter", str(yol)])


# ---- YASA / DÜRÜSTLÜK --------------------------------------------------------------------------

def _kod_govdesi() -> str:
    """Betiğin docstring'lerden ARINDIRILMIŞ kod gövdesi — gerekçe metinleri jeton taramasına
    girmemeli, yoksa "bu araç YAZMAZ" cümlesinin kendisi çiviyi kırardı."""
    kaynak = BETIK.read_text(encoding="utf-8")
    return "\n".join(s for s in kaynak.split('"""')[2::2])


def test_TESPIT_KATMANINDA_MODEL_YOK():
    """Global Constraint: tespit DETERMİNİSTİKTİR. Model listeyi üretirse bir arıza UYDURABİLİR;
    bu çivi, üretenin saf ölçüm olduğunu MEKANİK olarak mühürler."""
    kod = _kod_govdesi()
    for jeton in ("hermes", "llm", "gemini", "anthropic", "openai", "_agent_call", "notify"):
        assert jeton not in kod.lower(), f"tespit katmanına model/teslimat sızmış: {jeton}"


def test_TESPIT_KATMANI_HICBIR_BAYT_YAZMAZ():
    """"BU ARAÇ YAZMAZ" sözünün MEKANİK yarısı (dal denetimi L1, 2026-08-30).

    Başlık bunu bir SÖZ olarak veriyordu ve tek çivi (`test_TESPIT_KATMANINDA_MODEL_YOK`)
    jeton listesinde `obs`/`store`/yazma kipli `open`/`write` TAŞIMIYORDU. İleride eklenecek
    tek bir `obs.log` satırı, bu aracın OKUDUĞU defteri kirletir ve çivi yeşil kalırdı — yani
    ölçüm aracı kendi ölçtüğü kanıtı üretmeye başlar. BU OTURUMDA ÜÇ AJAN tam olarak bunu yaptı
    (canlı yerel deftere pytest DIŞINDA yazdılar), yani sınıf varsayımsal değil ÖLÇÜLMÜŞTÜR.

    OKUMA SERBEST, YAZMA YASAK: `defter.open("rb")` geçer, `open(..., "w")` geçmez. Kural
    biçimseldir (kip dizgesine bakar), isim listesi değil."""
    kod = _kod_govdesi()
    yasak = [
        (r"\bobs\s*\.", "olay defterine yazma (`obs.log`) — okuduğu kanıtı üretir"),
        (r"\bstore\s*\.", "durum deposu (`store.*`) — `state/` yazımı"),
        (r"\b(from|import)\s+meridian", "uygulama paketi ithali — yan etkileriyle birlikte yükler"),
        (r"\.write_text\s*\(|\.write_bytes\s*\(|\.writelines\s*\(|\.write\s*\(", "dosyaya yazma"),
        (r"\bjson\s*\.\s*dump\s*\(", "dosyaya JSON dökümü (`dumps` serbest, `dump` değil)"),
        (r"\.mkdir\s*\(|\.unlink\s*\(|\.rename\s*\(|\bos\s*\.\s*remove\b|\bshutil\s*\.",
         "dosya sistemi değişikliği"),
        # TEK SATIRLIK ÇAĞRI İÇİNE HAPSEDİLİR: sınırsız `[^)]*` ilk denemede `open("rb")`
        # satırından başlayıp AŞAĞIDAKİ satırlardaki bir `a` harfine kadar uzanıyor ve OKUMAYI
        # yazma sanıyordu — çivinin kendi ölçüm aracı yanlış şeyi ölçüyordu.
        (r"""open\s*\([^)\n]*["'][^"'\n]*[wax+][^"'\n]*["'][^)\n]*\)""", "yazma kipli `open`"),
    ]
    ihlal = [(kal, m.group(0)) for kal, m in
             ((kal, re.search(desen, kod)) for desen, kal in yasak) if m]
    assert not ihlal, f"tespit katmanı YAZIYOR — 'BU ARAÇ YAZMAZ' sözü mekanik değil: {ihlal}"
    assert 'defter.open("rb")' in kod, (
        "kural OKUMAYI da yasaklamış olabilir — çivi kendi hedefini kaybetmiş")


def test_SESSIZ_YUTMA_ISARETLENMIS():
    """YASA 4: her `except` ya bilgiyi kayda geçirir ya da ≥20 karakterlik GEREKÇEYLE işaretlenir."""
    satirlar = BETIK.read_text(encoding="utf-8").splitlines()
    for i, s in enumerate(satirlar):
        if not s.strip().startswith("except"):
            continue
        pencere = "\n".join(satirlar[max(0, i - 1):i + 3])
        assert "sessiz-yutma:" in pencere, f"işaretsiz except (satır {i + 1}): {s.strip()}"
        gerekce = pencere.split("sessiz-yutma:")[1].splitlines()[0].strip()
        assert len(gerekce) >= 20, f"gerekçe kısa (satır {i + 1}): {gerekce!r}"


def test_CIKARIM_GOZLEM_GIBI_SUNULMAZ():
    """Kalıcı docstring *"Canlı defterde birebir böyledir"* diyordu — brifingten gelen bir
    ÇIKARIM, canlıda koşturulmuş bir GÖZLEM gibi yazılmıştı. Bu makine canlı defteri GÖREMEZ
    (yerelde son 3 günde 5 satır; `sprint_cadence_skip`/`ardisik` hiç yok) ve dosya bunu
    KENDİSİ söylemeli — yalnız rapor değil."""
    kaynak = BETIK.read_text(encoding="utf-8")
    assert "Canlı defterde birebir böyledir" not in kaynak
    assert "DOĞRULANAMAYAN" in kaynak, "kanıt künyesi yok"
    assert "ÇIKARILAN" in kaynak and "ÖLÇÜLEN" in kaynak


# ---- DAL DENETİMİ (2026-08-30): H2 · M4 · M5 · M6 ----------------------------------------------

def _hukumsuz_defteri(tmp_path, ad="hukumsuz.jsonl", ekstra=()) -> pathlib.Path:
    """HÜKÜM KURULAMAYAN SINIFI KADEMELİ BÜYÜTEN defter — gerçek defterin ölçülen davranışı.

    20 olayın her biri 6 gün boyunca GÜNLÜK basılır, sonra susar; olay `n` `n`. günde başlar.
    Sessizlik gözlem ömrünün 3 katını aşınca (3b kanıt kapısı) olay DURAN'dan `kadans_olculemedi`
    sınıfına GÖÇER — olay `n` için tam olarak `n + 20`. günde. Yani `simdi` bir gün ilerledikçe
    sınıf BİR kalem büyür: gerçek yerel defterde 14 günde 65→73 yürüyen davranışın birebir aynısı
    (ve orada da düşen 7 DURAN'ın 7'si buraya göçtü).

    Fikstür bu yüzden hem H2'nin bandını hem M6'nın göçünü aynı şekilden besler."""
    s: list[str] = []
    for i in range(40 * 4):                                # 6 saatte bir nabız, 40 gün
        s.append(_satir(i * 6, "nabiz", yuk=i % 3))
    for n in range(20):
        for g in range(6):                                 # 6 kayıt, günlük ritim
            s.append(_satir((n + g) * 24, f"kadans_{n}", faz="a", adim=g % 3))
    s.extend(ekstra)
    return _yaz(tmp_path / ad, s)


def test_HUKUM_KURULAMADI_SINIFI_TOPLU_KALEME_INER(tmp_path, mod):
    """ÖLÇÜLMÜŞ ARIZA (dal denetimi H2, gerçek yerel defter 27.887 satır, üretim açıklığı):
    `0 TAKILI · 1 DURAN · 73 ÖLÇÜLEMEDİ`, 73'ünün 73'ü `kadans_olculemedi`. Bu sınıf
    (a) modelin SUSTURAMADIĞI, (b) `SESSIZ` hükmünü GEÇERSİZ kılan, (c) kalem başına bir satır
    üreten sınıftır — yani kararlı durumda günde ~10-16 arıza-olmayan satır, sonsuza dek.
    Görev 1'in "64 → 1" iyileştirmesi gürültüyü KALDIRMADI, bastırılamaz sınıfa TAŞIDI.

    İLKE KORUNUR: ölçülemeyen şey iyi huylu bir sıfır DEĞİLDİR ve model onu susturamaz. Değişen
    yalnız TESLİMAT BİÇİMİDİR — sınıf hâlâ `olculemedi`dedir, ama NEDEN BAŞINA TEK kalemdir.
    Tekil hüküm `olculemedi_ayrinti`de ölçülmeye devam eder."""
    r = mod.tara(gun=3, duran_gun=60, defter=_hukumsuz_defteri(tmp_path))
    toplu = [k for k in r["olculemedi"] if k["kanit"].get("toplu")]
    assert len(toplu) == 1, f"neden başına TEK toplu kalem beklenir: {_adlar(r['olculemedi'])}"
    assert toplu[0]["kanit"]["neden"] == "kadans_olculemedi"
    assert toplu[0]["kanit"]["olay_sayisi"] >= 9, toplu[0]["kanit"]
    # TEKİL kalemler KAYBOLMAZ — yalnız teslimat listesinden çıkar.
    ayrinti = [k for k in _ayrinti(r) if k["kanit"].get("neden") == "kadans_olculemedi"]
    assert len(ayrinti) == toplu[0]["kanit"]["olay_sayisi"], (len(ayrinti), toplu[0]["kanit"])
    # ÖLÇÜM ZİNCİRİ KIRIKLARI TOPLANMAZ: onlar "hüküm kurulamadı" değil, aracın kendi arızasıdır.
    assert toplu[0]["kanit"]["ornekler"], "toplu kalem hiçbir adı taşımıyor — denetlenemez"
    assert len(toplu[0]["kanit"]["ornekler"]) <= mod.ELENEN_ORNEK_TAVANI


def test_TOPLU_KALEMIN_DEGERI_GUNDEN_GUNE_KIPIRDAMAZ(tmp_path, mod):
    """H2'nin ASIL ŞARTI: kararlı bir ölçülemedi sınıfı SESSİZLİĞİ HER GÜN BOZAMAZ.

    ÖLÇÜLDÜ (gerçek yerel defter, `simdi` 14 gün geriye kaydırılarak, 2026-08-30): kalem sayısı
    14 günde 65→73 yürüdü ve TAM SAYI olarak 14 geçişin 6'sında değişti (%43). Yani `deger`e
    ham sayıyı koymak haftada ~3 "DEĞİŞTİ" bildirimi demekti. AYNI ÖLÇÜMDE ikilik büyüklük bandı
    (64-127) ve alt-neden kümesi 14 geçişin 0'ında değişti. `deger` bu yüzden BAND + ALT-NEDEN
    KÜMESİDİR; kesin sayı, sayım ve örnek adlar `kanit`e gider (mesajda görünür, kimlikte değil).

    Bandın BEDELİ BEYAN EDİLİR: sayı tam bir ikinin kuvvetine oturduğunda ±1'lik bir kıpırtı
    bandı atlatır. Ölçülen aralık (65-73) bugün sınırdan uzaktır — bu bir güvence değil, o
    günkü verinin şansıdır."""
    degerler, sayilar = set(), set()
    defter = _hukumsuz_defteri(tmp_path)
    for gun in range(30, 36):        # sınıf 10 → 15 kaleme büyür; ikilik bant (8-15) SABİT kalır
        an = TABAN + dt.timedelta(days=gun)
        r = mod.tara(gun=3, duran_gun=60, defter=defter, simdi=an)
        toplu = [k for k in r["olculemedi"] if k["kanit"].get("toplu")]
        assert toplu, f"gün {gun}: toplu kalem yok — fikstür sınıfı hiç kurmuyor"
        degerler.add(json.dumps(toplu[0]["deger"], sort_keys=True, ensure_ascii=False))
        sayilar.add(toplu[0]["kanit"]["olay_sayisi"])
    assert len(sayilar) >= 2, (
        f"fikstür sınıfı BÜYÜTMÜYOR — çivi bandı ölçmüyor, yanlış sebeple yeşil olur: {sayilar}")
    assert len(degerler) == 1, (
        f"kararlı ölçülemedi sınıfı `deger`i {len(degerler)} kez değiştirdi — her biri bir "
        f"günlük bildirimdir: {sorted(degerler)}")


def test_TOPLU_KALEM_GERCEK_DEGISIMI_YINE_DE_SOYLER(tmp_path, mod):
    """Bandın öteki yarısı: sınıf GERÇEKTEN değişince kimlik DEĞİŞMELİ, yoksa toplama bir
    susturma aracına dönerdi. YENİ BİR ÖLÇÜLEMEZLİK TÜRÜ (`medyan_aralik_sifir`) girmesi
    kimliği kıpırdatır — sayı aynı bandda kalsa bile."""
    taban = mod.tara(gun=3, duran_gun=60, defter=_hukumsuz_defteri(tmp_path, "a.jsonl"))
    # AYNI SANİYEDE altı kayıt → `medyan_aralik_sifir`: yeni bir ölçülemezlik TÜRÜ.
    ek = [_satir(24 * 30, "ayni_saniye", faz="toplu") for _ in range(6)]
    yeni = mod.tara(gun=3, duran_gun=60, defter=_hukumsuz_defteri(tmp_path, "b.jsonl", ekstra=ek))
    t0 = [k for k in taban["olculemedi"] if k["kanit"].get("toplu")][0]
    t1 = [k for k in yeni["olculemedi"] if k["kanit"].get("toplu")][0]
    assert "medyan_aralik_sifir" not in t0["deger"]["alt_nedenler"], t0["deger"]
    assert "medyan_aralik_sifir" in t1["deger"]["alt_nedenler"], t1["deger"]
    assert t0["deger"] != t1["deger"], "yeni bir ölçülemezlik türü kimliği kıpırdatmadı"


def test_MANDAL_DEGERI_DURUM_KIMLIGINE_GIRMEZ(tmp_path, mod):
    """ÖLÇÜLDÜ (dal denetimi M4; 25 günlük sentetik defter, günlük kaydırma, 2026-08-30).

    3 GÜNDE BİR DÖNEN İYİ HUYLU BİR BAYRAK, `deger`e girdiği için kalemi 21 günde **8 kez**
    andırıyordu (`YENİ` + 7 × `DEĞİŞTİ`); hedeflenen kadans 168 saatte bir, yani 21 günde 3.
    Kalem hiçbir gün elenmiyordu — yani arıza `gecis↔oynak` salınımı DEĞİL, `gecis`in DEĞERİNİN
    durağanlık kimliğine girmesiydi. Pencere içinde KIPIRDAMIŞ bir alan, durağanlığın kanıtı
    olamaz: `_imza`nın kendi doktrini budur ve `deger` ona uymuyordu.

    KAPATILMAYAN YARI, BEYAN EDİLİR: periyodu pencereden UZUN bir bayrak, bu açıklıkta gerçekten
    iki farklı durumdur ve yeniden anılması DOĞRUDUR — bulgu 2'nin ilkesi burada da geçerli."""
    s: list[str] = []
    for i in range(25 * 24):
        s.append(_satir(i, "bayrak_olayi", sebep="bekliyor",
                        bayrak=((i // 24) // 3) % 2 == 0, esik=90, mod="kapali"))
        s.append(_satir(i, "nabiz", yuk=i % 3))
    yol = _yaz(tmp_path / "salinim.jsonl", s)
    degerler, mandallar = [], 0
    for gun in range(4, 25):
        an = TABAN + dt.timedelta(days=gun)
        kalem = _bul(mod.tara(gun=3, defter=yol, simdi=an)["takili"], "bayrak_olayi")
        assert len(kalem) == 1, f"gün {gun}: grup elendi — fikstür `deger` kapısını ölçmüyor"
        degerler.append(json.dumps(kalem[0]["deger"], sort_keys=True))
        mandallar += "bayrak" in kalem[0]["kanit"]["mandal_alanlar"]
    assert mandallar >= 15, (
        f"fikstür bayrağı MANDAL olarak sınıflandırtmıyor ({mandallar}/21) — çivi hedefini "
        "kaybetmiş")
    assert len(set(degerler)) == 1, (
        f"iyi huylu bayrak `deger`i 21 günde {len(set(degerler))} hâle soktu — her hâl bir "
        f"'DEĞİŞTİ' bildirimidir: {sorted(set(degerler))}")


def test_KALEM_KIMLIGI_SINIF_GOCUNDE_KORUNUR(tmp_path, mod):
    """ÖLÇÜLDÜ (dal denetimi M6; gerçek yerel defter, `simdi` 14 gün kaydırılarak): DURAN'dan
    düşen 7 olayın 7'si de `kadans_olculemedi`ye GÖÇTÜ — yani göç bir uç durum değil, DURMUŞ bir
    işin bu defterdeki NORMAL son durağıdır (sessizlik gözlem ömrünün 3 katını aşınca 3b kapısı
    ateşler). İki kalem AYRI anahtar alsaydı aynı olgu iki kez "YENİ" diye duyurulurdu.

    `kimlik` TARAMA AİLESİNİ taşır (`kadans:` / `durum:`), sınıf adını değil: aynı olay adının
    aynı taramada hem `takili` hem `duran` görünebilmesi ÖLÇÜLMÜŞ bir vakadır ve o ayrım KALIR."""
    s = [_satir(g * 24, "gecelik_yedek", hedef="db", adim=g % 4) for g in range(10)]
    s += [_satir(i * 6, "nabiz", yuk=i % 3) for i in range(41 * 4)]
    yol = _yaz(tmp_path / "goc.jsonl", s)

    erken = mod.tara(gun=3, duran_gun=60, defter=yol, simdi=TABAN + dt.timedelta(days=14))
    d = _bul(erken["duran"], "gecelik_yedek")
    assert len(d) == 1, f"fikstür DURAN hükmünü kurmuyor: {_adlar(erken['duran'])}"

    gec = mod.tara(gun=3, duran_gun=60, defter=yol, simdi=TABAN + dt.timedelta(days=38))
    assert _bul(gec["duran"], "gecelik_yedek") == [], "fikstür göçü hiç tetiklemedi"
    o = [k for k in _ayrinti(gec) if k["kanit"].get("olay") == "gecelik_yedek"]
    assert len(o) == 1 and o[0]["kanit"]["neden"] == "kadans_olculemedi", (
        f"olay göç etmedi, kayboldu: {[k['ad'] for k in _ayrinti(gec)]}")
    assert d[0]["kimlik"] == o[0]["kimlik"] == "kadans:gecelik_yedek", (
        f"göçte kimlik değişti: {d[0]['kimlik']!r} → {o[0]['kimlik']!r} — aynı olgu iki kez "
        "'YENİ' diye duyurulur")


def test_DURAN_KOR_NOKTA_BEYANI_SABITTEN_TURETILIR(mod):
    """BEYAN, KENDİ DOSYASINA KARŞI BAYATTI (dal denetimi M1). `_duran_tara` kör-nokta listesi
    "45 günlük pencere (45 örnek / 6 örnek)" diyordu; sabit 60'tı ve AYNI DOSYA iki satır yukarıda
    45'in NEDEN reddedildiğini anlatıyordu. Hiçbir çivi bunu ölçmüyordu — yani beyan sessizce
    çürüyebiliyordu, üstelik aracın dürüstlük iddiasını taşıyan bölümde."""
    d = mod._duran_tara.__doc__
    assert f"{mod.DURAN_VARSAYILAN_GUN} günlük pencere" in d, (
        f"kör nokta beyanı pencereyi sabitten türetmiyor: {mod.DURAN_VARSAYILAN_GUN} günlük "
        "pencere geçmiyor")
    assert f"{mod.DURAN_VARSAYILAN_GUN} örnek" in d and f"{mod.DURAN_VARSAYILAN_GUN // 7} örnek" in d, (
        "günlük/haftalık örnek aritmetiği beyanda sabitle uyuşmuyor")
    assert "45 günlük pencere" not in d, "bayat pencere sayısı beyanda hâlâ duruyor"


# ---- İKİNCİ DALGA (2026-08-30): terfi · çözünürlük · örnekleme · kusur penceresi ---------------

def test_GECMISI_OLAN_KALEM_TOPLU_YIGINA_KARISMAZ(tmp_path, mod):
    """ÖLÇÜLMÜŞ GERİLEME (yeniden denetim, gerçek yerel defter, 20 gün): toplama, DURAN'dan
    `kadans_olculemedi`ye göçen 7 olayın 7'sini de teslimat listesinden TAMAMEN çıkardı.
    Toplamadan ÖNCE her biri 168 saatte bir ADIYLA "hâlâ sürüyor" satırı alıyordu; SONRA hiçbiri
    bir daha anılmadı. Yani sessizlik, tam da bu botun var oluş sebebi olan sınıfın körleşmesiyle
    satın alınmıştı — ve göç bir uç durum değil, durmuş bir işin NORMAL yoludur.

    KAYIT YENİ BİR MEKANİZMA DEĞİL: harness'in kendi damga defteri. Bir kalem DAHA ÖNCE ADIYLA
    bildirildiyse, tanımı gereği sistemin yinelemesini beklediği bir olaydır. YIĞINI TOPLA,
    GEÇMİŞİ OLANI TUT."""
    yol = _hukumsuz_defteri(tmp_path)
    an = TABAN + dt.timedelta(days=33)
    yigin = mod.tara(gun=3, duran_gun=60, defter=yol, simdi=an)
    hedef = [k for k in yigin["olculemedi_ayrinti"]
             if k["kanit"].get("neden") == "kadans_olculemedi"][0]["kimlik"]
    assert not any(k["kimlik"] == hedef for k in yigin["olculemedi"]), (
        "fikstür kalemi zaten tekil bırakmış — çivi terfiyi ölçmüyor")

    terfili = mod.tara(gun=3, duran_gun=60, defter=yol, simdi=an, bilinen={hedef})
    tekil = [k for k in terfili["olculemedi"] if k["kimlik"] == hedef]
    assert len(tekil) == 1, (
        f"geçmişi olan kalem yığında kayboldu: {[k['ad'] for k in terfili['olculemedi']]}")
    yigin_adet = [k for k in yigin["olculemedi"] if k["kanit"].get("toplu")][0]["kanit"]["olay_sayisi"]
    toplu = [k for k in terfili["olculemedi"] if k["kanit"].get("toplu")][0]
    assert toplu["kanit"]["olay_sayisi"] == yigin_adet - 1, (
        f"terfi eden kalem yığından DÜŞMEDİ ({toplu['kanit']['olay_sayisi']} vs {yigin_adet}) — "
        "aynı olgu iki yerde sayılıyor")
    assert terfili["kapsam"]["hukumsuz_adiyla"] == 1, terfili["kapsam"]


def test_BILINEN_YALNIZ_PAKETLEMEYI_ETKILER(tmp_path, mod):
    """`bilinen` tarayıcıya harness'in geçmişini taşır — bir ÖLÇÜM girdisi DEĞİL. Tespitin
    deterministik kalması bu botun mimari sözleşmesidir; kapı olmazsa "kim neyi bildirdi"
    sessizce NEYİN ARIZA SAYILDIĞINI değiştirmeye başlar."""
    yol = _hukumsuz_defteri(tmp_path)
    an = TABAN + dt.timedelta(days=33)
    a = mod.tara(gun=3, duran_gun=60, defter=yol, simdi=an)
    kimlikler = {k["kimlik"] for k in a["olculemedi_ayrinti"]}
    b = mod.tara(gun=3, duran_gun=60, defter=yol, simdi=an, bilinen=kimlikler)
    assert kimlikler, "fikstür hiç ölçülemedi kalemi üretmiyor"
    assert _adlar(a["takili"]) == _adlar(b["takili"])
    assert _adlar(a["duran"]) == _adlar(b["duran"])
    assert _adlar(a["olculemedi_ayrinti"]) == _adlar(b["olculemedi_ayrinti"])
    for alan in ("grup_sayisi", "olay_sayisi", "esik_alti_grup", "oynak_deger_grup",
                 "duran_ornek_kitligi", "pencere_ici", "duran_pencere_ici", "pencere_disi"):
        assert a["kapsam"][alan] == b["kapsam"][alan], alan
    assert not any(k["kanit"].get("toplu") for k in b["olculemedi"]), (
        "hepsi tanıdıkken yığın boş kalmalı")


def test_TOPLU_KIMLIK_ALT_SINIFIN_BUYUMESINI_GORUR(tmp_path, mod):
    """İKİNCİ KAÇIŞ KAPISI ÖLÜYDÜ (yeniden denetim). İlk hâl `alt_nedenler`i yalnız KÜME olarak
    taşıyordu; `kadans_olculemedi`nin alfabesi ÜÇ elemanlı ve KAPALIDIR ve üçü de 20 gündür
    mevcuttu — yani küme DOYMUŞ, kimlik tek bir ikilik bite inmişti. Ölçülen bedel:
    `gozlem_suresi_yetersiz` 1 → 8 (sekiz kat) yürüdü ve TEK BİR BİLDİRİM çıkmadı.
    Kimlik artık ALT-NEDEN BAŞINA bant taşır; ham sayıya dönmez (ham sayı 30 geçişin 10'unda
    değişiyordu, alt-neden bantları 3'ünde)."""
    az = [_satir(24 * 30, "ayni_saniye_a", faz="t") for _ in range(6)]
    cok = [_satir(24 * 30, f"ayni_saniye_{i}", faz="t") for i in range(9) for _ in range(6)]
    a = mod.tara(gun=3, duran_gun=60, defter=_hukumsuz_defteri(tmp_path, "a.jsonl", ekstra=az))
    b = mod.tara(gun=3, duran_gun=60, defter=_hukumsuz_defteri(tmp_path, "b.jsonl", ekstra=cok))
    ta = [k for k in a["olculemedi"] if k["kanit"].get("toplu")][0]
    tb = [k for k in b["olculemedi"] if k["kanit"].get("toplu")][0]
    assert ta["kanit"]["alt_neden_sayimi"]["medyan_aralik_sifir"] == 1
    assert tb["kanit"]["alt_neden_sayimi"]["medyan_aralik_sifir"] == 9
    assert set(ta["deger"]["alt_nedenler"]) == set(tb["deger"]["alt_nedenler"]), (
        "fikstür alt-neden KÜMESİNİ değiştirmiş — çivi doymuş alfabeyi ölçmüyor, kolay yoldan "
        "yeşil oluyor")
    assert ta["deger"] != tb["deger"], (
        f"bir alt sınıfın 1→9 büyümesi kimliği kıpırdatmadı: {ta['deger']} == {tb['deger']}")


def test_TOPLU_ORNEKLER_EN_SON_GORULENDEN_SECILIR(tmp_path, mod):
    """ÖLÇÜLDÜ (yeniden denetim): 73 addan ALFABETİK İLK 8 günler boyunca BİREBİR sabit kaldı ve
    sınıfa yeni göçen 6 durmuş işten 0'ını içeriyordu — yani örnekleme, yapısal olarak SINIFA
    YENİ GİRENİ gösteremiyordu. "En son ne zaman görüldü" durumsuz, deterministik ve bilgi
    taşıyan tek sıralamadır: sınıfa en yeni düşen, en son susan olaydır."""
    yeni = [_satir(24 * 31 + i / 3600.0, "zzz_en_son_susan", kod=1) for i in range(30)]
    r = mod.tara(gun=3, duran_gun=60, defter=_hukumsuz_defteri(tmp_path, ekstra=yeni),
                 simdi=TABAN + dt.timedelta(days=39))
    toplu = [k for k in r["olculemedi"] if k["kanit"].get("toplu")][0]
    ornek = toplu["kanit"]["ornekler"]
    assert toplu["kanit"]["olay_sayisi"] > len(ornek), "fikstür örnekleme yapmıyor"
    assert ornek[0] == "zzz_en_son_susan", (
        f"en son susan olay örneklerin başında değil: {ornek}")
    assert "zzz_en_son_susan" not in sorted(
        k["kanit"]["olay"] for k in _ayrinti(r)
        if k["kanit"].get("neden") == "kadans_olculemedi")[:len(ornek)], (
        "fikstür alfabetik seçimle de aynı sonucu veriyor — çivi ayrımı ölçmüyor")
    assert toplu["kanit"]["ornek_secimi"] == "en_son_gorulen"


def test_ZAMANI_COZULEN_KUSUR_PENCEREYE_BAGLANIR(tmp_path, mod):
    """H1'İN İKİNCİ ÖRNEĞİ (yeniden denetim). `_oku` kusurları pencere süzgecinden ÖNCE
    kaydediyordu, yani DOSYANIN TAMAMINDAN: 2024 tarihli bozuk bir satır, 3 ve 60 günlük
    pencerelerin İKİSİNİN DE dışındayken kalem olarak raporlanıyor, aynı mesajın kapsam satırı
    ise "bu pencerenin DIŞI görülmedi" diyordu. Kusur `kusur:` ailesindedir — bilerek toplanmaz
    ve 168 saatte bir yeniden anılır: tek bir eski bozuk satır, sonsuza dek haftalık bir satır
    ve her seferinde geçersiz bir `SESSIZ` demekti."""
    yol = _yaz(tmp_path / "e.jsonl",
               [_satir(i, "nabiz", yuk=i % 3) for i in range(10)]
               + [json.dumps({"ts": "2024-01-01T00:00:00+00:00", "level": "info",
                              "detay": "pencere DIŞINDA, olay alanı yok"})]
               + [json.dumps({"ts": _ts(5), "level": "info", "detay": "pencere İÇİNDE"})])
    r = mod.tara(gun=3, duran_gun=60, defter=yol)
    kalem = _neden(r["olculemedi"], "olay_alani_yok")
    assert len(kalem) == 1 and kalem[0]["kanit"]["adet"] == 1, (
        f"pencere dışı kusur hâlâ raporlanıyor (ya da içerideki de düştü): {kalem}")
    assert kalem[0]["kanit"]["pencere"] == "pencere_ici", kalem[0]["kanit"]
    assert r["kapsam"]["pencere_disi"] >= 1, r["kapsam"]


def test_ZAMANI_COZULEMEYEN_KUSUR_DOSYA_GENELI_OLDUGUNU_SOYLER(sonuc, mod):
    """ONARIMIN DÜRÜST YARISI: bazı kusurların zamanı TANIMI GEREĞİ çözülemez (bozuk bayt,
    ayrıştırılamayan satır, damgasız satır). Onları pencere dışı sayıp ATMAK, ölçülemeyeni sıfır
    saymak olurdu. Raporlanırlar — ama kalemin İÇİNDE ve kapsam beyanında pencereye
    BAĞLANAMADIKLARINI söylerler; "bu pencerenin DIŞI görülmedi" cümlesi onlar için YANLIŞTIR."""
    for neden in ("bozuk_bayt", "ayristirilamayan_satir", "zaman_damgasi_ayristirilamadi"):
        kalem = _neden(sonuc["olculemedi"], neden)
        assert len(kalem) == 1, f"{neden} kalemi kayboldu — ölçülemeyen sessizce atıldı"
        assert kalem[0]["kanit"]["pencere"] == "dosyanin_tamami", kalem[0]["kanit"]
    beyan = mod.kapsam_beyani(sonuc)
    assert "DOSYANIN TAMAMINDAN" in beyan and "İSTİSNA" in beyan, beyan
    assert sonuc["kapsam"]["kusur_dosya_geneli"] >= 3, sonuc["kapsam"]


def test_TAKILI_KIMLIGI_DURUM_ONEKINI_TASIR(sonuc):
    """`kadans:` ön eki çiviliydi, `durum:` DEĞİLDİ (yeniden denetim). İki aile ayrılmazsa aynı
    olay adının aynı taramada hem `takili` hem `duran` görünebilmesi — ÖLÇÜLMÜŞ bir vaka — tek
    anahtara çöker ve iki hükümden biri sessizce susturulur."""
    for kalem in sonuc["takili"]:
        assert kalem["kimlik"] == f"durum:{kalem['ad']}", kalem
    for kalem in sonuc["duran"]:
        assert kalem["kimlik"] == f"kadans:{kalem['ad']}", kalem
    assert sonuc["takili"] and sonuc["duran"], "fikstür iki aileyi de üretmiyor"


def test_BANT_KENARI_BEYANI_OLCUME_UYAR(mod):
    """BEYAN KENDİ ÖLÇÜMÜNE KARŞI BAYATLAMIŞTI (yeniden denetim). İlk hâl "ölçülen aralık (65-73)
    bugün sınırdan uzaktır" diyordu; prob 30 güne uzatılınca seri 63'te yedi, 64'te beş gün
    durdu — tam bant kenarında. Bu, bu dosyanın `_duran_tara`da kapattığı sınıfın aynısıdır."""
    d = mod._buyukluk_bandi.__doc__
    assert "sınırdan uzaktır" not in d, "yanlışlanmış beyan hâlâ duruyor"
    assert "63" in d and "64" in d, "ölçülen kenar değerleri beyanda yok"
    assert "KONUMUNA" in d, "bandın konum duyarlılığı beyan edilmemiş"


def test_YAZMA_YASAGININ_KACAKLARI_BEYAN_EDILMIS(mod):
    """BEYAN EDİLMİŞ SINIR, ÇİVİYE BAĞLI (yeniden denetim). Tek satıra hapsedilmiş desenin bedeli
    ölçüldü: çok satırlı `open(`, DEĞİŞKEN kipli `open(p, kip)` ve `os.open(p, os.O_WRONLY)`
    KAÇAR. Bu çivi kaçakları ÖLÇER — biri kapatılırsa KIRMIZI olur ve beyan güncellenmek zorunda
    kalır; "söz mekanik" iddiasının kapsamı böylece kendi kendine bayatlayamaz.
    PRATİK RİSK DÜŞÜK ve bu da ölçülmüş: bu oturumda gerçekleşen olay sınıfı (ajanların `obs.log`
    eklemesi) `\\bobs\\s*\\.` koluyla zaten kapalı."""
    desen = r"""open\s*\([^)\n]*["'][^"'\n]*[wax+][^"'\n]*["'][^)\n]*\)"""
    kacaklar = ['open(\n    p,\n    "w")', "open(p, kip)", "os.open(p, os.O_WRONLY)"]
    for k in kacaklar:
        assert not re.search(desen, k), (
            f"beyan edilmiş kaçak KAPANMIŞ: {k!r} — beyanı güncelle, çiviyi sessizce silme")
    for tutmali in ('open(p, "w")', 'yol.open("wb")', 'open(p, mode="a")'):
        assert re.search(desen, tutmali), f"desen gerilemiş: {tutmali!r}"

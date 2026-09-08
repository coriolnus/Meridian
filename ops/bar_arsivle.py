#!/usr/bin/env python3
# bar_arsivle.py — state/bars/<sembol>.csv canlı önbelleğini BÖLÜMLÜ, TİPLİ parquet arşivine
# çevirir (varsayılan: state/barlar/<SEMBOL>.parquet — sembol başına TEK dosya). CSV SİLİNMEZ,
# DEĞİŞMEZ: canlı okuma yolu (`load_bars`) aynen kalır — bu bir strangler ARŞİVİdİR, yer
# değiştirme değil. Varsayılan KURU: `--uygula` verilmedikçe hedefe 1 bayt yazılmaz. Arşivin
# OKUYUCUSU ops/bar_sorgu.py'dır (Yasa 6).
# Koşum: .venv/bin/python ops/bar_arsivle.py --kaynak-dizin state/bars
"""ops/bar_arsivle.py — GÜNLÜK BAR ÖNBELLEĞİNİN BÖLÜMLÜ PARQUET ARŞİVİ
(TSK-020 [UYGULA-3] Task 1, 2026-09-07; tasarım: docs/TASARIM-BARS-PARQUET-DUCKDB-2026-09-06.md
§3.1; bölümleme seçeneği 2026-09-07 S4 ölçümünden sonra eklendi).

NEDEN VAR. Bar deposu bugün sembol başına bir CSV'dir (yerel + A1'de 260 dosya / 60 MB, ölçüm
2026-09-06) ve BİÇİMİ TİPSİZDİR: her okumada tarih ayrıştırılır, `sanitize_bars` onarımı yeniden
koşar, sütun tipleri metinden çıkarılır. Ayrıca "2024-06-24'te hangi sembollerin barı vardı",
"dikiş nerede", "hangi seans eksik" sınıfı PIT/replay soruları sembol-dosyası biçiminde SQL'siz
cevaplanamaz. Arşiv bu iki bedeli kapatır; canlı yol DEĞİŞMEZ.

BÖLÜMLEME BİR SEÇENEKTİR, VARSAYILANI `sembol` — VE BUNU ÖLÇÜM BELİRLEDİ. İlk sürüm ay/sembol
bölümlüydü (`<hedef>/AAAA-AA/<SEMBOL>.parquet`) ve tasarım §4 arşiv için "15–20 MB" bekliyordu.
A1'deki ilk gerçek koşum (S4, 2026-09-07) bunu ÇÜRÜTTÜ: 260 sembol × ~273 ay ≈ 70 bin küçük
dosya; koşum 480 s tavanında bitmedi (RC=124) ve YARIM hâlde bile 134 MB tuttu — kaynağı olan
CSV 60 MB iken. Sebep: GÜNLÜK barda bir ay dosyası ~21 satırdır ve o boyutta parquet footer +
şema metadata + ZSTD blok yükü İÇERİKTEN büyüktür. Üç yerleşim vardır ve hepsi aynı şemayı
yazar:
    `--bolum sembol`  (VARSAYILAN)  `<hedef>/<SEMBOL>.parquet`        — sembolün TAMAMI
    `--bolum yil`                   `<hedef>/<YIL>/<SEMBOL>.parquet`
    `--bolum ay`                    `<hedef>/<AAAA-AA>/<SEMBOL>.parquet` — eski, UYUMLULUK
`--ay` süzgeci YALNIZ `--bolum ay` ile kabul edilir: sembol/yıl düzeninde dosya bir AYın değil
sembolün ya da yılın TAMAMIdır, yani ay süzgeci YARIM bir dosya yazıp manifeste "tam" diye
kaydederdi (rc 2).

MANİFEST YERLEŞİMİ BEYAN EDER VE KARIŞMAYI DURDURUR. Manifestin `bolum` alanı arşivin hangi
yerleşimde yazıldığını söyler; farklı bir `--bolum` ile koşulunca araç DURUR (rc 5) ve
`--temizle`yi söyler. Gerekçe ölçülebilir: iki yerleşim aynı dizinde karışırsa okuyucunun dosya
listesi aynı sembolü İKİ KEZ toplar ve `kapsam` sessizce satırı ikiye katlar. `--temizle`
yalnız MANİFESTTE KAYITLI dosyaları siler (yol, manifestin KENDİ `bolum` beyanından türetilir) —
manifeste kayıtlı olmayan yabancı bir dosyaya DOKUNMAZ, ve boşalan bölüm dizinini yalnız GERÇEKTEN
boşsa kaldırır. Kuru koşumda `--temizle` de bayt silmez: neyin silineceğini söyler.

BEDEL RAPORLANIR (bedel yasası). Her koşum sonunda stderr'e dosya SAYISI + arşivin toplam BAYTI
+ kaynak CSV baytı + oran düşer. Ölçülemeyen alan UYDURULMAZ: kuru koşumda yazılmamış dosyanın
boyutu yoktur ("ÖLÇÜLEMEDİ"), `--ay` süzgeci varken oranın paydası CSV'nin TAMAMI olduğu için
oran da ölçülemez.

ONARIM BİR KEZ, ARŞİVDE TEMİZ. Arşive giren çerçeve `meridian.adapters.data`nın `sanitize_bars`
BOĞAZINDAN geçmiş çerçevedir — ham CSV değil. Kopya YAZILMADI, İTHAL edildi: takvim kapısı,
düzeltilmemiş-satır karantinası ve OHLC kıstırması tek bir yerde yaşar; ikinci bir uygulama
sessizce ayrışırdı (tek-kaynak yasası).

BU ARAÇ `meridian`I İTHAL EDER — ve bu, kardeş `ops/olay_sikistir.py`den BİLİNÇLİ bir ayrımdır.
O araç `meridian`a hiç dokunmaz (obs'a ulaşamaz, sızıntı yapısal olarak imkânsız). Burada
`sanitize_bars` ZORUNLU olduğu için aynı garanti verilemez: `sanitize_bars` hayalet-seans ve
karantina olaylarını `meridian.obs`a yazabilir. SONUÇ, açıkça: bu aracın her koşumu CANLI
`state/events.jsonl`e satır düşürebilir. Testler bu yüzden `sandbox_state` altında ve SÜREÇ
İÇİNDE (`main([...])`) koşar; `subprocess` çağrısı yamayı görmez ve canlı deftere yazardı.

ŞEMA DONUK VE TİPLİDİR:
    date DATE · open/high/low/close DOUBLE · volume BIGINT · kaynak VARCHAR ·
    ayarlama_olcegi DOUBLE
CSV'de OLMAYAN SÜTUN UYDURULMAZ. Ölçüldü (2026-09-07, canlı önbellek başlığı):
`date,open,high,low,close,volume` — `kaynak` ve `ayarlama_olcegi` YOKTUR. İkisi de NULL yazılır
ve manifestte `eksik_sutunlar` altında SEMBOL BAŞINA beyan edilir. "0" ya da "1.0" yazmak
bilmediğimiz bir şeyi bilir gibi göstermek olurdu (uydurma yasağı); okuyucu (`ops/bar_sorgu.py`
`dikis` alt komutu) beyanı okur ve "ölçülemedi" der.

SEMBOL ADI DOSYA ADINDAN TÜRER VE DÖNÜŞÜM TERSİNMEZDİR. Önbellek adlandırması `_cache_path`in
kuralıdır (küçük harf + `.` → `-`), yani `BRK.B` diske `brk-b.csv` olarak yazılır ve geri
okunurken `BRK-B`den ayırt edilemez. Arşiv sembolü `BRK-B` yazar; bu bir ÖLÇÜM SINIRIDIR,
manifestin `sembol_kaynagi` alanında beyan edilir. `--sembol` süzgeci ters yönde çalışmaz:
verilen sembol AYNI `_cache_path` kuralıyla dosya adına çevrilir (kural KOPYALANMAZ, çağrılır).

DOĞRULAMA TAŞIYICIDIR (rc 5). Yazılan her parquet, YERİNE KONMADAN ÖNCE DuckDB ile geri okunur
ve dört ölçüm kıyaslanır: satır sayısı · min(date) · max(date) · sum(close). İlk üçü TAM
eşitlik arar. Dördüncüsü `math.isclose(rel_tol=1e-9)` ile kıyaslanır — ve bu tolerans bir
gevşetme değil, kayan nokta toplamasının SIRA BAĞIMLILIĞInın kabulüdür: aynı DOUBLE kümesinin
bellek-içi taraması ile parquet taraması farklı sırada toplanabilir ve son bit oynayabilir.
Taşıyıcı ölçüm SATIR SAYISIDIR; toplam yalnız "aynı satırlar mı" sorusunun ikinci kanıtıdır.
Doğrulama düşerse geçici dosya SİLİNİR, hedefe DOKUNULMAZ.

MANİFEST HEPSİ-YA-HİÇ YAZILIR. Herhangi bir (sembol, ay) doğrulamadan düşerse manifest HİÇ
yazılmaz ve rc 5 döner. BEDEL AÇIKÇA: o koşumda başarıyla yazılmış parquet dosyaları diskte
kalır ama manifestte kaydı olmaz — yani bir sonraki koşum onları "yeni" sayıp yeniden yazar.
Bu bilinçli: yarım bir manifest, taşımadığı bir "doğrulandı" iddiası taşırdı; yeniden yazmanın
bedeli ise yalnız CPU'dur (çıktı içerik olarak aynıdır).

IDEMPOTENCY KIYASI = MANİFEST KAYDI + KAYNAK İÇERİK HASH'İ + DOSYANIN SHA256'SI. Bir (sembol,
parça) ancak şunların HEPSİ doğruysa "atlandı" olur: hedef dosya var · manifestte kaydı var ·
kayıttaki `kaynak_hash` BUGÜNKÜ CSV'nin sanitize edilmiş İÇERİĞİNİN (TÜM sütunlar, satır satır)
hash'iyle aynı · kayıttaki sha256 diskteki dosyanın sha256'sı. Son koşul dosyanın elle
değiştirilmediğini, öncekiler KAYNAĞIN değişmediğini ölçer. KIYAS İÇERİK HASH'İNE DAYANIR, yalnız
dört ÖZET istatistiğe (satır/ilk/son/kapanış toplamı) DEĞİL (bulgu C3, 2026-09-08): toplamı
KORUYAN bir OHLCV revizyonu (ör. bir gün open +1.0, başka gün -1.0) eski dört-özet kıyasını
YANILTIRDI — satır sayısı, ilk/son gün ve kapanış toplamı DEĞİŞMEDEN kalırdı ve arşiv düzeltilmiş
veriyi asla almazdı; içerik hash'i HER hücre değişikliğini yakalar. MANİFEST KAYDI `kaynak_hash` TAŞIR, `kapanis_toplami` TAŞIMAZ: ikincisinin
manifestteki okuyucusu kalmadı ve okunmayan artefakt üretilmemişten farksızdır (Yasa 6, bulgu
K5c 2026-09-08); doğrulamadaki kıyası AYNEN sürüyor. BİLİNEN BEDEL: parquet
baytları DuckDB sürümüyle değişebilir, yani sürüm yükseltmesinden sonraki ilk koşum her ayı
YENİDEN YAZAR.

GÖÇ BEDELİ, BEYANLI (bedel yasası — bulgu K5b, 2026-09-08). `kaynak_hash` alanı OLMAYAN bir
manifest kaydı (sürüm 2026-09-07.2 ve öncesi) kıyası GEÇEMEZ, yani sözleşme değişikliğinden
sonraki İLK `--uygula` arşivin TAMAMINI bir kez yeniden yazar — A1'de ölçüldü (2026-09-07
manifesti, 260 sembol, ~23 MB) ve manifest hepsi-ya-hiç yazıldığı için o turda TEK bir doğrulama
farkı bütün turu düşürür. Koşum bunu SESSİZ yapmaz: `kaynak_hash`siz kayıtların sayısı ve
gerekçesi ("eski sözleşme … yeniden yazılıyor") koşum sonunda stderr'e düşer, yoksa 260 satırlık
"yazıldı" listesi arıza gibi okunurdu. İKİNCİ BEDEL: hash `pandas.util.hash_pandas_object`in
BAYT BİÇİMİNE bağlıdır (yerelde pandas 3.0.3, 2026-09-08), yani bir pandas yükseltmesi
aynı tam yeniden yazımı bir kez daha tetikler — DuckDB sürüm bedeliyle aynı sınıf, aynı kabul. Kardeş `ops/olay_sikistir.py` bu yüzden bayt kıyasından kaçınır — orada yanlış bir
KIRMIZI doğardı; burada sonuç yalnız bir yeniden yazımdır ve arşiv değişmez.

WORKER KOŞARKEN GÜVENLİDİR: CSV'ler yalnız OKUNUR, hedef AYRI bir dizindir (`state/barlar/`) ve
her dosya önce aynı dizinde geçici bir ada yazılıp `os.replace` ile yerine konur — okuyucu ya
eski dosyayı ya yeni dosyayı görür, yarısını asla.

KULLANIM:
    python ops/bar_arsivle.py                          # KURU: ne yapacağını söyler, yazmaz
    python ops/bar_arsivle.py --uygula                 # arşivi yaz (bölüm: sembol)
    python ops/bar_arsivle.py --bolum yil --uygula
    python ops/bar_arsivle.py --bolum ay --sembol AAPL --ay 2024-01 --uygula
    python ops/bar_arsivle.py --bolum sembol --temizle --uygula   # eski düzeni sil, yeniden yaz
    python ops/bar_arsivle.py --kaynak-dizin /yol/bars --hedef /yol/barlar --uygula
    python ops/bar_arsivle.py --uygula --zorla         # manifest eşleşse bile yeniden yaz
    python ops/bar_arsivle.py --json                   # satır-JSON çıktı

ÇIKIŞ KODU: 0 = koştu (yazıldı/yazılacak/atlandı) · 1 = GİRDİ YOK (kaynak dizin/CSV/sembol/ay
           bulunamadı) · 2 = kullanım hatası · 4 = DuckDB'de düştü · 5 = HEDEFE DOKUNULMADI:
           ya DOĞRULAMA FARKI (parquet geri okunduğunda ölçüm tutmadı, manifest yazılmadı) ya da
           BÖLÜM UYUŞMAZLIĞI (manifest başka bir yerleşim beyan ediyor; önce `--temizle`).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import os
import pathlib
import re
import sys
import tempfile

import duckdb
import pandas as pd

# ops/ altından doğrudan koşulduğunda `meridian` paketi ve kardeş `ops` modülleri bulunabilsin.
# Kardeş betiklerin (bekci_brifingi, karne_brifingi, sef_brifingi…) hepsi bu satırı taşır.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from meridian import config as _config                       # noqa: E402
from meridian.adapters import data as _data                  # noqa: E402
from meridian.adapters.data import sanitize_bars             # noqa: E402
# TEK ATOMİK YAZIM YOLU — `store` başlığındaki B1 boğazı (tmp → write → fsync → replace →
# dizin fsync). İkinci bir uygulama yazmak, sertleşmenin (fsync) yalnız bir kopyada kalması
# demekti; manifest de bir DEFTERDİR ve yarım yazılmış bir defter "doğrulandı" yalanı söyler.
from meridian.store import _atomic_write as _atomik_yaz      # noqa: E402
from ops import olay_sorgu                                   # noqa: E402

#: Araç sürümü manifestteki üretim damgasında durur: arşivi kimin, hangi sözleşmeyle yazdığı
#: dosyanın kendisinden okunabilsin (şema değişirse bu artar ve eski arşiv AYIRT EDİLEBİLİR).
#: 2026-09-07.2 — bölümleme seçeneği + manifestin `bolum` beyanı (sürüm 2026-09-07.1 YALNIZ
#: ay/sembol yerleşimi yazardı ve manifestinde `bolum` alanı YOKTU).
#: 2026-09-08.1 — kayıtlara `kaynak_hash` GİRDİ, `kapanis_toplami` ÇIKTI (bulgu K5, 2026-09-08).
#: Aynı sınıf değişiklik: idempotency kıyasının sözleşmesi değişti, yani bir kaydın HANGİ
#: kıyasla doğrulandığı ancak bu damgadan ayırt edilebilir. Göç bedeli modül başlığında.
ARAC_SURUMU = "2026-09-08.1"
ARAC_ADI = "ops/bar_arsivle.py"

MANIFEST_ADI = "manifest.json"
VARSAYILAN_HEDEF_ALT = "barlar"

AY_DESENI = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

#: YERLEŞİMLER — gerekçe ve A1 ölçümü modül başlığında ("BÖLÜMLEME BİR SEÇENEKTİR").
BOLUM_SEMBOL = "sembol"
BOLUM_YIL = "yil"
BOLUM_AY = "ay"
BOLUMLER = (BOLUM_SEMBOL, BOLUM_YIL, BOLUM_AY)
VARSAYILAN_BOLUM = BOLUM_SEMBOL
#: Manifestte `bolum` alanı YOKSA yerleşim `ay`dır — bu bir tahmin değil ÖLÇÜM: alanı yazmayan
#: TEK sürüm 2026-09-07.1'dir ve o sürüm yalnız ay/sembol yerleşimi üretebiliyordu.
BOLUMSUZ_MANIFEST_DUZENI = BOLUM_AY

#: ARŞİV ŞEMASI — sıra da tiptir: okuyucu sütun ADINA bakar ama `DESCRIBE` kıyası SIRAYI da
#: ölçer ve şemanın sessizce yeniden sıralanması bir değişikliktir, kaza değil.
SUTUNLAR = ("date", "open", "high", "low", "close", "volume", "kaynak", "ayarlama_olcegi")
#: Ölçüldü (2026-09-07, canlı `state/bars/*.csv` başlığı): CSV bu altısını taşır.
CSV_SUTUNLARI = ("date", "open", "high", "low", "close", "volume")
#: SQL tipleri — arşiv tipli olsun diye her sütun AÇIKÇA cast edilir. `volume` CSV'de kayan
#: noktadır (`2024993600.0`) ve BIGINT'e çevrilir: hisse adedi tam sayıdır, kesir bilgi değil
#: biçim artığıdır.
SUTUN_TIPLERI = {"date": "DATE", "open": "DOUBLE", "high": "DOUBLE", "low": "DOUBLE",
                 "close": "DOUBLE", "volume": "BIGINT", "kaynak": "VARCHAR",
                 "ayarlama_olcegi": "DOUBLE"}

DURUM_YAZILDI = "yazıldı"
DURUM_YAZILACAK = "yazılacak"      # yalnız KURU koşum
DURUM_ATLANDI = "atlandı"
DURUM_FARK = "FARK"

#: `parca` sütunu BÖLÜM ANAHTARIdır: `ay` yerleşiminde AAAA-AA, `yil`de AAAA, `sembol`de YOKTUR
#: (None) — çünkü orada dosya sembolün kendisidir ve sembolü ikinci bir sütuna yazmak aynı
#: gerçeğin kopyası olurdu.
BASLIKLAR = ["sembol", "parca", "satir", "bayt", "durum", "dosya"]

#: `sum(close)` kıyasının toleransı — gerekçe modül başlığında ("DOĞRULAMA TAŞIYICIDIR").
KAPANIS_REL_TOL = 1e-9

#: `_olc`un ürettiği ama MANİFESTE YAZILMAYAN ölçümler (Yasa 6 — okuyucusuz yazım yok).
#: `kapanis_toplami` yazım-anı doğrulamasının (`_dogrula`) taşıyıcı ikinci kanıtıdır ve orada
#: BELLEK İÇİNDE okunur; idempotency kıyası `kaynak_hash` + dosya `sha256`ına geçtikten sonra
#: (bulgu C3, 2026-09-08) manifestteki kopyasının okuyucusu KALMADI — ölçüldü (depo geneli grep,
#: 2026-09-08: alan yalnız bu dosyada üretilip yine bu dosyada kıyaslanıyor; manifestten okuyan
#: kod ya da çivi YOK). Her koşum her sembol için okunmayan bir alan yazıyordu; alan DEFTERDEN
#: düşürüldü, DOĞRULAMADAN değil (bulgu K5c, 2026-09-08).
MANIFEST_DISI_OLCUMLER = ("kapanis_toplami",)


# ---------------------------------------------------------------------------------------------
# Kaynak tarafı
# ---------------------------------------------------------------------------------------------

def sembol_dosya_adi(sembol: str) -> str:
    """Sembolün önbellek dosya adı — kural `meridian.adapters.data`nın `_cache_path`indedir ve
    KOPYALANMAZ, ÇAĞRILIR. İki yerde yazılsaydı `BRK.B` bir tarafta `brk-b.csv`, diğerinde
    `brk.b.csv` olurdu ve süzgeç sessizce hiçbir şey bulamazdı."""
    return _data._cache_path(sembol).name


def sembol_adi(dosya: pathlib.Path) -> str:
    """Dosya adından sembol etiketi (`aapl.csv` → `AAPL`). TERSİNMEZ: `_cache_path` `.`ı `-`
    yaptığı için `brk-b.csv` hem `BRK.B` hem `BRK-B` olabilir; arşiv `BRK-B` yazar ve bunu
    manifeste beyan eder (uydurma yasağı: tahmin edilmez, sınır SÖYLENİR)."""
    return dosya.stem.upper()


def kaynak_dosyalari(kaynak: pathlib.Path,
                     semboller: list[str] | None) -> tuple[list[pathlib.Path], list[str]]:
    """(bulunan dosyalar, bulunamayan semboller). `--sembol` verilmezse dizindeki tüm CSV'ler."""
    if not semboller:
        return sorted(p for p in kaynak.glob("*.csv") if p.is_file()), []
    bulunan, eksik = [], []
    for s in semboller:
        p = kaynak / sembol_dosya_adi(s)
        (bulunan if p.is_file() else eksik).append(p if p.is_file() else s)
    return bulunan, eksik


def csv_oku(yol: pathlib.Path, sembol: str) -> tuple[pd.DataFrame, list[str]]:
    """CSV → `sanitize_bars` çıktısı + o çıktıda EKSİK olan arşiv sütunları (ölçülür, sayılmaz).

    `parse_dates=["date"]` canlı okuma yolunun (`load_bars`) yaptığının aynısıdır: `sanitize_bars`
    komşuluk ve takvim kıyaslarını tarih tipinde yapar, metin üzerinde yapamaz.

    `eksik` SANİTİZE EDİLMİŞ çerçeveden ölçülür, HAM `read_csv` çıktısından DEĞİL (bulgu K5d,
    2026-09-08). Manifestin `eksik_sutunlar` beyanı ile parquet'in NULL sütunları AYNI soruya
    verilen İKİ cevaptır ve `_secim_sql` CAST kararını sanitize edilmiş çerçeveden alır: ikisi
    ayrı çerçeveden ölçülseydi `sanitize_bars` bir gün bir sütun düşürdüğünde manifest "eksik
    değil" derken parquet NULL yazardı — C2'nin kapattığını iddia ettiği tam senaryo, sessizce
    geri gelirdi (tek-kaynak yasası). Bugün ayrışmıyor olmaları YAZILI OLMAYAN bir değişmezdi;
    artık türetme TEK noktadadır ve çivisi vardır."""
    ham = pd.read_csv(yol, parse_dates=["date"])
    temiz, _rapor = sanitize_bars(ham, sembol)
    eksik = sorted(set(SUTUNLAR) - set(temiz.columns))
    return temiz, eksik


# ---------------------------------------------------------------------------------------------
# Yerleşim (bölümleme) — yol ve manifest anahtarı TEK yerden türer
# ---------------------------------------------------------------------------------------------

def parca_seri(temiz: pd.DataFrame, bolum: str) -> pd.Series:
    """Her satırın BÖLÜM ANAHTARI. `sembol` yerleşiminde tek grup vardır ve anahtar YOKTUR:
    `None` taşınır (uydurma bir etiket, raporda gerçek bir bölüm parçası gibi okunurdu)."""
    if bolum == BOLUM_SEMBOL:
        return pd.Series([None] * len(temiz), index=temiz.index, dtype=object)
    bicim = "%Y" if bolum == BOLUM_YIL else "%Y-%m"
    return temiz["date"].dt.strftime(bicim)


def hedef_yolu(hedef: pathlib.Path, bolum: str, sembol: str, parca: str | None) -> pathlib.Path:
    """(bölüm, sembol, parça) → parquet yolu. YAZAN da SİLEN de burayı çağırır: iki yerde
    yazılsaydı `--temizle` yazıcının bıraktığından başka bir dosyayı silmeye çalışırdı."""
    if bolum == BOLUM_SEMBOL:
        return hedef / f"{sembol}.parquet"
    return hedef / str(parca) / f"{sembol}.parquet"


def manifest_bolumu(manifest: dict) -> str:
    """Manifestin BEYAN ETTİĞİ yerleşim. Alan yoksa `BOLUMSUZ_MANIFEST_DUZENI` (gerekçe orada)."""
    return manifest.get("bolum") or BOLUMSUZ_MANIFEST_DUZENI


def kayit_al(manifest: dict, bolum: str, sembol: str, parca: str | None) -> dict | None:
    """Manifestten bir (sembol, parça) kaydı. `sembol` yerleşiminde kayıt doğrudan sembolün
    altındadır (ara anahtar YOK); diğerlerinde parça anahtarının altındadır."""
    govde = manifest.get("semboller", {}).get(sembol)
    if not govde:
        return None
    if bolum == BOLUM_SEMBOL:
        return govde
    return govde.get(parca)


def manifest_dosyalari(hedef: pathlib.Path, manifest: dict) -> list[pathlib.Path]:
    """Manifestte KAYITLI parquet yolları — manifestin KENDİ `bolum` beyanına göre türetilir.
    `--temizle`nin sildiği küme budur; listede olmayan dosya YABANCIdır ve dokunulmaz."""
    bolum = manifest_bolumu(manifest)
    yollar: list[pathlib.Path] = []
    for sembol, govde in sorted((manifest.get("semboller") or {}).items()):
        if bolum == BOLUM_SEMBOL:
            yollar.append(hedef_yolu(hedef, bolum, sembol, None))
        else:
            for parca in sorted(govde or {}):
                yollar.append(hedef_yolu(hedef, bolum, sembol, parca))
    return yollar


def temizle_uygula(hedef: pathlib.Path, yollar: list[pathlib.Path]) -> tuple[int, int]:
    """Verilen yolları siler ve BOŞALAN bölüm dizinlerini kaldırır; (silinen, bayt) döner.

    Dizin ancak GERÇEKTEN boşsa kalkar — içinde yabancı bir dosya kaldıysa dizin de kalır.
    Hedefin KÖKÜ hiçbir koşulda silinmez (manifest orada yaşar)."""
    silinen, bayt = 0, 0
    for yol in yollar:
        if not yol.is_file():
            continue
        bayt += yol.stat().st_size
        yol.unlink()
        silinen += 1
    for d in sorted({y.parent for y in yollar}, reverse=True):
        if d != hedef and d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    return silinen, bayt


# ---------------------------------------------------------------------------------------------
# Parquet yazımı ve doğrulama
# ---------------------------------------------------------------------------------------------

def _secim_sql(kaynak_adi: str, mevcut_sutunlar) -> str:
    """Şemayı DONDURAN SELECT. Var olmayan sütun `CAST(NULL AS <tip>)` olur — sıfır ya da
    yer tutucu bir değer DEĞİL (uydurma yasağı).

    `mevcut_sutunlar` ÇAĞIRANIN DataFrame'inin GERÇEK sütun kümesidir — statik `CSV_SUTUNLARI`
    sabitine BAKILMAZ (bulgu C2, 2026-09-08): o sabit `csv_oku`'nun ölçtüğü `eksik` kümesinden
    BAĞIMSIZ bir ikinci karar noktasıydı ve ileride CSV'ye gerçek bir `kaynak`/`ayarlama_olcegi`
    sütunu eklenirse, manifest onu 'eksik değil' diye doğru beyan ederken bu fonksiyon yine de
    sabit tuple'a bakıp NULL yazardı — iki karar aynı soruyu bağımsız cevaplayıp sessizce
    ayrışırdı (tek-kaynak yasası). `CSV_SUTUNLARI` artık YALNIZ dokümantasyon/varsayılan amaçlı
    durur; CAST kararı burada TÜRETİLİR."""
    mevcut = set(mevcut_sutunlar)
    parcalar = []
    for s in SUTUNLAR:
        tip = SUTUN_TIPLERI[s]
        if s in mevcut:
            parcalar.append(f"CAST({s} AS {tip}) AS {s}")
        else:
            parcalar.append(f"CAST(NULL AS {tip}) AS {s}")
    return f"SELECT {', '.join(parcalar)} FROM {kaynak_adi} ORDER BY date"


def _olc(con: duckdb.DuckDBPyConnection, kaynak_sql: str) -> dict:
    """Bir kaynağın DOĞRULAMA ÖLÇÜMÜ: satır · min(date) · max(date) · sum(close). Kaynak
    bellek-içi çerçeve de olabilir, parquet de — kıyasın iki yakası AYNI ifadeyle ölçülür."""
    satir, ilk, son, kapanis = con.execute(
        f"SELECT count(*), min(date), max(date), sum(close) FROM ({kaynak_sql}) AS _k"
    ).fetchone()
    return {"satir": int(satir),
            "ilk": ilk.isoformat() if ilk is not None else None,
            "son": son.isoformat() if son is not None else None,
            "kapanis_toplami": float(kapanis) if kapanis is not None else None}


def _parquet_yaz(con: duckdb.DuckDBPyConnection, df: pd.DataFrame,
                 hedef_dosya: pathlib.Path) -> int:
    """Çerçeveyi parquet olarak yazar, DOSYA BOYUTUNU döndürür.

    pyarrow YOKTUR (yerel + A1'de ölçüldü 2026-09-07) ve EKLENMEZ: yazım DuckDB'nin kendi
    pandas taramasıyla (`register`) ve `COPY … (FORMAT PARQUET)` ile yapılır — `ops/olay_sikistir.py`
    ile AYNI mekanizma. Ölçüldü (duckdb 1.5.5, bu depoda): kayan noktalı `volume` BIGINT'e,
    `datetime64` DATE'e sorunsuz düşüyor ve NULL sütunlar tipini koruyor."""
    hedef_dosya.parent.mkdir(parents=True, exist_ok=True)
    con.register("_bar_kaynak", df)
    try:
        con.execute(
            f"COPY ({_secim_sql('_bar_kaynak', df.columns)}) TO "
            f"{olay_sorgu.sql_metni(hedef_dosya)} (FORMAT PARQUET, COMPRESSION ZSTD)")
    finally:
        con.unregister("_bar_kaynak")
    return hedef_dosya.stat().st_size


def _dogrula(beklenen: dict, olculen: dict) -> str | None:
    """Kabulde None, farkta GEREKÇE. Satır/ilk/son TAM eşitlik; kapanış toplamı toleranslı
    (gerekçe modül başlığında)."""
    if beklenen["satir"] != olculen["satir"]:
        return (f"satır sayısı tutmadı — CSV(sanitize) {beklenen['satir']}, "
                f"parquet {olculen['satir']}")
    for alan in ("ilk", "son"):
        if beklenen[alan] != olculen[alan]:
            return (f"{alan} gün tutmadı — CSV(sanitize) {beklenen[alan]}, "
                    f"parquet {olculen[alan]}")
    a, b = beklenen["kapanis_toplami"], olculen["kapanis_toplami"]
    if (a is None) != (b is None):
        return f"kapanış toplamı tutmadı — CSV(sanitize) {a}, parquet {b}"
    if a is not None and not math.isclose(a, b, rel_tol=KAPANIS_REL_TOL):
        return f"kapanış toplamı tutmadı — CSV(sanitize) {a!r}, parquet {b!r}"
    return None


def kaynak_icerik_hash(dilim: pd.DataFrame) -> str:
    """(sembol, parça) KAYNAĞININ İÇERİK hash'i — TÜM sütunlar, `date`e göre sıralı satır satır
    (bulgu C3, 2026-09-08). `atlanir_mi` kıyası buna dayanır: satır/ilk/son/kapanış TOPLAMI
    özet istatistikleri AYNI kalıp tek bir hücreyi (ör. bir günün `open`/`high`/`low`/`volume`
    değeri) değiştiren bir OHLCV revizyonu o dört özeti KORUR ama bu hash'i DEĞİŞTİRİR —
    `pandas.util.hash_pandas_object` her sütunun ham DEĞERLERİNİ (metne çevirmeden, biçim
    belirsizliği taşımadan) hash'ler, yani kayan nokta biçimlendirme farkı gürültü ÜRETMEZ.

    AKIŞA SÜTUN ADI VE UZUNLUĞU DA GİRER (bulgu K5a, 2026-09-08). Yalnız değer hash'lenirse üst
    akış CSV yazıcısının bir yeniden adlandırması (`volume` → `hacim`, DEĞERLER AYNI) bu hash'i
    DEĞİŞTİRMEZ: kapı "atlandı" der, parquet yeniden yazılmaz, ama `main()` `eksik_sutunlar`ı
    koşulsuz günceller — manifest "volume eksik" derken parquet gerçek volume taşır ve o beyanın
    okuyucusu VARDIR (`ops/bar_sorgu.py::_olculemedi_beyani`). Ad `\0` ile sonlandırılır, uzunluk
    8 baytlık sabit alanla önce yazılır: ikisi de ALAN AYRIMIdır — bitişik iki sütunun bayt
    akışının başka bir sütun kümesiyle çakışması (sınır belirsizliği) böyle kapanır."""
    sirali = dilim.sort_values("date").reset_index(drop=True)
    h = hashlib.sha256()
    for kolon in sirali.columns:
        degerler = pd.util.hash_pandas_object(sirali[kolon], index=False).values.tobytes()
        h.update(str(kolon).encode("utf-8") + b"\0")
        h.update(len(degerler).to_bytes(8, "little"))
        h.update(degerler)
    return h.hexdigest()


def sha256_dosya(yol: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


def yaz_ve_dogrula(con: duckdb.DuckDBPyConnection, df: pd.DataFrame, beklenen: dict,
                   hedef_dosya: pathlib.Path) -> tuple[int | None, str | None]:
    """Geçici dosyaya yaz → geri oku → doğrula → `os.replace`. Dönüş: (bayt, gerekçe|None).

    Doğrulama düşerse geçici dosya SİLİNİR ve hedefe DOKUNULMAZ: yarım doğrulanmış bir arşiv,
    hiç olmayan bir arşivden daha tehlikelidir (varmış gibi durur)."""
    hedef_dosya.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_adi = tempfile.mkstemp(dir=str(hedef_dosya.parent),
                                   prefix=f".{hedef_dosya.stem}-", suffix=".tmp")
    os.close(fd)
    tmp = pathlib.Path(tmp_adi)
    try:
        bayt = _parquet_yaz(con, df, tmp)
        olculen = _olc(con, f"SELECT * FROM read_parquet({olay_sorgu.sql_metni(tmp)})")
        gerekce = _dogrula(beklenen, olculen)
        if gerekce is not None:
            tmp.unlink()
            return None, gerekce
        os.replace(tmp_adi, hedef_dosya)
        return bayt, None
    except BaseException:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:  # sessiz-yutma: temizlik EN İYİ ÇABAdır, asıl istisna yukarı fırlatılmaya devam ediyor ve hüküm onundur
                pass
        raise


# ---------------------------------------------------------------------------------------------
# Manifest — okuyucusu BU aracın idempotency kapısı + ops/bar_sorgu.py (`dikis` beyanı)
# ---------------------------------------------------------------------------------------------

def manifest_yolu(hedef: pathlib.Path) -> pathlib.Path:
    return hedef / MANIFEST_ADI


def manifest_oku(hedef: pathlib.Path) -> dict:
    """Manifest yoksa BOŞ iskelet (henüz hiç arşivlenmemiş — hata değil). BOZUKSA sinyalli
    düşülür: "daha önce ne doğrulandı" bilgisi güvenilmiyorsa idempotency kararı da güvenilmez."""
    yol = manifest_yolu(hedef)
    if not yol.exists():
        return {"uretim": {}, "eksik_sutunlar": {}, "semboller": {}}
    try:
        icerik = json.loads(yol.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise RuntimeError(f"manifest okunamadı ({yol}): {type(e).__name__}: {e}") from e
    for alan in ("uretim", "eksik_sutunlar", "semboller"):
        icerik.setdefault(alan, {})
    return icerik


def manifest_guncelle(hedef: pathlib.Path, yeni_kayitlar: dict, eksik_sutunlar: dict,
                      bolum: str, sifirla: bool = False) -> None:
    """Mevcut kayıtları KORUR, verilenleri ekler/üzerine yazar; atomik (`store._atomic_write`).
    Tek sembollük bir koşum manifesti EZEMEZ — ezseydi, arşivin geri kalanı kaydını kaybeder ve
    bir sonraki tam koşumda hepsi yeniden yazılırdı.

    `sifirla` YALNIZ `--temizle`den sonra verilir: kayıtlı dosyalar diskten kalktığı an defterin
    onları hâlâ "doğrulandı" diye taşıması bir YALAN olurdu.

    `bolum` alanı arşivin TEK yerleşim beyanıdır — kayıtların içine KOPYALANMAZ; iki kopya
    sessizce ayrışır ve uyuşmazlık kapısı hangisine bakacağını bilemezdi (tek-kaynak yasası)."""
    mevcut = ({"uretim": {}, "eksik_sutunlar": {}, "semboller": {}} if sifirla
              else manifest_oku(hedef))
    for sembol, aylar in yeni_kayitlar.items():
        mevcut["semboller"].setdefault(sembol, {}).update(aylar)
    mevcut["eksik_sutunlar"].update(eksik_sutunlar)
    mevcut["bolum"] = bolum
    mevcut["uretim"] = {
        "utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "arac": ARAC_ADI,
        "surum": ARAC_SURUMU,
        "sembol_kaynagi": "dosya adı (küçük harf, '.' → '-') — dönüşüm TERSİNMEZ",
        "sema": list(SUTUNLAR),
    }
    hedef.mkdir(parents=True, exist_ok=True)
    _atomik_yaz(manifest_yolu(hedef),
                json.dumps(mevcut, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def atlanir_mi(kayit: dict | None, kaynak_hash: str, hedef_dosya: pathlib.Path) -> bool:
    """Bu (sembol, parça) yeniden yazılmadan geçilebilir mi? Koşullar modül başlığında
    ("IDEMPOTENCY KIYASI") sayılıdır — hepsi birden.

    KIYAS `kaynak_hash`e (İÇERİK hash'i, `kaynak_icerik_hash`) DAYANIR — dört özet istatistiğe
    (satır/ilk/son/kapanış toplamı) DEĞİL (bulgu C3, 2026-09-08: özetler toplamı KORUYAN bir
    OHLCV revizyonunu kaçırırdı). Disk sha256 kontrolü AYRI ve HÂLÂ VAR: biri KAYNAĞIN
    (`kaynak_hash`), diğeri HEDEF DOSYANIN elle değiştirilmediğini ölçer — ikisi FARKLI
    sorulardır ve biri diğerinin yerine geçemez."""
    if not kayit or not hedef_dosya.is_file():
        return False
    if kayit.get("kaynak_hash") != kaynak_hash:
        return False
    return kayit.get("sha256") == sha256_dosya(hedef_dosya)


# ---------------------------------------------------------------------------------------------

def _ayristirici() -> argparse.ArgumentParser:
    a = argparse.ArgumentParser(
        prog=ARAC_ADI,
        description="state/bars/*.csv önbelleğini bölümlü TİPLİ parquet arşivine çevirir "
                    "(CSV silinmez; varsayılan KURU; varsayılan bölüm: sembol).",
        epilog="Arşivin okuyucusu: ops/bar_sorgu.py",
    )
    a.add_argument("--kaynak-dizin", type=pathlib.Path, default=None, dest="kaynak_dizin",
                   help="CSV önbellek dizini (varsayılan: config.BARS = state/bars)")
    a.add_argument("--hedef", type=pathlib.Path, default=None,
                   help="arşiv dizini (varsayılan: config.STATE/barlar)")
    a.add_argument("--bolum", choices=BOLUMLER, default=VARSAYILAN_BOLUM,
                   help="yerleşim: sembol=<SEMBOL>.parquet (varsayılan) · yil=<YIL>/… · "
                        "ay=<AAAA-AA>/… (eski, uyumluluk)")
    a.add_argument("--temizle", action="store_true",
                   help="manifestte KAYITLI dosyaları sil (yerleşim değiştirirken); yabancı "
                        "dosyaya dokunmaz, kuru koşumda yalnız söyler")
    a.add_argument("--sembol", action="append", default=None,
                   help="yalnız bu sembol(ler) — birden çok kez verilebilir")
    a.add_argument("--ay", default=None, help="yalnız bu ay (AAAA-AA) — YALNIZ `--bolum ay` ile")
    a.add_argument("--uygula", action="store_true",
                   help="GERÇEKTEN yaz (varsayılan KURU: hiçbir bayt yazılmaz)")
    a.add_argument("--zorla", action="store_true",
                   help="manifest kaydı eşleşse bile yeniden yaz")
    a.add_argument("--json", action="store_true", dest="json_kipi", help="satır-JSON bas")
    return a


def main(argv: list[str] | None = None) -> int:
    args = _ayristirici().parse_args(argv)

    if args.ay is not None and not AY_DESENI.match(args.ay):
        print(f"HATA: `--ay` biçimi AAAA-AA olmalı (örn. 2024-01); verilen: {args.ay!r}",
              file=sys.stderr)
        return 2

    if args.ay is not None and args.bolum != BOLUM_AY:
        print(f"HATA: `--ay` süzgeci yalnız `--bolum ay` ile kullanılabilir; verilen bölüm: "
              f"{args.bolum!r}. `{args.bolum}` yerleşiminde bir dosya bir AYın değil "
              f"{'sembolün' if args.bolum == BOLUM_SEMBOL else 'yılın'} TAMAMIdır — ay süzgeci "
              f"YARIM bir dosya yazar ve manifest onu 'tam' diye kaydederdi.", file=sys.stderr)
        return 2

    kaynak = args.kaynak_dizin or pathlib.Path(_config.BARS)
    hedef = args.hedef or (pathlib.Path(_config.STATE) / VARSAYILAN_HEDEF_ALT)

    if not kaynak.is_dir():
        print(f"HATA: kaynak dizin bulunamadı: {kaynak}", file=sys.stderr)
        return 1

    dosyalar, eksik_semboller = kaynak_dosyalari(kaynak, args.sembol)
    if eksik_semboller:
        print(f"HATA: şu sembollerin CSV'si bulunamadı ({kaynak}): "
              f"{', '.join(sorted(eksik_semboller))}", file=sys.stderr)
        return 1
    if not dosyalar:
        print(f"HATA: {kaynak} altında hiç CSV yok — arşivlenecek girdi bulunamadı.",
              file=sys.stderr)
        return 1

    try:
        manifest = manifest_oku(hedef)
    except RuntimeError as e:
        print(f"HATA: {e}", file=sys.stderr)
        return 2

    kayitli_bolum = manifest_bolumu(manifest)
    kayitli_var = bool(manifest.get("semboller"))
    if kayitli_var and kayitli_bolum != args.bolum and not args.temizle:
        print(f"HATA: BÖLÜM UYUŞMAZLIĞI — {hedef} arşivi {kayitli_bolum!r} yerleşiminde "
              f"yazılmış, istenen yerleşim {args.bolum!r}. İki yerleşim aynı dizinde karışırsa "
              f"okuyucu aynı sembolü İKİ KEZ toplar ve kapsam sessizce şişer. Önce "
              f"`--temizle` (manifestte kayıtlı dosyaları siler, yabancıya dokunmaz), ya da "
              f"`--bolum {kayitli_bolum}` ile devam et. Hedefe DOKUNULMADI.", file=sys.stderr)
        return 5

    temizlenecek = manifest_dosyalari(hedef, manifest) if args.temizle else []
    if args.temizle:
        var_olan = [y for y in temizlenecek if y.is_file()]
        if not args.uygula:
            print(f"KURU KOŞUM: `--temizle` silinecek dosya sayısı {len(var_olan)} "
                  f"({kayitli_bolum!r} yerleşimi); hiçbiri SİLİNMEDİ. Silmek için `--uygula`.",
                  file=sys.stderr)
        else:
            silinen, silinen_bayt = temizle_uygula(hedef, temizlenecek)
            print(f"TEMİZLENDİ: {silinen} dosya / {silinen_bayt} bayt silinecekti ve silindi "
                  f"({kayitli_bolum!r} yerleşimi). Manifeste KAYITLI OLMAYAN dosyalara "
                  f"dokunulmadı.", file=sys.stderr)
            # Defter DİSKLE AYNI ANDA sıfırlanır: silinmiş dosyaları hâlâ "doğrulandı" diye
            # taşıyan bir manifest, koşumun geri kalanı düşerse yerinde kalırdı.
            manifest_guncelle(hedef, {}, {}, args.bolum, sifirla=True)
            manifest = manifest_oku(hedef)

    con = olay_sorgu.baglanti_kur()
    satirlar: list[dict] = []
    yeni_kayitlar: dict = {}
    eksik_sutunlar: dict = {}
    farklar: list[str] = []
    goc_kayitlari: list[str] = []      # `kaynak_hash`siz (eski sözleşme) manifest kayıtları
    csv_bayt = 0                       # BEDEL payda: yalnız satır ÜRETEN CSV'ler sayılır
    try:
        for yol in dosyalar:
            sembol = sembol_adi(yol)
            try:
                temiz, eksik = csv_oku(yol, sembol)
            except (OSError, ValueError, KeyError) as e:
                # Sinyalli: okunamayan bir defter SESSİZCE "0 satır" sayılmaz — o, arşivin
                # eksik olduğunu gizlerdi (Yasa 4).
                print(f"HATA: CSV okunamadı ({yol}): {type(e).__name__}: {e}", file=sys.stderr)
                return 2
            eksik_sutunlar[sembol] = eksik
            if temiz is None or temiz.empty:
                print(f"UYARI: {sembol} — sanitize sonrası 0 satır kaldı ({yol}); bu sembol "
                      f"için hiçbir ay yazılmaz.", file=sys.stderr)
                continue

            csv_bayt += yol.stat().st_size
            anahtarlar = parca_seri(temiz, args.bolum)
            for parca in sorted(anahtarlar.unique(), key=lambda k: (k is not None, k)):
                if args.ay is not None and parca != args.ay:
                    continue
                # `is None` kıyası: `sembol` yerleşiminde anahtar None'dır ve `==` ile
                # kıyaslamak pandas'ta satır maskesini SESSİZCE boş bırakırdı.
                maske = anahtarlar.isna() if parca is None else (anahtarlar == parca)
                dilim = temiz.loc[maske].reset_index(drop=True)
                etiket = sembol if parca is None else f"{sembol} {parca}"
                hedef_dosya = hedef_yolu(hedef, args.bolum, sembol, parca)
                try:
                    con.register("_bar_beklenen", dilim)
                    try:
                        beklenen = _olc(con, _secim_sql("_bar_beklenen", dilim.columns))
                    finally:
                        con.unregister("_bar_beklenen")
                except duckdb.Error as e:
                    print(f"HATA: ölçüm düştü ({etiket}): {e}", file=sys.stderr)
                    return 4
                kaynak_hash = kaynak_icerik_hash(dilim)

                kayit = kayit_al(manifest, args.bolum, sembol, parca)
                # GÖÇ GÖRÜNÜR OLSUN (bulgu K5b): `kaynak_hash` alanı OLMAYAN bir kayıt eski
                # sözleşmeyle yazılmıştır ve deterministik olarak yeniden yazılır. Neden
                # SAYILIR, satır satır BASILMAZ: 260 sembollük bir arşivde 260 ek satır bedeli
                # kendisi gürültü olurdu — özet tek satırda, koşum sonunda düşer.
                if kayit and "kaynak_hash" not in kayit:
                    goc_kayitlari.append(sembol if parca is None else f"{sembol} {parca}")
                if not args.zorla and atlanir_mi(kayit, kaynak_hash, hedef_dosya):
                    satirlar.append({"sembol": sembol, "parca": parca,
                                     "satir": beklenen["satir"],
                                     "bayt": hedef_dosya.stat().st_size,
                                     "durum": DURUM_ATLANDI, "dosya": str(hedef_dosya)})
                    continue

                if not args.uygula:
                    # bayt UYDURULMAZ: yazılmamış dosyanın boyutu ÖLÇÜLEMEZ.
                    satirlar.append({"sembol": sembol, "parca": parca,
                                     "satir": beklenen["satir"],
                                     "bayt": None, "durum": DURUM_YAZILACAK,
                                     "dosya": str(hedef_dosya)})
                    continue

                try:
                    bayt, gerekce = yaz_ve_dogrula(con, dilim, beklenen, hedef_dosya)
                except duckdb.Error as e:
                    print(f"HATA: parquet yazımı düştü ({etiket}): {e} — bu ana kadar "
                          f"yerine konmuş dosyalar diskte duruyor.", file=sys.stderr)
                    return 4
                if gerekce is not None:
                    farklar.append(f"{etiket}: {gerekce}")
                    satirlar.append({"sembol": sembol, "parca": parca,
                                     "satir": beklenen["satir"],
                                     "bayt": None, "durum": DURUM_FARK,
                                     "dosya": str(hedef_dosya)})
                    continue

                # `MANIFEST_DISI_OLCUMLER` DEFTERE GİRMEZ (Yasa 6, gerekçe sabitin yanında).
                govde = {"sha256": sha256_dosya(hedef_dosya), "kaynak_hash": kaynak_hash,
                         "bayt": bayt,
                         **{a: d for a, d in beklenen.items()
                            if a not in MANIFEST_DISI_OLCUMLER}}
                if parca is None:
                    yeni_kayitlar[sembol] = govde
                else:
                    yeni_kayitlar.setdefault(sembol, {})[parca] = govde
                satirlar.append({"sembol": sembol, "parca": parca, "satir": beklenen["satir"],
                                 "bayt": bayt, "durum": DURUM_YAZILDI,
                                 "dosya": str(hedef_dosya)})
    finally:
        con.close()

    if not satirlar:
        print("HATA: seçilen süzgeçle arşivlenecek (sembol, parça) yok — `--ay` ya da "
              "`--sembol` kaynakta karşılık bulmuyor.", file=sys.stderr)
        return 1

    bas = olay_sorgu.json_bas if args.json_kipi else olay_sorgu.tablo_bas
    bas(BASLIKLAR, [tuple(s[b] for b in BASLIKLAR) for s in satirlar], sys.stdout)

    if goc_kayitlari:
        ornek = ", ".join(goc_kayitlari[:5]) + (" …" if len(goc_kayitlari) > 5 else "")
        print(f"GÖÇ (bir kerelik, sürüm {ARAC_SURUMU}): {len(goc_kayitlari)} (sembol, parça) "
              f"kaydı eski sözleşme ile yazılmıştı (`kaynak_hash` alanı YOK) — yeniden "
              f"yazılıyor. Bu bir ARIZA DEĞİLDİR: kıyas sözleşmesi değişti, içerik değil. "
              f"Örnek: {ornek}", file=sys.stderr)

    _bedel_bas(args.bolum, satirlar, csv_bayt, args.ay is not None)

    if farklar:
        for g in farklar:
            print(f"HATA: DOĞRULAMA FARKI — {g}", file=sys.stderr)
        print("Manifest YAZILMADI (hepsi-ya-hiç): doğrulanamayan bir ay varken yarım bir "
              "manifest 'doğrulandı' iddiası taşırdı. Yerine konmuş dosyalar diskte durur ve "
              "sonraki koşum onları yeniden yazar.", file=sys.stderr)
        return 5

    if args.uygula:
        manifest_guncelle(hedef, yeni_kayitlar, eksik_sutunlar, args.bolum)
    else:
        print(f"KURU KOŞUM: hiçbir bayt yazılmadı ({hedef} dizinine dokunulmadı). Yazmak için "
              f"`--uygula`.", file=sys.stderr)
    return 0


def _bedel_bas(bolum: str, satirlar: list[dict], csv_bayt: int, ay_suzgeci: bool) -> None:
    """BEDEL YASASI: bölümlemenin kazancı da bedeli de AYNI satırda ölçülür — dosya SAYISI,
    arşivin toplam BAYTI, kaynak CSV baytı ve oran. Okuyucusu operatördür: A1'deki S4 koşumu
    tam olarak bu üç sayı basılmadığı için "bitmedi" ile "şişti" arasında ayrım yaptıramadı.

    Ölçülemeyen alan UYDURULMAZ: kuru koşumda dosya yazılmadığı için arşiv baytı yoktur, ve
    `--ay` süzgeci varken oranın PAYDASI CSV'nin tamamı olduğu için oran anlamsız olurdu."""
    baytlar = [s["bayt"] for s in satirlar]
    arsiv_bayt = None if any(b is None for b in baytlar) else sum(baytlar)
    parcalar = [f"BEDEL (bölüm={bolum}): {len(satirlar)} dosya"]
    if arsiv_bayt is None:
        parcalar.append("arşiv baytı ÖLÇÜLEMEDİ (dosya yazılmadı: kuru koşum ya da doğrulama "
                        "farkı)")
    else:
        parcalar.append(f"arşiv {arsiv_bayt} bayt")
    parcalar.append(f"CSV {csv_bayt} bayt")
    if arsiv_bayt is None or csv_bayt == 0 or ay_suzgeci:
        parcalar.append("oran ÖLÇÜLEMEDİ"
                        + (" (`--ay` süzgeci: payda CSV'nin TAMAMI)" if ay_suzgeci else ""))
    else:
        parcalar.append(f"oran {arsiv_bayt / csv_bayt:.2f}x (arşiv/CSV)")
    print(" · ".join(parcalar), file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())

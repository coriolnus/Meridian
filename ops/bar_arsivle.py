#!/usr/bin/env python3
# bar_arsivle.py — state/bars/<sembol>.csv canlı önbelleğini AY/SEMBOL bölümlü, TİPLİ parquet
# arşivine çevirir (state/barlar/AAAA-AA/<SEMBOL>.parquet). CSV SİLİNMEZ, DEĞİŞMEZ: canlı okuma
# yolu (`load_bars`) aynen kalır — bu bir strangler ARŞİVİdİR, yer değiştirme değil. Varsayılan
# KURU: `--uygula` verilmedikçe hedefe 1 bayt yazılmaz. Arşivin OKUYUCUSU ops/bar_sorgu.py'dır
# (Yasa 6). Koşum: .venv/bin/python ops/bar_arsivle.py --kaynak-dizin state/bars
"""ops/bar_arsivle.py — GÜNLÜK BAR ÖNBELLEĞİNİN AY/SEMBOL BÖLÜMLÜ PARQUET ARŞİVİ
(TSK-020 [UYGULA-3] Task 1, 2026-09-07; tasarım: docs/TASARIM-BARS-PARQUET-DUCKDB-2026-09-06.md
§3.1).

NEDEN VAR. Bar deposu bugün sembol başına bir CSV'dir (yerel + A1'de 260 dosya / 60 MB, ölçüm
2026-09-06) ve BİÇİMİ TİPSİZDİR: her okumada tarih ayrıştırılır, `sanitize_bars` onarımı yeniden
koşar, sütun tipleri metinden çıkarılır. Ayrıca "2024-06-24'te hangi sembollerin barı vardı",
"dikiş nerede", "hangi seans eksik" sınıfı PIT/replay soruları sembol-dosyası biçiminde SQL'siz
cevaplanamaz. Arşiv bu iki bedeli kapatır; canlı yol DEĞİŞMEZ.

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

IDEMPOTENCY KIYASI = MANİFEST KAYDI + DOSYANIN SHA256'SI. Bir (sembol, ay) ancak şunların HEPSİ
doğruysa "atlandı" olur: hedef dosya var · manifestte kaydı var · kayıttaki satır/ilk/son/kapanış
ölçümü BUGÜNKÜ CSV'nin sanitize edilmiş ölçümüyle aynı · kayıttaki sha256 diskteki dosyanın
sha256'sı. Son koşul dosyanın elle değiştirilmediğini, öncekiler KAYNAĞIN değişmediğini ölçer.
BİLİNEN BEDEL: parquet baytları DuckDB sürümüyle değişebilir, yani sürüm yükseltmesinden sonraki
ilk koşum her ayı YENİDEN YAZAR. Kardeş `ops/olay_sikistir.py` bu yüzden bayt kıyasından kaçınır
— orada yanlış bir KIRMIZI doğardı; burada sonuç yalnız bir yeniden yazımdır ve arşiv değişmez.

WORKER KOŞARKEN GÜVENLİDİR: CSV'ler yalnız OKUNUR, hedef AYRI bir dizindir (`state/barlar/`) ve
her dosya önce aynı dizinde geçici bir ada yazılıp `os.replace` ile yerine konur — okuyucu ya
eski dosyayı ya yeni dosyayı görür, yarısını asla.

KULLANIM:
    python ops/bar_arsivle.py                          # KURU: ne yapacağını söyler, yazmaz
    python ops/bar_arsivle.py --uygula                 # arşivi yaz
    python ops/bar_arsivle.py --sembol AAPL --ay 2024-01 --uygula
    python ops/bar_arsivle.py --kaynak-dizin /yol/bars --hedef /yol/barlar --uygula
    python ops/bar_arsivle.py --uygula --zorla         # manifest eşleşse bile yeniden yaz
    python ops/bar_arsivle.py --json                   # satır-JSON çıktı

ÇIKIŞ KODU: 0 = koştu (yazıldı/yazılacak/atlandı) · 1 = GİRDİ YOK (kaynak dizin/CSV/sembol/ay
           bulunamadı) · 2 = kullanım hatası · 4 = DuckDB'de düştü · 5 = DOĞRULAMA FARKI
           (parquet geri okunduğunda ölçüm tutmadı; hedefe dokunulmadı, manifest yazılmadı).
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
ARAC_SURUMU = "2026-09-07.1"
ARAC_ADI = "ops/bar_arsivle.py"

MANIFEST_ADI = "manifest.json"
VARSAYILAN_HEDEF_ALT = "barlar"

AY_DESENI = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

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

BASLIKLAR = ["sembol", "ay", "satir", "bayt", "durum", "dosya"]

#: `sum(close)` kıyasının toleransı — gerekçe modül başlığında ("DOĞRULAMA TAŞIYICIDIR").
KAPANIS_REL_TOL = 1e-9


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
    """CSV → `sanitize_bars` çıktısı + o dosyada EKSİK olan arşiv sütunları (ölçülür, sayılmaz).

    `parse_dates=["date"]` canlı okuma yolunun (`load_bars`) yaptığının aynısıdır: `sanitize_bars`
    komşuluk ve takvim kıyaslarını tarih tipinde yapar, metin üzerinde yapamaz."""
    ham = pd.read_csv(yol, parse_dates=["date"])
    eksik = sorted(set(SUTUNLAR) - set(ham.columns))
    temiz, _rapor = sanitize_bars(ham, sembol)
    return temiz, eksik


# ---------------------------------------------------------------------------------------------
# Parquet yazımı ve doğrulama
# ---------------------------------------------------------------------------------------------

def _secim_sql(kaynak_adi: str) -> str:
    """Şemayı DONDURAN SELECT. Var olmayan sütun `CAST(NULL AS <tip>)` olur — sıfır ya da
    yer tutucu bir değer DEĞİL (uydurma yasağı)."""
    parcalar = []
    for s in SUTUNLAR:
        tip = SUTUN_TIPLERI[s]
        if s in CSV_SUTUNLARI:
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
        con.execute(f"COPY ({_secim_sql('_bar_kaynak')}) TO {olay_sorgu.sql_metni(hedef_dosya)} "
                    "(FORMAT PARQUET, COMPRESSION ZSTD)")
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


def manifest_guncelle(hedef: pathlib.Path, yeni_kayitlar: dict, eksik_sutunlar: dict) -> None:
    """Mevcut kayıtları KORUR, verilenleri ekler/üzerine yazar; atomik (`store._atomic_write`).
    Tek sembollük bir koşum manifesti EZEMEZ — ezseydi, arşivin geri kalanı kaydını kaybeder ve
    bir sonraki tam koşumda hepsi yeniden yazılırdı."""
    mevcut = manifest_oku(hedef)
    for sembol, aylar in yeni_kayitlar.items():
        mevcut["semboller"].setdefault(sembol, {}).update(aylar)
    mevcut["eksik_sutunlar"].update(eksik_sutunlar)
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


def atlanir_mi(kayit: dict | None, beklenen: dict, hedef_dosya: pathlib.Path) -> bool:
    """Bu (sembol, ay) yeniden yazılmadan geçilebilir mi? Koşullar modül başlığında
    ("IDEMPOTENCY KIYASI") sayılıdır — hepsi birden."""
    if not kayit or not hedef_dosya.is_file():
        return False
    for alan in ("satir", "ilk", "son"):
        if kayit.get(alan) != beklenen[alan]:
            return False
    a, b = beklenen["kapanis_toplami"], kayit.get("kapanis_toplami")
    if (a is None) != (b is None):
        return False
    if a is not None and not math.isclose(a, b, rel_tol=KAPANIS_REL_TOL):
        return False
    return kayit.get("sha256") == sha256_dosya(hedef_dosya)


# ---------------------------------------------------------------------------------------------

def _ayristirici() -> argparse.ArgumentParser:
    a = argparse.ArgumentParser(
        prog=ARAC_ADI,
        description="state/bars/*.csv önbelleğini ay/sembol bölümlü TİPLİ parquet arşivine "
                    "çevirir (CSV silinmez; varsayılan KURU).",
        epilog="Arşivin okuyucusu: ops/bar_sorgu.py",
    )
    a.add_argument("--kaynak-dizin", type=pathlib.Path, default=None, dest="kaynak_dizin",
                   help="CSV önbellek dizini (varsayılan: config.BARS = state/bars)")
    a.add_argument("--hedef", type=pathlib.Path, default=None,
                   help="arşiv dizini (varsayılan: config.STATE/barlar)")
    a.add_argument("--sembol", action="append", default=None,
                   help="yalnız bu sembol(ler) — birden çok kez verilebilir")
    a.add_argument("--ay", default=None, help="yalnız bu ay (AAAA-AA)")
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

    con = olay_sorgu.baglanti_kur()
    satirlar: list[dict] = []
    yeni_kayitlar: dict = {}
    eksik_sutunlar: dict = {}
    farklar: list[str] = []
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

            aylar = temiz["date"].dt.strftime("%Y-%m")
            for ay in sorted(aylar.unique()):
                if args.ay is not None and ay != args.ay:
                    continue
                parca = temiz.loc[aylar == ay].reset_index(drop=True)
                hedef_dosya = hedef / ay / f"{sembol}.parquet"
                try:
                    con.register("_bar_beklenen", parca)
                    try:
                        beklenen = _olc(con, _secim_sql("_bar_beklenen"))
                    finally:
                        con.unregister("_bar_beklenen")
                except duckdb.Error as e:
                    print(f"HATA: ölçüm düştü ({sembol} {ay}): {e}", file=sys.stderr)
                    return 4

                kayit = manifest["semboller"].get(sembol, {}).get(ay)
                if not args.zorla and atlanir_mi(kayit, beklenen, hedef_dosya):
                    satirlar.append({"sembol": sembol, "ay": ay, "satir": beklenen["satir"],
                                     "bayt": hedef_dosya.stat().st_size,
                                     "durum": DURUM_ATLANDI, "dosya": str(hedef_dosya)})
                    continue

                if not args.uygula:
                    # bayt UYDURULMAZ: yazılmamış dosyanın boyutu ÖLÇÜLEMEZ.
                    satirlar.append({"sembol": sembol, "ay": ay, "satir": beklenen["satir"],
                                     "bayt": None, "durum": DURUM_YAZILACAK,
                                     "dosya": str(hedef_dosya)})
                    continue

                try:
                    bayt, gerekce = yaz_ve_dogrula(con, parca, beklenen, hedef_dosya)
                except duckdb.Error as e:
                    print(f"HATA: parquet yazımı düştü ({sembol} {ay}): {e} — bu ana kadar "
                          f"yerine konmuş dosyalar diskte duruyor.", file=sys.stderr)
                    return 4
                if gerekce is not None:
                    farklar.append(f"{sembol} {ay}: {gerekce}")
                    satirlar.append({"sembol": sembol, "ay": ay, "satir": beklenen["satir"],
                                     "bayt": None, "durum": DURUM_FARK,
                                     "dosya": str(hedef_dosya)})
                    continue

                yeni_kayitlar.setdefault(sembol, {})[ay] = {
                    "sha256": sha256_dosya(hedef_dosya), "bayt": bayt, **beklenen}
                satirlar.append({"sembol": sembol, "ay": ay, "satir": beklenen["satir"],
                                 "bayt": bayt, "durum": DURUM_YAZILDI,
                                 "dosya": str(hedef_dosya)})
    finally:
        con.close()

    if not satirlar:
        print("HATA: seçilen süzgeçle arşivlenecek (sembol, ay) yok — `--ay` ya da `--sembol` "
              "kaynakta karşılık bulmuyor.", file=sys.stderr)
        return 1

    bas = olay_sorgu.json_bas if args.json_kipi else olay_sorgu.tablo_bas
    bas(BASLIKLAR, [tuple(s[b] for b in BASLIKLAR) for s in satirlar], sys.stdout)

    if farklar:
        for g in farklar:
            print(f"HATA: DOĞRULAMA FARKI — {g}", file=sys.stderr)
        print("Manifest YAZILMADI (hepsi-ya-hiç): doğrulanamayan bir ay varken yarım bir "
              "manifest 'doğrulandı' iddiası taşırdı. Yerine konmuş dosyalar diskte durur ve "
              "sonraki koşum onları yeniden yazar.", file=sys.stderr)
        return 5

    if args.uygula:
        manifest_guncelle(hedef, yeni_kayitlar, eksik_sutunlar)
    else:
        print(f"KURU KOŞUM: hiçbir bayt yazılmadı ({hedef} dizinine dokunulmadı). Yazmak için "
              f"`--uygula`.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

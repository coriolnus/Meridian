"""bararchive.py — dakikalık WS bar çerçevelerinin gün-dosyalı kalıcı disk arşivi (kanıt katmanının ilk taşı).

NE YAPAR: `hotstate.ingest_bars` her başarılı çerçeve yazımından sonra `archive_frame(bars, ts)`
çağırır; çerçeve `{ts, bars:{ticker:bar}}` satırı olarak `state/intraday_bars/YYYY-MM-DD.jsonl`e
eklenir. Neden var: intraday hattı (hotstate → mrd:bars) BİLEREK uçucudur — Redis ring'i ~2 seans
tutar, TTL sonrası bar yoktur. "Dakika-hassas icra EOD icradan gerçekten daha mı iyi?" sorusu ancak
geçmiş dakikalık çerçeveler biriktikten SONRA cevaplanabilir; bugün başlamayan birikim üç ay sonra
üç aylık olmaz — arşiv bu yüzden ölçümden ÖNCE açılır. Tüketicisi bugün yoktur ve bu BİLİNÇLİDİR
(tüketici gelecekteki "dakika-hassas icra vs EOD" ölçüm raporu): okuyucusuz-yazım yasağına bilerek
ve beyanla verilmiş bir cevaptır — ihlal, kimsenin bilmeden bıraktığı okunmayan dosyadır.

KİLİT GİRİŞLER: archive_frame(bars, ts) (tek dış giriş; yazıldıysa True), ARCHIVE_DIR=
"intraday_bars", ARCHIVE_KEEP_DAYS=120 (takvim günü — kaba ve kasıtlı basit retention),
ENABLED (MERIDIAN_BAR_ARCHIVE=0 yalnız arşivi susturur, ingest'i değil).

DEĞİŞMEZLER: arşiv arızası ingest'i ASLA düşüremez — her istisna burada yakalanır, False dönülür ve
süreç başına TEK uyarı basılır (dakikalık akışta her karede uyarı, olay defterini boğardı). Hedef
dosya UTC gününe göredir: NY seansı 13:30-20:00 UTC aralığında tek UTC gününe düşer, gün sınırı
seansı bölmez. Retention yalnız yeni gün dosyasının İLK yazımında koşar; silinen dosyalar SAYILIR.
Türev-bayatlık dedektörlerine bilerek bağlanmadı: arşiv yalnız seans saatlerinde büyüdüğünden her
gece/hafta sonu sahte bayat alarmı doğardı — gürültüyle susturulmuş bir dedektör, dedektör değildir.

OKUR/YAZAR: `state/intraday_bars/*.jsonl`e store.append_jsonl ile yazar; Redis'i okumaz. Tarihli
f-string dosya adı statik artefakt grafında çözülemez ve `unresolved` olarak raporlanır — bu bilinen,
test edilmiş davranıştır; DECLARED_SINKS'e satır eklenmez ve gerekmez (graf "ihlal" değil
"göremiyorum" der).
"""
from __future__ import annotations

import datetime as dt
import os

from . import config, obs, store

# state/ altındaki arşiv klasörü. Gün başına TEK dosya: bir seansın bütün çerçeveleri yan yana
# okunabilsin ve retention tek `unlink` ile işlesin.
ARCHIVE_DIR = "intraday_bars"
ARCHIVE_KEEP_DAYS = 120          # ~6 ay borsa günü değil, 120 TAKVİM günü — kaba ve kasıtlı basit
# Arşiv KAPATILABİLİR olmalı: dar diskli bir ortamda ingest'in kendisi değil, yalnız arşiv susar.
ENABLED = os.environ.get("MERIDIAN_BAR_ARCHIVE", "1") != "0"

# SÜREÇ BAŞINA TEK UYARI. Dakikalık akışta her çerçevede bir uyarı basmak, olay defterini — yani
# gelen kutusunun ve bütün makullük dedektörlerinin okuduğu kaynağı — boğardı (obs'un susturma
# penceresiyle aynı ders). Anlatılacak olgu "arşiv arızalı", "her karede arızalı" değil.
_WARNED = False


def _archive_path(day: str):
    return config.STATE / ARCHIVE_DIR / f"{day}.jsonl"


def _warn_once(event: str, **fields) -> None:
    global _WARNED
    if _WARNED:
        return
    _WARNED = True
    obs.warn(event, **fields)


def _retention(day: str) -> None:
    """ARCHIVE_KEEP_DAYS'ten eski gün dosyalarını sil. YALNIZ yeni bir gün dosyası ilk kez
    yazılırken çağrılır — her çerçevede dizin taramak dakikalık yolda gereksiz G/Ç olurdu.

    Kendi istisnasını KENDİ yutar (ve bir kez uyarır): retention bir TEMİZLİKTİR; başarısız olması
    yazılmış bir çerçeveyi 'yazılmadı' göstermemeli. Silinenler SAYILIR — sessiz silme, sessiz veri
    kaybının kibar hâlidir."""
    try:
        cutoff = dt.date.fromisoformat(day) - dt.timedelta(days=ARCHIVE_KEEP_DAYS)
        base = config.STATE / ARCHIVE_DIR
        silinen = []
        for p in sorted(base.glob("*.jsonl")):
            try:
                d = dt.date.fromisoformat(p.stem)
            except ValueError:  # sessiz-yutma: tarih adı taşımayan dosya bu retention'ın konusu DEĞİLDİR — silmek yerine dokunulmadan bırakılır; bir uyarı yabancı bir dosya için her gün tekrarlanırdı
                continue
            if d < cutoff:
                p.unlink()
                silinen.append(p.name)
        if silinen:
            obs.log("bar_archive_pruned", removed=len(silinen), keep_days=ARCHIVE_KEEP_DAYS,
                    oldest_kept=cutoff.isoformat(), files=silinen[:10])
    except Exception as e:
        _warn_once("bar_archive_retention_failed", error=f"{type(e).__name__}: {str(e)[:120]}",
                   detail="eski gün dosyaları budanamadı — arşiv büyümeye devam eder, veri kaybı YOK")


def archive_frame(bars: dict, ts: str) -> bool:
    """Bir WS çerçevesini (sembol → bar) arşive düşür. Yazıldıysa True, aksi hâlde False.

    HEDEF DOSYA UTC GÜNÜNE GÖRE: `ts[:10]`. NY seansı 13:30-20:00 UTC aralığındadır, yani bir
    seansın tamamı TEK bir UTC gününe düşer — gün sınırı seansı asla ortadan bölmez. Yerel saate
    (ör. America/New_York) göre bölmek aynı sonucu verirdi ama saat dilimi verisine ve DST'ye
    bağımlılık eklerdi; UTC dilimi hem yeterli hem bağımsızdır.

    ARŞİV ARIZASI INGEST'İ ASLA DÜŞÜREMEZ. Her istisna BURADA yakalanır ve False döner: çağıran
    (hotstate.ingest_bars) sıcak fiyat + bar akışını ZATEN yazmıştır ve o yol kalıcı gerçeğin
    beslendiği yoldur. Bir kanıt-biriktirme yan etkisinin canlı veri hattını kesmesi, kazanılandan
    çok daha fazlasını kaybettirirdi — bu yüzden çağıranın ayrıca try yazmasına GEREK YOKTUR."""
    if not ENABLED:
        return False
    if not bars or not ts or len(str(ts)) < 10:
        return False
    try:
        day = str(ts)[:10]
        path = _archive_path(day)
        # GÜN DEĞİŞİMİ = HEDEF DOSYANIN İLK YAZIMI. Süreç-içi bir "son gün" değişkeni yerine diskin
        # kendisine sorulur: worker yeniden başladığında bellek sıfırlanır ama dosya durur, yani
        # bellek tabanlı bir bayrak her restart'ta gereksiz bir dizin taraması tetiklerdi.
        yeni_gun = not path.exists()
        store.append_jsonl(f"{ARCHIVE_DIR}/{day}.jsonl", {"ts": str(ts), "bars": bars})
        if yeni_gun:
            _retention(day)
        return True
    except Exception as e:
        _warn_once("bar_archive_failed", error=f"{type(e).__name__}: {str(e)[:120]}",
                   detail="dakikalık bar arşivi yazılamadı — ingest ETKİLENMEDİ, yalnız Faz 5 "
                          "kanıt birikimi duruyor (süreç başına tek uyarı)")
        return False

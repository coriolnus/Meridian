"""bararchive.py — Faz 5 KANIT KATMANININ İLK TAŞI: dakikalık bar çerçevelerinin kalıcı arşivi.

NEDEN ŞİMDİ: intraday hattı (hotstate → mrd:bars) UÇUCUDUR ve bilerek öyledir — Redis ring'i ~2
seans tutar, TTL sonrası bar yoktur. Bu, sıcak okuma için doğru; ama "dakika-hassas icra EOD icradan
gerçekten daha mı iyi?" sorusu ancak GEÇMİŞ dakikalık çerçeveler biriktikten SONRA cevaplanabilir.
Bugün başlamayan bir birikim, üç ay sonra da üç aylık olmaz. Arşiv bu yüzden ölçümden ÖNCE açılır.

TÜKETİCİSİ BUGÜN YOK VE BU BİLİNÇLİDİR. Tüketici GELECEK "dakika-hassas icra vs EOD" ölçüm
raporudur. Bunu yazmak, YASA 6'nın (üretilip tüketilmeyen artefakt) bilerek verilmiş bir cevabıdır:
ihlal, kimsenin OKUMADIĞI bir dosyayı kimsenin BİLMEDEN bırakmasıdır — kararın kendisi değil.

CODELAW BULGUSU (2026-07-27, ölçüldü — varsayılmadı): `codelaw.artifact_graph` bir yazma/okuma
çağrısının İLK ARGÜMANINI yalnız üç biçimde çözer: dize sabiti, modül/global sabit adı, ya da bir
attribute. Buradaki hedef ad TARİHLİDİR ve f-string ile kurulur (`intraday_bars/2026-07-27.jsonl`),
yani `ast.JoinedStr`dir → statik graf onu ÇÖZEMEZ ve `artifacts` sözlüğüne HİÇ girmez; bunun yerine
`unresolved` listesine yazılır (tarayıcı kendi körlüğünü gizlemez — tests/test_codelaw_v59.py'deki
`test_dinamik_adli_artefaktlar_unresolved_olarak_raporlanir` bu davranışı çiviler).
SONUÇ: `DECLARED_SINKS`'e bir satır EKLENEMEZ (anahtarlar `unread` artefakt adlarıyla eşleşir; tarihli
ad hiç artefakt olarak görünmediği için yazılan satır ölü bir muafiyet olurdu — üstelik `stale_sinks`
ihlali doğururdu) ve GEREKMEZ (graf zaten "ihlal" demiyor, "göremiyorum" diyor ve bunu raporluyor).
`codelaw.report()["ok"]` bu yüzden True kalır: `ok`, `unresolved` sayısına DEĞİL, `violations` ve
`unscanned` listelerine bakar.

WATCHDOG'A BAĞLANMADI (ilmek-1'deki v102 kararının aynısı): `DERIVED_SOURCES` (türev bayatlığı) ve
benzeri haritalara bir satır eklemek, seans-dışı her gün ve her hafta sonu SAHTE bayat alarmı
üretirdi — çünkü arşiv yalnız NY seansında (13:30-20:00 UTC) büyür ve akşamdan ertesi açılışa kadar
"kaynak ilerledi, türev ilerlemedi" görünür. Gürültüyle susturulmuş bir dedektör, dedektör değildir.
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

"""store.py — state/ defterlerinin tek okuma-yazma kapısı: atomik yazım + file_lock + db_backed yönlendirmesi.

NE YAPAR. state/ (tek mutasyona açık dizin) altındaki JSON/JSONL/metin defterlerinin tüm G/Ç'sini
tek boğazdan geçirir. Yazım dayanıklı-atomiktir: mkstemp + write + fsync + os.replace + dizin
fsync — `os.replace` tek başına yalnız yer değiştirmenin atomikliğini garanti eder, verinin diske
indiğini ETMEZ; fsync'siz hâli güç kesintisi sonrası sıfır-baytlık dosya bırakabiliyordu.
`sanitize` numpy skalerlerini yerli tiplere çevirir; NaN/±Inf → None (UYDURMA YASAĞI: ölçülemeyen
değer 0.0 diye yazılmaz). Bozuk dosya/satır varsayılana düşer ama SESSİZ DEĞİL
(`state_file_unreadable` / `jsonl_rows_skipped`, dosya başına bir kez).

KİLİT GİRİŞLER. `write_json`/`read_json`, `append_jsonl`/`read_jsonl`/`write_jsonl`, `write_text`
(JSON olmayan defterler için AYNI kapı), `update_json`/`update_jsonl`/`merge_dated_jsonl` (kilitli
oku-değiştir-yaz — kayıp-güncelleme yapısal olarak imkânsız), `file_lock(ad)` (süreç-içi RLock +
süreçler-arası `fcntl.flock`; RLock tek başına YETMİYORDU — yalnız aynı süreçte anlam taşır, kilit
dosyası `state/.locks/<ad>.lock`tur çünkü veri dosyası os.replace ile inode değiştirir),
`db_backed(ad)` (altı defter adı `state/meridian.db` varsa storage.py'ye yönlenir; depolama
migrasyonudur, davranış migrasyonu değil), `stamp`/`mtime` (arka-uç bağımsız tazelik damgası),
`kilit_budamasi`, `io_stats`.

DEĞİŞMEZLER. Kilit çağıranın elinde değil KAPININ İÇİNDEdir — kilitsiz yazmak store'u bypass
etmeyi gerektirir. DB'ye giden adda flock ALINMAZ: o adlar SQLite'ın kendi kilidiyle (WAL +
busy_timeout) korunur; iki kilit rejimini üst üste koymak iki farklı sırayla alınan iki kilit,
yani kilitlenme demekti. DB devredeyken kanonik adda kalan göç-edilmiş bayat dosya `.migrated`
disiplinine çekilir (hiçbir şey silinmez/ezilmez); göçü kanıtsız dosyaya `.migrated` denMEZ,
yalnız beyan edilir. Okur/yazar: yalnız state/ altı defterler + `state/.locks/`; DB devredeyken
altı varlık storage.py üzerinden `state/meridian.db`.
"""
from __future__ import annotations
import fcntl
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any
import numpy as np

from . import config
from . import storage


def _state():
    return config.STATE


def _path(name: str) -> Path:
    return _state() / name if not os.path.isabs(name) else Path(name)


def db_backed(name: str) -> bool:
    """Bu ad ŞU AN SQLite'tan mı okunuyor? (Okuyucusu: dbmigrate, ledgerstamp, testler.)"""
    aktif = storage.active(name) if not os.path.isabs(str(name)) else False
    if aktif:
        # DB devredeyse İLK temasta bayat-defter süzgeci koşar (aşağıda; süreç+yol başına BİR KEZ).
        # `MERIDIAN_DB=off` iken `aktif` False'tur, yani dosyaların OTORİTER olduğu modda süzgeç
        # yapısal olarak devre dışıdır — orada kanonik dosyayı taşımak defteri yok etmek olurdu.
        _bayat_defter_suzgeci()
    return aktif


# ---- BAYAT-DEFTER-KALINTISI SÜZGECİ ---------------------------------
# BULGU (VLO adli incelemesi): defterler 07-31'de DB'ye göçtü ama canlıda
# `state/trades.jsonl` 95 satırda DONUK bir kalıntı olarak kanonik adında kaldı (DB 97; portfolio/
# shadow_books `.migrated` olmuş, trades OLMAMIŞTI) ve Rol-1'i "pozisyon izsiz kayboldu" yanılgısına
# düşürdü — gerçek: T00097 DB'de düzgündü. `dbmigrate.apply` arşivlemeyi yalnız O KOŞUDA taşıdığı
# varlıklar için (`tasinan` listesi) ve yalnız `p.exists() and not hedef.exists()` ise yapar; yani
# disiplin TEK ATIŞLIKTIR ve üç sınıf açıkta kalır:
#   (a) hedef arşiv ZATEN varsa kaynak sessizce yerinde kalır (dbmigrate.apply arşiv döngüsü —
#       else dalı yok, rapora da düşmez);
#   (b) `zaten_tasindi` varlığın SONRADAN yeniden doğan kanonik dosyasına hiçbir koşu dokunmaz
#       (ikinci `--uygula` onu `tasinan`a almaz);
#   (c) `MERIDIAN_DB=off` penceresinde dosya yoluna yazılmış kanonik dosya, DB'ye dönülünce
#       görünmez olur ama diskte kanonik adıyla durur.
# Üçünde de UYGULAMA doğru okur (aşağıdaki read_* dallarında dosyaya düşüş YOKTUR — DB otoriter;
# test çivisi v234) ama İNSAN ve harici araç bayat dosyayı okur. Süzgeç bu sınıfı kapatır:
# DB'nin devrede olduğu ilk `db_backed` temasında, `migrated_at` DAMGALI bir varlığın kanonik düz
# dosyası hâlâ duruyorsa `.migrated`a çevrilir (hedef doluysa `.migrated-<ts>-p<pid>` — POSIX
# rename dolu hedefi SESSİZCE EZERDİ; hiçbir şey silinmez ve üzerine yazılmaz). İdempotent: bir
# sonraki restart/dağıtımda canlıda kendiliğinden düzelir. `migrated_at` DAMGASIZ varlığın kanonik
# dosyası TAŞINMAZ — içeriğinin DB'ye geçtiği hiç kanıtlanmadı, ona `.migrated` demek UYDURMA
# olurdu; yalnız beyan edilir (YASA 4: görünmez dosya sessiz bırakılmaz). dbmigrate'in kuru koşu /
# `--durum` / `--geri-al` yolları store'a hiç girmediği için bu süzgeç onların "tek bayt yazmam"
# sözünü delmez; `--geri-al` sonrası DB yok → `active()` False → süzgeç yapısal olarak kapalı.
_BAYAT_SUPURULDU: set = set()


def _bayat_defter_suzgeci() -> None:
    """Göç-edilmiş varlığın kanonik düz dosyası duruyorsa `.migrated` disiplinine çek (bir kez)."""
    key = str(storage.db_path())
    if key in _BAYAT_SUPURULDU:
        return
    if len(_BAYAT_SUPURULDU) > 64:      # sandbox yolları süreç ömrü boyunca birikmesin (_SCHEMA_OK deseni)
        _BAYAT_SUPURULDU.clear()
    # DAMGA İŞTEN ÖNCE (storage._OFF_OLCULDU deseni): aşağıdaki obs.warn → append_jsonl →
    # db_backed zinciri bu fonksiyona geri gelir; damga özyinelemeyi yapısal olarak keser.
    _BAYAT_SUPURULDU.add(key)
    arsivlenen: list = []
    gocsuz: list = []
    hatalar: list = []
    for name in storage.ENTITIES:
        try:
            p = _state() / name
            if not p.exists():
                continue
            m = storage.meta(name)
            if not (m and m.get("migrated_at")):
                gocsuz.append(name)
                continue
            # Adli sinyaller RENAME'DEN ÖNCE ölçülür (VLO vakasında dosyanın donukluğunu anlatan
            # da tam bunlardı: boyut 95 satırda, mtime migrasyon gününde). İçerik-digest kıyası
            # BİLEREK yok: karşılaştırılabilir digest borusu `dbmigrate`tedir ve store'un onu
            # import etmesi katman sözleşmesini (çekirdek-altyapı → üst katman, geçişli
            # barrepair→…→watchdog zinciri) deler; kopyalamak ise iki digest'in sessiz ayrışması
            # olurdu. Arşiv baytları AYNEN korunduğu için digest sonradan her an alınabilir —
            # ölçülmeyen şey burada None/eksik değil, ertelenmiş ve dosyada saklı.
            st = p.stat()
            hedef = p.with_name(name + storage.MIGRATED_SUFFIX)
            if hedef.exists():
                hedef = p.with_name(name + storage.MIGRATED_SUFFIX + "-"
                                    + _time.strftime("%Y%m%d-%H%M%S") + f"-p{os.getpid()}")
            p.rename(hedef)
            arsivlenen.append({"dosya": name, "hedef": hedef.name,
                               "boyut": st.st_size, "dosya_mtime": st.st_mtime,
                               "kaynak_digest": m.get("source_digest")})
        except OSError as e:
            if (_state() / name).exists():
                hatalar.append(f"{name}: {type(e).__name__}: {e}")
            # dosya artık yoksa yarışı eşzamanlı bir süreç kazandı — arşivleme ZATEN oldu,
            # bu bir hata değil sonucun kendisidir; kayda geçecek ayrıca bir şey kalmadı
    if not (arsivlenen or gocsuz or hatalar):
        return
    try:
        from . import obs
        if arsivlenen or hatalar:
            obs.warn("bayat_defter_arsivlendi",
                     arsivlenen=arsivlenen, hatalar=hatalar or None,
                     detail="DB devredeyken kanonik adda duran göç-edilmiş defter dosyaları "
                            ".migrated disiplinine çekildi — okuma yolu zaten DB-otoriterdi, bu "
                            "dosyaları yalnız insan ve harici araç okuyordu (bayat-defter "
                            "tuzağı, ROADMAP §2-6; hiçbir dosya silinmedi/ezilmedi)")
        if gocsuz:
            obs.warn("db_aktif_kanonik_dosya_gocsuz", dosyalar=gocsuz,
                     detail="DB devrede AMA bu adların kanonik dosyası migrated_at damgası "
                            "OLMADAN duruyor: içeriğinin DB'ye taşındığı kanıtlanmadı — "
                            ".migrated denMEDİ (uydurma olurdu) ve dosya store okuyucularına "
                            "görünmez; operatör içeriği ya dbmigrate ile taşımalı ya bilinçli "
                            "kaldırmalı")
    except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — arşivleme diskte zaten uygulandı; kayıt denemesi bir okuma yolunu düşüremez
        pass


def sanitize(obj: Any) -> Any:
    """Recursively convert numpy scalars/arrays to native python for JSON.

    SONLU OLMAYAN FLOAT → None. Eski hâli np tiplerini çeviriyor ama NaN/±Inf'i OLDUĞU
    GİBİ geçiriyordu; oysa JSON'da böyle bir değer YOKTUR ve bu iki yerde birden patlar:
      * telde: Starlette `JSONResponse` gövdeyi `allow_nan=False` ile dump eder → tek bir NaN ucun
        tamamını HTTP 500'e çevirir (numpy sızıntısının yaptığının aynısı, başka kapıdan);
      * diskte: `json.dumps` varsayılanı `NaN` YAZAR, ama tarayıcıdaki `JSON.parse` onu reddeder →
        pano dosyayı hiç okuyamaz.
    NaN'ı geçiren bir sigorta sigorta değildir. Ayrıca NaN "ölçülemedi" demektir ve bu depoda
    ölçülmeyenin dürüst temsili None'dır (UYDURMA YASAĞI): 0.0'a ya da başka bir sayıya çevirmek
    okura ölçülmemiş bir değeri ölçülmüş gibi gösterirdi.
    """
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, (np.floating,)):
        f = float(obj)
        return f if math.isfinite(f) else None
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return [sanitize(v) for v in obj.tolist()]
    # YERLİ float ayrı bir daldır ve np dallarından SONRA gelir: `np.float64` Python `float`ın alt
    # sınıfıdır, yani bu kontrol yukarı taşınsaydı np dalını gölgeler ve `np.float32` gibi float
    # OLMAYAN np tipleri sessizce elenirdi. Buradaki iş yalnız `float("nan")`/`float("inf")`:
    # numpy'ye hiç uğramadan (ör. sıfıra bölme koruması, dışarıdan gelen JSON) doğan sonsuzluklar.
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj


# Faz 1 (öneri 4c): atomik yazım gecikme telemetrisi. Disk darboğazı mkstemp+os.replace süresini
# uzatır — bu sessiz kalmamalı. Son 200 yazımın süresi tutulur; p95 > 50 ms olursa BİR KEZ uyarılır
# (obs kendisi de buradan yazar — warned bayrağı özyinelemeyi keser).
import time as _time
_IO = {"n": 0, "recent": [], "warned": False}


def _record_io(ms: float) -> None:
    _IO["n"] += 1
    r = _IO["recent"]
    r.append(ms)
    if len(r) > 200:
        del r[:len(r) - 200]
    if not _IO["warned"] and len(r) >= 20:
        srt = sorted(r)
        if srt[int(len(srt) * 0.95) - 1] > 50.0:
            _IO["warned"] = True
            try:
                from . import obs
                obs.warn("io_latency_high", p95_ms=round(srt[int(len(srt) * 0.95) - 1], 1), n=_IO["n"])
            except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
                pass


def io_stats() -> dict:
    r = sorted(_IO["recent"])
    return {"writes": _IO["n"], "recent_n": len(r),
            "p50_ms": round(r[len(r) // 2], 2) if r else None,
            "p95_ms": round(r[int(len(r) * 0.95) - 1], 2) if len(r) >= 20 else None,
            "max_ms": round(max(r), 2) if r else None}


_CORRUPT_SEEN: set = set()      # dosya başına BİR kez uyar (turu 34)

# ---- DOSYA BAŞINA OKU-DEĞİŞTİR-YAZ KİLİDİ ----
# BULGU: portfolio.json'u İKİ iş parçacığı yazıyordu — zamanlayıcı (daily_cycle) ve Hermes
# (LLM görüş damgası). Kilit yoktu: damga, döngünün ARADA yazdığı defteri (silahlı set, pozisyonlar,
# nakit) BAYAT bir kopyayla geri alabilirdi. memory.py'de aynı desen veri kaybettirmişti;
# burada kaybedilecek şey CANLI DEFTER. Aynı süreçteki iş parçacıkları için RLock yeterli.
#
# SÜREÇLER ARASI KATMAN: RLock süreç-içiydi ve bu depoda BELGELİ bir tehlike
# sınıfıydı — canlı worker, pano API'si ve sprint AYNI dosyalara yazabiliyor; `update_scoreboard`
# gibi oku-değiştir-yaz yazarları kilitsizdi. `fcntl.flock` aynı kilidi süreçler arasına taşır:
# API aynı, çağıran aynı, garanti farklı. RLock KALIR (aynı süreçteki iplikler için flock YETMEZ:
# flock tanıtıcı başınadır ve aynı süreçte ikinci bir kilitleme anında geçer).
import threading as _th
_FILE_LOCKS: dict = {}
_LOCKS_GUARD = _th.Lock()
_FLOCK_WARNED: set = set()


class _FileLock:
    """`with store.file_lock(ad):` — süreç-içi RLock + süreçler-arası flock.

    Kilit dosyası `state/.locks/<ad>.lock`tur ve VERİ dosyasının kendisine kilitlenmez: veri
    dosyası `os.replace` ile yer değiştirdiği için inode'u değişir, ve inode'a bağlı bir flock
    yer değiştirmeden sonra BAŞKA bir dosyayı kilitliyor olurdu — yani kilit sessizce hiçbir şeyi
    korumazdı. Ayrı bir kilit dosyası bu sınıfı yapısal olarak kapatır.

    KİLİT DOSYASI TEMBEL AÇILIR: `file_lock(ad)` yalnız nesneyi verir, hiçbir bayt yazmaz
    (testlerdeki kimlik iddiası ve canlı-state sızıntı bekçisi bu davranışa bağlı)."""

    __slots__ = ("name", "_rlock", "_depth", "_fd", "_dir")

    def __init__(self, name: str, lock_dir: Path):
        self.name = name
        self._rlock = _th.RLock()
        self._depth = 0
        self._fd: int | None = None
        self._dir = lock_dir

    def _lock_path(self) -> Path:
        return self._dir / (str(self.name).replace(os.sep, "_") + ".lock")

    def acquire(self, blocking: bool = True, timeout: float = -1) -> bool:
        if not self._rlock.acquire(blocking, timeout):
            return False
        if self._depth == 0:
            try:
                self._dir.mkdir(parents=True, exist_ok=True)
                fd = os.open(str(self._lock_path()), os.O_RDWR | os.O_CREAT, 0o644)
                fcntl.flock(fd, fcntl.LOCK_EX)
                self._fd = fd
            except OSError as e:
                # SÜREÇLER-ARASI katman kurulamadı (salt-okunur dizin, NFS, fd tükenmesi).
                # Süreç-İÇİ kilit yine de tutuluyor — yani eski davranışa düşülür, kilitsiz
                # kalınmaz. Sessiz kalırsa "kilit var" iddiası ölçülmemiş olur; bir kez uyarılır.
                if self.name not in _FLOCK_WARNED:
                    _FLOCK_WARNED.add(self.name)
                    try:
                        from . import obs
                        obs.warn("file_lock_flock_unavailable", file=str(self.name),
                                 error=f"{type(e).__name__}: {e}",
                                 detail="süreçler-arası kilit kurulamadı — süreç-İÇİ RLock'a düşüldü")
                    except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
                        pass
                self._fd = None
        self._depth += 1
        return True

    def release(self) -> None:
        self._depth -= 1
        if self._depth == 0 and self._fd is not None:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
                os.close(self._fd)
            except OSError:  # sessiz-yutma: kilit tanıtıcısı zaten kapanmış/geçersiz; süreç sonu onu her hâlükârda toplar ve bırakma denemesi çağıranı düşüremez
                pass
            self._fd = None
        self._rlock.release()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *exc):
        self.release()
        return False


def file_lock(name: str):
    """Ada göre TEK kilit nesnesi. Anahtar (state_dizini, ad): ölçüm sandbox'ları `config.STATE`i
    değiştirir ve iki ayrı sandbox'ın aynı adı AYNI kilide düşerse testler birbirini bekletirdi."""
    key = (str(_state()), str(name))
    with _LOCKS_GUARD:
        lk = _FILE_LOCKS.get(key)
        if lk is None:
            lk = _FileLock(name, Path(_state()) / ".locks")
            _FILE_LOCKS[key] = lk
        return lk


# ---- .LOCKS BUDAMASI ------------------------------------------------
def kilit_budamasi(lock_dir: Path | str | None = None, max_yas_saat: float = 24.0) -> dict:
    """`state/.locks` altındaki ESKİ ve SERBEST kilit dosyalarını budar; sonucu raporlar.

    NEDEN VAR (ölçüldü): pytest sandbox'ları MUTLAK tmp yollarını
    kilitleyince `.locks/` altında oturum-başına-benzersiz hash'li adlar birikir (tek koşu +2,
    budama yoktu → sınırsız birikinti). Kilit dosyası içerik taşımaz; tek tehlike YANLIŞ SİLMEdir:

      * TUTULAN kilidi silmek DIŞLAMAYI KIRAR: yol silinince bir sonraki `open(O_CREAT)` YENİ bir
        inode yaratır; eski fd'nin flock'u ile yenisininki artık FARKLI dosyaları kilitler ve iki
        "sahip" aynı anda içeride olur. Bu yüzden yalnız NON-BLOCKING flock ALINABİLEN dosya aday
        olur ve silme KİLİT ELDEYKEN yapılır — aday seçildikten sonra kilitlenen yarışçı, biz
        flock'u tutarken `acquire` içinde BEKLER, dosyayı yeniden yaratamaz.
      * `_FileLock.release()` fd'yi KAPATIR (depth→0), yani serbest kilidin askıda açık fd'si
        kalmaz — non-blocking flock testi bu depoda "canlı mı" sorusunun DOĞRU ölçümüdür (flock(2):
        aynı süreçte bile ayrı open'lar birbirini dışlar, test v234 bunu ölçer).
      * mtime BURADA DOĞUM zamanıdır: kilit dosyasına hiç bayt yazılmaz, open/flock mtime'ı
        İLERLETMEZ. Yani yaş eşiği "son kullanımdan beri" DEĞİL "yaratılıştan beri" ölçer — ad-sabit
        canlı kilitler (portfolio.json.lock) aktif kullanılırken bile ESKİ görünür. pytest-tmp
        adları ise oturumla doğar ve bir daha ASLA yeniden kullanılmaz; yaş yalnız orada gerçek
        ölülük ölçüsüdür. Bu asimetri, budamanın NEREDEN tetiklendiğini belirler (aşağıda).

    KONUM KARARI: MEKANİZMA burada (`.locks` yerleşiminin sahibi store'dur; birim-testlenebilir),
    TETİK YALNIZ `tests/conftest.py` oturum-sonu kancasında (yalnız xdist-kontrolcüsü). Canlı
    worker başlangıcına BİLEREK bağlanmadı: canlının `.locks`'u sınırlı bir ad kümesidir (pytest
    çöpü orada doğmaz → budanacak birikinti yok) ve worker+pano API'nin eşzamanlı systemd açılışında
    sil/yeniden-yarat yarış penceresi açmak, SIFIR kazanca karşılık dışlama riski satın almak
    olurdu. Ops betiği de gerekmez: birikinti tam olarak pytest'in koştuğu makinede doğar.

    DOKUNMADIKLARI: `.lock` uzantısız her şey, alt dizinler, `state/.reflect.lock` gibi `.locks`
    DIŞI kilitler, genç dosyalar, flock'u alınamayanlar, açılamayanlar (güvenli taraf: kalır).

    DÖNÜŞ (okuyucusu: conftest özet satırı + v234 testleri):
    {dizin, tarandi, budandi[], tutulan, genc, degisen, hata}."""
    d = Path(lock_dir) if lock_dir is not None else Path(_state()) / ".locks"
    rapor: dict = {"dizin": str(d), "tarandi": 0, "budandi": [],
                   "tutulan": 0, "genc": 0, "degisen": 0, "hata": 0}
    if not d.is_dir():
        return rapor
    esik = _time.time() - max_yas_saat * 3600.0
    for p in sorted(d.iterdir()):
        if not p.name.endswith(".lock") or not p.is_file():
            continue
        rapor["tarandi"] += 1
        try:
            st = p.stat()
        except OSError:  # sessiz-yutma: sayaçlı — dosya tarama ile stat arasında kaybolduysa budanacak bir şey de kalmadı; `hata` sayacı raporda okunur, budayıcı düşmez
            rapor["hata"] += 1
            continue
        if st.st_mtime > esik:
            rapor["genc"] += 1
            continue
        try:
            fd = os.open(str(p), os.O_RDWR)     # O_CREAT BİLEREK YOK: budayıcı kilit dosyası YARATMAZ
        except OSError:  # sessiz-yutma: sayaçlı — açılamayan dosyaya (erişim yok / yarışta kayboldu) DOKUNULMAZ; güvenli taraf silmemektir ve `hata` sayacı raporda okunur
            rapor["hata"] += 1
            continue
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:  # sessiz-yutma: sayaçlı — flock alınamadı, kilit CANLI (bir süreç tutuyor); budamak dışlamayı kırardı, dosyaya DOKUNULMAZ ve `tutulan` sayacı raporda okunur
            rapor["tutulan"] += 1
            try:
                os.close(fd)
            except OSError:  # sessiz-yutma: kapatılamayan tanıtıcıyı süreç sonu toplar; sayım yukarıda zaten yapıldı ve budayıcı bir sonraki dosyaya geçebilir
                pass
            continue
        try:
            # Kilit ELDEYKEN doğrula ve sil: yol hâlâ AYNI inode mu? (stat→open arasında dosya
            # değiştirildiyse elimizdeki flock BAŞKA bir dosyanın kilididir — silmek yanlış
            # dosyayı silmek olurdu.)
            if os.fstat(fd).st_ino == os.stat(str(p)).st_ino:
                os.unlink(str(p))
                rapor["budandi"].append(p.name)
            else:
                rapor["degisen"] += 1
        except OSError:  # sessiz-yutma: sayaçlı — sil/stat düşerse dosya YERİNDE KALIR (güvenli taraf silmemektir) ve `hata` sayacı raporda okuyucuya bunu söyler
            rapor["hata"] += 1
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
                os.close(fd)
            except OSError:  # sessiz-yutma: bırakma/kapatma düşse de silme kararı verildi ve uygulandı; açık kalan tanıtıcıyı süreç sonu toplar
                pass
    return rapor


from . import provenance as _prov


def update_json(name: str, fn, default: Any = None) -> Any:
    """Kilitli oku-değiştir-yaz. fn(doc) belgeyi yerinde değiştirir ve True dönerse yazılır.
    İki yazar arasındaki kayıp-güncellemeyi yapısal olarak imkânsız kılar."""
    with file_lock(name):
        doc = read_json(name, default)
        changed = fn(doc)
        if changed:
            write_json(name, doc)
        return doc


def update_jsonl(name: str, fn) -> list:
    """JSONL için aynı disiplin: kilit altında oku, değiştir, (gerekirse) yaz."""
    with file_lock(name):
        rows = read_jsonl(name)
        changed = fn(rows)
        if changed:
            write_jsonl(name, rows)
        return rows


def _atomic_write(path: Path, data: str) -> None:
    """TEK ATOMİK YAZIM YOLU (B1): tmp → write → fsync → os.replace → dizin fsync.

    Eskiden fsync YOKTU: `os.replace` yer değiştirmenin atomik olduğunu söyler, verinin diske
    indiğini SÖYLEMEZ. Güç kesintisi/kernel panic sonrası dosya VAR ama içi boş olabilirdi ve
    `read_json` onu "bozuk dosya → varsayılan" diye yutardı (defter BOŞ görünürdü). Bütün
    yazarlar bu tek boğazdan geçtiği için sertleşme bedavaya yayılır."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)   # atomic
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:  # sessiz-yutma: en iyi çaba temizlik; geçici dosya zaten yoksa yapacak bir şey yok ve asıl istisna yukarı çıkmaya devam eder
            pass
        raise
    try:
        dfd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    except OSError:  # sessiz-yutma: dizin fsync'i EN İYİ ÇABAdır (bazı dosya sistemleri dizin fd'sine fsync kabul etmez); dosyanın KENDİ fsync'i yukarıda garanti edildi, kayıp yarım-yazım değil en fazla yer değiştirmenin gecikmiş kalıcılığıdır
        pass


# ================================================================================================
# KİLİT ARTIK KAPININ İÇİNDE, ÇAĞIRANIN ELİNDE DEĞİL
# ================================================================================================
# ÖNCESİ: `_atomic_write` yalnız ATOMİKLİK veriyordu; flock'u ÇAĞIRAN alırdı (`update_json`,
# `update_jsonl`, `merge_dated_jsonl`). Yani kilit bir SÖZLEŞMEydi, YAPISAL bir garanti değil —
# ve bu depoda böyle sözleşmelerin nasıl bittiği ölçülmüştü: `update_scoreboard` kilitsiz yazıyordu
# (bkz. karne yazım güvenliği notu). Çıplak `write_json` çağıran her yol aynı boşluktaydı.
# Kilit KAPIYA indi: artık kilitsiz yazmak için store'u BYPASS etmek gerekir, ki [0c]/[0d] sınıfı
# kapılar tam olarak onu görünür kılar.
#
# NEDEN `db_backed` DALINDA FLOCK YOK — İKİ KİLİT REJİMİ BİRBİRİNE KARIŞTIRILMAZ: DB'ye giden ad
# zaten SQLite'ın süreçler-arası kilidiyle (WAL + `busy_timeout`) korunur. Üstüne flock
# koymak ikinci bir kilit SIRASI doğururdu (flock→SQLite burada, SQLite→flock `dbmigrate`in tek
# transaction'ında) ve iki farklı sırayla alınan iki kilit kilitlenmenin tanımıdır. Her ad TEK
# rejimde yaşar: dosya arka ucu → flock, DB arka ucu → SQLite. Sınır `db_backed`tir.
#
# YENİDEN GİRİŞ GÜVENLİ: `_FileLock` RLock+derinlik taşır, yani `update_json` (kilidi ALMIŞ) →
# `write_json` (aynı adı yeniden alır) zinciri kendini bloklamaz — bu zaten bugünkü sıcak yoldur.

def write_json(name: str, obj: Any) -> Path:
    t0 = _time.perf_counter()
    payload = sanitize(obj)
    if db_backed(name):
        storage.write_entity(name, payload)
        _record_io((_time.perf_counter() - t0) * 1000.0)
        return storage.db_path()
    path = _path(name)
    with file_lock(name):
        _atomic_write(path, json.dumps(payload, indent=2))
    _record_io((_time.perf_counter() - t0) * 1000.0)
    return path


def write_text(name: str, text: str) -> Path:
    """JSON OLMAYAN metin defterleri için AYNI TEK KAPI — atomik tmp+fsync+rename + flock.

    NEDEN VAR: `state/` altındaki her yazım JSON değildir ve
    JSON olmayanlar kapının DIŞINDA kalmıştı. Ölçülen kapı-dışı yollar aynı iki sınıfa düşüyordu:

      * ATOMİK OLMAYAN düz `write_text` — `memory.py` (`state/lessons.md`) ve `run.py`
        (`state/history/scoreboard-*.json` arşivi). Düz yazım dosyayı önce KIRPAR: okuyucu tam o
        anda gelirse yarım — hatta BOŞ — bir defter görür ve bu sessizce "ders yok" diye okunur.
      * ATOMİK ama HER YERDE YENİDEN YAZILMIŞ kalıp — `config.dump_yaml`, `earnings.py` (×2),
        `sprint_run._write_live_status`, `adapters/data._write_bars`, `auth._write`. Beşi de
        mkstemp+replace'i elle kurar; hiçbirinde `fsync` YOKTUR (B1'in kapattığı sıfır-baytlık
        dosya sınıfı bu kopyalarda hâlâ açık) ve hiçbiri flock ALMAZ. `auth._write` ayrıca SABİT
        bir tmp adı (`.json.tmp`) kullanır: iki süreç aynı anda yazarsa aynı geçici dosyaya
        yazarlar ve atomiklik iddiası orada biter.

    Kapıyı JSON'a özgü bırakmak, "tek kapı" iddiasını dosya UZANTISINA bağlamak olurdu; oysa
    korunan şey biçim değil DEFTERİN BÜTÜNLÜĞÜ. `write_json` ne veriyorsa bu da onu verir.

    DÖNÜŞ: yazılan yol. DB arka ucu YOKTUR: bu adlar (lessons.md, earnings.csv, strategy.yaml)
    varlık defteri değildir ve `storage`ta karşılıkları bulunmaz — `db_backed` dalı bilerek yok.
    """
    t0 = _time.perf_counter()
    path = _path(name)
    with file_lock(name):
        _atomic_write(path, text)
    _record_io((_time.perf_counter() - t0) * 1000.0)
    return path


def read_json(name: str, default: Any = None) -> Any:
    if db_backed(name):
        doc = storage.read_entity(name)
        return default if doc is None else _prov.sar(name, doc)
    path = _path(name)
    if not path.exists():
        return default
    try:
        with open(path) as f:
            # KÖKEN TAKİBİ: kapalıyken `sar` nesneyi olduğu gibi döndürür (sıfır maliyet).
            # Açıkken her .get()/[] okuması kaydedilir — bkz. meridian/provenance.py
            return _prov.sar(name, json.load(f))
    except (json.JSONDecodeError, OSError) as e:
        # a corrupt/unreadable state file must degrade to the default, never 500 an endpoint or kill a
        # cycle — writers are atomic, so this only fires on external damage (ops audit hardening).
        # AMA SESSİZ OLMAZ: portfolio.json bozulursa defter BOŞ görünür
        # ve motor pozisyonları yokmuş gibi davranır. "Varsayılana düştük" bir olay olarak kaydedilir;
        # dosya başına bir kez (log seli yok).
        if name not in _CORRUPT_SEEN:
            _CORRUPT_SEEN.add(name)
            try:
                from . import obs
                obs.warn("state_file_unreadable", file=str(name),
                         error=f"{type(e).__name__}", detail="varsayılana düşüldü — dosya bozuk olabilir")
            except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
                pass
        return default


def append_jsonl(name: str, row: dict) -> None:
    t0 = _time.perf_counter()
    payload = sanitize(row)
    if db_backed(name):
        storage.append_row(name, payload)
        _record_io((_time.perf_counter() - t0) * 1000.0)
        return
    path = _path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(payload) + "\n")
    _record_io((_time.perf_counter() - t0) * 1000.0)


def read_jsonl(name: str, limit: int | None = None) -> list[dict]:
    if db_backed(name):
        return _prov.sar(name, storage.read_rows(name, limit=limit))
    path = _path(name)
    if not path.exists():
        return []
    rows, bad = [], 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:  # sessiz-yutma: yardımcı G/Ç yolu; çağıran yokluğu zaten yedek değerle karşılıyor ve asıl okuma hatası store katmanında bir kez uyarılıyor
                    bad += 1
                    continue
    if bad and name not in _CORRUPT_SEEN:
        # BOZUK SATIR = SESSİZ VERİ KAYBI (turu 34): append_jsonl atomik değildir; çökme ya da disk
        # dolması yarım bir satır bırakır ve o işlem/plan/olay defterden sessizce düşerdi.
        _CORRUPT_SEEN.add(name)
        try:
            from . import obs
            obs.warn("jsonl_rows_skipped", file=str(name), skipped=bad, kept=len(rows))
        except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
            pass
    return _prov.sar(name, rows[-limit:] if limit else rows)


def merge_dated_jsonl(name: str, date_value: str, new_rows: list[dict], cap: int = 500) -> None:
    """Idempotent per-date write: drop any existing rows for date_value, append new_rows, keep the
    last `cap`. Lets candidates/plans accumulate a dated history without duplicating on re-run.

    KİLİT: bu bir OKU-DEĞİŞTİR-YAZdır ve kilitsizdi. `loop.daily_cycle` bunu
    `trade_plans.jsonl` için çağırırken Hermes'in görüş damgası (`update_jsonl`, KİLİTLİ) aynı
    deftere yazabiliyordu — kilitli taraf kilitsiz tarafı bekletemez, yani kilit tek taraflıysa
    kilit YOKTUR. Aynı ada bağlanır, böylece iki yol aynı sırayı paylaşır."""
    with file_lock(name):
        existing = [r for r in read_jsonl(name) if r.get("date") != date_value]
        write_jsonl(name, (existing + new_rows)[-cap:])


def write_jsonl(name: str, rows: list[dict]) -> None:
    if db_backed(name):
        storage.replace_rows(name, [sanitize(r) for r in rows])
        return
    path = _path(name)
    with file_lock(name):        # gerekçe write_json'ın üstündeki blokta
        _atomic_write(path, "".join(json.dumps(sanitize(r)) + "\n" for r in rows))


# ---- TAZELİK DAMGASI (dosya mtime'ının arka-uç bağımsız karşılığı) ------------------------------
# NEDEN VAR: beş yerde `(config.STATE / ad).stat()` ile ÖNBELLEK ANAHTARI ve TAZELİK ölçülüyordu
# (analytics._nd_stamp, shadow_model.dataset_fingerprint, intraday_cycle._planned,
# ledgerstamp._mtime, watchdog.coherence_report). Defter DB'ye taşındığında o dosyalar `.migrated`
# ekiyle DONAR: mtime bir daha ASLA değişmez, yani önbellek sonsuza kadar bayat kalır ve tazelik
# dedektörü "hiç güncellenmiyor" der. İkisi de SESSİZ yanlış cevaptır. Bu iki fonksiyon damgayı
# arka uçtan soyutlar; DB'de karşılığı `entity_meta.updated_at`/`rev`tir.
def stamp(name: str) -> tuple:
    """(değişim_damgası, boyut/revizyon) — yalnız İÇERİK değiştiğinde değişir. Yoksa (0, 0)."""
    if db_backed(name):
        return storage.stamp(name) or (0, 0)
    try:
        st = _path(name).stat()
        return (st.st_mtime_ns, st.st_size)
    except OSError:  # sessiz-yutma: defter henüz yok — damga sabit (0,0) ve bu KAYDA GEÇEN bir değerdir ("dosya yok" hâli), çağıran onu boş defterle aynı önbellek anahtarına eşler
        return (0, 0)


def mtime(name: str) -> float | None:
    """Son yazım zamanı (epoch sn) ya da ölçülemediyse None — arka uçtan bağımsız."""
    if db_backed(name):
        m = storage.meta(name)
        return float(m["updated_at"]) if m and m["present"] else None
    try:
        return _path(name).stat().st_mtime
    except OSError:  # sessiz-yutma: dosya yoksa/okunamıyorsa ÖLÇÜM YAPILAMADI demektir ve None tam olarak bunu söyler — çağıran onu "bilinmiyor" diye taşır, sıfır ya da şimdi UYDURULMAZ
        return None

"""barsarchive.py — `mrd:bars:{T}` akışlarının DAYANIKLI disk arşivcisi (kanıt katmanının ham maddesi).

NE YAPAR: `mrd:bars:*` Redis Stream'lerini KENDİ consumer-group'uyla (GROUP="archive") okur ve her
kapanmış dakikalık barı `state/bars_intraday/YYYY-MM-DD.jsonl` içine bir satır olarak düşürür.
`mrd:bars` bir RING'tir (BARS_MAXLEN=900, BARS_TTL_S≈2 seans) — TTL sonrası o dakika YOKTUR;
"dakika-hassas icra EOD'den iyi mi?" sorusu ancak geçmiş çerçeveler birikmişse cevaplanır, arşiv bu
yüzden ölçümden ÖNCE açılır. Ayrıca `summary()`/`render_summary()` arşiv istatistiği ile `gap_scan()`
seans-içi kesinti/boşluk dedektörünü (SAF ölçüm; kaydı çağıran scheduler yapar) barındırır.

KİLİT GİRİŞLER: BarsArchiver.poll() (tek tur; Redis yoksa None — "bar yoktu" ile "Redis yok" aynı
değer olamaz) / run() (uzun koşu), summary(), gap_scan(), CLI: `python -m meridian.barsarchive`
(--ozet / --bosluk / --once). Şema üreticiden TÜRETİLİR: BAR_FIELDS = hotstate._BAR_FIELDS,
ayrıştırma hotstate._bar_parse — alan listesi burada kopyalanmaz.

DEĞİŞMEZLER (atomik arşiv): SIRA fsync → XACK. Yazım başarısızsa ACK ATILMAZ; giriş PEL'de kalır,
yeniden teslim edilir ve diskten kurulan (ticker,t) günlük tekilleştirme kümesi çift satırı düşürür —
en-az-bir-kez teslim + idempotent yazım = pratikte tam-bir-kez arşiv. Grup `id="0"` ile kurulur
(barfeed'in "$" tetiğinden bilerek farklı: arşiv ring'de duran geçmişi de kurtarır, tetik replay
etmez). barfeed'den tam izole: farklı anahtar + grup durumu Redis'te grup başınadır; `mrd:*` altında
yalnız SCAN / XGROUP CREATE / XREADGROUP / XACK koşar, hiçbir XADD/DEL/EXPIRE yok — canlı worker'ın
akışına dokunmaz. TTL'li anahtarda grup ölümü (hafta sonu anahtar silinir, ilk bar grubu olmadan
yeniden yaratır) NOGROUP onarımıyla kendini toparlar; onarım sayılır ve uyarıyla görünür kılınır.
`t`siz giriş kimliksizdir: sayılır, ACK'lenir (sonsuz yeniden-teslim kilidi olmasın). Seans dışında
bekleme sunucu tarafındadır (XREADGROUP BLOCK); hiç akış yokken ucuz `idle_s` uykusu vardır.

OKUR/YAZAR: `mrd:bars:{T}` akışlarını okur/ACK'ler; `state/bars_intraday/*.jsonl`e doğrudan
open()+fsync ile yazar (store.append_jsonl fsync etmez — ACK öncesi dayanıklılık şart; bu dizine
YALNIZ bu modül yazar, tests/test_barsarchive_v116.py bunu kaynak taramasıyla çiviler). Komşu
`bararchive.py` (ad benzerliği devralındı) AYRI ve daha eski yoldur: ingest içinden çerçeve-şekilli
satırları BİR KEZ dener, başarısızsa çerçeve temelli kaybolur; bu modül ring kaynaklı olduğundan
yeniden dener — ikisi bilerek yan yana durur, birleştirme/emeklilik ayrı bir mimari karardır.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import time

from . import barclock, config, hotstate, obs

# --- Sabitler ------------------------------------------------------------------------------------
ARCHIVE_DIR = "bars_intraday"          # state/ altında; YALNIZ bu modül yazar (bkz. yazar tekliği)
GROUP = "archive"                      # barfeed'in "meridian-intraday" grubundan AYRI ve ayrı anahtarda
CONSUMER = os.environ.get("MERIDIAN_BARSARCHIVE_CONSUMER", "a1")
BARS_MATCH = hotstate.PREFIX + "bars:*"      # keşif deseni; PREFIX üreticiden ALINIR, kopyalanmaz
_KEY_PREFIX = hotstate.PREFIX + "bars:"

# XREADGROUP BLOCK'u hotstate.BLOCKING_SOCKET_TIMEOUT'tan KÜÇÜK olmalı, yoksa soket-timeout bloklu
# okumayı keser ve sahte "Redis down" churn'ü doğar (barfeed'in canlı restart'ta öğrendiği ders).
DEFAULT_POLL_MS = 2000
MAX_POLL_MS = int(hotstate.BLOCKING_SOCKET_TIMEOUT * 1000) - 500
DEFAULT_IDLE_S = 5.0                   # hiç akış yokken (seans dışı / taze kurulum) tur arası uyku
DEFAULT_COUNT = 500                    # tur başına akış başına en fazla giriş


def archive_dir():
    """Arşiv dizini. ÇAĞRI ANINDA hesaplanır — `config.STATE` testlerde sandbox'a yamalanır; modül
    yükleme anında dondurmak testleri canlı `state/`e yazdırırdı (conftest bekçisinin tam konusu)."""
    return config.STATE / ARCHIVE_DIR


def _day_path(day: str):
    return archive_dir() / f"{day}.jsonl"


def _ticker_of(key: str) -> str:
    """`mrd:bars:AAPL` → `AAPL`. Önek üreticiden türetilir; ayrıştırma varsayıma dayanmaz."""
    return key[len(_KEY_PREFIX):] if key.startswith(_KEY_PREFIX) else key


# --- Şema ----------------------------------------------------------------------------------------
# UYDURMA YASAĞI: alan listesi BURADA TANIMLANMAZ, üreticiden ALINIR. `hotstate._BAR_FIELDS` XADD'e
# giden alanların TEK kaynağıdır (`_bar_wire` onu kullanır); ayrıştırma da üreticinin kendi
# `_bar_parse`'ıdır (sayısal alanlar float'a, `t` dize damga olarak kalır). Böylece şema kopyalanmaz,
# TÜRETİLİR — hotstate şemayı değiştirirse burası kendiliğinden takip eder ve v116 testi çakılır.
BAR_FIELDS = tuple(hotstate._BAR_FIELDS)          # ("o","h","l","c","v","vw","n","t")


def _row(ticker: str, fields: dict) -> dict | None:
    """Bir XREADGROUP girişini arşiv satırına çevir. `t` YOKSA None döner.

    `t` ZORUNLUDUR ve bu keyfi değildir: (a) gün dosyasını `t[:10]` belirler, (b) tekilleştirme
    anahtarı (ticker,t)'dir, (c) look-ahead sözleşmesi close_ts=t+60s'e dayanır (hotstate:238).
    `t`siz bir giriş arşivde kimliksizdir — sayılır ve raporlanır, sessizce yutulmaz."""
    bar = hotstate._bar_parse(fields)
    t = bar.get("t")
    if not t:
        return None
    row = {"ticker": ticker}
    for k in BAR_FIELDS:
        if k in bar:                   # `_bar_wire` None alanları düşürür → yokluk NORMALDİR, uydurulmaz
            row[k] = bar[k]
    return row


# --- Tekilleştirme -------------------------------------------------------------------------------
class _DayIndex:
    """Tek bir gün dosyası için (ticker,t) kümesi + açık dosya tanıtıcısı.

    KÜME DİSKTEN KURULUR, bellekten DEĞİL: yeniden başlatmada süreç belleği sıfırlanır ama dosya
    durur. PEL'de bekleyen (çökme öncesi yazılmış ama ACK'lenmemiş) girişler yeniden teslim edilir;
    diskten kurulan küme onları ÇİFT SATIR yazmadan düşürür. İdempotensin çalıştığı yer burasıdır."""

    def __init__(self, day: str):
        self.day = day
        self.seen: set[tuple[str, str]] = set()
        self.loaded_rows = 0
        self._fh = None
        path = _day_path(day)
        if path.exists():
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:  # sessiz-yutma: yarım satır (çökme/disk dolması) bir ÖNCEKİ koşunun kalıntısıdır; o bar ACK'lenmemiştir, yeniden teslim edilip yeniden yazılacaktır — burada uyarmak aynı olayı iki kez anlatırdı
                        continue
                    tk, t = rec.get("ticker"), rec.get("t")
                    if tk and t:
                        self.seen.add((str(tk), str(t)))
                    self.loaded_rows += 1

    def _handle(self):
        if self._fh is None:
            path = _day_path(self.day)
            path.parent.mkdir(parents=True, exist_ok=True)
            self._fh = open(path, "a")
        return self._fh

    def write(self, rows: list[dict]) -> int:
        """Yeni satırları yaz + fsync. Yazılan sayıyı döner. İSTİSNAYI YUTMAZ — çağıran ACK atmamalı."""
        if not rows:
            return 0
        fh = self._handle()
        for r in rows:
            fh.write(json.dumps(r) + "\n")
        fh.flush()
        os.fsync(fh.fileno())          # ACK'ten ÖNCE dayanıklılık; fsync'siz ACK crash-safe DEĞİLDİR
        for r in rows:
            self.seen.add((str(r["ticker"]), str(r["t"])))
        return len(rows)

    def close(self) -> None:
        if self._fh is not None:
            try:
                self._fh.close()
            except OSError:  # sessiz-yutma: kapatma hatası zaten fsync'lenmiş veriyi geri almaz; kapanışta ikinci bir kanal yok
                pass
            self._fh = None


class BarsArchiver:
    """`mrd:bars:*` → disk arşivcisi. `poll()` tek tur; `run()` uzun-koşan döngü."""

    def __init__(self, poll_ms: int = DEFAULT_POLL_MS, idle_s: float = DEFAULT_IDLE_S,
                 count: int = DEFAULT_COUNT, consumer: str = CONSUMER):
        self.poll_ms = max(100, min(int(poll_ms), MAX_POLL_MS))
        self.idle_s = float(idle_s)
        self.count = int(count)
        self.consumer = consumer
        self._days: dict[str, _DayIndex] = {}
        self._groups: set[str] = set()      # grubu kurulmuş akış anahtarları (tur başına XGROUP spam'i yok)
        self._drained: set[str] = set()     # PEL'i (id="0") bir kez tahliye edilmiş akışlar
        self._stop = False
        # Kümülatif sayaçlar — YASA 4: "hiç yazmadım" ile "Redis yok" ayırt edilebilir kalmalı.
        self.polls = 0
        self.read = 0
        self.written = 0
        self.duplicate = 0
        self.skipped_no_t = 0
        self.acked = 0
        self.write_failures = 0
        self.group_resets = 0               # NOGROUP onarımı kaç kez işledi (YASA 4: sessiz onarım yok)
        self.last_error: str = ""
        self.last_write_at: str | None = None

    # -- yardımcılar -------------------------------------------------------------------------
    def _index(self, day: str) -> _DayIndex:
        """Gün indeksini getir; GÜN ROTASYONU burada olur — yeni gün ilk satırında açılır, eskisi
        kapatılır (açık tanıtıcıları sonsuza dek biriktirmemek için)."""
        idx = self._days.get(day)
        if idx is None:
            for d, old in list(self._days.items()):
                if d != day:
                    old.close()
                    self._days.pop(d, None)
            idx = _DayIndex(day)
            self._days[day] = idx
        return idx

    def _streams(self, r) -> list[str]:
        """`mrd:bars:*` anahtarlarını keşfet. SCAN — KEYS üretimi bloklar (hotstate'in aynı dersi)."""
        return sorted(r.scan_iter(match=BARS_MATCH, count=500))

    def _ensure_group(self, r, key: str) -> None:
        """Grubu kur (idempotent). `id="0"` → ring'de HÂLÂ duran geçmiş de arşive girer. Zaten varsa
        BUSYGROUP döner ve bu bir hata DEĞİLDİR; başka her istisna görünür kılınır (YASA 4)."""
        if key in self._groups:
            return
        try:
            r.xgroup_create(name=key, groupname=GROUP, id="0", mkstream=True)
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                self.last_error = f"{type(e).__name__}: {str(e)[:120]}"
                obs.warn("bars_archive_group_failed", stream=key, group=GROUP, error=self.last_error,
                         detail="consumer-group kurulamadı — bu akış BU TURDA arşivlenmez, ring'de "
                                "TTL'ine kadar durur (sonraki tur yeniden dener)")
                return
        self._groups.add(key)

    def _forget_nogroup(self, err: Exception, keys: list[str]) -> list[str]:
        """NOGROUP ONARIMI (kopukluk avı) — TTL'li anahtarda GRUP ÖLÜMÜ.

        VAKA: `mrd:bars:{T}` anahtarının TTL'i (BARS_TTL_S = 2 gün) hafta sonu dolar → anahtar SİLİNİR
        ve consumer-group'u onunla birlikte ölür. Pazartesi ilk bar XADD ile anahtarı YENİDEN yaratır
        ama grup YOKTUR. `_ensure_group` ise anahtarı `_groups` kümesinde gördüğü için ERKEN DÖNER
        (idempotence optimizasyonu) ve XREADGROUP her turda `NOGROUP` hatası verir. Sonuç: o akış
        SÜREÇ YENİDEN BAŞLATILANA KADAR arşivlenmez. Üstelik yeni-giriş okuması TÜM akışları tek
        XREADGROUP'ta istediği için, TEK ölü grup bütün turu düşürüyordu.

        ONARIM: istisna NOGROUP ise etkilenen anahtarları `_groups`/`_drained`'ten DÜŞÜR — bir sonraki
        tur `_ensure_group`'u yeniden çağırır, grup `id="0"` ile kurulur ve ring'de duran barlar da
        arşive girer. Yeniden kurmak idempotenttir (BUSYGROUP zararsız), o yüzden anahtar adı hata
        metninden ÇÖZÜLEMEZSE tur içindeki tüm canlı anahtarlar unutulur — muhafazakâr taraf, çünkü
        gereksiz bir XGROUP CREATE bedava, kaçırılmış bir onarım ise sessiz veri kaybıdır.

        Onarımın kendisi SESSİZ DEĞİLDİR: `group_resets` sayacı + uyarı. "Kendini onardı" cümlesi
        sayılmadıkça bir iddiadır; sayıldığında hafta sonu grup ölümünün SIKLIĞI ölçülebilir olur."""
        if "NOGROUP" not in str(err):
            return []
        hit = [k for k in keys if k in str(err)] or list(keys)
        for k in hit:
            self._groups.discard(k)
            self._drained.discard(k)
        self.group_resets += len(hit)
        obs.warn("bars_archive_group_reset", streams=len(hit), first=hit[0] if hit else None,
                 resolved_from_error=bool([k for k in keys if k in str(err)]),
                 detail="NOGROUP — TTL'li anahtarda grup öldü (hafta sonu/flush); grup kaydı düşürüldü, "
                        "sonraki tur id=0 ile yeniden kurar ve ring'de duran barlar arşive girer")
        return hit

    def _consume(self, r, batch, ack: bool = True) -> None:
        """XREADGROUP sonucunu diske düşür ve YALNIZ yazımı BAŞARILI olanları ACK'le.

        SIRA KRİTİKTİR: fsync → XACK. Ters sırada bir çökme, ACK'lenmiş ama diskte olmayan bir barı
        TEMELLİ kaybettirirdi (Redis onu bir daha teslim etmez). Yazım patlarsa ACK ATILMAZ: giriş
        PEL'de kalır ve sonraki turda yeniden teslim edilir — kayıp yerine tekrar, tekrar da
        tekilleştirmeyle zararsızdır."""
        for key, entries in batch:
            ticker = _ticker_of(key)
            per_day: dict[str, list] = {}
            ack_ids: list[str] = []
            for _id, fields in entries:
                self.read += 1
                row = _row(ticker, fields)
                if row is None:
                    # `t`siz giriş: arşivde kimliksizdir. ACK'lenir — aksi hâlde PEL'de sonsuza dek
                    # birikir ve her turda yeniden işlenirdi (sonsuz yeniden-teslim kilidi).
                    self.skipped_no_t += 1
                    ack_ids.append(_id)
                    continue
                day = str(row["t"])[:10]
                per_day.setdefault(day, []).append((_id, row))
            for day, items in per_day.items():
                idx = self._index(day)
                fresh, ids = [], []
                for _id, row in items:
                    ids.append(_id)
                    k = (row["ticker"], str(row["t"]))
                    if k in idx.seen:
                        self.duplicate += 1      # yeniden teslim ya da yeniden başlatma — çift satır YOK
                        continue
                    fresh.append(row)
                try:
                    n = idx.write(fresh)
                except Exception as e:
                    # ACK YOK. Bu satırlar PEL'de kalır ve sonraki turda yeniden denenir.
                    self.write_failures += 1
                    self.last_error = f"{type(e).__name__}: {str(e)[:120]}"
                    obs.warn("bars_archive_write_failed", day=day, ticker=ticker, rows=len(fresh),
                             error=self.last_error,
                             detail="diske yazılamadı — ACK ATILMADI, giriş PEL'de kaldı ve yeniden "
                                    "denenecek; kayıp YOK, arşiv bu tur ilerlemedi")
                    continue
                self.written += n
                if n:
                    self.last_write_at = _now_iso()
                ack_ids.extend(ids)
            if ack and ack_ids:
                try:
                    self.acked += int(r.xack(key, GROUP, *ack_ids) or 0)
                except Exception as e:
                    # ACK düştü: satırlar DİSKTE. Yeniden teslim gelirse tekilleştirme düşürür.
                    self.last_error = f"{type(e).__name__}: {str(e)[:120]}"
                    obs.warn("bars_archive_ack_failed", stream=key, count=len(ack_ids),
                             error=self.last_error,
                             detail="XACK başarısız — satırlar DİSKE YAZILDI, giriş PEL'de kaldı; "
                                    "yeniden teslimde tekilleştirme çift satırı önler")

    # -- tek tur -----------------------------------------------------------------------------
    def poll(self) -> dict | None:
        """Bir tur oku-yaz-ACK. Redis YOKSA `None` döner (YASA 4: "yazacak bar yoktu" ile "Redis'e
        ulaşamadım" AYNI ŞEY DEĞİLDİR ve aynı değeri dönemez). Redis varsa akış boş olsa bile bir
        SÖZLÜK döner — sıfırlar dürüst bir ölçümdür."""
        r = hotstate._blocking_redis()
        if r is None:
            return None
        self.polls += 1
        # TUR DELTASI için başlangıç: dönen sözlüğün HER alanı "bu turda" anlamına gelir. Kümülatif
        # toplamlar `snapshot()`tadır. İkisini tek sözlükte karıştırmak, `--once` çıktısını okuyan
        # birine "bu turda 900 bar atladım" dedirtirdi — oysa sayı bütün koşunun toplamıdır.
        before = (self.read, self.written, self.duplicate, self.acked, self.skipped_no_t)
        try:
            keys = self._streams(r)
        except Exception as e:
            self.last_error = f"{type(e).__name__}: {str(e)[:120]}"
            obs.warn("bars_archive_scan_failed", error=self.last_error,
                     detail="mrd:bars:* keşfi başarısız — bu tur hiçbir akış okunmadı")
            return None
        if not keys:
            # AKIŞ YOK (seans dışı taze kurulum / Redis flush). Boş sözlük değil, sıfırlı sözlük:
            # "0 akış gördüm" bir ölçümdür, "Redis yok" (None) değildir.
            return {"streams": 0, "read": 0, "written": 0, "duplicate": 0,
                    "skipped_no_t": 0, "acked": 0, "idle": True}
        for k in keys:
            self._ensure_group(r, k)
        live = [k for k in keys if k in self._groups]
        if not live:
            return {"streams": len(keys), "read": 0, "written": 0, "duplicate": 0,
                    "skipped_no_t": 0, "acked": 0, "idle": True}
        # (1) PEL TAHLİYESİ: id="0" bu tüketiciye teslim edilmiş ama ACK'lenmemiş girişleri döner —
        # yani önceki koşu fsync ile ACK arasında çöktüyse o barlar BURADA kurtarılır. Akış başına
        # BİR KEZ; her turda yapmak seans boyu boşuna PEL taraması olurdu.
        todo = [k for k in live if k not in self._drained]
        if todo:
            try:
                pending = r.xreadgroup(groupname=GROUP, consumername=self.consumer,
                                       streams={k: "0" for k in todo}, count=self.count)
                if pending:
                    self._consume(r, pending)
            except Exception as e:
                self.last_error = f"{type(e).__name__}: {str(e)[:120]}"
                if not self._forget_nogroup(e, todo):
                    obs.warn("bars_archive_pending_failed", error=self.last_error,
                             detail="PEL tahliyesi başarısız — ACK'lenmemiş girişler PEL'de KALDI "
                                    "(kayıp yok); sonraki tur yeniden dener")
            else:
                self._drained.update(todo)
        # (2) YENİ GİRİŞLER: ">" yalnız hiç teslim edilmemişleri verir. BLOCK sunucu tarafında bekler —
        # seans dışında bu, meşgul döngü yerine tek bir bloklu soket okumasıdır (ucuz bekleme).
        try:
            batch = r.xreadgroup(groupname=GROUP, consumername=self.consumer,
                                 streams={k: ">" for k in live}, count=self.count,
                                 block=self.poll_ms)
            if batch:
                self._consume(r, batch)
        except Exception as e:
            self.last_error = f"{type(e).__name__}: {str(e)[:120]}"
            if not self._forget_nogroup(e, live):
                obs.warn("bars_archive_read_failed", error=self.last_error,
                         detail="XREADGROUP başarısız — bu turda bar okunmadı; girişler ring'de/PEL'de "
                                "durur, sonraki tur yeniden dener")
            return None
        d_read = self.read - before[0]
        return {"streams": len(live), "read": d_read, "written": self.written - before[1],
                "duplicate": self.duplicate - before[2],
                "skipped_no_t": self.skipped_no_t - before[4],
                "acked": self.acked - before[3], "idle": d_read == 0}

    # -- uzun koşu ---------------------------------------------------------------------------
    def run(self, max_polls: int | None = None) -> dict:
        """Uzun-koşan döngü. `max_polls` yalnız test/tek-atış içindir (None = sonsuz).

        UCUZ BEKLEME: akış varken bekleme XREADGROUP BLOCK ile SUNUCUDA yapılır (istemci uyanık
        döngü kurmaz). Akış hiç yokken ya da Redis düştüğünde `idle_s` uykusu vardır — Redis'i
        saniyede bir yeniden bağlanma denemesiyle dövmemek için."""
        self._stop = False
        n = 0
        started = _now_iso()
        while not self._stop and (max_polls is None or n < max_polls):
            n += 1
            res = self.poll()
            if res is None:
                # Redis yok/hatalı: görünür bekleme. `poll` zaten uyardı; burada susmak YASA 4 ihlali
                # değil — aynı olayı tur başına tekrarlamak olay defterini boğardı.
                self._sleep(self.idle_s)
                continue
            if res.get("streams", 0) == 0:
                self._sleep(self.idle_s)     # hiç akış yok → BLOCK yapılacak bir şey de yok
        self.close()
        return {"polls": n, "started_at": started, "stopped_at": _now_iso(), **self.snapshot()}

    def _sleep(self, s: float) -> None:
        """Testlerin yamalayabilmesi için tek nokta (uyku gerçek zamanı suite'e ödetmesin)."""
        time.sleep(s)

    def stop(self) -> None:
        self._stop = True

    def close(self) -> None:
        for idx in self._days.values():
            idx.close()
        self._days.clear()

    def snapshot(self) -> dict:
        return {"group": GROUP, "consumer": self.consumer, "polls": self.polls, "read": self.read,
                "written": self.written, "duplicate": self.duplicate,
                "skipped_no_t": self.skipped_no_t, "acked": self.acked,
                "write_failures": self.write_failures, "group_resets": self.group_resets,
                "last_write_at": self.last_write_at,
                "last_error": self.last_error or None}


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


# --- Arşiv istatistiği (YASA 6 tüketicisi) -------------------------------------------------------
def summary(limit_days: int | None = None) -> dict:
    """Diskteki arşivin ÖLÇÜMÜ: gün sayısı, satır sayısı, benzersiz sembol sayısı, tarih aralığı.

    Dizin YOKSA `exists=False` ve sıfırlar döner — "arşiv boş" ile "arşiv hiç açılmamış" farkı
    çağıranda görünür kalır (YASA 4). Bozuk satırlar SAYILIR ve raporlanır, sessizce atılmaz."""
    base = archive_dir()
    if not base.exists():
        return {"exists": False, "days": 0, "rows": 0, "symbols": 0, "bad_lines": 0,
                "first_day": None, "last_day": None, "bytes": 0, "per_day": [], "dir": str(base)}
    files = sorted(base.glob("*.jsonl"))
    if limit_days:
        files = files[-limit_days:]
    rows = bad = size = 0
    symbols: set[str] = set()
    per_day = []
    for p in files:
        d_rows = d_bad = 0
        d_syms: set[str] = set()
        size += p.stat().st_size
        with open(p) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:  # sessiz-yutma: YUTMA DEĞİL — bozuk satır `d_bad`'e SAYILIR ve `bad_lines` alanıyla çağırana/CLI'ya raporlanır; burada ayrıca uyarmak, ölçüm fonksiyonunu her okunuşunda olay defterine yazdırırdı
                    d_bad += 1
                    continue
                d_rows += 1
                tk = rec.get("ticker")
                if tk:
                    d_syms.add(str(tk))
        rows += d_rows
        bad += d_bad
        symbols |= d_syms
        per_day.append({"day": p.stem, "rows": d_rows, "symbols": len(d_syms), "bad_lines": d_bad})
    return {"exists": True, "days": len(files), "rows": rows, "symbols": len(symbols),
            "bad_lines": bad, "first_day": files[0].stem if files else None,
            "last_day": files[-1].stem if files else None, "bytes": size,
            "per_day": per_day, "dir": str(base)}


# --- SEANS-İÇİ KESİNTİ/BOŞLUK DEDEKTÖRÜ (5.3) ---------------------------------------------------
# NE DEĞİL: tarihsel tarama değil. `summary()` arşivin BÜYÜKLÜĞÜNÜ ölçer ("kaç gün, kaç satır") ve
# sıfır satırla dolu bir günü "arşiv var" diye okur. Bu ise CANLI AKIŞ SAĞLIĞIdır: seans İÇİNDE,
# son `GAP_WINDOW_MIN` dakikada beklenen dakikalık barların gelmediği bir pencere var mı?
#
# NEDEN GEREKLİ: akış kopuşunun bugünkü tek sinyali `marketstream`in WS bağlantı durumu
# (`streamhealth`) — yani SOKET'in sağlığı. Soket ayakta kalıp abonelik sessizleşirse (sağlayıcı
# tarafında düşen sembol, kısılan feed, tüketicinin takılması) bağlantı YEŞİL görünür ve dakikalar
# sessizce kaybolur. Kayıp da kalıcıdır: `mrd:bars` bir RING'tir (~2 seans), o dakika geri gelmez.
#
# İKİ SINIF, İKİSİ DE AYRI OKUNUR — birleştirilirse ikisi de görünmez olur:
#   * "akis"   → o dakikada HİÇBİR sembolden bar gelmedi. Bu bir KESİNTİdir.
#   * "sembol" → akış genelde akıyor ama BU sembol sustu.
#
# YANLIŞ POZİTİF KAPISI (ve neden yoğunluk değil BAĞLAM ölçülüyor): dakikalık bar yalnız İŞLEM
# olduğunda doğar. Seyrek işlem gören bir sembolde eksik dakika NORMALDİR ve onu boşluk saymak
# beklentiyi UYDURMAK olurdu. Bu yüzden bir sembol boşluğu ancak deliğin İKİ YANINDA da sembolün
# dakika dakika tıkırdadığı kanıtlanırsa raporlanır (`GAP_CONTEXT_*`). Pencere-geneli "yoğunluk"
# ölçüsü bilerek KULLANILMADI: büyük bir delik yoğunluğu kendi düşürür ve dedektör tam da en büyük
# kesintiyi görmez olurdu.
GAP_WINDOW_MIN = 60        # geriye bakılan pencere (dk) — canlı sağlık, tarih taraması değil
GAP_LAG_MIN = 2            # son N dakika HENÜZ boşluk sayılmaz (bar kapanışı + XREADGROUP + fsync gecikir)
GAP_MIN_MIN = 3            # bu kadar ARDIŞIK eksik dakika bir BOŞLUKTUR (1-2 dk = gürültü)
GAP_CONTEXT_MIN = 5        # deliğin iki yanında bakılan bağlam (dk)
GAP_CONTEXT_NEED = 4       # bağlamın en az bu kadar dakikasında bar OLMALI (sembol "sürekli akıyor")
GAP_TAIL_BYTES = 4_000_000  # gün dosyasının yalnız SONU okunur (bkz. `_pencere_satirlari`)
GAP_MAX_REPORT = 20        # rapora giren en fazla boşluk (yük sınırı; sayı ayrıca `bosluk_sayisi`de)
GAP_CALENDAR = "XNYS"      # seans takvimi — data.CALENDAR / scheduler._leg_ready ile AYNI ad
GAP_SEANS_CACHE_MAX = 40   # gün başına bir kayıt; uzun ömürlü worker'da sözlük sınırsız büyümesin
_SEANS_CACHE: dict = {}    # {gün: (durum, açılış, kapanış, hata)} — YALNIZ başarılı okumalar


def _seans_araligi(gun: str) -> tuple:
    """O GÜNÜN GERÇEK seans aralığı — XNYS `schedule()`ten, UTC. `(durum, açılış, kapanış, hata)`.

    durum: `"ok"` (seans günü; açılış/kapanış dolu) · `"seans_disi"` (takvim OKUNDU ve o gün seans
    değil: hafta sonu/tam tatil) · `"takvim_yok"` (takvim okunamadı → HÜKÜM YOK).

    NEDEN `barclock.is_market_open` DEĞİL: o fonksiyon kendi
    docstring'inde "TATİLLER hariç (yaklaşık)" der ve bunu şöyle meşrulaştırır — "Alpaca zaten
    kapalıyken bar göndermez, o yüzden bu yalnız bir KOLAYLIK kapısıdır". Gerekçe `is_admissible`
    için doğru, `gap_scan` için TERSİNE ÇEVRİLMİŞTİR: burada semantik "bar YOKSA kesinti VAR"dır,
    yani barın gelmemesi tam da alarm sebebidir. Somut vaka NYSE YARIM GÜNLERİ (13:00 ET kapanış —
    Şükran ertesi, 24 Aralık, 3 Temmuz): o gün dosya VARDIR (sabah barları yazılmıştır), ama
    13:03-16:00 ET penceresi tamamen kapanış SONRASINA düşer; eski beklenti ~58 dakika üretir,
    `dolu` boştur ve `tur="akis"` boşluğu SAHTE bir `intraday_gap_detected` uyarısı bastırırdı
    ("mrd:bars bir RING'tir, o dakikalar geri gelmez" — yani operatör geri alınamaz bir veri kaybı
    sanır). TAM tatil `arsiv_yok` ile kurtuluyordu, yarım gün kurtulmuyordu.

    TAKVİM OKUNAMAZSA YEDEK BEKLENTİ ÜRETİLMEZ: `is_market_open`a geri düşmek kapatılan deliği
    aynen geri açardı (yaklaşık takvim = sahte alarm). Ölçülemeyen şey None'dır ve `gap_scan`
    `durum="takvim_yok"` ile HÜKÜM VERMEZ. Bu bir DARALMA değil, hükümsüzlüktür: gerçek bir
    kesinti de o turda raporlanmaz, ama uydurma bir kesinti de raporlanmaz.

    ÖNBELLEK YALNIZ BAŞARIYA: `gap_scan` her poll'de (300 sn) aynı günü sorar, takvim sorgusu
    boşuna tekrarlanmasın. Ama bir ARIZAYI önbelleğe almak, takvim modülü geri geldikten sonra bile
    o günü sonsuza dek "takvim_yok" bırakırdı — arıza her çağrıda yeniden denenir."""
    key = str(gun)[:10]
    hit = _SEANS_CACHE.get(key)
    if hit is not None:
        return hit
    try:
        import pandas_market_calendars as mcal
        sched = mcal.get_calendar(GAP_CALENDAR).schedule(start_date=key, end_date=key)
    except Exception as e:  # sessiz-yutma DEĞİL: neden `durum`/`seans.hata` ile çağırana ÇIKAR ve gap_scan hüküm vermez (olay basmak SAF fonksiyonun sözleşmesini kırardı — kaydı çağıran yapar)
        return ("takvim_yok", None, None, f"{type(e).__name__}: {e}")
    if not len(sched):
        out = ("seans_disi", None, None, None)
    else:
        satir = sched.iloc[0]
        out = ("ok", satir["market_open"].to_pydatetime(),
               satir["market_close"].to_pydatetime(), None)
    if len(_SEANS_CACHE) >= GAP_SEANS_CACHE_MAX:
        for k in sorted(_SEANS_CACHE)[:len(_SEANS_CACHE) - GAP_SEANS_CACHE_MAX + 1]:
            _SEANS_CACHE.pop(k, None)
    _SEANS_CACHE[key] = out
    return out


def _pencere_satirlari(day: str, tail_bytes: int = GAP_TAIL_BYTES):
    """Gün dosyasının SONUNDAN (ticker, t) çiftleri. `(satirlar, bozuk, var_mi)` döner.

    NEDEN TAM DOSYA DEĞİL: 250 sembol × 390 dakika ≈ 100 bin satır/gün. Dedektör son bir saati
    yargılıyor, günü değil — tam dosyayı her poll'de ayrıştırmak ölçtüğü şeyin bin katı iş olurdu.
    Kuyruk okumasının TEK riski yarım ilk satırdır ve o AÇIKÇA atılır (`readline`), bozuk sayılmaz."""
    p = _day_path(day)
    if not p.exists():
        return [], 0, False
    boyut = p.stat().st_size
    with open(p, "rb") as fh:
        if boyut > tail_bytes:
            fh.seek(boyut - tail_bytes)
            fh.readline()                     # YARIM İLK SATIR: veri değil, kesik — atılır
        ham = fh.read()
    satirlar, bozuk = [], 0
    for line in ham.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:  # sessiz-yutma: YUTMA DEĞİL — bozuk satır `bozuk` sayacına girer ve raporun `bozuk_satir` alanıyla çağırana çıkar; ayrıca uyarmak, her poll'de olay defterine satır düşürürdü
            bozuk += 1
            continue
        tk, t = rec.get("ticker"), rec.get("t")
        if tk and t:
            satirlar.append((str(tk), str(t)))
    return satirlar, bozuk, True


def _kosular(eksik: list) -> list:
    """Sıralı eksik-dakika listesini ARDIŞIK koşulara böl: [(ilk, son, uzunluk), ...]"""
    out = []
    for m in eksik:
        if out and (m - out[-1][1]).total_seconds() == 60:
            out[-1][1] = m
            out[-1][2] += 1
        else:
            out.append([m, m, 1])
    return [tuple(x) for x in out]


def gap_scan(as_of=None, day: str | None = None, rows=None,
             window_min: int = GAP_WINDOW_MIN, lag_min: int = GAP_LAG_MIN,
             min_gap_min: int = GAP_MIN_MIN, context_min: int = GAP_CONTEXT_MIN,
             context_need: int = GAP_CONTEXT_NEED) -> dict:
    """SAF ölçüm — olay BASMAZ, dosya YAZMAZ. Kaydı ve tekrar-bastırmayı çağıran yapar
    (`scheduler._intraday_gap_check`); böylece testler gerçek `events.jsonl`'a dokunmadan koşar.

    `rows` verilirse diske hiç gidilmez (fikstür yolu). `as_of` verilmezse TEK saat `barclock`tan
    gelir; SEANS SINIRI ise `barclock` DEĞİL, XNYS takvimidir (`_seans_araligi` — yarım gün/tatil
    bilir). Saat yasası barclock'ta, TAKVİM yasası takvimde: ikisi de burada KOPYALANMAZ."""
    simdi = as_of or barclock.now()
    if simdi.tzinfo is None:
        simdi = simdi.replace(tzinfo=barclock.UTC)
    gun = day or barclock.session_date(simdi)
    bitis = simdi.replace(second=0, microsecond=0) - dt.timedelta(minutes=int(lag_min))
    baslangic = bitis - dt.timedelta(minutes=int(window_min))
    # BEKLENTİ GERÇEK SEANS ARALIĞINDAN ÜRETİLİR: "9:30-16:00 hafta içi" varsayımı yarım günlerde
    # kapanış SONRASINI beklenti sayıyor ve sahte akış-kesintisi alarmı basıyordu (bkz. `_seans_araligi`).
    _cal_durum, _acilis, _kapanis, _cal_hata = _seans_araligi(gun)
    beklenen = []
    if _cal_durum == "ok":
        m = baslangic
        while m < bitis:
            if _acilis <= m < _kapanis:
                beklenen.append(m)
            m += dt.timedelta(minutes=1)
    out = {"gun": gun, "olculdu": _now_iso(), "durum": "ok", "bosluklar": [], "bosluk_sayisi": 0,
           "pencere": {"baslangic": baslangic.isoformat(), "bitis": bitis.isoformat(),
                       "beklenen_dk": len(beklenen)},
           # SEANSIN KENDİSİ RAPORA GİRER: "58 dakika bekledim" cümlesinin NEDEN'i okunabilsin —
           # yarım gün mü, tam gün mü, yoksa takvim mi konuşmadı (üç hâl üç adla ayrılır).
           "seans": {"durum": _cal_durum, "takvim": GAP_CALENDAR,
                     "acilis": _acilis.isoformat() if _acilis else None,
                     "kapanis": _kapanis.isoformat() if _kapanis else None, "hata": _cal_hata},
           "sembol": 0, "gelen_bar": 0, "bozuk_satir": 0,
           "esik": {"pencere_dk": int(window_min), "gecikme_dk": int(lag_min),
                    "asgari_bosluk_dk": int(min_gap_min), "baglam_dk": int(context_min),
                    "baglam_gereken": int(context_need)}}
    if _cal_durum == "takvim_yok":
        # TAKVİM KONUŞMADI: beklenti ÜRETİLEMEZ, dolayısıyla eksiklik de ÖLÇÜLEMEZ. Yaklaşık bir
        # takvimle hüküm vermek (eski davranış) yarım günlerde uydurma kesinti raporluyordu;
        # "ölçemedim" demek, yanlış ölçmekten dürüsttür (uydurma yasağı).
        out["durum"] = "takvim_yok"
        return out
    if not beklenen:
        # SEANS DIŞI: beklenti YOK, dolayısıyla eksiklik de yok. "Sıfır boşluk bulundu" demek,
        # gece yarısı için sağlıklı akış RAPORU üretmek olurdu — üçüncü hâl adıyla söylenir.
        # ARTIK TAM TATİLİ VE YARIM GÜNÜN KAPANIŞ SONRASINI DA KAPSAR: pencere gerçek
        # market_open/market_close aralığının tamamen dışındaysa buraya düşer (eskiden yarım günde
        # düşmüyordu — `beklenen` doluyor ve sahte "akis" boşluğu üretiliyordu).
        out["durum"] = "seans_disi"
        return out
    if rows is None:
        rows, bozuk, var = _pencere_satirlari(gun)
        out["bozuk_satir"] = bozuk
        if not var:
            # ARŞİV HİÇ AÇILMAMIŞ: arşivci koşmuyorsa "akış koptu" demek YANLIŞ suçlamadır —
            # ölçülemeyen bir şey None'dır (uydurma yasağı), hüküm verilmez.
            out["durum"] = "arsiv_yok"
            return out
    pencere = {}
    for tk, t in rows:
        o = barclock.parse_utc(t)
        if o is None:
            continue
        o = o.replace(second=0, microsecond=0)
        if baslangic <= o < bitis:
            pencere.setdefault(str(tk).upper(), set()).add(o)
    out["sembol"] = len(pencere)
    out["gelen_bar"] = sum(len(v) for v in pencere.values())
    bek = set(beklenen)
    dolu = set().union(*pencere.values()) if pencere else set()
    akis_eksik = sorted(bek - dolu)
    bosluklar = []
    for ilk, son, n in _kosular(akis_eksik):
        if n >= min_gap_min:
            bosluklar.append({"tur": "akis", "sembol": None, "baslangic": ilk.isoformat(),
                              "bitis": son.isoformat(), "eksik_dk": n,
                              "beklenen": len(beklenen), "gelen": len(dolu)})
    akis_eksik_kume = set(akis_eksik)
    for tk in sorted(pencere):
        var = pencere[tk]
        for ilk, son, n in _kosular(sorted(bek - var)):
            if n < min_gap_min:
                continue
            # AKIŞ KESİNTİSİNİN İÇİNDE KALAN SEMBOL BOŞLUĞU AYRICA RAPORLANMAZ: tek kesinti için
            # 250 satır basmak, asıl olayı kendi gürültüsüyle gömerdi (ve iki kez saydırırdı).
            if all(x in akis_eksik_kume for x in _dakikalar(ilk, son)):
                continue
            onces = [x for x in _dakikalar(ilk - dt.timedelta(minutes=context_min),
                                           ilk - dt.timedelta(minutes=1)) if x in bek]
            sonras = [x for x in _dakikalar(son + dt.timedelta(minutes=1),
                                            son + dt.timedelta(minutes=context_min)) if x in bek]
            if len(onces) < context_need or len(sonras) < context_need:
                continue            # bağlam pencereye SIĞMIYOR → hüküm verilemez (kenar etkisi)
            if sum(1 for x in onces if x in var) < context_need or \
               sum(1 for x in sonras if x in var) < context_need:
                continue            # sembol zaten seyrek akıyor → delik BEKLENTİ değil, normal
            bosluklar.append({"tur": "sembol", "sembol": tk, "baslangic": ilk.isoformat(),
                              "bitis": son.isoformat(), "eksik_dk": n,
                              "beklenen": len(beklenen), "gelen": len(var)})
    if not dolu:
        # DOSYA VAR AMA PENCEREDE TEK BAR YOK: bu, yukarıdaki `akis` koşusuyla zaten yakalanır
        # (tüm pencere tek boşluktur); durum adı okuyucuya sebebi söyler.
        out["durum"] = "pencerede_bar_yok"
    out["bosluk_sayisi"] = len(bosluklar)
    out["bosluklar"] = sorted(bosluklar, key=lambda b: (-b["eksik_dk"], str(b["sembol"] or "")))[:GAP_MAX_REPORT]
    return out


def _dakikalar(ilk, son) -> list:
    out, m = [], ilk
    while m <= son:
        out.append(m)
        m += dt.timedelta(minutes=1)
    return out


def render_summary(limit_days: int | None = None) -> str:
    """`--ozet` metni. Sıfır satırlı arşiv SAHTE bir 'her şey yolunda' göstermez — açıkça söyler."""
    s = summary(limit_days)
    if not s["exists"]:
        return (f"bars_intraday arşivi YOK ({s['dir']}).\n"
                f"Henüz hiç tur koşmadı ya da Redis'te bar birikmedi. "
                f"Runner: python -m meridian.barsarchive")
    if s["rows"] == 0:
        return (f"bars_intraday arşivi BOŞ ({s['days']} dosya, 0 satır) — {s['dir']}\n"
                f"Dizin var ama bar yazılmadı; Redis'te mrd:bars:* akışı var mı bakın.")
    out = [f"bars_intraday arşivi — {s['dir']}",
           f"  gun      : {s['days']}  ({s['first_day']} → {s['last_day']})",
           f"  satir    : {s['rows']}",
           f"  sembol   : {s['symbols']} (benzersiz)",
           f"  boyut    : {s['bytes'] / 1024:.1f} KiB"]
    if s["bad_lines"]:
        out.append(f"  BOZUK SATIR: {s['bad_lines']} — yarım yazım (çökme/disk); ACK'lenmemişse "
                   f"yeniden teslimde onarılır")
    out.append("  gun kirilimi (son 10):")
    for d in s["per_day"][-10:]:
        out.append(f"    {d['day']}  satir={d['rows']:<7} sembol={d['symbols']:<5}"
                   + (f" BOZUK={d['bad_lines']}" if d["bad_lines"] else ""))
    return "\n".join(out)


# --- CLI -----------------------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    import argparse
    p = argparse.ArgumentParser(
        prog="python -m meridian.barsarchive",
        description="mrd:bars:* → state/bars_intraday/YYYY-MM-DD.jsonl dayanıklı arşivci")
    p.add_argument("--ozet", action="store_true", help="arşiv istatistiğini yaz ve çık (koşma)")
    p.add_argument("--gun", type=int, default=None, metavar="N",
                   help="--ozet: yalnız son N günü özetle")
    p.add_argument("--poll-ms", type=int, default=DEFAULT_POLL_MS,
                   help=f"XREADGROUP BLOCK süresi (ms, tavan {MAX_POLL_MS}); varsayılan {DEFAULT_POLL_MS}")
    p.add_argument("--idle-s", type=float, default=DEFAULT_IDLE_S,
                   help=f"hiç akış yokken tur arası uyku (sn); varsayılan {DEFAULT_IDLE_S}")
    p.add_argument("--count", type=int, default=DEFAULT_COUNT, help="tur/akış başına en fazla giriş")
    p.add_argument("--once", action="store_true", help="tek tur koş ve çık (cron/duman testi)")
    p.add_argument("--bosluk", action="store_true",
                   help="seans-içi boşluk taraması (5.3): son penceredeki eksik bar aralıkları")
    a = p.parse_args(argv)

    if a.ozet:
        print(render_summary(a.gun))
        return 0

    if a.bosluk:
        # OPERATÖRÜN İKİNCİ OKUYUCUSU (asıl tüketici: scheduler kancası → /api/diagnostics).
        print(json.dumps(gap_scan(), ensure_ascii=False, indent=1))
        return 0

    arch = BarsArchiver(poll_ms=a.poll_ms, idle_s=a.idle_s, count=a.count)
    if a.once:
        res = arch.poll()
        arch.close()
        if res is None:
            # DÜRÜST BAŞARISIZLIK: Redis yok ≠ yazacak bar yok. Çıkış kodu da bunu söyler.
            print("REDIS YOK — hiçbir akış okunamadı (arşiv ilerlemedi). "
                  "MERIDIAN_REDIS_URL'e bakın.")
            return 2
        print(json.dumps(res, ensure_ascii=False))
        return 0
    print(f"barsarchive: grup={GROUP} tuketici={arch.consumer} poll={arch.poll_ms}ms "
          f"idle={arch.idle_s}s dizin={archive_dir()}")
    try:
        arch.run()
    except KeyboardInterrupt:
        arch.stop()
        arch.close()
        print("\n" + json.dumps(arch.snapshot(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

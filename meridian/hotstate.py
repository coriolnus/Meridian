"""hotstate.py — Redis SICAK-DURUM katmanı (intraday, 2026-07-23, operatör mimari isteği).

NEDEN: intraday (dakikalık bar) için son fiyatlar / açık pozisyonlar / emirler saniyeler içinde,
defalarca okunur. Bunları her seferinde JSON dosyadan okuyup parse etmek (counterfactuals 4.9M değil
ama portfolio/heartbeat her tick) EOD kadansında sorun değildi; dakikalık döngüde I/O darboğazı olur.
Redis in-memory bu okumaları ~ms'e indirir.

İKİ SIKI İLKE — bu kod tabanının dürüstlük/denetlenebilirlik kimliğini korur:

  1. REDIS UÇUCUDUR, KALICI GERÇEK DEĞİL. İşlemler, kararlar, cf, hipotezler HÂLÂ store.py JSON/JSONL
     defterlerinde yaşar — 7 katmanlı bütünlük/provenance dedektörü onları okur, grep'lenir, denetlenir.
     Redis yalnız TÜREV/UÇUCU tutar: son fiyat, pozisyon/emir SICAK KOPYASI, hesaplama cache. Redis
     tamamen silinse bile hiçbir kalıcı gerçek kaybolmaz — kaynak dosyadır, Redis hızlı okuma katmanı.

  2. GRACEFUL DEGRADATION. Redis yoksa/çökse sistem DURMAZ: her okuma None döner (çağıran dosyaya
     düşer), her yazma sessizce no-op'lar ama bir kez olay yazar. `mirror_stream`'in "sahte güvenli-
     başarısızlık değil, görünür başarısızlık" dersi: down durumu health()'te ve panoda görünür.

Anahtar şeması (hepsi `mrd:` önekli, TTL'li — bayat sıcak veri birikmesin):
  mrd:price:{TICKER}   → hash {price, ts}          (son işlem/bar fiyatı; yazan: ingest_bars)
  mrd:pos              → hash {TICKER: json}        (açık pozisyon sıcak kopyası)

`mrd:ord` (açık emir sıcak kopyası) BEYANI KALDIRILDI (kopukluk avı, 2026-07-30): şema burada
yazılıydı ama bu anahtara yazan/okuyan TEK BİR fonksiyon bile yoktu — yani belge, var olmayan bir
katmanı var gibi gösteriyordu. Ölü bir şema beyanı yalnız fazlalık değildir: sonraki okuyucuyu
"emirler zaten sıcak katmanda" diye yanlış yönlendirir. Açık emirlerin gerçek kaynağı
`broker_reconcile.json` + `mirror_stream`'dir. Emir sıcak kopyası gerçekten gerekirse şema o gün,
yazan fonksiyonuyla birlikte gelir.

YALNIZ-YAZILIR KATMAN KARARI (aynı tur): `mrd:price` ve `mrd:pos`ın PRODÜKSİYONDA HİÇBİR OKUYUCUSU
yok — `get_price`/`get_positions` yalnız testlerden çağrılıyor (statik tarama: 2026-07-30). EOD
döngüsündeki iki yazım noktası (loop._save_broker → cache_positions, loop.daily_cycle → set_prices)
bu yüzden DEVRE DIŞI bırakıldı; gerekçe ve geri açma yolu loop.py'deki iki yorumda. Fonksiyonlar
BURADA KALIR (silinmedi): 4b/pano tüketicisi geldiği gün kanca tek satırdır. `mrd:price`ın intraday
yazıcısı (`ingest_bars`) DEĞİŞMEDİ — kapanmış bar → sıcak fiyat TEK yazma yolu hâlâ oradadır.
"""
from __future__ import annotations

import json
import os
import time

_URL = os.environ.get("MERIDIAN_REDIS_URL", "redis://127.0.0.1:6379/0")
PREFIX = "mrd:"
PRICE_TTL_S = 3600          # sıcak fiyat 1 saat sonra bayat sayılır (döngü zaten çok daha sık yeniler)
# Faz 2: dakikalık KAPANMIŞ bar tamponu (mrd:bars:{T} Redis Stream). UÇUCU türev — kalıcı öğrenme
# kaynağı YİNE EOD immutable bar dosyalarıdır; mrd:bars backtest/recompute'a ASLA girmez.
BARS_MAXLEN = int(os.environ.get("MERIDIAN_BARS_MAXLEN", "900"))     # ~2 seans (ring); eski bar düşer
BARS_TTL_S = int(os.environ.get("MERIDIAN_BARS_TTL_S", "172800"))    # 2 gün; delisted sembol solar
# Faz 3: DAYANIKLI bar-tetiği. mrd:barfeed tek birleşik "yeni bar geldi" olay akışıdır; her ingest_bars
# çağrısı buraya bir olay {ts,n,syms} XADD eder. Bir consumer-group (XREADGROUP+ACK) bunu okuyup karar
# döngüsünü uyandırır — bare pub/sub'ın aksine tüketici bir an düşse bile tetik DÜŞMEZ (restart'ta
# son ACK'ten devam). Faz 4 intraday_cycle bu tetiğe bağlanır.
BARFEED = PREFIX + "barfeed"
BARFEED_MAXLEN = int(os.environ.get("MERIDIAN_BARFEED_MAXLEN", "5000"))

_client = None
# Bloklu stream okumaları (XREADGROUP block=Nms) için AYRI client. Hot-path client'ın 0.5s
# socket_timeout'u bloklu okumayı keserdi → her turda sahte TimeoutError → yanlış 'Redis down' churn
# (çekişmeli-inceleme sonrası CANLI restart'ta yakalandı). Bunun socket_timeout'u block'tan BÜYÜK.
_blocking_client = None
BLOCKING_SOCKET_TIMEOUT = 5.0        # barfeed block_ms (2000) bundan KÜÇÜK olmalı
_HEALTH: dict = {"ok": None, "reads": 0, "writes": 0, "fails": 0, "last_error": "", "at": None,
                 "down_since": None}


def _now_iso() -> str:
    import datetime as _dt
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat()


def _redis():
    """Tembel bağlantı. redis-py yoksa ya da bağlanamazsa None — çağıran dosyaya düşer."""
    global _client
    if _client is not None:
        return _client
    try:
        import redis
        _client = redis.from_url(_URL, socket_timeout=0.5, socket_connect_timeout=0.5,
                                 decode_responses=True)
        _client.ping()
        _HEALTH.update(ok=True, down_since=None, at=_now_iso())
        return _client
    except Exception as e:
        _client = None
        _note_down(e)
        return None


def _blocking_redis():
    """Bloklu okumalar (barfeed XREADGROUP) için tembel AYRI bağlantı; socket_timeout block'tan büyük
    (BLOCKING_SOCKET_TIMEOUT) ki bloklu okuma soket-timeout'la kesilmesin."""
    global _blocking_client
    if _blocking_client is not None:
        return _blocking_client
    try:
        import redis
        _blocking_client = redis.from_url(_URL, socket_connect_timeout=0.5,
                                          socket_timeout=BLOCKING_SOCKET_TIMEOUT, decode_responses=True)
        _blocking_client.ping()
        return _blocking_client
    except Exception as e:
        _blocking_client = None
        _note_down(e)
        return None


def _note_down(exc: BaseException) -> None:
    global _client, _blocking_client
    _HEALTH["fails"] += 1
    _HEALTH["last_error"] = f"{type(exc).__name__}: {str(exc)[:120]}"
    _HEALTH["at"] = _now_iso()
    # KURT MASALI YASAĞI (çekişmeli inceleme bulgusu, 2026-07-23): girdi hataları (float(None) vb.)
    # Redis'in DOWN olduğu anlamına GELMEZ — TypeError/ValueError/KeyError sağlığı DÜŞÜRMEZ, yalnız
    # sayaç artırır. Aksi hâlde bozuk tek bir değer panoyu "Redis erişilemez" diye yanlış-kırmızıya boyar.
    if isinstance(exc, (TypeError, ValueError, KeyError)):
        return
    # BAĞLANTI hatası: her iki client'ı da BIRAK ki bir sonraki _redis()/_blocking_redis() yeniden
    # ping'lesin. Aksi hâlde önbellekli client ping ATMADAN dönüyor ve hiçbir başarı yolu ok'u True'ya
    # geri almıyordu → geçici bir blip'ten sonra sağlık ÖMÜR BOYU False kalıyordu (mirror'ın 'toparlanma
    # temizler' dersinin yarım hâli).
    _client = None
    _blocking_client = None
    if _HEALTH.get("ok") is not False:
        _HEALTH["ok"] = False
        _HEALTH["down_since"] = _now_iso()
        _emit_down()
    else:
        # KOPUŞ SÜRÜYOR. Eskiden burada HİÇBİR ŞEY yazılmıyordu ("bir KEZ olay yaz" — kenar sinyali)
        # ama K1 denetimi 24 SAATTE 6.834 `hotstate_down` ÖLÇTÜ ve olay defterinin %91'i bu tek
        # olaydı. Sebep: kenar gerçekten çırpınıyor — her başarılı ping `ok`u True'ya geri alıyor,
        # sıradaki hata yeni bir KENAR sayılıyor ve olay yeniden yazılıyor. Yani "tek kenar" iddiası
        # doğruydu, kenar sayısı değil.
        # ÇÖZÜM streamhealth'ın DESENİ (aynı depoda aynı sorunun çözülmüş hâli): süregelen kopuş
        # DOWN_REASSERT_S'te BİR kez yeniden basar, arada bastırılanlar SAYILIR ve bir sonraki
        # kayıtta `suppressed` olarak görünür — sel kesilir, GERÇEK kaybolmaz.
        _HEALTH["reassert_suppressed"] = int(_HEALTH.get("reassert_suppressed", 0)) + 1
        _maybe_reassert_down()


# DOWN olayının YENİDEN basılma aralığı. streamhealth.DOWN_REASSERT_S ile AYNI değer (300s): aynı
# depoda "süregelen kopuş ne sıklıkla yeniden kayda geçer?" sorusunun iki farklı cevabı olmasın.
DOWN_REASSERT_S = 300
_LAST_DOWN_EMIT: float = 0.0


def _emit_down(reassert: bool = False) -> None:
    """`hotstate_down` olayını yaz ve zaman damgasını güncelle. Bastırılan sayısı KAYITTA görünür."""
    global _LAST_DOWN_EMIT
    import time as _t
    _LAST_DOWN_EMIT = _t.monotonic()
    bastirilan = int(_HEALTH.get("reassert_suppressed", 0))
    _HEALTH["reassert_suppressed"] = 0
    try:
        from . import obs
        obs.warn("hotstate_down", url=_mask(_URL), error=_HEALTH["last_error"],
                 reassert=bool(reassert), suppressed=bastirilan,
                 down_since=_HEALTH.get("down_since"),
                 detail="Redis sıcak katmanı erişilemez — sistem dosya defterlerine düşüyor "
                        "(kalıcı gerçek kaybı YOK, yalnız intraday okuma yavaşlar)"
                        + (f"; ARADA {bastirilan} kopma BASTIRILDI (throttle {DOWN_REASSERT_S}s)"
                           if bastirilan else ""))
        # ALARM TÜRETMESİ (K1): tek tek kopmalar uyarıdır, ama bir throttle penceresinde ÇOK sayıda
        # kopma ÇIRPINMA demektir ve o ayrı bir olgudur (ağ/servis kararsızlığı). Eşik aşılırsa
        # DATA_QUALITY alarmına türetilir — uyarı seli alarm ÜRETMEZ, oran üretir.
        if bastirilan >= REASSERT_ALARM_MIN:
            obs.alarm(obs.ALARM_DATA_QUALITY,
                      f"hotstate ÇIRPINMA: {DOWN_REASSERT_S}s içinde {bastirilan} kopma",
                      suppressed=bastirilan, window_s=DOWN_REASSERT_S,
                      down_since=_HEALTH.get("down_since"))
    except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü; ikinci kanal yok, telemetri asıl yolu düşüremez
        pass


# Bir throttle penceresinde bu kadar bastırılmış kopma ÇIRPINMA sayılır. 20: 300 saniyede 20 kopma
# = ~15 saniyede bir; normal bir geçici blip bu hızda tekrarlamaz, K1'in ölçtüğü sel (6.834/24s ≈
# 4,7/dakika) bu eşiği rahatça aşar.
REASSERT_ALARM_MIN = 20


def _maybe_reassert_down() -> None:
    import time as _t
    if (_t.monotonic() - _LAST_DOWN_EMIT) >= DOWN_REASSERT_S:
        _emit_down(reassert=True)


def _mask(url: str) -> str:
    # redis://user:pass@host — parolayı maskele
    import re
    return re.sub(r"(//[^:@/]+:)[^@/]+@", r"\1***@", url)


def available() -> bool:
    """Redis ERİŞİLEBİLİR mi (ping). available()=True 'çalışıyor' demektir, fmp.available'ın aksine
    burada anlık ping yapılır çünkü intraday'de down durumu hızlı bilinmeli."""
    return _redis() is not None


def health() -> dict:
    return dict(_HEALTH)


# ---------------- FİYAT (en sık okunan sıcak veri) ----------------
def set_price(ticker: str, price: float, ts: str | None = None) -> bool:
    r = _redis()
    if r is None:
        return False
    try:
        r.hset(PREFIX + "price:" + ticker, mapping={"price": float(price), "ts": ts or _now_iso()})
        r.expire(PREFIX + "price:" + ticker, PRICE_TTL_S)
        _HEALTH["writes"] += 1
        return True
    except Exception as e:
        _note_down(e)
        return False


def set_prices(mapping: dict[str, float], ts: str | None = None) -> int:
    """Toplu — dakikalık bar geldiğinde tüm evren tek turda. pipeline ile tek round-trip."""
    r = _redis()
    if r is None:
        return 0
    ts = ts or _now_iso()
    try:
        pipe = r.pipeline()
        for tk, px in mapping.items():
            k = PREFIX + "price:" + tk
            pipe.hset(k, mapping={"price": float(px), "ts": ts})
            pipe.expire(k, PRICE_TTL_S)
        pipe.execute()
        _HEALTH["writes"] += len(mapping)
        return len(mapping)
    except Exception as e:
        _note_down(e)
        return 0


def get_price(ticker: str) -> dict | None:
    """Son sıcak fiyat + zaman damgası; Redis yoksa None → çağıran dosya/bar'a düşer."""
    r = _redis()
    if r is None:
        return None
    try:
        h = r.hgetall(PREFIX + "price:" + ticker)
        _HEALTH["reads"] += 1
        return {"price": float(h["price"]), "ts": h["ts"]} if h else None
    except Exception as e:
        _note_down(e)
        return None


# ---------------- POZİSYON / EMİR SICAK KOPYASI ----------------
# Kaynak HÂLÂ portfolio.json (kalıcı, denetlenebilir). Bunlar intraday hızlı-okuma kopyası.
# Yazan taraf her değişimde hem dosyayı (kalıcı) hem burayı (sıcak) günceller.
def cache_positions(positions: dict) -> bool:
    r = _redis()
    if r is None:
        return False
    try:
        r.delete(PREFIX + "pos")
        if positions:
            r.hset(PREFIX + "pos", mapping={t: json.dumps(p, default=str) for t, p in positions.items()})
        _HEALTH["writes"] += 1
        return True
    except Exception as e:
        _note_down(e)
        return False


def get_positions() -> dict | None:
    r = _redis()
    if r is None:
        return None
    try:
        h = r.hgetall(PREFIX + "pos")
        _HEALTH["reads"] += 1
        return {t: json.loads(v) for t, v in h.items()}
    except Exception as e:
        _note_down(e)
        return None


def flush() -> int:
    """Tüm mrd:* anahtarlarını sil (test/reset). SCAN — KEYS üretimi bloklar. mrd:bars:* dahil."""
    r = _redis()
    if r is None:
        return 0
    n = 0
    try:
        for k in r.scan_iter(match=PREFIX + "*", count=500):
            r.delete(k)
            n += 1
    except Exception as e:
        _note_down(e)
    return n


# ---------------- DAKİKALIK KAPANMIŞ BAR (Faz 2, Redis Stream) ----------------
# Anahtar şeması:
#   mrd:bars:{TICKER} → Redis Stream. Her giriş bir KAPANMIŞ dakikalık bar {o,h,l,c,v,vw,n,t}.
#     t = DAKİKA BAŞLANGICI, RFC-3339 UTC ('...Z'). LOOK-AHEAD SÖZLEŞMESİ: close_ts = parse_utc(t)+60s;
#     tüketici (gelecek faz) barı ancak decision_as_of >= close_ts iken kabul eder — `t`'ye gate ETMEZ
#     (aksi 60 sn erken kabul = look-ahead deler). MAXLEN~ (approximate ring) + EXPIRE. UÇUCU türev.
#   mrd:price:{TICKER} → mevcut hash; ingest price=c, ts=t yazar (kapanmış bar → sıcak fiyat TEK yolda).
_BAR_FIELDS = ("o", "h", "l", "c", "v", "vw", "n", "t")
_BAR_NUM = ("o", "h", "l", "c", "v", "vw", "n")


def _bar_wire(bar: dict) -> dict:
    """Bar'ı XADD alanlarına indir (None'ları at — Redis stream boş dize sevmez)."""
    out = {}
    for k in _BAR_FIELDS:
        v = bar.get(k)
        if v is not None:
            out[k] = v
    return out


def _bar_parse(fields: dict) -> dict:
    """XRANGE alanlarını sayısal bar'a geri çevir; `t` dize kalır (damga)."""
    out = {}
    for k, v in fields.items():
        if k in _BAR_NUM:
            try:
                out[k] = float(v)
            except (TypeError, ValueError):  # sessiz-yutma: biçimsiz tek alan zaten ham dizeyle döner; bar bir bütün olarak kullanılabilir kalır, satır başına uyarı dakikalık akışta log seli olurdu
                out[k] = v
        else:
            out[k] = v
    return out


def append_bar(ticker: str, bar: dict, maxlen: int = BARS_MAXLEN) -> str | None:
    """Tek bir kapanmış barı mrd:bars:{ticker} stream'ine ekle (XADD + EXPIRE). Redis yoksa None
    (çağıran dosya/bar'a düşer). Sıcak fiyatı GÜNCELLEMEZ — o `ingest_bar`ın işi (tek yazma yolu)."""
    r = _redis()
    if r is None:
        return None
    wire = _bar_wire(bar)
    if not wire:
        return None
    try:
        k = PREFIX + "bars:" + ticker
        _id = r.xadd(k, wire, maxlen=maxlen, approximate=True)
        r.expire(k, BARS_TTL_S)
        _HEALTH["writes"] += 1
        return _id
    except Exception as e:
        _note_down(e)
        return None


def ingest_bar(ticker: str, bar: dict) -> bool:
    """SICAK YOL — bir kapanmış bar geldiğinde TEK pipeline'da (tek round-trip): (1) sıcak fiyatı bar
    kapanışına (`c`) + damgaya (`t`) çek, (2) barı stream'e ekle. 'Her kapanmış bar sıcak fiyatı
    güncellemeli' yasası burada TEK yazma yolunda karşılanır. Redis yoksa False, istisna YOK."""
    return ingest_bars({ticker: bar}) == 1


def ingest_bars(bars: dict[str, dict]) -> int:
    """Bir WS frame'indeki TÜM barları tek pipeline'da yaz (fiyat hash + bar stream, her sembol için).
    Yazılan sembol sayısını döner; Redis yoksa 0 (no-op, istisna YOK)."""
    r = _redis()
    if r is None or not bars:
        return 0
    ts0 = _now_iso()
    try:
        pipe = r.pipeline()
        n = 0
        wrote = []
        for tk, bar in bars.items():
            wire = _bar_wire(bar)
            c = bar.get("c")
            t = bar.get("t")
            # `t` ZORUNLU (çekişmeli inceleme bulgusu): look-ahead sözleşmesi close_ts=t+60s'e dayanır;
            # `t`siz bir bar akışa girerse tüketici kapıyı hesaplayamaz. Yapısal güvence yazma anında.
            if c is None or t is None or not wire:
                continue
            pk = PREFIX + "price:" + tk
            pipe.hset(pk, mapping={"price": float(c), "ts": t or ts0})
            pipe.expire(pk, PRICE_TTL_S)
            bk = PREFIX + "bars:" + tk
            pipe.xadd(bk, wire, maxlen=BARS_MAXLEN, approximate=True)
            pipe.expire(bk, BARS_TTL_S)
            n += 1
            wrote.append(tk)
        if n:
            # Faz 3 DAYANIKLI TETİK: bu frame için tek birleşik olay (hangi semboller güncellendi).
            pipe.xadd(BARFEED, {"ts": ts0, "n": n, "syms": ",".join(wrote)},
                      maxlen=BARFEED_MAXLEN, approximate=True)
            pipe.expire(BARFEED, BARS_TTL_S)
        pipe.execute()
        _HEALTH["writes"] += n
    except Exception as e:
        _note_down(e)
        return 0
    # Faz 5 KANIT BİRİKİMİ: Redis ring'i ~2 seans tutar ve TTL sonrası bu çerçeve YOKTUR.
    # "Dakika-hassas icra EOD'den iyi mi?" sorusu ancak geçmiş çerçeveler birikmişse cevaplanabilir;
    # birikim bugün başlamazsa üç ay sonra üç aylık olmaz. Yalnız GERÇEKTEN yazılan çerçeveler (n>0)
    # arşivlenir — boş/atlanmış kare kanıt değildir.
    # YEREL İMPORT: hotstate Redis'siz ortamlarda da import ediliyor; arşiv modülünü dosya başına
    # taşımak o yolları store/config'e bağlardı. Çağrı KENDİ içinde güvenlidir (her istisnayı yutar,
    # False döner) — burada ek bir try YOKTUR ve gerekmez.
    # TRY BLOĞUNUN DIŞINDA: içeride olsaydı bir arşiv/import arızası `_note_down`a düşer ve BAŞARILI
    # bir yazımı "Redis düştü" diye raporlayıp 0 döndürürdü — yani kanıt yan etkisi, canlı hattın
    # sağlık ölçümünü yalanlardı.
    if n:
        from . import bararchive
        bararchive.archive_frame(bars, ts0)
    return n


def read_bars(ticker: str, count: int = 100) -> list[dict] | None:
    """Son `count` kapanmış barı ESKİDEN-YENİYE döndür; Redis yoksa None → çağıran dosyaya düşer."""
    r = _redis()
    if r is None:
        return None
    try:
        rows = r.xrevrange(PREFIX + "bars:" + ticker, count=count)   # yeniden-eskiye
        _HEALTH["reads"] += 1
        return [_bar_parse(f) for _id, f in reversed(rows)]           # eskiden-yeniye
    except Exception as e:
        _note_down(e)
        return None


def bars_len(ticker: str) -> int:
    """mrd:bars:{ticker} stream uzunluğu (XLEN); Redis yoksa 0."""
    r = _redis()
    if r is None:
        return 0
    try:
        n = r.xlen(PREFIX + "bars:" + ticker)
        _HEALTH["reads"] += 1
        return int(n)
    except Exception as e:
        _note_down(e)
        return 0


# ---------------- BARFEED CONSUMER-GROUP (Faz 3, DAYANIKLI tetik) ----------------
def ensure_barfeed_group(group: str) -> bool:
    """Consumer-group'u oluştur (idempotent; MKSTREAM ile akış yoksa yaratır). `id="$"` → grup YALNIZ
    bu andan SONRAKİ olayları görür (geçmişi replay etmez — canlı tetik). Zaten varsa (BUSYGROUP) sorun
    değil. Redis yoksa False."""
    r = _redis()
    if r is None:
        return False
    try:
        r.xgroup_create(BARFEED, group, id="$", mkstream=True)
        return True
    except Exception as e:
        if "BUSYGROUP" in str(e):     # zaten var — idempotent
            return True
        _note_down(e)
        return False


def read_barfeed(group: str, consumer: str, count: int = 50, block_ms: int = 2000) -> list | None:
    """Grup için YENİ (henüz teslim edilmemiş) barfeed olaylarını oku (XREADGROUP '>'). `[(id, fields)]`
    döner; Redis yoksa/hata None. block_ms kadar bloklar (SENKRON — çağıran AYRI thread'de koşmalı,
    event-loop'u dondurmasın). AYRI bloklu-client kullanır (hot-path'in 0.5s socket_timeout'u bloklu
    okumayı keser, sahte 'Redis down' churn yapardı). ACK ayrı: tüketici işledikten sonra ack_barfeed."""
    r = _blocking_redis()
    if r is None:
        return None
    try:
        res = r.xreadgroup(group, consumer, {BARFEED: ">"}, count=count, block=block_ms)
        _HEALTH["reads"] += 1
        out = []
        for _stream, entries in (res or []):
            for _id, fields in entries:
                out.append((_id, fields))
        return out
    except Exception as e:
        _note_down(e)
        return None


def ack_barfeed(group: str, ids) -> int:
    """İşlenen olayları ACK'le (XACK) — böylece restart'ta yeniden teslim edilmezler. Redis yoksa 0."""
    r = _redis()
    if r is None or not ids:
        return 0
    try:
        return int(r.xack(BARFEED, group, *ids))
    except Exception as e:
        _note_down(e)
        return 0


def barfeed_pending(group: str) -> int:
    """Grubun BEKLEYEN (okunmuş ama ACK'lenmemiş) olay sayısı — tüketici geride mi (lag)? Redis yoksa 0."""
    r = _redis()
    if r is None:
        return 0
    try:
        info = r.xpending(BARFEED, group)
        return int(info.get("pending", 0)) if isinstance(info, dict) else int(info[0] or 0)
    except Exception as e:
        if "NOGROUP" in str(e):       # grup henüz yok → bekleyen yok
            return 0
        _note_down(e)
        return 0


def claim_and_drop_stale_barfeed(group: str, consumer: str, min_idle_ms: int = 60000, count: int = 200) -> int:
    """Bayat PEL girişlerini (min_idle_ms'ten uzun ACK'lenmemiş) XAUTOCLAIM ile al ve HEMEN ACK'le (DÜŞ).
    Intraday tüketici EN SON barı işler; bayat tetikler yeniden-işlenmez, yalnız PEL'i şişirir (ör. Redis
    churn döneminde ACK edilememiş olaylar). Düşürülen sayısını döner; Redis yoksa 0."""
    r = _redis()
    if r is None:
        return 0
    try:
        res = r.xautoclaim(BARFEED, group, consumer, min_idle_time=min_idle_ms, start_id="0-0", count=count)
        claimed = res[1] if isinstance(res, (list, tuple)) and len(res) >= 2 else []
        ids = [i for i, _f in claimed]
        if ids:
            r.xack(BARFEED, group, *ids)
        return len(ids)
    except Exception as e:
        if "NOGROUP" in str(e):
            return 0
        _note_down(e)
        return 0

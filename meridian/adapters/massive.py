"""adapters/massive.py — Massive (massive.com) EOD bar sağlayıcısı.

NEDEN VAR: bugün 250 sembollük BİR bar tazelemesi, SEMBOL BAŞINA bir FMP isteği atıyor ve ücretsiz
katmanın günlük kotasının TAMAMINI yakıyor (canlı kanıt: state/fmp_usage.json, 2026-07-27'de
`calls_today: 251` ile "Limit Reach"). Massive'in **grouped daily** ucu TÜM ABD piyasasının o güne ait
EOD barlarını TEK çağrıda döndürür — yani artımlı günlük tazeleme N istekten 1 isteğe iner.

ROL AYRIMI (Rol 1 kararı):
  * Massive → GÜNLÜK ARTIMLI tazeleme (önbellekte zaten geçmişi olan sembollerin SON barı) +
    çapraz doğrulama. Ücretsiz katman: 5 çağrı/dk, ~2 yıl geçmiş, EOD.
  * FMP     → DERİN geçmiş backfill (2021+; walk-forward bunu ister) ve Massive düşerse yedek.
  * Alpaca  → dakikalık; bu modül ona hiç dokunmaz.

UÇLAR — DOKÜMANDAN DOĞRULANDI (2026-07-29, massive.com/docs endpoint sayfaları):
  grouped daily   GET {BASE}/v2/aggs/grouped/locale/us/market/stocks/{YYYY-MM-DD}
                      ?adjusted=true&include_otc=false
  custom bars     GET {BASE}/v2/aggs/ticker/{ticker}/range/{mult}/{timespan}/{from}/{to}
  all tickers     GET {BASE}/v3/reference/tickers
NOT: massive.com/llms.txt bu uçları `/rest/stocks/aggregates/daily-market-summary` gibi adlarla
listeler — bunlar DOKÜMAN SAYFASI yollarıdır, istek yolları değil. İstek yolları yukarıdaki gibidir
(her uç sayfasındaki literal "GET https://api.massive.com/..." satırından alındı).

ALAN EŞLEMESİ (results[] → bizim CSV şeması date,open,high,low,close,volume):
    T  → (ticker; satırın kimliği, sütun değil)      o → open      h → high
    l  → low            c → close        v → volume   t → date (unix ms, ET seansına çevrilir)
    vw → **ATILIR** (CSV şemasında vwap sütunu YOK — state/bars/*.csv başlığı doğrulandı)
    n  → **ATILIR** (işlem sayısı; şemada yok)     otc → ATILIR (include_otc=false zaten)

ANAHTAR YOKSA: her uç None döner (BOŞ LİSTE DEĞİL — "istek atılamadı" ile "sağlayıcı sıfır satır
döndürdü" ayrı şeylerdir; data.py'deki HATA≠BOŞ disiplininin aynısı) ve yokluk BİR KEZ obs'a kaydedilir
(YASA 4: yokluk kaydedilir, sessiz değil). Zincir FMP ile aynen sürer.

YAZIM ZİNCİRİNE GİRİŞ ÖLÇÜME BAĞLIDIR — ve ölçüm YAPILDI (ayrıntı: BASELINE):
  * Rol 1, iki ayrı tarihte (25 ve 12 sembol; arada temettü ex-tarihi geçen KO/PEP/O/VZ/MO dahil):
    maksimum sapma %0.000.
  * Rol 2 (bu ajan) BAĞIMSIZ tekrar, TÜM önbellek evreni (251 sembol, 2026-07-28): maksimum sapma
    **%0.081**, %0.1 toleransını aşan 0/251. Yani "sıfır sapma" DOĞRU DEĞİL — küçük örneklemin
    yuvarlamasıydı; gerçek iyi huylu gürültü tabanı ~%0.08. Sapmalar DAĞINIK, çarpımsal değil:
    bölünme 2x/4x, temettü %1–15 SABİT kayma üretirdi, bu ise venue/consolidated close farkı.
  * Hacim ekseni de ölçüldü (brief istemiyordu, ama bar yazan kaynak hacmi de yazar): 239/251
    birebir aynı, medyan oran 1.000 → sistematik hacim kırılması YOK.
Hüküm: iki kaynak AYNI ayarlama politikasında (yalnız bölünme-düzeltmeli) → kapı AÇIK. Yerel
`--dogrula` koşulursa hüküm ONUN olur ve "uyumsuz" derse kapı kapanır; taban yerel kanıtı ezemez.

Anahtar YOKSA hiçbir şey değişmez: uçlar None döner, zincir FMP→Cboe→Nasdaq olarak aynen sürer.
Bugün worker'da anahtar yoktur (Claude eklentisinin anahtarı worker'a AKMAZ) — yani bu modül
panoya `MASSIVE_API_KEY` girilene kadar çalışma zamanında HİÇBİR davranışı değiştirmez.
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from collections import deque

import httpx

from .. import secrets

BASE = "https://api.massive.com"
KEY_NAME = "MASSIVE_API_KEY"
SOURCE_NAME = "massive"          # bars_source.json / _LAST_SOURCE'ta görünecek ad

# Ücretsiz katman sınırları (Rol 1 doküman doğrulaması)
RATE_PER_MIN = 5                 # istek/dakika
RATE_WINDOW_S = 60.0
HISTORY_YEARS = 2                # ücretsiz katmanın geçmiş derinliği — backfill için FMP gerekir
MAX_RETRY = 4                    # 429/5xx için toplam deneme
BACKOFF_BASE_S = 2.0             # 2, 4, 8 sn üstel geri çekilme

SNAPSHOT_FILE = "massive_grouped_last.json"   # {date, fetched_at, bars:{T:{...}}} — süreçler arası tek çağrı
VERIFY_FILE = "massive_verify.json"           # --dogrula ölçümünün SONUCU; write_enabled() bunu okur

# --- TABAN ÖLÇÜMÜ: yazım kapısının dayandığı KANIT (Rol 1, 2026-07-29) -------------------------
# Brief'in 2. maddesi "ayarlama (adjusted) tutarlılığı ÖLÇÜLECEK, varsayılmayacak" diyordu. Ölçümü
# Rol 1 yaptı (operatör Massive'i Claude eklentisi olarak kurmuştu; MCP kanalı üzerinden canlı API).
# Bu sabit, kapının HANGİ kanıta dayandığını koda yazar — kapı "öylesine açık" değil, ATIFLI ve
# ÇÜRÜTÜLEBİLİR bir ölçüme dayalı olarak açıktır. Yerel `--dogrula` koşulduğu anda bu tabanı EZER
# (en taze kanıt kazanır); yerel ölçüm "uyumsuz" derse kapı kapanır.
#
# DÜZELTME (bu ajanın ölçümü): Rol 1 kıyas tarafını "FMP önbelleği" diye adlandırdı; canlı defter
# (state/bars_source.json) geçmişin sahibinin cboe=192 + nasdaq=59, FMP=0 olduğunu gösteriyor. Yani
# kıyas fiilen Massive↔Cboe/Nasdaq idi — ki Massive'in üstüne EKLEYECEĞİ ölçek tam olarak budur.
# Kıyas yanlış adlandırılmıştı ama DOĞRU tarafı ölçmüş: sonuç daha da yerinde.
BASELINE = {
    "by": "Rol 1 + Rol 2 (bağımsız tekrar)",
    "method": "MCP (massive.com Claude eklentisi) üzerinden canlı API",
    "at": "2026-07-29", "grouped_rows_single_call": 12482,
    "comparisons": [
        {"date": "2026-07-24", "symbols": 25, "max_abs_dev_pct": 0.000, "by": "Rol 1",
         "note": "temettü ödeyenler + bölünme geçmişi olanlar dahil"},
        {"date": "2026-05-15", "symbols": 12, "max_abs_dev_pct": 0.000, "by": "Rol 1",
         "note": "arada temettü ex-tarihi geçen KO/PEP/O/VZ/MO — temettü düzeltmesi olsaydı tam "
                 "orada ayrışırlardı, ayrışmadılar"},
        {"date": "2026-07-28", "symbols": 251, "max_abs_dev_pct": 0.081, "by": "Rol 2",
         "note": "TÜM önbellek evreni. Rol 1'in 25/12 sembollük örneklemi %0.000 vermişti; 251 "
                 "sembolde en kötü hâl %0.081 (T), %0.1 toleransını aşan 0/251. Sapmalar "
                 "DAĞINIK (%0.01–0.08), çarpımsal DEĞİL — bölünme 2x/4x, temettü %1–15 sabit "
                 "kayma üretirdi. Yani ölçek uyumu doğrulandı, ama 'sıfır sapma' DOĞRU DEĞİL: "
                 "iyi huylu gürültü tabanı ~%0.08 (bkz. data.MASSIVE_TOL gerekçesi)"},
    ],
    "volume_check": {"date": "2026-07-28", "symbols": 251, "median_ratio": 1.000,
                     "note": "HACİM EKSENİ DE ÖLÇÜLDÜ (brief bunu istemiyordu ama bar yazan bir "
                             "kaynak hacmi de yazar): 239/251 birebir aynı, medyan oran 1.000 — "
                             "sistematik hacim ölçeği kırılması YOK. 12 sembolde oran 1.10–2.32; "
                             "bunlar bizim önbelleğimizdeki YARIM/gecikmeli barlar (aynı semboller "
                             "en yüksek fiyat sapmasını da gösteriyor), Massive'in barı daha tam."},
    "verdict": "uyumlu",
    "detail": "iki kaynak AYNI ayarlama politikasında: yalnız BÖLÜNME-düzeltmeli (temettü düzeltmesi "
              "YOK). Fiyat ekseninde sistematik kayma yok (en kötü %0.081, dağınık), hacim ekseninde "
              "medyan oran 1.000. Zincire YAZIM modunda bağlanması ölçüyle desteklenir.",
}

# --- yazım kapısının eşikleri (ölçüm → karar) -------------------------------------------------
VERIFY_TOL = 0.001               # %0.1 — aynı ticker+gün kapanış farkı bu üstündeyse "uyuşmazlık"
VERIFY_MIN_SAMPLES = 50          # bu kadar ÖRTÜŞEN bar ölçülmeden yazım AÇILMAZ
VERIFY_MAX_MISMATCH = 0.02       # örneklemin %2'sinden fazlası toleransı aşarsa ölçek UYUMSUZ sayılır
VERIFY_MAX_AGE_DAYS = 30         # ölçüm bayatlarsa kapı KAPANIR (sağlayıcı sessizce ölçek değiştirebilir)
ROUND_EPS = 0.005                # CSV'deki yuvarlama payı (yarım cent) — ucuz hisselerde sahte sapma olmasın

_HEALTH = {"ok": None, "calls": 0, "fails": 0, "last_status": None, "last_error": "", "at": None,
           "rate_waits": 0, "retries": 0}
_LOCK = threading.RLock()
_CALLS: deque = deque()          # token bucket: son RATE_WINDOW_S içindeki istek zaman damgaları
_MEM_SNAPSHOT: dict = {}         # {date: {TICKER: bar}} — süreç-içi memo (aynı turda tek çağrı)
_FAIL_AT: dict[str, float] = {}  # {date: _now()} — BAŞARISIZ denemenin zamanı (aşağıdaki gerekçe)
FAIL_COOLDOWN_S = 300.0          # başarısız grouped denemesi bu süre boyunca TEKRARLANMAZ
_NO_KEY_LOGGED = False


# ---------------------------------------------------------------- altyapı
def _sleep(seconds: float) -> None:
    """Uyku TEK NOKTADAN geçer ki testler ağa da saate de dokunmadan geri çekilmeyi ölçebilsin."""
    time.sleep(seconds)


def _now() -> float:
    """Saat de tek noktadan. Testin stdlib `time`ı yamalaması gerekseydi yama süresince TÜM suite
    aynı sahte saati görürdü — ölçmek istediğimiz şeyin yanında istemediğimiz yan etki."""
    return time.monotonic()


def available() -> bool:
    """ANAHTAR VAR demektir — ÇALIŞIYOR demek DEĞİL (fmp.available() ile aynı disiplin).
    Üretim sorusunun cevabı health()."""
    return bool(secrets.get(KEY_NAME))


def health() -> dict:
    return dict(_HEALTH)


def _note_no_key() -> None:
    """YASA 4: yokluk KAYDEDİLİR, sessiz değil. Süreç başına bir kez — 250 sembollük turda 250 satır
    basmak sinyali gürültüye çevirirdi."""
    global _NO_KEY_LOGGED
    if _NO_KEY_LOGGED:
        return
    _NO_KEY_LOGGED = True
    try:
        from .. import obs
        obs.log("massive_disabled_no_key", key=KEY_NAME,
                detail="MASSIVE_API_KEY girilmemiş — artımlı grouped yolu KAPALI; bar zinciri "
                       "FMP→Cboe→Nasdaq ile aynen sürüyor (davranış değişmedi)")
    except Exception:
        # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci kanal yok; telemetri denemesi
        # çağıranı ASLA düşüremez.
        pass


class MassiveError(RuntimeError):
    """İstek başarısız — "sağlayıcı veri yok dedi" ile KARIŞTIRILMAMALI.

    `.reason` kısa ve makine-okunur ("HTTP 429", "ConnectTimeout"). URL/anahtar ASLA taşınmaz:
    anahtar Authorization başlığında gider ama httpx'in hata metni tam URL'i içerir ve o metin bir
    gün loglanırsa sorgu parametreleri diske düşer."""

    def __init__(self, reason: str, status: int | None = None):
        super().__init__(f"massive isteği başarısız: {reason}")
        self.reason = reason
        self.status = status


def _throttle() -> None:
    """5 istek/dk token-bucket. Pencere dolduysa EN ESKİ isteğin süresi dolana kadar bekler.
    Grouped kullanımında günde ~1 çağrı olduğu için bu yol pratikte hiç ısınmaz — ama `--dogrula`
    çok sembollü koşarken sağlayıcıyı dövmemek için ZORUNLU."""
    while True:
        with _LOCK:
            now = _now()
            while _CALLS and (now - _CALLS[0]) >= RATE_WINDOW_S:
                _CALLS.popleft()
            if len(_CALLS) < RATE_PER_MIN:
                _CALLS.append(now)
                return
            wait = RATE_WINDOW_S - (now - _CALLS[0]) + 0.01
            _HEALTH["rate_waits"] += 1
        _sleep(max(wait, 0.0))


def _get(path: str, params: dict | None = None, timeout: float = 30.0) -> dict:
    """Tek GET: hız sınırı + 429/5xx'te üstel geri çekilme + sağlık muhasebesi.

    Anahtar `Authorization: Bearer` BAŞLIĞINDA gider, sorgu parametresinde DEĞİL — parametre olsaydı
    her hata metni ve her ara-vekil logu anahtarı taşırdı (FMP tarafında tam olarak bu yüzden
    `_redact` yazılmıştı). 401/403 geri çekilmeyle çözülmez, hemen fırlatılır."""
    key = secrets.get(KEY_NAME)
    if not key:
        _note_no_key()
        raise MassiveError("anahtar yok")
    import datetime as _dt
    url = f"{BASE}/{path.lstrip('/')}"
    headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
    reason, status = "bilinmiyor", None
    for attempt in range(MAX_RETRY):
        _throttle()
        with _LOCK:
            _HEALTH["calls"] += 1
            _HEALTH["at"] = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
        try:
            r = httpx.get(url, params=params or {}, headers=headers, timeout=timeout)
            status = r.status_code
            _HEALTH["last_status"] = status
            if status == 429 or status >= 500:
                # 429 = kota/hız; 5xx = sağlayıcı arızası. İKİSİ DE geçicidir → geri çekil.
                reason = f"HTTP {status}"
                _HEALTH["fails"] += 1
                if attempt < MAX_RETRY - 1:
                    _HEALTH["retries"] += 1
                    _sleep(BACKOFF_BASE_S * (2 ** attempt))     # 2, 4, 8 sn
                    continue
                break
            r.raise_for_status()
            data = r.json()
            _HEALTH.update({"ok": True, "last_error": ""})
            return data if isinstance(data, dict) else {"results": data}
        except httpx.HTTPStatusError as e:
            # 4xx (401/403/404): geri çekilme ÇÖZMEZ — anahtar yanlış ya da yol yok.
            status = getattr(getattr(e, "response", None), "status_code", status)
            reason = f"HTTP {status}"
            _HEALTH["fails"] += 1
            break
        except Exception as e:
            reason = type(e).__name__
            _HEALTH["fails"] += 1
            if attempt < MAX_RETRY - 1:
                _HEALTH["retries"] += 1
                _sleep(BACKOFF_BASE_S * (2 ** attempt))
                continue
            break
    _HEALTH.update({"ok": False, "last_error": reason})
    raise MassiveError(reason, status)


# ---------------------------------------------------------------- uçlar
def grouped_daily(date: str, adjusted: bool = True, include_otc: bool = False) -> list[dict] | None:
    """TÜM ABD piyasasının `date` günündeki EOD barları — TEK ÇAĞRI. Bu modülün varlık sebebi.

    None  = istek atılamadı/patladı (anahtar yok, 429, ağ) — sembol/gün hakkında HÜKÜM YOK
    []    = sağlayıcı DÜZGÜN cevap verdi ama sıfır satır (hafta sonu/tatil — seans yok)
    [..]  = ham results[] (T/o/h/l/c/v/vw/t/n)
    """
    if not available():
        _note_no_key()
        return None
    try:
        d = _get(f"/v2/aggs/grouped/locale/us/market/stocks/{date}",
                 {"adjusted": "true" if adjusted else "false",
                  "include_otc": "true" if include_otc else "false"})
    except MassiveError as e:
        _warn("massive_grouped_failed", date=date, reason=e.reason)
        return None
    rows = d.get("results") or []
    return [r for r in rows if isinstance(r, dict) and r.get("T")]


def custom_bars(ticker: str, start: str, end: str, multiplier: int = 1,
                timespan: str = "day") -> list[dict] | None:
    """Tek sembolün [start, end] aralığındaki barları. Grouped'ın YEDEĞİ ve `--dogrula`nın ölçüm
    aracı; günlük tazelemede KULLANILMAZ (sembol başına istek = kaçınmaya çalıştığımız şeyin ta
    kendisi). None/[] ayrımı grouped_daily ile aynı."""
    if not available():
        _note_no_key()
        return None
    if not ticker:
        return None
    try:
        d = _get(f"/v2/aggs/ticker/{ticker.upper()}/range/{int(multiplier)}/{timespan}/{start}/{end}",
                 {"adjusted": "true", "sort": "asc", "limit": 50000})
    except MassiveError as e:
        _warn("massive_custom_bars_failed", ticker=ticker.upper(), reason=e.reason)
        return None
    return [r for r in (d.get("results") or []) if isinstance(r, dict)]


def all_tickers(limit: int = 1000, active: bool = True) -> list[dict] | None:
    """Referans sembol listesi (tek sayfa). Evren bakımı/doğrulama için; karar yoluna BAĞLI DEĞİL."""
    if not available():
        _note_no_key()
        return None
    try:
        d = _get("/v3/reference/tickers",
                 {"market": "stocks", "active": "true" if active else "false",
                  "limit": int(limit)})
    except MassiveError as e:
        _warn("massive_all_tickers_failed", reason=e.reason)
        return None
    return [r for r in (d.get("results") or []) if isinstance(r, dict)]


def _warn(event: str, **fields) -> None:
    try:
        from .. import obs
        obs.warn(event, **fields)
    except Exception:
        # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci kanal yok; telemetri çağıranı düşüremez
        pass


# ---------------------------------------------------------------- alan eşlemesi
def bar_date(ms: int):
    """Unix ms → SEANS TARİHİ.

    CANLI ÖLÇÜM (2026-07-29): sağlayıcı günlük barın damgasını seans KAPANIŞINDA verir — 2026-07-28
    barı için t=1785268800000 = 20:00Z = **16:00 ET**. (Doküman bunu yazmıyordu; ilk yazımda "seans
    başlangıcı, 04:00Z" varsayılmıştı ve bu YANLIŞTI.) Kışın aynı an 21:00Z olur.

    ET'ye çevirip normalize etmek her iki hâlde de doğru seans gününü verir. Ham UTC tarihini almak
    16:00 ET damgası için de tesadüfen çalışır (20:00Z ve 21:00Z aynı takvim günündedir), ama
    sağlayıcı damgayı bir gün 20:00 ET'ye (= ertesi gün 00:00Z) taşırsa ham UTC bir gün KAYARDI —
    açık çeviri o riski kapatır."""
    import pandas as pd
    return (pd.to_datetime(int(ms), unit="ms", utc=True)
            .tz_convert("America/New_York").normalize().tz_localize(None))


def to_bar(row: dict, date=None) -> dict | None:
    """Ham results[] satırı → bizim bar sözlüğümüz. FAZLA alan (vw, n, otc, T) ATILIR; eksik alan
    None kalır ve çağıran onu düşürür. `date` verilirse (grouped'da istenen gün) o kullanılır —
    grouped için istenen tarih, damgadan türetmekten daha güvenilir bir kimliktir."""
    import pandas as pd
    if not isinstance(row, dict):
        return None
    try:
        d = pd.Timestamp(date) if date is not None else (bar_date(row["t"]) if row.get("t") else None)
    except Exception:  # sessiz-yutma: sağlayıcının biçimsiz TEK satırı; tarihi çözülemeyen bar DÜŞER (None) ve çağıran onu atar — 12.400 satırlık grouped yanıtında satır başına uyarı log seli olurdu
        return None
    if d is None:
        return None
    out = {"date": d}
    for src, dst in (("o", "open"), ("h", "high"), ("l", "low"), ("c", "close"), ("v", "volume")):
        v = row.get(src)
        try:
            out[dst] = float(v) if v is not None else None      # eksik alan → None
        except (TypeError, ValueError):  # sessiz-yutma: tek ALANIN biçimi bozuk; None kalır ve kapanış None ise satır zaten düşer — bar başına uyarı basmak grouped turunda gürültü olurdu
            out[dst] = None
    if out["close"] is None:
        return None                                             # kapanışsız bar bar değildir
    return out


def to_frame(rows: list[dict], date=None):
    """results[] → COLS şemasında DataFrame (date,open,high,low,close,volume). vw/n atılır."""
    import pandas as pd
    recs = [b for b in (to_bar(r, date) for r in (rows or [])) if b]
    if not recs:
        return pd.DataFrame()
    df = pd.DataFrame(recs)
    return df[["date", "open", "high", "low", "close", "volume"]].sort_values("date").reset_index(drop=True)


# ---------------------------------------------------------------- günlük anlık görüntü (tek çağrı)
def _store():
    from .. import store
    return store


def last_session(end=None, back: int = 0) -> str:
    """`end`den geriye doğru `back` iş günü. Hafta sonu/tatilde grouped boş döner; çağıran birkaç gün
    geri deneyebilsin diye tarih üretimi TEK yerde."""
    import datetime as _dt
    import pandas as pd
    d = pd.Timestamp(end) if end is not None else pd.Timestamp(_dt.date.today())
    days = pd.bdate_range(end=d, periods=max(back, 0) + 1)
    return str(days[0].date())


def snapshot(date: str | None = None, max_back: int = 3, end=None) -> dict:
    """O günün TÜM piyasa barları: {TICKER: bar}. TEK grouped çağrısıyla doldurulur ve hem süreç-içi
    hem DİSKTE önbelleklenir — 250 sembollük tur boyunca ikinci bir istek atılmaz, süreç yeniden
    başlasa bile (zamanlayıcı + API ayrı süreçler) gün içinde tekrar çağrılmaz.

    `date` verilmezse son iş gününden başlayıp en çok `max_back` gün geriye yürür: tatil günlerinde
    grouped DÜZGÜNCE boş döner ve bir önceki seans denenir. Boş sözlük = veri yok (anahtar yok,
    istek patladı ya da geriye yürüyüş boyunca seans bulunamadı)."""
    wanted = date or last_session(end)
    if wanted in _MEM_SNAPSHOT:
        return _MEM_SNAPSHOT[wanted]
    if not available():
        _note_no_key()
        return {}
    # BAŞARISIZLIK DA HATIRLANIR (yoksa tek arıza saatlerce sürer): `bar_for` TİCKER BAŞINA çağrılır.
    # Başarısız denemeyi hatırlamazsak 250 sembollük bir tur, aynı düşmüş grouped çağrısını 250 KEZ
    # dener; her deneme 4 tekrar + üstel bekleme (2+4+8sn) + 5/dk kovası demektir. Yani bir dakikalık
    # sağlayıcı arızası, tazelemeyi saatlerce bloke ederdi. Soğuma penceresi hasarı "tur başına 250
    # deneme"den "5 dakikada 1 deneme"ye indirir; kalıcı arızada zincir zaten FMP/Cboe'ye düşer.
    son_hata = _FAIL_AT.get(wanted)
    if son_hata is not None and (_now() - son_hata) < FAIL_COOLDOWN_S:
        return {}
    disk = _read_snapshot_disk()
    if disk.get("date") == wanted and disk.get("bars"):
        _MEM_SNAPSHOT[wanted] = disk["bars"]
        return disk["bars"]
    # tarih VERİLMİŞSE geriye yürüme (çağıran o günü istedi); verilmemişse son seansı ara
    tries = [wanted] if date else [last_session(end, back=i) for i in range(max_back + 1)]
    for d in tries:
        rows = grouped_daily(d)
        if rows is None:
            _FAIL_AT[wanted] = _now()       # istek patladı — HÜKÜM YOK ama tekrar tekrar deneme
            return {}
        if not rows:
            continue                        # seans yok (hafta sonu/tatil) — bir öncekine bak
        bars = {}
        for r in rows:
            b = to_bar(r, date=d)
            if b:
                b["date"] = str(b["date"].date())
                bars[str(r["T"]).upper()] = b
        _MEM_SNAPSHOT[d] = bars
        _MEM_SNAPSHOT[wanted] = bars
        _write_snapshot_disk(d, bars)
        try:
            from .. import obs
            obs.log("massive_grouped_snapshot", date=d, tickers=len(bars), calls=1,
                    detail="TÜM ABD piyasasının EOD barları TEK çağrıda alındı")
        except Exception:
            # sessiz-yutma: kayıt kanalı düştü; anlık görüntünün kendisi geçerli
            pass
        return bars
    _FAIL_AT[wanted] = _now()               # hiçbir denemede seans bulunamadı — aynı soğuma geçerli
    return {}


def _read_snapshot_disk() -> dict:
    try:
        return _store().read_json(SNAPSHOT_FILE, {}) or {}
    except Exception:
        # sessiz-yutma: önbellek okunamazsa yalnız bir çağrı fazladan atılır; karar etkilenmez
        return {}


def _write_snapshot_disk(date: str, bars: dict) -> None:
    import datetime as _dt
    try:
        _store().write_json(SNAPSHOT_FILE, {
            "date": date, "tickers": len(bars),
            "fetched_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "bars": bars})
    except Exception as e:
        _warn("massive_snapshot_write_failed", error=f"{type(e).__name__}: {e}")


def latest_bar(ticker: str, end=None) -> dict | None:
    """Sembolün `end`e kadarki EN TAZE YAYINLANMIŞ barı — artımlı tazelemenin kullandığı yol.

    NEDEN `bar_for` DEĞİL (canlı bulgu, 2026-07-29): artımlı kol önce `bar_for(t, last_session(end))`
    kullanıyordu, yani TEK ve KESİN bir gün istiyordu. `end` bugün olduğunda ve günün EOD'si henüz
    yayınlanmadığında grouped boş döner → kol boş döner → zincir Cboe'ye düşer. Canlı defterde tam
    bunu gördük: 250 ticker'ın hepsi `source=cboe` ile kaydedilmişti, yani kotayı kurtaran yol hiç
    devreye girmemişti. Doğru davranış "bugünün barı" değil "ELDEKİ EN TAZE bar"dır: geriye yürüyüş
    (snapshot max_back) dünün barını bulur, dikiş koruması da onu yalnız önbellekten YENİ ise ekler.
    Yani gün içinde çalışan bir tazeleme de kotasız ilerler."""
    snap = snapshot(end=end)
    return snap.get(ticker.upper()) if snap else None


def bar_for(ticker: str, date: str) -> dict | None:
    """Tek sembolün `date` günündeki Massive barı — anlık görüntüden okunur, EK İSTEK YOK.
    Çapraz doğrulamanın sıcak yolu budur: 250 sembol için toplam 1 çağrı."""
    snap = snapshot(date)
    return snap.get(ticker.upper()) if snap else None


HISTORY_MARGIN_DAYS = 30         # 2 yıl sınırına bu kadar YAKLAŞMA — sağlayıcının kesme noktası tam
                                 # 2 yıl olmayabilir; sınırda yarım seri almak sessiz veri kaybı olurdu


def covers(start: str) -> bool:
    """Massive'in ÜCRETSİZ katmanı `start`e kadar uzanıyor mu? (~2 yıl)

    NEDEN KAPI: derin tarih isteyen bir çağrıya Massive BOŞ ya da YARIM seri döndürür. Boş dönüş
    yedek zincirini kirletir (bir kol daha 'denendi ve veremedi' diye kaydedilir); YARIM seri ise
    çok daha kötüdür — sessizce kısa bir geçmiş yazılır ve walk-forward ısınmasız barlarla koşar.
    Bu yüzden 2 yıldan eski başlangıç isteyen çağrılar Massive'e HİÇ SORULMAZ, doğrudan FMP'ye gider.
    Üretimdeki toplu yol (dataset.FETCH_START = 2021-01-01) tam olarak bu sınıfa girer — yani evren
    tazelemesi asla sembol-başına Massive isteğine dönüşemez (5/dk sınırı 250 sembolü kaldırmaz)."""
    try:
        import datetime as _dt
        import pandas as pd
        sinir = (pd.Timestamp(_dt.date.today())
                 - pd.DateOffset(years=HISTORY_YEARS)
                 + pd.Timedelta(days=HISTORY_MARGIN_DAYS))
        return pd.Timestamp(start) >= sinir
    except Exception:  # sessiz-yutma: tarih ayrıştırılamadı → MUHAFAZAKÂR taraf (False = Massive'e hiç sorma, FMP'de kal); yokluk davranışı zincirin eski hâli olduğu için karar bozulmaz
        return False


def reset_cache() -> None:
    """Süreç-içi anlık görüntü memosunu (ve başarısızlık soğumasını) temizle — testler, gün dönümü."""
    _MEM_SNAPSHOT.clear()
    _FAIL_AT.clear()


# ---------------------------------------------------------------- yazım kapısı (ölçüm → karar)
def verify_state() -> dict:
    try:
        return _store().read_json(VERIFY_FILE, {}) or {}
    except Exception:
        # sessiz-yutma: defter okunamazsa kapı KAPALI kabul edilir — muhafazakâr taraf
        return {}


def verify_basis() -> dict:
    """Kapı HANGİ kanıta dayanıyor? Yerel `--dogrula` ölçümü varsa O (en taze kanıt kazanır);
    yoksa Rol 1'in taban ölçümü. Bu fonksiyon olmadan operatör "neden yazım modundayız" sorusunu
    tahminle cevaplardı — kapının gerekçesi her zaman okunabilir olmalı."""
    v = verify_state()
    if v.get("verdict"):
        return {"basis": "yerel_olcum", "verdict": v.get("verdict"), "samples": v.get("samples"),
                "checked_at": v.get("checked_at"), "max_dev": v.get("max_dev")}
    return {"basis": "rol1_taban", "verdict": BASELINE["verdict"], "at": BASELINE["at"],
            "method": BASELINE["method"], "detail": BASELINE["detail"]}


def write_enabled() -> bool:
    """Massive barları YAZIM zincirine girsin mi?

    KARAR ÖLÇÜMEDİR, VARSAYIM DEĞİL. İki kanıt kaynağı vardır ve YEREL olan tabanı EZER:

      1) YEREL ölçüm (`--dogrula`) varsa hüküm ONUNDUR: "uyumlu" + yeterli örneklem + bayatlamamış
         olmalı. "uyumsuz" derse kapı KAPANIR — taban ölçümü bunu geçersiz kılamaz, çünkü yerel
         ölçüm bu makinenin GERÇEK önbelleğiyle yapılmıştır ve daha tazedir.
      2) Yerel ölçüm yoksa Rol 1'in TABAN ölçümü (BASELINE) geçerlidir: 2026-07-29'da MCP kanalıyla,
         iki ayrı tarihte, temettü ex-tarihi geçen isimler dahil, maksimum sapma %0.0000.

    Neden bu kadar titiz: Massive `adjusted=true` ile bölünme-düzeltmeli seri verir; önbellekteki
    geçmişi Cboe/Nasdaq sahipleniyor. İki kaynak AYNI ölçekte DEĞİLSE yeni barı eskisinin üstüne
    eklemek sahte bir gecelik uçurum imal eder ve her hareketli ortalamayı zehirler — bu depoda
    canlıda YAŞANMIŞ bir hata sınıfı (data.py D1 dikiş koruması). Ölçüm tam da bunu dışladı.

    Anahtar yoksa her hâlükârda False: kapı açık olsa bile çağıracak bir uç yok."""
    if not available():
        return False
    taban = BASELINE["verdict"] == "uyumlu"
    v = verify_state()
    if v.get("verdict") == "uyumsuz":
        return False        # ÇÜRÜTÜLDÜ: yerel ölçüm ölçekleri farklı buldu. Yaşına BAKILMAZ — bir
                            # çürütme, yeni bir ölçümle geçersizleşene kadar geçerlidir.
    if v.get("verdict") != "uyumlu":
        return taban        # ölçüm yok / yetersiz örneklem / ölçülemedi → ÇÜRÜTME DEĞİL, tabana dön
    if int(v.get("samples") or 0) < VERIFY_MIN_SAMPLES:
        return taban        # zayıf onay da çürütme değildir
    # BAYATLIK ≠ ÇELİŞKİ (2026-07-29). İlk yazımda bayat ölçüm kapıyı KAPATIYORDU ve bu sessiz bir
    # ZAMAN BOMBASIYDI: 30 gün sonra yazım modu kendiliğinden kapanır, zincir sembol-başına FMP'ye
    # döner ve kota yağmuru (250 istek/tazeleme) hiçbir şey değişmemiş gibi geri gelirdi — kimse de
    # sebebini bilmezdi. Ölçümün ESKİMESİ, ölçeklerin AYRIŞTIĞININ kanıtı değildir. Doğru davranış:
    # tabana dön (davranış korunur) ve yeniden ölçüm GEREKTİĞİNİ söyle. Gerçek çelişki yukarıda,
    # "uyumsuz" dalında, yaştan bağımsız olarak kapıyı kapatır.
    try:
        import datetime as _dt
        at = _dt.datetime.fromisoformat(str(v.get("checked_at")).replace("Z", "+00:00"))
        if (_dt.datetime.now(_dt.timezone.utc) - at).days > VERIFY_MAX_AGE_DAYS:
            _warn("massive_verify_stale", checked_at=v.get("checked_at"),
                  max_age_days=VERIFY_MAX_AGE_DAYS,
                  detail="yerel ayarlama ölçümü bayatladı — `python -m meridian.adapters.massive "
                         "--dogrula` ile yenile. Kapı KAPATILMADI (bayatlık çelişki değildir); "
                         "taban ölçümü yürürlükte")
            return taban
    except Exception:  # sessiz-yutma: damgası okunamayan bir ONAY, onay sayılmaz → tabana dönülür; çürütme dalı yukarıda ve oraya hiç girmez
        return taban
    return True


def mode() -> str:
    """İnsan-okunur mod: kapali_anahtar_yok / yalniz_alarm / yazim."""
    if not available():
        return "kapali_anahtar_yok"
    return "yazim" if write_enabled() else "yalniz_alarm"


def _tol_for(close: float, tol: float) -> float:
    """Bara özgü tolerans: CSV kapanışları yuvarlanmış olabilir, yarım-cent hata ucuz hisselerde
    %0.1'i tek başına aşar. Sahte uyuşmazlık üretmemek için taban tolerans yuvarlama payıyla
    genişletilir. (Pahalı hisselerde etkisi yok: 0.005/740 ≈ %0.0007.)"""
    try:
        c = float(close)
        return max(tol, ROUND_EPS / c) if c > 0 else tol
    except (TypeError, ValueError):  # sessiz-yutma: yuvarlama payı hesaplanamadı → TABAN tolerans kullanılır; yalnız eşiği bir tık sıkılaştırır, ölçümü bozmaz
        return tol


def compare(ref: dict, mas: dict, tol: float = VERIFY_TOL) -> dict:
    """İki {tarih: kapanış} haritasını ÖRTÜŞEN günlerde karşılaştır. Saf fonksiyon — ağ yok, yazım
    yok — ki ölçüm mantığı testte çivilenebilsin."""
    dates = sorted(set(ref) & set(mas))
    devs, worst, worst_d = [], 0.0, None
    mism = 0
    for d in dates:
        try:
            a, b = float(ref[d]), float(mas[d])
        except (TypeError, ValueError):  # sessiz-yutma: o GÜNÜN kapanışı sayı değil; yalnız o gün örneklemden düşer ve `samples` sayacı bunu zaten görünür kılar
            continue
        if a <= 0:
            continue
        dev = abs(b - a) / a
        devs.append(dev)
        if dev > _tol_for(a, tol):
            mism += 1
        if dev > worst:
            worst, worst_d = dev, d
    n = len(devs)
    return {"samples": n, "mismatches": mism,
            "mismatch_pct": round(mism / n, 4) if n else None,
            "max_dev": round(worst, 6) if n else None, "max_dev_date": worst_d,
            "mean_dev": round(sum(devs) / n, 6) if n else None}


def _cache_closes(ticker: str, since: str) -> dict:
    """Diskteki bar önbelleğinden {tarih: kapanış} — AĞ YOK. Karşılaştırmanın referans tarafı budur:
    canlı kanıt (state/bars_source.json) geçmişin bugün Cboe(192)/Nasdaq(59) tarafından sahiplenildiğini,
    FMP'nin HİÇBİR sembolün geçmişini yazmadığını gösteriyor — yani Massive'in fiilen ekleneceği
    ölçek BU dosyalardaki ölçektir."""
    import pandas as pd
    from . import data as _data
    cp = _data._cache_path(ticker)
    if not cp.exists():
        return {}
    try:
        df = pd.read_csv(cp, parse_dates=["date"])
    except Exception:
        # sessiz-yutma: tek sembolün önbelleği okunamadı; ölçüm diğer sembollerle sürer
        return {}
    df = df[df["date"] >= pd.Timestamp(since)]
    return {str(pd.Timestamp(d).date()): float(c) for d, c in zip(df["date"], df["close"])}


def _massive_closes(ticker: str, start: str, end: str) -> dict | None:
    rows = custom_bars(ticker, start, end)
    if rows is None:
        return None
    out = {}
    for r in rows:
        b = to_bar(r)
        if b:
            out[str(b["date"].date())] = b["close"]
    return out


def _fmp_closes(ticker: str, since: str) -> dict:
    from . import fmp
    out = {}
    for r in fmp.historical_eod(ticker) or []:
        d = str(r.get("date") or "")[:10]
        try:
            if d >= since:
                out[d] = float(r.get("close"))
        except (TypeError, ValueError):  # sessiz-yutma: FMP'nin biçimsiz TEK satırı; yalnız o tarih düşer, kıyas diğer günlerle sürer
            continue
    return out


def verify(symbols: list[str] | None = None, days: int = 60, tol: float = VERIFY_TOL,
           use_fmp: bool = False, write: bool = True) -> dict:
    """AYARLAMA (adjusted) TUTARLILIK ÖLÇÜMÜ — yazım kapısının dayanağı.

    Massive'in son `days` günlük barlarını, ÖRTÜŞEN günlerde iki referansla karşılaştırır:
      * `cache`  — diskteki bar önbelleği (Cboe/Nasdaq ölçeği). Massive fiilen BUNUN üstüne
                   ekleyeceği için kapıyı BU kıyas belirler. Ek ağ maliyeti: sembol başına 1 Massive
                   isteği (5/dk sınırına uyularak).
      * `fmp`    — yalnız `use_fmp=True` iken. SEMBOL BAŞINA 1 FMP isteği harcar (kota!), bu yüzden
                   varsayılan KAPALI. Brief'in istediği kıyas budur; ölçülür ve raporlanır ama kapıyı
                   tek başına açmaz — çünkü FMP bugün hiçbir sembolün geçmişini sahiplenmiyor.

    Hüküm: yeterli örneklem VE toleransı aşan bar oranı eşiğin altında ise "uyumlu". Aksi hâlde
    "uyumsuz" — ve `write_enabled()` kapalı kalır, yani zincire DOKUNULMAZ (yalnız-alarm sürer).
    """
    import datetime as _dt
    import pandas as pd
    end = str(_dt.date.today())
    start = str((pd.Timestamp(end) - pd.Timedelta(days=int(days))).date())
    if not symbols:
        from . import data as _data
        symbols = [t for t in _data.REPLAY_UNIVERSE if _data._cache_path(t).exists()][:8]
    out = {"checked_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
           "window": {"start": start, "end": end, "days": int(days)}, "tol": tol,
           "symbols": list(symbols), "per_symbol": {}, "reference": "cache",
           "thresholds": {"min_samples": VERIFY_MIN_SAMPLES, "max_mismatch": VERIFY_MAX_MISMATCH}}
    if not available():
        out.update({"verdict": "olculemedi", "reason": "MASSIVE_API_KEY yok", "samples": 0})
        return out
    tot_s = tot_m = 0
    worst, worst_sym = 0.0, None
    fmp_s = fmp_m = 0
    for sym in symbols:
        mas = _massive_closes(sym, start, end)
        if mas is None:
            out["per_symbol"][sym] = {"error": "massive_istegi_basarisiz"}
            continue
        if not mas:
            out["per_symbol"][sym] = {"error": "massive_bos"}
            continue
        row = {"massive_bars": len(mas)}
        c = compare(_cache_closes(sym, start), mas, tol)
        row["cache"] = c
        tot_s += c["samples"]; tot_m += c["mismatches"]
        if c["max_dev"] and c["max_dev"] > worst:
            worst, worst_sym = c["max_dev"], sym
        if use_fmp:
            f = compare(_fmp_closes(sym, start), mas, tol)
            row["fmp"] = f
            fmp_s += f["samples"]; fmp_m += f["mismatches"]
        out["per_symbol"][sym] = row
    out.update({"samples": tot_s, "mismatches": tot_m,
                "mismatch_pct": round(tot_m / tot_s, 4) if tot_s else None,
                "max_dev": round(worst, 6) if tot_s else None, "max_dev_symbol": worst_sym})
    if use_fmp:
        out["fmp_totals"] = {"samples": fmp_s, "mismatches": fmp_m,
                             "mismatch_pct": round(fmp_m / fmp_s, 4) if fmp_s else None}
    if tot_s < VERIFY_MIN_SAMPLES:
        out["verdict"] = "yetersiz_orneklem"
        out["reason"] = f"{tot_s} örtüşen bar < gereken {VERIFY_MIN_SAMPLES}"
    elif (tot_m / tot_s) > VERIFY_MAX_MISMATCH:
        out["verdict"] = "uyumsuz"
        out["reason"] = (f"örneklemin %{100 * tot_m / tot_s:.2f}'i %{100 * tol:.2f} toleransını aşıyor "
                         f"— ölçekler farklı; zincir KARIŞTIRILMAZ")
    else:
        out["verdict"] = "uyumlu"
        out["reason"] = f"{tot_s} barın {tot_m} tanesi toleransı aştı — aynı ayarlama ölçeği"
    if write:
        try:
            _store().write_json(VERIFY_FILE, out)
        except Exception as e:
            _warn("massive_verify_write_failed", error=f"{type(e).__name__}: {e}")
    try:
        from .. import obs
        obs.log("massive_verify", verdict=out["verdict"], samples=tot_s, mismatches=tot_m,
                max_dev=out.get("max_dev"), mode_after=mode())
    except Exception:
        # sessiz-yutma: kayıt kanalı düştü; ölçüm dosyası zaten yazıldı
        pass
    return out


def ping() -> dict:
    """Pano "Test et" düğmesi için canlı erişilebilirlik + yetki denetimi. ANAHTARI ASLA DÖNDÜRMEZ —
    yalnız {ok, detail} (fmp.ping/finviz.ping ile aynı sözleşme).

    UÇ SEÇİMİ: grouped-daily yerine `/v3/reference/tickers?limit=1`. İkisi de TEK çağrıdır ama
    grouped ~12.400 satır indirir; referans ucu aynı yetkiyi bir satırla doğrular. Ücretsiz katman
    5 çağrı/dk olduğundan test düğmesinin ucuz olması önemlidir (operatör arka arkaya basabilir).
    401/403 = anahtar geçersiz; 429 = kota/hız (anahtar DOĞRU olabilir) — ayrı ayrı söylenir."""
    if not available():
        return {"ok": False, "detail": f"{KEY_NAME} girilmemiş"}
    try:
        d = _get("/v3/reference/tickers", {"market": "stocks", "limit": 1}, timeout=12.0)
    except MassiveError as e:
        if e.status in (401, 403):
            return {"ok": False, "detail": "anahtar geçersiz/yetkisiz"}
        if e.status == 429:
            return {"ok": False, "detail": "hız/kota sınırı (5/dk) — anahtar geçerli olabilir, "
                                           "biraz bekleyip tekrar deneyin"}
        return {"ok": False, "detail": f"bağlanılamadı ({e.reason})"}
    rows = d.get("results") or []
    if not rows:
        return {"ok": False, "detail": "beklenmedik yanıt (anahtar geçersiz olabilir)"}
    ornek = str((rows[0] or {}).get("ticker") or "?")
    return {"ok": True, "detail": f"bağlandı · örnek sembol {ornek} · mod: {mode()}"}


def status() -> dict:
    v = verify_state()
    return {"provider": "Massive", "available": available(), "mode": mode(),
            "write_enabled": write_enabled(), "basis": verify_basis(),
            "verify": {"verdict": v.get("verdict"), "samples": v.get("samples"),
                       "checked_at": v.get("checked_at"), "max_dev": v.get("max_dev")},
            "rate_limit": f"{RATE_PER_MIN}/dk", "history_years": HISTORY_YEARS,
            "reason": "" if available() else f"{KEY_NAME} yok — Ayarlar'dan ekleyin"}


# ---------------------------------------------------------------- CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m meridian.adapters.massive",
        description="Massive EOD adaptörü. AĞ ÇAĞRISI YALNIZ BURADAN (ve zincirin artımlı yolundan).")
    ap.add_argument("--durum", action="store_true", help="anahtar/mod/ölçüm durumu (AĞ YOK)")
    ap.add_argument("--dogrula", action="store_true",
                    help="AYARLAMA TUTARLILIK ÖLÇÜMÜ: Massive barlarını önbellekle karşılaştırır ve "
                         "yazım kapısının hükmünü yazar (sembol başına 1 Massive isteği)")
    ap.add_argument("--fmp", action="store_true",
                    help="--dogrula'ya FMP kıyasını da ekle (SEMBOL BAŞINA 1 FMP İSTEĞİ — kota!)")
    ap.add_argument("--sembol", action="append", default=None, metavar="TICKER",
                    help="doğrulanacak sembol (tekrarlanabilir; varsayılan: önbellekli ilk 8)")
    ap.add_argument("--gun", type=int, default=60, help="doğrulama penceresi (varsayılan 60 gün)")
    ap.add_argument("--anlik", action="store_true",
                    help="grouped anlık görüntüyü çek (TEK çağrı) ve özetini yaz")
    a = ap.parse_args(argv)

    if not any((a.durum, a.dogrula, a.anlik)):
        ap.print_help()
        return 2
    cikti: dict = {}
    if a.durum:
        cikti["durum"] = status()
    if a.anlik:
        snap = snapshot()
        ornek = sorted(snap)[:5]
        cikti["anlik"] = {"tickers": len(snap), "ornek": {k: snap[k] for k in ornek},
                          "hata": None if snap else "veri yok (anahtar/istek/seans)"}
    if a.dogrula:
        cikti["dogrula"] = verify(symbols=a.sembol, days=a.gun, use_fmp=a.fmp)
        cikti["mod_sonrasi"] = mode()
    print(json.dumps(cikti, ensure_ascii=False, indent=2, default=str))
    v = cikti.get("dogrula") or {}
    return 1 if v.get("verdict") in ("uyumsuz", "olculemedi") else 0


if __name__ == "__main__":
    sys.exit(main())

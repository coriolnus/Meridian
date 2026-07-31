"""barclock.py — Intraday LOOK-AHEAD saati (Faz 4). TEK ortak zaman kaynağı + kapanmış-bar admissibility
+ NY seans kapıları. (Faz 2'de K6 ile ertelenmişti; intraday-tüketici fazının BİRİNCİ görevi.)

LOOK-AHEAD YASASININ intraday hâli (Faz 2 look-ahead adverserinin verdiği KESİN kural): bir dakikalık bar
bir karara ancak `close_ts = parse_utc(t) + 60s` VE `karar_anı >= close_ts` iken girer. `t` dakika
BAŞLANGICI olduğundan bara `t` anında değil `t+60s` (dakika KAPANIŞI) sonrasında güvenilir — aksi hâlde
60 sn erken kabul = look-ahead deler. İki damga da BU modülden gelir (tek saat); aksi "aynı zaman iki
kaynak" ayrışmasıdır (bu kod tabanının baskın kusuru).

FAIL-CLOSED: damgasız/biçimsiz bar admissible DEĞİL — bilinmeyen tazelik 'kabul etme' demektir.

Saat ENJEKTE edilebilir (set_clock): testler gerçek zamandan bağımsız admissibility doğrular.
"""
from __future__ import annotations
import datetime as dt
from zoneinfo import ZoneInfo

UTC = dt.timezone.utc
NY = ZoneInfo("America/New_York")
BAR_SECONDS = 60                      # dakikalık bar: close = open(t) + 60s


def _default_now() -> dt.datetime:
    return dt.datetime.now(UTC)


_now_fn = _default_now                # enjekte edilebilir (testler override eder)


def set_clock(fn) -> None:
    """Saat kaynağını değiştir (YALNIZ test). fn() tz-aware UTC datetime döndürmeli."""
    global _now_fn
    _now_fn = fn


def reset_clock() -> None:
    global _now_fn
    _now_fn = _default_now


def now() -> dt.datetime:
    """Tek ortak ŞİMDİ (tz-aware UTC)."""
    return _now_fn()


def parse_utc(ts) -> dt.datetime | None:
    """RFC-3339 bar damgasını ('...Z' ya da +00:00) tz-aware UTC'ye çevir; okunamıyorsa None."""
    if not ts:
        return None
    s = str(ts).strip()
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        d = dt.datetime.fromisoformat(s)
        return d.astimezone(UTC) if d.tzinfo else d.replace(tzinfo=UTC)
    except (TypeError, ValueError):  # sessiz-yutma: biçimsiz damga = 'tazelik bilinmiyor'; çağıran fail-closed davranır (admissible değil), ayrı uyarı gereksiz
        return None


def close_ts(bar_t) -> dt.datetime | None:
    """Bir dakikalık barın KAPANIŞ anı = parse_utc(t) + 60s. t dakika BAŞLANGICIdır."""
    o = parse_utc(bar_t)
    return o + dt.timedelta(seconds=BAR_SECONDS) if o else None


def is_admissible(bar_t, as_of: dt.datetime | None = None) -> bool:
    """LOOK-AHEAD KAPISI: bu bar KARARA girebilir mi? Yalnız bar KAPANMIŞSA (as_of >= close_ts).
    Damgasız/biçimsiz bar → False (fail-closed: bilinmeyen tazelik = kabul etme)."""
    ct = close_ts(bar_t)
    if ct is None:
        return False
    a = as_of or now()
    if a.tzinfo is None:
        a = a.replace(tzinfo=UTC)
    return a >= ct


def admissible_bars(bars: list[dict], as_of: dt.datetime | None = None) -> list[dict]:
    """Bir bar listesinden yalnız KAPANMIŞ (admissible) olanları döndür — sıra korunur. Tek `as_of`
    ile ölçülür ki liste içinde saat kaymasın."""
    a = as_of or now()
    return [b for b in bars if is_admissible(b.get("t"), a)]


def age_s(bar_t, as_of: dt.datetime | None = None) -> float | None:
    """Barın KAPANIŞINDAN bu yana geçen süre (sn) = (as_of|now) - close_ts. Biçimsiz/damgasız → None
    ('tazelik bilinmiyor'). 'Tek saat, tek yer' ilkesi: bayatlık karşılaştırması da barclock'ta, tüketiciye
    saçılmaz."""
    ct = close_ts(bar_t)
    if ct is None:
        return None
    a = as_of or now()
    if a.tzinfo is None:
        a = a.replace(tzinfo=UTC)
    return (a - ct).total_seconds()


def is_fresh(bar_t, max_age_s: float, as_of: dt.datetime | None = None) -> bool:
    """Bar hem ADMISSIBLE (kapanmış) hem de TAZE mi (kapanışından beri ≤ max_age_s)? Bayat bir kapanmış
    bar (ör. akış koptu, eski bar) look-ahead güvenli ama KARARA girmemeli — eski fiyatla işlem."""
    a = age_s(bar_t, as_of)
    return a is not None and 0.0 <= a <= float(max_age_s)


# ---------------- NY SEANS (DST-farkında) ----------------
def is_market_open(at: dt.datetime | None = None) -> bool:
    """ABD hisse REGULAR seansı (9:30–16:00 ET, hafta içi) açık mı? DST'yi zoneinfo halleder. TATİLLER
    hariç (yaklaşık — kesin tatil takvimi ayrı kaynak ister; Alpaca zaten kapalıyken bar göndermez, o
    yüzden bu yalnız bir kolaylık kapısıdır, look-ahead güvenliği admissible()'a dayanır)."""
    a = at or now()
    if a.tzinfo is None:
        a = a.replace(tzinfo=UTC)
    ny = a.astimezone(NY)
    if ny.weekday() >= 5:            # Cmt/Paz
        return False
    minutes = ny.hour * 60 + ny.minute
    return 9 * 60 + 30 <= minutes < 16 * 60


def session_date(at: dt.datetime | None = None) -> str:
    """İçinde bulunulan ET seans tarihi (YYYY-MM-DD) — intraday kayıtları günle etiketlemek için."""
    a = at or now()
    if a.tzinfo is None:
        a = a.replace(tzinfo=UTC)
    return a.astimezone(NY).date().isoformat()

"""barclock.py — intraday'in TEK ortak zaman kaynağı: kapanmış-bar admissibility + NY seans kapıları.

NE YAPAR: dakikalık barların bir karara girip giremeyeceğini tek saatten yargılar. Look-ahead
yasasının intraday hâli: bir dakikalık bar bir karara ancak `close_ts = parse_utc(t) + 60s` VE
`karar_anı >= close_ts` iken girer. `t` dakika BAŞLANGICI olduğundan bara `t` anında değil dakika
KAPANIŞINDAN sonra güvenilir — aksi hâlde 60 sn erken kabul = look-ahead deler. Hem bar damgası hem
karar anı BU modülden ölçülür; aksi "aynı zamanın iki kaynağı" ayrışmasıdır — bu kod tabanının
baskın kusur sınıfı.

KİLİT GİRİŞLER: now() (tz-aware UTC tek ŞİMDİ), parse_utc(ts) (RFC-3339 → UTC; okunamazsa None),
close_ts(bar_t), is_admissible / admissible_bars (look-ahead kapısı; liste tek `as_of` ile ölçülür),
age_s / is_fresh (kapanıştan bu yana bayatlık — bayat kapanmış bar look-ahead güvenli ama karara
girmemeli), is_market_open / session_date (NY seansı; DST'yi zoneinfo halleder), set_clock /
reset_clock (YALNIZ test: saat enjeksiyonu), BAR_SECONDS=60.

DEĞİŞMEZLER: FAIL-CLOSED — damgasız/biçimsiz bar admissible DEĞİLDİR (bilinmeyen tazelik = kabul
etme). Bayatlık karşılaştırması da burada yaşar, tüketicilere saçılmaz ("tek saat, tek yer").
is_market_open tatilleri bilmez ve yalnız kolaylık kapısıdır; look-ahead güvenliği is_admissible'a
dayanır.

OKUR/YAZAR: hiçbir şey — saf zaman/aritmetik modülüdür; Redis'e, diske ve ağa dokunmaz.
"""
from __future__ import annotations
import datetime as dt
from zoneinfo import ZoneInfo

UTC = dt.timezone.utc
NY = ZoneInfo("America/New_York")
BAR_SECONDS = 60                      # dakikalık bar: close = open(t) + 60s


def _default_now() -> dt.datetime:
    """Varsayılan saat kaynağı: gerçek şimdi (tz-aware UTC)."""
    return dt.datetime.now(UTC)


_now_fn = _default_now                # enjekte edilebilir (testler override eder)


def set_clock(fn) -> None:
    """Saat kaynağını değiştir (YALNIZ test). fn() tz-aware UTC datetime döndürmeli."""
    global _now_fn
    _now_fn = fn


def reset_clock() -> None:
    """Saat kaynağını gerçek zamana geri alır (`set_clock` enjeksiyonunu iptal eder — test temizliği)."""
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


# ---------------- SABAH TETİK PENCERESİ (EXE-2026-009 + K2) ----------------
# OPERATÖR KARARI (docs/KARAR-2026-08-23-YEDI-KARAR.md K2, kanıt EDG-2026-047: açılış bandının
# menzili −%42,3 [−%44,3, −%40,1], bedel medyan +4,65 bps): canlı sabah tarama/emir tetiği
# 13:30 → 13:45 UTC. ÖLÇÜLEN MEKANİZMA (uydurma değil): kodda "13:30" diye bir gönderim sabiti
# YOKTU — sabah dolumu iki yoldan geliyordu: (a) EOD akşam gönderilen GTC marketable-limit emir
# gece boyunca DİNLENİP açılışta doluyordu, (b) intraday tarama `is_market_open` (9:30 ET)
# kapısıyla açılışta başlıyordu. Tetiği kaydırmak = (a) gönderimi pencereye ertelemek
# (loop.mirror_submit_armed pencere yasası + intraday_cycle sabah kancası) ve (b) taramayı bu
# pencereden başlatmak. HEPSİ AŞAĞIDAKİ TEK SABİTTEN OKUNUR — E2 `pencere` damgası da
# (`pencere_rejimi`) aynı kaynaktan türetilir; ikiz-değer üretmek EQUIVALENT_TRUTHS sınıfı
# tuzağıdır ve kartın hakemini (EDG-042 alt-bant kıyası) sessizce köreltirdi.
# NOT (DST beyanı): sabit ET-dakikadır; "13:45 UTC" karar metni EDT içindir (kışın 14:45 UTC'ye
# denk gelir — açılışa göre +15 dk ilişkisi korunur, karar da "açılış-sonrası 15 dk" kararıdır).
ENTRY_WINDOW_ET_MIN = 9 * 60 + 45     # EXE-2026-009 + K2: tetik 9:45 ET (EDT'de 13:45 UTC)
# Rejim adları KARTTA DONUK ("1330"/"1345") — sabitin bilinen iki değeri dışında ad UYDURULMAZ:
# bilinmeyen değerde KeyError yükselir (sessizce yanlış damga basmaktan iyidir; UYDURMA YASAĞI).
_PENCERE_REJIMLERI = {9 * 60 + 30: "1330", 9 * 60 + 45: "1345"}


def pencere_rejimi() -> str:
    """E2 `pencere` damgasının YÜRÜRLÜK rejimi — tetik sabitiyle AYNI kaynaktan (EXE-009 kill#3:
    damga rejimi ikinci bir değerden okunursa tetik geri alındığında damga yalan söylerdi)."""
    return _PENCERE_REJIMLERI[ENTRY_WINDOW_ET_MIN]


def is_entry_window(at: dt.datetime | None = None) -> bool:
    """Sabah tetik penceresi açık mı? (hafta içi, ET dakika ∈ [ENTRY_WINDOW_ET_MIN, 16:00)).

    `is_market_open`ın ALT kümesidir ve onun yerine GEÇMEZ: seans yasası (RTH 9:30-16:00) veri/
    gözlem katmanlarının kapısıdır ve değişmedi; bu pencere yalnız TARAMA/EMİR tetiğinin yasasıdır.
    Tatil sınırı da aynıdır (bilmez — kolaylık kapısı; bkz. is_market_open docstring'i)."""
    a = at or now()
    if a.tzinfo is None:
        a = a.replace(tzinfo=UTC)
    ny = a.astimezone(NY)
    if ny.weekday() >= 5:            # Cmt/Paz
        return False
    minutes = ny.hour * 60 + ny.minute
    return ENTRY_WINDOW_ET_MIN <= minutes < 16 * 60


def session_date(at: dt.datetime | None = None) -> str:
    """İçinde bulunulan ET seans tarihi (YYYY-MM-DD) — intraday kayıtları günle etiketlemek için."""
    a = at or now()
    if a.tzinfo is None:
        a = a.replace(tzinfo=UTC)
    return a.astimezone(NY).date().isoformat()

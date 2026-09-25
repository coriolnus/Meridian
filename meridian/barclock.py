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
girmemeli), seans_araligi (O GÜNÜN gerçek XNYS seans aralığı — TEK takvim yolu), is_market_open /
is_entry_window / session_date (NY seansı; tatil + erken kapanış XNYS takviminden, DST zoneinfo'dan),
set_clock / reset_clock (YALNIZ test: saat enjeksiyonu), BAR_SECONDS=60.

DEĞİŞMEZLER: FAIL-CLOSED — damgasız/biçimsiz bar admissible DEĞİLDİR (bilinmeyen tazelik = kabul
etme); takvim okunamazsa seans kapısı KAPALI döner (bilinmeyen seans = açık sayma). Bayatlık
karşılaştırması da burada yaşar, tüketicilere saçılmaz ("tek saat, tek yer"). Seans kapısı çıkış
(TSK-205) ve giriş penceresi (EXE-009+K2) yasalarının kapısıdır; look-ahead güvenliği ise yine
is_admissible'a dayanır.

OKUR/YAZAR: kurulu `pandas_market_calendars` paketinin XNYS takvimini okur (paket-içi kural
tablosu; ağ YOK) ve başarılı günleri süreç-içi `_SEANS_CACHE`te tutar. Redis'e ve diske dokunmaz;
tek yazımı takvim arızasında süreç başına BİR `obs.warn` olayıdır (bkz. is_market_open).
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


# ---------------- NY SEANS (XNYS takvimi; DST-farkında) ----------------
# SEANS GERÇEĞİNİN TEK KAYNAĞI XNYS TAKVİMİDİR (TSK-223, Rol-1 kararı 2026-09-25). Depo seans
# gerçeğini zaten bu takvimden okuyor (`adapters.data.CALENDAR`, `scheduler._last_closed_session`,
# `scheduler._leg_ready`); Alpaca `/v2/clock` gibi ağdan ikinci bir saat kaynağı "aynı zaman iki
# kaynak" sınıfı olurdu. Emsal: `gap_scan` yarım gün sahte alarmı (WP-D, 2026-08-02) tam olarak
# yaklaşık kapı yerine XNYS `schedule()` kullanılarak kapatılmıştı — o yol artık BURADA yaşar ve
# barsarchive onu kullanır (`barsarchive._seans_araligi` ince sarmalayıcıdır). Bilinen bedel: öngörülmemiş
# olağanüstü kapanış (ör. ulusal yas günü) takvim paketi güncellenene dek bilinmez → o gün kapı
# eski (tatil-kör) davranışa düşer, daha kötüsüne değil.
SEANS_TAKVIMI = "XNYS"      # data.CALENDAR / scheduler._leg_ready ile AYNI ad
SEANS_CACHE_MAX = 40        # gün başına bir kayıt; uzun ömürlü worker'da sözlük sınırsız büyümesin
_SEANS_CACHE: dict = {}     # {gün: (durum, açılış, kapanış, hata)} — YALNIZ başarılı okumalar
# İKİ İŞ PARÇACIĞI PAYLAŞIR (TSK-223 ile YENİ): barfeed tüketicisi (`is_market_open`) ve zamanlayıcı
# (`barsarchive.gap_scan`). Kilit yok, bilerek: tahliye `sorted()` ile ÖNCE listeye döker (yineleme
# sırasında boyut değişimi hatası doğmaz); en kötü sonuç tavanın geçici aşılması ya da aynı günün iki
# kez sorgulanmasıdır — ikisi de bir sonraki çağrıda kendiliğinden düzelir (inceleme KÜÇÜK-1, 2026-09-25).
# Takvim arızası uyarısı SÜREÇ BAŞINA BİR KEZ: kapı her barfeed olayında ve her poll'de (300 sn)
# sorulur; koşulsuz uyarı olay defterini — pano olay akışının ve alarm bütçesinin okuduğu kaynağı —
# boğardı. `scheduler._CALENDAR_WARNED` ile AYNI desen: GERİ SIFIRLANMAZ (takvim gidip geldikçe
# bastırılan sel geri açılmasın). Arızanın KENDİSİ ise önbelleğe alınmaz — takvim dönünce kapı düzelir.
_SEANS_TAKVIMI_UYARILDI = False
EV_SEANS_TAKVIMI_YOK = "session_gate_calendar_unavailable"


def seans_araligi(gun) -> tuple:
    """O GÜNÜN GERÇEK seans aralığı — XNYS `schedule()`ten, UTC. `(durum, açılış, kapanış, hata)`.

    durum: `"ok"` (seans günü; açılış/kapanış dolu — erken kapanışta kapanış 13:00 ET'dir) ·
    `"seans_disi"` (takvim OKUNDU ve o gün seans değil: hafta sonu/tam tatil) · `"takvim_yok"`
    (takvim okunamadı → HÜKÜM YOK; `hata` nedeni taşır).

    TEK TAKVİM YOLU: `is_market_open`/`is_entry_window` ve `barsarchive.gap_scan` (onun
    `_seans_araligi` sarmalayıcısı üzerinden) seans sınırını BURADAN okur; ikinci bir `schedule()`
    yolu açmak aynı gerçeğin iki kopyasıdır (tek-kaynak yasası; v548 K2 çivisi).

    SAF: olay BASMAZ — kaydı çağıran yapar (`is_market_open` süreç başına bir uyarı, `gap_scan`
    raporun `seans.hata` alanı). ÖNBELLEK YALNIZ BAŞARIYA: aynı gün her poll'de/olayda sorulur, takvim
    sorgusu boşuna tekrarlanmasın; ama bir ARIZAYI önbelleğe almak takvim geri geldikten sonra bile o
    günü sonsuza dek "takvim_yok" bırakırdı — arıza her çağrıda yeniden denenir. Önbellek
    `SEANS_CACHE_MAX` ile tavanlıdır (en eski günler düşer)."""
    key = str(gun)[:10]
    hit = _SEANS_CACHE.get(key)
    if hit is not None:
        return hit
    try:
        import pandas_market_calendars as mcal
        sched = mcal.get_calendar(SEANS_TAKVIMI).schedule(start_date=key, end_date=key)
    except Exception as e:  # sessiz-yutma DEĞİL: neden `hata` ile çağırana ÇIKAR — is_market_open süreç başına uyarır, gap_scan raporda taşır (olay basmak SAF yardımcının sözleşmesini kırardı)
        return ("takvim_yok", None, None, f"{type(e).__name__}: {e}")
    if not len(sched):
        out = ("seans_disi", None, None, None)
    else:
        satir = sched.iloc[0]
        out = ("ok", satir["market_open"].to_pydatetime(),
               satir["market_close"].to_pydatetime(), None)
    if len(_SEANS_CACHE) >= SEANS_CACHE_MAX:
        for k in sorted(_SEANS_CACHE)[:len(_SEANS_CACHE) - SEANS_CACHE_MAX + 1]:
            _SEANS_CACHE.pop(k, None)
    _SEANS_CACHE[key] = out
    return out


def _takvim_yok_uyar(gun: str, hata) -> None:
    """Takvim arızasını SÜREÇ BAŞINA BİR KEZ olay defterine yazar (okuyucular: pano olay akışı ve
    `watchdog.alarm_budget` warn=low sayımı). `obs` tembel içe aktarılır: barclock en alt katmandır."""
    global _SEANS_TAKVIMI_UYARILDI
    if _SEANS_TAKVIMI_UYARILDI:
        return
    _SEANS_TAKVIMI_UYARILDI = True
    from . import obs
    obs.warn(EV_SEANS_TAKVIMI_YOK, gun=gun, takvim=SEANS_TAKVIMI, error=hata,
             detail="XNYS takvimi okunamadı — seans kapısı KAPALI döner (fail-closed): ayna çıkışı "
                    "açılışa ertelenir (koruma bacakları yerinde), giriş gönderimi ve intraday "
                    "tarama durur; takvim dönünce kapı kendiliğinden düzelir (arıza önbelleğe "
                    "alınmaz). Süreç başına bir kez kaydedilir")


def is_market_open(at: dt.datetime | None = None) -> bool:
    """ABD hisse REGULAR seansı açık mı? Açık ⇔ `at`'in NY tarihinde XNYS seansı VAR ve
    `market_open ≤ at < market_close` (`seans_araligi`). Resmî TATİLİ ve ERKEN KAPANIŞI (13:00 ET)
    takvimden bilir; DST'yi takvimin UTC damgaları ve zoneinfo halleder. `at` tz'siz gelirse UTC sayılır.

    KAPI OLARAK OKUNUR, kolaylık değil: ayna çıkışı (`loop._mirror_exit_sync`,
    `loop.mirror_exit_acilis_turu` — TSK-205) ve giriş penceresi (`is_entry_window` → pencere yasası)
    bu cevaba dayanır; erken kapanış akşamı "açık" demek kapatmayı seans dışında kuyruklatır.

    FAIL-CLOSED: takvim okunamazsa False (çıkışta koruma yerinde kalır, çıplak pencere açılmaz; kardeş
    `scheduler._leg_ready` de "kapalı taraf güvenli taraftır" der) ve süreç başına BİR uyarı basılır.
    Hafta sonu takvim sorulmadan kapalıdır."""
    a = at or now()
    if a.tzinfo is None:
        a = a.replace(tzinfo=UTC)
    ny = a.astimezone(NY)
    if ny.weekday() >= 5:            # Cmt/Paz — takvim sorgusu gereksiz
        return False
    gun = ny.date().isoformat()
    durum, acilis, kapanis, hata = seans_araligi(gun)
    if durum == "takvim_yok":
        _takvim_yok_uyar(gun, hata)
        return False
    if durum != "ok":                # takvim okundu, o gün seans yok (tam tatil)
        return False
    return acilis <= a < kapanis


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
    """Sabah tetik penceresi açık mı? ⇔ `is_market_open(at)` VE ET dakika ≥ ENTRY_WINDOW_ET_MIN.

    `is_market_open`ın ALT kümesidir — YAPISAL olarak (onu çağırır) — ve onun yerine GEÇMEZ: seans
    yasası veri/gözlem katmanlarının kapısıdır; bu pencere yalnız TARAMA/EMİR tetiğinin yasasıdır.
    Tatil, erken kapanış (13:00 ET) ve takvim-yok fail-closed davranışı seans kapısından MİRAS alınır:
    erken kapanış akşamı (13:16 ET döngüsü) pencere KAPALIDIR, giriş emri kapanıştan sonra gidip gece
    dinlenmez (TSK-223)."""
    a = at or now()
    if a.tzinfo is None:
        a = a.replace(tzinfo=UTC)
    if not is_market_open(a):
        return False
    ny = a.astimezone(NY)
    return ny.hour * 60 + ny.minute >= ENTRY_WINDOW_ET_MIN


def session_date(at: dt.datetime | None = None) -> str:
    """İçinde bulunulan ET seans tarihi (YYYY-MM-DD) — intraday kayıtları günle etiketlemek için."""
    a = at or now()
    if a.tzinfo is None:
        a = a.replace(tzinfo=UTC)
    return a.astimezone(NY).date().isoformat()

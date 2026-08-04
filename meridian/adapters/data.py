"""adapters/data.py — real daily OHLCV, no API key. Primary: Cboe delayed_quotes historical
(clean full-history JSON, split-adjusted). Fallback: Nasdaq historical API. Cached to state/bars/.

Adds: validate_bars() — an integrity gate so a single unadjusted split can't inject fake gaps that
poison the backtest (Hard Rule 7); incremental cache (fetch only when the cache is stale, then merge);
and exponential backoff on transient fetch errors."""
from __future__ import annotations
import time
from pathlib import Path
import httpx
import pandas as pd

from .. import config as _config

_UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
       "Accept": "application/json"}
CBOE = "https://cdn.cboe.com/api/global/delayed_quotes/charts/historical/{sym}.json"
NASDAQ = ("https://api.nasdaq.com/api/quote/{sym}/historical"
          "?assetclass=stocks&fromdate={d1}&todate={d2}&limit=9999")
COLS = ["date", "open", "high", "low", "close", "volume"]
SPLIT_SUSPECT_RET = 0.35   # |day-over-day close move| above this is flagged (possible unadjusted split)
FRESH_DAYS = 3             # cache within this many days of `end` is considered fresh -> no refetch
CORP_ACTION_PCT = 0.25     # overlapping-date adjusted-close divergence beyond this ⇒ split/dividend re-adjustment
_WARMUP_WARNED: set = set()   # once-per-process telemetry for caches that can't reach FETCH_START (audit #44)
BAR_EPS = 1e-6                # relative close delta above this = the bar CHANGED (not float noise)
SOURCE_FILE = "bars_source.json"   # {ticker: {"source": ..., "at": ...}} — hangi kaynak yazdı (D1)
_LAST_SOURCE: dict[str, str] = {}  # fetch() bu turda hangi kaynağın verdiğini buraya yazar

# ---- MASSIVE ARTIMLI YOLU (2026-07-29) --------------------------------------------------------
# Massive'in grouped ucu TÜM ABD piyasasının o günkü EOD barlarını TEK çağrıda verir. Bugün 250
# sembollük bir tazeleme SEMBOL BAŞINA bir FMP isteği atıyor ve ücretsiz kotanın tamamını yakıyor
# (canlı kanıt: state/fmp_usage.json → 2026-07-27, `calls_today: 251`, "Limit Reach").
#
# İKİ MOD VAR ve hangisinde olduğumuza ÖLÇÜM karar verir (adapters/massive.write_enabled):
#   YAZIM (bugünkü hâl) → Massive zincirin İLK kolu; o sembol için FMP'ye HİÇ istek atılmaz.
#   YALNIZ-ALARM        → zincir DEĞİŞMEZ; Massive yalnız kıyaslanır ve uyuşmazlık kaydedilir.
# Kapıyı açan kanıt: Rol 1'in 2026-07-29 ölçümü (MCP kanalı, iki ayrı tarih, temettü ex-tarihi geçen
# isimler dahil, maksimum sapma %0.0000 → aynı bölünme-düzeltmeli ölçek). Yerel `--dogrula` bu tabanı
# EZER ve "uyumsuz" derse kapı kapanır. Ölçümsüz yazıma geçmek, iki farklı ayarlama ölçeğini
# birbirine ekleyip sahte bir gecelik uçurum imal etmek olurdu — bu depoda canlıda YAŞANMIŞ hata
# sınıfı (aşağıdaki D1 dikiş koruması).
#
# İKİ AYRI KOL, İKİ AYRI KAYNAK ADI (kasıtlı):
#   "massive"      → grouped daily; TEK çağrıda tüm piyasa, sembol başına TEK bar. Yalnız EKLER:
#                    geçmişi asla sahiplenmez, dikiş defterine yazılmaz (aşağıda gerekçesi).
#   "massive_hist" → custom-bars; tek sembolün ~2 yıllık PENCERESİ. Gerçek geçmiş taşır, bu yüzden
#                    NORMAL bir kaynak gibi davranır (sahiplenebilir, dikiş kuralına tabidir).
# Ayrım kasıtlı: iki mekanizmanın defterdeki izi farklı olmalı ki "bu barı hangi yol yazdı" sorusu
# tahminle değil kayıtla cevaplansın.
# ALARM EŞİĞİ ÖLÇÜLDÜ (2026-07-29, 251 sembol, canlı grouped vs diskteki önbellek): iyi huylu
# sapmaların TABANI ~%0.08 (en kötü hâl T: %0.081; hepsi dağınık, çarpımsal değil). İlk yazımda
# eşik %0.1 idi — yani gürültü tabanının hemen ÜSTÜNDE. Böyle bir eşik ilk oynak günde yanlış
# alarm üretir ve yanlış alarmlar gerçek alarmları okunmaz yapar (bu depoda dikiş uyarısının
# 250 satır/tur basıp sinyali gömmesi tam bu hataydı). Gerçek arıza sınıfı — yanlış ölçek, bayat
# bar, bozuk print — %1'in ÜSTÜNDEDİR. %0.5 ikisinin arasında güvenli bir yer: gürültünün ~6 katı,
# gerçek arızanın yarısı altı. Ölçek HÜKMÜ ayrı ve daha sıkı bir eşikle verilir (massive.VERIFY_TOL).
MASSIVE_TOL = 0.005            # %0.5 — aynı ticker+gün kapanış farkı bunun üstündeyse uyuşmazlık ALARMI
MIN_INCREMENTAL_BARS = 200     # bu kadar geçmişi olmayan sembolde artımlı kaynak KULLANILMAZ (tek bar
                               # bir geçmiş kuramaz; derin backfill FMP'nin işi)
CROSSCHECK_FILE = "massive_crosscheck.json"   # çapraz-kaynak ölçümünün BİRİKİMİ (yalnız alarm değil, sayı)
_XCHECK: dict = {}
_XCHECK_DIRTY = 0
_XCHECK_FLUSH_EVERY = 25       # 250'lik turda ~10 yazım (her sembolde bir değil)
_MASSIVE_MODE_LOGGED = False


def _nabiz(asama: str, i: int | None = None, n: int | None = None) -> None:
    """İLERLEME NABZI (v186, 2026-08-04) — asılı-tick bekçisine "bu süpürme İLERLİYOR" de.

    Gerekçenin tamamı `scheduler.py`nin İLERLEME NABZI bloğundadır (canlı vaka: 2026-08-03 akşamı
    bekçi meşru-uzun EOD döngüsünü üç kez öldürdü). Burada yalnız iki BİÇİM kararı yazılıdır:

    GEÇ İMPORT, MODÜL BAŞINDA DEĞİL: `adapters.data` katman olarak zamanlayıcının ALTINDADIR
    (zamanlayıcı bu modülü çağırır, tersi değil) ve modül başına `from .. import scheduler` yazmak
    o yönü tersine çevirirdi. Kısılan çağrının maliyeti bir `sys.modules` aramasıdır; bu modüldeki
    döngüler evren boyundadır (≤ birkaç yüz) ve her yinelemesinde ağ/disk işi yapar.

    HÜKÜM ZAMANLAYICIDA: burası "ilerledim" der, "damgayı tazele" DEMEZ. Yazıp yazmamaya
    `scheduler.nabiz` karar verir (30 sn kısma + iş parçacığı sahipliği) — yani replay tohumu,
    sprint alt süreçleri ve havuz işçileri bu satırdan geçse bile canlı damgaya DOKUNAMAZ."""
    try:
        from .. import scheduler
        scheduler.nabiz(asama, i, n)
    except Exception:  # sessiz-yutma: nabız saf telemetridir — zamanlayıcı bu süreçte hiç yüklenmemiş olabilir (replay/sprint) ve bir damga denemesi veri hattını ASLA düşüremez
        pass


def _cache_path(ticker: str) -> Path:
    return _config.BARS / f"{ticker.lower().replace('.', '-')}.csv"


_BAR_WARNED: set = set()   # olay türü başına bir kez — bu yollar ticker döngüsünde çağrılır


def _bar_warn(event: str, exc: BaseException, **extra) -> None:
    """Bar defteri yardımcılarının sessizce düşmesini görünür kılar (yasa 4). Olay başına BİR kez:
    500 ticker'lık bir turda aynı disk hatasını 500 kez basmak sinyali gürültüye çevirirdi."""
    if event in _BAR_WARNED:
        return
    _BAR_WARNED.add(event)
    try:
        from .. import obs
        obs.warn(event, error=f"{type(exc).__name__}: {exc}", **extra)
    except Exception:
        # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci kanal yok; telemetri denemesi
        # bar çekimini ASLA düşüremez.
        pass


# ---------------- yazma disiplini (denetim turu 2, 2026-07-21) ----------------
def _bump_wf_rev() -> None:
    """Bar geçmişi DEĞİŞTİ → önbelleklenmiş walk-forward'lar artık var olmayan barlara ait. Revizyon
    MONOTON artar (zaman damgası); sıfırlanamaz, yarışta kayıp-güncelleme olmaz."""
    try:
        from .. import store as _st
        import time as _t
        _prev = int(_st.read_json("wf_cache_rev.json", {}).get("rev", 0))
        _st.write_json("wf_cache_rev.json", {"rev": max(int(_t.time()), _prev + 1)})
    except Exception as e:
        # YASA 4 (2026-07-21): revizyon artmazsa ARTIK VAR OLMAYAN barlara ait walk-forward'lar
        # geçerli sayılır — bölünme/temettü yeniden düzeltmesinden sonra motor ESKİ sonuçla karar
        # verir. Sessizce başarısız olması, en tehlikeli sınıf: yanlış ama tutarlı görünen sonuç.
        _bar_warn("wf_rev_bump_failed", e)


def _write_bars(df: pd.DataFrame, cp: Path) -> None:
    """ATOMİK yazım. Eskiden düz `to_csv` idi: süreç havuzundaki işçiler (dataset.load_cached) aynı
    dosyayı EŞ ZAMANLI okuyor — yarım yazılmış bir CSV okunduğunda ticker sessizce kırpılmış barlarla
    değerlendirilir ve bu 'küçülmüş dosya' olarak bütünlük dedektörüne düşer. mkstemp+os.replace ile
    okuyucu ya eski ya yeni dosyayı görür, asla yarısını (store.write_json ile aynı disiplin)."""
    import os
    import tempfile
    cp.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(cp.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="") as fh:
            df.to_csv(fh, index=False)
        os.replace(tmp, cp)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:  # sessiz-yutma: en iyi çaba temizlik/kilit bırakma; hedef zaten yoksa yapacak bir şey yok ve asıl iş yolu bundan ötürü durduramaz
            pass
        raise


def _bar_source(ticker: str) -> str | None:
    try:
        from .. import store as _st
        return (_st.read_json(SOURCE_FILE, {}) or {}).get(ticker.upper(), {}).get("source")
    except Exception as e:
        # YASA 4: kaynak sabitleme defteri okunamazsa "kaynak bilinmiyor" ile devam edilir — yani
        # bir ticker'ın barları sessizce KAYNAK DEĞİŞTİREBİLİR (FMP↔Alpaca), ki bu tam olarak
        # 2026-07-21'deki "aynı sembol, iki farklı fiyat serisi" sınıfı. Davranış aynı, iz var.
        _bar_warn("bar_source_unreadable", e, file=SOURCE_FILE)
        return None


def _pin_source(ticker: str, source: str) -> None:
    try:
        from .. import store as _st
        import datetime as _dt
        m = _st.read_json(SOURCE_FILE, {}) or {}
        m[ticker.upper()] = {"source": source,
                             "at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")}
        _st.write_json(SOURCE_FILE, m)
    except Exception as e:
        _bar_warn("bar_source_pin_failed", e, file=SOURCE_FILE)


def _changed_rows(cached: pd.DataFrame, merged: pd.DataFrame) -> tuple[int, float]:
    """Kaç ÖNCEDEN VAR OLAN bar değişti ve en büyük göreli sapma ne? (salt ekleme → (0, 0.0))"""
    try:
        m = cached[["date", "close"]].merge(merged[["date", "close"]], on="date", suffixes=("_c", "_m"))
        if m.empty:
            return 0, 0.0
        c, n = m["close_c"].astype(float), m["close_m"].astype(float)
        rel = ((n - c).abs() / c.where(c > 0)).dropna()
        changed = rel[rel > BAR_EPS]
        return int(len(changed)), float(changed.max()) if len(changed) else 0.0
    except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
        return 0, 0.0


# ==================================================================================================
# HAYALET SEANS KAPISI + DÜZELTİLMEMİŞ SATIR KARANTİNASI  (2026-07-30)
# ==================================================================================================
# ÖLÇÜLMÜŞ KÖK NEDEN (yerel state/bars taraması, 259 dosya / 1.344.334 satır — uydurma değil, sayım):
# takvimde SEANS OLMAYAN iki tarih, bar defterlerinde gerçek bir seans satırı gibi duruyor.
#   2025-05-26 (Memorial Day, piyasa KAPALI) → 258/259 dosyada. 199'u 05-23'ün BİREBİR kopyası,
#       52'si yuvarlama farklı yakın kopyası, 7'si BÖLÜNME-DÜZELTİLMEMİŞ ham fiyat
#       (BKNG ×25, ORLY ×15, KLAC ×10, NFLX ×10, NOW ×5, HON ×0,5, DD ×0,333 — hacim TERS oranlı).
#   2018-11-22 (Thanksgiving, piyasa KAPALI) → 184/259 dosyada. 169'u önceki kapanışta donmuş
#       düz bar (OHLC eşit, hacim 0), 15'i ham fiyat (ORLY ×15, WMT ×3, GE ×0,125 …), hacim 0.
# ZARARI SOMUT: BKNG'nin 2025-05-26 satırı 213,31 → 5332,80 → 214,28 gidiş-gelişi üretir; bu satırdan
# geçen her 20 günlük "getiri" +%2500 mertebesinde bir HAYAL olur ve o hayal component_ic/cf defteri/
# eşik eğrileri gibi R-tabanlı her artefakta akar.
#
# ÜÇ SAVUNMA DA NEDEN GEÇİRDİ (her biri kendi işini doğru yapıyordu — kimse bu soruyu sormuyordu):
#   sanitize_bars      → yalnız AYNI tarihin tekrarını tekilleştirir; "bu tarih seans mı" diye sormaz.
#   validate_bars      → split_suspect'i SOFT sayar (ok=True döner) — hüküm vermeyen bir dedektör.
#   bar_source_seams   → kaynak ÖLÇEĞİ dikişini sayar; tek satırlık hayaleti tanımaz.
#
# KAPI NEREYE KONDU VE NEDEN: `sanitize_bars` zincirin TEK ortak boğazıdır — her kaynak bacağı
# (massive/massive_hist/fmp/cboe/nasdaq/alpaca_sip/alpaca_iex) `fetch` içinde buradan geçer,
# onarım geçidi (`_merge_repair_bar`) buradan geçer, disk önbelleğinin OKUMA yolu (`load_bars`,
# `dataset.load_cached`) da buradan geçer. Kapıyı `_write_bars`a koymak yalnız DİSKİ temizlerdi:
# bellekteki seri kirli kalır, karar kirli barla verilir ve disk ile bellek AYRIŞIRDI.
#
# FAIL-OPEN, BİLEREK: takvim modülü yoksa/patlarsa satır DÜŞÜRÜLMEZ (yalnız bir kez uyarılır).
# Bir bütünlük kapısının fail-closed olması genelde doğrudur; burada değil — "takvimi okuyamadım"
# hâlinde fail-closed davranmak, 1,3 milyon satırlık geçmişi silmek demektir. Kapının yokluğu bizi
# BUGÜNKÜ davranışa döndürür (bilinen, ölçülmüş, kötü ama sınırlı); yanlış tarafa kapanması geri
# alınamaz veri kaybıdır.
CALENDAR = "XNYS"                    # NYSE/NASDAQ ortak seans takvimi (scheduler/run.py ile AYNI ad)
CAL_START = "1990-01-01"             # en eski yerel bar 2004-01-02; taban bilerek daha geride
CAL_FORWARD_DAYS = 730               # ileri pencere: uzun ömürlü süreçte takvim yeniden üretilmesin
UNADJ_REVERT_TOL = 0.10              # sıçrama ERTESİ BAR geri dönüyorsa izole hayalet; dönmüyorsa DİKİŞ
UNADJ_STRICT_REVERT_TOL = 0.05       # …bu kadar TAM geri dönüyorsa fiyat kanıtı TEK BAŞINA yeter
UNADJ_VOLUME_TOL = 0.10              # ham/düzeltilmiş satırın imzası: fiyat ×N iken hacim ×1/N
UNADJ_VOL_SURGE_MIN = 1.5            # gerçek %35+ hareket hacmi PATLATIR; patlamadıysa hacim onaylamadı
UNADJ_VOL_WINDOW = 63                # …"normal hacim" = geriye bakan 63 seansın medyanı
UNADJ_DOLLAR_VOL_FLOOR = 5e6         # bu dolar hacmin altındaki bar, evrenin hiçbir gerçek seansı değil
CAL_MISMATCH_SHARE = 0.01            # bu orandan fazlası takvim-dışıysa kapı REDDEDER (bkz. _calendar_scan)
CAL_MISMATCH_MIN_ROWS = 2            # …ve en az bu kadar satır olmalı (TEK satır her zaman adjudike edilir)
_SESSIONS: frozenset = frozenset()   # süreç-içi takvim önbelleği (her satır için API'ye gidilmez)
_SESSION_SPAN: tuple = ()            # takvimin KAPSADIĞI aralık — dışındaki tarih hakkında hüküm YOK
_CAL_FAILED = False
_GHOST: dict = {}                    # {tarih: {"rows": n, "tickers": [...], "classes": {...}}}
_GHOST_EVENTED: set = set()          # tarih başına BİR olay (259 sembolde 259 satır sinyali gömerdi)
_QUAR_EVENTED: set = set()
_CAL_MISMATCH: dict = {}             # {TICKER: {...}} — kapının REDDETTİĞİ seriler (sessiz kalmasın)
_CAL_MISMATCH_WARNED: set = set()
_GHOST_EMITTED = 0                   # tur-sonu özetinde en son duyurulan toplam (yalnız artışta bas)


def _sessions() -> frozenset:
    """Geçerli XNYS seans tarihleri (YYYY-MM-DD) — SÜREÇ BAŞINA BİR KEZ üretilir, sonra küme araması.
    Ölçüldü: `valid_days(1990→+2y)` 0,11 sn ve 9.820 tarih; satır başına takvim sorgusu yapmak
    (259 sembol × ~5.400 bar) bunun on binlerce katı olurdu."""
    global _SESSIONS, _SESSION_SPAN, _CAL_FAILED
    if _SESSIONS or _CAL_FAILED:
        return _SESSIONS
    try:
        import datetime as _dt
        import pandas_market_calendars as mcal
        end = (_dt.date.today() + _dt.timedelta(days=CAL_FORWARD_DAYS)).isoformat()
        days = mcal.get_calendar(CALENDAR).valid_days(CAL_START, end)
        _SESSIONS = frozenset(str(d.date()) for d in days)
        _SESSION_SPAN = (CAL_START, end)
    except Exception as e:
        _CAL_FAILED = True
        _SESSIONS, _SESSION_SPAN = frozenset(), ()
        # FAIL-OPEN'IN SESİ: kapı kapanmadıysa bunu SÖYLEMEK zorundayız — sessizce açık kalan bir
        # bütünlük kapısı, var olduğu sanılan ama olmayan bir savunmadır (bu deponun baskın kusuru).
        _bar_warn("bar_calendar_unavailable", e, calendar=CALENDAR)
    return _SESSIONS


def _calendar_scan(df: pd.DataFrame) -> tuple:
    """(hayalet_maskesi, red_ölçümü|None) — TEK geçiş, SAF (hiçbir yan etkisi yok).

    KİTLESEL UYUŞMAZLIK REDDEDİLİR, SESSİZCE UYGULANMAZ (2026-07-30 — `bar_row_loss_refused` ile
    AYNI yasa, yeni yüzey): kapı bir serinin KÜÇÜK bir kısmını düşürüyorsa bu bir arıza onarımıdır;
    BÜYÜK bir kısmını düşürüyorsa artık onarım değil, serinin TAKVİMİNİ reddetmektir — seri başka
    bir borsanın/venue'nün olabilir, sentetik olabilir, ya da takvimin kendisi yanlış olabilir.
    Böyle bir seriden %4 satır silmek, hayalet barların verdiği zarardan çok daha büyük ve GERİ
    ALINAMAZ bir zarardır (gösterge sürekliliği ve pencere uzunlukları çöker). Doğru davranış:
    DOKUNMA, SÖYLE — hükmü operatör verir.

    EŞİK ÖLÇÜLDÜ, SEÇİLMEDİ. Yerel 259 defterin HİÇBİRİNDE 2'den fazla hayalet satır yok, en yüksek
    pay %0,1233 ve en KISA defter bile 811 bar (KVUE) — yani gerçek arızanın payı her zaman %1'in
    çok altında. Buna karşılık iş-günü takvimiyle üretilmiş (`bdate_range`) bir seride yılda ~9-10
    borsa tatili satır olarak durur; ölçülen paylar %3,3-5. Çizgi ikisinin ARASINA konur:
    pay > %1 VE en az 2 satır.
    HANGİSİ TAŞIYICI, AÇIKÇA: PAY testi taşıyıcıdır. Satır tabanı yalnız şunu söyler — TEK BAŞINA
    duran bir hayalet satır HER ZAMAN adjudike edilir (kısa bir çerçevede tek satır payı yanıltıcı
    biçimde büyütür ve o satırı 'takvim uyuşmazlığı' saymak, gerçek arızayı kaçırmak olurdu)."""
    ses = _sessions()
    empty = pd.Series(False, index=df.index)
    if df is None or df.empty or not ses or not _SESSION_SPAN:
        return empty, None
    d = df["date"].astype(str).str.slice(0, 10)
    lo, hi = _SESSION_SPAN
    mask = (~d.isin(ses)) & (d >= lo) & (d <= hi)
    n = int(mask.sum())
    if n >= CAL_MISMATCH_MIN_ROWS and n > CAL_MISMATCH_SHARE * max(len(df), 1):
        return empty, {"non_session_rows": n, "rows": int(len(df)),
                       "share_pct": round(100.0 * n / max(len(df), 1), 3)}
    return mask, None


def _ghost_mask(df: pd.DataFrame) -> pd.Series:
    """Takvim-dışı satırlar (True = hayalet). Kapsam dışı/okunamayan tarihler ve REDDEDİLEN seriler
    False (hüküm yok)."""
    return _calendar_scan(df)[0]


def calendar_mismatch(df: pd.DataFrame) -> dict | None:
    """Kapı bu seriyi adjudike etmeyi REDDEDER mi? (saf). `barrepair` kuru koşusunun "hiçbir bayt
    yazılmadı" vaadi, bu ölçümün olay YAZMAMASINA bağlıdır."""
    return _calendar_scan(df)[1]


def _note_cal_mismatch(ticker: str, red: dict) -> None:
    """Kitlesel takvim uyuşmazlığını DUYUR — sembol başına bir kez.

    NEREDEN ÇAĞRILIR VE NEDEN ORADAN: yalnız DİSK yolundan (`load_bars`). `sanitize_bars` bu olayı
    kendi atamaz, çünkü o fonksiyon her doğrulama/dönüşüm çağrısında koşar ve olay yazan bir
    dönüştürücü, ölçtüğü defteri kirletir (kum-havuzsuz her çağrı CANLI `events.jsonl`e düşerdi).
    Diskteki bir defter için red DURUM'dur ve orada duyurulur; ara çerçeveler için ölçüm süreç-içi
    defterde (`ghost_report()['refused']`) birikir ve `barrepair` raporunda okunur."""
    _CAL_MISMATCH[ticker] = dict(red)
    if ticker in _CAL_MISMATCH_WARNED:
        return
    _CAL_MISMATCH_WARNED.add(ticker)
    try:
        from .. import obs
        obs.warn("bar_calendar_mismatch", ticker=ticker, calendar=CALENDAR,
                 threshold_pct=round(CAL_MISMATCH_SHARE * 100, 2), **red,
                 detail="serinin büyük bir kısmı bu takvimde seans DEĞİL — kapı hiçbir satırı "
                        "DÜŞÜRMEDİ (kitlesel silme onarım değil, geri alınamaz kayıp olurdu). "
                        "Seri başka bir takvime ait olabilir; hüküm operatörün")
    except Exception:  # sessiz-yutma: kayıt kanalı düştü — ikinci kanal yok; sayaç yine tutuldu
        pass


def _unadjusted_mask(df: pd.DataFrame) -> pd.Series:
    """GEÇERLİ bir seansta duran BÖLÜNME-DÜZELTİLMEMİŞ tek satırın imzası (True = karantina).

    2026-07-31 YENİDEN TASARIM — HACİM ŞARTI ARTIK VETO DEĞİL, ZAYIFLATICI.
    Ölçüldü (aynı 259 defter / 1.343.892 geçerli-seans satırı, hayalet-round-2):
      (a) |hareket| > %35                                     → 216 satır
      (a&b) sıçra-VE-GERİ-DÖN = gerçek tek-satır hayalet sınıfı →  13 satır
      (a&b&c) ESKİ kuralın karantinaya aldığı                  →   3 satır
      → ESKİ (c) şartı sınıfın %77'sini (13'ün 10'unu) VETO EDİYORDU. Kaçanlar arasında
        GILD/CMCSA 2013-12-18 (+%110 / +%105, ertesi gün yarıya), DLTR 2012-06-26, UNP 2014-06-06 —
        hepsi apaçık ×2 ölçek satırı; hacimleri "tutarlı" göründüğü için geçiyorlardı.

    HANGİ ŞART NEYİ TAŞIYOR (ölçülmüş, seçilmemiş):
      (a) |r−1| > SPLIT_SUSPECT_RET — aday havuzu.
      (b) GERİ-DÖNÜŞ, r·back ≈ 1 — yanlış-pozitifi kesen ASIL şart. Ölçüm: geri-DÖNMEYEN 203 satırın
          |r·back−1| değeri EN AZ 0,1250; geri-dönen 13 satırın EN ÇOK 0,0854. İki sınıf arasında
          fiilî bir boşluk var ve eşik (%10) tam ortasına düşüyor.
      (c) HACİM — artık iki kademeli:
          KADEME 1 (|r·back−1| < UNADJ_STRICT_REVERT_TOL, %5): fiyat kanıtı TEK BAŞINA hükümdür.
              Ölçüm: 13 kusurun 11'i burada; en yakın masum satır 0,1250 (2,6× pay).
          KADEME 2 (%5 ≤ |r·back−1| < %10): geri dönüş TAM değil → hacim TARAFINDAN DESTEK istenir.
              Destek şartı ESKİSİNDEN ZAYIF: hacim 0 · hacim TERS oranlı · hacim PATLAMADI
              (v < UNADJ_VOL_SURGE_MIN × son 63 seansın medyanı) · ya da dolar hacmi
              UNADJ_DOLLAR_VOL_FLOOR altında (AVGO 2008-06-12 $1.180, PINS 2013 $262 — bunlar bu
              evrende hiçbir gerçek seansın hacmi değildir).
      GEREKÇE: eski (c) "hacim TAM TERS oranlı olmalı" diyordu; sağlayıcı ham fiyatı düzeltilmiş
      hacimle eşleştirdiğinde (2013-12-18 kümesinin tamamı) bu imza YOK ve satır kaçıyordu. Yeni
      şart "hacim bu hareketi DOĞRULAMIYOR" diyor — kanıtın yokluğu da kanıttır, ama yalnız fiyat
      kanıtı zayıfken devreye girer.

    YANLIŞ-POZİTİF KORUMASI DEĞİŞMEDİ (round-1 dersi, kitlesel-red yasasının kardeşi): GERÇEK ölçek
    dikişi geri DÖNMEZ — yeni ölçek kalıcıdır (2006-01-03'te 43 sembol, 2006-10-24'te 11 sembol).
    O satırlar yeni ölçeğin İLK barıdır; silmek deliği kapatmaz, geçmişi DELİK yapar. Yeni kuralın
    ölçülen masum-vurması: 203 kalıcı-adım satırının 0'ı. Kalıcı dikişler SATIR OLARAK DEĞİL,
    `bars_integrity` defterinde DÖNEM olarak damgalanır (aşağıdaki blok).
    """
    n = len(df)
    if n < 3:
        return pd.Series(False, index=df.index)   # tek/iki barlık çerçevede komşu yok — hüküm YOK
    c = pd.to_numeric(df["close"], errors="coerce")
    v = pd.to_numeric(df["volume"], errors="coerce")
    prev_c, next_c, prev_v = c.shift(1), c.shift(-1), v.shift(1)
    r = (c / prev_c.where(prev_c > 0))
    back = (next_c / c.where(c > 0))
    spike = (r - 1.0).abs() > SPLIT_SUSPECT_RET
    drr = (r * back - 1.0).abs()
    revert = drr < UNADJ_REVERT_TOL
    strict = drr < UNADJ_STRICT_REVERT_TOL
    zero_vol = v.fillna(-1) == 0
    recip = ((r * (v / prev_v.where(prev_v > 0))) - 1.0).abs() < UNADJ_VOLUME_TOL
    # GERİYE BAKAN pencere: "normal hacim" ölçüsü sıçramanın KENDİSİNİ içermez (yoksa patlama kendi
    # eşiğini yükseltir ve kural kendi kanıtını yer). min_periods → kısa çerçevede NaN → koşul False.
    med_v = v.shift(1).rolling(UNADJ_VOL_WINDOW, min_periods=20).median()
    no_surge = (v / med_v.where(med_v > 0)) < UNADJ_VOL_SURGE_MIN
    thin = (c * v) < UNADJ_DOLLAR_VOL_FLOOR
    vol_weak = (zero_vol | recip | no_surge.fillna(False) | thin.fillna(False))
    return (spike & (strict | (revert & vol_weak))).fillna(False)


# ---------------- bars_integrity: ÇÖZÜLMEMİŞ ÖLÇEK/KİMLİK KIRILMALARI ----------------
# NEDEN AYRI BİR DEFTER VAR (ve neden satır SİLMİYORUZ):
# Karantina kuralı TEK SATIRLIK hayaleti çözer. Ölçülen ikinci sınıf ise tek satır değil: bir
# sembolün geçmişinin BÜTÜN BİR DÖNEMİ başka bir ölçekte/kimlikte duruyor (CHTR 2010-09-15'te ×1158
# — iflas öncesi hisse; AVGO 2009-08-06 ×162; PINS'in 2013-2018 "geçmişi" 200-5000 dolarlık kuruş
# barları, Pinterest 2019'da halka açıldı; GOOGL 2013-12-18 ×2,6 C-hissesi; RTX 2020-04-03 ×3,8
# UTX birleşmesi; ABT/DD/HON/EQT/WBD/HLT düzeltilmemiş spinoff adımları; TDG'nin 2011-11→2012-01
# kesiti tamamen bozuk). Bu satırları SİLMEK yanlış olurdu — onlar yeni ölçeğin İLK barıdır ve
# silmek geçmişi delik yapar (round-1'in kitlesel-red dersi). Doğru davranış: satırı YERİNDE BIRAK,
# kırılmadan ÖNCEKİ dönemi "ölçüm için güvensiz" diye DAMGALA ve damgayı bardan değil DEFTERDEN oku.
#
# SINIRI AÇIKÇA: bu defter ÖLÇÜM yollarının tüketicisidir (component_ic, cf_backfill, donmuş
# walk-forward yolu). CANLI karar yoluna (dataset.load/load_live) BİLEREK bağlanmadı: HON'un
# 2026-06-29 kırılması bugün 22 seans önce — canlı yolda uygulanırsa HON'un göstergeleri ısınma
# barı bulamaz ve sembol tarama evreninden SESSİZCE düşerdi. Geçmişi ölçen için doğru olan, bugünü
# tarayan için yıkıcıdır; bu yüzden kablo tek yönlüdür ve adı geçen yerlerde AÇIKÇA çağrılır.
INTEGRITY_FILE = "bars_integrity.json"
BREAK_UP, BREAK_DN = 1.90, 0.55      # kalıcı adım eşiği (×1,9 üstü / ×0,55 altı) — ölçüldü, bkz. barrepair
BREAK_OGAP_TOL = 0.10                # AÇILIŞ da aynı oranda kaydıysa BÜTÜN BAR yeniden ölçeklenmiştir
BREAK_HL_NORMAL = 1.30               # …ve o seansın kendi high/low aralığı NORMAL kalmıştır
CORRUPT_HL_MAX = 3.0                 # bir seansta %200 iç aralık: OHLC şüpheli
CORRUPT_RUN_MIN = 3                  # …ama ancak KÜMELENİRSE kesit bozuktur (tekil bar hüküm değil)
PHANTOM_DOLLAR_VOL = 1e5             # bu evrende bir sembolün 63-seans medyan dolar hacmi bunun
PHANTOM_WINDOW = 63                  # …altındaysa o dönem gerçek bir listelenme DEĞİLDİR


def _integrity_feats(df: pd.DataFrame) -> dict:
    c = pd.to_numeric(df["close"], errors="coerce")
    v = pd.to_numeric(df["volume"], errors="coerce")
    o = pd.to_numeric(df["open"], errors="coerce")
    h = pd.to_numeric(df["high"], errors="coerce")
    lo = pd.to_numeric(df["low"], errors="coerce")
    prev_c = c.shift(1)
    r = c / prev_c.where(prev_c > 0)
    back = c.shift(-1) / c.where(c > 0)
    return {"c": c, "v": v, "r": r, "drr": (r * back - 1.0).abs(),
            "hl": h / lo.where(lo > 0),
            "ogap": (o / prev_c.where(prev_c > 0)) / r.where(r > 0),
            "dvol": c * v}


def integrity_corrupt_bars(df: pd.DataFrame) -> list[str]:
    """SAF. high/low > CORRUPT_HL_MAX olan barların TARİHLERİ — hüküm YOK, yalnız olgu.

    Tekil bir bar hem gerçek kriz seansı hem tek-günlük bozuk print olabilir; ayrımı bu fonksiyon
    YAPMAZ (bkz. `integrity_breaks` K2). Ayrı durmasının sebebi: kümelenme hükmünü veren kural ile
    olguyu ölçen kural aynı yerde yaşarsa, ikisinden birini gevşetmek diğerini sessizce bozar."""
    if df is None or len(df) < 2 or "high" not in df:
        return []
    h = pd.to_numeric(df["high"], errors="coerce")
    lo = pd.to_numeric(df["low"], errors="coerce")
    bad = ((h / lo.where(lo > 0)) > CORRUPT_HL_MAX).fillna(False)
    return [str(x)[:10] for x in df.loc[bad.values, "date"].astype(str)]


def integrity_breaks(df: pd.DataFrame) -> list[dict]:
    """SAF. Bir defterdeki ÇÖZÜLMEMİŞ kırılmaları sınıflandırır (satır DÜŞÜRMEZ, olay YAZMAZ).

    ÜÇ KURAL, ÜÇÜ DE 259 defter üzerinde ÖLÇÜLEREK ayarlandı (yanlış-pozitif tablosu barrepair
    `--integrity-tara` raporunda; gerçek piyasa olayları DAMGALANMAZ):

    K1 ÖLÇEK DİKİŞİ — r ≥ BREAK_UP ya da r ≤ BREAK_DN, GERİ DÖNMÜYOR (karantina sınıfı değil), VE
       hareket bir SEANS hareketi değil bir YENİDEN ÖLÇEKLEMEdir: açılış da kapanışla aynı oranda
       kaymış (|ogap/r − 1| < BREAK_OGAP_TOL) ve seansın kendi high/low aralığı normal
       (hl < BREAK_HL_NORMAL). AYIRICI GÜCÜ ÖLÇÜLDÜ: damgalanan 94 kırılmanın |ogap/r−1| değeri en
       çok 0,091; damgalanmayan gerçek olayların (AIG 2008-09-15/17, OXY + TRGP 2020-03-09) en az
       0,117 — eşik tam aralarında. İkinci kilit hl: damgalananların en yükseği 1,15, gerçek
       olayların en düşüğü 1,19. Tek bir özelliğin kenarda kalması hükmü çeviremesin diye VE'lendi.
    K2 BOZUK KESİT — hl > CORRUPT_HL_MAX olan barların KÜMELENMESİ (PHANTOM_WINDOW seans içinde en az
       CORRUPT_RUN_MIN tane). TEKİL bar damgalanmaz ve bu ayrım ÖLÇÜLEREK kondu: yerel geçmişte
       hl>3 olan 15 bar var; 9'u TDG'nin 2011-11→2012-01 kesitinde (bozuk), kalan 6'sı TEK
       başına duruyor ve üçü GERÇEK kriz seansıdır (UAL 2008-09-08 sahte iflas haberi, AIG ve CEG
       2008-09-16 kurtarma günü), üçü tek-günlük bozuk print (MRK 2021-06-11, TMO 2015-07-22,
       VZ 2026-01-08). Tekil barı kümeden ayırt edemeyecek bir kural, 22 yıllık VZ geçmişini tek
       bir hatalı `low` alanı yüzünden çöpe atardı (ölçüldü: 5.540 bar). Tekiller `barrepair
       --integrity-tara` raporunda ELLE DENETİM listesine düşer — görünür, ama hüküm verilmez.
    K3 HAYALET GEÇMİŞ — 63-seans medyan dolar hacmi PHANTOM_DOLLAR_VOL altında kalan dönem. Ölçüldü
       (sembol başına EN DÜŞÜK medyan): hayalet dönemler 0$ (DD 2017-19 hacim alanı sıfır),
       609$ (PINS 2013-18), 1.860$ (APO), 1.900$ (AVGO), 58.000$ (RTX 2008) — sonra tabanda BÜYÜK
       bir sıçrama: 329.448$ (MPWR 2005), 382.076$ (ENPH 2013), 425.730$, 714.826$, 847.641$
       (LNG 2009 — GERÇEKTEN küçük ama GERÇEK). Eşik iki tabanın arasında ve iki yana ~3,3 kat pay
       bırakıyor. Bu kural oran-tabanlı kuralların GÖREMEDİĞİ şeyi görür: kırılma ANI değil,
       kırılmadan önceki DÖNEMİN kendisi uydurmadır.
    """
    out: list[dict] = []
    if df is None or len(df) < 5 or "close" not in df:
        return out
    d = df.reset_index(drop=True)
    f = _integrity_feats(d)
    dates = d["date"].astype(str).str.slice(0, 10)
    bozuk = integrity_corrupt_bars(d)
    if len(bozuk) >= CORRUPT_RUN_MIN:
        pos = {v: k for k, v in dates.items()}
        ix = sorted(pos[b] for b in bozuk if b in pos)
        kume = [i for i in ix if sum(1 for j in ix if i <= j < i + PHANTOM_WINDOW) >= CORRUPT_RUN_MIN]
        if kume:
            son = max(j for j in ix if j <= max(kume) + PHANTOM_WINDOW)
            out.append({"tarih": dates.iloc[son], "oran": None, "sinif": "bozuk_kesit", "kural": "K2",
                        "kanit": {"donem": [dates.iloc[min(kume)], dates.iloc[son]],
                                  "bozuk_bar": len(ix),
                                  "max_high_low": round(float(f["hl"].iloc[ix].max()), 2)}})
    for i in range(1, len(d)):
        r = f["r"].iloc[i]
        if not (r == r) or r <= 0:                    # NaN/geçersiz — hüküm YOK
            continue
        if not (r >= BREAK_UP or r <= BREAK_DN):
            continue
        drr = f["drr"].iloc[i]
        if drr == drr and drr < UNADJ_REVERT_TOL:     # geri dönüyor → karantinanın işi, dikiş değil
            continue
        og, hl = f["ogap"].iloc[i], f["hl"].iloc[i]
        if not (og == og) or abs(float(og) - 1.0) >= BREAK_OGAP_TOL:
            continue                                  # açılış AYRI hareket etmiş → gerçek seans
        if hl == hl and hl >= BREAK_HL_NORMAL:
            continue                                  # gün-içi aralık geniş → gerçek seans
        out.append({"tarih": dates.iloc[i], "oran": round(float(r), 4), "sinif": "olcek_dikisi",
                    "kural": "K1", "kanit": {"acilis_orani": round(float(og), 3),
                                             "high_low": round(float(hl), 3) if hl == hl else None}})
    # K3: dönemsel — kırılma ANI yok, dönemin SONU var
    dv = f["dvol"].rolling(PHANTOM_WINDOW, min_periods=20).median()
    thin = (dv < PHANTOM_DOLLAR_VOL).fillna(False)
    if bool(thin.any()):
        son = int(thin.to_numpy().nonzero()[0].max())
        ilk = int(thin.to_numpy().nonzero()[0].min())
        out.append({"tarih": dates.iloc[son], "oran": None, "sinif": "hayalet_gecmis", "kural": "K3",
                    "kanit": {"donem": [dates.iloc[ilk], dates.iloc[son]],
                              "medyan_dolar_hacmi": round(float(dv.iloc[son]), 1),
                              "seans": int(thin.sum())}})
    return sorted(out, key=lambda x: x["tarih"])


def integrity_safe_start(df: pd.DataFrame) -> tuple[str | None, list[dict]]:
    """(güvenli_baslangic, kirilma_listesi). Güvenli başlangıç = SON kırılmadan sonraki İLK bar.

    NEDEN "SON" KIRILMA: iki kırılma arasındaki dönem de güvensizdir (2006-01-03'te ×0,5, 2006-10-24'te
    ×2 olan 11 sembolde arada 10 aylık YANLIŞ ölçekli bir ada var). En son dikişten öncesini toptan
    güvensiz saymak, o adayı ayrıca aramaktan hem daha basit hem daha muhafazakârdır."""
    brk = integrity_breaks(df)
    if not brk:
        return None, []
    son = max(b["tarih"] for b in brk)
    d = df["date"].astype(str).str.slice(0, 10)
    sonrasi = d[d > son]
    return (str(sonrasi.iloc[0]) if len(sonrasi) else None), brk


_INTEGRITY_APPLIED: dict = {}        # {TICKER: düşürülen satır} — YASA 6: damga SAYILIR, sessiz değil
_INTEGRITY_WARNED: set = set()


def bars_integrity() -> dict:
    """`bars_integrity.json` defterini oku — YALNIZ `store` üzerinden, FAIL-OPEN.

    OKUMA `store.read_json`DAN GEÇER; bu modül state dizininin yolunu HİÇ kurmaz. Üç gerekçe, üçü de
    bu depoda yaşanmış: (1) `store` o dizinin TEK kapısıdır ve bu modül onun istisna listesinde
    DEĞİLDİR (`test_gaps_final_v52`); (2) bozuk bir defter çağıranı düşüremez — `store` varsayılana
    düşer ve olayı ADIYLA yazar; (3) artefakt grafı (`codelaw.artifact_graph`) okuyucuyu ancak
    `store` çağrısından tanır — ham okuma, defteri "yazılıyor ama kimse okumuyor" LAĞIMI gibi
    gösterirdi (YASA 6).

    ÖNBELLEK YOK, BİLEREK: ilk sürüm mtime önbellekliydi ve anahtarının kum-havuzu yolunu içermesi
    gerekiyordu (havuzlar o yolu değiştirir; yalnız mtime'a bakan önbellek bir testin defterini
    diğerine servis ederdi). Yani önbellek, tam da kaçınmak istediğimiz yol referansını ZORUNLU
    kılıyordu. Maliyet ölçüldü ve önemsiz: defter ~60 satır, tüketiciler onu sembol başına bir kez
    okur (250 sembollük turda ~25 ms) — buna karşılık her okuma TAZE, yanlış-önbellek yüzeyi SIFIR.

    Defter YOKSA boş sözlük döner ve hiçbir şey dışlanmaz — bir bütünlük defterinin yokluğu, tüm
    ölçüm evrenini susturmak için gerekçe değildir (takvim kapısının fail-open gerekçesinin aynısı).
    Üretimi: `python -m meridian.barrepair --integrity-tara --uygula`."""
    try:
        from .. import store as _st
        return _st.read_json(INTEGRITY_FILE, {}) or {}
    except Exception as e:  # YASA 4: store'un kendisi düştü — sessizce "kısıt yok" demek, defteri
        _bar_warn("bars_integrity_unreadable", e)      # var sanıp hiç uygulamamak olurdu
        return {}


def safe_start(ticker: str) -> str | None:
    """Bu sembolün ÖLÇÜM için güvenli ilk tarihi (defterde yoksa None = kısıt yok)."""
    rec = (bars_integrity().get("semboller") or {}).get(str(ticker or "").upper())
    return (rec or {}).get("guvenli_baslangic")


def measurement_bars(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """ÖLÇÜM ÇERÇEVESİ: `bars_integrity` defterinin güvensiz saydığı dönemi DIŞLA.

    TÜKETİCİ BURADA (YASA 6): `component_ic` (evren + endeks) ve `cf_backfill` (evren + SPY) bu
    fonksiyondan geçer. Dışlama BARIN İÇİNDEN değil DEFTERDEN öğrenilir — yani ölçüm fonksiyonu
    kendi bütünlük kuralını ikinci kez yazmaz (bu depoda tekrar eden hata sınıfı: aynı yasanın iki
    kopyası zamanla ayrışır).

    `dataset` YOLU BİLEREK BAĞLANMADI — ve bu bir eksiklik değil, ÖLÇÜLMÜŞ bir karardır:
      1. `dataset.load()` CANLI karar yolunun da boğazıdır (`load_live` → `_load_live_inner` →
         `load()`, ve ikisi AYNI `_cache`'i paylaşır; `run.py once()/worker()` de onu çağırır).
         Oraya bağlamak HON'u — kırılması 22 seans önce — canlı tarama evreninden SESSİZCE
         düşürürdü: geçmişi ölçen için doğru olan, bugünü tarayan için yıkıcıdır.
      2. YALNIZ `load_cached()`e bağlamak DAHA KÖTÜ olurdu: `reflect` ebeveyni `load()`, havuz
         işçileri `load_cached()` kullanır → incumbent ve aday FARKLI bar kümesinde ölçülürdü.
         Bu, `test_bottleneck_v12`nin yazılma sebebi olan elma-armut kusurunun ta kendisi.
    Yani walk-forward/prescreen/reflect tabloları HÂLÂ kirli dönemi görüyor. Kapatılması
    `dataset.load()`un replay-girişi ile canlı-girişine AYRILMASINI gerektirir (trim çıkışta
    uygulanır, `_cache` ham kalır) ve HON/DD'nin canlı evrenden düşmesi OPERATÖR kararıdır.

    SESSİZ DEĞİL: düşen satır sayısı `integrity_report()`ta birikir ve sembol başına bir kez olay
    yazılır — çünkü "bu ölçüm neden daha az satır gördü?" sorusunun cevabı kaydedilmezse, defter
    ölçümü sessizce daraltan görünmez bir el olurdu."""
    if df is None or df.empty:
        return df
    ss = safe_start(ticker)
    if not ss:
        return df
    keep = df["date"].astype(str).str.slice(0, 10) >= ss
    dropped = int((~keep).sum())
    if not dropped:
        return df
    t = str(ticker or "?").upper()
    _INTEGRITY_APPLIED[t] = _INTEGRITY_APPLIED.get(t, 0) + dropped
    if t not in _INTEGRITY_WARNED:
        _INTEGRITY_WARNED.add(t)
        try:
            from .. import obs
            obs.warn("bars_integrity_period_excluded", ticker=t, safe_start=ss, rows=dropped,
                     detail="çözülmemiş ölçek/kimlik kırılması öncesi dönem ÖLÇÜMDEN dışlandı "
                            "(satır silinmedi; defter: state/bars_integrity.json)")
        except Exception:  # sessiz-yutma: kayıt kanalı düştü — sayaç integrity_report()'ta duruyor
            pass
    return df.loc[keep].reset_index(drop=True)


def integrity_report() -> dict:
    """Bu süreçte defter yüzünden kaç satır ölçümden dışlandı (üretilen kanıt TÜKETİLİR)."""
    led = bars_integrity()
    return {"file": INTEGRITY_FILE,
            "ledger_symbols": len((led.get("semboller") or {})),
            "ledger_rev": led.get("rev"), "generated_at": led.get("uretildi"),
            "applied": dict(sorted(_INTEGRITY_APPLIED.items())),
            "rows_excluded": sum(_INTEGRITY_APPLIED.values())}


def _note_ghost(kind: str, ticker: str, dates: list, detail: str) -> None:
    """Düşen satırları SAY ve tarih başına BİR kez duyur. Sayaç `ghost_report()` ile okunur:
    yalnız uyarı basmak, üretilip tüketilmeyen kanıt bırakmak olurdu (bu deponun YASA 6'sı)."""
    for d in dates:
        row = _GHOST.setdefault(str(d)[:10], {"rows": 0, "tickers": [], "classes": {}})
        row["rows"] += 1
        row["classes"][kind] = int(row["classes"].get(kind) or 0) + 1
        if len(row["tickers"]) < 12 and ticker not in row["tickers"]:
            row["tickers"].append(ticker)
    seen = _GHOST_EVENTED if kind == "ghost_session" else _QUAR_EVENTED
    yeni = [str(d)[:10] for d in dates if str(d)[:10] not in seen]
    if not yeni:
        return
    seen.update(yeni)
    try:
        from .. import obs
        event = ("bar_ghost_session_dropped" if kind == "ghost_session"
                 else "bar_unadjusted_row_quarantined")
        obs.warn(event, ticker=str(ticker).upper(), dates=",".join(sorted(yeni)), n=len(yeni),
                 calendar=CALENDAR, detail=detail)
    except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci kanal yok; sayaç yine tutuldu
        pass


def _emit_ghost_round() -> None:
    """TUR SONU TOPLAMI. Tarih-başına-tek olay "NE oldu"yu söyler; bu satır "NE KADAR"ı söyler —
    259 sembollük bir turda kaç satır düştü, kaç defter reddedildi. Yalnız sayı BÜYÜDÜĞÜNDE atılır:
    her turda aynı kümülatif rakamı basmak, ilk günden sonra okunmaz bir gürültü olurdu."""
    global _GHOST_EMITTED
    rep = ghost_report()
    if rep["rows"] <= _GHOST_EMITTED and not (rep["refused"] and _GHOST_EMITTED == 0):
        return
    _GHOST_EMITTED = rep["rows"]
    try:
        from .. import obs
        obs.warn("bar_ghost_round_summary", rows=rep["rows"], dates=",".join(rep["dates"]),
                 refused=len(rep["refused"]), calendar_ok=rep["calendar_ok"],
                 detail="bu süreçte kapıdan düşen hayalet/karantina satırı toplamı; DİSKTEKİ "
                        "CSV'ler için `python -m meridian.barrepair` (kuru koşu) — türetilmiş "
                        "artefaktlar onarım sonrası yeniden üretilmeli")
    except Exception:  # sessiz-yutma: kayıt kanalı düştü; sayaç ghost_report()'ta duruyor
        pass


def ghost_report() -> dict:
    """Bu SÜREÇTE kaç hayalet/karantina satırı düşürüldü, hangi tarihlerde, hangi sembollerde.

    NEDEN DİSKE YAZILMIYOR: bu sayaç `dataset.load_cached` üzerinden HAVUZ İŞÇİLERİNDE de birikir
    ve `store.write_json` kilidi SÜREÇ-İÇİDİR (bu depoda belgeli). Çok süreçli bir yazım, ölçmek
    istediğimiz bütünlüğün kendisini bozardı. Tüketici: `python -m meridian.barrepair` raporu
    (kalıcı envanter oradan, DİSKTEN üretilir) + olay defterindeki tarih-başına-bir satır."""
    return {"dates": {d: {"rows": v["rows"], "classes": dict(v["classes"]),
                          "tickers": list(v["tickers"])} for d, v in sorted(_GHOST.items())},
            "rows": sum(v["rows"] for v in _GHOST.values()),
            "calendar": CALENDAR, "calendar_ok": bool(_sessions()),
            # REDDEDİLENLER DE RAPORA GİRER: kapının DOKUNMADIĞI seriler, dokunduklarından daha
            # önemli olabilir — "hiç hayalet yok" ile "kapı bu seriyi adjudike etmeyi reddetti"
            # aynı görünmemeli (üretilip tüketilmeyen kanıt yasağının aynası).
            "refused": {t: dict(v) for t, v in sorted(_CAL_MISMATCH.items())},
            "note": "takvimde seans OLMAYAN tarihlerin satırları düşürüldü (bellek içi); DİSKTEKİ "
                    "CSV ancak bir sonraki yazımda ya da `python -m meridian.barrepair --uygula` "
                    "ile temizlenir"}


# ---------------- deterministic repair ----------------
def sanitize_bars(df: pd.DataFrame, ticker: str = "?") -> tuple[pd.DataFrame, dict]:
    """Repair the obvious, safe source glitches so the engine never trades on inconsistent bars, and
    so an old data typo can't halt today's trading. Repairs: drop NaN/non-positive OHLC rows, keep the
    last of duplicate dates, and clamp high=max(OHLC)/low=min(OHLC) (the true high must be >= all of
    open/close, the true low <= all). This is standard data cleaning, not fabrication.

    2026-07-30 EKİ — TAKVİM KAPISI: geçerli bir XNYS seansı OLMAYAN tarihin satırı DÜŞER
    (`bar_ghost_session_dropped`), ve geçerli seansta duran izole bölünme-düzeltilmemiş satır
    KARANTİNAYA alınır (`bar_unadjusted_row_quarantined`). İkisi de sessiz değildir; gerekçe ve
    ölçüm yukarıdaki blokta."""
    if df is None or df.empty:
        return df if df is not None else pd.DataFrame(), {}
    rep = {}
    n0 = len(df)
    df = df.dropna(subset=["open", "high", "low", "close"])
    df = df[(df[["open", "high", "low", "close"]] > 0).all(axis=1)]
    if len(df) != n0:
        rep["dropped_rows"] = n0 - len(df)
    d0 = int(df["date"].duplicated().sum())
    if d0:
        df = df.drop_duplicates("date", keep="last"); rep["deduped_dates"] = d0
    # SIRALAMA BURAYA ÇEKİLDİ (eskiden yalnız return satırındaydı): aşağıdaki iki kapı KOMŞU barlara
    # bakar (önceki/sonraki kapanış) ve komşuluk ancak kronolojik sırada anlamlıdır. Tekilleştirme
    # ÖNCE kalır: `keep="last"` çekim SIRASINA dayanır (taze bar önbellektekini yener) ve sıralama
    # kararlı olmadığı için önce sıralamak o kuralı sessizce bozardı.
    df = df.sort_values("date").reset_index(drop=True)
    gh, red = _calendar_scan(df)
    if red:
        # REDDİN KENDİSİ DE BİR BULGUDUR: "0 hayalet satır" ile "kapı bu seriyi hiç adjudike
        # etmedi" aynı görünmemeli. Olay DEĞİL sayı üretilir (gerekçe `_note_cal_mismatch`te);
        # duyuruyu disk yolu (`load_bars`) yapar, süreç-içi defteri `ghost_report()` okur.
        rep["calendar_mismatch_rows"] = int(red["non_session_rows"])
        _CAL_MISMATCH[str(ticker).upper()] = dict(red)
    if gh.any():
        dates = sorted({str(x)[:10] for x in df.loc[gh, "date"].astype(str)})
        rep["ghost_session_dropped"] = int(gh.sum())
        _note_ghost("ghost_session", ticker, dates,
                    "takvimde SEANS OLMAYAN tarihte bar satırı — kaynak çoğu sembolde önceki seansı "
                    "kopyalamış, bir kısmında BÖLÜNME-DÜZELTİLMEMİŞ ham fiyat yazmış; satır düştü")
        df = df.loc[~gh].reset_index(drop=True)
    q = _unadjusted_mask(df)
    if q.any():
        dates = sorted({str(x)[:10] for x in df.loc[q, "date"].astype(str)})
        rep["unadjusted_quarantined"] = int(q.sum())
        _note_ghost("unadjusted_row", ticker, dates,
                    "geçerli seansta izole düzeltilmemiş fiyat satırı (|hareket|>%35, ertesi bar "
                    "geri dönüyor, hacim tutarsız) — split_suspect artık SOFT değil, satır karantinada")
        df = df.loc[~q].reset_index(drop=True)
    hi = df[["open", "high", "low", "close"]].max(axis=1)
    lo = df[["open", "high", "low", "close"]].min(axis=1)
    fixed = int(((df["high"] < hi) | (df["low"] > lo)).sum())
    if fixed:
        df = df.assign(high=df["high"].where(df["high"] >= hi, hi), low=df["low"].where(df["low"] <= lo, lo))
        rep["clamped_ohlc"] = fixed
    return df.reset_index(drop=True), rep


# ---------------- integrity gate ----------------
def validate_bars(df: pd.DataFrame, ticker: str = "?") -> tuple[bool, list[dict]]:
    """Return (ok, issues). Hard issues (severity='hard') mean the data must NOT be traded on."""
    issues = []
    if df is None or df.empty:
        return False, [{"severity": "hard", "code": "empty", "detail": "no bars"}]
    o, h, l, c, v = df["open"], df["high"], df["low"], df["close"], df["volume"]
    if (df[["open", "high", "low", "close"]] <= 0).any().any():
        issues.append({"severity": "hard", "code": "nonpositive_price", "detail": "OHLC <= 0 present"})
    if df[["open", "high", "low", "close"]].isna().any().any():
        issues.append({"severity": "hard", "code": "nan_price", "detail": "NaN in OHLC"})
    bad_hl = (h < l) | (h < o) | (h < c) | (l > o) | (l > c)
    if bad_hl.any():
        issues.append({"severity": "hard", "code": "ohlc_inconsistent",
                       "detail": f"{int(bad_hl.sum())} bar(s) violate high>=low/open/close"})
    if df["date"].duplicated().any():
        issues.append({"severity": "hard", "code": "duplicate_dates",
                       "detail": f"{int(df['date'].duplicated().sum())} duplicate dates"})
    if not df["date"].is_monotonic_increasing:
        issues.append({"severity": "soft", "code": "unsorted", "detail": "dates not strictly increasing"})
    # ---- HAYALET SEANS: SERT (2026-07-30) ----
    # Neden sert: bu satır bir "şüphe" değil, bir OLGUDUR — piyasa o gün kapalıydı, o bar hiç var
    # olmadı. Soft bırakmak, `load_many`nin ticker'ı geçirmesi ve kararın uydurma bir bara dayanması
    # demek olurdu. Kapı (`sanitize_bars`) normalde bu satırları zaten düşürür; buraya düşen bir
    # çerçeve kapıyı ATLAMIŞ demektir ve o çerçeveye güvenilmez.
    try:
        gh = _ghost_mask(df)
        if gh.any():
            gd = sorted({str(x)[:10] for x in df.loc[gh, "date"].astype(str)})
            issues.append({"severity": "hard", "code": "ghost_session",
                           "detail": f"{int(gh.sum())} bar(s) on non-session dates ({','.join(gd[:5])}) "
                                     f"— {CALENDAR} takviminde seans yok"})
        # KOMŞULUK ANCAK SIRALI ÇERÇEVEDE ANLAMLI: sırasız bir seride "önceki/sonraki bar" gerçek
        # komşu değildir ve kural masum bir satırı SERT bulguya çevirebilirdi (sırasızlık zaten
        # yukarıda soft bulgudur — iki kez cezalandırmak yanlış hüküm üretir).
        uq = _unadjusted_mask(df) if df["date"].is_monotonic_increasing else pd.Series(False, index=df.index)
        if uq.any():
            ud = sorted({str(x)[:10] for x in df.loc[uq, "date"].astype(str)})
            issues.append({"severity": "hard", "code": "unadjusted_row",
                           "detail": f"{int(uq.sum())} izole düzeltilmemiş satır ({','.join(ud[:5])}) "
                                     f"— sıçra-ve-geri-dön + hacim tutarsızlığı"})
    except Exception as e:  # sessiz-yutma DEĞİL: takvim/imza hesabı patlarsa kapı YOK demektir, söylenir
        _bar_warn("bar_calendar_validate_failed", e, ticker=str(ticker).upper())
    ret = (c / c.shift(1) - 1.0).abs()
    n_susp = int((ret > SPLIT_SUSPECT_RET).sum())
    if n_susp:
        worst = df.loc[ret.idxmax(), "date"] if ret.notna().any() else None
        # SOFT KALIR — ama artık YALNIZ gerçek şüphe için: hayalet-tarihli ve izole-düzeltilmemiş
        # vakalar yukarıda SERT'e yükseldi. Geriye kalan "büyük hareket" sınıfı gerçekten belirsizdir
        # (meşru kazanç şoku ile ölçek dikişi aynı imzayı verir) ve tek satır düşürerek çözülmez.
        issues.append({"severity": "soft", "code": "split_suspect",
                       "detail": f"{n_susp} day(s) with |move|>{SPLIT_SUSPECT_RET:.0%} (worst {worst}) — possible unadjusted split"})
    # --- #34 completeness: zero-volume bars, big calendar gaps, and staleness ---
    n_zero = int((v <= 0).sum())
    if n_zero:
        issues.append({"severity": "soft", "code": "zero_volume",
                       "detail": f"{n_zero} bar(s) with volume<=0 — RS/volume signals unreliable there"})
    if len(df) > 2 and df["date"].is_monotonic_increasing:
        gaps = df["date"].diff().dt.days.dropna()
        big = int((gaps > 10).sum())                      # >10 calendar days between sessions = a hole
        if big:
            issues.append({"severity": "soft", "code": "calendar_gap",
                           "detail": f"{big} gap(s) >10 days between consecutive bars (max {int(gaps.max())}d)"})
    try:
        import datetime as _dt
        stale_days = (_dt.date.today() - df["date"].max().date()).days
        if stale_days > 10:                               # last bar is old — the name may be delisted/halted
            issues.append({"severity": "soft", "code": "stale_ticker",
                           "detail": f"last bar {stale_days}d old — possibly delisted/halted; RS is stale"})
    except Exception:  # sessiz-yutma: bayatlık yalnız SOFT bir bulgu üretir; hesaplanamaması sert bütünlük kararını değiştirmez (ok sadece hard bulgulara bakar)
        pass
    ok = not any(i["severity"] == "hard" for i in issues)
    return ok, issues


class FetchError(RuntimeError):
    """Kaynak İSTEĞİ başarısız oldu — 'kaynak veri yok dedi' ile KARIŞTIRILMAMALI.

    `.reason` makine-okunur ve KISA tutulur (örn. "HTTP 429", "ConnectTimeout"). URL ASLA taşınmaz:
    zincirdeki FMP isteği anahtarı sorgu parametresinde götürür ve httpx'in hata metni tam URL'i
    içerir — o metin bir gün loglanırsa anahtar diske düşer."""

    def __init__(self, reason: str, attempts: int):
        super().__init__(f"fetch failed after {attempts} tries: {reason}")
        self.reason = reason
        self.attempts = attempts


def _get_json(url: str, timeout: float, attempts: int = 3):
    reason = "bilinmiyor"
    for i in range(attempts):
        try:
            r = httpx.get(url, timeout=timeout, headers=_UA, follow_redirects=True)
            r.raise_for_status()
            return r
        except httpx.HTTPStatusError as e:
            reason = f"HTTP {e.response.status_code}"
            time.sleep(0.4 * (2 ** i))   # 0.4, 0.8, 1.6s backoff
        except Exception as e:
            reason = type(e).__name__
            time.sleep(0.4 * (2 ** i))
    raise FetchError(reason, attempts)


def _fetch_cboe(ticker: str, timeout: float) -> pd.DataFrame:
    data = _get_json(CBOE.format(sym=ticker.upper()), timeout).json().get("data", [])
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    return df[COLS]


def _fetch_nasdaq(ticker: str, start: str, end: str, timeout: float) -> pd.DataFrame:
    rows = (_get_json(NASDAQ.format(sym=ticker.upper(), d1=start, d2=end), timeout).json()
            .get("data") or {}).get("tradesTable", {}).get("rows") or []
    if not rows:
        return pd.DataFrame()
    def num(x):
        return float(str(x).replace("$", "").replace(",", "")) if x not in (None, "", "N/A") else None
    recs = [{"date": pd.to_datetime(r_["date"]), "open": num(r_.get("open")), "high": num(r_.get("high")),
             "low": num(r_.get("low")), "close": num(r_.get("close")), "volume": num(r_.get("volume"))}
            for r_ in rows]
    return pd.DataFrame(recs)[COLS]


def _fetch_fmp(ticker: str, start: str, end: str, timeout: float) -> pd.DataFrame:
    """Full SPLIT-adjusted EOD from FMP (freshest source; ~1 day ahead of the delayed Cboe feed).
    DİKKAT (2026-07-23 doküman doğrulaması): FMP `/historical-price-eod/full` YALNIZ split-adjusted verir,
    dividend-adjusted DEĞİL (o ayrı endpoint: /stable/historical-price-eod/dividend-adjusted → adjClose).
    Cboe fallback de split-only olduğundan iki kaynak AYNI ölçekte — splice güvenli, ama "dividend-adjusted"
    varsaymak yanlış olurdu. Only reachable when FMP_API_KEY is set. Returns the WHOLE series so the cache is single-source
    (no Cboe/FMP adjustment seam) once a full refetch lands."""
    from . import fmp
    rows = fmp.historical_eod(ticker)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if "date" not in df.columns or not all(c in df.columns for c in ("open", "high", "low", "close", "volume")):
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["date"])
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df[COLS].dropna(subset=["close"]).sort_values("date").reset_index(drop=True)


def _fetch_massive(ticker: str, end: str, timeout: float = 30.0) -> pd.DataFrame:
    """Massive'in GÜNLÜK anlık görüntüsünden bu sembolün son barı. AĞA SEMBOL BAŞINA GİTMEZ: anlık
    görüntü tek grouped çağrısıyla dolar, disk+bellekte önbelleklenir ve turdaki 250 sembolün hepsi
    aynı çağrıdan okunur. Dönen çerçeve TEK satırlıktır — bu yüzden yalnız geçmişi ZATEN olan
    sembollerde zincire konur (bkz. MIN_INCREMENTAL_BARS)."""
    from . import massive
    # EN TAZE YAYINLANMIŞ bar (kesin bir gün DEĞİL): `end` bugünse ve günün EOD'si henüz
    # yayınlanmadıysa kesin-gün isteği boş döner ve zincir Cboe'ye düşerdi — canlı defterde 250
    # ticker'ın hepsi `source=cboe` çıkmıştı, yani kotayı kurtaran yol hiç çalışmamıştı.
    bar = massive.latest_bar(ticker, end)
    if not bar:
        return pd.DataFrame()
    df = pd.DataFrame([bar])
    df["date"] = pd.to_datetime(df["date"])
    return df[COLS]


def _fetch_massive_hist(ticker: str, start: str, end: str, timeout: float = 30.0) -> pd.DataFrame:
    """Massive custom-bars ile SEMBOL-BAŞINA yakın-dönem penceresi (~son 2 yıl).

    Kota tahsis politikası (operatör kararı, 2026-07-29): FMP kotası BİLGİ katmanına ayrıldı (temel
    veri, insider, kazanç, haber, 13F); bar tarafı Massive'e taşındı. Bu kol, grouped'ın karşılamadığı
    yolu kapatır — tek sembolün bir PENCERESİNİ isteyen çağrılar (işlem replay pencereleri, analitik).
    Yalnız `massive.covers(start)` doğruyken zincire girer; 2 yıldan eski başlangıçlar FMP'de kalır."""
    from . import massive
    rows = massive.custom_bars(ticker, start, end)
    if not rows:
        return pd.DataFrame()
    return massive.to_frame(rows)


def _massive_crosscheck(ticker: str, df: pd.DataFrame, src: str) -> None:
    """ÇAPRAZ KAYNAK DOĞRULAMASI: zincirin yazdığı son kapanış ile Massive'in aynı güne ait kapanışı
    aynı mı? Uyuşmazlık v1'de ALARMDIR — otomatik karantina YOK (yanlış tarafı bilmiyoruz; kaynak
    seçimini bir ölçüm birikmeden değiştirmek, teşhisi olmayan bir tedavi olurdu).

    Maliyet SIFIRA yakındır: anlık görüntü zaten tek çağrıyla alınmıştır, burada yalnız sözlük
    araması yapılır. Massive'in KENDİSİ yazdıysa kıyas anlamsızdır — atlanır."""
    if src == "massive" or df is None or df.empty:
        return
    try:
        from . import massive
        if not massive.available():
            return
        last = df.sort_values("date").iloc[-1]
        d = str(pd.Timestamp(last["date"]).date())
        bar = massive.bar_for(ticker, d)
        if not bar or not bar.get("close"):
            return
        pc, mc = float(last["close"]), float(bar["close"])
        if pc <= 0:
            return
        dev = abs(mc - pc) / pc
        _record_xcheck(ticker.upper(), src, dev)
        if dev > MASSIVE_TOL:
            from .. import obs
            # KENDİ METNİNİN VAADİNİ TUTAN SEVİYE (K1, 2026-07-30): bu olay "v1'de ALARM" diye
            # yazıyordu ama `obs.warn` seviyesindeydi — ve notify.py:84 alarm-olmayan her satırı
            # eler, yani uyuşmazlık NOTIFY/inbox/telefon zincirine hiç giremiyordu. Canlıda 1
            # gerçek uyuşmazlık olayı var ve hiçbir özel yüzeye ulaşmadı. İki kaynağın fiyat
            # ayrışması DATA_QUALITY sınıfıdır: kararların dayandığı barın kendisi tartışmalı.
            # Karantina hâlâ YOK (davranış değişmedi) — değişen tek şey duyulabilirlik.
            obs.alarm(obs.ALARM_DATA_QUALITY,
                      f"BAR KAYNAK UYUŞMAZLIĞI: {ticker.upper()} {d} — {src} {round(pc, 4)} vs "
                      f"massive {round(mc, 4)} (%{round(dev * 100, 3)} > tol %{round(MASSIVE_TOL * 100, 3)})",
                      # MAKİNE-OKUNUR AD KORUNUR: obs.alarm olay adını "DATA_QUALITY <mesaj>"a
                      # çevirir, yani `event == "bar_kaynak_uyusmazligi"` süzgeci ARTIK TUTMAZ.
                      # Bu tam olarak `failed_broker_rejection` tuzağıydı (watchdog süzgeci hiç
                      # yayınlanmayan bir olay adını bekliyordu). Ad `kind` alanında yaşar —
                      # bugün süzgeci olan bir tüketici yok, yarın olursa imza hazır.
                      kind="bar_kaynak_uyusmazligi",
                      ticker=ticker.upper(), date=d, source=src,
                      source_close=round(pc, 4), massive_close=round(mc, 4),
                      dev_pct=round(dev * 100, 3), tol_pct=round(MASSIVE_TOL * 100, 3),
                      detail="aynı ticker+gün için iki kaynak farklı kapanış veriyor — otomatik "
                             "karantina YOK; birikim: state/" + CROSSCHECK_FILE)
    except Exception as e:
        _bar_warn("massive_crosscheck_failed", e, ticker=ticker.upper())


def _record_xcheck(ticker: str, src: str, dev: float) -> None:
    """Ölçümü BİRİKTİR. Yalnız alarm basmak, üretilip tüketilmeyen kanıt bırakmak olurdu: kaç bar
    kıyaslandı, kaçı toleransı aştı, en kötüsü ne — karar ancak bu sayılardan çıkar."""
    global _XCHECK_DIRTY
    reg = _xcheck()
    row = reg.setdefault(ticker, {"n": 0, "mismatch": 0, "max_dev": 0.0, "source": src})
    row["n"] = int(row.get("n") or 0) + 1
    row["source"] = src
    if dev > MASSIVE_TOL:
        row["mismatch"] = int(row.get("mismatch") or 0) + 1
    if dev > float(row.get("max_dev") or 0.0):
        row["max_dev"] = round(float(dev), 6)
    _XCHECK_DIRTY += 1
    if _XCHECK_DIRTY >= _XCHECK_FLUSH_EVERY:
        flush_xcheck()


def _xcheck() -> dict:
    global _XCHECK
    if not _XCHECK:
        from .. import store
        _XCHECK = store.read_json(CROSSCHECK_FILE, {}) or {}
    return _XCHECK


def flush_xcheck() -> None:
    global _XCHECK_DIRTY
    try:
        from .. import store
        store.write_json(CROSSCHECK_FILE, _XCHECK)
        _XCHECK_DIRTY = 0
    except Exception as e:
        _bar_warn("massive_xcheck_write_failed", e, file=CROSSCHECK_FILE)


def crosscheck_report() -> dict:
    """Çapraz-kaynak ölçümünün okunabilir özeti: Massive ile mevcut zincir ne kadar örtüşüyor?
    `--dogrula`nın yanında İKİNCİ ve bağımsız kanıt — bu sayılar canlı turlarda kendiliğinden birikir."""
    reg = _xcheck()
    n = sum(int(v.get("n") or 0) for v in reg.values())
    mism = sum(int(v.get("mismatch") or 0) for v in reg.values())
    worst = max((float(v.get("max_dev") or 0.0) for v in reg.values()), default=0.0)
    worst_t = max(reg, key=lambda t: float(reg[t].get("max_dev") or 0.0), default=None) if reg else None
    return {"tickers": len(reg), "compared": n, "mismatches": mism,
            "mismatch_pct": round(mism / n, 4) if n else None,
            "max_dev": round(worst, 6) if reg else None, "max_dev_ticker": worst_t,
            "tol_pct": round(MASSIVE_TOL * 100, 3),
            "note": "Massive vs zincirin yazdığı kapanış, ÖRTÜŞEN günlerde. Uyuşmazlık ALARM'dır, "
                    "karantina değil — hangi tarafın haklı olduğu ayrıca ölçülür (massive --dogrula)"}


def _log_massive_mode() -> None:
    """Hangi modda koştuğumuz süreç başına BİR kez kaydedilir: 'yalnız-alarm' ile 'yazım' arasındaki
    fark, FMP kotasının yanıp yanmadığıdır — sessiz kalırsa operatör hangi rejimde olduğunu bilemez."""
    global _MASSIVE_MODE_LOGGED
    if _MASSIVE_MODE_LOGGED:
        return
    _MASSIVE_MODE_LOGGED = True
    try:
        from . import massive
        from .. import obs
        obs.log("massive_mode", mode=massive.mode(), write_enabled=massive.write_enabled(),
                detail="yazim = artımlı barları Massive yazar (sembol başına FMP isteği YOK); "
                       "yalniz_alarm = zincir değişmedi, Massive yalnız kıyaslanıyor")
    except Exception:
        # sessiz-yutma: kayıt kanalı düştü; mod kararının kendisi bundan etkilenmez
        pass


# ==================================================================================================
# AYNI-AKŞAM BACAĞI (Alpaca IEX) + T+1 OTORİTER DÜZELTME + ONARIM GEÇİDİ  (2026-07-30)
# ==================================================================================================
# KÖK NEDEN (Rol 1'in kanıtlı teşhisi): zincirin en taze kolu (Massive grouped) ücretsiz katmanda
# T+1 yayınlıyor — canlı kanıt state/massive_grouped_last.json (date 07-28, fetched_at 07-29 21:15Z).
# Kapanış sonrası pencerede yalnız cboe/nasdaq kısmileri geliyor: 07-29 barı ertesi gün hâlâ 259
# sembolün 44'ünde (kapsama 0,172). Yani "akşam yayını" varsayımı sessizce çökmüştü ve motor her
# seans için sahte bir "SEANS ATLANDI" alarmı üretiyordu (164 tarihsel satır, aynı imza).
#
# BACAK İKİ BASAMAKLIDIR (hangisinin servis ettiği KAYNAK DAMGASINDAN okunur):
#   alpaca_sip → konsolide günlük bar. Hacim GERÇEK; ölçekleme sorusu yok. ⚠ YALNIZ GEÇMİŞ SEANS:
#                ölçüldü (2026-07-30 21:14Z) ki BUGÜNÜN barı için sip 403 döner ("recent SIP"
#                penceresi takvim günü bitene kadar sürüyor). Rol 1'in 07-29'daki 200'ü DÜNÜ
#                sorduğu için gelmişti — yani aynı-akşam iddiasını hiç sınamamıştı.
#   alpaca_iex → tek borsanın temsilî barı. Hacim ÖLÇEKLENMEDEN kullanılamaz (aşağıda). Canlı ölçüm:
#                IEX hacmi konsolidenin medyan %2,2-2,5'i — yani ölçeklemesiz yazım rvol'ü ~40 kat
#                küçültürdü. AYNI AKŞAMIN TEK KATMANI BUDUR; ölü kod değil, yolun kendisi.
# Basamak reddi ham hata metniyle deftere yazılır (alpaca_sip_rejected) — ama artık YALNIZ geçmiş
# seansta: bugünün seansı için sip hiç sorulmaz, o yüzden "abonelik reddetti" satırı ancak GERÇEK
# bir yetki arızasında doğar.
#
# TASARIM — DÖRT PARÇA, HER BİRİ DAR:
#   1. BACAK   : GÜNCEL seansın barını aynı akşam getirir (fiilen iex). GEÇMİŞ TAŞIMAZ: yalnız
#                önbelleğin son barından SONRAKİ tarih (ya da kendi yazdığı geçici barın
#                tazelenmesi) yazılabilir. Sahiplik ASLA ona geçmez (massive ile aynı ilke).
#   2. SIP DÜZELTİCİ (2026-07-30, tasarım düzeltmesi): ertesi günün onarım/düzeltme koşusunda,
#                dünün IEX-damgalı satırları KONSOLİDE sip barıyla değiştirilir. Massive'den ÖNCE
#                koşar — çünkü sip o saatte hazırdır ve grouped kapsaması gecikebilir (canlı: 0,172).
#                Bu basamak ne SAHİPLİK alır ne de NİHAİ otoritedir; yalnız geçici satırı temsilîden
#                konsolideye taşır ve hacim oranını GERÇEK ölçümle tazeler.
#   3. DÜZELTME: Massive grouped D barını (ertesi gün) getirdiğinde D'nin satırları NİHAİ otoriteyle
#                EZİLİR — sip düzelticisi çalışmış olsa da. Bu bir "sessiz bar mutasyonu" DEĞİLDİR:
#                mevcut SANCTIONED yoldan geçer (`_bump_wf_rev()` → watchdog `rev_bumped` görür) +
#                `bar_source_upgrade` olayı + ıraksama ÖLÇÜMÜ. Sıra: iex → sip → massive.
#   4. ONARIM  : seans başına bir kez son K seansın kapsaması taranır; eksik seans grouped ile kapanır.
#
# ⚠ IEX HACMİ KONSOLİDE HACİM DEĞİLDİR (yalnız 3. basamak için geçerli). `v` yalnız IEX'te dönen hacim —
# konsolidenin küçük bir kesri. Düzeltmeden yazılırsa rvol20 = bugünkü_IEX / 20g_konsolide_ortalama
# ≈ 0'a çöker ve hacim kapıları HİÇ açılmaz: hiçbir istisna fırlamadan, hiçbir testi kırmadan,
# sinyalin sessizce ölmesi. Bu yüzden hacim SEMBOL BAŞINA ÖLÇÜLMÜŞ oranla ölçeklenir; oranı
# OLMAYAN sembolde hacim UYDURULMAZ — 0 yazılır (hacim türevleri muhafazakâr tarafta kapanır) ve
# satır deftere `volume_scaled=false` ile damgalanır. Fiyat alanları ölçeklenmez (IEX işlem
# fiyatları temsilîdir); kapanış sapması ıraksama defterinde ÖLÇÜLÜR, varsayılmaz.
ALPACA_SIP_SOURCE = "alpaca_sip"      # BİRİNCİL: konsolide bar (ölçekleme YOK) — canlı doğrulandı
ALPACA_SOURCE = "alpaca_iex"          # YEDEK: tek borsanın temsilî barı (hacim ÖLÇEKLENİR)
_LEG_SOURCES = (ALPACA_SIP_SOURCE, ALPACA_SOURCE)
# GEÇMİŞİ SAHİPLENMEYEN KAYNAKLAR: hepsi yalnız EKLER (biri T+1 gecikmeli tek bar, diğerleri
# aynı-akşam barı). Sabitleme, dikiş defteri ve corporate-action yükseltmesi aynı listeyi okur —
# üç yerde ayrı ayrı yazılsaydı biri güncellenip diğeri unutulurdu (bu depoda yaşanmış hata sınıfı).
_NON_OWNING = ("massive", *_LEG_SOURCES)
SAME_EVENING_FILE = "bar_same_evening.json"   # geçici barlar + hacim kalibrasyonu + ıraksama birikimi
SAME_EVENING_MAX_AGE_DAYS = 3         # bacak yalnız GÜNCEL/yakın seans için — daha eskisi zincirin işi
VOLUME_CAL_DAYS = 45                  # bootstrap örnekleme penceresi (takvim günü)
VOLUME_CAL_MIN_SAMPLES = 5            # bu kadar eşleşen gün olmadan oran YAZILMAZ (ölçüm yoksa None)
VOLUME_CAL_MAX_AGE_DAYS = 30          # kalibrasyon bayatlarsa yeniden ölçülür (borsa payları kayar)
VOLUME_CAL_KEEP = 10                  # sembol başına saklanan son ölçüm sayısı (medyan bunun üstünde)
REPAIR_LOOKBACK = 5                   # onarım geçidi: son K seans taranır
REPAIR_MIN_COVERAGE = 0.90            # motorun kapısıyla AYNI eşik ailesi (loop.UNIVERSE_MIN_COVERAGE)
PROVISIONAL_KEEP_SESSIONS = 10        # defterde tutulan geçici seans sayısı (sınırsız büyümesin)

# ÖLÇÜM NEREDE BİRİKİYOR — VE NEDEN `data_quality.json` DEĞİL (beyan edilmiş sapma, 2026-07-30):
# brief "ıraksama data_quality.json'a yeni bir anahtar altında BİRİKSİN" diyordu. Ölçülmüş engel:
# `loop.daily_cycle` o dosyayı her seansta SIFIRDAN yazıyor (loop.py:334 — tek bir sözlük literali,
# read-modify-write DEĞİL) ve loop.py bu turda başka bir ajanın yüzeyi. Oraya yazılan bir anahtar
# aynı turun içinde silinirdi: "birikim" o dosyada YAPISAL olarak imkânsız. Üretilip tüketilmeyen —
# üstelik silinen — kanıt bırakmaktansa defter kendi dosyasında tutulur ve DIŞ tüketiciye bağlanır
# (scheduler.status() → /api/hermes `scheduler` + /api/scheduler → pano). YASA 6 böyle karşılanır.
_SE: dict = {}
_SE_DIRTY = 0
_SE_FLUSH_EVERY = 25                  # 250'lik turda ~10 yazım (her sembolde bir değil)
_SE_PENDING_EVENT: set = set()        # olay ATILACAK seanslar (tur sonunda tek satır, sembol başına değil)
_ALPACA_MEMO: dict = {}               # {seans: {TICKER: bar}} — süreç-içi; evren TEK çağrı grubunda
_ALPACA_ASKED: dict = {}              # {seans: {TICKER,...}} — sorulmuş sembol iki kez sorulmaz
_ALPACA_PENDING: dict = {}            # {TICKER: {tarih: ham kayıt}} — yazım BAŞARILI olursa deftere geçer

try:
    import contextvars as _cv
    _LEG_SESSION = _cv.ContextVar("meridian_same_evening_session", default=None)
except Exception:  # sessiz-yutma: contextvars yoksa (imkânsız, stdlib) bacak KAPALI kalır — güvenli taraf
    _LEG_SESSION = None


class _LegCtx:
    """`with data.live_session_leg(seans):` — bacağı YALNIZ canlı ileri-yürüyen yol için açar.

    NEDEN AÇIK BİR KAPI: replay/karantina yolu (dataset.load) ile canlı yol (dataset.load_live)
    AYNI `load_bars`ı çağırır. Bacağı modül düzeyinde açık bırakmak, bugünün IEX barını 2023
    replay'ine sızdırabilirdi — look-ahead karantinasının aynı dersi. Kapıyı SEANS ADIYLA açmak
    ikinci bir güvence: çağıran GERÇEKTEN KAPANMIŞ bir seans adı veremiyorsa (scheduler dışında
    kimse veremez) bacak hiç çalışmaz. Seans içi çağrıda snapshot KISMİ bar döndürür — o yüzden
    "hangi seans" sorusunun cevabı tahminle değil, çağıranın bilgisiyle verilir."""

    def __init__(self, session: str | None):
        self.session = str(session)[:10] if session else None
        self._token = None

    def __enter__(self):
        if _LEG_SESSION is not None:
            self._token = _LEG_SESSION.set(self.session)
        return self

    def __exit__(self, *exc):
        if _LEG_SESSION is not None and self._token is not None:
            _LEG_SESSION.reset(self._token)
        return False


def live_session_leg(session: str | None):
    return _LegCtx(session)


def _leg_session() -> str | None:
    return _LEG_SESSION.get() if _LEG_SESSION is not None else None


# ---------------- aynı-akşam defteri (geçici barlar + kalibrasyon + ıraksama) --------------------
def _se() -> dict:
    global _SE
    if not _SE:
        from .. import store
        doc = store.read_json(SAME_EVENING_FILE, {}) or {}
        if not isinstance(doc, dict):
            doc = {}
        doc.setdefault("provisional", {})
        doc.setdefault("volume_ratio", {})
        doc.setdefault("sessions", {})
        _SE = doc
    return _SE


def flush_same_evening() -> None:
    """Defteri diske yaz + biriken ıraksama olaylarını TUR BAŞINA BİR kez duyur."""
    global _SE_DIRTY
    try:
        from .. import memory, store
        doc = _se()
        doc["updated"] = memory.now_iso()
        store.write_json(SAME_EVENING_FILE, doc)
        _SE_DIRTY = 0
    except Exception as e:
        _bar_warn("same_evening_write_failed", e, file=SAME_EVENING_FILE)
    _emit_upgrade_events()


def _se_touch() -> None:
    global _SE_DIRTY
    _SE_DIRTY += 1
    if _SE_DIRTY >= _SE_FLUSH_EVERY:
        flush_same_evening()


def _note_provisional(ticker: str, rows: dict) -> None:
    """`{tarih: kayıt}` geçici (IEX kaynaklı) bar(lar)ını deftere işle. Kayıt HAM IEX hacmini de
    taşır: T+1 düzeltmesi geldiğinde GERÇEK konsolide/IEX oranı ancak ikisi yan yana ölçülebilir."""
    if not rows:
        return
    reg = _se()["provisional"].setdefault(ticker.upper(), {})
    reg.update(rows)
    for d in sorted(reg)[:-PROVISIONAL_KEEP_SESSIONS]:      # defter sınırsız büyümez
        reg.pop(d, None)
    _se_touch()


def _provisional_dates(ticker: str) -> set:
    return set((_se()["provisional"].get(ticker.upper()) or {}).keys())


def _volume_ratio(ticker: str) -> float | None:
    """Konsolide/IEX hacim oranı — ÖLÇÜLMÜŞSE. Ölçülmemişse None (varsayılan oran UYDURULMAZ)."""
    row = (_se()["volume_ratio"].get(ticker.upper()) or {})
    r = row.get("ratio")
    try:
        r = float(r)
    except (TypeError, ValueError):  # sessiz-yutma: defterdeki tek alan bozuk — "ölçüm yok" sayılır (muhafazakâr taraf)
        return None
    return r if r > 0 else None


def _median(xs: list) -> float | None:
    vals = sorted(float(x) for x in xs if x is not None and float(x) > 0)
    if not vals:
        return None
    n = len(vals)
    return vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2.0


def _set_volume_ratio(ticker: str, samples: list, source: str) -> float | None:
    from .. import memory
    t = ticker.upper()
    keep = [float(s) for s in samples if s and float(s) > 0][-VOLUME_CAL_KEEP:]
    ratio = _median(keep)
    _se()["volume_ratio"][t] = {"ratio": round(ratio, 4) if ratio else None, "n": len(keep),
                                "samples": [round(s, 4) for s in keep], "source": source,
                                "at": memory.now_iso()}
    _se_touch()
    return ratio


# ---------------- bacak: Alpaca IEX aynı-akşam barı ---------------------------------------------
def _leg_universe(ticker: str) -> list:
    """İlk çağrıda TÜM evren tek istek grubunda sorulur (SPY + REPLAY_UNIVERSE + istenen sembol);
    o gruptaki sonraki her sembol bedavadır. Evren dışındaki bir sembol (Finviz keşfi) kendi küçük
    isteğini yapar. SAYI YAZILMAZ: buradaki eski "259 sembol ≈ 3 çağrı" notu evren büyüdükçe
    sessizce yalan söylüyordu — büyüklük `REPLAY_UNIVERSE`ün kendisinden okunur."""
    return [INDEX_SYMBOL, *REPLAY_UNIVERSE, ticker.upper()]


def _leg_temiz_cevap(source, calls, fails) -> bool:
    """BACAK İSTEĞİ "TEMİZ TAM CEVAP" MI? — TEK YASA, İKİ TÜKETİCİ.

    (a) `_alpaca_session_bars`: temizse barı DÖNMEYEN sembol de `asked` defterine girer (tekrar-dövme
        yasağı — bkz. C20 bloğu); (b) `_leg_outcome_reason`: temizse barsızlık `"empty"`dir, temiz
        DEĞİLSE `outcomes`a `error:` yazılır (HATA ≠ BOŞ).
    İKİ KOPYA YAZILSAYDI biri güncellenir diğeri unutulurdu — ve bu tam olarak yaşandı: C20
    2026-08-02'de (a)'da düzeltildi, (b) açık kaldı ve ROADMAP küçük-kuyruğuna düştü."""
    return bool(source) and int(calls or 0) > 0 and int(fails or 0) == 0


def _leg_outcome_reason(tasima: dict) -> str | None:
    """Bacak barsız döndüyse bu bir CEVAP mı, bir ARIZA mı? Cevapsa None (`"empty"` meşru), arızaysa
    `outcomes`a yazılacak NEDEN (çağıran başına `error:` önekini koyar).

    ÖLÇÜLÜR, TAHMİN EDİLMEZ: girdisi `alpaca.data_transport()` sayaçlarının BU ÇAĞRIDAKİ deltası ve
    sembolün `asked` defterindeki hâli. `asked` zaten "bu sembol hakkında GÜVENİLİR bir cevabımız
    var" defteridir; ikinci bir ölçüt uydurmak aynı yasanın ikinci uygulaması olurdu.

    ÜÇ ARIZA SINIFI AYRI ADLANDIRILIR çünkü operatörün yapacağı şey farklıdır: `transport_fail`
    (istek düştü — 429/5xx), `transport_no_call` (ağa HİÇ çıkılmadı: soğuma ya da anahtarsızlık),
    `transport_no_source` (istek gitti, hiçbir katman servis etmedi). Üçü de sembol hakkında HÜKÜM
    VERMEZ; hepsi `source_error` hükmüne akar ve `_record_no_data` serisini BESLEMEZ."""
    if not tasima:
        # ÖLÇÜM YOK (kayıtlı sahteler / eski çağrı yolu): "arıza" demek uydurma olurdu → eski
        # davranış korunur ve barsızlık `"empty"` sayılır.
        return None
    if tasima.get("cevaplandi"):
        return None                                   # TEMİZ cevap geldi, bar yok → gerçekten barsız
    fails, calls = int(tasima.get("fails") or 0), int(tasima.get("calls") or 0)
    if fails:
        return f"transport_fail:{fails}/{calls}"
    if not calls:
        return "transport_no_call"
    return "transport_no_source"


def _alpaca_session_bars(ticker: str, session: str, tasima: dict | None = None) -> dict:
    """{TICKER: bar + `_source`}. Damga BAR BAŞINA taşınır: hangi basamağın (sip/iex)
    servis ettiği tahmin edilmez — `alpaca.same_evening_bars` söyler ve defterde o adla yaşar.
    Basamak turlar arasında değişebilir (abonelik soğuması), o yüzden damga sembolle birlikte gider.

    `asked` İSTEKTEN SONRA İŞARETLENİR (denetim C20, 2026-08-02). Eskiden işaret istekten ÖNCE
    atılıyordu ve `same_evening_bars` ARIZADA FIRLATMIYOR ({"source": None, "bars": {}} döner),
    altındaki `snapshots`/`daily_bars` ise chunk arızasında KISMİ sonuç döndürüyor. Yani 3 chunk'ın
    2.'si 429 aldığında ~150 sembol "soruldu" sayılıyor ama memo'ya HİÇ girmiyordu; defteri temizleyen
    üretim yolu olmadığı için o semboller SEANS BOYUNCA bir daha SORULAMIYOR (`need` boş kalıyor),
    `_session_coverage` 0,90 altında sıkışıyor ve merdiven `_declare_terminal_skip`e yürüyordu —
    bacağın kapatmak için yazıldığı SAHTE "SEANS ATLANDI" sınıfının ta kendisi.

    "CEVAP GELDİ" NASIL ÖLÇÜLÜR (uydurma yasağı — tahmin edilmez, SAYAÇTAN okunur): `bars` içinde
    dönen sembol tanım gereği cevaplamıştır. Barsız kalan sembol için iki ayrı gerçek vardır ve
    dönen sözlük ikisini ayırt etmez: (a) istek TEMİZ tamamlandı, sembolün o seansta gerçekten barı
    yok; (b) istek düştü/soğumaya takıldı, sembol HİÇ sorulmadı. Ayrımı `alpaca.data_transport()`
    sayaçları verir — `calls` istek başına, `fails` arıza başına artar (alpaca._get_data). En az bir
    istek çıktıysa (calls>0), hiç arıza yoksa (fails==0) ve bir katman servis ettiyse (source), o
    turda İSTENEN HER SEMBOL cevaplanmıştır → hepsi işaretlenir; aksi hâlde YALNIZ barı dönenler
    işaretlenir, kalanlar bir sonraki poll'de yeniden sorulur.

    TEKRAR-DÖVME BURADA DEĞİL, SOĞUMADA DURUR: arıza `alpaca._data_fail` ile 300 sn'lik soğuma
    yazar; aynı turdaki sonraki semboller `_data_cooled` yüzünden AĞA HİÇ ÇIKMAZ (None → bars boş →
    yine işaret yok). Soğuma dolunca poll yeniden dener — kaybedilen tek şey bir soğuma penceresidir,
    bütün seans değil.

    `tasima` ÇIKTI PARAMETRESİ (ROADMAP küçük-kuyruk, 2026-08-02): verilirse bu çağrıdaki taşıma
    deltası (`calls`/`fails`/`source`), istek çıkıp çıkmadığı (`istendi`) ve sembolün NİHAİ `asked`
    hâli (`cevaplandi`) doldurulur. Tüketicisi `_fetch_alpaca_session`tir: barsızlığın "cevap" mı
    "arıza" mı olduğu ancak bu sayaçlarla ayrılır (bkz. `_leg_outcome_reason`). Sözlük verilmezse
    davranış BİT-BİT eskisi gibidir — bu bir alan kazanımıdır, sözleşme değişikliği değil."""
    from . import alpaca
    memo = _ALPACA_MEMO.setdefault(session, {})
    asked = _ALPACA_ASKED.setdefault(session, set())
    need = [s for s in _leg_universe(ticker) if s.upper() not in asked]
    if tasima is not None:
        tasima.update({"istendi": bool(need), "calls": 0, "fails": 0, "source": None})
    if need:
        _tr0 = alpaca.data_transport() or {}
        res = alpaca.same_evening_bars(need, session) or {}
        _tr1 = alpaca.data_transport() or {}
        src = res.get("source")
        bars = res.get("bars") or {}
        for sym, bar in bars.items():
            memo[sym] = {**bar, "_source": src}
        answered = {str(s).upper() for s in bars}
        _calls = int(_tr1.get("calls") or 0) - int(_tr0.get("calls") or 0)
        _fails = int(_tr1.get("fails") or 0) - int(_tr0.get("fails") or 0)
        if tasima is not None:
            tasima.update({"calls": _calls, "fails": _fails, "source": src})
        if _leg_temiz_cevap(src, _calls, _fails):
            answered |= {s.upper() for s in need}     # TEMİZ tam cevap: barsız sembol GERÇEKTEN barsız
        asked.update(answered)
    if tasima is not None:
        # NİHAİ HÂL, ARA HÂL DEĞİL: sembol bu turda cevaplamış da olabilir, ÖNCEKİ bir turun temiz
        # cevabıyla zaten defterde de olabilir. İkisi de "güvenilir cevabımız var" demektir.
        tasima["cevaplandi"] = ticker.upper() in asked
    return memo


def _fetch_alpaca_session(ticker: str, session: str) -> tuple[pd.DataFrame, str | None, str | None]:
    """Aynı-akşam barı → (COLS çerçevesi, kaynak damgası, TAŞIMA ARIZA NEDENİ|None).

    HACİM: `alpaca_sip` KONSOLİDEDİR ve ham yazılır. `alpaca_iex` tek borsanın hacmidir ve
    ölçülmüş oranla ÇARPILIR; oran yoksa hacim UYDURULMAZ (0 + `volume_scaled: false`).
    Ham kayıt `_ALPACA_PENDING`e konur ve deftere ancak yazım BAŞARILI olursa geçer — yazılmamış
    bir barı 'geçici' diye kaydetmek, olmayan bir satır hakkında hüküm üretmek olurdu.

    ÜÇÜNCÜ ALAN — HATA ≠ BOŞ'UN İKİNCİ DELİĞİ (ROADMAP küçük-kuyruk, 2026-08-02): C20 kardeşi
    yalnız FIRLATAN yolu kapatmıştı. `alpaca.same_evening_bars` ARIZADA FIRLATMAZ ({"source": None,
    "bars": {}} döner), yani taşıma çöktüğünde bu fonksiyon SESSİZCE `(boş çerçeve, None)`
    döndürüyor ve çağıran `outcomes`a `"empty"` yazıyordu — ağ arızası `symbol_unknown` hükmüne,
    oradan `_record_no_data` serisine ve 5. turda "evren bakımı gerekiyor olabilir" alarmına
    dönüşüyordu. Artık ayrımı `_alpaca_session_bars`ın `tasima` sayaçları veriyor: barsızlık ancak
    TEMİZ bir cevabın ardından "empty"dir, aksi hâlde neden ADIYLA yukarı taşınır."""
    from .. import memory
    _tasima: dict = {}
    bar = (_alpaca_session_bars(ticker, session, tasima=_tasima) or {}).get(ticker.upper())
    if not bar or not bar.get("close"):
        return pd.DataFrame(), None, _leg_outcome_reason(_tasima)
    src = bar.get("_source") or ALPACA_SOURCE
    raw_v = float(bar.get("volume") or 0.0)
    if src != ALPACA_SOURCE:
        # KONSOLİDE BASAMAK (sip): hacim zaten tüm piyasadır — ölçekleme SORUSU YOK.
        vol, ratio, scaled = raw_v, None, None
    else:
        ratio = _volume_ratio(ticker)
        vol = float(round(raw_v * ratio)) if (ratio and raw_v > 0) else 0.0
        scaled = bool(ratio and raw_v > 0)
    row = {"date": pd.to_datetime(bar["date"]), "open": bar.get("open"), "high": bar.get("high"),
           "low": bar.get("low"), "close": bar.get("close"), "volume": float(vol)}
    _ALPACA_PENDING.setdefault(ticker.upper(), {})[str(bar["date"])[:10]] = {
        "source": src, "close": float(bar["close"]), "iex_volume": raw_v if scaled is not None else None,
        "volume": float(vol), "ratio": round(ratio, 4) if ratio else None,
        "volume_scaled": scaled, "at": memory.now_iso()}
    return pd.DataFrame([row])[COLS], src, None


def _leg_eligible(ticker: str, end: str, incremental_ok: bool, best: pd.DataFrame) -> str | None:
    """Bacak devreye girsin mi? Girerse hedef seansı döndürür, girmezse None.

    KOŞULLAR (hepsi ZORUNLU): (a) canlı yol açık ve hedef seans ADIYLA verilmiş, (b) hedef seans
    GÜNCEL/yakın (SAME_EVENING_MAX_AGE_DAYS), (c) istenen pencere o seansı kapsıyor, (d) sembolün
    zaten bir geçmişi var (tek bar geçmiş kuramaz — massive kolunun aynı disiplini), (e) mevcut
    kaynaklar o seansı VEREMEDİ (verdiyse bacak gereksizdir; konsolide veri her zaman üstündür)."""
    session = _leg_session()
    if not session or not incremental_ok:
        return None
    from . import alpaca
    if not alpaca.data_available():
        return None
    try:
        s = pd.Timestamp(session)
        if s > pd.Timestamp(end) or (pd.Timestamp(end) - s).days > SAME_EVENING_MAX_AGE_DAYS:
            return None
        if not best.empty and best["date"].max() >= s:
            return None                      # zincir zaten getirdi — KONSOLİDE veri kazanır
    except Exception as e:
        _bar_warn("same_evening_gate_failed", e, ticker=ticker.upper())
        return None
    return session


# ---------------- T+1 otoriter düzeltme: ölçüm + SANCTIONED mutasyon ------------------------------
def _note_dev(session: str, src: str, ticker: str, dev: float, vratio: float | None) -> None:
    """Bir seansın ıraksama defterine TEK ölçüm işle — KAYNAK ADIYLA.

    İKİ ÇAĞIRANI VAR ve bu KASITLIDIR: sip düzelticisi (iex → konsolide sip) ve T+1 massive
    düzeltmesi (→ nihai otorite). "Defter iki kaynağı da ölçer" cümlesinin uygulaması budur.
    Toplamlar (mean/max) GERİYE UYUMLU kalır — dış tüketici (scheduler.status → pano) onları
    okuyor; ayrım `by_source` altında AYRICA birikir, çünkü iex→sip farkı ile sip→massive farkı
    aynı büyüklük DEĞİLDİR ve tek ortalamada eritilirse ikisi de okunamaz hâle gelir."""
    from .. import memory
    sess = _se()["sessions"].setdefault(session, {
        "upgraded": 0, "sum_abs_dev": 0.0, "max_dev": 0.0, "max_dev_ticker": None,
        "n_volume": 0, "sum_volume_ratio": 0.0, "max_volume_ratio": None,
        "sources": {}, "first_at": memory.now_iso()})
    sess["upgraded"] = int(sess.get("upgraded") or 0) + 1
    sess["sum_abs_dev"] = round(float(sess.get("sum_abs_dev") or 0.0) + dev, 8)
    if dev > float(sess.get("max_dev") or 0.0):
        sess["max_dev"], sess["max_dev_ticker"] = round(dev, 6), ticker.upper()
    if vratio:
        sess["n_volume"] = int(sess.get("n_volume") or 0) + 1
        sess["sum_volume_ratio"] = round(float(sess.get("sum_volume_ratio") or 0.0) + vratio, 4)
        if vratio > float(sess.get("max_volume_ratio") or 0.0):
            sess["max_volume_ratio"] = round(vratio, 4)
    sess["sources"][src] = int(sess["sources"].get(src) or 0) + 1
    by = sess.setdefault("by_source", {}).setdefault(
        src, {"n": 0, "sum_abs_dev": 0.0, "max_dev": 0.0, "max_dev_ticker": None})
    by["n"] = int(by.get("n") or 0) + 1
    by["sum_abs_dev"] = round(float(by.get("sum_abs_dev") or 0.0) + dev, 8)
    if dev > float(by.get("max_dev") or 0.0):
        by["max_dev"], by["max_dev_ticker"] = round(dev, 6), ticker.upper()
    sess["last_at"] = memory.now_iso()


def _note_upgrades(ticker: str, merged: pd.DataFrame, fetched: pd.DataFrame, src: str) -> None:
    """Geçici (IEX) bir bar OTORİTER bir kaynakla değiştiyse: ıraksamayı ÖLÇ, hacim oranını yeniden
    kalibre et, geçici damgayı KALDIR. Determinizm kontrolüyle ilişki: bu yol barı DEĞİŞTİRDİĞİ için
    `load_bars` zaten `_changed_rows` → `_bump_wf_rev()` çağırır; yani watchdog `rev_bumped=True`
    görür ve mutasyon SESSİZ değil SANCTIONED'dır. Burada ölçü ve olay eklenir."""
    if src in _LEG_SOURCES:
        return
    prov = _se()["provisional"].get(ticker.upper()) or {}
    if not prov or merged is None or merged.empty or fetched is None or fetched.empty:
        return
    fdates = {str(x)[:10] for x in fetched["date"].astype(str)}
    rows = merged.assign(_d=merged["date"].astype(str).str.slice(0, 10)).set_index("_d")
    for d in sorted(set(prov) & fdates):
        old = prov.get(d) or {}
        if d not in rows.index:
            continue
        try:
            new_close = float(rows.loc[d, "close"])
            new_vol = float(rows.loc[d, "volume"])
            old_close = float(old.get("close") or 0.0)
        except (TypeError, ValueError, KeyError):  # sessiz-yutma: tek satırın biçimi bozuk — damga KALIR, bir sonraki tur yeniden dener (ölçüm uydurulmaz)
            continue
        if old_close <= 0:
            prov.pop(d, None)
            continue
        dev = abs(new_close - old_close) / old_close
        iex_v = float(old.get("iex_volume") or 0.0)
        vratio = (new_vol / iex_v) if (iex_v > 0 and new_vol > 0) else None
        if vratio:                        # (c) SÜREKLİ YENİDEN KALİBRASYON: gerçek oran ölçüldü
            cur = (_se()["volume_ratio"].get(ticker.upper()) or {}).get("samples") or []
            _set_volume_ratio(ticker, list(cur) + [vratio], "t1_upgrade")
        _note_dev(d, src, ticker, dev, vratio)
        prov.pop(d, None)
        _SE_PENDING_EVENT.add(d)
    if not prov:
        _se()["provisional"].pop(ticker.upper(), None)
    _se_touch()


def _emit_upgrade_events() -> None:
    """`bar_source_upgrade` — SEANS BAŞINA TEK satır (sembol başına 250 satır sinyali gömerdi).
    Alanlar: seans, sembol sayısı, ortalama/maks |Δclose|/close ve ölçülen hacim oranı."""
    if not _SE_PENDING_EVENT:
        return
    for d in sorted(_SE_PENDING_EVENT):
        row = (_se()["sessions"].get(d) or {})
        n = int(row.get("upgraded") or 0)
        nv = int(row.get("n_volume") or 0)
        try:
            from .. import obs
            obs.log("bar_source_upgrade", session=d, symbols=n,
                    mean_dev_pct=round(100 * float(row.get("sum_abs_dev") or 0.0) / n, 4) if n else None,
                    max_dev_pct=round(100 * float(row.get("max_dev") or 0.0), 4) if n else None,
                    max_dev_ticker=row.get("max_dev_ticker"),
                    mean_volume_ratio=round(float(row.get("sum_volume_ratio") or 0.0) / nv, 3) if nv else None,
                    sources=",".join(f"{k}:{v}" for k, v in sorted((row.get("sources") or {}).items())),
                    detail="aynı-akşam (IEX) barları otoriter kaynakla DEĞİŞTİRİLDİ — wf revizyonu "
                           "bumplandı (determinizm kontrolü için sessiz mutasyon DEĞİL)")
        except Exception:  # sessiz-yutma: kayıt kanalı düştü — ikinci kanal yok; ölçüm zaten deftere yazıldı
            pass
    _SE_PENDING_EVENT.clear()


def upgrade_divergence(doc: dict | None = None, session: str | None = None) -> dict:
    """AYNI-AKŞAM barı ↔ otoriter (konsolide) bar ıraksamasının OKUNABİLİR hâli. Ölçüm yoksa alanlar None — sıfır DEĞİL
    ("sapma yok" ile "hiç ölçülmedi" farklı iddialardır).

    `doc`: dışarıdan OKUNMUŞ defter. Neden parametre: defterin DIŞ tüketicisi `scheduler.status()`
    ve o okumayı orada yapıyor (codelaw artefakt grafı okuyucuyu ancak `store.read_json` çağrısında
    görebilir — erişimci fonksiyonun ardına gizlenen okuma 'okuyucusu yok' diye işaretlenirdi).
    Şekillendirme yine TEK yerde durur: iki ayrı özetleyici, bu depoda 'aynı yasanın iki uygulaması'
    hatasının ta kendisidir."""
    d0 = doc if isinstance(doc, dict) else _se()
    sess = (d0.get("sessions") or {})
    prov = len(d0.get("provisional") or {})
    if not sess:
        return {"sessions": 0, "last_session": None, "symbols": None, "mean_dev_pct": None,
                "max_dev_pct": None, "max_dev_ticker": None, "mean_volume_ratio": None,
                "by_source": {}, "provisional_tickers": prov}
    d = str(session)[:10] if session else max(sess)
    row = sess.get(d) or {}
    n, nv = int(row.get("upgraded") or 0), int(row.get("n_volume") or 0)
    # KAYNAK AYRIMI (2026-07-30): aynı seansta ARTIK İKİ düzeltici var — sip düzelticisi (iex →
    # konsolide) ve massive (→ nihai otorite). İkisinin sapması aynı büyüklük DEĞİLDİR (biri
    # temsilî↔konsolide farkı, öteki iki konsolide kaynağın farkı); tek ortalamada eritilirse
    # ikisi de okunamaz hâle gelir ve "sip massive ile uyuşuyor mu?" sorusu cevapsız kalır.
    by = {}
    for s, b in sorted((row.get("by_source") or {}).items()):
        bn = int((b or {}).get("n") or 0)
        by[s] = {"symbols": bn or None,
                 "mean_dev_pct": round(100 * float(b.get("sum_abs_dev") or 0.0) / bn, 4) if bn else None,
                 "max_dev_pct": round(100 * float(b.get("max_dev") or 0.0), 4) if bn else None,
                 "max_dev_ticker": b.get("max_dev_ticker")}
    return {"sessions": len(sess), "last_session": d, "symbols": n or None,
            "mean_dev_pct": round(100 * float(row.get("sum_abs_dev") or 0.0) / n, 4) if n else None,
            "max_dev_pct": round(100 * float(row.get("max_dev") or 0.0), 4) if n else None,
            "max_dev_ticker": row.get("max_dev_ticker"),
            "mean_volume_ratio": round(float(row.get("sum_volume_ratio") or 0.0) / nv, 3) if nv else None,
            "by_source": by, "provisional_tickers": prov,
            "note": "IEX barı fiyat için temsilî, hacim için ölçeklenmiş; ertesi gün önce sip "
                    "(konsolide), sonra massive (nihai otorite) ile değiştirilir ve HER İKİ farkı "
                    "burada ölçülür (varsayılmaz)"}


# ---------------- SIP DÜZELTİCİ: ikinci konsolide kaynak, massive'den ÖNCE -----------------------
# NEDEN VAR (tasarım düzeltmesi, 2026-07-30 canlı bulgusu). Aynı akşam sip 403 veriyor ("recent SIP"
# penceresi takvim günü bitene kadar sürüyor) — yani D seansının satırları o akşam KAÇINILMAZ olarak
# temsilî IEX'tir. Eski tasarımda o satırların konsolideye dönmesi TEK BİR kaynağa, Massive grouped'a
# bağlıydı; ve grouped'ın gecikmesi bu turun kök nedeninin ta kendisiydi (canlı kapsama 0,172).
# Sip ertesi gün HAZIRDIR ve grouped'dan bağımsızdır: onu ikinci konsolide kaynak yapmak, tek-kaynak
# bağımlılığını kaldırır. NİHAİ OTORİTE DEĞİŞMEZ — massive geldiğinde satırı yine o yazar (sıra
# iex → sip → massive) ve ıraksama defteri İKİ farkı da ayrı ayrı ölçer (`by_source`).
# KOTA: seans başına evren / DATA_CHUNK kadar çağrı (≈3), Alpaca'nın 200/dk sınırında önemsiz.
SIP_CORRECT_MAX_SESSIONS = 3     # defterdeki EN YENİ K geçici seans (daha eskisi zaten massive'in işi)


def _overwrite_bar(ticker: str, bar: dict) -> bool:
    """VAR OLAN bir tarihin barını konsolide değerlerle DEĞİŞTİR. `_merge_repair_bar`ın TERSİ ve
    tamamlayıcısı: o YALNIZ ekler (var olan tarihe dokunmaz), bu YALNIZ var olanı değiştirir (yeni
    tarih AÇMAZ). İkisi de asla ötekinin işini yapmaz — tek fonksiyona sıkıştırılsaydı "delik
    doldurma" ile "üstüne yazma" aynı çağrıda karışır ve bacak geçmiş kurabilir hâle gelirdi.

    Geçmiş DEĞİŞTİĞİ için wf revizyonu BUMPLANIR (SANCTIONED yol: watchdog `rev_bumped` görür ve
    mutasyonu sessiz saymaz). Hiçbir alan değişmiyorsa yazım da bump da YAPILMAZ."""
    cp = _cache_path(ticker)
    try:
        cached = pd.read_csv(cp, parse_dates=["date"])
    except Exception as e:
        _bar_warn("sip_correct_read_failed", e, ticker=ticker.upper())
        return False
    if cached.empty:
        return False
    d = str(bar.get("date"))[:10]
    mask = cached["date"].astype(str).str.slice(0, 10) == d
    if not mask.any():
        return False               # o tarih diskte YOK — düzeltilecek satır yok (onarım geçidinin işi)
    try:
        close = float(bar.get("close"))
    except (TypeError, ValueError):  # sessiz-yutma: sağlayıcının TEK barı kapanışsız/biçimsiz — kapanışsız satır bar DEĞİLDİR; düzeltme YAPILMAZ ve geçici damga kalır (massive nihai otorite olarak yine dener)
        return False
    if not (close > 0):
        return False
    upd, i, changed = cached.copy(), cached.index[mask][0], False
    for k in ("open", "high", "low", "close", "volume"):
        v = bar.get(k)
        if v is None:
            continue
        try:
            v = float(v)
        except (TypeError, ValueError):  # sessiz-yutma: TEK alanın biçimi bozuk — o alan eski değerinde kalır (uydurma yok)
            continue
        try:
            old = float(upd.at[i, k])
        except (TypeError, ValueError):  # sessiz-yutma: diskteki alan okunamıyor — "değişti" say (muhafazakâr: düzeltme yazılsın)
            old = None
        # GÖRECELİ eşik (`_changed_rows` ile aynı aile): mutlak eşik hacimde 1e-6'yı anlamlı sayıp
        # her turda yeniden yazım tetiklerdi (milyonluk sayılarda kayan-nokta gürültüsü).
        if old is None or abs(v - old) > BAR_EPS * max(abs(old), 1.0):
            changed = True
        upd.at[i, k] = v
    if not changed:
        return True                # satır zaten konsolide değerlerde: damga güncellenir, disk değil
    merged, _rep = sanitize_bars(upd, ticker)
    if len(merged) < len(cached):
        # SATIR KAYBI REDDİ (D3 ikizi): düzeltme geçmişi KISALTAMAZ. Sessiz kalmaz.
        try:
            from .. import obs
            obs.warn("sip_correct_row_loss_refused", ticker=ticker.upper(), session=d,
                     had=int(len(cached)), offered=int(len(merged)),
                     detail="konsolide düzeltme satır düşürüyordu — yazım REDDEDİLDİ, geçici damga kalır")
        except Exception:  # sessiz-yutma: kayıt kanalı düştü; reddin kendisi uygulandı
            pass
        return False
    _write_bars(merged, cp)
    _bump_wf_rev()
    return True


def sip_correct_provisional(tickers: list[str] | None = None,
                            max_sessions: int = SIP_CORRECT_MAX_SESSIONS) -> dict:
    """GEÇMİŞ seansların IEX-damgalı satırlarını KONSOLİDE (sip) barla düzelt — massive'den ÖNCE.

    Hedef seçimi defterden gelir, tahminden değil: `provisional` içindeki YALNIZ `alpaca_iex`
    damgalı ve takvim günü KAPANMIŞ satırlar. Zaten sip'e taşınmış bir satır ikinci kez SORULMAZ.
    Geçici damga KALDIRILMAZ: nihai otorite hâlâ massive'dir ve o geldiğinde `_note_upgrades`
    ikinci farkı ölçmelidir.

    HACİM: sip konsolidedir → ham yazılır ve konsolide/IEX oranı GERÇEK ölçümle tazelenir
    (`sip_correction`). Ölçüm yapıldıktan sonra `iex_volume` defterden DÜŞÜLÜR: aynı IEX hacmini
    bir de massive ile eşleştirmek, tek bir gerçeği iki bağımsız örnek gibi saymak olurdu."""
    from . import alpaca
    out: dict = {"sessions": {}, "targets": 0, "corrected": 0, "asked_sessions": 0,
                 "skipped": None, "at": None}
    if not alpaca.data_available():
        out["skipped"] = "alpaca veri anahtarı yok"
        return out
    only = {str(t).upper() for t in tickers} if tickers else None
    targets: dict[str, list] = {}
    for t, rows in (_se()["provisional"] or {}).items():
        if only and str(t).upper() not in only:
            continue
        for d, rec in (rows or {}).items():
            if (rec or {}).get("source") != ALPACA_SOURCE:
                continue                     # zaten konsolide (sip düzeltilmiş) → ikinci kez sorulmaz
            if not alpaca.sip_allowed(d):
                continue                     # BUGÜNÜN seansı: sip 'recent' sayar, garantili 403
            targets.setdefault(str(d)[:10], []).append(str(t).upper())
    out["targets"] = sum(len(v) for v in targets.values())
    if not targets:
        return out
    _hedef_seans = sorted(targets)[-max(1, int(max_sessions)):]
    for _i_d, d in enumerate(_hedef_seans, 1):
        syms = sorted(set(targets[d]))
        out["asked_sessions"] += 1
        _nabiz("sip_duzeltme:seans", _i_d, len(_hedef_seans))   # v186: sonraki satır ağa çıkar
        got = alpaca.sip_session_bars(syms, d)
        if got is None:
            # HÜKÜM YOK: istek atılamadı/patladı. Damga KALIR, massive nihai otorite olarak bekler.
            out["sessions"][d] = {"asked": len(syms), "corrected": 0, "verdict": "no_answer"}
            continue
        n = 0
        for _i_t, t in enumerate(syms, 1):
            _nabiz("sip_duzeltme:bar", _i_t, len(syms))   # v186: `_overwrite_bar` sembol başına CSV yazar
            if _apply_sip_correction(t, d, got.get(t)):
                n += 1
        out["corrected"] += n
        out["sessions"][d] = {"asked": len(syms), "corrected": n,
                              "verdict": "corrected" if n else "no_rows"}
        if n:
            try:
                from .. import obs
                row = (_se()["sessions"].get(d) or {}).get("by_source", {}).get(ALPACA_SIP_SOURCE) or {}
                bn = int(row.get("n") or 0)
                obs.log("alpaca_sip_correction", session=d, symbols=n, asked=len(syms),
                        mean_dev_pct=round(100 * float(row.get("sum_abs_dev") or 0.0) / bn, 4) if bn else None,
                        max_dev_pct=round(100 * float(row.get("max_dev") or 0.0), 4) if bn else None,
                        max_dev_ticker=row.get("max_dev_ticker"),
                        detail="temsilî (iex) satırlar KONSOLİDE sip barıyla değiştirildi — massive "
                               "NİHAİ otorite olarak beklemede; wf revizyonu bumplandı (sessiz "
                               "mutasyon DEĞİL)")
            except Exception:  # sessiz-yutma: kayıt kanalı düştü; düzeltme zaten diske indi
                pass
    from .. import memory
    out["at"] = memory.now_iso()
    flush_same_evening()
    return out


def _apply_sip_correction(ticker: str, session: str, bar: dict | None) -> bool:
    """Tek sembol/tek seans: konsolide barı diske yaz, ıraksamayı ÖLÇ, hacim oranını tazele.

    SIRA KASITLI: ölçüm ancak satır DİSKE düştükten SONRA deftere geçer — önce ölçüp sonra yazımdan
    vazgeçmek (satır-kaybı reddi), olmayan bir bar hakkında hüküm bırakmak olurdu (`_ALPACA_PENDING`
    ile aynı ders)."""
    rec = (_se()["provisional"].get(ticker.upper()) or {}).get(session)
    if not rec or not bar or rec.get("source") != ALPACA_SOURCE:
        return False
    try:
        new_close = float(bar.get("close"))
        old_close = float(rec.get("close") or 0.0)
    except (TypeError, ValueError):  # sessiz-yutma: tek satırın biçimi bozuk — damga KALIR, massive yine dener (ölçüm uydurulmaz)
        return False
    if not (new_close > 0) or old_close <= 0:
        return False
    if not _overwrite_bar(ticker, {**bar, "date": session}):
        return False
    from .. import memory
    try:
        new_vol = float(bar.get("volume") or 0.0)
    except (TypeError, ValueError):  # sessiz-yutma: hacim alanı bozuk — oran ÖLÇÜLMEZ (0 değil: None)
        new_vol = 0.0
    iex_v = float(rec.get("iex_volume") or 0.0)
    vratio = (new_vol / iex_v) if (iex_v > 0 and new_vol > 0) else None
    if vratio:
        cur = (_se()["volume_ratio"].get(ticker.upper()) or {}).get("samples") or []
        _set_volume_ratio(ticker, list(cur) + [vratio], "sip_correction")
    _note_dev(session, ALPACA_SIP_SOURCE, ticker, abs(new_close - old_close) / old_close, vratio)
    rec.update({"source": ALPACA_SIP_SOURCE, "close": new_close, "volume": new_vol,
                # ÖLÇÜM TÜKETİLDİ: aynı IEX hacmini bir de massive ile eşleştirmek, tek gerçeği iki
                # bağımsız örnek gibi saymak olurdu (medyanı sahte bir güvenle daraltırdı).
                "iex_volume": None, "ratio": None, "volume_scaled": None,
                "at": memory.now_iso()})
    _se_touch()
    return True


# ---------------- hacim kalibrasyonu (bootstrap) --------------------------------------------------
def volume_calibration_stale() -> bool:
    """Kalibrasyon yok ya da bayat mı? (borsa payları kayar; bayat oran sessizce yanlış hacim yazar)"""
    import datetime as _dt
    reg = _se()["volume_ratio"]
    if not reg:
        return True
    ages = []
    for v in reg.values():
        try:
            ages.append((_dt.datetime.now(_dt.timezone.utc)
                         - _dt.datetime.fromisoformat(str(v.get("at")))).days)
        except (TypeError, ValueError):  # sessiz-yutma: damgasız/bozuk satır "yaşı bilinmiyor" — aşağıda muhafazakâr taraf (bayat say)
            return True
    return min(ages) > VOLUME_CAL_MAX_AGE_DAYS if ages else True


def calibrate_volume(tickers: list[str] | None = None, days: int = VOLUME_CAL_DAYS) -> dict:
    """SEMBOL BAŞINA konsolide/IEX hacim oranı: Alpaca IEX günlük barları ile DİSKTEKİ konsolide
    hacimleri aynı-tarih eşleştirip medyan oran. Dağıtımda BİR KEZ; sonra T+1 düzeltmeleri oranı
    kendiliğinden tazeler. Ölçülemeyen sembolde oran YAZILMAZ (None) — varsayılan oran uydurmaktansa
    o sembolün hacmini 0 yazıp muhafazakâr tarafta kalmak doğrudur."""
    import datetime as _dt
    from . import alpaca
    out = {"asked": 0, "calibrated": 0, "unmeasured": [], "days": int(days), "at": None}
    if not alpaca.data_available():
        out["skipped"] = "alpaca veri anahtarı yok"
        return out
    syms = [s.upper() for s in (tickers or ([INDEX_SYMBOL] + list(REPLAY_UNIVERSE)))]
    out["asked"] = len(syms)
    end = _dt.date.today()
    start = end - _dt.timedelta(days=int(days))
    got = alpaca.daily_bars(syms, str(start), str(end))
    if got is None:
        out["skipped"] = "veri ucu isteği başarısız (hüküm yok)"
        return out
    for _i_t, t in enumerate(syms, 1):
        _nabiz("hacim_kalibrasyonu", _i_t, len(syms))   # v186: evren boyu CSV okuması
        rows = got.get(t) or []
        if not rows:
            out["unmeasured"].append(t)
            continue
        cp = _cache_path(t)
        if not cp.exists():
            out["unmeasured"].append(t)
            continue
        try:
            cdf = pd.read_csv(cp, usecols=["date", "volume"])
            cons = {str(d)[:10]: float(v) for d, v in zip(cdf["date"], cdf["volume"]) if v and float(v) > 0}
        except Exception as e:
            _bar_warn("volume_cal_cache_unreadable", e, ticker=t)
            out["unmeasured"].append(t)
            continue
        samples = [cons[b["date"]] / float(b["volume"]) for b in rows
                   if b.get("volume") and float(b["volume"]) > 0 and b.get("date") in cons]
        if len(samples) < VOLUME_CAL_MIN_SAMPLES:
            out["unmeasured"].append(t)
            continue
        if _set_volume_ratio(t, samples, "bootstrap"):
            out["calibrated"] += 1
    from .. import memory
    out["at"] = memory.now_iso()
    flush_same_evening()
    try:
        from .. import obs
        obs.log("alpaca_volume_calibrated", asked=out["asked"], calibrated=out["calibrated"],
                unmeasured=len(out["unmeasured"]), days=int(days),
                sample=",".join(out["unmeasured"][:8]),
                detail="IEX hacmi konsolide DEĞİLDİR; oranı ölçülemeyen sembolde aynı-akşam barının "
                       "hacmi 0 yazılır (uydurma yok) ve hacim türevleri o barda kapanır")
    except Exception:  # sessiz-yutma: kayıt kanalı düştü; ölçüm zaten deftere yazıldı
        pass
    return out


# ---------------- onarım geçidi: son K seansın kapsaması ------------------------------------------
def repair_coverage(tickers: list[str] | None = None, sessions: int = REPAIR_LOOKBACK,
                    min_coverage: float = REPAIR_MIN_COVERAGE) -> dict:
    """Son K seansın kapsamasını DİSKTEN ölç; eksik seansı Massive grouped ile KAPAT.

    NEDEN VAR: eski yol tazelemeyi 8 denemeyle sınırlıyordu ve sonra seans KALICI atlanıyordu —
    onarım geçidi YOKTU. Canlı delik: 2026-07-29 barı 259 sembolün 44'ünde (0,172). Bu yol o deliği
    dağıtımdan sonraki ilk turda kendiliğinden kapatır. MALİYET: eksik seans başına EN ÇOK bir
    grouped çağrısı (snapshot önbelleği + FAIL_COOLDOWN'a saygılı) — günde ≤5."""
    from . import massive
    syms = [s.upper() for s in (tickers or ([INDEX_SYMBOL] + list(REPLAY_UNIVERSE)))]
    have: dict[str, set] = {}
    for _i_s, t in enumerate(syms, 1):
        _nabiz("onarim:kapsama_taramasi", _i_s, len(syms))   # v186: evren boyu CSV okuması
        cp = _cache_path(t)
        if not cp.exists():
            continue
        try:
            have[t] = {str(x)[:10] for x in pd.read_csv(cp, usecols=["date"])["date"]}
        except Exception as e:
            _bar_warn("repair_cache_unreadable", e, ticker=t)
    out = {"universe": len(have), "coverage": {}, "repaired": {}, "grouped_calls": 0,
           "sessions_checked": []}
    if not have:
        return out
    for i in range(max(1, int(sessions))):
        d = massive.last_session(back=i)
        _nabiz("onarim:seans", i + 1, max(1, int(sessions)))   # v186: sonraki satır ağa çıkabilir
        out["sessions_checked"].append(d)
        cov = sum(1 for s in have.values() if d in s) / len(have)
        out["coverage"][d] = round(cov, 3)
        if cov >= min_coverage:
            continue
        snap = massive.snapshot(d)                 # önbellekliyse 0 çağrı; değilse 1
        out["grouped_calls"] += 1
        if not snap:
            out["repaired"][d] = 0
            continue
        n = 0
        for _i_r, (t, dates) in enumerate(have.items(), 1):
            # v186: `_merge_repair_bar` sembol başına CSV okur + sanitize eder + YENİDEN YAZAR —
            # eksik bir seansta bu, evren boyu bir disk süpürmesidir.
            _nabiz("onarim:bar_birlestirme", _i_r, len(have))
            if d in dates:
                continue
            bar = snap.get(t)
            if bar and _merge_repair_bar(t, bar):
                n += 1
        out["repaired"][d] = n
        if n:
            try:
                from .. import obs
                obs.log("bar_coverage_repaired", session=d, filled=n, universe=len(have),
                        coverage_before=round(cov, 3),
                        coverage_after=round((cov * len(have) + n) / len(have), 3),
                        detail="onarım geçidi: eksik seans grouped anlık görüntüsünden kapatıldı")
            except Exception:  # sessiz-yutma: kayıt kanalı düştü; onarımın kendisi diske yazıldı
                pass
    return out


def _merge_repair_bar(ticker: str, bar: dict) -> bool:
    """Eksik seansın barını önbelleğe EKLE. Yalnız EKLEME: var olan hiçbir tarih değiştirilmez.
    GEÇMİŞE eklenen bir bar (delik doldurma) wf revizyonunu BUMPLAR — determinizm yasası 'dosya
    büyümesi zararsızdır' derken SONA eklemeyi kastediyor; ortadaki bir deliğin dolması geçmiş
    pencerelerin sonucunu DEĞİŞTİRİR ve önbelleklenmiş walk-forward'lar artık başka bir seriye aittir."""
    cp = _cache_path(ticker)
    try:
        cached = pd.read_csv(cp, parse_dates=["date"])
    except Exception as e:
        _bar_warn("repair_read_failed", e, ticker=ticker.upper())
        return False
    if cached.empty:
        return False
    d = pd.Timestamp(str(bar.get("date"))[:10])
    if (cached["date"].astype(str).str.slice(0, 10) == str(d.date())).any():
        return False
    row = {"date": d, "open": bar.get("open"), "high": bar.get("high"), "low": bar.get("low"),
           "close": bar.get("close"), "volume": bar.get("volume")}
    if not row["close"]:
        return False
    merged, _ = sanitize_bars(pd.concat([cached, pd.DataFrame([row])[COLS]], ignore_index=True), ticker)
    if len(merged) <= len(cached):
        return False
    interior = d < cached["date"].max()
    _write_bars(merged, cp)
    if interior:
        _bump_wf_rev()
    return True


def fetch(ticker: str, start: str, end: str, timeout: float = 30.0,
          incremental_ok: bool = False) -> pd.DataFrame:
    """[Massive grouped artımlı] → [Massive custom-bars, yalnız ~2 yıl içi] → FMP (when keyed —
    SPLIT-adjusted; dividend DEĞİL) → Cboe (split-adjusted) → Nasdaq.

    Massive kolları yalnız ayarlama ölçeği ölçülüp uyumlu bulunmuşken devrededir (ölçüm çürütülürse
    zincir HARFİYEN eskisi gibi çalışır ve Massive sadece çapraz-doğrulama alarmı üretir). Derin
    tarih (2 yıldan eski `start`) Massive'e HİÇ sorulmaz — orada yarım seri döner ve sessizce kısa
    geçmiş yazmak boş dönmekten çok daha kötüdür.
    FRESHNESS-AWARE: a source that returns data but lags the wanted window does NOT short-circuit the
    chain — the next source may carry the newer session. (Live evidence: FMP serves nothing for ~19
    symbols, Cboe lags one session, and Nasdaq was never tried because 'first non-empty wins' — a third
    of the universe was evaluated one close behind.) A source whose last bar reaches end-1d is accepted
    immediately (no extra network for the healthy majority); otherwise the FRESHEST result wins, earlier
    sources win ties. Empty df if all fail.

    HATA ≠ BOŞ: her kolun sonucu `outcomes` içinde ayrı kaydedilir (error:HTTP 429 / empty /
    empty_after_sanitize / rows:N). Hiçbir kaynak üretmediğinde olayın `verdict` alanı kararı verir —
    `source_error` sembol hakkında HÜKÜM VERMEZ, yalnız `symbol_unknown` evren bakımı adayıdır."""
    from . import fmp, massive
    if massive.available():
        # Mod kaydı YALNIZ anahtar varken: anahtarsız kurulumda Massive zincire hiç girmiyor ve her
        # `fetch` çağrısında "kapali_anahtar_yok" basmak, olmayan bir bileşen hakkında gürültü olurdu
        # (yokluğun kaydı massive._note_no_key'de bir kez tutuluyor — YASA 4 zaten karşılanıyor).
        _log_massive_mode()
    chain = []
    # MASSIVE ARTIMLI KOL — yalnız (a) çağıran bu sembolde tek-günlük bir uzatmanın YETERLİ olduğunu
    # söylediyse (geçmiş zaten var) ve (b) ayarlama ölçeği ÖLÇÜLMÜŞ ve uyumlu bulunduysa. İkisi de
    # doğruysa bu sembol için FMP'ye HİÇ istek atılmaz — kotanın kurtulduğu yer tam olarak burası.
    if incremental_ok and massive.write_enabled():
        chain.append(("massive", lambda: _fetch_massive(ticker, end, timeout)))
    # SEMBOL-BAŞINA YAKIN DÖNEM: Massive ÖNCE, FMP sonra (kota tahsis politikası 2026-07-29 — FMP
    # kotası bilgi katmanına ayrıldı). 2 yıldan eski başlangıç isteyen çağrılar bu kola HİÇ girmez:
    # Massive orada yarım seri döndürür ve sessizce kısa geçmiş yazmak, boş dönmekten çok daha kötüdür.
    if massive.write_enabled() and massive.covers(start):
        chain.append(("massive_hist", lambda: _fetch_massive_hist(ticker, start, end, timeout)))
    if fmp.available() and not fmp.quota_blocked():   # kota dolduysa 250 boş isteği daha atma
        chain.append(("fmp", lambda: _fetch_fmp(ticker, start, end, timeout)))
    chain += [("cboe", lambda: _fetch_cboe(ticker, timeout)),
              ("nasdaq", lambda: _fetch_nasdaq(ticker, start, end, timeout))]
    fresh_enough = pd.Timestamp(end) - pd.Timedelta(days=1)   # ≥ end-1d ⇒ latest plausible session present
    # CANLI KAPI AÇIKSA ÇITA HEDEF SEANSTIR (2026-07-30 — bacağı ÖLÜ DOĞMAKTAN kurtaran satır).
    # `end-1d` toleransı "kaynaklar gecikmeli yayınlar" kabulüydü; ama kapanış AKŞAMINDA end=BUGÜN
    # ve tolerans DÜNü taze sayıyor — yani bir gün geride olan Cboe zinciri ERKEN döndürüyor ve
    # aynı-akşam bacağına sıra HİÇ gelmiyordu. Tam da kapatmaya çalıştığımız delik, kapatma yolunun
    # önünde duruyordu. Kapı KAPALIYKEN (replay/normal yol) davranış HARFİYEN eskisi gibidir.
    _leg_target = _leg_session()
    if _leg_target:
        try:
            fresh_enough = max(fresh_enough, pd.Timestamp(_leg_target))
        except Exception as e:
            _bar_warn("same_evening_target_unparsed", e, target=str(_leg_target))
    best, best_src, tried = pd.DataFrame(), None, []
    outcomes: dict[str, str] = {}                # kaynak → NEDEN üretmedi (hata mı, gerçekten boş mu)
    _LAST_SOURCE.pop(ticker.upper(), None)
    for name, fn in chain:
        try:
            df = fn()
        except FetchError as e:
            tried.append(name)
            outcomes[name] = f"error:{e.reason}"     # İSTEK PATLADI — sembol hakkında hiçbir şey söylemez
            continue
        except Exception as e:
            tried.append(name)
            outcomes[name] = f"error:{type(e).__name__}"
            continue
        if df is None or df.empty:
            tried.append(name)
            # FMP kolu istisnaları kendi içinde yutup [] döner (adapters.fmp.historical_eod); "boş"
            # ile "429" onun için de ayırt edilemezdi. Sağlık kaydından SON DURUMU okuyup ayır.
            outcomes[name] = _empty_reason(name)
            continue
        df = sanitize_bars(df.assign(volume=df["volume"].fillna(0)), ticker)[0]
        if df.empty:
            tried.append(name)
            outcomes[name] = "empty_after_sanitize"  # satır geldi ama hepsi bozuktu — bu da veri arızası
            continue
        outcomes[name] = f"rows:{len(df)}"
        if df["date"].max() >= fresh_enough:
            _LAST_SOURCE[ticker.upper()] = name
            _clear_no_data(ticker.upper())
            _massive_crosscheck(ticker, df, name)     # bedava: anlık görüntü zaten alınmış
            return df
        if best.empty or df["date"].max() > best["date"].max():
            best, best_src = df, name
    # ---- AYNI-AKŞAM BACAĞI (Alpaca IEX) — ZİNCİRİN SONUNDA, YALNIZ AÇIK KALAN SEANS İÇİN ----
    # Konumu KASITLI: zincirin ÖNÜNE konsaydı konsolide veriyi elde varken temsilî IEX barını
    # yazardık. Buraya konunca yalnız "hiçbir kaynak bu seansı veremedi" hâlinde devreye girer —
    # yani boşluğu doldurur, veriyi ele geçirmez. T+1'de otoriter kaynak geldiğinde EZİLİR.
    _leg = _leg_eligible(ticker, end, incremental_ok, best)
    if _leg:
        _leg_src, _leg_err = None, None
        try:
            _leg_res = _fetch_alpaca_session(ticker, _leg)
            # ŞEKİL NORMALİZASYONU (earnings._pair ile AYNI gerekçe): fonksiyon ÜÇLÜ döner
            # (çerçeve, damga, taşıma-arızası). Kayıtlı sahteler — tests/test_denetim_verihatti_v157
            # `lambda t, s: (pd.DataFrame(), None)` — İKİLİ döndürür ve o sözleşme KIRILMAZ: üçüncü
            # alan yoksa "taşıma hakkında ÖLÇÜM YOK" demektir ve eski davranış ("empty") sürer.
            adf, _leg_src = _leg_res[0], _leg_res[1]
            _leg_err = _leg_res[2] if len(_leg_res) > 2 else None
        except Exception as e:
            adf = pd.DataFrame()
            _leg_err = type(e).__name__
            _bar_warn("same_evening_leg_failed", e, ticker=ticker.upper())
        if adf is not None and not adf.empty:
            adf = sanitize_bars(adf.assign(volume=adf["volume"].fillna(0)), ticker)[0]
        if adf is not None and not adf.empty and not best.empty:
            adf = adf[~adf["date"].isin(set(best["date"]))]   # ZİNCİRİN satırı KAZANIR, ezilmez
        if adf is None or adf.empty or not _leg_src:
            # BACAK KOLU DA ZİNCİRİN SÖZLEŞMESİNE TABİDİR (denetim C20 hafif-kardeşi, 2026-08-02):
            # İSTEK PATLADIYSA "empty" YAZILAMAZ. Aşağıdaki hüküm `o.startswith("error")` ile
            # okunuyor; bacak hiçbir zaman `error:` yazmadığı için diğer kolların temiz-boş döndüğü
            # bir turda İSTİSNA `symbol_unknown` hükmüne dönüşüyor, `_record_no_data` serisi artıyor
            # ve 5. turda DATA_QUALITY "evren bakımı gerekiyor olabilir" diyordu — yani ağ arızası
            # "sembol öldü" kanıtına çevriliyordu. Bu, aşağıda uzun uzun anlatılan ve 2026-07-22'de
            # düzeltildiği söylenen hatanın bacaktaki nüshasıydı. Anahtar da damgayı izler:
            # başarıda `outcomes[_leg_src]` yazılıyor, arızada damga HENÜZ YOK → "alpaca".
            #
            # İKİNCİ DELİK DE KAPALI (ROADMAP küçük-kuyruk, 2026-08-02): yukarıdaki `except` YALNIZ
            # FIRLATAN yolu yakalıyordu; `alpaca.same_evening_bars` ise arızada FIRLATMAZ
            # ({"source": None, "bars": {}}). Yani 429/soğuma/kotasızlık hâlinde `_leg_err` None
            # kalıyor ve buraya yine "empty" yazılıyordu — düzeltmenin BEYAN ETTİĞİ sınıf açıktı.
            # Neden artık taşıma sayaçlarından (calls/fails deltası) `_fetch_alpaca_session`
            # üzerinden geliyor; `_leg_err` iki yolu da temsil eder.
            outcomes[_leg_src or "alpaca"] = f"error:{_leg_err}" if _leg_err else "empty"
            _ALPACA_PENDING.pop(ticker.upper(), None)         # yazılmayacak bar 'geçici' sayılmaz
        else:
            outcomes[_leg_src] = f"rows:{len(adf)}"
            _LAST_SOURCE[ticker.upper()] = _leg_src
            _clear_no_data(ticker.upper())
            return (adf if best.empty else
                    pd.concat([best, adf]).sort_values("date").reset_index(drop=True))
    if best_src:
        _LAST_SOURCE[ticker.upper()] = best_src
        _clear_no_data(ticker.upper())
        _massive_crosscheck(ticker, best, best_src)
    elif tried:
        # HİÇBİR kaynak veri vermedi. Eskiden bu tamamen sessizdi: load_bars bayat önbelleği döndürür,
        # motor eski barlarla işlem yapmaya devam ederdi ve hiçbir yerde iz kalmazdı (denetim turu 2).
        #
        # HATA ≠ BOŞ (2026-07-22). Eskiden her kol `except Exception: df = pd.DataFrame()` ile
        # boşluğa çevriliyordu, olay da yalnız "bar_sources_all_empty tried=cboe,nasdaq" diyordu.
        # Operatör bunu okuyup DOĞAL olarak "sembol borsadan düşmüş, evrenden çıkarayım" diye
        # yorumluyor. Canlı kanıt bunun yanlış olduğunu gösterdi: 2026-07-21 16:27–17:15 arası
        # evren sırasında ARDIŞIK 18 sembol (SNAP…ROST) tam olarak birer kez bu olayı bastı ve
        # HEPSİNİN diskteki geçmişi 2026-07-21'e kadar sapasağlam. Yani sebep sembol değil, o
        # penceredeki kısıtlama/throttle idi. Artık kararı olay VERİR:
        #   verdict=source_error   → en az bir kaynak İSTEK hatası verdi; sembol hakkında hüküm YOK
        #   verdict=symbol_unknown → her kaynak DÜZGÜN cevap verip sıfır satır döndü; evren bakımı adayı
        errored = sorted(n for n, o in outcomes.items() if o.startswith("error"))
        verdict = "source_error" if errored else "symbol_unknown"
        streak = _record_no_data(ticker.upper(), verdict, ",".join(tried))
        try:
            from .. import obs
            obs.warn("bar_sources_all_empty", ticker=ticker.upper(), tried=",".join(tried),
                     outcomes=";".join(f"{k}={v}" for k, v in outcomes.items()),
                     verdict=verdict, errored=",".join(errored), streak=streak,
                     detail=("kaynak isteği başarısız — sembol hakkında hüküm YOK, evrenden ÇIKARMA"
                             if verdict == "source_error" else
                             "her kaynak düzgün cevap verip sıfır satır döndü — evren bakımı adayı; "
                             "sayaç: state/" + NO_DATA_FILE))
        except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
            pass
    return best


def _empty_reason(source: str) -> str:
    """Kaynak boş döndü — KENDİ isteği patladığı için mi, yoksa gerçekten satır olmadığı için mi?
    FMP kolu hatayı kendi içinde yutup [] döndürdüğünden tek ipucu sağlık kaydıdır."""
    if source != "fmp":
        return "empty"
    try:
        from . import fmp
        h = fmp.health()
        if h.get("ok") is False and h.get("last_status"):
            return f"error:HTTP {h['last_status']}"
        if h.get("ok") is False:
            return "error:fmp_call_failed"
    except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
        pass
    return "empty"


# ---- VERİSİZ SEMBOL DEFTERİ (2026-07-22) ------------------------------------------------------
# "Hiçbir kaynak satır vermedi" bulgusu tek başına bir SEANSLIK gürültüdür; anlamlı olan ISRARDIR.
# Defter yalnız `symbol_unknown` hükmünü (her kaynak düzgün cevap verip sıfır satır) sayar; ilk
# başarılı çekimde SIFIRLANIR. Evren elle bakımlıdır (loop._universe_drift_check bugün HTTP 403
# yüzünden "unknown" dönüyor) — bu defter, ölü sembol sorusunun İKİNCİ ve bağımsız kanıtıdır.
NO_DATA_FILE = "symbol_no_data.json"
NO_DATA_CONFIRM_STREAK = 5   # bu kadar ARDIŞIK temiz-boş cevaptan sonra operatöre "bak" denir
_NO_DATA: dict = {}


def _no_data_reg() -> dict:
    global _NO_DATA
    if not _NO_DATA:
        from .. import store
        _NO_DATA = store.read_json(NO_DATA_FILE, {}) or {}
    return _NO_DATA


def _record_no_data(ticker: str, verdict: str, tried: str) -> int:
    """Hükmü kaydet, ARDIŞIK `symbol_unknown` serisini döndür. `source_error` seriyi ARTIRMAZ —
    ağ arızasını 'sembol öldü' kanıtına dönüştürmek tam da düzeltilen hatanın kendisiydi."""
    from .. import memory, obs, store
    reg = _no_data_reg()
    prev = reg.get(ticker) or {}
    streak = int(prev.get("streak") or 0) + 1 if verdict == "symbol_unknown" else 0
    now = memory.now_iso()
    reg[ticker] = {"verdict": verdict, "tried": tried, "streak": streak,
                   "first_seen": prev.get("first_seen") or now, "last_seen": now,
                   "last_error_at": now if verdict == "source_error" else prev.get("last_error_at")}
    try:
        store.write_json(NO_DATA_FILE, reg)
    except Exception as e:
        _bar_warn("no_data_ledger_write_failed", e, file=NO_DATA_FILE)
    if streak == NO_DATA_CONFIRM_STREAK:      # bir KEZ — eşiği geçtiği anda; sonrası sayaçta okunur
        obs.alarm("DATA_QUALITY",
                  f"{ticker}: {streak} ardışık turda hiçbir kaynak satır vermedi (istek hatası YOK) "
                  f"— evren bakımı gerekiyor olabilir",
                  ticker=ticker, streak=streak, tried=tried)
    return streak


def _clear_no_data(ticker: str) -> None:
    """Sembol yine veri verdi → seri SIFIRLANIR. Sıfırlamayan bir sayaç, bir kez arızalanan her
    sembolü sonsuza dek 'ölü aday' listesinde tutar ve liste okunmaz hâle gelir."""
    reg = _no_data_reg()
    if ticker in reg:
        reg.pop(ticker, None)
        try:
            from .. import store
            store.write_json(NO_DATA_FILE, reg)
        except Exception as e:
            _bar_warn("no_data_ledger_write_failed", e, file=NO_DATA_FILE)


def no_data_report() -> dict:
    """Evren bakımı için okunabilir özet: hangi semboller ISRARLA veri vermiyor, hangileri yalnız
    kaynak arızası yaşadı. Üretilip tüketilmeyen kanıt bırakmamak için var.

    EMEKLİLİK AYRIMI (2026-07-30): defterdeki her kayıt artık emekli mi diye SORULUR. Emekli bir
    sembolün (`RETIRED_SYMBOLS`) veri vermemesi bir BULGU değil, beklenen sonuçtur — hükmü zaten
    verilmiştir. Onu `confirmed_no_data` içinde bırakmak, kapanmış bir dosyayı her turda yeniden
    "evren bakımı adayı" diye açmak olurdu; operatör aynı sekiz ismi sonsuza dek incelerdi. Bu
    yüzden emekliler aday listelerinden DÜŞÜLÜR ama SİLİNMEZ: kendi `retired` listelerinde adıyla
    durur, çünkü ölü bir sembolün hâlâ fetch edilmeye çalışılması ayrı ve gerçek bir bulgudur."""
    reg = _no_data_reg()
    retired = sorted(t for t in reg if is_retired(t))
    dead = sorted(t for t, v in reg.items()
                  if int(v.get("streak") or 0) >= NO_DATA_CONFIRM_STREAK and not is_retired(t))
    suspect = sorted(t for t, v in reg.items()
                     if 0 < int(v.get("streak") or 0) < NO_DATA_CONFIRM_STREAK and not is_retired(t))
    errored = sorted(t for t, v in reg.items() if v.get("verdict") == "source_error")
    return {"tracked": len(reg), "confirmed_no_data": dead, "suspect": suspect,
            "source_error_only": errored, "retired": retired,
            "confirm_streak": NO_DATA_CONFIRM_STREAK,
            "note": "confirmed_no_data = her kaynak DÜZGÜN cevap verip sıfır satır döndü "
                    "(ardışık); source_error_only = istek patladı, sembol hakkında hüküm YOK; "
                    "retired = delist hükmü ZATEN verilmiş, bakım adayı DEĞİL"}


def load_bars(ticker: str, start: str, end: str, use_cache: bool = True, polite_delay: float = 0.1) -> pd.DataFrame:
    """Load daily bars for [start, end]. Uses the cache when fresh; otherwise fetches and MERGES with
    the cache (union by date) rather than blindly overwriting."""
    cp = _cache_path(ticker)
    cached, cached_raw_rows, _gate_dropped = None, 0, 0
    if cp.exists():
        # ALWAYS read the disk cache — even under use_cache=False. use_cache=False means "don't TRUST
        # freshness, force a network fetch"; it must still merge with disk, run the corporate-action
        # check, and fall back to the cache when all sources fail (blindly overwriting the cache and
        # returning empty on a transient outage was audit #45/#42).
        _raw = pd.read_csv(cp, parse_dates=["date"])
        cached_raw_rows = len(_raw)
        cached, _rep = sanitize_bars(_raw, ticker)         # repair any legacy glitch on read
        # KAPININ DÜŞÜRDÜĞÜ SATIR "KAYIP" DEĞİLDİR (2026-07-30). Aşağıdaki D3 monotonluk koruması
        # DİSKTEKİ ham satır sayısıyla kıyaslar ve haklı olarak öyle yapar (kaybın gerçek yolu
        # sanitize'ın düşürdüğü satırların geri yazılmasıydı). Ama takvim kapısı SAYILI, OLAYLI ve
        # KASITLI bir düşüştür: baz ondan arındırılmazsa her tur `bar_row_loss_refused` basar,
        # yazım reddedilir ve hayalet satır DİSKTE sonsuza dek yaşar — yani düzeltme, kendi
        # korumasının önünde durur. Diğer sanitize düşüşleri baza AYNEN dahil kalır.
        _gate_dropped = (int(_rep.get("ghost_session_dropped") or 0)
                         + int(_rep.get("unadjusted_quarantined") or 0))
        cached_raw_rows -= _gate_dropped
        _red = _CAL_MISMATCH.get(ticker.upper()) if _rep.get("calendar_mismatch_rows") else None
        if _red:
            # DİSKTEKİ bir defterin takvimi tutmuyorsa bu KALICI bir durumdur ve duyurulur (ara
            # çerçevelerin aksine — orada yalnız sayılır). Sembol başına bir kez.
            _note_cal_mismatch(ticker.upper(), _red)
        if _rep:
            # ONARIM SESSİZDİ: sanitize satır DÜŞÜREBİLİR ve onarılmış hâl sonra diske geri yazılırdı —
            # yani okuma yolu, kimseye söylemeden kalıcı veri siliyordu (denetim turu 2).
            try:
                from .. import obs
                obs.warn("bar_cache_repaired", ticker=ticker.upper(), **{k: int(v) for k, v in _rep.items()})
            except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
                pass
    if use_cache and cached is not None and not cached.empty:
        # Freshness = RECENCY only. The old min-date condition (cache must reach FETCH_START+7d) was
        # permanently unsatisfiable for sources whose history window doesn't reach that far back — those
        # caches were bypassed and re-downloaded on EVERY load for nothing (audit #43). Short warmup
        # coverage is telemetry, not a refetch trigger (refetching cannot conjure older data).
        if cached["date"].min() > pd.Timestamp(start) + pd.Timedelta(days=7) \
                and ticker.upper() not in _WARMUP_WARNED:
            _WARMUP_WARNED.add(ticker.upper())
            try:
                from .. import obs
                from ..indicators import TREND_TEMPLATE_WARMUP as _tt_warm
                # BULGU EYLEME BAĞLANDI (2026-07-22): olay eskiden yalnız "ilk bar geç" diyordu ve
                # hiçbir tüketicisi yoktu. Asıl soru "motor bu sembolde gösterge hesaplıyor mu?"dur.
                # Cevap artık indicators.trend_template içinde: ısınma dolmadan NaN döner ve dört
                # kurulumun `pd.isna(tt)` koruması sembolü dışlar. Olay, o eşiği ölçüyle söyler.
                obs.warn("warmup_coverage_short", ticker=ticker,
                         first_bar=str(cached["date"].min().date()), wanted_start=start,
                         bars=int(len(cached)), warmup_needed=int(_tt_warm),
                         indicators_trustworthy=bool(len(cached) >= _tt_warm),
                         detail="kaynak bundan eskisini taşımıyor — yeniden çekmek eski barı YARATMAZ; "
                                "ısınma dolmayan barlarda trend şablonu NaN döner (sembol dışlanır)")
            except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
                pass
        if cached["date"].max() >= pd.Timestamp(end) - pd.Timedelta(days=FRESH_DAYS):
            return _window(cached, start, end)
    corp_reset = False
    # ARTIMLI YETERLİ Mİ? Massive tek-günlük bar döndürür; bunun ANLAMLI olabilmesi için sembolün
    # diskte zaten sağlam bir geçmişi olmalı. Geçmişi yoksa (yeni sembol, kısa önbellek) tek bar bir
    # geçmiş kuramaz — o durumda derin backfill FMP'nin işidir ve Massive kolu zincire hiç girmez.
    incremental_ok = bool(cached is not None and len(cached) >= MIN_INCREMENTAL_BARS)
    fetched = fetch(ticker, start, end, incremental_ok=incremental_ok)
    if fetched.empty:
        return _window(cached, start, end) if cached is not None else pd.DataFrame()
    src = _LAST_SOURCE.get(ticker.upper())
    # ---- ARTIMLI KAYNAK GEÇMİŞİ SIFIRLAYAMAZ (2026-07-29) ----
    # Aşağıdaki kurumsal-aksiyon yolu `fetched`in TAM GEÇMİŞ olduğunu VARSAYAR: önbelleği atar ve
    # yerine YALNIZ `fetched`i yazar. Massive TEK BAR döndürür — o varsayımla birleşirse bir bölünme
    # şüphesi, sembolün tüm geçmişini tek satıra indirir (ve corp_reset istisnası yüzünden satır-kaybı
    # koruması da devreye girmez). Bu yüzden şüphe artımlı bir bardan doğduğunda karar VERİLMEZ:
    # artımlı kol kapatılıp derin kaynaktan tam çekim yapılır ve hüküm ONUN üstünde yeniden kurulur.
    if cached is not None and not cached.empty and src in _NON_OWNING and _corporate_action(cached, fetched):
        try:
            from .. import obs
            obs.warn("massive_corp_action_escalated", ticker=ticker.upper(),
                     detail="artımlı tek bar bölünme/ölçek şüphesi doğurdu — geçmişi TEK BARA "
                            "indirmemek için artımlı kol kapatıldı, derin kaynaktan tam çekim yapılıyor")
        except Exception:  # sessiz-yutma: kayıt kanalı düştü; yükseltmenin kendisi yine de yapılır
            pass
        fetched = fetch(ticker, start, end, incremental_ok=False)
        src = _LAST_SOURCE.get(ticker.upper())
        if fetched.empty:
            return _window(cached, start, end)     # derin kaynak da veremedi → geçmişe DOKUNMA
    # CORPORATE-ACTION DEFENSE (Phase 2): FMP `/full` returns SPLIT-adjusted history (dividend-adjusted DEĞİL),
    # so a SPLIT re-adjusts the whole series (dividend'ler split-only seriyi kaydırmaz — yakalanacak bir şey yok).
    # If an overlapping date's adjusted close now diverges from the
    # cached close by > CORP_ACTION_PCT, the cache is on the OLD adjustment scale — splicing the two scales
    # would manufacture a fake overnight crash that destroys every moving average and fires fatal false
    # signals. Discard the stale-scale cache and keep ONLY the fresh, fully-adjusted fetch (that IS the full
    # historical refetch). A legitimate big price move does NOT trigger this — it is identical in both. Same
    # FMP→Cboe→Nasdaq fallback + polite_delay as any refetch.
    if cached is not None and not cached.empty and _corporate_action(cached, fetched):
        try:
            from .. import obs
            obs.log("corporate_action_cache_reset", ticker=ticker)
        except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
            pass
        # DOSYAYI SİLMİYORUZ (2026-07-22 — canlı `index_bars_invalid {"issues": ["empty"]}` kökü).
        # Eskiden burada `cp.unlink()` vardı: dosya SİLİNİYOR, yeni hâli ancak ~40 satır sonra
        # `_write_bars` ile yazılıyordu. Aradaki pencerede önbellek DİSKTE YOKTU ve o anda okuyan
        # herkes (havuz işçilerinin dataset.load_cached'i, ikinci bir sürecin load_bars'ı)
        # `cp.exists() == False` görüyordu; kaynaklar da kısıtlıysa (o gün 429 seliydi) sonuç BOŞ
        # seri oluyordu. SPY için bunun karşılığı doğrudan "endeks boş" — yani rejim sınıflamasının
        # dayanağının yok olması. `_write_bars` zaten mkstemp+os.replace ile ATOMİK: eski hâli yeni
        # hâlle tek adımda değiştirir, okuyucu ya birini ya diğerini görür, asla YOKLUĞU görmez.
        # `cached = None` zaten "bayat ölçekli geçmişi kullanma" demek için yeterli — silmek fazladan
        # bir şey kazandırmıyor, süreç iki adım arasında ölürse geçmişi KALICI olarak kaybettiriyordu.
        corp_reset = True
        # KRİTİK (2026-07-21'de canlıda bulundu): bu satır BARLARI değiştirir — önbelleklenmiş her
        # walk-forward artık ARTIK VAR OLMAYAN barlar üzerinde hesaplanmıştır. Revizyon bumplanmazsa
        # kapı, BAYAT-bar incumbent'ını TAZE-bar candidate'ıyla kıyaslar (elma-armut) ve kararı geçersiz
        # olur. Canlı kanıt: aynı v4 incumbent'ı 0.2043 → 0.1130 → 0.0988 sürüklendi. Aynı koruma
        # windows ve seans-tazelemesi için zaten vardı; corporate-action yolu atlanmıştı.
        # reflect'i import ETMEYİZ (döngü riski) — revizyon sayacını doğrudan artırırız.
        _bump_wf_rev()
        cached = None

    pinned = _bar_source(ticker)
    _prov = _provisional_dates(ticker)
    # ---- AYNI-AKŞAM BACAĞI GEÇMİŞE YAZAMAZ (2026-07-30) ----
    # IEX barı TEMSİLÎDİR (tek borsanın işlemleri) ve hacmi ölçeklenmiştir. Zincirin sabitlenmiş
    # sahibi yoksa (pinned is None) aşağıdaki dikiş kuralı hiç çalışmaz ve keep="last" ile bir IEX
    # satırı, önbellekteki KONSOLİDE bir barı sessizce ezebilirdi — düzeltmenin TERSİ yönde bir
    # gerileme. Kural açıkça yazılır: yalnız önbelleğin son barından SONRASI, ya da bu bacağın
    # KENDİ yazdığı geçici barın tazelenmesi.
    if src in _LEG_SOURCES and cached is not None and not cached.empty:
        _fd = fetched["date"].astype(str).str.slice(0, 10)
        fetched = fetched[(fetched["date"] > cached["date"].max()) | _fd.isin(_prov)]
        if fetched.empty:
            return _window(cached, start, end)
    # ---- D1: KAYNAK-ÖLÇEĞİ DİKİŞİ (denetim turu 2, 2026-07-21 — canlıda yakalandı) ----
    # FMP tam TEMETTÜ+bölünme düzeltmeli seri döner; Cboe yalnız bölünme düzeltmelidir. FMP kotası
    # dolunca (bugün: 429 — 250 ticker'lık tazeleme günlük kotanın tamamını yakıyor) zincir Cboe'ye
    # düşer ve Cboe DE tam geçmiş döndürdüğü için keep="last" TÜM geçmişi başka bir düzeltme ölçeğine
    # çevirir. Temettü farkı tipik olarak %1-15 — corporate-action eşiğinin (%25) ALTINDA, yani ne
    # sıfırlama ne revizyon bumpı olur: kapı bayat-bar incumbent'ını taze-bar candidate'ıyla kıyaslar.
    # KURAL: geçmişi TEK kaynak sahiplenir; farklı bir kaynak yalnız YENİ tarihleri EKLEYEBİLİR.
    if (cached is not None and not cached.empty and src and pinned and src != pinned):
        # T+1 DÜZELTME KAPISI (2026-07-30): "yalnız YENİ tarih" kuralı, aynı-akşam bacağının yazdığı
        # GEÇİCİ barı da dokunulmaz yapardı — yani IEX satırı sonsuza dek kalır ve düzeltme
        # YAPISAL olarak imkânsız olurdu. Geçici tarihler kuralın BİLİNÇLİ istisnasıdır: o satırın
        # sahibi zaten hiçbir zaman bu bacak değildi (defter onu 'provisional' diye kaydetti).
        _fd2 = fetched["date"].astype(str).str.slice(0, 10)
        newer = fetched[(fetched["date"] > cached["date"].max()) | _fd2.isin(_prov)]
        # MASSIVE İSTİSNASI (2026-07-29): dikiş defteri "geçmişi ARTIK YAYIN YAPMAYAN bir kaynak
        # sahipleniyor" ANOMALİSİNİ sayar. Massive ise TASARIMI GEREĞİ yalnız yeni tarih ekler —
        # geçmişi hiç talep etmez. Onu deftere yazmak, 251 sembolün hepsini tek seferde "dikişli"
        # göstererek defteri okunmaz hâle getirirdi (canlı dağılım: cboe 192 + nasdaq 59, fmp 0 —
        # yani Massive açıldığı gün HER sembol dikiş sayılırdı). Ekleme-yalnız kısıtı AYNEN uygulanır;
        # kaydedilmeyen tek şey, anomali OLMAYAN bir durumun anomali defterine düşmesidir.
        if src not in _NON_OWNING:
            _record_seam(ticker.upper(), pinned, src, int(len(newer)))
        fetched = newer                                  # geçmişe DOKUNMA, yalnız uzat
        if fetched.empty:
            return _window(cached, start, end)
    # keep="last": on a duplicate date the freshly-FETCHED bar wins over the cached one, so a retroactive
    # split-adjustment or source correction replaces the stale bar instead of being silently dropped
    # (keep="first" kept `cached` and poisoned every downstream indicator across the split date).
    merged = fetched if cached is None else (pd.concat([cached, fetched]).drop_duplicates("date", keep="last")
                                             .sort_values("date").reset_index(drop=True))
    # ---- D3: MONOTONLUK — bar geçmişi kısalamaz ----
    # Salt-ekleme dışında bir yazım satır SAYISINI düşürüyorsa bu düzeltme değil KAYIPTIR (kırpılmış
    # indirme, dar pencereli fallback, yarım okuma). Corporate-action sıfırlaması bilinçli istisnadır.
    # NOT: karşılaştırma DİSKTEKİ ham satır sayısıyla yapılır, sanitize edilmiş kopyayla değil —
    # kaybın gerçek yolu tam da sanitize'ın düşürdüğü satırların geri yazılmasıydı.
    if cached is not None and not corp_reset and len(merged) < cached_raw_rows:
        try:
            from .. import obs
            obs.warn("bar_row_loss_refused", ticker=ticker.upper(), had=int(cached_raw_rows),
                     offered=int(len(merged)))
        except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
            pass
        return _window(cached, start, end)
    # ---- D1b: geçmiş DEĞİŞTİYSE revizyonu bumpla (salt ekleme masumdur) ----
    # HAYALET SATIRIN SİLİNMESİ DE BİR GEÇMİŞ DEĞİŞİMİDİR (2026-07-30): `_changed_rows` yalnız
    # ÖRTÜŞEN tarihlerin kapanışını kıyaslar — silinen bir tarih orada hiç görünmez. Bump olmadan
    # dosya küçülür ve watchdog.determinism_report bunu haklı olarak "SESSİZ BAR MUTASYONU" sayar;
    # ayrıca o hayalet bardan geçen önbelleklenmiş walk-forward'lar gerçekten geçersizdir.
    if _gate_dropped:
        _bump_wf_rev()
    if cached is not None and not cached.empty:
        n_ch, worst = _changed_rows(cached, merged)
        if n_ch:
            _bump_wf_rev()
            try:
                from .. import obs
                obs.log("bar_history_rewritten", ticker=ticker.upper(), source=src or "?",
                        changed=n_ch, max_pct=round(worst * 100, 3))
            except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
                pass
    _write_bars(merged, cp)                              # D4: atomik (yarım CSV okunamaz)
    # ---- YAZIM BAŞARILI: geçici damga KONUR ya da KALKAR ----
    # Sıra kasıtlı: damga ancak satır DİSKE düştükten sonra anlamlıdır. Önce damgalayıp sonra
    # yazımdan vazgeçmek (satır-kaybı reddi, boş fetched) defterde OLMAYAN bir bar hakkında hüküm
    # bırakırdı — ve T+1 düzeltmesi o hayalet satırla ıraksama ölçerdi.
    if src in _LEG_SOURCES:
        _kalan = {d: v for d, v in (_ALPACA_PENDING.pop(ticker.upper(), {}) or {}).items()
                  if d in set(merged["date"].astype(str).str.slice(0, 10))}
        _note_provisional(ticker, _kalan)
    else:
        _ALPACA_PENDING.pop(ticker.upper(), None)
        _note_upgrades(ticker, merged, fetched, src or "?")
    # SAHİPLİK ARTIMLI KAYNAĞA GEÇMEZ (2026-07-29): sabitleme "bu geçmişi kim YAZDI" sorusunun
    # cevabıdır ve ölçek dikişi kararı buna dayanır. Massive tek bar ekler — geçmişi o yazmadı.
    # Sahipliği ona vermek, gerçek sahibi (Cboe/Nasdaq) bir gün geri geldiğinde onu "yabancı kaynak"
    # sayıp geçmişi uzatmasını engellerdi. Massive her zaman EKLEYENDİR, sahip değil.
    # AYNI-AKŞAM BACAĞI DA EKLEYENDİR (2026-07-30): tek bir temsilî bar geçmişin sahibi olamaz ve
    # zaten T+1'de kendisi EZİLİYOR — sahiplenmesi, ertesi gün gerçek sahibi dikiş sayardı.
    if src and src not in _NON_OWNING and (corp_reset or pinned is None):
        _pin_source(ticker, src)                         # geçmişin sahibi: onu yazan kaynak
    time.sleep(polite_delay)
    return _window(merged, start, end)


def _corporate_action(cached: pd.DataFrame, fetched: pd.DataFrame) -> bool:
    """True if the fresh (fully-adjusted) fetch re-adjusted the historical series vs the cache — the tell of a
    split/dividend since the cache was written. Compares OVERLAPPING dates' adjusted closes; a legitimate big
    price move is identical in both and does NOT trigger (avoids false positives on earnings gaps)."""
    try:
        m = cached[["date", "close"]].merge(fetched[["date", "close"]], on="date", suffixes=("_c", "_f"))
        if m.empty:
            # DISJOINT ranges (stale cache + a narrow windowed fallback fetch): no overlap to diff, but a
            # seam between two adjustment scales is exactly what must not be spliced (audit #48). Check
            # boundary continuity with a DOUBLE threshold so a legitimate gap between the ranges never
            # false-positives — only a catastrophic scale jump (>±50%) flags.
            a, b = (cached, fetched) if cached["date"].max() < fetched["date"].min() else \
                   ((fetched, cached) if fetched["date"].max() < cached["date"].min() else (None, None))
            if a is None:
                return False
            last_a = float(a.sort_values("date")["close"].iloc[-1])
            first_b = float(b.sort_values("date")["close"].iloc[0])
            if last_a <= 0:
                return False
            r = first_b / last_a
            return bool(r > 1 + 2 * CORP_ACTION_PCT or r < 1 - 2 * CORP_ACTION_PCT)
        c, f = m["close_c"].astype(float), m["close_f"].astype(float)
        ratio = (f / c).where(c > 0).dropna()
        if ratio.empty:
            return False
        return bool(((ratio > 1 + CORP_ACTION_PCT) | (ratio < 1 - CORP_ACTION_PCT)).any())
    except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
        return False



# ---- KAYNAK DİKİŞİ DEFTERİ (2026-07-22) -------------------------------------------------------
# Dikiş koruması DOĞRU çalışıyor ama her sembolde HER tazelemede uyarı basıyordu: 250 satır × her tur.
# Sonuç, susturmaktan beter bir şeydi — gerçek uyarılar bu gürültünün içinde görünmez oluyordu.
# Ama sessizce yok saymak da olmaz: dikiş, geçmişin ARTIK YAYIN YAPMAYAN bir kaynağa ait olduğu
# anlamına gelir ve bu kalıcı bir durumdur. Kural: DURUM bir kez kaydedilir ve bir kez uyarılır;
# tekrarlar sayılır ve `seam_report()` ile okunabilir kalır (üretilip tüketilmeyen kanıt olmasın).
SEAM_FILE = "bar_source_seams.json"
_SEAMS: dict = {}          # süreç-içi ayna; None = henüz diskten okunmadı
_SEAM_DIRTY = 0
_SEAM_FLUSH_EVERY = 25     # 250'lik tazelemede ~10 yazım (her sembolde bir değil)


def _seams() -> dict:
    global _SEAMS
    if not _SEAMS:
        from .. import store
        _SEAMS = store.read_json(SEAM_FILE, {}) or {}
    return _SEAMS


def flush_seams() -> None:
    """Dikiş defterini diske yaz. Yeni bir dikişte ve her _SEAM_FLUSH_EVERY tekrarda çağrılır."""
    global _SEAM_DIRTY
    from .. import store
    store.write_json(SEAM_FILE, _SEAMS)
    _SEAM_DIRTY = 0


def _record_seam(ticker: str, pinned: str, offered: str, appended: int) -> None:
    """Dikişi kaydet; YALNIZ yeni bir durum belirdiğinde uyar."""
    global _SEAM_DIRTY
    from .. import memory, obs
    reg = _seams()
    prev = reg.get(ticker) or {}
    yeni = (prev.get("pinned") != pinned) or (prev.get("offered") != offered)
    now = memory.now_iso()
    reg[ticker] = {"pinned": pinned, "offered": offered,
                   "first_seen": prev.get("first_seen") or now, "last_seen": now,
                   "n": int(prev.get("n") or 0) + 1,
                   "appended_last": int(appended)}
    if yeni:
        # DURUM DEĞİŞTİ (ilk kez ya da kaynak değişti) — bu bir bulgudur, bir kez söylenir.
        obs.warn("bar_source_seam_opened", ticker=ticker, pinned=pinned, offered=offered,
                 appended=appended,
                 detail="geçmişi sabitlenmiş kaynak sahipleniyor; yeni kaynak YALNIZ yeni tarihleri "
                        "ekleyebilir. Tekrarlar susturuldu — sayaç: state/" + SEAM_FILE)
        flush_seams()
    else:
        _SEAM_DIRTY += 1
        if _SEAM_DIRTY >= _SEAM_FLUSH_EVERY:
            flush_seams()


def seam_report() -> dict:
    """Kaç sembolün geçmişi, artık yayın yapmayan bir kaynağa sabitli? Susturulan uyarının
    TOPLAMI burada okunur — pano ve teşhis ucu buradan besleniyor."""
    reg = _seams()
    by_pair: dict = {}
    for t, v in reg.items():
        k = f"{v.get('pinned')}→{v.get('offered')}"
        by_pair.setdefault(k, []).append(t)
    return {"tickers": len(reg), "by_pair": {k: len(v) for k, v in by_pair.items()},
            "sample": {k: sorted(v)[:5] for k, v in by_pair.items()},
            "oldest": min((v.get("first_seen") or "") for v in reg.values()) if reg else None,
            "note": "geçmişi sabit kaynağa ait; yeni kaynak yalnız yeni tarih ekler (ölçek karışmaz)"}


def _window(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    if df is None or df.empty:
        return df if df is not None else pd.DataFrame()
    m = (df["date"] >= pd.Timestamp(start)) & (df["date"] <= pd.Timestamp(end))
    return df.loc[m].reset_index(drop=True)


def load_many(tickers: list[str], start: str, end: str, use_cache: bool = True) -> dict[str, pd.DataFrame]:
    """Load bars and DROP any ticker whose data fails the hard integrity gate (never trade on bad data)."""
    out: dict[str, pd.DataFrame] = {}
    failed, quarantined = [], []
    _n_uni = len(tickers)
    for _i_t, t in enumerate(tickers, 1):
        # v186 NABIZ NOKTASI #1 (turun en uzunu): sembol başına tam zincir (massive → fmp → cboe →
        # nasdaq → aynı-akşam bacağı) + hayalet süpürmesi + CSV yazımı. 2026-08-03 akşamı bekçiyi
        # üç kez ateşleyen blok BURASIYDI (408 sembol, 367 satırlık onarım kuyruğu).
        _nabiz("bar_yukleme", _i_t, _n_uni)
        try:
            df = load_bars(t, start, end, use_cache=use_cache)
        except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
            df = pd.DataFrame()
        if df is None or len(df) <= 50:
            failed.append(t)
            continue
        ok, issues = validate_bars(df, t)
        if not ok:
            quarantined.append((t, [i["code"] for i in issues if i["severity"] == "hard"]))
            continue
        out[t] = df
    if failed:
        print(f"[data] {len(out)} loaded, {len(failed)} unavailable: {', '.join(failed[:12])}"
              + (" ..." if len(failed) > 12 else ""))
    if quarantined:
        print(f"[data] QUARANTINED {len(quarantined)} on integrity failure: "
              + ", ".join(f'{t}({",".join(c)})' for t, c in quarantined[:8]))
    # D5 KORUNUM (denetim turu 2): evrenden düşen ticker'lar yalnız STDOUT'a yazılıyordu — olay
    # defterinde iz yoktu. Evren 250'den 180'e insin, hiçbir kayıtta görünmezdi. Artık kayıtlı.
    # TUR SONU: aynı-akşam defteri diske iner ve biriken ıraksama olayı SEANS BAŞINA tek satır
    # olarak duyurulur (eşik-tabanlı flush turun ortasında kalmasın diye — 250 sembolde defterin
    # son %10'u aksi hâlde yalnız bellekte kalırdı).
    flush_same_evening()
    _emit_ghost_round()               # hayalet/karantina toplamı: tur sonunda TEK satır
    if failed or quarantined:
        try:
            from .. import obs
            obs.warn("universe_shrunk", loaded=len(out), wanted=len(tickers),
                     unavailable=",".join(failed[:20]),
                     quarantined=",".join(t for t, _ in quarantined[:20]))
        except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
            pass
    return out


REPLAY_UNIVERSE = [
    # leaders (kept)
    "AAPL", "MSFT", "NVDA", "AVGO", "AMD", "CRM", "ADBE", "ORCL", "GOOGL", "META", "NFLX",
    "AMZN", "TSLA", "HD", "NKE", "MCD", "SBUX", "COST", "LOW",
    "JPM", "BAC", "GS", "V", "MA", "AXP",
    "UNH", "LLY", "JNJ", "ABBV", "MRK",
    "CAT", "DE", "BA", "XOM", "CVX", "LIN", "GE", "HON",
    "PG", "KO", "WMT", "PEP",
    # laggards / dispersers 2022–2025 — real S&P names that fell or went sideways. Including them fixes
    # the survivorship bias: the learning gate now tunes against losers too, not only today's winners.
    "INTC", "PYPL", "DIS", "T", "EA", "PFE", "ENPH", "MRNA", "MMM", "HRL", "VFC", "F",
    # #1 EVREN GENİŞLEMESİ (2026-07-20, operatör kararı: 250 likit hisse) — tüm kanıt motorları
    # (karşı-olgusal defter, gölge/skor/LLM kalibrasyonu, EP ölçümü) evrenle DOĞRUSAL ölçeklenir.
    # Sektör-dengeli S&P büyük/orta boy likit isimler; her birinin backtest.SECTORS'ta etiketi var
    # (test-zorlamalı). Geçiş günü RS yüzdelik dağılımı kayar — deftere obs ile işaretlenir.
    # Yukarıdaki 250, 2026-07-20 kararının tarihsel kaydıdır; evren 2026-07-30'da FISV ile 251 oldu.
    # genişleme · comms (14)
    "GOOG", "CMCSA", "TMUS", "VZ", "CHTR", "WBD", "OMC", "TTWO", "MTCH", "PINS", "SNAP", "SPOT",
    "ROKU", "LYV",
    # genişleme · consumer (20)
    "BKNG", "MAR", "HLT", "RCL", "CCL", "NCLH", "DAL", "UAL", "LUV", "EXPE", "ORLY", "AZO",
    "TJX", "ROST", "BURL", "DG", "DLTR", "TGT", "LULU", "DECK",
    # genişleme · energy (17)
    "COP", "EOG", "SLB", "HAL", "BKR", "OXY", "PSX", "VLO", "MPC", "DVN", "FANG", "EQT",
    "WMB", "KMI", "OKE", "LNG", "TRGP",
    # genişleme · financials (21)
    "WFC", "C", "MS", "SCHW", "BLK", "BX", "KKR", "APO", "CB", "PGR", "TRV", "ALL",
    "MET", "PRU", "AFL", "AIG", "COF", "PNC", "SYF", "USB",
    # FISV (2026-07-30, operatör kararı) — emekli FI'nin halefi (2025-11-11 NYSE delist, borsa
    # transferi; şirket Nasdaq'ta sürüyor). Sağlayıcı geçmişi 2025-11-11'de BAŞLAR: FI dönemi geriye
    # birleştirilmemiş, yeni kimlik olarak servis ediliyor. Yani seri gençtir (~178 bar) ve pencere
    # isteyen göstergeler dolana dek bu sembol kısıtlı görünür — bu bir arıza DEĞİL, olmayan geçmişi
    # uydurmamanın dürüst sonucudur.
    "FISV",
    # genişleme · health (20)
    "TMO", "DHR", "ABT", "BMY", "AMGN", "GILD", "VRTX", "REGN", "BIIB", "ISRG", "SYK", "BSX",
    "MDT", "EW", "ZBH", "BAX", "BDX", "CI", "CVS", "HUM",
    # genişleme · industrials (20)
    "UNP", "CSX", "NSC", "UPS", "FDX", "LMT", "RTX", "NOC", "GD", "LHX", "TDG", "HWM",
    "ETN", "EMR", "PH", "ITW", "CMI", "PCAR", "ROK", "DOV",
    # genişleme · materials (17)
    "SHW", "APD", "ECL", "FCX", "NEM", "NUE", "STLD", "DOW", "DD", "LYB", "PPG", "VMC",
    "MLM", "ALB", "CF", "IP", "PKG",
    # genişleme · reits (14)
    "PLD", "AMT", "CCI", "EQIX", "SPG", "O", "PSA", "DLR", "WELL", "AVB", "EQR", "VTR",
    "IRM", "CBRE",
    # genişleme · staples (20)
    "PM", "MO", "KMB", "CL", "GIS", "KVUE", "KHC", "HSY", "STZ", "MDLZ", "MKC", "CHD",
    "CLX", "SYY", "KR", "TSN", "CAG", "EL", "KDP", "MNST",
    # genişleme · tech (21)
    "TXN", "QCOM", "MU", "ADI", "LRCX", "KLAC", "AMAT", "NXPI", "MCHP", "ON", "MRVL", "SWKS",
    "TER", "MPWR", "SNPS", "CDNS", "CTSH", "ADSK", "INTU", "NOW", "PANW",
    # genişleme · utilities (13)
    "NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL", "ED", "WEC", "ES", "PEG",
    "CEG",
]
INDEX_SYMBOL = "SPY"

# SEMBOL EMEKLİLİK DEFTERİ (2026-07-30) — "artık işlem görmüyor" hükmü TEK YERDE yazılıdır.
#
# NEDEN VAR: bu sekiz sembol evrenden ZATEN çıkarıldı, ama çıkarmak yetmedi. `state/bars/` altında
# CSV'leri duruyor ve DİSKİ SAYAN her yüzey (pano "Piyasa" sekmesi, marketview) onları sonsuza dek
# "bayat" gösteriyordu: son barları delist gününde donmuş, ve o gün ASLA gelmeyecek. Bayatlık
# uyarısı böylece kalıcı gürültüye dönüşüp gerçek bayatlığı (bar hattı bugün durdu) görünmez
# kılıyordu. İkinci boşluk: Finviz keşfi evren dışından sembol getirir — teorik olarak ölü bir
# ismi geri sokabilirdi ve hiçbir kapı onu durdurmuyordu.
#
# DOĞRULAMA: Massive `/v3/reference/tickers` ucu, 2026-07-30 ölçümü — sekizi de `active: false`.
# Her sembolün diskteki son bar tarihi aşağıdaki delist tarihiyle örtüşüyor (yani kayıt sessizce
# kesilmemiş, gerçekten orada bitmiş).
#
# CSV'LER BİLEREK SİLİNMEZ: replay determinizmi diskteki barların değişmemesine dayanır — 2023'ü
# yürüten bir tur, o gün GERÇEKTEN işlem gören bir sembolü görmeye devam etmelidir. Emeklilik
# geçmişi geri almaz, bugünü etiketler.
#
# KAPSAM: bu defter YALNIZ CANLI yüzeyleri etkiler — pano etiketi, Finviz keşif filtresi, sapma
# raporu. BAR ZİNCİRİNE DOKUNMAZ: bu semboller evrende olmadığı için zaten fetch edilmiyorlar;
# buraya bir "fetch etme" kuralı yazmak, var olmayan bir çağrıyı engellemek olurdu.
RETIRED_SYMBOLS: dict[str, str] = {
    "ANSS": "2025-07-18 delist — Synopsys birleşmesi",
    "DFS": "2025-05-19 delist — Capital One birleşmesi",
    "FI": "2025-11-11 NYSE delist — borsa transferi; Nasdaq'ta FISV olarak sürüyor "
          "(halef FISV 2026-07-30'da evrene alındı, operatör kararı — kimlikler AYRI: FI emekli kalır)",
    "HES": "2025-07-21 delist — Chevron birleşmesi",
    "IPG": "2025-11-28 delist — Omnicom birleşmesi",
    "K": "2025-12-12 delist — Mars birleşmesi",
    "PARA": "2025-08-08 delist — Skydance birleşmesi (halef PSKY evrende değil)",
    "WBA": "2025-08-29 delist — Sycamore take-private",
}


def is_retired(ticker: str) -> bool:
    """Sembol emekli mi? Tek kapı: her tüketici `RETIRED_SYMBOLS`u kendi normalizasyonuyla
    sorgularsa (biri .upper() yapar, biri yapmaz) defter aynı sembol için iki farklı cevap verir."""
    return str(ticker or "").upper() in RETIRED_SYMBOLS


# Nasdaq takviminin `time` alanı → kanonik BMO/AMC. ÖLÇÜM (2026-08-01, 6 iş günü / 1307 satır):
#   time-not-supplied  859 (%65,7)   time-after-hours  258 (%19,7)   time-pre-market  190 (%14,5)
# Yani satırların ~%34'ünde baskının seans-öncesi/sonrası olduğu GERÇEKTEN biliniyor. Haritada
# OLMAYAN her değer None'a düşer — "bilinmiyor" bir varsayılan DEĞİL, bir yokluktur (uydurma yasağı).
NASDAQ_EARNINGS_TIME = {"time-pre-market": "bmo", "time-after-hours": "amc"}


EARNINGS_WINDOW_FAILED_DAYS_KEPT = 8   # `stats["dusen_gunler"]` listesi sınırsız büyümez (olay satırı okunabilir kalır)


def nasdaq_earnings_window(start: str, end: str, polite_delay: float = 0.25,
                           with_time: bool = False, stats: dict | None = None) -> dict:
    """#5 — Nasdaq'ın ANAHTARSIZ kazanç takvimi (api.nasdaq.com/api/calendar/earnings?date=...).
    Gün başına bir istek; iş günü penceresi için {TICKER: [date,...]} döner. FMP'nin 250/gün kota
    duvarına karşı birincil kaynak: 21 günlük pencere ≈ 15 istek (evren boyundan BAĞIMSIZ — FMP'de
    250 ticker = 250 istek = bütün günlük kota). Hata gün bazında yutulur; kısmi sonuç dürüsttür.

    `with_time=True` → değerler `(date, "bmo"|"amc"|None)` İKİLİSİ olur. VARSAYILAN False, yani
    şekil DEĞİŞMEZ: mevcut çağıranlar ve kayıtlı sahteler aynı sözlüğü görür (alan eklemek, eski
    sözleşmeyi kırmadan yapılır).

    `stats` — GÜN-BAŞINA DÜRÜSTLÜK SAYACI (denetim C25, 2026-08-02). Verilirse şu alanlarla
    DOLDURULUR: `istenen` (iş günü sayısı), `cevaplayan`, `dusen`, `dusen_gunler` (ilk N tarih),
    `son_hata` (son düşen günün istisna adı), `kapsama` (cevaplayan/istenen; iş günü YOKSA None —
    sıfıra bölünen bir oranı 0,0 diye yazmak ölçülmemiş bir sayı uydurmak olurdu).

    NEDEN DÖNÜŞ TİPİ DEĞİL DE YARDIMCI ALAN: dönüşü ikiliye çevirmek `{TICKER: [...]}` sözleşmesine
    yaslanan kayıtlı sahteleri (tests/test_wpd_kalanlar_v147.py, tests/test_throughput_v7.py)
    kırardı; `stats` sözlüğü çağıran tarafından verildiği için eski çağıran HİÇBİR fark görmez ve
    doldurulmamış bir `stats` "ölçülmedi" demektir — "kapsama tam" DEMEZ (uydurma yasağı).

    BU FONKSİYON HÜKÜM VERMEZ: eşik/yedeğe düşme kararı çağıranındır (bkz. earnings.refresh);
    burada yalnız SAYILIR."""
    out: dict[str, list] = {}
    _ok, _dusen, _gunler, _son_hata = 0, 0, [], None
    _gunler_tum = pd.bdate_range(start, end)
    for _i_g, d in enumerate(_gunler_tum, 1):
        ds = str(d.date())
        # v186: gün başına bir HTTP (3 deneme + geri çekilme) + `polite_delay` — pencere ~30 iş günü
        # olduğunda bu blok tek başına dakikalarca sürer ve eski hâlde tek bir tick yazmazdı.
        _nabiz("kazanc_takvimi:gun", _i_g, len(_gunler_tum))
        try:
            rows = ((_get_json(f"https://api.nasdaq.com/api/calendar/earnings?date={ds}", 20.0)
                     .json().get("data") or {}).get("rows")) or []
            for r_ in rows:
                sym = str(r_.get("symbol") or "").upper().strip()
                if sym:
                    tm = NASDAQ_EARNINGS_TIME.get(str(r_.get("time") or "").strip().lower())
                    out.setdefault(sym, []).append((ds, tm) if with_time else ds)
            _ok += 1
        except Exception as _e:  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli ve tek gün turu düşüremez; DÜŞEN GÜN ARTIK SAYILIYOR (`stats`) ve hükmü çağıran verir
            _dusen += 1
            _son_hata = type(_e).__name__
            if len(_gunler) < EARNINGS_WINDOW_FAILED_DAYS_KEPT:
                _gunler.append(ds)
        time.sleep(polite_delay)
    if stats is not None:
        _istenen = _ok + _dusen
        stats.update(istenen=_istenen, cevaplayan=_ok, dusen=_dusen, dusen_gunler=_gunler,
                     son_hata=_son_hata,
                     kapsama=(round(_ok / _istenen, 4) if _istenen else None),
                     kapsama_yok_nedeni=(None if _istenen else "pencerede iş günü yok"))
    return out


def crosscheck_index(divergence_pct: float = 0.015) -> dict:
    """öneri #5b — endeks (SPY) kapanışını BAĞIMSIZ kaynaktan çapraz doğrula. Zincir tek kaynağın
    dediğine güveniyor; kaynaklardan biri sessizce bozuk kapanış basarsa tüm rejim/tarama o sayının
    üstüne kurulur. Önbellekteki SPY son barı ile Cboe'nin (anahtarsız, gecikmeli) aynı-gün kapanışı
    karşılaştırılır. Aynı gün barı yoksa 'source_lagging' (gecikmeli kaynak suç değil) — yalnız
    AYNI güne ait >%1.5 sapma 'diverged' sayılır ve loop bunu data_bad'e çevirir."""
    import datetime as _dt
    out = {"checked_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
           "status": "fetch_failed", "date": None, "primary_close": None, "cboe_close": None,
           "divergence": None}
    try:
        cp = _cache_path("SPY")
        cached = pd.read_csv(cp, parse_dates=["date"]) if cp.exists() else None
        if cached is None or not len(cached):
            out["status"] = "no_cache"
            return out
        cached = cached.sort_values("date")
        last = cached.iloc[-1]
        pdate, pclose = str(pd.Timestamp(last["date"]).date()), float(last["close"])
        out["date"], out["primary_close"] = pdate, round(pclose, 4)
        # bayat önbellek karşılaştırılMAZ: son bar 5 günden eskiyse tazeleme henüz oturmamış demektir —
        # eski bara karşı doğrulama yanlış-pozitif üretir (canlıda görüldü: test artığı 500.0 vs gerçek 754.95).
        import datetime as _dt2
        if (_dt2.date.today() - _dt2.date.fromisoformat(pdate)).days > 5:
            out["status"] = "cache_stale"
            return out
        ext = _fetch_cboe("SPY", timeout=20.0)
        if ext is None or not len(ext):
            return out
        ext = ext.sort_values("date")
        m = ext[ext["date"].astype(str).str.slice(0, 10) == pdate]
        if not len(m):
            out["status"] = "source_lagging"
            return out
        xclose = float(m.iloc[-1]["close"])
        div = abs(pclose - xclose) / xclose if xclose else 0.0
        out.update({"cboe_close": round(xclose, 4), "divergence": round(div, 5),
                    "status": "diverged" if div > divergence_pct else "ok"})
        return out
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
        return out

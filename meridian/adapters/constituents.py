"""adapters/constituents.py — point-in-time S&P 500 üyeliği (#36).

DENETİM 2026-07-21 (dönüşümlü tur 3) — bu modül hakkında DÜRÜST DURUM:
  * Hiçbir üretim yolu bunu ÇAĞIRMIYORDU. `current()`/`as_of()` yalnız testlerden çağrılıyor; canlı
    evren elle bakımlı `data.REPLAY_UNIVERSE`. Yani #49/#52/#53 denetimlerinde düzeltilen üç gerçek
    hata, hiçbir zaman koşmayan bir kodda düzeltilmişti. (Desen 1: koşuyor mu değil, ÜRETİYOR mu.)
  * Wikipedia yolu bu kurulumda ÇALIŞAMAZ: (a) `pandas.read_html` lxml/bs4/html5lib ister — üçü de
    kurulu değil; (b) Wikipedia bu User-Agent'a **403** dönüyor (bot politikası). İkisi de
    `except: return None` ile yutuluyordu, dolayısıyla modül sessizce hep bayat önbelleği döndürürdü.
  * Diskteki ÜRETİM önbelleği TEST VERİSİYDİ: {"as_of": "2099-01-01", "current":
    ["AAPL","MSFT","NVDA"], changes:[{removed:"nan"}]} — bir test koşusu gerçek state klasörüne
    sızmıştı (2026-07-18). Bir tüketici olsaydı S&P 500 diye ÜÇ sembol alacaktı ve `as_of()` uydurma
    bir tarihsel üyelik üretecekti. Karantina: state/quarantine/.

BU YÜZDEN artık: (1) kaynak zinciri FMP'yi (anahtarlı, zaten kullanımda) birincil yapar, Wikipedia
en iyi-çaba ikincildir; (2) her okuma/yazım MAKULLUK KAPISINDAN geçer — 400'den az sembol S&P 500
değildir, reddedilir; (3) başarısızlık SESSİZ değildir: `health()` + watchdog üretkenlik dedektörü;
(4) `universe_drift()` gerçek bir tüketicidir — elle bakımlı evrendeki ölü isimleri söyler.

HONEST LIMIT (değişmedi): bu, üyelik survivorship'ini düzeltir; gerçekten yanlılıksız bir backtest
delisted isimlerin BARLARINI da ister ve ücretsiz kaynaklar onu taşımaz. PIT iskelesi, bias-free
evren değil.
"""
from __future__ import annotations
import datetime as dt

from .. import store

WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
CACHE = "sp500_constituents.json"
MIN_MEMBERS = 400          # S&P 500 ~503 isim; bunun altı "üyelik listesi" DEĞİLDİR (fixture/kırpık)
_HEALTH = {"ok": None, "source": None, "n": 0, "at": None, "error": ""}


def health() -> dict:
    """Kaynak gerçekten üretti mi? 'except: return []' ile yutulan her hata burada görünür kalır."""
    return dict(_HEALTH)


def _note(ok: bool, source: str | None = None, n: int = 0, error: str = "") -> None:
    _HEALTH.update({"ok": ok, "source": source, "n": int(n), "error": error[:200],
                    "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")})


def _plausible(members) -> bool:
    """MAKULLUK KAPISI: bir üyelik listesi ancak yeterince büyük ve sembol-şeklindeyse kabul edilir.
    Diskteki sahte önbellek (3 sembol) tam da buradan geçemezdi (denetim turu 3)."""
    if not isinstance(members, list) or len(members) < MIN_MEMBERS:
        return False
    good = [m for m in members if isinstance(m, str) and 1 <= len(m.strip()) <= 6
            and _tick(m) and all(ch.isalnum() or ch == "-" for ch in m.strip())]
    return len(good) >= MIN_MEMBERS


def _cached() -> dict:
    """Önbelleği OKU ve makullükten geçir. Geçemezse boş — bayat/uydurma veri asla servis edilmez."""
    d = store.read_json(CACHE, {}) or {}
    if d.get("current") and not _plausible(d.get("current")):
        try:
            from .. import obs
            obs.warn("constituents_cache_invalid", n=len(d.get("current") or []),
                     as_of=str(d.get("as_of"))[:10])
        except Exception:  # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci bir kanal yok; kayıt denemesi çağıranı düşüremez
            pass
        return {}
    # gelecek tarihli damga = bozuk yazım (fixture'da "2099-01-01" vardı); tazelik kontrolü anlamsızlaşır
    try:
        if d.get("as_of") and dt.date.fromisoformat(str(d["as_of"])[:10]) > dt.date.today():
            return {}
    except ValueError:  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
        return {}
    return d


def _fetch_tables():
    """(current_symbols, changes) — Wikipedia'dan. Başarısızlıkta (None, None) AMA sebebi kaydederek.
    NOT: pandas.read_html lxml/bs4 ister ve Wikipedia botlara 403 dönebilir; ikisi de burada görünür."""
    try:
        import pandas as pd
        import httpx
        r = httpx.get(WIKI_URL, timeout=20, headers={"User-Agent": "Meridian/1.0"},
                      follow_redirects=True)
        if r.status_code >= 400:
            _note(False, "wikipedia", 0, f"HTTP {r.status_code}")
            return None, None
        tables = pd.read_html(r.text)                     # needs lxml/html5lib+bs4; may raise if absent
    except Exception as e:
        _note(False, "wikipedia", 0, f"{type(e).__name__}: {e}")
        return None, None
    cur, changes = None, []
    try:
        cur = [str(s).strip().upper().replace(".", "-") for s in tables[0]["Symbol"].tolist()]
    except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
        cur = None
    try:
        ch = tables[1]
        ch.columns = ["_".join(str(x) for x in c) if isinstance(c, tuple) else str(c) for c in ch.columns]
        dcol = next((c for c in ch.columns if "Date" in c), None)
        acol = next((c for c in ch.columns if "Added" in c and "Ticker" in c), None)
        rcol = next((c for c in ch.columns if "Removed" in c and "Ticker" in c), None)
        # NaN-safe cell read (L3): pandas reads an empty change-log cell as float('nan'), and bool(nan) is
        # True, so `nan or ""` returned nan and str(nan)=='nan' — as_of() then added a fabricated 'NAN'
        # ticker to point-in-time membership. Coalesce NaN/None to "" explicitly.
        def _cell(v):
            return "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v).strip()
        for _, row in ch.iterrows():
            changes.append({"date": _cell(row.get(dcol)), "added": _cell(row.get(acol)),
                            "removed": _cell(row.get(rcol))})
    except Exception:  # sessiz-yutma: ağ/sağlayıcı hatası bu yolun NORMAL hâli; çağıran boş sonuç üzerinden yedek kaynağa düşer ve kaynak seçimi ayrıca kaydedilir
        changes = []
    return cur, changes


def current(use_cache: bool = True) -> list[str]:
    """Güncel S&P 500 sembolleri. Zincir: FMP (anahtarlı, zaten kullanımda) → Wikipedia (en iyi çaba).
    Günlük önbellek; hiçbir kaynak MAKUL liste veremezse [] — çağıran elle bakımlı evrene düşer.

    ÖNEMLİ: eskiden başarısızlıkta 'dünün listesi'ni döndürüyordu; o liste sahte olduğunda (canlıda
    öyleydi) sahtelik sonsuza kadar servis ediliyordu. Artık önbellek de makullük kapısından geçer."""
    today = dt.date.today().isoformat()
    cached = _cached()
    if use_cache and cached.get("as_of") == today and cached.get("current"):
        _note(True, "cache", len(cached["current"]))
        return cached["current"]

    from . import fmp
    if fmp.available() and not fmp.quota_blocked():
        syms = [str(s).strip().upper().replace(".", "-") for s in (fmp.sp500_constituents() or [])]
        if _plausible(syms):
            store.write_json(CACHE, {"as_of": today, "current": syms,
                                     "changes": cached.get("changes", []), "source": "fmp"})
            _note(True, "fmp", len(syms))
            return syms
        _note(False, "fmp", len(syms), "makul olmayan/boş liste (kota?)")

    cur, changes = _fetch_tables()
    if _plausible(cur):
        store.write_json(CACHE, {"as_of": today, "current": cur, "changes": changes,
                                 "source": "wikipedia"})
        _note(True, "wikipedia", len(cur))
        return cur
    if not _HEALTH.get("error"):
        _note(False, None, 0, "hiçbir kaynak makul üyelik listesi vermedi")
    return cached.get("current", []) if _plausible(cached.get("current")) else []


def _iso(d) -> str | None:
    """Normalize a change-log date to ISO YYYY-MM-DD. Wikipedia's column is human-readable ('October 1,
    2024'); the old code sliced [:10] and compared LEXICALLY, so every letter-leading date read as
    'after any query date' and the PIT reconstruction INVERTED (audit #52). None if unparseable."""
    s = str(d or "").strip()
    if not s:
        return None
    import datetime as dt
    try:
        return dt.date.fromisoformat(s[:10]).isoformat()
    except ValueError:  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
        try:
            import pandas as pd
            ts = pd.to_datetime(s, errors="coerce")
            return None if ts is None or ts is pd.NaT else str(ts.date())
        except Exception:  # sessiz-yutma: pandas ile İKİNCİ deneme de tarihi çözemedi; alan None kalır ve çağıran None'ı zaten 'tarih yok' diye ele alıyor
            return None


def _tick(v) -> str:
    """Ticker cell → clean symbol; '' for NaN-ish junk. The fetch path sanitizes, but PERSISTED caches
    written before that fix still carry literal 'nan' strings that fabricated a phantom 'NAN' instrument
    in PIT membership (audit #49 — live on disk)."""
    s = str(v or "").strip().upper()
    return "" if s in ("", "NAN", "NONE", "N/A", "-", "—") else s


def as_of(date: str) -> list[str]:
    """Reconstruct membership on `date` by walking the change-log back from the current list. Best-effort
    (Wikipedia's change table only spans recent years); [] if unavailable. Honest scaffold for PIT.

    [] dönmesi 'o tarihte kimse yoktu' DEĞİL 'BİLMİYORUZ' demektir — çağıran bunu üyelik gibi
    kullanmamalı (denetim turu 3: sessiz boş liste, survivorship'i 'düzeltildi' sanmaya yol açar)."""
    data = _cached()
    members = set(data.get("current", []))
    if not members:
        members = set(current())
        data = _cached()                     # current() just wrote the cache — re-read so the change-log
        if not members:                      # is actually applied instead of iterating the stale pre-fetch
            return []                        # snapshot (audit #53: cold cache returned CURRENT membership
                                             # for any historical date — survivorship bias)
    for ch in data.get("changes", []):
        d = _iso(ch.get("date"))
        if d and d > date:                                # undo changes that happened AFTER `date`
            add, rem = _tick(ch.get("added")), _tick(ch.get("removed"))
            if add:
                members.discard(add)                      # it was added after `date` → not a member then
            if rem:
                members.add(rem)                          # it was removed after `date` → was a member then
    return sorted(m for m in members if _tick(m))


def universe_drift() -> dict:
    """GERÇEK TÜKETİCİ (denetim turu 3): elle bakımlı REPLAY_UNIVERSE ile güncel endeks üyeliğini
    karşılaştır. 2026-07-21'de 7 ölü sembol (DFS, FI, HES, IPG, PARA, K, WBA) ELLE bulunmuştu —
    tam da bu modülün söylemesi gereken şey. Kaynak yoksa 'unknown' döner: 'sapma yok' DEMEZ."""
    from . import data as _data
    REPLAY_UNIVERSE = _data.REPLAY_UNIVERSE
    # İKİNCİ, BAĞIMSIZ KANIT (2026-07-22): üyelik kaynağı bu kurulumda ÇALIŞMIYOR (Wikipedia 403,
    # FMP kotası) ve rapor haklı olarak "unknown" diyor — ama o zaman ölü sembol sorusu CEVAPSIZ
    # kalıyordu. Bar hattının verisiz-sembol defteri tam bu soruyu başka bir yerden cevaplıyor:
    # "her kaynak DÜZGÜN cevap verip sıfır satır döndü" hükmünün ARDIŞIK tekrarı. Üyelik listesi
    # olmasa da bu kanıt taşınır; olay defterinde üretilip tüketilmeyen bir sayaç bırakmıyoruz.
    _nd = store.read_json(_data.NO_DATA_FILE, {}) or {}
    no_data = sorted(t for t, v in _nd.items()
                     if int((v or {}).get("streak") or 0) >= _data.NO_DATA_CONFIRM_STREAK)
    # ÜÇÜNCÜ KANIT — EMEKLİLİK DEFTERİ VE ONUN BEKÇİSİ (2026-07-30). 2026-07-21'de ELLE bulunan
    # ölü isimler artık `data.RETIRED_SYMBOLS`ta hükümle yazılı ve evrenden çıkarılmış. Rapor iki
    # şeyi söyler: kaç isme emeklilik hükmü verildiği (bakımın YAPILDIĞININ kanıtı), ve o isimlerden
    # herhangi biri evrene GERİ girmiş mi. `retired_in_universe` normalde BOŞTUR; boş değilse biri
    # (elle düzenleme, birleşme sonrası kopyala-yapıştır) delist olmuş bir sembolü tarama evrenine
    # geri koymuş demektir — sessiz kalırsa motor günlerce ölü bir isim hakkında karar üretirdi.
    retired_in_universe = sorted(t for t in REPLAY_UNIVERSE if _data.is_retired(t))
    members = current()
    if not _plausible(members):
        return {"status": "unknown", "reason": _HEALTH.get("error") or "üyelik kaynağı yok",
                "universe": len(REPLAY_UNIVERSE), "stale": [], "n_stale": 0,
                "no_data": no_data, "n_no_data": len(no_data),
                "retired_n": len(_data.RETIRED_SYMBOLS), "retired_in_universe": retired_in_universe}
    mset = {m.upper() for m in members}
    stale = sorted(t for t in REPLAY_UNIVERSE if t.upper() not in mset)
    return {"status": "ok", "source": _HEALTH.get("source"), "universe": len(REPLAY_UNIVERSE),
            "members": len(mset), "stale": stale, "n_stale": len(stale),
            "no_data": no_data, "n_no_data": len(no_data),
            "retired_n": len(_data.RETIRED_SYMBOLS), "retired_in_universe": retired_in_universe}

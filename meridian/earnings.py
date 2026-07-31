"""earnings.py — the earnings blackout. A swing-momentum entry taken right into an earnings print
is a coin flip on a gap, not an edge (Hard Rule 7: no fantasy fills). If state/earnings.csv exists
(rows: ticker,date  — one scheduled report date per line, YYYY-MM-DD), a plan whose date falls within
BLACKOUT_DAYS *before* the next scheduled report is not armed. No CSV -> no-op, so the gate is present
and testable now and simply activates the day an earnings feed (FMP) writes the file. Deterministic,
network-free: it only reads the file it is handed."""
from __future__ import annotations
import csv
import datetime as dt

from . import config

BLACKOUT_DAYS = 5   # no fresh entry within this many calendar days before a scheduled report

# {ticker: [date, ...]} cached by file mtime so a rewritten earnings.csv is picked up without restart
_CACHE: dict = {}
_CACHE_MTIME: float | None = None


def _load() -> dict:
    global _CACHE, _CACHE_MTIME
    path = config.STATE / "earnings.csv"
    if not path.exists():
        _CACHE, _CACHE_MTIME = {}, None
        return _CACHE
    mtime = path.stat().st_mtime
    if mtime == _CACHE_MTIME:
        return _CACHE
    out: dict[str, list[str]] = {}
    try:
        with path.open(newline="") as fh:
            for row in csv.reader(fh):
                if len(row) < 2:
                    continue
                tkr, d = row[0].strip().upper(), row[1].strip()
                if not tkr or tkr in ("TICKER", "SYMBOL"):    # tolerate a header line
                    continue
                try:
                    dt.date.fromisoformat(d)
                except ValueError:  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
                    continue
                out.setdefault(tkr, []).append(d)
    except Exception as e:
        # YASA 4 (2026-07-21) — BU SESSİZLİK PARA KAYBETTİRİR: takvim boş dönerse kazanç karartması
        # tamamen KAPANIR ve motor bilanço gününe pozisyonla girer. Hiçbir istisna yükselmez, hiçbir
        # test kırılmaz; yalnız "bugün karartma yok" der. Davranış korunuyor (boş takvim), sinyal var.
        try:
            from . import obs
            obs.warn("earnings_calendar_unreadable", path=str(path), error=f"{type(e).__name__}: {e}",
                     detail="karartma penceresi bu turda DEVRE DIŞI")
        except Exception:
            # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci kanal yok; uyarı denemesi
            # takvim yüklemesini düşüremez.
            pass
        out = {}
    for tkr in out:
        out[tkr].sort()
    _CACHE, _CACHE_MTIME = out, mtime
    return out


def clear_cache() -> None:
    global _CACHE_MTIME
    _CACHE_MTIME = None


def days_since_report(ticker: str, on_date: str, max_days: int = 2) -> bool:
    """PEAD/episodik-pivot çapası: on_date, ticker'ın bir kazanç raporundan sonraki max_days GÜN
    içinde mi? (rapor günü dahil). Veri yoksa False — kurulum uydurma tetiklemez."""
    try:
        d = dt.date.fromisoformat(str(on_date)[:10])
    except (ValueError, TypeError):  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
        return False
    for ds in _load().get(str(ticker).upper(), []):
        try:
            e = dt.date.fromisoformat(ds)
        except ValueError:  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
            continue
        if 0 <= (d - e).days <= max_days:
            return True
    return False


def refresh(tickers: list[str]) -> int:
    """#5 — birleşik tazeleme: BİRİNCİL kaynak Nasdaq takvimi (anahtarsız, evren-boyundan bağımsız
    ~15 istek: geriye 7 gün [PEAD çapası] + ileriye 14 gün [karartma penceresi]); Nasdaq boş dönerse
    FMP'ye düşülür (anahtar varsa; 250 ticker = 250 istek = günlük kota — o yüzden yedek). Sonuç
    MEVCUT csv ile BİRLEŞTİRİLİR (kaynak değişimi geçmiş çapaları silmez)."""
    import datetime as _dt
    from .adapters import data as _da
    today = _dt.date.today()
    uni = {str(t).upper() for t in tickers}
    fetched = _da.nasdaq_earnings_window(str(today - _dt.timedelta(days=7)),
                                         str(today + _dt.timedelta(days=14)))
    rows = [(t, d) for t, ds in fetched.items() if t in uni for d in ds]
    src = "nasdaq"
    if not rows:
        src = "fmp"
        n = refresh_from_fmp(tickers)
        if not n:
            # YASA 4 — HER İKİ KAYNAK DA BOŞ (2026-07-26). Bu yol SESSİZ dönüyordu: `refresh` 0
            # döndürüyor, çağıran onu "yeni satır yok" diye okuyor ve takvim OLDUĞU GİBİ kalıyordu.
            # Ama takvim bayatladığında (gelecek tarih kalmadığında) `in_blackout` herkes için
            # False döner, yani karartma guard'ı FAIL-OPEN kapanır ve motor bilanço gününe
            # pozisyonla girer. "Tazeleme koştu, yeni bir şey yoktu" ile "İKİ KAYNAK DA KONUŞMADI"
            # aynı sayıyla anlatılamaz; ikincisi bir arıza sinyalidir.
            from . import obs
            from .adapters import fmp as _fmp
            cov = coverage(tickers)
            obs.warn("earnings_refresh_empty", sources="nasdaq+fmp", universe=len(uni),
                     fmp_key_present=bool(_fmp.available()), fmp_quota_blocked=bool(_fmp.quota_blocked()),
                     known_tickers=cov.get("known_tickers"), future_dates=cov.get("future_dates"),
                     inert=cov.get("inert"),
                     detail="kazanç takvimi HİÇ tazelenemedi — takvim bayatlarsa karartma guard'ı "
                            "fail-open kapanır ve bilanço gününde işlem açılır")
        return n
    merged = {(t, d) for t, ds in _load().items() for d in ds} | set(rows)
    import tempfile, os
    path = config.STATE / "earnings.csv"
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    with os.fdopen(fd, "w") as fh:
        fh.write("ticker,date\n")
        for t, d in sorted(merged):
            fh.write(f"{t},{d}\n")
    os.replace(tmp, path)
    clear_cache()
    from . import obs
    obs.log("earnings_refreshed", source=src, new_rows=len(rows), total=len(merged))
    return len(rows)


def refresh_from_fmp(tickers: list[str]) -> int:
    """Evrenin kazanç tarihlerini FMP'den çekip state/earnings.csv'ye yazar (ticker,date). Hem PEAD
    çapasını hem MEVCUT kazanç-karartma guard'ını (bugüne dek boş veriyle no-op'tu) gerçek veriyle
    besler. Anahtar yoksa 0 döner; kısmi hata bir ticker'ı atlar, dosyayı bozmaz."""
    from .adapters import fmp
    if not fmp.available():
        return 0
    import time as _t
    rows, failed = [], []
    for t in tickers:
        try:
            for d in fmp.earnings_dates(t, strict=True):   # hata YUTULMAZ: eksik ≠ "kazanç yok"
                rows.append((t.upper(), d))
        except Exception:  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
            failed.append(t.upper())
            if fmp.quota_blocked():                        # kota bitti: kalanı denemek anlamsız
                failed.extend(x.upper() for x in tickers[tickers.index(t) + 1:])
                break
            continue
        _t.sleep(0.1)                                     # polite delay — refetch ile aynı görgü kuralı
    if not rows:
        return 0
    # KISMİ BAŞARISIZLIK KORUMASI (adapters.fmp denetimi, tur 4 — 2026-07-21):
    # Eskiden dosya, gelen ne varsa ONUNLA ÜZERİNE YAZILIYORDU. Kota pasın ortasında biterse
    # (bugün oldu) 100 ticker gelir, 150'si düşerdi; in_blackout() veri yokken FAIL-OPEN olduğu için
    # o 150 isimde KAZANÇ GÜNÜ işlem açılırdı — sert bir guard sessizce no-op'a dönerdi.
    # Çözüm: yaz değil BİRLEŞTİR; başarısız ticker'ların ESKİ tarihleri korunur ve durum kaydedilir.
    if failed:
        from . import obs
        prev = _load()
        for t in failed:
            for d in prev.get(t, []):
                rows.append((t, d))
        obs.warn("earnings_refresh_partial", ok=len(tickers) - len(failed), failed=len(failed),
                 kept_from_cache=len({t for t in failed if prev.get(t)}))
    import tempfile, os
    path = config.STATE / "earnings.csv"
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    with __import__("os").fdopen(fd, "w") as fh:
        fh.write("ticker,date\n")
        for t, d in sorted(set(rows)):
            fh.write(f"{t},{d}\n")
    os.replace(tmp, path)
    clear_cache()
    return len(set(rows))


def in_blackout(ticker: str, on_date: str, days: int = BLACKOUT_DAYS) -> bool:
    """True if `on_date` is within `days` calendar days *before* (or on) the ticker's next scheduled
    earnings date. Unknown ticker / no CSV -> False (never blocks when there is no information)."""
    dates = _load().get((ticker or "").upper())
    if not dates:
        return False
    try:
        d0 = dt.date.fromisoformat(str(on_date)[:10])
    except ValueError:  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
        return False
    for ds in dates:
        ed = dt.date.fromisoformat(ds)
        if 0 <= (ed - d0).days <= days:
            return True
    return False


def known(ticker: str) -> bool:
    """Bu sembol için takvimde HİÇ tarih var mı? in_blackout() False dönüyorsa iki şey demek olabilir:
    'kontrol edildi, temiz' ya da 'hiç veri yok'. İkisi aynı şey DEĞİL (denetim turu 11)."""
    return bool(_load().get((ticker or "").upper()))


def coverage(tickers: list | None = None) -> dict:
    """Karartma guard'ı GERÇEKTEN kaç sembolü koruyor? Canlıda 250 evrenin 181'i biliniyordu; kalan
    69'unda guard sessizce KAPALIYDI ve hiçbir yer bunu söylemiyordu. Ayrıca takvim bayatlarsa
    (gelecek tarih kalmazsa) guard herkes için kapanır — bunu da burada söylüyoruz."""
    import datetime as _dt
    data = _load()
    today = _dt.date.today().isoformat()
    future = sum(1 for ds in data.values() for d in ds if d >= today)
    all_dates = [d for ds in data.values() for d in ds]
    out = {"known_tickers": len(data), "future_dates": future,
           "max_date": max(all_dates) if all_dates else None,
           "inert": future == 0}          # gelecek tarih yoksa guard fiilen KAPALI
    if tickers:
        uni = [str(t).upper() for t in tickers]
        unknown = [t for t in uni if t not in data]
        out.update({"universe": len(uni), "unknown": len(unknown), "unknown_sample": unknown[:12],
                    "covered_pct": round(100 * (len(uni) - len(unknown)) / max(1, len(uni)), 1)})
    return out


def blackout_radar(tickers: list, on_date: str) -> dict:
    """öneri 2b — karartma radarı: 'neden işlem yapmadı?' sorusunu panelde cevaplar. Verilen evren
    için bugün karartmada olan semboller + bilinen bir SONRAKİ rapor tarihi. CSV boşsa dürüstçe
    empty=True döner (radar 'veri yok' der, boş liste 'karartma yok' gibi OKUNMAZ)."""
    data = _load()
    rows = []
    for t in tickers:
        ds = data.get(str(t).upper())
        if not ds:
            continue
        try:
            d0 = dt.date.fromisoformat(str(on_date)[:10])
        except ValueError:  # sessiz-yutma: biçimsiz/eksik tek alan; yalnız bu değer düşer, satır başına uyarı asıl sinyali log seline gömerdi
            break
        nxt = next((x for x in ds if dt.date.fromisoformat(x) >= d0), None)
        if in_blackout(t, on_date):
            rows.append({"ticker": str(t).upper(), "next_report": nxt,
                         "days_left": (dt.date.fromisoformat(nxt) - d0).days if nxt else None})
    return {"empty": not data, "date": on_date, "blackout": sorted(rows, key=lambda r: r["ticker"]),
            "known_tickers": len(data)}

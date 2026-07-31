"""marketview.py — İZLENEN EVRENİN TEK BAKIŞTA OKUNAN GÖRÜNTÜSÜ (2026-07-27).

Pano bugüne kadar yalnız KARARA girmiş sembolleri gösteriyordu: aday, plan, pozisyon. Oysa motorun
izlediği evren `state/bars/*.csv` ve operatörün "bugün neyi izliyorum?" sorusunun panoda hiçbir
cevabı yoktu — evrenin varlığı yalnız bir dizindeki DOSYA SAYISIYDI. Kapının elediği 250 sembol,
elenmedikleri için değil, hiç GÖRÜNMEDİKLERİ için yoktu.

BU BİR FİYAT SERVİSİ DEĞİLDİR. Gövdedeki her sayı EOD (kapanmış günlük) bardan türer; canlı fiyat
İDDİA EDİLMEZ. En taze bar hangi seanstansa `as_of` odur ve ondan geride kalan satırlar `stale_n`
ile ADIYLA sayılır: bayat bir kapanışı taze gibi göstermek, panonun okura yalan söylemesidir.

SEANS İÇİ KOLON (2026-07-27) BU ÇİZGİYİ BOZMAZ, DARALTIR. `intraday_close` YALNIZ silahlı
sembollerde doludur — çünkü dakikalık bar akışı (barfeed) yalnız onları izler — ve değeri sıcak
fiyat değil, KAPANMIŞ dakikalık barın kapanışıdır. İzlenmeyen bir sembole fiyat yazmak, ölçülmemiş
bir şeyi ölçülmüş göstermekti; kapanmamış barın "kapanışını" yazmak look-ahead'i panoya taşımaktı.
Bugün silahlı plan sıfır olduğu için kolon baştan sona "—"dır: bu bir arıza değil, DOĞRU cevap.

ÖLÇÜLEMEYEN None KALIR (UYDURMA YASAĞI). 21 barı olmayan bir sembolün 20 günlük değişimi YOKTUR;
oraya 0.0 yazmak "değişmedi" diye okunur. Her pencere kendi asgari bar sayısını ister, yoksa alan
None döner ve pano onu "—" olarak gösterir.
"""
from __future__ import annotations

import datetime as dt
import math
from pathlib import Path

import pandas as pd

from . import barclock, config, earnings, hotstate, store
# EMEKLİLİK DEFTERİ TEK KAYNAKTAN (2026-07-30): hangi sembolün delist olduğu `adapters.data`da
# yazılıdır. Buraya ikinci bir liste kopyalamak, zamanla AYRIŞAN iki gerçek demekti.
from .adapters import data as _data
# TAZELİK YASASI TEK KAYNAKTAN: intraday_cycle karar verirken hangi eşiği kullanıyorsa ölçüm de
# onu kullanır. Buraya ikinci bir "120" yazmak, zamanla AYRIŞAN iki yasa demekti — pano "taze"
# derken motorun "bayat" dediği bir barı gösterebilirdi. intraday_cycle marketview'ü import
# ETMEZ (yalnız barclock/hotstate/store/obs/health), yani döngü yok.
from .intraday_cycle import STALE_TOL_S

# Pencereler. Hepsi BAR sayısıdır (takvim günü değil): 252 bar ≈ 52 hafta, 20 bar ≈ bir ay.
_SPARK_BARS = 60
_ADV_BARS = 20
_CHG20_BARS = 21          # 20 GÜNLÜK değişim 21 kapanış ister (t ile t-20)
_HIGH_BARS = 252

# {csv mutlak yolu: (mtime_ns, satır çekirdeği)} — SÜREÇ-İÇİ önbellek.
# İlk çağrı 260 CSV okur (kabul edilen bedel); sonraki her çağrı dosyanın mtime'ı DEĞİŞMEDİKÇE
# diske hiç inmez. EOD dosyaları günde bir kez yazıldığı için isabet oranı fiilen 1'dir — pano
# 15 saniyede bir tazelendiğinde aynı 260 dosyayı yeniden ayrıştırmak saf israftı.
# Anahtar MUTLAK yoldur: sandbox'lı testler canlı önbellekle aynı gözü paylaşmaz.
_CACHE: dict[str, tuple[int, dict]] = {}

# Bar'dan türeyen alanların ÖLÇÜLMEMİŞ hâli. Tek yerde durur ki "barı olmayan satır" (finviz
# ekstrası) ile "barı okunamayan satır" aynı dürüst şekli taşısın.
_EMPTY_CORE: dict = {"last_date": None, "close": None, "chg1_pct": None, "chg20_pct": None,
                     "dist_52w_high_pct": None, "adv20_usd": None, "spark": []}


def clear_cache() -> None:
    """Önbelleği boşalt. mtime değişmeden içeriğin değiştiği tek senaryo testlerdir; üretimde
    dosyayı yazan her yol mtime'ı da değiştirir."""
    _CACHE.clear()


def _f(x):
    """Sonlu float ya da None. NaN/±Inf 'ölçüldü' diye okunamaz (bkz. store.sanitize gerekçesi)."""
    try:
        v = float(x)
    except (TypeError, ValueError):  # sessiz-yutma: tek bir hücre sayı değil — YALNIZ o alan None olur, satır yaşar; 260 sembol × her tur uyarı asıl sinyali log seline gömerdi
        return None
    return v if math.isfinite(v) else None


def _pct(base, son):
    """`son`un `base`e göre yüzde farkı. base yoksa/0 ise ölçüm YOKTUR — None."""
    if base is None or son is None or base == 0:
        return None
    return (son / base - 1.0) * 100.0


def _read_csv(path: Path) -> pd.DataFrame:
    """TEK okuma boğazı: önbellek isabeti buradan ölçülür (ve testte sayılır). `usecols` ile üç
    kolon okunur — OHLC'nin tamamı bu görünümde kullanılmıyor, 260 dosyada boşuna ayrıştırılmaz."""
    return pd.read_csv(path, usecols=["date", "close", "volume"])


def _compute_core(path: Path) -> dict:
    """Bir sembolün BAR'dan türeyen alanları. Dosya okunamazsa satır DÜŞMEZ, alanları None kalır:
    "izleniyor ama barı okunamadı" bilgisinin kendisi operatör için sinyaldir; sembolü evrenden
    sessizce silmek, sorunu görünmez kılardı."""
    try:
        df = _read_csv(path)
    except Exception as e:
        from . import obs
        obs.warn("marketview_bars_unreadable", file=path.name, error=f"{type(e).__name__}: {e}",
                 detail="sembol evrende ÖLÇÜMSÜZ satır olarak kalır — listeden düşmez")
        return dict(_EMPTY_CORE)

    closes = [_f(v) for v in df["close"].tolist()]
    vols = [_f(v) for v in df["volume"].tolist()]
    dates = [str(v)[:10] for v in df["date"].tolist()]
    # Kapanışı olmayan bar bir bar DEĞİLDİR: pencere sayımına girerse "20 barım var" yalanı olur.
    keep = [i for i, c in enumerate(closes) if c is not None]
    if not keep:
        return dict(_EMPTY_CORE)
    closes = [closes[i] for i in keep]
    vols = [vols[i] for i in keep]
    dates = [dates[i] for i in keep]

    n = len(closes)
    out = dict(_EMPTY_CORE)
    out["last_date"] = dates[-1]
    out["close"] = closes[-1]
    if n >= 2:
        out["chg1_pct"] = _pct(closes[-2], closes[-1])
    if n >= _CHG20_BARS:
        out["chg20_pct"] = _pct(closes[-_CHG20_BARS], closes[-1])
    if n >= _HIGH_BARS:
        # 52 haftalık zirveye uzaklık KAPANIŞ üzerinden ölçülür (intraday high değil): bu görünümün
        # tamamı kapanış verisidir, iki farklı fiyat tanımını tek kolonda karıştırmak olurdu.
        out["dist_52w_high_pct"] = _pct(max(closes[-_HIGH_BARS:]), closes[-1])
    if n >= _ADV_BARS:
        pen_c, pen_v = closes[-_ADV_BARS:], vols[-_ADV_BARS:]
        if all(v is not None for v in pen_v):
            out["adv20_usd"] = sum(c * v for c, v in zip(pen_c, pen_v)) / _ADV_BARS
    out["spark"] = closes[-_SPARK_BARS:]
    return out


def _bar_core(path: Path) -> dict:
    """Önbellekli `_compute_core`. Anahtar yol, geçerlilik ölçüsü mtime_ns."""
    key = str(path)
    try:
        mtime = path.stat().st_mtime_ns
    except OSError as e:
        from . import obs
        obs.warn("marketview_bars_stat_failed", file=path.name, error=f"{type(e).__name__}: {e}",
                 detail="önbellek geçerliliği ölçülemedi — çekirdek bu turda yeniden hesaplanır")
        return _compute_core(path)
    hit = _CACHE.get(key)
    if hit is not None and hit[0] == mtime:
        return hit[1]
    core = _compute_core(path)
    _CACHE[key] = (mtime, core)
    return core


# Silahlı bir sembol için okunacak bar sayısı. `admissible_bars` en yenisini seçtiği için derin
# geçmişe gerek YOK: 10 bar, kapanmamış son barı elemeye ve bir öncekine düşmeye fazlasıyla yeter.
# intraday_cycle 390 okur çünkü o KURULUM hesaplar; burada tek soru "en yeni kapanmış kapanış ne?".
_INTRADAY_BARS = 10


def _intraday(ticker: str, as_of: dt.datetime) -> tuple:
    """(kapanış, damga, durum) — durum: "ok" | "akis_yok" | "bayat".

    DİSİPLİN, intraday_cycle'ın AYNISI ve bilinçli olarak dardır:
      * yalnız KAPANMIŞ (admissible) dakikalık bar okunur — sıcak/anlık fiyat DEĞİL. Kapanmamış bir
        barın kapanışı diye bir şey yoktur; onu göstermek look-ahead'i panoya taşımak olurdu.
      * en yeni kapanmış bar STALE_TOL_S'ten eskiyse ölçüm YOKTUR (None). Bayat bir fiyatı "seans
        içi" diye göstermek, akış koptuğunda operatöre canlı bir sayı gösterirdi — sessiz yalan.
    """
    raw = hotstate.read_bars(ticker, _INTRADAY_BARS)
    if raw is None:                      # Redis yok/erişilemiyor — dosyaya düşülür, uydurulmaz
        return None, None, "akis_yok"
    bars = barclock.admissible_bars(raw, as_of)
    if not bars:
        return None, None, "bayat"       # akış var ama KAPANMIŞ bar yok — ölçüm yine yok
    son = bars[-1]
    if not barclock.is_fresh(son.get("t"), STALE_TOL_S, as_of):
        return None, None, "bayat"
    return _f(son.get("c")), son.get("t"), "ok"


def _next_report(dates: list, on_date: str | None):
    """`on_date`ten itibaren BİR SONRAKİ rapor tarihi; yoksa None.

    GEÇMİŞ RAPOR YAZILMAZ: bu kolonun cevapladığı soru "önümde bir bilanço riski var mı?"dır.
    Geçmiş bir tarihi aynı hücrede göstermek, geçmiş ile gelecek riski tek sayıya karıştırırdı."""
    if not dates or not on_date:
        return None
    return next((d for d in sorted(dates) if d >= on_date), None)


def build() -> dict:
    """İzlenen evrenin tamamı — pano 'Piyasa' sekmesinin tek kaynağı.

    Evren = `state/bars/*.csv` (motorun fiilen bar tuttuğu semboller). `finviz_universe.json`
    keşfi bars'ta OLMAYAN bir sembol getirirse o da satır olur ama bar alanları None kalır ve
    `source="finviz"` etiketiyle işaretlenir — "keşfedildi" ile "ölçülüyor" aynı şey değildir.

    EMEKLİ SEMBOLLER satır olarak KALIR (bar geçmişi gerçek, CSV replay determinizmi için silinmez)
    ama BAYATLIK ÖLÇÜMÜNE GİRMEZ: son barı delist gününde donmuş bir sembol her gün "bayat" sayılır
    ve o kalıcı gürültü, gerçek bayatlığı (bar hattı bugün durdu) görünmez kılardı.
    """
    bars_dir = config.BARS
    files = sorted(bars_dir.glob("*.csv")) if bars_dir.exists() else []

    # ---- bar çekirdekleri (önbellekli) + evrenin `as_of`u -----------------------------------
    cores: dict[str, dict] = {}
    for p in files:
        # Dosya adı küçük harf ('.' → '-' ile yazılır, bkz. api.py bar indirme yolu); defterler
        # (portfolio/plan/earnings) BÜYÜK harf kullanır. Eşleme tek yönde normalize edilir.
        cores[p.stem.upper()] = _bar_core(p)
    tarihler = [c["last_date"] for c in cores.values() if c["last_date"]]
    as_of = max(tarihler) if tarihler else None

    # ---- defterlerden gelen bağlam ------------------------------------------------------------
    portfolio = store.read_json("portfolio.json", {}) or {}
    pozisyonlar = {str(t).upper() for t in (portfolio.get("positions") or {})}
    silahli = {str((pl or {}).get("ticker") or "").upper()
               for pl in (portfolio.get("armed") or []) if isinstance(pl, dict)}
    silahli.discard("")

    plan_n: dict[str, int] = {}
    plan_son: dict[str, str] = {}
    for satir in store.read_jsonl("trade_plans.jsonl"):
        t = str(satir.get("ticker") or "").upper()
        if not t:
            continue
        plan_n[t] = plan_n.get(t, 0) + 1
        d = str(satir.get("date") or "")
        if d and d > plan_son.get(t, ""):
            plan_son[t] = d

    # Kazanç takvimi earnings modülünün KENDİ yükleyicisinden okunur (mtime önbellekli, biçim
    # toleransı orada yazılı). CSV'yi burada ikinci kez ayrıştırmak, aynı yasanın iki kaynağı
    # demektir — bu depodaki baskın hata deseni tam olarak budur.
    takvim = earnings._load()
    takvim_gunu = as_of or dt.date.today().isoformat()

    fv = store.read_json("finviz_universe.json", {}) or {}
    fv_tickers = {str(t).upper() for t in (fv.get("tickers") or []) if str(t).strip()}
    fv_ekstra = sorted(fv_tickers - set(cores))

    # ---- seans içi ölçüm — YALNIZ silahlı semboller -------------------------------------------
    # barfeed zaten YALNIZ silahlı planların sembollerini izler; 260 sembol için sıcak katmana
    # gitmek hem israf (260 Redis çağrısı/tazeleme) hem de disiplin ihlali olurdu: izlenmeyen bir
    # sembolde "seans içi fiyat" göstermek, olmayan bir ölçümü varmış gibi sunmaktır.
    as_of_ts = barclock.now()
    intraday: dict[str, tuple] = {}
    durumlar: list[str] = []
    for t in sorted(silahli):
        kapanis, damga, durum = _intraday(t, as_of_ts)
        intraday[t] = (kapanis, damga)
        durumlar.append(durum)

    def _satir(ticker: str, source: str, core: dict) -> dict:
        ic_kapanis, ic_damga = intraday.get(ticker, (None, None))
        return {
            "ticker": ticker, "source": source,
            **{k: core[k] for k in _EMPTY_CORE},
            "intraday_close": ic_kapanis, "intraday_ts": ic_damga,
            "position": ticker in pozisyonlar,
            "armed": ticker in silahli,
            "retired": ticker in _data.RETIRED_SYMBOLS,
            "plans_n": plan_n.get(ticker, 0),
            "last_plan_date": plan_son.get(ticker),
            "earnings_date": _next_report(takvim.get(ticker) or [], takvim_gunu),
        }

    rows = [_satir(t, "bars", cores[t]) for t in sorted(cores)]
    rows += [_satir(t, "finviz", dict(_EMPTY_CORE)) for t in fv_ekstra]

    # BAYATLIK YALNIZ YAŞAYAN SEMBOLE SORULUR. Emekli bir sembolün barı as_of'un gerisinde olmak
    # ZORUNDADIR — delist gününden sonra bar YOK. Onu saymak, sayacı hiç düşmeyen bir tabana
    # oturtur ve "8 hisse bayat" uyarısı kalıcı dekora dönüşürdü.
    stale_n = sum(1 for r in rows
                  if not r["retired"] and r["last_date"] and as_of and r["last_date"] < as_of)
    # Yalnız bars'ta GERÇEKTEN CSV'si olan emekliler sayılır: defterde adı geçip diskte karşılığı
    # olmayan bir sembol panoda hiçbir satır üretmiyor demektir, onu saymak sayıyı şişirirdi.
    retired_n = sum(1 for r in rows if r["retired"] and r["source"] == "bars")

    # Rejim ÖZETİ dosyada GERÇEKTEN duran alanlarla sınırlıdır: olmayan bir anahtarı None ile
    # doldurmak, panoda "ölçüldü ve boş çıktı" diye okunurdu (UYDURMA YASAĞI).
    ham_rejim = store.read_json("regime.json", {}) or {}
    rejim = {k: ham_rejim[k] for k in ("date", "regime", "exposure_budget_pct", "distribution_days")
             if k in ham_rejim}

    # BOŞLUĞUN SEBEBİ ÖLÇÜLÜ OLARAK YAZILIR: "seans içi kolon boş" üç AYRI şey olabilir ve üçü
    # farklı iş gerektirir — izlenecek sembol yok (normal), akış hiç yok (Redis/altyapı), akış var
    # ama bayat (bağlantı koptu). Tek bir boş kolon üçünü de aynı sessizliğe indirirdi.
    olculen = sum(1 for r in rows if r["intraday_close"] is not None)
    if not durumlar:
        neden = "silahlı plan yok"
    elif olculen:
        neden = ""
    elif all(d == "akis_yok" for d in durumlar):
        neden = "bar akışı yok — sıcak katman (Redis) okunamıyor"
    else:
        neden = f"bar akışı bayat — en yeni kapanmış bar {STALE_TOL_S} sn'den eski"

    return {
        "as_of": as_of,
        "n": len(rows),
        "stale_n": stale_n,
        "retired_n": retired_n,
        "source": {"bars": len(files), "finviz_extra": len(fv_ekstra),
                   "finviz_reason": fv.get("reason") or ""},
        # `stale_tol_s` DIŞA VERİLİR ki pano eşiği METİNDE tekrar yazmasın: "≤120 sn" cümlesini
        # arayüze elle gömmek, motorun eşiği değişince panonun sessizce yalan söylemesi olurdu.
        "intraday": {"tracked_n": len(durumlar), "measured_n": olculen,
                     "reason": neden, "stale_tol_s": STALE_TOL_S},
        "regime": rejim,
        "rows": rows,
    }

"""WP2 ÖLÇÜM DALGASI — ORTAK ALTYAPI (EDG-2026-012 / -013 / -014).

Şablon: max_olcum/olcum.py + pullback_olcum/olcum.py (kesit boru hattı, takvim kapısı +
bars_integrity dışlaması, 21g blok-bootstrap, ham rvol20 @20 cf-katman IC çivisi, PK4/PK5).

Yasa: repo/state'e HİÇBİR yazım yok (config.STATE sandbox'a çevrilir; barlar CANLI önbellekten
SALT-OKUNUR). UYDURMA YASAĞI: ölçülemeyen her hücre None + neden. KART DIŞINA ÖLÇÜM YOK.

Bu dosya HÜKÜM VERMEZ; yalnız veri/istatistik altyapısıdır.
"""
from __future__ import annotations

import json
import pathlib
import pickle
import shutil
import sys

REPO = pathlib.Path("/Users/erdemozturk/AI-Trading")
SANDBOX = pathlib.Path(__file__).resolve().parent
LIVE_STATE = REPO / "state"
LIVE_BARS = LIVE_STATE / "bars"
EDGAR = REPO / "research" / "edgar_facts"
CACHE = SANDBOX / "_cache"
CACHE.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(REPO))
from meridian import config  # noqa: E402

config.STATE = SANDBOX / "_state"
config.STATE.mkdir(parents=True, exist_ok=True)
config.HISTORY = config.STATE / "history"
config.BARS = LIVE_BARS
assert config.BARS == LIVE_BARS
_LEDGER_SRC = LIVE_STATE / "bars_integrity.json"
if _LEDGER_SRC.exists():                       # kanonik defter yolu sandbox'ta da GERÇEKTEN koşsun
    shutil.copy2(_LEDGER_SRC, config.STATE / "bars_integrity.json")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from meridian import indicators as ind  # noqa: E402
from meridian.adapters import data as dat  # noqa: E402
from meridian.analytics import spearman_ic  # noqa: E402
from meridian.backtest import SECTORS  # noqa: E402

# ------------------------------------------------------------------ şablon sabitleri
BLOCK = 21              # blok-bootstrap: 21 ARDIŞIK GÖZLEM GÜNÜ (şablon)
BOOT = 2000
BOOT_IC = 600
MIN_SLICE = 30          # analytics.IC_MIN_SAMPLE tabanı (şablon)
MALIYET_BPS = 10.0      # üç kartın da cost_model'i "10bps + not"
MIN_KESIT = 50          # bir gözlem gününün kesiti bu kadar sembolden azsa gün kullanılmaz
BAR_MIN_UZUNLUK = ind.TREND_TEMPLATE_WARMUP + 60 + 5   # şablonla aynı taban (252 + en uzun ufuk)
RNG = np.random.default_rng(20260801)

# ------------------------------------------------------------------ hisse serisi sabitleri
ANLIK_ETIKET = ["EntityCommonStockSharesOutstanding",     # dei — kapak, medyan 7g gecikme
                "CommonStockSharesOutstanding"]           # us-gaap — bilanço, ~36g
# Issued KULLANILMAZ (hazine farkı); ağırlıklı-ortalama serileri SEVİYE olarak KULLANILMAZ
# (yalnız split yeniden-beyan KANITI olarak okunur — beyan: build_split_takvimi).
DEI = ANLIK_ETIKET[0]
USGAAP = ANLIK_ETIKET[1]
BIRINCIL_MIN_FILED = 8          # birincil etiket seçimi: dei'de en az bu kadar farklı filed
BAYAT_GUN = 200                 # son filed t'den bu kadar eskiyse as-of None (bayat seri)
SICRAMA_ESIK = 5.0              # kart: "5×'ten büyük sıçrama split ile açıklanamıyorsa şüpheli"
JUMP_TARAMA = 1.4               # split adayı taraması için sıçrama alt sınırı (tespit eşiği)
SNAP_TOL = 0.04                 # split oranı "temiz orana" bu bağıl toleransla oturmalı
_FWD_ORAN = [1.25, 4 / 3, 1.5, 1.6, 2, 2.5, 3, 3.5, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 25, 30]
SPLIT_ADAY_ORAN = sorted(_FWD_ORAN + [1.0 / x for x in _FWD_ORAN])

# ------------------------------------------------------------------ fundamentals sabitleri
GELIR_ONCELIK = ["Revenues",                                             # tutarsizlik.json #1
                 "RevenueFromContractWithCustomerExcludingAssessedTax",
                 "RevenueFromContractWithCustomerIncludingAssessedTax"]
MALIYET_ONCELIK = ["CostOfRevenue", "CostOfGoodsAndServicesSold"]        # kart 014 sırası
AKIS_ETIKET = GELIR_ONCELIK + MALIYET_ONCELIK + ["GrossProfit"]


def _r6(x):
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return None if not np.isfinite(f) else round(f, 6)


# ================================================================== BARLAR (şablon birebir)
def load_bars() -> tuple[dict, dict]:
    """Takvim kapısı (sanitize_bars) + bars_integrity güvensiz-dönem dışlaması.

    İKİ YOL DA KOŞAR: (1) KANONİK defter yolu dat.measurement_bars, (2) HESAPLANAN yol
    dat.integrity_safe_start. pullback_olcum ile birebir aynı.
    """
    per, acc = {}, {"istenen": 0, "dosya_yok": 0, "okunamadi": 0, "kisa": 0, "yuklendi": 0,
                    "hayalet_dusen": 0, "karantina_dusen": 0, "takvim_reddedilen": [],
                    "defter_yolu_dusen": 0, "defter_yolu_sembol": 0,
                    "hesaplanan_dislanan_satir": 0, "iki_yol_ayrisan_sembol": [],
                    "kirilma_sinifi": {}, "kisa_semboller": []}
    for t in dat.REPLAY_UNIVERSE:
        acc["istenen"] += 1
        cp = dat._cache_path(t)
        if not cp.exists():
            acc["dosya_yok"] += 1
            continue
        try:
            raw = pd.read_csv(cp, parse_dates=["date"])
            df, rep = dat.sanitize_bars(raw, t)
        except Exception as e:
            acc["okunamadi"] += 1
            print(f"  ! bar okunamadi {t}: {type(e).__name__}: {e}", file=sys.stderr)
            continue
        acc["hayalet_dusen"] += int(rep.get("ghost_session_dropped") or 0)
        acc["karantina_dusen"] += int(rep.get("unadjusted_quarantined") or 0)
        if rep.get("calendar_mismatch_rows"):
            acc["takvim_reddedilen"].append(t)

        n_once = len(df)
        df = dat.measurement_bars(df, t)                    # (1) KANONİK defter yolu
        d_defter = n_once - len(df)
        acc["defter_yolu_dusen"] += d_defter
        acc["defter_yolu_sembol"] += int(d_defter > 0)

        try:                                                 # (2) HESAPLANAN yol
            ss, brk = dat.integrity_safe_start(df)
        except Exception as e:
            ss, brk = None, []
            print(f"  ! integrity {t}: {type(e).__name__}: {e}", file=sys.stderr)
        for b in (brk or []):
            k = b.get("sinif", "?")
            acc["kirilma_sinifi"][k] = acc["kirilma_sinifi"].get(k, 0) + 1
        if ss:
            keep = df["date"].astype(str).str.slice(0, 10) >= ss
            ek = int((~keep).sum())
            acc["hesaplanan_dislanan_satir"] += ek
            if ek > 0 and d_defter > 0:
                acc["iki_yol_ayrisan_sembol"].append(t)
            df = df.loc[keep].reset_index(drop=True)

        if df is None or len(df) < BAR_MIN_UZUNLUK:
            acc["kisa"] += 1
            acc["kisa_semboller"].append(t)
            continue
        per[t] = df.reset_index(drop=True)
        acc["yuklendi"] += 1
    return per, acc


def bar_paneli(per: dict, ufuklar=(5, 10, 20, 60)) -> dict:
    """Sembol → {dates, close, volume, fwd{h}, chain{h}, rvol20, mom21, med_hacim21}."""
    out = {}
    for t, df in per.items():
        close = df["close"].to_numpy(float)
        vol = df["volume"].to_numpy(float)
        n = len(df)
        dates = df["date"].dt.strftime("%Y-%m-%d").to_numpy()
        rec = {"dates": dates, "close": close, "volume": vol}
        for h in ufuklar:
            f = np.full(n, np.nan)
            f[:n - h] = close[h:] / close[:n - h] - 1.0
            rec[f"fwd{h}"] = f
        ret = np.full(n, np.nan)
        ret[1:] = close[1:] / close[:-1] - 1.0
        lr = pd.Series(np.log1p(ret))
        for h in ufuklar:                                    # PK4 için bağımsız zincir yolu
            rec[f"chain{h}"] = np.expm1(
                lr.shift(-1).rolling(h).sum().shift(-(h - 1))).to_numpy(float)
        rec["rvol20"] = ind.rvol20(df["volume"]).to_numpy(float)
        m21 = np.full(n, np.nan)
        m21[21:] = close[21:] / close[:-21] - 1.0
        rec["mom21"] = m21
        rec["med_hacim21"] = pd.Series(vol).rolling(21, min_periods=21).median().to_numpy(float)
        out[t] = rec
    return out


def bars_cached():
    p = CACHE / "bars.pkl"
    if p.exists():
        with open(p, "rb") as fh:
            return pickle.load(fh)
    per, acc = load_bars()
    pan = bar_paneli(per)
    obj = (pan, acc)
    with open(p, "wb") as fh:
        pickle.dump(obj, fh, protocol=4)
    return obj


# ================================================================== İSTATİSTİK (şablon)
def _blok_kur(dates: np.ndarray):
    uniq, inv = np.unique(dates, return_inverse=True)
    return uniq, inv


def block_boot(stat_fn, dates: np.ndarray, n_boot: int = BOOT) -> dict:
    """21 ARDIŞIK GÖZLEM GÜNÜ blok-bootstrap (şablon). Yeniden örnekleme birimi ardışık gün bloğu:
    aynı günün satırlarının bağımlılığını ve ÖRTÜŞEN ileri getirilerin seri korelasyonunu taşır."""
    uniq, inv = _blok_kur(dates)
    rows_by_date = [np.where(inv == i)[0] for i in range(len(uniq))]
    nd = len(uniq)
    if nd < BLOCK * 3:
        return {"lo": None, "hi": None, "n_gun": nd, "n_boot_gecerli": 0,
                "neden": f"gözlem günü sayısı < {BLOCK * 3} (blok bootstrap için yetersiz)"}
    n_blok = int(np.ceil(nd / BLOCK))
    son_bas = nd - BLOCK
    vals, atlanan = [], 0
    for _ in range(n_boot):
        bas = RNG.integers(0, son_bas + 1, n_blok)
        gun = np.concatenate([np.arange(b, b + BLOCK) for b in bas])[:nd]
        idx = np.concatenate([rows_by_date[g] for g in gun])
        v = stat_fn(idx)
        if v is None or not np.isfinite(v):
            atlanan += 1
            continue
        vals.append(v)
    if len(vals) < n_boot * 0.5:
        return {"lo": None, "hi": None, "n_gun": nd, "n_boot_gecerli": len(vals),
                "neden": "bootstrap tekrarlarının yarısından fazlası ölçülemedi"}
    a = np.asarray(vals, float)
    return {"lo": _r6(np.percentile(a, 2.5)), "hi": _r6(np.percentile(a, 97.5)),
            "n_gun": nd, "n_boot_gecerli": len(vals), "blok": BLOCK, "atlanan": atlanan,
            "neden": None}


def mean_block_boot(y: np.ndarray, dates: np.ndarray, n_boot: int = BOOT, blok: int = BLOCK) -> dict:
    """block_boot'un ORTALAMA istatistiği için cebirsel özdeş hızlı yolu (PK5-C bunu sınar)."""
    uniq, inv = np.unique(dates, return_inverse=True)
    nd = len(uniq)
    if nd < blok * 3:
        return {"lo": None, "hi": None, "n_gun": nd, "n_boot_gecerli": 0,
                "neden": f"gözlem günü sayısı < {blok * 3} (blok bootstrap için yetersiz)"}
    sums = np.bincount(inv, weights=y, minlength=nd)
    cnts = np.bincount(inv, minlength=nd).astype(float)
    n_blok = int(np.ceil(nd / blok))
    son_bas = nd - blok
    ofs = np.arange(blok)
    vals, atlanan = [], 0
    for _ in range(n_boot):
        bas = RNG.integers(0, son_bas + 1, n_blok)
        gun = (bas[:, None] + ofs[None, :]).ravel()[:nd]
        c = cnts[gun].sum()
        if c <= 0:
            atlanan += 1
            continue
        vals.append(sums[gun].sum() / c)
    if len(vals) < n_boot * 0.5:
        return {"lo": None, "hi": None, "n_gun": nd, "n_boot_gecerli": len(vals),
                "neden": "bootstrap tekrarlarının yarısından fazlası ölçülemedi"}
    a = np.asarray(vals, float)
    return {"lo": _r6(np.percentile(a, 2.5)), "hi": _r6(np.percentile(a, 97.5)),
            "n_gun": nd, "n_boot_gecerli": len(vals), "blok": blok, "atlanan": atlanan,
            "neden": None}


def mean_with_ci(y: np.ndarray, dates: np.ndarray, n_boot: int = BOOT, blok: int = BLOCK) -> dict:
    n = int(len(y))
    if n < MIN_SLICE:
        return {"n": n, "ort": None, "ci": None, "anlamli": None, "pozitif_anlamli": None,
                "negatif_anlamli": None, "neden": f"n<{MIN_SLICE}"}
    ci = mean_block_boot(y, dates, n_boot, blok)
    ort = float(np.mean(y))
    return {"n": n, "ort": _r6(ort), "medyan": _r6(np.median(y)),
            "std": _r6(np.std(y, ddof=1)), "pozitif_oran": _r6(float((y > 0).mean())),
            "ci": None if ci["lo"] is None else {"lo": ci["lo"], "hi": ci["hi"], "seviye": 0.95},
            "ci_meta": ci,
            "anlamli": None if ci["lo"] is None else bool(ci["lo"] > 0 or ci["hi"] < 0),
            "pozitif_anlamli": None if ci["lo"] is None else bool(ci["lo"] > 0),
            "negatif_anlamli": None if ci["lo"] is None else bool(ci["hi"] < 0),
            "maliyet_dusulmus_ort": _r6(ort - MALIYET_BPS / 10000.0),
            "neden": None}


def fark_with_ci(yA: np.ndarray, dA: np.ndarray, yB: np.ndarray, dB: np.ndarray,
                 n_boot: int = BOOT, blok: int = BLOCK) -> dict:
    """A ve B dilimlerinin ORTALAMA FARKI (A−B) + 21g blok CI.

    EŞLEŞTİRME: bootstrap AYNI gün dizisini iki dilime de uygular (ortak takvim). Böylece fark
    istatistiği gün-etkisinden arınır; artımlılık (013) ve yayılım (014) bacakları bunu okur."""
    uniq = np.unique(np.concatenate([dA, dB]))
    nd = len(uniq)
    if nd < blok * 3:
        return {"nA": int(len(yA)), "nB": int(len(yB)), "fark": None, "ci": None,
                "neden": f"ortak gözlem günü < {blok * 3}"}
    ia = np.searchsorted(uniq, dA)
    ib = np.searchsorted(uniq, dB)
    sA = np.bincount(ia, weights=yA, minlength=nd)
    cA = np.bincount(ia, minlength=nd).astype(float)
    sB = np.bincount(ib, weights=yB, minlength=nd)
    cB = np.bincount(ib, minlength=nd).astype(float)
    n_blok = int(np.ceil(nd / blok))
    son_bas = nd - blok
    ofs = np.arange(blok)
    vals, atlanan = [], 0
    for _ in range(n_boot):
        bas = RNG.integers(0, son_bas + 1, n_blok)
        gun = (bas[:, None] + ofs[None, :]).ravel()[:nd]
        ca, cb = cA[gun].sum(), cB[gun].sum()
        if ca <= 0 or cb <= 0:
            atlanan += 1
            continue
        vals.append(sA[gun].sum() / ca - sB[gun].sum() / cb)
    if len(vals) < n_boot * 0.5:
        return {"nA": int(len(yA)), "nB": int(len(yB)), "fark": None, "ci": None,
                "neden": "bootstrap tekrarlarının yarısından fazlası ölçülemedi"}
    a = np.asarray(vals, float)
    lo, hi = _r6(np.percentile(a, 2.5)), _r6(np.percentile(a, 97.5))
    return {"nA": int(len(yA)), "nB": int(len(yB)),
            "fark": _r6(float(np.mean(yA)) - float(np.mean(yB))),
            "ci": {"lo": lo, "hi": hi, "seviye": 0.95},
            "n_gun": nd, "blok": blok, "n_boot_gecerli": len(vals), "atlanan": atlanan,
            "anlamli": bool(lo > 0 or hi < 0), "pozitif_anlamli": bool(lo > 0),
            "negatif_anlamli": bool(hi < 0), "neden": None}


def spearman_np(x, y):
    """Spearman ρ — scipy YOK (ortamda kurulu değil); rütbe dönüşümü + Pearson ile hesaplanır.
    Bağlar için ORTALAMA rütbe (pandas rank varsayılanı) kullanılır."""
    a = pd.Series(np.asarray(x, float))
    b = pd.Series(np.asarray(y, float))
    m = a.notna() & b.notna()
    if int(m.sum()) < 3:
        return None
    ra = a[m].rank().to_numpy()
    rb = b[m].rank().to_numpy()
    if ra.std() == 0 or rb.std() == 0:
        return None
    return float(np.corrcoef(ra, rb)[0, 1])


def ic_with_ci(x: np.ndarray, y: np.ndarray, dates: np.ndarray, n_boot: int = BOOT_IC) -> dict:
    if len(x) < MIN_SLICE:
        return {"ic": None, "n": int(len(x)), "ci": None, "anlamli": None, "neden": f"n<{MIN_SLICE}"}
    ic = spearman_ic(list(zip(x.tolist(), y.tolist())))
    if ic is None:
        return {"ic": None, "n": int(len(x)), "ci": None, "anlamli": None,
                "neden": "rütbe değişimi yok"}

    def _stat(idx):
        v = spearman_ic(list(zip(x[idx].tolist(), y[idx].tolist())))
        return None if v is None else float(v)

    ci = block_boot(_stat, dates, n_boot=n_boot)
    return {"ic": round(float(ic), 4), "n": int(len(x)),
            "ci": None if ci["lo"] is None else {"lo": round(ci["lo"], 4),
                                                 "hi": round(ci["hi"], 4), "seviye": 0.95},
            "ci_meta": ci,
            "anlamli": None if ci["lo"] is None else bool(ci["lo"] > 0 or ci["hi"] < 0),
            "neden": None}


# ================================================================== HİSSE SAYIMI (PIT as-of)
def _snap(r: float, tol: float = SNAP_TOL):
    best, bd = None, 9e99
    for c in SPLIT_ADAY_ORAN:
        d = abs(r - c) / c
        if d < bd:
            bd, best = d, c
    return (best, bd) if bd <= tol else (None, bd)


def _shares_ham() -> pd.DataFrame:
    S = pd.read_csv(EDGAR / "shares_outstanding.csv.gz")
    S["start"] = S["start"].fillna("")
    return S


def build_split_takvimi(S: pd.DataFrame, birincil: dict, sadece_anlik_kanit=False) -> tuple[dict, dict]:
    """SPLIT TAKVİMİ — EDGAR'IN KENDİ GERİYE-DÖNÜK YENİDEN-BEYANINDAN türetilir.

    NEDEN BAR'DAN DEĞİL (beyan): state/bars/*.csv SPLIT-DÜZELTİLMİŞ bir seridir (FMP
    /historical-price-eod/full + Cboe, ikisi de split-adjusted). NVDA 2024-06-10, AVGO 2024-07-15,
    AAPL 2020-08-31, TSLA 2022-08-25, GOOGL 2022-07-18 bar serilerinde HİÇBİR fiyat/hacim sıçraması
    YOKTUR (doğrudan sınandı, sonuc.json → split_takvimi.bar_serisi_duz_mu). Yani bölünme günü bar
    verisinden OKUNAMAZ; brief'in önerdiği yol bu veri kümesinde MEVCUT DEĞİL. Yerine kullanılan yol
    kendi içinde PIT-temizdir:

      (a) TESPİT — birincil as-of serisinde ardışık iki dosyalama arasındaki oran >=1.4 veya <=1/1.4
          ise ADAY sıçrama; oran "temiz" bir bölünme oranına (%4 tolerans) oturmalı.
      (b) DOĞRULAMA — aynı sembolde HERHANGİ bir (tag,start,end) üçlüsünün DAHA ÖNCE dosyalanmış
          değeri, sıçrama dosyalamasında ~aynı oranla yeniden beyan edilmiş olmalı. Bölünme geçmiş
          dönemleri geriye dönük düzeltir; BİRLEŞME/İHRAÇ DÜZELTMEZ. Ayrım budur.
      (c) Bölünmenin "yürürlük" tarihi = sıçramanın görüldüğü DOSYALAMA günü g. Ölçüm bunu ister:
          as-of değerin bazı tam o gün değişir. Ex-date'e ihtiyaç YOKTUR (aşağıdaki dönüşüm hem
          ex-date ile g arasındaki pencerede hem dışında BİREBİR doğrudur).

    Ağırlıklı-ortalama etiketleri burada YALNIZ (b) KANITI olarak okunur, seviye olarak ASLA
    (kart 012: "ağırlıklı-ortalama serileri KULLANILMAZ"). `sadece_anlik_kanit=True` ile kanıt
    yalnız anlık etiketlerden toplanır — iki takvimin aynı çıktığı ayrıca muhasebeleşir.
    """
    kanit = S.sort_values(["symbol", "tag", "start", "end", "filed"])
    if sadece_anlik_kanit:
        kanit = kanit[kanit.donem_turu == "anlik"]
    g = kanit.groupby(["symbol", "tag", "start", "end"], sort=False)
    pv, pf = g["val"].shift(1), g["filed"].shift(1)
    EV = pd.DataFrame({"symbol": kanit.symbol.to_numpy(), "f_old": pf.to_numpy(),
                       "f_new": kanit.filed.to_numpy(), "r": (kanit.val / pv).to_numpy()}).dropna()
    EV = EV[(EV.r >= JUMP_TARAMA) | (EV.r <= 1 / JUMP_TARAMA)]
    ev_by_sym = {s: d for s, d in EV.groupby("symbol")}

    takvim, acc = {}, {"aday_sicrama": 0, "snap_olmayan": 0, "kanitsiz": 0, "kabul": 0,
                       "kabul_sembol": 0, "kirik_sinir": 0, "olcek_gidis_donus": 0,
                       "kabul_listesi": [], "kirik_listesi": [], "gidis_donus_listesi": []}
    for sym, tg in birincil.items():
        sub = S[(S.symbol == sym) & (S.tag == tg) & (S.donem_turu == "anlik")]
        sub = sub.sort_values(["filed", "end"]).groupby("filed", as_index=False).last()
        v = sub.val.to_numpy(float)
        f = sub.filed.to_numpy()
        ev = ev_by_sym.get(sym)
        olay, kirik, aday_kirik = [], [], []
        for i in range(1, len(v)):
            r = v[i] / v[i - 1]
            if 1 / JUMP_TARAMA < r < JUMP_TARAMA:
                continue
            acc["aday_sicrama"] += 1
            sn, sap = _snap(r)
            n_kanit, kanit_r = 0, None
            if ev is not None and sn is not None:
                e = ev[(ev.f_old < f[i]) & (ev.f_new >= f[i])]
                ok = e[(e.r / r).between(0.9, 1.1)]
                n_kanit = int(len(ok))
                kanit_r = float(ok.r.median()) if n_kanit else None
            if sn is None:
                acc["snap_olmayan"] += 1
            elif n_kanit == 0:
                acc["kanitsiz"] += 1
            if sn is not None and n_kanit > 0:
                olay.append({"filed": str(f[i]), "oran": sn, "ham_oran": _r6(r),
                             "kanit_n": n_kanit, "kanit_oran": _r6(kanit_r)})
                acc["kabul"] += 1
                acc["kabul_listesi"].append({"symbol": sym, "filed": str(f[i]), "oran": sn,
                                             "ham_oran": _r6(r), "kanit_n": n_kanit})
            else:
                aday_kirik.append((i, r, sn, n_kanit))
        # kart kuralı: split ile AÇIKLANAMAYAN >=5× sıçrama → şüpheli işaret
        for i, r, sn, n_kanit in aday_kirik:
            if r >= SICRAMA_ESIK or r <= 1 / SICRAMA_ESIK:
                kirik.append({"filed": str(f[i]), "oran": _r6(r), "ham_oran": float(r),
                              "snap": sn, "kanit_n": n_kanit, "idx": i})
                acc["kirik_sinir"] += 1
                acc["kirik_listesi"].append({"symbol": sym, "filed": str(f[i]), "oran": _r6(r)})
        # ölçek-hatası GİDİŞ-DÖNÜŞ: >=5× sıçrama, 6 dosyalama içinde ~1/oran ile geri dönüyorsa
        gecersiz = []
        for a in range(len(kirik)):
            for b in range(a + 1, len(kirik)):
                if kirik[b]["idx"] - kirik[a]["idx"] > 6:
                    break
                if abs(kirik[a]["ham_oran"] * kirik[b]["ham_oran"] - 1.0) < 0.1:
                    gecersiz.append((kirik[a]["idx"], kirik[b]["idx"]))
                    acc["olcek_gidis_donus"] += 1
                    acc["gidis_donus_listesi"].append(
                        {"symbol": sym, "bas": kirik[a]["filed"], "son": kirik[b]["filed"],
                         "oran": kirik[a]["oran"]})
                    break
        takvim[sym] = {"olaylar": olay, "kirik": [k["filed"] for k in kirik],
                       "gecersiz_aralik": gecersiz}
        if olay:
            acc["kabul_sembol"] += 1
    return takvim, acc


class HisseSerisi:
    """Sembol başına PIT as-of hisse sayımı + split-normalize edilmiş GÜNCEL BAZ karşılığı.

    GÜNCEL BAZ DÖNÜŞÜMÜ (beyan): bir dosyalama f'de bildirilen sayı, o gün geçerli hisse biriminde
    yazılmıştır. shares_guncel(t) = as_of_val(t) × B_son / B(f_t), burada B(f) = f gününe kadar
    (dahil) kabul edilmiş bölünme oranlarının çarpımı, B_son hepsinin çarpımı. Bu dönüşüm
      · net ihracı bölünmeden arındırır (iki uç aynı bazda),
      · devir hızını doğru yapar (bar hacmi de GÜNCEL bazda split-düzeltilmiş),
      · ex-date ile ilk-yansıtan-dosyalama arasındaki pencerede DE doğrudur (pay ve payda aynı bazda).
    """

    def __init__(self, birincil_tag, filed, val, gecersiz_mask, B, B_son, kirik_filed, kaynak_tag):
        self.birincil_tag = birincil_tag
        self.fiziksel = np.zeros(len(filed), bool)   # fiziksel bekçi işareti (ayrı neden kodu)
        self.filed = filed                  # sorted np.array[str]
        self.val = val                      # np.array[float]
        self.gecersiz = gecersiz_mask       # np.array[bool] — ölçek hatası penceresi
        self.B = B                          # np.array[float] — o dosyalamanın baz çarpanı
        self.B_son = B_son
        self.kirik_filed = kirik_filed      # list[str]
        self.kaynak_tag = kaynak_tag        # np.array[str] — hangi etiketten geldi

    def idx_asof(self, t_arr: np.ndarray) -> np.ndarray:
        return np.searchsorted(self.filed, t_arr, side="right") - 1

    def asof(self, t_arr: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """→ (guncel_baz_deger, kaynak_filed, neden_kodu). Ölçülemeyen hücre NaN + neden kodu."""
        i = self.idx_asof(t_arr)
        n = len(t_arr)
        out = np.full(n, np.nan)
        srcf = np.full(n, "", dtype=object)
        neden = np.full(n, "", dtype=object)
        ok = i >= 0
        neden[~ok] = "dosyalama_yok"
        ii = i[ok]
        f = self.filed[ii]
        srcf[ok] = f
        yas = (pd.to_datetime(t_arr[ok]) - pd.to_datetime(f)).days
        bayat = yas > BAYAT_GUN
        gec = self.gecersiz[ii]
        deger = self.val[ii] * self.B_son / self.B[ii]
        deger = np.where(bayat | gec, np.nan, deger)
        fz = self.fiziksel[ii]
        nd = np.where(gec & fz, "olcek_hatasi_fiziksel_imkansiz",
                      np.where(gec, "olcek_hatasi_gidis_donus",
                               np.where(bayat, "bayat_seri", "")))
        out[ok] = deger
        neden[ok] = nd
        return out, srcf, neden

    def kirik_arada(self, f1: np.ndarray, f2: np.ndarray) -> np.ndarray:
        """(f1, f2] aralığında açıklanamayan >=5× sınır var mı."""
        if not self.kirik_filed:
            return np.zeros(len(f1), bool)
        kb = np.array(sorted(self.kirik_filed))
        a = np.searchsorted(kb, f1, side="right")
        b = np.searchsorted(kb, f2, side="right")
        return b > a


def build_hisse(S: pd.DataFrame) -> tuple[dict, dict, dict]:
    """→ (seriler, birincil_tag, muhasebe). Kart 012 features_asof kuralları BİREBİR."""
    acc = {"ham_satir": int(len(S))}
    s = S[(S.unit == "shares") & (S.val > 0)].copy()
    acc["birim_veya_val_dusen"] = int(len(S) - len(s))
    a = s[(s.donem_turu == "anlik") & (s.tag.isin(ANLIK_ETIKET))]
    acc["anlik_iki_etiket_satir"] = int(len(a))
    # birincil etiket seçimi (kart: dei → us-gaap Outstanding)
    say = a.groupby(["symbol", "tag"]).filed.nunique().unstack(fill_value=0)
    for c in ANLIK_ETIKET:
        if c not in say.columns:
            say[c] = 0
    birincil = {}
    for sym, row in say.iterrows():
        if row[DEI] >= BIRINCIL_MIN_FILED:
            birincil[sym] = DEI
        elif row[USGAAP] > 0:
            birincil[sym] = USGAAP
        elif row[DEI] > 0:
            birincil[sym] = DEI
    acc["birincil_dei"] = int(sum(1 for v in birincil.values() if v == DEI))
    acc["birincil_usgaap"] = int(sum(1 for v in birincil.values() if v == USGAAP))
    acc["seri_olmayan_sembol"] = sorted(set(dat.REPLAY_UNIVERSE) - set(birincil))

    takvim, tk_acc = build_split_takvimi(s, birincil)
    takvim_anlik, tk_acc2 = build_split_takvimi(s, birincil, sadece_anlik_kanit=True)
    ayni = sorted(set(takvim) | set(takvim_anlik))
    tk_acc["yalniz_anlik_kanitla_ayni_mi"] = bool(all(
        [o["filed"] for o in takvim[k]["olaylar"]] == [o["filed"] for o in takvim_anlik[k]["olaylar"]]
        for k in ayni))
    tk_acc["yalniz_anlik_kanitla_kabul_n"] = tk_acc2["kabul"]

    seriler = {}
    yedek_kullanim = 0
    for sym, tg in birincil.items():
        sub = a[(a.symbol == sym) & (a.tag == tg)]
        sub = sub.sort_values(["filed", "end"]).groupby("filed", as_index=False).last()
        sub = sub.sort_values("filed")
        filed = sub.filed.to_numpy()
        val = sub.val.to_numpy(float)
        tag_arr = np.full(len(filed), tg, dtype=object)
        # YEDEK ETİKET: birincilde >BAYAT_GUN boşluk varsa o boşluğa diğer etiketten kayıt eklenir
        oth = USGAAP if tg == DEI else DEI
        o = a[(a.symbol == sym) & (a.tag == oth)]
        if len(o):
            o = o.sort_values(["filed", "end"]).groupby("filed", as_index=False).last()
            of, ov = o.filed.to_numpy(), o.val.to_numpy(float)
            ekle_f, ekle_v = [], []
            for k in range(len(of)):
                j = np.searchsorted(filed, of[k], side="right") - 1
                onceki = filed[j] if j >= 0 else None
                sonraki = filed[j + 1] if j + 1 < len(filed) else None
                bosluk_bas = (pd.Timestamp(of[k]) - pd.Timestamp(onceki)).days if onceki else 10 ** 6
                if bosluk_bas > BAYAT_GUN and (sonraki is None or of[k] < sonraki):
                    ekle_f.append(of[k])
                    ekle_v.append(ov[k])
            if ekle_f:
                yedek_kullanim += len(ekle_f)
                filed = np.concatenate([filed, np.array(ekle_f)])
                val = np.concatenate([val, np.array(ekle_v)])
                tag_arr = np.concatenate([tag_arr, np.full(len(ekle_f), oth, dtype=object)])
                sr = np.argsort(filed, kind="stable")
                filed, val, tag_arr = filed[sr], val[sr], tag_arr[sr]
        tk = takvim.get(sym, {"olaylar": [], "kirik": [], "gecersiz_aralik": []})
        of_ = np.array([o["filed"] for o in tk["olaylar"]])
        orn = np.array([o["oran"] for o in tk["olaylar"]], float)
        if len(of_):
            cum = np.cumprod(orn)
            pos = np.searchsorted(of_, filed, side="right")
            B = np.concatenate([[1.0], cum])[pos]
            B_son = float(cum[-1])
        else:
            B = np.ones(len(filed))
            B_son = 1.0
        gec = np.zeros(len(filed), bool)
        # geçersiz aralık indeksleri BİRİNCİL seri indekslerinde tanımlı; filed üzerinden eşle
        if tk["gecersiz_aralik"]:
            psub = S[(S.symbol == sym) & (S.tag == tg) & (S.donem_turu == "anlik") &
                     (S.unit == "shares") & (S.val > 0)]
            pf = psub.sort_values(["filed", "end"]).groupby("filed", as_index=False).last() \
                .sort_values("filed").filed.to_numpy()
            for i0, i1 in tk["gecersiz_aralik"]:
                lo, hi = pf[i0], pf[i1]
                gec |= (filed >= lo) & (filed < hi)
        seriler[sym] = HisseSerisi(tg, filed, val, gec, B, B_son, tk["kirik"], tag_arr)
    acc["yedek_etiket_eklenen_kayit"] = yedek_kullanim
    acc["split_takvimi"] = tk_acc
    return seriler, birincil, acc


FIZIKSEL_TURNOVER_TAVAN = 1.0   # medyan-21g hacim, dolaşımdaki hissenin TAMAMINI aşamaz


def fiziksel_bekci(seriler: dict, pan: dict) -> dict:
    """ÖLÇEK-HATASI BEKÇİSİ (VERİ KALİTESİ — sinyal eşiği DEĞİL, beyanlı).

    NEDEN GEREKLİ: kartın ">=5× sıçrama" kuralı bir sıçramanın HANGİ tarafının bozuk olduğunu
    söylemez ve serinin BAŞINDAKİ bozuk değeri (yeni kayıtçı kapak sayfasında 100 hisse yazan
    kabuk kaydı) hiç yakalamaz. Ölçülen vakalar: CSX 2011-04-20 → 3 hisse, ETN 2012-11 → 100,
    BKR 2017-08 → 100, SPG 2013-02 → 8.000, LIN 2017-10 → 25.000, ROKU IPO öncesi tek sınıf.
    Bunlar devir hızını 10^4 katına çıkarıyordu.

    KURAL: bir as-of kaydının geçerlilik penceresinde [filed_j, filed_{j+1}) medyan-21g hacmin
    MEDYANI, o kaydın güncel-baz hisse sayısını AŞIYORSA (implied turnover > 1) kayıt GEÇERSİZDİR.
    Bu bir eşik ayarı değil FİZİKSEL İMKÂNSIZLIKTIR: bir şirketin günlük medyan işlem hacmi
    dolaşımdaki hissesinin tamamını geçemez. Kartın hiçbir eşiğine dokunmaz; yalnız uydurma
    değerin ölçüme girmesini engeller (None + neden).
    """
    acc = {"tavan": FIZIKSEL_TURNOVER_TAVAN, "gecersiz_kayit": 0, "etkilenen_sembol": {},
           "bar_yok_sembol": 0}
    for sym, s in seriler.items():
        v = pan.get(sym)
        if v is None:
            acc["bar_yok_sembol"] += 1
            continue
        d, mh = v["dates"], v["med_hacim21"]
        deger = s.val * s.B_son / s.B
        lo = np.searchsorted(d, s.filed, side="left")
        hi = np.concatenate([lo[1:], [len(d)]])
        n_yeni = 0
        for j in range(len(s.filed)):
            if s.gecersiz[j] or not np.isfinite(deger[j]) or deger[j] <= 0:
                continue
            seg = mh[lo[j]:max(hi[j], lo[j] + 1)]
            seg = seg[np.isfinite(seg)]
            if len(seg) == 0:
                continue
            if float(np.median(seg)) / deger[j] > FIZIKSEL_TURNOVER_TAVAN:
                s.gecersiz[j] = True
                s.fiziksel[j] = True
                n_yeni += 1
        if n_yeni:
            acc["gecersiz_kayit"] += n_yeni
            acc["etkilenen_sembol"][sym] = {"kayit": n_yeni,
                                            "ornek_deger": float(np.nanmin(deger))}
    return acc


# ================================================================== FUNDAMENTALS (PIT as-of)
class TemelSeri:
    def __init__(self, filed, gp, assets, gpa, kaynak, end):
        self.filed, self.gp, self.assets, self.gpa = filed, gp, assets, gpa
        self.kaynak, self.end = kaynak, end

    def asof(self, t_arr: np.ndarray):
        i = np.searchsorted(self.filed, t_arr, side="right") - 1
        n = len(t_arr)
        out = np.full(n, np.nan)
        srcf = np.full(n, "", dtype=object)
        neden = np.full(n, "", dtype=object)
        ok = i >= 0
        neden[~ok] = "FY_dosyalama_yok"
        ii = i[ok]
        f = self.filed[ii]
        srcf[ok] = f
        yas = (pd.to_datetime(t_arr[ok]) - pd.to_datetime(f)).days
        bayat = yas > 550                      # yıllık kayıt: 1,5 yıldan eskiyse bayat
        v = np.where(bayat, np.nan, self.gpa[ii])
        out[ok] = v
        neden[ok] = np.where(bayat, "bayat_FY_serisi", "")
        return out, srcf, neden


def build_temel() -> tuple[dict, dict]:
    """gp(t) = GrossProfit(filed<=t son FY); yoksa Revenues−CostOfRevenue|CostOfGoodsAndServicesSold.
    assets(t) AYNI dosyalamadan (aynı FY sonu); gpa = gp/assets. Etiket öncelikleri kart 014'ten."""
    F = pd.read_csv(EDGAR / "fundamentals.csv.gz")
    acc = {"ham_satir": int(len(F))}
    f = F[(F.unit == "USD") & (F.val > 0)].copy()
    acc["birim_veya_val_dusen"] = int(len(F) - len(f))
    acc["AFN_dusen"] = int((F.unit != "USD").sum())
    acc["grossprofit_val_le0_dusen"] = int(((F.tag == "GrossProfit") & (F.val <= 0)).sum())
    akis = f[(f.donem_turu == "yillik") & (f.tag.isin(AKIS_ETIKET))]
    varlik = f[(f.donem_turu == "anlik") & (f.tag == "Assets")]
    acc["FY_akis_satir"] = int(len(akis))
    acc["assets_anlik_satir"] = int(len(varlik))

    piv = akis.pivot_table(index=["symbol", "filed", "start", "end"], columns="tag",
                           values="val", aggfunc="last").reset_index()
    for c in AKIS_ETIKET:
        if c not in piv.columns:
            piv[c] = np.nan
    gp = np.full(len(piv), np.nan)
    kaynak = np.full(len(piv), "", dtype=object)
    gpv = piv["GrossProfit"].to_numpy(float)
    have = np.isfinite(gpv)
    gp[have] = gpv[have]
    kaynak[have] = "GrossProfit"
    rev = np.full(len(piv), np.nan)
    revtag = np.full(len(piv), "", dtype=object)
    for tg in GELIR_ONCELIK:
        v = piv[tg].to_numpy(float)
        m = (~np.isfinite(rev)) & np.isfinite(v)
        rev[m], revtag[m] = v[m], tg
    cost = np.full(len(piv), np.nan)
    costtag = np.full(len(piv), "", dtype=object)
    for tg in MALIYET_ONCELIK:
        v = piv[tg].to_numpy(float)
        m = (~np.isfinite(cost)) & np.isfinite(v)
        cost[m], costtag[m] = v[m], tg
    m2 = (~have) & np.isfinite(rev) & np.isfinite(cost)
    gp[m2] = rev[m2] - cost[m2]
    kaynak[m2] = np.array([f"{a}-{b}" for a, b in zip(revtag[m2], costtag[m2])], dtype=object)
    piv["gp"], piv["gp_kaynak"] = gp, kaynak
    acc["gp_grossprofit_etiketi"] = int(have.sum())
    acc["gp_gelir_eksi_maliyet"] = int(m2.sum())
    piv = piv[np.isfinite(piv.gp.to_numpy(float))]

    # Assets: kart "assets(t) aynı filed'dan". BİRİNCİL eşleşme aynı (symbol, filed, end);
    # aynı DOSYALAMADA o `end` yoksa AYNI dosyalamanın flow-end'ini AŞMAYAN en yakın `end`i
    # (karşılaştırmalı sütun). BAŞKA bir dosyalamaya ASLA düşülmez — kart metni bunu yasaklıyor.
    va = varlik.groupby(["symbol", "filed", "end"], as_index=False).val.last() \
        .rename(columns={"val": "assets"})
    m = piv.merge(va, on=["symbol", "filed", "end"], how="left")
    acc["assets_ayni_dosyalama_ayni_end"] = int(m.assets.notna().sum())
    eksik = m.assets.isna()
    acc["assets_ayni_end_eslesmeyen"] = int(eksik.sum())
    acc["assets_ayni_dosyalama_yakin_end"] = 0
    if eksik.any():
        harita = {}
        for (sy, fl), gsub in va.groupby(["symbol", "filed"], sort=False):
            gsub = gsub.sort_values("end")
            harita[(sy, fl)] = (gsub["end"].to_numpy(), gsub["assets"].to_numpy(float))
        idxs, vals = [], []
        for i, sy, fl, en in zip(m.index[eksik], m.loc[eksik, "symbol"],
                                 m.loc[eksik, "filed"], m.loc[eksik, "end"]):
            h = harita.get((sy, fl))
            if h is None:
                continue
            k = int(np.searchsorted(h[0], en, side="right")) - 1
            if k >= 0:
                idxs.append(i)
                vals.append(h[1][k])
        if idxs:
            m.loc[idxs, "assets"] = vals
            acc["assets_ayni_dosyalama_yakin_end"] = len(idxs)
    acc["assets_eslesmeyen"] = int(m.assets.isna().sum())
    m = m[m.assets.notna() & (m.assets > 0)]
    m["gpa"] = m.gp / m.assets
    m = m.sort_values(["symbol", "filed", "end"])
    acc["gozlem_satir"] = int(len(m))

    seriler = {}
    for sym, sub in m.groupby("symbol"):
        sub = sub.groupby("filed", as_index=False).last().sort_values("filed")
        seriler[sym] = TemelSeri(sub.filed.to_numpy(), sub.gp.to_numpy(float),
                                 sub.assets.to_numpy(float), sub.gpa.to_numpy(float),
                                 sub.gp_kaynak.to_numpy(), sub.end.to_numpy())
    acc["sembol_n"] = len(seriler)
    acc["evren_kesisim_n"] = len(set(seriler) & set(dat.REPLAY_UNIVERSE))
    acc["gp_kaynak_dagilimi"] = m.gp_kaynak.value_counts().to_dict()
    return seriler, acc


# ================================================================== GÖZLEM TAKVİMİ
def ortak_takvim(pan: dict) -> np.ndarray:
    d = sorted(set().union(*[set(v["dates"].tolist()) for v in pan.values()]))
    return np.array(d)


def ay_sonu_gunleri(takvim: np.ndarray) -> np.ndarray:
    s = pd.Series(takvim)
    ay = s.str.slice(0, 7)
    return s.groupby(ay).max().to_numpy()


def kesit_fazlasi(D: pd.DataFrame, taban_kol: str, h: int) -> pd.DataFrame:
    """Aynı-gün taban ortalaması (ders #3) — fazla = ham ileri getiri − o günün taban ortalaması."""
    g = D.loc[D[taban_kol], ["date", f"fwd{h}"]].dropna().groupby("date")[f"fwd{h}"]
    ort, n = g.mean(), g.size()
    return ort, n


def _leak_kontrol(filed_arr, t_arr) -> int:
    """PIT ihlali sayacı: seçilen kaydın filed'ı gözlem gününden BÜYÜK olamaz."""
    m = (filed_arr != "") & (filed_arr > t_arr)
    return int(np.sum(m))


def json_yaz(p: pathlib.Path, obj) -> None:
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str))

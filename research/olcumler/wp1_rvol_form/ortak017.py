"""EDG-2026-017 · rvol FORM REVİZYONU — ORTAK ÖLÇÜM ALTYAPISI.

Kart: research/cards/EDG-2026-017-rvol-form-revizyonu.yaml (status: registered).
KARTA DOKUNULMAZ · HÜKÜM VERİLMEZ · EŞİK ÖLÇÜMDEN SONRA DEĞİŞMEZ.

KÖKEN (yeniden kullanılan altyapı, kartın "EDG-002 altyapısı varsa yeniden kullanılır" notu):
  scratchpad/wp2_olcum/ortak.py + pk.py + k016.py  (EDG-2026-012/-013/-014/-016 dalgası,
  2026-08-01). Bar yolu, 21g blok-bootstrap, hızlı Spearman ve pozitif-kontrol çivisi ORADAN
  BİREBİR alındı; bu dosya onların KOPYASIDIR, yeniden tanımı DEĞİL. Ek olan tek şey
  `temiz_evren_tabani` (Ders #4 kıyas temizliği) — kartın guard'ı onu ZORUNLU kılıyor.

YASALAR
  * repo/state'e HİÇBİR yazım yok: config.STATE kum havuzuna çevrilir, barlar CANLI önbellekten
    SALT-OKUNUR okunur.
  * UYDURMA YASAĞI: ölçülemeyen her hücre None + neden.
  * Motor ÇALIŞMA AĞACINDAN KUM HAVUZUNA KOPYALANIR ve dosya bazında sha256 damgalanır: ölçüm
    anında repoda başka ajanlar uçuştaydı (s1_retro'nun "eşzamanlı ajan etkisi" şerhi) ve canlı
    dosyaların ölçüm ortasında değişmesi sayıları sessizce kaydırırdı.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import pickle
import shutil
import sys

REPO = pathlib.Path("/Users/erdemozturk/AI-Trading")
KLASOR = pathlib.Path(__file__).resolve().parent            # research/olcumler/wp1_rvol_form
CALISMA = pathlib.Path("/private/tmp/claude-501/-Users-erdemozturk-AI-Trading/"
                       "70939c98-2d7b-4bea-aa38-9223f540792e/scratchpad/wp1_rvol_form_calisma")
LIVE_STATE = REPO / "state"
LIVE_BARS = LIVE_STATE / "bars"
MOTOR = CALISMA / "_motor"
CACHE = CALISMA / "_cache"
for _p in (CALISMA, CACHE):
    _p.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------ MOTOR ANLIK GÖRÜNTÜSÜ
def _motor_kopyala() -> dict:
    """meridian paketini kum havuzuna kopyala ve sha256 damgala (repo ↔ kopya)."""
    src = REPO / "meridian"
    if MOTOR.exists():
        shutil.rmtree(MOTOR)
    MOTOR.mkdir(parents=True)
    shutil.copytree(src, MOTOR / "meridian",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    damga = {}
    for p in sorted(src.rglob("*.py")):
        rel = str(p.relative_to(src))
        if "__pycache__" in rel:
            continue
        q = MOTOR / "meridian" / rel
        damga[rel] = {"repo": hashlib.sha256(p.read_bytes()).hexdigest()[:32],
                      "kopya": hashlib.sha256(q.read_bytes()).hexdigest()[:32]}
    return damga


MOTOR_DAMGA = _motor_kopyala()
sys.path.insert(0, str(MOTOR))

from meridian import config  # noqa: E402

config.STATE = CALISMA / "_state"
config.STATE.mkdir(parents=True, exist_ok=True)
config.HISTORY = config.STATE / "history"
config.BARS = LIVE_BARS
assert config.BARS == LIVE_BARS
_LEDGER_SRC = LIVE_STATE / "bars_integrity.json"
if _LEDGER_SRC.exists():          # kanonik defter yolu kum havuzunda da GERÇEKTEN koşsun
    shutil.copy2(_LEDGER_SRC, config.STATE / "bars_integrity.json")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from meridian import indicators as ind  # noqa: E402
from meridian.adapters import data as dat  # noqa: E402
from meridian.analytics import spearman_ic  # noqa: E402
from meridian.olcum_araclari import temiz_taban  # noqa: E402

# ------------------------------------------------------------------ ŞABLON SABİTLERİ (wp2 ile aynı)
BLOCK = 21              # blok-bootstrap: 21 ARDIŞIK GÖZLEM GÜNÜ (kart: "21g blok CI")
BOOT = 2000
BOOT_IC = 600
MIN_SLICE = 30          # analytics.IC_MIN_SAMPLE tabanı (şablon)
MALIYET_BPS = 10.0      # kart cost_model: "10bps sabit + 20bps duyarlılık satırı"
MIN_KESIT = 50          # kesiti bu kadar sembolden az olan gözlem günü kullanılmaz
BAR_MIN_UZUNLUK = ind.TREND_TEMPLATE_WARMUP + 60 + 5   # wp2 dalgasıyla BİREBİR aynı taban
RNG = np.random.default_rng(20260802)


def _r6(x):
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return None if not np.isfinite(f) else round(f, 6)


# ================================================================== BARLAR (wp2/ortak.py birebir)
def load_bars() -> tuple[dict, dict]:
    """Takvim kapısı (sanitize_bars) + bars_integrity GÜVENSİZ-DÖNEM dışlaması.

    İKİ YOL DA KOŞAR: (1) KANONİK defter yolu `dat.measurement_bars`, (2) HESAPLANAN yol
    `dat.integrity_safe_start`. İkisinin ayrıştığı sembol adıyla sayılır."""
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


def bar_paneli(per: dict, ufuklar=(5, 10, 20)) -> dict:
    """Sembol → {dates, close, volume, fwd{h}, chain{h}, rvol20, rvol20_medyan}."""
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
        for h in ufuklar:                                    # PK4 için BAĞIMSIZ zincir yolu
            rec[f"chain{h}"] = np.expm1(
                lr.shift(-1).rolling(h).sum().shift(-(h - 1))).to_numpy(float)
        # CANLI TANIM (indicators.rvol20 = hacim / SMA20(hacim)) — kart "canlı tanımla BİREBİR"
        rec["rvol20"] = ind.rvol20(df["volume"]).to_numpy(float)
        # kart METNİNİN yazdığı ikinci tanım (medyan20) — YALNIZ TANI satırı için, hüküm taşımaz
        rec["rvol20_medyan"] = (df["volume"] /
                                df["volume"].rolling(20, min_periods=20).median()).to_numpy(float)
        out[t] = rec
    return out


def bars_cached():
    p = CACHE / "bars017.pkl"
    if p.exists():
        with open(p, "rb") as fh:
            return pickle.load(fh)
    per, acc = load_bars()
    pan = bar_paneli(per)
    obj = (pan, acc)
    with open(p, "wb") as fh:
        pickle.dump(obj, fh, protocol=4)
    return obj


# ================================================================== İSTATİSTİK (wp2 birebir)
def block_boot(stat_fn, dates: np.ndarray, n_boot: int = BOOT) -> dict:
    """21 ARDIŞIK GÖZLEM GÜNÜ blok-bootstrap. Yeniden örnekleme birimi ardışık gün bloğudur:
    aynı günün satırlarının bağımlılığını ve ÖRTÜŞEN ileri getirilerin seri korelasyonunu taşır."""
    uniq, inv = np.unique(dates, return_inverse=True)
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
            "neden": None}


def fark_with_ci(yA: np.ndarray, dA: np.ndarray, yB: np.ndarray, dB: np.ndarray,
                 n_boot: int = BOOT, blok: int = BLOCK) -> dict:
    """A ve B dilimlerinin ORTALAMA FARKI (A−B) + 21g blok CI; bootstrap AYNI gün dizisini iki
    dilime de uygular (ortak takvim) → fark istatistiği gün-etkisinden arınır."""
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
    """Spearman rho — scipy YOK; rütbe dönüşümü + Pearson. Bağlar ORTALAMA rütbeyle kırılır."""
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
    """KANONİK IC yolu (analytics.spearman_ic + block_boot). Pozitif kontrol bunu kullanır."""
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


# ---------------------------------------------------- hızlı Spearman (k016.py'den birebir)
def _rank_avg_np(a: np.ndarray) -> np.ndarray:
    return pd.Series(a).rank().to_numpy()


def spearman_fast(x: np.ndarray, y: np.ndarray):
    rx, ry = _rank_avg_np(x), _rank_avg_np(y)
    sx, sy = rx.std(), ry.std()
    if sx <= 0 or sy <= 0:
        return None
    return float(((rx - rx.mean()) * (ry - ry.mean())).mean() / (sx * sy))


def _gun_indeksi(dates: np.ndarray):
    uniq, inv = np.unique(dates, return_inverse=True)
    order = np.argsort(inv, kind="stable")
    cnt = np.bincount(inv, minlength=len(uniq))
    start = np.concatenate([[0], np.cumsum(cnt)[:-1]])
    return uniq, order, start, cnt


def ic_block_boot_fast(x: np.ndarray, y: np.ndarray, dates: np.ndarray,
                       n_boot: int = BOOT_IC, blok: int = BLOCK) -> dict:
    """block_boot ile AYNI şema, IC istatistiği için vektörel yol (kesit ~1,2 milyon satır;
    kanonik yol saatler sürerdi). Kanonikle ÖZDEŞLİĞİ ayrıca sınanır."""
    uniq, order, start, cnt = _gun_indeksi(dates)
    nd = len(uniq)
    if nd < blok * 3:
        return {"lo": None, "hi": None, "n_gun": nd, "n_boot_gecerli": 0,
                "neden": f"gözlem günü sayısı < {blok * 3} (blok bootstrap için yetersiz)"}
    n_blok = int(np.ceil(nd / blok))
    son_bas = nd - blok
    ofs = np.arange(blok)
    vals, atlanan = [], 0
    for _ in range(n_boot):
        bas = RNG.integers(0, son_bas + 1, n_blok)
        gun = (bas[:, None] + ofs[None, :]).ravel()[:nd]
        c = cnt[gun]
        tot = int(c.sum())
        if tot < MIN_SLICE:
            atlanan += 1
            continue
        cikis_bas = np.concatenate([[0], np.cumsum(c)[:-1]])
        poz = np.arange(tot) - np.repeat(cikis_bas, c) + np.repeat(start[gun], c)
        idx = order[poz]
        v = spearman_fast(x[idx], y[idx])
        if v is None or not np.isfinite(v):
            atlanan += 1
            continue
        vals.append(v)
    if len(vals) < n_boot * 0.5:
        return {"lo": None, "hi": None, "n_gun": nd, "n_boot_gecerli": len(vals),
                "neden": "bootstrap tekrarlarının yarısından fazlası ölçülemedi"}
    a = np.asarray(vals, float)
    return {"lo": _r6(np.percentile(a, 2.5)), "hi": _r6(np.percentile(a, 97.5)),
            "n_gun": nd, "n_boot_gecerli": len(vals), "blok": blok, "atlanan": atlanan,
            "neden": None}


def ic_hizli(x: np.ndarray, y: np.ndarray, dates: np.ndarray, ci: bool = True) -> dict:
    """Nokta tahmini KANONİK analytics.spearman_ic ile; CI hızlı blok-bootstrap ile."""
    n = int(len(x))
    if n < MIN_SLICE:
        return {"ic": None, "n": n, "ci": None, "anlamli": None, "neden": f"n<{MIN_SLICE}"}
    ic = spearman_ic(list(zip(x.tolist(), y.tolist())))
    if ic is None:
        return {"ic": None, "n": n, "ci": None, "anlamli": None, "neden": "rütbe değişimi yok"}
    if not ci:
        return {"ic": round(float(ic), 4), "n": n, "ci": None, "anlamli": None,
                "neden": "CI istenmedi (tanı okuması — kart bacağı değil)"}
    c = ic_block_boot_fast(x, y, dates)
    return {"ic": round(float(ic), 4), "n": n,
            "ci": None if c["lo"] is None else {"lo": round(c["lo"], 4),
                                                "hi": round(c["hi"], 4), "seviye": 0.95},
            "ci_meta": c,
            "anlamli": None if c["lo"] is None else bool(c["lo"] > 0 or c["hi"] < 0),
            "pozitif_anlamli": None if c["lo"] is None else bool(c["lo"] > 0),
            "negatif_anlamli": None if c["lo"] is None else bool(c["hi"] < 0),
            "neden": None}


# ================================================================== GÖZLEM TAKVİMİ
def ortak_takvim(pan: dict) -> np.ndarray:
    d = sorted(set().union(*[set(v["dates"].tolist()) for v in pan.values()]))
    return np.array(d)


# ================================================================== DERS #4 — TEMİZ KIYAS TABANI
def temiz_maske(sym_kod: np.ndarray, seans: np.ndarray, olay_maske: np.ndarray,
                h: int) -> np.ndarray:
    """VEKTÖREL yol: satır (sembol, seans_ordinali) olay penceresi DIŞINDA mı?

    Pencere (h, h) SEANS ORDİNALİ birimindedir (takvim günü DEĞİL): ileri getiri h BAR'dır ve
    kirlilik tam olarak "olayın kendi h-barlık penceresi bu satırın penceresiyle örtüşüyor mu"
    sorusudur. `meridian.olcum_araclari.temiz_taban` ile ÖZDEŞLİĞİ pk017.py'de sınanır
    (o fonksiyon `-once <= (o-oe) <= sonra` der; once=sonra=h ⇒ |o-oe| <= h — aynı koşul).
    """
    kirli = np.zeros(len(sym_kod), bool)
    order = np.argsort(sym_kod, kind="stable")
    s_sorted = sym_kod[order]
    sinir = np.searchsorted(s_sorted, np.arange(sym_kod.max() + 2))
    for s in range(sym_kod.max() + 1):
        idx = order[sinir[s]:sinir[s + 1]]
        if len(idx) == 0:
            continue
        ev = np.sort(seans[idx][olay_maske[idx]])
        if len(ev) == 0:
            continue
        o = seans[idx]
        j = np.searchsorted(ev, o)
        d_sag = np.where(j < len(ev), ev[np.minimum(j, len(ev) - 1)] - o, 1 << 30)
        d_sol = np.where(j > 0, o - ev[np.maximum(j - 1, 0)], 1 << 30)
        kirli[idx] = np.minimum(np.abs(d_sag), np.abs(d_sol)) <= h
    return ~kirli


def temiz_evren_tabani(gun_kod: np.ndarray, y: np.ndarray, temiz: np.ndarray, n_gun: int):
    """Gün başına TEMİZ evren ortalaması (olay-penceresi DIŞI satırlar) + muhasebe."""
    w = temiz.astype(float)
    s = np.bincount(gun_kod, weights=y * w, minlength=n_gun)
    c = np.bincount(gun_kod, weights=w, minlength=n_gun)
    with np.errstate(divide="ignore", invalid="ignore"):
        taban = np.where(c > 0, s / c, np.nan)
    return taban, c


def json_yaz(p: pathlib.Path, obj) -> None:
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str))

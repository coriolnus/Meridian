"""score.py — kapanmış işlem defterinden [-1, +1] aralığında bileşik performans skoru.

Ne yapar: gerçekleşen getiriyi hedefe, düşüşü (drawdown) tavana ve Sharpe'ı tabana oranlayıp
0.5/0.3/0.2 ağırlıkla tek sayıya indirger; kapı, yürürlükteki stratejiyle adayı bu sayıyla
karşılaştırır. Mutlak değer sezgiseldir — önemli olan iki tarafın BİREBİR aynı fonksiyonla
puanlanması, yani kapının benzeri benzerle kıyaslamasıdır. Ayrıca stratejinin kendi gerçekleşmiş
kenarından boyut tavsiyesi (Kelly) ve blok-bootstrap kuyruk riski (VaR/CVaR) üretir.

Kilit girişler: score / score_detail (kapının sayısı; span_days ve mtm_equity ile), equity_curve,
max_drawdown, kelly_fraction, tail_risk.

Değişmezler: saf hesap — dosya yazmaz, ağ yok, duvar saati okumaz (süre yalnız işlem
damgalarından türetilir). goal.min_sample altındaki örneklemde skor None'dur, 0.0 DEĞİL:
bilinmeyen skor vasat skorla karıştırılamaz. Sharpe ölçülemediğinde sayı muhafazakâr 0.0 kalır
ama ayrı sharpe_measurable bayrağı "ölçülemedi"yi söyler. tail_risk sabit tohumla determinist,
çekilişi seri boyundan bağımsız ve blok-örneklemelidir (kayıp serileri korunur; IID örnekleme
kuyruğu sistematik küçültürdü). Süre hesabı düşerse yıllıklandırma paydası sabite iner ve bu
tek-seferlik uyarıyla beyan edilir — sessiz miktar kayması yok.

Okur/yazar: yalnız verilen trades/goal yapılarını okur; tek yan etkisi arıza uyarısının obs
kanalına düşmesidir (uyarı denemesi skor hesabını asla düşüremez)."""
from __future__ import annotations
from typing import Optional
import math
import numpy as np

START_EQUITY = 100_000.0


def _clip(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    """Değeri [lo, hi] aralığına kırpar (varsayılan [-1, +1])."""
    return max(lo, min(hi, x))


_SPAN_WARNED = False


def _span_warn(exc: BaseException, ilk: str, son: str) -> None:
    """Süre hesabı düştüğünde BİR kez uyarır — skor fonksiyonu arama sırasında binlerce kez çağrılır."""
    global _SPAN_WARNED
    if _SPAN_WARNED:
        return
    _SPAN_WARNED = True
    try:
        from . import obs
        obs.warn("span_days_fallback", error=f"{type(exc).__name__}: {exc}", first=ilk, last=son,
                 detail="yıllıklandırma paydası 30 güne sabitlendi — skor kayar")
    except Exception:
        # sessiz-yutma: kayıt kanalının kendisi düştü — ikinci kanal yok; telemetri denemesi
        # skor hesabını ASLA düşüremez.
        pass


def _span_days(trades: list[dict]) -> float:
    """İşlem defterinin ilk ve son damgası arasındaki gün sayısı (yıllıklandırmanın paydası).
    İki damgadan az varsa ya da tarih çözülemezse 30 güne düşer — düşüş SESSİZ DEĞİLDİR,
    YASA 4 uyarısı bir kez yazılır."""
    ts = []
    for t in trades:
        for k in ("ts_open", "ts_close"):
            v = t.get(k)
            if v:
                ts.append(str(v)[:10])
    if len(ts) < 2:
        return 30.0
    ts.sort()
    try:
        import datetime as dt
        a = dt.date.fromisoformat(ts[0])
        b = dt.date.fromisoformat(ts[-1])
        return max(1.0, (b - a).days)
    except Exception as e:
        # YASA 4: burası SESSİZ KALAMAZ — süre, yıllıklandırmanın paydasıdır. Biçimsiz
        # bir ts_open/ts_close 30 güne düşerse skor (dolayısıyla kapı kararı) sistematik olarak
        # kayar ve hiçbir yerde hata görünmez; tam olarak "hata değil, miktar değişimi" sınıfı.
        _span_warn(e, ts[0], ts[-1])
        return 30.0


def equity_curve(trades: list[dict], start_equity: float = START_EQUITY) -> list[float]:
    """İşlemleri kapanış sırasına dizip kümülatif sermaye eğrisini kurar (başlangıç sermayesiyle başlar)."""
    eq = start_equity
    curve = [eq]
    for t in sorted(trades, key=lambda x: str(x.get("ts_close", ""))):
        eq += float(t.get("pnl_dollars", 0.0))
        curve.append(eq)
    return curve


def max_drawdown(curve: list[float]) -> float:
    """Sermaye eğrisinin azami tepe-dip düşüşünü oran olarak verir (0.0 = hiç düşmemiş)."""
    peak = curve[0]
    mdd = 0.0
    for v in curve:
        peak = max(peak, v)
        if peak > 0:
            mdd = max(mdd, (peak - v) / peak)
    return mdd


def score_detail(trades: list[dict], goal: dict, start_equity: float = START_EQUITY,
                 span_days: float | None = None, mtm_equity: list | None = None) -> dict:
    """span_days: the EVALUATION WINDOW's calendar length. Without it, annualization derives from the
    trade cluster's own span — a 20-day burst inside a 183-day OOS window inflated realized_30d ~9x and
    sqrt-scaled Sharpe absurdly (regime slices cluster by construction, so this mattered).
    mtm_equity: the replay's daily mark-to-market curve [(date, eq)] — drawdown becomes the WORSE of the
    closed-trade curve and the daily M2M curve, so open-position drawdowns can't hide."""
    min_sample = int(goal.get("min_sample", 20))
    n = len(trades)
    if n < min_sample:
        return {"score": None, "n": n, "min_sample": min_sample,
                "reason": f"{n}/{min_sample} closed trades — score undefined (None, not 0.0)"}

    curve = equity_curve(trades, start_equity)
    total_return = curve[-1] / curve[0] - 1.0
    span = float(span_days) if span_days and span_days > 0 else _span_days(trades)
    realized_30d = (1.0 + total_return) ** (30.0 / span) - 1.0 if total_return > -1 else -1.0
    dd = max_drawdown(curve)
    if mtm_equity:
        try:
            dd = max(dd, max_drawdown([float(e) for _, e in mtm_equity]))
        except (TypeError, ValueError):  # sessiz-yutma: yardımcı/telemetri yolu; başarısızlığı karara girmez ve çağıran yedek değerle aynen devam eder
            pass

    r = np.array([float(t.get("r_multiple", 0.0)) for t in trades], dtype=float)
    per_trade_ret = np.array([float(t.get("pnl_dollars", 0.0)) for t in trades]) / start_equity
    trades_per_year = n / (span / 365.0) if span > 0 else n
    # SIRA ÖNEMLİ: `std(ddof=1)` ÖNCE değerlendiriliyordu ve n<2 iken numpy
    # "Degrees of freedom <= 0" uyarısı basıp NaN üretiyordu. Sonuç doğru çıkıyordu (NaN > 0 False)
    # ama hesap boşuna yapılıyor ve testler her koşuda RuntimeWarning yağdırıyordu — gürültü, gerçek
    # uyarıyı gizler. Örneklem yeterli DEĞİLSE varyans hiç hesaplanmaz.
    sharpe_measurable = n > 2 and float(per_trade_ret.std(ddof=1)) > 0 if n > 2 else False
    if sharpe_measurable:
        sharpe = per_trade_ret.mean() / per_trade_ret.std(ddof=1) * math.sqrt(max(trades_per_year, 1))
    else:
        # DÜRÜSTLÜK: 0.0, "ölçtük ve sıfır çıktı" gibi okunur. Oysa burada "ÖLÇÜLEMEDİ" demek
        # istiyoruz. Sayı muhafazakâr tarafta 0 kalır (kapıyı gevşetmez) ama ayrı bir bayrak
        # ölçülebilirliği söyler; tüketici "min_sharpe geçilemedi" ile "veri yetmedi"yi ayırabilsin.
        sharpe = 0.0

    target = float(goal["target_return_30d"])
    max_dd = float(goal["max_drawdown"])
    min_sharpe = float(goal["min_sharpe"])

    ret_c = _clip(realized_30d / target if target else 0.0)
    dd_c = _clip(1.0 - dd / max_dd if max_dd else 0.0)
    sharpe_c = _clip(sharpe / (min_sharpe * 2.0) if min_sharpe else 0.0)
    composite = _clip(0.5 * ret_c + 0.3 * dd_c + 0.2 * sharpe_c)

    win_rate = float((r > 0).mean()) if n else 0.0
    return {
        "score": round(composite, 4), "n": n, "min_sample": min_sample,
        "total_return": round(total_return, 4), "realized_30d": round(realized_30d, 4),
        "max_drawdown": round(dd, 4), "sharpe": round(sharpe, 3),
        "sharpe_measurable": bool(sharpe_measurable),   # 0.0 "ölçüldü sıfır" mı, "ölçülemedi" mi
        "avg_r": round(float(r.mean()), 3),
        "win_rate": round(win_rate, 3), "components": {"ret": round(ret_c, 3), "dd": round(dd_c, 3),
        "sharpe": round(sharpe_c, 3)},
        "targets": {"target_return_30d": target, "max_drawdown": max_dd, "min_sharpe": min_sharpe},
    }


def score(trades: list[dict], goal: dict, start_equity: float = START_EQUITY) -> Optional[float]:
    """The gate's number. None below min_sample."""
    return score_detail(trades, goal, start_equity)["score"]


TAIL_MIN_SAMPLE = 12   # below this the bootstrap has nothing honest to say


def kelly_fraction(trades: list[dict]) -> Optional[dict]:
    """Fractional-Kelly sizing ceiling from the strategy's OWN realized edge: full Kelly f* = W − (1−W)/R
    (W = win rate, R = avg-win / avg-loss), reported alongside HALF-Kelly as a sane cap. Advisory — a
    negative f* says the realized edge does not justify the current size. None below TAIL_MIN_SAMPLE."""
    rs = [float(t.get("r_multiple", 0.0)) for t in trades if "r_multiple" in t]
    if len(rs) < TAIL_MIN_SAMPLE:
        return None
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r < 0]
    if not wins or not losses:
        return None
    W = len(wins) / len(rs)
    R = (sum(wins) / len(wins)) / abs(sum(losses) / len(losses))
    f = W - (1.0 - W) / R if R > 0 else -1.0
    return {"win_rate": round(W, 3), "win_loss_ratio": round(R, 2),
            "full_kelly": round(f, 3), "half_kelly": round(max(0.0, f / 2.0), 3), "n": len(rs)}


TAIL_SIMS = 20_000   # bkz. aşağıdaki (2): 4000, vetonun KENDİ marjından daha gürültülüydü


def tail_risk(trades: list[dict], horizon: int = 20, sims: int = TAIL_SIMS,
              alpha: float = 0.95, seed: int = 7) -> Optional[dict]:
    """Bootstrap Monte Carlo tail risk over a `horizon`-trade window, in R units. Resamples the
    realized per-trade R-multiples (with replacement) `sims` times, sums each path, and reports the
    (1-alpha) VaR and CVaR (expected shortfall) as POSITIVE loss magnitudes. Deterministic (fixed
    seed) — the point is relative tail behavior, not an absolute forecast. Returns None below
    TAIL_MIN_SAMPLE (honest 'unknown').

    İKİ DÜZELTME (kapı istatistiği denetimi):

    (1) "AYNI ÇEKİLİŞ" İDDİASI DOĞRU DEĞİLDİ. Eski satır `rng.integers(0, rs.size, ...)` idi; ÜST
        SINIR rs.size olduğundan aynı tohum farklı uzunluktaki iki seride FARKLI tamsayılar üretir.
        incumbent ile aday neredeyse hiçbir zaman aynı işlem sayısında olmadığı için "ikisi aynı
        çekilişte karşılaştırılır" cümlesi pratikte HİÇ geçerli değildi — yani sert kuyruk vetosu
        eşleştirilmemiş iki Monte Carlo'yu kıyaslıyordu. Artık çekiliş BOYUTTAN BAĞIMSIZ: [0,1)
        üniformları bir kez çekilir, her seri kendi boyuna ölçeklenir → iki taraf serilerinin AYNI
        GÖRELİ konumlarından örneklenir ve MC gürültüsü farkta kısmen sönümlenir.

    (2) MC GÜRÜLTÜSÜ VETO MARJINDAN BÜYÜKTÜ. reflect.TAIL_MARGIN_R = 0.5R SERT bir veto eşiği; ama
        sims=4000 ile SABİT veride yalnız tohumu değiştirmek cvar_r'yi 0.91R, var_r'yi 0.64R
        aralığında oynatıyordu (30 tohum, 60 işlem). Yani vetonun karar sınırı kendi simülasyon
        gürültüsünün İÇİNDEydi; sabit tohum bunu TEKRARLANABİLİR yapar, DOĞRU yapmaz. sims=20000 ile
        aynı ölçüm 0.22R/0.23R'ye iner (marjın yarısının altı). Maliyet çağrı başına ~5 ms ve
        tail_risk walk_forward başına bir kez çağrılır — dakikalar süren bir replay yanında yok."""
    rs = np.array([float(t.get("r_multiple", 0.0)) for t in trades if "r_multiple" in t], dtype=float)
    if rs.size < TAIL_MIN_SAMPLE:
        return None
    rng = np.random.default_rng(seed)
    # CIRCULAR BLOCK bootstrap (block=5): resample contiguous runs of trades, not IID single trades, so
    # the serial clustering of losses (a bad streak) is preserved. IID resampling breaks that dependence
    # and systematically UNDERSTATES the tail — the whole point of a tail gate is to not do that.
    block = min(5, horizon)
    n_blocks = -(-horizon // block)                                    # ceil(horizon / block)
    starts = (rng.random((sims, n_blocks)) * rs.size).astype(np.int64)       # boyuttan bağımsız — (1)
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]) % rs.size   # (sims, n_blocks, block)
    paths = rs[idx].reshape(sims, n_blocks * block)[:, :horizon].sum(axis=1)  # cumulative R per path
    q = float(np.percentile(paths, (1.0 - alpha) * 100.0))                   # the (1-alpha) quantile
    tail = paths[paths <= q]
    var_r = round(-q, 3)                                                     # loss at the quantile
    cvar_r = round(float(-tail.mean()), 3) if tail.size else var_r           # mean loss beyond it
    return {"horizon": horizon, "alpha": alpha, "n": int(rs.size),
            "var_r": var_r, "cvar_r": cvar_r,
            "worst_r": round(float(-paths.min()), 3), "mean_r": round(float(paths.mean()), 3)}

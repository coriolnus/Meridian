"""backtest.py — walk-forward out-of-sample engine. THE learning gate. Replays through the exact
same strategy.py + broker.py used live, so backtest numbers are honest (§4).

Event ordering per trading day D (no look-ahead — decisions use bars <= D, executions at D+1 open):
  1. OPEN(D):   execute time-stop/regime-flip exits flagged at D-1 close; fill entries armed at D-1 close
  2. INTRADAY(D): gap-aware touch exits (stop/trail/target) for all open positions, using levels set <= D-1
  3. CLOSE(D):  update trailing stops; recompute regime; scan + rank new entry signals; arm for D+1
"""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

from . import strategy as strat
from . import regime as regime_mod
from . import indicators as ind
from . import score as score_mod
from . import guard

# Backtest sıcak yolda çalışır (binlerce seans × yüzlerce sembol): aynı arıza her turda loglanırsa
# olay defteri boğulur ve gerçek uyarılar görünmez olur. Süreç başına BİR kez uyar — ama MUTLAKA uyar.
_WARNED: set = set()


def _warn_once(event: str, **fields) -> None:
    if event in _WARNED:
        return
    _WARNED.add(event)
    from . import obs
    obs.warn(event, **fields)

from . import earnings
from . import config
from . import skills as skills_mod
from . import broker as brk
from .broker import PaperBroker

# Sector map for the replay universe — enables the max_sector_exposure_pct guard in backtest.
SECTORS = {
    "AAPL": "tech", "MSFT": "tech", "NVDA": "tech", "AVGO": "tech", "AMD": "tech", "CRM": "tech",
    "ADBE": "tech", "ORCL": "tech", "GOOGL": "comms", "META": "comms", "NFLX": "comms",
    "AMZN": "consumer", "TSLA": "consumer", "HD": "consumer", "NKE": "consumer", "MCD": "consumer",
    "SBUX": "consumer", "COST": "staples", "LOW": "consumer",
    "JPM": "financials", "BAC": "financials", "GS": "financials", "V": "financials",
    "MA": "financials", "AXP": "financials",
    "UNH": "health", "LLY": "health", "JNJ": "health", "ABBV": "health", "MRK": "health",
    "CAT": "industrials", "DE": "industrials", "BA": "industrials", "GE": "industrials",
    "HON": "industrials", "XOM": "energy", "CVX": "energy", "LIN": "materials",
    "PG": "staples", "KO": "staples", "WMT": "staples", "PEP": "staples",
    # laggards / dispersers (survivorship fix)
    "INTC": "tech", "PYPL": "financials", "DIS": "comms", "T": "comms", "EA": "comms",
    "PFE": "health", "ENPH": "tech", "MRNA": "health", "MMM": "industrials", "HRL": "staples",
    "VFC": "consumer", "F": "consumer",
    # genişleme · comms
    "GOOG": "comms", "CMCSA": "comms", "TMUS": "comms", "VZ": "comms", "CHTR": "comms", "WBD": "comms", "OMC": "comms",
    "TTWO": "comms", "MTCH": "comms", "PINS": "comms", "SNAP": "comms", "SPOT": "comms", "ROKU": "comms", "LYV": "comms",
    # genişleme · consumer
    "BKNG": "consumer", "MAR": "consumer", "HLT": "consumer", "RCL": "consumer", "CCL": "consumer", "NCLH": "consumer", "DAL": "consumer",
    "UAL": "consumer", "LUV": "consumer", "EXPE": "consumer", "ORLY": "consumer", "AZO": "consumer", "TJX": "consumer", "ROST": "consumer",
    "BURL": "consumer", "DG": "consumer", "DLTR": "consumer", "TGT": "consumer", "LULU": "consumer", "DECK": "consumer",
    # genişleme · energy
    "COP": "energy", "EOG": "energy", "SLB": "energy", "HAL": "energy", "BKR": "energy", "OXY": "energy", "PSX": "energy",
    "VLO": "energy", "MPC": "energy", "DVN": "energy", "FANG": "energy", "EQT": "energy", "WMB": "energy", "KMI": "energy",
    "OKE": "energy", "LNG": "energy", "TRGP": "energy",
    # genişleme · financials
    "WFC": "financials", "C": "financials", "MS": "financials", "SCHW": "financials", "BLK": "financials", "BX": "financials", "KKR": "financials",
    "APO": "financials", "CB": "financials", "PGR": "financials", "TRV": "financials", "ALL": "financials", "MET": "financials", "PRU": "financials",
    "AFL": "financials", "AIG": "financials", "COF": "financials", "PNC": "financials", "SYF": "financials", "USB": "financials",
    # FISV (2026-07-30) — ödeme işlemcisi; GICS 2023'ten beri financials, akranları V/MA/PYPL ile aynı etiket.
    "FISV": "financials",
    # genişleme · health
    "TMO": "health", "DHR": "health", "ABT": "health", "BMY": "health", "AMGN": "health", "GILD": "health", "VRTX": "health",
    "REGN": "health", "BIIB": "health", "ISRG": "health", "SYK": "health", "BSX": "health", "MDT": "health", "EW": "health",
    "ZBH": "health", "BAX": "health", "BDX": "health", "CI": "health", "CVS": "health", "HUM": "health",
    # genişleme · industrials
    "UNP": "industrials", "CSX": "industrials", "NSC": "industrials", "UPS": "industrials", "FDX": "industrials", "LMT": "industrials", "RTX": "industrials",
    "NOC": "industrials", "GD": "industrials", "LHX": "industrials", "TDG": "industrials", "HWM": "industrials", "ETN": "industrials", "EMR": "industrials",
    "PH": "industrials", "ITW": "industrials", "CMI": "industrials", "PCAR": "industrials", "ROK": "industrials", "DOV": "industrials",
    # genişleme · materials
    "SHW": "materials", "APD": "materials", "ECL": "materials", "FCX": "materials", "NEM": "materials", "NUE": "materials", "STLD": "materials",
    "DOW": "materials", "DD": "materials", "LYB": "materials", "PPG": "materials", "VMC": "materials", "MLM": "materials", "ALB": "materials",
    "CF": "materials", "IP": "materials", "PKG": "materials",
    # genişleme · reits
    "PLD": "reits", "AMT": "reits", "CCI": "reits", "EQIX": "reits", "SPG": "reits", "O": "reits", "PSA": "reits",
    "DLR": "reits", "WELL": "reits", "AVB": "reits", "EQR": "reits", "VTR": "reits", "IRM": "reits", "CBRE": "reits",
    # genişleme · staples
    "PM": "staples", "MO": "staples", "KMB": "staples", "CL": "staples", "GIS": "staples", "KVUE": "staples", "KHC": "staples",
    "HSY": "staples", "STZ": "staples", "MDLZ": "staples", "MKC": "staples", "CHD": "staples", "CLX": "staples", "SYY": "staples",
    "KR": "staples", "TSN": "staples", "CAG": "staples", "EL": "staples", "KDP": "staples", "MNST": "staples",
    # genişleme · tech
    "TXN": "tech", "QCOM": "tech", "MU": "tech", "ADI": "tech", "LRCX": "tech", "KLAC": "tech", "AMAT": "tech",
    "NXPI": "tech", "MCHP": "tech", "ON": "tech", "MRVL": "tech", "SWKS": "tech", "TER": "tech", "MPWR": "tech",
    "SNPS": "tech", "CDNS": "tech", "CTSH": "tech", "ADSK": "tech", "INTU": "tech", "NOW": "tech", "PANW": "tech",
    # genişleme · utilities
    "NEE": "utilities", "DUK": "utilities", "SO": "utilities", "D": "utilities", "AEP": "utilities", "EXC": "utilities", "SRE": "utilities",
    "XEL": "utilities", "ED": "utilities", "WEC": "utilities", "ES": "utilities", "PEG": "utilities", "CEG": "utilities",
}


@dataclass
class BacktestResult:
    trades: list
    equity: list          # [(date, equity)]
    params: dict
    start: str
    end: str
    plan_log: list = None       # every armed/rejected plan, dated (for the Signals page)
    candidate_log: list = None  # top candidates scanned per day, dated
    # C18 (2026-08-02): silahlı planın dolmama NEDENLERİ, neden → adet. `entry_missed_limit` burada
    # görünür olmadan "replay canlının reddettiği dolumları yazıyor mu?" sorusu ÖLÇÜLEMİYORDU (canlı
    # taraf aynı sayacı `entry_exec.jsonl`in `karar` alanına yazıyor, replay tarafında karşılığı yoktu).
    # None = bu sonuç eski bir çağrıdan geliyor / sayaç hiç doldurulmadı; {} = doldu ve HİÇ ret olmadı.
    entry_rejects: dict = None
    # 2026-08-03 (Rol-1 kararı 2): replay'de kazanç-karartması ÖLÇÜLEMEZ (PIT takvim yok) ve artık
    # ölçülmüş GİBİ davranmıyor. Bu sayaç "kaç plan karartma kapısı KONUŞAMADAN karar aldı"yı taşır;
    # None = eski bir çağrı, {} = doldu. Üretilen kanıt TÜKETİLİR (YASA 6): replay raporunu okuyan
    # her yer, o tabloda karartma etkisinin SIFIR olduğunu buradan görür.
    earnings_gate: dict = None

    def detail(self, goal: dict) -> dict:
        return score_mod.score_detail(self.trades, goal)


def _indexed(bars: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    return {t: df.set_index("date") for t, df in bars.items()}


def _adv(df: pd.DataFrame, d, window: int = 20) -> float | None:
    """Causal average daily volume (shares) strictly BEFORE bar d. None if there is no volume column
    or no history (synthetic/thin bars) — the broker then uses fixed slippage with no liquidity cap."""
    try:
        if "volume" not in df.columns:
            return None
        vol = df.loc[:d]["volume"].iloc[:-1].tail(window)
        if len(vol) == 0:
            return None
        m = float(vol.mean())
        return m if m > 0 else None
    except Exception:  # sessiz-yutma: None DÖNÜŞÜN KENDİSİ cevap — çağıran "hacim bilinmiyor" dalını işletir, likidite kapısı muhafazakâr tarafta kalır
        return None


def replay(params: dict, bars: dict[str, pd.DataFrame], index_bars: pd.DataFrame,
           goal: dict, start: str, end: str, strategy_version: int = 1,
           params_by_regime: dict | None = None,
           with_gate_detail: bool = False) -> BacktestResult:
    limits = goal["limits"]
    max_open = int(limits["max_open_positions"])
    max_pos_r = float(limits["max_position_r"])
    # SEKTÖR TAVANI BURADA OKUNMAZ — VE BU BİLİNÇLİDİR (2026-08-14, ROADMAP §2-35b).
    # BURADA ŞU SATIR VARDI: `max_sector_pct = float(limits["max_sector_exposure_pct"])`. Atanıyor,
    # HİÇBİR YERDE okunmuyordu (ölü yerel; repo genelinde `max_sector_pct` adının meridian/ içindeki
    # TEK geçtiği yerdi). Replay sektör tavanını `guard.classify_gate`e DEVREDER: kapıya
    # `portfolio["sector_counts"]` (bu fonksiyonda `sector_ct`ten kurulur) ve `goal` gider, kural
    # guard'ın `sector_cap` satırında işler, paydasını `guard.sector_cap_basis` belirler. Yani ikinci
    # bir uygulama YOKTUR ve olmaması İYİDİR — WP-15g'nin payda ayrıştırması replay'i bu yüzden
    # otomatik kapsadı. Ölü yerel KALDIRILDI çünkü politikanın ADINI taşıyordu ve kullanılan
    # `max_open`/`max_pos_r` satırlarının dibinde duruyordu: "birileri bağlarsa" ikinci ve AYRIŞMIŞ
    # bir sektör kuralı doğardı (`guard.check_trade` docstring'indeki tur-12 ayrışma sınıfı).
    # BURAYA YENİ BİR SEKTÖR KURALI YAZILMAZ — tavan guard'ta TEKtir, replay onu ÇAĞIRIR.
    # ÖLÇÜLEN TEK YAN ETKİ (gizlenmiyor): satırın gözlenebilir tek işlevi, `max_sector_exposure_pct`
    # anahtarı EKSİK bir goal sözlüğünde KeyError'ı replay GİRİŞİNDE yükseltmesiydi. Artık aynı
    # KeyError kapıya giren İLK planda `guard.classify_gate`ten yükselir (fail-closed korunur, yeri
    # değişir); hiç plan kapıya girmeyen bir koşumda ise hiç yükselmez — eksik anahtarlı goal zaten
    # `config.goal()` yolundan gelmez (state/goal.yaml `limits.max_sector_exposure_pct` taşır ve ad
    # `guard.LIMIT_KEYS`te kayıtlıdır).
    max_daily_loss = float(limits["max_daily_loss_pct"]) / 100.0
    no_trade_before = int(limits.get("no_trade_before_bars", 0))

    slip = float(goal.get("slippage_bps", 5))
    commission = float(goal.get("commission_per_share", 0.0))
    broker = PaperBroker(score_mod.START_EQUITY, slip, commission)

    idx = index_bars.set_index("date").sort_index()
    calendar = [d for d in idx.index if pd.Timestamp(start) <= d <= pd.Timestamp(end)]
    per = _indexed(bars)

    armed: list[dict] = []          # plans to fill at next open
    # G3b (2026-07-30): kurulumun YAPI çizgisi (pivot), silahlı plan için AYRI bir yan haritada taşınır
    # — plan SÖZLÜĞÜNE alan olarak EKLENMEZ. GEREKÇE, ve bu bilinçli bir tasarım kararıdır:
    # `test_differential_v60.test_plan_dicts_have_the_same_field_set` iki plan üreticisinin (canlı
    # loop.py P3_PLAN + replay) alan kümelerinin AYNI olmasını şart koşar ve CANLI-only alanlar için
    # bir allowlist tutarken REPLAY-only alanlar için BİLİNÇLİ OLARAK tutmaz: replay'in bilip canlının
    # bilmediği bir alan, tam olarak "backtest sayıları yalan olur" ayrışmasıdır (§4). Pivot bir
    # DEFTER alanı değil bir İCRA girdisidir (broker.fill_entry → Position.pivot →
    # strategy.early_kill_pivot_exit), o yüzden defter şemasına değil icra yoluna konur.
    # C13 (2026-08-02) — DİKİŞ KAPANDI: canlı yol da artık pivotu taşıyor (loop.py `entry_law` yan
    # tablosu → fill_entry(pivot=...) → Position.pivot → manage_position sözlüğü). Eskiden burada
    # "canlı fill_entry'e pivot GEÇİRMEZ → erken itlaf canlıda atıl" yazıyordu; o cümle artık YANLIŞ
    # olurdu ve `exit.early_kill_pivot` terfi ederse canlıda sessiz no-op üreten sahte-terfi yolunun
    # ta kendisiydi.
    armed_pivots: dict[str, float] = {}
    # C11+C18 (denetim 2026-08-02): ATR de AYNI yan-harita deseniyle taşınır. ÖNCESİ: replay
    # `fill_entry`e `atr=` HİÇ geçmiyordu → `broker.entry_limit_price` `a > 0` dalına giremiyor ve
    # limit DAİMA yüzde tavanına (%1) düşüyordu; canlı motor ise min(0,5·ATR14, %1) ile koşuyordu.
    # Yani "TEK YASA, İKİ MOTOR" (broker.py başlığı) giriş limitinde KIRIKTI ve kırılma tek yönlüydü:
    # replay canlının REDDEDECEĞİ dolumları yazıyor, `entry_missed_limit` sayısını sıfırlıyor ve
    # öğrenme kapısı/gölge terfisi iyimser bir icra modeli üzerinden karar veriyordu.
    # ATR ölçülemezse None KALIR (0.0 değil): `entry_limit_price` None'ı "ölçülemedi" diye okur ve
    # yalnız yüzde tavanını bağlar — uydurma ATR yok (UYDURMA YASAĞI).
    armed_atr: dict[str, float | None] = {}
    # C18: kaçan dolumlar SAYILIR, yutulmaz. `reject_out` sözlüğü fill başına doldurulur ve nedenler
    # burada birikir; `BacktestResult.entry_rejects` iki motorun kaçırdığı dolumları kıyaslanabilir
    # kılar (canlı taraf aynı sayacı `entry_exec` defterine `karar` alanıyla zaten yazıyor).
    entry_rejects: dict[str, int] = {}
    # Replay'de kazanç-kapısının SAYACI (2026-08-03, Rol-1 kararı 2). Gerekçe karar satırının
    # yanında; burada yalnız kabı var. Boş kalırsa ({}) "hiç plan değerlendirilmedi" demektir ve
    # bu, "kapı konuştu ve hiçbir şey bulmadı"dan farklı bir olgudur.
    _eg: dict[str, int] = {}
    pending_exits: dict[str, str] = {}  # ticker -> reason, to execute at next open
    # regime-resolved params for INTRADAY consumers (scale_out): the regime known at D's intraday is
    # D-1's (computed at the prior CLOSE) — using flat `params` here silently ignored any
    # exit.scale_out_*@regime override, so such a candidate replayed byte-identical to the incumbent.
    # Before the first close no regime is known → flat params (byte-identical to the old behavior).
    prev_eff = dict(params)
    equity_curve = []
    peak_equity = broker.start_equity
    plan_log: list[dict] = []
    candidate_log: list[dict] = []
    day_start_equity = broker.start_equity
    plan_seq = 0
    _id = [0]

    def marks_on(d):
        return {t: per[t].loc[d, "close"] for t in broker.positions if d in per[t].index}

    def marks_open_on(d):
        # OPEN-phase equity must be marked at D's OPEN — using D's close during the open phase let the
        # breaker/de-risk/sizing "know" the afternoon's move at the morning open (audit #1 look-ahead)
        return {t: per[t].loc[d, "open"] for t in broker.positions if d in per[t].index}

    for bar_i, d in enumerate(calendar):
        # ---- 1. OPEN(D): pending exits, then armed entries ----
        for t, reason in list(pending_exits.items()):
            if t in broker.positions and t in per and d in per[t].index:
                broker.close_position(t, per[t].loc[d, "open"], reason, str(d.date()))
        pending_exits.clear()

        eq_now = broker.equity(marks_open_on(d))           # OPEN marks — no same-day close look-ahead (#1)
        peak_equity = max(peak_equity, eq_now)
        size_mult = brk.derisk_mult(eq_now, peak_equity)   # graded de-risk on the running drawdown
        eff_max_open = brk.max_positions_at(eq_now, peak_equity, max_open)   # + concurrent-position throttle
        breaker_tripped = (eq_now - day_start_equity) / day_start_equity <= -max_daily_loss
        for plan in armed:
            t = plan["ticker"]
            if t in per and d in per[t].index and not breaker_tripped and size_mult > 0 \
                    and len(broker.positions) < eff_max_open and t not in broker.positions:
                _rej: dict = {}
                broker.fill_entry(plan, per[t].loc[d, "open"], str(d.date()), eq_now,
                                  size_mult=size_mult, adv=_adv(per[t], d),
                                  pivot=armed_pivots.get(t, 0.0),   # G3b: yapı çizgisi (icra girdisi)
                                  atr=armed_atr.get(t),             # C11/C18: E1 limitinin ATR bacağı
                                  reject_out=_rej)
                if _rej.get("reason"):
                    entry_rejects[_rej["reason"]] = entry_rejects.get(_rej["reason"], 0) + 1
        # KASITLI REPLAY↔CANLI FARKI (2026-07-23, tarama "diverged" işaretledi ama sürüklenme DEĞİL):
        # canlı loop._carry_armed_without_bar bar-yok planı bir seans TAŞIR (GS-1140), replay burada
        # armed'ı SIFIRLAR. İki senaryo AYRIdır: canlıda bar-yok = EOD YAYIN GECİKMESİ (geçici, plan
        # hâlâ geçerli → taşınır); replay geçmiş veriyle koşar, orada bar-yok = TATİL/DELİSTİNG (kalıcı
        # boşluk, plan gerçekten dolmaz → düşer). Replay'e carry eklemek tatilde plan taşımak olurdu.
        # Aynı gerekçe keşif-modu (canlı bütçe %0 dalı) ve cf_backfill'in basit taken slot seçimi için
        # de geçerli: replay/backfill, canlının BASİTLEŞTİRİLMİŞ modelidir — hizalanacak sürüklenme yok.
        armed = []
        armed_pivots = {}            # yan harita `armed` ile AYNI ömre sahip: birlikte doğar, birlikte ölür
        armed_atr = {}               # (aynı ömür — ATR de silahlanma anında sabitlenir, yeniden hesaplanmaz)
        day_start_equity = broker.equity(marks_open_on(d))

        # ---- 2. INTRADAY(D): touch exits ----
        for t in list(broker.positions.keys()):
            if t not in per or d not in per[t].index:
                continue
            pos = broker.positions[t]
            bar = per[t].loc[d]
            broker.scale_out(pos, {"high": bar["high"], "low": bar["low"], "open": bar["open"]}, prev_eff)
            ex = broker._touch_exit(pos, {"open": bar["open"], "high": bar["high"], "low": bar["low"]})
            if ex:
                broker.close_position(t, ex[0], ex[1], str(d.date()))
            else:
                pos.bars_held += 1
            # daily-loss circuit breaker: flatten no new entries once tripped (handled at fill)

        # ---- 3. CLOSE(D): manage trails, regime, scan+arm ----
        idx_slice = idx.loc[:d]
        rj = regime_mod.build_regime_json(idx_slice.reset_index(), params, str(d.date()))
        # LİDER SEKTÖRLER — canlı döngü ve cf_backfill bunu dolduruyordu, BACKTEST doldurmuyordu
        # (denetim turu 23, 2026-07-21). Sonuç: guard'ın 'leading_sector' soft kontrolü kapıda HİÇ
        # ateşlenmiyor, canlıda ateşleniyordu; yani kapının ölçtüğü karar akışı ile canlınınki
        # ayrışıyordu. NO_GO'yu değiştirmediği için işlem sayısı aynı kalıyor ama REVIEW dağılımı
        # (ve ona bakan her katman) yanlış. Aynı yasa, tek uygulama.
        _srets = {t: float(df.loc[:d]["close"].iloc[-1] / df.loc[:d]["close"].iloc[-22] - 1.0)
                  for t, df in per.items() if len(df.loc[:d]) > 22}
        rj["leading_sectors"] = regime_mod.sector_momentum(_srets, SECTORS)
        regime_ok = rj["regime"] in ("trend_up", "chop") and rj["exposure_budget_pct"] > 0
        # regime-conditional params: base params overlaid with this regime's overrides (no-op if none)
        eff = config.resolve_params(params, params_by_regime, rj["regime"])
        prev_eff = eff                       # tomorrow's intraday (scale_out) runs under today's regime

        for t in list(broker.positions.keys()):
            if t not in per or d not in per[t].index:
                continue
            pos = broker.positions[t]
            df_t = per[t].loc[:d].reset_index()
            dec = strat.manage_position(df_t, {"entry": pos.entry, "stop": pos.stop,
                    "trail_stop": pos.trail_stop, "r_per_share": pos.r_per_share,
                    "pivot": pos.pivot},          # G3b: yapı çizgisi (erken itlaf okur; 0.0 → atıl)
                    eff, pos.bars_held, regime_ok)
            pos.trail_stop = dec.trail_stop
            if dec.exit_now:
                pending_exits[t] = dec.exit_reason

        slots = max_open - len(broker.positions)
        if bar_i >= no_trade_before and rj["exposure_budget_pct"] > 0 and slots > 0:
            # cross-sectional RS for the day
            rets = {}
            for t, df_t in per.items():
                sub = df_t.loc[:d]
                if d not in df_t.index:      # güncellik: bu seansın barı yoksa (delist/boşluk) havuza girmez
                    continue
                if len(sub) > strat.RS_LOOKBACK + 1:
                    rets[t] = float(sub["close"].iloc[-1] / sub["close"].iloc[-1 - strat.RS_LOOKBACK] - 1.0)
            rs_map = ind.rs_rating(rets)

            # current sector exposure
            sector_ct: dict[str, int] = {}
            for t in broker.positions:
                sector_ct[SECTORS.get(t, "?")] = sector_ct.get(SECTORS.get(t, "?"), 0) + 1
            others_rets = [ind.returns_tail(per[o].loc[:d, "close"]) for o in broker.positions if o in per]  # once/day
            # C12: Y3 NAV tavanlarının üretici tarafı (canlı döngüyle AYNI yasa — `guard.y3_*`
            # ÇAĞRILIR, kopyalanmaz). Kitap seansta bir kez ölçülür; `armed` aday başına eklenir.
            # NAV kapanış markıyla (`marks_on`), çünkü arm CLOSE(D) fazındadır — `marks_open_on`
            # AÇILIŞ fazının (devre kesici/kısma) markıdır ve buraya konması denetim #1'in
            # ileri-bakış hatasının aynadaki hâli olurdu.
            _y3_mk = marks_on(d)
            _y3_eq = broker.equity(_y3_mk)
            _y3_book = [{"sector": SECTORS.get(t, "?"), "qty": p.qty, "entry": p.entry,
                         "stop": p.stop, "trail_stop": p.trail_stop, "mark": _y3_mk.get(t)}
                        for t, p in broker.positions.items()]

            candidates = []
            for t, df_t in per.items():
                if t in broker.positions or any(a["ticker"] == t for a in armed):
                    continue
                if d not in df_t.index:      # güncellik: bayat kuyrukla tarama = hayalet/bayat tetik riski
                    continue
                sub = df_t.loc[:d].reset_index()
                sig = strat.scan_entry(sub.tail(340), eff, rs_map.get(t, 50), ticker=t)
                if sig:
                    candidates.append(sig)
            candidates.sort(key=lambda s: s.score, reverse=True)
            for sig in candidates[:5]:
                candidate_log.append({"date": str(d.date()), "ticker": sig.ticker,
                                      "source_skill": skills_mod.screener_for(sig.setup), "score": sig.score,
                                      "setup": sig.setup, "sector": SECTORS.get(sig.ticker, "?"),
                                      **{k: sig.as_row()[k] for k in ("pivot", "stop", "atr", "rs_rating")}})

            for sig in candidates:
                sec = SECTORS.get(sig.ticker, "?")
                plan_seq += 1
                # PLAN KİMLİĞİ = CANLI ŞEMANIN AYNISI (2026-07-21). Eskiden backtest `P00140` gibi bir
                # SIRA numarası veriyordu; canlı döngü ve cf_backfill ise `P-{tarih}-{ticker}`. Sonuç:
                # cf_fidelity — simülasyonun gerçeğe uyup uymadığını ölçen TEK mekanizma —
                # plan_id'yi `P-YYYY-MM-DD-TICKER` diye ayrıştırdığı için replay'den tohumlanmış
                # 90 işlemin 90'ını da eleyip SONSUZA KADAR None dönüyordu. "Veri birikmiyor" değil,
                # BİRLEŞTİRME İMKÂNSIZDI. Üçüncü kez aynı desen: iki üretici, farklı şema.
                plan = {
                    "id": f"P-{d.date()}-{sig.ticker}", "date": str(d.date()), "ticker": sig.ticker,
                    "side": "long",
                    "entry_trigger": sig.entry_trigger, "stop": sig.stop, "profit_target": sig.profit_target,
                    "targets": [sig.profit_target], "size_r": min(sig.size_r, max_pos_r),
                    "r_multiple_expected": round((sig.profit_target - sig.entry_trigger) / sig.r_per_share, 2),
                    "regime_at_plan": rj["regime"], "strategy_version": strategy_version,
                    "skill_chain": [skills_mod.screener_for(sig.setup), "position-sizer", "pre-trade-discipline-gate"],
                    "sector": sec, "score": sig.score, "setup": sig.setup,
                }
                portfolio = {"open_positions": max_open - slots, "sector_counts": sector_ct,
                             "day_pnl_pct": 0.0,  # breaker enforced at fill (open), not at arm time
                             "open_risk_r": sum(p.size_r for p in broker.positions.values())
                                            + sum(a["size_r"] for a in armed),
                             "max_corr": ind.corr_max(per[sig.ticker].loc[:d, "close"], others_rets),
                             **guard.y3_portfolio_inputs(_y3_book, armed, equity=_y3_eq,
                                                         size_fn=broker.size_position)}
                # KARAR AĞACI (ikinci tur denetimi, 2026-07-21): plan defterini İKİ üretici yazıyor —
                # canlı döngü (gate_checks ile) ve replay tohumu (gate_checks OLMADAN). Defter replay ile
                # tohumlandığı için panonun karar-ağacı tablosu 144 satırın 144'ünde BOŞTU: "neden GO
                # verdi?" sorusu (geçen kontroller dahil) kayıttan cevaplanamıyordu. Aynı yasanın iki
                # uygulaması deseninin ŞEMA hâli. detay yalnız İSTENDİĞİNDE üretilir: arama yolunda
                # binlerce replay koşuyor, her plana 8 sözlük eklemek belleği şişirirdi.
                _det = [] if with_gate_detail else None
                # C12: dolar büyüklükleri kapıya PLAN ŞEMASINI BOZMADAN gider (canlı döngüyle aynı
                # desen ve aynı gerekçe: plan defterinin şeması iki motorda EŞİT kalmalı —
                # test_differential_v60 tam bunu çiviliyor).
                _gate_plan = {**plan, **guard.y3_plan_inputs(plan, equity=_y3_eq,
                                                             size_fn=broker.size_position)}
                verdict, greasons = guard.classify_gate(_gate_plan, portfolio, rj, goal, eff, detail_out=_det)
                # KARAR AĞACININ SATIRI da tek yasa olmalı (diferansiyel motor testi, 2026-07-22):
                # karartma kuralını İKİ motor da uyguluyordu ama KANITINI yalnız canlı döngü yazıyordu —
                # replay'den tohumlanan planların gate_checks'inde 'earnings_blackout' satırı YOKTU.
                # gate_checks'in 144/144 boş çıkmasıyla aynı desenin satır seviyesindeki hâli: kural
                # aynı, kayıt farklı; "neden GO verdi?" sorusu tohum döneminde eksik cevaplanıyordu.
                # Karar mantığı DEĞİŞMEDİ (aynı koşul, aynı sıra) — yalnız kanıt iki motorda da var.
                #
                # ---- REPLAY-PIT DÜZELTMESİ (2026-08-03, Rol-1 kararı 2) --------------------------
                # ÖLÇÜLDÜ (research/olcumler/wpd_earnings_failopen/RAPOR.md §3c): bu satır
                # `in_blackout(ticker, <2023 tarihli replay günü>)` çağırıyordu ama `earnings.csv`
                # PIT DEĞİL — bugünün ileri-pencere snapshot'ı. 390 planın YALNIZ 10'unda takvimde
                # plan tarihinden sonraki 0-5 gün içinde bir rapor tarihi vardı; yani 380 planda
                # (%97,4) `in_blackout` zaten yapısal olarak False dönüyordu. Kapı canlıda diri,
                # replay'de ÖLÜ — üstelik `coverage: "known"` etiketi bunu ÖRTÜYORDU: o etiket plan
                # tarihindeki değil BUGÜNKÜ kapsamı yansıtıyordu, yani kayıt "kontrol edildi, temiz"
                # diyordu ve bu bir YALANDI (UYDURMA YASAĞI).
                #
                # ARTIK: bugünün takvimini tarihsel bir plana uygulayan yol TAMAMEN KAPALI.
                # `in_blackout` replay bacağında ÇAĞRILMIYOR (ne veto, ne etiket). Etiket dürüst:
                # "olculemedi_replay". Sayaç `earnings_gate`te birikir ve raporda görünür.
                #
                # NEDEN VETOYU "DOĞRU TAKVİMLE" HESAPLAMIYORUZ: PIT kazanç takvimi bu depoda YOK
                # (earnings.csv sembol başına 1,0 tarih tutuyor, geçmiş çapa biriktirmiyor). Onu
                # üretmeden veto koymak, ölçülmemiş bir kapıyı ölçülmüş gibi göstermek olurdu.
                # Kapının replay'de SIFIR etkisi olduğu artık YAZILI — sessiz sıfır değil, beyanlı.
                #
                # DİFERANSİYEL MOTOR NOTU (test_differential_v60'ın konusu): iki motor bundan böyle
                # bu satırda BİLEREK ayrışıyor ve ayrışmanın adı var. Canlı motorda takvim PIT'tir
                # (bugünün kararı bugünün takvimiyle verilir); replay'de değildir. "Aynı yasanın iki
                # kopyası" kusuru DEĞİL bu — aynı yasanın uygulanamadığı yerde uygulanmış NUMARASI
                # yapmayı bırakmak.
                _bl = False
                _ek = earnings.known(sig.ticker)     # yalnız BEYAN için (aşağıdaki nota girer)
                _eg["plan"] = _eg.get("plan", 0) + 1
                _eg["olculemedi_replay"] = _eg.get("olculemedi_replay", 0) + 1
                if _det is not None:
                    _det.append({"check": "earnings_blackout", "passed": True, "severity": "hard",
                                 "value": sig.ticker, "threshold": None,
                                 "coverage": "olculemedi_replay",
                                 "note": "replay: PIT kazanç takvimi yok — karartma kapısı bu kararda "
                                         "KONUŞMADI (bugünün takvimi tarihsel plana uygulanmaz)"})
                # BEYANLI FAIL-OPEN NOTU — AYNI YASA, İKİ MOTOR (2026-08-01). Yukarıdaki 2026-07-22
                # dersinin birebir tekrarı: kural iki motorda da uygulanıyor, KAYDI yalnız canlıda
                # yazılsaydı `test_differential_v60` haklı olarak ayrışma derdi ve replay'den
                # tohumlanan planlar "kapsam bilgisi hiç yokmuş" gibi görünürdü. Not KARAR
                # DEĞİŞTİRMEZ; sıra da canlıyla AYNI (önce karartma vetosu, sonra not).
                # `_ek` artık detay kapalıyken de ölçülür: maliyeti `_load()`in mtime-önbellekli tek
                # `stat()`ı — arama yolunda plan başına bir sistem çağrısı, ölçülü ve kabul edilmiş.
                if not _ek:
                    greasons = list(greasons) + [earnings.COVERAGE_NOTE]
                plan["gate_verdict"], plan["gate_reasons"] = verdict, greasons
                if _det is not None:
                    plan["gate_checks"] = _det
                if verdict != "NO_GO":                 # GO or REVIEW arm (== old pass); NO_GO does not
                    armed.append(plan)
                    armed_pivots[sig.ticker] = float(sig.pivot)     # G3b: yapı çizgisi plana DEĞİL yana
                    # C11/C18: ATR SİNYAL BARINDA ölçülmüştür (strategy.EntrySignal.atr) — silahlanma
                    # anında sabitlenir, dolum anında yeniden hesaplanmaz (canlı `entry_law` tablosuyla
                    # aynı yasa: aynı plan iki motorda iki farklı limitle dolamaz).
                    _a = float(sig.atr) if sig.atr else 0.0
                    armed_atr[sig.ticker] = _a if _a > 0 else None   # ölçülemedi → None (0.0 DEĞİL)
                    sector_ct[sec] = sector_ct.get(sec, 0) + 1
                    slots -= 1
                plan_log.append(plan)

        equity_curve.append((str(d.date()), round(broker.equity(marks_on(d)), 2)))

    # close anything still open at final bar's close (mark-out)
    if calendar:
        d = calendar[-1]
        for t in list(broker.positions.keys()):
            if t in per and d in per[t].index:
                broker.close_position(t, per[t].loc[d, "close"], "eod_markout", str(d.date()))
            else:
                # ticker's data ENDED before the final bar (delisting/halt — PARA/WBA class): without this
                # the position silently vanished from grading — its loss never hit n/avg_r/drawdown/tail
                # (audit #7/#46 survivorship no-op). Close at the last AVAILABLE bar's close instead.
                try:
                    last_d = per[t].index.max()
                    broker.close_position(t, per[t].loc[last_d, "close"], "delisted_markout",
                                          str(last_d.date()))
                except Exception as e:
                    # Kapatılamayan pozisyon simülasyonda AÇIK kalır: K/Z eksik, işlem sayısı düşük,
                    # skor yanlış. Sessizce atlanırsa backtest gerçeğe göre iyimser görünür.
                    _warn_once("markout_close_failed", ticker=t, error=f"{type(e).__name__}: {e}")

    return BacktestResult(trades=broker.closed, equity=equity_curve, params=params, start=start,
                          end=end, plan_log=plan_log, candidate_log=candidate_log,
                          entry_rejects=entry_rejects, earnings_gate=_eg)


def holding_day_r_curve(trades: list, max_day: int = 40) -> dict:
    """TIME-STOP KALİBRASYON EĞRİSİ (G3b ③, 2026-07-30) — SAF fonksiyon, I/O yok, knob DEĞİL.

    Soru: `exit.time_stop_days` = 15 doğru yerde mi? Şelale ölçümünde time_stop, çıkışın TEK güçlü
    bileşeniydi (+%50 verim) — yani zaman kesişi PARA KAZANDIRIYOR ve "nerede kesmeli" sorusu
    ölçülmeye değer. Bu fonksiyon kapanmış işlemlerden tutuş-günü bazında R muhasebesi çıkarır.

    ÖLÇÜMÜN SINIRI, EN BAŞTA VE AÇIKÇA — bu bir KARŞI-OLGU DEĞİLDİR. Kapanmış bir işlem yalnız
    KAPANDIĞI günü ve NİHAİ R'sini bilir; "gün 7'de kesseydim ne olurdu" sorusu, hâlâ açık olan
    işlemlerin gün-7 K/Z'sini gerektirir ve o bilgi `trades` içinde YOKTUR (mfe_r/mae_r bile ZAMANSIZ
    uçlardır — hangi barda olduğu kayıtta değil). Bu yüzden aşağıdaki `kumulatif_ort_r` "gün d'de
    kesersem ortalama R'm bu olur" DEĞİL, "gün d'ye KADAR kapanan işlemlerin ortalama R'si" demektir.
    İkisini karıştırmak, ölçülmemiş bir sayıyı ölçülmüş gibi raporlamak olurdu. Gerçek karşı-olgu
    replay'i time_stop değerleriyle YENİDEN KOŞMAKTIR (ölçüm scriptinin işi, tek bir fonksiyonun değil).

    NE VERİR (ve bu neden yeterince güçlü bir sinyal): `gunler[d]` = tam d bar tutulmuş işlemlerin
    sayısı + ortalama R'si + toplam R'si + çıkış sebebi dağılımı. Bir zaman kesişinin doğru yeri,
    marjinal günlerin İŞARETİNDEN okunur: geç günlerin R toplamı NEGATİFSE o günler masaya para
    koymuyor, KAYBETTİRİYOR — ve kesiş öne alınabilir. Pozitifse (kâr sağ kuyruktan gelir tezi)
    kesiş geciktirilebilir. `kuyruk_toplam_r[d]` = d gün ve SONRASINDA kapanan işlemlerin toplam R'si
    tam bu soruyu cevaplar ve karşı-olgu gerektirmez: bu işlemler GERÇEKTEN o kadar tutuldu.

    Dönüş: {"n": …, "ort_r": …, "gunler": [{"gun", "n", "ort_r", "toplam_r", "sebepler"}…],
             "kumulatif": [{"gun", "n_kumulatif", "kumulatif_ort_r", "kuyruk_n", "kuyruk_toplam_r"}…]}
    Boş girdi → n=0 ve boş listeler (uydurma sıfır eğrisi değil)."""
    rows = [t for t in (trades or []) if t.get("bars_held") is not None
            and t.get("r_multiple") is not None]
    n = len(rows)
    if n == 0:
        return {"n": 0, "ort_r": None, "gunler": [], "kumulatif": []}
    per_day: dict[int, list] = {}
    for t in rows:
        try:
            d = int(t["bars_held"])
            r = float(t["r_multiple"])
        except (TypeError, ValueError):
            # sessiz-yutma: biçimsiz bir defter satırı eğriye GİRMEZ ama KAYBOLMAZ — atlananların
            # sayısı dönen sözlüğün `n_atlanan` alanında raporlanır, yani "kaç satır ölçülemedi"
            # sorusu kayıttan cevaplanabilir kalır (uydurma bir R'yi eğriye sokmak alternatifti).
            continue
        per_day.setdefault(min(max(d, 0), max_day), []).append((r, str(t.get("exit_reason") or "?")))
    n_used = sum(len(v) for v in per_day.values())
    gunler = []
    for d in sorted(per_day):
        rs = [r for r, _ in per_day[d]]
        sebepler: dict[str, int] = {}
        for _, why in per_day[d]:
            sebepler[why] = sebepler.get(why, 0) + 1
        gunler.append({"gun": d, "n": len(rs), "ort_r": round(sum(rs) / len(rs), 4),
                       "toplam_r": round(sum(rs), 4),
                       "sebepler": dict(sorted(sebepler.items(), key=lambda kv: -kv[1]))})
    # KÜMÜLATİF/KUYRUK muhasebesi HAM toplamlardan yürür: `gunler[*]["toplam_r"]` rapor için 4 haneye
    # yuvarlanmış bir alandır ve 40 kovada birikince eğriyi ~1e-3 kaydırabilirdi (raporlanan sayı ile
    # hesaplanan sayının sessizce ayrışması).
    ham_toplam = {d: sum(r for r, _ in per_day[d]) for d in per_day}
    toplam_r = sum(ham_toplam.values())
    kumulatif, run_n, run_sum = [], 0, 0.0
    for g in gunler:
        run_n += g["n"]; run_sum += ham_toplam[g["gun"]]
        kumulatif.append({"gun": g["gun"], "n_kumulatif": run_n,
                          "kumulatif_ort_r": round(run_sum / run_n, 4),
                          # KUYRUK = bu gün DAHİL sonrası: "d gününden itibaren tutulan barlar toplamda
                          # ne kazandırdı?" Negatifse zaman kesişi o günden önceye alınabilir.
                          "kuyruk_n": n_used - run_n + g["n"],
                          "kuyruk_toplam_r": round(toplam_r - run_sum + ham_toplam[g["gun"]], 4)})
    return {"n": n_used, "n_atlanan": n - n_used, "ort_r": round(toplam_r / n_used, 4),
            "gunler": gunler, "kumulatif": kumulatif}


# ---- ② AÇIK-POZİSYON DÜŞÜŞÜ: M2M EĞRİSİNİN KENDİ RAPORU (WP-M borcu, 2026-08-01) ---------------
# NEDEN VAR. Kapının okuduğu `max_drawdown`, `score.score_detail` içinde KAPANMIŞ-İŞLEM eğrisiyle
# günlük M2M eğrisinin KÖTÜSÜ olarak birleşiyor (audit #6 düzeltmesi) — yani M2M zaten sayılıyor,
# ama AYRI BİR SAYI OLARAK HİÇBİR YERDE DURMUYOR. Sonuç: "kapalı işlem düşüşü %4,6 ama açık
# pozisyonlarla M2M %12,9" gibi bir bulgu ancak ÖLÇÜM BETİĞİYLE elde ediliyordu (EDG-2026-003
# kill#2 tam olarak böyle ölçüldü) ve her ölçüm turunda elle yeniden üretiliyordu.
#
# BU BLOK HÜKÜM VERMEZ — adı "veto" ama kapı değildir, VETONUN EŞİĞİNE GÖRE OKUNAN BİR RAPORDUR.
# Eşik `shadowlaw.DD_VETO_MARGIN`den gelir çünkü EDG-2026-003'ün kill ölçütü ("rampa-kapalı koşulda
# maxDD veto sınırını aşarsa") o sabiti adıyla anıyor; ikinci bir eşik tanımlamak aynı yasanın ikinci
# uygulaması olurdu. Kapının kendi düşüş vetosu (`reflect._gate_eval`, aday↔incumbent FARKI üzerinden)
# DEĞİŞMEDİ ve bu blok ona hiçbir girdi vermez.
#
# UYDURMA YASAĞI: eğri boşsa `max_mtm_dd` None ve `ihlal` None döner — "ihlal yok" DEĞİL,
# "ÖLÇÜLEMEDİ". Boş bir eğriden False üretmek, hiç bakılmamış bir koşula temiz kâğıdı vermekti.
MTM_DD_ORNEK_LIMIT = 5     # ihlal günlerinden çıktıya girecek İLK n örnek (defter şişmesin)


def mtm_dd_veto(equity_curve: list, esik: float | None = None,
                ornek: int = MTM_DD_ORNEK_LIMIT) -> dict:
    """Günlük M2M özkaynak eğrisinin tepe-altı düşüşü + veto eşiğine göre okunuşu (RAPOR).

    `equity_curve`: `BacktestResult.equity` biçimi — [(tarih, özkaynak)]. Dönüş, `walk_forward`ın
    `mtm_dd_veto` anahtarına aynen konur; hiçbir kapı kararına girmez."""
    from . import shadowlaw
    # EŞİĞİN KAYNAĞI DA RAPORLANIR: bir ölçüm turunda eşik elle verilmişse (duyarlılık taraması) o
    # rapor "yasanın eşiğiyle ölçüldü" diye okunamamalı — kaynak alanı yalanı imkânsız kılar.
    esik_kaynagi = "shadowlaw.DD_VETO_MARGIN" if esik is None else "cagiran_verdi"
    esik = float(shadowlaw.DD_VETO_MARGIN if esik is None else esik)
    ortak = {"esik": esik, "esik_kaynagi": esik_kaynagi, "hukum_verir": False,
             "kapsam": ("günlük piyasaya-göre (M2M) özkaynak eğrisinin tepe-altı düşüşü — AÇIK "
                        "pozisyonların çukurunu kapanmış-işlem eğrisi gizler. RAPOR: ölçüm "
                        "kartlarına girer, kapıya girmez.")}
    pts: list[tuple[str, float]] = []
    for satir in (equity_curve or []):
        try:
            tarih, eq = satir[0], float(satir[1])
        except (TypeError, ValueError, IndexError, KeyError):  # sessiz-yutma: biçimsiz eğri noktası düşüş hesabına GİREMEZ ama KAYBOLMAZ — `n_atlanan` alanında raporlanır, yani "eğrinin kaç noktası okunamadı" sorusu raporun kendisinden cevaplanabilir kalır
            continue
        pts.append((str(tarih)[:10], eq))
    n_atlanan = len(equity_curve or []) - len(pts)
    if not pts:
        return {**ortak, "olculdu": False, "max_mtm_dd": None, "ihlal": None,
                "ihlal_gunleri": [], "n_gun": 0, "n_ihlal_gunu": 0, "n_atlanan": n_atlanan,
                "pencere": None,
                "neden": "M2M eğrisi boş/biçimsiz — açık-pozisyon düşüşü ÖLÇÜLEMEDİ (sıfır değil)"}
    tepe = pts[0][1]
    maks = 0.0
    maks_gun = pts[0][0]
    ihlaller: list[dict] = []
    for tarih, eq in pts:
        tepe = max(tepe, eq)
        dd = ((tepe - eq) / tepe) if tepe > 0 else 0.0
        if dd > maks:
            maks, maks_gun = dd, tarih
        if dd > esik:
            ihlaller.append({"tarih": tarih, "dd": round(dd, 4),
                             "tepe": round(tepe, 2), "equity": round(eq, 2)})
    return {**ortak, "olculdu": True, "max_mtm_dd": round(maks, 4),
            "max_mtm_dd_gunu": maks_gun, "ihlal": bool(maks > esik),
            "ihlal_gunleri": ihlaller[:max(0, int(ornek))],
            "n_gun": len(pts), "n_ihlal_gunu": len(ihlaller), "n_atlanan": n_atlanan,
            "pencere": {"ilk": pts[0][0], "son": pts[-1][0]}, "neden": None}


# ---- ② DEVAMI: M2M EĞRİSİNİN DİLİMLENMESİ — TEK YASA, İKİ OKUYUCU (WP-M ②, 2026-08-02) ---------
# NEDEN AYRI FONKSİYON. Bu dilimleme yasası `segment_score` içinde satır-içiydi ve şimdi İKİNCİ bir
# okuyucu doğuyor (`walk_forward._mtm_search` → kapının açık-pozisyon düşüş bacağı). Aynı yasanın iki
# kopyası, bu depoda tekrar tekrar bulunan sürüklenme sınıfıdır (wf_fixtures'ın var oluş sebebi):
# biri değişir, diğeri sessizce eski yasada kalır ve İKİ FARKLI POPÜLASYON ölçülür. Tek uygulama.
# YARI-AÇIK [lo, seg_end): `_in_segment`in işlem yasasıyla AYNI sınır dilbilgisi — sınır günü iki
# komşu dilimde birden sayılamaz.
def mtm_slice(equity_curve: list, lo: str, seg_end: str) -> list:
    """Günlük M2M özkaynak eğrisinin [lo, seg_end) dilimi. Biçim korunur: [(tarih, özkaynak)]."""
    return [(dd, e) for dd, e in (equity_curve or []) if lo <= str(dd)[:10] < seg_end]


def _regime_slice(trades: list, eval_regime: str | None) -> list:
    """Phase 3 regime-isolated learning: when a hypothesis targets ONE regime (var@regime), it must be
    graded only on trades that occurred UNDER that regime. Every replay trade already carries the tag
    (broker writes pos.regime_at_plan as 'regime'). None → no filter (global hypothesis, global grading)."""
    if not eval_regime:
        return trades
    return [t for t in trades if str(t.get("regime")) == str(eval_regime)]


def _in_segment(t: dict, lo: str, seg_end: str) -> bool:
    """Segment membership: opened in [lo, seg_end) — HALF-OPEN so a boundary-date trade can never be
    counted in two adjacent segments/folds (audit #4) — AND closed by seg_end, so P&L realized from
    price action AFTER the segment (e.g. an OOS trade riding into the frozen holdout) can never leak
    into this segment's score (audit #3: 'holdout never drives acceptance' now holds by construction).
    A still-open trade near the boundary is graded in NO segment — a purge, not a leak."""
    op = str(t.get("ts_open", ""))[:10]
    cl = str(t.get("ts_close", ""))[:10]
    return bool(lo <= op < seg_end and (not cl or cl <= seg_end))


def segment_score(trades: list, goal: dict, seg_start: str, seg_end: str, embargo_days: int = 0,
                  mtm_equity: list | None = None) -> dict:
    """Score trades belonging to [seg_start(+embargo), seg_end) — see _in_segment for the membership
    law. Annualization uses the SEGMENT's calendar length (not the trade cluster's span), and drawdown
    folds in the daily mark-to-market curve when provided.

    --- FORMÜLÜN DÜZ-YAZI AÇIKLAMASI (Hafta 3a "ölçünün ölçümü" raporu, 2026-07-30) ---

    Bu fonksiyon `score.score_detail`e delege eder; kapının BÜYÜKLÜK yasasının okuduğu `oos_score`
    oradan gelir ve şudur:

        bileşik = kıs( 0,5 · ret_c  +  0,3 · dd_c  +  0,2 · sharpe_c ),   kıs(·) = [-1, +1]

        ret_c    = kıs( gerçekleşen_30g / hedef_30g )       hedef_30g = goal.target_return_30d = 0,07
        dd_c     = kıs( 1 − düşüş / maks_düşüş )            maks_düşüş = goal.max_drawdown = 0,08
        sharpe_c = kıs( sharpe / (2 · min_sharpe) )         min_sharpe = goal.min_sharpe = 1,2

        toplam_getiri   = Σ pnl_dolar / başlangıç_sermayesi
        gerçekleşen_30g = (1 + toplam_getiri)^(30 / segment_gün_sayısı) − 1
        sharpe          = ort(işlem_getirisi)/std(işlem_getirisi) · √(işlem/yıl)

    HANGİ TERİM NEYİ ÖDÜLLENDİRİYOR — VE NOMİNAL AĞIRLIK GERÇEK AĞIRLIK DEĞİL. `ret_c` NOMİNAL
    olarak yarısını (0,5) taşır ama YAŞADIĞI ARALIK çok küçüktür: çok yıllık bir toplam getiri
    30 GÜNE indirgenip AYLIK %7 hedefe bölünür, yani birkaç yılda üretilmiş +%6,8'lik bir getiri
    ret_c = 0,05 verir. Diskteki gerçek walk-forward kayıtlarında (state/sprint/.../probe_cache.json,
    7 ayrı ölçüm) ret_c ∈ [−0,040, +0,052]; aynı kayıtlarda dd_c ∈ [0,196, 0,380] ve
    sharpe_c ∈ [−0,726, +0,358]. Katkılara çevirince (0,2118 skorlu gerçek satır):

        0,5·0,052 = 0,026  (skorun %12'si)   ← "para kazandık mı?"
        0,3·0,380 = 0,114  (skorun %54'ü)    ← "düşüş sığ mıydı?"
        0,2·0,358 = 0,072  (skorun %34'ü)    ← "getiri düzgün müydü?"

    Yani kapının BÜYÜKLÜK yasası fiilen bir DÜŞÜŞ+DÜZGÜNLÜK yasasıdır; kâr terimi, ölçek
    seçiminden (aylık %7 hedef × 30/span indirgemesi) dolayı kendi aralığının ~1/20'sine
    sıkıştırılmıştır. Bir aday, kârı artırıp düşüşü ya da Sharpe'ı hafifçe bozarak bu skorda
    KAYBEDEBİLİR — ROADMAP §3.1'in "büyüklük yasası revizyonu gerekir mi?" sorusunun sayısal
    zemini budur. (Bu bir HATA raporu değil ÖLÇÜM: yasa bilinçli olarak risk-ağırlıklıdır; ölçülen
    şey, o ağırlığın nominal 0,3+0,2 değil fiilen ~0,88 olduğudur.)

    İKİNCİ YAPISAL NOT — FREKANS İKİ TERİMDE TERS YÖNDE ÇALIŞIR: n büyürse `sharpe_c` √(işlem/yıl)
    üzerinden BÜYÜR, ama `ret_c` yalnız Σpnl arttıysa büyür. Ortalama R'si düşüp işlem sayısı artan
    bir aday (S2 vakası: n 98→106) Sharpe'tan kazanıp getiriden kaybeder ve net etki işaretsizdir —
    "daha çok işlem = daha çok kanıt" sezgisi bu skorda otomatik ödül DEĞİLDİR.

    ÖLÇÜM BORCU KAPATILDI: bu ayrıştırma bugüne kadar hiçbir kapı kaydında yoktu (S1/S2 ve G3a
    ölçümleri yalnız `oos_score` sakladı, `oos_detail.components` saklamadı — o yüzden o vakaların
    terim kırılımı yeniden koşmadan çıkarılamıyor). Artık her resmî kapı değerlendirmesinde
    `validation_ledger.jsonl` satırının `oos_components` alanında duruyor."""
    lo = _embargoed_start(seg_start, embargo_days)
    seg = [t for t in trades if _in_segment(t, lo, seg_end)]
    try:
        import datetime as _dt
        span = (_dt.date.fromisoformat(seg_end) - _dt.date.fromisoformat(lo)).days
    except Exception:  # sessiz-yutma: span yalnız RAPOR alanıdır; None dürüstçe "bilinmiyor" der ve hiçbir kapı kararına girmez
        span = None
    mtm = mtm_slice(mtm_equity, lo, seg_end) or None
    return score_mod.score_detail(seg, goal, span_days=span, mtm_equity=mtm)


def _embargoed_start(seg_start: str, embargo_days: int = 0) -> str:
    """Lower bound of a segment after the purge zone: seg_start + embargo_days (calendar). Shared by the
    magnitude gate AND the tail-risk veto so they can never drift onto different trade populations (L1)."""
    if not embargo_days:
        return seg_start
    import datetime as dt
    try:
        return (dt.date.fromisoformat(seg_start) + dt.timedelta(days=embargo_days)).isoformat()
    except Exception as e:
        # seg_start'a düşmek AMBARGOYU FİİLEN KAPATIR: eğitim ve sınav pencereleri bitişir,
        # sızıntı başlar ve kapı olduğundan iyi bir OOS skoru ölçer. Asla sessiz olamaz.
        _warn_once("embargo_disabled", seg_start=str(seg_start), error=f"{type(e).__name__}: {e}",
                   detail="ambargo uygulanamadı — OOS skoru SIZINTILI olabilir")
        return seg_start


def _fold_metrics(trades: list, fold_bounds: list, embargo_days: int) -> list:
    """Per-fold LIGHT metrics (avg realized R + n) over consecutive windows, WITHOUT a min_sample
    floor — folds are short (~6mo) so a composite score would be None everywhere. avg_r is meaningful
    with a handful of trades and is used only for the robustness/majority check, not the magnitude gate."""
    import datetime as dt
    out = []
    for i in range(len(fold_bounds) - 1):
        lo, hi = fold_bounds[i], fold_bounds[i + 1]
        if embargo_days:
            try:
                lo = (dt.date.fromisoformat(lo) + dt.timedelta(days=embargo_days)).isoformat()
            except Exception as e:
                _warn_once("embargo_disabled", fold_lo=str(lo), error=f"{type(e).__name__}: {e}",
                           detail="kat ambargosu uygulanamadı — fold skoru SIZINTILI olabilir")
        seg = [t for t in trades if _in_segment(t, lo, hi)]   # same half-open + closed-by law as the gate
        n = len(seg)
        avg_r = round(sum(float(t.get("r_multiple", 0.0)) for t in seg) / n, 4) if n else None
        out.append({"start": fold_bounds[i], "end": hi, "n": n, "avg_r": avg_r})
    return out


# ---- N-DENGELİ FOLD KESİMİ (Kârlılık Programı Aşama 2.1, 2026-07-28) --------------------------
# NEDEN: fold sınırları bugüne kadar TAKVİMDEN geliyordu (`dataset.OOS_FOLDS` = sabit tarih listesi).
# Takvim eşit uzunlukta pencereler üretir; PİYASA eşit sayıda işlem üretmez. Canlı ölçüm: OOS fold
# dağılımı [45, 46, 7]. Üçüncü fold 7 işlemle kapı OYLAMASINA eşit ağırlıkla katılıyordu — yani üç
# oylu bir çoğunlukta bir oy tamamen gürültüydü ve bir adayın kaderi o gürültüye bağlanabiliyordu.
# 7 işlemlik bir ortalama R, "bu pencerede de sağlam" cümlesini KURAMAZ.
#
# YÖNTEM VE KARŞILAŞTIRILABİLİRLİK ŞARTI: sınırlar YALNIZ incumbent'ın OOS işlem zaman damgalarından
# TEK KEZ türetilir, sonra incumbent VE adaya AYNEN uygulanır. Adayın kendi işlemleri kesime
# girseydi her aday kendi lehine bir pencere bölünmesi doğurur ve iki taraf farklı pencerelerde
# ölçülürdü — kapının elma-armut karşılaştırması yasağının ta kendisi.
#
# KAPI YASASININ SEMANTİĞİ DEĞİŞMEZ: fold çoğunluğu, VaR/CVaR kuyruk vetosu, k_probes cezası ve
# GATE_MARGIN aynen yürürlükte. Değişen YALNIZ sınırların nerede kesildiği.
FOLD_TARGET_N = 25     # hedef minimum fold işlem sayısı: bu civarda bir ortalama R'nin işareti
                       # örneklem gürültüsünden ayrılmaya başlar (canlı fold 3 = 7 işlemdi)
FOLD_MIN_N = 15        # SERT TABAN — bunun altında fold ÜRETİLMEZ. n<15 bir pencere, "sağlamlık"
                       # oylamasında oy kullanamaz; oy kullanırsa çoğunluk gürültüyle belirlenir.
FOLD_K_TRY = (3, 2)    # önce 3 fold denenir; taban dolmuyorsa 2'ye düşülür (asla 1'e değil:
                       # tek pencerelik bir edge sağlamlığın kanıtı değil ZITTIDIR — _gate_eval'in
                       # `fold_total == 1 → majority False` yasası da aynı şeyi söyler)


def balanced_fold_bounds(trades: list, hi: str, embargo_days: int = 0,
                         k_try: tuple = FOLD_K_TRY) -> list:
    """İşlem-SAYISI-dengeli fold sınırları; tam deterministik (yalnız sıralı tarihlere bakar).

    `trades` = sınırların türetileceği taraf (incumbent'ın Search-OOS işlemleri). `hi` = üst sınır
    (yarı-açık: dilimin dışı). Dönüş: `_fold_metrics`e verilebilecek sınır listesi, ya da hiçbir
    bölünme tabanı tutturamıyorsa BOŞ LİSTE.

    BOŞ LİSTE = "kontrol ÇALIŞTIRILAMADI" ve `_gate_eval` bunu `fold_total == 0` olarak okur (veto
    değil). Bu dal pratikte ulaşılamaz: olasılıksal yasanın kendi `thin` tabanı iki tarafta da en az
    `min_sample*0.7` (canlıda 21) işlem arar, yani 2×15'i tutturamayan bir aday zaten büyüklük
    kapısından geçemez. İki koruma birbirini kilitler; yine de sessiz bir "fold yok" hâli doğmasın
    diye sebep `_gate_eval`in kapı kaydına yazılır.

    AMBARGO ÇİFTE UYGULANMAZ: gelen işlemler zaten `walk_forward`ta ambargolu alt sınırdan sonrasını
    kapsıyor. `_fold_metrics` her sınıra ambargo EKLEDİĞİ için ilk sınır o kadar GERİ alınır — aksi
    hâlde ilk fold, bir kez daha purge edilerek haksızca inceltilirdi (ve dengeleme bozulurdu)."""
    import datetime as dt
    tarihler = sorted(str(t.get("ts_open") or "")[:10] for t in (trades or [])
                      if str(t.get("ts_open") or "")[:10] and str(t.get("ts_open") or "")[:10] < hi)
    if len(tarihler) < FOLD_MIN_N * min(k_try):
        return []
    n = len(tarihler)
    try:
        ilk = (dt.date.fromisoformat(tarihler[0]) - dt.timedelta(days=embargo_days)).isoformat()
    except ValueError as e:
        # YASA 4: biçimsiz bir `ts_open` dengelemeyi SESSİZCE kapatır ve kapı, hiçbir yerde
        # görünmeden takvim fold'larına geri düşerdi — yani reform "çalışıyor" sanılırken
        # çalışmıyor olurdu. Davranış aynı (takvime dön), ama artık adıyla görünüyor.
        _warn_once("balanced_folds_disabled", first_ts=str(tarihler[0]),
                   error=f"{type(e).__name__}: {e}",
                   detail="fold dengelemesi yapılamadı — takvim fold'ları yürürlükte kalır")
        return []
    aday_sinirlar = []
    for k in k_try:
        # EŞİT-SAYI QUANTILE KESİMİ: i·n/k indeksindeki işlemin tarihi sınır olur (yarı-açık yasa
        # gereği o işlem BİR SONRAKİ fold'a düşer). Aynı güne düşen çok sayıda işlem sınırı
        # tekrarlatabilir; tekrar eden sınır boş fold üretir, o yüzden ayrıştırılır ve k düşer.
        kesim = [ilk] + [tarihler[(i * n) // k] for i in range(1, k)] + [hi]
        temiz = [kesim[0]]
        for b in kesim[1:]:
            if b > temiz[-1]:
                temiz.append(b)
        if len(temiz) == k + 1:
            aday_sinirlar.append((k, temiz))
    # SEÇİM: SERT TABANI TUTTURAN EN ÇOK FOLD'LU KESİM.
    #
    # BURADA BİR TASARIM DÜZELTMESİ VAR (ölçülerek bulundu, 2026-07-28 — brief'in düz okunuşundan
    # SAPMA, gerekçesi şu): "önce hedefi (n>=25) tutturan kesim, olmazsa fold sayısını düşür" kuralı
    # DAHA ÇOK VERİYLE DAHA AZ FOLD üretiyordu. Ölçüldü: 50 işlem → 3 fold [16,16,15]; 90 işlem →
    # 2 fold [45,42]. Sebep, ambargo ve "kapanışı dilim içinde" kuralının k=3'te bir fold'u 24'e
    # (hedefin bir altına) tıraşlaması; kural o zaman k=2'ye düşüyor ve hedefi orada buluyordu.
    #
    # Bu YALNIZ tuhaf değil, KAPIYI GEVŞETİYOR: çoğunluk yasası `fold_wins >= (fold_total+1)//2`
    # olduğu için 2 fold'da BİR galibiyet yeterlidir, 3 fold'da İKİ gerekir. Yani "daha büyük
    # örneklem" uğruna fold sayısını düşürmek, sağlamlık sınavını fiilen kolaylaştırıyordu.
    # Doğru muhafazakâr seçim: taban tuttuğu sürece EN ÇOK fold. FOLD_TARGET_N ölü sabit değildir —
    # kesimin hedefi tutturup tutturmadığı `fold_target_met` ile kapı kaydına yazılır ve panoda
    # okunur; yani aspirasyon ölçülür, ama sınavı kolaylaştırmak için kullanılmaz.
    uygun = []
    for k, sinirlar in aday_sinirlar:
        folds = _fold_metrics(trades, sinirlar, embargo_days)
        if folds and min(f["n"] for f in folds) >= FOLD_MIN_N:
            uygun.append((k, sinirlar))
    return max(uygun, key=lambda ks: ks[0])[1] if uygun else []


def walk_forward(params: dict, bars: dict, index_bars: pd.DataFrame, goal: dict,
                 is_start: str, oos_start: str, oos_end: str, holdout_end: str,
                 strategy_version: int = 1, oos_folds: list | None = None, embargo_days: int = 0,
                 params_by_regime: dict | None = None, eval_regime: str | None = None) -> dict:
    """Replay once over [is_start, holdout_end]. Two-part gate:
      * MAGNITUDE — the full OOS window's composite score (min_sample-gated; None below the floor).
      * ROBUSTNESS — per-fold avg_r across SEVERAL purged+embargoed folds, so the edge can't hinge on
        one lucky window. Folds use avg_r (no min_sample floor) since each is short.
    The frozen holdout is reported to the human only and never drives acceptance.
    eval_regime (Phase 3): grade ONLY trades tagged with that regime — the REPLAY itself is untouched
    (portfolio effects stay realistic); only the scoring population narrows. The min_sample floor then
    applies to the regime slice, so a thin regime honestly yields score=None (cannot ship) instead of a
    noisy small-sample verdict. The caller must use the same eval_regime for incumbent AND candidate."""
    res = replay(params, bars, index_bars, goal, is_start, holdout_end, strategy_version,
                 params_by_regime=params_by_regime)
    graded = _regime_slice(res.trades, eval_regime)
    is_d = segment_score(graded, goal, is_start, oos_start, mtm_equity=res.equity)
    oos_d = segment_score(graded, goal, oos_start, oos_end, embargo_days, mtm_equity=res.equity)
    hold_d = segment_score(graded, goal, oos_end, holdout_end, mtm_equity=res.equity)
    # ---- CONFIRM-OOS SIZINTISI KAPATILDI (2026-07-22, kapı denetimi bulgu #1) ----
    # `oos_pipeline` Confirm dilimini "aramanın ASLA dokunmadığı %30" diye tanımlıyor. Ama fold'lar
    # ve kuyruk riski TAM OOS üzerinde hesaplanıyordu ve `reflect._gate_eval` bunları HER SONDADA
    # okuyordu. Ölçüldü: fold 3 = [2025-01-11, 2025-12-31) Confirm penceresinin 354 gününün 274'ünü
    # (%77) kapsıyor; kuyruk vetosunun popülasyonu ise Confirm'in TAMAMI. Kanıt: Search dilimleri
    # BİREBİR aynı (search_p 0.9965) iki aday, yalnız Confirm işlemleri farklı olduğu için ZIT karar
    # alıyordu — biri geçiyor, diğeri fold_wins 3/3 → 2/3 ve tail_ok kaybediyordu.
    # Sonuç: teyit yürüyüşü "dokunulmamış" bir dilimde değil, adayın zaten ÖN ELEMEDEN geçtiği bir
    # dilimde yapılıyordu — kazananın-laneti savunması fiilen yoktu.
    # Düzeltme: arama yasasının gördüğü fold ve kuyruk YALNIZ Search-OOS'tan hesaplanır.
    from .oos_pipeline import split_date as _split_date
    _search_end = _split_date(oos_start, oos_end)
    _search_folds = [b for b in (oos_folds or []) if b < _search_end] + [_search_end] \
        if oos_folds else []
    folds = _fold_metrics(graded, _search_folds, embargo_days) if len(_search_folds) >= 2 else []
    avgs = [f["avg_r"] for f in folds if f["avg_r"] is not None]
    # Tam-OOS fold'ları RAPOR için korunur (bilgi atılmaz) ama hiçbir arama kararına girmez.
    folds_full = _fold_metrics(graded, oos_folds, embargo_days) if oos_folds else []
    # tail-risk on the OOS window's trades (capital-preservation gate; None below TAIL_MIN_SAMPLE). Uses the
    # SAME membership law (embargoed lower bound + half-open + closed-by) as the magnitude gate — the hard
    # tail veto must never run on a different trade population than the rest of the gate (L1 + #3/#4).
    _tail_lo = _embargoed_start(oos_start, embargo_days)
    # KUYRUK DA SEARCH'E DARALTILDI (aynı bulgu): veto popülasyonu Confirm'in tamamını kapsıyordu.
    tail = score_mod.tail_risk([t for t in graded if _in_segment(t, _tail_lo, _search_end)])
    tail_full = score_mod.tail_risk([t for t in graded if _in_segment(t, _tail_lo, oos_end)])
    # v3 olasılıksal kapı dilimleri: OOS kronolojik %70 Search / %30 Confirm. Arama adayları yalnız
    # Search'te yarışır; kazanan Confirm'de teyit yürüyüşüne girer (oos_pipeline). Embargo Search'ün
    # alt sınırına aynen uygulanır — kapının hiçbir parçası farklı popülasyon göremez.
    _s_end = _search_end
    return {
        "params": params, "n_trades_total": len(res.trades),
        "eval_regime": eval_regime, "n_trades_graded": len(graded),
        "oos_split": {"search_start": _tail_lo, "search_end": _s_end,
                      "confirm_start": _s_end, "confirm_end": oos_end},
        "_trades_search": [t for t in graded if _in_segment(t, _tail_lo, _s_end)],
        "_trades_confirm": [t for t in graded if _in_segment(t, _s_end, oos_end)],
        # ② AÇIK-POZİSYON DÜŞÜŞÜNÜN KAPIYA GİDEN YOLU (WP-M ②, 2026-08-02). `reflect._gate_eval`in
        # düşüş vetosu bugüne kadar YALNIZ kapanmış-işlem eğrisini okuyabiliyordu ve bunun sebebi
        # kendi yorumunda adıyla yazılıydı: "walk_forward o eğriyi DİLİM BAŞINA döndürmüyor".
        # Artık döndürüyor. Dilim, `_trades_search` ile BİREBİR aynı sınırlardır (embargolu alt
        # sınır + yarı-açık üst sınır) — veto bacağının iki tarafı farklı pencere görürse kıyas
        # kıyas olmaktan çıkardı. Alt çizgili anahtar: `_trades_*` ile AYNI sözleşme — kapı girdisi,
        # HÜKÜM DEFTERLERİNE (validation_ledger/kapı kaydı) yazılmaz.
        # MALİYET BEYANI (ölçüldü, tahmin değil): `reflect._inc_disk_save` incumbent walk'ın TÜM
        # sözlüğünü `state/inc_cache.json`a serileştirir, yani bu anahtar O DOSYAYI büyütür —
        # canlı R1 Search penceresinde (2024-01-11→2025-08-18, ~417 iş günü) kayıt başına ~11 KB,
        # 40 kayıtlık tavanda üst sınır ~440 KB (dosya bugün 190 KB). Eğriyi diskten KIRPMAK
        # alternatifti ve REDDEDİLDİ: önbellekten gelen incumbent eğrisiz kalırdı, kapı sessizce
        # "olculemedi" yazardı ve ölçüm hiç birikmezdi — yani bacağın var oluş sebebi ölürdü.
        "_mtm_search": mtm_slice(res.equity, _tail_lo, _s_end),
        "is_score": is_d["score"], "is_detail": is_d,
        "oos_score": oos_d["score"], "oos_detail": oos_d,          # magnitude gate
        "oos_folds": folds, "oos_fold_avg_r_mean": round(sum(avgs) / len(avgs), 4) if avgs else None,
        "oos_tail_risk": tail,           # SEARCH dilimi — arama yasasının gördüğü tek kuyruk
        # Rapor/teşhis için tam-OOS karşılıkları; hiçbir kapı kararına GİRMEZ (sızıntı olurdu).
        "oos_folds_full": folds_full, "oos_tail_risk_full": tail_full,
        "holdout_score": hold_d["score"], "holdout_detail": hold_d,
        "full_detail": res.detail(goal),
        # ② AÇIK-POZİSYON DÜŞÜŞÜ (WP-M, 2026-08-01): TAM replay penceresinin ([is_start,
        # holdout_end]) M2M eğrisi üzerinden. Dilim SEÇİLMEZ çünkü blok kapıya girmez ve dilim
        # seçmek "hangi pencerede kırmızı?" sorusunu rapor okuyucusundan gizlerdi; pencere
        # `pencere` alanında adıyla yazılıdır. `oos_detail.max_drawdown` bu eğriyi ZATEN
        # kapanmış-işlem eğrisiyle birleştirip tek sayıya indiriyor — bu blok o birleşmeden ÖNCEKİ
        # M2M sayısını ayrı tutar (EDG-2026-003'ün "kapalı %9,7 / M2M %12,9" bulgusunun kalıcı hâli).
        "mtm_dd_veto": mtm_dd_veto(res.equity),
    }

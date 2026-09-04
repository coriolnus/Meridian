"""analytics.py — panonun okuma-modeli: state/ üzerinden türetilen analitik hesapların tek çatısı.

NE YAPAR. Panonun gösterdiği her sayı burada GERÇEK state'ten türetilir, asla fikstürden değil.
Skor/kalibrasyon ölçümleri, kenar ve sonuç hükümleri, portföy ısısı, otonomi merdiveni, rejim
hücreleri ve öğrenme karneleri tek modülde durur ki iki yüzey aynı ölçüyü iki ayrı formülle
anlatmasın.

KİLİT GİRİŞLER. `edge_verdict()` / `result_verdict()` — istatistiksel anlamlılıkla (blok
bootstrap CI, CVaR) ölçüt satırları; `portfolio_heat()` — açık risk toplamı; `autonomy_ladder()`
(+`_breaker_trips_since`: takvim-günü penceresi — satır penceresi olay seli altında sessizce
daralıyordu, ts-tabanlıya düzeltildi ve taranan kapsam BEYAN edilir); `per_regime_scores`,
`skill_attribution`, `score_calibration`/`spearman_ic`, `llm_opinion_calibration`,
`exit_efficiency`, `profit_waterfall`, `cf_fidelity`, `near_miss_report`, `regime_edge`,
`benchmark_relative`, `trade_alpha_beta`, `live_expectancy_ceiling` (ölçer ve beyan eder, hükme
girmez), `learning_scorecard`, `hermes_scorecard`, `shadow_law_row`, `mae_profile`,
`shrunk_regime_cells` (empirik Bayes büzülmesi).

DEĞİŞMEZLER. Defterlere (trades/plans/portfolio/scoreboard) ASLA yazılmaz; salt-okunur
read-model'in tek istisnası, kendi türetilmiş kalibrasyon artefaktını kalıcılaştıran üreticilerdir
(`llm_calibration.json`, `exit_efficiency.json`, `cf_fidelity.json`, `near_miss.json`,
`regime_edge.json`, `mae_profile.json`, `score_calibration_history.jsonl` — idempotent nokta
kaydı). Ölçülemeyen değer None döner, sıfırla doldurulmaz (UYDURMA YASAĞI); pencere/kapsama
iddiası ölçülen gerçeğe göre beyan edilir ("son 30 gün" tavana çarptıysa bunu söyler).

NEYİ OKUR. `trades.jsonl`, `trade_plans.jsonl`, `events.jsonl`, portföy/karne/eğri defterleri ve
kalibrasyon artefaktları — hepsi store üzerinden."""
from __future__ import annotations
import datetime as dt
from collections import defaultdict

from . import store, config, score as score_mod, health, memory


def _trades():
    """Kapanmış işlem defterinin (`trades.jsonl`) tüm satırları — bu modülün ANA okuma kapısı.

    TEK KAPI DEĞİL (borç kaydı, ölçüldü): `learning_scorecard` aynı defteri
    `store.read_jsonl("trades.jsonl")` ile DOĞRUDAN, bu fonksiyona uğramadan ikinci kez okur
    (defterin damga ayrıştırmasını `ledgerstamp.counts` ile kendisi yapar). İkinci okuyucu
    ADIYLA beyanlıdır ki "tek kapı" cümlesi denetlenmemiş bir tekillik iddia etmesin; kapı
    gerçekten tekleşirse o çağrı buraya bağlanmalı ve bu paragraf silinmelidir."""
    return store.read_jsonl("trades.jsonl")


# Otonomi merdiveninin devre-kesici penceresi TAKVİM cinsindendir (bkz. `autonomy_ladder`). 30 gün:
# merdivenin diğer ölçütleri (60 kapanmış işlem, 2 rejimde pozitif skor) de bir aylık ölçekte
# konuşuyor; pencere onlardan kısa olsaydı "temiz sicil" cümlesi diğer ölçütlerle aynı defteri
# anlatmıyor olurdu.
LADDER_BREAKER_WINDOW_DAYS = 30
LADDER_BREAKER_SCAN_CAP = 60_000   # okuma maliyeti tavanı (olay defteri MB'larca): satır değil, ÜST SINIR


def _breaker_trips_since(days: int = LADDER_BREAKER_WINDOW_DAYS) -> tuple[int, dict]:
    """Son `days` TAKVİM GÜNÜNDEKİ devre-kesici alarmlarını sayar (satır penceresi değil).

    Neden ts-tabanlı: bkz. `autonomy_ladder` içindeki gerekçe — olay defteri sel altındayken satır
    penceresi kendiliğinden daralıyor ve "temiz sicil" iddiası sessizce yarım saate iniyordu.
    Dönen sözlük TARANMIŞ pencereyi beyan eder: tavana çarpıldıysa (`kapak_doldu`) iddia "son 30
    gün" DEĞİL "taranan en eski olaydan bu yana"dır ve çıktı bunu söyler."""
    import datetime as _dt
    from . import obs
    rows = obs.recent(LADDER_BREAKER_SCAN_CAP)
    kesim = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=int(days))).isoformat()
    n_scanned = 0
    trips = 0
    oldest = None
    for e in rows:
        ts = str(e.get("ts") or "")
        if ts and ts < kesim:
            continue
        n_scanned += 1
        if oldest is None or (ts and ts < oldest):
            oldest = ts
        if e.get("alarm") == obs.ALARM_CIRCUIT_BREAKER:
            trips += 1
    return trips, {"days": int(days), "n_scanned": n_scanned, "oldest": oldest,
                   "kapak_doldu": len(rows) >= LADDER_BREAKER_SCAN_CAP,
                   "kapsam": ("taranan en eski olaydan bu yana (satır tavanı doldu — pencere "
                              "beyan edilenden KISA olabilir)" if len(rows) >= LADDER_BREAKER_SCAN_CAP
                              else f"son {int(days)} takvim günü")}


def per_regime_scores(goal: dict | None = None) -> dict:
    """Rejim başına skor karnesi: `{rejim: {n, score, win_rate, avg_r, total_return}}`.

    İşlemler `regime` alanına göre gruplanır (alan yoksa "?" kovası) ve her grup ayrı ayrı
    `score.score_detail`den geçer. Salt-okuma."""
    goal = goal or config.goal()
    trades = _trades()
    by = defaultdict(list)
    for t in trades:
        by[t.get("regime", "?")].append(t)
    out = {}
    for reg, ts in by.items():
        d = score_mod.score_detail(ts, goal)
        out[reg] = {"n": len(ts), "score": d["score"], "win_rate": d.get("win_rate"),
                    "avg_r": d.get("avg_r"), "total_return": d.get("total_return")}
    return out


def per_skill_hit_rate() -> dict:
    """Hit rate (win rate) by the screening skill that sourced each trade's plan."""
    trades = _trades()
    by = defaultdict(lambda: {"n": 0, "wins": 0})
    for t in trades:
        chain = t.get("skill_chain", [])
        src = chain[0] if chain else "?"
        by[src]["n"] += 1
        by[src]["wins"] += 1 if t.get("r_multiple", 0) > 0 else 0
    return {k: {"n": v["n"], "hit_rate": round(v["wins"] / v["n"], 3) if v["n"] else None}
            for k, v in by.items()}


def skill_attribution() -> dict:
    """Axis-2 groundwork: performance attribution across EVERY skill in each trade's chain (not just the
    source). Per skill: trades touched, win rate, avg R, and total R contributed. This is the honest
    signal a skill-evolution loop needs — which skills ride the winners and which drag — before any skill
    is auto-rewritten. Sorted worst avg_r first so the weakest link surfaces at the top."""
    trades = _trades()
    by = defaultdict(lambda: {"n": 0, "wins": 0, "sum_r": 0.0})
    for t in trades:
        r = float(t.get("r_multiple", 0.0))
        seen = set()
        for sk in t.get("skill_chain", []) or ["?"]:
            if sk in seen:                        # count each skill once per trade
                continue
            seen.add(sk)
            by[sk]["n"] += 1
            by[sk]["wins"] += 1 if r > 0 else 0
            by[sk]["sum_r"] += r
    # #3: karşı-olgusal defter — screener başına SİMÜLE katkı (ayrı sütunlar; Eksen-2 önerileri ve
    # sıralama GERÇEK sütunlardan; cf yalnız erken-uyarı kanıtıdır ve panelde 'sim' etiketiyle ayrışır)
    cf_by = defaultdict(lambda: {"n": 0, "sum_r": 0.0})
    try:
        from . import counterfactual as _cf
        for r2 in _cf.resolved_rows(entered_only=True):
            sk2 = r2.get("screener")
            if sk2 and r2.get("r_multiple") is not None:
                cf_by[sk2]["n"] += 1
                cf_by[sk2]["sum_r"] += float(r2["r_multiple"])
    except Exception as e:
        # cf tarafı düşerse beceri katkısı YALNIZ gerçek işlemlerden hesaplanır ve tablo
        # "bu araç az kullanılmış" der — oysa kanıt okunamamıştır.
        from . import obs
        obs.warn("skill_attribution_cf_unavailable", error=f"{type(e).__name__}: {e}",
                 detail="beceri katkısı yalnız gerçek işlemlerden — cf kanıtı DIŞARIDA")
    all_names = set(by) | set(cf_by)
    out = []
    for k in all_names:
        v = by.get(k, {"n": 0, "wins": 0, "sum_r": 0.0})
        c2 = cf_by.get(k)
        out.append({"skill": k, "n": v["n"],
                    "win_rate": round(v["wins"] / v["n"], 3) if v["n"] else None,
                    "avg_r": round(v["sum_r"] / v["n"], 3) if v["n"] else None,
                    "total_r": round(v["sum_r"], 2),
                    "n_cf": c2["n"] if c2 else 0,
                    "cf_avg_r": round(c2["sum_r"] / c2["n"], 3) if c2 and c2["n"] else None})
    out.sort(key=lambda x: (x["avg_r"] if x["avg_r"] is not None else 0.0))
    return {"skills": out, "n_trades": len(trades)}


def autonomy_ladder(goal: dict | None = None) -> dict:
    """L0->L1 promotion criteria, each computed from real state. Manual/infra items are flagged.
    guard.py enforces these; the dashboard renders how far the agent is from being trusted with money."""
    goal = goal or config.goal()
    trades = _trades()
    n = len(trades)
    regs = per_regime_scores(goal)
    positive_regimes = [r for r, v in regs.items() if v["score"] is not None and v["score"] > 0]
    detail = score_mod.score_detail(trades, goal)
    max_dd = detail.get("max_drawdown") if detail.get("score") is not None else None
    hyps = memory.all_hypotheses()
    calibrated = [h for h in hyps if h.get("calibration_hit") is True]

    # count REAL circuit-breaker alarms from the event log (was hardcoded True — a vanity pass on a
    # criterion that gates real money). obs.alarm() tags the event with fields["alarm"]=<token>.
    #
    # SAYIM TS-TABANLI OLDU. ESKİSİ `obs.recent(400)` idi — SATIR sayısıyla
    # sınırlı bir pencere. Denetim olay defterinin %91'inin `hotstate_down` olduğunu ölçtü
    # (6.834 kopma / 24 saat): 400 satır, sel varken YARIM SAATİ kapsıyor. Yani "son 400 olayda
    # devre kesici tetiklenmedi" cümlesi, otonomi merdiveninde "temiz sicil" olarak okunuyordu ama
    # fiilen "son yarım saatte" demekti — ve gürültü arttıkça pencere KENDİLİĞİNDEN daralıyordu.
    # Artık pencere TAKVİMDİR (LADDER_BREAKER_WINDOW_DAYS gün) ve satır tavanı yalnız okuma
    # maliyetini sınırlar; kaç olayın gerçekten tarandığı çıktıda görünür.
    breaker_trips = 0
    breaker_window = None
    try:
        from . import obs
        breaker_trips, breaker_window = _breaker_trips_since(LADDER_BREAKER_WINDOW_DAYS)
    except Exception as e:
        # 0 tetiklenme, otonomi merdiveninde "temiz sicil" olarak okunur — okunamayan olay defteri
        # temiz sicil DEĞİLDİR ve merdiveni haksız yere yükseltebilir.
        from . import obs as _o
        _o.warn("ladder_breaker_count_unavailable", error=f"{type(e).__name__}: {e}",
                detail="devre kesici sicili OKUNAMADI — 0 sanılmasın")
        breaker_trips = 0
        breaker_window = {"okunamadi": True}

    def crit(label, met, detail_str, manual=False):
        """Merdiven ölçütünü tek satırda paketler: etiket, sağlandı mı, açıklama ve ELLE mi.

        `manual=True` olan ölçütler operatör/altyapı adımıdır; otomatik ilerleme sayacına girmez."""
        return {"label": label, "met": bool(met), "detail": detail_str, "manual": manual}

    l0_l1 = [
        crit("≥ 60 closed paper trades", n >= 60, f"{n} / 60"),
        crit("Positive score in ≥ 2 regimes", len(positive_regimes) >= 2,
             f"{len(positive_regimes)} regimes positive: {', '.join(positive_regimes) or 'none'}"),
        crit(f"Max drawdown within {goal['max_drawdown']*100:.0f}%",
             max_dd is not None and max_dd <= goal["max_drawdown"],
             f"{max_dd*100:.2f}% observed" if max_dd is not None else "score below min_sample"),
        crit("≥ 3 accepted hypotheses matched prediction", len(calibrated) >= 3,
             f"{len(calibrated)} / 3 calibrated"),
        crit("Zero unexplained breaker trips (recent events)", breaker_trips == 0,
             f"{breaker_trips} observed — pencere: " + (
                 "olay defteri OKUNAMADI" if (breaker_window or {}).get("okunamadi")
                 else f"son {LADDER_BREAKER_WINDOW_DAYS} gün "
                      f"({(breaker_window or {}).get('n_scanned', 0)} olay tarandı, "
                      f"en eski {(breaker_window or {}).get('oldest') or '?'})")),
        crit("Broker key: withdrawals disabled + VM IP allow-listed", False,
             "operator/infra step at promotion time", manual=True),
        crit("Both env flags hand-set (MERIDIAN_MODE=live, I_ACCEPT_RISK=true)",
             config.live_enabled(), "operator step; refused by engine at L0", manual=True),
        crit("Phone kill-switch wired", False, "infra step at promotion time", manual=True),
    ]
    auto_met = sum(1 for c in l0_l1 if c["met"] and not c["manual"])
    auto_total = sum(1 for c in l0_l1 if not c["manual"])
    return {
        "current_level": goal["limits"]["autonomy_level"],
        "levels": [
            {"id": "L0", "name": "Paper, fully autonomous", "active": goal["limits"]["autonomy_level"] == 0},
            {"id": "L1", "name": "Live, every order approved", "active": goal["limits"]["autonomy_level"] == 1},
            {"id": "L2", "name": "Live, autonomous", "active": goal["limits"]["autonomy_level"] == 2},
        ],
        "l0_to_l1": l0_l1,
        "auto_progress": {"met": auto_met, "total": auto_total},
    }


def today() -> dict:
    """Panonun "bugün" görünümü: nabız + bayatlık/HALT, rejim, açık pozisyonlar, EN SON tarihli plan
    kümesi ve hüküm dağılımı, açık risk ve maruziyet yüzdesi.

    SALT-OKUMA: yalnız state artefaktlarını okur, hiçbir dosyaya yazmaz ve hiçbir kapıyı beslemez."""
    hb = store.read_json("heartbeat.json", {})
    regime = store.read_json("regime.json", {})
    portfolio = store.read_json("portfolio.json", {})
    plans = store.read_jsonl("trade_plans.jsonl")
    dated = [p.get("date") for p in plans if p.get("date")]
    latest_date = dated[-1] if dated else None
    todays_plans = [p for p in plans if p.get("date") == latest_date] if latest_date else []
    open_positions = []
    for tk, p in (portfolio.get("positions", {}) or {}).items():
        open_positions.append(p)
    equity = hb.get("equity") or portfolio.get("cash") or score_mod.START_EQUITY
    open_risk = sum(float(p.get("risk_dollars", 0.0)) for p in open_positions)
    current_exposure_pct = round(100.0 * open_risk / equity, 1) if equity else 0.0
    pending = [p for p in todays_plans if p.get("gate_verdict") in ("GO", "REVIEW")]
    verdict_counts = {}
    for p in todays_plans:
        v = p.get("gate_verdict", "?")
        verdict_counts[v] = verdict_counts.get(v, 0) + 1
    return {
        "heartbeat": hb, "heartbeat_age_seconds": health.heartbeat_age_seconds(),
        "stale": health.stale(), "halted": health.halted(),
        "regime": regime, "open_positions": open_positions,
        "todays_plans": todays_plans, "todays_plan_date": latest_date,
        "day_pnl_pct": hb.get("day_pnl_pct"), "equity": equity,
        "current_exposure_pct": current_exposure_pct, "pending_count": len(pending),
        # NİYET yüzeyi: sıradaki açılışta ateşlenecek silahlı planlar + hangileri Alpaca aynasına
        # zaten gönderildi — canlı-paper modda operatörün akşam sorusu "yarın ne yapacaksın?"dır.
        "armed_plans": portfolio.get("armed", []),
        "alpaca_submitted": portfolio.get("alpaca_submitted", []),
        "verdict_counts": verdict_counts,
        "mode": config.MODE, "autonomy_level": config.limits()["autonomy_level"],
        "broker": "Alpaca · paper" if _alpaca_present() else "Dahili broker · paper",
    }


def _alpaca_present() -> bool:
    """Alpaca kâğıt aynası kullanılabilir mi? YOKLAMA — herhangi bir arızada False.

    Başarısızlık bilginin kendisidir: "ayna var mı?" sorusunun cevabı zaten False olurdu."""
    try:
        from .adapters import alpaca
        return alpaca.paper_available()
    except Exception:  # sessiz-yutma: bu bir YOKLAMA — "ayna var mı?" sorusunun cevabı zaten False'tur; başarısızlık bilginin kendisidir
        return False


def calibration(hyps: list | None = None) -> dict:
    """Score how well Hermes' confidence tracks reality (Brier + reliability bins). A hypothesis is
    'closed' once its realized_delta has been written back. forecast p = confidence for an
    'improve' prediction (1-confidence for 'worsen'); outcome = 1 if realized_delta>0 else 0."""
    hyps = hyps if hyps is not None else memory.all_hypotheses()
    closed = [h for h in hyps if h.get("realized_delta") is not None and h.get("confidence") is not None]
    if not closed:
        return {"n": 0, "brier": None, "hit_rate": None, "reliability": [],
                "note": "henüz sonuçlanan (min_sample'a ulaşmış) tahmin yok"}
    pts = []
    for h in closed:
        outcome = 1.0 if h["realized_delta"] > 0 else 0.0
        conf = max(0.0, min(1.0, float(h["confidence"])))
        p = conf if h.get("predicted_direction", "improve_oos_score") == "improve_oos_score" else 1.0 - conf
        pts.append((p, outcome))
    brier = sum((p - o) ** 2 for p, o in pts) / len(pts)
    bins: dict = {}
    for p, o in pts:
        b = min(4, int(p * 5))
        bins.setdefault(b, []).append(o)
    reliability = [{"bin": f"%{b*20}-{b*20+20}", "n": len(v), "observed": round(sum(v) / len(v), 2)}
                   for b, v in sorted(bins.items())]
    return {"n": len(closed), "brier": round(brier, 4),
            "hit_rate": round(sum(o for _, o in pts) / len(pts), 3), "reliability": reliability}


# ---- MARUZİYET-DÜZELTİLMİŞ KIYAS --------------------------------------------
BENCH_BOOTSTRAP_N = 2000     # yeniden örnekleme sayısı — 2000, %95 aralığın uç noktalarını iki
                             # ondalıkta oturtan ilk taban (500'de aralık koşudan koşuya oynuyordu).
BENCH_BOOTSTRAP_SEED = 20260729   # SABİT TOHUM: aynı defter iki kez ölçüldüğünde AYNI aralığı
                             # vermeli. Rastgele tohum, hiçbir işlem değişmediği hâlde panoda her
                             # turda kıpırdayan bir güven aralığı üretirdi — okur bunu "yeni bilgi"
                             # sanardı. (Aynı gerekçe rollback idempotans testinde de yazılı.)


def _exposure_ratio(trades: list, start: str, end: str) -> tuple[float | None, dict]:
    """ORTALAMA YATIRIMDA-KALMA ORANI: sermayenin ne kadarı, ortalama olarak, piyasada durdu?

    Her takvim günü için o gün AÇIK olan işlemlerin giriş notional'ı (entry*qty) toplanır ve
    başlangıç sermayesine bölünür; oran bu günlük değerlerin [start, end] penceresi boyunca
    ortalamasıdır. Tek kaynak `trades.jsonl`in KENDİ alanlarıdır (`ts_open`, `ts_close`, `entry`,
    `qty` — canlı dosyadan doğrulandı); pozisyon defterinin gün-sonu enstantaneleri gerekmez.

    NEDEN NOTIONAL, NEDEN "GÜN AÇIK MIYDI" DEĞİL: "en az bir pozisyon açıktı" ikili sayımı, tek
    hisselik bir günü beş hisselik bir günle aynı sayar — oysa beta maruziyeti ikisinde beş kat
    farklıdır. Kıyasın amacı "SPY'ı ne kadar taşıdık"ı ölçmek olduğu için payda sermaye olmalıdır.

    Oran 1.0'ı AŞABİLİR (aynı anda sermayeden büyük toplam notional) ve bu KIRPILMAZ: kırpmak,
    kaldıraçlı bir günü kaldıraçsız gibi göstererek düzeltmeyi strateji lehine bozardı."""
    from datetime import date as _date, timedelta as _td
    from . import sieve
    if not trades or not start or not end:
        return None, {"neden": "işlem yok ya da pencere yok"}
    try:
        d_lo, d_hi = _date.fromisoformat(start[:10]), _date.fromisoformat(end[:10])
    except ValueError as e:
        return None, {"neden": f"pencere ayrıştırılamadı: {e}"}
    n_gun = (d_hi - d_lo).days + 1
    if n_gun < 1:
        return None, {"neden": "pencere boş"}
    start_eq = float(score_mod.START_EQUITY)
    if start_eq <= 0:
        return None, {"neden": "başlangıç sermayesi tanımsız"}
    gunluk = [0.0] * n_gun
    n_kullanilan = 0
    # persist=False: `benchmark_relative` /api/diagnostics'in HER anketinde çalışan bir OKUMA
    # modelidir; kalıcı bir Sieve onu her poll'da state/sieve.json'a yazan bir YAZICIYA çevirirdi
    # (modül başlığındaki "pure reads; no mutation" sözleşmesinin ihlali). Muhasebe yine tutulur ve
    # sayaçlar çıktının içinde panoya gider — YASA 4'ün istediği görünürlük kaybolmaz.
    with sieve.Sieve("benchmark.maruziyet", persist=False) as sv:
        for t in trades:
            o, c = str(t.get("ts_open") or "")[:10], str(t.get("ts_close") or "")[:10]
            if not o or not c:
                sv.drop("sema:eksik_alan:ts_open_veya_ts_close"); continue
            if t.get("entry") is None or t.get("qty") is None:
                sv.drop("sema:eksik_alan:entry_veya_qty"); continue
            try:
                notional = abs(float(t["entry"]) * float(t["qty"]))
                d0, d1 = _date.fromisoformat(o), _date.fromisoformat(c)
            except (TypeError, ValueError):  # sessiz-yutma: elenen satır GEREKÇESİYLE sayaca yazılıyor (sv.drop) ve sayaç çıktının `eleme` alanında panoya gidiyor — muhasebe görünür, kayıp sessiz değil
                sv.drop("sema:biçimsiz:tarih_veya_notional"); continue
            sv.keep()
            n_kullanilan += 1
            # Kapanış günü DAHİL: o gün pozisyon gün içinde taşınıyordu.
            d = max(d0, d_lo)
            son = min(d1, d_hi)
            while d <= son:
                gunluk[(d - d_lo).days] += notional
                d += _td(days=1)
    if not n_kullanilan:
        return None, {"neden": "maruziyet hesaplanabilir tek işlem yok", "eleme": sv.snapshot()}
    oran = (sum(gunluk) / n_gun) / start_eq
    return round(oran, 4), {"n_islem": n_kullanilan, "n_gun": n_gun,
                            "yatirimda_gun_orani": round(sum(1 for g in gunluk if g > 0) / n_gun, 4),
                            "start_equity": start_eq, "eleme": sv.snapshot()}


def benchmark_relative() -> dict | None:
    """#33 — honest alpha-vs-beta: the strategy's return vs simply holding SPY over the SAME window. A
    system that returns +3% while SPY did +40% is not finding edge, it is underperforming beta — the
    single most important thing a return number can hide. None below a handful of trades / no SPY data.

    MARUZİYET DÜZELTMESİ. HAM FARK NEDEN YANILTICI: `excess_return` stratejinin
    getirisinden SPY'ın TAM DÖNEM getirisini çıkarır — yani stratejiyi, parası sürekli piyasada duran
    bir SPY tutucusuyla kıyaslar. Oysa strateji sermayesinin yalnız bir kısmını, zamanın yalnız bir
    kısmında taşır. BOĞA piyasasında bu, stratejiye hak etmediği bir ceza yazar (SPY'ın tam maruziyetle
    ürettiği getiriyi, yarım maruziyetle üretilmiş bir getiriden çıkarırız); DÜŞÜŞTE ise tersi olur ve
    kenarsız bir strateji, sadece piyasada AZ durduğu için "SPY'ı yendi" diye görünür — kuzey
    yıldızının 2. ölçütü tam olarak böyle sahte yanabilir.
    Düzeltilmiş fark: `strateji_getirisi − (ortalama maruziyet × SPY getirisi)`; yani "aynı betayı
    pasif taşısaydık ne kazanırdık?"ın üstüne kalan artık.

    ESKİ ALAN KALDIRILMAZ: `excess_return`/`beat_benchmark` aynen kalır (geriye dönük uyum — pano,
    /api/performance ve mevcut testler onları okuyor). Yeni alanlar YANLARINA eklenir ve hüküm
    (edge_verdict 2. ölçüt) yeni alanı okur.

    GÜVEN ARALIĞI VE KAPSAMI: aralık, gerçekleşen işlem P&L'inin ÖRNEKLEM DEĞİŞKENLİĞİNİ yansıtır
    (işlemler yerine koymalı yeniden örneklenir, sabit tohum). SPY getirisi ve maruziyet oranı
    bootstrap'ta SABİT tutulur — onlar bu defterin tek bir gerçekleşmiş yolundan ölçülmüştür, yeniden
    örneklenecek bir dağılımları yoktur. Aralık bu yüzden "toplam belirsizlik" DEĞİL, yalnız işlem
    kuyruğundan gelen belirsizliktir; alan adı (`ci_kapsam`) bunu çıktının içinde söyler."""
    trades = _trades()
    if len(trades) < 5:
        return None
    curve = score_mod.equity_curve(trades)
    strat_ret = curve[-1] / curve[0] - 1.0 if curve[0] else 0.0
    opens = sorted(str(t.get("ts_open", ""))[:10] for t in trades if t.get("ts_open"))
    closes = sorted(str(t.get("ts_close", ""))[:10] for t in trades if t.get("ts_close"))
    if not opens or not closes:
        return None
    start, end = opens[0], closes[-1]
    try:
        from .adapters import data
        spy = data.load_bars(data.INDEX_SYMBOL, start, end, use_cache=True)
        if spy is None or spy.empty:
            return None
        spy_ret = float(spy["close"].iloc[-1] / spy["close"].iloc[0] - 1.0)
    except Exception as e:
        # None dönmek panoda "kıyas yok" gösterir; ama SEBEBİ görünmezse endeks verisi bozulduğunda
        # strateji sonsuza kadar kıyassız kalır ve kimse aramaz.
        from . import obs
        obs.warn("benchmark_unavailable", error=f"{type(e).__name__}: {e}",
                 detail="SPY kıyası hesaplanamadı — göreli performans gösterilemiyor")
        return None
    excess = strat_ret - spy_ret
    out = {"start": start, "end": end, "benchmark": data.INDEX_SYMBOL,
           "strategy_return": round(strat_ret, 4), "benchmark_return": round(spy_ret, 4),
           # bool(): excess derives from the numpy/pandas layer — a raw comparison would be a numpy.bool_,
           # which is NOT JSON-serializable and 500s any endpoint carrying it (see reflect._gate_eval).
           "excess_return": round(excess, 4), "beat_benchmark": bool(excess > 0)}

    # ---- MARUZİYET DÜZELTMESİ + BOOTSTRAP ARALIĞI ----------------------------------------
    maruziyet, mdetay = _exposure_ratio(trades, start, end)
    out["maruziyet"] = {"oran": maruziyet, "yontem":
                        "ortalama günlük (Σ açık pozisyon notional) / başlangıç sermayesi", **mdetay}
    if maruziyet is None:
        # ÖLÇÜLEMEDİ → DÜZELTİLMİŞ FARK DA ÖLÇÜLEMEDİ. Ham farkı "düzeltilmiş" adıyla ikinci kez
        # yayınlamak, düzeltme yapılmadığı hâlde yapılmış gibi okunurdu (UYDURMA YASAĞI).
        out["exposure_adjusted_excess"] = None
        out["exposure_adjusted_beat"] = None
        out["ci"] = None
        out["anlamli"] = None
        out["ci_kapsam"] = "maruziyet ölçülemedi — düzeltilmiş fark üretilmedi"
        return out

    adj = strat_ret - maruziyet * spy_ret
    import numpy as np
    rng = np.random.default_rng(BENCH_BOOTSTRAP_SEED)
    pnl = np.array([float(t.get("pnl_dollars") or 0.0) for t in trades], dtype=float)
    start_eq = float(score_mod.START_EQUITY)
    # YENİDEN ÖRNEKLEME İŞLEM DÜZEYİNDE: her tur n işlem yerine koymalı çekilir ve strateji getirisi
    # o kuyruktan yeniden hesaplanır. Getiri tanımı NOKTA TAHMİNİYLE AYNI olmalı — `equity_curve`
    # pnl'leri sermayeye ekleyip oranlıyor, yani toplam getiri = Σpnl / başlangıç sermayesi; aynı
    # formül burada da kullanılır, yoksa aralık başka bir büyüklüğün etrafında kurulurdu.
    #
    # BLOK BOOTSTRAP'A GEÇTİ. Buradaki aralık ÖNCEDEN BİLİNÇLİ olarak IID
    # bırakılmıştı ("2. ölçütün hükmü habersiz kaymasın" gerekçesiyle). Blok bootstrap kalemi tam olarak
    # o bilinçli istisnayı kapatmaktır: kayıp SERİLERİ bu büyüklükte de vardır, IID onları kırar ve
    # aralığı sistematik DARALTIR — yani ölçülmemiş bir kesinlik yazar.
    # HÜKÜM KAYMASI AÇIKÇA BEYAN EDİLİR (habersiz kayma yasak): aralık GENİŞLEDİĞİ için `anlamli`
    # False'a dönebilir ve `edge_verdict`in 2. ölçütü SAGLANDI → ZAYIF'a inebilir. İki alan bu yüzden
    # yanında taşınır: `ci_iid_karsilastirma` (eski yöntemin aynı defterdeki aralığı) ve
    # `hukum_kaymasi` (iki yöntemin anlamlılık hükmü ayrışıyor mu). Eski aralık SİLİNMEZ —
    # karşılaştırma, kaymanın kanıtıdır.
    def _bench_dagilim(blok: int) -> np.ndarray:
        """Maruziyet-düzeltilmiş fazla getirinin CIRCULAR BLOK bootstrap dağılımı.

        `blok` işlem uzunluğunda bloklar çekilir (blok=1 ⇔ eski IID yöntem); tohum SABİTtir, yani
        aynı defter aynı aralığı verir. Dönen dizi B adet yeniden örneklenmiş fazla getiridir."""
        n = pnl.size
        b = max(1, min(int(blok), n))
        n_blok = -(-n // b)
        r = np.random.default_rng(BENCH_BOOTSTRAP_SEED)
        bas = (r.random((BENCH_BOOTSTRAP_N, n_blok)) * n).astype(np.int64)
        idx = (bas[:, :, None] + np.arange(b)[None, None, :]) % n     # circular blok
        top = pnl[idx].reshape(BENCH_BOOTSTRAP_N, n_blok * b)[:, :n].sum(axis=1)
        return top / start_eq - maruziyet * spy_ret

    dagilim = _bench_dagilim(BOOT_BLOCK_TRADES)
    lo, hi = np.percentile(dagilim, [2.5, 97.5])
    d_iid = _bench_dagilim(1)                                          # blok=1 ⇔ IID (eski yöntem)
    lo_i, hi_i = np.percentile(d_iid, [2.5, 97.5])
    out["exposure_adjusted_excess"] = round(float(adj), 4)
    out["exposure_adjusted_beat"] = bool(adj > 0)
    out["ci"] = {"lo": round(float(lo), 4), "hi": round(float(hi), 4), "seviye": 0.95,
                 "yontem": (f"circular blok bootstrap (blok={BOOT_BLOCK_TRADES} işlem, "
                            f"B={BENCH_BOOTSTRAP_N}, tohum sabit)"),
                 "n": len(pnl)}
    out["ci_iid_karsilastirma"] = {
        "lo": round(float(lo_i), 4), "hi": round(float(hi_i), 4),
        "anlamli": bool(lo_i > 0 or hi_i < 0),
        "yontem": "ESKİ yöntem (IID işlem-düzeyi bootstrap) — yalnız karşılaştırma için tutulur"}
    out["hukum_kaymasi"] = bool((lo > 0 or hi < 0) != (lo_i > 0 or hi_i < 0))
    # ANLAMLILIK = ARALIK SIFIRI DIŞARIDA BIRAKIYOR MU. Tek bir eşik karşılaştırması ("adj > 0")
    # 95 işlemlik bir defterde yazı-turadan ayırt edilemez bir farkı da "geçti" sayardı; edge_verdict
    # bu alanı okuyup ZAYIF durumunu üretir.
    out["anlamli"] = bool(lo > 0 or hi < 0)
    out["ci_kapsam"] = ("yalnız işlem P&L'inin örneklem değişkenliği; SPY getirisi ve maruziyet "
                        "oranı sabit tutuldu (tek gerçekleşmiş yoldan ölçüldüler)")
    return out


# ---- İŞLEM-PENCERESİ ATRİBÜSYONU: ALFA vs BETA -----------------------------
# NEDEN AYRI BİR ÖLÇÜM (ve neden `benchmark_relative` yetmiyor): `benchmark_relative` PORTFÖY
# düzeyinde konuşur — tüm dönemin getirisini, ortalama maruziyetle ölçeklenmiş SPY'a karşı koyar.
# O rakam "sermayem SPY'a karşı ne yaptı?"yı cevaplar. Ama denetimin sorduğu soru başkaydı:
# "kurallar, TUTTUKLARI PENCERELERDE piyasadan fazlasını üretiyor mu?" — yani her işlemin KENDİ
# penceresinde SPY ne yaptı? İkisi aynı defterde ciddi biçimde ayrışır: strateji piyasada yalnız
# bazı pencerelerde durur ve o pencereleri SEÇER; portföy düzeyi ölçüm bu seçimin iyi mi kötü mü
# olduğunu gizler.
#
# 2026-07-30 gecesi bu ölçüm ELLE yapıldı: defter −%0,225 vs SPY +%0,411 →
# işlem başına kaba alfa −%0,64; kazanan işlemler SPY'ın +%1,89 koştuğu pencerelerdeydi (yani
# kazançların karakteri TIMING değil BETA). Bu fonksiyon o elle ölçümün KALICI hâlidir — aynı
# tanım, aynı sayı, artık bir uçtan servis ediliyor.
#
# PENCERE TANIMI (ve neden bu): SPY KAPANIŞ(ts_open) → KAPANIŞ(ts_close). Kapanış-kapanış seçildi
# çünkü (a) elle ölçümün rakamlarını birebir üretir, (b) açılış-kapanış karışımı işlemin kendi
# bacaklarına daha yakın görünse de günlük barda giriş açılışı ile çıkışın gün-içi anı arasındaki
# asimetriyi ölçülmemiş bir kesinlikle kapatırdı. Tanım çıktının içinde `yontem` alanıyla beyan
# edilir — okur hangi kıyası gördüğünü tahmin etmek zorunda kalmaz.
#
# SPY BARLARI KAPIDAN GEÇER: `data.load_bars` okuma yolunda `sanitize_bars` çalıştırır (hayalet
# seans + düzeltilmemiş fiyat kapısı). Ham CSV okumak, kapının elediği kirli barları bu
# ölçüme taşımak olurdu.
# "0g" GERÇEK BİR DİLİMDİR, ÖLÇÜM BOŞLUĞU DEĞİL: aynı seans içinde açılıp kapanan işlem (canlı
# defterde var — T00070/TDG 2025-05-06) `bars_held=0` taşır. İlk sürümde alt sınır 1'di ve o satır
# "olculemedi" kovasına düşüyordu; yani ÖLÇÜLMÜŞ bir tutuşu ölçülmemiş gibi göstermek olurdu.
# "olculemedi" yalnız `bars_held` YOK ya da biçimsiz olduğunda kullanılır.
ALFA_TUTUS_DILIMLERI = ((0, 0, "0g"), (1, 1, "1g"), (2, 3, "2-3g"), (4, 7, "4-7g"),
                        (8, 15, "8-15g"), (16, None, "16g+"))
ALFA_HUCRE_MIN_N = 5      # altındaki hücre `yeterli: False` taşır — değeri GİZLENMEZ, etiketlenir


def _tutus_dilimi(bars_held) -> str:
    """`bars_held` → tutuş dilimi etiketi. Ölçülemeyen (None/biçimsiz) satır kendi kovasında kalır;
    "1g" gibi bir dilime düşürmek, ölçülmemiş bir tutuşu ölçülmüş gibi gösterirdi."""
    try:
        b = int(bars_held)
    except (TypeError, ValueError):  # sessiz-yutma: kova ADIYLA dışarı çıkıyor ("olculemedi") ve kırılım tablosunda ayrı satır olarak görünür — kayıp sessiz değil
        return "olculemedi"
    for lo, hi, ad in ALFA_TUTUS_DILIMLERI:
        if b >= lo and (hi is None or b <= hi):
            return ad
    return "olculemedi"


def _alfa_ozet(kayitlar: list[dict]) -> dict:
    """Bir hücrenin özeti. Boş hücrede sayılar None'dır (0.0 DEĞİL — ölçülmedi ile sıfır aynı şey
    değildir); `n` her zaman gerçektir."""
    n = len(kayitlar)
    if not n:
        return {"n": 0, "ort_fark": None, "ort_spy": None, "ort_islem": None,
                "kazanan_orani": None, "yeterli": False}
    fark = sum(k["fark"] for k in kayitlar) / n
    spy = sum(k["spy"] for k in kayitlar) / n
    isl = sum(k["islem"] for k in kayitlar) / n
    return {"n": n, "ort_fark": round(fark, 5), "ort_spy": round(spy, 5),
            "ort_islem": round(isl, 5),
            "kazanan_orani": round(sum(1 for k in kayitlar if k["islem"] > 0) / n, 3),
            "yeterli": bool(n >= ALFA_HUCRE_MIN_N)}


def _alfa_grupla(kayitlar: list[dict], anahtar) -> dict:
    """Alfa kayıtlarını `anahtar(kayit)` fonksiyonuna göre gruplar ve her grubun `_alfa_ozet`ini döner.

    Gruplar anahtarın metin hâline göre SIRALI çıkar (rapor çıktısı kararlı olsun)."""
    by = defaultdict(list)
    for k in kayitlar:
        by[anahtar(k)].append(k)
    return {str(g): _alfa_ozet(v) for g, v in sorted(by.items(), key=lambda x: str(x[0]))}


def trade_alpha_beta() -> dict:
    """BETA-DÜZELTİLMİŞ ATRİBÜSYON: her kapanan işlemin KENDİ penceresinde SPY'a karşı farkı.

    Saf okuma (trades.jsonl + SPY barları). Hiçbir dosyaya yazmaz, hiçbir karara girmez —
    `result_verdict`in dört ölçütüne DE girmez (bkz. oradaki `beta_duzeltilmis` bloğu).

    ÖLÇÜLEMEYEN ÖLÇÜLMÜŞ GİBİ GÖSTERİLMEZ: SPY barı bulunamayan ya da tarihi defterin barlarında
    olmayan işlem `n_olculemeyen`e yazılır ve HİÇBİR ortalamaya girmez; hiçbir SPY penceresi
    ölçülemezse fonksiyon `ort_fark: None` ile döner (tüm kırılımlar boş).

    KAYNAK DAMGASI KIRILIMI: aynı ölçüm `live_paper`/`replay_seed`/`belirsiz`
    paydalarında AYRI verilir. Tohum satırlarının alfası "kuralların karakteri"dir, canlı
    performans DEĞİL — ikisini tek ortalamada toplamak, denetimin şikâyet ettiği karışımın
    ta kendisi olurdu."""
    from . import ledgerstamp
    trades = _trades()
    out: dict = {
        "n": len(trades), "n_olculebilir": 0, "n_olculemeyen": 0,
        "yontem": ("işlem getirisi = pnl_pct (friksiyon dolum fiyatının içinde); kıyas = SPY "
                   "kapanış(ts_open) → kapanış(ts_close), AYNI pencere; fark = işlem − SPY"),
        "kaynak_notu": ("SPY barları `adapters.data.load_bars` üzerinden okunur — hayalet seans + "
                        "düzeltilmemiş fiyat kapısından (sanitize_bars) geçmiş hâl (BT-2)"),
        "pencere": None, "ort_islem": None, "ort_spy": None, "ort_fark": None,
        "kazanan_n": None, "kazananlarin_spy_ortalamasi": None,
        "kaybeden_n": None, "kaybedenlerin_spy_ortalamasi": None,
        "kirilim": {"aile": {}, "rejim": {}, "tutus_dilimi": {}, "hucreler": []},
        "kaynak_kirilim": {}, "hucre_min_n": ALFA_HUCRE_MIN_N, "neden_bos": None,
    }
    if not trades:
        out["neden_bos"] = "defter boş"
        return out
    opens = sorted(str(t.get("ts_open", ""))[:10] for t in trades if t.get("ts_open"))
    closes = sorted(str(t.get("ts_close", ""))[:10] for t in trades if t.get("ts_close"))
    if not opens or not closes:
        out["neden_bos"] = "işlem penceresi okunamadı (ts_open/ts_close yok)"
        return out
    start, end = opens[0], closes[-1]
    out["pencere"] = {"start": start, "end": end}
    try:
        from .adapters import data
        spy = data.load_bars(data.INDEX_SYMBOL, start, end, use_cache=True)
        if spy is None or spy.empty:
            out["neden_bos"] = f"{data.INDEX_SYMBOL} barı yok — pencere kıyası yapılamadı"
            return out
        kapanis = {str(d)[:10]: float(c) for d, c in zip(spy["date"], spy["close"])}
        out["benchmark"] = data.INDEX_SYMBOL
    except Exception as e:
        # None/boş dönmek panoda "kıyas yok" gösterir; SEBEBİ görünmezse endeks verisi bozulduğunda
        # atribüsyon sonsuza dek sessizce boş kalır ve kimse aramaz (benchmark_relative ile aynı ders).
        from . import obs
        obs.warn("alpha_beta_unavailable", error=f"{type(e).__name__}: {e}",
                 detail="işlem-penceresi SPY kıyası hesaplanamadı — alfa/beta kolonu boş kalacak")
        out["neden_bos"] = f"SPY barı okunamadı: {type(e).__name__}"
        return out

    kayitlar: list[dict] = []
    for t in trades:
        o, c = str(t.get("ts_open") or "")[:10], str(t.get("ts_close") or "")[:10]
        p0, p1 = kapanis.get(o), kapanis.get(c)
        r = t.get("pnl_pct")
        if p0 is None or p1 is None or not p0 or r is None:
            out["n_olculemeyen"] += 1
            continue
        try:
            islem = float(r)
        except (TypeError, ValueError):  # sessiz-yutma: biçimsiz satır `n_olculemeyen` SAYACINA yazılıyor ve o sayaç çıktının içinde panoya gidiyor — payda görünür kalır
            out["n_olculemeyen"] += 1
            continue
        spy_ret = p1 / p0 - 1.0
        kayitlar.append({"islem": islem, "spy": spy_ret, "fark": islem - spy_ret,
                         "aile": t.get("setup") or "?", "rejim": t.get("regime") or "?",
                         "dilim": _tutus_dilimi(t.get("bars_held")),
                         "kaynak": ledgerstamp.kaynak_of(t)})
    out["n_olculebilir"] = len(kayitlar)
    if not kayitlar:
        out["neden_bos"] = "hiçbir işlemin SPY penceresi ölçülemedi"
        return out

    toplam = _alfa_ozet(kayitlar)
    out["ort_islem"], out["ort_spy"] = toplam["ort_islem"], toplam["ort_spy"]
    out["ort_fark"] = toplam["ort_fark"]
    kazananlar = [k for k in kayitlar if k["islem"] > 0]
    kaybedenler = [k for k in kayitlar if k["islem"] <= 0]
    out["kazanan_n"] = len(kazananlar)
    out["kaybeden_n"] = len(kaybedenler)
    # KAZANANLARIN SPY PENCERESİ — DENETİMİN ASIL BULGUSU. Kazanan işlemler SPY'ın da koştuğu
    # pencerelerdeyse "kazandık" cümlesi seçim değil beta anlatır; bu tek sayı o ayrımı taşır.
    out["kazananlarin_spy_ortalamasi"] = (round(sum(k["spy"] for k in kazananlar) / len(kazananlar), 5)
                                          if kazananlar else None)
    out["kaybedenlerin_spy_ortalamasi"] = (round(sum(k["spy"] for k in kaybedenler) / len(kaybedenler), 5)
                                           if kaybedenler else None)
    out["kirilim"]["aile"] = _alfa_grupla(kayitlar, lambda k: k["aile"])
    out["kirilim"]["rejim"] = _alfa_grupla(kayitlar, lambda k: k["rejim"])
    out["kirilim"]["tutus_dilimi"] = _alfa_grupla(kayitlar, lambda k: k["dilim"])
    # TAM ÇAPRAZ HÜCRELER: aile × rejim × tutuş-dilimi. Kenar dağılımları (yukarıda) "hangi eksende
    # sorun var?" der; çapraz hücreler "hangi KOMBİNASYONDA?" der ve ikisi farklı sorulardır —
    # n=95'lik bir defterde çoğu hücre seyrek olacaktır, o yüzden her hücre `n` + `yeterli` taşır.
    capraz = defaultdict(list)
    for k in kayitlar:
        capraz[(k["aile"], k["rejim"], k["dilim"])].append(k)
    out["kirilim"]["hucreler"] = [
        {"aile": a, "rejim": r, "tutus_dilimi": d, **_alfa_ozet(v)}
        for (a, r, d), v in sorted(capraz.items())]
    out["kaynak_kirilim"] = _alfa_grupla(kayitlar, lambda k: k["kaynak"])
    return out


# SHIP DURUMLARI — TEK KAYNAK (v304, 2026-08-25). Bu küme İKİ yerde ayrı ayrı yazılıydı ve
# AYRIŞMIŞTI: `learning_scorecard` `superseded`i saymıyordu, `deflate_why` sayıyordu. Operatöre
# yanlış sayan servis ediliyordu ve karne "hiçbir öneri OOS kapısını geçemedi" diyordu — oysa
# defterde İKİ ship vardı (H00026 v1→v2, H00029 v2→v3) ve İKİ DÜĞME DE CANLIDA (v5, parent 3).
#
# `superseded` NEDEN SHIP'TİR: `rollback.sweep_orphan_hypotheses` YALNIZ `status == "live"` olanı
# bu duruma taşır (`rollback.py::sweep_orphan_hypotheses`) ve bir hipotez ancak SHIP ETTİYSE `live`
# olur (çapa sembole çevrildi 2026-09-03, TSK-030 adım-3; hedef okundu: gövde `status != "live"`
# olanı atlar ve kalanı `superseded`e taşır — çapanın anlattığı şey oradadır). Yani
# sonradan eklenen bir HİJYEN mekanizması, daha eski bir sayacın varsayımını geçersiz kılmış ve
# öğrenmenin kanıtını karneden sessizce silmişti. Arıza biçimi makul bir cümle olduğu için
# ("sistem hiç öğrenmedi") kimse fark etmedi. Çivi v304 süpürmenin HEDEF durumunu kaynaktan
# okuyup bu kümede arar — hedef değişirse öter.
SHIP_DURUMLARI = ("live", "promoted", "superseded", "rolled_back")


def learning_scorecard(goal: dict | None = None) -> dict:
    """An HONEST answer to 'is the agent actually learning?' — not vanity metrics. Reports how far the
    reflection→outcome loop has actually closed: how many hypotheses shipped, how many were measured
    against reality (realized_delta written), how well its predictions calibrate, and a plain verdict.
    Before the outcome loop was wired this would have read all-zeros forever — which was the honest truth."""
    from collections import Counter
    hyps = memory.all_hypotheses()
    sc = Counter(h.get("status") for h in hyps)
    outcomes = [h for h in hyps if h.get("realized_delta") is not None]
    cal = calibration(hyps)
    sb = store.read_json("scoreboard.json", {"versions": {}})
    shipped = sc.get("live", 0) + sc.get("promoted", 0)
    n_cal = cal.get("n", 0)
    # HONEST loop_state — name the REAL blocker instead of the misleading "yeterli işlem yok" (there may be
    # hundreds of trades; the loop is stuck because nothing ever SHIPPED, so the live version never gained a
    # parent and evaluate_outcomes has nothing to measure). ever_shipped counts every version that reached
    # live (incl. ones later rolled back) — a shipped-then-rolled-back change still closed the loop once.
    ever_shipped = sum(sc.get(s, 0) for s in SHIP_DURUMLARI)
    trades = store.read_jsonl("trades.jsonl")
    trades_total = len(trades)
    # ---- DEFTERİN KAYNAK AYRIŞTIRMASI ---------------------------------------
    # BU KARNENİN EN BÜYÜK YALANI BURADAYDI: `trades_total` 95 diyordu ve altındaki her cümle o 95'i
    # "canlı defter" sayıyordu — oysa gövdesi replay tohumuydu (tek toplu yazım, bugünkü evrenle,
    # survivorship'li). Yani "v4 yayında, 95/30 işlem birikti" cümlesi ölçülmemiş bir olgunluk
    # iddia ediyordu. Sayaçlar artık damgadan okunuyor ve GERÇEK CANLI n ayrı durur.
    from . import ledgerstamp as _ls
    defter = _ls.counts(trades)
    # ÖRNEKLEM = TOHUM OLMAYAN SATIRLAR. Damgasız/belirsiz satır tohum SAYILMAZ (kanıtımız yok;
    # "belirsiz"i tohuma yazmak da uydurma olurdu) ama `gercek_canli_n` yalnız KANITLI canlı
    # satırları sayar. İki sayı bilerek ayrı: biri kapının paydası, öteki kanıtın kendisi.
    defter["gercek_canli_n"] = defter["live_paper_n"]
    defter["orneklem_n"] = defter["live_paper_n"] + defter["belirsiz_n"]
    defter["orneklem_kapsam"] = ("min_sample paydası = live_paper + belirsiz (damgasızlar dahil); "
                                 "replay_seed satırları TRAINING sayılır ve paydaya girmez")
    defter["sinir"] = _ls.seed_boundary()
    min_s = int((goal or config.goal())["min_sample"])
    if not hyps:
        verdict, loop_state = "henüz hiç hipotez yok — reflect hiç çalışmamış", "no_hypotheses"
    elif ever_shipped == 0:
        # SÜRÜM ÖLÇÜLÜR, UYDURULMAZ: eski cümle "hâlâ v1 (parent yok)" diye SABİT bir literal
        # basıyordu ve canlı v5/parent 3 taşırken bile aynen çıkıyordu. Ölçülemezse hiç söylenmez.
        try:
            _v = int(config.load_strategy().get("version", 0)) or None
        except Exception:  # sessiz-yutma: sürüm okunamazsa cümle SÜRÜMDEN HİÇ BAHSETMEZ; uydurma bir "v1" basmak, tam da düzeltilen kusurun kendisi olurdu
            _v = None
        _sur = f"canlı strateji v{_v}" if _v else "canlı strateji sürümü ölçülemedi"
        verdict = (f"hiçbir öneri OOS kapısını geçemedi — {_sur}, değerlendirilecek bir evrim yok. "
                   f"{sc.get('rejected_by_backtest', 0)} backtest, "
                   f"{sc.get('rejected_by_guard', 0)} guard reddi. Öğrenme antrenmanı başlatabilirsin.")
        loop_state = "no_ship_v1_stands"
    elif not outcomes:
        cur_v = sb.get("current_version")
        # TOHUM SATIRI OLGUNLUK SAYMAZ: eskiden payda `strategy_version == cur_v` olan HER
        # satırdı ve tohum koşusu defterin tamamını cur_v ile damgaladığı için sayaç bir gecede
        # dolu görünüyordu. Payda artık tohum-olmayan satırlardır; tohumun kendisi cümlede
        # "training" olarak AYRICA söylenir — gizlenmez, ama olgunluk diye sayılmaz.
        n_cur = sum(1 for t in trades
                    if t.get("strategy_version") == cur_v
                    and _ls.kaynak_of(t) != _ls.REPLAY_SEED)
        n_seed = defter["replay_seed_n"]
        verdict = (f"v{cur_v} yayında — {n_cur}/{min_s} kapanmış işlem birikti; min örneğe ulaşınca "
                   f"sonuç yazılacak ve döngü kapanacak")
        if n_seed:
            verdict += (f" (ayrıca {n_seed} tohum/training satırı defterde duruyor — "
                        f"replay_seed damgalı, canlı kanıt sayılmaz)")
        loop_state = "shipped_awaiting_min_sample"
    elif n_cal < 3:
        verdict, loop_state = "döngü kapanıyor — birkaç sonuç daha gerekiyor", "closing"
    elif cal.get("hit_rate", 0) >= 0.5:
        verdict, loop_state = "döngü kapalı ve kalibre ölçülüyor — gerçekten öğreniyor", "closed_learning"
    else:
        verdict, loop_state = "öğreniyor ama tahminleri zayıf kalibre (hit-rate düşük)", "closed_weak_cal"
    return {"status_counts": dict(sc), "shipped": shipped, "promoted": sc.get("promoted", 0),
            "rolled_back": sc.get("rolled_back", 0), "rejected_by_backtest": sc.get("rejected_by_backtest", 0),
            "rejected_by_guard": sc.get("rejected_by_guard", 0),
            "outcomes_measured": len(outcomes), "trades_total": trades_total, "loop_state": loop_state,
            # DEFTERİN KAYNAK SAYAÇLARI — panonun ve /api/today'in okuduğu alan.
            # `trades_total` geriye dönük uyum için AYNEN kalır (ham satır sayısı); karar verecek
            # olan `defter.gercek_canli_n`dir.
            "defter": defter,
            "calibration": {"n": n_cal, "brier": cal.get("brier"), "hit_rate": cal.get("hit_rate")},
            "overfit_suspects": sum(1 for h in hyps if h.get("overfit_suspect")),
            "versions": len(sb.get("versions", {})), "current_version": sb.get("current_version"),
            "min_sample": min_s,   # UI binds captions to THIS, never a hardcoded 30 (dashboard audit)
            "regime_budget_triggers": __import__("meridian.regime_trigger", fromlist=["DeferredRegimeBudgetTrigger"]).DeferredRegimeBudgetTrigger().evaluate(trades),
            # BESLEME KANALLARI KARNEYE GİRER. Yukarıdaki sayılar (0 ship / 0 terfi /
            # 1 ölçülmüş sonuç) DÜRÜSTTÜR ve bu tur onları UYDURMADI — ama "neden 0?" sorusunun
            # cevabı bu karnede hiç yoktu. İki besleme kanalı burada görünür:
            #   `antrenman` — gölge model taze mi, terfi kaç çift uzakta (ölçüm: n_live=0/30 ve
            #                 bu DÜRÜST: p_win_shadow damgası 2026-07-21'de başladı, damgalı 23
            #                 planın hiçbiri henüz kapanmadı);
            #   `dolgu_kuyrugu` — LLM görüş↔sonuç kalibrasyonunu besleyen kuyruk (ölçüm: 93 gün /
            #                 95 satır dolgulanabilir, 386 plan görüşsüz).
            # İkisi de ÖLÇÜM taşır, hüküm değil: ship sayısını değiştirmezler, "0"ın nedenini
            # okunur yaparlar.
            "besleme": _learning_feeds(),
            # TSK-074 (2026-09-04, r1 revizyonu): "süzülen hayalet öneri" sayacı — Ö-48 süzgecinin
            # öneri katmanında GERÇEKTEN bir şey yaptığının canlı kanıtı (operatör kapı kararı: 2
            # hafta sonra bu sayı okunur, sıfırsa kablolama geri alınır). KÜMÜLATİF (kabloladığı
            # günden BUGÜNE), kayan pencere DEĞİL — geç bakılsa da doğru cevap kalsın diye.
            # Ölçülemeyen 0 DEĞİL, hiç olay yoksa da 0 döner (uydurma değil): events.jsonl her
            # zaman okunabilir, boş küme geçerli veri.
            "hayalet_suzulen_n": _hayalet_suzulen_n(),
            "verdict": verdict}


# TSK-074 r1 (2026-09-04, Rol-1 review): sayaç KAYAN pencere DEĞİL, KABLOLAMA TARİHİNDEN beri
# BİRİKİMLİDİR — operatörün "2 hafta sonra sıfırsa geri al" sorusu geç sorulsa da bu doğru cevabı
# verir (kayan 14g pencere, geç okunursa erken günleri sessizce unuturdu).
HAYALET_SUZGEC_KABLOLAMA_TARIHI = "2026-09-04"

# KUYRUK-SINIRLI OKUMA TAVANI (r1). ÖLÇÜLDÜ (store.py::read_jsonl): `limit=N` yalnız DÖNEN LİSTEYİ
# (`rows[-limit:]`) ve dolayısıyla bu fonksiyonun kendi döngüsünü sınırlar — dosyanın TAMAMI yine
# okunup satır satır ayrıştırılır (G/Ç ve JSON-parse maliyeti `limit`ten BAĞIMSIZ, ~dosya boyu).
# Yani bu sabit `learning_scorecard` çağrısının (canlıda ~30 sn'de bir) KENDİ döngüsündeki
# `adlar.update(...)` iş yükünü ve dönen liste boyutunu sınırlar; `store.read_jsonl`ın kendi G/Ç
# maliyetini DEĞİL — bu, r1'in "limit=… ölç" isteğinin ölçülmüş, dürüst sonucudur.
#
# N ÖLÇÜMÜ (2026-09-04, yerel `state/events.jsonl`): 27.888 satır, ts aralığı 2026-07-14→2026-09-03
# (52 takvim günü) → günlük ortalama 27888/52 ≈ 536/gün (ham; gün-içi dağılım çok düzensiz, min
# 1/gün — maks 7256/gün tek bir yoğun günde — bu yüzden ORTALAMA, medyan değil, seçildi: tek bir
# ölçüm düşük-trafik günlerini yanlış temsil etmesin). N = 14 gün × 536 × 2 güvenlik payı ≈ 15.036
# → 15.000'e yuvarlandı.
#
# BİLİNEN SINIR (bedel yasası — gizlenmedi): sayaç KÜMÜLATİF (kablolama gününden BUGÜNE) ama okuma
# KUYRUK-SINIRLIDIR — kablolama gününden bugüne toplam (yalnız hayalet değil, HER TÜRDEN) olay
# `HAYALET_SAYAC_N_SATIR`ı aşarsa en eski hayalet olayı kuyruktan sessizce düşer ve sayaç ONU bir
# daha SAYMAZ. Bu sınır operatörün 2 haftalık karar penceresini (2026-09-04 → ~2026-09-18) 2×
# payla GÜVENLE kapsar; sayaç o pencereden SONRA da kalıcı bir gösterge olarak TUTULACAKSA bu sabit
# YENİDEN ÖLÇÜLMELİ ya da okuma stratejisi (tarih-bölümlü/indeksli) değişmelidir — sessizce
# doğruluğunu kaybetmeye bırakılmamalı.
HAYALET_SAYAC_N_SATIR = 15000


def _hayalet_suzulen_n(baslangic: str = HAYALET_SUZGEC_KABLOLAMA_TARIHI) -> int:
    """KÜMÜLATİF "süzülen hayalet öneri" SAYACI (TSK-074 r1, 2026-09-04 — Rol-1 review: kayan 14
    gün DEĞİL, `baslangic`tan — varsayılan kablolama günü — BUGÜNE birikimli). `hermes.virgin_
    knobs()` içindeki Ö-48 tek boğazının (`reflect.hayalet_suzgeci(..., kaynak="hermes.virgin_
    knobs")`) yazdığı `reflect_hayalet_dugme_suzuldu` olaylarını `state/events.jsonl`dan okur —
    İKİNCİ bir yazım kanalı AÇILMADI (tek-kaynak yasası): süzgeç zaten kendi olayını basıyor, bu
    fonksiyon yalnız OKUYUCUDUR (YASA 6).

    SAYILAN ŞEY OLAY DEĞİL, ADIN KENDİSİ: `virgin_knobs()` her reflect turunda yeniden çağrılır,
    yani kalıcı tek bir hayalet düğme günler boyunca AYNI adla tekrar tekrar süzülür — olay
    SAYISINI toplamak, tek düğmeyi çok düğmeymiş gibi şişirirdi. Bunun yerine `baslangic`tan
    BUGÜNE olaylardan GERÇEKTEN süzülen FARKLI anahtar adlarının KÜMESİ sayılır (uydurma yasağı:
    sayaç yalnız gerçekten süzülen adları sayar, tekrarları değil).

    OKUMA KUYRUK-SINIRLIDIR (`HAYALET_SAYAC_N_SATIR`, yukarıda ölçümlü) — bilinen sınır orada
    beyanlı: kablolama gününden bugüne o tavanı aşan toplam olay birikirse en eski hayalet olayı
    kuyruktan sessizce düşer."""
    import datetime as _dt
    sinir = _dt.datetime.fromisoformat(baslangic).replace(tzinfo=_dt.timezone.utc)
    adlar: set = set()
    for e in store.read_jsonl("events.jsonl", limit=HAYALET_SAYAC_N_SATIR):
        if not isinstance(e, dict):
            continue   # dict olmayan/bozuk satır — store.read_jsonl kendi jsonl_rows_skipped uyarısını zaten basıyor, burada yalnız TİP süzülüyor
        if e.get("event") != "reflect_hayalet_dugme_suzuldu" or e.get("kaynak") != "hermes.virgin_knobs":
            continue
        ts = e.get("ts")
        try:
            zaman = _dt.datetime.fromisoformat(ts) if ts else None
        except (ValueError, TypeError):
            # sessiz-yutma: bozuk/eski biçim TEK satırı düşürür, sayacı değil — events.jsonl elle
            # düzenlenmiş ya da eski şema satırı taşıyabilir; sayaç KÖRLEŞMEZ, o satır atlanır
            zaman = None
        if zaman is None or zaman < sinir:
            continue
        adlar.update(e.get("hayalet") or [])
    return len(adlar)


def _learning_feeds() -> dict:
    """Öğrenme döngüsünün İKİ BESLEME KANALI, karne satırı hâlinde. Okunamayan kanal None döner
    (uydurma yasağı) ve nedeni olaya yazılır — boş bir sözlük 'kanal sağlıklı' gibi okunurdu."""
    out: dict = {"antrenman": None, "dolgu_kuyrugu": None}
    try:
        from . import shadow_model as _sm
        out["antrenman"] = _sm.training_status()
    except Exception as e:
        from . import obs as _o
        _o.warn("learning_scorecard_training_failed", error=f"{type(e).__name__}: {e}",
                detail="antrenman durumu karneye GİRMEDİ (uydurulmadı)")
    try:
        from . import hermes as _h
        out["dolgu_kuyrugu"] = _h.backfill_queue()
    except Exception as e:
        from . import obs as _o2
        _o2.warn("learning_scorecard_backfill_failed", error=f"{type(e).__name__}: {e}",
                 detail="dolgu kuyruğu karneye GİRMEDİ (uydurulmadı)")
    # ÖĞRENME ANTRENMANI (sprint) DA BİR BESLEME KANALIDIR. `outcomes_measured` bugün
    # 1 ve o TEK satır H00026'dır (`source: sprint_search`, realized_delta −0,0364, 2026-07-14) —
    # yani karnedeki tek ölçülmüş sonuç sprint kökenli. Kanalın kendisi sekiz gündür atıl duruyordu
    # ve karnede bunun HİÇBİR izi yoktu: sayı "1" görünüyor, "1'de kalmasının sebebi" görünmüyordu.
    try:
        from . import sprint as _sp
        k = _sp.should_run()
        out["antrenman_sprinti"] = {
            "kos": k["kos"], "sebep": k["sebep"], "gecen_gun": k["gecen_gun"],
            "taze_hipotez": k["taze_hipotez"], "cfg": k["cfg"],
            "tetik": {"haftalik_gun": _sp.SPRINT_STALE_DAYS,
                      "taze_hipotez_esigi": _sp.SPRINT_MIN_NEW_HYP,
                      "gece_dilimi": list(_sp.SPRINT_HOURS)}}
    except Exception as e:
        from . import obs as _o3
        _o3.warn("learning_scorecard_sprint_failed", error=f"{type(e).__name__}: {e}",
                 detail="antrenman sprinti durumu karneye GİRMEDİ (uydurulmadı)")
        out["antrenman_sprinti"] = None
    return out


def agent_view() -> dict:
    """Öğrenme ajanının pano görünümü: skor tahtası, tüm hipotezler, kalibrasyon saçılımı
    (tahmin↔gerçekleşen), Brier kalibrasyonu ve beceri atribüsyonu.

    Salt-okuma; saçılıma yalnız `realized_delta`sı YAZILMIŞ (sonuçlanmış) hipotezler girer."""
    sb = store.read_json("scoreboard.json", {"versions": {}})
    hyps = memory.all_hypotheses()
    scatter = [{"predicted": h.get("predicted_delta"), "realized": h.get("realized_delta"),
                "variable": h.get("variable"), "status": h.get("status")}
               for h in hyps if h.get("realized_delta") is not None]
    return {"scoreboard": sb, "hypotheses": hyps, "calibration_scatter": scatter,
            "calibration": calibration(hyps), "skill_attribution": skill_attribution()}


# ---- SIRALAMA MATEMATİĞİ TEK YERDE ----------------------------------------------
# Bu iki yardımcı `score_calibration()`ın İÇİNDE kapalıydı. Bileşen IC'si aynı Spearman
# hesabını yapmak zorunda ve onu kendi dosyasında yeniden yazmak, aynı büyüklüğün iki uygulaması
# demekti — beraberlik kırma ya da tanımsızlık kuralı birinde değişirse iki rakam sessizce ayrışır
# ve hangisinin doğru olduğu hiçbir yerde yazmaz. Modül düzeyine çıkarıldı; davranış birebir aynı.
IC_MIN_SAMPLE = 30      # bir dilimin IC'si için en az satır; altı ÖLÇÜLEMEDİ'dir (None), 0.0 değil


def _rank_avg(x) -> "np.ndarray":
    """BERABERLİKLER ORTALAMA RÜTBEYLE KIRILIR (scipy'nin `ties='average'` eşdeğeri, elle).

    Eski `argsort(argsort(x))` beraberlikleri KEYFİ ve ASİMETRİK kırıyordu: skor 65 olan on
    aday, defterdeki SIRALARINA göre 12..21 rütbelerine dağılıyordu. Skor 0-100 tam sayı ve
    r_multiple sık sık aynı (ör. tam stop = -1.0R) olduğu için beraberlik burada istisna değil
    KURAL; kırılma yönü de veriden değil satır sırasından geliyordu — yani ölçüm, defterin
    yazılma sırasına duyarlıydı ve bunun hiçbir izi yoktu."""
    import numpy as np
    a1 = np.asarray(x, float)
    order = np.argsort(a1, kind="mergesort")        # kararlı sıralama: eşitler sırasını korur
    sx = a1[order]
    ranks = np.empty(len(a1), float)
    i = 0
    while i < len(order):
        k = i
        while k + 1 < len(order) and sx[k + 1] == sx[i]:
            k += 1
        ranks[order[i:k + 1]] = (i + k) / 2.0        # beraber olanların hepsine ORTALAMA rütbe
        i = k + 1
    return ranks


def spearman_ic(rows: list):
    """Spearman rank-IC ya da ÖLÇÜLEMEDİ (None) — TEK yöntem: havuzlanmış hesap, dilim hesabı ve
    bileşen IC'si hepsi bunu çağırır. `rows` = [(x, y), ...]. İki ayrı yerde iki ayrı rütbeleme,
    aynı büyüklüğün iki farklı değerini üretirdi."""
    import numpy as np
    a2 = np.asarray(rows, float)
    if a2.size == 0:
        return None
    rs2, rr2 = _rank_avg(a2[:, 0]), _rank_avg(a2[:, 1])
    den = rs2.std() * rr2.std()
    if den <= 0:
        # ÖLÇÜLEMEDİ, "0.0 KORELASYON" DEĞİL: bir tarafta hiç rütbe değişimi yoksa
        # (tüm skorlar aynı) korelasyon TANIMSIZDIR. Eski kod burada 0.0 döndürüyordu ve bu sayı
        # "ölçtük, ilişki yok" diye okunuyordu — ölçülmemiş bir değeri varsayılanla doldurmak.
        return None
    return float(((rs2 - rs2.mean()) * (rr2 - rr2.mean())).mean() / den)


def score_calibration() -> dict | None:
    """öneri #3 — skor→sonuç kalibrasyonu: 0-100 skor gerçekten monoton mu? Gerçek işlemler +
    karşı-olgusal defter (entered) birleşir; skor beşliklerine (quintile) kazanç oranı / ort. R ve
    Spearman rank-IC hesaplanır. Rapor-amaçlı: hiçbir karar okumaz; skor ağırlığı önerileri yine
    olasılıksal kapıdan geçmek zorunda. < 30 örneklem → None (uydurma istatistik yok)."""
    import numpy as np
    from . import counterfactual, sieve
    pairs = []
    # ELEME MUHASEBESİ — İKİ AYRI AŞAMA, TEK HARMAN DEĞİL: eski `.get() is not None`
    # sınaması eski şemayla tohumlanmış 90 GERÇEK işlemin 90'ını da sessizce eledi ("gerçek 0 /
    # simüle 241"). Gerçek ve cf akışları TEK sayaçta toplansaydı dedektör yine susardı — 241>0
    # olduğu için "hiç çıkmadı" kuralı tetiklenmezdi. Ayrı aşama = ayrı payda = görünür sıfır.
    from . import ledgerstamp as _ls
    # KAYNAK DAMGASI ÜÇÜNCÜ BİR AYRIM AÇAR. "gerçek" dilimi bugüne kadar TEK
    # popülasyondu; oysa içindeki satırların gövdesi replay tohumuydu. Yani "skorun tahmin gücü"
    # diye raporlanan IC, fiilen SİMÜLE bir defterin IC'siydi — cf dilimini ayırmakla çözülen
    # sorunun aynısı, bu kez gerçek dilimin İÇİNDE. Damga `pairs` üçlüsünün kaynak alanına yazılır;
    # eski `real`/`cf` alanları AYNEN kalır (geriye dönük uyum), ayrım `katmanlar`da açılır.
    kaynak_of = {}
    with sieve.Sieve("score_calibration.gercek") as sv:
        for t in _trades():
            if t.get("score") is None:
                sv.drop("sema:eksik_alan:score"); continue
            if t.get("r_multiple") is None:
                sv.drop("sema:eksik_alan:r_multiple"); continue
            sv.keep()
            k = _ls.kaynak_of(t)
            pairs.append((float(t["score"]), float(t["r_multiple"]), "real"))
            kaynak_of[len(pairs) - 1] = k
    with sieve.Sieve("score_calibration.cf") as sv:
        for r in counterfactual.resolved_rows(entered_only=True):
            if r.get("score") is None:
                sv.drop("sema:eksik_alan:score"); continue
            if r.get("r_multiple") is None:
                sv.drop("sema:eksik_alan:r_multiple"); continue
            sv.keep()
            pairs.append((float(r["score"]), float(r["r_multiple"]), "cf"))
    if len(pairs) < 30:
        return None

    _ic_of = spearman_ic          # modül düzeyindeki TEK yöntem (yukarı taşındı, davranış aynı)

    def _rank_ic(rows: list) -> dict | None:
        """Tek bir POPÜLASYON için Spearman rank-IC. Ayrı hesaplanır çünkü gerçek işlemler ile
        karşı-olgusal satırlar AYNI popülasyon değildir: gerçekler kapıdan geçmiş girişlerdir,
        cf satırları ise alınmamış hipotetik girişler. İkisini tek havuzda toplamak, kod tabanının
        rollback.py'de açıkça yasakladığı popülasyon karışımının ta kendisidir — ve canlıda 2102
        cf, 95 gerçeği 22:1 oranında boğuyordu: raporlanan 'skor IC'si' fiilen cf'in IC'siydi."""
        if len(rows) < IC_MIN_SAMPLE:
            return None
        ic2 = _ic_of(rows)
        if ic2 is None:
            return None                 # ölçülemedi → dilim YOK sayılır; sahte bir sayı sunulmaz
        return {"rank_ic": round(ic2, 4), "n": len(rows)}

    a = np.asarray([(s0, r0) for s0, r0, _ in pairs], float)
    sc, rm = a[:, 0], a[:, 1]
    ic = _ic_of([(s0, r0) for s0, r0, _ in pairs])      # havuzlanmış hesap da AYNI yardımcıyı kullanır
    order = np.argsort(sc)
    buckets = np.array_split(order, 5)                              # beşlikler: düşük→yüksek skor
    quint = [{"n": int(len(ix)), "score_lo": round(float(sc[ix].min()), 1),
              "score_hi": round(float(sc[ix].max()), 1),
              "win_rate": round(float((rm[ix] > 0).mean()), 3),
              "avg_r": round(float(rm[ix].mean()), 3)} for ix in buckets if len(ix)]
    n_real = sum(1 for *_, src in pairs if src == "real")
    n_cf = sum(1 for *_, src in pairs if src == "cf")
    real_ic = _rank_ic([(s0, r0) for s0, r0, src in pairs if src == "real"])
    cf_ic = _rank_ic([(s0, r0) for s0, r0, src in pairs if src == "cf"])
    # ANLAMLILIK YALNIZ GERÇEK DİLİM İÇİN. cf gözlemleri güne ve ticker'a KÜMELENMİŞ (tek günde
    # onlarca satır), yani i.i.d. değiller; dar bir güven aralığı ölçülmemiş bir kesinlik iddia
    # ederdi. Ölçemediğimizi None bırakıyoruz — canslim deseni.
    anlamli = None
    if real_ic:
        se = 1.0 / (real_ic["n"] - 1) ** 0.5
        anlamli = bool(abs(real_ic["rank_ic"]) > 1.96 * se)
        real_ic.update({"anlamli": anlamli, "se_yontem": "i.i.d._varsayimi"})
    if cf_ic:
        cf_ic["anlamli"] = None
        # CF DİLİMİ SADAKAT UYARISINI YANINDA TAŞIR: bu IC ALINMAMIŞ
        # hipotetik girişlerin, üstelik canlı motorun çıkış mekanizmalarının BİR KISMIYLA simüle
        # edilmiş sonuçlarının korelasyonudur. Etiketi sayının yanında durmazsa okur onu gerçek
        # işlem IC'siyle aynı kefeye koyar — cf 2100 satırla gerçeğin 95'ini 22:1 boğduğu için
        # bu karışım tam olarak havuzlanmış rakamı değersiz kılan şeydi.
        cf_ic["sadakat"] = CF_EXIT_FIDELITY_NOTE
    # ---- ÜÇ KATMAN AÇIK ADLA -------------------------------------------
    # `real`/`cf`/`rank_ic` alanları geriye dönük uyum için AYNEN kalır (eski tüketiciler kırılmasın).
    # `katmanlar` onların üstüne TEK ŞEKİLLİ bir sözlük koyar: pano, evidence_pack ve bileşen IC'si
    # üç katmanı aynı biçimde dolaşabilsin diye. Ayrı şekiller = her tüketicide ayrı ayrıştırma kodu
    # = katmanların birinin sessizce atlanması (havuzlanmış rakamın yıllarca tek görünen sayı olması
    # tam olarak böyle oldu).
    katmanlar = {
        "gercek": dict(real_ic) if real_ic else None,
        "cf": dict(cf_ic) if cf_ic else None,
        "havuz": ({"rank_ic": round(ic, 4), "n": len(pairs), "anlamli": None,
                   "karisim": f"{n_real} gerçek / {n_cf} sim"} if ic is not None else None),
    }
    # GERÇEK DİLİMİN İÇİ AÇILIR: canlı kâğıt satırlar ile replay tohumu AYNI popülasyON
    # değildir — tohum bugünkü evrenle (survivorship) üretilmiş bir simülasyondur. Ayrı IC'ler
    # <30 örneklemde None döner (`_rank_ic` kuralı): ölçülmeyen sayı UYDURULMAZ.
    # AYRI EKSEN, AYRI ALAN: `katmanlar` "gerçek / cf / havuz" ÜÇLÜSÜDÜR ve tüketiciler onu
    # tek şekilli üç kova olarak dolaşır (`test_kuzey_yildizi_v108` bu üçlüyü ADIYLA kilitler).
    # Kaynak kırılımı o üçlünün dördüncü kovası DEĞİL, "gerçek" kovasının İÇ eksenidir — oraya
    # dördüncü anahtar olarak girseydi üçlüyü dolaşan her tüketici onu yanlışlıkla bir katman
    # sanardı. Üst düzeyde, kendi adıyla durur.
    kaynak_katman = {}
    for _ad in (_ls.LIVE_PAPER, _ls.REPLAY_SEED, _ls.BELIRSIZ):
        _rows = [(s0, r0) for i, (s0, r0, src) in enumerate(pairs)
                 if src == "real" and kaynak_of.get(i) == _ad]
        kaynak_katman[_ad] = {"n": len(_rows), "ic": _rank_ic(_rows)}
    return {"n": len(pairs), "n_real": n_real, "n_cf": n_cf,
            # GERÇEK DİLİMİN KAYNAK KIRILIMI ÜST DÜZEYDE DE DURUR: `katmanlar` içinde gömülü
            # kalsaydı eski tüketiciler (pano, evidence_pack) onu hiç görmezdi ve "gerçek n=95"
            # cümlesi yine tek sayı olarak okunurdu.
            "gercek_kaynak": kaynak_katman,
            "rank_ic": None if ic is None else round(ic, 4), "quintiles": quint,
            "katmanlar": katmanlar,
            # AYRIŞTIRILMIŞ ÖLÇÜM: `rank_ic` geriye dönük uyum için HAVUZLANMIŞ
            # değer olarak kalır (eski tüketiciler kırılmasın), ama karar verecek olan bunlardır.
            "real": real_ic, "cf": cf_ic,
            # HÜKÜM METNİ İKİ AYRI ÖLÇÜLEMEYİŞİ BİRLİKTE ANLATIR: dilim <30 olabilir ya
            # da 30+ olup rütbe değişimi hiç olmayabilir (tüm skorlar aynı → korelasyon tanımsız).
            # İkisi de "ÖLÇÜLMEDİ"dir; hangisi olduğu n_real alanından okunur.
            "verdict": (f"gerçek dilim ÖLÇÜLMEDİ (n={n_real}; <30 ya da rütbe değişimi yok) — "
                        f"skorun tahmin gücü hakkında bir şey söylenemez" if not real_ic
                        else f"gerçek dilim IC {real_ic['rank_ic']} (n={real_ic['n']}), "
                             + ("anlamlı" if anlamli else "gürültüden ayırt EDİLEMİYOR")),
            "monotone_hint": bool(len(quint) == 5 and quint[-1]["avg_r"] > quint[0]["avg_r"]),
            sieve.PROV_KEY: sieve.provenance(len(pairs), n_real, n_cf,
                                             stages_=("score_calibration.gercek",
                                                      "score_calibration.cf"))}


SCORE_CAL_HISTORY = "score_calibration_history.jsonl"


def record_score_calibration_point(date: str, cal: dict) -> bool:
    """SKOR IC'sinin ZAMAN SERİSİ — "yükseliyor mu?" tek bir sayıdan CEVAPLANAMAZ.

    `score_calibration.json` her P5 turunda ÜZERİNE yazılır: panoda hep bugünün IC'si durur, dünkü
    hiç var olmamış gibi. Oysa operatörün sorduğu soru "IC bugün kaç?" değil "IC YÜKSELİYOR MU?" —
    yani öğrenme çarkının gerçekten döndüğünün tek bakışta görünen kanıtı. Bu fonksiyon her bar
    gününe BİR nokta düşürür (P5 bar günü başına), böylece trend defterde birikir.

    IDEMPOTENT: worker yeniden başlarsa ya da aynı gün P5 iki kez koşarsa aynı tarihe İKİNCİ nokta
    düşmez (False döner). Aksi hâlde tek bir yeniden başlatma seriyi sahte bir "yoğunlaşma" ile
    doldurur ve trendin eğimi ölçümden değil süreç kazalarından gelirdi.

    Alanlar `score_calibration()` çıktısının GERÇEK şemasından alınır: `rank_ic` HAVUZLANMIŞ (sim
    ağırlıklı) değerdir, `real` ise gerçek dilimin ayrı hesabıdır ve <30 örneklemde ya da rütbe
    değişimi yokken None'dır — ölçülmeyen None kalır, sıfırla doldurulmaz (UYDURMA YASAĞI)."""
    if not date or not isinstance(cal, dict):
        return False
    rows = store.read_jsonl(SCORE_CAL_HISTORY)
    if rows and rows[-1].get("date") == date:
        return False
    real = cal.get("real") or {}
    cfl = cal.get("cf") or {}
    store.append_jsonl(SCORE_CAL_HISTORY, {
        "date": date,
        "rank_ic": cal.get("rank_ic"),          # havuzlanmış — cf satırları gerçekleri boğar, etiketi panoda
        "real_ic": real.get("rank_ic"),         # kararın dayanacağı ölçüm; ölçülmediyse None
        # ÜÇÜNCÜ KATMAN SERİYE DE GİRER: trend grafiği iki çizgi çiziyordu
        # (gerçek + havuz) ve aradaki farkın NEREDEN geldiği okunamıyordu. cf dilimi ayrı çizilmeden
        # "havuz neden gerçekten farklı?" sorusu her bakışta yeniden tahmin edilmek zorundaydı.
        "cf_ic": cfl.get("rank_ic"),
        "n_real": cal.get("n_real"),
        "n_cf": cal.get("n_cf")})
    return True


def prediction_hit_rate() -> dict:
    """ÖĞRENME ÇARKININ KAPANAN UCU: tahmin edilen delta ile GERÇEKLEŞEN delta tutuyor mu?

    Yalnız İKİSİ DE ölçülü satırlar sayılır. `predicted_delta` neredeyse her hipotezde vardır ama
    `realized_delta` yalnız terminal (promoted/rolled_back/superseded) satırlarda dolar — tek başına
    tahmin sayısını raporlamak "35 tahmin ölçüldü" gibi okunurdu, oysa ölçülen bir tanesi bile
    olmayabilir. k=0 iken oran UYDURULMAZ: sign_hits/mean_abs_err None kalır (dürüst boş)."""
    n = hits = 0
    err = 0.0
    for h in store.read_jsonl("hypotheses.jsonl"):
        p, r = h.get("predicted_delta"), h.get("realized_delta")
        if p is None or r is None:
            continue
        try:
            p, r = float(p), float(r)
        except (TypeError, ValueError):  # sessiz-yutma: biçimsiz tek defter satırı ölçümün DIŞINDA kalır; sayılsaydı payda şişer ve isabet oranı seyrelirdi — atlanan satır zaten n'e girmediği için sayım dürüst kalır
            continue
        n += 1
        # İŞARET TUTTU MU: 0 kendi başına bir işarettir (tahmin "değişmez" dediyse ve gerçekten
        # değişmediyse bu bir İSABETTİR); >0/<0 ile aynı kefeye konsaydı sıfır tahminler ya hep
        # tutar ya hep tutmaz görünürdü.
        if (p > 0 and r > 0) or (p < 0 and r < 0) or (p == 0 and r == 0):
            hits += 1
        err += abs(r - p)
    if not n:
        return {"n": 0, "sign_hits": None, "mean_abs_err": None}
    return {"n": n, "sign_hits": hits, "mean_abs_err": round(err / n, 4)}


def deflate_stats() -> dict | None:
    """Model Aşırı-Güven sayacı: her ship'te arama-OOS iyimserliği (predicted_delta_search)
    onay yürüyüşü ortalamasıyla (predicted_delta) DEFLATE ediliyor. Bu fonksiyon o kırpmanın oranını
    raporlar: deflasyon% = 1 − onay/arama. Yüksek ortalama deflasyon = arama katmanı sistematik
    iyimser demektir (kapının bunu kırptığının kanıtı). Ship'siz defter → None."""
    rows = []
    for h in store.read_jsonl("hypotheses.jsonl"):
        ps, pc = h.get("predicted_delta_search"), h.get("predicted_delta")
        if ps is None or pc is None or abs(float(ps)) < 1e-9:
            continue
        rows.append({"id": h.get("id"), "variable": h.get("variable"),
                     "search": round(float(ps), 4), "confirm": round(float(pc), 4),
                     "deflation_pct": round((1.0 - float(pc) / float(ps)) * 100.0, 1)})
    if not rows:
        return None
    import numpy as np
    return {"n": len(rows), "avg_deflation_pct": round(float(np.mean([r["deflation_pct"] for r in rows])), 1),
            "last": rows[-8:]}


def deflate_why() -> dict:
    """BOŞ GÖSTERGENİN GEREKÇESİ — ölçülmüş, uydurulmamış.

    Pano boş deflasyon halkasını "henüz ship yok — ilk ship'te dolar" diye açıklıyordu. Bu iddia
    `deflate_stats() is None`'dan TÜRETİLMİŞTİ, ship sayısından değil — ve defterde ship VARDI
    (2 superseded). Daha kötüsü vaat de yanlıştı: `predicted_delta_search` YALNIZ teyit yürüyüşünü
    geçen ship yolunda yazılır, dolayısıyla hipotezlerin hepsi kapıda elenirken halka asla dolmaz.
    Boş bir gösterge huninin NEREDE öldüğünü söylemeli; "birazdan dolar" dememeli."""
    from collections import Counter
    hyp = store.read_jsonl("hypotheses.jsonl")
    dur = Counter(h.get("status") or "?" for h in hyp)
    shipped = sum(n for s, n in dur.items() if s in SHIP_DURUMLARI)
    olculu = sum(1 for h in hyp if h.get("predicted_delta_search") is not None)
    return {"n_hypotheses": len(hyp), "shipped": shipped, "measured": olculu,
            "by_status": dict(dur.most_common()),
            # ship olmuş ama alanı olmayan satırlar = alan eklenmeden önce ship edilmiş eski kayıtlar
            "legacy_ships": max(0, shipped - olculu)}


# ---- LLM danışman kalibrasyonu + terfi kuralı (ŞİMDİDEN yazılı, yetki uykuda) ----
LLM_CAL_FILE = "llm_calibration.json"
LLM_PROMOTE_MIN_PAIRS = 30      # toplam taze görüş-sonuç çifti tabanı
LLM_PROMOTE_MIN_BUCKET = 8      # hem 'destekle' hem 'karşı' kovasında en az bu kadar örnek
LLM_PROMOTE_R_GAP = 0.3        # avg_r(destekle) − avg_r(karşı) en az bu kadar olmalı


PLAN_ATIF_KIRILIM_NOT = (
    "MODEL KIRILIMI TERFİYE GİRMEZ — betimleyicidir. Terfi kuralı (`n_pairs`/kova/`r_gap`) "
    "DEĞİŞMEDİ; eşiği model başına bölmek kart-önce iştir. `atifsiz_n` atıf defteri doğmadan "
    "(2026-08-24) damgalanmış çiftlerdir: retro damga YASAK olduğu için künyeleri hiç olmayacak "
    "ve bir modele YAMANMAZLAR. `olculemeyen_n` atfı VAR ama adı ölçülememiş çiftlerdir (zincir "
    "adsızdı) — 'atıf yok' ile 'ad yok' ayrı hâllerdir. `backfill_n` o modelin çiftlerinden kaçının "
    "GERİYE damga olduğunu söyler: geriye damga bir arıza değildir, ama karışırsa 'model değişti, "
    "isabet arttı' okuması sahte çıkar (Ö-39'un kök kusuru)."
)


def _plan_atif_kirilimi(pair_pids: list, pairs: list) -> dict:
    """Kalibrasyon çiftlerini `plan_atif.jsonl` (Ö-39 atıf defteri) ile plan_id üstünden birleştirir.

    YASA 6'nın gereği: bu defterin okuyucusu İLK GÜNDEN vardır — okuyucusuz defter açılmaz
    (uyuyan-yol dersi). Cevapladığı soru: "hangi model kaç çift üretti, ortalama R'si ne, kaçı
    geriye damga?" — terfi 2026-08-14'te açıldığından beri sorulabilir ama cevaplanamaz olan soru.
    AYNI PLANA BİRDEN ÇOK SATIR: damga var olan `llm_opinion`ı ezmediği için normalde tek satır
    düşer; yine de defter append-only olduğundan İLK satır otorite kabul edilir (görüşü yazan
    çağrı odur), sonrakiler sayılmaz."""
    atif = {}
    for r in store.read_jsonl("plan_atif.jsonl"):
        pid = str(r.get("plan_id"))
        if pid not in atif:
            atif[pid] = r
    modeller: dict = {}
    atifli = olculemeyen = 0
    for pid, (_op, r_mult) in zip(pair_pids, pairs):
        row = atif.get(pid)
        if row is None:
            continue
        atifli += 1
        ad = row.get("model")
        if not ad:
            # UYDURMA YASAĞI: adsız satır bir kovaya yazılmaz ("varsayılan" diye bir model YOK).
            olculemeyen += 1
            continue
        b = modeller.setdefault(ad, {"n": 0, "sum_r": 0.0, "backfill_n": 0})
        b["n"] += 1
        b["sum_r"] += float(r_mult)
        b["backfill_n"] += 1 if row.get("backfill") else 0
    return {"n_cift": len(pairs), "atifli_n": atifli, "atifsiz_n": len(pairs) - atifli,
            "olculemeyen_n": olculemeyen,
            "modeller": {ad: {"n": b["n"], "avg_r": round(b["sum_r"] / b["n"], 3),
                              "backfill_n": b["backfill_n"]}
                         for ad, b in modeller.items()},
            "not": PLAN_ATIF_KIRILIM_NOT}


def llm_opinion_calibration() -> dict:
    """Ajanın görüşleri gerçekten sinyal mi? Kapanan işlemler plan görüşleriyle (plan_id join)
    eşleştirilir; kova başına n / kazanma / ort.R. Terfi yalnız yazılı kuralla: ≥{pairs} çift,
    her kovada ≥{bucket}, R farkı ≥{gap}. Terfi SONRASI tek yetki: REVIEW + 'karşı' → dolumdan
    düşürme (P4). GO'ya, boyuta, çıkışa asla dokunamaz."""
    from . import sieve
    plan_rows = store.read_jsonl("trade_plans.jsonl")
    plans = {p.get("id"): p for p in plan_rows}      # join tarafı: kimliğe göre (son satır kazanır)
    pairs = []
    pair_pids: list[str] = []                        # `pairs` ile HİZALI plan kimlikleri (Ö-39 atfı)
    # `(plans.get(...) or {}).get("llm_opinion")` üç AYRI sessiz elemeyi tek satıra gizliyordu:
    # plan_id yok / plan birleşmedi (canlıda `P00140` ↔ `P-2026-07-20-AAA` şema çatışması) /
    # görüş yok. İlk ikisi ŞEMA hatası, üçüncüsü meşru bilgi — artık ayrı ayrı sayılıyor.
    with sieve.Sieve("llm_opinion_calibration.gercek") as sv:
        for t in _trades():
            pid = t.get("plan_id")
            if not pid:
                sv.drop("sema:eksik_alan:plan_id"); continue
            plan = plans.get(pid)
            if plan is None:
                sv.drop("sema:plan_join_yok"); continue
            op = plan.get("llm_opinion")
            if not op:
                # EZER: (ezen kod değil GÖRÜŞ KURAKLIĞI) LLM_PROMOTE_MIN_PAIRS terfi eşiği ezilen
                # taraf — 25d zinciri c-8 (canlı sieve: 97 gerçek işlemin 93'ü bu satırdan
                # düşüyor → n_pairs 4 < 30, promoted=false; eşik değil ÜRETİCİ bağlıyor), 2026-08-23
                sv.drop("piyasa:llm_görüşü_yok"); continue
            if t.get("r_multiple") is None:
                sv.drop("sema:eksik_alan:r_multiple"); continue
            sv.keep()
            pairs.append((op, float(t["r_multiple"])))
            pair_pids.append(str(pid))                       # atıf kırılımının join anahtarı
        if len(pairs) > 100:                                 # taze pencere kırpması da bir elemedir
            sv.drop("piyasa:taze_pencere_dışı", n=len(pairs) - 100, from_kept=True)
    pairs = pairs[-100:]                                     # taze pencere
    pair_pids = pair_pids[-100:]                             # AYNI kırpma — iki liste hizalı kalmalı
    buckets = {}
    for op, r in pairs:
        b = buckets.setdefault(op, {"n": 0, "wins": 0, "sum_r": 0.0})
        b["n"] += 1; b["wins"] += 1 if r > 0 else 0; b["sum_r"] += r
    out_b = {op: {"n": b["n"], "win_rate": round(b["wins"] / b["n"], 3),
                  "avg_r": round(b["sum_r"] / b["n"], 3)} for op, b in buckets.items()}
    d, k = out_b.get("destekle"), out_b.get("karşı")
    gap = round(d["avg_r"] - k["avg_r"], 3) if d and k else None
    promoted = bool(len(pairs) >= LLM_PROMOTE_MIN_PAIRS and d and k
                    and d["n"] >= LLM_PROMOTE_MIN_BUCKET and k["n"] >= LLM_PROMOTE_MIN_BUCKET
                    and gap is not None and gap >= LLM_PROMOTE_R_GAP)
    # #4: SİMÜLE (karşı-olgusal) çiftler — yalnız GÖSTERGE. Terfi kararına asla girmez (doldurma
    # gerçekçiliği yok); amacı ajanın sinyal taşıyıp taşımadığını aylar değil haftalar içinde göstermek.
    cf_buckets = {}
    with sieve.Sieve("llm_opinion_calibration.cf") as sv:
        try:
            from . import counterfactual
            for r in counterfactual.resolved_rows(entered_only=True):
                op = r.get("llm_opinion")
                if not op:
                    sv.drop("piyasa:llm_görüşü_yok"); continue
                if r.get("r_multiple") is None:
                    sv.drop("sema:eksik_alan:r_multiple"); continue
                sv.keep()
                b = cf_buckets.setdefault(op, {"n": 0, "sum_r": 0.0})
                b["n"] += 1; b["sum_r"] += float(r["r_multiple"])
        except Exception as e:
            # BULGU: burası `except Exception: pass` idi. cf defteri okunamazsa gösterge kovaları
            # BOŞ dönüyor ve pano "simüle kanıt yok" diye gösteriyordu — oysa kanıt vardı, okuma
            # patlamıştı. Artık hem olay kaydı hem sayılı bir eleme (aşama in>0/out==0 → ihlal).
            from . import obs
            obs.warn("llm_cal_cf_source_failed", error=type(e).__name__)
            sv.drop("sema:kaynak_okunamadı:counterfactual")
    cf_out = {op: {"n": b["n"], "avg_r": round(b["sum_r"] / b["n"], 3)} for op, b in cf_buckets.items()}
    prev = store.read_json(LLM_CAL_FILE, {})
    _n_cf = sum(b["n"] for b in cf_out.values())
    # ÖNCÜ GÖSTERGE — ÇİFTLERDEN ÖNCE GELİR. `n_pairs` ancak KAPANAN işlemlerle dolar,
    # yani 0→30 yolu haftalar sürer. Beyin 07-21'den 07-26'ya ölüydü ve o süre boyunca damgalama da
    # durmuştu; bugün diriltildi. "Damgalama gerçekten geri döndü mü" sorusunun cevabı plan
    # defterinde çiftlerden GÜNLER önce görünür: yeni bir plan görüş taşıyorsa `_stamp_llm_opinions`
    # yeniden koşuyor demektir. Bunu ölçmeden beklemek, ölü bir beyni "örneklem birikiyor" sanmaktır
    # — 07-21..26'da tam olarak olan buydu. Sayım TÜM defter üzerindedir (join sözlüğü değil: kimliksiz
    # satırlar tek anahtara çökerdi ve öncü gösterge kendi eksiğini gizlerdi).
    _opinion_rows = [p for p in plan_rows if p.get("llm_opinion")]
    _opinion_dates = sorted(str(p["date"]) for p in _opinion_rows if p.get("date"))
    out = {"n_pairs": len(pairs), "buckets": out_b, "r_gap": gap, "promoted": promoted,
           "cf_buckets": cf_out, "cf_pairs": _n_cf,
           "n_plans_with_opinion": len(_opinion_rows),
           # UYDURMA YASAĞI: hiç görüşlü plan yoksa (ya da hiçbirinde tarih yoksa) None — "bugün"
           # yazmak ölü bir damgalamayı diri göstermenin en kısa yolu olurdu.
           "last_opinion_plan_date": _opinion_dates[-1] if _opinion_dates else None,
           # Ö-39 ATIF KIRILIMI: "hangi beyin ne kadar isabetli" sorusunun ilk cevap yüzeyi.
           # BETİMLEYİCİ — `promoted` hesabına GİRMEZ (bkz. PLAN_ATIF_KIRILIM_NOT).
           "model_kirilim": _plan_atif_kirilimi(pair_pids, pairs),
           "rule": f">={LLM_PROMOTE_MIN_PAIRS} çift · kova>={LLM_PROMOTE_MIN_BUCKET} · "
                   f"Rfark>={LLM_PROMOTE_R_GAP} → yalnız REVIEW+karşı dolum vetosu",
           # KÜNYE: terfi kararı YALNIZ gerçek çiftlerden çıkar; cf yalnız göstergedir. Tek bir
           # "n_pairs" yayınlamak bu ayrımı gizlerdi — payda ve kaynak artık satırın yanında.
           sieve.PROV_KEY: sieve.provenance(len(pairs) + _n_cf, len(pairs), _n_cf,
                                            stages_=("llm_opinion_calibration.gercek",
                                                     "llm_opinion_calibration.cf"))}
    store.write_json(LLM_CAL_FILE, out)
    if promoted != bool(prev.get("promoted")):
        # YETKİ DEĞİŞİMİ ALARM SEVİYESİDİR. Buradaki flip, bir danışmanın CANLI karar
        # yüzeyine dokunma hakkını EŞİK DOLDUĞU İÇİN kendiliğinden kazanması ya da kaybetmesidir —
        # operatör onaylamaz, HABERDAR EDİLİR. `obs.log` ile yazıldığında bu devir olay defterinin
        # içinde sıradan bir satırdı ve panel açılmadan hiçbir yere ulaşmıyordu.
        # İKİ YÖN DE YÜKSEK SESLİ: yetkinin geri alınması sessiz kalırsa "danışman hâlâ konuşuyor"
        # sanılır — kayıp, kazanım kadar operatörü ilgilendirir. Alan adları DEĞİŞMEDİ (promoted /
        # r_gap / n): kanal yükseldi, sözleşme değil.
        from . import obs
        obs.alarm(obs.ALARM_AUTHORITY,
                  f"LLM danışman yetkisi {'AÇILDI' if promoted else 'GERİ ALINDI'} — "
                  f"R farkı {gap if gap is not None else 'ölçülmedi'}, n={len(pairs)} çift "
                  f"(yetki: yalnız REVIEW+karşı dolum vetosu)",
                  promoted=promoted, r_gap=gap, n=len(pairs))
    return out


def llm_promoted() -> bool:
    """LLM görüşü kalibrasyon dosyasında TERFİ ETMİŞ olarak işaretli mi? (salt-okuma, dosya yoksa False)."""
    return bool(store.read_json(LLM_CAL_FILE, {}).get("promoted"))


EXIT_EFF_FILE = "exit_efficiency.json"
EXIT_NUDGE_LEFT_R = 0.5    # ort. masada-kalan R bu eşiği aşarsa UCB'de exit.* düğmeleri küçük öncelik alır


def exit_efficiency() -> dict | None:
    """#4 — MFE/MAE tüketicisi: çıkış nedeni başına 'tepe gördü ama nerede kapandı?' muhasebesi.
    left_r = ort(MFE − gerçekleşen R) = masada bırakılan ödül. Gerçek işlemler + cf (entered) birleşir;
    kaynak kırılımı dürüstçe ayrı. Rapor-amaçlı: karar yetkisi yok; UCB yalnız KÜÇÜK bir sıralama
    dürtmesi alır (reflect._ucb_rank) — kapı yasası değişmez. <10 örnek → None."""
    from . import counterfactual as cf, sieve
    rows = []
    with sieve.Sieve("exit_efficiency.gercek") as sv:
        for t in _trades():
            if t.get("mfe_r") is None:
                sv.drop("sema:eksik_alan:mfe_r"); continue
            if t.get("r_multiple") is None:
                sv.drop("sema:eksik_alan:r_multiple"); continue
            sv.keep()
            rows.append((str(t.get("exit_reason") or "?"), float(t["mfe_r"]), float(t["r_multiple"]), "real"))
    with sieve.Sieve("exit_efficiency.cf") as sv:
        for r in cf.resolved_rows(entered_only=True):
            if r.get("mfe_r") is None:
                sv.drop("sema:eksik_alan:mfe_r"); continue
            if r.get("r_multiple") is None:
                sv.drop("sema:eksik_alan:r_multiple"); continue
            sv.keep()
            rows.append((str(r.get("exit_reason") or "?"), float(r["mfe_r"]), float(r["r_multiple"]), "cf"))
    if len(rows) < 10:
        return None
    by: dict[str, dict] = {}
    for reason, mfe, rm, src in rows:
        b = by.setdefault(reason, {"n": 0, "sum_mfe": 0.0, "sum_r": 0.0, "n_cf": 0})
        b["n"] += 1; b["sum_mfe"] += mfe; b["sum_r"] += rm
        b["n_cf"] += 1 if src == "cf" else 0
    reasons = {k: {"n": b["n"], "n_cf": b["n_cf"], "avg_mfe_r": round(b["sum_mfe"] / b["n"], 3),
                   "avg_realized_r": round(b["sum_r"] / b["n"], 3),
                   "left_r": round((b["sum_mfe"] - b["sum_r"]) / b["n"], 3)}
               for k, b in by.items()}
    total_left = round(sum(b["sum_mfe"] - b["sum_r"] for b in by.values()) / len(rows), 3)
    worst = max(reasons.items(), key=lambda kv: kv[1]["left_r"])
    _n_cf = sum(1 for *_, src in rows if src == "cf")
    out = {"n": len(rows), "avg_left_r": total_left, "worst_reason": worst[0],
           "worst_left_r": worst[1]["left_r"], "reasons": reasons,
           "nudge_active": total_left > EXIT_NUDGE_LEFT_R,
           # nudge_active UCB sıralamasını dürtüyor: hangi paydadan geldiği (gerçek mi simüle mi)
           # rakamın YANINDA durmalı — statik-bracket cf'si MFE'yi sistematik farklı ölçer.
           sieve.PROV_KEY: sieve.provenance(len(rows), len(rows) - _n_cf, _n_cf,
                                            stages_=("exit_efficiency.gercek", "exit_efficiency.cf"))}
    store.write_json(EXIT_EFF_FILE, out)
    return out


# ---- KÂR ŞELALESİ -----------------------------------------------------------
# NEDEN. "Edge var mı?" ile "para var mı?" AYNI SORU DEĞİL. Bir sinyal doğru yönü gösterip yine de
# para kaybettirebilir: tepe görülür ama geri verilir, ya da friksiyon kalanı yer. Bugüne kadar bu
# üç kayıp kaynağı tek bir sayının (`r_multiple`) içinde eriyordu ve "hangisini düzeltirsek para
# gelir?" sorusunun cevabı yoktu — çıkış mimarisinin bütün kararları buna bakacak.
#
# ÖZDEŞLİK (yaklaşık değil, TAM): net_R = MFE_R + (brüt_R − MFE_R) − friksiyon_R
#   * MFE_R          = `mfe_r` — sinyalin SUNDUĞU en iyi nokta (friksiyonsuz, fiyat tabanlı).
#   * brüt_R − MFE_R = tepeden çıkışa GERİ VERİLEN kısım (çıkış kuralının imzası; hep ≤ 0).
#   * friksiyon_R    = `costs` / risk_dolar — komisyon + kayma.
#   * net_R          = `r_multiple` (defterdeki gerçekleşen).
# ALAN ANLAMLARI CANLI KAYNAKTAN DOĞRULANDI (broker.close_position):
#   `pnl_dollars` NET'tir (komisyonlar düşülmüş, kayma zaten fiyatın içinde), `r_multiple` =
#   pnl/risk_dolar yani O DA NET, `costs` = giriş kayması + çıkış kayması + ÇIKIŞ komisyonu.
#   `costs` GİRİŞ komisyonunu İÇERMEZ (broker onu "informational total friction" diye toplar);
#   canlı `goal.yaml`da `commission_per_share: 0.0` olduğu için bugün fark sıfırdır, ama komisyon
#   açılırsa friksiyon bacağı hafif EKSİK ölçer — bu yüzden yazıyor (uydurma yasağı: bilinen kusur
#   beyan edilir, sessizce taşınmaz).
# risk_dolar defterde ALAN DEĞİLDİR ama türetilebilir: r_multiple = pnl_dollars / risk_dolar
# özdeşliğinden risk_dolar = pnl_dollars / r_multiple. r_multiple = 0 olan satırda bölme tanımsız →
# o satırın friksiyonu None kalır (satır tümden atılmaz: MFE bacağı hâlâ ölçülebilir).
WATERFALL_MIN_N = 5


def _waterfall_rows(trades: list) -> tuple[list, dict]:
    """Şelalenin işlem başına ayrıştırması. (satırlar, eleme_muhasebesi)."""
    from . import sieve
    out = []
    # persist=False — `benchmark_relative` ile aynı gerekçe: bu fonksiyon /api/diagnostics'in her
    # anketinde koşar, okuma modeli yazıcıya dönüşmemeli.
    with sieve.Sieve("profit_waterfall", persist=False) as sv:
        for t in trades:
            if t.get("r_multiple") is None:
                sv.drop("sema:eksik_alan:r_multiple"); continue
            try:
                net_r = float(t["r_multiple"])
            except (TypeError, ValueError):  # sessiz-yutma: aynı gerekçe — sv.drop sayacı `eleme` alanıyla dışarı veriliyor
                sv.drop("sema:biçimsiz:r_multiple"); continue
            mfe = t.get("mfe_r")
            try:
                mfe_r = None if mfe is None else float(mfe)
            except (TypeError, ValueError):  # sessiz-yutma: biçimsiz MFE satırı DÜŞÜRMEZ; sinyal bacağının paydası `n_mfe` olarak ayrı raporlanır ve `n`den küçük kalması eksikliği görünür kılar
                mfe_r = None
            # MFE'si olmayan satır DÜŞÜRÜLMEZ, `keep` sayılır: friksiyon ve net bacakları onda da
            # ölçülebilir. Eleme muhasebesi "bu satır kullanıldı mı?" sorusunu cevaplar; bacak
            # bazında hangi paydaya girdiği ayrı sayaçlarda durur (`n`, `n_mfe`, `n_friksiyon`,
            # `n_verim`). Burada `drop` demek, kullanılan bir satırı elenmiş göstermek olurdu —
            # muhasebe kendi kendine yalan söylerdi.
            sv.keep()
            risk_d = None
            try:
                pnl_d, costs = float(t.get("pnl_dollars")), float(t.get("costs"))
                if abs(net_r) > 1e-9:
                    risk_d = pnl_d / net_r
            except (TypeError, ValueError):  # sessiz-yutma: friksiyon ÖLÇÜLEMEDİ → None; bacağın paydası `n_friksiyon` ayrı sayılır ve `n`den küçüklüğü eksik ölçümü ele verir (uydurma sıfır yazılmaz)
                costs = None
            friksiyon_r = (round(costs / risk_d, 4)
                           if (costs is not None and risk_d not in (None, 0.0) and risk_d > 0)
                           else None)
            brut_r = None if friksiyon_r is None else round(net_r + friksiyon_r, 4)
            # ÇIKIŞ VERİMİ = gerçekleşen R / MFE. MFE<=0 olan işlemde TANIMSIZ (None): sinyal hiç
            # lehte hareket sunmadıysa "tepenin ne kadarını aldık?" sorusunun paydası yoktur —
            # 0'a bölmek ya da 0 yazmak, çıkış kuralını hiç suçu olmayan bir kayıptan sorumlu
            # tutardı (kayıp GİRİŞ tarafındandır).
            verim = (round(net_r / mfe_r, 4) if (mfe_r is not None and mfe_r > 1e-9) else None)
            out.append({"exit_reason": str(t.get("exit_reason") or "?"),
                        "mfe_r": mfe_r, "brut_r": brut_r, "friksiyon_r": friksiyon_r,
                        "net_r": round(net_r, 4), "cikis_verimi": verim})
        return out, sv.snapshot()


def _ort(vals: list) -> float | None:
    """Listenin ortalaması (4 ondalık); liste BOŞSA None — boş örneklem 0.0 SAYILMAZ."""
    return None if not vals else round(sum(vals) / len(vals), 4)


def profit_waterfall() -> dict | None:
    """SİNYAL → ÇIKIŞ → FRİKSİYON → NET: kâr nerede kazanılıyor, nerede sızıyor?

    Saf okuma (hiçbir dosyaya yazmaz, hiçbir karara girmez). `exit_reason` kırılımı 2026-07-28
    otopsisinin KALICILAŞMASIdır: o gün kârın time_stop'tan geldiği (+$3.944, %70 isabet), stopların
    kanattığı (-$11.811, ort. MFE +0.71R) tek seferlik bir elde-hesapla bulunmuştu; tek seferlik
    bulgu bir sonraki hafta kimsenin bakmadığı bir yerde eskir.

    `<{WATERFALL_MIN_N} işlem → None`: dört işlemden "çıkış verimi %31" diye bir oran üretmek,
    ölçüm değil süslemedir."""
    trades = _trades()
    rows, eleme = _waterfall_rows(trades)
    if len(rows) < WATERFALL_MIN_N:
        return None

    def _blok(rs: list) -> dict:
        """Bir satır kümesinin şelale bloğu: sinyal MFE, geri verilen, friksiyon, net R ve çıkış verimi.

        Her büyüklük KENDİ ölçülmüş paydasından hesaplanır ve payda sayıları (`n_mfe`, `n_friksiyon`,
        `n_verim`) ayrıca raporlanır; "geri verilen" yalnız HER İKİ ucu da ölçülü satırlardan alınır."""
        mfe = [r["mfe_r"] for r in rs if r["mfe_r"] is not None]
        fr = [r["friksiyon_r"] for r in rs if r["friksiyon_r"] is not None]
        net = [r["net_r"] for r in rs]
        # GERİ VERİLEN: yalnız HER İKİ ucu da ölçülü satırlardan (brüt ve MFE aynı satırda varsa).
        # Farklı paydalardan iki ortalamayı çıkarmak, özdeşliği bozan bir "şelale" üretirdi.
        geri = [r["brut_r"] - r["mfe_r"] for r in rs
                if r["brut_r"] is not None and r["mfe_r"] is not None]
        verim = [r["cikis_verimi"] for r in rs if r["cikis_verimi"] is not None]
        return {"n": len(rs), "n_mfe": len(mfe), "n_friksiyon": len(fr), "n_verim": len(verim),
                "sinyal_mfe_r": _ort(mfe), "geri_verilen_r": _ort(geri),
                "friksiyon_r": _ort(fr), "net_r": _ort(net),
                # ÇIKIŞ VERİMİ İKİ TÜRLÜ: satır başına oranların ortalaması (`ort_verim`) uç
                # değerlere duyarlıdır (MFE 0.01 olan bir satır oranı patlatır); toplulaştırılmış
                # oran (`toplam_verim` = ΣR / ΣMFE) portföy düzeyinde ne olduğunu söyler. İkisi
                # farklı sorular ve ikisi de raporlanır — biri diğerinin yerine geçemez.
                "ort_verim": _ort(verim),
                "toplam_verim": (round(sum(net) / sum(mfe), 4)
                                 if mfe and sum(mfe) > 1e-9 else None)}

    genel = _blok(rows)
    by_reason = {}
    for r in rows:
        by_reason.setdefault(r["exit_reason"], []).append(r)
    nedenler = {k: _blok(v) for k, v in sorted(by_reason.items(), key=lambda kv: -len(kv[1]))}
    # ÖZDEŞLİK DENETİMİ ÇIKTININ İÇİNDE: şelale bacakları toplamı net'e eşit değilse tablo
    # kendi kendine yalan söylüyor demektir (farklı paydalar, eksik satır). Sayı raporlanır ki
    # bozulma sessizce panoda durmasın.
    bacaklar = [genel["sinyal_mfe_r"], genel["geri_verilen_r"], genel["friksiyon_r"]]
    ozdeslik = (None if any(b is None for b in bacaklar) or genel["net_r"] is None
                else round(genel["sinyal_mfe_r"] + genel["geri_verilen_r"]
                           - genel["friksiyon_r"] - genel["net_r"], 4))
    # KÖTÜMSER İKİZ SÜTUN: şelalenin friksiyon bacağı, kötümser açılış varsayımıyla ne olurdu?
    # Bacaklara KARIŞMAZ (özdeşlik korunur) — yanına ayrı bir sözlük olarak konur.
    return {"genel": genel, "exit_reason": nedenler, "n": len(rows),
            "net_kotumser": net_kotumser(),
            "ozdeslik_farki": ozdeslik,
            "ozdeslik": "net_R = MFE_R + (brüt_R − MFE_R) − friksiyon_R",
            "friksiyon_kapsam": ("costs = giriş kayması + çıkış kayması + ÇIKIŞ komisyonu; giriş "
                                 "komisyonu HARİÇ (goal.yaml'da komisyon 0 olduğu sürece fark yok)"),
            "verim_tanimi": "gerçekleşen R / MFE_R — MFE<=0 işlemlerde TANIMSIZ (None)",
            "eleme": eleme}


CF_FIDELITY_FILE = "cf_fidelity.json"

# ---- CF ÜRETİM SADAKATİ DENETİMİ --------------------------------------
# DENETİM SORUSU: cf_backfill'in çıkış simülasyonu canlı çıkış kurallarını ve friksiyonu BİREBİR
# uyguluyor mu? CEVAP: HAYIR — ve bu bugüne kadar yalnız `note` alanındaki bir cümlede ("trail/
# scale-out farkı") serbest metin olarak duruyordu. Serbest metin denetlenemez: kod değişince cümle
# olduğu yerde kalır ve yanlışlığı hiçbir yerde görünmez. Aşağıdaki listeler o cümlenin MAKİNE
# OKUNUR hâlidir ve v108 testi bunları canlı kaynak koduyla karşılaştırır — beyan ile gerçek
# ayrışırsa test düşer.
#
# ÖLÇÜLEN SAPMA (canlı defter, 2026-07-28): n=89 eşleşmiş çift, corr 0.935, mean_diff_r +0.039
# (pozitif = simülasyon iyimser). Yani sapma YÖN olarak beklendiği gibi ve BÜYÜKLÜK olarak küçük;
# ama sıfır değil ve cf satırları skor IC havuzunun %96'sını oluşturuyor.
#
# NEDEN DÜZELTİLMİYOR (bilinçli, beyanlı): cf.advance'i canlı çıkış yasasına taşımak, defterdeki
# 7159 satırın YARISININ eski yasayla, yarısının yenisiyle çözülmesi demek — tek dosyada iki farklı
# çıkış rejimi, hiçbir satırda hangisinin uygulandığı yazmadan. Tutarlı hâle getirmek TÜM tarihin
# yeniden koşulmasını (saatler süren, state/'e yazan bir iş) gerektirir ve bu tur canlı worker
# koşarken yapılamaz. Kusur ÖLÇÜLÜ ve BEYANLI bırakılıyor; kapatılması ayrı bir turun işidir.
CF_SIM_EXITS = ("stop_gap", "target_gap", "stop", "target", "time_stop")
CF_MISSING_EXITS = ("trail_atr", "breakeven_lock", "chandelier", "giveback", "regime_flip",
                    "scale_out")
CF_MISSING_FRICTION = ("commission_per_share", "adv_cap", "price_impact", "notional_cap",
                       "derisk_mult")
CF_EXIT_FIDELITY_NOTE = (f"statik parantez: yalnız {'/'.join(CF_SIM_EXITS)} simüle edilir; "
                         f"canlı motorun {len(CF_MISSING_EXITS)} çıkış mekanizması "
                         f"({', '.join(CF_MISSING_EXITS)}) ve {len(CF_MISSING_FRICTION)} friksiyon "
                         f"kalemi ({', '.join(CF_MISSING_FRICTION)}) UYGULANMAZ")


def cf_fidelity() -> dict | None:
    """cf defterinin GÜVEN ÇAPASI: alınan planlar hem cf'de simüle ediliyor hem gerçekte
    yaşanıyor — o kesişimde simülasyon R'si ile gerçek R sürekli karşılaştırılır (korelasyon +
    ortalama sapma). Statik-bracket yaklaşımının canlı yasadan (trail/scale-out) sapması böylece
    ölçülü hale gelir; cf-beslemeli her kalibrasyon bu bayrağa bakarak okunmalı. Kesişim <5 → None
    (istatistik uydurulmaz). fidelity_ok: n>=10 iken korelasyon>=0.6 VE |sapma|<=0.5R."""
    import numpy as np
    from . import counterfactual as cf, sieve
    real_by_key = {}
    # BU AŞAMA CANLIDA HİÇ KURULAMADI: backtest `P00140`, canlı döngü `P-YYYY-MM-DD-TICKER` üretiyordu;
    # `pid.startswith("P-")` eski şemadaki HER satırı sessizce eledi ve simülasyonun gerçeğe uyup
    # uymadığını ölçen TEK mekanizma hiç veri görmedi. Artık biçim uyuşmazlığı sayılı bir şema hatası.
    with sieve.Sieve("cf_fidelity.gercek") as sv:
        for t in _trades():
            pid = str(t.get("plan_id") or "")
            if not pid:
                sv.drop("sema:eksik_alan:plan_id"); continue
            if not pid.startswith("P-"):
                sv.drop("sema:plan_id_biçimi:eski_şema"); continue
            if t.get("r_multiple") is None:
                sv.drop("sema:eksik_alan:r_multiple"); continue
            parts = pid.split("-")                       # P-YYYY-MM-DD-TICKER
            if len(parts) < 5:
                sv.drop("sema:plan_id_biçimi:eksik_parça"); continue
            sv.keep()
            real_by_key[("-".join(parts[1:4]), parts[4])] = float(t["r_multiple"])
    pairs = []
    with sieve.Sieve("cf_fidelity.kesisim") as sv:
        for r in cf.resolved_rows(entered_only=True):
            if not r.get("taken"):
                sv.drop("piyasa:alınmamış_plan"); continue      # meşru: o gün silahlanmadı
            key = (str(r.get("date")), str(r.get("ticker")))
            if key not in real_by_key:
                sv.drop("piyasa:gerçekte_eşleşmedi"); continue  # meşru: silahlandı ama dolmadı
            if r.get("r_multiple") is None:
                sv.drop("sema:eksik_alan:r_multiple"); continue
            sv.keep()
            pairs.append((float(r["r_multiple"]), real_by_key[key]))
    if len(pairs) < 5:
        return None
    a = np.asarray(pairs, float)
    sim, real = a[:, 0], a[:, 1]
    corr = float(np.corrcoef(sim, real)[0, 1]) if sim.std() > 0 and real.std() > 0 else None
    mean_diff = float(np.mean(sim - real))
    out = {"n": len(pairs), "corr": round(corr, 3) if corr is not None else None,
           "mean_diff_r": round(mean_diff, 3),
           "fidelity_ok": bool(len(pairs) >= 10 and corr is not None
                               and corr >= 0.6 and abs(mean_diff) <= 0.5),
           "note": "sim − gerçek; pozitif = simülasyon iyimser (trail/scale-out farkı)",
           # SADAKAT BEYANI SAYININ YANINDA: `fidelity_ok: true` tek başına "simülasyon
           # canlıyı temsil ediyor" diye okunuyordu. Oysa o bayrak yalnız KORELASYON ve ORTALAMA
           # SAPMA eşiğini söyler — hangi mekanizmaların hiç simüle EDİLMEDİĞİNİ değil. İkisi ayrı
           # sorudur ve ikincisi cevapsız kaldığı sürece birincisi yanlış güven üretir.
           "sim_cikislar": list(CF_SIM_EXITS),
           "eksik_mekanizmalar": list(CF_MISSING_EXITS),
           "eksik_friksiyon": list(CF_MISSING_FRICTION),
           "sadakat_beyani": CF_EXIT_FIDELITY_NOTE,
           # KIRILIM BURADA ANLAMSIZ: her çift zaten HEM gerçek HEM simüle. n_real/n_cf uydurmak
           # (ör. ikisine de n yazmak) paydayı ikiye katlayan bir yalan olurdu — kaynak açıkça yazılı.
           sieve.PROV_KEY: sieve.provenance(len(pairs), source=sieve.SRC_INTERSECTION,
                                            stages_=("cf_fidelity.gercek", "cf_fidelity.kesisim"))}
    store.write_json(CF_FIDELITY_FILE, out)
    return out


def near_miss_report() -> dict:
    """Eşik-altı gölge adayların karnesi: ölüm-nedeni (blocked_by) kovası
    başına adet / giriş / ortalama R. Cevapladığı soru: "hangi eşik masada para bırakıyor?" Sıfır yetki —
    yalnız rapor; bir eşik ancak bu kanıt biriktikten sonra arama+OOS kapısından geçerek değişebilir."""
    from . import counterfactual as cf, sieve
    rows = []
    with sieve.Sieve("near_miss_report.satirlar") as sv:
        for r in cf.resolved_rows(entered_only=False, include_near_miss=True):
            if not r.get("near_miss"):
                sv.drop("piyasa:eşik_altı_değil"); continue      # meşru: normal aday, bu raporun konusu değil
            sv.keep()
            rows.append(r)
    # AYRI AŞAMA — REJİM DİLİMİ: selfreview bu kanıttan "knob@rejim sondası" ÖNERİSİ üretiyor.
    # Canlıda çözülmüş satırların %70'i `regime: "?"` taşıyordu, yani öneri hangi rejime yazılacağını
    # dayandıramıyordu. Satır çıktıdan düşer ama davranış korunur: aşağıdaki muhasebede "?" kovası
    # yerinde kalır — DEĞİŞEN tek şey, o kanıtın rejime atfedilemez olduğunun artık SAYILMASI.
    with sieve.Sieve("near_miss_report.rejim_dilimi") as sv:
        for r in rows:
            if not r.get("entered"):
                sv.drop("piyasa:girilmedi"); continue            # meşru: simüle giriş dolmadı
            if r.get("r_multiple") is None:
                sv.drop("sema:eksik_alan:r_multiple"); continue
            if (r.get("regime") or "?") not in config.VALID_REGIMES:
                sv.drop("sema:rejim_damgasız"); continue
            sv.keep()
    by: dict = {}
    for r in rows:
        rg = r.get("regime") or "?"
        for b in (r.get("blocked_by") or ["diğer"]):
            d = by.setdefault(b, {"n": 0, "entered": 0, "rs": [], "by_regime": {}})
            d["n"] += 1
            if r.get("entered"):
                d["entered"] += 1
                if r.get("r_multiple") is not None:
                    d["rs"].append(float(r["r_multiple"]))
                    # REJİM DİLİMİ: selfreview bu kanıttan
                    # "knob@rejim sondası aramaya değer" ÖNERİSİ üretiyor; kanıtta rejim yoksa
                    # öneri hangi rejime yazılacağını dayandıramaz. Artık kova başına rejim kırılımı.
                    d["by_regime"].setdefault(rg, []).append(float(r["r_multiple"]))
    out = {"resolved_total": len(rows),
           # KÜNYE: bu rapor SADECE karşı-olgusal defterden beslenir — gerçek/simüle kırılımı
           # uydurulmaz, kaynak açıkça "yalnız-simüle" yazılır (n_real dürüstçe 0).
           sieve.PROV_KEY: sieve.provenance(len(rows), 0, len(rows),
                                            stages_=("near_miss_report.satirlar",
                                                     "near_miss_report.rejim_dilimi")),
           "buckets": {b: {"n": d["n"], "entered": d["entered"], "n_r": len(d["rs"]),
                           "avg_r": round(sum(d["rs"]) / len(d["rs"]), 3) if d["rs"] else None,
                           "by_regime": {rg: {"n_r": len(v), "avg_r": round(sum(v) / len(v), 3)}
                                         for rg, v in d["by_regime"].items()}}
                       for b, d in by.items()}}
    store.write_json("near_miss.json", out)
    return out


def regime_edge() -> dict:
    """cf-tarih bootstrap'ının en güçlü bulgusu: rejim başına giriş-edge'i (chop gerçekten zararlı mı,
    trend_up pozitif mi?). Çözülmüş cf (near-miss HARİÇ — silahlanacak adaylar) rejime göre gruplanır;
    n/ort.R/kazanma. Sıfır yetki: yalnız rapor + ajanın kanıt paketine besleme. regime_edge.json'a yazar."""
    from . import counterfactual as cf, sieve
    by: dict = {}
    with sieve.Sieve("regime_edge") as sv:
        for r in cf.resolved_rows(entered_only=True):          # girilen cf (near-miss varsayılan dışında)
            rg = r.get("regime") or "?"
            if r.get("r_multiple") is None:
                sv.drop("sema:eksik_alan:r_multiple"); continue
            if rg not in config.VALID_REGIMES:
                # Satır "?" kovasında GÖRÜNÜR kalır (davranış birebir korunur) ama rejim-edge'in
                # çıktısına sayılamaz: rejimsiz kanıttan rejim tavsiyesi çıkmaz. Canlıda defterin
                # %70'i böyleydi ve bu hiçbir yerde yazmıyordu.
                sv.drop("sema:rejim_damgasız")
            else:
                sv.keep()
            d = by.setdefault(rg, [])
            d.append(float(r["r_multiple"]))
    out = {rg: {"n": len(rs), "avg_r": round(sum(rs) / len(rs), 3),
                "win_rate": round(sum(1 for x in rs if x > 0) / len(rs), 3)}
           for rg, rs in by.items() if rs}
    # KÜNYE `_kaynak` altında ve `n_total` adıyla: bu artefaktın KÖKÜ "rejim adı → istatistik"
    # haritasıdır. Onu okuyan iki tüketici (watchdog ölçülen-edge dedektörü, hermes kanıt paketi)
    # `n` alanı olan her sözlüğü REJİM sanıyor — künyede `n` olsaydı sahte bir rejim gibi sayılır ve
    # watchdog'un "her rejimde edge negatif" alarmını paydayı şişirerek SUSTURABİLİRDİ.
    out[sieve.PROV_KEY] = sieve.provenance(sum(len(rs) for rs in by.values()),
                                           0, sum(len(rs) for rs in by.values()),
                                           stages_=("regime_edge",))
    store.write_json("regime_edge.json", out)
    return out


# ---- EDGE HÜKMÜ: BEŞ ölçütün TEK yazılı kararı --------------
# NEDEN: pano dört ölçütü yan yana gösteriyordu ama "peki KENAR VAR MI?" sorusunu okurun kafasında
# birleştirmesini bekliyordu. Dört ayrı sayıdan hüküm çıkarmak her bakışta yeniden yapılan, yazılı
# olmayan ve bu yüzden HER SEFERİNDE FARKLI çıkabilen bir işlemdir. Eşikler burada, kodda, tek yerde
# durur; hüküm cümlesi de onlardan türer.
#
# ÜÇÜNCÜ DURUM ZORUNLUDUR. Bir ölçüt "geçti/kaldı" ikilisine sıkıştırılırsa ÖLÇÜLMEMİŞ olan sessizce
# "kaldı" sayılır — ve dört ölçütün üçü ölçülemezken pano kırmızı yanıp "edge yok" der; oysa doğru
# cevap "henüz bilmiyoruz"dur. Sabır ile başarısızlık aynı renge boyanamaz (UYDURMA YASAĞI).
# EŞİKLER — HEPSİ ADLANDIRILMIŞ SABİT, HEPSİ GEREKÇELİ.
# v1 (07-27) eşikleri havuzlanmış IC gövdesine göre seçilmişti; bu tur 1. ölçütü GERÇEK katmana
# taşıdığı için taban da yeniden ayarlandı — aynı eşiği 2100 satırlık sim havuzuna ve 95 satırlık
# gerçek deftere uygulamak, iki farklı büyüklüğü tek isimle yönetmek olurdu.
EDGE_IC_MIN = 0.03          # gerçek katman rank-IC: friksiyon sonrası anlamlı bir seçicilik için
                            # gereken asgari eğim. v1'de 0.05'ti; o eşik havuzlanmış (sim ağırlıklı)
                            # gövdeye göre seçilmişti. Gerçek defter aylar boyunca yüzlerce satıra
                            # ulaşmayacağı için 0.05, ölçütü fiilen ulaşılamaz kılardı — kuzey
                            # yıldızı hiç yanmayan bir lamba olurdu.
EDGE_IC_N_MIN = 60          # GERÇEK katman satır sayısı (v1: 100, havuz satırı). Gerçek işlemler
                            # ayda ~10-15 birikiyor; 60 yaklaşık altı aylık canlı defter demektir ve
                            # rank-IC'nin işaretinin tesadüf olmadığını söylemeye yeten en küçük
                            # taban. Altında hüküm ÖLÇÜLEMEDİ'dir — negatif bir IC bile "kenar yok"
                            # değil "henüz okunmuyor" anlamına gelir.
PRED_HIT_N_MIN = 10         # tahmin↔gerçekleşen çifti (v1: 5). 5 çiftte 3 isabet %60 yapar ve bu
                            # yazı-turadan ayırt edilemez; 10 çift, oranın en azından bir yöne
                            # işaret etmesini sağlayan ilk taban.
PRED_HIT_RATE_MIN = 0.6     # işaret isabeti: yazı-turadan (0.5) anlamlıca yukarısı (v1'den aynen)
REGIME_N_MIN = 30           # bir rejimin edge iddiası için en az satır (v1: 100). 100, cf defterinin
                            # rejim damgası taşıyan dilimi için fiilen ulaşılamazdı (satırların
                            # çoğunluğu rejimsiz eleniyor) ve ölçüt kalıcı olarak ölçülemedi'de
                            # takılıydı. 30, IC_MIN_SAMPLE ile aynı taban — aynı depoda "bir istatistik
                            # için en az kaç satır" sorusunun iki farklı cevabı olmasın diye.
REGIME_AVG_R_MIN = 0.0      # rejim başına ortalama R — karşılaştırma KESİN BÜYÜKTÜR (`> MIN`), yani
                            # "o rejimde pozitif beklenti var". v1'de 0.05'ti; ama friksiyon zaten
                            # gerçekleşen R'nin içinde olduğu için sıfırın üstü kendi başına anlamlı
                            # bir iddiadır ve ikinci bir tampon eklemek eşiği gerekçesiz sertleştirirdi.


EDGE_DURUM_ADI = {"gecti": "SAGLANDI", "kaldi": "SAGLANMADI", "olculemedi": "OLCULEMEDI",
                  "zayif": "ZAYIF"}


# ---- BEŞİNCİ ÖLÇÜT: KUYRUK -----------------------------------------
# NEDEN BEŞİNCİ BİR ÖLÇÜT. Dört ölçütün dördü de "seçim doğru mu?" sorusunun bir türevi: skor
# sonucu öngörüyor mu, SPY'ı geçiyor mu, tahmin tutuyor mu, hangi rejimde tutuyor. Hiçbiri
# "SERMAYE HAYATTA KALIR MI?" sorusunu sormuyordu — ve bir momentum sistemini öldüren şey ortalama
# değil KUYRUKtur. Kapı yasası kuyruğu 2026-07-22'den beri VETO olarak taşıyor (VaR/CVaR
# kötüleşmesi adayı reddeder); kuzey yıldızı ise onu HİÇ görmüyordu. Aynı depoda kuyruğun kapıda
# veto, hükümde yok olması, iki farklı risk iştahı beyan etmekti.
#
# ÖLÇÜT İKİ BACAKLIDIR VE İKİSİ BİRDEN GEREKİR ("VE", "VEYA" DEĞİL): gerçekleşen maksimum düşüş
# YOL riskini ölçer (sıralanmış kayıpların bileşik etkisi), işlem-R CVaR'ı ise BİRİM riskini
# (tek işlemin en kötü %5'i risk birimini aşıyor mu). Bir sistem stop disiplinini kusursuz
# uygulayıp (CVaR temiz) yine de üst üste kayıplarla %20 düşebilir; ya da düşüşü küçük tutup tek
# bir boşlukta 4R yiyebilir. İki soru, iki cevap; biri diğerini affedemez.
EDGE_TAIL_N_MIN = 40        # kuyruk hükmü için asgari kapanmış işlem. %5'lik dilim n=40'ta 2
                            # işlemdir — bir CVaR'ın "en kötülerin ortalaması" olabilmesi için
                            # gereken en küçük taban. Altında hüküm OLCULEMEDI'dir: n=20'de tek
                            # kötü işlem CVaR'ı tek başına belirler ve o bir dağılım değil bir
                            # anekdottur. (EDGE_IC_N_MIN 60'tan KÜÇÜK bilinçli: IC bir EĞİM
                            # tahminidir ve daha çok satır ister; kuyruk bir UÇ değeridir.)
EDGE_MAXDD_MAX = 0.16       # gerçekleşen maksimum düşüş tavanı. `goal.yaml`ın `max_drawdown`
                            # değeriyle BİREBİR AYNI — çünkü o sayı operatörün yazılı BAŞARISIZLIK
                            # SINIRIdır ve kuzey yıldızının ikinci bir risk iştahı icat etmesi,
                            # aynı depoda iki farklı "kabul edilebilir düşüş" tanımı doğururdu.
                            # Sabit burada TEKRAR yazılır (goal'dan okunmaz) ki hüküm eşikleri
                            # diğer dördüyle AYNI yerde denetlenebilsin; ikisinin eşitliği testle
                            # çivilenir, yani sürüklenme imkânsızdır.
EDGE_CVAR5_MIN_R = -1.5     # işlem-R dağılımının en kötü %5'inin ORTALAMASI için taban (işaret
                            # GETİRİ yönünde: negatif = kayıp; "≥ taban" = "bundan daha kötü
                            # değil"). GEREKÇE ÖLÇÜMDEN DEĞİL YASADAN TÜRETİLİR: pozisyon
                            # boyutlayıcı adedi `risk_dolar / (giriş − stop)` diye kurar, yani
                            # stopa uyulan bir çıkış TAM −1.0R'dir. −1.0'ın ötesi yalnız iki
                            # kanaldan gelir: stopun ÜSTÜNDEN geçen gece boşluğu ve stop
                            # dolumundaki kayma. −1.5R, risk biriminin YARISI kadar boşluk
                            # hasarına izin verir; bundan kötüsü "stop bir stop değil" demektir ve
                            # o hâlde 1R'lik boyutlandırma yasasının söz verdiği şey artık yoktur.


# ---- M2M SERİSİNİN YAZARI — ADIYLA ------------------------------------------------------------
# ÇAPA SEMBOLDÜR, SATIR DEĞİL (depo yasası): eğrinin tek kadanslı yazarı `loop`un
# `_persist_equity_point` fonksiyonudur (WP2-D bacak-2). Ad burada DİZGE olarak durur çünkü
# `analytics` modül düzeyinde `loop`u içe aktaramaz (loop ağır bağımlılıkları — pandas, adapters —
# çeker ve analytics'i kendi içinden LAZY olarak çağırır: modül düzeyinde çift yönlü bağ olurdu).
# Adın bayatlaması `test_karne_veri_hatti_v293`te çivilidir (fonksiyon VAR mı diye bakar).
EGRI_KADANSLI_YAZAR = "loop._persist_equity_point"
# Yazarın kendi düşüş olayları (`loop._persist_equity_point`ın obs adları). Bu iki ad ile
# "olay YOK" hâli arasındaki fark, iki AYRI arıza hipotezini ayırır.
EGRI_YAZAR_OLAYLARI = ("equity_point_skipped", "equity_point_failed")
EGRI_YAZAR_OLAY_TARAMA = 2000   # olay defterinde geriye BAKILACAK satır TAVANI. NE YAPMADIĞI
                                # BEYANLI: bu sayı okuma MALİYETİNİ düşürmez — `store.read_jsonl`
                                # dosya arka ucunda defterin tamamını ayrıştırıp kuyruğu keser
                                # (ölçüldü, bkz. `_egri_yazar_kaniti` maliyet beyanı). Yalnız
                                # "en son ne oldu" penceresini sınırlar; teşhis bir tarihçe değil.


def _gecikme_gun(seri_son: str | None, defter_seansi: str | None) -> int | None:
    """Seri ile kitap seansı arasındaki TAKVİM GÜNÜ farkı; ölçülemezse None (0 DEĞİL).

    NEDEN GÜN SAYISI: "kapsamıyor" ikili bir bayraktır ve "bugün akşam kapanış henüz yazılmadı"
    (1 gün) ile "yazar haftalardır koşmuyor" (30 gün) arasındaki farkı GİZLER. İkisi aynı bayrağa
    düşünce fiş her koşuda aynı cümleyle doğuyor, aciliyet okunamıyordu.

    Seri kitabın İLERİSİNDEyse gecikme 0'dır (negatif bir gecikme bir gecikme değildir); tarih
    ayrıştırılamıyorsa None — dedektörün körlüğü sayıya çevrilmez."""
    import datetime as _dt
    try:
        a = _dt.date.fromisoformat(str(seri_son)[:10])
        b = _dt.date.fromisoformat(str(defter_seansi)[:10])
    except (TypeError, ValueError):  # sessiz-yutma: DEĞİL — None DÖNÜŞÜN KENDİSİ cevap ("gecikme ölçülemedi") ve çağıran onu çıktıya aynen basar; 0 yazmak "ölçtük, gecikme yok" demek olurdu
        return None
    return max(0, (b - a).days)


def _egri_yazar_kaniti() -> dict:
    """Seri kitabı kapsamıyorken TEK soruyu cevaplar: kadanslı yazar KOŞTU da mı reddedildi, yoksa
    HİÇ Mİ KOŞMADI?

    NEDEN GEREKLİ. Bayat seri iki TAMAMEN FARKLI arızanın aynı görüntüsüdür:
      (a) yazar koştu ve kendi kapılarından birinde reddedildi (ölçülemeyen öz sermaye, okunamayan
          beyanlı ofset, geriye yazım reddi) → düzeltme YAZARIN GİRDİLERİNDEDİR;
      (b) yazar hiç koşmadı (günlük döngü tamamlanmıyor / o sürüm dağıtılmamış) → düzeltme
          ÇALIŞTIRMA KATMANINDADIR.
    Ayrım yapılmadan fiş "seri bayat" diyor ve her koşuda yeniden doğuyordu; iki hipotez arasında
    seçim yapmak için canlıya bakmak gerekiyordu.

    KANIT KAYNAĞI: yazarın KENDİ düşüş olayları (`EGRI_YAZAR_OLAYLARI`). Yazar başarıyla yazdığında
    olay basmaz — ama o hâlde seri zaten kitabı kapsardı, yani bu fonksiyon hiç çağrılmaz. Bu
    yüzden "olay yok" burada DÜRÜSTÇE (b)'yi işaret eder ve `durum` bunu ADIYLA söyler.

    SAF OKUMA, HÜKÜM YOK: dönüş hiçbir eşiğe girmez, hiçbir sayacı oynatmaz; yalnız `_realized_
    drawdown`ın teşhis alanına düşer.

    MALİYET BEYANI (ÖLÇÜLDÜ, tahmin değil — 2026-08-25, yerel 9 MB `events.jsonl`): `obs.recent`
    dosya arka ucunda defterin TAMAMINI ayrıştırır, sonra kuyruğu keser — soğuk 119 ms, sıcak
    45 ms. `result_verdict` ve `edge_verdict` `_realized_drawdown`ı ayrı ayrı çağırdığı için tek
    bir /api/diagnostics turunda bu bedel İKİ KEZ ödenir (~90 ms) ve YALNIZ kusur sürdüğü sürece
    ödenir (seri kitabı kapsar kapsamaz bu fonksiyon hiç çağrılmaz). Önbellek BİLEREK eklenmedi:
    telemetri turu zaten 12 üretici koşuyor, 90 ms orada gürültüdür; bir önbellek ise yeni bir
    bayatlık sınıfı açardı ve bu dosyanın tam da kapatmaya çalıştığı kusur BAYATLIKTIR."""
    from . import obs
    try:
        satirlar = [r for r in obs.recent(EGRI_YAZAR_OLAY_TARAMA)
                    if isinstance(r, dict) and r.get("event") in EGRI_YAZAR_OLAYLARI]
    except Exception as e:
        # YASA 4: olay defteri okunamazsa "yazar hiç koşmamış" DENEMEZ — o, ölçülmemiş bir iddia
        # olurdu ve teşhisi tam ters yöne çevirirdi. Düşüş adıyla döner.
        return {"durum": "olculemedi", "son_olay": None, "son_neden": None, "son_ts": None,
                "taranan": 0,
                "neden": (f"olay defteri okunamadı ({type(e).__name__}: {e}) — yazarın koşup "
                          f"koşmadığı ÖLÇÜLEMEDİ ('hiç koşmadı' SAYILMAZ)")}
    if not satirlar:
        return {"durum": "olay_yok", "son_olay": None, "son_neden": None, "son_ts": None,
                "taranan": EGRI_YAZAR_OLAY_TARAMA,
                "neden": (f"son {EGRI_YAZAR_OLAY_TARAMA} olayda `{EGRI_KADANSLI_YAZAR}`ın TEK bir "
                          f"düşüş olayı ({'/'.join(EGRI_YAZAR_OLAYLARI)}) yok — yazar denenip "
                          f"reddedilmiş DEĞİL, hiç KOŞMAMIŞ görünüyor: günlük döngü o seansı "
                          f"tamamlamıyor ya da yazarın bulunduğu sürüm koşmuyor")}
    son = satirlar[-1]
    return {"durum": "olay_var", "son_olay": son.get("event"),
            # İki olay nedeni İKİ AYRI alanda taşır (`neden` vs `error`); ikisini tek yerde
            # toplamak, okuyucunun hangi olayı okuduğuna göre dal açmasını gereksiz kılar.
            "son_neden": son.get("neden") or son.get("error"),
            "son_ts": son.get("ts"), "taranan": EGRI_YAZAR_OLAY_TARAMA,
            "neden": (f"`{EGRI_KADANSLI_YAZAR}` KOŞTU ve nokta yazılMADI ({son.get('event')}) — "
                      f"düzeltme yazarın GİRDİLERİNDE, çalıştırma katmanında değil")}


def _realized_drawdown() -> dict:
    """Gerçekleşen maksimum düşüş — KAPANMIŞ İŞLEM eğrisi ile GÜNLÜK piyasaya-göre eğrinin
    KÖTÜ OLANI. `score.score_detail`in `mtm_equity` yasası ile birebir aynı kural:
    yalnız kapanmış işlemlere bakan bir eğri, açık pozisyonların düşüşünü GİZLER.

    CANLI ÖLÇÜM BU AYRIMIN NE KADAR ÖNEMLİ OLDUĞUNU GÖSTERDİ (2026-07-30): kapanmış-işlem eğrisi
    %5,70 diyor, günlük eğri %8,04. Yani kapanmış eğri tek başına okunsaydı hem SONUÇ HÜKMÜ hem
    EDGE'in beşinci ölçütü eşiği GEÇMİŞ görünürdü — düşüşün kendisi hiç küçülmemişken.

    İKİ HÜKÜM TEK KAYNAKTAN OKUR: `result_verdict` (maks düşüş ölçütü) ve `edge_verdict` (kuyruk
    ölçütünün ilk bacağı) aynı fonksiyonu çağırır. İki ayrı hesap olsaydı iki hüküm aynı olgu
    hakkında farklı şey söyleyebilirdi.

    ---- SERİ, KAPSADIĞI DÖNEMLE ETİKETLENİR -----------------------------------
    ÖLÇÜLEN KUSUR (canlı A1 2026-08-08 21:52Z):
    `equity_curve.json`ın son noktası **2026-07-20 / 94.457,91$** — yani 19 gün geride VE 1 Ağustos
    sermaye resetinden ÖNCEKİ tabanda. Bu bir arıza değil TASARIM: eğrinin tek canlı yazarları
    `run.replay_seed` / `sermaye.uygula` / `mutation`dır ve `ledgerstamp.seed_boundary()` onu
    DOĞRU okur — son nokta TOHUM SINIRIDIR. Kusur İKİNCİ TÜKETİCİDEYDİ: burası aynı noktaları
    "GÜNCEL piyasaya-göre eğri" sanıp TOHUM döneminin %8,04'ünü CANLI dönemin m2m düşüşü diye
    hükme sokuyordu. Yani canlı kâğıt döneminin (2026-07-21 →) m2m düşüşü hükümde HİÇ yokken,
    tohum döneminin düşüşü güncelmiş gibi sayılıyordu.

    MEKANİZMA DÜZELTMESİ (bu paragrafın eski hâli YANLIŞ bir kapı anlatıyordu): %8,04 bugünkü
    `EDGE_MAXDD_MAX`/`RESULT_MAXDD_MAX`ın (0,16 — `goal.max_drawdown` ile birebir aynı sayı)
    ALTINDADIR, yani tavanı AŞARAK hiçbir kilidi düşürmez; eski metnin dayandığı 0,08 tavanı
    bugün yürürlükte değildir (0,08 → 0,16 taşıması operatör kararıdır, 2026-08-13; eşitliği
    `test_hafta3a_v119` ve `test_orgu2_v103` çiviler). Bayat serinin GERÇEK hasarı eşik aşımı
    değil, HAK EDİLMEMİŞ BİR "GEÇTİ"dir: tohum dönemine ait düşüş güncel sayılınca m2m bacağı
    ÖLÇÜLMÜŞ görünür ve `edge_verdict`in kuyruk ölçütü ile `result_verdict`in düşüş ölçütü
    tavanın altında kalan bir sayıyla "gecti" yazar. Düzeltmeden sonra o seri hükümden çekilir,
    bacak ÖLÇÜLEMEDİ olur, `max_dd` bir ALT SINIRA döner (`max_dd_alt_sinir=True`) ve iki hüküm
    de "gecti" yerine "olculemedi" verir.

    DÜZELTME İLKESİ — BU TURDA EŞİĞE DOKUNULMADI: düzeltme `EDGE_MAXDD_MAX`/`RESULT_MAXDD_MAX`ın
    bir hanesini bile oynatmadı (sonraki 0,16 kararı AYRI bir operatör kararıdır, bu mekanizmanın
    parçası değil). Değişen tek şey, serinin KAPSADIĞI DÖNEMİN ölçülmesi:
      * seri kitabın işlediği seansı KAPSIYORSA → m2m bacağı ölçülür, davranış BİREBİR eskisi gibi;
      * KAPSAMIYORSA → m2m bacağı **ÖLÇÜLEMEDİ**'dir. Bayat seriyle "kötüsü" HESAPLANMAZ, ama
        görülen sayı da GİZLENMEZ: `bayat_seri_dd` alanında ADIYLA durur (değeri saklamak hükmü
        denetlenemez yapardı — `_olcut`un aynı yasası);
      * kitabın seansı OKUNAMIYORSA (analitik fikstürleri, defterisiz sandbox) dönem kapsaması
        ÖLÇÜLEMEZ ve seri bayat SAYILMAZ — kuramadığımız bir dönemin dışında olmakla suçlamak,
        dedektörün kendi körlüğünü bulguya çevirmek olurdu.
    `max_dd` m2m bacağı ölçülemediğinde bir **ALT SINIRDIR** (`max_dd_alt_sinir=True`): ölçülmeyen
    bacak 0 SAYILMAZ, "bilinmiyor" sayılır — ve tüketiciler (`edge_verdict`, `result_verdict`)
    eşiği geçen bir ALT SINIRI "geçti" diye okuyamaz (bkz. oradaki hüküm kuralı).

    DÖNEMİN REFERANSI KİTAPTIR (`portfolio.last_date`), defter değil: `trades.jsonl`in son kapanış
    tarihi bir işlemin kapandığı gündür, motorun BUGÜN hangi seansta olduğunu söylemez; eğrinin
    kapsaması gereken şey ikincisidir.

    ---- TEŞHİS ÜÇLÜSÜ (2026-08-25; fiş 7/8'in KÖKÜ) ---------------------------
    ÖLÇÜLEN KUSUR OKUMA DEĞİL, TEŞHİSTİ. Yukarıdaki kapsama kuralı DOĞRU çalışıyor (kanıt: canlı
    karne kopyasında tek bir kadanslı nokta düşünce `m2m_durum` `donem_disi` → `olculdu` oluyor ve
    İKİ hüküm birden `olculemedi`den çıkıyor — `test_karne_veri_hatti_v293` bunu uçtan uca çiviler).
    Kusur, çıktının "seri bayat" deyip ÜÇ soruyu cevaplamamasıydı ve bu yüzden aynı kalem her
    koşuda yeniden fişleniyor, hiçbir koşuda aksiyona çevrilemiyordu:
      * `gecikme_gun` — kaç gün geride? "Bugünün kapanışı henüz yazılmadı" (1) ile "yazar
        haftalardır koşmuyor" (30) tek bir ikili bayrağa düşüyordu.
      * `yazar` — seriyi KİM yazmalı? Tek kadanslı yazar `EGRI_KADANSLI_YAZAR`dır; adı çıktıda
        durur ki okuyucu kusuru TÜKETİCİDE (burada) aramasın.
      * `yazar_kanit` — yazar KOŞUP reddedildi mi (girdi arızası), yoksa HİÇ mi koşmadı
        (çalıştırma arızası)? İki hipotez `_egri_yazar_kaniti` ile ayrışır; YALNIZ `kapsamiyor`
        hâlinde okunur (kusursuz turda olay defteri hiç taranmaz).
    HİÇBİR EŞİĞE VE HİÇBİR HÜKME DOKUNULMADI: üçü de rapor alanıdır, `max_dd`/`max_dd_alt_sinir`
    aynen eskisi gibi hesaplanır."""
    trades = _trades()
    kapali = score_mod.max_drawdown(score_mod.equity_curve(trades)) if trades else None
    gunluk, n_gun, seri_donem = None, 0, None
    m2m_durum, m2m_neden = "yok", "günlük piyasaya-göre eğri diskte yok"
    try:
        pts = (store.read_json("equity_curve.json", None) or {}).get("points") or []
        seri = [float(v) for _, v in pts]
        n_gun = len(seri)
        if pts:
            seri_donem = [str(pts[0][0]), str(pts[-1][0])]
        if len(seri) >= 2:
            gunluk = score_mod.max_drawdown(seri)
            m2m_durum, m2m_neden = "olculdu", ""
        elif pts:
            m2m_neden = "eğride 2'den az nokta var — düşüş hesaplanamaz"
    except (TypeError, ValueError, KeyError) as e:
        # YASA 4: günlük eğri okunamazsa düşüş SESSİZCE küçülür (yalnız kapanmış eğri kalır) ve
        # her iki hüküm de hak etmediği bir "SAGLANDI" alabilir. Davranış aynı (kapanmışa düş),
        # ama neden görünür.
        from . import obs
        obs.warn("mtm_curve_unreadable", error=f"{type(e).__name__}: {e}",
                 detail="günlük piyasaya-göre eğri okunamadı — maks düşüş yalnız kapanmış "
                        "işlemlerden ölçüldü (açık pozisyon düşüşü GİZLİ kalır)")
        m2m_durum, m2m_neden = "okunamadi", f"eğri okunamadı: {type(e).__name__}"

    # ---- DÖNEM KAPSAMASI ----------------------------------------------------------------------
    defter_seansi = str((store.read_json("portfolio.json", {}) or {}).get("last_date") or "") or None
    bayat_seri_dd, donem_kapsami = None, "olculemedi"
    if seri_donem and defter_seansi:
        donem_kapsami = "kapsiyor" if seri_donem[1] >= defter_seansi else "kapsamiyor"
    gecikme_gun = _gecikme_gun(seri_donem[1] if seri_donem else None, defter_seansi)
    if donem_kapsami == "kapsamiyor" and gunluk is not None:
        bayat_seri_dd = round(gunluk, 4)
        gunluk = None
        m2m_durum = "donem_disi"
        m2m_neden = (f"seri {seri_donem[0]} → {seri_donem[1]} dönemini kapsıyor; kitap "
                     f"{defter_seansi} seansını işledi — CANLI döneme ait m2m serisi YOK, "
                     f"bayat seriyle 'kötüsü' hesaplanmaz (o serinin düşüşü: {bayat_seri_dd})"
                     + (f"; gecikme {gecikme_gun} gün" if gecikme_gun is not None else ""))
    # TEŞHİS YALNIZ KUSUR HÂLİNDE KONUŞUR (ve olay defterini yalnız o hâlde okur — kusursuz turda
    # ödenmeyecek bir bedel). `kapsamiyor` bir tüketici kusuru DEĞİL bir ÜRETİCİ boşluğudur ve bu
    # alan onu isimlendirir: yazar KOŞUP reddedildi mi, yoksa HİÇ mi koşmadı?
    yazar_kanit = _egri_yazar_kaniti() if donem_kapsami == "kapsamiyor" else None

    adaylar = [x for x in (kapali, gunluk) if x is not None]
    kaynak = ("kapanmış işlem eğrisi ile günlük piyasaya-göre eğrinin KÖTÜ olanı"
              if gunluk is not None else
              ("yalnız kapanmış işlem eğrisi — günlük eğri okunamadı" if m2m_durum == "okunamadi"
               else f"yalnız kapanmış işlem eğrisi — günlük m2m bacağı ÖLÇÜLEMEDİ ({m2m_neden})"))
    return {"max_dd": None if not adaylar else round(max(adaylar), 4),
            "kapali_islem_dd": None if kapali is None else round(kapali, 4),
            "gunluk_m2m_dd": None if gunluk is None else round(gunluk, 4),
            "n_islem": len(trades), "n_gun": n_gun,
            # ÖLÇÜLEMEYEN BACAK 0 DEĞİL: `max_dd` o hâlde bir ALT SINIRDIR ve tüketiciler bunu
            # okumak ZORUNDADIR — eşiği geçen bir alt sınır "geçti" hükmü doğurmaz.
            # KAPSAM BEYANI (bilinçli, dar): bayrak YALNIZ `donem_dısı` hâlinde kalkar — yani
            # VAR OLAN bir seri YANLIŞ DÖNEMİ anlatırken. "Eğri hiç yok" ve "eğri okunamadı"
            # hâlleri AYNI SINIFTAN olsa da bu turda DEĞİŞTİRİLMEDİ: ikisi de zaten kendi
            # gerekçeleriyle beyanlı (YASA 4 uyarısı + `kaynak` metni) ve bugünkü hükümlerin
            # tabanı onların üstünde duruyor; bayrağı oraya genişletmek bu kusuru
            # değil, hüküm tabanının tamamını oynatırdı. Ölçülen kusur BAYAT SERİDİR.
            "max_dd_alt_sinir": bool(m2m_durum == "donem_disi"),
            "m2m_durum": m2m_durum, "m2m_neden": m2m_neden,
            "seri_donem": seri_donem, "defter_seansi": defter_seansi,
            "donem_kapsami": donem_kapsami, "bayat_seri_dd": bayat_seri_dd,
            # ---- TEŞHİS ÜÇLÜSÜ (2026-08-25, fiş 7/8) --------------------------------------------
            # Fiş her koşuda yeniden doğuyordu çünkü çıktı "seri bayat" diyor ama ÜÇ soruyu
            # cevaplamıyordu: kaç gün geride · seriyi KİM yazmalı · yazar deneyip mi reddedildi.
            # Üçü olmadan kalem aksiyona çevrilemiyor, aynı cümleyle yeniden fişleniyordu.
            "gecikme_gun": gecikme_gun, "yazar": EGRI_KADANSLI_YAZAR,
            "yazar_kanit": yazar_kanit,
            "kaynak": kaynak}


# ---- BLOK BOOTSTRAP ----------------------------------------------------------------
# NEDEN BLOK, NEDEN IID DEĞİL. İşlem sonuçları bağımsız değildir: aynı rejimde açılan pozisyonlar
# birlikte kazanır, birlikte kaybeder (kayıp SERİLERİ). IID yeniden örnekleme o bağımlılığı kırar
# ve aralığı SİSTEMATİK OLARAK DARALTIR — yani ölçülmemiş bir kesinlik yazar. CANLI ÖLÇÜM
# (2026-07-30, n=95): işlem başına ortalama $ için IID aralık [−116,86, −0,00] sıfırı KIL PAYI
# dışarıda bırakıyor, blok aralığı [−137,75, +14,53] ise sıfırı İÇERİYOR. Yani IID okuma
# "kaybettiğimiz kanıtlandı" derdi; blok okuma dürüst cevabı verir: n=95'te henüz kanıtlanmadı.
#
# KAPSAM BEYANI: bu, "genel blok-bootstrap CI standardı" kalemi DEĞİLDİR.
# Burada YALNIZ dolar beklentisi için bir aralık üretilir; `benchmark_relative` kendi IID
# işlem-düzeyi bootstrap'ında (BENCH_BOOTSTRAP_*) bilinçli olarak DEĞİŞMEDEN bırakıldı, çünkü onun
# ölçtüğü büyüklük (toplam getiri farkı) ve o alanın tüketicileri bu turun kapsamı dışında ve
# sessizce değiştirilmesi mevcut hükmü (2. ölçüt) haber vermeden kaydırırdı.
#
# BU KALEM NEREYE İNDİ: genel standart `olcum_araclari.blok_bootstrap_ci`dir (MOVING blok,
# n^(1/3) kuralı, getiri serileri için) ve İLERİYE dönük ölçüm şablonlarını bağlar. AŞAĞIDAKİ
# HESAP ONA DEVREDİLMEDİ ve bir hanesi bile oynatılmadı: burası CIRCULAR blok, blok=5 İŞLEM ekseni
# ve YAYIMLANMIŞ hükümlerin tabanı; ortak bir gövdeye indirgemek `result_verdict`in aralıklarını
# habersiz kaydırırdı. İki uygulama, iki eksen, iki yazılı gerekçe — kopya değil, sözleşme farkı.
BOOT_BLOCK_TRADES = 5   # blok uzunluğu, İŞLEM cinsinden. `score.tail_risk`ın circular-block
                        # bootstrap'ı da 5 kullanıyor: aynı depoda "işlem ekseninde bağımlılık
                        # bloğu ne kadar uzun?" sorusunun iki farklı cevabı olmasın.
BOOT_N = 10_000         # tekrar sayısı. `score.TAIL_SIMS` 20.000, `BENCH_BOOTSTRAP_N` 2.000;
                        # 10.000'de %2,5/%97,5 yüzdelikleri tohumdan tohuma ~$1 oynar (marjın
                        # yanında yok) ve maliyet /api/diagnostics anketinde ~10 ms.
BOOT_SEED = 11          # sabit tohum: aynı defter aynı aralığı verir (tekrarlanabilirlik).


def _blok_bootstrap_ci(vals: list, seviye: float = 0.95) -> dict | None:
    """Ortalamanın blok-bootstrap güven aralığı. CIRCULAR block: bloklar dizinin sonundan başına
    sarılır, böylece her gözlem eşit olasılıkla örneklenir (uçlardaki gözlemleri eksik örneklemek
    aralığı kaydırırdı). None: 2'den az gözlem."""
    import numpy as np
    x = np.array([float(v) for v in vals], dtype=float)
    n = x.size
    if n < 2:
        return None
    blok = min(BOOT_BLOCK_TRADES, n)
    n_blok = -(-n // blok)                                   # ceil(n / blok)
    rng = np.random.default_rng(BOOT_SEED)
    bas = (rng.random((BOOT_N, n_blok)) * n).astype(np.int64)
    idx = (bas[:, :, None] + np.arange(blok)[None, None, :]) % n
    ort = x[idx].reshape(BOOT_N, n_blok * blok)[:, :n].mean(axis=1)
    alt = (1.0 - seviye) / 2.0 * 100.0
    lo, hi = np.percentile(ort, [alt, 100.0 - alt])
    return {"lo": round(float(lo), 2), "hi": round(float(hi), 2), "seviye": seviye,
            "n": int(n), "blok": int(blok), "B": BOOT_N,
            "yontem": f"circular blok bootstrap (blok={blok} işlem, B={BOOT_N}, tohum sabit)",
            "sifiri_disliyor": bool(lo > 0 or hi < 0)}


def _cvar(vals: list, yuzde: float = 5.0) -> dict | None:
    """Alt `yuzde`'lik dilimin ORTALAMASI (expected shortfall), İŞARET GETİRİ YÖNÜNDE.

    DİKKAT — İŞARET SÖZLEŞMESİ: `score.tail_risk` VaR/CVaR'ı POZİTİF KAYIP BÜYÜKLÜĞÜ olarak
    raporlar (ve 20 işlemlik bir UFUK üzerinde, Monte Carlo ile). Buradaki hesap AYRI bir
    büyüklüktür: TEK işlemin gerçekleşen R dağılımının alt kuyruğu, getiri işaretiyle (negatif =
    kayıp). İki sözleşmeyi aynı ada sıkıştırmak bir işaret hatasıyla vetoyu tersine çevirebilirdi;
    bu yüzden alan adı `cvar5_r` ve `isaret` alanı sözleşmeyi çıktının İÇİNDE söyler."""
    import numpy as np
    x = np.array([float(v) for v in vals], dtype=float)
    if x.size < 2:
        return None
    q = float(np.percentile(x, yuzde))
    kuyruk = x[x <= q]
    return {"cvar5_r": round(float(kuyruk.mean()), 4) if kuyruk.size else round(q, 4),
            "var5_r": round(q, 4), "kuyruk_n": int(kuyruk.size), "n": int(x.size),
            "en_kotu_r": round(float(x.min()), 4), "yuzde": yuzde,
            "isaret": "getiri yönünde (negatif = kayıp) — score.tail_risk'in POZİTİF kayıp "
                      "büyüklüğü sözleşmesinden AYRI"}


# ---- DÖRDÜNCÜ DURUM: ZAYIF -----------------------------------------
# NEDEN. 2026-07-29 sabahı 1. ölçüt "SAGLANDI" yanıyordu: gerçek katman IC 0.0492, eşik 0.03. Aynı
# payload'ın iki alan ötesinde `anlamli: False` yazıyordu — çünkü n=95'te i.i.d. güven aralığı
# ±0.20 civarı ve 0.0492 o aralığın içinde, yani yazı-turadan AYIRT EDİLEMEZ. Kuzey yıldızı
# gürültüyle yanamaz: eşiği geçmek bir İDDİA, anlamlılık ise o iddianın ölçümden mi tesadüften mi
# geldiğinin cevabıdır. İkisi tek duruma sıkıştırılırsa "SAGLANDI" kelimesi, sistemin en pahalı
# kararlarının (rafineri yatırımı, sermaye artırımı) dayanağı olarak, ölçülmemiş bir kesinlik
# taşır. Bu yüzden SAGLANDI artık İKİSİNİ BİRDEN ister; eşiği geçip anlamlılığı geçemeyen ölçüt
# ZAYIF'tır — kaldı DEĞİL (değer gerçekten eşiğin üstünde), sağlandı da DEĞİL.
#
# UYDURMA YASAĞI SINIRI: bu mantık YALNIZ anlamlılık HESABI OLAN ölçütlere uygulanır. Bugün bunlar
# 1. ölçüt (`score_calibration.katmanlar.gercek.anlamli`, i.i.d. SE) ve 2. ölçüttür
# (`benchmark_relative.anlamli`, bootstrap aralığı sıfırı dışarıda bırakıyor mu). 3. ölçütün
# (tahmin isabeti) ve 4. ölçütün (rejim edge) bugün bir anlamlılık hesabı YOKTUR — onlara "anlamlı
# değil" damgası basmak, yapılmamış bir testin sonucunu uydurmak olurdu. Onlar eski iki durumlarında
# kalır ve `anlamlilik_hesabi: False` alanıyla bunu AÇIKÇA söylerler.
def _durum_anlamlilikla(esik_gecti: bool, anlamli: bool | None) -> str:
    """(eşik, anlamlılık) → durum. Anlamlılık ÖLÇÜLEMEDİYSE (None) hüküm TAMAMLANAMAZ: eşiği geçmiş
    bir değeri "sağlandı" saymak anlamlılığı varsaymak, "zayıf" saymak ise yapılmamış bir testin
    olumsuz sonucunu uydurmak olurdu. İkisi de yasak → olculemedi."""
    if not esik_gecti:
        return "kaldi"
    if anlamli is True:
        return "gecti"
    if anlamli is False:
        return "zayif"
    return "olculemedi"


def _olcut(status: str, value, esik: str, kaynak: str, **ek) -> dict:
    """Tek ölçütün SABİT şekli. Dört durum: gecti / zayif / kaldi / olculemedi. `value` ölçülemeyen
    hâlde de raporlanır (varsa) — "ne gördük"ü gizlemek, hükmü denetlenemez yapardı."""
    return {"status": status, "value": value, "esik": esik, "kaynak": kaynak, **ek}


def edge_verdict() -> dict:
    """BEŞ ÖLÇÜTÜN TEK HÜKMÜ. Saf okuma: hiçbir dosyaya yazmaz, hiçbir karara girmez — panonun ve
    /api/diagnostics'in okuduğu tek cümleyi üretir.

    BOOLEAN UYDURMA YASAK: dönen sözlükte "edge var/yok" diye tek bir bayrak YOKTUR. Ölçülemeyenler
    hem sayılır (`unmeasured`) hem de hüküm cümlesinde AÇIKÇA anılır; beşi de geçmeden "TAM" kelimesi
    kullanılmaz ve `passed == 5` ancak `unmeasured == 0` iken mümkündür (beş ölçüt, tek payda).

    BEŞİNCİ ÖLÇÜT KUYRUK: ilk dördü "seçim doğru mu?"nun türevleriydi;
    kuyruk "sermaye hayatta kalır mı?" sorusunu sorar. Kapı yasası kuyruğu 2026-07-22'den beri
    VETO olarak taşıyordu, kuzey yıldızı ise hiç görmüyordu — aynı depoda iki risk iştahı.

    HÜKMÜN KULLANIM YERİ: rafineri kararları (emir bacağı, otonomi, çıkış reformu)
    YALNIZ bu hükme bakar; sermaye artırımı ve silahlanma İKİ hükme birden bakar (bu + SONUÇ
    HÜKMÜ, `result_verdict`). Ayrım kasıtlı: EDGE "bir kenar var mı?" sorusunu R biriminde sorar,
    SONUÇ "para var mı?" sorusunu DOLAR biriminde. R-birimi geniş stopa yapısal önyargılıdır
    (okuma düzeltmeleri), yani sermaye kararı tek başına ona bırakılamaz."""
    cal = store.read_json("score_calibration.json", None) or {}
    # --- 1) SKOR → SONUÇ (rank-IC) --------------------------------------------------------------
    # KANIT GÖVDESİ ARTIK YALNIZ GERÇEK KATMAN (v1'in havuz kararının
    # geri alınması). v1 gerekçesi "gerçek dilim aylarca <30 kalır, hüküm sonsuza kadar ölçülemedi
    # der" idi. Ölçüldü ve gerekçe artık geçerli değil: gerçek dilim n=95'e ulaştı. Buna karşılık
    # havuzun bedeli ölçüldü ve büyüktü — 2102 cf satırı 95 gerçeği 22:1 boğuyor, yani "skorun tahmin
    # gücü" diye raporlanan sayı fiilen cf'in IC'siydi. Üstelik o cf satırları canlı çıkış yasasının
    # yalnız bir kısmıyla simüle edilmiş sonuçlar taşıyor (bkz. CF_EXIT_FIDELITY_NOTE): kuzey
    # yıldızının dayandığı sayı, sadakati beyanen eksik bir simülasyondan gelemez.
    # Havuz ve cf katmanları BİLGİ olarak yanında durmaya devam eder (atılmaz), ama hüküm taşımaz.
    kat = cal.get("katmanlar") or {}
    real = kat.get("gercek") or cal.get("real") or {}          # yeni şema, eski şemaya düşerek
    havuz = kat.get("havuz") or {}
    cf_kat = kat.get("cf") or cal.get("cf") or {}
    ic, ic_n = real.get("rank_ic"), real.get("n")
    ic_kaynak = "gerçek kapanmış işlem (cf HARİÇ)"
    # EŞİK ARTIK TEK BAŞINA YETMEZ: `anlamli` alanı ZATEN payload'ın
    # içindeydi ve `False` diyordu; hüküm onu okumuyordu. Aynı sözlükten iki farklı cevap çıkması —
    # kart "SAGLANDI", iki satır altı "gürültüden ayırt EDİLEMİYOR" — kuzey yıldızının kendi
    # içindeki en büyük çelişkiydi. Eşik metni bu yüzden anlamlılığı da ADIYLA anar.
    ic_esik = f"gerçek katman rank_ic >= {EDGE_IC_MIN} (n >= {EDGE_IC_N_MIN}) VE istatistiksel anlamlılık"
    # HAVUZ ARTIK "DOĞRULAMA BANDI" DEĞİL BAĞLAM: hükmün dayandığı sayı ile ona eşlik eden sayılar
    # yer değiştirdi, isim de onu takip etmeli — eski `dogrulama_bandi` alanı korunur ama içeriği
    # ters yönde doldurulur (gerçek hüküm verir, havuz bağlam olur).
    ek = {"n": ic_n,
          "dogrulama_bandi": havuz.get("rank_ic") if havuz.get("rank_ic") is not None else "ölçülmedi",
          "havuz_ic": havuz.get("rank_ic"), "cf_ic": cf_kat.get("rank_ic"),
          "n_real": cal.get("n_real"), "n_cf": cal.get("n_cf"),
          # ANLAMLILIK ARTIK EŞİĞE GİRER (ÖNCEKİ "eşiğe girmez ama gizlenmez" sapma
          # beyanının GERİ ALINMASI). Gerekçe ölçüldü: n=60-95 bandında i.i.d. güven aralığı ±0.20
          # civarı, yani 0.03 eşiğini geçen bir IC gürültüden ayırt edilemeyebilir — canlıda tam
          # olarak bu oldu (IC 0.0492, anlamli=False, kart yine de SAGLANDI yanıyordu). Alan hem
          # `ek` içinde görünür kalır hem de `_durum_anlamlilikla` üzerinden DURUMU belirler.
          "anlamli": real.get("anlamli"),
          "anlamlilik_hesabi": True,
          "sadakat": "gerçek defter — simülasyon sadakati sorusu bu ölçüte GİRMEZ"}
    # EŞİK ARTIK TEK BAŞINA YETMEZ: `anlamli` alanı ZATEN payload'ın
    # içindeydi ve `False` diyordu; hüküm onu okumuyordu. Aynı sözlükten iki farklı cevap çıkması —
    # kart "SAGLANDI", iki satır altı "gürültüden ayırt EDİLEMİYOR" — kuzey yıldızının kendi
    # içindeki en büyük çelişkiydi.
    ic_esik = f"gerçek katman rank_ic >= {EDGE_IC_MIN} (n >= {EDGE_IC_N_MIN}) VE istatistiksel anlamlılık"
    if ic is None or not isinstance(ic_n, (int, float)) or ic_n < EDGE_IC_N_MIN:
        skor = _olcut("olculemedi", ic, ic_esik, ic_kaynak, **ek)
    else:
        skor = _olcut(_durum_anlamlilikla(ic >= EDGE_IC_MIN, real.get("anlamli")),
                      ic, ic_esik, ic_kaynak, **ek)

    # --- 2) SPY ÜSTÜ ----------------------------------------------------------------------------
    # Pozitiflik ölçütü `benchmark_relative()`ın KENDİ alanına bağlanır: `beat_benchmark` (o fonksiyon
    # `excess_return > 0`u zaten numpy sigortasından geçirip bool'a çeviriyor). Burada ikinci bir
    # eşik tanımlamak, aynı olgunun iki farklı yerde iki farklı hesabı olurdu.
    # ÖLÇÜT ARTIK MARUZİYET-DÜZELTİLMİŞ FARKI OKUR. Ham `excess_return`, parası
    # sürekli piyasada duran bir SPY tutucusuyla kıyas yapıyordu; strateji ise sermayesinin bir
    # kısmını, zamanın bir kısmında taşır (canlı defterde ortalama maruziyet 1.0'ın epey altında).
    # Boğa piyasasında bu, taşınmamış betanın getirisini stratejiden DÜŞERek hak edilmemiş bir
    # başarısızlık; düşüşte ise taşınmamış betanın kaybını EKLEyerek hak edilmemiş bir başarı yazar.
    # Ham alanlar `ek` içinde görünür kalır (kaldırılmadı — geriye dönük uyum ve denetlenebilirlik).
    br = benchmark_relative()
    spy_esik = "maruziyet-düzeltilmiş fark > 0 VE bootstrap aralığı sıfırı dışarıda bırakıyor"
    if not br:
        spy = _olcut("olculemedi", None, spy_esik, "gerçek kapanmış işlem vs SPY",
                     anlamlilik_hesabi=True)
    else:
        spy_ek = {"ham_excess_return": br.get("excess_return"),
                  "ham_beat_benchmark": br.get("beat_benchmark"),
                  "strategy_return": br.get("strategy_return"),
                  "benchmark_return": br.get("benchmark_return"),
                  "maruziyet": (br.get("maruziyet") or {}).get("oran"),
                  "ci": br.get("ci"), "ci_kapsam": br.get("ci_kapsam"),
                  "anlamli": br.get("anlamli"), "anlamlilik_hesabi": True}
        spy_kaynak = (f"gerçek kapanmış işlem vs {br.get('benchmark') or 'SPY'} "
                      f"({br.get('start') or '?'} → {br.get('end') or '?'}), maruziyet-düzeltilmiş")
        adj = br.get("exposure_adjusted_excess")
        if adj is None:
            # Maruziyet ölçülemedi → düzeltilmiş fark yok. Ham farka geri düşüp onu "geçti" saymak,
            # ölçütün adını değiştirip yasasını değiştirmemek olurdu.
            spy = _olcut("olculemedi", None, spy_esik, spy_kaynak, **spy_ek)
        else:
            spy = _olcut(_durum_anlamlilikla(bool(br.get("exposure_adjusted_beat")), br.get("anlamli")),
                         adj, spy_esik, spy_kaynak, **spy_ek)

    # --- 3) TAHMİN İSABETİ ----------------------------------------------------------------------
    ph = prediction_hit_rate()
    ph_n, ph_hits = ph.get("n") or 0, ph.get("sign_hits")
    ph_oran = round(ph_hits / ph_n, 3) if ph_n and ph_hits is not None else None
    ph_esik = f"sign_hits/n >= {PRED_HIT_RATE_MIN} (n >= {PRED_HIT_N_MIN})"
    if ph_n < PRED_HIT_N_MIN:
        # Değer YİNE raporlanır: "2/3 tuttu ama n yetersiz" ile "hiç ölçüm yok" aynı şey değildir.
        ph_olcut = _olcut("olculemedi", ph_oran, ph_esik, "terminal hipotez (tahmin+gerçekleşen)",
                          n=ph_n, sign_hits=ph_hits, anlamlilik_hesabi=False)
    else:
        ph_olcut = _olcut("gecti" if ph_oran is not None and ph_oran >= PRED_HIT_RATE_MIN else "kaldi",
                          ph_oran, ph_esik, "terminal hipotez (tahmin+gerçekleşen)",
                          n=ph_n, sign_hits=ph_hits, anlamlilik_hesabi=False)

    # --- 4) REJİM BAŞINA EDGE -------------------------------------------------------------------
    # `_kaynak` künyesi bir REJİM DEĞİLDİR (regime_edge'in kendi yorumu: içinde `n` alanı olan her
    # sözlüğü rejim sanan tüketici paydayı şişirir). Künye burada da açıkça elenir.
    from . import sieve
    re_doc = store.read_json("regime_edge.json", None) or {}
    rejimler = [(k, v) for k, v in re_doc.items()
                if k != sieve.PROV_KEY and isinstance(v, dict) and v.get("n") is not None]
    yeterli = [(k, v) for k, v in rejimler if (v.get("n") or 0) >= REGIME_N_MIN]
    re_esik = f"herhangi bir rejimde n >= {REGIME_N_MIN} VE avg_r > {REGIME_AVG_R_MIN}"
    re_kaynak = (re_doc.get(sieve.PROV_KEY) or {}).get("source") or "karşı-olgusal defter (sim)"
    if not yeterli:
        # HİÇBİR REJİM n EŞİĞİNİ GEÇMİYORSA BU BİR BAŞARISIZLIK DEĞİL, ÖLÇÜLEMEYİŞTİR: ince
        # örneklemde negatif bir avg_r "o rejimde kenar yok" demez, "henüz okunmuyor" der.
        rejim = _olcut("olculemedi", None, re_esik, re_kaynak,
                       rejim_sayisi=len(rejimler), anlamlilik_hesabi=False,
                       en_buyuk_n=max([v.get("n") or 0 for _, v in rejimler], default=0))
    else:
        # KESİN BÜYÜKTÜR: eşik 0.0 olduğu için `>=` tam sıfırı da "kenar var" sayardı — sıfır beklenti
        # bir kenar iddiası değildir, kenarın YOKLUĞUdur.
        gecen = [(k, v) for k, v in yeterli if (v.get("avg_r") is not None
                                                and v["avg_r"] > REGIME_AVG_R_MIN)]
        en_iyi = max(gecen or yeterli, key=lambda kv: (kv[1].get("avg_r") is not None,
                                                       kv[1].get("avg_r") or 0.0))
        rejim = _olcut("gecti" if gecen else "kaldi",
                       {"regime": en_iyi[0], "n": en_iyi[1].get("n"), "avg_r": en_iyi[1].get("avg_r")},
                       re_esik, re_kaynak, rejim_sayisi=len(rejimler), esik_ustu_rejim=len(yeterli),
                       anlamlilik_hesabi=False)

    # --- 5) KUYRUK: SERMAYE HAYATTA KALIR MI? -------------------------
    # İKİ BACAK, İKİSİ BİRDEN: gerçekleşen maks düşüş ≤ EDGE_MAXDD_MAX **VE** işlem-R CVaR(%5) ≥
    # EDGE_CVAR5_MIN_R. Gerekçeler sabitlerin yanında yazılı. n < EDGE_TAIL_N_MIN iken OLCULEMEDI
    # ve ölçülen değerler YİNE raporlanır: "%8,04 düşüş gördük ama n yetersiz" ile "hiç ölçüm yok"
    # aynı cümle değildir.
    # ANLAMLILIK HESABI YOK ve bu AÇIKÇA söylenir (`anlamlilik_hesabi: False`): ne düşüşün ne de
    # CVaR'ın bugün bir güven aralığı var. ZAYIF durumunu buraya uygulamak, yapılmamış bir testin
    # olumsuz sonucunu uydurmak olurdu (3. ve 4. ölçütün aynı sınırı).
    dd = _realized_drawdown()
    _rs = [float(t["r_multiple"]) for t in _trades() if t.get("r_multiple") is not None]
    cv = _cvar(_rs, 5.0)
    kuyruk_esik = (f"gerçekleşen maks düşüş <= {EDGE_MAXDD_MAX} VE işlem-R CVaR(%5) >= "
                   f"{EDGE_CVAR5_MIN_R}R (n >= {EDGE_TAIL_N_MIN})")
    kuyruk_kaynak = "gerçek kapanmış işlem + günlük piyasaya-göre sermaye eğrisi"
    kuyruk_ek = {"n": len(_rs), "max_dd": dd["max_dd"], "dd_kaynak": dd["kaynak"],
                 "kapali_islem_dd": dd["kapali_islem_dd"], "gunluk_m2m_dd": dd["gunluk_m2m_dd"],
                 "max_dd_alt_sinir": dd["max_dd_alt_sinir"], "m2m_durum": dd["m2m_durum"],
                 "m2m_neden": dd["m2m_neden"], "seri_donem": dd["seri_donem"],
                 "defter_seansi": dd["defter_seansi"], "bayat_seri_dd": dd["bayat_seri_dd"],
                 # YASA 6 ZİNCİRİ — `result_verdict`in maks-düşüş ölçütüyle AYNI üçlü. İki hüküm
                 # aynı olguyu okur; teşhisi yalnız birine koymak, kuyruk fişini (dd_bacagi null)
                 # yine kör bırakırdı.
                 "gecikme_gun": dd["gecikme_gun"], "egri_yazari": dd["yazar"],
                 "yazar_kanit": dd["yazar_kanit"],
                 "cvar5_r": (cv or {}).get("cvar5_r"), "var5_r": (cv or {}).get("var5_r"),
                 "kuyruk_n": (cv or {}).get("kuyruk_n"), "en_kotu_r": (cv or {}).get("en_kotu_r"),
                 "isaret": (cv or {}).get("isaret"),
                 "esikler": {"max_dd": EDGE_MAXDD_MAX, "cvar5_r": EDGE_CVAR5_MIN_R,
                             "n_min": EDGE_TAIL_N_MIN},
                 "anlamlilik_hesabi": False}
    _kdeger = {"max_dd": dd["max_dd"], "cvar5_r": (cv or {}).get("cvar5_r")}
    if len(_rs) < EDGE_TAIL_N_MIN or dd["max_dd"] is None or cv is None:
        kuyruk = _olcut("olculemedi", _kdeger, kuyruk_esik, kuyruk_kaynak, **kuyruk_ek)
    else:
        # ALT SINIR HÜKMÜ — EŞİĞE DOKUNULMADI, OKUMA DÜRÜSTLEŞTİRİLDİ.
        # m2m bacağı ölçülemediğinde `max_dd` KAPANMIŞ bacaktan gelen bir ALT SINIRDIR; gerçek
        # düşüş bundan yalnız KÖTÜ olabilir (yasanın kendisi "kötü olanı" der). Üç hâl:
        #   * alt sınır eşiği ZATEN AŞIYORSA → hüküm KESİNDİR: kaldı (eksik bacak iyileştiremez);
        #   * CVaR bacağı düşüyorsa → yine KESİN: kaldı (bağlaç VE, biri diğerini affetmez);
        #   * alt sınır eşiğin altında AMA yalnız alt sınırsa → "geçti" DENEMEZ, ÖLÇÜLEMEDİ.
        # Ölçülmeyen bacağı 0 saymak tam olarak bugüne kadarki sessiz kusurdu; onu "kaldı" saymak
        # ise ölçülmemiş bir başarısızlık UYDURMAK olurdu (3. ve 4. ölçütün aynı sınırı).
        _dd_asti = dd["max_dd"] > EDGE_MAXDD_MAX
        _cv_ok = cv["cvar5_r"] >= EDGE_CVAR5_MIN_R
        _alt = bool(dd["max_dd_alt_sinir"])
        if _dd_asti or not _cv_ok:
            _durum = "kaldi"
        elif _alt:
            _durum = "olculemedi"
        else:
            _durum = "gecti"
        # `dd_bacagi` ÜÇ DEĞERLİ OLDU: True (ölçüldü, geçti) / False (ölçüldü, aştı) / None
        # (ölçülemedi — pano `null`ı zaten "mut" rengiyle çiziyor, app.js:4944 üçlü dalı hazır).
        kuyruk = _olcut(_durum, _kdeger, kuyruk_esik, kuyruk_kaynak,
                        dd_bacagi=(False if _dd_asti else (None if _alt else True)),
                        cvar_bacagi=bool(_cv_ok), **kuyruk_ek)

    criteria = {"skor_sonuc": skor, "spy_ustu": spy, "tahmin_isabeti": ph_olcut,
                "rejim_edge": rejim, "kuyruk": kuyruk}
    # ÜÇ DURUMUN YAZILI DİLİ: makine değerleri `gecti/kaldi/olculemedi` AYNEN kalır —
    # pano ve testler onlara bağlı ve bir sözleşmeyi yalnız okunabilirlik için kırmak, kırılan her
    # tüketicide sessiz bir dal açar. `durum` alanı o değerin insan dilindeki karşılığını TAŞIR;
    # tek yerde eşleşir, her tüketicide yeniden çevrilmez (iki farklı çeviri = iki farklı hüküm).
    for _c in criteria.values():
        _c["durum"] = EDGE_DURUM_ADI[_c["status"]]
    passed = sum(1 for c in criteria.values() if c["status"] == "gecti")
    failed = sum(1 for c in criteria.values() if c["status"] == "kaldi")
    unmeasured = sum(1 for c in criteria.values() if c["status"] == "olculemedi")
    zayif = sum(1 for c in criteria.values() if c["status"] == "zayif")
    # TEK YAZILI HÜKÜM. Sayılar DÖRT kovadan gelir ve DÖRDÜ DE cümlede
    # geçer: "x/5 sağlandı" tek başına, kalanların başarısız mı, henüz ölçülemez mi, yoksa eşiği
    # geçip anlamlılığı geçemeyen mi olduğunu gizlerdi — sabır, başarısızlık ve gürültü aynı cümleye
    # sıkıştırılamaz. `passed` YALNIZ eşik+anlamlılık birlikte sağlananları sayar; ZAYIF olan bir
    # ölçüt paydaya girer ama paya GİRMEZ.
    # PAYDA ARTIK 5: `len(criteria)`den TÜREYİP sabit yazılmadığı için beşinci ölçüt
    # eklendiğinde cümle kendiliğinden düzeldi — ama tüketiciler (pano şeridi, testler) 4'ü sabit
    # yazmıştı ve onlar bu turda elle güncellendi.
    n = len(criteria)
    if passed == n:
        verdict = (f"EDGE KANITI: {passed}/{n} sağlandı — beş ölçütün beşi de eşiği VE "
                   f"anlamlılığı geçti (TAM)")
    else:
        verdict = (f"EDGE KANITI: {passed}/{n} sağlandı ({zayif} zayıf, {failed} sağlanmadı, "
                   f"{unmeasured} ölçülemedi) — edge kanıtlanmadı")
    return {"criteria": criteria, "passed": passed, "failed": failed,
            "unmeasured": unmeasured, "zayif": zayif, "verdict": verdict}


# ---- SONUÇ HÜKMÜ: EDGE'İN İKİZİ, DOLAR MERCEĞİ ----------------------
# NEDEN VAR. Sistem "para var mı?" sorusunu bugüne kadar R ORTALAMASIYLA yargılıyordu ve R birimi
# geniş stopa YAPISAL OLARAK ÖNYARGILI: stop genişlerse boyut R-nötr biçimde küçülür, aynı fiyat
# hareketi daha az R üretir, kazananların R'leri daralır. Yani "ortalama R düştü" cümlesi "daha az
# para kazandık" cümlesiyle AYNI ŞEY DEĞİLDİR — ve çıkış reformunun bütün adayları tam bu iki
# cümlenin karıştığı yerde reddedildi:
#   * Üç çıkış paketi: kuyruk KAZANDI (CVaR farkı −2,20 / −2,33 / −3,46R), bileşik skor kaybetti.
#   * Bant filtresi: fold 3/3 + kuyruk farkı −2,26R + n 98→106, bileşik skor yine kaybetti.
# Üç bağımsız ölçümde aynı desen görüldüğünde şüphe artık adayda değil ÖLÇÜTTEDİR. Bu hüküm o
# şüpheyi giderecek İKİNCİ MERCEĞİ kurar: aynı defter, dolar biriminde.
#
# KARAR KULLANIMI: **rafineri kararları EDGE'e, sermaye/silahlanma
# İKİSİNE bakar.** Yani bir çıkış kuralı ya da otonomi kademesi EDGE hükmüyle yargılanır; sermaye
# artırımı ve Faz 6 silahlanması EDGE **ve** SONUÇ hükmünün İKİSİNİ birden ister. Bu hüküm EDGE'in
# yerine geçmez ve EDGE'i gevşetmez — payda ayrıdır, cümle ayrıdır, eşikler ayrıdır.
#
# FRİKSİYON İKİ KEZ KESİLMEZ (canlı kaynaktan doğrulandı — broker.close_position):
# `pnl_dollars` ZATEN NET'tir (kayma dolum fiyatının İÇİNDE, iki bacağın komisyonu düşülmüş) ve
# `costs` alanı broker'ın kendi ifadesiyle "informational total friction" — YENİDEN KESİLMEZ.
# "Friksiyon-sonrası dolar beklentisi" bu yüzden `pnl_dollars`ın ortalamasıdır; `costs`tan bir kez
# daha çıkarmak friksiyonu ikiye katlayıp hükmü hak edilmemiş biçimde sertleştirirdi. `costs`
# yalnız 4. ölçütte KIYAS TABANI olarak kullanılır (kenar, ödediği ücretten büyük mü?).
RESULT_N_MIN = 30              # dolar hükmü için asgari kapanmış işlem. `goal.yaml`ın `min_sample`
                               # değeriyle BİREBİR: aynı depoda "bir istatistik için en az kaç
                               # satır" sorusunun ikinci bir cevabı olmamalı (EDGE'in REGIME_N_MIN
                               # sabiti de aynı gerekçeyle 30'a çekilmişti).
RESULT_PF_MIN = 1.3            # profit factor tabanı (Σkazanç / |Σkayıp|). 1,0 tam başabaştır;
                               # 1,0-1,2 bandı 95 işlemlik bir defterde örneklem gürültüsünün
                               # içindedir VE dolum kalitesindeki mütevazı bir kötüleşmeyle silinir
                               # (Alpaca paper dolumları iyimser — TCA hâlâ ölçülmedi). 1,3
                               # friksiyonun üstünde ~%30 tampon bırakır.
RESULT_MAXDD_MAX = 0.16        # gerçekleşen maks düşüş tavanı — `goal.yaml`ın `max_drawdown`'ı ve
                               # `EDGE_MAXDD_MAX` ile BİREBİR AYNI. Üç yerde aynı sayı bilinçli:
                               # operatörün yazılı başarısızlık sınırı TEK olmalı. Eşitlik testle
                               # çivilenir; ayrışırsa orası kırmızı yanar.
RESULT_NET_OVER_FRICTION = 1.0 # net PnL, ödenen friksiyonun EN AZ bu katı olmalı. NEDEN "net > 0"
                               # DEĞİL: net PnL'in İŞARETİ, işlem başına beklentinin işaretiyle
                               # matematiksel olarak AYNI sorudur (Σpnl = n × ortalama) — iki ölçüt
                               # tek soruyu iki kez sorup paydayı şişirirdi. 4. ölçüt bu yüzden
                               # BÜYÜKLÜK sorar: kenar, geçiş ücretinden büyük mü? Katsayı 1,0 =
                               # "friksiyon kadar bile kazanmayan bir kenar, dolum kalitesi iki kat
                               # kötüleştiğinde tamamen silinir" (gerçek broker sorusu hâlâ açık).


def _pf(pnls: list) -> dict:
    """Profit factor + brüt bacakları. Kayıp bacağı SIFIRSA oran TANIMSIZ (None): kayıpsız bir
    defterde "sonsuz profit factor" yazmak, bölmenin tanımsızlığını bir başarı iddiasına
    çevirmek olurdu."""
    kazanc = sum(p for p in pnls if p > 0)
    kayip = sum(p for p in pnls if p < 0)
    return {"pf": (round(kazanc / abs(kayip), 4) if kayip < 0 else None),
            "brut_kazanc": round(kazanc, 2), "brut_kayip": round(kayip, 2),
            "n_kazanan": sum(1 for p in pnls if p > 0), "n_kaybeden": sum(1 for p in pnls if p < 0)}


# ---- CANLI-BEKLENTİ TAVANI — YAZILI KURALIN ÖLÇÜLEN HÂLİ -------------------
# NEDEN BURADA VE NEDEN BİR KOLON. Borç listesinde şu kural yazılıydı: "canlı
# beklenti tavanı backtest×0,5 ve <×0,4 süspansiyon". Kural yazılıydı ama HİÇBİR KOD onu OKUMUYORDU
# ve bu tam olarak `explore_rate`/`kill_switch_file` sınıfıdır: operatör yürürlükte sanır, hiçbir
# yüzey ölçmez.
#
# ARANDI VE BULUNAMADI — bağlanacak MEVCUT bir karar noktası YOK (tarama: probgate,
# reflect/rollback, guard, arming, autonomy_ladder, oos_erosion, watchdog, versioning). Depoda
# canlı ile backtest'i kıyaslayan TEK mekanizma `probgate.refresh_meta_calibration`dır ve o,
# BEKLENTİ SEVİYESİNİ değil ΔS FARKINI kıyaslar (predicted_delta ↔ realized_delta) — üstelik kendi
# beyanıyla ÖLÇEK BORCU altındadır (`olcek_borcu`: iki taraf farklı birimde). Yani "canlı beklenti
# tavanı"nı oraya bağlamak, farklı bir soruyu ölçen bir mekanizmanın üstüne ikinci bir anlam
# yüklemek olurdu.
#
# SEÇİLEN YOL: EN YAKIN DÜRÜST YER = SONUÇ hükmünün KOLONU. Canlı işlem-başına beklenti zaten
# `result_verdict`in 1. ölçütünde (dolar merceğinde) yaşıyor; bu kolon aynı defteri R biriminde,
# backtest karşılığıyla YAN YANA koyar. `beta_duzeltilmis` ve `net_kotumser` ile AYNI SINIF:
# sayaçlara (passed/failed/unmeasured/zayif) HİÇ dokunmaz, `criteria` sözlüğüne GİRMEZ, payda 4
# kalır. HÜKÜM VERMEZ — süspansiyon kararı operatörün, kapı kararı probgate'indir.
LIVE_CEILING_DURUMLAR = ("olculemedi", "tavan_altinda", "tavan_ustunde", "suspansiyon_degerlendirmesi")

# ---- BACKTEST BEKLENTİSİ: TEK SORU, ÜÇ YAZAR, İKİ ALAN ----------------------------------------
# ÖLÇÜLEN KUSUR (fiş 1/4/9, canlı karne 2026-08-25): tavan hükmü backtest tarafını TEK bir alandan
# okuyordu (`versions[<sürüm>].backtest_full.avg_r`) ve o alanı karneye YALNIZ tam re-seed yolu
# yazıyor. Sürüm doğuran diğer iki yol onu HİÇ yazmaz — yani ölçüm diskte YAZILI olduğu hâlde kapı
# "ölçülemedi" diyordu. Canlı satır: `current_version = 5`, v5 = {params, parent, source,
# live_since, note}; v4'te `backtest_full` VAR (re-seed yazmış), v5'te ne o ne fold'lar.
#
# KÖK YUKARIDAN DA KAPANDI (2026-09-01, akıbet kalemi N00017): ship yolu artık GLOBAL ship'te
# `backtest_full`ı da yazıyor — `walk_forward`ın `full_detail`i zaten hesaplanıyordu ve atılıyordu.
#
# REJİM SATIRI DA KAPANDI (2026-09-02, TSK-002) — AMA KENDİ POPÜLASYONUYLA. 2026-09-01'de rejim
# ship'i bu alanı bilerek yazmıyordu: `full_detail` dilimlenmemiştir ve onu rejim satırının
# ÖNCELİKLİ bacağına koymak `backtest_oos@<rejim>` ek-adının önlediği hatanın ta kendisi olurdu.
# `walk_forward` artık rejimli çağrıda İKİNCİ bir defter döndürüyor (`full_detail_graded`, nüfusu
# `_regime_slice`) ve rejim ship'i onu `backtest_full@<rejim>` diye yazıyor — yani ÜÇÜNCÜ bir
# kaynak doğdu ve okuma sırasına DÜZ anahtarın hemen ardına girdi (aşağıdaki sıra yasası).
#
# İKİNCİ BACAK (fold'lar) YİNE EMEKLİ OLMADI, gerekçesi bir kez daha DARALDI: operatör kalemi
# hiçbirini yazmaz ve üretici dilimli defteri veremezse rejim satırında da yalnız fold'lar kalır.
# Yani "ship edildi ama tam-pencere defteri yok" hâli hâlâ mümkündür.
#
# ŞABLON ANAHTAR: ek-adlı kaynağın SOMUT adı satırdan türetilir (rejim orada yazılıdır), o yüzden
# sözleşme kaydına ŞABLONUYLA girer. `<rejim>` yer tutucusu hem kayıt anahtarında hem kapsam
# metnindedir ve dönen `kapsam` o metinden ÜRETİLİR — iki yerde ayrı ayrı yazılsaydı sessizce
# ayrışırlardı (TEK-KAYNAK YASASI).
EK_ADLI_TAM_PENCERE = "backtest_full@<rejim>"
BACKTEST_BEKLENTI_KAYNAKLARI = ("backtest_full", EK_ADLI_TAM_PENCERE, "backtest_folds")
#: Satırdaki rejim damgasının okunduğu yer: ship yolu OOS skorunu HER rejim ship'inde bu ön ekle
#: yazar (`reflect._submit_locked`), tam-pencere defterini ise ancak üretici verirse. Rejimi
#: buradan türetmek, "hangi dilim?" sorusunu satırın KENDİSİNE sordurur — okuyucunun tahminine değil.
OOS_EK_ONEKI = "backtest_oos@"
BACKTEST_BEKLENTI_KAPSAM = {
    "backtest_full": ("TAM replay penceresi — `score.score_detail` çıktısının `avg_r` alanı "
                      "(yazan: run.py'nin re-seed yolu ve reflect.py'nin ship yolu — ship "
                      "tarafında YALNIZ global ship; rejim ship'i ek-adlı kardeşini yazar)"),
    EK_ADLI_TAM_PENCERE: ("TAM replay penceresinin <rejim> dilimi — `score.score_detail` çıktısı, "
                          "nüfusu `backtest._regime_slice(res.trades, '<rejim>')` (yazan: "
                          "reflect.py'nin REJİM ship yolu, kaynağı `walk_forward.full_detail_graded`). "
                          "Düz `backtest_full` ile AYNI pencere, DAR nüfus; okunan alan `avg_r`dir "
                          "— span-türevi alanlar (score/sharpe/realized_30d) dilim kümelenmesinden "
                          "yıllıklanır, kıyaslanabilir sayılmaz (üreticideki bedel beyanı, madde 3)"),
    "backtest_folds": ("Search-OOS walk-forward fold'larının n-AĞIRLIKLI ortalaması — "
                       "`backtest._fold_metrics` şekli (yazan: reflect.py'nin ship yolu). "
                       "`backtest_full`tan DAR bir penceredir: tam replay değil, OOS dilimi"),
}


def _tam_pencere_okumasi(bt, alan_adi: str, ariza: list) -> dict | None:
    """Bir TAM-PENCERE defterinden (`score.score_detail` şekli) `avg_r`/`n` çıkarır — düz ve
    ek-adlı bacağın ORTAK gövdesi.

    NEDEN ORTAK: iki bacak aynı şekli okur ve aynı arıza sınıflarını ("alan yok" ↔ "alan bozuk")
    ayırt etmek zorundadır. İki kopya sessizce ayrışırdı: biri bir gün `n`i zorunlu kılar, diğeri
    kılmaz ve rejim satırları global satırlardan FARKLI bir yasayla okunmaya başlar (TEK-KAYNAK
    YASASI). `alan_adi` yalnız arıza METNİ içindir — okuyucu koda inmeden hangi alanın bozuk
    olduğunu görsün.

    None döner = bu bacak çözülmedi (yok ya da bozuk); bozuksa `ariza` listesi ADIYLA konuşur."""
    if not (isinstance(bt, dict) and bt.get("avg_r") is not None):
        return None
    try:
        _r = float(bt["avg_r"])
    except (TypeError, ValueError):  # sessiz-yutma: SESSİZ DEĞİL — biçimsiz alanın adı `ariza` listesine girer ve hiçbir bacak çözülmezse dönüşteki `neden` cümlesinde ADIYLA basılır ("alan yok" ile "alan bozuk" ayrı arıza sınıflarıdır); sonraki bacaklar yine denenir, yani bilgi kaybı da yok
        ariza.append(f"`{alan_adi}.avg_r` BİÇİMSİZ")
        return None
    _n = bt.get("n")
    try:
        _n = None if _n is None else int(_n)
    except (TypeError, ValueError):  # sessiz-yutma: yalnız RAPOR alanı olan örneklem sayısı; beklentinin kendisi ölçüldü ve n=None "sayı bilinmiyor" diye okunur, hüküm bu alandan türemiyor
        _n = None
    return {"avg_r": _r, "n": _n}


def _backtest_beklenti_r(satir: dict) -> dict:
    """Karne satırından BACKTEST BEKLENTİSİNİ (R = işlem başına ortalama) çözen TEK yer.

    NEDEN ÜÇ BACAK. "Bu sürümün backtest beklentisi nedir?" TEK bir sorudur, ama karneye yazan
    yollar tek değildir ve hiçbiri diğerinin alanını yazmaz:
      * tam re-seed (`run.py`) → `backtest_full` = `score.score_detail(...)` çıktısı, içinde `avg_r`;
      * öğrenme döngüsünün GLOBAL ship yolu (`reflect.py` → `versioning.update_scoreboard`) →
        `backtest_folds` = `backtest._fold_metrics` çıktısı (her fold `n` + `avg_r`) ve
        2026-09-01'den beri `backtest_full` de (`walk_forward.full_detail`);
      * REJİM ship yolu → `backtest_folds` ve 2026-09-02'den beri `backtest_full@<rejim>`
        (`walk_forward.full_detail_graded` — AYNI pencere, `_regime_slice` ile DAR nüfus).
        DÜZ `backtest_full` rejim satırına ASLA düşmez: damgasız bir girdi `rollback`un
        düz-anahtar geri-düşüşlerinde GLOBAL sayılır ve uydurma delta üretirdi;
      * operatör kalemi → HİÇBİRİNİ yazmaz (yokluk BEYANLIdır, uydurulmaz).
    Tek bacak okuyan bir kapı, rejim ship'lerinde ve operatör satırlarında "ölçülemedi" der —
    ölçüm diskte dururken. (2026-08-25'te bu, ship edilen HER sürüm için doğruydu.)

    SIRA KEYFÎ DEĞİL VE DEĞİŞMEZ: tam-pencere defterleri fold'lardan GENİŞtir, GENİŞ olan önce
    okunur. Düz anahtar ek-adlıdan önce gelir çünkü damgasızlık GLOBAL demektir ve global nüfus
    hiçbir dilime indirgenemez. Hangisinin okunduğu `kaynak` + `kapsam` alanlarında ADIYLA durur —
    iki farklı popülasyon aynı sayı sanılamaz (bu, ek bacakların bedelidir ve gizlenmez).

    EK-ADLI BACAĞIN REJİMİ SATIRDAN TÜRETİLİR, TAHMİN EDİLMEZ: rejim ship'i OOS skorunu HER ZAMAN
    `backtest_oos@<rejim>` diye damgalar, yani "bu satır hangi dilimde notlandı?" sorusunun cevabı
    satırın kendisindedir. BİRDEN ÇOK ek-adlı OOS anahtarı görülürse (bugünkü üretici tekli yazar)
    HİÇBİRİ seçilmez — "herhalde ilki" bir tahmindir ve tavan hükmü o tahmine dayanırdı.

    AĞIRLIK n'DİR, DÜZ ORTALAMA DEĞİL: fold'lar eşit uzunlukta değildir. Düz ortalama, 7 işlemlik
    bir pencerenin gürültüsünü 45 işlemlik bir pencereyle aynı ağırlıkta sayardı — `backtest`in
    `FOLD_MIN_N` gerekçesiyle birebir aynı kusur, farklı yüzeyden.

    ÖLÇÜLEMEYEN 0 DEĞİLDİR: hiçbir bacak çözülmezse `avg_r` None döner ve `neden` hangi alanın
    eksik, hangisinin biçimsiz/belirsiz olduğunu söyler. 0.0 yazmak "ölçtük, beklenti sıfır" demek
    olurdu ve `bt_r <= 0` kapısı o sahte sayıya dayanırdı."""
    satir = satir if isinstance(satir, dict) else {}
    # 1. BACAK AİLESİNİN ARIZA DEFTERİ: biçimsiz alanlar VE ek-adlı seçim belirsizliği. İkisi de
    # "ölçüm yok" değil "ölçüme ULAŞILAMADI" sınıfıdır ve yedek bacak okunsa BİLE dönüşteki
    # `neden`e taşınır — yoksa okuyucu fold'ları bir TERCİH sanar, oysa bir ARIZA TELAFİSİdir.
    bicimsiz = []

    # --- 1. BACAK: tam replay detayı (DÜZ anahtar = global nüfus) --------------------------------
    _c = _tam_pencere_okumasi(satir.get("backtest_full"), "backtest_full", bicimsiz)
    if _c:
        return {**_c, "kaynak": "backtest_full",
                "kapsam": BACKTEST_BEKLENTI_KAPSAM["backtest_full"], "neden": None}

    # --- 1b. BACAK: EK-ADLI tam replay detayı (rejim ship'i — AYNI pencere, DAR nüfus) -----------
    _ekler = sorted(k for k in satir if isinstance(k, str) and k.startswith(OOS_EK_ONEKI))
    if len(_ekler) > 1:
        # TAHMİN YASAK. Arıza deftere ADLARIYLA yazılır: okuyucu satırın hangi iki (ya da daha
        # fazla) dilim damgası taşıdığını koda inmeden görsün ve YAZANI arasın.
        # Kapı OOS damgasını sayar; "tek oos@ + iki full@" gibi çapraz varyantlar da aynı
        # ulaşılamazlık ailesindendir (sürüm numarası asla yeniden kullanılmaz + re-seed satırı
        # sıfırdan kurar ve @'lı anahtarları taşımaz) — o dallar bu yüzden YAZILMADI (v100'ün
        # "ulaşılamaz dal yazılmaz" emsali; gerekçenin tamamı TSK-002 rapor §5 + incelemesi).
        bicimsiz.append(f"ek-adlı tam-pencere bacağı SEÇİLEMEDİ — satırda birden çok rejim damgası "
                        f"var ({', '.join(_ekler)}); hangi dilimin defteri okunacağı TAHMİN EDİLMEZ")
    elif _ekler:
        _rejim = _ekler[0][len(OOS_EK_ONEKI):]
        _ad = EK_ADLI_TAM_PENCERE.replace("<rejim>", _rejim)
        _c = _tam_pencere_okumasi(satir.get(_ad), _ad, bicimsiz)
        if _c:
            return {**_c, "kaynak": _ad,
                    "kapsam": BACKTEST_BEKLENTI_KAPSAM[EK_ADLI_TAM_PENCERE].replace("<rejim>",
                                                                                    _rejim),
                    "neden": None}

    # --- 2. BACAK: ship yolunun walk-forward fold'ları ------------------------------------------
    folds = satir.get("backtest_folds")
    toplam_r, toplam_n, atilan = 0.0, 0, 0
    for f in (folds if isinstance(folds, list) else []):
        if not isinstance(f, dict) or f.get("avg_r") is None:
            atilan += 1
            continue
        try:
            _fn, _fr = int(f.get("n") or 0), float(f["avg_r"])
        except (TypeError, ValueError):  # sessiz-yutma: SESSİZ DEĞİL — biçimsiz TEK fold, ölçülmüş fold'ları çöpe atmaz (bilgi kaybı olurdu) ama paya da girmez (uydurma olurdu); düşen fold sayısı `atilan`da toplanır ve dönüşteki `neden` alanında SAYIYLA raporlanır, payda `backtest_n`de görünür
            atilan += 1
            continue
        if _fn <= 0:
            atilan += 1
            continue
        toplam_r += _fn * _fr
        toplam_n += _fn
    if toplam_n > 0:
        # UYARI METNİ İKİ KAYBI DA TAŞIR: düşen fold'lar VE (varsa) tam-pencere bacaklarının
        # arızası (biçimsiz alan ya da ek-adda çözülemeyen rejim belirsizliği). İkincisi buraya
        # taşınmazsa "tam-pencere defteri okunamadı ama fold'lardan okuduk" bilgisi KAYBOLURDU —
        # okuyucu yedek bacağı bir tercih sanardı, oysa bir ARIZA telafisiydi.
        uyari = [f"{atilan} fold ölçülmemiş/biçimsiz olduğu için paydaya GİRMEDİ" if atilan else "",
                 *bicimsiz]
        uyari = [u for u in uyari if u]
        return {"avg_r": round(toplam_r / toplam_n, 4), "n": toplam_n, "kaynak": "backtest_folds",
                "kapsam": BACKTEST_BEKLENTI_KAPSAM["backtest_folds"],
                "neden": None if not uyari else f"{' · '.join(uyari)} (payda n={toplam_n})"}

    # --- HİÇBİRİ ÇÖZÜLMEDİ ----------------------------------------------------------------------
    # `backtest_full.avg_r` YOK ibaresi BEYANLI olarak bu cümlede kalır: fiş metinleri ve
    # `test_wpm_borclari_v146` onu arıyor; ikinci bacak eklendi diye ilk bacağın adı düşürülemez.
    # SINIR (inceleme 2026-09-02): `bicimsiz` artık seçim-belirsizliğini de taşır — düz anahtar
    # gerçekten YOK + çoklu damga hâlinde ibare belirsizlik metnine düşer. Bilinçli: o hâl bugün
    # ulaşılamaz (yukarıdaki ulaşılamazlık notu) ve iki metni yapıştırmak v146'nın aradığı cümleyi
    # başka bir arızanın gövdesine gömerdi.
    eksik = "`backtest_full.avg_r` YOK" if not bicimsiz else " + ".join(bicimsiz)
    fold_neden = (f"`backtest_folds` VAR ama ölçülmüş fold taşımıyor ({atilan} fold düştü)"
                  if isinstance(folds, list) and folds else "`backtest_folds` da YOK")
    return {"avg_r": None, "n": None, "kaynak": None, "kapsam": None,
            "neden": (f"{eksik} ve {fold_neden} — backtest beklentisi ölçülmemiş, tavan "
                      f"hesaplanamaz")}


def live_expectancy_ceiling(goal: dict | None = None) -> dict:
    """Canlı beklenti ↔ backtest beklentisi kıyası. SAF OKUMA, HÜKÜM YOK.

    İKİ TARAF, TEK BİRİM (R = işlem başına ortalama):
      canlı    — `trades.jsonl`ın YÜRÜRLÜKTEKİ sürüme ait, TOHUM OLMAYAN satırlarının `r_multiple`
                 ortalaması. Payda yasası `learning_scorecard`ınkiyle BİREBİR aynıdır
                 (live_paper + belirsiz; `replay_seed` TRAINING sayılır ve girmez) — aynı depoda
                 "canlı defter kimdir?" sorusunun ikinci bir cevabı olamaz.
      backtest — karnedeki AYNI sürümün backtest beklentisi, `_backtest_beklenti_r` ile YAZILI bir
                 öncelikte çözülür: `backtest_full.avg_r` (tam replay penceresi, GLOBAL nüfus),
                 yoksa `backtest_full@<rejim>.avg_r` (aynı pencerenin rejim dilimi — rejim
                 ship'leri), yoksa `backtest_folds`un n-ağırlıklı `avg_r` ortalaması (Search-OOS
                 dilimi). Hangi bacak okundu → `backtest_kaynak`/`backtest_kapsam`. Fold bacağı
                 2026-08-25'te eklendi: ship yolu o gün `backtest_full` YAZMIYORDU, yani ship
                 edilen her sürümde ölçüm diskte dururken taraf "ölçülemedi" görünüyordu
                 (fiş 1/4/9). Kök 2026-09-01'de global ship'te, 2026-09-02'de rejim ship'inde
                 yukarıdan da kapandı; fold bacağı operatör satırları ve üreticinin defter
                 veremediği hâller için DURUYOR. Sürüm eşleşmesi
                 `rollback.check_and_rollback`in popülasyon yasasıyla aynıdır; iki tarafı farklı
                 sürümlerden okumak like-for-like'ı bozardı.

    ORAN YALNIZ POZİTİF BİR BACKTEST BEKLENTİSİNDE TANIMLIDIR. Negatif bir beklentinin "yarısı"
    bir tavan değildir (−0,04'ün yarısı −0,02'dir ve canlı −0,01 gelirse "tavanı aştı" demek
    saçmadır). Bu durumda durum `olculemedi`dir ve nedeni adıyla yazılır — UYDURMA YASAĞI.

    DÖRT DURUM (`LIVE_CEILING_DURUMLAR`):
      olculemedi                — taraflardan biri yok / n yetersiz / backtest beklentisi ≤ 0
      suspansiyon_degerlendirmesi — oran < suspend_ratio (ÖNCE bakılır: daha sert olan hüküm)
      tavan_altinda             — canlı ≤ tavan; kuralın BEKLEDİĞİ hâl (iyi haber değil, NORMAL hâl)
      tavan_ustunde             — canlı > tavan; bir başarı ilanı DEĞİL, bir ŞÜPHE işareti:
                                  ya backtest fazla kötümser modellenmiş ya canlı örneklem şanslı."""
    from . import ledgerstamp as _ls
    g = goal or config.goal()
    kural = config.live_expectancy_rule(g)
    min_s = int(g.get("min_sample") or 30)

    sb = store.read_json("scoreboard.json", {"versions": {}})
    surum = sb.get("current_version")
    satir = ((sb.get("versions") or {}).get(str(surum)) or {}) if surum is not None else {}
    # BACKTEST TARAFI TEK ÇÖZÜCÜDEN GELİR (`_backtest_beklenti_r`): iki yazarın iki alanı, yazılı
    # bir öncelikle. Buradaki tek satırlık okuma, "hangi alandan okuduk?" sorusunu çıktıya taşır.
    _bt = _backtest_beklenti_r(satir)
    bt_r, bt_n = _bt["avg_r"], _bt["n"]

    # --- canlı taraf: tohum-olmayan, yürürlükteki sürüme ait, R'si ölçülmüş satırlar ------------
    rlar, kanitli_n, belirsiz_n = [], 0, 0
    for t in _trades():
        if surum is None or t.get("strategy_version") != surum:
            continue
        kaynak_damgasi = _ls.kaynak_of(t)
        if kaynak_damgasi == _ls.REPLAY_SEED:
            continue
        r = t.get("r_multiple")
        if r is None:
            continue
        try:
            rlar.append(float(r))
        except (TypeError, ValueError):  # sessiz-yutma: biçimsiz tek r_multiple; n çıktıda görünür, gizli kayıp yok
            continue
        if kaynak_damgasi == _ls.LIVE_PAPER:
            kanitli_n += 1
        else:
            belirsiz_n += 1
    canli_n = len(rlar)
    # YUVARLAMA UÇTA (probgate._score_pair ile aynı gerekçe): oran ve tavan kıyası HAM ortalamadan
    # hesaplanır; rapor alanları uçta yuvarlanır. Yuvarlanmış bir paydan bölmek, eşik civarındaki
    # bir hükmü ölçüm hassasiyetine bağlardı.
    canli_ham = (sum(rlar) / canli_n) if canli_n else None
    canli_r = round(canli_ham, 4) if canli_ham is not None else None

    tavan_ham = None if (bt_r is None or bt_r <= 0) else bt_r * kural["cap_mult"]
    tavan = None if tavan_ham is None else round(tavan_ham, 4)
    oran = (round(canli_ham / bt_r, 3) if (canli_ham is not None and bt_r is not None and bt_r > 0)
            else None)

    neden = None
    if surum is None:
        durum, neden = "olculemedi", "karnede yürürlükteki sürüm yok (current_version boş)"
    elif bt_r is None:
        durum, neden = "olculemedi", f"v{surum} karne satırında {_bt['neden']}"
    elif bt_r <= 0:
        durum, neden = "olculemedi", (f"backtest beklentisi pozitif DEĞİL ({bt_r}R) — negatif bir "
                                      f"beklentinin yarısı bir tavan değildir; oran TANIMSIZ")
    elif canli_n < min_s:
        durum, neden = "olculemedi", (f"canlı örneklem {canli_n} < min_sample {min_s} — beklenti "
                                      f"ölçülemedi (0 değil, BİLİNMİYOR)")
    elif (canli_ham / bt_r) < kural["suspend_ratio"]:
        durum = "suspansiyon_degerlendirmesi"
    elif canli_ham > tavan_ham:
        durum = "tavan_ustunde"
    else:
        durum = "tavan_altinda"

    hukum = {
        "olculemedi": f"TAVAN DURUMU ÖLÇÜLEMEDİ — {neden}",
        "suspansiyon_degerlendirmesi": (
            f"canlı {canli_r}R / backtest {bt_r}R = {oran} < {kural['suspend_ratio']} — "
            f"SÜSPANSİYON DEĞERLENDİRMESİ kuralı tetiklendi (ROADMAP §WP-M). Bu satır bir KARAR "
            f"DEĞİL, bir ÇAĞRIdır: süspansiyon operatör kalemidir"),
        "tavan_ustunde": (
            f"canlı {canli_r}R, tavanın ({tavan}R = backtest {bt_r}R × {kural['cap_mult']}) "
            f"ÜSTÜNDE — bir başarı ilanı değil ŞÜPHE işareti: ya backtest fazla kötümser "
            f"modellenmiş ya canlı örneklem şanslı (n={canli_n})"),
        "tavan_altinda": (
            f"canlı {canli_r}R ≤ tavan {tavan}R (backtest {bt_r}R × {kural['cap_mult']}); "
            f"oran {oran} ≥ süspansiyon eşiği {kural['suspend_ratio']} — kuralın BEKLEDİĞİ hâl"),
    }[durum]

    return {
        "durum": durum, "hukum": hukum, "neden": neden,
        # DURUM UZAYI ÇIKTININ İÇİNDE: okuyucu "başka hangi değerler mümkün?" sorusunu koda inmeden
        # cevaplayabilmeli — `getiri_tanimi`/`ci_yontem` beyanlarıyla aynı gerekçe.
        "durumlar": list(LIVE_CEILING_DURUMLAR),
        "hukme_girmez": True,
        "surum": surum,
        "canli_beklenti_r": canli_r, "canli_n": canli_n,
        "canli_kanitli_n": kanitli_n, "canli_belirsiz_n": belirsiz_n,
        "backtest_beklenti_r": bt_r, "backtest_n": bt_n,
        # HANGİ BACAKTAN OKUNDU: iki kaynaklı bir alan kaynağını söylemezse okuyucu iki farklı
        # popülasyonu (tam replay ↔ Search-OOS dilimi) aynı sayı sanar. `backtest_kaynak` None ise
        # taraf ölçülemedi ve `neden` hangi alanların eksik olduğunu söyler.
        "backtest_kaynak": _bt["kaynak"], "backtest_kapsam": _bt["kapsam"],
        "backtest_kaynaklar": list(BACKTEST_BEKLENTI_KAYNAKLARI),
        "backtest_uyari": _bt["neden"] if _bt["kaynak"] else None,
        "tavan_r": tavan, "oran": oran,
        "cap_mult": kural["cap_mult"], "suspend_ratio": kural["suspend_ratio"],
        "kural_kaynak": kural["kaynak"], "kural_metni": kural["kural_metni"],
        "kural_uyari": kural["uyari"],
        "min_sample": min_s,
        "birim": "R (işlem başına ortalama)",
        "kaynak": ("canlı: trades.jsonl · yürürlükteki sürüm · replay_seed HARİÇ (payda yasası "
                   "learning_scorecard ile aynı) | backtest: scoreboard.json "
                   "versions[<sürüm>].backtest_full.avg_r, yoksa aynı satırdaki "
                   "backtest_full@<rejim>.avg_r (rejim satırlarında; rejim satırın kendi "
                   "backtest_oos@<rejim> damgasından türetilir), yoksa backtest_folds'un "
                   "n-ağırlıklı avg_r ortalaması (öncelik yazılıdır; okunan bacak "
                   "`backtest_kaynak` alanında durur)"),
        "kapsam": ("ADVISORY KOLON — `result_verdict`in dört ölçütünden hiçbirini değiştirmez, "
                   "passed/failed/unmeasured/zayif sayaçlarına GİRMEZ ve hiçbir kapıyı "
                   "(probgate/guard/arming) kısmaz. Süspansiyon bir OPERATÖR kararıdır; bu alan "
                   "onu yalnız GÖRÜNÜR kılar"),
    }


def result_verdict() -> dict:
    """SONUÇ HÜKMÜ — DÖRT DOLAR ÖLÇÜTÜNÜN TEK YAZILI KARARI. EDGE hükmünün ikizi: aynı dört durum
    (SAGLANDI/ZAYIF/SAGLANMADI/OLCULEMEDI), aynı `_olcut` şekli, aynı tek-cümle deseni.

    Saf okuma — hiçbir dosyaya yazmaz, hiçbir karara girmez.

    DÖRT ÖLÇÜT, DÖRT AYRI SORU (kasıtlı olarak birbirinin türevi değil):
      1. BEKLENTİ  — işlem başına ortalama net $ pozitif VE blok-bootstrap aralığı sıfırı
                     dışlıyor mu? (anlamlılık hesabı VAR → ZAYIF durumu MÜMKÜN)
      2. PROFIT FACTOR — kazanç/kayıp ORANI eşiği geçiyor mu? (ortalamanın değil DAĞILIMIN sorusu:
                     n büyükse istatistiksel olarak pozitif ama ekonomik olarak kırılgan bir
                     beklenti mümkündür)
      3. MAKS DÜŞÜŞ — gerçekleşen düşüş operatörün yazılı başarısızlık sınırının içinde mi? (YOL
                     riski; ortalama hiçbir şey söylemez)
      4. NET PnL   — birikmiş net, ÖDENEN FRİKSİYONUN katı olarak yeterli mi? (büyüklük sorusu —
                     bkz. RESULT_NET_OVER_FRICTION'ın gerekçesi)

    2. ve 4. ölçütte anlamlılık hesabı YOKTUR ve bu `anlamlilik_hesabi: False` ile açıkça
    söylenir; 3. ölçüt de öyle. Onlara "anlamlı değil" damgası basmak, yapılmamış bir testin
    sonucunu uydurmak olurdu (EDGE'in 3./4. ölçütüyle aynı sınır)."""
    trades = _trades()
    pnls = [float(t["pnl_dollars"]) for t in trades if t.get("pnl_dollars") is not None]
    costs = [float(t["costs"]) for t in trades if t.get("costs") is not None]
    n = len(pnls)
    yeterli = n >= RESULT_N_MIN
    kaynak = "gerçek kapanmış işlem (trades.jsonl) — friksiyon dolum fiyatının İÇİNDE"

    # --- 1) İŞLEM BAŞINA DOLAR BEKLENTİSİ -------------------------------------------------------
    ort = round(sum(pnls) / n, 2) if n else None
    ci = _blok_bootstrap_ci(pnls) if n >= 2 else None
    b_esik = f"işlem başına ortalama net $ > 0 VE blok-bootstrap %95 aralığı sıfırı dışlıyor (n >= {RESULT_N_MIN})"
    b_ek = {"n": n, "ci": ci, "toplam_net": round(sum(pnls), 2) if n else None,
            "medyan": round(sorted(pnls)[n // 2], 2) if n else None,
            "anlamli": None if ci is None else ci["sifiri_disliyor"],
            "anlamlilik_hesabi": True,
            "ci_kapsam": ("yalnız işlem sırasının örneklem değişkenliği; bloklar kayıp SERİLERİNİ "
                          "korur (IID örnekleme aralığı sistematik olarak daraltır)")}
    if not yeterli or ort is None:
        beklenti = _olcut("olculemedi", ort, b_esik, kaynak, **b_ek)
    else:
        beklenti = _olcut(_durum_anlamlilikla(ort > 0, None if ci is None else ci["sifiri_disliyor"]),
                          ort, b_esik, kaynak, **b_ek)

    # --- 2) PROFIT FACTOR -----------------------------------------------------------------------
    pfd = _pf(pnls)
    pf_esik = f"profit factor >= {RESULT_PF_MIN} (n >= {RESULT_N_MIN})"
    # `esik_deger` MAKİNE OKUNUR OLARAK DA TAŞINIR: pano eşiği `esik` METNİNDEN ayıklamaya
    # çalışırsa (regex) sabit değişince sessizce yanlış sayı gösterir — eşik alanı ADIYLA gelir.
    pf_ek = {**pfd, "n": n, "esik_deger": RESULT_PF_MIN, "anlamlilik_hesabi": False}
    if not yeterli or pfd["pf"] is None:
        pf_olcut = _olcut("olculemedi", pfd["pf"], pf_esik, kaynak, **pf_ek)
    else:
        pf_olcut = _olcut("gecti" if pfd["pf"] >= RESULT_PF_MIN else "kaldi", pfd["pf"],
                          pf_esik, kaynak, **pf_ek)

    # --- 3) MAKS DÜŞÜŞ (SERMAYE EĞRİSİNDEN) -----------------------------------------------------
    dd = _realized_drawdown()
    dd_esik = f"gerçekleşen maks düşüş <= {RESULT_MAXDD_MAX} (n >= {RESULT_N_MIN})"
    dd_ek = {"n": n, "kapali_islem_dd": dd["kapali_islem_dd"], "gunluk_m2m_dd": dd["gunluk_m2m_dd"],
             "n_gun": dd["n_gun"], "dd_kaynak": dd["kaynak"],
             "max_dd_alt_sinir": dd["max_dd_alt_sinir"], "m2m_durum": dd["m2m_durum"],
             "m2m_neden": dd["m2m_neden"], "seri_donem": dd["seri_donem"],
             "defter_seansi": dd["defter_seansi"], "bayat_seri_dd": dd["bayat_seri_dd"],
             # YASA 6 ZİNCİRİ (fiş 7/8): teşhis üçlüsü buradan `system_telemetry.sonuc_hukmu`ne,
             # oradan fiş üreten beyne gider. Alanlar burada durmazsa teşhis `_realized_drawdown`ın
             # içinde kalır ve fiş yine "seri bayat" cümlesiyle yeniden doğar.
             "gecikme_gun": dd["gecikme_gun"], "egri_yazari": dd["yazar"],
             "yazar_kanit": dd["yazar_kanit"],
             "anlamlilik_hesabi": False}
    if not yeterli or dd["max_dd"] is None:
        dd_olcut = _olcut("olculemedi", dd["max_dd"], dd_esik,
                          "kapanmış işlem + günlük piyasaya-göre sermaye eğrisi", **dd_ek)
    else:
        # ALT SINIR HÜKMÜ — EDGE'in kuyruk bacağıyla BİREBİR aynı kural.
        # İki hüküm aynı olgu hakkında farklı şey söyleyemez: `_realized_drawdown` tek kaynaktı,
        # okuma kuralı da tek olmak zorunda.
        if dd["max_dd"] > RESULT_MAXDD_MAX:
            _dur = "kaldi"
        elif dd["max_dd_alt_sinir"]:
            _dur = "olculemedi"
        else:
            _dur = "gecti"
        dd_olcut = _olcut(_dur, dd["max_dd"], dd_esik,
                          "kapanmış işlem + günlük piyasaya-göre sermaye eğrisi", **dd_ek)

    # --- 4) TOPLAM NET PnL vs ÖDENEN FRİKSİYON --------------------------------------------------
    net = round(sum(pnls), 2) if n else None
    friksiyon = round(sum(costs), 2) if costs else None
    net_esik = (f"toplam net PnL > 0 VE net >= {RESULT_NET_OVER_FRICTION} × ödenen friksiyon "
                f"(n >= {RESULT_N_MIN})")
    net_ek = {"n": n, "toplam_friksiyon": friksiyon, "n_costs": len(costs),
              "oran": (round(net / friksiyon, 3) if (net is not None and friksiyon
                                                     and friksiyon > 0) else None),
              "friksiyon_kapsam": ("costs = giriş kayması + çıkış kayması + ÇIKIŞ komisyonu; GİRİŞ "
                                   "komisyonu HARİÇ (goal.yaml'da komisyon 0 olduğu sürece fark "
                                   "yok) — profit_waterfall ile AYNI beyan"),
              "anlamlilik_hesabi": False}
    if not yeterli or net is None or friksiyon is None:
        net_olcut = _olcut("olculemedi", net, net_esik, kaynak, **net_ek)
    else:
        net_olcut = _olcut("gecti" if (net > 0 and net >= RESULT_NET_OVER_FRICTION * friksiyon)
                           else "kaldi", net, net_esik, kaynak, **net_ek)

    criteria = {"dolar_beklenti": beklenti, "profit_factor": pf_olcut,
                "maks_dusus": dd_olcut, "net_pnl": net_olcut}
    for _c in criteria.values():
        _c["durum"] = EDGE_DURUM_ADI[_c["status"]]      # TEK eşleşme tablosu — iki çeviri = iki hüküm
    passed = sum(1 for c in criteria.values() if c["status"] == "gecti")
    failed = sum(1 for c in criteria.values() if c["status"] == "kaldi")
    unmeasured = sum(1 for c in criteria.values() if c["status"] == "olculemedi")
    zayif = sum(1 for c in criteria.values() if c["status"] == "zayif")
    nn = len(criteria)
    if passed == nn:
        verdict = (f"SONUÇ: {passed}/{nn} sağlandı — dört dolar ölçütünün dördü de eşiği VE "
                   f"anlamlılığı geçti (TAM)")
    else:
        verdict = (f"SONUÇ: {passed}/{nn} sağlandı ({zayif} zayıf, {failed} sağlanmadı, "
                   f"{unmeasured} ölçülemedi) — para kanıtlanmadı")
    # --- BETA-DÜZELTİLMİŞ KOLON ----------------------------------------------
    # NEDEN BEŞİNCİ ÖLÇÜT DEĞİL, KOLON: dört ölçüt bu depoda YAZILI bir sözleşmedir (`passed/4`
    # cümlesi, health.py'nin sonuc_hukmu kapısı, /api/diagnostics tüketicisi ve testler onu dört
    # sayıyor). Beşinci bir ölçüt eklemek, hiçbir eşiği değiştirmeden hükmü kaydırırdı — bu depoda
    # "habersiz hüküm kayması" yasak. Kolon ölçümü YANINA koyar: `hukme_girmez: True` ve sayaçlara
    # (passed/failed/unmeasured/zayif) HİÇ dokunmaz.
    #
    # NE SÖYLER: dört dolar ölçütü "para kazandık mı?" diye sorar, hiçbiri "kazandıysak bu piyasa
    # mıydı?" diye sormaz. 2026-07-30 denetimi bu boşluğu MAJÖR işaretledi: defter −%0,225
    # üretirken aynı pencerelerde SPY +%0,411 koşuyordu ve kazananlar SPY'ın +%1,89 koştuğu
    # pencerelerdeydi. Bu kolon o ölçümün kalıcı hâlidir.
    _ab = trade_alpha_beta()
    beta_kolon = {
        "ort_fark": _ab.get("ort_fark"),
        "ort_islem": _ab.get("ort_islem"),
        "ort_spy": _ab.get("ort_spy"),
        "kazananlarin_spy_ortalamasi": _ab.get("kazananlarin_spy_ortalamasi"),
        "kazanan_n": _ab.get("kazanan_n"),
        "n_olculebilir": _ab.get("n_olculebilir"), "n_olculemeyen": _ab.get("n_olculemeyen"),
        "benchmark": _ab.get("benchmark"), "pencere": _ab.get("pencere"),
        "yontem": _ab.get("yontem"), "neden_bos": _ab.get("neden_bos"),
        "kirilim": _ab.get("kirilim"), "kaynak_kirilim": _ab.get("kaynak_kirilim"),
        "hukme_girmez": True,
        "durum": ("olculemedi" if _ab.get("ort_fark") is None
                  else ("pozitif" if _ab["ort_fark"] > 0 else "negatif")),
        "kapsam": ("işlem başına, AYNI pencerede SPY'a karşı fark — ADVISORY. Dört dolar "
                   "ölçütünün hiçbirini değiştirmez ve passed/failed sayaçlarına girmez; "
                   "'kazandık' cümlesinin beta mı alfa mı olduğunu söyler"),
    }
    # --- KÖTÜMSER İKİZ SÜTUN ----------------------------------------------
    # `beta_duzeltilmis` ile AYNI SINIF: kolon, ölçüt değil. Dört ölçüt bu depoda yazılı bir
    # sözleşmedir (`passed/4`, health.sonuc_hukmu kapısı, /api/diagnostics tüketicisi, testler);
    # beşinci bir ölçüt eklemek hiçbir eşiği değiştirmeden hükmü kaydırırdı. Bu sütun ölçümü
    # YANINA koyar: sayaçlara (passed/failed/unmeasured/zayif) HİÇ dokunmaz.
    _kot = net_kotumser()
    kotumser_kolon = {
        **_kot,
        # 4. ÖLÇÜTÜN İKİZİ: net, ödenen friksiyonun katı olarak kötümser varsayımda da yeterli mi?
        "net_over_friksiyon_kotumser": (
            round(_kot["net_kotumser"] / friksiyon, 3)
            if (_kot.get("net_kotumser") is not None and friksiyon and friksiyon > 0) else None),
        "esik_deger": RESULT_NET_OVER_FRICTION,
        "durum": ("olculemedi" if _kot.get("net_kotumser") is None
                  else ("pozitif" if _kot["net_kotumser"] > 0 else "negatif")),
    }
    # --- CANLI-BEKLENTİ TAVANI KOLONU -----------------------------------------
    # `beta_duzeltilmis`/`net_kotumser` ile AYNI SINIF ve aynı gerekçe: kolon, ölçüt değil. Dört
    # ölçüt bu depoda yazılı bir sözleşmedir (`passed/4`, health.sonuc_hukmu kapısı, testler);
    # beşinci bir ölçüt eklemek hiçbir eşiği değiştirmeden hükmü kaydırırdı. Bu kolon,
    # yazılı ama bugüne kadar hiçbir kodun okumadığı canlı-beklenti tavanı kuralını GÖRÜNÜR yapar.
    return {"criteria": criteria, "passed": passed, "failed": failed,
            "unmeasured": unmeasured, "zayif": zayif, "verdict": verdict,
            "beta_duzeltilmis": beta_kolon,
            "net_kotumser": kotumser_kolon,
            "tavan_durumu": live_expectancy_ceiling(),
            "birim": "USD (başlangıç sermayesi $100.000)",
            "karar_kullanimi": ("rafineri kararları EDGE hükmüne bakar; sermaye artırımı ve "
                                "silahlanma İKİ hükme birden (EDGE + SONUÇ) bakar — ROADMAP §5.1")}


# ---- PORTFÖY ISISI: MASADAKİ TOPLAM RİSK ---------------------------
# NEDEN VAR. Pozisyon başına risk kapılı (max_position_r) ve pozisyon SAYISI kapılı
# (max_open_positions), ama TOPLAM AÇIK RİSK hiçbir yerde tek sayı olarak durmuyordu: beş pozisyon
# × 1R = masada 5R, yani NAV'ın %5'i, ve bu sayı ne panoda ne bir kapıda vardı. `analytics.today`
# `risk_dollars` toplamını `current_exposure_pct` diye taşıyor ama o alan GİRİŞTEKİ riski toplar —
# stop yukarı taşındıkça gerçek risk düşer ve pano olduğundan sıcak görünür.
#
# BU TURDA YALNIZ GÖSTERGEDİR — HİÇBİR KAPIYA BAĞLANMAZ. Isı TAVANI (açık risk ≤ NAV %6-8)
# ilerideki rejim/risk dörtlüsünde default-OFF knob olacak; onu bu turda bağlamak, ölçülmemiş
# bir eşiğin canlı emir akışını kesmesi demekti. Ölçüm ÖNCE, kapı SONRA.
#
# İKİ SAYI BİRDEN, ÇÜNKÜ İKİ AYRI SORU: `acik_risk_dolar` YÜRÜRLÜKTEKİ stopa göredir (trail dahil)
# = "şu an masada ne kadar para var?"; `ilk_stop_riski_dolar` GİRİŞ stopuna göredir = "bu
# pozisyonlar açıldığında ne kadar riske girdik?". Brief'in yazdığı formül (giriş−stop)×adet
# ikincisidir; birincisi "anlık" kelimesinin gerektirdiğidir ve ikisi bir kazanan pozisyonda
# ciddi biçimde ayrışır. İkisi de raporlanır (SAPMA BEYANI: formül genişletildi, değiştirilmedi).
#
# NEGATİF RİSK SIFIRA KISILIR, DİĞER POZİSYONU AFFETMEZ: trail'i girişin üstüne çıkmış bir
# pozisyonun riski negatiftir (kilitlenmiş kâr) — ama o negatif, başka bir pozisyonun açık riskini
# DÜŞÜREMEZ; toplamda mahsup edilse ısı olduğundan soğuk görünürdü. Pozisyon başına max(0, ·).
def portfolio_heat() -> dict:
    """ANLIK PORTFÖY ISISI: Σ max(0, giriş − yürürlükteki stop) × adet / özsermaye.

    Saf okuma (portfolio.json + heartbeat.json). Açık pozisyon yoksa ısı 0.0'dır ve bu bir
    ölçüm boşluğu DEĞİL ölçülmüş gerçektir (`n_pozisyon: 0` yanında durur) — None dönmek
    "bilmiyoruz" derdi, oysa masada gerçekten hiçbir şey yok."""
    pf = store.read_json("portfolio.json", {}) or {}
    hb = store.read_json("heartbeat.json", {}) or {}
    pos = list((pf.get("positions") or {}).values())
    equity = hb.get("equity") or pf.get("cash") or score_mod.START_EQUITY
    try:
        equity = float(equity)
    except (TypeError, ValueError):  # sessiz-yutma: yedek değer başlangıç sermayesidir ve `ozsermaye_kaynagi` hangisinin kullanıldığını dışarı verir
        equity = float(score_mod.START_EQUITY)
    satirlar, toplam, ilk_toplam, eksik = [], 0.0, 0.0, 0
    for p in pos:
        try:
            giris, adet = float(p["entry"]), int(p["qty"])
            stop0 = float(p["stop"])
            trail = float(p.get("trail_stop", stop0))
        except (KeyError, TypeError, ValueError):  # sessiz-yutma: sinyal SAYAÇTIR — satır atlanır ama sayılır, `n_eksik` alanıyla dışarı verilir ve döngüden SONRA tek bir uyarıya çevrilir (döngü içinde uyarmak 5 pozisyonda 5 kez bağırırdı)
            eksik += 1
            continue
        etkin = max(stop0, trail)               # trail asla gevşemez (broker yasası) — savunmacı max
        r_simdi = max(0.0, (giris - etkin) * adet)
        r_ilk = max(0.0, (giris - stop0) * adet)
        toplam += r_simdi
        ilk_toplam += r_ilk
        satirlar.append({"ticker": p.get("ticker"), "adet": adet, "giris": round(giris, 4),
                         "stop": round(stop0, 4), "yururlukteki_stop": round(etkin, 4),
                         "risk_dolar": round(r_simdi, 2), "ilk_stop_riski_dolar": round(r_ilk, 2)})
    if eksik:
        # YASA 4 — SAYAÇ UYARIYA ÇEVRİLİR: eksik alanlı bir pozisyon ısıyı olduğundan SOĞUK
        # gösterir (risk sayıya girmez) ve ısı tavanı İLERİDE kapıya bağlanacak. O gün sessiz
        # bir eksik satır, kapının göremediği bir risk demek olurdu.
        from . import obs
        obs.warn("heat_position_incomplete", n_eksik=eksik, n_pozisyon=len(pos),
                 detail="pozisyon satırında entry/stop/qty eksik ya da biçimsiz — portföy ısısı "
                        "bu pozisyonları SAYMADI (olduğundan soğuk okunur)")
    return {"acik_risk_dolar": round(toplam, 2),
            "ilk_stop_riski_dolar": round(ilk_toplam, 2),
            "ozsermaye": round(equity, 2),
            "isi_pct": round(100.0 * toplam / equity, 3) if equity else None,
            "ilk_stop_isi_pct": round(100.0 * ilk_toplam / equity, 3) if equity else None,
            "n_pozisyon": len(pos), "n_eksik": eksik, "pozisyonlar": satirlar,
            "ozsermaye_kaynagi": ("heartbeat.equity" if hb.get("equity") else
                                  "portfolio.cash" if pf.get("cash") else "score.START_EQUITY"),
            "formul": "Σ max(0, giriş − yürürlükteki stop) × adet / özsermaye",
            "rol": ("YALNIZ GÖSTERGE — bu turda hiçbir kapıya bağlı DEĞİL. Isı TAVANI (açık risk "
                    "≤ NAV %6-8) Hafta 3b'nin Y3 dörtlüsünde default-OFF knob olarak gelir.")}


# ---- DOĞRULAMA ÜÇLÜSÜNÜN OKUMA MODELİ ------------------------------------------
# YASA 6: `validation.py` aday getiri defterini YAZAR; onu BAŞKA bir modülden okuyan taraf burasıdır
# (statik artefakt grafı, kendi yazdığını kendi okuyan modülü tüketici saymaz). Pano bu fonksiyonu
# /api/diagnostics üzerinden görür.
#
# K-CEZASI KALİBRASYONU — DENGELEME REFERANSI (GEVŞETME DEĞİL). Bu dosyanın
# K-cezası okumaları (`validation_trio`nun DSR n_trials'ı; `dead_families`in "K büyür → p_required
# yükselir" beyanı; cezanın kendisi `probgate.py::PairedProbabilisticGate.p_required_for`) bilinçli olarak SIKI gelenektedir
# (Harvey-Liu-Zhu 2016 "kesitte t>3" ailesi; DSR da [Bailey & López de Prado] aynı damar).
# Literatürün DENGELEME bacağı da adresli dursun: Andrew Y. Chen (2022), "Do t-Statistic Hurdles
# Need to Be Raised?" — yayımlanmış kesit-öngörücü popülasyonunda yanlış-keşif oranının sanılandan
# KÜÇÜK olduğunu, çıtayı körce yükseltmenin bedelinin kaçırılan gerçek edge (yanlış-red) olduğunu,
# hurdle seçiminin iki hata türü arasında bir DENGE olduğunu savunur. BU NOT BİR GEVŞETME DEĞİLDİR:
# hiçbir eşik/formül değişmedi (eşik sonradan değişmez; kill-list dokunulmaz) — not, K-cezası
# şeffaflığının METODOLOJİ bacağıdır (yüzey bacağı: pano/F13). Künye bellekten yazıldı
# (yazar/yıl/başlıkta eminiz); yayın yeri/nihai sürüm için operatör literatür doğrulaması gerekir
# (UYDURMA YASAĞI şerhi — doğrulanmadan künyeye dergi/cilt EKLENMEZ).
def validation_trio() -> dict:
    """DSR / PBO / sorgu sayacı YAN YANA — panonun "doğrulama" satırının tek kaynağı.

    DSR burada CANLI DEFTERE uygulanır (kapı kayıtlarındaki adaylara değil): "bu sistemin
    gerçekleşen Sharpe'ı, bugüne kadar sorulmuş SORU SAYISI karşısında hâlâ şaşırtıcı mı?"
    Deneme sayısı N iki kanaldan toplanır ve ikisi de görünür kalır — aşınma defterinin ömür-boyu
    sorgu sayısı (oturumlar arası) + kapı kayıtlarındaki k_probes toplamı (oturum içi). İkisini
    toplamak KASITLIDIR: aynı pencereye sorulan her soru, ister aylar arayla ister aynı gece,
    seçilim baskısına eşit katkı yapar.

    RETRO DAMGA SINIRI AÇIKÇA TAŞINIR: aşınma sayacı 2026-07-28'de başladı, ondan önceki ~38
    hipotez sayıya GİRMEZ — yani N bir ALT SINIRdır ve `n_trials_beyan` bunu söyler."""
    from . import oos_erosion, validation, dataset
    trades = _trades()
    ret = [float(t["pnl_dollars"]) / float(score_mod.START_EQUITY)
           for t in trades if t.get("pnl_dollars") is not None]
    # AŞINMA SAYISI `oos_erosion.report()`TAN OKUNUR, dosyadan DEĞİL: toplamı burada yeniden
    # hesaplamak aynı sayının ikinci bir tanımını doğururdu (ve `oos_erosion.json`ın beyan edilmiş
    # lağım durumunu da bozardı — dosyanın tek dış tüketicisi o erişimci fonksiyondur).
    er = oos_erosion.report() or {}
    sorgu = int(er.get("toplam_sorgu") or 0)
    kp = 0
    for h in memory.all_hypotheses():
        bt = h.get("backtest") or {}
        kp += int(bt.get("k_probes") or 0)
    n_trials = sorgu + kp
    # DOSYA ADI LİTERAL YAZILIR (sabitten ya da `validation.ledger()` üzerinden türetilmez):
    # `codelaw.artifact_graph` STATİK bir graftır ve bir fonksiyonun içindeki okumayı o fonksiyonu
    # BARINDIRAN modüle sayar. `validation.ledger()` çağrılsaydı defterin tek okuyucusu yine
    # `validation.py` (yazarı) olurdu ve artefakt "okuyucusu yok" diye görünürdü — YASA 6 ihlali.
    # api.py'deki `component_ic.json` satırı aynı gerekçeyle literal yazılmıştır.
    defter = store.read_jsonl("validation_ledger.jsonl", limit=validation.LEDGER_CAP)
    # ---- PBO PENCERE BAŞINA (HOLDOUT ROTASYONU R1) ----------------------------------
    # PBO/CSCV, N adayı AYNI zaman ızgarasında yarıştırıp "en iyi seçilenin OOS sırası" dağılımını
    # ölçer. Rotasyondan sonra defter İKİ FARKLI SINAV KÂĞIDININ satırlarını taşıyor: R0 satırlarının
    # serileri 2023-07→2025-12 ızgarasında, R1 satırlarının serileri 2024-01→2026-04 ızgarasında.
    # Havuzlamak, ledgers sözleşmesinin AYNI TURDA yazdığı uyarıyı (iki `pencere_id` = iki popülasyon)
    # tüketici tarafında ihlal etmek olurdu — ve sessizce: `_matris` ızgaraları BİRLEŞTİRİR, yani
    # kesişmeyen iki dönem tek matriste sıfırlarla dolar ve PBO gürültüyü "aşırı-uydurma yok" diye
    # okur. Bir sözleşme uyarısı, yalnız onu UYGULAYAN bir tüketiciyle birlikte gerçektir.
    # Damgasız satır = R1 ÖNCESİ (retro damga yasağı: geriye dönük doldurulmaz).
    guncel = [r for r in defter if r.get("pencere_id") == dataset.ROTATION_ID]
    onceki = [r for r in defter if r.get("pencere_id") != dataset.ROTATION_ID]
    return {"dsr_canli": validation.deflated_sharpe(ret, max(1, n_trials)),
            "n_trials": n_trials, "erosion_sorgu": sorgu, "k_probes_toplam": kp,
            "n_trials_beyan": ("ALT SINIR — aşınma sayacı " + str(er.get("sayac_baslangici") or "?")
                               + " tarihinde başladı; ondan önceki hipotezler retro damga yasağı "
                                 "gereği sayılmadı"),
            # PBO YALNIZ YÜRÜRLÜKTEKİ PENCEREDEN. Satır sayısı `PBO_MIN_ADAY` altındaysa
            # `pbo_cscv` zaten dürüstçe ölçmez — bu, havuzlayıp uydurmaktan İYİDİR.
            "pbo": validation.pbo_cscv(guncel),
            "pencere_id": dataset.ROTATION_ID, "rotasyon_tarihi": dataset.ROTATION_DATE,
            "kiyas_uyarisi": dataset.PENCERE_KIYAS_UYARISI,
            "defter": {"n_kayit": len(defter), "dosya": validation.LEDGER_FILE,
                       "son": (defter[-1].get("ts") if defter else None),
                       # PANO DOĞRULAMA SATIRI PENCEREYİ AYRI AYRI GÖRÜR: "PBO 12 kayıttan" ile
                       # "PBO yürürlükteki pencerenin 2 kaydından" aynı cümle değildir.
                       "n_kayit_guncel_pencere": len(guncel),
                       "n_kayit_onceki_pencereler": len(onceki),
                       "beyan": ("defter BUGÜNDEN sayar — geçmiş kapı kayıtları seri taşımıyordu "
                                 "ve geriye dönük üretilmedi. PBO YALNIZ `pencere_id="
                                 + str(dataset.ROTATION_ID) + "` satırlarından hesaplanır: iki "
                                 "pencere iki AYRI sınav kâğıdıdır ve tek ızgarada havuzlanamaz "
                                 "(ledgers sözleşmesi). Önceki pencere satırları SİLİNMEDİ, "
                                 "PBO paydasına GİRMEZ.")},
            # ROL GÜNCELLENDİ — "ADVISORY" hâlâ DOĞRU ama artık YALNIZ
            # KAPI İÇİN doğru: `_gate_eval.passes` semantiği değişmedi (DSR o satırın altında
            # üretilir). Sertlik SHIP yolunda ve MOD-FARKINDALIKLI; ayrıca bu fonksiyonun DSR'si
            # Faz-6 kilit zincirinin BEŞİNCİ kilidini besliyor. Eski cümleyi bırakmak, sertleşmiş
            # iki kapıyı panoda tavsiye gibi göstermek olurdu.
            "rol": ("KAPI (`_gate_eval.passes`) İÇİN ÜÇÜ DE ADVISORY — o semantik DEĞİŞMEDİ. SHIP "
                    "yolu (v130): DSR mod-farkındalıklı SERT (kâğıt=damga · gerçek-para=fail-closed), "
                    "PBO ölçülebilirse İKİ MODDA SERT. Bu DSR ayrıca Faz-6 zincirinin 5. kilidi")}


# ==================================================================================================
# HERMES ETKİNLEŞTİRME PAKETİ — ÜRETİCİLER
# İlke (operatör yönü): "daha aktif ≠ daha çok hipotez; daha az + TAM DÖNGÜLÜ + KENDİ KARNESİNİ
# GÖREN". Buradaki her fonksiyon, hermes'in bugüne kadar GÖRMEDİĞİ ölçülmüş bir gerçeği prompt'un
# kanıt paketine taşımak için vardır — yeni bileşen değil, kopuk kablonun bağlanması.
# ==================================================================================================

# TAHMİN-İSABET BANDI ---------------------------------------------------------------------
# NEDEN. `probgate.refresh_meta_calibration` predicted/realized çiftlerinin MEDYAN ORANINI zaten
# ölçüyor ve kapı eşiğini sıkılaştırıyor. Ama hermes bunu HİÇ GÖRMÜYOR: kendi tahminlerinin ne
# kadar tuttuğunu bilmeden her tur yeni bir predicted_delta yazıyor. Bant, o karnenin hermes'e
# geri verilmesidir — "kendi karnesini gören" maddesinin somut hâli.
#
# TABANIN GERÇEĞİ: bugün defterde TEK bir gerçek çift var (v4 rollback: öngörü +0,0593, gerçekleşen
# −0,0364, oran −0,61). Bir çiftle "kalibrasyon bandı" demek uydurma olurdu; o yüzden bant n<
# A4_BAND_MIN_N iken SAYI VERMEZ, "n=1, bant ÖLÇÜLEMEDİ" der ve tek çiftin kendisini gösterir.
# Bu, boş bir karneyi "her şey yolunda" diye sunmamanın tek yoludur.
A4_BAND_MIN_N = 3          # bunun altında bant yok — yalnız çiftlerin listesi ve "ölçülemedi" hükmü
A4_BAND_TARGET_RATIO = 1.0  # gerçekleşen/öngörülen = 1 ⇔ kusursuz kalibrasyon


def prediction_accuracy_band() -> dict:
    """hermes'in öngörülen ΔS'i ile GERÇEKLEŞEN ΔS'inin karnesi.

    Çift kaynakları (ikisi de like-for-like, yani AYNI ölçüm yasasıyla):
      * rollback kayıtları — `hypotheses.jsonl`ın `realized_delta` alanı (writeback_outcome yazar)
      * ship ölçümleri     — aynı alan; ship'ten sonra ölçülen gerçekleşme

    `oran` = gerçekleşen/öngörülen. 1'in ALTI sistematik iyimserliktir (kapı bunu extra_p ile
    cezalandırır); NEGATİF oran, tahminin YÖNÜNÜN bile yanlış olduğunu söyler ve ayrı sayılır —
    büyüklük hatasıyla yön hatası aynı sayıda erirse hermes "biraz iyimserim" diye okur, oysa
    bugünkü tek kayıt "ters yöne gitti" diyor.

    PARA ÖLÇEĞİ SÜTUNU (`shadowlaw.realized_usd`in okuyucusu, YASA 6).
    `oran` BİLEŞİK ölçekte bir sayıdır: `realized_delta`yı rollback eski bileşik skordan yazıyor
    (`probgate.refresh_meta_calibration` bunu `olcek_borcu` alanıyla adıyla beyan ediyor). Yani bu
    karne "SKOR ne kadar tuttu?" sorusunu cevaplıyor, "PARA ne yaptı?" sorusunu DEĞİL — ve ikisi
    ters işaretli olabilir. Sütun o ikinci cetveli yanına koyar: her çift, ROLLBACK'İN KENDİ
    popülasyon yasasıyla (`strategy_version` eşleşmesi — `rollback.check_and_rollback` aynen böyle
    diliyor) dolar tarafından da okunur. Yeni mekanizma YOK: aynı defter, aynı dilimleme, ikinci
    bir birim. `celiski=True` = skor iyileşme derken para tersini söylüyor; hükmü yoktur, GÖRÜNÜR
    kılar. Ölçülemeyen taraf None kalır (UYDURMA YASAĞI)."""
    from . import shadowlaw
    hyps = memory.all_hypotheses()
    _tr = _trades()
    _g = config.goal()

    def _para_of(version_to) -> dict | None:
        """Bir sürümün canlı defterdeki dolar karnesi — rollback'in `cur_trades` dilimiyle AYNI.

        Blok `money_score_detail`in KENDİ çıktısından okunur (ayrı bir hesap kurulmaz): kapının
        gördüğü sözlük ile karnenin gördüğü sözlük AYNI olmak zorunda, yoksa iki cetvel sessizce
        ayrışır. `money_score_detail` min_sample altında da bu bloğu döndürür — bu yüzden skor
        None iken bile para okunabilir."""
        if version_to is None:
            return None
        rows = [t for t in _tr if t.get("strategy_version") == version_to]
        return shadowlaw.money_score_detail(rows, _g)["realized_usd"] if rows else None

    ciftler = []
    for h in hyps:
        pd_, rd_ = h.get("predicted_delta"), h.get("realized_delta")
        if pd_ is None or rd_ is None:
            continue
        try:
            p, r = float(pd_), float(rd_)
        except (TypeError, ValueError):  # sessiz-yutma: biçimsiz tek çift; kalibrasyon bandı n'i AZALIR ve n çıktıda görünür (gizli kayıp yok)
            continue
        if abs(p) < 1e-9:
            continue
        _pb = _para_of(h.get("version_to"))
        _usd = (_pb or {}).get("pnl_usd")
        ciftler.append({"id": h.get("id"), "ts": h.get("ts"), "variable": h.get("variable"),
                        "status": h.get("status"), "predicted": round(p, 4),
                        "realized": round(r, 4), "oran": round(r / p, 3),
                        "yon_dogru": bool((r > 0) == (p > 0)),
                        # --- para sütunu ---
                        "para_usd": _usd, "para_n": (_pb or {}).get("n_pnl", 0),
                        # İŞARETSİZ (0) taraf ÇELİŞKİ ÜRETEMEZ: sıfırı "kötü" saymak, ölçülmemiş bir
                        # yönü ölçülmüş gibi raporlamak olurdu.
                        "celiski": (None if (_usd is None or r == 0 or _usd == 0)
                                    else bool((r > 0) != (_usd > 0)))})
    n = len(ciftler)
    _para_olculen = [c for c in ciftler if c["celiski"] is not None]
    out = {"n": n, "min_n": A4_BAND_MIN_N, "ciftler": ciftler[-10:],
           "hedef_oran": A4_BAND_TARGET_RATIO,
           "kaynak": "hypotheses.jsonl predicted_delta ↔ realized_delta (rollback + ship ölçümleri)",
           "para_olcegi": {
               "n_olculen": len(_para_olculen),
               "n_celiski": sum(1 for c in _para_olculen if c["celiski"]),
               "celiskili_idler": [c["id"] for c in _para_olculen if c["celiski"]][:10],
               "birim": "USD", "hukum_verir": False,
               "kaynak": ("shadowlaw.realized_usd — trades.jsonl'ın `strategy_version` dilimi "
                          "(rollback.check_and_rollback ile AYNI popülasyon yasası)"),
               "beyan": ("`oran` BİLEŞİK ölçektedir (realized_delta rollback'ten gelir), bu sütun "
                         "DOLAR. Çelişki = skor iyileşme derken paranın tersini söylemesi; hüküm "
                         "vermez, ölçek borcunun (probgate.olcek_borcu) görünür yüzüdür."),
               "hukum": ("PARA TARAFI ÖLÇÜLEMEDİ — hiçbir çiftin sürümü canlı defterde "
                         "`pnl_dollars`lı satır taşımıyor" if not _para_olculen else
                         ("ÇELİŞKİ YOK — ölçülen çiftlerde skor ve para AYNI yönü gösteriyor"
                          if not any(c["celiski"] for c in _para_olculen) else
                          "ÇELİŞKİ VAR — skor ile para ters yönü gösteren çift(ler) mevcut"))}}
    if n == 0:
        out.update({"band": None, "hukum": "HİÇ ÇİFT YOK — hermes'in tahmin isabeti ÖLÇÜLMEMİŞ "
                                          "(ship olmadan gerçekleşme yazılamaz)", "yon_isabeti": None})
        return out
    oranlar = sorted(c["oran"] for c in ciftler)
    yon = sum(1 for c in ciftler if c["yon_dogru"])
    out["yon_isabeti"] = {"dogru": yon, "n": n, "oran": round(yon / n, 3)}
    if n < A4_BAND_MIN_N:
        out.update({"band": None,
                    "hukum": (f"n={n} < {A4_BAND_MIN_N} — BANT ÖLÇÜLEMEDİ (sıfır değil, bilinmiyor). "
                              f"Eldeki tek kanıt: " + "; ".join(
                                  f"{c['id']} öngörü {c['predicted']:+} → gerçek {c['realized']:+} "
                                  f"(oran {c['oran']}, yön {'DOĞRU' if c['yon_dogru'] else 'TERS'})"
                                  for c in ciftler))})
        return out
    import statistics as _st
    med = float(_st.median(oranlar))
    out.update({"band": {"medyan_oran": round(med, 3),
                         "p25": round(oranlar[max(0, int(0.25 * (n - 1)))], 3),
                         "p75": round(oranlar[min(n - 1, int(0.75 * (n - 1)))], 3),
                         "min": round(oranlar[0], 3), "max": round(oranlar[-1], 3)},
                "hukum": ("SİSTEMATİK İYİMSER — öngörülerin medyanı gerçekleşmenin üstünde"
                          if med < 0.75 else
                          "KALİBRE — medyan oran 1'in etrafında" if med <= 1.25 else
                          "SİSTEMATİK KARAMSAR — gerçekleşme öngörüyü aşıyor")})
    return out


# RET-NEDENİ AİLE HAFIZASI -------------------------------------------------------------------
# NEDEN. Kapı kayıtlarındaki `why`/`reject_reasons` alanları 41 hipotezlik bir mezarlık taşıyor ama
# hermes onları GÖRMÜYOR; her tur aynı ailelere dönüyor. ÖLÇÜLDÜ: 41 hipotezin 21'i (%51) TEK bir
# değişkende — `stop_loss_atr_mult` — ve hepsi reddedildi. Buna karşılık bounds.yaml'daki düğmelerin
# YARISI defterde HİÇ görünmedi. "Ölü aile" özeti + "hiç önerilmemiş düğmeler" satırı, bu iki
# gerçeği prompt'a taşır.
DEAD_FAMILY_MIN_N = 3      # bir aileyi "ölü" ilan etmek için gereken en az deneme sayısı


def _knob_family(variable: str | None) -> str:
    """`entry.rs_rating_min@trend_up` → `entry.rs_rating_min` (rejim eki ailenin parçası değildir);
    `exit.profit_target_r` → `exit.profit_target_r`. Aile = KNOB kimliği."""
    v = str(variable or "?").strip()
    return v.split("@", 1)[0] if "@" in v else v


def dead_families() -> dict:
    """Reddedilmiş aileler + hiç denenmemiş düğmeler + YAPMA listesi — hermes'in kayıp hafızası.

    "Ölü aile": DEAD_FAMILY_MIN_N ya da daha çok denenmiş ve HİÇ ship'e ulaşmamış knob. Bu bir YASAK
    değildir (kapı tek hakem kalır) — bir MALİYET bilgisidir: aynı aileye n'inci kez dönmek, aile
    hata bütçesini (K) büyütür ve p_required'ı yükseltir, yani sıradaki adayı kendi elleriyle
    zorlaştırır. Beyan: sayılar defterin KENDİSİNDEN gelir, eşik dışında hiçbir yargı katılmaz."""
    from collections import Counter
    hyps = memory.all_hypotheses()
    aile: dict[str, dict] = {}
    for h in hyps:
        f = _knob_family(h.get("variable"))
        a = aile.setdefault(f, {"n": 0, "shipped": 0, "durumlar": Counter(), "son_ts": None,
                               "denenen_degerler": []})
        a["n"] += 1
        st = str(h.get("status") or "?")
        a["durumlar"][st] += 1
        if st in ("live", "promoted", "rolled_back"):
            a["shipped"] += 1
        if h.get("ts") and (a["son_ts"] is None or str(h["ts"]) > a["son_ts"]):
            a["son_ts"] = str(h["ts"])
        if h.get("new") is not None and h["new"] not in a["denenen_degerler"]:
            a["denenen_degerler"].append(h["new"])
    olu = {f: {"denendi": a["n"], "ship": a["shipped"], "son": (a["son_ts"] or "")[:10],
               "durumlar": dict(a["durumlar"]),
               "denenen_degerler": a["denenen_degerler"][:8]}
           for f, a in aile.items() if a["n"] >= DEAD_FAMILY_MIN_N and a["shipped"] == 0}
    # HİÇ ÖNERİLMEMİŞ DÜĞMELER — kopukluk avının bulgusu (bounds 24 düğmeden 10'u; sayı DİNAMİK
    # okunur, sabitlenmez: sonraki turlar bounds'a satır ekliyor ve donmuş bir sayı yalan söylerdi).
    try:
        tum = sorted(config.bounds().keys())
    except Exception as e:
        from . import obs as _o
        _o.warn("dead_families_bounds_unreadable", error=f"{type(e).__name__}: {e}",
                detail="bounds okunamadı — 'hiç önerilmemiş düğme' satırı ÜRETİLMEDİ (uydurulmadı)")
        tum = []
    denenmis = {_knob_family(h.get("variable")) for h in hyps}
    hic = [k for k in tum if k not in denenmis]
    return {
        "n_hipotez": len(hyps), "n_aile": len(aile),
        "olu_aileler": dict(sorted(olu.items(), key=lambda kv: -kv[1]["denendi"])),
        "en_yogun_aile": (max(aile.items(), key=lambda kv: kv[1]["n"])[0] if aile else None),
        "en_yogun_pay": (round(max(a["n"] for a in aile.values()) / len(hyps), 3) if hyps else None),
        "hic_onerilmemis_dugmeler": hic,
        "hic_onerilmemis_sayi": f"{len(hic)}/{len(tum)}" if tum else "bounds okunamadı",
        "beyan": ("ölü aile = >= " + str(DEAD_FAMILY_MIN_N) + " deneme, 0 ship. YASAK DEĞİL, MALİYET "
                  "bilgisi: aynı aileye dönmek K'yı (aile hata bütçesi paydası) büyütür ve "
                  "p_required'ı yükseltir."),
    }


# YAPMA LİSTESİNİN MAKİNE-OKUNUR KISA HÂLİ. Kaynağı yol haritasıdır (ölçülmüş/belgeli çürükler).
# NEDEN KODDA: prompt'a giren her satır DETERMİNİSTİK olmalı; yol haritasını ayrıştırmak (markdown → madde)
# sessizce bozulabilecek bir bağımlılıktır ve bozulduğunda hermes YASAK bilgisini kaybederdi. Liste
# kısa tutulur ve yol haritası değişince BURASI da güncellenir (tek satırlık bakım borcu, beyanlı).
DO_NOT_LIST: tuple[str, ...] = (
    "min_score yükseltmek: ölçüldü, havuzu kurutur ve edge getirmez",
    "aynı (variable,value) çiftini yeniden önermek: reject_reasons'da zaten var",
    "stop_loss_atr_mult ailesine dönmek: 21 deneme, 0 ship (en yoğun ölü aile)",
    "evren genişletmek (G1): mid-cap IC ölçüldü, sinyal kalitesi vaat etmiyor",
    "Finviz point-in-time (B-9): net edge görülmeden başlanmaz",
)


def hermes_scorecard() -> dict:
    """TAHMİN İSABETİ + AİLE HAFIZASININ TEK ÇATISI — evidence_pack'in okuduğu ve panonun çizdiği kaynak.

    Adı "karne": içinde hermes'in KENDİ performansı (tahmin isabeti), KENDİ mezarlığı (ölü aileler)
    ve KENDİ kör noktası (hiç denenmemiş düğmeler) var. Üçü bir arada, "daha az + tam-döngülü"
    ilkesinin ölçülebilir hâlidir."""
    out = {"prediction_band": prediction_accuracy_band(), "families": dead_families(),
           "do_not": list(DO_NOT_LIST)}
    out["threshold_curve"] = threshold_cross_note()
    try:
        out["composite_queue"] = composite_queue_status()
    except Exception as e:
        from . import obs as _o
        _o.warn("hermes_scorecard_queue_failed", error=f"{type(e).__name__}: {e}")
        out["composite_queue"] = None
    # KEŞİF PAYI KARNEYE GİRER (YASA 6). `hermes.exploration_share` bugün eklendi ve
    # TEK tüketicisi hermes'in KENDİ istemiydi (`_exploration_sections`) — yani üreteç kendi
    # dağılımını beyne anlatıyor ama OPERATÖR onu hiçbir yerde göremiyordu. Kanıt üretip yalnız
    # kendine tüketmek, bu depoda tekrar tekrar bulunan "üretilip tüketilmeyen kanıt" deseninin
    # ters yönlü hâli: kanıt tüketiliyor ama DENETLENEMİYOR.
    try:
        from . import hermes as _h
        out["kesif_payi"] = _h.exploration_share()
        out["butce"] = {"arama": _h.search_budget(), "dolgu": _h.backfill_budget()}
    except Exception as e:
        from . import obs as _o2
        _o2.warn("hermes_scorecard_exploration_failed", error=f"{type(e).__name__}: {e}",
                 detail="keşif payı/bütçe karneye GİRMEDİ (uydurulmadı)")
        out["kesif_payi"] = None
        out["butce"] = None
    try:
        out["ogrenme_otomasyonu"] = learning_automation()
    except Exception as e:
        from . import obs as _o3
        _o3.warn("hermes_scorecard_automation_failed", error=f"{type(e).__name__}: {e}")
        out["ogrenme_otomasyonu"] = None
    return out


# ---- ÖĞRENME OTOMASYONUNUN DIŞ OKUYUCUSU (YASA 6) ----------------------------------
# `scheduler._learning_cadence` `learning_cadence.json`u, `skills.axis2_cycle` `axis2_status.json`u
# YAZAR; ikisini de BAŞKA bir modülden okuyan taraf burasıdır → /api/diagnostics + /api/hermes.
# DOSYA ADLARI LİTERAL yazılır (`scheduler.LEARN_FILE` üzerinden DEĞİL): `codelaw.artifact_graph`
# statik bir graftır ve sabitten gelen adı çözemez — defter o zaman "okuyucusu yok" görünür ve
# YASA 6 denetimi onu hiç göremez (composite_queue_status'taki notla aynı gerekçe).
#
# NABIZ TAZELİĞİ BURADA HESAPLANIR, `watchdog.report()`ta DEĞİL — AMA BEKÇİ DE ARTIK İZLİYOR.
# Üç mekanizma adı (`shadow_fit`, `axis2_cycle`, `opinion_backfill`) `watchdog.EXPECTED` sözlüğüne
# GİRDİ (shadow_fit/axis2_cycle seans-bağımlı pencere, opinion_backfill haftalık+pay: bütçe
# kısılınca damga atılmadığı için daha geniş), yani MECHANISM_STALE onları da üretebiliyor. Eski
# not "eksik olan yalnız bekçinin penceresi" diyordu; o borç `watchdog.py` tarafında kapandı ve
# buradaki ölçüm bekçinin YERİNE değil YANINDA durur (aşağıdaki gerekçe).
#
# TAZELİK `mechanism_beats.json`DAN OKUNMAZ — VE BU BİLİNÇLİ. GEREKÇE 2026-08-16'DA GÜNCELLENDİ:
# eski gerekçe "o defter `codelaw.DECLARED_SINKS`te beyanlıdır, literal adla okumak beyanı
# bayatlatırdı" diyordu. O gerekçe ARTIK GEÇERSİZ — `mechanism_beats.json` DECLARED_SINKS'ten
# ÇIKARILDI (bkz. codelaw.py, aynı adın geçtiği NOT bloğu) ve dosyanın dış okuyucusu VAR:
# `api._hat_cizelgesi` onu doğrudan okuyup `/api/diagnostics` `cizelge` alanıyla panoya servis
# ediyor. Yani buradan okumak bugün hiçbir beyanı bayatlatmazdı.
# KARAR YİNE DE AYNI KALIYOR, ÇÜNKÜ İKİNCİ GEREKÇE HÂLÂ DOĞRU: nabız yalnız "koştu mu" der;
# kadansın KENDİ damgası "ne çıktı"yı da taşır ve bu ekranın sorusu tam olarak budur. Yani seçim
# artık bir yasa kısıtı değil, BİLGİ İÇERİĞİ tercihidir:
#   shadow_fit       → shadow_model.json  `fit_attempt_ts`  (training_status üzerinden)
#   axis2_cycle      → axis2_status.json  `ts`
#   opinion_backfill → learning_cadence.json `ts` + `dolgu`
LEARN_STALE_S = 4 * 24 * 3600      # seans-bağımlı pencere (uzun hafta sonu + tatil toleransı)


def learning_automation() -> dict:
    """ÖĞRENME OTOMASYONUNUN TEK KARNE SATIRI: antrenman + Eksen-2 + dolgu, üçü bir arada.

    Ölçülemeyen alan None (uydurma yasağı). Kadans hiç koşmadıysa `son_kosu` None döner ve
    `durum` bunu ADIYLA söyler — boş bir sözlük "her şey yolunda" gibi okunurdu."""
    from . import shadow_model as _sm
    doc = store.read_json("learning_cadence.json", None)
    ax = store.read_json("axis2_status.json", None)
    egitim = _sm.training_status()
    now = dt.datetime.now(dt.timezone.utc)

    def _yas(ts) -> dict:
        """ISO damgadan tazelik satırı. Damga yoksa/bozuksa `hic_kosmadi` — 0 saat DEĞİL, çünkü
        "az önce koştu" ile "hiç koşmadı" aynı sayıya katlanırsa duruş taze görünür."""
        try:
            gap = (now - dt.datetime.fromisoformat(str(ts))).total_seconds()
        except (TypeError, ValueError):  # sessiz-yutma: sonuç KAYDA GEÇİYOR (hic_kosmadi=True) — bozuk/eksik damga dürüstçe "hiç koşmadı" sayılır, bilgi kaybolmaz
            return {"gecen_saat": None, "pencere_saat": round(LEARN_STALE_S / 3600, 1),
                    "bayat": None, "hic_kosmadi": True}
        return {"gecen_saat": round(gap / 3600, 1),
                "pencere_saat": round(LEARN_STALE_S / 3600, 1),
                "bayat": bool(gap > LEARN_STALE_S), "hic_kosmadi": False}

    nabiz = {"shadow_fit": _yas(egitim.get("son_deneme_ts")),
             "axis2_cycle": _yas((ax or {}).get("ts")),
             "opinion_backfill": _yas((doc or {}).get("ts"))}
    try:
        from . import hermes as _h
        kuyruk = _h.backfill_queue()
    except Exception as e:
        from . import obs as _o
        _o.warn("learning_automation_queue_failed", error=f"{type(e).__name__}: {e}")
        kuyruk = None
    return {
        "antrenman": egitim,
        "dolgu_kuyrugu": kuyruk,
        "eksen2": (None if not ax else
                   {"ts": ax.get("ts"), "uretilen": len(ax.get("uretilen") or []),
                    "kaydedilen": len(ax.get("kaydedilen") or []),
                    "bekleyen_toplam": ax.get("bekleyen_toplam"),
                    "kovalar": (ax.get("teshis") or {}).get("sayim"),
                    "esik": (ax.get("teshis") or {}).get("esik"),
                    "otomatik_uygulanan": len((ax.get("otomatik") or {}).get("uygulanan") or [])}),
        "son_kosu": (None if not doc else
                     {"session": doc.get("session"), "ts": doc.get("ts"),
                      "antrenman": doc.get("antrenman"), "dolgu": doc.get("dolgu")}),
        "nabiz": nabiz,
        "durum": ("kadans HİÇ koşmadı — zamanlayıcı seans-sonrası kancası tetiklenmemiş"
                  if not doc else "koştu"),
        # PANODA GÖRÜNÜR METİN (app.js `RENDER` → "Bekçi notu"). Bu yüzden içeriği ölçülmüş
        # olmak ZORUNDA: eski hâli "mechanism_beats.json beyanlı bir lağımdır ve dışarıdan
        # okunmaz" diyordu — dosya DECLARED_SINKS'ten çıkarıldıktan ve `api._hat_cizelgesi`
        # onu panoya taşıdıktan sonra bu cümle operatöre YANLIŞ bilgi veriyordu (2026-08-16).
        "bekci_notu": ("bu üç ad `watchdog.EXPECTED` sözlüğünde VAR — `beat()` yazılıyor ve "
                       "MECHANISM_STALE onları izliyor. Buradaki tazelik yine de kadansların "
                       "KENDİ damgalarından ölçülür: kadans damgası nabızdan daha bilgilidir — "
                       "yalnız 'koştu mu' değil 'ne çıktı'. Nabızların kendisi panoda ayrıca "
                       "var (çizelge kartı, /api/diagnostics `cizelge`). İki ölçüm rakip "
                       "değil, tamamlayıcı."),
    }


def composite_queue_status() -> dict:
    """Bileşik öneri kuyruğunun durumu (bekleyen/ölçülen/haftalık bütçe kalanı).

    YASA 6: `hermes_composite.py` deftere YAZAR; onu BAŞKA bir modülden okuyan taraf burasıdır.
    DOSYA ADI LİTERAL yazılır (`hermes_composite.QUEUE_FILE` üzerinden DEĞİL): `codelaw.artifact_graph`
    statik bir graftır ve sabitten gelen adı çözemez — defter o zaman "okuyucusu yok" görünür ve
    YASA 6 denetimi onu hiç göremez (validation_trio'daki not ile aynı gerekçe)."""
    from . import hermes_composite
    return hermes_composite.queue_status(store.read_jsonl("composite_queue.jsonl"))


def threshold_cross_note() -> dict | None:
    """Eşik eğrisinin ÇAPRAZ-NOTLU kısa özeti — evidence_pack'e giden hâli.

    YASA 6: `threshold_curve.py` dosyayı yazar; onu BAŞKA bir modülden okuyan taraf burasıdır.
    ÇAPRAZ NOT PROMPTA MUTLAKA GİRER: eğrinin kendisi "eşiği yükselt" der gibi okunur (dilim
    istatistiği eşikle birlikte yükselir) ama 2026-07-28 replay'i tam tersini ölçtü — SEÇİM ETKİSİ
    ≠ SİSTEM ETKİSİ. Notu düşürüp yalnız sayıları prompt'a koymak, hermes'i çürütülmüş bir
    hipoteze davet etmek olurdu."""
    doc = store.read_json("threshold_curve.json", None)
    if not doc:
        return None
    gercek = (doc.get("egri") or {}).get("gercek") or []
    satir = []
    for h in gercek:
        fw = (h.get("ileri_getiri") or {}).get("20") or (h.get("ileri_getiri") or {}).get("5") or {}
        if (fw.get("n") or 0) >= (doc.get("min_n") or 10):
            satir.append({"esik": h.get("esik"), "n": fw.get("n"), "ort": fw.get("ort")})
    return {"canli_min_score": doc.get("canli_min_score"), "n_gozlem": doc.get("n_gozlem"),
            "verdict": doc.get("verdict"), "capraz_not": doc.get("capraz_not"),
            "egri_ozet": satir[:6],
            "ufuk": "ileri getiri @20 bar (yoksa @5) — gerçek katman, cf hariç"}


# ---- GÖLGE-VARYANT DEFTERİNİN DIŞ OKUYUCUSU -------------------------
# YASA 6 + `codelaw.DECLARED_SINKS`ten ÇIKARMANIN ŞARTI: defteri BAŞKA bir modül okumalı. Sadeleştirme
# turu beyanı süreliydi ("pano/api tüketicisi sonraya devredildi"); devir burada tamamlanıyor.
# DOSYA ADI LİTERAL: `codelaw.artifact_graph` statik bir graftır ve `shadow_variants.LEDGER`
# üzerinden okumak, okuyucuyu yine yazarın kendisi gibi gösterirdi (bkz. validation_trio'daki not).
def shadow_variant_summary(days: int = 10) -> dict:
    """Panonun gölge-varyant kartı: varyant başına SON KARAR + KÜMÜLATİF AYRIŞMA sayısı.

    BOŞ DEFTER SAHTE BİR 'HER ŞEY YOLUNDA' GÖSTERMEZ — `durum` alanı ne eksik olduğunu söyler.
    `k_variants` kartta görünür çünkü "en iyi varyant" okuması çoklu-karşılaştırma paydası olmadan
    kazananın-lanetini görmezden gelir."""
    from . import shadow_variants
    rows = store.read_jsonl("shadow_variants.jsonl")
    ozet = shadow_variants.summarize(rows, days=days)
    son_karar = {}
    for r in rows:
        vid = str(r.get("variant") or "?")
        prev = son_karar.get(vid)
        if prev is None or str(r.get("date") or "") >= prev["date"]:
            son_karar[vid] = {
                "date": str(r.get("date") or ""), "label": r.get("label"),
                "signal_n": r.get("signal_n"), "would_arm_n": r.get("would_arm_n"),
                "only_variant": len(r.get("only_variant") or []),
                "only_live": len(r.get("only_live") or []),
            }
    ayrisma = {vid: (v.get("only_variant_n", 0) + v.get("only_live_n", 0))
               for vid, v in (ozet.get("per_variant") or {}).items()}
    return {
        "durum": ("DEFTER BOŞ — ilk satırlar ilk EOD döngüsünde doğar (loop P3 kancası); "
                  f"{ozet.get('variants')} varyant tanımlı" if not rows else "dolu"),
        "n_satir": len(rows), "n_gun": ozet.get("days"), "son_tarih": ozet.get("last_date"),
        "k_variants": ozet.get("k_variants"), "gates_applied": ozet.get("gates_applied"),
        "son_karar": son_karar, "kumulatif_ayrisma": ayrisma,
        "per_variant": ozet.get("per_variant"),
        "rol": "KÂĞIT DEFTER — ship yolu YOKTUR; k_variants çoklu-karşılaştırma paydasıdır",
    }


# ---- GÖLGE YASA v2'NİN PANO/API YÜZEYİ ----------------------------------------------------
def _dd_veto_okumasi() -> dict:
    """`DD_VETO_MARGIN` NASIL OKUNUR — tek cümlelik ilişki beyanı.

    NEDEN VAR. Marj panoda/kayıtlarda ÇIPLAK bir sayı olarak duruyordu ve bir ölçüm raporunda tam
    da korkulan biçimde okundu: MUTLAK bir M2M düşüşü (%7,2) o sayıyla kıyaslanıp 'ihlal' yazıldı.
    Oysa marj hiçbir zaman bir düşüş TAVANI değildi — `reflect._gate_eval`in
    veto koşulu `candidate_dd > incumbent_dd + marj`dır, yani marj İKİ ADAY ARASINDAKİ FARKA
    uygulanır ve tek yönlüdür. Mutlak okumanın çıpası AYRI bir sayıdır: `goal.max_drawdown`.

    MARJ DA YAZILMAZ, OKUNUR: değeri tek kaynaktan (`shadowlaw.DD_VETO_MARGIN`) alınır ve
    `marj` alanında döner. Bu docstring'e bir sayı gömmek, kendi öğüdünü çiğnemek olurdu —
    nitekim eski hâli marjı "(0,04)" diye anıyordu ve sabit o değerde değildi.

    ORAN ÖLÇÜLÜR, YAZILMAZ: tavan dosyadan (goal.yaml) okunur ve oran her çağrıda hesaplanır.
    Böylece operatör bir gün bütçeyi değiştirirse bu satır sessizce yalan söylemez. Tavan
    okunamazsa alan None + `tavan_neden`dir (UYDURMA YASAĞI); marj yine yazılır çünkü marjın
    kendisi koddaki sabittir ve okunamamış bir bütçe onu geçersiz kılmaz."""
    from . import shadowlaw
    marj = float(shadowlaw.DD_VETO_MARGIN)
    tavan, oran, neden = None, None, None
    try:
        tavan = float(config.goal()["max_drawdown"])
    except (OSError, ValueError, KeyError, TypeError) as e:
        neden = f"goal.max_drawdown okunamadı: {type(e).__name__}: {e}"
    if tavan:
        oran = round(marj / tavan, 4)
    return {
        "marj": marj,
        "tip": "GÖRECE MARJ — mutlak düşüş tavanı DEĞİL",
        "kural": "veto koşulu: candidate_dd > incumbent_dd + marj (reflect._gate_eval, TEK YÖNLÜ)",
        "mutlak_tavan": tavan, "mutlak_tavan_kaynagi": "goal.max_drawdown",
        "tavan_neden": neden,
        "marj_tavan_orani": oran,
        "beyan": (f"DD_VETO_MARGIN ({marj}) bir düşüş TAVANI DEĞİLDİR: mutlak düşüş bütçesi "
                  f"`goal.max_drawdown`dır ("
                  f"{'ölçülemedi — ' + str(neden) if tavan is None else tavan}"
                  f"{'' if oran is None else f', marj onun ölçülen {oran} katı'}) ve marj YALNIZ "
                  f"aday ile incumbent'ın düşüşleri ARASINDAKİ farka uygulanır. MUTLAK bir düşüşü "
                  f"(ör. backtest.mtm_dd_veto'nun ölçtüğü M2M düşüşü) bu marjla kıyaslayan bir "
                  f"rapor, göreli bir marjı mutlak eşik gibi okur — oradaki `ihlal` alanı bir kapı "
                  f"hükmü değil marj-ölçekli bir işarettir ve mutlak okuma goal.max_drawdown'a "
                  f"çıpalanmalıdır."),
    }


def shadow_law_row() -> dict:
    """Büyüklük yasası satırı — panonun tek kaynağı. **TERS GÖLGELEME** (PARA-v3).

    ÖNCEDEN bu satır "v2 olsaydı" diyordu: karar eski bileşik skordaydı, v2 kayda geçiyordu. Yasa
    yeniden tasarlandıktan sonra yön TERSİNE döndü ve satırın işi de tersine döndü:

      (1) YÜRÜRLÜKTEKİ yasa PARA-v3'tür ve `passes`i O üretir (`law_transition: True`),
      (2) ESKİ yasa (bileşik) her değerlendirmede GÖLGE olarak ölçülür ve kayda geçer,
      (3) son kapı kaydında iki yasanın hükmü AYNI mı (ıraksama sayacı) — süreklilik böyle görünür,
      (4) v2 rötuşunun ölçüm kaydı NEDEN v3'e geçildiğinin belgesi olarak DURUR (silinmedi).

    Satırın "GEÇİŞ YAPILDI" demesi ZORUNLU: bir operatör bu satıra bakıp hâlâ eski yasanın koştuğunu
    sanarsa, kapı kayıtlarındaki p'leri yanlış yasanın p'si olarak okur."""
    from . import shadowlaw
    hyps = memory.all_hypotheses()
    son_kayit, ayrisan, sayilan, gecis_oncesi = None, 0, 0, 0
    for h in hyps:
        b = h.get("backtest") or {}
        for pref in ("search", "confirm"):
            sh = b.get(f"{pref}_eski_yasa")
            if not isinstance(sh, dict):
                # GEÇİŞ ÖNCESİ KAYIT: gölge alanı yok ve retro damga yasağı gereği doldurulmaz.
                # Sayılır ama "ıraksama" olarak sayılmaz — ölçülmemiş bir hüküm ıraksayamaz.
                if b.get(f"{pref}_p") is not None:
                    gecis_oncesi += 1
                continue
            sayilan += 1
            gercek = bool(float(b.get(f"{pref}_p") or 0.0) >= float(b.get(f"{pref}_p_required") or 1.0))
            if bool(sh.get("would_pass")) != gercek:
                ayrisan += 1
            son_kayit = {"id": h.get("id"), "dilim": pref, "p_v3": b.get(f"{pref}_p"),
                         "p_eski": sh.get("p"), "p_required": b.get(f"{pref}_p_required"),
                         "v3_gecti": gercek, "eski_gecerdi": sh.get("would_pass"),
                         "yasa_surumu": b.get(f"{pref}_yasa_surumu")}
    return {
        "law_transition": True,
        "yasa_surumu": shadowlaw.YASA_SURUMU, "gecis_tarihi": shadowlaw.YASA_GECIS_TARIHI,
        "aktif_yasa": (f"PARA-v3: {shadowlaw.YASA_METNI} — dd_c ve sharpe_c SKORDAN ÇIKTI, "
                       f"vetolara taşındı"),
        "golge_yasa": f"ESKİ (artık yalnız kayıt): {shadowlaw.OLD_LAW_METNI}",
        "annual_target": shadowlaw.ANNUAL_TARGET_RETURN,
        "money_gate_margin": shadowlaw.MONEY_GATE_MARGIN,
        "gate_margin_eski": 0.02, "margin_scale": shadowlaw.MARGIN_MONEY_SCALE,
        "dd_veto_margin": shadowlaw.DD_VETO_MARGIN,
        # ÇIPLAK SAYININ YANINDA OKUMA KURALI: `dd_veto_margin` tek başına
        # basıldığında mutlak bir düşüş tavanı gibi okunabiliyordu (ve bir raporda öyle okundu).
        # İlişki beyanı artık sayının YANINDA durur; mutlak çıpa goal.yaml'dan ölçülür.
        "dd_veto_okumasi": _dd_veto_okumasi(),
        # PARA payı: yasanın kendi çivisi — v3'te TEK terim olduğu için 1,0 olmak ZORUNDA
        "varyans_payi": {"eski": shadowlaw.MEASURED_V3["eski_paylar"],
                         "v3": shadowlaw.MEASURED_V3["v3_paylar"]},
        "para_payi_eski": shadowlaw.MEASURED_V3["para_payi_eski"],
        "para_payi_v3": shadowlaw.MEASURED_V3["para_payi_v3"],
        "ret_scale_k": shadowlaw.MEASURED_V3["ret_scale_k"],
        "sd_dusus": shadowlaw.MEASURED_V3["sd_dusus"],
        # v2 RÖTUŞU: neden yetmedi (v3'ün gerekçesi — ölçülmüş olumsuz sonuç silinmez)
        "v2_rotusu": {"hedef": shadowlaw.V2_MONEY_SHARE_TARGET,
                      "hedef_tuttu": shadowlaw.MEASURED_V2["target_met"],
                      "deneme_sayisi": shadowlaw.MEASURED_V2["trials"],
                      "en_iyi_para_payi": max(s for _, _, s in shadowlaw.V2_WEIGHT_TRIALS),
                      "hukum": shadowlaw.MEASURED_V2["hukum"],
                      "denemeler": [{"etiket": e, "agirliklar": list(w), "para_payi": s}
                                    for e, w, s in shadowlaw.V2_WEIGHT_TRIALS]},
        "neden_tutmadi": shadowlaw.WHY_40_UNREACHABLE,
        "olcum": {k: shadowlaw.MEASURED_V3[k] for k in
                  ("ts", "n_trades", "span_days", "block_days", "n_boot", "seed",
                   "hedef_pencere", "ret_scale_k", "margin_scale")},
        "golge_kayit_sayisi": sayilan, "iraksayan_kayit": ayrisan,
        "gecis_oncesi_kayit": gecis_oncesi,
        "son_kayit": son_kayit,
        "beyan": ("ÇİFT HESAP, TERS YÖN: her kapı değerlendirmesinde P(ΔS_para>0) KARAR verir, "
                  "ESKİ yasanın bileşik hükmü KAYDA geçer. Geçiş YAPILDI (2026-07-30); geçiş "
                  "öncesi kayıtların p'si ESKİ yasanın p'sidir ve v3 hükmü ters çevrilemez."),
    }


# ---- MAE MUHASEBESİ — STOPLARIN KÖR İKİZİ ---------------------------
# NEDEN. `exit_efficiency` MFE'yi (görülen en iyi nokta) çıkış nedeni başına muhasebeleştiriyor ve
# "masada ne bıraktık?" sorusunu cevaplıyor. `mae_r` alanı defterde 95 satırın hepsinde VAR ama
# HİÇBİR tüketicisi yoktu — yani stop mesafesinin karnesi ölçülmüyordu. MAE, MFE'nin ikizidir:
# MFE çıkış kuralını, MAE STOP kuralını yargılar.
#
# İKİ SORUYU AYRI AYRI SORAR (tek ortalama ikisini de gizler):
#   (1) KAZANANLAR ne kadar acı çekti? Kazanan işlemlerin MAE'si stopun ne kadar YAKIN olabileceğini
#       söyler: kazananların hiçbiri 0,7R'den derine gitmediyse 1,0R'lik stop fazla geniştir.
#   (2) KAYBEDENLER stopa ne kadar YAKIN öldü? Kaybedenlerin MAE'si ~1,0R'de kümeleniyorsa stop
#       ÇALIŞIYOR; belirgin biçimde AŞIYORSA (>1,15R) gap/kayma var ve "stop 1R" iddiası yanlıştır.
# ÖLÇÜLDÜ (canlı defter): `mae_r` POZİTİF BÜYÜKLÜK olarak yazılıyor (T00095: mae_r 1.175, r −0.982
# — yani acının BÜYÜKLÜĞÜ, işareti değil). Bu yüzden karşılaştırmalar mutlak değerle yapılır ve
# alan adı (`birim`) bunu çıktının içinde söyler.
MAE_MIN_N = 10          # bunun altında dağılım okunmaz (ölçülemedi, sıfır değil)
MAE_STOP_TIGHT_R = 0.70    # kazananların MAE p90'ı bunun altındaysa stop FAZLA GENİŞ adayı
MAE_STOP_SLIP_R = 1.15     # kaybedenlerin MAE medyanı bunu aşıyorsa gap/kayma şüphesi


def mae_profile() -> dict | None:
    """MAE (maximum adverse excursion) karnesi — stop mesafesinin ÖLÇÜLMÜŞ hâli. None: n < MAE_MIN_N."""
    import numpy as np
    kaz, kyb = [], []
    n_eksik = 0
    for t in _trades():
        m, r = t.get("mae_r"), t.get("r_multiple")
        if m is None or r is None:
            n_eksik += 1
            continue
        (kaz if float(r) > 0 else kyb).append(abs(float(m)))
    n = len(kaz) + len(kyb)
    if n < MAE_MIN_N:
        return None

    def _ozet(xs: list) -> dict | None:
        """MAE değerlerinin dağılım özeti (n, medyan, ort, p90, maks); liste boşsa None."""
        if not xs:
            return None
        a = np.asarray(xs, dtype=float)
        return {"n": int(a.size), "medyan": round(float(np.median(a)), 3),
                "ort": round(float(a.mean()), 3),
                "p90": round(float(np.percentile(a, 90)), 3),
                "maks": round(float(a.max()), 3)}

    k, l = _ozet(kaz), _ozet(kyb)
    hukumler = []
    if k and k["p90"] <= MAE_STOP_TIGHT_R:
        hukumler.append(f"kazananların MAE p90'ı {k['p90']}R ≤ {MAE_STOP_TIGHT_R}R — stop FAZLA "
                        f"GENİŞ olabilir (daha sıkı stop kazananları kesmeden riski küçültür)")
    if l and l["medyan"] > MAE_STOP_SLIP_R:
        hukumler.append(f"kaybedenlerin MAE medyanı {l['medyan']}R > {MAE_STOP_SLIP_R}R — GAP/KAYMA: "
                        f"'stop 1R' iddiası gerçekleşen kayıpla uyuşmuyor")
    if not hukumler:
        hukumler.append("stop mesafesi ölçülen dağılımla TUTARLI — sıkılaştırma/gevşetme için "
                        "kanıt YOK")
    out = {"n": n, "n_eksik_alan": n_eksik, "kazananlar": k, "kaybedenler": l,
           "birim": "R (POZİTİF büyüklük — defterde mae_r acının BÜYÜKLÜĞÜ olarak yazılı)",
           "esikler": {"kazanan_p90_dar": MAE_STOP_TIGHT_R, "kaybeden_medyan_kayma": MAE_STOP_SLIP_R},
           "hukum": hukumler,
           "rol": ("RAPOR — hiçbir kapıya bağlı DEĞİL. MFE çıkış kuralını, MAE STOP kuralını "
                   "yargılar; ikisi `exit_efficiency` ile yan yana okunur.")}
    store.write_json("mae_profile.json", out)
    return out


# ==================================================================================================
# EMPİRİK BAYES KÜÇÜLTME
# ==================================================================================================
# SORUN. Rejim hücreleri ve bileşen IC'leri KÜÇÜK örneklemli tahminlerdir ve panoda HAM okunuyorlar.
# n=21'lik bir `pullback` hücresinin −0,968R'si ile n=1338'lik `trend_up`ın +0,112R'si aynı yazı
# tipiyle yan yana duruyor; okur ikisine aynı güveni verir. Küçük hücrenin ekstrem değeri büyük
# ölçüde GÜRÜLTÜDÜR ve "en kötü rejim" seçimi tam olarak o gürültüyü seçer (kazananın-laneti,
# ters yönde).
#
# ÇÖZÜM. Her hücre GENEL ORTALAMAYA doğru küçültülür: küçültme ağırlığı w = τ²/(τ² + σ²ᵢ), yani
# hücrenin kendi belirsizliği (σ²ᵢ = s²/nᵢ) hücreler-arası gerçek yayılıma (τ²) göre ne kadar
# büyükse o kadar çok küçültülür. τ², hücreler-arası gözlenen varyanstan ORTALAMA hücre-içi
# varyans çıkarılarak tahmin edilir (momentler yöntemi); negatif çıkarsa 0'a kıstırılır ve bu
# "hücreler arasında ölçülebilir gerçek fark YOK" demektir — o hâlde her hücre genel ortalamaya
# TAM küçültülür, ki dürüst cevap budur.
#
# VERDICT TABANLARINA DOKUNULMAZ. Küçültülmüş değer, `edge_verdict`/`result_verdict`in ölçüt
# tabanlarına GİREMEZ: taban dolmadan (n >= eşik) hiçbir ölçüt SAGLANDI olamaz ve küçültme, n'i
# BÜYÜTMEZ — yalnız ortalamayı çeker. Küçültülmüş sayıyı tabana sokmak, örneklem yokluğunu
# istatistik hilesiyle örtmek olurdu. Panoda ayrı bir "küçültülmüş" ETİKETİYLE gösterilir.
SHRINK_MIN_CELLS = 3      # bunun altında hücreler-arası varyans tahmin EDİLEMEZ → küçültme yok


def _empirical_bayes(cells: dict) -> dict:
    """cells: {ad: {"mean": float, "n": int, "sd": float|None}} → küçültülmüş tahminler.

    Dönüşte her hücre `ham`, `kucultulmus`, `agirlik` (w) ve `cekim` (ham−küçültülmüş) taşır:
    küçültmenin NE KADAR olduğunu görmeden küçültülmüş sayıya güvenmek, ham sayıya güvenmekten
    daha iyi değildir.

    İKİZİ VAR, BİLEREK AYRI: `olcum_araclari.eb_kucult` aynı momentler yöntemini
    doğrudan SE ile ve düz-ortalama hedefiyle uygular; o, KART ÖZETLERİNİN ileriye dönük standardı
    ve "en iyi hücre" seçim yanlılığına karşı yazıldı. BURASI n-ağırlıklı tabanla çalışır ve
    YAYIMLANMIŞ sayıların (`component_ic.json` `eb` sütunu, pano) kaynağıdır — ikisini tek gövdeye
    indirgemek yayımlanmış `eb_ic` değerlerini HABERSİZ oynatırdı. Bu turda tek hane oynatılmadı."""
    iyi = {k: v for k, v in (cells or {}).items()
           if v.get("mean") is not None and (v.get("n") or 0) > 0}
    if len(iyi) < SHRINK_MIN_CELLS:
        return {"n_hucre": len(iyi), "kucultuldu": False,
                "neden": f"{len(iyi)} hücre < {SHRINK_MIN_CELLS} — hücreler-arası varyans "
                         f"tahmin EDİLEMEZ (küçültme yapılmadı, uydurulmadı)",
                "hucreler": {k: {"ham": v.get("mean"), "kucultulmus": v.get("mean"),
                                 "n": v.get("n"), "agirlik": 1.0, "cekim": 0.0} for k, v in iyi.items()}}
    n_tot = sum(int(v["n"]) for v in iyi.values())
    genel = sum(float(v["mean"]) * int(v["n"]) for v in iyi.values()) / n_tot   # n-ağırlıklı taban
    # hücre-içi varyans: sd verilmişse ondan, yoksa hücreler-arası yayılımdan VEKİL (beyanlı)
    sd_var = [float(v["sd"]) ** 2 / int(v["n"]) for v in iyi.values() if v.get("sd")]
    ort_ic = (sum(sd_var) / len(sd_var)) if sd_var else None
    arasi = sum((float(v["mean"]) - genel) ** 2 for v in iyi.values()) / (len(iyi) - 1)
    if ort_ic is None:
        # sd YOKSA hücre-içi varyans ölçülemez; küçültme n oranıyla yapılır ve BU BEYAN EDİLİR.
        tau2 = arasi
        vekil = True
    else:
        tau2 = max(0.0, arasi - ort_ic)
        vekil = False
    out = {}
    for k, v in iyi.items():
        n = int(v["n"])
        sigma2 = (float(v["sd"]) ** 2 / n) if v.get("sd") else (arasi * (n_tot / n) / len(iyi))
        w = (tau2 / (tau2 + sigma2)) if (tau2 + sigma2) > 0 else 0.0
        km = w * float(v["mean"]) + (1.0 - w) * genel
        out[k] = {"ham": round(float(v["mean"]), 4), "kucultulmus": round(km, 4), "n": n,
                  "agirlik": round(w, 3), "cekim": round(float(v["mean"]) - km, 4)}
    return {"n_hucre": len(iyi), "kucultuldu": True, "genel_ortalama": round(genel, 4),
            "tau2": round(tau2, 6), "hucreler": out,
            "sigma2_vekil": vekil,
            "yontem": ("empirik Bayes (momentler): w = τ²/(τ²+σ²ᵢ); τ² = hücreler-arası varyans − "
                       "ortalama hücre-içi varyans, 0'a kıstırılmış"
                       + (" — σ²ᵢ VEKİL (hücre sd'si yok, n oranından türetildi)" if vekil else "")),
            "beyan": ("KÜÇÜLTÜLMÜŞ değer verdict TABANLARINA GİREMEZ: küçültme n'i büyütmez, yalnız "
                      "ortalamayı çeker. Taban dolmadan hiçbir ölçüt SAGLANDI olamaz.")}


def shrunk_regime_cells(goal: dict | None = None) -> dict:
    """Rejim hücrelerinin küçültülmüş avg_r'si — panoda "küçültülmüş" etiketiyle gösterilir."""
    import numpy as np
    goal = goal or config.goal()
    by = defaultdict(list)
    for t in _trades():
        r = t.get("r_multiple")
        if r is not None:
            by[str(t.get("regime") or "?")].append(float(r))
    cells = {k: {"mean": float(np.mean(v)), "n": len(v),
                 "sd": (float(np.std(v, ddof=1)) if len(v) > 1 else None)}
             for k, v in by.items()}
    out = _empirical_bayes(cells)
    out["birim"] = "R (işlem başına ortalama)"
    out["rol"] = "GÖSTERGE — verdict tabanlarına girmez (bkz. beyan)"
    return out


# σᵢ YASASI, TEK YERDE. Küçültme HAM IC ÖLÇEĞİNDE (r) yapılır ve orada
# Var(r) ≈ 1/(n−1)'dir. Aynı hücrenin YAYIMLANAN güven aralığı ise Fisher-z ölçeğinde kurulur ve
# orada Var(z) = 1/(n−3)'tür (`component_ic._fisher_ci`). İKİ FARKLI SABİT, İKİ FARKLI ÖLÇEK —
# çelişki değil; ama yazılı olmazsa "aynı tabloda iki cetvel" gibi okunur, o yüzden burada duruyor.
def _ic_hucreleri(katman_tablo: dict) -> dict:
    """component_ic tablosunun BİR KATMANINDAN empirik-Bayes hücreleri: {bileşen@ufuk: {mean,n,sd}}.

    TEK TANIM, İKİ TÜKETİCİ: pano okuyucusu (`shrunk_component_ic`) ve tablonun KENDİ `eb` bloğu
    (`component_ic._eb_blok`). İkinci bir yerde hücre kurmak, aynı adı taşıyan iki farklı küçültme
    üretirdi ve fark ancak üçüncü haneyi karşılaştıran biri tarafından görülürdü.

    ŞEMA KAYNAKTAN DOĞRULANDI: tablo[katman][bileşen][ufuk] = {ic, n, ci, anlamli}.
    Tahmin edilen bir şema ("hucreler" listesi) SESSİZCE 0 hücre veriyordu ve okuyucu "küçültme
    yapılmadı" diyerek DOĞRU ama YANLIŞ NEDENLE dürüst kalıyordu — tam olarak `trades.jsonl`ın
    setup/score dersi: alan adı tutmazsa tüketici satırı sessizce eler."""
    import math as _m
    cells: dict = {}
    for bilesen, ufuklar in (katman_tablo or {}).items():
        if not isinstance(ufuklar, dict):
            continue
        for ufuk, h in ufuklar.items():
            if not isinstance(h, dict):
                continue
            ic, n = h.get("ic"), h.get("n")
            if ic is None or not n:
                continue
            # σᵢ = 1/√(n−1) → `_empirical_bayes` σ²ᵢ = sd²/n hesapladığı için sd = √(n/(n−1)).
            cells[f"{bilesen}@{ufuk}"] = {
                "mean": float(ic), "n": int(n),
                "sd": (float(_m.sqrt(int(n)) / _m.sqrt(max(1, int(n) - 1))) if int(n) > 1 else None)}
    return cells


def shrunk_component_ic() -> dict:
    """Bileşen IC'lerinin küçültülmüş hâli. Kaynak `component_ic.json`ın GERÇEK katmanı; cf katmanı
    dahil EDİLMEZ (farklı popülasyon — alınmamış hipotetik girişler; ikisini bir havuzda küçültmek
    iki farklı gerçeği tek ortalamaya çekerdi).

    `tablo_ici_eb`: tablonun KENDİ `eb` bloğunun DIŞ OKUYUCUSU (YASA 6).
    Bu fonksiyon hesabı eskisi gibi kendisi yapmaya devam eder — blok yalnız GÖRÜNÜR olur, hükme
    girmez. Blok yoksa (dosya `eb` alanı eklenmeden önce üretilmişse) bu dürüstçe söylenir;
    "yok"u "sıfır küçültme" diye raporlamak uydurma olurdu."""
    doc = store.read_json("component_ic.json", None)
    if not doc:
        return {"n_hucre": 0, "kucultuldu": False, "neden": "component_ic.json yok",
                "tablo_ici_eb": {"var": False, "neden": "component_ic.json yok"}}
    out = _empirical_bayes(_ic_hucreleri((doc.get("tablo") or {}).get("gercek") or {}))
    out["kaynak"] = "component_ic.json — YALNIZ gerçek katman (cf hariç: farklı popülasyon)"
    out["rol"] = "GÖSTERGE — verdict tabanlarına girmez"
    out["tablo_ici_eb"] = _tablo_ici_eb_ozeti(doc)
    return out


def _tablo_ici_eb_ozeti(doc: dict) -> dict:
    """`component_ic.json`ın tablo-içi `eb` bloğunun TEK SATIRLIK özeti (YASA 6 okuyucusu).

    Ham `ic` alanlarına DOKUNMAZ ve hiçbir hüküm üretmez; yalnız "blok var mı, kaç hücre
    küçültüldü, en çok hangi hücre çekildi" sorularını cevaplar. En çok çekilen hücre bilerek
    seçilir: küçültmenin NE KADAR olduğunu görmeden küçültülmüş bir sayıya güvenmek, ham sayıya
    güvenmekten daha iyi değildir (bu bloğun kendi gerekçesi)."""
    eb = doc.get("eb")
    if not isinstance(eb, dict) or not (eb.get("katmanlar") or {}):
        return {"var": False,
                "neden": ("tabloda `eb` bloğu YOK — dosya blok eklenmeden ÖNCE üretilmiş "
                          "(bir sonraki `component_ic()` koşumunda doğar)")}
    ger = (eb.get("katmanlar") or {}).get("gercek") or {}
    hucreler = ger.get("hucreler") or {}
    en_cok = None
    if hucreler:
        ad, h = max(hucreler.items(), key=lambda kv: abs(kv[1].get("cekim") or 0.0))
        en_cok = {"hucre": ad, "ham_ic": h.get("ham_ic"), "eb_ic": h.get("eb_ic"),
                  "shrink_katsayisi": h.get("shrink_katsayisi"), "cekim": h.get("cekim"),
                  "n": h.get("n")}
    return {"var": True, "n_hucre": ger.get("n_hucre"), "kucultuldu": ger.get("kucultuldu"),
            "genel_ortalama": ger.get("genel_ortalama"), "tau2": ger.get("tau2"),
            "neden": ger.get("neden"), "en_cok_cekilen": en_cok,
            "yontem": eb.get("yontem"), "hukum_verir": False,
            "kapsam": ("component_ic tablosunun KENDİ eb sütunu (yalnız gerçek katman özetlendi); "
                       "ham `ic` alanları DEĞİŞMEZ ve okuyucular ham ic okumaya devam eder")}


# ==================================================================================================
# HOLDOUT ROTASYON DEĞERLENDİRİCİSİ
# ==================================================================================================
# SORUN. Aşınma defteri aynı pencereye kaç kez sorulduğunu sayıyor (canlı: bir parmak izinde 290
# sorgu) ve eşik aşılınca kapıya ek marj yazıyor. Ama ek marj bir SEMPTOM tedavisidir: 290 kez
# sorulmuş bir holdout artık holdout DEĞİLDİR ve marj onu yeniden holdout yapmaz. Gerçek çözüm
# pencereyi DÖNDÜRMEKTİR (yeni bir holdout dilimi ayırmak).
#
# BU FONKSİYON ÖNERİR, UYGULAMAZ. Pencere değiştirmek TÜM geçmiş kapı kayıtlarının
# karşılaştırılabilirliğini keser (fingerprint değişir, eski p'ler yeni pencerede geçerli değildir)
# ve bu bir OPERATÖR kararıdır. Otomatik döndürmek, sistemin kendi sınav kâğıdını kendi değiştirmesi
# olurdu — aşınma yasasının önlemeye çalıştığı şeyin ta kendisi.
ROTATION_RECOMMEND_RATIO = 1.0   # sorgu/limit oranı bunu aşarsa öneri doğar (yani eşik aşıldıysa)


def holdout_rotation_advice() -> dict:
    """Aşınma sayacı eşiğindeyken holdout rotasyonu ÖNERİR (uygulamaz).

    R1 UYGULANDIKTAN SONRAKİ HÂLİ. Bu değerlendirici R1'in GEREKÇESİYDİ: R0'a 434 sorgu
    sorulmuştu (limit 20 → 21,7×) ve öneri üretiliyordu. Operatör öneriyi uyguladı. Artık fonksiyonun
    iki AYRI şeyi söylemesi gerekiyor ve ikisini karıştırmamak zorunda:
      (a) HANGİ ROTASYON YÜRÜRLÜKTE (R1, tarihiyle) — yoksa panoyu okuyan biri öneriyi hâlâ bekliyor
          sanır, ya da daha kötüsü, arşivlenmiş R0 sayacını yürürlükteki aşınma sanır.
      (b) BİR SONRAKİ rotasyonun gerekip gerekmediği — ve bu YENİ pencerede yeniden birikmesi gereken
          bir ölçümdür. `oos_erosion.report()` rotasyondan sonra `en_cok`u YALNIZ yürürlükteki
          pencereden seçer, yani buradaki oran R1'in kendi aşınmasıdır; R0'ın 434'ü öneriyi bir daha
          tetikleyemez (tetiklerse rotasyon sonsuz döngüye girer: her tur "döndür" der, çünkü ölü bir
          sayaç hiç düşmez).
    Sayaç sıfırdan başlar ve bu "aşınma yok" DEĞİL "R1'de henüz ölçülmedi" demektir — beyan bunu yazar.
    """
    from . import oos_erosion, dataset
    rep = oos_erosion.report()
    limit = int(rep.get("limit") or 0)
    en = rep.get("en_cok") or {}
    q = int(en.get("queries") or 0)
    # YÜRÜRLÜKTEKİ PENCEREDE HİÇ KAYIT YOKSA ORAN **None**, 0.0 DEĞİL — ve bu ayrım rotasyonla
    # ÖNEMLİ hâle geldi. Rotasyondan hemen sonra `en_cok` boştur; 0.0 yazmak "eşik aşılmadı, aşınma
    # yok" derdi, oysa doğru cümle "R1'de HENÜZ ÖLÇÜLMEDİ"dir. Modülün başındaki ayrımın ta kendisi
    # (`report()` de aynı sebeple `toplam_sorgu`yu None döner): ölçülmemiş bir şeyi sıfır ölçülmüş
    # gibi sunmak, aşınma yasasının önlemek için var olduğu şeydir.
    oran = ((q / limit) if limit else None) if rep.get("en_cok") else None
    out = {"limit": limit, "en_cok_sorgu": q, "oran": (round(oran, 3) if oran is not None else None),
           "n_pencere": rep.get("n_pencere"), "pencere": en.get("pencere"),
           "extra_margin_yururlukte": rep.get("extra_margin_yururlukte"),
           "uygular_mi": False,
           # ---- (a) YÜRÜRLÜKTEKİ ROTASYON ----
           "uygulanan_rotasyon": {
               "pencere_id": dataset.ROTATION_ID, "tarih": dataset.ROTATION_DATE,
               "onceki": dataset.ROTATION_PREV_ID,
               "yeni_geometri": {"is_start": dataset.IS_START, "oos_start": dataset.OOS_START,
                                 "oos_end": dataset.OOS_END, "holdout_end": dataset.HOLDOUT_END,
                                 "folds": list(dataset.OOS_FOLDS)},
               # DONMUŞ HOLDOUT vs BUGÜN — İKİSİ AYRI SATIR, VE AYRILIK BİLİNÇLİ. Kapı
               # `holdout_end`i DONMUŞ okur (parmak izi kararlı kalsın, aşınma sayacı birikebilsin);
               # insan ise "o dilim bugüne kadar ne kadar uzadı" sorusunu sorar. Tek sayı iki soruya
               # cevap veremez, o yüzden iki sayı yan yana durur — ve aradaki gün sayısı, bir
               # sonraki rotasyonun ne kadar taze veri bulacağının ölçüsüdür.
               "dondurulmus_holdout": {"baslangic": dataset.OOS_END,
                                       "son_DONMUS": dataset.HOLDOUT_END,
                                       "bugun_RAPOR": dataset.holdout_report_end(),
                                       "beyan": ("holdout sonu kapı tarafında DONMUŞtur "
                                                 "(yuvarlanmaz): `oos_erosion.fingerprint` "
                                                 "girdilerinde `holdout_end` var, yuvarlanan bir "
                                                 "sonu her gün parmak izini değiştirir ve aşınma "
                                                 "sayacı hiç birikemezdi. Bugüne kadarki uzama "
                                                 "YALNIZ insana raporlanır; kabule GİRMEZ ve "
                                                 "pencerelemeye girmez.")},
               "durum": (f"{dataset.ROTATION_ID} UYGULANDI ({dataset.ROTATION_DATE}) — operatör "
                         f"onaylı; sayaç bu pencerede sıfırdan birikiyor"),
               "arsiv": rep.get("arsiv")},
           "kiyas_uyarisi": dataset.PENCERE_KIYAS_UYARISI,
           "beyan": ("ÖNERİ — UYGULAMAZ. Pencere değişimi tüm geçmiş kapı kayıtlarının "
                     "karşılaştırılabilirliğini keser (fingerprint değişir) ve bu bir OPERATÖR "
                     "kararıdır. Otomatik rotasyon, sistemin kendi sınav kâğıdını kendi "
                     "değiştirmesi olurdu.")}
    if oran is None:
        out["oneri"] = None
        out["hukum"] = (f"{dataset.ROTATION_ID} uygulandı ({dataset.ROTATION_DATE}); yeni pencerede "
                        f"aşınma defteri HENÜZ ÖLÇMÜYOR — 'aşınma yok' değil 'ölçülmedi'. "
                        f"Bir sonraki rotasyon önerisi için sayaç bu pencerede birikmeye devam eder.")
        return out
    if oran < ROTATION_RECOMMEND_RATIO:
        out["oneri"] = None
        out["hukum"] = (f"{dataset.ROTATION_ID} ({dataset.ROTATION_DATE}) yürürlükte · sorgu "
                        f"{q}/{limit} — eşik AŞILMADI; rotasyon önerisi YOK "
                        f"(ek marj {rep.get('extra_margin_yururlukte')})")
        return out
    p = en.get("pencere") or {}
    out["oneri"] = {
        # SONRAKİ rotasyon: R1'in KENDİ aşınması eşiği aştı. Numaralandırma R1'den türetilir ki
        # öneri "hangi rotasyonu öneriyorsun" sorusuna cevap verebilsin (R0→R1 sırası zaten yazılı).
        "eylem": f"holdout dilimini DÖNDÜR ({dataset.ROTATION_ID} sonrası bir sonraki rotasyon)",
        "yururlukteki_rotasyon": {"pencere_id": dataset.ROTATION_ID,
                                  "tarih": dataset.ROTATION_DATE},
        "mevcut_holdout": {"oos_end": p.get("oos_end"), "holdout_end": p.get("holdout_end")},
        "gerekce": (f"{dataset.ROTATION_ID} penceresine {q} kez soruldu (limit {limit}) — {q} "
                    f"sorgudan sonra holdout artık holdout değildir; ek marj semptomu tedavi eder, "
                    f"nedeni etmez"),
        "secenekler": [
            "oos_end'i ileri taşı ve yeni holdout dilimi aç (en temiz; eski kayıtlar arşivlenir)",
            "holdout'u ikiye böl: yarısını dokunulmamış bırak (kanıt yavaşlar, temizlik artar)",
            "pencereyi sabit tut ve YENİ aday üretimini durdur (aşınmayı dondurur)",
        ],
        "maliyet": "fingerprint değişir → geçmiş p/ΔS kayıtları yeni pencerede KARŞILAŞTIRILAMAZ",
        # ÖNCEKİ ROTASYONUN KANITI ÖNERİNİN İÇİNDE: "bu daha önce yapıldı ve şu maliyeti oldu"
        # bilgisi, aynı kararı ikinci kez verecek operatörün en çok ihtiyaç duyduğu şeydir.
        "onceki_rotasyon_dersi": (
            f"{dataset.ROTATION_PREV_ID} → {dataset.ROTATION_ID} rotasyonu "
            f"{dataset.ROTATION_DATE}'de uygulandı; o pencere arşivde "
            f"{(rep.get('arsiv') or {}).get('toplam_sorgu')} sorguyla duruyor (silinmedi)"),
    }
    out["hukum"] = (f"ROTASYON ÖNERİLİR ({dataset.ROTATION_ID} sonrası): sorgu {q}/{limit} "
                    f"(oran {oran:.2f})")
    return out


# =================================================================================================
# NOUS SİSTEM-DEĞERLENDİRME KATMANI · KATMAN A: TELEMETRİ PAKETİ
# =================================================================================================
# OPERATÖR YÖNÜ: "bütün mekanizmaları değerlendirip güncellenmesi gerekenleri nous bulmalı; sistem
# kısıtlı alanda kalmadan sürekli kendini geliştirmeli". Katman B (nous'un haftalık MEKANİZMA
# değerlendirmesi) bir girdi ister ve o girdi UYDURULAMAZ: paket YALNIZ hâlihazırda var olan
# üreticileri çağırır, yeni bir ölçüm İCAT ETMEZ. Yeni ölçüm icat etmek burada iki kat tehlikeliydi,
# çünkü çıktısı bir LLM prompt'una gidiyor: uydurma bir alan adı, uydurma bir gözleme, o da uydurma
# bir öneriye dönüşür ve zincirin hiçbir halkası yalanı yakalamaz.
#
# HER BÖLÜM "ÖLÇÜLEMEDİ"Yİ DÜRÜSTÇE TAŞIR ve bu bir teknik detay değil, paketin ASIL değeri:
# "ölçülemedi" bir öneri KONUSUDUR ("bunu ölçmeye başla" — kopuk kablo), "kötü" ise BAŞKA bir öneri
# konusudur ("bunu değiştir" — parametre/tasarım). İkisi tek alana katlanırsa öneriler de katlanır ve
# beyin ölçülmemiş bir şeyi "iyi" sanıp hiç dokunmaz. Bugün paketin 12 bölümünün birkaçı gerçekten
# ölçülemez durumdadır (boş gölge-varyant defteri, R1'de henüz sıfır aşınma kaydı, PBO tabanı 0/8) ve
# paket bunu SAYIYLA söyler — sahte bir "her şey yolunda" göstermez.
#
# BÖLÜM ADLARI ADLANDIRILMIŞ SABİTTİR: 12 üreticiyi prompt'a ayrı ayrı taşımak, hangi bölümün eksik
# kaldığını SAYILAMAZ kılardı. Sabit liste + `n_olculemedi` sayacı, "paket bu hafta neyi görmedi"
# sorusunun tek cevabıdır.
TELEMETRY_SECTIONS: tuple[str, ...] = (
    "kar_selalesi", "sonuc_hukmu", "edge_hukmu", "veto_istatistigi", "skill_atiflari",
    "hermes_karnesi", "asinma_pencere", "golge_varyant_ayrisma", "dsr_pbo",
    "coverage_ariza", "mae_profili", "time_stop_r_egrisi",
)

TELEMETRY_EVENT_DAYS = 7        # coverage/arıza sayaçlarının penceresi — paketin kadansı haftalık
GATE_TALLY_CAP = 12             # en çok listelenen veto adedi (kuyruk token, baş kısım sinyal)


def _olculemedi(neden: str, **ek) -> dict:
    """Ölçülemeyen bölümün SABİT şekli. `_olcut`un dört-durumlu şekliyle aynı gerekçe: ölçülemeyen
    bir bölümü `None` ile geçmek, "neden ölçülemedi" bilgisini yok eder — ve tam o bilgi Katman B'nin
    en verimli öneri kaynağıdır (kopuk kablo, boş defter, dolmamış taban)."""
    return {"durum": "olculemedi", "neden": neden, **ek}


def gate_veto_tally() -> dict:
    """KAPI KAYITLARININ VETO İSTATİSTİĞİ — "hangi veto kaç kez, hangi aileler".

    İKİ KAPI VAR VE İKİSİ AYRI SORUYA CEVAP VERİR; tek sayıda birleştirilemezler:
      (a) İŞLEM KAPISI (`trade_plans.jsonl` → `gate_verdict`/`gate_reasons`/`gate_checks`):
          "bugünün adayları neden silahlanmadı" — günlük, yüksek hacimli, plan başına.
      (b) HİPOTEZ KAPISI (`hypotheses.jsonl` → `status`/`reject_reasons`): "hangi DÜĞME denemesi
          neden düştü" — haftalık, düşük hacimli, öğrenme muhasebesinin kendisi.
    Aynı kovaya atılsalar 390 plan reddi 41 hipotez reddini boğar ve öğrenme kapısının istatistiği
    görünmez olurdu (`rejected_by_dsr`ın `rejected_by_backtest`e karıştırılmama gerekçesinin aynısı).

    NEDEN BU FONKSİYON VARDI DA YOKTU: repo genelinde plan-başına veto sayan hiçbir toplayıcı
    yoktu — tek komşu `api._benchmark_veto_tally` ve o YALNIZ SPY vetosunu sayar. Yani "kapı en çok
    neyi eliyor" sorusu bugüne kadar hiç ölçülmemişti, oysa cevabı `gate_checks` alanında 390 satır
    boyunca yazılıydı (YASA 6'nın klasik hâli: üretilen kanıt tüketilmiyor).

    SEVERITY AYRIMI KORUNUR: `hard` bir kontrol düşerse plan ÖLÜR, `soft` düşerse REVIEW olur.
    Toplarken karıştırmak, "en sık veto" listesini karar-etkisi olmayan yumuşak notlarla doldurur."""
    plans = store.read_jsonl("trade_plans.jsonl")
    hyps = memory.all_hypotheses()

    verdicts: dict[str, int] = {}
    hard: dict[str, int] = {}
    soft: dict[str, int] = {}
    reasons: dict[str, int] = {}
    n_checkli = n_llm_veto = 0
    for p in plans:
        verdicts[str(p.get("gate_verdict") or "?")] = verdicts.get(str(p.get("gate_verdict") or "?"), 0) + 1
        if p.get("llm_veto"):
            n_llm_veto += 1
        gc = p.get("gate_checks")
        if isinstance(gc, list) and gc:
            n_checkli += 1
            for c in gc:
                if isinstance(c, dict) and c.get("passed") is False:
                    kova = hard if str(c.get("severity")) == "hard" else soft
                    ad = str(c.get("check") or "?")
                    kova[ad] = kova.get(ad, 0) + 1
        for r in (p.get("gate_reasons") or []):
            # SERBEST METİN AİLEYE İNDİRİLİR: gerekçeler sayı taşır ("score 58 < 60") ve ham metin
            # sayıldığında her satır kendi kovasını açar — istatistik olmaz, döküm olur. İlk iki
            # kelime AİLE olarak alınır ve bu bir BEYANDIR (kanonik bir aile alanı defterde YOK).
            aile = " ".join(str(r).split()[:2])[:48] or "?"
            reasons[aile] = reasons.get(aile, 0) + 1

    statuses: dict[str, int] = {}
    hyp_reasons: dict[str, int] = {}
    n_reason_alanli = 0
    for h in hyps:
        statuses[str(h.get("status") or "?")] = statuses.get(str(h.get("status") or "?"), 0) + 1
        rr = h.get("reject_reasons")
        if isinstance(rr, list) and rr:
            n_reason_alanli += 1
            for r in rr:
                aile = " ".join(str(r).split()[:2])[:48] or "?"
                hyp_reasons[aile] = hyp_reasons.get(aile, 0) + 1

    def _top(d: dict) -> list:
        """Sayaç sözlüğünü en sık görülenden başlayarak `[{"veto": ad, "n": sayı}]` listesine çevirir.

        `GATE_TALLY_CAP` ile kırpılır — kuyruk raporu şişirmez."""
        return [{"veto": k, "n": v} for k, v in
                sorted(d.items(), key=lambda kv: -kv[1])[:GATE_TALLY_CAP]]

    return {
        "islem_kapisi": {
            "n_plan": len(plans), "hukumler": verdicts,
            "n_gate_checks_alanli": n_checkli,
            "kapsam_beyani": (f"{n_checkli}/{len(plans)} planda `gate_checks` alanı var — "
                              f"eksik satırlarda karar ağacı ÖLÇÜLEMEZ (sözleşme bu alanı "
                              f"İSTEĞE BAĞLI tutuyor)"),
            "sert_vetolar": _top(hard), "yumusak_vetolar": _top(soft),
            "gerekce_aileleri": _top(reasons), "n_llm_veto": n_llm_veto,
        },
        "hipotez_kapisi": {
            "n_hipotez": len(hyps), "statuler": statuses,
            "n_reject_reasons_alanli": n_reason_alanli,
            "ret_nedeni_aileleri": _top(hyp_reasons),
        },
        # DÜĞME AİLELERİ TEK KAYNAKTAN GELİR, BURADA YENİDEN SAYILMAZ: iki yerde iki aile tanımı olsaydı
        # panodaki "ölü aile" ile prompt'taki "ölü aile" sessizce ayrışırdı.
        "dugme_aileleri": dead_families(),
        "rol": "RAPOR — hiçbir kapıya bağlı DEĞİL; sayım kapı kararlarını değiştirmez",
        "beyan": ("gerekçe AİLESİ ilk iki kelimeden türetilir (defterde kanonik aile alanı YOK) — "
                  "bu bir yaklaşımdır ve sayıları aile-içi kırılım için değil SIRALAMA için okuyun"),
    }


def coverage_breakage_counters(days: int = TELEMETRY_EVENT_DAYS) -> dict:
    """COVERAGE + ARIZA SAYAÇLARI — evren kapsaması ve hotstate çırpınması.

    İKİSİ DE DOSYADA DEĞİL, OLAY DEFTERİNDE YAŞAR ve bu bilinçli bir okuma kararıdır:
      * `universe_coverage` bir `state/*.json` anahtarı DEĞİL, `watchdog.parity_report` içindeki bir
        kontrol SATIRIdır; ham sayı yalnız olaylarda durur.
      * hotstate çırpınma sayacı (`reassert_suppressed`) SÜREÇ-İÇİ bir değişkendir ve her emisyonda
        SIFIRLANIR — bu paket ayrı bir süreçte koşar, yani o sayacı okumak BAŞKA bir sürecin
        belleğine bakmak olurdu (ve okunsa 0 görünüp "çırpınma yok" YANLIŞ hükmünü verirdi).
        Dayanıklı iz olay defterindedir.

    HOTSTATE BLOĞU SENSÖRDEN GELİR, BURADA HESAPLANMAZ (2026-09-01, akıbet kalemi N00016). Alan
    (`coverage_ariza.hotstate.surec_ici_sayac`) SABİT `None`du ve yanındaki beyan "OKUNMADI"
    diyordu — oysa `watchdog.hotstate_health_report` sensörü 2026-08-26'dan beri hazırdı ve iki
    yarımı ayrı ayrı ölçüyordu. Yani ölçüm vardı, KABLO yoktu ve fiş her koşuda yeniden doğuyordu.
    İkinci bir hesap yazmak yerine sensör çağrılır: "alansız satır 0 DEĞİLDİR" yasası tek yerde
    yaşar, kopyada sessizce ölmez. Süreç-içi yarım bu süreçte hâlâ `None`+neden olabilir ve bu
    DÜRÜSTLÜKTÜR (pano süreci hotstate'e dokunmaz) — kablo o yasayı gevşetmez.

    PENCERE TARİH TABANLIDIR (satır limiti DEĞİL): `hotstate_down` seli defterin %60'ını tek olaya
    çevirdi ve satır-limitli her tüketici geçmişe kör kaldı — bkz. `watchdog.events_since`.
    Defter AYNI TURDA BİR KEZ okunur: ham satırlar sensöre elden verilir (`olaylar=ev`)."""
    from . import watchdog as _wd
    ev = _wd.events_since(days)
    say: dict[str, int] = {}
    kapsama_degerleri = []
    for e in ev:
        ad = str(e.get("event") or e.get("kind") or "?")
        say[ad] = say.get(ad, 0) + 1
        for alan in ("universe_coverage", "coverage"):
            v = e.get(alan)
            if isinstance(v, (int, float)):
                kapsama_degerleri.append(float(v))
    kapsama_degerleri.sort()
    n_cov = len(kapsama_degerleri)
    # TEK KAYNAK: iki yarımı da sensör ölçer. `ev` elden verilir — aynı tur defteri ikinci kez
    # okumaz ve iki okuma arasında düşen bir satır iki farklı sayı üretemez.
    _hs = _wd.hotstate_health_report(days, olaylar=ev)
    return {
        "pencere_gun": days, "n_olay": len(ev),
        "evren_kapsamasi": {
            "n_olcum": n_cov,
            "en_kotu": (kapsama_degerleri[0] if n_cov else None),
            "medyan": (kapsama_degerleri[n_cov // 2] if n_cov else None),
            "session_deferred_for_coverage": say.get("session_deferred_for_coverage", 0),
            "session_bar_never_published": say.get("session_bar_never_published", 0),
            "universe_coverage_low": say.get("universe_coverage_low", 0),
        },
        "hotstate": {
            # Olay sayımı da sensörden okunur: `say` ile ikinci bir sayım tutmak, iki pencere
            # yasasının (olay adı ↔ `kind` yedeği) sessizce ayrışabileceği bir kopya olurdu.
            "hotstate_down": _hs["defter"]["olay"],
            # SÜREÇ-İÇİ YARIM — bu paketi ÜRETEN sürecin gördüğü. Pano/telemetri süreci hotstate'e
            # hiç dokunmadıysa cevap None + NEDEN'dir (SIFIR BASILMAZ: "ölçtük, çırpınma yok" ile
            # "bu süreç ölçmedi" ayrı hâllerdir). Sayacı artıran süreç raporu kendisi üretirse
            # burada ÖLÇÜLMÜŞ bir sayı durur.
            "surec_ici_sayac": _hs["surec_ici"]["bastirilan"],
            "surec_ici_neden": _hs["surec_ici"]["bastirilan_neden"],
            # DEFTER YARIMI — süreç sınırını geçen tek iz (`events.jsonl`). Sensörün sözlüğü
            # OLDUĞU GİBİ taşınır: alan alan kopyalamak, "alansız satır 0 DEĞİLDİR" beyanını
            # (`alt_sinir`, `*_neden`) taşımayı unutabilecek ikinci bir şema demekti.
            "defter": _hs["defter"],
            "capraz_surec": _hs["capraz_surec"],
            "beyan": ("İKİ YARIM, İKİ AYRI SORU — tek kaynak `watchdog.hotstate_health_report`: "
                      "`surec_ici_sayac` = `hotstate.health().reassert_suppressed`, YALNIZ bu "
                      "paketi üreten sürecin gördüğü (süreç-içi ve her emisyonda sıfırlanır; "
                      "dokunulmamışsa None + `surec_ici_neden`). `defter` = olay defterindeki "
                      "`hotstate_down` satırları, yani BÜTÜN süreçler — sayaç süreç sınırını "
                      "yalnız orada geçer ve alan taşımayan satırlar 0 SAYILMAZ"),
        },
        "en_sik_olaylar": [{"olay": k, "n": v} for k, v in
                           sorted(say.items(), key=lambda kv: -kv[1])[:GATE_TALLY_CAP]],
        "rol": "RAPOR — sayaçlar hiçbir kapıya bağlı DEĞİL",
    }


def system_telemetry(edge: dict | None = None, sonuc: dict | None = None,
                     days: int = TELEMETRY_EVENT_DAYS) -> dict:
    """HAFTALIK SİSTEM-TELEMETRİ ÖZETİ — Katman B'nin (nous mekanizma-değerlendirmesi) TEK girdisi.

    `edge`/`sonuc` ENJEKTE EDİLEBİLİR (`health.faz6_kilitleri` deseni): iki hüküm de bootstrap CI
    koşar ve api zaten her `/api/diagnostics` isteğinde hesaplıyor — paket onları yeniden hesaplarsa
    aynı ölçüm iki kez, iki farklı anda yapılır ve iki farklı sayı verebilir. Enjeksiyon yalnız
    maliyet değil TUTARLILIK kararıdır: pano ile prompt AYNI hükmü görmeli.

    BÖLÜM BAŞARISIZLIĞI PAKETİ DÜŞÜRMEZ (YASA 4 ile çelişmez — sessizlik yok): bir üretici istisna
    fırlatırsa bölüm `olculemedi` olur, NEDENİ istisna metniyle yazılır ve `n_olculemedi` artar.
    Tek bir bölüm yüzünden paketin tamamının düşmesi, haftalık değerlendirmenin hiç koşmaması
    demekti — ve o sessizlik, bir bölümün eksikliğinden çok daha pahalıdır."""
    from . import oos_erosion as _ero
    hafta = _week_stamp()
    boliim: dict = {}

    def _al(ad: str, fn, bos_neden: str | None = None):
        """Bölümü çağır; istisna ya da boş dönüş `olculemedi`ye çevrilir."""
        try:
            v = fn()
        except Exception as e:                      # noqa: BLE001 — bölüm izolasyonu (bkz. üstteki not)
            from . import obs as _o
            _o.warn("system_telemetry_section_failed", section=ad,
                    error=f"{type(e).__name__}: {e}")
            boliim[ad] = _olculemedi(f"üretici düştü: {type(e).__name__}: {e}")
            return
        boliim[ad] = _olculemedi(bos_neden or "üretici None döndü (taban dolmadı)") if v is None else v

    _al("kar_selalesi", profit_waterfall,
        f"kapanmış işlem sayısı {WATERFALL_MIN_N} tabanının altında — şelale ÖLÇÜLEMEDİ")
    _al("sonuc_hukmu", (lambda: sonuc if sonuc is not None else result_verdict()))
    _al("edge_hukmu", (lambda: edge if edge is not None else edge_verdict()))
    _al("veto_istatistigi", gate_veto_tally)
    _al("skill_atiflari", skill_attribution)
    _al("hermes_karnesi", hermes_scorecard)
    _al("asinma_pencere", _ero.report)
    _al("golge_varyant_ayrisma", shadow_variant_summary)
    _al("dsr_pbo", validation_trio)
    _al("coverage_ariza", (lambda: coverage_breakage_counters(days)))
    # MAE: `mae_profile()` üretici YAZAR (store.write_json). Telemetri SAF OKUYUCUDUR — canlı worker
    # koşarken paket bir artefaktı yeniden yazarsa iki yazar arasına girmiş oluruz. Dosya okunur.
    _al("mae_profili", (lambda: store.read_json("mae_profile.json", None)),
        "state/mae_profile.json yok — profil hiç üretilmemiş (MAE_MIN_N dolmamış olabilir)")
    _al("time_stop_r_egrisi", _time_stop_curve,
        "kapanmış işlem yok — gün-gün R eğrisi ÖLÇÜLEMEDİ")

    olculemedi = [k for k, v in boliim.items()
                  if isinstance(v, dict) and v.get("durum") == "olculemedi"]
    eksik_bolum = [k for k in TELEMETRY_SECTIONS if k not in boliim]
    bosluklar = _beyan_edilen_bosluklar(boliim)
    return {
        "hafta": hafta,
        "uretildi": memory.now_iso(),
        "bolumler": boliim,
        "bolum_adlari": list(TELEMETRY_SECTIONS),
        "n_bolum": len(TELEMETRY_SECTIONS),
        # İKİ AYRI SAYAÇ, İKİ AYRI SORU — birleştirilemezler:
        #   `n_olculemedi`   : üretici HİÇBİR ÇIKTI vermedi (None/istisna) → bölüm boş.
        #   `beyan_edilen_bosluklar`: üretici çıktı VERDİ ama kendi içinde "bu ölçülemedi" DEDİ
        #                      (boş defter, dolmamış taban, sıfırlanmış sayaç).
        # İlk koşuda birincisi 0, ikincisi 5'ti: paket "12/12 bölüm doldu" diyordu ve bu DOĞRUydu,
        # ama beş mekanizma kendi içinde ölçmediğini beyan ediyordu. Yalnız birinci sayacı raporlamak
        # sahte bir "her şey ölçülüyor" hükmü verirdi — ve Katman B'nin EN VERİMLİ öneri kaynağı tam
        # olarak bu beş boşluktur ("kabloyu bağla" / "tabanı doldur" önerileri).
        "n_olculemedi": len(olculemedi),
        "olculemeyenler": olculemedi,
        "beyan_edilen_bosluklar": bosluklar,
        "n_beyan_edilen_bosluk": len(bosluklar),
        # Sabit listede olup pakette HİÇ görünmeyen bölüm = kod ile sabit ayrışmış demektir. Sıfır
        # olmalı ve testi var; yine de dışa verilir çünkü sessiz bir ayrışma paketi yalancı yapar.
        "sabit_ile_ayrisan": eksik_bolum,
        # BOUNDS DÜĞME ADLARI: Katman C (parametre-şekilli öneri) yalnız bounds'ta TANIMLI bir düğme
        # için kurulabilir. Adlar prompt'a girmezse beyin var olmayan düğmeler önerir ve öneriler
        # şekil denetiminde toptan düşer — kalite kapısı gürültüye boğulur. SALT OKUMA.
        "bounds_dugmeleri": sorted((config.bounds() or {}).keys()),
        "rol": ("RAPOR — paket hiçbir kapıya bağlı DEĞİL ve hiçbir şeyi UYGULAMAZ. Katman B'nin "
                "girdisi, Rol 1 denetiminin özeti."),
        "beyan": ("YENİ ÖLÇÜM İCAT EDİLMEDİ: her bölüm mevcut bir üreticinin çıktısıdır. "
                  "'olculemedi' bir bölüm SAHTE bir 'her şey yolunda' göstermez — eksikliğin "
                  "kendisi bir öneri konusudur ve öyle raporlanır."),
    }


_BOSLUK_ANAHTARLARI = ("durum", "dsr_durum", "status")


def _beyan_edilen_bosluklar(bolumler: dict) -> list:
    """Üreticilerin KENDİ beyan ettiği ölçüm boşlukları — bölüm.yol biçiminde.

    HEURİSTİK DEĞİL, KODUN KENDİ DEYİMİ: bu depo ölçülemeyeni iki yazılı biçimde söyler —
    `{"durum"|"dsr_durum"|"status": "olculemedi"}` (validation/health deyimi) ve boş defterin
    `durum` cümlesi ("DEFTER BOŞ — ..."). Tarama YALNIZ bu iki imzayı arar. "Bir yerde 0 var, demek
    ki ölçülmemiş" gibi bir çıkarım YAPILMAZ: o bir tahmin olurdu ve tahmin, uydurma yasağının
    kapsamına girer."""
    out = []

    def _gez(x, yol: str, derinlik: int = 0):
        """Rapor ağacında özyinelemeli gezinip BOŞLUK işaretlerini ("olculemedi" / "DEFTER BOŞ...")
        nokta-ayraçlı yollarıyla `out` listesine toplar.

        Derinlik 6 ve liste başına 20 öğe ile sınırlıdır (rapor gezintisi patlamasın)."""
        if derinlik > 6 or not isinstance(x, (dict, list, tuple)):
            return
        if isinstance(x, dict):
            for k, v in x.items():
                if k in _BOSLUK_ANAHTARLARI and isinstance(v, str):
                    if v == "olculemedi" or v.startswith("DEFTER BOŞ"):
                        out.append(f"{yol}.{k}" if yol else str(k))
                _gez(v, f"{yol}.{k}" if yol else str(k), derinlik + 1)
        else:
            for i, v in enumerate(x[:20] if isinstance(x, (list, tuple)) else []):
                _gez(v, f"{yol}[{i}]", derinlik + 1)
    for ad, payload in (bolumler or {}).items():
        _gez(payload, ad)
    return out


def _time_stop_curve() -> dict | None:
    """time-stop gün-gün R eğrisi. Üreticisi `backtest.holding_day_r_curve` SAF bir
    fonksiyondur, state artefaktı YOKTUR ve bugüne kadar ÜRETİM ÇAĞIRANI DA YOKTU (tek çağıranı
    testlerdi) — YASA 6'nın bir başka hâli. Paket onun ilk üretim tüketicisidir."""
    from . import backtest as _bt
    rows = _trades()
    if not rows:
        return None
    egri = _bt.holding_day_r_curve(rows)
    if not (egri or {}).get("n"):
        return None
    # KUYRUK KIRPILIR: 40 günlük tam döküm prompt'ta ~4k karakter ve karar bilgisi ilk günlerdedir.
    # Kümülatif eğri TAM kalır (time-stop kararı kümülatifte okunur).
    return {"n": egri.get("n"), "ort_r": egri.get("ort_r"),
            "gunler": (egri.get("gunler") or [])[:15],
            "kumulatif": egri.get("kumulatif"),
            "kaynak": "backtest.holding_day_r_curve (saf fonksiyon — state artefaktı YOK)"}


def _week_stamp(ts: str | None = None) -> str:
    """Hafta damgası — `hermes_composite.week_key` ile AYNI FONKSİYON.

    İki damga biçimi olsaydı Katman C'nin bütçe anahtarı (`composite_budget.json` haftaları) ile
    önerinin hafta damgası ayrışır ve "bu hafta kaç yoklama harcandı" sorusu iki farklı cevap
    verirdi. Tek kaynak: bütçeyi sayan modül."""
    from . import hermes_composite as _hc
    return _hc.week_key(ts)


def improvement_proposals_status(limit_hafta: int = 3) -> dict:
    """SİSTEM ÖNERİLERİ DEFTERİNİN DIŞ OKUYUCUSU (Katman B/C/D'nin pano + CLI yüzeyi).

    YASA 6: `nous_eval.py` deftere YAZAR; onu BAŞKA bir modülden okuyan taraf burasıdır. DOSYA ADI
    LİTERAL yazılır (`nous_eval.PROPOSALS_FILE` üzerinden DEĞİL): `codelaw.artifact_graph` statik bir
    graftır ve sabitten gelen adı çözemez — defter o zaman "yazılıyor ama okunmuyor" görünür ve YASA
    6 denetimi onu hiç göremez (`validation_trio`/`composite_queue_status`taki notun aynısı).

    DÜŞÜRÜLEN ÖNERİ SAYISI KARTTA GÖRÜNÜR: kalite kapısı sessiz çalışırsa "beyin bu hafta 4 öneri
    üretti" ile "beyin 9 üretti, 5'i kanıt-atıfsız düştü" aynı görünür — ve ikincisi beynin kendi
    karnesi hakkında birincisinden ÇOK daha fazla şey söyler."""
    rows = store.read_jsonl("improvement_proposals.jsonl")
    if not rows:
        return {"durum": ("DEFTER BOŞ — ilk satırlar ilk haftalık nous değerlendirmesinde doğar "
                          "(scheduler haftalık kadansı)"),
                "n": 0, "haftalar": [], "son_hafta": None, "oneriler": [],
                "sekil_dagilimi": {}, "oncelik_dagilimi": {}, "n_dusen": 0,
                "rol": "RAPOR — öneriler UYGULANMAZ; yalnız parametre-şekilli olanlar ÖLÇÜM sırasına girer"}
    haftalar = sorted({str(r.get("hafta") or "?") for r in rows})
    son = haftalar[-1] if haftalar else None
    guncel = [r for r in rows if str(r.get("hafta") or "?") == son]
    sekil: dict[str, int] = {}
    oncelik: dict[str, int] = {}
    for r in guncel:
        sekil[str(r.get("sekil") or "?")] = sekil.get(str(r.get("sekil") or "?"), 0) + 1
        oncelik[str(r.get("oncelik") or "?")] = oncelik.get(str(r.get("oncelik") or "?"), 0) + 1
    kosu = store.read_json("nous_eval_runs.json", {}) or {}
    son_kosu = ((kosu.get("haftalar") or {}).get(str(son)) or {}) if son else {}
    return {
        "durum": "dolu",
        "n": len(rows), "haftalar": haftalar[-limit_hafta:], "son_hafta": son,
        "n_son_hafta": len(guncel),
        "oneriler": [{k: r.get(k) for k in
                      ("id", "hafta", "alan", "gozlem", "oneri", "beklenen_etki", "onerilen_olcum",
                       "oncelik", "sekil", "kanit_atifi", "kuyruk", "kuyruk_id", "akibet")}
                     for r in guncel],
        "sekil_dagilimi": sekil, "oncelik_dagilimi": oncelik,
        # KALİTE KAPISI İSTATİSTİĞİ koşu kaydından gelir (düşen öneri DEFTERE YAZILMAZ — defter
        # kabul edilenlerin kaydıdır; düşenlerin SAYISI ve NEDENİ koşu kaydında durur).
        "n_dusen": int(son_kosu.get("n_dusen") or 0),
        "dusme_nedenleri": son_kosu.get("dusme_nedenleri") or {},
        "n_uretilen": son_kosu.get("n_uretilen"),
        "beyin": son_kosu.get("beyin"), "model": son_kosu.get("model"),
        "kosu_durumu": son_kosu.get("durum"),
        "devreden": son_kosu.get("devreden") or [],
        "rol": ("RAPOR — öneriler UYGULANMAZ. Yalnız `sekil=parametre` olanlar H4 bütçesi içinde "
                "ÖLÇÜM sırasına girer; `sekil=cekirdek_hakkinda` YAPISAL olarak kuyruğa GİREMEZ."),
    }


# =================================================================================================
# İCRA GERÇEKLİĞİ: SLİPAJ ÖZETİ · KÖTÜMSER BAND · GECE/GÜNDÜZ
# =================================================================================================
# Üçü de SAF OKUMA: hiçbir dosyaya yazmaz, hiçbir kapıya bağlı değildir, `probgate`/`prescreen`
# çıktılarına DOKUNMAZ. Ölçüm kartı bir EDGE kartı değil İCRA kartıdır — bu yüzden buradaki
# sayılar bir hüküm üretmez, hükümlerin YANINA ikiz sütun/kolon olarak durur.
ENTRY_LEDGER = "entry_execution.jsonl"     # yazan: loop (giriş icra yolu) — bkz. loop.ENTRY_LEDGER
ENTRY_SUMMARY_DAYS = 7                     # "haftalık özet" penceresi (takvim günü)
BAND_MIN_N = 20                            # ampirik banda geçiş için asgari ÖLÇÜLMÜŞ dolum


def _entry_rows(days: int | None = None) -> list:
    """Giriş icra defterinin satırları; `days` verilirse yalnız son o kadar TAKVİM gününe ait olanlar."""
    rows = store.read_jsonl(ENTRY_LEDGER)
    if not days:
        return rows
    cutoff = (dt.date.today() - dt.timedelta(days=days)).isoformat()
    return [r for r in rows if str(r.get("date") or "") >= cutoff]


def entry_execution_summary(days: int = ENTRY_SUMMARY_DAYS) -> dict:
    """GİRİŞ İCRA / SLİPAJ DEFTERİNİN HAFTALIK ÖZETİ.

    ÜÇ SORUYU AYRI AYRI CEVAPLAR (biri diğerinin yerine geçemez):
      1. AYNA GÖNDERİYOR MU? — gönderim/ret/veto sayıları + RET NEDENİ DAĞILIMI. Kartın başarı
         ölçütü (a) tam olarak budur: `stop_vs_current` sınıfı sıfıra inmeli (95/95 reddin kökü).
      2. DOLUM NE KADARA GELDİ? — `fill_vs_resmi_acilis_bps` (açılış mikroyapısının faturası) ve
         `fill_vs_limit_bps` (yasanın tavanı bağladı mı?) dağılımları.
      3. İKİ MOTOR AYNI ŞEYİ Mİ YAPTI? — aynı `plan_id` için iç motorun kararı ile aynanın kararı.

    ÜÇÜNÜN YANINDA DÖRDÜNCÜ BİR KOVA DURUR ama bir SORU DEĞİL, betimleyici bir sayımdır: `kapi`
    (`motor="kapi"`, yazan `loop._armed_drop_row`). O satırlar hiç icra edilmemiş — kapıda düşmüş —
    silahlı planlardır; oran/eşik üretmezler ve kill paydasının DIŞINDADIR (bkz. bölüm 4).

    `n=0` bir kusur DEĞİL bir DURUMDUR ve öyle yazılır: defter bugün doğdu, ilk satırlar ilk
    `alpaca_paper` döngüsünde düşer. Boş defterden ortalama üretmek (0.0 bps) "slipaj yok" demek
    olurdu."""
    rows = _entry_rows(days)
    tum = store.read_jsonl(ENTRY_LEDGER)
    ayna = [r for r in rows if r.get("motor") == "ayna"]
    ic = [r for r in rows if r.get("motor") == "ic"]
    kapi = [r for r in rows if r.get("motor") == "kapi"]
    out: dict = {
        "pencere_gun": days, "n": len(rows), "n_defter": len(tum),
        "ayna": {"n": len(ayna)}, "ic_motor": {"n": len(ic)}, "kapi": {"n": len(kapi)},
        "durum": ("defter boş — ilk satır ilk ayna döngüsünde düşer (BROKER=alpaca_paper)"
                  if not tum else "dolu"),
        "kaynak": f"state/{ENTRY_LEDGER} (yazan: loop; E1 yasası: broker.entry_law)",
    }
    # --- 1) AYNA: gönderim / ret / veto + RET NEDENİ DAĞILIMI --------------------------------
    kararlar: dict = defaultdict(int)
    red_sinif: dict = defaultdict(int)
    for r in ayna:
        kararlar[str(r.get("karar") or "?")] += 1
        if r.get("red_sinifi"):
            red_sinif[str(r["red_sinifi"])] += 1
    gonderilen = kararlar.get("submitted", 0)
    reddedilen = kararlar.get("rejected", 0)
    out["ayna"].update({
        "karar_dagilimi": dict(kararlar), "red_sinifi_dagilimi": dict(red_sinif),
        # RET ORANI kartın (a) ölçütü. Payda GÖNDERİM DENEMESİdir (veto ve ulaşılamama HARİÇ):
        # kendi vetomuzu broker reddi saymak, brokerin sağlığı hakkında yanlış sayı üretirdi.
        "red_orani": (round(reddedilen / (gonderilen + reddedilen), 4)
                      if (gonderilen + reddedilen) else None),
        "emir_tipi_dagilimi": _sayac(ayna, "emir_tipi"), "tif_dagilimi": _sayac(ayna, "tif"),
    })
    # --- 2) DOLUM: iki bps dağılımı -----------------------------------------------------------
    dolan = [r for r in ayna if r.get("fill") is not None]
    out["ayna"]["dolum"] = {
        "n_dolan": len(dolan),
        "dolum_orani": (round(len(dolan) / gonderilen, 4) if gonderilen else None),
        "fill_vs_resmi_acilis_bps": _bps_ozet([r.get("fill_vs_resmi_acilis_bps") for r in dolan]),
        "fill_vs_limit_bps": _bps_ozet([r.get("fill_vs_limit_bps") for r in dolan]),
        # "tavan gevşetilebilir" bir HÜKÜMdür ve n_dolan<BAND_MIN_N iken
        # SUSTURULUR — dört dolumla "tavan gevşetilebilir" demek az örnekten hüküm uydurmaktır
        # (UYDURMA YASAĞI). Dağılım yine gösterilir; yalnız HÜKÜM cümlesi ampirik eşiğe bağlanır
        # (aynı eşik ampirik bandın BAND_MIN_N'i — tek eşik, iki okuyucu).
        "yorum": (
            ("fill_vs_limit_bps ≈ 0 → limit BAĞLADI (tavanda dolduk); belirgin NEGATİF → "
             "yasa para bıraktı, tavan gevşetilebilir (kart grid'inin ölçüm girdisi)")
            if len(dolan) >= BAND_MIN_N else
            (f"n_dolan={len(dolan)} < {BAND_MIN_N} — HÜKÜM YOK: dağılım gösterilir ama tavan "
             f"hükmü verilemez (ampirik eşik {BAND_MIN_N} dolum). Az örnekten hüküm UYDURULMAZ "
             f"(UYDURMA YASAĞI); hüküm cümlesi bu örneklemde SUSTURULDU")),
    }
    # --- 3) İÇ MOTOR: dolum / kaçan işlem ------------------------------------------------------
    ic_karar = _sayac(ic, "karar")
    ic_dolan = [r for r in ic if r.get("karar") == "fill"]
    # İç motorun "dolum vs resmî açılış" bps'i TOTOLOJİKtir (dolum açılıştan
    # sabit slippage ile türer) → yazar (loop) satıra None + beyan bırakır. Özet o beyanı satırdan
    # SURFACE eder (modül-bağımsız: analytics loop'u import etmez). `_bps_ozet` None'ları paydadan
    # düşürür (ort=None, n_olculemeyen=n) — 0 basmaz. `fill_vs_limit_bps` (limit-bacağı) AYRIDIR.
    _ic_beyan = next((r.get("fill_vs_resmi_acilis_beyan") for r in ic_dolan
                      if r.get("fill_vs_resmi_acilis_beyan")), None)
    out["ic_motor"].update({
        "karar_dagilimi": ic_karar,
        "n_dolan": len(ic_dolan),
        # KART KILL-KRİTERİ: "dolmama > %40 ise tasarım geri döner". Sayı burada ÖLÇÜLÜR.
        "dolmama_orani": (round(1 - len(ic_dolan) / len(ic), 4) if ic else None),
        "kacan_limit_n": ic_karar.get("entry_missed_limit", 0),
        "gap_veto_n": ic_karar.get("entry_gap_veto", 0),
        "kill_esigi": 0.40,
        "fill_vs_resmi_acilis_bps": _bps_ozet([r.get("fill_vs_resmi_acilis_bps") for r in ic_dolan]),
        "fill_vs_resmi_acilis_beyan": _ic_beyan,   # totoloji: yazar None + beyan bıraktı
    })
    # --- 4) KAPIDA DÜŞEN SİLAHLI PLANLAR (BETİMLEYİCİ SAYIM — ORAN/EŞİK YOK) -------------------
    # `motor="kapi"` satırlarını yazan `loop._armed_drop_row`tur: plan silahlıydı, kapı kapalıydı,
    # dolum HİÇ denenmedi. Burada YALNIZ sayılır — oran/eşik üretmek ön-kayıtsız YENİ bir ölçüt
    # doğururdu (ölçüm grid'inin dışında kalırdı). Gate adı üç kademede okunur:
    # `red_detay.kapi` → `karar`ın `armed_dropped_` öneki soyulmuş hâli → "?" (BİLİNMEYEN GİZLENMEZ:
    # sınıflanamayan satır ham olarak sayılır, sessizce düşürülmez).
    kapi_dag: dict = defaultdict(int)
    for r in kapi:
        g = (r.get("red_detay") or {}).get("kapi")
        if not g:
            k = str(r.get("karar") or "")
            g = k[len("armed_dropped_"):] if k.startswith("armed_dropped_") else None
        kapi_dag[str(g) if g else "?"] += 1
    out["kapi"].update({
        "kapi_dagilimi": dict(kapi_dag),
        "not": ("Bu satırlar ne iç motorun ne aynanın İCRA KARARIDIR — plan ikisine de ULAŞMADAN "
                "kapıda düştü, dolum HİÇ denenmedi. BİLEREK `ic_motor.dolmama_orani` paydasının "
                "DIŞINDADIR: kill ölçütünün paydasını şişirmek eşiği kod değişikliğiyle sessizce "
                "kaydırırdı (kill-list dokunulmazdır — kart EXE-2026-001)."),
    })
    # --- 5) İKİ MOTOR MUTABAKATI (kartın (c) ölçütü) -------------------------------------------
    ic_by = {r.get("plan_id"): r for r in ic if r.get("plan_id")}
    ayrisan, ortak = [], 0
    for r in ayna:
        pid = r.get("plan_id")
        o = ic_by.get(pid)
        if not o:
            continue
        ortak += 1
        ayna_girdi = r.get("karar") in ("submitted",) and r.get("fill") is not None
        ic_girdi = o.get("karar") == "fill"
        if ayna_girdi != ic_girdi:
            ayrisan.append({"plan_id": pid, "ticker": r.get("ticker"),
                            "ayna": r.get("karar"), "ayna_fill": r.get("fill"),
                            "ic": o.get("karar")})
    out["mutabakat"] = {
        "ortak_plan_n": ortak, "ayrisan_n": len(ayrisan), "ayrisan": ayrisan[:10],
        "not": ("AYRIŞMA GİZLENMEZ (kart kill_criteria): iki motor hizalanamıyorsa fark KALICI "
                "ÖLÇÜM olarak durur. `ayna_fill=None` + `ic=fill` satırları ayna dolumunun henüz "
                "uzlaştırılmadığı (aynı gün) hâli de olabilir — pencere ilerledikçe kapanır."),
    }
    return out


def _sayac(rows: list, alan: str) -> dict:
    """Satırlarda bir alanın değer dağılımını sayar: `{deger: adet}`.

    Alanı None olan satır HİÇ sayılmaz — ölçülemeyen bir değer kendi kovasını doldurmaz."""
    out: dict = defaultdict(int)
    for r in rows:
        v = r.get(alan)
        if v is not None:
            out[str(v)] += 1
    return dict(out)


def _bps_ozet(vals: list) -> dict:
    """bps listesinin özeti. ÖLÇÜLEMEYEN (None) satırlar paydadan DÜŞER ve `n_olculemeyen` ile
    ayrı raporlanır — 0.0 saymak "slipaj yoktu" demek olurdu."""
    v = [float(x) for x in vals if x is not None]
    yok = len(vals) - len(v)
    if not v:
        return {"n": 0, "n_olculemeyen": yok, "ort": None, "medyan": None,
                "p90": None, "min": None, "maks": None}
    s = sorted(v)
    return {"n": len(v), "n_olculemeyen": yok,
            "ort": round(sum(v) / len(v), 3), "medyan": round(s[len(s) // 2], 3),
            "p90": round(s[min(len(s) - 1, int(0.9 * len(s)))], 3),
            "min": round(s[0], 3), "maks": round(s[-1], 3)}


# ---- KÖTÜMSER MALİYET BANDI ---------------------------------------------------------------
# NEDEN VAR. Yürürlükteki friksiyon modeli tek yönde 5 bps'tir ve bu GÜN İÇİ ortalama bir spread
# varsayar. Ama bu sistemin girişlerinin TAMAMI AÇILIŞTA olur; açılış müzayedesinin efektif
# spread'i gün ortasının katıdır ve large-cap'te bile onlarca bps'e çıkar (Bogousslavsky-Muravyev
# 2023 JFM). Yani modelimiz TAM OLARAK en pahalı anı en ucuz varsayımla fiyatlıyor.
# İKİZ SÜTUN, YENİ HÜKÜM DEĞİL: dört dolar ölçütü bu depoda YAZILI bir sözleşmedir (`passed/4`).
# Bant onları DEĞİŞTİRMEZ; yanlarına "aynı defter, kötümser dolum varsayımıyla" sütunu koyar.
def pessimistic_band(goal: dict | None = None) -> dict:
    """Yürürlükteki kötümser band. Kaynak `goal.yaml → pessimistic_band_v2` (DEĞİŞMEZ dosya).

    EK MALİYET GİRİŞ BACAĞINDADIR: kötümser varsayım açılış müzayedesiyle ilgilidir ve bu sistem
    YALNIZ girişte açılıştadır (çıkışlar bar-içi dokunuş). `ek_bps = max(0, açılış_spread/2 −
    yürürlükteki_slipaj)`; yarım spread, marketable bir emrin ödediği taraftır.

    AMPİRİK ÜSTÜNDÜR: operatör `ampirik_bps`i doldurduysa (bkz. `pessimistic_band_update`) literatür
    değeri yerine O kullanılır ve `taban: "ampirik"` yazılır. Doldurulmadıysa None kalır — ölçülmemiş
    bir sayıyı ölçülmüş göstermeyiz."""
    g = goal or config.goal()
    blok = (g.get("pessimistic_band_v2") or {}) if isinstance(g, dict) else {}
    slip = float(g.get("slippage_bps", 5) or 0)
    try:
        spread = float(blok.get("acilis_spread_bps") or 0.0)
    except (TypeError, ValueError):  # sessiz-yutma: biçimsiz band → 0 ek maliyet + `taban: yok` ile DIŞARI çıkar
        spread = 0.0
    amp = blok.get("ampirik_bps")
    try:
        amp = None if amp is None else float(amp)
    except (TypeError, ValueError):  # sessiz-yutma: aynı gerekçe; ampirik yoksa literatür tabanı kalır
        amp = None
    if amp is not None:
        ek, taban = max(0.0, amp - slip), "ampirik"
    elif spread > 0:
        ek, taban = max(0.0, spread / 2.0 - slip), "literatur"
    else:
        ek, taban = 0.0, "yok"
    return {"ek_bps_giris": round(ek, 3), "taban": taban,
            "acilis_spread_bps": spread or None, "ampirik_bps": amp,
            "ampirik_n": int(blok.get("ampirik_n") or 0),
            "yururlukteki_slippage_bps": slip,
            "mevcut_model_bps": blok.get("mevcut_model_bps"),
            "kaynak": blok.get("kaynak"),
            "kapsam": ("ek maliyet YALNIZ giriş bacağına uygulanır (girişler açılışta, çıkışlar "
                       "bar-içi); notional = entry × qty")}


def pessimistic_band_update(days: int | None = None) -> dict:
    """GİRİŞ İCRA DEFTERİNDEN AMPİRİK BAND — ÖLÇER, UYGULAMAZ.

    `goal.yaml` DEĞİŞMEZDİR ve bu fonksiyon ona YAZMAZ (bir ajanın kendi maliyet paydasını
    güncellemesi, karnesini kendisinin yazması olurdu). Ölçümü döndürür; `ampirik_bps` alanının
    doldurulması operatör eylemidir ve çıktı bunu `uygulama` alanıyla söyler.

    ÖLÇÜM: dolan aynadaki satırların `fill_vs_resmi_acilis_bps` ORTALAMASI — yani "resmî açılışa
    göre gerçekte ne ödedik?". n < BAND_MIN_N ise sonuç None döner ve `neden` yazılır: 6 dolumdan
    "gerçek açılış maliyeti 12,4 bps" diye bir sayı üretmek ölçüm değil süslemedir."""
    rows = [r for r in _entry_rows(days) if r.get("fill") is not None]
    v = [float(r["fill_vs_resmi_acilis_bps"]) for r in rows
         if r.get("fill_vs_resmi_acilis_bps") is not None]
    band = pessimistic_band()
    out = {"n_dolan": len(rows), "n_olculen": len(v), "min_n": BAND_MIN_N,
           "ampirik_bps": None, "neden": None, "yururlukteki": band,
           "uygulama": ("ÖLÇÜM — goal.yaml'a YAZILMAZ. `pessimistic_band_v2.ampirik_bps` alanını "
                        "doldurmak operatör eylemidir (değişmez dosya sözleşmesi).")}
    if len(v) < BAND_MIN_N:
        out["neden"] = f"ölçülmüş dolum {len(v)} < {BAND_MIN_N} — ampirik band HENÜZ YOK"
        return out
    s = sorted(v)
    out["ampirik_bps"] = round(sum(v) / len(v), 3)
    out["medyan_bps"] = round(s[len(s) // 2], 3)
    out["p90_bps"] = round(s[min(len(s) - 1, int(0.9 * len(s)))], 3)
    return out


def _kotumser_ek_dolar(trades: list, band: dict) -> tuple[float | None, int, int]:
    """Bandın DOLAR karşılığı: Σ ek_bps × giriş notional'ı. Dönen: (ek_dolar, n_olculen, n_atlanan).
    `entry`/`qty` taşımayan satır ATLANIR ve sayılır — notional uydurulmaz."""
    ek = float(band.get("ek_bps_giris") or 0.0) / 10000.0
    top, n, atlanan = 0.0, 0, 0
    for t in trades:
        try:
            notional = float(t["entry"]) * float(t["qty"])
        except (TypeError, ValueError, KeyError):  # sessiz-yutma: alan yok/biçimsiz → satır `n_atlanan` SAYACINA yazılıyor ve o sayaç çıktıya çıkıyor
            atlanan += 1
            continue
        top += notional * ek
        n += 1
    return (round(top, 2) if n else None), n, atlanan


def net_kotumser() -> dict:
    """PARA-v3 RAPOR YÜZEYİNİN İKİZ SÜTUNU: aynı defter, kötümser dolum varsayımıyla.

    HÜKME GİRMEZ (`hukme_girmez: True`) — dört dolar ölçütünün sayaçlarına dokunmaz, `passes`
    üretmez, hiçbir kapıya bağlı değildir. Söylediği tek şey şudur: "bugünkü net, açılış spread'i
    literatürdeki gibi olsaydı ne olurdu?" Ölçüt eşiklerinden biri (net > friksiyon) bu sütunda
    düşüyorsa, kenar dolum kalitesine bağımlıdır ve bu bilinmeye değer."""
    band = pessimistic_band()
    trades = _trades()
    pnls = [float(t["pnl_dollars"]) for t in trades if t.get("pnl_dollars") is not None]
    net = round(sum(pnls), 2) if pnls else None
    ek, n_olc, n_atl = _kotumser_ek_dolar(trades, band)
    kotumser = (None if (net is None or ek is None) else round(net - ek, 2))
    return {
        "band": band, "net": net, "ek_maliyet": ek, "net_kotumser": kotumser,
        "n": len(trades), "n_olculen": n_olc, "n_notional_yok": n_atl,
        "isaret_donuyor": (None if (net is None or kotumser is None)
                           else bool(net > 0 and kotumser <= 0)),
        "hukme_girmez": True,
        "kapsam": ("ek maliyet yalnız GİRİŞ bacağına (girişler açılışta) uygulanır; `pnl_dollars` "
                   "zaten NET'tir ve friksiyon İKİ KEZ kesilmez — bu sütun mevcut modelin ÜSTÜNE "
                   "yalnız FARKI (açılış_spread/2 − yürürlükteki_slipaj) ekler"),
    }


# ---- GECE / GÜNDÜZ AYRIŞTIRMASI ------------------------------------------------------------
# NEDEN VAR (Lou-Polk-Skouras 2019 JFE): momentum getirisinin İŞARETİ gece ve gündüz bacaklarında
# ZITTIR — momentum geceye, tersine-dönüş gündüze yığılır. Bu sistemin girişleri AÇILIŞTA olur,
# yani her işlem önce bir GECE bacağı satın alır. "Kâr nereden geliyor?" sorusunun bu ekseni bugüne
# dek hiç sorulmadı; ölçülen "yalnız 8-15 gün diliminde pozitif" kırılımı ile çaprazlanır.
#
# ÖZDEŞLİK (yaklaşık değil, TAM): close_N − open_0 = Σ(close_i − open_i) + Σ(open_i − close_{i-1}).
# Yani gündüz + gece = TUTULAN YOLUN tamamı. İşlemin GERÇEK pnl_pct'i bundan farklıdır (çıkış
# bar-içi bir seviyededir ve friksiyon fiyatın içindedir) — fark `icra_farki` olarak AYRI raporlanır
# ve tam olarak giriş icra ölçümünün konusudur. Üçünü tek sayıda toplamak, icra maliyetini piyasa
# hareketiymiş gibi göstermek olurdu.
NIGHTDAY_HUCRE_MIN_N = 5
_ND_CACHE: dict = {}       # (defter damgası) → sonuç. Bkz. night_day_split gerekçesi.


def _nd_stamp() -> tuple:
    """Defterin parmak izi — `ledgers.declared_writers`ın `_src_stamp`i ile AYNI desen: sonuç
    yalnız girdiye bağlıysa, damga girdinin mtime'ı olur ve girdi değişince önbellek kendiliğinden
    düşer. Zaman tabanlı bir TTL bunun yerine "bayat sayı kaç dakika gösterilebilir?" sorusunu
    açardı; burada cevap SIFIR.

    STATE YOLU DA DAMGANIN İÇİNDE: testler her koşuda AYRI bir sandbox'a yönlendirilir ve yol
    olmasaydı "defter yok" hâli (0, 0) iki farklı sandbox'ta AYNI anahtara düşerdi — bir testin
    sonucu diğerine sızardı (conftest'in `_clear_module_caches` yazarken şikâyet ettiği sınıf)."""
    # DAMGA ARTIK `store.stamp`: defter SQLite'a taşındığında
    # `state/trades.jsonl` `.migrated` ekiyle DONAR ve mtime'ı bir daha değişmez — bu önbelleği
    # SONSUZA kadar bayat yapardı ve hiçbir yerde görünmezdi. `store.stamp` iki arka uçta da
    # "yalnız içerik değişince değişen" bir demet verir (dosyada mtime+boyut, DB'de updated_at+rev).
    return (str(config.STATE), *store.stamp("trades.jsonl"))


def _nd_ozet(kayitlar: list[dict]) -> dict:
    """Gece/gündüz bacak kayıtlarının özeti: ortalama gece, gündüz, tutulan yol, işlem getirisi,
    icra farkı ve gecenin PAYI.

    Kayıt yoksa tüm alanlar None (`yeterli=False`) — boş örneklem 0.0 sayılmaz. Pay MUTLAK
    büyüklüklerden alınır: zıt işaretli bacaklarda net yol küçülüp oran anlamsızlaşırdı."""
    n = len(kayitlar)
    if not n:
        return {"n": 0, "gece": None, "gunduz": None, "yol": None, "islem": None,
                "icra_farki": None, "gece_payi": None, "yeterli": False}
    g = sum(k["gece"] for k in kayitlar) / n
    d = sum(k["gunduz"] for k in kayitlar) / n
    yol = sum(k["yol"] for k in kayitlar) / n
    isl = sum(k["islem"] for k in kayitlar) / n
    top = abs(g) + abs(d)
    return {"n": n, "gece": round(g, 5), "gunduz": round(d, 5), "yol": round(yol, 5),
            "islem": round(isl, 5), "icra_farki": round(isl - yol, 5),
            # PAY MUTLAK BÜYÜKLÜKTEN: iki bacak zıt işaretliyse (literatürün beklediği hâl) net
            # yol küçülür ve "gecenin payı %480" gibi anlamsız bir oran çıkardı.
            "gece_payi": (round(abs(g) / top, 3) if top > 1e-12 else None),
            "yeterli": bool(n >= NIGHTDAY_HUCRE_MIN_N)}


def night_day_split() -> dict:
    """HER İŞLEMİN TUTUŞ YOLUNU GECE (close→open) ve GÜNDÜZ (open→close) BACAKLARINA AYIRIR.

    Saf okuma: `trades.jsonl` × günlük barlar (`adapters.data.load_bars` — sanitize kapısından geçmiş
    hâl; ham CSV okumak kirletilmiş barları bu ölçüme taşırdı).

    KAYNAK DAMGASI AYRI SATIR: `replay_seed` satırları `training` etiketiyle KENDİ
    kırılımında durur. Tohumun gece/gündüz karakteri "kuralların karakteri"dir, canlı icra DEĞİL;
    ikisini tek ortalamada toplamak, kapatılan karışımın ta kendisi olurdu.

    GİRİŞ GAP'İ AYRI ÖLÇÜLÜR: `giris_gap_bps` = (open_0 / close_{-1} − 1) — bu, SATIN ALDIĞIMIZ
    gece bacağıdır ve tutulan yolun İÇİNDE DEĞİLDİR (yol open_0'da başlar). Giriş yasasının limit tavanı tam
    olarak bu sayıyı kelepçeler, o yüzden yan yana durmaları gerekir.

    SÜREÇ-İÇİ MEMO (ölçüldü: 95 satırlık defterde ~2,4 sn — 76 ayrı sembolün barları diskten
    okunur ve sanitize kapısından geçirilir). `/api/diagnostics` her pano anketinde koşuyor; bu maliyeti
    her istekte ödemek `system_telemetry`nin uçtan çıkarılma gerekçesinin aynısını doğururdu.
    Damga defterin mtime'ıdır: defter değişince önbellek KENDİLİĞİNDEN düşer, yani bayat sayı
    gösterme penceresi YOKTUR."""
    from . import ledgerstamp, obs
    _key = _nd_stamp()
    if _key in _ND_CACHE:
        return _ND_CACHE[_key]

    def _ret(o: dict) -> dict:
        """Sonucu damga anahtarıyla önbelleğe koyup döner (TEK girişlik: eski damga temizlenir).

        Fonksiyonun bütün çıkış dallarının paylaştığı tek kapı — bir dal önbelleği atlayamaz."""
        _ND_CACHE.clear()          # TEK giriş: eski damga bir daha sorulmaz, bellek sabit kalır
        _ND_CACHE[_key] = o
        return o

    trades = _trades()
    out: dict = {
        "n": len(trades), "n_olculebilir": 0, "n_olculemeyen": 0,
        "ozdeslik": "close_N − open_0 = Σ(close−open) [gündüz] + Σ(open−close_prev) [gece]",
        "yontem": ("bacaklar TUTULAN YOLDAN türetilir (giriş açılışı → son seans kapanışı), "
                   "işlemin kendi getirisi `pnl_pct`; ikisinin farkı `icra_farki` = çıkış "
                   "seviyesi + friksiyon (E1/E2'nin ölçtüğü şey)"),
        "genel": None, "kaynak_kirilim": {}, "tutus_dilimi": {}, "capraz": [],
        "giris_gap_bps": None, "hucre_min_n": NIGHTDAY_HUCRE_MIN_N, "neden_bos": None,
    }
    if not trades:
        out["neden_bos"] = "defter boş"
        return _ret(out)
    try:
        from .adapters import data
    except Exception as e:
        out["neden_bos"] = f"bar adaptörü yüklenemedi: {type(e).__name__}"
        return _ret(out)
    kayitlar: list[dict] = []
    gapler: list[float] = []
    bar_cache: dict = {}
    for t in trades:
        tk = t.get("ticker")
        o_d, c_d = str(t.get("ts_open") or "")[:10], str(t.get("ts_close") or "")[:10]
        if not tk or not o_d or not c_d or c_d < o_d:
            out["n_olculemeyen"] += 1
            continue
        if tk not in bar_cache:
            try:
                # pencere BİLEREK geniş: giriş gününün BİR ÖNCEKİ kapanışı da gerekiyor.
                df = data.load_bars(tk, (dt.date.fromisoformat(o_d) - dt.timedelta(days=14)).isoformat(),
                                    c_d, use_cache=True)
                bar_cache[tk] = None if df is None or df.empty else df
            except Exception as e:
                obs.warn("night_day_bars_unavailable", ticker=tk,
                         error=f"{type(e).__name__}: {e}",
                         detail="gece/gündüz ayrıştırması bu işlem için ölçülemedi")
                bar_cache[tk] = None
        df = bar_cache.get(tk)
        if df is None:
            out["n_olculemeyen"] += 1
            continue
        ds = [str(x)[:10] for x in df["date"]]
        try:
            i0, i1 = ds.index(o_d), ds.index(c_d)
        except ValueError:  # sessiz-yutma: giriş/çıkış seansı barlarda YOK → satır `n_olculemeyen` sayacına yazılıyor ve payda çıktıda görünür
            out["n_olculemeyen"] += 1
            continue
        op = [float(x) for x in df["open"]]
        cl = [float(x) for x in df["close"]]
        if op[i0] <= 0:
            out["n_olculemeyen"] += 1
            continue
        gunduz = sum(cl[i] - op[i] for i in range(i0, i1 + 1))
        gece = sum(op[i] - cl[i - 1] for i in range(i0 + 1, i1 + 1))
        yol = cl[i1] - op[i0]
        if i0 > 0 and cl[i0 - 1] > 0:
            gapler.append((op[i0] / cl[i0 - 1] - 1.0) * 10000.0)
        try:
            islem = float(t.get("pnl_pct"))
        except (TypeError, ValueError):  # sessiz-yutma: `pnl_pct` yok/biçimsiz → satır ölçülemeyen sayılıyor
            out["n_olculemeyen"] += 1
            continue
        kn = ledgerstamp.kaynak_of(t)
        kayitlar.append({
            "gece": gece / op[i0], "gunduz": gunduz / op[i0], "yol": yol / op[i0],
            "islem": islem, "dilim": _tutus_dilimi(t.get("bars_held")),
            # KAYNAK ETİKETİ: `replay_seed` = eğitim satırı, canlı kanıt DEĞİL.
            "kaynak": ("training" if kn == ledgerstamp.REPLAY_SEED else kn),
            "aile": t.get("setup") or "?",
        })
    out["n_olculebilir"] = len(kayitlar)
    if not kayitlar:
        out["neden_bos"] = "hiçbir işlemin bar penceresi ölçülemedi"
        return _ret(out)
    out["genel"] = _nd_ozet(kayitlar)
    out["kaynak_kirilim"] = {k: _nd_ozet(v) for k, v in
                             sorted(_grupla(kayitlar, lambda x: x["kaynak"]).items())}
    out["tutus_dilimi"] = {k: _nd_ozet(v) for k, v in
                           sorted(_grupla(kayitlar, lambda x: x["dilim"]).items())}
    # ÇAPRAZ TABLO: kaynak × tutuş-dilimi — "8-15g tek pozitif dilim" kırılımı bu eksende
    # okunur ve tohum/canlı ayrımı korunur (aynı hücrede karışmaz).
    capraz = _grupla(kayitlar, lambda x: (x["kaynak"], x["dilim"]))
    out["capraz"] = [{"kaynak": k, "tutus_dilimi": d, **_nd_ozet(v)}
                     for (k, d), v in sorted(capraz.items())]
    out["giris_gap_bps"] = _bps_ozet(gapler)
    return _ret(out)


def _grupla(kayitlar: list[dict], anahtar) -> dict:
    """Kayıtları `anahtar(kayit)` fonksiyonuna göre gruplar: `{anahtar: [kayıt, ...]}` (özet almaz)."""
    by = defaultdict(list)
    for k in kayitlar:
        by[anahtar(k)].append(k)
    return dict(by)

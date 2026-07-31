"""mutation.py — MUTASYON KOŞUMU: dedektörlerin NEYİ GÖREMEDİĞİNİ ölçer (2026-07-22).

NEDEN VAR: 2026-07-21'de tek günde on üç hata çıktı ve HİÇBİRİ istisna fırlatmadı. Ardından yedi
bütünlük dedektörü (watchdog) ve yazılı bir defter sözleşmesi (ledgers) eklendi. Ama şu soru hiç
sorulmadı: **bu dedektörler hangi bozulma sınıflarını GERÇEKTEN yakalar?**

Gelecekteki hataları sayamayız. Yapabileceğimiz tek dürüst ölçüm şudur: bilinen bozulma sınıflarını
TEK TEK, kontrollü biçimde üretip dedektör bataryasının kırmızıya dönüp dönmediğine bakmak. Bu,
mutasyon testinin KODA değil VERİ SÖZLEŞMELERİNE uygulanmış hâlidir — çünkü 2026-07-21'in hataları
kod hatası değil, şema/kayıt hatalarıydı.

ÇIKTI BİR KÖRLÜK HARİTASIDIR. Düşük bir kapsama sayısı burada BAŞARISIZLIK DEĞİL, en değerli
bulgudur: her MISSED satırı, sistemin bugün göremediği bir hata sınıfının adıdır. Sayıyı yukarı
çekmek için mutasyonu zayıflatmak, ölçümün kendisini yalana çevirir.

TASARIM KARARLARI (hepsi acıyla öğrenilmiş):
  * TEMEL DURUM ÖNCE TEMİZ OLMALI. Kirli bir temel durumda her mutasyon "yakalandı" görünür ve
    kapsama sayısı yalan söyler. run() bunu ölçer ve temel kirliyse DÜRÜSTÇE patlar.
  * Dedektörlerin üçü DURUMLUDUR (determinizm/monotonluk/sahiplik önceki anlık görüntüyle kıyaslar).
    Bu yüzden batarya temel durumda İKİ KEZ koşturulur: birincisi görüntüyü yazar, ikincisi gerçek
    temel durumu ölçer. Mutasyon kopyası bu görüntüleri de taşır — yani "defter kısaldı" gibi
    ihlaller ancak böyle görülebilir.
  * KOŞUM DEFTERLERE `store.*` İLE YAZMAZ. Yazsaydı `ledgers.declared_writers()` bu modülü beyan
    edilmemiş bir yazar sayar, `ledger_writers` satırı kırmızıya döner ve TEMEL DURUM kirlenirdi:
    dedektörü ölçen araç, dedektörün ölçtüğü şeyi bozmuş olurdu. Dosyalar doğrudan yazılır.
  * CANLI `state/` DİZİNİNE ASLA DOKUNMAZ (aşağıdaki _assert_not_live her yolda çağrılır).

Kullanım:  python -m meridian.mutation        (ya da: from meridian.mutation import run)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import os
import shutil
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import yaml

from . import config
from .score import START_EQUITY      # TEK kaynak: burada sabit yazmak, bu denetimin kovaladığı
                                     # "aynı yasanın iki uygulaması" hatasının kendisi olurdu
                                     # (recompute.py de aynı sabiti oradan okuyor).

LOG = logging.getLogger("meridian.mutation")

# Canlı defter — koşumun ASLA dokunamayacağı yol. config.STATE test/koşum sırasında yamalanabildiği
# için sabit ROOT'tan türetilir (yamalı bir STATE'i "canlı değil" sanmak tam da istemediğimiz hata).
_LIVE_STATE = (Path(config.ROOT) / "state").resolve()


# =============================================================================================
# YOL GÜVENLİĞİ + DURUM BAĞLAMI
# =============================================================================================
def _assert_not_live(p: Path) -> Path:
    rp = Path(p).resolve()
    if rp == _LIVE_STATE or _LIVE_STATE in rp.parents or rp in _LIVE_STATE.parents:
        raise RuntimeError(f"mutasyon koşumu canlı defterin yakınına yazamaz: {rp}")
    return rp


@contextmanager
def using_state(path: Path):
    """config.STATE'i geçici dizine yönlendir. goal/bounds lru_cache'i her iki uçta da boşaltılır —
    aksi hâlde bir önceki dizinin goal'ü yeni dizinde kullanılırdı (canlıda yaşanan dondurma hatası)."""
    path = _assert_not_live(path)
    old = (config.STATE, config.HISTORY, config.BARS)
    config.STATE, config.HISTORY, config.BARS = path, path / "history", path / "bars"
    config.reload_config()
    try:
        yield path
    finally:
        config.STATE, config.HISTORY, config.BARS = old
        config.reload_config()


@contextmanager
def quiet_externals():
    """AĞA çıkan iki üretkenlik kontrolünü sustur (S&P üyelik kaynağı, FMP). Bunlar dedektörün değil
    İNTERNETİN durumunu ölçer; koşumda kırmızı kalsalar temel durum hiç temizlenemezdi. Neyi
    sustuğumuz raporda yazar — sessizce yok saymıyoruz, KAPSAM DIŞI olduğunu söylüyoruz."""
    from .adapters import constituents, fmp
    old_c, old_f = constituents.health, fmp.available
    constituents.health = lambda: {"ok": True, "note": "mutasyon koşumu: ağ kontrolü kapsam dışı"}
    fmp.available = lambda: False
    LOG.info("ağ tabanlı üretkenlik kontrolleri kapsam dışı: sp500_membership, fmp_source")
    try:
        yield
    finally:
        constituents.health, fmp.available = old_c, old_f


# =============================================================================================
# GERÇEKÇİ, SÖZLEŞMEYE UYAN TEMEL DURUM
# =============================================================================================
def _wjson(state: Path, name: str, obj) -> None:
    (state / name).write_text(json.dumps(obj, indent=2))


def _wjsonl(state: Path, name: str, rows: list) -> None:
    (state / name).write_text("".join(json.dumps(r) + "\n" for r in rows))


def rjsonl(state: Path, name: str) -> list:
    p = state / name
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def rjson(state: Path, name: str, default=None):
    p = state / name
    return json.loads(p.read_text()) if p.exists() else default


UNIVERSE = [("AAPL", "tech"), ("JPM", "financials"), ("UNH", "health"), ("CAT", "industrials"),
            ("XOM", "energy"), ("KO", "staples"), ("NKE", "consumer"), ("MRK", "health")]
SESSIONS = [f"2026-06-{d:02d}" for d in range(1, 25)]      # 24 seans
BOOK_DATE = "2026-06-25"                                    # defterin son tarihi (planlar bundan eski)


def build_state(dest: Path) -> Path:
    """Dedektörlerin YARGILAYACAK bir şeyi olsun diye gerçekçi bir defter seti üretir. Satır
    şekilleri mümkün olan her yerde GERÇEK üreticilerden gelir (broker işlem satırını, guard karar
    ağacını üretir) — elle yazılmış bir fixture, sözleşmeden sessizce ayrışabilirdi."""
    dest = _assert_not_live(dest)
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "bars").mkdir(exist_ok=True)
    (dest / "history").mkdir(exist_ok=True)
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(_LIVE_STATE / f, dest / f)             # SALT OKUMA: canlı sözleşme kopyalanır
    (dest / "strategy.yaml").write_text(yaml.safe_dump(config.default_strategy()))

    with using_state(dest):
        _build_ledgers(dest)
        _build_artifacts(dest)
    return dest


def _build_ledgers(state: Path) -> None:
    from . import guard
    from .broker import PaperBroker

    goal = config.goal()
    params = config.default_strategy()["params"]
    regime = {"date": BOOK_DATE, "regime": "chop", "exposure_budget_pct": 45,
              "leading_sectors": ["tech", "energy"]}

    plans, trades, cfs, candidates = [], [], [], []
    broker = PaperBroker(START_EQUITY, 5.0, 0.005)
    for i, sess in enumerate(SESSIONS):
        tkr, sec = UNIVERSE[i % len(UNIVERSE)]
        px = 100.0 + i
        plan = {"id": f"P-{sess}-{tkr}", "date": sess, "ticker": tkr, "side": "long",
                "entry_trigger": round(px, 4), "stop": round(px * 0.95, 4),
                "targets": [round(px * 1.15, 4)], "profit_target": round(px * 1.15, 4),
                "size_r": 1.0, "r_multiple_expected": 3.0, "regime_at_plan": "chop",
                "sector": sec, "score": 68 + (i % 12), "setup": "breakout_vcp",
                "dormant_setup": False, "strategy_version": 1,
                "skill_chain": ["vcp-screener", "position-sizer", "pre-trade-discipline-gate"]}
        portfolio = {"open_positions": i % 3, "sector_counts": {sec: i % 2},
                     "day_pnl_pct": 0.0, "open_risk_r": 1.0, "max_corr": 0.2}
        checks: list = []
        verdict, reasons = guard.classify_gate(plan, portfolio, regime, goal, params,
                                               detail_out=checks)
        # her 5. plan bilinçli olarak kapıda ölsün: NO_GO da MEŞRU bir terminal durumdur ve
        # korunum dedektörünün "sessiz kayıp" tanımı buna dayanır.
        if i % 5 == 4:
            verdict, reasons = "NO_GO", list(reasons) + ["mutasyon koşumu: kapıda ölen plan"]
        checks.append({"check": "earnings_blackout", "passed": True, "severity": "hard",
                       "value": tkr, "threshold": None, "coverage": "known", "note": None})
        plan["gate_verdict"], plan["gate_reasons"], plan["gate_checks"] = verdict, reasons, checks
        if i % 3 == 0:
            plan["llm_opinion"] = "destekle"
        plans.append(plan)
        candidates.append({"date": sess, "ticker": tkr, "score": plan["score"],
                           "setup": "breakout_vcp", "sector": sec, "source_skill": "vcp-screener"})

        if verdict != "NO_GO":            # GERÇEK ÜRETİCİ: işlem satırını broker yazar
            broker.fill_entry(plan, px, sess, START_EQUITY)
            close_px = px * (1.08 if i % 3 else 0.96)
            row = broker.close_position(tkr, close_px, "target" if i % 3 else "stop",
                                        f"2026-06-{min(28, int(sess[-2:]) + 3):02d}")
            if row:
                trades.append(row)
        # cf ŞEMASI counterfactual.collect ile HİZALI olmalı (2026-07-23, tarama bulgusu): build_state
        # yalnız `gate_verdict`/`plan_id` yazıyordu ama validation_report.py:30-31 `verdict` ve `taken`
        # okuyor — ikisi de None kalıyor ve o tüketiciyi bozan mutasyonlar TEMEL DURUMDA da None gördüğü
        # için asla yakalanamıyordu (kapsama sahte yüksek). Kanonik alanlar da yazılır.
        cfs.append({"id": f"CF-{sess}-{tkr}", "date": sess, "ticker": tkr, "setup": "breakout_vcp",
                    "regime": "chop", "status": "closed_target" if i % 3 else "closed_stop",
                    "r_multiple_expected": 3.0, "rr_expected": 3.0,
                    "r_multiple": 1.2 if i % 3 else -1.0, "entered": True,
                    "plan_id": f"P-{sess}-{tkr}", "gate_verdict": verdict,
                    "verdict": verdict, "taken": verdict != "NO_GO", "dormant": False,
                    "screener": "vcp-screener"})

    _wjsonl(state, "trade_plans.jsonl", plans)
    _wjsonl(state, "trades.jsonl", trades)
    _wjsonl(state, "counterfactuals.jsonl", cfs)
    _wjsonl(state, "candidates.jsonl", candidates)
    _wjsonl(state, "hypotheses.jsonl", [
        {"id": f"H{i:05d}", "ts": f"2026-06-{i:02d}T12:00:00+00:00", "variable": "entry.min_score",
         "new": 60 + i, "status": "proposed" if i % 2 else "shipped"} for i in range(1, 8)])
    _wjsonl(state, "spend.jsonl", [
        {"ts": f"2026-06-{i:02d}T09:00:00+00:00", "model": "claude-opus-4-8",
         "cost_usd": 0.01 * i, "in_tokens": 900, "out_tokens": 300} for i in range(1, 9)])
    _wjsonl(state, "pipeline_runs.jsonl", [
        {"run_id": f"R{i:04d}", "pipeline": p, "started": f"2026-06-{i:02d}T21:05:00+00:00",
         "status": "ok", "artifact": "state/candidates.jsonl"}
        for i, p in enumerate(["P1_REGIME", "P2_SCREEN", "P3_PLAN", "P4_EXECUTE"] * 2, start=1)])
    # OLAY DEFTERİ: makullük dedektörü döngü sayısına ve aday verimine buradan bakar. Ayrıca
    # korunum dedektörünün "canlı dönem" sınırı ilk daily_cycle olayının tarihidir — planların
    # HEPSİ o sınırın içinde kalmalı, yoksa "replay dönemi" sayılıp yargılanmazlar (ve o zaman
    # mutasyonlar da görünmezdi).
    events = [{"ts": "2026-05-30T21:00:00+00:00", "level": "info", "event": "daily_cycle",
               "date": "2026-05-30", "candidates": 4, "armed": 1, "plans": 3}]
    for i, sess in enumerate(SESSIONS):
        events.append({"ts": f"{sess}T21:00:00+00:00", "level": "info", "event": "daily_cycle",
                       "date": sess, "candidates": 3 + (i % 4), "armed": i % 2, "plans": 2})
    _wjsonl(state, "events.jsonl", events)


def _build_artifacts(state: Path) -> None:
    trades = rjsonl(state, "trades.jsonl")
    n_tr = len(trades)
    # YENİDEN HESAP dedektörü (recompute.py) aynı büyüklüğü iki yoldan hesaplayıp kıyaslıyor:
    # nakit kimliği, gerçekleşen K/Z, sermaye eğrisinin kuyruğu, karne örneklemi. Temel durumun
    # bunları TUTTURMASI şart — tutturmazsa her mutasyon "yakalandı" görünürdü.
    realized = round(sum(float(t.get("pnl_dollars") or 0.0) for t in trades), 2)
    cash = round(START_EQUITY + realized, 2)
    # --- KAYNAKLAR (türevlerden ÖNCE yazılır: tutarlılık dedektörü mtime kıyaslar) ---
    _wjson(state, "portfolio.json", {"last_date": BOOK_DATE, "cash": cash, "positions": {},
                                     "armed": [], "peak_equity": max(104_000.0, cash),
                                     "realized_pnl": realized,
                                     "day_start_equity": cash, "alpaca_submitted": []})
    _wjson(state, "regime.json", {"date": BOOK_DATE, "regime": "chop", "exposure_budget_pct": 45,
                                  "leading_sectors": ["tech", "energy"], "score": 55})
    _wjson(state, "data_quality.json", {"date": BOOK_DATE, "index_ok": True, "index_issues": [],
                                        "tickers_failed": [], "universe": len(UNIVERSE),
                                        "data_halt": False})
    _wjson(state, "heartbeat.json", {"ts": f"{BOOK_DATE}T21:10:00+00:00", "regime": "chop",
                                     "exposure_budget_pct": 45, "equity": 103_500.0,
                                     "last_bar": BOOK_DATE, "version": 1, "open_positions": 0})
    _wjson(state, "wf_cache_rev.json", {"rev": 3})
    # eğrinin SON noktası kitabın nakdi olmak zorunda (recompute: equity_curve_tail)
    _wjson(state, "equity_curve.json", {"version": 1, "points":
           [[s, round(START_EQUITY + realized * (i + 1) / len(SESSIONS), 2)]
            for i, s in enumerate(SESSIONS)]})
    # ELEME MUHASEBESİ (sieve): tüketicilerin kaç satır gördüğü/elediği. Temel durumda yalnız
    # MEŞRU (piyasa:) elemeler var — şema elemesi sıfır, yani sözleşme tutuyor.
    _wjson(state, "sieve.json", {
        "score_calibration.gercek": {"in": n_tr, "out": n_tr, "drops": {},
                                     "ts": f"{BOOK_DATE}T22:00:00+00:00"},
        "shadow_model.egitim": {"in": 30, "out": 27, "drops": {"piyasa:skor_esigin_altinda": 3},
                                "ts": f"{BOOK_DATE}T22:00:00+00:00"}})
    _wjson(state, "skills_registry.json", {"skills": {
        "vcp-screener": {"enabled": True, "mode": "active", "pipeline": "P2_SCREEN"}}})
    # kazanç takvimi: GELECEK tarih yoksa karartma guard'ı fiilen kapalıdır ve üretkenlik dedektörü
    # (haklı olarak) bunu 'starved' sayar — temel durumun temiz olması için takvim canlı tutulur.
    (state / "earnings.csv").write_text(
        "ticker,date\n" + "".join(f"{t},2027-02-{(i % 27) + 1:02d}\n"
                                  for i, (t, _) in enumerate(UNIVERSE)))
    for i in range(3):
        (state / "bars" / f"SYM{i}.csv").write_text(
            "date,open,high,low,close,volume\n" +
            "".join(f"2026-06-{d:02d},10,11,9,10.5,1000000\n" for d in range(1, 26)))

    # --- TÜREVLER (kaynaklardan SONRA) ---
    _wjson(state, "score_calibration.json", {"n": 60, "n_real": n_tr, "n_cf": 60 - n_tr,
                                             "buckets": {"60-70": {"n": 30, "avg_r": 0.4}}})
    _wjson(state, "near_miss.json", {"resolved_total": 42, "blockers": {"volume_ratio": 20}})
    _wjson(state, "regime_edge.json", {"chop": {"n": 40, "avg_r": 0.35},
                                       "trend_up": {"n": 25, "avg_r": 0.6}})
    _wjson(state, "cf_fidelity.json", {"n": 25, "corr": 0.78, "mean_diff_r": 0.12,
                                       "fidelity_ok": True})
    _wjson(state, "exit_efficiency.json", {"n": 18, "capture_pct": 61.0})
    _wjson(state, "llm_calibration.json", {"n_pairs": 12, "buckets": {"destekle": {"n": 12}},
                                           "promoted": False})
    _wjson(state, "gate_calibration.json", {"n_measured": 30, "go_win_rate": 0.44})
    _wjson(state, "shadow_model.json", {"n": 60, "brier": 0.21, "promoted": False})
    _wjson(state, "self_review.json", {"ts": f"{BOOK_DATE}T22:00:00+00:00", "findings": []})
    _wjson(state, "arming_report.json", {"n": 30, "candidates": []})
    _wjson(state, "scoreboard.json", {"current_version": "1",
                                      "versions": {"1": {"oos_score": 0.42, "n_trades": n_tr}}})
    _wjson(state, "broker_reconcile.json", {"ts": f"{BOOK_DATE}T21:15:00+00:00", "positions": {},
                                            "alive_order_syms": []})


# =============================================================================================
# DEDEKTÖR BATARYASI — "kırmızı" jetonların kümesi
# =============================================================================================
def detector_red(log: list | None = None) -> set[str]:
    """Bataryayı koştur ve KIRMIZI olan her şeyi tek bir jeton kümesine indir. Karşılaştırma
    küme farkıyla yapılır: mutasyondan SONRA beliren jeton = o mutasyonun yakalandığı yer."""
    from . import ledgers as lg
    from . import watchdog as wd

    red: set[str] = set()
    # persist=True: mutasyon koşumu TABANI da ilerletmeli — dedektörler "önceki vs şimdiki"
    # kıyaslar ve taban yazılmazsa mutasyondan önce/sonra aynı boş tabanla karşılaştırılır.
    # Canlıda bu yolun sahibi günlük döngüdür; burada geçici kopya üzerinde çalışılıyor.
    rep = wd.integrity_report(persist=True)
    for s in rep["production"]["starved"]:
        red.add(f"production:{s['name']}")
    if rep["conservation"].get("unexplained"):
        red.add("conservation:unexplained")
    if not rep["determinism"].get("ok"):
        red.add("determinism:silent_bar_mutation")
    for st in rep["coherence"].get("stale", []):
        red.add(f"coherence:{st['artifact']}")
    for rg in rep["monotonicity"].get("regressions", []):
        red.add(f"monotonicity:{rg['field']}")
    for lo in rep["ownership"].get("lost", []):
        red.add(f"ownership:{lo['file']}.{lo['field']}")
    for pr in rep["parity"].get("rows", []):
        if not pr.get("ok"):
            red.add(f"parity:{pr['check']}")

    lrep = lg.report()
    for name in lrep.get("violating", []):
        red.add(f"ledger:{name}")
    for name in lrep.get("writer_violations", {}):
        red.add(f"ledger_writers:{name}")

    # SİEVE: başka bir iz tarafından yazılıyor olabilir. Yoksa koşum durmaz — ama SESSİZ de kalmaz;
    # "ölçülmedi" ile "temiz" aynı şey değildir (bu denetimin tamamı bu ayrımdan doğdu).
    try:
        from . import sieve as _sieve
        srep = _sieve.report()
        if isinstance(srep, dict):
            for v in srep.get("violations", []):          # sieve'in kendi biçimi
                red.add(f"sieve:{v.get('stage', '?')}:{v.get('rule', '?')}")
            for row in srep.get("rows", []):              # ileride satır biçimine dönerse
                if not row.get("ok", True):
                    red.add(f"sieve:{row.get('check', '?')}")
            if srep.get("ok") is False and not (srep.get("violations") or srep.get("rows")):
                red.add("sieve:not_ok")
    except ImportError as e:
        msg = f"sieve dedektörü YOK — bu koşumda ölçülmedi ({type(e).__name__}: {e})"
        LOG.info(msg)
        if log is not None and msg not in log:
            log.append(msg)
    except Exception as e:                      # dedektörün KENDİ arızası sessiz kalmasın
        msg = f"sieve dedektörü hata verdi: {type(e).__name__}: {e}"
        LOG.warning(msg)
        if log is not None and msg not in log:
            log.append(msg)
    return red


# =============================================================================================
# MUTASYON KATALOĞU — her biri TEK bir şeyi bozar
# =============================================================================================
@dataclass(frozen=True)
class Mutation:
    name: str
    note: str                      # Türkçe: bu hangi gerçek olayın sınıfı?
    apply: Callable[[Path], None]


def _m_plan_id_legacy(state: Path) -> None:
    rows = rjsonl(state, "trade_plans.jsonl")
    for i, r in enumerate(rows):
        r["id"] = f"P{i:05d}"
    _wjsonl(state, "trade_plans.jsonl", rows)


def _m_trade_plan_id_legacy(state: Path) -> None:
    rows = rjsonl(state, "trades.jsonl")
    for i, r in enumerate(rows):
        r["plan_id"] = f"P{i:05d}"
    _wjsonl(state, "trades.jsonl", rows)


def _m_cf_id_legacy(state: Path) -> None:
    rows = rjsonl(state, "counterfactuals.jsonl")
    for i, r in enumerate(rows):
        r["id"] = f"CF{i:04d}"
    _wjsonl(state, "counterfactuals.jsonl", rows)


def _m_drop_setup_from_trades(state: Path) -> None:
    rows = rjsonl(state, "trades.jsonl")
    for r in rows:
        r.pop("setup", None)
    _wjsonl(state, "trades.jsonl", rows)


def _m_drop_status_from_cf(state: Path) -> None:
    rows = rjsonl(state, "counterfactuals.jsonl")
    for r in rows:
        r.pop("status", None)
    _wjsonl(state, "counterfactuals.jsonl", rows)


def _m_rename_to_legacy_alias(state: Path) -> None:
    rows = rjsonl(state, "counterfactuals.jsonl")
    for r in rows:
        r["rr_expected"] = r.pop("r_multiple_expected", None)
    _wjsonl(state, "counterfactuals.jsonl", rows)


def _m_regime_is_question_mark(state: Path) -> None:
    rows = rjsonl(state, "counterfactuals.jsonl")
    for r in rows:
        r["regime"] = "?"
    _wjsonl(state, "counterfactuals.jsonl", rows)


def _m_truncate_trades(state: Path) -> None:
    rows = rjsonl(state, "trades.jsonl")
    _wjsonl(state, "trades.jsonl", rows[: max(1, len(rows) // 2)])


def _m_truncate_events(state: Path) -> None:
    rows = rjsonl(state, "events.jsonl")
    _wjsonl(state, "events.jsonl", rows[: max(1, len(rows) // 3)])


def _m_stale_derived(state: Path) -> None:
    """Kaynak ilerledi, türev yerinde saydı — gölge modelin 7115 yeni satıra rağmen eski veriyle
    durduğu canlı olayın sınıfı."""
    future = dt.datetime.now().timestamp() + 3 * 3600
    os.utime(state / "counterfactuals.jsonl", (future, future))


def _m_zero_out_calibration(state: Path) -> None:
    _wjson(state, "score_calibration.json", {"n": 0, "n_real": 0, "n_cf": 0, "buckets": {}})


def _m_duplicate_trade_rows(state: Path) -> None:
    """Canlıda yaşandı: döngü ortasında istisna → her 300 sn'lik yeniden deneme aynı satırı
    yeniden yazıyordu (audit #11)."""
    rows = rjsonl(state, "trades.jsonl")
    _wjsonl(state, "trades.jsonl", rows + rows[:5])


def _m_size_out_of_bounds(state: Path) -> None:
    rows = rjsonl(state, "trade_plans.jsonl")
    for r in rows[:5]:
        r["size_r"] = 99.0                     # bounds.yaml tavanının çok üstünde
    _wjsonl(state, "trade_plans.jsonl", rows)


def _m_unread_writer_output(state: Path) -> None:
    """Kimsenin okumadığı bir defter üretmek: mekanizma 'koşuyor', çıktı hiçbir karara değmiyor."""
    _wjsonl(state, "phantom_metrics.jsonl",
            [{"ts": f"2026-06-{i:02d}T10:00:00+00:00", "metric": "edge_proxy", "value": i}
             for i in range(1, 12)])


def _m_heartbeat_field_clobbered(state: Path) -> None:
    hb = rjson(state, "heartbeat.json", {})
    hb.pop("regime", None)
    _wjson(state, "heartbeat.json", hb)


def _m_book_date_regression(state: Path) -> None:
    pf = rjson(state, "portfolio.json", {})
    pf["last_date"] = "2026-05-01"
    _wjson(state, "portfolio.json", pf)


def _m_bars_file_shrinks(state: Path) -> None:
    p = sorted((state / "bars").glob("*.csv"))[0]
    lines = p.read_text().splitlines()
    p.write_text("\n".join(lines[: len(lines) // 2]) + "\n")


def _m_hypothesis_id_reused(state: Path) -> None:
    """Sözleşme diyor ki: kimlik ASLA yeniden kullanılmaz (max+1). Yeniden kullanım, öğrenme
    geçmişini sessizce üzerine yazar."""
    rows = rjsonl(state, "hypotheses.jsonl")
    for r in rows[-3:]:
        r["id"] = rows[0]["id"]
    _wjsonl(state, "hypotheses.jsonl", rows)


def _m_candidates_emptied(state: Path) -> None:
    _wjsonl(state, "candidates.jsonl", [])


def _m_silent_plan_loss(state: Path) -> None:
    """Silahlanmış ama hiçbir terminal duruma ulaşmamış planlar: P4 buharlaşmasının ta kendisi."""
    rows = rjsonl(state, "trade_plans.jsonl")
    extra = []
    for i in range(4):
        r = dict(rows[i])
        r["id"] = f"P-2026-06-1{i}-GHOST{i}"
        r["ticker"] = f"GHOST{i}"
        r["gate_verdict"] = "GO"
        extra.append(r)
    _wjsonl(state, "trade_plans.jsonl", rows + extra)


def _m_consumer_drops_every_row(state: Path) -> None:
    """"gerçek 0 / simüle 241"in ta kendisi: bir tüketici aşaması satırların HEPSİNİ şema
    nedeniyle eler ve dışarıdan bakan bunu 'veri yok' sanır."""
    d = rjson(state, "sieve.json", {}) or {}
    d["score_calibration.gercek"] = {"in": 24, "out": 0,
                                     "drops": {"sema:eksik_alan:setup": 24},
                                     "ts": f"{BOOK_DATE}T22:00:00+00:00"}
    _wjson(state, "sieve.json", d)


def _m_realized_pnl_drift(state: Path) -> None:
    """Broker muhasebesi ile defter toplamı ayrışır: işlem kaybolmuş ya da çift sayılmıştır."""
    pf = rjson(state, "portfolio.json", {})
    pf["realized_pnl"] = float(pf.get("realized_pnl") or 0.0) + 4_200.0
    _wjson(state, "portfolio.json", pf)


def _m_negative_edge_everywhere(state: Path) -> None:
    _wjson(state, "regime_edge.json", {"chop": {"n": 40, "avg_r": -0.5},
                                       "trend_up": {"n": 25, "avg_r": -0.8}})


MUTATIONS: list[Mutation] = [
    Mutation("plan_id_legacy_scheme",
             "plan defterinin anahtarı eski `P00140` şemasına döner — 2026-07-21'de cf_fidelity'yi "
             "sonsuza kadar None yapan hata", _m_plan_id_legacy),
    Mutation("trade_plan_id_legacy_scheme",
             "işlem satırındaki birleştirme anahtarı bozulur: sim↔gerçek kıyası kurulamaz",
             _m_trade_plan_id_legacy),
    Mutation("cf_id_legacy_scheme",
             "karşı-olgusal kimliği sözleşmedeki biçimden çıkar", _m_cf_id_legacy),
    Mutation("drop_required_field_setup",
             "işlem satırından `setup` alanı silinir — 'gerçek 0 / simüle 241' olayının kökü",
             _m_drop_setup_from_trades),
    Mutation("drop_required_field_status",
             "karşı-olgusal satırdan `status` alanı silinir", _m_drop_status_from_cf),
    Mutation("rename_field_to_legacy_alias",
             "`r_multiple_expected` → `rr_expected` yeniden adlandırması (yaması olmayan tüketici "
             "satırı sessizce eler)", _m_rename_to_legacy_alias),
    Mutation("regime_overwritten_with_question_mark",
             "rejim etiketi '?' olur — rejim bazlı her dilimleme boşa düşer",
             _m_regime_is_question_mark),
    Mutation("truncate_trades_ledger",
             "işlem defterinin yarısı kaybolur (kötü restore / yarım yazım)", _m_truncate_trades),
    Mutation("truncate_events_ledger",
             "olay defterinin üçte ikisi kaybolur — teşhis geçmişi silinir", _m_truncate_events),
    Mutation("stale_derived_artifact",
             "kaynak ilerler, türev yerinde sayar (gölge modelin bayat kalması sınıfı)",
             _m_stale_derived),
    Mutation("zero_out_calibration_artifact",
             "kalibrasyon artefaktı sıfırlanır — mekanizma 'koşuyor' ama üretmiyor",
             _m_zero_out_calibration),
    Mutation("duplicate_rows_in_trades",
             "aynı işlem satırı yeniden yazılır (300 sn'lik yeniden deneme kopyalaması)",
             _m_duplicate_trade_rows),
    Mutation("value_shifted_out_of_bounds",
             "plan boyutu bounds tavanının çok üstüne çıkar", _m_size_out_of_bounds),
    Mutation("writer_produces_rows_nobody_reads",
             "hiçbir tüketicisi olmayan bir defter üretilir — 'üretilip tüketilmeyen kanıt' sınıfı",
             _m_unread_writer_output),
    Mutation("owned_field_clobbered",
             "nabızdaki `regime` alanı bir yazıcı tarafından ezilir (HUD 'rejim yok' gösterdi)",
             _m_heartbeat_field_clobbered),
    Mutation("book_date_regression",
             "defterin tarihi GERİ gider — GS-1140'ı öldüren geriye-seans hatası",
             _m_book_date_regression),
    Mutation("bars_file_shrinks_without_rev_bump",
             "bar dosyası küçülür ama wf-revizyonu sabit kalır: önbelleklenmiş walk-forward'lar "
             "artık var olmayan barlara ait", _m_bars_file_shrinks),
    Mutation("hypothesis_id_reused",
             "hipotez kimliği yeniden kullanılır — öğrenme geçmişi sessizce üzerine yazılır",
             _m_hypothesis_id_reused),
    Mutation("candidates_ledger_emptied",
             "aday defteri boşalır — huninin girişi görünmez olur", _m_candidates_emptied),
    Mutation("silent_plan_loss",
             "silahlı planlar hiçbir terminal duruma ulaşmadan kaybolur (P4 buharlaşması)",
             _m_silent_plan_loss),
    Mutation("consumer_silently_drops_every_row",
             "bir tüketim aşaması giren satırların HEPSİNİ şema nedeniyle eler — 'veri yok' ile "
             "'veri elendi' karışır ('gerçek 0 / simüle 241')", _m_consumer_drops_every_row),
    Mutation("realized_pnl_drifts_from_the_ledger",
             "broker muhasebesi ile işlem defterinin toplamı ayrışır: işlem kaybolmuş ya da çift "
             "sayılmış", _m_realized_pnl_drift),
    Mutation("measured_edge_turns_negative",
             "ölçülen edge her rejimde negatife döner — bir SONUÇ, ama alarm mı?",
             _m_negative_edge_everywhere),
]


# =============================================================================================
# KOŞUM
# =============================================================================================
def dir_digest(state: Path) -> dict:
    """Dizinin içerik parmak izi — bir mutasyonun GERÇEKTEN bir şey değiştirdiğini kanıtlar.
    Hiçbir şeyi değiştirmeyen bir mutasyon, kapsama sayısını sessizce şişirirdi."""
    import hashlib
    out = {}
    for p in sorted(state.rglob("*")):
        if p.is_file():
            st = p.stat()
            out[str(p.relative_to(state))] = (
                hashlib.sha256(p.read_bytes()).hexdigest()[:16], round(st.st_mtime, 3))
    return out


def run(workdir: Path | None = None, keep: bool = False, strict: bool = True) -> dict:
    """Bataryayı temel durumda ve her mutasyonda koştur; körlük haritasını döndür."""
    log: list[str] = []
    tmp_root = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="meridian-mutation-"))
    _assert_not_live(tmp_root)
    base_dir = tmp_root / "baseline"
    result: dict = {"workdir": str(tmp_root), "log": log}
    try:
        with quiet_externals():
            build_state(base_dir)
            with using_state(base_dir):
                detector_red(log)                    # 1. geçiş: durumlu dedektörler görüntü yazar
                baseline = detector_red(log)         # 2. geçiş: GERÇEK temel durum
            result["baseline_red"] = sorted(baseline)
            result["baseline_clean"] = not baseline
            if baseline and strict:
                raise RuntimeError(
                    "TEMEL DURUM KİRLİ — ölçüm yapılamaz: kirli bir temelde her mutasyon "
                    f"'yakalandı' görünür ve kapsama sayısı yalan söyler. Kırmızı: {sorted(baseline)}")
            base_digest = dir_digest(base_dir)

            caught, missed, rows = {}, [], []
            for mut in MUTATIONS:
                work = tmp_root / f"mut_{mut.name}"
                if work.exists():
                    shutil.rmtree(work)
                shutil.copytree(base_dir, work)
                mut.apply(work)
                changed = dir_digest(work) != base_digest
                with using_state(work):
                    after = detector_red(log)
                new = sorted(after - baseline)
                row = {"mutation": mut.name, "note": mut.note, "changed_state": changed,
                       "caught": bool(new), "detectors": new}
                rows.append(row)
                if new:
                    caught[mut.name] = new
                else:
                    missed.append(mut.name)
                if not changed:
                    log.append(f"UYARI: '{mut.name}' durumu hiç değiştirmedi — ölçüm anlamsız")
            n = len(MUTATIONS)
            result.update({
                "n_mutations": n, "n_caught": len(caught), "n_missed": len(missed),
                "coverage_pct": round(100.0 * len(caught) / n, 1) if n else 0.0,
                "caught": caught, "missed": missed, "rows": rows,
                "blind_spots": [{"mutation": m, "note": next(x.note for x in MUTATIONS if x.name == m)}
                                for m in missed],
                "sieve_present": not any("sieve dedektörü YOK" in m for m in log),
                "out_of_scope": ["sp500_membership (ağ)", "fmp_source (ağ)"],
            })
        return result
    finally:
        if not keep and not workdir:
            shutil.rmtree(tmp_root, ignore_errors=True)


def format_report(res: dict) -> str:
    """İnsan okuyacak: sayı değil, KÖRLÜK LİSTESİ önemli."""
    L = ["MUTASYON KOŞUMU — dedektör körlük haritası", "=" * 62]
    L.append(f"temel durum: {'TEMİZ' if res.get('baseline_clean') else 'KİRLİ ' + str(res.get('baseline_red'))}")
    L.append(f"mutasyon: {res['n_mutations']}  ·  yakalanan: {res['n_caught']}  ·  "
             f"KAÇAN: {res['n_missed']}  ·  kapsama: %{res['coverage_pct']}")
    L.append(f"sieve dedektörü: {'var' if res.get('sieve_present') else 'YOK (ölçülmedi)'}")
    L.append(f"kapsam dışı (ağ): {', '.join(res.get('out_of_scope', []))}")
    L.append("")
    L.append("YAKALANANLAR")
    for r in res["rows"]:
        if r["caught"]:
            L.append(f"  ✓ {r['mutation']:38s} → {', '.join(r['detectors'])}")
    L.append("")
    L.append("KAÇANLAR — bugün GÖREMEDİĞİMİZ hata sınıfları (asıl çıktı budur)")
    for b in res["blind_spots"]:
        L.append(f"  ✗ {b['mutation']}")
        L.append(f"      {b['note']}")
    if not res["blind_spots"]:
        L.append("  (yok — bu SÜPHELİ bir sonuçtur: mutasyonlar yeterince keskin mi?)")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Mutasyon koşumu: dedektörlerin körlüğünü ölçer.")
    ap.add_argument("--json", action="store_true", help="raporu JSON olarak yaz")
    ap.add_argument("--keep", action="store_true", help="geçici dizini silme (inceleme için)")
    ap.add_argument("--workdir", default=None, help="çalışma dizini (canlı state/ OLAMAZ)")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        res = run(workdir=Path(a.workdir) if a.workdir else None, keep=a.keep)
    except RuntimeError as e:
        print(f"KOŞUM DURDU: {e}", file=sys.stderr)
        return 2
    print(json.dumps(res, indent=2, ensure_ascii=False) if a.json else format_report(res))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

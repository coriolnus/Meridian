"""test_loop_gaps_v48.py — loop'un AÇIK BOŞLUKLARI (2026-07-21, boşluk kapatma turu 2).

daily_cycle motorun kalbi: rejim → tarama → plan → kapı → silahlanma → dolum → uzlaştırma → öğrenme.
İlk tam turda 2/6 doluydu (korunum + monotonluk). Kalan dördü:

  uretkenlik — bir döngü GERÇEKTEN artefakt üretir: regime.json, data_quality.json, portfolio,
               aday/plan defterleri. "Koştu ama hiçbir şey yazmadı" bir hatadır.
  determinizm — AYNI barlar + AYNI tarih iki kez koşarsa aynı sonucu verir; işlem defteri
               ÇOĞALMAZ (canlıda yaşandı: mid-cycle istisna her 300 sn'de satır kopyalıyordu)
  tutarlilik  — regime.json döngünün İŞLEDİĞİ günün tarihini taşır (bayat rejimle karar verilmez)
  sahiplik    — döngü goal/bounds/secrets'a ASLA yazmaz; yalnız kendi durum dosyalarına
"""
from __future__ import annotations

import ast
import inspect
import pathlib
import shutil
from pathlib import Path

import pytest
import yaml

from meridian import config, ledgerstamp, loop, store
from tests.conftest import make_bars


@pytest.fixture
def seeded(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    (sandbox_state / "strategy.yaml").write_text(yaml.safe_dump(config.default_strategy()))
    yield sandbox_state
    config.reload_config()


def _universe():
    idx = make_bars(300, seed=1, trend=0.0009)
    bars = {"AAA": make_bars(300, seed=2, breakout_at=200),
            "BBB": make_bars(300, seed=3, breakout_at=150),
            "CCC": make_bars(300, seed=4, trend=0.001)}
    return bars, idx


def _last_date(idx):
    return str(idx["date"].iloc[-1].date())


# ---------- ÜRETKENLİK: bir döngü artefakt üretir ----------
def test_a_cycle_produces_its_artifacts(seeded):
    bars, idx = _universe()
    d = _last_date(idx)
    summary = loop.daily_cycle(bars, idx, on_date=d)
    assert isinstance(summary, dict) and summary.get("date") == d
    rj = store.read_json("regime.json", {})
    assert rj.get("regime") and rj.get("date") == d, "rejim artefaktı üretilmedi"
    assert store.read_json("data_quality.json", {}).get("date") == d
    assert store.read_json(loop.PORTFOLIO, {}).get("last_date") == d
    assert (config.STATE / "heartbeat.json").exists(), "nabız yazılmadı — canlılık görünmez"


def test_cycle_records_candidates_or_says_why_not(seeded):
    """Aday üretilmediyse bu da bir SONUÇTUR: özet sayıları taşımalı (sessiz boşluk değil)."""
    bars, idx = _universe()
    s = loop.daily_cycle(bars, idx, on_date=_last_date(idx))
    for k in ("candidates", "plans", "armed", "open_positions"):
        assert k in s, f"özet '{k}' alanını taşımıyor"
        assert isinstance(s[k], int)
    for k in ("regime", "equity", "halted", "data_ok"):
        assert k in s, f"özet '{k}' alanını taşımıyor"


# ---------- DETERMİNİZM: aynı gün iki kez → aynı sonuç, çoğalma yok ----------
def test_same_day_twice_is_idempotent(seeded):
    """Canlıda yaşandı: mid-cycle istisna sonrası her 300 sn'lik yeniden deneme trades.jsonl'a
    KOPYA satır yazıyordu (audit #11). Aynı günü iki kez işlemek defteri şişirmemeli."""
    bars, idx = _universe()
    d = _last_date(idx)
    s1 = loop.daily_cycle(bars, idx, on_date=d)
    n1 = len(store.read_jsonl("trades.jsonl"))
    plans1 = len(store.read_jsonl("trade_plans.jsonl"))
    s2 = loop.daily_cycle(bars, idx, on_date=d)
    n2 = len(store.read_jsonl("trades.jsonl"))
    plans2 = len(store.read_jsonl("trade_plans.jsonl"))
    assert n2 == n1, f"işlem defteri çoğaldı: {n1} → {n2}"
    assert plans2 == plans1, f"plan defteri çoğaldı: {plans1} → {plans2}"
    assert s2.get("date") == s1.get("date")


def test_regressive_session_is_refused(seeded):
    """Kitap ileri gider: DÜNÜN seansı yeniden işlenemez (GS-1140'ın kökü)."""
    bars, idx = _universe()
    d_last = _last_date(idx)
    d_prev = str(idx["date"].iloc[-6].date())
    loop.daily_cycle(bars, idx, on_date=d_last)
    out = loop.daily_cycle(bars, idx, on_date=d_prev)
    assert out.get("status") == "refused_regressive", f"geriye seans işlendi: {out}"
    assert store.read_json(loop.PORTFOLIO, {}).get("last_date") == d_last


# ---------- TUTARLILIK: rejim işlenen günün rejimidir ----------
def test_regime_artifact_matches_the_processed_session(seeded):
    bars, idx = _universe()
    d = str(idx["date"].iloc[-4].date())
    loop.daily_cycle(bars, idx, on_date=d)
    rj = store.read_json("regime.json", {})
    assert rj["date"] == d, "rejim BAŞKA bir günün — kararlar bayat rejimle verilir"
    assert rj["regime"] in config.VALID_REGIMES
    assert rj["exposure_budget_pct"] >= 0


def test_leading_sectors_are_populated_live(seeded):
    bars, idx = _universe()
    loop.daily_cycle(bars, idx, on_date=_last_date(idx))
    rj = store.read_json("regime.json", {})
    assert isinstance(rj.get("leading_sectors"), list)      # backtest ile aynı alan (turu 23)


# ---------- SAHİPLİK: döngü neyi YAZAR, neyi ASLA yazmaz ----------
def test_cycle_never_writes_immutable_config(seeded):
    bars, idx = _universe()
    before = {f: (config.STATE / f).read_text() for f in ("goal.yaml", "bounds.yaml")}
    loop.daily_cycle(bars, idx, on_date=_last_date(idx))
    for f, txt in before.items():
        assert (config.STATE / f).read_text() == txt, f"döngü {f} dosyasına YAZDI (değişmez olmalı)"


def test_cycle_never_writes_secrets_or_strategy(seeded):
    bars, idx = _universe()
    strat_before = (config.STATE / "strategy.yaml").read_text()
    loop.daily_cycle(bars, idx, on_date=_last_date(idx))
    assert (config.STATE / "strategy.yaml").read_text() == strat_before, \
        "döngü stratejiyi değiştirdi — ship yetkisi YALNIZ reflect.submit'te"
    assert not (config.STATE / "secrets.json").exists()


def test_loop_writes_only_declared_state_files():
    """Statik sahiplik sınırı: döngünün yazdığı dosya adları BİLİNÇLİ bir liste olmalı; yenisi
    eklenirse burada tartışılır (sessizce bir dosyanın sahibi olunmaz)."""
    tree = ast.parse(pathlib.Path("meridian/loop.py").read_text())
    written = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr in ("write_json", "write_jsonl", "append_jsonl", "merge_dated_jsonl") \
                and n.args and isinstance(n.args[0], ast.Constant):
            written.add(n.args[0].value)
    allowed = {"universe_drift.json", "portfolio.json", "trade_plans.jsonl", "scan_debt.json",
               "data_quality.json", "regime.json", "candidates.jsonl", "score_calibration.json",
               "trades.jsonl", "broker_reconcile.json", "counterfactuals.jsonl", "near_miss.json",
               # WP2-D bacak-2 (2026-08-14): eğrinin KADANSLI yazarı. Sahiplik ORTAK ve beyanlı
               # (test_na_revision_v53::test_no_module_writes_another_modules_file): run.py tohumu,
               # sermaye.py zarftaki reset işaretini, loop.py seans noktasını yazar. Yazım
               # `store.update_json` (file_lock + oku-değiştir-yaz) ile ve YALNIZ `points`e EKLER —
               # zarfın öteki anahtarları (bacak-1'in sınırı orada) korunur.
               ledgerstamp.EQUITY}
    assert loop.EQUITY_CURVE == ledgerstamp.EQUITY, "ikiz literal ayrıştı"
    extra = written - allowed
    assert not extra, f"döngü beyan edilmemiş dosyalara yazıyor: {extra}"
    assert "goal.yaml" not in written and "bounds.yaml" not in written


# ---------- İKİNCİ TUR (2026-07-21): üretilen satır, tüketicinin sorusuna yetiyor mu? ----------
def test_plan_ledger_has_one_schema_across_both_producers():
    """BULGU: plan defterini İKİ üretici yazıyor — canlı döngü (gate_checks ile) ve replay tohumu
    (gate_checks OLMADAN). Defter replay ile tohumlandığı için panonun karar-ağacı tablosu canlıda
    144 satırın 144'ünde BOŞTU: "neden GO verdi?" (geçen kontroller dahil) kayıttan cevaplanamıyordu.
    Aynı yasanın iki uygulaması deseninin ŞEMA hâli — mantık değil, VERİ ayrışması."""
    from meridian import backtest
    from tests.conftest import make_bars
    # ISINMA PENCERESİ (2026-07-22): trend_template artık 220 bar dolmadan NaN döndürüyor —
    # eskiden yetersiz geçmişte sessizce "zayıf trend" puanı üretiyordu (NaN karşılaştırması False
    # verdiği için "200g ortalama yok" ile "koşul sağlanmadı" aynı skoru alıyordu). Doğru davranış
    # bu; fikstür de gerçek dünyanın şartını taşımalı: kırılımlar ısınma DOLDUKTAN sonra olmalı.
    idx = make_bars(700, seed=1, trend=0.0015)
    bars = {"AAA": make_bars(700, seed=2, breakout_at=560),
            "BBB": make_bars(700, seed=3, breakout_at=510)}
    end = str(idx["date"].iloc[-1].date())
    res = backtest.replay(config.default_strategy()["params"], bars, idx, config.goal(),
                          "2022-06-01", end, strategy_version=1, with_gate_detail=True)
    assert res.plan_log, "plan üretilmedi — test bir şey kanıtlamıyor"
    for p in res.plan_log:
        assert p.get("gate_checks"), "replay planı karar ağacı taşımıyor"
        for c in p["gate_checks"]:
            assert {"check", "passed", "severity"} <= set(c)
    # GEÇEN kontroller de kayıtta: "neden GO verdi" sorusu yalnız vetolarla cevaplanamaz
    assert any(c["passed"] for p in res.plan_log for c in p["gate_checks"])


def test_gate_detail_is_off_by_default_for_the_search_path():
    """Arama yolunda binlerce replay koşuyor; her plana 8 sözlük eklemek belleği şişirir.
    Detay yalnız İSTENDİĞİNDE üretilir — tohumlama açar, kapı ölçümü kapalı bırakır."""
    from meridian import backtest
    from tests.conftest import make_bars
    idx = make_bars(300, seed=1, trend=0.0009)
    bars = {"AAA": make_bars(300, seed=2, breakout_at=200)}
    res = backtest.replay(config.default_strategy()["params"], bars, idx, config.goal(),
                          "2022-06-01", "2023-06-01", strategy_version=1)
    assert all("gate_checks" not in p for p in (res.plan_log or []))
    import inspect
    from meridian import run
    assert "with_gate_detail=True" in inspect.getsource(run.replay_seed)


def test_live_cycle_plans_carry_the_decision_tree(seeded):
    bars, idx = _universe()
    loop.daily_cycle(bars, idx, on_date=_last_date(idx))
    plans = store.read_jsonl("trade_plans.jsonl")
    for p in plans:
        assert "gate_verdict" in p
        if p.get("gate_checks"):
            names = {c["check"] for c in p["gate_checks"]}
            assert {"exposure_budget", "earnings_blackout"} <= names


# ---------- EVREN BÜTÜNLÜĞÜ (2026-07-21, canlı kanıtla bulundu) ----------
def _bars_with_lag(n_fresh: int, n_lagging: int):
    """Endeks son seansa sahip; sembollerin bir kısmı BİR GÜN geride (ücretsiz kaynak gerçeği)."""
    idx = make_bars(300, seed=1, trend=0.0009)
    bars = {}
    for i in range(n_fresh):
        bars[f"F{i}"] = make_bars(300, seed=10 + i, breakout_at=250)
    for i in range(n_lagging):
        bars[f"L{i}"] = make_bars(300, seed=50 + i, breakout_at=250).iloc[:-1]   # son bar YOK
    return bars, idx


def test_cycle_defers_to_the_session_the_universe_actually_has(seeded):
    """CANLI BULGU: SPY 07-21 barına sahipken 250 sembolün yalnız 46'sı sahipti. Tazelik koruması
    kalan 204'ü atlıyor → motor evrenin %18'ini tarayıp 'aday: 0' yazıyordu. Üstelik o %18 rastgele
    değil, hangi kaynağın önce güncellediğine bağlı: kapı 250'de ölçer, canlı taraf yanlı bir alt
    kümede karar verir. Motor artık evrenin ÇOĞUNLUĞUNUN barı olan seansı işler."""
    bars, idx = _bars_with_lag(n_fresh=2, n_lagging=18)          # %10 taze, %90 bir gün geride
    s = loop.daily_cycle(bars, idx)
    idx_last = str(idx["date"].iloc[-1].date())
    assert s["date"] != idx_last, "motor %10'luk yanlı kesitte karar verdi"
    assert s["date"] == str(idx["date"].iloc[-2].date())
    ev = [e for e in store.read_jsonl("events.jsonl")
          if e.get("event") == "session_deferred_for_coverage"]
    assert ev and ev[-1]["chosen"] == s["date"] and ev[-1]["coverage"] >= 0.9


def test_full_coverage_session_is_processed_as_is(seeded):
    bars, idx = _bars_with_lag(n_fresh=20, n_lagging=0)
    s = loop.daily_cycle(bars, idx)
    assert s["date"] == str(idx["date"].iloc[-1].date())         # gecikme yoksa erteleme de yok
    assert not [e for e in store.read_jsonl("events.jsonl")
                if e.get("event") == "session_deferred_for_coverage"]


def test_persistently_low_coverage_is_reported_not_hidden(seeded):
    """Hiçbir yakın seansta evren tamam değilse SESSİZ kalınmaz — veri arızası görünür olur."""
    idx = make_bars(300, seed=1, trend=0.0009)
    bars = {f"L{i}": make_bars(300, seed=60 + i).iloc[:-6] for i in range(10)}   # hepsi 6 gün geride
    loop.daily_cycle(bars, idx)
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "universe_coverage_low"]
    assert ev and ev[-1]["min_required"] == loop.UNIVERSE_MIN_COVERAGE


def test_waiting_for_universe_is_not_reported_as_a_regressive_fault(seeded):
    """Kapsama ertelemesi ile monotonluk bekçisi çarpışabilir: düzeltme ÖNCESİ kitap düşük
    kapsamalı bir seansta ilerletildiyse, tam kapsamalı seans kitabın gerisinde kalır. Bu bir
    BEKLEME'dir, 'bayat/yedek kaynak' arızası değil — teşhis ikisini karıştırmamalı."""
    bars, idx = _bars_with_lag(n_fresh=2, n_lagging=18)
    store.write_json(loop.PORTFOLIO, {"last_date": str(idx["date"].iloc[-1].date()),
                                      "cash": 100000.0, "positions": {}, "armed": []})
    out = loop.daily_cycle(bars, idx)
    assert out["status"] == "waiting_for_universe"
    assert out["date"] == str(idx["date"].iloc[-2].date()) and out["book_at"] == str(idx["date"].iloc[-1].date())
    evs = {e.get("event") for e in store.read_jsonl("events.jsonl")}
    assert "waiting_for_universe" in evs and "regressive_session_refused" not in evs


def test_a_genuinely_regressive_session_is_still_refused(seeded):
    """Bekleme yolu, GERÇEK geriye-sarmayı maskelememeli: kapsama tamsa bekçi eskisi gibi reddeder."""
    bars, idx = _bars_with_lag(n_fresh=20, n_lagging=0)
    store.write_json(loop.PORTFOLIO, {"last_date": "2099-01-01", "cash": 100000.0,
                                      "positions": {}, "armed": []})
    out = loop.daily_cycle(bars, idx)
    assert out["status"] == "refused_regressive"

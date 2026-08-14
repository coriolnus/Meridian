"""test_na_revision_v53.py — N/A beyanlarının YENİDEN SORGULANMASI (2026-07-21).

Operatör sordu: "109 N/A'yı yeniden sorgula." Sorgu, **7 OLGUSAL HATA** buldu: `obs`, `probgate`,
`scheduler`, `selfreview`, `shadow_model`, `spend`, `watchdog` için "hiçbir şey yazmaz" demiştim —
AST taraması hepsinin state YAZDIĞINI gösterdi. Yani sahiplik sorusu anlamsız değildi, ben yanlış
biliyordum. 21 hücre daha "soru anlamsız" değil "test etmesi zahmetli" olduğu için elenmişti.

Toplam 28 hücre N/A'dan ÇIKTI ve burada gerçek kontrollere bağlanıyor. Ders: eleme ölçütü
"sorulabilir mi" olmalı, "kolay mı" değil — aksi halde N/A, kapsamı şişiren bir kaçış olur.
"""
from __future__ import annotations

import ast
import datetime as dt
import inspect
import pathlib
import shutil
from pathlib import Path

import numpy as np
import pytest
import yaml

from meridian import config, store


@pytest.fixture
def seeded(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    yield sandbox_state
    config.reload_config()


def _writes(mod_path: str) -> set:
    """Modülün yazdığı state dosyaları. Sabit adları (PORTFOLIO = "portfolio.json") DA çözer:
    yoksa bir modül adı bir sabite taşıyarak sahiplik taramasından sessizce kaçabilir."""
    tree = ast.parse(pathlib.Path(mod_path).read_text())
    consts = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant) \
                and isinstance(n.value.value, str):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    consts[t.id] = n.value.value
    out = set()
    WRITERS = ("write_json", "write_jsonl", "append_jsonl", "merge_dated_jsonl",
               "update_json", "update_jsonl")
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr in WRITERS and n.args:
            a = n.args[0]
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                out.add(a.value)
            elif isinstance(a, ast.Name) and a.id in consts:
                out.add(consts[a.id])
    return out


# ============ SAHİPLİK — "yazmaz" dediklerim aslında YAZIYOR ============
def test_obs_owns_only_the_event_ledger_and_notify_state(sandbox_state):
    # notify_undelivered.json (2026-07-22): kanal yapılandırılmamışken alarm hiçbir yere gitmiyordu
    # ve bu SESSİZDİ (canlıda 23 MECHANISM_STALE yazıldı, 0'ı teslim edildi). Teslim edilemeyen
    # alarm artık sayılıyor; sahiplik obs'ta, çünkü kararı veren `_maybe_notify`.
    # alarm_mandal.json (2026-08-12, gelen-kutusu hijyeni): tekrar-mandalı imza defteri — kararı
    # veren obs'un kendi mandal hunisi, okuyucusu watchdog.parity_report. Kardeş çivilerin deseni
    # gibi modül SABİTİNDEN okunur (elle literal değil — test_scheduler_owns_only_its_own_state
    # docstring'indeki gerekçe: sabit değişirse test kendiliğinden izler, ikiz-literal bayatlamaz).
    from meridian.obs import MANDAL_FILE
    assert _writes("meridian/obs.py") <= {"events.jsonl", "notify_sent.json",
                                          "notify_undelivered.json", MANDAL_FILE}


def test_probgate_owns_only_its_calibration_file(sandbox_state):
    from meridian.probgate import META_FILE
    assert _writes("meridian/probgate.py") <= {META_FILE}


def test_scheduler_owns_only_its_own_state(sandbox_state):
    """Zamanlayıcı YALNIZ kendi state'ini yazar — iddia bu, ve iddia değişmedi.

    ÇİVİ 2026-07-30'da BAYATLADI (iki yeni artefakt, ikisi de o günden): `learning_cadence.json`
    (öğrenme kadansının seans başına bir kez yazdığı koşu kaydı) ve `validation_report.json`
    (haftalık kanıt raporu). İkisi de MEŞRU sahipliktir — AST taraması ikisinin de TEK yazarının
    `scheduler.py` olduğunu gösteriyor (`test_no_module_writes_another_modules_file` aynı taramayı
    bütün depo için yapıyor ve yeşil). Yani bulunan şey bir sahiplik ihlali değil, elle yazılmış
    bir listenin geride kalmasıydı.

    ADLAR ARTIK MODÜLDEN OKUNUR, ELLE KOPYALANMAZ — kardeş çivilerin (`probgate.META_FILE`,
    `shadow_model.STATE_FILE`, `wd.BEATS_FILE`) deseni. Elle kopyalanmış bir ad, dosya adı
    değiştiği gün çiviyi sessizce YANLIŞ yapar: liste eski adı "izinli" saymaya devam eder ve
    yeni ad ihlal gibi görünür. Sabiti olmayan tek ad `index_crosscheck.json` (kaynakta da çıplak
    literal) — o yüzden burada da literal."""
    from meridian import scheduler as sch
    assert _writes("meridian/scheduler.py") <= {sch.STATUS_FILE, sch.LEARN_FILE,
                                                sch.VALIDATION_FILE, "index_crosscheck.json"}


def test_selfreview_owns_only_its_report(sandbox_state):
    from meridian.selfreview import REVIEW_FILE
    assert _writes("meridian/selfreview.py") <= {REVIEW_FILE}


def test_shadow_model_owns_only_its_model_file(sandbox_state):
    from meridian.shadow_model import STATE_FILE
    assert _writes("meridian/shadow_model.py") <= {STATE_FILE}


def test_spend_owns_only_its_ledger(sandbox_state):
    assert _writes("meridian/spend.py") <= {"spend.jsonl"}


def test_watchdog_owns_only_its_beat_and_alarm_files(sandbox_state):
    from meridian import watchdog as wd
    assert _writes("meridian/watchdog.py") <= {wd.BEATS_FILE, wd.ALARMED_FILE,
                                               # v192 alarm hijyeni: mekanizma-başına GÜNLÜK alarm
                                               # sayacı (tavan + bastırma + askıda). Mandalın (ALARMED)
                                               # yanına AYRI dosya: mandal "şu an bayat olan" kümesidir
                                               # ve her koşuda tamamen yeniden yazılır; gün sayacı ise
                                               # birikimlidir — tek dosyada birleştirmek sayacı her
                                               # toparlanmada sıfırlardı (çırpınma tam oradan geliyordu)
                                               wd.ALARM_GUNLUK_FILE,
                                               "integrity_alarmed.json", "monotonic_state.json",
                                               "bars_fingerprint.json", "ownership_state.json",
                                               # meşru küçülmenin yazılı affı (2026-07-22): re-seed
                                               # gibi KASITLI yeniden kurulumları sessiz kayıptan
                                               # ayırır; gerekçesiz af geçersizdir
                                               wd.AMNESTY_FILE,
                                               # SB-4 damgasız-yazım bekçisinin ÖNCEKİ ÖLÇÜMÜ
                                               # (2026-08-09): izlenen belgenin (rev/updated_at)
                                               # damgası + içerik sha256'sı. `ownership_state.json`
                                               # ve `monotonic_state.json` ile BİREBİR aynı sınıf —
                                               # bir dedektörün "önceki durum" tabanı; sahibi de
                                               # okuyucusu da watchdog'dur ve kalıcı olmak ZORUNDA
                                               # (kıyas iki poll ARASINDADIR; bellek-içi bir taban
                                               # süreç yeniden başlayınca 2026-08-04 sınıfı bir
                                               # yazımı sessizce yutardı).
                                               # ÇAPRAZ REFERANS: aynı gerekçe `codelaw.
                                               # DECLARED_SINKS["entity_damga.json"]`te yazılı —
                                               # YASA 6 tarafı orada, SAHİPLİK tarafı burada
                                               # kapanır; iki kapı aynı artefaktın iki ayrı
                                               # sorusunu sorar ("kim okuyor" ve "kim yazıyor").
                                               wd.DAMGA_FILE}


def test_no_module_writes_another_modules_file():
    """Sahiplik çakışması taraması: aynı dosyayı İKİ modül yazıyorsa 'sahibi kim' sorusu cevapsızdır
    ve kayıp-güncelleme kapıdadır (memory #19, skills turu 30 aynı hataydı)."""
    owners: dict[str, set] = {}
    for f in pathlib.Path("meridian").rglob("*.py"):
        for name in _writes(str(f)):
            owners.setdefault(name, set()).add(f.name)
    shared = {k: v for k, v in owners.items() if len(v) > 1}
    # BİLİNEN ve kabul edilmiş ortak yazımlar (her biri gerekçeli)
    # BEYAN EDİLMİŞ ortak yazımlar — her biri gerekçeli. YENİ BULGU (2026-07-21): hermes.py,
    # LLM görüş damgasını trade_plans.jsonl / cf_open.json / portfolio.json'a AYRI BİR İŞ
    # PARÇACIĞINDAN yazıyordu; portfolio.json canlı defter olduğu için bu kilitsiz hâlde
    # kayıp-güncelleme demekti. Artık üçü de store.update_json/update_jsonl (dosya kilidi) ile.
    allowed = {
        "trade_plans.jsonl": {"loop.py", "run.py", "hermes.py"},
        # ledgerstamp.py (BT-1, 2026-07-31): TEK SEFERLİK kaynak-damgası migrasyonu. Ortak yazım
        # burada KAYIP-GÜNCELLEME riski taşımıyor çünkü üçüncü yazar bir DAEMON değil, elle
        # koşulan bir CLI: kuru koşu varsayılan, `--uygula` canlı süreç görürse REDDEDİLİYOR
        # (barrepair'in aynı kilidi, aynı fonksiyon) ve yazım tek atomik write_jsonl.
        # Satır EKLEMEZ/SİLMEZ — yalnız `kaynak` alanını basar. `ledgers.CONTRACTS`te de beyanlı.
        "trades.jsonl": {"loop.py", "run.py", "ledgerstamp.py"},
        # run.py: yalnız RE-SEED yolunda kitabı tohumlanan deftere hizalar (2026-07-22).
        # Hizalamasaydı pano nakdi ile sermaye eğrisi birbirini tutmuyordu ve hiçbir istisna
        # fırlamıyordu — `yeniden_hesap` dedektörü yakaladı.
        # sermaye.py (tohum-ayrıştırması, 2026-08-01): TEK SEFERLİK sermaye tabanı migrasyonu —
        # `ledgerstamp.py`nin trades.jsonl'daki rolünün AYNISI ve aynı gerekçelerle güvenli:
        # yazar bir DAEMON değil elle koşulan CLI'dir (kuru koşu varsayılan, `--uygula` canlı süreç
        # görürse REDDEDİLİR — barrepair'in aynı fonksiyonu), yazım `store.file_lock(PORTFOLIO)`
        # altında oku-değiştir-yaz'dır (loop._save_broker ve hermes damgasıyla AYNI kilit), ve
        # İDEMPOTENTTİR (ikinci koşu `zaten_ayrisik` der, tek bayt yazmaz). Dokunduğu alanlar
        # dört tanedir ve kitapta `sermaye_resetleri` kaydıyla BEYANLIDIR.
        # api.py (C8, 2026-08-02): pano "gönder" düğmesi artık döngüyle AYNI gönderim kapısından
        # (`loop.mirror_submit_armed`) geçiyor ve gönderimin SONUCUNU yazmak ZORUNDA — eskiden
        # yazmadığı için `alpaca_submitted` dedup kümesi düğme yolunda hiç oluşmuyordu ve döngü
        # aynı planı ikinci kez gönderip duplicate-coid reddi alınca planı silahlı kümeden
        # düşürüyordu (denetim C8, bulgu 3). Kayıp-güncelleme riski YOK: yazım `store.update_json`
        # ile `file_lock(PORTFOLIO)` altında oku-değiştir-yaz'dır (loop._save_broker ve hermes
        # damgasıyla AYNI kilit) ve TAM BELGE YAZMAZ — yalnız üç alanı YAMALAR: gönderilen
        # kimlikler `alpaca_submitted`a EKLENİR, düşen (veto/ret) planlar `armed`dan kimlikle
        # ÇIKARILIR, `broker_rejected` defteri güncellenir. Canlı worker'ın o an ürettiği yeni
        # armed satırları bu yüzden EZİLMEZ (tam belge yazımı bilerek reddedildi).
        # DARALMA (2026-08-12, icra-sözleşmesi v233): api.py listeden ÇIKTI — pano gönderim ucu artık
        # kitaba KENDİSİ yazmıyor, tek kapı `loop.mirror_submit_ve_kalicilastir`ı çağırıyor (C8 tek-kapı
        # çivisinin devamı; yazar sayısı 6→5, sahiplik sıkılaştı).
        "portfolio.json": {"loop.py", "sprint_run.py", "hermes.py", "run.py", "sermaye.py"},
        # ÜÇ YAZAR, ÜÇ AYRI KAPSAM (WP2-D, 2026-08-14):
        #   run.py     — tohum koşusu: `points`i TOPTAN yazar (defterle ardışık, tek toplu yazım).
        #   sermaye.py — `points`e DOKUNMAZ; zarftaki `reset_isaretleri` anahtarına kırılma beyanı
        #                yazar (o beyan artık tohum sınırının TEK kaynağıdır).
        #   loop.py    — seans sonu KADANSLI NOKTASI: `store.update_json` (file_lock + oku-değiştir-
        #                yaz) ile `points`e TEK nokta EKLER, zarfın öteki anahtarlarına dokunmaz ve
        #                günde bir noktadan fazlasını yazamaz (idempotens fonksiyonun içinde).
        # Kayıp-güncelleme riski YOK: üçü de aynı `file_lock(equity_curve.json)` sırasını paylaşır
        # ve run.py/sermaye.py yolları canlı worker koşarken zaten reddediliyor.
        # ESKİ GEREKÇE ARTIK GEÇERSİZ ve bu BİLEREK kayda geçiyor: "nokta eklemek seed_boundary'nin
        # tohum sınırını kaydırırdı" — kaydırmıyor, çünkü sınır bacak-1'den beri eğrinin son
        # noktasından DEĞİL reset işaretinin donmuş `egri_son_nokta`sından okunuyor.
        "equity_curve.json": {"run.py", "sermaye.py", "loop.py"},
        "candidates.jsonl": {"loop.py", "run.py"},
        "counterfactuals.jsonl": {"counterfactual.py", "cf_backfill.py"},
        "cf_open.json": {"counterfactual.py", "hermes.py"},   # cf sahibi + LLM görüş damgası (kilitli)
        "wf_cache_rev.json": {"data.py", "reflect.py"},
        "scoreboard.json": {"versioning.py", "run.py"},
        "hypotheses.jsonl": {"memory.py", "sprint.py"},
        "data_quality.json": {"loop.py", "scheduler.py"},
        "strategy.yaml": {"sprint.py"},
        "events.jsonl": {"obs.py"},
    }
    unexpected = {k: sorted(v) for k, v in shared.items() if set(v) != allowed.get(k, set())}
    assert not unexpected, f"beyan edilmemiş ortak yazım (sahiplik belirsiz): {unexpected}"


# ============ ÜRETKENLİK — "çıktısı sessizce boş olabilir" ============
def test_api_diagnostics_is_never_silently_empty(sandbox_state, monkeypatch):
    from fastapi.testclient import TestClient
    from meridian import api
    monkeypatch.setattr(api, "DASH_TOKEN", "")
    d = TestClient(api.app).get("/api/diagnostics").json()
    for section in ("integrity", "coverage", "watchdog", "pipeline"):
        assert section in d and d[section] is not None, f"teşhis '{section}' bölümü boş"


def test_indicators_are_not_silently_all_nan():
    """Hepsi-NaN bir gösterge = ölü sinyal; tarama sessizce hiçbir aday üretmez."""
    from meridian import indicators as ind
    from tests.conftest import make_bars
    bars = make_bars(320, seed=5, trend=0.0008)
    for name, series in (("atr", ind.atr(bars, 14)), ("sma50", ind.sma(bars["close"], 50)),
                         ("volume_ratio", ind.volume_ratio(bars["volume"], 50)),
                         ("pivot_high", ind.pivot_high(bars["high"], 40, 1)),
                         ("trend_template", ind.trend_template(bars))):
        tail = series.iloc[-30:]
        assert tail.notna().any(), f"{name}: son 30 barın TAMAMI NaN — gösterge ölü"


def test_oos_pipeline_is_not_permanently_legacy(seeded):
    """Hep 'legacy' dönmek teyit kapısını SESSİZCE kapatır: gerçek dilimlerle olasılıksal yasa koşmalı."""
    from meridian.oos_pipeline import OutOfSamplePipeline
    from tests.test_decision_v3 import synth_trades, wf_fix
    goal = config.goal()
    inc = synth_trades(111, seed=5)
    cand = [{**t, "r_multiple": t["r_multiple"] + 0.4} for t in inc]
    pipe = OutOfSamplePipeline(goal, n_boot=200, seed=42)
    res = pipe.evaluate_search(wf_fix(inc, goal), wf_fix(cand, goal))
    assert res.law == "probabilistic" and res.p is not None


def test_probgate_produces_a_probability_on_real_slices(seeded):
    from meridian.probgate import PairedProbabilisticGate
    from tests.test_decision_v3 import synth_trades, OOS_START, OOS_END
    inc = synth_trades(111, seed=6)
    cand = [{**t, "r_multiple": t["r_multiple"] + 0.3} for t in inc]
    g = PairedProbabilisticGate(config.goal(), n_boot=200, seed=42).evaluate(
        inc, cand, OOS_START, OOS_END)
    assert g.law == "probabilistic" and g.p is not None and g.n_valid > 0


def test_score_is_defined_once_the_sample_exists(seeded):
    """Hep None dönen bir skor kapıyı sonsuza dek kör bırakır."""
    from meridian import score as sc
    goal = config.goal()
    n = int(goal["min_sample"])
    trades = [{"r_multiple": 0.5, "pnl_dollars": 500,
               "ts_open": f"2026-01-{(i % 27) + 1:02d}", "ts_close": f"2026-02-{(i % 27) + 1:02d}"}
              for i in range(n)]
    assert sc.score(trades, goal) is not None


# ============ KORUNUM — içeri giren sayılabilir bir şey var ============
def test_guard_returns_a_verdict_for_every_plan(seeded):
    from meridian import guard
    goal = config.goal()
    for size_r in (0.1, 1.0, 99.0):
        for budget in (0, 60):
            v, reasons = guard.classify_gate(
                {"ticker": "AAA", "sector": "tech", "size_r": size_r, "r_multiple_expected": 2.5},
                {"open_positions": 0, "sector_counts": {}, "day_pnl_pct": 0.0},
                {"exposure_budget_pct": budget}, goal)
            assert v in ("GO", "REVIEW", "NO_GO") and isinstance(reasons, list)


def test_strategy_runs_every_screen_without_short_circuit():
    """scan_all HER ekranı koşturur: biri sinyal verdi diye diğerleri atlanırsa cf defteri uyuyan
    kurulumları hiç göremez (kanıt üretimi sessizce yarıya iner)."""
    from meridian import strategy
    src = inspect.getsource(strategy.scan_all)
    assert "for fn in" in src and "break" not in src and "return" not in src.split("for fn in")[1].split("return by_setup")[0]


def test_shadow_model_reports_rows_it_could_not_use(sandbox_state):
    """KORUNUM: özelliği eksik satırlar eğitim setinden SESSİZCE düşüyordu — kaç satırın kullanıldığı
    (n_fit) kayıtlı olmalı ki 'model neden zayıf' sorusu cevaplanabilsin."""
    from meridian.shadow_model import ShadowTradeOutcomeModel as M
    good = [{"id": f"P{i}", "score": 70, "rr_expected": 2.5, "regime": "trend_up",
             "r_multiple": 1.0 if i % 2 else -1.0, "entered": True} for i in range(60)]
    bad = [{"id": f"X{i}", "score": None, "rr_expected": None, "regime": "??",
            "r_multiple": 1.0, "entered": True} for i in range(40)]
    store.write_jsonl("counterfactuals.jsonl", good + bad)
    store.write_jsonl("trades.jsonl", [])
    m = M().fit()
    assert m.n_fit == 60, f"kullanılamayan satırlar sayıma karışıyor: n_fit={m.n_fit}"
    m.save()
    assert store.read_json(M.__module__.split('.')[-1] and "shadow_model.json", {}).get("n_fit") == 60


def test_analytics_calibration_counts_what_it_used(sandbox_state):
    from meridian import analytics
    rows = [{"plan_id": f"P{i}", "score": 60 + i, "r_multiple": 1.0 if i % 2 else -1.0,
             "ts_close": "2026-05-01"} for i in range(40)]
    store.write_jsonl("trades.jsonl", rows)
    out = analytics.score_calibration()
    assert out is None or out.get("n") is not None    # 'kaç örnekle' HER ZAMAN yazılı


# ============ DETERMİNİZM — hesap bizim tarafımızda ============
def test_earnings_blackout_is_deterministic(sandbox_state):
    from meridian import earnings
    fut = (dt.date.today() + dt.timedelta(days=3)).isoformat()
    (sandbox_state / "earnings.csv").write_text(f"ticker,date\nAAA,{fut}\n")
    earnings.clear_cache()
    today = dt.date.today().isoformat()
    assert earnings.in_blackout("AAA", today) == earnings.in_blackout("AAA", today)
    assert earnings.coverage(["AAA", "BBB"]) == earnings.coverage(["AAA", "BBB"])


def test_memory_derivations_are_deterministic(sandbox_state):
    from meridian import memory
    store.write_jsonl(memory.HYP, [
        {"id": "H00001", "variable": "entry.min_score", "status": "rejected_by_backtest",
         "predicted_direction": "up", "regime": "chop", "ts": "2026-07-01T00:00:00+00:00"}])
    assert memory.next_id() == memory.next_id() == "H00002"
    assert memory.distill_lessons() == memory.distill_lessons()
    assert memory.accepted_this_month("2026-07-15T00:00:00+00:00") == \
        memory.accepted_this_month("2026-07-15T00:00:00+00:00")


def test_rollback_decision_is_deterministic(seeded):
    """Bir KARAR mekanizması: sabit defterde iki koşu aynı sonucu vermeli."""
    from meridian import rollback, memory as mem
    n = int(config.goal()["min_sample"])
    config.HISTORY.mkdir(parents=True, exist_ok=True)
    config.dump_yaml(config.default_strategy(), config.HISTORY / "v0001.yaml")
    (config.STATE / "strategy.yaml").write_text(yaml.safe_dump(
        {**config.default_strategy(), "version": 2, "parent": 1}))
    mem.record({"id": "H1", "version_to": 2, "status": "live", "variable": "entry.min_score",
                "predicted_delta": 0.05, "backtest": {"incumbent_oos": 0.30}})
    store.write_jsonl("trades.jsonl", [
        {"strategy_version": v, "regime": "trend_up", "r_multiple": r, "pnl_dollars": r * 1000,
         "ts_open": f"2026-0{1 + (i % 6)}-{(i % 27) + 1:02d}",
         "ts_close": f"2026-0{1 + (i % 6)}-{(i % 27) + 2:02d}"}
        for v, r in ((2, 0.32), (1, 0.30)) for i in range(n)])
    a = rollback.evaluate_outcomes()
    b = rollback.evaluate_outcomes()
    assert a["delta"] == b["delta"] and a["rolled_back"] == b["rolled_back"]


def test_skills_enablement_decision_is_deterministic(sandbox_state, monkeypatch):
    from meridian import skills as sk
    from meridian.adapters import fmp, alpaca
    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(alpaca, "paper_available", lambda: False)
    store.write_json(sk.REGISTRY, {"skills": {"canslim-screener": {
        "enabled": False, "mode": "disabled", "reason": "x", "fmp": "req", "alpaca": "opt",
        "style_active": True}}})
    a = sk.reconcile_enablement()
    b = sk.reconcile_enablement()
    assert b["changed"] == [] and a["fmp_ok"] == b["fmp_ok"]      # ikinci koşu NO-OP (idempotent)


def test_spend_cost_math_is_pure():
    from meridian import spend
    assert spend.estimate_cost(1000, 500, "claude-opus-4-8") == \
        spend.estimate_cost(1000, 500, "claude-opus-4-8")
    assert spend.price_for("claude-opus-4-8") == spend.price_for("claude-opus-4-8")


def test_versioning_bump_is_deterministic(seeded):
    from meridian import versioning
    cur = {**config.default_strategy(), "version": 1, "parent": None}
    a = versioning.bump(cur, "entry.min_score", 65)
    b = versioning.bump(cur, "entry.min_score", 65)
    assert a == b and cur["params"]["entry.min_score"] != 65      # girdi mutasyona uğramadı


def test_watchdog_reports_are_deterministic(sandbox_state):
    from meridian import watchdog as wd
    store.write_jsonl("trade_plans.jsonl", [{"id": "P1", "date": "2026-07-20", "gate_verdict": "NO_GO"}])
    assert wd.conservation_report() == wd.conservation_report()
    assert wd.production_report() == wd.production_report()


# ============ TUTARLILIK ============
def test_mcp_serves_the_same_state_the_files_hold(sandbox_state):
    """Ajana SUNULAN türev, kaynağıyla birebir olmalı — bayat bir kopya sunmak ajanı yanlış
    kanıtla düşündürür ve bunu kimse fark etmez."""
    import json
    from meridian import mcp_server as mcp
    store.write_json("regime.json", {"date": "2026-07-20", "regime": "chop",
                                     "exposure_budget_pct": 40, "exposure_score": 45})
    res = mcp._handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": "meridian_regime", "arguments": {}}})
    served = json.loads(res["result"]["content"][0]["text"])
    disk = store.read_json("regime.json", {})
    for k in ("date", "regime", "exposure_budget_pct"):
        assert served[k] == disk[k]


def test_scoreboard_current_version_tracks_the_live_strategy(seeded):
    from meridian import versioning
    versioning.snapshot({**config.default_strategy(), "version": 1, "parent": None})
    child = versioning.bump({**config.default_strategy(), "version": 1, "parent": None},
                            "entry.min_score", 65)
    versioning.commit(child)
    versioning.update_scoreboard(child["version"], parent=1)
    assert int(versioning.scoreboard()["current_version"]) == int(config.load_strategy()["version"])


# ============ MONOTONLUK ============
def test_counterfactual_ledger_is_append_only(sandbox_state):
    """Çözülmüş bir satır 'açık'a GERİ DÖNMEZ ve defter kısalmaz — kanıt geriye sarmaz."""
    from meridian import counterfactual as cf
    rows = [{"id": "P1", "status": "resolved", "entered": True, "r_multiple": 1.2}]
    store.write_jsonl(cf.LEDGER, rows)
    n0 = len(store.read_jsonl(cf.LEDGER))
    store.append_jsonl(cf.LEDGER, {"id": "P2", "status": "resolved", "entered": True, "r_multiple": -0.5})
    after = store.read_jsonl(cf.LEDGER)
    assert len(after) == n0 + 1 and after[0]["id"] == "P1" and after[0]["status"] == "resolved"
    src = inspect.getsource(cf)
    assert "write_jsonl(LEDGER" not in src, "cf defteri TOPTAN yeniden yazılıyor — geçmiş kanıt silinebilir"


def test_obs_event_ledger_only_grows(sandbox_state):
    from meridian import obs
    n0 = len(store.read_jsonl("events.jsonl"))
    obs.log("a"); obs.log("b")
    assert len(store.read_jsonl("events.jsonl")) == n0 + 2
    src = inspect.getsource(obs)
    assert "write_jsonl" not in src, "olay defteri toptan yazılıyor — geçmiş olaylar silinebilir"


def test_shared_writers_go_through_the_file_lock():
    """BULGU (N/A yeniden sorgulaması): hermes, canlı defteri (portfolio.json) AYRI bir iş
    parçacığından kilitsiz yazıyordu — döngünün silahlı setini/pozisyonlarını bayat bir kopyayla
    geri alabilirdi (memory audit #19'un canlı defterdeki hâli). Ortak yazılan her dosya kilitten
    geçmeli."""
    import inspect as _i
    from meridian import hermes, loop, store
    src_h = _i.getsource(hermes._stamp_llm_opinions)
    assert "update_jsonl" in src_h and "update_json" in src_h
    assert 'write_json("portfolio.json"' not in src_h
    assert "file_lock(PORTFOLIO)" in _i.getsource(loop._save_broker)
    # kilit gerçekten dosya başına tek nesne
    assert store.file_lock("x.json") is store.file_lock("x.json")
    assert store.file_lock("x.json") is not store.file_lock("y.json")


def test_update_json_is_atomic_read_modify_write(sandbox_state):
    from meridian import store
    store.write_json("k.json", {"n": 0})
    def bump(doc):
        doc["n"] = doc.get("n", 0) + 1
        return True
    for _ in range(5):
        store.update_json("k.json", bump, {})
    assert store.read_json("k.json", {})["n"] == 5
    # değişiklik yoksa dosyaya DOKUNULMAZ
    before = (sandbox_state / "k.json").read_text()
    store.update_json("k.json", lambda d: False, {})
    assert (sandbox_state / "k.json").read_text() == before

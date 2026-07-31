"""test_ops_v11.py — sentez & koruma katmanı (v11: 1→4, 2026-07-21).

#1 bildirim: yalnız beyaz-liste token'ları kanala gider; token başına 6 saat sessizlik; bekçi
   bayat-GEÇİŞİ bir kez alarmlar, toparlanınca sıfırlanır. (launchd TCC engeli → keepalive modeli;
   süreç dirilişi canlıda kanıtlandı, bu dosya davranış kurallarını test eder.)
#2 öz-değerlendirme: rapor şekli + DİKKAT kuralları eşik-tabanlı (görüş değil).
#3 çelişki dedektörü: katman-çifti kuralları; veri yetersizken sessiz.
#4 gelen kutusu: üç karar türü tek listede; silahlanma bilgi-amaçlı (eylem yok), revizyon/öneri eylemli."""
import shutil
import time
from pathlib import Path

import pytest

from meridian import config, store, obs, watchdog, selfreview


@pytest.fixture
def seeded_sandbox(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.goal.cache_clear(); config.bounds.cache_clear()
    return sandbox_state


# ---------------- #1: bildirim beyaz-listesi + sessizlik penceresi ----------------
def test_notify_whitelist_and_cooldown(seeded_sandbox, monkeypatch):
    from meridian import notify
    sent = []
    monkeypatch.setattr(notify, "configured", lambda: True)
    monkeypatch.setattr(notify, "send", lambda t: sent.append(t) or True)
    obs.alarm("ARMING_READY", "EP hazır")
    # NOT (denetim turu 20, 2026-07-21): eskiden burada HEARTBEAT_STALE vardı — ama o, operatörün
    # UYANMASI gereken sınıftan ve listede olmaması bir eksiklikti; artık bildiriliyor. Beyaz-liste
    # süzgecini test etmek için gerçekten liste dışı, jenerik bir token kullanıyoruz.
    obs.alarm("INTERNAL_DEBUG_TOKEN", "liste dışı — kanala gitmemeli")
    assert len(sent) == 1 and "ARMING_READY" in sent[0]                   # yalnız beyaz-liste
    obs.alarm("ARMING_READY", "tekrar")
    assert len(sent) == 1                                                 # 6 saatlik sessizlik penceresi
    st = store.read_json("notify_sent.json", {})
    st["ARMING_READY"] = time.time() - 7 * 3600
    store.write_json("notify_sent.json", st)
    obs.alarm("ARMING_READY", "pencere geçti")
    assert len(sent) == 2                                                 # pencere dolunca yeniden


def test_watchdog_stale_transition_alarms_once(seeded_sandbox, monkeypatch):
    alarms = []
    monkeypatch.setattr(obs, "alarm", lambda tok, msg, **kw: alarms.append((tok, kw.get("mechanism"))))
    store.write_json(watchdog.BEATS_FILE, {"scheduler_poll": time.time() - 3600})   # pencere 30 dk → bayat
    watchdog.check_and_alarm()
    watchdog.check_and_alarm()                                            # ikinci koşum: aynı bayatlık
    assert alarms.count(("MECHANISM_STALE", "scheduler_poll")) == 1       # bir kez alarmlar (spam yok)
    store.write_json(watchdog.BEATS_FILE, {"scheduler_poll": time.time()})  # toparlandı
    watchdog.check_and_alarm()
    store.write_json(watchdog.BEATS_FILE, {"scheduler_poll": time.time() - 3600})   # yine bayat
    watchdog.check_and_alarm()
    assert alarms.count(("MECHANISM_STALE", "scheduler_poll")) == 2       # yeni bayatlama yine görünür


# ---------------- #2: öz-değerlendirme ----------------
def test_selfreview_shape_and_attention_rules(seeded_sandbox):
    # ŞEMA GÜNCELLENDİ (2026-07-26): dikkat satırı artık GERÇEK dilim + ÖLÇÜLMÜŞ anlamlılık +
    # -0.05 etki eşiği ister (havuzlanmış IC fiilen cf'in IC'siydi ve satırı sürekli tetikliyordu).
    # Fikstür KENDİ İÇİNDE TUTARLI: n=44'te anlamlılık eşiği 1.96/√43 ≈ 0.30, |−0.35| onu aşıyor.
    store.write_json("score_calibration.json",
                     {"rank_ic": -0.35, "n": 44, "n_real": 44, "n_cf": 0, "monotone_hint": False,
                      "real": {"rank_ic": -0.35, "n": 44, "anlamli": True,
                               "se_yontem": "i.i.d._varsayimi"}, "cf": None})
    store.write_json("cf_fidelity.json", {"n": 15, "corr": 0.3, "mean_diff_r": 0.9, "fidelity_ok": False})
    store.write_json("shadow_model.json", {"promotion": {"n_live": 31, "promoted": False}})
    rep = selfreview.build()
    assert {"week", "progress", "calibrations", "attention", "contradictions"} <= set(rep)
    whys = " | ".join(a["why"] for a in rep["attention"])
    assert "NEGATİF" in whys                                              # IC eşiği geçti → dikkat
    assert "iskontolu" in whys or "ONAYSIZ" in whys                       # sadakat onaysız → dikkat
    assert "shadow_promotion" in whys and "31/30" in whys                 # eşik doldu → "karar hazır"
    assert store.read_json(selfreview.REVIEW_FILE, {}).get("generated")   # kalıcılaştı


def test_selfreview_quiet_when_nothing_crosses_threshold(seeded_sandbox):
    rep = selfreview.build()                                              # boş state → eşik geçen yok
    assert rep["attention"] == [] and rep["contradictions"] == []         # sessizlik dürüst


# ---------------- #3: çelişki dedektörü ----------------
def test_contradiction_shadow_vs_llm(seeded_sandbox):
    rows = [{"id": f"P{i}", "ticker": f"T{i}", "p_win_shadow": 0.7, "llm_opinion": "karşı"}
            for i in range(10)]
    store.write_jsonl("trade_plans.jsonl", rows)
    out = selfreview.contradictions()
    pairs = [c["pair"] for c in out]
    assert "gölge_model↔LLM_görüşü" in pairs                              # %100 zıtlık → çelişki


def test_near_miss_feeds_learning_loop(seeded_sandbox):
    """#2 (2026-07-20): eşik-altı karne ARTIK bir karara besleniyor — bir kova yeterli (n>=10) ve
    tutarlı +R (>=0.15) gösterince, ilgili @rejim düğmesini ARAMAYA öneren DİKKAT + çelişki satırı çıkar;
    kanıt zaten denenmişse sessiz; ince dilimde (n<10) sessiz."""
    store.write_json("near_miss.json", {"resolved_total": 60, "buckets": {
        "hacim": {"n": 40, "entered": 35, "n_r": 35, "avg_r": 0.4},       # güçlü kanıt (n_r>=30) → öneri
        "rs": {"n": 6, "entered": 5, "n_r": 5, "avg_r": 0.5},             # n<30 → ince dilim, sessiz
    }})
    rep = selfreview.build()
    whys = " | ".join(a["why"] for a in rep["attention"])
    assert "min_volume_ratio" in whys and "hacim" in whys                 # hacim eşiği → sonda önerisi
    assert "rs_rating_min" not in whys                                    # rs ince dilim → önerilmez
    pairs = [c["pair"] for c in rep["contradictions"]]
    assert "eşik-altı_karne↔arama" in pairs                              # kanıt var, düğme denenmemiş
    # düğme denendiyse çelişki + dikkat düşer
    store.write_jsonl("hypotheses.jsonl", [{"variable": "entry.min_volume_ratio@chop", "ts": "2026-07-20"}])
    rep2 = selfreview.build()
    assert "min_volume_ratio" not in " ".join(a["why"] for a in rep2["attention"])
    assert not any(c["pair"] == "eşik-altı_karne↔arama" for c in rep2["contradictions"])


def test_contradiction_ic_negative_without_weight_probes(seeded_sandbox):
    store.write_json("score_calibration.json", {"rank_ic": -0.2, "n": 40})
    store.write_jsonl("hypotheses.jsonl", [{"variable": "stop_loss_atr_mult", "ts": "2026-07-19"}])
    out = selfreview.contradictions()
    assert any(c["pair"] == "skor_kalibrasyonu↔arama" for c in out)       # kanıt var, öneri yok
    store.append_jsonl("hypotheses.jsonl", {"variable": "entry.w_rs@chop", "ts": "2026-07-20"})
    out2 = selfreview.contradictions()
    assert not any(c["pair"] == "skor_kalibrasyonu↔arama" for c in out2)  # denenmiş → çelişki düştü


# ---------------- #4: gelen kutusu ----------------
def test_inbox_assembles_all_decision_types(seeded_sandbox, monkeypatch):
    from fastapi.testclient import TestClient
    from meridian.api import app
    store.write_json("arming_report.json", {"measurements": {"episodic_pivot":
        {"status": "gate_passed", "search_p": 0.88, "confirm_p": 0.74}},
        "cf_report": {"episodic_pivot": {"n": 34, "avg_r": 0.42}}})
    store.write_json("skill_revisions.json", [{"skill": "vcp-screener", "status": "draft",
                                               "rationale": "stop disiplini", "evidence": {"n": 20, "avg_r": -0.3}}])
    from meridian import skills as sk
    monkeypatch.setattr(sk, "pending_recommendations",
                        lambda: [{"skill": "market-news-analyst", "action": "shadow", "rationale": "zarar"}])
    with TestClient(app) as client:
        d = client.get("/api/approvals").json()
    types = {i["type"] for i in d["inbox"]}
    assert types == {"arming", "skill_revision", "skill_rec"}             # üç tür tek listede
    arm = next(i for i in d["inbox"] if i["type"] == "arming")
    assert arm["actions"] == [] and "Claude" in arm["note"]               # silahlanma: bilgi + insan yolu
    rev = next(i for i in d["inbox"] if i["type"] == "skill_revision")
    assert set(rev["actions"]) == {"apply", "reject"}                     # revizyon: tek tık eylemli


# ---------------- bayat-sinyal dürüstlüğü (GS-1140 dersi, 2026-07-20) ----------------
def test_stale_plan_enrichment(seeded_sandbox):
    """Süresi dolmuş sinyal taze karar gibi OKUNMAZ: expired/age/last_close/traded alanları API'de."""
    import pandas as pd
    from fastapi.testclient import TestClient
    from meridian.api import app
    store.write_jsonl("trade_plans.jsonl", [
        {"id": "P-2026-07-14-GS", "ticker": "GS", "date": "2026-07-14", "entry_trigger": 1140.0,
         "gate_verdict": "GO", "targets": [1313.5]},
    ])
    store.write_json("portfolio.json", {"last_date": "2026-07-17", "positions": {}, "armed": []})
    store.write_jsonl("trades.jsonl", [])
    pd.DataFrame({"date": ["2026-07-16", "2026-07-17"], "close": [1095.46, 1065.22]}).to_csv(
        config.BARS / "gs.csv", index=False)
    with TestClient(app) as client:
        d = client.get("/api/signals").json()
    p2 = next(p3 for p3 in d["plans"] if p3["ticker"] == "GS")
    assert p2["expired"] is True and p2["age_days"] == 3          # 14 → 17 takvim farkı
    assert p2["last_close"] == 1065.22 and p2["drift_pct"] == pytest.approx(-6.6, abs=0.1)
    assert p2["traded"] is False                                  # emre dönüşmedi — dürüstçe görünür
    assert d["latest_session"] == "2026-07-17"
    store.append_jsonl("trades.jsonl", {"plan_id": "P-2026-07-14-GS", "r_multiple": 0.5})
    with TestClient(app) as client:
        d2 = client.get("/api/signals").json()
    assert next(p3 for p3 in d2["plans"] if p3["ticker"] == "GS")["traded"] is True


# ---------------- P4 buharlaşma yaması (GS-1140 KÖK nedeni, 2026-07-20) ----------------
def test_armed_plan_carries_once_when_bar_unpublished(seeded_sandbox):
    """Canlıda yaşandı (GS, 2026-07-15): silahlı plan, dolum anında bar henüz yayınlanmamışsa
    kayıtsız buharlaşıyordu. Yasa: bar yoksa plan BİR seans taşınır (olaylı); ikinci seansta da
    bar yoksa olaylı düşer. Bar'ı olan plan taşınMAZ — dolum adayıdır."""
    from meridian import loop
    plan = {"id": "P-GS", "ticker": "GS", "entry_trigger": 1140.0}
    fillable, carried = loop._carry_armed_without_bar([plan], lambda t: False)   # 1. seans: bar yok
    assert fillable == [] and carried == [plan] and plan["carried"] == 1
    evs = store.read_jsonl("events.jsonl")
    assert any(e.get("event") == "armed_no_bar_carried" and e.get("ticker") == "GS" for e in evs)
    fillable2, carried2 = loop._carry_armed_without_bar(carried, lambda t: False)  # 2. seans: yine yok
    assert fillable2 == [] and carried2 == []                                    # düştü — ama KAYITLI
    assert any(e.get("event") == "armed_expired_no_bar" and e.get("ticker") == "GS"
               for e in store.read_jsonl("events.jsonl"))
    ok_plan = {"id": "P-OK", "ticker": "NVDA"}
    fillable3, carried3 = loop._carry_armed_without_bar([ok_plan], lambda t: True)
    assert fillable3 == [ok_plan] and carried3 == [] and "carried" not in ok_plan


def test_halt_preserves_heartbeat_context_fields(seeded_sandbox):
    """Canlıda görüldü (2026-07-20): /api/halt nabzı yalnız note ile sıfırdan yazınca rejim/bütçe
    silinip HUD 'rejim: yok' gösteriyordu. HALT bağlam alanlarını korumalı; ts/halted tazelenmeli."""
    from fastapi.testclient import TestClient
    from meridian.api import app
    from meridian import health
    health.write_heartbeat(regime="chop", exposure_budget_pct=0, equity=108000.0)
    with TestClient(app) as client:
        assert client.post("/api/halt").status_code == 200
    hb = store.read_json("heartbeat.json", {})
    assert hb["regime"] == "chop" and hb["exposure_budget_pct"] == 0     # bağlam korunuyor
    assert hb["note"] == "HALT via dashboard" and hb["halted"] is True   # niyet + taze durum
    health.halt_path().unlink()                                          # sandbox temizliği


def test_explore_capacity_three_slots_with_total_r_cap(seeded_sandbox):
    """Öğrenme debisi (operatör, 2026-07-20 akşam): kâğıt modunda 5 sonda. Sonda başına 0.25R tavanı
    DEĞİŞMEDİ; toplam keşif riski ≤1.25R sabitle sınırlı. Kaynak-denetim: sabitler + döngü tavanları."""
    import inspect
    from meridian import loop
    assert loop.EXPLORE_MAX_POS == 5 and loop.EXPLORE_MAX_R == 0.25
    assert loop.EXPLORE_TOTAL_R == pytest.approx(5 * 0.25)
    src = inspect.getsource(loop.daily_cycle)
    assert "n_explore >= EXPLORE_MAX_POS" in src                  # slot tavanı döngüde denetleniyor
    assert "used_r + EXPLORE_MAX_R > EXPLORE_TOTAL_R" in src      # toplam R tavanı döngüde denetleniyor
    assert 'min(float(chosen["size_r"]), EXPLORE_MAX_R)' in src   # sonda başına tavan korunuyor

"""test_llm_advisor_v6.py — LLM danışman katmanı (Kademe 1-3 + keşif-slot seçimi, 2026-07-20).

Kademe 1: görüşler plan satırlarına GERİYE dönük damgalanır (inceleme asenkron iner) — trade_plans +
          portfolio.armed; damga bilgidir, yetkisi yoktur.
Kademe 2: görüş↔sonuç kalibrasyon defteri; terfi kuralı ŞİMDİDEN yazılı (≥30 çift, kova≥8, Rfark≥0.3).
Kademe 3: terfili ajanın TEK yetkisi REVIEW+karşı planı dolumdan düşürmek — ayna iptali doğrulanmadan
          ASLA (iki defterin ayrışması vetodan büyük risk). GO dokunulmaz.
Bonus:    keşif slotu — kapıyı geçmiş eşitler arasında sıralama; cevap yoksa skor sırası (fail-open).
Yalıtım:  llm_opinion backtest/kapı kaynağına hiçbir koşulda giremez."""
import inspect
import shutil
from pathlib import Path

import pytest

from meridian import config, store, analytics, loop
from meridian import hermes


@pytest.fixture
def seeded_sandbox(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.goal.cache_clear(); config.bounds.cache_clear()
    return sandbox_state


def _plan_row(pid, ticker, date="2026-07-20", verdict="REVIEW", opinion=None):
    r = {"id": pid, "ticker": ticker, "date": date, "gate_verdict": verdict}
    if opinion:
        r["llm_opinion"] = opinion
    return r


# ---------------- Kademe 1: geri-damga ----------------
def test_stamp_backfills_plans_and_armed(seeded_sandbox):
    store.write_jsonl("trade_plans.jsonl", [_plan_row("P1", "AAA"), _plan_row("P2", "BBB"),
                                            _plan_row("P3", "CCC", date="2026-07-19")])
    store.write_json("portfolio.json", {"armed": [_plan_row("P1", "AAA")], "positions": {}})
    hermes._stamp_llm_opinions("2026-07-20", [{"ticker": "AAA", "opinion": "karşı"},
                                              {"ticker": "BBB", "opinion": "destekle"},
                                              {"ticker": "CCC", "opinion": "karşı"}])
    plans = {p["id"]: p for p in store.read_jsonl("trade_plans.jsonl")}
    assert plans["P1"]["llm_opinion"] == "karşı" and plans["P2"]["llm_opinion"] == "destekle"
    assert "llm_opinion" not in plans["P3"]                        # başka günün planına damga sızmaz
    armed = store.read_json("portfolio.json", {})["armed"]
    assert armed[0]["llm_opinion"] == "karşı"                      # P4 vetosunun okuyacağı kopya da damgalı


# ---------------- Kademe 2: kalibrasyon + yazılı terfi kuralı ----------------
def _seed_pairs(n_destekle, n_karsi, r_destekle, r_karsi):
    plans, trades = [], []
    i = 0
    for _ in range(n_destekle):
        plans.append(_plan_row(f"D{i}", f"T{i}", opinion="destekle"))
        trades.append({"plan_id": f"D{i}", "r_multiple": r_destekle}); i += 1
    for _ in range(n_karsi):
        plans.append(_plan_row(f"K{i}", f"T{i}", opinion="karşı"))
        trades.append({"plan_id": f"K{i}", "r_multiple": r_karsi}); i += 1
    store.write_jsonl("trade_plans.jsonl", plans)
    store.write_jsonl("trades.jsonl", trades)


def test_llm_calibration_buckets_and_promotion_rule(seeded_sandbox, monkeypatch):
    monkeypatch.setattr(analytics, "_trades", lambda: store.read_jsonl("trades.jsonl"))
    _seed_pairs(20, 15, 0.5, -0.2)                                  # 35 çift · kovalar dolu · fark 0.7R
    out = analytics.llm_opinion_calibration()
    assert out["buckets"]["destekle"]["n"] == 20 and out["buckets"]["karşı"]["avg_r"] == -0.2
    assert out["r_gap"] == pytest.approx(0.7) and out["promoted"] is True
    assert analytics.llm_promoted() is True
    _seed_pairs(20, 15, 0.5, 0.4)                                   # fark 0.1 < 0.3 → sinyal yok
    assert analytics.llm_opinion_calibration()["promoted"] is False
    _seed_pairs(15, 5, 0.9, -0.9)                                   # 'karşı' kovası < 8 → yetersiz
    assert analytics.llm_opinion_calibration()["promoted"] is False
    assert analytics.llm_promoted() is False                        # terfi düşünce yetki de düşer


# ---------------- Kademe 3: dolum-anı vetosu ----------------
def test_veto_needs_promotion_and_respects_mirror(seeded_sandbox, monkeypatch):
    meta = {"armed": [_plan_row("P1", "AAA", verdict="REVIEW", opinion="karşı"),
                      _plan_row("P2", "BBB", verdict="GO", opinion="karşı"),
                      _plan_row("P3", "CCC", verdict="REVIEW", opinion="destekle")],
            "alpaca_submitted": []}
    store.write_jsonl("trade_plans.jsonl", [dict(p) for p in meta["armed"]])
    monkeypatch.setattr(analytics, "llm_promoted", lambda: False)
    loop._llm_veto_filter(meta)
    assert len(meta["armed"]) == 3                                  # TERFİSİZ → hiçbir şeye dokunamaz
    monkeypatch.setattr(analytics, "llm_promoted", lambda: True)
    loop._llm_veto_filter(meta)
    ids = [p["id"] for p in meta["armed"]]
    assert ids == ["P2", "P3"]                                      # yalnız REVIEW+karşı düştü; GO dokunulmadı
    led = {p["id"]: p for p in store.read_jsonl("trade_plans.jsonl")}
    assert led["P1"].get("llm_veto") is True                        # defterde denetlenebilir iz


def test_veto_never_desyncs_mirror(seeded_sandbox, monkeypatch):
    """Alpaca'ya gönderilmiş plan: iptal DOĞRULANAMAZSA dolum sürer (tutarlılık > veto)."""
    from meridian.adapters import alpaca
    meta = {"armed": [_plan_row("P1", "AAA", verdict="REVIEW", opinion="karşı")],
            "alpaca_submitted": ["P1"]}
    store.write_jsonl("trade_plans.jsonl", [dict(meta["armed"][0])])
    monkeypatch.setattr(analytics, "llm_promoted", lambda: True)
    monkeypatch.setattr(alpaca, "orders", lambda **k: (_ for _ in ()).throw(RuntimeError("api down")))
    loop._llm_veto_filter(meta)
    assert [p["id"] for p in meta["armed"]] == ["P1"]               # API çöktü → plan KORUNDU
    ok = [{"id": "o9", "client_order_id": "P1", "filled_qty": "0", "status": "new"}]
    monkeypatch.setattr(alpaca, "orders", lambda **k: ok)
    monkeypatch.setattr(alpaca, "cancel_order", lambda oid: {"ok": True})
    loop._llm_veto_filter(meta)
    assert meta["armed"] == []                                      # iptal doğrulandı → şimdi düşebilir


# ---------------- Bonus: keşif-slot sıralayıcı ----------------
def test_rank_explore_parses_and_fails_open(sandbox_state, monkeypatch):
    """NOT (2026-07-21): bu test sandbox'sız yazılmıştı ve CANLI state'teki agent_budget.json'u
    okuyordu — günlük ajan kotası dolunca (day=150) _agent_call None döndürüyor ve test, kodda
    hiçbir şey değişmeden kırılıyordu. Testler canlı mutable duruma bağlanamaz."""
    import subprocess
    cands = [{"ticker": "AAA", "setup": "breakout_vcp", "score": 80, "rr": 2.5},
             {"ticker": "BBB", "setup": "pullback", "score": 75, "rr": 2.2}]
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/fake/hermes")
    class R: returncode = 0; stdout = "╭─ panel ─╮\nI pick BBB because...\n╰─╯"; stderr = ""
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: R())
    assert hermes.rank_explore(cands) == "BBB"                      # süslü çıktıdan geçerli sembol
    class Bad: returncode = 0; stdout = "ZZZ maybe?"; stderr = ""
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: Bad())
    assert hermes.rank_explore(cands) is None                       # geçersiz cevap → fail-open
    assert hermes.rank_explore(cands[:1]) is None                   # tek aday → çağrı bile yok
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: None)
    assert hermes.rank_explore(cands) is None                       # ajan yok → skor sırası devralır
    src = inspect.getsource(loop.daily_cycle)
    assert "ordered = list(explore_pool)" in src                    # fallback kaynakta sabit: havuz
    assert "EXPLORE_TOTAL_R" in src                                 # skor sıralı gelir, toplam R tavanlı


# ---------------- Yalıtım: görüş kapıya/backtest'e sızamaz ----------------
def test_llm_opinion_never_reaches_gate_or_backtest():
    import meridian.backtest as bt, meridian.probgate as pg, meridian.guard as gd, meridian.reflect as rf
    for mod in (bt, pg, gd, rf):
        assert "llm_opinion" not in inspect.getsource(mod), mod.__name__
    # veto fonksiyonu terfi kapısıyla korunuyor (kaynak denetimi)
    src = inspect.getsource(loop._llm_veto_filter)
    assert "llm_promoted" in src and '"REVIEW"' in src and "karşı" in src


# ---------------- ajan skill senkronu + skill-farkındalıklı çağrılar (2026-07-20) ----------------
def test_agent_skill_sync_links_enabled_prunes_stale_spares_alien(tmp_path, monkeypatch, sandbox_state):
    """Ajan skill seti = Meridian enabled seti: eksik linklenir, bayat Meridian linki sökülür,
    ajanın KENDİ (yabancı) dizinlerine asla dokunulmaz. Canlıda yakalanan kusurun kalıcı testi:
    8 devre-dışı skill ajanda aktif kalmıştı."""
    import os
    from meridian import hermes, skills as sk
    agent = tmp_path / "agent_skills"; agent.mkdir()
    monkeypatch.setattr(hermes, "AGENT_SKILLS_DIR", str(agent))
    repo = Path(hermes.__file__).resolve().parent.parent / "skills"
    enabled = {s2["name"] for s2 in sk.catalog() if s2.get("enabled")}
    disabled = next(s2["name"] for s2 in sk.catalog() if not s2.get("enabled"))
    (agent / "yabanci-builtin").mkdir()                                   # ajanın kendi dizini (link değil)
    os.symlink(repo / disabled, agent / disabled)                         # bayat: devre-dışı ama linkli
    out = hermes.sync_agent_skills()
    # ALAN ADI GÜNCELLENDİ (v242, 2026-08-13): dönüşteki `linked` → `yeni_baglanan`. İDDİA
    # DEĞİŞMEDİ, ADI DEĞİŞTİ — eski ad `agent_skill_coverage()`teki `linked` ile ÇAKIŞIYORDU
    # (biri "o senkronda YENİ kurulan", öteki "bağlı TOPLAM") ve canlı bir denetim tam bu yüzden
    # `linked: 4`ü "30'un yalnız 4'ü bağlı" diye okudu. Alt satırdaki `cov["linked"]` BİLEREK
    # dokunulmadan bırakıldı: pano onu okuyor ve orada anlamı zaten toplamdır.
    assert out["enabled"] == len(enabled) and len(out["yeni_baglanan"]) == len(enabled)
    assert disabled in out["pruned"]                                      # kapalı skill ajandan söküldü
    assert (agent / "yabanci-builtin").exists()                           # yabancı dizin kutsal
    cov = hermes.agent_skill_coverage()
    assert cov["linked"] == cov["enabled"] and cov["stale_linked"] == 0 and cov["missing"] == []
    assert out["bagli_toplam"] == cov["linked"]                           # iki yüzey aynı sayıyı der


def test_skill_preload_sets_are_curated_and_capped():
    from meridian import hermes, skills as sk
    ps = hermes._skill_preload("proposal")
    assert len(ps) <= 8 and "pre-trade-discipline-gate" in ps and "macro-regime-detector" in ps
    rv = hermes._skill_preload("review", ("breakout_vcp", "episodic_pivot"))
    assert "vcp-screener" in rv and "stockbee-episodic-pivot-analyzer" in rv and len(rv) <= 8
    enabled = {s2["name"] for s2 in sk.catalog() if s2.get("enabled")}
    assert set(ps) <= enabled and set(rv) <= enabled                      # asla kapalı skill yüklenmez


def test_proposal_path_is_skill_aware_not_tool_forbidding():
    import inspect
    from meridian import hermes
    src = inspect.getsource(hermes._propose_nous_local)
    assert "no tool use" not in src.lower()                               # eski yasak kalktı
    assert "_agent_call(" in src and "_skill_preload" in src              # tek kapı + ön-yükleme
    assert "FINAL message" in src and "ONLY the JSON" in src              # çıktı disiplini korunur
    wsrc = inspect.getsource(hermes._agent_call)                          # sözleşme sarmalayıcıda yaşıyor:
    assert "sync_agent_skills()" in wsrc                                  # set eşitleme
    assert "_agent_budget_take" in wsrc                                   # + oran bütçesi (v9)
    # ÇİVİ TAŞINAN GÖVDEYE YENİDEN HEDEFLENDİ (2026-08-02, HERMES-DAYANIKLILIK turu; 8aaf05e emsali).
    # `-s` ön-yükleme bayrağı artık komutu kuran TEK yerde (`_agent_chat_cmd`) yaşıyor — çünkü `-Q`
    # sessiz-mod bayrağı eklenirken komut iki kez kuruluyordu (bayrağın yarısını taşıyan ikinci
    # davranış riski). İDDİA DEĞİŞMEDİ, YERİ DEĞİŞTİ: aranan şey hâlâ "ön-yükleme gerçekten
    # gönderiliyor mu". Üçüncü satır kaçış yolunu kapatır: gövde ayrı dosyaya taşınıp `_agent_call`
    # onu ÇAĞIRMASA, ilk iki iddia yine geçerdi ve çivi hiçbir şey ölçmezdi.
    csrc = inspect.getsource(hermes._agent_chat_cmd)
    assert '"-s"' in csrc                                                 # -s yükleme (taşınan gövde)
    assert "_agent_chat_cmd(" in wsrc                                     # ve tek kapı onu ÇAĞIRIYOR

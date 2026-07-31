"""test_cf_round2_v55.py — counterfactual, İKİNCİ TUR denetimi (2026-07-21).

İlk turda cf'nin altı deseni de kapanmıştı. İkinci tur farklı bir soru sorar:
**"testler geçiyor, peki üretilen KANIT gerçekten sorulan soruya cevap veriyor mu?"**

BULGU: cf defterinin %70'i (canlıda 7115 satırın 4950'si) `regime: "?"` taşıyordu. Plan satırları
rejimi plandan alıyordu; UYUYAN ve EŞİK-ALTI satırlar rejimsiz yazılıyordu. Testlerin hiçbiri
kırılmıyordu — çünkü hepsi "satır üretildi mi / korunuyor mu / deterministik mi" diye soruyordu.

Sessiz sonuç bir MANTIK BOŞLUĞUYDU: selfreview, eşik-altı kanıtından *"`knob`@rejim sondası
aramaya değer"* önerisi üretiyor — ama kanıtta rejim yok. Öneri, hangi rejime yazılacağını
dayandıramıyordu. Zincir artık uçtan uca kapalı: cf rejimi damgalar → near_miss raporu rejim
dilimi taşır → öneri EN GÜÇLÜ dilimi adlandırır, yoksa dürüstçe global der.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from meridian import analytics, config, counterfactual as cf, selfreview, store


@pytest.fixture
def seeded(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    yield sandbox_state
    config.reload_config()


class _Sig:
    def __init__(self, ticker, setup="breakout_vcp", score=68):
        self.ticker, self.setup, self.score = ticker, setup, score
        self.entry_trigger, self.stop, self.profit_target = 100.0, 95.0, 115.0


def _plan(tid="P1", ticker="AAA", regime="chop"):
    return {"id": tid, "ticker": ticker, "setup": "breakout_vcp", "score": 71,
            "entry_trigger": 100.0, "stop": 95.0, "profit_target": 115.0,
            "r_multiple_expected": 3.0, "regime_at_plan": regime, "gate_verdict": "GO",
            "skill_chain": ["vcp-screener"]}


# ---------- BULGU: her cf satırı rejim taşır ----------
def test_every_cf_row_carries_the_session_regime(seeded):
    cf.collect("2026-07-20", [_plan()], {"P1"}, [_Sig("BBB")], 15,
               near_miss=[(_Sig("CCC"), ["hacim"])], regime="chop")
    rows = store.read_json(cf.OPEN_FILE, [])
    assert len(rows) == 3
    by_ticker = {r["ticker"]: r for r in rows}
    assert by_ticker["AAA"]["regime"] == "chop"        # plandan
    assert by_ticker["BBB"]["regime"] == "chop", "UYUYAN satır rejimsiz — rejim analizi kör kalır"
    assert by_ticker["CCC"]["regime"] == "chop", "EŞİK-ALTI satır rejimsiz — öneri dayanaksız kalır"


def test_regime_defaults_to_unknown_when_not_supplied(seeded):
    """Rejim verilmezse UYDURULMAZ: '?' dürüsttür ve rejim dilimlerinden dışlanır."""
    cf.collect("2026-07-20", [], set(), [_Sig("DDD")], 15, near_miss=[(_Sig("EEE"), ["rs"])])
    rows = {r["ticker"]: r for r in store.read_json(cf.OPEN_FILE, [])}
    assert rows["DDD"]["regime"] == "?" and rows["EEE"]["regime"] == "?"


def test_loop_and_backfill_both_pass_the_regime():
    import inspect
    from meridian import loop, cf_backfill
    assert 'regime=rj["regime"]' in inspect.getsource(loop.daily_cycle)
    assert 'regime=rj["regime"]' in inspect.getsource(cf_backfill)


# ---------- zincirin ikinci halkası: rapor rejim dilimi taşır ----------
def test_near_miss_report_slices_by_regime(seeded):
    rows = []
    for i in range(12):
        rows.append({"id": f"N{i}", "near_miss": True, "blocked_by": ["hacim"], "entered": True,
                     "status": "resolved", "r_multiple": 0.5, "regime": "chop"})
    for i in range(12):
        rows.append({"id": f"M{i}", "near_miss": True, "blocked_by": ["hacim"], "entered": True,
                     "status": "resolved", "r_multiple": -0.3, "regime": "trend_up"})
    store.write_jsonl(cf.LEDGER, rows)
    rep = analytics.near_miss_report()
    b = rep["buckets"]["hacim"]
    assert b["n_r"] == 24
    assert b["by_regime"]["chop"]["avg_r"] == 0.5 and b["by_regime"]["chop"]["n_r"] == 12
    assert b["by_regime"]["trend_up"]["avg_r"] == -0.3


# ---------- zincirin üçüncü halkası: öneri KANITLANMIŞ rejimi adlandırır ----------
def test_recommendation_names_the_regime_the_evidence_supports(seeded):
    store.write_json("near_miss.json", {"resolved_total": 40, "buckets": {
        "hacim": {"n": 40, "entered": 35, "n_r": 35, "avg_r": 0.30,
                  "by_regime": {"chop": {"n_r": 30, "avg_r": 0.55},
                                "trend_up": {"n_r": 5, "avg_r": 0.02}}}}})
    whys = " | ".join(a["why"] for a in selfreview.build()["attention"])
    assert "min_volume_ratio@chop" in whys, f"öneri rejimi adlandırmıyor: {whys}"
    assert "0.55" in whys and "n=30" in whys                 # DAYANAK gösteriliyor


def test_recommendation_falls_back_to_global_without_regime_evidence(seeded):
    """Rejim dilimi eşiği dolduramadıysa uydurma bir rejim SEÇİLMEZ — dürüstçe global sonda önerilir."""
    store.write_json("near_miss.json", {"resolved_total": 40, "buckets": {
        "hacim": {"n": 40, "entered": 35, "n_r": 35, "avg_r": 0.30,
                  "by_regime": {"?": {"n_r": 35, "avg_r": 0.30}}}}})
    whys = " | ".join(a["why"] for a in selfreview.build()["attention"])
    assert "min_volume_ratio" in whys and "@" not in whys.split("min_volume_ratio")[1][:12]
    assert "GLOBAL" in whys


def test_unknown_regime_is_never_treated_as_a_regime(seeded):
    """'?' bir rejim DEĞİLDİR: dilim seçiminde asla aday olamaz (uydurma @? knob'u yaratmaz)."""
    store.write_json("near_miss.json", {"resolved_total": 60, "buckets": {
        "hacim": {"n": 60, "entered": 55, "n_r": 55, "avg_r": 0.40,
                  "by_regime": {"?": {"n_r": 50, "avg_r": 0.9}}}}})
    whys = " | ".join(a["why"] for a in selfreview.build()["attention"])
    assert "@?" not in whys


# ---------- ilk turun testleri hâlâ geçerli mi (çürüme kontrolü) ----------
def test_first_round_invariants_still_hold(seeded):
    """İkinci tur, birinci turun iddialarını da yeniden doğrular: sıfır yetki + yalnız kendi dosyaları."""
    import ast, pathlib as _p
    src = _p.Path("meridian/counterfactual.py").read_text()
    called = {n.func.attr for n in ast.walk(ast.parse(src))
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    for forbidden in ("submit", "commit", "dump_yaml", "write_heartbeat"):
        assert forbidden not in called
    writes = {n.args[0].value for n in ast.walk(ast.parse(src))
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
              and n.func.attr in ("write_json", "write_jsonl", "append_jsonl")
              and n.args and isinstance(n.args[0], ast.Constant)}
    assert writes <= {cf.OPEN_FILE, cf.LEDGER}


def test_near_miss_rows_stay_out_of_the_default_evidence_set(seeded):
    """Eşik-altı satırlar VARSAYILAN kanıt kümesinde YOK (8 tüketici seyrelmesin) — ama artık
    rejimli oldukları için near_miss raporunda tam güçle kullanılabiliyorlar."""
    store.write_jsonl(cf.LEDGER, [
        {"id": "A", "entered": True, "status": "resolved", "r_multiple": 1.0, "regime": "chop"},
        {"id": "B", "entered": True, "status": "resolved", "r_multiple": -1.0, "regime": "chop",
         "near_miss": True}])
    assert [r["id"] for r in cf.resolved_rows(entered_only=True)] == ["A"]
    assert len(cf.resolved_rows(entered_only=True, include_near_miss=True)) == 2


# ---------- backfill tekrarının çift kanıt üretmemesi ----------
def test_collect_is_idempotent_against_the_resolved_ledger(seeded):
    """BACKFILL TEKRARINDAN ÖNCE BULUNDU: `collect` yalnız AÇIK satırları eliyordu. Çözülmüş bir
    satır open_rows'ta olmadığı için, defteri yeniden üreten her koşu AYNI kanıtı ikinci kez
    açardı — 7115 satır 14000 olur ve her ölçüm (kazanma, ort. R, skill katkısı) çift sayılmış
    kanıtla hesaplanırdı. Hiçbir alarm ötmezdi."""
    cf._LEDGER_IDS.update(mtime=None, ids=set())
    store.write_jsonl(cf.LEDGER, [{"id": "CF-2026-07-20-AAA-breakout_vcp", "status": "resolved",
                                   "entered": True, "r_multiple": 1.0, "regime": "chop"}])
    n = cf.collect("2026-07-20", [_plan()], {"P1"}, [], 15, regime="chop")
    assert n == 0, "çözülmüş kanıt İKİNCİ kez açıldı"
    assert store.read_json(cf.OPEN_FILE, []) == []


def test_ledger_id_cache_follows_the_file(seeded):
    cf._LEDGER_IDS.update(mtime=None, ids=set())
    store.write_jsonl(cf.LEDGER, [{"id": "X1"}])
    assert "X1" in cf._ledger_ids()
    store.write_jsonl(cf.LEDGER, [{"id": "X1"}, {"id": "X2"}])
    assert "X2" in cf._ledger_ids(), "defter değişti, kimlik önbelleği bayat kaldı"

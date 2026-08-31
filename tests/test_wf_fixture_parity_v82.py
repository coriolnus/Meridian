"""test_wf_fixture_parity_v82.py — WALK_FORWARD FİKSTÜR KAYNAĞI ÜRETİCİYİ YANSITIYOR MU (2026-07-23).

`tests/wf_fixtures.py` beş+ test dosyasının elle taklitlerinin yerini aldı. Ama merkezi bir taklit de
sürüklenebilir: üretici (backtest.walk_forward) yasasını değiştirir, fabrika eski yasada kalır ve tüm
o dosyalar yine kendi kopyalarını doğrular. Bu dosya kaynağı üreticiye ÇİVİLER: sürüklenirse burası
kırmızı yanar ve nereye bakılacağını söyler.
"""
from __future__ import annotations

import inspect

import pytest

from meridian import backtest, config, reflect
from meridian.oos_pipeline import OutOfSamplePipeline
from tests import wf_fixtures as wf


@pytest.fixture
def seeded(sandbox_state):
    import shutil
    from pathlib import Path
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        if (repo / f).exists():
            shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    yield sandbox_state
    config.reload_config()


def test_the_fixture_derives_slices_the_same_way_the_producer_does():
    """ÜRETİCİ YASASI KİLİDİ: walk_forward Search'e daraltıyorsa fabrika da daraltmalı."""
    src = inspect.getsource(backtest.walk_forward)
    assert "_search_folds" in src and "_search_end" in src, \
        "üretici artık Search'e daraltmıyor — wf_fixtures'ı da güncelle"
    assert wf.SEARCH_FOLDS == [b for b in wf.FOLDS if b < wf.S_END] + [wf.S_END]
    assert wf.SEARCH_FOLDS[-1] == wf.S_END and all(b <= wf.S_END for b in wf.SEARCH_FOLDS)


def test_the_fixture_output_has_the_keys_the_gate_reads():
    """SÖZLEŞME KİLİDİ: kapının VE SHIP YOLUNUN okuduğu her alan fabrikanın çıktısında olmalı,
    yoksa sessiz None. `full_detail` 2026-09-01'de listeye girdi: ship yolu onu karneye
    `backtest_full` olarak yazıyor (N00017) ve alanı `.get` ile okuyor — fikstürden düşerse
    kırmızı değil SESSİZ bir yazmama olurdu."""
    reads = {"oos_score", "oos_folds", "oos_tail_risk", "holdout_score",
             "oos_split", "_trades_search", "_trades_confirm", "full_detail"}
    out = wf.wf_from_trades(wf.trades(40, 1, wf.S_LO, wf.S_END, 0.5) +
                            wf.trades(20, 2, wf.S_END, wf.OOS_END, 0.5))
    missing = reads - set(out)
    assert not missing, f"fabrika kapının okuduğu alanları üretmiyor: {missing}"
    sp = out["oos_split"]
    assert set(sp) == {"search_start", "search_end", "confirm_start", "confirm_end"}


def test_the_fixture_triggers_the_probabilistic_law_not_legacy(seeded):
    """ASIL AMAÇ: eski taklitler legacy yasaya düşüyordu. Fabrika çıktısı has_slices=True vermeli ve
    _gate_eval OLASILIKSAL yola girmeli — yoksa bütün refactor boşuna."""
    assert OutOfSamplePipeline.has_slices(
        wf.wf_from_trades(wf.trades(40, 1, wf.S_LO, wf.S_END, 0.5))) is True

    goal = config.goal()
    inc = wf.wf_from_scores(0.20, folds=((40, 0.4), (40, 0.4)))
    cand = wf.wf_from_scores(0.55, folds=((40, 1.2), (40, 1.2)))
    passes, gate, why = reflect._gate_eval(inc, cand, k_probes=1)
    assert gate.get("law") != "legacy", f"fabrika hâlâ legacy yasayı tetikliyor: {gate}"
    assert "search_p" in gate, "olasılıksal yol koşmadı — dilimler tüketilmedi"


def test_wf_from_scores_preserves_the_caller_supplied_scalars(seeded):
    """KÖPRÜ SÖZLEŞMESİ: wf_from_scores verilen oos/tail/holdout'u KORUMALI (magnitude gate testleri
    bu skalarlara güvenir) ve altına gerçek dilimler döşemeli."""
    w = wf.wf_from_scores(0.37, folds=((25, 0.6),), tail={"cvar": -0.5}, holdout=0.29)
    assert w["oos_score"] == 0.37 and w["oos_tail_risk"] == {"cvar": -0.5} and w["holdout_score"] == 0.29
    assert w["oos_folds"] == [{"n": 25, "avg_r": 0.6}]
    assert len(w["_trades_search"]) > 0 and len(w["_trades_confirm"]) > 0

"""test_score_audit_v40.py — score denetimi (2026-07-21, tur 27).

Kapının okuduğu TEK sayı burada üretiliyor. Mutlak değeri sezgisel; kritik olan İKİ tarafın aynı
fonksiyonla ölçülmesi ve sayının yalan söylememesi. 7. soru:
  SC1 "bilinmeyen skor 0 değildir" → None dönüşü sözleşmenin kalbi; bir gün 0.0'a düşerse kapı
     'vasat ama tanımlı' bir sayı görür ve zayıf adayı ölçer gibi yapar
  SC2 "yıllıklaştırma PENCEREYE bağlıdır" → 20 günlük bir patlama 183 günlük OOS'ta 9x şişiyordu
     (audit #5); span_days verilmezse KÜMENİN kendi aralığına düşer — bu ikisinin farkı test edilmeli
  SC3 "drawdown açık pozisyonu saklayamaz" → M2M eğrisi verilince DAHA KÖTÜ olan kazanır (audit #6)
  SC4 "kuyruk riski bağımlılığı korur" → blok bootstrap; IID örnekleme kuyruğu SİSTEMATİK küçültür
  SC5 "aynı girdi aynı sayı" → kapı iki tarafı kıyaslıyor; gürültü varsa kıyas anlamsız
"""
from __future__ import annotations

import pytest

from meridian import score as sc


GOAL = {"min_sample": 20, "target_return_30d": 0.03, "max_drawdown": 0.12, "min_sharpe": 1.0}


def _trades(n=30, r=0.5, pnl=500.0, start="2026-01-01", step=3):
    import datetime as dt
    d0 = dt.date.fromisoformat(start)
    return [{"r_multiple": r, "pnl_dollars": pnl,
             "ts_open": str(d0 + dt.timedelta(days=i * step)),
             "ts_close": str(d0 + dt.timedelta(days=i * step + 1))} for i in range(n)]


# ---------- SC1: bilinmeyen ≠ vasat ----------
def test_sc1_below_min_sample_is_none_not_zero():
    d = sc.score_detail(_trades(19), GOAL)
    assert d["score"] is None and "undefined" in d["reason"]
    assert sc.score(_trades(19), GOAL) is None
    assert sc.score([], GOAL) is None


def test_sc1b_at_min_sample_it_becomes_defined():
    assert sc.score(_trades(20), GOAL) is not None


# ---------- SC2: yıllıklaştırma penceresi ----------
def test_sc2_window_length_deflates_a_clustered_burst():
    """Aynı işlemler: 20 güne sıkışmış bir patlama, 183 günlük pencerede ölçülünce DAHA DÜŞÜK
    30-günlük getiri vermeli. Bu düzeltilmeden önce kapı sahte bir kazanan üretiyordu (audit #5)."""
    burst = _trades(30, r=1.0, pnl=800.0, step=0)          # hepsi ~aynı gün
    tight = sc.score_detail(burst, GOAL, span_days=20)
    wide = sc.score_detail(burst, GOAL, span_days=183)
    assert wide["realized_30d"] < tight["realized_30d"]
    assert wide["score"] <= tight["score"]


def test_sc2b_without_span_it_uses_the_cluster_span():
    t = _trades(30, step=6)                                 # ~174 gün
    d = sc.score_detail(t, GOAL)
    assert d["realized_30d"] == sc.score_detail(t, GOAL, span_days=sc._span_days(t))["realized_30d"]


# ---------- SC3: drawdown saklanamaz ----------
def test_sc3_mtm_curve_can_only_worsen_drawdown():
    t = _trades(30, r=0.5, pnl=500.0)
    base = sc.score_detail(t, GOAL, span_days=90)
    worse = sc.score_detail(t, GOAL, span_days=90,
                            mtm_equity=[("2026-01-05", 100_000), ("2026-01-06", 70_000),
                                        ("2026-01-07", 105_000)])
    assert worse["max_drawdown"] > base["max_drawdown"], "açık pozisyon drawdown'ı saklanıyor"
    assert worse["score"] <= base["score"]


def test_sc3b_broken_mtm_input_does_not_crash():
    t = _trades(30)
    d = sc.score_detail(t, GOAL, span_days=90, mtm_equity=[("x", "bozuk")])
    assert d["score"] is not None


# ---------- SC4/SC5: kuyruk + determinizm ----------
def test_sc4_tail_risk_is_deterministic_and_honest_when_thin():
    t = _trades(30, r=0.4)
    assert sc.tail_risk(_trades(5)) is None                 # ince dilimde UYDURMA yok
    a, b = sc.tail_risk(t), sc.tail_risk(t)
    assert a == b and a["var_r"] is not None


def test_sc4b_tail_grows_with_a_fat_left_tail():
    good = [{"r_multiple": 0.5} for _ in range(40)]
    bad = good[:35] + [{"r_multiple": -6.0} for _ in range(5)]
    assert sc.tail_risk(bad)["cvar_r"] > sc.tail_risk(good)["cvar_r"]


def test_sc5_scoring_is_deterministic():
    t = _trades(40, r=0.3, pnl=300.0)
    assert sc.score_detail(t, GOAL, span_days=120) == sc.score_detail(t, GOAL, span_days=120)


def test_score_is_bounded_and_directional():
    win = sc.score(_trades(30, r=1.0, pnl=900.0), GOAL, )
    lose = sc.score(_trades(30, r=-1.0, pnl=-900.0), GOAL)
    assert -1.0 <= lose < win <= 1.0


def test_kelly_is_none_without_both_sides():
    only_wins = [{"r_multiple": 1.0} for _ in range(20)]
    assert sc.kelly_fraction(only_wins) is None             # kayıp yoksa oran tanımsız
    mixed = only_wins[:12] + [{"r_multiple": -1.0} for _ in range(8)]
    k = sc.kelly_fraction(mixed)
    assert k and 0.0 <= k["half_kelly"] <= abs(k["full_kelly"]) + 1e-9


def test_max_drawdown_math():
    assert sc.max_drawdown([100, 120, 60, 90]) == pytest.approx(0.5)
    assert sc.max_drawdown([100, 101, 102]) == 0.0

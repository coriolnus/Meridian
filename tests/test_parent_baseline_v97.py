"""test_parent_baseline_v97.py — EBEVEYN TABANININ ÖLÇÜLMESİ (2026-07-26).

`rollback.evaluate_outcomes` bugün `no_parent_score` ile açık: v4'ün ebeveyni v3'ün karnede satırı
da skoru da yok. `meridian/baseline.py` tabanı UYDURMAZ, walk-forward'dan ÖLÇER — ama ölçmek üç ayrı
şeyi birbirine karıştırmaz ve bu dosyanın soruları tam olarak o üç ayrımdır:

  B1 ÖLÇÜM CANLI SÜRÜMÜ OYNATAMAZ — `set_row_fields`, `update_scoreboard`'ın aksine
     `current_version`'a dokunmaz. Dokunsaydı geçmişe dönük bir backfill, karnedeki canlı sürüm
     işaretini sessizce ATAYA çevirirdi ve strategy.yaml ile karne birbirini yalanlardı.
  B2 KARŞILAŞTIRILAMAYAN SAYI YAYINLANMAZ — örneklem yoksa ya da iki tarafın işlem sıklığı
     ayrışıyorsa hüküm "ölçülemez"dir ve `backtest_oos` YAZILMAZ (yazılsaydı `rollback` onu taban
     diye okur ve canlı sürümü uydurma bir deltayla geri alırdı).
  B3 CANLI WORKER KOŞARKEN YAZILMAZ — `set_row_fields` kilitsizdir; iki yazar aynı satıra binerse
     kayıp sessizdir.
  B4 ÜRETİLEN ALAN TÜKETİLİR (yasa 6) — `baseline_verdict` teşhise ve pano satırına ulaşır.
"""
from __future__ import annotations

import datetime as _dt

import pytest
import yaml

from meridian import baseline, config, health, rollback, store, versioning
from meridian import watchdog as wd


@pytest.fixture
def seeded(sandbox_state):
    config.reload_config()
    yield sandbox_state
    config.reload_config()


# OOS penceresi: 2023-07-01 → 2025-12-31 = 914 gün ≈ 2.5024 yıl (frekans paydası).
_W = ("2022-01-01", "2023-07-01", "2025-12-31", "2026-07-10",
      ["2023-07-01", "2024-04-01", "2025-01-01", "2025-12-31"], 10)


def _kur(version: int = 4, parent: int = 3) -> None:
    """strategy.yaml (çocuk canlı) + ebeveynin anlık görüntüsü — ölçümün tek girdisi bu ikisi."""
    config.HISTORY.mkdir(parents=True, exist_ok=True)
    (config.HISTORY / f"v{parent:04d}.yaml").write_text(yaml.safe_dump(
        {"version": parent, "parent": None, "params": config.default_strategy()["params"]}))
    (config.STATE / "strategy.yaml").write_text(yaml.safe_dump(
        {"version": version, "parent": parent, "params": config.default_strategy()["params"]}))


def _canli(n: int, version: int = 4, span_days: int = 365) -> list[dict]:
    """Canlı defter satırları — sıklık ölçümü için ilk/son damga arası TAM `span_days`."""
    base = _dt.date(2025, 7, 1)
    step = span_days / max(n - 1, 1)
    rows = []
    for i in range(n):
        d = (base + _dt.timedelta(days=round(i * step))).isoformat()
        rows.append({"id": f"T{i:03d}", "strategy_version": version, "ts_open": d, "ts_close": d,
                     "r_multiple": 0.1, "pnl_dollars": 100.0, "regime": "chop"})
    return rows


def _yamala(monkeypatch, *, oos_score, folds) -> None:
    """Ölçüm boru hattını sabitle: testte GERÇEK bar yüklenmez, gerçek walk-forward koşmaz."""
    from meridian import backtest, dataset, reflect
    monkeypatch.setattr(dataset, "load", lambda *a, **k: ({}, None))
    monkeypatch.setattr(reflect, "_default_windows", lambda: _W)
    monkeypatch.setattr(backtest, "walk_forward",
                        lambda *a, **k: {"oos_score": oos_score, "oos_folds": folds})
    # Tavan ORTAMDAN okunuyor; operatörün makinesindeki bir değişken testin hükmünü değiştirmesin.
    monkeypatch.setattr(baseline, "FREQ_RATIO_MAX", 2.0)
    monkeypatch.delenv("MERIDIAN_FORCE_BASELINE", raising=False)


# ---------- B1: ölçüm canlı sürüm işaretini oynatamaz ----------
def test_b1_set_row_fields_canli_surum_isaretini_degistirmez(seeded):
    versioning.update_scoreboard(4, live_score=-0.0089)
    assert versioning.scoreboard()["current_version"] == 4

    sb = versioning.set_row_fields(3, backtest_oos=0.12)

    assert sb["current_version"] == 4, "geçmişe dönük yazım canlı sürüm işaretini ataya çevirdi"
    disk = versioning.scoreboard()
    assert disk["current_version"] == 4
    assert disk["versions"]["3"]["backtest_oos"] == 0.12
    assert disk["versions"]["4"]["live_score"] == -0.0089, "kardeş satır bozuldu"


# ---------- B2: karşılaştırılamayan sayı yayınlanmaz ----------
def test_b2a_orneklem_yoksa_hukum_olculemez_ve_skor_yazilmaz(seeded, monkeypatch):
    _kur()
    store.write_jsonl("trades.jsonl", _canli(10))
    _yamala(monkeypatch, oos_score=None, folds=[{"n": 4, "avg_r": 0.1}, {"n": 3, "avg_r": -0.2}])

    out = baseline.measure_parent_baseline(publish=True)

    assert out["verdict"] == "olculemez_orneklem" and out["published"] is True
    row = versioning.scoreboard()["versions"]["3"]
    assert "backtest_oos" not in row, "OOS skoru None'ken karneye bir sayı düştü — uydurma"
    assert row["baseline_verdict"] == "olculemez_orneklem"
    assert row["baseline_source"] == "parent_backfill" and row["baseline_measured_at"]
    assert row["baseline_n_trades"] == 7 and row["baseline_span_days"] == 914


def test_b2b_frekans_ayrisiyorsa_hukum_frekans_ve_skor_yazilmaz(seeded, monkeypatch):
    _kur()
    store.write_jsonl("trades.jsonl", _canli(40, span_days=60))     # ~243 işlem/yıl
    _yamala(monkeypatch, oos_score=0.31, folds=[{"n": 13}, {"n": 12}])   # ~10 işlem/yıl

    out = baseline.measure_parent_baseline(publish=True)

    assert out["verdict"] == "olculemez_frekans"
    assert out["freq_ratio"] > 2.0 and out["oos_score"] == 0.31   # skor ÖLÇÜLDÜ ama yayınlanmadı
    row = versioning.scoreboard()["versions"]["3"]
    assert "backtest_oos" not in row, "frekansı ayrışan iki tarafın deltası beceri değil frekanstır"
    assert row["baseline_verdict"] == "olculemez_frekans" and row["baseline_freq_ratio"] > 2.0


def test_b2c_olculebilir_hukumde_skor_yayinlanir_canli_surum_sabit_kalir(seeded, monkeypatch):
    _kur()
    versioning.update_scoreboard(4, live_score=-0.0089)             # canlı sürüm işareti = 4
    store.write_jsonl("trades.jsonl", _canli(10, span_days=365))    # ~10 işlem/yıl
    _yamala(monkeypatch, oos_score=0.2437, folds=[{"n": 13}, {"n": 12}])   # ~10 işlem/yıl

    out = baseline.measure_parent_baseline(publish=True)

    assert out["verdict"] == "olculebilir" and out["published"] is True
    disk = versioning.scoreboard()
    assert disk["versions"]["3"]["backtest_oos"] == 0.2437
    assert disk["versions"]["3"]["baseline_verdict"] == "olculebilir"
    assert disk["current_version"] == 4, "taban backfill'i canlı sürüm işaretini oynattı"


def test_b2d_publish_bayragi_olmadan_hicbir_sey_yazilmaz(seeded, monkeypatch):
    _kur()
    store.write_jsonl("trades.jsonl", _canli(10, span_days=365))
    _yamala(monkeypatch, oos_score=0.2437, folds=[{"n": 13}, {"n": 12}])

    out = baseline.measure_parent_baseline()

    assert out["verdict"] == "olculebilir" and out["published"] is False
    assert versioning.scoreboard()["versions"] == {}, "ölçmek yayınlamak DEĞİLDİR"


# ---------- B3: canlı worker koşarken yazılmaz ----------
def test_b3_taze_nabizla_yayin_reddedilir_ve_karne_dokunulmaz_kalir(seeded, monkeypatch):
    _kur()
    versioning.update_scoreboard(4, live_score=-0.0089)
    onceki = versioning.scoreboard()
    store.write_jsonl("trades.jsonl", _canli(10, span_days=365))
    _yamala(monkeypatch, oos_score=0.2437, folds=[{"n": 13}, {"n": 12}])
    monkeypatch.setattr(health, "stale", lambda *a, **k: False)      # nabız TAZE → worker koşuyor
    monkeypatch.setattr(health, "heartbeat_age_seconds", lambda: 12.0)

    out = baseline.measure_parent_baseline(publish=True)

    assert out["error"] == "live_worker_running" and out["published"] is False
    assert out["verdict"] == "olculebilir", "ölçüm yine de yapılır; reddedilen YAYIN'dır"
    assert versioning.scoreboard() == onceki, "reddedilen yayın yine de karneye dokunmuş"


# ---------- B4: üretilen alanın tüketicisi var (yasa 6) ----------
def test_b4a_teshis_taban_hukmunu_tasir(seeded):
    versioning.set_row_fields(3, baseline_verdict="olculemez_frekans", baseline_freq_ratio=24.4)

    diag = rollback._no_parent_diagnostics(4, 3)

    assert diag["baseline_verdict"] == "olculemez_frekans"
    assert diag["baseline_freq_ratio"] == 24.4
    assert diag["parent_row_exists"] is True and diag["parent_row_has_score"] is False


def test_b4b_pano_satiri_hukmu_gosterir_temiz_kurulumda_hic_cikmaz(seeded):
    def _satir():
        return next((r for r in wd.parity_report()["rows"] if r["check"] == "learning_loop"), None)

    assert _satir() is None, "kapanmış döngü için kırmızı satır bir kurt masalıdır"

    store.write_json(rollback.OPEN_LOOP_FILE,
                     {"reason": "no_parent_score", "n": 3, "version": 4, "parent": 3,
                      "parent_row_exists": True, "parent_row_has_score": False,
                      "ship_hypothesis_exists": False, "baseline_verdict": "olculemez_orneklem"})
    r = _satir()
    assert r is not None and r["ok"] is False
    assert "baseline_verdict=olculemez_orneklem" in r["detail"]

    # Hüküm HİÇ ölçülmemişse satır yine çıkar ama "ölçülmedi" der — yokluk sessiz kalmaz.
    store.write_json(rollback.OPEN_LOOP_FILE, {"reason": "no_parent_score", "n": 3})
    assert "baseline_verdict=ölçülmedi" in _satir()["detail"]

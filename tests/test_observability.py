"""Batch A tests — data-quality gate (sanitize + validate), secrets TTL rotation, obs alarm tokens."""
import os
import numpy as np
import pandas as pd
import pytest

from meridian.adapters import data
from meridian import secrets, obs


def _bars(n=60):
    return pd.DataFrame({
        "date": pd.bdate_range("2024-01-02", periods=n),
        "open": 100 + np.arange(n) * 0.1, "high": 101 + np.arange(n) * 0.1,
        "low": 99 + np.arange(n) * 0.1, "close": 100.5 + np.arange(n) * 0.1,
        "volume": np.full(n, 1_000_000.0),
    })


def test_validate_passes_clean_bars():
    ok, issues = data.validate_bars(_bars(), "X")
    assert ok and not [i for i in issues if i["severity"] == "hard"]


def test_validate_flags_ohlc_inconsistency_hard():
    df = _bars()
    df.loc[5, "high"] = df.loc[5, "low"] - 1.0     # high < low
    ok, issues = data.validate_bars(df, "X")
    assert not ok and any(i["code"] == "ohlc_inconsistent" for i in issues)


def test_sanitize_repairs_ohlc_dedup_and_then_validates():
    df = _bars()
    df.loc[5, "high"] = df.loc[5, "low"] - 1.0            # inconsistent
    df = pd.concat([df, df.iloc[[10]]], ignore_index=True)  # duplicate date
    clean, rep = data.sanitize_bars(df)
    assert rep.get("clamped_ohlc", 0) >= 1 and rep.get("deduped_dates", 0) >= 1
    ok, issues = data.validate_bars(clean, "X")
    assert ok, [i for i in issues if i["severity"] == "hard"]   # repair makes it tradeable


def test_sanitize_drops_nonpositive():
    df = _bars()
    df.loc[3, "close"] = -1.0
    clean, rep = data.sanitize_bars(df)
    assert rep.get("dropped_rows", 0) >= 1 and (clean[["open", "high", "low", "close"]] > 0).all().all()


def test_split_suspect_is_soft_not_hard():
    """AMBİGÜ büyük hareket SOFT kalır: meşru şok ile ölçek dikişi aynı imzayı verir ve tek satır
    düşürerek çözülmez.

    ADIM KALICI OLMALI (2026-07-31, hayalet-round-2): eskiden yalnız 30. bar yarıya iniyordu, yani
    ertesi bar geri dönüyordu — bu, `unadjusted_row` KARANTİNASININ imzasıdır (v138), hâlâ SERT'tir
    ve o gün yalnız hacim şartı sayesinde 'soft' görünüyordu. Şart gevşeyince (v141) fikstür kendi
    başlığını yalanlar hâle geldi. Ölçmek istediği sınıf GERİ DÖNMEYEN adımdır."""
    df = _bars()
    for i in range(30, len(df)):                       # -50% ADIM KALICI (dikiş değil, hayalet değil)
        for col in ("open", "high", "low", "close"):
            df.loc[i, col] = df.loc[i, col] * 0.5
    ok, issues = data.validate_bars(df, "X")
    assert ok and any(i["code"] == "split_suspect" and i["severity"] == "soft" for i in issues)


def test_secrets_ttl_rotation():
    os.environ["MERIDIAN_TEST_ROT"] = "one"
    secrets.clear_cache()
    assert secrets.get("MERIDIAN_TEST_ROT") == "one"
    os.environ["MERIDIAN_TEST_ROT"] = "two"
    secrets.clear_cache()                    # simulate rotation + explicit invalidation
    assert secrets.get("MERIDIAN_TEST_ROT") == "two"
    del os.environ["MERIDIAN_TEST_ROT"]


def test_obs_alarm_contains_token(tmp_path, monkeypatch):
    from meridian import config
    monkeypatch.setattr(config, "STATE", tmp_path)
    rec = obs.alarm(obs.ALARM_CIRCUIT_BREAKER, "test breaker", day_pnl_pct=-0.03)
    assert obs.ALARM_CIRCUIT_BREAKER in rec["event"] and rec["alarm"] == obs.ALARM_CIRCUIT_BREAKER
    assert any(e["alarm"] == obs.ALARM_CIRCUIT_BREAKER for e in obs.recent(5))

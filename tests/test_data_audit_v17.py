"""test_data_audit_v17.py — adapters.data dönüşümlü bütünlük denetimi (2026-07-21, tur 2).

7. soru ("neyi VARSAYIYOR ama hiçbir yerde İDDİA ETMİYOR?") beş yazısız varsayım çıkardı:
  D1 "geçmiş barlar yalnız corporate-action ile değişir"  → kaynak değişimi de tüm geçmişi yeniden
     yazar (FMP temettü-düzeltmeli ↔ Cboe bölünme-düzeltmeli) ve %25 eşiğinin ALTINDA kalır
  D2 "anahtar varsa kaynak üretiyordur"                    → 429 sessizce yutuluyordu
  D3 "birleştirme satır kaybetmez"                          → kısalmış yazıma engel yoktu
  D4 "CSV yazımı atomiktir"                                 → düz to_csv; havuz işçileri yarım okuyabilir
  D5 "evrenden düşen ticker kayda geçer"                    → yalnız stdout'a print ediliyordu
"""
from __future__ import annotations

import json

import pandas as pd
import pytest

from meridian import config, store
from meridian.adapters import data



@pytest.fixture(autouse=True)
def _sandbox_all(sandbox_state):
    """Bu dosyadaki her test kum havuzunda koşar (2026-07-22, sızıntı bekçisi): FMP yolları her
    çağrıda `fmp_usage.json` (kota/429 telemetrisi) yazıyor ve fikstürsüz testler operatörün CANLI
    kota sayacını eziyordu."""
    yield


def _bars(dates, close):
    return pd.DataFrame({"date": pd.to_datetime(dates), "open": close, "high": [c * 1.01 for c in close],
                         "low": [c * 0.99 for c in close], "close": close,
                         "volume": [1_000_000] * len(dates)})


D = ["2026-07-01", "2026-07-02", "2026-07-06", "2026-07-07"]


@pytest.fixture
def bars_sandbox(sandbox_state, monkeypatch):
    (sandbox_state / "bars").mkdir(exist_ok=True)
    monkeypatch.setattr(config, "BARS", sandbox_state / "bars")
    data._LAST_SOURCE.clear()
    monkeypatch.setattr(data.time, "sleep", lambda *_: None)
    return sandbox_state


def _seed(ticker, df, source=None):
    data._write_bars(df, data._cache_path(ticker))
    if source:
        data._pin_source(ticker, source)


def _rev():
    return int(store.read_json("wf_cache_rev.json", {}).get("rev", 0))


# ---------- D1: kaynak-ölçeği dikişi ----------
def test_d1_foreign_source_may_extend_but_not_rewrite_history(bars_sandbox, monkeypatch):
    """ASIL BULGU: FMP kotası dolunca zincir Cboe'ye düşer, Cboe de TAM geçmiş döndürür ve
    keep='last' bütün geçmişi başka düzeltme ölçeğine çevirirdi — %25 eşiğinin altında olduğu için
    ne sıfırlama ne revizyon bumpı olurdu."""
    _seed("KO", _bars(D, [100.0, 101.0, 102.0, 103.0]), source="fmp")
    # Cboe aynı tarihleri %3 farklı (temettü düzeltmesi yok) + bir yeni gün getiriyor
    cboe = _bars(D + ["2026-07-08"], [103.0, 104.0, 105.1, 106.1, 107.0])
    monkeypatch.setattr(data, "fetch", lambda t, s, e, **k: (data._LAST_SOURCE.__setitem__(t.upper(), "cboe"), cboe)[1])

    out = data.load_bars("KO", "2026-07-01", "2026-07-08", use_cache=False)
    disk = pd.read_csv(data._cache_path("KO"), parse_dates=["date"])
    # geçmiş KORUNDU (fmp ölçeği), yalnız yeni gün eklendi
    assert list(disk["close"])[:4] == [100.0, 101.0, 102.0, 103.0]
    assert str(disk["date"].max().date()) == "2026-07-08" and len(disk) == 5
    assert len(out) == 5
    # OLAY ADI DEĞİŞTİ (2026-07-22): "blocked" her tazelemede basılıyordu (250 sembol × her tur) ve
    # gerçek uyarıları boğuyordu. Artık DURUM bir kez bildirilir ("opened"), tekrarlar sayılır.
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "bar_source_seam_opened"]
    assert ev and ev[-1]["pinned"] == "fmp" and ev[-1]["offered"] == "cboe"
    n0 = len(ev)
    from meridian.adapters import data as _d
    _d._record_seam("KO", "fmp", "cboe", 0)          # aynı durum tekrar
    ev2 = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "bar_source_seam_opened"]
    assert len(ev2) == n0, "aynı dikiş ikinci kez loglandı — susturma çalışmıyor"
    assert _d.seam_report()["by_pair"]["fmp→cboe"] >= 1, "susturulan durum sayılmıyor"


def test_d1b_same_source_rewrite_bumps_wf_rev(bars_sandbox, monkeypatch):
    """Aynı kaynak geçmişi düzeltebilir — ama bu önbelleklenmiş walk-forward'ları geçersiz kılar,
    dolayısıyla revizyon MUTLAKA bumplanmalı (aksi halde kapı elma-armut kıyaslar)."""
    _seed("KO", _bars(D, [100.0, 101.0, 102.0, 103.0]), source="fmp")
    store.write_json("wf_cache_rev.json", {"rev": 5})
    fixed = _bars(D, [100.0, 101.0, 102.5, 103.0])                     # tek bar düzeltildi
    monkeypatch.setattr(data, "fetch", lambda t, s, e, **k: (data._LAST_SOURCE.__setitem__(t.upper(), "fmp"), fixed)[1])

    data.load_bars("KO", "2026-07-01", "2026-07-08", use_cache=False)
    assert _rev() > 5
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "bar_history_rewritten"]
    assert ev and ev[-1]["changed"] == 1


def test_d1c_pure_append_does_not_bump(bars_sandbox, monkeypatch):
    """Salt ekleme MASUMDUR: eski barlar aynı kaldıysa önbellekli walk-forward'lar hâlâ geçerli —
    gereksiz bump her seansta tüm önbelleği çöpe atardı."""
    _seed("KO", _bars(D, [100.0, 101.0, 102.0, 103.0]), source="fmp")
    store.write_json("wf_cache_rev.json", {"rev": 5})
    more = _bars(D + ["2026-07-08"], [100.0, 101.0, 102.0, 103.0, 104.0])
    monkeypatch.setattr(data, "fetch", lambda t, s, e, **k: (data._LAST_SOURCE.__setitem__(t.upper(), "fmp"), more)[1])

    data.load_bars("KO", "2026-07-01", "2026-07-08", use_cache=False)
    assert _rev() == 5


# ---------- D3: monotonluk — geçmiş kısalamaz ----------
def test_d3_row_loss_is_refused(bars_sandbox, monkeypatch):
    """Kaybın GERÇEK yolu: okuma sırasındaki sanitize satır düşürür, sonra o kısaltılmış hâl diske
    geri yazılırdı — yani okuma yolu sessizce kalıcı veri siliyordu. Karşılaştırma diskteki HAM
    satır sayısıyla yapılmalı (sanitize'lı kopyayla değil; onunla birleştirme asla kaybettirmez)."""
    df = _bars(D, [100.0, 101.0, 102.0, 103.0])
    df.loc[1, "close"] = -1.0                                          # bozuk satır: sanitize düşürür
    _seed("KO", df, source="fmp")
    fresh = _bars(D[2:], [102.0, 103.0])
    monkeypatch.setattr(data, "fetch", lambda t, s, e, **k: (data._LAST_SOURCE.__setitem__(t.upper(), "fmp"), fresh)[1])

    out = data.load_bars("KO", "2026-07-01", "2026-07-08", use_cache=False)
    disk = pd.read_csv(data._cache_path("KO"), parse_dates=["date"])
    assert len(disk) == 4                                              # disk KORUNDU (bozuk satır dahil)
    assert len(out) == 3                                               # bellekteki kopya onarılmış
    ev = {e.get("event") for e in store.read_jsonl("events.jsonl")}
    assert "bar_row_loss_refused" in ev and "bar_cache_repaired" in ev


def test_d3b_corporate_action_reset_may_shrink(bars_sandbox, monkeypatch):
    """Bilinçli istisna: bölünme sonrası tam yeniden çekim daha kısa bir seri getirebilir; bu KAYIP
    değil, ölçek sıfırlamasıdır — ve revizyonu zaten bumplar."""
    _seed("KO", _bars(D, [100.0, 101.0, 102.0, 103.0]), source="fmp")
    store.write_json("wf_cache_rev.json", {"rev": 5})
    split = _bars(D[:3], [25.0, 25.3, 25.5])                           # 4:1 bölünme, %25 eşiğini aşar
    monkeypatch.setattr(data, "fetch", lambda t, s, e, **k: (data._LAST_SOURCE.__setitem__(t.upper(), "fmp"), split)[1])

    data.load_bars("KO", "2026-07-01", "2026-07-08", use_cache=False)
    disk = pd.read_csv(data._cache_path("KO"), parse_dates=["date"])
    assert len(disk) == 3 and float(disk["close"].iloc[0]) == 25.0
    assert _rev() > 5


# ---------- D4: atomik yazım ----------
def test_d4_write_is_atomic(bars_sandbox, monkeypatch):
    """Havuz işçileri (dataset.load_cached) aynı CSV'yi eş zamanlı OKUYOR: yarım yazılmış dosya
    sessizce kırpılmış bar demektir. Yazım çökerse dosya ESKİ hâlinde kalmalı, yarım değil."""
    cp = data._cache_path("KO")
    _seed("KO", _bars(D, [100.0, 101.0, 102.0, 103.0]), source="fmp")
    before = cp.read_text()

    import meridian.adapters.data as M
    real = pd.DataFrame.to_csv

    def _boom(self, *a, **k):
        raise OSError("disk full")

    monkeypatch.setattr(pd.DataFrame, "to_csv", _boom)
    with pytest.raises(OSError):
        M._write_bars(_bars(D, [1.0, 2.0, 3.0, 4.0]), cp)
    monkeypatch.setattr(pd.DataFrame, "to_csv", real)
    assert cp.read_text() == before                                    # yarım dosya YOK
    assert not list(cp.parent.glob("*.tmp"))                           # geçici dosya temizlendi


def test_d4b_no_raw_to_csv_left_in_load_bars():
    import inspect
    src = inspect.getsource(data.load_bars)
    assert "_write_bars(" in src and ".to_csv(" not in src


# ---------- D5: korunum — evren sessizce küçülemez ----------
def test_d5_universe_shrink_is_recorded(bars_sandbox, monkeypatch):
    monkeypatch.setattr(data, "load_bars", lambda t, s, e, **k: pd.DataFrame())
    data.load_many(["AAA", "BBB"], "2026-07-01", "2026-07-08")
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "universe_shrunk"]
    assert ev and ev[-1]["loaded"] == 0 and ev[-1]["wanted"] == 2


# ---------- D2: kaynak üretkenliği ----------
def test_d2_all_sources_empty_is_recorded(bars_sandbox, monkeypatch):
    from meridian.adapters import fmp
    monkeypatch.setattr(fmp, "available", lambda: False)
    monkeypatch.setattr(data, "_fetch_cboe", lambda *a, **k: pd.DataFrame())
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda *a, **k: pd.DataFrame())
    assert data.fetch("KO", "2026-07-01", "2026-07-08").empty
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "bar_sources_all_empty"]
    assert ev and ev[-1]["ticker"] == "KO"


def test_d2b_fmp_available_is_not_health(monkeypatch, sandbox_state):
    """'anahtar var' ≠ 'veri üretiyor'. 429 eskiden tamamen yutuluyordu."""
    from meridian.adapters import fmp
    import httpx

    class _R:
        status_code = 429

        def raise_for_status(self):
            raise httpx.HTTPStatusError("429", request=None, response=None)

        def json(self): return {}

    monkeypatch.setattr(fmp.secrets, "get", lambda n, *a, **k: "SECRET-KEY-123")
    monkeypatch.setattr(fmp.secrets, "present", lambda n: True)
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _R())
    assert fmp.available() is True
    assert fmp.historical_eod("KO") == []                 # çağıran hâlâ boş liste görür
    h = fmp.health()
    assert h["ok"] is False and h["last_status"] == 429
    assert fmp.quota_blocked() is True                   # toplu tazeleme 250 boş istek daha atmaz
    # `blocked_until` sıfırlaması SİLİNDİ (2026-07-26): alan üretimden kaldırıldı; bloğun sahibi
    # `_KEY_BLOCKED` ve onu conftest `_clear_module_caches` her testte temizliyor.


def test_d2c_api_key_never_appears_in_error_text(monkeypatch, sandbox_state):
    """httpx'in hata metni TAM URL'i (dolayısıyla apikey'i) taşır — bir gün loglanırsa anahtar diske
    düşer. Kaynağında maskelenmeli."""
    from meridian.adapters import fmp
    import httpx
    KEY = "SUPERSECRETKEY"
    monkeypatch.setattr(fmp.secrets, "get", lambda n, *a, **k: KEY)
    monkeypatch.setattr(fmp.secrets, "present", lambda n: True)

    def _boom(*a, **k):
        raise httpx.ConnectError(f"failed for url https://x/stable/quote?apikey={KEY}")

    monkeypatch.setattr(httpx, "get", _boom)
    with pytest.raises(Exception) as ei:
        fmp._get("quote", {"symbol": "KO"})
    assert KEY not in str(ei.value) and "***" in str(ei.value)
    assert KEY not in json.dumps(fmp.health())


# ---------- kaynak sabitlemesi kalıcı ----------
def test_source_pin_persists(bars_sandbox, monkeypatch):
    fresh = _bars(D, [100.0, 101.0, 102.0, 103.0])
    monkeypatch.setattr(data, "fetch", lambda t, s, e, **k: (data._LAST_SOURCE.__setitem__(t.upper(), "cboe"), fresh)[1])
    data.load_bars("ZZ", "2026-07-01", "2026-07-08", use_cache=False)
    assert data._bar_source("ZZ") == "cboe"
    assert store.read_json(data.SOURCE_FILE, {})["ZZ"]["source"] == "cboe"

"""test_cf_backfill_v14.py — karşı-olgusal motorun TARİH bootstrap'ı (2026-07-21).

cf.collect/advance yalnız canlı daily_cycle'da koşuyordu → 2022→bugün replay'i 0 cf kanıtı üretti.
cf_backfill, P2+P3'ü BİREBİR CANLI FONKSİYONLARLA tekrar koşarak defteri tarihten doldurur.
Değişmezler: (1) SIFIR YETKİ — yalnız cf defterine yazar, hiçbir karar/kapı/portföy dosyasına değil;
(2) canlı fonksiyonları kullanır (scan_all/classify_gate/cf.collect/advance) — algoritma tek yerde."""
import inspect

import pandas as pd

from meridian import cf_backfill, store, config


def test_backfill_is_zero_authority_and_reuses_live_functions():
    """Kaynak-denetim: backfill yalnız cf motorunu + canlı P2/P3 fonksiyonlarını kullanır; portföy/
    trades/strateji dosyalarına ASLA yazmaz (yalnız cf defterini doldurur)."""
    src = inspect.getsource(cf_backfill)
    for tok in ("strat.scan_all", "guard.classify_gate", "cf.collect", "cf.advance",
                "regime_mod.build_regime_json", "config.resolve_params"):
        assert tok in src, f"canlı fonksiyon kullanılmıyor: {tok}"
    # yazma yalnız cf motoru üzerinden (collect/advance) olmalı — doğrudan portföy/trades yazımı yok
    for forbidden in ('write_json("portfolio', 'write_jsonl("trades', 'write_json("strategy',
                      'write_json("scoreboard'):
        assert forbidden not in src, f"backfill yasak dosyaya yazıyor: {forbidden}"


def test_plans_for_session_shape_and_gate(sandbox_state, monkeypatch):
    """_plans_for_session: sentetik barlarda çökmeden (plans, armed_ids, dormant, near_miss, regime)
    beşlisini döner; üretilen her planda gate_verdict bulunur (kapıdan geçmiş)."""
    import shutil
    from pathlib import Path
    from tests.conftest import make_bars
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml", "strategy.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.goal.cache_clear(); config.bounds.cache_clear()

    # küçük sentetik evren: SPY (endeks) + 3 isim, biri temiz kırılımlı
    from meridian.adapters import data as _data
    monkeypatch.setattr(_data, "REPLAY_UNIVERSE", ["SPY", "AAA", "BBB", "CCC"])
    monkeypatch.setattr(_data, "validate_bars", lambda df, t: (True, []))   # veri kapısı başka yerde test edilir
    # monkeypatch.setitem: SECTORS ÜRETİM sözlüğüdür ve `loop.SECTORS` ile AYNI nesnedir.
    # `setdefault` ile yazmak onu oturum boyunca kalıcı olarak kirletiyordu (2026-07-22, suite'i
    # ters sırada koşturunca yakalandı: test_b3_sector_map_covers_the_universe_exactly "evrende
    # olmayan sembol haritada: AAA, BBB, CCC" diye düştü). Alfabetik sırada zehirleme SONRA geldiği
    # için görünmüyordu — testler arası sızıntının klasik hâli.
    from meridian.backtest import SECTORS
    for t in ("AAA", "BBB", "CCC"):
        monkeypatch.setitem(SECTORS, t, "tech")
    per = {"SPY": make_bars(n=340, seed=1, trend=0.0004).set_index("date").sort_index(),
           "AAA": make_bars(n=340, seed=2, trend=0.0006, breakout_at=330).set_index("date").sort_index(),
           "BBB": make_bars(n=340, seed=3, trend=0.0003).set_index("date").sort_index(),
           "CCC": make_bars(n=340, seed=4, trend=0.0005, breakout_at=332).set_index("date").sort_index()}
    idx = per["SPY"]
    strat_cfg = config.load_strategy()
    d = idx.index[-1]
    plans, armed, dormant, nmiss, rj = cf_backfill._plans_for_session(
        d, str(d.date()), per, idx, strat_cfg["params"], strat_cfg.get("params_by_regime"),
        config.goal(), 1)
    assert rj is not None and isinstance(plans, list)
    for p in plans:
        assert p.get("gate_verdict") in ("GO", "REVIEW", "NO_GO")     # her plan kapıdan geçmiş
        assert "id" in p and "entry_trigger" in p and "stop" in p
    assert isinstance(armed, set) and isinstance(nmiss, list)


def test_backfill_only_touches_cf_files(sandbox_state, monkeypatch):
    """Çalıştırma güvenliği: run() yalnız cf_open.json + counterfactuals.jsonl'a dokunur; portföy/
    trades sandbox'ta oluşmaz (backfill canlı defteri kirletemez)."""
    import shutil
    from pathlib import Path
    from tests.conftest import make_bars
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml", "strategy.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.goal.cache_clear(); config.bounds.cache_clear()
    from meridian.adapters import data as _data
    monkeypatch.setattr(_data, "REPLAY_UNIVERSE", ["SPY", "AAA"])
    monkeypatch.setattr(_data, "validate_bars", lambda df, t: (True, []))
    from meridian.backtest import SECTORS
    monkeypatch.setitem(SECTORS, "AAA", "tech")   # kalıcı kirletme yok (bkz. yukarıdaki gerekçe)
    # sentetik CSV'leri sandbox bars'a yaz (run() doğrudan CSV okur)
    for t, seed, bo in (("SPY", 1, None), ("AAA", 2, 330)):
        make_bars(n=340, seed=seed, breakout_at=bo).to_csv(config.BARS / f"{t.lower()}.csv", index=False)
    start = "2022-01-03"
    out = cf_backfill.run(start=start, end=None, progress_every=0)
    assert out["sessions"] > 0                                        # seanslar işlendi
    # portföy/trades'e DOKUNULMADI (backfill yalnız cf)
    assert store.read_json("portfolio.json", None) is None
    assert store.read_jsonl("trades.jsonl") == []

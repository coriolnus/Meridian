"""replay_kol.py — EDG-2026-025 bacak (b): TEK kol tam-replay koşucusu. argv[1] = kol adı.

KOLLAR:
  taban       : bugünkü motor + canlı parametreler (strategy.yaml v-canlı) + mevcut ARMED_SETUPS
                (breakout_vcp, pullback, exhaustion_hammer — strategy.py:1009). Karşılaştırma tabanı.
  taban_pk    : taban'ın BİREBİR ikizi — determinizm pozitif kontrolü (kill#3 şasi doğrulaması;
                karne_tazeleme_2026-08-03 `tam_guncel_pk` emsali).
  mb_silahli  : TEK FARK — params["entry.armed_extra"] = ["momentum_burst"]. Bu, motorun KENDİ
                ölçüm kanalıdır (arming.py:12-13 + arming.py:317; strategy.py:1046-1049
                `scan_entry`: `for setup in ARMED_SETUPS + extra`): global ARMED_SETUPS'a ve repo
                koduna DOKUNULMAZ; monkeypatch bile gerekmez — kanal parametre üzerinden akar.
                Tuple sırası gereği momentum_burst en DÜŞÜK önceliklidir (canlı yasa birebir).

SALT-ÖLÇÜM SÖZLEŞMESİ (karne_tazeleme_2026-08-03/kosum.py emsali):
  * MERIDIAN_ROOT sandbox'a yönlendirilir → tüm state okuma/yazmaları (obs olayları dahil)
    sandbox/state/ altında kalır; GERÇEK state/'e tek bayt yazılmaz.
  * Motor sandbox'a KOPYALANDI (kod_damgasi.json bayt-eşitlik damgası) — paralel ajan repo'yu
    değiştirse bile üç kol AYNI donmuş kodla koşar.
  * Barlar canlı önbellekten SEMBOLİK BAĞ ile SALT-OKUNUR (dataset.load_cached ağa çıkmaz,
    CSV yeniden yazmaz — dataset.py:274-283).
  * YASAKLI MODÜL TRİPWIRE: loop/counterfactual/cf_backfill/hermes İTHAL EDİLMEZ; koşum sonunda
    sys.modules üzerinde DOĞRULANIR (statik iddia değil, çalışma-zamanı kanıtı).

Pencere: kart AYNEN — 2022-01 → 2026-07 (START/END aşağıda; takvim SPY endeks barlarından).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import sys

BURASI = pathlib.Path(__file__).resolve().parent
SANDBOX = BURASI / "sandbox"
KOL = sys.argv[1]
assert KOL in ("taban", "taban_pk", "mb_silahli"), f"bilinmeyen kol: {KOL}"

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ["MERIDIAN_ROOT"] = str(SANDBOX)          # config.py:10 — ROOT env'den
sys.path.insert(0, str(SANDBOX))

import numpy as np                        # noqa: E402
import pandas as pd                       # noqa: E402  (motor bağımlılığı; burada da kullanılıyor)
import yaml                               # noqa: E402

import meridian                           # noqa: E402
from meridian import config               # noqa: E402

# MOTOR SANDBOX'TAN MI? (karne kosum.py'nin MOTOR assert'i birebir)
assert str(pathlib.Path(meridian.__file__).resolve()).startswith(str(SANDBOX)), \
    f"YANLIŞ MOTOR: {meridian.__file__}"
assert config.STATE == SANDBOX / "state", f"STATE sandbox'ta değil: {config.STATE}"

from meridian import backtest, dataset    # noqa: E402  (brief: backtest+strategy OKU/İTHAL serbest)
from meridian import strategy as strat    # noqa: E402

START, END = "2022-01-01", "2026-07-31"   # kart: 2022-01 → 2026-07

# İşlem satırı alan kümesi — karne_tazeleme_2026-08-03/kosum.py ISLEM_ALAN ile BİREBİR
ISLEM_ALAN = ("ticker", "ts_open", "ts_close", "entry", "exit", "r_multiple", "size_r",
              "exit_reason", "setup", "regime_at_plan", "pnl_dollars", "pnl_pct", "costs",
              "bars_held", "qty", "plan_id", "id", "score", "regime", "mfe_r", "mae_r",
              "scaled_out", "strategy_version")


def trade_digest(trades: list) -> str:
    """karne_tazeleme_2026-08-03/kosum.py trade_digest ile BİREBİR AYNI TANIM (kıyas meşruiyeti)."""
    rows = []
    for t in sorted(trades, key=lambda x: (str(x.get("ts_open")), str(x.get("ticker")))):
        rows.append("|".join(str(t.get(k)) for k in
                             ("ticker", "ts_open", "ts_close", "entry", "exit", "r_multiple",
                              "size_r", "exit_reason", "setup")))
    return hashlib.sha256("\n".join(rows).encode()).hexdigest()


def main() -> None:
    st = yaml.safe_load((SANDBOX / "state" / "strategy.yaml").read_text())
    params = dict(st["params"])
    by_regime = st.get("params_by_regime") or None
    sv = st.get("version")
    assert isinstance(sv, int), f"strategy.yaml version okunamadı: {sv!r}"
    if KOL == "mb_silahli":
        # arming.py:317 kanalı — cand_params = {**params, "entry.armed_extra": [setup]}
        params["entry.armed_extra"] = ["momentum_burst"]
    goal = config.goal()

    t0 = dt.datetime.now()
    bars, index = dataset.load_cached()
    print(f"[{KOL}] barlar: {len(bars)} sembol, endeks {len(index)} satır, sv={sv}", flush=True)
    res = backtest.replay(params, bars, index, goal, START, END,
                          strategy_version=sv, params_by_regime=by_regime)
    sure = round((dt.datetime.now() - t0).total_seconds(), 1)

    # YASAKLI MODÜL TRIPWIRE (çalışma-zamanı kanıtı)
    yasak = [m for m in ("meridian.loop", "meridian.counterfactual",
                         "meridian.cf_backfill", "meridian.hermes") if m in sys.modules]
    assert not yasak, f"YASAKLI modül ithal edildi: {yasak}"

    trades = res.trades or []
    eqs = res.equity or []
    out = {
        "kol": KOL,
        "motor": str(pathlib.Path(meridian.__file__).resolve().parent),
        "armed_setups_repo": list(strat.ARMED_SETUPS),
        "armed_extra": params.get("entry.armed_extra"),
        "strategy_version": sv,
        "strategy_version_kaynagi": "sandbox/state/strategy.yaml:version (canlı kopya)",
        "params": {k: v for k, v in params.items()},
        "params_by_regime": by_regime,
        "goal_limits": (goal or {}).get("limits"),
        "goal_execution_v2": (goal or {}).get("execution_v2"),
        "pencere": {"start": START, "end": END},
        "calendar_ilk": (str(eqs[0][0]) if eqs else None),
        "calendar_son": (str(eqs[-1][0]) if eqs else None),
        "n_sembol": len(bars), "n_endeks_satir": int(len(index)),
        "sure_sn": sure,
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "n_trades": len(trades),
        "n_plans": len(res.plan_log or []),
        "entry_rejects": res.entry_rejects,
        "earnings_gate": res.earnings_gate,
        "trade_digest": trade_digest(trades),
        "equity_digest": hashlib.sha256("\n".join(f"{d}|{v}" for d, v in eqs).encode()).hexdigest(),
        "yasakli_modul_tripwire": "temiz (loop/counterfactual/cf_backfill/hermes sys.modules'ta yok)",
        "trades": [{k: t.get(k) for k in ISLEM_ALAN} for t in trades],
        "equity": [[str(d), float(v)] for d, v in eqs],
    }
    hedef = BURASI / f"kol_{KOL}.json"
    hedef.write_text(json.dumps(out, ensure_ascii=False))
    print(f"[{KOL}] bitti: {len(trades)} işlem, {sure}s → {hedef.name}", flush=True)


if __name__ == "__main__":
    main()

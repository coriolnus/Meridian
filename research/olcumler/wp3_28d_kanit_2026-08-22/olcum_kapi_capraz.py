"""WP3/28d KART-KANITI · kapı çapraz-doğrulama SAYIMI (analiz; kartı Rol-1 yazacak).

ÜÇ SORU (hepsi sayım, hüküm yok):
  (1) ÇAPRAZ-DOĞRULAMA: inc_cache'teki chop-etiketli işlemlerin plan günü (ts_open'dan önceki
      işlem günü) benim gün-serimde de chop mu? (regime_at_plan, planın kurulduğu KAPANIŞIN
      rejimi — backtest.py:373'te gün d kapanışında rj üretilir, giriş ertesi gün.)
      Tutuyorsa: yerel yeniden-hesap kapının dünyasıyla AYNI — gün-vs-işlem ayrımı gerçek.
  (2) CHOP GÜNLERİNDE BÜTÇE: build_regime_json (dd cezası dahil) chop günlerinde
      exposure_budget_pct kaç? budget=0 chop günü girişe KAPALIdır (backtest.py:382 regime_ok).
      → "chop günü vardı ama işlem yoktu"nun mekanik payı.
  (3) KAPININ DİLİM SAYILARI (yerel inc_cache): eval_regime başına search/confirm dilim
      büyüklükleri + confirm tabanının aritmetiği (oos_pipeline.py:79):
      _floor = max(10, int(0.7·min_sample)); min_sample=30 → 21; 10 ancak min_sample≤14 iken bağlar.

Çıktı: sonuc_kapi_capraz.json. UYDURMA YASAĞI: ölçülemeyen null + neden.
"""
from __future__ import annotations
import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from meridian import regime as regime_mod          # noqa: E402

FETCH_START = "2021-01-01"
OUT_DIR = Path(__file__).resolve().parent
MIN_EXP_DEFAULT = 40   # regime.py build_regime_json: params.get("regime.min_exposure_score", 40)


def main() -> None:
    gun = pd.read_csv(OUT_DIR / "gunluk_rejim.csv")
    gun_map = dict(zip(gun["date"], gun["regime"]))
    tarihler = list(gun["date"])

    spy = pd.read_csv(REPO / "state/bars/spy.csv", parse_dates=["date"])
    spy = spy[spy["date"] >= FETCH_START].reset_index(drop=True)

    # strategy.yaml'daki fiili min_exposure_score (varsa)
    try:
        import yaml
        strat = yaml.safe_load((REPO / "state/strategy.yaml").read_text())
        min_exp = int((strat.get("params") or {}).get("regime.min_exposure_score", MIN_EXP_DEFAULT))
        params = strat.get("params") or {}
    except Exception as e:                          # ölçülemedi → varsayılan + beyan
        min_exp, params = MIN_EXP_DEFAULT, {}
        strat_hata = f"{type(e).__name__}: {e}"
    else:
        strat_hata = None

    # ---- (1) çapraz-doğrulama: inc_cache chop işlemleri ------------------------------------------
    inc = json.load(open(REPO / "state/inc_cache.json"))
    ents = list(inc["entries"].values())
    capraz = []
    for v in ents[:1]:  # global (eval_regime=None) girdi yeter — işlem listesi üçünde aynı
        for tr in (v.get("_trades_search") or []) + (v.get("_trades_confirm") or []):
            if tr.get("regime") != "chop":
                continue
            ts_open = str(tr.get("ts_open"))[:10]
            oncekiler = [d for d in tarihler if d < ts_open]
            plan_gunu = oncekiler[-1] if oncekiler else None
            capraz.append({"ticker": tr.get("ticker"), "ts_open": ts_open,
                           "plan_gunu": plan_gunu,
                           "gun_serisi_etiketi": gun_map.get(plan_gunu),
                           "tutarli": gun_map.get(plan_gunu) == "chop"})

    # ---- (2) chop günlerinde bütçe (dd cezası dahil, üretim fonksiyonuyla) -----------------------
    chop_gunleri = [d for d, r in gun_map.items() if r == "chop"]
    spy_idx = spy.set_index("date")
    butce = []
    for d in chop_gunleri:
        sl = spy_idx.loc[:d].reset_index()
        rj = regime_mod.build_regime_json(sl, params, d)
        butce.append({"date": d, "budget": rj["exposure_budget_pct"], "dd": rj["distribution_days"],
                      "score": rj["exposure_score"]})
    bdf = pd.DataFrame(butce)
    acik = bdf[bdf["budget"] > 0]
    kapali = bdf[bdf["budget"] == 0]
    claim = bdf[bdf["date"] >= "2025-07-01"]

    # ---- (3) kapının dilim sayıları + taban aritmetiği -------------------------------------------
    dilimler = []
    for v in ents:
        cs = Counter(str(t.get("regime")) for t in v.get("_trades_search") or [])
        cc = Counter(str(t.get("regime")) for t in v.get("_trades_confirm") or [])
        dilimler.append({"eval_regime": v.get("eval_regime"), "oos_split": v.get("oos_split"),
                         "n_graded": v.get("n_trades_graded"),
                         "search": dict(cs), "confirm": dict(cc)})
    goal_min_sample = 30  # state/goal.yaml:33 (okundu; sabitleme değil kayıt)
    taban = {
        "kod_satiri": "meridian/oos_pipeline.py:79  _floor = max(10, int(0.7 * min_sample))",
        "ikinci_kopya": "meridian/reflect.py:580  floor = max(10, int(min_sample * 0.7)) (arama dilimi)",
        "bos_dilim_davranisi": ("meridian/oos_pipeline.py:83-86: _n < _floor → GateResult(False, "
                                "law='legacy', why='teyit dilimi ince (N < F işlem) — ship yetkisi "
                                "bu kanıtla verilemez') — FAIL-CLOSED; ayrıca reflect.py:628-637 "
                                "dilim VAR + ölçüm YOK → law='olculemedi', magnitude_ok=False (28f)"),
        "min_sample_guncel": goal_min_sample,
        "floor_guncel": max(10, int(0.7 * goal_min_sample)),
        "on_bagladigi_bolge": "max'ın 10 kolu ancak min_sample<=14 iken bağlar (int(0.7*14)=9); "
                              "min_sample>=15'te bağlayıcı kol 0.7·min_sample'dır",
        "floor_tablosu": {ms: max(10, int(0.7 * ms)) for ms in (5, 10, 14, 15, 20, 30)},
    }

    sonuc = {
        "kart_kaniti": "WP3/28d — kapı çapraz-doğrulama sayımı (hüküm yok)",
        "olcum_ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "capraz_dogrulama_chop_islemleri": {
            "aciklama": "inc_cache global girdisindeki chop-etiketli işlemler vs yerel gün-serisi "
                        "(plan günü = ts_open'dan önceki işlem günü)",
            "islemler": capraz,
            "tutarli_sayisi": sum(1 for c in capraz if c["tutarli"]),
            "toplam": len(capraz),
        },
        "chop_gunlerinde_butce": {
            "aciklama": "build_regime_json (üretim) ile; budget=0 → regime_ok=False → giriş yok "
                        "(backtest.py:382, loop.py:1597)",
            "params_kaynagi": ("state/strategy.yaml params" if strat_hata is None
                               else f"OKUNAMADI ({strat_hata}) → varsayılan min_exp={MIN_EXP_DEFAULT}"),
            "min_exposure_score": min_exp,
            "toplam_chop_gunu": int(len(bdf)),
            "girise_acik_chop_gunu(budget>0)": int(len(acik)),
            "girise_kapali_chop_gunu(budget=0)": int(len(kapali)),
            "kapali_gunlerin_dd_dagilimi": dict(Counter(kapali["dd"])) if len(kapali) else {},
            "claim_sonrasi(2025-07-01+)": {
                "chop_gunu": int(len(claim)),
                "girise_acik": int((claim["budget"] > 0).sum()),
                "girise_kapali": int((claim["budget"] == 0).sum()),
            },
        },
        "kapi_dilim_sayilari_yerel_inc_cache": dilimler,
        "confirm_tabani": taban,
    }
    (OUT_DIR / "sonuc_kapi_capraz.json").write_text(json.dumps(sonuc, indent=2, ensure_ascii=False))
    print(json.dumps({k: sonuc[k] for k in ("capraz_dogrulama_chop_islemleri",
                                            "chop_gunlerinde_butce")}, ensure_ascii=False))


if __name__ == "__main__":
    main()

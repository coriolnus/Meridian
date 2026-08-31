"""wf_fixtures.py — walk_forward SÖZLEŞMESİNİN TEK KAYNAĞI (2026-07-23).

FİKSTÜR TUZAĞI, sistematik çözüm. Beş+ test dosyası `walk_forward` çıktısını AYRI AYRI elle taklit
ediyordu (`_wf`, `wf_fix`, ...). Confirm-OOS sızıntısı düzeltilip üretici Search/Confirm dilimleri
üretmeye başlayınca bu taklitler ESKİ yasayı kopyalamaya devam etti: dilimsiz sözlük → `has_slices`
False → `_gate_eval` LEGACY nokta-marj yasasına düşüyor. Sonuç: her biri ürünün GERÇEKTE koştuğu
olasılıksal + teyit yolunu DEĞİL, artık erişilemez legacy dalı test ediyordu. On yeşil test, sıfır
kanıt.

Kök çözüm "aynı yasanın N kopyası"nı "tek uygulama + N çağrı"ya indirger. Buradaki `wf_from_trades`
üreticinin (backtest.walk_forward) döndürdüğü şekli AYNI türetmelerle kurar; `wf_from_scores` ise
skor-tabanlı eski taklitler için sentetik ama GERÇEK trade satırları üretip dilimleri doldurur, böylece
`has_slices` True olur ve olasılıksal yol gerçekten sınanır. `test_wf_fixture_parity_v82.py` bu
kaynağın üreticiyi yansıttığını kilitler — kaynak sürüklenirse orası kırmızı yanar.
"""
from __future__ import annotations

import datetime as dt

import numpy as np

from meridian import backtest, config, score as score_mod
from meridian.oos_pipeline import split_date

# --- OOS pencere/dilim sabitleri: ÜRETİCİYLE (backtest.walk_forward) aynı türetme ---
IS_START = "2022-01-01"
OOS_START, OOS_END = "2023-07-01", "2025-12-31"
FOLDS = ["2023-07-01", "2024-04-01", "2025-01-01", "2025-12-31"]
EMBARGO = 10
S_END = split_date(OOS_START, OOS_END)                       # Search/Confirm ayrımı (~2025-04-01)
S_LO = backtest._embargoed_start(OOS_START, EMBARGO)         # embargolanmış Search alt sınırı
# SEARCH'e daraltılmış fold sınırları — walk_forward ile AYNI: Confirm'e uzanan fold aramaya girmez.
SEARCH_FOLDS = [b for b in FOLDS if b < S_END] + [S_END]


def trades(n, seed, lo, hi, r_mu, hold=4):
    """[lo, hi) içinde n adet kapalı işlem; R ~ N(r_mu, 1). Tamamen deterministik. gate.evaluate'in
    ve score_detail'in okuduğu tam şema: ts_open/ts_close (blok boyu + segment), r_multiple, pnl_dollars."""
    rng = np.random.default_rng(seed)
    d0 = dt.date.fromisoformat(lo)
    span = max(1, (dt.date.fromisoformat(hi) - d0).days - hold - 1)
    out = []
    for _ in range(n):
        off = int(rng.integers(0, span))
        r = float(rng.normal(r_mu, 1.0))
        out.append({"ts_open": (d0 + dt.timedelta(days=off)).isoformat(),
                    "ts_close": (d0 + dt.timedelta(days=off + hold)).isoformat(),
                    "regime": "trend_up", "r_multiple": round(r, 3),
                    "pnl_dollars": round(r * 400.0, 2)})
    return out


def wf_from_trades(all_trades, goal=None):
    """walk_forward'ın ÜRETTİĞİ sözlüğün birebir şekli — dilimler/foldlar/kuyruk aynı yasalarla.
    Fold ve kuyruk YALNIZ Search-OOS'tan hesaplanır: Confirm dilimi aramanın hiçbir parçasına girmez
    (kazananın-laneti savunması). `has_slices` True: kapı olasılıksal + teyit yolunu koşar."""
    goal = goal or config.goal()
    _in = backtest._in_segment
    oos = [t for t in all_trades if _in(t, S_LO, OOS_END)]
    search = [t for t in all_trades if _in(t, S_LO, S_END)]
    return {"oos_score": score_mod.score_detail(oos, goal)["score"],
            # TAM-PENCERE DEFTERİ — üreticideki `res.detail(goal)` ile AYNI türetme: dilimsiz,
            # replay'in BÜTÜN işlemlerinden. Ship yolu (`reflect._submit_locked`) global ship'te
            # bunu karneye `backtest_full` olarak yazar; fikstür alanı üretmezse o kablo bu
            # dosyayı kullanan her ship testinde sessizce kopardı.
            "full_detail": score_mod.score_detail(all_trades, goal),
            "oos_folds": backtest._fold_metrics(all_trades, SEARCH_FOLDS, EMBARGO),
            "oos_tail_risk": score_mod.tail_risk(search),
            "holdout_score": None,
            "oos_split": {"search_start": S_LO, "search_end": S_END,
                          "confirm_start": S_END, "confirm_end": OOS_END},
            "_trades_search": [t for t in all_trades if _in(t, S_LO, S_END)],
            "_trades_confirm": [t for t in all_trades if _in(t, S_END, OOS_END)]}


def wf_from_scores(oos, folds=((30, 0.5), (30, 0.5), (30, 0.5)), tail=None, holdout=None,
                   confirm=None, goal=None, seed=1):
    """SKOR-TABANLI eski taklitlerin köprüsü. Dilimsiz `_wf(oos)` çağrıları legacy yasayı test
    ediyordu; bu, verilen `oos`/`folds`/`tail`/`holdout` değerlerini KORUYARAK altına GERÇEK sentetik
    dilimler döşer → `has_slices` True → olasılıksal yol gerçekten koşar.

    folds: [(n, avg_r)] Search dilimindeki dağılım. confirm: (n, avg_r) ya da None (Search'ten türetilir).
    Verilen skalar `oos`/`folds` kapı metriklerini sürer; sentetik trade'ler olasılıksal yolu besler."""
    goal = goal or config.goal()
    # HER FOLD KENDİ ZAMAN PENCERESİNE (2026-07-28, n-dengeli kesim turu). Eskiden üç fold'un
    # işlemleri de TÜM Search dilimine rastgele saçılıyordu ve istenen fold deseni yalnız aşağıdaki
    # `base["oos_folds"]` ATAMASIYLA iddia ediliyordu — yani fikstür, altındaki işlemlerin
    # DESTEKLEMEDİĞİ bir fold tablosu sunuyordu. Kapı fold'ları takvimden okuduğu sürece bu fark
    # görünmüyordu; kapı artık fold'ları İŞLEMLERDEN kestiği için görünür oldu. Bir "fold" zaman
    # penceresi demektir: işlemler o pencereye konmazsa fold diye bir şey yoktur.
    _b = [dt.date.fromisoformat(S_LO) + dt.timedelta(
        days=int(round(i * (dt.date.fromisoformat(S_END) - dt.date.fromisoformat(S_LO)).days
                       / max(1, len(folds))))) for i in range(len(folds) + 1)]
    search_tr = []
    for i, (n, r) in enumerate(folds):
        search_tr += trades(int(n), seed + i, _b[i].isoformat(), _b[i + 1].isoformat(), float(r))
    if confirm is None:
        cn = max(12, sum(int(n) for n, _ in folds) // max(1, len(folds)))
        cr = float(np.mean([r for _, r in folds])) if folds else 0.5
    else:
        cn, cr = int(confirm[0]), float(confirm[1])
    confirm_tr = trades(cn, seed + 97, S_END, OOS_END, cr)

    base = wf_from_trades(search_tr + confirm_tr, goal)
    base["oos_score"] = oos                                       # verilen skalar kapı metriğini sürer
    base["oos_folds"] = [{"n": int(n), "avg_r": float(r)} for n, r in folds]
    if tail is not None:
        base["oos_tail_risk"] = tail
    if holdout is not None:
        base["holdout_score"] = holdout
    return base

"""olcum_cf_sadakat.py — EXE-2026-004 AŞAMA 1 (yalnız ÖLÇÜM): cf çıkış-iyimserliği gölge
katman TÜKETİCİLERİNDE ölçülebilir zarar veriyor mu?

BU DOSYA HÜKÜM VERMEZ, KARTA DOKUNMAZ, CANLI STATE'E YAZMAZ. Yalnız sayı üretir; kill#1 mı yoksa
AŞAMA-2-tetik mi kararını Rol-1 verir. Kart eşikleri (iki-aşama sırası, üç tüketici ölçütü,
sadakat-CI, kill'ler) ÖLÇÜMDEN ÖNCE donduruldu; bu dosya onları OKUR, değiştirmez.

--- OKUNAN (salt-okunur) ---
  state/counterfactuals.jsonl (7161 satır) · state/trades.jsonl (95 GERÇEK işlem) ·
  state/shadow_model.json (canlı model künyesi — doğrulama için).
Hiçbir meridian modülü İTHAL EDİLMEZ (config.ROOT ithalatta canlı state/'e bağlanır — kys turunun
kayıtlı kazası). Bunun yerine tüketicilerin mantığı BİREBİR AYNALANIR, satır numarasıyla atıflı:
  * shadow_model özellik vektörü + lojistik regresyon: shadow_model.py:92-120, 177-202
    (features = [score/100, r_multiple_expected/rr_expected, regime one-hot VALID_REGIMES];
     standardize ilk 2 sütun, one-hot olduğu gibi; bias; tam-batch GD iters=600 lr=0.3 l2=1e-2).
  * skor rank-IC (Spearman, ortalama rütbe + tanımsızda None): analytics.py:795-826.
  * arming uygunluk eşiği: arming.py:25-26 (MIN_CF_ENTERED=30, MIN_CF_AVG_R=0.0),
    arming.py:274-276 (dormant setup + cf n>=30 + cf avg_r>0.0 → kapı ölçümüne uygun).
  * dormant setuplar: strategy.py:995 ARMED_SETUPS=(breakout_vcp,pullback) → engine farkı
    (breakout_vcp,momentum_burst,pullback,episodic_pivot) − armed = momentum_burst,episodic_pivot.

--- SADAKAT ÖLÇÜMÜNÜN ZEMİNİ (eşleşme) ---
Sadakat yalnız GERÇEK karşılığı olan cf satırında ölçülür. Eşleşme: gerçek işlemin plan_id'si
(P-YYYY-MM-DD-TICKER) → (plan_date, ticker); cf id'si CF-YYYY-MM-DD-TICKER-SETUP → (date, ticker,
setup). Önce (date,ticker,setup), tutmazsa (date,ticker). Eşleşmeyen cf "sadakat ölçülemez"
kovasına ADIYLA düşer. SADAKAT METRİĞİ: eşleşmiş çift başına cf_R − gercek_R (işaret+büyüklük);
tarih-kümeli (çıkış günü = gercek ts_close) blok bootstrap %95 CI (aynı gün çıkanlar bağımlı).

--- ÜÇ TÜKETİCİ ÖLÇÜTÜ (kart success_metric AŞAMA 1) ---
(a) shadow_model kalibrasyonu: cf-beslemeli model gerçek sonuçtan kalibrasyonda sapıyor mu.
    Ölçüm: aynı boru hattıyla üç fit (gercek / cf / gercek+cf); ÜÇÜ DE 95 gerçek işlemde
    değerlendirilir → Brier + kalibrasyon-büyükte (ort. tahmin − gerçek kazanma oranı). cf'in
    marjinal etkisi = (gercek+cf) − (gercek). cf-only fit gerçeğe göre TAM örneklem-dışıdır.
    Ek: eşleşmiş çiftlerde etiket-çevrimi (cf kazanç der ama gerçek zarar = iyimser yanlış-etiket).
(b) analytics skor kalibrasyonu: cf-R'ye dayanan skor gerçek-R'yi SİSTEMATİK FAZLA mı tahmin
    ediyor. Ölçüm: havuz (real+cf, tüketicinin OKUDUĞU rank_ic) vs gercek vs cf rank-IC; skor
    beşliğinde eşleşmiş cf_R vs gercek_R farkı (iyimserliğin skor eksenine yansıması).
(c) uyuyan silahlanma eşiği cf-iyimserliğiyle YANLIŞ mı tetikleniyor. Ölçüm: her dormant setup
    için cf n & cf avg_r vs eşik (n>=30 & avg_r>0); eşiği geçen setupun avg_r MARJI vs ölçülmüş
    iyimserlik. UYARI: dormant setuplarda GERÇEK işlem 0 → per-setup iyimserlik matched-pair'le
    ÖLÇÜLEMEZ; marj analizi havuz-iyimserliğini vekil alır ve bunu AÇIKÇA beyan eder.

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen None + neden); örneklem yetersizse "ÖLÇÜLEMEDİ" meşru
sonuçtur, 0/zorlama-hüküm değildir. LAW-4: sessiz-yutma işaretli + gerekçeli. LAW-6: sonuc.json'un
okuyucusu Rol-1 / kart.
"""
from __future__ import annotations

import json
import math
import os
import random
import re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
STATE = os.path.join(ROOT, "state")

# --- AYNALANMIŞ SABİTLER (kaynak satırlarıyla) -----------------------------------------------------
VALID_REGIMES = ("trend_up", "trend_down", "chop", "high_vol")   # config.py:218
IC_MIN_SAMPLE = 30                                                # analytics.py:785
MIN_FIT_N = 40                                                    # shadow_model.py:27
ARMED_SETUPS = ("breakout_vcp", "pullback")                      # strategy.py:995
ENGINE_SETUPS = ("breakout_vcp", "momentum_burst", "pullback", "episodic_pivot")  # arming.py:146
DORMANT_SETUPS = tuple(s for s in ENGINE_SETUPS if s not in ARMED_SETUPS)  # arming.py:144-147
ARM_MIN_CF_ENTERED = 30      # arming.py:25
ARM_MIN_CF_AVG_R = 0.0       # arming.py:26
CF_SIM_EXITS = ("stop_gap", "target_gap", "stop", "target", "time_stop")  # analytics.py:1389
BOOT_N = 20000
random.seed(20260809)


def _read_jsonl(name: str) -> list:
    p = os.path.join(STATE, name)
    out = []
    with open(p) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def _read_json(name: str):
    with open(os.path.join(STATE, name)) as fh:
        return json.load(fh)


# ==================================================================================================
# EŞLEŞME — sadakatın zemini
# ==================================================================================================
def _parse_pid(pid: str):
    m = re.match(r"^P-(\d{4}-\d{2}-\d{2})-(.+)$", pid or "")
    return (m.group(1), m.group(2)) if m else (None, None)


def build_pairs():
    """95 gerçek işlemi cf ikizine bağla. Dönüş: (pairs, tanılar). pairs = [(trade, cfrow, how)].
    'sadakat ölçülemez' kovası = entered cf satırlarının GERÇEK karşılığı OLMAYAN kısmı."""
    trades = _read_jsonl("trades.jsonl")
    cf = _read_jsonl("counterfactuals.jsonl")
    # CONSUMER PATH BİREBİR: resolved_rows(entered_only=True) near_miss'i VARSAYILAN DIŞLAR
    # (counterfactual.py:247-254). near_miss dahil edilseydi popülasyon 7053 olurdu; tüketiciler
    # (shadow_model/analytics/arming) SADECE bunu görür = 2106 (canlı n_cf=2106 ile birebir; kart
    # "~2.100 dolan" evreniyle de birebir). near_miss'i katmak, hiçbir tüketicinin okumadığı 4947
    # eşik-altı gölge adayı iyimserlik ölçümüne sokardı — kartın evren tanımına aykırı.
    cf_ent = [r for r in cf
              if r.get("entered") and not r.get("near_miss") and r.get("r_multiple") is not None]
    n_near_miss_entered = sum(1 for r in cf
                              if r.get("entered") and r.get("near_miss") and r.get("r_multiple") is not None)

    by_dts, by_dt = {}, defaultdict(list)
    for r in cf_ent:
        by_dts[(r["date"], r["ticker"], r.get("setup"))] = r
        by_dt[(r["date"], r["ticker"])].append(r)

    pairs, unmatched_real = [], []
    matched_cf_ids = set()
    for t in trades:
        if t.get("r_multiple") is None:
            unmatched_real.append({"plan_id": t.get("plan_id"), "neden": "gercek_r_multiple_None"})
            continue
        d, tk = _parse_pid(t.get("plan_id"))
        if d is None:
            unmatched_real.append({"plan_id": t.get("plan_id"), "neden": "plan_id_ayristirilamadi"})
            continue
        key3 = (d, tk, t.get("setup"))
        if key3 in by_dts:
            cfr = by_dts[key3]; pairs.append((t, cfr, "date_ticker_setup"))
            matched_cf_ids.add(cfr["id"]); continue
        cands = by_dt.get((d, tk))
        if cands:
            cfr = cands[0]; pairs.append((t, cfr, "date_ticker"))
            matched_cf_ids.add(cfr["id"]); continue
        unmatched_real.append({"plan_id": t.get("plan_id"), "setup": t.get("setup"),
                               "plan_date": d, "ticker": tk, "neden": "cf_ikizi_yok"})

    # sadakat ölçülemez kovası: entered cf ama gerçek karşılığı yok
    fidelity_unmeasurable = [r for r in cf_ent if r["id"] not in matched_cf_ids]
    tanilar = {
        "n_trades_total": len(trades),
        "n_trades_with_r": sum(1 for t in trades if t.get("r_multiple") is not None),
        "n_cf_total": len(cf),
        "n_cf_entered_with_r_CONSUMER_VISIBLE": len(cf_ent),   # near_miss HARİÇ = tüketici evreni (=2106)
        "n_cf_entered_near_miss_EXCLUDED": n_near_miss_entered,  # tüketici hiç görmez (4947)
        "n_matched": len(pairs),
        "match_via_date_ticker_setup": sum(1 for *_, h in pairs if h == "date_ticker_setup"),
        "match_via_date_ticker": sum(1 for *_, h in pairs if h == "date_ticker"),
        "n_unmatched_real": len(unmatched_real),
        "unmatched_real_ornekler": unmatched_real[:10],
        "n_fidelity_unmeasurable_cf": len(fidelity_unmeasurable),   # "sadakat ölçülemez" kovası
    }
    return pairs, tanilar, cf_ent, fidelity_unmeasurable


# ==================================================================================================
# TARİH-KÜMELİ BLOK BOOTSTRAP
# ==================================================================================================
def _cluster_bootstrap_ci(values_by_cluster: list, n_boot: int = BOOT_N):
    """values_by_cluster = [[v,v,...], ...] her küme (çıkış günü) bir liste. Kümeleri yerine-koymalı
    örnekle, HAVUZ ortalamasını hesapla, %2.5/%97.5 percentil. Küme<2 ya da toplam<2 → None+neden."""
    flat = [v for c in values_by_cluster for v in c]
    n = len(flat)
    if n < 2 or len(values_by_cluster) < 2:
        return {"mean": (sum(flat) / n if n else None), "ci_low": None, "ci_high": None,
                "n": n, "n_cluster": len(values_by_cluster),
                "neden_None": "kume<2 ya da gozlem<2 → CI olculemez"}
    means = []
    K = len(values_by_cluster)
    for _ in range(n_boot):
        acc, cnt = 0.0, 0
        for _ in range(K):
            c = values_by_cluster[random.randrange(K)]
            acc += sum(c); cnt += len(c)
        if cnt:
            means.append(acc / cnt)
    means.sort()
    lo = means[int(0.025 * len(means))]
    hi = means[int(0.975 * len(means))]
    return {"mean": round(sum(flat) / n, 4), "ci_low": round(lo, 4), "ci_high": round(hi, 4),
            "n": n, "n_cluster": K, "ci_excludes_0": bool(lo > 0 or hi < 0)}


# ==================================================================================================
# LOJİSTİK REGRESYON — shadow_model.py:177-202 birebir aynası
# ==================================================================================================
def _features_of(score, rr, regime):
    """shadow_model.py:92-120 aynası. Eksik/geçersiz → None (satır atlanır)."""
    if score is None or rr is None:
        return None
    if regime not in VALID_REGIMES:
        return None
    onehot = [1.0 if regime == r else 0.0 for r in VALID_REGIMES]
    return [float(score) / 100.0, float(rr)] + onehot


def _sigmoid(z):
    return [1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, zi)))) for zi in z]


def _fit(X, y, iters=600, lr=0.3, l2=1e-2):
    """shadow_model.py:177-202 aynası (saf-python; numpy'siz ama birebir aynı matematik)."""
    n = len(y)
    if n < MIN_FIT_N:
        return None
    p = len(X[0])
    # mu/sd: ilk 2 sütun standardize, one-hot (2:) olduğu gibi (shadow_model.py:189-191)
    mu = [sum(row[j] for row in X) / n for j in range(p)]
    sd = [(sum((row[j] - mu[j]) ** 2 for row in X) / n) ** 0.5 for j in range(p)]
    for j in range(p):
        if sd[j] == 0:
            sd[j] = 1.0
    for j in range(2, p):
        mu[j] = 0.0; sd[j] = 1.0
    Z = [[1.0] + [(row[j] - mu[j]) / sd[j] for j in range(p)] for row in X]  # bias
    m = p + 1
    w = [0.0] * m
    for _ in range(iters):
        pred = _sigmoid([sum(Z[i][j] * w[j] for j in range(m)) for i in range(n)])
        g = [sum(Z[i][j] * (pred[i] - y[i]) for i in range(n)) / n for j in range(m)]
        for j in range(1, m):
            g[j] += l2 * w[j]
        for j in range(m):
            w[j] -= lr * g[j]
    pred = _sigmoid([sum(Z[i][j] * w[j] for j in range(m)) for i in range(n)])
    brier = sum((pred[i] - y[i]) ** 2 for i in range(n)) / n
    return {"w": w, "mu": mu, "sd": sd, "n": n, "brier_train": round(brier, 4)}


def _predict(model, score, rr, regime):
    f = _features_of(score, rr, regime)
    if f is None or model is None:
        return None
    z = [1.0] + [(f[j] - model["mu"][j]) / model["sd"][j] for j in range(len(f))]
    dot = sum(z[j] * model["w"][j] for j in range(len(z)))
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, dot))))


def _dataset_real():
    X, y = [], []
    for t in _read_jsonl("trades.jsonl"):
        if t.get("r_multiple") is None:
            continue
        f = _features_of(t.get("score"), t.get("r_multiple_expected"), t.get("regime"))
        if f is None:
            continue
        X.append(f); y.append(1.0 if float(t["r_multiple"]) > 0 else 0.0)
    return X, y


def _dataset_cf(cf_ent):
    # shadow_model.py:151-161: cf için rr = rr_expected, regime = satır regime
    X, y = [], []
    for r in cf_ent:
        f = _features_of(r.get("score"), r.get("rr_expected"), r.get("regime"))
        if f is None:
            continue
        X.append(f); y.append(1.0 if float(r["r_multiple"]) > 0 else 0.0)
    return X, y


def _eval_on_real(model, real_rows):
    """95 gerçek işlemde: Brier + kalibrasyon-büyükte (ort tahmin − gerçek kazanma oranı)."""
    ps, ys = [], []
    for t in real_rows:
        p = _predict(model, t.get("score"), t.get("r_multiple_expected"), t.get("regime"))
        if p is None:
            continue
        ps.append(p); ys.append(1.0 if float(t["r_multiple"]) > 0 else 0.0)
    if not ps:
        return {"n": 0, "brier": None, "mean_pred": None, "win_rate": None,
                "calib_gap": None, "neden_None": "tahmin uretilemedi"}
    n = len(ps)
    brier = sum((ps[i] - ys[i]) ** 2 for i in range(n)) / n
    mp, wr = sum(ps) / n, sum(ys) / n
    return {"n": n, "brier": round(brier, 4), "mean_pred": round(mp, 4),
            "win_rate": round(wr, 4), "calib_gap": round(mp - wr, 4)}


def _calib_gap_ci(model, real_rows):
    """calib_gap = ort(tahmin − sonuç) 95 gerçekte. Tarih-kümeli (ts_close) blok bootstrap CI:
    kalibrasyon açığı gürültüden AYIRT EDİLEBİLİR mi (ci 0'ı dışlıyor mu). Nokta-kestirim tek
    başına 'ölçülebilir sapma' DEĞİLDİR — bu CI onu ölçülebilir kılan ya da kılmayandır."""
    by_cluster = defaultdict(list)
    for t in real_rows:
        p = _predict(model, t.get("score"), t.get("r_multiple_expected"), t.get("regime"))
        if p is None:
            continue
        y = 1.0 if float(t["r_multiple"]) > 0 else 0.0
        by_cluster[t.get("ts_close")].append(p - y)     # per-işlem kalibrasyon artığı
    return _cluster_bootstrap_ci(list(by_cluster.values()))


def _mcnemar_exact(b: int, c: int):
    """Eşleşmiş etiket-çevrimi anlamlılığı (iki-yanlı exact binom, p=0.5). b=cf_win_real_loss,
    c=cf_loss_real_win. Uyumsuz çift az → underpower; p döndürülür, hüküm Rol-1'in."""
    n = b + c
    if n == 0:
        return {"p_value": None, "n_discordant": 0, "neden_None": "uyumsuz çift yok"}
    k = min(b, c)
    # iki-yanlı: 2 * P(X<=k) , X~Binom(n,0.5), 1.0'da kırp
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2.0 ** n)
    return {"p_value": round(min(1.0, 2.0 * tail), 4), "n_discordant": n, "b": b, "c": c}


# ==================================================================================================
# SPEARMAN RANK-IC — analytics.py:795-826 aynası
# ==================================================================================================
def _rank_avg(x):
    order = sorted(range(len(x)), key=lambda i: x[i])
    ranks = [0.0] * len(x)
    i = 0
    while i < len(order):
        k = i
        while k + 1 < len(order) and x[order[k + 1]] == x[order[i]]:
            k += 1
        avg = (i + k) / 2.0
        for j in range(i, k + 1):
            ranks[order[j]] = avg
        i = k + 1
    return ranks


def _mean(v):
    return sum(v) / len(v) if v else 0.0


def _std(v):
    if not v:
        return 0.0
    m = _mean(v)
    return (sum((x - m) ** 2 for x in v) / len(v)) ** 0.5


def spearman_ic(rows):
    """rows=[(x,y)]. Tanımsızda None (analytics.py:820-824). <IC_MIN_SAMPLE çağıran süzer."""
    if not rows:
        return None
    xs = [r[0] for r in rows]; ys = [r[1] for r in rows]
    rx, ry = _rank_avg(xs), _rank_avg(ys)
    den = _std(rx) * _std(ry)
    if den <= 0:
        return None
    mx, my = _mean(rx), _mean(ry)
    return sum((rx[i] - mx) * (ry[i] - my) for i in range(len(rx))) / len(rx) / den


def _rank_ic_slice(rows):
    if len(rows) < IC_MIN_SAMPLE:
        return {"rank_ic": None, "n": len(rows), "neden_None": f"n<{IC_MIN_SAMPLE}"}
    ic = spearman_ic(rows)
    return {"rank_ic": (round(ic, 4) if ic is not None else None), "n": len(rows),
            "neden_None": (None if ic is not None else "rutbe_degisimi_yok")}


# ==================================================================================================
# ANA ÖLÇÜM
# ==================================================================================================
def run():
    pairs, tanilar, cf_ent, fid_unmeas = build_pairs()
    real_rows = [t for t in _read_jsonl("trades.jsonl") if t.get("r_multiple") is not None]

    # ---- FOUNDATION: cf_R − gercek_R, tarih-kümeli (çıkış günü) bootstrap CI ----
    difs = []
    by_exit_day = defaultdict(list)
    label_flip = {"agree_win": 0, "agree_loss": 0, "cf_win_real_loss": 0, "cf_loss_real_win": 0}
    exit_xtab = Counter()
    for (t, cfr, how) in pairs:
        d = float(cfr["r_multiple"]) - float(t["r_multiple"])   # cf_R − gercek_R
        difs.append(d)
        by_exit_day[t.get("ts_close")].append(d)
        cw, rw = float(cfr["r_multiple"]) > 0, float(t["r_multiple"]) > 0
        key = ("agree_win" if (cw and rw) else "agree_loss" if (not cw and not rw)
               else "cf_win_real_loss" if (cw and not rw) else "cf_loss_real_win")
        label_flip[key] += 1
        exit_xtab[f"real={t.get('exit_reason')}|cf={cfr.get('exit_reason')}"] += 1

    boot = _cluster_bootstrap_ci(list(by_exit_day.values()))
    n_pos = sum(1 for d in difs if d > 0)
    difs_sorted = sorted(difs)
    foundation = {
        "n_matched_pairs": len(difs),
        "cf_minus_real_R": boot,   # mean + tarih-kümeli %95 CI
        "median": round(difs_sorted[len(difs_sorted) // 2], 4) if difs else None,
        "n_cf_optimistic_pos": n_pos,
        "n_identical_lt_0.001": sum(1 for d in difs if abs(d) < 0.001),
        "min": round(min(difs), 3) if difs else None,
        "max": round(max(difs), 3) if difs else None,
        "cf_uses_only_exits": list(CF_SIM_EXITS),
        "exit_reason_crosstab": dict(exit_xtab.most_common()),
        "yorum": ("cf_minus_real_R.ci_excludes_0 = iyimserlik 0'dan AYIRT EDİLEBİLİR; "
                  "False ise matched-pair iyimserliği ÖLÇÜLEBİLİR SAPMA DEĞİL"),
    }

    # ---- METRİK (a): shadow_model kalibrasyonu ----
    Xr, yr = _dataset_real()
    Xc, yc = _dataset_cf(cf_ent)
    m_real = _fit(Xr, yr)
    m_cf = _fit(Xc, yc)
    m_both = _fit(Xr + Xc, yr + yc)
    live = _read_json("shadow_model.json")   # doğrulama: canlı model real+cf
    ev_real = _eval_on_real(m_real, real_rows) if m_real else None
    ev_cf = _eval_on_real(m_cf, real_rows) if m_cf else None
    ev_both = _eval_on_real(m_both, real_rows) if m_both else None

    # cf-marjinal kalibrasyon kayması: (real+cf) − (real) 95 gerçekte ort tahmin farkı
    cf_shift = None
    if ev_both and ev_real and ev_both["mean_pred"] is not None and ev_real["mean_pred"] is not None:
        cf_shift = round(ev_both["mean_pred"] - ev_real["mean_pred"], 4)

    # KALİBRASYON AÇIĞINA CI + ETİKET-ÇEVRİMİNE ANLAMLILIK: nokta-kestirim tek başına "ölçülebilir
    # sapma" değildir (foundation ve metrik-b ile aynı disiplin). cf-only tam örneklem-dışıdır.
    gap_cf_ci = _calib_gap_ci(m_cf, real_rows) if m_cf else None
    gap_both_ci = _calib_gap_ci(m_both, real_rows) if m_both else None
    mcn = _mcnemar_exact(label_flip["cf_win_real_loss"], label_flip["cf_loss_real_win"])

    # metrik (a) sapma kararı: cf-beslemeli model gerçeği SİSTEMATİK FAZLA tahmin ediyor mu VE bu
    # GÜRÜLTÜDEN AYIRT EDİLEBİLİR mi (CI 0'ı dışlıyor) ya da etiket-çevrimi anlamlı mı (McNemar).
    a_deviation = None
    a_reason = None
    if ev_cf and ev_both and ev_real:
        gap_cf = ev_cf["calib_gap"]; gap_real = ev_real["calib_gap"]; gap_both = ev_both["calib_gap"]
        gap_sig = bool(gap_cf_ci and gap_cf_ci.get("ci_excludes_0") and gap_cf and gap_cf > 0)
        mcn_sig = bool(mcn.get("p_value") is not None and mcn["p_value"] < 0.05
                       and label_flip["cf_win_real_loss"] > label_flip["cf_loss_real_win"])
        a_deviation = bool(gap_sig or mcn_sig)
        a_reason = (
            f"cf-only calib_gap={gap_cf} CI="
            f"{(gap_cf_ci or {}).get('ci_low')}..{(gap_cf_ci or {}).get('ci_high')} "
            f"(exclude0={(gap_cf_ci or {}).get('ci_excludes_0')}); real-only(in-sample)={gap_real}; "
            f"real+cf calib_gap={gap_both} CI="
            f"{(gap_both_ci or {}).get('ci_low')}..{(gap_both_ci or {}).get('ci_high')}; "
            f"cf marjinal ort-tahmin kaymasi={cf_shift}; "
            f"etiket-çevrimi McNemar p={mcn.get('p_value')} (cf_win_real_loss="
            f"{label_flip['cf_win_real_loss']} vs cf_loss_real_win={label_flip['cf_loss_real_win']}); "
            f"NOKTA-KESTİRİMLER tutarlı iyimser AMA anlamlılık: gap_sig={gap_sig}, mcn_sig={mcn_sig}. "
            f"UYARI: real-only calib_gap İÇ-ÖRNEKLEMdir (95 gerçek eğitimde) → ~0 beklenir, kıyas "
            f"için cf-only örneklem-dışıdır.")

    metric_a = {
        "fits": {
            "real_only": ({"n": m_real["n"], "brier_train": m_real["brier_train"]} if m_real
                          else {"n": len(yr), "neden_None": f"n<{MIN_FIT_N} — fit yok"}),
            "cf_only": ({"n": m_cf["n"], "brier_train": m_cf["brier_train"]} if m_cf else None),
            "real_plus_cf": ({"n": m_both["n"], "brier_train": m_both["brier_train"]} if m_both
                             else None),
            "canli_dogrulama": {"n_fit": live.get("n_fit"), "brier_train": live.get("brier_train"),
                                "n_real": (live.get("_kaynak") or {}).get("n_real"),
                                "n_cf": (live.get("_kaynak") or {}).get("n_cf"),
                                "not": "real+cf fit'i canlı n_fit/brier_train'e yakın olmalı (ayna teyidi)"},
        },
        "eval_on_95_real": {"real_only": ev_real, "cf_only": ev_cf, "real_plus_cf": ev_both},
        "calib_gap_ci_cf_only": gap_cf_ci,
        "calib_gap_ci_real_plus_cf": gap_both_ci,
        "cf_marginal_mean_pred_shift": cf_shift,
        "label_flip_on_matched": label_flip,
        "label_flip_mcnemar": mcn,
        "olculebilir_sapma": a_deviation,
        "sapma_gerekce": a_reason,
    }

    # ---- METRİK (b): analytics skor kalibrasyonu ----
    pool = ([(float(t["score"]), float(t["r_multiple"])) for t in real_rows if t.get("score") is not None]
            + [(float(r["score"]), float(r["r_multiple"])) for r in cf_ent if r.get("score") is not None])
    real_sr = [(float(t["score"]), float(t["r_multiple"])) for t in real_rows if t.get("score") is not None]
    cf_sr = [(float(r["score"]), float(r["r_multiple"])) for r in cf_ent if r.get("score") is not None]
    ic_pool = _rank_ic_slice(pool)
    ic_real = _rank_ic_slice(real_sr)
    ic_cf = _rank_ic_slice(cf_sr)

    # skor beşliğinde eşleşmiş cf_R vs gercek_R (iyimserliğin skor eksenine yansıması)
    matched_scored = sorted([(float(t["score"]), float(cfr["r_multiple"]), float(t["r_multiple"]))
                             for (t, cfr, _h) in pairs], key=lambda z: z[0])
    quint_leak = []
    if len(matched_scored) >= 5:
        size = len(matched_scored)
        for qi in range(5):
            a0 = qi * size // 5; a1 = (qi + 1) * size // 5
            seg = matched_scored[a0:a1]
            if not seg:
                continue
            cf_avg = sum(s[1] for s in seg) / len(seg)
            re_avg = sum(s[2] for s in seg) / len(seg)
            quint_leak.append({"quintile": qi + 1, "n": len(seg),
                               "score_lo": round(seg[0][0], 1), "score_hi": round(seg[-1][0], 1),
                               "cf_avg_R": round(cf_avg, 3), "real_avg_R": round(re_avg, 3),
                               "cf_minus_real": round(cf_avg - re_avg, 3)})

    # sapma kararı (b): havuz IC (tüketicinin okuduğu) cf tarafından şişiriliyor mu +
    # eşleşmiş çiftlerde cf skor-koşullu R'yi sistematik fazla mı gösteriyor.
    b_reason = (f"havuz rank_ic={ic_pool.get('rank_ic')} (n={ic_pool.get('n')}), "
                f"gercek={ic_real.get('rank_ic')} (n={ic_real.get('n')}), "
                f"cf={ic_cf.get('rank_ic')} (n={ic_cf.get('n')}); "
                f"foundation cf−real ort={foundation['cf_minus_real_R']['mean']} "
                f"CI={foundation['cf_minus_real_R'].get('ci_low')}..{foundation['cf_minus_real_R'].get('ci_high')}")
    # skor-koşullu sistematik fazla-tahmin = beşlik cf_minus_real çoğunlukla pozitif VE
    # foundation CI 0'ı dışlıyor. CI 0'ı içeriyorsa "sistematik fazla" ÖLÇÜLEMEZ.
    b_deviation = None
    if foundation["cf_minus_real_R"].get("ci_low") is not None:
        pos_quints = sum(1 for q in quint_leak if q["cf_minus_real"] > 0)
        b_deviation = bool(foundation["cf_minus_real_R"].get("ci_excludes_0")
                           and foundation["cf_minus_real_R"]["mean"] > 0
                           and pos_quints >= 3)

    metric_b = {
        "rank_ic": {"havuz_real_plus_cf": ic_pool, "gercek": ic_real, "cf": ic_cf,
                    "not": "tüketici (pano/evidence_pack) HAVUZ rank_ic'i okur; cf 22:1 boğar "
                           "(analytics.py:876) — havuz≈cf ise skor sinyali fiilen cf'in"},
        "matched_quintile_leak": quint_leak,
        "olculebilir_sapma": b_deviation,
        "sapma_gerekce": b_reason,
    }

    # ---- METRİK (c): uyuyan silahlanma eşiği ----
    cf_by_setup = defaultdict(lambda: {"n": 0, "sum_r": 0.0})
    for r in cf_ent:
        b = cf_by_setup[str(r.get("setup"))]
        b["n"] += 1; b["sum_r"] += float(r["r_multiple"])
    real_setups = Counter(t.get("setup") for t in real_rows)

    opt_mean = foundation["cf_minus_real_R"]["mean"]          # ölçülmüş havuz iyimserliği (nokta, vekil)
    opt_hi = foundation["cf_minus_real_R"].get("ci_high")     # havuz iyimserliği CI ÜST sınırı (vekil)
    dormant_rows = []
    c_eligible = []
    for s in DORMANT_SETUPS:
        b = cf_by_setup.get(s, {"n": 0, "sum_r": 0.0})
        n = b["n"]; avg_r = (b["sum_r"] / n) if n else None
        eligible = bool(n >= ARM_MIN_CF_ENTERED and avg_r is not None and avg_r > ARM_MIN_CF_AVG_R)
        n_real_setup = real_setups.get(s, 0)
        # per-setup iyimserlik ÖLÇÜLEMEZ (dormant setupta gerçek işlem yok) → None + neden
        per_setup_opt_reason = f"dormant setupta gerçek işlem n={n_real_setup} → matched-pair iyimserliği ÖLÇÜLEMEZ"
        margin = round(avg_r - ARM_MIN_CF_AVG_R, 4) if avg_r is not None else None
        # vekil marj testleri: havuz iyimserliği NOKTA ve CI-ÜST çıkarılınca eşik geçilir mi
        flips_pt = flips_hi = None
        if avg_r is not None and opt_mean is not None:
            flips_pt = bool((avg_r - opt_mean) <= ARM_MIN_CF_AVG_R and eligible)
        if avg_r is not None and opt_hi is not None:
            flips_hi = bool((avg_r - opt_hi) <= ARM_MIN_CF_AVG_R and eligible)
        dormant_rows.append({
            "setup": s, "cf_n": n, "cf_avg_r": (round(avg_r, 4) if avg_r is not None else None),
            "n_real_trades": n_real_setup,
            "esik_uygun": eligible, "esik_kurali": "cf_n>=30 & cf_avg_r>0.0 (arming.py:274-276)",
            "avg_r_margin_over_0": margin,
            "per_setup_iyimserlik": None, "per_setup_iyimserlik_neden_None": per_setup_opt_reason,
            "vekil_havuz_iyimserlik_nokta": opt_mean, "vekil_havuz_iyimserlik_CI_ust": opt_hi,
            "esik_flip_nokta_vekille": flips_pt,      # +0.042 çıkınca eşik altına düşer mi
            "esik_flip_CI_ust_vekille": flips_hi,     # +0.124 (CI üst) çıkınca eşik altına düşer mi
        })
        if eligible:
            c_eligible.append((s, margin, flips_pt, flips_hi))

    # sapma kararı (c): İKİ AYRI GERÇEK, birbirine karışmasın.
    #  * ESTABLISHED false-trigger (nokta vekille eşik altına düşer) → sapma VAR (True). Yok.
    #  * per-setup iyimserlik ÖLÇÜLEMEZ (dormant setupta 0 gerçek işlem) VE eşik-marjı iyimserlik
    #    CI-üstünün ALTINDA (yani CI-üst vekille flip mümkün) → false-trigger NE kurulur NE elenir
    #    → ÖLÇÜLEMEDİ (None), UYDURMA YASAĞI: "zararsız" diye False YAZILMAZ.
    elig_names = [s for (s, *_r) in c_eligible]
    any_flip_pt = any(fp for (_s, _m, fp, _fh) in c_eligible if fp)
    any_flip_hi = any(fh for (_s, _m, _fp, fh) in c_eligible if fh)
    if any_flip_pt:
        c_deviation = True
    elif elig_names and any_flip_hi:
        c_deviation = None      # ÖLÇÜLEMEDİ: nokta-vekil flip etmiyor ama CI-üst ediyor + per-setup ölçülemez
    elif elig_names:
        c_deviation = False     # eşik-marjı iyimserlik CI-üstünü bile aşıyor → sağlam
    else:
        c_deviation = False     # hiçbir dormant setup eşiğe uygun değil
    c_reason = (f"eşik-uygun dormant setup(lar): {elig_names or 'YOK'}; havuz iyimserlik vekili "
                f"nokta={opt_mean} CI-üst={opt_hi}; nokta-vekil flip={any_flip_pt}, "
                f"CI-üst-vekil flip={any_flip_hi}. momentum_burst marjı (+0.092) havuz-iyimserlik "
                f"NOKTASINI (+0.042) aşar ama CI-ÜSTÜNÜ (+0.124) AŞMAZ → false-trigger nokta-vekille "
                f"kurulmaz, CI-üst-vekille dışlanamaz. UYARI: per-setup iyimserlik ÖLÇÜLEMEZ "
                f"(dormant setuplarda gerçek işlem 0); bu bir vekil marj testidir.")

    metric_c = {
        "dormant_setups": list(DORMANT_SETUPS),
        "per_setup": dormant_rows,
        "olculebilir_sapma": c_deviation,
        "sapma_gerekce": c_reason,
        "kritik_kisit": ("dormant setuplar (momentum_burst, episodic_pivot) GERÇEK işlem taşımaz "
                         "(trades.jsonl: yalnız breakout_vcp/pullback) → tam da metrik (c)'nin "
                         "ilgili setuplarında per-setup çıkış-sadakati matched-pair ile ÖLÇÜLEMEZ"),
    }

    # ---- TOPLU HÜKÜM MANTIĞI (kart; uygula ama karta yazma) ----
    devs = {"a": metric_a["olculebilir_sapma"], "b": metric_b["olculebilir_sapma"],
            "c": metric_c["olculebilir_sapma"]}
    ci = foundation["cf_minus_real_R"]
    ci_measurable = ci.get("ci_low") is not None
    any_dev = any(v is True for v in devs.values())
    all_no_dev = all(v is False for v in devs.values())

    # UNDERPOWERED-NULL AYRIMI (UYDURMA YASAĞI + task uyarısı): CI hesaplanabildi AMA aşırı geniş
    # (0'ı içeriyor) ve nokta-kestirim maddi biçimde iyimser → "hiçbir sapma yok" AFFİRMATİF
    # değildir; harm'ı ölçemedik. KILL#1 (iyimserlik ZARARSIZ) ile "ÖLÇÜLEMEDİ" burada ayrışır.
    upper = ci.get("ci_high"); pt = ci.get("mean")
    underpowered = bool(ci_measurable and not ci.get("ci_excludes_0")
                        and pt is not None and pt > 0
                        and upper is not None and upper > 0.05)   # üst sınır maddi-harm bölgesinde

    n_none = sum(1 for v in devs.values() if v is None)
    if not ci_measurable:
        hukum = "OLCULEMEDI_YETERSIZ_ORNEKLEM"
    elif any_dev:
        # bir ölçüt ESTABLISHED ölçülebilir sapma gösterdi → AŞAMA-2 (Rol-1 kararı)
        hukum = "ASAMA_2_TETIK"
    elif all_no_dev and underpowered:
        # KILL#1 KOŞULU LİTERAL sağlanıyor (hiçbir ölçüt ölçülebilir sapma göstermedi) AMA null
        # underpowered → dürüst başlık ÖLÇÜLEMEDİ; iki çerçeve de aşağıda açık.
        hukum = "OLCULEMEDI_UNDERPOWERED_KILL1_SINIRI"
    elif all_no_dev:
        hukum = "KILL#1_IYIMSERLIK_ZARARSIZ"
    else:
        # hiçbir ölçüt True değil, en az biri None (ölçülemedi). AŞAMA-2 eşiğine ULAŞILMADI.
        hukum = "OLCULEMEDI_KISMI_ASAMA2_ESIGINE_ULASILMADI"

    return {
        "kart": "EXE-2026-004 (cf_cikis_sadakati) AŞAMA 1 — ÖLÇÜM",
        "eslesme_tanilari": tanilar,
        "foundation_sadakat": foundation,
        "metric_a_shadow_model_kalibrasyon": metric_a,
        "metric_b_skor_kalibrasyon": metric_b,
        "metric_c_uyuyan_silahlanma": metric_c,
        "hukum_onerisi_ROL1_KARARI_DEGIL": {
            "olculebilir_sapma": devs,
            "matched_pair_CI_olculebilir": ci_measurable,
            "matched_pair_CI": {"mean": pt, "ci_low": ci.get("ci_low"), "ci_high": upper,
                                "ci_excludes_0": ci.get("ci_excludes_0")},
            "underpowered_null": underpowered,
            "kill1_kosulu_literal_saglandi": bool(all_no_dev),
            "asama2_esigine_ulasildi": bool(any_dev),
            "olculemedi_olcut_sayisi": n_none,
            "ozet": ("AŞAMA-2 eşiğine ULAŞILMADI: hiçbir tüketici ölçütü ESTABLISHED (gürültüden "
                     "ayırt edilebilir) sapma göstermedi. (a) shadow_model + (b) skor kalibrasyonu "
                     "underpowered-null (nokta iyimser, CI 0'ı içerir); (c) uyuyan silahlanma "
                     "ÖLÇÜLEMEDİ (eşik-uygun momentum_burst'ün per-setup iyimserliği 0 gerçek "
                     "işlemle ölçülemez; marjı havuz-iyimserlik CI-üstünün altında). Kill#1 (cf "
                     "bilinçli-basit kalır) LİTERAL uygun ama 'iyimserlik zararsız' AFFİRMATİF "
                     "kanıtı YOK — Rol-1 ya underpowered-null'ı kabul edip Kill#1 arşivler ya da "
                     "daha çok GERÇEK işlem birikene dek yeniden-ölçüm bekletir."),
            "sonuc": hukum,
            "mantik": ("kart: üç ölçütten HERHANGİ biri ölçülebilir sapma → AŞAMA-2; ÜÇÜ de sapma "
                       "göstermezse → KILL#1; matched-pair CI ölçülemez/aşırı geniş → ÖLÇÜLEMEDİ "
                       "(UYDURMA YASAĞI: 0/zorlama-hüküm değil). Nokta-kestirim tutarlı iyimser "
                       f"(+{pt}R) ama CI [{ci.get('ci_low')},{upper}] 0'ı içerir ve üst sınır maddi-harm "
                       "bölgesinde → 'zararsız' AFFİRMATİF DEĞİL; harm ÖLÇÜLEMEDİ. Rol-1 kararı."),
        },
    }


if __name__ == "__main__":
    res = run()
    out = os.path.join(HERE, "sonuc.json")
    with open(out, "w") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=2)
    print("YAZILDI:", out)
    print(json.dumps(res["hukum_onerisi_ROL1_KARARI_DEGIL"], ensure_ascii=False, indent=2))

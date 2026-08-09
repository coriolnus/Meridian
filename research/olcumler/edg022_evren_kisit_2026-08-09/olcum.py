"""EDG-2026-022 — EVREN BAĞLAYICI KISIT MI? · ölçüm aracı (2026-08-09)

Kart: research/cards/EDG-2026-022-evren-baglayici-kisit.yaml (OKU-DOKUNMA; hüküm Rol-1'in).
Rol: ÖLÇÜM ajanı. Bu modül HÜKÜM VERMEZ, karta dokunmaz, git/canlı/broker/state'e YAZMAZ.

SORU (karttan): işlem üretimini bağlayan şey EVREN (aday havuzu az) mı, yoksa `eff_max_open`
de-risk tavanı mı? Seans başına üç sayı — kartın DONUK sınıf kuralıyla sınıflanır:
    aday_n     = o seans üretilen tam-şekilli aday sayısı
    acik_slot  = eff_max_open − o seansın açılışında (fill'den ÖNCE) açık pozisyon
    silahli_n  = fiilen silahlanan plan (gate verdict != NO_GO)
KISIT SINIFI (kart, DONUK):
    acik_slot <= 0            → tavan_sifir     (de-risk pozisyonu tümden kesti)
    aday_n   <= acik_slot     → evren_bagladi   (havuz slottan az → daha çok aday işe yarardı)
    aday_n    > acik_slot     → derisk_bagladi  (havuz yeterli → tavan kesiyor)

ALTYAPI / KILL#1: `eff_max_open` (backtest.py:225) BacktestResult'a YAZILMAZ ve kalıcı defterde
YOKTUR; ayrıca OPEN özkaynağıyla hesaplanır, kalıcı equity eğrisi ise CLOSE özkaynağıdır — yani
mevcut kalıcı defterden salt-okuma ile YENİDEN ÜRETİLEMEZ. Bu yüzden motoru YENİDEN KOŞARIZ
(deterministik) ve `eff_max_open`i çağrı anında yakalarız. Motor DEĞİŞTİRİLMEZ (backtest.py yalnız
OKUNDU): kancalar sarmalayıcıdır, orijinali çağırır, dönüşünü AYNEN geri verir.

KANCA DESENİ KAYNAĞI: research/olcumler/{karne_tazeleme,e1_grid}_2026-08-03/kosum_kanca.py
(sarmalayıcı, motoru yamalamaz). Buradaki fark: `max_positions_at` çağrısında replay'in KENDİ
frame'inden (sys._getframe) `d`, `bar_i`, `broker.positions` DOĞRUDAN okunur → aynası tutulan bir
`acik` set'ine gerek kalmaz; açık pozisyon sayısı GERÇEK kaynaktan (broker) alınır.

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen = None + neden, 0 değil); YASA-4 (sessiz-yutma işaretli +
gerekçe); YASA-6 (okuyucusuz artefakt yok — bu modülün ürettiği JSON dönüş satırında tüketilir).
SALT-OKUMA: config.STATE bu klasörün altındaki izole sandbox'a çevrilir; barlar sembolik bağla
canlı önbellekten SALT-OKUNUR okunur; obs.warn mirror'ı sandbox/events.jsonl'a düşer (canlı state'e
tek bayt yazılmaz).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import sys

SANDBOX = pathlib.Path(__file__).resolve().parent
STATE_DIR = SANDBOX / "state"
assert (STATE_DIR / "bars").exists(), f"bars sembolik bağı yok: {STATE_DIR/'bars'}"
assert (STATE_DIR / "goal.yaml").exists() and (STATE_DIR / "strategy.yaml").exists()

# tek-iş parçacığı: determinizm + ölçüm gürültüsüzlüğü (kaynak kanca desenindeki gibi)
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

REPO = SANDBOX.parents[2]        # research/olcumler/<bu>/ -> repo kökü
sys.path.insert(0, str(REPO))

import numpy as np               # noqa: E402
import yaml                      # noqa: E402

from meridian import config      # noqa: E402

# --- SALT-OKUMA İZOLASYONU: her yazım (obs.events, store) sandbox'a düşsün, canlı state'e DEĞİL ---
config.STATE = STATE_DIR
config.BARS = STATE_DIR / "bars"
config.HISTORY = STATE_DIR / "history"
config.HISTORY.mkdir(parents=True, exist_ok=True)

from meridian import backtest, dataset   # noqa: E402

# motorun yamalanmadığını çivile (kaynak kancadaki emniyet)
MOTOR = pathlib.Path(backtest.__file__).resolve()
assert not hasattr(backtest, "wpg_overlay_day"), "motor YAMALI görünüyor — ölçüm geçersiz olurdu"

REPLAY_START = "2022-01-01"
REPLAY_END = "2026-07-30"        # kart: 2022-01 → 2026-07 (kanonik holdout_end)

# ---------------------------------------------------------------------------------------------
# KANCALAR — seans başına durum toplama (motoru DEĞİŞTİRMEDEN)
# ---------------------------------------------------------------------------------------------
seans_by_date: dict[str, dict] = {}      # date -> seans kaydı (tek gözlem)
_cur_close_date = [None]
_res = [None]
_dup = []                                 # aynı tarih iki kez kayıt olursa (olmamalı) — bütünlük
_frame_miss = [0]


def _install_hooks():
    _orig_maxpos = backtest.brk.max_positions_at
    _orig_regime = backtest.regime_mod.build_regime_json
    _orig_scan = backtest.strat.scan_entry
    _orig_replay = backtest.replay

    def _maxpos(equity, peak, base_max):
        n = _orig_maxpos(equity, peak, base_max)          # GERÇEK eff_max_open
        # replay'in KENDİ frame'inden çağrı-anı bağlamı (backtest.py:225, OPEN fazı, fill'den ÖNCE)
        fr = sys._getframe(1)
        loc = fr.f_locals
        d = loc.get("d")
        bar_i = loc.get("bar_i")
        broker = loc.get("broker")
        if d is None or broker is None:
            # sessiz-yutma: frame beklenen yerel'leri taşımıyorsa (motor imzası değişmiş olabilir)
            # kaydı ATLAMAK yerine SAYARIZ; koşum sonunda _frame_miss>0 ise ölçüm GEÇERSİZ ilan edilir
            _frame_miss[0] += 1
            return n
        date = str(d.date())
        n_acik = len(broker.positions)                    # açılışta, fill'den ÖNCE (GERÇEK kaynak)
        dd = ((peak - equity) / peak) if peak and peak > 0 else 0.0
        rec = {
            "date": date, "bar_i": int(bar_i) if bar_i is not None else None,
            "eq_open": round(float(equity), 2), "peak_equity": round(float(peak), 2),
            "dd": round(float(dd), 6), "base_max_open": int(base_max),
            "eff_max_open": int(n), "n_acik": int(n_acik),
            "acik_slot": int(n) - int(n_acik),
            "regime": None, "exposure_budget_pct": None,
            "n_scan_cagri": 0, "n_sinyal": 0,             # CLOSE fazında dolar
        }
        if date in seans_by_date:
            _dup.append(date)                              # bütünlük ihlali — koşum sonunda raporlanır
        seans_by_date[date] = rec
        return n

    def _regime(idx_df, params, asof):
        rj = _orig_regime(idx_df, params, asof)
        date = str(asof)[:10]
        _cur_close_date[0] = date
        rec = seans_by_date.get(date)
        if rec is not None:
            rec["regime"] = rj.get("regime")
            rec["exposure_budget_pct"] = rj.get("exposure_budget_pct")
        return rj

    def _scan(*a, **kw):
        rec = seans_by_date.get(_cur_close_date[0])
        if rec is not None:
            rec["n_scan_cagri"] += 1
        sig = _orig_scan(*a, **kw)
        if sig and rec is not None:
            rec["n_sinyal"] += 1
        return sig

    def _replay(*a, **kw):
        res = _orig_replay(*a, **kw)
        _res[0] = res
        return res

    backtest.brk.max_positions_at = _maxpos
    backtest.regime_mod.build_regime_json = _regime
    backtest.strat.scan_entry = _scan
    backtest.replay = _replay


# ---------------------------------------------------------------------------------------------
# SINIFLAMA (kartın DONUK kuralı) + dürüst kalıntı etiketleri
# ---------------------------------------------------------------------------------------------
def classify(rec: dict, no_trade_before: int) -> str:
    """Kartın 3 sınıfı + evren/de-risk ikilisine GİRMEYEN yapısal kalıntı (isinma / rejim_kapali).

    Kalıntıyı `evren_bagladi`ya İTMEK UYDURMA olurdu: ısınma ve rejim-kapalı günlerde aday_n=0'dır
    ama bunun nedeni EVREN değil (tarama HİÇ koşmadı). Kart kuralı aday_n<=acik_slot→evren derken
    tarama-koşan günü varsayar. Bu yüzden kural, uygulanabildiği yerde AYNEN uygulanır; kalıntı
    ayrıca ETİKETLENİR ve birincil paydadan çıkarılır (hepsi raporlanır — alt-örnek değil, tam
    tasnif). acik_slot<=0 kuralı rejim/ısınmadan ÖNCE gelir (kart: acik_slot<=0 → tavan_sifir,
    koşulsuz)."""
    acik_slot = rec["acik_slot"]
    if acik_slot <= 0:
        return "tavan_sifir"
    if rec["bar_i"] is not None and rec["bar_i"] < no_trade_before:
        return "isinma"                         # gösterge ısınması — tarama koşmaz (yapısal)
    if (rec["exposure_budget_pct"] or 0) <= 0:
        return "rejim_kapali"                   # rejim kapısı 0 bütçe — evren/de-risk DEĞİL
    # buraya gelen her seansta tarama koşmuştur (acik_slot>0 ⇒ slots>0 & budget>0 & bar_i>=ntb)
    return "evren_bagladi" if rec["aday_n"] <= acik_slot else "derisk_bagladi"


def bootstrap_ci(sess: list[dict], siniflar: list[str], n_iter: int = 5000,
                 seed: int = 20260809) -> dict:
    """Tarih-KÜMELİ (aylık blok) bootstrap %95 CI. Bitişik günler bağımlıdır (de-risk epizodları
    haftalar sürer); günleri iid çekmek CI'yi sahte-daraltır. Küme = takvim ayı (date[:7]); aylar
    yerine-koymalı çekilir, çekilen ayların TÜM birincil seansları havuzlanır, oranlar yeniden
    hesaplanır. Kart eşiği: %95, tarih-kümeli — DONUK."""
    rng = np.random.default_rng(seed)
    aylar: dict[str, list[str]] = {}
    for s in sess:
        aylar.setdefault(s["date"][:7], []).append(s["sinif"])
    ay_adlari = list(aylar.keys())
    ay_siniflar = {a: np.array(v) for a, v in aylar.items()}
    m = len(ay_adlari)
    props = {c: np.empty(n_iter) for c in siniflar}
    props["derisk+tavan"] = np.empty(n_iter)
    idx_all = np.arange(m)
    for i in range(n_iter):
        pick = rng.choice(idx_all, size=m, replace=True)
        pooled = np.concatenate([ay_siniflar[ay_adlari[j]] for j in pick])
        tot = len(pooled)
        for c in siniflar:
            props[c][i] = np.count_nonzero(pooled == c) / tot
        props["derisk+tavan"][i] = (np.count_nonzero(pooled == "derisk_bagladi") +
                                    np.count_nonzero(pooled == "tavan_sifir")) / tot
    out = {}
    for c, arr in props.items():
        out[c] = {"lo": round(float(np.percentile(arr, 2.5)), 4),
                  "hi": round(float(np.percentile(arr, 97.5)), 4),
                  "orta": round(float(np.median(arr)), 4)}
    out["_n_ay_kume"] = m
    return out


def main():
    _install_hooks()
    st = yaml.safe_load((STATE_DIR / "strategy.yaml").read_text())
    params = dict(st["params"])
    by_regime = st.get("params_by_regime") or None
    sv = int(st.get("version"))
    goal = config.goal()
    limits = goal["limits"]
    max_open = int(limits["max_open_positions"])
    no_trade_before = int(limits.get("no_trade_before_bars", 0))

    t0 = dt.datetime.now()
    bars, index = dataset.load_cached()
    # TEK, tam-dönem replay (walk_forward DEĞİL — o örtüşen çok replay koşar; biz seans başına
    # TEK gözlem istiyoruz). Motor bunu OKUNAN backtest.replay ile aynen koşar.
    backtest.replay(params, bars, index, goal, REPLAY_START, REPLAY_END,
                    strategy_version=sv, params_by_regime=by_regime, with_gate_detail=False)
    res = _res[0]
    assert res is not None, "replay sonucu yakalanamadı"

    # --- plan_log çapraz-kontrolü: aday_n (tam) ve silahli_n tarih başına --------------------
    plan_aday: dict[str, int] = {}       # tarih -> plan sayısı (= tam aday sayısı; her aday 1 plan)
    plan_silahli: dict[str, int] = {}    # tarih -> verdict != NO_GO
    for p in (res.plan_log or []):
        d = str(p.get("date"))[:10]
        plan_aday[d] = plan_aday.get(d, 0) + 1
        if p.get("gate_verdict") != "NO_GO":
            plan_silahli[d] = plan_silahli.get(d, 0) + 1
    cand_capped: dict[str, int] = {}     # candidate_log tarih başına (top-5 CAPLI — kartın literal kaynağı)
    for c in (res.candidate_log or []):
        d = str(c.get("date"))[:10]
        cand_capped[d] = cand_capped.get(d, 0) + 1

    # --- seans kayıtlarına aday_n / silahli_n işle + çapraz-kontrol -------------------------
    sess = sorted(seans_by_date.values(), key=lambda r: (r["bar_i"] if r["bar_i"] is not None else 0))
    scan_vs_plan_uyusmaz = []
    for r in sess:
        d = r["date"]
        r["aday_n"] = r["n_sinyal"]                       # TAM aday (tarama kancası; CAPSIZ)
        r["aday_n_capped5"] = cand_capped.get(d, 0)       # kartın literal candidate_log'u (<=5)
        r["silahli_n"] = plan_silahli.get(d, 0)
        r["plan_aday"] = plan_aday.get(d, 0)
        # ÇAPRAZ-KONTROL (YASA-6: üretilen kanıt tüketilir): tarama sinyali == plan_log aday sayısı?
        if r["n_sinyal"] != r["plan_aday"]:
            scan_vs_plan_uyusmaz.append({"date": d, "n_sinyal": r["n_sinyal"],
                                         "plan_aday": r["plan_aday"]})

    # --- sınıfla ---------------------------------------------------------------------------
    for r in sess:
        r["sinif"] = classify(r, no_trade_before)
        # kartın LİTERAL candidate_log'uyla (top-5 caplı) sınıf — yanlılık kıyası için
        r_capped = dict(r); r_capped["aday_n"] = r["aday_n_capped5"]
        r["sinif_capped5"] = classify(r_capped, no_trade_before)

    KART3 = ["tavan_sifir", "evren_bagladi", "derisk_bagladi"]
    KALINTI = ["isinma", "rejim_kapali"]
    n_top = len(sess)

    def dagit(records, key="sinif"):
        c = {}
        for r in records:
            c[r[key]] = c.get(r[key], 0) + 1
        return c

    tum_dagilim = dagit(sess)
    birincil = [r for r in sess if r["sinif"] in KART3]        # kartın 3 sınıfı = birincil payda
    n_bir = len(birincil)
    bir_dagilim = dagit(birincil)

    def yuzde(cnt, tot):
        return {k: {"n": v, "pct": round(100.0 * v / tot, 2)} for k, v in sorted(cnt.items())}

    ci = bootstrap_ci(birincil, KART3)
    ci_capped = None
    # caplı varyant birincil paydası (isinma/rejim aynı; sınıf farkı yalnız evren/de-risk sınırında)
    birincil_capped = [r for r in sess if r["sinif_capped5"] in KART3]
    if birincil_capped:
        for r in birincil_capped:
            r["_sc"] = r["sinif_capped5"]
        # bootstrap için geçici "sinif" alanı
        tmp = [{"date": r["date"], "sinif": r["sinif_capped5"]} for r in birincil_capped]
        ci_capped = bootstrap_ci(tmp, KART3)

    # --- rejim kırılımı (birincil payda) ---------------------------------------------------
    rejimler = sorted({r["regime"] for r in birincil if r["regime"]})
    rejim_kirilim = {}
    for reg in rejimler:
        alt = [r for r in birincil if r["regime"] == reg]
        d = dagit(alt)
        rejim_kirilim[reg] = {"n": len(alt), "dagilim": yuzde(d, len(alt)),
                              "baskin": max(d, key=d.get) if d else None}

    # --- yardımcı betimleyiciler (ROADMAP:425 %92 iddiasıyla uzlaştırma) --------------------
    n_all = len(sess)
    dd_aktif = sum(1 for r in sess if r["dd"] > 0.03)          # de-risk "aktif" (dd>%3)
    eff_lt5 = sum(1 for r in sess if r["eff_max_open"] < max_open)
    eff_eq1 = sum(1 for r in sess if r["eff_max_open"] == 1)
    eff_eq0 = sum(1 for r in sess if r["eff_max_open"] == 0)
    slot_le0 = sum(1 for r in sess if r["acik_slot"] <= 0)
    # tavan_sifir ∩ rejim_kapali örtüşmesi (şeffaflık)
    tavan_ve_rejim0 = sum(1 for r in sess
                          if r["acik_slot"] <= 0 and (r["exposure_budget_pct"] or 0) <= 0)

    out = {
        "kart": "EDG-2026-022",
        "modul": str(pathlib.Path(__file__).resolve()),
        "motor": str(MOTOR), "motor_yamasiz": True,
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sure_sn": round((dt.datetime.now() - t0).total_seconds(), 1),
        "replay": {"start": REPLAY_START, "end": REPLAY_END, "strategy_version": sv,
                   "params": params, "params_by_regime": by_regime,
                   "n_sembol": len(bars), "n_endeks_satir": int(len(index)),
                   "max_open": max_open, "no_trade_before": no_trade_before,
                   "derisk": "derisk_mult: full<=3%dd, lineer→0 @8%dd; eff_max_open=round(5·m)"},
        # ---- KILL#1 / BÜTÜNLÜK ----
        "kill1": {
            "eff_max_open_kalici_defterde": False,
            "eff_max_open_nereden": "motor yeniden koşuldu; max_positions_at çağrısında yakalandı",
            "aday_n_kaynak": "tarama kancası n_sinyal (CAPSIZ) == plan_log tarih-sayımı",
            "aday_n_candidate_log_capli": True,
            "candidate_log_cap": 5,
            "frame_okunamadi": _frame_miss[0],
            "tekrar_tarih": _dup,
            "scan_vs_plan_uyusmazlik_n": len(scan_vs_plan_uyusmaz),
            "scan_vs_plan_uyusmaz_ornek": scan_vs_plan_uyusmaz[:10],
            "gecerli": (_frame_miss[0] == 0 and not _dup and not scan_vs_plan_uyusmaz),
        },
        # ---- BETİMLEYİCİ ----
        "betim": {
            "n_seans_tum": n_all,
            "dd_aktif_gt3pct_n": dd_aktif, "dd_aktif_pct": round(100.0*dd_aktif/n_all, 2),
            "eff_max_open_lt5_n": eff_lt5, "eff_max_open_lt5_pct": round(100.0*eff_lt5/n_all, 2),
            "eff_max_open_eq1_n": eff_eq1, "eff_max_open_eq1_pct": round(100.0*eff_eq1/n_all, 2),
            "eff_max_open_eq0_n": eff_eq0, "eff_max_open_eq0_pct": round(100.0*eff_eq0/n_all, 2),
            "acik_slot_le0_n": slot_le0, "acik_slot_le0_pct": round(100.0*slot_le0/n_all, 2),
            "tavan_sifir_ve_rejim0_ortusme_n": tavan_ve_rejim0,
        },
        # ---- TASNİF ----
        "tasnif_tum_seans": {"n": n_all, "dagilim": yuzde(tum_dagilim, n_all)},
        "birincil_payda_aciklama": ("kartın 3 sınıfı (tavan_sifir+evren+derisk). isinma "
                                    "(gösterge ısınması, bar_i<no_trade_before) ve rejim_kapali "
                                    "(exposure_budget=0) evren/de-risk ikilisine girmez → çıkarıldı, "
                                    "ama tasnif_tum_seans'ta görünür (alt-örnek değil, tam tasnif)."),
        "birincil": {"n": n_bir, "dagilim": yuzde(bir_dagilim, n_bir)},
        "ci95_tarih_kumeli": ci,
        "ci95_capped5_variant": ci_capped,
        "capped5_aciklama": ("kart aday_n kaynağını 'candidate_log' diye adlandırır AMA "
                             "candidate_log backtest.py:333'te top-5 CAPLIdır → aday_n<=5 yapay "
                             "tavanı evren_bagladi'yı ŞİŞİRİR. Doğru kaynak plan_log/tarama "
                             "(capsiz). Bu varyant kartın literal kaynağının yanlılığını gösterir."),
        "rejim_kirilim": rejim_kirilim,
        "success_metric_okuma": {
            "evren_ci": ci["evren_bagladi"],
            "derisk_arti_tavan_ci": ci["derisk+tavan"],
            "kural": "evren CI>%50 → FINVIZ değerli; (derisk+tavan) CI>%50 → FINVIZ boşa gider",
        },
    }

    outp = SANDBOX / "sonuc.json"
    outp.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))
    # ham seans defteri (analiz/denetim için — YASA-6 okuyucusu: bu modül + rapor)
    (SANDBOX / "seanslar.json").write_text(
        json.dumps(sess, ensure_ascii=False, default=str))

    # ---- yapısal özet (stdout) ----
    print("\n==================== EDG-022 ÖLÇÜM ÖZETİ ====================")
    print(f"replay {REPLAY_START}→{REPLAY_END}  sv={sv}  sembol={len(bars)}  süre={out['sure_sn']}s")
    print(f"KILL#1 geçerli={out['kill1']['gecerli']}  frame_miss={_frame_miss[0]}  "
          f"dup={len(_dup)}  scan!=plan={len(scan_vs_plan_uyusmaz)}")
    print(f"eff_max_open: <5 %{out['betim']['eff_max_open_lt5_pct']}  ==1 %{out['betim']['eff_max_open_eq1_pct']}  "
          f"==0 %{out['betim']['eff_max_open_eq0_pct']}   dd>3%% %{out['betim']['dd_aktif_pct']}")
    print(f"toplam seans={n_all}  birincil(3 sınıf)={n_bir}")
    print("TÜM SEANS tasnif:", {k: v["pct"] for k, v in out["tasnif_tum_seans"]["dagilim"].items()})
    print("BİRİNCİL tasnif :", {k: v["pct"] for k, v in out["birincil"]["dagilim"].items()})
    print("CI95 (tarih-kümeli, birincil):")
    for c in KART3 + ["derisk+tavan"]:
        print(f"   {c:16s} [{ci[c]['lo']*100:5.1f}%, {ci[c]['hi']*100:5.1f}%]  orta {ci[c]['orta']*100:4.1f}%")
    if ci_capped:
        print("CI95 capped5 (kartın literal candidate_log kaynağı — YANLI):")
        for c in KART3:
            print(f"   {c:16s} [{ci_capped[c]['lo']*100:5.1f}%, {ci_capped[c]['hi']*100:5.1f}%]")
    print("REJİM KIRILIMI (birincil):")
    for reg, v in rejim_kirilim.items():
        print(f"   {reg:12s} n={v['n']:5d} baskın={v['baskin']:14s} "
              + " ".join(f"{k}={vv['pct']}%" for k, vv in v["dagilim"].items()))
    print(f"\nyazıldı: {outp}")
    print("============================================================\n")


if __name__ == "__main__":
    main()

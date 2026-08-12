"""EDG-2026-023 — DE-RISK RAMPA BANDI · ölçüm aracı (2026-08-12)

Kart: research/cards/EDG-2026-023-derisk-rampa-bandi.yaml (OKU-DOKUNMA; hüküm Rol-1'in).
Rol: ÖLÇÜM ajanı. Bu modül HÜKÜM VERMEZ, karta dokunmaz, git/canlı/broker/state'e YAZMAZ.
Şasi: EDG-022 (research/olcumler/edg022_evren_kisit_2026-08-09/olcum.py) — kanca deseni,
sınıf kuralı ve ay-kümeli bootstrap oradan AYNEN alındı (tutarlılık çivisi kill#2'nin şartı).

İKİ KOŞUM (kart features_asof, DONUK):
  (A) taban_3_8    : mevcut rampa (tam<=%3 dd, lineer→0 @%8) — motor OLDUĞU GİBİ, sıfır yama.
                     kill#2: EDG-022'nin yayınlı birincil tavan_sifir'ı %57.54 (389/676)
                     ±2pp bandında YENİDEN üretilmeli, yoksa ölçüm GEÇERSİZ (şasi bozulmuş).
  (B) varyant_15_36: rampa (tam<=%15 dd, lineer→0 @%36) — operatör seçimi 2026-08-12.

RAMPA ENJEKSİYONU — BEYAN (kart 'motor YAMASIZ' ilkesi + brief):
  Tam-kapasite eşiği 0.03, broker.derisk_mult GÖVDESİNDE sabittir (broker.py:220,224);
  taban eşiği DERISK_FLOOR_DD modül sabitidir. Motor CONFIG/PARAM enjeksiyon yüzeyi SUNMAZ
  → varyant koşumunda `meridian.broker.derisk_mult` modül-özniteliği, ÖLÇÜM MODÜLÜ İÇİNDE,
  orijinal formülün birebir parametrize kopyasıyla DEĞİŞTİRİLİR (monkeypatch). Motor
  DOSYASINA tek bayt dokunulmaz. Yayılım kanıtlı ve tekildir: replay yolunda rampayı okuyan
  iki uç var — backtest.py:224 `brk.derisk_mult` (çağrı anında modül-öznitelik çözümü) ve
  broker.max_positions_at:231 içindeki `derisk_mult` (modül-global çözümü) — ikisi de yamayı
  görür. TABAN koşumda HİÇBİR yama yok (orijinal fonksiyon nesnesi doğrulanır).

TANIMLAR (ölçümden ÖNCE donduruldu; sonuç görüldükten sonra değişmez):
  islem            = kapanmış işlem satırı (broker.closed; eod/delisted markout DAHİL).
  ay kümesi        = ts_open[:7] (giriş ayı — rampanın kıstığı şey GİRİŞtir).
  islem CI (A↔B)   = tarih-kümeli EŞLENİK bootstrap: aynı ay çekilişi iki koşuma birden
                     uygulanır (aylar yerine-koymalı, 5000 iter, seed 20260812); fark=B−A.
  doluluk          = OPEN fazında (fill'den ÖNCE) açık pozisyon sayısı toplamı (pozisyon-gün);
                     ikincil tanım: Σ bars_held (kapanmış işlemlerden).
  tavan_sifir oranı= EDG-022 birincil payda (kartın 3 sınıfı) — sınıf kuralı DONUK, aynen.
  max-dd           = motor-kanonik score.score_detail.max_drawdown (kapalı-işlem eğrisi ile
                     günlük M2M eğrisinin KÖTÜSÜ — denetim #6 tanımı). kill#3 BUNUN üstünden
                     okunur; yalnız-M2M ayrıca raporlanır (şeffaflık, ikinci eşik değil).
  net P&L          = M2M equity eğrisi son değer − START_EQUITY; çapraz: Σ pnl_dollars.
  ort R            = score_detail.avg_r (Σ r_multiple / n ile aynı).

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen = None + neden); YASA-4 (sessiz-yutma işaretli +
gerekçe); YASA-6 (üretilen her artefaktın okuyucusu var: sonuc_*.json'ları `birlestir` tüketir,
sonuc.json'u dönüş raporu + Rol-1 tüketir). SALT-OKUMA: config.STATE koşum-başına izole
sandbox'a çevrilir; barlar sembolik bağla canlı önbellekten SALT-OKUNUR; canlı state'e ve
motor dosyalarına tek bayt yazılmaz. meridian.loop / counterfactual / cf_backfill İTHAL
EDİLMEZ (paralel ajan düzenliyor) — koşum sonunda sys.modules ile KANITLANIR.

KULLANIM:
  olcum.py taban            # koşum A → sonuc_taban.json + seanslar_taban.json + islemler_taban.json
  olcum.py varyant          # koşum B → sonuc_varyant.json + ...
  olcum.py birlestir        # A+B → eşlenik bootstrap CI'ları + kill tabloları → sonuc.json
  (--smoke: kısa pencere 2022-01-01→2022-06-30, çıktılar smoke/ altına — şasi provası)
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import shutil
import sys

SANDBOX = pathlib.Path(__file__).resolve().parent
REPO = SANDBOX.parents[2]                      # research/olcumler/<bu>/ -> repo kökü
EDG022 = REPO / "research/olcumler/edg022_evren_kisit_2026-08-09"

# tek-iş parçacığı: determinizm + ölçüm gürültüsüzlüğü (EDG-022 ile aynı)
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

REPLAY_START = "2022-01-01"
REPLAY_END = "2026-07-30"                      # kart: 2022-01 → 2026-07 (EDG-022 ile aynı)
BOOT_SEED = 20260812
BOOT_ITER = 5000

# rampa bantları (kart parameter_grid, DONUK)
RAMPALAR = {
    "taban":   {"tam_dd": 0.03, "sifir_dd": 0.08, "yama": False},   # motor orijinali — yama YOK
    "varyant": {"tam_dd": 0.15, "sifir_dd": 0.36, "yama": True},    # monkeypatch (beyan yukarıda)
}

# kill#2 çivisi (kart, DONUK): EDG-022 yayınlı birincil tavan_sifir %57.5 ± 2pp
KILL2_HEDEF_PCT = 57.5
KILL2_TOL_PP = 2.0
EDG022_YAYIN = {"tavan_sifir_pct": 57.54, "n_birincil": 676, "n_tavan": 389}

KART3 = ["tavan_sifir", "evren_bagladi", "derisk_bagladi"]


def _sha(p: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    except OSError:
        return None    # ölçülemedi (dosya yok/okunamadı) — None, uydurma özet değil


# ---------------------------------------------------------------------------------------------
# SANDBOX HAZIRLIĞI — koşum başına izole state (EDG-022'nin DONMUŞ config kopyalarından)
# ---------------------------------------------------------------------------------------------
def hazirla(run: str) -> pathlib.Path:
    st = SANDBOX / f"state_{run}"
    st.mkdir(exist_ok=True)
    (st / "history").mkdir(exist_ok=True)
    bars = st / "bars"
    if not bars.exists():
        bars.symlink_to(REPO / "state" / "bars")          # SALT-OKUNUR canlı önbellek
    for f in ("goal.yaml", "strategy.yaml", "bounds.yaml"):
        dst = st / f
        if not dst.exists():
            # kaynak = EDG-022'nin DONMUŞ kopyaları (tutarlılık çivisi). 2026-08-12 diff'i:
            # üçü de repo state/ ile bayt-aynı; sha'lar sonuc bloğunda yine de kayıtlı.
            shutil.copyfile(EDG022 / "state" / f, dst)
    return st


# ---------------------------------------------------------------------------------------------
# RAMPA — orijinal formülün birebir parametrize kopyası (yalnız varyantta devreye girer)
# ---------------------------------------------------------------------------------------------
def _rampa_fn(tam_dd: float, sifir_dd: float):
    def derisk_mult_param(equity: float, peak: float) -> float:
        # broker.derisk_mult'un birebir aynası — yalnız 0.03/DERISK_FLOOR_DD yerine parametre.
        if peak <= 0:
            return 1.0
        dd = (peak - equity) / peak
        if dd <= tam_dd:
            return 1.0
        if dd >= sifir_dd:
            return 0.0
        return round(1.0 - (dd - tam_dd) / (sifir_dd - tam_dd), 4)
    return derisk_mult_param


# ---------------------------------------------------------------------------------------------
# SINIFLAMA — EDG-022'nin DONUK kuralı (AYNEN; gerekçeler kaynak modülde)
# ---------------------------------------------------------------------------------------------
def classify(rec: dict, no_trade_before: int) -> str:
    acik_slot = rec["acik_slot"]
    if acik_slot <= 0:
        return "tavan_sifir"
    if rec["bar_i"] is not None and rec["bar_i"] < no_trade_before:
        return "isinma"
    if (rec["exposure_budget_pct"] or 0) <= 0:
        return "rejim_kapali"
    return "evren_bagladi" if rec["aday_n"] <= acik_slot else "derisk_bagladi"


def bootstrap_ci(sess: list[dict], siniflar: list[str], n_iter: int = BOOT_ITER,
                 seed: int = BOOT_SEED) -> dict:
    """Ay-kümeli bootstrap %95 CI — EDG-022'nin fonksiyonu AYNEN (bitişik günler bağımlı;
    iid gün çekimi CI'yi sahte-daraltır). Tek fark: seed bu kartın tarihi (beyanlı)."""
    import numpy as np
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


# ---------------------------------------------------------------------------------------------
# TEK KOŞUM (taban | varyant)
# ---------------------------------------------------------------------------------------------
def kosum(run: str, smoke: bool = False):
    assert run in RAMPALAR, f"bilinmeyen koşum: {run}"
    rampa = RAMPALAR[run]
    outdir = (SANDBOX / "smoke") if smoke else SANDBOX
    outdir.mkdir(exist_ok=True)
    r_start, r_end = (REPLAY_START, "2022-06-30") if smoke else (REPLAY_START, REPLAY_END)

    st_dir = hazirla(run + ("_smoke" if smoke else ""))
    sys.path.insert(0, str(REPO))

    from meridian import config
    # SALT-OKUMA İZOLASYONU: her yazım (obs.events, history) sandbox'a düşer, canlı state'e DEĞİL
    config.STATE = st_dir
    config.BARS = st_dir / "bars"
    config.HISTORY = st_dir / "history"

    import numpy as np                     # noqa: F401  (bootstrap_ci içinde kullanılır)
    import yaml
    from meridian import backtest, dataset, score as score_mod

    # motorun yamalanmadığını çivile (EDG-022 emniyeti) + YASAKLI modül kanıtı (ithal ÖNCESİ)
    assert not hasattr(backtest, "wpg_overlay_day"), "motor YAMALI görünüyor — ölçüm geçersiz"
    YASAK = ("meridian.loop", "meridian.counterfactual", "meridian.cf_backfill")
    assert not [m for m in sys.modules if m in YASAK], "yasaklı modül ithal edilmiş"

    brk = backtest.brk                     # meridian.broker modülü
    ORIJ_DERISK = brk.derisk_mult          # orijinal fonksiyon nesnesi (taban doğrulaması)

    # ---- rampa kurulumu + öz-sınama (koşum ÖNCESİ) ------------------------------------------
    if rampa["yama"]:
        brk.derisk_mult = _rampa_fn(rampa["tam_dd"], rampa["sifir_dd"])
        # yama semantiği: dd=%10 tam boy; dd=%20 → 1-(0.05/0.21)=0.7619; dd>=%36 → 0
        assert brk.derisk_mult(90.0, 100.0) == 1.0
        assert abs(brk.derisk_mult(80.0, 100.0) - 0.7619) < 1e-9
        assert brk.derisk_mult(64.0, 100.0) == 0.0
        # yayılım kanıtı: max_positions_at İÇİNDEKİ global çözüm de yamayı görüyor
        assert brk.max_positions_at(80.0, 100.0, 5) == 4      # round(5*0.7619)=4 (taban olsaydı 0)
    else:
        assert brk.derisk_mult is ORIJ_DERISK and brk.DERISK_FLOOR_DD == 0.08
        assert brk.derisk_mult(97.5, 100.0) == 1.0            # dd %2.5 → tam boy
        assert abs(brk.derisk_mult(94.5, 100.0) - 0.5) < 1e-9  # dd %5.5 → 0.5
        assert brk.derisk_mult(92.0, 100.0) == 0.0            # dd %8 → 0
        assert brk.max_positions_at(80.0, 100.0, 5) == 0      # dd %20 → tavan 0 (taban davranışı)

    # ---- kancalar (EDG-022 deseni: sarmalayıcı, motoru DEĞİŞTİRMEZ) -------------------------
    seans_by_date: dict[str, dict] = {}
    _cur_close_date = [None]
    _dup: list[str] = []
    _frame_miss = [0]

    _orig_maxpos = brk.max_positions_at
    _orig_regime = backtest.regime_mod.build_regime_json
    _orig_scan = backtest.strat.scan_entry

    def _maxpos(equity, peak, base_max):
        n = _orig_maxpos(equity, peak, base_max)              # GERÇEK eff_max_open (yürürlükteki rampa)
        fr = sys._getframe(1)
        loc = fr.f_locals
        d = loc.get("d")
        bar_i = loc.get("bar_i")
        broker = loc.get("broker")
        if d is None or broker is None:
            _frame_miss[0] += 1                               # sessiz-yutma DEĞİL: sayılır, sonda geçerlilik bozar
            return n
        date = str(d.date())
        n_acik = len(broker.positions)                        # açılışta, fill'den ÖNCE
        dd = ((peak - equity) / peak) if peak and peak > 0 else 0.0
        rec = {
            "date": date, "bar_i": int(bar_i) if bar_i is not None else None,
            "eq_open": round(float(equity), 2), "peak_equity": round(float(peak), 2),
            "dd": round(float(dd), 6), "base_max_open": int(base_max),
            "eff_max_open": int(n), "n_acik": int(n_acik),
            "acik_slot": int(n) - int(n_acik),
            # yürürlükteki rampanın size çarpanı — motorun backtest.py:224'te aldığı değerin
            # AYNI fonksiyon + AYNI girdilerle yakalanışı (türetme değil, aynı kaynaktan okuma)
            "size_mult": float(brk.derisk_mult(equity, peak)),
            "regime": None, "exposure_budget_pct": None,
            "n_scan_cagri": 0, "n_sinyal": 0,
        }
        if date in seans_by_date:
            _dup.append(date)
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

    brk.max_positions_at = _maxpos
    backtest.regime_mod.build_regime_json = _regime
    backtest.strat.scan_entry = _scan

    # ---- girdiler ---------------------------------------------------------------------------
    stg = yaml.safe_load((st_dir / "strategy.yaml").read_text())
    params = dict(stg["params"])
    by_regime = stg.get("params_by_regime") or None
    sv = int(stg.get("version"))
    goal = config.goal()
    limits = goal["limits"]
    max_open = int(limits["max_open_positions"])
    no_trade_before = int(limits.get("no_trade_before_bars", 0))

    t0 = dt.datetime.now()
    bars, index = dataset.load_cached()
    res = backtest.replay(params, bars, index, goal, r_start, r_end,
                          strategy_version=sv, params_by_regime=by_regime, with_gate_detail=False)
    sure = round((dt.datetime.now() - t0).total_seconds(), 1)

    # koşum sonrası kanıt: yasaklı modüller replay SIRASINDA da yüklenmedi
    yasak_yuklu = [m for m in sys.modules if m in YASAK]

    # ---- plan_log çapraz-kontrolü (EDG-022 aynen) -------------------------------------------
    plan_aday: dict[str, int] = {}
    plan_silahli: dict[str, int] = {}
    for p in (res.plan_log or []):
        dts = str(p.get("date"))[:10]
        plan_aday[dts] = plan_aday.get(dts, 0) + 1
        if p.get("gate_verdict") != "NO_GO":
            plan_silahli[dts] = plan_silahli.get(dts, 0) + 1

    sess = sorted(seans_by_date.values(),
                  key=lambda r: (r["bar_i"] if r["bar_i"] is not None else 0))
    scan_vs_plan = []
    for r in sess:
        r["aday_n"] = r["n_sinyal"]                           # TAM aday (CAPSIZ — EDG-022 birincil kaynağı)
        r["silahli_n"] = plan_silahli.get(r["date"], 0)
        r["plan_aday"] = plan_aday.get(r["date"], 0)
        if r["n_sinyal"] != r["plan_aday"]:
            scan_vs_plan.append({"date": r["date"], "n_sinyal": r["n_sinyal"],
                                 "plan_aday": r["plan_aday"]})
        r["sinif"] = classify(r, no_trade_before)

    n_all = len(sess)
    birincil = [r for r in sess if r["sinif"] in KART3]
    n_bir = len(birincil)

    def dagit(records):
        c: dict[str, int] = {}
        for r in records:
            c[r["sinif"]] = c.get(r["sinif"], 0) + 1
        return c

    def yuzde(cnt, tot):
        return {k: {"n": v, "pct": round(100.0 * v / tot, 2)} for k, v in sorted(cnt.items())}

    ci = bootstrap_ci(birincil, KART3) if birincil else None

    # ---- işlem/doluluk/performans metrikleri ------------------------------------------------
    trades = res.trades or []
    n_islem = len(trades)
    aylik: dict[str, int] = {}
    for t in trades:
        aylik[str(t["ts_open"])[:7]] = aylik.get(str(t["ts_open"])[:7], 0) + 1
    pencere_gun = (dt.date.fromisoformat(r_end) - dt.date.fromisoformat(r_start)).days
    yil = pencere_gun / 365.25

    eq_vals = [float(e) for _, e in (res.equity or [])]
    net_pnl_equity = round(eq_vals[-1] - score_mod.START_EQUITY, 2) if eq_vals else None
    net_pnl_trades = round(sum(float(t.get("pnl_dollars", 0.0)) for t in trades), 2)
    maxdd_m2m = round(score_mod.max_drawdown(eq_vals), 4) if eq_vals else None
    detail = score_mod.score_detail(trades, goal, span_days=pencere_gun, mtm_equity=res.equity)

    doluluk_pozgun = sum(r["n_acik"] for r in sess)           # OPEN-fazı tanımı (birincil)
    doluluk_barsheld = sum(int(t.get("bars_held") or 0) for t in trades)
    exit_dist: dict[str, int] = {}
    for t in trades:
        exit_dist[str(t.get("exit_reason"))] = exit_dist.get(str(t.get("exit_reason")), 0) + 1

    eff_eq0 = sum(1 for r in sess if r["eff_max_open"] == 0)
    eff_eq1 = sum(1 for r in sess if r["eff_max_open"] == 1)
    eff_lt = sum(1 for r in sess if r["eff_max_open"] < max_open)
    slot_le0 = sum(1 for r in sess if r["acik_slot"] <= 0)
    dd_gt_tam = sum(1 for r in sess if r["dd"] > rampa["tam_dd"])
    size0 = sum(1 for r in sess if r["size_mult"] <= 0.0)

    tavan_pct_bir = round(100.0 * sum(1 for r in birincil if r["sinif"] == "tavan_sifir")
                          / n_bir, 2) if n_bir else None

    out = {
        "kart": "EDG-2026-023", "kosum": run, "smoke": smoke,
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sure_sn": sure,
        "rampa": {"tam_dd": rampa["tam_dd"], "sifir_dd": rampa["sifir_dd"],
                  "enjeksiyon": ("MONKEYPATCH — ölçüm modülü içinde broker.derisk_mult "
                                 "modül-özniteliği değiştirildi; motor DOSYASI değişmedi. "
                                 "Gerekçe: tam-eşik 0.03 fonksiyon gövdesinde sabit, motorda "
                                 "config/param enjeksiyon yüzeyi yok (beyan, kart+brief uyarınca)")
                  if rampa["yama"] else "YOK — motor orijinali (yama sıfır)"},
        "motor_sha256_16": {f: _sha(REPO / "meridian" / f)
                            for f in ("broker.py", "backtest.py", "strategy.py")},
        "config_sha256_16": {f: {"sandbox": _sha(st_dir / f),
                                 "edg022": _sha(EDG022 / "state" / f),
                                 "repo_state": _sha(REPO / "state" / f)}
                             for f in ("goal.yaml", "strategy.yaml", "bounds.yaml")},
        "replay": {"start": r_start, "end": r_end, "strategy_version": sv,
                   "params_by_regime": bool(by_regime), "n_sembol": len(bars),
                   "n_endeks_satir": int(len(index)), "max_open": max_open,
                   "no_trade_before": no_trade_before,
                   "cost_model": {"slippage_bps": float(goal.get("slippage_bps", 5)),
                                  "commission_per_share": float(goal.get("commission_per_share", 0.0)),
                                  "not": "motorun kendi maliyet modeli — dokunulmadı (kart: değişmez)"}},
        "butunluk": {
            "frame_okunamadi": _frame_miss[0], "tekrar_tarih": _dup,
            "scan_vs_plan_uyusmazlik_n": len(scan_vs_plan),
            "scan_vs_plan_ornek": scan_vs_plan[:10],
            "yasakli_modul_yuklendi": yasak_yuklu,             # [] olmalı
            "gecerli": (_frame_miss[0] == 0 and not _dup and not scan_vs_plan
                        and not yasak_yuklu),
        },
        "islem": {
            "n": n_islem, "islem_yil": round(n_islem / yil, 2),
            "aylik_ts_open": dict(sorted(aylik.items())),
            "silahlanan_plan": sum(plan_silahli.values()),
            "toplam_plan": sum(plan_aday.values()),
            "entry_rejects": res.entry_rejects,
            "exit_reason_dagilim": dict(sorted(exit_dist.items(), key=lambda kv: -kv[1])),
        },
        "performans": {
            "net_pnl_equity": net_pnl_equity, "net_pnl_trades": net_pnl_trades,
            "maxdd_kanonik": detail.get("max_drawdown"),       # kill#3'ün okuduğu sayı
            "maxdd_m2m": maxdd_m2m,
            "avg_r": detail.get("avg_r"), "win_rate": detail.get("win_rate"),
            "sharpe": detail.get("sharpe"), "sharpe_measurable": detail.get("sharpe_measurable"),
            "score": detail.get("score"), "score_n": detail.get("n"),
            "total_return": detail.get("total_return"),
        },
        "doluluk": {"pozisyon_gun_open_fazi": doluluk_pozgun,
                    "ort_acik_pozisyon": round(doluluk_pozgun / n_all, 3) if n_all else None,
                    "toplam_bars_held": doluluk_barsheld},
        "betim": {
            "n_seans": n_all, "dd_gt_tam_esik_n": dd_gt_tam,
            "eff_max_open_eq0_n": eff_eq0, "eff_max_open_eq1_n": eff_eq1,
            "eff_max_open_lt_base_n": eff_lt, "acik_slot_le0_n": slot_le0,
            "size_mult_0_n": size0,
        },
        "tasnif_tum_seans": {"n": n_all, "dagilim": yuzde(dagit(sess), n_all)},
        "birincil": {"n": n_bir, "dagilim": yuzde(dagit(birincil), n_bir) if n_bir else {},
                     "tavan_sifir_pct": tavan_pct_bir},
        "ci95_ay_kumeli": ci,
    }

    if run == "taban" and not smoke:
        fark_pp = (round(abs(tavan_pct_bir - KILL2_HEDEF_PCT), 2)
                   if tavan_pct_bir is not None else None)
        out["kill2"] = {
            "civi": f"EDG-022 yayınlı birincil tavan_sifir %{KILL2_HEDEF_PCT} ± {KILL2_TOL_PP}pp",
            "edg022_yayin": EDG022_YAYIN,
            "taban_tavan_sifir_pct": tavan_pct_bir, "fark_pp": fark_pp,
            "evren_251": (len(bars) == 251),
            "config_ayni_edg022": all(
                out["config_sha256_16"][f]["sandbox"] == out["config_sha256_16"][f]["edg022"]
                for f in ("goal.yaml", "strategy.yaml", "bounds.yaml")),
            "gecti": (fark_pp is not None and fark_pp <= KILL2_TOL_PP
                      and len(bars) == 251 and out["butunluk"]["gecerli"]),
        }

    ek = "_smoke" if smoke else ""
    (outdir / f"sonuc_{run}{ek}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str))
    (outdir / f"seanslar_{run}{ek}.json").write_text(
        json.dumps(sess, ensure_ascii=False, default=str))
    slim = [{k: t.get(k) for k in ("ts_open", "ts_close", "ticker", "r_multiple",
                                   "pnl_dollars", "exit_reason", "bars_held", "regime",
                                   "setup", "qty")} for t in trades]
    (outdir / f"islemler_{run}{ek}.json").write_text(
        json.dumps(slim, ensure_ascii=False, default=str))

    print(f"\n=========== EDG-023 KOŞUM [{run}{ek}] ===========")
    print(f"replay {r_start}→{r_end}  sv={sv}  sembol={len(bars)}  süre={sure}s")
    print(f"bütünlük geçerli={out['butunluk']['gecerli']}  frame_miss={_frame_miss[0]} "
          f"dup={len(_dup)} scan!=plan={len(scan_vs_plan)} yasak={yasak_yuklu}")
    print(f"işlem n={n_islem} ({out['islem']['islem_yil']}/yıl)  net_pnl={net_pnl_equity}  "
          f"maxdd_kanonik={detail.get('max_drawdown')}  maxdd_m2m={maxdd_m2m}  "
          f"avg_r={detail.get('avg_r')}")
    print(f"birincil n={n_bir}  tavan_sifir %{tavan_pct_bir}")
    if "kill2" in out:
        print(f"KILL#2: fark={out['kill2']['fark_pp']}pp  geçti={out['kill2']['gecti']}")
    print(f"yazıldı: {outdir}/sonuc_{run}{ek}.json")


# ---------------------------------------------------------------------------------------------
# BİRLEŞTİR — A↔B eşlenik (ay-kümeli) bootstrap + kill tabloları → sonuc.json
# ---------------------------------------------------------------------------------------------
def birlestir():
    import numpy as np
    S = {}
    for run in ("taban", "varyant"):
        S[run] = {
            "sonuc": json.loads((SANDBOX / f"sonuc_{run}.json").read_text()),
            "seans": json.loads((SANDBOX / f"seanslar_{run}.json").read_text()),
            "islem": json.loads((SANDBOX / f"islemler_{run}.json").read_text()),
        }

    # takvim kimliği: iki koşum aynı seans kümesinde koşmuş olmalı
    tarih_t = [s["date"] for s in S["taban"]["seans"]]
    tarih_v = [s["date"] for s in S["varyant"]["seans"]]
    takvim_ayni = (tarih_t == tarih_v)
    aylar = sorted({d[:7] for d in tarih_t})
    M = len(aylar)

    # ay → işlem sayısı (ts_open) ve ay → birincil sınıf listesi
    def ay_islem(islemler):
        c = {a: 0 for a in aylar}
        for t in islemler:
            a = str(t["ts_open"])[:7]
            if a in c:
                c[a] += 1
        return np.array([c[a] for a in aylar], dtype=float)

    def ay_birincil(seans):
        by = {a: [] for a in aylar}
        for s in seans:
            if s["sinif"] in KART3:
                by[s["date"][:7]].append(1.0 if s["sinif"] == "tavan_sifir" else 0.0)
        return {a: np.array(v) for a, v in by.items()}

    cA, cB = ay_islem(S["taban"]["islem"]), ay_islem(S["varyant"]["islem"])
    pA, pB = ay_birincil(S["taban"]["seans"]), ay_birincil(S["varyant"]["seans"])

    rng = np.random.default_rng(BOOT_SEED)
    fark = np.empty(BOOT_ITER)
    oran = []                                   # cA*=0 iterasyonu atlanır (sayısı raporlanır)
    tavan_fark_pp = np.empty(BOOT_ITER)
    tavan_bos = 0                               # birincil payda boş kalan iterasyon (olmamalı)
    idx_all = np.arange(M)
    for i in range(BOOT_ITER):
        pick = rng.choice(idx_all, size=M, replace=True)     # EŞLENİK: aynı çekiliş iki koşuma
        tA, tB = float(cA[pick].sum()), float(cB[pick].sum())
        fark[i] = tB - tA
        if tA > 0:
            oran.append(tB / tA)
        sA = np.concatenate([pA[aylar[j]] for j in pick]) if M else np.array([])
        sB = np.concatenate([pB[aylar[j]] for j in pick]) if M else np.array([])
        if len(sA) and len(sB):
            tavan_fark_pp[i] = 100.0 * (sB.mean() - sA.mean())
        else:
            tavan_fark_pp[i] = np.nan
            tavan_bos += 1

    def ci95(arr):
        a = np.asarray([x for x in arr if x == x])           # NaN dışarı (sayısı ayrı raporlı)
        if not len(a):
            return None                                       # ölçülemedi
        return {"lo": round(float(np.percentile(a, 2.5)), 3),
                "hi": round(float(np.percentile(a, 97.5)), 3),
                "orta": round(float(np.median(a)), 3)}

    fark_ci, oran_ci, tavan_ci = ci95(fark), ci95(oran), ci95(tavan_fark_pp)
    nT, nV = int(cA.sum()), int(cB.sum())

    st_, sv_ = S["taban"]["sonuc"], S["varyant"]["sonuc"]
    perf_t, perf_v = st_["performans"], sv_["performans"]

    # kill bayrakları — kartın DONUK eşikleri; HÜKÜM DEĞİL, koşul değerinin kaydı
    kill2 = st_.get("kill2")
    artis_ci_0_disi = (fark_ci is not None and fark_ci["lo"] > 0)
    kill1_tetiklendi = not artis_ci_0_disi
    ddt, ddv = perf_t.get("maxdd_kanonik"), perf_v.get("maxdd_kanonik")
    kill3 = {
        "esik": "maxdd_varyant > 2 × maxdd_taban (kanonik: score_detail — kapalı∨M2M kötüsü)",
        "maxdd_taban": ddt, "maxdd_varyant": ddv,
        "oran": round(ddv / ddt, 3) if (ddt not in (None, 0) and ddv is not None) else None,
        "tetiklendi": (ddv > 2 * ddt) if (ddt not in (None, 0) and ddv is not None) else None,
        "m2m_yalniz": {"taban": perf_t.get("maxdd_m2m"), "varyant": perf_v.get("maxdd_m2m"),
                       "tetiklendi": (perf_v["maxdd_m2m"] > 2 * perf_t["maxdd_m2m"])
                       if (perf_t.get("maxdd_m2m") not in (None, 0)
                           and perf_v.get("maxdd_m2m") is not None) else None},
    }

    def satir(anahtar, *yol):
        def cek(s):
            v = s
            for k in yol:
                v = v.get(k) if isinstance(v, dict) else None
                if v is None:
                    return None
            return v
        return {"taban": cek(st_), "varyant": cek(sv_)}

    tablo = {
        "islem_n": {"taban": nT, "varyant": nV, "fark": nV - nT,
                    "fark_pct": round(100.0 * (nV - nT) / nT, 1) if nT else None},
        "islem_yil": satir("islem_yil", "islem", "islem_yil"),
        "islem_fark_ci95_ay_kumeli_eslenik": fark_ci,
        "islem_oran_ci95": oran_ci,
        "tavan_sifir_birincil_pct": satir("t", "birincil", "tavan_sifir_pct"),
        "tavan_sifir_fark_pp_ci95": tavan_ci,
        "birincil_n": satir("n", "birincil", "n"),
        "tasnif_birincil": satir("d", "birincil", "dagilim"),
        "tasnif_tum_seans": satir("d", "tasnif_tum_seans", "dagilim"),
        "ci95_ay_kumeli_kosum_ici": {"taban": st_.get("ci95_ay_kumeli"),
                                     "varyant": sv_.get("ci95_ay_kumeli")},
        "net_pnl_equity": satir("p", "performans", "net_pnl_equity"),
        "net_pnl_trades": satir("p", "performans", "net_pnl_trades"),
        "maxdd_kanonik": satir("p", "performans", "maxdd_kanonik"),
        "maxdd_m2m": satir("p", "performans", "maxdd_m2m"),
        "avg_r": satir("p", "performans", "avg_r"),
        "win_rate": satir("p", "performans", "win_rate"),
        "sharpe": satir("p", "performans", "sharpe"),
        "score": satir("p", "performans", "score"),
        "doluluk_pozisyon_gun": satir("d", "doluluk", "pozisyon_gun_open_fazi"),
        "ort_acik_pozisyon": satir("d", "doluluk", "ort_acik_pozisyon"),
        "toplam_bars_held": satir("d", "doluluk", "toplam_bars_held"),
        "silahlanan_plan": satir("s", "islem", "silahlanan_plan"),
        "toplam_plan": satir("s", "islem", "toplam_plan"),
        "entry_rejects": satir("e", "islem", "entry_rejects"),
        "exit_reason_dagilim": satir("e", "islem", "exit_reason_dagilim"),
        "eff_max_open_eq0_n": satir("b", "betim", "eff_max_open_eq0_n"),
        "eff_max_open_eq1_n": satir("b", "betim", "eff_max_open_eq1_n"),
        "acik_slot_le0_n": satir("b", "betim", "acik_slot_le0_n"),
    }

    out = {
        "kart": "EDG-2026-023",
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "yontem": {
            "eslenik_bootstrap": ("tarih-kümeli (ay) EŞLENİK bootstrap: aynı ay çekilişi iki "
                                  "koşuma birden uygulanır; fark=varyant−taban; "
                                  f"iter={BOOT_ITER}, seed={BOOT_SEED}, n_ay={M}"),
            "islem_ay_anahtari": "ts_open[:7] (giriş ayı)",
            "oran_atlanan_iter": BOOT_ITER - len(oran),
            "tavan_bos_iter": tavan_bos,
            "takvim_ayni": takvim_ayni,
        },
        "rampalar": {"taban": st_["rampa"], "varyant": sv_["rampa"]},
        "butunluk": {"taban": st_["butunluk"], "varyant": sv_["butunluk"]},
        "kill2_tutarlilik": kill2,
        "kill1": {
            "esik": "varyant işlem sayısını CI ile artırmıyorsa (fark CI'ı 0'ı dışlamalı, artı yönde)",
            "fark_ci95": fark_ci, "artis_ci_0_disi": artis_ci_0_disi,
            "tetiklendi": kill1_tetiklendi,
        },
        "kill3": kill3,
        "tablo": tablo,
        "dosyalar": {r: {"sonuc": f"sonuc_{r}.json", "seanslar": f"seanslar_{r}.json",
                         "islemler": f"islemler_{r}.json"} for r in ("taban", "varyant")},
    }
    (SANDBOX / "sonuc.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))

    print("\n==================== EDG-023 A↔B ÖZET ====================")
    print(f"takvim aynı={takvim_ayni}  n_ay={M}")
    if kill2:
        print(f"KILL#2 (şasi): taban tavan_sifir %{kill2['taban_tavan_sifir_pct']} "
              f"(çivi %{KILL2_HEDEF_PCT}±{KILL2_TOL_PP}) → geçti={kill2['gecti']}")
    print(f"işlem: taban {nT} → varyant {nV}  fark={nV-nT}  CI95={fark_ci}  oran CI={oran_ci}")
    print(f"KILL#1 tetiklendi={kill1_tetiklendi} (artış CI-0-dışı={artis_ci_0_disi})")
    print(f"tavan_sifir birincil: taban %{tablo['tavan_sifir_birincil_pct']['taban']} → "
          f"varyant %{tablo['tavan_sifir_birincil_pct']['varyant']}  fark_pp CI={tavan_ci}")
    print(f"maxdd kanonik: {ddt} → {ddv}  oran={kill3['oran']}  KILL#3 tetiklendi={kill3['tetiklendi']}")
    print(f"net_pnl: {tablo['net_pnl_equity']}  avg_r: {tablo['avg_r']}")
    print(f"yazıldı: {SANDBOX/'sonuc.json'}")
    print("==========================================================\n")


if __name__ == "__main__":
    mod = sys.argv[1] if len(sys.argv) > 1 else ""
    smoke = "--smoke" in sys.argv
    if mod in ("taban", "varyant"):
        kosum(mod, smoke=smoke)
    elif mod == "birlestir":
        birlestir()
    else:
        sys.exit("kullanım: olcum.py {taban|varyant|birlestir} [--smoke]")

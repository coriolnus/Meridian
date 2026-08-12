"""EDG-2026-030 — REJİM EŞİĞİ (regime.min_exposure_score 40→30, 40→20) · ölçüm aracı (2026-08-12)

Kart: research/cards/EDG-2026-030-rejim-esigi.yaml (OKU-DOKUNMA; hüküm Rol-1'in).
Rol: ÖLÇÜM ajanı. Bu modül HÜKÜM VERMEZ, karta dokunmaz, git/canlı/broker/state'e YAZMAZ.

ŞASİ: EDG-026 (research/olcumler/edg026_slot20_2026-08-12/olcum.py) C-dünyası AYNEN devralındı:
izole sandbox (EDG-022 donmuş config kopyaları + bars symlink SALT-OKUNUR), rampa-15/36
monkeypatch'i (beyanlı, 023 deseni), slot-20 + 0.5R param-enjeksiyonları, kancalar, bütünlük
kontrolleri, ay-kümeli bootstrap (5000 iter, seed 20260812). KIYAS TABANI = EDG-026'nın HAZIR
C çıktıları (sonuc_c/seanslar_c/islemler_c — YENİDEN KOŞULMAZ, salt-okunur; sha256 kaydedilir).

İKİ HÜCRE (kart parameter_grid, DONUK):
  esik_30: regime.min_exposure_score 40→30
  esik_20: regime.min_exposure_score 40→20
  (C dünyasının kalanı AYNEN: rampa 15/36 mp + max_open=20 + position_size_r=0.5)

EŞİK ENJEKSİYON YÜZEYİ — BEYAN + KANIT (kart: "motor yamasız; param'dan okunduğu öz-sınamayla
kanıtlanır; okunmuyorsa beyan + monkeypatch beyanlı"):
  * Anahtar STRATEJİ params yüzeyinde YAŞIYOR: EDG-022 donmuş strategy.yaml params bloğunda
    `regime.min_exposure_score: 40` satırı VAR; motor onu regime.py:133
    `int(params.get("regime.min_exposure_score", 40))` ile okur ve backtest.py:267 build_regime_json'a
    HAM global params sözlüğünü geçirir (resolve_params satır 278'de SONRA çalışır — rejim-json
    çözümü per-rejim override'dan ETKİLENMEZ). Dolayısıyla enjeksiyon = params sözlük girdisi;
    MONKEYPATCH GEREKMEZ, motor dosyası DEĞİŞMEZ.
  * ÖZ-SINAMA 1 (koşum öncesi, sentetik): <220 barlık sentetik endekste classify=CHOP →
    exposure_score=45 sabittir; build_regime_json'a esik∈{20,30,40,45,46,50} verilip
    budget'ın {45,45,45,45,0,0} ve min_exposure_score yankısının esik'e eşit olduğu assert edilir
    (eşik GERÇEKTEN param'dan okunuyor + kapı GERÇEKTEN eşikle açılıp kapanıyor kanıtı).
  * ÖZ-SINAMA 2 (koşum içi, her seans): _regime kancası motorun geçirdiği params_'ın eşiğini VE
    rj["min_exposure_score"] yankısını VE bütçe kuralını (budget == score if score>=esik else 0)
    HER build_regime_json çağrısında doğrular; ihlal sayısı bütünlük kaydına girer (0 olmalı).
  * params_by_regime GÖLGELEME KANITI: dört rejimde de anahtar yok (koşum öncesi assert) +
    resolve_params dört rejim için enjekte eşik değerini döndürür (assert).

TANIMLAR (ölçümden ÖNCE donduruldu; sonuç görüldükten sonra değişmez):
  islem                = kapanmış işlem satırı (broker.closed; eod/delisted markout DAHİL).
  islem kimliği        = (ts_open[:10], ticker) çifti — hücre↔C işlem-kümesi eşlemesi bu anahtarla.
  EKLENEN islem        = hücrede olup C'de OLMAYAN kimlik. ÇIKAN islem = C'de olup hücrede olmayan
                         (yan-etki/knock-on beyanı — ayrıca raporlanır). ORTAK = iki tarafta da var;
                         ortak-çıkış-kayması = ts_close VEYA exit_reason VEYA r_multiple farklı.
  ay kümesi            = ts_open[:7] (giriş ayı); ay evreni = seans takviminin TÜM ayları.
  eşlenik fark CI      = ay-kümeli EŞLENİK bootstrap (aylar yerine-koymalı, 5000 iter, seed
                         20260812; AYNI ay çekilişi iki koşuma birden): işlem n farkı, net P&L
                         farkı (Σ pnl_dollars, giriş-ayı anahtarı), sharpe farkı, max-dd farkı.
  bootstrap sharpe     = kanonik score.score_detail FORMÜLÜYLE iterasyon içi yeniden hesap:
                         per_trade_ret = pnl/START_EQUITY; mean/std(ddof=1)·sqrt(max(n/(span/365),1));
                         span = TAM pencere gün sayısı (sabit). n≤2 veya std=0 → iterasyon o metrik
                         için ATLANIR (sayısı raporlanır). Nokta değerleri MOTOR score_detail'den.
  bootstrap max-dd     = kanonik score.equity_curve (ts_close sıralı) + score.max_drawdown,
                         çekilen ay-çoklu-kümesinin işlemleri üzerinde (kapalı-işlem eğrisi;
                         ay yeniden-örneklemesi dd'nin zaman sırasını yapay kurar — CI bu beyanla
                         okunur; kanonik NOKTA dd motor score_detail.max_drawdown'dan).
  eklenen ort-R CI     = TEK-ÖRNEKLEM ay-kümeli bootstrap: yalnız eklenen işlemlerin ayları
                         çekilir, iterasyon ortalama R'si; <2 ay kümesi → CI olculemedi (None+neden).
  rejim-kırılımı       = işlem kaydındaki `regime` alanı (arm/plan günü rejimi — motor kaydı).
  arm günü             = ts_open'dan önceki seans (arm CLOSE(D), dolum OPEN(D+1)); eklenen işlemin
                         arm günü C'de bütçe-kapalı mıydı (C seans kaydı exposure_budget_pct∈{0,None})
                         → "C'de kapalı günden gelen" sayısı; kalanı knock-on (C açıkken slot/ısı/
                         equity sapmasından). Arm günü skoru hücre seans kaydından (skor bandı ile).
  skor kimliği         = exposure_score parametreden BAĞIMSIZ saf bar fonksiyonudur; C'de budget>0
                         olan her seansta hücre skoru == C bütçesi olmalı (şasi-kimlik çaprazı).
  max-dd (nokta)       = motor-kanonik score.score_detail.max_drawdown (kapalı-işlem ∨ günlük M2M
                         kötüsü); maxdd_m2m ayrıca raporlu. net P&L = M2M equity son − START;
                         çapraz Σ pnl_dollars. NO_GO/REVIEW dağılımı 026 eşlemesiyle.

KILL KONTROLLERİ (kart, DONUK — koşul değerinin kaydı, hüküm DEĞİL):
  kill#1: eklenen işlem <30/hücre → o hücre OLCULEMEDI.
  kill#2: şasi bütünlüğü bozuksa (frame_miss=0, dup=0, scan==plan, yasak modül yok,
          base_max_open==20, eşik-yankı ihlali=0, bütçe-kural ihlali=0, motor/config sha == C) GEÇERSİZ.
  (kartın success_metric'indeki dd C×1.5 koşulu HÜKÜM GİRDİSİDİR; değeri kaydedilir, hüküm yazılmaz.)

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen = None + neden); YASA-4 (sessiz-yutma işaretli + gerekçe);
YASA-6 (okuyucu: sonuc_e*/seanslar_e*/islemler_e* → `kiyas` tüketir; sonuc.json → dönüş raporu +
Rol-1). SALT-OKUMA: config.STATE koşum-başına izole sandbox; canlı state'e ve motor dosyalarına tek
bayt yazılmaz. meridian.loop / counterfactual / cf_backfill / hermes İTHAL EDİLMEZ — sys.modules
ile KANITLANIR.

KULLANIM:
  olcum.py kosum e30 [--smoke]   # hücre esik_30 → sonuc_e30.json + seanslar_e30 + islemler_e30
  olcum.py kosum e20 [--smoke]   # hücre esik_20
  olcum.py kiyas [--smoke]       # iki hücre + C (026 HAZIR çıktıları) → sonuc.json
  (--smoke: 2022-01-01→2022-06-30, çıktılar smoke/ altına; C smoke tabanı 026/smoke'tan okunur)
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
EDG026 = REPO / "research/olcumler/edg026_slot20_2026-08-12"

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

REPLAY_START = "2022-01-01"
REPLAY_END = "2026-07-30"                      # C (026) ile AYNI pencere
BOOT_SEED = 20260812
BOOT_ITER = 5000

# C dünyasının DONUK parametreleri (026'dan AYNEN — hücreler yalnız eşiği değiştirir)
RAMPA = {"tam_dd": 0.15, "sifir_dd": 0.36}
SLOT = 20
BOYUT_R = 0.5
ESKI_ESIK = 40                                 # C'nin eşiği (donmuş strategy.yaml değeri)
HUCRELER = {"e30": 30, "e20": 20}              # kart parameter_grid: esik [30, 20]
KILL1_MIN_EKLENEN = 30                         # kart kill#1
DD_KOSUL_KATSAYI = 1.5                         # kartın success_metric dd koşulu (hüküm girdisi)

KART3 = ["tavan_sifir", "evren_bagladi", "derisk_bagladi"]
YASAK = ("meridian.loop", "meridian.counterfactual", "meridian.cf_backfill", "meridian.hermes")

# NO_GO/REVIEW neden eşlemesi — 026 şasisi AYNEN (eşleşmeyen HAM sayılır; YASA-4)
NEDEN_ESLEME = [
    ("heat_hard", "portföy ısısı sert tavanı"),
    ("max_open_positions", "pozisyon dolu"),
    ("sector_cap", "sektör tavanı"),
    ("rr_floor", "yetersiz ödül/risk"),
    ("exposure_budget", "exposure_budget"),
    ("daily_loss_breaker", "devre kesici"),
    ("position_size", "boyut "),
    ("heat_review", "portföy ısısı yüksek"),
    ("sector_stacking", "korelasyon yığılması"),
    ("correlation", "yüksek korelasyon"),
    ("leading_sector", "lider sektörlerinde değil"),
    ("rr_marginal", "marjinal"),
    ("rr_defined", "R:R belirsiz"),
    ("score_band", "skor alt bantta"),
    ("earnings_coverage_note", "kazanç kapsamı"),
]

SKOR_BANTLARI = [(0, 20, "0-19"), (20, 30, "20-29"), (30, 40, "30-39"), (40, 101, "40+")]


def _sha(p: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    except OSError:
        return None    # ölçülemedi (dosya yok/okunamadı)


def _sha_full(p: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None


def _neden_dagit(nedenler_listesi) -> dict:
    c: dict[str, int] = {}
    for neden in nedenler_listesi:
        ad = None
        for kontrol, parca in NEDEN_ESLEME:
            if parca in neden:
                ad = kontrol
                break
        c[ad or f"HAM:{neden[:80]}"] = c.get(ad or f"HAM:{neden[:80]}", 0) + 1
    return dict(sorted(c.items(), key=lambda kv: -kv[1]))


def _skor_bandi(s) -> str:
    if s is None:
        return "skor_yok"
    for lo, hi, ad in SKOR_BANTLARI:
        if lo <= s < hi:
            return ad
    return "skor_yok"


# ---------------------------------------------------------------------------------------------
# SANDBOX HAZIRLIĞI — izole state (EDG-022 DONMUŞ config kopyaları; 026 şasisi AYNEN)
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
            # DOSYALAR DEĞİŞTİRİLMEZ: eşik/slot/boyut enjeksiyonu YÜKLENMİŞ sözlüklere yapılır ki
            # config sha'ları C ile bayt-aynı kalsın ve şasi kimliği sha ile kanıtlansın.
            shutil.copyfile(EDG022 / "state" / f, dst)
    return st


# ---------------------------------------------------------------------------------------------
# RAMPA — 023/026 deseni AYNEN (monkeypatch, beyan başlıkta)
# ---------------------------------------------------------------------------------------------
def _rampa_fn(tam_dd: float, sifir_dd: float):
    def derisk_mult_param(equity: float, peak: float) -> float:
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
# SINIFLAMA + seans-CI — EDG-022/026 DONUK kuralları AYNEN
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


def _isi_ozet(degerler: list[float]) -> dict | None:
    import numpy as np
    if not degerler:
        return None
    a = np.asarray(degerler, dtype=float)
    hist: dict[str, int] = {}
    for v in a:
        k = f"{round(v * 2) / 2:.1f}"
        hist[k] = hist.get(k, 0) + 1
    return {"max": round(float(a.max()), 3),
            "p50": round(float(np.percentile(a, 50)), 3),
            "p90": round(float(np.percentile(a, 90)), 3),
            "p99": round(float(np.percentile(a, 99)), 3),
            "ort": round(float(a.mean()), 3),
            "sifir_ustu_seans_n": int((a > 0).sum()),
            "n_seans": int(len(a)),
            "histogram_0p5R": dict(sorted(hist.items(), key=lambda kv: float(kv[0])))}


def _islem_araligi_sayimi(islemler: list[dict], takvim: list[str]) -> list[int]:
    araliklar = [(str(t["ts_open"])[:10], str(t["ts_close"])[:10]) for t in islemler
                 if t.get("ts_open") and t.get("ts_close")]
    out = []
    for d in takvim:
        out.append(sum(1 for a, b in araliklar if a <= d <= b))
    return out


# ---------------------------------------------------------------------------------------------
# EŞİK ÖZ-SINAMASI 1 — sentetik endeksle param yüzeyinin kanıtı (motor yamasız)
# ---------------------------------------------------------------------------------------------
def esik_oz_sinama(regime_mod) -> dict:
    """<220 bar → classify CHOP (ısınma yetersiz dalı), metrics'te high_vol anahtarı YOK →
    exposure_score(CHOP)=45 SABİT; kapanışlar monoton artan → distribution_days=0 (kesinti yok).
    Böylece budget'ı yalnız eşik belirler: eşik≤45 → 45, eşik>45 → 0."""
    import pandas as pd
    n = 30
    tiny = pd.DataFrame({
        "open": [100.0 + i * 0.1 for i in range(n)],
        "high": [100.5 + i * 0.1 for i in range(n)],
        "low": [99.5 + i * 0.1 for i in range(n)],
        "close": [100.0 + i * 0.1 for i in range(n)],   # monoton ↑ → down-day yok → dd=0
        "volume": [1_000_000.0] * n,
    })
    beklenen = {20: 45, 30: 45, 40: 45, 45: 45, 46: 0, 50: 0}
    kayit = {}
    for esik, buc in beklenen.items():
        rj = regime_mod.build_regime_json(tiny, {"regime.min_exposure_score": esik}, "2020-01-01")
        assert rj["min_exposure_score"] == esik, f"eşik yankısı bozuk: {esik} → {rj['min_exposure_score']}"
        assert rj["exposure_score"] == 45, f"sentetik skor 45 değil: {rj['exposure_score']}"
        assert rj["exposure_budget_pct"] == buc, f"eşik {esik}: budget {rj['exposure_budget_pct']} != {buc}"
        kayit[str(esik)] = {"budget": rj["exposure_budget_pct"], "yanki": rj["min_exposure_score"]}
    rj0 = regime_mod.build_regime_json(tiny, {}, "2020-01-01")     # anahtar yoksa varsayılan 40
    assert rj0["min_exposure_score"] == 40 and rj0["exposure_budget_pct"] == 45
    return {"gecti": True, "senaryolar": kayit,
            "beyan": ("eşik params sözlüğünden OKUNUYOR (regime.py:133 params.get) ve kapıyı "
                      "GERÇEKTEN o değer açıp kapatıyor — monkeypatch GEREKMEDİ, motor yamasız")}


# ---------------------------------------------------------------------------------------------
# HÜCRE KOŞUMU (esik_30 | esik_20) — 026 kosum() düzeni + eşik enjeksiyonu/kanıtları
# ---------------------------------------------------------------------------------------------
def kosum(hucre: str, smoke: bool = False):
    assert hucre in HUCRELER, f"hücre {hucre} tanımsız (e30|e20)"
    ESIK = HUCRELER[hucre]
    outdir = (SANDBOX / "smoke") if smoke else SANDBOX
    outdir.mkdir(exist_ok=True)
    r_start, r_end = (REPLAY_START, "2022-06-30") if smoke else (REPLAY_START, REPLAY_END)

    st_dir = hazirla(hucre + ("_smoke" if smoke else ""))
    sys.path.insert(0, str(REPO))

    from meridian import config
    config.STATE = st_dir
    config.BARS = st_dir / "bars"
    config.HISTORY = st_dir / "history"

    import numpy as np                     # noqa: F401
    import yaml
    from meridian import backtest, dataset, score as score_mod

    assert not hasattr(backtest, "wpg_overlay_day"), "motor YAMALI görünüyor — ölçüm geçersiz"
    assert not [m for m in sys.modules if m in YASAK], "yasaklı modül ithal edilmiş"

    brk = backtest.brk
    ORIJ_DERISK = brk.derisk_mult

    # ---- rampa kurulumu + öz-sınama (026 AYNEN) ----------------------------------------------
    brk.derisk_mult = _rampa_fn(RAMPA["tam_dd"], RAMPA["sifir_dd"])
    assert brk.derisk_mult is not ORIJ_DERISK
    assert brk.derisk_mult(90.0, 100.0) == 1.0
    assert abs(brk.derisk_mult(80.0, 100.0) - 0.7619) < 1e-9
    assert brk.derisk_mult(64.0, 100.0) == 0.0
    assert brk.max_positions_at(80.0, 100.0, 5) == 4
    assert brk.max_positions_at(80.0, 100.0, 20) == 15

    # ---- EŞİK ÖZ-SINAMASI 1 (sentetik; motor yamasız kanıtı) ---------------------------------
    oz1 = esik_oz_sinama(backtest.regime_mod)

    # ---- girdiler + PARAM-ENJEKSİYONLARI (dosya DEĞİŞMEZ; 026 ikilisi + eşik) ----------------
    stg = yaml.safe_load((st_dir / "strategy.yaml").read_text())
    params = dict(stg["params"])
    by_regime = stg.get("params_by_regime") or None
    sv = int(stg.get("version"))
    goal = config.goal()                                   # derin kopya

    onceki = {"max_open_positions": int(goal["limits"]["max_open_positions"]),
              "position_size_r": float(params["position_size_r"]),
              "regime.min_exposure_score": int(params["regime.min_exposure_score"])}
    assert onceki["regime.min_exposure_score"] == ESKI_ESIK, \
        f"donmuş strategy.yaml eşiği {onceki['regime.min_exposure_score']} != {ESKI_ESIK}"
    goal["limits"]["max_open_positions"] = SLOT            # ENJEKSİYON 1 (C dünyası — 026)
    params["position_size_r"] = BOYUT_R                    # ENJEKSİYON 2 (C dünyası — 026)
    params["regime.min_exposure_score"] = ESIK             # ENJEKSİYON 3 (BU KARTIN değişkeni)

    # gölgeleme kanıtı: dört rejimde de override yok + resolve_params enjekte değeri döndürüyor
    for _rg in ("trend_up", "trend_down", "chop", "high_vol"):
        _eff = config.resolve_params(params, by_regime, _rg)
        assert float(_eff["position_size_r"]) == BOYUT_R, f"rejim override sızıntısı: {_rg}"
        assert int(_eff["regime.min_exposure_score"]) == ESIK, f"eşik override sızıntısı: {_rg}"
        _bl = (by_regime or {}).get(_rg) or {}
        assert "position_size_r" not in _bl and "regime.min_exposure_score" not in _bl, \
            f"params_by_regime[{_rg}] gölgeleme içeriyor — tek-nokta enjeksiyonu yetersiz"
    assert float(goal["limits"]["max_position_r"]) >= BOYUT_R
    limits = goal["limits"]
    max_open = int(limits["max_open_positions"])
    no_trade_before = int(limits.get("no_trade_before_bars", 0))
    assert max_open == SLOT

    # ---- kancalar (026 deseni + eşik-yankı/bütçe-kural sayaçları) ----------------------------
    seans_by_date: dict[str, dict] = {}
    _cur_close_date = [None]
    _dup: list[str] = []
    _frame_miss = [0]
    _esik_ihlal: list[dict] = []          # params_/yankı eşiği != ESIK görülen çağrılar (0 olmalı)
    _butce_ihlal: list[dict] = []         # budget != (score if score>=ESIK else 0) (0 olmalı)

    _orig_maxpos = brk.max_positions_at
    _orig_regime = backtest.regime_mod.build_regime_json
    _orig_scan = backtest.strat.scan_entry

    def _maxpos(equity, peak, base_max):
        n = _orig_maxpos(equity, peak, base_max)
        fr = sys._getframe(1)
        loc = fr.f_locals
        d = loc.get("d")
        bar_i = loc.get("bar_i")
        broker = loc.get("broker")
        if d is None or broker is None:
            _frame_miss[0] += 1
            return n
        date = str(d.date())
        n_acik = len(broker.positions)
        dd = ((peak - equity) / peak) if peak and peak > 0 else 0.0
        pozlar = list(broker.positions.values())
        rec = {
            "date": date, "bar_i": int(bar_i) if bar_i is not None else None,
            "eq_open": round(float(equity), 2), "peak_equity": round(float(peak), 2),
            "dd": round(float(dd), 6), "base_max_open": int(base_max),
            "eff_max_open": int(n), "n_acik": int(n_acik),
            "acik_slot": int(n) - int(n_acik),
            "size_mult": float(brk.derisk_mult(equity, peak)),
            "acik_size_r_toplam": round(sum(float(p.size_r) for p in pozlar), 3),
            "acik_risk_dollars_giris": round(sum(float(p.risk_dollars) for p in pozlar), 2),
            "acik_kalan_risk_dollars": round(sum(
                max(0.0, (float(p.entry) - max(float(p.stop), float(p.trail_stop))) * int(p.qty))
                for p in pozlar), 2),
            "regime": None, "exposure_budget_pct": None,
            "exposure_score": None, "min_exposure_score": None,   # EDG-030 alanları
            "n_scan_cagri": 0, "n_sinyal": 0,
        }
        if date in seans_by_date:
            _dup.append(date)
        seans_by_date[date] = rec
        return n

    def _regime(idx_df, params_, asof):
        rj = _orig_regime(idx_df, params_, asof)
        date = str(asof)[:10]
        _cur_close_date[0] = date
        # ÖZ-SINAMA 2: motorun geçirdiği params_ eşiği + rj yankısı + bütçe kuralı HER çağrıda
        p_esik = params_.get("regime.min_exposure_score") if isinstance(params_, dict) else None
        if p_esik != ESIK or rj.get("min_exposure_score") != ESIK:
            _esik_ihlal.append({"date": date, "params_esik": p_esik,
                                "yanki": rj.get("min_exposure_score")})
        sc, bu = rj.get("exposure_score"), rj.get("exposure_budget_pct")
        if sc is not None and bu != (sc if sc >= ESIK else 0):
            _butce_ihlal.append({"date": date, "score": sc, "budget": bu})
        rec = seans_by_date.get(date)
        if rec is not None:
            rec["regime"] = rj.get("regime")
            rec["exposure_budget_pct"] = rj.get("exposure_budget_pct")
            rec["exposure_score"] = rj.get("exposure_score")
            rec["min_exposure_score"] = rj.get("min_exposure_score")
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

    t0 = dt.datetime.now()
    bars, index = dataset.load_cached()
    res = backtest.replay(params, bars, index, goal, r_start, r_end,
                          strategy_version=sv, params_by_regime=by_regime, with_gate_detail=False)
    sure = round((dt.datetime.now() - t0).total_seconds(), 1)

    yasak_yuklu = [m for m in sys.modules if m in YASAK]

    # ---- plan_log çapraz-kontrolü + NO_GO/REVIEW dağılımı (026 AYNEN) ------------------------
    plan_aday: dict[str, int] = {}
    plan_silahli: dict[str, int] = {}
    nogo_nedenler: list[str] = []
    review_nedenler: list[str] = []
    verdict_n = {"GO": 0, "REVIEW": 0, "NO_GO": 0}
    silahli_size_r: list[float] = []
    for p in (res.plan_log or []):
        dts = str(p.get("date"))[:10]
        plan_aday[dts] = plan_aday.get(dts, 0) + 1
        v = p.get("gate_verdict")
        verdict_n[v] = verdict_n.get(v, 0) + 1
        if v != "NO_GO":
            plan_silahli[dts] = plan_silahli.get(dts, 0) + 1
            silahli_size_r.append(float(p.get("size_r") or 0.0))
            if v == "REVIEW":
                review_nedenler.extend(p.get("gate_reasons") or [])
        else:
            nogo_nedenler.extend(p.get("gate_reasons") or [])

    sess = sorted(seans_by_date.values(),
                  key=lambda r: (r["bar_i"] if r["bar_i"] is not None else 0))
    scan_vs_plan = []
    for r in sess:
        r["aday_n"] = r["n_sinyal"]
        r["silahli_n"] = plan_silahli.get(r["date"], 0)
        r["plan_aday"] = plan_aday.get(r["date"], 0)
        if r["n_sinyal"] != r["plan_aday"]:
            scan_vs_plan.append({"date": r["date"], "n_sinyal": r["n_sinyal"],
                                 "plan_aday": r["plan_aday"]})
        r["sinif"] = classify(r, no_trade_before)

    n_all = len(sess)
    base_max_bozuk = [r["date"] for r in sess if r["base_max_open"] != SLOT]
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

    # ---- işlem/doluluk/ısı/performans (026 AYNEN) --------------------------------------------
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

    doluluk_pozgun = sum(r["n_acik"] for r in sess)
    doluluk_barsheld = sum(int(t.get("bars_held") or 0) for t in trades)
    exit_dist: dict[str, int] = {}
    for t in trades:
        exit_dist[str(t.get("exit_reason"))] = exit_dist.get(str(t.get("exit_reason")), 0) + 1

    takvim = [r["date"] for r in sess]
    aralik_sayim = _islem_araligi_sayimi(
        [{"ts_open": t.get("ts_open"), "ts_close": t.get("ts_close")} for t in trades], takvim)
    isi = {
        "formul": f"nominal = n_eszamanli × {BOYUT_R}R (üst sınır; conviction 0.6-1.0×)",
        "nominal_open_fazi_R": _isi_ozet([r["n_acik"] * BOYUT_R for r in sess]),
        "nominal_islem_araligi_R": _isi_ozet([n * BOYUT_R for n in aralik_sayim]),
        "gerceklesen_open_fazi": {
            "size_r_toplam": _isi_ozet([r["acik_size_r_toplam"] for r in sess]),
            "risk_dollars_giris_max": round(max((r["acik_risk_dollars_giris"] for r in sess),
                                                default=0.0), 2),
            "kalan_risk_dollars_max": round(max((r["acik_kalan_risk_dollars"] for r in sess),
                                                default=0.0), 2),
            "kalan_risk_nav_pct_max": round(max(
                (100.0 * r["acik_kalan_risk_dollars"] / r["eq_open"]
                 for r in sess if r["eq_open"] > 0), default=0.0), 3),
        },
        "eszamanli_poz_max": {"open_fazi": max((r["n_acik"] for r in sess), default=0),
                              "islem_araligi": max(aralik_sayim, default=0)},
    }

    # rejim/bütçe betimi — bu kartın ana merceği
    butce_acik_n = sum(1 for r in sess if (r["exposure_budget_pct"] or 0) > 0)
    skor_bant_dag: dict[str, int] = {}
    skor_bant_acik: dict[str, int] = {}
    rejim_dag: dict[str, int] = {}
    for r in sess:
        b = _skor_bandi(r["exposure_score"])
        skor_bant_dag[b] = skor_bant_dag.get(b, 0) + 1
        if (r["exposure_budget_pct"] or 0) > 0:
            skor_bant_acik[b] = skor_bant_acik.get(b, 0) + 1
        rejim_dag[str(r["regime"])] = rejim_dag.get(str(r["regime"]), 0) + 1

    eff_lt = sum(1 for r in sess if r["eff_max_open"] < max_open)
    slot_le0 = sum(1 for r in sess if r["acik_slot"] <= 0)
    dd_gt_tam = sum(1 for r in sess if r["dd"] > RAMPA["tam_dd"])
    size0 = sum(1 for r in sess if r["size_mult"] <= 0.0)
    tavan_pct_bir = round(100.0 * sum(1 for r in birincil if r["sinif"] == "tavan_sifir")
                          / n_bir, 2) if n_bir else None

    butunluk_gecerli = (_frame_miss[0] == 0 and not _dup and not scan_vs_plan
                        and not yasak_yuklu and not base_max_bozuk
                        and not _esik_ihlal and not _butce_ihlal)

    out = {
        "kart": "EDG-2026-030", "kosum": f"esik_{ESIK}", "hucre": hucre, "smoke": smoke,
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sure_sn": sure,
        "rampa": {"tam_dd": RAMPA["tam_dd"], "sifir_dd": RAMPA["sifir_dd"],
                  "enjeksiyon": "MONKEYPATCH (beyanlı — 023/026 deseni AYNEN; motor DOSYASI değişmedi)"},
        "param_enjeksiyon": {
            "max_open_positions": {"once": onceki["max_open_positions"], "sonra": SLOT,
                                   "yuzey": "goal['limits'] (026 C dünyası AYNEN)"},
            "position_size_r": {"once": onceki["position_size_r"], "sonra": BOYUT_R,
                                "yuzey": "strateji params sözlüğü (026 C dünyası AYNEN)"},
            "regime.min_exposure_score": {
                "once": onceki["regime.min_exposure_score"], "sonra": ESIK,
                "yuzey": ("strateji params sözlüğü — regime.py:133 params.get ile okur; "
                          "backtest.py:267 build_regime_json'a HAM global params geçirir "
                          "(resolve_params SONRA). MONKEYPATCH GEREKMEDİ — motor yamasız; "
                          "kanıt: oz_sinama_1 (sentetik) + oz_sinama_2 (koşum içi her seans)")},
            "zarf_sabit": ("heat_hard_r=5.0R, heat_review_r=3.5R, max_position_r=1.0, "
                           "max_sector_exposure_pct=40 DEĞİŞMEDİ (026 zarfı AYNEN; kart yalnız eşiği oynatır)"),
        },
        "esik_oz_sinama_1": oz1,
        "esik_oz_sinama_2": {"cagri_ihlal_n": len(_esik_ihlal), "ornek": _esik_ihlal[:5],
                             "butce_kural_ihlal_n": len(_butce_ihlal), "ornek_butce": _butce_ihlal[:5],
                             "beyan": ("her build_regime_json çağrısında params_ eşiği + rj yankısı + "
                                       "budget==(score if score>=esik else 0) doğrulandı")},
        "motor_sha256_16": {f: _sha(REPO / "meridian" / f)
                            for f in ("broker.py", "backtest.py", "strategy.py", "regime.py",
                                      "guard.py", "score.py")},
        "config_sha256_16": {f: {"sandbox": _sha(st_dir / f),
                                 "edg022": _sha(EDG022 / "state" / f)}
                             for f in ("goal.yaml", "strategy.yaml", "bounds.yaml")},
        "replay": {"start": r_start, "end": r_end, "strategy_version": sv,
                   "params_by_regime": bool(by_regime), "n_sembol": len(bars),
                   "n_endeks_satir": int(len(index)), "max_open": max_open,
                   "no_trade_before": no_trade_before,
                   "cost_model": {"slippage_bps": float(goal.get("slippage_bps", 5)),
                                  "commission_per_share": float(goal.get("commission_per_share", 0.0)),
                                  "not": "motorun kendi maliyet modeli — dokunulmadı"}},
        "butunluk": {
            "frame_okunamadi": _frame_miss[0], "tekrar_tarih": _dup,
            "scan_vs_plan_uyusmazlik_n": len(scan_vs_plan),
            "scan_vs_plan_ornek": scan_vs_plan[:10],
            "yasakli_modul_yuklendi": yasak_yuklu,
            "base_max_open_bozuk": base_max_bozuk[:10],
            "esik_yanki_ihlal_n": len(_esik_ihlal),
            "butce_kural_ihlal_n": len(_butce_ihlal),
            "gecerli": butunluk_gecerli,
        },
        "islem": {
            "n": n_islem, "islem_yil": round(n_islem / yil, 2),
            "aylik_ts_open": dict(sorted(aylik.items())),
            "silahlanan_plan": sum(plan_silahli.values()),
            "toplam_plan": sum(plan_aday.values()),
            "verdict_dagilim": verdict_n,
            "nogo_neden_dagilim": _neden_dagit(nogo_nedenler),
            "review_neden_dagilim": _neden_dagit(review_nedenler),
            "silahli_plan_size_r": {"min": round(min(silahli_size_r), 3) if silahli_size_r else None,
                                    "max": round(max(silahli_size_r), 3) if silahli_size_r else None,
                                    "ort": round(sum(silahli_size_r) / len(silahli_size_r), 3)
                                    if silahli_size_r else None},
            "entry_rejects": res.entry_rejects,
            "exit_reason_dagilim": dict(sorted(exit_dist.items(), key=lambda kv: -kv[1])),
        },
        "performans": {
            "net_pnl_equity": net_pnl_equity, "net_pnl_trades": net_pnl_trades,
            "maxdd_kanonik": detail.get("max_drawdown"),
            "maxdd_m2m": maxdd_m2m,
            "avg_r": detail.get("avg_r"), "win_rate": detail.get("win_rate"),
            "sharpe": detail.get("sharpe"), "sharpe_measurable": detail.get("sharpe_measurable"),
            "score": detail.get("score"), "score_n": detail.get("n"),
            "total_return": detail.get("total_return"),
        },
        "doluluk": {"pozisyon_gun_open_fazi": doluluk_pozgun,
                    "ort_acik_pozisyon": round(doluluk_pozgun / n_all, 3) if n_all else None,
                    "doluluk_orani_slot": round(doluluk_pozgun / n_all / SLOT, 4) if n_all else None,
                    "toplam_bars_held": doluluk_barsheld},
        "tepe_isi": isi,
        "rejim_butce": {
            "butce_acik_seans_n": butce_acik_n,
            "butce_kapali_seans_n": n_all - butce_acik_n,
            "skor_bant_dagilim_tum": dict(sorted(skor_bant_dag.items())),
            "skor_bant_dagilim_butce_acik": dict(sorted(skor_bant_acik.items())),
            "rejim_dagilim_seans": dict(sorted(rejim_dag.items(), key=lambda kv: -kv[1])),
        },
        "betim": {
            "n_seans": n_all, "dd_gt_tam_esik_n": dd_gt_tam,
            "eff_max_open_lt_base_n": eff_lt, "acik_slot_le0_n": slot_le0,
            "size_mult_0_n": size0,
        },
        "tasnif_tum_seans": {"n": n_all, "dagilim": yuzde(dagit(sess), n_all)},
        "birincil": {"n": n_bir, "dagilim": yuzde(dagit(birincil), n_bir) if n_bir else {},
                     "tavan_sifir_pct": tavan_pct_bir},
        "ci95_ay_kumeli": ci,
    }

    ek = "_smoke" if smoke else ""
    (outdir / f"sonuc_{hucre}{ek}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str))
    (outdir / f"seanslar_{hucre}{ek}.json").write_text(
        json.dumps(sess, ensure_ascii=False, default=str))
    slim = [{k: t.get(k) for k in ("ts_open", "ts_close", "ticker", "r_multiple",
                                   "pnl_dollars", "exit_reason", "bars_held", "regime",
                                   "setup", "qty", "risk_dollars", "size_r")} for t in trades]
    (outdir / f"islemler_{hucre}{ek}.json").write_text(
        json.dumps(slim, ensure_ascii=False, default=str))

    print(f"\n=========== EDG-030 KOŞUM [esik_{ESIK}{ek}] ===========")
    print(f"replay {r_start}→{r_end}  sv={sv}  sembol={len(bars)}  süre={sure}s")
    print(f"enjeksiyon: max_open {onceki['max_open_positions']}→{max_open}  "
          f"size_r {onceki['position_size_r']}→{params['position_size_r']}  "
          f"esik {onceki['regime.min_exposure_score']}→{params['regime.min_exposure_score']}")
    print(f"bütünlük geçerli={out['butunluk']['gecerli']}  frame_miss={_frame_miss[0]} "
          f"dup={len(_dup)} scan!=plan={len(scan_vs_plan)} yasak={yasak_yuklu} "
          f"base_max_bozuk={len(base_max_bozuk)} esik_ihlal={len(_esik_ihlal)} "
          f"butce_ihlal={len(_butce_ihlal)}")
    print(f"işlem n={n_islem} ({out['islem']['islem_yil']}/yıl)  net_pnl={net_pnl_equity}  "
          f"maxdd_kanonik={detail.get('max_drawdown')}  maxdd_m2m={maxdd_m2m}  "
          f"avg_r={detail.get('avg_r')}  sharpe={detail.get('sharpe')}")
    print(f"bütçe: açık {butce_acik_n}/{n_all} seans  skor-bant(açık)={skor_bant_acik}")
    print(f"NO_GO nedenleri: {out['islem']['nogo_neden_dagilim']}")
    print(f"yazıldı: {outdir}/sonuc_{hucre}{ek}.json")
    print(f"KOSUM_{hucre.upper()}{ek.upper()}_BITTI")


# ---------------------------------------------------------------------------------------------
# KIYAS — hücreler (yerel) ↔ C (EDG-026 HAZIR çıktıları; YENİDEN KOŞULMAZ) → sonuc.json
# ---------------------------------------------------------------------------------------------
def _yukle(base: pathlib.Path, on_ek: str, ek: str) -> dict:
    return {"sonuc": json.loads((base / f"sonuc_{on_ek}{ek}.json").read_text()),
            "seans": json.loads((base / f"seanslar_{on_ek}{ek}.json").read_text()),
            "islem": json.loads((base / f"islemler_{on_ek}{ek}.json").read_text())}


def kiyas(smoke: bool = False):
    import numpy as np
    sys.path.insert(0, str(REPO))
    from meridian import score as score_mod          # kanonik equity_curve/max_drawdown formülleri

    ek = "_smoke" if smoke else ""
    yerel = (SANDBOX / "smoke") if smoke else SANDBOX
    c_dir = (EDG026 / "smoke") if smoke else EDG026

    C = _yukle(c_dir, "c", ek)
    c_sha = {f"{ad}_c{ek}.json": _sha_full(c_dir / f"{ad}_c{ek}.json")
             for ad in ("sonuc", "seanslar", "islemler")}

    sc = C["sonuc"]
    tarih_c = [s["date"] for s in C["seans"]]
    aylar = sorted({d[:7] for d in tarih_c})
    M = len(aylar)
    r_start = sc["replay"]["start"]
    r_end = sc["replay"]["end"]
    pencere_gun = (dt.date.fromisoformat(r_end) - dt.date.fromisoformat(r_start)).days

    C_kimlik = {(str(t["ts_open"])[:10], t["ticker"]) for t in C["islem"]}
    C_by_kimlik = {(str(t["ts_open"])[:10], t["ticker"]): t for t in C["islem"]}
    C_seans_by_date = {s["date"]: s for s in C["seans"]}

    def ay_grup(islemler):
        g: dict[str, list[dict]] = {a: [] for a in aylar}
        for t in islemler:
            a = str(t["ts_open"])[:7]
            if a in g:
                g[a].append(t)
        return g

    def ci95(arr):
        a = np.asarray([x for x in arr if x == x], dtype=float)
        if not len(a):
            return None
        return {"lo": round(float(np.percentile(a, 2.5)), 4),
                "hi": round(float(np.percentile(a, 97.5)), 4),
                "orta": round(float(np.median(a)), 4)}

    def iter_metrikler(gr, pick):
        """Çekilen ay-çoklu-kümesinin işlemlerinden (n, Σpnl, sharpe|nan, maxdd|nan) — kanonik formüller."""
        ts: list[dict] = []
        for j in sorted(pick):                     # takvim sırası; çift çekilen ay ardışık iki kez
            ts.extend(gr[aylar[j]])
        n = len(ts)
        pnl = float(sum(float(t.get("pnl_dollars", 0.0)) for t in ts))
        if n > 2:
            ret = np.array([float(t.get("pnl_dollars", 0.0)) for t in ts]) / score_mod.START_EQUITY
            sd = float(ret.std(ddof=1))
            if sd > 0:
                tpy = n / (pencere_gun / 365.0)
                sh = float(ret.mean()) / sd * float(np.sqrt(max(tpy, 1.0)))
            else:
                sh = float("nan")
        else:
            sh = float("nan")
        dd = float(score_mod.max_drawdown(score_mod.equity_curve(ts))) if n else float("nan")
        return n, pnl, sh, dd

    def hucre_kiyas(hucre: str) -> dict:
        E = _yukle(yerel, hucre, ek)
        se, sonuc_e = E["sonuc"], E["sonuc"]

        # ---- şasi kimliği: motor+config sha C ile birebir mi ---------------------------------
        motor_ayni = {f: (se["motor_sha256_16"].get(f) == sc["motor_sha256_16"].get(f)
                          and se["motor_sha256_16"].get(f) is not None)
                      for f in ("broker.py", "backtest.py", "strategy.py")}     # C'nin kaydettiği üçlü
        config_ayni = {f: (se["config_sha256_16"][f]["sandbox"] == sc["config_sha256_16"][f]["sandbox"]
                           and se["config_sha256_16"][f]["sandbox"] is not None)
                       for f in ("goal.yaml", "strategy.yaml", "bounds.yaml")}
        serh = None
        if not all(motor_ayni.values()) or not all(config_ayni.values()):
            serh = ("MOTOR/CONFIG SHA'LARI C İLE BİREBİR DEĞİL — kıyas ŞERHLİ: "
                    f"motor={motor_ayni} config={config_ayni}")
        rampa_ayni = (se["rampa"]["tam_dd"] == sc["rampa"]["tam_dd"] == 0.15
                      and se["rampa"]["sifir_dd"] == sc["rampa"]["sifir_dd"] == 0.36)
        tarih_e = [s["date"] for s in E["seans"]]
        takvim_ayni = (tarih_e == tarih_c)

        # ---- skor kimliği: C budget>0 seanslarında hücre skoru == C bütçesi ------------------
        e_seans_by_date = {s["date"]: s for s in E["seans"]}
        skor_uyusmaz = []
        for d0, s0 in C_seans_by_date.items():
            b0 = s0.get("exposure_budget_pct")
            if b0 and b0 > 0:
                e0 = e_seans_by_date.get(d0)
                if e0 is None or e0.get("exposure_score") != b0:
                    skor_uyusmaz.append({"date": d0, "C_budget": b0,
                                         "hucre_skor": None if e0 is None else e0.get("exposure_score")})

        # ---- eşlenik ay-kümeli bootstrap: Δn, Δpnl, Δsharpe, Δmaxdd --------------------------
        grC, grE = ay_grup(C["islem"]), ay_grup(E["islem"])
        rng = np.random.default_rng(BOOT_SEED)
        d_n = np.empty(BOOT_ITER)
        d_pnl = np.empty(BOOT_ITER)
        d_sh: list[float] = []
        d_dd: list[float] = []
        oran: list[float] = []
        sh_atlanan = dd_atlanan = 0
        idx_all = np.arange(M)
        for i in range(BOOT_ITER):
            pick = rng.choice(idx_all, size=M, replace=True)      # EŞLENİK: aynı çekiliş iki koşuma
            nC_i, pC_i, shC_i, ddC_i = iter_metrikler(grC, pick)
            nE_i, pE_i, shE_i, ddE_i = iter_metrikler(grE, pick)
            d_n[i] = nE_i - nC_i
            d_pnl[i] = pE_i - pC_i
            if nC_i > 0:
                oran.append(nE_i / nC_i)
            if shC_i == shC_i and shE_i == shE_i:
                d_sh.append(shE_i - shC_i)
            else:
                sh_atlanan += 1
            if ddC_i == ddC_i and ddE_i == ddE_i:
                d_dd.append(ddE_i - ddC_i)
            else:
                dd_atlanan += 1

        nC, nE = len(C["islem"]), len(E["islem"])
        fark_ci = ci95(d_n)
        pnl_ci = ci95(d_pnl)
        sh_ci = ci95(d_sh)
        dd_ci = ci95(d_dd)
        oran_ci = ci95(oran)

        # ---- işlem-kümesi eşlemesi: EKLENEN / ÇIKAN / ORTAK ----------------------------------
        E_kimlik = {(str(t["ts_open"])[:10], t["ticker"]) for t in E["islem"]}
        E_by_kimlik = {(str(t["ts_open"])[:10], t["ticker"]): t for t in E["islem"]}
        eklenen_k = sorted(E_kimlik - C_kimlik)
        cikan_k = sorted(C_kimlik - E_kimlik)
        ortak_k = sorted(C_kimlik & E_kimlik)
        eklenen = [E_by_kimlik[k] for k in eklenen_k]
        cikan = [C_by_kimlik[k] for k in cikan_k]
        kayan = []
        ortak_dpnl = 0.0
        for k in ortak_k:
            a, b = C_by_kimlik[k], E_by_kimlik[k]
            ortak_dpnl += float(b.get("pnl_dollars", 0.0)) - float(a.get("pnl_dollars", 0.0))
            if (str(a.get("ts_close"))[:10] != str(b.get("ts_close"))[:10]
                    or a.get("exit_reason") != b.get("exit_reason")
                    or abs(float(a.get("r_multiple") or 0) - float(b.get("r_multiple") or 0)) > 1e-9):
                kayan.append(k)

        def _kume_ozet(ts: list[dict]) -> dict | None:
            if not ts:
                return None
            rs = [float(t.get("r_multiple") or 0.0) for t in ts]
            reg: dict[str, dict] = {}
            for t in ts:
                g = reg.setdefault(str(t.get("regime")), {"n": 0, "r_toplam": 0.0, "pnl": 0.0})
                g["n"] += 1
                g["r_toplam"] += float(t.get("r_multiple") or 0.0)
                g["pnl"] += float(t.get("pnl_dollars") or 0.0)
            for g in reg.values():
                g["ort_r"] = round(g["r_toplam"] / g["n"], 3)
                g["pnl"] = round(g["pnl"], 2)
                del g["r_toplam"]
            ex: dict[str, int] = {}
            st: dict[str, int] = {}
            for t in ts:
                ex[str(t.get("exit_reason"))] = ex.get(str(t.get("exit_reason")), 0) + 1
                st[str(t.get("setup"))] = st.get(str(t.get("setup")), 0) + 1
            return {"n": len(ts), "ort_r": round(sum(rs) / len(rs), 3),
                    "medyan_r": round(float(np.median(rs)), 3),
                    "pnl_toplam": round(sum(float(t.get("pnl_dollars") or 0.0) for t in ts), 2),
                    "kazanma_orani": round(sum(1 for r in rs if r > 0) / len(rs), 3),
                    "rejim_kirilimi": dict(sorted(reg.items(), key=lambda kv: -kv[1]["n"])),
                    "exit_reason_dagilim": dict(sorted(ex.items(), key=lambda kv: -kv[1])),
                    "setup_dagilim": dict(sorted(st.items(), key=lambda kv: -kv[1])),
                    "aylik_n": {a: sum(1 for t in ts if str(t["ts_open"])[:7] == a)
                                for a in sorted({str(t["ts_open"])[:7] for t in ts})}}

        # ---- EKLENEN ort-R tek-örneklem ay-kümeli bootstrap CI -------------------------------
        ekl_r_ci = None
        ekl_r_ci_neden = None
        ekl_aylar = sorted({str(t["ts_open"])[:7] for t in eklenen})
        if len(ekl_aylar) >= 2:
            gr = {a: [float(t.get("r_multiple") or 0.0)
                      for t in eklenen if str(t["ts_open"])[:7] == a] for a in ekl_aylar}
            rng2 = np.random.default_rng(BOOT_SEED)
            m2 = len(ekl_aylar)
            ort = np.empty(BOOT_ITER)
            for i in range(BOOT_ITER):
                pk = rng2.choice(np.arange(m2), size=m2, replace=True)
                hav: list[float] = []
                for j in pk:
                    hav.extend(gr[ekl_aylar[j]])
                ort[i] = float(np.mean(hav)) if hav else float("nan")
            ekl_r_ci = ci95(ort)
        else:
            ekl_r_ci_neden = (f"eklenen işlemler {len(ekl_aylar)} ay kümesinde — ay-kümeli CI için "
                              "<2 küme; olculemedi (None)")

        # ---- eklenen işlemlerin arm-günü analizi ---------------------------------------------
        # arm günü = ts_open'dan önceki seans (hücre takviminde). C'de o gün bütçe kapalı mıydı?
        idx_by_date = {d: i for i, d in enumerate(tarih_e)}
        arm_c_kapali = arm_c_acik = arm_bulunamadi = 0
        arm_skor_bant: dict[str, int] = {}
        for t in eklenen:
            d0 = str(t["ts_open"])[:10]
            i0 = idx_by_date.get(d0)
            if i0 is None or i0 == 0:
                arm_bulunamadi += 1
                continue
            arm_d = tarih_e[i0 - 1]
            cs = C_seans_by_date.get(arm_d)
            if cs is None:
                arm_bulunamadi += 1
                continue
            if (cs.get("exposure_budget_pct") or 0) > 0:
                arm_c_acik += 1
            else:
                arm_c_kapali += 1
            es = e_seans_by_date.get(arm_d) or {}
            b = _skor_bandi(es.get("exposure_score"))
            arm_skor_bant[b] = arm_skor_bant.get(b, 0) + 1

        # ---- kill bayrakları (kart, DONUK — koşul kaydı, hüküm değil) ------------------------
        kill1 = {
            "esik": f"eklenen işlem <{KILL1_MIN_EKLENEN}/hücre → OLCULEMEDI (kart kill#1)",
            "eklenen_n": len(eklenen),
            "tetiklendi": len(eklenen) < KILL1_MIN_EKLENEN,
            "beyan": (None if len(eklenen) >= KILL1_MIN_EKLENEN else
                      f"eklenen {len(eklenen)} < {KILL1_MIN_EKLENEN} — bu hücre OLCULEMEDI"),
        }
        kill2 = {
            "esik": ("şasi bütünlüğü (koşum-içi kontroller + eşik-yankı + bütçe-kural + "
                     "motor/config sha == C + takvim + skor-kimliği) bozuksa GEÇERSİZ (kart kill#2)"),
            "hucre_butunluk": se["butunluk"]["gecerli"],
            "C_butunluk": sc["butunluk"]["gecerli"],
            "motor_sha_ayni": all(motor_ayni.values()),
            "config_sha_ayni": all(config_ayni.values()),
            "rampa_ayni_15_36": rampa_ayni,
            "takvim_ayni": takvim_ayni,
            "skor_kimligi_uyusmaz_n": len(skor_uyusmaz),
            "skor_kimligi_ornek": skor_uyusmaz[:5],
            "tetiklendi": not (se["butunluk"]["gecerli"] and sc["butunluk"]["gecerli"]
                               and all(motor_ayni.values()) and all(config_ayni.values())
                               and rampa_ayni and takvim_ayni and not skor_uyusmaz),
        }
        ddc = sc["performans"].get("maxdd_kanonik")
        dde = se["performans"].get("maxdd_kanonik")
        dd_kosul = {
            "not": ("HÜKÜM GİRDİSİ (kart success_metric) — kill değil: dd_hücre vs C×1.5 kaydı; "
                    "hüküm Rol-1'in"),
            "maxdd_C": ddc, "maxdd_hucre": dde,
            "oran": round(dde / ddc, 3) if (ddc not in (None, 0) and dde is not None) else None,
            "C_x1p5_ustunde": (dde > DD_KOSUL_KATSAYI * ddc)
            if (ddc not in (None, 0) and dde is not None) else None,
        }

        perf_c, perf_e = sc["performans"], se["performans"]

        def satir(*yol):
            def cek(s):
                v = s
                for kk in yol:
                    v = v.get(kk) if isinstance(v, dict) else None
                    if v is None:
                        return None
                return v
            return {"C_esik40": cek(sc), f"hucre_esik{HUCRELER[hucre]}": cek(se)}

        tablo = {
            "islem_n": {"C_esik40": nC, f"hucre_esik{HUCRELER[hucre]}": nE, "fark": nE - nC,
                        "fark_pct": round(100.0 * (nE - nC) / nC, 1) if nC else None},
            "islem_yil": satir("islem", "islem_yil"),
            "islem_fark_ci95": fark_ci, "islem_oran_ci95": oran_ci,
            "net_pnl_equity": satir("performans", "net_pnl_equity"),
            "net_pnl_trades": satir("performans", "net_pnl_trades"),
            "net_pnl_fark_ci95": pnl_ci,
            "maxdd_kanonik": satir("performans", "maxdd_kanonik"),
            "maxdd_m2m": satir("performans", "maxdd_m2m"),
            "maxdd_fark_ci95_kapali_islem_egrisi": dd_ci,
            "maxdd_ci_atlanan_iter": dd_atlanan,
            "sharpe": satir("performans", "sharpe"),
            "sharpe_fark_ci95": sh_ci,
            "sharpe_ci_atlanan_iter": sh_atlanan,
            "avg_r": satir("performans", "avg_r"),
            "win_rate": satir("performans", "win_rate"),
            "score": satir("performans", "score"),
            "total_return": satir("performans", "total_return"),
            "silahlanan_plan": satir("islem", "silahlanan_plan"),
            "toplam_plan": satir("islem", "toplam_plan"),
            "verdict_dagilim": satir("islem", "verdict_dagilim"),
            "nogo_neden_dagilim": satir("islem", "nogo_neden_dagilim"),
            "review_neden_dagilim": satir("islem", "review_neden_dagilim"),
            "entry_rejects": satir("islem", "entry_rejects"),
            "exit_reason_dagilim": satir("islem", "exit_reason_dagilim"),
            "doluluk_pozisyon_gun": satir("doluluk", "pozisyon_gun_open_fazi"),
            "ort_acik_pozisyon": satir("doluluk", "ort_acik_pozisyon"),
            "tasnif_tum_seans": satir("tasnif_tum_seans", "dagilim"),
            "rejim_butce_hucre": se.get("rejim_butce"),
            "tepe_isi_ozet": {
                "C_esik40": {"nominal_open_max": (sc["tepe_isi"]["nominal_open_fazi_R"] or {}).get("max"),
                             "gerceklesen_sizeR_max": ((sc["tepe_isi"].get("gerceklesen_open_fazi") or {})
                                                       .get("size_r_toplam") or {}).get("max"),
                             "eszamanli_poz_max": sc["tepe_isi"]["eszamanli_poz_max"]},
                f"hucre_esik{HUCRELER[hucre]}": {
                    "nominal_open_max": (se["tepe_isi"]["nominal_open_fazi_R"] or {}).get("max"),
                    "gerceklesen_sizeR_max": ((se["tepe_isi"].get("gerceklesen_open_fazi") or {})
                                              .get("size_r_toplam") or {}).get("max"),
                    "eszamanli_poz_max": se["tepe_isi"]["eszamanli_poz_max"]},
            },
        }

        # pnl ayrıştırma kimliği: Δ(Σpnl) == Σeklenen + Σortak_Δ − Σçıkan (kalıntı ~0 olmalı)
        d_pnl_nokta = round(float(perf_e.get("net_pnl_trades") or 0) - float(perf_c.get("net_pnl_trades") or 0), 2)
        ekl_pnl = round(sum(float(t.get("pnl_dollars") or 0.0) for t in eklenen), 2)
        cik_pnl = round(sum(float(t.get("pnl_dollars") or 0.0) for t in cikan), 2)
        kalinti = round(d_pnl_nokta - (ekl_pnl + round(ortak_dpnl, 2) - cik_pnl), 2)

        return {
            "hucre": hucre, "esik": HUCRELER[hucre],
            "sasi_kimligi": {"motor_sha_ayni": motor_ayni, "config_sha_ayni": config_ayni,
                             "rampa_ayni_15_36": rampa_ayni, "takvim_ayni": takvim_ayni,
                             "skor_kimligi_uyusmaz_n": len(skor_uyusmaz), "serh": serh},
            "tablo": tablo,
            "islem_kumesi": {
                "kimlik": "(ts_open, ticker)",
                "ortak_n": len(ortak_k), "eklenen_n": len(eklenen), "cikan_n": len(cikan),
                "ortak_cikis_kayan_n": len(kayan),
                "ortak_pnl_farki": round(ortak_dpnl, 2),
                "pnl_ayristirma": {"delta_net_pnl_trades": d_pnl_nokta,
                                   "eklenen_pnl": ekl_pnl, "cikan_pnl": cik_pnl,
                                   "ortak_delta_pnl": round(ortak_dpnl, 2), "kalinti": kalinti},
            },
            "eklenen_analiz": {
                "ozet": _kume_ozet(eklenen),
                "ort_r_ci95_ay_kumeli": ekl_r_ci,
                "ort_r_ci_olculemedi_neden": ekl_r_ci_neden,
                "arm_gunu": {"C_de_kapali_gunden": arm_c_kapali, "C_de_acik_gunden_knockon": arm_c_acik,
                             "arm_gunu_bulunamadi": arm_bulunamadi,
                             "arm_gunu_skor_bandi": dict(sorted(arm_skor_bant.items())),
                             "tanim": ("arm = ts_open'dan önceki seans; C'de o seans "
                                       "exposure_budget_pct∈{0,None} ise 'kapalı günden'")},
            },
            "cikan_analiz": {"ozet": _kume_ozet(cikan),
                             "beyan": ("çıkanlar yan-etkidir (knock-on): erken eklenen işlemler "
                                       "slot/ısı/equity yolunu değiştirir; C'deki bu işlemler hücrede "
                                       "oluşmadı")},
            "kill1_eklenen_min30": kill1,
            "kill2_sasi_butunlugu": kill2,
            "dd_kosul_kaydi_x1p5": dd_kosul,
        }

    hucre_sonuclari = {h: hucre_kiyas(h) for h in HUCRELER}

    out = {
        "kart": "EDG-2026-030",
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "smoke": smoke,
        "kiyas_taban": {
            "kaynak": "EDG-026 C (slot20+0.5R+rampa15/36) HAZIR çıktıları — yeniden koşulmadı, salt-okundu",
            "dosyalar": {ad: str(c_dir / f"{ad}_c{ek}.json") for ad in ("sonuc", "seanslar", "islemler")},
            "sha256": c_sha,
        },
        "yontem": {
            "eslenik_bootstrap": (f"ay-kümeli EŞLENİK bootstrap (iter={BOOT_ITER}, seed={BOOT_SEED}, "
                                  f"n_ay={M}): aynı ay çekilişi iki koşuma birden; fark = hücre − C; "
                                  "metrikler iterasyon içinde kanonik formüllerle yeniden hesaplanır"),
            "islem_ay_anahtari": "ts_open[:7] (giriş ayı)",
            "sharpe_boot": ("kanonik score_detail formülü; span = tam pencere gün sayısı (sabit); "
                            "n≤2 veya std=0 iterasyonları atlanır (sayı raporlu)"),
            "maxdd_boot": ("kanonik equity_curve (ts_close sıralı) + max_drawdown, çekilen ayların "
                           "işlemleri takvim sırasında; ay yeniden-örneklemesi dd zaman-sırasını "
                           "yapay kurar — CI bu beyanla okunur; NOKTA dd motor kanonik"),
            "eklenen_r_ci": "tek-örneklem ay-kümeli bootstrap (yalnız eklenen işlemlerin ayları)",
        },
        "hucreler": hucre_sonuclari,
        "dosyalar": {h: {"sonuc": f"sonuc_{h}{ek}.json", "seanslar": f"seanslar_{h}{ek}.json",
                         "islemler": f"islemler_{h}{ek}.json"} for h in HUCRELER},
        "hukum": None,   # HÜKÜM YAZILMAZ — Rol-1'in
    }
    (yerel / "sonuc.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))

    print(f"\n==================== EDG-030 KIYAS ÖZETİ{ek} ====================")
    for h, hs in hucre_sonuclari.items():
        t = hs["tablo"]
        ek_a = hs["eklenen_analiz"]["ozet"]
        he = "hucre_esik" + str(hs["esik"])
        print(f"\n--- hücre {h} (esik {hs['esik']}) ---")
        print(f"şasi: serh={hs['sasi_kimligi']['serh']}  takvim={hs['sasi_kimligi']['takvim_ayni']}  "
              f"skor_uyusmaz={hs['sasi_kimligi']['skor_kimligi_uyusmaz_n']}")
        print(f"işlem: C {t['islem_n']['C_esik40']} → {t['islem_n'][he]} "
              f"(fark {t['islem_n']['fark']})  ΔCI95={t['islem_fark_ci95']}")
        print(f"net_pnl: {t['net_pnl_trades']}  ΔCI95={t['net_pnl_fark_ci95']}")
        print(f"maxdd: {t['maxdd_kanonik']}  ΔCI95(kapalı-işlem)={t['maxdd_fark_ci95_kapali_islem_egrisi']}")
        print(f"sharpe: {t['sharpe']}  ΔCI95={t['sharpe_fark_ci95']}")
        print(f"küme: ortak={hs['islem_kumesi']['ortak_n']} eklenen={hs['islem_kumesi']['eklenen_n']} "
              f"çıkan={hs['islem_kumesi']['cikan_n']} kayan={hs['islem_kumesi']['ortak_cikis_kayan_n']}")
        if ek_a:
            print(f"eklenen: n={ek_a['n']} ort_r={ek_a['ort_r']} CI={hs['eklenen_analiz']['ort_r_ci95_ay_kumeli']} "
                  f"rejim={ {k: v['n'] for k, v in ek_a['rejim_kirilimi'].items()} }")
        print(f"KILL#1 tetiklendi={hs['kill1_eklenen_min30']['tetiklendi']}  "
              f"KILL#2 tetiklendi={hs['kill2_sasi_butunlugu']['tetiklendi']}  "
              f"dd×1.5 koşulu={hs['dd_kosul_kaydi_x1p5']['C_x1p5_ustunde']}")
    print(f"\nyazıldı: {yerel/'sonuc.json'}")
    print("KIYAS_BITTI")


if __name__ == "__main__":
    argv = sys.argv[1:]
    smoke = "--smoke" in argv
    argv = [a for a in argv if a != "--smoke"]
    if argv and argv[0] == "kosum" and len(argv) > 1:
        kosum(argv[1], smoke=smoke)
    elif argv and argv[0] == "kiyas":
        kiyas(smoke=smoke)
    else:
        sys.exit("kullanım: olcum.py kosum {e30|e20} [--smoke] | olcum.py kiyas [--smoke]")

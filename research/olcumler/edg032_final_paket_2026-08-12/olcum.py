"""EDG-2026-032 — FİNAL-PAKET DOĞRULAMA (C+mb) · ölçüm aracı (2026-08-12)

Kart: research/cards/EDG-2026-032-final-paket-dogrulama.yaml (OKU-DOKUNMA; kapı hükmü Rol-1'in).
Rol: ÖLÇÜM ajanı. Bu modül HÜKÜM VERMEZ, karta dokunmaz, git/canlı/broker/state'e YAZMAZ.

ŞASİ: EDG-026 (research/olcumler/edg026_slot20_2026-08-12/olcum.py) AYNEN devralındı —
C dünyası DONUK: rampa 15/36 monkeypatch (beyanlı) + max_open_positions=20 (goal/limits
enjeksiyonu) + position_size_r=0.5 (strateji params enjeksiyonu) + zarf 5R DOKUNULMADI;
izole sandbox, kancalar, bütünlük kontrolleri, eşlenik ay-kümeli bootstrap (5000, seed 20260812).

TEK KOŞUM (CMB = C + momentum_burst silahlı) — kart features_asof, DONUK:
  C-şasi AYNEN (yukarıdaki üç kalem)
  + params["entry.armed_extra"] = ["momentum_burst"]   (ENJEKSİYON 3 — MOTORUN KENDİ KANALI)

MB-SİLAHLAMA KANALI (ARMED_SETUPS/strategy.py'ye DOKUNULMAZ; monkeypatch DEĞİL):
  * arming.py:317 emsali: `cand_params = {**params, "entry.armed_extra": [setup]}` — motorun
    kendi ölçüm kanalı; 025 replay_kol.py `mb_silahli` kolu birebir bu deseni kullandı.
  * strategy.py scan_entry: `extra = tuple(params.get("entry.armed_extra") or ())` →
    `for setup in ARMED_SETUPS + extra` — tuple sırası gereği momentum_burst en DÜŞÜK
    önceliklidir (canlı yasa birebir; silahlı üçlü önce ateşler).
  * ÖZ-SINAMA (koşum öncesi, kancalar takılmadan): strategy.scan_all GEÇİCİ stub'lanır,
    (a) extra'lı params ile scan_entry mb-sinyalini DÖNER, (b) extra'sız params ile None döner,
    (c) silahlı kurulum + mb birlikte varken silahlı kurulum ÖNCE seçilir (öncelik yasası).
    Stub restore edilir ve restore ASSERT'lenir. Ayrıca resolve_params 4 rejimde de
    entry.armed_extra'yı taşıyor mu kanıtlanır (params_by_regime sızıntı kontrolü).
  * Koşum SONRASI: ARMED_SETUPS hâlâ ("breakout_vcp","pullback","exhaustion_hammer") assert'i
    (global duruma dokunulmadığının çalışma-zamanı kanıtı) + plan/işlem defterinde mb sayımı.

KIYAS TABANI: EDG-026'nın HAZIR C çıktıları (sonuc_c/seanslar_c/islemler_c — YENİDEN KOŞULMAZ,
okunur; dosya sha256'ları künyeye yazılır). Motor/config sha'ları C kaydıyla birebir DOĞRULANIR;
değilse kıyas ŞERHLİ.

TANIMLAR (ölçümden ÖNCE donduruldu; sonuç görüldükten sonra değişmez):
  islem            = kapanmış işlem satırı (broker.closed; eod/delisted markout DAHİL).
  ay kümesi        = ts_open[:7] (giriş ayı) — şasi tanımı AYNEN.
  eşlenik bootstrap= ay-kümeli EŞLENİK bootstrap: takvimin ay listesi üzerinden aynı ay çekilişi
                     iki koşuma birden (yerine-koymalı, 5000 iter, seed 20260812);
                     fark = CMB − C. Uygulandığı üç seri: işlem sayısı, işlem-P&L ay toplamı,
                     havuzlanmış ort-R (ΣR/Σn; payda 0 iterasyonu atlanır + sayısı raporlanır).
  max-dd           = motor-kanonik score.score_detail.max_drawdown (kapalı-işlem ∨ günlük M2M
                     kötüsü). Kapı (ii) BUNUN üstünden.
  net P&L          = M2M equity son değer − START_EQUITY; çapraz: Σ pnl_dollars.
  mb-karnesi       = setup=="momentum_burst" işlemleri: n, ort-R, win, P&L; CI birincil =
                     ay-kümeli (ts_open[:7], şasi tanımı), duyarlılık = çıkış-günü-kümeli
                     (ts_close[:10], 025 bacak-b deseni).
  slot-çalma       = CMB'nin mb-DIŞI işlemleri ↔ C'nin TÜM işlemleri (C'de mb dormant'tı):
                     kurulum-bazında n/P&L/ort-R tablosu + eşlenik ay-kümeli CI (n ve P&L farkı).

KAPI-ÖLÇÜTLERİ (kart success_metric, DONUK — geçti/düştü İŞARETLENİR, hüküm YAZILMAZ):
  (i)   net P&L farkı (CMB−C) eşlenik ay-kümeli %95 CI ÜST ucu ≥ 0
  (ii)  maxdd_kanonik_CMB ≤ maxdd_kanonik_C × 1.3   (0.1235 × 1.3 = 0.16055 ≈ 0.1606)
  (iii) sharpe_CMB ≥ 0.20

KILL KONTROLLERİ (kart, DONUK — koşul değerinin kaydı, hüküm DEĞİL):
  kill#1 (şasi): bütünlük bozuksa (frame_miss/dup/scan!=plan/yasak modül/base_max!=20) ∨ motor-
         config sha'ları C ile uyuşmuyorsa ∨ takvim farklıysa → ölçüm GEÇERSİZ beyanı.
  kill#2 (mb-n): mb işlem sayısı < 20 → mb-karnesi "olculemedi" damgası; paket-kapısı yine
         üç ölçütle işler (kart açık hükmü).

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen = None + neden); YASA-4 (sessiz-yutma işaretli + gerekçe);
YASA-6 (okuyucu: sonuc_cmb.json + seanslar_cmb + islemler_cmb → `kiyas` tüketir; sonuc.json →
dönüş raporu + Rol-1). SALT-OKUMA: config.STATE koşum-başına izole sandbox; barlar sembolik
bağla SALT-OKUNUR; canlı state'e ve motor dosyalarına tek bayt yazılmaz. meridian.loop /
counterfactual / cf_backfill / hermes İTHAL EDİLMEZ — sys.modules ile KANITLANIR.

KULLANIM:
  olcum.py cmb            # koşum CMB → sonuc_cmb.json + seanslar_cmb.json + islemler_cmb.json
  olcum.py kiyas          # CMB (yerel) + C (EDG-026 hazır çıktıları) → sonuc.json
  (--smoke: kısa pencere 2022-01-01→2022-06-30, çıktılar smoke/ altına — şasi + kanal provası)
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

# tek-iş parçacığı: determinizm + ölçüm gürültüsüzlüğü (şasi ile aynı)
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

REPLAY_START = "2022-01-01"
REPLAY_END = "2026-07-30"                      # kart: C (EDG-026) ile AYNI pencere
BOOT_SEED = 20260812
BOOT_ITER = 5000

# koşum CMB'nin DONUK parametreleri (kart features_asof)
RAMPA = {"tam_dd": 0.15, "sifir_dd": 0.36}     # C ile aynı — monkeypatch (beyan başlıkta)
SLOT = 20                                      # goal/limits enjeksiyonu (C ile aynı)
BOYUT_R = 0.5                                  # strateji params enjeksiyonu (C ile aynı)
MB_EXTRA = ["momentum_burst"]                  # ENJEKSİYON 3 — motorun kendi kanalı (arming.py:317)
ARMED_BEKLENEN = ("breakout_vcp", "pullback", "exhaustion_hammer")   # repo ARMED_SETUPS (dokunulmaz)

# kapı-ölçütleri (kart success_metric, DONUK)
KAPI_DD_KATSAYI = 1.3
KAPI_SHARPE_MIN = 0.20
KILL_MB_N = 20                                 # kart kill#2: mb işlem <20 → karne olculemedi

KART3 = ["tavan_sifir", "evren_bagladi", "derisk_bagladi"]
YASAK = ("meridian.loop", "meridian.counterfactual", "meridian.cf_backfill", "meridian.hermes")

# NO_GO/REVIEW neden eşlemesi (şasi AYNEN — guard.py sabit alt-dizgileri; eşleşmeyen HAM sayılır)
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


def _sha(p: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    except OSError:
        return None    # ölçülemedi (dosya yok/okunamadı) — None, uydurma özet değil


def _neden_dagit(nedenler_listesi) -> dict:
    """gate_reasons dizgilerini sabit kontrol adlarına indirger; eşleşmeyen ham kalır."""
    c: dict[str, int] = {}
    for neden in nedenler_listesi:
        ad = None
        for kontrol, parca in NEDEN_ESLEME:
            if parca in neden:
                ad = kontrol
                break
        c[ad or f"HAM:{neden[:80]}"] = c.get(ad or f"HAM:{neden[:80]}", 0) + 1
    return dict(sorted(c.items(), key=lambda kv: -kv[1]))


# ---------------------------------------------------------------------------------------------
# SANDBOX HAZIRLIĞI — izole state (EDG-022'nin DONMUŞ config kopyalarından; şasi AYNEN)
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
            # kaynak = EDG-022'nin DONMUŞ kopyaları (tutarlılık çivisi — C de aynı kaynaktan koştu).
            # DOSYALAR DEĞİŞTİRİLMEZ: slot/boyut/mb enjeksiyonu YÜKLENMİŞ sözlüklere yapılır ki
            # config sha'ları C ile bayt-aynı kalsın ve şasi kimliği sha ile kanıtlansın.
            shutil.copyfile(EDG022 / "state" / f, dst)
    return st


# ---------------------------------------------------------------------------------------------
# RAMPA — orijinal formülün birebir parametrize kopyası (şasi AYNEN)
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
# SINIFLAMA + BOOTSTRAP + ISI — şasi fonksiyonları AYNEN
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
    """Ay-kümeli bootstrap %95 CI — şasi fonksiyonu AYNEN (bitişik günler bağımlı;
    iid gün çekimi CI'yi sahte-daraltır)."""
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
    """Isı serisinin özeti: max + persentiller + histogram (0.5R kovaları). Boş → None."""
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
    """Seans-başına eşzamanlı pozisyon (işlem aralıklarından): ts_open ≤ seans ≤ ts_close."""
    araliklar = [(str(t["ts_open"])[:10], str(t["ts_close"])[:10]) for t in islemler
                 if t.get("ts_open") and t.get("ts_close")]
    out = []
    for d in takvim:
        out.append(sum(1 for a, b in araliklar if a <= d <= b))
    return out


def _setup_ozet(ts: list[dict]) -> dict:
    """Kurulum-bazında n / P&L / ort-R (025 bacak-b _setup_ozet deseni)."""
    by: dict[str, dict] = {}
    for t in ts:
        b = by.setdefault(t.get("setup") or "?", {"n": 0, "pnl": 0.0, "sum_r": 0.0, "n_r": 0})
        b["n"] += 1
        b["pnl"] += float(t.get("pnl_dollars") or 0.0)
        if t.get("r_multiple") is not None:
            b["sum_r"] += float(t["r_multiple"])
            b["n_r"] += 1
    return {s: {"n": v["n"], "pnl": round(v["pnl"], 2),
                "avg_r": round(v["sum_r"] / v["n_r"], 4) if v["n_r"] else None}
            for s, v in sorted(by.items())}


# ---------------------------------------------------------------------------------------------
# TEK KOŞUM (CMB — slot20_r05 + momentum_burst silahlı)
# ---------------------------------------------------------------------------------------------
def kosum(smoke: bool = False):
    outdir = (SANDBOX / "smoke") if smoke else SANDBOX
    outdir.mkdir(exist_ok=True)
    r_start, r_end = (REPLAY_START, "2022-06-30") if smoke else (REPLAY_START, REPLAY_END)

    st_dir = hazirla("cmb" + ("_smoke" if smoke else ""))
    sys.path.insert(0, str(REPO))

    from meridian import config
    # SALT-OKUMA İZOLASYONU: her yazım (obs.events, history) sandbox'a düşer, canlı state'e DEĞİL
    config.STATE = st_dir
    config.BARS = st_dir / "bars"
    config.HISTORY = st_dir / "history"

    import numpy as np                     # noqa: F401
    import yaml
    from meridian import backtest, dataset, score as score_mod

    # motorun yamalanmadığını çivile + YASAKLI modül kanıtı (ithal ÖNCESİ)
    assert not hasattr(backtest, "wpg_overlay_day"), "motor YAMALI görünüyor — ölçüm geçersiz"
    assert not [m for m in sys.modules if m in YASAK], "yasaklı modül ithal edilmiş"

    brk = backtest.brk                     # meridian.broker modülü
    strat = backtest.strat                 # meridian.strategy modülü
    ORIJ_DERISK = brk.derisk_mult          # orijinal fonksiyon nesnesi (kayıt için)

    # ---- rampa kurulumu + öz-sınama (şasi AYNEN; yayılım kanıtı 5 VE 20 tabanla) -------------
    brk.derisk_mult = _rampa_fn(RAMPA["tam_dd"], RAMPA["sifir_dd"])
    assert brk.derisk_mult is not ORIJ_DERISK
    assert brk.derisk_mult(90.0, 100.0) == 1.0
    assert abs(brk.derisk_mult(80.0, 100.0) - 0.7619) < 1e-9
    assert brk.derisk_mult(64.0, 100.0) == 0.0
    assert brk.max_positions_at(80.0, 100.0, 5) == 4       # round(5×0.7619)=4 (023 çivisi)
    assert brk.max_positions_at(80.0, 100.0, 20) == 15     # round(20×0.7619)=15 (slot-20 tabanı)

    # ---- girdiler + PARAM-ENJEKSİYONLARI (dosya DEĞİŞMEZ; sözlükler değişir, beyan başlıkta) -
    stg = yaml.safe_load((st_dir / "strategy.yaml").read_text())
    params = dict(stg["params"])
    by_regime = stg.get("params_by_regime") or None
    sv = int(stg.get("version"))
    goal = config.goal()                                   # derin kopya — dosyaya/önbelleğe sızmaz

    onceki = {"max_open_positions": int(goal["limits"]["max_open_positions"]),
              "position_size_r": float(params["position_size_r"]),
              "entry.armed_extra": params.get("entry.armed_extra")}   # beklenen: yok (None)
    goal["limits"]["max_open_positions"] = SLOT            # ENJEKSİYON 1 (goal/limits — C ile aynı)
    params["position_size_r"] = BOYUT_R                    # ENJEKSİYON 2 (strateji params — C ile aynı)
    params["entry.armed_extra"] = list(MB_EXTRA)           # ENJEKSİYON 3 (motorun kendi kanalı —
    #                                                        arming.py:317 / 025 replay_kol deseni)

    # enjeksiyon öz-sınaması: rejim çözümü DÖRT rejimde de 0.5 VE mb-kanalını görmeli
    for _rg in ("trend_up", "trend_down", "chop", "high_vol"):
        _eff = config.resolve_params(params, by_regime, _rg)
        assert float(_eff["position_size_r"]) == BOYUT_R, f"rejim override sızıntısı: {_rg}"
        assert list(_eff.get("entry.armed_extra") or []) == MB_EXTRA, \
            f"entry.armed_extra rejim çözümünde kayboldu: {_rg}"
        _ovr = (by_regime or {}).get(_rg) or {}
        assert "position_size_r" not in _ovr, f"params_by_regime[{_rg}] position_size_r içeriyor"
        assert "entry.armed_extra" not in _ovr, f"params_by_regime[{_rg}] entry.armed_extra içeriyor"
    assert float(goal["limits"]["max_position_r"]) >= BOYUT_R          # yukarı-kırpma 0.5'i etkilemez
    limits = goal["limits"]
    max_open = int(limits["max_open_positions"])
    no_trade_before = int(limits.get("no_trade_before_bars", 0))
    assert max_open == SLOT

    # ---- MB-KANALI ÖZ-SINAMASI (kancalar takılmadan ÖNCE; stub geçici, restore assert'li) ----
    assert tuple(strat.ARMED_SETUPS) == ARMED_BEKLENEN, \
        f"repo ARMED_SETUPS beklenenden farklı: {strat.ARMED_SETUPS}"
    assert "momentum_burst" not in strat.ARMED_SETUPS      # mb repo'da DORMANT — kanal şart
    _orij_scan_all = strat.scan_all
    _mb_sinyal = {"kim": "mb_sentinel"}
    _bv_sinyal = {"kim": "bv_sentinel"}
    try:
        # (a) extra'lı params → scan_entry mb'yi SİLAHLI sayar (kanal gerçekten silahlıyor)
        strat.scan_all = lambda *a, **k: {"momentum_burst": _mb_sinyal}
        assert strat.scan_entry(None, params, 0, "SELFTEST") is _mb_sinyal, \
            "KANAL ÖLÜ: entry.armed_extra ile mb sinyali seçilmedi"
        # (b) extra'sız params → mb seçilmez (dormant yasası bozulmadı)
        p_yok = {k: v for k, v in params.items() if k != "entry.armed_extra"}
        assert strat.scan_entry(None, p_yok, 0, "SELFTEST") is None, \
            "DORMANT YASASI BOZUK: extra'sız taramada mb seçildi"
        # (c) öncelik: silahlı üçlü mb'den ÖNCE (tuple sırası — canlı yasa birebir)
        strat.scan_all = lambda *a, **k: {"momentum_burst": _mb_sinyal, "breakout_vcp": _bv_sinyal}
        assert strat.scan_entry(None, params, 0, "SELFTEST") is _bv_sinyal, \
            "ÖNCELİK BOZUK: mb, silahlı kurulumun önüne geçti"
    finally:
        strat.scan_all = _orij_scan_all
    assert strat.scan_all is _orij_scan_all                # restore kanıtı
    kanal_oz_sinama = {
        "a_extra_ile_silahlaniyor": True, "b_extrasiz_dormant": True,
        "c_oncelik_armed_once_mb_son": True,
        "yontem": ("strategy.scan_all GEÇİCİ stub (yalnız bu modül içinde, 3 çağrı); scan_entry "
                   "gerçek fonksiyon olarak çağrıldı; stub finally'de restore + is-assert. "
                   "Motor dosyasına dokunulmadı; ARMED_SETUPS değişmedi (koşum sonrası assert)"),
    }

    # ---- kancalar (şasi deseni AYNEN) --------------------------------------------------------
    seans_by_date: dict[str, dict] = {}
    _cur_close_date = [None]
    _dup: list[str] = []
    _frame_miss = [0]

    _orig_maxpos = brk.max_positions_at
    _orig_regime = backtest.regime_mod.build_regime_json
    _orig_scan = backtest.strat.scan_entry

    def _maxpos(equity, peak, base_max):
        n = _orig_maxpos(equity, peak, base_max)              # GERÇEK eff_max_open (15/36 rampası)
        fr = sys._getframe(1)
        loc = fr.f_locals
        d = loc.get("d")
        bar_i = loc.get("bar_i")
        broker = loc.get("broker")
        if d is None or broker is None:
            _frame_miss[0] += 1                               # sessiz-yutma DEĞİL: sayılır, geçerliliği bozar
            return n
        date = str(d.date())
        n_acik = len(broker.positions)                        # açılışta, fill'den ÖNCE
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

    t0 = dt.datetime.now()
    bars, index = dataset.load_cached()
    res = backtest.replay(params, bars, index, goal, r_start, r_end,
                          strategy_version=sv, params_by_regime=by_regime, with_gate_detail=False)
    sure = round((dt.datetime.now() - t0).total_seconds(), 1)

    # koşum sonrası kanıtlar: yasaklı modül yok + ARMED_SETUPS dokunulmamış (global durum temiz)
    yasak_yuklu = [m for m in sys.modules if m in YASAK]
    armed_sonrasi_ayni = tuple(strat.ARMED_SETUPS) == ARMED_BEKLENEN
    assert armed_sonrasi_ayni, f"ARMED_SETUPS koşum sonrasında değişmiş: {strat.ARMED_SETUPS}"

    # ---- plan_log çapraz-kontrolü + NO_GO/REVIEW neden dağılımı ------------------------------
    plan_aday: dict[str, int] = {}
    plan_silahli: dict[str, int] = {}
    nogo_nedenler: list[str] = []
    review_nedenler: list[str] = []
    verdict_n = {"GO": 0, "REVIEW": 0, "NO_GO": 0}
    silahli_size_r: list[float] = []
    plan_setup_n: dict[str, int] = {}
    mb_plan_verdict = {"GO": 0, "REVIEW": 0, "NO_GO": 0}
    for p in (res.plan_log or []):
        dts = str(p.get("date"))[:10]
        plan_aday[dts] = plan_aday.get(dts, 0) + 1
        v = p.get("gate_verdict")
        verdict_n[v] = verdict_n.get(v, 0) + 1
        su = p.get("setup") or "?"
        plan_setup_n[su] = plan_setup_n.get(su, 0) + 1
        if su == "momentum_burst":
            mb_plan_verdict[v] = mb_plan_verdict.get(v, 0) + 1
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
        r["aday_n"] = r["n_sinyal"]                           # TAM aday (CAPSIZ — şasi birincil kaynağı)
        r["silahli_n"] = plan_silahli.get(r["date"], 0)
        r["plan_aday"] = plan_aday.get(r["date"], 0)
        if r["n_sinyal"] != r["plan_aday"]:
            scan_vs_plan.append({"date": r["date"], "n_sinyal": r["n_sinyal"],
                                 "plan_aday": r["plan_aday"]})
        r["sinif"] = classify(r, no_trade_before)

    n_all = len(sess)
    base_max_bozuk = [r["date"] for r in sess if r["base_max_open"] != SLOT]   # enjeksiyon çivisi
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

    # ---- işlem/doluluk/ısı/performans metrikleri ---------------------------------------------
    trades = res.trades or []
    n_islem = len(trades)
    mb_islem_n = sum(1 for t in trades if t.get("setup") == "momentum_burst")
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

    takvim = [r["date"] for r in sess]
    aralik_sayim = _islem_araligi_sayimi(
        [{"ts_open": t.get("ts_open"), "ts_close": t.get("ts_close")} for t in trades], takvim)
    isi = {
        "formul": f"nominal = n_eszamanli × {BOYUT_R}R (kart formülü; conviction 0.6-1.0× nedeniyle ÜST SINIR)",
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

    eff_eq0 = sum(1 for r in sess if r["eff_max_open"] == 0)
    eff_eq1 = sum(1 for r in sess if r["eff_max_open"] == 1)
    eff_lt = sum(1 for r in sess if r["eff_max_open"] < max_open)
    slot_le0 = sum(1 for r in sess if r["acik_slot"] <= 0)
    dd_gt_tam = sum(1 for r in sess if r["dd"] > RAMPA["tam_dd"])
    size0 = sum(1 for r in sess if r["size_mult"] <= 0.0)

    tavan_pct_bir = round(100.0 * sum(1 for r in birincil if r["sinif"] == "tavan_sifir")
                          / n_bir, 2) if n_bir else None

    butunluk_gecerli = (_frame_miss[0] == 0 and not _dup and not scan_vs_plan
                        and not yasak_yuklu and not base_max_bozuk)

    out = {
        "kart": "EDG-2026-032", "kosum": "cmb_slot20_r05_mb", "smoke": smoke,
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sure_sn": sure,
        "rampa": {"tam_dd": RAMPA["tam_dd"], "sifir_dd": RAMPA["sifir_dd"],
                  "enjeksiyon": ("MONKEYPATCH — ölçüm modülü içinde broker.derisk_mult "
                                 "modül-özniteliği değiştirildi; motor DOSYASI değişmedi "
                                 "(EDG-023/026 şasi deseni AYNEN — beyan modül başlığında)")},
        "param_enjeksiyon": {
            "max_open_positions": {"once": onceki["max_open_positions"], "sonra": SLOT,
                                   "yuzey": "goal['limits'] (config.goal() derin kopyası — dosya değişmedi)"},
            "position_size_r": {"once": onceki["position_size_r"], "sonra": BOYUT_R,
                                "yuzey": ("strateji params sözlüğü (strategy.py _f yüzeyi; "
                                          "params_by_regime 4 rejimde boş — resolve_params assert'i "
                                          "koşum öncesi; 026 beyanı AYNEN)")},
            "entry.armed_extra": {"once": onceki["entry.armed_extra"], "sonra": MB_EXTRA,
                                  "yuzey": ("strateji params sözlüğü — MOTORUN KENDİ ölçüm kanalı "
                                            "(arming.py:317 `cand_params={**params, 'entry.armed_extra'...}` "
                                            "emsali; strategy.py scan_entry `ARMED_SETUPS + extra`; "
                                            "025 replay_kol.py mb_silahli deseni). ARMED_SETUPS/strategy.py "
                                            "DOKUNULMADI; monkeypatch DEĞİL — kanal param üzerinden akar")},
            "zarf_sabit": ("heat_hard_r=5.0R, heat_review_r=3.5R, max_position_r=1.0, "
                           "max_sector_exposure_pct=40 DEĞİŞMEDİ (kart: C-şasi AYNEN). "
                           "sector_cap paydası max_open_positions olduğundan sektör-başına fiili "
                           "tavan 8 (slot-20'nin motor-içi doğal sonucu, 026 beyanı AYNEN)"),
        },
        "mb_kanal": {
            "armed_setups_repo": list(ARMED_BEKLENEN),
            "armed_setups_kosum_sonrasi_ayni": armed_sonrasi_ayni,
            "armed_extra": MB_EXTRA,
            "oz_sinama": kanal_oz_sinama,
            "plan_setup_dagilim": dict(sorted(plan_setup_n.items(), key=lambda kv: -kv[1])),
            "mb_plan_verdict": mb_plan_verdict,
            "mb_islem_n": mb_islem_n,
        },
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
                                  "not": "motorun kendi maliyet modeli — dokunulmadı (kart: pessimistic_band_v2 rapor bandı ayrı)"}},
        "butunluk": {
            "frame_okunamadi": _frame_miss[0], "tekrar_tarih": _dup,
            "scan_vs_plan_uyusmazlik_n": len(scan_vs_plan),
            "scan_vs_plan_ornek": scan_vs_plan[:10],
            "yasakli_modul_yuklendi": yasak_yuklu,             # [] olmalı
            "base_max_open_bozuk": base_max_bozuk[:10],        # [] olmalı — enjeksiyon çivisi
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
            "setup_bazinda": _setup_ozet([{k: t.get(k) for k in
                                           ("setup", "pnl_dollars", "r_multiple")} for t in trades]),
        },
        "performans": {
            "net_pnl_equity": net_pnl_equity, "net_pnl_trades": net_pnl_trades,
            "maxdd_kanonik": detail.get("max_drawdown"),       # kapı (ii) BUNUN üstünden
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

    ek = "_smoke" if smoke else ""
    (outdir / f"sonuc_cmb{ek}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str))
    (outdir / f"seanslar_cmb{ek}.json").write_text(
        json.dumps(sess, ensure_ascii=False, default=str))
    slim = [{k: t.get(k) for k in ("ts_open", "ts_close", "ticker", "r_multiple",
                                   "pnl_dollars", "exit_reason", "bars_held", "regime",
                                   "setup", "qty", "risk_dollars", "size_r")} for t in trades]
    (outdir / f"islemler_cmb{ek}.json").write_text(
        json.dumps(slim, ensure_ascii=False, default=str))

    print(f"\n=========== EDG-032 KOŞUM [cmb_slot20_r05_mb{ek}] ===========")
    print(f"replay {r_start}→{r_end}  sv={sv}  sembol={len(bars)}  süre={sure}s")
    print(f"enjeksiyon: max_open {onceki['max_open_positions']}→{max_open}  "
          f"position_size_r {onceki['position_size_r']}→{params['position_size_r']}  "
          f"armed_extra {onceki['entry.armed_extra']}→{params['entry.armed_extra']}")
    print(f"mb-kanal öz-sınama: {kanal_oz_sinama['a_extra_ile_silahlaniyor']}/"
          f"{kanal_oz_sinama['b_extrasiz_dormant']}/{kanal_oz_sinama['c_oncelik_armed_once_mb_son']} "
          f"(silahlanıyor/dormant/öncelik)  ARMED_SETUPS sonrası aynı={armed_sonrasi_ayni}")
    print(f"bütünlük geçerli={out['butunluk']['gecerli']}  frame_miss={_frame_miss[0]} "
          f"dup={len(_dup)} scan!=plan={len(scan_vs_plan)} yasak={yasak_yuklu} "
          f"base_max_bozuk={len(base_max_bozuk)}")
    print(f"işlem n={n_islem} (mb={mb_islem_n})  net_pnl={net_pnl_equity}  "
          f"maxdd_kanonik={detail.get('max_drawdown')}  sharpe={detail.get('sharpe')}  "
          f"avg_r={detail.get('avg_r')}")
    print(f"plan setup dağılımı: {out['mb_kanal']['plan_setup_dagilim']}")
    print(f"mb plan verdict: {mb_plan_verdict}")
    print(f"NO_GO nedenleri: {out['islem']['nogo_neden_dagilim']}")
    print(f"yazıldı: {outdir}/sonuc_cmb{ek}.json")


# ---------------------------------------------------------------------------------------------
# KIYAS — CMB (yerel) ↔ C (EDG-026 HAZIR çıktıları; YENİDEN KOŞULMAZ) → sonuc.json
# ---------------------------------------------------------------------------------------------
def kiyas():
    import numpy as np
    CMB = {"sonuc": json.loads((SANDBOX / "sonuc_cmb.json").read_text()),
           "seans": json.loads((SANDBOX / "seanslar_cmb.json").read_text()),
           "islem": json.loads((SANDBOX / "islemler_cmb.json").read_text())}
    C = {"sonuc": json.loads((EDG026 / "sonuc_c.json").read_text()),
         "seans": json.loads((EDG026 / "seanslar_c.json").read_text()),
         "islem": json.loads((EDG026 / "islemler_c.json").read_text())}

    sm, sc = CMB["sonuc"], C["sonuc"]

    # ---- C-taban künyesi: dosya sha256'ları (HAZIR çıktı — yeniden koşulmadı, sha kayıtlı) ---
    c_dosya_sha = {f: _sha(EDG026 / f) for f in
                   ("sonuc_c.json", "seanslar_c.json", "islemler_c.json")}

    # ---- şasi kimliği: motor/config sha'ları C kaydıyla birebir mi? --------------------------
    motor_m, motor_c = sm["motor_sha256_16"], sc["motor_sha256_16"]
    motor_ayni = {f: (motor_m.get(f) == motor_c.get(f) and motor_m.get(f) is not None)
                  for f in ("broker.py", "backtest.py", "strategy.py")}
    config_ayni = {f: (sm["config_sha256_16"][f]["sandbox"] == sc["config_sha256_16"][f]["sandbox"]
                       and sm["config_sha256_16"][f]["sandbox"] is not None)
                   for f in ("goal.yaml", "strategy.yaml", "bounds.yaml")}
    serh = None
    if not all(motor_ayni.values()) or not all(config_ayni.values()):
        serh = ("MOTOR/CONFIG SHA'LARI C İLE BİREBİR DEĞİL — kıyas ŞERHLİDİR (kart universe "
                f"koşulu): motor={motor_ayni} config={config_ayni}")

    # rampa + pencere + enjeksiyon kimliği (C-şasi AYNEN koşulu)
    rampa_ayni = (sm["rampa"]["tam_dd"] == sc["rampa"]["tam_dd"] == 0.15
                  and sm["rampa"]["sifir_dd"] == sc["rampa"]["sifir_dd"] == 0.36)
    pencere_ayni = (sm["replay"]["start"] == sc["replay"]["start"]
                    and sm["replay"]["end"] == sc["replay"]["end"]
                    and sm["replay"]["strategy_version"] == sc["replay"]["strategy_version"])
    enjeksiyon_ayni = (sm["param_enjeksiyon"]["max_open_positions"]["sonra"] ==
                       sc["param_enjeksiyon"]["max_open_positions"]["sonra"] == 20
                       and sm["param_enjeksiyon"]["position_size_r"]["sonra"] ==
                       sc["param_enjeksiyon"]["position_size_r"]["sonra"] == 0.5)

    # takvim kimliği
    tarih_m = [s["date"] for s in CMB["seans"]]
    tarih_c = [s["date"] for s in C["seans"]]
    takvim_ayni = (tarih_m == tarih_c)
    aylar = sorted({d[:7] for d in tarih_c})
    M = len(aylar)

    # ---- eşlenik ay-kümeli bootstrap: işlem n + P&L + havuzlanmış ort-R (CMB − C) ------------
    def ay_seri(islemler):
        cnt = {a: 0 for a in aylar}
        pnl = {a: 0.0 for a in aylar}
        rsum = {a: 0.0 for a in aylar}
        rn = {a: 0 for a in aylar}
        disi = 0
        for t in islemler:
            a = str(t["ts_open"])[:7]
            if a not in cnt:
                disi += 1                       # takvim dışı ay — sayılır, sessiz düşmez (YASA-4)
                continue
            cnt[a] += 1
            pnl[a] += float(t.get("pnl_dollars") or 0.0)
            if t.get("r_multiple") is not None:
                rsum[a] += float(t["r_multiple"])
                rn[a] += 1
        arr = lambda d: np.array([d[a] for a in aylar], dtype=float)
        return {"cnt": arr(cnt), "pnl": arr(pnl), "rsum": arr(rsum), "rn": arr(rn),
                "takvim_disi_islem": disi}

    A_c, A_m = ay_seri(C["islem"]), ay_seri(CMB["islem"])

    rng = np.random.default_rng(BOOT_SEED)
    f_cnt = np.empty(BOOT_ITER)
    f_pnl = np.empty(BOOT_ITER)
    f_avgr = []
    oran = []
    avgr_atlanan = 0
    idx_all = np.arange(M)
    for i in range(BOOT_ITER):
        pick = rng.choice(idx_all, size=M, replace=True)     # EŞLENİK: aynı çekiliş iki koşuma
        cC, cM = float(A_c["cnt"][pick].sum()), float(A_m["cnt"][pick].sum())
        f_cnt[i] = cM - cC
        f_pnl[i] = float(A_m["pnl"][pick].sum()) - float(A_c["pnl"][pick].sum())
        if cC > 0:
            oran.append(cM / cC)
        rnC, rnM = float(A_c["rn"][pick].sum()), float(A_m["rn"][pick].sum())
        if rnC > 0 and rnM > 0:
            f_avgr.append(float(A_m["rsum"][pick].sum()) / rnM
                          - float(A_c["rsum"][pick].sum()) / rnC)
        else:
            avgr_atlanan += 1

    def ci95(arr, nd=3):
        a = np.asarray([x for x in arr if x == x])
        if not len(a):
            return None                                       # ölçülemedi
        return {"lo": round(float(np.percentile(a, 2.5)), nd),
                "hi": round(float(np.percentile(a, 97.5)), nd),
                "orta": round(float(np.median(a)), nd)}

    fark_cnt_ci = ci95(f_cnt)
    fark_pnl_ci = ci95(f_pnl, nd=1)
    fark_avgr_ci = ci95(f_avgr, nd=4)
    oran_ci = ci95(oran)
    nC, nM = int(A_c["cnt"].sum()), int(A_m["cnt"].sum())

    perf_m, perf_c = sm["performans"], sc["performans"]

    # ---- mb-karnesi (AYRI; kill#2 damgası) ---------------------------------------------------
    mb_ts = [t for t in CMB["islem"] if t.get("setup") == "momentum_burst"]
    n_mb = len(mb_ts)
    mb_r = [float(t["r_multiple"]) for t in mb_ts if t.get("r_multiple") is not None]

    def _kume_ci(ts, anahtar_fn, deger_fn, mode="mean", nd=4):
        """Küme-bootstrap %95 CI (mean: havuzlanmış ortalama; sum: küme toplamı).
        Kümeler yerine-koymalı çekilir; 5000 iter, seed 20260812. Boş → None + neden."""
        kume: dict[str, list[float]] = {}
        for t in ts:
            try:
                kume.setdefault(anahtar_fn(t), []).append(deger_fn(t))
            except (TypeError, ValueError):
                continue                        # değer yok — mb_r süzgeciyle zaten dışarıda
        adlar = list(kume.keys())
        if not adlar:
            return {"lo": None, "hi": None, "orta": None, "neden": "küme yok (n=0)"}
        arrs = [np.asarray(kume[a], dtype=float) for a in adlar]
        k = len(adlar)
        rng2 = np.random.default_rng(BOOT_SEED)
        vals = np.empty(BOOT_ITER)
        for i in range(BOOT_ITER):
            pick = rng2.choice(k, size=k, replace=True)
            pooled = np.concatenate([arrs[j] for j in pick])
            vals[i] = pooled.mean() if mode == "mean" else pooled.sum()
        return {"lo": round(float(np.percentile(vals, 2.5)), nd),
                "hi": round(float(np.percentile(vals, 97.5)), nd),
                "orta": round(float(np.median(vals)), nd), "n_kume": k}

    mb_r_ts = [t for t in mb_ts if t.get("r_multiple") is not None]
    ci_mb_ay = _kume_ci(mb_r_ts, lambda t: str(t["ts_open"])[:7], lambda t: float(t["r_multiple"]))
    ci_mb_cikis = _kume_ci(mb_r_ts, lambda t: str(t["ts_close"])[:10],
                           lambda t: float(t["r_multiple"]))
    ci_mb_pnl = _kume_ci([t for t in mb_ts if t.get("pnl_dollars") is not None],
                         lambda t: str(t["ts_open"])[:7], lambda t: float(t["pnl_dollars"]),
                         mode="sum", nd=1)
    mb_exit: dict[str, int] = {}
    mb_yil: dict[str, list[float]] = {}
    for t in mb_ts:
        mb_exit[str(t.get("exit_reason"))] = mb_exit.get(str(t.get("exit_reason")), 0) + 1
        if t.get("r_multiple") is not None:
            mb_yil.setdefault(str(t["ts_open"])[:4], []).append(float(t["r_multiple"]))
    kill_mb = n_mb < KILL_MB_N
    mb_karne = {
        "n": n_mb,
        "kill2_esik20": (f"olculemedi — mb işlem {n_mb} < {KILL_MB_N} (kart kill#2); "
                         "paket-kapısı yine üç ölçütle işler") if kill_mb else "esik_ustu",
        "avg_r": round(sum(mb_r) / len(mb_r), 4) if mb_r else None,
        "win_rate": round(sum(1 for x in mb_r if x > 0) / len(mb_r), 4) if mb_r else None,
        "toplam_pnl": round(sum(float(t.get("pnl_dollars") or 0.0) for t in mb_ts), 2),
        "ci95_avg_r_ay_kumeli": ci_mb_ay,                 # birincil (şasi ay tanımı ts_open[:7])
        "ci95_avg_r_cikis_gunu_kumeli": ci_mb_cikis,      # duyarlılık (025 bacak-b deseni)
        "ci95_toplam_pnl_ay_kumeli": ci_mb_pnl,
        "exit_reason_dagilim": dict(sorted(mb_exit.items(), key=lambda kv: -kv[1])),
        "yil_bazinda": {y: {"n": len(v), "avg_r": round(sum(v) / len(v), 4)}
                        for y, v in sorted(mb_yil.items())},
        "plan_gorunumu": sm.get("mb_kanal", {}).get("mb_plan_verdict"),
    }

    # ---- slot-çalma: CMB'nin mb-DIŞI işlemleri ↔ C'nin TÜM işlemleri (025 deseni) ------------
    diger_ts = [t for t in CMB["islem"] if t.get("setup") != "momentum_burst"]
    A_dg = ay_seri(diger_ts)
    rng3 = np.random.default_rng(BOOT_SEED)
    f_dg_cnt = np.empty(BOOT_ITER)
    f_dg_pnl = np.empty(BOOT_ITER)
    for i in range(BOOT_ITER):
        pick = rng3.choice(idx_all, size=M, replace=True)
        f_dg_cnt[i] = float(A_dg["cnt"][pick].sum()) - float(A_c["cnt"][pick].sum())
        f_dg_pnl[i] = float(A_dg["pnl"][pick].sum()) - float(A_c["pnl"][pick].sum())
    pnl_of = lambda ts: round(sum(float(t.get("pnl_dollars") or 0.0) for t in ts), 2)
    slot_calma = {
        "tanim": ("CMB'nin mb-DIŞI işlemleri ↔ C'nin TÜM işlemleri (C'de mb dormant'tı — C'nin "
                  "tamamı 'diğer kurulumlar'dır); eşlenik ay-kümeli bootstrap (ts_open[:7])"),
        "n_diger_C": nC, "n_diger_CMB": len(diger_ts),
        "delta_n_diger": len(diger_ts) - nC,
        "ci95_delta_n_diger": ci95(f_dg_cnt),
        "pnl_diger_C": pnl_of(C["islem"]), "pnl_diger_CMB": pnl_of(diger_ts),
        "delta_pnl_diger": round(pnl_of(diger_ts) - pnl_of(C["islem"]), 2),
        "ci95_delta_pnl_diger": ci95(f_dg_pnl, nd=1),
        "setup_bazinda_C": _setup_ozet(C["islem"]),
        "setup_bazinda_CMB": _setup_ozet(CMB["islem"]),
    }

    # ---- ÜÇ KAPI-ÖLÇÜTÜ (kart success_metric, DONUK) — İŞARET, hüküm DEĞİL -------------------
    ddc = perf_c.get("maxdd_kanonik")
    ddm = perf_m.get("maxdd_kanonik")
    dd_esik = round(ddc * KAPI_DD_KATSAYI, 5) if ddc is not None else None
    kapi_i = {
        "olcut": "net P&L farkı (CMB−C) eşlenik ay-kümeli %95 CI ÜST ucu ≥ 0",
        "fark_nokta_equity": (round(perf_m["net_pnl_equity"] - perf_c["net_pnl_equity"], 2)
                              if perf_m.get("net_pnl_equity") is not None
                              and perf_c.get("net_pnl_equity") is not None else None),
        "fark_nokta_islem_toplami": (round(perf_m["net_pnl_trades"] - perf_c["net_pnl_trades"], 2)
                                     if perf_m.get("net_pnl_trades") is not None
                                     and perf_c.get("net_pnl_trades") is not None else None),
        "fark_ci95": fark_pnl_ci,
        "isaret": ("gecti" if (fark_pnl_ci is not None and fark_pnl_ci["hi"] >= 0) else
                   ("olculemedi" if fark_pnl_ci is None else "dustu")),
    }
    kapi_ii = {
        "olcut": f"maxdd_kanonik_CMB ≤ maxdd_kanonik_C × {KAPI_DD_KATSAYI}",
        "maxdd_C": ddc, "maxdd_CMB": ddm,
        "esik": dd_esik, "esik_kart_yuvarlak": 0.1606,
        "oran": round(ddm / ddc, 3) if (ddc not in (None, 0) and ddm is not None) else None,
        "isaret": (("gecti" if ddm <= ddc * KAPI_DD_KATSAYI else "dustu")
                   if (ddc is not None and ddm is not None) else "olculemedi"),
    }
    kapi_iii = {
        "olcut": f"sharpe_CMB ≥ {KAPI_SHARPE_MIN}",
        "sharpe_C": perf_c.get("sharpe"), "sharpe_CMB": perf_m.get("sharpe"),
        "sharpe_measurable_CMB": perf_m.get("sharpe_measurable"),
        "isaret": (("gecti" if perf_m["sharpe"] >= KAPI_SHARPE_MIN else "dustu")
                   if perf_m.get("sharpe") is not None else "olculemedi"),
    }

    # ---- kill bayrakları (kart, DONUK — koşul kaydı, hüküm DEĞİL) ----------------------------
    kill_sasi = {
        "esik": ("şasi bütünlüğü: koşum-içi bütünlük (her iki koşum) + motor/config sha C ile "
                 "birebir + rampa/pencere/enjeksiyon aynı + takvim aynı; bozuksa ölçüm GEÇERSİZ "
                 "(kart kill#1)"),
        "CMB_butunluk": sm["butunluk"]["gecerli"], "C_butunluk": sc["butunluk"]["gecerli"],
        "motor_sha_ayni": motor_ayni, "config_sha_ayni": config_ayni,
        "rampa_ayni_15_36": rampa_ayni, "pencere_ayni": pencere_ayni,
        "enjeksiyon_c_sasi_ayni": enjeksiyon_ayni, "takvim_ayni": takvim_ayni,
        "tetiklendi": not (sm["butunluk"]["gecerli"] and sc["butunluk"]["gecerli"]
                           and all(motor_ayni.values()) and all(config_ayni.values())
                           and rampa_ayni and pencere_ayni and enjeksiyon_ayni and takvim_ayni),
    }
    kill_mb_n = {
        "esik": f"mb işlem sayısı < {KILL_MB_N} → mb-karnesi 'olculemedi' (kart kill#2); "
                "paket-kapısı yine üç ölçütle işler",
        "n_mb": n_mb, "tetiklendi": kill_mb,
    }

    def satir(*yol):
        def cek(s):
            v = s
            for k in yol:
                v = v.get(k) if isinstance(v, dict) else None
                if v is None:
                    return None
            return v
        return {"C_slot20_r05": cek(sc), "CMB_slot20_r05_mb": cek(sm)}

    tablo = {
        "islem_n": {"C_slot20_r05": nC, "CMB_slot20_r05_mb": nM, "fark": nM - nC,
                    "fark_pct": round(100.0 * (nM - nC) / nC, 1) if nC else None},
        "islem_yil": satir("islem", "islem_yil"),
        "islem_fark_ci95_ay_kumeli_eslenik": fark_cnt_ci,
        "islem_oran_ci95": oran_ci,
        "net_pnl_equity": satir("performans", "net_pnl_equity"),
        "net_pnl_trades": satir("performans", "net_pnl_trades"),
        "net_pnl_fark_ci95_ay_kumeli_eslenik": fark_pnl_ci,
        "maxdd_kanonik": satir("performans", "maxdd_kanonik"),
        "maxdd_m2m": satir("performans", "maxdd_m2m"),
        "avg_r": satir("performans", "avg_r"),
        "avg_r_fark_ci95_ay_kumeli_eslenik": fark_avgr_ci,
        "avg_r_fark_atlanan_iter": avgr_atlanan,
        "win_rate": satir("performans", "win_rate"),
        "sharpe": satir("performans", "sharpe"),
        "score": satir("performans", "score"),
        "total_return": satir("performans", "total_return"),
        "silahlanan_plan": satir("islem", "silahlanan_plan"),
        "toplam_plan": satir("islem", "toplam_plan"),
        "verdict_dagilim": satir("islem", "verdict_dagilim"),
        "nogo_neden_dagilim": satir("islem", "nogo_neden_dagilim"),
        "review_neden_dagilim": satir("islem", "review_neden_dagilim"),
        "entry_rejects": satir("islem", "entry_rejects"),
        "exit_reason_dagilim": satir("islem", "exit_reason_dagilim"),
        "setup_bazinda": {"C_slot20_r05": slot_calma["setup_bazinda_C"],
                          "CMB_slot20_r05_mb": slot_calma["setup_bazinda_CMB"]},
        "doluluk_pozisyon_gun": satir("doluluk", "pozisyon_gun_open_fazi"),
        "ort_acik_pozisyon": satir("doluluk", "ort_acik_pozisyon"),
        "doluluk_orani_slot": satir("doluluk", "doluluk_orani_slot"),
        "toplam_bars_held": satir("doluluk", "toplam_bars_held"),
        "tepe_isi_nominal_open_fazi_max": {
            "C_slot20_r05": (sc["tepe_isi"]["nominal_open_fazi_R"] or {}).get("max"),
            "CMB_slot20_r05_mb": (sm["tepe_isi"]["nominal_open_fazi_R"] or {}).get("max")},
        "tepe_isi_gerceklesen_size_r_max": {
            "C_slot20_r05": ((sc["tepe_isi"]["gerceklesen_open_fazi"]["size_r_toplam"] or {}).get("max")),
            "CMB_slot20_r05_mb": ((sm["tepe_isi"]["gerceklesen_open_fazi"]["size_r_toplam"] or {}).get("max"))},
        "eszamanli_poz_max": {"C_slot20_r05": sc["tepe_isi"]["eszamanli_poz_max"],
                              "CMB_slot20_r05_mb": sm["tepe_isi"]["eszamanli_poz_max"]},
        "tasnif_birincil": satir("birincil", "dagilim"),
        "tasnif_tum_seans": satir("tasnif_tum_seans", "dagilim"),
        "takvim_disi_islem": {"C_slot20_r05": A_c["takvim_disi_islem"],
                              "CMB_slot20_r05_mb": A_m["takvim_disi_islem"]},
    }

    out = {
        "kart": "EDG-2026-032",
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "olcum_ajani_beyani": (
            "SALT-ÖLÇÜM: karta/ARMED_SETUPS'a/strategy.py'ye/gerçek state'e DOKUNULMADI; "
            "git/canlı/ssh/serve.sh YOK. mb-silahlama motorun kendi kanalıyla "
            "(entry.armed_extra param — arming.py:317 emsali); kanal öz-sınamayla kanıtlı "
            "(sonuc_cmb.mb_kanal.oz_sinama). C tabanı EDG-026'nın HAZIR çıktısı — yeniden "
            "koşulmadı, dosya sha'ları künyede. loop/counterfactual/cf_backfill/hermes ithal "
            "edilmedi (sys.modules kanıtı koşum kaydında). HÜKÜM YAZILMADI — Rol-1 işler."),
        "kiyas_taban": {"kaynak": "EDG-026 koşum C HAZIR çıktıları — yeniden koşulmadı",
                        "dosyalar": [str(EDG026 / "sonuc_c.json"),
                                     str(EDG026 / "seanslar_c.json"),
                                     str(EDG026 / "islemler_c.json")],
                        "dosya_sha256_16": c_dosya_sha},
        "sasi_kimligi": {"motor_sha_ayni": motor_ayni, "config_sha_ayni": config_ayni,
                         "rampa_ayni_15_36": rampa_ayni, "pencere_ayni": pencere_ayni,
                         "enjeksiyon_c_sasi_ayni": enjeksiyon_ayni,
                         "takvim_ayni": takvim_ayni, "serh": serh},
        "yontem": {
            "eslenik_bootstrap": ("ay-kümeli EŞLENİK bootstrap: takvim aylarından aynı çekiliş "
                                  f"iki koşuma birden; fark = CMB − C; iter={BOOT_ITER}, "
                                  f"seed={BOOT_SEED}, n_ay={M}"),
            "islem_ay_anahtari": "ts_open[:7] (giriş ayı — şasi tanımı AYNEN)",
            "oran_atlanan_iter": BOOT_ITER - len(oran),
            "avg_r_atlanan_iter": avgr_atlanan,
            "mb_ci": ("birincil ay-kümeli (ts_open[:7], şasi tanımı); duyarlılık çıkış-günü-kümeli "
                      "(ts_close[:10], 025 bacak-b deseni); P&L CI ay-kümeli toplam"),
        },
        "param_enjeksiyon": sm["param_enjeksiyon"],
        "mb_kanal": sm["mb_kanal"],
        "butunluk": {"CMB": sm["butunluk"], "C": sc["butunluk"]},
        "kapi_olcutleri_kart_donuk": {
            "i_pnl_fark_ci_ust_ge0": kapi_i,
            "ii_maxdd_le_c_1p3x": kapi_ii,
            "iii_sharpe_ge_0p20": kapi_iii,
            "not": ("MEKANİK işaretler — kart success_metric'in düz okuması; paket/dağıtım "
                    "HÜKMÜ Rol-1'in"),
        },
        "kill_bayraklari": {"kill_sasi_gecersizlik": kill_sasi, "kill_mb_n20": kill_mb_n},
        "mb_karnesi": mb_karne,
        "slot_calma": slot_calma,
        "tablo": tablo,
        "dosyalar": {"CMB": {"sonuc": "sonuc_cmb.json", "seanslar": "seanslar_cmb.json",
                             "islemler": "islemler_cmb.json"},
                     "C": "EDG-026 dizini (kiyas_taban.dosyalar)"},
    }
    (SANDBOX / "sonuc.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))

    print("\n==================== EDG-032 C↔CMB ÖZET ====================")
    print(f"şasi: motor_ayni={all(motor_ayni.values())} config_ayni={all(config_ayni.values())} "
          f"rampa_ayni={rampa_ayni} pencere_ayni={pencere_ayni} takvim_ayni={takvim_ayni} "
          f"şerh={serh}")
    print(f"işlem: C {nC} → CMB {nM}  fark={nM-nC}  CI95={fark_cnt_ci}  oran CI={oran_ci}")
    print(f"net_pnl: {tablo['net_pnl_equity']}  fark CI95={fark_pnl_ci}")
    print(f"maxdd kanonik: C {ddc} → CMB {ddm}  eşik(×{KAPI_DD_KATSAYI})={dd_esik}")
    print(f"sharpe: C {perf_c.get('sharpe')} → CMB {perf_m.get('sharpe')}  "
          f"avg_r: C {perf_c.get('avg_r')} → CMB {perf_m.get('avg_r')}  fark CI={fark_avgr_ci}")
    print(f"KAPI (i) P&L-CI-üst≥0: {kapi_i['isaret']}   (ii) dd≤C×1.3: {kapi_ii['isaret']}   "
          f"(iii) sharpe≥0.20: {kapi_iii['isaret']}")
    print(f"KILL şasi tetiklendi={kill_sasi['tetiklendi']}  KILL mb-n20 tetiklendi="
          f"{kill_mb_n['tetiklendi']} (n_mb={n_mb})")
    print(f"mb-karne: n={n_mb} avg_r={mb_karne['avg_r']} pnl={mb_karne['toplam_pnl']} "
          f"CI(ay)={ci_mb_ay}")
    print(f"slot-çalma: Δn_diğer={slot_calma['delta_n_diger']} (CI={slot_calma['ci95_delta_n_diger']})  "
          f"Δpnl_diğer={slot_calma['delta_pnl_diger']} (CI={slot_calma['ci95_delta_pnl_diger']})")
    print(f"yazıldı: {SANDBOX/'sonuc.json'}")
    print("============================================================\n")


if __name__ == "__main__":
    mod = sys.argv[1] if len(sys.argv) > 1 else ""
    smoke = "--smoke" in sys.argv
    if mod == "cmb":
        kosum(smoke=smoke)
    elif mod == "kiyas":
        kiyas()
    else:
        sys.exit("kullanım: olcum.py {cmb|kiyas} [--smoke]")

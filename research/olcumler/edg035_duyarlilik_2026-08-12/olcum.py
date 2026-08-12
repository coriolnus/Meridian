"""EDG-2026-035 — YEREL DUYARLILIK TARAMASI (OFAT, merkez C+mb) · ölçüm aracı (2026-08-12)

Kart: research/cards/EDG-2026-035-yerel-duyarlilik.yaml (OKU-DOKUNMA; hüküm Rol-1'in).
Rol: ÖLÇÜM ajanı. Bu modül HÜKÜM VERMEZ, karta dokunmaz, git/canlı/broker/state'e YAZMAZ,
repo koduna DOKUNMAZ.

ŞASİ: EDG-026/032 (research/olcumler/edg032_final_paket_2026-08-12/olcum.py) devralındı —
izole sandbox (EDG-022 DONMUŞ config kopyaları + salt-okunur bars symlink), kayıt kancaları,
bütünlük kontrolleri, eşlenik ay-kümeli bootstrap (5000, seed 20260812). İKİ FARK (kod-turu
v237 dağıtımı sonrası — kartın universe beyanı):
  1. RAMPA MONKEYPATCH YOK: broker.derisk_mult artık derisk_ramp() üzerinden goal.yaml okur;
     sandbox goal'ünde (EDG-022 donuk kopya) derisk anahtarı YOK → fail-safe 0.15/0.36 devrede
     = C+mb rampası. Kanıt: kaynak alanı "kod varsayilani" + 023/026 değer çivileri assert'li.
  2. MB armed_extra KANALI YOK: strategy.ARMED_SETUPS artık ("breakout_vcp","pullback",
     "exhaustion_hammer","momentum_burst") — mb SONDA (032'nin `ARMED_SETUPS + extra`
     önceliğiyle birebir aynı sıra; strategy.py blok beyanı). Kanıt: tuple assert + sıra assert.

ŞASİ-KONTROLÜ (kill#1, kart): `kontrol` hücresi (yeni-motor default + goal-enjeksiyon
max_open=20 & position_size_r=0.5, zarf DOKUNULMAZ) TAM replay çıktıları EDG-032 cmb ile
BİT-ÖZDEŞ olmalı: islemler/seanslar dosyaları sha256 bayt-özdeş + sonuc ölçüm blokları derin-eşit.
(sonuc_cmb.json'ın kendisi bayt-özdeş OLAMAZ: olcum_zamani/sure_sn/motor-sha alanları koşum
kimliğidir; bit-özdeşlik iddiası DETERMİNİSTİK replay içeriği üzerinden kanıtlanır — islemler +
seanslar baytları ve sonuc'un ölçüm blokları.) Düşerse ölçüm DURUR (dağıtım-regresyon kanıtı).
Geçerse kontrol koşumu = TABAN.

ALTI OFAT HÜCRESİ (kart parameter_grid, DONUK; her hücrede TEK eksen merkezden sapar):
  slot15  : goal limits.max_open_positions 20→15
  slot25  : goal limits.max_open_positions 20→25
  size040 : strateji params position_size_r 0.5→0.40   (026 enjeksiyon deseni)
  size065 : strateji params position_size_r 0.5→0.65
  zarf65  : goal limits.heat_hard_r 5.0→6.5            (028 T10 emsali; kanonik yüzey
  zarf80  : goal limits.heat_hard_r 5.0→8.0             guard.classify_gate → limits.get(...)
                                                        guard.py:326; öz-sınama sentetik planla)

TANIMLAR (ölçümden ÖNCE donuk; 032 şasi tanımları AYNEN):
  islem            = kapanmış işlem satırı (broker.closed; eod/delisted markout DAHİL).
  ay kümesi        = ts_open[:7] (giriş ayı).
  eşlenik bootstrap= takvim ayları üzerinden AYNI çekiliş iki koşuma birden (yerine-koymalı,
                     5000 iter, seed 20260812); fark = HÜCRE − TABAN. Seriler: işlem sayısı,
                     işlem-P&L ay toplamı, havuzlanmış ort-R (ΣR/Σn; payda-0 iter atlanır+sayılır).
  max-dd           = motor-kanonik score.score_detail.max_drawdown (kapı b BUNUN üstünden).
  net P&L          = M2M equity son değer − START_EQUITY; çapraz: Σ pnl_dollars.

KAPI-ÖLÇÜTLERİ (kart success_metric, DONUK — hücre başına MEKANİK işaret, hüküm YOK):
  (a) ΔP&L(hücre−taban) eşlenik ay-kümeli %95 CI ALT ucu > 0   [CI-üstünlük]
  (b) maxdd_kanonik_hücre ≤ maxdd_kanonik_taban × 1.3          (0.1268×1.3=0.16484; kart 0.1648)
  (c) sharpe_hücre ≥ 0.20
  NOKTA-P&L SIRALAMASI HÜKÜM GİRDİSİ DEĞİLDİR (kart serap-koruması; 024 dersi) — sıralama üretilmez.

KILL KONTROLLERİ (kart, DONUK):
  kill#1 şasi-kontrolü: kontrol ≠ 032-cmb bit-özdeş → ölçüm DURUR (kontrol_kiyas çıkış kodu ≠0).
  kill#2 bütünlük: frame_miss/dup/scan!=plan/yasak-modül/base_max bozuk → hücre GEÇERSİZ.
  kill#3 mtime: motor dosyalarında koşum sırasında sha/mtime değişimi → o hücre GEÇERSİZ (033 dersi).

EK ÇIKTI (karar değil bilgi): üç eksenin yerel eğim haritası (birim beyanlı sonlu farklar).

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen None + neden); YASA-4 (sessiz-yutma işaretli + gerekçe);
YASA-6 (okuyucu: sonuc_<hücre>.json + islemler/seanslar → `kiyas` tüketir; kontrol_kiyas.json +
sonuc.json → dönüş raporu + Rol-1). SALT-OKUMA: config.STATE koşum-başına izole sandbox; barlar
symlink ile salt-okunur; canlı state'e ve motor dosyalarına tek bayt yazılmaz. meridian.loop /
counterfactual / cf_backfill / hermes İTHAL EDİLMEZ — sys.modules ile kanıtlanır.

KULLANIM:
  olcum.py kontrol|slot15|slot25|size040|size065|zarf65|zarf80   [--smoke]
  olcum.py kontrol_kiyas [--smoke]     # kill#1 şasi-kontrolü (bit-özdeşlik); düşerse exit 2
  olcum.py kiyas                       # 6 hücre ↔ taban + kapılar + eğim haritası → sonuc.json
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
EDG032 = REPO / "research/olcumler/edg032_final_paket_2026-08-12"

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

REPLAY_START = "2022-01-01"
REPLAY_END = "2026-07-30"                      # 032/026 penceresi AYNEN
BOOT_SEED = 20260812
BOOT_ITER = 5000

# merkez (C+mb) — kart universe; her hücre TEK eksen saptırır
MERKEZ = {"slot": 20, "size": 0.5, "zarf": None}     # zarf None = DOKUNULMAZ (5.0 assert'lenir)
HUCRELER = {
    "kontrol": {},                                   # şasi-kontrolü + TABAN
    "slot15": {"slot": 15},
    "slot25": {"slot": 25},
    "size040": {"size": 0.40},
    "size065": {"size": 0.65},
    "zarf65": {"zarf": 6.5},
    "zarf80": {"zarf": 8.0},
}
OFAT_SIRA = ["slot15", "slot25", "size040", "size065", "zarf65", "zarf80"]

ZARF_MERKEZ = 5.0                              # frozen goal beklenen zarf (assert)
RAMPA_BEKLENEN = {"full_dd": 0.15, "floor_dd": 0.36}   # kablolu fail-safe = C+mb rampası
ARMED_BEKLENEN = ("breakout_vcp", "pullback", "exhaustion_hammer", "momentum_burst")

KAPI_DD_KATSAYI = 1.3
KAPI_SHARPE_MIN = 0.20

KART3 = ["tavan_sifir", "evren_bagladi", "derisk_bagladi"]
YASAK = ("meridian.loop", "meridian.counterfactual", "meridian.cf_backfill", "meridian.hermes")
MOTOR_DOSYALAR = ("broker.py", "backtest.py", "strategy.py", "guard.py",
                  "config.py", "dataset.py", "score.py", "regime.py")

# NO_GO/REVIEW neden eşlemesi (şasi AYNEN)
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
        return None    # ölçülemedi (dosya yok/okunamadı)


def _sha_full(p: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None


def _motor_kunye() -> dict:
    """kill#3 parmak izi: motor dosyaları sha256 + mtime_ns (033 dersi)."""
    out = {}
    for f in MOTOR_DOSYALAR:
        p = REPO / "meridian" / f
        try:
            st = p.stat()
            out[f] = {"sha256_16": _sha(p), "mtime_ns": st.st_mtime_ns}
        except OSError:
            out[f] = {"sha256_16": None, "mtime_ns": None}   # ölçülemedi
    return out


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


# ---------------------------------------------------------------------------------------------
# SANDBOX HAZIRLIĞI — izole state (EDG-022 DONMUŞ kopyaları; 026/032 şasisi AYNEN)
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
            # kaynak = EDG-022 DONMUŞ kopyaları (026/032/C ile aynı kaynak — tutarlılık çivisi).
            # DOSYALAR DEĞİŞTİRİLMEZ: enjeksiyonlar YÜKLENMİŞ sözlüklere yapılır ki config
            # sha'ları 032 kaydıyla bayt-aynı kalsın (şasi kimliği sha ile kanıtlanır).
            shutil.copyfile(EDG022 / "state" / f, dst)
    return st


# ---------------------------------------------------------------------------------------------
# SINIFLAMA + BOOTSTRAP + ISI — şasi fonksiyonları AYNEN (032)
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


def _setup_ozet(ts: list[dict]) -> dict:
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
# TEK HÜCRE KOŞUMU (kontrol + 6 OFAT hücresi — tek şasi, hücre-parametreli)
# ---------------------------------------------------------------------------------------------
def kosum(run: str, smoke: bool = False):
    hucre = dict(MERKEZ)
    hucre.update(HUCRELER[run])
    SLOT, BOYUT_R, ZARF = int(hucre["slot"]), float(hucre["size"]), hucre["zarf"]

    outdir = (SANDBOX / "smoke") if smoke else SANDBOX
    outdir.mkdir(exist_ok=True)
    r_start, r_end = (REPLAY_START, "2022-06-30") if smoke else (REPLAY_START, REPLAY_END)

    st_dir = hazirla(run + ("_smoke" if smoke else ""))
    sys.path.insert(0, str(REPO))

    # kill#3 parmak izi — replay ÖNCESİ (koşum sonunda yeniden alınıp karşılaştırılır)
    motor_once = _motor_kunye()

    # ŞASİ KİMLİK ÇİVİSİ: sandbox config sha'ları 032-cmb kaydıyla bayt-aynı olmalı
    cmb_kayit = json.loads((EDG032 / "sonuc_cmb.json").read_text())
    for f in ("goal.yaml", "strategy.yaml", "bounds.yaml"):
        beklenen = cmb_kayit["config_sha256_16"][f]["sandbox"]
        gercek = _sha(st_dir / f)
        assert gercek == beklenen, \
            f"ŞASİ KİMLİĞİ BOZUK: sandbox {f} sha {gercek} ≠ 032 kaydı {beklenen}"

    from meridian import config
    # SALT-OKUMA İZOLASYONU: her yazım sandbox'a düşer, canlı state'e DEĞİL
    config.STATE = st_dir
    config.BARS = st_dir / "bars"
    config.HISTORY = st_dir / "history"
    config.reload_config()      # lru_cache boşalt: goal() bundan sonra SANDBOX dosyasını okur
    #                             (derisk_ramp/entry_law config.goal() okuyucusudur — izolasyon şartı)

    import numpy as np                     # noqa: F401
    import yaml
    from meridian import backtest, dataset, guard, score as score_mod

    assert not hasattr(backtest, "wpg_overlay_day"), "motor YAMALI görünüyor — ölçüm geçersiz"
    assert not [m for m in sys.modules if m in YASAK], "yasaklı modül ithal edilmiş"

    brk = backtest.brk
    strat = backtest.strat
    ORIJ_DERISK = brk.derisk_mult          # kablolu-rampa kanıtı: koşum boyunca YAMASIZ kalmalı

    # ---- RAMPA KABLOLU KANITI (kart universe: monkeypatch YOK — motor goal-okuyucu) ----------
    rampa_cfg = brk.derisk_ramp()
    assert rampa_cfg["full_dd"] == RAMPA_BEKLENEN["full_dd"] \
        and rampa_cfg["floor_dd"] == RAMPA_BEKLENEN["floor_dd"], \
        f"rampa bandı beklenen 15/36 değil: {rampa_cfg}"
    # sandbox goal'ünde derisk anahtarı YOK → kaynak 'kod varsayilani' (fail-safe = C+mb bandı)
    _sand_goal = yaml.safe_load((st_dir / "goal.yaml").read_text())
    assert "derisk_full_dd" not in (_sand_goal.get("limits") or {}) \
        and "derisk_floor_dd" not in (_sand_goal.get("limits") or {}), \
        "sandbox goal derisk anahtarı içeriyor — şasi beklentisi bozuk"
    # 023/026 değer çivileri — bu kez YAMASIZ motor fonksiyonunun kendisi üstünde
    assert brk.derisk_mult(90.0, 100.0) == 1.0
    assert abs(brk.derisk_mult(80.0, 100.0) - 0.7619) < 1e-9
    assert brk.derisk_mult(64.0, 100.0) == 0.0
    assert brk.max_positions_at(80.0, 100.0, 5) == 4       # 023 çivisi
    assert brk.max_positions_at(80.0, 100.0, 20) == 15     # slot-20 tabanı (026 çivisi)
    assert brk.max_positions_at(80.0, 100.0, SLOT) == max(1, int(round(SLOT * 0.7619)))
    rampa_kanit = {
        "monkeypatch": False,
        "kaynak": rampa_cfg["kaynak"],     # beklenen: iki alan da 'kod varsayilani' (fail-safe)
        "band": {"full_dd": rampa_cfg["full_dd"], "floor_dd": rampa_cfg["floor_dd"]},
        "beyan": ("broker.derisk_ramp() goal-okuyucu (broker.py:227); sandbox goal'ünde "
                  "derisk anahtarı yok → fail-safe 0.15/0.36 = C+mb bandı. derisk_mult "
                  "YAMASIZ; 023/026 değer çivileri koşum başında assert'lendi"),
    }

    # ---- girdiler + HÜCRE ENJEKSİYONLARI (dosya DEĞİŞMEZ; sözlükler değişir) -----------------
    stg = yaml.safe_load((st_dir / "strategy.yaml").read_text())
    params = dict(stg["params"])
    by_regime = stg.get("params_by_regime") or None
    sv = int(stg.get("version"))
    goal = config.goal()                                   # derin kopya — dosyaya/önbelleğe sızmaz

    onceki = {"max_open_positions": int(goal["limits"]["max_open_positions"]),
              "position_size_r": float(params["position_size_r"]),
              "heat_hard_r": float(goal["limits"]["heat_hard_r"]),
              "entry.armed_extra": params.get("entry.armed_extra")}   # beklenen: None (v3 dosya)
    assert onceki["heat_hard_r"] == ZARF_MERKEZ, \
        f"beklenen zarf merkezi 5.0 değil: {onceki['heat_hard_r']}"
    assert onceki["entry.armed_extra"] is None, \
        "frozen strategy.yaml entry.armed_extra içeriyor — şasi beklentisi bozuk"

    goal["limits"]["max_open_positions"] = SLOT            # ENJEKSİYON 1 (goal/limits)
    params["position_size_r"] = BOYUT_R                    # ENJEKSİYON 2 (strateji params)
    if ZARF is not None:
        goal["limits"]["heat_hard_r"] = float(ZARF)        # ENJEKSİYON 3 (zarf hücreleri; 028 emsali)

    for _rg in ("trend_up", "trend_down", "chop", "high_vol"):
        _eff = config.resolve_params(params, by_regime, _rg)
        assert float(_eff["position_size_r"]) == BOYUT_R, f"rejim override sızıntısı: {_rg}"
        _ovr = (by_regime or {}).get(_rg) or {}
        assert "position_size_r" not in _ovr, f"params_by_regime[{_rg}] position_size_r içeriyor"
        assert "entry.armed_extra" not in _ovr, f"params_by_regime[{_rg}] entry.armed_extra içeriyor"
    assert float(goal["limits"]["max_position_r"]) >= BOYUT_R          # yukarı-kırpma etkilemez
    limits = goal["limits"]
    max_open = int(limits["max_open_positions"])
    no_trade_before = int(limits.get("no_trade_before_bars", 0))
    assert max_open == SLOT

    # ---- MB MOTORDA SİLAHLI KANITI (kanal enjeksiyonu YOK — kart universe) -------------------
    assert tuple(strat.ARMED_SETUPS) == ARMED_BEKLENEN, \
        f"repo ARMED_SETUPS beklenenden farklı: {strat.ARMED_SETUPS}"
    assert strat.ARMED_SETUPS[-1] == "momentum_burst", \
        "mb SONDA değil — 032'nin ölçtüğü öncelik sırası (armed üçlü önce) bozulmuş olur"
    mb_kanit = {
        "armed_setups": list(strat.ARMED_SETUPS),
        "armed_extra_enjeksiyonu": None,
        "beyan": ("mb motorun kendi ARMED_SETUPS'unda ve SONDA (strategy.py:1029) — 032'nin "
                  "`ARMED_SETUPS + extra` (extra sonda) önceliğiyle birebir; kanal gereksiz"),
    }

    # ---- ZARF YÜZEYİ ÖZ-SINAMASI (yalnız zarf hücreleri; 028 T10 emsali AYNEN) ---------------
    zarf_oz_sinama = None
    if ZARF is not None:
        Z = float(ZARF)
        # sentetik plan/portföy: open_heat = open_risk_r + size_r (guard.py:375)
        _tp = {"sector": "tech", "r_multiple_expected": 2.5, "size_r": 0.5, "score": 95}
        _rj = {"exposure_budget_pct": 60, "leading_sectors": []}
        _pf_ara = {"open_positions": 3, "sector_counts": {}, "day_pnl_pct": 0.0,
                   "open_risk_r": Z - 0.8, "max_corr": 0.0}    # heat = Z-0.3: eski zarfın ÜSTÜ, yeninin ALTI
        _pf_ust = {**_pf_ara, "open_risk_r": Z + 0.2}          # heat = Z+0.7: yeni zarfın da ÜSTÜ
        assert (Z - 0.8 + 0.5) > ZARF_MERKEZ, "öz-sınama aralığı eski zarfın üstünde değil — sınama anlamsız"
        _g5 = {"limits": {**limits, "heat_hard_r": ZARF_MERKEZ}}
        _v5, _n5 = guard.classify_gate(_tp, _pf_ara, _rj, _g5)
        assert _v5 == "NO_GO" and any("ısısı sert tavanı" in x for x in _n5), \
            "5R zarf yüzeyi kanıtlanamadı (ara-ısı eski zarfta kesilmedi)"
        _vZ, _nZ = guard.classify_gate(_tp, _pf_ara, _rj, goal)
        assert _vZ != "NO_GO", f"zarf enjeksiyonu ısı kapısına işlemedi (ara-ısı hâlâ kesiliyor): {_nZ}"
        _vZu, _nZu = guard.classify_gate(_tp, _pf_ust, _rj, goal)
        assert _vZu == "NO_GO" and any("ısısı sert tavanı" in x for x in _nZu), \
            f"{Z}R tavanın ÜSTÜ kesilmiyor — enjeksiyon yanlış yüzeyde"
        zarf_oz_sinama = {
            "ara_isi_R": round(Z - 0.3, 2), "ust_isi_R": round(Z + 0.7, 2),
            "eski_zarfta_NO_GO": True, "yeni_zarfta_gecer": True, "yeni_zarf_ustu_NO_GO": True,
            "yuzey": "guard.classify_gate → goal['limits']['heat_hard_r'] (guard.py:326; 028 emsali)",
        }

    # ---- kancalar (032 şasi deseni AYNEN) ----------------------------------------------------
    seans_by_date: dict[str, dict] = {}
    _cur_close_date = [None]
    _dup: list[str] = []
    _frame_miss = [0]

    _orig_maxpos = brk.max_positions_at
    _orig_regime = backtest.regime_mod.build_regime_json
    _orig_scan = backtest.strat.scan_entry

    def _maxpos(equity, peak, base_max):
        n = _orig_maxpos(equity, peak, base_max)              # GERÇEK eff_max_open (kablolu rampa)
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

    # kanca restorasyonu (kanıtlı) — süreç tek koşumluk ama düzen gereği geri takılır
    brk.max_positions_at = _orig_maxpos
    backtest.regime_mod.build_regime_json = _orig_regime
    backtest.strat.scan_entry = _orig_scan

    # koşum sonrası kanıtlar
    yasak_yuklu = [m for m in sys.modules if m in YASAK]
    armed_sonrasi_ayni = tuple(strat.ARMED_SETUPS) == ARMED_BEKLENEN
    assert armed_sonrasi_ayni, f"ARMED_SETUPS koşum sonrasında değişmiş: {strat.ARMED_SETUPS}"
    assert brk.derisk_mult is ORIJ_DERISK, "derisk_mult koşum sırasında yamalanmış — rampa kanıtı bozuk"

    # kill#3: motor parmak izi replay SONRASI aynı mı? (033 dersi — mtime değişimi hücreyi geçersiz kılar)
    motor_sonra = _motor_kunye()
    kill3_bozuk = [f for f in MOTOR_DOSYALAR if motor_once[f] != motor_sonra[f]]

    # ---- plan_log çapraz-kontrolü + NO_GO/REVIEW neden dağılımı (032 AYNEN) ------------------
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

    # ---- işlem/doluluk/ısı/performans metrikleri (032 AYNEN) ---------------------------------
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

    doluluk_pozgun = sum(r["n_acik"] for r in sess)
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
    dd_gt_tam = sum(1 for r in sess if r["dd"] > RAMPA_BEKLENEN["full_dd"])
    size0 = sum(1 for r in sess if r["size_mult"] <= 0.0)

    tavan_pct_bir = round(100.0 * sum(1 for r in birincil if r["sinif"] == "tavan_sifir")
                          / n_bir, 2) if n_bir else None

    butunluk_gecerli = (_frame_miss[0] == 0 and not _dup and not scan_vs_plan
                        and not yasak_yuklu and not base_max_bozuk and not kill3_bozuk)

    out = {
        "kart": "EDG-2026-035", "kosum": run, "smoke": smoke,
        "hucre": {"eksen": ("merkez" if run == "kontrol" else
                            ("slot" if "slot" in HUCRELER[run] else
                             "size" if "size" in HUCRELER[run] else "zarf")),
                  "slot": SLOT, "position_size_r": BOYUT_R,
                  "heat_hard_r": (float(ZARF) if ZARF is not None else ZARF_MERKEZ),
                  "zarf_enjekte": ZARF is not None},
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sure_sn": sure,
        "rampa_kablolu": rampa_kanit,
        "mb_motor": mb_kanit,
        "param_enjeksiyon": {
            "max_open_positions": {"once": onceki["max_open_positions"], "sonra": SLOT,
                                   "yuzey": "goal['limits'] (config.goal() derin kopyası — dosya değişmedi)"},
            "position_size_r": {"once": onceki["position_size_r"], "sonra": BOYUT_R,
                                "yuzey": ("strateji params sözlüğü (strategy.py _f yüzeyi; "
                                          "params_by_regime 4 rejimde boş — resolve_params assert'i; "
                                          "026 beyanı AYNEN)")},
            "heat_hard_r": {"once": onceki["heat_hard_r"],
                            "sonra": (float(ZARF) if ZARF is not None else onceki["heat_hard_r"]),
                            "yuzey": ("goal['limits'] — guard.classify_gate kanonik okuma yüzeyi "
                                      "(guard.py:326; 028 T10 emsali)" if ZARF is not None
                                      else "DOKUNULMADI (merkez 5.0R)")},
            "zarf_oz_sinama": zarf_oz_sinama,
        },
        "kill3_mtime": {"motor_once": motor_once, "motor_sonra": motor_sonra,
                        "bozuk_dosyalar": kill3_bozuk,
                        "temiz": not kill3_bozuk},
        "motor_sha256_16": {f: _sha(REPO / "meridian" / f)
                            for f in ("broker.py", "backtest.py", "strategy.py", "guard.py")},
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
            "yasakli_modul_yuklendi": yasak_yuklu,
            "base_max_open_bozuk": base_max_bozuk[:10],
            "kill3_bozuk_dosyalar": kill3_bozuk,
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
            "mb_islem_n": mb_islem_n,
            "plan_setup_dagilim": dict(sorted(plan_setup_n.items(), key=lambda kv: -kv[1])),
            "mb_plan_verdict": mb_plan_verdict,
        },
        "performans": {
            "net_pnl_equity": net_pnl_equity, "net_pnl_trades": net_pnl_trades,
            "maxdd_kanonik": detail.get("max_drawdown"),       # kapı (b) BUNUN üstünden
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
    (outdir / f"sonuc_{run}{ek}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str))
    (outdir / f"seanslar_{run}{ek}.json").write_text(
        json.dumps(sess, ensure_ascii=False, default=str))
    slim = [{k: t.get(k) for k in ("ts_open", "ts_close", "ticker", "r_multiple",
                                   "pnl_dollars", "exit_reason", "bars_held", "regime",
                                   "setup", "qty", "risk_dollars", "size_r")} for t in trades]
    (outdir / f"islemler_{run}{ek}.json").write_text(
        json.dumps(slim, ensure_ascii=False, default=str))

    print(f"\n=========== EDG-035 KOŞUM [{run}{ek}] ===========")
    print(f"hücre: slot={SLOT} size_r={BOYUT_R} zarf={out['hucre']['heat_hard_r']} "
          f"(enjekte={out['hucre']['zarf_enjekte']})")
    print(f"replay {r_start}→{r_end}  sv={sv}  sembol={len(bars)}  süre={sure}s")
    print(f"rampa kablolu: band={rampa_cfg['full_dd']}/{rampa_cfg['floor_dd']} "
          f"kaynak={rampa_cfg['kaynak']}  mb ARMED_SETUPS'ta (sonda)={armed_sonrasi_ayni}")
    print(f"bütünlük geçerli={butunluk_gecerli}  frame_miss={_frame_miss[0]} dup={len(_dup)} "
          f"scan!=plan={len(scan_vs_plan)} yasak={yasak_yuklu} base_max_bozuk={len(base_max_bozuk)} "
          f"kill3_bozuk={kill3_bozuk}")
    print(f"işlem n={n_islem} (mb={mb_islem_n})  net_pnl={net_pnl_equity}  "
          f"maxdd_kanonik={detail.get('max_drawdown')}  sharpe={detail.get('sharpe')}  "
          f"avg_r={detail.get('avg_r')}")
    print(f"NO_GO nedenleri: {out['islem']['nogo_neden_dagilim']}")
    print(f"yazıldı: {outdir}/sonuc_{run}{ek}.json")


# ---------------------------------------------------------------------------------------------
# KİLL#1 ŞASİ-KONTROLÜ — kontrol ↔ EDG-032 cmb BİT-ÖZDEŞLİK
# ---------------------------------------------------------------------------------------------
# sonuc'un ölçüm blokları: bunlar replay içeriğinin deterministik türevleridir → derin-eşit OLMALI
SONUC_OLCUM_BLOKLARI = ("performans", "doluluk", "tepe_isi", "betim",
                        "tasnif_tum_seans", "birincil", "ci95_ay_kumeli")


def kontrol_kiyas(smoke: bool = False):
    ek = "_smoke" if smoke else ""
    yerel_dir = (SANDBOX / "smoke") if smoke else SANDBOX
    ref_dir = (EDG032 / "smoke") if smoke else EDG032

    yerel = {
        "islemler": yerel_dir / f"islemler_kontrol{ek}.json",
        "seanslar": yerel_dir / f"seanslar_kontrol{ek}.json",
        "sonuc": yerel_dir / f"sonuc_kontrol{ek}.json",
    }
    ref = {
        "islemler": ref_dir / f"islemler_cmb{ek}.json",
        "seanslar": ref_dir / f"seanslar_cmb{ek}.json",
        "sonuc": ref_dir / f"sonuc_cmb{ek}.json",
    }
    for ad, p in {**yerel, **ref}.items():
        if not p.exists():
            sys.exit(f"kontrol_kiyas: dosya yok: {p}")

    sha_yerel = {k: _sha_full(p) for k, p in yerel.items()}
    sha_ref = {k: _sha_full(p) for k, p in ref.items()}
    bayt_ozdes = {k: (sha_yerel[k] == sha_ref[k]) for k in ("islemler", "seanslar")}

    sy = json.loads(yerel["sonuc"].read_text())
    sr = json.loads(ref["sonuc"].read_text())

    blok_esit = {}
    blok_fark_ozet = {}
    for b in SONUC_OLCUM_BLOKLARI:
        blok_esit[b] = (sy.get(b) == sr.get(b))
        if not blok_esit[b]:
            blok_fark_ozet[b] = {"yerel": sy.get(b), "ref_032": sr.get(b)}

    # islem bloğu: 032'de mb sayaçları mb_kanal altındaydı; ölçüm içeriği aynı olmalı
    islem_y = {k: v for k, v in (sy.get("islem") or {}).items()
               if k not in ("mb_islem_n", "plan_setup_dagilim", "mb_plan_verdict")}
    islem_r = dict(sr.get("islem") or {})
    blok_esit["islem"] = (islem_y == islem_r)
    if not blok_esit["islem"]:
        blok_fark_ozet["islem"] = {
            k: {"yerel": islem_y.get(k), "ref_032": islem_r.get(k)}
            for k in sorted(set(islem_y) | set(islem_r)) if islem_y.get(k) != islem_r.get(k)}
    blok_esit["mb_sayaclari"] = (
        sy["islem"].get("mb_islem_n") == sr.get("mb_kanal", {}).get("mb_islem_n")
        and sy["islem"].get("plan_setup_dagilim") == sr.get("mb_kanal", {}).get("plan_setup_dagilim")
        and sy["islem"].get("mb_plan_verdict") == sr.get("mb_kanal", {}).get("mb_plan_verdict"))

    # replay kimliği (deterministik künye alanları)
    replay_esit = (sy.get("replay") == sr.get("replay"))
    if not replay_esit:
        blok_fark_ozet["replay"] = {"yerel": sy.get("replay"), "ref_032": sr.get("replay")}
    blok_esit["replay"] = replay_esit

    # bütünlük sayaçları (032'de kill3 alanı yoktu — ortak sayaçlar kıyaslanır)
    ortak_but = ("frame_okunamadi", "tekrar_tarih", "scan_vs_plan_uyusmazlik_n",
                 "yasakli_modul_yuklendi", "base_max_open_bozuk", "gecerli")
    blok_esit["butunluk_ortak"] = all(
        sy["butunluk"].get(k) == sr["butunluk"].get(k) for k in ortak_but)

    # config sha kimliği (sandbox kopyaları bayt-aynı kaynaktan mı?)
    config_esit = all(
        sy["config_sha256_16"][f]["sandbox"] == sr["config_sha256_16"][f]["sandbox"]
        for f in ("goal.yaml", "strategy.yaml", "bounds.yaml"))
    blok_esit["config_sha_sandbox"] = config_esit

    # motor sha: FARKLI OLMASI BEKLENİR (v237 dağıtımı) — kayıt, kıyas ölçütü DEĞİL
    motor_fark = {f: {"yerel_v237": sy["motor_sha256_16"].get(f),
                      "ref_032": sr["motor_sha256_16"].get(f)}
                  for f in ("broker.py", "backtest.py", "strategy.py")}

    gecti = all(bayt_ozdes.values()) and all(blok_esit.values())

    out = {
        "kart": "EDG-2026-035", "adim": f"kill#1 şasi-kontrolü{ek}",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "tanim": ("yeni-motor (v237) default + goal-enjeksiyon(max_open 20, size 0.5) TAM replay "
                  "↔ EDG-032 cmb HAZIR çıktıları. Bit-özdeşlik iddiası DETERMİNİSTİK replay "
                  "içeriği üzerinden: islemler+seanslar dosya baytları (sha256) + sonuc ölçüm "
                  "blokları derin-eşit. sonuc_cmb.json'ın kendisi bayt-özdeş OLAMAZ "
                  "(olcum_zamani/sure_sn/motor-sha koşum kimliğidir; motor-sha FARKI dağıtımın "
                  "kendisidir ve beklenen farktır)."),
        "dosya_sha256": {"yerel": sha_yerel, "ref_032": sha_ref},
        "bayt_ozdeslik": bayt_ozdes,
        "sonuc_blok_esitligi": blok_esit,
        "blok_fark_ozet": blok_fark_ozet or None,
        "motor_sha_farki_beklenen": motor_fark,
        "kill1_gecti": gecti,
    }
    (yerel_dir / f"kontrol_kiyas{ek}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str))

    print(f"\n===== EDG-035 KILL#1 ŞASİ-KONTROLÜ{ek} =====")
    print(f"islemler bayt-özdeş={bayt_ozdes['islemler']}  seanslar bayt-özdeş={bayt_ozdes['seanslar']}")
    print(f"sonuc blokları eşit: { {k: v for k, v in blok_esit.items()} }")
    print(f"KILL#1: {'GEÇTİ — kontrol koşumu = TABAN' if gecti else 'DÜŞTÜ — ölçüm DURUR (dağıtım-regresyon teşhisi)'}")
    print(f"yazıldı: {yerel_dir / f'kontrol_kiyas{ek}.json'}")
    if not gecti:
        sys.exit(2)


# ---------------------------------------------------------------------------------------------
# KIYAS — 6 hücre ↔ taban (kontrol) + kapı işaretleri + eğim haritası → sonuc.json
# ---------------------------------------------------------------------------------------------
def kiyas():
    import numpy as np

    def yukle(run):
        return {"sonuc": json.loads((SANDBOX / f"sonuc_{run}.json").read_text()),
                "seans": json.loads((SANDBOX / f"seanslar_{run}.json").read_text()),
                "islem": json.loads((SANDBOX / f"islemler_{run}.json").read_text())}

    R = {run: yukle(run) for run in ["kontrol"] + OFAT_SIRA}
    taban = R["kontrol"]
    st, pt = taban["sonuc"], taban["sonuc"]["performans"]

    # ---- kill#1 kanıtı: kontrol_kiyas.json GEÇMİŞ olmalı (taban ancak öyle taban olur) -------
    kk = json.loads((SANDBOX / "kontrol_kiyas.json").read_text())
    assert kk["kill1_gecti"], "kill#1 GEÇMEMİŞ — kiyas koşulamaz (kart: ölçüm durur)"

    # ---- bütünlük + kimlik: tüm koşumlar geçerli, motor parmak izi 7 koşumda AYNI ------------
    motor_ref = st["kill3_mtime"]["motor_once"]
    kimlik = {}
    for run in ["kontrol"] + OFAT_SIRA:
        s = R[run]["sonuc"]
        kimlik[run] = {
            "butunluk_gecerli": s["butunluk"]["gecerli"],
            "kill3_temiz": s["kill3_mtime"]["temiz"],
            "motor_ayni_tabanla": (s["kill3_mtime"]["motor_once"] == motor_ref
                                   and s["kill3_mtime"]["motor_sonra"] == motor_ref),
            "config_sha_ayni": all(
                s["config_sha256_16"][f]["sandbox"] == st["config_sha256_16"][f]["sandbox"]
                for f in ("goal.yaml", "strategy.yaml", "bounds.yaml")),
            "pencere_ayni": (s["replay"]["start"] == st["replay"]["start"]
                             and s["replay"]["end"] == st["replay"]["end"]
                             and s["replay"]["strategy_version"] == st["replay"]["strategy_version"]),
        }
    takvim_taban = [x["date"] for x in taban["seans"]]
    for run in OFAT_SIRA:
        kimlik[run]["takvim_ayni"] = ([x["date"] for x in R[run]["seans"]] == takvim_taban)
    kimlik_temiz = all(all(v for v in k.values()) for k in kimlik.values())

    aylar = sorted({d[:7] for d in takvim_taban})
    M = len(aylar)
    idx_all = np.arange(M)

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

    def ci95(arr, nd=3):
        a = np.asarray([x for x in arr if x == x])
        if not len(a):
            return None
        return {"lo": round(float(np.percentile(a, 2.5)), nd),
                "hi": round(float(np.percentile(a, 97.5)), nd),
                "orta": round(float(np.median(a)), nd)}

    A_t = ay_seri(taban["islem"])
    dd_taban = pt["maxdd_kanonik"]
    dd_esik = round(dd_taban * KAPI_DD_KATSAYI, 5) if dd_taban is not None else None

    hucre_tablo = {}
    for run in OFAT_SIRA:
        s = R[run]["sonuc"]
        p = s["performans"]
        A_h = ay_seri(R[run]["islem"])

        # EŞLENİK bootstrap: her hücre-taban çifti İÇİN AYNI tohum → çekilişler hücreler arasında
        # da özdeş (default_rng(BOOT_SEED), M aynı) — kıyaslanabilirlik maksimum
        rng = np.random.default_rng(BOOT_SEED)
        f_cnt = np.empty(BOOT_ITER)
        f_pnl = np.empty(BOOT_ITER)
        f_avgr = []
        avgr_atlanan = 0
        for i in range(BOOT_ITER):
            pick = rng.choice(idx_all, size=M, replace=True)
            f_cnt[i] = float(A_h["cnt"][pick].sum()) - float(A_t["cnt"][pick].sum())
            f_pnl[i] = float(A_h["pnl"][pick].sum()) - float(A_t["pnl"][pick].sum())
            rnT, rnH = float(A_t["rn"][pick].sum()), float(A_h["rn"][pick].sum())
            if rnT > 0 and rnH > 0:
                f_avgr.append(float(A_h["rsum"][pick].sum()) / rnH
                              - float(A_t["rsum"][pick].sum()) / rnT)
            else:
                avgr_atlanan += 1

        fark_pnl_ci = ci95(f_pnl, nd=1)
        fark_cnt_ci = ci95(f_cnt)
        fark_avgr_ci = ci95(f_avgr, nd=4)

        # ---- ÜÇ KAPI (kart success_metric, DONUK — MEKANİK işaret, hüküm YOK) ----------------
        kapi_a = ("gecti" if (fark_pnl_ci is not None and fark_pnl_ci["lo"] > 0) else
                  ("olculemedi" if fark_pnl_ci is None else "dustu"))
        kapi_b = (("gecti" if p["maxdd_kanonik"] <= dd_taban * KAPI_DD_KATSAYI else "dustu")
                  if (dd_taban is not None and p.get("maxdd_kanonik") is not None) else "olculemedi")
        kapi_c = (("gecti" if p["sharpe"] >= KAPI_SHARPE_MIN else "dustu")
                  if p.get("sharpe") is not None else "olculemedi")
        aday = "EVET" if (kapi_a == "gecti" and kapi_b == "gecti" and kapi_c == "gecti") else "hayir"

        hucre_tablo[run] = {
            "hucre": s["hucre"],
            "islem_n": s["islem"]["n"], "delta_n": s["islem"]["n"] - st["islem"]["n"],
            "delta_n_ci95": fark_cnt_ci,
            "net_pnl_equity": p["net_pnl_equity"],
            "delta_pnl_nokta": (round(p["net_pnl_equity"] - pt["net_pnl_equity"], 2)
                                if (p.get("net_pnl_equity") is not None
                                    and pt.get("net_pnl_equity") is not None) else None),
            "delta_pnl_ci95_eslenik_ay_kumeli": fark_pnl_ci,
            "maxdd_kanonik": p["maxdd_kanonik"], "maxdd_m2m": p["maxdd_m2m"],
            "sharpe": p["sharpe"], "avg_r": p["avg_r"],
            "delta_avg_r_ci95": fark_avgr_ci, "avg_r_atlanan_iter": avgr_atlanan,
            "win_rate": p["win_rate"], "total_return": p["total_return"],
            "mb_islem_n": s["islem"]["mb_islem_n"],
            "setup_bazinda": s["islem"]["setup_bazinda"],
            "verdict_dagilim": s["islem"]["verdict_dagilim"],
            "nogo_heat_hard_n": s["islem"]["nogo_neden_dagilim"].get("heat_hard", 0),
            "nogo_max_open_n": s["islem"]["nogo_neden_dagilim"].get("max_open_positions", 0),
            "doluluk_orani_slot": s["doluluk"]["doluluk_orani_slot"],
            "ort_acik_pozisyon": s["doluluk"]["ort_acik_pozisyon"],
            "isi_gerceklesen_max": ((s["tepe_isi"]["gerceklesen_open_fazi"]["size_r_toplam"] or {})
                                    .get("max")),
            "eszamanli_poz_max": s["tepe_isi"]["eszamanli_poz_max"],
            "tavan_sifir_pct_birincil": s["birincil"]["tavan_sifir_pct"],
            "takvim_disi_islem": A_h["takvim_disi_islem"],
            "kapilar_kart_donuk": {
                "a_dpnl_ci_alt_gt0": {"olcut": "ΔP&L(hücre−taban) CI ALT > 0 (CI-üstünlük)",
                                      "ci": fark_pnl_ci, "isaret": kapi_a},
                "b_dd_le_taban_1p3x": {"olcut": f"maxdd ≤ taban×{KAPI_DD_KATSAYI}",
                                       "taban_dd": dd_taban, "esik": dd_esik,
                                       "esik_kart_yuvarlak": 0.1648,
                                       "deger": p["maxdd_kanonik"], "isaret": kapi_b},
                "c_sharpe_ge_0p20": {"olcut": f"sharpe ≥ {KAPI_SHARPE_MIN}",
                                     "deger": p["sharpe"], "isaret": kapi_c},
                "benimseme_adayi_mekanik": aday,
            },
        }

    # ---- EĞİM HARİTASI (kart: karar değil bilgi; birim beyanlı sonlu farklar) ----------------
    def nokta(run):
        if run == "kontrol":
            return {"pnl": pt["net_pnl_equity"], "sharpe": pt["sharpe"],
                    "dd": pt["maxdd_kanonik"], "n": st["islem"]["n"], "avg_r": pt["avg_r"]}
        p = R[run]["sonuc"]["performans"]
        return {"pnl": p["net_pnl_equity"], "sharpe": p["sharpe"],
                "dd": p["maxdd_kanonik"], "n": R[run]["sonuc"]["islem"]["n"], "avg_r": p["avg_r"]}

    def egim(sol_run, sol_x, sag_run, sag_x, birim_adi):
        a, b = nokta(sol_run), nokta(sag_run)
        dx = sag_x - sol_x
        seg = {"aralik": f"{sol_x}→{sag_x}", "birim": birim_adi}
        for m in ("pnl", "sharpe", "dd", "n", "avg_r"):
            if a[m] is None or b[m] is None:
                seg[f"d{m}_per_birim"] = None      # ölçülemedi
            else:
                seg[f"d{m}_per_birim"] = round((b[m] - a[m]) / dx, 6 if m != "pnl" else 2)
        return seg

    egim_haritasi = {
        "not": ("KARAR DEĞİL BİLGİ (kart features_asof): nokta-tahmin sonlu farkları — CI'sız; "
                "benimseme yalnız kapı-işaretlerinden, eğimden DEĞİL. Zarf ekseninde merkez 5.0 "
                "SOL uçtur (kart grid'i 6.5/8.0 — iki komşu da sağda)"),
        "slot": {"noktalar": {"15": nokta("slot15"), "20": nokta("kontrol"), "25": nokta("slot25")},
                 "segmentler": [egim("slot15", 15, "kontrol", 20, "1 slot"),
                                egim("kontrol", 20, "slot25", 25, "1 slot")]},
        "size_r": {"noktalar": {"0.40": nokta("size040"), "0.50": nokta("kontrol"),
                                "0.65": nokta("size065")},
                   "segmentler": [egim("size040", 0.40, "kontrol", 0.50, "1.0R (ΔP&L/ΔR)"),
                                  egim("kontrol", 0.50, "size065", 0.65, "1.0R (ΔP&L/ΔR)")]},
        "zarf_r": {"noktalar": {"5.0": nokta("kontrol"), "6.5": nokta("zarf65"),
                                "8.0": nokta("zarf80")},
                   "segmentler": [egim("kontrol", 5.0, "zarf65", 6.5, "1.0R zarf"),
                                  egim("zarf65", 6.5, "zarf80", 8.0, "1.0R zarf")]},
    }

    out = {
        "kart": "EDG-2026-035",
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "olcum_ajani_beyani": (
            "SALT-ÖLÇÜM: karta/motor koduna/gerçek state'e DOKUNULMADI; git/canlı/ssh/serve.sh "
            "YOK. Rampa monkeypatch'siz (motor kablolu — kanıt rampa_kablolu bloklarında); mb "
            "motorun ARMED_SETUPS'unda (kanal enjeksiyonu yok). Zarf hücreleri goal['limits'] "
            "kanonik yüzeyinde beyanlı enjeksiyon + sentetik öz-sınama (028 T10 emsali). "
            "TABAN = kontrol koşumu (kill#1 bit-özdeşlik kanıtı kontrol_kiyas.json'da; 032-cmb "
            "ile islemler/seanslar sha256 bayt-özdeş). NOKTA-P&L SIRALAMASI ÜRETİLMEDİ (kart "
            "serap-koruması). HÜKÜM YAZILMADI — Rol-1 işler."),
        "kill1_sasi_kontrolu": {"kaynak": "kontrol_kiyas.json", "gecti": kk["kill1_gecti"],
                                "islemler_sha256": kk["dosya_sha256"]["yerel"]["islemler"],
                                "ref_032_islemler_sha256": kk["dosya_sha256"]["ref_032"]["islemler"]},
        "taban": {"koşum": "kontrol (= 032-cmb bit-özdeş)",
                  "islem_n": st["islem"]["n"], "net_pnl_equity": pt["net_pnl_equity"],
                  "maxdd_kanonik": dd_taban, "sharpe": pt["sharpe"], "avg_r": pt["avg_r"],
                  "win_rate": pt["win_rate"], "mb_islem_n": st["islem"]["mb_islem_n"],
                  "dd_kapi_esigi_1p3x": dd_esik},
        "yontem": {
            "eslenik_bootstrap": ("ay-kümeli EŞLENİK bootstrap: takvim aylarından AYNI çekiliş "
                                  f"hücre+taban çiftine; fark = HÜCRE − TABAN; iter={BOOT_ITER}, "
                                  f"seed={BOOT_SEED}, n_ay={M}; tohum hücreler arasında da aynı "
                                  "(çekilişler özdeş → hücreler arası kıyaslanabilir)"),
            "islem_ay_anahtari": "ts_open[:7] (giriş ayı — şasi tanımı AYNEN)",
            "maxdd": "motor-kanonik score.score_detail.max_drawdown",
            "cok_test_notu": ("K=6 hücre tek kartta sınandı (kart k_registry; K grid'de çarpılarak "
                              "sayılır) — DSR/çoklu-test değerlendirmesi Rol-1'in"),
        },
        "kimlik_butunluk": {"per_run": kimlik, "hepsi_temiz": kimlik_temiz,
                            "motor_sha256_16_v237": st["motor_sha256_16"]},
        "hucre_tablosu": hucre_tablo,
        "egim_haritasi": egim_haritasi,
        "kapi_ozeti_mekanik": {run: hucre_tablo[run]["kapilar_kart_donuk"]["benimseme_adayi_mekanik"]
                               for run in OFAT_SIRA},
        "dosyalar": {run: {"sonuc": f"sonuc_{run}.json", "seanslar": f"seanslar_{run}.json",
                           "islemler": f"islemler_{run}.json"}
                     for run in ["kontrol"] + OFAT_SIRA},
    }
    (SANDBOX / "sonuc.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))

    print("\n==================== EDG-035 OFAT ÖZET ====================")
    print(f"kimlik/bütünlük hepsi temiz: {kimlik_temiz}")
    print(f"taban: n={st['islem']['n']} pnl={pt['net_pnl_equity']} dd={dd_taban} "
          f"sharpe={pt['sharpe']} (dd eşiği ×1.3 = {dd_esik})")
    for run in OFAT_SIRA:
        h = hucre_tablo[run]
        k = h["kapilar_kart_donuk"]
        print(f"{run:8s} n={h['islem_n']:4d} pnl={h['net_pnl_equity']:>9} "
              f"Δpnl_CI=[{(k['a_dpnl_ci_alt_gt0']['ci'] or {}).get('lo')}, "
              f"{(k['a_dpnl_ci_alt_gt0']['ci'] or {}).get('hi')}] "
              f"dd={h['maxdd_kanonik']} sharpe={h['sharpe']} | "
              f"kapılar a={k['a_dpnl_ci_alt_gt0']['isaret']} b={k['b_dd_le_taban_1p3x']['isaret']} "
              f"c={k['c_sharpe_ge_0p20']['isaret']} aday={k['benimseme_adayi_mekanik']}")
    print(f"yazıldı: {SANDBOX/'sonuc.json'}")
    print("===========================================================\n")


if __name__ == "__main__":
    mod = sys.argv[1] if len(sys.argv) > 1 else ""
    smoke = "--smoke" in sys.argv
    if mod in HUCRELER:
        kosum(mod, smoke=smoke)
    elif mod == "kontrol_kiyas":
        kontrol_kiyas(smoke=smoke)
    elif mod == "kiyas":
        kiyas()
    else:
        sys.exit("kullanım: olcum.py {kontrol|slot15|slot25|size040|size065|zarf65|zarf80|kontrol_kiyas|kiyas} [--smoke]")

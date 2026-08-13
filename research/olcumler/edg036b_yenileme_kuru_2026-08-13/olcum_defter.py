"""EDG-2026-036b — TAM-SATIR TOHUM KOŞUMU + PLAN DEFTERİ (C+mb, 032 dünyası birebir) · 2026-08-13

Kart: research/cards/EDG-2026-036-tohum-yenileme.yaml (OKU-DOKUNMA; hüküm Rol-1'in).
Rol: ÖLÇÜM ajanı. Bu modül HÜKÜM VERMEZ, karta dokunmaz, git/canlı/broker/state'e YAZMAZ,
repo koduna DOKUNMAZ.

036b EKİ (bu koşumun VAR OLMA SEBEBİ — kart `hukum_duzeltmesi.eksik_adim`):
  EDG-032b koşumu yalnız İŞLEM defterini yazdı. Gerçek yenileme yolu (`run.py:276-283`)
  `trade_plans.jsonl`i de BAŞTAN yazar. Plan defteri olmadan yenileme korunum dedektörünü bozar
  (bugün 409 plan ↔ 97 işlem; 885 işleme karşı ESKİ plan defteri kalırsa "açıklanamayan" patlar).
  Bu koşum AYNI DÜNYAYI yeniden üretir ve bu kez `res.plan_log`u da TAM SATIR serileştirir:
    planlar_tam_kontrol.json       = res.plan_log OLDUĞU GİBİ (kırpma YOK) — ham kaynak
    planlar_yenileme_kontrol.json  = run.py:276-283 `_keep` seçimi BİREBİR = yenilemenin YAZACAĞI defter
    adaylar_yenileme_kontrol.json  = run.py:281 `candidate_log[-300:]` = candidates.jsonl'ın yazacağı
  ÖZDEŞLİK KAPISI DEĞİŞMEDİ: işlem defteri (slim) yine 032-cmb ile BAYT-ÖZDEŞ olmak ZORUNDA.

NİÇİN: EDG-036 hükmü — tohum yenilemesi MEVCUT artefaktla YAPILAMAZ, çünkü
`edg032_final_paket_2026-08-12/islemler_cmb.json` bir SLIM PROJEKSİYON (olcum.py:725-729 tam
işlem satırını 12 alana kırpıyor; ikisi — risk_dollars/size_r — broker satırında olmadığı için
885/885 boş). Canlı `trades` şeması 26 alan. TAM satırlar 032 koşumunda BELLEKTE vardı
(broker.close_position → broker.py:685-702) ama diske yazılmadı. Bu koşum AYNI DÜNYAYI yeniden
üretir ve defteri KIRPMADAN serileştirir.

ŞASİ: EDG-035 (research/olcumler/edg035_duyarlilik_2026-08-12/olcum.py) KONTROL koşumu AYNEN
devralındı — o koşum yeni motorla (v237+) 032-cmb ile BAYT-ÖZDEŞ çıktı üretti
(islemler sha d4033de6…c11a7d). Devralınan her şey aynı: izole sandbox (EDG-022 DONMUŞ config
kopyaları + salt-okunur bars symlink), kayıt kancaları, bütünlük kontrolleri, ay-kümeli
bootstrap (5000, seed 20260812), rampa-kablolu kanıtı, mb-ARMED_SETUPS kanıtı.
  1. RAMPA MONKEYPATCH YOK: broker.derisk_mult derisk_ramp() üzerinden goal okur; sandbox
     goal'ünde derisk anahtarı YOK → fail-safe 0.15/0.36 = C+mb rampası (assert'li).
  2. MB armed_extra KANALI YOK: strat.ARMED_SETUPS mb'yi SONDA içeriyor (assert'li).

TEK FARK (bu kartın tüm işi): işlem defteri İKİ dosyaya yazılır —
  islemler_kontrol.json  = 12 alanlık SLIM projeksiyon (035/032 ile birebir kod) → ÖZDEŞLİK KAPISI
  islemler_tam.json      = broker satırının KENDİSİ, kırpma YOK (tohum adayı)
Slim projeksiyon 032'nin `islemler_cmb.json`u ile BAYT-ÖZDEŞ olmak ZORUNDA (kill#1). Değilse
tam-satır yazımı dünyayı değiştirmiş demektir ve defter tohum olarak kullanılamaz.

ÖZDEŞLİK KAPISI (kill#1): islemler(slim)+seanslar dosya baytları 032-cmb ile sha256-özdeş +
sonuc ölçüm blokları derin-eşit. (sonuc dosyasının KENDİSİ bayt-özdeş OLAMAZ: olcum_zamani/
sure_sn/motor-sha koşum kimliğidir.) Düşerse ölçüm DURUR (exit 2).

KAPSAMA RAPORU (`kapsama`): canlı `trades` şemasının 26 alanı için ALAN ALAN muhasebe —
dolu / yapısal-boş (prosedürel damga: replay üretmez, yazar basar) / eksik + NEDEN.
UYDURMA YASAĞI: hiçbir eksik alan doldurulmaz; adıyla sayılır.

TANIMLAR (035/032 şasi tanımları AYNEN): seans, ay kümesi = ts_open[:7], eşlenik ay-kümeli
bootstrap (5000, seed 20260812), max-dd = score.score_detail.max_drawdown.

KILL KONTROLLERİ:
  kill#1 özdeşlik: slim ≠ 032-cmb bayt-özdeş → ölçüm DURUR (exit 2).
  kill#2 bütünlük: frame_miss/dup/scan!=plan/yasak-modül/base_max bozuk → koşum GEÇERSİZ.
  kill#3 mtime  : motor dosyalarında koşum sırasında sha/mtime değişimi → koşum GEÇERSİZ.

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen = None + neden); YASA-4 (sessiz-yutma işaretli); YASA-6
(okuyucu: sonuc_kontrol.json + islemler_tam + ozdeslik.json + kapsama.json → dönüş raporu +
Rol-1). SALT-OKUMA: config.STATE koşum-başına izole sandbox; barlar sembolik bağla SALT-OKUNUR;
canlı state'e ve motor dosyalarına tek bayt yazılmaz. meridian.loop / counterfactual /
cf_backfill / hermes İTHAL EDİLMEZ — sys.modules ile kanıtlanır.

KULLANIM:
  olcum.py kontrol [--smoke]     # tam koşum (slim + TAM defter)
  olcum.py ozdeslik [--smoke]    # kill#1 özdeşlik kapısı; düşerse exit 2
  olcum.py kapsama               # 26 alanın kapsama tablosu → kapsama.json
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

# merkez (C+mb) — 032/035-kontrol dünyası AYNEN; bu kartta SAPMA YOK (tek hücre)
MERKEZ = {"slot": 20, "size": 0.5, "zarf": None, "gate_detay": False}
HUCRELER = {
    "kontrol": {},                                   # 032-cmb dünyası = özdeşlik tabanı
    # GERÇEK YENİLEME YOLU: run.py:190-191 `backtest.replay(..., with_gate_detail=True)`.
    # 032/032b şasisi with_gate_detail=False koşuyordu → plan satırında `gate_checks` YOK,
    # canlı defterde ise 409/409 DOLU. Bu hücre AYNI dünyayı gate-detay AÇIK koşar; işlem
    # defteri hâlâ 032-cmb ile bayt-özdeş çıkmalı (detay saf ÇIKTI toplayıcısıdır:
    # guard.classify_gate(detail_out=_det) — hükmü DEĞİL kaydını üretir). Özdeşlik ÖLÇÜLÜR.
    "kontrolgd": {"gate_detay": True},
}

# canlı `trades` şeması — storage.py:82-95 tipli kolonlar (25) + skill_chain (extra_json) = 26.
# EDG-036 `sema_uyumu.canli_trades_alanlari` ile birebir aynı liste (sıralı kıyas assert'i altında).
CANLI_SEMA = ("bars_held", "costs", "entry", "exit", "exit_reason", "exploration", "id", "kaynak",
              "mae_r", "mfe_r", "plan_id", "pnl_dollars", "pnl_pct", "qty", "r_multiple",
              "r_multiple_expected", "regime", "scaled_out", "score", "setup", "side",
              "skill_chain", "strategy_version", "ticker", "ts_close", "ts_open")
# replay defterinin ÜRETMEDİĞİ, yazarın bastığı prosedürel damgalar (ledgerstamp.py / yazar yolu)
PROSEDUREL_DAMGA = {
    "kaynak": ("ledgerstamp.stamp() ürünü — `loop._persist_trade`→live_paper, `run.replay_seed`→"
               "replay_seed (broker.py:666-667). Üretici satıra damga BASMAZ: satırın nereye "
               "yazıldığını bilen katman basar. Replay çıktısında YAPISAL OLARAK YOK."),
    "id": ("broker._id sayacı (T00001…) — koşum-içi sıra numarası. Replay ÜRETİR ama defter "
           "kimliği değildir: canlı deftere yazılırken yazarın sayacıyla yeniden basılır."),
    "strategy_version": ("plan['strategy_version'] üzerinden taşınır; replay DONMUŞ sandbox "
                         "strategy.yaml sürümünü (v3) yazar. Tohum partisinin sürüm damgası "
                         "prosedürdür (kart aşama-2) — replay'in ürettiği değer o damga DEĞİLDİR."),
}

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
    GATE_DETAY = bool(hucre.get("gate_detay"))

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
                          strategy_version=sv, params_by_regime=by_regime,
                          with_gate_detail=GATE_DETAY)
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
        "kart": "EDG-2026-036", "adim": "032b tam-satır koşumu", "kosum": run, "smoke": smoke,
        "hucre": {"eksen": ("merkez" if run == "kontrol" else
                            ("gate_detay" if HUCRELER[run].get("gate_detay") else
                             "slot" if "slot" in HUCRELER[run] else
                             "size" if "size" in HUCRELER[run] else "zarf")),
                  "slot": SLOT, "position_size_r": BOYUT_R,
                  "heat_hard_r": (float(ZARF) if ZARF is not None else ZARF_MERKEZ),
                  "zarf_enjekte": ZARF is not None,
                  "with_gate_detail": GATE_DETAY,
                  "gate_detay_beyani": ("run.py:190-191 gerçek yenileme yolu True koşar; "
                                        "032/032b şasisi False koşuyordu — bu alan hangi "
                                        "koşumun okunduğunu ayırır")},
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
    # (1) SLIM PROJEKSİYON — 032/035 kodu HARFİ HARFİNE (özdeşlik kapısının kıyas nesnesi)
    slim = [{k: t.get(k) for k in ("ts_open", "ts_close", "ticker", "r_multiple",
                                   "pnl_dollars", "exit_reason", "bars_held", "regime",
                                   "setup", "qty", "risk_dollars", "size_r")} for t in trades]
    (outdir / f"islemler_{run}{ek}.json").write_text(
        json.dumps(slim, ensure_ascii=False, default=str))
    # (2) TAM SATIR — broker.close_position'ın ürettiği sözlük OLDUĞU GİBİ (broker.py:685-702).
    # KIRPMA YOK, EKLEME YOK, YENİDEN ADLANDIRMA YOK: `res.trades` = `broker.closed`
    # (backtest.py:464) ve satırlar yalnız close_position tarafından append edilir (broker.py:703).
    # Anahtar sırası da bozulmaz (sort_keys YOK) — satırın kendi şeması kanıt niteliğindedir.
    (outdir / f"islemler_tam_{run}{ek}.json").write_text(
        json.dumps(trades, ensure_ascii=False, indent=1, default=str))
    # tam-satır defterinin alan envanteri (kapsama raporunun ham girdisi; hüküm YOK)
    tam_alanlar: dict[str, dict] = {}
    for t in trades:
        for k, v in t.items():
            b = tam_alanlar.setdefault(k, {"var": 0, "dolu": 0, "tipler": {}})
            b["var"] += 1
            if v is not None:
                b["dolu"] += 1
            tn = type(v).__name__
            b["tipler"][tn] = b["tipler"].get(tn, 0) + 1
    (outdir / f"alan_envanteri_{run}{ek}.json").write_text(json.dumps(
        {"n_satir": n_islem, "alanlar": dict(sorted(tam_alanlar.items())),
         "satir_anahtar_sirasi": list(trades[0].keys()) if trades else None,
         "tum_satirlar_ayni_anahtar_kumesi": (
             len({tuple(t.keys()) for t in trades}) == 1 if trades else None)},
        ensure_ascii=False, indent=1, default=str))

    # ---- (3) PLAN DEFTERİ — 036b'nin EKSİK ADIMI (kart hukum_duzeltmesi.eksik_adim) -----------
    # `res.plan_log` = backtest.py:441 `plan_log.append(plan)`; plan sözlüğü backtest.py:340-360
    # civarında kurulur ve guard.classify_gate hükmüyle damgalanır. KIRPMA/EKLEME/AD DEĞİŞİMİ YOK.
    planlar = res.plan_log or []
    adaylar = res.candidate_log or []
    (outdir / f"planlar_tam_{run}{ek}.json").write_text(
        json.dumps(planlar, ensure_ascii=False, indent=1, default=str))
    # YENİLEMENİN FİİLEN YAZACAĞI DEFTER — run.py:276-283 mantığı HARFİ HARFİNE kopyalandı:
    #   _keep = son 300 plan; ARTI işleme dönüşmüş ama son-300'de olmayan HER plan (öne eklenir).
    # Bu kod yolu `store.write_jsonl("trade_plans.jsonl", _keep)` ile diske giden listedir.
    _plans = planlar
    _need = {t.get("plan_id") for t in trades if t.get("plan_id")}
    _keep = _plans[-300:]
    _have = {p.get("id") for p in _keep}
    _keep = [p for p in _plans if p.get("id") in _need and p.get("id") not in _have] + _keep
    (outdir / f"planlar_yenileme_{run}{ek}.json").write_text(
        json.dumps(_keep, ensure_ascii=False, indent=1, default=str))
    _cand_keep = adaylar[-300:]
    (outdir / f"adaylar_yenileme_{run}{ek}.json").write_text(
        json.dumps(_cand_keep, ensure_ascii=False, indent=1, default=str))
    # plan defterinin alan envanteri (ham girdi; hüküm YOK)
    plan_alanlar: dict[str, dict] = {}
    for p in _keep:
        for k, v in p.items():
            b = plan_alanlar.setdefault(k, {"var": 0, "dolu": 0, "tipler": {}})
            b["var"] += 1
            if v is not None:
                b["dolu"] += 1
            b["tipler"][type(v).__name__] = b["tipler"].get(type(v).__name__, 0) + 1
    # KORUNUM DEDEKTÖRÜ GİRDİSİ: kaç işlem satırı `_keep` içinde plan bulabiliyor?
    _keep_ids = {p.get("id") for p in _keep}
    _eslesen = sum(1 for t in trades if t.get("plan_id") in _keep_ids)
    (outdir / f"plan_envanteri_{run}{ek}.json").write_text(json.dumps(
        {"plan_log_ham_n": len(planlar), "yenileme_keep_n": len(_keep),
         "candidate_log_ham_n": len(adaylar), "adaylar_keep_n": len(_cand_keep),
         "islem_n": n_islem, "islem_plan_id_tekil_n": len(_need),
         "keep_icinde_eslesen_islem_n": _eslesen,
         "keep_disinda_kalan_islem_n": n_islem - _eslesen,
         "korunum_orani": round(_eslesen / n_islem, 6) if n_islem else None,
         "alanlar": dict(sorted(plan_alanlar.items())),
         "satir_anahtar_sirasi": list(_keep[0].keys()) if _keep else None,
         "tum_satirlar_ayni_anahtar_kumesi": (
             len({tuple(p.keys()) for p in _keep}) == 1 if _keep else None),
         "anahtar_kumesi_cesidi": len({tuple(sorted(p.keys())) for p in _keep}) if _keep else None},
        ensure_ascii=False, indent=1, default=str))
    out["plan_defteri"] = {
        "plan_log_ham_n": len(planlar), "yenileme_keep_n": len(_keep),
        "candidate_log_ham_n": len(adaylar),
        "keep_icinde_eslesen_islem_n": _eslesen, "islem_n": n_islem,
        "yol": ("run.py:276-283 BİREBİR (son 300 + işleme dönüşen her plan) — "
                "store.write_jsonl('trade_plans.jsonl', _keep) girdisi"),
    }
    # sonuc dosyasını plan bloğuyla YENİDEN yaz (özdeşlik kapısı SONUC_OLCUM_BLOKLARI'na bakar;
    # `plan_defteri` o listede DEĞİL → kapı etkilenmez, ama künye tam olur)
    (outdir / f"sonuc_{run}{ek}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str))

    print(f"\n=========== EDG-032b TAM-SATIR KOŞUM [{run}{ek}] ===========")
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
    print(f"TAM defter: {outdir}/islemler_tam_{run}{ek}.json  satır={n_islem} "
          f"alan={len(tam_alanlar)} anahtar_kümesi_tek={len({tuple(t.keys()) for t in trades}) == 1 if trades else None}")
    print(f"PLAN defteri: plan_log_ham={len(planlar)}  yenileme_keep={len(_keep)}  "
          f"aday_keep={len(_cand_keep)}  keep-içinde-eşleşen-işlem={_eslesen}/{n_islem}  "
          f"plan_alan={len(plan_alanlar)}")
    print(f"yazıldı: {outdir}/sonuc_{run}{ek}.json")


# ---------------------------------------------------------------------------------------------
# KİLL#1 ŞASİ-KONTROLÜ — kontrol ↔ EDG-032 cmb BİT-ÖZDEŞLİK
# ---------------------------------------------------------------------------------------------
# sonuc'un ölçüm blokları: bunlar replay içeriğinin deterministik türevleridir → derin-eşit OLMALI
SONUC_OLCUM_BLOKLARI = ("performans", "doluluk", "tepe_isi", "betim",
                        "tasnif_tum_seans", "birincil", "ci95_ay_kumeli")


def ozdeslik(smoke: bool = False):
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
            sys.exit(f"ozdeslik: dosya yok: {p}")

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
        "kart": "EDG-2026-036", "adim": f"kill#1 ÖZDEŞLİK KAPISI{ek} (tam-satır koşumu ↔ EDG-032 cmb)",
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
    (yerel_dir / f"ozdeslik{ek}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str))

    print(f"\n===== EDG-032b KILL#1 ÖZDEŞLİK KAPISI{ek} =====")
    print(f"islemler bayt-özdeş={bayt_ozdes['islemler']}  seanslar bayt-özdeş={bayt_ozdes['seanslar']}")
    print(f"sonuc blokları eşit: { {k: v for k, v in blok_esit.items()} }")
    print(f"KILL#1: {'GEÇTİ — tam-satır defteri 032 dünyasının KENDİSİ' if gecti else 'DÜŞTÜ — ölçüm DURUR (tam-satır yazımı dünyayı değiştirmiş olur)'}")
    print(f"yazıldı: {yerel_dir / f'ozdeslik{ek}.json'}")
    if not gecti:
        sys.exit(2)


# ---------------------------------------------------------------------------------------------
# KAPSAMA — canlı `trades` şemasının 26 alanı için ALAN ALAN muhasebe → kapsama.json
# ---------------------------------------------------------------------------------------------
def kapsama(smoke: bool = False):
    """UYDURMA YASAĞI: hiçbir eksik alan doldurulmaz. Her alan üç kovadan BİRİNE düşer:
       dolu        = tam-satır defterinde var ve en az bir satırda None değil (n_dolu raporlanır)
       yapisal_bos = replay ÜRETMEZ; yazar/prosedür basar (PROSEDUREL_DAMGA gerekçesiyle)
       eksik       = şemada var, defterde YOK ∨ tüm satırlarda None — NEDEN adıyla yazılır
    """
    ek = "_smoke" if smoke else ""
    d = (SANDBOX / "smoke") if smoke else SANDBOX
    tam_p = d / f"islemler_tam_kontrol{ek}.json"
    slim_p = d / f"islemler_kontrol{ek}.json"
    if not tam_p.exists():
        sys.exit(f"kapsama: tam defter yok: {tam_p}")
    tam = json.loads(tam_p.read_text())
    slim = json.loads(slim_p.read_text()) if slim_p.exists() else []
    n = len(tam)

    # EDG-036'nın 26-alan listesiyle birebir mi? (kayma olursa ölçüm kendini ele verir)
    edg036 = json.loads((REPO / "research/olcumler/edg036_tohum_2026-08-13/sonuc.json").read_text())
    edg036_sema = tuple(edg036["sema_uyumu"]["canli_trades_alanlari"])
    edg036_eksik = list(edg036["sema_uyumu"]["EKSIK (uydurulamaz — None kalır)"])
    sema_ayni = tuple(sorted(CANLI_SEMA)) == tuple(sorted(edg036_sema))

    sayim: dict[str, dict] = {}
    for t in tam:
        for k, v in t.items():
            b = sayim.setdefault(k, {"var": 0, "dolu": 0, "tipler": {}, "ornek": None,
                                             "degerler": set()})
            b["var"] += 1
            if v is not None:
                b["dolu"] += 1
                if b["ornek"] is None:
                    b["ornek"] = v
            b["tipler"][type(v).__name__] = b["tipler"].get(type(v).__name__, 0) + 1
            # farklı-değer sayacı: `dolu` bir alanın SABİT mi (ör. hep False) yoksa DEĞİŞKEN mi
            # olduğunu ayırır — "alan üretildi" ile "alan bilgi taşıyor" aynı şey değildir.
            if len(b["degerler"]) <= 12:
                try:
                    b["degerler"].add(v if not isinstance(v, list) else tuple(v))
                except TypeError:
                    b["degerler"].add("<hashsiz>")

    tablo = {}
    kova: dict[str, list] = {"dolu": [], "yapisal_bos": [], "eksik": []}
    for alan in CANLI_SEMA:
        c = sayim.get(alan)
        if alan in PROSEDUREL_DAMGA and (c is None or c["dolu"] == 0):
            tablo[alan] = {"kova": "yapisal_bos", "defterde_var": bool(c), "n_dolu": 0,
                           "neden": PROSEDUREL_DAMGA[alan]}
            kova["yapisal_bos"].append(alan)
        elif c is None:
            tablo[alan] = {"kova": "eksik", "defterde_var": False, "n_dolu": 0,
                           "neden": ("broker.close_position satırında (broker.py:685-702) bu "
                                     "anahtar HİÇ üretilmiyor — replay motorunun bilmediği alan")}
            kova["eksik"].append(alan)
        elif c["dolu"] == 0:
            tablo[alan] = {"kova": "eksik", "defterde_var": True, "n_dolu": 0,
                           "tipler": c["tipler"],
                           "neden": ("satırda VAR ama %d/%d dolu — motor bu koşumda değer "
                                     "üretmedi (uydurulmadı, None bırakıldı)" % (0, n))}
            kova["eksik"].append(alan)
        else:
            girdi = {"kova": "dolu", "defterde_var": True, "n_dolu": c["dolu"], "n_satir": n,
                     "kapsama_pct": round(100.0 * c["dolu"] / n, 2) if n else None,
                     "tipler": c["tipler"], "ornek": c["ornek"],
                     "farkli_deger_n": (len(c["degerler"]) if len(c["degerler"]) <= 12
                                        else ">12 (sayılmadı — kardinalite yüksek)"),
                     "deger_kumesi": (sorted(map(str, c["degerler"]))
                                      if len(c["degerler"]) <= 12 else None)}
            if alan in PROSEDUREL_DAMGA:
                girdi["prosedurel_serh"] = PROSEDUREL_DAMGA[alan]
            tablo[alan] = girdi
            kova["dolu"].append(alan)

    fazla = sorted(set(sayim) - set(CANLI_SEMA))          # defterde var, canlı şemada yok
    slim_alanlar = sorted({k for t in slim for k in t}) if slim else []
    slim_dolu = sorted({k for t in slim for k, v in t.items() if v is not None}) if slim else []

    # ---- skill_chain ÖZEL ÖLÇÜMÜ (görev maddesi 4) ------------------------------------------
    zincirler: dict[str, int] = {}
    ilk_halka: dict[str, int] = {}
    bos_zincir = 0
    for t in tam:
        z = t.get("skill_chain")
        if not z:
            bos_zincir += 1
            continue
        anahtar = " > ".join(map(str, z))
        zincirler[anahtar] = zincirler.get(anahtar, 0) + 1
        ilk_halka[str(z[0])] = ilk_halka.get(str(z[0]), 0) + 1
    skill_chain_olcumu = {
        "replay_uretiyor_mu": (n - bos_zincir) > 0,
        "n_dolu": n - bos_zincir, "n_bos": bos_zincir, "n_satir": n,
        "uretim_noktasi": ("backtest.replay plan sözlüğü (backtest.py:355): "
                           "[skills.screener_for(setup), 'position-sizer', "
                           "'pre-trade-discipline-gate'] → broker.fill_entry (broker.py:549) → "
                           "Position.skill_chain → kapanış satırı (broker.py:694)"),
        "zincir_dagilimi": dict(sorted(zincirler.items(), key=lambda kv: -kv[1])),
        "ilk_halka_dagilimi": dict(sorted(ilk_halka.items(), key=lambda kv: -kv[1])),
        "canli_yazar_deseni": ("loop.py:1713 canlı döngü AYNI üçlüyü kuruyor "
                               "(skills.screener_for(setup) + position-sizer + "
                               "pre-trade-discipline-gate) — iki üreticinin zincir şeması "
                               "kod düzeyinde aynı desende"),
        "not": ("EDG-036 bu alanı 'uydurulamaz eksik' saymıştı; o hüküm SLIM PROJEKSİYON "
                "üzerinden verildi (slim 12 alanda skill_chain yoktu). Bu ölçüm alanın "
                "kendisini tam-satır defterinden okur."),
    }

    # ---- plan_id BİÇİMİ (EDG-036 sieve'inin 885/885 elediği eksen) ---------------------------
    import re as _re
    bicim = _re.compile(r"^P-\d{4}-\d{2}-\d{2}-[A-Za-z.\-]+$")
    pid = [t.get("plan_id") for t in tam]
    plan_id_olcumu = {
        "n_dolu": sum(1 for x in pid if x),
        "canli_bicim_uyan_n": sum(1 for x in pid if x and bicim.match(str(x))),
        "bicim_beyani": ("canlı şema `P-YYYY-MM-DD-TICKER` (backtest.py:342-349 blok beyanı: "
                         "replay plan kimliği 2026-07-21'de canlı şemaya çevrildi)"),
        "ornek": next((x for x in pid if x), None),
        "tekil_n": len({x for x in pid if x}),
    }

    out = {
        "kart": "EDG-2026-036", "adim": f"tam-satır kapsama raporu{ek}",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "defter": {"yol": str(tam_p), "n_satir": n, "boyut_bayt": tam_p.stat().st_size,
                   "sha256": _sha_full(tam_p),
                   "satir_anahtar_sirasi": list(tam[0].keys()) if tam else None,
                   "tum_satirlar_ayni_anahtar_kumesi": (
                       len({tuple(t.keys()) for t in tam}) == 1 if tam else None)},
        "canli_sema": {"n_alan": len(CANLI_SEMA), "alanlar": list(CANLI_SEMA),
                       "kaynak": ("meridian/storage.py:82-95 tipli kolonlar (25) + skill_chain "
                                  "(extra_json — storage.py:79 beyanı) = 26"),
                       "edg036_listesiyle_ayni": sema_ayni},
        "kapsama_tablosu": tablo,
        "kova_ozeti": {k: {"n": len(v), "alanlar": v} for k, v in kova.items()},
        "defterde_fazla_canli_semada_yok": fazla,
        "slim_projeksiyon_kiyasi": {
            "yol": str(slim_p), "n_alan": len(slim_alanlar), "alanlar": slim_alanlar,
            "dolu_alanlar": slim_dolu,
            "slim_hep_bos_alanlar": sorted(set(slim_alanlar) - set(slim_dolu)),
            "tam_defterin_slim_uzeri_kazanimi": sorted(set(sayim) - set(slim_alanlar)),
        },
        "skill_chain_olcumu": skill_chain_olcumu,
        "plan_id_olcumu": plan_id_olcumu,
        "edg036_eksik_listesinin_yeniden_olcumu": {
            a: tablo.get(a, {}).get("kova", "SEMADA_YOK") for a in edg036_eksik},
        "beyan": ("Bu dosya HÜKÜM İÇERMEZ. Kovalar mekaniktir: `dolu` = defterde ≥1 satırda "
                  "None-olmayan değer; `yapisal_bos` = replay üretmez, yazar/prosedür basar; "
                  "`eksik` = şemada var, defterde yok ∨ hepsi None. Hiçbir alan doldurulmadı."),
    }
    (d / f"kapsama{ek}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))

    print(f"\n===== EDG-032b KAPSAMA RAPORU{ek} =====")
    print(f"defter: {tam_p}  satır={n}  boyut={tam_p.stat().st_size}B")
    print(f"canlı şema {len(CANLI_SEMA)} alan (EDG-036 listesiyle aynı={sema_ayni})")
    for kv in ("dolu", "yapisal_bos", "eksik"):
        print(f"  {kv:12s} n={len(kova[kv]):2d}  {kova[kv]}")
    print(f"defterde fazla (canlı şemada yok): {fazla}")
    print(f"skill_chain: replay üretiyor={skill_chain_olcumu['replay_uretiyor_mu']} "
          f"dolu={skill_chain_olcumu['n_dolu']}/{n} zincir_çeşidi={len(zincirler)}")
    print(f"plan_id: dolu={plan_id_olcumu['n_dolu']}/{n} "
          f"canlı-biçim-uyan={plan_id_olcumu['canli_bicim_uyan_n']} örnek={plan_id_olcumu['ornek']}")
    print(f"yazıldı: {d / f'kapsama{ek}.json'}")



if __name__ == "__main__":
    mod = sys.argv[1] if len(sys.argv) > 1 else ""
    smoke = "--smoke" in sys.argv
    if mod in HUCRELER:
        kosum(mod, smoke=smoke)
    elif mod == "ozdeslik":
        ozdeslik(smoke=smoke)
    elif mod == "kapsama":
        kapsama(smoke=smoke)
    else:
        sys.exit("kullanım: olcum.py {kontrol|ozdeslik|kapsama} [--smoke]")

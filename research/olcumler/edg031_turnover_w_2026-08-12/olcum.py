"""EDG-2026-031 — TURNOVER AĞIRLIĞI (w_turnover 0.05 / 0.10) · ölçüm aracı (2026-08-12)

Kart: research/cards/EDG-2026-031-turnover-agirlik.yaml (OKU-DOKUNMA; hüküm Rol-1'in).
Rol: ÖLÇÜM ajanı. Bu modül HÜKÜM VERMEZ, karta dokunmaz, git/canlı/broker/state'e YAZMAZ.

ŞASİ: EDG-026 (research/olcumler/edg026_slot20_2026-08-12/olcum.py) C-dünyası AYNEN devralındı:
izole sandbox (EDG-022 donmuş config'leri), rampa-15/36 monkeypatch'i (beyanlı), slot-20 +
0.5R param-enjeksiyonları, kancalar, bütünlük kontrolleri, ay-kümeli EŞLENİK bootstrap
(5000 iter, seed 20260812). KIYAS TABANI = EDG-026'nın HAZIR C çıktıları (YENİDEN KOŞULMAZ;
motor/config sha'ları birebir DOĞRULANIR — değilse kıyas ŞERHLİ). test_turnover_kablolama_v149
w=0 varsayılanının bit-bit sıfır-etkili olduğunu çivilediği için C AYNI ZAMANDA w=0 hücresidir.

İKİ KOŞUM (kart parameter_grid, DONUK):
  w005: entry.w_turnover = 0.05    w010: entry.w_turnover = 0.10
  ENJEKSİYON 3 (bu kartın tek yeni değişkeni): strateji params sözlüğüne DÜZ anahtar
  "entry.w_turnover" yazılır (strategy.py:477 `_f(params,"entry.w_turnover",0.0)` — dosyaya tek
  bayt yazılmaz; params_by_regime 4 rejimde de bu anahtarı İÇERMEZ, koşum öncesi assert edilir;
  resolve_params yayılımı 4 rejimde kanıtlanır). Kablo YALNIZ evaluate_entry'de (breakout_vcp)
  yaşar; pullback/exhaustion_hammer skorları terimi OKUMAZ (beyan — payda sayacının kapsamı bu).

ÖZ-SINAMA (kart: "enjeksiyonda skorun GERÇEKTEN değiştiğini kanıtla") — İKİ KATMAN:
  (1) ÖN-UÇUŞ (replay'den önce): gerçek bir kapsam-içi sembolün (AAPL/MSFT/NVDA/AMZN ilk bulunan)
      backtest yoluyla BİREBİR kurulan alt-çerçevesinde `_turnover_now` ölçülebilir değer ve
      `turnover_score` [1,99] puanı dönmeli — payda kablosunun sandbox içinde canlı olduğunun kanıtı.
  (2) TARAMA-İÇİ KARŞI-OLGUSAL: scan_entry kancası, sinyal DOĞAN her (gün,sembol) için aynı
      girdilerle `entry.w_turnover=0.0` kopyasını da tarar (girdiler portföyden bağımsız — aynı
      sub/rs/eff; tek fark anahtar). Koşum sonu: turnover'ı ÖLÇÜLEN breakout sinyalleri arasında
      skoru w0'dan SAPAN en az 1 sinyal ŞARTTIR (yoksa enjeksiyon fiilen İNERT → bütünlük kırmızı);
      turnover'ı ÖLÇÜLEMEYEN ya da breakout-dışı aynı-setup sinyallerde skor w0 ile BİREBİR AYNI
      olmak ZORUNDADIR (FAIL-OPEN çivisinin replay-içi hâli; ihlal → bütünlük kırmızı).
      ASİMETRİ BEYANI: karşı-olgusal yalnız sinyal DOĞDUĞUNDA taranır (None dönen taramada
      taranmaz — 251×1147 çift tarama koşum süresini ikiler). Terimin SİLDİĞİ sinyaller bu
      telemetride görünmez; onlar birincil ölçümün kendisinde, C-taban işlem kıyasında görünür.

TANIMLAR (ölçümden ÖNCE donduruldu; sonuç görüldükten sonra değişmez):
  islem            = kapanmış işlem satırı (broker.closed; eod/delisted markout DAHİL) — şasi tanımı.
  ay anahtarı      = işlem için ts_open[:7] (giriş ayı); ay evreni = seans takviminin ayları.
  ΔnetP&L CI       = ay-kümeli EŞLENİK bootstrap: aylık pnl_dollars toplamları (ts_open ayına
                     atanır), aynı ay çekilişi iki koşuma birden (yerine-koymalı, 5000 iter,
                     seed 20260812); fark = HÜCRE − C; %95 CI = [p2.5, p97.5].
  Δsharpe CI       = AY-GETİRİLİ sharpe farkı, eşlenik: seans eq_open serisinden (OPEN fazı,
                     fill'den önce — iki tarafta da AYNI alan) günlük oran → ay içinde bileşik
                     aylık getiri; sharpe_ay = mean/std(ddof=1)×√12; çekilen ay kümesi üzerinde
                     iki koşum için yeniden hesap, fark = HÜCRE − C. std=0 ya da <2 ay → o
                     iterasyon atlanır ve SAYISI raporlanır. NOKTA değerler ayrıca raporlanır:
                     motor-kanonik score_detail.sharpe (CI'sız) + sharpe_ay nokta.
  Δişlem n CI      = şasi kiyas tanımı AYNEN (aylık işlem sayıları, eşlenik; oran CI'da tB=0
                     iterasyonu atlanır ve sayılır).
  max-dd           = motor-kanonik score_detail.max_drawdown + yalnız-M2M; NOKTA kıyas (kart CI
                     istemez).
  seçilim farkı    = işlem anahtarı (ticker, ts_open[:10]). yalnız_C / yalnız_hücre / ortak.
                     R profili = {n, ort_r, medyan_r, win_rate, toplam_r, toplam_pnl, setup dağ.}.
                     Ortak işlemlerde çıkış farkı sayısı + Δr/Δpnl betimi (boyutlama conviction
                     üzerinden skora bağlı olduğundan ortak işlemde de pnl kayar — beyan).
                     MEKANİZMA SONDASI: plan günü = ts_open'dan önceki seans (replay'de silahlı
                     plan tam BİR açılış yaşar — backtest.py `armed=[]` open-fazı sonunda).
                     yalnız_C işlemi için hücrenin aynı (plan-günü,sembol) kaydına bakılır:
                     pozisyon-açıktı (tarama atlandı) / sinyal-yok (w terimi kapıda) / plan-var
                     (verdict + dolum). yalnız_hücre için hücrenin w0 karşı-olgusalı okunur.
                     C'nin kendi sinyal/plan defteri 026 çıktısında SAKLANMADI → C tarafı bu
                     sondada ölçülemedi = None + bu neden (UYDURMA YASAĞI).
  payda sayacı     = (a) SİNYAL düzeyi: breakout_vcp sinyalleri içinde turnover21≠None payı
                     (kablo yalnız orada yaşar — kapsam beyanı yukarıda);
                     (b) İŞLEM düzeyi: breakout_vcp işlemleri (plan eşlemesiyle) içinde payı;
                     (c) SEMBOL düzeyi: evren sembolleri içinde EDGAR kapsamı (okuma_raporu
                     kapsam_disi_sembol ∩ evren üzerinden);
                     (d) ÇAĞRI düzeyi: adapters.edgar_shares.okuma_raporu() — TELEMETRİ
                     (ön-uçuş + karşı-olgusal çift-çağrıları da sayar; kill bunun üstünden
                     HESAPLANMAZ, beyanlı).
  edgar kaynağı    = research/edgar_facts/shares_outstanding.csv.gz (config.ROOT altından SALT-
                     OKUNUR; modülde ağ yolu YOK — adapters.edgar_shares yalnız dosya okur).

KILL KONTROLLERİ (kart, DONUK — koşul değerinin kaydı, hüküm DEĞİL):
  kill#1 (kart): turnover-kaynak payda %50'nin altındaysa → olculemedi.
                 İşletim: hücrede (a) sinyal-düzeyi payı < 0.50 VEYA (b) işlem-düzeyi payı < 0.50.
  kill#2 (kart): şasi bütünlüğü bozuksa geçersiz.
                 İşletim: şasi çivileri (frame_miss=0, dup=0, scan==plan, yasak modül yok,
                 base_max_open==20) + motor/config sha'ları C ile birebir + takvim C ile birebir
                 + enjeksiyon çivileri + öz-sınama (skor-değişim kanıtı ≥1, FAIL-OPEN ihlali 0,
                 karşı-olgusal tarama hatası 0).

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen = None + neden); YASA-4 (sessiz-yutma işaretli + gerekçe);
YASA-6 (okuyucu: sonuc_w*.json + seanslar_w* + islemler_w* + sinyaller_w* + planlar_w* → `kiyas`
tüketir; sonuc.json → dönüş raporu + Rol-1). SALT-OKUMA: config.STATE koşum-başına izole sandbox;
barlar sembolik bağla SALT-OKUNUR; canlı state'e ve motor dosyalarına tek bayt yazılmaz.
meridian.loop / counterfactual / cf_backfill / hermes İTHAL EDİLMEZ — sys.modules ile KANITLANIR.

KULLANIM:
  olcum.py w005            # hücre w=0.05 → sonuc_w005.json + seanslar/islemler/sinyaller/planlar
  olcum.py w010            # hücre w=0.10 → sonuc_w010.json + ...
  olcum.py kiyas           # iki hücre (yerel) + C (EDG-026 hazır çıktıları) → sonuc.json
  (--smoke: kısa pencere 2022-01-01→2022-06-30, çıktılar smoke/ altına — şasi provası;
   smoke'ta skor-değişim çivisi ZORUNLU DEĞİL — sinyal örneklemi küçük, bayrak yine raporlanır)
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
REPLAY_END = "2026-07-30"                      # kart: C-şasi ile AYNI pencere
BOOT_SEED = 20260812
BOOT_ITER = 5000

# şasi C-dünyası DONUK parametreleri (EDG-026 AYNEN — bu kart bunlara DOKUNMAZ)
RAMPA = {"tam_dd": 0.15, "sifir_dd": 0.36}     # monkeypatch (beyan başlıkta)
SLOT = 20                                      # goal/limits enjeksiyonu (ENJ-1)
BOYUT_R = 0.5                                  # strateji params enjeksiyonu (ENJ-2)

# EDG-031 hücreleri (kart parameter_grid, DONUK)
KEY = "entry.w_turnover"
HUCRELER = {"w005": 0.05, "w010": 0.10}
PAYDA_KILL_ESIK = 0.50                         # kart kill#1: %50
ONUCUS_SEMBOLLER = ("AAPL", "MSFT", "NVDA", "AMZN")   # ön-uçuş payda kanıtı adayları

KART3 = ["tavan_sifir", "evren_bagladi", "derisk_bagladi"]
YASAK = ("meridian.loop", "meridian.counterfactual", "meridian.cf_backfill", "meridian.hermes")

# NO_GO/REVIEW neden eşlemesi (şasi AYNEN; eşleşmeyen HAM dizgiyle sayılır — YASA-4)
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
# SANDBOX HAZIRLIĞI — izole state (EDG-022'nin DONMUŞ config kopyaları; şasi AYNEN)
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
            # kaynak = EDG-022'nin DONMUŞ kopyaları (şasi çivisi — C de aynı kaynaktan koştu).
            # DOSYALAR DEĞİŞTİRİLMEZ: tüm enjeksiyonlar YÜKLENMİŞ sözlüklere yapılır ki config
            # sha'ları C ile bayt-aynı kalsın ve şasi kimliği sha ile kanıtlansın.
            shutil.copyfile(EDG022 / "state" / f, dst)
    return st


# ---------------------------------------------------------------------------------------------
# RAMPA — orijinal formülün birebir parametrize kopyası (şasi AYNEN)
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
# SINIFLAMA + bootstrap + ısı yardımcıları (şasi AYNEN)
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
# R PROFİLİ — seçilim-farkı betiminin ortak özeti (tanım başlıkta, DONUK)
# ---------------------------------------------------------------------------------------------
def _r_profili(islemler: list[dict]) -> dict | None:
    import numpy as np
    if not islemler:
        return None
    r = np.asarray([float(t.get("r_multiple") or 0.0) for t in islemler])
    pnl = np.asarray([float(t.get("pnl_dollars") or 0.0) for t in islemler])
    setup: dict[str, int] = {}
    for t in islemler:
        setup[str(t.get("setup"))] = setup.get(str(t.get("setup")), 0) + 1
    exit_d: dict[str, int] = {}
    for t in islemler:
        exit_d[str(t.get("exit_reason"))] = exit_d.get(str(t.get("exit_reason")), 0) + 1
    return {"n": int(len(r)),
            "ort_r": round(float(r.mean()), 4), "medyan_r": round(float(np.median(r)), 4),
            "win_rate": round(float((r > 0).mean()), 4),
            "toplam_r": round(float(r.sum()), 3), "toplam_pnl": round(float(pnl.sum()), 2),
            "setup_dagilim": dict(sorted(setup.items(), key=lambda kv: -kv[1])),
            "exit_dagilim": dict(sorted(exit_d.items(), key=lambda kv: -kv[1]))}


# ---------------------------------------------------------------------------------------------
# HÜCRE KOŞUMU (w005 | w010) — şasi kosum() + ENJ-3 + öz-sınama + payda sayaçları
# ---------------------------------------------------------------------------------------------
def kosum(run_adi: str, smoke: bool = False):
    W = HUCRELER[run_adi]
    outdir = (SANDBOX / "smoke") if smoke else SANDBOX
    outdir.mkdir(exist_ok=True)
    r_start, r_end = (REPLAY_START, "2022-06-30") if smoke else (REPLAY_START, REPLAY_END)

    st_dir = hazirla(run_adi + ("_smoke" if smoke else ""))
    sys.path.insert(0, str(REPO))

    from meridian import config
    # SALT-OKUMA İZOLASYONU: her yazım (obs.events, history) sandbox'a düşer, canlı state'e DEĞİL
    config.STATE = st_dir
    config.BARS = st_dir / "bars"
    config.HISTORY = st_dir / "history"

    import numpy as np                     # noqa: F401
    import pandas as pd
    import yaml
    from meridian import backtest, dataset, score as score_mod
    from meridian.adapters import edgar_shares as es_mod

    # motorun yamalanmadığını çivile + YASAKLI modül kanıtı (ithal ÖNCESİ)
    assert not hasattr(backtest, "wpg_overlay_day"), "motor YAMALI görünüyor — ölçüm geçersiz"
    assert not [m for m in sys.modules if m in YASAK], "yasaklı modül ithal edilmiş"

    brk = backtest.brk                     # meridian.broker modülü
    strat = backtest.strat                 # meridian.strategy modülü
    ORIJ_DERISK = brk.derisk_mult

    # ---- rampa kurulumu + öz-sınama (şasi AYNEN) ---------------------------------------------
    brk.derisk_mult = _rampa_fn(RAMPA["tam_dd"], RAMPA["sifir_dd"])
    assert brk.derisk_mult is not ORIJ_DERISK
    assert brk.derisk_mult(90.0, 100.0) == 1.0
    assert abs(brk.derisk_mult(80.0, 100.0) - 0.7619) < 1e-9
    assert brk.derisk_mult(64.0, 100.0) == 0.0
    assert brk.max_positions_at(80.0, 100.0, 5) == 4
    assert brk.max_positions_at(80.0, 100.0, 20) == 15

    # ---- girdiler + PARAM-ENJEKSİYONLARI (dosya DEĞİŞMEZ; sözlükler değişir) -----------------
    stg = yaml.safe_load((st_dir / "strategy.yaml").read_text())
    params = dict(stg["params"])
    by_regime = stg.get("params_by_regime") or None
    sv = int(stg.get("version"))
    goal = config.goal()                                   # derin kopya — dosyaya/önbelleğe sızmaz

    onceki = {"max_open_positions": int(goal["limits"]["max_open_positions"]),
              "position_size_r": float(params["position_size_r"]),
              KEY: params.get(KEY)}                        # beklenen: None (anahtar hiç yoktu)
    goal["limits"]["max_open_positions"] = SLOT            # ENJ-1 (şasi)
    params["position_size_r"] = BOYUT_R                    # ENJ-2 (şasi)
    params[KEY] = W                                        # ENJ-3 (EDG-031 — bu kartın değişkeni)

    # enjeksiyon öz-sınaması: rejim çözümü DÖRT rejimde de W görmeli (şasi deseni AYNEN + ENJ-3)
    for _rg in ("trend_up", "trend_down", "chop", "high_vol"):
        _eff = config.resolve_params(params, by_regime, _rg)
        assert float(_eff["position_size_r"]) == BOYUT_R, f"rejim override sızıntısı: {_rg}"
        assert float(_eff[KEY]) == W, f"w_turnover rejim çözümünde kayboldu: {_rg}"
        _ov = (by_regime or {}).get(_rg) or {}
        assert "position_size_r" not in _ov, f"params_by_regime[{_rg}] position_size_r içeriyor"
        assert KEY not in _ov, f"params_by_regime[{_rg}] {KEY} içeriyor — tek-nokta enjeksiyonu yetersiz"
    assert float(goal["limits"]["max_position_r"]) >= BOYUT_R
    # bounds çivisi (bilgi + doğrulama): kartın dayandığı arama-uzayı satırı gerçekten var ve W ızgarada
    _bounds = yaml.safe_load((st_dir / "bounds.yaml").read_text())
    _bk = _bounds.get(KEY) if isinstance(_bounds, dict) else None
    assert _bk is not None, f"bounds.yaml'da {KEY} satırı yok — kartın evidence_refs'i doğrulanamadı"
    assert float(_bk["min"]) <= W <= float(_bk["max"]), f"W={W} bounds aralığı dışında"
    limits = goal["limits"]
    max_open = int(limits["max_open_positions"])
    no_trade_before = int(limits.get("no_trade_before_bars", 0))
    assert max_open == SLOT

    # ---- veri + ÖN-UÇUŞ PAYDA KANITI (öz-sınama katman-1; replay'den ÖNCE) -------------------
    t0 = dt.datetime.now()
    bars, index = dataset.load_cached()

    onucus = {"sembol": None, "tarih": None, "turnover21": None, "turnover_score": None,
              "neden": None, "gecerli": False}
    for _sym in ONUCUS_SEMBOLLER:
        if _sym not in bars:
            continue
        _pf = backtest._indexed({_sym: bars[_sym]})[_sym]
        _uygun = _pf.index[_pf.index <= pd.Timestamp("2024-06-28")]
        if not len(_uygun):
            continue
        _d0 = _uygun[-1]
        _sub0 = _pf.loc[:_d0].reset_index().tail(340)
        assert "date" in _sub0.columns, "backtest alt-çerçevesinde 'date' sütunu yok — payda kablosu kör"
        _v, _neden = strat._turnover_now(_sub0, _sym)
        onucus.update({"sembol": _sym, "tarih": str(_d0)[:10], "neden": _neden or None})
        if _v is not None:
            _ts = strat.turnover_score(_v)
            onucus.update({"turnover21": round(float(_v), 8),
                           "turnover_score": (None if _ts is None else round(float(_ts), 3)),
                           "gecerli": (_ts is not None and 1.0 <= float(_ts) <= 99.0)})
            break
    assert onucus["gecerli"], f"ÖN-UÇUŞ BAŞARISIZ — payda kablosu ölçülebilir değer vermedi: {onucus}"

    # ---- kancalar (şasi deseni AYNEN; scan kancasına EDG-031 karşı-olgusal telemetri eklendi) -
    seans_by_date: dict[str, dict] = {}
    _cur_close_date = [None]
    _dup: list[str] = []
    _frame_miss = [0]

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
            _frame_miss[0] += 1                # sessiz-yutma DEĞİL: sayılır, geçerliliği bozar
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

    # EDG-031 telemetri kapları
    sinyal_kayitlari: list[dict] = []
    _cf_hata: list[dict] = []              # karşı-olgusal tarama istisnaları (YASA-4: işaretli)
    _enj_scan_gordu = [0]                  # scan yüzeyinde KEY==W kaç kez doğrulandı
    _enj_scan_bozuk = [0]                  # scan yüzeyinde KEY!=W görülme sayısı (0 olmalı)

    def _scan(*a, **kw):
        rec = seans_by_date.get(_cur_close_date[0])
        if rec is not None:
            rec["n_scan_cagri"] += 1
        sig = _orig_scan(*a, **kw)
        if sig and rec is not None:
            rec["n_sinyal"] += 1
            # ---- EDG-031: w=0 KARŞI-OLGUSAL taraması (yalnız sinyal doğduğunda — beyan başlıkta)
            p_eff = a[1] if len(a) > 1 else kw.get("params")
            if isinstance(p_eff, dict):
                if p_eff.get(KEY) == W:
                    _enj_scan_gordu[0] += 1
                else:
                    _enj_scan_bozuk[0] += 1
                try:
                    p_w0 = dict(p_eff)
                    p_w0[KEY] = 0.0
                    sig0 = _orig_scan(a[0], p_w0, *a[2:], **kw)
                except Exception as e:  # işaretli-yutma: hata sayılır ve bütünlüğü KIRMIZI yapar (YASA-4)
                    sig0 = None
                    _cf_hata.append({"date": rec["date"], "ticker": getattr(sig, "ticker", "?"),
                                     "hata": f"{type(e).__name__}: {e}"})
            else:
                sig0 = None
                _cf_hata.append({"date": rec["date"], "ticker": getattr(sig, "ticker", "?"),
                                 "hata": "params argümanı sözlük değil — karşı-olgusal taranamadı"})
            _tsc = (None if sig.turnover21 is None else strat.turnover_score(sig.turnover21))
            sinyal_kayitlari.append({
                "date": rec["date"], "ticker": sig.ticker, "setup": sig.setup,
                "score": int(sig.score),
                "turnover21": (None if sig.turnover21 is None else round(float(sig.turnover21), 8)),
                "turnover_score": (None if _tsc is None else round(float(_tsc), 3)),
                "size_r": float(sig.size_r),
                "w0_var": bool(sig0),
                "w0_setup": (sig0.setup if sig0 else None),
                "w0_score": (int(sig0.score) if sig0 else None),
                "w0_size_r": (float(sig0.size_r) if sig0 else None),
            })
        return sig

    brk.max_positions_at = _maxpos
    backtest.regime_mod.build_regime_json = _regime
    backtest.strat.scan_entry = _scan

    res = backtest.replay(params, bars, index, goal, r_start, r_end,
                          strategy_version=sv, params_by_regime=by_regime, with_gate_detail=False)
    sure = round((dt.datetime.now() - t0).total_seconds(), 1)

    yasak_yuklu = [m for m in sys.modules if m in YASAK]
    payda_raporu = es_mod.okuma_raporu()   # ÇAĞRI düzeyi telemetri (beyan: çift-çağrılar dahil)

    # ---- plan_log çapraz-kontrolü + NO_GO/REVIEW neden dağılımı (şasi AYNEN) -----------------
    plan_aday: dict[str, int] = {}
    plan_silahli: dict[str, int] = {}
    nogo_nedenler: list[str] = []
    review_nedenler: list[str] = []
    verdict_n = {"GO": 0, "REVIEW": 0, "NO_GO": 0}
    silahli_size_r: list[float] = []
    planlar_slim: list[dict] = []          # EDG-031: mekanizma sondası için slim plan defteri
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
        planlar_slim.append({"date": dts, "ticker": p.get("ticker"), "setup": p.get("setup"),
                             "score": p.get("score"), "size_r": p.get("size_r"),
                             "verdict": v})

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

    # ---- EDG-031 ÖZ-SINAMA DEĞERLENDİRMESİ (katman-2: tarama-içi karşı-olgusal) --------------
    ayni_setup = [k for k in sinyal_kayitlari if k["w0_var"] and k["w0_setup"] == k["setup"]]
    bv_olculdu = [k for k in ayni_setup
                  if k["setup"] == "breakout_vcp" and k["turnover21"] is not None]
    skor_degisen = [k for k in bv_olculdu if k["score"] != k["w0_score"]]
    # FAIL-OPEN çivisi (replay-içi): turnover ölçülemeyen breakout + breakout-dışı aynı-setup
    # sinyallerde skor w0 ile BİREBİR aynı olmalı
    failopen_kume = [k for k in ayni_setup
                     if not (k["setup"] == "breakout_vcp" and k["turnover21"] is not None)]
    failopen_ihlal = [k for k in failopen_kume if k["score"] != k["w0_score"]]
    setup_degisen = [k for k in sinyal_kayitlari if k["w0_var"] and k["w0_setup"] != k["setup"]]
    w0_yok = [k for k in sinyal_kayitlari if not k["w0_var"]]     # terimin DOĞURDUĞU sinyaller
    skor_fark = [k["score"] - k["w0_score"] for k in bv_olculdu]
    oz_sinama = {
        "n_sinyal": len(sinyal_kayitlari),
        "n_ayni_setup": len(ayni_setup),
        "n_bv_turnover_olculdu": len(bv_olculdu),
        "n_skor_degisti": len(skor_degisen),
        "skor_degisti_pct": (round(100.0 * len(skor_degisen) / len(bv_olculdu), 2)
                             if bv_olculdu else None),
        "skor_fark_dagilim": (None if not skor_fark else {
            "min": int(min(skor_fark)), "max": int(max(skor_fark)),
            "ort": round(sum(skor_fark) / len(skor_fark), 3),
            "pozitif_n": sum(1 for x in skor_fark if x > 0),
            "negatif_n": sum(1 for x in skor_fark if x < 0),
            "sifir_n": sum(1 for x in skor_fark if x == 0)}),
        "n_failopen_kume": len(failopen_kume),
        "n_failopen_ihlal": len(failopen_ihlal),
        "failopen_ihlal_ornek": failopen_ihlal[:5],
        "n_setup_degisen": len(setup_degisen),
        "n_w0_sinyal_yok": len(w0_yok),          # w=0 dünyasında hiç doğmayacak sinyaller
        "cf_hata_n": len(_cf_hata), "cf_hata_ornek": _cf_hata[:5],
        "enj_scan_gordu_n": _enj_scan_gordu[0], "enj_scan_bozuk_n": _enj_scan_bozuk[0],
        "skor_degisim_kaniti": (len(skor_degisen) >= 1),
        "beyan": ("karşı-olgusal yalnız sinyal doğduğunda taranır; terimin SİLDİĞİ sinyaller bu "
                  "telemetride değil C-taban işlem kıyasında görünür (asimetri beyanı başlıkta)"),
    }
    # skor-değişim çivisi: tam koşumda ZORUNLU (smoke'ta yalnız bayrak — örneklem küçük)
    if not smoke:
        assert oz_sinama["skor_degisim_kaniti"], \
            "ÖZ-SINAMA BAŞARISIZ: hiçbir ölçülü breakout sinyalinde skor w0'dan sapmadı — enjeksiyon İNERT"
    assert not failopen_ihlal, f"FAIL-OPEN İHLALİ (replay-içi): {failopen_ihlal[:3]}"

    # ---- işlem → sinyal eşlemesi (plan_id = P-YYYY-MM-DD-TICKER) + payda sayaçları -----------
    trades = res.trades or []
    sinyal_ix = {(k["date"], k["ticker"]): k for k in sinyal_kayitlari}
    islem_eslesme_yok = 0
    for t in trades:
        pid = str(t.get("plan_id") or "")
        k = None
        if pid.startswith("P-") and len(pid) > 13:
            k = sinyal_ix.get((pid[2:12], pid[13:]))
        if k is None:
            islem_eslesme_yok += 1
        t["_edg031_plan_date"] = (pid[2:12] if pid.startswith("P-") and len(pid) > 13 else None)
        t["_edg031_turnover21"] = (k or {}).get("turnover21")
        t["_edg031_turnover_score"] = (k or {}).get("turnover_score")
        t["_edg031_w0_var"] = (k or {}).get("w0_var")
        t["_edg031_w0_setup"] = (k or {}).get("w0_setup")
        t["_edg031_w0_score"] = (k or {}).get("w0_score")

    bv_sinyal = [k for k in sinyal_kayitlari if k["setup"] == "breakout_vcp"]
    bv_islem = [t for t in trades if str(t.get("setup")) == "breakout_vcp"]
    evren = sorted(bars.keys())
    kapsam_disi_evren = sorted(set(payda_raporu.get("kapsam_disi_sembol") or []) & set(evren))
    payda = {
        "sinyal_bv": {"n": len(bv_sinyal),
                      "olculdu_n": sum(1 for k in bv_sinyal if k["turnover21"] is not None),
                      "pay": (round(sum(1 for k in bv_sinyal if k["turnover21"] is not None)
                                    / len(bv_sinyal), 4) if bv_sinyal else None)},
        "islem_bv": {"n": len(bv_islem),
                     "olculdu_n": sum(1 for t in bv_islem if t["_edg031_turnover21"] is not None),
                     "pay": (round(sum(1 for t in bv_islem if t["_edg031_turnover21"] is not None)
                                   / len(bv_islem), 4) if bv_islem else None),
                     "eslesme_yok_n_tum_islem": islem_eslesme_yok},
        "sembol": {"evren_n": len(evren),
                   "kapsam_disi_gorulen": kapsam_disi_evren,
                   "kapsam_disi_n": len(kapsam_disi_evren),
                   "beyan": ("kapsam_disi yalnız TARANAN sembollerde birikir (tembel seri kurulumu) "
                             "— evren-genelinde mutlak kapsam sayısı değil, koşumda GÖRÜLEN "
                             "kapsam-dışılıktır")},
        "cagri_okuma_raporu": {**payda_raporu,
                               "beyan_ek": ("ön-uçuş + karşı-olgusal çift-çağrılar dahil — kill "
                                            "bunun üstünden hesaplanmaz (tanım başlıkta)")},
    }

    # ---- işlem/doluluk/ısı/performans metrikleri (şasi AYNEN) --------------------------------
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
        "formul": f"nominal = n_eszamanli × {BOYUT_R}R (şasi formülü; conviction 0.6-1.0× nedeniyle ÜST SINIR)",
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
                        and not yasak_yuklu and not base_max_bozuk
                        and not _cf_hata and not failopen_ihlal
                        and _enj_scan_bozuk[0] == 0
                        and (smoke or oz_sinama["skor_degisim_kaniti"]))

    out = {
        "kart": "EDG-2026-031", "kosum": run_adi, "w_turnover": W, "smoke": smoke,
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sure_sn": sure,
        "sasi": "EDG-026 C-dünyası (rampa 15/36 + slot20 + 0.5R) — beyan modül başlığında",
        "rampa": {"tam_dd": RAMPA["tam_dd"], "sifir_dd": RAMPA["sifir_dd"],
                  "enjeksiyon": ("MONKEYPATCH — ölçüm modülü içinde broker.derisk_mult "
                                 "modül-özniteliği değiştirildi; motor DOSYASI değişmedi "
                                 "(EDG-026 şasi deseni AYNEN — beyan modül başlığında)")},
        "param_enjeksiyon": {
            "max_open_positions": {"once": onceki["max_open_positions"], "sonra": SLOT,
                                   "yuzey": "goal['limits'] (şasi ENJ-1)"},
            "position_size_r": {"once": onceki["position_size_r"], "sonra": BOYUT_R,
                                "yuzey": "strateji params sözlüğü (şasi ENJ-2)"},
            KEY: {"once": onceki[KEY], "sonra": W,
                  "yuzey": ("strateji params sözlüğü DÜZ anahtar — strategy.py:477 "
                            "_f(params,'entry.w_turnover',0.0); resolve_params 4 rejimde kanıtlı; "
                            "bounds satırı doğrulandı (EDG-031 ENJ-3)")},
            "zarf_sabit": ("heat_hard_r=5.0R, heat_review_r=3.5R, max_position_r=1.0, "
                           "max_sector_exposure_pct=40 DEĞİŞMEDİ; bu kart yalnız w_turnover "
                           "değiştirir, şasi enjeksiyonları C ile AYNI"),
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
            "yasakli_modul_yuklendi": yasak_yuklu,
            "base_max_open_bozuk": base_max_bozuk[:10],
            "cf_hata_n": len(_cf_hata),
            "failopen_ihlal_n": len(failopen_ihlal),
            "enj_scan_bozuk_n": _enj_scan_bozuk[0],
            "gecerli": butunluk_gecerli,
        },
        "onucus_payda_kaniti": onucus,
        "oz_sinama": oz_sinama,
        "payda_sayaci": payda,
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
            "setup_dagilim": {s: sum(1 for t in trades if str(t.get("setup")) == s)
                              for s in sorted({str(t.get("setup")) for t in trades})},
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
    (outdir / f"sonuc_{run_adi}{ek}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str))
    (outdir / f"seanslar_{run_adi}{ek}.json").write_text(
        json.dumps(sess, ensure_ascii=False, default=str))
    slim = [{**{k: t.get(k) for k in ("ts_open", "ts_close", "ticker", "r_multiple",
                                      "pnl_dollars", "exit_reason", "bars_held", "regime",
                                      "setup", "qty", "risk_dollars", "size_r")},
             "plan_id": t.get("plan_id"), "score": t.get("score"),
             "plan_date": t.get("_edg031_plan_date"),
             "turnover21": t.get("_edg031_turnover21"),
             "turnover_score": t.get("_edg031_turnover_score"),
             "w0_var": t.get("_edg031_w0_var"), "w0_setup": t.get("_edg031_w0_setup"),
             "w0_score": t.get("_edg031_w0_score")} for t in trades]
    (outdir / f"islemler_{run_adi}{ek}.json").write_text(
        json.dumps(slim, ensure_ascii=False, default=str))
    (outdir / f"sinyaller_{run_adi}{ek}.json").write_text(
        json.dumps(sinyal_kayitlari, ensure_ascii=False, default=str))
    (outdir / f"planlar_{run_adi}{ek}.json").write_text(
        json.dumps(planlar_slim, ensure_ascii=False, default=str))

    print(f"\n=========== EDG-031 KOŞUM [{run_adi}{ek}] w_turnover={W} ===========")
    print(f"replay {r_start}→{r_end}  sv={sv}  sembol={len(bars)}  süre={sure}s")
    print(f"enjeksiyon: max_open {onceki['max_open_positions']}→{max_open}  "
          f"size_r {onceki['position_size_r']}→{params['position_size_r']}  "
          f"{KEY} {onceki[KEY]}→{params[KEY]}")
    print(f"ön-uçuş: {onucus['sembol']}@{onucus['tarih']} turnover={onucus['turnover21']} "
          f"puan={onucus['turnover_score']}")
    print(f"öz-sınama: bv-ölçülü={oz_sinama['n_bv_turnover_olculdu']} "
          f"skor-değişen={oz_sinama['n_skor_degisti']} (%{oz_sinama['skor_degisti_pct']})  "
          f"failopen-ihlal={oz_sinama['n_failopen_ihlal']}  setup-değişen={oz_sinama['n_setup_degisen']}  "
          f"w0-yok={oz_sinama['n_w0_sinyal_yok']}  cf-hata={oz_sinama['cf_hata_n']}")
    print(f"payda: sinyal-bv {payda['sinyal_bv']['olculdu_n']}/{payda['sinyal_bv']['n']} "
          f"(pay={payda['sinyal_bv']['pay']})  işlem-bv {payda['islem_bv']['olculdu_n']}/"
          f"{payda['islem_bv']['n']} (pay={payda['islem_bv']['pay']})")
    print(f"bütünlük geçerli={out['butunluk']['gecerli']}  frame_miss={_frame_miss[0]} "
          f"dup={len(_dup)} scan!=plan={len(scan_vs_plan)} yasak={yasak_yuklu} "
          f"base_max_bozuk={len(base_max_bozuk)}")
    print(f"işlem n={n_islem} ({out['islem']['islem_yil']}/yıl)  net_pnl={net_pnl_equity}  "
          f"maxdd_kanonik={detail.get('max_drawdown')}  sharpe={detail.get('sharpe')}  "
          f"avg_r={detail.get('avg_r')}")
    print(f"NO_GO nedenleri: {out['islem']['nogo_neden_dagilim']}")
    print(f"yazıldı: {outdir}/sonuc_{run_adi}{ek}.json")


# ---------------------------------------------------------------------------------------------
# KIYAS — hücreler (yerel) ↔ C (EDG-026 HAZIR çıktıları; YENİDEN KOŞULMAZ) → sonuc.json
# ---------------------------------------------------------------------------------------------
def _aylik_pnl(islemler: list[dict], aylar: list[str]):
    import numpy as np
    c = {a: 0.0 for a in aylar}
    for t in islemler:
        a = str(t["ts_open"])[:7]
        if a in c:
            c[a] += float(t.get("pnl_dollars") or 0.0)
    return np.array([c[a] for a in aylar], dtype=float)


def _aylik_islem(islemler: list[dict], aylar: list[str]):
    import numpy as np
    c = {a: 0 for a in aylar}
    for t in islemler:
        a = str(t["ts_open"])[:7]
        if a in c:
            c[a] += 1
    return np.array([c[a] for a in aylar], dtype=float)


def _aylik_getiri(seanslar: list[dict], aylar: list[str]):
    """eq_open serisinden aylık BİLEŞİK getiri (tanım başlıkta, DONUK). Getirisiz ay NaN."""
    import numpy as np
    acc = {a: None for a in aylar}
    prev = None
    for s in seanslar:
        eq = float(s["eq_open"])
        if prev is not None and prev > 0:
            r = eq / prev - 1.0
            a = s["date"][:7]
            if a in acc:
                acc[a] = (1.0 + (acc[a] if acc[a] is not None else 0.0)) * (1.0 + r) - 1.0
        prev = eq
    return np.array([np.nan if acc[a] is None else acc[a] for a in aylar], dtype=float)


def _sharpe_ay(vals) -> float | None:
    """Aylık getiri vektöründen sharpe (mean/std(ddof=1)×√12). std=0 ya da n<2 → None."""
    import numpy as np
    v = np.asarray(vals, dtype=float)
    v = v[~np.isnan(v)]
    if len(v) < 2:
        return None
    sd = float(np.std(v, ddof=1))
    if sd <= 0:
        return None
    return float(np.mean(v) / sd * (12.0 ** 0.5))


def kiyas(smoke: bool = False):
    import numpy as np
    ek = "_smoke" if smoke else ""
    cdir = (EDG026 / "smoke") if smoke else EDG026
    ldir = (SANDBOX / "smoke") if smoke else SANDBOX

    C = {"sonuc": json.loads((cdir / f"sonuc_c{ek}.json").read_text()),
         "seans": json.loads((cdir / f"seanslar_c{ek}.json").read_text()),
         "islem": json.loads((cdir / f"islemler_c{ek}.json").read_text())}
    sc = C["sonuc"]
    c_dosya_sha = {f: _sha(cdir / f"{f}_c{ek}.json") for f in ("sonuc", "seanslar", "islemler")}

    tarih_c = [s["date"] for s in C["seans"]]
    aylar = sorted({d[:7] for d in tarih_c})
    M = len(aylar)
    perf_c = sc["performans"]
    cC_islem = _aylik_islem(C["islem"], aylar)
    cC_pnl = _aylik_pnl(C["islem"], aylar)
    cC_ret = _aylik_getiri(C["seans"], aylar)
    c_islem_ix = {(t["ticker"], str(t["ts_open"])[:10]): t for t in C["islem"]}
    takvim_ix = {d: i for i, d in enumerate(tarih_c)}

    def ci95(arr):
        a = np.asarray([x for x in arr if x == x])
        if not len(a):
            return None                                       # ölçülemedi
        return {"lo": round(float(np.percentile(a, 2.5)), 3),
                "hi": round(float(np.percentile(a, 97.5)), 3),
                "orta": round(float(np.median(a)), 3)}

    hucre_bloklari = {}
    for run_adi in HUCRELER:
        H = {"sonuc": json.loads((ldir / f"sonuc_{run_adi}{ek}.json").read_text()),
             "seans": json.loads((ldir / f"seanslar_{run_adi}{ek}.json").read_text()),
             "islem": json.loads((ldir / f"islemler_{run_adi}{ek}.json").read_text()),
             "sinyal": json.loads((ldir / f"sinyaller_{run_adi}{ek}.json").read_text()),
             "plan": json.loads((ldir / f"planlar_{run_adi}{ek}.json").read_text())}
        sh = H["sonuc"]

        # ---- şasi kimliği: motor/config sha'ları C ile birebir mi? (değilse ŞERHLİ) ----------
        motor_ayni = {f: (sh["motor_sha256_16"].get(f) == sc["motor_sha256_16"].get(f)
                          and sh["motor_sha256_16"].get(f) is not None)
                      for f in ("broker.py", "backtest.py", "strategy.py")}
        config_ayni = {f: (sh["config_sha256_16"][f]["sandbox"] == sc["config_sha256_16"][f]["sandbox"]
                           and sh["config_sha256_16"][f]["sandbox"] is not None)
                       for f in ("goal.yaml", "strategy.yaml", "bounds.yaml")}
        rampa_ayni = (sh["rampa"]["tam_dd"] == sc["rampa"]["tam_dd"] == 0.15
                      and sh["rampa"]["sifir_dd"] == sc["rampa"]["sifir_dd"] == 0.36)
        tarih_h = [s["date"] for s in H["seans"]]
        takvim_ayni = (tarih_h == tarih_c)
        serh = None
        if not all(motor_ayni.values()) or not all(config_ayni.values()) or not takvim_ayni:
            serh = ("MOTOR/CONFIG SHA'LARI ya da TAKVİM C İLE BİREBİR DEĞİL — kıyas ŞERHLİDİR "
                    f"(kart universe koşulu): motor={motor_ayni} config={config_ayni} "
                    f"takvim={takvim_ayni}")

        # ---- eşlenik ay-kümeli bootstrap: Δişlem, ΔnetP&L, Δsharpe(aylık) — TEK çekiliş ------
        cH_islem = _aylik_islem(H["islem"], aylar)
        cH_pnl = _aylik_pnl(H["islem"], aylar)
        cH_ret = _aylik_getiri(H["seans"], aylar)
        rng = np.random.default_rng(BOOT_SEED)      # hücre başına AYNI tohum → hücreler arası da eşlenik
        f_islem = np.empty(BOOT_ITER)
        f_pnl = np.empty(BOOT_ITER)
        f_sharpe = np.full(BOOT_ITER, np.nan)
        oran = []
        sharpe_atlanan = 0
        idx_all = np.arange(M)
        for i in range(BOOT_ITER):
            pick = rng.choice(idx_all, size=M, replace=True)   # EŞLENİK: aynı çekiliş iki koşuma
            tC, tH = float(cC_islem[pick].sum()), float(cH_islem[pick].sum())
            f_islem[i] = tH - tC
            if tC > 0:
                oran.append(tH / tC)
            f_pnl[i] = float(cH_pnl[pick].sum()) - float(cC_pnl[pick].sum())
            s_c, s_h = _sharpe_ay(cC_ret[pick]), _sharpe_ay(cH_ret[pick])
            if s_c is None or s_h is None:
                sharpe_atlanan += 1
            else:
                f_sharpe[i] = s_h - s_c

        nC, nH = int(cC_islem.sum()), int(cH_islem.sum())
        perf_h = sh["performans"]
        sharpe_ay_nokta = {"C": _sharpe_ay(cC_ret), "hucre": _sharpe_ay(cH_ret)}
        sharpe_ay_nokta = {k: (None if v is None else round(v, 4)) for k, v in sharpe_ay_nokta.items()}

        # ---- seçilim farkı (anahtar: ticker + ts_open[:10]) ----------------------------------
        h_islem_ix = {(t["ticker"], str(t["ts_open"])[:10]): t for t in H["islem"]}
        yalniz_c_k = [k for k in c_islem_ix if k not in h_islem_ix]
        yalniz_h_k = [k for k in h_islem_ix if k not in c_islem_ix]
        ortak_k = [k for k in c_islem_ix if k in h_islem_ix]
        yalniz_c = [c_islem_ix[k] for k in yalniz_c_k]
        yalniz_h = [h_islem_ix[k] for k in yalniz_h_k]

        ortak_cikis_farkli = [k for k in ortak_k
                              if str(c_islem_ix[k].get("exit_reason")) != str(h_islem_ix[k].get("exit_reason"))]
        d_r = [float(h_islem_ix[k].get("r_multiple") or 0) - float(c_islem_ix[k].get("r_multiple") or 0)
               for k in ortak_k]
        d_pnl = [float(h_islem_ix[k].get("pnl_dollars") or 0) - float(c_islem_ix[k].get("pnl_dollars") or 0)
                 for k in ortak_k]

        # mekanizma sondası — yalnız_C: hücre o (plan-günü,sembol)ünde ne gördü?
        sinyal_ix = {(s["date"], s["ticker"]): s for s in H["sinyal"]}
        plan_ix = {(p["date"], p["ticker"]): p for p in H["plan"]}
        h_araliklar = [(t["ticker"], str(t["ts_open"])[:10], str(t["ts_close"])[:10]) for t in H["islem"]]

        def _pozisyon_acikti(tic: str, gun: str) -> bool:
            return any(a <= gun <= b for tt, a, b in h_araliklar if tt == tic)

        sonda = {"plan_gunu_bulunamadi": 0, "hucrede_pozisyon_acikti": 0,
                 "hucre_sinyal_uretmedi": 0, "hucre_plan_NO_GO": 0,
                 "hucre_silahli_dolmadi": 0, "ornekler_sinyal_uretmedi": []}
        for k in yalniz_c_k:
            tic, ts_open = k
            i = takvim_ix.get(ts_open)
            if i is None or i == 0:
                sonda["plan_gunu_bulunamadi"] += 1
                continue
            pg = tarih_c[i - 1]                       # plan günü = dolumdan önceki seans (beyan başlıkta)
            sk = sinyal_ix.get((pg, tic))
            if sk is None:
                if _pozisyon_acikti(tic, pg):
                    sonda["hucrede_pozisyon_acikti"] += 1
                else:
                    sonda["hucre_sinyal_uretmedi"] += 1
                    if len(sonda["ornekler_sinyal_uretmedi"]) < 10:
                        sonda["ornekler_sinyal_uretmedi"].append({"plan_gunu": pg, "ticker": tic})
                continue
            pl = plan_ix.get((pg, tic))
            if pl is not None and pl.get("verdict") == "NO_GO":
                sonda["hucre_plan_NO_GO"] += 1
            else:
                sonda["hucre_silahli_dolmadi"] += 1
        sonda["beyan"] = ("C'nin kendi sinyal/plan defteri 026 çıktısında saklanmadı → simetrik "
                          "C-tarafı sondası ölçülemedi (None); bu sonda hücre defterinden okur. "
                          "'hucre_sinyal_uretmedi' = aynı (gün,sembol) girdisiyle hücre taraması "
                          "sinyal döndürmedi (girdiler portföyden bağımsız → w teriminin skor/"
                          "kapı etkisi) ya da hücrede sembol o gün armed idi (ayrıştırılamaz, "
                          "armed-günü defteri yok — işaretli belirsizlik)")

        # yalnız_hücre: w0 karşı-olgusalı (hücrenin kendi kaydından)
        yh_w0 = {"w0_sinyal_yok_n": 0, "w0_ayni_setup_n": 0, "w0_setup_farkli_n": 0,
                 "kayit_yok_n": 0, "w0_skor_dusuk_n": 0}
        for t in yalniz_h:
            if t.get("w0_var") is None:
                yh_w0["kayit_yok_n"] += 1
            elif not t["w0_var"]:
                yh_w0["w0_sinyal_yok_n"] += 1
            elif t.get("w0_setup") == t.get("setup"):
                yh_w0["w0_ayni_setup_n"] += 1
                if (t.get("w0_score") is not None and t.get("score") is not None
                        and t["w0_score"] < t["score"]):
                    yh_w0["w0_skor_dusuk_n"] += 1
            else:
                yh_w0["w0_setup_farkli_n"] += 1

        secilim = {
            "anahtar": "(ticker, ts_open[:10])",
            "ortak": {"n": len(ortak_k),
                      "cikis_farkli_n": len(ortak_cikis_farkli),
                      "delta_r": {"ort": round(float(np.mean(d_r)), 5) if d_r else None,
                                  "ort_mutlak": round(float(np.mean(np.abs(d_r))), 5) if d_r else None,
                                  "max_mutlak": round(float(np.max(np.abs(d_r))), 4) if d_r else None},
                      "delta_pnl_toplam": round(float(np.sum(d_pnl)), 2) if d_pnl else None,
                      "beyan": ("ortak işlemde ΔR≈0 beklenir (çıkışlar portföyden bağımsız); "
                                "Δpnl conviction/equity boyutlamasından kayar — beyan başlıkta")},
            "yalniz_C": {"profil": _r_profili(yalniz_c), "mekanizma_sondasi": sonda},
            "yalniz_hucre": {"profil": _r_profili(yalniz_h), "w0_karsi_olgusal": yh_w0},
        }

        # ---- kill bayrakları (kart, DONUK — koşul kaydı, hüküm DEĞİL) ------------------------
        p_sin = sh["payda_sayaci"]["sinyal_bv"]["pay"]
        p_isl = sh["payda_sayaci"]["islem_bv"]["pay"]
        kill1 = {
            "esik": f"turnover-kaynak payda < {PAYDA_KILL_ESIK} → olculemedi (kart kill#1)",
            "sinyal_bv_pay": p_sin, "islem_bv_pay": p_isl,
            "tetiklendi": ((p_sin is not None and p_sin < PAYDA_KILL_ESIK)
                           or (p_isl is not None and p_isl < PAYDA_KILL_ESIK)
                           or p_sin is None or p_isl is None),
        }
        kill2 = {
            "esik": "şasi bütünlüğü bozuksa geçersiz (kart kill#2)",
            "hucre_butunluk": sh["butunluk"]["gecerli"],
            "C_butunluk": sc["butunluk"]["gecerli"],
            "motor_sha_ayni": motor_ayni, "config_sha_ayni": config_ayni,
            "rampa_ayni_15_36": rampa_ayni, "takvim_ayni": takvim_ayni,
            "oz_sinama_skor_kaniti": sh["oz_sinama"]["skor_degisim_kaniti"],
            "tetiklendi": not (sh["butunluk"]["gecerli"] and sc["butunluk"]["gecerli"]
                               and all(motor_ayni.values()) and all(config_ayni.values())
                               and rampa_ayni and takvim_ayni
                               and (smoke or sh["oz_sinama"]["skor_degisim_kaniti"])),
            "serh": serh,
        }

        hucre_bloklari[run_adi] = {
            "w_turnover": HUCRELER[run_adi],
            "sasi_kimligi": {"motor_sha_ayni": motor_ayni, "config_sha_ayni": config_ayni,
                             "rampa_ayni_15_36": rampa_ayni, "takvim_ayni": takvim_ayni,
                             "serh": serh},
            "birincil_farklar_ci95": {
                "net_pnl_fark": ci95(f_pnl),
                "sharpe_ay_fark": ci95(f_sharpe),
                "sharpe_atlanan_iter": sharpe_atlanan,
                "islem_fark": ci95(f_islem),
                "islem_oran": ci95(oran),
                "oran_atlanan_iter": BOOT_ITER - len(oran),
            },
            "tablo": {
                "islem_n": {"C": nC, "hucre": nH, "fark": nH - nC,
                            "fark_pct": round(100.0 * (nH - nC) / nC, 1) if nC else None},
                "net_pnl_equity": {"C": perf_c.get("net_pnl_equity"), "hucre": perf_h.get("net_pnl_equity"),
                                   "fark": (round(perf_h["net_pnl_equity"] - perf_c["net_pnl_equity"], 2)
                                            if None not in (perf_h.get("net_pnl_equity"),
                                                            perf_c.get("net_pnl_equity")) else None)},
                "net_pnl_trades": {"C": perf_c.get("net_pnl_trades"), "hucre": perf_h.get("net_pnl_trades")},
                "sharpe_kanonik": {"C": perf_c.get("sharpe"), "hucre": perf_h.get("sharpe"),
                                   "fark": (round(perf_h["sharpe"] - perf_c["sharpe"], 4)
                                            if None not in (perf_h.get("sharpe"), perf_c.get("sharpe"))
                                            else None)},
                "sharpe_ay_nokta": {**sharpe_ay_nokta,
                                    "fark": (None if None in sharpe_ay_nokta.values() else
                                             round(sharpe_ay_nokta["hucre"] - sharpe_ay_nokta["C"], 4))},
                "maxdd_kanonik": {"C": perf_c.get("maxdd_kanonik"), "hucre": perf_h.get("maxdd_kanonik"),
                                  "oran": (round(perf_h["maxdd_kanonik"] / perf_c["maxdd_kanonik"], 3)
                                           if perf_c.get("maxdd_kanonik") not in (None, 0)
                                           and perf_h.get("maxdd_kanonik") is not None else None)},
                "maxdd_m2m": {"C": perf_c.get("maxdd_m2m"), "hucre": perf_h.get("maxdd_m2m")},
                "avg_r": {"C": perf_c.get("avg_r"), "hucre": perf_h.get("avg_r")},
                "win_rate": {"C": perf_c.get("win_rate"), "hucre": perf_h.get("win_rate")},
                "score": {"C": perf_c.get("score"), "hucre": perf_h.get("score")},
                "total_return": {"C": perf_c.get("total_return"), "hucre": perf_h.get("total_return")},
                "islem_yil": {"C": sc["islem"].get("islem_yil"), "hucre": sh["islem"].get("islem_yil")},
                "silahlanan_plan": {"C": sc["islem"].get("silahlanan_plan"),
                                    "hucre": sh["islem"].get("silahlanan_plan")},
                "toplam_plan": {"C": sc["islem"].get("toplam_plan"), "hucre": sh["islem"].get("toplam_plan")},
                "verdict_dagilim": {"C": sc["islem"].get("verdict_dagilim"),
                                    "hucre": sh["islem"].get("verdict_dagilim")},
                "nogo_neden_dagilim": {"C": sc["islem"].get("nogo_neden_dagilim"),
                                       "hucre": sh["islem"].get("nogo_neden_dagilim")},
                "setup_dagilim_hucre": sh["islem"].get("setup_dagilim"),
                "exit_reason_dagilim": {"C": sc["islem"].get("exit_reason_dagilim"),
                                        "hucre": sh["islem"].get("exit_reason_dagilim")},
                "doluluk_pozisyon_gun": {"C": sc["doluluk"].get("pozisyon_gun_open_fazi"),
                                         "hucre": sh["doluluk"].get("pozisyon_gun_open_fazi")},
                "ort_acik_pozisyon": {"C": sc["doluluk"].get("ort_acik_pozisyon"),
                                      "hucre": sh["doluluk"].get("ort_acik_pozisyon")},
            },
            "secilim_farki": secilim,
            "payda_sayaci": sh["payda_sayaci"],
            "oz_sinama": sh["oz_sinama"],
            "onucus_payda_kaniti": sh["onucus_payda_kaniti"],
            "kill1_payda": kill1,
            "kill2_sasi": kill2,
        }

    out = {
        "kart": "EDG-2026-031",
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "smoke": smoke,
        "kiyas_taban": {"kaynak": "EDG-026 C koşumu HAZIR çıktıları — yeniden koşulmadı",
                        "dosyalar": [str(cdir / f"sonuc_c{ek}.json"),
                                     str(cdir / f"seanslar_c{ek}.json"),
                                     str(cdir / f"islemler_c{ek}.json")],
                        "dosya_sha256_16": c_dosya_sha,
                        "c_w_turnover": ("0.0 (varsayılan — test_turnover_kablolama_v149 bit-bit "
                                         "sıfır-etki çivisi; C = w=0 hücresi)")},
        "yontem": {
            "eslenik_bootstrap": ("ay-kümeli EŞLENİK bootstrap: aynı ay çekilişi iki koşuma birden; "
                                  f"fark = HÜCRE − C; iter={BOOT_ITER}, seed={BOOT_SEED}, n_ay={M}; "
                                  "üç metrik (işlem n, net P&L, sharpe_ay) AYNI çekiliş üzerinde"),
            "islem_ay_anahtari": "ts_open[:7] (giriş ayı)",
            "sharpe_ay_tanimi": ("seans eq_open serisinden aylık bileşik getiri; "
                                 "sharpe = mean/std(ddof=1)×√12; tanım başlıkta DONUK"),
            "birincil_metrikler": "net P&L farkı + sharpe farkı (kart success_metric)",
        },
        "hucreler": hucre_bloklari,
        "dosyalar": {r: {"sonuc": f"sonuc_{r}{ek}.json", "seanslar": f"seanslar_{r}{ek}.json",
                         "islemler": f"islemler_{r}{ek}.json", "sinyaller": f"sinyaller_{r}{ek}.json",
                         "planlar": f"planlar_{r}{ek}.json"} for r in HUCRELER},
        "hukum": None,   # HÜKÜM YAZILMAZ — Rol-1'in işi (kart sözleşmesi)
    }
    (ldir / f"sonuc{ek}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))

    print(f"\n==================== EDG-031 KIYAS ÖZETİ{ek} ====================")
    for r, b in hucre_bloklari.items():
        t = b["tablo"]
        f = b["birincil_farklar_ci95"]
        print(f"\n--- {r} (w={b['w_turnover']}) ---")
        print(f"şasi: serh={b['sasi_kimligi']['serh']}")
        print(f"işlem: C {t['islem_n']['C']} → {t['islem_n']['hucre']}  fark={t['islem_n']['fark']}  "
              f"CI={f['islem_fark']}")
        print(f"net_pnl: C {t['net_pnl_equity']['C']} → {t['net_pnl_equity']['hucre']}  "
              f"fark={t['net_pnl_equity']['fark']}  CI={f['net_pnl_fark']}")
        print(f"sharpe kanonik: C {t['sharpe_kanonik']['C']} → {t['sharpe_kanonik']['hucre']}  "
              f"fark={t['sharpe_kanonik']['fark']}; sharpe_ay fark CI={f['sharpe_ay_fark']} "
              f"(atlanan={f['sharpe_atlanan_iter']})")
        print(f"maxdd kanonik: C {t['maxdd_kanonik']['C']} → {t['maxdd_kanonik']['hucre']} "
              f"(oran={t['maxdd_kanonik']['oran']})")
        s = b["secilim_farki"]
        yc = s["yalniz_C"]["profil"] or {}
        yh = s["yalniz_hucre"]["profil"] or {}
        print(f"seçilim: ortak={s['ortak']['n']}  yalnız_C={yc.get('n', 0)} "
              f"(ort_r={yc.get('ort_r')})  yalnız_hücre={yh.get('n', 0)} (ort_r={yh.get('ort_r')})")
        print(f"payda: sinyal-bv={b['kill1_payda']['sinyal_bv_pay']}  "
              f"işlem-bv={b['kill1_payda']['islem_bv_pay']}  kill#1={b['kill1_payda']['tetiklendi']}")
        print(f"kill#2 (şasi) tetiklendi={b['kill2_sasi']['tetiklendi']}")
    print(f"\nyazıldı: {ldir / ('sonuc' + ek + '.json')}")
    print("==========================================================\n")


if __name__ == "__main__":
    mod = sys.argv[1] if len(sys.argv) > 1 else ""
    smoke = "--smoke" in sys.argv
    if mod in HUCRELER:
        kosum(mod, smoke=smoke)
    elif mod == "kiyas":
        kiyas(smoke=smoke)
    else:
        sys.exit("kullanım: olcum.py {w005|w010|kiyas} [--smoke]")

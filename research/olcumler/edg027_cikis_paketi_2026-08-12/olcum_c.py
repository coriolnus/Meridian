"""EDG-2026-027 — ÇIKIŞ PAKETİ OAT · FAZ-2 (yalnız C-taban hücreleri) · ölçüm aracı (2026-08-12)

Kart: research/cards/EDG-2026-027-cikis-paketi-oat.yaml (OKU-DOKUNMA; hüküm Rol-1'in).
Rol: ÖLÇÜM ajanı. Bu modül HÜKÜM VERMEZ, karta dokunmaz, git/canlı/broker/state'e YAZMAZ.

FAZ-2 KAPSAMI (brief, DONUK): kartın 4 hücresinden yalnız C-tabanlı ikisi ölçülür —
  (H3) C_scaleout   : C dünyası + exit.scale_out_frac 0.0→0.5 + exit.scale_out_r 2.0→1.5
  (H4) C_chandelier : C dünyası + exit.chandelier_lookback 0→20 (trail_atr_mult 2.5 SABİT)
B hücreleri (h1/h2) FAZ-1'de AYRI modülde (olcum.py) — bu modül onların dosyalarına DOKUNMAZ.
Ad ayrıklığı: bu fazın tüm çıktıları *_C_scaleout / *_C_chandelier / sonuc_C_hucreler.json.

C DÜNYASI (EDG-026 olcum.py'den AYNEN devralındı; oradaki yüzey beyanları geçerli):
  rampa 15/36 monkeypatch (broker.derisk_mult modül-özniteliği; motor DOSYASI değişmez)
  + max_open_positions = 20   (goal['limits'] — config.goal() derin kopyası; dosya değişmez)
  + position_size_r    = 0.5  (STRATEJİ params sözlüğü — motorda bu anahtar params yüzeyinde
                               yaşar, strategy.py _f; max_position_r=1.0 yukarı-kırpması 0.5'i
                               etkilemez; params_by_regime 4 rejimde boş — resolve_params kanıtı
                               koşum öncesi assert)
  ZARF SABİT: heat_hard_r=5.0R, heat_review_r=3.5R, max_position_r=1.0,
  max_sector_exposure_pct=40 DEĞİŞMEDİ; sector_cap paydası max_open olduğundan sektör-başına
  fiili tavan 2→8 (motor-içi doğal sonuç, EDG-026 beyanı AYNEN).

KOL ENJEKSİYONU (FAZ-1 olcum.py beyanı AYNEN): scale_out ve chandelier MEKANİZMALARI MOTORDA
ZATEN VAR (broker.scale_out broker.py:529; chandelier bloğu strategy.py:1101) ama paramlarla
KAPALI geldiler (scale_out_frac=0, chandelier_lookback=0). Motor DOSYASINA tek bayt dokunulmaz;
strategy.yaml'dan yüklenen params SÖZLÜĞÜNE koşum içinde değer yazılır. Yayılım motorun kendi
param yolu (backtest.py:257 scale_out(prev_eff); backtest.py:278 resolve_params→manage_position);
dört rejim için resolve_params kanıtı + GERÇEK motor fonksiyonlarıyla öz-sınama koşum öncesi.
Değerler bounds.yaml ızgarasının İÇİNDE (scale_out_r 1.5 ∈ [1.0,4.0]/0.5 · scale_out_frac
0.5 ∈ [0,0.75]/0.25 · chandelier_lookback 20 ∈ [0,30]/5).

TABAN (C) YENİDEN KOŞULMAZ: kıyas tabanı EDG-026'nın HAZIR c_slot20_r05 çıktılarıdır —
sonuc_c.json + islemler_c.json + seanslar_c.json (salt-oku). Karşılaştırılabilirlik sha
çivileriyle KANITLANIR (EDG026_MOTOR_SHA/EDG026_CONFIG_SHA): güncel motor dosyaları ==
EDG-026'nın kayıtları == bu koşumun gördüğü dosyalar; biri kayarsa koşum BAŞLAMADAN düşer.

TANIMLAR (ölçümden ÖNCE donduruldu; sonuç görüldükten sonra değişmez — FAZ-1 ile AYNI):
  islem            = kapanmış işlem satırı (res.trades; EDG-026 ile aynı sözleşme).
  islem R'si       = satırın kendi r_multiple'ı — scale-out'ta BİRLEŞİK (banked+kalan) R
                     (broker.close_position: pnl = pnl_remaining + banked_pnl; tek satır).
  eşli anahtar     = (ts_open[:10], ticker). Girişler değişmediği için aynı pozisyonun iki
                     dünyadaki R'si karşılaştırılır (BİRİNCİL katman). Anahtar tekrarı
                     bulunursa bütünlük bozulur. C dünyasında ısı/slot dinamiği girişleri
                     KAYDIRABİLİR (kart beyanı) → eşli-ortak + tam-defter iki katman.
  eşli fark        = R_hücre − R_C (pozitif = hücre lehine).
  eşli CI          = işlem-TARİH-kümeli eşlenik bootstrap: kümeler eşli kümenin ayrık ts_open
                     tarihleri; tarihler yerine-koymalı çekilir, çekilen her tarihin TÜM eşli
                     farkları havuzlanır, iterasyon istatistiği havuz ortalaması (5000 iter,
                     seed 20260812). Ay-kümeli CI yan-tablo (şeffaflık; ikinci eşik DEĞİL).
  kill#1 (kart)    = eşli-ortak küme hücrede <60 ise eşli-CI 'olculemedi'; tam-defter yine
                     raporlanır ama hüküm dili kullanılmaz.
  kill#2 (kart)    = şasi bütünlüğü: frame_miss=0, dup=0, scan==plan + yasaklı modül 0 +
                     base_max_open==20 + takvim C ile aynı; bozuksa hücre geçersiz.
  kill#3 (kart)    = C-taban 026 koşumu şasi-geçersizse C hücreleri 'bekliyor' — birlestir
                     C tabanının butunluk.gecerli kaydını assert eder (kapı koşum ÖNCESİ).
  hedefe-ulaşma    = (target + target_gap) / n. scale-out'un 1.5R-bankalaması AYRI sayılır
                     (scaled_out_n; hedef tanımını değiştirmez).
  max-dd           = motor-kanonik score.score_detail.max_drawdown; yalnız-M2M ayrıca raporlu.
  net P&L          = M2M equity son değer − START_EQUITY; çapraz: Σ pnl_dollars.

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen = None + neden); YASA-4 (sessiz-yutma işaretli +
gerekçe); YASA-6 (okuyucu: sonuc_C_*/islemler_C_*/seanslar_C_*.json'ları `birlestir` tüketir;
sonuc_C_hucreler.json'u dönüş raporu + Rol-1 tüketir). SALT-OKUMA: config.STATE koşum-başına
izole sandbox; barlar sembolik bağla SALT-OKUNUR; canlı state'e ve motor dosyalarına yazılmaz.
meridian.loop / counterfactual / cf_backfill / hermes İTHAL EDİLMEZ — sys.modules ile KANITLANIR.

KULLANIM:
  olcum_c.py C_scaleout     # H3 koşumu → sonuc_C_scaleout.json + seanslar_… + islemler_…
  olcum_c.py C_chandelier   # H4 koşumu → sonuc_C_chandelier.json + …
  olcum_c.py birlestir      # C(EDG-026) ↔ H3/H4 → eşli CI + tam-defter + kill → sonuc_C_hucreler.json
  (--smoke: kısa pencere 2022-01-01→2022-06-30, çıktılar smoke/ altına — şasi provası;
   smoke'ta birlestir YOK: kıyas tabanı TAM-pencere C'dir, smoke-C ile eşli kıyas anlamsız)
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
EDG022 = REPO / "research/olcumler/edg022_evren_kisit_2026-08-09"   # DONMUŞ config kaynağı (şasi)
EDG026 = REPO / "research/olcumler/edg026_slot20_2026-08-12"        # C-taban çıktıları (HAZIR)

# tek-iş parçacığı: determinizm + ölçüm gürültüsüzlüğü (şasi ile aynı)
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

REPLAY_START = "2022-01-01"
REPLAY_END = "2026-07-30"                      # EDG-026 ile aynı pencere (eşli kıyasın şartı)
BOOT_SEED = 20260812
BOOT_ITER = 5000
ESLI_MIN = 60                                  # kill#1 eşiği (kart, DONUK)

# C dünyasının DONUK parametreleri (EDG-026 features_asof AYNEN)
RAMPA = {"tam_dd": 0.15, "sifir_dd": 0.36}
SLOT = 20
BOYUT_R = 0.5

# hücre kayıtları (kart parameter_grid'in C satırları; K çarpımında sayılıyor)
HUCRELER = {
    "C_scaleout": {
        "trial_id": "pending-027-C-scaleout",
        "enjeksiyon": {"exit.scale_out_frac": 0.5, "exit.scale_out_r": 1.5},
        "sabit_kanit": {"exit.chandelier_lookback": 0},      # OAT saflığı: öteki alet KAPALI kalır
    },
    "C_chandelier": {
        "trial_id": "pending-027-C-chandelier",
        "enjeksiyon": {"exit.chandelier_lookback": 20},
        "sabit_kanit": {"exit.scale_out_frac": 0.0, "exit.trail_atr_mult": 2.5},  # trail 2.5 SABİT
    },
}

# strategy.yaml'ın enjeksiyon-ÖNCESİ değerleri (dosyadan beklenen; delta kanıtının yarısı)
DOSYA_DEGERLERI = {"exit.scale_out_frac": 0.0, "exit.scale_out_r": 2.0,
                   "exit.chandelier_lookback": 0, "exit.trail_atr_mult": 2.5}

# EDG-026 ÇİVİLERİ — 2026-08-12'de sonuc_c.json'dan okunup buraya SABİTLENDİ (üç-yönlü eşitlik:
# bu sabitler == EDG-026 dosyasının kaydı == güncel motor dosyalarının sha'sı).
EDG026_MOTOR_SHA = {"broker.py": "daa858a522d97c98", "backtest.py": "d345b6eed3d28be4",
                    "strategy.py": "ac7c53a3d89b6203"}
EDG026_CONFIG_SHA = {"goal.yaml": "099590dedee1ccf2", "strategy.yaml": "9f3e4732315abe52",
                     "bounds.yaml": "3e810b547ca95f9a"}
EDG026_C_CIVI = {"n_islem": 772, "net_pnl_equity": 9869.2, "maxdd_kanonik": 0.1235}

KART3 = ["tavan_sifir", "evren_bagladi", "derisk_bagladi"]   # seans sınıfları (şasi, DONUK)
YASAK = ("meridian.loop", "meridian.counterfactual", "meridian.cf_backfill", "meridian.hermes")

# NO_GO/REVIEW neden eşlemesi (EDG-026 AYNEN — guard.py sabit alt-dizgileri; eşleşmeyen HAM)
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


def _motor_sha_dogrula() -> dict:
    """Üç motor dosyasının GÜNCEL sha'sı EDG-026 çivisine eşit mi? Eşit değilse taban
    karşılaştırılamaz — koşum başlamadan ölür (assert)."""
    guncel = {f: _sha(REPO / "meridian" / f) for f in EDG026_MOTOR_SHA}
    for f, beklenen in EDG026_MOTOR_SHA.items():
        assert guncel[f] == beklenen, (
            f"MOTOR SHA KAYMIŞ: {f} güncel={guncel[f]} != EDG-026 çivisi={beklenen} — "
            "C tabanı karşılaştırılamaz, ölçüm geçersiz")
    return guncel


def _neden_dagit(nedenler_listesi) -> dict:
    """gate_reasons dizgilerini sabit kontrol adlarına indirger; eşleşmeyen ham kalır (YASA-4)."""
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
# SANDBOX HAZIRLIĞI — koşum başına izole state (şasi AYNEN; kaynak EDG-022 DONMUŞ kopyaları)
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
            shutil.copyfile(EDG022 / "state" / f, dst)
        # config çivisi: sandbox kopyası EDG-026'nın kayıtlı sha'sıyla AYNI olmalı
        assert _sha(dst) == EDG026_CONFIG_SHA[f], (
            f"CONFIG SHA KAYMIŞ: {f} sandbox={_sha(dst)} != EDG-026 çivisi="
            f"{EDG026_CONFIG_SHA[f]} — taban karşılaştırılamaz")
    return st


# ---------------------------------------------------------------------------------------------
# RAMPA — orijinal formülün birebir parametrize kopyası (023/026 varyant deseni AYNEN)
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
# SINIFLAMA + AY-KÜMELİ CI — şasi AYNEN (seans katmanı; tutarlılık için korunur)
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
    """Ay-kümeli bootstrap %95 CI — şasinin fonksiyonu AYNEN."""
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
    """Isı serisinin özeti: max + persentiller + histogram (0.5R kovaları). Boş → None.
    EDG-026 şasi fonksiyonu AYNEN."""
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
    """Seans-başına eşzamanlı pozisyon (işlem aralıklarından): ts_open ≤ seans ≤ ts_close.
    EDG-026 şasi fonksiyonu AYNEN."""
    araliklar = [(str(t["ts_open"])[:10], str(t["ts_close"])[:10]) for t in islemler
                 if t.get("ts_open") and t.get("ts_close")]
    out = []
    for d in takvim:
        out.append(sum(1 for a, b in araliklar if a <= d <= b))
    return out


# ---------------------------------------------------------------------------------------------
# ENJEKSİYON ÖZ-SINAMALARI — FAZ-1 olcum.py'den AYNEN (GERÇEK motor fonksiyonları, sentetik girdi)
# ---------------------------------------------------------------------------------------------
def _oz_sinama_scaleout(brkmod) -> None:
    """H3: enjeksiyon paramlarıyla broker.scale_out GERÇEKTEN 1.5R'de ½ bankalıyor mu?
    Atılabilir PaperBroker + sentetik Position (replay broker'ına dokunulmaz)."""
    def poz(target: float) -> object:
        return brkmod.Position(plan_id="SELFTEST", ticker="_ST", side="long", entry=100.0,
                               stop=95.0, trail_stop=95.0, target=target, qty=100,
                               r_per_share=5.0, risk_dollars=500.0, size_r=1.0,
                               ts_open="2020-01-01")
    b = brkmod.PaperBroker(100_000.0, 5.0, 0.0)          # goal ile aynı: 5 bps, komisyon 0
    prm = {"exit.scale_out_frac": 0.5, "exit.scale_out_r": 1.5}
    bar = {"open": 101.0, "high": 108.0, "low": 100.5}   # level=107.5 ≤ high; stop ihlali yok
    p = poz(target=112.5)                                # 2.5R hedef (goal'deki gibi)
    assert b.scale_out(p, bar, prm) is True, "scale_out enjeksiyonla ateşlemedi"
    assert p.scaled_out and p.qty == 50, "½ bankalama yanlış (qty)"
    assert p.trail_stop == 100.0, "runner breakeven'a kilitlenmedi"
    beklenen = round(50 * (107.5 * (1 - 0.0005) - 100.0), 2)   # 372.31 (slip fiyatın içinde)
    assert abs(p.banked_pnl - beklenen) < 1e-9, f"banked_pnl {p.banked_pnl} != {beklenen}"
    # muhafızlar: hedef-önce (level ≥ target → bankalama YOK) ve stop-önce (low ≤ stop → YOK)
    assert b.scale_out(poz(target=107.0), bar, prm) is False, "hedef-önce muhafızı delindi"
    assert b.scale_out(poz(target=112.5), {"open": 101.0, "high": 108.0, "low": 94.0},
                       prm) is False, "stop-önce muhafızı delindi"
    # kontrol: DOSYA değerleriyle (frac=0) alet kapalı kalır
    assert b.scale_out(poz(target=112.5), bar,
                       {"exit.scale_out_frac": 0.0, "exit.scale_out_r": 2.0}) is False, \
        "frac=0 ile scale_out ateşledi — taban davranışı bozuk"


def _oz_sinama_chandelier(strat, ind) -> None:
    """H4: chandelier_lookback=20 enjeksiyonu manage_position trail'ini GERÇEKTEN swing-high
    çapasına taşıyor mu? Sentetik seri: yükselen 30 bar + son-10-bar penceresinde 150 zirvesi."""
    import numpy as np
    import pandas as pd
    n = 30
    close = np.linspace(100.0, 130.0, n)
    high = close + 1.0
    high[-5] = 150.0                                     # pencere-içi zirve (bars_held=10 → son 10 bar)
    low = close - 1.0
    df = pd.DataFrame({"open": close, "high": high, "low": low, "close": close,
                       "volume": np.full(n, 1e6)})
    pos = {"entry": 100.0, "stop": 95.0, "trail_stop": 95.0, "r_per_share": 5.0, "pivot": 0.0}
    taban_p = dict(DOSYA_DEGERLERI, **{"exit.breakeven_r": 1.0, "exit.time_stop_days": 15,
                                       "exit.giveback_pct": 0.0})
    a = float(ind.atr(df, strat.ATR_PERIOD).iloc[-1])
    assert a > 0 and a < 12, f"sentetik ATR beklenmedik: {a}"    # sınamanın ön-şartı
    d0 = strat.manage_position(df, dict(pos), taban_p, bars_held=10, regime_ok=True)
    d20 = strat.manage_position(df, dict(pos), dict(taban_p, **{"exit.chandelier_lookback": 20}),
                                bars_held=10, regime_ok=True)
    assert not d0.exit_now and not d20.exit_now
    assert abs(d0.trail_stop - max(100.0, 130.0 - 2.5 * a)) < 1e-9, \
        "lookback=0 trail'i beklenen kapalı-alet değerinde değil"
    assert d20.trail_stop > d0.trail_stop, "chandelier trail'i yükseltmedi"
    assert abs(d20.trail_stop - (150.0 - 2.5 * a)) < 1e-9, \
        f"chandelier çapası yanlış: {d20.trail_stop} != {150.0 - 2.5 * a}"


# ---------------------------------------------------------------------------------------------
# TEK KOŞUM (C_scaleout | C_chandelier) — EDG-026 kosum gövdesi + FAZ-1 kol enjeksiyonu
# ---------------------------------------------------------------------------------------------
def kosum(run: str, smoke: bool = False):
    assert run in HUCRELER, f"bilinmeyen hücre: {run}"
    hucre = HUCRELER[run]
    outdir = (SANDBOX / "smoke") if smoke else SANDBOX
    outdir.mkdir(exist_ok=True)
    r_start, r_end = (REPLAY_START, "2022-06-30") if smoke else (REPLAY_START, REPLAY_END)

    motor_sha = _motor_sha_dogrula()                      # taban karşılaştırılamazsa BURADA öl
    st_dir = hazirla(run + ("_smoke" if smoke else ""))
    sys.path.insert(0, str(REPO))

    from meridian import config
    # SALT-OKUMA İZOLASYONU: her yazım (obs.events, history) sandbox'a düşer, canlı state'e DEĞİL
    config.STATE = st_dir
    config.BARS = st_dir / "bars"
    config.HISTORY = st_dir / "history"

    import numpy as np                     # noqa: F401  (bootstrap_ci içinde kullanılır)
    import yaml
    from meridian import backtest, broker as brkmod, dataset, indicators as ind, \
        score as score_mod

    # motorun yamalanmadığını çivile + YASAKLI modül kanıtı (ithal ÖNCESİ)
    assert not hasattr(backtest, "wpg_overlay_day"), "motor YAMALI görünüyor — ölçüm geçersiz"
    assert not [m for m in sys.modules if m in YASAK], "yasaklı modül ithal edilmiş"

    brk = backtest.brk                     # meridian.broker modülü
    assert brk is brkmod
    ORIJ_DERISK = brk.derisk_mult          # orijinal fonksiyon nesnesi (kayıt için)

    # ---- rampa kurulumu + öz-sınama (EDG-026 AYNEN; yayılım kanıtı 5 VE 20 tabanla) ----------
    brk.derisk_mult = _rampa_fn(RAMPA["tam_dd"], RAMPA["sifir_dd"])
    assert brk.derisk_mult is not ORIJ_DERISK
    # yama semantiği: dd=%10 tam boy; dd=%20 → 1-(0.05/0.21)=0.7619; dd>=%36 → 0
    assert brk.derisk_mult(90.0, 100.0) == 1.0
    assert abs(brk.derisk_mult(80.0, 100.0) - 0.7619) < 1e-9
    assert brk.derisk_mult(64.0, 100.0) == 0.0
    # yayılım kanıtı: max_positions_at İÇİNDEKİ global çözüm de yamayı görüyor
    assert brk.max_positions_at(80.0, 100.0, 5) == 4       # round(5×0.7619)=4 (023 çivisi)
    assert brk.max_positions_at(80.0, 100.0, 20) == 15     # round(20×0.7619)=15 (slot-20 tabanı)

    # ---- kol enjeksiyon öz-sınamaları (FAZ-1 AYNEN; GERÇEK motor fonksiyonları) --------------
    _oz_sinama_scaleout(brkmod)
    _oz_sinama_chandelier(backtest.strat, ind)

    # ---- girdiler + PARAM-ENJEKSİYONLARI (dosya DEĞİŞMEZ; sözlükler değişir, beyan başlıkta) -
    stg = yaml.safe_load((st_dir / "strategy.yaml").read_text())
    params = dict(stg["params"])
    by_regime = stg.get("params_by_regime") or None
    sv = int(stg.get("version"))
    goal = config.goal()                                   # derin kopya — dosyaya/önbelleğe sızmaz

    # dosya değerleri beklenen mi? (kol delta kanıtının 'önce' yarısı — FAZ-1 AYNEN)
    for k, v in DOSYA_DEGERLERI.items():
        assert float(params[k]) == float(v), f"strategy.yaml {k}={params[k]} beklenen {v} değil"

    onceki = {"max_open_positions": int(goal["limits"]["max_open_positions"]),
              "position_size_r": float(params["position_size_r"])}
    # C DÜNYASI (EDG-026 AYNEN):
    goal["limits"]["max_open_positions"] = SLOT            # ENJEKSİYON 1 (goal/limits)
    params["position_size_r"] = BOYUT_R                    # ENJEKSİYON 2 (strateji params)
    # KOL (FAZ-1 AYNEN):
    for k, v in hucre["enjeksiyon"].items():
        params[k] = v                                      # ENJEKSİYON 3 (çıkış aleti)
    # OAT saflığı: öteki alet/sabitler dosya değerinde KALDI mı?
    for k, v in hucre["sabit_kanit"].items():
        assert float(params[k]) == float(v), f"OAT saflığı bozuk: {k}={params[k]} != {v}"

    # yayılım kanıtı: rejim çözümü DÖRT rejimde de tüm enjeksiyonları taşıyor
    for _rg in ("trend_up", "trend_down", "chop", "high_vol"):
        _eff = config.resolve_params(params, by_regime, _rg)
        assert float(_eff["position_size_r"]) == BOYUT_R, f"rejim override sızıntısı: {_rg}"
        assert ("position_size_r" not in ((by_regime or {}).get(_rg) or {})), \
            f"params_by_regime[{_rg}] position_size_r içeriyor — tek-nokta enjeksiyonu yetersiz"
        for k, v in hucre["enjeksiyon"].items():
            assert _eff[k] == v, f"resolve_params {_rg} kol enjeksiyonunu düşürdü: {k}"
    assert float(goal["limits"]["max_position_r"]) >= BOYUT_R          # yukarı-kırpma 0.5'i etkilemez
    limits = goal["limits"]
    max_open = int(limits["max_open_positions"])
    no_trade_before = int(limits.get("no_trade_before_bars", 0))
    assert max_open == SLOT

    # ---- kancalar (EDG-026 AYNEN; gerçekleşen-ısı alanları DAHİL) ----------------------------
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
            # GERÇEKLEŞEN ISI (EDG-026 tanımları): scale-out sonrası qty/trail değişimi otomatik yansır
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

    # koşum sonrası kanıt: yasaklı modüller replay SIRASINDA da yüklenmedi
    yasak_yuklu = [m for m in sys.modules if m in YASAK]

    # ---- plan_log çapraz-kontrolü + NO_GO/REVIEW neden dağılımı (EDG-026 AYNEN) --------------
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

    # ---- işlem/doluluk/ısı/performans metrikleri (EDG-026 + FAZ-1 hücre eklentileri) ---------
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
    hedef_n = exit_dist.get("target", 0) + exit_dist.get("target_gap", 0)
    scaled_n = sum(1 for t in trades if t.get("scaled_out"))

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
        "kart": "EDG-2026-027", "faz": "FAZ-2 (C-taban)", "hucre": run,
        "trial_id": hucre["trial_id"], "smoke": smoke,
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sure_sn": sure,
        "rampa": {"tam_dd": RAMPA["tam_dd"], "sifir_dd": RAMPA["sifir_dd"],
                  "enjeksiyon": ("MONKEYPATCH — ölçüm modülü içinde broker.derisk_mult "
                                 "modül-özniteliği değiştirildi; motor DOSYASI değişmedi "
                                 "(EDG-023/026 varyant deseni AYNEN — beyan modül başlığında)")},
        "param_enjeksiyon": {
            "max_open_positions": {"once": onceki["max_open_positions"], "sonra": SLOT,
                                   "yuzey": "goal['limits'] (config.goal() derin kopyası — dosya değişmedi)"},
            "position_size_r": {"once": onceki["position_size_r"], "sonra": BOYUT_R,
                                "yuzey": ("strateji params sözlüğü — EDG-026 yüzey beyanı AYNEN; "
                                          "params_by_regime 4 rejimde boş, resolve_params kanıtı "
                                          "koşum öncesi assert edildi")},
            "zarf_sabit": ("heat_hard_r=5.0R, heat_review_r=3.5R, max_position_r=1.0, "
                           "max_sector_exposure_pct=40 DEĞİŞMEDİ. sector_cap paydası "
                           "max_open_positions olduğundan sektör-başına fiili tavan 2→8'e "
                           "gevşedi (motor-içi doğal sonuç, EDG-026 beyanı AYNEN)"),
        },
        "enjeksiyon_kol": {
            "degerler": hucre["enjeksiyon"],
            "dosya_once": {k: DOSYA_DEGERLERI[k] for k in
                           set(DOSYA_DEGERLERI) & (set(hucre["enjeksiyon"]) | set(hucre["sabit_kanit"]))},
            "sabit_kanit": hucre["sabit_kanit"],
            "beyan": ("PARAMS-SÖZLÜĞÜ ENJEKSİYONU — strategy.yaml DOSYASI ve motor DOSYALARI "
                      "değişmedi; mekanizma motorda mevcut ve paramla kapalıydı (broker.py:529 "
                      "scale_out, strategy.py:1101 chandelier). Yayılım motorun kendi param yolu "
                      "(prev_eff/resolve_params); dört rejim için resolve_params kanıtı + gerçek "
                      "motor fonksiyonlarıyla öz-sınama koşum öncesi geçti (FAZ-1 beyanı AYNEN)."),
        },
        "motor_sha256_16": motor_sha,
        "motor_sha_esit_edg026": True,                    # _motor_sha_dogrula assert'i geçti
        "config_sha256_16": {f: {"sandbox": _sha(st_dir / f),
                                 "edg022": _sha(EDG022 / "state" / f),
                                 "edg026_civi": EDG026_CONFIG_SHA[f],
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
            "hedef_n": hedef_n,
            "hedef_orani_pct": round(100.0 * hedef_n / n_islem, 2) if n_islem else None,
            "scaled_out_n": scaled_n,
            "scaled_out_pct": round(100.0 * scaled_n / n_islem, 2) if n_islem else None,
        },
        "performans": {
            "net_pnl_equity": net_pnl_equity, "net_pnl_trades": net_pnl_trades,
            "maxdd_kanonik": detail.get("max_drawdown"),       # kartın dd yan-tablosu BUNUN üstünden
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
    # slim satırlar: EDG-026 alanları + scaled_out (eşli makinenin soH okuyucusu — FAZ-1 deseni)
    slim = [{k: t.get(k) for k in ("ts_open", "ts_close", "ticker", "r_multiple",
                                   "pnl_dollars", "exit_reason", "bars_held", "regime",
                                   "setup", "qty", "risk_dollars", "size_r", "scaled_out")}
            for t in trades]
    (outdir / f"islemler_{run}{ek}.json").write_text(
        json.dumps(slim, ensure_ascii=False, default=str))

    print(f"\n=========== EDG-027 FAZ-2 KOŞUM [{run}{ek}] ===========")
    print(f"replay {r_start}→{r_end}  sv={sv}  sembol={len(bars)}  süre={sure}s")
    print(f"C dünyası: max_open {onceki['max_open_positions']}→{max_open}  "
          f"position_size_r {onceki['position_size_r']}→{params['position_size_r']}")
    print(f"kol enjeksiyonu: {hucre['enjeksiyon']}")
    print(f"bütünlük geçerli={out['butunluk']['gecerli']}  frame_miss={_frame_miss[0]} "
          f"dup={len(_dup)} scan!=plan={len(scan_vs_plan)} yasak={yasak_yuklu} "
          f"base_max_bozuk={len(base_max_bozuk)}")
    print(f"işlem n={n_islem} ({out['islem']['islem_yil']}/yıl)  net_pnl={net_pnl_equity}  "
          f"maxdd_kanonik={detail.get('max_drawdown')}  maxdd_m2m={maxdd_m2m}  "
          f"avg_r={detail.get('avg_r')}")
    print(f"çıkışlar: {out['islem']['exit_reason_dagilim']}")
    print(f"hedef oranı %{out['islem']['hedef_orani_pct']}  scaled_out n={scaled_n}")
    print(f"NO_GO nedenleri: {out['islem']['nogo_neden_dagilim']}")
    print(f"yazıldı: {outdir}/sonuc_{run}{ek}.json")


# ---------------------------------------------------------------------------------------------
# EŞLİ KIYAS MAKİNESİ — FAZ-1 olcum.py'den AYNEN ((ts_open,ticker) anahtar; tarih-kümeli eşlenik)
# ---------------------------------------------------------------------------------------------
def _anahtar_haritasi(islemler: list[dict]) -> tuple[dict, int]:
    m: dict = {}
    dup = 0
    for t in islemler:
        k = (str(t["ts_open"])[:10], t["ticker"])
        if k in m:
            dup += 1
        m[k] = t
    return m, dup


def _esli_analiz(islem_T: list[dict], islem_H: list[dict]) -> dict:
    """islem_T = taban (C), islem_H = hücre. FAZ-1 _esli_analiz gövdesi AYNEN (B→T adlandırma)."""
    import numpy as np
    mT, dupT = _anahtar_haritasi(islem_T)
    mH, dupH = _anahtar_haritasi(islem_H)
    ortak = sorted(set(mT) & set(mH))
    n = len(ortak)

    ciftler = []
    for k in ortak:
        rT = float(mT[k]["r_multiple"])
        rH = float(mH[k]["r_multiple"])
        ciftler.append({"tarih": k[0], "fark": rH - rT,
                        "cT": str(mT[k]["exit_reason"]), "cH": str(mH[k]["exit_reason"]),
                        "soH": bool(mH[k].get("scaled_out"))})

    farklar = np.array([c["fark"] for c in ciftler]) if ciftler else np.array([])
    gecis: dict[str, int] = {}
    for c in ciftler:
        key = f"{c['cT']}→{c['cH']}"
        gecis[key] = gecis.get(key, 0) + 1

    # tarih-kümeli eşlenik bootstrap (BİRİNCİL) + ay-kümeli yan-tablo (şeffaflık, ikinci eşik değil)
    def _kumeli_ci(anahtar_fn) -> dict | None:
        if not ciftler:
            return None
        kume: dict[str, list[float]] = {}
        for c in ciftler:
            kume.setdefault(anahtar_fn(c["tarih"]), []).append(c["fark"])
        adlar = sorted(kume)
        arrs = {a: np.array(kume[a]) for a in adlar}
        m = len(adlar)
        rng = np.random.default_rng(BOOT_SEED)
        ortalar = np.empty(BOOT_ITER)
        idx_all = np.arange(m)
        for i in range(BOOT_ITER):
            pick = rng.choice(idx_all, size=m, replace=True)
            pooled = np.concatenate([arrs[adlar[j]] for j in pick])
            ortalar[i] = pooled.mean()
        return {"lo": round(float(np.percentile(ortalar, 2.5)), 4),
                "hi": round(float(np.percentile(ortalar, 97.5)), 4),
                "orta": round(float(np.median(ortalar)), 4),
                "_n_kume": m}

    kill1 = n < ESLI_MIN
    ci_tarih = None if kill1 else _kumeli_ci(lambda d: d)
    ci_ay = None if kill1 else _kumeli_ci(lambda d: d[:7])

    def _tek_yon(anahtarlar, harita):
        satirlar = [harita[k] for k in anahtarlar]
        return {"n": len(satirlar),
                "toplam_r": round(sum(float(t["r_multiple"]) for t in satirlar), 3),
                "toplam_pnl": round(sum(float(t["pnl_dollars"]) for t in satirlar), 2)}

    return {
        "esli_n": n,
        "anahtar_tekrar": {"C": dupT, "H": dupH},        # 0 olmalı (bütünlük)
        "kill1_esli_lt_min": kill1,
        "kill1_esik": ESLI_MIN,
        "ort_fark": round(float(farklar.mean()), 4) if n else None,
        "medyan_fark": round(float(np.median(farklar)), 4) if n else None,
        "fark_pos_n": int((farklar > 0).sum()) if n else None,
        "fark_neg_n": int((farklar < 0).sum()) if n else None,
        "fark_sifir_n": int((farklar == 0).sum()) if n else None,
        "ci95_tarih_kumeli_eslenik": ("olculemedi (kill#1: eşli-ortak "
                                      f"{n} < {ESLI_MIN})") if kill1 else ci_tarih,
        "ci95_ay_kumeli_yan_tablo": None if kill1 else ci_ay,
        "cikis_gecis_matrisi": dict(sorted(gecis.items(), key=lambda kv: -kv[1])),
        "esli_scaled_out_n": sum(1 for c in ciftler if c["soH"]),
        "yalniz_C": _tek_yon(sorted(set(mT) - set(mH)), mT),
        "yalniz_H": _tek_yon(sorted(set(mH) - set(mT)), mH),
    }


# ---------------------------------------------------------------------------------------------
# BİRLEŞTİR — C(EDG-026 hazır) ↔ H3/H4 → eşli CI + tam-defter + kill → sonuc_C_hucreler.json
# ---------------------------------------------------------------------------------------------
def birlestir():
    # ---- C tabanı: EDG-026'nın HAZIR dosyaları (yeniden koşum YOK; salt-okuma) ---------------
    C_sonuc = json.loads((EDG026 / "sonuc_c.json").read_text())
    C_islem = json.loads((EDG026 / "islemler_c.json").read_text())
    C_seans = json.loads((EDG026 / "seanslar_c.json").read_text())

    # C çivisi: okunan dosya GERÇEKTEN 2026-08-12 c_slot20_r05 koşumu mu?
    assert C_sonuc["kosum"] == "c_slot20_r05" and not C_sonuc["smoke"]
    assert len(C_islem) == EDG026_C_CIVI["n_islem"], "C islemler dosyası çiviyle uyuşmuyor"
    assert C_sonuc["performans"]["net_pnl_equity"] == EDG026_C_CIVI["net_pnl_equity"]
    assert C_sonuc["performans"]["maxdd_kanonik"] == EDG026_C_CIVI["maxdd_kanonik"]
    assert C_sonuc["motor_sha256_16"] == EDG026_MOTOR_SHA, "C kayıtlı motor sha çiviyle uyuşmuyor"
    # kill#3 kapısı (kart): C-taban şasi-geçersizse C hücreleri 'bekliyor' — burada assert
    assert C_sonuc["butunluk"]["gecerli"] is True, (
        "KILL#3: C-taban (EDG-026) şasi-geçersiz — C hücreleri 'bekliyor'; bu birleştirme koşulamaz")
    motor_guncel = _motor_sha_dogrula()

    # ---- eşli makine öz-kontrolü: C↔C eşlemesi n=772, tüm farklar 0, CI [0,0] ----------------
    kendi = _esli_analiz(C_islem, C_islem)
    assert kendi["esli_n"] == EDG026_C_CIVI["n_islem"] and kendi["anahtar_tekrar"] == {"C": 0, "H": 0}
    assert kendi["ort_fark"] == 0.0 and kendi["fark_pos_n"] == 0 and kendi["fark_neg_n"] == 0
    assert kendi["ci95_tarih_kumeli_eslenik"]["lo"] == 0.0 and \
        kendi["ci95_tarih_kumeli_eslenik"]["hi"] == 0.0

    C_tarihler = [s["date"] for s in C_seans]
    iC_hedef_n = (C_sonuc["islem"]["exit_reason_dagilim"].get("target", 0)
                  + C_sonuc["islem"]["exit_reason_dagilim"].get("target_gap", 0))

    hucre_blok: dict[str, dict] = {}
    kill_ozeti: dict[str, dict] = {}
    for run in HUCRELER:
        H_sonuc = json.loads((SANDBOX / f"sonuc_{run}.json").read_text())
        H_islem = json.loads((SANDBOX / f"islemler_{run}.json").read_text())
        H_seans = json.loads((SANDBOX / f"seanslar_{run}.json").read_text())

        takvim_ayni = ([s["date"] for s in H_seans] == C_tarihler)
        esli = _esli_analiz(C_islem, H_islem)

        butunluk_ok = (H_sonuc["butunluk"]["gecerli"] and takvim_ayni
                       and esli["anahtar_tekrar"] == {"C": 0, "H": 0}
                       and H_sonuc["motor_sha256_16"] == EDG026_MOTOR_SHA)

        pC, pH = C_sonuc["performans"], H_sonuc["performans"]
        iC, iH = C_sonuc["islem"], H_sonuc["islem"]
        nC, nH = int(iC["n"]), int(iH["n"])

        tam_defter = {
            "islem_n": {"C": nC, "hucre": nH, "fark": nH - nC,
                        "fark_pct": round(100.0 * (nH - nC) / nC, 1) if nC else None},
            "islem_yil": {"C": iC["islem_yil"], "hucre": iH["islem_yil"]},
            "net_pnl_equity": {"C": pC["net_pnl_equity"], "hucre": pH["net_pnl_equity"],
                               "fark": round(pH["net_pnl_equity"] - pC["net_pnl_equity"], 2)},
            "net_pnl_trades": {"C": pC["net_pnl_trades"], "hucre": pH["net_pnl_trades"]},
            "maxdd_kanonik": {"C": pC["maxdd_kanonik"], "hucre": pH["maxdd_kanonik"]},
            "maxdd_m2m": {"C": pC["maxdd_m2m"], "hucre": pH["maxdd_m2m"]},
            "avg_r": {"C": pC["avg_r"], "hucre": pH["avg_r"]},
            "win_rate": {"C": pC["win_rate"], "hucre": pH["win_rate"]},
            "sharpe": {"C": pC["sharpe"], "hucre": pH["sharpe"]},
            "score": {"C": pC["score"], "hucre": pH["score"]},
            "exit_reason_dagilim": {"C": iC["exit_reason_dagilim"],
                                    "hucre": iH["exit_reason_dagilim"]},
            "hedef_orani_pct": {"C": round(100.0 * iC_hedef_n / nC, 2) if nC else None,
                                "hucre": iH["hedef_orani_pct"]},
            "scaled_out": {"C": {"n": 0, "not": "frac=0 — alet kapalı (tanım gereği)"},
                           "hucre": {"n": iH["scaled_out_n"], "pct": iH["scaled_out_pct"]}},
            "doluluk_pozisyon_gun": {"C": C_sonuc["doluluk"]["pozisyon_gun_open_fazi"],
                                     "hucre": H_sonuc["doluluk"]["pozisyon_gun_open_fazi"]},
            "ort_acik_pozisyon": {"C": C_sonuc["doluluk"]["ort_acik_pozisyon"],
                                  "hucre": H_sonuc["doluluk"]["ort_acik_pozisyon"]},
            "doluluk_orani_slot": {"C": C_sonuc["doluluk"]["doluluk_orani_slot"],
                                   "hucre": H_sonuc["doluluk"]["doluluk_orani_slot"]},
            "toplam_bars_held": {"C": C_sonuc["doluluk"]["toplam_bars_held"],
                                 "hucre": H_sonuc["doluluk"]["toplam_bars_held"]},
            "silahlanan_plan": {"C": iC["silahlanan_plan"], "hucre": iH["silahlanan_plan"]},
            "toplam_plan": {"C": iC["toplam_plan"], "hucre": iH["toplam_plan"]},
            "verdict_dagilim": {"C": iC["verdict_dagilim"], "hucre": iH["verdict_dagilim"]},
            "nogo_neden_dagilim": {"C": iC["nogo_neden_dagilim"],
                                   "hucre": iH["nogo_neden_dagilim"]},
            "entry_rejects": {"C": iC["entry_rejects"], "hucre": iH["entry_rejects"]},
            # C dünyasına özgü yan-tablo: ısı zarfı (heat_hard NO_GO ile birlikte okunur)
            "tepe_isi_ozet": {
                "C": {"nominal_open_max_R": C_sonuc["tepe_isi"]["nominal_open_fazi_R"]["max"],
                      "gerceklesen_sizeR_max": C_sonuc["tepe_isi"]["gerceklesen_open_fazi"]["size_r_toplam"]["max"],
                      "kalan_risk_nav_pct_max": C_sonuc["tepe_isi"]["gerceklesen_open_fazi"]["kalan_risk_nav_pct_max"],
                      "eszamanli_poz_max": C_sonuc["tepe_isi"]["eszamanli_poz_max"]},
                "hucre": {"nominal_open_max_R": H_sonuc["tepe_isi"]["nominal_open_fazi_R"]["max"],
                          "gerceklesen_sizeR_max": H_sonuc["tepe_isi"]["gerceklesen_open_fazi"]["size_r_toplam"]["max"],
                          "kalan_risk_nav_pct_max": H_sonuc["tepe_isi"]["gerceklesen_open_fazi"]["kalan_risk_nav_pct_max"],
                          "eszamanli_poz_max": H_sonuc["tepe_isi"]["eszamanli_poz_max"]},
            },
        }

        hucre_blok[run] = {
            "trial_id": HUCRELER[run]["trial_id"],
            "enjeksiyon_kol": H_sonuc["enjeksiyon_kol"]["degerler"],
            "sure_sn": H_sonuc["sure_sn"],
            "butunluk_hucre": H_sonuc["butunluk"],
            "takvim_ayni_C": takvim_ayni,
            "kill2_sasi_gecerli": butunluk_ok,
            "esli": esli,
            "tam_defter": tam_defter,
        }
        kill_ozeti[run] = {
            "kill1_esli_lt60": esli["kill1_esli_lt_min"],
            "kill2_sasi_bozuk": not butunluk_ok,
        }

    out = {
        "kart": "EDG-2026-027",
        "faz": "FAZ-2 — yalnız C-taban hücreleri (B hücreleri FAZ-1 olcum.py'de; bu modül onlara dokunmaz)",
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "yontem": {
            "esli_anahtar": "(ts_open[:10], ticker) — girişler değişmediği ölçüde aynı pozisyonun iki dünyadaki R'si",
            "esli_R": "satırın r_multiple'ı — scale-out'ta birleşik (banked+kalan; broker.close_position tek satır)",
            "esli_ci": ("işlem-TARİH-kümeli eşlenik bootstrap: kümeler eşli kümenin ayrık ts_open "
                        f"tarihleri; yerine-koymalı; iter={BOOT_ITER}, seed={BOOT_SEED}; "
                        "fark=hücre−C; ay-kümeli CI yan-tablo (ikinci eşik değil)"),
            "taban_C": ("EDG-026 c_slot20_r05 (rampa 15/36 + slot20 + 0.5R) HAZIR çıktıları — "
                        "yeniden koşulmadı; sha çivileri + n/pnl/dd çivileriyle doğrulandı"),
            "esli_makine_kontrolu": "C↔C öz-eşleme: n=772, tüm farklar 0, CI [0,0] — assert geçti",
        },
        "sha_dogrulama": {
            "motor_guncel": motor_guncel,
            "edg026_civi": EDG026_MOTOR_SHA,
            "hucre_kayitlari_esit": all(
                json.loads((SANDBOX / f"sonuc_{r}.json").read_text())["motor_sha256_16"]
                == EDG026_MOTOR_SHA for r in HUCRELER),
            "config_civi": EDG026_CONFIG_SHA,
        },
        "kill3_c_taban": {
            "esik": "C-taban 026 koşumu şasi-geçersizse C hücreleri 'bekliyor' (kart kill#3)",
            "c_taban_butunluk_gecerli": C_sonuc["butunluk"]["gecerli"],
            "tetiklendi": not C_sonuc["butunluk"]["gecerli"],
        },
        "taban_C_ozet": {
            "kaynak": str(EDG026),
            "islem_n": len(C_islem),
            "performans": C_sonuc["performans"],
            "exit_reason_dagilim": C_sonuc["islem"]["exit_reason_dagilim"],
            "nogo_neden_dagilim": C_sonuc["islem"]["nogo_neden_dagilim"],
            "butunluk": C_sonuc["butunluk"],
        },
        "hucreler": hucre_blok,
        "kill_bayraklari": kill_ozeti,
        "dosyalar": {
            "C": {"sonuc": str(EDG026 / "sonuc_c.json"),
                  "islemler": str(EDG026 / "islemler_c.json"),
                  "seanslar": str(EDG026 / "seanslar_c.json")},
            **{r: {"sonuc": f"sonuc_{r}.json", "seanslar": f"seanslar_{r}.json",
                   "islemler": f"islemler_{r}.json"} for r in HUCRELER},
        },
    }
    (SANDBOX / "sonuc_C_hucreler.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str))

    print("\n==================== EDG-027 FAZ-2 C↔{H3,H4} ÖZET ====================")
    for run, blok in hucre_blok.items():
        e = blok["esli"]
        t = blok["tam_defter"]
        print(f"\n--- {run}  enjeksiyon={blok['enjeksiyon_kol']}")
        print(f"  şasi geçerli={blok['kill2_sasi_gecerli']}  takvim_ayni={blok['takvim_ayni_C']}")
        print(f"  eşli n={e['esli_n']} (kill#1={e['kill1_esli_lt_min']})  "
              f"ort_fark={e['ort_fark']}  CI95_tarih={e['ci95_tarih_kumeli_eslenik']}")
        print(f"  eşli +/-/0: {e['fark_pos_n']}/{e['fark_neg_n']}/{e['fark_sifir_n']}  "
              f"yalnızC={e['yalniz_C']['n']} yalnızH={e['yalniz_H']['n']}")
        print(f"  işlem n: {t['islem_n']}  net_pnl: {t['net_pnl_equity']}")
        print(f"  maxdd_kanonik: {t['maxdd_kanonik']}  avg_r: {t['avg_r']}")
        print(f"  hedef oranı: {t['hedef_orani_pct']}  scaled_out: {t['scaled_out']['hucre']}")
        print(f"  NO_GO: C={t['nogo_neden_dagilim']['C']}")
        print(f"         H={t['nogo_neden_dagilim']['hucre']}")
    print(f"\nyazıldı: {SANDBOX / 'sonuc_C_hucreler.json'}")
    print("======================================================================\n")


if __name__ == "__main__":
    mod = sys.argv[1] if len(sys.argv) > 1 else ""
    smoke = "--smoke" in sys.argv
    if mod in HUCRELER:
        kosum(mod, smoke=smoke)
    elif mod == "birlestir":
        assert not smoke, "smoke'ta birlestir yok (kıyas tabanı TAM-pencere C'dir)"
        birlestir()
    else:
        sys.exit("kullanım: olcum_c.py {C_scaleout|C_chandelier|birlestir} [--smoke]")

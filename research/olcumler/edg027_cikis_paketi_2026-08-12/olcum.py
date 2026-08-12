"""EDG-2026-027 — ÇIKIŞ PAKETİ OAT · FAZ-1 (yalnız B-taban hücreleri) · ölçüm aracı (2026-08-12)

Kart: research/cards/EDG-2026-027-cikis-paketi-oat.yaml (OKU-DOKUNMA; hüküm Rol-1'in).
Rol: ÖLÇÜM ajanı. Bu modül HÜKÜM VERMEZ, karta dokunmaz, git/canlı/broker/state'e YAZMAZ.
Şasi: EDG-023 (research/olcumler/edg023_rampa_bandi_2026-08-12/olcum.py) — izole sandbox,
rampa-15/36 monkeypatch beyanı, kanca deseni, bütünlük kontrolleri ve eşlenik bootstrap
(seed 20260812) oradan AYNEN devralındı.

FAZ-1 KAPSAMI (brief, DONUK): kartın 4 hücresinden yalnız B-tabanlı ikisi ölçülür —
  (H1) h1_scaleout   : B paramları + exit.scale_out_frac 0.0→0.5 + exit.scale_out_r 2.0→1.5
  (H2) h2_chandelier : B paramları + exit.chandelier_lookback 0→20 (trail_atr_mult 2.5 SABİT)
C hücreleri (C_scaleout, C_chandelier) AYRI FAZDA — bu modül onlara DOKUNMAZ (kill#3 kartta:
C-taban 026 şasi-geçersizse C hücreleri 'bekliyor'; o karar bu fazın dışında).

TABAN (B) YENİDEN KOŞULMAZ: kıyas tabanı EDG-023'ün HAZIR varyant (15/36) çıktılarıdır —
sonuc_varyant.json + islemler_varyant.json + seanslar_varyant.json. Karşılaştırılabilirlik
üç sha çivisiyle KANITLANIR (aşağıda EDG023_MOTOR_SHA/EDG023_CONFIG_SHA): güncel motor
dosyaları == EDG-023'ün kayıtlı sha'ları == bu koşumun gördüğü dosyalar; biri kayarsa koşum
BAŞLAMADAN düşer (20 dakikalık koşumun sonunda değil).

"B paramları" = EDG-023 varyantı: rampa 15/36 monkeypatch (beyanı EDG-023 başlığında; burada
aynen tekrar uygulanır ve aynı öz-sınamalardan geçirilir) + slot 5 + 1R + v3 params.

ENJEKSİYON — BEYAN (kart 'motor YAMASIZ' ilkesi + brief NOT'u):
  scale_out ve chandelier MEKANİZMALARI MOTORDA ZATEN VAR (broker.scale_out broker.py:529;
  chandelier bloğu strategy.py:1101) ama goal/strategy paramlarıyla KAPALI geldiler
  (scale_out_frac=0, chandelier_lookback=0). Bu ölçüm motor DOSYASINA tek bayt dokunmaz;
  strategy.yaml'dan yüklenen params SÖZLÜĞÜNE koşum içinde değer yazar (enjeksiyon). Yayılım
  yüzeyi motorun kendi param yolu: backtest.py:257 scale_out(prev_eff) ve backtest.py:278
  resolve_params(...)→manage_position(eff). params_by_regime dört rejimde de boş {} olduğundan
  düz-params enjeksiyonu her tüketiciye ulaşır — yine de resolve_params üstünden dört rejim
  için KANITLANIR (öz-sınama). Değerler bounds.yaml ızgarasının İÇİNDE (scale_out_r 1.5 ∈
  [1.0,4.0]/0.5 · scale_out_frac 0.5 ∈ [0,0.75]/0.25 · chandelier_lookback 20 ∈ [0,30]/5).

TANIMLAR (ölçümden ÖNCE donduruldu; sonuç görüldükten sonra değişmez):
  islem            = kapanmış işlem satırı (res.trades; EDG-023 ile aynı sözleşme).
  islem R'si       = satırın kendi r_multiple'ı — scale-out'ta BİRLEŞİK (banked+kalan) R
                     (broker.close_position: pnl = pnl_remaining + banked_pnl; tek satır).
  eşli anahtar     = (ts_open[:10], ticker). Girişler değişmediği için aynı pozisyonun iki
                     dünyadaki R'si karşılaştırılır (BİRİNCİL katman). Anahtar tekrarı
                     bulunursa bütünlük bozulur (aynı gün aynı sembol iki kez açılamaz).
  eşli fark        = R_hücre − R_B (pozitif = hücre lehine).
  eşli CI          = işlem-TARİH-kümeli eşlenik bootstrap: kümeler eşli kümenin ayrık ts_open
                     tarihleri; tarihler yerine-koymalı çekilir, çekilen her tarihin TÜM eşli
                     farkları havuzlanır, iterasyon istatistiği havuz ortalaması (5000 iter,
                     seed 20260812). Eşlenik: fark serisi çiftin iki dünyasını BİRLİKTE taşır,
                     aynı çekiliş iki dünyaya birden uygulanmış olur. Ay-kümeli CI yan-tablo
                     olarak da verilir (bitişik-gün bağımlılığına karşı şeffaflık; ikinci
                     eşik DEĞİL).
  kill#1 (kart)    = eşli-ortak küme hücrede <60 ise eşli-CI 'olculemedi'; tam-defter yine
                     raporlanır ama hüküm dili kullanılmaz.
  kill#2 (kart)    = şasi bütünlüğü: frame_miss=0, dup=0, scan==plan (EDG-023 kancaları) +
                     yasaklı modül 0 + takvim B ile aynı; bozuksa hücre geçersiz.
  hedefe-ulaşma    = (target + target_gap) / n (çıkış-sebebi payı). scale-out'un kendi
                     1.5R-bankalaması AYRI sayılır (scaled_out_n; hedef tanımını değiştirmez).
  max-dd           = motor-kanonik score.score_detail.max_drawdown; yalnız-M2M ayrıca raporlu.
  net P&L          = M2M equity son değer − START_EQUITY; çapraz: Σ pnl_dollars.

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen = None + neden); YASA-4 (sessiz-yutma işaretli +
gerekçe); YASA-6 (okuyucu: sonuc_<hücre>/islemler_<hücre>/seanslar_<hücre>.json'ları
`birlestir` tüketir; sonuc.json'u dönüş raporu + Rol-1 tüketir). SALT-OKUMA: config.STATE
koşum-başına izole sandbox; barlar sembolik bağla canlı önbellekten SALT-OKUNUR; canlı
state'e ve motor dosyalarına yazılmaz. meridian.loop / counterfactual / cf_backfill / hermes
İTHAL EDİLMEZ — koşum sonunda sys.modules ile KANITLANIR (brief: hermes de listede).

KULLANIM:
  olcum.py h1_scaleout      # H1 koşumu → sonuc_h1_scaleout.json + seanslar_… + islemler_…
  olcum.py h2_chandelier    # H2 koşumu → sonuc_h2_chandelier.json + …
  olcum.py birlestir        # B(EDG-023) ↔ H1/H2 → eşli CI'lar + tam-defter + kill → sonuc.json
  (--smoke: kısa pencere 2022-01-01→2022-06-30, çıktılar smoke/ altına — şasi provası;
   smoke'ta birlestir YOK: B tabanının smoke çıktısı yok ve B yeniden koşulmaz)
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
EDG023 = REPO / "research/olcumler/edg023_rampa_bandi_2026-08-12"   # B-taban çıktıları (HAZIR)

# tek-iş parçacığı: determinizm + ölçüm gürültüsüzlüğü (şasi ile aynı)
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

REPLAY_START = "2022-01-01"
REPLAY_END = "2026-07-30"                      # EDG-023 ile aynı pencere (eşli kıyasın şartı)
BOOT_SEED = 20260812
BOOT_ITER = 5000
ESLI_MIN = 60                                  # kill#1 eşiği (kart, DONUK)

# rampa B bandı (EDG-023 varyantı, DONUK) — her iki hücrede AYNEN uygulanır
RAMPA_B = {"tam_dd": 0.15, "sifir_dd": 0.36}

# hücre kayıtları (kart parameter_grid'in B satırları; K çarpımında sayılıyor)
HUCRELER = {
    "h1_scaleout": {
        "trial_id": "pending-027-B-scaleout",
        "enjeksiyon": {"exit.scale_out_frac": 0.5, "exit.scale_out_r": 1.5},
        "sabit_kanit": {"exit.chandelier_lookback": 0},      # OAT saflığı: öteki alet KAPALI kalır
    },
    "h2_chandelier": {
        "trial_id": "pending-027-B-chandelier",
        "enjeksiyon": {"exit.chandelier_lookback": 20},
        "sabit_kanit": {"exit.scale_out_frac": 0.0, "exit.trail_atr_mult": 2.5},  # trail 2.5 SABİT
    },
}

# strategy.yaml'ın enjeksiyon-ÖNCESİ değerleri (dosyadan beklenen; delta kanıtının yarısı)
DOSYA_DEGERLERI = {"exit.scale_out_frac": 0.0, "exit.scale_out_r": 2.0,
                   "exit.chandelier_lookback": 0, "exit.trail_atr_mult": 2.5}

# EDG-023 ÇİVİLERİ — 2026-08-12'de sonuc_varyant.json'dan okunup buraya SABİTLENDİ (üç-yönlü
# eşitlik: bu sabitler == EDG-023 dosyasının kaydı == güncel motor dosyalarının sha'sı).
EDG023_MOTOR_SHA = {"broker.py": "daa858a522d97c98", "backtest.py": "d345b6eed3d28be4",
                    "strategy.py": "ac7c53a3d89b6203"}
EDG023_CONFIG_SHA = {"goal.yaml": "099590dedee1ccf2", "strategy.yaml": "9f3e4732315abe52",
                     "bounds.yaml": "3e810b547ca95f9a"}
EDG023_B_CIVI = {"n_islem": 410, "net_pnl_equity": 774.6, "maxdd_kanonik": 0.1775}

KART3 = ["tavan_sifir", "evren_bagladi", "derisk_bagladi"]   # seans sınıfları (şasi, DONUK)


def _sha(p: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    except OSError:
        return None    # ölçülemedi (dosya yok/okunamadı) — None, uydurma özet değil


def _motor_sha_dogrula() -> dict:
    """Üç motor dosyasının GÜNCEL sha'sı EDG-023 çivisine eşit mi? Eşit değilse taban
    karşılaştırılamaz — koşum başlamadan ölür (assert)."""
    guncel = {f: _sha(REPO / "meridian" / f) for f in EDG023_MOTOR_SHA}
    for f, beklenen in EDG023_MOTOR_SHA.items():
        assert guncel[f] == beklenen, (
            f"MOTOR SHA KAYMIŞ: {f} güncel={guncel[f]} != EDG-023 çivisi={beklenen} — "
            "B tabanı karşılaştırılamaz, ölçüm geçersiz")
    return guncel


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
        # config çivisi: sandbox kopyası EDG-023'ün kayıtlı sha'sıyla AYNI olmalı
        assert _sha(dst) == EDG023_CONFIG_SHA[f], (
            f"CONFIG SHA KAYMIŞ: {f} sandbox={_sha(dst)} != EDG-023 çivisi="
            f"{EDG023_CONFIG_SHA[f]} — taban karşılaştırılamaz")
    return st


# ---------------------------------------------------------------------------------------------
# RAMPA — şasinin birebir parametrize kopyası (B paramlarının parçası; beyan başlıkta)
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


# ---------------------------------------------------------------------------------------------
# ENJEKSİYON ÖZ-SINAMALARI — koşum ÖNCESİ, GERÇEK motor fonksiyonlarıyla (sentetik girdi)
# ---------------------------------------------------------------------------------------------
def _oz_sinama_scaleout(brkmod) -> None:
    """H1: enjeksiyon paramlarıyla broker.scale_out GERÇEKTEN 1.5R'de ½ bankalıyor mu?
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
    """H2: chandelier_lookback=20 enjeksiyonu manage_position trail'ini GERÇEKTEN swing-high
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
# TEK KOŞUM (h1_scaleout | h2_chandelier)
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

    # motorun yamalanmadığını çivile + YASAKLI modül kanıtı (ithal ÖNCESİ; hermes brief'le eklendi)
    assert not hasattr(backtest, "wpg_overlay_day"), "motor YAMALI görünüyor — ölçüm geçersiz"
    YASAK = ("meridian.loop", "meridian.counterfactual", "meridian.cf_backfill", "meridian.hermes")
    assert not [m for m in sys.modules if m in YASAK], "yasaklı modül ithal edilmiş"

    brk = backtest.brk                     # meridian.broker modülü
    assert brk is brkmod

    # ---- B paramlarının rampa bacağı: 15/36 monkeypatch + şasi öz-sınamaları -----------------
    brk.derisk_mult = _rampa_fn(RAMPA_B["tam_dd"], RAMPA_B["sifir_dd"])
    # yama semantiği (şasi varyant asertleri AYNEN): dd=%10 tam; dd=%20 → 0.7619; dd≥%36 → 0
    assert brk.derisk_mult(90.0, 100.0) == 1.0
    assert abs(brk.derisk_mult(80.0, 100.0) - 0.7619) < 1e-9
    assert brk.derisk_mult(64.0, 100.0) == 0.0
    assert brk.max_positions_at(80.0, 100.0, 5) == 4      # yayılım kanıtı (modül-global çözüm)

    # ---- enjeksiyon öz-sınamaları (GERÇEK motor fonksiyonları, sentetik girdi) ---------------
    _oz_sinama_scaleout(brkmod)
    _oz_sinama_chandelier(backtest.strat, ind)

    # ---- kancalar (şasi AYNEN: sarmalayıcı, motoru DEĞİŞTİRMEZ) ------------------------------
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
            _frame_miss[0] += 1                           # sessiz-yutma DEĞİL: sayılır, geçerliliği bozar
            return n
        date = str(d.date())
        n_acik = len(broker.positions)
        dd = ((peak - equity) / peak) if peak and peak > 0 else 0.0
        rec = {
            "date": date, "bar_i": int(bar_i) if bar_i is not None else None,
            "eq_open": round(float(equity), 2), "peak_equity": round(float(peak), 2),
            "dd": round(float(dd), 6), "base_max_open": int(base_max),
            "eff_max_open": int(n), "n_acik": int(n_acik),
            "acik_slot": int(n) - int(n_acik),
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

    # ---- girdiler + ENJEKSİYON ---------------------------------------------------------------
    stg = yaml.safe_load((st_dir / "strategy.yaml").read_text())
    params = dict(stg["params"])
    by_regime = stg.get("params_by_regime") or None
    sv = int(stg.get("version"))

    # dosya değerleri beklenen mi? (delta kanıtının 'önce' yarısı)
    for k, v in DOSYA_DEGERLERI.items():
        assert float(params[k]) == float(v), f"strategy.yaml {k}={params[k]} beklenen {v} değil"
    # enjeksiyon
    for k, v in hucre["enjeksiyon"].items():
        params[k] = v
    # OAT saflığı: öteki alet/sabitler dosya değerinde KALDI mı?
    for k, v in hucre["sabit_kanit"].items():
        assert float(params[k]) == float(v), f"OAT saflığı bozuk: {k}={params[k]} != {v}"
    # yayılım kanıtı: rejim çözünürlüğü enjeksiyonu dört rejimde de taşıyor
    for rg in ("trend_up", "trend_down", "chop", "high_vol"):
        eff_test = config.resolve_params(params, by_regime, rg)
        for k, v in hucre["enjeksiyon"].items():
            assert eff_test[k] == v, f"resolve_params {rg} enjeksiyonu düşürdü: {k}"

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

    # ---- plan_log çapraz-kontrolü (şasi AYNEN) -----------------------------------------------
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
        r["aday_n"] = r["n_sinyal"]
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

    # ---- işlem/doluluk/performans metrikleri (şasi + hücre eklentileri) ----------------------
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
    hedef_n = exit_dist.get("target", 0) + exit_dist.get("target_gap", 0)
    scaled_n = sum(1 for t in trades if t.get("scaled_out"))

    eff_eq0 = sum(1 for r in sess if r["eff_max_open"] == 0)
    eff_eq1 = sum(1 for r in sess if r["eff_max_open"] == 1)
    eff_lt = sum(1 for r in sess if r["eff_max_open"] < max_open)
    slot_le0 = sum(1 for r in sess if r["acik_slot"] <= 0)
    dd_gt_tam = sum(1 for r in sess if r["dd"] > RAMPA_B["tam_dd"])
    size0 = sum(1 for r in sess if r["size_mult"] <= 0.0)

    tavan_pct_bir = round(100.0 * sum(1 for r in birincil if r["sinif"] == "tavan_sifir")
                          / n_bir, 2) if n_bir else None

    out = {
        "kart": "EDG-2026-027", "faz": "FAZ-1 (B-taban)", "hucre": run,
        "trial_id": hucre["trial_id"], "smoke": smoke,
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sure_sn": sure,
        "rampa_B": {**RAMPA_B,
                    "enjeksiyon": "MONKEYPATCH — şasi EDG-023 varyant beyanı AYNEN (B paramlarının parçası)"},
        "enjeksiyon": {
            "degerler": hucre["enjeksiyon"],
            "dosya_once": {k: DOSYA_DEGERLERI[k] for k in
                           set(DOSYA_DEGERLERI) & (set(hucre["enjeksiyon"]) | set(hucre["sabit_kanit"]))},
            "sabit_kanit": hucre["sabit_kanit"],
            "beyan": ("PARAMS-SÖZLÜĞÜ ENJEKSİYONU — strategy.yaml DOSYASI ve motor DOSYALARI "
                      "değişmedi; mekanizma motorda mevcut ve paramla kapalıydı (broker.py:529 "
                      "scale_out, strategy.py:1101 chandelier). Yayılım motorun kendi param yolu "
                      "(prev_eff/resolve_params); dört rejim için resolve_params kanıtı + gerçek "
                      "motor fonksiyonlarıyla öz-sınama koşum öncesi geçti."),
        },
        "motor_sha256_16": motor_sha,
        "motor_sha_esit_edg023": True,                    # _motor_sha_dogrula assert'i geçti
        "config_sha256_16": {f: {"sandbox": _sha(st_dir / f),
                                 "edg022": _sha(EDG022 / "state" / f),
                                 "edg023_civi": EDG023_CONFIG_SHA[f],
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
            "yasakli_modul_yuklendi": yasak_yuklu,
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
            "hedef_n": hedef_n,
            "hedef_orani_pct": round(100.0 * hedef_n / n_islem, 2) if n_islem else None,
            "scaled_out_n": scaled_n,
            "scaled_out_pct": round(100.0 * scaled_n / n_islem, 2) if n_islem else None,
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

    ek = "_smoke" if smoke else ""
    (outdir / f"sonuc_{run}{ek}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str))
    (outdir / f"seanslar_{run}{ek}.json").write_text(
        json.dumps(sess, ensure_ascii=False, default=str))
    # slim satırlara scaled_out EKLİ (şasiden tek fark: scale-out erişim oranının okuyucusu birlestir)
    slim = [{k: t.get(k) for k in ("ts_open", "ts_close", "ticker", "r_multiple",
                                   "pnl_dollars", "exit_reason", "bars_held", "regime",
                                   "setup", "qty", "scaled_out")} for t in trades]
    (outdir / f"islemler_{run}{ek}.json").write_text(
        json.dumps(slim, ensure_ascii=False, default=str))

    print(f"\n=========== EDG-027 KOŞUM [{run}{ek}] ===========")
    print(f"replay {r_start}→{r_end}  sv={sv}  sembol={len(bars)}  süre={sure}s")
    print(f"enjeksiyon: {hucre['enjeksiyon']}")
    print(f"bütünlük geçerli={out['butunluk']['gecerli']}  frame_miss={_frame_miss[0]} "
          f"dup={len(_dup)} scan!=plan={len(scan_vs_plan)} yasak={yasak_yuklu}")
    print(f"işlem n={n_islem} ({out['islem']['islem_yil']}/yıl)  net_pnl={net_pnl_equity}  "
          f"maxdd_kanonik={detail.get('max_drawdown')}  avg_r={detail.get('avg_r')}")
    print(f"çıkışlar: {out['islem']['exit_reason_dagilim']}")
    print(f"hedef oranı %{out['islem']['hedef_orani_pct']}  scaled_out n={scaled_n}")
    print(f"yazıldı: {outdir}/sonuc_{run}{ek}.json")


# ---------------------------------------------------------------------------------------------
# EŞLİ KIYAS MAKİNESİ — (ts_open, ticker) anahtarlı; tarih-kümeli eşlenik bootstrap
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


def _esli_analiz(islem_B: list[dict], islem_H: list[dict]) -> dict:
    import numpy as np
    mB, dupB = _anahtar_haritasi(islem_B)
    mH, dupH = _anahtar_haritasi(islem_H)
    ortak = sorted(set(mB) & set(mH))
    n = len(ortak)

    ciftler = []
    for k in ortak:
        rB = float(mB[k]["r_multiple"])
        rH = float(mH[k]["r_multiple"])
        ciftler.append({"tarih": k[0], "fark": rH - rB,
                        "cB": str(mB[k]["exit_reason"]), "cH": str(mH[k]["exit_reason"]),
                        "soH": bool(mH[k].get("scaled_out"))})

    farklar = np.array([c["fark"] for c in ciftler]) if ciftler else np.array([])
    gecis: dict[str, int] = {}
    for c in ciftler:
        key = f"{c['cB']}→{c['cH']}"
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

    # scaled alt-küme betimi (BETİM — eşik değil): eşli farkın scale-out'a DOKUNAN çiftlerdeki
    # ve dokunmayanlardaki payı + aynı-bar kuplaj sayacı. Gerekçe (2026-08-12 ham gözlemi):
    # scale_out banking barında trail=entry_fill olur; entry_fill = open×(1+slip) > open
    # olduğundan, banking barı open'ı entry_fill ALTINDA kalan her koşucu AYNI BAR
    # _touch_exit'in o<=eff_stop dalıyla 'stop_gap' okunur (giriş-günü bankalamada DAİMA).
    # Ölçülebilir izi: scaled & bars_held==0 (giriş-günü otomatik kapanış) ve scaled &
    # exit_reason=stop_gap kümeleri. Yorum/hüküm Rol-1'in.
    sc_ciftler = [c for c in ciftler if c["soH"]]
    sc_disi = [c for c in ciftler if not c["soH"]]
    sc_H = [t for t in islem_H if t.get("scaled_out")]
    sc_reason: dict[str, int] = {}
    for t in sc_H:
        sc_reason[str(t["exit_reason"])] = sc_reason.get(str(t["exit_reason"]), 0) + 1
    scaled_betim = {
        "esli_scaled": {"n": len(sc_ciftler),
                        "ort_fark": round(sum(c["fark"] for c in sc_ciftler)
                                          / len(sc_ciftler), 4) if sc_ciftler else None},
        "esli_scaled_disi": {"n": len(sc_disi),
                             "ort_fark": round(sum(c["fark"] for c in sc_disi)
                                               / len(sc_disi), 4) if sc_disi else None,
                             "fark_sifir_disi_n": sum(1 for c in sc_disi if c["fark"] != 0)},
        "tam_defter_scaled": {
            "n": len(sc_H),
            "exit_reason_dagilim": dict(sorted(sc_reason.items(), key=lambda kv: -kv[1])),
            "bars_held_0_n": sum(1 for t in sc_H if int(t.get("bars_held") or 0) == 0),
            "r_060_080_n": sum(1 for t in sc_H if 0.60 <= float(t["r_multiple"]) <= 0.80),
        },
    }

    return {
        "esli_n": n,
        "anahtar_tekrar": {"B": dupB, "H": dupH},        # 0 olmalı (bütünlük)
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
        "scaled_betim": scaled_betim,
        "yalniz_B": _tek_yon(sorted(set(mB) - set(mH)), mB),
        "yalniz_H": _tek_yon(sorted(set(mH) - set(mB)), mH),
    }


# ---------------------------------------------------------------------------------------------
# BİRLEŞTİR — B(EDG-023 hazır) ↔ H1/H2 → eşli CI + tam-defter + kill bayrakları → sonuc.json
# ---------------------------------------------------------------------------------------------
def birlestir():
    # ---- B tabanı: EDG-023'ün HAZIR dosyaları (yeniden koşum YOK; salt-okuma) ----------------
    B_sonuc = json.loads((EDG023 / "sonuc_varyant.json").read_text())
    B_islem = json.loads((EDG023 / "islemler_varyant.json").read_text())
    B_seans = json.loads((EDG023 / "seanslar_varyant.json").read_text())

    # B çivisi: okunan dosya GERÇEKTEN 2026-08-12 varyant koşumu mu?
    assert B_sonuc["kosum"] == "varyant" and not B_sonuc["smoke"]
    assert len(B_islem) == EDG023_B_CIVI["n_islem"], "B islemler dosyası çiviyle uyuşmuyor"
    assert B_sonuc["performans"]["net_pnl_equity"] == EDG023_B_CIVI["net_pnl_equity"]
    assert B_sonuc["performans"]["maxdd_kanonik"] == EDG023_B_CIVI["maxdd_kanonik"]
    assert B_sonuc["motor_sha256_16"] == EDG023_MOTOR_SHA, "B kayıtlı motor sha çiviyle uyuşmuyor"
    motor_guncel = _motor_sha_dogrula()

    # ---- eşli makine öz-kontrolü: B↔B eşlemesi n=410, tüm farklar 0, CI [0,0] ----------------
    kendi = _esli_analiz(B_islem, B_islem)
    assert kendi["esli_n"] == EDG023_B_CIVI["n_islem"] and kendi["anahtar_tekrar"] == {"B": 0, "H": 0}
    assert kendi["ort_fark"] == 0.0 and kendi["fark_pos_n"] == 0 and kendi["fark_neg_n"] == 0
    assert kendi["ci95_tarih_kumeli_eslenik"]["lo"] == 0.0 and \
        kendi["ci95_tarih_kumeli_eslenik"]["hi"] == 0.0

    B_tarihler = [s["date"] for s in B_seans]

    hucre_blok: dict[str, dict] = {}
    kill_ozeti: dict[str, dict] = {}
    for run in HUCRELER:
        H_sonuc = json.loads((SANDBOX / f"sonuc_{run}.json").read_text())
        H_islem = json.loads((SANDBOX / f"islemler_{run}.json").read_text())
        H_seans = json.loads((SANDBOX / f"seanslar_{run}.json").read_text())

        takvim_ayni = ([s["date"] for s in H_seans] == B_tarihler)
        esli = _esli_analiz(B_islem, H_islem)

        butunluk_ok = (H_sonuc["butunluk"]["gecerli"] and takvim_ayni
                       and esli["anahtar_tekrar"] == {"B": 0, "H": 0}
                       and H_sonuc["motor_sha256_16"] == EDG023_MOTOR_SHA)

        pB, pH = B_sonuc["performans"], H_sonuc["performans"]
        iB, iH = B_sonuc["islem"], H_sonuc["islem"]
        nB, nH = int(iB["n"]), int(iH["n"])
        hedef_B_n = (iB["exit_reason_dagilim"].get("target", 0)
                     + iB["exit_reason_dagilim"].get("target_gap", 0))

        tam_defter = {
            "islem_n": {"B": nB, "hucre": nH, "fark": nH - nB,
                        "fark_pct": round(100.0 * (nH - nB) / nB, 1) if nB else None},
            "islem_yil": {"B": iB["islem_yil"], "hucre": iH["islem_yil"]},
            "net_pnl_equity": {"B": pB["net_pnl_equity"], "hucre": pH["net_pnl_equity"],
                               "fark": round(pH["net_pnl_equity"] - pB["net_pnl_equity"], 2)},
            "net_pnl_trades": {"B": pB["net_pnl_trades"], "hucre": pH["net_pnl_trades"]},
            "maxdd_kanonik": {"B": pB["maxdd_kanonik"], "hucre": pH["maxdd_kanonik"]},
            "maxdd_m2m": {"B": pB["maxdd_m2m"], "hucre": pH["maxdd_m2m"]},
            "avg_r": {"B": pB["avg_r"], "hucre": pH["avg_r"]},
            "win_rate": {"B": pB["win_rate"], "hucre": pH["win_rate"]},
            "sharpe": {"B": pB["sharpe"], "hucre": pH["sharpe"]},
            "score": {"B": pB["score"], "hucre": pH["score"]},
            "exit_reason_dagilim": {"B": iB["exit_reason_dagilim"],
                                    "hucre": iH["exit_reason_dagilim"]},
            "hedef_orani_pct": {"B": round(100.0 * hedef_B_n / nB, 2) if nB else None,
                                "hucre": iH["hedef_orani_pct"]},
            "scaled_out": {"B": {"n": 0, "not": "frac=0 — alet kapalı (tanım gereği)"},
                           "hucre": {"n": iH["scaled_out_n"], "pct": iH["scaled_out_pct"]}},
            "doluluk_pozisyon_gun": {"B": B_sonuc["doluluk"]["pozisyon_gun_open_fazi"],
                                     "hucre": H_sonuc["doluluk"]["pozisyon_gun_open_fazi"]},
            "ort_acik_pozisyon": {"B": B_sonuc["doluluk"]["ort_acik_pozisyon"],
                                  "hucre": H_sonuc["doluluk"]["ort_acik_pozisyon"]},
            "toplam_bars_held": {"B": B_sonuc["doluluk"]["toplam_bars_held"],
                                 "hucre": H_sonuc["doluluk"]["toplam_bars_held"]},
            "silahlanan_plan": {"B": iB["silahlanan_plan"], "hucre": iH["silahlanan_plan"]},
            "toplam_plan": {"B": iB["toplam_plan"], "hucre": iH["toplam_plan"]},
            "entry_rejects": {"B": iB["entry_rejects"], "hucre": iH["entry_rejects"]},
        }

        hucre_blok[run] = {
            "trial_id": HUCRELER[run]["trial_id"],
            "enjeksiyon": H_sonuc["enjeksiyon"]["degerler"],
            "sure_sn": H_sonuc["sure_sn"],
            "butunluk_hucre": H_sonuc["butunluk"],
            "takvim_ayni_B": takvim_ayni,
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
        "faz": "FAZ-1 — yalnız B-taban hücreleri (C hücreleri ayrı fazda; kill#3/C bu fazın dışında)",
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "yontem": {
            "esli_anahtar": "(ts_open[:10], ticker) — girişler değişmediği için aynı pozisyonun iki dünyadaki R'si",
            "esli_R": "satırın r_multiple'ı — scale-out'ta birleşik (banked+kalan; broker.close_position tek satır)",
            "esli_ci": ("işlem-TARİH-kümeli eşlenik bootstrap: kümeler eşli kümenin ayrık ts_open "
                        f"tarihleri; yerine-koymalı; iter={BOOT_ITER}, seed={BOOT_SEED}; "
                        "fark=hücre−B; ay-kümeli CI yan-tablo (ikinci eşik değil)"),
            "taban_B": ("EDG-023 varyant (rampa 15/36) HAZIR çıktıları — yeniden koşulmadı; "
                        "sha çivileri + n/pnl/dd çivileriyle doğrulandı"),
            "esli_makine_kontrolu": "B↔B öz-eşleme: n=410, tüm farklar 0, CI [0,0] — assert geçti",
        },
        "sha_dogrulama": {
            "motor_guncel": motor_guncel,
            "edg023_civi": EDG023_MOTOR_SHA,
            "hucre_kayitlari_esit": all(
                json.loads((SANDBOX / f"sonuc_{r}.json").read_text())["motor_sha256_16"]
                == EDG023_MOTOR_SHA for r in HUCRELER),
            "config_civi": EDG023_CONFIG_SHA,
        },
        "taban_B_ozet": {
            "kaynak": str(EDG023),
            "islem_n": len(B_islem),
            "performans": B_sonuc["performans"],
            "exit_reason_dagilim": B_sonuc["islem"]["exit_reason_dagilim"],
            "butunluk": B_sonuc["butunluk"],
        },
        "hucreler": hucre_blok,
        "kill_bayraklari": kill_ozeti,
        "dosyalar": {
            "B": {"sonuc": str(EDG023 / "sonuc_varyant.json"),
                  "islemler": str(EDG023 / "islemler_varyant.json"),
                  "seanslar": str(EDG023 / "seanslar_varyant.json")},
            **{r: {"sonuc": f"sonuc_{r}.json", "seanslar": f"seanslar_{r}.json",
                   "islemler": f"islemler_{r}.json"} for r in HUCRELER},
        },
    }
    (SANDBOX / "sonuc.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))

    print("\n==================== EDG-027 FAZ-1 B↔{H1,H2} ÖZET ====================")
    for run, blok in hucre_blok.items():
        e = blok["esli"]
        t = blok["tam_defter"]
        print(f"\n--- {run}  enjeksiyon={blok['enjeksiyon']}")
        print(f"  şasi geçerli={blok['kill2_sasi_gecerli']}  takvim_ayni={blok['takvim_ayni_B']}")
        print(f"  eşli n={e['esli_n']} (kill#1={e['kill1_esli_lt_min']})  "
              f"ort_fark={e['ort_fark']}  CI95_tarih={e['ci95_tarih_kumeli_eslenik']}")
        print(f"  eşli +/-/0: {e['fark_pos_n']}/{e['fark_neg_n']}/{e['fark_sifir_n']}  "
              f"yalnızB={e['yalniz_B']['n']} yalnızH={e['yalniz_H']['n']}")
        print(f"  işlem n: {t['islem_n']}  net_pnl: {t['net_pnl_equity']}")
        print(f"  maxdd_kanonik: {t['maxdd_kanonik']}  avg_r: {t['avg_r']}")
        print(f"  hedef oranı: {t['hedef_orani_pct']}  scaled_out: {t['scaled_out']['hucre']}")
    print(f"\nyazıldı: {SANDBOX / 'sonuc.json'}")
    print("======================================================================\n")


if __name__ == "__main__":
    mod = sys.argv[1] if len(sys.argv) > 1 else ""
    smoke = "--smoke" in sys.argv
    if mod in HUCRELER:
        kosum(mod, smoke=smoke)
    elif mod == "birlestir":
        assert not smoke, "smoke'ta birlestir yok (B tabanının smoke çıktısı yok; B yeniden koşulmaz)"
        birlestir()
    else:
        sys.exit("kullanım: olcum.py {h1_scaleout|h2_chandelier|birlestir} [--smoke]")

"""EDG-2026-033 — REJİM-KOŞULLU BOYUT (işlem-başı risk çarpanı rejim sınıfına göre) · ölçüm aracı (2026-08-12)

Kart: research/cards/EDG-2026-033-rejim-kosullu-boyut.yaml (OKU-DOKUNMA; hüküm Rol-1'in).
Rol: ÖLÇÜM ajanı. Bu modül HÜKÜM VERMEZ, karta dokunmaz, git/canlı/broker/state'e YAZMAZ.

ŞASİ: EDG-026 (research/olcumler/edg026_slot20_2026-08-12/olcum.py) C-dünyası AYNEN devralındı:
izole sandbox (EDG-022 donmuş config kopyaları + bars symlink SALT-OKUNUR), rampa-15/36
monkeypatch'i (beyanlı, 023 deseni), slot-20 + 0.5R-taban param-enjeksiyonları, kancalar, bütünlük
kontrolleri, eşlenik ay-kümeli bootstrap (5000 iter, seed 20260812). KIYAS TABANI = EDG-026'nın
HAZIR C çıktıları (sonuc_c/seanslar_c/islemler_c — YENİDEN KOŞULMAZ, salt-okunur; sha256 kaydedilir).
Rejim-kırılım karnesi + işlem-kümesi eşlemesi EDG-030 deseninden devralındı.

İKİ HÜCRE + KONTROL (kart features_asof, DONUK — rejim başına MUTLAK position_size_r):
  kontrol         : {trend_up 0.5, trend_down 0.5, chop 0.5, high_vol 0.5}  (çarpan≡1.0 — hücre DEĞİL,
                    şasi-sınaması; YALNIZ smoke penceresi; C ile BİT-ÖZDEŞLİK ŞART — kill#1)
  h1 yukari_asimetri : {trend_up 0.75, diğerleri 0.5}   (çarpan: trend_up 1.5×, diğer 1.0×)
  h2 tam_modulasyon  : {trend_up 0.75, diğerleri 0.35}  (çarpan: trend_up 1.5×, diğer 0.7×)
  H2 kart dili "açık-ama-trend_up-olmayan 0.35R"dir: kapalı-rejim seanslarında giriş taranmaz
  (backtest.py:295 `exposure_budget_pct > 0` kapısı) → trend_up-dışı TÜM rejimlere 0.35 atamak
  yalnız AÇIK seanslarda tüketilir; anlam birebir karttır. (C defteri çaprazı: işlemler yalnız
  trend_up+chop altında; trend_down/high_vol ataması fiilen atıldır, beyanlıdır.)

BOYUT-ÇARPANI ENJEKSİYON YÜZEYİ — KEŞİF BEYANI + KANIT (kart: "TEK kanonik yüzeyde BEYANLI
monkeypatch (position_size_r tüketim noktası — ajan yüzeyi keşfeder, tek nokta, öz-sınamalı)"):
  * KEŞİF: position_size_r'nin TÜKETİM noktası strateji params yüzeyidir — strategy.py
    487/553/610/669/774/851/978 `_f(params,"position_size_r",1.0)`; hepsi evaluate_* GİRİŞ
    fonksiyonlarında (scan_entry yolu). manage_position / scale_out / broker / guard bu anahtarı
    OKUMAZ (grep taraması: meridian/ altında başka tüketici yok; broker.py:15 yorum,
    config.py:286 varsayılan, recompute.py canlı-yol). Replay'de scan_entry'ye giden params =
    backtest.py:278 `eff = config.resolve_params(params, params_by_regime, rj["regime"])` —
    yani motorun KENDİ rejim-koşullu çözüm noktası ZATEN TEK kanonik yüzeydir ve seans rejimini
    motorun KENDİ sınıflayıcısından (regime.build_regime_json → rj["regime"]) alır. Plan boyutu
    `min(sig.size_r, max_position_r=1.0)` ile yalnız yukarı kırpılır (backtest.py:352; 0.75
    kırpılmaz — koşum öncesi assert). İşlem kaydındaki `regime` alanı = plan günü rj["regime"]
    (backtest.py:354 regime_at_plan) — boyutlandırmanın anahtarlandığı DEĞERİN KENDİSİ.
  * DOLAYISIYLA MONKEYPATCH GEREKMEDİ (EDG-030 emsali: param yüzeyi tüketim noktasına ulaşıyorsa
    enjeksiyon sözlük girdisidir, motor yamasız kalır): enjeksiyon = params_by_regime derin
    kopyasına rejim başına `position_size_r` anahtarı (TEK nokta). Donmuş strategy.yaml
    params_by_regime = {4 rejim: {}} (koşum öncesi assert: dördü de BOŞ) → çakışan override yok.
    resolve_params overlay kuralı `k in params` → position_size_r flat params'ta VAR → uygulanır.
  * ÖZ-SINAMA 1 (koşum öncesi): dört rejimde resolve_params(params, enjekte, rejim)
    ["position_size_r"] == hücre haritası; position_size_r DIŞINDA eff == params (TEK-ANAHTAR
    yüzey kanıtı); bilinmeyen rejimde taban 0.5 döner (beyan).
  * ÖZ-SINAMA 2 (koşum içi, her scan çağrısı): _scan kancası motorun scan_entry'ye GEÇİRDİĞİ
    params'ın position_size_r'sini o seansın rejimi için beklenen değerle karşılaştırır; ihlal
    sayısı bütünlük kaydına girer (0 olmalı).
  * ÖZ-SINAMA 3 (koşum sonrası, plan düzeyi): TÜM plan_log satırlarında
    size_r / harita[regime_at_plan] ∈ [0.598, 1.002] (conviction 0.6-1.0× + 3hane yuvarlama
    bandı); ihlal sayısı bütünlük kaydına girer (0 olmalı) — modülasyonun uca ulaştığının kanıtı.
    İŞLEM-düzeyi bant kanıtı ÖLÇÜLEMEZ: kapanmış-işlem satırında size_r/risk_dollars alanı YOK
    (026 slim şeması null taşır — C defterinde de null; motor closed-satırı bu alanları yazmaz).
    Her dolum aynı günün silahlı planından geldiği için işlem-düzeyi kanıt plan-düzeyinden
    devralınır; dolar-boyut izi ayrıca eşleşen-işlem qty-oranlarında görünür (ayrışım bölümü).

ZARF SABİT — BEYAN: heat_hard_r=5.0R, heat_review_r=3.5R, max_position_r=1.0,
max_sector_exposure_pct=40, slot=20, rampa 15/36 DEĞİŞMEDİ (kart: zarf 5R dokunulmaz). 0.75R
planların ısıyı hızlı tüketmesi ve heat-NO_GO/yer-değiştirme desenleri bu ÖLÇÜMÜN BULGUSUdur.

TANIMLAR (ölçümden ÖNCE donduruldu; sonuç görüldükten sonra değişmez):
  islem              = kapanmış işlem satırı (broker.closed; eod/delisted markout DAHİL).
  islem kimliği      = (ts_open[:10], ticker) — hücre↔C işlem-kümesi eşlemesi bu anahtarla.
  ORTAK/EKLENEN/ÇIKAN= iki tarafta da var / yalnız hücrede / yalnız C'de.
  yol-aynı ortak     = ts_close[:10] VE exit_reason aynı VE |Δr_multiple| ≤ 1e-9 (aksi yol-kayan).
  saf-boyut ayrışımı = Δ(Σpnl) ≡ Σeklenen + Σortak_Δ − Σçıkan; ortak_Δ üç kovaya TAM bölünür:
                       yol-aynı∧trend_up (amaçlanan boyut etkisi + equity-sürüklenmesi),
                       yol-aynı∧trend_up-dışı (H1'de saf equity-sürüklenmesi; H2'de boyut+sürüklenme),
                       yol-kayan (knock-on). Kalıntı raporlanır; |kalıntı| ≤ 0.01$ beklenir
                       (sente kapanan). qty_oran = qty_hücre/qty_C (yol-aynı çiftlerde, kova başına).
  ay kümesi          = ts_open[:7] (giriş ayı); ay evreni = seans takviminin TÜM ayları.
  eşlenik fark CI    = ay-kümeli EŞLENİK bootstrap (aylar yerine-koymalı, 5000 iter, seed 20260812;
                       AYNI ay çekilişi iki koşuma birden): işlem n farkı, net P&L farkı
                       (Σ pnl_dollars), sharpe farkı, max-dd farkı, REJİM-BAŞINA P&L farkı.
  bootstrap sharpe   = kanonik score.score_detail formülüyle iterasyon içi yeniden hesap (030 AYNEN);
                       n≤2 veya std=0 → iterasyon atlanır (sayısı raporlanır).
  bootstrap max-dd   = kanonik score.equity_curve (ts_close sıralı) + score.max_drawdown (030 AYNEN;
                       ay yeniden-örneklemesi dd zaman-sırasını yapay kurar — CI bu beyanla okunur).
  rejim-kırılım karne= işlem kaydındaki `regime` alanı (plan günü rejimi — motor kaydı, 030 deseni):
                       rejim başına n / ort-R / medyan-R / pnl / kazanma-oranı, C ve hücre yan yana.
  ısı-kullanım profili= şasi tepe_isi bloğu (nominal + GERÇEKLEŞEN Σsize_r/risk$) + seans-rejimi
                       kırılımlı gerçekleşen ısı özeti + heat_hard NO_GO sayıları + silahlı plan
                       size_r dağılımı (rejim başına).
  rejim kimliği      = build_regime_json portföy durumundan BAĞIMSIZDIR (endeks + params + tarih) →
                       her seansta hücre rejimi VE bütçesi C ile BİREBİR aynı olmalı (şasi çaprazı).
  bit-özdeşlik (kontrol) = seanslar+islemler dosyaları BAYT-AYNI (sha256) VE sonuc'un ekonomik
                       bölümleri [replay, butunluk, islem, performans, doluluk, tepe_isi, betim,
                       tasnif_tum_seans, birincil, ci95_ay_kumeli] sözlük-eşit (026 smoke C'ye karşı).
  max-dd (nokta)     = motor-kanonik score.score_detail.max_drawdown; kartın dd koşulu (C×1.3,
                       success_metric — HÜKÜM GİRDİSİ) bunun üstünden kaydedilir, hüküm yazılmaz.

KILL KONTROLLERİ (kart, DONUK — koşul değerinin kaydı, hüküm DEĞİL):
  kill#1: kontrol bit-özdeşliği düşerse ölçüm GEÇERSİZ (yama yüzeyi yan-etkili).
  kill#2: taban-defterde (C islemler_c) trend_up işlem n < 30 → olculemedi.
  kill#3: şasi bütünlüğü bozuksa GEÇERSİZ (koşum-içi kontroller + çarpan öz-sınamaları +
          motor/config sha == C + takvim + rejim-kimliği).

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen = None + neden); YASA-4 (sessiz-yutma işaretli + gerekçe);
YASA-6 (okuyucu: sonuc_h*/seanslar_h*/islemler_h* → `kiyas` tüketir; sonuc.json → dönüş raporu +
Rol-1). SALT-OKUMA: config.STATE koşum-başına izole sandbox; canlı state'e ve motor dosyalarına tek
bayt yazılmaz. meridian.loop / counterfactual / cf_backfill / hermes İTHAL EDİLMEZ — sys.modules
ile KANITLANIR.

KULLANIM:
  olcum.py kontrol               # çarpan≡1.0, ZORUNLU smoke penceresi + C bit-özdeşlik kıyası
  olcum.py kosum h1 [--smoke]    # hücre yukari_asimetri → sonuc_h1 + seanslar_h1 + islemler_h1
  olcum.py kosum h2 [--smoke]    # hücre tam_modulasyon
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
SMOKE_END = "2022-06-30"                       # 026 smoke penceresi AYNEN (≥3 ay — kart koşulu)
BOOT_SEED = 20260812
BOOT_ITER = 5000

# C dünyasının DONUK parametreleri (026'dan AYNEN — hücreler yalnız rejim-koşullu boyutu ekler)
RAMPA = {"tam_dd": 0.15, "sifir_dd": 0.36}
SLOT = 20
BOYUT_R = 0.5                                  # taban (C dünyası; flat params enjeksiyonu)
REGIMES = ("trend_up", "trend_down", "chop", "high_vol")   # config.VALID_REGIMES (motor sözlüğü)

# hücre haritaları: rejim → MUTLAK position_size_r (kart features_asof, DONUK)
HUCRELER: dict[str, dict[str, float]] = {
    "kontrol": {"trend_up": 0.5, "trend_down": 0.5, "chop": 0.5, "high_vol": 0.5},
    "h1": {"trend_up": 0.75, "trend_down": 0.5, "chop": 0.5, "high_vol": 0.5},
    "h2": {"trend_up": 0.75, "trend_down": 0.35, "chop": 0.35, "high_vol": 0.35},
}
HUCRE_AD = {"kontrol": "kontrol_carpan1", "h1": "yukari_asimetri", "h2": "tam_modulasyon"}
KILL2_TREND_UP_MIN = 30                        # kart kill#2: taban-defter trend_up n
DD_KOSUL_KATSAYI = 1.3                         # kart success_metric: dd ≤ C×1.3 (HÜKÜM GİRDİSİ)
CARPAN_BAND = (0.598, 1.002)                   # size_r/harita[rejim] bandı (conviction 0.6-1.0 + yuvarlama)

KART3 = ["tavan_sifir", "evren_bagladi", "derisk_bagladi"]
YASAK = ("meridian.loop", "meridian.counterfactual", "meridian.cf_backfill", "meridian.hermes")

# bit-özdeşlik sonuc bölümleri (kontrol tanımı — başlıkta donduruldu)
BIT_BOLUMLER = ("replay", "butunluk", "islem", "performans", "doluluk", "tepe_isi",
                "betim", "tasnif_tum_seans", "birincil", "ci95_ay_kumeli")

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
            # DOSYALAR DEĞİŞTİRİLMEZ: slot/boyut/çarpan enjeksiyonu YÜKLENMİŞ sözlüklere yapılır ki
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
# SINIFLAMA + seans-CI + ısı yardımcıları — EDG-022/026 DONUK kuralları AYNEN
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


def _isi_rejim_kirilimi(sess: list[dict]) -> dict:
    """Seans-rejimi kırılımlı GERÇEKLEŞEN ısı (Σ açık size_r) + doluluk — kart 'ısı-kullanım
    profili' merceği. Girdi: 026 şemalı seans kayıtları (regime + acik_size_r_toplam alanları)."""
    gruplar: dict[str, list[dict]] = {}
    for r in sess:
        gruplar.setdefault(str(r.get("regime")), []).append(r)
    out = {}
    for rg in sorted(gruplar, key=lambda k: -len(gruplar[k])):
        rs = gruplar[rg]
        out[rg] = {"seans_n": len(rs),
                   "gerceklesen_size_r": _isi_ozet([r["acik_size_r_toplam"] for r in rs]),
                   "ort_acik_pozisyon": round(sum(r["n_acik"] for r in rs) / len(rs), 3)}
    return out


# ---------------------------------------------------------------------------------------------
# HÜCRE KOŞUMU (kontrol | h1 | h2) — 026 kosum() düzeni + rejim-koşullu boyut enjeksiyonu
# ---------------------------------------------------------------------------------------------
def kosum(hucre: str, smoke: bool = False):
    assert hucre in HUCRELER, f"hücre {hucre} tanımsız (kontrol|h1|h2)"
    assert hucre != "kontrol" or smoke, "kontrol YALNIZ smoke penceresinde koşar (kart: şasi-sınaması)"
    HARITA = dict(HUCRELER[hucre])
    outdir = (SANDBOX / "smoke") if smoke else SANDBOX
    outdir.mkdir(exist_ok=True)
    r_start, r_end = (REPLAY_START, SMOKE_END) if smoke else (REPLAY_START, REPLAY_END)

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

    # ---- girdiler + PARAM-ENJEKSİYONLARI (dosya DEĞİŞMEZ; 026 ikilisi + rejim-koşullu boyut) -
    stg = yaml.safe_load((st_dir / "strategy.yaml").read_text())
    params = dict(stg["params"])
    by_regime_orij = stg.get("params_by_regime")
    sv = int(stg.get("version"))
    goal = config.goal()                                   # derin kopya — dosyaya/önbelleğe sızmaz

    onceki = {"max_open_positions": int(goal["limits"]["max_open_positions"]),
              "position_size_r": float(params["position_size_r"])}
    goal["limits"]["max_open_positions"] = SLOT            # ENJEKSİYON 1 (C dünyası — 026 AYNEN)
    params["position_size_r"] = BOYUT_R                    # ENJEKSİYON 2 (C dünyası — 026 AYNEN)

    # ---- ENJEKSİYON 3 (BU KARTIN değişkeni): params_by_regime derin kopyası + rejim→boyut ----
    # Donmuş strategy.yaml haritası {4 rejim: {}} olmalı — DOLU gelirse şasi başka bir dünyadır.
    assert isinstance(by_regime_orij, dict) and set(by_regime_orij.keys()) == set(REGIMES), \
        f"params_by_regime şeması beklenmedik: {by_regime_orij}"
    for _rg in REGIMES:
        assert not (by_regime_orij.get(_rg) or {}), \
            f"params_by_regime[{_rg}] BOŞ değil — donmuş şasi varsayımı bozuk"
    by_regime_inj = {rg: {"position_size_r": HARITA[rg]} for rg in REGIMES}

    # ---- ÇARPAN ÖZ-SINAMASI 1 (koşum öncesi): çözüm + tek-anahtar yüzey kanıtı ---------------
    for _rg in REGIMES:
        _eff = config.resolve_params(params, by_regime_inj, _rg)
        assert float(_eff["position_size_r"]) == HARITA[_rg], \
            f"resolve_params[{_rg}] {_eff['position_size_r']} != {HARITA[_rg]}"
        _a = {k: v for k, v in _eff.items() if k != "position_size_r"}
        _b = {k: v for k, v in params.items() if k != "position_size_r"}
        assert _a == _b, f"TEK-ANAHTAR yüzey ihlali: {_rg} rejiminde başka anahtar değişti"
    assert float(config.resolve_params(params, by_regime_inj, "bilinmeyen_rejim")
                 ["position_size_r"]) == BOYUT_R           # sözlük-dışı rejim → taban (beyan)
    assert float(goal["limits"]["max_position_r"]) >= max(HARITA.values()), \
        "max_position_r hücre boyutunu kırpar — yüzey varsayımı bozuk"
    oz1 = {"gecti": True,
           "harita": HARITA,
           "beyan": ("enjeksiyon = params_by_regime derin-kopya sözlük girdisi (TEK nokta; motor "
                     "yamasız — EDG-030 emsali). resolve_params dört rejimde haritayı döndürdü; "
                     "position_size_r DIŞINDA eff==params (tek-anahtar yüzey); bilinmeyen rejim "
                     "tabana düşer; max_position_r=1.0 kırpmaz")}
    limits = goal["limits"]
    max_open = int(limits["max_open_positions"])
    no_trade_before = int(limits.get("no_trade_before_bars", 0))
    assert max_open == SLOT

    # ---- kancalar (026 deseni AYNEN — seans şeması 026 İLE BİREBİR; bit-özdeşlik koşulu) -----
    seans_by_date: dict[str, dict] = {}
    _cur_close_date = [None]
    _dup: list[str] = []
    _frame_miss = [0]
    _carpan_ihlal: list[dict] = []        # ÖZ-SINAMA 2: scan params boyutu != rejim beklentisi (0 olmalı)

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
        # ÖZ-SINAMA 2: motorun scan_entry'ye geçirdiği eff'in boyutu == seans rejiminin haritası
        _ps = a[1].get("position_size_r") if (len(a) > 1 and isinstance(a[1], dict)) else None
        _rg = rec.get("regime") if rec is not None else None
        _bek = HARITA.get(str(_rg)) if _rg is not None else None
        if _bek is None or _ps != _bek:
            if len(_carpan_ihlal) < 20:
                _carpan_ihlal.append({"date": _cur_close_date[0], "regime": _rg,
                                      "gorulen": _ps, "beklenen": _bek})
            else:
                _carpan_ihlal.append({})            # sayaç büyür, örnek saklanmaz (ilk 20 yeter)
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
                          strategy_version=sv, params_by_regime=by_regime_inj,
                          with_gate_detail=False)
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

    # ---- ÇARPAN ÖZ-SINAMASI 3 (koşum sonrası): plan + işlem boyut bandı ----------------------
    plan_band_ihlal: list[dict] = []
    plan_rejim_size: dict[str, list[float]] = {}
    silahli_rejim_size: dict[str, list[float]] = {}
    for p in (res.plan_log or []):
        rg = str(p.get("regime_at_plan"))
        sr = float(p.get("size_r") or 0.0)
        plan_rejim_size.setdefault(rg, []).append(sr)
        if p.get("gate_verdict") != "NO_GO":
            silahli_rejim_size.setdefault(rg, []).append(sr)
        s0 = HARITA.get(rg)
        oranp = (sr / s0) if s0 else None
        if oranp is None or not (CARPAN_BAND[0] <= oranp <= CARPAN_BAND[1]):
            if len(plan_band_ihlal) < 20:
                plan_band_ihlal.append({"date": p.get("date"), "ticker": p.get("ticker"),
                                        "regime": rg, "size_r": sr, "beklenen_taban": s0})
            else:
                plan_band_ihlal.append({})
    trades = res.trades or []
    # İŞLEM-düzeyi bant kanıtı ÖLÇÜLEMEZ (None + neden — UYDURMA YASAĞI): kapanmış-işlem satırı
    # size_r/risk_dollars taşımaz (026 slim şeması null; motor closed-satırı yazmaz). Kanıt zinciri:
    # scan-params (öz-sınama 2) → plan size_r bandı (öz-sınama 3) → dolum aynı günün silahlı planından.
    islem_band_neden = ("olculemedi: closed-islem satırında size_r alanı yok (026 şeması null) — "
                        "kanıt plan-düzeyinden devralınır")

    def _size_ozet(v: list[float]) -> dict | None:
        if not v:
            return None
        return {"n": len(v), "min": round(min(v), 3), "max": round(max(v), 3),
                "ort": round(sum(v) / len(v), 3)}

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

    # ---- işlem/doluluk/ısı/performans (026 AYNEN — bölüm şekilleri bit-özdeşlik koşulu) ------
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
                        and not yasak_yuklu and not base_max_bozuk
                        and not _carpan_ihlal and not plan_band_ihlal)

    out = {
        "kart": "EDG-2026-033", "kosum": f"{hucre}_{HUCRE_AD[hucre]}", "hucre": hucre, "smoke": smoke,
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sure_sn": sure,
        "rampa": {"tam_dd": RAMPA["tam_dd"], "sifir_dd": RAMPA["sifir_dd"],
                  "enjeksiyon": "MONKEYPATCH (beyanlı — 023/026 deseni AYNEN; motor DOSYASI değişmedi)"},
        "param_enjeksiyon": {
            "max_open_positions": {"once": onceki["max_open_positions"], "sonra": SLOT,
                                   "yuzey": "goal['limits'] (026 C dünyası AYNEN)"},
            "position_size_r": {"once": onceki["position_size_r"], "sonra": BOYUT_R,
                                "yuzey": "strateji params sözlüğü — TABAN (026 C dünyası AYNEN)"},
            "zarf_sabit": ("heat_hard_r=5.0R, heat_review_r=3.5R, max_position_r=1.0, "
                           "max_sector_exposure_pct=40, slot=20, rampa 15/36 DEĞİŞMEDİ "
                           "(kart: zarf 5R dokunulmaz; kalan kaldıraç yalnız rejim-koşullu boyut)"),
        },
        "carpan_enjeksiyon": {
            "harita_mutlak_size_r": HARITA,
            "carpan_tabana_gore": {rg: round(HARITA[rg] / BOYUT_R, 3) for rg in REGIMES},
            "yuzey": ("params_by_regime derin-kopya sözlük girdisi → config.resolve_params "
                      "(backtest.py:278, motorun KENDİ rejim-koşullu çözüm noktası; rejim = "
                      "rj['regime'] motorun KENDİ sınıflayıcısından) → eff → scan_entry "
                      "(strategy.py _f 'position_size_r' — tek tüketim yüzeyi; giriş fonksiyonları "
                      "dışında okunmaz). MONKEYPATCH GEREKMEDİ — motor yamasız (030 emsali); "
                      "beyan modül başlığında"),
            "orijinal_params_by_regime_bos": True,   # koşum öncesi assert edildi
        },
        "carpan_oz_sinama": {
            "1_cozum_ve_tek_anahtar": oz1,
            "2_scan_cagri_ihlal": {"n": len(_carpan_ihlal), "ornek": [x for x in _carpan_ihlal[:20] if x]},
            "3_plan_bandi": {
                "band": list(CARPAN_BAND),
                "plan_ihlal_n": len(plan_band_ihlal), "plan_ornek": [x for x in plan_band_ihlal[:20] if x],
                "islem_duzeyi": None, "islem_duzeyi_neden": islem_band_neden,
                "beyan": ("TÜM plan_log satırlarında size_r/harita[regime_at_plan] ∈ band "
                          "(conviction 0.6-1.0 + 3hane yuvarlama) — modülasyon uca ulaştı kanıtı; "
                          "işlem-düzeyi plan-düzeyinden devralınır (dolum = aynı günün silahlı planı)")},
            "plan_size_r_rejim": {rg: _size_ozet(v) for rg, v in sorted(plan_rejim_size.items())},
            "silahli_size_r_rejim": {rg: _size_ozet(v) for rg, v in sorted(silahli_rejim_size.items())},
        },
        "motor_sha256_16": {f: _sha(REPO / "meridian" / f)
                            for f in ("broker.py", "backtest.py", "strategy.py", "regime.py",
                                      "guard.py", "score.py")},
        "config_sha256_16": {f: {"sandbox": _sha(st_dir / f),
                                 "edg022": _sha(EDG022 / "state" / f)}
                             for f in ("goal.yaml", "strategy.yaml", "bounds.yaml")},
        "replay": {"start": r_start, "end": r_end, "strategy_version": sv,
                   "params_by_regime": bool(by_regime_inj), "n_sembol": len(bars),
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
        "isi_rejim_kirilimi": _isi_rejim_kirilimi(sess),
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
    (outdir / f"sonuc_{hucre}{ek}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str))
    (outdir / f"seanslar_{hucre}{ek}.json").write_text(
        json.dumps(sess, ensure_ascii=False, default=str))
    slim = [{k: t.get(k) for k in ("ts_open", "ts_close", "ticker", "r_multiple",
                                   "pnl_dollars", "exit_reason", "bars_held", "regime",
                                   "setup", "qty", "risk_dollars", "size_r")} for t in trades]
    (outdir / f"islemler_{hucre}{ek}.json").write_text(
        json.dumps(slim, ensure_ascii=False, default=str))

    print(f"\n=========== EDG-033 KOŞUM [{hucre}_{HUCRE_AD[hucre]}{ek}] ===========")
    print(f"replay {r_start}→{r_end}  sv={sv}  sembol={len(bars)}  süre={sure}s")
    print(f"enjeksiyon: max_open {onceki['max_open_positions']}→{max_open}  "
          f"size_r taban {onceki['position_size_r']}→{BOYUT_R}  harita={HARITA}")
    print(f"bütünlük geçerli={out['butunluk']['gecerli']}  frame_miss={_frame_miss[0]} "
          f"dup={len(_dup)} scan!=plan={len(scan_vs_plan)} yasak={yasak_yuklu} "
          f"base_max_bozuk={len(base_max_bozuk)} carpan_ihlal={len(_carpan_ihlal)} "
          f"plan_band_ihlal={len(plan_band_ihlal)}")
    print(f"işlem n={n_islem} ({out['islem']['islem_yil']}/yıl)  net_pnl={net_pnl_equity}  "
          f"maxdd_kanonik={detail.get('max_drawdown')}  avg_r={detail.get('avg_r')}  "
          f"sharpe={detail.get('sharpe')}")
    print(f"silahlı size_r rejim: {out['carpan_oz_sinama']['silahli_size_r_rejim']}")
    print(f"NO_GO nedenleri: {out['islem']['nogo_neden_dagilim']}")
    print(f"yazıldı: {outdir}/sonuc_{hucre}{ek}.json")
    print(f"KOSUM_{hucre.upper()}{ek.upper()}_BITTI")


# ---------------------------------------------------------------------------------------------
# KONTROL — çarpan≡1.0 smoke koşumu + C (026 smoke) İLE BİT-ÖZDEŞLİK KIYASI (kart kill#1)
# ---------------------------------------------------------------------------------------------
def kontrol():
    kosum("kontrol", smoke=True)

    yerel = SANDBOX / "smoke"
    c_dir = EDG026 / "smoke"
    dosya_kiyas = {}
    for ad in ("seanslar", "islemler"):
        benim = _sha_full(yerel / f"{ad}_kontrol_smoke.json")
        c = _sha_full(c_dir / f"{ad}_c_smoke.json")
        dosya_kiyas[ad] = {"kontrol_sha256": benim, "c_sha256": c,
                           "bayt_ayni": (benim is not None and benim == c)}

    sk = json.loads((yerel / "sonuc_kontrol_smoke.json").read_text())
    sc = json.loads((c_dir / "sonuc_c_smoke.json").read_text())
    bolum_kiyas = {}
    for b in BIT_BOLUMLER:
        bolum_kiyas[b] = (sk.get(b) == sc.get(b))

    bit_ozdes = (all(v["bayt_ayni"] for v in dosya_kiyas.values())
                 and all(bolum_kiyas.values()))
    out = {
        "kart": "EDG-2026-033", "kontrol": "carpan_1.0_smoke_bit_ozdeslik",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "tanim": ("kill#1 kontrolü: çarpan≡1.0 (dört rejimde 0.5) smoke koşumu 026 C smoke "
                  "çıktılarıyla — seanslar+islemler BAYT-AYNI (sha256) ve sonuc ekonomik "
                  f"bölümleri {list(BIT_BOLUMLER)} sözlük-eşit"),
        "dosya_bayt_kiyasi": dosya_kiyas,
        "sonuc_bolum_esitligi": bolum_kiyas,
        "bit_ozdes": bit_ozdes,
        "kill1_tetiklendi": not bit_ozdes,
    }
    (yerel / "kontrol_bit_ozdeslik.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str))
    print(f"\n=========== EDG-033 KONTROL BİT-ÖZDEŞLİK ===========")
    print(f"dosya bayt-aynı: { {k: v['bayt_ayni'] for k, v in dosya_kiyas.items()} }")
    print(f"sonuc bölüm eşitliği: {bolum_kiyas}")
    print(f"bit_ozdes={bit_ozdes}  kill#1 tetiklendi={not bit_ozdes}")
    print(f"yazıldı: {yerel/'kontrol_bit_ozdeslik.json'}")
    print("KONTROL_PASS" if bit_ozdes else "KONTROL_FAIL")


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

    # kill#2 (kart): taban-defterde trend_up işlem sayısı
    c_trend_up_n = sum(1 for t in C["islem"] if str(t.get("regime")) == "trend_up")
    kill2 = {
        "esik": f"taban-defterde (C islemler) trend_up n < {KILL2_TREND_UP_MIN} → olculemedi (kart kill#2)",
        "trend_up_n_taban": c_trend_up_n,
        "tetiklendi": c_trend_up_n < KILL2_TREND_UP_MIN,
    }

    # kill#1 kaydı: kontrol bit-özdeşlik dosyasından (kontrol koşulmadıysa None + neden)
    kb_yol = SANDBOX / "smoke" / "kontrol_bit_ozdeslik.json"
    if kb_yol.exists():
        kb = json.loads(kb_yol.read_text())
        kill1 = {"esik": "kontrol bit-özdeşliği düşerse ölçüm GEÇERSİZ (kart kill#1)",
                 "bit_ozdes": kb.get("bit_ozdes"), "tetiklendi": bool(kb.get("kill1_tetiklendi")),
                 "kaynak": str(kb_yol)}
    else:
        kill1 = {"esik": "kontrol bit-özdeşliği düşerse ölçüm GEÇERSİZ (kart kill#1)",
                 "bit_ozdes": None, "tetiklendi": None,
                 "kaynak": None,
                 "neden": "kontrol koşumu bulunamadı — kontrol_bit_ozdeslik.json yok (olculemedi)"}

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
        """Çekilen ay-çoklu-kümesinin işlemlerinden (n, Σpnl, sharpe|nan, maxdd|nan) — kanonik
        formüller (030 AYNEN)."""
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

    def ay_rejim_pnl(islemler) -> dict[str, "np.ndarray"]:
        """rejim → ay-vektörü (Σpnl); rejim evreni REGIMES + 'None' (motor dışı değer sayılmaz,
        ham anahtarla görünür)."""
        evren = list(REGIMES)
        out = {rg: np.zeros(M) for rg in evren}
        ay_idx = {a: i for i, a in enumerate(aylar)}
        for t in islemler:
            a = str(t["ts_open"])[:7]
            rg = str(t.get("regime"))
            if a in ay_idx:
                if rg not in out:
                    out[rg] = np.zeros(M)
                out[rg][ay_idx[a]] += float(t.get("pnl_dollars", 0.0))
        return out

    def hucre_kiyas(hucre: str) -> dict:
        E = _yukle(yerel, hucre, ek)
        se = E["sonuc"]
        etiket = f"hucre_{HUCRE_AD[hucre]}"

        # ---- şasi kimliği: motor+config sha C ile birebir mi (C'nin kaydettiği kümede) -------
        motor_ayni = {f: (se["motor_sha256_16"].get(f) == sc["motor_sha256_16"].get(f)
                          and se["motor_sha256_16"].get(f) is not None)
                      for f in ("broker.py", "backtest.py", "strategy.py")}     # C üçlüsü
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

        # ---- REJİM KİMLİĞİ: her seansta hücre rejimi+bütçesi C ile birebir (şasi çaprazı) ----
        e_seans_by_date = {s["date"]: s for s in E["seans"]}
        rejim_uyusmaz = []
        for d0, s0 in C_seans_by_date.items():
            e0 = e_seans_by_date.get(d0)
            if e0 is None or e0.get("regime") != s0.get("regime") \
                    or e0.get("exposure_budget_pct") != s0.get("exposure_budget_pct"):
                rejim_uyusmaz.append({"date": d0, "C": [s0.get("regime"), s0.get("exposure_budget_pct")],
                                      "hucre": None if e0 is None
                                      else [e0.get("regime"), e0.get("exposure_budget_pct")]})

        # ---- eşlenik ay-kümeli bootstrap: Δn, Δpnl, Δsharpe, Δmaxdd + REJİM-BAŞINA Δpnl ------
        grC, grE = ay_grup(C["islem"]), ay_grup(E["islem"])
        regC, regE = ay_rejim_pnl(C["islem"]), ay_rejim_pnl(E["islem"])
        rejim_evren = sorted(set(regC) | set(regE))
        rng = np.random.default_rng(BOOT_SEED)
        d_n = np.empty(BOOT_ITER)
        d_pnl = np.empty(BOOT_ITER)
        d_pnl_rejim = {rg: np.empty(BOOT_ITER) for rg in rejim_evren}
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
            for rg in rejim_evren:
                cv = regC[rg][pick].sum() if rg in regC else 0.0
                ev = regE[rg][pick].sum() if rg in regE else 0.0
                d_pnl_rejim[rg][i] = ev - cv
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
        rejim_islem_var = {rg: (sum(1 for t in C["islem"] if str(t.get("regime")) == rg)
                                + sum(1 for t in E["islem"] if str(t.get("regime")) == rg))
                           for rg in rejim_evren}
        pnl_rejim_ci = {rg: (ci95(d_pnl_rejim[rg]) if rejim_islem_var[rg] > 0 else None)
                        for rg in rejim_evren}
        pnl_rejim_ci_neden = {rg: (None if rejim_islem_var[rg] > 0
                                   else "iki tarafta da bu rejimde işlem yok — CI olculemedi")
                              for rg in rejim_evren}

        # ---- rejim-kırılımlı karne (030 deseni; TAM defterler) -------------------------------
        def rejim_karne(ts: list[dict]) -> dict:
            reg: dict[str, dict] = {}
            for t in ts:
                g = reg.setdefault(str(t.get("regime")),
                                   {"n": 0, "r_toplam": 0.0, "pnl": 0.0, "kazanan": 0})
                g["n"] += 1
                g["r_toplam"] += float(t.get("r_multiple") or 0.0)
                g["pnl"] += float(t.get("pnl_dollars") or 0.0)
                if float(t.get("r_multiple") or 0.0) > 0:
                    g["kazanan"] += 1
            out_k = {}
            for rg, g in sorted(reg.items(), key=lambda kv: -kv[1]["n"]):
                rs = [float(t.get("r_multiple") or 0.0) for t in ts if str(t.get("regime")) == rg]
                out_k[rg] = {"n": g["n"], "ort_r": round(g["r_toplam"] / g["n"], 3),
                             "medyan_r": round(float(np.median(rs)), 3),
                             "pnl": round(g["pnl"], 2),
                             "kazanma_orani": round(g["kazanan"] / g["n"], 3)}
            return out_k

        karne_c = rejim_karne(C["islem"])
        karne_e = rejim_karne(E["islem"])
        karne_delta = {}
        for rg in sorted(set(karne_c) | set(karne_e)):
            a0, b0 = karne_c.get(rg), karne_e.get(rg)
            karne_delta[rg] = {
                "d_n": (b0["n"] if b0 else 0) - (a0["n"] if a0 else 0),
                "d_pnl": round((b0["pnl"] if b0 else 0.0) - (a0["pnl"] if a0 else 0.0), 2),
                "d_pnl_ci95_eslenik": pnl_rejim_ci.get(rg),
                "d_ort_r": (round(b0["ort_r"] - a0["ort_r"], 3) if (a0 and b0) else None),
            }

        # ---- işlem-kümesi eşlemesi + SAF-BOYUT AYRIŞIMI (sente kapanan) ----------------------
        E_kimlik = {(str(t["ts_open"])[:10], t["ticker"]) for t in E["islem"]}
        E_by_kimlik = {(str(t["ts_open"])[:10], t["ticker"]): t for t in E["islem"]}
        eklenen_k = sorted(E_kimlik - C_kimlik)
        cikan_k = sorted(C_kimlik - E_kimlik)
        ortak_k = sorted(C_kimlik & E_kimlik)
        eklenen = [E_by_kimlik[k] for k in eklenen_k]
        cikan = [C_by_kimlik[k] for k in cikan_k]

        kova = {"ayni_trend_up": {"n": 0, "d_pnl": 0.0, "qty_oran": []},
                "ayni_diger": {"n": 0, "d_pnl": 0.0, "qty_oran": []},
                "kayan": {"n": 0, "d_pnl": 0.0}}
        rejim_cift_uyusmaz = 0
        for k in ortak_k:
            a, b = C_by_kimlik[k], E_by_kimlik[k]
            dpnl = float(b.get("pnl_dollars", 0.0)) - float(a.get("pnl_dollars", 0.0))
            if str(a.get("regime")) != str(b.get("regime")):
                rejim_cift_uyusmaz += 1          # aynı (tarih,ticker) → aynı seans → aynı rejim olmalı
            yol_ayni = (str(a.get("ts_close"))[:10] == str(b.get("ts_close"))[:10]
                        and a.get("exit_reason") == b.get("exit_reason")
                        and abs(float(a.get("r_multiple") or 0) - float(b.get("r_multiple") or 0)) <= 1e-9)
            if not yol_ayni:
                kova["kayan"]["n"] += 1
                kova["kayan"]["d_pnl"] += dpnl
            else:
                ad = "ayni_trend_up" if str(b.get("regime")) == "trend_up" else "ayni_diger"
                kova[ad]["n"] += 1
                kova[ad]["d_pnl"] += dpnl
                qa, qb = float(a.get("qty") or 0), float(b.get("qty") or 0)
                if qa > 0:
                    kova[ad]["qty_oran"].append(qb / qa)

        def _qty_ozet(v: list[float]) -> dict | None:
            if not v:
                return None
            arr = np.asarray(v, dtype=float)
            return {"n": len(v), "medyan": round(float(np.median(arr)), 4),
                    "ort": round(float(arr.mean()), 4),
                    "min": round(float(arr.min()), 4), "max": round(float(arr.max()), 4)}

        ekl_pnl = round(sum(float(t.get("pnl_dollars") or 0.0) for t in eklenen), 2)
        cik_pnl = round(sum(float(t.get("pnl_dollars") or 0.0) for t in cikan), 2)
        ortak_dpnl = kova["ayni_trend_up"]["d_pnl"] + kova["ayni_diger"]["d_pnl"] + kova["kayan"]["d_pnl"]
        d_pnl_nokta = round(float(se["performans"].get("net_pnl_trades") or 0)
                            - float(sc["performans"].get("net_pnl_trades") or 0), 2)
        kalinti = round(d_pnl_nokta - (ekl_pnl + round(ortak_dpnl, 2) - cik_pnl), 2)

        def _kume_ozet(ts: list[dict]) -> dict | None:
            if not ts:
                return None
            rs = [float(t.get("r_multiple") or 0.0) for t in ts]
            return {"n": len(ts), "ort_r": round(sum(rs) / len(rs), 3),
                    "medyan_r": round(float(np.median(rs)), 3),
                    "pnl_toplam": round(sum(float(t.get("pnl_dollars") or 0.0) for t in ts), 2),
                    "kazanma_orani": round(sum(1 for r in rs if r > 0) / len(rs), 3),
                    "rejim_kirilimi": rejim_karne(ts),
                    "exit_reason_dagilim": dict(sorted(
                        {str(t.get("exit_reason")): sum(1 for x in ts
                                                        if str(x.get("exit_reason")) == str(t.get("exit_reason")))
                         for t in ts}.items(), key=lambda kv: -kv[1]))}

        ayrisim = {
            "kimlik": "(ts_open[:10], ticker); yol-aynı = ts_close+exit_reason aynı ∧ |Δr|≤1e-9",
            "ortak_n": len(ortak_k), "eklenen_n": len(eklenen), "cikan_n": len(cikan),
            "ortak_rejim_cift_uyusmaz_n": rejim_cift_uyusmaz,   # 0 olmalı (aynı seans → aynı rejim)
            "kovalar": {
                "ortak_yol_ayni_trend_up": {
                    "n": kova["ayni_trend_up"]["n"],
                    "d_pnl": round(kova["ayni_trend_up"]["d_pnl"], 2),
                    "qty_oran": _qty_ozet(kova["ayni_trend_up"]["qty_oran"]),
                    "yorum_beyani": ("amaçlanan SAF-BOYUT etkisi + equity-yolu sürüklenmesi "
                                     "(qty equity'ye bağlı; oran ≈ çarpan × equity-sapması)")},
                "ortak_yol_ayni_diger_rejim": {
                    "n": kova["ayni_diger"]["n"],
                    "d_pnl": round(kova["ayni_diger"]["d_pnl"], 2),
                    "qty_oran": _qty_ozet(kova["ayni_diger"]["qty_oran"]),
                    "yorum_beyani": ("H1'de çarpan=1.0 → fark saf equity-sürüklenmesi; "
                                     "H2'de 0.7× boyut + sürüklenme")},
                "ortak_yol_kayan_knockon": {
                    "n": kova["kayan"]["n"], "d_pnl": round(kova["kayan"]["d_pnl"], 2)},
                "eklenen": {"pnl": ekl_pnl, "ozet": _kume_ozet(eklenen)},
                "cikan": {"pnl": cik_pnl, "ozet": _kume_ozet(cikan)},
            },
            "pnl_kimligi": {
                "delta_net_pnl_trades": d_pnl_nokta,
                "eklenen_pnl": ekl_pnl, "cikan_pnl": cik_pnl,
                "ortak_delta_pnl": round(ortak_dpnl, 2),
                "kalinti": kalinti,
                "sente_kapandi": abs(kalinti) <= 0.01,
            },
        }

        # ---- ısı-kullanım profili ------------------------------------------------------------
        isi_profil = {
            "C": {"tepe_isi": sc["tepe_isi"],
                  "rejim_kirilimi": _isi_rejim_kirilimi(C["seans"]),
                  "heat_hard_nogo_n": (sc["islem"].get("nogo_neden_dagilim") or {}).get("heat_hard", 0),
                  "silahli_plan_size_r": sc["islem"].get("silahli_plan_size_r")},
            etiket: {"tepe_isi": se["tepe_isi"],
                     "rejim_kirilimi": se.get("isi_rejim_kirilimi"),
                     "heat_hard_nogo_n": (se["islem"].get("nogo_neden_dagilim") or {}).get("heat_hard", 0),
                     "silahli_plan_size_r": se["islem"].get("silahli_plan_size_r"),
                     "silahli_size_r_rejim": (se.get("carpan_oz_sinama") or {}).get("silahli_size_r_rejim")},
        }

        # ---- kill#3 şasi bütünlüğü -----------------------------------------------------------
        kill3 = {
            "esik": ("şasi bütünlüğü: koşum-içi kontroller (frame/dup/scan==plan/yasak/base_max) + "
                     "çarpan öz-sınamaları (scan-çağrı + plan/işlem bandı) + motor/config sha == C + "
                     "takvim + rejim-kimliği (kart kill#3)"),
            "hucre_butunluk": se["butunluk"]["gecerli"],
            "C_butunluk": sc["butunluk"]["gecerli"],
            "carpan_scan_ihlal_n": (se.get("carpan_oz_sinama") or {}).get("2_scan_cagri_ihlal", {}).get("n"),
            "carpan_plan_band_ihlal_n": (se.get("carpan_oz_sinama") or {}).get("3_plan_bandi", {}).get("plan_ihlal_n"),
            "motor_sha_ayni": all(motor_ayni.values()),
            "config_sha_ayni": all(config_ayni.values()),
            "rampa_ayni_15_36": rampa_ayni,
            "takvim_ayni": takvim_ayni,
            "rejim_kimligi_uyusmaz_n": len(rejim_uyusmaz),
            "rejim_kimligi_ornek": rejim_uyusmaz[:5],
            "tetiklendi": not (se["butunluk"]["gecerli"] and sc["butunluk"]["gecerli"]
                               and all(motor_ayni.values()) and all(config_ayni.values())
                               and rampa_ayni and takvim_ayni and not rejim_uyusmaz),
        }

        ddc = sc["performans"].get("maxdd_kanonik")
        dde = se["performans"].get("maxdd_kanonik")
        basari_kosulu = {
            "not": ("HÜKÜM GİRDİSİ (kart success_metric) — kill değil: ΔP&L CI-alt>0 VE "
                    f"dd ≤ C×{DD_KOSUL_KATSAYI} kaydı; hüküm Rol-1'in"),
            "d_pnl_ci_alt": (pnl_ci or {}).get("lo"),
            "d_pnl_ci_alt_pozitif": ((pnl_ci or {}).get("lo") is not None
                                     and (pnl_ci or {}).get("lo") > 0),
            "maxdd_C": ddc, "maxdd_hucre": dde,
            "dd_oran": round(dde / ddc, 3) if (ddc not in (None, 0) and dde is not None) else None,
            "dd_C_x1p3_icinde": (dde <= DD_KOSUL_KATSAYI * ddc)
            if (ddc not in (None, 0) and dde is not None) else None,
        }

        def satir(*yol):
            def cek(s):
                v = s
                for kk in yol:
                    v = v.get(kk) if isinstance(v, dict) else None
                    if v is None:
                        return None
                return v
            return {"C_duz_0p5R": cek(sc), etiket: cek(se)}

        tablo = {
            "islem_n": {"C_duz_0p5R": nC, etiket: nE, "fark": nE - nC,
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
            "silahli_plan_size_r": satir("islem", "silahli_plan_size_r"),
            "doluluk_pozisyon_gun": satir("doluluk", "pozisyon_gun_open_fazi"),
            "ort_acik_pozisyon": satir("doluluk", "ort_acik_pozisyon"),
            "toplam_bars_held": satir("doluluk", "toplam_bars_held"),
            "tasnif_tum_seans": satir("tasnif_tum_seans", "dagilim"),
        }

        return {
            "hucre": hucre, "ad": HUCRE_AD[hucre], "harita_mutlak_size_r": HUCRELER[hucre],
            "sasi_kimligi": {"motor_sha_ayni": motor_ayni, "config_sha_ayni": config_ayni,
                             "rampa_ayni_15_36": rampa_ayni, "takvim_ayni": takvim_ayni,
                             "rejim_kimligi_uyusmaz_n": len(rejim_uyusmaz), "serh": serh},
            "tablo": tablo,
            "rejim_karne": {"C_duz_0p5R": karne_c, etiket: karne_e, "delta": karne_delta,
                            "d_pnl_rejim_ci_olculemedi_neden": {k: v for k, v in pnl_rejim_ci_neden.items() if v},
                            "tanim": "işlem kaydındaki `regime` (plan günü, motor kaydı — 030 deseni)"},
            "isi_kullanim_profili": isi_profil,
            "saf_boyut_ayrisimi": ayrisim,
            "kill3_sasi_butunlugu": kill3,
            "basari_kosulu_kaydi": basari_kosulu,
        }

    hucre_sonuclari = {h: hucre_kiyas(h) for h in ("h1", "h2")}

    out = {
        "kart": "EDG-2026-033",
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
                                  "metrikler iterasyon içinde kanonik formüllerle yeniden hesaplanır; "
                                  "rejim-başına Δpnl aynı çekilişten (eşlenik)"),
            "islem_ay_anahtari": "ts_open[:7] (giriş ayı)",
            "sharpe_boot": ("kanonik score_detail formülü; span = tam pencere gün sayısı (sabit); "
                            "n≤2 veya std=0 iterasyonları atlanır (sayı raporlu)"),
            "maxdd_boot": ("kanonik equity_curve (ts_close sıralı) + max_drawdown; ay "
                           "yeniden-örneklemesi dd zaman-sırasını yapay kurar — CI bu beyanla "
                           "okunur; NOKTA dd motor kanonik"),
            "saf_boyut_ayrisimi": ("Δ(Σpnl) ≡ Σeklenen + Σortak_Δ − Σçıkan; ortak_Δ üç kovaya tam "
                                   "bölünür (yol-aynı∧trend_up / yol-aynı∧diğer / yol-kayan); "
                                   "kalıntı sente kapanmalı (|kalinti|≤0.01$)"),
        },
        "kill1_kontrol_bit_ozdesligi": kill1,
        "kill2_trend_up_taban_n": kill2,
        "hucreler": hucre_sonuclari,
        "dosyalar": {h: {"sonuc": f"sonuc_{h}{ek}.json", "seanslar": f"seanslar_{h}{ek}.json",
                         "islemler": f"islemler_{h}{ek}.json"} for h in ("h1", "h2")},
        "hukum": None,   # HÜKÜM YAZILMAZ — Rol-1'in
    }
    (yerel / "sonuc.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))

    print(f"\n==================== EDG-033 KIYAS ÖZETİ{ek} ====================")
    print(f"kill#1 kontrol bit-özdeşlik: bit_ozdes={kill1.get('bit_ozdes')} "
          f"tetiklendi={kill1.get('tetiklendi')}")
    print(f"kill#2 taban trend_up n={kill2['trend_up_n_taban']} tetiklendi={kill2['tetiklendi']}")
    for h, hs in hucre_sonuclari.items():
        t = hs["tablo"]
        et = f"hucre_{HUCRE_AD[h]}"
        ay = hs["saf_boyut_ayrisimi"]
        print(f"\n--- hücre {h} ({HUCRE_AD[h]}; harita={hs['harita_mutlak_size_r']}) ---")
        print(f"şasi: serh={hs['sasi_kimligi']['serh']}  takvim={hs['sasi_kimligi']['takvim_ayni']}  "
              f"rejim_uyusmaz={hs['sasi_kimligi']['rejim_kimligi_uyusmaz_n']}  "
              f"KILL#3 tetiklendi={hs['kill3_sasi_butunlugu']['tetiklendi']}")
        print(f"işlem: C {t['islem_n']['C_duz_0p5R']} → {t['islem_n'][et]} "
              f"(fark {t['islem_n']['fark']})  ΔCI95={t['islem_fark_ci95']}")
        print(f"net_pnl: {t['net_pnl_trades']}  ΔCI95={t['net_pnl_fark_ci95']}")
        print(f"maxdd: {t['maxdd_kanonik']}  ΔCI95={t['maxdd_fark_ci95_kapali_islem_egrisi']}")
        print(f"sharpe: {t['sharpe']}  ΔCI95={t['sharpe_fark_ci95']}")
        print(f"rejim karne Δ: { {rg: v['d_pnl'] for rg, v in hs['rejim_karne']['delta'].items()} }")
        print(f"ayrışım: ortak={ay['ortak_n']} (aynı-tu={ay['kovalar']['ortak_yol_ayni_trend_up']['n']} "
              f"Δ{ay['kovalar']['ortak_yol_ayni_trend_up']['d_pnl']} | "
              f"aynı-diğer={ay['kovalar']['ortak_yol_ayni_diger_rejim']['n']} "
              f"Δ{ay['kovalar']['ortak_yol_ayni_diger_rejim']['d_pnl']} | "
              f"kayan={ay['kovalar']['ortak_yol_kayan_knockon']['n']} "
              f"Δ{ay['kovalar']['ortak_yol_kayan_knockon']['d_pnl']})  "
              f"eklenen={ay['eklenen_n']} ({ay['kovalar']['eklenen']['pnl']})  "
              f"çıkan={ay['cikan_n']} ({ay['kovalar']['cikan']['pnl']})  "
              f"kalıntı={ay['pnl_kimligi']['kalinti']} sente_kapandı={ay['pnl_kimligi']['sente_kapandi']}")
        print(f"başarı koşulu kaydı: ΔP&L CI-alt={hs['basari_kosulu_kaydi']['d_pnl_ci_alt']} "
              f"(>0: {hs['basari_kosulu_kaydi']['d_pnl_ci_alt_pozitif']})  "
              f"dd_oran={hs['basari_kosulu_kaydi']['dd_oran']} "
              f"(≤1.3: {hs['basari_kosulu_kaydi']['dd_C_x1p3_icinde']})")
    print(f"\nyazıldı: {yerel/'sonuc.json'}")
    print("KIYAS_BITTI")


# ---------------------------------------------------------------------------------------------
# TEŞHİS — motor-sha driftinin KAYIT-ZAMANI/ÇALIŞMA-ZAMANI ayrımı (2026-08-12 vakası; salt-okuma)
# ---------------------------------------------------------------------------------------------
def teshis():
    """kill#3'ün tetiklediği motor-sha uyuşmazlığının teşhis kaydı. HÜKÜM DEĞİL — kanıt dizimi.

    VAKA: hücre koşumları ~18:08:2x UTC'de modülleri İTHAL ETTİ (log ilk satırı 18:08:25 = bar
    yükleme, ithal bitmiş); paralel oturum broker/guard/strategy'yi 18:11:47/18:12:00/18:14:31
    UTC'de (mtime) çalışma ağacında DEĞİŞTİRDİ (OPT Faz-1 rampa kablolaması + momentum_burst
    silahlanması — commit'lenmemiş ' M'); hücre sonuc'ları 18:22'de yazılırken _sha() YENİ
    baytları okudu. Yani sha kaydı = kayıt-zamanı görüntüsü; koşan kod = ESKİ (C-özdeş) motor.
    (Paralel-oturum drift teşhis emsali: 2026-08-02 bounds/goal vakası — önce mtime + kayıt bak.)"""
    import subprocess
    out = {
        "kart": "EDG-2026-033", "teshis": "motor_sha_drift_kayit_zamani",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "vaka_ozeti": ("kill#3 sha-uyuşmazlığı KAYIT-ZAMANI artefaktıdır: paralel oturumun "
                       "commit'lenmemiş çalışma-ağacı düzenlemeleri (OPT Faz-1: derisk rampası "
                       "goal.yaml'a kablolandı; momentum_burst ARMED_SETUPS'a eklendi) hücre "
                       "İTHALİNDEN SONRA, sonuc YAZIMINDAN ÖNCE diske indi. Koşan kod C-özdeş "
                       "ESKİ motordu — dört bağımsız kanıt aşağıda. Hüküm Rol-1'in."),
        "kanit_1_ithal_zamanlamasi": {
            "hucre_log_ilk_satir_utc": {
                h: (lambda p: (json.loads(p.read_text().splitlines()[0])["ts"]
                               if p.exists() and p.read_text().splitlines() else None))
                   (SANDBOX / f"kosum_{h}.log") for h in ("h1", "h2")},
            "motor_mtime_utc": {
                f: dt.datetime.fromtimestamp((REPO / "meridian" / f).stat().st_mtime,
                                             dt.timezone.utc).isoformat(timespec="seconds")
                for f in ("broker.py", "strategy.py", "guard.py")},
            "beyan": ("log ilk satırı (bar-yükleme uyarısı) ithalin BİTTİĞİ andan sonradır; "
                      "mtime'lar ondan 3-6 dk SONRA — ithal edilen baytlar eskiydi")},
        "kanit_2_kontrol_sha_kaydi": {
            "kontrol_sonuc_motor_sha": (json.loads((SANDBOX / "smoke" / "sonuc_kontrol_smoke.json")
                                                   .read_text())["motor_sha256_16"]
                                        if (SANDBOX / "smoke" / "sonuc_kontrol_smoke.json").exists() else None),
            "C_motor_sha": json.loads((EDG026 / "sonuc_c.json").read_text())["motor_sha256_16"],
            "beyan": ("18:07:30'da yazılan kontrol sonucu C'nin sha'larını BİREBİR kaydetti — "
                      "düzenlemelerden önce ağaç C-özdeşti; kontrol bit-özdeşliği ŞERHSİZ geçti")},
        "kanit_3_yapisal_typeerror": {
            "beyan": ("YENİ broker.max_positions_at, derisk_mult'u 3 argümanla çağırır "
                      "(equity, peak, cfg); şasinin monkeypatch'i 2-parametreli kapanıştır — YENİ "
                      "modül yüklenseydi koşum-öncesi assert'te (max_positions_at(80,100,5)==4) "
                      "TypeError ile ÇÖKERDİ. İki hücre de 820+ sn koşup tam defter üretti → "
                      "ESKİ max_positions_at yürüdü")},
        "kanit_4_defter_ici_setup_evreni": {
            "beyan": ("YENİ strategy.py momentum_burst'ü silahlar (ARMED_SETUPS 4'lü); hücre "
                      "defterlerinde SIFIR momentum_burst işlemi var — koşan ARMED_SETUPS eski "
                      "3'lüydü (C evreniyle aynı)"),
            "setup_dagilimlari": {
                h: (lambda ts: {s: sum(1 for t in ts if str(t.get("setup")) == s)
                                for s in sorted({str(t.get("setup")) for t in ts})})
                   (json.loads((SANDBOX / f"islemler_{h}.json").read_text()))
                for h in ("h1", "h2")}},
        "calisma_agaci_durumu": subprocess.run(
            ["git", "status", "--porcelain", "meridian/"], cwd=REPO,
            capture_output=True, text=True).stdout.strip().splitlines(),
        "simdiki_motor_sha256_16": {f: _sha(REPO / "meridian" / f)
                                    for f in ("broker.py", "backtest.py", "strategy.py",
                                              "regime.py", "guard.py", "score.py")},
        "sonuc_beyani": ("hücrelerin ÇALIŞMA-ZAMANI motoru C ile özdeşti (kanıt 1-4); kill#3 "
                        "bayrağı kayıt-zamanı sha görüntüsünü dürüstçe yansıtır ve sonuc.json'da "
                        "OLDUĞU GİBİ bırakılmıştır — yorum/hüküm Rol-1'in"),
    }
    (SANDBOX / "teshis_motor_drift.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str))
    print(json.dumps({k: out[k] for k in ("vaka_ozeti", "sonuc_beyani")}, ensure_ascii=False, indent=1))
    print(f"yazıldı: {SANDBOX/'teshis_motor_drift.json'}")
    print("TESHIS_BITTI")


if __name__ == "__main__":
    argv = sys.argv[1:]
    smoke = "--smoke" in argv
    argv = [a for a in argv if a != "--smoke"]
    if argv and argv[0] == "kontrol":
        kontrol()
    elif argv and argv[0] == "kosum" and len(argv) > 1:
        kosum(argv[1], smoke=smoke)
    elif argv and argv[0] == "kiyas":
        kiyas(smoke=smoke)
    elif argv and argv[0] == "teshis":
        teshis()
    else:
        sys.exit("kullanım: olcum.py {kontrol | kosum h1|h2 [--smoke] | kiyas [--smoke] | teshis}")

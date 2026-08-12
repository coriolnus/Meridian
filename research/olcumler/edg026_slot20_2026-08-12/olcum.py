"""EDG-2026-026 — SLOT 20 + BOYUT 0.5R · ölçüm aracı (2026-08-12)

Kart: research/cards/EDG-2026-026-slot20-boyut05.yaml (OKU-DOKUNMA; hüküm Rol-1'in).
Rol: ÖLÇÜM ajanı. Bu modül HÜKÜM VERMEZ, karta dokunmaz, git/canlı/broker/state'e YAZMAZ.
Şasi: EDG-023 (research/olcumler/edg023_rampa_bandi_2026-08-12/olcum.py) varyant (B) koşum
düzeni AYNEN devralındı: izole sandbox, rampa-15/36 monkeypatch'i (beyanlı), kancalar,
bütünlük kontrolleri, eşlenik ay-kümeli bootstrap (5000 iter, seed 20260812).

TEK KOŞUM (C) — kart features_asof, DONUK:
  rampa 15/36 (monkeypatch — 023 beyanlı deseni AYNEN)
  + max_open_positions = 20   (PARAM-enjeksiyonu: config.goal() derin-kopyası → goal["limits"];
                               dosyaya tek bayt yazılmaz, motor dosyası değişmez)
  + position_size_r    = 0.5  (PARAM-enjeksiyonu: strateji params sözlüğü — YÜZEY BEYANI aşağıda)

YÜZEY BEYANI (kart "goal/limits sözlüğünden" der; ölçülen gerçek yüzey):
  * max_open_positions gerçekten goal/limits yüzeyinden okunur (backtest.py:147) → enjeksiyon
    birebir kartta yazıldığı yerden.
  * position_size_r motorda goal/limits'te YOKTUR; STRATEJİ params yüzeyinden okunur
    (strategy.py:487/553/610/669/774/851/978 `_f(params,"position_size_r",1.0)`), plan boyutu
    `min(sig.size_r, limits.max_position_r)` ile yalnız YUKARI kırpılır (backtest.py:352;
    max_position_r=1.0 → 0.5 kırpılmaz). Enjeksiyon bu yüzden params sözlüğüne yapılır —
    kartın ilkesiyle aynı sınıf (sözlük girdisi, monkeypatch DEĞİL, motor dosyası DEĞİŞMEZ).
    params_by_regime dört rejimde de {} (koşum öncesi assert + resolve_params kanıtı) →
    tek enjeksiyon noktası yeterli ve yayılımı kanıtlı.

ZARF SABİT — BEYAN (kart yalnız İKİ parametreyi değiştirir; kalan zarf yürürlükte):
  * limits.heat_hard_r = 5.0R DEĞİŞMEDİ: guard.classify_gate `open_risk_r + plan.size_r > 5.0
    → NO_GO` (guard.py "heat_hard"). 0.5R planlarla aritmetik fiili tavan ≈ 10-16 eşzamanlı
    pozisyon (conviction 0.6-1.0× nedeniyle plan başına 0.3-0.5R). 20 slot'un ısı tavanına
    çarpması bu ÖLÇÜMÜN BULGUSUdur, düzeltilecek bir kusur değil — NO_GO neden dağılımı
    raporlanır, karar operatör penceresinin.
  * sector_cap YAN ETKİSİ: kural `(sektörde_n+1)/max_open_positions > %40` (guard.py) —
    payda 5→20 olunca sektör-başına fiili tavan 2→8 pozisyona GEVŞER. Bu, enjeksiyonun
    motor-içi doğal sonucu; ayrı bir parametre değişikliği DEĞİL. Beyanlı, ölçümde görünür.

KIYAS: EDG-023'ün B koşumunun HAZIR çıktıları (sonuc_varyant/seanslar_varyant/islemler_varyant
— YENİDEN KOŞULMAZ, okunur). Motor sha'ları B ile birebir DOĞRULANIR; değilse kıyas ŞERHLİ.

TANIMLAR (ölçümden ÖNCE donduruldu; sonuç görüldükten sonra değişmez):
  islem              = kapanmış işlem satırı (broker.closed; eod/delisted markout DAHİL).
  ay kümesi          = ts_open[:7] (giriş ayı).
  islem fark CI (C↔B)= ay-kümeli EŞLENİK bootstrap: aynı ay çekilişi iki koşuma birden
                       (aylar yerine-koymalı, 5000 iter, seed 20260812); fark = C − B.
  doluluk            = OPEN fazında (fill'den ÖNCE) açık pozisyon sayısı toplamı (pozisyon-gün);
                       ikincil: Σ bars_held.
  TEPE-ISI (nominal) = kart formülü: seans-başına eşzamanlı pozisyon × pozisyon-başına R
                       (C: n×0.5R, B: n×1.0R). İKİ pencerede ölçülür:
                       (a) open_fazi   : kancanın n_acik'i (fill'den ÖNCE — şasi tanımı),
                       (b) islem_araligi: işlem aralıklarından (ts_open ≤ seans ≤ ts_close;
                           aynı-gün dolumlar DAHİL — open-fazının göremediği gün-içi zirve).
                       Nominal formül ÜST SINIRDIR: conviction 0.6-1.0× gerçek boyutu düşürür.
  TEPE-ISI (gerçekleşen, yalnız C) = kancada açık pozisyonlardan doğrudan ölçülür:
                       Σ size_r (silahlanmış gerçek R), Σ risk_dollars (giriş riski $),
                       Σ max(0, (entry − max(stop,trail)) × qty) (kalan risk $ — guard ısı yasası).
                       B için ÖLÇÜLEMEZ (B seans şemasında alan yok; yeniden koşum kart gereği
                       yasak) → None + bu neden (UYDURMA YASAĞI).
  max-dd             = motor-kanonik score.score_detail.max_drawdown (kapalı-işlem ∨ günlük M2M
                       kötüsü). Kart dd kıyası (B×1.5) BUNUN üstünden; yalnız-M2M ayrıca raporlu.
  net P&L            = M2M equity son değer − START_EQUITY; çapraz: Σ pnl_dollars.
  NO_GO neden dağılımı = plan_log gate_reasons alt-dizgi eşlemesi (heat_hard/max_open/sector_cap/
                       rr_floor/exposure/breaker/position_size); eşleşmeyen HAM dizgiyle sayılır.

KILL KONTROLLERİ (kart, DONUK — koşul değerinin kaydı, hüküm DEĞİL):
  kill#1: C−B işlem farkı CI'ı 0'ı artı yönde DIŞLAMIYORSA → slot artışı fiilen İNERT beyanı.
  kill#2: maxdd_C > 1.5 × maxdd_B (kanonik) → "öneri dili kullanılmaz" bayrağı; sayılar tam.
  kill#3: şasi bütünlüğü (frame_miss=0, dup=0, scan==plan, yasak modül yok, base_max_open==20).

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen = None + neden); YASA-4 (sessiz-yutma işaretli + gerekçe);
YASA-6 (okuyucu: sonuc_c.json + seanslar_c + islemler_c → `kiyas` tüketir; sonuc.json → dönüş
raporu + Rol-1). SALT-OKUMA: config.STATE koşum-başına izole sandbox; barlar sembolik bağla
SALT-OKUNUR; canlı state'e ve motor dosyalarına tek bayt yazılmaz. meridian.loop /
counterfactual / cf_backfill / hermes İTHAL EDİLMEZ — sys.modules ile KANITLANIR.

KULLANIM:
  olcum.py c              # koşum C → sonuc_c.json + seanslar_c.json + islemler_c.json
  olcum.py kiyas          # C (yerel) + B (EDG-023 hazır çıktıları) → sonuc.json
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
EDG023 = REPO / "research/olcumler/edg023_rampa_bandi_2026-08-12"

# tek-iş parçacığı: determinizm + ölçüm gürültüsüzlüğü (şasi ile aynı)
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

REPLAY_START = "2022-01-01"
REPLAY_END = "2026-07-30"                      # kart: EDG-023 ile AYNI pencere
BOOT_SEED = 20260812
BOOT_ITER = 5000

# koşum C'nin DONUK parametreleri (kart features_asof)
RAMPA = {"tam_dd": 0.15, "sifir_dd": 0.36}     # B ile aynı — monkeypatch (beyan başlıkta)
SLOT = 20                                      # goal/limits enjeksiyonu
BOYUT_R = 0.5                                  # strateji params enjeksiyonu (yüzey beyanı başlıkta)
B_BOYUT_R = 1.0                                # B'nin nominal pozisyon-başına R'si (ısı formülü için)
KILL_DD_KATSAYI = 1.5                          # kart kill#2: dd B×1.5 kıyası

KART3 = ["tavan_sifir", "evren_bagladi", "derisk_bagladi"]
YASAK = ("meridian.loop", "meridian.counterfactual", "meridian.cf_backfill", "meridian.hermes")

# NO_GO/REVIEW neden eşlemesi (guard.py hard/soft mesajlarının SABİT alt-dizgileri).
# Eşleşmeyen neden HAM dizgisiyle sayılır — sessiz düşme yok (YASA-4).
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
            # kaynak = EDG-022'nin DONMUŞ kopyaları (tutarlılık çivisi — B de aynı kaynaktan koştu).
            # DOSYALAR DEĞİŞTİRİLMEZ: slot/boyut enjeksiyonu YÜKLENMİŞ sözlüklere yapılır ki
            # config sha'ları B ile bayt-aynı kalsın ve şasi kimliği sha ile kanıtlansın.
            shutil.copyfile(EDG022 / "state" / f, dst)
    return st


# ---------------------------------------------------------------------------------------------
# RAMPA — orijinal formülün birebir parametrize kopyası (023 varyant deseni AYNEN)
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
# SINIFLAMA — EDG-022'nin DONUK kuralı (AYNEN; heat-NO_GO'yu BİLMEZ — bu bilinçli: kural donuk,
# ısı bağlaması NO_GO neden dağılımından okunur)
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
    """Seans-başına eşzamanlı pozisyon (işlem aralıklarından): ts_open ≤ seans ≤ ts_close.
    Aynı-gün dolumlar DAHİL — open-fazı sayımının göremediği gün-içi zirveyi yakalar."""
    araliklar = [(str(t["ts_open"])[:10], str(t["ts_close"])[:10]) for t in islemler
                 if t.get("ts_open") and t.get("ts_close")]
    out = []
    for d in takvim:
        out.append(sum(1 for a, b in araliklar if a <= d <= b))
    return out


# ---------------------------------------------------------------------------------------------
# TEK KOŞUM (C — slot20_r05)
# ---------------------------------------------------------------------------------------------
def kosum(smoke: bool = False):
    outdir = (SANDBOX / "smoke") if smoke else SANDBOX
    outdir.mkdir(exist_ok=True)
    r_start, r_end = (REPLAY_START, "2022-06-30") if smoke else (REPLAY_START, REPLAY_END)

    st_dir = hazirla("c" + ("_smoke" if smoke else ""))
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
    ORIJ_DERISK = brk.derisk_mult          # orijinal fonksiyon nesnesi (kayıt için)

    # ---- rampa kurulumu + öz-sınama (023 varyant AYNEN; yayılım kanıtı 5 VE 20 tabanla) ------
    brk.derisk_mult = _rampa_fn(RAMPA["tam_dd"], RAMPA["sifir_dd"])
    assert brk.derisk_mult is not ORIJ_DERISK
    # yama semantiği: dd=%10 tam boy; dd=%20 → 1-(0.05/0.21)=0.7619; dd>=%36 → 0
    assert brk.derisk_mult(90.0, 100.0) == 1.0
    assert abs(brk.derisk_mult(80.0, 100.0) - 0.7619) < 1e-9
    assert brk.derisk_mult(64.0, 100.0) == 0.0
    # yayılım kanıtı: max_positions_at İÇİNDEKİ global çözüm de yamayı görüyor
    assert brk.max_positions_at(80.0, 100.0, 5) == 4       # round(5×0.7619)=4 (023 çivisi)
    assert brk.max_positions_at(80.0, 100.0, 20) == 15     # round(20×0.7619)=15 (slot-20 tabanı)

    # ---- girdiler + PARAM-ENJEKSİYONLARI (dosya DEĞİŞMEZ; sözlükler değişir, beyan başlıkta) -
    stg = yaml.safe_load((st_dir / "strategy.yaml").read_text())
    params = dict(stg["params"])
    by_regime = stg.get("params_by_regime") or None
    sv = int(stg.get("version"))
    goal = config.goal()                                   # derin kopya — dosyaya/önbelleğe sızmaz

    onceki = {"max_open_positions": int(goal["limits"]["max_open_positions"]),
              "position_size_r": float(params["position_size_r"])}
    goal["limits"]["max_open_positions"] = SLOT            # ENJEKSİYON 1 (goal/limits — kart yüzeyi)
    params["position_size_r"] = BOYUT_R                    # ENJEKSİYON 2 (strateji params — yüzey beyanı)

    # enjeksiyon öz-sınaması: rejim çözümü DÖRT rejimde de 0.5 görmeli (params_by_regime boş kanıtı)
    for _rg in ("trend_up", "trend_down", "chop", "high_vol"):
        _eff = config.resolve_params(params, by_regime, _rg)
        assert float(_eff["position_size_r"]) == BOYUT_R, f"rejim override sızıntısı: {_rg}"
        assert ("position_size_r" not in ((by_regime or {}).get(_rg) or {})), \
            f"params_by_regime[{_rg}] position_size_r içeriyor — tek-nokta enjeksiyonu yetersiz"
    assert float(goal["limits"]["max_position_r"]) >= BOYUT_R          # yukarı-kırpma 0.5'i etkilemez
    limits = goal["limits"]
    max_open = int(limits["max_open_positions"])
    no_trade_before = int(limits.get("no_trade_before_bars", 0))
    assert max_open == SLOT

    # ---- kancalar (şasi deseni AYNEN; +3 gerçekleşen-ısı alanı) ------------------------------
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
            # GERÇEKLEŞEN ISI (tanımlar başlıkta; nominal 0.5R×n formülü analizde n_acik'ten türer)
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

    # ---- plan_log çapraz-kontrolü + NO_GO/REVIEW neden dağılımı ------------------------------
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

    # ---- işlem/doluluk/ısı/performans metrikleri ---------------------------------------------
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
        "kart": "EDG-2026-026", "kosum": "c_slot20_r05", "smoke": smoke,
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sure_sn": sure,
        "rampa": {"tam_dd": RAMPA["tam_dd"], "sifir_dd": RAMPA["sifir_dd"],
                  "enjeksiyon": ("MONKEYPATCH — ölçüm modülü içinde broker.derisk_mult "
                                 "modül-özniteliği değiştirildi; motor DOSYASI değişmedi "
                                 "(EDG-023 varyant deseni AYNEN — beyan modül başlığında)")},
        "param_enjeksiyon": {
            "max_open_positions": {"once": onceki["max_open_positions"], "sonra": SLOT,
                                   "yuzey": "goal['limits'] (config.goal() derin kopyası — dosya değişmedi)"},
            "position_size_r": {"once": onceki["position_size_r"], "sonra": BOYUT_R,
                                "yuzey": ("strateji params sözlüğü — KART 'goal/limits' der; motorda bu "
                                          "anahtar params yüzeyinde yaşar (strategy.py _f). Beyan modül "
                                          "başlığında; params_by_regime 4 rejimde boş, resolve_params "
                                          "kanıtı koşum öncesi assert edildi")},
            "zarf_sabit": ("heat_hard_r=5.0R, heat_review_r=3.5R, max_position_r=1.0, "
                           "max_sector_exposure_pct=40 DEĞİŞMEDİ (kart yalnız 2 parametre). "
                           "sector_cap paydası max_open_positions olduğundan sektör-başına fiili "
                           "tavan 2→8'e gevşedi (motor-içi doğal sonuç, beyanlı)"),
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
        },
        "performans": {
            "net_pnl_equity": net_pnl_equity, "net_pnl_trades": net_pnl_trades,
            "maxdd_kanonik": detail.get("max_drawdown"),       # kartın dd kıyası BUNUN üstünden
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
    (outdir / f"sonuc_c{ek}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str))
    (outdir / f"seanslar_c{ek}.json").write_text(
        json.dumps(sess, ensure_ascii=False, default=str))
    slim = [{k: t.get(k) for k in ("ts_open", "ts_close", "ticker", "r_multiple",
                                   "pnl_dollars", "exit_reason", "bars_held", "regime",
                                   "setup", "qty", "risk_dollars", "size_r")} for t in trades]
    (outdir / f"islemler_c{ek}.json").write_text(
        json.dumps(slim, ensure_ascii=False, default=str))

    print(f"\n=========== EDG-026 KOŞUM [c_slot20_r05{ek}] ===========")
    print(f"replay {r_start}→{r_end}  sv={sv}  sembol={len(bars)}  süre={sure}s")
    print(f"enjeksiyon: max_open {onceki['max_open_positions']}→{max_open}  "
          f"position_size_r {onceki['position_size_r']}→{params['position_size_r']}")
    print(f"bütünlük geçerli={out['butunluk']['gecerli']}  frame_miss={_frame_miss[0]} "
          f"dup={len(_dup)} scan!=plan={len(scan_vs_plan)} yasak={yasak_yuklu} "
          f"base_max_bozuk={len(base_max_bozuk)}")
    print(f"işlem n={n_islem} ({out['islem']['islem_yil']}/yıl)  net_pnl={net_pnl_equity}  "
          f"maxdd_kanonik={detail.get('max_drawdown')}  maxdd_m2m={maxdd_m2m}  "
          f"avg_r={detail.get('avg_r')}")
    print(f"tepe-ısı nominal: open-fazı max={isi['nominal_open_fazi_R'] and isi['nominal_open_fazi_R']['max']}R  "
          f"işlem-aralığı max={isi['nominal_islem_araligi_R'] and isi['nominal_islem_araligi_R']['max']}R  "
          f"eşzamanlı-poz max={isi['eszamanli_poz_max']}")
    print(f"NO_GO nedenleri: {out['islem']['nogo_neden_dagilim']}")
    print(f"birincil n={n_bir}  tavan_sifir %{tavan_pct_bir}")
    print(f"yazıldı: {outdir}/sonuc_c{ek}.json")


# ---------------------------------------------------------------------------------------------
# KIYAS — C (yerel) ↔ B (EDG-023 HAZIR çıktıları; YENİDEN KOŞULMAZ) → sonuc.json
# ---------------------------------------------------------------------------------------------
def kiyas():
    import numpy as np
    C = {"sonuc": json.loads((SANDBOX / "sonuc_c.json").read_text()),
         "seans": json.loads((SANDBOX / "seanslar_c.json").read_text()),
         "islem": json.loads((SANDBOX / "islemler_c.json").read_text())}
    B = {"sonuc": json.loads((EDG023 / "sonuc_varyant.json").read_text()),
         "seans": json.loads((EDG023 / "seanslar_varyant.json").read_text()),
         "islem": json.loads((EDG023 / "islemler_varyant.json").read_text())}

    sc, sb = C["sonuc"], B["sonuc"]

    # ---- şasi kimliği: motor sha'ları B ile birebir mi? (kart: değilse kıyas ŞERHLİ) ---------
    motor_c, motor_b = sc["motor_sha256_16"], sb["motor_sha256_16"]
    motor_ayni = {f: (motor_c.get(f) == motor_b.get(f) and motor_c.get(f) is not None)
                  for f in ("broker.py", "backtest.py", "strategy.py")}
    config_ayni = {f: (sc["config_sha256_16"][f]["sandbox"] == sb["config_sha256_16"][f]["sandbox"]
                       and sc["config_sha256_16"][f]["sandbox"] is not None)
                   for f in ("goal.yaml", "strategy.yaml", "bounds.yaml")}
    serh = None
    if not all(motor_ayni.values()) or not all(config_ayni.values()):
        serh = ("MOTOR/CONFIG SHA'LARI B İLE BİREBİR DEĞİL — kıyas ŞERHLİDİR (kart universe "
                f"koşulu): motor={motor_ayni} config={config_ayni}")

    # rampa kimliği: iki koşum da 15/36 bandında koşmuş olmalı
    rampa_ayni = (sc["rampa"]["tam_dd"] == sb["rampa"]["tam_dd"] == 0.15
                  and sc["rampa"]["sifir_dd"] == sb["rampa"]["sifir_dd"] == 0.36)

    # takvim kimliği
    tarih_c = [s["date"] for s in C["seans"]]
    tarih_b = [s["date"] for s in B["seans"]]
    takvim_ayni = (tarih_c == tarih_b)
    aylar = sorted({d[:7] for d in tarih_c})
    M = len(aylar)

    # ---- eşlenik ay-kümeli bootstrap: işlem farkı (C−B) + oran -------------------------------
    def ay_islem(islemler):
        c = {a: 0 for a in aylar}
        for t in islemler:
            a = str(t["ts_open"])[:7]
            if a in c:
                c[a] += 1
        return np.array([c[a] for a in aylar], dtype=float)

    cB, cC = ay_islem(B["islem"]), ay_islem(C["islem"])

    rng = np.random.default_rng(BOOT_SEED)
    fark = np.empty(BOOT_ITER)
    oran = []                                   # cB*=0 iterasyonu atlanır (sayısı raporlanır)
    idx_all = np.arange(M)
    for i in range(BOOT_ITER):
        pick = rng.choice(idx_all, size=M, replace=True)     # EŞLENİK: aynı çekiliş iki koşuma
        tB, tC = float(cB[pick].sum()), float(cC[pick].sum())
        fark[i] = tC - tB
        if tB > 0:
            oran.append(tC / tB)

    def ci95(arr):
        a = np.asarray([x for x in arr if x == x])
        if not len(a):
            return None                                       # ölçülemedi
        return {"lo": round(float(np.percentile(a, 2.5)), 3),
                "hi": round(float(np.percentile(a, 97.5)), 3),
                "orta": round(float(np.median(a)), 3)}

    fark_ci, oran_ci = ci95(fark), ci95(oran)
    nB, nC = int(cB.sum()), int(cC.sum())

    # ---- tepe-ısı: C (kendi bloğu) + B (nominal 1.0R×n — B'nin HAZIR seans/işlem dosyalarından)
    b_isi_open = _isi_ozet([s["n_acik"] * B_BOYUT_R for s in B["seans"]])
    b_aralik = _islem_araligi_sayimi(B["islem"], tarih_b)
    b_isi_aralik = _isi_ozet([n * B_BOYUT_R for n in b_aralik])
    isi_kiyas = {
        "C_slot20_r05": sc["tepe_isi"],
        "B_slot5_r10": {
            "formul": f"nominal = n_eszamanli × {B_BOYUT_R}R (B'nin pozisyon-başına nominal R'si)",
            "nominal_open_fazi_R": b_isi_open,
            "nominal_islem_araligi_R": b_isi_aralik,
            "gerceklesen_open_fazi": None,
            "gerceklesen_neden_yok": ("B seans şemasında size_r/risk_dollars alanı yok; yeniden "
                                      "koşum kart gereği YASAK (hazır çıktı okunur) — ölçülemedi"),
            "eszamanli_poz_max": {"open_fazi": max((s["n_acik"] for s in B["seans"]), default=0),
                                  "islem_araligi": max(b_aralik, default=0)},
        },
    }

    perf_c, perf_b = sc["performans"], sb["performans"]

    # ---- kill bayrakları — kartın DONUK eşikleri; HÜKÜM DEĞİL, koşul değerinin kaydı ---------
    artis_ci_0_disi = (fark_ci is not None and fark_ci["lo"] > 0)
    kill1 = {
        "esik": "işlem sayısı B'ye göre CI ile ARTMIYORSA slot artışı fiilen İNERT (kart kill#1)",
        "fark_ci95": fark_ci, "artis_ci_0_disi": artis_ci_0_disi,
        "tetiklendi": not artis_ci_0_disi,
        "beyan": (None if artis_ci_0_disi else
                  "slot artışı fiilen İNERT — işlem artışı CI 0'ı dışlamıyor; bağlayıcı kısıt "
                  "başka yerde (NO_GO neden dağılımına ve doluluk/ısı tablosuna bak)"),
    }
    ddb, ddc = perf_b.get("maxdd_kanonik"), perf_c.get("maxdd_kanonik")
    kill2 = {
        "esik": f"maxdd_C > {KILL_DD_KATSAYI} × maxdd_B (kanonik) → 'öneri' dili kullanılmaz (kart kill#2)",
        "maxdd_B": ddb, "maxdd_C": ddc,
        "oran": round(ddc / ddb, 3) if (ddb not in (None, 0) and ddc is not None) else None,
        "tetiklendi": (ddc > KILL_DD_KATSAYI * ddb)
        if (ddb not in (None, 0) and ddc is not None) else None,
        "m2m_yalniz": {"B": perf_b.get("maxdd_m2m"), "C": perf_c.get("maxdd_m2m"),
                       "tetiklendi": (perf_c["maxdd_m2m"] > KILL_DD_KATSAYI * perf_b["maxdd_m2m"])
                       if (perf_b.get("maxdd_m2m") not in (None, 0)
                           and perf_c.get("maxdd_m2m") is not None) else None},
    }
    kill3 = {
        "esik": "şasi bütünlüğü (frame_miss=0, dup=0, scan==plan, yasak modül yok, base_max==20)",
        "C": sc["butunluk"]["gecerli"], "B": sb["butunluk"]["gecerli"],
        "tetiklendi": not (sc["butunluk"]["gecerli"] and sb["butunluk"]["gecerli"]),
    }

    def satir(*yol):
        def cek(s):
            v = s
            for k in yol:
                v = v.get(k) if isinstance(v, dict) else None
                if v is None:
                    return None
            return v
        return {"B_slot5_r10": cek(sb), "C_slot20_r05": cek(sc)}

    tablo = {
        "islem_n": {"B_slot5_r10": nB, "C_slot20_r05": nC, "fark": nC - nB,
                    "fark_pct": round(100.0 * (nC - nB) / nB, 1) if nB else None},
        "islem_yil": satir("islem", "islem_yil"),
        "islem_fark_ci95_ay_kumeli_eslenik": fark_ci,
        "islem_oran_ci95": oran_ci,
        "silahlanan_plan": satir("islem", "silahlanan_plan"),
        "toplam_plan": satir("islem", "toplam_plan"),
        "verdict_dagilim_C": sc["islem"].get("verdict_dagilim"),
        "nogo_neden_dagilim_C": sc["islem"].get("nogo_neden_dagilim"),
        "nogo_neden_dagilim_B": None,   # ölçülemedi: B plan_log'u 023 çıktısında saklanmadı (beyan)
        "entry_rejects": satir("islem", "entry_rejects"),
        "exit_reason_dagilim": satir("islem", "exit_reason_dagilim"),
        "net_pnl_equity": satir("performans", "net_pnl_equity"),
        "net_pnl_trades": satir("performans", "net_pnl_trades"),
        "maxdd_kanonik": satir("performans", "maxdd_kanonik"),
        "maxdd_m2m": satir("performans", "maxdd_m2m"),
        "avg_r": satir("performans", "avg_r"),
        "win_rate": satir("performans", "win_rate"),
        "sharpe": satir("performans", "sharpe"),
        "score": satir("performans", "score"),
        "total_return": satir("performans", "total_return"),
        "doluluk_pozisyon_gun": satir("doluluk", "pozisyon_gun_open_fazi"),
        "ort_acik_pozisyon": satir("doluluk", "ort_acik_pozisyon"),
        "doluluk_orani_slot": {"B_slot5_r10": (round(sb["doluluk"]["ort_acik_pozisyon"] / 5, 4)
                                               if sb["doluluk"].get("ort_acik_pozisyon") is not None else None),
                               "C_slot20_r05": sc["doluluk"].get("doluluk_orani_slot")},
        "toplam_bars_held": satir("doluluk", "toplam_bars_held"),
        "tasnif_birincil": satir("birincil", "dagilim"),
        "tavan_sifir_birincil_pct": satir("birincil", "tavan_sifir_pct"),
        "tasnif_tum_seans": satir("tasnif_tum_seans", "dagilim"),
        "ci95_ay_kumeli_kosum_ici": {"B_slot5_r10": sb.get("ci95_ay_kumeli"),
                                     "C_slot20_r05": sc.get("ci95_ay_kumeli")},
        "eff_max_open_lt_base_n": satir("betim", "eff_max_open_lt_base_n"),
        "acik_slot_le0_n": satir("betim", "acik_slot_le0_n"),
        "dd_gt_tam_esik_n": satir("betim", "dd_gt_tam_esik_n"),
    }

    out = {
        "kart": "EDG-2026-026",
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "kiyas_taban": {"kaynak": "EDG-023 varyant (B) HAZIR çıktıları — yeniden koşulmadı",
                        "dosyalar": [str(EDG023 / "sonuc_varyant.json"),
                                     str(EDG023 / "seanslar_varyant.json"),
                                     str(EDG023 / "islemler_varyant.json")]},
        "sasi_kimligi": {"motor_sha_ayni": motor_ayni, "config_sha_ayni": config_ayni,
                         "rampa_ayni_15_36": rampa_ayni, "takvim_ayni": takvim_ayni,
                         "serh": serh},
        "yontem": {
            "eslenik_bootstrap": ("ay-kümeli EŞLENİK bootstrap: aynı ay çekilişi iki koşuma "
                                  f"birden; fark = C − B; iter={BOOT_ITER}, seed={BOOT_SEED}, "
                                  f"n_ay={M}"),
            "islem_ay_anahtari": "ts_open[:7] (giriş ayı)",
            "oran_atlanan_iter": BOOT_ITER - len(oran),
        },
        "param_enjeksiyon": sc["param_enjeksiyon"],
        "butunluk": {"C": sc["butunluk"], "B": sb["butunluk"]},
        "kill1_islem_artisi": kill1,
        "kill2_maxdd_1p5x": kill2,
        "kill3_butunluk": kill3,
        "tepe_isi": isi_kiyas,
        "tablo": tablo,
        "dosyalar": {"C": {"sonuc": "sonuc_c.json", "seanslar": "seanslar_c.json",
                           "islemler": "islemler_c.json"},
                     "B": "EDG-023 dizini (kiyas_taban.dosyalar)"},
    }
    (SANDBOX / "sonuc.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))

    print("\n==================== EDG-026 C↔B ÖZET ====================")
    print(f"şasi: motor_ayni={all(motor_ayni.values())} config_ayni={all(config_ayni.values())} "
          f"rampa_ayni={rampa_ayni} takvim_ayni={takvim_ayni}  şerh={serh}")
    print(f"işlem: B {nB} → C {nC}  fark={nC-nB}  CI95={fark_ci}  oran CI={oran_ci}")
    print(f"KILL#1 tetiklendi={kill1['tetiklendi']} (artış CI-0-dışı={artis_ci_0_disi})")
    print(f"maxdd kanonik: B {ddb} → C {ddc}  oran={kill2['oran']}  KILL#2(×{KILL_DD_KATSAYI}) "
          f"tetiklendi={kill2['tetiklendi']}")
    print(f"KILL#3 (bütünlük) tetiklendi={kill3['tetiklendi']}")
    ic = sc["tepe_isi"]
    print(f"tepe-ısı C: open-fazı max={ic['nominal_open_fazi_R'] and ic['nominal_open_fazi_R']['max']}R  "
          f"işlem-aralığı max={ic['nominal_islem_araligi_R'] and ic['nominal_islem_araligi_R']['max']}R  "
          f"gerçekleşen ΣR max={ic['gerceklesen_open_fazi']['size_r_toplam'] and ic['gerceklesen_open_fazi']['size_r_toplam']['max']}")
    print(f"tepe-ısı B: open-fazı max={b_isi_open and b_isi_open['max']}R  "
          f"işlem-aralığı max={b_isi_aralik and b_isi_aralik['max']}R")
    print(f"net_pnl: {tablo['net_pnl_equity']}  avg_r: {tablo['avg_r']}  maxdd: {tablo['maxdd_kanonik']}")
    print(f"NO_GO nedenleri (C): {tablo['nogo_neden_dagilim_C']}")
    print(f"yazıldı: {SANDBOX/'sonuc.json'}")
    print("==========================================================\n")


if __name__ == "__main__":
    mod = sys.argv[1] if len(sys.argv) > 1 else ""
    smoke = "--smoke" in sys.argv
    if mod == "c":
        kosum(smoke=smoke)
    elif mod == "kiyas":
        kiyas()
    else:
        sys.exit("kullanım: olcum.py {c|kiyas} [--smoke]")

"""EDG-2026-028 — ISI KOŞUL AYARI · ölçüm aracı (2026-08-12)

Kart: research/cards/EDG-2026-028-isi-kosul-ayari.yaml (OKU-DOKUNMA; parameter_grid'in
2026-08-12 DEĞİŞİKLİK notu DAHİL: T10 hücresi + cap10 zarf enjeksiyonu). Hüküm Rol-1'in.
Rol: ÖLÇÜM ajanı. Bu modül HÜKÜM VERMEZ, karta dokunmaz, git/canlı/broker/state'e YAZMAZ.
Şasi: EDG-026 (research/olcumler/edg026_slot20_2026-08-12/olcum.py) C-koşum düzeni AYNEN
devralındı: izole sandbox, rampa-15/36 monkeypatch (023 beyanlı deseni), slot-20 + 0.5R
param-enjeksiyonları, kancalar, bütünlük kontrolleri, eşlenik ay-kümeli bootstrap
(5000 iter, seed 20260812). meridian.loop/counterfactual/cf_backfill/hermes İTHAL EDİLMEZ.

ÜÇ KOŞUM (kart parameter_grid AYNEN — yontem: [T10_sabit, rejim_haritali_cap10,
vol_hedefleme_cap10]):
  (T10) sabit-10R  : C dünyası + ZARF ENJEKSİYONU heat_hard_r 5.0→10.0; modülasyon YOK.
                     Zarf-etkisi = T10 vs C@5 (C@5 = EDG-026 HAZIR çıktıları, yeniden koşulmaz).
  (Y1)  rejim-haritalı cap10: seans rejimi r → ısı-tavanı {trend_up:10, chop:6, high_vol:4,
                     trend_down:2} R; slot-eşdeğeri = ısı/0.5R (20/12/8/4 pozisyon).
  (Y2)  vol-hedef cap10: gerçekleşen-vol = T10 KOŞUMUNUN günlük M2M getiri serisinin 20g
                     kayan std'si (yıllıklaştırılmış, ddof=1, ×√252; pencere o güne KADAR ve
                     o gün DAHİL — yalnız geçmiş); hedef = o serinin MEDYANI (DONUK — T10
                     bitince BİR KEZ hesaplanır, Y2 sabit kullanır, seans-içi yeniden
                     hesaplanmaz); ısı_t = clip(10 × hedef/vol_t, 2, 10).
  SIRA: T10 önce (Y2'nin hedefi ondan türer), sonra Y1+Y2.

ZARF ENJEKSİYONU — MOTOR SABİTİNİN YERİ VE YÜZEY BEYANI (kart DEĞİŞİKLİK notu):
  * Motor sabiti: guard.HEAT_HARD_R = 5.0 (guard.py:292) yalnız FAIL-SAFE'tir; KANONİK kaynak
    goal.yaml `limits.heat_hard_r: 5.0` (C24 taşıması) ve guard.classify_gate HER çağrıda
    `goal["limits"]`ten okur (guard.py:318). EDG-026 raporunun "zarf sabiti" dediği şey budur.
  * Enjeksiyon: config.goal() DERİN KOPYASININ limits sözlüğüne heat_hard_r=10.0 yazılır —
    026'nın max_open_positions enjeksiyonuyla AYNI SINIF (sözlük girdisi). MOTOR DOSYASINA
    TEK BAYT YAZILMAZ; monkeypatch yalnız rampa (023 deseni) + koşul-tabanlı max_positions_at
    sarmalayıcısı (aşağıda) — ikisi de ölçüm-içi, BEYANLI.
  * heat_review_r=3.5, corr_review=0.85, max_position_r=1.0, max_sector_exposure_pct=40
    DEĞİŞMEDİ (kart yalnız ısı tavanını enjekte eder; REVIEW yumuşak bayrağı silahlanmayı
    kesmez). max_open_positions=20 sabit kalır (026 dünyası).

ISI MODÜLASYONU — İKİ YÜZEY, TEK TAVAN (kart universe: "eff_max_open türetimine
koşul-çarpanı"; ölçüm-içi enjeksiyon BEYANLI, motor dosyası DEĞİŞMEZ):
  (a) ISI KAPISI (silahlanma, CLOSE fazı): goal["limits"]["heat_hard_r"] seans başına
      tavan_t'ye çekilir — classify_gate'in "heat_hard" sert kuralı armed+plan kümülatif
      size_r'ını tavana karşı keser (backtest.py open_risk_r armed'ı SAYAR).
  (b) SLOT-EŞDEĞERİ (dolum, OPEN fazı): brk.max_positions_at sarmalanır —
      eff = ORİJİNAL_max_positions_at(eq, peak, min(base_max, round(tavan_t/0.5R))).
      Koşul-çarpanı böylece motorun KENDİ yuvarlama/taban yasasıyla (max(1,·), rampa-0'da 0)
      ÇARPIMSAL birleşir (kart tezi: rampa öz-performans ekseniyle çarpımsal); formül
      KOPYALANMAZ, orijinal fonksiyon çağrılır. tavan=10 → taban 20 → T10/C ile birebir.
  ZAMANLAMA (ileri-bakışsızlık): tavan_t CLOSE(t)'de güncellenir (Y1: motorun O SEANS
      rejimi build_regime_json(t)'den; Y2: T10 serisinin t-DAHİL penceresi) → CLOSE(t)
      silahlanması ve OPEN(t+1) dolumu AYNI tavanı görür. İlk seansın OPEN'ı (henüz rejim
      yok) varsayılan 10R — pozisyon da yok, atıl; beyanlı. Y2 warmup (<20 getiri) → 10R
      (modülasyonsuz), beyanlı. Eşleşmeyen rejim/tarih → 10R + SAYILIR (YASA-4, sessiz değil).
  MEVCUT POZİSYONLAR KESİLMEZ: modülasyon yalnız YENİ girişi kısar (kart tezi "tavanın
      ALTINDA koşul-duyarlı kısma"); tavan düşünce miras kalan açık ısı tavan-üstü kalabilir —
      bu ÖLÇÜM BULGUSUdur, "tavan_ustu_seans_n" ile raporlanır, kusur değil.

KIYAS TABANLARI:
  * C@5 = EDG-026 sonuc_c/seanslar_c/islemler_c (SALT-OKU; dosya sha256 kaydedilir; motor/config
    sha'ları birebir DOĞRULANIR — değilse kıyas ŞERHLİ + kill-C bayrağı: "ölçüm bekler").
  * C@5'te M2M eğrisi SAKLANMAMIŞ → zarf kıyasında dd/sharpe için ay-kümeli CI ÖLÇÜLEMEZ
    (None + bu neden; UYDURMA YASAĞI). İşlem-bazlı CI'lar (n, P&L, R) ölçülür; dd/sharpe
    kapalı-işlem eğrisinden CI + kanonik NOKTA kıyas verilir.
  * Yx-vs-T10: üç koşum da bu modülden → tam set (n, P&L, R, kapalı-dd, M2M-dd, günlük-sharpe).

TANIMLAR (ölçümden ÖNCE donduruldu; 026 şasisiyle aynı olanlar AYNEN):
  islem / ay kümesi (ts_open[:7]) / doluluk / TEPE-ISI (nominal+gerçekleşen) / max-dd kanonik
  (score.score_detail: kapalı ∨ M2M kötüsü) / net P&L (M2M son − 100k; çapraz Σ pnl_dollars)
  / NO_GO neden dağılımı: 026 tanımları AYNEN.
  eşlenik bootstrap  = ay-kümeli, AYNI ay çekilişi tüm koşumlara (5000 iter, seed 20260812);
                       fark = hücre − taban. Kapalı-dd/M2M-dd/sharpe iterasyonda ay-BLOK
                       birleştirme sırasıyla kurulur (küme bootstrap standardı; global
                       kronolojik yeniden sıralama YAPILMAZ — beyanlı).
  günlük-sharpe      = M2M günlük getiri mean/std(ddof=1)×√252 (bootstrap'ta iyi tanımlı);
                       motor-kanonik işlem-bazlı sharpe (score_detail) NOKTA olarak ayrıca.
  gerçekleşen-ısı    = open-fazında açık pozisyonların Σ size_r (silahlanmış gerçek R);
                       rejim kırılımı seansın KENDİ rejim etiketiyle (close-fazı etiketi).
  OTOMATİK-BENİMSEME EŞİĞİ (kart, DONUK — İŞARETLENİR, HÜKÜM VERİLMEZ; zarf 5→10 kararı
  PENCEREDE): (i) maxdd_kanonik(Yx) < maxdd_kanonik(T10) [nokta] VE (ii) net P&L farkı
  (Yx−T10) CI'ının ÜST ucu ≥ 0 [CI 0'ı içeriyor-ya-da-üstünde] VE (iii) n(Yx) ≥ 0.6×n(T10).

KILL KONTROLLERİ (kart, DONUK — koşul değerinin kaydı, hüküm DEĞİL):
  kill-C   : C@5 sha-doğrulanamaz ya da 026 şasisi geçersiz → ölçüm bekler (önkoşul).
  kill-Y2  : vol-serisi ileri-bakış sızıntısı — kontrol: hedef T10-serisi medyanı olarak
             DONUK (bir kez, koşum öncesi), kayan-vol penceresi her seansta yalnız o güne
             kadar; NOKTA-KONTROL: 3 örnek tarihte vol, yalnız o güne kadar KESİLMİŞ seriden
             yeniden hesaplanır ve birebir eşitlenir. Tutmazsa → Y2 hücresi geçersiz.
  kill-debi: HER İKİ yöntemde de n < 0.6×n(T10) → otomatik-benimseme YAPILMAZ bayrağı
             (sayılar pencereye).
  + şasi bütünlüğü koşum başına: frame_miss=0, dup=0, scan==plan, yasak modül yok,
    base_max_open==20, zarf enjeksiyonu görünür (öz-sınamalar).

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen = None + neden); YASA-4 (sessiz-yutma işaretli +
gerekçe); YASA-6 (okuyucu: ekri_t10 → Y2 hedefi + kiyas bootstrap; sonuc_*/seanslar_*/
islemler_*/ekri_* → `kiyas`; sonuc.json → dönüş raporu + Rol-1). SALT-OKUMA: config.STATE
koşum-başına izole sandbox; barlar sembolik bağla SALT-OKUNUR; canlı state'e ve motor
dosyalarına tek bayt yazılmaz.

KULLANIM:
  olcum.py t10 [--smoke]     # önce bu (Y2 hedefi bundan türer) → sonuc_t10 + ekri_t10 ...
  olcum.py y1  [--smoke]
  olcum.py y2  [--smoke]     # ekri_t10 şart (SIRA yasası)
  olcum.py kiyas             # T10/Y1/Y2 (yerel) + C@5 (026 HAZIR) → sonuc.json
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
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
REPLAY_END = "2026-07-30"                      # 023/026 ile AYNI pencere
BOOT_SEED = 20260812
BOOT_ITER = 5000

RAMPA = {"tam_dd": 0.15, "sifir_dd": 0.36}     # C dünyası — monkeypatch (023 beyanlı deseni)
SLOT = 20                                      # goal/limits enjeksiyonu (026)
BOYUT_R = 0.5                                  # strateji params enjeksiyonu (026 yüzey beyanı)
ZARF_R = 10.0                                  # ZARF ENJEKSİYONU: heat_hard_r 5.0→10.0 (kart)
C5_ZARF_R = 5.0                                # C@5 referansının zarfı (026'da değişmedi)

Y1_HARITA = {"trend_up": 10.0, "chop": 6.0, "high_vol": 4.0, "trend_down": 2.0}   # kart grid
Y2_VOL_PENCERE = 20                            # 20g kayan std (kart)
Y2_BANT = (2.0, 10.0)                          # clip bandı [2R, 10R] (kart)
YILLIK_KOK = math.sqrt(252.0)

KART3 = ["tavan_sifir", "evren_bagladi", "derisk_bagladi"]
YASAK = ("meridian.loop", "meridian.counterfactual", "meridian.cf_backfill", "meridian.hermes")
KOSUMLAR = ("t10", "y1", "y2")

# NO_GO/REVIEW neden eşlemesi — 026 listesi AYNEN + earnings notunun GERÇEK alt-dizgisi
# (026'da "kazanç kapsamı" eşleşmiyordu ve HAM sayılıyordu; sayım davranışı AYNI, yalnız
# etiket düzgün — raporlama iyileştirmesi, ölçüm değişikliği değil; beyanlı).
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
    ("earnings_coverage_note", "earnings_kapsami_yok"),
    ("earnings_coverage_note", "kazanç kapsamı"),
]


def _sha16(p: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    except OSError:
        return None    # ölçülemedi (dosya yok/okunamadı) — None, uydurma özet değil


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
            # DOSYALAR DEĞİŞTİRİLMEZ: tüm enjeksiyonlar YÜKLENMİŞ sözlüklere — config sha'ları
            # 026/023 ile bayt-aynı kalır ve şasi kimliği sha ile kanıtlanır.
            shutil.copyfile(EDG022 / "state" / f, dst)
    return st


def _rampa_fn(tam_dd: float, sifir_dd: float):
    def derisk_mult_param(equity: float, peak: float) -> float:
        # broker.derisk_mult'un birebir aynası — yalnız 0.03/DERISK_FLOOR_DD yerine parametre (023).
        if peak <= 0:
            return 1.0
        dd = (peak - equity) / peak
        if dd <= tam_dd:
            return 1.0
        if dd >= sifir_dd:
            return 0.0
        return round(1.0 - (dd - tam_dd) / (sifir_dd - tam_dd), 4)
    return derisk_mult_param


# SINIFLAMA — EDG-022 DONUK kuralı (AYNEN; ısı bağlaması NO_GO neden dağılımından okunur)
def classify(rec: dict, no_trade_before: int) -> str:
    acik_slot = rec["acik_slot"]
    if acik_slot <= 0:
        return "tavan_sifir"
    if rec["bar_i"] is not None and rec["bar_i"] < no_trade_before:
        return "isinma"
    if (rec["exposure_budget_pct"] or 0) <= 0:
        return "rejim_kapali"
    return "evren_bagladi" if rec["aday_n"] <= acik_slot else "derisk_bagladi"


def bootstrap_ci_tasnif(sess: list[dict], siniflar: list[str], n_iter: int = BOOT_ITER,
                        seed: int = BOOT_SEED) -> dict:
    """Ay-kümeli bootstrap %95 CI (tasnif oranları) — 026 şasi fonksiyonu AYNEN."""
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
# Y2 ÖN-HAZIRLIK — T10 M2M eğrisinden vol serisi + DONUK hedef (kill-Y2 kontrolü içeride)
# ---------------------------------------------------------------------------------------------
def y2_seri_kur(ekri_path: pathlib.Path) -> dict:
    """T10 equity eğrisi → günlük getiri → 20g kayan std (yıllık, ddof=1, pencere t-DAHİL,
    yalnız geçmiş) → hedef = serinin MEDYANI (DONUK) → tarih→tavan haritası.
    Dönüş: {hedef, vol_by_date, tavan_by_date, warmup_n, sizinti_kontrol, ekri_sha}."""
    import numpy as np
    ekri = json.loads(ekri_path.read_text())                  # [(date, eq)]
    tarih = [str(r[0])[:10] for r in ekri]
    eq = np.asarray([float(r[1]) for r in ekri], dtype=float)
    if len(eq) < Y2_VOL_PENCERE + 2:
        raise SystemExit(f"Y2: T10 eğrisi çok kısa ({len(eq)}) — vol serisi kurulamaz")
    getiri = eq[1:] / eq[:-1] - 1.0                            # getiri[i] = tarih[i+1]'in getirisi
    vol_by_date: dict[str, float | None] = {tarih[0]: None}
    for i in range(1, len(tarih)):
        # tarih[i] için pencere: getiri[i-1] DAHİL geriye Y2_VOL_PENCERE getiri (yalnız geçmiş+o gün)
        if i < Y2_VOL_PENCERE:
            vol_by_date[tarih[i]] = None                       # warmup — ölçülemedi (None, uydurma yok)
            continue
        pencere = getiri[i - Y2_VOL_PENCERE:i]
        vol_by_date[tarih[i]] = float(np.std(pencere, ddof=1) * YILLIK_KOK)
    dolu = [v for v in vol_by_date.values() if v is not None]
    hedef = float(np.median(dolu))                             # DONUK — bir kez, burada
    lo, hi = Y2_BANT

    def tavan(v: float | None) -> float:
        if v is None:
            return ZARF_R          # warmup: modülasyonsuz 10R (beyanlı)
        if v <= 0.0:
            return hi              # vol 0 → oran ∞ → clip üst bant (beyanlı; yatay eğri = vol yok)
        return float(min(hi, max(lo, ZARF_R * hedef / v)))

    tavan_by_date = {d: tavan(v) for d, v in vol_by_date.items()}

    # kill-Y2 NOKTA-KONTROL: 3 örnek tarihte vol, yalnız o güne kadar KESİLMİŞ seriden yeniden
    # hesaplanır — tam-seri değeriyle birebir eşit olmalı (pencere ileriye bakmıyor kanıtı).
    kontrol = []
    n = len(tarih)
    for frac in (0.25, 0.5, 0.75):
        i = max(Y2_VOL_PENCERE, min(n - 1, int(n * frac)))
        eq_kesik = eq[:i + 1]                                  # yalnız tarih[i]'ye kadar (dahil)
        g_kesik = eq_kesik[1:] / eq_kesik[:-1] - 1.0
        v_kesik = float(np.std(g_kesik[-Y2_VOL_PENCERE:], ddof=1) * YILLIK_KOK)
        v_tam = vol_by_date[tarih[i]]
        kontrol.append({"tarih": tarih[i], "vol_tam_seri": v_tam, "vol_kesik_seri": v_kesik,
                        "esit": bool(v_tam is not None and abs(v_tam - v_kesik) < 1e-12)})
    sizinti = {"hedef_donuk": True,
               "hedef_kaynagi": "T10 kayan-vol serisinin medyanı — Y2 koşumu İÇİNDE yeniden hesaplanmaz",
               "nokta_kontrol": kontrol,
               "tetiklendi": (not all(k["esit"] for k in kontrol))}
    return {"hedef_vol_yillik": hedef, "vol_by_date": vol_by_date, "tavan_by_date": tavan_by_date,
            "warmup_seans_n": sum(1 for v in vol_by_date.values() if v is None),
            "sizinti_kontrol": sizinti, "ekri_sha256": _sha_full(ekri_path),
            "ekri_dosya": str(ekri_path)}


# ---------------------------------------------------------------------------------------------
# KOŞUM (t10 | y1 | y2)
# ---------------------------------------------------------------------------------------------
def kosum(run: str, smoke: bool = False):
    assert run in KOSUMLAR
    outdir = (SANDBOX / "smoke") if smoke else SANDBOX
    outdir.mkdir(exist_ok=True)
    ek = "_smoke" if smoke else ""
    r_start, r_end = (REPLAY_START, "2022-06-30") if smoke else (REPLAY_START, REPLAY_END)

    st_dir = hazirla(run + ek)
    sys.path.insert(0, str(REPO))

    from meridian import config
    config.STATE = st_dir                      # SALT-OKUMA İZOLASYONU: her yazım sandbox'a
    config.BARS = st_dir / "bars"
    config.HISTORY = st_dir / "history"

    import numpy as np                         # noqa: F401
    import yaml
    from meridian import backtest, dataset, guard, score as score_mod

    assert not hasattr(backtest, "wpg_overlay_day"), "motor YAMALI görünüyor — ölçüm geçersiz"
    assert not [m for m in sys.modules if m in YASAK], "yasaklı modül ithal edilmiş"

    brk = backtest.brk
    ORIJ_DERISK = brk.derisk_mult

    # ---- rampa kurulumu + öz-sınama (023/026 AYNEN) ------------------------------------------
    brk.derisk_mult = _rampa_fn(RAMPA["tam_dd"], RAMPA["sifir_dd"])
    assert brk.derisk_mult is not ORIJ_DERISK
    assert brk.derisk_mult(90.0, 100.0) == 1.0
    assert abs(brk.derisk_mult(80.0, 100.0) - 0.7619) < 1e-9
    assert brk.derisk_mult(64.0, 100.0) == 0.0
    assert brk.max_positions_at(80.0, 100.0, 5) == 4
    assert brk.max_positions_at(80.0, 100.0, 20) == 15

    # ---- girdiler + PARAM/ZARF ENJEKSİYONLARI (dosya DEĞİŞMEZ; sözlükler değişir) ------------
    stg = yaml.safe_load((st_dir / "strategy.yaml").read_text())
    params = dict(stg["params"])
    by_regime = stg.get("params_by_regime") or None
    sv = int(stg.get("version"))
    goal = config.goal()                                   # derin kopya — dosyaya/önbelleğe sızmaz

    onceki = {"max_open_positions": int(goal["limits"]["max_open_positions"]),
              "position_size_r": float(params["position_size_r"]),
              "heat_hard_r": float(goal["limits"]["heat_hard_r"])}
    assert onceki["heat_hard_r"] == C5_ZARF_R, \
        f"beklenen zarf sabiti 5.0 değil: {onceki['heat_hard_r']} — kart beyanı güncel değil"
    goal["limits"]["max_open_positions"] = SLOT            # ENJEKSİYON 1 (026)
    params["position_size_r"] = BOYUT_R                    # ENJEKSİYON 2 (026)
    goal["limits"]["heat_hard_r"] = ZARF_R                 # ENJEKSİYON 3 (028 ZARF: 5.0→10.0)

    for _rg in ("trend_up", "trend_down", "chop", "high_vol"):
        _eff = config.resolve_params(params, by_regime, _rg)
        assert float(_eff["position_size_r"]) == BOYUT_R, f"rejim override sızıntısı: {_rg}"
        assert ("position_size_r" not in ((by_regime or {}).get(_rg) or {}))
    assert float(goal["limits"]["max_position_r"]) >= BOYUT_R
    limits = goal["limits"]
    max_open = int(limits["max_open_positions"])
    no_trade_before = int(limits.get("no_trade_before_bars", 0))
    assert max_open == SLOT

    # ---- ZARF YÜZEYİ ÖZ-SINAMASI: classify_gate gerçekten goal['limits']ten mi okuyor? -------
    # Sentetik plan: 7.0R açık + 0.5R plan → @5 zarfta NO_GO(heat), @10 zarfta ısı kesmez.
    _tp = {"sector": "tech", "r_multiple_expected": 2.5, "size_r": 0.5, "score": 95}
    _pf = {"open_positions": 3, "sector_counts": {}, "day_pnl_pct": 0.0,
           "open_risk_r": 7.0, "max_corr": 0.0}
    _rj = {"exposure_budget_pct": 60, "leading_sectors": []}
    _g5 = {"limits": {**limits, "heat_hard_r": C5_ZARF_R}}
    _v5, _n5 = guard.classify_gate(_tp, _pf, _rj, _g5)
    assert _v5 == "NO_GO" and any("ısısı sert tavanı" in x for x in _n5), "5R zarf yüzeyi kanıtlanamadı"
    _v10, _n10 = guard.classify_gate(_tp, _pf, _rj, goal)
    assert _v10 != "NO_GO", f"10R enjeksiyonu ısı kapısına işlemedi: {_n10}"
    _pf2 = {**_pf, "open_risk_r": 9.8}
    _v10b, _n10b = guard.classify_gate(_tp, _pf2, _rj, goal)
    assert _v10b == "NO_GO" and any("ısısı sert tavanı" in x for x in _n10b), \
        "10R tavanın ÜSTÜ kesilmiyor — zarf enjeksiyonu yanlış yüzeyde"

    # ---- ISI MODÜLASYONU kurulumu ------------------------------------------------------------
    tavan_holder = [ZARF_R]                    # seans-içi geçerli tavan (R)
    kosul_sayac = {"esleme_disi_rejim": 0, "tarih_disi": 0}
    y2 = None
    if run == "y2":
        ekri_yol = outdir / f"ekri_t10{ek}.json"
        if not ekri_yol.exists():
            raise SystemExit(f"SIRA yasası: önce t10 koşulmalı — {ekri_yol} yok")
        y2 = y2_seri_kur(ekri_yol)
        if y2["sizinti_kontrol"]["tetiklendi"]:
            raise SystemExit("kill-Y2: vol serisi nokta-kontrolü TUTMADI — hücre geçersiz, onarım turu")

    def _kosul_base(base_max: int) -> int:
        # slot-eşdeğeri = ısı/0.5R; koşul-çarpanı orijinal max_positions_at'e TABAN olarak girer
        # (çarpımsal birleşim motorun kendi yasasıyla; formül kopyası YOK).
        return min(int(base_max), max(1, int(round(tavan_holder[0] / BOYUT_R))))

    _orig_maxpos = brk.max_positions_at
    # bileşim öz-sınaması (kayıt kancasından BAĞIMSIZ — frame sayaçlarını kirletmez)
    tavan_holder[0] = 6.0
    assert _kosul_base(20) == 12
    assert _orig_maxpos(100000.0, 100000.0, _kosul_base(20)) == 12       # m=1 → slot-eşdeğeri aynen
    assert _orig_maxpos(80000.0, 100000.0, _kosul_base(20)) == 9         # 12×0.7619→9 (çarpımsal)
    tavan_holder[0] = 2.0
    assert _kosul_base(20) == 4
    tavan_holder[0] = 4.0
    assert _kosul_base(20) == 8
    tavan_holder[0] = ZARF_R
    assert _kosul_base(20) == 20                                          # tavan=10 → T10/C mekaniği

    # ---- kancalar (026 şasi deseni + tavan alanları) -----------------------------------------
    seans_by_date: dict[str, dict] = {}
    _cur_close_date = [None]
    _dup: list[str] = []
    _frame_miss = [0]

    _orig_regime = backtest.regime_mod.build_regime_json
    _orig_scan = backtest.strat.scan_entry

    def _maxpos(equity, peak, base_max):
        n = _orig_maxpos(equity, peak, _kosul_base(base_max))   # GERÇEK eff (rampa × koşul)
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
            "isi_tavani_open": float(tavan_holder[0]),          # OPEN fazında geçerli tavan
            "kosul_slot_esdeger": int(_kosul_base(base_max)),
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
        # --- TAVAN GÜNCELLEME (CLOSE fazı; silahlanma + ertesi OPEN aynı tavanı görür) --------
        if run == "y1":
            yeni = Y1_HARITA.get(rj.get("regime"))
            if yeni is None:
                kosul_sayac["esleme_disi_rejim"] += 1          # YASA-4: sayılır, sessiz değil
                yeni = ZARF_R
        elif run == "y2":
            yeni = y2["tavan_by_date"].get(date)
            if yeni is None:
                kosul_sayac["tarih_disi"] += 1                 # YASA-4: sayılır, sessiz değil
                yeni = ZARF_R
        else:
            yeni = ZARF_R
        tavan_holder[0] = float(yeni)
        goal["limits"]["heat_hard_r"] = float(yeni)            # ısı kapısı yüzeyi (guard.py:318)
        if rec is not None:
            rec["isi_tavani_close"] = float(yeni)
            if run == "y2":
                rec["vol_t_yillik"] = (None if y2["vol_by_date"].get(date) is None
                                       else round(y2["vol_by_date"][date], 6))
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
    assert abs(goal["limits"]["heat_hard_r"] - tavan_holder[0]) < 1e-12   # yüzey-holder eşitlik çivisi

    # ---- plan_log çapraz-kontrolü + NO_GO/REVIEW neden dağılımı (026 AYNEN) ------------------
    plan_aday: dict[str, int] = {}
    plan_silahli: dict[str, int] = {}
    nogo_nedenler: list[str] = []
    review_nedenler: list[str] = []
    verdict_n = {"GO": 0, "REVIEW": 0, "NO_GO": 0}
    silahli_size_r: list[float] = []
    nogo_heat_rejim: dict[str, int] = {}       # rejim → ısı-NO_GO sayısı (modülasyon bağlaması)
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
            if any("ısısı sert tavanı" in x for x in (p.get("gate_reasons") or [])):
                rg = str(p.get("regime_at_plan"))
                nogo_heat_rejim[rg] = nogo_heat_rejim.get(rg, 0) + 1

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

    ci = bootstrap_ci_tasnif(birincil, KART3) if birincil else None

    # ---- işlem/doluluk/ısı/performans metrikleri (026 AYNEN) ---------------------------------
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

    # ---- REJİM KIRILIMI: gerçekleşen ısı + tavan + işlemler ----------------------------------
    import numpy as _np
    rejim_kirilim: dict[str, dict] = {}
    for rg in ("trend_up", "chop", "high_vol", "trend_down", None):
        grup = [r for r in sess if r.get("regime") == rg]
        if not grup:
            continue
        ger = _np.asarray([r["acik_size_r_toplam"] for r in grup], dtype=float)
        tav_o = _np.asarray([r.get("isi_tavani_open", ZARF_R) for r in grup], dtype=float)
        tav_c = _np.asarray([r.get("isi_tavani_close", ZARF_R) for r in grup], dtype=float)
        rejim_kirilim[str(rg)] = {
            "n_seans": len(grup),
            "tavan_close_ort": round(float(tav_c.mean()), 3),
            "tavan_open_ort": round(float(tav_o.mean()), 3),
            "gerceklesen_sizeR_ort": round(float(ger.mean()), 3),
            "gerceklesen_sizeR_p90": round(float(_np.percentile(ger, 90)), 3),
            "gerceklesen_sizeR_max": round(float(ger.max()), 3),
            "nominal_R_ort": round(float(_np.mean([r["n_acik"] * BOYUT_R for r in grup])), 3),
            "doluluk_kullanim_orani": (round(float((ger / tav_o).mean()), 4)
                                       if (tav_o > 0).all() else None),
            "tavan_ustu_seans_n": int((ger > tav_o + 1e-9).sum()),   # miras ısı (bulgu; kusur değil)
            "eff_max_open_ort": round(float(_np.mean([r["eff_max_open"] for r in grup])), 2),
        }
    islem_rejim: dict[str, dict] = {}
    for t in trades:
        rg = str(t.get("regime"))
        e = islem_rejim.setdefault(rg, {"n": 0, "pnl_dollars": 0.0, "r_toplam": 0.0})
        e["n"] += 1
        e["pnl_dollars"] += float(t.get("pnl_dollars", 0.0))
        e["r_toplam"] += float(t.get("r_multiple", 0.0))
    for rg, e in islem_rejim.items():
        e["pnl_dollars"] = round(e["pnl_dollars"], 2)
        e["avg_r"] = round(e["r_toplam"] / e["n"], 4) if e["n"] else None
        e["r_toplam"] = round(e["r_toplam"], 3)

    tavan_serisi_c = [r.get("isi_tavani_close", ZARF_R) for r in sess]
    tavan_hist: dict[str, int] = {}
    for v in tavan_serisi_c:
        k = f"{round(float(v), 1):.1f}"
        tavan_hist[k] = tavan_hist.get(k, 0) + 1

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

    modulasyon = {"t10": {"aktif": False, "tavan_sabit_R": ZARF_R},
                  "y1": {"aktif": True, "harita": Y1_HARITA,
                         "kaynak": ("motorun kendi seans rejimi (build_regime_json, CLOSE fazı); "
                                    "CLOSE(t) silahlanması ve OPEN(t+1) dolumu aynı tavanı görür"),
                         "esleme_disi_rejim_n": kosul_sayac["esleme_disi_rejim"]},
                  "y2": {"aktif": True, "bant_R": list(Y2_BANT), "vol_penceresi_g": Y2_VOL_PENCERE,
                         "hedef_vol_yillik": (round(y2["hedef_vol_yillik"], 6) if y2 else None),
                         "warmup_seans_n": (y2["warmup_seans_n"] if y2 else None),
                         "hedef_kaynagi_ekri": (y2["ekri_dosya"] if y2 else None),
                         "hedef_kaynagi_sha256": (y2["ekri_sha256"] if y2 else None),
                         "sizinti_kontrol": (y2["sizinti_kontrol"] if y2 else None),
                         "tarih_disi_n": kosul_sayac["tarih_disi"]}}[run]

    out = {
        "kart": "EDG-2026-028", "kosum": run, "smoke": smoke,
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sure_sn": sure,
        "rampa": {"tam_dd": RAMPA["tam_dd"], "sifir_dd": RAMPA["sifir_dd"],
                  "enjeksiyon": "MONKEYPATCH broker.derisk_mult (023/026 beyanlı deseni AYNEN)"},
        "param_enjeksiyon": {
            "max_open_positions": {"once": onceki["max_open_positions"], "sonra": SLOT,
                                   "yuzey": "goal['limits'] (026 AYNEN)"},
            "position_size_r": {"once": onceki["position_size_r"], "sonra": BOYUT_R,
                                "yuzey": "strateji params sözlüğü (026 yüzey beyanı AYNEN)"},
        },
        "zarf_enjeksiyon": {
            "heat_hard_r": {"once": onceki["heat_hard_r"], "sonra": ZARF_R,
                            "yuzey": ("goal['limits'] — classify_gate HER çağrıda buradan okur "
                                      "(guard.py:318); guard.HEAT_HARD_R=5.0 yalnız fail-safe "
                                      "(C24). Sözlük-enjeksiyonu; motor dosyası DEĞİŞMEDİ"),
                            "oz_sinama": "5R'de sentetik NO_GO(heat) + 10R'de geçiş + 10.3R'de NO_GO"},
            "degismeyen_zarf": ("heat_review_r=3.5R, corr_review=0.85, max_position_r=1.0, "
                                "max_sector_exposure_pct=40 AYNEN (kart yalnız ısı tavanı)"),
        },
        "isi_modulasyonu": {"kosum": run, **modulasyon,
                            "yuzeyler": ("(a) goal['limits']['heat_hard_r'] seans-başına (silahlanma "
                                         "kapısı) + (b) max_positions_at koşul-tabanı "
                                         "min(20, tavan/0.5R) (dolum tavanı; çarpımsal birleşim)"),
                            "tavan_close_histogram": dict(sorted(tavan_hist.items())),
                            "tavan_close_ort": round(float(_np.mean(tavan_serisi_c)), 4)},
        "motor_sha256_16": {f: _sha16(REPO / "meridian" / f)
                            for f in ("broker.py", "backtest.py", "strategy.py", "guard.py")},
        "config_sha256_16": {f: {"sandbox": _sha16(st_dir / f),
                                 "edg022": _sha16(EDG022 / "state" / f),
                                 "repo_state": _sha16(REPO / "state" / f)}
                             for f in ("goal.yaml", "strategy.yaml", "bounds.yaml")},
        "replay": {"start": r_start, "end": r_end, "strategy_version": sv,
                   "params_by_regime": bool(by_regime), "n_sembol": len(bars),
                   "n_endeks_satir": int(len(index)), "max_open": max_open,
                   "no_trade_before": no_trade_before,
                   "cost_model": {"slippage_bps": float(goal.get("slippage_bps", 5)),
                                  "commission_per_share": float(goal.get("commission_per_share", 0.0)),
                                  "not": "motorun kendi maliyet modeli — dokunulmadı (026 AYNEN; kart pessimistic_band_v2 rapor bandı ayrı)"}},
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
            "nogo_heat_rejim_dagilim": dict(sorted(nogo_heat_rejim.items(), key=lambda kv: -kv[1])),
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
        "rejim_kirilim": rejim_kirilim,
        "islem_rejim_dagilim": dict(sorted(islem_rejim.items(), key=lambda kv: -kv[1]["n"])),
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

    (outdir / f"sonuc_{run}{ek}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str))
    (outdir / f"seanslar_{run}{ek}.json").write_text(
        json.dumps(sess, ensure_ascii=False, default=str))
    slim = [{k: t.get(k) for k in ("ts_open", "ts_close", "ticker", "r_multiple",
                                   "pnl_dollars", "exit_reason", "bars_held", "regime",
                                   "setup", "qty", "risk_dollars", "size_r")} for t in trades]
    (outdir / f"islemler_{run}{ek}.json").write_text(
        json.dumps(slim, ensure_ascii=False, default=str))
    (outdir / f"ekri_{run}{ek}.json").write_text(
        json.dumps(res.equity, ensure_ascii=False, default=str))     # M2M eğrisi (Y2 + kiyas okur)

    print(f"\n=========== EDG-028 KOŞUM [{run}{ek}] ===========")
    print(f"replay {r_start}→{r_end}  sv={sv}  sembol={len(bars)}  süre={sure}s")
    print(f"enjeksiyon: max_open→{max_open}  size_r→{params['position_size_r']}  "
          f"heat_hard_r {onceki['heat_hard_r']}→{ZARF_R} (modülasyon={run != 't10'})")
    print(f"bütünlük geçerli={out['butunluk']['gecerli']}  frame_miss={_frame_miss[0]} "
          f"dup={len(_dup)} scan!=plan={len(scan_vs_plan)} yasak={yasak_yuklu} "
          f"base_max_bozuk={len(base_max_bozuk)}")
    print(f"tavan histogram (close): {out['isi_modulasyonu']['tavan_close_histogram']}")
    print(f"işlem n={n_islem} ({out['islem']['islem_yil']}/yıl)  net_pnl={net_pnl_equity}  "
          f"maxdd_kanonik={detail.get('max_drawdown')}  maxdd_m2m={maxdd_m2m}  "
          f"avg_r={detail.get('avg_r')}  sharpe={detail.get('sharpe')}")
    print(f"NO_GO nedenleri: {out['islem']['nogo_neden_dagilim']}")
    print(f"NO_GO(heat) rejim dağılımı: {out['islem']['nogo_heat_rejim_dagilim']}")
    print(f"tepe-ısı gerçekleşen ΣsizeR max="
          f"{isi['gerceklesen_open_fazi']['size_r_toplam'] and isi['gerceklesen_open_fazi']['size_r_toplam']['max']}")
    print(f"yazıldı: {outdir}/sonuc_{run}{ek}.json")
    print(f"KOSUM_{run.upper()}{ek.upper()}_BITTI")


# ---------------------------------------------------------------------------------------------
# KIYAS — T10/Y1/Y2 (yerel) ↔ C@5 (EDG-026 HAZIR) → sonuc.json
# ---------------------------------------------------------------------------------------------
def _yukle(prefix: str, dizin: pathlib.Path, adlar: dict) -> dict:
    d = {}
    for k, dosya in adlar.items():
        p = dizin / dosya
        d[k] = json.loads(p.read_text())
        d[f"{k}_sha256"] = _sha_full(p)
        d[f"{k}_dosya"] = str(p)
    d["_prefix"] = prefix
    return d


def kiyas():
    import numpy as np

    R = {}
    for run in KOSUMLAR:
        R[run] = _yukle(run, SANDBOX, {"sonuc": f"sonuc_{run}.json",
                                       "seans": f"seanslar_{run}.json",
                                       "islem": f"islemler_{run}.json",
                                       "ekri": f"ekri_{run}.json"})
    C5 = _yukle("c5", EDG026, {"sonuc": "sonuc_c.json", "seans": "seanslar_c.json",
                               "islem": "islemler_c.json"})

    # ---- şasi kimliği + kill-C (önkoşul) -----------------------------------------------------
    motor_simdiki = {f: _sha16(REPO / "meridian" / f) for f in ("broker.py", "backtest.py", "strategy.py")}
    motor_ayni = {}
    for f in ("broker.py", "backtest.py", "strategy.py"):
        degerler = {C5["sonuc"]["motor_sha256_16"].get(f), motor_simdiki[f],
                    *[R[r]["sonuc"]["motor_sha256_16"].get(f) for r in KOSUMLAR]}
        motor_ayni[f] = (len(degerler) == 1 and None not in degerler)
    config_ayni = {}
    for f in ("goal.yaml", "strategy.yaml", "bounds.yaml"):
        degerler = {C5["sonuc"]["config_sha256_16"][f]["sandbox"],
                    *[R[r]["sonuc"]["config_sha256_16"][f]["sandbox"] for r in KOSUMLAR]}
        config_ayni[f] = (len(degerler) == 1 and None not in degerler)
    rampa_ayni = all(R[r]["sonuc"]["rampa"]["tam_dd"] == 0.15 and
                     R[r]["sonuc"]["rampa"]["sifir_dd"] == 0.36 for r in KOSUMLAR) \
        and C5["sonuc"]["rampa"]["tam_dd"] == 0.15 and C5["sonuc"]["rampa"]["sifir_dd"] == 0.36
    tarihler = {r: [s["date"] for s in R[r]["seans"]] for r in KOSUMLAR}
    tarihler["c5"] = [s["date"] for s in C5["seans"]]
    takvim_ayni = (tarihler["t10"] == tarihler["y1"] == tarihler["y2"] == tarihler["c5"])
    butunluk_hepsi = all(R[r]["sonuc"]["butunluk"]["gecerli"] for r in KOSUMLAR) \
        and C5["sonuc"]["butunluk"]["gecerli"]
    kill_c = {
        "esik": "C@5 sha-doğrulanamaz ya da 026 şasisi geçersizse ölçüm bekler (kart kill#1)",
        "motor_sha_ayni": motor_ayni, "config_sha_ayni": config_ayni,
        "rampa_ayni_15_36": rampa_ayni, "takvim_ayni": takvim_ayni,
        "butunluk_hepsi_gecerli": butunluk_hepsi,
        "c5_dosya_sha256": {k: C5[f"{k}_sha256"] for k in ("sonuc", "seans", "islem")},
        "tetiklendi": not (all(motor_ayni.values()) and all(config_ayni.values())
                          and rampa_ayni and takvim_ayni and butunluk_hepsi),
    }
    serh = None
    if kill_c["tetiklendi"]:
        serh = ("ŞASİ KİMLİĞİ TUTMADI — kıyas ŞERHLİDİR (kart kill#1: C önkoşul): "
                f"motor={motor_ayni} config={config_ayni} rampa={rampa_ayni} takvim={takvim_ayni} "
                f"bütünlük={butunluk_hepsi}")

    aylar = sorted({d[:7] for d in tarihler["t10"]})
    M = len(aylar)
    ay_idx = {a: i for i, a in enumerate(aylar)}

    # ---- ay-kümeli hazırlıklar (işlem + günlük getiri) ---------------------------------------
    def islem_aylik(islemler):
        cnt = np.zeros(M)
        pnl = np.zeros(M)
        rlist: list[list[float]] = [[] for _ in range(M)]
        sirali: list[list[tuple]] = [[] for _ in range(M)]      # (ts_close, pnl) — kapalı-dd için
        for t in islemler:
            a = str(t["ts_open"])[:7]
            i = ay_idx.get(a)
            if i is None:
                continue     # sessiz-yutma DEĞİL: pencere-dışı ay yok (takvim_ayni çivisi); savunmacı dal
            cnt[i] += 1
            pnl[i] += float(t.get("pnl_dollars", 0.0))
            rlist[i].append(float(t.get("r_multiple", 0.0)))
            sirali[i].append((str(t.get("ts_close", "")), float(t.get("pnl_dollars", 0.0))))
        for i in range(M):
            sirali[i].sort()
            rlist[i] = np.asarray(rlist[i], dtype=float)
            sirali[i] = np.asarray([x[1] for x in sirali[i]], dtype=float)
        return {"cnt": cnt, "pnl": pnl, "r": rlist, "pnl_sirali": sirali}

    def gunluk_aylik(ekri):
        eq = np.asarray([float(e) for _, e in ekri], dtype=float)
        tar = [str(d)[:10] for d, _ in ekri]
        ret = eq[1:] / eq[:-1] - 1.0
        gr: list[list[float]] = [[] for _ in range(M)]
        for i in range(1, len(tar)):
            j = ay_idx.get(tar[i][:7])
            if j is not None:
                gr[j].append(float(ret[i - 1]))
        return [np.asarray(v, dtype=float) for v in gr]

    IA = {r: islem_aylik(R[r]["islem"]) for r in KOSUMLAR}
    IA["c5"] = islem_aylik(C5["islem"])
    GA = {r: gunluk_aylik(R[r]["ekri"]) for r in KOSUMLAR}     # C@5 M2M eğrisi YOK (beyan aşağıda)

    def maxdd_np(path: np.ndarray) -> float:
        peak = np.maximum.accumulate(path)
        with np.errstate(divide="ignore", invalid="ignore"):
            dd = np.where(peak > 0, (peak - path) / peak, 0.0)
        return float(dd.max()) if len(dd) else 0.0

    START_EQ = 100000.0
    rng = np.random.default_rng(BOOT_SEED)
    picks = rng.integers(0, M, size=(BOOT_ITER, M))            # TEK çekiliş seti → TÜM koşumlara (eşlenik)

    kolar = ["t10", "y1", "y2", "c5"]
    st = {k: {"n": np.empty(BOOT_ITER), "pnl": np.empty(BOOT_ITER),
              "avg_r": np.full(BOOT_ITER, np.nan), "dd_kapali": np.empty(BOOT_ITER),
              "dd_m2m": np.full(BOOT_ITER, np.nan), "sharpe_g": np.full(BOOT_ITER, np.nan)}
          for k in kolar}
    for it in range(BOOT_ITER):
        pick = picks[it]
        for k in kolar:
            ia = IA[k]
            st[k]["n"][it] = ia["cnt"][pick].sum()
            st[k]["pnl"][it] = ia["pnl"][pick].sum()
            rs = [ia["r"][j] for j in pick if len(ia["r"][j])]
            if rs:
                rcat = np.concatenate(rs)
                st[k]["avg_r"][it] = rcat.mean()
            pn = [ia["pnl_sirali"][j] for j in pick if len(ia["pnl_sirali"][j])]
            if pn:
                path = START_EQ + np.cumsum(np.concatenate(pn))
                st[k]["dd_kapali"][it] = maxdd_np(np.concatenate([[START_EQ], path]))
            else:
                st[k]["dd_kapali"][it] = 0.0
            if k in GA:
                g = [GA[k][j] for j in pick if len(GA[k][j])]
                if g:
                    gcat = np.concatenate(g)
                    st[k]["dd_m2m"][it] = maxdd_np(np.cumprod(1.0 + gcat) * START_EQ)
                    sd = gcat.std(ddof=1) if len(gcat) > 2 else 0.0
                    if sd > 0:
                        st[k]["sharpe_g"][it] = gcat.mean() / sd * YILLIK_KOK

    def ci95(arr) -> dict | None:
        a = np.asarray(arr, dtype=float)
        a = a[~np.isnan(a)]
        if not len(a):
            return None                                        # ölçülemedi
        return {"lo": round(float(np.percentile(a, 2.5)), 4),
                "hi": round(float(np.percentile(a, 97.5)), 4),
                "orta": round(float(np.median(a)), 4),
                "n_iter_gecerli": int(len(a))}

    def fark_ci(a_kol: str, b_kol: str, metrik: str) -> dict | None:
        return ci95(st[a_kol][metrik] - st[b_kol][metrik])

    def oran_ci(a_kol: str, b_kol: str) -> dict | None:
        payda = st[b_kol]["n"]
        gecerli = payda > 0
        if not gecerli.any():
            return None
        return ci95(st[a_kol]["n"][gecerli] / payda[gecerli])

    def perf(kol) -> dict:
        s = (C5 if kol == "c5" else R[kol])["sonuc"]
        return s["performans"]

    def isl(kol) -> dict:
        s = (C5 if kol == "c5" else R[kol])["sonuc"]
        return s["islem"]

    def hucre_tablosu(a_kol: str, b_kol: str, m2m_var: bool) -> dict:
        pa, pb = perf(a_kol), perf(b_kol)
        ia_, ib_ = isl(a_kol), isl(b_kol)
        na, nb = int(ia_["n"]), int(ib_["n"])
        t = {
            "islem_n": {a_kol: na, b_kol: nb, "fark": na - nb,
                        "fark_pct": round(100.0 * (na - nb) / nb, 1) if nb else None},
            "islem_fark_ci95": fark_ci(a_kol, b_kol, "n"),
            "islem_oran_ci95": oran_ci(a_kol, b_kol),
            "net_pnl_equity": {a_kol: pa["net_pnl_equity"], b_kol: pb["net_pnl_equity"]},
            "net_pnl_trades": {a_kol: pa["net_pnl_trades"], b_kol: pb["net_pnl_trades"],
                               "fark": round(pa["net_pnl_trades"] - pb["net_pnl_trades"], 2)},
            "net_pnl_fark_ci95": fark_ci(a_kol, b_kol, "pnl"),
            "maxdd_kanonik": {a_kol: pa["maxdd_kanonik"], b_kol: pb["maxdd_kanonik"],
                              "fark": round(pa["maxdd_kanonik"] - pb["maxdd_kanonik"], 4)},
            "maxdd_m2m": {a_kol: pa["maxdd_m2m"], b_kol: pb["maxdd_m2m"]},
            "maxdd_kapali_fark_ci95": fark_ci(a_kol, b_kol, "dd_kapali"),
            "maxdd_m2m_fark_ci95": (fark_ci(a_kol, b_kol, "dd_m2m") if m2m_var else None),
            "sharpe_islem_bazli": {a_kol: pa["sharpe"], b_kol: pb["sharpe"],
                                   "not": "score_detail işlem-bazlı (motor-kanonik NOKTA)"},
            "sharpe_gunluk_fark_ci95": (fark_ci(a_kol, b_kol, "sharpe_g") if m2m_var else None),
            "avg_r": {a_kol: pa["avg_r"], b_kol: pb["avg_r"],
                      "fark": round(pa["avg_r"] - pb["avg_r"], 4)},
            "avg_r_fark_ci95": fark_ci(a_kol, b_kol, "avg_r"),
            "win_rate": {a_kol: pa["win_rate"], b_kol: pb["win_rate"]},
            "verdict_dagilim": {a_kol: ia_["verdict_dagilim"], b_kol: ib_["verdict_dagilim"]},
            "nogo_neden_dagilim": {a_kol: ia_["nogo_neden_dagilim"], b_kol: ib_["nogo_neden_dagilim"]},
            "silahlanan_plan": {a_kol: ia_["silahlanan_plan"], b_kol: ib_["silahlanan_plan"]},
            "toplam_plan": {a_kol: ia_["toplam_plan"], b_kol: ib_["toplam_plan"]},
        }
        if not m2m_var:
            t["maxdd_m2m_fark_ci95_neden"] = ("ölçülemedi: C@5 (EDG-026) M2M eğrisini saklamadı; "
                                              "yeniden koşum kart gereği YASAK — kapalı-işlem dd CI'ı "
                                              "ve kanonik NOKTA kıyas verildi (UYDURMA YASAĞI)")
            t["sharpe_gunluk_fark_ci95_neden"] = "aynı neden (M2M günlük getiri serisi C@5'te yok)"
        return t

    # ---- (A) ZARF ETKİSİ: T10 vs C@5 ---------------------------------------------------------
    zarf_tablosu = hucre_tablosu("t10", "c5", m2m_var=False)
    zarf_tablosu["doluluk"] = {"t10": R["t10"]["sonuc"]["doluluk"], "c5": C5["sonuc"]["doluluk"]}
    zarf_tablosu["tepe_isi"] = {"t10": R["t10"]["sonuc"]["tepe_isi"], "c5": C5["sonuc"]["tepe_isi"]}
    zarf_tablosu["heat_hard_nogo_n"] = {
        "t10": R["t10"]["sonuc"]["islem"]["nogo_neden_dagilim"].get("heat_hard", 0),
        "c5": C5["sonuc"]["islem"]["nogo_neden_dagilim"].get("heat_hard", 0)}

    # ---- (B)(C) MODÜLASYON: Y1/Y2 vs T10 + ÜÇLÜ-EŞİK İŞARETLERİ ------------------------------
    def esik_isaretleri(kol: str) -> dict:
        pa, pt = perf(kol), perf("t10")
        na, nt = int(isl(kol)["n"]), int(isl("t10")["n"])
        pnl_ci = fark_ci(kol, "t10", "pnl")
        i_gecti = bool(pa["maxdd_kanonik"] < pt["maxdd_kanonik"])
        ii_gecti = bool(pnl_ci is not None and pnl_ci["hi"] >= 0.0)
        iii_gecti = bool(na >= 0.6 * nt)
        return {
            "esik_kaynagi": "kart success_metric (DONUK, ölçümden önce) — İŞARET, HÜKÜM DEĞİL",
            "i_maxdd_dusuyor_nokta": {"gecti": i_gecti,
                                      "deger": {kol: pa["maxdd_kanonik"], "t10": pt["maxdd_kanonik"]}},
            "ii_pnl_ci_bozulmuyor": {"gecti": ii_gecti, "ci95": pnl_ci,
                                     "kural": "fark CI üst ucu >= 0 (0'ı içeriyor-ya-da-üstünde)"},
            "iii_islem_debisi_60pct": {"gecti": iii_gecti,
                                       "deger": {kol: na, "t10_x0.6": round(0.6 * nt, 1)}},
            "ucu_birden": bool(i_gecti and ii_gecti and iii_gecti),
        }

    y1_tablosu = hucre_tablosu("y1", "t10", m2m_var=True)
    y2_tablosu = hucre_tablosu("y2", "t10", m2m_var=True)
    isaretler = {"y1": esik_isaretleri("y1"), "y2": esik_isaretleri("y2")}

    # ---- kill bayrakları ---------------------------------------------------------------------
    n_t10 = int(isl("t10")["n"])
    n_y1, n_y2 = int(isl("y1")["n"]), int(isl("y2")["n"])
    kill_y2 = {
        "esik": "Y2 vol-serisi ileri-bakış sızıntısı (kart kill#2)",
        "kontrol": R["y2"]["sonuc"]["isi_modulasyonu"]["sizinti_kontrol"],
        "hedef_vol_yillik": R["y2"]["sonuc"]["isi_modulasyonu"]["hedef_vol_yillik"],
        "hedef_kaynagi_sha256": R["y2"]["sonuc"]["isi_modulasyonu"]["hedef_kaynagi_sha256"],
        "tetiklendi": bool(R["y2"]["sonuc"]["isi_modulasyonu"]["sizinti_kontrol"]["tetiklendi"]),
    }
    kill_debi = {
        "esik": "HER İKİ yöntemde de n < 0.6×n(T10) → otomatik-benimseme YAPILMAZ (kart kill#3)",
        "n": {"t10": n_t10, "y1": n_y1, "y2": n_y2, "esik_0.6xT10": round(0.6 * n_t10, 1)},
        "tetiklendi": bool(n_y1 < 0.6 * n_t10 and n_y2 < 0.6 * n_t10),
    }

    rejim_isi = {k: (C5 if k == "c5" else R[k])["sonuc"].get("rejim_kirilim")
                 for k in ("t10", "y1", "y2")}
    rejim_isi["c5_neden_yok"] = ("C@5 seans şemasında isi_tavani alanları yok (026 bu kırılımı "
                                 "üretmedi); gerçekleşen ΣsizeR serisi 026 tepe_isi bloğunda — ölçülemedi/None")
    nogo_heat_rejim = {k: R[k]["sonuc"]["islem"].get("nogo_heat_rejim_dagilim") for k in KOSUMLAR}

    out = {
        "kart": "EDG-2026-028",
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "kosumlar": {r: {"sonuc": R[r]["sonuc_dosya"], "sure_sn": R[r]["sonuc"]["sure_sn"],
                         "tavan_histogram": R[r]["sonuc"]["isi_modulasyonu"]["tavan_close_histogram"]}
                     for r in KOSUMLAR},
        "kiyas_taban_c5": {"kaynak": "EDG-026 C HAZIR çıktıları — yeniden koşulmadı (salt-oku)",
                           "dosyalar": {k: C5[f"{k}_dosya"] for k in ("sonuc", "seans", "islem")},
                           "sha256": {k: C5[f"{k}_sha256"] for k in ("sonuc", "seans", "islem")}},
        "sasi_kimligi": {"motor_sha_ayni": motor_ayni, "config_sha_ayni": config_ayni,
                         "motor_sha_simdiki": motor_simdiki,
                         "rampa_ayni_15_36": rampa_ayni, "takvim_ayni": takvim_ayni,
                         "serh": serh},
        "yontem": {
            "eslenik_bootstrap": (f"ay-kümeli EŞLENİK bootstrap: TEK çekiliş seti (iter={BOOT_ITER}, "
                                  f"seed={BOOT_SEED}, n_ay={M}) dört kola birden; fark = hücre − taban"),
            "islem_ay_anahtari": "ts_open[:7] (giriş ayı — şasi tanımı)",
            "dd_bootstrap": ("iterasyonda ay-BLOK birleştirme sırası (küme bootstrap standardı; "
                             "global kronolojik yeniden sıralama YOK); kapalı-dd = ay içi ts_close "
                             "sıralı pnl kümülatifi; M2M-dd = günlük getiri bloklarının çarpımsal yolu"),
            "sharpe_gunluk": "M2M günlük getiri mean/std(ddof=1)×√252 (bootstrap'ta iyi tanımlı)",
        },
        "zarf_enjeksiyon": R["t10"]["sonuc"]["zarf_enjeksiyon"],
        "butunluk": {**{r: R[r]["sonuc"]["butunluk"] for r in KOSUMLAR}, "c5": C5["sonuc"]["butunluk"]},
        "kill_c_onkosul": kill_c,
        "kill_y2_sizinti": kill_y2,
        "kill_debi_60pct": kill_debi,
        "zarf_etkisi_t10_vs_c5": zarf_tablosu,
        "modulasyon_y1_vs_t10": y1_tablosu,
        "modulasyon_y2_vs_t10": y2_tablosu,
        "otomatik_benimseme_esik_isaretleri": isaretler,
        "rejim_kirilimli_gerceklesen_isi": rejim_isi,
        "nogo_heat_rejim_dagilim": nogo_heat_rejim,
        "y2_parametreleri": R["y2"]["sonuc"]["isi_modulasyonu"],
        "not_hukum": ("BU DOSYA HÜKÜM İÇERMEZ: eşik işaretleri kartın DONUK ölçütlerinin kayıtlarıdır; "
                      "benimseme/uygulama Rol-1 + operatör penceresinin (zarf 5→10 kararı PENCEREDE — "
                      "risk-artıran sınıf, politika §2-10)"),
    }
    (SANDBOX / "sonuc.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))

    print("\n==================== EDG-028 KIYAS ÖZETİ ====================")
    print(f"şasi: motor={all(motor_ayni.values())} config={all(config_ayni.values())} "
          f"rampa={rampa_ayni} takvim={takvim_ayni} bütünlük={butunluk_hepsi}  şerh={serh}")
    zt = zarf_tablosu
    print(f"[ZARF T10 vs C@5] işlem {zt['islem_n']}  pnl_fark_ci={zt['net_pnl_fark_ci95']}  "
          f"maxdd {zt['maxdd_kanonik']}  heat_NO_GO {zt['heat_hard_nogo_n']}")
    for ad, tb in (("Y1", y1_tablosu), ("Y2", y2_tablosu)):
        print(f"[{ad} vs T10] işlem {tb['islem_n']}  pnl_fark_ci={tb['net_pnl_fark_ci95']}  "
              f"maxdd {tb['maxdd_kanonik']}  m2m_dd_ci={tb['maxdd_m2m_fark_ci95']}")
    print(f"eşik işaretleri: y1={isaretler['y1']['ucu_birden']} (i={isaretler['y1']['i_maxdd_dusuyor_nokta']['gecti']} "
          f"ii={isaretler['y1']['ii_pnl_ci_bozulmuyor']['gecti']} iii={isaretler['y1']['iii_islem_debisi_60pct']['gecti']})  "
          f"y2={isaretler['y2']['ucu_birden']} (i={isaretler['y2']['i_maxdd_dusuyor_nokta']['gecti']} "
          f"ii={isaretler['y2']['ii_pnl_ci_bozulmuyor']['gecti']} iii={isaretler['y2']['iii_islem_debisi_60pct']['gecti']})")
    print(f"kill: C-önkoşul={kill_c['tetiklendi']}  Y2-sızıntı={kill_y2['tetiklendi']}  "
          f"debi-60={kill_debi['tetiklendi']}")
    print(f"yazıldı: {SANDBOX/'sonuc.json'}")
    print("=============================================================\n")


if __name__ == "__main__":
    mod = sys.argv[1] if len(sys.argv) > 1 else ""
    smoke = "--smoke" in sys.argv
    if mod in KOSUMLAR:
        kosum(mod, smoke=smoke)
    elif mod == "kiyas":
        kiyas()
    else:
        sys.exit("kullanım: olcum.py {t10|y1|y2|kiyas} [--smoke]")

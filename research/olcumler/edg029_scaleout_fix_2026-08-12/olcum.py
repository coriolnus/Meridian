"""EDG-2026-029 — SCALE-OUT DÜZELTİLMİŞ (trail-düzeltme) · ölçüm aracı (2026-08-12)

Kart: research/cards/EDG-2026-029-scaleout-duzeltilmis.yaml (OKU-DOKUNMA; hüküm Rol-1'in).
Rol: ÖLÇÜM ajanı. Bu modül HÜKÜM VERMEZ, karta dokunmaz, git/canlı/broker/state'e YAZMAZ.
Şasi: EDG-027 FAZ-1 olcum.py (eşli-kıyas makinesi + scale-out enjeksiyonu + öz-sınamalar +
kancalar + seed 20260812) AYNEN devralındı; C-dünyası enjeksiyon parçaları (slot20 + 0.5R +
yayılım kanıtları) EDG-027 FAZ-2 olcum_c.py'den AYNEN devralındı. TEK EK: trail-düzeltme
monkeypatch'i (aşağıda BEYAN).

HÜCRELER (kart parameter_grid; K += 2):
  (F1x) B_scaleout_fix : B dünyası (rampa 15/36 mp + slot5 + 1R) + scale-out(0.5@1.5R) + DÜZELTME
                         → taban EDG-023 varyant HAZIR çıktıları
  (F2x) C_scaleout_fix : C dünyası (rampa 15/36 mp + slot20 + 0.5R) + scale-out(0.5@1.5R) + DÜZELTME
                         → taban EDG-026 c_slot20_r05 HAZIR çıktıları
AYRICA: F1x ↔ H1 (EDG-027 h1_scaleout, düzeltmesiz scale-out) eşli farkı — düzeltmenin KENDİ etkisi.
Tabanlar ve H1 YENİDEN KOŞULMAZ (hepsi hazır dosya, sha+çivi doğrulamalı salt-okuma).

TRAIL-DÜZELTME — BEYAN (kartın tezi; ROADMAP §2-13 tanımı; motor DOSYASI değişmez):
  KUSUR (EDG-027/H1 mekanik bulgusu): broker.scale_out (broker.py:529 bloğu) bankalama barında
  `pos.trail_stop = max(trail, entry)` kurar (broker.py:581). entry = fill = open×(1+slip) > open
  olduğundan, bankalama barı open'ı entry ALTINDA kalan her koşucu AYNI BARIN _touch_exit'inde
  `o <= eff_stop` dalıyla 'stop_gap' okunur (giriş-günü bankalamasında DAİMA; ~0.7R'ye budanır).
  DÜZELTME (ölçüm-içi monkeypatch): PaperBroker.scale_out SINIF-özniteliği bir sarmalayıcıyla
  değiştirilir — orijinal scale_out AYNEN çağrılır (muhafızlar + bankalama muhasebesi tek bayt
  değişmez), bankalama ATEŞLEDİYSE trail_stop bankalama-ÖNCESİ değerine GERİ yazılır: bankalama
  barında trail entry'ye ÇEKİLMEZ. Breakeven kilidi motorun KENDİ kapanış-fazı yolundan gelir:
  strategy.manage_position'ın exit.breakeven_r=1.0 kuralı (strategy.py:1088-1090) bankalama barının
  kapanışında trail'i entry'ye taşır (bankalama high'ı ≥ entry+1.5R ≥ entry+1.0R olduğundan DAİMA
  ateşler) — yani trail güncellemesi bir SONRAKİ barın dokunuş-çıkışlarından itibaren etkir.
  exit.breakeven_r=1.0 dosya değeri bu semantiğin ÇİVİSİDİR ve koşum öncesi assert edilir.
  KANIT (kart kill#3; kanıtlanamazsa KOŞULMAZ — asserts replay'den ÖNCE ölür):
    (i) yamasız motorla kusurun VARLIĞI: giriş-günü bankalama → aynı-bar stop_gap @ open, R≈0.73;
    (ii) yamayla bankalama barında trail DEĞİŞMİYOR + aynı-bar dokunuşu koşucuyu YAŞATIYOR;
    (iii) bankalama barının kapanışında GERÇEK manage_position trail'i breakeven'a taşıyor (=entry);
    (iv) sonraki bar NORMAL güncelleniyor: breakeven'lı trail ile gap-açılış → stop_gap, bar-içi
         dokunuş → stop; yamalı scale_out sonraki barlarda False + trail'e dokunmuyor (idempotent);
    (v) muhafızlar (hedef-önce, açılış-hedef, stop-önce, frac=0) yamadan AYNEN geçiyor;
    (vi) bankalama muhasebesi (qty/banked_pnl/realized/cash) yamasızla BİREBİR aynı.
  Kapsam: chandelier bu kartın kolu DEĞİL (sabit 0 assert'li); şasinin chandelier öz-sınaması
  manage_position kapanış-fazı makinesinin değişmediğinin kanıtı olarak AYNEN korunur.

TANIMLAR (ölçümden ÖNCE donduruldu; sonuç görüldükten sonra değişmez — EDG-027 ile AYNI):
  islem/islem R'si = kapanmış işlem satırı; r_multiple scale-out'ta BİRLEŞİK (banked+kalan) R.
  eşli anahtar     = (ts_open[:10], ticker); tekrar bulunursa bütünlük bozulur.
  eşli fark        = R_hücre − R_taban (pozitif = hücre lehine). F1x↔H1'de fark = R_F1x − R_H1
                     (pozitif = düzeltme lehine).
  eşli CI          = işlem-TARİH-kümeli eşlenik bootstrap (5000 iter, seed 20260812);
                     ay-kümeli CI yan-tablo (şeffaflık; ikinci eşik DEĞİL).
  kill#1 (kart)    = eşli-ortak < 60 → eşli-CI 'olculemedi'; tam-defter yine raporlanır.
  kill#2 (kart)    = şasi bütünlüğü: frame_miss=0, dup=0, scan==plan, yasaklı modül 0,
                     base_max_open beklenen (B:5 / C:20), takvim taban ile aynı; bozuksa geçersiz.
  kill#3 (kart)    = monkeypatch DAVRANIŞ kanıtı (yukarıdaki i-vi); assert düşerse koşum başlamaz.
  hedefe-ulaşma    = (target+target_gap)/n; scaled_out_n AYRI sayılır.
  max-dd / net P&L = motor-kanonik score_detail.max_drawdown; M2M equity − START_EQUITY.

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen = None + neden); YASA-4 (sessiz-yutma işaretli + gerekçe);
YASA-6 (okuyucu: sonuc_F*/islemler_F*/seanslar_F*.json'ları `birlestir` tüketir; sonuc.json'u
dönüş raporu + Rol-1 tüketir). SALT-OKUMA: config.STATE koşum-başına izole sandbox; barlar
sembolik bağla canlı önbellekten SALT-OKUNUR; canlı state'e ve motor dosyalarına yazılmaz.
meridian.loop / counterfactual / cf_backfill / hermes İTHAL EDİLMEZ — sys.modules ile KANITLANIR.

KULLANIM:
  olcum.py selftest         # yalnız sha + yama + kill#3 öz-sınamaları (replay YOK; doğum kapısı)
  olcum.py F1x [--smoke]    # B+scaleout+düzeltme → sonuc_F1x.json + seanslar_… + islemler_…
  olcum.py F2x [--smoke]    # C+scaleout+düzeltme → sonuc_F2x.json + …
  olcum.py birlestir        # F1x↔B, F2x↔C, F1x↔H1 → eşli CI + tam-defter + kill → sonuc.json
  (--smoke: 2022-01-01→2022-06-30, çıktılar smoke/ altına — şasi provası; smoke'ta birlestir YOK)
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
EDG026 = REPO / "research/olcumler/edg026_slot20_2026-08-12"        # C-taban çıktıları (HAZIR)
EDG027 = REPO / "research/olcumler/edg027_cikis_paketi_2026-08-12"  # H1 (düzeltmesiz) çıktıları (HAZIR)

# tek-iş parçacığı: determinizm + ölçüm gürültüsüzlüğü (şasi ile aynı)
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

REPLAY_START = "2022-01-01"
REPLAY_END = "2026-07-30"                      # 023/026/027 ile aynı pencere (eşli kıyasın şartı)
BOOT_SEED = 20260812
BOOT_ITER = 5000
ESLI_MIN = 60                                  # kill#1 eşiği (kart, DONUK)

# dünya sabitleri (023 varyantı = B; 026 c_slot20_r05 = C) — DONUK
RAMPA = {"tam_dd": 0.15, "sifir_dd": 0.36}     # her iki dünyada AYNEN (023/026 varyant deseni)
C_SLOT = 20
C_BOYUT_R = 0.5
B_SLOT = 5                                     # dosya değeri (assert edilir, enjekte edilmez)
B_BOYUT_R = 1.0                                # dosya değeri (assert edilir, enjekte edilmez)

# hücre kayıtları (kart parameter_grid: [B_scaleout_fix, C_scaleout_fix]; K çarpımında sayılıyor)
KOL = {"exit.scale_out_frac": 0.5, "exit.scale_out_r": 1.5}
# sabit_kanit: OAT saflığı (chandelier kapalı) + DÜZELTME SEMANTİĞİ ÇİVİLERİ (trail 2.5 / be_r 1.0:
# "sonraki bardan breakeven" motorun kendi kapanış-fazı be_r kuralına yaslanır — dosya değeri şart)
SABIT = {"exit.chandelier_lookback": 0.0, "exit.trail_atr_mult": 2.5, "exit.breakeven_r": 1.0}
HUCRELER = {
    "F1x": {"trial_id": "pending-029-B-fix", "dunya": "B", "kart_adi": "B_scaleout_fix"},
    "F2x": {"trial_id": "pending-029-C-fix", "dunya": "C", "kart_adi": "C_scaleout_fix"},
}

# strategy.yaml'ın enjeksiyon-ÖNCESİ değerleri (dosyadan beklenen; delta kanıtının yarısı)
DOSYA_DEGERLERI = {"exit.scale_out_frac": 0.0, "exit.scale_out_r": 2.0,
                   "exit.chandelier_lookback": 0, "exit.trail_atr_mult": 2.5,
                   "exit.breakeven_r": 1.0, "position_size_r": 1.0}

# MOTOR/CONFIG ÇİVİLERİ — EDG-023 ve EDG-026 kayıtları AYNI (2026-08-12 doğrulandı); tek küme yeter.
MOTOR_SHA = {"broker.py": "daa858a522d97c98", "backtest.py": "d345b6eed3d28be4",
             "strategy.py": "ac7c53a3d89b6203"}
CONFIG_SHA = {"goal.yaml": "099590dedee1ccf2", "strategy.yaml": "9f3e4732315abe52",
              "bounds.yaml": "3e810b547ca95f9a"}
EDG023_B_CIVI = {"n_islem": 410, "net_pnl_equity": 774.6, "maxdd_kanonik": 0.1775}
EDG026_C_CIVI = {"n_islem": 772, "net_pnl_equity": 9869.2, "maxdd_kanonik": 0.1235}
EDG027_H1_CIVI = {"n_islem": 392, "net_pnl_equity": -16683.95, "scaled_out_n": 73}

KART3 = ["tavan_sifir", "evren_bagladi", "derisk_bagladi"]   # seans sınıfları (şasi, DONUK)
YASAK = ("meridian.loop", "meridian.counterfactual", "meridian.cf_backfill", "meridian.hermes")


def _sha(p: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    except OSError:
        return None    # ölçülemedi (dosya yok/okunamadı) — None, uydurma özet değil


def _motor_sha_dogrula() -> dict:
    """Üç motor dosyasının GÜNCEL sha'sı 023/026 çivisine eşit mi? Değilse tabanlar
    karşılaştırılamaz — koşum başlamadan ölür (assert)."""
    guncel = {f: _sha(REPO / "meridian" / f) for f in MOTOR_SHA}
    for f, beklenen in MOTOR_SHA.items():
        assert guncel[f] == beklenen, (
            f"MOTOR SHA KAYMIŞ: {f} güncel={guncel[f]} != çivi={beklenen} — "
            "tabanlar karşılaştırılamaz, ölçüm geçersiz")
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
        assert _sha(dst) == CONFIG_SHA[f], (
            f"CONFIG SHA KAYMIŞ: {f} sandbox={_sha(dst)} != çivi={CONFIG_SHA[f]} — "
            "taban karşılaştırılamaz")
    return st


# ---------------------------------------------------------------------------------------------
# RAMPA — şasinin birebir parametrize kopyası (B ve C dünyalarının ortak bacağı; beyan başlıkta)
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
# ÖZ-SINAMALAR — koşum ÖNCESİ, GERÇEK motor fonksiyonlarıyla (sentetik girdi)
# ---------------------------------------------------------------------------------------------
def _poz(brkmod, target: float, trail: float = 95.0, scaled: bool = False):
    p = brkmod.Position(plan_id="SELFTEST", ticker="_ST", side="long", entry=100.0,
                        stop=95.0, trail_stop=trail, target=target, qty=100,
                        r_per_share=5.0, risk_dollars=500.0, size_r=1.0,
                        ts_open="2020-01-01")
    p.scaled_out = scaled
    return p


# giriş-günü bankalama barı: open < entry (entry = open×(1+slip) sözleşmesinin sentetik aynası)
BAR_GIRIS = {"open": 99.95, "high": 108.0, "low": 99.9}
# şasinin bankalama barı: open > entry (kusur bu şekilde GÖRÜNMEZ; trail-çekme yine olur)
BAR_SASI = {"open": 101.0, "high": 108.0, "low": 100.5}
BANKED_BEKLENEN = round(50 * (107.5 * (1 - 0.0005) - 100.0), 2)     # 372.31 (slip fiyatın içinde)


def _oz_sinama_scaleout_orijinal(brkmod) -> dict:
    """YAMASIZ motor: şasi öz-sınaması AYNEN + KUSURUN VARLIK KANITI (kill#3 ön-yarısı).
    Atılabilir PaperBroker + sentetik Position (replay broker'ına dokunulmaz)."""
    b = brkmod.PaperBroker(100_000.0, 5.0, 0.0)          # goal ile aynı: 5 bps, komisyon 0
    prm = dict(KOL)
    # --- şasi AYNEN: 1.5R'de ½ bankalama + trail-çekme (orijinal davranış) ---
    p = _poz(brkmod, target=112.5)
    assert b.scale_out(p, BAR_SASI, prm) is True, "scale_out enjeksiyonla ateşlemedi"
    assert p.scaled_out and p.qty == 50, "½ bankalama yanlış (qty)"
    assert p.trail_stop == 100.0, "orijinal davranış kayboldu: trail entry'ye çekilmedi"
    assert abs(p.banked_pnl - BANKED_BEKLENEN) < 1e-9, f"banked_pnl {p.banked_pnl} != {BANKED_BEKLENEN}"
    # muhafızlar: hedef-önce / açılış-hedef / stop-önce / frac=0 (şasi AYNEN)
    assert b.scale_out(_poz(brkmod, 107.0), BAR_SASI, prm) is False, "hedef-önce muhafızı delindi"
    assert b.scale_out(_poz(brkmod, 112.5), {"open": 101.0, "high": 108.0, "low": 94.0},
                       prm) is False, "stop-önce muhafızı delindi"
    assert b.scale_out(_poz(brkmod, 112.5), BAR_SASI,
                       {"exit.scale_out_frac": 0.0, "exit.scale_out_r": 2.0}) is False, \
        "frac=0 ile scale_out ateşledi — taban davranışı bozuk"
    # --- KUSUR KANITI: giriş-günü bankalama → AYNI BAR stop_gap @ open, R ≈ 0.73 ---
    b2 = brkmod.PaperBroker(100_000.0, 5.0, 0.0)
    pk = _poz(brkmod, target=112.5)
    assert b2.scale_out(pk, BAR_GIRIS, prm) is True, "kusur senaryosunda bankalama ateşlemedi"
    assert pk.trail_stop == 100.0, "kusur senaryosunda trail çekilmedi"
    ex = b2._touch_exit(pk, BAR_GIRIS)
    assert ex is not None and ex[1] == "stop_gap" and ex[0] == BAR_GIRIS["open"], (
        f"kusur kanıtı düştü: aynı-bar stop_gap bekleniyordu, geldi={ex}")
    exit_fill = BAR_GIRIS["open"] * (1 - 0.0005)
    r_toplam = (pk.banked_pnl + pk.qty * (exit_fill - pk.entry)) / pk.risk_dollars
    assert abs(r_toplam - 0.7346) < 0.01, f"kusur R imzası ~0.73 değil: {r_toplam}"
    return {"sasi_bankalama_gecti": True, "kusur_ayni_bar_stop_gap": True,
            "kusur_r_imzasi": round(r_toplam, 4)}


def _yama_uygula(brkmod):
    """TRAIL-DÜZELTME monkeypatch'i (beyan modül başlığında). Motor DOSYASI değişmez;
    PaperBroker.scale_out SINIF-özniteliği sarmalayıcıyla değiştirilir."""
    orij = brkmod.PaperBroker.scale_out
    assert getattr(orij, "_edg029_yama", False) is False, "yama iki kez uygulanamaz"

    def scale_out_duzeltilmis(self, pos, bar, params):
        trail_once = pos.trail_stop
        ates = orij(self, pos, bar, params)
        if ates:
            pos.trail_stop = trail_once      # bankalama barında trail ÇEKİLMEZ (EDG-029 düzeltmesi)
        return ates

    scale_out_duzeltilmis._edg029_yama = True
    scale_out_duzeltilmis._edg029_orij = orij
    brkmod.PaperBroker.scale_out = scale_out_duzeltilmis
    assert brkmod.PaperBroker.scale_out is scale_out_duzeltilmis
    return scale_out_duzeltilmis


def _oz_sinama_trail_duzeltme(brkmod, strat, ind) -> dict:
    """kill#3 KANITI (yamalı motor): bankalama barında trail değişmiyor + koşucu yaşıyor +
    kapanış-fazı breakeven'ı GERÇEK manage_position'dan geliyor + sonraki bar normal güncelleniyor.
    Kanıtlanamazsa assert düşer → koşum başlamaz (kart: 'koşulmaz, araç turu')."""
    import numpy as np
    import pandas as pd
    prm = dict(KOL)
    assert getattr(brkmod.PaperBroker.scale_out, "_edg029_yama", False), "yama uygulanmamış"

    # (ii) bankalama barında trail DEĞİŞMİYOR + aynı-bar dokunuşu koşucuyu YAŞATIYOR
    b = brkmod.PaperBroker(100_000.0, 5.0, 0.0)
    p = _poz(brkmod, target=112.5)
    assert b.scale_out(p, BAR_GIRIS, prm) is True, "yamalı scale_out ateşlemedi"
    assert p.scaled_out and p.qty == 50, "yama bankalama muhasebesini bozdu (qty)"
    assert p.trail_stop == 95.0, f"DÜZELTME KANITI DÜŞTÜ: bankalama barında trail değişti ({p.trail_stop})"
    # (vi) muhasebe yamasızla BİREBİR: banked/realized/cash
    assert abs(p.banked_pnl - BANKED_BEKLENEN) < 1e-9, "yama banked_pnl'i değiştirdi"
    assert abs(b.realized_pnl - BANKED_BEKLENEN) < 1e-9, "yama realized_pnl'i değiştirdi"
    assert abs(b.cash - (100_000.0 + BANKED_BEKLENEN)) < 1e-9, "yama cash'i değiştirdi"
    assert b._touch_exit(p, BAR_GIRIS) is None, "koşucu bankalama barında yine kesildi — düzeltme etkisiz"
    # şasi-şekilli bar (open>entry) de aynı: bankala + trail sabit + koşucu yaşar
    b3 = brkmod.PaperBroker(100_000.0, 5.0, 0.0)
    p3 = _poz(brkmod, target=112.5)
    assert b3.scale_out(p3, BAR_SASI, prm) is True and p3.trail_stop == 95.0
    assert b3._touch_exit(p3, BAR_SASI) is None

    # (iii) bankalama barının KAPANIŞI: GERÇEK manage_position breakeven'ı kurar (=entry, TAM)
    n = 25
    close = np.append(np.linspace(98.0, 100.0, n - 1), 101.0)
    high = close + 0.6
    low = close - 0.6
    high[-1], low[-1] = BAR_GIRIS["high"], BAR_GIRIS["low"]      # son bar = bankalama barı
    df = pd.DataFrame({"open": close, "high": high, "low": low, "close": close,
                       "volume": np.full(n, 1e6)})
    a = float(ind.atr(df, strat.ATR_PERIOD).iloc[-1])
    assert a > 0, f"sentetik ATR beklenmedik: {a}"
    p_eff = {**{k: float(v) for k, v in DOSYA_DEGERLERI.items() if k.startswith("exit.")},
             **{"exit.time_stop_days": 15, "exit.giveback_pct": 0.0,
                "exit.profit_target_r": 2.5}, **KOL}
    dec = strat.manage_position(df, {"entry": 100.0, "stop": 95.0, "trail_stop": 95.0,
                                     "r_per_share": 5.0, "pivot": 0.0},
                                p_eff, bars_held=1, regime_ok=True)
    assert not dec.exit_now, f"kapanış-fazı beklenmedik çıkış: {dec.exit_reason}"
    assert abs(dec.trail_stop - 100.0) < 1e-9, (
        f"kapanış-fazı breakeven kanıtı düştü: trail {dec.trail_stop} != 100.0 "
        "(be_r=1.0 kuralı bankalama barında ateşlemedi)")

    # (iv) SONRAKİ BAR NORMAL: breakeven'lı trail ile normal dokunuş semantiği + yama idempotent
    p.trail_stop = dec.trail_stop                                 # motorun kapanış-fazı yazımı (backtest.py:290)
    bar2 = {"open": 101.0, "high": 103.0, "low": 100.8}
    assert b.scale_out(p, bar2, prm) is False, "scaled_out pozisyonda ikinci bankalama"
    assert p.trail_stop == 100.0, "yamalı scale_out sonraki barda trail'e dokundu (idempotens bozuk)"
    assert b._touch_exit(p, bar2) is None, "sonraki bar sağ-kalım senaryosu düştü"
    ex_gap = b._touch_exit(p, {"open": 99.5, "high": 101.0, "low": 99.0})
    assert ex_gap == (99.5, "stop_gap"), f"sonraki-bar gap-açılış semantiği bozuk: {ex_gap}"
    p4 = _poz(brkmod, target=112.5, trail=100.0, scaled=True)
    ex_bar = b._touch_exit(p4, {"open": 100.6, "high": 101.4, "low": 99.8})
    assert ex_bar == (100.0, "stop"), f"sonraki-bar bar-içi dokunuş semantiği bozuk: {ex_bar}"

    # (v) muhafızlar yamadan AYNEN geçiyor (False yollarında trail'e dokunulmaz)
    for poz_t, bar_t, prm_t in ((107.0, BAR_SASI, prm),
                                (112.5, {"open": 101.0, "high": 108.0, "low": 94.0}, prm),
                                (112.5, {"open": 94.5, "high": 108.0, "low": 94.0}, prm),
                                (112.5, BAR_SASI, {"exit.scale_out_frac": 0.0,
                                                   "exit.scale_out_r": 2.0})):
        pg = _poz(brkmod, target=poz_t)
        assert b.scale_out(pg, bar_t, prm_t) is False, f"muhafız delindi: {bar_t} {prm_t}"
        assert pg.trail_stop == 95.0 and not pg.scaled_out, "False yolunda durum değişti"

    return {"bankalama_barinda_trail_sabit": True, "ayni_bar_kosucu_yasiyor": True,
            "kapanis_fazi_breakeven_entry": True, "sonraki_bar_normal": True,
            "muhafizlar_korundu": True, "muhasebe_birebir": True}


def _oz_sinama_chandelier(strat, ind) -> None:
    """Şasi AYNEN (EDG-027): manage_position kapanış-fazı makinesinin değişmediğinin kanıtı.
    (chandelier bu kartın kolu DEĞİL; lookback=0 sabit_kanit ile kapalı tutulur.)"""
    import numpy as np
    import pandas as pd
    n = 30
    close = np.linspace(100.0, 130.0, n)
    high = close + 1.0
    high[-5] = 150.0
    low = close - 1.0
    df = pd.DataFrame({"open": close, "high": high, "low": low, "close": close,
                       "volume": np.full(n, 1e6)})
    pos = {"entry": 100.0, "stop": 95.0, "trail_stop": 95.0, "r_per_share": 5.0, "pivot": 0.0}
    taban_p = {"exit.scale_out_frac": 0.0, "exit.scale_out_r": 2.0, "exit.chandelier_lookback": 0,
               "exit.trail_atr_mult": 2.5, "exit.breakeven_r": 1.0, "exit.time_stop_days": 15,
               "exit.giveback_pct": 0.0}
    a = float(ind.atr(df, strat.ATR_PERIOD).iloc[-1])
    assert a > 0 and a < 12, f"sentetik ATR beklenmedik: {a}"
    d0 = strat.manage_position(df, dict(pos), taban_p, bars_held=10, regime_ok=True)
    d20 = strat.manage_position(df, dict(pos), dict(taban_p, **{"exit.chandelier_lookback": 20}),
                                bars_held=10, regime_ok=True)
    assert not d0.exit_now and not d20.exit_now
    assert abs(d0.trail_stop - max(100.0, 130.0 - 2.5 * a)) < 1e-9, \
        "lookback=0 trail'i beklenen kapalı-alet değerinde değil"
    assert d20.trail_stop > d0.trail_stop, "chandelier trail'i yükseltmedi"
    assert abs(d20.trail_stop - (150.0 - 2.5 * a)) < 1e-9, \
        f"chandelier çapası yanlış: {d20.trail_stop} != {150.0 - 2.5 * a}"


def _sinamalari_kos(st_dir: pathlib.Path | None = None):
    """selftest modu + kosum ortak gövdesi: sha → config-yönlendirme → ithal → rampa →
    yamasız kanıt → yama → kill#3. Döner: (config, brkmod, backtest, ind, motor_sha, özet)."""
    motor_sha = _motor_sha_dogrula()
    sys.path.insert(0, str(REPO))
    from meridian import config
    if st_dir is None:                         # selftest modu: yazımlar yine sandbox'a düşsün
        st_dir = SANDBOX / "state_selftest"
        st_dir.mkdir(exist_ok=True)
        (st_dir / "history").mkdir(exist_ok=True)
    # SALT-OKUMA İZOLASYONU: her yazım (obs.events, history) sandbox'a düşer, canlı state'e DEĞİL
    config.STATE = st_dir
    config.BARS = st_dir / "bars"
    config.HISTORY = st_dir / "history"
    from meridian import backtest, broker as brkmod, indicators as ind
    assert not hasattr(backtest, "wpg_overlay_day"), "motor YAMALI görünüyor — ölçüm geçersiz"
    assert not [m for m in sys.modules if m in YASAK], "yasaklı modül ithal edilmiş"
    assert backtest.brk is brkmod
    # rampa (B ve C dünyalarının ortak bacağı) + şasi asserts + yayılım (5 VE 20 tabanla)
    brkmod.derisk_mult = _rampa_fn(RAMPA["tam_dd"], RAMPA["sifir_dd"])
    assert brkmod.derisk_mult(90.0, 100.0) == 1.0
    assert abs(brkmod.derisk_mult(80.0, 100.0) - 0.7619) < 1e-9
    assert brkmod.derisk_mult(64.0, 100.0) == 0.0
    assert brkmod.max_positions_at(80.0, 100.0, 5) == 4       # round(5×0.7619)=4 (023 çivisi)
    assert brkmod.max_positions_at(80.0, 100.0, 20) == 15     # round(20×0.7619)=15 (026 çivisi)
    # öz-sınama zinciri: yamasız kanıt → yama → kill#3 kanıtı → şasi chandelier
    oz1 = _oz_sinama_scaleout_orijinal(brkmod)
    _yama_uygula(brkmod)
    oz2 = _oz_sinama_trail_duzeltme(brkmod, backtest.strat, ind)
    _oz_sinama_chandelier(backtest.strat, ind)
    return config, brkmod, backtest, ind, motor_sha, {"yamasiz": oz1, "kill3_duzeltme": oz2,
                                                      "chandelier_sasi": True}


# ---------------------------------------------------------------------------------------------
# TEK KOŞUM (F1x | F2x)
# ---------------------------------------------------------------------------------------------
def kosum(run: str, smoke: bool = False):
    assert run in HUCRELER, f"bilinmeyen hücre: {run}"
    hucre = HUCRELER[run]
    dunya = hucre["dunya"]
    outdir = (SANDBOX / "smoke") if smoke else SANDBOX
    outdir.mkdir(exist_ok=True)
    r_start, r_end = (REPLAY_START, "2022-06-30") if smoke else (REPLAY_START, REPLAY_END)

    st_dir = hazirla(run + ("_smoke" if smoke else ""))
    config, brkmod, backtest, ind, motor_sha, oz_ozet = _sinamalari_kos(st_dir)
    import yaml
    from meridian import dataset, score as score_mod
    brk = backtest.brk

    # ---- girdiler + ENJEKSİYONLAR (dosya DEĞİŞMEZ; sözlükler değişir; beyan başlıkta) ----------
    stg = yaml.safe_load((st_dir / "strategy.yaml").read_text())
    params = dict(stg["params"])
    by_regime = stg.get("params_by_regime") or None
    sv = int(stg.get("version"))
    goal = config.goal()                                   # derin kopya — dosyaya/önbelleğe sızmaz

    # dosya değerleri beklenen mi? (delta kanıtının 'önce' yarısı; be_r=1.0 düzeltme çivisi DAHİL)
    for k, v in DOSYA_DEGERLERI.items():
        assert float(params[k]) == float(v), f"strategy.yaml {k}={params[k]} beklenen {v} değil"
    assert int(goal["limits"]["max_open_positions"]) == B_SLOT, "goal max_open dosya değeri 5 değil"

    dunya_enj: dict = {"dunya": dunya}
    if dunya == "C":
        goal["limits"]["max_open_positions"] = C_SLOT      # ENJEKSİYON 1 (goal/limits; 026 AYNEN)
        params["position_size_r"] = C_BOYUT_R              # ENJEKSİYON 2 (strateji params; 026 AYNEN)
        assert float(goal["limits"]["max_position_r"]) >= C_BOYUT_R
        dunya_enj.update({"max_open_positions": {"once": B_SLOT, "sonra": C_SLOT},
                          "position_size_r": {"once": B_BOYUT_R, "sonra": C_BOYUT_R},
                          "zarf_sabit": ("heat_hard_r=5.0R, heat_review_r=3.5R, max_position_r=1.0, "
                                         "max_sector_exposure_pct=40 DEĞİŞMEDİ (EDG-026 beyanı AYNEN; "
                                         "sektör-başına fiili tavan 2→8 motor-içi doğal sonuç)")})
    else:
        dunya_enj.update({"max_open_positions": {"dosya": B_SLOT, "enjeksiyon": None},
                          "position_size_r": {"dosya": B_BOYUT_R, "enjeksiyon": None}})

    # KOL enjeksiyonu (şasi AYNEN) + sabit kanıtlar (OAT + düzeltme-semantiği çivileri)
    for k, v in KOL.items():
        params[k] = v
    for k, v in SABIT.items():
        assert float(params[k]) == float(v), f"sabit_kanit bozuk: {k}={params[k]} != {v}"
    # yayılım kanıtı: rejim çözünürlüğü TÜM enjeksiyonları dört rejimde de taşıyor
    for rg in ("trend_up", "trend_down", "chop", "high_vol"):
        eff_test = config.resolve_params(params, by_regime, rg)
        for k, v in KOL.items():
            assert eff_test[k] == v, f"resolve_params {rg} kol enjeksiyonunu düşürdü: {k}"
        if dunya == "C":
            assert float(eff_test["position_size_r"]) == C_BOYUT_R, f"rejim override sızıntısı: {rg}"
            assert ("position_size_r" not in ((by_regime or {}).get(rg) or {})), \
                f"params_by_regime[{rg}] position_size_r içeriyor — tek-nokta enjeksiyonu yetersiz"

    limits = goal["limits"]
    max_open = int(limits["max_open_positions"])
    beklenen_base = C_SLOT if dunya == "C" else B_SLOT
    assert max_open == beklenen_base
    no_trade_before = int(limits.get("no_trade_before_bars", 0))

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

    # koşum sonrası kanıt: yasaklı modüller replay SIRASINDA da yüklenmedi + yama YERİNDE kaldı
    yasak_yuklu = [m for m in sys.modules if m in YASAK]
    yama_yerinde = getattr(brkmod.PaperBroker.scale_out, "_edg029_yama", False)
    assert yama_yerinde, "yama replay sırasında düşmüş — ölçüm geçersiz"

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
    base_max_bozuk = [r["date"] for r in sess if r["base_max_open"] != beklenen_base]
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

    # ---- işlem/doluluk/performans metrikleri (şasi AYNEN + scaled eklentileri) ----------------
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
    scaled_bh0 = sum(1 for t in trades if t.get("scaled_out") and int(t.get("bars_held") or 0) == 0)

    eff_eq0 = sum(1 for r in sess if r["eff_max_open"] == 0)
    eff_eq1 = sum(1 for r in sess if r["eff_max_open"] == 1)
    eff_lt = sum(1 for r in sess if r["eff_max_open"] < max_open)
    slot_le0 = sum(1 for r in sess if r["acik_slot"] <= 0)
    dd_gt_tam = sum(1 for r in sess if r["dd"] > RAMPA["tam_dd"])
    size0 = sum(1 for r in sess if r["size_mult"] <= 0.0)

    tavan_pct_bir = round(100.0 * sum(1 for r in birincil if r["sinif"] == "tavan_sifir")
                          / n_bir, 2) if n_bir else None

    butunluk_gecerli = (_frame_miss[0] == 0 and not _dup and not scan_vs_plan
                        and not yasak_yuklu and not base_max_bozuk and yama_yerinde)

    out = {
        "kart": "EDG-2026-029", "hucre": run, "kart_adi": hucre["kart_adi"],
        "trial_id": hucre["trial_id"], "dunya": dunya, "smoke": smoke,
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sure_sn": sure,
        "rampa": {**RAMPA, "enjeksiyon": "MONKEYPATCH — 023/026 varyant beyanı AYNEN (dünyaların ortak bacağı)"},
        "dunya_enjeksiyonu": dunya_enj,
        "enjeksiyon_kol": {
            "degerler": KOL,
            "dosya_once": {k: DOSYA_DEGERLERI[k] for k in KOL},
            "sabit_kanit": SABIT,
            "beyan": ("PARAMS-SÖZLÜĞÜ ENJEKSİYONU — strategy.yaml DOSYASI ve motor DOSYALARI "
                      "değişmedi; mekanizma motorda mevcut ve paramla kapalıydı (broker.py:529 "
                      "scale_out). Yayılım motorun kendi param yolu (prev_eff/resolve_params); "
                      "dört rejim kanıtı + gerçek motor fonksiyonlarıyla öz-sınama koşum öncesi geçti."),
        },
        "duzeltme": {
            "mekanizma": ("PaperBroker.scale_out SINIF-monkeypatch'i (bu modülde sarmalayıcı): "
                          "orijinal scale_out AYNEN çağrılır (muhafızlar + bankalama muhasebesi "
                          "değişmez); bankalama ateşlediyse trail_stop bankalama-ÖNCESİ değerine "
                          "GERİ yazılır — bankalama barında trail entry'ye ÇEKİLMEZ. Breakeven "
                          "kilidi motorun KENDİ kapanış-fazı yolundan (strategy.manage_position "
                          "exit.breakeven_r=1.0, bankalama barının kapanışında trail≥entry) — "
                          "trail güncellemesi bir SONRAKİ barın dokunuşlarından itibaren etkir "
                          "(ROADMAP §2-13 tanımı; kart tezi)."),
            "motor_dosyasi_degisti": False,
            "be_r_civisi": 1.0,
            "oz_sinama_kill3": oz_ozet,
            "yama_replay_sonrasi_yerinde": yama_yerinde,
        },
        "motor_sha256_16": motor_sha,
        "config_sha256_16": {f: {"sandbox": _sha(st_dir / f),
                                 "edg022": _sha(EDG022 / "state" / f),
                                 "civi": CONFIG_SHA[f],
                                 "repo_state": _sha(REPO / "state" / f)}
                             for f in ("goal.yaml", "strategy.yaml", "bounds.yaml")},
        "replay": {"start": r_start, "end": r_end, "strategy_version": sv,
                   "params_by_regime": bool(by_regime), "n_sembol": len(bars),
                   "n_endeks_satir": int(len(index)), "max_open": max_open,
                   "no_trade_before": no_trade_before,
                   "cost_model": {"slippage_bps": float(goal.get("slippage_bps", 5)),
                                  "commission_per_share": float(goal.get("commission_per_share", 0.0)),
                                  "not": "motorun kendi maliyet modeli — dokunulmadı (kart: pessimistic_band_v2)"}},
        "butunluk": {
            "frame_okunamadi": _frame_miss[0], "tekrar_tarih": _dup,
            "scan_vs_plan_uyusmazlik_n": len(scan_vs_plan),
            "scan_vs_plan_ornek": scan_vs_plan[:10],
            "yasakli_modul_yuklendi": yasak_yuklu,
            "base_max_open_bozuk": base_max_bozuk[:10],
            "yama_yerinde": yama_yerinde,
            "gecerli": butunluk_gecerli,
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
            "scaled_bars_held_0_n": scaled_bh0,
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
                    "doluluk_orani_slot": round(doluluk_pozgun / n_all / max_open, 4) if n_all else None,
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
    # slim satırlar: FAZ-2 alan kümesi (üst-küme; eşli makinenin okuyucuları + Rol-1 kazı payı)
    slim = [{k: t.get(k) for k in ("ts_open", "ts_close", "ticker", "r_multiple",
                                   "pnl_dollars", "exit_reason", "bars_held", "regime",
                                   "setup", "qty", "risk_dollars", "size_r", "scaled_out")}
            for t in trades]
    (outdir / f"islemler_{run}{ek}.json").write_text(
        json.dumps(slim, ensure_ascii=False, default=str))

    print(f"\n=========== EDG-029 KOŞUM [{run}{ek}] ({hucre['kart_adi']}) ===========")
    print(f"replay {r_start}→{r_end}  sv={sv}  sembol={len(bars)}  süre={sure}s  dünya={dunya}")
    print(f"kol: {KOL}  düzeltme: bankalama-barı trail-çekme YOK (kill#3 kanıtlı)")
    print(f"bütünlük geçerli={out['butunluk']['gecerli']}  frame_miss={_frame_miss[0]} "
          f"dup={len(_dup)} scan!=plan={len(scan_vs_plan)} yasak={yasak_yuklu} "
          f"base_max_bozuk={len(base_max_bozuk)} yama_yerinde={yama_yerinde}")
    print(f"işlem n={n_islem} ({out['islem']['islem_yil']}/yıl)  net_pnl={net_pnl_equity}  "
          f"maxdd_kanonik={detail.get('max_drawdown')}  avg_r={detail.get('avg_r')}")
    print(f"çıkışlar: {out['islem']['exit_reason_dagilim']}")
    print(f"hedef %{out['islem']['hedef_orani_pct']}  scaled_out n={scaled_n} "
          f"(bars_held=0: {scaled_bh0})")
    print(f"yazıldı: {outdir}/sonuc_{run}{ek}.json")


# ---------------------------------------------------------------------------------------------
# EŞLİ KIYAS MAKİNESİ — şasi AYNEN ((ts_open[:10],ticker) anahtar; tarih-kümeli eşlenik bootstrap)
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
    """islem_T = taban (B / C / H1), islem_H = hücre. Şasi gövdesi AYNEN (taban/hücre adlandırma).
    fark = R_hücre − R_taban (pozitif = hücre lehine)."""
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

    # scaled alt-küme betimi (BETİM — eşik değil; şasi gerekçesi AYNEN: kusur izi bars_held==0 +
    # stop_gap kümeleri; düzeltmede bu izlerin sönmesi beklenir — beklenti≠hüküm, yorum Rol-1'in)
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
        "anahtar_tekrar": {"taban": dupT, "hucre": dupH},   # 0 olmalı (bütünlük)
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
        "yalniz_taban": _tek_yon(sorted(set(mT) - set(mH)), mT),
        "yalniz_hucre": _tek_yon(sorted(set(mH) - set(mT)), mH),
    }


# ---------------------------------------------------------------------------------------------
# BİRLEŞTİR — F1x↔B, F2x↔C, F1x↔H1 → eşli CI + tam-defter + kill bayrakları → sonuc.json
# ---------------------------------------------------------------------------------------------
def _tam_defter(T_sonuc: dict, H_sonuc: dict, taban_ad: str) -> dict:
    pT, pH = T_sonuc["performans"], H_sonuc["performans"]
    iT, iH = T_sonuc["islem"], H_sonuc["islem"]
    nT, nH = int(iT["n"]), int(iH["n"])
    hedef_T = (iT["exit_reason_dagilim"].get("target", 0)
               + iT["exit_reason_dagilim"].get("target_gap", 0))
    d = {
        "islem_n": {taban_ad: nT, "hucre": nH, "fark": nH - nT,
                    "fark_pct": round(100.0 * (nH - nT) / nT, 1) if nT else None},
        "islem_yil": {taban_ad: iT["islem_yil"], "hucre": iH["islem_yil"]},
        "net_pnl_equity": {taban_ad: pT["net_pnl_equity"], "hucre": pH["net_pnl_equity"],
                           "fark": round(pH["net_pnl_equity"] - pT["net_pnl_equity"], 2)},
        "net_pnl_trades": {taban_ad: pT["net_pnl_trades"], "hucre": pH["net_pnl_trades"]},
        "maxdd_kanonik": {taban_ad: pT["maxdd_kanonik"], "hucre": pH["maxdd_kanonik"]},
        "maxdd_m2m": {taban_ad: pT["maxdd_m2m"], "hucre": pH["maxdd_m2m"]},
        "avg_r": {taban_ad: pT["avg_r"], "hucre": pH["avg_r"]},
        "win_rate": {taban_ad: pT["win_rate"], "hucre": pH["win_rate"]},
        "sharpe": {taban_ad: pT["sharpe"], "hucre": pH["sharpe"]},
        "score": {taban_ad: pT["score"], "hucre": pH["score"]},
        "exit_reason_dagilim": {taban_ad: iT["exit_reason_dagilim"],
                                "hucre": iH["exit_reason_dagilim"]},
        "hedef_orani_pct": {taban_ad: round(100.0 * hedef_T / nT, 2) if nT else None,
                            "hucre": iH["hedef_orani_pct"]},
        "scaled_out": {taban_ad: {"n": iT.get("scaled_out_n", 0)},
                       "hucre": {"n": iH["scaled_out_n"], "pct": iH["scaled_out_pct"],
                                 "bars_held_0_n": iH.get("scaled_bars_held_0_n")}},
        "doluluk_pozisyon_gun": {taban_ad: T_sonuc["doluluk"]["pozisyon_gun_open_fazi"],
                                 "hucre": H_sonuc["doluluk"]["pozisyon_gun_open_fazi"]},
        "ort_acik_pozisyon": {taban_ad: T_sonuc["doluluk"]["ort_acik_pozisyon"],
                              "hucre": H_sonuc["doluluk"]["ort_acik_pozisyon"]},
        "toplam_bars_held": {taban_ad: T_sonuc["doluluk"]["toplam_bars_held"],
                             "hucre": H_sonuc["doluluk"]["toplam_bars_held"]},
        "silahlanan_plan": {taban_ad: iT["silahlanan_plan"], "hucre": iH["silahlanan_plan"]},
        "toplam_plan": {taban_ad: iT["toplam_plan"], "hucre": iH["toplam_plan"]},
        "entry_rejects": {taban_ad: iT["entry_rejects"], "hucre": iH["entry_rejects"]},
    }
    if "doluluk_orani_slot" in (T_sonuc["doluluk"] or {}) and \
            H_sonuc["doluluk"].get("doluluk_orani_slot") is not None:
        d["doluluk_orani_slot"] = {taban_ad: T_sonuc["doluluk"]["doluluk_orani_slot"],
                                   "hucre": H_sonuc["doluluk"]["doluluk_orani_slot"]}
    return d


def birlestir():
    # ---- tabanlar + H1: HAZIR dosyalar (yeniden koşum YOK; salt-okuma + çivi doğrulama) -------
    B_sonuc = json.loads((EDG023 / "sonuc_varyant.json").read_text())
    B_islem = json.loads((EDG023 / "islemler_varyant.json").read_text())
    B_seans = json.loads((EDG023 / "seanslar_varyant.json").read_text())
    assert B_sonuc["kosum"] == "varyant" and not B_sonuc["smoke"]
    assert len(B_islem) == EDG023_B_CIVI["n_islem"], "B islemler dosyası çiviyle uyuşmuyor"
    assert B_sonuc["performans"]["net_pnl_equity"] == EDG023_B_CIVI["net_pnl_equity"]
    assert B_sonuc["performans"]["maxdd_kanonik"] == EDG023_B_CIVI["maxdd_kanonik"]
    assert B_sonuc["motor_sha256_16"] == MOTOR_SHA, "B kayıtlı motor sha çiviyle uyuşmuyor"
    assert B_sonuc["butunluk"]["gecerli"] is True, "B tabanı şasi-geçersiz — kıyas koşulamaz"

    C_sonuc = json.loads((EDG026 / "sonuc_c.json").read_text())
    C_islem = json.loads((EDG026 / "islemler_c.json").read_text())
    C_seans = json.loads((EDG026 / "seanslar_c.json").read_text())
    assert C_sonuc["kosum"] == "c_slot20_r05" and not C_sonuc["smoke"]
    assert len(C_islem) == EDG026_C_CIVI["n_islem"], "C islemler dosyası çiviyle uyuşmuyor"
    assert C_sonuc["performans"]["net_pnl_equity"] == EDG026_C_CIVI["net_pnl_equity"]
    assert C_sonuc["performans"]["maxdd_kanonik"] == EDG026_C_CIVI["maxdd_kanonik"]
    assert C_sonuc["motor_sha256_16"] == MOTOR_SHA, "C kayıtlı motor sha çiviyle uyuşmuyor"
    assert C_sonuc["butunluk"]["gecerli"] is True, "C tabanı şasi-geçersiz — kıyas koşulamaz"

    H1_sonuc = json.loads((EDG027 / "sonuc_h1_scaleout.json").read_text())
    H1_islem = json.loads((EDG027 / "islemler_h1_scaleout.json").read_text())
    H1_seans = json.loads((EDG027 / "seanslar_h1_scaleout.json").read_text())
    assert H1_sonuc["hucre"] == "h1_scaleout" and not H1_sonuc["smoke"]
    assert len(H1_islem) == EDG027_H1_CIVI["n_islem"], "H1 islemler dosyası çiviyle uyuşmuyor"
    assert H1_sonuc["performans"]["net_pnl_equity"] == EDG027_H1_CIVI["net_pnl_equity"]
    assert H1_sonuc["islem"]["scaled_out_n"] == EDG027_H1_CIVI["scaled_out_n"]
    assert H1_sonuc["motor_sha256_16"] == MOTOR_SHA, "H1 kayıtlı motor sha çiviyle uyuşmuyor"
    assert H1_sonuc["butunluk"]["gecerli"] is True, "H1 şasi-geçersiz — düzeltme-etkisi kıyası koşulamaz"

    motor_guncel = _motor_sha_dogrula()

    # ---- eşli makine öz-kontrolleri: T↔T eşlemeleri fark=0, CI [0,0] --------------------------
    for ad, defter, civi in (("B", B_islem, EDG023_B_CIVI), ("C", C_islem, EDG026_C_CIVI)):
        kendi = _esli_analiz(defter, defter)
        assert kendi["esli_n"] == civi["n_islem"] and \
            kendi["anahtar_tekrar"] == {"taban": 0, "hucre": 0}, f"{ad}↔{ad} öz-eşleme bozuk"
        assert kendi["ort_fark"] == 0.0 and kendi["fark_pos_n"] == 0 and kendi["fark_neg_n"] == 0
        assert kendi["ci95_tarih_kumeli_eslenik"]["lo"] == 0.0 and \
            kendi["ci95_tarih_kumeli_eslenik"]["hi"] == 0.0, f"{ad}↔{ad} CI [0,0] değil"

    B_tarihler = [s["date"] for s in B_seans]
    C_tarihler = [s["date"] for s in C_seans]
    H1_tarihler = [s["date"] for s in H1_seans]
    assert H1_tarihler == B_tarihler, "H1 takvimi B ile aynı değil — F1x↔H1 kıyası şüpheli"

    taban_harita = {
        "F1x": ("B", B_sonuc, B_islem, B_tarihler,
                {"kaynak": str(EDG023), "dosya": "sonuc_varyant/islemler_varyant/seanslar_varyant"}),
        "F2x": ("C", C_sonuc, C_islem, C_tarihler,
                {"kaynak": str(EDG026), "dosya": "sonuc_c/islemler_c/seanslar_c"}),
    }

    hucre_blok: dict[str, dict] = {}
    kill_ozeti: dict[str, dict] = {}
    F_sonuclar: dict[str, dict] = {}
    F_islemler: dict[str, list] = {}
    for run in HUCRELER:
        taban_ad, T_sonuc, T_islem, T_tarihler, T_meta = taban_harita[run]
        H_sonuc = json.loads((SANDBOX / f"sonuc_{run}.json").read_text())
        H_islem = json.loads((SANDBOX / f"islemler_{run}.json").read_text())
        H_seans = json.loads((SANDBOX / f"seanslar_{run}.json").read_text())
        F_sonuclar[run] = H_sonuc
        F_islemler[run] = H_islem

        takvim_ayni = ([s["date"] for s in H_seans] == T_tarihler)
        esli = _esli_analiz(T_islem, H_islem)

        butunluk_ok = (H_sonuc["butunluk"]["gecerli"] and takvim_ayni
                       and esli["anahtar_tekrar"] == {"taban": 0, "hucre": 0}
                       and H_sonuc["motor_sha256_16"] == MOTOR_SHA)

        hucre_blok[run] = {
            "trial_id": HUCRELER[run]["trial_id"],
            "kart_adi": HUCRELER[run]["kart_adi"],
            "taban": {"ad": taban_ad, **T_meta},
            "enjeksiyon_kol": H_sonuc["enjeksiyon_kol"]["degerler"],
            "duzeltme_kill3": H_sonuc["duzeltme"]["oz_sinama_kill3"],
            "sure_sn": H_sonuc["sure_sn"],
            "butunluk_hucre": H_sonuc["butunluk"],
            "takvim_ayni_taban": takvim_ayni,
            "kill2_sasi_gecerli": butunluk_ok,
            "esli": esli,
            "tam_defter": _tam_defter(T_sonuc, H_sonuc, taban_ad),
        }
        kill_ozeti[run] = {
            "kill1_esli_lt60": esli["kill1_esli_lt_min"],
            "kill2_sasi_bozuk": not butunluk_ok,
            "kill3_monkeypatch_kanitsiz": False,   # koşum var = kill#3 assert'leri geçti (aksi halde ölürdü)
        }

    # ---- F1x ↔ H1: düzeltmenin KENDİ etkisi (taban=H1 düzeltmesiz; fark = R_F1x − R_H1) -------
    f1x_h1 = _esli_analiz(H1_islem, F_islemler["F1x"])
    f1x_vs_h1 = {
        "tanim": ("taban=H1 (EDG-027 h1_scaleout, düzeltmesiz scale-out), hücre=F1x (düzeltmeli); "
                  "fark = R_F1x − R_H1 (pozitif = düzeltme lehine). Aynı B dünyası + aynı kol "
                  "paramları; tek değişken trail-düzeltme monkeypatch'i."),
        "H1_civi": EDG027_H1_CIVI,
        "H1_butunluk_gecerli": H1_sonuc["butunluk"]["gecerli"],
        "esli": f1x_h1,
        "tam_defter": _tam_defter(H1_sonuc, F_sonuclar["F1x"], "H1"),
        "H1_scaled_kusur_izleri": {
            "scaled_out_n": H1_sonuc["islem"]["scaled_out_n"],
            "not": ("H1'in scaled kümesinde bars_held=0 n=18 + stop_gap n=21 (EDG-027 sonuc.json "
                    "scaled_betim kaydı); F1x'in aynı izleri hücre sonuc + esli.scaled_betim'de")},
    }

    out = {
        "kart": "EDG-2026-029",
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "yontem": {
            "esli_anahtar": "(ts_open[:10], ticker) — girişler değişmediği ölçüde aynı pozisyonun iki dünyadaki R'si",
            "esli_R": "satırın r_multiple'ı — scale-out'ta birleşik (banked+kalan; broker.close_position tek satır)",
            "esli_ci": ("işlem-TARİH-kümeli eşlenik bootstrap: kümeler eşli kümenin ayrık ts_open "
                        f"tarihleri; yerine-koymalı; iter={BOOT_ITER}, seed={BOOT_SEED}; "
                        "fark=hücre−taban; ay-kümeli CI yan-tablo (ikinci eşik değil)"),
            "tabanlar": ("B=EDG-023 varyant (rampa 15/36) · C=EDG-026 c_slot20_r05 (rampa 15/36 + "
                         "slot20 + 0.5R) · H1=EDG-027 h1_scaleout (B + scale-out DÜZELTMESİZ) — "
                         "hiçbiri yeniden koşulmadı; sha + n/pnl/dd çivileriyle doğrulandı"),
            "esli_makine_kontrolu": "B↔B (n=410) ve C↔C (n=772): tüm farklar 0, CI [0,0] — assert geçti",
            "duzeltme": "hücre sonuc.json'larının duzeltme bloğu (mekanizma + kill#3 öz-sınama kanıtları)",
        },
        "sha_dogrulama": {
            "motor_guncel": motor_guncel,
            "civi": MOTOR_SHA,
            "hucre_kayitlari_esit": all(
                F_sonuclar[r]["motor_sha256_16"] == MOTOR_SHA for r in HUCRELER),
            "config_civi": CONFIG_SHA,
        },
        "taban_ozetleri": {
            "B": {"kaynak": str(EDG023), "islem_n": len(B_islem),
                  "performans": B_sonuc["performans"],
                  "exit_reason_dagilim": B_sonuc["islem"]["exit_reason_dagilim"]},
            "C": {"kaynak": str(EDG026), "islem_n": len(C_islem),
                  "performans": C_sonuc["performans"],
                  "exit_reason_dagilim": C_sonuc["islem"]["exit_reason_dagilim"]},
            "H1": {"kaynak": str(EDG027), "islem_n": len(H1_islem),
                   "performans": H1_sonuc["performans"],
                   "exit_reason_dagilim": H1_sonuc["islem"]["exit_reason_dagilim"],
                   "esli_B_kaydi": "EDG-027 sonuc.json: eşli n=371, ort_fark=-0.1409, CI[-0.2639,-0.0451]"},
        },
        "hucreler": hucre_blok,
        "F1x_vs_H1_duzeltme_etkisi": f1x_vs_h1,
        "kill_bayraklari": kill_ozeti,
        "dosyalar": {
            "B": {"sonuc": str(EDG023 / "sonuc_varyant.json"),
                  "islemler": str(EDG023 / "islemler_varyant.json"),
                  "seanslar": str(EDG023 / "seanslar_varyant.json")},
            "C": {"sonuc": str(EDG026 / "sonuc_c.json"),
                  "islemler": str(EDG026 / "islemler_c.json"),
                  "seanslar": str(EDG026 / "seanslar_c.json")},
            "H1": {"sonuc": str(EDG027 / "sonuc_h1_scaleout.json"),
                   "islemler": str(EDG027 / "islemler_h1_scaleout.json"),
                   "seanslar": str(EDG027 / "seanslar_h1_scaleout.json")},
            **{r: {"sonuc": f"sonuc_{r}.json", "seanslar": f"seanslar_{r}.json",
                   "islemler": f"islemler_{r}.json"} for r in HUCRELER},
        },
    }
    (SANDBOX / "sonuc.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))

    print("\n==================== EDG-029 F1x↔B · F2x↔C · F1x↔H1 ÖZET ====================")
    for run, blok in hucre_blok.items():
        e = blok["esli"]
        t = blok["tam_defter"]
        ta = blok["taban"]["ad"]
        print(f"\n--- {run} ({blok['kart_adi']})  taban={ta}")
        print(f"  şasi geçerli={blok['kill2_sasi_gecerli']}  takvim_ayni={blok['takvim_ayni_taban']}")
        print(f"  eşli n={e['esli_n']} (kill#1={e['kill1_esli_lt_min']})  "
              f"ort_fark={e['ort_fark']}  CI95_tarih={e['ci95_tarih_kumeli_eslenik']}")
        print(f"  eşli +/-/0: {e['fark_pos_n']}/{e['fark_neg_n']}/{e['fark_sifir_n']}  "
              f"yalnız{ta}={e['yalniz_taban']['n']} yalnızH={e['yalniz_hucre']['n']}")
        print(f"  işlem n: {t['islem_n']}  net_pnl: {t['net_pnl_equity']}")
        print(f"  maxdd: {t['maxdd_kanonik']}  avg_r: {t['avg_r']}  hedef: {t['hedef_orani_pct']}")
        print(f"  scaled_out: {t['scaled_out']['hucre']}")
    e = f1x_vs_h1["esli"]
    print(f"\n--- F1x ↔ H1 (düzeltmenin kendi etkisi; fark = F1x − H1)")
    print(f"  eşli n={e['esli_n']}  ort_fark={e['ort_fark']}  CI95_tarih={e['ci95_tarih_kumeli_eslenik']}")
    print(f"  eşli +/-/0: {e['fark_pos_n']}/{e['fark_neg_n']}/{e['fark_sifir_n']}")
    print(f"  net_pnl fark: {f1x_vs_h1['tam_defter']['net_pnl_equity']}")
    print(f"\nyazıldı: {SANDBOX / 'sonuc.json'}")
    print("==============================================================================\n")


if __name__ == "__main__":
    mod = sys.argv[1] if len(sys.argv) > 1 else ""
    smoke = "--smoke" in sys.argv
    if mod in HUCRELER:
        kosum(mod, smoke=smoke)
    elif mod == "selftest":
        _sinamalari_kos()
        print("SELFTEST GEÇTİ: sha çivileri + rampa + yamasız kusur kanıtı + trail-düzeltme kill#3 "
              "kanıtları + şasi chandelier — replay koşulmadı (doğum kapısı).")
    elif mod == "birlestir":
        assert not smoke, "smoke'ta birlestir yok (tabanların smoke çıktısı yok; tabanlar yeniden koşulmaz)"
        birlestir()
    else:
        sys.exit("kullanım: olcum.py {F1x|F2x|selftest|birlestir} [--smoke]")

"""EDG-2026-072 — REJİM-KOŞULLU ÇIKIŞ override'ı (trend_up geniş trail/uzun time-stop, chop kısa
time-stop/erken breakeven) · ölçüm aracı (2026-09-04)

Kart: research/cards/EDG-2026-072-rejim-kosullu-cikis-onerisi.yaml (OKU-DOKUNMA; hüküm Rol-1'in).
Rol: ÖLÇÜM ajanı. Bu modül HÜKÜM VERMEZ, karta dokunmaz, git/canlı/broker/state'e YAZMAZ.

ŞASİ: EDG-026 (research/olcumler/edg026_slot20_2026-08-12/olcum.py) C-dünyası AYNEN devralındı
(izole sandbox, EDG-022 DONMUŞ config kopyaları + bars symlink SALT-OKUNUR, rampa-15/36
monkeypatch'i, slot-20 + 0.5R-taban param-enjeksiyonları, kancalar, bütünlük kontrolleri).
Yapısal ikiz emsal: research/olcumler/edg033_rejim_boyut_2026-08-12/olcum.py — bu ölçüm o
desenin params_by_regime enjeksiyon iskeletini devralır, ANCAK enjekte edilen anahtar
`position_size_r` (boyut) DEĞİL, çıkış anahtarlarıdır (`exit.trail_atr_mult`,
`exit.time_stop_days`, `exit.breakeven_r` — `meridian/config.py::REGIME_EXIT_KEYS`'te adıyla
izinli). KIYAS TABANI = EDG-026'nın HAZIR C çıktıları (sonuc_c/seanslar_c/islemler_c —
YENİDEN KOŞULMAZ, salt-okunur; sha256 aşağıda DONDURULDU).

GİT SAPMASI (beyan — AJAN kuralı "git YOK", ihlal=tur iptali): kart D1 "girdiler git BLOB'una
bağlanır (git rev-parse HEAD:<yol>)" diyor. Bu ölçüm ajanı turunda `git` HİÇBİR biçimde
çağrılmaz (salt-okunur dahil) — bu yüzden girdi kimliği git blob sha'sı DEĞİL, doğrudan sha256
içerik-adresleme ile bağlanır (aynı garanti: ağaç değişirse hash değişir). Ayrıca
`seanslar_c.json` (tam pencere) zaten `.gitignore:57` (`research/olcumler/*/seanslar_*.json`)
altında — git-izli DEĞİL, salt content-hash yolu ONU ZATEN kapsıyordu. EDG026_SHA256 sözlüğü bu
turda `shasum -a 256` ile DONDURULDU (git DEĞİL); her koşumda yeniden hesaplanıp kıyaslanır.

MOTOR YÜZEYİ (birebir çağrılır, YENİDEN YAZILMAZ): `config.resolve_params(params, by_regime,
regime)` — yalnız `k in params` VEYA `k in REGIME_EXIT_KEYS` olan anahtarları ezer (knob icat
edemez). `backtest.replay(..., params_by_regime=...)`: HER SEANS `eff = config.resolve_params(
params, params_by_regime, rj["regime"])` (o günün KAPANIŞ rejimi) hesaplar ve BUNU hem açık
pozisyonların `strategy.manage_position(df_t, pos_dict, eff, bars_held, regime_ok)` çağrısına
hem de o günün `strategy.scan_entry(..., eff, ...)` taramasına geçirir — yani bir pozisyonun
ÇIKIŞ kararı o pozisyonun GİRİŞ günündeki değil, YÖNETİLDİĞİ GÜNÜN rejimine göre çözülür (rejim
gün be gün değişebilir; kayıttaki `regime` alanı GİRİŞ/plan günü rejimidir — bu ayrım aşağıda
öz-sınama 2'de ayrıca izlenir). `strategy.manage_position` içinde üç anahtar okunur:
`exit.trail_atr_mult` (trail mesafesi), `exit.time_stop_days` (`bars_held >= time_stop` çıkışı),
`exit.breakeven_r` (kâr `>= be_r·R` olunca stopu girişe çeker). `guard.py` DOKUNULMAZ (sevk
kapısı bu turda açılmıyor).

HÜCRELER (kart k_registry, K=2 — DONUK, sonradan değişmez):
  kontrol : {rg: {} for rg in REGIMES}          — hiçbir override YOK; C ile BİT-ÖZDEŞ olmalı
  h1      : trend_up{trail_atr_mult ×1.5, time_stop_days ×1.5} + chop{time_stop_days ×0.5}
  h2      : h1 + chop{breakeven_r ×0.5}
  pk      : (kart pozitif_kontrol — K DIŞI, HÜKÜM YÜZEYİ DEĞİL) chop{time_stop_days=1} MUTLAK
            sentetik uç değer — override'ın gerçekten manage_position'a ulaştığının kanıtı.
Çarpanlar TABANA (donmuş EDG-022 strategy.yaml `params`) çalışma-anında uygulanır, hardcode
EDİLMEZ. YUVARLAMA BEYANI: int anahtar (`exit.time_stop_days`) `round()` (Python round-half-to-
-even) ile en yakın tama yuvarlanır; float anahtarlar 6 hane. trend_up time_stop: 15×1.5=22.5→22
(22 çift, round-half-to-even). chop time_stop: 15×0.5=7.5→8 (8 çift). İkisi de bounds.yaml
[3,40] içinde; trend_up trail 2.5×1.5=3.75 ([1.0,5.0] içinde); chop breakeven 1.0×0.5=0.5
([0.0,3.0] içinde) — sınır ihlali YOK (öz-sınamada doğrulanır).

ÖZ-SINAMA (EDG-033 deseni + EK — kart D4):
  1 (koşum öncesi): dört rejimde resolve_params(params, harita, rejim) beklenen anahtarları
     verir; DOKUNULMAYAN anahtarlar (rejimin haritası boşsa TÜMÜ) taban params'la birebir eşit
     (yüzey sızıntısı yok); bilinmeyen rejim → taban; değerler bounds içinde.
  2 (koşum içi): `strategy.manage_position`e giden params'ın DOKUNULAN anahtarları, O GÜNÜN
     rejimine göre beklenen değerle eşleşiyor mu (rejim `regime.build_regime_json` kancasından
     günlük yakalanır); ihlal sayısı bütünlük kaydına girer (0 olmalı).
  EK / POZİTİF KONTROL (kart pozitif_kontrol, `pk` hücresi): sentetik chop{time_stop_days=1}
     altında zaman-stopu ATEŞLEYEN kapanmış işlemlerin `bars_held`i her zaman `>=1`, `<15`
     (taban) aralığına DÜŞMELİ VE chop işlemlerinin bars_held DAĞILIMI kontrole göre ÖLÇÜLEBİLİR
     biçimde düşmeli — yol-tutarlı (gerçek replay üzerinden, sentetik bar/pozisyon DEĞİL).
     PK tutmazsa hiçbir sayı YAYILMAZ (bu modül PK başarısızsa `kiyasla` adımına GEÇMEZ — aşağıda
     `pk()` dönüşü kontrol edilir, çağıran script bunu zorunlu kılar).

PENCERELER: `smoke` = 2022-01-01→2022-06-30 (026/033 AYNEN; kill#1 bit-özdeşlik burada — bu
pencerede SIFIR chop işlemi var, yalnız şasi-kimliği kanıtı). `duman` = 2022-01-01→2023-03-01
(~14 ay; taban C defterinde bu aralıkta 64/84 chop işlemi var — kısa-pencereli mekanizma sanity
+ PK için chop popülasyonu taşıyan EN KISA aralık, taban C ile ölçülüp seçildi). `tam` = C'nin
kendi penceresi (2022-01-01→2026-07-30, 251 sembol, ~1787s — nohup ile ayrık koşulur, D7).

KULLANIM:
  olcum.py adim0                  # ADIM-0: sha eşleşmesi + params_by_regime boş kanıtı + rejim-n
  olcum.py oz_sinama               # öz-sınama 1 (koşum-öncesi resolve_params) — h1/h2/pk
  olcum.py smoke                   # kontrol_smoke + EDG-026 smoke C ile bit-özdeşlik (kill#1)
  olcum.py duman                   # kontrol_duman + h1_duman + pk_duman (mekanizma + PK, ön plan)
  olcum.py kosum {kontrol|h1|h2} --tam    # TAM pencere (~30dk) — nohup arkasından çağrılır
  olcum.py kiyasla                 # üç TAM koşum bittikten SONRA (Rol-1) → sonuc_<bugün>.json

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen = None + neden); YASA-4 (sessiz-yutma işaretli + gerekçe);
YASA-6 (okuyucu: sonuc_*/seanslar_*/islemler_* → `kiyasla` tüketir; sonuc_<tarih>.json → Rol-1).
SALT-OKUMA: config.STATE koşum-başına izole sandbox; canlı state'e ve motor dosyalarına tek bayt
yazılmaz. meridian.loop / counterfactual / cf_backfill / hermes İTHAL EDİLMEZ — sys.modules ile
KANITLANIR. `git` BU MODÜLDE HİÇ ÇAĞRILMAZ (yukarıdaki GİT SAPMASI beyanı).
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
REPLAY_END = "2026-07-30"                      # C (026) ile AYNI pencere — TAM koşum
SMOKE_END = "2022-06-30"                        # 026/033 smoke penceresi AYNEN (kill#1 tabanı)
DUMAN_END = "2023-03-01"                        # ~14 ay; taban C'de 64/84 chop işlemi bu aralıkta
BOOT_SEED = 20260904                            # slot-doluluk CI (kosum() içi, C-şasi teşhis bootstrap'ı — kart-kıyas seed'i DEĞİL)
BOOT_SEED_072 = BOOT_SEED                        # ALIAS (tek-kaynak): EDG-072 ΔP&L bootstrap seed'i, BOOT_SEED'i TAKİP eder
BOOT_SEED_073 = 20260903                         # kart EDG-2026-073 ZORUNLU seed (donuk, ön-kayıt — BOOT_SEED_072'den BAĞIMSIZ)
BOOT_ITER = 5000

# C dünyasının DONUK parametreleri (026'dan AYNEN — hücreler yalnız rejim-koşullu ÇIKIŞ ekler)
RAMPA = {"tam_dd": 0.15, "sifir_dd": 0.36}
SLOT = 20
BOYUT_R = 0.5                                   # taban (C dünyası; flat params enjeksiyonu, AYNEN)
REGIMES = ("trend_up", "trend_down", "chop", "high_vol")   # config.VALID_REGIMES

# ---------------------------------------------------------------------------------------------
# ADIM-0(a) — EDG-026 girdi kimliği: sha256 İÇERİK-ADRESLEME (git DEĞİL — bkz. başlık "GİT SAPMASI")
# Bu turda `shasum -a 256` ile DONDURULDU (2026-09-04); git blob sha DEĞİL, dosya baytlarının
# doğrudan sha256'sı — seanslar_c.json git-izli olmasa da (.gitignore:57) bu yol onu kapsar.
# ---------------------------------------------------------------------------------------------
EDG026_SHA256 = {
    "islemler_c.json": "fdb428551ceab4de69ca053a6ef4f16d8caad136306cd2946fb1a6edc6d5acda",
    "seanslar_c.json": "6a8aceaea7b453182c1179086fdc3be63e56d4cb81f5218a7551672f562c178b",
    "sonuc_c.json": "c18e3b4497dc1e618d8d3d543ad444060cc28a1fe2561b531d5a86adea5672ff",
    "olcum.py": "fd8b39c8e981a2f9a0eedf2f5f2d63804f2dbe299a6cbe6dac2ec12ff16cff2d",
}
KILL_TREND_UP_CHOP_MIN = 30                     # kart adim_0_fizibilite (c): rejim başına taban-n eşiği
DD_KOSUL_KATSAYI = 1.3   # kart success_metric (EDG-072/073 İKİSİNDE de "×1,3" — donuk; koda GÖMÜLMEDİ, yalnız hesap için; hüküm değil)

# ---------------------------------------------------------------------------------------------
# K REGISTRY (kart k_registry — DONUK, sonradan değişmez; çarpanlar TABANA çalışma-anında uygulanır)
# ---------------------------------------------------------------------------------------------
HUCRE_TRIAL_ID = {
    "kontrol": "sasi_sinamasi", "h1": "EDG-072-h1-trend-genis-chop-kisa",
    "h2": "EDG-072-h2-h1-arti-erken-breakeven", "pk": "kart_pozitif_kontrol_K_disi",
}
CARPAN_TANIM: dict[str, dict[str, dict[str, float]]] = {
    "h1": {
        "trend_up": {"exit.trail_atr_mult": 1.5, "exit.time_stop_days": 1.5},
        "chop": {"exit.time_stop_days": 0.5},
    },
    "h2": {
        "trend_up": {"exit.trail_atr_mult": 1.5, "exit.time_stop_days": 1.5},
        "chop": {"exit.time_stop_days": 0.5, "exit.breakeven_r": 0.5},
    },
}
PK_ABSOLUT: dict[str, dict[str, float]] = {"chop": {"exit.time_stop_days": 1}}   # sentetik, MUTLAK (çarpan değil)
TIP_KURALI = {"exit.trail_atr_mult": float, "exit.time_stop_days": int, "exit.breakeven_r": float}
YUVARLAMA_BEYANI = ("int anahtar (exit.time_stop_days): Python round() — round-half-to-even; "
                    "float anahtarlar: round(x, 6)")

KART3 = ["tavan_sifir", "evren_bagladi", "derisk_bagladi"]
YASAK = ("meridian.loop", "meridian.counterfactual", "meridian.cf_backfill", "meridian.hermes")
BIT_BOLUMLER = ("replay", "butunluk", "islem", "performans", "doluluk", "tepe_isi",
                "betim", "tasnif_tum_seans", "birincil", "ci95_ay_kumeli")

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


def _sha_full(p: pathlib.Path) -> str | None:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return None    # ölçülemedi (dosya yok/okunamadı)


def _sha(p: pathlib.Path) -> str | None:
    full = _sha_full(p)
    return full[:16] if full is not None else None


def _yakin(a, b, tol: float = 1e-9) -> bool:
    if a is None or b is None:
        return a is b
    return abs(float(a) - float(b)) <= tol


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


def _carpan_uygula(taban: float, katsayi: float, tip):
    ham = float(taban) * float(katsayi)
    if tip is int:
        return int(round(ham))          # round-half-to-even — YUVARLAMA_BEYANI
    return round(ham, 6)


def _taban_params() -> dict:
    """EDG-022 donmuş `strategy.yaml` params + ENJEKSİYON 2 (position_size_r=BOYUT_R) — kosum()
    içindeki AYNI türetimin TEK KAYNAĞI (tek-kaynak yasası: iki kopya sessizce ayrışmasın diye
    `kosum()` da normalde bunu tekrar yapar; burada yalnız kosum()'u tetiklemeden — sandbox/bars
    gerekmeden — şasi sınaması gibi HAFİF kontroller için kullanılır)."""
    import yaml
    stg = yaml.safe_load((EDG022 / "state" / "strategy.yaml").read_text())
    params = dict(stg["params"])
    params["position_size_r"] = BOYUT_R
    return params


def _bar_cache_ozet(bars_dir: pathlib.Path | None = None) -> dict:
    """`state/bars` içeriğinin İÇERİK-adresli özeti (git DEĞİL — GİT SAPMASI AYNEN, modül
    başlığı): her CSV'nin sha256(16)'sı + dosya adı birleştirilip TEK bir sha256'ya indirgenir
    ('birleşik sha'). En yeni mtime de taşınır — 073 kill-2'nin 'koşum sırasında değişmedi'
    beyanı bunu kullanır (kesin kanıt DEĞİL, mtime-tabanlı çıkarım)."""
    d = bars_dir or (REPO / "state" / "bars")
    dosyalar = sorted(d.glob("*.csv"))
    parcalar = []
    en_yeni = 0.0
    for p in dosyalar:
        h = _sha(p)
        if h is None:
            continue
        en_yeni = max(en_yeni, p.stat().st_mtime)
        parcalar.append(f"{p.name}:{h}")
    birlesik = hashlib.sha256("\n".join(parcalar).encode()).hexdigest()
    return {"n_dosya": len(dosyalar), "birlesik_sha256": birlesik,
           "en_yeni_mtime_utc": (dt.datetime.fromtimestamp(en_yeni, dt.timezone.utc).isoformat(timespec="seconds")
                                if dosyalar else None)}


def _log_baslangic_ts(log_path: pathlib.Path) -> str | None:
    """Bir `kosum_*.log`'un İLK satırının `ts` alanı — o koşumun yaklaşık başlangıç anı (dataset
    yüklemesi en erken uyarı satırından hemen önce başlar). Dosya yoksa/hiç geçerli JSON satırı
    yoksa None (UYDURMA YASAĞI — ölçülemedi)."""
    if not log_path.exists():
        return None
    with log_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = rec.get("ts")
            if ts:
                return ts
    return None


def harita_olustur(hucre: str, taban: dict) -> dict[str, dict[str, float]]:
    """hücre → rejim → {anahtar: değer} MUTLAK haritası. Değerler TABANDAN (donmuş params) çalışma
    anında türetilir — hardcode edilmez (kart: "çarpanlar ön-kayıttır, sonradan değişmez", ama
    SAYI ön-kayıt DEĞİL, TÜRETİM kuralı ön-kayıttır)."""
    out: dict[str, dict[str, float]] = {rg: {} for rg in REGIMES}
    if hucre == "kontrol":
        return out
    if hucre == "pk":
        for rg, ov in PK_ABSOLUT.items():
            out[rg] = dict(ov)
        return out
    assert hucre in CARPAN_TANIM, f"hücre {hucre} tanımsız (kontrol|h1|h2|pk)"
    for rg, kmap in CARPAN_TANIM[hucre].items():
        for k, kat in kmap.items():
            out[rg][k] = _carpan_uygula(taban[k], kat, TIP_KURALI[k])
    return out


# ---------------------------------------------------------------------------------------------
# ADIM-0 — sha eşleşmesi + params_by_regime boş kanıtı + rejim başına taban-n (kart adim_0_fizibilite)
# ---------------------------------------------------------------------------------------------
def adim0():
    dosya_kiyas = {}
    for ad, beklenen in EDG026_SHA256.items():
        simdi = _sha_full(EDG026 / ad)
        dosya_kiyas[ad] = {"beklenen": beklenen, "simdi": simdi, "esit": simdi == beklenen}
    a_hepsi_esit = all(v["esit"] for v in dosya_kiyas.values())

    stg = json.loads(json.dumps(__import__("yaml").safe_load(
        (EDG022 / "state" / "strategy.yaml").read_text())))
    by_regime = stg.get("params_by_regime")
    b_sema_dogru = isinstance(by_regime, dict) and set(by_regime.keys()) == set(REGIMES)
    b_hepsi_bos = b_sema_dogru and all(not (by_regime.get(rg) or {}) for rg in REGIMES)

    islemler_c = json.loads((EDG026 / "islemler_c.json").read_text())
    n_rejim: dict[str, int] = {}
    for t in islemler_c:
        rg = str(t.get("regime"))
        n_rejim[rg] = n_rejim.get(rg, 0) + 1
    c_rejim = {}
    for rg in REGIMES:
        n = n_rejim.get(rg, 0)
        c_rejim[rg] = {"n": n, "esik": KILL_TREND_UP_CHOP_MIN,
                       "olculebilir": n >= KILL_TREND_UP_CHOP_MIN}

    gecerli = a_hepsi_esit and b_hepsi_bos
    out = {
        "kart": "EDG-2026-072", "adim": "0",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "a_edg026_sha_eslesme": {"dosya_kiyas": dosya_kiyas, "hepsi_esit": a_hepsi_esit,
                                 "not": ("git rev-parse DEĞİL — içerik sha256 (GİT SAPMASI beyanı, "
                                         "modül başlığı); EDG026_SHA256 bu turda shasum ile donduruldu")},
        "b_params_by_regime_bos": {"sema_dogru": b_sema_dogru, "hepsi_bos": b_hepsi_bos,
                                   "kaynak": str(EDG022 / "state" / "strategy.yaml"),
                                   "icerik": by_regime},
        "c_rejim_basina_taban_n": c_rejim,
        "gecerli": gecerli,
        "not": ("kill-list (kart): (a) veya (b) düşerse ölçüm GEÇERSİZ. (c) yalnız KAYIT — "
                "trend_down/high_vol taban-defterde 0 işlem taşıyor (K registry zaten yalnız "
                "trend_up+chop dokunuyor, bu iki rejim eşiği geçiyor); hücre yine koşar."),
    }
    (SANDBOX / "adim0.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True, default=str))
    print(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True, default=str))
    print(f"yazıldı: {SANDBOX/'adim0.json'}")
    print("ADIM0_GECERLI" if gecerli else "ADIM0_GECERSIZ")
    return gecerli


# ---------------------------------------------------------------------------------------------
# SANDBOX HAZIRLIĞI — izole state (EDG-022 DONMUŞ config kopyaları; 026/033 şasisi AYNEN)
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
    return st


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


def classify(rec: dict, no_trade_before: int) -> str:
    acik_slot = rec["acik_slot"]
    if acik_slot <= 0:
        return "tavan_sifir"
    if rec["bar_i"] is not None and rec["bar_i"] < no_trade_before:
        return "isinma"
    if (rec["exposure_budget_pct"] or 0) <= 0:
        return "rejim_kapali"
    return "evren_bagladi" if rec["aday_n"] <= acik_slot else "derisk_bagladi"


def _isi_ozet(degerler: list[float]) -> dict | None:
    import numpy as np
    if not degerler:
        return None
    a = np.asarray(degerler, dtype=float)
    hist: dict[str, int] = {}
    for v in a:
        k = f"{round(v * 2) / 2:.1f}"
        hist[k] = hist.get(k, 0) + 1
    return {"max": round(float(a.max()), 3), "p50": round(float(np.percentile(a, 50)), 3),
            "p90": round(float(np.percentile(a, 90)), 3), "p99": round(float(np.percentile(a, 99)), 3),
            "ort": round(float(a.mean()), 3), "sifir_ustu_seans_n": int((a > 0).sum()),
            "n_seans": int(len(a)),
            "histogram_0p5R": dict(sorted(hist.items(), key=lambda kv: float(kv[0])))}


def _isi_rejim_kirilimi(sess: list[dict]) -> dict:
    gruplar: dict[str, list[dict]] = {}
    for r in sess:
        gruplar.setdefault(str(r.get("regime")), []).append(r)
    out = {}
    for rg in sorted(gruplar, key=lambda k: -len(gruplar[k])):
        rs = gruplar[rg]
        out[rg] = {"seans_n": len(rs), "gerceklesen_size_r": _isi_ozet([r["acik_size_r_toplam"] for r in rs]),
                   "ort_acik_pozisyon": round(sum(r["n_acik"] for r in rs) / len(rs), 3)}
    return out


def bootstrap_ci(sess: list[dict], siniflar: list[str], n_iter: int = BOOT_ITER,
                 seed: int = BOOT_SEED) -> dict | None:
    import numpy as np
    if not sess:
        return None
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
        out[c] = {"lo": round(float(np.percentile(arr, 2.5)), 4), "hi": round(float(np.percentile(arr, 97.5)), 4),
                  "orta": round(float(np.median(arr)), 4)}
    out["_n_ay_kume"] = m
    return out


def _islem_araligi_sayimi(islemler: list[dict], takvim: list[str]) -> list[int]:
    araliklar = [(str(t["ts_open"])[:10], str(t["ts_close"])[:10]) for t in islemler
                 if t.get("ts_open") and t.get("ts_close")]
    out = []
    for d in takvim:
        out.append(sum(1 for a, b in araliklar if a <= d <= b))
    return out


# ---------------------------------------------------------------------------------------------
# ÖZ-SINAMA 1 (koşum öncesi) — resolve_params, tek koşum başlatmadan (bars gerekmez)
# ---------------------------------------------------------------------------------------------
def oz_sinama_1(hucre: str, params: dict, harita: dict, bounds: dict) -> dict:
    sys.path.insert(0, str(REPO))
    from meridian import config
    by_regime_inj = {rg: dict(harita.get(rg, {})) for rg in REGIMES}
    kayit = []
    bounds_ihlal = []
    for rg in REGIMES:
        eff = config.resolve_params(params, by_regime_inj, rg)
        beklenen_rg = harita.get(rg, {})
        for k, v in beklenen_rg.items():
            assert _yakin(eff.get(k), v), f"{hucre}/{rg}/{k}: {eff.get(k)} != {v}"
            b = bounds.get(k)
            if b is not None and not (float(b["min"]) <= float(v) <= float(b["max"])):
                bounds_ihlal.append({"rejim": rg, "anahtar": k, "deger": v, "bounds": b})
        a = {kk: vv for kk, vv in eff.items() if kk not in beklenen_rg}
        b0 = {kk: vv for kk, vv in params.items() if kk not in beklenen_rg}
        assert a == b0, f"{hucre}/{rg}: dokunulmayan anahtar yüzeyi sızdı"
        kayit.append({"rejim": rg, "dokunulan": beklenen_rg})
    eff_bilinmeyen = config.resolve_params(params, by_regime_inj, "bilinmeyen_rejim")
    assert eff_bilinmeyen == params, "bilinmeyen rejim tabana düşmedi"
    return {"hucre": hucre, "gecti": True, "kayit": kayit, "bounds_ihlal": bounds_ihlal,
           "bilinmeyen_rejim_taban": True, "yuvarlama_beyani": YUVARLAMA_BEYANI}


def oz_sinama_calistir() -> dict:
    st_dir = hazirla("oz_sinama")
    sys.path.insert(0, str(REPO))
    import yaml
    from meridian import config
    config.STATE = st_dir
    stg = yaml.safe_load((st_dir / "strategy.yaml").read_text())
    params = dict(stg["params"])
    bounds = yaml.safe_load((st_dir / "bounds.yaml").read_text())
    sonuclar = {}
    for hucre in ("h1", "h2", "pk"):
        harita = harita_olustur(hucre, params)
        sonuclar[hucre] = oz_sinama_1(hucre, params, harita, bounds)
        sonuclar[hucre]["harita_mutlak"] = harita
    out = {"kart": "EDG-2026-072", "adim": "oz_sinama_1",
          "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
          "taban_params": {k: params[k] for k in TIP_KURALI}, "sonuclar": sonuclar,
          "hepsi_gecti": all(v["gecti"] for v in sonuclar.values())}
    (SANDBOX / "oz_sinama_1.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True, default=str))
    print(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True, default=str))
    print(f"yazıldı: {SANDBOX/'oz_sinama_1.json'}")
    print("OZ_SINAMA_1_GECTI" if out["hepsi_gecti"] else "OZ_SINAMA_1_BASARISIZ")
    return out


# ---------------------------------------------------------------------------------------------
# HÜCRE KOŞUMU (kontrol | h1 | h2 | pk) — 026/033 kosum() düzeni + rejim-koşullu ÇIKIŞ enjeksiyonu
# ---------------------------------------------------------------------------------------------
def kosum(hucre: str, pencere: str = "tam"):
    assert hucre in ("kontrol", "h1", "h2", "pk"), f"hücre {hucre} tanımsız"
    assert pencere in ("tam", "smoke", "duman"), f"pencere {pencere} tanımsız"
    r_start = REPLAY_START
    r_end = {"tam": REPLAY_END, "smoke": SMOKE_END, "duman": DUMAN_END}[pencere]
    outdir = SANDBOX if pencere == "tam" else (SANDBOX / pencere)
    outdir.mkdir(exist_ok=True)
    run_id = hucre if pencere == "tam" else f"{hucre}_{pencere}"

    st_dir = hazirla(run_id)
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

    brk.derisk_mult = _rampa_fn(RAMPA["tam_dd"], RAMPA["sifir_dd"])
    assert brk.derisk_mult is not ORIJ_DERISK
    assert brk.derisk_mult(90.0, 100.0) == 1.0
    assert abs(brk.derisk_mult(80.0, 100.0) - 0.7619) < 1e-9
    assert brk.derisk_mult(64.0, 100.0) == 0.0
    assert brk.max_positions_at(80.0, 100.0, 5) == 4
    assert brk.max_positions_at(80.0, 100.0, 20) == 15

    stg = yaml.safe_load((st_dir / "strategy.yaml").read_text())
    params = dict(stg["params"])
    by_regime_orij = stg.get("params_by_regime")
    sv = int(stg.get("version"))
    bounds = yaml.safe_load((st_dir / "bounds.yaml").read_text())
    goal = config.goal()

    onceki = {"max_open_positions": int(goal["limits"]["max_open_positions"]),
              "position_size_r": float(params["position_size_r"])}
    goal["limits"]["max_open_positions"] = SLOT            # ENJEKSİYON 1 (C dünyası AYNEN)
    params["position_size_r"] = BOYUT_R                    # ENJEKSİYON 2 (C dünyası AYNEN)

    assert isinstance(by_regime_orij, dict) and set(by_regime_orij.keys()) == set(REGIMES), \
        f"params_by_regime şeması beklenmedik: {by_regime_orij}"
    for _rg in REGIMES:
        assert not (by_regime_orij.get(_rg) or {}), \
            f"params_by_regime[{_rg}] BOŞ değil — donmuş şasi varsayımı bozuk"

    # ---- ENJEKSİYON 3 (BU KARTIN değişkeni): rejim-koşullu ÇIKIŞ anahtarları ------------------
    HARITA = harita_olustur(hucre, params)
    by_regime_inj = {rg: dict(HARITA.get(rg, {})) for rg in REGIMES}
    touched_keys = sorted({k for m in HARITA.values() for k in m})

    oz1 = oz_sinama_1(hucre, params, HARITA, bounds)

    limits = goal["limits"]
    max_open = int(limits["max_open_positions"])
    no_trade_before = int(limits.get("no_trade_before_bars", 0))
    assert max_open == SLOT

    # ---- kancalar (026/033 deseni AYNEN + ÖZ-SINAMA 2: manage_position tüketim kanıtı) --------
    seans_by_date: dict[str, dict] = {}
    _cur_close_date = [None]
    _gunun_rejimi = [None]
    _dup: list[str] = []
    _frame_miss = [0]
    _carpan_ihlal: list[dict] = []     # ÖZ-SINAMA 2: manage_position'a giden eff != beklenen
    _zaman_stop_kanit: list[dict] = []  # time_stop ATEŞLEYEN her kapanış: bars_held vs eşik (PK kanıtı)

    _orig_maxpos = brk.max_positions_at
    _orig_regime = backtest.regime_mod.build_regime_json
    _orig_scan = backtest.strat.scan_entry
    _orig_manage = backtest.strat.manage_position

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
            "eff_max_open": int(n), "n_acik": int(n_acik), "acik_slot": int(n) - int(n_acik),
            "size_mult": float(brk.derisk_mult(equity, peak)),
            "acik_size_r_toplam": round(sum(float(p.size_r) for p in pozlar), 3),
            "acik_risk_dollars_giris": round(sum(float(p.risk_dollars) for p in pozlar), 2),
            "acik_kalan_risk_dollars": round(sum(
                max(0.0, (float(p.entry) - max(float(p.stop), float(p.trail_stop))) * int(p.qty))
                for p in pozlar), 2),
            "regime": None, "exposure_budget_pct": None, "n_scan_cagri": 0, "n_sinyal": 0,
        }
        if date in seans_by_date:
            _dup.append(date)
        seans_by_date[date] = rec
        return n

    def _regime(idx_df, params_, asof):
        rj = _orig_regime(idx_df, params_, asof)
        date = str(asof)[:10]
        _cur_close_date[0] = date
        _gunun_rejimi[0] = rj.get("regime")
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

    def _manage(bars, position, params_, bars_held, regime_ok):
        rg = str(_gunun_rejimi[0])
        beklenen_rg = HARITA.get(rg, {})
        for k in touched_keys:
            exp_v = beklenen_rg[k] if k in beklenen_rg else params[k]
            got_v = params_.get(k)
            if not _yakin(got_v, exp_v):
                if len(_carpan_ihlal) < 20:
                    _carpan_ihlal.append({"date": _cur_close_date[0], "regime": rg, "anahtar": k,
                                          "gorulen": got_v, "beklenen": exp_v})
                else:
                    _carpan_ihlal.append({})
        dec = _orig_manage(bars, position, params_, bars_held, regime_ok)
        if dec.exit_reason == "time_stop":
            esik = beklenen_rg.get("exit.time_stop_days", params["exit.time_stop_days"])
            if len(_zaman_stop_kanit) < 500:
                _zaman_stop_kanit.append({"date": _cur_close_date[0], "regime": rg,
                                          "bars_held": int(bars_held), "esik": esik,
                                          "esigi_karsiladi": bars_held >= esik})
        return dec

    brk.max_positions_at = _maxpos
    backtest.regime_mod.build_regime_json = _regime
    backtest.strat.scan_entry = _scan
    backtest.strat.manage_position = _manage

    t0 = dt.datetime.now()
    bars, index = dataset.load_cached()
    res = backtest.replay(params, bars, index, goal, r_start, r_end,
                          strategy_version=sv, params_by_regime=by_regime_inj,
                          with_gate_detail=False)
    sure = round((dt.datetime.now() - t0).total_seconds(), 1)

    yasak_yuklu = [m for m in sys.modules if m in YASAK]

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

    trades = res.trades or []

    def _size_ozet(v: list[float]) -> dict | None:
        if not v:
            return None
        return {"n": len(v), "min": round(min(v), 3), "max": round(max(v), 3), "ort": round(sum(v) / len(v), 3)}

    sess = sorted(seans_by_date.values(), key=lambda r: (r["bar_i"] if r["bar_i"] is not None else 0))
    scan_vs_plan = []
    for r in sess:
        r["aday_n"] = r["n_sinyal"]
        r["silahli_n"] = plan_silahli.get(r["date"], 0)
        r["plan_aday"] = plan_aday.get(r["date"], 0)
        if r["n_sinyal"] != r["plan_aday"]:
            scan_vs_plan.append({"date": r["date"], "n_sinyal": r["n_sinyal"], "plan_aday": r["plan_aday"]})
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
            "risk_dollars_giris_max": round(max((r["acik_risk_dollars_giris"] for r in sess), default=0.0), 2),
            "kalan_risk_dollars_max": round(max((r["acik_kalan_risk_dollars"] for r in sess), default=0.0), 2),
            "kalan_risk_nav_pct_max": round(max(
                (100.0 * r["acik_kalan_risk_dollars"] / r["eq_open"] for r in sess if r["eq_open"] > 0),
                default=0.0), 3),
        },
        "eszamanli_poz_max": {"open_fazi": max((r["n_acik"] for r in sess), default=0),
                              "islem_araligi": max(aralik_sayim, default=0)},
    }

    butunluk_gecerli = (_frame_miss[0] == 0 and not _dup and not scan_vs_plan
                        and not yasak_yuklu and not base_max_bozuk and not _carpan_ihlal)

    # ---- diagnostic: time_stop kanıt tablosu, rejim başına (PK/self-test 2'nin post-run özeti) --
    zs_rejim: dict[str, dict] = {}
    for kayit in _zaman_stop_kanit:
        rg = str(kayit["regime"])
        g = zs_rejim.setdefault(rg, {"n": 0, "esigi_karsilamayan_n": 0, "bars_held": []})
        g["n"] += 1
        g["bars_held"].append(kayit["bars_held"])
        if not kayit["esigi_karsiladi"]:
            g["esigi_karsilamayan_n"] += 1
    zs_ozet = {rg: {"n": g["n"], "esigi_karsilamayan_n": g["esigi_karsilamayan_n"],
                    "bars_held_min": min(g["bars_held"]), "bars_held_max": max(g["bars_held"]),
                    "bars_held_ort": round(sum(g["bars_held"]) / len(g["bars_held"]), 3)}
              for rg, g in zs_rejim.items()}

    out = {
        "kart": "EDG-2026-072", "kosum": f"{hucre}_{HUCRE_TRIAL_ID[hucre]}", "hucre": hucre,
        "pencere": pencere, "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sure_sn": sure,
        "rampa": {"tam_dd": RAMPA["tam_dd"], "sifir_dd": RAMPA["sifir_dd"],
                  "enjeksiyon": "MONKEYPATCH (beyanlı — 023/026/033 deseni AYNEN; motor DOSYASI değişmedi)"},
        "param_enjeksiyon": {
            "max_open_positions": {"once": onceki["max_open_positions"], "sonra": SLOT,
                                   "yuzey": "goal['limits'] (026 C dünyası AYNEN)"},
            "position_size_r": {"once": onceki["position_size_r"], "sonra": BOYUT_R,
                                "yuzey": "strateji params sözlüğü — TABAN (026 C dünyası AYNEN)"},
        },
        "cikis_enjeksiyon": {
            "harita_mutlak": HARITA, "touched_keys": touched_keys,
            "yuvarlama_beyani": YUVARLAMA_BEYANI,
            "yuzey": ("params_by_regime derin-kopya sözlük girdisi → config.resolve_params "
                      "(backtest.py::replay, motorun KENDİ rejim-koşullu çözüm noktası; rejim = o "
                      "GÜNÜN KAPANIŞ rejimi rj['regime']) → eff → strategy.manage_position "
                      "(exit.trail_atr_mult/time_stop_days/breakeven_r — REGIME_EXIT_KEYS izniyle "
                      "flat params'ta OLMASA da uygulanır). MONKEYPATCH GEREKMEDİ — motor yamasız; "
                      "beyan modül başlığında"),
            "orijinal_params_by_regime_bos": True,
        },
        "cikis_oz_sinama": {
            "1_cozum_ve_yuzey": oz1,
            "2_manage_position_ihlal": {"n": len(_carpan_ihlal), "ornek": [x for x in _carpan_ihlal[:20] if x]},
            "zaman_stop_kanit_rejim": zs_ozet,
        },
        "motor_sha256_16": {f: _sha(REPO / "meridian" / f)
                            for f in ("broker.py", "backtest.py", "strategy.py", "regime.py",
                                      "guard.py", "score.py", "config.py")},
        "config_sha256_16": {f: {"sandbox": _sha(st_dir / f), "edg022": _sha(EDG022 / "state" / f)}
                             for f in ("goal.yaml", "strategy.yaml", "bounds.yaml")},
        "bar_onbellek_ozet": _bar_cache_ozet(st_dir / "bars"),   # EDG-073 kill-2: KOŞUMUN KENDİSİ kaydeder (post-hoc tahmin değil)
        "replay": {"start": r_start, "end": r_end, "strategy_version": sv,
                   "params_by_regime": bool(by_regime_inj), "n_sembol": len(bars),
                   "n_endeks_satir": int(len(index)), "max_open": max_open,
                   "no_trade_before": no_trade_before,
                   "cost_model": {"slippage_bps": float(goal.get("slippage_bps", 5)),
                                  "commission_per_share": float(goal.get("commission_per_share", 0.0))}},
        "butunluk": {
            "frame_okunamadi": _frame_miss[0], "tekrar_tarih": _dup,
            "scan_vs_plan_uyusmazlik_n": len(scan_vs_plan), "scan_vs_plan_ornek": scan_vs_plan[:10],
            "yasakli_modul_yuklendi": yasak_yuklu, "base_max_open_bozuk": base_max_bozuk[:10],
            "gecerli": butunluk_gecerli,
        },
        "islem": {
            "n": n_islem, "islem_yil": round(n_islem / yil, 2), "aylik_ts_open": dict(sorted(aylik.items())),
            "silahlanan_plan": sum(plan_silahli.values()), "toplam_plan": sum(plan_aday.values()),
            "verdict_dagilim": verdict_n, "nogo_neden_dagilim": _neden_dagit(nogo_nedenler),
            "review_neden_dagilim": _neden_dagit(review_nedenler),
            "silahli_plan_size_r": {"min": round(min(silahli_size_r), 3) if silahli_size_r else None,
                                    "max": round(max(silahli_size_r), 3) if silahli_size_r else None,
                                    "ort": round(sum(silahli_size_r) / len(silahli_size_r), 3)
                                    if silahli_size_r else None},
            "entry_rejects": res.entry_rejects, "exit_reason_dagilim": dict(sorted(exit_dist.items(), key=lambda kv: -kv[1])),
        },
        "performans": {
            "net_pnl_equity": net_pnl_equity, "net_pnl_trades": net_pnl_trades,
            "maxdd_kanonik": detail.get("max_drawdown"), "maxdd_m2m": maxdd_m2m,
            "avg_r": detail.get("avg_r"), "win_rate": detail.get("win_rate"),
            "sharpe": detail.get("sharpe"), "sharpe_measurable": detail.get("sharpe_measurable"),
            "score": detail.get("score"), "score_n": detail.get("n"), "total_return": detail.get("total_return"),
        },
        "doluluk": {"pozisyon_gun_open_fazi": doluluk_pozgun,
                    "ort_acik_pozisyon": round(doluluk_pozgun / n_all, 3) if n_all else None,
                    "doluluk_orani_slot": round(doluluk_pozgun / n_all / SLOT, 4) if n_all else None,
                    "toplam_bars_held": doluluk_barsheld},
        "tepe_isi": isi, "isi_rejim_kirilimi": _isi_rejim_kirilimi(sess),
        "betim": {"n_seans": n_all,
                  "dd_gt_tam_esik_n": sum(1 for r in sess if r["dd"] > RAMPA["tam_dd"]),
                  "eff_max_open_eq0_n": sum(1 for r in sess if r["eff_max_open"] == 0),
                  "eff_max_open_eq1_n": sum(1 for r in sess if r["eff_max_open"] == 1),
                  "eff_max_open_lt_base_n": sum(1 for r in sess if r["eff_max_open"] < max_open),
                  "acik_slot_le0_n": sum(1 for r in sess if r["acik_slot"] <= 0),
                  "size_mult_0_n": sum(1 for r in sess if r["size_mult"] <= 0.0)},
        "tasnif_tum_seans": {"n": n_all, "dagilim": yuzde(dagit(sess), n_all)},
        "birincil": {"n": n_bir, "dagilim": yuzde(dagit(birincil), n_bir) if n_bir else {},
                     "tavan_sifir_pct": round(100.0 * sum(1 for r in birincil if r["sinif"] == "tavan_sifir")
                                              / n_bir, 2) if n_bir else None},
        "ci95_ay_kumeli": ci,
    }

    (outdir / f"sonuc_{hucre}{('' if pencere == 'tam' else '_' + pencere)}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True, default=str))
    (outdir / f"seanslar_{hucre}{('' if pencere == 'tam' else '_' + pencere)}.json").write_text(
        json.dumps(sess, ensure_ascii=False, sort_keys=True, default=str))
    slim = [{k: t.get(k) for k in ("ts_open", "ts_close", "ticker", "r_multiple", "pnl_dollars",
                                   "exit_reason", "bars_held", "regime", "setup", "qty",
                                   "risk_dollars", "size_r")} for t in trades]
    (outdir / f"islemler_{hucre}{('' if pencere == 'tam' else '_' + pencere)}.json").write_text(
        json.dumps(slim, ensure_ascii=False, sort_keys=True, default=str))

    print(f"\n=========== EDG-072 KOŞUM [{hucre}_{HUCRE_TRIAL_ID[hucre]} / {pencere}] ===========")
    print(f"replay {r_start}→{r_end}  sv={sv}  sembol={len(bars)}  süre={sure}s")
    print(f"harita={HARITA}")
    print(f"bütünlük geçerli={out['butunluk']['gecerli']}  frame_miss={_frame_miss[0]} dup={len(_dup)} "
          f"scan!=plan={len(scan_vs_plan)} yasak={yasak_yuklu} base_max_bozuk={len(base_max_bozuk)} "
          f"manage_ihlal={len(_carpan_ihlal)}")
    print(f"işlem n={n_islem} ({out['islem']['islem_yil']}/yıl)  net_pnl={net_pnl_equity}  "
          f"maxdd_kanonik={detail.get('max_drawdown')}  avg_r={detail.get('avg_r')}  sharpe={detail.get('sharpe')}")
    print(f"zaman_stop kanıtı (rejim): {zs_ozet}")
    print(f"yazıldı: {outdir}/sonuc_{hucre}{('' if pencere == 'tam' else '_' + pencere)}.json")
    print(f"KOSUM_{hucre.upper()}_{pencere.upper()}_BITTI")
    return out


# ---------------------------------------------------------------------------------------------
# SMOKE — kontrol_smoke + EDG-026 smoke C İLE BİT-ÖZDEŞLİK (kill#1, kart pozitif_kontrol parça-1)
# ---------------------------------------------------------------------------------------------
def smoke():
    out_k = kosum("kontrol", pencere="smoke")

    yerel = SANDBOX / "smoke"
    c_dir = EDG026 / "smoke"
    dosya_kiyas = {}
    for ad in ("seanslar", "islemler"):
        benim = _sha_full(yerel / f"{ad}_kontrol_smoke.json")
        c = _sha_full(c_dir / f"{ad}_c_smoke.json")
        dosya_kiyas[ad] = {"kontrol_sha256": benim, "c_sha256": c, "bayt_ayni": (benim is not None and benim == c)}

    sk = json.loads((yerel / "sonuc_kontrol_smoke.json").read_text())
    sc = json.loads((c_dir / "sonuc_c_smoke.json").read_text())
    bolum_kiyas = {}
    for b in BIT_BOLUMLER:
        bolum_kiyas[b] = (sk.get(b) == sc.get(b))

    bit_ozdes = all(v["bayt_ayni"] for v in dosya_kiyas.values()) and all(bolum_kiyas.values())
    out = {
        "kart": "EDG-2026-072", "kontrol": "override_bos_smoke_bit_ozdeslik",
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "tanim": ("kill-list (kart): kontrol bit-özdeşliği düşerse ölçüm GEÇERSİZ. Boş "
                  "params_by_regime smoke koşumu EDG-026 smoke C çıktılarıyla — seanslar+islemler "
                  f"BAYT-AYNI (sha256) ve sonuc ekonomik bölümleri {list(BIT_BOLUMLER)} sözlük-eşit. "
                  "NOT: bu pencerede (2022-01→2022-06) SIFIR chop işlemi var — yalnız ŞASİ kimliği "
                  "kanıtı, PK'nin chop-mekanizma parçası `duman()`da (chop popülasyonu taşıyan pencere)."),
        "dosya_bayt_kiyasi": dosya_kiyas, "sonuc_bolum_esitligi": bolum_kiyas, "bit_ozdes": bit_ozdes,
        "kill_tetiklendi": not bit_ozdes,
    }
    (yerel / "kontrol_bit_ozdeslik.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True, default=str))
    print(f"\n=========== EDG-072 SMOKE BİT-ÖZDEŞLİK ===========")
    print(f"dosya bayt-aynı: { {k: v['bayt_ayni'] for k, v in dosya_kiyas.items()} }")
    print(f"sonuc bölüm eşitliği: {bolum_kiyas}")
    print(f"bit_ozdes={bit_ozdes}  kill tetiklendi={not bit_ozdes}")
    print(f"yazıldı: {yerel/'kontrol_bit_ozdeslik.json'}")
    print("SMOKE_PASS" if bit_ozdes else "SMOKE_FAIL")
    return out


# ---------------------------------------------------------------------------------------------
# DUMAN — kontrol_duman + h1_duman + pk_duman (mekanizma sanity + PK), KISA pencere, ÖN PLAN (D7)
# ---------------------------------------------------------------------------------------------
def duman():
    import statistics
    out_kontrol = kosum("kontrol", pencere="duman")
    out_h1 = kosum("h1", pencere="duman")
    out_pk = kosum("pk", pencere="duman")

    def _chop_bars(sonuc_hucre_json_path: pathlib.Path) -> list[int]:
        islemler = json.loads(sonuc_hucre_json_path.read_text())
        return [int(t["bars_held"]) for t in islemler if str(t.get("regime")) == "chop"]

    yerel = SANDBOX / "duman"
    bh_kontrol = _chop_bars(yerel / "islemler_kontrol_duman.json")
    bh_h1 = _chop_bars(yerel / "islemler_h1_duman.json")
    bh_pk = _chop_bars(yerel / "islemler_pk_duman.json")

    def _ozet(v: list[int]) -> dict | None:
        if not v:
            return None
        return {"n": len(v), "min": min(v), "max": max(v), "medyan": statistics.median(v),
               "ort": round(sum(v) / len(v), 3)}

    pk_dustu = (bool(bh_kontrol) and bool(bh_pk)
               and statistics.median(bh_pk) < statistics.median(bh_kontrol)
               and max(bh_pk) <= max(1, max(bh_kontrol)))
    mekanizma_farkli = (out_kontrol["islem"]["n"] != out_h1["islem"]["n"]
                        or out_kontrol["performans"]["net_pnl_trades"] != out_h1["performans"]["net_pnl_trades"])

    out = {
        "kart": "EDG-2026-072", "adim": "duman", "pencere": [REPLAY_START, DUMAN_END],
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "not": ("D7: kısa-pencereli mekanizma sanity (kontrol vs h1) + kart pozitif_kontrol "
                "(sentetik chop time_stop_days=1, kontrol vs pk) — HÜKÜM DEĞİL, yalnız mekanizma. "
                "Resmî hüküm TAM pencere üç koşumdan (nohup) sonra `kiyasla()`."),
        "mekanizma_kontrol_vs_h1": {
            "kontrol_islem_n": out_kontrol["islem"]["n"], "h1_islem_n": out_h1["islem"]["n"],
            "kontrol_net_pnl": out_kontrol["performans"]["net_pnl_trades"],
            "h1_net_pnl": out_h1["performans"]["net_pnl_trades"],
            "farkli_defter": mekanizma_farkli,
            "manage_ihlal_kontrol": out_kontrol["cikis_oz_sinama"]["2_manage_position_ihlal"]["n"],
            "manage_ihlal_h1": out_h1["cikis_oz_sinama"]["2_manage_position_ihlal"]["n"],
        },
        "pozitif_kontrol_chop_time_stop_1": {
            "chop_bars_held_kontrol": _ozet(bh_kontrol), "chop_bars_held_pk": _ozet(bh_pk),
            "manage_ihlal_pk": out_pk["cikis_oz_sinama"]["2_manage_position_ihlal"]["n"],
            "zaman_stop_kanit_chop_pk": out_pk["cikis_oz_sinama"]["zaman_stop_kanit_rejim"].get("chop"),
            "olculebilir_dustu": pk_dustu,
            "beyan": ("chop{exit.time_stop_days=1} altında time_stop ateşleyen HER chop işlemi "
                      "bars_held>=1 eşiğini karşılamalı (esigi_karsilamayan_n==0 beklenir) VE chop "
                      "bars_held medyanı kontrole göre AÇIKÇA düşmeli — override'ın "
                      "resolve_params→manage_position zincirine GERÇEKTEN ulaştığının kanıtı "
                      "(config.py şerhi: 'sessizce düşen override' sınıfı bu PK ile dışlanır)"),
        },
        "pk_gecti": (pk_dustu and out_pk["cikis_oz_sinama"]["2_manage_position_ihlal"]["n"] == 0
                    and (out_pk["cikis_oz_sinama"]["zaman_stop_kanit_rejim"].get("chop") or {})
                    .get("esigi_karsilamayan_n") == 0),
    }
    (SANDBOX / "duman_ozet.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True, default=str))
    print(f"\n=========== EDG-072 DUMAN ÖZETİ ===========")
    print(f"mekanizma (kontrol vs h1) farklı_defter={mekanizma_farkli}")
    print(f"chop bars_held  kontrol={_ozet(bh_kontrol)}  pk={_ozet(bh_pk)}")
    print(f"PK geçti={out['pk_gecti']}")
    print(f"yazıldı: {SANDBOX/'duman_ozet.json'}")
    print("DUMAN_PK_GECTI" if out["pk_gecti"] else "DUMAN_PK_BASARISIZ")
    return out


# ---------------------------------------------------------------------------------------------
# ORTAK ÇEKİRDEK — eşlenik ay-kümeli bootstrap + rejim karnesi + saf-çıkış ayrışımı (tek-kaynak
# yasası: EDG-072 VE EDG-073 AYNI matematiği kullanır; kartlar arasında yalnız K'nin KAYNAĞI
# [eski dondurulmuş C ya da TAZE kontrol] ve boot_seed çağırana göre değişir — kod TEK yerde).
# ---------------------------------------------------------------------------------------------
def _kok_baz(kok: str) -> tuple[pathlib.Path, str]:
    if kok == "tam":
        return SANDBOX, ""
    if kok in ("duman", "smoke"):
        return SANDBOX / kok, f"_{kok}"
    raise ValueError(f"kok tanımsız: {kok} (tam|duman|smoke)")


def _yukle_uclu(base: pathlib.Path, hucre: str, suffix: str = "") -> dict | None:
    yollar = {ad: base / f"{ad}_{hucre}{suffix}.json" for ad in ("sonuc", "seanslar", "islemler")}
    if not all(p.exists() for p in yollar.values()):
        return None
    return {"sonuc": json.loads(yollar["sonuc"].read_text()),
           "seans": json.loads(yollar["seanslar"].read_text()),
           "islem": json.loads(yollar["islemler"].read_text())}


def _hucre_karsilastir(K: dict, hucre: str, E: dict, aylar: list[str], M: int,
                       pencere_gun: int, boot_seed: int,
                       dd_katsayi: float = DD_KOSUL_KATSAYI) -> dict:
    """K (taban üçlüsü: sonuc/seans/islem) ile E (hücre üçlüsü) arasında eşlenik ay-kümeli
    bootstrap + rejim karnesi + saf-çıkış ayrışımı + başarı-koşulu kaydı. EDG-072 (K=eski
    dondurulmuş C ya da taze kontrol) VE EDG-073 (K=taze kontrol, boot_seed=BOOT_SEED_073) bu
    ÇEKİRDEĞİ PAYLAŞIR — matematik ayrışmasın diye tek yerde."""
    import numpy as np
    sys.path.insert(0, str(REPO))
    from meridian import score as score_mod

    se = E["sonuc"]

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
        return {"lo": round(float(np.percentile(a, 2.5)), 4), "hi": round(float(np.percentile(a, 97.5)), 4),
                "orta": round(float(np.median(a)), 4)}

    def iter_metrikler(gr, pick):
        ts: list[dict] = []
        for j in sorted(pick):
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

    grK, grE = ay_grup(K["islem"]), ay_grup(E["islem"])
    rng = np.random.default_rng(boot_seed)
    idx_all = np.arange(M)
    d_n = np.empty(BOOT_ITER)
    d_pnl = np.empty(BOOT_ITER)
    d_sh: list[float] = []
    d_dd: list[float] = []
    sh_atlanan = dd_atlanan = 0
    for i in range(BOOT_ITER):
        pick = rng.choice(idx_all, size=M, replace=True)
        nK_i, pK_i, shK_i, ddK_i = iter_metrikler(grK, pick)
        nE_i, pE_i, shE_i, ddE_i = iter_metrikler(grE, pick)
        d_n[i] = nE_i - nK_i
        d_pnl[i] = pE_i - pK_i
        if shK_i == shK_i and shE_i == shE_i:
            d_sh.append(shE_i - shK_i)
        else:
            sh_atlanan += 1
        if ddK_i == ddK_i and ddE_i == ddE_i:
            d_dd.append(ddE_i - ddK_i)
        else:
            dd_atlanan += 1

    nK, nE = len(K["islem"]), len(E["islem"])
    pnl_ci = ci95(d_pnl)
    fark_ci = ci95(d_n)
    sh_ci = ci95(d_sh)
    dd_ci = ci95(d_dd)

    def rejim_karne(ts: list[dict]) -> dict:
        reg: dict[str, dict] = {}
        for t in ts:
            g = reg.setdefault(str(t.get("regime")), {"n": 0, "r_toplam": 0.0, "pnl": 0.0, "kazanan": 0})
            g["n"] += 1
            g["r_toplam"] += float(t.get("r_multiple") or 0.0)
            g["pnl"] += float(t.get("pnl_dollars") or 0.0)
            if float(t.get("r_multiple") or 0.0) > 0:
                g["kazanan"] += 1
        out_k = {}
        for rg, g in sorted(reg.items(), key=lambda kv: -kv[1]["n"]):
            rs = [float(t.get("r_multiple") or 0.0) for t in ts if str(t.get("regime")) == rg]
            out_k[rg] = {"n": g["n"], "ort_r": round(g["r_toplam"] / g["n"], 3),
                         "medyan_r": round(float(np.median(rs)), 3), "pnl": round(g["pnl"], 2),
                         "kazanma_orani": round(g["kazanan"] / g["n"], 3)}
        return out_k

    karne_k, karne_e = rejim_karne(K["islem"]), rejim_karne(E["islem"])
    karne_delta = {}
    for rg in sorted(set(karne_k) | set(karne_e)):
        a0, b0 = karne_k.get(rg), karne_e.get(rg)
        karne_delta[rg] = {"d_n": (b0["n"] if b0 else 0) - (a0["n"] if a0 else 0),
                           "d_pnl": round((b0["pnl"] if b0 else 0.0) - (a0["pnl"] if a0 else 0.0), 2)}

    K_kimlik = {(str(t["ts_open"])[:10], t["ticker"]) for t in K["islem"]}
    E_kimlik = {(str(t["ts_open"])[:10], t["ticker"]) for t in E["islem"]}
    K_by = {(str(t["ts_open"])[:10], t["ticker"]): t for t in K["islem"]}
    E_by = {(str(t["ts_open"])[:10], t["ticker"]): t for t in E["islem"]}
    eklenen_k = sorted(E_kimlik - K_kimlik)
    cikan_k = sorted(K_kimlik - E_kimlik)
    ortak_k = sorted(K_kimlik & E_kimlik)
    eklenen = [E_by[k] for k in eklenen_k]
    cikan = [K_by[k] for k in cikan_k]

    kova = {"ayni_trend_up": {"n": 0, "d_pnl": 0.0}, "ayni_chop": {"n": 0, "d_pnl": 0.0},
           "ayni_diger": {"n": 0, "d_pnl": 0.0}, "kayan": {"n": 0, "d_pnl": 0.0}}
    for k in ortak_k:
        a, b = K_by[k], E_by[k]
        dpnl = float(b.get("pnl_dollars", 0.0)) - float(a.get("pnl_dollars", 0.0))
        yol_ayni = (str(a.get("ts_close"))[:10] == str(b.get("ts_close"))[:10]
                   and a.get("exit_reason") == b.get("exit_reason")
                   and abs(float(a.get("r_multiple") or 0) - float(b.get("r_multiple") or 0)) <= 1e-9)
        if not yol_ayni:
            kova["kayan"]["n"] += 1
            kova["kayan"]["d_pnl"] += dpnl
        else:
            rg = str(b.get("regime"))
            ad = "ayni_trend_up" if rg == "trend_up" else ("ayni_chop" if rg == "chop" else "ayni_diger")
            kova[ad]["n"] += 1
            kova[ad]["d_pnl"] += dpnl

    ekl_pnl = round(sum(float(t.get("pnl_dollars") or 0.0) for t in eklenen), 2)
    cik_pnl = round(sum(float(t.get("pnl_dollars") or 0.0) for t in cikan), 2)
    ortak_dpnl = sum(v["d_pnl"] for v in kova.values())
    d_pnl_nokta = round(float(se["performans"].get("net_pnl_trades") or 0)
                        - float(K["sonuc"]["performans"].get("net_pnl_trades") or 0), 2)
    kalinti = round(d_pnl_nokta - (ekl_pnl + round(ortak_dpnl, 2) - cik_pnl), 2)

    ddk = K["sonuc"]["performans"].get("maxdd_kanonik")
    dde = se["performans"].get("maxdd_kanonik")
    basari_kosulu = {
        "not": "HÜKÜM GİRDİSİ (kart success_metric) — kill değil; hüküm Rol-1'in",
        "d_pnl_ci_alt": (pnl_ci or {}).get("lo"),
        "d_pnl_ci_alt_pozitif": ((pnl_ci or {}).get("lo") is not None and (pnl_ci or {}).get("lo") > 0),
        "maxdd_kontrol": ddk, "maxdd_hucre": dde,
        "dd_oran": round(dde / ddk, 3) if (ddk not in (None, 0) and dde is not None) else None,
        "dd_kontrol_x1p3_icinde": (dde <= dd_katsayi * ddk) if (ddk not in (None, 0) and dde is not None) else None,
    }

    return {
        "hucre": hucre, "harita_mutlak": se["cikis_enjeksiyon"]["harita_mutlak"], "boot_seed": boot_seed,
        "tablo": {
            "islem_n": {"kontrol": nK, hucre: nE, "fark": nE - nK,
                        "fark_pct": round(100.0 * (nE - nK) / nK, 1) if nK else None},
            "islem_fark_ci95": fark_ci,
            "net_pnl_trades": {"kontrol": K["sonuc"]["performans"]["net_pnl_trades"],
                               hucre: se["performans"]["net_pnl_trades"]},
            "net_pnl_fark_ci95": pnl_ci,
            "maxdd_kanonik": {"kontrol": ddk, hucre: dde},
            "maxdd_fark_ci95_kapali_islem_egrisi": dd_ci, "maxdd_ci_atlanan_iter": dd_atlanan,
            "sharpe": {"kontrol": K["sonuc"]["performans"]["sharpe"], hucre: se["performans"]["sharpe"]},
            "sharpe_fark_ci95": sh_ci, "sharpe_ci_atlanan_iter": sh_atlanan,
        },
        "rejim_karne": {"kontrol": karne_k, hucre: karne_e, "delta": karne_delta},
        "saf_cikis_ayrisimi": {
            "kimlik": "(ts_open[:10], ticker); yol-aynı = ts_close+exit_reason aynı ∧ |Δr|≤1e-9",
            "ortak_n": len(ortak_k), "eklenen_n": len(eklenen), "cikan_n": len(cikan),
            "kovalar": {k: {"n": v["n"], "d_pnl": round(v["d_pnl"], 2)} for k, v in kova.items()},
            "eklenen_pnl": ekl_pnl, "cikan_pnl": cik_pnl,
            "pnl_kimligi": {"delta_net_pnl_trades": d_pnl_nokta, "ortak_delta_pnl": round(ortak_dpnl, 2),
                           "kalinti": kalinti, "sente_kapandi": abs(kalinti) <= 0.01},
        },
        "basari_kosulu_kaydi": basari_kosulu,
    }


# ---------------------------------------------------------------------------------------------
# EDG-072 — h1/h2 vs TAM kontrol, KILL_D3 = kontrol↔eski-C bit-özdeşliği (şasi bayatlığı yüzünden
# 2026-09-04 itibariyle YAPISAL OLARAK düşük olasılıkla geçer — bkz. rapor §3; kart bu R1 ile
# "kaldı — şasi bayatlığı, kriter yerinde düzeltilmedi" olarak kapandı, EDG-073 R2'ye devredildi.
# Bu fonksiyon AYRICA raporlanmaya devam eder, EDG-073 hükmüne KARIŞMAZ.)
# ---------------------------------------------------------------------------------------------
def kiyasla_072(kok: str = "tam") -> dict:
    if kok != "tam":
        return {"kart": "EDG-2026-072",
                "olculemedi": f"kok={kok} — EDG-072 C-kıyası yalnız TAM pencerede anlamlı (eski C yalnız tam-pencere donmuş defter taşır)"}

    gerekli = {
        "kontrol": ("sonuc_kontrol.json", "seanslar_kontrol.json", "islemler_kontrol.json"),
        "h1": ("sonuc_h1.json", "seanslar_h1.json", "islemler_h1.json"),
        "h2": ("sonuc_h2.json", "seanslar_h2.json", "islemler_h2.json"),
    }
    eksik = [f for files in gerekli.values() for f in files if not (SANDBOX / f).exists()]
    if eksik:
        return {"kart": "EDG-2026-072",
                "olculemedi": f"TAM koşum çıktıları eksik (nohup henüz bitmemiş olabilir) — eksik: {eksik}"}

    K = _yukle_uclu(SANDBOX, "kontrol")
    C = {"sonuc": json.loads((EDG026 / "sonuc_c.json").read_text()),
        "seans": json.loads((EDG026 / "seanslar_c.json").read_text()),
        "islem": json.loads((EDG026 / "islemler_c.json").read_text())}

    # ---- D3: kontrol (TAM) C ile BİT-ÖZDEŞ mi (işlem listesi sha eşit) — kill ----------------
    k_islem_sha = hashlib.sha256(json.dumps(K["islem"], sort_keys=True, default=str).encode()).hexdigest()
    c_islem_sha = hashlib.sha256(json.dumps(C["islem"], sort_keys=True, default=str).encode()).hexdigest()
    k_seans_sha = hashlib.sha256(json.dumps(K["seans"], sort_keys=True, default=str).encode()).hexdigest()
    c_seans_sha = hashlib.sha256(json.dumps(C["seans"], sort_keys=True, default=str).encode()).hexdigest()
    bolum_kiyas = {b: (K["sonuc"].get(b) == C["sonuc"].get(b)) for b in BIT_BOLUMLER}
    kontrol_bit_ozdes = (k_islem_sha == c_islem_sha and k_seans_sha == c_seans_sha
                         and all(bolum_kiyas.values()))
    kill_d3 = {
        "esik": ("TAM kontrol koşumu C ile bit-özdeş DEĞİLSE ölçüm GEÇERSİZ (EDG-072 kill-list) — "
                "R1 KÖK NEDEN TEŞHİSİ (2026-09-04, rapor §3): resolve_params YAN ETKİLİ DEĞİL; "
                "EDG-026 C-şasisi 2026-08-12'de dondu, o günden bu yana meridian/ üzerinde 178 "
                "commit + bar önbelleğinin 24/260 dosyası yenilendi (şasi bayatlığı). §5 gereği "
                "kriter YERİNDE düzeltilmedi — EDG-072 bu bulguyla 'kaldı' kapandı, EDG-073 R2 "
                "TAZE-kontrol tabanıyla devraldı (bkz. kiyasla_073)."),
        "islem_sha_esit": k_islem_sha == c_islem_sha, "seans_sha_esit": k_seans_sha == c_seans_sha,
        "sonuc_bolum_esitligi": bolum_kiyas, "bit_ozdes": kontrol_bit_ozdes, "tetiklendi": not kontrol_bit_ozdes,
    }

    aylar = sorted({s["date"][:7] for s in K["seans"]})
    M = len(aylar)
    r_start, r_end = K["sonuc"]["replay"]["start"], K["sonuc"]["replay"]["end"]
    pencere_gun = (dt.date.fromisoformat(r_end) - dt.date.fromisoformat(r_start)).days

    if kontrol_bit_ozdes:
        hucre_sonuclari = {h: _hucre_karsilastir(K, h, _yukle_uclu(SANDBOX, h), aylar, M, pencere_gun, BOOT_SEED_072)
                           for h in ("h1", "h2")}
    else:
        hucre_sonuclari = {"not": "kontrol bit-özdeş DEĞİL — h1/h2 hesaplanmadı (kill-list: hiçbir sayı yayılmaz)"}

    return {
        "kart": "EDG-2026-072",
        "kiyas_taban": {"kaynak": "EDG-026 C (slot20+0.5R+rampa15/36) HAZIR çıktıları — salt-okundu",
                        "sha256": EDG026_SHA256},
        "kill_d3_kontrol_bit_ozdesligi": kill_d3,
        "hucreler": hucre_sonuclari,
        "hukum": None,
        "kart_durumu": "KALDI — şasi bayatlığı (§5, kriter yerinde düzeltilmedi); EDG-2026-073 R2 devraldı (Rol-1, 2026-09-04)",
    }


# ---------------------------------------------------------------------------------------------
# EDG-073 — R2: KIYAS TABANI = TAZE kontrol (eski C'ye HİÇ dokunmaz). Kill-1 = şasi sınaması
# (resolve_params(params,{},rejim) HER gözlenen rejim için params'la birebir eşit); kill-2 =
# üç koşumun motor+bar özdeşliği. Bootstrap seed = BOOT_SEED_073 (kart, donuk, 20260903).
# ---------------------------------------------------------------------------------------------
def sasi_sinamasi_073(gozlenen_rejimler: set[str]) -> dict:
    """073 kill-1: `resolve_params(params, {}, rejim)` HER gözlenen rejim etiketi için `params`
    ile birebir eşit mi (saf fonksiyon kanıtı) — EDG-072'nin 'C ile bit-özdeş' maddesinin
    ŞASİ-BAYATLIĞINDAN BAĞIMSIZ, ÖLÇÜLEBİLİR karşılığı (kart kill_list madde-1). `by_regime={}`
    (boş sözlük, falsy) verildiğinde `resolve_params`'ın KENDİ gövdesi `if by_regime:` dalına hiç
    girmez — yani bu sınama NORMAL ŞARTLARDA istisnasız geçer; asıl işlevi bir MUTASYONU (motoru
    ya da bu betiği yan-etkili bir sürüme değiştiren bir hata) YAKALAMAKTIR (v404 mutasyon çivisi)."""
    sys.path.insert(0, str(REPO))
    from meridian import config
    params = _taban_params()
    kayit = []
    tetiklendi = False
    for rg in sorted(gozlenen_rejimler):
        params_once = dict(params)
        eff = config.resolve_params(params, {}, rg)
        eff_esit = (eff == params)
        girdi_saglam = (params == params_once)
        if not (eff_esit and girdi_saglam):
            tetiklendi = True
        kayit.append({"rejim": rg, "eff_params_esit": eff_esit, "girdi_mutasyona_ugramadi": girdi_saglam})
    return {
        "esik": ("kart EDG-2026-073 kill-list madde-1: resolve_params(params,{},rejim) HER "
                "gözlenen rejim için params ile birebir eşit DEĞİLSE ölçüm GEÇERSİZ (yol yan-etkili)"),
        "gozlenen_rejimler": sorted(gozlenen_rejimler), "kayit": kayit,
        "tetiklendi": tetiklendi, "gecti": not tetiklendi,
    }


def kill2_motor_bar_073(K: dict, H1: dict | None, H2: dict | None, kontrol_log: pathlib.Path | None) -> dict:
    """073 kill-2: üç koşumun motor sha256 + bar önbelleği İÇERİK özeti AYNI mı. Motor: her
    koşum KENDİ execution'ında `motor_sha256_16`'yı zaten kaydetti (kosum() içinde — DOĞRUDAN
    kanıt, post-hoc tahmin DEĞİL) → üç kaydı doğrudan karşılaştırırız. Bar önbelleği: EDG-072'nin
    üç TAM koşumu (kosum_kontrol/h1/h2, 2026-09-04T11:47Z) `bar_onbellek_ozet` alanını TAŞIMIYORDU
    (bu tur EKLENDİ, ama süreçler zaten belleğe aldıkları ESKİ kodla koştu) → TEK post-hoc ölçüm +
    'koşum sırasında değişmedi' varsayımı AÇIKÇA beyan edilir (mtime kanıtıyla — kesin kanıt
    DEĞİL). Gelecekteki koşumlar `kosum()`'un artık kaydettiği alanı taşıyacak; bu fonksiyon o alan
    VARSA (üç kayıt da doluysa) post-hoc ölçümü ATLAR ve DOĞRUDAN kayıtları karşılaştırır."""
    motor_kayitlari: dict[str, dict | None] = {"kontrol": K["sonuc"].get("motor_sha256_16")}
    if H1 is not None:
        motor_kayitlari["h1"] = H1["sonuc"].get("motor_sha256_16")
    if H2 is not None:
        motor_kayitlari["h2"] = H2["sonuc"].get("motor_sha256_16")
    degerler = [v for v in motor_kayitlari.values() if v is not None]
    motor_ayni = len(degerler) >= 1 and all(v == degerler[0] for v in degerler)

    bar_kayitlari = {"kontrol": K["sonuc"].get("bar_onbellek_ozet")}
    if H1 is not None:
        bar_kayitlari["h1"] = H1["sonuc"].get("bar_onbellek_ozet")
    if H2 is not None:
        bar_kayitlari["h2"] = H2["sonuc"].get("bar_onbellek_ozet")
    bar_degerler = [v.get("birlesik_sha256") for v in bar_kayitlari.values() if v is not None]

    if len(bar_degerler) >= 1 and len(bar_degerler) == len(bar_kayitlari):
        # her üç koşum da KENDİ bar özetini kaydetmiş — DOĞRUDAN kıyas (post-hoc ölçüm gerekmez)
        bar_yontem = "DOGRUDAN (üç koşum da kendi bar_onbellek_ozet'ini kaydetti)"
        bar_ayni = all(v == bar_degerler[0] for v in bar_degerler)
        bar_once_donduruldu = None
        ozet = None
        baslangic_ts = None
    else:
        bar_yontem = ("POST-HOC (tek ölçüm, koşumlar bittikten SONRA) — bu üç koşumun kodu "
                     "bar-özet alanı taşımıyordu (yeni alan, bu turda kosum()'a eklendi); "
                     "'koşum sırasında değişmedi' VARSAYIMI, kesin kanıt DEĞİL")
        ozet = _bar_cache_ozet()
        baslangic_ts = _log_baslangic_ts(kontrol_log) if kontrol_log is not None else None
        bar_once_donduruldu = None
        if baslangic_ts is not None and ozet.get("en_yeni_mtime_utc") is not None:
            bar_once_donduruldu = ozet["en_yeni_mtime_utc"] <= baslangic_ts
        # ölçülemeyen (None) BLOKLAMAZ (kayıt edilir); yalnız AÇIKÇA ölçülmüş uyumsuzluk (False) bloklar
        bar_ayni = bar_once_donduruldu is not False

    tetiklendi = (motor_ayni is False) or (bar_ayni is False)
    return {
        "esik": "üç koşum aynı motor sha + aynı bar özeti taşımıyorsa GEÇERSİZ (kart kill-list madde-2)",
        "motor": {"kayitlar": motor_kayitlari, "her_kosum_KENDI_calisma_aninda_kaydetti": True, "ayni": motor_ayni},
        "bar_onbellek": {
            "olcum_yontemi": bar_yontem, "kayitlar": bar_kayitlari if bar_degerler else None,
            "post_hoc_ozet": ozet, "kosum_baslangic_ts_utc": baslangic_ts,
            "en_yeni_bar_dosyasi_kosumdan_once_mi": bar_once_donduruldu, "ayni_varsayilan": bar_ayni,
        },
        "tetiklendi": tetiklendi, "gecti": not tetiklendi,
    }


def adim0c_taze(K_islem: list[dict]) -> dict:
    """073 ADIM-0(c): TAZE kontrol defterinden rejim başına işlem sayısı (kart eşiği 30)."""
    n_rejim: dict[str, int] = {}
    for t in K_islem:
        rg = str(t.get("regime"))
        n_rejim[rg] = n_rejim.get(rg, 0) + 1
    out = {}
    for rg in REGIMES:
        n = n_rejim.get(rg, 0)
        out[rg] = {"n": n, "esik": KILL_TREND_UP_CHOP_MIN, "olculebilir": n >= KILL_TREND_UP_CHOP_MIN}
    return out


def kiyasla_073(kok: str = "tam") -> dict:
    base, suf = _kok_baz(kok)
    K = _yukle_uclu(base, "kontrol", suf)
    if K is None:
        return {"kart": "EDG-2026-073", "kok": kok,
                "olculemedi": f"TAZE kontrol çıktıları yok ({base}/*_kontrol{suf}.json) — nohup henüz bitmemiş olabilir"}

    gozlenen_rejimler = {str(s.get("regime")) for s in K["seans"] if s.get("regime") is not None}
    sasi = sasi_sinamasi_073(gozlenen_rejimler)

    kontrol_log = SANDBOX / "kosum_kontrol.log" if kok == "tam" else None
    H1 = _yukle_uclu(base, "h1", suf)
    H2 = _yukle_uclu(base, "h2", suf)
    k2 = kill2_motor_bar_073(K, H1, H2, kontrol_log)

    a0c = adim0c_taze(K["islem"])
    a0c_gecti = all(v["olculebilir"] for rg, v in a0c.items() if rg in ("trend_up", "chop"))

    genel_gecti = sasi["gecti"] and k2["gecti"] and a0c_gecti

    aylar = sorted({s["date"][:7] for s in K["seans"]})
    M = len(aylar)
    r_start, r_end = K["sonuc"]["replay"]["start"], K["sonuc"]["replay"]["end"]
    pencere_gun = (dt.date.fromisoformat(r_end) - dt.date.fromisoformat(r_start)).days

    if genel_gecti:
        hucre_sonuclari = {}
        for hucre, E in (("h1", H1), ("h2", H2)):
            if E is None:
                hucre_sonuclari[hucre] = {"olculemedi": f"{base}/sonuc_{hucre}{suf}.json yok"}
                continue
            hucre_sonuclari[hucre] = _hucre_karsilastir(K, hucre, E, aylar, M, pencere_gun, BOOT_SEED_073)
    else:
        hucre_sonuclari = {"not": "kill-1/kill-2/adım0(c)'ten biri tetiklendi — h1/h2 hesaplanmadı (kill-list: hiçbir sayı yayılmaz)"}

    return {
        "kart": "EDG-2026-073", "kok": kok, "kuru_deneme": kok != "tam",
        "kiyas_taban": {"kaynak": f"TAZE kontrol koşumu ({base}, kok={kok}) — AYNI motor+bar, eski C'ye HİÇ DOKUNMAZ",
                        "boot_seed": BOOT_SEED_073},
        "kill1_sasi_sinamasi": sasi,
        "kill2_motor_bar_ayniligi": k2,
        "adim0c_taze_rejim_n": a0c,
        "genel_gecerli": genel_gecti,
        "hucreler": hucre_sonuclari,
        "hukum": None,
    }


def kiyasla(kart: str = "EDG-2026-073", kok: str = "tam") -> dict:
    """CLI yüzeyi: `olcum.py kiyasla [--kart EDG-2026-072|EDG-2026-073] [--kok tam|duman]`.
    kart=EDG-2026-073 (varsayılan, R1 sonrası önerilen yol): edg073 (TAZE-kontrol tabanlı,
    kill-1/kill-2 kapılı) HESAPLANIR; kok=tam ise edg072 (eski-C kıyası, kill_d3 kapılı, AYRICA
    raporlanır — 073 hükmüne KARIŞMAZ) da eklenir; kok≠tam ise edg072 atlanır (eski C yalnız tam
    pencere taşır). kart=EDG-2026-072: yalnız edg072 (eski davranış, ayrı dosya adı)."""
    assert kart in ("EDG-2026-072", "EDG-2026-073"), f"kart tanımsız: {kart} (EDG-2026-072|EDG-2026-073)"
    assert kok in ("tam", "duman", "smoke"), f"kok tanımsız: {kok} (tam|duman|smoke)"
    bugun = dt.date.today().isoformat()

    if kart == "EDG-2026-072":
        payload = {"edg072": kiyasla_072(kok)}
        dosya_ad = f"sonuc_edg072_{bugun}.json" if kok == "tam" else f"sonuc_edg072_{bugun}_kuru_{kok}.json"
    else:
        edg073 = kiyasla_073(kok)
        edg072 = kiyasla_072(kok) if kok == "tam" else {
            "kart": "EDG-2026-072", "olculemedi": f"kok={kok} — bu çağrı kuru deneme, EDG-072 C-kıyası yalnız tam pencerede koşulur"}
        payload = {"edg072": edg072, "edg073": edg073}
        dosya_ad = f"sonuc_{bugun}.json" if kok == "tam" else f"sonuc_{bugun}_kuru_{kok}.json"

    out = {"modul": str(pathlib.Path(__file__).resolve()),
          "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
          "derleme_tarihi": bugun, "kart_istegi": kart, "kok": kok, **payload}
    (SANDBOX / dosya_ad).write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True, default=str))

    print(f"\n==================== KIYASLA ÖZETİ (kart={kart}, kok={kok}) ====================")
    # NOT: aşağıdaki özet baskısı KASITLI SAVUNMACI (.get(), doğrudan indeks DEĞİL) — hem gerçek
    # eksik-girdi ("olculemedi") gövdelerine hem test/stub gövdelerine karşı sağlam olsun diye;
    # tek gerçek kaynak yine `out`/`payload`dır, bu yalnız insan-okur bir özet.
    if "edg073" in payload:
        e73 = payload["edg073"]
        if "olculemedi" in e73:
            print(f"[EDG-073] olculemedi: {e73['olculemedi']}")
        elif "kill1_sasi_sinamasi" not in e73:
            print(f"[EDG-073] (özet alanları eksik — muhtemelen test/stub gövdesi): {e73}")
        else:
            print(f"[EDG-073] kill-1 şasi sınaması gecti={e73['kill1_sasi_sinamasi']['gecti']}  "
                  f"kill-2 motor/bar gecti={e73['kill2_motor_bar_ayniligi']['gecti']}  "
                  f"adım0c_gecti={all(v['olculebilir'] for rg, v in e73['adim0c_taze_rejim_n'].items() if rg in ('trend_up', 'chop'))}  "
                  f"genel_gecerli={e73['genel_gecerli']}")
            for h, hs in (e73.get("hucreler") or {}).items():
                if "tablo" not in hs:
                    print(f"  {h}: {hs}")
                    continue
                t = hs["tablo"]
                print(f"  --- {h} (harita={hs['harita_mutlak']}) ---")
                print(f"  işlem: kontrol {t['islem_n']['kontrol']} → {t['islem_n'][h]} (fark {t['islem_n']['fark']})")
                print(f"  net_pnl ΔCI95={t['net_pnl_fark_ci95']}  maxdd ΔCI95={t['maxdd_fark_ci95_kapali_islem_egrisi']}")
                print(f"  başarı kaydı: {hs['basari_kosulu_kaydi']}")
    if "edg072" in payload:
        e72 = payload["edg072"]
        if "olculemedi" in e72:
            print(f"[EDG-072] olculemedi: {e72['olculemedi']}")
        elif "kill_d3_kontrol_bit_ozdesligi" not in e72:
            print(f"[EDG-072] (özet alanları eksik — muhtemelen test/stub gövdesi): {e72}")
        else:
            print(f"[EDG-072] kill_d3 tetiklendi={e72['kill_d3_kontrol_bit_ozdesligi']['tetiklendi']}  kart_durumu={e72.get('kart_durumu')}")
    print(f"\nyazıldı: {SANDBOX/dosya_ad}")
    print("KIYASLA_BITTI")
    return out


_KULLANIM = ("kullanım: olcum.py {adim0 | oz_sinama | smoke | duman | "
            "kosum {kontrol|h1|h2} --tam | "
            "kiyasla [--kart EDG-2026-072|EDG-2026-073] [--kok tam|duman]}")


def _bayrak_degeri(argv: list[str], ad: str, varsayilan: str) -> str:
    if ad in argv:
        i = argv.index(ad)
        if i + 1 < len(argv):
            return argv[i + 1]
    return varsayilan


if __name__ == "__main__":
    argv = sys.argv[1:]
    if not argv:
        sys.exit(_KULLANIM)
    cmd = argv[0]
    if cmd == "adim0":
        ok = adim0()
        sys.exit(0 if ok else 1)
    elif cmd == "oz_sinama":
        r = oz_sinama_calistir()
        sys.exit(0 if r["hepsi_gecti"] else 1)
    elif cmd == "smoke":
        r = smoke()
        sys.exit(0 if r["bit_ozdes"] else 1)
    elif cmd == "duman":
        r = duman()
        sys.exit(0 if r["pk_gecti"] else 1)
    elif cmd == "kosum" and len(argv) > 1 and argv[1] in ("kontrol", "h1", "h2"):
        pencere = "duman" if "--duman" in argv else ("smoke" if "--smoke" in argv else "tam")
        kosum(argv[1], pencere=pencere)
    elif cmd == "kiyasla":
        kart = _bayrak_degeri(argv, "--kart", "EDG-2026-073")
        kok = _bayrak_degeri(argv, "--kok", "tam")
        kiyasla(kart=kart, kok=kok)
    else:
        sys.exit(_KULLANIM)

"""EDG-2026-024 — EŞİK RETRO KANIT · ölçüm aracı (2026-08-12)

Kart: research/cards/EDG-2026-024-esik-retro-kanit.yaml (OKU-DOKUNMA; hüküm Rol-1'in).
Rol: ÖLÇÜM ajanı. Bu modül HÜKÜM VERMEZ, karta dokunmaz, git/canlı/broker/state'e YAZMAZ.

SORU (karttan): giriş eşikleri ILIMLI gevşeseydi (hacim 1.5→1.25 · RS 70→65 — operatör seçimi
2026-08-12, tek kademe) TABANA GÖRE EKLENEN işlemlerin GERÇEK-yasalı R'si ne olurdu — hangi eşik
masada para bırakıyor: hacim mi, RS mi, ikisi mi?

DÖRT KOŞUM (kart AYNEN; K yalnız 3 gevşek hücre için artar, taban tutarlılık çivisidir):
    (0) taban      mevcut eşikler (kill#3 tutarlılık çivisi)
    (1) hacim_125  entry.min_volume_ratio 1.5→1.25 (RS 70 SABİT)
    (2) rs_65      entry.rs_rating_min    70→65    (hacim 1.5 SABİT)
    (3) ikisi      1.25 + 65

PARAM ENJEKSİYONU: yalnız strategy.yaml param SÖZLÜĞÜNÜN kopyası hücrede değişir; motor YAMASIZ —
bu modül HİÇBİR meridian fonksiyonunu sarmalamaz/değiştirmez (EDG-022'nin kancaları burada GEREKMEZ:
ihtiyaç duyulan her şey — trades/plan_log/equity — BacktestResult dönüşünde zaten var). Eşikleri
tüketen yol motorun kendisidir: entry.min_volume_ratio YALNIZ evaluate_entry (breakout_vcp,
strategy.py:377); entry.rs_rating_min TÜM kurulumlar (silahlı üçlüde: breakout_vcp:375,
pullback:543, exhaustion_hammer:748). guard.py bu iki anahtarı OKUMAZ (grep-doğrulandı) — eşik
etkisi tamamen tarama katmanında.

EKLENEN-İŞLEM TANIMI (diff yasası): işlem kimliği plan_id (P-YYYY-AA-GG-TICKER, motor şeması).
    eklenen = hücre defterinde olup TABAN defterinde olmayan plan_id'ler
    çıkan   = taban defterinde olup hücre defterinde olmayanlar (kaskad dürüstlüğü: gevşek eşik
              portföy durumunu değiştirir → bazı taban işlemleri kaybolabilir; SAKLANMAZ, raporlanır)
    ortak   = iki defterde de olan plan_id'ler (kaskad P&L kayması ayrıca raporlanır)
Eklenen işlemlerin R'si HÜCRE koşumunun kendi defterinden okunur — motorun kendi çıkış yasalarıyla
tam replay (cf DEĞİL; kartın "GERÇEK-R" şartı). Net P&L farkı TAM-defter farkıdır (kaskad dahil):
sum(pnl hücre) − sum(pnl taban); dekompozisyon (eklenen − çıkan + ortak-kayma) aritmetik olarak
doğrulanır ve raporlanır.

KILL'LER (kart, DONUK):
    kill#2: hücrede eklenen < 15 → o hücre `olculemedi` (CI anlamsız — hesaplanmaz, None + neden)
    kill#3: taban koşum mevcut canlı/022 davranışını yeniden üretemezse ölçüm geçersiz.
        Operasyonalizasyon (bu modül olguları ölçer, hükmü Rol-1 verir):
        (a) ŞASİ = EDG-022: evren 251 sembol · seans takvimi 022 seanslar.json ile BİREBİR
            (1147 tarih) · max_open=5 · no_trade_before=3 · params 022 koşumunun params'ına eşit.
        (b) CANLI DAVRANIŞ = bu ağacın motoru, SIFIR yama, canlı state/strategy.yaml params'ı
            (sha256 eşitliği kayıtta). MOTOR 022 KOŞUMUNDAN SONRA DEĞİŞTİ (beyan, tarihçe-koru):
            de47ea2/v233 (2026-08-12) exhaustion_hammer OPERATÖR ONAYIYLA silahlandı;
            becb03b/v236 broker birikim sent-yuvarlaması. Bu yüzden taban, 022 kaydıyla
            İŞLEM-DÜZEYİ bit-özdeş OLAMAZ ve bunu beklemek yanlış çivi olurdu: kartın "mevcut
            canlı" dediği şey BUGÜNKÜ motordur. Kısmi güç-testi yine de yapılır: tarih-başına
            plan sayısı 022 kaydıyla İLK SAPMA gününe kadar karşılaştırılır ve ilk sapmanın
            hammer-kaynaklı olup olmadığı raporlanır.
    (kill#1 kartta bir HÜKÜM kuralıdır — üç hücrede CI-0-üstü yoksa eşikler doğrulanmış olur;
     bu modül yalnız CI olgularını üretir.)

MALİYET (kart: pessimistic_band_v2): birincil R'ler motorun KENDİ maliyetiyle (goal.yaml
slippage_bps=5/bacak, komisyon 0 — dolum fiyatının İÇİNDE). Kötümser bant goal.yaml
pessimistic_band_v2 bloğundan: açılış efektif spread 20bps → tek yön 10bps; mevcut model tek yön
5bps → EK maliyet 5bps/bacak = 0.0005·qty·(entry+exit) işlem başına. Eklenen kümenin CI'sı iki
maliyette de raporlanır (pozitif bir hüküm kötümser bandı da aşmalı — s1_retro emsali).

İSTATİSTİK: tarih-KÜMELİ bootstrap %95 CI (EDG-022 emsali): küme = ts_open takvim ayı; aylar
yerine-koymalı çekilir, çekilen ayların işlemleri havuzlanır, ortalama R dağılımından yüzdelik
2.5/97.5. Bitişik günlerin işlemleri bağımlıdır (rejim epizodları); iid işlem çekmek CI'yi
sahte-daraltırdı. Küme sayısı < 2 ise CI `olculemedi` (tek kümeden bootstrap dejenere).

DİSİPLİN: UYDURMA YASAĞI (ölçülemeyen None + neden); YASA-4 (sessiz-yutma işaretli + ≥20 karakter
gerekçe); YASA-6 (okuyucusuz yazım yok — sonuc.json dönüş raporunda tüketilir, hücre defterleri
denetim içindir). SALT-OKUMA: config.STATE bu klasörün altındaki izole sandbox'a çevrilir; barlar
sembolik bağla canlı önbellekten SALT-OKUNUR; canlı state'e tek bayt yazılmaz. loop.py /
counterfactual.py / cf_backfill.py İTHAL EDİLMEZ (paralel ajan sözleşmesi — koşum sonunda
sys.modules üzerinde ÇİVİLENİR).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import sys

SANDBOX = pathlib.Path(__file__).resolve().parent
STATE_DIR = SANDBOX / "state"
assert (STATE_DIR / "bars").exists(), f"bars sembolik bağı yok: {STATE_DIR/'bars'}"
assert (STATE_DIR / "goal.yaml").exists() and (STATE_DIR / "strategy.yaml").exists()

# tek-iş parçacığı: determinizm + ölçüm gürültüsüzlüğü (EDG-022 emsali)
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

REPO = SANDBOX.parents[2]        # research/olcumler/<bu>/ -> repo kökü
sys.path.insert(0, str(REPO))

import numpy as np               # noqa: E402
import yaml                      # noqa: E402

from meridian import config      # noqa: E402

# --- SALT-OKUMA İZOLASYONU: her yazım (obs.events, store) sandbox'a düşsün, canlı state'e DEĞİL ---
config.STATE = STATE_DIR
config.BARS = STATE_DIR / "bars"
config.HISTORY = STATE_DIR / "history"
config.HISTORY.mkdir(parents=True, exist_ok=True)

from meridian import backtest, dataset      # noqa: E402
from meridian import strategy as strat      # noqa: E402  (yalnız OKUMA: ARMED_SETUPS beyanı)

# ---- PARALEL-AJAN SÖZLEŞMESİ: yasak modüller ithal zincirine GİRMEMİŞ olmalı -------------------
YASAK_MODULLER = ("meridian.loop", "meridian.counterfactual", "meridian.cf_backfill")
for _m in YASAK_MODULLER:
    assert _m not in sys.modules, f"YASAK modül ithal edilmiş: {_m} (paralel ajan sözleşmesi ihlali)"

# ---- MOTOR KİMLİĞİ (yamasızlık + sürüm beyanı) --------------------------------------------------
MOTOR_DOSYALAR = {
    "backtest": pathlib.Path(backtest.__file__).resolve(),
    "strategy": pathlib.Path(strat.__file__).resolve(),
    "broker": pathlib.Path(sys.modules["meridian.broker"].__file__).resolve(),
}
assert not hasattr(backtest, "wpg_overlay_day"), "motor YAMALI görünüyor — ölçüm geçersiz olurdu"


def _sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


REPLAY_START = "2022-01-01"
# DUMAN TESTİ (yalnız araç doğrulaması, ölçüm DEĞİL): EDG024_SMOKE_END kısa pencere verir ve
# çıktılar *_smoke.json'a düşer — gerçek sonuc.json ASLA duman koşumuyla yazılmaz.
SMOKE_END = os.environ.get("EDG024_SMOKE_END")
REPLAY_END = SMOKE_END or "2026-07-30"   # kart: 2022-01 → 2026-07 (kanonik; EDG-022 ile aynı)
SMOKE = bool(SMOKE_END)

EDG022_DIR = REPO / "research/olcumler/edg022_evren_kisit_2026-08-09"

# Hücre tanımları — kart AYNEN (parameter_grid + taban çivisi). Değerler DONUK: operatör seçimi
# 2026-08-12 (hacim 1.25× / RS 65, tek kademe). Buradan başka hiçbir yerde eşik türetilmez.
HUCRELER = [
    ("taban", {}),
    ("hacim_125", {"entry.min_volume_ratio": 1.25}),
    ("rs_65", {"entry.rs_rating_min": 65}),
    ("ikisi", {"entry.min_volume_ratio": 1.25, "entry.rs_rating_min": 65}),
]

MIN_EKLENEN = 15                 # kill#2 eşiği (kart, DONUK)
BOOT_N = 5000
BOOT_SEED = 20260812             # tarih-tohumlu, DONUK (EDG-022 deseni)

# Kötümser bant (goal.yaml pessimistic_band_v2): tek yön 20/2=10bps − model 5bps = EK 5bps/bacak.
KOTUMSER_EK_BPS_BACAK = 5.0


def bootstrap_ci_ortR(satirlar: list[dict], r_alan: str, n_iter: int = BOOT_N,
                      seed: int = BOOT_SEED) -> dict | None:
    """Tarih-KÜMELİ (ts_open takvim ayı) bootstrap %95 CI — ortalama R için.

    Küme < 2 ise None (tek kümeden bootstrap dejenere olur: her çekiliş aynı havuz, sahte
    sıfır-genişlikli CI — UYDURMA YASAĞI'nın CI hâli). r_alan None olan satır CI'ya giremez;
    sayısı çağıranda raporlanır (buraya gelen liste zaten süzülmüş olmalı)."""
    aylar: dict[str, list[float]] = {}
    for t in satirlar:
        aylar.setdefault(str(t["ts_open"])[:7], []).append(float(t[r_alan]))
    ay_adlari = sorted(aylar)
    m = len(ay_adlari)
    if m < 2:
        return None
    ay_r = [np.asarray(aylar[a], dtype=float) for a in ay_adlari]
    rng = np.random.default_rng(seed)
    ortalar = np.empty(n_iter)
    idx_all = np.arange(m)
    for i in range(n_iter):
        pick = rng.choice(idx_all, size=m, replace=True)
        pooled = np.concatenate([ay_r[j] for j in pick])
        ortalar[i] = pooled.mean()
    return {"lo": round(float(np.percentile(ortalar, 2.5)), 4),
            "hi": round(float(np.percentile(ortalar, 97.5)), 4),
            "orta": round(float(np.median(ortalar)), 4),
            "n_ay_kume": m}


def islem_ozeti(rows: list[dict]) -> dict:
    """Bir işlem kümesinin betimleyicileri — motorun kendi maliyetli R'siyle (r_multiple)."""
    n = len(rows)
    if n == 0:
        return {"n": 0, "ort_r": None, "medyan_r": None, "toplam_r": None, "toplam_pnl": 0.0,
                "kazanc_orani": None, "setup_dagilim": {}, "neden": "küme boş — betimleyici yok"}
    rs = np.asarray([float(t["r_multiple"]) for t in rows])
    setups: dict[str, int] = {}
    for t in rows:
        setups[str(t.get("setup"))] = setups.get(str(t.get("setup")), 0) + 1
    return {"n": n,
            "ort_r": round(float(rs.mean()), 4),
            "medyan_r": round(float(np.median(rs)), 4),
            "toplam_r": round(float(rs.sum()), 3),
            "toplam_pnl": round(float(sum(float(t["pnl_dollars"]) for t in rows)), 2),
            "kazanc_orani": round(float((rs > 0).mean()), 4),
            "setup_dagilim": dict(sorted(setups.items(), key=lambda kv: -kv[1]))}


def kotumser_r_ekle(rows: list[dict]) -> tuple[list[dict], int]:
    """Her satıra r_kotumser ekler: R − ek_maliyet/risk_dolari.

    ek_maliyet = 5bps/bacak × qty × (entry+exit)  (goal.pessimistic_band_v2: 20bps açılış spread'i
    → tek yön 10bps; mevcut model 5bps → fark 5bps/bacak). risk_dolari defter satırından
    pnl_dollars/r_multiple ile geri türetilir (broker yasası: r_multiple = pnl/risk_dollars);
    |r_multiple| ~ 0 ise risk geri türetilemez → r_kotumser None + sayaç (UYDURMA YASAĞI:
    ölçülemeyen satıra maliyet uydurulmaz; CI'da bu satırlar düşer ve sayısı raporlanır)."""
    ek_oran = KOTUMSER_EK_BPS_BACAK / 1e4
    n_hesaplanamadi = 0
    out = []
    for t in rows:
        r = float(t["r_multiple"])
        pnl = float(t["pnl_dollars"])
        ek = ek_oran * float(t["qty"]) * (float(t["entry"]) + float(t["exit"]))
        if abs(r) < 1e-9:
            # sessiz-yutma İŞARETLİ: r_multiple==0 → risk_dollars geri türetilemez (0/0); bu satır
            # kötümser CI'dan düşer ve n_kotumser_hesaplanamadi sayacında görünür — yutulmadı.
            n_hesaplanamadi += 1
            out.append({**t, "r_kotumser": None})
            continue
        risk = pnl / r
        if risk <= 0:
            n_hesaplanamadi += 1
            out.append({**t, "r_kotumser": None})
            continue
        out.append({**t, "r_kotumser": round(r - ek / risk, 4)})
    return out, n_hesaplanamadi


def main():
    t0 = dt.datetime.now()

    # ---- parametre kaynağı: sandbox strategy.yaml == canlı state/strategy.yaml (sha kanıtı) ----
    st_yaml = (STATE_DIR / "strategy.yaml").read_text()
    canli_p = REPO / "state" / "strategy.yaml"
    canli_sha = _sha(canli_p) if canli_p.exists() else None
    sandbox_sha = hashlib.sha256(st_yaml.encode()).hexdigest()
    st = yaml.safe_load(st_yaml)
    base_params = dict(st["params"])
    by_regime = st.get("params_by_regime") or None
    sv = int(st.get("version"))
    # rejim-koşullu geçersiz kılma boş olmalı — yoksa hücre enjeksiyonu rejim tablosuna da girmeliydi
    rejim_bos = all(not (v or {}) for v in (by_regime or {}).values())
    assert rejim_bos, "params_by_regime BOŞ değil — düz-param enjeksiyonu tek başına yetmezdi"
    # kart ön-şartı: taban eşikler kartın 'mevcut' dediği değerler olmalı
    assert float(base_params["entry.min_volume_ratio"]) == 1.5, "taban hacim eşiği 1.5 değil"
    assert float(base_params["entry.rs_rating_min"]) == 70, "taban RS eşiği 70 değil"

    goal = config.goal()
    limits = goal["limits"]

    # ---- EDG-022 şasi çapaları (kill#3 girdileri) ----------------------------------------------
    s022 = json.loads((EDG022_DIR / "sonuc.json").read_text())
    seans022 = json.loads((EDG022_DIR / "seanslar.json").read_text())
    tarihler_022 = [r["date"] for r in sorted(seans022, key=lambda r: r["date"])]
    plan022_gunluk = {r["date"]: int(r.get("plan_aday", 0)) for r in seans022}

    bars, index = dataset.load_cached()

    # ---- DÖRT KOŞUM (tek süreç, sıralı; motor yamasız — çıplak backtest.replay çağrısı) --------
    # KONTROL NOKTASI (2026-08-12 kill vakası: taban+hacim_125 bitmişken süreç dışarıdan öldürüldü,
    # defterler bellekteydi → 50 dk kayıp). Hücre biter bitmez ara_<hücre>.json'a döker; yeniden
    # başlatmada GEÇERLİLİK BEKÇİSİYLE yükler: tam-param + pencere + motor-sha eşleşmeyen checkpoint
    # KULLANILMAZ (bayat checkpoint ölçümü zehirlerdi — sessizce değil, beyanla yeniden koşulur).
    # Deterministik motor + donmuş bar önbelleği → aynı girdiyle yeniden-kullanım sağlam.
    motor_sha_simdi = {k: _sha(v) for k, v in MOTOR_DOSYALAR.items()}
    kosum: dict[str, dict] = {}
    for ad, degisiklik in HUCRELER:
        cp = dict(base_params)
        cp.update(degisiklik)
        ckpt = SANDBOX / (f"ara_{ad}_smoke.json" if SMOKE else f"ara_{ad}.json")
        rec = None
        if ckpt.exists():
            try:
                aday = json.loads(ckpt.read_text())
                g = aday.get("_gecerlilik") or {}
                if (g.get("cell_params") == {k: float(v) for k, v in cp.items()
                                             if isinstance(v, (int, float))}
                        and g.get("start") == REPLAY_START and g.get("end") == REPLAY_END
                        and g.get("motor_sha") == motor_sha_simdi and g.get("sv") == sv):
                    rec = aday
                    print(f"[kosum] {ad:10s} KONTROL NOKTASINDAN yüklendi ({ckpt.name})", flush=True)
                else:
                    print(f"[kosum] {ad:10s} checkpoint BAYAT (param/pencere/motor uyuşmadı) — "
                          "yeniden koşulacak", flush=True)
            except (json.JSONDecodeError, OSError) as e:
                # sessiz-yutma İŞARETLİ: bozuk checkpoint kullanılmaz, nedeni logda — yeniden koşum
                print(f"[kosum] {ad:10s} checkpoint OKUNAMADI ({type(e).__name__}: {e}) — "
                      "yeniden koşulacak", flush=True)
        if rec is None:
            tk0 = dt.datetime.now()
            res = backtest.replay(cp, bars, index, goal, REPLAY_START, REPLAY_END,
                                  strategy_version=sv, params_by_regime=by_regime,
                                  with_gate_detail=False)
            sure = (dt.datetime.now() - tk0).total_seconds()
            trades = list(res.trades or [])
            # işlem kimliği: plan_id benzersiz olmalı (diff yasasının temeli)
            ids = [t.get("plan_id") for t in trades]
            assert all(ids), f"{ad}: plan_id'siz işlem satırı var — diff yasası kurulamaz"
            assert len(ids) == len(set(ids)), f"{ad}: tekrarlı plan_id — diff yasası kurulamaz"
            plan_gunluk: dict[str, int] = {}
            arm_setup: dict[str, int] = {}
            n_armed = 0
            for p in (res.plan_log or []):
                d = str(p.get("date"))[:10]
                plan_gunluk[d] = plan_gunluk.get(d, 0) + 1
                if p.get("gate_verdict") != "NO_GO":
                    n_armed += 1
                    s = str(p.get("setup"))
                    arm_setup[s] = arm_setup.get(s, 0) + 1
            n_scaled = sum(1 for t in trades if t.get("scaled_out"))
            rec = {
                "_gecerlilik": {"cell_params": {k: float(v) for k, v in cp.items()
                                                if isinstance(v, (int, float))},
                                "start": REPLAY_START, "end": REPLAY_END,
                                "motor_sha": motor_sha_simdi, "sv": sv},
                "params_degisen": degisiklik, "sure_sn": round(sure, 1),
                "trades": trades,
                "n_trades": len(trades),
                "toplam_pnl": round(sum(float(t["pnl_dollars"]) for t in trades), 2),
                "final_equity": (float(res.equity[-1][1]) if res.equity else None),
                "n_plan": len(res.plan_log or []), "n_armed": n_armed,
                "armed_setup_dagilim": dict(sorted(arm_setup.items(), key=lambda kv: -kv[1])),
                "plan_gunluk": plan_gunluk,
                "entry_rejects": dict(res.entry_rejects or {}),
                "n_scaled_out": n_scaled,
                "n_seans": len(res.equity or []),
                "seans_tarihleri": [e[0] for e in (res.equity or [])],
            }
            ckpt.write_text(json.dumps(rec, ensure_ascii=False, default=str))
            print(f"[kosum] {ad:10s} bitti  sure={sure:7.1f}s  n_trades={len(trades):4d}  "
                  f"pnl={rec['toplam_pnl']:10.2f}  n_plan={rec['n_plan']}  ckpt={ckpt.name}",
                  flush=True)
        kosum[ad] = dict(rec)
        kosum[ad]["by_id"] = {t["plan_id"]: t for t in kosum[ad]["trades"]}

    taban = kosum["taban"]

    # ---- KILL#3 olguları -----------------------------------------------------------------------
    takvim_esit = (taban["seans_tarihleri"] == tarihler_022)
    # 022 kaydıyla tarih-başına plan sayısı: İLK SAPMA günü (motor değişimi beyanının güç-testi)
    ilk_sapma = None
    n_esit_gun = 0
    for d in tarihler_022:
        a = taban["plan_gunluk"].get(d, 0)
        b = plan022_gunluk.get(d, 0)
        if a == b:
            n_esit_gun += 1
        elif ilk_sapma is None:
            ilk_sapma = {"tarih": d, "taban_plan": a, "edg022_plan": b}
    params_022_esit = (s022["replay"]["params"] == base_params)
    kill3 = {
        "sasi_022": {
            "n_sembol": len(bars), "n_sembol_beklenen": 251, "n_sembol_esit": len(bars) == 251,
            "n_seans": taban["n_seans"], "n_seans_022": len(tarihler_022),
            "takvim_birebir_esit": takvim_esit,
            "max_open": int(limits["max_open_positions"]),
            "no_trade_before": int(limits.get("no_trade_before_bars", 0)),
            "limits_022_esit": (int(limits["max_open_positions"]) == s022["replay"]["max_open"]
                                and int(limits.get("no_trade_before_bars", 0)) == s022["replay"]["no_trade_before"]),
            "params_022_esit": params_022_esit,
        },
        "canli_davranis": {
            "params_sha256_canli": canli_sha, "params_sha256_sandbox": sandbox_sha,
            "params_canli_esit": (canli_sha == sandbox_sha),
            "armed_setups": list(strat.ARMED_SETUPS),
            "motor_yamasiz": True,
            "motor_sha256": {k: _sha(v) for k, v in MOTOR_DOSYALAR.items()},
            "motor_degisim_beyani": [
                "de47ea2/v233 2026-08-12: exhaustion_hammer OPERATÖR ONAYIYLA silahlandı (ARMED_SETUPS'a girdi)",
                "becb03b/v236 2026-08-12: broker birikim sent-yuvarlaması (scale_out/close akümülatörleri)",
            ],
            "aciklama": ("taban = BUGÜNKÜ motor (mevcut canlı davranış) + canlı params; 022 kaydıyla "
                         "işlem-düzeyi bit-özdeşlik motor değişimi (operatör onaylı) nedeniyle "
                         "TANIMSIZ — şasi (evren/takvim/limit/params) düzeyinde özdeşlik ölçüldü."),
        },
        "plan_gunluk_022_kiyas": {
            "n_esit_gun": n_esit_gun, "n_gun": len(tarihler_022),
            "ilk_sapma": ilk_sapma,
            "okuma": ("ilk sapmaya kadar birebir eşit gün sayısı; sapmanın v233 hammer-silahlanmasının "
                      "beklenen izi olup olmadığını Rol-1 okur (taban armed_setup_dagilim'ında "
                      "exhaustion_hammer görünür)"),
        },
    }

    # ---- HÜCRE DIFF'LERİ -----------------------------------------------------------------------
    hucreler_out: dict[str, dict] = {}
    taban_ids = set(taban["by_id"])
    for ad, _ in HUCRELER[1:]:
        h = kosum[ad]
        h_ids = set(h["by_id"])
        eklenen_ids = sorted(h_ids - taban_ids)
        cikan_ids = sorted(taban_ids - h_ids)
        ortak_ids = h_ids & taban_ids
        eklenen = [h["by_id"][i] for i in eklenen_ids]
        cikan = [taban["by_id"][i] for i in cikan_ids]
        ortak_kayma = round(sum(float(h["by_id"][i]["pnl_dollars"]) -
                                float(taban["by_id"][i]["pnl_dollars"]) for i in ortak_ids), 2)
        net_pnl_farki = round(h["toplam_pnl"] - taban["toplam_pnl"], 2)
        eklenen_pnl = round(sum(float(t["pnl_dollars"]) for t in eklenen), 2)
        cikan_pnl = round(sum(float(t["pnl_dollars"]) for t in cikan), 2)
        dekomp_fark = round(net_pnl_farki - (eklenen_pnl - cikan_pnl + ortak_kayma), 2)

        n_ek = len(eklenen)
        olculemedi = n_ek < MIN_EKLENEN
        ci = ci_kot = kot_ozet = None
        n_kot_yok = 0
        if not olculemedi:
            ci = bootstrap_ci_ortR(eklenen, "r_multiple")
            ekli, n_kot_yok = kotumser_r_ekle(eklenen)
            kot_rows = [t for t in ekli if t["r_kotumser"] is not None]
            if len(kot_rows) >= MIN_EKLENEN:
                ci_kot = bootstrap_ci_ortR(kot_rows, "r_kotumser")
            if kot_rows:
                # YALNIZ R istatistiği: pnl alanları motor-maliyetlidir, kötümser blokta pnl
                # raporlamak bandı düşülmüş gibi okunurdu (yanlış etiket — o yüzden yok).
                krs = np.asarray([t["r_kotumser"] for t in kot_rows], dtype=float)
                kot_ozet = {"n": len(kot_rows), "ort_r": round(float(krs.mean()), 4),
                            "medyan_r": round(float(np.median(krs)), 4),
                            "toplam_r": round(float(krs.sum()), 3),
                            "kazanc_orani": round(float((krs > 0).mean()), 4)}

        hucreler_out[ad] = {
            "params_degisen": h["params_degisen"],
            "n_trades": h["n_trades"], "toplam_pnl": h["toplam_pnl"],
            "final_equity": h["final_equity"],
            "n_plan": h["n_plan"], "n_armed": h["n_armed"],
            "armed_setup_dagilim": h["armed_setup_dagilim"],
            "entry_rejects": h["entry_rejects"],
            "eklenen": {
                "ids_n": n_ek,
                "olculemedi": olculemedi,
                "olculemedi_neden": (f"eklenen {n_ek} < {MIN_EKLENEN} — kill#2: örneklem yetersiz, "
                                     "CI anlamsız (hesaplanmadı)") if olculemedi else None,
                "ozet": islem_ozeti(eklenen),
                "ci95_ort_r": ci,
                "ci95_ort_r_kotumser": ci_kot,
                "kotumser_ozet": kot_ozet,
                "n_kotumser_hesaplanamadi": n_kot_yok,
                "ci_0_ustu": (bool(ci and ci["lo"] > 0) if not olculemedi and ci else None),
                "ci_0_ustu_kotumser": (bool(ci_kot and ci_kot["lo"] > 0)
                                       if not olculemedi and ci_kot else None),
            },
            "cikan": {"n": len(cikan), "toplam_pnl": cikan_pnl,
                      "ozet": islem_ozeti(cikan) if cikan else None},
            "ortak": {"n": len(ortak_ids), "pnl_kaymasi": ortak_kayma},
            "net_pnl_farki_tam_defter": net_pnl_farki,
            "dekompozisyon": {"eklenen_pnl": eklenen_pnl, "cikan_pnl": cikan_pnl,
                              "ortak_kayma": ortak_kayma, "artik": dekomp_fark,
                              "tutarli": abs(dekomp_fark) < 0.05},
            "sure_sn": h["sure_sn"],
        }

    # ---- ÇIKTI ---------------------------------------------------------------------------------
    ci_ustu = [ad for ad, v in hucreler_out.items()
               if v["eklenen"]["ci_0_ustu"] is True]
    out = {
        "kart": "EDG-2026-024",
        "modul": str(pathlib.Path(__file__).resolve()),
        "olcum_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "sure_sn_toplam": round((dt.datetime.now() - t0).total_seconds(), 1),
        "replay": {"start": REPLAY_START, "end": REPLAY_END, "strategy_version": sv,
                   "params_taban": base_params, "params_by_regime": by_regime,
                   "n_sembol": len(bars), "n_endeks_satir": int(len(index)),
                   "cost_model": {"birincil": "motorun kendisi: slippage_bps=5/bacak fiyatın içinde, komisyon 0",
                                  "kotumser_band": "pessimistic_band_v2: 20bps açılış spread → +5bps/bacak ek",
                                  "ek_bps_bacak": KOTUMSER_EK_BPS_BACAK}},
        "kill3": kill3,
        "taban": {k: taban[k] for k in ("n_trades", "toplam_pnl", "final_equity", "n_plan",
                                        "n_armed", "armed_setup_dagilim", "entry_rejects",
                                        "n_scaled_out", "sure_sn")},
        "taban_ozet": islem_ozeti(taban["trades"]),
        "hucreler": hucreler_out,
        "ci_0_ustu_hucreler": ci_ustu,
        "kill2_okuma": {ad: v["eklenen"]["olculemedi"] for ad, v in hucreler_out.items()},
        "bootstrap": {"n_iter": BOOT_N, "seed": BOOT_SEED, "kume": "ts_open takvim ayı",
                      "duzey": 0.95},
        "bounds_notu": ("BİLGİ (hüküm değil): bounds.yaml entry.min_volume_ratio {min:1.0, step:0.1} "
                        "— 1.25 IZGARA-DIŞI (1.2/1.3 ızgarada); entry.rs_rating_min {min:60, step:1} "
                        "— 65 ızgara-içi. Olası değişiklik önerisinin OOS kapısında önem taşır; "
                        "ölçüm kart değerlerini AYNEN kullandı."),
        "smoke": SMOKE,
        "hukum": None,   # HÜKÜM YAZILMAZ — kartın hükmünü Rol-1 işler (ölçüm disiplini)
    }
    sonuc_ad = "sonuc_smoke.json" if SMOKE else "sonuc.json"
    defter_ad = "hucre_defterleri_smoke.json" if SMOKE else "hucre_defterleri.json"
    (SANDBOX / sonuc_ad).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str))

    # hücre defterleri (denetim/yeniden-analiz — YASA-6 okuyucusu: dönüş raporu + Rol-1 denetimi)
    defter = {ad: {"params_degisen": kosum[ad]["params_degisen"], "trades": kosum[ad]["trades"]}
              for ad, _ in HUCRELER}
    (SANDBOX / defter_ad).write_text(json.dumps(defter, ensure_ascii=False, default=str))

    # kontrol noktaları artık gereksiz: içerik hucre_defterleri + sonuc'ta kalıcı — temizle
    for ad, _ in HUCRELER:
        ck = SANDBOX / (f"ara_{ad}_smoke.json" if SMOKE else f"ara_{ad}.json")
        if ck.exists():
            ck.unlink()

    # ---- yapısal özet (stdout) ----
    print("\n==================== EDG-024 ÖLÇÜM ÖZETİ ====================")
    if SMOKE:
        print("!!! DUMAN KOŞUMU (kısa pencere) — ÖLÇÜM DEĞİL, yalnız araç doğrulaması !!!")
    print(f"replay {REPLAY_START}→{REPLAY_END}  sv={sv}  sembol={len(bars)}  "
          f"toplam süre={out['sure_sn_toplam']}s")
    k3 = kill3["sasi_022"]
    print(f"KILL#3 şasi: sembol_esit={k3['n_sembol_esit']} takvim_esit={k3['takvim_birebir_esit']} "
          f"params_022_esit={k3['params_022_esit']} limits_esit={k3['limits_022_esit']}")
    print(f"KILL#3 canlı: params_canli_esit={kill3['canli_davranis']['params_canli_esit']} "
          f"armed={kill3['canli_davranis']['armed_setups']}")
    print(f"022 plan-kıyas: eşit_gün={kill3['plan_gunluk_022_kiyas']['n_esit_gun']}"
          f"/{kill3['plan_gunluk_022_kiyas']['n_gun']}  ilk_sapma={kill3['plan_gunluk_022_kiyas']['ilk_sapma']}")
    tb = out["taban_ozet"]
    print(f"TABAN: n={taban['n_trades']}  pnl={taban['toplam_pnl']}  ort_r={tb['ort_r']}  "
          f"setup={tb['setup_dagilim']}")
    for ad, v in hucreler_out.items():
        e = v["eklenen"]
        oz = e["ozet"]
        ci = e["ci95_ort_r"]
        cis = f"[{ci['lo']}, {ci['hi']}] ay={ci['n_ay_kume']}" if ci else "—"
        cik = e["ci95_ort_r_kotumser"]
        ciks = f"[{cik['lo']}, {cik['hi']}]" if cik else "—"
        print(f"{ad:10s} eklenen_n={e['ids_n']:3d} olculemedi={e['olculemedi']} "
              f"ort_r={oz.get('ort_r')} CI95={cis} kötümserCI={ciks} "
              f"netPnL_farkı={v['net_pnl_farki_tam_defter']:+.2f} "
              f"(eklenen {v['dekompozisyon']['eklenen_pnl']:+.2f} / çıkan {v['cikan']['n']} "
              f"{v['dekompozisyon']['cikan_pnl']:+.2f} / kayma {v['dekompozisyon']['ortak_kayma']:+.2f}) "
              f"setup={oz.get('setup_dagilim')}")
    print(f"CI-0-ÜSTÜ hücreler: {ci_ustu or 'YOK'}")
    for _m in YASAK_MODULLER:
        assert _m not in sys.modules, f"YASAK modül koşum sırasında ithal edilmiş: {_m}"
    print("yasak modül çivisi: loop/counterfactual/cf_backfill ithal EDİLMEDİ (doğrulandı)")
    print(f"yazıldı: {SANDBOX/sonuc_ad}")
    print("=============================================================\n")


if __name__ == "__main__":
    main()

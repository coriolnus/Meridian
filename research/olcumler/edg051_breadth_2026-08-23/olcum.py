#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EDG-2026-051 — genişlik (breadth) dilim ölçümü. KART: research/cards/EDG-2026-051-genislik-dilimi.yaml
HÜKÜM YOK — bu betik yalnız ölçer; hükmü Rol-1 işler.

TABAN (DONUK, SALT-OKUMA):
  - Vekil işlem tabanı: research/olcumler/exe003_golge_kapsam_2026-08-22/canli_state/meridian.db
    (28g teşhisiyle AYNI taban; wp3_holdout_teshis_2026-08-22/04_canli_holdout_islemler.py ile
    AYNI _in_segment yasası: lo <= ts_open[:10] < hi and (not ts_close or ts_close[:10] <= hi)).
  - Bar arşivi: state/bars/*.csv — KANONİK ölçüm kapısıyla okunur
    (data.REPLAY_UNIVERSE 251 sembol + sanitize_bars + measurement_bars; component_ic._load_universe
    ile aynı yol: ağ yok, bütünlük defteri uygulanır).

PIT SÖZLEŞMESİ (kart kill#3): breadth(t) YALNIZ t'den ÖNCEKİ barlarla — seans t'ye atanan değer,
t'den küçük en son seansın (d*) kapanışlarından: sembol payda'ya girer ⇔ d*'de barı var ve d*'ye
dek ≥50 kapanışı var; pay ⇔ close(d*) > MA50(d*). Kod-içi assert'ler: (a) d* < t her çağrıda,
(b) tohumlu nokta-sınamaları ham CSV'nin t-ÖNCESİ dilimiyle yeniden hesaplar ve karşılaştırır,
(c) örneklenmiş (sembol,gün)'de MA50 son-50-pencerenin geleceğe bakmadığı doğrudan doğrulanır.

BÖLME (kart, DONUK): 87 işlemin giriş-günü breadth'i; medyan = bu 87 değerin medyanı
(holdout-penceresi içinden — tüm giriş günleri 2026-04-30..2026-07-22 pencere içidir);
genis: breadth >= medyan · dar: breadth < medyan. Döküm ölçüm-ÖNCE sonuc.json'a yazılır
(FAZ-A; r_multiple/çıkış alanları FAZ-A'da HİÇ okunmaz), sonra FAZ-B dilim metriklerini ekler.

STATE'E DOKUNMAMA: meridian.obs._emit normalde state/events.jsonl'a aynalar; burada ölçüm
dizinindeki obs_events.jsonl'a YÖNLENDİRİLİR (olay kaybolmaz — YASA 4'e uygun; state yazılmaz).
"""
import sys, os, json, hashlib, sqlite3, datetime as dt

sys.path.insert(0, "/Users/erdemozturk/AI-Trading")
OUT = "/Users/erdemozturk/AI-Trading/research/olcumler/edg051_breadth_2026-08-23"
DB = "/Users/erdemozturk/AI-Trading/research/olcumler/exe003_golge_kapsam_2026-08-22/canli_state/meridian.db"

# --- obs yönlendirme: state/events.jsonl YERİNE ölçüm dizinine (state'e dokunma) ---
from meridian import obs as _obs
_OBSF = os.path.join(OUT, "obs_events.jsonl")
def _emit_local(level, event, fields):
    rec = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "level": level, "event": event, **{k: str(v) for k, v in fields.items()}}
    print(f"[obs->{level}] {event} {fields}")
    with open(_OBSF, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec
_obs._emit = _emit_local  # süreç-içi; motor DOSYALARINA dokunulmaz

import numpy as np
import pandas as pd
from meridian.adapters import data as data_adapter

SEED = 20260812
B = 5000
MA_N = 50
HOLD_LO, HOLD_HI = "2026-04-30", "2026-07-30"
FULL_LO, FULL_HI = "2022-01-01", "2026-07-30"   # tam-pencere kıyası: inc-cache geometrisinin tamamı (IS başı → holdout sonu)

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()

# ============ [1] BREADTH SERİSİ (PIT) ============
print("== [1] evren barları (kanonik kapı: sanitize_bars + measurement_bars) ==")
frames, okunamayan, ma_yetersiz = [], [], []
raw_cache = {}   # PIT nokta-sınamaları için HAM (kapıdan geçmiş) df saklanır
for t in data_adapter.REPLAY_UNIVERSE:
    cp = data_adapter._cache_path(t)
    if not cp.exists():
        okunamayan.append((t, "csv yok"))
        continue
    try:
        df, _rep = data_adapter.sanitize_bars(pd.read_csv(cp, parse_dates=["date"]), t)
        df = data_adapter.measurement_bars(df, t)
        if df is None or df.empty:
            okunamayan.append((t, "kapı sonrası boş"))
            continue
        df = df[["date", "close"]].sort_values("date").reset_index(drop=True)
        raw_cache[t] = df
        ma = df["close"].rolling(MA_N, min_periods=MA_N).mean()   # pencere t'DE BİTER (geriye bakar)
        g = pd.DataFrame({"date": df["date"].dt.strftime("%Y-%m-%d"),
                          "above": (df["close"] > ma) & ma.notna(),
                          "meas": ma.notna()})
        frames.append(g)
        if not ma.notna().any():
            ma_yetersiz.append(t)
    except Exception as e:
        okunamayan.append((t, f"{type(e).__name__}: {e}"))   # sessiz düşürme YOK — rapora girer

agg = pd.concat(frames).groupby("date").agg(A=("above", "sum"), M=("meas", "sum")).sort_index()
agg = agg[agg["M"] > 0]
SESS = agg.index.to_numpy()          # ölçülebilir seans takvimi (sıralı)
A = agg["A"].to_numpy(float); M = agg["M"].to_numpy(float)
BR = 100.0 * A / M                   # seans-sonu breadth (o seansın kapanışıyla)

def breadth_asof(t_date: str):
    """Seans/gün t için PIT breadth: t'den ÖNCEKİ son ölçülebilir seansın değeri. d* < t assert'li."""
    i = int(np.searchsorted(SESS, t_date))          # SESS[i-1] < t_date <= SESS[i]
    assert i > 0, f"PIT: {t_date} öncesi seans yok"
    d_star = SESS[i - 1]
    assert d_star < t_date, f"PIT İHLALİ: d*={d_star} !< t={t_date}"   # kill#3 kod-içi kapı
    return float(BR[i - 1]), str(d_star), int(M[i - 1])

# --- PIT öz-sınaması 1: MA penceresi geleceğe bakmıyor (örneklenmiş doğrudan doğrulama) ---
rng0 = np.random.default_rng(SEED)
syms = sorted(raw_cache)
pit1 = []
for t in rng0.choice(syms, size=10, replace=False):
    df = raw_cache[t]
    j = int(rng0.integers(MA_N, len(df) - 1))
    el_ma = float(df["close"].iloc[j - MA_N + 1: j + 1].mean())      # son 50 kapanış, j DAHİL, gelecek YOK
    ser_ma = float(df["close"].rolling(MA_N, min_periods=MA_N).mean().iloc[j])
    assert abs(el_ma - ser_ma) < 1e-9, f"MA pencere ihlali {t}@{j}"
    pit1.append({"sembol": str(t), "idx": j, "tarih": df['date'].iloc[j].strftime('%Y-%m-%d'), "ma_esit": True})
print(f"PIT öz-sınama 1 (MA penceresi, 10 örnek): GEÇTİ")

# ============ [2] HOLDOUT İŞLEMLERİ — FAZ A (SONUÇ ALANLARI OKUNMAZ) ============
print("== [2] FAZ A: giriş-günü breadth + medyan bölmesi (döküm ölçüm-ÖNCE beyan) ==")
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True); con.row_factory = sqlite3.Row
fazA = [dict(r) for r in con.execute("SELECT id, ticker, ts_open, ts_close FROM trades")]
con.close()

def in_segment(t, lo, hi):
    op = str(t.get("ts_open") or "")[:10]; cl = str(t.get("ts_close") or "")[:10]
    return bool(lo <= op < hi and (not cl or cl <= hi))

H = sorted([t for t in fazA if in_segment(t, HOLD_LO, HOLD_HI)], key=lambda t: (str(t["ts_open"]), t["id"]))
assert len(H) == 87, f"holdout n={len(H)} != 87 — taban teşhisle örtüşmüyor, ölçüm durdu"

dokum = []
for t in H:
    gday = str(t["ts_open"])[:10]
    b, dstar, m = breadth_asof(gday)
    dokum.append({"id": t["id"], "ticker": t["ticker"], "giris_gunu": gday,
                  "breadth_kaynak_seans": dstar, "payda_n": m, "breadth_pct": round(b, 4)})

vals = np.array([d["breadth_pct"] for d in dokum])
medyan = float(np.median(vals))                       # 87 değerin medyanı (n tek → gözlenen değer)
for d in dokum:
    d["dilim"] = "genis" if d["breadth_pct"] >= medyan else "dar"
n_genis = sum(1 for d in dokum if d["dilim"] == "genis")
n_dar = len(dokum) - n_genis
kill1 = (n_genis < 20) or (n_dar < 20)

# --- PIT öz-sınaması 2: tohumlu nokta-sınamaları — ham verinin t-ÖNCESİ dilimiyle yeniden hesap ---
rng1 = np.random.default_rng(SEED + 1)
pit2 = []
for d in [dokum[int(i)] for i in rng1.choice(len(dokum), size=12, replace=False)]:
    tday = d["giris_gunu"]
    el_above = el_meas = 0
    for s in syms:
        df = raw_cache[s]
        past = df[df["date"] < pd.Timestamp(tday)]    # KESİN: yalnız t'den önceki barlar
        if len(past) >= MA_N and past["date"].iloc[-1].strftime("%Y-%m-%d") == d["breadth_kaynak_seans"]:
            el_meas += 1
            if float(past["close"].iloc[-1]) > float(past["close"].iloc[-MA_N:].mean()):
                el_above += 1
    el_b = 100.0 * el_above / el_meas
    assert abs(el_b - d["breadth_pct"]) < 1e-6, f"PIT nokta-sınama TUTMADI {tday}: {el_b} vs {d['breadth_pct']}"
    pit2.append({"giris_gunu": tday, "beklenen": d["breadth_pct"], "yeniden_hesap": round(el_b, 4), "esit": True})
print(f"PIT öz-sınama 2 (12 giriş günü, t-öncesi dilimle yeniden hesap): GEÇTİ")

beyan = {
    "kart": "EDG-2026-051", "faz": "A-beyan (SONUÇ ALANLARI OKUNMADI)",
    "beyan_ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    "pit_sozlesmesi": "breadth(t) = t'den ÖNCEKİ son seansın (d*) kapanışlarıyla; d*<t kod-içi assert; MA50 penceresi d*'de biter",
    "taban": {"db": DB, "db_sha256": sha256(DB),
              "bar_kapisi": "data.REPLAY_UNIVERSE(251) + sanitize_bars + measurement_bars (component_ic._load_universe ile aynı yol)",
              "segment_yasasi": "lo <= ts_open[:10] < hi and (not ts_close or ts_close[:10] <= hi) — wp3 teşhisle AYNI"},
    "evren": {"n_evren": len(data_adapter.REPLAY_UNIVERSE), "n_seride": len(frames),
              "okunamayan": okunamayan, "ma_hic_olusamayan": ma_yetersiz},
    "medyan_breadth_pct": medyan,
    "bolme_kurali": "genis: breadth >= medyan | dar: breadth < medyan (kart; DEĞİŞMEZ)",
    "n_genis": n_genis, "n_dar": n_dar,
    "kill1_n20": {"tetiklendi": bool(kill1), "kural": "dilimlerden biri n<20 → hüküm YOK, betimleyici damga (bölme değişmez)"},
    "dokum": dokum,
    "pit_oz_sinama": {"ma_pencere_10ornek": pit1, "nokta_sinama_12gun": pit2},
}
sonuc_path = os.path.join(OUT, "sonuc.json")
with open(sonuc_path, "w") as f:
    json.dump({"bolme_beyani": beyan}, f, indent=1, ensure_ascii=False)
    f.flush(); os.fsync(f.fileno())
beyan_sha = sha256(sonuc_path)
print(f"FAZ A beyan diske yazıldı: medyan={medyan:.4f} n_genis={n_genis} n_dar={n_dar} kill1={kill1}")
print(f"beyan sha256: {beyan_sha}")

# ============ [3] FAZ B: SONUÇ METRİKLERİ (beyan değişmeden üstüne eklenir) ============
print("== [3] FAZ B: dilim metrikleri + bootstrap ==")
ondisk = json.load(open(sonuc_path))
assert json.dumps(ondisk["bolme_beyani"], sort_keys=True) == json.dumps(beyan, sort_keys=True), "beyan diskte değişmiş!"

con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True); con.row_factory = sqlite3.Row
outc = {r["id"]: dict(r) for r in con.execute("SELECT id, r_multiple, exit_reason, setup FROM trades")}
con.close()

def dilim_metrik(ids):
    rs = np.array([float(outc[i]["r_multiple"] or 0) for i in ids])
    ex = [str(outc[i]["exit_reason"]) for i in ids]
    st = [str(outc[i]["setup"]) for i in ids]
    n = len(ids)
    cnt = lambda xs: {k: xs.count(k) for k in sorted(set(xs))}
    return {"n": n, "toplam_R": round(float(rs.sum()), 3), "ort_R": round(float(rs.mean()), 4),
            "stop_payi_pct": round(100.0 * ex.count("stop") / n, 1),
            "stop_gap_payi_pct": round(100.0 * ex.count("stop_gap") / n, 1),
            "stop_veya_gap_payi_pct": round(100.0 * (ex.count("stop") + ex.count("stop_gap")) / n, 1),
            "kazanma_pct": round(100.0 * float((rs > 0).mean()), 1),
            "cikis_dagilimi": cnt(ex), "setup_dagilimi": cnt(st)}, rs

ids_genis = [d["id"] for d in dokum if d["dilim"] == "genis"]
ids_dar = [d["id"] for d in dokum if d["dilim"] == "dar"]
m_genis, rs_genis = dilim_metrik(ids_genis)
m_dar, rs_dar = dilim_metrik(ids_dar)

delta = float(rs_dar.mean() - rs_genis.mean())            # ΔortR(dar − genis)
rng = np.random.default_rng(SEED)
boot = np.empty(B)
for b in range(B):                                        # işlem-düzeyi, dilim-içi yeniden örnekleme
    boot[b] = (rng.choice(rs_dar, size=len(rs_dar), replace=True).mean()
               - rng.choice(rs_genis, size=len(rs_genis), replace=True).mean())
ci_lo, ci_hi = (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)))

# betimleyici (HÜKÜM DEĞİL): breadth seyri — holdout penceresi + tam-pencere kıyası
def pencere_ozet(lo, hi):
    m = (SESS >= lo) & (SESS < hi)
    v = BR[m]
    return {"pencere": f"{lo}..{hi}", "seans_n": int(m.sum()),
            "min": round(float(v.min()), 2), "q25": round(float(np.percentile(v, 25)), 2),
            "medyan": round(float(np.median(v)), 2), "q75": round(float(np.percentile(v, 75)), 2),
            "maks": round(float(v.max()), 2),
            "payda_araligi": [int(M[m].min()), int(M[m].max())]}
hold_seyir = pencere_ozet(HOLD_LO, HOLD_HI)
tam_seyir = pencere_ozet(FULL_LO, FULL_HI)
tam_v = BR[(SESS >= FULL_LO) & (SESS < FULL_HI)]
hold_v = BR[(SESS >= HOLD_LO) & (SESS < HOLD_HI)]
yuzdelik = round(100.0 * float((tam_v < np.median(hold_v)).mean()), 1)

sonuc = {
    "bolme_beyani": beyan,
    "bolme_beyani_disk_sha256_fazB_oncesi": beyan_sha,
    "fazB_ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    "dilimler": {"genis_breadth_yuksek": m_genis, "dar_breadth_dusuk": m_dar},
    "ayrisma": {"delta_ortR_dar_eksi_genis": round(delta, 4),
                "bootstrap": {"B": B, "seed": SEED, "yontem": "işlem-düzeyi, dilim-içi yeniden örnekleme; yüzdelik CI",
                              "ci95": [round(ci_lo, 4), round(ci_hi, 4)]},
                "karar_kurali_hatirlatma_HUKUM_DEGIL": "kart: CI-üst < 0 → 'ayırıyor'; CI 0-içi → 'ayırmıyor' — hüküm Rol-1'in"},
    "kill1_damga": ("HÜKÜM-YOK/BETİMLEYİCİ (n<20 dilim var)" if kill1 else "tetiklenmedi (iki dilim de n>=20)"),
    "betimleyici_breadth_seyri_HUKUM_DEGIL": {
        "holdout_penceresi": hold_seyir, "tam_pencere_2022_2026": tam_seyir,
        "holdout_medyaninin_tam_penceredeki_yuzdeligi": yuzdelik},
    "dosyalar": {"olcum_py_sha256": sha256(os.path.join(OUT, "olcum.py")), "db_sha256": beyan["taban"]["db_sha256"]},
}
with open(sonuc_path, "w") as f:
    json.dump(sonuc, f, indent=1, ensure_ascii=False)
    f.flush(); os.fsync(f.fileno())

print(json.dumps({k: sonuc[k] for k in ["dilimler", "ayrisma", "kill1_damga", "betimleyici_breadth_seyri_HUKUM_DEGIL"]},
                 indent=1, ensure_ascii=False))
print(f"\nOK -> {sonuc_path}")

"""WP3/28d KART-KANITI · rejim tarihçesi SAYIMI (analiz; kartı Rol-1 yazacak).

NE SAYAR (hüküm YOK, eşik önerisi YOK — envanter + sayım):
  (1) 2022-01-01 → yerel son bar: gün-başına rejim etiketi, ÜRETİM KOD YOLUYLA birebir:
      `meridian.regime.classify(idx.loc[:d])` — kapı yolu backtest.py:373, canlı yol loop.py:1592,
      ikisi de FETCH_START=2021-01-01'den genişleyen dilimle çağırır (dataset.py:40,199).
  (2) Ham-dal ayrıştırması: classify'ın high_vol BİNDİRMESİNDEN ÖNCEKİ dalı (trend_up/
      trend_down/chop) yerelde yeniden türetilir ve classify çıktısıyla TUTARLILIK ASSERT edilir
      (kopya-mantık sapması sessiz kalamaz).
  (3) chop iddiası: "2025-07-01'den beri chop = 0 mı?" — sayıyla.
  (4) high_vol bindirmesinin chop'u YEMESİ: ham-dal=chop iken etiket=high_vol olan günler.
  (5) trend_up günlerinde üç koşulun marj dağılımı (dedektör-mü-piyasa-mı ayrıştırması için
      ham veri): m1=c/sma50−1, m2=sma50/sma200−1, m3=sma200/sma200_prev−1.
  (6) Eşik ADAYI ENVANTERİ: dedektördeki sayısal sabitler + her birinin üzerinde kesim yapılacak
      ham istatistikler. SEÇİM YOK — karta kalır.

Çıktı: sonuc_rejim_tarihce.json + gunluk_rejim.csv (gün-başına ham seri).
UYDURMA YASAĞI: ölçülemeyen alan null + neden.
"""
from __future__ import annotations
import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from meridian import regime as regime_mod          # noqa: E402
from meridian import indicators as ind             # noqa: E402

FETCH_START = "2021-01-01"     # dataset.py:40 — üretim dünyasının seri başlangıcı
COUNT_START = "2022-01-01"     # dataset.py:102 IS_START — sayım penceresi başı
CLAIM_DATE = "2025-07-01"      # iddia: bu tarihten beri chop hiç oluşmadı
OUT_DIR = Path(__file__).resolve().parent


def load_spy() -> pd.DataFrame:
    df = pd.read_csv(REPO / "state/bars/spy.csv", parse_dates=["date"])
    df = df[df["date"] >= FETCH_START].reset_index(drop=True)
    return df


def raw_branch(sl: pd.DataFrame) -> tuple[str, dict]:
    """classify'ın high_vol bindirmesinden ÖNCEKİ dalını ve marjları türetir.
    classify (meridian/regime.py:75-90) ile AYNI aritmetik — tutarlılık main'de assert edilir."""
    close = sl["close"]
    sma50 = ind.sma(close, 50).iloc[-1]
    s200 = ind.sma(close, 200)
    sma200 = s200.iloc[-1]
    sma200_prev = s200.shift(20).iloc[-1]
    c = close.iloc[-1]
    atr14 = ind.atr(sl, 14).iloc[-1]
    atr_pct = atr14 / c if c else 0.0
    aps = (ind.atr(sl, 14) / close).dropna()
    hi_thr = aps.quantile(0.80) if len(aps) > 30 else atr_pct
    # genişleyen yüzdelik: bugünkü atr_pct serinin neresinde
    atr_pct_rank = float((aps <= atr_pct).mean()) if len(aps) else None
    if pd.isna(sma50) or pd.isna(sma200) or pd.isna(sma200_prev):
        rb = "chop_nan"
    elif c > sma50 and sma50 > sma200 and sma200 >= sma200_prev:
        rb = "trend_up"
    elif c < sma50 and sma50 < sma200:
        rb = "trend_down"
    else:
        rb = "chop"
    m = {
        "m1_c_sma50": float(c / sma50 - 1.0) if not pd.isna(sma50) else None,
        "m2_sma50_sma200": float(sma50 / sma200 - 1.0) if not (pd.isna(sma50) or pd.isna(sma200)) else None,
        "m3_sma200_slope": float(sma200 / sma200_prev - 1.0) if not (pd.isna(sma200) or pd.isna(sma200_prev)) else None,
        "atr_pct": float(atr_pct), "hi_vol_thresh": float(hi_thr),
        "atr_pct_rank": atr_pct_rank,
        "high_vol_flag": bool(atr_pct >= hi_thr and atr_pct > 0.0),
    }
    return rb, m


def main() -> None:
    df = load_spy()
    dates = df["date"]
    rows = []
    n_assert = 0
    for i in range(len(df)):
        d = dates.iloc[i]
        if str(d.date()) < COUNT_START:
            continue
        sl = df.iloc[: i + 1]
        label, metrics = regime_mod.classify(sl)
        rb, m = raw_branch(sl)
        # TUTARLILIK: ham-dal + bindirme = classify etiketi (kopya-mantık sapmasına çivi)
        expect = rb if rb != "chop_nan" else "chop"
        if m["high_vol_flag"] and expect != "trend_up":
            expect = "high_vol"
        if len(sl) < regime_mod.TREND_WARMUP:
            expect = "chop"  # ısınma dalı (regime.py:66-71) — 2021 başlangıçla beklenmez
        assert expect == label, f"{d.date()}: türetilen {expect} != classify {label}"
        n_assert += 1
        rows.append({"date": str(d.date()), "regime": label, "raw_branch": rb, **m})

    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "gunluk_rejim.csv", index=False)

    def dist(sub: pd.DataFrame) -> dict:
        return dict(Counter(sub["regime"]))

    per_year = {y: dist(g) for y, g in out.groupby(out["date"].str[:4])}
    since = out[out["date"] >= CLAIM_DATE]
    chop_days = out[out["regime"] == "chop"]
    raw_chop = out[out["raw_branch"] == "chop"]
    eaten = out[(out["raw_branch"] == "chop") & (out["regime"] == "high_vol")]
    eaten_since = eaten[eaten["date"] >= CLAIM_DATE]
    raw_chop_since = raw_chop[raw_chop["date"] >= CLAIM_DATE]
    tu_since = since[since["regime"] == "trend_up"]

    def qtiles(s: pd.Series) -> dict | None:
        s = s.dropna()
        if not len(s):
            return None
        return {"n": int(len(s)), "min": round(float(s.min()), 5),
                "p05": round(float(s.quantile(0.05)), 5), "p25": round(float(s.quantile(0.25)), 5),
                "median": round(float(s.median()), 5), "p75": round(float(s.quantile(0.75)), 5),
                "max": round(float(s.max()), 5)}

    # trend_up gününü chop'a düşürecek EN YAKIN koşul: min(m1, m2, m3) — sayım, eşik değil
    tu_margin_min = tu_since[["m1_c_sma50", "m2_sma50_sma200", "m3_sma200_slope"]].min(axis=1)

    sonuc = {
        "kart_kaniti": "WP3/28d — chop rejimi tarihçesi sayımı (hüküm yok)",
        "olcum_ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "kod_yolu": {
            "siniflayici": "meridian/regime.py:41 classify (üretim fonksiyonunun KENDİSİ çağrıldı)",
            "kapi_yolu": "meridian/backtest.py:373 build_regime_json(idx.loc[:d]) → classify",
            "canli_yolu": "meridian/loop.py:1592 build_regime_json(idx.loc[:d]) → classify",
            "seri_baslangici": FETCH_START + " (dataset.py:40 FETCH_START; genişleyen dilim)",
            "islem_etiketi": "broker pos.regime_at_plan → backtest.py:723 _regime_slice",
        },
        "veri": {"kaynak": "state/bars/spy.csv (yerel)", "ilk_bar": str(dates.iloc[0].date()),
                 "son_bar": str(dates.iloc[-1].date()), "sayim_penceresi": [COUNT_START, str(dates.iloc[-1].date())],
                 "gun_sayisi": int(len(out)), "tutarlilik_assert": n_assert,
                 "eksik_kuyruk_notu": "yerel seri son_bar'da biter; bugüne kadarki kuyruk canli_cek ile ayrıca sayılır"},
        "gun_basina_dagilim": {
            "toplam": dist(out), "yil_basina": per_year,
            "iddia_penceresi": {"pencere": [CLAIM_DATE, str(dates.iloc[-1].date())],
                                "gun": int(len(since)), "dagilim": dist(since)},
        },
        "chop_sayimi": {
            "toplam_chop_gunu": int(len(chop_days)),
            "son_chop_gunu": (chop_days["date"].iloc[-1] if len(chop_days) else None),
            "claim_sonrasi_chop": int((since["regime"] == "chop").sum()),
            "chop_gunleri_2025": sorted(chop_days[chop_days["date"] >= "2025-01-01"]["date"].tolist()),
        },
        "ham_dal_ayristirmasi": {
            "aciklama": "raw_branch = high_vol bindirmesinden ÖNCEKİ dal (regime.py:82-88); "
                        "bindirme: high_vol ve dal!=trend_up ise etiket high_vol olur (regime.py:89-90)",
            "toplam_ham_dal": dict(Counter(out["raw_branch"])),
            "claim_sonrasi_ham_dal": dict(Counter(since["raw_branch"])),
            "high_vol_yedigi_chop_toplam": int(len(eaten)),
            "high_vol_yedigi_chop_claim_sonrasi": int(len(eaten_since)),
            "high_vol_yedigi_chop_gunleri_claim_sonrasi": sorted(eaten_since["date"].tolist()),
            "ham_chop_claim_sonrasi_gunleri": sorted(raw_chop_since["date"].tolist()),
        },
        "trend_up_marjlari_claim_sonrasi": {
            "aciklama": "trend_up'ı bozmaya EN YAKIN koşulun marjı (min m1,m2,m3); sayım — eşik değil",
            "m1_c_sma50": qtiles(tu_since["m1_c_sma50"]),
            "m2_sma50_sma200": qtiles(tu_since["m2_sma50_sma200"]),
            "m3_sma200_slope": qtiles(tu_since["m3_sma200_slope"]),
            "min_marj": qtiles(tu_margin_min),
            "min_marj_altinda_gun": {esik: int((tu_margin_min < float(esik)).sum())
                                     for esik in ("0.001", "0.0025", "0.005", "0.01", "0.02")},
        },
        "atr_pct_ham_chop_gunlerinde": qtiles(raw_chop["atr_pct_rank"]),
        "esik_adayi_envanteri": {
            "beyan": "ENVANTER — seçim/öneri YOK; hangi eşik donacaksa kart (Rol-1) seçer",
            "dedektor_sabitleri": {
                "sma_kisa": 50, "sma_uzun": 200, "egim_penceresi_bar": 20,
                "atr_penceresi": 14, "hi_vol_quantile": 0.80, "hi_vol_min_gozlem": 30,
                "TREND_WARMUP": regime_mod.TREND_WARMUP, "ret20_penceresi": 21,
                "kaynak": "meridian/regime.py:41-104 (classify gövdesi)",
            },
            "uzerinde_kesilecek_ham_istatistikler": {
                "claim_sonrasi_trend_up_min_marj_dagilimi": qtiles(tu_margin_min),
                "claim_sonrasi_atr_pct_rank": qtiles(since["atr_pct_rank"]),
                "tum_pencere_atr_pct_rank_ham_chopta": qtiles(raw_chop["atr_pct_rank"]),
            },
        },
    }
    (OUT_DIR / "sonuc_rejim_tarihce.json").write_text(
        json.dumps(sonuc, indent=2, ensure_ascii=False))
    print(json.dumps(sonuc["gun_basina_dagilim"], ensure_ascii=False))
    print("chop:", sonuc["chop_sayimi"]["toplam_chop_gunu"],
          "son:", sonuc["chop_sayimi"]["son_chop_gunu"],
          "claim_sonrasi:", sonuc["chop_sayimi"]["claim_sonrasi_chop"])


if __name__ == "__main__":
    main()

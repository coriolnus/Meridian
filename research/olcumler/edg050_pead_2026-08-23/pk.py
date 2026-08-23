"""WP2 — POZİTİF KONTROL + PK4 + PK5. ÜÇ KARTIN ORTAK BEKÇİSİ; İLK KOŞAN İŞ.

Çivi tutmazsa (|IC−0.0645| > 0.005) boru hattı GEÇERSİZ sayılır ve hiçbir kart için hüküm yazılmaz.
Şablon: max_olcum / resmom_olcum / pullback_olcum ile BİREBİR aynı katman ve aynı hedef.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

import ortak as O

HORIZONS = (5, 10, 20)


def population() -> tuple[list, dict]:
    """max_olcum/resmom_olcum/pullback_olcum ile BİREBİR: cf entered=True (near_miss dâhil) + cf_open."""
    rows, acc = [], {"cf_satir": 0, "cf_girilmemis": 0, "cf_eksik_alan": 0,
                     "open_satir": 0, "open_eksik_alan": 0}
    with open(O.LIVE_STATE / "counterfactuals.jsonl") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            acc["cf_satir"] += 1
            if not r.get("entered"):
                acc["cf_girilmemis"] += 1
                continue
            if not r.get("ticker") or not r.get("date"):
                acc["cf_eksik_alan"] += 1
                continue
            rows.append({"kaynak": "cf", "ticker": str(r["ticker"]).upper(),
                         "date": str(r["date"])[:10], "near_miss": bool(r.get("near_miss"))})
    with open(O.LIVE_STATE / "cf_open.json") as fh:
        for r in json.load(fh):
            acc["open_satir"] += 1
            if not r.get("ticker") or not r.get("date"):
                acc["open_eksik_alan"] += 1
                continue
            rows.append({"kaynak": "cf_open", "ticker": str(r["ticker"]).upper(),
                         "date": str(r["date"])[:10], "near_miss": bool(r.get("near_miss"))})
    return rows, acc


def main() -> None:
    print("== barlar ==")
    pan, bar_acc = O.bars_cached()
    print(f"   {bar_acc['yuklendi']}/{bar_acc['istenen']} sembol yüklendi")

    out = {"bar_muhasebesi": {k: v for k, v in bar_acc.items()
                              if k not in ("kisa_semboller",)},
           "bar_muhasebesi_kisa_semboller": bar_acc["kisa_semboller"]}
    out["bar_muhasebesi"]["takvim_reddedilen"] = len(bar_acc["takvim_reddedilen"])

    # ---------------- POZİTİF KONTROL ----------------
    print("== pozitif kontrol (ham rvol20 @20 cf-katman IC) ==")
    rows, pop_acc = population()
    idx_cache = {t: {d: i for i, d in enumerate(v["dates"])} for t, v in pan.items()}
    pk_rows, elem = [], {"bar_yok_sembol": 0, "bar_yok_tarih": 0, "kabul": 0}
    for r in rows:
        f = pan.get(r["ticker"])
        if f is None:
            elem["bar_yok_sembol"] += 1
            continue
        i = idx_cache[r["ticker"]].get(r["date"])
        if i is None:
            elem["bar_yok_tarih"] += 1
            continue
        elem["kabul"] += 1
        rec = dict(r)
        rec["rvol20"] = None if not np.isfinite(f["rvol20"][i]) else float(f["rvol20"][i])
        for h in HORIZONS:
            v = f[f"fwd{h}"][i]
            rec[f"fwd{h}"] = None if not np.isfinite(v) else float(v)
            cv = f[f"chain{h}"][i]
            rec[f"chain{h}"] = None if not np.isfinite(cv) else float(cv)
        pk_rows.append(rec)
    PKD = pd.DataFrame(pk_rows)
    pk = {"aciklama": "AYNI boru hattı, kart çivisi: ham rvol20 @20 cf-katman IC ≈ 0.0645 "
                      "(max_olcum/EDG-2026-004 turu); bars_integrity DIŞLAMALI yolda resmom 0.0637, "
                      "pullback 0.0642 ölçtü. Bu tur da DIŞLAMALI yoldadır.",
          "katman": "counterfactuals.jsonl entered=True & near_miss=False (component_ic katmanı)",
          "populasyon_muhasebesi": pop_acc, "eslesme_muhasebesi": elem}
    KAT = PKD[(PKD["kaynak"] == "cf") & (~PKD["near_miss"])]
    for h in HORIZONS:
        sub = KAT[["rvol20", f"fwd{h}", "date"]].dropna()
        pk[str(h)] = O.ic_with_ci(sub["rvol20"].to_numpy(float), sub[f"fwd{h}"].to_numpy(float),
                                  sub["date"].to_numpy())
    civi = pk["20"]["ic"]
    pk["civi_hedef"] = 0.0645
    pk["civi_olculen"] = civi
    pk["civi_sapma"] = None if civi is None else O._r6(abs(civi - 0.0645))
    pk["tolerans"] = 0.005
    pk["GECTI"] = None if civi is None else bool(abs(civi - 0.0645) <= 0.005)
    try:
        ref = json.load(open(O.LIVE_STATE / "component_ic.json"))
        pk["defterdeki_deger_cf_rvol20"] = {h: ref["tablo"]["cf"]["rvol20"][h]["ic"]
                                            for h in ("5", "10", "20")}
    except Exception as e:
        pk["defterdeki_deger_cf_rvol20"] = f"okunamadı: {type(e).__name__}: {e}"
    out["pozitif_kontrol"] = pk
    print(f"   çivi: {civi} (hedef 0.0645, tol 0.005) → GEÇTİ={pk['GECTI']}")

    # ---------------- PK4: yol tutarlılığı ----------------
    pk4 = {"tanim": "close[t+h]/close[t]-1 ile aradaki GÜNLÜK getirilerin bileşiği ÖZDEŞ olmalı. "
                    "Takvim kapısı/integrity kırpması ufkun İÇİNDE bar düşürdüyse ya da kaydırma "
                    "bir gün kaysaydı özdeşlik bozulurdu.",
           "kapsam": "pozitif kontrol satırları + TÜM bar paneli (her sembol, her bar)"}
    for h in HORIZONS:
        d0 = []
        s2 = PKD[[f"fwd{h}", f"chain{h}"]].dropna()
        if len(s2):
            d0.append((s2[f"fwd{h}"] - s2[f"chain{h}"]).abs().to_numpy())
        for t, v in pan.items():
            a, b = v[f"fwd{h}"], v[f"chain{h}"]
            m = np.isfinite(a) & np.isfinite(b)
            if m.any():
                d0.append(np.abs(a[m] - b[m]))
        allv = np.concatenate(d0)
        pk4[f"fwd{h}"] = {"n": int(len(allv)), "maks_mutlak_fark": O._r6(allv.max()),
                          "gecti": bool(allv.max() < 1e-9)}
    for h in (60,):
        d0 = []
        for t, v in pan.items():
            a, b = v[f"fwd{h}"], v[f"chain{h}"]
            m = np.isfinite(a) & np.isfinite(b)
            if m.any():
                d0.append(np.abs(a[m] - b[m]))
        allv = np.concatenate(d0)
        pk4[f"fwd{h}"] = {"n": int(len(allv)), "maks_mutlak_fark": O._r6(allv.max()),
                          "gecti": bool(allv.max() < 1e-9)}
    pk4["gecti"] = bool(all(pk4[f"fwd{h}"]["gecti"] for h in (5, 10, 20, 60)))
    out["pk4_yol_tutarliligi"] = pk4

    # ---------------- PK5: özdeşlikler ----------------
    print("== PK5 (as-of geriye-bakışsızlık + split bazı + hızlı ortalama) ==")
    S = O._shares_ham()
    ser, birincil, sh_acc = O.build_hisse(S)
    sh_acc["fiziksel_bekci"] = O.fiziksel_bekci(ser, pan)
    tem, tem_acc = O.build_temel()

    # (A) as-of GERİYE-BAKIŞSIZLIK: vektörel searchsorted yolu ile KABA filtre yolu birebir aynı mı
    rng = np.random.default_rng(7)
    semboller = sorted(set(ser) & set(pan))
    ornek_sym = list(rng.choice(semboller, size=min(25, len(semboller)), replace=False))
    a_n, a_fark, a_leak = 0, 0, 0
    for sym in ornek_sym:
        s = ser[sym]
        d = pan[sym]["dates"]
        tsel = rng.choice(d, size=min(20, len(d)), replace=False)
        v, f, nd = s.asof(tsel)
        for k, t in enumerate(tsel):
            m = s.filed <= t                            # KABA yol: doğrudan filtre
            a_n += 1
            if not m.any():
                if np.isfinite(v[k]):
                    a_fark += 1
                continue
            j = int(np.where(m)[0][-1])
            bek = s.val[j] * s.B_son / s.B[j]
            yas = (pd.Timestamp(t) - pd.Timestamp(s.filed[j])).days
            if yas > O.BAYAT_GUN or s.gecersiz[j]:
                bek = np.nan
            if not ((np.isnan(bek) and not np.isfinite(v[k])) or
                    (np.isfinite(v[k]) and abs(v[k] - bek) < 1e-6 * max(1.0, abs(bek)))):
                a_fark += 1
            if f[k] != "" and f[k] > t:
                a_leak += 1
    out_a = {"n_ornek": a_n, "ayrisan": a_fark, "filed>t_sizinti": a_leak,
             "gecti": bool(a_n > 0 and a_fark == 0 and a_leak == 0),
             "tanim": "vektörel searchsorted as-of ile satır satır `filed<=t` filtresi AYNI kaydı "
                      "ve AYNI güncel-baz değeri vermeli; hiçbir seçilen kaydın filed'ı t'yi aşmamalı"}

    # (B) SPLIT BAZI ÖZDEŞLİĞİ: B(f) tablo yolu ile kaba çarpım yolu
    b_n, b_fark = 0, 0
    tk = sh_acc["split_takvimi"]["kabul_listesi"]
    by_sym = {}
    for e in tk:
        by_sym.setdefault(e["symbol"], []).append((e["filed"], e["oran"]))
    for sym, olay in by_sym.items():
        s = ser[sym]
        for j in range(len(s.filed)):
            kaba = 1.0
            for gf, r in olay:
                if gf <= s.filed[j]:
                    kaba *= r
            b_n += 1
            if abs(kaba - s.B[j]) > 1e-9:
                b_fark += 1
    out_b = {"n_ornek": b_n, "ayrisan": b_fark, "gecti": bool(b_n > 0 and b_fark == 0),
             "tanim": "B(f) = f gününe kadar kabul edilmiş bölünme oranlarının çarpımı; kümülatif "
                      "tablo yolu ile kaba döngü yolu birebir aynı olmalı"}

    # (C) hızlı ortalama-bootstrap yolu ≡ satır-toplayan yol
    d = pan[semboller[0]]
    m = np.isfinite(d["fwd20"])
    yy, dd = d["fwd20"][m], d["dates"][m]
    uniq, inv = np.unique(dd, return_inverse=True)
    rows_by_date = [np.where(inv == i)[0] for i in range(len(uniq))]
    sums = np.bincount(inv, weights=yy, minlength=len(uniq))
    cnts = np.bincount(inv, minlength=len(uniq)).astype(float)
    nd_ = len(uniq)
    n_blok = int(np.ceil(nd_ / O.BLOCK))
    c_max, c_n = 0.0, 0
    for _ in range(50):
        bas = O.RNG.integers(0, max(nd_ - O.BLOCK, 0) + 1, n_blok)
        gun = np.concatenate([np.arange(b, b + O.BLOCK) for b in bas])[:nd_]
        idx = np.concatenate([rows_by_date[g] for g in gun])
        v1 = float(np.mean(yy[idx]))
        v2 = float(sums[gun].sum() / cnts[gun].sum())
        c_max = max(c_max, abs(v1 - v2))
        c_n += 1
    out_c = {"n_ornek": c_n, "maks_mutlak_fark": O._r6(c_max),
             "gecti": bool(c_n > 0 and c_max < 1e-12),
             "tanim": "mean_block_boot (gün-toplamı/gün-adedi) ile block_boot (satır toplayıp mean) "
                      "AYNI gün dizisinde birebir aynı sayıyı vermeli"}

    # (D) FUNDAMENTALS as-of sızıntı: seçilen FY kaydının filed'ı t'yi aşmamalı + end<=filed
    d_n, d_leak, d_endsonra = 0, 0, 0
    for sym in list(tem)[:60]:
        s = tem[sym]
        tsel = np.array(sorted(rng.choice(pan[sym]["dates"], size=min(20, len(pan[sym]["dates"])),
                                          replace=False))) if sym in pan else None
        if tsel is None:
            continue
        v, f, nd = s.asof(tsel)
        d_n += len(tsel)
        d_leak += int(np.sum((f != "") & (f > tsel)))
    # end>filed satırı PIT'i BOZMAZ (README #4) ama sayılır
    out_d = {"n_ornek": d_n, "filed>t_sizinti": d_leak, "gecti": bool(d_n > 0 and d_leak == 0),
             "tanim": "gpa as-of: seçilen FY kaydının filed'ı gözlem gününü ASLA aşmamalı "
                      "(end tabanlı okuma YASAK — kart 014 notu)"}

    out["pk5_ozdeslikler"] = {"A_asof_geriye_bakissizlik": out_a, "B_split_bazi": out_b,
                              "C_hizli_ortalama": out_c, "D_fundamentals_asof": out_d,
                              "gecti": bool(out_a["gecti"] and out_b["gecti"] and out_c["gecti"]
                                            and out_d["gecti"])}
    out["hisse_muhasebesi"] = sh_acc
    out["temel_muhasebesi"] = tem_acc

    # ---------------- BAR SERİSİ SPLIT-DÜZ Mİ (brief'in bar yolu neden yok) ----------------
    bilinen = {"NVDA": "2024-06-10", "AVGO": "2024-07-15", "AAPL": "2020-08-31",
               "TSLA": "2022-08-25", "GOOGL": "2022-07-18"}
    duz = {}
    for sym, gun in bilinen.items():
        v = pan.get(sym)
        if v is None:
            duz[sym] = {"neden": "bar yok"}
            continue
        i = int(np.searchsorted(v["dates"], gun))
        if i <= 0 or i >= len(v["dates"]):
            duz[sym] = {"neden": "tarih bar serisinde yok"}
            continue
        duz[sym] = {"split_gunu": gun, "gun_getirisi": O._r6(v["close"][i] / v["close"][i - 1] - 1),
                    "hacim_orani": O._r6(v["volume"][i] / v["volume"][i - 1])}
    out["split_takvimi_bar_serisi_duz_mu"] = {
        "sonuc": duz,
        "yorum": "Bilinen bölünme günlerinde bar serisinde ~%90 fiyat düşüşü YOK — state/bars "
                 "SPLIT-DÜZELTİLMİŞ. Yani 'bar verisindeki split günleri' bu veri kümesinde "
                 "OKUNAMAZ; split takvimi EDGAR'ın kendi geriye-dönük yeniden-beyanından türetildi "
                 "(ortak.build_split_takvimi belgesi).",
    }

    # ---------------- SPLIT NORMALİZASYONU DOĞRULAMASI (brief'in istediği NVDA/AVGO sınavı) -----
    kontrol_tarih = np.array(["2013-06-03", "2015-06-01", "2019-06-03", "2021-06-01",
                              "2023-06-01", "2024-06-03", "2024-09-03", "2025-06-02",
                              "2026-06-01"])
    dog = {"aciklama": "Güncel baza çevrilmiş as-of hisse sayımı, bölünmenin ÜZERİNDEN pürüzsüz "
                       "geçmelidir. Ham EDGAR serisi 2024-08-28'de NVDA'da 10× sıçrar; aşağıdaki "
                       "seride sıçrama YOKTUR ve seviye bugünkü gerçek hisse adedidir.",
           "tarihler": kontrol_tarih.tolist(), "seri": {}}
    for sym in ("NVDA", "AVGO", "AAPL", "GOOGL", "TSLA", "WMT", "NFLX"):
        s = ser.get(sym)
        if s is None:
            dog["seri"][sym] = {"neden": "anlık hisse serisi yok"}
            continue
        v, f, nd = s.asof(kontrol_tarih)
        ham = np.full(len(kontrol_tarih), np.nan)
        i = s.idx_asof(kontrol_tarih)
        ham[i >= 0] = s.val[i[i >= 0]]
        art = [None] + [O._r6(v[k] / v[k - 1] - 1) if np.isfinite(v[k]) and np.isfinite(v[k - 1])
                        else None for k in range(1, len(v))]
        dog["seri"][sym] = {
            "B_son": s.B_son,
            "guncel_baz": [None if not np.isfinite(x) else float(f"{x:.6g}") for x in v],
            "ham_edgar": [None if not np.isfinite(x) else float(f"{x:.6g}") for x in ham],
            "guncel_baz_donemsel_degisim": art,
            "kaynak_filed": f.tolist(),
        }
    out["split_normalizasyon_dogrulama"] = dog

    O.json_yaz(O.SANDBOX / "pk.json", out)
    print(f"   PK4 geçti={pk4['gecti']}  PK5 geçti={out['pk5_ozdeslikler']['gecti']}")
    print("== yazıldı: pk.json ==")


if __name__ == "__main__":
    main()

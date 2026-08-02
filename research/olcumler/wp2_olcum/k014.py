"""EDG-2026-014 · BRÜT KÂRLILIK (GP/Assets) — SALT-ÖLÇÜM, SANDBOX.

Kart: research/cards/EDG-2026-014-gross-profitability.yaml (status: registered).
"PIT'siz fundamentals proxy YASAK" yasası bu kartla İLK KEZ meşru aşılıyor: as-of YALNIZ `filed`
üzerinden okunur; `end` tabanlı okuma YASAK (sızıntı). KART DIŞINA ÖLÇÜM YOK.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import ortak as O

HORIZONS = (20, 60)
DILIM_PCT = 0.30                 # kart parameter_grid: üst %30 / alt %30
MIN_SEMBOL_AY = 2500             # kart kill#3
FINANS = {"financials", "reits"}  # "finans-dışı" tanı dilimi için (meridian.backtest.SECTORS)


def panel(pan, tem, OBS):
    parts, acc = [], {"sembol": 0, "gozlem_hucre": 0, "neden_sayimi": {}, "gecerli": 0,
                      "filed_gecikme_gun": [], "gp_kaynak_hucre": {}}
    for sym, v in pan.items():
        d = v["dates"]
        pos = np.searchsorted(d, OBS)
        pos_c = np.minimum(pos, len(d) - 1)
        ok = (pos < len(d)) & (d[pos_c] == OBS)
        idx = pos[ok]
        tdates = OBS[ok]
        if len(idx) == 0:
            continue
        acc["sembol"] += 1
        acc["gozlem_hucre"] += int(len(idx))
        row = {"date": tdates, "ticker": sym, "sektor": O.SECTORS.get(sym, "?")}
        for h in HORIZONS:
            row[f"fwd{h}"] = v[f"fwd{h}"][idx]
        s = tem.get(sym)
        if s is None:
            row["gpa"] = np.full(len(idx), np.nan)
            row["filed"] = ""
            acc["neden_sayimi"]["GP_hesaplanamayan_sembol"] = \
                acc["neden_sayimi"].get("GP_hesaplanamayan_sembol", 0) + len(idx)
        else:
            g, f, nd = s.asof(tdates)
            row["gpa"] = g
            row["filed"] = f
            for k, c in zip(*np.unique(nd[nd != ""], return_counts=True)):
                acc["neden_sayimi"][str(k)] = acc["neden_sayimi"].get(str(k), 0) + int(c)
            fin = np.isfinite(g)
            if fin.any():
                gg = (pd.to_datetime(tdates[fin]) - pd.to_datetime(f[fin].astype(str))).days
                acc["filed_gecikme_gun"].extend(gg.tolist())
                j = np.searchsorted(s.filed, tdates[fin], side="right") - 1
                for k, c in zip(*np.unique(s.kaynak[j], return_counts=True)):
                    acc["gp_kaynak_hucre"][str(k)] = acc["gp_kaynak_hucre"].get(str(k), 0) + int(c)
        parts.append(pd.DataFrame(row))
    D = pd.concat(parts, ignore_index=True)
    acc["gecerli"] = int(D["gpa"].notna().sum())
    gg = np.array(acc.pop("filed_gecikme_gun"), float)
    acc["filed_gecikme_ozeti"] = ({"n": int(len(gg)), "medyan": O._r6(np.median(gg)),
                                   "p10": O._r6(np.percentile(gg, 10)),
                                   "p90": O._r6(np.percentile(gg, 90)),
                                   "maks": O._r6(gg.max()), "negatif_n": int((gg < 0).sum())}
                                  if len(gg) else {"n": 0, "neden": "gözlem yok"})
    return D, acc


def dilimle(V, tab, etiket_ust, etiket_alt):
    V = V.copy()
    V["pct"] = V.groupby("date")["gpa"].rank(pct=True, method="first")
    V["dilim"] = np.where(V["pct"] > 1 - DILIM_PCT, etiket_ust,
                          np.where(V["pct"] <= DILIM_PCT, etiket_alt, "orta"))
    out, fazla = {}, {}
    for ad in (etiket_ust, etiket_alt):
        sub = V[V["dilim"] == ad]
        blok = {"n_sembol_ay": int(len(sub)), "n_gun": int(sub["date"].nunique()),
                "n_sembol": int(sub["ticker"].nunique()),
                "gpa_ort": O._r6(sub["gpa"].mean()), "gpa_medyan": O._r6(sub["gpa"].median()),
                "ufuklar": {}}
        for h in HORIZONS:
            s2 = sub[["date", f"fwd{h}"]].dropna()
            if len(s2) < O.MIN_SLICE:
                blok["ufuklar"][str(h)] = {"n": int(len(s2)), "neden": f"n<{O.MIN_SLICE}"}
                continue
            y = s2[f"fwd{h}"].to_numpy(float)
            dts = s2["date"].to_numpy()
            base = s2["date"].map(tab[h]).to_numpy(float)
            ok = np.isfinite(base)
            blok["ufuklar"][str(h)] = {
                "ham": O.mean_with_ci(y, dts),
                "kendi_evren_fazlasi": O.mean_with_ci((y - base)[ok], dts[ok]),
                "kendi_evren_fazlasi_blok3": O.mean_with_ci((y - base)[ok], dts[ok], blok=3),
            }
            fazla[(ad, h)] = ((y - base)[ok], dts[ok])
        out[ad] = blok
    yay = {}
    for h in HORIZONS:
        if (etiket_ust, h) in fazla and (etiket_alt, h) in fazla:
            ya, da = fazla[(etiket_ust, h)]
            yb, db = fazla[(etiket_alt, h)]
            yay[str(h)] = O.fark_with_ci(ya, da, yb, db)
    return out, yay, V


def main() -> None:
    pan, bar_acc = O.bars_cached()
    tem, tem_acc = O.build_temel()
    takvim = O.ortak_takvim(pan)
    OBS = O.ay_sonu_gunleri(takvim)
    print(f"== 014: {len(OBS)} aylık gözlem günü, {len(pan)} sembol ==")

    D, pacc = panel(pan, tem, OBS)
    sonuc = {
        "kart": "EDG-2026-014", "aile": "gross_profitability",
        "olcum_tarihi": pd.Timestamp.now("UTC").isoformat(), "sandbox": str(O.SANDBOX),
        "DURUM": None,
        "kart_metni_uygulamasi": {
            "pit": "as-of YALNIZ `filed` üzerinden (filed<=t son FY kaydı). `end<=t` okuması "
                   "KULLANILMADI — README §1: end filtresi PIT DEĞİLDİR.",
            "fy_secimi": "donem_turu == 'yillik' (donem_gun 316–400) akış kalemleri; Assets "
                         "donem_turu == 'anlik'.",
            "gp_etiket_onceligi": "GrossProfit varsa o; yoksa (Revenues → RevenueFromContract"
                                  "...Excluding → ...Including) − (CostOfRevenue → "
                                  "CostOfGoodsAndServicesSold). REIT gelir-etiketi tuzağı: "
                                  "`Revenues` ÖNCE (tutarsizlik.json #1).",
            "assets": "AYNI dosyalamadan (aynı symbol+filed) ve AYNI `end`; eşleşmeyen gözlem "
                      "DÜŞÜRÜLDÜ (uydurma yok).",
            "temizlik": "unit=='USD' (MPWR FY2012 AFN satırı düşer) & val>0 (kart: 'val<=0 "
                        "düşülür' — GrossProfit etiketinin negatif satırları da bu kuralla düşer; "
                        "sayısı muhasebede).",
            "bayatlik_bekcisi": "son FY dosyalaması gözlem gününden 550 günden eskiyse None "
                                "('bayat_FY_serisi') — companyfacts'in kendi gecikmesi "
                                "(tutarsizlik.json #6) sessizce eski veriyle karar aldırmasın.",
            "gpa": "gp / assets",
            "gozlem": "her takvim ayının SON işlem günü",
            "dilim": f"aynı gün kesitinde gpa üst %{int(DILIM_PCT*100)} / alt %{int(DILIM_PCT*100)}",
            "taban": "kart: aynı-gün GP-ALT-KÜMESİ ortalaması (kendi evreninin tabanı — EDG-009 "
                     "dersi), tüm evren DEĞİL",
            "evren_beyani": "GP-hesaplanabilir alt-küme. SEKTÖR ÇARPIKLIĞI BEYANLI: banka/sigorta/"
                            "REIT satış-maliyeti yayımlamaz (tutarsizlik.json → "
                            "brutkar_ve_maliyet_yok). Hüküm 'bu alt-kümede' okunur.",
            "ci": f"{O.BLOCK} ardışık gözlem günü blok-bootstrap (%95, {O.BOOT} tekrar); aylık "
                  f"panelde {O.BLOCK} ay — 60g örtüşmesinden GENİŞ, muhafazakâr. 3 aylık blok "
                  f"tanı olarak ayrıca verildi.",
            "maliyet": f"{O.MALIYET_BPS}bps tek-yön; hüküm BRÜT üzerinden",
        },
        "bar_muhasebesi": {k: v for k, v in bar_acc.items() if k != "kisa_semboller"},
        "temel_muhasebesi": tem_acc,
        "panel_muhasebesi": pacc,
    }
    sonuc["bar_muhasebesi"]["takvim_reddedilen"] = len(bar_acc["takvim_reddedilen"])

    kill3 = {"gecerli_sembol_ay": pacc["gecerli"], "esik": MIN_SEMBOL_AY,
             "yeterli": bool(pacc["gecerli"] >= MIN_SEMBOL_AY)}
    sonuc["kill3_ornekem"] = kill3
    if not kill3["yeterli"]:
        sonuc["DURUM"] = "OLCULMEDI"
        sonuc["neden"] = (f"kart kill#3: geçerli sembol-ay {pacc['gecerli']} < {MIN_SEMBOL_AY} — "
                          f"tanım GEVŞETİLMEZ, kart ASKIDA (K harcanmaz)")
        O.json_yaz(O.SANDBOX / "sonuc_014.json", sonuc)
        print("== KILL#3: askı ==")
        return

    V0 = D[D["gpa"].notna()].copy()
    kesit = V0.groupby("date").size()
    kullanilan = kesit[kesit >= O.MIN_KESIT].index
    V = V0[V0["date"].isin(kullanilan)].copy()
    tab = {}
    for h in HORIZONS:                       # KENDİ evreninin tabanı (kart)
        tab[h] = V[["date", f"fwd{h}"]].dropna().groupby("date")[f"fwd{h}"].mean()
    sonuc["kesit_muhasebesi"] = {
        "gozlem_gunu_toplam": int(D["date"].nunique()),
        "gecerli_gpa_gunu": int(V0["date"].nunique()),
        "kesit_yeterli_gun": int(len(kullanilan)), "min_kesit": O.MIN_KESIT,
        "kesit_buyuklugu": {"medyan": O._r6(kesit.median()), "min": int(kesit.min()),
                            "maks": int(kesit.max())},
        "tarih_araligi": [str(V["date"].min()), str(V["date"].max())],
        "gp_altkume_sembol_n": int(V["ticker"].nunique()),
        "gpa_dagilimi": {q: O._r6(V["gpa"].quantile(q))
                         for q in (0.01, 0.1, 0.3, 0.5, 0.7, 0.9, 0.99)},
        "sektor_dagilimi": V.groupby("ticker")["sektor"].first().value_counts().to_dict(),
    }

    # kapsam tanısı: README §3 "F ∧ G = 184/251" ile bu ölçümün alt-kümesi neden ayrışıyor
    Fx = pd.read_csv(O.EDGAR / "fundamentals.csv.gz")
    evren = set(O.dat.REPLAY_UNIVERSE)
    gp_var = set(Fx[Fx.tag == "GrossProfit"].symbol) | (
        set(Fx[Fx.tag.isin(O.GELIR_ONCELIK)].symbol) & set(Fx[Fx.tag.isin(O.MALIYET_ONCELIK)].symbol))
    readme_altkume = (gp_var & set(Fx[Fx.tag == "Assets"].symbol) & evren)
    sonuc["kapsam_tanisi"] = {
        "README_F_ve_G_evrende": len(readme_altkume),
        "bu_olcumde_gpa_uretebilen": int(V0[V0["gpa"].notna()]["ticker"].nunique()),
        "aradaki_semboller": sorted(readme_altkume - set(V0[V0["gpa"].notna()]["ticker"])),
        "neden": "README kapsamı 'etiket var mı' sorusunu sorar; bu ölçüm ek olarak FY "
                 "(donem_turu=='yillik') VE aynı dosyalamada Assets VE val>0 ister. Aradaki "
                 "semboller bu üç şarttan birini sağlamıyor.",
        "yil_basina_kesit": V0[V0["gpa"].notna()].assign(yil=lambda x: x["date"].str.slice(0, 4))
                              .groupby("yil")["ticker"].nunique().to_dict(),
    }

    dilim, yay, V = dilimle(V, tab, "gpa_ust_30pct", "gpa_alt_30pct")
    sonuc["i_dilim_tablosu"] = dilim
    sonuc["ii_yayilim_ust_eksi_alt"] = yay

    # beşli dilim TANI (CI yok — K harcanmaz)
    V["q5"] = V.groupby("date")["gpa"].transform(
        lambda s: pd.qcut(s.rank(method="first"), 5, labels=False, duplicates="drop"))
    q5 = {}
    for h in HORIZONS:
        g = V[["q5", "date", "gpa", f"fwd{h}"]].dropna()
        g = g.assign(fazla=g[f"fwd{h}"].to_numpy(float) - g["date"].map(tab[h]).to_numpy(float))
        g = g.dropna(subset=["fazla"])
        q5[str(h)] = {str(int(k)): {"n": int(len(v)), "fazla_ort": O._r6(v["fazla"].mean()),
                                    "gpa_ort": O._r6(v["gpa"].mean())}
                      for k, v in g.groupby("q5")}
    sonuc["iii_besli_dilim_TANI"] = {"not": "0 = en düşük gpa, 4 = en yüksek. CI BİLEREK yok — "
                                            "hüküm bacağı değil, K harcanmaz.", "ufuklar": q5}

    # ---------------- SEKTÖR-DUYARLILIK (kart guard: TANI, eşik DEĞİL) ----------------
    NF = V0[~V0["sektor"].isin(FINANS)].copy()
    kesit2 = NF.groupby("date").size()
    NF = NF[NF["date"].isin(kesit2[kesit2 >= O.MIN_KESIT].index)].copy()
    tab_nf = {h: NF[["date", f"fwd{h}"]].dropna().groupby("date")[f"fwd{h}"].mean()
              for h in HORIZONS}
    dilim_nf, yay_nf, _ = dilimle(NF, tab_nf, "gpa_ust_30pct_FINANSDISI",
                                  "gpa_alt_30pct_FINANSDISI")
    sonuc["iv_sektor_duyarliligi_TANI"] = {
        "not": "kart guard: 'finans-dışı alt-küme aynı yönde mi — EŞİK DEĞİL, TANI'. Finans = "
               "meridian.backtest.SECTORS içinde {financials, reits}. Kendi tabanı kendi "
               "alt-kümesinden. HÜKME GİRMEZ, K harcanmaz.",
        "finansdisi_sembol_n": int(NF["ticker"].nunique()),
        "GP_altkumesinde_kalan_finans_sembol": sorted(
            V0[V0["sektor"].isin(FINANS)]["ticker"].unique().tolist()),
        "dilim": dilim_nf, "yayilim": yay_nf}

    # ---------------- HÜKÜM ÖNERİSİ ----------------
    def leg(ad, h):
        return dilim[ad]["ufuklar"].get(str(h), {}).get("kendi_evren_fazlasi", {})

    u60, u20 = leg("gpa_ust_30pct", 60), leg("gpa_ust_30pct", 20)
    a60, a20 = leg("gpa_alt_30pct", 60), leg("gpa_alt_30pct", 20)
    y60 = yay.get("60", {})
    y20 = yay.get("20", {})
    bacak1 = bool(u60.get("pozitif_anlamli"))
    bacak2 = bool(y60.get("pozitif_anlamli"))
    ters = bool(u60.get("negatif_anlamli") or y60.get("negatif_anlamli"))
    bilgisiz = bool(u20.get("anlamli") is False and u60.get("anlamli") is False and
                    y20.get("anlamli") is False and y60.get("anlamli") is False)
    hukum = {
        "kart_success_metric": "üst-dilim fazlası @60 anlamlı POZİTİF (CI 0-dışı; @20 "
                               "destekleyici) VE üst−alt yayılımı pozitif anlamlı",
        "bacaklar": {
            "ust@60": {k: u60.get(k) for k in ("n", "ort", "ci", "anlamli", "pozitif_anlamli",
                                               "negatif_anlamli")},
            "ust@20": {k: u20.get(k) for k in ("n", "ort", "ci", "anlamli")},
            "alt@60": {k: a60.get(k) for k in ("n", "ort", "ci", "anlamli")},
            "alt@20": {k: a20.get(k) for k in ("n", "ort", "ci", "anlamli")},
            "yayilim@60": y60, "yayilim@20": y20,
        },
        "bacak1_ust60_pozitif_anlamli": bacak1,
        "bacak2_yayilim60_pozitif_anlamli": bacak2,
        "success_metric_KARSILANDI": bool(bacak1 and bacak2),
        "kill1_ust_ve_yayilim_20_60_CI_0_ici": bilgisiz,
        "kill2_yon_ters_anlamli": ters,
        "kill3_ornek_yetersiz": bool(not kill3["yeterli"]),
    }
    if hukum["success_metric_KARSILANDI"]:
        hukum["oneri"] = "SUCCESS — kart ölçütü karşılandı"
    elif ters:
        hukum["oneri"] = "ARŞİV — kill#2 (yön ters-anlamlı; 'bu evrende ters' + not)"
    elif bilgisiz:
        hukum["oneri"] = "ARŞİV — kill#1 (üst dilim ve yayılım @20+@60 CI-0-içi, bilgisiz)"
    else:
        hukum["oneri"] = "KARMA — bacaklar ayrışıyor, hüküm Rol-1'de"
    sonuc["hukum_onerisi"] = hukum
    sonuc["DURUM"] = "OLCULDU"

    O.json_yaz(O.SANDBOX / "sonuc_014.json", sonuc)
    V.to_csv(O.SANDBOX / "panel_014.csv.gz", index=False, compression="gzip")
    print(f"   geçerli sembol-ay={pacc['gecerli']}  öneri={hukum['oneri']}")


if __name__ == "__main__":
    main()

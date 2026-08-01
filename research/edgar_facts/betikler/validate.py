"""Kapsam + tutarsizlik + spot dogrulama. Hukum YOK; yalniz sayim ve tarif."""
import json, os, statistics as st
from datetime import date

import pandas as pd

WORK = os.path.dirname(os.path.abspath(__file__))
REPO = "/Users/erdemozturk/AI-Trading"
OUT = os.path.join(REPO, "research/edgar_facts")

SHARE_TAGS = ["EntityCommonStockSharesOutstanding", "CommonStockSharesOutstanding",
              "CommonStockSharesIssued"]
REV_TAGS = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
            "RevenueFromContractWithCustomerIncludingAssessedTax"]
COST_TAGS = ["CostOfRevenue", "CostOfGoodsAndServicesSold"]


def d(s):
    y, m, dd = str(s).split("-")
    return date(int(y), int(m), int(dd))


def lag_days(df):
    return (pd.to_datetime(df["filed"]) - pd.to_datetime(df["end"])).dt.days


def kapsam(df, universe):
    rows = []
    for tag, g in df.groupby("tag"):
        gu = g[g["symbol"].isin(universe)]
        lg = lag_days(g)
        rows.append({
            "tag": tag,
            "sembol_n_tum": g["symbol"].nunique(),
            "sembol_n_evren251": gu["symbol"].nunique(),
            "satir": len(g),
            "end_min": g["end"].min(), "end_max": g["end"].max(),
            "filed_min": g["filed"].min(), "filed_max": g["filed"].max(),
            "gecikme_medyan_gun": float(lg.median()),
            "gecikme_p10": float(lg.quantile(.10)), "gecikme_p90": float(lg.quantile(.90)),
            "gecikme_negatif_n": int((lg < 0).sum()),
            "birimler": ",".join(sorted(g["unit"].unique())),
            "form_ilk5": ",".join(g["form"].value_counts().head(5).index.astype(str)),
        })
    return pd.DataFrame(rows).sort_values("tag")


def main():
    sh = pd.read_csv(os.path.join(WORK, "shares_outstanding.csv"), dtype={"fy": "Int64"})
    fu = pd.read_csv(os.path.join(WORK, "fundamentals.csv"), dtype={"fy": "Int64"})
    cikmap = json.load(open(os.path.join(WORK, "cikmap.json")))
    universe = {r["symbol"] for r in cikmap["eslesen"] if r["rol"] == "universe"}
    retired = {r["symbol"] for r in cikmap["eslesen"] if r["rol"] == "retired"}
    rapor = {}

    k1, k2 = kapsam(sh, universe), kapsam(fu, universe)
    kap = pd.concat([k1.assign(aile="shares"), k2.assign(aile="fundamentals")])
    kap.to_csv(os.path.join(OUT, "kapsam.csv"), index=False)
    print("=== KAPSAM ===")
    print(kap.to_string(index=False))

    # --- tutarsizlik envanteri ---
    tut = {}
    # 1) hic gelir etiketi olmayan semboller
    rev_syms = set(fu[fu["tag"].isin(REV_TAGS)]["symbol"])
    tut["gelir_etiketi_yok"] = sorted((universe | retired) - rev_syms)
    # 2) brut kar hesaplanamaz: GrossProfit yok VE maliyet etiketi yok
    gp = set(fu[fu["tag"] == "GrossProfit"]["symbol"])
    cost = set(fu[fu["tag"].isin(COST_TAGS)]["symbol"])
    tut["brutkar_ve_maliyet_yok"] = sorted((universe | retired) - gp - cost)
    tut["gross_profit_yok_ama_maliyet_var"] = sorted(((universe | retired) - gp) & cost)
    # 3) Assets yok
    tut["assets_yok"] = sorted((universe | retired) - set(fu[fu["tag"] == "Assets"]["symbol"]))
    # 4) iki gelir etiketi ayni donemde farkli deger
    ov = []
    rev = fu[fu["tag"].isin(REV_TAGS[:2])]
    for sym, g in rev.groupby("symbol"):
        p = g.pivot_table(index=["start", "end"], columns="tag", values="val", aggfunc="last")
        if p.shape[1] < 2:
            continue
        both = p.dropna()
        if len(both) == 0:
            continue
        diff = (both.iloc[:, 0] - both.iloc[:, 1]).abs()
        rel = diff / both.iloc[:, 0].abs().clip(lower=1)
        ov.append({"symbol": sym, "ortak_donem": int(len(both)),
                   "farkli_deger_n": int((rel > 0.001).sum()),
                   "max_rel_fark": float(rel.max())})
    tut["iki_gelir_etiketi_cakisma"] = sorted(
        [o for o in ov if o["farkli_deger_n"] > 0], key=lambda x: -x["farkli_deger_n"])[:25]
    tut["iki_gelir_etiketi_cakisan_sembol_n"] = len(ov)
    # 5) hisse etiketleri: dei vs us-gaap ayni end tarihinde farkli
    hs = []
    for sym, g in sh.groupby("symbol"):
        p = g.pivot_table(index="end", columns="tag", values="val", aggfunc="max")
        if "EntityCommonStockSharesOutstanding" in p and "CommonStockSharesOutstanding" in p:
            both = p[["EntityCommonStockSharesOutstanding", "CommonStockSharesOutstanding"]].dropna()
            if len(both):
                rel = ((both.iloc[:, 0] - both.iloc[:, 1]).abs() / both.iloc[:, 0].abs().clip(lower=1))
                hs.append({"symbol": sym, "ortak_tarih": int(len(both)),
                           "rel_fark_medyan": float(rel.median()), "rel_fark_max": float(rel.max())})
    tut["dei_vs_usgaap_hisse"] = {
        "karsilastirilabilir_sembol_n": len(hs),
        "medyan_rel_fark_>1%_sembol_n": sum(1 for h in hs if h["rel_fark_medyan"] > 0.01),
        "en_buyuk_10": sorted(hs, key=lambda x: -x["rel_fark_medyan"])[:10]}
    # 5b) BAYAT SERI: canli evren sembolunde son dosyalama 4 aydan eski mi (kimlik/CIK
    #     kaymasi bu sekilde yakalanir — XOM vakasinin genel taramasi)
    bayat = []
    hepsi = pd.concat([sh[["symbol", "filed"]], fu[["symbol", "filed"]]])
    son = hepsi.groupby("symbol")["filed"].max()
    for sym in sorted(universe):
        f = son.get(sym, "")
        if not f or f < "2026-04-01":
            bayat.append({"symbol": sym, "son_filed": f or "SERI YOK"})
    tut["bayat_seri_evren"] = bayat
    tut["bayat_seri_emekli"] = [{"symbol": s, "son_filed": son.get(s, "SERI YOK")}
                                for s in sorted(retired)]
    # 6) birim anomalileri
    tut["shares_birimleri"] = sh["unit"].value_counts().to_dict()
    tut["fundamentals_birimleri"] = fu["unit"].value_counts().to_dict()
    tut["shares_val_sifir_veya_negatif"] = int((sh["val"] <= 0).sum())
    # 7) negatif gecikme (filed < end) — imkansiz gorunur, kapak tarihi semantigi
    for nm, df in (("shares", sh), ("fundamentals", fu)):
        lg = lag_days(df)
        neg = df[lg < 0]
        tut[f"{nm}_filed_end_oncesi"] = {
            "satir": int(len(neg)),
            "tag_dagilimi": neg["tag"].value_counts().head(5).to_dict(),
            "en_negatif_gun": int(lg.min())}
    rapor["tutarsizlik"] = tut

    # --- spot dogrulama: bilinen split'lerde dei hisse serisi ---
    spot = {}
    hedef = {"AAPL": ("2020-08-31", 4), "NVDA": ("2024-06-10", 10), "AVGO": ("2024-07-15", 10),
             "GOOGL": ("2022-07-18", 20), "TSLA": ("2022-08-25", 3)}
    for sym, (sd, ratio) in hedef.items():
        kullanilan = "EntityCommonStockSharesOutstanding"
        g = sh[(sh["symbol"] == sym) & (sh["tag"] == kullanilan)]
        if len(g) == 0:  # cok-sinifli ihracci: dei kapak sayisi yok -> us-gaap bilanco sayisi
            kullanilan = "CommonStockSharesOutstanding"
            g = sh[(sh["symbol"] == sym) & (sh["tag"] == kullanilan)]
        g = g.sort_values("filed")[["end", "filed", "val", "form"]]
        onc = g[g["filed"] < sd].tail(2)
        son = g[g["filed"] >= sd].head(2)
        if len(onc) and len(son):
            oran = float(son.iloc[0]["val"]) / float(onc.iloc[-1]["val"])
        else:
            oran = None
        spot[sym] = {"split_tarihi": sd, "beklenen_oran": ratio, "kullanilan_tag": kullanilan,
                     "son_split_oncesi_dosyalama": onc.to_dict("records"),
                     "ilk_split_sonrasi_dosyalama": son.to_dict("records"),
                     "gozlenen_oran": oran}
    rapor["spot"] = spot

    # --- her sembol icin ozet (kapsam kartinin sembol kirilimi) ---
    per = []
    for sym in sorted(universe | retired):
        s_sym = sh[sh["symbol"] == sym]
        f_sym = fu[fu["symbol"] == sym]
        dei = s_sym[s_sym["tag"] == "EntityCommonStockSharesOutstanding"]
        per.append({
            "symbol": sym,
            "rol": "universe" if sym in universe else "retired",
            "shares_dei_n": len(dei),
            "shares_dei_end_min": dei["end"].min() if len(dei) else "",
            "shares_dei_end_max": dei["end"].max() if len(dei) else "",
            "shares_anlik_n": int(s_sym["tag"].isin(SHARE_TAGS).sum()),
            "shares_wavg_n": int((~s_sym["tag"].isin(SHARE_TAGS)).sum()),
            "revenue_n": int(f_sym["tag"].isin(REV_TAGS).sum()),
            "cost_n": int(f_sym["tag"].isin(COST_TAGS).sum()),
            "grossprofit_n": int((f_sym["tag"] == "GrossProfit").sum()),
            "assets_n": int((f_sym["tag"] == "Assets").sum()),
            "fund_end_min": f_sym["end"].min() if len(f_sym) else "",
            "fund_end_max": f_sym["end"].max() if len(f_sym) else "",
        })
    pd.DataFrame(per).to_csv(os.path.join(OUT, "sembol_kapsam.csv"), index=False)

    json.dump(rapor, open(os.path.join(WORK, "validate_rapor.json"), "w"), indent=1, default=str)
    print("\n=== TUTARSIZLIK (ozet) ===")
    for k, v in tut.items():
        if isinstance(v, list):
            print(f"{k}: n={len(v)} -> {v[:15]}")
        else:
            print(f"{k}: {v}")
    print("\n=== SPOT ===")
    for k, v in spot.items():
        print(k, v["split_tarihi"], "beklenen 1/%d" % v["beklenen_oran"], "gozlenen oran:", v["gozlenen_oran"])
        print("   once:", v["son_split_oncesi_dosyalama"])
        print("   sonra:", v["ilk_split_sonrasi_dosyalama"])


if __name__ == "__main__":
    main()

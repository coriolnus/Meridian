"""Nihai ciktilari research/edgar_facts/ altina yaz: seriler + PIT gecikme tablosu +
tutarsizlik envanteri."""
import json, os

import pandas as pd

WORK = os.path.dirname(os.path.abspath(__file__))
OUT = "/Users/erdemozturk/AI-Trading/research/edgar_facts"
COLS = ["symbol", "cik", "taxonomy", "tag", "unit", "start", "end", "filed", "val",
        "form", "fy", "fp", "donem_gun", "donem_turu", "accn", "frame"]


def donem_turu(g):
    if pd.isna(g):
        return "anlik"
    if g <= 45:
        return "diger"
    if g <= 135:
        return "ceyrek"
    if g <= 225:
        return "yarim"
    if g <= 315:
        return "9ay"
    if g <= 400:
        return "yillik"
    return "diger"


def hazirla(path):
    df = pd.read_csv(path, dtype={"fy": "Int64", "start": "string", "frame": "string"})
    g = (pd.to_datetime(df["end"]) - pd.to_datetime(df["start"])).dt.days
    df["donem_gun"] = g.astype("Int64")
    df["donem_turu"] = [donem_turu(x) for x in g]
    df["start"] = df["start"].fillna("")
    df["frame"] = df["frame"].fillna("")
    return df.sort_values(["symbol", "tag", "end", "filed"])[COLS]


def ilk_ifsa(df):
    key = ["symbol", "tag", "start", "end"]
    first = df.groupby(key, as_index=False, dropna=False)["filed"].min()
    first["lag"] = (pd.to_datetime(first["filed"]) - pd.to_datetime(first["end"])).dt.days
    out = first.groupby("tag")["lag"].agg(
        ilk_ifsa_n="count", medyan_gun="median",
        p10=lambda s: s.quantile(.10), p90=lambda s: s.quantile(.90),
        min_gun="min", max_gun="max").reset_index()
    return out


def main():
    sh = hazirla(os.path.join(WORK, "shares_outstanding.csv"))
    fu = hazirla(os.path.join(WORK, "fundamentals.csv"))
    # gzip: duz CSV 44 MB tutuyor, depodaki en buyuk izlenen dosya 5.5 MB ve .git 15 MB.
    # pandas .csv.gz'yi dogrudan okur (read_csv yolu uzantidan cozer).
    sh.to_csv(os.path.join(OUT, "shares_outstanding.csv.gz"), index=False, compression="gzip")
    fu.to_csv(os.path.join(OUT, "fundamentals.csv.gz"), index=False, compression="gzip")
    for eski in ("shares_outstanding.csv", "fundamentals.csv"):
        p = os.path.join(OUT, eski)
        if os.path.exists(p):
            os.remove(p)

    lag = pd.concat([ilk_ifsa(sh).assign(aile="shares"), ilk_ifsa(fu).assign(aile="fundamentals")])
    lag.to_csv(os.path.join(OUT, "ilk_ifsa_gecikme.csv"), index=False)
    print(lag.to_string(index=False))

    rap = json.load(open(os.path.join(WORK, "validate_rapor.json")))
    tut = rap["tutarsizlik"]
    tut["_okuma_notu"] = (
        "Bu envanter KAYNAKTAKI (SEC dosyalamalarindaki) tutarsizliklarin sayimidir; "
        "duzeltilmemistir. Olcum tarafi filtresini kendisi secer ve kartinda yazar.")
    tut["ornekler"] = {
        "MET_dei_sifir": "MET 2010-06-30: dei EntityCommonStockSharesOutstanding=0 iken "
                         "us-gaap CommonStockSharesOutstanding=820,397,071 (dosyalayan hatasi: sifir)",
        "CCI_olcek_hatasi": "CCI 2008-12-31: us-gaap Issued/Outstanding=2.884644e11, dei=288,665,752 "
                            "(us-gaap tarafinda 1000x olcek hatasi)",
        "OXY_issued_vs_outstanding": "OXY 2023-09-30: Issued=1.105568e9 > Outstanding=877,701,484 "
                                     "(fark hazine hissesi — HATA DEGIL, semantik)",
        "AVB_gelir_etiketi": "AVB 2026Q2: RevenueFromContract...=1.78e6 ama Revenues=7.78e8 "
                             "(REIT'te kira geliri sozlesme-geliri etiketine girmez; iki etiket "
                             "AYNI SEY DEGIL)",
        "COP_gelir_etiketi": "COP 2026Q1: RevenueFromContract...=1.350e10, Revenues=1.576e10 "
                             "(fark: diger gelirler)",
        "MPWR_AFN": "MPWR FY2012 Revenues birimi 'AFN' (Afgan afganisi) olarak etiketlenmis — "
                    "tek satir, dosyalayan hatasi; USD filtresi bunu duser",
        "GOOG_GOOGL_dei_yok": "Alphabet'te dei:EntityCommonStockSharesOutstanding YOK (cok-sinifli "
                              "kapak sayisi boyutlu/dimensioned tag ile verilir, companyfacts "
                              "boyutlu olculeri tasimaz). us-gaap CommonStockSharesOutstanding "
                              "toplam sinif adedini veriyor (2026-06-30: 1.223e10).",
        "negatif_gecikme": "11 satirda filed < end (kapak tarihi dosyalamadan SONRAYA yazilmis; "
                           "ADBE end=2010-06-15 filed=2010-01-22 gibi acik yazim hatalari). PIT "
                           "kurali `filed`i kullandigi icin bu satirlar erken bilgi SIZDIRMAZ.",
        "XOM_kimlik_kaymasi": "company_tickers.json XOM -> CIK 2115436 ('ExxonMobil Holdings "
                              "Corp', NYSE, halef S-8 POS'lari 2026-07-01); o kayitta TEK BIR "
                              "us-gaap/dei olcusu yok (yalniz 'ffd' ucret olgusu). Butun gecmis "
                              "oncul CIK 34088'de ('Exxon Mobil Corporation', son 10-Q 2026-05-04) "
                              "— haritaya EK CIK olarak eklendi, XOM satirlari 34088'den geliyor.",
        "C_companyfacts_gecikmesi": "Citigroup (CIK 831001) 2026-05-07'de 2026-03-31 donemli, "
                                    "inline-XBRL'li 10-Q dosyalamis (submissions API'de gorunuyor) "
                                    "ama 2026-08-01 cekiminde companyfacts'teki en son filed "
                                    "2026-02-20 (FY2025 10-K). Yani SEC toplayicisinin kendisi "
                                    "gecikebiliyor; canli kullanimda 'son filed' bekcisi sart.",
        "SPOT_ifrs": "SPOT (Spotify) yabanci ozel ihracci: 20-F + 'ifrs-full' taksonomisi. "
                     "us-gaap etiketlerinin HICBIRI yok (Assets dahil); yalniz dei hisse serisi "
                     "var. IFRS cikarimi bu turda YAPILMADI.",
        "GS_SYF_gelir_etiketi": "GS ve SYF'de us-gaap:Revenues ve RevenueFromContract... YOK; "
                                "finansal kurumlar geliri InterestAndDividendIncomeOperating / "
                                "RevenuesNetOfInterestExpense gibi etiketlerle verir (bu turda "
                                "cekilmedi).",
    }
    json.dump(tut, open(os.path.join(OUT, "tutarsizlik.json"), "w"), indent=1, default=str)
    print("\nsatir: shares", len(sh), "| fundamentals", len(fu))


if __name__ == "__main__":
    main()

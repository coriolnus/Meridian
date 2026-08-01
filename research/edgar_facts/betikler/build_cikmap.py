"""Evren sembolleri -> CIK eslemesi. SEC company_tickers.json (guncel listeler) kaynak;
guncel listede olmayan (delist/birlesme) semboller EDGAR browse-edgar atom ile cozuldu."""
import json, os, sys

WORK = os.path.dirname(os.path.abspath(__file__))
REPO = "/Users/erdemozturk/AI-Trading"
sys.path.insert(0, REPO)
from meridian.adapters.data import REPLAY_UNIVERSE, RETIRED_SYMBOLS  # noqa: E402

# browse-edgar atom (action=getcompany&CIK=<ticker>) ile ELDE EDILEN, uydurulmadi:
# ANSS/DFS/HES/IPG/K/PARA/WBA -> asagidaki CIK'ler sorgu ciktisidir.
DELIST_COZUM = {
    "ANSS": (1013462, "ANSYS INC", "browse-edgar atom (ticker cozumu)"),
    "DFS": (1393612, "Discover Financial Services", "browse-edgar atom (ticker cozumu)"),
    "HES": (4447, "HESS CORP", "browse-edgar atom (ticker cozumu)"),
    "IPG": (51644, "INTERPUBLIC GROUP OF COMPANIES, INC.", "browse-edgar atom (ticker cozumu)"),
    "K": (55067, "KELLANOVA", "browse-edgar atom (ticker cozumu)"),
    "PARA": (813828, "Paramount Global", "browse-edgar atom (ticker cozumu)"),
    "WBA": (1618921, "Walgreens Boots Alliance, Inc.", "browse-edgar atom (ticker cozumu)"),
    # FI: browse-edgar ticker cozumu BOS dondu (NYSE listesi kapandi). Ayni ihraccinin
    # Nasdaq listesi FISV company_tickers.json'da CIK 798354 ile var -> FI ayni CIK.
    "FI": (798354, "FISERV INC", "FISV ile ayni ihracci (CIK 798354); ticker cozumu bos"),
}

# EK CIK'ler: guncel ticker->CIK eslemesi finansal olguyu TASIMIYORSA oncul/halef kayit.
# XOM: company_tickers.json XOM'u CIK 2115436'ya ("ExxonMobil Holdings Corp", NYSE, ilk
# S-8 POS halef dosyalamalari 2026-07-01) baglar; o kaydin companyfacts'inde YALNIZ 'ffd'
# (ucret) olgusu var, tek bir us-gaap/dei finansal olcusu yok. Tum finansal gecmis oncul
# "Exxon Mobil Corporation" CIK 34088'de (son 10-Q 2026-05-04). Ikisi de haritada.
EK_CIK = [("XOM", 34088, "Exxon Mobil Corporation", "universe",
           "oncul kayit — guncel CIK 2115436'da finansal XBRL olgusu yok (yalniz ffd)")]

with open(os.path.join(WORK, "company_tickers.json")) as f:
    raw = json.load(f)
by_ticker = {rec["ticker"].upper(): (int(rec["cik_str"]), rec["title"]) for rec in raw.values()}

universe = sorted(set(REPLAY_UNIVERSE))
retired = sorted(RETIRED_SYMBOLS)
targets = [(s, "universe") for s in universe] + [(s, "retired") for s in retired if s not in set(universe)]

rows, missing = [], []
for sym, rol in targets:
    hit = by_ticker.get(sym)
    if hit:
        rows.append({"symbol": sym, "cik": hit[0], "title": hit[1], "rol": rol,
                     "cik_kaynak": "company_tickers.json"})
    elif sym in DELIST_COZUM:
        cik, title, src = DELIST_COZUM[sym]
        rows.append({"symbol": sym, "cik": cik, "title": title, "rol": rol, "cik_kaynak": src})
    else:
        missing.append({"symbol": sym, "rol": rol, "neden": "hicbir kaynakta cozulemedi"})

for sym, cik, title, rol, notu in EK_CIK:
    rows.append({"symbol": sym, "cik": cik, "title": title, "rol": rol,
                 "cik_kaynak": "oncul/halef cozumu", "not": notu})

# ayni CIK'i paylasan sembol gruplari (cok-sinifli hisseler, listeleme degisimi)
by_cik = {}
for r in rows:
    by_cik.setdefault(r["cik"], []).append(r["symbol"])
paylasilan = {c: s for c, s in by_cik.items() if len(s) > 1}

print("hedef:", len(targets), "| eslesen:", len(rows), "| eslesmeyen:", len(missing))
print("benzersiz CIK:", len(by_cik))
print("paylasilan CIK gruplari:", paylasilan)
print("eslesmeyen:", missing)
with open(os.path.join(WORK, "cikmap.json"), "w") as f:
    json.dump({"eslesen": rows, "eslesmeyen": missing,
               "paylasilan_cik": {str(k): v for k, v in paylasilan.items()}}, f, indent=1)

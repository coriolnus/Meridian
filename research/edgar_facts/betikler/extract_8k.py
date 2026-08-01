"""Ham submissions JSON'lardan 8-K / Item 2.02 ("Results of Operations and Financial
Condition") satirlarini ayiklar -> earnings_8k_tarihleri.csv.

Kural (brief): form == '8-K' VE items alaninda '2.02' token'i. 8-K/A (duzeltme)
satirlari CSV'ye GIRMEZ ama sayilir ve kaynak damgasina yazilir (duzeltme yeni bir
duyuru degildir; sayilsa kapsam sisirilirdi).

Kapsam: filed >= 2010-01-01.
Cikti kolonlari: symbol, cik, filed, report_date, acceptance, items, accn
  filed       : SEC'e dosyalama gunu (EDGAR filingDate, ET takvim gunu)
  report_date : 8-K'nin "period of report" alani = raporlanan olayin gunu (duyuru gunu
                adayi; bos olabilir)
  acceptance  : EDGAR acceptanceDateTime ham dizgesi (saat dilimi damgasi belirsiz —
                ham birakildi, yorumlanmadi)
"""
import csv, glob, gzip, json, os, sys
from collections import defaultdict

WORK = "/Users/erdemozturk/AI-Trading/scratchpad/edgar_8k"
RAW = os.path.join(WORK, "raw")
OUT = "/Users/erdemozturk/AI-Trading/research/edgar_facts/earnings_8k_tarihleri.csv"
CIKMAP = "/Users/erdemozturk/AI-Trading/research/edgar_facts/cik_haritasi.json"
BASLANGIC = "2010-01-01"

cikmap = json.load(open(CIKMAP))
by_cik = defaultdict(list)
for r in cikmap["eslesen"]:
    by_cik[r["cik"]].append(r["symbol"])


def item_2_02(items):
    """items alani '2.02,9.01' / 'Item 2.02' / '' bicimlerinde gelebilir."""
    if not items:
        return False
    for tok in str(items).split(","):
        tok = tok.strip().replace("Item", "").strip()
        if tok == "2.02" or tok.startswith("2.02"):
            return True
    return False


def rows_from(blob):
    """Ana dosya (filings.recent) ya da eski sayfa (duz) -> satir sozlukleri."""
    if "filings" in blob:
        blob = blob["filings"]["recent"]
    n = len(blob.get("form", []))
    for i in range(n):
        yield {k: (blob[k][i] if k in blob and i < len(blob[k]) else "")
               for k in ("accessionNumber", "filingDate", "reportDate",
                         "acceptanceDateTime", "form", "items")}


kayitlar = []          # CSV satirlari
sayac = defaultdict(int)
amend = []             # 8-K/A + 2.02 (CSV disi)
eksik_cik = []
gorulen = set()        # (symbol, accn) tekillestirme

for cik in sorted(by_cik):
    syms = by_cik[cik]
    ana = os.path.join(RAW, f"CIK{cik:010d}.json.gz")
    if not os.path.exists(ana):
        eksik_cik.append(cik)
        continue
    dosyalar = [ana] + sorted(glob.glob(os.path.join(RAW, f"CIK{cik:010d}-submissions-*.json.gz")))
    for path in dosyalar:
        blob = json.loads(gzip.decompress(open(path, "rb").read()))
        for r in rows_from(blob):
            filed = r["filingDate"]
            if not filed or filed < BASLANGIC:
                continue
            if not item_2_02(r["items"]):
                continue
            form = r["form"]
            if form == "8-K":
                for s in syms:
                    key = (s, r["accessionNumber"])
                    if key in gorulen:
                        sayac["yinelenen_atlandi"] += 1
                        continue
                    gorulen.add(key)
                    kayitlar.append({"symbol": s, "cik": cik, "filed": filed,
                                     "report_date": r["reportDate"],
                                     "acceptance": r["acceptanceDateTime"],
                                     "items": r["items"],
                                     "accn": r["accessionNumber"]})
            elif form.startswith("8-K"):     # 8-K/A
                amend.append({"cik": cik, "symbols": syms, "filed": filed,
                              "form": form, "accn": r["accessionNumber"]})
                sayac["amend_2_02"] += 1

kayitlar.sort(key=lambda x: (x["symbol"], x["filed"], x["accn"]))
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["symbol", "cik", "filed", "report_date",
                                      "acceptance", "items", "accn"])
    w.writeheader()
    w.writerows(kayitlar)

with open(os.path.join(WORK, "amend_2_02.json"), "w") as f:
    json.dump(amend, f, indent=1)

semboller = {k["symbol"] for k in kayitlar}
print("satir:", len(kayitlar), "| sembol:", len(semboller),
      "| eksik CIK dosyasi:", len(eksik_cik), eksik_cik[:10])
print("8-K/A(2.02) CSV disi:", sayac["amend_2_02"], "| yinelenen atlandi:", sayac["yinelenen_atlandi"])
if kayitlar:
    print("filed araligi:", min(k["filed"] for k in kayitlar), "->",
          max(k["filed"] for k in kayitlar))
kapsanmayan = sorted({r["symbol"] for r in cikmap["eslesen"]} - semboller)
print("2.02 satiri OLMAYAN sembol:", len(kapsanmayan), kapsanmayan)

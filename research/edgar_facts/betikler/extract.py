"""companyfacts -> iki PIT serisi (shares_outstanding, fundamentals).

PIT semantigi: her satirda `end` (degerin ait oldugu tarih/donem sonu) ve `filed`
(SEC'e dosyalandigi, yani degerin BILINIR oldugu ilk gun) AYRI tutulur. Olcum
`filed`i kullanir; `end` yalniz donem etiketidir.
"""
import csv, gzip, json, os

WORK = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(WORK, "raw")
OUT = "/Users/erdemozturk/AI-Trading/research/edgar_facts"

SHARE_TAGS = [
    # ANLIK SAYIM (bilanco/kapak tarihine ait adet)
    ("dei", "EntityCommonStockSharesOutstanding"),
    ("us-gaap", "CommonStockSharesOutstanding"),
    ("us-gaap", "CommonStockSharesIssued"),
    # DONEM ORTALAMASI (EPS paydasi). Brief'in uc etiketinin cok-sinifli ihracclarda
    # (META/EL/MKC/STZ/HRL) BOS kalmasi bunlari zorunlu kildi: kapak sayisi boyutlu
    # (per-class) verildiginde companyfacts'e girmiyor, agirlikli ortalama giriyor.
    ("us-gaap", "WeightedAverageNumberOfSharesOutstandingBasic"),
    ("us-gaap", "WeightedAverageNumberOfDilutedSharesOutstanding"),
    ("us-gaap", "WeightedAverageNumberOfShareOutstandingBasicAndDiluted"),
]
FUND_TAGS = [
    ("us-gaap", "Revenues"),
    ("us-gaap", "RevenueFromContractWithCustomerExcludingAssessedTax"),
    ("us-gaap", "RevenueFromContractWithCustomerIncludingAssessedTax"),
    ("us-gaap", "CostOfRevenue"),
    ("us-gaap", "CostOfGoodsAndServicesSold"),
    ("us-gaap", "GrossProfit"),
    ("us-gaap", "Assets"),
]
COLS = ["symbol", "cik", "taxonomy", "tag", "unit", "start", "end", "filed",
        "val", "form", "fy", "fp", "accn", "frame"]


def pull(facts, taxonomy, tag):
    node = ((facts.get(taxonomy) or {}).get(tag) or {})
    for unit, entries in (node.get("units") or {}).items():
        for e in entries:
            yield unit, e


def main():
    cikmap = json.load(open(os.path.join(WORK, "cikmap.json")))
    by_cik = {}
    for r in cikmap["eslesen"]:
        by_cik.setdefault(r["cik"], []).append(r["symbol"])

    os.makedirs(OUT, exist_ok=True)
    fh_s = open(os.path.join(WORK, "shares_outstanding.csv"), "w", newline="")
    fh_f = open(os.path.join(WORK, "fundamentals.csv"), "w", newline="")
    w_s, w_f = csv.DictWriter(fh_s, COLS), csv.DictWriter(fh_f, COLS)
    w_s.writeheader(); w_f.writeheader()

    stats = {}          # symbol -> {tag: {"n":, "min_end":, "max_end":, "gecikme":[...]}}
    eksik_dosya, bos_facts = [], []
    n_s = n_f = 0
    for cik, syms in sorted(by_cik.items()):
        path = os.path.join(RAW, f"CIK{cik:010d}.json.gz")
        if not os.path.exists(path):
            eksik_dosya.append((cik, syms)); continue
        doc = json.loads(gzip.decompress(open(path, "rb").read()))
        facts = doc.get("facts") or {}
        if not facts:
            bos_facts.append((cik, syms)); continue
        for writer, taglist, is_share in ((w_s, SHARE_TAGS, True), (w_f, FUND_TAGS, False)):
            seen = set()
            rows = []
            for tax, tag in taglist:
                for unit, e in pull(facts, tax, tag):
                    key = (tag, unit, e.get("start"), e.get("end"), e.get("val"),
                           e.get("filed"), e.get("accn"), e.get("form"))
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append({"taxonomy": tax, "tag": tag, "unit": unit,
                                 "start": e.get("start") or "", "end": e.get("end"),
                                 "filed": e.get("filed"), "val": e.get("val"),
                                 "form": e.get("form"), "fy": e.get("fy"), "fp": e.get("fp"),
                                 "accn": e.get("accn"), "frame": e.get("frame") or ""})
            rows.sort(key=lambda r: (r["tag"], r["end"] or "", r["filed"] or ""))
            for sym in syms:
                st = stats.setdefault(sym, {})
                for r in rows:
                    writer.writerow({"symbol": sym, "cik": cik, **r})
                    s = st.setdefault(r["tag"], {"n": 0, "min_end": "9999", "max_end": "0",
                                                 "min_filed": "9999", "max_filed": "0", "lag": []})
                    s["n"] += 1
                    if r["end"]:
                        s["min_end"] = min(s["min_end"], r["end"]); s["max_end"] = max(s["max_end"], r["end"])
                    if r["filed"]:
                        s["min_filed"] = min(s["min_filed"], r["filed"]); s["max_filed"] = max(s["max_filed"], r["filed"])
                    if r["end"] and r["filed"]:
                        s["lag"].append((r["end"], r["filed"]))
                if is_share:
                    n_s += len(rows) * 1
                else:
                    n_f += len(rows) * 1
    fh_s.close(); fh_f.close()
    json.dump({"eksik_dosya": eksik_dosya, "bos_facts": bos_facts,
               "satir_shares": n_s, "satir_fund": n_f},
              open(os.path.join(WORK, "extract_summary.json"), "w"), indent=1)
    # istatistik ham hali (lag listesi buyuk) -> ayri dosya, sonra ozetlenecek
    with open(os.path.join(WORK, "stats_raw.json"), "w") as f:
        json.dump(stats, f)
    print("shares satir:", n_s, "| fundamentals satir:", n_f)
    print("eksik dosya:", eksik_dosya, "| bos facts:", bos_facts)


if __name__ == "__main__":
    main()

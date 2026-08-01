"""SEC EDGAR submissions indirici (8-K kazanc-tarihi vekili icin).

Nazik: sirali, istek arasi 0.15s (<=~6.7 istek/sn, SEC siniri 10/sn), zorunlu
User-Agent. Her CIK icin submissions/CIK##########.json cekilir; JSON'un
filings.files listesindeki ESKI SAYFALAR da ayrica cekilir (recent yalnizca son
~1000 dosyalamayi tasir, 2010'a inmek icin sayfalar sart).

Ham JSON gzip'lenip raw/ altina yazilir; her dosyanin sha256'si (ham, sikistirilmamis
bayt uzerinden) manifest'e islenir. Hatalar sessiz yutulmaz -> manifest'e yazilir.
"""
import gzip, hashlib, json, os, ssl, time, urllib.request, urllib.error

import certifi

SSLCTX = ssl.create_default_context(cafile=certifi.where())

WORK = "/Users/erdemozturk/AI-Trading/scratchpad/edgar_8k"
RAW = os.path.join(WORK, "raw")
os.makedirs(RAW, exist_ok=True)
UA = "Meridian Research oztrkerdem@gmail.com"
TPL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
PAGE_TPL = "https://data.sec.gov/submissions/{name}"
DELAY = 0.15

CIKMAP = "/Users/erdemozturk/AI-Trading/research/edgar_facts/cik_haritasi.json"
cikmap = json.load(open(CIKMAP))
by_cik = {}
for r in cikmap["eslesen"]:
    by_cik.setdefault(r["cik"], []).append(r["symbol"])

manifest = []


def fetch(url, out, meta):
    """Tek istek. Diskte varsa yeniden indirmez; zaman damgasi dosyanin mtime'i."""
    rec = dict(meta)
    rec["url"] = url
    rec["dosya"] = os.path.basename(out)
    if os.path.exists(out):
        data = gzip.decompress(open(out, "rb").read())
        rec |= {"http": 200, "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "indirme_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                             time.gmtime(os.path.getmtime(out))),
                "not": "diskteki dosya (bu calistirmada yeniden indirilmedi); zaman = dosya mtime"}
        manifest.append(rec)
        return data
    rec["indirme_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Encoding": "gzip",
                                               "Host": "data.sec.gov"})
    data = None
    try:
        with urllib.request.urlopen(req, timeout=90, context=SSLCTX) as resp:
            body = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                body = gzip.decompress(body)
            rec |= {"http": resp.status, "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest()}
            with open(out, "wb") as f:
                f.write(gzip.compress(body, 6))
            data = body
    except urllib.error.HTTPError as e:
        rec |= {"http": e.code, "bytes": 0, "sha256": None, "hata": str(e)}
    except Exception as e:
        rec |= {"http": None, "bytes": 0, "sha256": None, "hata": repr(e)}
    manifest.append(rec)
    time.sleep(DELAY)
    return data


t0 = time.time()
n_page = 0
for i, (cik, syms) in enumerate(sorted(by_cik.items()), 1):
    meta = {"cik": cik, "symbols": syms, "tur": "ana"}
    out = os.path.join(RAW, f"CIK{cik:010d}.json.gz")
    data = fetch(TPL.format(cik=cik), out, meta)
    if data is None:
        continue
    try:
        j = json.loads(data)
    except Exception as e:
        manifest[-1]["parse_hata"] = repr(e)
        continue
    for f in j.get("filings", {}).get("files", []):
        name = f.get("name")
        if not name:
            continue
        # eski sayfa: yalnizca 2010 ve sonrasina degen sayfalar gerekli
        to = f.get("filingTo", "")
        if to and to < "2010-01-01":
            continue
        n_page += 1
        pmeta = {"cik": cik, "symbols": syms, "tur": "sayfa",
                 "filingFrom": f.get("filingFrom"), "filingTo": to,
                 "filingCount": f.get("filingCount")}
        fetch(PAGE_TPL.format(name=name), os.path.join(RAW, name + ".gz"), pmeta)
    if i % 25 == 0:
        print(f"{i}/{len(by_cik)} sayfa={n_page} gecen={time.time()-t0:.0f}s", flush=True)

with open(os.path.join(WORK, "download_manifest_8k.json"), "w") as f:
    json.dump(manifest, f, indent=1)
bad = [m for m in manifest if m.get("http") != 200]
print("BITTI istek=", len(manifest), "| ana=", sum(1 for m in manifest if m["tur"] == "ana"),
      "| sayfa=", n_page, "| hatali=", len(bad), [(m["cik"], m.get("http")) for m in bad][:20])
print("toplam bayt:", sum(m["bytes"] for m in manifest))

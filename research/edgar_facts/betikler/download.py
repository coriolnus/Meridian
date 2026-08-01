"""SEC companyfacts indirici. Nazik: sirali, istek arasi 0.15s (<=~5 istek/sn),
zorunlu User-Agent. Ham JSON gzip'lenip raw/ altina yazilir; her dosyanin
sha256'si (ham bayt uzerinden) manifest'e islenir."""
import gzip, hashlib, json, os, ssl, time, urllib.request, urllib.error

import certifi

SSLCTX = ssl.create_default_context(cafile=certifi.where())  # sistem CA yolu bos -> certifi

WORK = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(WORK, "raw")
UA = "Meridian Research oztrkerdem@gmail.com"
TPL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
DELAY = 0.15

cikmap = json.load(open(os.path.join(WORK, "cikmap.json")))
by_cik = {}
for r in cikmap["eslesen"]:
    by_cik.setdefault(r["cik"], []).append(r["symbol"])

manifest = []
t0 = time.time()
for i, (cik, syms) in enumerate(sorted(by_cik.items()), 1):
    url = TPL.format(cik=cik)
    out = os.path.join(RAW, f"CIK{cik:010d}.json.gz")
    rec = {"cik": cik, "symbols": syms, "url": url,
           "indirme_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if os.path.exists(out):  # yeniden calistirmada tekrar indirme
        data = gzip.decompress(open(out, "rb").read())
        # zaman damgasi dosyanin KENDI mtime'i — yeniden calistirma anini indirme
        # zamani gibi gostermek uydurma olurdu
        rec |= {"http": 200, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                "indirme_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                             time.gmtime(os.path.getmtime(out))),
                "not": "diskteki dosya (bu calistirmada yeniden indirilmedi); zaman = dosya mtime"}
        manifest.append(rec)
        continue
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip",
                                               "Host": "data.sec.gov"})
    try:
        with urllib.request.urlopen(req, timeout=90, context=SSLCTX) as resp:
            body = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                body = gzip.decompress(body)
            rec |= {"http": resp.status, "bytes": len(body),
                    "sha256": hashlib.sha256(body).hexdigest()}
            with open(out, "wb") as f:
                f.write(gzip.compress(body, 6))
    except urllib.error.HTTPError as e:
        rec |= {"http": e.code, "bytes": 0, "sha256": None, "hata": str(e)}
    except Exception as e:  # ag hatasi: sessiz yutulmuyor, manifest'e yaziliyor
        rec |= {"http": None, "bytes": 0, "sha256": None, "hata": repr(e)}
    manifest.append(rec)
    if i % 25 == 0:
        print(f"{i}/{len(by_cik)} gecen={time.time()-t0:.0f}s", flush=True)
    time.sleep(DELAY)

with open(os.path.join(WORK, "download_manifest.json"), "w") as f:
    json.dump(manifest, f, indent=1)
bad = [m for m in manifest if m.get("http") != 200]
print("BITTI", len(manifest), "dosya | hatali:", len(bad), [m["cik"] for m in bad])
print("toplam bayt:", sum(m["bytes"] for m in manifest))

# EDG-2026-067 arsiv ingest'i — A1'de systemd-run ile SEANS-DISI kosar (kill maddesi).
# Idempotent: document_id=repo-yolu (upsert) + ilerleme dosyasi; yarim kalirsa ayni komutla devam.
# Cikti /opt/hindsight/ingest067/log.txt'e (ssh-pipe kopmasi dersi: stdout'a guvenilmez).
# Bu repo kopyasi REFERANSTIR; kosan kopya A1: /opt/hindsight/ingest067/ingest067.py (yollar A1-sabit).
import json
import os
import time
import urllib.request
import urllib.error

KOK = "/opt/hindsight/ingest067"
BASE = "http://127.0.0.1:8888/v1/default"
BANK = "meridian-arsiv"
KEY = os.environ.get("HS_KEY") or open("/opt/hindsight/.env").read().split(
    "HINDSIGHT_API_TENANT_API_KEY=")[1].splitlines()[0]
LOG = open(f"{KOK}/log.txt", "a", buffering=1)


def kayit(*a):
    LOG.write(time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a) + "\n")


def api(method, path, body=None, timeout=3600):  # 138KB+ belgeler chunk basina LLM yer — 900 sn yetmedi (elle test 2026-09-01)
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read() or b"{}")


# 0. kill maddesi: "embedding boyutu 1024 dogrulanmadan baslayan ingest gecersiz"
env_metin = open("/opt/hindsight/.env").read()
if "HINDSIGHT_API_EMBEDDINGS_ONNX_DIMENSIONS=1024" not in env_metin:
    kayit("ABORT: DIMENSIONS=1024 .env'de dogrulanamadi")
    raise SystemExit(3)
st, _ = api("GET", "/banks")  # servis ayakta degilse burada duser
kayit("boyut=1024 (.env) + servis ayakta dogrulandi")

# 1. bank + Memory Defense (kill: defense KAPALI bank'le kosum GECERSIZ)
api("PUT", f"/banks/{BANK}", {"name": BANK})
api("PATCH", f"/banks/{BANK}/config",
    {"updates": {"memory_defense": {"enabled": True,
                 "rules": [{"on": "sensitive_data", "action": "redact"}]}}})
st, cfg = api("GET", f"/banks/{BANK}/config")
md = (cfg.get("config") or {}).get("memory_defense") or cfg.get("memory_defense") or {}
if md.get("enabled") is not True:
    kayit("ABORT: Memory Defense acilamadi:", json.dumps(md)[:200])
    raise SystemExit(2)
kayit("defense enabled=true dogrulandi")

manifest = json.load(open(f"{KOK}/manifest.json"))
kayit("manifest:", len(manifest["dosyalar"]), "dosya · commit", manifest["head_commit"][:9])

ilerleme_yolu = f"{KOK}/ilerleme.jsonl"
bitenler = set()
if os.path.exists(ilerleme_yolu):
    for satir in open(ilerleme_yolu):
        try:
            bitenler.add(json.loads(satir)["yol"])
        except Exception as e:  # sessiz-yutma: bozuk ilerleme satiri yalnizca yeniden-isleme demektir, kayit dusuyoruz
            kayit("ilerleme satiri bozuk, yok sayildi:", e)
ilerleme = open(ilerleme_yolu, "a", buffering=1)

toplam_usage = {"girdi": 0, "cikti": 0}
basarisiz = []
for d in manifest["dosyalar"]:
    yol = d["yol"]
    if yol in bitenler:
        continue
    icerik = open(f"{KOK}/korpus/{yol}", encoding="utf-8").read()
    govde = {"items": [{"content": icerik, "document_id": yol,
                        "context": "arsiv-ingest EDG-2026-067",
                        "metadata": {"blob": d["blob"], "commit": manifest["head_commit"]}}],
             "async": False}
    ok = False
    for deneme in (1, 2, 3):
        t0 = time.time()
        try:
            st, r = api("POST", f"/banks/{BANK}/memories", govde)
            u = r.get("usage") or {}
            gi, ci = u.get("input_tokens", 0) or 0, u.get("output_tokens", 0) or 0
            toplam_usage["girdi"] += gi
            toplam_usage["cikti"] += ci
            kayit(f"OK {yol} {time.time()-t0:.0f}s deneme={deneme} tok={gi}/{ci}")
            ilerleme.write(json.dumps({"yol": yol, "blob": d["blob"],
                                       "sure_s": round(time.time()-t0, 1),
                                       "girdi_tok": gi, "cikti_tok": ci}) + "\n")
            ok = True
            break
        except urllib.error.HTTPError as e:
            kayit(f"HATA {yol} deneme={deneme} HTTP {e.code} {e.read()[:150]!r}")
        except Exception as e:  # sessiz-yutma: ag/timeout sinifi — kaydedilip backoff'la yeniden denenir
            kayit(f"HATA {yol} deneme={deneme} {type(e).__name__}: {e}")
        time.sleep(30 * deneme)  # free-model dalgalanmasi (vaka 2026-09-01): backoff
    if not ok:
        basarisiz.append(yol)

kayit("BITTI · basarisiz:", len(basarisiz), basarisiz[:5],
      "· toplam token girdi/cikti:", toplam_usage["girdi"], toplam_usage["cikti"])
st, r = api("GET", f"/banks/{BANK}/documents")
kayit("bank belge sayisi:", len(r.get("items", [])))
raise SystemExit(0 if not basarisiz else 1)

"""EDG-2026-037 · TCA — CANLI HAM KANIT ÇEKİMİ (SALT-OKUMA).

KOŞUM (yereldeki oturumdan, stdin deseni — canlıya DOSYA YAZILMAZ):
    ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 \
        'cd /opt/meridian && ./.venv/bin/python -' < canli_cek.py > canli_ham.json

NE YAPAR: TCA'nın ihtiyaç duyduğu ÜÇ kaynağı tek JSON'a toplar.
  (1) AYNA/İCRA defteri  — state/entry_execution.jsonl (E2 icra defteri: plan tetiği, resmî açılış,
                           gerçek dolum, motor ayrımı ayna/iç) + state/mirror_orders.json
  (2) BROKER GERÇEĞİ     — Alpaca kâğıt hesabından /v2/orders (status=all, sayfalı, nested) +
                           /v2/account/activities (FILL = dolum OLAYI düzeyi; FEE = gerçek ücret)
  (3) DEFTER             — trades (SQLite) satırları: kaynak damgası, costs, pnl_dollars,
                           alpaca_fill_price + goal.yaml friksiyon parametreleri

YAZMA YOK: hiçbir dosya açılmaz/yazılmaz, hiçbir emir gönderilmez/iptal edilmez. Alpaca tarafında
YALNIZ GET çağrılır (`alpaca.account/positions/orders` + iki GET uç noktası).

UYDURMA YASAĞI: okunamayan her kalem `null` + `_hata` alanıyla döner; varsayılan sayı üretilmez.
"""
import datetime as dt
import hashlib
import json
import os
import sys
from collections import Counter

OUT: dict = {"kart": "EDG-2026-037", "cekim_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def _sha(path: str) -> str | None:
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    except Exception:
        return None


def _dosya(ad: str) -> str:
    return os.path.join("state", ad)


# ---------------------------------------------------------------- (1) icra defteri + ayna
try:
    rows = []
    with open(_dosya("entry_execution.jsonl")) as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    OUT["entry_execution"] = {"n": len(rows), "satirlar": rows,
                              "sha256_16": _sha(_dosya("entry_execution.jsonl"))}
except Exception as e:
    OUT["entry_execution"] = {"n": None, "_hata": f"{type(e).__name__}: {e}"}

try:
    mo = json.load(open(_dosya("mirror_orders.json")))
    OUT["mirror_orders"] = {"n": len(mo.get("orders") or {}), "updated": mo.get("updated"),
                            "last_event_ts": mo.get("last_event_ts"),
                            "orders": mo.get("orders") or {},
                            "sha256_16": _sha(_dosya("mirror_orders.json"))}
except Exception as e:
    OUT["mirror_orders"] = {"n": None, "_hata": f"{type(e).__name__}: {e}"}

try:
    OUT["broker_reconcile"] = json.load(open(_dosya("broker_reconcile.json")))
except Exception as e:
    OUT["broker_reconcile"] = {"_hata": f"{type(e).__name__}: {e}"}

# ---------------------------------------------------------------- (3) defter + friksiyon ayarı
try:
    from meridian import store, config
    tr = store.read_jsonl("trades.jsonl")
    OUT["trades"] = {
        "n": len(tr),
        "kaynak_dagilim": dict(Counter(str(r.get("kaynak")) for r in tr)),
        "alpaca_fill_price_dolu": sum(1 for r in tr if r.get("alpaca_fill_price") is not None),
        "mirror_divergence_dolu": sum(1 for r in tr if r.get("mirror_divergence") is not None),
        "costs_dolu": sum(1 for r in tr if r.get("costs") is not None),
        "costs_toplam": round(sum(float(r.get("costs") or 0.0) for r in tr), 4),
        "pnl_dollars_toplam": round(sum(float(r.get("pnl_dollars") or 0.0) for r in tr), 4),
        "brut_kazanc": round(sum(float(r["pnl_dollars"]) for r in tr if float(r.get("pnl_dollars") or 0) > 0), 4),
        "brut_kayip": round(sum(float(r["pnl_dollars"]) for r in tr if float(r.get("pnl_dollars") or 0) < 0), 4),
        "anahtarlar": sorted({k for r in tr for k in r}),
        "satirlar": [{k: r.get(k) for k in
                      ("id", "plan_id", "ticker", "kaynak", "ts_open", "ts_close", "entry", "exit",
                       "qty", "costs", "pnl_dollars", "exit_reason", "alpaca_fill_price",
                       "mirror_divergence")} for r in tr],
    }
except Exception as e:
    OUT["trades"] = {"n": None, "_hata": f"{type(e).__name__}: {e}"}

try:
    g = config.goal()
    OUT["friksiyon_ayari"] = {
        "slippage_bps": g.get("slippage_bps"),
        "commission_per_share": g.get("commission_per_share"),
        "pessimistic_band_v2": g.get("pessimistic_band_v2"),
        "goal_sha256_16": _sha(_dosya("goal.yaml")),
    }
except Exception as e:
    OUT["friksiyon_ayari"] = {"_hata": f"{type(e).__name__}: {e}"}

try:
    from meridian import ledgerstamp
    OUT["ledgerstamp"] = ledgerstamp.ozet() if hasattr(ledgerstamp, "ozet") else None
except Exception as e:
    OUT["ledgerstamp"] = {"_hata": f"{type(e).__name__}: {e}"}

# ---------------------------------------------------------------- (2) broker gerçeği (GET-only)
try:
    import httpx
    from meridian.adapters import alpaca
    OUT["alpaca"] = {"paper_available": alpaca.paper_available(), "endpoint": alpaca._paper_base()}
    acct = alpaca.account()
    OUT["alpaca"]["account"] = ({k: acct.get(k) for k in
                                 ("equity", "last_equity", "cash", "portfolio_value", "created_at",
                                  "status", "account_number")} if acct else None)
    OUT["alpaca"]["positions"] = [{k: p.get(k) for k in
                                   ("symbol", "qty", "avg_entry_price", "side", "cost_basis",
                                    "market_value", "unrealized_pl")}
                                  for p in alpaca.positions()]

    # --- tüm emirler (sayfalı, geriye doğru) + bacakları düzleştir
    tum, until, sayfalar = [], None, []
    for _ in range(20):
        batch = alpaca.orders(status="all", limit=500, nested=True, until=until)
        if not batch:
            break
        tum.extend(batch)
        en_eski = min(str(o.get("submitted_at") or "") for o in batch)
        sayfalar.append({"n": len(batch), "en_eski": en_eski})
        if len(batch) < 500:
            break
        until = en_eski
    duz: dict = {}

    def _ekle(o, parent=None):
        # PARENT KİMLİĞİ TAŞINIR: bracket'ın koruma bacaklarının `client_order_id`si Alpaca'nın
        # ürettiği UUID'dir, motor öneki (`P-`) TAŞIMAZ. Ebeveyn bağı kaydedilmezse o bacaklar
        # 'motor emri değil' diye sınıflanır ve ÇIKIŞ bacağının paydası sessizce eksilir.
        if isinstance(o, dict) and o.get("id"):
            o = {**o, "_parent_id": parent}
            duz[o["id"]] = o
            for l in (o.get("legs") or []):
                _ekle(l, o["id"])
    for o in tum:
        _ekle(o)
    ALANLAR = ("id", "_parent_id", "client_order_id", "symbol", "side", "type", "order_class", "qty",
               "filled_qty", "filled_avg_price", "limit_price", "stop_price", "status",
               "time_in_force", "submitted_at", "filled_at", "canceled_at", "expired_at")
    OUT["alpaca"]["orders"] = {
        "sayfalar": sayfalar, "n_ust_duzey": len(tum), "n_tekil_bacaklarla": len(duz),
        "status_dagilim": dict(Counter(str(o.get("status")) for o in duz.values())),
        "satirlar": sorted([{k: o.get(k) for k in ALANLAR} for o in duz.values()],
                           key=lambda x: str(x.get("submitted_at") or "")),
    }

    # --- dolum OLAYI düzeyi + gerçek ücretler
    base, hdr = alpaca._paper_base(), alpaca._headers()
    akt: dict = {}
    for tip in ("FILL", "FEE", "CFEE", "PTC"):
        acts, token, hata = [], None, None
        for _ in range(20):
            params = {"activity_types": tip, "page_size": 100}
            if token:
                params["page_token"] = token
            r = httpx.get(f"{base}/v2/account/activities", headers=hdr, params=params, timeout=20)
            if r.status_code != 200:
                hata = f"HTTP {r.status_code}: {r.text[:200]}"
                break
            b = r.json()
            if not b:
                break
            acts.extend(b)
            if len(b) < 100:
                break
            token = b[-1].get("id")
        akt[tip] = {"n": len(acts), "kayitlar": acts, "_hata": hata}
    OUT["alpaca"]["activities"] = akt
except Exception as e:
    OUT.setdefault("alpaca", {})["_hata"] = f"{type(e).__name__}: {e}"

json.dump(OUT, sys.stdout, ensure_ascii=False, indent=1, default=str)

"""EDG-2026-038 · TCA tur-2 — CANLI HAM KANIT ÇEKİMİ (SALT-OKUMA).

KOŞUM (yereldeki oturumdan, stdin deseni — canlıya DOSYA YAZILMAZ):
    ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 \
        'cd /opt/meridian && ./.venv/bin/python -' < canli_cek.py > canli_ham.json

EDG-037'nin çekiminden FARKI (ikisi de gerekli, bu kart ikisini birleştirir):
  (1) KONSOLİDE FİYAT — `feed=sip` günlük bar (açılış müzayedesi basımı) + `timeframe=1Min`
      dakika barları (ilk-dakika VWAP + menzil orta-noktası). EDG-037 paydası `feed=iex` idi;
      bu çekim İKİSİNİ DE alır ki yan yana konabilsin.
  (2) ÇIKIŞ BACAĞI — bütün SATIŞ emirleri + koruma OCO'larının yaşam döngüsü (tip/TIF/limit_price/
      status/zaman damgaları) ve pozisyonların KORUMASIZ kaldığı pencerenin ham girdileri.

YAZMA YOK: hiçbir dosya açılmaz/yazılmaz, hiçbir emir gönderilmez/iptal edilmez/değiştirilmez.
Alpaca tarafında YALNIZ GET çağrılır.

UYDURMA YASAĞI: okunamayan her kalem `null` + `_hata` alanıyla döner; varsayılan sayı üretilmez.
"""
import datetime as dt
import hashlib
import json
import os
import sys
from collections import Counter

SEANS = "2026-08-06"                       # EDG-037'nin dört dolumunun seansı
SEMBOLLER = ["NUE", "EMR", "BKNG", "AMGN"]
OUT: dict = {"kart": "EDG-2026-038",
             "cekim_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}


def _sha(path: str) -> str | None:
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    except Exception:
        return None


def _dosya(ad: str) -> str:
    return os.path.join("state", ad)


# ---------------------------------------------------------------- (0) icra defteri + ayna
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

# replay bar arşivinin KAYNAK DAMGASI — kanonik ölçüt gerekçe_1'in çürütme sınaması
try:
    bs = json.load(open(_dosya("bars_source.json")))
    OUT["bars_source"] = {"n": len(bs),
                          "dagilim": dict(Counter((v or {}).get("source") if isinstance(v, dict) else v
                                                  for v in bs.values())),
                          "dort_sembol": {s: bs.get(s) or bs.get(s.lower()) for s in SEMBOLLER},
                          "sha256_16": _sha(_dosya("bars_source.json"))}
except Exception as e:
    OUT["bars_source"] = {"_hata": f"{type(e).__name__}: {e}"}

# replay'in KENDİ bar arşivinden o günün açılışı (motorun paydası) — varsa
try:
    import csv as _csv
    ac = {}
    for s in SEMBOLLER:
        p = _dosya(os.path.join("bars", f"{s.lower()}.csv"))
        row = None
        if os.path.exists(p):
            with open(p, newline="") as f:
                for r in _csv.DictReader(f):
                    if r.get("date") == SEANS:
                        row = r
                        break
        ac[s] = row
    OUT["replay_bar_arsivi"] = {"seans": SEANS, "barlar": ac,
                                "not": "motorun `next_open` paydası bu arşivden gelir (broker.py:515)"}
except Exception as e:
    OUT["replay_bar_arsivi"] = {"_hata": f"{type(e).__name__}: {e}"}

try:
    from meridian import config
    g = config.goal()
    OUT["friksiyon_ayari"] = {"slippage_bps": g.get("slippage_bps"),
                              "commission_per_share": g.get("commission_per_share"),
                              "pessimistic_band_v2": g.get("pessimistic_band_v2"),
                              "execution_v2": g.get("execution_v2"),
                              "goal_sha256_16": _sha(_dosya("goal.yaml"))}
except Exception as e:
    OUT["friksiyon_ayari"] = {"_hata": f"{type(e).__name__}: {e}"}

# ---------------------------------------------------------------- (1) KONSOLİDE + IEX FİYAT
# feed künyesi KODDAN okunur — "sip kullandık" cümlesi rapora elle yazılmaz.
try:
    from meridian.adapters import alpaca
    OUT["feed_kunyesi"] = {
        "DATA_BASE": alpaca.DATA_BASE,
        "DATA_FEED_yururlukteki": alpaca.DATA_FEED,          # 'iex'  — EDG-037'nin paydası
        "DATA_FEED_SIP": alpaca.DATA_FEED_SIP,               # 'sip'  — konsolide
        "IEX_SOURCE": alpaca.IEX_SOURCE, "SIP_SOURCE": alpaca.SIP_SOURCE,
        "kod": "meridian/adapters/alpaca.py:1091-1095",
        "gunluk_bar_ucu": "/v2/stocks/bars timeframe=1Day adjustment=split (alpaca.py:1428-1432)",
    }
except Exception as e:
    OUT["feed_kunyesi"] = {"_hata": f"{type(e).__name__}: {e}"}

for etiket, feed in (("sip", "sip"), ("iex", "iex")):
    try:
        from meridian.adapters import alpaca
        d = alpaca._get_data("/v2/stocks/bars",
                             {"symbols": ",".join(SEMBOLLER), "timeframe": "1Day",
                              "start": SEANS, "end": SEANS, "limit": 100, "feed": feed,
                              "adjustment": "split", "sort": "asc"}, 30.0)
        OUT[f"gunluk_bar_{etiket}"] = {"istek": {"timeframe": "1Day", "feed": feed, "session": SEANS,
                                                 "adjustment": "split"},
                                       "bars": d.get("bars")}
    except Exception as e:
        OUT[f"gunluk_bar_{etiket}"] = {"_hata": f"{type(e).__name__}: {getattr(e, 'reason', e)}",
                                       "_status": getattr(e, "status", None),
                                       "_body": getattr(e, "body", "")}

# dakika barları — açılış penceresi (13:25-14:05Z) KONSOLİDE ve IEX
for etiket, feed in (("sip", "sip"), ("iex", "iex")):
    try:
        from meridian.adapters import alpaca
        acc, token, sayfa, hata = [], None, 0, None
        while sayfa < 10:
            params = {"symbols": ",".join(SEMBOLLER), "timeframe": "1Min",
                      "start": f"{SEANS}T13:25:00Z", "end": f"{SEANS}T14:05:00Z",
                      "limit": 10000, "feed": feed, "adjustment": "split", "sort": "asc"}
            if token:
                params["page_token"] = token
            d = alpaca._get_data("/v2/stocks/bars", params, 30.0)
            acc.append(d.get("bars") or {})
            token = d.get("next_page_token")
            sayfa += 1
            if not token:
                break
        birlesik: dict = {}
        for blok in acc:
            for sym, rs in blok.items():
                birlesik.setdefault(str(sym).upper(), []).extend(rs or [])
        OUT[f"dakika_bar_{etiket}"] = {"istek": {"timeframe": "1Min", "feed": feed,
                                                 "pencere": f"{SEANS}T13:25Z..14:05Z"},
                                       "sayfa": sayfa, "bars": birlesik, "_hata": hata}
    except Exception as e:
        OUT[f"dakika_bar_{etiket}"] = {"_hata": f"{type(e).__name__}: {getattr(e, 'reason', e)}",
                                       "_status": getattr(e, "status", None),
                                       "_body": getattr(e, "body", "")}

# ---------------------------------------------------------------- (2) BROKER GERÇEĞİ (GET-only)
try:
    import httpx
    from meridian.adapters import alpaca
    OUT["alpaca"] = {"paper_available": alpaca.paper_available(), "endpoint": alpaca._paper_base(),
                     "KORUMA_TIF": alpaca.KORUMA_TIF, "KORUMA_COID_ONEK": alpaca.KORUMA_COID_ONEK,
                     "ENGINE_COID_PREFIX": alpaca.ENGINE_COID_PREFIX}
    try:
        from meridian import broker as _bk
        OUT["alpaca"]["ENTRY_TIF"] = _bk.ENTRY_TIF
        OUT["alpaca"]["ENTRY_TIF_ALLOWED"] = list(_bk.ENTRY_TIF_ALLOWED)
        OUT["alpaca"]["ENTRY_LAW_VERSION"] = _bk.ENTRY_LAW_VERSION
        OUT["alpaca"]["entry_law"] = _bk.entry_law()
    except Exception as e:
        OUT["alpaca"]["_broker_hata"] = f"{type(e).__name__}: {e}"

    acct = alpaca.account()
    OUT["alpaca"]["account"] = ({k: acct.get(k) for k in
                                 ("equity", "last_equity", "cash", "portfolio_value", "created_at",
                                  "status", "account_number")} if acct else None)
    OUT["alpaca"]["positions"] = [{k: p.get(k) for k in
                                   ("symbol", "qty", "avg_entry_price", "side", "cost_basis",
                                    "market_value", "unrealized_pl")}
                                  for p in alpaca.positions()]

    # --- TÜM emirler (sayfalı, geriye doğru) + bacakları düzleştir (ebeveyn bağı KORUNUR)
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
        if isinstance(o, dict) and o.get("id"):
            o = {**o, "_parent_id": parent}
            duz[o["id"]] = o
            for l in (o.get("legs") or []):
                _ekle(l, o["id"])
    for o in tum:
        _ekle(o)
    # ÇIKIŞ BACAĞI İÇİN GEREKEN ALANLAR: `limit_price` (stop bacağında null olması = MARKET kanıtı),
    # `order_class`, `replaced_*` (koruma yeniden kurulumu), `legs` sayısı.
    ALANLAR = ("id", "_parent_id", "client_order_id", "symbol", "side", "type", "order_class", "qty",
               "filled_qty", "filled_avg_price", "limit_price", "stop_price", "trail_percent",
               "status", "time_in_force", "extended_hours", "created_at", "submitted_at",
               "filled_at", "canceled_at", "expired_at", "replaced_at", "replaced_by", "replaces",
               "legs_n")
    def _satir(o):
        r = {k: o.get(k) for k in ALANLAR}
        r["legs_n"] = len(o.get("legs") or [])
        return r
    OUT["alpaca"]["orders"] = {
        "sayfalar": sayfalar, "n_ust_duzey": len(tum), "n_tekil_bacaklarla": len(duz),
        "status_dagilim": dict(Counter(str(o.get("status")) for o in duz.values())),
        "side_dagilim": dict(Counter(str(o.get("side")) for o in duz.values())),
        "satirlar": sorted([_satir(o) for o in duz.values()],
                           key=lambda x: str(x.get("submitted_at") or "")),
    }

    # --- dolum OLAYI düzeyi + ücretler
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

# ---------------------------------------------------------------- (3) SATIŞ dolumu olan sembollerin
# konsolide barları — çıkış slipajı ölçülebilirse paydası buradan gelir. Emir listesi okunduktan
# SONRA çalışır: hangi sembol/hangi gün satış doldu, ONLARI çeker (kör tarama yok).
try:
    from meridian.adapters import alpaca
    satis_gun: dict = {}
    for a in ((OUT.get("alpaca") or {}).get("activities") or {}).get("FILL", {}).get("kayitlar") or []:
        if str(a.get("side", "")).startswith("sell"):
            gun = str(a.get("transaction_time") or "")[:10]
            if gun:
                satis_gun.setdefault(gun, set()).add(str(a.get("symbol")).upper())
    cikis: dict = {}
    for gun, syms in sorted(satis_gun.items()):
        syms = sorted(syms)
        blok = {}
        for etiket, feed in (("sip", "sip"), ("iex", "iex")):
            try:
                d = alpaca._get_data("/v2/stocks/bars",
                                     {"symbols": ",".join(syms), "timeframe": "1Day",
                                      "start": gun, "end": gun, "limit": 100, "feed": feed,
                                      "adjustment": "split", "sort": "asc"}, 30.0)
                blok[f"gunluk_{etiket}"] = d.get("bars")
            except Exception as e:
                blok[f"gunluk_{etiket}"] = {"_hata": f"{type(e).__name__}: {getattr(e, 'reason', e)}",
                                            "_status": getattr(e, "status", None)}
            try:
                d = alpaca._get_data("/v2/stocks/bars",
                                     {"symbols": ",".join(syms), "timeframe": "1Min",
                                      "start": f"{gun}T13:25:00Z", "end": f"{gun}T20:05:00Z",
                                      "limit": 10000, "feed": feed, "adjustment": "split",
                                      "sort": "asc"}, 30.0)
                blok[f"dakika_{etiket}"] = d.get("bars")
            except Exception as e:
                blok[f"dakika_{etiket}"] = {"_hata": f"{type(e).__name__}: {getattr(e, 'reason', e)}",
                                            "_status": getattr(e, "status", None)}
        cikis[gun] = {"semboller": syms, **blok}
    OUT["cikis_gunu_barlari"] = {"n_gun": len(cikis), "gunler": cikis,
                                 "not": "SATIŞ dolumu OLAN gün/sembol çiftleri için; yoksa boştur (n=0 kanıtı)"}
except Exception as e:
    OUT["cikis_gunu_barlari"] = {"_hata": f"{type(e).__name__}: {e}"}

json.dump(OUT, sys.stdout, ensure_ascii=False, indent=1, default=str)

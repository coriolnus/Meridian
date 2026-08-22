"""WP2/SB-2 · DAVRANIŞSAL EOD SÜPÜRME KANITI — CANLI HAM ÇEKİM (SALT-OKUMA).

KOŞUM (yerelden, stdin deseni — canlıya DOSYA YAZILMAZ; emsal: exe007/edg037/edg038):
    ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 \
        'cd /opt/meridian && ./.venv/bin/python -' \
        < research/olcumler/wp2_eod_supurme_2026-08-22/canli_cek.py \
        > research/olcumler/wp2_eod_supurme_2026-08-22/canli_ham.json

NE ÖLÇER (A4 sorusu: "fixli süpürücü GERÇEK bir EOD süpürmesinde koştu mu?" — kayıt bugüne
dek YOK):
  (1) events.jsonl — süpürme ailesinin ÜÇ olayı (`mirror_stale_entries_cancelled` = günlük
      kadans, `mirror_entries_cancelled` = HALT/breaker, `mirror_cancel_sinif_dokumu` =
      koruma-karşılaşma dökümü) + `mirror_entry_cancel_failed` (düşen denemeler) — TÜM satırlar.
  (2) events.jsonl — `daily_cycle` olayları (hangi seanslar gerçekten İŞLENDİ; payda budur).
  (3) portfolio.json `last_date` (kitabın işlediği son seans).
  (4) Broker emir defteri (GET /v2/orders?status=closed — SALT-OKUMA): son ~20 günün
      canceled/expired emirleri; akşam-iptali deseni yerelde bu hamdan çıkarılır.

YAZMA YOK: hiçbir dosya açılıp yazılmaz, hiçbir emir/POST yok. UYDURMA YASAĞI: okunamayan
kalem null + `_hata` alanıyla döner (null = ölçülemedi ≠ 0, v196).
"""
import datetime as dt
import json

OUT: dict = {"kalem": "WP2/SB-2 davranışsal EOD süpürme kanıtı (A4)",
             "cekim_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
             "makine": "A1 (canli)"}

try:
    from meridian import store
except Exception as e:
    OUT["_hata"] = f"meridian.store import: {type(e).__name__}: {e}"
    print(json.dumps(OUT))
    raise SystemExit(0)

SUPURME_OLAYLARI = ("mirror_stale_entries_cancelled", "mirror_entries_cancelled",
                    "mirror_cancel_sinif_dokumu", "mirror_entry_cancel_failed")

# (1)+(2) olay defteri — tek okuma, iki süzgeç
try:
    rows = store.read_jsonl("events.jsonl")
    sup = [r for r in rows if r.get("event") in SUPURME_OLAYLARI]
    OUT["supurme_olaylari"] = {"n": len(sup), "satirlar": sup}
    dc = [{"ts": r.get("ts"), "date": r.get("date")} for r in rows
          if r.get("event") == "daily_cycle"]
    OUT["daily_cycle"] = {"n": len(dc), "satirlar": dc[-40:]}
    OUT["defter_toplam_satir"] = len(rows)
except Exception as e:
    OUT["supurme_olaylari"] = {"n": None, "_hata": f"{type(e).__name__}: {e}"}
    OUT["daily_cycle"] = {"n": None, "_hata": f"{type(e).__name__}: {e}"}

# (3) kitabın son seansı
try:
    pf = store.read_json("portfolio.json", {}) or {}
    OUT["kitap_son_seans"] = pf.get("last_date")
except Exception as e:
    OUT["kitap_son_seans"] = None
    OUT["kitap_hata"] = f"{type(e).__name__}: {e}"

# (4) broker emir defteri — kapalı emirler (GET, salt-okuma; sayfalama: submitted_at desc)
try:
    from meridian.adapters import alpaca
    if not alpaca.paper_available():
        OUT["broker_kapali_emirler"] = {"n": None, "_hata": "paper_available()=False"}
    else:
        ALAN = ("symbol", "client_order_id", "status", "side", "order_type", "time_in_force",
                "submitted_at", "canceled_at", "expired_at", "filled_at", "updated_at",
                "filled_qty", "order_class")
        toplanan, until = [], None
        for _ in range(6):                       # 6 sayfa x 500 — ~20 gün fazlasıyla
            sayfa = alpaca.orders(status="closed", limit=500, nested=True, until=until)
            if not sayfa:
                break
            toplanan.extend(sayfa)
            en_eski = min((o.get("submitted_at") or "" for o in sayfa)) or None
            if not en_eski or en_eski == until:
                break
            until = en_eski
        kesit = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=20)
        kes = kesit.isoformat()
        pencere = [o for o in toplanan if str(o.get("submitted_at") or "") >= kes
                   or str(o.get("canceled_at") or "") >= kes
                   or str(o.get("expired_at") or "") >= kes]
        OUT["broker_kapali_emirler"] = {
            "n_toplam_cekilen": len(toplanan), "n_pencere_20g": len(pencere),
            "satirlar": [{k: o.get(k) for k in ALAN} for o in pencere]}
except Exception as e:
    OUT["broker_kapali_emirler"] = {"n": None, "_hata": f"{type(e).__name__}: {e}"}

print(json.dumps(OUT))

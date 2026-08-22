"""WP2/SB-2 · canli_ham.json → ozet.json (yerel, salt-okuma analiz).

SORU: son 10 İŞLENEN seansta EOD süpürmesi (günlük kadans `mirror_stale_entries_cancelled`)
fiilen koştu mu; kaç emir süpürdü; broker emir defterindeki akşam canceled/expired deseni
bununla tutuyor mu? (UYDURMA YASAĞI: ölçülemeyen alan null + neden.)
"""
import json
import pathlib
from collections import Counter

D = pathlib.Path(__file__).parent
ham = json.loads((D / "canli_ham.json").read_text())

ozet = {"kaynak": "canli_ham.json", "cekim_zamani": ham.get("cekim_zamani"),
        "kitap_son_seans": ham.get("kitap_son_seans")}

sup = (ham.get("supurme_olaylari") or {}).get("satirlar")
dcler = (ham.get("daily_cycle") or {}).get("satirlar")

if sup is None or dcler is None:
    ozet["_hata"] = "olay defteri okunamadı — süpürme geçmişi ÖLÇÜLEMEDİ"
else:
    # işlenen seanslar (payda) — daily_cycle.date, son 10 benzersiz
    seanslar = []
    for r in dcler:
        d = r.get("date")
        if d and d not in seanslar:
            seanslar.append(d)
    son10 = seanslar[-10:]
    # süpürme olayları: olay-adına göre ayrıştır
    kadans = [r for r in sup if r.get("event") == "mirror_stale_entries_cancelled"]
    halt = [r for r in sup if r.get("event") == "mirror_entries_cancelled"]
    dokum = [r for r in sup if r.get("event") == "mirror_cancel_sinif_dokumu"]
    dusen = [r for r in sup if r.get("event") == "mirror_entry_cancel_failed"]
    kadans_by_date = {}
    for r in kadans:
        kadans_by_date.setdefault(r.get("date"), []).append(r)
    tablo = []
    for s in son10:
        evs = kadans_by_date.get(s, [])
        tablo.append({"seans": s, "kadans_supurme_kosdu": bool(evs),
                      "n_olay": len(evs),
                      "cancelled": sum(int(e.get("cancelled") or 0) for e in evs) if evs else None,
                      "kept": sum(int(e.get("kept") or 0) for e in evs) if evs else None,
                      "foreign": sum(int(e.get("foreign") or 0) for e in evs) if evs else None,
                      "ts": [e.get("ts") for e in evs]})
    ozet["son10_islenen_seans"] = tablo
    ozet["sayimlar"] = {
        "kadans_supurme_toplam_olay": len(kadans),
        "kadans_kosan_seans": sum(1 for t in tablo if t["kadans_supurme_kosdu"]),
        "kadans_kosMAyan_seans": sum(1 for t in tablo if not t["kadans_supurme_kosdu"]),
        "toplam_cancelled_son10": sum(t["cancelled"] or 0 for t in tablo),
        "halt_breaker_olay": len(halt),
        "sinif_dokumu_olay": len(dokum),
        "cancel_failed_olay": len(dusen)}
    ozet["kadans_tum_gecmis"] = [{"ts": r.get("ts"), "date": r.get("date"),
                                  "cancelled": r.get("cancelled"), "kept": r.get("kept"),
                                  "foreign": r.get("foreign")} for r in kadans]
    ozet["v220_sonrasi_ilk_gercek_supurme"] = next(
        ((r.get("ts"), r.get("cancelled")) for r in kadans
         if str(r.get("ts") or "") >= "2026-08-09"), None)

bro = ham.get("broker_kapali_emirler") or {}
if bro.get("satirlar") is None:
    ozet["broker"] = {"_hata": bro.get("_hata") or "satır yok — broker deseni ÖLÇÜLEMEDİ"}
else:
    rows = bro["satirlar"]
    ce = [o for o in rows if str(o.get("status")) in ("canceled", "expired")]
    def saat(o):
        ts = o.get("canceled_at") or o.get("expired_at") or o.get("updated_at") or ""
        return str(ts)[11:13] if len(str(ts)) > 13 else None
    aksam = [o for o in ce if (saat(o) or "") in ("19", "20", "21", "22")]  # UTC akşam penceresi
    ozet["broker"] = {
        "n_pencere_20g": bro.get("n_pencere_20g"),
        "n_canceled_expired": len(ce),
        "n_aksam_19_22_utc": len(aksam),
        "saat_dagilimi_utc": dict(Counter(saat(o) for o in ce)),
        "status_dagilimi": dict(Counter(str(o.get("status")) for o in rows)),
        "aksam_ornek": [{k: o.get(k) for k in ("symbol", "client_order_id", "status", "side",
                                               "canceled_at", "expired_at", "filled_qty")}
                        for o in aksam[:15]]}

(D / "ozet.json").write_text(json.dumps(ozet, indent=2, ensure_ascii=False))
print(json.dumps(ozet, indent=2, ensure_ascii=False)[:4000])

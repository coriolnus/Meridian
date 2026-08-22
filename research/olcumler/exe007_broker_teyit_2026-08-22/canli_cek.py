"""EXE-2026-007 · broker-teyitli defter — CANLI HAM KANIT ÇEKİMİ (SALT-OKUMA).

KOŞUM (yereldeki oturumdan, stdin deseni — canlıya DOSYA YAZILMAZ; emsal: edg037/edg038):
    ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 \
        'cd /opt/meridian && ./.venv/bin/python -' \
        < research/olcumler/exe007_broker_teyit_2026-08-22/canli_cek.py \
        > research/olcumler/exe007_broker_teyit_2026-08-22/canli_ham.json

NE ÇEKER (hepsi `meridian.store` üzerinden — DB-arkalıklı defterlerde otoriter kaynak DB'dir):
  (1) trades.jsonl — TÜM satırlar (indeksli; Ö3 defter-indeksi kıyası ham liste üzerinde yapılır).
      Satır başına yalnız ölçümün kullandığı alanlar taşınır (id/ticker/ts_open/ts_close/
      pnl_dollars/kaynak/plan_id/regime) — sır yok, fazlalık yok.
  (2) hermes_status.json — `_horizon_ok`un tabanı: `hermes_runtime._restored_baseline`
      `store.read_json(STATUS_FILE).get("last_reflect_at")` okur (hermes_runtime.py:360).
      Ö3'ün "yansıma tabanı" kaynağı TAM OLARAK budur; tahmin değil, kod okundu.

YAZMA YOK: hiçbir dosya açılıp yazılmaz, hiçbir emir/POST yok. UYDURMA YASAĞI: okunamayan
kalem null + `_hata` alanıyla döner.
"""
import datetime as dt
import json

OUT: dict = {"kart": "EXE-2026-007",
             "cekim_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
             "makine": "A1 (canli)"}

try:
    from meridian import store
except Exception as e:                      # içe aktarılamazsa her şey ölçülemedi
    OUT["_hata"] = f"meridian.store import: {type(e).__name__}: {e}"
    print(json.dumps(OUT))
    raise SystemExit(0)

# (1) canlı işlem defteri — otoriter okuma store üzerinden (DB devredeyse DB'den gelir)
try:
    trades = store.read_jsonl("trades.jsonl")
    ALANLAR = ("id", "ticker", "ts_open", "ts_close", "pnl_dollars", "kaynak",
               "plan_id", "regime", "exit_reason")
    OUT["trades"] = {"n": len(trades),
                     "satirlar": [{k: t.get(k) for k in ALANLAR} for t in trades]}
except Exception as e:
    OUT["trades"] = {"n": None, "_hata": f"{type(e).__name__}: {e}"}

# (2) yansıma tabanı — _horizon_ok'un okuduğu kalıcı kaynak (hermes_status.json)
try:
    hs = store.read_json("hermes_status.json", {}) or {}
    OUT["hermes_status"] = {"last_reflect_at": hs.get("last_reflect_at"),
                            "reflections": hs.get("reflections"),
                            "last_reflection": hs.get("last_reflection"),
                            "bg_reflect_by_regime": hs.get("bg_reflect_by_regime"),
                            "horizon_ready": hs.get("horizon_ready"),
                            "horizon_regime": hs.get("horizon_regime")}
except Exception as e:
    OUT["hermes_status"] = {"last_reflect_at": None, "_hata": f"{type(e).__name__}: {e}"}

print(json.dumps(OUT))

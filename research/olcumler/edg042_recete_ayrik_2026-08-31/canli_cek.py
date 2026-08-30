"""EDG-2026-042 · gerçek friksiyon — CANLI HAM KANIT ÇEKİMİ (SALT-OKUMA, BETİMLEYİCİ ARA-KOŞUM).

KOŞUM (yereldeki oturumdan, stdin deseni — canlıya DOSYA YAZILMAZ; emsal: exe007/canli_cek.py):
    ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 \
        'cd /opt/meridian && ./.venv/bin/python -' \
        < research/olcumler/edg042_betimleyici_2026-08-22/canli_cek.py \
        > research/olcumler/edg042_betimleyici_2026-08-22/canli_ham.json

NE ÇEKER (hepsi `meridian.store` üzerinden — DB-arkalıklı defterlerde otoriter kaynak DB'dir):
  (1) entry_execution.jsonl — TÜM satırlar; satır başına yalnız kartın K1 filtresi + betimleyici
      çıktının kullandığı alanlar (date/plan_id/ticker/motor/karar/fill/fill_status/
      fill_vs_resmi_acilis_bps). Kill kuralı gereği payda YENİDEN TÜRETİLMEZ — ölçü, defterde
      KAYITLI `fill_vs_resmi_acilis_bps` alanıdır; bu betik onu yalnız TAŞIR.
  (2) trades.jsonl — TÜM satırlar; K2/K3 filtresi + kill kriterlerinin kullandığı alanlar
      (id/plan_id/ticker/ts_close/side/exit/exit_reason/kaynak/broker_teyit/broker_teyit_neden/
      alpaca_fill_price/alpaca_fill_beyan). `alpaca_fill_beyan` KIYASA GİRMEZ (beyan ≠ ölçüm);
      yalnız sayımı raporlansın diye taşınır.
  (3) goal.slippage_bps — kartın model-farkı sütununun KOŞUM GÜNÜ künyesi (kart beyanlı sınır 5:
      '5' sabitlenmez, koşum günkü değeri künyelenir). config.goal() salt-okumadır.

YAZMA YOK: hiçbir dosya açılıp yazılmaz, hiçbir emir/POST yok. UYDURMA YASAĞI: okunamayan
kalem null + `_hata` alanıyla döner.
"""
import datetime as dt
import json

OUT: dict = {"kart": "EDG-2026-042",
             "kosum": "betimleyici_ara_kosum",
             "cekim_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
             "makine": "A1 (canli)"}

try:
    from meridian import store
except Exception as e:                      # içe aktarılamazsa her şey ölçülemedi
    OUT["_hata"] = f"meridian.store import: {type(e).__name__}: {e}"
    print(json.dumps(OUT))
    raise SystemExit(0)

# (1) E2 giriş-icra defteri — K1'in tek kaynağı
try:
    rows = store.read_jsonl("entry_execution.jsonl")
    # `ts` (P-3/AYRIK, operatör kararı 2026-08-31): K1'i bölen ANAHTAR. Gönderim anının
    # damgası — defterde ZATEN dolu, burada yalnız TAŞINIR (türetilmez). Bu alan olmadan
    # kollar ayrılamaz: `pencere` damgasına göre bölmek kaydırma öncesi 13 damgasız satırı
    # her iki koldan düşürürdü (EXE-009 kill#3 geriye dönük etiketlemeyi yasaklar).
    E2_ALAN = ("date", "plan_id", "ticker", "motor", "karar", "fill", "fill_status",
               "fill_vs_resmi_acilis_bps", "ts")
    OUT["entry_execution"] = {"n": len(rows),
                              "satirlar": [{k: r.get(k) for k in E2_ALAN} for r in rows]}
except Exception as e:
    OUT["entry_execution"] = {"n": None, "_hata": f"{type(e).__name__}: {e}"}

# (2) işlem defteri — K2/K3'ün tek kaynağı
try:
    trades = store.read_jsonl("trades.jsonl")
    TR_ALAN = ("id", "plan_id", "ticker", "ts_close", "side", "exit", "exit_reason",
               "kaynak", "broker_teyit", "broker_teyit_neden",
               "alpaca_fill_price", "alpaca_fill_beyan")
    OUT["trades"] = {"n": len(trades),
                     "satirlar": [{k: t.get(k) for k in TR_ALAN} for t in trades]}
except Exception as e:
    OUT["trades"] = {"n": None, "_hata": f"{type(e).__name__}: {e}"}

# (3) model varsayımının koşum-günü künyesi
try:
    from meridian import config
    OUT["goal_slippage_bps"] = config.goal().get("slippage_bps")
except Exception as e:
    OUT["goal_slippage_bps"] = None
    OUT["goal_slippage_bps_hata"] = f"{type(e).__name__}: {e}"

print(json.dumps(OUT))

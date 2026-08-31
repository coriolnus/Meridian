"""EXE-2026-009 · pencere alt-bant HAM ÇEKİMİ (SALT-OKUMA; EDG-042 haftalık koşumun YANINA).

Kart: research/cards/EXE-2026-009-pencere-kaydirma.yaml (DONUK). EDG-042'nin donuk reçetesi
(canli_cek.py + olcum.py) DEĞİŞTİRİLMEDİ — alt-bant katmanı AYRI çekim + AYRI modülle onun
ÜSTÜNE eklenir (mimari gerekçe pencere_altbant.py başlığında).

KOŞUM (haftalık 042 koşumunun [1] adımıyla aynı ssh-stdin deseni; canlıya DOSYA YAZILMAZ):
    ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 \
        'cd /opt/meridian && ./.venv/bin/python -' \
        < research/olcumler/edg042_kosum_<TARIH>/pencere_cek.py \
        > research/olcumler/edg042_kosum_<TARIH>/pencere_ham.json

NE ÇEKER: entry_execution.jsonl TÜM satırları — alt-bant katmanının K1 filtresi + damga alanları
(date/plan_id/ticker/motor/karar/fill/fill_status/fill_vs_resmi_acilis_bps/pencere). Ölçü, E2'de
KAYITLI `fill_vs_resmi_acilis_bps` alanıdır (042 kill #1/#2 aynen: payda yeniden türetilmez).
`pencere` damgası da yalnız TAŞINIR — damgasız (kaydırma-öncesi) satır damgasız kalır (geriye
dönük etiketleme YASAK, EXE-009 kill#3).

YAZMA YOK · UYDURMA YASAĞI: okunamayan kalem null + `_hata` alanıyla döner."""
import datetime as dt
import json

OUT: dict = {"kart": "EXE-2026-009",
             "kosum": "pencere_altbant_ham_cekimi",
             "cekim_zamani": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
             "makine": "A1 (canli)"}

try:
    from meridian import store
except Exception as e:                      # içe aktarılamazsa her şey ölçülemedi
    OUT["_hata"] = f"meridian.store import: {type(e).__name__}: {e}"
    print(json.dumps(OUT))
    raise SystemExit(0)

try:
    rows = store.read_jsonl("entry_execution.jsonl")
    E2_ALAN = ("date", "plan_id", "ticker", "motor", "karar", "fill", "fill_status",
               "fill_vs_resmi_acilis_bps", "pencere")
    OUT["entry_execution"] = {"n": len(rows),
                              "satirlar": [{k: r.get(k) for k in E2_ALAN} for r in rows]}
except Exception as e:
    OUT["entry_execution"] = {"n": None, "_hata": f"{type(e).__name__}: {e}"}

# yürürlük rejimi künyesi: çekim ANINDA canlıda hangi tetik sabiti koşuyor (tek kaynaktan)
try:
    from meridian import barclock
    OUT["yururluk_rejimi"] = barclock.pencere_rejimi()
except Exception as e:
    OUT["yururluk_rejimi"] = None
    OUT["yururluk_rejimi_hata"] = f"{type(e).__name__}: {e}"

print(json.dumps(OUT))

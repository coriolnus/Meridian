"""EXE-2026-009 · K1 ayrık-kol HAM ÇEKİMİ (SALT-OKUMA; EDG-042 haftalık koşumun YANINA).

Kart: research/cards/EXE-2026-009-pencere-kaydirma.yaml, hüküm bloğu `p2_kapanis_2026_09_01`.
EDG-042'nin donuk reçetesi (canli_cek.py + olcum.py) DEĞİŞTİRİLMEDİ — hakem katmanı AYRI çekim +
AYRI rapor modülüyle onun ÜSTÜNE eklenir (mimari gerekçe pencere_altbant.py başlığında).
2026-08-22 hakem dizini TARİHÇEDİR ve tek bayt değişmedi; bu dosya onun P-2 revizyonudur.

KOŞUM (haftalık 042 koşumunun [1] adımıyla aynı ssh-stdin deseni; canlıya DOSYA YAZILMAZ):
    ssh -i ~/.ssh/oci-a1.key ubuntu@130.61.126.87 \
        'cd /opt/meridian && ./.venv/bin/python -' \
        < research/olcumler/edg042_hakem_2026-09-01/pencere_cek.py \
        > research/olcumler/edg042_hakem_2026-09-01/pencere_ham.json

NE ÇEKER: entry_execution.jsonl TÜM satırları — hakem katmanının K1 filtresi + BÖLME + çapraz
alanları (date/plan_id/ticker/motor/karar/fill/fill_status/fill_vs_resmi_acilis_bps/pencere/ts).
Ölçü, E2'de KAYITLI `fill_vs_resmi_acilis_bps` alanıdır (042 kill #1/#2 aynen: payda yeniden
türetilmez). `pencere` damgası ve `ts` yalnız TAŞINIR — türetilmez, düzeltilmez, doldurulmaz.

`ts` NEDEN EKLENDİ (P-1'in görünmezlik zehiri, kart p2_kapanis): hakem P-2'den itibaren satırı
GÖNDERİM ANIYLA böler, ama bu çekim `ts` alanını HİÇ taşımıyordu — hakem kendi bölme anahtarını
göremiyordu. Alan listesine EKLEME budur ve YALNIZ budur: alan çıkarmak K1 filtresini ya da
damga↔ts çapraz sütununu kör ederdi.

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
    # `ts` = P-2 bölme anahtarı (gönderim anı) · `pencere` = artık BÖLMEYEN, DOĞRULAYAN damga.
    # Liste 2026-08-22 çekiminin listesi + `ts`'tir; başka alan eklenmedi/çıkarılmadı.
    E2_ALAN = ("date", "plan_id", "ticker", "motor", "karar", "fill", "fill_status",
               "fill_vs_resmi_acilis_bps", "pencere", "ts")
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

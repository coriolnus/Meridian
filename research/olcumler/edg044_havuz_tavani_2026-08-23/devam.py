#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""EDG-2026-044 aşama-1 DEVAM koşucusu — arka plan görev sınırı (~60 dk) tam diziyi kestiği
için kalan hücreler TEK TEK koşulur (her hücre < 60 dk). İş yükü ve mekanik olcum.py'den
AYNEN alınır (aynı sabit aday kümesi, aynı havuz yolu) — hiçbir eşik/tanım değişmedi.
Kullanım: devam.py <ETIKET> <ISCI>   (örn. devam.py B1 3)
4 sayılan hücre tamamlanınca eşik kıyası + determinizm kontrolü yapılır, sonuc.json yazılır."""
import json
import os
import sys
import time

OUTDIR = "/Users/erdemozturk/AI-Trading/research/olcumler/edg044_havuz_tavani_2026-08-23"
sys.path.insert(0, OUTDIR)
import olcum  # noqa: E402  (REPO yolunu kendisi ekler)

PARTIAL = os.path.join(OUTDIR, "sonuc_partial.json")


def main() -> None:
    label, workers = sys.argv[1], int(sys.argv[2])
    with open(PARTIAL) as f:
        sonuc = json.load(f)
    if any(c["hucre"] == label for c in sonuc["hucreler"]):
        print(f"{label} zaten kayıtlı — çift koşum reddedildi", flush=True)
        return
    jobs = olcum.build_jobs()
    c = olcum.run_cell(label, workers, jobs)
    sonuc["hucreler"].append(c)
    sonuc.setdefault("kesinti_notu", (
        "İlk koşum (KAL+A1+B1-başlangıcı) arka plan görev sınırında ~60 dk'da öldürüldü "
        "(03:22:38→04:22 kill; B1 ~2 dk'da kesildi, kalıcı yazım yok). Kalan hücreler aynı "
        "iş yükü/mekanikle devam.py üzerinden TEK TEK, yine SIRAYLA koşuldu."))
    with open(PARTIAL, "w") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=1)
    print(f"  bitti: {c['duvar_saati_sn']} sn (işçi={workers})", flush=True)

    if len(sonuc["hucreler"]) < 4:
        return
    # FİNALİZE — olcum.py main() sonundaki mekanik kıyasın birebir kopyası
    fp_setleri = [json.dumps(c["sonuc_parmak_izleri"], sort_keys=True) for c in sonuc["hucreler"]]
    sonuc["determinizm_ayni_sonuclar"] = len(set(fp_setleri)) == 1
    t2 = [c["duvar_saati_sn"] for c in sonuc["hucreler"] if c["isci"] == 2]
    t3 = [c["duvar_saati_sn"] for c in sonuc["hucreler"] if c["isci"] == 3]
    med = lambda v: sorted(v)[len(v) // 2] if len(v) % 2 else sum(sorted(v)[len(v) // 2 - 1:len(v) // 2 + 1]) / 2
    kiyas = {}
    for ad, agg in (("ortalama", lambda v: sum(v) / len(v)), ("medyan", med)):
        a2, a3 = agg(t2), agg(t3)
        oran = a3 / a2
        kiyas[ad] = {"t2_sn": round(a2, 2), "t3_sn": round(a3, 2),
                     "oran_O1_3isci_bolu_2isci": round(oran, 4),
                     "kazanc_pct": round((1 - oran) * 100, 2),
                     "esik_pct20_karsilandi": (1 - oran) >= 0.20}
    sonuc["esik_kiyasi"] = {"kural": "kart success_metric aşama-1: kazanç ≥ %20 değilse kart kapanır",
                            "t2_kosumlari_sn": t2, "t3_kosumlari_sn": t3, **kiyas}
    sonuc["bitis_yuku"] = olcum.sysload()
    with open(os.path.join(OUTDIR, "sonuc.json"), "w") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=1)
    os.remove(PARTIAL)
    print("SONUC:", json.dumps(sonuc["esik_kiyasi"], ensure_ascii=False, indent=1), flush=True)
    print("determinizm_ayni_sonuclar:", sonuc["determinizm_ayni_sonuclar"], flush=True)


if __name__ == "__main__":
    main()

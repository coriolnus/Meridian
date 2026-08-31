#!/usr/bin/env python3
"""EDG-066 geri-dolum kapsam dosyasını üretir — TEK kaynak bu betiktir, kapsam.txt elle
düzenlenmez. Üçlü birleşim (operatör kararı 2026-08-31: "S&P 500 + Nasdaq-100 birleşimi"
+ pitlaw beyanı EDG-066 hükmünde):

  1. PIT S&P 500: research/pit_universe/sp500_uyelik_tarihi.csv — 2020-01-01'den dosya
     sonuna (2026-06-30) kadar HERHANGİ bir gün üye olmuş her sembol. Sağkalan-yanlılığını
     S&P tarafında kapatır: 2020'de düşen üyeler de arşive girer (⑥a eğitimi pitlaw'a tabi).
  2. NDX-100 güncel anlık görüntü: ndx100_2026-08-31.txt (PIT DEĞİL — beyan dosya başında).
  3. Canlı evren anlık görüntüsü: evren_2026-08-31.txt (ticaret ettiklerimiz her koşulda kapsanır).

Çıktı: kapsam.txt (sıralı, satır başına sembol, başlıkta üretim künyesi).
Sembol biçimi feed ile birebir: sınıf hisseleri nokta taşır (BRK.B, BF.B) — doğrulandı
2026-08-25 sayımında.
"""
from __future__ import annotations

import csv
import pathlib
import sys

BURA = pathlib.Path(__file__).resolve().parent
KOK = BURA.parents[2]
PENCERE_BASI = "2020-01-01"


def yorum_suz(yol: pathlib.Path) -> set[str]:
    return {s.strip().upper() for s in yol.read_text().splitlines()
            if s.strip() and not s.strip().startswith("#")}


def main() -> int:
    pit = set()
    son_tarih = ""
    with (KOK / "research" / "pit_universe" / "sp500_uyelik_tarihi.csv").open() as f:
        for satir in csv.reader(f):
            if satir and satir[0][:1].isdigit() and satir[0] >= PENCERE_BASI:
                pit.update(satir[1].split(","))
                son_tarih = satir[0]
    ndx = yorum_suz(BURA / "ndx100_2026-08-31.txt")
    evren = yorum_suz(BURA / "evren_2026-08-31.txt")
    hepsi = sorted(pit | ndx | evren)

    hedef = BURA / "kapsam.txt"
    with hedef.open("w") as f:
        f.write("# ÜRETİLMİŞ — elle düzenlenmez; kaynak: kapsam_uret.py (EDG-066)\n")
        f.write(f"# PIT-S&P {PENCERE_BASI}->{son_tarih}: {len(pit)} · NDX anlık: {len(ndx)}"
                f" · evren anlık: {len(evren)} · birleşim: {len(hepsi)}\n")
        f.write("\n".join(hepsi) + "\n")
    print(f"yazıldı: {hedef} · PIT-S&P={len(pit)} NDX={len(ndx)} evren={len(evren)}"
          f" birleşim={len(hepsi)} (S&P son tarihi {son_tarih})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

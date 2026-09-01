#!/usr/bin/env python3
"""EDG-066 geri-dolum sürücüsü — IEX HIST tick arşivini GERİYE DOĞRU doldurur.

Tetik: meridian-geridolum.timer (saatlik) → meridian-geridolum.service (oneshot, uzun koşum).
Kurulu yeri /opt/veri/geridolum.py; repo kaynağı deploy/oracle-a1/geridolum.py (F9 sınıfı).
Ayrıştırıcı: /opt/veri/pilot.py (repo kaynağı research/olcumler/edg066_tick_arsiv/pilot.py,
EDG-066 kart artefaktı) — --kapsam /opt/veri/kapsam.txt ile (662 sembol, kapsam_uret.py üretir).

Operatör kararları (2026-08-31, EDG-066 kartında kayıtlı): kapsam S&P500+NDX100 birleşimi ·
pencere 2020-01→bugün geriye doğru · tavan 120 GB (pencere ÇIKTIdır) · seyreltme 1/sn +
işlemler tam + işlem-anı anlık görüntü · meridian-learn program bitene dek KAPALI (2 CPU
bu işe dedike — İŞÇİ=2 oradan gelir; learn geri açılırsa İŞÇİ yeniden değerlendirilir).

Bekçiler (her turda, iş AÇILMADAN önce):
  · RTH penceresi: ABD seansı içinde (ve seansa <35 dk kala) yeni tur açılmaz — canlı döngü
    makinenin sahibidir. Koşan tur kesilmez; nice/ionice zaten geri planda tutar.
  · 120 GB tavan: tick kalıcı artefaktları (kotasyon_1s+islem+sayim) tavana ulaştıysa çık,
    TAVAN-DOLDU işareti bırak (dolunca eski gün silme kararı operatörün — panik kararı yok).
  · Disk payı: ham gz geçicileri için <25 GB boş kaldıysa KIRMIZI çık (ENOSPC'ye yürüme).
  · flock tekilliği: iki sürücü aynı anda koşamaz (timer + elle koşum çakışması).

Hüküm/okuyucu (Yasa 6): stdout → journald (birim düşerse /api/infra 'arizali' sınıflar —
failed'in okuyucusu var); kalıcı defter /opt/veri/tick/manifest.jsonl (pilot yazar) +
gecilen.jsonl (tatil/veri-yok günleri, bu sürücü yazar).
"""
from __future__ import annotations

import datetime as dt
import fcntl
import json
import pathlib
import subprocess
import sys

KOK = pathlib.Path("/opt/veri")
PY = KOK / "pilot-venv" / "bin" / "python"
PILOT = KOK / "pilot.py"
KAPSAM = KOK / "kapsam.txt"
TAVAN_BAYT = 120 * 1000**3          # kart: "120 GB" — GB, GiB değil
DISK_PAYI_BAYT = 25 * 1000**3       # ham gz geçicileri (yoğun gün ~15 GB) + emniyet
PENCERE_BASI = dt.date(2020, 1, 1)
ISCI = 2
# Operatör kararı 2026-09-01 ("geri dolum kesintisiz çalışmalı, seans içi dahil"): seans
# penceresi kilidi kapatıldı. Eski davranışa dönüş: True. Kaynak sınırları (ISCI=2, TAVAN,
# DISK_PAYI) AYNEN — kesintisizlik kaynak çitlerini gevşetmez.
SEANS_KILIDI = False
TAZE_GUN = 5                        # bundan yeni boş HIST cevabı "henüz yayımlanmadı" sayılır


def rth_yakin(pay_dk: int = 35) -> bool:
    u = dt.datetime.now(dt.timezone.utc)
    if u.weekday() >= 5:
        return False
    dk = u.hour * 60 + u.minute + pay_dk
    # 13:20Z ön-pay ile 20:10Z: ABD seansı (yaz saati) + açılış/kapanış tamponu
    return 13 * 60 + 20 <= dk and u.hour * 60 + u.minute <= 20 * 60 + 10


def tick_bayt() -> int:
    return sum(f.stat().st_size
               for alt in ("kotasyon_1s", "islem", "sayim")
               for f in (KOK / "tick" / alt).glob("*") if f.is_file())


def bos_bayt() -> int:
    import shutil
    return shutil.disk_usage(KOK).free


def islenmis() -> set[str]:
    done = set()
    for ad in ("manifest.jsonl", "gecilen.jsonl"):
        y = KOK / "tick" / ad
        if y.exists():
            for satir in y.read_text().splitlines():
                try:
                    done.add(json.loads(satir)["gun"])
                except (ValueError, KeyError):
                    # sessiz-yutma: bozuk defter satırı tek günü düşürür, koşumu değil;
                    # gün yeniden denenir — kayıp değil yineleme üretir, KIRMIZI'ya gerek yok
                    print(f"UYARI: {ad} içinde çözülemeyen satır atlandı", flush=True)
    return done


def sonraki_gunler(n: int, done: set[str]) -> list[str]:
    out: list[str] = []
    g = dt.date.today() - dt.timedelta(days=1)
    while len(out) < n and g >= PENCERE_BASI:
        if g.weekday() < 5 and g.isoformat() not in done:
            out.append(g.isoformat())
        g -= dt.timedelta(days=1)
    return out


def main() -> int:
    kilit = (KOK / "geridolum.kilit").open("w")
    try:
        fcntl.flock(kilit, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print("zaten koşuyor — çıkılıyor (flock)")
        return 0

    if not (PILOT.exists() and KAPSAM.exists()):
        print(f"KIRMIZI: {PILOT} ya da {KAPSAM} yok — kurulum eksik", flush=True)
        return 1

    atlanan: set[str] = set()   # taze-boş günler — bu KOŞUM içinde tekrar denenmez
    while True:
        bugun = dt.date.today()   # koşum günlerce sürebilir — her turda tazelenir
        if SEANS_KILIDI and rth_yakin():
            print("seans penceresi (ya da <35 dk kala) — tur açılmadı, çıkılıyor")
            return 0
        kullanilan = tick_bayt()
        if kullanilan >= TAVAN_BAYT:
            (KOK / "tick" / "TAVAN-DOLDU").write_text(
                f"{dt.datetime.now(dt.timezone.utc).isoformat()} kullanılan={kullanilan}\n")
            print(f"TAVAN: {kullanilan / 1e9:.1f} GB >= 120 GB — çıkılıyor (karar operatörün)")
            return 0
        if bos_bayt() < DISK_PAYI_BAYT:
            print(f"KIRMIZI: disk payı < {DISK_PAYI_BAYT / 1e9:.0f} GB — ham geçiciler sığmaz",
                  flush=True)
            return 1

        done = islenmis() | atlanan
        gunler = sonraki_gunler(ISCI, done)
        if not gunler:
            print("PENCERE-TAMAM: 2020-01-01'e kadar tüm iş günleri işlendi/geçildi")
            (KOK / "tick" / "PENCERE-TAMAM").write_text(
                dt.datetime.now(dt.timezone.utc).isoformat() + "\n")
            return 0

        surecler = []
        for g in gunler:
            print(f"başlıyor: {g}", flush=True)
            p = subprocess.Popen(
                ["nice", "-n", "10", "ionice", "-c", "3", str(PY), str(PILOT),
                 "--gun", g, "--kapsam", str(KAPSAM)],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            surecler.append((g, p))

        for g, p in surecler:
            cikti, _ = p.communicate()
            son = cikti.strip().splitlines()[-3:] if cikti.strip() else ["<çıktı yok>"]
            if p.returncode == 0:
                print(f"bitti: {g} · " + " | ".join(son), flush=True)
            elif "boş döndü" in cikti:
                yas = (bugun - dt.date.fromisoformat(g)).days
                if yas > TAZE_GUN:
                    with (KOK / "tick" / "gecilen.jsonl").open("a") as f:
                        f.write(json.dumps({
                            "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
                            "gun": g, "neden": "hist-bos (tatil/yarım gün)"}) + "\n")
                    print(f"geçildi: {g} — HIST boş, yaş {yas} gün (tatil sayıldı)", flush=True)
                else:
                    atlanan.add(g)   # bu koşumda atla, kalıcı kayıt YOK — sonraki koşum yine dener
                    print(f"taze-boş: {g} — henüz yayımlanmamış olabilir, kalıcı kayıt yok",
                          flush=True)
            else:
                print(f"KIRMIZI: {g} rc={p.returncode}\n" + cikti[-2000:], flush=True)
                return 1   # birim failed → panoda görünür; timer sonraki saatte yeniden dener
    # not: while True'dan tek çıkışlar yukarıdaki return'lerdir


if __name__ == "__main__":
    sys.exit(main())

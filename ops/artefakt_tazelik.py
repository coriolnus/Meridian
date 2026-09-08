#!/usr/bin/env python3
"""ops/artefakt_tazelik.py — pano artefaktı kaynağından taze mi? ([5c] kapısı).

NEREDEN GELDİ. Gövde `dagit.sh`ın [5c] adımında iki-platform `stat` (`stat -f %m` / `stat -c %Y`)
ve iki-platform `find` (`-exec stat` / `-printf`) sarmalıyla yaşıyordu. TSK-176 Faz A1'de dosyaya
çıkarıldı: `deploy/ansible/dagit.yml` bu kapıyı Play 1'de (localhost, `check_mode: false`)
koşturacak ve gömülü çok-satır kabuk bir Ansible görevinde YASAK.

DEĞİŞMEZ:  mtime(meridian/web/pano.html)  >=  en yeni mtime(ui/ altındaki kaynak)

NEDEN VAR. [5b] "dağıtılan dosya = kaynak" varsayar ve Python için bu DOĞRU. shadcn göçüyle araya
bir DERLEME girdi: canlıya giden `meridian/web/pano*` artefaktı `ui/` altındaki kaynaktan
ÜRETİLİR. Kaynak değişip `npm run build` koşmazsa canlı sessizce bayat kalır ve [5b] bunu GÖREMEZ
(o Python mtime'ına bakar, artefaktı hiç tanımaz) — `meridian-learn`de yaşanan sessiz
etkisizliğin aynısı: doğru bir cümle, anlamsız bir güvence.

YERELDE ölçülür (dağıtımdan ÖNCE), çünkü onarım da yereldir: `cd ui && npm run build`. Canlıda
ölçmenin anlamı yok — orada kaynak zaten yok (rsync `/ui`yi dışlar).

KOMUT SATIRI SÖZLEŞMESİ:

    python ops/artefakt_tazelik.py --repo <depo-kökü>

Çıkış kodu HÜKÜMDÜR:
    0  TAMAM      artefakt kaynağından taze  → dağıtım sürer
    1  IHLAL      artefakt BAYAT             → dağıtım DURUR (onarım: cd ui && npm run build)
    2  ÖLÇÜLEMEDİ zemin yok                  → dağıtım sürer, ama "taze" DENMEZ

ÇIKIŞ 2 BEYANLI BİR DÜRÜSTLEŞMEDİR (davranış birebir kuralının tek istisnası, ölçülüp yazıldı
2026-09-08): dagit.sh'ın kabuk gövdesi, `ui/` altında hiç kaynak bulamadığında "TAMAM artefakt
kaynağından taze" basıyordu — ölçülemeyen bir hükmü TAZE saymak, uydurma yasağının tam karşıtı.
Yeni kod o hâli 2 ile ayırır. DAĞITIM AKIŞI DEĞİŞMEZ: çağıran 2'de eskisi gibi devam eder
(artefakt henüz derlenmemiş olabilir — bu bir arıza değil, bir ölçüm boşluğudur); değişen tek şey
operatörün okuduğu cümledir.

İKİ-PLATFORM SORUNU KÖKTEN GİTTİ: kabuk gövdesi BSD/GNU `stat` ve `find` farkını iki ayrı dalla
taşıyordu (biri sessizce boş dönerse hüküm kayardı). Python `os.stat` her iki platformda aynı
alanı verir — dal yok, ayrışacak ikinci kaynak yok.

KIYAS TAM SANİYEDEDİR, KESİRLİ DEĞİL (düzeltme turu 2, ölçüldü 2026-09-08). Kabuk gövdesi
`stat -f %m` / `stat -c %Y` / `find -printf '%T@' | cut -d. -f1` ile TAM SANİYE okuyordu ve
`os.stat().st_mtime` kesirlidir: artefakt T+0,2 · kaynak T+0,8 (aynı saniye) girdisinde eski
gövde `TAMAM`/0, ilk taşıma `IHLAL`/1 veriyordu — beyan dışı bir sapma, üstelik dağıtımı DURDURAN
yönde. Sınıf gerçek: `git checkout <sha>` (dagit.sh'ın kendi geri-alma reçetesi) bütün ağacı aynı
saniyenin içine yazar ve hüküm kesirlerin sırasına kalırdı. `int()` ile kırpma davranışı gömülü
gövdeyle BİREBİR yapar (Global Constraint). Çivi: `tests/test_ansible_dagit_v452.py` A4b5.

OKUYUCU (YASA 6): `dagit.sh` [5c] adımı · `deploy/ansible/dagit.yml` (Task 2) ·
`tests/test_ansible_dagit_v452.py` bölüm A4b · `tests/test_ui_pilot_kapilari_v286.py` G2c.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

#: Derlemeye giren kaynak uzantıları — kabuk gövdesindeki `-name` listesiyle BİREBİR.
KAYNAK_UZANTILAR = (".ts", ".tsx", ".css", ".html", ".json")
#: Kaynak ağacı ve ölçülen artefakt (depo köküne göreli).
UI_DIZIN = "ui"
ARTEFAKT_YOL = "meridian/web/pano.html"


def en_yeni_kaynak(ui: pathlib.Path) -> tuple[float | None, pathlib.Path | None]:
    """`ui/` altındaki (node_modules HARİÇ) en yeni kaynak dosyanın (mtime, yol)'u.

    `node_modules` DIŞLAMASI TAŞIYICIDIR: `npm install` oraya sürekli taze `.json`/`.ts`/`.css`
    yazar. Dışlama düşerse artefakt GERÇEKTEN tazeyken `IHLAL` basılır, HER dağıtım [5c]'de
    durur ve operatörün basılan reçeteyi (`npm run build`) koşması ihlali GİDERMEZ — aynı duvara
    çarpar. Çivi: `tests/test_ansible_dagit_v452.py` A4b6 (dışlama kalkınca kırmızı)."""
    enyeni: float | None = None
    enyeni_yol: pathlib.Path | None = None
    for p in ui.rglob("*"):
        if not p.is_file() or p.suffix not in KAYNAK_UZANTILAR:
            continue
        if "node_modules" in p.parts:
            continue
        m = p.stat().st_mtime
        if enyeni is None or m > enyeni:
            enyeni, enyeni_yol = m, p
    return enyeni, enyeni_yol


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="pano artefaktı kaynağından taze mi ([5c] kapısı)")
    ap.add_argument("--repo", required=True, help="depo kökü (yerel çalışma ağacı)")
    a = ap.parse_args(argv)
    kok = pathlib.Path(a.repo)

    ui = kok / UI_DIZIN
    if not ui.is_dir():
        print(f"  ÖLÇÜLEMEDİ kaynak ağacı yok ({UI_DIZIN}/) — kıyas zemini yok, dağıtım sürüyor")
        return 2

    art = kok / ARTEFAKT_YOL
    if not art.is_file():
        print(f"  ATLANDI pano artefaktı yok ({ARTEFAKT_YOL}, henüz derlenmedi) — "
              "kapı ÖLÇÜLEMEDİ, dağıtım sürüyor")
        return 2

    art_m = art.stat().st_mtime
    kay_m, kay_yol = en_yeni_kaynak(ui)
    if kay_m is None:
        print(f"  ÖLÇÜLEMEDİ {UI_DIZIN}/ altında kaynak dosya yok "
              f"({', '.join(KAYNAK_UZANTILAR)}) — dağıtım sürüyor")
        return 2

    # TAM SANİYE (davranış birebir — gerekçe dosya başlığında): kesirli kıyas aynı saniyeye düşen
    # bir ağaçta (örn. `git checkout <sha>`) hükmü kesirlerin sırasına bırakır ve dağıtımı durdurur.
    art_s, kay_s = int(art_m), int(kay_m)
    if art_s < kay_s:
        print(f"  IHLAL artefakt BAYAT: {ARTEFAKT_YOL} {art_s} < {UI_DIZIN}/ kaynak "
              f"{kay_s} ({kay_yol})")
        print("  onarım: cd ui && npm run build   (sonra dağıtımı tekrar koş — rsync idempotent)")
        return 1

    print("  TAMAM artefakt kaynağından taze")
    return 0


if __name__ == "__main__":
    sys.exit(main())

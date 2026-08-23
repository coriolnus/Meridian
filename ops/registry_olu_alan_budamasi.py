#!/usr/bin/env python3
"""registry_olu_alan_budamasi.py — 25a: skills_registry.json'daki OKUYUCUSUZ ölü alan budaması.

NEDEN BU BİR OPS BETİĞİ (repo düzenlemesi değil): kayıt defteri (`state/skills_registry.json`)
canlı A1'de yaşayan, git-İZSİZ bir state dosyasıdır — worktree'de kopyası yoktur ve canlı worker
koşarken state'e yazılmaz (CLAUDE.md §5). Budama bu yüzden koddan değil, BAKIM PENCERESİNDE
operatör/Rol-1 elinden bu betikle yapılır. Varsayılan DRY-RUN'dur; yazım yalnız `--uygula` ile.

ENVANTER HÜKMÜ ve YENİDEN DOĞRULAMA (K5 paketi, 2026-08-23):
  docs/DENETIM-OLU-BILESEN-ENVANTERI-2026-08-13.md §b-7, 12 registry alanını "hiçbir okuyucusu
  yok" saymıştı. Kaldırma günü YENİDEN grep'lendi (25a şartı: okuyucu çıkarsa KALDIRMA) ve
  12'nin YALNIZ 3'ü hâlâ okuyucusuz çıktı — envanterden bu yana okuyucu KAZANANLAR:

  KALDIRILMAZ (okuyucu/protokol kanıtı, 2026-08-23 grep):
    merged_into · retired_at   → skills/trading-skills-navigator/scripts/recommend.py
                                 (_facts_from_registry_entries; navigator emeklilik kapısı)
    agent_authored             → meridian/web/app.js "ajan yazdı" rozeti (skill sayfası)
    retired_folder · retired_requires · denetim_notu · aktivasyon_kosulu · stale_last_run_cleared
                               → tests/test_skill_cleanup_v121 sözleşme çivileri (C2/C7/C9) +
                                 skills/_emekli/README.md geri-dönüş protokolü
    retired_from_pipeline      → skills/_emekli/README.md geri-dönüş protokolü verisi (emekli
                                 skill'in eski boru hattı beyanı; silinirse dönüş yolu kaybolur)

  KALDIRILIR (üç alan; hâlâ sıfır okuyucu — YASA 6: okuyucusuz yazım yok):
    api_free · failure_count · engine
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import tempfile

#: 2026-08-23 grep'iyle DOĞRULANMIŞ okuyucusuz alanlar. Bu listeye ekleme yapmadan önce aynı
#: doğrulama zorunludur (okuyucu çıkan alan buraya giremez — üstteki KALDIRILMAZ listesi).
OLU_ALANLAR = ("api_free", "failure_count", "engine")

#: Okuyucusu/protokolü kanıtlı alanlar — betik bunları İSTESEN DE silmez (fail-closed).
KORUNAN_ALANLAR = frozenset({
    "merged_into", "retired_at", "agent_authored", "retired_folder", "retired_requires",
    "denetim_notu", "aktivasyon_kosulu", "stale_last_run_cleared", "retired_from_pipeline",
})


def buda(veri: dict) -> tuple[dict, dict]:
    """Kayıt defterinin `skills` haritasından OLU_ALANLAR'ı düşürür. Saf: dosya okumaz/yazmaz.

    Dönüş: (yeni_veri, rapor). Rapor alan→düşen-kayıt-sayısı taşır; hiç alan yoksa 0 (no-op
    güvenli). KORUNAN_ALANLAR'a dokunulmadığı yapısal olarak garantidir (yalnız OLU_ALANLAR
    gezilir)."""
    yeni = json.loads(json.dumps(veri))  # derin kopya — girdi sözlüğü çağıranın malıdır
    sayim = {alan: 0 for alan in OLU_ALANLAR}
    skills = yeni.get("skills")
    if isinstance(skills, dict):
        for _ad, kayit in skills.items():
            if not isinstance(kayit, dict):
                continue
            for alan in OLU_ALANLAR:
                if alan in kayit:
                    del kayit[alan]
                    sayim[alan] += 1
    return yeni, sayim


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--registry", default="state/skills_registry.json",
                    help="kayıt defteri yolu (varsayılan: state/skills_registry.json)")
    ap.add_argument("--uygula", action="store_true",
                    help="YAZ (varsayılan dry-run). Yalnız bakım penceresinde, canlı worker "
                         "dururken — atomik tmp+rename ile yazar.")
    args = ap.parse_args(argv)

    p = pathlib.Path(args.registry)
    if not p.is_file():
        print(f"HATA: kayıt defteri yok: {p}", file=sys.stderr)
        return 2
    try:
        veri = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        print(f"HATA: kayıt defteri JSON değil ({e}) — DOKUNULMADI", file=sys.stderr)
        return 2

    yeni, sayim = buda(veri)
    toplam = sum(sayim.values())
    for alan, n in sayim.items():
        print(f"  {alan:>15}: {n} kayıttan düşürülecek")
    print(f"TOPLAM {toplam} alan-örneği · mod: {'UYGULA' if args.uygula else 'DRY-RUN (yazım yok)'}")

    if args.uygula and toplam:
        # atomik yazım: yarım dosya, kilitsz okuyucular için bozuk JSON'dan kötüdür
        with tempfile.NamedTemporaryFile("w", dir=p.parent, delete=False,
                                         encoding="utf-8", suffix=".tmp") as f:
            json.dump(yeni, f, ensure_ascii=False, indent=2)
            tmp = pathlib.Path(f.name)
        tmp.replace(p)
        print(f"YAZILDI: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

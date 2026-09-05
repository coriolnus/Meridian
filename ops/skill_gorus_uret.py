#!/usr/bin/env python3
"""ops/skill_gorus_uret.py — GÖRÜŞ KUYRUĞUNUN SEANS-DIŞI ÜRETİCİSİ (EDG-2026-019 kill#1 kök çözümü).

NEDEN VAR. Kartın kill#1'i "görüş üretimi canlı döngü p95 süresini +%10'dan fazla artırırsa katman
KAPATILIR" der ve canlıda p95_pay 6,57 ölçüldü (2026-08-21'den beri): üretim, öğrenme kadansının
İÇİNDE senkron koşuyordu. Kapatma doğru hükümdü ama bir çözüm değildi — katman kapalıyken kanıt
birikmez ve kartın yeniden açılışı için gereken ölçüm hiç koşamaz. Kök çözüm işi İKİYE BÖLER:

  * KADANS İÇİ (gece döngüsü) — `skill_gorus.kuyruk_kadansi`: yalnız t-anı GİRDİ KESİTİ tek satır
    olarak `state/skill_gorus_kuyruk.jsonl`e eklenir. Ağır hesap YOK.
  * SEANS DIŞI (bu betik) — `skill_gorus.kuyruktan_uret`: işlenmemiş kesitlerden görüş satırları
    türetilir, deftere yazılır, kesit İŞLENDİ diye işaretlenir.

t-ÇİTİ. Üretilen satırın `ts`'i SNAPSHOT anıdır, üretim anı değil; üretici kesitte olmayan hiçbir
alana bakmaz. Yani bu betiğin gece yarısı mı ertesi öğlen mi koştuğu ÖLÇÜME GİRMEZ — geciken bir
koşum görüşü tazelemez, yalnız yazımı erteler.

KOŞUM SÖZLEŞMESİ KOMUT SATIRIDIR. Varsayılan KURU: hiçbir şey yazılmaz, ne yazılacağı basılır.
Yazım YALNIZ `--uygula` ile olur ve o da `config.SKILL_GORUS_URETIM_ACIK` bayrağının arkasındadır
(bayrak Rol-1'in kararıdır; bu betik onu AÇMAZ).

PENCERE SAYACI (EDG-2026-078 dilimi, EDG-2026-019 kill#3 borcu). Her `--uygula` koşumu ayrıca
`skill_gorus.rapor()`ı çağırıp skill×yüzey başına bir PENCERE satırını `state/skill_gorus_
pencereler.jsonl`e yazar (`skill_gorus.pencere_yaz`) — gün başına İDEMPOTENT (aynı gün ikinci kez
koşulursa yazmaz). `rapor()` bu defterden `ardisik_pencere` türetir; terfinin "2 ardışık pencere"
(Aşama B ön şartı) ve emekliliğin "3 ardışık pencere" (kart kill#3) şartları BUNSUZ ölçülemezdi.

KULLANIM:
    python ops/skill_gorus_uret.py                 # KURU koşu — ne üretilecek?
    python ops/skill_gorus_uret.py --uygula        # deftere yaz + kesitleri işaretle
    python ops/skill_gorus_uret.py --durum         # kuyruk derinliği (yazmaz, üretmez)
    python ops/skill_gorus_uret.py --tavan 500     # bu koşumda en fazla N görüş satırı
    python ops/skill_gorus_uret.py --llm           # EDG-2026-063 gölge üretici (beyan-only küme)
    python ops/skill_gorus_uret.py --llm --yuzey aday-siralayici   # yüzeyi açıkça seç

ÇIKIŞ KODLARI: 0 = koştu · 1 = `--uygula` istendi ama katman KAPALI (yazım olmadı).
"""
from __future__ import annotations

import argparse
import json
import sys

# Depo kökü yola girer: betik `python ops/...` diye koşulur, paket olarak değil.
import pathlib

KOK = pathlib.Path(__file__).resolve().parents[1]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from meridian import config, skill_gorus as sg  # noqa: E402


def _kuyruk_ozeti() -> dict:
    """Kuyruğun HAM SATIR TAŞIMAYAN özeti — derinlik, bekleyen gözlem, üretilen toplam."""
    rows = [r for r in sg.kuyruk_oku() if isinstance(r, dict)]
    bekleyen = [r for r in rows if not r.get("islendi")]
    tsler = [str(r.get("ts")) for r in bekleyen if r.get("ts")]
    return {"snapshot": len(rows), "bekleyen": len(bekleyen),
            "islenmis": len(rows) - len(bekleyen),
            "bekleyen_gozlem": sum(int(r.get("n_gozlem") or 0) for r in bekleyen),
            "en_eski_bekleyen_ts": (min(tsler) if tsler else None),
            "uretilen_toplam": sum(int(r.get("uretilen") or 0) for r in rows if r.get("islendi"))}


def _bas(baslik: str, veri: dict) -> None:
    print(f"== {baslik}")
    print(json.dumps(veri, ensure_ascii=False, indent=2, sort_keys=True, default=str))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="skill görüş kuyruğunun seans-dışı üreticisi (EDG-2026-019 / EDG-2026-063)")
    ap.add_argument("--uygula", action="store_true",
                    help="görüşleri deftere YAZ ve kesitleri işaretle (varsayılan: kuru koşu)")
    ap.add_argument("--durum", action="store_true",
                    help="yalnız kuyruk derinliğini bas; üretim yapma")
    ap.add_argument("--tavan", type=int, default=None,
                    help="bu koşumda en fazla N görüş satırı (varsayılan: tavan yok)")
    ap.add_argument("--llm", action="store_true",
                    help="EDG-2026-063 LLM gölge üreticisi (beyan-only skill kümesi)")
    # YÜZEY SEÇİMİ YALNIZ LLM YOLUNDA ANLAMLIDIR ve VARSAYILAN `cikis`i KAPSAMAZ: `cozucu_cikis`
    # görüşün `karar`ını okumaz, skill başına aday kümesini ölçer — beyan-only skill'lerin aday
    # kümesi ise skill'den bağımsız olduğu için `cikis` satırları ÖZDEŞ çıkar ve sahte bir
    # FDR-sağkalan üretebilir (inceleme bulgusu B1, 2026-09-01). Operatör bilerek isterse
    # `--yuzey cikis` verebilir; hüküm o zaman da Rol-1'indir.
    ap.add_argument("--yuzey", action="append", default=None,
                    choices=["aday-siralayici", "cikis"],
                    help="LLM üretiminde hangi yüzey(ler) (varsayılan: aday-siralayici)")
    a = ap.parse_args(argv)

    ozet = _kuyruk_ozeti()
    _bas("kuyruk", ozet)
    if a.durum:
        return 0

    bayrak = bool(config.SKILL_GORUS_URETIM_ACIK)
    print(f"== bayrak SKILL_GORUS_URETIM_ACIK={bayrak} · mod="
          f"{'UYGULA' if a.uygula else 'KURU KOŞU (varsayılan)'}")
    if a.uygula and not bayrak:
        # SESSİZ BAŞARI YOK: operatör "uygula" dedi, sistem yazmadı — bu bir ÇIKIŞ KODUDUR.
        print("KATMAN KAPALI: EDG-2026-019 kill#1 mandalı (config.SKILL_GORUS_URETIM_ACIK=False) "
              "— hiçbir satır yazılmadı. Açılış kartın resmileşmiş ölçümüyle ve Rol-1 kararıyla.",
              file=sys.stderr)
        return 1

    if a.llm:
        from meridian import skill_gorus_llm as sgl
        yuzeyler = tuple(a.yuzey) if a.yuzey else None      # None → modülün donuk varsayılanı
        sonuc = sgl.uret(apply=a.uygula, yuzeyler=yuzeyler)
        _bas("llm-golge-uretim (EDG-2026-063)", sonuc)
    else:
        sonuc = sg.kuyruktan_uret(apply=a.uygula, tavan=a.tavan)
        _bas("uretim (EDG-2026-019)", sonuc)
    _bas("kuyruk (koşum sonrası)", _kuyruk_ozeti())

    # PENCERE SAYACI (EDG-2026-078 dilimi, EDG-2026-019 kill#3 borcu) — YALNIZ `--uygula`da: kuru
    # koşu bir HÜKÜM üretmez, pencereye yazacak bir şey yoktur. `rapor()` burada BİR KEZ hesaplanır
    # ve pencere yazımına AYNEN geçilir — ikinci bir `rapor()` çağrısı aynı işi tekrarlamaz.
    if a.uygula:
        rapor_sonucu = sg.rapor()
        pencere_ozet = sg.pencere_yaz(rapor_sonucu)
        _bas("pencere-sayaci (EDG-2026-078)", pencere_ozet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

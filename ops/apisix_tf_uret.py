#!/usr/bin/env python3
"""ops/apisix_tf_uret.py — deploy/apisix/routes.yaml → altyapi/apisix/import.tf (TSK-176 T1 Task 2).

SÖZLEŞME KOMUT SATIRIDIR (vaka 2026-08-30: ops betiklerinin sözleşmesi `main()` değil, çağrılan
komuttur):

    python3 ops/apisix_tf_uret.py --cikti altyapi/apisix/import.tf   # üret (stdout'a YAZMAZ)
    python3 ops/apisix_tf_uret.py --kontrol                          # depodaki dosya güncel mi (0/1)

TEK KAYNAK. `deploy/apisix/routes.yaml` geçiş süresince canlı SSoT'dur (`ops/apisix_uygula.py`
onu Admin API'ye uygular); `altyapi/apisix/import.tf` ondan ÜRETİLİR ve ELLE DÜZENLENMEZ. İki
yerde elle tutulan bir kimlik listesi sessizce ayrışır — bu yüzden üretim burada, kıyas ise
çivide (`tests/test_apisix_tf_uret_v502.py` test_b) durur. `--kontrol` aynı kıyası operatörün ve
`altyapi/altyapi.sh import-uret` adımının koşabileceği biçimde verir.

OKUYUCULAR (Yasa 6 — üretilen `import.tf` okunmayan bir artefakt DEĞİLDİR):
  · `terraform plan` (A1'de `altyapi/altyapi.sh plan`) — import blokları `-generate-config-out`
    ile HCL üretir; import.tf'siz o adım hiçbir kaynağı tanımaz;
  · `tests/test_apisix_tf_uret_v502.py` test_b — depodaki dosya üreticinin çıktısıyla birebir mi;
  · `--kontrol` kipi (bu betik) — bayatlığı çıkış koduyla bildirir.

SIR YOK: bu betik ne admin anahtarını ne uç adresini görür; ürettiği HCL yalnız KİMLİK taşır
(anahtar kanalı `altyapi/altyapi.sh` ile `ops/apisix_uygula.py::kanal_bildir` sözleşmesindedir).

`meridian` İTHAL EDİLMEZ — bilinçli (CLAUDE.md §2): saf dosya dönüşümü `meridian.obs`a ulaşmaz,
dolayısıyla yerel canlı deftere yazmaz ve ajan tarafından da koşulabilir.
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROUTES = ROOT / "deploy/apisix/routes.yaml"
HEDEF = ROOT / "altyapi/apisix/import.tf"
BASLIK = "# ÜRETİLMİŞ — ops/apisix_tf_uret.py; kaynak deploy/apisix/routes.yaml. Elle düzenlenmez.\n\n"


def hcl_ad(kimlik: str) -> str:
    """APISIX kimliğini HCL kaynak adına çevirir (tire → alt çizgi; rakamla başlayan öne `_` alır).

    APISIX kimliğinin KENDİSİ değişmez: `id` alanında AYNEN durur — dönüşüm yalnız HCL'in kaynak
    adı dilbilgisi içindir.
    """
    ad = re.sub(r"[^a-z0-9_]", "_", str(kimlik).lower())
    return ad if re.match(r"[a-z_]", ad) else "_" + ad


def _blok(tur: str, kimlik: str) -> str:
    return f'import {{\n  to = {tur}.{hcl_ad(kimlik)}\n  id = "{kimlik}"\n}}\n\n'


def uret(routes: dict) -> str:
    """routes.yaml gövdesinden import bloklarının TAM metnini üretir (grup → tüketici → rota)."""
    out = [BASLIK]
    out += [_blok("apisix_consumer_group", g["id"]) for g in routes.get("tuketici_gruplari", [])]
    out += [_blok("apisix_consumer", c["username"]) for c in routes.get("tuketiciler", [])]
    out += [_blok("apisix_route", r["id"]) for r in routes.get("rotalar", [])]
    return "".join(out)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="routes.yaml → import.tf (TSK-176 T1)")
    p.add_argument("--cikti", help="yazılacak dosya yolu (stdout'a yazılmaz)")
    p.add_argument("--kontrol", action="store_true", help="depodaki import.tf güncel mi (0/1)")
    a = p.parse_args(argv)
    metin = uret(yaml.safe_load(ROUTES.read_text(encoding="utf-8")))
    if a.kontrol:
        guncel = HEDEF.exists() and HEDEF.read_text(encoding="utf-8") == metin
        print("import.tf güncel" if guncel else "import.tf BAYAT — --cikti ile yeniden üret", file=sys.stderr)
        return 0 if guncel else 1
    if not a.cikti:
        p.error("--cikti ya da --kontrol gerekli")
    pathlib.Path(a.cikti).write_text(metin, encoding="utf-8")
    print(f"yazıldı: {a.cikti} ({metin.count('import {')} import bloğu)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

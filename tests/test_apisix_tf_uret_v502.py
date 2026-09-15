"""v502 · routes.yaml → import.tf üretici + altyapi.sh sır sözleşmesi — TSK-176 T1 Task 2.

NUMARA KİMLİKTİR: `v502` planın SABİT atamasıdır; `ls tests | grep -E "v50[0-9]"` bu turda yalnız
`test_soul_denetimi_ilk_satir_v500.py` (+ bu turda doğan v501) verdi — çakışma YOK (2026-09-15).

ÜÇ YÜZEY:
  1. `ops/apisix_tf_uret.py` — `deploy/apisix/routes.yaml` (canlı SSoT) → `altyapi/apisix/import.tf`
     (ÜRETİLMİŞ). Kimlik kümesi BİREBİR: üretici bir kalemi düşürürse test_a/test_b öter.
  2. `altyapi/altyapi.sh` — admin anahtarının SÖZLEŞMESİ: iki kanal (kredi dosyası → .env yedeği),
     yalnız ortam değişkeni, hiçbir çıktıya DEĞER yazılmaz, okunan KANALIN ADI stderr'e.
     `apply` alt komutu YOKTUR (2026-09-15 ruling: yerel state yalnız import/plan).
  3. HCL iskeleti — sağlayıcı/sürüm pinleri ve `backend "local"` yolu (rsync ağacının DIŞINDA).

SIR DEĞERİ YOK: bu dosya hiçbir anahtar deseni taşımaz; beklediği şey DEĞERİN BASILMAMASIDIR
(v476'nın aynı disiplini).

PLANDAN BİLİNÇLİ FARK (tur raporunda da yazılı): plan test_d'de yalnız "apply etiketi YOK" diyordu;
`case` etiketleri kod ile AYNI satırda yazılırsa o iddia BOŞ KÜME üzerinde geçerdi ("çivi yeşili
kanıt değildir" — CLAUDE.md §6). Bu yüzden etiket kümesi TAM olarak ölçülür ve `altyapi.sh`
etiketleri kendi satırlarında taşır: `apply)` eklenirse çivi gerçekten kırılır.
"""
from __future__ import annotations

import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ops import apisix_tf_uret as U  # betikten modül yükle: ham exec_module YASAK (v334)

BEKLENEN_ALT_KOMUTLAR = {"init", "import-uret", "plan", "denetle"}


def _routes():
    return yaml.safe_load((ROOT / "deploy/apisix/routes.yaml").read_text(encoding="utf-8"))


def _alt_komut_etiketleri(metin: str) -> set[str]:
    """`case` gövdesindeki alt komut etiketleri (kendi satırlarında; `*)` `\\w` değildir)."""
    return {e for e in re.findall(r"^\s*(\w[\w-]*)\)\s*$", metin, re.M)}


def test_a_import_bloklari_routes_yaml_kimlikleriyle_birebir():
    hcl = U.uret(_routes())
    r = _routes()
    for rid in [x["id"] for x in r["rotalar"]]:
        assert f"to = apisix_route.{U.hcl_ad(rid)}" in hcl and f'id = "{rid}"' in hcl
    for g in [x["id"] for x in r["tuketici_gruplari"]]:
        assert f"to = apisix_consumer_group.{U.hcl_ad(g)}" in hcl
    for c in [x["username"] for x in r["tuketiciler"]]:
        assert f"to = apisix_consumer.{U.hcl_ad(c)}" in hcl
    assert hcl.count("import {") == len(r["rotalar"]) + len(r["tuketici_gruplari"]) + len(r["tuketiciler"])


def test_b_uretilmis_dosya_guncel():
    """Depodaki import.tf üreticinin çıktısıyla BİREBİR (üretilmiş dosya elle düzenlenmez)."""
    beklenen = U.uret(_routes())
    assert (ROOT / "altyapi/apisix/import.tf").read_text(encoding="utf-8") == beklenen


def test_c_hcl_ad_guvenli():
    assert U.hcl_ad("llm-danisma") == "llm_danisma" and U.hcl_ad("bot_sef") == "bot_sef"
    assert re.fullmatch(r"[a-z_][a-z0-9_]*", U.hcl_ad("metrics-dis"))


def test_d_altyapi_sh_anahtari_basmaz_ve_kanali_bildirir():
    metin = (ROOT / "altyapi/altyapi.sh").read_text(encoding="utf-8")
    assert "set -euo pipefail" in metin
    assert "/etc/meridian/apisix_admin_key" in metin and "APISIX_ADMIN_KEY=" in metin, "iki kanal, apisix_uygula sırası"
    assert "export APISIX_APIKEY" in metin
    assert not re.search(r"echo .*\$\{?APISIX_APIKEY", metin), "anahtar hiçbir echo'ya girmez"
    assert "kanal:" in metin and ">&2" in metin, "okunan kanalın ADI stderr'e"
    etiketler = _alt_komut_etiketleri(metin)
    assert etiketler == BEKLENEN_ALT_KOMUTLAR, "alt komut kümesi TAM (apply YOK — 2026-09-15 ruling)"


def test_e_provider_blogu_anahtarsiz_ve_pinli():
    prov = (ROOT / "altyapi/apisix/provider.tf").read_text(encoding="utf-8")
    assert "api_key" not in prov and "endpoint" not in prov, "değerler ortamdan; HCL'de sır/uç yok"
    ver = (ROOT / "altyapi/apisix/versions.tf").read_text(encoding="utf-8")
    assert 'required_version = "= 1.16.2"' in ver and 'version = "= 1.8.1"' in ver and "rework-space-com/apisix" in ver
    back = (ROOT / "altyapi/apisix/backend.tf").read_text(encoding="utf-8")
    assert 'backend "local"' in back and "/opt/veri/altyapi/apisix/terraform.tfstate" in back

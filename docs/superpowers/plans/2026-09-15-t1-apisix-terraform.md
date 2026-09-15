# TSK-176 T1 — APISIX yapılandırmasının Terraform'a alınması (import-first) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Canlı APISIX kapısının rota/upstream/tüketici/tüketici-grubu yapılandırmasını, A1'de koşan pinli bir Terraform + `rework-space-com/apisix` sağlayıcısıyla **import-first** yönetime almak; `terraform plan -detailed-exitcode` drift denetimi olur; `ops/apisix_uygula.py` bir sürüm geri-alım için kalır.

**Architecture:** `altyapi/apisix/` dizini (HCL: `versions.tf`, `provider.tf`, `import.tf` üretilir, `kaynaklar.tf` `-generate-config-out` ile üretilip elle sadeleştirilir) + `altyapi/altyapi.sh` (A1 sarmalayıcısı: anahtarı KREDİ DOSYASINDAN ortam değişkenine alır, hiçbir çıktıya yazmaz; `init | import-uret | plan | denetle` alt komutları; `apply` ALT KOMUTU YOK — bkz. Global Constraints) + `ops/apisix_tf_uret.py` (routes.yaml → `import.tf`; tek-kaynak köprüsü) + A0 rolüne Terraform kurulumu. State bu fazda A1'de **yerel** ve **yalnız import/plan** içindir.

**Tech Stack:** Terraform 1.16.2 (BUSL 1.1 — lisans beyanı ROADMAP TSK-176 Ref'te), sağlayıcı `rework-space-com/apisix` 1.8.1 (MPL-2.0; APISIX 3.15 ile test edilmiş; kaynaklar: route, upstream, consumer, consumer_group, service, ssl_certificate, global_rule, plugin_config, plugin_metadata, stream_route, secret; `plugins` alanı JSON dizgesi, `jsonencode`), Ansible A0 rolü (`deploy/ansible/roles/meridian_a1`), pytest çivileri.

**Spec:** `docs/TASARIM-ALTYAPI-KOD-2026-09-08.md` (§1.1 state/backend, §1.2 sağlayıcı eşlemesi, §5 T1 satırı, §6 bedel, §8 operatör kararları) + ROADMAP `[TSK-176]` What notu 2026-09-15 15:3xZ (operatör: "uzak hesap olmadan başla" + Rol-1 ruling).

## Global Constraints

- **State backend (Rol-1 ruling 2026-09-15, tasarım §1.1 ile uyumlu):** `backend "local"` YALNIZ import / `-generate-config-out` / `plan` aşamasında; state yolu `/opt/meridian/altyapi/apisix/terraform.tfstate` (rsync ağacının DIŞINDA). **Bu planda `terraform apply` YOKTUR** — ilk `apply` öncesi (B) OCI Object Storage S3-uyumlu arka ucu (T2'de; OCI Customer Secret Key operatörde) ve `terraform init -migrate-state`. `altyapi.sh` `apply` alt komutu taşımaz; Task 3'te plan çıktısı `-detailed-exitcode` 0 (drift yok) hedeflenir, drift varsa hüküm Rol-1'in ve düzeltme `ops/apisix_uygula.py --uygula` ile (mevcut araç, bir sürüm daha yaşar).
- **Sır:** APISIX admin anahtarı yalnız `/etc/meridian/apisix_admin_key` (0400 root; TSK-064 Faz-1C kanalı) ya da yedek `/opt/apisix/.env-apisix` `APISIX_ADMIN_KEY=` satırından, `ops/apisix_uygula.py` ile AYNI sırada okunur; DEĞER hiçbir stdout/stderr/log/argv'ye yazılmaz; okunan KANALIN ADI stderr'e bildirilir (`kanal_bildir` emsali, v476). HCL dosyalarında anahtar YOK (`provider "apisix"` bloğu boş; `APISIX_ENDPOINT`/`APISIX_APIKEY` ortamdan).
- **Sürüm pinleri:** Terraform `= 1.16.2` (apt paketi `terraform=1.16.2-1`), sağlayıcı `= 1.8.1`; `.terraform.lock.hcl` depoya girer (tek kaynak).
- **Tek kaynak:** geçiş süresince `deploy/apisix/routes.yaml` canlı SSoT olarak KALIR; `altyapi/apisix/import.tf` ondan ÜRETİLİR (elle yazılmaz); çivi: import.tf kimlik kümesi == routes.yaml kimlik kümesi (6 rota + 1 grup + 4 tüketici). HCL'in SSoT olması T1 kapanışında ayrı karar (routes.yaml + apisix_uygula emekliliği, bir sürüm sonra).
- **Kapılar (CLAUDE.md):** kod yazan ajan Opus; her görev bağımsız Sonnet incelemesi; `dosya.py:NNN` çapası YOK; `except`/fallback işaretli; yeni test numarası `ls tests | grep vNNN` ile boş doğrulanır (v501'den başla; çakışırsa sonraki); pytest dışı betik koşumu yok; A1'e giden her komut `ssh` sarmalı; canlı koşumlar (Task 3) yalnız Rol-1.
- **Bedel beyanı (tasarım §6):** topluluk sağlayıcısı bakım riski — sürüm pinli, plan çıktısı okunur, `apisix_uygula.py` geri-alım için bir sürüm kalır. Sağlayıcının **satır-içi `upstream` desteği DOĞRULANMADI** (route.md `upstream_id`/`service_id` sunuyor); canlı rotalar satır-içi upstream taşıyor → Task 3 ölçer; desteklenmiyorsa Task 4 kararı (upstream kaynaklarına ayırma) operatörle.

---

### Task 1: A0 rolüne Terraform kurulumu (HashiCorp apt deposu, pinli)

**Files:**
- Modify: `deploy/ansible/roles/meridian_a1/tasks/paketler.yml` (sonuna iki görev)
- Modify: `deploy/ansible/vars/a0_vars.yml` ya da rolün `defaults/main.yml` — hangisi `apt_paketleri`yi tanımlıyorsa (bul: `grep -rn apt_paketleri deploy/ansible`): `terraform_surumu: "1.16.2-1"` değişkeni
- Modify: `deploy/ansible/roles/meridian_a1/tasks/saglik.yml`: `terraform version` sağlık kapısı ("kurulu ≠ çalışır")
- Test: `tests/test_ansible_a0_terraform_v501.py`

**Interfaces:**
- Consumes: A0 rolü mevcut `apt` deseni (`cache_valid_time: 3600`), `saglik.yml` kapı deseni.
- Produces: A1'de `/usr/bin/terraform` 1.16.2; Task 2/3 bunu varsayar.

- [ ] **Step 1: Kırmızı çivi — rol dosyaları Terraform görevini ve pini taşımalı**

```python
"""v501 · A0 rolü Terraform kurulumu — TSK-176 T1 Task 1.
Çiviler dosyayı OKUR (Ansible koşmaz): (a) HashiCorp deposu deb822 ile ve imza anahtarı dosyadan; (b) paket pinli
(`terraform=1.16.2-1`, `state: present`, `allow_downgrade` yok); (c) saglik.yml `terraform version` kapısı taşır;
(d) sürüm TEK yerde (vars) — paketler.yml sabit sürüm dizgesi taşımaz."""
import pathlib, re
import yaml
ROOT = pathlib.Path(__file__).resolve().parents[1]
ROL = ROOT / "deploy/ansible/roles/meridian_a1/tasks"

def _yukle(p):
    return yaml.safe_load(p.read_text(encoding="utf-8"))

def test_a_hashicorp_deposu_deb822_ile_kurulur():
    gorevler = _yukle(ROL / "paketler.yml")
    depo = [g for g in gorevler if "ansible.builtin.deb822_repository" in g]
    assert len(depo) == 1, "HashiCorp deposu tek deb822_repository görevi olmalı"
    d = depo[0]["ansible.builtin.deb822_repository"]
    assert d["uris"] == "https://apt.releases.hashicorp.com" and "arm64" in str(d.get("architectures", ""))
    assert str(d["signed_by"]).startswith("https://apt.releases.hashicorp.com/gpg")

def test_b_terraform_paketi_pinli_ve_surum_tek_yerde():
    metin = (ROL / "paketler.yml").read_text(encoding="utf-8")
    assert "terraform={{ terraform_surumu }}" in metin, "paket adı pinli ve değişkenden"
    assert not re.search(r"terraform=1\.\d+\.\d+", metin), "sabit sürüm dizgesi paketler.yml'de olamaz (tek kaynak)"
    vars_metin = "\n".join(p.read_text(encoding="utf-8") for p in ROOT.glob("deploy/ansible/**/*.yml") if "vars" in p.parts or "defaults" in p.parts)
    assert re.search(r'terraform_surumu:\s*"1\.16\.2-1"', vars_metin)

def test_c_saglik_kapisi_terraform_version():
    metin = (ROL / "saglik.yml").read_text(encoding="utf-8")
    assert "terraform version" in metin and "1.16.2" not in metin, "kapı sürümü değişkenden okur, sabit yazmaz"
```

- [ ] **Step 2: Kırmızıyı gör**

Run: `.venv/bin/python -m pytest tests/test_ansible_a0_terraform_v501.py -p no:cacheprovider`
Expected: 3 FAILED (görevler yok).

- [ ] **Step 3: paketler.yml sonuna iki görev + vars + saglik kapısı**

```yaml
# TSK-176 T1 Task 1 — Terraform (HashiCorp apt deposu, aarch64). Sürüm TEK yerde: `terraform_surumu`.
# BUSL 1.1 lisans beyanı ROADMAP TSK-176 Ref'te; state/backend kararı tasarım §1.1 + 2026-09-15 ruling.
- name: HashiCorp apt deposu (deb822, imza anahtarı URL'den)
  ansible.builtin.deb822_repository:
    name: hashicorp
    types: deb
    uris: https://apt.releases.hashicorp.com
    suites: "{{ ansible_distribution_release }}"
    components: main
    architectures: arm64
    signed_by: https://apt.releases.hashicorp.com/gpg
    state: present

- name: Terraform (pinli; yükseltme apt'ye bırakılmaz — sürüm değişimi bir commit'tir)
  ansible.builtin.apt:
    name: "terraform={{ terraform_surumu }}"
    state: present
    update_cache: true
    cache_valid_time: 3600
```

`vars` dosyasına: `terraform_surumu: "1.16.2-1"`.

`saglik.yml`'e (mevcut kapı deseniyle aynı biçimde):

```yaml
- name: Terraform sürümü ("kurulu != çalışır"; beklenen {{ terraform_surumu }})
  ansible.builtin.command: terraform version -json
  register: tf_surum
  changed_when: false
- name: Terraform sürümü beklenenle eşit mi
  ansible.builtin.assert:
    that: "(tf_surum.stdout | from_json).terraform_version == (terraform_surumu | regex_replace('-\\d+$',''))"
    fail_msg: "terraform sürümü pinden ayrıştı"
```

- [ ] **Step 4: Yeşili gör + syntax-check**

Run: `.venv/bin/python -m pytest tests/test_ansible_a0_terraform_v501.py tests/test_ansible_a0_v451.py -p no:cacheprovider`
Expected: hepsi passed. Ayrıca (Rol-1, yerel): `ansible-playbook --syntax-check -i deploy/ansible/inventory.ini deploy/ansible/site.yml`.

- [ ] **Step 5: Commit (Rol-1 — ajan git koşmaz)**

`git add deploy/ansible/roles/meridian_a1/tasks/paketler.yml deploy/ansible/roles/meridian_a1/tasks/saglik.yml <vars dosyası> tests/test_ansible_a0_terraform_v501.py`

---

### Task 2: `altyapi/apisix/` iskeleti + `altyapi.sh` sarmalayıcı + `ops/apisix_tf_uret.py` (routes.yaml → import.tf)

**Files:**
- Create: `altyapi/apisix/versions.tf`, `altyapi/apisix/provider.tf`, `altyapi/apisix/backend.tf`, `altyapi/apisix/README.md`
- Create: `altyapi/altyapi.sh` (bash; A1'de `sudo` ile koşar)
- Create: `ops/apisix_tf_uret.py`
- Create: `altyapi/apisix/import.tf` (ÜRETİLMİŞ — `ops/apisix_tf_uret.py --cikti altyapi/apisix/import.tf`; elle düzenlenmez)
- Test: `tests/test_apisix_tf_uret_v502.py`
- Modify: `deploy/ansible/vars/dagit_vars.yml` — `altyapi/` rsync kapsamına girer mi? KARAR: girer (A1'de `/opt/meridian/altyapi/` koşum yeri); state dizini `/opt/meridian/altyapi/apisix/terraform.tfstate` ise rsync `--delete` ile SİLİNİR → state yolu **`/opt/veri/altyapi/apisix/terraform.tfstate`** olarak ağaç dışına alınır (Task 2 Step 3'teki `backend.tf`), ve dagit `[1c]`/`[F9]` listelerine dokunulmaz. (`altyapi/` yeni üst dizin: `tests/test_dagit_f9_beyan_v266.py`/`v452` kapsam çivileri koşulur.)

**Interfaces:**
- Consumes: `deploy/apisix/routes.yaml` (`rotalar[].id`, `tuketiciler[].username`, `tuketici_gruplari[].id`); `ops/apisix_uygula.py::ADMIN_ALAN`, `KRED_DOSYASI` (anahtar kanalı sözleşmesi).
- Produces: `altyapi.sh {init|import-uret|plan|denetle}`; `apisix_tf_uret.py --cikti <yol>` (stdout'a yazmaz; `--kontrol` kipi: dosya güncel mi, çıkış 0/1).

- [ ] **Step 1: Kırmızı çiviler**

```python
"""v502 · routes.yaml → import.tf üretici + altyapi.sh sır sözleşmesi — TSK-176 T1 Task 2."""
import pathlib, re, subprocess, sys
import yaml
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ops import apisix_tf_uret as U  # betikten modül yükle: ham exec_module YASAK (v334)

def _routes():
    return yaml.safe_load((ROOT / "deploy/apisix/routes.yaml").read_text(encoding="utf-8"))

def test_a_import_bloklari_routes_yaml_kimlikleriyle_birebir(tmp_path):
    hcl = U.uret(_routes())
    r = _routes()
    for rid in [x["id"] for x in r["rotalar"]]:
        assert f'to = apisix_route.{U.hcl_ad(rid)}' in hcl and f'id = "{rid}"' in hcl
    for g in [x["id"] for x in r["tuketici_gruplari"]]:
        assert f'to = apisix_consumer_group.{U.hcl_ad(g)}' in hcl
    for c in [x["username"] for x in r["tuketiciler"]]:
        assert f'to = apisix_consumer.{U.hcl_ad(c)}' in hcl
    assert hcl.count("import {") == len(r["rotalar"]) + len(r["tuketici_gruplari"]) + len(r["tuketiciler"])

def test_b_uretilmis_dosya_guncel(tmp_path):
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
    assert not re.search(r'echo .*\$\{?APISIX_APIKEY', metin), "anahtar hiçbir echo'ya girmez"
    assert "kanal:" in metin and ">&2" in metin, "okunan kanalın ADI stderr'e"
    assert "apply" not in [s.strip() for s in re.findall(r'^\s*(\w[\w-]*)\)\s*$', metin, re.M)], "apply alt komutu YOK (ruling)"

def test_e_provider_blogu_anahtarsiz_ve_pinli():
    prov = (ROOT / "altyapi/apisix/provider.tf").read_text(encoding="utf-8")
    assert "api_key" not in prov and "endpoint" not in prov, "değerler ortamdan; HCL'de sır/uç yok"
    ver = (ROOT / "altyapi/apisix/versions.tf").read_text(encoding="utf-8")
    assert 'required_version = "= 1.16.2"' in ver and 'version = "= 1.8.1"' in ver and "rework-space-com/apisix" in ver
    back = (ROOT / "altyapi/apisix/backend.tf").read_text(encoding="utf-8")
    assert 'backend "local"' in back and "/opt/veri/altyapi/apisix/terraform.tfstate" in back
```

- [ ] **Step 2: Kırmızıyı gör** — `.venv/bin/python -m pytest tests/test_apisix_tf_uret_v502.py -p no:cacheprovider` → ImportError/FAILED.

- [ ] **Step 3: HCL iskeleti**

`altyapi/apisix/versions.tf`:
```hcl
terraform {
  required_version = "= 1.16.2"
  required_providers {
    apisix = {
      source  = "rework-space-com/apisix"
      version = "= 1.8.1"
    }
  }
}
```
`altyapi/apisix/provider.tf`:
```hcl
# Uç ve anahtar ORTAMDAN (APISIX_ENDPOINT / APISIX_APIKEY) — altyapi.sh doldurur; HCL sır taşımaz.
provider "apisix" {}
```
`altyapi/apisix/backend.tf`:
```hcl
# T1 (2026-09-15 ruling): yerel state YALNIZ import/plan aşaması; apply YOK. T2'de OCI Object Storage
# S3-uyumlu arka ucuna `terraform init -migrate-state`. Yol rsync ağacının DIŞINDA (dagit --delete silmesin).
terraform {
  backend "local" {
    path = "/opt/veri/altyapi/apisix/terraform.tfstate"
  }
}
```

- [ ] **Step 4: `ops/apisix_tf_uret.py`**

```python
#!/usr/bin/env python3
"""ops/apisix_tf_uret.py — deploy/apisix/routes.yaml → altyapi/apisix/import.tf (TSK-176 T1 Task 2).
SÖZLEŞME KOMUT SATIRIDIR:
    python3 ops/apisix_tf_uret.py --cikti altyapi/apisix/import.tf   # üret (stdout'a yazmaz)
    python3 ops/apisix_tf_uret.py --kontrol                            # depodaki dosya güncel mi (0/1)
Tek kaynak: routes.yaml. import.tf ÜRETİLMİŞTİR, elle düzenlenmez (çivi v502 test_b). Kimlik eşlemesi
`hcl_ad` (tire → alt çizgi); APISIX kimliği `id` alanında AYNEN kalır."""
import argparse, pathlib, re, sys
import yaml
ROOT = pathlib.Path(__file__).resolve().parents[1]
ROUTES = ROOT / "deploy/apisix/routes.yaml"
BASLIK = "# ÜRETİLMİŞ — ops/apisix_tf_uret.py; kaynak deploy/apisix/routes.yaml. Elle düzenlenmez.\n\n"

def hcl_ad(kimlik: str) -> str:
    ad = re.sub(r"[^a-z0-9_]", "_", str(kimlik).lower())
    return ad if re.match(r"[a-z_]", ad) else "_" + ad

def _blok(tur: str, kimlik: str) -> str:
    return f'import {{\n  to = {tur}.{hcl_ad(kimlik)}\n  id = "{kimlik}"\n}}\n\n'

def uret(routes: dict) -> str:
    out = [BASLIK]
    out += [_blok("apisix_consumer_group", g["id"]) for g in routes.get("tuketici_gruplari", [])]
    out += [_blok("apisix_consumer", c["username"]) for c in routes.get("tuketiciler", [])]
    out += [_blok("apisix_route", r["id"]) for r in routes.get("rotalar", [])]
    return "".join(out)

def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--cikti"); p.add_argument("--kontrol", action="store_true")
    a = p.parse_args(argv)
    metin = uret(yaml.safe_load(ROUTES.read_text(encoding="utf-8")))
    if a.kontrol:
        hedef = ROOT / "altyapi/apisix/import.tf"
        guncel = hedef.exists() and hedef.read_text(encoding="utf-8") == metin
        print("import.tf güncel" if guncel else "import.tf BAYAT — --cikti ile yeniden üret", file=sys.stderr)
        return 0 if guncel else 1
    if not a.cikti:
        p.error("--cikti ya da --kontrol gerekli")
    pathlib.Path(a.cikti).write_text(metin, encoding="utf-8")
    print(f"yazıldı: {a.cikti} ({metin.count('import {')} import bloğu)", file=sys.stderr)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: `altyapi/altyapi.sh`**

```bash
#!/usr/bin/env bash
# altyapi/altyapi.sh — A1'de Terraform sarmalayıcısı (TSK-176 T1). ROOT ile koşar: sudo ./altyapi/altyapi.sh <komut>
#   init         terraform init (sağlayıcı 1.8.1, kilit dosyası depodan)
#   import-uret  import.tf'yi routes.yaml'dan yeniden üret (ops/apisix_tf_uret.py) + kontrol
#   plan         terraform plan -generate-config-out=uretilen.tf (ilk import) / düz plan
#   denetle      terraform plan -detailed-exitcode (0 drift yok · 2 drift · 1 hata) — apisix_uygula --denetle ikizi
# APPLY ALT KOMUTU YOK (2026-09-15 ruling): yerel state yalnız import/plan; apply T2'de uzak arka uçla.
# SIR: anahtar apisix_uygula.py ile AYNI sırada (kredi dosyası → .env-apisix), yalnız ortam değişkenine; hiçbir çıktıya girmez.
set -euo pipefail
KOK="$(cd "$(dirname "$0")/.." && pwd)"; DIZIN="$KOK/altyapi/apisix"
KRED=/etc/meridian/apisix_admin_key; ENVF=/opt/apisix/.env-apisix
export APISIX_ENDPOINT="${APISIX_ENDPOINT:-http://127.0.0.1:9180}"
if [ -r "$KRED" ]; then
  APISIX_APIKEY="$(tr -d '\n' < "$KRED")"; echo "kanal: kredi dosyası ($KRED)" >&2
elif [ -r "$ENVF" ]; then
  APISIX_APIKEY="$(sed -n 's/^APISIX_ADMIN_KEY=//p' "$ENVF" | head -1 | tr -d '\n')"; echo "kanal: .env-apisix yedeği" >&2
else
  echo "anahtar kanalı yok ($KRED / $ENVF)" >&2; exit 2
fi
[ -n "$APISIX_APIKEY" ] || { echo "anahtar boş (2026-09-07 sınıfı: 1 baytlık satır)" >&2; exit 2; }
export APISIX_APIKEY
cd "$DIZIN"
case "${1:-}" in
  init)        terraform init -input=false ;;
  import-uret) python3 "$KOK/ops/apisix_tf_uret.py" --cikti "$DIZIN/import.tf" && python3 "$KOK/ops/apisix_tf_uret.py" --kontrol ;;
  plan)        if [ ! -f uretilen.tf ]; then terraform plan -input=false -generate-config-out=uretilen.tf; else terraform plan -input=false; fi ;;
  denetle)     terraform plan -input=false -detailed-exitcode ;;
  *)           echo "kullanım: altyapi.sh {init|import-uret|plan|denetle}" >&2; exit 64 ;;
esac
```

- [ ] **Step 6: import.tf üret (ajan: yalnız üretici ile; pytest dışı koşum DEĞİL, saf dosya dönüşümü — `meridian.obs`a ulaşmaz)**

Run: `.venv/bin/python ops/apisix_tf_uret.py --cikti altyapi/apisix/import.tf`
Expected: stderr "yazıldı: … (11 import bloğu)".

- [ ] **Step 7: Yeşili gör + kapsam tarama çivileri**

Run: `.venv/bin/python -m pytest tests/test_apisix_tf_uret_v502.py tests/test_apisix_uygula_tuketici_v364.py tests/test_apisix_admin_credential_v476.py tests/test_bayat_bytecode_v334.py tests/test_dagit_f9_beyan_v266.py tests/test_ansible_dagit_v452.py tests/test_kovab_dilim_v382.py tests/test_tests_ops_satir_capasi_v401.py tests/test_yorum_sembol_capasi_v402.py tests/test_codelaw_v59.py -p no:cacheprovider`
Expected: hepsi passed. Mutasyon: `uret()` içindeki rota döngüsünü kaldır → test_a/test_b kırmızı; `altyapi.sh`'a `echo "$APISIX_APIKEY"` ekle → test_d kırmızı; geri al (yedek kopyadan).

- [ ] **Step 8: Commit (Rol-1)**

`git add altyapi/apisix/versions.tf altyapi/apisix/provider.tf altyapi/apisix/backend.tf altyapi/apisix/import.tf altyapi/apisix/README.md altyapi/altyapi.sh ops/apisix_tf_uret.py tests/test_apisix_tf_uret_v502.py`

---

### Task 3: A1'de ilk import + üretilen HCL'in ölçümü (Rol-1; apply YOK)

**Files:**
- Create (A1 → depo): `altyapi/apisix/uretilen.tf` (`-generate-config-out` çıktısı; Rol-1 inceleyip `kaynaklar.tf` adıyla sadeleştirir), `altyapi/apisix/.terraform.lock.hcl`
- Ölçüm kaydı: ROADMAP TSK-176 What + günlük

**Interfaces:** Task 1 (terraform kurulu) + Task 2 (iskelet) canlıda; A0 rolü koşumu (`ansible-playbook … site.yml`, Rol-1) ve dağıtım (`dagit.sh`) ile A1'e taşınmış.

- [ ] **Step 1:** A0 rolü koşumu: `ansible-playbook -i deploy/ansible/inventory.ini deploy/ansible/site.yml --check --diff` → `failed=0` → `ansible-playbook … site.yml` → A1'de `terraform version` = 1.16.2 (saglik kapısı).
- [ ] **Step 2:** Dağıtım (dagit) ile `altyapi/` A1'e; A1'de `sudo mkdir -p /opt/veri/altyapi/apisix && sudo ./altyapi/altyapi.sh init` (kilit dosyası depodan; `.terraform/` dizini git-ignore'da — `.gitignore`'a `altyapi/apisix/.terraform/` ve `*.tfstate*` satırları Task 2'de eklenir).
- [ ] **Step 3:** `sudo ./altyapi/altyapi.sh import-uret && sudo ./altyapi/altyapi.sh plan` → `uretilen.tf` doğar. ÖLÇÜM (Global Constraints bedel beyanı): üretilen `apisix_route` blokları canlı satır-içi `upstream`ı taşıyor mu? (a) taşıyorsa → `kaynaklar.tf` olarak sadeleştir (jsonencode plugins), ikinci `plan -detailed-exitcode` → **0** hedef; (b) taşımıyorsa (yalnız `upstream_id`) → planın Task 4 kararı: rotaları `apisix_upstream` kaynaklarına ayırmak canlı DEĞİŞİKLİK gerektirir (apply) → T2 arka ucu ve operatör onayı (K4) öncesi YAPILMAZ; kayıt ROADMAP'e, T1 "kısmi: import+drift denetimi rota/tüketici/grup için".
- [ ] **Step 4:** Kanıt: `altyapi.sh denetle` çıkış kodu + `ops/apisix_uygula.py --denetle` aynı gece aynı hüküm (iki denetçi uyuşuyor mu — tek-kaynak köprüsü). Sonuç günlük + ROADMAP.
- [ ] **Step 5:** Commit (Rol-1): `git add altyapi/apisix/kaynaklar.tf altyapi/apisix/.terraform.lock.hcl` (+ docs).

---

### Task 4: Belgeler ve kapılar (Rol-1)

- [ ] ROADMAP TSK-176: T1 durumu (import edilen kaynak sayısı, drift hükmü, satır-içi upstream ölçümü, T2 ön-koşulu: OCI Customer Secret Key operatörde).
- [ ] CLAUDE.md §2 satırı: "`altyapi.sh` / `terraform apply`" → "Rol-1 miyim? Arka uç uzak mı (T2)? Yerel state ile apply YOK (ruling 2026-09-15)".
- [ ] `docs/TASARIM-ALTYAPI-KOD-2026-09-08.md` §8'e revizyon notu: karar 3 (HCP) 2026-09-15'te operatörce geri alındı → (B) OCI S3-uyumlu; §1.1 "local kesinlikle değil" ÜRETİM için geçerli, bootstrap istisnası bu planla.
- [ ] RUNBOOK yeniden üretimi (`ops/runbook_uret.py --cikti docs/RUNBOOK.md`) + belge çivileri; tek commit.

## Self-review (yazar, 2026-09-15)

- Spec kapsamı: §5 T1 satırının dört öğesi (HCL, pinli sağlayıcı, drift denetimi, apisix_uygula geri-alım) → Task 2/3; "apisix_uygula emekli" T1 kapanışına ERTELENDİ (tek-kaynak geçişi bir sürüm sonra) — bilinçli fark, Global Constraints'te.
- Yer tutucu taraması: yok; v501/v502 numaraları çakışma kontrolüyle.
- Tür tutarlılığı: `hcl_ad`, `uret`, `--cikti/--kontrol` Task 2 test ↔ kod aynı adlarla.
- Açık risk: satır-içi upstream desteği (Task 3 ölçer, Task 4 kararı); `deb822_repository` modülü `ansible.builtin` 2.15+ (A0 koleksiyon sürümü `requirements.yml`de doğrulanır — Task 1 Step 4 syntax-check yakalar).

"""v501 · A0 rolü Terraform kurulumu — TSK-176 T1 Task 1.

NUMARA KİMLİKTİR: `v501` planın (`docs/superpowers/plans/2026-09-15-t1-apisix-terraform.md`
Global Constraints) SABİT atamasıdır; bu turda `ls tests | grep -E "v50[0-9]"` yalnız
`test_soul_denetimi_ilk_satir_v500.py`yi verdi — çakışma YOK (ölçüldü 2026-09-15).

ÇİVİLER DOSYAYI OKUR, ANSIBLE KOŞMAZ (v451'in yöntemiyle aynı sınıf): A1'e hiçbir bağlantı yok,
ölçülen katman SÖZLEŞMEDİR —
  (a) HashiCorp deposu `deb822_repository` ile ve imza anahtarı URL'den (elle `apt-key` yok);
  (b) paket PİNLİ (`terraform={{ terraform_surumu }}`) ve sürüm dizgesi paketler.yml'de YOK;
  (c) `saglik.yml` `terraform version` kapısı taşır ve sürümü SABİT yazmaz ("kurulu != çalışır");
  (d) sürüm TEK yerde (rolün `defaults/main.yml`i — `apt_paketleri` orada tanımlı).

BİLİNEN SINIR, dürüst beyan: bu dosya kurulumun A1'de GERÇEKTEN olduğunu ölçmez (o soru
`saglik.yml` kapısının kendisidir ve yalnız playbook koşumunda cevaplanır); burada ölçülen,
kapının VAR olduğu ve sürümü değişkenden okuduğudur.
"""
from __future__ import annotations

import pathlib
import re

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROL = ROOT / "deploy/ansible/roles/meridian_a1/tasks"


def _yukle(p: pathlib.Path):
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
    vars_metin = "\n".join(
        p.read_text(encoding="utf-8")
        for p in ROOT.glob("deploy/ansible/**/*.yml")
        if "vars" in p.parts or "defaults" in p.parts
    )
    assert re.search(r'terraform_surumu:\s*"1\.16\.2-1"', vars_metin)


def test_c_saglik_kapisi_terraform_version():
    metin = (ROL / "saglik.yml").read_text(encoding="utf-8")
    assert "terraform version" in metin and "1.16.2" not in metin, "kapı sürümü değişkenden okur, sabit yazmaz"

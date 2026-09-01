"""tests/test_ajan_git_shim_v360.py — TSK-050 git-shim çivileri (B-AJAN-GIT v1).

Shim'in sözleşmesi ops/ajan_git_shim.sh başlığında: yalnız İKİ evrensel-yasak sınıf kapanır
(stash · add -A/--all/.), geri kalan her şey gerçek git'e SAYDAM devredilir; CLAUDECODE!=1
ortamı hiç etkilenmez. Testler shim'i gerçek kabukta koşturur (sözleşme KOMUT SATIRIdır),
gerçek git yerine MERIDIAN_GERCEK_GIT kancasıyla sahte git enjekte edilir — çivi shim'in
NEYİ engelleyip NEYİ devrettiğini ölçer, git'in kendisini değil.
"""
from __future__ import annotations

import os
import pathlib
import stat
import subprocess

KOK = pathlib.Path(__file__).resolve().parents[1]
SHIM = KOK / "ops" / "ajan_git_shim.sh"

SAHTE_GIT = """#!/bin/sh
echo "SAHTE_GIT_KOSTU $@"
exit 0
"""


def _kos(tmp_path, argv, env_ek=None):
    sahte = tmp_path / "sahte_git"
    if not sahte.exists():
        sahte.write_text(SAHTE_GIT)
        sahte.chmod(sahte.stat().st_mode | stat.S_IXUSR)
    env = dict(os.environ)
    env.pop("MERIDIAN_GIT_BYPASS", None)
    env["CLAUDECODE"] = "1"
    env["MERIDIAN_GERCEK_GIT"] = str(sahte)
    if env_ek:
        env.update(env_ek)
    return subprocess.run(["sh", str(SHIM), *argv],
                          capture_output=True, text=True, env=env, timeout=10)


# --- RED sınıfı ---------------------------------------------------------------------------

def test_A1_stash_reddedilir(tmp_path):
    r = _kos(tmp_path, ["stash"])
    assert r.returncode == 86
    assert "stash" in r.stderr and "SAHTE_GIT_KOSTU" not in r.stdout


def test_A2_stash_alt_bicimleri_de_reddedilir(tmp_path):
    for alt in (["stash", "list"], ["stash", "pop"], ["stash", "push", "-m", "x"]):
        r = _kos(tmp_path, alt)
        assert r.returncode == 86, alt


def test_A3_global_bayrakli_stash_kacamaz(tmp_path):
    # -C <dizin> değer taşır; alt-komut yine stash'tir — bayrak ayrıştırıcı atlamalı.
    r = _kos(tmp_path, ["-C", "/tmp", "stash"])
    assert r.returncode == 86
    # -c ad=deger biçimi de değer taşır.
    r2 = _kos(tmp_path, ["-c", "user.name=x", "stash"])
    assert r2.returncode == 86


def test_A4_add_buyuk_A_reddedilir(tmp_path):
    r = _kos(tmp_path, ["add", "-A"])
    assert r.returncode == 86 and "a94d425" in r.stderr


def test_A5_add_all_ve_nokta_reddedilir(tmp_path):
    assert _kos(tmp_path, ["add", "--all"]).returncode == 86
    assert _kos(tmp_path, ["add", "."]).returncode == 86
    assert _kos(tmp_path, ["add", "dosya.py", "."]).returncode == 86


# --- SAYDAM sınıfı ------------------------------------------------------------------------

def test_B1_acik_yollu_add_gecer(tmp_path):
    r = _kos(tmp_path, ["add", "ROADMAP.md", "ops/x.py"])
    assert r.returncode == 0 and "SAHTE_GIT_KOSTU add ROADMAP.md ops/x.py" in r.stdout


def test_B2_nokta_onekli_yol_gecer(tmp_path):
    # `git add ./dosya` meşru — "." yalnız TAM jeton olarak yasak.
    r = _kos(tmp_path, ["add", "./dosya.py"])
    assert r.returncode == 0 and "SAHTE_GIT_KOSTU" in r.stdout


def test_B3_gunluk_komutlar_gecer(tmp_path):
    for argv in (["log", "-1"], ["status", "--porcelain"], ["commit", "-m", "x"],
                 ["push", "origin", "main"], ["diff"], ["rev-parse", "HEAD"]):
        r = _kos(tmp_path, argv)
        assert r.returncode == 0 and "SAHTE_GIT_KOSTU" in r.stdout, argv


def test_B4_stash_kelimesi_arguman_olarak_gecer(tmp_path):
    # Alt-komut "log" — "stash" yalnız bir ref argümanı; engellenmemeli.
    r = _kos(tmp_path, ["log", "stash"])
    assert r.returncode == 0 and "SAHTE_GIT_KOSTU log stash" in r.stdout


# --- ORTAM sınıfı -------------------------------------------------------------------------

def test_C1_claude_disi_ortam_hic_etkilenmez(tmp_path):
    r = _kos(tmp_path, ["stash"], env_ek={"CLAUDECODE": "0"})
    assert r.returncode == 0 and "SAHTE_GIT_KOSTU stash" in r.stdout


def test_C2_bilincli_kacis_gecer(tmp_path):
    r = _kos(tmp_path, ["stash"], env_ek={"MERIDIAN_GIT_BYPASS": "1"})
    assert r.returncode == 0 and "SAHTE_GIT_KOSTU stash" in r.stdout


def test_C3_shim_calistirilabilir_ve_sh_uyumlu():
    # Kurulum sözleşmesi başlıkta; dosya sh -n ile sözdizim-temiz olmalı.
    r = subprocess.run(["sh", "-n", str(SHIM)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_C4_kurulu_kopya_repo_ile_ayrismamis():
    """Tek-kaynak yasası: ~/.local/bin/git KURULUYSA repo dosyasının bayt-aynı kopyası olmalı.

    Kurulu değilse test atlanır (kurulum operatör makinesine özgü); ayrışma bulunursa hüküm
    "kurulumu tazele" (cp ops/ajan_git_shim.sh ~/.local/bin/git)."""
    import hashlib

    import pytest
    kurulu = pathlib.Path.home() / ".local" / "bin" / "git"
    if not kurulu.exists():
        pytest.skip("shim kurulu değil — kurulum operatör makinesine özgü")
    assert hashlib.sha256(kurulu.read_bytes()).hexdigest() == \
        hashlib.sha256(SHIM.read_bytes()).hexdigest(), \
        "kurulu shim repo'dan ayrışmış — tazele: cp ops/ajan_git_shim.sh ~/.local/bin/git"

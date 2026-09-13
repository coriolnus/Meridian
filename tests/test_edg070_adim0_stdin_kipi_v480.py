"""v480 — EDG-2026-070 ADIM-0 betiği (`research/olcumler/edg070_pit_midcap/adim0_kapsama.py`) STDIN KİPİ çivileri.

NEDEN VAR. Betik A1'e deploy edilmeden `ssh a1 '.venv/bin/python - --repo /opt/meridian --cikti …' < adim0_kapsama.py`
ile koşsun diye yazıldı; ilk gerçek A1 koşumu (2026-09-13 19:1xZ) argparse KURULURKEN düştü:
`--repo` varsayılanı `SANDBOX.parents[2]` idi, stdin kipinde SANDBOX=cwd=/opt/meridian'ın yalnız iki üstü var
→ IndexError, `--repo` açık verilmiş olsa bile (varsayılan add_argument anında hesaplanır); ikinci kusur: `python -`
`__file__`ı "<stdin>" olarak TANIMLAR, `"__file__" in globals()` sınaması stdin'i dosya sanıyordu. Yerel dosya-kipi
koşumu bunu göremezdi. Çiviler betiği GERÇEKTEN stdin'den, kök dizinden (cwd="/", sıfır üst) koşturur —
`--help` argparse kurulumunu ağa/veriye dokunmadan sınar. Mutasyon kanıtı: HEAD'deki eski satırla
`git show HEAD:… | (cd / && python - --help)` rc 1 (IndexError), düzeltmeyle rc 0 (Rol-1, 2026-09-13).
NUMARA: v478 olarak doğdu, aynı saatte TSK-185'in `test_pano_artefakt_temizlik_v478.py` (19 çivi) ile çakıştı —
az-çapalı taraf (bu dosya, 0 dış çapa) v480'e taşındı (vNNN kimlik kuralı, CLAUDE.md §2).
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
BETIK = REPO / "research" / "olcumler" / "edg070_pit_midcap" / "adim0_kapsama.py"


def _stdin_kos(*args: str, cwd: str = "/") -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-", *args], input=BETIK.read_bytes(), cwd=cwd,
                          capture_output=True, timeout=60)


def test_stdin_kipi_kok_dizinden_help_KURULUR():
    r = _stdin_kos("--help")
    assert r.returncode == 0, r.stderr.decode()[-400:]
    assert b"--alpaca-sonda" in r.stdout and b"IndexError" not in r.stderr


def test_stdin_kipi_repo_verilmezse_KULLANIM_HATASI_cikis_2():
    r = _stdin_kos()
    assert r.returncode == 2 and b"--repo zorunlu" in r.stderr, (r.returncode, r.stderr.decode()[-300:])


def test_stdin_kipi_cikti_verilmezse_KULLANIM_HATASI_cikis_2(tmp_path):
    r = _stdin_kos("--repo", str(REPO))
    assert r.returncode == 2 and b"--cikti zorunlu" in r.stderr, (r.returncode, r.stderr.decode()[-300:])


def test_dosya_kipi_varsayilan_repo_UC_UST_help():
    r = subprocess.run([sys.executable, str(BETIK), "--help"], capture_output=True, timeout=60, cwd="/")
    assert r.returncode == 0 and b"--repo" in r.stdout, r.stderr.decode()[-300:]

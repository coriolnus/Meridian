"""test_mimari_sozlesme_v549.py — import-linter mimari sözleşmelerinin TAMAMI suite içinde koşar.

VAKA (Rol-1 ölçümü, 2026-09-25, TSK-223 tur 1 birleşmesi ba8a6124): tam suite YEŞİLDİ (14.167/0), ama
dağıtım kapısı `[0c] lint-imports` (`deploy/ansible/dagit.yml`) ve CI duman (`ops/ci_duman.sh` [2/4])
KIRMIZIYDI:

    saf yapraklar (indicators/barclock/codelaw/provenance/macro) birbirinden bağımsız BROKEN
    meridian.barclock -> meridian.obs -> meridian.store -> meridian.provenance

`barclock`taki tembel `from . import obs` import-linter'ın grafiğine girer (statik analiz fonksiyon-içi
import'u da kenar sayar). Sözleşmeler (`pyproject.toml [tool.importlinter]`) yalnız CI duman ve dağıtım
kapısında koşuyordu — suite bu sınıfı HİÇ görmüyordu, kırık ilk kez dağıtım anında ortaya çıktı. Bu çivi
aynı ölçümü suite'e taşır: kırık, birleşmeden ÖNCE Rol-1'in suite'inde görünür.

NASIL: `lint-imports` alt süreçle, `cwd` = deponun kökü (config `pyproject.toml`dan okunur) ve
`PYTHONPATH` = deponun kökü. İKİNCİSİ ŞART: worktree'de venv ana checkout'a kuruludur; PYTHONPATH
verilmezse ANA checkout'un `meridian`ı analiz edilir ve çivi yanlış ağacı ölçer (bellek:
worktree-pythonpath-tuzagi) — bu yüzden çözülen paket yolu ayrıca çivilenir. `--no-cache`: grimp
önbelleği dosya damgasıyla anahtarlanır; aynı saniyede yapılan bir değişiklik (mutasyon/geri alma) bayat
grafikle ölçülebilirdi (aynı-saniye .pyc tuzağının ikizi). Statik analizdir — modülleri İÇE AKTARMAZ,
`obs`'a ulaşmaz, canlı deftere yazamaz.

POZİTİF KONTROL: "Contracts: N kept, 0 broken" satırında N, pyproject'teki sözleşme SAYISINA eşit
olmalı — sıfır sözleşme koşan ("boş ölçüm") ya da bir sözleşmeyi atlayan koşum yeşil sayılmaz.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _lint_imports_yolu() -> str:
    """Çivi koşan yorumlayıcının venv'indeki `lint-imports`; yoksa PATH. Bulunamazsa ÖLÇÜLEMEZ —
    sessiz atlama değil kırmızı (kapı yeşil sayılırsa sözleşme yine yalnız dağıtımda görünürdü)."""
    aday = Path(sys.executable).parent / "lint-imports"
    if aday.exists():
        return str(aday)
    yol = shutil.which("lint-imports")
    if yol:
        return yol
    pytest.fail("lint-imports bulunamadı (import-linter dev bağımlılığı kurulu değil) — mimari "
                "sözleşmeler bu koşumda ÖLÇÜLEMEDİ; yeşil sayılamaz")


def _ortam() -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO)
    return env


def _pyproject_sozlesme_sayisi() -> int:
    with open(REPO / "pyproject.toml", "rb") as fh:
        return len(tomllib.load(fh)["tool"]["importlinter"]["contracts"])


def test_cozulen_meridian_paketi_BU_agactadir():
    """Worktree tuzağı: lint-imports'un gördüğü `meridian` bu çivinin ağacındaki paket olmalı. Paket
    `find_spec` ile ÇÖZÜLÜR, içe AKTARILMAZ (üst düzey paket için find_spec `__init__`i koşmaz)."""
    r = subprocess.run(
        [sys.executable, "-c",
         "import importlib.util; s = importlib.util.find_spec('meridian'); "
         "print(list(s.submodule_search_locations)[0])"],
        cwd=REPO, env=_ortam(), capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr[-2000:]
    assert Path(r.stdout.strip()).resolve() == (REPO / "meridian").resolve(), \
        f"lint-imports başka bir ağacın meridian'ını analiz ederdi: {r.stdout.strip()}"


def test_import_linter_sozlesmelerinin_TAMAMI_korunuyor():
    """Dağıtım kapısı [0c] ve CI duman [2/4] ile AYNI ölçüm. KIRMIZI-ÖNCE: TSK-223 tur 1'in
    `barclock -> obs` kenarı "saf yapraklar birbirinden bağımsız" sözleşmesini kırıyordu."""
    beklenen = _pyproject_sozlesme_sayisi()
    assert beklenen > 0, "pyproject'te sözleşme yok — ölçülecek bir şey yok"
    r = subprocess.run([_lint_imports_yolu(), "--no-cache"], cwd=REPO, env=_ortam(),
                       capture_output=True, text=True, timeout=300)
    cikti = r.stdout + r.stderr
    m = re.search(r"Contracts:\s*(\d+)\s+kept,\s*(\d+)\s+broken", cikti)
    assert m, f"lint-imports özet satırı yok — ölçüm okunamadı:\n{cikti[-3000:]}"
    tutulan, kirik = int(m.group(1)), int(m.group(2))
    assert kirik == 0 and r.returncode == 0, f"mimari sözleşme KIRIK:\n{cikti[-4000:]}"
    assert tutulan == beklenen, (f"{beklenen} sözleşmeden yalnız {tutulan} tanesi ölçüldü — "
                                 f"boş/kısmi ölçüm yeşil sayılmaz:\n{cikti[-2000:]}")

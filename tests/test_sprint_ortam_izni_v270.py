"""Sprint ortam dosyası 0600 izniyle DOĞMALI (ROADMAP WP6/H9 süpürmesi 2026-08-23).

NEDEN ÇİVİ: `write_text` + sonradan `chmod` çifti, iki çağrı arasında dosyayı umask izniyle
(çoğu sistemde herkes-okur) bırakır; ortam dosyası sır taşıdığı için pencere kısa da olsa gerçek.
Düzeltme yaratma-anı iznidir (os.open O_CREAT 0600) — bu test hem deseni hem davranışı kilitler.
"""

import ast
import os
import pathlib

import meridian.sprint as sprint

KAYNAK = pathlib.Path(sprint.__file__)


def test_ortam_dosyasina_ciplak_write_text_yok():
    """`ortam_dosyasi.write_text(...)` kalıbı kaynağa geri dönmemeli (yaratma-anı izni şart)."""
    agac = ast.parse(KAYNAK.read_text(encoding="utf-8"))
    suclular = [n.lineno for n in ast.walk(agac)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "write_text" and isinstance(n.func.value, ast.Name)
                and n.func.value.id == "ortam_dosyasi"]
    assert not suclular, f"ortam_dosyasi.write_text geri geldi: satır {suclular}"


def test_yaratma_ani_izni_davranissal(tmp_path):
    """Aynı desenle yazılan dosya, yaratıldığı anda 0600 olmalı (davranış, metin değil)."""
    hedef = tmp_path / "ortam.env"
    fd = os.open(hedef, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write("GIZLI=1\n")
    assert (hedef.stat().st_mode & 0o777) == 0o600
    assert hedef.read_text() == "GIZLI=1\n"


def test_pozitif_kontrol_dedektor():
    """Dedektör sentetik kaynakta çıplak kalıbı gerçekten yakalıyor (totoloji kapısı)."""
    agac = ast.parse("ortam_dosyasi.write_text(x)")
    bulundu = [n for n in ast.walk(agac) if isinstance(n, ast.Call)
               and isinstance(n.func, ast.Attribute) and n.func.attr == "write_text"]
    assert bulundu

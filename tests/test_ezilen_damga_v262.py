"""v262 — EZİLEN-BİLEŞEN DAMGALARI (WP6/25b, DENETIM-OLU-BILESEN-ENVANTERI-2026-08-13 §D-2).

NE KORUR: Envanterin "DAMGALA" hükmü verdiği ezilen bileşenlerin KALICI BEYAN damgaları
(neden atıl · hangi katman eziyor · hangi koşulda canlanır) kaynak dosyalarında durur ve
her damga, beyan ettiği MEKANİZMANIN hemen yanında oturur. Damga bir yorum bloğudur;
davranış değişikliği SIFIRDIR — bu dosya yalnız beyanın varlığını ve yerini çiviler.

NEDEN METİN ÇİVİSİ (AST değil): korunan artefaktın kendisi bir YORUM bloğu — AST yorum
görmez. Totoloji riski üç kilitle kapatılır: (1) damga imi dosya başına TAM BİR kez,
(2) mekanizma satırı (gerçek kod) hâlâ dosyada, (3) damga imi mekanizma satırının en çok
YAKINLIK_SATIRI satır ÜSTÜNDE — damga konusundan koparılamaz, konu damgasız taşınamaz.

25b-6 (skill registry 93 bayrak) BURADA DAMGALANMADI: envanterin damga hedefi pano rozeti
(meridian/web/app.js) ve o dosya bu turda başka ajanın; kod-tarafı beyan zaten
meridian/skills.py'de yazılı — son test o beyanı çiviler (pano kalemi WP7/24h'de yürür).
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

#: Damga imi mekanizma satırından en çok bu kadar satır uzakta (üstünde) olabilir.
YAKINLIK_SATIRI = 40

# im → (dosya, mekanizma satırının birebir kod parçası)
DAMGALAR: dict[str, tuple[str, str]] = {
    "EZILEN-DAMGA[25b-1]": ("meridian/guard.py", 'len(proposal["changes"]) != 1'),
    "EZILEN-DAMGA[25b-2]": ("meridian/guard.py", '_chk("daily_loss_breaker"'),
    "EZILEN-DAMGA[25b-3]": ("meridian/loop.py", 'slots = limits["max_open_positions"]'),
    "EZILEN-DAMGA[25b-4]": ("meridian/broker.py", 'off = min(float(cfg["limit_atr_mult"]) * a, pct_off)'),
    "EZILEN-DAMGA[25b-5]": ("meridian/broker.py", 'gap = (rp is None) or (t > 0 and rp >= t)'),
}

# Her damga bloğunun taşımak ZORUNDA olduğu üç bacak (brief'in damga tanımı) + kalem-özgü çekirdek.
ORTAK_BACAKLAR = ("ATIL", "EZEN KATMAN", "CANLANMA")
OZGU_IDDIA: dict[str, tuple[str, ...]] = {
    "EZILEN-DAMGA[25b-1]": ("one_variable_only", "HİÇBİR KOD OKUMAZ", "KOŞULSUZ"),
    "EZILEN-DAMGA[25b-2]": ("max_position_r", "max_daily_loss_pct", "0/409", "fail-safe"),
    "EZILEN-DAMGA[25b-3]": ("max_open_positions", "heat_hard_r", "EDG-2026-035", "sektör"),
    "EZILEN-DAMGA[25b-4]": ("limit_atr_mult", "limit_pct_cap", "100", "2026-08-03"),
    "EZILEN-DAMGA[25b-5]": ("gap_behavior", "TOTOLOJİ", "gap_at_submit", "sinyal barı"),
}


def _oku(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


@pytest.mark.parametrize("im", sorted(DAMGALAR))
def test_damga_var_tekil_ve_mekanizmaya_bitisik(im: str) -> None:
    rel, mekanizma = DAMGALAR[im]
    kaynak = _oku(rel)
    assert kaynak.count(im) == 1, f"{rel}: '{im}' TAM BİR kez olmalı (bulunan: {kaynak.count(im)})"
    satirlar = kaynak.splitlines()
    im_no = next(i for i, s in enumerate(satirlar) if im in s)
    mek_nolar = [i for i, s in enumerate(satirlar) if mekanizma in s]
    assert mek_nolar, f"{rel}: damgalanan mekanizma satırı kayıp: {mekanizma!r}"
    mek_no = mek_nolar[0]
    assert im_no < mek_no, f"{rel}: damga ({im_no + 1}) mekanizmanın ({mek_no + 1}) ÜSTÜNDE olmalı"
    assert mek_no - im_no <= YAKINLIK_SATIRI, (
        f"{rel}: damga ile mekanizma arası {mek_no - im_no} satır > {YAKINLIK_SATIRI} — "
        f"damga konusundan kopmuş")


@pytest.mark.parametrize("im", sorted(DAMGALAR))
def test_damga_uc_bacagi_ve_cekirdek_iddiayi_tasiyor(im: str) -> None:
    rel, _ = DAMGALAR[im]
    satirlar = _oku(rel).splitlines()
    im_no = next((i for i, s in enumerate(satirlar) if im in s), None)
    assert im_no is not None, f"{rel}: '{im}' yok"
    blok = "\n".join(satirlar[im_no:im_no + 14])  # damga bloğu: im satırı + altındaki yorumlar
    for bacak in ORTAK_BACAKLAR:
        assert bacak in blok, f"{im}: damga bloğunda '{bacak}' bacağı eksik"
    for iddia in OZGU_IDDIA[im]:
        assert iddia in blok, f"{im}: damga bloğunda çekirdek iddia eksik: {iddia!r}"


def test_25b6_kod_tarafi_beyani_skills_py_de_durur() -> None:
    """25b-6 (registry enabled/mode/shadow) damgası pano rozetine ait (başka ajanın dosyası);
    kod tarafındaki mevcut beyan — "registry'ye bayrak yazmak davranışı DEĞİŞTİRMEZ" —
    skills.py'de yazılıdır ve bu çivi onu sürüklenmeye karşı tutar."""
    kaynak = _oku("meridian/skills.py")
    assert "registry'ye bayrak yazmak davranışı" in kaynak
    assert "motor_ici_esik_asan" in kaynak

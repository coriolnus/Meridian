"""v406 — TSK-132 D4: YÖN UTILITY KÖPRÜSÜ ÇİVİSİ (2026-09-04).

TETİK: brief D1–D7 (`.superpowers/sdd/2026-09-04-tsk132/brief.md`) D4 — `ui/src` genelinde
9 dosyada 26 `[var(--yon-arti)]`/`[var(--yon-eksi)]` bracket kullanımı ölçüldü (Tailwind
arbitrary-value söz dizimi CSS değişkenini DOĞRUDAN okuyordu, utility katmanı hiç YOKTU).
`ui/src/tema.css` `@theme inline`e sekiz eşleme eklendi (`--color-yon-arti[-h/-t/-zemin]`,
`--color-yon-eksi[-h/-t/-zemin]`, `--basari` ailesinin emsaliyle AYNI desen) ve 26 kullanımın
TAMAMI `text-yon-arti`, `fill-yon-arti/85`, `stroke-yon-eksi`, `bg-yon-arti/85`, `ring-yon-eksi`
gibi DÜZ Tailwind utility'lerine taşındı.

NUMARA ÇAKIŞMASI TARANDI (2026-09-04): `ls tests | grep v406` BOŞ döndü (v405 EDG-071'indir).

ÇİVİNİN SINIFI VE ZAYIFLIĞI (v388 ailesinin deseni): TSX/TS'i METİN olarak okur, davranışı
DEĞİL davranışı üreten satırın YOKLUĞUNU/VARLIĞINI ölçer. Zayıflık MUTASYONLA telafi edilir
(rapor: bir bracket kullanımı geri getirmek bu çiviyi öttürdü, geri alındı).

GÖRÜNÜM: bracket zaten `var(--yon-arti)`nin ta kendisini çözüyordu; utility karşılığı
`--color-yon-arti: var(--yon-arti)` üzerinden AYNI değişkene gider — DEĞER değişmedi, yalnız
Tailwind'in class üretim yolu değişti.
"""
from __future__ import annotations

import pathlib
import re

from meridian import config

ROOT = pathlib.Path(config.ROOT)
UI_SRC = ROOT / "ui" / "src"
TEMA = UI_SRC / "tema.css"

BRACKET = re.compile(r"\[var\(--yon-(arti|eksi)")


def test_olculen_dosyalar_YERINDE():
    """KÖRLÜK ALARMI: yol bayatlarsa aşağıdaki tarama sessizce boş dizin okur ve
    'sıfır ihlal' bir okuma yokluğu olur, gerçek bir ölçüm değil."""
    assert UI_SRC.is_dir(), f"ölçülecek dizin yok: {UI_SRC}"
    assert TEMA.is_file(), f"ölçülecek dosya yok: {TEMA}"


def test_BRACKET_DEDEKTORU_kendisi_olculuyor():
    """POZİTİF KONTROL (v378 K6 / v388 emsali): dedektör bozuksa aşağıdaki SIFIR iddiası bir
    okuma yokluğunu 'temiz' diye okur. Bilinen ihlal örnekleri (arti VE eksi, tek ve çift
    bracket) ve bilinen TEMİZ (utility) biçim ayrı ayrı sınanır."""
    tek = 'className="text-[var(--yon-arti)]"'
    cift = 'className="fill-[var(--yon-eksi)]/85 stroke-[var(--yon-eksi)]"'
    temiz = 'className="text-yon-arti fill-yon-eksi/85"'
    assert BRACKET.search(tek), "dedektör bilinen tekli arti ihlalini yakalamıyor"
    assert len(BRACKET.findall(cift)) == 2, "dedektör bilinen çiftli eksi ihlalini yakalamıyor"
    assert not BRACKET.search(temiz), "dedektör utility biçimini de İHLAL sanıyor (yanlış pozitif)"


def test_YON_BRACKET_KULLANIMI_SIFIR():
    """(D4) ui/src genelinde `[var(--yon-arti|eksi...)]` KULLANIMI SIFIR — 26 kullanım (9 dosya,
    ölçüldü 2026-09-04: ogrenme/ortak · portfoy/olcum · ajan/HipotezDefteri ·
    analiz/TopviewsTablosu · bugun/ortak · analiz/ortak · kanban/PlanKarti · kimlik/Broker ·
    meridian/OlcumHucresi) utility'ye taşındı. MUTASYONLA sınandı: bir bracket kullanımını geri
    getirmek bu çiviyi öttürdü, geri alındı."""
    ihlaller: list[str] = []
    for p in sorted(set(UI_SRC.rglob("*.ts")) | set(UI_SRC.rglob("*.tsx"))):
        metin = p.read_text(encoding="utf-8")
        for m in BRACKET.finditer(metin):
            satir = metin.count("\n", 0, m.start()) + 1
            ihlaller.append(f"{p.relative_to(ROOT)} (satır {satir})")
    assert not ihlaller, f"hâlâ bracket kullanımı var, utility'ye taşınmadı: {ihlaller}"


def test_TEMA_CSS_YON_UTILITY_ESLEMELERI_VAR():
    """Köprünün karşı ucu: `@theme inline` sekiz `--color-yon-*` eşlemesi taşımalı — yoksa
    yukarıdaki 'sıfır bracket' iddiası bir KÖPRÜ değil bir KAYIP anlamına gelirdi (bracket
    kalkar ama utility hiçbir CSS değişkenine bağlı değil, sessizce varsayılan/renksiz render
    alır — `text-yon-arti` tanımsız bir jenerik renge düşer, hata vermez)."""
    css = TEMA.read_text(encoding="utf-8")
    for yon in ("arti", "eksi"):
        for ek in ("", "-h", "-t", "-zemin"):
            beklenen = f"--color-yon-{yon}{ek}: var(--yon-{yon}{ek});"
            assert beklenen in css, f"tema.css'te eşleme yok: {beklenen}"


def test_ESLEME_KUNYELI():
    """Yeni bir CSS bloğu TSK künyesiz eklenirse kaynağı/tarihi kaybolur (bu deponun
    dokümantasyon geleneği — bkz. CLAUDE.md §4 tek-kaynak yasası emsalleri)."""
    css = TEMA.read_text(encoding="utf-8")
    m = re.search(r"--color-yon-arti:\s*var\(--yon-arti\);", css)
    assert m, "yön köprüsü tema.css'te bulunamadı"
    civar = css[max(0, m.start() - 400) : m.start()]
    assert "TSK-132" in civar, "yön utility köprüsü künyesiz eklenmiş (TSK-132 civarda yok)"

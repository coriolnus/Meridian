"""v407 — TSK-134 D5: JETONLAR.CSS ↔ TEMA.CSS SHADCN AD ÇAKIŞMASI, BEYANLI (2026-09-04).

TETİK: ROADMAP `[TSK-134]` keşfi "`ui/src/jetonlar.css` genel-amaçlı adları (`--card`,
`--card-2`, `--accent`, `--accent-2`, `--accent-tint`, `--bg`, `--tx*`, `--line*`) pano shadcn
temasıyla AYNI adı tanımlıyor" SEKİZ isim iddia ediyordu. TSK-132 brief keşfi (2026-09-04) bunu
ÖLÇEREK TEKRAR SINADI: `card-2`/`accent-2`/`accent-tint`/`bg`/`tx*`/`line*` shadcn'in
`--card`/`--accent` gibi TEK KELİMELİK adlarıyla AYNI DEĞİL — GERÇEK isim-düzeyi çakışma
(jetonlar.css `:root` ∩ tema.css `:root`) İKİDİR: `--card`, `--accent`. tema.css KAZANIR çünkü
`@import "./jetonlar.css"` tema.css'in EN BAŞINDA (dosyanın kendi shadcn `:root` bloğundan
ÖNCE) ve CSS'te aynı özgüllükte (`:root`, tek sınıf yok) SON bildirim kazanır.

BU TUR KOD DEĞİŞTİRMEDİ (brief D5): yalnız BEYAN + ÇİVİ. `ops/jeton_css_uret.py::BASLIK`
(jetonlar.css'in üretici başlığı, tek yazma noktası) çakışmayı adıyla taşıyor; jetonlar.css
`python ops/jeton_css_uret.py` ile YENİDEN ÜRETİLDİ (`--kontrol` GÜNCEL). Düşürme (jetonlar.css
sözlüğünden bu iki adı çıkarmak, eski sayfaların bağımlılığını kırmadan) AYRI bir kalem —
kapsam DIŞINDA, ROADMAP notu Rol-1'e bırakıldı.

NUMARA ÇAKIŞMASI TARANDI (2026-09-04): `ls tests | grep v407` BOŞ döndü (v406 bu turun kardeşi).

ÇİVİNİN SINIFI: metin/CSS-parse ölçümü — tarayıcı cascade DAVRANIŞI değil, isim KÜMESİ ölçülür
ve BEYANLA eşleşiyor mu sınanır. Yeni bir çakışma (ör. jetonlar.css'e `--tx` gibi tema.css'te
de yaşayan bir ad eklenirse, ya da tema.css'e `--tx` eklenirse) BEYANLI kümeyi büyütür ve bu
çivi ÖTER — sessizce büyümüyor. MUTASYONLA sınandı (rapor: tema.css'e `--tx` eklemek çiviyi
öttürdü, geri alındı).
"""
from __future__ import annotations

import pathlib
import re

from meridian import config

ROOT = pathlib.Path(config.ROOT)
UI_SRC = ROOT / "ui" / "src"
JETONLAR_CSS = UI_SRC / "jetonlar.css"
TEMA_CSS = UI_SRC / "tema.css"
JETON_URET = ROOT / "ops" / "jeton_css_uret.py"

#: BEYAN — TEK KAYNAK bu sözlük DEĞİL, `ops/jeton_css_uret.py::BASLIK`in kendi metni (aşağıdaki
#: `test_BASLIK_CAKISMAYI_BEYAN_EDIYOR` ikisini birlikte zorlar). Burada de facto ÖLÇÜLEN
#: durumu tutmak, çivinin kendi hükmünü kendi kopyasıyla karşılaştırmasını sağlar.
BEYANLI_CAKISMA = frozenset({"--card", "--accent"})


def test_olculen_dosyalar_YERINDE():
    """KÖRLÜK ALARMI: yol bayatlarsa aşağıdaki her okuma sessizce boş/eksik metin döner ve
    'çakışma yok' bir okuma yokluğu olur, gerçek bir ölçüm değil."""
    for p in (JETONLAR_CSS, TEMA_CSS, JETON_URET):
        assert p.is_file(), f"ölçülecek dosya yok: {p}"


def _root_adlari(metin: str) -> set[str]:
    """Bir CSS metnindeki TÜM `:root { ... }` bloklarının birleşik özel-özellik adları.
    tema.css İKİ ayrı `:root` bloğu taşıyor (seri rampası + shadcn tabanı, satır 111 ve 142) —
    yalnız İLKİNİ bulan bir regex ikinciyi (`--card`in GERÇEK yaşadığı blok) sessizce KAÇIRIR ve
    aşağıdaki kesişim iddiası hep boş dönerdi (yanlış 'çakışma yok')."""
    adlar: set[str] = set()
    for m in re.finditer(r"\n:root\s*\{(.*?)\n\}", metin, re.S):
        adlar |= set(re.findall(r"(--[a-zA-Z0-9_-]+):", m.group(1)))
    return adlar


def test_ROOT_BLOK_DEDEKTORU_kendisi_olculuyor():
    """POZİTİF KONTROL (v378 K6 / v388 emsali): örnek metinde İKİ ayrı `:root` bloğu var —
    dedektör yalnız birini bulup dursaydı bu test onu yakalar."""
    ornek = "\n:root {\n  --a: 1;\n}\nfoo {\n  --z: 9;\n}\n:root {\n  --b: 2;\n}\n"
    assert _root_adlari(ornek) == {"--a", "--b"}, "dedektör ikinci :root bloğunu kaçırıyor"


def test_JETONLAR_TEMA_CAKISMASI_BEYANLI_KUMEYLE_AYNI():
    """(D5) GERÇEK kesişim BEYAN edilen kümeyle BİREBİR — ne eksik ne fazla. Fazlası: yeni bir
    çakışma sessizce doğdu ve beyan edilmedi (mutasyon: tema.css'e `--tx` eklemek bunu ölçtü).
    Eksiği: beyan artık bu depoyu tarif etmiyor (ör. biri jetonlar.css'ten `--card`i sildi) —
    ikisi de sessizce geçmemeli, KARAR gerektirir."""
    jeton_adlari = _root_adlari(JETONLAR_CSS.read_text(encoding="utf-8"))
    tema_adlari = _root_adlari(TEMA_CSS.read_text(encoding="utf-8"))
    assert jeton_adlari, "jetonlar.css :root okunamadı — desen bayat"
    assert tema_adlari, "tema.css :root okunamadı — desen bayat"
    cakisma = jeton_adlari & tema_adlari
    assert cakisma == BEYANLI_CAKISMA, (
        f"gerçek çakışma {sorted(cakisma)}, beyan {sorted(BEYANLI_CAKISMA)} — "
        "ops/jeton_css_uret.py::BASLIK ve bu çivi birlikte güncellenmeli")


def test_IMPORT_SIRASI_jetonlar_ONCE_govde_SONRA():
    """CASCADE KAZANANI SIRADAN: tema.css'in KENDİ shadcn `:root` gövdesi (`--card`in GERÇEK
    tanımı) metinde `@import "./jetonlar.css"`tan SONRA gelmeli — yoksa 'tema.css kazanır'
    iddiası (BASLIK'a yazılan beyan) YANLIŞ olurdu."""
    css = TEMA_CSS.read_text(encoding="utf-8")
    import_idx = css.index('@import "./jetonlar.css"')
    govde_idx = css.index("\n:root {\n  --radius:")
    assert import_idx < govde_idx, (
        "tema.css'in shadcn :root gövdesi import'tan ÖNCE — cascade sırası ters, "
        "'tema.css kazanır' beyanı artık doğru değil")


def test_BASLIK_CAKISMAYI_BEYAN_EDIYOR():
    """(D5, TSK-134) Üretici başlık (`ops/jeton_css_uret.py::BASLIK`) çakışan iki adı ADIYLA ve
    künyeli yazıyor mu — beyan koddaki `BEYANLI_CAKISMA`dan DEĞİL, üretici modülün kendi
    metninden okunur: ikisi ayrışırsa biri unutulmuş demektir."""
    kaynak = JETON_URET.read_text(encoding="utf-8")
    m = re.search(r'BASLIK = """(.*?)"""', kaynak, re.S)
    assert m, "BASLIK sabiti okunamadı — desen bayat"
    baslik = m.group(1)
    for ad in BEYANLI_CAKISMA:
        assert ad in baslik, f"BASLIK {ad} çakışmasını beyan etmiyor"
    assert "TSK-134" in baslik, "beyan künyesiz — gerekçe/kapsam izlenemez"


def test_JETONLAR_CSS_BASLIGI_URETICIYLE_AYNI():
    """ÜRETİLMİŞ dosya elle düzenlenmez (bu depo kuralı, CLAUDE.md §2) — jetonlar.css'in İLK
    bloğu (ilk `:root`tan önceki metin) `ops/jeton_css_uret.py::BASLIK` ile BİREBİR AYNI olmalı.
    Ayrışma = BASLIK değişti ama `python ops/jeton_css_uret.py` koşulmadı — yani D5 beyanı
    ops/'ta yazılı ama jetonlar.css'e hiç ULAŞMADI."""
    kaynak = JETON_URET.read_text(encoding="utf-8")
    m = re.search(r'BASLIK = """(.*?)"""', kaynak, re.S)
    assert m, "BASLIK sabiti okunamadı — desen bayat"
    baslik = m.group(1)
    css = JETONLAR_CSS.read_text(encoding="utf-8")
    assert css.startswith(baslik), (
        "jetonlar.css başlığı ops/jeton_css_uret.py::BASLIK ile ayrışmış — "
        "`python ops/jeton_css_uret.py` koşulmamış olabilir")


def test_PANO_KAYNAGINDA_CARD_ACCENT_BRACKET_OKUMASI_YOK():
    """Çakışma zararsız çünkü pano hiçbir yerde `var(--card)`/`var(--accent)`ı bracket'le
    OKUMUYOR (utility `bg-card`/`bg-accent` `@theme inline`in KENDİ `--color-card`/
    `--color-accent` eşlemesinden gelir, jetonlar.css'in aynı adlı `--card`/`--accent`ından
    değil) — ölçüldü 2026-09-04. Bracket okuması olsaydı hangi tanımın kazandığı GÖRÜNMEZ bir
    kırılganlık olurdu (tema.css bugün kazanıyor ama import sırası tersine dönerse sessizce
    jetonlar.css kazanırdı)."""
    ihlaller: list[str] = []
    desen = re.compile(r"\[var\(--(card|accent)\)\]")
    for p in sorted(set(UI_SRC.rglob("*.ts")) | set(UI_SRC.rglob("*.tsx"))):
        metin = p.read_text(encoding="utf-8")
        if desen.search(metin):
            ihlaller.append(str(p.relative_to(ROOT)))
    assert not ihlaller, f"pano kaynağı --card/--accent'i bracket'le okuyor: {ihlaller}"

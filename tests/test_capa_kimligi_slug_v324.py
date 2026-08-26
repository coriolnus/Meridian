"""ÇAPA KİMLİĞİ SLUG OLMAK ZORUNDA — v324 (2026-08-26)

NEDEN BU ÇİVİ VAR — ÖLÇÜLMÜŞ VAKA, aynı sınıfın İKİNCİ tekrarı.

A turu (arayüz dili sözlüğü, `docs/ARAYUZ-SOZLUGU.md`) kullanıcıya görünen metni
çeviriyordu. Kapsamı "çift tırnaklı dize literalleri" diye daralttım. O daraltma
YETERSİZDİ: çift tırnaklı bir dize KULLANICI METNİ OLMAK ZORUNDA DEĞİLDİR.

    ui/src/pano/yuzeyler/antrenman/Sprint.tsx:120   kimlik="sprint"  → kimlik="antrenman turu"
    ui/src/pano/yuzeyler/antrenman/Hermes.tsx:67    kimlik="hermes"  → kimlik="danışma"

`kimlik` sarmalayıcıya gider ve orada `id={`bolum-${kimlik}`}` olur — yani bir DOM
ÇAPASIDIR. Bozulduğunda kenar çubuğundaki derin bağ HATA VERMEZ: sayfa açılır,
bölüme kaydırmaz. `id="bolum-antrenman turu"` içindeki BOŞLUK ayrıca CSS/`querySelector`
tarafında ayrı bir tuzaktır.

v288 bunu kayıt↔çapa PARİTESİ üzerinden yakaladı (ve yakaladı — 26 dakikalık tam
suite'in tek kırmızısıydı). Ama v288 ancak kayıt ile ekran AYRIŞTIĞINDA öter. İkisi
BİRLİKTE yeniden adlandırılsaydı parite korunur, çivi susar, ve ortada boşluklu bir
DOM id kalırdı. Bu çivi o boşluğu kapatır: değeri BİÇİMİNDEN denetler, eşinden değil.

SÖZLEŞME: `ui/src/pano/**` içinde geçen her `kimlik` DEĞERİ slug'dır — `^[a-z0-9_-]+$`.
Büyük harf, boşluk, Türkçe karakter YASAK. Kullanıcıya gösterilecek ad `baslik`tır.

ALT ÇİZGİ NEDEN SERBEST — ölçülerek genişletildi, tahminle değil. İlk yazımda desen
`^[a-z0-9-]+$` idi ve üç YALANCI POZİTİF verdi: `kabuk/krizUclari.ts`teki
`soft_halt` · `cancel_open` · `learn_halt`. Bunlar DOM çapası değil, `KolKimlik` tip
anahtarları — yani API kimlikleri. Onları "düzeltmek" çalışan bir sözleşmeyi kaynağı
çiviye uydurmak için bozmak olurdu. Çivinin gerçekten koruduğu şey ALFABE değil BİÇİM:
değer TANIMLAYICI görünmeli, DÜZYAZI değil. Alt çizgi tanımlayıcı biçimidir; boşluk ve
`ı/ş/ğ` değildir.
"""
from __future__ import annotations

import pathlib
import re

import pytest

KOK = pathlib.Path(__file__).resolve().parent.parent
PANO = KOK / "ui" / "src" / "pano"

pytestmark = pytest.mark.skipif(not PANO.exists(), reason="ui/ yok — pano kaynağı bu ağaçta değil")

SLUG = re.compile(r"^[a-z0-9_-]+$")
# JSX propu (`kimlik="x"` / `kimlik={"x"}`) ve kayıt alanı (`kimlik: "x"`) — ikisi de
# aynı değeri besliyor, ikisi de denetlenir.
DEGER = re.compile(r'\bkimlik\s*[:=]\s*\{?\s*"([^"]*)"')


def _kaynaklar() -> list[pathlib.Path]:
    return sorted([*PANO.rglob("*.tsx"), *PANO.rglob("*.ts")])


def test_ayristirici_bayat_degil():
    """Regex hiçbir şey görmezse aşağıdaki çivi TRIVIAL geçer. Bu nöbetçi onu yakalar.
    (Bu depoda birebir bu tuzağa düşüldü — v288'in kendi nöbetçisine bak.)"""
    toplam = sum(len(DEGER.findall(p.read_text(encoding="utf-8"))) for p in _kaynaklar())
    assert toplam >= 20, f"ayrıştırıcı yalnız {toplam} `kimlik` değeri gördü — desen bayat"


def test_her_capa_kimligi_SLUG():
    bozuk: list[str] = []
    for p in _kaynaklar():
        for satir_no, satir in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            for deger in DEGER.findall(satir):
                if not SLUG.match(deger):
                    bozuk.append(f"{p.relative_to(KOK).as_posix()}:{satir_no}  kimlik={deger!r}")
    assert not bozuk, (
        f"slug OLMAYAN {len(bozuk)} çapa kimliği:\n  " + "\n  ".join(bozuk) + "\n"
        "`kimlik` DOM çapasıdır (`id={`bolum-${kimlik}`}`) — kullanıcı metni DEĞİLDİR.\n"
        "Gösterilecek adı `baslik`e yaz; `kimlik`i slug bırak."
    )

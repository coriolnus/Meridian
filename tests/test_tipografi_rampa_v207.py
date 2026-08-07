"""D6 ÇİVİSİ — `runbook.html` tip rampası (2026-08-07).

NE ÇAKIYOR. BASELINE-2026-08-06 **T10** bu yüzeyde üç rampa-dışı sabit ölçü saydı
(`15px` gövde, `26px` h1, `18px` h2) + iki göreli ölçü (`.86em`/`.92em`). D6 turu ölçtü ve
hepsini rampaya taşıdı; hüküm ve sayılar `research/olcumler/tipografi_rampa_2026-08-07/`
ve DESIGN.md § "runbook.html on the ramp"da.

NEDEN LİNT DEĞİL ÇİVİ. `test_tasarim_token_v153.py` runbook.html'i BİLEREK kapsam dışında
tutar (orada gerekçesiyle yazılı: onu renk lintine sokmak ölçüm değil HÜKÜM olurdu ve o hüküm
verilmedi). O karar RENK içindir ve bu dosya onu değiştirmez — burada yalnız TİP ölçüleri
çakılıyor. İki eksen ayrı yürüyor; bu dosya renge hiç bakmaz.

NEDEN DEĞERLERİ DEĞİL KURALI ÇAKIYORUZ. Bir sonraki tur gövdeyi 14'ten başka bir RAMPA
basamağına taşımak isterse bu testin düşmemesi gerekir — düşmesi gereken tek şey rampadan
ÇIKMAK. Bu yüzden asıl çivi (`test_her_font_size_rampada`) basamak kümesini sınar, tek tek
sayıları değil. Ölçülmüş İLİŞKİLER ayrıca çakılır, çünkü hükmü taşıyan onlardır.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[1]
RUNBOOK_HTML = KOK / "meridian" / "web" / "runbook.html"
INDEX_HTML = KOK / "meridian" / "web" / "index.html"
DESIGN_MD = KOK / "DESIGN.md"
OLCUM = KOK / "research" / "olcumler" / "tipografi_rampa_2026-08-07"

# DESIGN.md Rampa Kuralı — dokuz basamak, başkası yok.
RAMPA = {10, 11, 12, 13, 14, 17, 20, 24, 28}

_YORUM = re.compile(r"/\*.*?\*/|<!--.*?-->", re.S)
_FONT_SIZE = re.compile(r"font-size:\s*([^;}\s]+)")


def _kural_govdesi(yol: Path) -> str:
    """Yorumlar ÇIKARILIR. Gerekçe metni bir bildirim değildir — bu dosyanın kendi
    gerekçelerinde `15px` geçiyor olması onu ihlal saymamalı (v153'ün `_yorumsuz_html`
    dersi; sürüklenme yorumda değil kuralda yaşar)."""
    return _YORUM.sub("", yol.read_text(encoding="utf-8"))


def _font_size_degerleri(yol: Path) -> list[str]:
    return _FONT_SIZE.findall(_kural_govdesi(yol))


def test_her_font_size_rampada():
    """ASIL ÇİVİ. Kural gövdesindeki HER `font-size` bir rampa basamağı olmalı.

    Göreli birimler (`em`/`rem`/`%`) de düşürür: T10'un ikinci bacağı buydu ve ölçüldüğünde
    ikisi de zaten bir basamağa nişan alıyordu (14px'te .86em=12,04 · .92em=12,88). Yaklaşık
    doğru bir değer, belirsiz bir beyandır."""
    disari = []
    for ham in _font_size_degerleri(RUNBOOK_HTML):
        m = re.fullmatch(r"(\d+)px", ham)
        if not m or int(m.group(1)) not in RAMPA:
            disari.append(ham)
    assert not disari, (
        f"runbook.html rampa dışı font-size taşıyor: {disari}. "
        f"İzinli basamaklar: {sorted(RAMPA)} (DESIGN.md Rampa Kuralı). "
        "Yeni bir ölçü gerekiyorsa gereken şey farklı bir öğedir — ya da ölçülmüş bir "
        "sapma hükmü (bkz. research/olcumler/tipografi_rampa_2026-08-07/)."
    )


def test_uc_ihlal_geri_gelmedi():
    """T10'un ADIYLA saydığı üç değer. Yukarıdaki çivi bunları zaten yakalar; bu test
    kusuru ADIYLA anıyor ki geri gelirse hata mesajı hangi vaka olduğunu söylesin."""
    govde = _kural_govdesi(RUNBOOK_HTML)
    for kotu, nerede in (("15px", "gövde"), ("26px", "h1"), ("18px", "h2"),
                         (".86em", "code"), (".92em", "em")):
        assert f"font-size:{kotu}" not in govde.replace(" ", ""), (
            f"T10 nüksetti: {nerede} yeniden `{kotu}` (rampa dışı). "
            "D6 hükmü DESIGN.md § 'runbook.html on the ramp'ta."
        )


def test_govde_panonun_uzun_metin_olcutuyle_ayni():
    """Hükmün ÇEKİRDEĞİ: runbook gövdesi artık kendi uzun-metin sözleşmesini icat etmiyor,
    panonunkini (`index.html` `.md`) kullanıyor. Ölçüt ORADAN okunur — burada sabit
    yazılsaydı iki kopya olurdu ve zamanla ayrışırlardı (bu deponun baskın hata deseni)."""
    md = re.search(r"\.md\{([^}]*)\}", _kural_govdesi(INDEX_HTML))
    assert md, "index.html `.md` kuralı bulunamadı — ölçüt kayboldu, hüküm dayanaksız kaldı"
    kural = md.group(1).replace(" ", "")
    olcut = {k: v for k, v in (p.split(":", 1) for p in kural.split(";") if ":" in p)}

    body = re.search(r"\nbody\{([^}]*)\}", _kural_govdesi(RUNBOOK_HTML))
    assert body, "runbook.html `body` kuralı bulunamadı"
    b = body.group(1).replace("\n", "").replace(" ", "")

    assert f"font-size:{olcut['font-size']}" in b, (
        f"runbook gövdesi panonun uzun-metin ölçütünden ayrıştı "
        f"(`.md` {olcut['font-size']}, runbook farklı)"
    )
    assert f"line-height:{olcut['line-height']}" in b, (
        f"satır yüksekliği ayrıştı (`.md` {olcut['line-height']})"
    )
    p = re.search(r"\np\{([^}]*)\}", _kural_govdesi(RUNBOOK_HTML))
    assert p and f"max-width:{olcut['max-width']}" in p.group(1).replace(" ", ""), (
        f"ölçü (max-width) ayrıştı (`.md` {olcut['max-width']})"
    )


def test_baslik_merdiveni_olculen_ayrimi_koruyor():
    """Merdivenin işi AYIRMAKTIR. Ölçülen hüküm: h1=28 · h2=20 · gövde=14 — h1↔h2 cap
    ayrımını eski 26/18'le birebir korur (5,64px) ve h2↔gövde ayrımını ikiye katlar
    (2,11 -> 4,23px). Bu ikinci sayı BASELINE:92'nin `flat-type-hierarchy` bulgusudur:
    çapayla gelen operatör bir h2'ye düşer, h1'e değil."""
    govde = _kural_govdesi(RUNBOOK_HTML)
    olculen = {}
    for etiket in ("h1", "h2"):
        m = re.search(rf"\n{etiket}\{{([^}}]*)\}}", govde)
        assert m, f"runbook.html `{etiket}` kuralı bulunamadı"
        fs = _FONT_SIZE.search(m.group(1))
        assert fs, f"`{etiket}` font-size taşımıyor"
        olculen[etiket] = int(fs.group(1).removesuffix("px"))
    body = re.search(r"\nbody\{([^}]*)\}", govde)
    olculen["body"] = int(_FONT_SIZE.search(body.group(1)).group(1).removesuffix("px"))

    assert olculen["h1"] > olculen["h2"] > olculen["body"], (
        f"merdiven monoton değil: {olculen}"
    )
    # Ölçülen ayrımların KORUNMASI: h1↔h2 en az bir tam rampa aralığı (20->28), ve
    # h2 gövdenin en az bir basamak üstünde. Sayı değil İLİŞKİ çakılıyor.
    assert olculen["h1"] - olculen["h2"] >= 8, (
        f"h1↔h2 ayrımı ölçülen 28/20 hükmünün altına düştü: {olculen} — "
        "24/20 adayı ölçüldü ve h1↔h2'yi 5,64px'ten 2,82px'e yarıya indiriyordu"
    )
    assert olculen["h2"] - olculen["body"] >= 6, (
        f"h2↔gövde ayrımı `flat-type-hierarchy` bölgesine geri düştü: {olculen} — "
        "eski 18/15 buradaydı (2,11px cap ayrımı, BASELINE:92)"
    )


def test_baslik_ici_kod_gomulmedi():
    """Kaynakta 15 `##` başlığının TAMAMI baştan sona bir kod parçasıdır
    (`## \\`ops/kapilar.sh\\``). Düz `code{font-size:12px}` onları gövde ölçüsüne düşürüp
    başlık olmaktan çıkarırdı — bu yüzden `h2 code` ayrı ve bir üst basamakta."""
    govde = _kural_govdesi(RUNBOOK_HTML)
    m = re.search(r"h2 code\{([^}]*)\}", govde)
    assert m, ("`h2 code` kuralı yok — başlık içi kod gövde ölçüsüne düşer ve 15 başlık "
               "sessizce mertebe kaybeder (ölçüldü: docs/RUNBOOK.md'de 15 adet `## \\`…\\``)")
    kod_px = int(_FONT_SIZE.search(m.group(1)).group(1).removesuffix("px"))
    h2_px = int(_FONT_SIZE.search(re.search(r"\nh2\{([^}]*)\}", govde).group(1))
                .group(1).removesuffix("px"))
    assert kod_px in RAMPA and kod_px < h2_px, (
        f"başlık içi kod ölçüsü ({kod_px}px) rampada ve h2'nin ({h2_px}px) altında olmalı"
    )


@pytest.mark.parametrize("dosya", ["ON_KAYIT.md", "olcum.html", "olcum_sonucu.json",
                                   "baslik_olcum.html", "ornek_metin.json",
                                   "baslik_ornegi.json", "en_dar_h1_araligi.html",
                                   "korpus_uret.py"])
def test_kanit_zinciri_depoda(dosya):
    """EDG-016 dersi (MERIDIAN_ENGINEERING_LOG): bir hüküm, kanıtı + ÜRETEN KODU depoda
    değilse tekrar-üretilemez bir iddiadır. Ölçüm scratchpad'de yaşarsa silindiği gün
    DESIGN.md'deki sayılar dayanaksız kalır.

    `korpus_uret.py` listeye SONRADAN girdi ve girmesi gereken asıl dosya oydu: ilk turda
    harness'lar depodaydı ama onları besleyen korpus çıkarımı satır-içi heredoc'tu — yani
    kanıt vardı, kanıtı ÜRETEN kod yoktu. Tam da EDG-016'nın sınıfı."""
    assert (OLCUM / dosya).exists(), (
        f"D6 kanıt zinciri kopuk: {dosya} yok. DESIGN.md'nin tip rampası hükmü bu "
        "dosyalara dayanıyor (ön-kayıt + üretici + harness + sonuç)."
    )


def test_korpus_ureticisi_artefaktlari_birebir_uretiyor():
    """Üreticinin VARLIĞI yetmez — ÜRETTİĞİ şey ölçülen şey olmalı. Betik yeniden koşar ve
    üç artefaktın commit'li hâliyle SHA-256 karşılaştırılır.

    Bu test `docs/RUNBOOK.md` değişince DÜŞER ve düşmesi DOĞRUDUR: o zaman DESIGN.md'deki
    D6 sayıları artık yürürlükteki belgeye ait değildir ve ölçüm yenilenmelidir. Düşen bu
    test 'betiği düzelt' demez, 'ölçümü tazele' der."""
    import hashlib
    import importlib.util

    spec = importlib.util.spec_from_file_location("korpus_uret", OLCUM / "korpus_uret.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    ayrisan = []
    for ad, icerik in mod.uretilenler().items():
        diskte = (OLCUM / ad).read_text(encoding="utf-8")
        if hashlib.sha256(icerik.encode()).hexdigest() != hashlib.sha256(diskte.encode()).hexdigest():
            ayrisan.append(ad)
    assert not ayrisan, (
        f"korpus artefaktları üreticiyle ayrıştı: {ayrisan}. `docs/RUNBOOK.md` değiştiyse "
        "D6 ölçümü o belgeye ait DEĞİLDİR — yeniden koş, sonra DESIGN.md'yi güncelle. "
        "Kontrol: python research/olcumler/tipografi_rampa_2026-08-07/korpus_uret.py --kontrol"
    )


def test_design_md_hukmu_yaziyor():
    """YASA 6'nın tipografi hâli: ölçülen ama yazılmayan hüküm, bir sonraki denetimde ya
    silinir ya sessizce genişletilir. DESIGN.md'nin envanter tablosu da düzeltilmiş
    olmalı — o tablo 'no off-ramp fixed literal on any surface' derken runbook'u saymıyordu."""
    d = DESIGN_MD.read_text(encoding="utf-8")
    assert "runbook.html` on the ramp" in d, "D6 hükmü DESIGN.md'ye yazılmamış"
    assert "| `runbook.html` | 0 |" in d, (
        "akışkan-tip envanteri hâlâ dördüncü yüzeyi saymıyor — 'any surface' niceleyicisi "
        "üç satırlık bir tabloda duruyor"
    )

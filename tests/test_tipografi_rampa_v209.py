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

from tests.conftest import betikten_modul_yukle

KOK = Path(__file__).resolve().parents[1]
RUNBOOK_HTML = KOK / "meridian" / "web" / "runbook.html"
INDEX_HTML = KOK / "meridian" / "web" / "index.html"
DESIGN_MD = KOK / "DESIGN.md"
OLCUM = KOK / "research" / "olcumler" / "tipografi_rampa_2026-08-07"

# DESIGN.md Rampa Kuralı — dokuz basamak, başkası yok.
#
# 2026-08-24 · DUB DÖNÜŞÜMÜ (KARAR-2026-08-24-B §3). İki değişiklik ve ikisi de ÖLÇÜLDÜ:
#   +30  Dub Analytics'in büyük metrik rakamı. Rampanın yeni en üst basamağı; `index.html`de
#        jeton taşır (`--t-num`) ve tek okuyucusu `.mcard .v`dir.
#   −13  Kaldırıldı. Gerekçe kararın kendi cümlesi: ara basamakların oranı hiyerarşi değil
#        GÜRÜLTÜ üretiyor (14→15 = 1.07; 13→14 = 1.077). Bedeli ölçüldü ve ödendi:
#        DÖRT yüzeyin tamamında gövde basamağına (14px) taşındı: `index.html` 28,
#        `landing.html` 12, `workflow.html` 3, `runbook.html` 3 kullanım. İlk üçü artık
#        `var(--t-body)` yazıyor (rampa jetonlandı); runbook ham px kalır ve bu dosyanın
#        lint'i onu okur — `test_govde_panonun_uzun_metin_olcutuyle_ayni` iki biçimi
#        index.html'in `:root`undan çözerek karşılaştırır.
#   15   Zaten rampada DEĞİLDİ (D6, 2026-08-07'de kaldırılmıştı); karar onu tekrar anıyor.
# ~~Emekli rampa (D6, 2026-08-07 → 2026-08-24): {10, 11, 12, 13, 14, 17, 20, 24, 28}~~
RAMPA = {10, 11, 12, 14, 17, 20, 24, 28, 30}

_YORUM = re.compile(r"/\*.*?\*/|<!--.*?-->", re.S)
_FONT_SIZE = re.compile(r"font-size:\s*([^;}\s]+)")


def _kural_govdesi(yol: Path) -> str:
    """Yorumlar ÇIKARILIR. Gerekçe metni bir bildirim değildir — bu dosyanın kendi
    gerekçelerinde `15px` geçiyor olması onu ihlal saymamalı (v153'ün `_yorumsuz_html`
    dersi; sürüklenme yorumda değil kuralda yaşar)."""
    return _YORUM.sub("", yol.read_text(encoding="utf-8"))


_KOK_TIP = dict(re.findall(r"--(t-[a-z0-9-]+|label-size)\s*:\s*(\d+px)",
                           _YORUM.sub(" ", INDEX_HTML.read_text(encoding="utf-8"))))


def _px_coz(govde: str) -> str:
    """`var(--t-body)` → `14px`, index.html'in kendi `:root` tablosundan."""
    return re.sub(r"var\(\s*--([a-z0-9-]+)\s*\)",
                  lambda m: _KOK_TIP.get(m.group(1), m.group(0)), govde)


def test_tip_jetonlari_HIYERARSI_RAMPASINDA():
    """Jetonlanmış her basamak rampada olmalı — jeton, rampadan kaçmanın yeni yolu OLAMAZ.

    2026-08-24'te index.html'in tip rampası jetonlandı (`--t-cap/--t-body/--t-lg/--t-sub/
    --t-h/--t-num`). Bir jetonun değeri sessizce rampa dışına kayarsa, onu okuyan 79 kural
    birden kayar ve `test_her_font_size_rampada` bunu GÖREMEZ (o kural gövdelerine bakar,
    jeton tanımına değil). Kapı burası."""
    tip = {k: v for k, v in _KOK_TIP.items() if k.startswith("t-")}
    assert len(tip) == 6, f"tip jetonu sayısı {len(tip)} (beklenen 6): {sorted(tip)}"
    disari = {k: v for k, v in tip.items() if _px(v) not in RAMPA}
    assert not disari, f"tip jetonu rampa dışında: {disari} · izinli {sorted(RAMPA)}"
    # HİYERARŞİ RAMPASI (Ö6) — yüzey rampasının ALT KÜMESİ ve adımları ölçülmüştür.
    # docs/kontrast-denetimi.md §12.3: karar §3'ün 11/14/16/20/24/30 rampası 16/14=1.1429
    # ile eşiğin (1.15) altında kaldı; daraltma 16 → 17 oldu.
    basamak = sorted(_px(v) for v in tip.values())
    assert basamak == [11, 14, 17, 20, 24, 30], (
        f"hiyerarşi rampası değişmiş: {basamak}. Değişecekse ÖLÇÜLEREK değişir "
        f"(research/olcumler/dub_donusumu_2026-08-24/olc.py · Ö6) ve §12.3 güncellenir.")
    adim = [round(basamak[i + 1] / basamak[i], 4) for i in range(len(basamak) - 1)]
    assert min(adim) >= 1.15 and max(adim) >= 1.25, f"Ö6 adım eşiği düştü: {adim}"


# ---- JETON ÇÖZÜCÜ (D1, 2026-08-24) ------------------------------------------------------------
# Rampa artık `--t-*` jetonlarıyla yönetiliyor: 2026-08-24 öncesi 165 sert punto kural
# gövdelerine dağılmıştı ve ölçek yarıdan fazla baypas ediliyordu. Ham `NNpx` ayrıştıran bir
# çivi, DOĞRU olan jetonlu yazımı "rampa dışı" sanar — yani düzeltmeyi cezalandırırdı.
# Bu dosyanın İDDİALARI değişmedi; yalnız ölçmeden önce jetonu çözüyor.
_JETON_PX = {"--t-cap": 11, "--t-body": 14, "--t-lg": 17, "--t-sub": 20,
             "--t-h": 24, "--t-num": 30, "--label-size": 11}


def _px(v: str) -> int:
    """`14px` ya da `var(--t-body)` → 14. Tanınmayan jeton SESSİZ GEÇMEZ, hata verir."""
    v = v.strip()
    j = re.fullmatch(r"var\(\s*(--[a-z0-9-]+)\s*\)", v)
    if j:
        px = _JETON_PX.get(j.group(1))
        assert px is not None, f"tanınmayan punto jetonu: {v} — `_JETON_PX`e ekle"
        return px
    return int(v.removesuffix("px"))


def _font_size_degerleri(yol: Path) -> list[str]:
    return _FONT_SIZE.findall(_kural_govdesi(yol))


def test_her_font_size_rampada():
    """ASIL ÇİVİ. Kural gövdesindeki HER `font-size` bir rampa basamağı olmalı.

    Göreli birimler (`em`/`rem`/`%`) de düşürür: T10'un ikinci bacağı buydu ve ölçüldüğünde
    ikisi de zaten bir basamağa nişan alıyordu (14px'te .86em=12,04 · .92em=12,88). Yaklaşık
    doğru bir değer, belirsiz bir beyandır."""
    # D1 (2026-08-24) — JETON ÇÖZÜLÜR, SONRA ÖLÇÜLÜR. Rampa artık `--t-*` jetonlarıyla
    # yönetiliyor (165 sert punto tek tek kural gövdelerindeydi ve ölçek yarıdan fazla
    # baypas ediliyordu). Ham `NNpx` arayan bir çivi, DOĞRU olan jetonlu yazımı "rampa dışı"
    # sanar — yani düzeltmenin kendisini cezalandırırdı. Çivinin İDDİASI aynı: çizilen punto
    # bir rampa basamağı olmalı; değişen, o puntoya nasıl ulaşıldığı.
    JETON_PX = {"--t-cap": 11, "--t-body": 14, "--t-lg": 17, "--t-sub": 20,
                "--t-h": 24, "--t-num": 30, "--label-size": 11}
    disari = []
    for ham in _font_size_degerleri(RUNBOOK_HTML):
        h = ham.strip()
        if h == "inherit":
            continue
        j = re.fullmatch(r"var\(\s*(--[a-z0-9-]+)\s*\)", h)
        if j:
            px = JETON_PX.get(j.group(1))
            if px is None or px not in RAMPA:
                disari.append(f"{h} (jeton tanınmadı ya da rampada değil)")
            continue
        m = re.fullmatch(r"(\d+)px", h)
        if not m or int(m.group(1)) not in RAMPA:
            disari.append(h)
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
                         (".86em", "code"), (".92em", "em"),
                         # 2026-08-24: 13px rampadan düştü ve runbook'un ÜÇ kullanımı
                         # (`.ust a`, `nav.toc`, `em`) gövde basamağına taşındı. Yukarıdaki
                         # asıl çivi bunu zaten yakalar; burada ADIYLA anılıyor ki nüksederse
                         # hata mesajı hangi kararın çiğnendiğini söylesin.
                         ("13px", "bağlantı/TOC/em")):
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
    # 2026-08-24 · index.html'in tip rampası JETONLANDI (`font-size:var(--t-body)`), runbook
    # hâlâ ham px yazıyor. ÖLÇÜLEN ŞEY ÖLÇÜDÜR, YAZILIŞ BİÇİMİ DEĞİL: jeton index.html'in
    # KENDİ `:root`undan çözülür. Buraya sabit `14px` yazmak, karşılaştırmanın iki kopyasını
    # yaratır ve bu dosyanın kovaladığı ayrışmanın ta kendisi olurdu.
    kural = _px_coz(md.group(1)).replace(" ", "")
    olcut = {k: v for k, v in (p.split(":", 1) for p in kural.split(";") if ":" in p)}

    body = re.search(r"\nbody\{([^}]*)\}", _kural_govdesi(RUNBOOK_HTML))
    assert body, "runbook.html `body` kuralı bulunamadı"
    b = body.group(1).replace("\n", "").replace(" ", "")

    # D1 (2026-08-24): karşılaştırma ÇÖZÜLMÜŞ değer üzerinden. İki taraf farklı BİÇİMDE
    # yazılabilir (biri `14px`, öteki `var(--t-body)`) ama iddia "aynı PUNTO" olmalı — biçim
    # eşitliği aramak, jetona geçen tarafı sahte kırmızıya düşürüyordu.
    _b_fs = _FONT_SIZE.search(b)
    assert _b_fs and _px(_b_fs.group(1)) == _px(olcut['font-size']), (
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
        olculen[etiket] = _px(fs.group(1))
    body = re.search(r"\nbody\{([^}]*)\}", govde)
    olculen["body"] = _px(_FONT_SIZE.search(body.group(1)).group(1))

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
    kod_px = _px(_FONT_SIZE.search(m.group(1)).group(1))
    h2_px = _px(_FONT_SIZE.search(re.search(r"\nh2\{([^}]*)\}", govde).group(1))
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

    mod = betikten_modul_yukle(OLCUM / "korpus_uret.py", "korpus_uret")

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

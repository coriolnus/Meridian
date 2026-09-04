"""v171 — WP-P/P9: kapsama ısı-matrisi · renk skalaları · B1/B6 · SH_TR borçları · senkron damgası.

ÖLÇÜLEN KUSUR SINIFLARI (dördü de bu turda kapandı ve dördü de AYNI aileden):
**bir şeyin BEYAN EDİLDİĞİ hâli ile EKRANDA ÇİZİLDİĞİ hâli arasındaki sessiz fark.**

  Ç1 · SKALA JETONDAN GELİR — ısı matrisinin dört sequential + dört diverging basamağı
       `tokens.json`/`:root` jetonlarıdır. Bir hücreye ham renk yazmak, ikinci temayı
       sessizce kırardı (`--nav-bg` emsali, v153). P9 diliminde ham renk sayımı SIFIR
       olmalı ve bu ölçülür, beyan edilmez.
  Ç2 · MERDİVEN ÇÖKÜŞÜ (B1) — `--tx3` iki temada da `--tx2`'nin bire-bir kopyasıydı ve
       bullet grafiğinin nitel bant listesi BEŞ elemanlıydı; oysa çağrıların çoğu İKİ bant
       istiyor, yani ekranda çizilen tek geçiş listenin ilk adımıydı (1.09:1 — görünmüyordu).
       Test hem jetonların AYRIŞTIĞINI hem merdivenin ÜÇ banda indiğini ölçer.
  Ç3 · İKİ SERİ AYNI RENK (B6) — `--violet` = `--accent`ti; efsane üç adı üç RENKLE
       etiketliyor, grafik ise deseni ayırıyordu. Artık tek tablo (`IC_SERI`) iki tüketiciyi
       (çizim + efsane) besliyor ve ayrışamazlar.
  Ç4 · ÖKSÜZ ALAN (YASA 6) — `intraday_shadow` satırının `red_nedeni` / `atr_kaynak` / `atr`
       / `limit` alanlarının panoda TEK okuyucusu yoktu. `red_nedeni` bir JETON kümesidir ve
       o küme `broker.py`nin `_red(...)` çağrılarıdır: test iki tarafı KARŞILAŞTIRIR, yani
       üretici yeni bir ret sebebi eklerse burada kırmızı verir.
  Ç5 · DAMGASIZ DURUM CÜMLESİ — "senkron hatası (OSError)" satırı NE ZAMAN ölçüldüğünü
       söylemiyordu ve altı gün önceki bir hata taze hüküm gibi okundu (ders (b)). Damga
       yoksa "damga yok" yazılır; `Date.now()` basmak uydurma olurdu.

Testler KAYNAĞA ve DAVRANIŞA bakar (repo deseni: v139/v151/v153/v160). Hüküm dilimleri
Node'da FİİLEN koşturulur — kaynakta doğru görünen bir eşik tablosunun yanlış dallandığı
bir vaka bu depoda zaten yaşandı (v160 `_patOK`).
"""
from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess

import pytest

SRC = pathlib.Path(__file__).resolve().parents[1]
WEB = SRC / "meridian" / "web"
APPJS = (WEB / "app.js").read_text()
INDEX = (WEB / "index.html").read_text()
TOKENS = json.loads((WEB / "tokens.json").read_text())
APIPY = (SRC / "meridian" / "api.py").read_text()
HERMES = (SRC / "meridian" / "hermes.py").read_text()
BROKER = (SRC / "meridian" / "broker.py").read_text()
MARKETVIEW = (SRC / "meridian" / "marketview.py").read_text()
RAPOR = (SRC / "docs" / "kontrast-denetimi.md").read_text()
CSS = re.sub(r"/\*.*?\*/", "", INDEX[INDEX.index("<style>") + 7:INDEX.index("</style>")], flags=re.S)

NODE = shutil.which("node")

# Yorumsuz gövde (v154/v155/v156/v160 deseni): bir kuralın GEREKÇESİNİ anlatan yorum, o
# kuralın ihlali sanılmamalı — "artık --tx3 kullanmıyoruz" cümlesi tam da aranan dizgiyi taşır.
KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))


def _govde(bas: str, son: str, kaynak: str = APPJS) -> str:
    i = kaynak.index(bas)
    return kaynak[i:kaynak.index(son, i)]


def _node(betik: str):
    if not NODE:
        pytest.skip("node bulunamadı — saf çekirdek testleri koşulamıyor (ÖLÇÜLMEDİ)")
    r = subprocess.run([NODE, "-e", betik], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"node hatası:\n{r.stderr}"
    return json.loads(r.stdout)


# ================================ JETON OKUMA / KONTRAST =========================================
def _blok(sel: str) -> str:
    i = CSS.index(sel)
    j = CSS.index("{", i)
    return CSS[j + 1:CSS.index("}", j)]


def _jetonlar(b: str) -> dict:
    return {m.group(1): m.group(2).strip()
            for m in re.finditer(r"--([a-z0-9-]+)\s*:\s*([^;}]+)", b)}


ROOT = _jetonlar(_blok(":root{"))
GECE_OV = _jetonlar(_blok(':root[data-theme="gece"]'))


def _rgba(deger, tema):
    d, tablo = deger.strip(), (dict(ROOT, **GECE_OV) if tema == "gece" else ROOT)
    for _ in range(8):
        m = re.fullmatch(r"--([a-z0-9-]+)", d)
        if not m:
            break
        d = tablo[m.group(1)].strip()
    m = re.fullmatch(r"#([0-9a-fA-F]{6})", d)
    if m:
        h = m.group(1)
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0)
    m = re.fullmatch(r"rgba?\(\s*(\d+),\s*(\d+),\s*(\d+),\s*([0-9.]+)\)", d)
    assert m, f"renk değil: {d!r}"
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)), float(m.group(4)))


def _uzerine(ust, alt):
    return tuple(round(ust[i] * ust[3] + alt[i] * (1 - ust[3])) for i in range(3)) + (1.0,)


def _yigin(katmanlar, tema):
    c = _rgba(katmanlar[0], tema)
    for k in katmanlar[1:]:
        c = _uzerine(_rgba(k, tema), c)
    return c


def _lum(c):
    def k(v):
        v /= 255.0
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * k(c[0]) + 0.7152 * k(c[1]) + 0.0722 * k(c[2])


def _oran(a, b):
    l1, l2 = sorted((_lum(a), _lum(b)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def _lstar(c):
    """CIE L* — ALGISAL açıklık ekseni. `_lum` (WCAG) kontrast oranı içindir; ÇG1 "iki seri
    birbirinden yeterince açık mı" diye sorar ve bu SORU L* eksenindedir. İkisini karıştırmak
    komşu adımı zeminin parlaklığına göre sessizce büyütür/küçültürdü."""
    y = _lum(c)
    return 116 * (y ** (1 / 3)) - 16 if y > 0.008856 else 903.3 * y


def _metin(ink, zemin, tema):
    zc = _yigin(zemin, tema)
    ic = _rgba(ink, tema)
    return _oran(_uzerine(ic, zc) if ic[3] < 1.0 else ic, zc)


# =================================================================================================
# Ç2 · B1 — ÜÇÜNCÜ BASAMAK AYRIŞTI VE MERDİVEN ÜÇ BANDA İNDİ
# =================================================================================================
def test_tx3_artik_tx2nin_KOPYASI_DEGIL_ve_AA_korunuyor():
    """B1'in birinci yarısı. `--tx3` iki temada da `--tx2` ile BİREBİR aynıydı (oran 1.00),
    yani 'üç basamaklı mürekkep merdiveni' ekranda iki basamaktı. Ayrışma ÖLÇÜLÜR; ve
    ayrışmanın bedeli AA olamaz — `--tx3` metin olarak kullanılıyor (.dk-neden, soru cümlesi,
    efsane), yani 4.5'in altına inemez."""
    for tema in ("gunduz", "gece"):
        assert _rgba("--tx3", tema) != _rgba("--tx2", tema), \
            f"--tx3 ({tema}) hâlâ --tx2'nin kopyası — B1 merdiven çöküşü geri geldi"
        adim = _oran(_rgba("--tx3", tema), _rgba("--tx2", tema))
        assert adim >= 1.20, f"--tx3 ↔ --tx2 adımı {adim:.2f} ({tema}) — ayrışma ölçülemez kadar dar"
        for zemin in (["--bg"], ["--card"], ["--card-2"]):
            o = _metin("--tx3", zemin, tema)
            assert o >= 4.5, f"--tx3 metin AA altı: {o:.2f} ({tema}, {zemin})"


def test_band_2_IKI_TEMAYA_da_girdi_ve_merdiven_adimlari_olculdu():
    """Yeni bir renk jetonunun tek temaya girmesi bu deponun kayıtlı arıza sınıfıdır
    (--nav-bg). Ayrıca merdivenin İDDİASI ölçülür: üç bant, iki adım, ikisi de gerçek."""
    assert "band-2" in ROOT and "band-2" in GECE_OV, "--band-2 iki temaya birden girmemiş"
    for tema in ("gunduz", "gece"):
        a1 = _oran(_rgba("--card-2", tema), _rgba("--band-2", tema))
        a2 = _oran(_rgba("--band-2", tema), _rgba("--tx2", tema))
        assert a1 >= 2.0 and a2 >= 2.0, \
            f"nitel bant adımları zayıf ({tema}): {a1:.2f} / {a2:.2f} — eski merdiven 1.09/1.15'ti"


_YOG_SATIRI = re.search(r"const YOG = \[(.*?)\];", KOD, re.S)


def test_bullet_merdiveni_UC_BANT_ve_hicbiri_tekrar_DEGIL():
    """B1'in ikinci yarısı — ve asıl kusur: liste beş elemanlıydı ama `bantlar` varsayılanı
    üç, çağrıların çoğu İKİ. Yani ekranda çizilen bantlar listenin İLK ikisiydi
    (`--card-2`, `--line`) ve o adım 1.09'du. Liste artık merdivenin KENDİSİ kadar."""
    assert _YOG_SATIRI, "YOG merdiven listesi bulunamadı — bullet çizimi yeniden yazılmış"
    jetonlar = re.findall(r"var\((--[a-z0-9-]+)\)", _YOG_SATIRI.group(1))
    assert jetonlar == ["--card-2", "--band-2", "--tx2"], \
        f"nitel bant merdiveni beklenen üçlü değil: {jetonlar}"
    assert len(set(jetonlar)) == 3, "merdivende tekrar eden jeton var — B1'in ta kendisi"
    assert "--tx3" not in jetonlar, \
        "--tx3 merdivene geri gelmiş: o jeton artık METİN basamağıdır, bant değil"


def test_bant_sayisi_MERDIVENE_bagli_sabit_5e_DEGIL():
    """`.slice(0, 5)` sabiti, merdiven kısaldığında fazladan sınırın son bandı sessizce
    TEKRARLAMASINA yol açardı — beş bant iddiasının kaynaktaki kalıntısı."""
    m = re.search(r"const bantlar = .*?\.slice\(0, ([^)]+)\)", KOD)
    assert m, "bantlar dilimleme satırı bulunamadı"
    assert m.group(1).strip() == "YOG.length", \
        f"bant sayısı merdivene bağlı değil: slice(0, {m.group(1)})"


def _bullet_bant_dilimi() -> str:
    dilim = _govde("  const YOG = [", "  const bar = olculdu")
    assert "const bantlar" in dilim and "const iz" in dilim, \
        "bant dilimi çıpaları kaymış — test boş bir dilim ölçemez"
    return dilim


def test_bullet_bantlari_NODEDA_UCTEN_FAZLA_CIZMEZ():
    """Davranış ölçümü: beş sınır verilse bile üç bant çizilir ve üçü de FARKLI jetondur.
    Kaynağa bakmak yetmez — `YOG[i] || YOG[YOG.length-1]` yedeği, fazla sınırı sessizce son
    bandın kopyası yapardı ve tabloda 'beş bant' görünürdü."""
    out = _node(
        "(function(){const W=150,H=18,IZ=12;const o={bantlar:[.2,.4,.6,.8,1]};\n"
        + _bullet_bant_dilimi() +
        "\nconst f=(iz.match(/fill=\"([^\"]+)\"/g)||[]);\n"
        "process.stdout.write(JSON.stringify(f));})();")
    assert len(out) == 3, f"{len(out)} bant çizildi — merdiven üç bant olmalı"
    assert len(set(out)) == 3, f"bantlar tekrar ediyor: {out}"


# =================================================================================================
# Ç3 · B6 — İKİ SERİ ARTIK AYNI RENK DEĞİL, VE EFSANE DESENİ GÖSTERİYOR
# =================================================================================================
def test_violet_accentin_KOPYASI_DEGIL_ve_uc_seri_bir_MERDIVEN():
    """B6. `--violet` = `--accent`ti (oran 1.00). Üç seri artık bir luminans merdiveni ve
    sıralama İKİ temada da aynı yönde olmalı — ters dönerse efsane grafiği yalanlar.

    D2 (2026-08-24) — TAŞIYICI DEĞİŞİMİ, SERİ ÜÇLÜSÜ DEĞİŞTİ. Karar §10.3 seri sözleşmesini
    `--accent`/`--violet`/`--tx3`ten `--blue`/`--violet`/`--violet2`ye taşıdı; jetonlar hâlâ
    tanımlı ama artık SERİ DEĞİLLER, yani bu çivi bugüne kadar var olmayan bir sözleşmeyi
    ölçüyordu (bayat, gecede 5.92 > 6.00 ile düşüyordu). İddia AYNEN duruyor — ölçtüğü üçlü
    tazelendi. İki eşik de KARARDA DONDURULMUŞTUR (§10, ölçümden ÖNCE):
      ÇG1 · komşu seriler arası ΔL* ≥ 15      ÇG2 · her seri kart zemininde ≥ 3.00
    ~~`_oran(--accent, --violet) >= 1.35`~~ DÜŞTÜ (2026-08-24): iki jeton artık komşu seri
    değil, aralarında oran ölçmek anlamsız — yerini ÇG1'in ΔL* adımı aldı.
    ~~`v >= 4.5` (AA, metin)~~ DÜŞTÜ (2026-08-24): efsane etiketi artık `--tx2` ile
    basılıyor, renk YALNIZ `<line stroke>` örneğinde. Seri jetonu metin OLMADIĞI için geçerli
    kural AA değil grafik-nesne kuralıdır (ÇG2 = 3.00). Bu muafiyetin BEDELİ var: aşağıdaki
    son iddia, jetonun metne geri sızmasını yasaklar — sızarsa 3.00 eşiği meşruiyetini
    kaybeder ve çivi kırmızı verir."""
    # 2026-08-24: seri jetonları rol adlarına geçti (`--violet` hiç mor değildi ve
    # `--lavender` denemesi `--mod-canli` ile BİREBİR çakıştığı için geri alındı).
    SERI = ("--sapphire", "--blue", "--sky")
    for tema in ("gunduz", "gece"):
        renkler = [_rgba(x, tema) for x in SERI]
        assert len(set(renkler)) == 3, f"seri jetonları kopyalanmış ({tema}): {renkler}"
        kart = ["--card"]
        oranlar = [_metin(x, kart, tema) for x in SERI]
        assert oranlar == sorted(oranlar, reverse=True), \
            f"seri merdiveni sırasız ({tema}): {[f'{o:.2f}' for o in oranlar]}"
        for ad, o in zip(SERI, oranlar):
            assert o >= 3.00, f"ÇG2 düştü — {ad} kartta {o:.2f} < 3.00 ({tema})"
        yildizlar = [_lstar(_uzerine(c, _yigin(kart, tema)) if c[3] < 1.0 else c) for c in renkler]
        for i in range(len(SERI) - 1):
            d = abs(yildizlar[i] - yildizlar[i + 1])
            assert d >= 15.0, \
                f"ÇG1 düştü — {SERI[i]} ↔ {SERI[i+1]} ΔL* {d:.1f} < 15 ({tema})"
    # ÇG2'nin (3.00) meşruiyet şartı: seri jetonu METİN olarak basılamaz. Efsanenin etiketi
    # `--tx2`dir; renk yalnız çizgi örneğinde yaşar. Sızarsa AA kuralı geri gelir ve gecedeki
    # `--violet2` (3.50) AA altı kalır — yani bu satır 3.00 eşiğinin bedelidir.
    efsane_g = _govde("function icEfsane() {", "\nconst CHECK_TR")
    assert 'color:var(--tx2)' in efsane_g, "efsane etiketi --tx2 değil — ÇG2 muafiyeti düştü"
    for jeton in SERI:
        assert f"color:var({jeton})" not in efsane_g, \
            f"{jeton} efsanede METİN rengi olmuş — AA kuralı geri gelir, ÇG2 yetmez"


def test_IC_serileri_TEK_TABLODAN_okunur_cizim_ve_efsane_AYRISAMAZ():
    """B6'nın asıl arızası efsanedeydi: çizim deseni ayırıyor, efsane rengi etiketliyordu.
    İki tüketici tek tablodan (`IC_SERI`) okursa ayrışamazlar."""
    assert "const IC_SERI = {" in KOD, "IC_SERI tablosu yok — efsane yeniden ayrışabilir"
    ictrend = _govde("function icTrend(hist) {", "const IC_SERI")
    assert "var(--blue)" not in ictrend and "var(--tx3)" not in ictrend, \
        "icTrend seri rengini tablodan DEĞİL doğrudan yazıyor — ayrışma kapısı açık"
    efsane = _govde("function icEfsane() {", "\nconst CHECK_TR")
    assert "IC_SERI" in efsane and "stroke-dasharray" in efsane, \
        "efsane çizgi ÖRNEĞİNİ göstermiyor (Ö8) — renk tek kanal kalır"
    # efsane hâlâ srow içinden çağrılıyor mu (ölü fonksiyon değil)
    assert "${icEfsane()}" in KOD, "icEfsane çağrılmıyor — okuyucusuz yazım (YASA 6)"


def test_IC_desenleri_UCU_de_FARKLI():
    """Renk körü okuyucunun taşıyıcı kanalı desendir; iki seri aynı deseni alırsa renk
    düzeltmesi tek başına yetmez."""
    tablo = _node("(function(){" + _govde("const IC_SERI = {", "function icEfsane()")
                  + "\nprocess.stdout.write(JSON.stringify(IC_SERI));})();")
    assert set(tablo) == {"gercek", "sim", "havuz"}
    desenler = [v[2] for v in tablo.values()]
    assert len(set(desenler)) == 3, f"seri desenleri tekrar ediyor: {desenler}"
    renkler = [v[1] for v in tablo.values()]
    assert len(set(renkler)) == 3, f"seri renkleri tekrar ediyor: {renkler}"


# =================================================================================================
# Ç1 · P9 ISI-MATRİSİ — SKALA JETONDAN, HAM RENK SIFIR, EKSENLER ÜRETİCİDEN
# =================================================================================================
P9_DILIM = _govde("const KM_OLCUM = [", "window.kmMod =")

_HEX = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
_FONK = re.compile(r"\b(?:rgba?|hsla?|oklch|color)\([^)]*\)")


def test_P9_diliminde_HAM_RENK_SIFIR():
    """Ç3 (v153) linti bu dilime de uygulanır ve ayrıca burada ölçülür: bir ısı skalası, ham
    renk kaçırmanın en olası yeridir (basamaklar sayısaldır, jeton yazmak 'fazladan iş'
    hissettirir). Kaçan tek değer ikinci temayı sessizce kırar."""
    kodsuz = "\n".join(l for l in P9_DILIM.splitlines() if not l.lstrip().startswith("//"))
    bulunan = sorted(set(_HEX.findall(kodsuz)) | set(_FONK.findall(kodsuz)))
    assert not bulunan, f"P9 diliminde jeton dışı ham renk: {bulunan}"


def test_isi_matrisi_skalasi_JETONLARDAN_gelir():
    """Sekiz basamağın sekizi de CSS'te bir jetona bağlı olmalı ve sekizi de İKİ temada
    tanımlı — `--nav-bg` sınıfının kapısı."""
    for i in range(1, 5):
        assert f".km-cell.k{i}{{background:var(--kap-{i})}}" in CSS.replace("\n", ""), \
            f"k{i} bandı jetona bağlı değil"
        assert f"kap-{i}" in ROOT and f"kap-{i}" in GECE_OV, f"--kap-{i} tek temada"
    for ad in ("dn2", "dn1", "dp1", "dp2"):
        jeton = f"--dv-{ad[1]}{ad[2]}"                     # dn2 → --dv-n2
        assert f".km-cell.{ad}{{background:var({jeton})}}" in CSS.replace("\n", ""), \
            f"{ad} kutbu jetona bağlı değil ({jeton})"
        assert jeton[2:] in ROOT and jeton[2:] in GECE_OV, f"{jeton} tek temada"


def test_sequential_rampa_TEK_HUE_ve_MONOTON():
    """'Tek-hue sequential' bir iddiadır ve ölçülür: dört basamak aynı mürekkepten türer
    (alfa artışı) ve yoğunluk her adımda TEK YÖNE gider. Ters dönen bir adım, skalayı
    okunamaz kılar ve hiçbir göz onu yakalamaz."""
    for tema in ("gunduz", "gece"):
        temel = {_rgba(f"--kap-{i}", tema)[:3] for i in range(1, 5)}
        assert len(temel) == 1, f"kapsama rampası tek hue değil ({tema}): {temel}"
        alfalar = [_rgba(f"--kap-{i}", tema)[3] for i in range(1, 5)]
        assert alfalar == sorted(alfalar) and len(set(alfalar)) == 4, \
            f"rampa monoton değil ({tema}): {alfalar}"
        lums = [_lum(_yigin(["--card", f"--kap-{i}"], tema)) for i in range(1, 5)]
        assert lums == sorted(lums) or lums == sorted(lums, reverse=True), \
            f"rampa zemin üstünde monoton değil ({tema}): {lums}"


def test_kapsama_rampasinin_TAVANI_AA_ile_sinirli():
    """Tavan alfa bir tasarım tercihi değil ÖLÇÜLMÜŞ bir sınır: hücrenin rakamı en koyu
    bandın üstünde okunabilir kalmalı. Bu eşik SONRADAN düşürülemez."""
    for tema in ("gunduz", "gece"):
        o = _metin("--tx", ["--card", "--kap-4"], tema)
        assert o >= 4.5, f"hücre rakamı en koyu kapsama bandında AA altı: {o:.2f} ({tema})"
        for ad in ("--dv-n2", "--dv-p2"):
            o2 = _metin("--tx", ["--card", ad], tema)
            assert o2 >= 4.5, f"hücre rakamı {ad} üstünde AA altı: {o2:.2f} ({tema})"


def test_diverging_kutuplari_CVD_ekseninde_ve_para_renklerinden_AYRI():
    """Diverging bir skala bu depoda yeşil↔kırmızı OLAMAZ: (a) protan/deutan o ekseni siler,
    (b) yeşil/kırmızı bu panoda PARA demektir. Ölçüm: iki kutup mavi-sarı ekseninde ayrışır
    (b−r işaretleri TERS) ve hiçbiri para jetonlarının RGB'siyle aynı değildir."""
    para = {_rgba(x, t)[:3] for x in ("--green", "--amber", "--red") for t in ("gunduz", "gece")}
    for tema in ("gunduz", "gece"):
        n, p = _rgba("--dv-n2", tema), _rgba("--dv-p2", tema)
        assert n[:3] not in para and p[:3] not in para, \
            f"sapma kutbu bir para rengiyle aynı ({tema}) — renk yalnız parayı anlatır"
        assert (n[2] - n[0]) > 0 > (p[2] - p[0]), \
            f"kutuplar mavi-sarı ekseninde ayrışmıyor ({tema}): {n[:3]} / {p[:3]}"
        for ad in ("--dv-n1", "--dv-p1", "--dv-n2", "--dv-p2"):
            assert _rgba(ad, tema)[3] < 1.0, f"{ad} opak — dolgu alfası olmalı"


def test_isi_matrisi_EKSENLERI_URETICIDEN_dogrulanir():
    """YASA 6'nın aynası: matris `marketview`in ÜRETTİĞİ alanları okur. Bir alan adı üretici
    tarafında değişirse matris sessizce boş kapsama gösterirdi — 'ölçülemedi' ile 'alan yok'
    aynı ekrana düşer ve ikisi AYRI şeydir."""
    olcum = _node("(function(){" + _govde("const KM_OLCUM = [", "let _KM_MOD")
                  + "\nprocess.stdout.write(JSON.stringify([KM_OLCUM, KM_DILIM.map(x=>x[0])]));})();")
    olcumler, dilimler = olcum
    assert len(olcumler) == 7, f"ölçüm ekseni {len(olcumler)} satır — beklenen 7"
    for _bas, alan, _pen in olcumler:
        assert re.search(rf'"{re.escape(alan)}"', MARKETVIEW), \
            f"matrisin okuduğu alan üreticide yok: {alan} (marketview.py)"
    assert dilimler[0] == "TÜM", "ilk sütun taban olmalı — sapma kipi ondan çıkarır"
    for alan in ("position", "armed", "plans_n", "retired", "source"):
        assert f'"{alan}"' in MARKETVIEW, f"dilim alanı üreticide yok: {alan}"


def test_bant_esikleri_SABIT_ve_dogru_dallaniyor():
    """Eşikler veriye göre kaymamalı: yüzdelik dilim kullanmak aynı matrisi iki koşumda iki
    farklı renkle basardı ve 'dün daha iyiydi' okuması ölçülemez olurdu. Dallanma Node'da
    FİİLEN koşturulur (v160 dersi: doğru görünen bir eşik tablosu yanlış dallanabilir)."""
    fn = _govde("const _KM_ESIK = [", "function kmCiz()")
    out = _node("(function(){" + fn +
                "\nprocess.stdout.write(JSON.stringify({"
                "b:[0,49,50,79,80,94,95,100].map(_kmBant),"
                "s:[-40,-20,-19,-5,-4,0,4,5,19,20,40].map(_kmSapmaBant)}));})();")
    assert out["b"] == ["k1", "k1", "k2", "k2", "k3", "k3", "k4", "k4"], out["b"]
    assert out["s"] == ["dn2", "dn2", "dn1", "dn1", "", "", "", "dp1", "dp1", "dp2", "dp2"], out["s"]


def test_bos_dilim_SIFIR_diye_boyanmaz():
    """'Sıfır bir ölçümdür, yokluk değil' — bu panonun en eski kuralı. Payda 0 olan bir
    sütun renklendirilirse operatör onu 'kapsama %0' diye okur."""
    assert 'class="km-cell km-yok"' in P9_DILIM and "dilim yok" in P9_DILIM, \
        "boş dilim için ayrı bir dürüst hâl yok"
    assert "taban" in P9_DILIM, "sapma kipinde taban sütunu kendi kendini 0 diye basıyor olabilir"
    assert P9_DILIM.count("if (!n) return") == 1, "payda kontrolü tek yerde olmalı"


def test_matris_CSP_uyumlu_ve_kart_Veri_Sagliginda():
    """Satır içi işleyici yok (CSP script-src 'self'), eylem izin listesinde kayıtlı, ve kart
    Veri Sağlığı'nın market bölümünde çiziliyor — başka bir sayfada olsaydı sayfanın soru
    cümlesine hizmet etmezdi (ADR 'ekrana dök' yasağı)."""
    assert "onclick" not in P9_DILIM, "matris satır içi işleyici taşıyor — CSP kırılır"
    assert '"kmMod"' in _govde("const EYLEMLER = new Set([", "]);"), \
        "kmMod eylem izin listesinde yok — düğme sessizce çalışmaz"
    market = _govde("RENDER.market = async () => {", "\n// Şeridin \"Piyasa\" satırı")
    assert 'id="km-kart"' in market and "kmCiz();" in market, \
        "ısı-matrisi Veri Sağlığı → market bölümünde çizilmiyor"


def test_kontrast_raporu_P9_BOLUMUNU_tasiyor():
    """Yeni bir renk katmanı ölçülmeden giremez. Rapor bayatlarsa v153 kırmızı verir; bu test
    o raporun P9 yüzeyini KAPSADIĞINI ayrıca ölçer."""
    for baslik in ("## 11 · WP-P/P9 jeton turu eki", "### J · kapsama ısı-matrisi (P9)",
                   "| **İ8** |"):
        assert baslik in RAPOR, f"kontrast raporunda eksik bölüm: {baslik}"
    assert "ÇÖZÜLDÜ" in RAPOR, "B1/B6 hükmü rapora işlenmemiş"


# =================================================================================================
# Ç4 · SH_TR / red_nedeni / atr_kaynak — ÖKSÜZ ALAN KALMADI (YASA 6)
# =================================================================================================
def test_SH_TR_broker_kuralini_ceviriyor():
    """Ham durum kodu `.tag`in uppercase'iyle tr-TR'de bozulur (`POSİTİON_EXİSTS`) ve zaten
    operatörün dili değildir."""
    sh = _govde("  const SH_TR = {", "  const shDurum")
    for jeton in ("broker_kurali", "breaker_olculemedi", "data_bad_olculemedi"):
        assert jeton in sh, f"SH_TR'de çevirisi olmayan durum jetonu: {jeton}"


def test_RED_TR_brokerin_URETTIGI_JETON_KUMESINI_tam_kapsar():
    """ÜRETİCİ/TÜKETİCİ PARİTESİ. `red_nedeni` alanının değerleri `broker.py::PaperBroker.fill_entry`in
    `_red(...)` çağrılarıdır. Üretici yeni bir ret sebebi eklerse pano onu HAM basardı ve
    kimse fark etmezdi — o yüzden küme burada karşılaştırılır, beyan edilmez."""
    uretilen = set(re.findall(r'_red\("([a-z_]+)"', BROKER))
    assert uretilen, "broker.py'de _red(...) çağrısı bulunamadı — çıpa kaymış"
    red_tr = _govde("  const RED_TR = {", "  const redNedeni")
    cevrilen = set(re.findall(r"(\w+):", red_tr))
    eksik = uretilen - cevrilen
    assert not eksik, f"broker'ın ürettiği ama panonun çevirmediği ret sebebi: {sorted(eksik)}"


SHADOW = (SRC / "meridian" / "intraday_shadow.py").read_text()


def test_SH_TR_URETICININ_TUM_DURUM_JETONLARINI_kapsar():
    """ÜRETİCİ/TÜKETİCİ PARİTESİ — `status` alanının değer kümesi `_blocking`in dönüşleri +
    `broker_kurali` + `would_submit`tir. Üretici yeni bir kapı eklerse (bu tam olarak
    `breaker_olculemedi`/`data_bad_olculemedi` ile bir kez yaşandı) pano onu HAM basardı."""
    blocking = SHADOW[SHADOW.index("def _blocking("):SHADOW.index("def record(")]
    uretilen = set(re.findall(r'return "([a-z_]+)"', blocking))
    uretilen |= {"would_submit"}
    uretilen |= set(re.findall(r'engel = "([a-z_]+)"', SHADOW))
    sh = _govde("  const SH_TR = {", "  const shDurum")
    cevrilen = set(re.findall(r"(\w+):", sh))
    eksik = uretilen - cevrilen
    assert not eksik, f"üreticinin ürettiği ama SH_TR'de çevirisi olmayan durum: {sorted(eksik)}"
    assert "broker_kurali" in cevrilen and "breaker_olculemedi" in cevrilen


def test_UC_ICRA_GIRDISI_de_OKUNUYOR_ve_kaynaklariyla():
    """Altısı da `intraday_shadow.record` tarafından yazılıyor, `summarize` aynen geçiriyor,
    `/api/diagnostics` servis ediyor — ve panoda TEK okuyucusu yoktu. Öksüz alan = YASA 6.
    Satır düzeyinde bir uç 'tüketiliyor' görünürken alanları öksüz kalabilir; bu test o
    farkı ölçer."""
    satir = _govde("    const icra = [", "  const veRows")
    for alan in ("r.atr", "r.atr_kaynak", "r.pivot", "r.pivot_kaynak",
                 "r.gap_at_submit", "r.gap_at_submit_kaynak", "r.limit"):
        assert alan in satir, f"gölge satırında okunmayan icra alanı: {alan}"
    assert "r.red_nedeni" in _govde("    const icra = [", "  const veRows") or \
        "r.red_nedeni" in _govde("  const shRows = (sh.today", "  const veRows"), \
        "red_nedeni okunmuyor"
    # ÇİFT YÖNLÜ ÇİVİ: üretici gerçekten bu alanları yazıyor mu
    for alan in ('"red_nedeni"', '"atr_kaynak"', '"atr"', '"limit"',
                 '"pivot"', '"pivot_kaynak"', '"gap_at_submit"', '"gap_at_submit_kaynak"'):
        assert alan in SHADOW, f"üretici bu alanı yazmıyor: {alan} — pano olmayanı okuyor"


def test_icra_girdisi_UC_HALI_AYIRIR_ve_cipalar_URETICIYE_civili():
    """Üçlü ayrım (KOPUK / ÖLÇÜLEMEDİ / ölçüldü) üreticinin cümlesinden okunuyor; o cümle
    `_yan_tablo_kaynagi`nin İKİ dalında yazılı. Çıpalar burada üretici kaynağına karşı
    çivilenir — üretici cümlesini değiştirirse pano SESSİZCE yanlış sınıflandırmasın."""
    yan = SHADOW[SHADOW.index("def _yan_tablo_kaynagi("):SHADOW.index("def record(")]
    dilim = _govde("  const _IK_KOPUK =", "  const shRows")
    m = re.search(r'const _IK_KOPUK = "([^"]+)", _IK_OLCULEMEDI = "([^"]+)"', dilim)
    assert m, "üçlü-ayrım çıpaları bulunamadı"
    kopuk, olculemedi = m.group(1), m.group(2)
    assert kopuk in yan, f"KOPUK çıpası üreticide yok: {kopuk!r}"
    assert olculemedi in yan, f"ÖLÇÜLEMEDİ çıpası üreticide yok: {olculemedi!r}"
    # çıpalar birbirini KAPSAMAMALI, yoksa sınıflandırma sıraya bağlı olur
    assert kopuk not in olculemedi and olculemedi not in kopuk
    # ve üreticinin ÜÇÜNCÜ dalı (ölçüldü) iki çıpanın hiçbirini taşımamalı
    ucuncu = yan[yan.rindex("return f"):]
    assert kopuk not in ucuncu and olculemedi not in ucuncu, \
        "ölçülmüş hâlin cümlesi bir çıpa taşıyor — üç hâl ikiye katlanır"


def test_icra_girdisi_UCLU_AYRIMI_NODEDA_dogru_dalliyor():
    """Davranış ölçümü. Kaynakta doğru görünen bir sınıflandırıcının yanlış dallandığı vaka
    bu depoda yaşandı (v160 `_patOK`). `belirsiz()` ve `esc()` sahte kurulur — ölçülen şey
    DAL, biçim değil."""
    dilim = _govde("  const _IK_KOPUK =", "  const shRows")
    out = _node(
        "(function(){const esc=s=>String(s);const trn=(x,d)=>String(x);"
        "const belirsiz=(i,b)=>'['+i+'|'+b+']';\n" + dilim +
        "\nconst K='portfolio.json.entry_law\\'da bu plan için satır YOK — ATR ÖLÇÜLEMEDİ';"
        "const O='portfolio.json.entry_law[p1] var ama `atr` None — x';"
        "const M='portfolio.json.entry_law[p1] — silahlanma anında sabitlendi';"
        "process.stdout.write(JSON.stringify({"
        "durum:[icraDurum(K),icraDurum(O),icraDurum(M),icraDurum(null),icraDurum('')],"
        "kopuk:icraGirdi('ATR',null,K,v=>'X'),"
        "olcumsuz:icraGirdi('gap',null,O,v=>'X'),"
        "olculdu:icraGirdi('gap',false,M,v=>(v?'VAR':'yok')),"
        "yok:icraGirdi('pivot',null,null,v=>'X')}));})();")
    assert out["durum"] == ["kopuk", "olculemedi", "olculdu", "yok", "yok"], out["durum"]
    assert "KABLO KOPUK" in out["kopuk"] and "warn" in out["kopuk"]
    assert "ÖLÇÜLEMEDİ" in out["olcumsuz"] and "mut" in out["olcumsuz"]
    # ölçülmüş `false` "yok" yazar ama ÖLÇÜLEMEDİ demez — üçüncü hâl ikinciye katlanmamalı
    assert out["olculdu"] == "gap yok", out["olculdu"]
    assert out["yok"] == "", "üretici alanı hiç yazmamışsa satıra uydurma girdi eklenmemeli"


def test_icra_girdisi_karti_UC_HALI_EKRANDA_da_ANLATIR():
    """Ö-S3-1 dersi: ikinci kanal KELİMEdir ve kelime bir yerde TANIMLANMALI. Kart, üç hâlin
    ne demek olduğunu ekrandan söylemezse operatör 'KABLO KOPUK' ile 'ÖLÇÜLEMEDİ' farkını
    tahmin eder."""
    s5 = _govde('  const s5 = `<div class="card rise"><h2 class="t">Gölge icra', "  return { s1")
    for kelime in ("ATR", "gap", "pivot", "ÖLÇÜLEMEDİ", "KABLO KOPUK", "entry_law"):
        assert kelime in s5, f"gölge kartı üçlü ayrımı anlatmıyor: {kelime}"


# =================================================================================================
# Ç5 · HERMES SENKRON DURUMU ZAMAN DAMGALI (ders (b))
# =================================================================================================
def _sozlukler(metin: str, cipa: str) -> list[str]:
    """`cipa`dan sonra gelen `{...}` sözlüklerini PARANTEZ DENGESİYLE söker. Regex ile
    `\\{[^}]*\\}` yazmak burada yanlış cevap verir: gövdedeki f-string'ler süslü parantez
    taşıyor ve dilim ilk `}`de kesilirdi — yani test, damgayı GÖREMEDİĞİ için kırmızı verirdi
    (ölçüm aracının kendi arızası, ölçtüğü şeyin değil)."""
    out = []
    for m in re.finditer(re.escape(cipa) + r"\s*\{", metin):
        i, derinlik = m.end() - 1, 0
        for j in range(i, len(metin)):
            if metin[j] == "{":
                derinlik += 1
            elif metin[j] == "}":
                derinlik -= 1
                if derinlik == 0:
                    out.append(metin[i:j + 1])
                    break
    return out


def test_hermes_senkronu_HER_DONUSTE_damga_tasir():
    """Üretici tarafı. Damgasız bir dönüş, panoya 'damga yok' yazdırır — ama o hâl bir
    ÖLÇÜM BOŞLUĞUDUR ve üreticinin bilinen bir zamanı bilinmiyor göstermesi kabul edilemez."""
    fn = HERMES[HERMES.index("def sync_local_agent_gemini"):]
    fn = fn[:fn.index("\nREVIEW_SKILLS")]
    donusler = _sozlukler(fn, "return")
    assert len(donusler) >= 4, f"beklenenden az dönüş noktası ({len(donusler)}) — çıpa kaymış"
    for d in donusler:
        assert "senkron_ts" in d, f"damgasız dönüş: {d[:80]}"


def test_api_ISTISNA_dallari_da_damga_tasir():
    """api.py'nin iki `except` dalı `sync_local_agent_gemini`i hiç çağıramadan sözlük
    kuruyor; damgayı orada atlamak, BİLİNEN bir ölçüm anını bilinmiyor göstermekti."""
    dallar = [d for d in _sozlukler(APIPY, "local_agent =") if '"ok": False' in d]
    assert len(dallar) == 2, f"beklenen iki istisna dalı, bulunan {len(dallar)}"
    for d in dallar:
        assert "senkron_ts" in d, f"api.py istisna dalı damgasız: {d[:80]}"


def test_pano_damgayi_BASAR_ve_yoksa_UYDURMAZ():
    """Okuyan taraf. Damga varsa MUTLAK basılır (göreli süre, sayfa yenilenmeden yaşlanır);
    yoksa 'damga yok' — `Date.now()` basmak ölçülmemiş bir anı ölçülmüş göstermek olurdu."""
    fn = _govde("function _senkronSatiri(name, la) {", "window.clearSecret")
    assert "la.senkron_ts" in fn and "mutlakTs" in fn, "senkron damgası okunmuyor"
    assert "damga yok" in fn, "damgasız hâl için dürüst boşluk cümlesi yok"
    assert "Date.now()" not in fn and "new Date()" not in fn, \
        "pano damgayı KENDİ üretiyor — uydurma yasağı"
    assert _govde("window.clearSecret = async (name) => {", "window.notifyTest").count(
        "_senkronSatiri") == 1, \
        "anahtar SİLİNDİĞİNDE de senkron koşuyor; sonucunun okuyucusu olmalı (YASA 6)"


def test_mutlakTs_AYRISTIRILAMAYAN_damgada_null_doner():
    """Bozuk bir damga 'Invalid Date' diye ekrana basılamaz ve bugüne de yuvarlanamaz."""
    out = _node("(function(){" + _govde("function mutlakTs(ts) {", "function eventsFeed") +
                "\nprocess.stdout.write(JSON.stringify(["
                "mutlakTs(null), mutlakTs(''), mutlakTs('bozuk-damga'),"
                "typeof mutlakTs('2026-07-30T14:55:00Z')]));})();")
    assert out[:3] == [None, None, None], f"bozuk damga null dönmüyor: {out}"
    assert out[3] == "string", "geçerli damga biçimlenmiyor"


# =================================================================================================
# EK · BOŞLUK TARAMASI — BİLİNMEYEN DURUM YEŞİL DOĞAMAZ (WP-D `takvim_yok`)
# =================================================================================================
BARSARCHIVE = (SRC / "meridian" / "barsarchive.py").read_text()


def test_gap_haritasi_URETICININ_TUM_DURUMLARINI_tanir():
    """ÜRETİCİ/TÜKETİCİ PARİTESİ. `gap_scan` `out["durum"]`a yazdığı her adı pano tanımalı;
    tanımadığı ad ÖLÇÜLMÜŞ SONUÇ dalına düşüyordu ve `bosluk_sayisi:0` yüzünden YEŞİL
    'boşluk yok' basıyordu — `takvim_yok` tam olarak böyle doğdu."""
    gs = BARSARCHIVE[BARSARCHIVE.index("def gap_scan("):]
    uretilen = set(re.findall(r'out\["durum"\] = "([a-z_]+)"', gs))
    uretilen |= set(re.findall(r'"durum": "([a-z_]+)"', gs))
    uretilen |= set(re.findall(r'return \("([a-z_]+)"', BARSARCHIVE))     # _seans_araligi dönüşleri
    uretilen -= {"ok"}                                                    # ölçülmüş sonuç dalı
    harita = _govde("const _GAP_DURUM = {", "\nfunction _gapRows")
    tanınan = set(re.findall(r"^\s{2}([a-z_]+):", harita, re.M))
    eksik = uretilen - tanınan
    assert not eksik, f"panonun tanımadığı tarama durumu: {sorted(eksik)} — sahte-sağlıklı doğar"
    assert "takvim_yok" in tanınan and "seans_disi" in tanınan


def test_gapRows_BILINMEYEN_durumu_YESIL_basmaz():
    """Varsayılan hüküm NÖTR olmalı: üreticinin yarın ekleyeceği her yeni hâl, aksi hâlde
    sahte-sağlıklı doğar ve bu hata SESSİZDİR. Davranış Node'da ölçülür."""
    fn = _govde("const _GAP_DURUM = {", "\n// ====")
    out = _node(
        "(function(){const esc=s=>String(s==null?'':s);"
        "const _chip=(t,c)=>'<CHIP '+c+':'+t+'>';const trn=(x,d)=>String(x);\n" + fn +
        "\nprocess.stdout.write(JSON.stringify({"
        "takvim:_gapRows({durum:'takvim_yok',bosluk_sayisi:0,gelen_bar:0,sembol:0}),"
        "yeni:_gapRows({durum:'gelecekte_eklenen_hal',bosluk_sayisi:0,gelen_bar:0,sembol:0}),"
        "seans:_gapRows({durum:'seans_disi'}),"
        "temiz:_gapRows({durum:'ok',bosluk_sayisi:0,gelen_bar:120,sembol:8,pencere:{beklenen_dk:58}}),"
        "bulgu:_gapRows({durum:'ok',bosluk_sayisi:2,gelen_bar:10,sembol:3,pencere:{beklenen_dk:58},bosluklar:[]}),"
        "hic:_gapRows(null)}));})();")
    # ÖLÇÜLMÜŞ DALIN İMZASI aranır (`boşluk yok · N bar / M sembol`), yalın sözcük DEĞİL:
    # `takvim_yok` cümlesi bilerek `"boşluk yok" DEĞİL` diye yazıyor ve yalın arama onu
    # yakalardı — testin kendi yanlış-pozitifi, ölçtüğü şeyin arızası değil.
    for ad in ("takvim", "yeni", "seans"):
        assert 'class="pos"' not in out[ad], f"{ad}: ölçülemeyen hâl YEŞİL basılıyor"
        assert "boşluk yok · " not in out[ad], \
            f"{ad}: ölçülmemiş sessizlik ölçülmüş-temiz dalına düşüyor"
        assert "<CHIP t-vi:" in out[ad], f"{ad}: nötr çip yok — üçüncü durum görünmüyor"
    assert "ÖLÇÜLEMEDİ" in out["takvim"] and "takvim" in out["takvim"]
    assert "HÜKÜM YOK" in out["seans"], "seans dışı 'ölçemedim' demez — ölçülecek şey yoktu"
    assert "ÖLÇÜLEMEDİ" in out["yeni"] and "bilinmeyen" in out["yeni"], \
        "bilinmeyen durum ham adıyla ve nötr basılmıyor"
    # ÖLÇÜLMÜŞ dal DEĞİŞMEDİ: gerçek temizlik hâlâ yeşil, gerçek bulgu hâlâ kırmızı
    assert 'class="pos"' in out["temiz"] and "boşluk yok" in out["temiz"]
    assert 'class="neg"' in out["bulgu"] and "2 boşluk" in out["bulgu"]
    assert "hiç koşmadı" in out["hic"]


def test_TEST_KENDINI_KANITLAR_eski_gapRows_YESIL_derdi():
    """Kıramayan bir test süstür. Eski `_gapRows` bilinmeyen durumu ölçülmüş sayıyordu; aynı
    girdi eski dalda YEŞİL 'boşluk yok' üretir ve bu burada yeniden kurulur."""
    eski = ("function _gapRowsEski(g,_GAP_DURUM){if(!g)return 'yok';"
            "const not=_GAP_DURUM[g.durum];if(not)return not;"
            "const n=g.bosluk_sayisi??0;"
            "return '<b class=\"'+(n?'neg':'pos')+'\">'+(n?n+' boşluk':'boşluk yok')+'</b>';}")
    out = _node("(function(){" + eski +
                "\nprocess.stdout.write(JSON.stringify("
                "_gapRowsEski({durum:'takvim_yok',bosluk_sayisi:0},{seans_disi:'x'})));})();")
    assert 'class="pos"' in out and "boşluk yok" in out, \
        "eski davranış yeniden üretilemedi — bu test hiçbir şey ölçmüyor demektir"


# =================================================================================================
# NODE --check — dağıtılan her yüzey ayrıştırılabilir olmalı
# =================================================================================================
def test_node_check_TUM_web_yuzeyleri():
    """Bu tur beş dosyaya da dokunmadı ama ikisini (app.js) ağır düzenledi. Ayrıştırılamayan
    bir dosya CSP'den önce gelir: sayfa hiç açılmaz."""
    if not NODE:
        pytest.skip("node bulunamadı — ÖLÇÜLMEDİ")
    for ad in sorted(p.name for p in WEB.glob("*.js")):
        r = subprocess.run([NODE, "--check", str(WEB / ad)], capture_output=True, text=True)
        assert r.returncode == 0, f"{ad} ayrıştırılamadı:\n{r.stderr}"


def test_TEST_KENDINI_KANITLAR_eski_dunya_kirmizi_verirdi():
    """Kıramayan bir test yeşil veren bir süstür. Eski dünyanın iki jetonu (tx3 = tx2,
    violet = accent) bu dosyanın ölçülerini AÇIKÇA devirir; ölçüt burada yeniden kurulur."""
    eski = {"tx3": "#585450", "tx2": "#585450", "violet": "#050505", "accent": "#050505"}
    assert eski["tx3"] == eski["tx2"] and eski["violet"] == eski["accent"]
    # `violet` adı 2026-08-24'te DÜŞTÜ; B6'nın bugünkü karşılığı seri üçlüsünün
    # birbirinin kopyası OLMAMASIDIR ve o aşağıda ölçülüyor.
    # aynı ölçü bugünkü kaynakta AYRIŞMIŞ olmalı — yoksa test hiçbir şey ölçmüyor demektir
    assert ROOT["tx3"] != ROOT["tx2"]
    assert len({ROOT["sapphire"], ROOT["blue"], ROOT["sky"]}) == 3, "seri üçlüsü kopyalanmış (B6)"

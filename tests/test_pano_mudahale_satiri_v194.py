"""v194 — MÜDAHALE BÖLÜMÜ: ŞABLON İÇİNDE TERS TIRNAK + SATIR-DÜZEYİ YALITIM.

CANLI ARIZA (2026-08-06, operatör ekran görüntüsü). Kilitler & Yapılandırma sayfasında müdahale
bölümü tamamen düştü:

    BÖLÜM YÜKLENEMEDİ — TypeError: undefined is not an object (evaluating
    '<div class="kol-satir"> … <!-- TEHLİKE İŞARETİ SATIR İÇİ, YENİ SINIF DEĞİL: `.dlbtn')
    "bu blok mudahale verisini okuyamadı"

KÖK NEDEN VERİ DEĞİLDİ, ŞABLON KAÇIŞIYDI. `RENDER.mudahale` içindeki `kol()` şablon değişmezinin
İÇİNE bir HTML yorumu yazılmıştı ve o yorum bir sınıf adını TERS TIRNAK içinde anıyordu
(".dlbtn.tehlike"). Ters tırnak şablon değişmezini KAPATIR: ardından gelen `.dlbtn.tehlike` bir üye
erişimine, onu izleyen ikinci ters tırnak da ETİKETLİ ŞABLON (tagged template) çağrısına dönüşür.
"<metin>".dlbtn `undefined` olduğu için `.tehlike` okuması çalışma zamanında patlar. Sözdizimi
GEÇERLİDİR — `node --check` bu dosyayı sorunsuz geçiriyordu; kusur ANLAMDAYDI. Bu, bu deponun
"kurulu ≠ çalışır" kusur sınıfının şablon-tarafı hâli.

İKİNCİ BULGU — MERTEBE. Bölüm çerçevesi (`alanSayfasi`) doğru davrandı: hatayı sayfadan bölüme
küçülttü. Ama müdahale bölümünün TEK satır üreticisi patladığı için dört kolun DÖRDÜ birden
ekrandan silindi — HALT ve FLATTEN dahil. Panonun en yüksek bahisli düğmelerinin bir çizim
kusuruyla görünmez olması, çerçevenin bir mertebe fazla büyük olmasındandır. `satirKoru()` o
eksik mertebeyi ekler: bozuk satır dürüst bir "ÖLÇÜLEMEDİ" satırına döner, KALANLAR çizilir.

Testler hem KAYNAĞA hem DAVRANIŞA bakar (repo deseni: v139/v160/v171). Şablon dilimleri Node'da
FİİLEN koşturulur — kaynakta doğru görünen bir şablonun çalışma zamanında patladığı vakanın ta
kendisi bu dosyanın konusu, yani yalnız dizgi aramak bu arızayı bir daha yakalamazdı.
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

NODE = shutil.which("node")

# Yorumsuz gövde (v154/v155/v156/v160/v171 deseni): bir kuralın GEREKÇESİNİ anlatan yorum, o
# kuralın ihlali sanılmamalı. Bu turda bu ayrım ZORUNLU — düzeltmenin kendisi, kaldırdığı hatalı
# deseni (ters tırnaklı sınıf adı) yorumda ANLATIYOR.
KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))


def _blok(bas: str, bitti) -> str:
    """`bas` ile başlayan satırdan, `bitti(satır)` doğru olana kadar olan kaynak dilimi."""
    i = APPJS.index(bas)
    parcalar = []
    for ln in APPJS[i:].splitlines(keepends=True):
        parcalar.append(ln)
        if len(parcalar) > 1 and bitti(ln):
            return "".join(parcalar)
        if len(parcalar) == 1 and bitti(ln):
            return "".join(parcalar)
    raise AssertionError(f"kapanış bulunamadı: {bas}")


SATIR_KORU_SRC = _blok("function satirKoru(alan, uret) {",
                       lambda ln: ln.rstrip("\n") == "}")
KOL_SRC = _blok("const kol = (no, ad, ne, durum, sinif, eylem, etiket, tehlike) =>",
                lambda ln: ln.rstrip().endswith("</div>`;"))


# ---------------- 1) KÖK NEDEN: ŞABLON İÇİNDE TERS TIRNAK ----------------
def test_html_yorumlari_ters_tirnak_TASIMAZ():
    """SINIF-DÜZEYİ ÇİVİ. Bir `.js` dosyasında `<!-- … -->` ancak bir ŞABLON DEĞİŞMEZİNİN içinde
    bulunabilir — yani oradaki her ters tırnak, şablonu erkenden kapatan bir mayındır. Kural tek
    bir satır için değil, dosyanın tamamı ve tüm web betikleri için konur: aynı kusur bir sonraki
    sefer başka bir bölümde doğardı ve yine `node --check`ten geçerdi."""
    ihlaller = []
    for f in sorted(WEB.glob("*.js")):
        s = f.read_text()
        for m in re.finditer(r"<!--.*?-->", s, re.S):
            if "`" in m.group(0):
                satir = s[:m.start()].count("\n") + 1
                ihlaller.append(f"{f.name}:{satir}: {m.group(0)[:90]!r}")
    assert not ihlaller, (
        "Şablon değişmezi içindeki HTML yorumunda TERS TIRNAK var — şablonu kapatır ve etiketli "
        "şablon çağrısına dönüşür (2026-08-06 canlı arızası):\n" + "\n".join(ihlaller))


def test_kol_sablonunda_hic_html_yorumu_yok():
    """Arızanın doğduğu şablon TEMİZ: gerekçe metni şablonun DIŞINA, JS yorumuna taşındı.
    HTML yorumu ayrıca her çizimde istemciye boşuna bayt gönderiyordu."""
    assert "<!--" not in KOL_SRC, "kol() şablonuna yine HTML yorumu girmiş"
    govde = KOL_SRC[KOL_SRC.index("=> `") + 4:KOL_SRC.rindex("`")]   # açan/kapayan hariç
    assert "`" not in govde, "kol() şablonunun gövdesinde ters tırnak var"


def test_gerekce_kaynakta_DURUYOR_ama_sablonun_disinda():
    """YASA 6 / repo deseni: kaldırılan hatalı desenin NEDEN hatalı olduğu kaynakta kalır. Aksi
    hâlde bir sonraki tur aynı HTML yorumunu 'daha okunaklı' diye geri koyar."""
    assert "tagged template" in APPJS, "etiketli-şablon tuzağının açıklaması kaynaktan düşmüş"
    assert "şablon değişmezinin içine ters tırnak YAZILMAZ" in APPJS


@pytest.mark.skipif(NODE is None, reason="node yok")
def test_node_check_gecer():
    """Sözdizimi kapısı — arızayı YAKALAMAZ (o yüzden tek başına yeterli değildir) ama düzeltmenin
    yeni bir sözdizimi kusuru getirmediğini söyler."""
    r = subprocess.run([NODE, "--check", str(WEB / "app.js")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


# ---------------- 2) DAVRANIŞ: ŞABLON GERÇEKTEN KOŞUYOR ----------------
_HARNESS = """
const esc = s => String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const _hata = [];
const console = { error: (...a) => _hata.push(a.map(String).join(" ")) };
%(satirKoru)s
%(kol)s
const ham = kol("Kademe 1", "Soft Halt", "ne", "<span>serbest</span>", "",
                "opSoftHalt", "Soft Halt", false);
const tehlikeli = kol("Kademe 3", "Flatten", "ne", "<span>anlık</span>", "",
                      "opFlatten", "FLATTEN", true);
const korunmus = satirKoru("Kademe 1 · Soft Halt", () =>
  kol("Kademe 1", "Soft Halt", "ne", "<span>serbest</span>", "",
      "opSoftHalt", "Soft Halt", false));
const bozuk = satirKoru("Kademe 4 · Halt Learning", () => {
  const sekilsiz = undefined; return sekilsiz.learn_halted; });
const bosDonus = satirKoru("Kademe 2 · Cancel-Open", () => undefined);
process.stdout.write(JSON.stringify({ ham, tehlikeli, korunmus, bozuk, bosDonus, hata: _hata }));
"""


@pytest.fixture(scope="module")
def kosum():
    if NODE is None:
        pytest.skip("node yok")
    betik = _HARNESS % {"satirKoru": SATIR_KORU_SRC, "kol": KOL_SRC}
    p = subprocess.run([NODE, "-e", betik], capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, f"şablon dilimi Node'da patladı:\n{p.stderr}"
    return json.loads(p.stdout)


def test_kol_satiri_CIZILIYOR_patlamiyor(kosum):
    """ASIL REGRESYON. Arızalı hâlde bu çağrı `TypeError: undefined is not an object` atıyordu ve
    testin kendisi Node'da düşerdi."""
    ham = kosum["ham"]
    assert 'class="kol-satir"' in ham
    assert 'data-act="opSoftHalt"' in ham
    assert "Kademe 1" in ham and "Soft Halt" in ham


def test_tehlike_isareti_satir_ici_kaldi(kosum):
    """Düzeltme görsel sözleşmeyi DEĞİŞTİRMEDİ: FLATTEN hâlâ kırmızı, ve bunu olmayan bir
    `.dlbtn.tehlike` sınıfıyla değil satır içi stille yapıyor."""
    assert "border-color:var(--red)" in kosum["tehlikeli"]
    assert "dlbtn.tehlike" not in kosum["tehlikeli"]
    assert ".tehlike" not in INDEX.split("</style>")[0], "olmayan sınıf CSS'e sonradan doğmuş"


def test_normal_veride_BIREBIR_eski_cikti(kosum):
    """Guard sarmalayıcıdır, çizici değil: sağlam satırda çıktı bayt-bayt aynı kalır."""
    assert kosum["korunmus"] == kosum["ham"]


# ---------------- 3) SATIR-DÜZEYİ YALITIM ----------------
def test_bozuk_satir_DURUST_satira_doner_bolum_ayakta(kosum):
    """Şekilsiz eleman TÜM bölümü düşürmez; kendi satırına düşer ve ne olduğunu SÖYLER."""
    b = kosum["bozuk"]
    assert 'class="kol-satir"' in b, "bozuk satır listenin dışına düşmüş"
    assert "ÖLÇÜLEMEDİ" in b
    assert "veri-şekli beklenmedik (alan: Kademe 4 · Halt Learning)" in b


def test_bos_donus_de_sekil_kusurudur(kosum):
    """`innerHTML`e "undefined" yazmak sessizce bozuk bir satır çizmek olurdu — ekranda durur,
    hiçbir şey söylemez."""
    assert "ÖLÇÜLEMEDİ" in kosum["bosDonus"]
    assert "undefined" not in kosum["bosDonus"].replace("(reading", "")


def test_bozuk_satir_DURUM_UYDURMAZ(kosum):
    """UYDURMA YASAĞI. Bir kolun hâli ölçülemediyse guard "serbest"/"ÇEKİLİ" YAZMAZ — fail-closed
    bir kolun hâlini uydurmak operatöre olmayan bir güvence vermek olurdu (None ≠ 0)."""
    b = kosum["bozuk"]
    for uydurma in ("serbest", "ÇEKİLİ", "kapalı", "sağlıklı"):
        assert uydurma not in b, f"guard ölçmediği bir hâli yazıyor: {uydurma}"
    # Bozuk satır TIKLANABİLİR BİR KOL SUNMAZ: hâli bilinmeyen bir kola düğme koymak, ne olacağı
    # bilinmeyen bir eylemi davet etmek olurdu.
    assert "<button" not in b


def test_yutma_YOK_yasa4(kosum):
    """YASA 4 — sessiz yutma yasağı. Hata satırın gövdesine yazılır VE konsola düşer."""
    assert len(kosum["hata"]) == 2, kosum["hata"]
    assert all(h.startswith("satır çizilemedi:") for h in kosum["hata"])


def test_guard_YENI_SINIF_ACMAZ():
    """Olmayan bir sınıf yazmak, ileride "neden çizilmiyor?" diye aranacak bir hayalet bırakır.
    Guard yalnız index.html'de KURALI OLAN sınıfları kullanır."""
    CSS = INDEX[INDEX.index("<style>"):INDEX.index("</style>")]
    for sinif in re.findall(r'class="([^"$]+)"', SATIR_KORU_SRC):
        for ad in sinif.split():
            assert f".{ad}" in CSS, f"guard kuralı olmayan bir sınıf yazıyor: .{ad}"


# ---------------- 4) BÖLÜM GUARD'I FİİLEN KULLANIYOR ----------------
def test_dort_kademenin_DORDU_de_sarmalanmis():
    """Guard'ın var olması yetmez — kullanılması gerekir ("kurulu ≠ çalışır"). Sarmalanmamış tek
    bir satır, arızanın eski hâlini geri getirirdi."""
    mud = APPJS[APPJS.index("RENDER.mudahale = async () => {"):APPJS.index("function _bellSVG(h) {")]
    for kademe in ("Kademe 1 · Soft Halt", "Kademe 2 · Cancel-Open",
                   "Kademe 3 · Flatten", "Kademe 4 · Halt Learning"):
        assert f'satirKoru("{kademe}", () =>' in mud, f"{kademe} guard'sız çiziliyor"
    assert mud.count("satirKoru(") == 4
    # Guard TEMBEL çağrılır: `satirKoru("x", kol(...))` yazılsaydı satır guard'a GİRMEDEN
    # değerlenir ve koruma hiçbir şey yapmazdı.
    assert "satirKoru(" not in re.sub(r'satirKoru\("[^"]+", \(\) =>', "", mud)


def test_guard_bolum_cercevesinin_KUCUK_KARDESI_olarak_belgelenmis():
    """İki mertebe (sayfa→bölüm, bölüm→satır) tek yerde okunabilir olmalı; yoksa bir sonraki tur
    üçüncü bir kap icat eder."""
    assert "function satirKoru(alan, uret) {" in APPJS
    assert "SATIR-DÜZEYİ YALITIM" in APPJS
    # Bölüm çerçevesi YERİNDE DURUYOR — satır guard'ı onun yerine geçmez, altına girer.
    assert 'Bölüm yüklenemedi' in APPJS

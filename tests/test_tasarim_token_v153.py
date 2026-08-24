"""v153 — UIUX S1-T1/T2: DTCG jeton eş-kaydı · ham-renk linti · kontrast çivisi.

ÖLÇÜLEN KUSUR SINIFI (tek ve yeni): **jeton katmanının SESSİZCE ayrışması.**
Bu deponun kayıtlı emsali `--nav-bg`dir: renk taşıyan bir değer bir kuralın içine
sabit yazılmıştı, gece temasında dönmüyordu ve üst bar beyaz kalınca HALT kırmızısı
1.27:1'e düşüyordu — acil durdurma görünmez olmuştu. Arıza gürültüsüzdü: hiçbir test
kırmızı vermedi, çünkü "her renk jetondan gelir" ve "her renk jetonunun iki teması
vardır" kuralları YAZILIYDI ama ÖLÇÜLMÜYORDU.

Bu dosya o iki kuralı ölçer, ve üçüncüsünü ekler:

  Ç1 · EŞ-KAYIT   — meridian/web/tokens.json ile index.html'in iki :root katmanı
                    bire-bir aynı olmalı. tokens.json üretim kaynağı DEĞİL (stack'te
                    bundler yok, dagit.sh'e derleme adımı eklenmedi — UIUX iş emri
                    "strangler" kuralı); bağ derleme değil, bu çividir. Sürüklenme
                    = kırmızı.
  Ç2 · TAM PALET  — bir renk jetonu iki temaya birden girmezse kırmızı. --nav-bg
                    sınıfının kapısı burasıdır.
  Ç3 · HAM RENK   — ALTI yüzeyde jeton dışı renk yok: index.html · landing.html ·
                    workflow.html · app.js · palette.js · theme.js. Allowlist BOŞ ve
                    bu ölçüldü (bkz. IZIN_VERILEN). Kapsam 2026-08-07'de dörtten altıya
                    çıktı; sebebi orada, ölçülmüş bir arıza vakasıyla yazılı.

  Ç4 · KONTRAST   — docs/kontrast-denetimi.md'nin çivi tablosundaki her rakam
                    KAYNAKTAN yeniden hesaplanır. Bir jeton değerlenirse rapor
                    bayatlar ve test bunu söyler; sessizce eskimiş bir denetim
                    raporu, hiç yapılmamış bir denetimden daha kötüdür.

D1 · ÜÇÜNCÜ KATMAN (2026-08-07) — dosyanın SÖZLEŞMESİ değişmedi, MİMARİSİ değişti.
Jeton sistemi hue-adlı tek renk katmanından İKİ katmana taşındı:

    temel  →  tema-bağımsız ölçüler (tipografi, boşluk, yarıçap, süre) — renk YOK
    tema   →  DEĞER katmanı: bir HUE'nun adı (--green / --amber / --red)
    rol    →  ROL katmanı: bir İŞİN adı (--sev-1/2/3, --yon-arti/eksi,
              --mod-kagit/canli/kesif, --olcek-guven) — bileşen kuralları YALNIZ
              bunu okur (kanıt: research/olcumler/renk_rolleri_2026-08-07/).

Bu dosyanın ölçtüğü kusur sınıfı — "jeton katmanının SESSİZCE ayrışması" — üçüncü
katmanla BÜYÜDÜ, küçülmedi: artık iki renk katmanı iki temada birden tutarlı olmak
zorunda. O yüzden aşağıdaki eş-kayıt karşılaştırmaları `tema`ya DEĞİL, `tema + rol`
toplamına bakar; yalnız `tema`ya bakan bir ölçüm 62 rol jeton-kaydını (2×31) hiç
görmezdi ve görmediği şey tam olarak bu dosyanın var olma sebebidir.

Rol katmanının ÖLÇÜM sözleşmesi (kroma sınırları, rol ayrıklığı, emisyon tavanı,
yeni jetonların AA'sı) tests/test_renk_rolleri_v197.py'dedir. Burada ölçülen şey
o mimarinin KAYIT bütünlüğü: tokens.json ↔ CSS eş-kaydı ve alias zincirinin
tek-gerçekliliği.

Testler KAYNAĞA bakar (repo deseni: test_pano_turu_v139, test_pano_sessiz_hat_v151).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
WEB = SRC / "meridian" / "web"
INDEX = (WEB / "index.html").read_text()
# Ç3'ÜN KAPSAMI (2026-08-07). Bu iki yüzey bir yıl boyunca ham-renk lintinin DIŞINDAYDI ve
# maliyeti ölçüldü: `landing.html`in `.btn-f` (birincil eylem düğmesi) ve `.pillc` (sayaç
# rozeti) kurallarında `color:#fff` sabit yazılıydı; gece zemininde `--accent:#d4d0cb`
# üzerinde 1,53:1 ediyordu (docs/BASELINE-2026-08-06.md §B.5 / T1) — yani düğmenin yazısı
# kendi dolgusunda kayboluyordu. Kusur sınıfı --nav-bg'nin BİREBİR aynısı; onu yakalayan lint
# vardı, bu yüzeye BAKMIYORDU. Kapsam boşluğu, ölçümün kendisi kadar sessiz bir arıza sebebidir.
LANDING = (WEB / "landing.html").read_text()
WORKFLOW = (WEB / "workflow.html").read_text()
APPJS = (WEB / "app.js").read_text()
PALETTE = (WEB / "palette.js").read_text()
THEME = (WEB / "theme.js").read_text()
TOKENS = json.loads((WEB / "tokens.json").read_text())
RAPOR = (SRC / "docs" / "kontrast-denetimi.md").read_text()


# =============================== KAYNAK OKUMA ===============================
def _css(kaynak: str) -> str:
    """Bir HTML yüzeyinin YALNIZ CSS'i, yorumlar ayıklanmış. Belge metni kural sanılmasın
    (v139/v151'in aynı kuralı: bu dosyada her karar GEREKÇESİYLE yazılıyor).

    PARAMETRELEŞTİ (2026-08-07): `INDEX` globaline sabitti ve o sabitlik, Ç3'ün kapsamını
    tek yüzeye çivileyen şeydi. Artık kaynak metin argümandır; her yüzey KENDİ metniyle
    çağırır."""
    css = kaynak[kaynak.index("<style>") + 7:kaynak.index("</style>")]
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


# Ç1/Ç2/Ç4 (eş-kayıt · tam palet · kontrast çivisi) YALNIZ index.html'in jeton katmanına
# bakar: tokens.json'ın eş-kaydı odur, öteki iki yüzeyin değil. `CSS` bu yüzden index'e bağlı
# KALIR — Ç3'ün kapsam genişlemesi bu üç ölçümün kapsamını DEĞİŞTİRMEZ, ve karıştırılmamalı.
CSS = _css(INDEX)


def _blok(sel: str) -> str:
    i = CSS.index(sel)
    j = CSS.index("{", i)
    k = CSS.index("}", j)
    return CSS[j + 1:k]


def _jetonlar(blok: str) -> dict:
    return {m.group(1): m.group(2).strip()
            for m in re.finditer(r"--([a-z0-9-]+)\s*:\s*([^;}]+)", blok)}


ROOT = _jetonlar(_blok(":root{"))
GECE_OV = _jetonlar(_blok(':root[data-theme="gece"]'))


def _duz(dugum, yol=()):
    """tokens.json'ı (yol, token) çiftlerine indir. Token = $value taşıyan sözlük."""
    if isinstance(dugum, dict) and "$value" in dugum:
        yield yol, dugum
        return
    if isinstance(dugum, dict):
        for k, v in dugum.items():
            if k.startswith("$"):
                continue
            yield from _duz(v, yol + (k,))


TOKEN_LISTESI = list(_duz(TOKENS))
TOKEN_YOLU = {yol: tk for yol, tk in TOKEN_LISTESI}


def _css_adi(tk) -> str:
    return tk["$extensions"]["org.meridian.css"]["var"]


def _literal(tk) -> str:
    return tk["$extensions"]["org.meridian.css"]["literal"]


def _cozulen(tk) -> str:
    """Rol jetonunun var() zincirinin UCUNDAKİ değer (tokens.json'ın kendi beyanı).
    Değer katmanında böyle bir alan yoktur: orada literal zaten çözülmüş hâldir."""
    return tk["$extensions"]["org.meridian.css"].get("cozulen-deger")


TEMEL = {_css_adi(tk)[2:]: _literal(tk) for yol, tk in TOKEN_LISTESI if yol[0] == "temel"}
GUNDUZ = {_css_adi(tk)[2:]: _literal(tk)
          for yol, tk in TOKEN_LISTESI if yol[:2] == ("tema", "gunduz")}
GECE = {_css_adi(tk)[2:]: _literal(tk)
        for yol, tk in TOKEN_LISTESI if yol[:2] == ("tema", "gece")}
# D1 (2026-08-07) · ROL KATMANI. Ayrı bir sözlük olarak durur, `tema`ya KATILMAZ: iki
# katmanın ÖLÇÜTÜ farklıdır (değer jetonu ham renk literali taşır, rol jetonu çoğunlukla
# bir `var()` alias'ıdır) ve ikisini tek kovaya atmak, "tema katmanında renk olmayan jeton
# yok" ölçümünü sessizce gevşetirdi.
# Rol tarafında jetonun KENDİSİ de tutulur (alias zinciri `cozulen-deger`i okumayı gerektirir);
# ad→literal sözlüğü ondan TÜRETİLİR, ikinci bir kavrayışla yeniden kurulmaz.
ROL_TK_GUNDUZ = {_css_adi(tk)[2:]: tk for yol, tk in TOKEN_LISTESI if yol[:2] == ("rol", "gunduz")}
ROL_TK_GECE = {_css_adi(tk)[2:]: tk for yol, tk in TOKEN_LISTESI if yol[:2] == ("rol", "gece")}
ROL_GUNDUZ = {ad: _literal(tk) for ad, tk in ROL_TK_GUNDUZ.items()}
ROL_GECE = {ad: _literal(tk) for ad, tk in ROL_TK_GECE.items()}

# CSS'in İKİ bloğunun tokens.json'daki KARŞILIĞI. `:root{}` üç katmanın toplamıdır
# (temel + gündüz değer + gündüz rol), gece override'ı İKİ RENK katmanının (temel gece
# bloğunda TEKRARLANMAZ — bkz. test_temel_katman_TEMADAN_BAGIMSIZ). Eş-kayıt ölçümleri
# bu toplamları kullanır; tek bir katmanı unutmak, unutulan katmanın sürüklenmesini
# ölçülmez kılardı ve bu dosyanın ölçtüğü kusur sınıfı tam olarak odur.
GUNDUZ_HEPSI = {**GUNDUZ, **ROL_GUNDUZ}
GECE_HEPSI = {**GECE, **ROL_GECE}

# Rol jetonunun adı bir İŞİN adıdır ve bu önekle taşınır (değer jetonu HİÇBİRİNİ taşımaz).
# "nav" 2026-08-24'te eklendi (ROL 6 · GEZİNME/SEÇİM, KARAR-2026-08-24-B §2). Önek TİRESİZ
# yazılır çünkü rolün kendi adı `--nav`dır; `--nav-2/-t/-h/-bg` onun ailesidir.
# `--nav-bg` (üst bar perdesi) BU TURDA `tema.*.perde`den `rol.*.nav`a TAŞINDI: bir gezinme
# yüzeyidir ve önek kuralı onu değer katmanında bırakırsa iki katman ADIYLA karışırdı.
ROL_ONEK = ("sev-", "yon-", "mod-", "olcek-", "nav")


# =============================== Ç1 · EŞ-KAYIT ===============================
def test_tokens_json_UC_KATMAN_ve_TEK_dosya():
    """Yapı beyanı kaynakta durmalı: bir okuyucu tema temsilini dosyanın kendisinden
    öğrenebilmeli, bir commit mesajından değil."""
    # D1'e kadar iki katman vardı (temel + tema) ve testin adı zaten "ÜÇ KATMAN" diyordu —
    # üçüncüsü `$description`/`$extensions` beyan bloğuydu. D1'den beri üçüncü bir JETON
    # katmanı da var (`rol`) ve o katman bu listede DURMAK ZORUNDA: bir okuyucu dosyanın
    # kaç katmanı olduğunu dosyanın kendisinden öğrenemezse, katmanı sessizce kaldırmak
    # ya da eklemek serbest kalır.
    assert set(TOKENS) >= {"temel", "tema", "rol", "$description", "$extensions"}
    assert set(TOKENS["tema"]) >= {"gunduz", "gece"}
    assert set(TOKENS["rol"]) >= {"gunduz", "gece"}, \
        "rol katmanı zemin başına yazılmamış — bir zeminde tanımsız rol ötekinden MİRAS alınır"
    assert len(TOKENS["rol"].get("$description", "")) >= 200, \
        "rol katmanı NE OLDUĞUNU söylemeden kurulmuş — iki katmanlı sistemin gerekçesi kaynakta durmalı"
    beyan = TOKENS["$extensions"]["org.meridian"]
    assert "tema-temsili" in beyan and len(beyan["tema-temsili"]) >= 200, \
        "tema temsili BEYAN EDİLMEDEN kurulmuş — DTCG'nin tema yapısı yok, seçim gerekçe ister"
    assert beyan["uretim-yolu"].startswith("eş-doğrulama"), \
        "üretim yolu değişmişse (build adımı) bu testin sözleşmesi de değişmeli"


def test_her_CSS_jetonu_tokens_jsonda_BIRE_BIR():
    """Sürüklenmenin birinci yönü: CSS'te olup jetonda olmayan.

    D1'den beri `:root{}` ÜÇ katmanın toplamıdır; karşılaştırma da öyle olmak zorunda.
    Yalnız `temel|tema`ya bakan bir ölçüm 31 rol jetonunu "kayıtsız" ilan ederdi (yanlış
    kırmızı), ya da — daha kötüsü — o kayıtları hiç açmadan yeşil verirdi."""
    css_hepsi = set(ROOT)
    json_hepsi = set(TEMEL) | set(GUNDUZ_HEPSI)
    eksik = css_hepsi - json_hepsi
    assert not eksik, f"CSS :root'ta olup tokens.json'da olmayan jeton: {sorted(eksik)}"
    for ad, deger in ROOT.items():
        kayit = TEMEL.get(ad, GUNDUZ_HEPSI.get(ad))
        assert kayit == deger, \
            f"--{ad}: CSS {deger!r} ↔ tokens.json {kayit!r} — jeton katmanı ayrışmış"


def test_gece_blogu_BIRE_BIR():
    """Aynı ölçüm gece bloğu için. Gece override'ı İKİ renk katmanı taşır (değer + rol):
    `--sev-1:var(--red)` satırı gece bloğunda da AYRICA yazılıdır, çünkü bir zeminde
    tanımsız kalan rol jetonu ötekinden miras alınır — kural çalışır ama YANLIŞ zeminin
    rengiyle. Kayıt tarafında bunun karşılığı `rol.gece`dir ve burada ölçülür."""
    for ad, deger in GECE_OV.items():
        assert GECE_HEPSI.get(ad) == deger, \
            f"--{ad} (gece): CSS {deger!r} ↔ tokens.json {GECE_HEPSI.get(ad)!r}"


def test_tokens_jsonda_CSSte_OLMAYAN_jeton_YOK():
    """Sürüklenmenin ikinci yönü: silinmiş bir jetonun kayıtta hayalet kalması.
    Bu, kaldırılmış bir kararı hâlâ yürürlükteymiş gibi göstermek olurdu.

    D1 BU YÖNÜ FİİLEN KULLANDI: `--pm-pos`/`--pm-neg` tokens.json'da duran ama CSS'te
    karşılığı OLMAYAN iki hayalet kayıttı (matris hücre zemini artık --yon-*-zemin).
    Ölçüm rol katmanını da kapsamazsa, bir sonraki hayalet 31 jetonluk bir katmanın
    içinde saklanabilir."""
    fazla = (set(TEMEL) | set(GUNDUZ_HEPSI)) - set(ROOT)
    assert not fazla, f"tokens.json'da olup CSS'te olmayan jeton: {sorted(fazla)}"
    fazla_gece = set(GECE_HEPSI) - set(GECE_OV)
    assert not fazla_gece, f"gece katmanında karşılığı olmayan jeton: {sorted(fazla_gece)}"


def test_temel_katman_TEMADAN_BAGIMSIZ():
    """`temel`e konan bir jeton gece bloğunda override EDİLEMEZ; edilirse yeri yanlış
    ve tema sessizce yarım çalışır."""
    kacak = set(TEMEL) & set(GECE_OV)
    assert not kacak, f"`temel`de duran ama gece bloğunda override edilen jeton: {sorted(kacak)}"


# =============================== Ç2 · TAM PALET ===============================
def test_gece_TAM_palet_hicbir_renk_jetonu_YARIM_KALMAZ():
    """--nav-bg ARIZASININ KAPISI. O jeton bir kuralın içinde sabit rgba idi, gece
    dönmüyordu ve üst barda HALT kırmızısı 1.27:1'e düşüyordu. Kural: renk taşıyan
    her jeton İKİ temaya birden girer. Eksikse burada durur.

    D1 SONRASI KURAL AYNI, KAPSAMI İKİ KATLI: hem DEĞER katmanı (--green) hem ROL
    katmanı (--sev-3) iki temaya birden girer. Rol jetonunun çoğu bir alias'tır ama
    alias'ın KENDİSİ zemin başına yazılır — tek zeminde tanımlı bir rol, ötekinde
    sessizce miras alınır ve kural yanlış zeminin rengiyle çalışır. Yani --nav-bg
    arıza sınıfının rol katmanındaki birebir aynası. İDDİA KORUNDU, yalnız hangi
    katmanın nereye karşılık geldiği düzeltildi."""
    assert set(GUNDUZ) == set(GECE), \
        f"DEĞER (tema) katmanları ayrışıyor: {sorted(set(GUNDUZ) ^ set(GECE))}"
    assert set(ROL_GUNDUZ) == set(ROL_GECE), \
        f"ROL katmanları ayrışıyor: {sorted(set(ROL_GUNDUZ) ^ set(ROL_GECE))}"
    assert set(GUNDUZ_HEPSI) == set(GECE_OV), \
        ("gündüz renk katmanları (değer+rol) ile CSS'in gece override kümesi ayrışıyor "
         f"(GECE bloğunda karşılığı olmayan renk jetonu): {sorted(set(GUNDUZ_HEPSI) ^ set(GECE_OV))}")
    # ÖLÇÜLMÜŞ SAYIM — hangi katman kaç jeton getiriyor, beyan kaynakta dursun:
    #   temel  23  tema-bağımsız ölçüler (tipografi/boşluk/yarıçap/süre/ease) — D1'de DEĞİŞMEDİ.
    #   tema   43  DEĞER katmanı, zemin başına. 36 → 45 (WP-P/P9, 2026-08-02: --band-2 nitel
    #              bant orta basamağı + --kap-1..4 sequential kapsama rampası + --dv-n2/n1/p1/p2
    #              CVD-güvenli diverging skalası) → 43 (D1, 2026-08-07: --pm-pos/--pm-neg
    #              HAYALET kayıtlardı — tokens.json'da vardı, CSS'te yoktu; matrisin hücre
    #              zeminini artık --yon-arti-zemin/--yon-eksi-zemin taşıyor ve o ikisi ROL
    #              katmanında doğdu, yani sayı `tema`dan `rol`e TAŞINDI, kaybolmadı).
    #   rol    31  D1'in yeni katmanı, zemin başına ve İKİ ZEMİNDE AYNI AD KÜMESİ:
    #              şiddet 11 (--sev-1/2/3 · -t/-h · --sev-2-h2 · --sev-3-damga)
    #            + yön     8 (--yon-arti/eksi · -t/-h/-zemin)
    #            + mod     9 (--mod-kagit/canli/kesif · -t/-h)
    #            + ölçek   3 (--olcek-guven · -t/-h)
    # CSS :root  = 23 temel + 43 değer + 31 rol = 97   (68 → 97)
    # CSS gece   =            43 değer + 31 rol = 74   (45 → 74; `temel` gece bloğunda YOK)
    # 2026-08-24 · DUB DÖNÜŞÜMÜ (KARAR-2026-08-24-B). Sayım değişti ve ayrışımı şu:
    #   temel 23 → 33: +4 yarıçap (--r-input/--r-btn/--r-lg/--r-tag, Dub ölçeği devralındı)
    #                  +6 tip rampası (--t-cap/--t-body/--t-lg/--t-sub/--t-h/--t-num).
    #                  Rampa 2026-08-24'te JETONLANDI: o güne kadar tek jeton --t-num idi,
    #                  geri kalan boylar kural gövdelerinde sabit px duruyordu — iki kaynak,
    #                  ayrışabilir iki gerçek. Ölçülen rampa 11/14/17/20/24/30 (Ö6).
    #   tema  43 → 44: +2 gölge (--sh-btn/--sh-ring, Dub'ın iki gölgesi; renk taşıdıkları
    #                  için `temel`de DURAMAZLAR) −1 (--nav-bg `rol.nav`a taşındı)
    #   rol   31 → 36: +5 ROL 6 (--nav/--nav-2/--nav-t/--nav-h/--nav-bg)
    assert (len(TEMEL) == 33 and len(GUNDUZ) == 44 and len(ROL_GUNDUZ) == 36
            and len(ROOT) == 113 and len(GECE_OV) == 80), \
        (f"jeton sayımı değişmiş: temel {len(TEMEL)} · değer {len(GUNDUZ)} · rol "
         f"{len(ROL_GUNDUZ)} · :root {len(ROOT)} · gece {len(GECE_OV)}")


def test_renk_jetonlarinin_HEPSI_renk_TEMEL_jetonlarin_HICBIRI_degil():
    """Katman ayrımı ANLAMLI olmalı: `tema` altında renk olmayan bir şey varsa ya da
    `temel` altında renk varsa, bölünme keyfîdir ve bir sonraki turda çöker.

    D1 SONRASI BÖLÜNME ÜÇ YÖNLÜ ve her yönün kendi ölçütü var — çünkü katmanları AYIRAN
    şey artık yalnız "renk mi değil mi" değil, ADIN NE SÖYLEDİĞİ:

      temel — renk YOK (ölçü/süre/tipografi).
      tema  — hepsi ham renk literali, ve adı bir HUE'nun adıdır: rol öneki TAŞIMAZ.
      rol   — adı bir İŞİN adıdır: --sev-/--yon-/--mod-/--olcek- öneki ZORUNLU, ve
              ekranda bir renge çözülür (literali ya doğrudan renk ya bir var() zinciri).

    Rol jetonlarını `tema` ölçütüyle sınamak YANLIŞ olurdu: `--sev-1:var(--red)` bir renk
    LİTERALİ değildir ama ekranda bir renktir. Bu yüzden rol tarafında ölçüt literale
    değil ÇÖZÜLEN DEĞERE bakar (zincirin CSS'te gerçekten kapandığı ayrıca ölçülür:
    test_ROL_alias_zinciri_TEK_gercek_soyler)."""
    renk = re.compile(r"#[0-9a-fA-F]{6}|rgba?\(")
    for ad, lit in GUNDUZ.items():
        assert renk.match(lit), f"`tema` katmanında renk olmayan jeton: --{ad} = {lit!r}"
    for ad, lit in TEMEL.items():
        assert not renk.match(lit), f"`temel` katmanında renk jetonu: --{ad} = {lit!r}"
    # ROL KATMANI — çözülen değer bir renk (ya da `transparent`: "bu rol kroma HARCAMAZ"
    # bilinçli bir hükümdür, --mod-kagit'in tinti; ölçülemeyen bir boşluk değil).
    for tablo, zemin in ((ROL_TK_GUNDUZ, "gündüz"), (ROL_TK_GECE, "gece")):
        for ad, tk in tablo.items():
            coz = _cozulen(tk)
            assert coz is not None, f"--{ad} ({zemin}): rol jetonu çözülen değerini BEYAN ETMİYOR"
            assert renk.match(coz) or coz == "transparent", \
                f"`rol` katmanında renge çözülmeyen jeton: --{ad} ({zemin}) = {coz!r}"
    # ADLANDIRMA — katmanı ayıran ikinci kanal. Rol öneksiz bir rol jetonu ya da rol önekli
    # bir değer jetonu, iki katmanı ADIYLA birbirine karıştırırdı; o karışma sessizdir,
    # çünkü ikisi de "çalışan" bir renk üretir.
    for ad in ROL_GUNDUZ:
        assert ad.startswith(ROL_ONEK), f"rol jetonunun adı bir İŞİN adı değil: --{ad}"
    for ad in set(GUNDUZ) | set(TEMEL):
        assert not ad.startswith(ROL_ONEK), f"değer/ölçü jetonu rol adı taşıyor: --{ad}"
    # Ve ad kümeleri AYRIK: aynı ad iki katmanda dursaydı eş-kayıt karşılaştırmalarındaki
    # `{**a, **b}` birini sessizce yutar, yutulan kaydın sürüklenmesi hiç ölçülmezdi.
    assert not (set(TEMEL) & set(GUNDUZ)), f"temel↔tema ad çakışması: {sorted(set(TEMEL) & set(GUNDUZ))}"
    assert not (set(TEMEL) & set(ROL_GUNDUZ)), f"temel↔rol ad çakışması: {sorted(set(TEMEL) & set(ROL_GUNDUZ))}"
    assert not (set(GUNDUZ) & set(ROL_GUNDUZ)), f"tema↔rol ad çakışması: {sorted(set(GUNDUZ) & set(ROL_GUNDUZ))}"


# =============================== Ç1b · DTCG ŞEMASI ===============================
IZINLI_ANAHTAR = {"$value", "$type", "$description", "$deprecated", "$extensions",
                  "$extends", "$ref"}
IZINLI_TIP = {"color", "dimension", "duration", "cubicBezier", "fontFamily",
              "fontWeight", "number", "shadow", "strokeStyle", "border",
              "transition", "gradient", "typography"}


def _gez(dugum, yol=(), miras=None):
    if not isinstance(dugum, dict):
        return
    tip = dugum.get("$type", miras)
    if "$value" in dugum:
        yield yol, dugum, tip
        return
    for k, v in dugum.items():
        if k.startswith("$"):
            assert k in IZINLI_ANAHTAR, f"{'.'.join(yol)}: bilinmeyen $ anahtarı {k}"
            continue
        assert not k.startswith("$"), k
        assert not re.search(r"[{}.]", k), f"DTCG ad kuralı: {k!r} `{{`/`}}`/`.` taşıyamaz"
        yield from _gez(v, yol + (k,), tip)


def test_DTCG_semasi_gecerli():
    """Biçim doğruluğu SONRADAN kanıtlanmaz: dosya DTCG diye adlandırıldıysa DTCG
    kurallarını burada geçmek zorundadır."""
    sayac = 0
    for yol, tk, tip in _gez(TOKENS):
        sayac += 1
        p = ".".join(yol)
        for k in tk:
            assert k in IZINLI_ANAHTAR, f"{p}: bilinmeyen $ anahtarı {k}"
        assert tip is None or tip in IZINLI_TIP, f"{p}: bilinmeyen $type {tip!r}"
        assert "$description" in tk and tk["$description"].strip(), \
            f"{p}: açıklamasız jeton — okuyucusuz yazım yok (YASA 6)"
        assert "$extensions" in tk and "org.meridian.css" in tk["$extensions"], \
            f"{p}: CSS eş-kaydı yok — eş-doğrulama yolu bu alan olmadan kurulamaz"
    # 113 → 171 (D1, 2026-08-07) → 193 (Dub dönüşümü + tip rampası jetonlaması, 2026-08-24). Ayrışım yukarıdaki tam-palet ölçümüyle AYNI ve orada
    # gerekçelendirildi: 23 temel (tema-bağımsız) + 2×43 değer (tema, zemin başına) +
    # 2×31 rol (D1'in üçüncü katmanı, zemin başına). Sayı bir BÜTÇE değil bir MUHASEBEdir:
    # burada tutmayan bir toplam, DTCG ağacına eş-kayıtsız bir dal eklendiğini söyler.
    assert sayac == 33 + 2 * 44 + 2 * 36, \
        f"jeton sayımı {sayac} (beklenen 193 = 33 temel + 2×44 değer + 2×36 rol)"


def test_takma_adlar_COZULUYOR():
    """`{a.b.c}` biçimindeki DTCG takma adı var olmayan bir yolu gösteremez —
    gösterirse dosya kendi içinde tutarsızdır ve hiçbir araç onu okuyamaz."""
    bulunan = 0
    for yol, tk, _ in _gez(TOKENS):
        v = tk["$value"]
        if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
            hedef = tuple(v[1:-1].split("."))
            assert hedef in TOKEN_YOLU, f"{'.'.join(yol)}: çözülmeyen takma ad {v}"
            bulunan += 1
    assert bulunan >= 2, "CSS'te var(--sans)'a bağlı iki jeton var; takma ad olarak yazılmalıydı"


def _renk_coz(lit):
    m = re.fullmatch(r"#([0-9a-fA-F]{6})", lit)
    if m:
        h = m.group(1)
        return [int(h[i:i + 2], 16) for i in (0, 2, 4)], 1.0
    m = re.fullmatch(r"rgba?\((\d+),(\d+),(\d+),([0-9.]+)\)", lit.replace(" ", ""))
    assert m, f"renk çözülemedi: {lit!r}"
    return [int(m.group(i)) for i in (1, 2, 3)], float(m.group(4))


def _olcu_yaz(o):
    """DTCG dimension -> CSS parçası. Sıfır BİRİMSİZ yazılır (`0`, `0px` değil) çünkü
    CSS'te fiilen öyle duruyor ve eş-kayıt BİREBİR olmak zorunda."""
    return "0" if o["value"] == 0 else f"{o['value']:g}{o['unit']}"


def _renk_yaz(c):
    r, g, b = [int(round(x * 255)) for x in c["components"]]
    if c.get("alpha", 1) == 1:
        return c["hex"]
    return f"rgba({r},{g},{b},{('%.2f' % c['alpha']).lstrip('0')})"


def _golge_serilestir(katmanlar):
    """DTCG shadow -> CSS literali. Ölçüm aracının kendi çivisi aşağıda
    (test_golge_serilestirici_KENDINI_KANITLAR)."""
    return ", ".join(
        " ".join([_renk_yaz(k["color"]), _olcu_yaz(k["offsetX"]), _olcu_yaz(k["offsetY"]),
                  _olcu_yaz(k["blur"]), _olcu_yaz(k["spread"])])
        for k in katmanlar)


def test_golge_serilestirici_KENDINI_KANITLAR():
    """Serileştirici sessizce bozulursa yukarıdaki gölge çivisi yalancı yeşil verir."""
    ornek = [{"color": {"colorSpace": "srgb", "components": [0.0, 0.0, 0.0], "alpha": 0.05},
              "offsetX": {"value": 0, "unit": "px"}, "offsetY": {"value": 1, "unit": "px"},
              "blur": {"value": 2, "unit": "px"}, "spread": {"value": 0, "unit": "px"}}]
    assert _golge_serilestir(ornek) == "rgba(0,0,0,.05) 0 1px 2px 0"


def test_DTCG_degeri_CSS_LITERALINDEN_yeniden_uretilebilir():
    """$value ile literal ayrı ayrı elle güncellenebilir; ayrışırlarsa dosya iki
    farklı gerçeği aynı anda söyler. İkisi arasındaki bağ da ölçülür.

    KAPSAM: bu ölçüm `$type` taşıyan jetonlara bakar — yani `temel` + `tema`. Rol katmanı
    tipsizdir (bir rolün TİPİ yoktur; taşıdığı değerin tipi vardır) ve orada bağ farklı
    kurulur: `literal` bir var() zinciridir, `$value` o zincirin ucudur. O bağ AYRI ve
    aynı sıkılıkta ölçülür — bkz. test_ROL_alias_zinciri_TEK_gercek_soyler. Rol katmanını
    burada sessizce geçmek, 62 jeton kaydını ölçüsüz bırakmak olurdu."""
    for yol, tk, tip in _gez(TOKENS):
        lit, v, p = None, tk["$value"], ".".join(yol)
        lit = tk["$extensions"]["org.meridian.css"]["literal"]
        if tip == "color":
            c, a = _renk_coz(lit)
            assert v["colorSpace"] == "srgb"
            assert v["components"] == [round(x / 255, 6) for x in c], f"{p}: bileşen ayrışmış"
            assert abs(v["alpha"] - a) < 1e-9, f"{p}: alfa ayrışmış"
            if a == 1.0:
                assert v["hex"] == lit.lower(), f"{p}: hex ayrışmış"
            else:
                assert "hex" not in v, \
                    f"{p}: alfa taşıyan jetonda opak `hex` — ekranda var olmayan bir renk beyanı"
        elif tip == "dimension":
            m = re.fullmatch(r"([0-9.]+)(px|rem)", lit)
            assert m and float(v["value"]) == float(m.group(1)) and v["unit"] == m.group(2), p
        elif tip == "duration":
            m = re.fullmatch(r"([0-9.]+)(ms|s)", lit)
            assert m and float(v["value"]) == float(m.group(1)) and v["unit"] == m.group(2), p
        elif tip == "cubicBezier":
            sayilar = [float(x) for x in re.fullmatch(r"cubic-bezier\(([^)]*)\)", lit).group(1).split(",")]
            assert v == sayilar, p
        elif tip == "shadow":
            # KARTLARDA GÖLGE HÂLÂ YOK (`--elev:none`, boş katman listesi) — Omega'nın
            # ölçülmüş kararı Dub dönüşümünde de durur, çünkü Dub da kenar-öncedir.
            # 2026-08-24'te İKİ gölge geldi ve ikisi de KART DIŞI (`--sh-btn` düğme
            # oklüzyonu, `--sh-ring` yardımcı odak halkası). Onlar için bağ, renk
            # jetonlarındakiyle AYNI sıkılıkta ölçülür: katman listesi literale GERİ
            # SERİLEŞTİRİLİR ve birebir eşleşmek zorundadır. Yoksa `$value` ile literal
            # ayrı ayrı elle güncellenebilir ve dosya iki gerçek söylerdi.
            if lit == "none":
                assert v == [], f"{p}: `none` gölgenin katman listesi boş olmalı"
                continue
            assert isinstance(v, list) and v, f"{p}: gölge katman listesi boş"
            assert _golge_serilestir(v) == lit, \
                f"{p}: gölge ayrışmış — kayıt {_golge_serilestir(v)!r}, CSS {lit!r}"
            for katman in v:
                assert set(katman) == {"color", "offsetX", "offsetY", "blur", "spread"}, \
                    f"{p}: DTCG gölge katmanı eksik/fazla alan taşıyor: {sorted(katman)}"


# =========================== Ç1c · ROL ALIAS ZİNCİRİ (D1) ===========================
def _coz_css(deger: str, tablo: dict) -> str:
    """CSS'in `var(--x)` zincirini tabloda yürü — tarayıcının fiilen yaptığı iş budur."""
    d = deger.strip()
    for _ in range(8):
        m = re.fullmatch(r"var\(\s*--([a-z0-9-]+)\s*\)", d)
        if not m:
            return d
        assert m.group(1) in tablo, f"var(--{m.group(1)}) tanımsız — zincir kopuk"
        d = tablo[m.group(1)].strip()
    raise AssertionError(f"var() zinciri kapanmıyor (döngü?): {deger!r}")


def test_ROL_alias_zinciri_TEK_gercek_soyler():
    """Rol katmanının Ç1 ÖLÇÜMÜ. Bir rol jetonu ÜÇ yerde birden konuşur:

        CSS       --sev-1:var(--red)
        literal   "var(--red)"          (aynı ifade, kayıtta)
        $value    "#b3242c"             (o zincirin UCU, kayıtta ayrıca yazılı)

    Üçü elle güncellenebilir. Ayrıştıkları anda dosya aynı jeton hakkında iki farklı
    gerçek söyler ve HİÇBİRİ ekranı yanlış göstermez — yalnız kayıt yalan söyler; yani
    tam olarak bu dosyanın kovaladığı sessiz sürüklenme. Zincir CSS'in KENDİ tablosunda
    yürütülür: `--sev-1` gündüz --red'e, gecede BAŞKA bir --red'e çözülür ve iki zeminin
    ucu farklı olmak ZORUNDADIR (aynı olsaydı tema dönmüyordu demektir)."""
    for tk_tablo, css_tablo, zemin in ((ROL_TK_GUNDUZ, ROOT, "gündüz"),
                                       (ROL_TK_GECE, dict(ROOT, **GECE_OV), "gece")):
        for ad, tk in tk_tablo.items():
            lit, coz = _literal(tk), _cozulen(tk)
            assert _coz_css(lit, css_tablo) == coz, \
                (f"--{ad} ({zemin}): literal {lit!r} CSS'te "
                 f"{_coz_css(lit, css_tablo)!r}'e çözülüyor, kayıt {coz!r} diyor")
            assert tk["$value"] == coz, \
                f"--{ad} ({zemin}): $value {tk['$value']!r} ↔ çözülen değer {coz!r} ayrışmış"
    # TEMA GERÇEKTEN DÖNÜYOR MU: kroma taşıyan her rol jetonunun iki zemindeki ucu farklı
    # olmalı. Aynı olsaydı jeton gece bloğunda YAZILI ama İŞLEVSİZ olurdu — ad kümesi
    # eşitliği testi böyle bir jetonu yakalayamazdı (adı var, değeri dönmüyor).
    ayni = [ad for ad in ROL_TK_GUNDUZ
            if _cozulen(ROL_TK_GUNDUZ[ad]) == _cozulen(ROL_TK_GECE[ad])
            and _cozulen(ROL_TK_GUNDUZ[ad]) != "transparent"]
    assert not ayni, f"rol jetonu iki zeminde AYNI değere çözülüyor (tema dönmüyor): {ayni}"


# =============================== Ç3 · HAM RENK LİNTİ ===============================
# KAPSAM: DÖRT → ALTI YÜZEY (2026-08-07). Kapsam boşluğu bir yıl açıktı ve BEDELİ ÖLÇÜLDÜ —
# landing.html'in `.btn-f`/`.pillc` kurallarındaki `color:#fff` gecede 1,53:1 (§B.5/T1). O iki
# satır 2026-08-07'de `var(--bg2)`ye çevrildi (ölçüldü: gündüz 19,54 · gece 10,45), ama
# DÜZELTME LİNT DEĞİLDİR: aynı satırı yarın tekrar yazan bir el, ölçülmeyen bir yüzeyde yine
# sessiz kalırdı. Kapatılan şey o el değil, o yüzeyin ölçüsüzlüğü.
#
# ALLOWLIST BOŞ VE BU YENİDEN ÖLÇÜLDÜ (2026-08-07, altı yüzeyin tamamı): jeton blokları ve
# yorumlar dışında TEK ham renk çıkmadı — landing.html 0, workflow.html 0, ötekiler 0. Boş bir
# liste bir eksiklik değil bir bulgu: jeton sözleşmesi bugün fiilen %100 tutuyor. Buraya bir
# satır eklemek ≥20 karakter gerekçe yazmayı GEREKTİRİR (YASA 4) — istisna sessizce büyüyemez.
#
# BEYANLI KAPSAM DIŞI (sessiz-yutma işareti, YASA 4). Üç şey bu lintin DIŞINDA kalır ve
# üçü de bilinçlidir; yazılmasaydı, dışarıda kalışları ölçülmemiş bir boşluk olurdu:
#   1) JETON BLOKLARI (`:root{}` + gece override'ı) — jeton TANIMI meşru ham renk taşır;
#      linte girseydi sözleşmenin kendisi ihlal sayılırdı. index.html'in blokları Ç1'de
#      tokens.json'a karşı çivilenir. AMA landing/workflow'unkiler HİÇBİR YERDE ölçülmüyor
#      ve BUGÜN İNDEX'TEN AYRIŞMIŞ DURUMDA (ölçüldü 2026-08-07: gündüzde 13 jeton DEĞER
#      olarak farklı — --card, --card-2, --line-2, --tx3, --nav-bg, --violet …; gecede 2;
#      ayrıca index'in 40 jetonu — rol katmanının tamamı — o iki yüzeyde hiç yok). Bu, tam
#      da bu dosyanın kovaladığı sürüklenme sınıfıdır, yalnız başka bir yüzeyde; landing.html
#      kendi gece bloğunun başında "index.html ile AYNI değer takımı" YAZAR ve bu cümle
#      bugün DOĞRU DEĞİLDİR. Ç3 o bloğu linte sokmaz (sokmamalı) — ama boşluk burada ADIYLA
#      duruyor ki dışlama, sürüklenmeyi aklayan sessiz bir kapı olmasın. Hükmü Rol-1 verir.
#   2) YORUMLAR (`/* */` ve `<!-- -->`) — bkz. `_yorumsuz_html` gerekçesi.
#   3) meridian/web'in kalan üç dosyası: landing.js · workflow.js (ikisi de ölçüldü, ham renk
#      YOK) ve runbook.html (ölçüldü: kural gövdelerinde 9 ham renk — kendi koyu paletini
#      taşıyor, `gece` bloğu ve theme.js bağı YOK, yani jeton sözleşmesine hiç girmemiş bir
#      yüzey). Onu bu linte sokmak bir ölçüm değil bir HÜKÜM olurdu ("runbook jeton
#      sistemine dahildir") ve o hüküm verilmedi. Sayı burada dursun: bulunmamış değil,
#      bulunmuş ve kapsam dışı bırakılmıştır.
IZIN_VERILEN: dict[str, str] = {}

_HEX = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
_FONK = re.compile(r"\b(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch|color)\([^)]*\)")
# `white-space` / `black-box` gibi bileşik sözcükler renk DEĞİL: ad tek başına durmalı.
#
# 2026-08-24 · SOLDAKİ AD DA ÖLÇÜLÜR — ve bu bir gevşetme değil bir DÜZELTME. Desen eskiden
# yalnız iki nokta ÜSTÜNDEN sonrasına bakıyordu (`:\s*red`) ve bu, CSS dışındaki her `ad: deger`
# yapısını renk sanıyordu. Ölçülen vaka: `app.js` Top Views kırılımında
#     { anahtar: "red", ad: "Kapı reddi", satirlar: red, … }
# `red` burada Türkçe "reddi"nin kısaltması olan bir DEĞİŞKEN adıdır; hiçbir piksel boyamaz.
# Yalancı kırmızı, gerçek kırmızıdan daha pahalıdır: bir yıl içinde ya lint kapatılır ya
# allowlist'e `named:red` yazılır — ve o satır ondan sonra GERÇEK ihlalleri de yutardı.
# SIKILIK KORUNDU: renk hâlâ iki noktadan HEMEN SONRA gelmek zorunda (yani `border:1px solid
# red` bugün de yakalanmıyor — eskiden de yakalanmıyordu); eklenen tek kısıt, solundaki adın
# bir RENK ÖZELLİĞİ olması. `test_lint_KENDINI_KANITLAR` her iki yönü de sınar.
_RENK_OZ = r"[a-z-]*(?:color|background|border|outline|fill|stroke|shadow)"
_ADLI = re.compile(
    rf"\b{_RENK_OZ}\s*:\s*(black|white|red|green|blue|gray|grey|orange|yellow|purple|silver)\b")


def _yorumsuz_js(s: str) -> str:
    s = "\n".join(l for l in s.splitlines() if not l.lstrip().startswith("//"))
    return re.sub(r"/\*.*?\*/", "", s, flags=re.S)


def _yorumsuz_html(s: str) -> str:
    """HTML yorumları ayıklanmış belge metni.

    AYIKLAMA ZORUNLUDUR VE BUNUN NEDENİ ÖLÇÜLDÜ (2026-08-07). landing.html'de `#fff`/`#ffffff`
    kaba grep'i ÜÇ yer verir ve üçü de ihlal DEĞİLDİR — ama üçü ÜÇ FARKLI mekanizmayla dışarıda
    kalır ve karıştırılmamaları gerekir:
      · sat. 29  `#ffffff ground` — baştaki DIRECTION CONTRACT (HTML yorumu). Zaten dilim
        sınırının dışında: belge dilimi `</style>`ten BAŞLAR, `<style>` öncesi baş bölge
        hiçbir dilime girmez (index.html'in bir yıldır aldığı muamele; kasıtlı).
      · sat. 112 `--bg:#ffffff` — `:root{}` jeton TANIMI. `_css_govdeleri` bloğu keser.
      · sat. 222-223 — `.btn-f` DÜZELTMESİNİ ANLATAN CSS yorumu ("burada ham `#fff` duruyordu
        … `#ffffff` = 1,53:1"). BUNU YALNIZ YORUM AYIKLAMASI dışarıda tutar. Ayıklama olmasaydı
        arızayı KAYDA GEÇEN cümle arızanın kendisi sayılırdı — gerekçe yazmayı cezalandıran bir
        lint, ve bu depoda gerekçe yazmak zorunludur (YASA 6).
    Bedeli de beyan edilir: yorum içine gizlenmiş bir ham renk GÖRÜNMEZ — ama yorum ekrana
    çizilmez, yani ölçülen kusur sınıfının (ikinci temada sessizce kırılan renk) dışındadır.
    Ayıklamanın İKİ YÖNDE de doğru çalıştığı ölçülür: test_lint_KENDINI_KANITLAR yorum içine
    de, yorumların ARASINA da renk enjekte eder ve yalnız ikincisinin ısırdığını sınar."""
    return re.sub(r"<!--.*?-->", "", s, flags=re.S)


def _css_govdeleri(css: str) -> str:
    """CSS'in YALNIZ bildirim gövdeleri, jeton blokları çıkarılmış.
    Seçiciler dışarıda kalır — yoksa `#gate-pw2-wrap` gibi bir id seçicisi renk sanılır.

    PARAMETRELEŞTİ (2026-08-07): `CSS` globaline (yani index.html'e) sabitti. Kapsamı altı
    yüzeye çıkaran değişikliğin tek yapısal engeli buydu."""
    for sel in (":root{", ':root[data-theme="gece"]'):
        i = css.index(sel)
        j = css.index("{", i)
        k = css.index("}", j)
        css = css[:i] + css[k + 1:]
        assert sel not in css or sel == ":root{", sel
    return "\n".join(m.group(1) for m in re.finditer(r"\{([^{}]*)\}", css))


def _ham_renkler(metin: str) -> list:
    return sorted(set(_HEX.findall(metin)) | set(_FONK.findall(metin)) |
                  {"named:" + a for a in _ADLI.findall(metin)})


# Üç HTML yüzeyi TEK sözlükte durur ki kapsam bir VERİ olsun, koda serpiştirilmiş bir alışkanlık
# değil: yeni bir yüzey eklemek buraya bir satır yazmaktır ve pozitif kontrol (aşağıda) o satırı
# otomatik olarak dişler. Kapsamın kodda dağınık durması, 2026-08-07'ye kadar landing/workflow'un
# unutulmasının mekanik sebebiydi.
HTML_KAYNAK = {
    "index.html": INDEX,
    "landing.html": LANDING,
    "workflow.html": WORKFLOW,
}


def _html_yuzeyleri(ad: str, kaynak: str) -> dict:
    """Bir HTML yüzeyinin İKİ lint dilimi. Dilimler AYRIK ve bu ölçülür:
       · `<style>` içi kural gövdeleri (jeton blokları + yorumlar ayıklanmış)
       · `</style>` sonrası belge gövdesi — satır-içi `style="…"` buradan yakalanır."""
    return {
        f"{ad} <style> (jeton blokları hariç)": _css_govdeleri(_css(kaynak)),
        f"{ad} gövdesi (satır içi stil)": _yorumsuz_html(kaynak[kaynak.index("</style>"):]),
    }


def _yuzeyler(html_kaynak: dict | None = None) -> dict:
    """Lint'in taradığı yüzeylerin tamamı. `html_kaynak` YALNIZ pozitif kontrol içindir:
    sentetik olarak kirletilmiş bir kaynakla çağrılır ve lintin kırmızıya döndüğü ölçülür."""
    yuzey = {}
    for ad, kaynak in (html_kaynak or HTML_KAYNAK).items():
        yuzey.update(_html_yuzeyleri(ad, kaynak))
    yuzey["app.js"] = _yorumsuz_js(APPJS)
    yuzey["palette.js"] = _yorumsuz_js(PALETTE)
    yuzey["theme.js"] = _yorumsuz_js(THEME)
    return yuzey


def test_ham_renk_YOK_alti_yuzeyde():
    """Renk taşıyan hiçbir değer kuralın içine YAZILMAZ, jetondan gelir. Aksi hâlde
    ikinci tema sessizce kırılır — bu tam olarak --nav-bg'de, sonra bir kez daha
    landing.html'in `.btn-f`/`.pillc` kurallarında yaşandı (gece 1,53:1).

    ESKİ ADI: test_ham_renk_YOK_dort_yuzeyde (2026-08-01 → 2026-08-07). Ad, kapsam dörtten
    altıya çıkınca gerçeğe uyduruldu: yanlış bir ad, kapsamı okumadan varsayan bir okuyucu
    üretir — kapsam boşluğunun bir yıl fark edilmemesinin sebeplerinden biri tam olarak buydu.
    İzlenebilirlik için eski ad burada duruyor."""
    for ad, metin in _yuzeyler().items():
        bulunan = [h for h in _ham_renkler(metin) if h not in IZIN_VERILEN]
        assert not bulunan, f"{ad}: jeton dışı ham renk {bulunan}"
    # KAPSAM SAYIMI — altı yüzey, dokuz dilim (üç HTML × 2 + üç JS). Sessizce daralan bir
    # kapsam yeşil verir; ölçümün kendisi kadar sayısı da çivilenir.
    assert len(HTML_KAYNAK) == 3 and len(_yuzeyler()) == 9, \
        f"kapsam değişmiş: {len(HTML_KAYNAK)} HTML yüzeyi · {len(_yuzeyler())} dilim"


def test_allowlist_ISTISNALARI_GEREKCESIZ_OLAMAZ():
    """YASA 4: sessiz-yutma işaretli + ≥20 karakter gerekçe. Bir istisna, gerekçesi
    olmadan listeye giremez; girerse liste bir yılda anlamsızlaşır."""
    for renk, gerekce in IZIN_VERILEN.items():
        assert len(gerekce) >= 20, f"{renk}: gerekçe {len(gerekce)} karakter (≥20 gerekli)"


_TUZAK = "#ff00aa"


def _enjekte_kural(kaynak: str) -> str:
    """`</style>`'ın hemen ÖNÜNE, İKİ YORUMUN ARASINA sentetik bir kural sok.
    Yorumların arasına konması bilinçli: yorum ayıklayıcısı açgözlü olsaydı (`.*` yerine
    `.*?` yazılmasaydı) iki yorumun ARASINDAKİ gerçek ihlali de siler ve lint kendi
    körlüğünü üretirdi — ölçüldü (2026-08-07): açgözlü desen bu parçadan `.zz-tuzak{…}`
    kuralını komple yutuyor. (Bugün o mutasyon zaten import anında patlar, çünkü açgözlü
    desen jeton bloklarını da siler ve `_css_govdeleri` onları bulamaz; buradaki enjeksiyon
    o kazaya BAĞLI KALMAMAK içindir — jeton blokları bir gün taşınırsa tek kalan diş bu olur.)"""
    i = kaynak.index("</style>")
    return kaynak[:i] + f"\n/* önce */\n.zz-tuzak{{color:{_TUZAK}}}\n/* sonra */\n" + kaynak[i:]


def _enjekte_satirici(kaynak: str) -> str:
    """Belge gövdesine satır-içi stil sok — CSS dosyasına hiç uğramadan renk taşımanın yolu."""
    return kaynak + f'\n<div style="background:{_TUZAK}"></div>\n'


def _enjekte_yorum(kaynak: str) -> str:
    """Aynı rengi YORUMUN İÇİNE koy (hem CSS hem HTML yorumu). Bu bir ihlal DEĞİLDİR ve
    yakalanmamalıdır; `.btn-f` düzeltmesini ANLATAN not tam olarak bu biçimdedir."""
    i = kaynak.index("</style>")
    return (kaynak[:i] + f"\n/* düzeltme notu: burada ham {_TUZAK} duruyordu */\n" + kaynak[i:]
            + f"\n<!-- tarih notu: {_TUZAK} 2026-08-07'de kaldırıldı -->\n")


def test_lint_KENDINI_KANITLAR():
    """Kıramayan bir lint, yeşil veren bir süstür. Enjekte edilmiş bir ham renk
    yakalanmıyorsa yukarıdaki üç test hiçbir şey ölçmüyor demektir.

    KAPSAM GENİŞLEDİYSE KANIT DA GENİŞLER (2026-08-07). Bir yüzeyi `_yuzeyler()`e yazmak,
    onun TARANDIĞINI kanıtlamaz: çıkarma boru hattı (yorum ayıklama · jeton bloğu kesme ·
    `{…}` gövde toplama) o yüzeyde sessizce boş metin üretirse lint YALANCI YEŞİL verir ve
    yeni kapsam bir süs olur. Bu yüzden aşağıda yüzey BAŞINA diş ölçülür: kaynağa sentetik
    bir ham renk enjekte edilir ve tam O DİLİMİN kırmızıya döndüğü sınanır."""
    for tuzak in ("color:#ff00aa", "background:rgba(1,2,3,.5)", "border-color:white"):
        assert _ham_renkler("x{" + tuzak + "}"), f"lint bu tuzağı kaçırıyor: {tuzak}"
    # ve YANLIŞ POZİTİF vermemeli
    for temiz in ("white-space:nowrap", "#gate-pw2-wrap{display:none}",
                  "color:var(--tx)", "background:transparent", "fill:currentColor",
                  # 2026-08-24 · ÖLÇÜLEN YALANCI POZİTİF: CSS OLMAYAN bir `ad: deger` çifti.
                  # `red` burada "reddi"nin kısaltması olan bir JS değişkenidir (app.js Top
                  # Views kırılımı) ve hiçbir piksel boyamaz.
                  '{ anahtar: "red", ad: "Kapı reddi", satirlar: red }',
                  "gorunum: green", "durum: blue"):
        assert not _ham_renkler(temiz), f"lint yanlış pozitif: {temiz}"
    # VE DİŞLERİ YERİNDE: renk ÖZELLİĞİNİN sağındaki adlı renk hâlâ ısırır.
    for tuzak in ("color:red", "background-color:white", "fill:green", "stroke:blue",
                  "outline-color:orange", "border-bottom-color:silver"):
        assert _ham_renkler("x{" + tuzak + "}"), f"lint bu adlı rengi kaçırıyor: {tuzak}"

    # ---- YÜZEY BAŞINA DİŞ: her HTML yüzeyinin İKİ dilimi de ayrı ayrı ısırmalı ----
    for ad, kaynak in HTML_KAYNAK.items():
        kural_dilim = f"{ad} <style> (jeton blokları hariç)"
        govde_dilim = f"{ad} gövdesi (satır içi stil)"

        y = _yuzeyler({**HTML_KAYNAK, ad: _enjekte_kural(kaynak)})
        assert _TUZAK in _ham_renkler(y[kural_dilim]), \
            f"{kural_dilim}: kural gövdesine enjekte edilen ham renk lint'ten KAÇIYOR"
        assert _TUZAK not in _ham_renkler(y[govde_dilim]), \
            (f"{govde_dilim}: <style> içine sokulan renk BELGE dilimine sızıyor — iki dilim "
             "ayrık değil, yani birinin yeşili ötekinin ölçüsü sanılabilir")

        y = _yuzeyler({**HTML_KAYNAK, ad: _enjekte_satirici(kaynak)})
        assert _TUZAK in _ham_renkler(y[govde_dilim]), \
            f"{govde_dilim}: satır-içi stile enjekte edilen ham renk lint'ten KAÇIYOR"
        assert _TUZAK not in _ham_renkler(y[kural_dilim]), \
            f"{kural_dilim}: belge gövdesindeki renk KURAL dilimine sızıyor"

        # Ve yorum ayıklaması İKİ YÖNDE de doğru: ihlali yutmaz (yukarıda), gerekçeyi
        # ihlal saymaz (burada). İkincisi olmadan bu depoda ölçüm YAZILAMAZDI.
        y = _yuzeyler({**HTML_KAYNAK, ad: _enjekte_yorum(kaynak)})
        assert _TUZAK not in _ham_renkler(y[kural_dilim]), \
            f"{kural_dilim}: CSS YORUMUNDAKİ renk ihlal sayılıyor — düzeltmeyi anlatan not kırmızı verir"
        assert _TUZAK not in _ham_renkler(y[govde_dilim]), \
            f"{govde_dilim}: HTML YORUMUNDAKİ renk ihlal sayılıyor"

    # Enjeksiyon yalnız HEDEF yüzeyi kirletmeli: ötekiler temiz kalmazsa `_yuzeyler()` kaynak
    # sızdırıyor demektir ve tek bir kirli yüzey dokuz dilimi birden kırmızıya boyardı.
    kirli = _yuzeyler({**HTML_KAYNAK, "landing.html": _enjekte_kural(LANDING)})
    lekeli = [d for d, m in kirli.items() if _TUZAK in _ham_renkler(m)]
    assert lekeli == ["landing.html <style> (jeton blokları hariç)"], \
        f"enjeksiyon yüzeyler arasında sızıyor: {lekeli}"


# =============================== Ç4 · KONTRAST ÇİVİSİ ===============================
def _rgba(deger, tema):
    d, tablo = deger.strip(), (dict(ROOT, **GECE_OV) if tema == "gece" else ROOT)
    for _ in range(8):
        # D1'den beri bir jetonun değeri BAŞKA bir jetona `var()` ile bağlı olabilir
        # (rol katmanı: `--sev-1:var(--red)`). İki biçim de yürünür — yoksa rol adıyla
        # yazılmış bir çivi satırı "renk değil" diye düşerdi ve düşme sebebi mimari
        # olurdu, ölçüm değil.
        m = re.fullmatch(r"--([a-z0-9-]+)", d) or re.fullmatch(r"var\(\s*--([a-z0-9-]+)\s*\)", d)
        if not m:
            break
        d = tablo[m.group(1)].strip()
    m = re.fullmatch(r"#([0-9a-fA-F]{6})", d)
    if m:
        h = m.group(1)
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 1.0)
    # GÖLGE JETONU DA ÖLÇÜLÜR (2026-08-24). `--sh-ring` bir renk DEĞİL bir gölgedir
    # (`rgba(...) 0 0 0 4px`) ama ekranda çizdiği şey bir RENKTİR ve o rengin zeminine
    # karşı oranı G4'ün kapsamındadır. Geometri atılır, renk ölçülür; atmasaydık çivi
    # tablosu bu satırı "renk değil" diye reddeder ve halkanın 3:1 altında kaldığı
    # ÖLÇÜLMEDEN kalırdı — tam olarak bu dosyanın kovaladığı sessiz boşluk.
    m = re.match(r"(rgba?\([^)]*\))\s+\S+\s+\S+\s+\S+\s+\S+$", d)
    if m:
        d = m.group(1)
    m = re.fullmatch(r"rgba?\(\s*(\d+),\s*(\d+),\s*(\d+),\s*([0-9.]+)\)", d)
    assert m, f"renk değil: {d!r}"
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)), float(m.group(4)))


def _uzerine(ust, alt):
    """8-bit sRGB'de source-over — tarayıcının fiilen yaptığı işlem. Alfa'yı
    yok sayıp jetonun ham değerini ölçmek, ekranda var OLMAYAN bir rengi ölçmektir."""
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


def _civi_satirlari():
    """docs/kontrast-denetimi.md'nin ÇİVİ TABLOSU bölümü. Biçim:
    | mürekkep | zemin-yığını | tema | oran | eşik |"""
    i = RAPOR.index("<!-- CIVI-TABLOSU-BASI -->")
    j = RAPOR.index("<!-- CIVI-TABLOSU-SONU -->")
    for satir in RAPOR[i:j].splitlines():
        h = [x.strip() for x in satir.strip().strip("|").split("|")]
        if len(h) != 5 or h[0].startswith(("mürekkep", ":--", "---")):
            continue
        yield h


def test_rapordaki_KONTRAST_RAKAMLARI_yeniden_uretilebilir():
    """Bayat bir erişilebilirlik raporu, hiç yapılmamış bir denetimden daha kötüdür:
    okuyucu ona güvenir. Jeton değeri kımıldarsa rapor burada bayat ilan edilir."""
    sayac = 0
    for murekkep, zemin, tema, oran_s, _esik in _civi_satirlari():
        katmanlar = [k.strip() for k in zemin.split("+")]
        zc = _yigin(katmanlar, tema)
        ic = _rgba(murekkep, tema)
        ic = _uzerine(ic, zc) if ic[3] < 1.0 else ic
        olculen = _oran(ic, zc)
        assert abs(olculen - float(oran_s)) < 0.005, \
            (f"rapor BAYAT: {murekkep} üzerinde {zemin} ({tema}) — "
             f"raporda {oran_s}, kaynaktan {olculen:.2f}")
        sayac += 1
    assert sayac >= 24, f"çivi tablosu {sayac} satır — kapsam daralmış"


def test_para_renkleri_EN_KOTU_GERCEK_ZEMINDE_AA_kalir():
    """Jeton yeniden-değerleme turu geldiğinde (gündüz beyazı) bu üç renk AA altına
    düşerse pano parayı okunamaz yazıyor demektir. Eşik SONRADAN düşürülemez.

    D1 SONRASI OKUNAN KATMAN DEĞİŞTİ, EŞİK DEĞİŞMEDİ. Ekranda fiilen çizilen jeton artık
    ROL jetonudur (`.durum-kart.uyari{color:var(--sev-2)}`); --green/--amber/--red yalnız
    o rollerin BUGÜNKÜ kaynağıdır. Ölçüm rolü izler, çünkü kırılma bu depoda tam olarak
    şöyle olurdu: bir rol başka bir hue'ya yeniden bağlanır, ekran değişir, ama hue'yu
    ölçen test yeşil kalır. Bugün üçü de alias olduğu için SAYILAR AYNI (gündüz 4.72 /
    5.57 / 4.59 · gece 5.31 / 5.39 / 5.01) — iddia zayıflamadı, adresi düzeldi.
    YÖN ve MOD rollerinin AA'sı tests/test_renk_rolleri_v197.py §7'de ölçülür; buraya
    ikinci bir kopya koymak, ilk düzenlemede ayrışacak iki eşik demek olurdu."""
    en_kotu = {"--sev-3": "--sev-3-t", "--sev-2": "--sev-2-t", "--sev-1": "--sev-1-t"}
    for tema in ("gunduz", "gece"):
        for ink, tint in en_kotu.items():
            zc = _yigin(["--card-2", tint], tema)
            assert _oran(_rgba(ink, tema), zc) >= 4.5, \
                f"{ink} ({tema}) kendi tinti gömülü panelde AA ALTI"


def test_odak_halkasi_HER_ZEMINDE_3_1():
    """WCAG 2.2 2.4.11/1.4.11: odak göstergesi görünür OLMAK ZORUNDA. Bu pano
    klavye-öncelikli tasarlandı; halka kaybolursa gezinme kaybolur.

    ZEMİN LİSTESİ ROL ADLARIYLA YAZILIR (D1): halkanın üstüne bindiği tint'ler bileşen
    kurallarında rol jetonudur. Matrisin hücre zemini de listeye girdi — o zemin D1'de
    `--pm-pos`/`--pm-neg`ten `--yon-*-zemin`e taşındı ve `.pm-cell` odaklanabilir bir
    düğmedir; adı "HER ZEMİNDE" olan bir ölçümün onu atlaması adın kendisini yalanlardı."""
    for tema in ("gunduz", "gece"):
        for zemin in (["--bg"], ["--card"], ["--card-2"], ["--accent-tint"],
                      ["--card-2", "--sev-1-t"], ["--card-2", "--sev-2-t"],
                      ["--card-2", "--yon-arti-zemin"], ["--card-2", "--yon-eksi-zemin"]):
            assert _oran(_rgba("--accent", tema), _yigin(zemin, tema)) >= 3.0, \
                f"odak halkası {tema}/{zemin} üzerinde 3:1 altında"


def test_rapor_BILINCLI_ISTISNA_ve_ONERI_bolumlerini_TASIR():
    """Kalan çiftler için hüküm önerisi rapordadır, değer değişikliği DEĞİL (WP0
    kararı: jeton yeniden-değerlemesi ayrı onay turu). İki bölüm de zorunlu:
    biri olmadan rapor ya sansürlü ya da yetkisiz bir değişiklik olur."""
    for baslik in ("## 6 · Bilinçli istisnalar", "## 7 · Değişiklik önerileri",
                   "<!-- CIVI-TABLOSU-BASI -->"):
        assert baslik in RAPOR, f"kontrast raporunda eksik bölüm: {baslik}"
    assert "ÖNERİ — UYGULANMADI" in RAPOR, \
        "öneriler uygulanmadıkları açıkça yazılmadan durursa okuyucu onları hüküm sanır"

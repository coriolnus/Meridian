"""test_ui_pilot_kapilari_v286.py — SHADCN PİLOTUNUN ÜÇ KAPISI (2026-08-24).

NEDEN BU DOSYA VAR — operatörün önerisi ve ONUN GEREKÇESİ:
    "mimariyi buna çevirmenin ne gibi avantajı olur, shadcnblocks altında bütün
     ihtiyaçlarımızı karşılayan bileşenler mevcut, bu şekilde tutarlılığı çok daha
     rahat sağlayabileceğiz gibi geliyor"

Argüman DOĞRU olan bir mekanizmaya dayanıyor ve küçültülmedi: panonun hastalığı tam da
buydu — tek bir kavram (`rozet`) için beş CSS reçetesi yan yana yaşıyordu ve ALTINCISININ
doğmasını hiçbir şey engellemiyordu. Bir bileşen sınırı altıncıyı YAZILAMAZ kılar; çivi
yalnız TESPİT eder. Bileşen sınırı, konvansiyondan güçlüdür.

Karşı tarafta ölçülmüş maliyet var: `app.js` 12.653 satır / 401 HTML emisyonu; dört tasarım
dosyasında 129 çivi CSS'i KAYNAK METİN olarak okuyor; dağıtım derleme adımı olmayan bir
rsync hattı ve `[5b]` tazelik kapısı "dağıtılan dosya = kaynak" varsayıyor.

İKİ TARAF DA TAHMİN OLDUĞU İÇİN ÖLÇÜLÜYOR. Pilot yüzeyi `workflow.html`: canlı veri bağı
SIFIR (para yolunda değil), ama tam jeton/kontrast sistemini, kendi-barındırdığımız yazı
tiplerini ve tema anahtarını kullanıyor — yani üç kapıyı da gerçekten sınar.
(`runbook.html` PİLOT OLARAK REDDEDİLDİ: kendi yazılı sözleşmesi "sıfır sayfa mantığı,
JS kapalıyken de eksiksiz okunur" ve gövdesini `meridian/api.py::runbook()` SUNUCUDA
dolduruyor — React'e taşımak sayfanın kendi kararını çiğnerdi.)

ÜÇ KAPI. Üçü de geçerse pano da taşınır; biri düşerse pilot kalır, pano taşınmaz.
  G1  JETON/KONTRAST DENKLİĞİ — ölçülmüş kontrast garantileri (ÇG1/ÇG2/ÇG3, AA tabloları)
      Tailwind katmanına geçerken KAYBOLMUYOR.
  G2  DAĞITIM BÜTÜNLÜĞÜ — araç zinciri canlıya SIZMIYOR, artefakt kaynağından TAZE ve
      CSP (`script-src 'self'`) satır içi betikle çiğnenmiyor.
  G3  EPİSTEMİK DEĞİŞMEZLER — Meridian'ın çivileri GÖRSEL değil: "paydanı beyan et",
      "ölçülemedi ile sıfır aynı kutuya girmez". Bunlar bileşen değişmezi olarak
      YAZILABİLİYOR mu? shadcn bunlar hakkında hiçbir şey bilmez; yazılamıyorsa taşıma
      görsel tutarlılık kazandırıp DOĞRULUK tutarlılığını kaybettirir.

Bu dosya PİLOT İNMEDEN ÖNCE yazıldı ve KIRMIZI başlar (TDD). `PILOT_VAR` yanlışken
kapılar `skip` değil, açıkça "pilot henüz kurulmadı" diye atlanır — sessiz yeşil YASAK.
"""
from __future__ import annotations

import json
import pathlib
import re

import pytest

KOK = pathlib.Path(__file__).resolve().parents[1]
UI = KOK / "ui"
WEB = KOK / "meridian" / "web"
DAGIT = KOK / "dagit.sh"

# Pilotun ürettiği artefakt. Mevcut `workflow.html` YERİNE GEÇMEZ — yan yana durur ki
# ikisi aynı ekranda karşılaştırılabilsin ve karar ölçümle verilsin.
ARTEFAKT = WEB / "pilot-workflow.html"
ARTEFAKT_VARLIK = WEB / "pilot-assets"

PILOT_VAR = UI.is_dir()


_TS_YORUM = re.compile(r"/\*.*?\*/|(?<![:'\"])//[^\n]*", re.S)


def _soy(metin: str) -> str:
    """TS/TSX yorumlarını çıkar.

    NEDEN AYRI YARDIMCI: bu oturumda ÜÇ ayrı çivi aynı hataya düştü — Meridian'ın
    belge geleneği kararın gerekçesini yazarken YASAKLANAN ŞEYİ ALINTILAR
    ("`text-green-600` bir rol DEĞİLDİR", "`payda?: string` yazılsaydı..."), ve
    alıntıyı kullanım sanan çivi kendi belge geleneğini suçlar. Soymadan ölçme.
    """
    return _TS_YORUM.sub("", metin)


def _ts_kaynaklari() -> list[pathlib.Path]:
    return [p for p in list(UI.rglob("*.ts")) + list(UI.rglob("*.tsx"))
            if "node_modules" not in p.parts]


def _pilot_gerekli():
    if not PILOT_VAR:
        pytest.fail(
            "PİLOT HENÜZ KURULMADI (ui/ yok). Bu bir 'geçti' değildir — kapı ölçülemedi. "
            "Kapılar pilottan ÖNCE yazıldı (TDD) ve pilot inene kadar KIRMIZI kalır.")


# =================================================================================================
# G2 — DAĞITIM BÜTÜNLÜĞÜ (ilk sırada: kurulumun kendisi bir sızıntı sınıfıdır)
# =================================================================================================
# 2026-08-24 vakası bu sınıfın canlı kanıtı: `scratch-panov2/` kuru koşumda 5 girdiyle CANLIYA
# GİDİYORDU çünkü yerelde .gitignore'luydu ama RSYNC GITIGNORE OKUMAZ — yalnız kendi listesini
# okur. İki mekanizma AYRI ve birini kapatmak ötekini kapatmaz. Aynı ders daha önce araç
# katmanında da alınmıştı (`.impeccable`, `.import_linter_cache`).

ARAC_ZINCIRI = ["node_modules", "ui/node_modules"]


def _rsync_dislamalari() -> set[str]:
    return set(re.findall(r"--exclude '([^']*)'", DAGIT.read_text()))


@pytest.mark.parametrize("desen", ARAC_ZINCIRI)
def test_G2a_arac_zinciri_CANLIYA_SIZMAZ(desen):
    """`npm install` bir dağıtım olayıdır. node_modules on binlerce dosyadır, canlıda
    okuyucusu yoktur ve rsync onu .gitignore'a bakmadan taşır."""
    dis = _rsync_dislamalari()
    assert desen in dis or any(d.rstrip("/") == desen.rstrip("/") for d in dis), (
        f"dagit.sh rsync dışlama listesinde '{desen}' YOK — kurulum canlıya sızar. "
        f"UYARI: .gitignore YETMEZ, rsync onu okumaz (2026-08-24 scratch-panov2 vakası).")


def test_G2b_pilot_KAYNAGI_canliya_gitmez_ARTEFAKT_gider():
    """Canlıya giden ARTEFAKT'tır, kaynak değil. `ui/` altındaki TSX/config canlıda
    okuyucusuz durur (YASA 6) ve dağıtım yüzeyini gereksiz büyütür."""
    dis = _rsync_dislamalari()
    assert any(d.strip("/") in ("ui", "ui/*") for d in dis), (
        "dagit.sh 'ui' kaynağını dışlamıyor — derlenmemiş kaynak canlıya gider")
    # Artefakt DIŞLANMAMALI: dışlanırsa sayfa canlıda 404 olur ve bunu kimse görmez.
    for yasak in ("pilot-workflow.html", "pilot-assets", "meridian/web/pilot*"):
        assert yasak not in dis, f"artefakt '{yasak}' dışlanmış — sayfa canlıda doğmaz"


def test_G2c_artefakt_TAZELIK_kapisi_dagitta_VAR():
    """`[5b]` kod tazeliği "dağıtılan dosya = kaynak" varsayıyor. Araya derleme girince o
    varsayım DÜŞER: kaynak değişip artefakt yeniden üretilmezse canlı SESSİZCE bayat kalır
    ve doğrulama 'active' der — tam olarak `meridian-learn`'de yaşadığımız sessiz etkisizlik.

    Bu yüzden dağıtımın artefaktın KENDİ tazeliğini de ölçmesi gerekir:
        mtime(artefakt) >= max(mtime(ui/ altındaki kaynaklar))
    """
    _pilot_gerekli()
    s = DAGIT.read_text()
    assert "ARTEFAKT TAZELİĞİ" in s, (
        "dagit.sh'te artefakt tazelik kapısı YOK — kaynak değişip build koşmazsa canlı "
        "sessizce bayat kalır ve [5b] bunu göremez (o Python mtime'ına bakar)")
    assert "pilot-workflow.html" in s, "tazelik kapısı pilot artefaktını tanımıyor"


def test_G2d_uretilen_sayfa_CSP_uyumlu():
    """Dağıtım CSP'si `script-src 'self'` (deploy/Caddyfile). Satır içi `<script>` ve satır
    içi işleyici ÜRETİMDE BLOKLANIR — sayfa canlıda ölü açılır. Bu arıza bu depoda İKİ KEZ
    yaşandı: landing.html + workflow.html satır içi `<script>` taşıyordu → landing.js/
    workflow.js'e alındı. Kayıt `meridian/api.py`in CSP blokunda (satır ÇAPASI YOK —
    bu oturumda ölçüldü: satır çapaları bayatlar, `codelaw` onları kırmızı sayar)."""
    _pilot_gerekli()
    if not ARTEFAKT.exists():
        pytest.fail(f"pilot artefaktı üretilmemiş: {ARTEFAKT}")
    s = ARTEFAKT.read_text()
    satir_ici = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(?!\s*</script>)", s)
    assert not satir_ici, (
        f"üretilen sayfada {len(satir_ici)} satır içi <script> var — CSP `script-src 'self'` "
        f"bunları bloklar ve sayfa canlıda ÖLÜ açılır. Vite'ın modulepreload/inline "
        f"davranışı kapatılmalı.")
    isleyici = re.findall(r"\son(?:click|load|error|change|submit)\s*=", s)
    assert not isleyici, f"satır içi olay işleyicisi var ({len(isleyici)}) — CSP bloklar"


def test_G2e_dis_origin_YOK():
    """"AĞ YOKKEN DE AÇILIR" sözleşmesi dört yüzeyin ortak kararı: yazı tipi bu sunucunun
    kendi baytları, CDN yok, üçüncü taraf yok. shadcn/Tailwind şablonları varsayılan olarak
    Google Fonts bağlar — pilot bunu GETİREMEZ."""
    _pilot_gerekli()
    if not ARTEFAKT.exists():
        pytest.fail(f"pilot artefaktı üretilmemiş: {ARTEFAKT}")
    s = ARTEFAKT.read_text()
    dis = re.findall(r'(?:href|src)="(https?://[^"]+)"', s)
    assert not dis, f"üretilen sayfa dış origin'e gidiyor: {dis[:5]} — ağ yokken açılmaz"


# =================================================================================================
# G1 — JETON / KONTRAST DENKLİĞİ
# =================================================================================================
# Meridian'ın renk katmanı bir üslup değil bir GÜVENLİK KAYDI: rol jetonları (ROL 1-6), rezerve
# hue bantları (mod 285-335°, nav 255-272°) ve ÖLÇÜLMÜŞ kontrast tabloları. Tailwind'e geçerken
# bunların "yaklaşık aynı" olması yetmez — BİREBİR aynı olmalı, yoksa taşıma sessizce bir
# güvenlik sinyalini bozar (örn. kâğıt/canlı mod çipi bir grafik serisiyle aynı renge düşer).

ROL_JETONLARI = [
    "--sev-1", "--sev-2", "--sev-3",
    "--yon-arti", "--yon-eksi",
    "--mod-canli", "--mod-kesif",
    "--nav", "--nav-2",
    "--huni-1", "--huni-2", "--huni-3",
]


def _css_jetonlari_metinden(s: str, tema: str = "gunduz") -> dict[str, str]:
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    if tema == "gece":
        m = re.search(r'\[data-theme="dark"\][^{]*\{(.*?)\n\}', s, re.S)
        s = m.group(1) if m else ""
    else:
        # GÜNDÜZ: gece bloklarını ÇIKAR, yoksa son yazan kazanır ve gündüz gece
        # değerine düşer — üretecin kendisi bu hatayı yaptı ve ölçümle yakalandı.
        s = re.sub(r'\[data-theme="dark"\]\s*\{[^{}]*\}', "", s, flags=re.S)
        s = re.sub(r"@media\s*\(prefers-color-scheme:\s*dark\)\s*\{(?:[^{}]|\{[^{}]*\})*\}", "", s, flags=re.S)
    return {m.group(1): m.group(2).strip()
            for m in re.finditer(r"(--[a-z0-9-]+)\s*:\s*([^;}]+)", s)}


def _css_jetonlari(yol: pathlib.Path, tema: str = "gunduz") -> dict[str, str]:
    """Bir yüzeyin jeton bildirimlerini oku (yalnız ilk/gündüz bloğu)."""
    s = yol.read_text()
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    if tema == "gece":
        m = re.search(r'\[data-theme="dark"\][^{]*\{(.*?)\n\}', s, re.S)
        s = m.group(1) if m else ""
    return {m.group(1): m.group(2).strip()
            for m in re.finditer(r"(--[a-z0-9-]+)\s*:\s*([^;}]+)", s)}


@pytest.mark.parametrize("jeton", ROL_JETONLARI)
def test_G1a_rol_jetonlari_BIREBIR_tasiniyor(jeton):
    """Pilot yüzeyi rol jetonlarını ana panoyla AYNI değerde taşımalı.

    "Yaklaşık" kabul edilmez: `--mod-canli` bir zamanlar Dub'ın `--lavender`ıyla BİREBİR
    aynı hex'ti ve bu, "canlı para" çipiyle bir grafik serisini aynı renge düşürüyordu —
    kâğıt/canlı ayrımı bir güvenlik sinyalidir.
    """
    _pilot_gerekli()
    if not ARTEFAKT.exists():
        pytest.fail(f"pilot artefaktı üretilmemiş: {ARTEFAKT}")
    ana = _css_jetonlari(WEB / "index.html")
    # ARTEFAKT İKİ PARÇADIR: Vite CSS'i ayrı dosyaya çıkarır ve HTML ona <link> ile bağlanır.
    # Yalnız HTML'e bakmak "jeton kayboldu" der — ölçüm bağlamı tuzağı; bağlı CSS de okunur.
    pilot_metin = ARTEFAKT.read_text()
    for m in re.finditer(r'<link[^>]+href="(/pilot-assets/[^"]+\.css)"', pilot_metin):
        yol = WEB / m.group(1).lstrip("/")
        assert yol.exists(), f"artefaktın bağladığı CSS diskte yok: {yol}"
        pilot_metin += "\n" + yol.read_text()
    pilot = _css_jetonlari_metinden(pilot_metin)
    assert jeton in ana, f"{jeton} ana panoda tanımlı değil — çivinin listesi bayat"
    assert jeton in pilot, (
        f"{jeton} pilot yüzeyinde YOK — Tailwind katmanı rol jetonunu düşürdü. "
        f"Rol katmanı sözleşmesi (index.html:296-299) bileşenin YALNIZ rol jetonu "
        f"okumasını zorunlu kılar; jeton yoksa bileşen değer jetonuna ya da hex'e kaçar.")
    assert pilot[jeton] == ana[jeton], (
        f"{jeton}: ana pano '{ana[jeton]}' ↔ pilot '{pilot[jeton]}' — taşıma sırasında ayrıştı")


def test_G1b_ciplak_hex_ve_deger_jetonu_BILESENDE_yok():
    """Rol katmanı sözleşmesi: bileşen kuralları YALNIZ rol jetonu okur. Tailwind'in utility
    sınıfları bu sözleşmeyi kırmanın en kolay yoludur (`text-green-600` bir rol değildir)."""
    _pilot_gerekli()
    kaynaklar = _ts_kaynaklari()
    assert kaynaklar, "ui/ altında kaynak yok — pilot boş"
    ihlal = []
    for p in kaynaklar:
        s = _soy(p.read_text())
        for m in re.finditer(r"#[0-9a-fA-F]{3,8}\b", s):
            ihlal.append(f"{p.relative_to(KOK)}: {m.group(0)}")
        # Tailwind'in HAZIR renk skalası bir rol DEĞİLDİR
        for m in re.finditer(r"\b(?:text|bg|border|fill|stroke)-(?:red|green|blue|amber|"
                             r"yellow|orange|purple|violet|slate|gray|zinc|neutral|stone)-\d{2,3}\b", s):
            ihlal.append(f"{p.relative_to(KOK)}: {m.group(0)}")
    assert not ihlal, (
        f"pilot bileşenleri rol katmanını atlıyor ({len(ihlal)}): {ihlal[:8]} — "
        f"renk YALNIZ rol jetonundan gelir")


# =================================================================================================
# G3 — EPİSTEMİK DEĞİŞMEZLER (kapının en zoru ve en önemlisi)
# =================================================================================================
# Bu kapı düşerse pilot "güzel ama Meridian değil" demektir. shadcn görsel tutarlılık verir;
# Meridian'ın yasaları DOĞRULUK tutarlılığı hakkında ve onları bileşen sınırına taşıyabilmemiz
# gerekir — yoksa taşıma bir kazanç değil, takas olur.

def test_G3a_olcum_bileseni_PAYDA_beyanini_ZORUNLU_kilar():
    """`hucreCubuk` kuralı (app.js): oran 0 → çubuk çizilir ve BOŞ görünür ("ölçtük, sıfır
    çıktı"); oran null → çubuk HİÇ DOĞMAZ ("ölçemedik"). Paydasız çubuk YASAK — okuru kendi
    uydurduğu tavana göre okutur.

    Bileşen sınırında bu, `payda`nın OPSİYONEL OLMAYAN bir alan olması demektir.
    """
    _pilot_gerekli()
    aday = [p for p in _ts_kaynaklari() if "meridian" in p.parts]
    assert aday, ("ui/src altında ölçüm bileşeni yok — G3 ölçülemedi. Pilotun anlamı "
                  "shadcn'in kartını çizmek değil, Meridian'ın ölçüm hücresini onun "
                  "gramerinde YENİDEN KURABİLMEK.")
    s = "\n".join(_soy(p.read_text()) for p in aday)
    assert re.search(r"payda\s*:\s*string", s), (
        "ölçüm bileşeni `payda`yı ZORUNLU alan olarak bildirmiyor — paydasız çubuk yazılabilir")
    assert not re.search(r"payda\?\s*:", s), (
        "`payda` opsiyonel bildirilmiş — o an kural bir konvansiyona geri düşer")


def test_G3b_olculemedi_ile_sifir_AYRI_kutuda():
    """UYDURMA YASAĞI'nın bileşendeki karşılığı: `deger` yokluğu bir SAYI DEĞİLDİR.
    `deger: number | null` yetmez — null'ın NEDENİ de taşınmalı, yoksa bileşen "veri yok"
    yazar ve okur bunu "sıfır" sanır."""
    _pilot_gerekli()
    s = "\n".join(_soy(p.read_text()) for p in _ts_kaynaklari())
    assert re.search(r"neden\s*:\s*string", s), (
        "hiçbir bileşen `neden` alanı bildirmiyor — ölçülemeyen değerin NEDENİ taşınmıyor. "
        "UYDURMA YASAĞI: ölçülemeyen None + NEDEN.")
    # İKİ MEŞRU BİÇİM: `deger: number | null` (zayıf) ve AYRIK BİRLEŞİM (güçlü) —
    # ikincisinde `{ deger: null }` TEK BAŞINA yazılamaz çünkü `neden` eksiktir, yani
    # "nedensiz null" derleyicide durur. Çivi güçlü biçimi de tanımalı, yoksa daha iyi
    # tasarımı cezalandırır.
    zayif = re.search(r"deger\s*:\s*[^;]*\|\s*null", s)
    ayrik = re.search(r"deger\s*:\s*null\s*;[^}]*neden\s*:\s*string", s, re.S)
    assert zayif or ayrik, (
        "`deger` null taşıyamıyor — 'ölçülemedi' hâli tipte yok")
    if ayrik and not zayif:
        # Ayrık birleşim seçilmişse `neden`in ZORUNLU olduğunu da doğrula: opsiyonel
        # olsaydı nedensiz null yine yazılabilirdi ve kural konvansiyona düşerdi.
        assert not re.search(r"deger\s*:\s*null\s*;[^}]*neden\?\s*:", s, re.S), \
            "ayrık birleşimde `neden` OPSİYONEL — nedensiz null hâlâ yazılabilir"


def test_G3c_ozet_kapida_epistemik_civiler_SAYILIYOR():
    """Pilot bir KARAR dosyasıyla gelir: hangi epistemik çivi bileşen değişmezine çevrildi,
    hangisi ÇEVRİLEMEDİ. Çevrilemeyenler taşımanın gerçek bedelidir ve yazılmadan karar
    verilemez (YASA 6: okuyucusuz yazım yok — ama okuyucusuz KARAR da yok)."""
    _pilot_gerekli()
    kararlar = list((KOK / "docs").glob("KARAR-*UI-PILOT*.md")) \
        + list((KOK / "docs").glob("KARAR-*SHADCN*.md"))
    assert kararlar, ("pilot karar belgesi yok — hangi çivinin taşındığı/taşınamadığı "
                      "yazılmadan bu kapı geçemez")
    s = "\n".join(p.read_text() for p in kararlar)
    assert "TAŞINAMAYAN" in s.upper(), (
        "karar belgesi yalnız kazançları yazıyor — taşınamayan çiviler de yazılmalı")

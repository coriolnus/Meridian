"""v199 — D2-b: YENİ BİLGİ MİMARİSİ (beş yüzey) + OLAY YÜZEYLERİ + runbook emilimi.

BU DOSYANIN ÖLÇTÜĞÜ KUSUR SINIFI: **taşımanın yarım kalması**. S2R-2'nin göç testi (v156) bir
bölümün YANLIŞ EVE düşmesini yakalıyordu; D2-b'de risk bir kademe yukarı çıkıyor çünkü artık
SAYFALARIN KENDİSİ birleşiyor ve bir sayfa ortadan kalktığında ondan geriye üç şey kalır:

  A) KIRIK DERİN BAĞ — `kosu#adaylar`, `portfoy#mutabakat`, `gozetim#failsub`, `veri#veriboru`
     biçiminde YÜZLERCE eski adres var: `docs/RUNBOOK.md` bağları, çekmece çipleri, operatörün
     yer imleri. Sayfa kalkınca bunlar hiçbir yere gitmez ve hata da vermez — go() tanımadığı
     bir kimlikte sessizce varsayılan rotaya düşer. Operatör "bağ çalıştı" sanır, yanlış yerdedir.
  B) YARIM YÜZEY — bir bölüm iki yüzeyde birden görünür ya da hiçbirinde. İkisi de sessiz.
  C) ÖKSÜZ OLAY — `runbook.html` panoya emiliyor; emilmenin yarım kalması demek, alarmdan
     teşhise giden yolun HİÇBİR yere çıkmaması demek. Bir alarm jetonunun yüzeyi yoksa
     operatör olay anında boş bir çekmece açar — en pahalı anda en pahalı boşluk.
  D) YİNELENEN GERÇEK — aynı değer birden çok yerde yazılır ve biri sessizce bayatlar
     (baseline §2'nin ölçtüğü on çift).

TESTLER KAYNAĞA BAKAR (repo deseni: v154/v155/v156/v160). Tarayıcı ve yerel sunucu YOK
(CLAUDE.md §5): dosyalar okunur ve JS blokları düz metin olarak ölçülür.
"""
from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
WEB = SRC / "meridian" / "web"
APPJS = (WEB / "app.js").read_text()
INDEX = (WEB / "index.html").read_text()
PALETTE = (WEB / "palette.js").read_text()
RUNBOOK_HTML = (WEB / "runbook.html").read_text()
WORKFLOW_HTML = (WEB / "workflow.html").read_text()

# Yorum satırları KURAL SAYILMAZ: bu turun her kararı gerekçesiyle yazıldı ("eski hâli şuydu,
# neden yanlıştı"). O gerekçe kaynakta durmalı ama "hâlâ orada" diye okunmamalı — yoksa doğru
# davranan bir düzeltme kendi mezar taşı yüzünden düşer (v154/v155/v156'nın aynı kuralı).
KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))

# ---- BAĞLAYICI IA (docs/TASARIM-YONU-2026-08-07.md §3) --------------------------------------
# Bu liste testin KENDİ iddiasıdır ve kaynaktan TÜRETİLMEZ: türetilseydi test "kod kendine
# uyuyor mu?" diye sorardı ve bir yüzeyi yanlış adlandırmak testi yeşil bırakırdı.
YUZEYLER = ["bugun", "karar", "saglik", "ogrenme", "kilitler"]
YUZEY_ADI = {"bugun": "Bugün", "karar": "Karar", "saglik": "Sağlık",
             "ogrenme": "Öğrenme", "kilitler": "Kilitler"}
# Eski beş ALAN SAYFASI → yeni yüzeyi. Bunların DOM kabı YOKTUR (birleştiler); tek varlıkları
# ROUTE_ALIAS'taki satırlarıdır ve o satır kalkarsa (A) sınıfı doğar.
ESKI_SAYFALAR = {"genel": "bugun", "kosu": "karar", "portfoy": "karar",
                 "veri": "saglik", "gozetim": "saglik"}
# Denetim raporlarının ve RUNBOOK'un taşıdığı GERÇEK eski adresler — örneklem, tam liste değil.
ESKI_DERIN_ADRESLER = ["kosu#adaylar", "kosu#kapilar", "portfoy#brifing", "portfoy#onaylar",
                       "portfoy#mutabakat", "portfoy#intraemir", "portfoy#performans",
                       "portfoy#failsub", "veri#market", "veri#intraday", "veri#veriboru",
                       "gozetim#operasyon", "genel"]
# Olay yüzeyi sınıfları — brief'in adlandırdığı beş sınıf + `yetki` (ARMING_READY /
# AUTHORITY_CHANGE'in evi; onlar da alarmdır ve evsiz kalamazlar).
OLAY_SINIFLARI = ["besleme", "mutabakat", "kill", "butunluk", "yetki", "kota"]


def _sozluk(ad: str) -> dict[str, str]:
    blok = re.search(r"const %s = \{(.*?)\};" % ad, APPJS, re.S)
    assert blok, f"{ad} tanımlı değil"
    return dict(re.findall(r"(\w+):\s*\"([^\"]+)\"", blok.group(1)))


def _views() -> list[tuple[str, str]]:
    blok = re.search(r"const VIEWS = \[(.*?)\];", APPJS, re.S)
    assert blok, "VIEWS tanımlı değil"
    return re.findall(r'\["(\w+)", "([^"]+)"\]', blok.group(1))


def _alan_bolumleri() -> dict[str, list[str]]:
    blok = re.search(r"const ALAN_BOLUMLERI = \{(.*?)\n\};", APPJS, re.S)
    assert blok, "ALAN_BOLUMLERI tanımlı değil"
    return {alan: re.findall(r'"(\w+)"', liste)
            for alan, liste in re.findall(r"^\s*(\w+):\s*\[([^\]]*)\]", blok.group(1), re.M)}


def _govde(baslangic: str, bitis: str, kaynak: str = APPJS) -> str:
    i = kaynak.index(baslangic)
    return kaynak[i:kaynak.index(bitis, i)]


def _olay_yuzeyleri() -> str:
    return _govde("const OLAY_YUZEYLERI = {", "\n// JETON → SINIF")


# =================================================================================================
# 1) BEŞ YÜZEY — var, sıralı, tam
# =================================================================================================
def test_bes_yuzey_baglayici_sirayla():
    """Sıra bir zevk meselesi değil: çıplak 1-5 tuşları `VIEWS.findIndex` ile bu listeden türüyor
    ve yön belgesi §3 yüzeyleri ①..⑤ diye NUMARALIYOR."""
    assert [v for v, _ in _views()] == YUZEYLER
    for vid, ad in _views():
        assert ad == YUZEY_ADI[vid], f"{vid} yüzeyinin adı '{ad}' — bağlayıcı ad '{YUZEY_ADI[vid]}'"


def test_her_yuzeyin_kabi_sorusu_ve_ikonu_var():
    """Bir yüzey DÖRT şeyin buluşmasıdır: DOM kabı, çizim yolu, soru cümlesi, ray ikonu.
    Birinden biri eksikse yüzey bir vaattir — tıklanır, boş kalır ya da adsız görünür."""
    sorular = _sozluk("EKRAN_SORUSU")
    bolumlu = set(_alan_bolumleri())
    acik_render = set(re.findall(r"^RENDER\.(\w+) = ", APPJS, re.M))
    ikon = _govde("const RAIL_ICON = {", "\n};")
    for y in YUZEYLER:
        assert f'id="page-{y}"' in INDEX, f"page-{y} kabı index.html'de yok"
        assert y in bolumlu or y in acik_render, f"RENDER.{y} yok — yüzey çizilemez"
        assert y in sorular, f"{y}: soru cümlesi yok ('ekrana dök' yasağının çıpası)"
        assert re.search(r"^\s*%s: _ico\(" % y, ikon, re.M), f"{y}: ray ikonu yok"


def test_yuzey_sorulari_yon_belgesinin_sorularini_tasir():
    """Cümle bir SÖZLEŞMEDİR: yön belgesi §3 her yüzeyin cevapladığı soruyu yazıyor ve o soru
    ekranda görünmeden bir denetim çıpası olamaz. Anahtar kelime düzeyinde çivilenir — birebir
    dizge çivisi cümleyi düzeltilemez yapardı."""
    s = _sozluk("EKRAN_SORUSU")
    assert "dün gece" in s["bugun"] and "benden ne bekleniyor" in s["bugun"]
    assert "ne önerildi" in s["karar"] and "geçti/geçmedi" in s["karar"]
    assert "güvenilir mi" in s["saglik"] and "bozulduysa" in s["saglik"]
    assert "öğreniyor mu" in s["ogrenme"]
    assert "yetkisi" in s["kilitler"] and "durdururum" in s["kilitler"]
    for y in YUZEYLER:
        assert s[y].startswith("Bu ekran şunu cevaplar:"), \
            f"{y}: mertebe ön eki bozulmuş — sayfa cümlesi 'Bu ekran' ile başlar"


def test_her_bolum_TAM_BIR_yuzeyde():
    """(B) sınıfı. Bir bölüm iki yüzeyde birden görünürse aynı tablo iki kez okunur; hiçbirinde
    görünmezse içerik sessizce kaybolur. Üç kaynak birlikte ölçülür: ALAN_BOLUMLERI (çizim
    sırası), index.html (DOM evi) ve palette.js (harita)."""
    ab = _alan_bolumleri()
    assert set(ab) == set(YUZEYLER) - {"bugun"}, (
        "① Bugün'ün bölümü OLMAMALI (tek ekranlık kart kompozisyonu), diğer dördünün OLMALI: "
        f"{sorted(ab)}")
    hepsi = [b for bl in ab.values() for b in bl]
    assert len(hepsi) == len(set(hepsi)), "bir bölüm iki yüzeyde birden çiziliyor"

    # DOM evi — bölüm kabı hangi `.page`in içinde?
    ana = INDEX[INDEX.index('<main id="main">'):INDEX.index("</main>")]
    ev: dict[str, str] = {}
    for parca in re.split(r'(?=<section class="page)', ana):
        m = re.match(r'<section class="page[^"]*" id="page-(\w+)"', parca)
        if not m:
            continue
        for kap in re.findall(r'id="page-(\w+)"', parca)[1:]:
            assert kap not in ev, f"#page-{kap} DOM'da iki kez var"
            ev[kap] = m.group(1)
    for yuzey, bolumler in ab.items():
        assert [b for b, a in ev.items() if a == yuzey] == bolumler, (
            f"{yuzey}: DOM sırası tabloyla ayrışmış — "
            f"DOM {[b for b, a in ev.items() if a == yuzey]}, tablo {bolumler}")


def test_page_sinifi_YALNIZ_bes_yuzeyde():
    """`go()` aktifliği `.page` üzerinden çeviriyor. Birleşen sayfaların kapları `.page` olarak
    kalsaydı gizli bir yüzey 'aktif' kalır ve j/k gezinmesi görünmeyen satırları sayardı."""
    sayfalar = re.findall(r'<section class="page[^"]*" id="page-(\w+)"', INDEX)
    assert sorted(sayfalar) == sorted(YUZEYLER), f"`.page` kapları: {sorted(sayfalar)}"
    assert INDEX.count('class="page active"') == 1, "birden fazla (ya da hiç) açılış yüzeyi"


# =================================================================================================
# 2) GERİ UYUM — eski adresler ÇÖZÜLMEYE DEVAM EDER
# =================================================================================================
def test_route_alias_eski_SAYFALARI_da_cozer():
    """(A) sınıfının birinci yarısı. Yüzeyi kalkmış beş eski sayfa alias almazsa `kosu#adaylar`
    biçimindeki her eski adres go()'nun tanımadığı bir kimliğe düşer ve SESSİZCE varsayılan
    rotaya gider — operatör bağın çalıştığını sanır, yanlış yerdedir."""
    alias = _sozluk("ROUTE_ALIAS")
    for eski, yeni in ESKI_SAYFALAR.items():
        assert alias.get(eski) == yeni, f"eski sayfa {eski} → {alias.get(eski)} (beklenen {yeni})"
    assert set(alias.values()) <= set(YUZEYLER), \
        f"tanınmayan alias hedefi: {sorted(set(alias.values()) - set(YUZEYLER))}"


def test_eski_derin_adresler_capasiyla_birlikte_cozulur():
    """(A) sınıfının ikinci yarısı — ve asıl tehlikeli olan. go() çapayı ÖNCE ayırır, sonra
    alias'ı uygular (`id.split("#")` → `ROUTE_ALIAS[id]`). Yani `portfoy#mutabakat` iki şeye
    birden bağlıdır: alias'ın hedefi VE `mutabakat` çapasının o hedefte gerçekten üretiliyor
    olması. İkisini ayrı ayrı doğru yapıp birlikte yanlış yapmak mümkün."""
    alias = _sozluk("ROUTE_ALIAS")
    bolumler = {b for bl in _alan_bolumleri().values() for b in bl}
    capalar = bolumler | {"failsub"}          # elle yazılmış tek çapa (mutabakat masasının ret bloğu)
    # go() çapayı ayırıp alias'ı SONRA uygular — sıra bozulursa `portfoy#x` hiç çözülmez.
    go = _govde("async function go(id) {", "\nfunction revealActive(")
    assert go.index('id.includes("#")') < go.index("ROUTE_ALIAS[id]"), \
        "go() alias'ı çapadan ÖNCE uyguluyor — `portfoy#mutabakat` biçimi kırılır"
    for adres in ESKI_DERIN_ADRESLER:
        sayfa, _sep, capa = adres.partition("#")
        assert sayfa in alias or sayfa in YUZEYLER, f"{adres}: yüzey çözülemiyor"
        hedef = alias.get(sayfa, sayfa)
        assert hedef in YUZEYLER, f"{adres}: alias tanınmayan yüzeye gidiyor ({hedef})"
        if capa:
            assert capa in capalar, f"{adres}: çapa hiçbir bölümde üretilmiyor"


def test_pano_kendi_icinde_YENI_adres_dilini_konusur():
    """Alias GERİ UYUM içindir, iç kullanım için DEĞİL. Pano kendi içinde eski adı kullanmaya
    devam etseydi alias bir geçiş katmanı değil kalıcı bir ikinci dil olurdu ve hangi adın
    güncel olduğu ölçülemez hâle gelirdi."""
    hedefler = set(re.findall(r'data-act="go" data-a1="([\w#]+)"', APPJS))
    hedefler |= set(re.findall(r'gorunum: "([\w#]+)"', PALETTE))
    hedefler |= set(re.findall(r'gorunumeGec\("([\w#]+)"\)', PALETTE))
    hedefler -= {"${k.hedef}", "${hedef}", "${id}"}
    eskiler = sorted(h for h in hedefler if h.split("#")[0] in ESKI_SAYFALAR)
    assert not eskiler, f"pano kendi içinde eski adresi kullanıyor: {eskiler}"


def test_palet_yuzey_sutunu_ALAN_BOLUMLERI_ile_ayni():
    """Palet bir bilgi mimarisi haritasıdır; yüzey sütunu ayrışırsa komut doğru bölüme gider
    ama altyazısı yanlış yüzeyi söyler — harita bir kez yalan söyleyince bir daha okunmaz."""
    tablo = re.findall(r'^    \["(\w+)", "(\w+)", "', PALETTE, re.M)
    ab = _alan_bolumleri()
    beklenen = [(b, alan) for alan, bl in ab.items() for b in bl]
    assert tablo == beklenen, f"palet tablosu ayrışmış:\n  palet: {tablo}\n  app.js: {beklenen}"
    sayfa_adi = re.search(r"var SAYFA_ADI = \{(.*?)\};", PALETTE, re.S)
    assert sayfa_adi, "SAYFA_ADI tanımlı değil"
    adlar = dict(re.findall(r'(\w+):\s*"([^"]+)"', sayfa_adi.group(1)))
    assert set(adlar) == set(ab), f"SAYFA_ADI yüzey kümesinden ayrışmış: {sorted(adlar)}"


# =================================================================================================
# 3) OLAY YÜZEYLERİ (Tier-4) — dört bölüm, tek çekmece
# =================================================================================================
def test_olay_yuzeyi_siniflari_TAM():
    """Brief'in adlandırdığı beş sınıf ZORUNLU: besleme kopuk/bayat · mutabakat çatışması ·
    kill-switch · bütünlük ihlali · ajan/beyin kotası. `yetki` altıncı olarak eklendi çünkü
    ARMING_READY ve AUTHORITY_CHANGE de alarmdır ve evsiz bir alarm boş çekmece açar."""
    blok = _olay_yuzeyleri()
    bulunan = re.findall(r"^  (\w+): \{$", blok, re.M)
    assert bulunan == OLAY_SINIFLARI, f"olay yüzeyi sınıfları: {bulunan}"


def test_her_olay_yuzeyi_DORT_BOLUMU_de_tasir():
    """(C) sınıfının çivisi. Yön belgesi §3: 'Her biri tek yerde: ne oldu · değerler ŞİMDİ ne ·
    runbook adımları · mevcut eylemler.' Dördünden biri eksikse operatör olay anında yine
    başka bir yere bakmak zorunda kalır — emilmenin bütün amacı buydu."""
    blok = _olay_yuzeyleri()
    for sinif in OLAY_SINIFLARI:
        i = blok.index(f"\n  {sinif}: {{")
        j = blok.index("\n  },", i)
        govde = blok[i:j]
        for alan in ("ad:", "ozet:", "jetonlar:", "neOldu:", "kaynak:",
                     "degerler:", "adimlar:", "eylemler:"):
            assert alan in govde, f"{sinif}: '{alan}' yok — olay yüzeyi yarım"
        assert govde.count("\"") >= 4, f"{sinif}: gövde şüpheli derecede boş"
    # ÇEKMECE GÖVDESİ dört bölümü de NUMARALI başlıkla yazar ve SIRA sabittir: operatör olay
    # anında aynı yerde aynı şeyi bulmalı.
    ciz = _govde("function olayYuzeyiHTML(sinif, ad) {", "\n// TEK KAPI")
    sirali = [ciz.index(b) for b in ("1 · Ne oldu", "2 · Değerler şimdi ne",
                                     "3 · Runbook adımları", "4 · Mevcut eylemler")]
    assert sirali == sorted(sirali), "olay yüzeyinin dört bölümü sırasını kaybetmiş"


def test_olay_yuzeyi_CEKMECE_desenini_yeniden_kullanir():
    """YENİ BİLEŞEN YOK (brief). Aynı `openDrawer` kapısı, aynı odak tuzağı, aynı Esc
    sözleşmesi. İkinci bir modal deseni açmak, klavye ve odak sözleşmesini ikiye bölerdi."""
    ac = _govde("window.olayAc = (ad, segment) => {", "\n// OLAY BAĞI")
    assert ac.count("openDrawer(") == 2, "olayAc çekmece dışında bir yüzey açıyor olabilir"
    assert "class=\"pdrawer\"" in INDEX, "çekmece kabı yok"
    # Bağ TEK yerde üretilir ve `data-act` izin listesinden geçer (CSP: satır içi olay YOK).
    assert 'data-act="olayAc"' in APPJS
    izin = _govde("const EYLEMLER = new Set([", "\n]);")
    assert '"olayAc"' in izin, "olayAc izin listesinde değil — düğme sessizce ölü"
    assert "onclick=" not in _govde("function olayBagi(ad, sinif, segment) {", "\n}", APPJS)


def test_olay_yuzeyi_UYDURMA_yapmaz():
    """Bu yüzeyin en yüksek bahisli kuralı. `docs/RUNBOOK.md` çoğu jeton için 'runbook girdisi
    henüz yazılmadı' diyor; yüzeyin o boşluğu doldurması, olay anında yapılabilecek en pahalı
    yalandır. Ayrıca ölçülemeyen bir değer 0 yazmaz, ADIYLA ölçülemedi der."""
    ciz = _govde("function olayYuzeyiHTML(sinif, ad) {", "\n// TEK KAPI")
    assert "henüz yazılmadı" in ciz, "çözüm boşluğu beyan edilmiyor — uydurma riski"
    assert "ölçülemedi" in ciz, "ölçülemeyen değer için dürüst hâl yok"
    assert "v == null" in ciz, "ölçülemeyen alan sıfıra düşürülüyor olabilir (None ≠ 0)"
    assert "?? 0" not in ciz and "|| 0" not in ciz, "olay yüzeyinde bir alan sıfıra çöküyor"
    # Kotanın kendi jetonu YOK ve bu BEYAN EDİLİR — boş bir liste sessiz bir eksik olamaz.
    assert "bu sınıfın kendi alarm jetonu YOK" in ciz


def test_olay_yuzeyi_TEK_EMIR_YOLUNU_bozmaz():
    """Çekmeceye bir HALT/FLATTEN düğmesi koymak panoda İKİNCİ bir emir yüzeyi açmak olurdu.
    'Mevcut eylemler' yalnız kolun GERÇEKTEN yaşadığı bölüme götürür."""
    blok = _olay_yuzeyleri()
    eylemler = re.findall(r"eylemler:\s*\[(.*?)\]\],", blok, re.S)
    assert len(eylemler) == len(OLAY_SINIFLARI), "her sınıfın eylem listesi okunamadı"
    yuzeyler = set(YUZEYLER)
    for e in eylemler:
        for adres in re.findall(r'"([\w#]+)"\]', e):
            assert adres.split("#")[0] in yuzeyler, f"eylem tanınmayan yüzeye gidiyor: {adres}"
    for yasak in ("opFlatten", "opSoftHalt", "toggleHalt", "opCancelOpen", "alpacaSubmit"):
        assert yasak not in blok, f"olay yüzeyine ikinci bir emir yolu sızmış: {yasak}"


def test_alarmdan_olay_yuzeyine_giden_yol_PANOYU_TERK_ETMEZ():
    """Denetim B14'ün kapanışı: alarm satırı ve sessiz-hat sapması artık dördüncü bir görsel
    dünyaya değil, aynı çekmeceye çıkar."""
    alarm = _govde("function alertsInbox(a) {", "\nwindow.ackAlerts")
    assert "olayBagi(g.token)" in alarm and "/runbook" not in alarm
    sh = _govde("function sessizHat(sh) {", "\nfunction alarmButce(")
    assert "olayBagi(x.ad" in sh and "/runbook" not in sh


# =================================================================================================
# 4) RUNBOOK EMİLİMİ + WORKFLOW EMEKLİLİĞİ — yönlendirme var, dosya duruyor
# =================================================================================================
def test_runbook_html_yonlendirme_birakti_ama_YER_TUTUCULARI_korudu():
    """Dosya bu turda SİLİNMEZ (silme D5'te, bağ denetimiyle) — ama içeriğin taşındığı
    yazılmalı. `meridian/api.py::runbook()` iki yer tutucuyu ARAR ve bulamazsa sessiz boş sayfa
    yerine hata döner; yönlendirme eklerken onları düşürmek rotayı 500'e çevirirdi."""
    for yt in ("<!--RUNBOOK-GOVDE-->", "<!--RUNBOOK-TOC-->"):
        assert yt in RUNBOOK_HTML, f"{yt} yer tutucusu kaybolmuş — /runbook rotası hata döner"
    assert "içeriği panoya taşındı" in RUNBOOK_HTML.lower() or \
           "panoya taşındı" in RUNBOOK_HTML, "yönlendirme notu yok"
    assert "olay yüzeyi" in RUNBOOK_HTML, "yönlendirme NEREYE gidileceğini söylemiyor"
    assert 'href="/#saglik"' in RUNBOOK_HTML, "panoya dönüş bağı yeni yüzeye gitmiyor"


def test_workflow_html_emekli_ve_halefini_adlandiriyor():
    """Statik boru-hattı resmi emekli; halefi ③'ün canlı zaman çizelgesi. Dosya duruyor (silme
    D5) ama bayat olduğunu SÖYLEMELİ — canlı ölçümden beslenmeyen bir resim bunu söylemezse
    güncel sanılır.

    ÇİVİ GÜNCELLENDİ (envanter #26, docs/ENVANTER-DEGER-ESITLIGI-2026-08-22.md): eski çivi
    yalnız "tazelenmiyor" dizgisinin VARLIĞINA bakıyordu; afiş tarih damgalıydı ("2026-07-20
    sürümüdür ve o günden beri …") ve dosya iki onarım turu geçirince (workflow.js 08-12 içerik
    + 08-13 "SAYIYLA YAZILMAZ" düzeltmeleri) İDDİANIN KENDİSİ bayatladı — "emekli ama bazı
    satırları güncel" üçüncü hâl, denetimin en kötü dediği. Kendini tarihleyemeyen statik sayfa
    tarih İDDİA ETMEZ: kalıcı-doğru beyan "canlı ölçümden beslenmez"dir; tarih-damgalı tazelik
    iddiası artık NEGATİF çivilidir."""
    assert "EMEKLİ" in WORKFLOW_HTML, "emeklilik ekranda yazmıyor"
    assert 'href="/#saglik"' in WORKFLOW_HTML, "halefine bağ yok"
    assert "canlı ölçümden beslenmez" in WORKFLOW_HTML, "bayatlık beyan edilmiyor"
    assert "tazelenmiyor" not in WORKFLOW_HTML, (
        "mutlak 'tazelenmiyor' iddiası geri gelmiş — dosya bir kez daha tazelendiğinde afişin "
        "kendisi yalan olur (envanter #26 vakasının aynısı)")
    assert not re.search(r"20\d\d-\d\d-\d\d sürümüdür", WORKFLOW_HTML), (
        "tarih-damgalı sürüm iddiası geri gelmiş — statik sayfa kendi tarihini doğrulayamaz")


def test_canli_zaman_cizelgesi_yuzeyi_kuruldu():
    """workflow.html'in halefi GERÇEK bir bölüm olmalı: kabı, render'ı, soru cümlesi ve palet
    satırı. `HAT_ADIMLARI` liste-VERİdir (şablona gömülü değil) — yani sayılabilir."""
    assert 'id="page-cizelge"' in INDEX
    assert "RENDER.cizelge = async () => {" in APPJS
    assert "cizelge" in _sozluk("EKRAN_SORUSU")
    assert "cizelge" in _alan_bolumleri()["saglik"]
    blok = re.search(r"const HAT_ADIMLARI = \[(.*?)\n\];", APPJS, re.S)
    assert blok, "HAT_ADIMLARI liste-veri değil — adımlar sayılamaz"
    adimlar = re.findall(r'^\s*\["([^"]+)",', blok.group(1), re.M)
    assert len(adimlar) >= 10, f"hat adımları şüpheli derecede az: {adimlar}"


def test_cizelge_ONYEDI_BEKCININ_HEPSINI_kapsar():
    """Bir mekanizmayı çizelgeye koymamak, geciktiğinde operatörün onu hattın neresinde
    arayacağını bilememesi demektir. Kaynak `watchdog.EXPECTED` — ikinci bir liste açılmaz."""
    wd = (SRC / "meridian" / "watchdog.py").read_text()
    blok = re.search(r"EXPECTED: dict\[str, int\] = \{(.*?)\n\}", wd, re.S)
    assert blok, "watchdog.EXPECTED okunamadı"
    beklenen = set(re.findall(r'^\s*"(\w+)":', blok.group(1), re.M))
    assert len(beklenen) >= 17, f"bekçi envanteri şüpheli derecede küçük: {sorted(beklenen)}"
    hat = re.search(r"const HAT_ADIMLARI = \[(.*?)\n\];", APPJS, re.S).group(1)
    kapsanan = set(re.findall(r'"(\w+)"\]\],', hat)) | set(
        m for satir in re.findall(r"\[([^\]]*)\]\],", hat) for m in re.findall(r'"(\w+)"', satir))
    eksik = sorted(beklenen - kapsanan)
    assert not eksik, f"çizelgede evi olmayan bekçi mekanizması: {eksik}"


def test_cizelge_OLCULMEYENI_uydurmaz():
    """Bekçi raporu YALNIZ gecikenleri adlandırır; penceresinde olanlar bir SAYIdır. Yani
    "bu adım 03:12'de koştu" bilgisi bu uçtan GELMİYOR ve çizelge onu uydurmamalı."""
    fn = _govde("function _hatSatiri(ad, ne, mekler, wd) {", "\nRENDER.cizelge")
    assert "kendi bekçi damgası YOK" in fn, "damgasız adım için dürüst hâl yok"
    assert "?? 0" not in fn and "|| 0" not in fn
    ciz = _govde("RENDER.cizelge = async () => {", "\n// ---- PORTFÖY · MUTABAKAT")
    assert "ölçülemedi" in ciz, "teşhis ucu düştüğünde çizelge sessiz kalıyor"
    assert "bir çıkarımdır" in ciz, "'penceresinde' hükmünün kanıt sınırı beyan edilmiyor"


# =================================================================================================
# 5) YİNELENEN ÇİFTLER — aynı gerçek TEK yerde
# =================================================================================================
def test_durum_izgarasi_TEK_yuzeyde():
    """P-çakışmasının kökü: ızgara iki sayfada çiziliyordu çünkü 'sistem şu an nerede?' sorusu
    iki sayfaya bölünmüştü. Sayfalar birleşince `durumIzgarasiCiz` çağrısı ikiden BİRE indi."""
    m = re.search(r"const DURUM_SAYFALARI = new Set\(\[([^\]]*)\]\);", APPJS)
    assert m, "DURUM_SAYFALARI tanımlı değil"
    assert re.findall(r'"(\w+)"', m.group(1)) == ["karar"]


def test_ws_akisinin_TEK_evi_mutabakat_masasi():
    """P5: 'WS akıyor mu?' DÖRT yerde yazılıyordu (HUD çipi · durum kartı · triyaj şeridi ·
    mutabakat satırı). Değerin tek evi mutabakat masasıdır; durum kartı yalnız ANOMALİ hâlinde
    konuşur (o zaman cümle bir tekrar değil, taşıdığı rozetin gerekçesidir)."""
    kart = _govde("function _durumEmirKarti(t, d) {", "\n// ---- ④ POZİSYONLAR")
    assert "mutabakat masasında (tek ev)" in kart, "kart hâlâ değeri tekrarlıyor"
    assert "ayna akışı canlı" not in kart, "sağlıklı hâl ikinci kez yazılıyor"
    assert "akis === false" in kart, "üçüncü hâl (hiç kanıt yok) KOPUK ile aynı kovaya düşüyor"


def test_bekci_rozeti_HUD_tan_dustu():
    """P3: 'Bekçiler ne durumda?' HUD çipi ve sessiz hattın `bekçiler` segmenti aynı `_wd_rep`
    nesnesinden besleniyordu ve çip sağlıklıyken de konuşuyordu. Ayrıntının tam hâli artık
    ③'ün çizelgesinde — kaldırılan çiple birlikte hiçbir bilgi düşmedi."""
    hud = _govde("  hud.innerHTML = [", "\n  ].filter(Boolean).join(\"\");", KOD)
    assert "bekçi" not in hud, "bekçi rozeti HUD'da geri gelmiş — P3 tekilleştirmesi bozuldu"
    sh = _govde("function sessizHat(sh) {", "\nfunction alarmButce(")
    assert "s.ad" in sh, "sessiz hat bekçi segmentini çizmiyor — bilgi gerçekten düşerdi"


def test_ray_ozeti_banttaki_gercekleri_TEKRARLAMAZ():
    """P4 ve P10: nabız tazeliği `#statuspill`de YAŞIYLA, otonomi `#statuspill`de harfle
    duruyordu; ray ikisini de bir kez daha yazıyordu. Ray özeti yüzeyin KENDİ cümlesidir."""
    subs = _govde("  const subs = {", "\n  };", KOD)
    assert "nabız gecikmiş" not in subs, "nabız tazeliği rayda tekrar ediyor"
    assert "ayna SAPMA" not in subs, "ayna sapması rayda tekrar ediyor (P6)"
    assert subs.count('onk("L"') == 1, "otonomi seviyesi rayda birden fazla yerde"
    acct = _govde('    <p class="slab">HESAP</p>', '<p class="slab">GÖRÜNÜM</p>', KOD)
    assert 'onk("L"' not in acct, "otonomi hesap kutusunda da yazıyor — P10 üç kopyaya döner"
    assert "MOD_OLCULEMEDI" in acct, "mod her durumda görünür (Dalga-0 hükmü) — satır düşmüş"


def test_olu_onay_kolu_SILINDI():
    """N1: `pending_count > 0 && autonomy_level >= 1` kolu sistem L0'da olduğu için hiç
    ateşlemedi ve saydığı alan 'onay bekleyen' DEĞİL. 'Bugün ne bekliyor?' sorusunun tek evi
    ① Bugün'ün kartıdır (`inbox_count` + REVIEW kırılımı)."""
    fn = _govde("function spineHTML(t, h, rc, ws) {", "\nfunction nextSessionCard(t) {", KOD)
    assert "autonomy_level >= 1" not in fn, "ölü onay kolu geri gelmiş"
    assert "t.pending_count" not in fn, "şerit hâlâ yanlış adlandırılmış sayacı okuyor"
    genel = _govde("RENDER.bugun = async () => {", "\n// ALARM BÜTÇESİ TEK SATIR")
    assert "inbox_count" in genel, "bekleyen onayın tek evi de boşalmış"

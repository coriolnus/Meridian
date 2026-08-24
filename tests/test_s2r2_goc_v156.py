"""v156 — S2R-2: içerik göçü, Öğrenme birleşimi, "soruya hizmet" denetimi ve emekli listesi.

BU DOSYANIN ÖLÇTÜĞÜ KUSUR SINIFI: **göçün sessiz kaybı**. S2R-1 kabuğu kurmuştu ve testi
"hiçbir görünüm düşmedi mi?" diye soruyordu. S2R-2'de risk bir kademe derinleşiyor, çünkü artık
GÖRÜNÜMLER değil BÖLÜMLER taşınıyor ve üç görünüm ikiye BÖLÜNÜYOR (onaylar, intraday, operasyon).
Bölme, birleştirmeden daha tehlikelidir:

  A) YARIM TAŞIMA — bir görünümün yarısı yeni evine gider, öteki yarısı eski gövdede unutulur.
     Hiçbir şey kırmızı yanmaz: iki sayfa da çizilir, biri eksiktir ve eksikliği yalnız o veriyi
     arayan kişi fark eder.
  B) ÖKSÜZ TABLO — taşınırken bir kart silinir ve okuduğu API alanının TEK okuyucusu oydu. Arka
     uç o alanı üretmeye devam eder; kimse okumaz (YASA-6 ihlali, HTTP→DOM katmanında ve statik
     Python grafının GÖREMEDİĞİ yerde).
  C) YANLIŞ ADRES — sessiz-hat çipi, palet komutu ya da `data-a1` hedefi taşınan bölümün ESKİ
     adına bakar. Alias sayesinde doğru sayfaya gidilir ama aranan bölüm bulunamaz; operatör
     aramayı bırakır. Yanlış bağ, ölü bağdan pahalıdır.
  D) YENİ DEPO — "birleşim" adı altında bir sayfaya on bölüm yığılır ve okuma sırası kaybolur.
     Hiyerarşi ancak SIRA ölçülebilirse bir sözleşmedir.

TESTLER KAYNAĞA BAKAR (repo deseni: v139/v151/v152/v154/v155). Tarayıcı ve yerel sunucu YOK
(CLAUDE.md §5): dosyalar okunur. Tek istisna `codelaw.artifact_graph`, o da saf statik tarama.
"""
from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
WEB = SRC / "meridian" / "web"
APPJS = (WEB / "app.js").read_text()
INDEX = (WEB / "index.html").read_text()
PALETTE = (WEB / "palette.js").read_text()
ADR = (SRC / "docs" / "UIUX-S2R-REDESIGN.md").read_text()

# Yorum satırları çıkarılmış hâl (v154/v155 deseni): bir kuralın GEREKÇESİNİ anlatan yorum, o
# kuralın ihlali sanılmamalı — "artık şuna bakmıyoruz" diye yazılmış bir cümle, tam da aranan
# dizgiyi içerir.
KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))
CSS = re.search(r"<style>(.*?)</style>", INDEX, re.S).group(1)

# ---- ADR'NİN HEDEF IA'SI, BÖLÜM DÜZEYİNDE ---------------------------------------------------
# Bu sözlük testin KENDİ iddiasıdır ve ADR'nin §"Hedef IA" + S2R-2 iş emrinin eşlemesinden
# yazılmıştır. Kaynaktan TÜRETİLMEZ — türetilseydi test "kod kendine uyuyor mu?" diye sorardı ve
# bir bölümü yanlış eve taşımak testi yeşil bırakırdı.
# SIRA DA İDDİANIN PARÇASI: "en kritik üstte" ancak sıra ölçülebilirse bir sözleşmedir.
# D2-b GÜNCELLEMESİ (2026-08-07): yön belgesi §3'ün beş yüzeyi bağlayıcı oldu ve iki birleşme
# yapıldı — kosu+portfoy → karar, veri+gozetim → saglik. İDDİA TAŞINDI, SÖKÜLMEDİ: sıra hâlâ
# testin KENDİ iddiasıdır ve kaynaktan türetilmez. Yeni sıra yüzeyin sorusuna hizmet sırasıdır
# (② ne önerildi → neden geçti → onay → ne oldu → mutabakat → seans-içi → birikim;
#  ③ önce bozulan → hattın çizelgesi → hattın iç sağlığı → evren → akış).
# 2026-08-24 (operatör) — BEŞ YÜZEY YEDİ OLDU, onaylanan maketin kenar çubuğu gruplamasıyla.
# Eski tek "Karar" alanı SEKİZ bölüm taşıyordu ve içinde ÜÇ AYRI soru vardı; her soru artık
# kendi yüzeyinde ve sırası o sorunun cevap sırası:
#   ② Portföy       kitap → mutabakat → seans-içi emir     ("kitap nerede duruyor?")
#   ③ Karar zinciri aday → kapı → onay                     ("neden geçti ya da geçmedi?")
#   ④ Analiz        toplulaştırma → birikim defteri        ("ne birikti ve nerede?")
# Analiz operatörün ADIYLA istediği sekmedir; keşif (kırılım) önce, defter sonra gelir —
# keşif soruyu doğurur, defter cevabı taşır.
ADR_HARITASI: dict[str, list[str]] = {
    "portfoy":  ["brifing", "mutabakat", "intraemir"],
    "karar":    ["adaylar", "kapilar", "onaylar"],
    "analiz":   ["topviews", "performans"],
    "saglik":   ["operasyon", "cizelge", "veriboru", "market", "intraday"],
    "ogrenme":  ["karne", "golge", "bilesenic", "hermes", "ajan", "skiller", "hafiza"],
    "kilitler": ["mudahale", "ayarlar"],
}
# Eski beş ALAN SAYFASI — bugün yalnız birer alias (kapları yok, yüzeyleri birleşti).
# 2026-08-24: `portfoy` BU LİSTEDEN ÇIKTI — artık bir alias değil, kendi DOM kabı olan
# gerçek bir yüzey (maket gruplaması). Eski `portfoy#mutabakat` bağları hâlâ çalışır ve
# çapası korunur; değişen, hedefin artık gerçekten orada olması.
ESKI_SAYFALAR = {"genel": "bugun", "kosu": "karar",
                 "veri": "saglik", "gozetim": "saglik"}
ESKI_GORUNUMLER = ["brifing", "performans", "adaylar", "onaylar", "market", "intraday",
                   "ajan", "hermes", "skiller", "hafiza", "operasyon", "ayarlar"]
# S2R-2'de doğan sekiz bölüm. Hiçbiri bir eski yer imi DEĞİL: alias almazlar (bkz. ROUTE_ALIAS
# yorumu), çapaları `<sayfa>#<bölüm>` biçiminde çalışır.
YENI_BOLUMLER = ["veriboru", "kapilar", "mutabakat", "intraemir",
                 "karne", "golge", "bilesenic", "mudahale", "cizelge"]


def _sozluk(ad: str) -> dict[str, str]:
    blok = re.search(r"const %s = \{(.*?)\};" % ad, APPJS, re.S)
    assert blok, f"{ad} tanımlı değil"
    return dict(re.findall(r"(\w+):\s*\"([^\"]+)\"", blok.group(1)))


def _alan_bolumleri() -> dict[str, list[str]]:
    blok = re.search(r"const ALAN_BOLUMLERI = \{(.*?)\n\};", APPJS, re.S)
    assert blok, "ALAN_BOLUMLERI tanımlı değil — göç kaydı kaybolmuş"
    return {alan: re.findall(r'"(\w+)"', liste)
            for alan, liste in re.findall(r"^\s*(\w+):\s*\[([^\]]*)\]", blok.group(1), re.M)}


def _dom_evleri() -> dict[str, tuple[str, int]]:
    """kap kimliği → (içinde bulunduğu alan sayfası, o sayfadaki sırası)."""
    ana = INDEX[INDEX.index('<main id="main">'):INDEX.index("</main>")]
    ev: dict[str, tuple[str, int]] = {}
    for parca in re.split(r'(?=<section class="page)', ana):
        m = re.match(r'<section class="page[^"]*" id="page-(\w+)"', parca)
        if not m:
            continue
        for i, kap in enumerate(re.findall(r'id="page-(\w+)"', parca)[1:]):
            ev[kap] = (m.group(1), i)
    return ev


def _govde(baslangic: str, bitis: str, kaynak: str = APPJS) -> str:
    i = kaynak.index(baslangic)
    return kaynak[i:kaynak.index(bitis, i)]


def _yorumsuz(s: str) -> str:
    """Yorum satırlarını at. GEREKÇE, İHLAL SANILMAMALI: "artık RENDER.operasyon() çağırmıyoruz"
    diye yazılmış bir cümle, tam da aranan dizgiyi içerir (v154/v155 deseni)."""
    return "\n".join(l for l in s.splitlines() if not l.lstrip().startswith("//"))


# =================================================================================================
# 1) GÖÇ HARİTASI — bölüm → sayfa, ADR'ye BİREBİR
# =================================================================================================
def test_bolum_sayfa_haritasi_ADR_ile_birebir():
    """Kusur A'nın en geniş ağı: bir bölüm yanlış eve taşınırsa hem kaynak sayfa eksilir hem
    hedef sayfa kendi sorusuna hizmet etmeyen bir blok kazanır. İki tarafta da sessiz."""
    assert _alan_bolumleri() == ADR_HARITASI, (
        "ALAN_BOLUMLERI ADR eşlemesinden ayrışmış:\n"
        f"  kod: {_alan_bolumleri()}\n  ADR: {ADR_HARITASI}")


def test_her_bolumun_kabi_render_i_ve_sorusu_var():
    """Bir bölüm ÜÇ şeyin buluşmasıdır: DOM kabı, render ve soru cümlesi. Üçünden biri eksikse
    bölüm bir vaattir — sayfada yer tutar, hiçbir şey yazmaz."""
    sorular = _sozluk("EKRAN_SORUSU")
    renderlar = set(re.findall(r"^RENDER\.(\w+) = ", APPJS, re.M))
    ev = _dom_evleri()
    for alan, bolumler in ADR_HARITASI.items():
        for b in bolumler:
            assert b in ev, f"#page-{b} kabı hiçbir alan sayfasının içinde değil — içerik kayıp"
            assert b in renderlar, f"RENDER.{b} yok — bölüm çizilemez"
            assert b in sorular, f"{b}: soru cümlesi yok ('ekrana dök' yasağının çıpası)"


def test_dom_sirasi_tabloyla_ayni():
    """Kusur D: sıra iki yerde tutuluyor (index.html'in kap dizilimi + ALAN_BOLUMLERI). Ayrışsalar
    çizim sırası ile OKUMA sırası farklı olur — operatör "en kritik üstte" sanır, değildir."""
    ev = _dom_evleri()
    for alan, bolumler in ADR_HARITASI.items():
        dom = [b for b, (a, _) in sorted(ev.items(), key=lambda kv: kv[1][1]) if a == alan]
        assert dom == bolumler, f"{alan}: DOM sırası {dom}, tablo {bolumler}"


def test_hicbir_bolum_kabi_page_sinifi_tasimaz():
    """`go()` aktifliği `.page` üzerinden çeviriyor. Yirmi bölüm kabından biri `.page` olsaydı
    gizli bir bölüm 'aktif' kalır ve j/k gezinmesi görünmeyen satırları sayardı."""
    sayfalar = re.findall(r'<section class="page[^"]*" id="page-(\w+)"', INDEX)
    assert sorted(sayfalar) == sorted(["bugun"] + list(ADR_HARITASI)), \
        f"`.page` taşıyan kaplar beş yüzeyle aynı değil: {sorted(sayfalar)}"


def test_eski_on_iki_render_SILINMEDI():
    """ADR geri-dönüş sözleşmesi: eski görünüm fonksiyonları silinmez. S2R-2 üçünü BÖLDÜ ama
    hiçbirinin adını düşürmedi — `git revert` bir tek commit'lik iş olarak kalır."""
    for ad in ESKI_GORUNUMLER:
        assert f"RENDER.{ad} = " in APPJS, f"RENDER.{ad} silinmiş — içerik ve geri dönüş kaybı"


def test_yeni_bolumler_alias_almaz():
    """ALIAS BİR ESKİ-HASH SÖZLÜĞÜDÜR. Yeni bölümlere alias vermek, hiç var olmamış bir
    `#mutabakat` yer imini destekliyormuş gibi yapmak olurdu; ve alias listesi bir kez "bölüm
    listesi" sanılmaya başlayınca eski hash'lerin hangileri olduğu ölçülemez hâle gelir."""
    alias = _sozluk("ROUTE_ALIAS")
    beklenen = set(ESKI_GORUNUMLER) | set(ESKI_SAYFALAR)
    assert sorted(alias) == sorted(beklenen), \
        f"alias listesi eski adres kümesinden ayrışmış: {sorted(set(alias) ^ beklenen)}"
    for b in YENI_BOLUMLER:
        assert b not in alias, f"{b} yeni bir bölüm, eski bir yer imi değil — alias almamalı"


def test_alias_hedefi_kabin_GERCEKTEN_durdugu_sayfadir():
    """Kusur C'nin en sinsi biçimi: alias var, sayfa açılıyor, içerik BAŞKA sayfada. S2R-2'de
    `onaylar` ev değiştirdi (kosu → portfoy) ve alias onunla birlikte taşınmak ZORUNDAYDI."""
    alias = _sozluk("ROUTE_ALIAS")
    ev = _dom_evleri()
    for eski, hedef in alias.items():
        if eski in ESKI_SAYFALAR:
            # SAYFA ALIASI (D2-b): kabı yok — yüzeyi birleşti. Ölçülen şey hedefin GERÇEK bir
            # `.page` olması; çapa (`kosu#adaylar`) go()'nun çapa dalıyla ayrıca çözülür ve
            # aşağıdaki `test_ic_hedeflerin_HEPSI_cozulebilir` onu ölçer.
            assert ESKI_SAYFALAR[eski] == hedef, f"sayfa alias'ı kaymış: {eski} → {hedef}"
            assert f'id="page-{hedef}"' in INDEX, f"sayfa alias'ı {eski} → {hedef} boşa gidiyor"
            continue
        assert eski in ev, f"#page-{eski} kabı hiçbir alan sayfasının içinde değil"
        assert ev[eski][0] == hedef, (
            f"alias {eski} → {hedef} diyor ama kap {ev[eski][0]} sayfasının içinde")


# =================================================================================================
# 2) BÖLÜNMELER — onaylar / intraday / operasyon
# =================================================================================================
def test_onaylar_adaylardan_AYRILDI():
    """S2R-1'in birinci beyanlı borcu. Kuyruk `#page-adaylar`ın İÇİNDEYDİ ve `RENDER.adaylar`
    onu kendi gövdesinden çağırıyordu; ikisi de kırılmadan alias Portföy'e bakamazdı."""
    ev = _dom_evleri()
    assert ev["onaylar"][0] == "karar", "onay kuyruğu kendi kabında değil"
    assert ev["adaylar"][0] == "karar"
    adaylar = _govde("RENDER.adaylar = async () => {", "\nfunction planRowFull(p) {")
    assert "RENDER.onaylar()" not in adaylar, \
        "adaylar hâlâ onaylar'ı kendi gövdesinden çağırıyor — sıra gizli kalır, taşınamaz"
    assert _sozluk("ROUTE_ALIAS")["onaylar"] == "karar"


def test_intraday_akis_ve_emir_olarak_bolundu():
    """S2R-1'in ikinci beyanlı borcu (ADR: "akış→Veri, emir→Portföy").

    BÖLÜNMENİN TESTİ PARÇA SAYISI DEĞİL, PARÇALARIN NEREYE GİTTİĞİ: `intraParcalar` beş kart
    üretir; akış yarısı (s3+s4) Veri'de, emir yarısı (s1+s2+s5) Portföy'de yazılır. Aynı kart
    ikisinde birden yazılsaydı operatör aynı tabloyu iki sayfada iki kez okurdu."""
    assert "async function intraParcalar()" in APPJS, "intraday tek gövde olarak duruyor"
    ev = _dom_evleri()
    # 2026-08-24: emir yarısının evi ② PORTFÖY oldu (maket gruplaması) — "silahlanma ve
    # gölge icra" kitabın hâliyle aynı soruyu cevaplıyor, kapının gerekçesiyle değil.
    # ~~`ev["intraemir"][0] == "karar"`~~ İKİYE BÖLÜNME iddiası AYNEN duruyor: akış ③ Sağlık'ta,
    # emir ② Portföy'de — ikisi AYRI yüzeyde, ki bölünmenin kazancı ölçülebilsin.
    assert ev["intraday"][0] == "saglik" and ev["intraemir"][0] == "portfoy"
    akis = _govde("RENDER.intraday = async () => {", "\n// EMİR / SİLAHLAMA YARISI")
    emir = _govde("RENDER.intraemir = async () => {", "\n};")
    assert re.search(r"p\.s3 \+ p\.s4", akis), "akış yarısı s3+s4 yazmıyor"
    assert re.search(r"p\.s1 \+ p\.s2 \+ p\.s5", emir), "emir yarısı s1+s2+s5 yazmıyor"
    for parca in ("p.s1", "p.s2", "p.s5"):
        assert parca not in akis, f"{parca} iki sayfada birden çiziliyor — tekrar"
    for parca in ("p.s3", "p.s4"):
        assert parca not in emir, f"{parca} iki sayfada birden çiziliyor — tekrar"
    # ARM düğmesi EMİR yarısında: bir emir kapısının evi kitap sayfasıdır.
    assert 'data-act="intradayArm"' in _govde(
        "async function intraParcalar()", "\n  // ---- 2) Son intraday ölçümleri ----")


def test_operasyon_parcalandi_ve_HER_PARCA_bir_eve_dustu():
    """Eski `RENDER.operasyon` on dokuz kart basıyordu ve hiçbiri o sayfanın soru cümlesine
    hizmet etmiyordu. Parçalar `opParcalar()`ta üretilir, sayfalara orada dağıtılır.

    ÖLÇÜM: üretilen HER anahtar en az bir yerde YAZILMALI. Bir parçayı üretip hiçbir sayfaya
    koymamak, kartı silmekle aynı sonucu verir ama kodda VARMIŞ gibi durur — göçün en sessiz
    kaybı budur."""
    assert "async function opParcalar() {" in APPJS
    ret = re.search(r"return \{ alarm: alarmButce\(d\.alarm_butcesi\),(.*?)\};", APPJS, re.S)
    assert ret, "opParcalar bir parça sözlüğü döndürmüyor"
    anahtarlar = {"alarm"} | set(re.findall(r"\b(s\w+)\b", ret.group(1)))
    tuketiciler = _govde("RENDER.operasyon = async () => {", "\n// ==========")
    tuketiciler += APPJS[APPJS.index("RENDER.mutabakat = async () => {"):]
    for k in sorted(anahtarlar):
        assert re.search(r"[p|op]\.%s\b" % re.escape(k), tuketiciler), \
            f"opParcalar '{k}' üretiyor ama hiçbir sayfa yazmıyor — sessiz kayıp"


def test_alarm_gelen_kutusu_ve_olay_gunlugu_gozetimde():
    """ADR Gözetim: "alarm gelen kutusu (runbook bağlı) … olay günlüğü". İkisi de Bugün'ün
    (şimdi Portföy) içindeydi: alarmın iki evi vardı ve ikisi de yarımdı."""
    brifing = _govde("RENDER.brifing = async () => {", "\nfunction staleBits(p) {")
    gozetim = _govde("RENDER.operasyon = async () => {", "\n// ---- PORTFÖY · MUTABAKAT")
    for kanca in ('id="bp-alerts"', 'id="bp-events"'):
        assert kanca not in brifing, f"{kanca} hâlâ Portföy'ün kitap bölümünde"
        assert kanca in gozetim, f"{kanca} Gözetim'e taşınmamış"
    assert 'j("/api/alerts")' in gozetim and 'j("/api/events")' in gozetim, \
        "gelen kutusu/olay akışı uçları taşınmamış — kutu boş kalır"


def test_performans_karne_yarisi_ogrenmeye_gitti():
    """"Öğreniyor mu?" ile "ne birikti?" iki AYRI sorudur ve tek gövdede ikisi de yarım kalıyordu.
    Kırılım tabloları (rejim/araç) Portföy'de dururken kimse onları öğrenme kanıtı okumuyordu."""
    perf = _govde("RENDER.performans = async () => {", "\n// ---- ÖĞRENME · KARNE")
    karne = _govde("RENDER.karne = async () => {", "\n// ---- BOYUT TAVANI")
    assert "Piyasa havasına göre kırılım" in karne and "Piyasa havasına göre kırılım" not in perf
    assert "Hangi araç ne kadar isabetli" in karne and "Hangi araç ne kadar isabetli" not in perf
    assert "Para eğrisi (paper)" in perf and "Para eğrisi (paper)" not in karne
    assert "riskCard(" in perf, "boyut tavanı/kuyruk riski Portföy'den düşmüş"
    assert "tradeRows(" in perf, "kapanmış işlem defteri Portföy'den düşmüş"


def test_karne_karti_TEK_yerde():
    """Dört sayaç (yayınlanan/terfi/geri alınan/ölçülen) iki bölümde birden çizilseydi aynı
    hüküm iki kez okunur ve biri sessizce bayatlardı."""
    assert KOD.count("Öğreniyor mu? — dürüst karne") == 2, (
        "karne başlığı beklenen iki yerde değil (biri 'ölçülemedi' hâli, biri gerçek kart)")
    hermes = _govde("RENDER.hermes = async () => {", "\nwindow.applySkillRec")
    assert "Öğreniyor mu?" not in hermes, "karne kartı hâlâ Hermes bölümünün ortasında"


# =================================================================================================
# 3) ÖĞRENME BİRLEŞİMİ — hiyerarşi ve katman erimesi
# =================================================================================================
def test_ogrenme_hiyerarsi_sirasi():
    """ADR Öğrenme: "karne, gölge kollar, bileşen-IC+EB, hipotez/sprint, K-defteri". Sıra bir
    zevk meselesi değil: hüküm (karne) önce gelmezse sayfa bir ölçüm yığınına döner ve
    "makine ne öğreniyor?" sorusu yedi bölüm sonra cevaplanır."""
    assert _alan_bolumleri()["ogrenme"] == ADR_HARITASI["ogrenme"]
    sira = _alan_bolumleri()["ogrenme"]
    assert sira[0] == "karne", "hüküm ilk sırada değil"
    assert sira.index("golge") < sira.index("bilesenic") < sira.index("hermes"), \
        "gölge kollar → bileşen-IC → beyin/sprint sırası bozulmuş"
    assert sira.index("hermes") < sira.index("ajan"), "sprint hipotez defterinden sonra kalmış"
    assert sira[-2:] == ["skiller", "hafiza"], "beceriler ve dersler en altta değil"


def test_bolum_basligi_TEK_kalipta_ve_kart_icinde_kart_yok():
    """Kusur D'nin görsel hâli: her bölüm kendi `.slabel` + `<h1>` + `.subline` üçlüsünü
    basıyordu; yedi bölümlü Öğrenme'de aynı ritim yedi kez tekrarlanıyordu. Kalıp artık tek."""
    assert "function bolumBasHTML(id, baslik, altyazi)" in APPJS
    fn = _govde("function bolumBasHTML(id, baslik, altyazi) {", "\n}")
    assert '<h2 class="ph"' in fn, "bölüm başlığı h2 değil — sayfada ikinci bir h1 doğar"
    assert 'id="${esc(id)}"' in fn, "bölüm başlığı çapa taşımıyor — iç hedefler bölüme inemez"
    assert "soruCumlesi(id)" in fn, "bölüm başlığı denetim çıpasını basmıyor"
    # Bölüm gövdeleri artık kendi `<h1>`ini basmıyor: tek h1 alan sayfasınındır.
    assert "<h1 class=\"greet quiet\">" not in KOD, "eritilmesi gereken selamlama h1'i duruyor"
    assert '<h1 class="ph">Öğrenme.' not in KOD, "eylem şeridinin h1'i eritilmemiş"
    assert ".bolum-bas{" in CSS, "bölüm başlığı kalıbının CSS'i yok"


def test_ogrenme_eylem_seridi_bir_BOLUM_degil():
    """Şerit bir soruya cevap vermez, bir iş BAŞLATIR: soru cümlesi yok, `.alan-bolum` değil.
    Bölüm sayılsaydı "her bölümün bir sorusu var" kuralı ya yalan olurdu ya uydurma bir cümle
    doğurdu."""
    assert 'id="ogrenme-eylem"' in INDEX
    m = re.search(r'<div id="ogrenme-eylem"></div>', INDEX)
    assert m, "eylem şeridi kabı yok"
    assert "ogrenme-eylem" not in str(_alan_bolumleri())
    assert 'class="alan-bolum" id="page-ogrenme-eylem"' not in INDEX


def test_ogrenme_alt_render_zinciri_sokuldu():
    """`RENDER.ajan` hermes+skiller+hafiza'yı kendi gövdesinden çağırıyordu; sıra o gövdede
    gizliydi ve `Promise.all` üçünü PARALEL koşuyordu (recReset zincirine bağlı yüzeylerde
    yarış). Sırayı artık yalnız ALAN_BOLUMLERI söyler, çizimi alanSayfasi SIRAYLA yapar."""
    ajan = _govde("RENDER.ajan = async () => {", "\nfunction disaAktarHTML()")
    for cagri in ("RENDER.hermes()", "RENDER.skiller()", "RENDER.hafiza()"):
        assert cagri not in ajan, f"ajan hâlâ {cagri} çağırıyor — sıra gizli kalır"
    assert "await RENDER[ad]()" in _govde("function alanSayfasi(id, bolumler) {",
                                          "\n// ---- S2R-2 · BÖLÜM → SAYFA")


# =================================================================================================
# 4) "SORUYA HİZMET" DENETİMİ — emekli/indirilen bölümler ve OKUYUCU KORUNUMU
# =================================================================================================
# Emeklilik kuralı (YASA-6): bölüm SİLİNMEZ, detay katmanına iner. Her satır: (arayacağımız
# başlık parçası, o bloğun korunan tek-okuyucu kanıtı).
INDIRILENLER = [
    ("Geçmiş sinyaller · denetim izi", "L.plans_shown"),
    ("Ham tarama çıktısı",             "L.candidates_shown"),
    ("Yedek anahtar havuzu",           'data-act="addPoolKey"'),
    ("Hermes entegrasyonları",         "it.tool_use"),
    ("Dışa aktarım · teşhis paketi",   "/api/debug_export"),
    ("Intraday · Faz 4a gözlem özeti", "bf2.running"),
]


def test_indirilen_bolumler_SILINMEDI_details_e_indi():
    """Kusur B'nin doğrudan panzehiri. "Soruya hizmet etmiyor" hükmü bir SİLME emri DEĞİL: bu
    bloklar okudukları alanların tek okuyucusu ve silinmeleri arka uçta öksüz bir tablo bırakır.
    Mertebeleri düşer — varsayılan-kapalı `<details>` — ve gerekçe satırın kendisinde durur."""
    assert "function detayKatmani(baslik, neden, govde)" in APPJS
    fn = _govde("function detayKatmani(baslik, neden, govde) {", "\n}")
    assert "<details" in fn and "<summary>" in fn, "detay katmanı katlanabilir değil"
    assert "open" not in re.search(r"<details class=\"([^\"]+)\"", fn).group(1), \
        "detay katmanı varsayılan olarak AÇIK — indirim gerçekleşmemiş"
    assert "dk-neden" in fn, "indirim gerekçesi ekranda yazılı değil"
    for baslik, kanit in INDIRILENLER:
        assert baslik in APPJS, f"{baslik}: indirilen blok kaynakta yok — SİLİNMİŞ olabilir"
        # OKUYUCU KORUNUMU (emeklilik kuralının şartı): bloğun okuduğu alan/uç hâlâ kaynakta.
        # Başlığı bırakıp gövdeyi boşaltmak, silmekle aynı sonucu verir ama kodda VARMIŞ görünür.
        assert kanit in APPJS, f"{baslik}: korunması gereken okuyucu ({kanit}) kaybolmuş"


def test_indirilen_her_blok_bir_detayKatmani_cagrisinda():
    """Başlığın kaynakta durması yetmez: `<details>` sarmalayıcısına GERÇEKTEN girmiş olmalı.
    Aksi hâlde "indirdik" bir iddia, testi de bir temenni olurdu."""
    cagrilar = re.findall(r'detayKatmani\(\s*[`"]([^`"]+)[`"]', APPJS)
    for baslik, _ in INDIRILENLER:
        assert any(baslik in c for c in cagrilar), \
            f"{baslik} bir detayKatmani() çağrısında değil: {cagrilar}"


def test_disa_aktarim_ogrenmeden_kilitlere_tasindi():
    """CSV/özet/durum-yedeği/teşhis-zip/bildirim-testi "makine ne öğreniyor?" sorusuna hizmet
    etmiyordu. TAŞINDI (silinmedi): altı ucun ve /halt sayfasının TEK yüzeyi buydu."""
    ajan = _yorumsuz(_govde("RENDER.ajan = async () => {", "\nfunction disaAktarHTML()"))
    ayarlar = APPJS[APPJS.index("RENDER.ayarlar = async () => {"):]
    for uc in ("/api/report.csv", "/api/digest", "/api/state/snapshot", "/api/debug_export"):
        assert uc not in ajan, f"{uc} hâlâ Öğrenme'de"
    assert "disaAktarHTML()" in ayarlar, "dışa aktarım kutusu Kilitler'de çizilmiyor"
    for uc in ("/api/report.csv", "/api/digest", "/api/digest/weekly", "/api/state/snapshot",
               "/api/debug_export", "/halt"):
        assert uc in APPJS, f"{uc} göç sırasında düşmüş — uç öksüz kalır"
    assert 'data-act="notifyTest"' in APPJS, "bildirim testi düğmesi düşmüş"


def test_hicbir_uc_ve_alan_okumasi_dusmedi():
    """ÖKSÜZ TABLO TARAMASI · HTTP KATMANI. Göç sırasında bir kart silindiğinde arka uç o alanı
    üretmeye devam eder ve statik Python grafı bunu GÖREMEZ (okuma JS'te). Bu yüzden burada
    panonun okuduğu uçların ve alan adlarının TAMAMI çivili: liste yalnız BÜYÜYEBİLİR.

    ÇİVİ S2R-2 GÖÇÜ ÖNCESİNDEN (HEAD) ölçüldü ve hem uç kümesi hem alan-okuma kümesi göç
    sonrasında AYNEN korundu (kayıp: 0)."""
    # Pano İKİ dosyadan sürülüyor: app.js ve palette.js (runbook/workflow/landing bağları
    # paletindir). Yalnız birine bakmak, diğerinden düşen bir ucu görmezden gelmek olurdu.
    uclar = set(re.findall(r'["\'](/(?:api/[\w./-]+|halt|runbook|workflow|landing))["\']',
                           APPJS + PALETTE))
    zorunlu = {
        "/api/today", "/api/summary", "/api/hermes", "/api/signals", "/api/market",
        "/api/diagnostics", "/api/agent", "/api/performance", "/api/alpaca", "/api/secrets",
        "/api/alerts", "/api/events", "/api/approvals", "/api/memory", "/api/skills",
        "/api/report.csv", "/api/digest", "/api/digest/weekly", "/api/state/snapshot",
        "/api/debug_export", "/api/notify/test", "/api/intraday-arm", "/api/broker_reject/ack",
        "/api/control/learn_halt", "/api/control/cancel_open", "/api/sprint/start",
        "/api/sprint/stop", "/api/hermes/reflect", "/api/hermes/backfill", "/api/hermes/pool_key",
        "/api/skills/revision", "/api/skills/apply", "/api/alpaca/submit_armed",
        "/halt", "/runbook", "/workflow", "/landing",
    }
    assert zorunlu <= uclar, f"göçte düşen uç: {sorted(zorunlu - uclar)}"
    # Bölüm başına en az bir "sahip" tablo/alan: bir bölümün taşınırken içinin boşalması.
    sahipler = {
        "mutabakat": ["hwm_pairs", "failed_submissions", "partial_fills", "force_sync"],
        "kapilar":   ["blackout_radar", "gk.plans", "arming"],
        "veriboru":  ["quarantine", "ledgers", "hotstate", "marketstream"],
        "intraemir": ["shadow", "vs_eod", "decisions_written"],
        "karne":     ["per_regime", "per_skill", "calibration_scatter", "outcomes_measured"],
        # ÇİVİ TAŞINDI (S2R-3, 2026-08-02): "Gölge-varyant portföyleri" bu satırda `karne_ek`
        # altındaydı ve bu, S2R-2'nin BEYANLI BORCUNU kaydediyordu — blok Hermes karnesi kartının
        # bir alt başlığıydı ve göç sözleşmesi ("bölüm taşı, kart gövdesi yeniden yazma") onu
        # ayırmaya izin vermiyordu. Cila turu gövdeyi böldü; blok artık `golge` bölümünün kendi
        # kartı. Çivi SİLİNMEDİ, ev değiştirdi — silinseydi tablo bir daha hiç izlenmezdi.
        # (Alanların TAM listesi ve bölünmenin okuyucu korunumu: test_s2r3_cila_v160.)
        "golge":     ["trend_kitabi", "shadow_variants", "Gölge-varyant portföyleri"],
        "karne_ek":  ["MAE · stopun kör ikizi", "improvement_proposals"],
        "bilesenic": ["component_ic", "score_calibration_history", "prediction_hit",
                      "benchmark_relative", "regime_edge"],
        "mudahale":  ["opSoftHalt", "opCancelOpen", "opFlatten", "opLearnHaltToggle"],
    }
    for bolum, alanlar in sahipler.items():
        for a in alanlar:
            assert a in APPJS, f"{bolum} bölümünün okuduğu '{a}' kaynaktan düşmüş — öksüz tablo"


def test_codelaw_artefakt_grafi_ihlalsiz():
    """ÖKSÜZ TABLO TARAMASI · DOSYA KATMANI. `codelaw.artifact_graph` her artefakt için
    "başka bir modül okuyor mu?" diye sorar. Bu tur panoya dokundu, arka uca değil — ama bir
    göç sırasında "artık okumuyoruz" diye bir Python okuyucusunun da silinmesi tam olarak
    beklenen kaza sınıfıdır. Tarama YEŞİL olmalı ve tarayıcının kendi körlüğü (`unscanned`)
    de boş olmalı: sıfır-ihlal iddiasının şartı budur."""
    import sys
    sys.path.insert(0, str(SRC))
    from meridian import codelaw
    g = codelaw.artifact_graph("meridian")
    assert g["violations"] == [], f"beyansız öksüz artefakt: {g['violations']}"
    assert g["stale_sinks"] == [], f"beyanı bayatlamış sink: {g['stale_sinks']}"
    assert not codelaw.UNSCANNED, f"tarayıcı bazı dosyaları okuyamadı: {codelaw.UNSCANNED}"


# =================================================================================================
# 5) İÇ HEDEF YÖNLENDİRMELERİ (S2R-1'in beyanlı borcu)
# =================================================================================================
def test_sessiz_hat_cipleri_BOLUM_capasina_gider():
    """Şeridin her çipi bir ADRESTİR. S2R-1'de adresler eski görünüm adlarıydı; alias doğru
    sayfaya götürüyordu ama sayfanın BAŞINA — beş bölümlük bir Portföy'de "3 emir reddedildi"
    çipi operatörü aradığı tablodan üç ekran uzağa bırakıyordu."""
    fn = _govde("function spineHTML(t, h, rc, ws) {", "\n// ---- SIRADAKİ SEANS")
    hedefler = set(re.findall(r'"([a-z]+(?:#[a-z]+)?)"\]\)', fn))
    for eski in ("performans", "ayarlar", "operasyon#failsub", "onaylar", "ajan"):
        assert f'"{eski}"]' not in fn, f"şerit hâlâ eski hedefe bakıyor: {eski}"
    assert "karar#failsub" in fn, "ret çipi mutabakat masasının ret bloğuna gitmiyor"
    assert "karar#mutabakat" in fn, "ayna sapması mutabakat masasına gitmiyor"
    assert "kilitler#mudahale" in fn, "HALT/devre kesici müdahale kollarına gitmiyor"
    assert "ogrenme#hermes" in fn, "Hermes bütçesi beyin bölümüne gitmiyor"
    assert hedefler, "şeritte hiç hedef kalmamış"


def test_ic_hedeflerin_HEPSI_cozulebilir():
    """Var olmayan bir rotaya işaret eden bir bağ, hiç işaret etmemekten kötüdür (v154 dersi).
    `data-a1` hedefleri ve palet komutları YEDİ SAYFA ∪ ALIAS ∪ BÖLÜM ÇAPASI kümesine düşmeli."""
    sayfalar = set(["bugun"] + list(ADR_HARITASI))
    bolumler = {b for bl in ADR_HARITASI.values() for b in bl}
    alias = set(_sozluk("ROUTE_ALIAS"))
    # Bölüm başlığı çapası + app.js'in ürettiği tek elle-yazılmış çapa (`id="failsub"`).
    capalar = bolumler | {"failsub"}

    def cozulur(h: str) -> bool:
        sayfa, _, capa = h.partition("#")
        if sayfa not in sayfalar and sayfa not in alias:
            return False
        return (not capa) or capa in capalar

    hedefler = set(re.findall(r'data-act="go" data-a1="([\w#]+)"', APPJS))
    hedefler |= set(re.findall(r'gorunum: "([\w#]+)"', PALETTE))
    hedefler |= set(re.findall(r'gorunumeGec\("([\w#]+)"\)', PALETTE))
    hedefler -= {"${k.hedef}", "${hedef}", "${id}"}          # şablon değişkenleri kayıttan gelir
    assert hedefler, "hiç iç hedef bulunamadı — ölçüm boşa çıkmış olabilir"
    for h in sorted(hedefler):
        assert cozulur(h), f"çözülemeyen iç hedef: {h}"


def test_palet_mudahale_komutlari_kilitlere_gider():
    """ADR: "müdahale ⌘K'da da yaşar". Kollar artık Kilitler'de bir BÖLÜM; palet komutu
    operatörü o bölüme götürmeli ki kolun yeni durumu (çekili mi?) tıkladıktan sonra görünsün."""
    for fn in ("opSoftHalt", "opCancelOpen", "opFlatten", "opLearnHaltToggle"):
        m = re.search(r'gorunum: "([\w#]+)", fn: "%s"' % fn, PALETTE)
        assert m, f"{fn} için palet görünüm bağlaması yok"
        assert m.group(1) == "kilitler#mudahale", f"{fn} → {m.group(1)} (kilitler#mudahale olmalı)"


def test_mudahale_kollari_UC_yuzeyde_ama_TEK_govde():
    """Üst bar kapağı, ⌘K ve yeni bölüm — üçü de aynı `window.op*` fonksiyonlarını çağırır.
    İkinci bir yetki yolu (paletin ya da bölümün doğrudan /api/halt'a gitmesi) `HALTED` bayrağı
    ile üst bardaki nabzı 15 saniyeye kadar ayrıştırırdı."""
    assert 'data-act="opSoftHalt"' in INDEX, "üst bar kapağındaki kol düşmüş"
    mud = _govde("RENDER.mudahale = async () => {", "\n// ---- KİLİTLER") \
        if "\n// ---- KİLİTLER" in APPJS[APPJS.index("RENDER.mudahale = async () => {"):] \
        else APPJS[APPJS.index("RENDER.mudahale = async () => {"):
                   APPJS.index("function _bellSVG(h) {")]
    for fn in ("opSoftHalt", "opCancelOpen", "opFlatten", "opLearnHaltToggle"):
        assert f'"{fn}"' in mud, f"{fn} müdahale bölümünde yok"
    assert "apiFetch(" not in mud, "müdahale bölümü kendi yazma yolunu açmış — ikinci yetki yolu"
    # Ölçülemeyen kol durumu "kapalı" YAZMAZ.
    assert "ölçülemedi" in mud, "teşhis ucu düştüğünde kol durumu uydurulabilir"


def test_aktif_sayfa_tazelenir_sabit_render_adi_degil():
    """Müdahale kolları ve ret-kapatma `RENDER.operasyon()` çağırıyordu. O render S2R-2'de altı
    parçaya bölündü: sabit ada çağrı, operatörün BAKMADIĞI sayfayı tazelemek ve sonuç mesajının
    yazılacağı düğümü (`#fsub-msg`) hiç bulamamak demek olurdu."""
    assert "async function _aktifSayfayiCiz()" in APPJS
    for w in ("opSoftHalt", "opLearnHalt", "opCancelOpen", "opFlatten"):
        govde = _yorumsuz(_govde(f"window.{w} = async ", "\n};"))
        assert "_aktifSayfayiCiz()" in govde, f"{w} aktif sayfayı tazelemiyor"
        assert "RENDER.operasyon()" not in govde, f"{w} hâlâ sabit render adına çağrı yapıyor"
    ack = _yorumsuz(_govde("async function _ackRejects(payload, msgYazi) {", "\nwindow.ackReject ="))
    assert "_aktifSayfayiCiz()" in ack and "RENDER.operasyon()" not in ack


# =================================================================================================
# 6) CSP, JETON VE MERTEBE — göç yeni bir kaçak açmadı mı?
# =================================================================================================
def test_yeni_yuzeylerde_satir_ici_olay_yok():
    """CSP `script-src 'self'` satır içi işleyicileri bloklar. Sekiz yeni bölüm de o kurala
    tabi — burada erken yakalanır (dağıtımda değil)."""
    for ad in YENI_BOLUMLER:
        i = APPJS.index(f"RENDER.{ad} = async ")
        parca = APPJS[i:i + 4000]
        assert not re.search(r'\son[a-z]+\s*=\s*["\']', parca), f"{ad}: satır içi olay özniteliği"


def test_yeni_CSS_jeton_disi_renk_kullanmaz():
    """Omega kuralı: renk taşıyan hiçbir değer kuralın içinde yazılmaz, jetondan gelir."""
    blok = CSS[CSS.index("S2R-2 · İÇERİK GÖÇÜ"):]
    blok = blok[:blok.index("/* ---- GENEL BAKIŞ")]
    for kotu in re.findall(r"(#[0-9a-fA-F]{3,8}|rgba?\()", blok):
        raise AssertionError(f"S2R-2 CSS'inde jeton dışı renk: {kotu}")


def test_detay_katmani_klavyeyle_acilir():
    """`<details>/<summary>` yerel olarak odaklanabilir ve Enter/Space ile açılır — ama
    `list-style:none` ile işaretçiyi kaldırırken odak halkasını da kaldırmak kolaydır."""
    kural = re.search(r"\.detay-kat>summary\{([^}]*)\}", CSS)
    assert kural and "cursor:pointer" in kural.group(1)
    assert re.search(r"\.detay-kat>summary:focus-visible\{[^}]*outline:", CSS), \
        "detay katmanı özetinin odak halkası yok — klavye kullanıcısı nerede olduğunu bilmez"

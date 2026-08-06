"""v151 — WP-P TUR-1: sessiz hat · alarm bütçesi · gauge yasağı · saf-siyah · hareket kuralı.

Bu dosyanın ölçtüğü kusur sınıfı TEK ve v139'unkinden FARKLI: v139 "pano gördüğünü yanlış
anlatıyor" idi; burada ölçülen **panonun SAĞLIKLIYKEN de konuşması** — yani sinyalin gürültüye
gömülmesi. Üç biçimi vardı ve üçü de artefaktta ölçüldü:

  A) DAĞINIK SAĞLIK — bekçi/kilit/tazelik ÜÇ ayrı yerde (HUD rozeti · statuspill · Bölüm 1) ve
                      üçü de her hâlde konuşuyor. Sapma anında ses değişimi ÜRETİLEMİYOR.
  B) ÖLÇÜLMEYEN YÜK  — alarm ÜRETİMİ kayıtlıydı (her jeton bir satır), alarm YÜKÜ hiç ölçülmüyordu.
                      Operatörü kör eden şey kaçırılan tek alarm değil, bakılamayacak kadar çoğu.
  C) ANLAMSIZ HAREKET — `.dot.pulse` sınıfı KOŞULSUZ basılıyordu; sağlıklı sistemde de üst barda
                      sürekli yanıp sönen bir nokta vardı. Sürekli hareket, hareketin haber olma
                      kapasitesini tüketir.

Testler KAYNAĞA bakar (repo deseni: test_pano_turu_v139, test_empty_gauge_honesty_v79): bir alanın
API'de var olması onun PANODA okunduğu anlamına gelmez ve bu turun yarısı tam olarak o boşluğun
kapatılmasıdır. Üretici/tüketici pariteleri ayrıca zorlanır.
"""
from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
WEB = SRC / "meridian" / "web"
APPJS = (WEB / "app.js").read_text()
INDEX = (WEB / "index.html").read_text()
THEME = (WEB / "theme.js").read_text()
API = (SRC / "meridian" / "api.py").read_text()
WATCHDOG = (SRC / "meridian" / "watchdog.py").read_text()

# Yorum satırları sayılmaz: bu turun her kaldırma kararı GEREKÇESİYLE yazıldı ("eski kural şuydu,
# neden yanlıştı"). O gerekçe kaynakta durmalı ama "hâlâ orada" diye okunmamalı — yoksa doğru
# davranan bir düzeltme kendi belgesi yüzünden düşer (v139'un aynı kuralı).
KOD_JS = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))


def _style_blogu() -> str:
    """index.html'in YALNIZ CSS'i, yorumlar ayıklanmış. Belge metni kural sanılmasın."""
    css = INDEX[INDEX.index("<style>") + 7:INDEX.index("</style>")]
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


CSS = _style_blogu()


# =============================== P1 · SESSİZ HAT ===============================
def test_sessiz_hat_api_alani_uretiliyor():
    """Toplama SUNUCUDA kurulur. Panoda kurulsaydı aynı gerçeğin ikinci bir metni doğardı ve
    biri sessizce bayatlardı (bu deponun tekrar eden kusur sınıfı)."""
    assert "def _sessiz_hat(wd: dict, hb: dict) -> dict:" in API
    assert '"sessiz_hat": _sessiz_hat(_wd_rep, hb),' in API
    # ÜÇ SEGMENT, ADLARIYLA
    for ad in ('"ad": "bekçiler"', '"ad": "kilitler"', '"ad": "veri"'):
        assert ad in API, f"sessiz hat {ad} segmentini üretmiyor"


def test_bekci_raporu_TEK_KEZ_hesaplanir():
    """Aynı yanıtta iki okuma anı = iki farklı "kaç bekçi gecikti" cevabı. `watchdog.report()`
    doğrudan çağrısı diagnostics dönüşünde KALMAMALI."""
    # v192: yük `_wd_rep`i genişletiyor (`alarm_gunluk` günlük alarm sayacı) — ama HÂLÂ TEK
    # hesaplanmış rapordan türüyor. Sözleşme "alan eklenemez" değil, "ikinci bir okuma anı
    # doğamaz"dır; çivi o yüzden `report()` ÇAĞRI SAYISINI ölçer, dizgeyi değil.
    assert "_wd_rep" in API and '"watchdog": {**_wd_rep' in API
    assert '"watchdog": __import__("meridian.watchdog", fromlist=["report"]).report()' not in API
    assert API.count("_wd.report()") == 1, "bekçi raporu birden çok kez hesaplanıyor"


def test_sessiz_hat_saglikliyken_TEK_SONUK_SATIR():
    """SÖZLEŞME: hepsi sağlıklıyken şerit tek satırdır, renk TAŞIMAZ ve segmentler sönük kalır.
    `.sessizhat` kuralının kendisi --tx2'dedir ve sağlıklı `b` gövdesi rengi MİRAS alır —
    kalın/renkli bir sayı, haber olmaması gereken şeyi haber gibi gösterirdi."""
    assert ".sessizhat{" in CSS
    m = re.search(r"\.sessizhat\{([^}]*)\}", CSS)
    assert m and "var(--tx2)" in m.group(1), "sessiz hat sönük değil"
    assert re.search(r"\.sessizhat \.sh-seg b\{[^}]*color:inherit", CSS), \
        "sağlıklı segmentin sayısı kendi rengini taşıyor — sönük kalmalı"


def test_renk_YALNIZ_sapan_segmentte():
    """Şeridin tamamını boyamak 'hepsi bozuk' der ve toplamanın ayırt etme gücünü siler."""
    assert re.search(r"\.sessizhat \.sh-sap\{[^}]*var\(--amber\)", CSS)
    assert re.search(r"\.sessizhat \.sh-sap\.kritik\{[^}]*var\(--red\)", CSS)
    # `.sessizhat` kök kuralı bir para rengi TAŞIMAMALI
    kok = re.search(r"\.sessizhat\{([^}]*)\}", CSS).group(1)
    for jeton in ("--amber", "--red", "--green"):
        assert jeton not in kok, f"sessiz hattın kök kuralı {jeton} taşıyor — sağlıklı şerit renkli"


def test_sapma_ad_sure_ve_runbook_ipucu_tasir():
    """"Bekçi gecikti" bir bayrak, "warmup_sprint 49 sa gecikti — süreç canlı mı" bir karardır."""
    assert "function sessizHat(sh)" in APPJS
    for parca in ("x.ad", "x.sure", "x.ipucu"):
        assert parca in APPJS, f"sessiz hat açılımı {parca} okumuyor"
    assert '"ipucu": "mekanizma kadansı durdu' in API
    assert "_sure_metni" in API, "sapmanın SÜRESİ üretilmiyor"


def test_acilim_kirpmasi_SESSIZ_DEGIL():
    """11 bekçi birden gecikince şerit listeye dönüşür ve Level-1 olmaktan çıkar. Tavan var,
    ama kırpılan sayı YAZILIR — sessiz kırpma, kapatılmaya çalışılan kusurun ta kendisi."""
    assert "const SH_ACILIM_TAVAN = 4;" in APPJS
    assert "+${kalan} daha" in APPJS


def test_kilit_segmenti_FAZ6_ZINCIRI_DEGIL():
    """Faz-6 zinciri fail-closed'dır ve KAPALI olması NORMAL hâldir (Faz 6 açılmadı). Sessiz hatta
    konsaydı şerit ilk günden kalıcı olarak kırmızı olurdu — toplamanın tam tersi."""
    i = API.index("def _sessiz_hat(")
    govde = API[i:API.index("\n\n\n", i)] if "\n\n\n" in API[i:] else API[i:i + 6000]
    assert "faz6_kilitleri" not in govde, "sessiz hat Faz-6 kilit zincirini okuyor — kalıcı kırmızı"
    assert "health.halted()" in govde and "health.learn_halted()" in govde
    assert "Faz-6 kilit zinciri BU DEĞİLDİR" in API, "kilit tanımının beyanı yok"


def test_veri_segmenti_BAYATKEN_taze_demez():
    """Bayat bir nabzın yanında duran "taze" damgası, sessiz hattın kapatmak için kurulduğu
    yanılsamanın ta kendisi olurdu."""
    assert '"ozet": ((f"taze — {son_bar}" if son_bar else "taze") if not v_sapma' in API


# =============================== P2 · ALARM BÜTÇESİ ===============================
def test_alarm_butcesi_alanlari_var():
    assert "def alarm_budget() -> dict:" in WATCHDOG
    assert "def alarm_budget_cached() -> tuple[dict, float]:" in WATCHDOG
    assert '"alarm_butcesi": {**_alarm_rep, "yas_s": _alarm_age},' in API
    for alan in ("tepe_10dk", "tavan_10dk", "duran", "tavan_duran", "dagilim", "hedef_yuzde"):
        assert f'"{alan}"' in WATCHDOG, f"alarm bütçesi {alan} üretmiyor"


def test_eemua_eslemesi_BEYANLI_ve_uretici_ile_ESLESIR():
    """ÜRETİCİ/TÜKETİCİ PARİTESİ: eşleme `obs._emit`in bastığı seviyelerden türer. obs yeni bir
    seviye eklerse (ya da birini kaldırırsa) bu test kırılır ve eşleme sessizce eskimez."""
    assert 'SEVIYE_EEMUA = {"warn": "low", "alarm": "high"}' in WATCHDOG
    obs = (SRC / "meridian" / "obs.py").read_text()
    basilan = set(re.findall(r'_emit\(\s*"([a-z]+)"', obs))
    assert basilan, "obs._emit seviyeleri okunamadı — ayıklama deseni bozuldu"
    eslenen = set(re.findall(r'"([a-z]+)": "(?:low|high|emergency)"', WATCHDOG))
    # `info` bilerek DIŞARIDA: bir alarm değil, bir kayıt satırı.
    assert basilan - eslenen == {"info"}, \
        f"obs seviyeleri ile EEMUA eşlemesi ayrıştı: eşlenmeyen={sorted(basilan - eslenen - {'info'})}"


def test_emergency_SIFIR_DEGIL_None_ve_gerekcesi_tasinir():
    """0 yazmak "ölçtük, acil alarm çıkmadı" demek olurdu; gerçek şu ki bu sistem acil sınıfını
    ÜRETEMİYOR. Uydurma yasağının sayaç hâli."""
    assert '"emergency": None' in WATCHDOG
    assert '"emergency_neden"' in WATCHDOG
    assert "acil ölçülemez (üretici yok)" in APPJS, "pano acil dilimini 0 gibi gösteriyor olabilir"


def test_uyari_TONU_yalniz_olculen_tavan_asiminda():
    """Dağılım hedefi (80/15/5) ton TAŞIMAZ: üç dilimden biri üretilemiyor, yani hedefe göre
    "aşım" hükmü kurulamaz — kurulsaydı ölçülemeyen bir şey hakkında hüküm olurdu."""
    assert '"asim_var": bool(asim["tepe"] or asim["duran"])' in WATCHDOG
    assert 'ab.asim_var ? " asim" : ""' in APPJS
    assert re.search(r"\.alarmbutce\.asim\{[^}]*var\(--amber\)", CSS)
    kok = re.search(r"\.alarmbutce\{([^}]*)\}", CSS).group(1)
    for jeton in ("--amber", "--red", "--green"):
        assert jeton not in kok, f"alarm bütçesi satırı sapma yokken {jeton} taşıyor"


def test_onbellek_yasi_DISARI_VERILIR():
    """Önbellekli bir sayıyı taze gibi göstermek bu deponun kovaladığı kusur sınıfı
    (`integrity_age_s` emsali)."""
    assert '"yas_s": _alarm_age' in API
    assert "sn önce hesaplandı" in APPJS


def test_damgasiz_satir_SAYIMA_GIRMEZ_ama_GORUNUR():
    """Bir zaman noktasına oturtulamayan satırı 24 saatlik sayıma katmak "bu satır bu pencerede
    oldu" iddiası olurdu. Ama sessizce düşürmek de ölçüm kaybı olurdu — ayrı sayaç."""
    assert '"damgasiz": damgasiz' in WATCHDOG
    assert "damgasız satır sayıma girmedi" in APPJS


# =============================== P3 · GAUGE YASAĞI ===============================
def test_radyal_gauge_YOK():
    """Few'nun bullet graph spesifikasyonu tam olarak "metre ve kadranların yerini almak üzere"
    yazıldı. Kelime bazlı tarama: yorumlarda gerekçe olarak geçmesi serbest, KODDA üretilmesi
    değil."""
    # JETONLAR RADYAL KODLAMAYA ÖZGÜ SEÇİLDİ. `stroke-dasharray` LİSTEDE DEĞİL ve bu bir
    # gevşeme değil bir DÜZELTME: kesik çizgi bir halka tekniği değil, kartezyen bir eşik
    # çizgisidir ve `_bellSVG` onu meşru olarak kullanıyor (Δ=0 ve eşik kuantili). Halkanın
    # imzası `stroke-dashoffset`tir — çevreyi kesirle doldurma hilesi.
    for jeton in ("_donut", "_ring(", "conic-gradient", "stroke-dashoffset"):
        assert jeton not in KOD_JS, f"radyal gösterge kalıntısı: {jeton}"
    # `.gaugewrap` sarmalayıcı ADI korunur (app.js sınıfı isimle üretiyor) ama radyal bir kural
    # taşımamalı.
    assert "gaugewrap" in APPJS
    assert not re.search(r"\.gaugewrap\{[^}]*border-radius:\s*50%", CSS)


def test_bullet_FEW_bes_bilesenini_tasir():
    """1 etiket · 2 NİCEL eksen · 3 belirgin bar · 4 karşılaştırma çentiği · 5 ≤3 nitel aralık."""
    assert "function _bullet(o)" in APPJS
    assert 'class="bl-lab"' in APPJS                       # 1
    assert "const centik = [0, ...bantlar]" in APPJS       # 2 — ölçek işaretleri
    assert 'class="bl-ax"' in APPJS and 'text-anchor="end"' in APPJS   # 2 — uç etiketleri
    assert re.search(r"\.bl-ax\{[^}]*font-family:var\(--mono\)", CSS)  # 2 — biçimi CSS'te
    assert "const bar = olculdu ?" in APPJS                # 3
    assert "const hedef = (o.hedef != null" in APPJS       # 4
    assert "const bantlar = (o.bantlar" in APPJS           # 5


def test_bullet_tek_hue_yogunluk_merdiveni():
    """Aralıklar TEK hue'nun farklı yoğunluklarıyla kodlanır — farklı hue, renk körü bir okuyucunun
    ayıramadığı tam olarak o şeydir."""
    m = re.search(r"const YOG = \[(.*?)\];", APPJS, re.S)
    assert m, "yoğunluk merdiveni bulunamadı"
    for para in ("--green", "--red", "--amber", "--blue", "--violet"):
        assert para not in m.group(1), f"bant merdiveni hue taşıyor: {para}"


def test_mini_trend_YALNIZ_GERCEK_SERIYLE():
    """Boş bir sparkline kutusu "trend ölçtük, düz çıktı" diye okunur — ölçülmemiş bir şey için
    bu bir uydurmadır. Seri yoksa yer de TUTULMAZ."""
    assert "const seri = (o.seri || []).map(Number).filter(Number.isFinite);" in APPJS
    assert "if (seri.length >= 2)" in APPJS
    assert 'trendSvg ? `<div class="bl-trend">' in APPJS
    # Seri GERÇEK bir üreticiden gelir: analytics.deflate_stats().last per-ship deflation_pct.
    assert "(ml.deflate && ml.deflate.last || []).map(r => r.deflation_pct)" in APPJS
    an = (SRC / "meridian" / "analytics.py").read_text()
    assert '"deflation_pct": round(' in an and '"last": rows[-8:]' in an, \
        "sparkline'ın beslendiği seri üreticide yok — pano uydurma seri çiziyor olabilir"


# =============================== P5 · BELİRSİZLİK ===============================
def test_belirsizlik_isareti_RENK_KULLANMAZ():
    """Renk bu panoda ÖLÇÜMÜN kanalı (Money Rule). Belirsizlik ölçüm değil, ölçümün KÖKENİ
    hakkında bir şerhtir — ayrı bir kanal ister."""
    m = re.search(r"\.belirsiz\{([^}]*)\}", CSS)
    assert m, ".belirsiz kuralı yok"
    kural = m.group(1)
    assert "dashed" in kural and "currentColor" in kural
    for jeton in ("--amber", "--red", "--green", "--accent"):
        assert jeton not in kural, f"belirsizlik işareti renk kanalını kullanıyor: {jeton}"


def test_belirsiz_hucre_BEYANSIZ_olamaz():
    """`title` olmadan kesik çizgi bir SÜS olur."""
    assert "function belirsiz(icerik, beyan)" in APPJS
    assert 'title="${esc(beyan)}"' in APPJS
    # sim/havuz kökenli iki IC hücresi işaretli
    assert "SİM KÖKENLİ" in APPJS and "KARIŞIK KÖKEN" in APPJS


def test_bayatlik_solmasi_UC_KADEME_ve_esikler_TEK_YERDE():
    """Opaklık NİCELİK TAŞIMAZ; yalnız "bu satır eskiyor" der. Sayı hiçbir kademede gizlenmez."""
    assert "const BAYAT_ESIK_GUN = [1, 3, 7];" in APPJS
    assert "function bayatSinif(tarih, referans)" in APPJS
    for k in ("bayat-1", "bayat-2", "bayat-3"):
        assert f".{k}{{" in CSS.replace(" ", ""), f"{k} sınıfı CSS'te yok"
    assert ".bayat-4" not in CSS, "dördüncü kademe okunamayan bir gri merdiveni olur"
    # ölçülemeyen bayatlık SOLDURULMAZ
    assert 'if (!tarih || !referans) return "";' in APPJS


# =============================== P6 · SAF SİYAH SÜRGÜNÜ ===============================
def test_gece_temasinda_saf_siyah_beyaz_YOK():
    """Halation argümanının hedeflediği yüzey KOYU zemindir. Gece bloğunda tek bir saf değer bile
    olamaz — zemin #1c1a18, mürekkep #d4d0cb."""
    i = CSS.index(':root[data-theme="gece"]')
    blok = CSS[i:CSS.index("}", i)]
    for yasak in ("#000", "#fff", "#ffffff", "#000000"):
        assert yasak not in blok.lower(), f"gece temasında saf değer: {yasak}"
    assert not re.search(r":\s*(black|white)\b", blok)


def test_app_js_ve_theme_js_renk_DEGERI_tasimaz():
    """Jeton sözleşmesi: renk taşıyan hiçbir değer kuralın içinde YAZILMAZ, jetondan gelir.
    Aksi hâlde ikinci tema sessizce kırılır (canlı emsal: --nav-bg)."""
    for ad, kaynak in (("app.js", KOD_JS), ("theme.js", THEME)):
        bulunan = re.findall(r"#[0-9a-fA-F]{3,8}\b", kaynak)
        # `#` ile başlayan DOM id seçicileri hariç: onlar renk değil (ör. $("#gate")).
        renkler = [h for h in bulunan if re.fullmatch(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})", h)]
        assert not renkler, f"{ad} renk DEĞERİ taşıyor (jeton olmalı): {sorted(set(renkler))}"


# =============================== P10 · HAREKET KURALI ===============================
def test_reduced_motion_blogu_TUM_gecis_ve_animasyonlari_kapatir():
    assert re.search(r"@media\(prefers-reduced-motion:reduce\)\{\s*\*\{transition:none!important;"
                     r"animation:none!important\}", CSS), \
        "genel prefers-reduced-motion bloğu yok ya da tüm animasyonları kapatmıyor"


def test_puls_YALNIZ_anomali_sinyalinde():
    """`.dot.pulse` sınıfını app.js KOŞULSUZ basıyor — kural niteleyicisiz kalırsa sağlıklı
    sistemde de üst barda sürekli yanıp sönen bir nokta olur ve gerçekten bir şey bozulduğunda
    hareket zaten tüketilmiştir."""
    assert ".dot.pulse.stale,.dot.pulse.halt{animation:pulse" in CSS
    assert not re.search(r"(?<![.\w])\.dot\.pulse\{[^}]*animation", CSS), \
        "koşulsuz .dot.pulse animasyonu geri gelmiş"
    # app.js sözleşmesi korunuyor: sınıf adları DEĞİŞMEDİ
    assert '"dot pulse" + (t.halted ? " halt" : (t.stale ? " stale" : ""))' in APPJS


def test_kesif_modu_cercevesi_ARTIK_PULSLAMIYOR():
    """Keşif modu bir ANOMALİ DEĞİL, operatörün seçtiği bir duruş. Ekranın dört kenarında saatlerce
    nefes alan bir çerçeve, hareketi durum bildiriminin diline çeviriyordu."""
    assert "@keyframes explorePulse" not in CSS
    assert "animation:explorePulse" not in CSS
    # ÇERÇEVE DURUYOR: mod hâlâ görünür.
    assert "body.explore-mode::after" in CSS and "var(--amber)" in CSS


def test_yanip_sonme_YALNIZ_gercek_anomalide():
    """`.blink` yalnız GHOST ve DESYNC çiplerinde — ikisi de mutabakat kırılmasıdır."""
    kullanim = re.findall(r'_chip\("([^"]+)",\s*"[^"]*blink[^"]*"\)', APPJS)
    assert set(kullanim) <= {"GHOST", "DESYNC"}, f"blink anomali dışında kullanılıyor: {kullanim}"


# =============================== P4 · TİPOGRAFİ ===============================
def test_slashed_zero_OLCULMUS_gerekceyle_EKLENMEZ():
    """Geist Mono'da `zero` özelliği YOK ve eğik çizgi zaten varsayılan glifin içinde (tarayıcıda
    ölçüldü 2026-08-01). Bildirimi eklemek, ölçülmüş olarak ETKİSİZ bir şeyi "tipografi denetimi
    yapıldı" diye kayda geçirmek olurdu."""
    assert "font-feature-settings" not in CSS, \
        "etkisiz bir font-feature bildirimi eklenmiş — kaynaktaki ölçüm bunun no-op olduğunu söylüyor"
    assert "WP-P/P4" in INDEX, "hükmün yeniden açılmasını engelleyen kayıt yok"


def test_sayi_sutunlari_SAGA_HIZALI():
    """Sağa hizalı olmayan bir sayı sütununda "0,0312" ile "1,4" karşılaştırılamaz. Kural iki
    tablo biçiminde de (gerçek <table> ve .trow ızgarası) YÜRÜRLÜKTE olmalı — tek panoda iki
    farklı sayı sütunu grameri olamaz."""
    assert re.search(r"\.tbl \.num\{[^}]*text-align:right", CSS)
    assert re.search(r"\.trow > \.num\{[^}]*text-align:right", CSS)
    # BAŞLIK DA İŞARETLİ: sütunun hangi kenardan okunacağı belirsiz kalmasın.
    assert '<span class="num">ÖRNEKLEM</span><span class="num">ORT. R</span>' in APPJS
    assert '${hz.map(h => `<span class="num">${h} BAR</span>`).join("")}' in APPJS


def test_tabloda_sayi_hucresi_baslikla_AYNI_kenardan_okunur():
    """Gerçek <table class="tbl"> bloklarında `class="num"` taşıyan her BAŞLIK için gövdede de
    en az bir `class="num"` hücre olmalı — biri işaretlenip öteki unutulursa sütun kendi içinde
    ayrışır."""
    for m in re.finditer(r"<table class=\"tbl\">(.*?)</table>", APPJS, re.S):
        blok = m.group(1)
        th_num = len(re.findall(r'<th class="num"', blok))
        td_num = len(re.findall(r'<td class="num', blok))
        if th_num:
            assert td_num >= th_num, \
                f"tabloda {th_num} sayı başlığı var ama {td_num} sayı hücresi işaretli"

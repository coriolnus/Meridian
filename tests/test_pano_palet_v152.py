"""⌘K KOMUT PALETİ (meridian/web/palette.js) — kaynak-çivili + saf-fonksiyon testleri.

NİYE BU BİÇİM: pano testleri tarayıcı açmaz. jsdom yok, yerel sunucu yok (çift emir
riski). Bu yüzden iki katman:

  1. SAF ÇEKİRDEK, NODE İLE KOŞTURULUR. palette.js bulanık skorlayıcıyı, sıralamayı ve
     geçmiş güncellemesini DOM'a hiç dokunmayan saf fonksiyonlarda tutuyor ve Node'da
     `module.exports` ile dışa veriyor (tarayıcıda `module` tanımsız → dal ölü). Yani
     aramanın DAVRANIŞI gerçekten çalıştırılarak sınanır, kaynağa bakılarak değil.

  2. KAYNAK ÇİVİLERİ. Geri kalanı — CSP uyumu, jeton sözleşmesi, iki adımlı onay,
     erişilebilirlik iskeleti, index.html'e tek satır dahil, api.py yolu — dosya
     metninden çivilenir. Bunlar "kod incelemesi yerine test" değil; her biri
     DAĞITILDIĞINDA SESSİZCE ölen bir arıza sınıfının bekçisi:
       · satır içi işleyici  → CSP bloklar, düğme çalışmaz (bkz. test_web_csp_uyum.py)
       · api.py yolu yok     → /palette.js 404, palet hiç var olmaz
       · sabit renk kodu     → gece temasında palet yanlış boyanır
       · yeni auth yüzeyi    → token ikinci bir yerden okunur, sapma görünmez
"""
import json
import pathlib
import re
import shutil
import subprocess

import pytest

KOK = pathlib.Path(__file__).resolve().parents[1]
WEB = KOK / "meridian" / "web"
PALET = WEB / "palette.js"
INDEX = WEB / "index.html"
API = KOK / "meridian" / "api.py"

NODE = shutil.which("node")


@pytest.fixture(scope="module")
def kaynak():
    assert PALET.exists(), f"{PALET} yok — palet dosyası taşınmış ya da silinmiş"
    return PALET.read_text()


def _node(ifade: str):
    """palette.js'i Node'da yükle, `ifade`yi değerlendir, JSON olarak geri al.

    Değer JSON'a çevrilemezse test kırılır — sessizce `undefined` dönmez.
    """
    if not NODE:
        pytest.skip("node bulunamadı — saf çekirdek testleri koşulamıyor (ÖLÇÜLMEDİ)")
    betik = (
        "const P = require(%s);\n"
        "const _v = (%s);\n"
        "process.stdout.write(JSON.stringify(_v === undefined ? null : _v));\n"
        % (json.dumps(str(PALET)), ifade)
    )
    r = subprocess.run([NODE, "-e", betik], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, f"node hatası:\n{r.stderr}"
    return json.loads(r.stdout)


def _skor(hedef, sorgu):
    r = _node("P.bulanikSkor(%s, %s)" % (json.dumps(hedef), json.dumps(sorgu)))
    return None if r is None else r["skor"]


# =====================================================================================
# 1. SAF ÇEKİRDEK — gerçekten çalıştırılır
# =====================================================================================

def test_node_syntaksi_gecerli():
    """Dosya hiç yüklenemiyorsa geri kalan her şey anlamsız — ilk kapı bu."""
    if not NODE:
        pytest.skip("node bulunamadı (ÖLÇÜLMEDİ)")
    r = subprocess.run([NODE, "--check", str(PALET)], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, f"palette.js sözdizimi hatalı:\n{r.stderr}"


def test_turkce_katlama_bilesik_i_uretmez():
    """`"İ".toLowerCase()` bileşik "i̇" (i + birleşen nokta) üretir ve "i" ile EŞLEŞMEZ.

    Katlama küçültmeden ÖNCE yapılmazsa "İntraday" araması kendi adını bulamaz —
    ve hata görünmez, sadece "sonuç yok" der.
    """
    assert _node('P.katla("İSTANBUL")') == "istanbul"
    assert _node('P.katla("Öğrenme")') == "ogrenme"
    assert _node('P.katla("ÇILGIN ışık ŞUBAT")') == "cilgin isik subat"
    # bileşik karakter sızmamalı
    assert "̇" not in _node('P.katla("İİİ")')


def test_turkcesiz_klavyeyle_aranabilir():
    """Klavyede ö/ğ/ş olmayabilir; olsa bile kimse aramak için o tuşları aramaz."""
    assert _node('P.bulanikSkor("Öğrenme", "ogrenme") !== null') is True
    assert _node('P.bulanikSkor("Kısayol haritası", "kisayol") !== null') is True


def test_eslesmeyen_sorgu_null_doner():
    """Eşik değil, GERÇEK yokluk: bir harf bile düşerse eşleşme yoktur."""
    assert _node('P.bulanikSkor("Bugün", "zzz")') is None
    assert _node('P.bulanikSkor("HALT", "haltx")') is None


def test_bos_sorgu_her_seyle_eslesir():
    """Palet açıldığında liste BOŞ görünmemeli — sıralama geçmişe kalır."""
    r = _node('P.bulanikSkor("herhangi bir komut", "")')
    assert r == {"skor": 0, "isaret": []}


def test_isaret_indisleri_gercek_eslesme_yerleridir():
    """Ekranda altı çizilen harf ile skoru üreten harf AYNI olmalı (tek eşleştirici)."""
    assert _node('P.bulanikSkor("kararlar", "kar").isaret') == [0, 1, 2]
    assert _node('P.bulanikSkor("kararlar", "kra").isaret') == [0, 2, 3]


def test_bitisiklik_dagilmis_eslesmeyi_yener():
    """"kar" tam olarak yazıldığı gibi duruyorsa, harfleri dağılmış eşleşmeden üstündür."""
    assert _skor("kararlar", "kar") > _skor("kararlar", "kra")


def test_bastan_eslesme_ortadan_eslesmeyi_yener():
    """Aynı sorgu iki komutta da geçiyorsa, adı ONUNLA BAŞLAYAN üstte olmalı."""
    assert _skor("HALT — acil durdur", "halt") > _skor("Kademe 4 · Halt Learning", "halt")


def test_kelime_siniri_odullenir():
    """Kelime başı eşleşmesi, kelimenin ortasındaki aynı harften daha anlamlıdır.

    İki hedef AYNI uzunlukta ve eşleşme İKİSİNDE DE aynı indislerde — tek fark
    'o'nun bir kelime başında mı yoksa kelimenin ortasında mı durduğu. Uzunluk ve
    başlangıç ödülleri böylece sadeleşir, ölçülen şey yalnız sınır ödülüdür.
    """
    assert _skor("Cancel Open", "cop") > _skor("Cancelxopen", "cop")


def test_esitlikte_kisa_hedef_kazanir():
    """İki komut da eşleşiyorsa daha az gürültü taşıyan kısa ad üstte olmalı."""
    assert _skor("Piyasa", "piyasa") > _skor("Piyasa filtresi · Silahlı", "piyasa")


def test_komut_skoru_anahtar_kelimeden_de_eslesir():
    """"durdur" yazan operatör HALT'ı bulmalı — ad "HALT — acil durdur" olmasa bile."""
    r = _node(
        'P.komutSkoru({id:"x", ad:"HALT", anahtarlar:["durdur","acil","panik"]}, "panik")'
    )
    assert r is not None and r["skor"] > 0
    # anahtar/altyazı eşleşmesinde ADIN harfleri VURGULANMAZ — yoksa neyin eşleştiği
    # konusunda okuyucuya yalan söylenir.
    assert r["isaret"] == []


def test_ad_eslesince_anahtarlara_hic_bakilmaz():
    """Tek komut içinde ad eşleşmesi kısa devre yapar: skor ADIN skorudur, kırpılmaz.

    (Bu, "ad her zaman anahtardan yüksek puan alır" DEĞİLDİR — farklı komutlarda
    kısa bir anahtar uzun bir adı geçebilir ve bu doğrudur. Çivilenen şey, aynı
    komutta iki kaynağın karışmaması.)
    """
    tam = _node('P.komutSkoru({id:"a", ad:"Panoyu yenile", anahtarlar:["yenile"]}, "yenile")')
    saf = _node('P.bulanikSkor("Panoyu yenile", "yenile")')
    assert tam["skor"] == saf["skor"]
    assert tam["isaret"] == saf["isaret"] != []


def test_ayni_metin_adda_anahtardan_degerlidir():
    ad = 'P.komutSkoru({id:"a", ad:"Yenile", anahtarlar:[]}, "yenile").skor'
    anahtar = 'P.komutSkoru({id:"b", ad:"Zzz", anahtarlar:["Yenile"]}, "yenile").skor'
    assert _node(ad) > _node(anahtar)


KOMUT_ORNEK = (
    '[{id:"a",ad:"Bugün",grup:"Gezinme"},'
    ' {id:"b",ad:"Kararlar",grup:"Gezinme"},'
    ' {id:"c",ad:"HALT",grup:"Müdahale",anahtarlar:["durdur"]},'
    ' {id:"d",ad:"Panoyu yenile",grup:"Yardımcı"}]'
)


def test_bos_sorguda_son_kullanilanlar_once_ve_favori_numarali():
    r = _node(
        'P.sirala(%s, "", [{id:"c",n:3,t:9},{id:"d",n:1,t:8}])'
        '.map(x => [x.komut.id, x.grup, x.favori])' % KOMUT_ORNEK
    )
    assert r[0] == ["c", _node("P.SON_GRUP"), 1]
    assert r[1] == ["d", _node("P.SON_GRUP"), 2]
    # Geri kalanlar kanonik grup sırasında; hiçbir komut DÜŞMEZ.
    assert [x[0] for x in r] == ["c", "d", "a", "b"]
    assert len(r) == 4


def test_bos_sorguda_gruplar_kanonik_sirada():
    r = _node('P.sirala(%s, "", []).map(x => x.grup)' % KOMUT_ORNEK)
    sira = _node("P.GRUP_SIRA")
    gorulen = []
    for g in r:
        if not gorulen or gorulen[-1] != g:
            gorulen.append(g)
    assert gorulen == [g for g in sira if g in gorulen]


def test_favori_en_fazla_dokuz():
    """⌘1-9 dokuz tuş — onuncu bir favori numarası verilirse ipucu yalan olurdu."""
    gecmis = "[" + ",".join('{id:"k%d",n:1,t:%d}' % (i, 100 - i) for i in range(12)) + "]"
    komutlar = "[" + ",".join('{id:"k%d",ad:"K%d",grup:"Gezinme"}' % (i, i) for i in range(12)) + "]"
    fav = _node("P.sirala(%s, '', %s).map(x => x.favori)" % (komutlar, gecmis))
    assert max(fav) == 9
    assert sorted(f for f in fav if f) == list(range(1, 10))


def test_sorguda_eslesmeyen_komut_listeden_duser():
    r = _node('P.sirala(%s, "kar", []).map(x => x.komut.id)' % KOMUT_ORNEK)
    assert r == ["b"]


def test_sorguda_grup_basligi_basilmaz():
    """Sıralanmış bir listeyi başlıklara bölmek en iyi eşleşmeyi aşağı gömerdi."""
    r = _node('P.sirala(%s, "a", []).map(x => x.grup)' % KOMUT_ORNEK)
    assert r and all(g is None for g in r)


def test_son_kullanilan_esit_skorda_one_gecer():
    iki = '[{id:"x",ad:"Aynı ad",grup:"Gezinme"},{id:"y",ad:"Aynı ad",grup:"Gezinme"}]'
    r = _node('P.sirala(%s, "ayni", [{id:"y",n:2,t:1}]).map(x => x.komut.id)' % iki)
    assert r[0] == "y"


def test_gecmis_tekrarsiz_sayaci_korur_ve_sinirli():
    r = _node(
        'P.gecmisiGuncelle(P.gecmisiGuncelle(P.gecmisiGuncelle([], "a", 1), "b", 2), "a", 3)'
    )
    assert [x["id"] for x in r] == ["a", "b"]          # en son kullanılan başta, tekrar yok
    assert r[0]["n"] == 2 and r[1]["n"] == 1          # sayaç korunuyor ("sık" ayrı sinyal)

    uzun = "[" + ",".join('{id:"g%d",n:1,t:%d}' % (i, i) for i in range(40)) + "]"
    assert len(_node('P.gecmisiGuncelle(%s, "yeni", 99)' % uzun)) == 24


# =====================================================================================
# 2. CSP + JETON SÖZLEŞMESİ
# =====================================================================================

SATIR_ICI = re.compile(r'\son[a-z]+\s*=\s*["\']')


def test_satir_ici_olay_ozniteligi_yok(kaynak):
    """CSP `script-src 'self'` satır içi işleyicileri bloklar — düğme ölü olurdu.

    (Bu kural test_web_csp_uyum.py'de yaşıyor ama oradaki YUZEYLER listesi ad ad
    yazılı ve palette.js oraya EKLENMEDİ — palet turu o dosyanın kapsamı dışındaydı.
    Kural burada, kendi dosyasında ayrıca çivileniyor ki boşluk kalmasın.)
    """
    bulunan = SATIR_ICI.findall(kaynak)
    assert not bulunan, f"palette.js'te satır içi işleyici: {sorted(set(bulunan))}"


def test_govdeli_script_ya_da_dinamik_kod_yok(kaynak):
    for desen, ad in ((r"\beval\s*\(", "eval()"),
                      (r"\bnew\s+Function\s*\(", "new Function()"),
                      (r"javascript:", "javascript: URL")):
        assert not re.search(desen, kaynak), f"palette.js'te {ad} var — CSP bloklar"


def test_sabit_renk_kodu_yok(kaynak):
    """Palet renk DEĞERİ taşımaz: yalnız mevcut jetonları okur.

    Bir hex kodu buraya girerse gece temasında palet o rengi taşımaya devam eder ve
    tema anahtarı sessizce yarım çalışır — panonun daha önce bir kez yaşadığı hata
    sınıfı (nav barın gece beyaz kalması).
    """
    hexler = re.findall(r"#[0-9a-fA-F]{3,8}\b", kaynak)
    assert not hexler, f"palette.js'te sabit renk: {sorted(set(hexler))} — var(--jeton) kullan"
    assert not re.search(r"\brgba?\s*\(", kaynak), "palette.js'te ham rgb()/rgba() — jeton kullan"


def test_stilini_kendi_enjekte_eder(kaynak):
    """Sözleşme: paletin TAMAMI tek dosyada. index.html'e stil eklenmez."""
    assert 'createElement("style")' in kaynak
    assert kaynak.count("var(--") >= 20, "jeton kullanımı beklenenden az — stil dışarı kaçmış olabilir"


def test_app_js_eylem_izin_listesine_dokunmaz(kaynak):
    """Palet kendi düğmelerini kendi bağlar; `data-act` kullansaydı app.js'teki
    EYLEMLER kümesine yeni ad eklemek gerekirdi ve bu tur o dosyaya dokunmuyor.

    NOT: paletin OKUDUĞU `[data-act="..."]` seçicileri (mevcut düğmelerden durum
    türetmek için) bunun dışındadır — onlar üretim değil, okuma.
    """
    assert not re.search(r'\.dataset\.act\s*=', kaynak)
    assert not re.search(r'setAttribute\(\s*["\']data-act["\']', kaynak)


# =====================================================================================
# 3. YENİ AUTH YÜZEYİ YOK
# =====================================================================================

def _kod(kaynak: str) -> str:
    """Yorumları düşür — kural KODA bakar, yorumdaki örneğe değil.

    Ayıklayıcı basittir ve basit kalabilmesi bir varsayıma dayanır: dosyada `://`
    yoktur (yoksa bir URL'in içindeki `//` yorum sanılırdı). Varsayım tahmin değil,
    aşağıda ayrıca çivili.
    """
    assert "://" not in kaynak, "palette.js'e mutlak URL girmiş — yorum ayıklayıcısı artık güvenilmez"
    s = re.sub(r"/\*[\s\S]*?\*/", "", kaynak)
    return "\n".join(re.sub(r"//.*$", "", satir) for satir in s.splitlines())


def test_palet_kendi_ag_cagrisini_yapmaz(kaynak):
    """Palet /api/*'a DOĞRUDAN gitmez ve token'ı ikinci bir yerden okumaz.

    Sebep ölçüldü: app.js `HALTED` bayrağını süreç-içi tutuyor ve nabzı 15 sn'de bir
    tazeliyor (`setInterval(refreshStatus, 15000)`). Palet /api/halt'a doğrudan
    gitseydi üst bardaki durum en yüksek bahisli eylemden hemen SONRA 15 saniyeye
    kadar yalan söylerdi. Bu yüzden zincir app.js'in kendi fonksiyonundan geçer.
    """
    kod = _kod(kaynak)
    for yasak in ("fetch(", "XMLHttpRequest", "x-meridian-token", "meridian_token",
                  "/api/", "navigator.sendBeacon"):
        assert yasak not in kod, (
            f"palette.js içinde {yasak!r} var — palet kendi ağ/auth yüzeyini açmış. "
            "Yazma eylemleri app.js'in global fonksiyonları üzerinden gitmeli."
        )


def test_yazma_eylemleri_app_js_fonksiyonlarina_baglanir(kaynak):
    """Kilit/onay komutları app.js'te GERÇEKTEN tanımlı adlara bağlanmalı.

    Kayıtsız bir ad sessizce ölür (palet `pasif` çizer ama komut hiç çalışmaz).
    """
    app = (WEB / "app.js").read_text()
    adlar = set(re.findall(r'fn:\s*"([A-Za-z_$][\w$]*)"', kaynak))
    assert adlar, "palette.js'te hiç `fn:` bağlaması yok — yazma komutları kaybolmuş"
    eksik = [a for a in sorted(adlar)
             if not re.search(rf"(window\.{re.escape(a)}\s*=|function\s+{re.escape(a)}\s*\()", app)]
    assert not eksik, f"palette.js şu adlara bağlanıyor ama app.js'te tanımı yok: {eksik}"


def test_yazma_komutlari_dogru_gorunume_gotururu(kaynak):
    """app.js'in eylemleri sonucu SAYFAYA ait bir düğüme yazıyor (#hbtn-msg, #ntf-msg,
    #bp-alerts…). O sayfa çizilmemişken çağrı POST'u atar ama sonuç hiçbir yerde
    görünmez — sessiz bir yazma. Palet bu yüzden önce görünüme geçer.
    """
    assert re.search(r'if \(k\.gorunum\) gorunumeGec\(k\.gorunum\)', kaynak), (
        "yazma komutları çalıştırılmadan önce ilgili görünüme geçmiyor"
    )
    # ÇİVİ TAŞINDI (S2R-2, silme yok): hedefler eski görünüm adlarıydı ("ajan", "brifing",
    # "operasyon") ve alias sayesinde doğru SAYFAYA gidiyorlardı — ama sayfanın BAŞINA. İçerik
    # göçünden sonra o sayfalar beş-yedi bölümlü; komutun yazdığı düğme (#hbtn-msg, #bp-alerts,
    # #fsub-msg) sayfanın ortasında kalıyordu. Hedefler artık BÖLÜM ÇAPASI taşıyor. Ölçülen kural
    # aynı: her yazma komutu, sonucunu göreceği yüzeye götürmeli.
    for beklenen in ('gorunum: "ogrenme#hermes"', 'gorunum: "gozetim"',
                     'gorunum: "kilitler#mudahale"', 'gorunum: "portfoy#failsub"'):
        assert beklenen in kaynak, f"{beklenen} bağlaması kayıp"


# =====================================================================================
# 4. İKİ ADIMLI ONAY
# =====================================================================================

def test_yazan_her_komut_iki_adimli(kaynak):
    """Enter TEK BAŞINA yazan bir komutu çalıştıramaz."""
    assert re.search(r'if \(k\.yazma\) \{\s*onayIste\(k\);\s*return;\s*\}', kaynak), (
        "calistirSecili yazma komutunu doğrudan yürütüyor olabilir — iki adım kırılmış"
    )
    assert "function onayIste(" in kaynak
    # Onay adımında yalnız Enter geçer ve TUŞ TEKRARI reddedilir: birinci Enter'ı
    # basılı tutmak ikinci adımı geçmemeli.
    assert re.search(r'if \(ONAY\) \{\s*\n\s*if \(e\.key === "Enter" && !e\.repeat\)', kaynak), (
        "onay adımında `e.repeat` reddi yok — Enter'ı basılı tutmak Flatten'ı çalıştırabilir"
    )


def test_yazan_komutlar_isaretli(kaynak):
    """Kriz kademeleri, onay kuyrukları ve öğrenme eylemleri `yazma: true` taşımalı."""
    yazanlar = re.findall(r'id:\s*"(act:[^"]+)"[\s\S]{0,900}?yazma:\s*(true|false)', kaynak)
    harita = dict(yazanlar)
    for gerekli in ("act:halt", "act:soft", "act:cancel", "act:flatten", "act:learnhalt",
                    "act:ackalerts", "act:ackrejects", "act:reflect", "act:backfill",
                    "act:sprintstart", "act:sprintstop"):
        assert harita.get(gerekli) == "true", f"{gerekli} yazma olarak işaretli değil: {harita.get(gerekli)}"


def test_yikici_komutlar_tehlike_isaretli(kaynak):
    """Kırmızı onay kenarı yalnız gerçekten yıkıcı olanlarda — enflasyon uyarıyı öldürür."""
    for gerekli in ("act:flatten", "act:cancel", "act:halt"):
        blok = re.search(r'id:\s*"%s"[\s\S]{0,900}?\}\);' % re.escape(gerekli), kaynak)
        assert blok and "tehlike: true" in blok.group(0), f"{gerekli} tehlike işareti taşımıyor"


def test_yerli_confirm_onceden_soylenir(kaynak):
    """app.js'in kendi confirm() kutusu çıkacaksa operatör bunu ÖNCEDEN bilmeli;
    sürpriz ikinci modal 'onayladım' hissini bozar ve yanlış refleks kurar."""
    assert "yerliOnay" in kaynak
    assert "tarayıcı onay kutusu da çıkacak" in kaynak


def test_intraday_silahlama_tahmin_edilmez(kaynak):
    """Silahlama durumu yalnız Intraday çizildiğinde DOM'dan okunabilir.

    Bilinmeyen durumda `intradayArm(true)` çağırmak, zaten silahlıyken tekrar
    silahlamak (ya da tersini) demektir. Palet tahmin etmez, oraya götürür.
    """
    # ÇİVİ TAŞINDI (S2R-2): ARM düğmesi intraday'in EMİR yarısıyla birlikte Portföy'e taşındı
    # (`#page-intraemir`). Eski seçici hiçbir şey bulamaz ve palet SESSİZCE yedek "git" komutuna
    # düşerdi — yani silahlama komutu kalıcı olarak çalışmaz hâle gelirdi ve testi yeşil kalırdı.
    assert 'document.querySelector(\'#page-intraemir [data-act="intradayArm"]\')' in kaynak
    assert "act:arm-git" in kaynak, "durum bilinmiyorken kullanılan gezinme yedeği yok"


# =====================================================================================
# 5. ERİŞİLEBİLİRLİK İSKELETİ
# =====================================================================================

@pytest.mark.parametrize("parca,neden", [
    ('"role", "dialog"', "modal olarak duyurulmalı"),
    ('"aria-modal", "true"', "arkadaki sayfa ekran okuyucuda gezilebilir kalmamalı"),
    ('"role", "listbox"', "liste bir seçim listesi olarak duyurulmalı"),
    ('"role", "option"', "satırlar seçenek olarak duyurulmalı"),
    ('"aria-selected"', "hangi satırın seçili olduğu ilan edilmeli"),
    ('"aria-activedescendant"', "roving index: odak girişte kalır, seçim ilan edilir"),
    ('"role", "combobox"', "giriş kutusu listeyi süren bir combobox"),
    ('"aria-disabled", "true"', "pasif satır pasif olduğunu söylemeli"),
])
def test_erisilebilirlik_civileri(kaynak, parca, neden):
    assert parca in kaynak, f"{parca} yok — {neden}"


def test_odak_tuzagi_ve_iadesi(kaynak):
    """Tab modalın dışına kaçmamalı; kapanınca odak geldiği yere dönmeli."""
    assert re.search(r'if \(e\.key === "Tab"\)', kaynak), "Tab yakalanmıyor — odak tuzağı yok"
    assert "ONCEKI_ODAK" in kaynak and "document.contains(ONCEKI_ODAK)" in kaynak, (
        "odak iadesi yok — kapanışta odak <body>'ye düşer"
    )


def test_giris_kapisi_acikken_palet_acilmaz(kaynak):
    """Oturum yokken her komut 401 alırdı ve operatör bunu arıza sanardı."""
    assert "function kapiAcik()" in kaynak
    assert re.search(r'if \(acikMi\(\) \|\| kapiAcik\(\)\) return;', kaynak)


# =====================================================================================
# 6. KISAYOL KAYDI
# =====================================================================================

def test_kendi_keydown_kaydini_yapar(kaynak):
    """Palet kendi global dinleyicisini kurar — app.js'e kayıt eklenmez."""
    assert re.search(r'document\.addEventListener\("keydown",[\s\S]{0,1200}?\}, true\);', kaynak), (
        "global keydown yakalama evresinde kayıtlı değil"
    )
    assert "e.metaKey || e.ctrlKey" in kaynak, "⌘K ve Ctrl+K'nın ikisi de bağlanmalı"
    assert 'String(e.key).toLowerCase() !== "k"' in kaynak


def test_jk_satir_gezinmesiyle_cakismaz():
    """app.js `j/k` ile satır geziyor ama değiştirici tuş varsa ERKEN DÖNÜYOR.

    O erken dönüş kalkarsa ⌘K hem paleti açar hem satır atlar. Çakışmanın olmadığı
    bu satıra bağlı, o yüzden satır burada çivili.
    """
    app = (WEB / "app.js").read_text()
    assert re.search(r'if \(e\.metaKey \|\| e\.ctrlKey \|\| e\.altKey\) return;', app), (
        "app.js'in klavye kısayolları artık değiştirici tuşta erken dönmüyor — ⌘K çakışır"
    )


# =====================================================================================
# 7. DAHİL EDİLME — index.html ve api.py
# =====================================================================================

def test_index_tek_satirla_dahil_eder():
    src = INDEX.read_text()
    bulunan = re.findall(r'<script src="/palette\.js"></script>', src)
    assert len(bulunan) == 1, f"index.html'de {len(bulunan)} palette.js etiketi var (1 olmalı)"
    # app.js'ten SONRA ve </body>'den hemen önce: palet açılışta app.js'in globallerini
    # (go, toggleHalt…) görebilmeli.
    assert re.search(
        r'<script src="/app\.js"></script>\s*\n<script src="/palette\.js"></script>\s*\n</body>',
        src,
    ), "palette.js etiketi app.js'ten sonra ve </body>'den hemen önce değil"


def test_index_baska_script_eklenmemis():
    """Bu tur index.html'e TEK satır ekledi — üçüncü bir betik sızmadı."""
    src = INDEX.read_text()
    betikler = re.findall(r'<script src="([^"]+)"></script>', src)
    assert betikler == ["/theme.js", "/app.js", "/palette.js"], betikler


def test_api_palette_js_yolunu_sunar():
    """StaticFiles montajı YOK — yol ad ad yazılmazsa üretimde 404 ve palet hiç var olmaz.

    Bu, script etiketini eklemenin TEK BAŞINA yetmediği yer: yerelde dosya
    okunabilir görünüp canlıda sessizce kaybolan arıza sınıfı.
    """
    src = API.read_text()
    assert '@app.get("/palette.js")' in src, "api.py'de /palette.js yolu yok — üretimde 404"
    assert re.search(r'FileResponse\(WEB / "palette\.js"', src)


def test_palette_js_yolu_gercekten_kayitli():
    """Kaynak çivisi yolun YAZILDIĞINI söyler; bu test KAYITLI olduğunu söyler.

    Uygulama AYAĞA KALDIRILMAZ: `TestClient(app)` yaşam döngüsü olayları canlı
    `state/events.jsonl`e yazıyor (conftest'in canlı-yazım bekçisi bunu düşürüyor,
    doğru olarak). Rota tablosu ve işleyicinin döndürdüğü dosya yolu, HTTP'ye hiç
    çıkmadan aynı gerçeği kanıtlıyor.
    """
    from meridian.api import app

    rota = [r for r in app.routes if getattr(r, "path", None) == "/palette.js"]
    assert rota, "/palette.js rota tablosunda yok — üretimde 404 ve palet hiç var olmaz"
    yanit = rota[0].endpoint()
    assert pathlib.Path(yanit.path) == PALET, f"rota yanlış dosyayı sunuyor: {yanit.path}"
    assert "javascript" in yanit.media_type

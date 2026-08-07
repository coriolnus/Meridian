"""v155 — S2R-1: pano kabuğu (yedi alan sayfası + alias katmanı) ve Genel Bakış v1.

BU DOSYANIN ÖLÇTÜĞÜ KUSUR SINIFI: **yeniden yapılanmanın sessiz kaybı**. Bir bilgi mimarisi
değişiminde üç şey sessizce ölür ve üçü de yalnız kullanıldığı an fark edilir:

  A) KAYBOLAN İÇERİK — bir görünüm yeni IA'da bir ev bulamaz ve render'ı hiç çağrılmaz. Tablo
     öksüz kalır (YASA-6), ama pano çizilmeye devam ettiği için hiçbir şey kırmızı yanmaz.
  B) KIRILAN BAĞ — eski `#market` yer imi, palet komutu ya da sayfa-içi `data-a1="operasyon"`
     hedefi artık var olmayan bir rotaya işaret eder. `go()` sessizce hiçbir şey yapar.
  C) ŞİŞEN "TEK EKRAN" — Genel Bakış'ın sözleşmesi kaydırmasız olmaktır ve o sözleşme, bir kart
     daha eklemek her seferinde ucuz göründüğü için aşınır. Piksel ölçemeyiz; KART SAYISINI ve
     SÜTUN DÜZENİNİ ölçebiliriz ve tek ekranı fiilen bozan da bu ikisidir.

TESTLER KAYNAĞA BAKAR (repo deseni: v139/v151/v152/v154). Tarayıcı ve yerel sunucu YOK
(CLAUDE.md §5): dosyalar okunur.
"""
from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
WEB = SRC / "meridian" / "web"
APPJS = (WEB / "app.js").read_text()
INDEX = (WEB / "index.html").read_text()
PALETTE = (WEB / "palette.js").read_text()
# Yorum satırları çıkarılmış hâl (v154 deseni): bir kuralın GEREKÇESİNİ anlatan yorum, o
# kuralın ihlali sanılmamalı — "artık şuna bakmıyoruz" diye yazılmış bir cümle, tam da
# aranan dizgiyi içerir.
KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))

# index.html'in <style> bloğu — düzen sözleşmesi orada yaşıyor.
CSS = re.search(r"<style>(.*?)</style>", INDEX, re.S).group(1)

# BAĞLAYICI IA — docs/TASARIM-YONU-2026-08-07.md §3'ün BEŞ YÜZEYİ, EKRANDAKİ SIRAYLA.
# Sıra çivilidir çünkü çıplak 1-5 tuşları VIEWS sırasından türüyor: liste karışırsa kas
# hafızası sessizce yanlış sayfaya gider.
# ÇİVİ TAŞINDI, SÖKÜLMEDİ (D2-b): S2R'nin yedilisi iki birleşmeyle beşe indi
# (kosu+portfoy → karar, veri+gozetim → saglik, genel → bugun). Kural aynı kural.
ADR_SAYFALARI = ["bugun", "karar", "saglik", "ogrenme", "kilitler"]
# ESKİ ALAN SAYFALARI — bugün birer alias. Kapları YOK (yüzeyleri birleşti), yani alias
# doğrulaması bölüm alias'ından AYRI bir sınıftır (aşağıda ikisi de ölçülür).
ESKI_SAYFALAR = {"genel": "bugun", "kosu": "karar", "portfoy": "karar",
                 "veri": "saglik", "gozetim": "saglik"}

# S2R-1 öncesi on iki çizilebilir yüzey. Hiçbiri düşmez; her biri bir eve TAŞINIR.
ESKI_GORUNUMLER = ["brifing", "performans", "adaylar", "onaylar", "market", "intraday",
                   "ajan", "hermes", "skiller", "hafiza", "operasyon", "ayarlar"]


def _sozluk(ad: str) -> dict[str, str]:
    """app.js'teki `const <ad> = { k: "v", … };` bloğunu Python sözlüğüne indir."""
    blok = re.search(r"const %s = \{(.*?)\};" % ad, APPJS, re.S)
    assert blok, f"{ad} tanımlı değil"
    return dict(re.findall(r"(\w+):\s*\"([^\"]+)\"", blok.group(1)))


def _views() -> list[tuple[str, str]]:
    blok = re.search(r"const VIEWS = \[(.*?)\];", APPJS, re.S)
    assert blok, "VIEWS tanımlı değil"
    return re.findall(r'\["(\w+)", "([^"]+)"\]', blok.group(1))


def _govde(baslangic: str, bitis: str) -> str:
    """Kaynaktan bir gövde kes — `baslangic`ten `bitis`e kadar (ikisi de dahil değil)."""
    i = APPJS.index(baslangic)
    return APPJS[i:APPJS.index(bitis, i)]


def _kural(secici: str) -> str:
    """Satır başında duran (yani @media DIŞINDAKİ) CSS kuralının gövdesi."""
    m = re.search(r"\n%s\{([^}]*)\}" % re.escape(secici), CSS)
    assert m, f"{secici} kuralı yok (ya da yalnız bir @media içinde tanımlı)"
    return m.group(1)


# =================================================================================================
# 1) YEDİ ROTA — var, sıralı, çizilebilir
# =================================================================================================
def test_yedi_rota_ADR_sirasiyla_var():
    """Beş yüzey, yön belgesinin sırasıyla. Sıra bir zevk meselesi değil: çıplak 1-5 tuşları
    `VIEWS.findIndex` ile bu listeden türüyor."""
    assert [v for v, _ in _views()] == ADR_SAYFALARI


def test_her_rotanin_kabi_ve_render_i_var():
    """Rota üç şeyin buluşmasıdır: bir DOM kabı, bir render ve bir soru cümlesi. Üçünden biri
    eksikse rota bir vaattir — tıklanır, hiçbir şey olmaz."""
    sorular = _sozluk("EKRAN_SORUSU")
    bolumler = re.search(r"const ALAN_BOLUMLERI = \{(.*?)\n\};", APPJS, re.S)
    assert bolumler, "ALAN_BOLUMLERI tanımlı değil"
    kabuklu = set(re.findall(r"^\s*(\w+):\s*\[", bolumler.group(1), re.M))
    acik_render = set(re.findall(r"^RENDER\.(\w+) = ", APPJS, re.M))
    for sid in ADR_SAYFALARI:
        assert f'<section class="page' in INDEX and f'id="page-{sid}"' in INDEX, \
            f"page-{sid} kabı index.html'de yok"
        assert sid in kabuklu or sid in acik_render, f"RENDER.{sid} yok — sayfa çizilemez"
        assert sid in sorular, f"{sid}: soru cümlesi yok ('ekrana dök' yasağının çıpası)"


def test_page_sinifi_YALNIZ_yedi_yeni_sayfada():
    """`go()` aktifliği `.page` üzerinden çeviriyor. Eski kaplar da `.page` kalsaydı iç içe iki
    'aktif' sayfa doğar, gizli bölümdeki satırlar j/k gezinmesine girer ve ekran okuyucu
    görünmeyen içeriği okurdu."""
    sayfalar = re.findall(r'<section class="page[^"]*" id="page-(\w+)"', INDEX)
    assert sorted(sayfalar) == sorted(ADR_SAYFALARI), \
        f"`.page` taşıyan kaplar beş yüzeyle aynı değil: {sorted(sayfalar)}"
    assert INDEX.count('class="page active"') == 1, "birden fazla (ya da hiç) açılış sayfası"


def test_varsayilan_rota_tek_yerde_ve_genel():
    """Üç yerde ('baslat', ray, R tuşu) elle yazılmış bir varsayılan, üç ayrı yere kayabilir."""
    assert 'const VARSAYILAN_ROTA = "bugun";' in APPJS
    assert '|| "brifing"' not in APPJS, "eski varsayılan rota bir yerde elle kalmış"
    assert '|| "genel"' not in APPJS, "eski varsayılan rota bir yerde elle kalmış"


# =================================================================================================
# 2) ALIAS KATMANI — 12/12, ve alias'ın gittiği yerde içerik GERÇEKTEN var
# =================================================================================================
def test_alias_haritasi_eski_on_ikiyi_TAM_kapsar():
    """ÇİVİ GENİŞLEDİ, GEVŞEMEDİ (D2-b): alias artık İKİ sınıf taşır ve ikisi de TAM kapsanır —
    eski on iki GÖRÜNÜM (bugün birer bölüm) ve eski beş ALAN SAYFASI (yüzeyleri birleşti).
    İkinci sınıf olmadan `kosu#adaylar` / `portfoy#mutabakat` biçimindeki her eski adres —
    RUNBOOK bağları, çekmece çipleri, operatörün yer imleri — kırık bağa düşerdi."""
    alias = _sozluk("ROUTE_ALIAS")
    beklenen = set(ESKI_GORUNUMLER) | set(ESKI_SAYFALAR)
    assert sorted(alias) == sorted(beklenen), (
        f"alias'ı olmayan / fazladan alias'lanmış adres: {sorted(set(alias) ^ beklenen)}")
    hedefler = set(alias.values())
    assert hedefler <= set(ADR_SAYFALARI), f"tanınmayan alias hedefi: {hedefler - set(ADR_SAYFALARI)}"
    for eski, yeni in ESKI_SAYFALAR.items():
        assert alias[eski] == yeni, f"eski sayfa {eski} → {yeni} çözülmüyor (kırık derin bağ)"


def test_alias_hedefi_iceriğin_GERCEKTEN_durdugu_sayfadir():
    """Kusur sınıfı B'nin en sinsi biçimi: alias var, sayfa açılıyor, ama içerik BAŞKA sayfada.
    Bağ ölü değil — YANLIŞ, ve yanlış bağ ölü bağdan daha pahalıdır çünkü operatör aramayı
    bırakır. Bu yüzden her eski kabın DOM'da hangi sayfanın içinde olduğu ölçülür."""
    alias = _sozluk("ROUTE_ALIAS")
    # <main> içindeki tek <section> ailesi yedi sayfadır; bloklara onlardan bölünür.
    ana = INDEX[INDEX.index("<main id=\"main\">"):INDEX.index("</main>")]
    parcalar = re.split(r'(?=<section class="page)', ana)
    ev = {}
    for p in parcalar:
        m = re.match(r'<section class="page[^"]*" id="page-(\w+)"', p)
        if not m:
            continue
        for kap in re.findall(r'id="page-(\w+)"', p)[1:]:
            ev[kap] = m.group(1)
    for eski, hedef in alias.items():
        if eski in ESKI_SAYFALAR:
            # SAYFA ALIASI: kabı YOKTUR (yüzeyi birleşti). Ölçülecek şey hedefin GERÇEK bir
            # yüzey olması — çapa kısmı (`kosu#adaylar`) go()'nun çapa dalıyla ayrıca çözülür.
            assert f'id="page-{hedef}"' in INDEX, f"sayfa alias'ı {eski} → {hedef} boşa gidiyor"
            continue
        assert eski in ev, f"#page-{eski} kabı hiçbir alan sayfasının içinde değil — içerik kayıp"
        assert ev[eski] == hedef, (
            f"alias {eski} → {hedef} diyor ama kap {ev[eski]} sayfasının içinde: "
            "operatör doğru sayfaya gider, aradığı bölümü orada BULAMAZ")


def test_alias_ve_alan_bolumleri_ayni_gercegi_soyler():
    """Alias'ı OLAN her bölüm, alias'ının gösterdiği sayfanın altında çizilmeli. Ayrışırlarsa
    bir görünüm ya çizilir-ama-erişilemez ya erişilir-ama-çizilmez olur; ikisi de sessizdir.

    ÇİVİ TAŞINDI (S2R-2, silme yok): eski hâli "ALAN_BOLUMLERI'nin HER girdisinin bir alias'ı
    olmalı" diyordu ve bu S2R-1'de doğruydu — o zaman bölüm listesi eski on iki görünümün TAM
    kopyasıydı. S2R-2'de sekiz YENİ bölüm doğdu (mutabakat, kapilar, veriboru, intraemir,
    karne, golge, bilesenic, mudahale) ve hiçbiri bir eski yer imi DEĞİL. Onlara alias vermek,
    hiç var olmamış bir `#mutabakat` yer imini destekliyormuş gibi yapmak olurdu. Kural
    daraldı, gevşemedi: alias'ı olan bölüm için eşleşme hâlâ ZORUNLU."""
    alias = _sozluk("ROUTE_ALIAS")
    blok = re.search(r"const ALAN_BOLUMLERI = \{(.*?)\n\};", APPJS, re.S).group(1)
    for alan, liste in re.findall(r"^\s*(\w+):\s*\[([^\]]*)\]", blok, re.M):
        for bolum in re.findall(r'"(\w+)"', liste):
            if bolum not in alias or bolum in ESKI_SAYFALAR:
                continue                      # yeni bölüm ya da sayfa alias'ı — eski yer imi yok
            assert alias[bolum] == alan, \
                f"{bolum} kabuk tarafından {alan} altında çiziliyor ama alias'ı {alias[bolum]}"


def test_bolum_hatasi_SAYFAYI_dusurmez():
    """Birleşmenin doğrudan bedeli: Piyasa ile Intraday eskiden AYRI sayfalardı, biri düşse
    diğeri sağlamdı. Aynı sayfaya alındıkları an tek bir istisna sayfanın TAMAMINI 'Veri
    yüklenemedi' ekranına çevirirdi. Hata bölüm başına yalıtılır — ve YUTULMAZ (YASA 4): düşen
    bölüm kendi kabında ne olduğunu yazar."""
    # ÇİVİ TAŞINDI (S2R-2): kesme sınırı "\n// EŞLEME ROUTE_ALIAS'IN" idi ve o yorum bloğu
    # içerik göçüyle birlikte yeniden yazıldı (eşleme artık ROUTE_ALIAS'ın aynası DEĞİL).
    # Yeni sınır tablonun kendi başlığı — gövde aynı gövde, sınır adı güncel.
    fn = _govde("function alanSayfasi(id, bolumler) {", "\n// ---- S2R-2 · BÖLÜM → SAYFA")
    assert "try {" in fn and "catch (e)" in fn, "bölüm hatası yalıtılmıyor"
    assert "Bölüm yüklenemedi" in fn, "düşen bölüm sessiz kalıyor"
    assert "esc(String(e))" in fn, "istisna metni gösterilmiyor — sessiz yutma"
    assert "else throw e;" in fn, "kabı olmayan bölümün hatası görünmez kalıyor"


def test_eski_gorunumlerin_render_lari_SILINMEDI():
    """Geri dönüş sözleşmesi (ADR): eski render'lar S2R-2 sonuna dek silinmez — tek `git revert`
    ile dönüş mümkün kalsın."""
    for ad in ESKI_GORUNUMLER:
        assert f"RENDER.{ad} = " in APPJS, f"RENDER.{ad} silinmiş — içerik ve geri dönüş kaybı"


def test_ogrenme_yoklamalari_HASH_e_bakmiyor():
    """S2R-1'in sessizce kırabileceği en pahalı şey buydu: sprint ve Hermes yoklamaları
    `location.hash.includes("ajan")` diye soruyordu ve hash artık '#ogrenme'. Yoklama hiç
    dönmez, canlı arama ilerlemesi ekranda DONAR, hiçbir hata görünmez."""
    assert 'location.hash.includes("ajan")' not in KOD, \
        "yoklama hâlâ eski hash adına bakıyor — alias'lı bir rotada sessizce ölür"
    assert "const _ogrenmeAcik = () => !!$(\"page-ogrenme\")?.classList.contains(\"active\")" in APPJS
    assert APPJS.count("_ogrenmeAcik()") >= 4, "yoklamaların hepsi yeni kontrole geçmemiş"


# =================================================================================================
# 3) GENEL BAKIŞ v1 — kart bütçesi, tek bağ, özet-olma zorunluluğu
# =================================================================================================
def _genel_kartlari() -> list[tuple[str, str, str]]:
    blok = re.search(r"const GENEL_KARTLARI = \[(.*?)\n\];", APPJS, re.S)
    assert blok, "GENEL_KARTLARI tanımlı değil — kompozisyon sözleşmesi şablona gömülmüş"
    # HEDEF `sayfa` YA DA `sayfa#bolum` (v195-a): panonun geri kalanının adresleme dilinin aynısı.
    # Çapaya izin vermek "tek bağ" kuralını GEVŞETMEZ — bağın SAYISI değil, indiği YER değişti.
    return re.findall(r'\["(\w+)",\s*"([^"]+)",\s*"([\w#]+)"\]', blok.group(1))


def _alan_bolumleri() -> dict[str, list[str]]:
    blok = re.search(r"const ALAN_BOLUMLERI = \{(.*?)\n\};", APPJS, re.S)
    assert blok, "ALAN_BOLUMLERI tanımlı değil"
    return {alan: re.findall(r'"(\w+)"', ic)
            for alan, ic in re.findall(r"(\w+):\s*\[(.*?)\]", blok.group(1))}


def _render_genel() -> str:
    return _govde("RENDER.bugun = async () => {", "\n// ALARM BÜTÇESİ TEK SATIR")


def test_genel_bakis_kart_butcesi_alti_kartla_sinirli():
    """TEK EKRAN SÖZLEŞMESİ (ADR, 1440×900). Piksel-kesin ölçemeyiz — yazı tipi, tarayıcı, zum.
    Ama kart sayısı bir bütçedir ve altıncıdan sonrası tek ekranı fiilen yer. Sayı burada
    çivili; bir kart daha eklemek isteyen önce bu satırı değiştirmek ve gerekçelendirmek zorunda.
    """
    kartlar = _genel_kartlari()
    assert 0 < len(kartlar) <= 6, f"Genel Bakış {len(kartlar)} kart taşıyor — tek ekran bütçesi 6"
    anahtarlar = [k for k, _, _ in kartlar]
    assert len(set(anahtarlar)) == len(anahtarlar), "yinelenen kart anahtarı"


def test_her_kart_TEK_bag_tasir():
    """ADR: 'HER KART tek → alan sayfası bağı taşır; kart içinde detay YOK.' Kural ancak bağın
    TEK bir yerde üretilmesiyle sayılabilir olur — iki üretim noktası olsaydı 'tek bağ' bir
    vaat, testi de bir temenni olurdu."""
    assert APPJS.count('class="gb-kart') == 1, \
        "gb-kart birden fazla yerde üretiliyor — 'kart başına tek bağ' artık sayılamaz"
    fn = _govde("function gbKart(anahtar, govde) {", "\n// \"—\" ile \"0\"")
    assert fn.count("data-act=") == 1, f"gbKart {fn.count('data-act=')} eylem taşıyor, 1 olmalı"
    assert 'data-act="go" data-a1="${k.hedef}"' in fn, "bağ hedefi kart kaydından gelmiyor"
    # Kartın kendisi tıklanabilir DEĞİL: özet okurken en ucuz hata, kazara sayfa değiştirmektir.
    assert "<section class=\"gb-kart" in fn and "data-act" not in fn.split("<div class=\"gb-govde\"")[0]


def test_kart_hedefleri_gercek_alan_sayfalaridir():
    """Var olmayan bir rotaya işaret eden bir bağ, hiç işaret etmemekten kötüdür (v154 dersi).

    ÇAPA DA GERÇEK OLMAK ZORUNDA (v195-a): `go()` bulamadığı bir çapada SESSİZCE vazgeçer — yani
    yanlış yazılmış bir `sayfa#bolum` hedefi hiçbir hata vermez, yalnız kaydırma olmaz."""
    bolumler = _alan_bolumleri()
    for anahtar, _, hedef in _genel_kartlari():
        sayfa, _sep, capa = hedef.partition("#")
        assert sayfa in ADR_SAYFALARI, f"{anahtar} kartı tanınmayan sayfaya bağlıyor: {sayfa}"
        if capa:
            assert capa in bolumler.get(sayfa, []), (
                f"{anahtar} kartı {sayfa} sayfasında olmayan bir bölüme çapalıyor: {capa}")


def test_render_genel_kartlari_kayittan_cizer():
    """Kayıt ile çizim ayrışırsa bütçe testi yalan söyler: liste 6 der, ekranda 8 kart olur."""
    govde = _render_genel()
    cagri = re.findall(r'gbKart\("(\w+)"', govde)
    assert sorted(cagri) == sorted(k for k, _, _ in _genel_kartlari()), (
        f"çizilen kartlar kayıtla aynı değil: çizilen={sorted(cagri)}")


def test_genel_bakis_OZETTIR_detay_tablosu_tasimaz():
    """ADR: 'HEPSİ özet … kart içinde detay YOK. BAŞKA HİÇBİR ŞEY.' Bir tablo satırı (`trow`)
    tanım gereği detaydır ve bu sayfaya bir kez girdiğinde tek ekran sözleşmesi biter."""
    govde = _render_genel()
    for yasak in ("trow", "<table", "class=\"card"):
        assert yasak not in govde, f"Genel Bakış'a detay yüzeyi sızmış: {yasak}"


def test_alarm_butcesi_TEK_SATIR_kart_degil():
    """ADR alarm bütçesini kart değil TEK SATIR sayıyor. Kart olsaydı yedinci kart olur ve
    bütçeyi kart sayısıyla değil YÜKSEKLİĞİYLE sessizce yerdi."""
    fn = _govde("function gbAlarmSatiri(ab) {", "\n}\n")
    assert 'class="gb-alarm' in fn and "gb-kart" not in fn
    assert fn.count("data-act=") == 1, "tek satırın da tek bağı olmalı"
    assert 'data-act="go" data-a1="${hedef}"' in fn
    # Ölçülemeyen bütçe "0" ya da "sağlıklı" YAZMAZ.
    assert "ölçülmedi" in fn, "alarm bütçesi ölçülemediğinde uydurma sayı riski"


def test_genel_bakis_kaydirmasizligi_TEK_SUTUNA_dusmez():
    """Altı kart tek kolona dizilseydi sayfa ~2400px olur ve 'tek ekran' iddiası sessizce
    düşerdi. Sütun düzeni bu yüzden kuralın kendisinde çivili; tek sütuna iniş YALNIZ dar
    ekran sorgusunda olabilir (orada kaydırma zaten dürüst hâldir)."""
    for secici in (".gb-ust", ".gb-trend"):
        kural = _kural(secici)
        m = re.search(r"grid-template-columns:([^;]+)", kural)
        assert m, f"{secici} bir ızgara değil — düzen sözleşmesi ölçülemez"
        deger = m.group(1).strip()
        assert deger != "1fr", f"{secici} masaüstünde TEK SÜTUN — tek ekran sözleşmesi düşer"
        assert " " in deger or deger.startswith("repeat("), f"{secici}: tek parça izleme ({deger})"
    assert re.search(r"@media\([^)]*\)\{\.gb-ust,\.gb-trend\{grid-template-columns:1fr\}\}", CSS), \
        "dar ekran karşılığı yok — 980px altında üç kart yan yana sıkışırdı"


# =================================================================================================
# 4) SESSİZ HAT — her sayfada, TEK yerde
# =================================================================================================
def test_sessiz_hat_global_kapta_ve_TEK_kez_ciziliyor():
    """İş emrinin imza öğesi bugüne dek YALNIZ Operasyon sayfasında çiziliyordu: panonun
    hatırlanacak tek şeyi, operatörün en az açtığı sayfanın içinde yaşıyordu. Artık `<main>`in
    ilk çocuğu. İki çizim noktası olsaydı iki farklı tazelikte iki şerit doğardı."""
    assert 'id="sessizhat-global"' in INDEX, "global sessiz hat kabı yok"
    ana = INDEX[INDEX.index('<main id="main">'):INDEX.index("</main>")]
    assert ana.index('id="sessizhat-global"') < ana.index('<section class="page'), \
        "sessiz hat sayfaların ÜSTÜNDE değil"
    assert "position:sticky" in _kural(".sh-global"), "şerit sayfayla birlikte kayıp gidiyor"
    # Tanım (`function sessizHat(sh)`) sayılmaz; sayılan ÇAĞRI yerleridir.
    cagri = [m for m in re.findall(r"(?<!function )sessizHat\(([^)]*)\)", KOD) if m.strip()]
    assert len(cagri) == 1, f"sessiz hat {len(cagri)} yerden çiziliyor: {cagri}"
    assert "function sessizHatGlobal(sh)" in APPJS
    # Ölçülemediyse şerit BOŞ kalır, "sağlıklı" yazmaz.
    fn = _govde("function sessizHatGlobal(sh) {", "\n}\n")
    assert 'el.innerHTML = sh ? sessizHat(sh) : "";' in fn


def test_sessiz_hat_nabzi_15_saniyelik_turdan_gelir():
    """Şeridin her sayfada olması yetmez, her sayfada TAZE olmalı — yoksa 'sabit üstte' bir
    dekora dönüşür. Nabzı zaten dönen tur besler ve HALT satırını BEKLETMEZ."""
    fn = _govde("async function refreshStatus() {", "\n// Şerit tek yerde çizilir")
    assert 'j("/api/diagnostics").then(d => sessizHatGlobal(d && d.sessiz_hat))' in fn, \
        "şerit periyodik turdan beslenmiyor"
    assert "await j(\"/api/diagnostics\")" not in fn, \
        "teşhis ucu bekleniyor — bir alt sistemin yavaşlığı HALT satırını geciktiremez"


# =================================================================================================
# 5) KLAVYE, PALET, BAŞLIK HİYERARŞİSİ
# =================================================================================================
def test_g_kisayollari_yedi_sayfayi_kapsar():
    esleme = _sozluk("GIT_KISAYOL")
    assert sorted(esleme.values()) == sorted(ADR_SAYFALARI), \
        f"g-eşlemesi yeni IA ile ayrışmış: {sorted(set(esleme.values()) ^ set(ADR_SAYFALARI))}"
    assert len(set(esleme)) == len(ADR_SAYFALARI), "iki yüzey aynı harfi paylaşıyor"


def test_palet_gorunum_hedefleri_COZULEBILIR():
    """Palet bir eylemi çalıştırmadan önce ilgili görünüme geçiyor (`gorunum: "ajan"`), çünkü
    eylemler sonucunu SAYFAYA AİT bir düğüme yazıyor. Hedef çözülemezse POST atılır ama sonuç
    hiçbir yerde görünmez — sessiz bir yazma işlemi. Eski adlar alias sayesinde çözülüyor;
    ÇÖZÜLDÜĞÜ burada ölçülür, umulmaz."""
    alias = _sozluk("ROUTE_ALIAS")
    gecerli = set(ADR_SAYFALARI) | set(alias)
    hedefler = re.findall(r'gorunum: "([\w#]+)"', PALETTE) + \
        re.findall(r'gorunumeGec\("([\w#]+)"\)', PALETTE)
    assert hedefler, "palet hiçbir görünüme geçmiyor — komutlar sessiz yazma riski taşır"
    for h in hedefler:
        assert h.split("#")[0] in gecerli, f"palet çözülemeyen bir rotaya gidiyor: {h}"


def test_ray_etiketleri_KESILMEZ():
    """Yeni IA'nın adları eskisinden uzun ("Kilitler & Yapılandırma" 23 karakter) ve ray 208px.
    Mevcut `text-overflow:ellipsis` onu "Kilitler & Yapılandır…" diye keserdi: yarım okunan bir
    menü maddesi, hiç okunmayandan daha yanıltıcıdır — kullanıcı gördüğünü TAM sanır."""
    kural = _kural(".side .sitem .vis-label")
    assert "white-space:normal" in kural, "ray etiketi hâlâ tek satıra zorlanıyor"
    assert "text-overflow:clip" in kural, "kesme (ellipsis) hâlâ yürürlükte"
    assert "align-items:flex-start" in _kural(".side .sitem .top"), \
        "iki satıra saran maddede ikon ortalanır ve ilk satırdan kayar"


def test_palet_gezinmesi_RAYDAN_turer():
    """Yedi maddelik yeni ray palete elle kopyalanmaz: kopyalansaydı bu tur paleti sekiz eski
    adla bırakırdı ve kimse fark etmezdi."""
    assert "document.querySelectorAll('.sitem[data-p]')" in PALETTE


def test_bolum_basliklari_h2_ye_iniyor_ve_her_cizimde():
    """Eski görünümlerin her biri kendi `<h1>`ini basıyor — o zaman her biri bir SAYFAYDI.
    Artık bölümler; sayfada birden çok h1 bırakmak 'bu sayfa neyin sayfası?' sorusunu cevapsız
    bırakır. Düzeltme `revealActive` içinde olmak ZORUNDA: eski görünümlerin çoğu kendini
    yeniden çiziyor (sprint/Hermes yoklaması, intradayArm, ackReject, saveSecret) ve her
    yeniden çizim kendi h1'ini geri koyuyor."""
    assert "function _bolumBasliklariniIndir(kok)" in APPJS
    fn = _govde("function _bolumBasliklariniIndir(kok) {", "\n}\n")
    assert 'kok.querySelectorAll(".alan-bolum h1")' in fn
    ra = _govde("function revealActive(instant) {", "\naddEventListener(\"hashchange\"")
    assert "_bolumBasliklariniIndir(document.querySelector(\".page.active\"))" in ra, \
        "düzeltme yalnız açılışta koşuyor — ilk yoklamada geri düşer"


def test_yeni_yuzeyde_satir_ici_olay_yok():
    """CSP `script-src 'self'` satır içi işleyicileri bloklar (bkz. test_web_csp_uyum).
    Yeni kabuk ve Genel Bakış da o kurala tabi — burada erken yakalanır."""
    for parca in (_render_genel(), _govde("function gbKart(anahtar, govde) {", "\n// \"—\" ile \"0\"")):
        assert not re.search(r'\son[a-z]+\s*=\s*["\']', parca), "satır içi olay özniteliği"


def test_yeni_CSS_jeton_disi_renk_kullanmaz():
    """Omega kuralı: renk taşıyan hiçbir değer kuralın içinde yazılmaz, jetondan gelir —
    aksi hâlde ikinci tema sessizce kırılır."""
    blok = CSS[CSS.index("S2R-1 · ALAN SAYFASI KABUĞU"):]
    blok = blok[:blok.index("/* ---- DURUM ŞERİDİ")] if "/* ---- DURUM ŞERİDİ" in blok else blok
    for kotu in re.findall(r"(#[0-9a-fA-F]{3,8}|rgba?\()", blok):
        raise AssertionError(f"S2R-1 CSS'inde jeton dışı renk: {kotu}")

"""v191/v192 — DURUM KART-IZGARASI + HÜCRE ANATOMİSİ.

OPERATÖR BULGUSU (2026-08-06): "Koşu & Döngü ile Portföy ve Emirler çakışıyor, benzer şeyleri
gösteriyorlar; kartlara bölüp tıklayınca detay."

İKİNCİ TUR — v192 (aynı gün, ekran görüntüsüyle): "durum bandını ve iki sayfanın bölüm içeriklerini
panodaki MEVCUT setup×rejim karne matrisinin hücre-mimarisine çevir." Ölçülen kusur sınıfı bu turda
ÇİFT-KAYNAK değil, ÇİFT-DİL: aynı büyüklük (bir ölçüm ve onun kanıt gücü) panoda üç ayrı biçimde
yazılıyordu — `.durum-say`+`.durum-alt`, `.mcard` döşemesi, `.srow` satırı — ve ÜÇÜNDEN HİÇBİRİ
örneklemi/paydayı taşımıyordu. Yalnız matris taşıyordu (`.pm-conf` güven rayı): 3 işlemlik bir
ortalama ile 55 işlemlik bir ortalama orada birbirine benzemiyordu, panonun geri kalanında ise
benziyordu. v192 matrisin dilini ORTAKLAŞTIRIR; ikinci bir hücre ailesi AÇMAZ.

Bu dosyanın §9 bölümü o anatominin sözleşmesini çivi ler: çubuk paydasız çizilmez, ölçülemeyen
değer "VERİ YOK" dalına düşer (uydurma sıfır yok), rozet koşulludur, sınıflar TEK yerde tanımlıdır.

BİRİNCİ TUR — v191 (§1-§8). Ölçülen kusur sınıfının adı ÇİFT-KAYNAK: aynı gerçek iki yüzeyden
anlatılır, ikisi ayrı kodda yaşar, biri güncellenir diğeri bayatlar — ve operatör hangisinin doğru
olduğunu ekrandan öğrenemez. Dört ölçülmüş biçimi vardı:

  A) SERMAYE/GÜN K/Z/POZİSYON SAYISI — Portföy'ün kahraman bloğunda ve kenar şeridinde.
  B) GÜNÜN PLANLARI — Portföy'ün "Son sinyaller" kartında (`planRowBrief`) ve Koşu'nun `adaylar`
     bölümünde (`planRowFull`). AYNI satırlar, iki çizici, iki başlık.
  C) REJİM TAVANI / SATIŞ GÜNÜ / FTD — Portföy'ün "Risk" sütununda ve Koşu'nun `kapilar` bölümünde.
  D) SİLAHLI EMİR + AYNA DURUMU — kahraman bloğun "Ajan" sütununda, `nextSessionCard` çiplerinde ve
     `mutabakat` masasında; hiçbiri "kaç tane silahlı, kaçı gitti, kaçı doldu" sorusunu tek bakışta
     cevaplamıyordu.

TESTLER app.js/index.html KAYNAĞINA BAKAR (repo deseni: test_empty_gauge_honesty_v79,
test_pano_turu_v139): kusur da orada yaşıyor ve bir alanın API'de var olması onun PANODA okunduğu
anlamına gelmez. YASA-6 pariteleri iki yönde de zorlanır — kaldırdığımız her okuyucu için alanın
BAŞKA bir okuyucusu olduğu, eklediğimiz her API alanı için de bir okuyucu olduğu ölçülür.
"""
from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
APPJS = (SRC / "meridian" / "web" / "app.js").read_text()
INDEX = (SRC / "meridian" / "web" / "index.html").read_text()
APIPY = (SRC / "meridian" / "api.py").read_text()

# YORUM SATIRLARI SAYILMAZ: bu turun her silmesi kaldırdığı bloğu GEREKÇESİYLE birlikte yazıyor
# ("eski hâl şuydu, neden çakışmaydı"). O gerekçe kaynakta durmalı ama "hâlâ orada" diye
# okunmamalı — yoksa doğru davranan bir silme kendi belgesi yüzünden düşer (v139/v155 deseni).
KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))
# CSS tarafında da aynı ayrım: v192 sildiği her kuralı gerekçesiyle yazıyor ("`.durum-say` SİLİNDİ,
# çünkü …"). O gerekçe kalmalı ama BİLDİRİM sanılmamalı.
CSS_KOD = re.sub(r"/\*.*?\*/", "", INDEX, flags=re.S)

# Kart gövdeleri ve çekmece kurucuları — testlerin çoğu bu dar bölgeye bakar.
_KART_GOVDE = {
    "dongu":    ("function _durumDonguKarti(", "\n// ---- ② KİTAP"),
    "kitap":    ("function _durumKitapKarti(", "\n// ---- ③ EMİRLER"),
    "emir":     ("function _durumEmirKarti(", "\n// ---- ④ POZİSYONLAR"),
    "pozisyon": ("function _durumPozisyonKarti(", "\n// Etkin stop ="),
}
_CEKMECE_GOVDE = {
    "dongu":    ("  durumDongu(o) {", "\n  durumKitap(o) {"),
    "kitap":    ("  durumKitap(o) {", "\n  durumEmir(o) {"),
    "emir":     ("  durumEmir(o) {", "\n  durumPozisyon(o) {"),
    "pozisyon": ("  durumPozisyon(o) {", "\n  // 0a · REDDEDİLEN"),
}


def _govde(baslangic: str, bitis: str, kaynak: str = APPJS) -> str:
    i = kaynak.index(baslangic)
    return kaynak[i:kaynak.index(bitis, i)]


def _kart_bolgesi() -> str:
    """Dört kart gövdesi + dört çekmece kurucusu. `?? 0` gibi ARAMALAR bu bölgeye kapatılır:
    panonun başka yerlerinde (ör. mutabakat masasının icra kartı) aynı desen BAŞKA bir sözleşme
    altında ve BAŞKA bir alan için kullanılıyor olabilir; oraya bu turun kuralını dayatmak, testi
    ilgisiz bir bloğu kırdığı için kırmızıya çeviren bir ağ hâline getirirdi."""
    parcalar = [_govde(*v) for v in _KART_GOVDE.values()]
    parcalar += [_govde(*v) for v in _CEKMECE_GOVDE.values()]
    return "\n".join(parcalar)


def _liste(ad: str) -> list[tuple[str, str]]:
    blok = re.search(r"const %s = \[(.*?)\n\];" % ad, APPJS, re.S)
    assert blok, f"{ad} tanımlı değil"
    return re.findall(r'\["(\w+)",\s*"([^"]+)"\]', blok.group(1))


# =================================================================================================
# 1) IZGARANIN KENDİSİ — dört kart, tek tanım, iki sayfa
# =================================================================================================
def test_dort_kart_ve_sayilari_veri_olarak_durur():
    """Kart sayısı bir TASARIM BÜTÇESİdir (Genel Bakış'ın altı kartıyla aynı gerekçe): beşincisi
    ızgarayı tek satırdan taşırır ve "tek bakış" iddiasını sessizce yer. Liste veri olduğu için
    test onu SAYABİLİYOR; şablona gömülü olsaydı sayılamazdı."""
    kartlar = _liste("DURUM_KARTLARI")
    assert [k for k, _ in kartlar] == ["dongu", "kitap", "emir", "pozisyon"], kartlar
    assert len(kartlar) == 4, f"kart bütçesi aşıldı/eksildi: {kartlar}"


def test_izgara_YALNIZ_cakisan_iki_sayfada():
    """Izgara çakışmayı KAPATMAK için var. Üçüncü bir sayfaya yayılsaydı çakışmayı çözmek yerine
    büyütürdü; Genel Bakış'ın kendi altı kartı zaten aynı soruların 60 saniyelik hâli."""
    m = re.search(r'const DURUM_SAYFALARI = new Set\(\[([^\]]*)\]\);', APPJS)
    assert m, "DURUM_SAYFALARI tanımlı değil"
    # ÇİVİ TAŞINDI (D2-b): çakışan İKİ sayfa BİRLEŞTİ (kosu+portfoy → karar), yani ızgaranın
    # var oluş sebebi olan çakışma KÖKÜNDEN kapandı ve `durumIzgarasiCiz` çağrısı ikiden bire
    # indi. Kural aynı kural ve bir kademe SERTLEŞTİ: ızgara TEK yüzeyde çizilir.
    assert sorted(re.findall(r'"(\w+)"', m.group(1))) == ["karar"]


def test_izgara_TEK_yerde_uretilir():
    """İki sayfa aynı ızgarayı gösteriyor; iki KOPYA olsaydı biri güncellenip diğeri bayatlardı —
    yani bu turun kapattığı kusurun kendisini ızgaranın içinde yeniden üretirdik."""
    assert KOD.count("function durumIzgarasiHTML(") == 1
    assert KOD.count('<div class="durum-izgara">') == 1, \
        "ızgara gövdesi birden fazla yerde kuruluyor — tek tanım sözleşmesi kırıldı"
    for fn in ("_durumDonguKarti", "_durumKitapKarti", "_durumEmirKarti", "_durumPozisyonKarti"):
        assert KOD.count(f"function {fn}(") == 1, f"{fn} tek tanımlı değil"


def test_kabuk_izgarayi_recReset_SONRASINDA_cizer():
    """Kartların çekmece anahtarları `rec()` ile yazılır ve `recReset()` `_REC` haritasını SİLER.
    Izgara sıfırlamadan ÖNCE çizilseydi dört kart da "kayıt bulunamadı" ile açılırdı — ekranda
    duran, tıklanan, hiçbir şey göstermeyen bir kart: S2R-2'nin `ajan` vakasının aynısı."""
    govde = _govde("function alanSayfasi(id, bolumler) {", "\n// ---- S2R-2 · BÖLÜM → SAYFA")
    kod = "\n".join(l for l in govde.splitlines() if not l.lstrip().startswith("//"))
    assert "recReset();" in kod and "durumIzgarasiCiz(" in kod
    assert kod.index("recReset();") < kod.index("durumIzgarasiCiz("), \
        "ızgara recReset'ten ÖNCE çiziliyor — kayıt anahtarları hemen siliniyor"
    # Kap ID İLE DEĞİL SORGUYLA bulunur: iki sayfanın ızgarası DOM'da aynı anda durur ve sabit bir
    # id, `$()` yüzünden her zaman belge sırasındaki ilkini (kosu) döndürürdü.
    assert 'querySelector(".durum-izgara-kap")' in kod
    assert 'id="durum-izgara"' not in APPJS, "ızgara kabına sabit id verilmiş — ikinci sayfa hiç dolmaz"


# =================================================================================================
# 2) ÇEKMECE — mevcut desen yeniden kullanıldı, yeni bileşen İCAT EDİLMEDİ
# =================================================================================================
def test_her_kartin_kaydi_ve_cekmece_kurucusu_var():
    """Kart ÜÇ şeyin buluşmasıdır: bir `rec()` kaydı, bir `RECORD_VIEW` kurucusu ve bir düğme.
    Üçünden biri eksikse kart bir vaattir — tıklanır, hiçbir şey açılmaz."""
    kinds = set(re.findall(r'rec\("(durum\w+)"', APPJS))
    assert kinds == {"durumDongu", "durumKitap", "durumEmir", "durumPozisyon"}, kinds
    rv = _govde("const RECORD_VIEW = {", "\n  // 0a · REDDEDİLEN GÖNDERİM")
    for k in sorted(kinds):
        assert re.search(r"^  %s\(o\) \{" % k, rv, re.M), f"RECORD_VIEW.{k} yok — kart açılamaz"


def test_kart_bir_dugme_ve_ortak_kayit_baglayicisini_kullanir():
    """Klavye sözleşmesi (H23): kart `<button>` olduğu için Tab ile gezilir ve Enter/Space
    tarayıcının kendi düğme davranışıyla açılır — ikinci bir tuş dinleyicisi YAZILMAZ.
    `rowAttrs` odak dönüşünü, `aria-label`i ve `data-rk` bağını planla/matrisle AYNI yapar."""
    govde = _govde("function durumKartHTML(", "\n// Döngü tazelik çubuğunun penceresi")
    assert '<button class="durum-kart' in govde
    assert "rowAttrs(kayitK" in govde, "kart kendi bağını icat ediyor — ortak kayıt defteri atlandı"
    assert 'role="button"' not in govde, "düğme yerine role=button — klavye sözleşmesi ikiye ayrıldı"
    # v192: gövde artık `hucreGovde` ile kurulur — kart kendi sayı dilini yazmaz.
    assert "hucreGovde(hucre)" in govde, "kart gövdesi ortak hücre anatomisinden geçmiyor"


def test_secili_isaretin_seçicisi_TEK_yerde():
    """`openRecord` işareti KOYAR, `closeDrawer` KALDIRIR. Liste iki yerde elle tutulsaydı yeni
    yüzey (durum kartı) `.sel` sınıfını üstünde bırakırdı: çekmece kapalıyken hâlâ seçili görünen
    bir kart — sessiz ve yalnız gözle fark edilir."""
    assert 'const _SECILI = ".pm-cell.sel,.rowbtn.sel,.durum-kart.sel";' in APPJS
    assert KOD.count("querySelectorAll(_SECILI)") == 2
    assert '.pm-cell.sel,.rowbtn.sel"' not in KOD, "eski elle yazılmış seçici bir yerde kalmış"


# =================================================================================================
# 3) TEK KAYNAK — aynı sayı iki kartta DURMAZ
# =================================================================================================
# Her sayı TEK bir kartın işidir. Sol taraf kaynak ifadesi, sağ taraf sahibi olan kart.
_SAHIP = {
    "t.equity":                  "kitap",
    "kk.gercek_canli_sermaye":   "kitap",
    "kk.canli_pnl_usd":          "kitap",
    "kb.day_start_equity":       "kitap",
    "t.day_pnl_pct":             "kitap",
    "sd.candidates":             "dongu",
    "sd.plans":                  "dongu",
    "sd.armed":                  "dongu",
    "sd.yas_saat":               "dongu",
    "t.armed_plans":             "emir",
    "t.alpaca_submitted":        "emir",
    "dl.n_dolan":                "emir",
    "rc.stream_ok":              "emir",
    "t.open_positions":          "pozisyon",
}


def test_ayni_sayi_iki_kartta_gosterilmez():
    """Operatörün şikâyetinin ızgara-içi hâli. Aynı sayının ikinci kopyası bir HİYERARŞİ gibi
    okunur ("demek ki bu önemli"); yoktur, yalnızca kopyadır — ve kopyalar ayrışır."""
    govdeler = {k: _govde(*v) for k, v in _KART_GOVDE.items()}
    for ifade, sahip in _SAHIP.items():
        gorunen = [k for k, g in govdeler.items() if ifade in g]
        assert gorunen == [sahip], \
            f"`{ifade}` {sahip} kartına ait ama {gorunen} kart(lar)ında okunuyor"


# =================================================================================================
# 4) DÜRÜSTLÜK-UI — None ≠ 0, ölçülemeyen alan NEDENİYLE durur (UYDURMA YASAĞI)
# =================================================================================================
def test_olculmeyen_alan_sifir_yazmaz():
    """Bu panonun birinci yasası. Dört alan da ölçülemeyebilir ve dördü de `0` DEĞİL bir CÜMLE
    basmak zorunda: gün-başı tabanı (kitapta yok), dolan emir (icra defteri boş), toplam ısı
    (size_r taşımayan satır), stop mesafesi (giriş/stop okunamadı)."""
    bolge = _kart_bolgesi()
    # Izgaranın HİÇBİR yerinde ölçülmemiş bir alan sıfıra düşürülmez.
    assert "?? 0" not in bolge, "durum ızgarasında bir alan sıfıra düşürülüyor (None ≠ 0)"

    g = _govde("function _durumKitapKarti(", "\n// ---- ③ EMİRLER")
    assert "kb.day_start_equity == null" in g and "ölçülmedi" in g
    assert "kk.canli_pnl_usd == null" in g

    g = _govde("function _durumEmirKarti(", "\n// ---- ④ POZİSYONLAR")
    assert "dl.n_dolan == null" in g, "dolan emir ölçülemediğinde tire yerine sayı basılıyor"
    assert "slp.durum" in g, "ölçüm yoksa SEBEP basılmıyor — uydurma boşluk"
    # ÇİVİ TAŞINDI (D2-b · P5 tekilleştirmesi): akışın DEĞERİ artık bu kartta yazmıyor —
    # tek evi mutabakat masası. Kart yalnız ANOMALİ hâlinde konuşur, çünkü o zaman cümle
    # taşıdığı "kopuk" rozetinin gerekçesidir. Ölçülen şey aynı kaldı: üçüncü hâl (hiç kanıt
    # yok) KOPUK ile aynı kovaya DÜŞMEZ — `akis === false` üçlü ayrımı koruyan tek testtir.
    assert "rc.stream_ok" in g and "akis === false" in g, \
        "akış üçüncü hâli (hiç kanıt yok) KOPUK ile aynı kovaya düşüyor"
    assert "mutabakat masasında (tek ev)" in g, \
        "P5 tekilleştirmesi geri alınmış — akışın değeri ikinci kez yazılıyor"

    g = _govde("function _durumPozisyonKarti(", "\n// Etkin stop =")
    assert "isiOlculdu" in g and "ölçülemedi" in g, \
        "size_r taşımayan satır varken toplam ısı yine de toplanıyor — eksik toplam, tam gibi okunur"
    assert "enYakin == null" in g


def test_gerceklesmis_KZ_karti_defter_toplamini_DEGIL_gercek_canliyi_gosterir():
    """CANLI ÖLÇÜM (2026-08-06): `portfolio.realized_pnl` = −5.542,09$ ve bu sayının tamamı
    antrenman tohumundan geliyor; gerçek-canlı işlem sayısı SIFIR. O toplamı karta KIRMIZI basmak,
    `meridian/sermaye.py`nin var olma sebebi olan yanlış okumayı geri getirirdi ("bir eğitim
    artefaktını sistemin kaybı diye okumak"). Defter toplamı ÇEKMECEDE, tohum ayrıştırmasının
    yanında ve etiketiyle durur."""
    kart = _govde("function _durumKitapKarti(", "\n// ---- ③ EMİRLER")
    assert "kk.canli_pnl_usd" in kart and "gerçek-canlı" in kart
    assert "kb.realized_pnl" not in kart, "defter toplamı (tohum dahil) kartın kendisinde"
    cekmece = _govde("  durumKitap(o) {", "\n  durumEmir(o) {")
    assert "kb.realized_pnl" in cekmece and "tohum dahil" in cekmece


def test_son_dongu_kaydi_yoksa_SUNUCUNUN_nedeni_basilir():
    """"Sıfır aday" ile "ölçülemedi" AYRI şeylerdir ve uç bunu `neden` alanıyla söylüyor (v190).
    Pano ikinci bir açıklama UYDURMAZ."""
    g = _govde("function _durumDonguKarti(", "\n// ---- ② KİTAP")
    assert "sd.var" in g and "sd.neden" in g
    assert "sıfır aday DEĞİL" in g.lower() or "ölçülemedi" in g


def test_beyan_ofset_rozeti_YALNIZ_beyan_varken_cizilir():
    """`sermaye_koken.ayrisik` false iken rozet HİÇ çizilmez. "ofset 0" yazmak, hiç yapılmamış bir
    sermaye beyanını yapılmış gibi göstermek olurdu — kitabın en pahalı yanlış okuması."""
    g = _govde("function _durumKitapKarti(", "\n// ---- ③ EMİRLER")
    assert "kk.ayrisik" in g and "beyan-ofset" in g
    # Rozet bir KOŞULUN içinde doğar; koşulsuz basılsaydı beyan yokken de görünürdü.
    assert re.search(r"kk\.ayrisik\s*\n?\s*\?", g), "rozet koşulsuz basılıyor"


def test_stop_mesafesi_CARI_FIYAT_iddia_etmez():
    """Kitapta cari fiyat YOK (portfolio.positions entry/stop/trail_stop taşır). "Cari fiyata
    mesafe" yazmak ölçmediğimiz bir şeyi ölçmüş gibi göstermek olurdu; etiket ölçtüğümüzü söyler."""
    g = _govde("function _durumPozisyonKarti(", "\n// Etkin stop =")
    assert "girişin altında" in g and "cari fiyat" in g
    fn = _govde("function _durumStopMesafeleri(", "\n// ---- IZGARANIN KENDİSİ")
    assert "trail_stop" in fn and "return null" in fn, \
        "giriş/stop okunamayan satır 0 sayılıyor olabilir — düşmeli"


# =================================================================================================
# 5) HUNİ — üç basamak AYNI PAYDADAN gelmiyor ve bu BEYAN EDİLİYOR
# =================================================================================================
def test_huni_paydalari_beyanli():
    """İlk iki basamak ŞU ANKİ silahlı kümeden (portfolio.armed × alpaca_submitted), üçüncüsü icra
    defterinin PENCERESİNDEN gelir. Üçünü tek bir huni gibi yazmak, farklı paydaları aynı sanmaktır
    — ve o hata sessizdir: sayılar toplanır, kimse sormaz."""
    g = _govde("function _durumEmirKarti(", "\n// ---- ④ POZİSYONLAR")
    assert "slp.pencere_gun" in g, "dolan sayısının PENCERESİ ekranda yazmıyor"
    rv = _govde("  durumEmir(o) {", "\n  durumPozisyon(o) {")
    assert "aynı payda değildir" in rv


def test_gonderilecekte_kalan_plan_bir_bakista_gorunur():
    """Operatörün adını koyduğu vaka: silahlı ama ne aynaya gitmiş ne reddedilmiş bir plan. Bugüne
    kadar yalnız `nextSessionCard` satırındaki küçük bir çipte vardı — yani ancak tabloyu satır
    satır okuyan görürdü."""
    g = _govde("function _durumEmirKarti(", "\n// ---- ④ POZİSYONLAR")
    assert "bekleyen" in g and "gönderilecekte kaldı" in g
    # v192: anomali NOKTASI kaldırıldı, kanal tek — hücrenin mürekkebi renklenir ve rozet doğar.
    assert 'anomali: "uyari"' in g, "bekleyen plan varken kartta anomali rengi yok"
    assert 'rozet: bekleyen ? "BEKLİYOR"' in g, "bekleyen plan varken rozet çipi doğmuyor"


# =================================================================================================
# 6) ÇAKIŞMA KAPANDI — Portföy'deki İKİZ bloklar gitti, alanları ÖKSÜZ kalmadı (YASA 6)
# =================================================================================================
def test_brifing_kahraman_blogu_ve_son_sinyaller_karti_gitti():
    """Çakışmanın ölçülmüş gövdesi bu ikisiydi. `.hero` üç sütunun üçünde de başka bir yüzeyin
    sayısını tekrarlıyordu; "Son sinyaller" ise Koşu'daki `adaylar` tablosunun AYNISIYDI."""
    g = _govde("RENDER.brifing = async () => {", "\nfunction staleBits(p) {")
    kod = "\n".join(l for l in g.splitlines() if not l.lstrip().startswith("//"))
    assert '<div class="hero rise">' not in kod, "kahraman bloğu hâlâ Portföy'de — çakışma sürüyor"
    assert "Son sinyaller" not in kod, "plan tablosu hâlâ iki sayfada"
    assert "planRowBrief" not in kod
    # Bölüm boşalmadı: kartın SAYISI ızgarada, satırları burada.
    assert "nextSessionCard(t)" in kod and "posRows" in kod


def test_planRowBrief_silindi_ve_alanlari_planRowFull_da_okunuyor():
    """ÖLÜ KOD DEĞİL, İKİZ KOD: iki çizici aynı satırları çiziyordu. Silmenin şartı YASA-6'dır —
    okuduğu her alanın başka bir okuyucusu olmalı."""
    assert "function planRowBrief(" not in APPJS
    full = _govde("function planRowFull(p) {", "\n// ================= ÖĞRENME")
    for alan in ("gate_verdict", "gate_reasons", "r_multiple_expected", "ticker"):
        assert alan in full, f"planRowFull `{alan}` okumuyor — silme bir alanı öksüz bıraktı"
    # `setup`/`score`/`size_r` çekmecede (RECORD_VIEW.plan) ve kapı kaydında okunuyor.
    assert 'rec("plan", p)' in full


def test_kahramandan_dusen_alanlarin_BASKA_okuyucusu_var():
    """Silinen bir bloğun TEK okuyucusu olduğu alan, silmeyle birlikte sessizce körleşir. Beş alan
    tek tek kontrol edilir: rejim tavanı, açıktaki risk, satış günü, FTD ve strateji sürümü."""
    parite = {
        "exposure_budget_pct": "rejim maruziyet tavanı",
        "current_exposure_pct": "açıktaki risk",
        "distribution_days": "satış günleri",
        "ftd": "follow-through günü",
        "strategy_version": "strateji sürümü",
    }
    for alan, ad in parite.items():
        assert alan in KOD, f"{ad} (`{alan}`) panoda hiç okunmuyor — kahraman bloğuyla birlikte düştü"
    # FTD ve açıktaki risk artık ÇEKMECELERDE yaşıyor; adresleri çivilenir ki bir sonraki
    # düzenleme onları "kimse okumuyor" diye silmesin.
    assert "r.ftd" in _govde("  durumDongu(o) {", "\n  durumKitap(o) {")
    assert "t.current_exposure_pct" in _govde("  durumPozisyon(o) {", "\n  // 0a · REDDEDİLEN")
    assert "s.strategy_version" in _govde("  durumKitap(o) {", "\n  durumEmir(o) {")


def test_pozisyon_sayisi_artik_TEK_yerde():
    """Sayı ④ POZİSYONLAR kartının; "Açık pozisyonlar (N)" başlığındaki kopya düştü."""
    g = _govde("RENDER.brifing = async () => {", "\nfunction staleBits(p) {")
    assert 'Açık pozisyonlar (' not in g, "başlıkta hâlâ ikinci bir pozisyon sayacı var"


# =================================================================================================
# 7) API PARİTESİ — yeni alanlar var VE okunuyor (YASA 6, iki yön)
# =================================================================================================
def test_api_today_kitap_blogu_uc_alani_verir():
    blok = _govde('d["kitap"] = {', "return d", APIPY)
    for alan in ("realized_pnl", "day_start_equity", "peak_equity"):
        assert f'"{alan}"' in blok, f"/api/today.kitap.{alan} verilmiyor"
    # Beyan ofseti burada TEKRARLANMAZ: `sermaye_koken` onu zaten taşıyor ve aynı sayının iki alanı
    # ilk düzenlemede sessizce ayrışır.
    assert "ofset" not in blok


def test_kitap_blogunun_her_alaninin_panoda_okuyucusu_var():
    for alan in ("realized_pnl", "day_start_equity", "peak_equity"):
        assert f"kb.{alan}" in KOD, f"kitap.{alan} üretiliyor ama pano okumuyor (YASA 6)"


def test_kitap_bloğu_TURETMEZ_kitaptan_okur():
    """`day_start_equity`i `equity/(1+day_pnl_pct)` diye hesaplamak ikinci bir taban yasası
    doğururdu — kitabınki ile panonunki aynı gün ayrışabilirdi (`sermaye.koken`in "iki hesap"
    kusuru). Alan kitaptan OKUNUR."""
    blok = _govde('d["kitap"] = {', "return d", APIPY)
    assert "_pf.get(" in blok and "day_pnl_pct" not in blok


def test_portfolio_json_TEK_kez_okunur():
    """`latest_session` ve `kitap` aynı dosyadan gelir. İki ayrı `read_json` çağrısı, tek istekte
    dosyanın İKİ farklı anını okuyabilirdi (worker araya yazarsa) — tek yanıtta iki gerçek olamaz."""
    g = _govde("def api_today(request: Request):", "@app.get(\"/api/signals\")", APIPY)
    assert g.count('read_json("portfolio.json"') == 1, "portfolio.json bu uçta birden fazla okunuyor"


# =================================================================================================
# 8) WP-P YASALARI — jeton, ritim, hareket, erişilebilirlik
# =================================================================================================
def test_izgara_YENI_RENK_JETONU_acmaz():
    """Omega kuralı: ayrım saç teli çizgi ve tondan gelir. Yeni bir hex, panonun görsel dilini
    ikiye böler ve WCAG ölçümü olmayan bir renk doğurur.

    D1 (2026-08-07) — LİSTE ROL ADLARIYLA YAZILIR. İddia aynı ("ızgara yeni bir görsel dil
    açmaz, mevcut dili tekrar eder"); değişen, mevcut dilin ADIdır. Jeton mimarisi iki
    katmana ayrıldı: DEĞER katmanı bir hue'nun adını taşır (--amber), ROL katmanı bir işin
    adını (--sev-2 = "insan gerekiyor"). Bileşen kuralları YALNIZ rol katmanını okur, çünkü
    denetim aynı hue'nun beş ayrı işe koşulduğunu ölçtü ve hue adıyla bağlanan bir kural
    ikinci bir anlamı ödünç almayı ÜCRETSİZ kılıyordu."""
    blok = _govde("/* ---- DURUM KART-IZGARASI (v191)", "@media(max-width:1100px)", INDEX)
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", blok), f"ham renk değeri: {blok}"
    # JETON ADI GEÇEN BİR YORUM, KULLANILAN JETON DEĞİLDİR (dosyanın kendi kuralı, bkz. CSS_KOD):
    # bu bloğun yorumları jeton adlarını düzyazıda sayıyor ("--card / --line-2 / --r-card"), ve
    # D1 sonrası hangi KATMANIN okunduğu tam olarak burada ölçülüyor — ölçüm yorumdan beslenirse
    # kural hue'ya geri dönse bile test yeşil kalırdı.
    blok_kod = re.sub(r"/\*.*?\*/", "", blok, flags=re.S)
    for jeton in ("--card", "--line-2", "--r-card", "--mono", "--tx2", "--tx3", "--sev-2", "--sev-1"):
        assert jeton in blok_kod, f"{jeton} jetonu kullanılmıyor — değer başka yerden geliyor olabilir"
    # Ham hex kadar sessiz bir geri düşüş: kuralın hue adına geri bağlanması. Yasağın GENEL
    # hâli test_renk_rolleri_v197::test_bilesen_kurallari_ham_hue_okumaz'dadır; burada ızgaraya
    # özgü mesajıyla tekrarlanır, çünkü bu bloğun sözleşmesi bu dosyada okunuyor.
    assert not re.search(r"var\(\s*--(green|amber|red)\b", blok_kod), \
        "ızgara kuralı hue adına geri bağlanmış — kural hangi ROLÜ taşıdığını söylemiyor"


def test_sayilar_tabular_nums():
    """P4: hizalı sabit ondalık. Bir kartın sayısı komşusuyla dikey hizada okunmalı.

    v192'de bu bildirim kartın KENDİ bloğundan çıktı ve hücre sınıflarına taşındı — çünkü aynı
    sayıyı artık matris, durum kartı ve özet şeridi ORTAK sınıflarla basıyor. Kural hâlâ tek
    yerde; ölçüldüğü yer değişti, gevşemedi."""
    for sinif in (".mono-num{", ".pm-n{"):
        kural = _govde(sinif, "}", CSS_KOD)
        assert "font-variant-numeric:tabular-nums" in kural, f"{sinif} tabular-nums taşımıyor"
    # Ve kart gövdesi gerçekten o sınıflardan geçiyor (`hucreGovde` `pm-yield mono-num` basar).
    assert '<span class="pm-yield mono-num' in _govde("function hucreGovde(", "\n// ÖZET ŞERİDİ")


def test_anomali_rengi_ve_hareket_butcesini_bozmaz():
    """P1/P2: renk YALNIZ anomalide, ve P10: kalıcı bir puls kalıcı bir hareket olurdu.

    v192'de kanal TEKE indi. Eskiden aynı sapma İKİ dille anlatılıyordu: başlıktaki 7px'lik
    `.durum-nokta` ve gövdedeki uyarı satırı. Artık matrisin kuralı burada da geçerli — sapma
    hücrenin MÜREKKEBİNİ renklendirir (`.durum-kart.uyari` / `.durum-kart.kopuk`), adı düğmenin
    `aria-label`ına girer (nokta zaten okuyucuya hiçbir şey söylemiyordu) ve rozet çipi doğar.

    D1 (2026-08-07): iki kural ROL katmanına bağlandı. Bu, anomali kanalının en doğru
    ifadesi — `.uyari` ile `.kopuk` zaten bir HUE değil bir ŞİDDET söylüyordu ("insan
    gerekiyor" / "şimdi müdahale"), ve artık jetonun adı da onu söylüyor: --sev-2 / --sev-1.
    ÖLÇÜLEN DEĞER AYNI (rol bugün ilgili hue'ya alias); değişen, kuralın hangi işi taşıdığını
    beyan etmesi."""
    assert ".durum-nokta" not in CSS_KOD, "anomali noktası CSS'te kalmış — iki işaret dili sürüyor"
    assert "durum-nokta" not in KOD, "anomali noktası JS'te kalmış"
    for kural in (".durum-kart.uyari{color:var(--sev-2)}", ".durum-kart.kopuk{color:var(--sev-1)}"):
        assert kural in INDEX, f"anomali renk kuralı yok: {kural}"
    blok = _govde(".durum-kart.uyari{", "\n.durum-dus{", INDEX)
    assert "animation" not in blok and "blink" not in blok
    g = _govde("function _durumEmirKarti(", "\n// ---- ④ POZİSYONLAR")
    assert 'anomali: "kopuk"' in g and 'anomali: "uyari"' in g
    # Sağlıklı hâlde renk HİÇ verilmez — "yeşil kart" bir alarm bütçesi kalemidir.
    assert 'anomali: "iyi"' not in APPJS and 'anomali: "yesil"' not in APPJS
    # Sapmanın ADI ekrandan da okunur: düğmenin erişilebilir adına girer.
    kart = _govde("function durumKartHTML(", "\n// Döngü tazelik çubuğunun penceresi")
    assert "anomaliNe" in kart and "rowAttrs(kayitK" in kart


def test_izgara_dis_kaynak_cekmez():
    """CSP script-src 'self': ızgara ne yazı tipi ne ikon ne betik indirir (Geist kalır)."""
    blok = _govde("/* ---- DURUM KART-IZGARASI (v191)", "@media(max-width:1100px)", INDEX)
    assert "url(" not in blok and "@import" not in blok
    assert "http://" not in blok and "https://" not in blok


def test_kart_sutun_sayisi_ve_dar_ekran_civili():
    """Sütun sayısı bir SÖZLEŞMEdir (Genel Bakış'ın `.gb-ust`'üyle aynı gerekçe): dört kart tek
    kolona dizilseydi "tek bakış" iddiası sessizce düşerdi. Dar ekranda kaydırma DÜRÜST hâldir."""
    assert ".durum-izgara{display:grid;grid-template-columns:repeat(4,minmax(0,1fr))" in INDEX
    assert "@media(max-width:1100px){.durum-izgara{grid-template-columns:repeat(2,minmax(0,1fr))}}" in INDEX
    assert "@media(max-width:640px){.durum-izgara{grid-template-columns:1fr}}" in INDEX


def test_kart_odak_halkasi_var():
    """Klavye kullanıcısı hangi kartta olduğunu GÖRMELİ. `:focus-visible` olmadan Tab gezinmesi
    görünmez bir imleçle yapılır."""
    assert ".durum-kart:focus-visible{outline:2px solid var(--accent)" in INDEX


# =================================================================================================
# 9) HÜCRE ANATOMİSİ (v192) — PANONUN TEK SAYI DİLİ
# =================================================================================================
# Ölçülen kusur: aynı büyüklük panoda üç ayrı biçimde yazılıyordu ve ÜÇÜNDEN HİÇBİRİ kanıtın
# gücünü taşımıyordu. Bu bölüm anatominin sözleşmesini çivi ler; gevşerse hücre dili ikiye ayrılır
# ve ayrılma sessizdir (iki dil de "çalışır" görünür).

# Bölüm-içi özet şeritlerinin YAŞADIĞI dört bölge. Şerit BİR ÖZETTİR: satır tabloları (plan,
# eleme, ret, ayrışma) yoğun-uzman düzeni olarak AYNEN kalır — hepsi hücreleşseydi "özet" değil
# ikinci bir tablo doğardı ve bu turun kazancı tam tersine dönerdi.
_SERIT_BOLGELERI = {
    "performans · riskCard": ("function riskCard(kelly, tail, slip, veto) {",
                              "\n// çıkış nedenleri"),
    "adaylar":               ("RENDER.adaylar = async () => {", "\nfunction planRowFull(p) {"),
    "kapilar · s2":          ("  const s2Ozet = ozetSerit([", "\n  const s2 = "),
    "mutabakat · sIcra":     ("    const _ozet = ozetSerit([", "\n    return `${bas}${_ozet}"),
    # BEŞİNCİ BÖLGE (v207, 2026-08-07) — Eksen-2 üretecinin "0 üretildi"si. Dört paydasız sayı
    # (`0 üretildi · 0 kaydedildi · 0 bekleyen · 0 otomatik uygulandı`) bir BAŞARISIZLIK gibi
    # okunuyordu; oysa ölçüm KANIT YOKLUĞU diyor (67 skillin 60'ı gerçek katmanda hiç ölçülmemiş).
    # Deftere yazılmasının bedeli aşağıdaki payda denetimidir — `_EKSEN2_PAYDALARI`.
    "ogrenme · eksen2":      ("    const eksen2Blok = (() => {", "\n      const miDetay = "),
    # ALTINCI BÖLGE (v219, 2026-08-08) — FAZ-6 kilitlerinin `olcum` sözlüğü. Beş kilidin ölçüm
    # sözlüğünün bugüne dek HİÇBİR pano okuyucusu yoktu (yalnız `esik` + `neden`, ikisi de bir
    # `title=` ipucunun içinde); `test_faz5_cikis_v212`nin C-YASA6 çivisi tam olarak bunu kayda
    # geçiriyordu. Şerit BEŞ KİLİT İÇİN TEK emisyondur (`.map()` içinde) ve dört hücresi kilide
    # göre değil SORUYA göre sabittir — bedeli aşağıdaki payda denetimidir (`_KILIT_PAYDALARI`,
    # davranış tarafı `tests/test_gorunurluk_v219.py`).
    "kilitler · faz6 olcum": ("  const olcumBloklari = f.adlar.map(ad => {",
                              "\n  return `<div style=\"margin-top:18px"),
}


def _serit_hucre_sayilari() -> list[int]:
    """Her `ozetSerit([...])` çağrısındaki ÜST DÜZEY girdi sayısı.

    Neden ayraç yürüyüşü, neden regex değil: girdiler `ozetHucre(etiket, {…})` çağrılarıdır ve
    içleri virgül doludur — düz bir `split(",")` dört hücreyi otuz sanardı. `//` yorumları
    nötrlenir çünkü bu turun yorumları Türkçe düzyazı ve içlerinde virgül var; dizgiler
    KORUNUR, zira her dizgi virgülü derinlik ≥2'dedir (bir çağrının içindedir)."""
    kaynak = re.sub(r"^(\s*)//[^\n]*$", r"\1", APPJS, flags=re.M)
    kaynak = re.sub(r"([^:])//[^\n]*$", r"\1", kaynak, flags=re.M)
    out, i = [], 0
    while (i := kaynak.find("ozetSerit([", i)) != -1:
        j = kaynak.index("[", i)
        derinlik, bas, parcalar, k = 0, j + 1, [], j
        while k < len(kaynak):
            c = kaynak[k]
            if c in "([{":
                derinlik += 1
            elif c in ")]}":
                derinlik -= 1
                if derinlik == 0:
                    break
            elif c == "," and derinlik == 1:
                parcalar.append(kaynak[bas:k]); bas = k + 1
            k += 1
        son = kaynak[bas:k].strip()
        if son:
            parcalar.append(son)
        out.append(len([p for p in parcalar if p.strip()]))
        i = k
    return out


def test_serit_basina_DORT_hucre_butcesi():
    """Dört, durum bandının dört kartıyla AYNI gerekçeyle dörttür: beşinci hücre şeridi tek
    satırdan taşırır ve "tek bakışta özet" iddiasını sessizce yer. CSS de dört sütuna çivili
    (`repeat(4,…)`), yani beşinci hücre eklendiği gün ızgara ikinci satıra sarkardı ve bunu
    ancak gözle gören fark ederdi — test onu sayabilsin diye bu ölçüm var."""
    sayilar = _serit_hucre_sayilari()
    assert len(sayilar) == len(_SERIT_BOLGELERI), f"beyan edilmemiş şerit: {sayilar}"
    assert sayilar == [4] * len(_SERIT_BOLGELERI), f"şerit başına hücre sayısı: {sayilar}"


def test_hucre_dili_TEK_yerde_tanimli():
    """İkinci bir kopya ilk düzenlemede ayrışır ve ayrışma GÖZLE görülmez: iki dil de çizer."""
    for fn in ("kanitOrani", "azOrnek"):
        assert KOD.count(f"const {fn} = ") == 1, f"{fn} tek tanımlı değil"
    for fn in ("hucreCubuk", "hucreGovde", "ozetHucre", "ozetSerit"):
        assert KOD.count(f"function {fn}(") == 1, f"{fn} tek tanımlı değil"
    # Eski ikinci dil GERÇEKTEN düştü — ne CSS'te ne JS'te bir kalıntısı var.
    for eski in (".durum-say", ".durum-alt", "durum-say", "durum-alt"):
        assert eski not in CSS_KOD, f"CSS'te eski sayı dili kalmış: {eski}"
    assert "durum-say" not in KOD and "durum-alt" not in KOD, "JS eski sayı dilini basmayı sürdürüyor"


def test_hucre_sinifları_MATRISIN_sinifları_ve_tek_kez_tanimli():
    """Yeni bir sınıf ailesi AÇILMADI. `.km-*` bilerek ayrıdır (ayrı semantik: sıralı kapsama
    ölçeği); burada semantik matrisin ta kendisi — değer + kanıt çubuğu + payda + rozet."""
    # TABAN KURAL SÜTUN 0'DA YAZILIR, medya-sorgusu ezmeleri girintilidir (dosyanın kendi
    # düzeni). Sayım tabana bakar: bir sınıfın İKİ taban kuralı olması, kazananın kaynak
    # sırasına bağlı olması demektir ve bu bu depoda ölçülmüş bir kusur (S2R-3 `.mrow` vakası).
    for sinif in (".pm-yield{", ".pm-conf{", ".pm-n{", ".pm-thin{", ".pm-none{", ".pm-sectlabel{"):
        n = len(re.findall(r"^%s" % re.escape(sinif), CSS_KOD, re.M))
        assert n == 1, f"{sinif} CSS'te {n} taban kuralı taşıyor"
    govde = _govde("function hucreGovde(", "\n// ÖZET ŞERİDİ")
    for sinif in ("pm-yield mono-num", "pm-n", "pm-thin", "pm-none"):
        assert sinif in govde, f"hücre gövdesi `{sinif}` basmıyor — dil ayrışmış"
    assert 'class="pm-cell"' in _govde("function ozetHucre(", "\nfunction ozetSerit(")


def test_cubuk_PAYDASIZ_cizilmez():
    """Bir çubuk "ne kadar dolu" der. Neyin paydası olduğu yazmıyorsa okur onu KENDİ uydurduğu
    bir tavana göre okur — ve bu, ölçülmemiş bir doluluğu ölçülmüş göstermenin en sessiz yolu."""
    fn = _govde("function hucreCubuk(", "\n// HÜCRENİN GÖVDESİ")
    assert "|| !payda) return \"\"" in fn, "payda boşken çubuk yine de çiziliyor"
    assert 'data-payda="${esc(payda)}"' in fn, "payda makine-okunur biçimde beyan edilmiyor"
    assert "çubuk paydası:" in fn, "payda insan-okunur biçimde (title) beyan edilmiyor"
    # ÖLÇÜLDÜ-SIFIR ile ÖLÇÜLEMEDİ ayrı: oran 0 çubuğu ÇİZER (boş görünür), null HİÇ çizmez.
    assert "oran == null" in fn, "ölçülemeyen oran ile sıfır oran aynı kovaya düşüyor"


def test_VERI_YOK_dali_uydurma_sifir_basmaz():
    """Matrisin "ekilmemiş parsel"i. Değer yoksa hücre harf-aralıklı gri "VERİ YOK" der; `0`
    basmak "ölçtük, sıfır çıktı" demek olurdu ve o cümle YANLIŞ olurdu."""
    govde = _govde("function hucreGovde(", "\n// ÖZET ŞERİDİ")
    m = re.search(r'if \(o\.deger == null \|\| o\.deger === ""\) return `<span class="pm-none">',
                  govde)
    assert m, "boş hücre dalı yok ya da koşulu gevşemiş"
    # Boş dalda DEĞER hiç basılmaz — `.pm-yield` yalnız dolu dalda doğar.
    bos_dal = govde[m.start():]
    assert "pm-yield" not in bos_dal.split("\n")[0], "boş hücre yine de bir değer basıyor"
    # Ve boş hücrenin görünümü matrisle AYNI kuralı okur.
    assert ".pm-none{" in CSS_KOD and "text-transform:uppercase" in _govde(".pm-none{", "}", CSS_KOD)


def test_dort_kartin_dordu_de_hucre_anatomisinden_gecer():
    """Kart artık kendi sayı dilini yazmaz: değer + (payda beyanlı) çubuk + meta + rozet."""
    beklenen_payda = {
        "dongu":    "tazelik",                    # bugün-mü tazeliği · 24 saatlik pencere
        "kitap":    "gün içi K/Z",                # gün-içi K/Z bandı
        "emir":     "silahlı plan",               # aynaya gönderim oranı
        "pozisyon": "rejim maruziyet tavanı",     # açık riskin zarfa oranı
    }
    for ad, (bas, bit) in _KART_GOVDE.items():
        g = _govde(bas, bit)
        assert re.search(r'durumKartHTML\("%s", k, \{' % ad, g), \
            f"{ad} kartı hücre nesnesiyle çağrılmıyor (eski HTML dizgisi mi kaldı?)"
        assert "deger:" in g and "meta:" in g, f"{ad} kartında hücre anatomisi eksik"
        assert "oran:" in g and "payda:" in g, f"{ad} kartında çubuk ya da paydası yok"
        assert beklenen_payda[ad] in g, \
            f"{ad} kartının çubuk paydası beyan edilmiyor (beklenen: {beklenen_payda[ad]})"


def test_rozet_kosullu_dogar_ve_kelimesi_beyanlidir():
    """Rozet bir UYARIDIR ("bu sayıyı okurken şunu bil"), bir süs değil. Koşulsuz basılan bir
    rozet ilk bakışta bilgi taşır, ikinci bakışta gürültü olur ve üçüncüde görülmez."""
    beklenen = {
        "dongu":    ('rozet: sd.yas_saat == null ? "ÖLÇÜLEMEDİ"', "ÖLÇÜLEMEDİ"),
        "kitap":    ('rozet: kk.ayrisik ? "SERMAYE-RESET"', "SERMAYE-RESET"),
        "emir":     ('rozet: bekleyen ? "BEKLİYOR"', "BEKLİYOR"),
        "pozisyon": ('rozet: isi == null ? "ÖLÇÜLEMEDİ"', "ÖLÇÜLEMEDİ"),
    }
    for ad, (ifade, kelime) in beklenen.items():
        g = _govde(*_KART_GOVDE[ad])
        assert ifade in g, f"{ad} kartının rozeti koşullu doğmuyor: {kelime}"
    # Matrisin kendi rozeti ("az örnek") ve şeritlerinki AYNI çip sınıfını kullanır.
    assert 'rozet: thin ? "az örnek"' in _govde("function plotCell(", "\nasync function renderPlotMap()")


def test_kanit_olcegi_TEK_ve_matris_onu_kullanir():
    """Log ölçek eskiden `plotCell`in içindeydi; özet şeritleri de aynı ölçeği kullanıyor ve
    ikinci bir kopya, iki yüzeyde AYNI n'in farklı doluluk çizmesi demek olurdu."""
    pc = _govde("function plotCell(", "\nasync function renderPlotMap()")
    assert "kanitOrani(c.n)" in pc, "matris ortak kanıt ölçeğini kullanmıyor"
    assert "Math.log10" not in pc, "matris kendi log ölçeğini yeniden yazıyor"
    assert KOD.count("Math.log10(") == 2, "log ölçeği birden fazla yerde hesaplanıyor"
    # "AZ ÖRNEK" eşiği de tek yerde ve bir KAPI DEĞİL: hiçbir karar bu sayıda değişmez.
    assert "const AZ_ORNEK_N = 10;" in KOD and "azOrnek(c.n)" in pc


def test_dort_bolumun_ozet_seridi_var_ve_TIKLANMAZ():
    """İş emrinin ikinci maddesi: iki sayfanın bölüm-içi sayısal özet başlıkları hücreleşir.
    Şerit TIKLANMAZ — bu hücrelerin çekmece kaydı yoktur ve tıklanabilir görünüp hiçbir şey
    açmayan bir yüzey, panonun en ucuz yalanıdır."""
    for ad, (bas, bit) in _SERIT_BOLGELERI.items():
        g = _govde(bas, bit)
        assert "ozetSerit([" in g, f"{ad}: bölüm özeti hücreleşmemiş"
        assert g.count("ozetHucre(") >= 1, f"{ad}: şeritte hücre yok"
    # Şerit hücresi ne düğmedir ne kayıt bağı taşır.
    hucre = _govde("function ozetHucre(", "\nfunction ozetSerit(")
    assert "<button" not in hucre and "rowAttrs" not in hucre and "rec(" not in hucre
    # Şerit yalnız bu dört bölgede kurulur; beşinci bir çağrı yeni bir yüzey demektir ve
    # o yüzeyin de paydalarının denetlenmesi gerekir.
    assert KOD.count("ozetSerit([") == len(_SERIT_BOLGELERI), \
        "beyan edilmemiş bir özet şeridi var — _SERIT_BOLGELERI'ne ekle (paydaları da denetlenmeli)"
    # Her şerit erişilebilir bir adla duyurulur (dört sayı bir GRUPTUR, dört rastgele kutu değil).
    assert KOD.count('role="group" aria-label="${esc(adlandirma)}"') == 1
    for g in (_govde(*v) for v in _SERIT_BOLGELERI.values()):
        assert re.search(r"\], \"[^\"]+\"\)", g), "şerit adlandırılmadan kuruluyor"


# -------------------------------------------------------------------------------------------------
# BEŞİNCİ ŞERİDİN PAYDA DENETİMİ (v207) — defterin VARLIK SEBEBİ
# -------------------------------------------------------------------------------------------------
# `_SERIT_BOLGELERI`ne bir satır eklemek bir kauçuk damga DEĞİLDİR: yukarıdaki testin kendi hükmü
# "o yüzeyin de paydalarının denetlenmesi gerekir" der. Beşinci şerit Eksen-2 üretecinin dört
# sayısını taşıyor ve dördünün paydası AYNI DEĞİL — bu denetim tam olarak o farkı çiviler.
#
# ÖLÇÜLEN AYRIM (v207 raporu): üretimin paydası KATALOG DEĞİLDİR. Canlıda 67 skillin 60'ı gerçek
# katmanda hiç ölçülmemiş, 5'i motor içi; hüküm verilebilen 2. "0/67" üretecin altmış yedi skilde
# başarısız olduğunu söylerdi — oysa altmış beşinde ölçüm YOK, yani hüküm kurulamaz. Payda 2'dir.
_EKSEN2_PAYDALARI = {
    # hücre adı → (oran ifadesi, payda ifadesi). İkisi de KAYNAKTAN çivilenir: payda metnini
    # sunucu kurup istemci geçiriyorsa (hücre 1) o da burada yazılı olmalı, yoksa payda sessizce
    # başka bir sayıya kayabilir ve çubuk aynı görünmeye devam eder.
    "Kanıt tabanı":   ("oran: olculemedi ? null : oz.oran",
                       'payda: olculemedi ? "" : oz.payda'),
    "Üretilen öneri": ("oran: paydaVar && uretilen != null ? Math.min(1, uretilen / oz.olculen) : null",
                       'payda: paydaVar ? `hüküm verilebilen skill (${trn(oz.olculen)})` : ""'),
}
# PAYDASI OLMAYAN İKİ HÜCRE — ve paydasızlıkları BİLEREK. `hucreCubuk` paydasız çubuk çizmez;
# burada bir adım daha ileri gidilir: bu iki hücre `oran` DA vermez, yani uydurma bir tavana
# göre doluluk çizme ihtimali kaynakta kapalıdır.
#   bekleyen öneri     → kuyruğun tavanı YOKTUR (kaç öneri "tam" sayılır? tanımsız).
#   motor-içi aşan     → yükte motor-içi skill sayısı yoktur; `korumali` kovası PROTECTED'tır,
#                        ENGINE_IMPLEMENTED ile aynı küme DEĞİL — payda uydurmak olurdu.
_EKSEN2_PAYDASIZ = ("Bekleyen öneri", "Motor-içi eşiği aşan")


def _hucre_dilimi(bolge: str, ad: str) -> str:
    """`ozetHucre("<ad>", { … })` çağrısının nesne gövdesi (ayraç yürüyüşü — iç virgüller yüzünden
    düz bölme yanlış keser, `_serit_hucre_sayilari` ile aynı gerekçe)."""
    i = bolge.index(f'ozetHucre("{ad}"')
    j = bolge.index("{", i)
    derinlik, k = 0, j
    while k < len(bolge):
        c = bolge[k]
        if c in "([{":
            derinlik += 1
        elif c in ")]}":
            derinlik -= 1
            if derinlik == 0:
                return bolge[j:k + 1]
        k += 1
    raise AssertionError(f"{ad}: hücre gövdesi kapanmıyor")


def test_eksen2_seridinin_DORT_PAYDASI_denetlendi():
    """Beşinci şeridin bedeli. Çubuk taşıyan iki hücrenin paydası ADIYLA yazılı; taşımayan iki
    hücre `oran` da vermiyor (paydasızlık bir unutma değil, bir hüküm)."""
    bolge = _govde(*_SERIT_BOLGELERI["ogrenme · eksen2"])
    adlar = re.findall(r'ozetHucre\("([^"]+)"', bolge)
    assert adlar == ["Kanıt tabanı", "Üretilen öneri", "Bekleyen öneri", "Motor-içi eşiği aşan"], adlar
    for ad, (oran, payda) in _EKSEN2_PAYDALARI.items():
        g = _hucre_dilimi(bolge, ad)
        assert oran in g, f"{ad}: oran ifadesi değişmiş — payda denetimi bayatladı\n{g}"
        assert payda in g, f"{ad}: çubuk paydası beyan edilmiyor (beklenen: {payda})\n{g}"
    for ad in _EKSEN2_PAYDASIZ:
        g = _hucre_dilimi(bolge, ad)
        assert "oran:" not in g and "payda:" not in g, \
            f"{ad}: paydasız olması gereken hücreye çubuk girmiş — tavanı yok, uydurulamaz\n{g}"


def test_uretim_paydasi_KATALOG_DEGIL_hukum_verilebilen():
    """ÇEKİRDEK AYRIM. Üretim çubuğu katalog sayısına (67) bölünseydi, ölçülmemiş 65 skill
    üretecin BAŞARISIZLIĞI gibi sayılırdı. Payda hüküm verilebilen skilldir (canlıda 2)."""
    g = _hucre_dilimi(_govde(*_SERIT_BOLGELERI["ogrenme · eksen2"]), "Üretilen öneri")
    assert "uretilen / oz.olculen" in g, "üretim oranının paydası `olculen` değil"
    assert "oz.toplam_skill" not in g, "üretim hücresi KATALOG sayısına bölüyor — 65 ölçülmemiş "\
                                       "skill başarısızlık sayılır"
    # Payda 0 ise çubuk HİÇ doğmaz: bölünecek taban yokken doluluk uydurulamaz.
    assert "paydaVar" in g
    assert "const paydaVar = !olculemedi && oz.olculen > 0;" in KOD


def test_eksen2_seridi_OLCULEMEDI_dalinda_PAYDA_IDDIA_ETMIYOR():
    """Ölçülemeyen hâlde payda bir İDDİAdır ve iddia edilecek bir şey yoktur: `payda` boş dizgiye,
    `oran` null'a düşer — `hucreCubuk` ikisinde de çubuk çizmez."""
    g = _hucre_dilimi(_govde(*_SERIT_BOLGELERI["ogrenme · eksen2"]), "Kanıt tabanı")
    assert 'payda: olculemedi ? "" : oz.payda' in g
    assert "oran: olculemedi ? null : oz.oran" in g
    assert 'rozet: olculemedi ? "ÖLÇÜLEMEDİ" : ""' in g, "ölçülemeyen hâl rozetsiz kalıyor"


def test_kanit_tabani_paydasini_SUNUCU_kuruyor():
    """Payda metni sunucuda kurulur (`api._eksen2_ozeti`) — pano ikinci bir cümle kurmaz, yoksa
    aynı gerçeğin iki metni doğar ve biri bayatlar (bu deponun tekrar eden kusur sınıfı).
    Sunucu tarafı da sayıyı UYDURMAZ: payda kova toplamından gelir.

    PAYDA METNİ Ç3'TE DÜZELTİLDİ (2026-08-09, EDG-2026-019 turu). Eski metin "katalogda beyan
    edilen skill sayısı (67)" idi ve 67 kayıt TOPLAMIydı — içinde 36 ARŞİV kaydı vardı, çünkü
    `skills.catalog()` kayıt defterinin bildiği `retired` alanını düşürüyordu. Sayı doğru
    sayılmış ama yanlış etiketlenmişti; payda artık AKTİF kümedir ve arşiv AYRI bir sayı olarak
    durur. Bu testin iddiası değişmedi (payda sunucuda kurulur, uydurulmaz) — ölçtüğü metin
    düzeldi ve altına arşivin paydadan DÜŞÜLDÜĞÜNÜ çivileyen ikinci bir hâl eklendi."""
    from meridian import api
    oz = api._eksen2_ozeti({"kovalar": {"gercek_katman_olculmemis": 57, "korumali": 5,
                                        "gercek_katman_olculmemis_cf_dolu": 3,
                                        "esik_araliginda": 1, "ornek_yetersiz_cf_de_yetersiz": 1}})
    assert oz["payda"] == "AKTİF skill sayısı (67) — arşiv (0) hariç, kayıt toplamı 67"
    assert oz["oran"] == round(2 / 67, 4), "çubuk oranı payda ile aynı tabandan gelmiyor"
    # ARŞİV PAYDADAN DÜŞER: aynı kovalar + 36 arşiv kaydı → payda 67 DEĞİL 31 olmalı, yoksa
    # emekli edilmiş bir kayıt "ölçülmemiş aktif skill" diye sayılmaya geri döner.
    oz2 = api._eksen2_ozeti({"kovalar": {"gercek_katman_olculmemis": 22, "korumali": 5,
                                         "gercek_katman_olculmemis_cf_dolu": 2,
                                         "esik_araliginda": 1, "ornek_yetersiz_cf_de_yetersiz": 1,
                                         "arsiv": 36}})
    assert oz2["toplam_skill"] == 31 and oz2["arsiv"] == 36 and oz2["kayit_toplam"] == 67
    assert oz2["oran"] == round(2 / 31, 4)
    # Ölçülemeyen hâlde payda İDDİA EDİLMEZ (None — boş dizgi de değil, 0 hiç değil).
    assert api._eksen2_ozeti({"kovalar": {}})["payda"] is None


def test_ozet_seridi_matrisin_recetesini_tekrar_eder():
    """Kap `.pm-grid` ile AYNI reçete (1px saç teli ızgara, hücre zemini `--bg`). Ayrı bir kap
    dili, ilk düzenlemede iki farklı hücre çerçevesi demekti."""
    blok = _govde(".ozet-serit{", "\n@media(max-width:760px){", CSS_KOD)
    assert "grid-template-columns:repeat(4,minmax(0,1fr))" in blok, "dört hücre bütçesi çivili değil"
    assert "gap:1px" in blok and "background:var(--line)" in blok, "saç teli ızgara reçetesi değil"
    assert ".ozet-serit>*{background:var(--bg)}" in blok
    # Dar ekran dalları: dörtten ikiye, ikiden tek kolona (matrisin kendi kuralıyla aynı gerekçe).
    assert "@media(max-width:900px){.ozet-serit{grid-template-columns:repeat(2,minmax(0,1fr))}}" in INDEX
    assert "@media(max-width:560px){.ozet-serit{grid-template-columns:1fr}}" in INDEX
    # Omega kuralı + CSP: yeni renk jetonu yok, dış kaynak yok, hareket yok.
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", blok), f"ham renk değeri: {blok}"
    assert "url(" not in blok and "@import" not in blok and "http" not in blok
    assert "animation" not in blok and "transition" not in blok


def test_degerin_KENDI_rengi_hucrenin_rengini_YENER():
    """SESSİZ SIRA ÇAKIŞMASI (2026-08-06'da ölçüldü, v191'den beri açıktı). `.pos/.neg/.warn`
    yardımcıları stylesheet'in BAŞINDA (0,1,0); değerin kabı (v191'de `.durum-say`, v192'de
    `.pm-yield`) AŞAĞIDA ve AYNI özgüllükte `color` bildiriyordu — kaynak sırası gereği kap
    kazanıyordu. Yani `SERMAYE_RENK` kartın sayısına yeşil/kırmızı VERİYORDU ve ekranda hiç
    görünmüyordu: para kuralının tek görünür kanalı, hiçbir testin bakmadığı bir sıra
    çakışmasıyla ölüydü. Bu ölçüm o kanalı canlı tutar.

    D1 (2026-08-07) — ÜÇ KURAL İKİ AYRI ROLE AYRILDI ve bu ayrım bu testin iddiasını
    KESKİNLEŞTİRİR. `.pos`/`.neg` bir K/Z İŞARETİdir → YÖN rolü (--yon-arti/--yon-eksi),
    kroması bilerek şiddetin altında: kârlı bir gün bir risk ihlaliyle dikkat için
    yarışamaz. `.warn` ise bir işaret değil bir ALARM'dır → ŞİDDET rolü (--sev-2). Eskiden
    üçü de aynı hue kovasından (green/red/amber) geliyordu ve "para işareti" ile "uyarı"
    ekranda aynı ağırlıkta bağırıyordu. Kanalın canlılığı iddiası aynen duruyor; kanal
    artık İKİ kanal olduğunu da söylüyor."""
    for kural in (".pm-yield.pos{color:var(--yon-arti)}", ".pm-yield.neg{color:var(--yon-eksi)}",
                  ".pm-yield.warn{color:var(--sev-2)}"):
        assert kural in INDEX, f"değer rengi kuralı yok: {kural}"
    # Kural `.pm-yield` taban kuralından SONRA gelmeli (aynı özgüllükte olsaydı sıra yine kaybettirirdi
    # — burada özgüllük 0,2,0 olduğu için yenmesi garanti, ama sıra da doğru olsun).
    assert CSS_KOD.index(".pm-yield.pos{") > CSS_KOD.index(".pm-yield{")
    # Ve kart gerçekten bu kanalı kullanıyor: sermaye kökeninin hükmü değerin sınıfına gidiyor.
    g = _govde(*_KART_GOVDE["kitap"])
    assert "degerSinif: SERMAYE_RENK[kk.renk]" in g, "para rengi değere bağlanmamış"


def test_kartin_SAYISI_ekran_okuyucuya_da_ulasir():
    """`rowAttrs` düğmeye bir `aria-label` koyar ve o etiket düğmenin İÇİNDEKİ metnin YERİNE
    geçer. v191'de etiket yalnız "Son döngü — durum kaydını aç" diyordu: ekran okuyucu kullanan
    operatör bandın dört sayısının HİÇBİRİNİ duymuyordu — bir "özet bandı"nın tam olarak
    duyurmadığı şey. Matris bunu kendi hücresinde zaten çözmüştü; v192 çözümü banda taşır.

    ETİKET GÖVDEDEN TÜRER, ikinci kez YAZILMAZ: elle yazılmış bir cümle meta değiştiği gün
    sessizce bayatlardı ve bayatlığı YALNIZ ekran okuyucu kullanan görebilirdi."""
    assert KOD.count("function hucreSesli(") == 1
    fn = _govde("function hucreSesli(", "\n// ÖZET ŞERİDİ")
    assert "o.deger" in fn and "o.meta" in fn and "o.rozet" in fn, \
        "sesli hâl gövdenin üç katmanını da taşımıyor"
    assert 'replace(/<[^>]*>/g, "")' in fn, "meta'nın HTML'i sesli hâle sızıyor"
    assert "veri yok" in fn, "boş hücre sesli hâlde de boş olduğunu söylemiyor"
    kart = _govde("function durumKartHTML(", "\n// Döngü tazelik çubuğunun penceresi")
    assert "hucreSesli(hucre)" in kart, "kartın erişilebilir adı hâlâ yalnız başlığı söylüyor"


def test_hucre_etiketi_TEK_gorsel_tanim_iki_baglam():
    """`.pm-sectlabel` görünümü eskiden YALNIZ 760px medya sorgusunun içindeydi. Özet şeridi onu
    masaüstünde de gösterdiği için ikinci bir kopya gerekirdi — ve iki kopya ayrışırdı."""
    kural = _govde(".pm-sectlabel{", "}", CSS_KOD)
    assert "display:none" in kural and "text-transform:uppercase" in kural, \
        "etiket görünümü taban kuralda değil"
    assert ".ozet-serit .pm-sectlabel{display:block}" in INDEX, "şeritte etiket görünmüyor"
    assert ".pm-grid .pm-sectlabel{display:block}" in INDEX, "telefonda matris etiketi düştü"

"""v191 — DURUM KART-IZGARASI: "Koşu & Döngü ile Portföy & Emirler çakışıyor" bulgusunun kapanışı.

OPERATÖR BULGUSU (2026-08-06): "Koşu & Döngü ile Portföy ve Emirler çakışıyor, benzer şeyleri
gösteriyorlar; kartlara bölüp tıklayınca detay."

Bu dosyanın ölçtüğü kusur sınıfı TEK ve adı ÇİFT-KAYNAK: aynı gerçek iki yüzeyden anlatılır, ikisi
ayrı kodda yaşar, biri güncellenir diğeri bayatlar — ve operatör hangisinin doğru olduğunu ekrandan
öğrenemez. Dört ölçülmüş biçimi vardı:

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
    assert sorted(re.findall(r'"(\w+)"', m.group(1))) == ["kosu", "portfoy"]


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
    govde = _govde("function durumKartHTML(", "\n// ---- ① SON DÖNGÜ")
    assert '<button class="durum-kart"' in govde
    assert "rowAttrs(kayitK" in govde, "kart kendi bağını icat ediyor — ortak kayıt defteri atlandı"
    assert 'role="button"' not in govde, "düğme yerine role=button — klavye sözleşmesi ikiye ayrıldı"


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
    assert "rc.stream_ok" in g and "akis == null" in g, \
        "akış üçüncü hâli (hiç kanıt yok) KOPUK ile aynı kovaya düşüyor"

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
    assert 'nokta: "uyari"' in g, "bekleyen plan varken kartta anomali noktası yok"


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
    ikiye böler ve WCAG ölçümü olmayan bir renk doğurur."""
    blok = _govde("/* ---- DURUM KART-IZGARASI (v191)", "@media(max-width:1100px)", INDEX)
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", blok), f"ham renk değeri: {blok}"
    for jeton in ("--card", "--line-2", "--r-card", "--mono", "--tx2", "--tx3", "--amber", "--red"):
        assert jeton in blok, f"{jeton} jetonu kullanılmıyor — değer başka yerden geliyor olabilir"


def test_sayilar_tabular_nums():
    """P4: hizalı sabit ondalık. Bir kartın sayısı komşusuyla dikey hizada okunmalı."""
    blok = _govde("/* ---- DURUM KART-IZGARASI (v191)", "@media(max-width:1100px)", INDEX)
    assert blok.count("font-variant-numeric:tabular-nums") >= 2


def test_anomali_noktasi_renk_ve_hareket_butcesini_bozmaz():
    """P1/P2: renk YALNIZ anomalide, ve P10: kalıcı bir puls kalıcı bir hareket olurdu. Nokta iki
    ölçülmüş sapmada doğar (gönderilecekte kalan plan · kopuk akış) ve HİÇ animasyonu yoktur."""
    blok = _govde(".durum-nokta{", "\n.durum-dus{", INDEX)
    assert "animation" not in blok and "blink" not in blok
    g = _govde("function _durumEmirKarti(", "\n// ---- ④ POZİSYONLAR")
    assert 'nokta: "kopuk"' in g and 'nokta: "uyari"' in g
    # Sağlıklı hâlde nokta HİÇ çizilmez — "yeşil nokta" bir alarm bütçesi kalemidir.
    assert 'nokta: "iyi"' not in APPJS and 'nokta: "yesil"' not in APPJS


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

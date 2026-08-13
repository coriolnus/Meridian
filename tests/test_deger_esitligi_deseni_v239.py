"""v239 KALEM 5 — 8. BÜTÜNLÜK DESENİ: DEĞER-EŞİTLİĞİ (`divergence`).

ÖLÇÜLEN BOŞLUK (denetim §5, 2026-08-13): `watchdog.coherence_report` yalnız **mtime** kıyaslıyordu
("türev kaynağından eski mi?"). Yedi dedektörün hiçbiri "iki kaynak AYNI ŞEYİ mi söylüyor?" diye
sormuyordu — yani aynı saniyede yazılmış ZIT DEĞERLİ iki dosya bütün kapılardan YEŞİL geçiyordu.
Denetimin en ağır üç bulgusu (pano rozeti ↔ mutabakat · ortamlar arası `max_drawdown` · hiçbir
şeyden türemeyen anlatı) tam bu yapısal kör noktadan doğdu.

BU DOSYA ÇİVİLER:
  (1) dedektör AYRIŞMAYI yakalar ve temiz hâlde SUSAR (pozitif kontrol — kurt masalı yasağı);
  (2) "yarisi" gibi ilişkiler kıyas uzayına DOĞRU taşınır;
  (3) `beyanli-ayri` ikizleme kayda GİRER ama ihlal SAYILMAZ (sessiz muafiyet yok);
  (4) OKUNAMAYAN kaynak ihlal DEĞİLDİR, adıyla `olculemeyen`e düşer (C22 dersi);
  (5) sunum anlatısı taraması TARİHÎ bayat cümleyi hâlâ yakalar (karşı-test) ama bugünkü
      düzeltilmiş metinde SUSAR ve Türkçe küçültme tuzağına düşmez;
  (6) desen dedektör ailesine, panoya ve mutasyon körlük haritasına BAĞLANMIŞTIR (YASA 6:
      okuyucusuz yazım yok).
"""
from __future__ import annotations

from meridian import watchdog as wd


# ============================== (1)+(2) ÇEKİRDEK: AYRIŞMA / EŞİTLİK ==============================

def _kayit(monkeypatch, kaynaklar, neden="test olgusu"):
    monkeypatch.setattr(wd, "EQUIVALENT_TRUTHS",
                        {"olgu_x": {"neden": neden, "kaynaklar": kaynaklar}})


def test_1a_zit_deger_YAKALANIR(sandbox_state, monkeypatch):
    """ASIL İDDİA: iki kaynak, iki farklı değer → AYRIK. Bayatlık YOKTUR (ikisi de bu an okundu) —
    `coherence` bu hâlde yeşil verirdi."""
    _kayit(monkeypatch, [("a", lambda: 0.16), ("b", lambda: 0.08)])
    r = wd.divergence_report()
    assert len(r["ayrik"]) == 1 and r["ayrik"][0]["olgu"] == "olgu_x", r
    assert r["ayrik"][0]["kaynaklar"]["a"]["deger"] == 0.16
    assert r["ayrik"][0]["kaynaklar"]["b"]["deger"] == 0.08
    assert r["esit"] == 0 and r["total"] == 1


def test_1b_esit_deger_SUSAR(sandbox_state, monkeypatch):
    """POZİTİF KONTROL: dedektörü sabit-kırmızı yapmak testi yeşil bırakmamalı."""
    _kayit(monkeypatch, [("a", lambda: 0.16), ("b", lambda: 0.16), ("c", lambda: 0.16)])
    r = wd.divergence_report()
    assert r["ayrik"] == [] and r["esit"] == 1


def test_2a_yarisi_iliskisi_kiyas_uzayina_tasinir(sandbox_state, monkeypatch):
    """`shadowlaw.DD_VETO_MARGIN` goal'ün YARISIDIR — ham eşitlik aramak yanlış alarm üretirdi."""
    _kayit(monkeypatch, [("goal", lambda: 0.16), ("veto", lambda: 0.08, "yarisi")])
    assert wd.divergence_report()["ayrik"] == []
    _kayit(monkeypatch, [("goal", lambda: 0.16), ("veto", lambda: 0.04, "yarisi")])
    ayrik = wd.divergence_report()["ayrik"]
    assert len(ayrik) == 1, "yarısı-ilişkisi ayrışması kaçtı (ölçüm sırasında canlıda yakalandı)"
    # RAPOR HAM DEĞERİ GÖSTERİR, normalize edileni değil: operatör dosyada NE YAZDIĞINI görmeli.
    assert ayrik[0]["kaynaklar"]["veto"]["deger"] == 0.04


# ============================== (3)+(4) MUAFİYET VE ÖLÇÜLEMEZLİK ==============================

def test_3a_beyanli_ikizleme_kayda_girer_ihlal_SAYILMAZ(sandbox_state, monkeypatch):
    """§7'nin bilinçli ikizlemeleri kayda GİRMELİ (sessiz muafiyet yok) ama kıyasa GİRMEMELİ."""
    _kayit(monkeypatch, [("a", lambda: 4), ("b", lambda: 4), ("ikiz", lambda: 0, "beyanli-ayri")],
           neden="trades KAPANMIŞ işlem defteridir")
    r = wd.divergence_report()
    assert r["ayrik"] == []
    assert len(r["beyanli"]) == 1 and r["beyanli"][0]["kaynak"] == "ikiz"
    assert r["beyanli"][0]["neden"], "muafiyetin gerekçesi kayda girmemiş — gerekçesiz istisna sessizliktir"


def test_4a_okunamayan_kaynak_IHLAL_degildir(sandbox_state, monkeypatch):
    """C22 dersi: "ölçemedim" hükmünü "ihlal" diye anlatmak da bir uydurmadır."""
    def _patla():
        raise FileNotFoundError("bounds.yaml yok")
    _kayit(monkeypatch, [("a", lambda: 1), ("b", lambda: 1), ("c", _patla)])
    r = wd.divergence_report()
    assert r["ayrik"] == [] and r["esit"] == 1
    assert len(r["olculemeyen"]) == 1 and r["olculemeyen"][0]["kaynak"] == "c"
    assert "FileNotFoundError" in r["olculemeyen"][0]["error"]


def test_4b_tek_olculen_kaynak_kiyas_URETMEZ(sandbox_state, monkeypatch):
    """Kıyas için EN AZ İKİ ölçülmüş kaynak gerekir; biriyle "eşit" demek uydurma olurdu."""
    def _patla():
        raise RuntimeError("okunamadı")
    _kayit(monkeypatch, [("a", lambda: 1), ("b", _patla)])
    r = wd.divergence_report()
    assert r["ayrik"] == [] and r["esit"] == 0 and len(r["olculemeyen"]) == 1


# ============================== (5) SUNUM ANLATISI TARAMASI ==============================

ARMED = ("breakout_vcp", "pullback", "exhaustion_hammer", "momentum_burst")

TARIHI_BAYAT = ('tip:"breakout_vcp ve pullback <b>SİLAHLI</b>; momentum_burst ve episodik pivot '
                '<b>UYUYAN</b> (kapı silahlanma kararını verene dek ölçülür). EP\'de kazanç raporu '
                'çapası ZORUNLU."')


def test_5a_tarihi_bayat_cumleyi_HALA_yakaliyor():
    """KARŞI-TEST (v204 kuralı): repo düzeldiğinde kanıt kaybolmamalı. Bu, `workflow-diagram.html`in
    2026-08-13 öncesi hâlidir — momentum_burst 2026-08-12'de silahlanmıştı, sayfa "UYUYAN" diyordu.

    NOT: cümlede "silahlanma" GEÇİYOR ve yine de yakalanıyor — sözcük listesi bilerek KÖK değil TAM
    biçimdir; kök seçilseydi bu cümle kendi kendini susturur ve dedektör körleşirdi."""
    assert wd.uyuyan_iddia_tara(TARIHI_BAYAT, ARMED) == {"momentum_burst"}


def test_5b_turkce_kucultme_tuzagina_dusmez():
    """`"TAM SİLAHLANDI".lower()` → `'tam si̇lahlandi'` (noktalı İ, U+0307 ile açılır). Düz bir
    `in` kontrolü SESSİZCE kaçıyordu ve ilk koşumda YANLIŞ POZİTİF üretti."""
    assert "silahlandi" not in "TAM SİLAHLANDI".lower(), "tuzak artık yok mu? testi gözden geçir"
    metin = ('lb:"Uyuyan kurulum mu?" tip:"momentum_burst pencere kararıyla TAM SİLAHLANDI '
             '(ölçüm kartı)."')
    assert wd.uyuyan_iddia_tara(metin, ARMED) == set()


def test_5c_silahsiz_kurulum_adi_ihlal_uretmez():
    """`episodic_pivot` ARMED_SETUPS'ta DEĞİL — onu uyuyan ilan etmek DOĞRU bir cümledir."""
    metin = 'tip:"Kalan uyuyan ateşlemeler (ör. episodic_pivot) yalnız keşif sondası olur."'
    assert wd.uyuyan_iddia_tara(metin, ARMED) == set()


def test_5d_bugunku_repo_temiz(sandbox_state):
    """Bu turda `workflow.js` ve `workflow-diagram.html` düzeltildi — dedektör susmalı."""
    assert wd._sunum_uyuyan_iddialari() == frozenset()


# ============================== (6) BAĞLANTI: YASA 6 (okuyucusuz yazım yok) ==============================

def test_6a_dedektor_ailesine_ve_rapora_bagli(sandbox_state):
    assert "divergence" in wd._DEDEKTOR_BOS
    rep = wd.integrity_report()
    assert "divergence" in rep and isinstance(rep["divergence"], dict)
    for alan in ("ayrik", "esit", "total", "olculemeyen", "beyanli"):
        assert alan in rep["divergence"], f"iskelet alanı eksik: {alan}"


def test_6b_panoda_bir_satiri_var():
    """Üretilip tüketilmeyen kanıt, bu deponun kovaladığı kusur sınıfının kendisidir."""
    from pathlib import Path
    js = (Path(__file__).resolve().parent.parent / "meridian" / "web" / "app.js").read_text()
    assert "divergence: \"değer-eşitliği\"" in js, "8. desen panoda adlandırılmamış"
    assert 'k === "divergence"' in js, "8. desen için hüküm/metin dalı yok"


def test_6c_pano_basligi_ARTIK_SABIT_SAYI_TASIMIYOR():
    """§3.6: başlık "(7 desen)" derken aynı kartın kapsam satırı 6 render ediyordu. Sabit sayı
    kalksaydı bile ikinci kez bayatlardı — sayı rapordan TÜREMELİ."""
    from pathlib import Path
    js = (Path(__file__).resolve().parent.parent / "meridian" / "web" / "app.js").read_text()
    kod = "\n".join(l for l in js.splitlines() if not l.lstrip().startswith("//"))
    assert "Bütünlük dedektörleri (7 desen)" not in kod, "sabit dedektör sayısı geri gelmiş"
    assert "Bütünlük dedektörleri (${" in kod, "başlık sayıyı rapordan türetmiyor"
    assert "kapsam matrisi deseni" in kod, (
        "kapsam matrisi deseni ile dedektör sayısı hâlâ aynı sözcükle anlatılıyor")


def test_6d_mutasyon_korluk_haritasi_aileyi_TURETIYOR():
    """`mutation.py` yedi adlık SABİT bir tuple taşıyordu — `_DEDEKTOR_BOS`un ikinci, elle bakımlı
    kopyası. 8. dedektör eklendiğinde sessizce geride kalır ve düşen bir dedektör "düşmedi"
    sayılırdı; yani körlük haritası yalan söylerdi."""
    from pathlib import Path
    src = (Path(__file__).resolve().parent.parent / "meridian" / "mutation.py").read_text()
    assert "_DEDEKTORLER = tuple(wd._DEDEKTOR_BOS)" in src, "aile hâlâ elle yazılıyor"
    assert 'red.add(f"divergence:{dv[\'olgu\']}")' in src, "ayrışma jetonu mutasyon kümesine girmiyor"


def test_6e_alarm_kolu_olgu_basina_jeton_uretir():
    from pathlib import Path
    src = (Path(__file__).resolve().parent.parent / "meridian" / "watchdog.py").read_text()
    assert 'tok = f"divergence:{dv[\'olgu\']}"' in src, (
        "tek jeton mandala yapışırsa yeni bir olgu ayrıştığında alarm üretilemez")

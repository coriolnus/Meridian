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

import pytest

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


# ==================================================================================================
# (7) İKİNCİ DALGA — WP6/26 DEĞER-EŞİTLİĞİ KAPISI (2026-08-14)
# --------------------------------------------------------------------------------------------------
# Denetim (`docs/DENETIM-ROADMAP-TUTARLILIK-2026-08-13.md` D3) "26 kapısız çift" dedi; kaynağı
# `docs/DENETIM-SPLIT-SINIFI-2026-08-13.md` §4.1 tablosudur (26 numaralı satır — tablo BAŞLIĞI
# "(18)" der, sayım ile başlık kendi içinde ayrıktır ve bu ölçülüp beyan edildi).
# O 26'nın ÇOĞU 08-13 turunda KAYNAĞINDA onarıldı (README/workflow.js/workflow-diagram.html
# "sayı yazma, adres ver" desenine geçti) — bu dalga, KALANLARDAN kapıya bağlanabilir olanları
# bağlar. Bağlanmayanlar rapor gövdesinde ADIYLA ve NEDENİYLE listelidir.
# ==================================================================================================

YENI_CIFTLER = ("asgari_ornek", "rr_tabani", "alarm_jetonlari",
                "defter_sema_kapsami", "derisk_tabani")


def test_7a_yeni_ciftler_kayda_GEREKCESIYLE_girdi():
    """Gerekçesiz bir çift, kapı değil bir iddiadır: kırmızı yandığında operatör 'bu ikisi neden
    aynı olmalıydı?' sorusuna rapordan cevap alamaz."""
    for olgu in YENI_CIFTLER:
        assert olgu in wd.EQUIVALENT_TRUTHS, f"çift kayda girmemiş: {olgu}"
        kayit = wd.EQUIVALENT_TRUTHS[olgu]
        assert len(str(kayit.get("neden") or "").strip()) >= 20, f"{olgu}: gerekçe yok/zayıf"
        assert len(kayit["kaynaklar"]) >= 2, f"{olgu}: tek kaynak kıyas üretmez"


def test_7b_yeni_ciftler_GERCEKTEN_kiyas_uretiyor_ve_bugun_ESIT(sandbox_state):
    """KAPININ KAPSAMI ÖLÇÜLÜR, VARSAYILMAZ. İki ÖLÇÜLMÜŞ kaynağı olmayan bir çift `divergence_report`
    tarafından sessizce atlanır (`len(degerler) < 2`) — yani kayıtta durur, kapı GÖRÜNÜR, ama hiçbir
    şeyi kıyaslamaz. C10'un "yeşil yanıyor ama ölçtüğü şey yanlış" dersinin bu desendeki hâli budur.

    `derisk_tabani` BİLEREK dışarıda: ikinci kaynağı `beyanli-ayri`dır (kıyasa girmez, kayda girer).
    Onu (8) bölümü ayrıca çiviler."""
    for olgu in ("asgari_ornek", "rr_tabani", "alarm_jetonlari", "defter_sema_kapsami"):
        degerler, hatalar = [], []
        for kaynak in wd.EQUIVALENT_TRUTHS[olgu]["kaynaklar"]:
            try:
                degerler.append((kaynak[0], kaynak[1]()))
            except Exception as e:
                hatalar.append(f"{kaynak[0]}: {type(e).__name__}: {e}")
        assert len(degerler) >= 2, f"{olgu}: kıyas için iki ölçülmüş kaynak yok — {hatalar}"
        tekil = {wd._kiyas_anahtari(v) for _ad, v in degerler}
        assert len(tekil) == 1, f"{olgu} AYRIK: {degerler}"


def test_7c_bos_kume_ILE_olculemedi_AYRI_hallerdir(sandbox_state, monkeypatch):
    """UYDURMA YASAĞININ BU DESENDEKİ HÂLİ. İki yardımcı da bir küme döndürür; kaynak okunamadığında
    BOŞ küme dönselerdi rapor "14 jeton kayıp" / "her zorunlu alan kolonsuz" diye KIRMIZI yanardı —
    yani kapı, kapatmaya çalıştığı sınıfın (ölçülmemiş sayıyı iddia etmek) kendisini üretirdi.
    Doğru hüküm üçüncü hâldir: `olculemeyen` + neden; ne temiz, ne kırmızı."""
    monkeypatch.setattr(wd, "_dosya_metni", lambda p: "// jeton dizisi API'den türetiliyor artık")
    with pytest.raises(LookupError):
        wd._pano_alarm_jetonlari()

    monkeypatch.setattr(wd, "_sabit", lambda m, a: {})
    with pytest.raises(LookupError):
        wd._defter_sema_alanlari()


def test_7d_okunamayan_kaynak_raporda_ADIYLA_ve_NEDENIYLE_durur(sandbox_state, monkeypatch):
    """(4a)'nın gerçek kayıt üzerindeki hâli: düşen kaynak olguyu kıyastan DÜŞÜRÜR, `esit` saymaz,
    `ayrik` saymaz — ve hem olgu hem hata metni raporda görünür."""
    monkeypatch.setattr(wd, "EQUIVALENT_TRUTHS", {
        "olgu_x": {"neden": "iki kaynak aynı eşiği iddia eder",
                   "kaynaklar": [("okunur", lambda: 30),
                                 ("okunmaz", _patlat("bounds.yaml yok"))]}})
    r = wd.divergence_report()
    assert r["esit"] == 0 and r["ayrik"] == []
    assert len(r["olculemeyen"]) == 1
    kayit = r["olculemeyen"][0]
    assert kayit["olgu"] == "olgu_x" and kayit["kaynak"] == "okunmaz"
    assert "bounds.yaml yok" in kayit["error"], "neden kayboldu — 'ölçülemedi' gerekçesizse sessizliktir"


def _patlat(mesaj):
    def _f():
        raise FileNotFoundError(mesaj)
    return _f


def test_7e_kume_donduren_kaynak_dedektoru_TOPYEKUN_dusurmez(sandbox_state, monkeypatch):
    """`defter_sema_kapsami` küme döndürür. Kıyas ham `set`le yapılsaydı `{set(), set()}` TypeError
    fırlatır ve SEKİZİNCİ DESEN BÜTÜNÜYLE düşerdi — tek bir çift, dokuzunun hükmünü birden
    susturur. `_tut` bunu "dedektor_dustu" diye duyururdu ama hüküm yine kaybolurdu."""
    _kayit(monkeypatch, [("a", lambda: {"x", "y"}), ("b", lambda: {"y", "x"})])
    assert wd.divergence_report()["esit"] == 1

    _kayit(monkeypatch, [("a", lambda: {"x", "y"}), ("b", lambda: {"x"})])
    ayrik = wd.divergence_report()["ayrik"]
    assert len(ayrik) == 1, "küme ayrışması kaçtı"
    assert ayrik[0]["kaynaklar"]["b"]["deger"] == ["x"], "küme rapora sıralı listeye çevrilmeli"


def test_7f_tur_kutusu_ACILIR_KAPANIR_ve_dosyayi_BIR_KEZ_ayristirir(sandbox_state, monkeypatch):
    """MALİYET SIKIŞTIRMASI DAVRANIŞ DEĞİŞTİRMEZ. Üç olgu `goal.yaml`ı okuyor; kutu olmasaydı dosya
    üç kez ayrıştırılırdı (3,8 ms × 3). Kutu TURUN fotoğrafıdır: turlar arası taşınmaz — `_yaml_alan`
    ın 'önbellekten okuma yasağı' gerekçesi (canlı↔repo `max_drawdown` ayrışması) korunur.
    Ayrıca yan fayda çivilenir: tek turun kaynakları AYNI anlık görüntüyü görür, yani yazım ortasında
    yakalanmış bir dosya UYDURMA ayrışma üretemez."""
    assert getattr(wd._OKUMA, "kutu", None) is None, "tur başlamadan kutu dolu"

    sayac = {"n": 0}
    gercek = wd._yaml_yukle

    def _sayan(metin):
        sayac["n"] += 1
        return gercek(metin)
    monkeypatch.setattr(wd, "_yaml_yukle", _sayan)

    okuyanlar = [olgu for olgu, k in wd.EQUIVALENT_TRUTHS.items()
                 if any("goal.yaml" in s[0] for s in k["kaynaklar"])]
    assert len(okuyanlar) >= 2, f"goal.yaml'ı okuyan tek olgu var — çivi anlamsız: {okuyanlar}"

    wd.divergence_report()
    goal_ayristirma = sayac["n"]
    assert getattr(wd._OKUMA, "kutu", None) is None, "tur bitti, kutu hâlâ dolu"
    # goal.yaml + bounds.yaml (+ sandbox'ta olmayan strategy.yaml okunamaz): DOSYA sayısı kadar
    assert goal_ayristirma <= 2, (
        f"{len(okuyanlar)} olgu goal.yaml okuyor ama {goal_ayristirma} ayrıştırma yapıldı")

    sayac["n"] = 0
    wd.divergence_report()
    assert sayac["n"] == goal_ayristirma, "ikinci tur diskten okumadı — kutu turlar arası sızıyor"


def test_7g_libyaml_ayni_BELGEYI_veriyor(sandbox_state):
    """`_yaml_yukle` hız için `CSafeLoader`a geçer. Değişen ayrıştırıcının DİLİdir, kabul edilen
    belge sınıfı değil — ama bunu iddia etmek ölçmek değildir, o yüzden ölçülür."""
    import yaml
    from meridian import config
    okunan = 0
    for f in ("goal.yaml", "bounds.yaml", "strategy.yaml"):
        p = config.STATE / f
        if not p.exists():
            continue
        metin = p.read_text()
        assert wd._yaml_yukle(metin) == yaml.safe_load(metin), f"{f}: iki ayrıştırıcı ayrık belge verdi"
        okunan += 1
    assert okunan >= 2, "kıyaslanacak yapılandırma bulunamadı — çivi boşa koştu"


def test_7h_MEVCUT_dortlunun_davranisi_DEGISMEDI():
    """REGRESYON ÇİVİSİ: ikinci dalga, birinci dalganın hükmüne dokunmamalı. Kayıt sırası ve
    ilişkiler aynen durmalı — `yarisi` düşerse `DD_VETO_MARGIN` yanlış alarm üretir, `beyanli-ayri`
    düşerse bilinçli ikizleme İHLAL sayılır."""
    ilk_dort = ["max_drawdown", "strateji_surumu", "acik_pozisyon_defteri", "silahli_kurulumlar"]
    assert list(wd.EQUIVALENT_TRUTHS)[:4] == ilk_dort, "ilk dalganın kayıt sırası bozuldu"

    md = wd.EQUIVALENT_TRUTHS["max_drawdown"]["kaynaklar"]
    assert len(md) == 4 and md[3][0] == "shadowlaw.DD_VETO_MARGIN" and md[3][2] == "yarisi"

    ap = wd.EQUIVALENT_TRUTHS["acik_pozisyon_defteri"]["kaynaklar"]
    assert ap[1][2] == "beyanli-ayri", "bilinçli ikizleme muafiyeti kayboldu"


def test_7i_beyanli_ikizleme_KAYDA_girer_kiyasa_GIRMEZ(sandbox_state):
    """`derisk_tabani`: `broker.DERISK_FLOOR_DD` bağı 2026-08-12'de BİLEREK koparıldı (broker.py:33).
    Kayda giriyor ki muafiyet SESSİZ olmasın; kıyasa girmiyor ki yanlış alarm üretmesin."""
    kaynaklar = wd.EQUIVALENT_TRUTHS["derisk_tabani"]["kaynaklar"]
    assert kaynaklar[1][0] == "broker.DERISK_FLOOR_DD" and kaynaklar[1][2] == "beyanli-ayri"
    beyanli = wd.divergence_report()["beyanli"]
    satir = [b for b in beyanli if b["olgu"] == "derisk_tabani"]
    assert len(satir) == 1 and satir[0]["neden"], "muafiyet gerekçesiz kayda girdi"


def test_7j_MALIYET_olculdu(sandbox_state):
    """ÖLÇÜM KAYDI — SÜRE EŞİĞİ ÇİVİSİ DEĞİL (bilerek: makine-bağımlı bir eşik, kurt masalının
    performans hâlidir). Bu tur ölçülen (yerel main, 2026-08-14, medyan/9-11 koşum):

        4 çift, saf-Python yaml   ->  9,10 ms   (BAŞLANGIÇ)
        9 çift, saf-Python yaml   -> 16,14 ms   (1,77x — bounds.yaml 5,74 + app.js 1,24)
        9 çift, CSafeLoader       ->  7,14 ms   (0,78x — BAŞLANGICIN ALTINDA)

    Yani beş yeni çift sıcak yolu (pano teşhis) şişirmedi; şişme ayrıştırıcı seçimiyle kaynağında
    kapatıldı. Sayı burada durur ki bir sonraki dalga kendi öncesini uydurmak zorunda kalmasın."""
    import time
    sureler = []
    for _ in range(5):
        t0 = time.perf_counter()
        r = wd.divergence_report()
        sureler.append((time.perf_counter() - t0) * 1000)
    medyan = sorted(sureler)[len(sureler) // 2]
    print(f"\ndivergence_report medyan: {medyan:.2f} ms · {r['total']} çift "
          f"({r['esit']} eşit / {len(r['ayrik'])} ayrık / {len(r['olculemeyen'])} ölçülemedi "
          f"/ {len(r['beyanli'])} beyanlı)")
    assert medyan > 0 and r["total"] == len(wd.EQUIVALENT_TRUTHS)


# ==================================================================================================
# (8) ENVANTER KAPANIŞLARI (docs/ENVANTER-DEGER-ESITLIGI-2026-08-22.md) — dedektörün OKUYAMADIĞI
# iki yüzeyin statik çivisi. #16: `goal.get("min_sample", N)` ÇAĞRI-İÇİ yedek literal — dedektör
# modül sabitini okuyabilir (`_sabit`), bir çağrı ifadesinin içindeki yedeği okuyamaz
# (adreslenebilir yüzey yok); kapı ancak kaynak taramasıdır. #10: PRODUCT.md anlatısı
# `equity_curve.json`u "state/ dosyası" sayıyordu; `storage.py` onu altı DB varlığından biri
# ilan eder — anlatı varlık kaydından koparsa belgeye güvenen biri canlıda boş yol arar.
# ==================================================================================================

def test_8a_min_sample_yedek_literalleri_goal_ile_esit():
    """Envanter #16 (LATENT ayrıklık): `score.py:108` ve `shadow_variants.py:532` yedeği 20
    taşıyordu, goal 30 der — goal'da anahtar durdukça ısırmaz, anahtar düşerse iki modül sessizce
    yanlış tabana döner. Kural: yedek, goal'daki değerle EŞİT tutulur. Çivi elle liste tutmaz,
    TÜM `meridian/**/*.py` yedeklerini tarar — bir sonraki modül aynı sınıfı yeniden açamaz."""
    import re as _re
    from pathlib import Path as _Path

    import yaml as _yaml
    repo = _Path(__file__).resolve().parent.parent
    gercek = int(_yaml.safe_load((repo / "state" / "goal.yaml").read_text())["min_sample"])
    desen = _re.compile(r'\.get\(\s*"min_sample"\s*,\s*(\d+)')
    bulunan: dict = {}
    for p in sorted((repo / "meridian").rglob("*.py")):
        for m in desen.finditer(p.read_text()):
            bulunan.setdefault(p.name, []).append(int(m.group(1)))
    assert bulunan, "hiç yedek literal bulunamadı — desen mi, kod mu değişti? çivi boşa koşuyor"
    ayrik = {ad: v for ad, v in bulunan.items() if any(x != gercek for x in v)}
    assert not ayrik, f"min_sample yedeği goal'daki değerden ({gercek}) ayrık: {ayrik}"


def test_8b_PRODUCT_anlatisi_DB_varligini_dosya_diye_satamaz():
    """Envanter #10: PRODUCT.md "gerçek sayıların tek kaynağı state/ dosyaları" derken
    `equity_curve.json`u örnek gösteriyordu — canlıda o bir dosya DEĞİL, `state/meridian.db`
    varlığıdır (kanonik dosya arşivde). Çivi elle liste tutmaz, `storage.ENTITIES`ten TÜRETİR:
    anlatı bir DB varlığının kanonik adını anıyorsa DB gerçeğini de anmak zorundadır."""
    from pathlib import Path as _Path

    from meridian import storage
    repo = _Path(__file__).resolve().parent.parent
    metin = (repo / "PRODUCT.md").read_text()
    anilan = [ad for ad in storage.ENTITIES if ad in metin]
    if anilan:
        assert "meridian.db" in metin, (
            f"PRODUCT.md DB varlıklarını anıyor ({anilan}) ama meridian.db gerçeğini anmıyor — "
            "belgeye güvenen biri canlıda boş yol arar")

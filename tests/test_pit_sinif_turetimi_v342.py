"""v338 — PIT yasasının İKİNCİ çivisi: sınıf atamasının mekanik denetimi.

v337 yasağı mekanikleştirdi ama tek bir elle atamaya dayanıyordu: `PIT_DISI_KAYNAKLAR` her sembole
`karar_etkili` / `bilgi` sınıfı verir ve `pitlaw.karar_etkili()` süzgeci YALNIZ ilkini yasağın
konusu sayar. Devir notunun kendi ifadesiyle (2026-08-30, §5) bu, çivinin **en zayıf halkasıydı**:
bir `bilgi` sembolünün dönüşü yarın bir `verdict`e bağlanırsa kayıt sessizce yanlışlanır ve yasa
o kaynağı bir daha HİÇ görmez. Yanlış sınıf, yasayı kapatan tek satırdır.

BEYAN KALKMADI, ÇÜRÜTMESİ MEKANİKLEŞTİ (`codelaw.declared_claims` disiplini). Kayıt gerekçeyi
taşımaya devam eder; `pitlaw.sinif_turet` aynı soruyu KAYNAKTAN sorar ve ikisi ayrışırsa suite
kırmızıya döner. Türetimi tek otorite yapmak yanlış olurdu: türetim ölçemediği yerde `None` döner
ve "ölçemedim"i "bilgi" saymak tam olarak uydurma olurdu.

ÇELİŞKİ İKİ YÖNLÜ SAYILIR (emsal: `arming.PIT_CAPALI_KURULUMLAR` / çivi v301):
  `beyan_bilgi_gercek_karar` — en tehlikeli yön, PIT'siz veri sessizce karara girer;
  `beyan_karar_gercek_bilgi` — kayıt fazla katı, gereksiz kısıt da bir hatadır.

NUMARA: `v338` bu turda boştu (v337 bir önceki turda bu iş kolunda doğdu). `v325` çakışması
(iki dosya) bu dosyadan önce vardı ve bu tur onu ne büyüttü ne düzeltti.

`sandbox_state` KULLANILMAZ (pitlaw/codelaw diske yazmaz), `exec_module` KULLANILMAZ (v334).

SÜRÜM v338 → 342 önekiyle v341/v342 (2026-08-31): dosya worktree'de v338
olarak yazıldı; entegrasyon anında main'de v338 zaten doluydu (tahta_hijyeni_v337 /
karne_brifingi_v338). vNNN KİMLİKTİR; az-çapalı taraf taşınır — bu, oturumun ÜÇÜNCÜ vNNN
çakışması ve devir brief'i bunu kalem 3 olarak öngörmüştü.
"""
from __future__ import annotations

import pathlib
import textwrap

import pytest

from meridian import pitlaw

KOK = "meridian"

#: Sentetik kayıt — canlı `PIT_DISI_KAYNAKLAR` yerine enjekte edilir. Yalıtım şart: canlı kayıt
#: 19 sembol taşır ve tmp ağacında hiçbiri bulunmaz, yani her sentetik hüküm `None`a düşerdi.
def _kayit(sinif: str, mk: str = "earnings", fn: str = "in_blackout") -> dict:
    return {(mk, fn): {"sinif": sinif, "gerekce": "sentetik kayıt — en az yirmi karakter gerekçe"}}


def _yaz(kok: pathlib.Path, ad: str, govde: str) -> None:
    (kok / ad).write_text(textwrap.dedent(govde), encoding="utf-8")


def _earnings(kok: pathlib.Path) -> None:
    _yaz(kok, "earnings.py", """
        def in_blackout(t, d):
            return False

        def known(t):
            return True
    """)


def _uretici_sozlesmesi(kok: pathlib.Path, uretici: str = "evaluate_pead",
                        ek: str = "", cagri: bool = True, ikinci: str = "") -> None:
    """Sinyal sözleşmesinin sentetik ikizi: `strategy.scan_all` değerlendiricileri bir demetten
    koşturur — canlı `strategy.py`nin birebir biçimi. `ek` ile demete GİRMEYEN ikinci bir
    fonksiyon eklenebilir.

    `cagri=False`: üretici PIT'siz sembolü ÇAĞIRMAZ. Çağrı yerlerini kontrol altında tutması
    gereken testler için — sözleşme sağlanır ama ağaca fazladan bir çağrı yeri girmez. (Ölçüldü:
    sözleşme yardımcısını koşulsuz eklemek iki testin ölçtüğü şeyi bozuyordu.)"""
    govde = (f"    if not earn.in_blackout(t, d):\n        return None\n"
             if cagri else "    if d is None:\n        return None\n")
    ikinci_def = (f"def {ikinci}(t, d):\n    if d is None:\n        return None\n"
                  f"    return 1\n\n" if ikinci else "")
    demet = f"{uretici}, {ikinci}" if ikinci else f"{uretici},"
    (kok / "strategy.py").write_text(
        f"from . import earnings as earn\n\n"
        f"def {uretici}(t, d):\n"
        f"{govde}"
        f"    return {{'setup': 'x'}}\n\n"
        f"{ikinci_def}"
        f"{ek}"
        f"def scan_all(t, d):\n"
        f"    by_setup = {{}}\n"
        f"    for fn in ({demet}):\n"
        f"        sig = fn(t, d)\n"
        f"        if sig is not None:\n"
        f"            by_setup['x'] = sig\n"
        f"    return by_setup\n", encoding="utf-8")


def _guard(kok: pathlib.Path, kararlar: tuple[str, ...] = ("GO", "NO_GO", "REVIEW")) -> None:
    """Kapı sözleşmesinin sentetik ikizi: `classify_gate` her dalda `return "<KARAR>", <gerekçe>`
    yapar — canlı `guard.py`nin birebir biçimi."""
    govde = "def classify_gate(plan, portfolio, regime, goal, params=None):\n"
    for i, k in enumerate(kararlar):
        govde += f"    if plan.get('k{i}'):\n        return \"{k}\", []\n"
    govde += "    return None, []\n"
    (kok / "guard.py").write_text(govde, encoding="utf-8")


# ---------------------------------------------------------------------------
# A0) KARAR ADLARI KAPI SÖZLEŞMESİNDEN TÜRETİLİR — elle liste yok
# ---------------------------------------------------------------------------
def test_vokabuler_classify_gate_RETURN_lerinden_turetilir(tmp_path):
    """Sözleşme fonksiyonun kendi gövdesindedir: her `return`ün İLK pozisyonundaki string sabit
    bir karar hükmüdür. `guard.classify_gate` docstring'i de aynısını söyler
    ("verdict ∈ {GO, REVIEW, NO_GO}") ama hüküm METİNDEN değil KODDAN okunur — docstring bayatlar,
    `return` bayatlamaz."""
    _guard(tmp_path)
    assert pitlaw.karar_vokabuleri(str(tmp_path)) == frozenset({"GO", "NO_GO", "REVIEW"})


def test_vokabuler_GEREKCE_pozisyonunu_karar_SAYMAZ(tmp_path):
    """`return "NO_GO", hard` — ikinci pozisyon gerekçedir. Onu da toplamak, gerekçe listesine
    atanan her adı karar adı yapardı."""
    (tmp_path / "guard.py").write_text(
        'def classify_gate(p):\n    return "NO_GO", "sert kural ihlali"\n', encoding="utf-8")
    assert pitlaw.karar_vokabuleri(str(tmp_path)) == frozenset({"NO_GO"}), \
        "gerekçe pozisyonundaki sabit karar vokabülerine karıştı"


def test_karar_ADI_vokabuler_sabitine_atanan_addir(tmp_path):
    """Karar adı = kapı hükmünün AKTIĞI değişken. `verdict, reasons = "NO_GO", list(...)`
    biçiminde tuple açımı POZİSYONEL çözülür: `verdict` sabit alır, `reasons` bir çağrı alır."""
    _guard(tmp_path)
    _earnings(tmp_path)
    _yaz(tmp_path, "loop.py", """
        from . import earnings

        def daily_cycle(d):
            verdict, reasons = "GO", []
            if earnings.in_blackout("AAPL", d):
                verdict, reasons = "NO_GO", list(reasons) + ["karartma"]
            return verdict, reasons
    """)
    ka = pitlaw.karar_adlari(str(tmp_path))
    assert ka["adlar"] == frozenset({"verdict"}), \
        f"karar adı türetimi yanlış küme verdi (reasons sızmış olabilir): {ka}"
    assert ka["kanit"], "kanıt yok — okuyan hangi satırdan türetildiğini göremez"


def test_SOZLESME_okunamazsa_sinif_hukmu_HIC_verilmez(tmp_path):
    """`guard.py` yoksa ya da `classify_gate` adı değiştiyse doğru cevap "sözleşmeyi bulamadım"dır.
    Boş ad kümesiyle devam etmek, kapı hükmüne bağlı HER sembolü sessizce `bilgi` ilan ederdi —
    yasayı kapatan tam da o satır olurdu."""
    _earnings(tmp_path)          # guard.py BİLEREK yazılmıyor: sözleşmesiz ağaç bu testin konusu
    _yaz(tmp_path, "loop.py", """
        from . import earnings

        def daily_cycle(d):
            verdict = "GO"
            if earnings.in_blackout("AAPL", d):
                verdict = "NO_GO"
            return verdict
    """)
    assert pitlaw.karar_vokabuleri(str(tmp_path)) is None, "guard.py yokken vokabüler uyduruldu"
    t = pitlaw.sinif_turet(str(tmp_path), kaynaklar=_kayit("karar_etkili"))
    kayit = t[("earnings", "in_blackout")]
    assert kayit["turetilen"] is None and kayit["neden"] == "kapi_sozlesmesi_okunamadi", \
        f"sözleşmesiz ağaçta sınıf hükmü verildi: {kayit}"


def test_canli_agacta_karar_adi_TEK_ve_VERDICT(tmp_path=None):
    """CANLI ÖLÇÜM: kapı vokabülerine atanan tek ad `verdict`tir (5 yer: loop.py ×4,
    shadow_variants.py ×1). Elle yazılan eski liste `score`/`score_num`/`size_r`yi de taşıyordu ve
    hiçbiri kanıt üretmiyordu — ölü kayıt, bu deponun yasasına göre çürük."""
    ka = pitlaw.karar_adlari(KOK)
    assert ka["vokabuler"] == frozenset({"GO", "NO_GO", "REVIEW"}), ka["vokabuler"]
    assert ka["adlar"] == frozenset({"verdict"}), (
        f"canlı ağaçta beklenmedik karar adı kümesi: {sorted(ka['adlar'] or [])} — "
        "yeni bir ad kapı hükmü taşımaya başladıysa bu çivi onu ADIYLA gösterir")
    assert len(ka["kanit"]) >= 5, f"kanıt sayısı düştü: {ka['kanit']}"


def test_kayittaki_her_sozlesme_kodda_GERCEKTEN_var(tmp_path):
    """İKİ YÖNLÜ TAMLIĞIN İLK YÖNÜ. Kayıtta duran ama kodda bulunamayan sözleşme çürüktür —
    yasa var olmayan bir sözleşmeye dayanamaz."""
    _guard(tmp_path)
    d = pitlaw.kapi_sozlesme_denetimi(str(tmp_path))
    assert d["curuk"] == [], f"sözleşme kodda var ama çürük sayıldı: {d}"
    # guard.py'yi kaldır: kayıt ölü kalır ve ADIYLA görünür.
    (tmp_path / "guard.py").unlink()
    d2 = pitlaw.kapi_sozlesme_denetimi(str(tmp_path))
    assert d2["curuk"] == ["guard.py::classify_gate"], f"ölü sözleşme yakalanmadı: {d2}"


def test_KAYITSIZ_kapi_yuzeyi_yakalanir(tmp_path):
    """İKİNCİ YÖN — ve bu maddenin var oluş sebebi. Kayıtta OLMAYAN ama karar sabiti DÖNDÜREN bir
    fonksiyon, ikinci bir kapı yüzeyidir: hükümleri sınıf türetimine girmez, yani yasa o yüzeyde
    sessizce kör kalır. İkinci kapı doğduğu gün bu çivi onu ADIYLA gösterir."""
    _guard(tmp_path)
    _yaz(tmp_path, "intraday_cycle.py", """
        def classify_intraday_gate(plan):
            if plan.get("hard"):
                return "NO_GO", ["gun ici sert kural"]
            return "GO", []
    """)
    d = pitlaw.kapi_sozlesme_denetimi(str(tmp_path))
    yerler = [k["yer"] for k in d["kayitsiz"]]
    assert yerler == ["intraday_cycle.py::classify_intraday_gate"], \
        f"kayıtsız kapı yüzeyi görülmedi: {d}"
    assert set(d["kayitsiz"][0]["sabitler"]) == {"GO", "NO_GO"}


def test_KAYITLI_sozlesme_kayitsiz_sayilmaz(tmp_path):
    """Aşırıya kaçmama: kayıttaki sözleşmenin kendisi "kayıtsız kapı" olarak raporlanmamalı,
    yoksa çivi ilk günden kendi kaydını ihbar ederdi."""
    _guard(tmp_path)
    d = pitlaw.kapi_sozlesme_denetimi(str(tmp_path))
    assert d["kayitsiz"] == [], f"kayıtlı sözleşme kayıtsız sayıldı: {d}"


def test_GEREKCE_pozisyonundaki_sabit_kapi_yuzeyi_URETMEZ(tmp_path):
    """`return None, "GO ile ilgisiz bir gerekçe"` — ikinci pozisyondaki sabit karar değildir.
    Tarama ilk pozisyona baktığı için bu fonksiyon kapı yüzeyi sayılmaz."""
    _guard(tmp_path)
    _yaz(tmp_path, "raporlayici.py", """
        def ozet(plan):
            return None, "GO"
    """)
    d = pitlaw.kapi_sozlesme_denetimi(str(tmp_path))
    assert d["kayitsiz"] == [], f"gerekçe pozisyonundaki sabit kapı yüzeyi ürettirdi: {d}"


def test_canli_agacta_kapi_sozlesmesi_kaydi_TAM(canli):
    """CANLI HÜKÜM: kayıt kodla uyuşuyor ve bilinen vokabülerle konuşan başka bir kapı yüzeyi
    bu kapsamda bulunamadı. Ölçüm (2026-08-31): `guard.classify_gate` tek kapı yüzeyi."""
    assert canli["kapi_sozlesmesi_curuk"] == [], \
        f"kayıtta duran ama kodda olmayan sözleşme: {canli['kapi_sozlesmesi_curuk']}"
    assert canli["kapi_sozlesmesi_kayitsiz"] == [], (
        "kayıtta OLMAYAN bir kapı yüzeyi karar sabiti döndürüyor — `KAPI_SOZLESMELERI` "
        f"genişletilmeli: {canli['kapi_sozlesmesi_kayitsiz']}")
    assert canli["kapi_sozlesmeleri"] == ["guard.py::classify_gate"], canli["kapi_sozlesmeleri"]


def test_sinyal_kaydindaki_sozlesme_kodda_GERCEKTEN_var(tmp_path):
    """Kapı tarafının birebir kardeşi, ilk yön: kayıtta duran ama kodda bulunamayan tarayıcı
    çürüktür."""
    _uretici_sozlesmesi(tmp_path, cagri=False)
    assert pitlaw.sinyal_sozlesme_denetimi(str(tmp_path))["curuk"] == []
    (tmp_path / "strategy.py").unlink()
    d = pitlaw.sinyal_sozlesme_denetimi(str(tmp_path))
    assert d["curuk"] == ["strategy.py::scan_all"], f"ölü tarayıcı kaydı yakalanmadı: {d}"


def test_KAYITSIZ_ikinci_TARAYICI_yakalanir(tmp_path):
    """İKİNCİ YÖN — bu maddenin sebebi. Kayıtta olmayan ama değerlendiricileri BİR ARADA koşturan
    bir fonksiyon ikinci bir tarayıcıdır. Bulunmazsa onun koşturduğu değerlendiricilerin erken
    `return`leri karar sayılmaz ve PIT'siz bir kaynak sessizce `bilgi` sınıfına düşer."""
    # İkisi de KAYITLI tarayıcının demetinde, yani BİLİNEN üretici.
    _uretici_sozlesmesi(tmp_path, cagri=False, ikinci="evaluate_ikinci")
    _yaz(tmp_path, "intraday_cycle.py", """
        from .strategy import evaluate_pead, evaluate_ikinci

        def intraday_scan(t, d):
            out = {}
            for fn in (evaluate_pead, evaluate_ikinci):
                out[fn.__name__] = fn(t, d)
            return out
    """)
    d = pitlaw.sinyal_sozlesme_denetimi(str(tmp_path))
    assert [k["yer"] for k in d["kayitsiz"]] == ["intraday_cycle.py::intraday_scan"], \
        f"ikinci tarayıcı görülmedi: {d}"
    assert d["kayitsiz"][0]["ureticiler"] == ["evaluate_ikinci", "evaluate_pead"]


def test_TAMAMEN_YENI_degerlendiricili_tarayici_GORUNMEZ(tmp_path):
    """KAPSAM BEYANININ ÇİVİSİ — sınırı gizlemek yerine ÖLÇÜYORUZ. Tarama BİLİNEN üreticilerle
    yapılır; kendi yeni değerlendiricilerini koşturan bir tarayıcı bu tarayıcıya görünmez
    (kapı tarafındaki "yeni vokabüler" sınırının kardeşi). Sıfır sonuç "başka tarayıcı yok"
    değil, "bilinen değerlendiricileri koşturan başka tarayıcı bulunamadı"dır."""
    _uretici_sozlesmesi(tmp_path, cagri=False)          # bilinen üretici: yalnız evaluate_pead
    _yaz(tmp_path, "intraday_cycle.py", """
        def evaluate_yeni_a(t, d):
            return None

        def evaluate_yeni_b(t, d):
            return None

        def intraday_scan(t, d):
            for fn in (evaluate_yeni_a, evaluate_yeni_b):
                fn(t, d)
    """)
    d = pitlaw.sinyal_sozlesme_denetimi(str(tmp_path))
    assert d["kayitsiz"] == [], (
        "beklenmedik biçimde görüldü — sınır değişmişse kapsam beyanı da güncellenmeli: "
        f"{d}")


def test_TEK_degerlendiriciyi_anan_fonksiyon_TARAYICI_sayilmaz(tmp_path):
    """EŞİK ÇİVİSİ. Tek bir değerlendiriciyi çağırmak sarmalayıcılıktır, tarayıcılık değil;
    eşik 1 olsaydı her sarmalayıcı (ve her test yardımcısı) ikinci tarayıcı sayılırdı."""
    _uretici_sozlesmesi(tmp_path, cagri=False)
    _yaz(tmp_path, "sarmalayici.py", """
        from .strategy import evaluate_pead

        def tek_kosum(t, d):
            return evaluate_pead(t, d)
    """)
    d = pitlaw.sinyal_sozlesme_denetimi(str(tmp_path))
    assert d["kayitsiz"] == [], f"tek değerlendirici anan sarmalayıcı tarayıcı sayıldı: {d}"


def test_YORUMDA_gecen_degerlendirici_adi_TARAYICI_URETMEZ(tmp_path):
    """ÖLÇÜLMÜŞ AYRIM. Depoda `evaluate_pead` gibi adlar onlarca YORUM satırında geçiyor
    (`watchdog`, `indicators`, `component_ic`, `reflect`, `ledgers`, `arming`). Metin taraması
    bunların hepsini tarayıcı sanırdı; AST yalnız gerçek kod referansını (`ast.Name`) görür."""
    _uretici_sozlesmesi(tmp_path, cagri=False, ek=(
        "def evaluate_ikinci(t, d):\n    return 1\n\n"))
    _yaz(tmp_path, "yorumcu.py", '''
        def aciklama(x):
            """Bu fonksiyon evaluate_pead ve evaluate_ikinci hakkında KONUŞUR ama onları
            koşturmaz — strategy.evaluate_pead / strategy.evaluate_ikinci."""
            # evaluate_pead, evaluate_ikinci
            return x
    ''')
    d = pitlaw.sinyal_sozlesme_denetimi(str(tmp_path))
    assert d["kayitsiz"] == [], f"yorumdaki ad tarayıcı ürettirdi: {d}"


def test_ATAMA_hedefi_olan_degerlendirici_adi_TARAYICI_URETMEZ(tmp_path):
    """`_anilan_adlar` yalnız DEĞER olarak anılan adları (Load) sayar. Bir fonksiyon
    değerlendirici adlarına ATAMA yapıyorsa (yerel gölgeleme, sahte/monkeypatch kurulumu) onları
    koşturmuyordur — Store bağlamı tarayıcılık kanıtı değildir.

    BU ÇİVİ MUTASYONLA EKLENDİ: `Load` filtresi kaldırıldığında hiçbir test düşmüyordu, yani
    savunma çivisizdi (ölçüm 2026-08-31, mutasyon T3)."""
    _uretici_sozlesmesi(tmp_path, cagri=False, ikinci="evaluate_ikinci")
    # Adlar YALNIZ atama hedefi; hiçbir yerde okunmuyorlar. (İlk yazımda `return evaluate_pead,
    # evaluate_ikinci` vardı — o satır ikisini de Load bağlamına sokuyordu ve çivi mutasyonsuz
    # hâlde de kırmızı veriyordu: senaryo yanlıştı, mekanizma değil.)
    _yaz(tmp_path, "sahte_kurulum.py", """
        def hazirla(kaynak):
            evaluate_pead = None
            evaluate_ikinci = None
            kaynak["hazir"] = True
    """)
    d = pitlaw.sinyal_sozlesme_denetimi(str(tmp_path))
    yerler = [k["yer"] for k in d["kayitsiz"]]
    assert "sahte_kurulum.py::hazirla" not in yerler, (
        f"atama hedefi olan ad tarayıcı ürettirdi (Load filtresi kaçmış): {d}")


def test_canli_agacta_sinyal_sozlesmesi_kaydi_TAM(canli):
    """CANLI HÜKÜM: kayıt kodla uyuşuyor ve bilinen değerlendiricileri koşturan başka bir tarayıcı
    bu kapsamda bulunamadı. Ölçüm (2026-08-31): `strategy.scan_all` tek tarayıcı — diğer
    modüllerdeki tüm `evaluate_*` eşleşmeleri yorum/docstring."""
    assert canli["sinyal_sozlesmesi_curuk"] == [], \
        f"kayıtta duran ama kodda olmayan tarayıcı: {canli['sinyal_sozlesmesi_curuk']}"
    assert canli["sinyal_sozlesmesi_kayitsiz"] == [], (
        "kayıtta OLMAYAN bir tarayıcı değerlendiricileri koşturuyor — `SINYAL_SOZLESMELERI` "
        f"genişletilmeli: {canli['sinyal_sozlesmesi_kayitsiz']}")
    assert canli["sinyal_sozlesmeleri"] == ["strategy.py::scan_all"], canli["sinyal_sozlesmeleri"]


# ---------------------------------------------------------------------------
# A) POZİTİF KONTROL — türetim KARAR'ı gerçekten görür
# ---------------------------------------------------------------------------
def test_if_testindeki_deger_dalda_VERDICT_atiyorsa_KARAR_turetilir(tmp_path):
    """`loop.daily_cycle`in GERÇEK biçimi: `_bl = earnings.in_blackout(...)` → `if ... and _bl:`
    → `verdict = "NO_GO"`. Sonuç bir ada atanıyor, ad teste giriyor, dalda karar veriliyor."""
    _earnings(tmp_path)
    _guard(tmp_path)
    _uretici_sozlesmesi(tmp_path)
    _yaz(tmp_path, "loop.py", """
        from . import earnings

        def daily_cycle(d):
            verdict = "GO"
            _bl = earnings.in_blackout("AAPL", d)
            if verdict != "NO_GO" and _bl:
                verdict = "NO_GO"
            return verdict
    """)
    t = pitlaw.sinif_turet(str(tmp_path), kaynaklar=_kayit("karar_etkili"))
    kayit = t[("earnings", "in_blackout")]
    assert kayit["turetilen"] == "karar_etkili", f"karar bağı görülmedi: {kayit}"
    assert kayit["kanit"] and kayit["kanit"][0]["eylem"] == "verdict", kayit["kanit"]


def test_DOGRUDAN_if_testinde_erken_return_KARAR_turetilir(tmp_path):
    """`strategy.evaluate_pead`in GERÇEK biçimi: çağrı doğrudan testin içinde, dalda `return None`.
    Sinyal ÜRETMEMEK de bir karardır — kurulum o gün hiç ateşleyemez."""
    _earnings(tmp_path)
    _guard(tmp_path)
    _uretici_sozlesmesi(tmp_path)   # `evaluate_pead` + onu koşturan `scan_all` demeti
    t = pitlaw.sinif_turet(str(tmp_path), kaynaklar=_kayit("karar_etkili"))
    kayit = t[("earnings", "in_blackout")]
    assert kayit["turetilen"] == "karar_etkili", f"erken return karar sayılmadı: {kayit}"
    assert kayit["kanit"][0]["eylem"] == "return"


def test_URETICI_OLMAYAN_fonksiyondaki_erken_return_KARAR_SAYILMAZ(tmp_path):
    """DARALTMANIN KENDİSİ. Aynı erken-`return` biçimi, `scan_all` demetinde OLMAYAN bir
    fonksiyonda karar değildir: `if not veri: return` bir bakım/koruma dönüşüdür, "kurulum
    ateşleyemez" hükmü değil. Daraltmadan önce ikisi ayırt edilemiyordu."""
    _earnings(tmp_path)
    _guard(tmp_path)
    # `_yardimci` demete GİRMEZ; `scan_all` yalnız `evaluate_pead`i koşturur.
    _uretici_sozlesmesi(tmp_path, ek=(
        "def _yardimci(t, d):\n"
        "    if not earn.in_blackout(t, d):\n"
        "        return None\n"
        "    return 1\n\n"))
    t = pitlaw.sinif_turet(str(tmp_path), kaynaklar=_kayit("karar_etkili"))
    kanit = t[("earnings", "in_blackout")]["kanit"]
    kapsamlar = {k["yer"] for k in kanit}
    assert kanit, "üretici içindeki erken return de kayboldu — daraltma fazla kesti"
    # `_yardimci`nin satırı kanıtta OLMAMALI: iki çağrı yeri var, yalnız biri karar.
    assert len(kapsamlar) == 1, (
        f"üretici olmayan fonksiyondaki erken return de karar sayıldı: {kanit}")


def test_sinyal_ureticileri_scan_all_DEMETINDEN_turetilir(tmp_path):
    """Kayıt kodun kendisidir: `scan_all` gövdesinde ADI ANILAN ve aynı modülde TANIMLI
    fonksiyonlar. `by_setup`/`sig` gibi yerel adlar tanımlı-fonksiyon kesişimiyle elenir."""
    _uretici_sozlesmesi(tmp_path, ek="def _yardimci(t, d):\n    return 1\n\n")
    su = pitlaw.sinyal_ureticileri(str(tmp_path))
    assert su == frozenset({"evaluate_pead"}), (
        f"üretici kümesi yanlış türetildi (yerel ad sızmış ya da demet dışı fonksiyon "
        f"girmiş olabilir): {su}")


def test_SINYAL_sozlesmesi_okunamazsa_sinif_hukmu_HIC_verilmez(tmp_path):
    """Karar eyleminin iki biçimi iki ayrı kayıttan gelir; biri okunamazsa türetim EKSİKTİR.
    Hangi sembolün hangi bacağa bağlı olduğu önceden bilinemez, o yüzden eksik türetimle hüküm
    verilmez — `evaluate_pead` yalnız `return` bacağıyla karar sayılıyordu."""
    _earnings(tmp_path)
    _guard(tmp_path)          # kapı sözleşmesi VAR, sinyal sözleşmesi YOK
    t = pitlaw.sinif_turet(str(tmp_path), kaynaklar=_kayit("karar_etkili"))
    kayit = t[("earnings", "in_blackout")]
    assert kayit["turetilen"] is None and kayit["neden"] == "sinyal_sozlesmesi_okunamadi", \
        f"sinyal sözleşmesi yokken sınıf hükmü verildi: {kayit}"


def test_canli_agacta_sinyal_ureticileri_DEGERLENDIRICILER(canli):
    """CANLI ÖLÇÜM: `scan_all`ın koşturduğu değerlendiriciler. `evaluate_pead` ve
    `evaluate_episodic_pivot` bu kümede — `days_since_report`ın karar bağı onlara dayanıyor."""
    su = set(canli["sinyal_ureticileri"] or [])
    assert {"evaluate_pead", "evaluate_episodic_pivot"} <= su, (
        f"kazanç-çapalı değerlendiriciler üretici kümesinde yok: {sorted(su)}")
    assert all(a.startswith("evaluate_") for a in su), \
        f"üretici kümesine değerlendirici olmayan ad sızdı: {sorted(su)}"


def test_IC_ICE_daldaki_karar_eylemi_de_gorulur(tmp_path):
    """`calendar_untrustworthy`nin GERÇEK biçimi: karar eylemi İKİ sıçrama ötede
    (`if _kusur:` → `_dusus = verdict == "GO"` → `if _dusus:` → `verdict = "REVIEW"`).
    Yalnız dalın ilk seviyesine bakan bir tarayıcı bunu `bilgi` sanardı."""
    _earnings(tmp_path)
    _guard(tmp_path)
    _uretici_sozlesmesi(tmp_path)
    _yaz(tmp_path, "loop.py", """
        from . import earnings

        def daily_cycle(d):
            verdict = "GO"
            _kusur = earnings.in_blackout("AAPL", d)
            if _kusur:
                _dusus = verdict == "GO"
                if _dusus:
                    verdict = "REVIEW"
            return verdict
    """)
    t = pitlaw.sinif_turet(str(tmp_path), kaynaklar=_kayit("karar_etkili"))
    assert t[("earnings", "in_blackout")]["turetilen"] == "karar_etkili", \
        f"iç içe daldaki karar eylemi görülmedi: {t[('earnings', 'in_blackout')]}"


def test_yalniz_SOZLUGE_akan_deger_BILGI_turetilir(tmp_path):
    """`earnings.known`in GERÇEK biçimi: sonuç hiçbir `if` TESTİNE girmez; yalnız üçlü ifadeye ve
    bir sözlüğe akar. `_checks.append({...})` bir kayıt yazımıdır, bir karar değil — kodun kendi
    beyanı da bunu söyler ("Not KARAR DEĞİŞTİRMEZ")."""
    _earnings(tmp_path)
    _guard(tmp_path)
    _uretici_sozlesmesi(tmp_path)
    _yaz(tmp_path, "loop.py", """
        from . import earnings

        def daily_cycle(d):
            checks = []
            _ek = earnings.known("AAPL")
            checks.append({"coverage": "known" if _ek else "no_calendar_data",
                           "note": None if _ek else "kazanç takvimi YOK"})
            return checks
    """)
    t = pitlaw.sinif_turet(str(tmp_path), kaynaklar=_kayit("bilgi", fn="known"))
    kayit = t[("earnings", "known")]
    assert kayit["turetilen"] == "bilgi", f"bilgi akışı karar sayıldı: {kayit}"
    assert kayit["kanit"] == []
    assert kayit["yerler"], "çağrı yeri hiç görülmedi — türetim yanlış sebeple 'bilgi' demiş olabilir"


# ---------------------------------------------------------------------------
# B) AŞIRIYA KAÇMAMA — türetim fazlasını ölçmez
# ---------------------------------------------------------------------------
def test_KARAR_MODULU_DISINDAKI_cagri_sinifi_BELIRLEMEZ(tmp_path):
    """Sınıf soyut bir iddia değil, "karar yüzeyinde bir karar eylemine bağlanıyor mu" sorusudur.
    `api.py`deki bir `if ...: return` bir HTTP yanıtı döndürür, bir emri değil — o yüzden kapsam
    yalnız karar modülleridir ve dışarıdaki çağrı hükmü DEĞİŞTİRMEZ."""
    _earnings(tmp_path)
    _guard(tmp_path)
    _uretici_sozlesmesi(tmp_path, cagri=False)  # sözleşme sağlanır, fazladan çağrı yeri girmez
    _yaz(tmp_path, "api.py", """
        from . import earnings

        def api_state(d):
            if earnings.in_blackout("AAPL", d):
                return {"blackout": True}
            return {}
    """)
    t = pitlaw.sinif_turet(str(tmp_path), kaynaklar=_kayit("bilgi"))
    kayit = t[("earnings", "in_blackout")]
    assert kayit["turetilen"] is None, f"kapsam dışı çağrı sınıf belirledi: {kayit}"
    assert kayit["yerler"] == []


def test_cagrisi_OLMAYAN_sembol_None_dondurur_BILGI_DEGIL(tmp_path):
    """ÖLÇÜLEMEDİ ≠ BİLGİ (uydurma yasağı). Boş kanıt listesi "baktım, karar değil" der; doğru
    cevap "bu kapsamda çağrısı yok"tur. İkisini tek değere toplamak, hiç sınanmamış bir beyanı
    doğrulanmış göstermek olurdu."""
    _earnings(tmp_path)
    t = pitlaw.sinif_turet(str(tmp_path), kaynaklar=_kayit("bilgi"))
    assert t[("earnings", "in_blackout")]["turetilen"] is None


def test_AYNI_SATIRDAKI_baska_cagrinin_sonucu_tohum_sayilmaz(tmp_path):
    """Tohum eşleşmesi KİMLİKLE (`is`) yapılır. `x = f(earnings.known(t))` satırında `x`, `known`ın
    değil `f`in sonucudur; `x`i tohum saymak sahte bir karar bağı üretirdi."""
    _earnings(tmp_path)
    _guard(tmp_path)
    _uretici_sozlesmesi(tmp_path)
    _yaz(tmp_path, "loop.py", """
        from . import earnings

        def sarmala(v):
            return v

        def daily_cycle(d):
            verdict = "GO"
            x = sarmala(earnings.known("AAPL"))
            if x:
                verdict = "NO_GO"
            return verdict
    """)
    t = pitlaw.sinif_turet(str(tmp_path), kaynaklar=_kayit("bilgi", fn="known"))
    assert t[("earnings", "known")]["turetilen"] == "bilgi", (
        "sarmalayıcıdan geçen değer doğrudan tohum sayıldı — kimlik eşleşmesi kaçmış: "
        f"{t[('earnings', 'known')]}")


# ---------------------------------------------------------------------------
# C) ÇELİŞKİ HÜKMÜ — iki yön de kırmızıdır
# ---------------------------------------------------------------------------
def test_beyan_BILGI_gercek_KARAR_celiski_uretir(tmp_path):
    """EN TEHLİKELİ YÖN — ve bu çivinin var oluş sebebi. Kayıt "bilgi" derken dönüş bir karar
    eylemine bağlanmışsa, `karar_etkili()` süzgeci o sembolü DIŞARIDA bırakır: PIT'siz veri
    karara girer ve v337'nin tüm hükümleri o kaynak için sessizce kapanır."""
    _earnings(tmp_path)
    _guard(tmp_path)
    _uretici_sozlesmesi(tmp_path)
    _yaz(tmp_path, "loop.py", """
        from . import earnings

        def daily_cycle(d):
            verdict = "GO"
            if earnings.in_blackout("AAPL", d):
                verdict = "NO_GO"
            return verdict
    """)
    c = pitlaw.sinif_celiskileri(str(tmp_path), kaynaklar=_kayit("bilgi"))
    assert len(c) == 1, f"çelişki yakalanmadı: {c}"
    assert c[0]["neden"] == "beyan_bilgi_gercek_karar"
    assert c[0]["beyan"] == "bilgi" and c[0]["turetilen"] == "karar_etkili"
    assert c[0]["kanit"], "çelişki kanıtsız raporlandı — okuyan nereye bakacağını bilemez"


def test_beyan_KARAR_gercek_BILGI_de_celiski_uretir(tmp_path):
    """İKİNCİ YÖN (arming v301 disiplini): kayıt fazla katı. Ölçülebilir bir karar bağı yokken
    sembolü yasağın konusu saymak gereksiz bir kısıttır ve kaydın gerçeği yansıtması iki yönde de
    şarttır — yoksa kayıt bir dilek listesine döner."""
    _earnings(tmp_path)
    _guard(tmp_path)
    _uretici_sozlesmesi(tmp_path, cagri=False)  # sözleşme sağlanır, fazladan çağrı yeri girmez
    _yaz(tmp_path, "loop.py", """
        from . import earnings

        def daily_cycle(d):
            checks = []
            checks.append({"blackout": earnings.in_blackout("AAPL", d)})
            return checks
    """)
    c = pitlaw.sinif_celiskileri(str(tmp_path), kaynaklar=_kayit("karar_etkili"))
    assert [k["neden"] for k in c] == ["beyan_karar_gercek_bilgi"], f"ikinci yön kaçtı: {c}"


def test_celiski_ok_hukmunu_DUSURUR(tmp_path):
    """Yasanın kendi kaydı yanlışsa geri kalan her hüküm vakumdur; `ok` bunu yansıtmalıdır."""
    _earnings(tmp_path)
    _guard(tmp_path)
    _uretici_sozlesmesi(tmp_path)
    _yaz(tmp_path, "loop.py", """
        from . import earnings

        def daily_cycle(d):
            verdict = "GO"
            if earnings.in_blackout("AAPL", d):
                verdict = "NO_GO"
            return verdict
    """)
    r = pitlaw.rapor(str(tmp_path), kaynaklar=_kayit("bilgi"))
    assert r["sinif_celiskileri"], f"enjekte edilen kayıtla çelişki görülmedi: {r}"
    assert r["ok"] is False, "sınıf çelişkisi ok'u düşürmedi — çivi rapor eder ama çivilemez"


def test_SENTETIK_kokte_sinif_hukmu_VERILMEZ_None_doner(tmp_path):
    """ÖLÇÜLMÜŞ TUZAK (bu turda v337'nin iki çivisini kırmızıya düşürdü). Sınıf beyanı CANLI AĞAÇ
    hakkındadır: kayıt, sembolün üretimdeki TÜM çağrı yerlerine bakılarak yazılır. Bir tmp ağacında
    o yerlerin ancak biri bulunur; "beyan karar diyor ama burada karar bağı yok" hükmü bir çelişki
    değil bir KATEGORİ HATASIdır.

    Ve cevap boş liste DEĞİL `None`: boş liste "baktım, uyumlu" der; doğru cevap "bu ağaçta
    sorulamaz"dır (`codelaw.report`un tsx alanlarıyla aynı disiplin)."""
    _earnings(tmp_path)
    _guard(tmp_path)
    _uretici_sozlesmesi(tmp_path)
    _yaz(tmp_path, "loop.py", """
        from . import earnings

        def daily_cycle(d):
            verdict = "GO"
            if earnings.in_blackout("AAPL", d):
                verdict = "NO_GO"
            return verdict
    """)
    r = pitlaw.rapor(str(tmp_path))
    assert r["sinif_celiskileri"] is None, "sentetik kökte sınıf hükmü verildi (yalıtım kırık)"
    assert r["sinif_olculemedi"] is None and r["sinif_dogrulandi"] is None
    assert r["ok"] is True, "ölçülmemiş sınıf hükmü ok'u düşürdü — hüküm kurulamayan ihlal sayıldı"


# ---------------------------------------------------------------------------
# D) CANLI AĞACIN HÜKMÜ
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def canli():
    return pitlaw.rapor(KOK)


def test_canli_agacta_SINIF_CELISKISI_YOK(canli):
    """Kaydın sınıf ataması kaynakla uyuşuyor. Bir `bilgi` sembolü karar yoluna bağlandığı gün
    bu çivi öter — v337'nin sessizce kapanması artık mümkün değil."""
    assert canli["sinif_celiskileri"] == [], (
        "beyan edilen sınıf kaynaktan türetilenle ayrıştı: "
        f"{canli['sinif_celiskileri']}")


def test_UC_karar_sembolu_TURETIMLE_dogrulandi(canli):
    """v337'nin `CANLI_TABAN`ını üreten üç sembolün karar bağı artık ölçülmüş — elle iddia değil."""
    beklenen = {"earnings.in_blackout", "earnings.days_since_report",
                "earnings.calendar_untrustworthy"}
    assert beklenen <= set(canli["sinif_dogrulandi"]), (
        f"karar sembollerinin bağı türetimle doğrulanamadı: "
        f"{sorted(beklenen - set(canli['sinif_dogrulandi']))}")


def test_known_BILGI_oldugu_TURETIMLE_dogrulandi(canli):
    """`earnings.known` karar modülünde ÇAĞRILIYOR ama karar eylemine bağlanmıyor — yani `bilgi`
    hükmü ölçülmüş bir hükümdür, çağrı yokluğundan gelen bir varsayım değil."""
    assert "earnings.known" in canli["sinif_dogrulandi"], \
        "known'ın sınıfı ölçülemedi — çağrı yeri mi kayboldu?"
    assert "earnings.known" not in [c["sembol"] for c in canli["sinif_celiskileri"]]


def test_sinifi_OLCULEMEYENLER_adiyla_sayilir(canli):
    """Sıfır çelişki iddiası, kaçının hiç sınanmadığı bilinmeden okunamaz. Karar modüllerinde
    çağrısı olmayan semboller `sinif_olculemedi` kovasında ADIYLA durur ve `ok`u ETKİLEMEZ."""
    olculemedi = set(canli["sinif_olculemedi"])
    dogrulandi = set(canli["sinif_dogrulandi"])
    assert olculemedi and dogrulandi, "iki kova da dolu olmalı — biri boşsa türetim koşmamış"
    assert not (olculemedi & dogrulandi), "bir sembol hem ölçüldü hem ölçülemedi sayıldı"
    assert len(olculemedi | dogrulandi) == len(pitlaw.PIT_DISI_KAYNAKLAR), \
        "kayıttaki her sembol iki kovadan BİRİNDE olmalı — sessizce düşen var"
    # `insider`/`short_interest` bugün karar yüzeyinde DEĞİL; sınıfları bu kapsamda çürütülemez.
    # Bu bir kusur değil, kapsamın dürüst beyanı: bağlandıkları gün türetim onları görmeye başlar.
    assert {"insider.ozet", "shortinterest.ozet"} <= olculemedi, sorted(olculemedi)


def test_ok_hukmu_TUM_bilesenleri_KAPSAR(canli):
    """`ok` altı hükmün birleşimidir; biri bileşenlerden düşerse çivi rapor eder ama suite yeşil
    kalır — yani hiç çivilenmemiş olur. Kayıt denetiminin iki yönü (`curuk`/`kayitsiz`) de
    buraya dâhildir: bugün ikisi de boş olduğu için formülden düşseler fark edilmezdi, ve tam
    o yüzden burada ADIYLA sayılıyorlar."""
    assert canli["ok"] is (not canli["tarihsel_dogrudan"] and not canli["tarihsel_dolayli_beyansiz"]
                           and not canli["curuk_beyan"] and not canli["sinif_celiskileri"]
                           and len(canli["canli_karar_cagrilari"]) <= pitlaw.CANLI_TABAN
                           and not canli["unscanned"]
                           and not canli["kapi_sozlesmesi_curuk"]
                           and not canli["kapi_sozlesmesi_kayitsiz"]
                           and not canli["sinyal_sozlesmesi_curuk"]
                           and not canli["sinyal_sozlesmesi_kayitsiz"]), \
        f"ok bileşenleriyle tutarsız: {canli}"

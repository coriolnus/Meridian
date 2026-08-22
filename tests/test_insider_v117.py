"""test_insider_v117.py — FORM 4 İÇERİDEN İŞLEM ADAPTÖRÜ (ROADMAP §5.4 Y4, 2026-07-29).

Tasarım sözleşmesi (meridian/adapters/insider.py):
  1. UYDURMA YASAĞI — geçmiş penceresi KAPSANMIYORSA cevap `siniflanamadi`'dır, `firsatci` DEĞİL.
     Bu suite'in EN ÖNEMLİ testi budur: taze bir defterde varsayılan-fırsatçı, sinyali %100 dolu
     gösterir, hiçbir testi kırmaz ve tamamen uydurmadır.
  2. 'İKTİSAP' ≠ 'AÇIK PİYASA ALIMI' — ödül/icra/stopaj/bağış satırları nete GİRMEZ.
  3. ARTIMLI DELTA — ikinci koşu su işaretine yetişince DURUR; kota etkisi ölçülür, tahmin edilmez.
  4. DÜRÜST BOZUNMA (YASA 4) — HTTP hatası/kota bloğu sessiz boş dönüş ÜRETMEZ; sebep adıyla döner.
  5. YAZAR TEKLİĞİ — insider_trades.json / insider_signals.json'ı yalnız bu adaptör yazar.

TESTLERDE CANLI ÇAĞRI YOKTUR: FMP kapısı (`fmp._get`) her testte yamalanır.
"""
from __future__ import annotations

import datetime as dt
import pathlib
import re

import pytest

from meridian.adapters import insider

# GERÇEK YAZIM ÇAĞRISINI çözer, "dosya adı metinde geçiyor" DEĞİL. İlk hâli naifti ("adı geçiyor VE
# dosyada write_json var") ve kendi ayağına sıktı: `codelaw.py` artefaktları DECLARED_SINKS'te
# BEYAN ederken adlarını anıyor ve bir DENETÇİ olarak `write_json` dizgesini desen olarak taşıyor —
# yani hiç yazmadığı hâlde "ikinci yazar" sanıldı. Bir bekçi, ölçtüğü şeyi yanlış ölçüyorsa kanıt
# değil gürültü üretir; burada argüman modül sabitlerine karşı ÇÖZÜLÜR.
_YAZIM_RE = re.compile(r"(?:write_json|write_jsonl|append_jsonl)\(\s*"
                       r"([A-Za-z_][\w.]*|\"[^\"]+\"|'[^']+')")


def yazar_dosyalari(artefakt: str) -> set[str]:
    """`artefakt`a GERÇEKTEN yazan .py dosyalarının adları. `write_json(SABIT, ...)` çağrısındaki
    sabit, o dosyanın modül-düzeyi string sabitlerine karşı çözülür."""
    kok = pathlib.Path(insider.__file__).resolve().parent.parent
    yazanlar: set[str] = set()
    for p in kok.rglob("*.py"):
        if "__pycache__" in str(p):
            continue
        metin = p.read_text(errors="ignore")
        sabitler = dict(re.findall(r"^([A-Z_][A-Z0-9_]*)\s*=\s*[\"']([^\"']+)[\"']", metin, re.M))
        for arg in _YAZIM_RE.findall(metin):
            deger = arg[1:-1] if arg[:1] in "\"'" else sabitler.get(arg.split(".")[-1])
            if deger == artefakt:
                yazanlar.add(p.name)
    return yazanlar


# ------------------------------------------------------------------ yardımcılar
def _bugun() -> dt.date:
    return dt.date.today()


def _gun_once(n: int) -> str:
    return (_bugun() - dt.timedelta(days=n)).isoformat()


def _ham(symbol="AAPL", tarih=None, kisi="DOE JOHN", kod="P-Purchase", adet=1000, fiyat=10.0):
    """FMP stable insider-trading satırının sözleşmeye uygun ham hâli."""
    return {"symbol": symbol, "filingDate": tarih or _gun_once(1),
            "transactionDate": tarih or _gun_once(1), "reportingName": kisi,
            "typeOfOwner": "officer: CFO", "transactionType": kod,
            "securitiesTransacted": adet, "price": fiyat,
            "acquisitionOrDisposition": "A" if str(kod).startswith(("P", "A", "M")) else "D",
            "link": "https://sec.gov/x"}


def _kur_fmp(monkeypatch, sayfalar, blocked=False, available=True):
    """`fmp._get`i sayfa listesiyle yamalar; ÇAĞRI SAYISINI döndüren bir sayaç verir."""
    from meridian.adapters import fmp
    sayac = {"n": 0, "params": []}

    def _get(path, params=None, timeout=20.0):
        sayac["n"] += 1
        sayac["params"].append((path, dict(params or {})))
        i = int((params or {}).get("page", 0))
        if callable(sayfalar):
            return sayfalar(path, params)
        return sayfalar[i] if i < len(sayfalar) else []

    monkeypatch.setattr(fmp, "_get", _get)
    monkeypatch.setattr(fmp, "available", lambda: available)
    monkeypatch.setattr(fmp, "quota_blocked", lambda: blocked)
    return sayac


@pytest.fixture(autouse=True)
def _kucuk_evren(monkeypatch):
    monkeypatch.setattr(insider, "_universe", lambda: ["AAPL", "MSFT", "NVDA"])


@pytest.fixture(autouse=True)
def _reset_health():
    insider._HEALTH.update({"ok": None, "calls": 0, "fails": 0, "last_error": "", "at": None,
                            "last_path": None, "rows": 0})
    yield


# ================================================================== 1) UYDURMA YASAĞI
def test_kapsam_yoksa_siniflanamadi_asla_firsatci_degil():
    """EN KRİTİK TEST. Defter yalnız son 30 günü görüyorsa 3 yıllık kural DEĞERLENDİRİLEMEZ.
    Varsayılan-fırsatçı, taze bir defterdeki HER işlemi sinyal ilan ederdi."""
    islem = _gun_once(5)
    sinif = insider.siniflandir("DOE JOHN", "AAPL", islem, gecmis=[{"islem_tarihi": islem}],
                                kapsam_baslangic=_gun_once(30))
    assert sinif == "siniflanamadi", (
        "kapsam yokken fırsatçı ilan edildi — veri yokluğu sinyale çevrildi (UYDURMA)")


def test_kapsam_varsa_ve_gecmis_ay_bossa_firsatci():
    """Kapsam GERÇEKTEN 3 yılı görüyorsa ve o aylarda işlem YOKSA: fırsatçı. Bu, 1. testin
    aynadaki hâli — ikisi birlikte 'yokluk' ile 'bakamamak' ayrımını kilitler."""
    islem = "2026-07-10"
    sinif = insider.siniflandir("DOE JOHN", "AAPL", islem, gecmis=[{"islem_tarihi": islem}],
                                kapsam_baslangic="2020-01-02")
    assert sinif == "firsatci"


def test_ayni_ayda_uc_yil_ust_uste_islem_rutindir():
    """CMP'nin ta kendisi: takvimsel (vesting/10b5-1) desen sinyal DEĞİLDİR."""
    islem = "2026-07-10"
    gecmis = [{"islem_tarihi": islem}, {"islem_tarihi": "2025-07-14"},
              {"islem_tarihi": "2024-07-09"}, {"islem_tarihi": "2023-07-11"}]
    assert insider.siniflandir("DOE JOHN", "AAPL", islem, gecmis, "2019-01-02") == "rutin"


def test_uc_yildan_biri_eksikse_rutin_degildir():
    """Kural 'HER BİRİNDE' der. İki yıl tutup biri tutmazsa desen kırılmıştır → fırsatçı."""
    islem = "2026-07-10"
    gecmis = [{"islem_tarihi": islem}, {"islem_tarihi": "2025-07-14"},
              {"islem_tarihi": "2023-07-11"}]        # 2024 YOK
    assert insider.siniflandir("DOE JOHN", "AAPL", islem, gecmis, "2019-01-02") == "firsatci"


def test_kisi_bilinmiyorsa_siniflanamadi():
    """'Aynı kişi' kuralı kişi olmadan uygulanamaz — anonim satır fırsatçı sayılmaz."""
    assert insider.siniflandir(None, "AAPL", "2026-07-10", [], "2019-01-02") == "siniflanamadi"


# ================================================================== 2) İKTİSAP ≠ ALIM
@pytest.mark.parametrize("kod,beklenen", [
    ("P-Purchase", "alim"), ("S-Sale", "satim"),
    ("A-Award", "diger"), ("M-Exempt", "diger"), ("F-InKind", "diger"), ("G-Gift", "diger"),
])
def test_form4_kodu_yonu_belirler(kod, beklenen):
    assert insider.yon_coz(kod, "A") == beklenen


def test_taninmayan_kod_bilinmiyordur_alim_degil():
    """Tanınmayan kodu 'alim'e yuvarlamak, sağlayıcı şeması kayınca sinyali sessizce şişirirdi."""
    assert insider.yon_coz("?-Weird", "") == "bilinmiyor"
    assert insider.yon_coz(None, None) == "bilinmiyor"


def test_odul_satirlari_net_alima_girmez(sandbox_state, monkeypatch):
    """Form 4 akışının çoğu ödüldür. Ödül nete girseydi her şirket 'içeriden alım' gösterirdi."""
    tarih = _gun_once(3)
    monkeypatch.setattr(insider, "defter_oku", lambda: {
        **insider.bos_defter(),
        "kapsam_sembol": {"AAPL": "2018-01-02"},
        "islemler": [
            {**_kanon(_ham("AAPL", tarih, "A", "A-Award", 50_000, 100.0))},
            {**_kanon(_ham("AAPL", tarih, "B", "P-Purchase", 1_000, 10.0))},
        ]})
    d = insider.ozet(pencere_gun=90, yaz=False)
    e = d["semboller"]["AAPL"]
    assert e["firsatci_net_alim_adet"] == 1000.0, "ödül satırı nete sızdı"
    assert e["firsatci_net_alim_usd"] == 10_000.0
    assert e["yon_diger_n"] == 1


def _kanon(ham):
    s, _ = insider._kanonik(ham)
    return s


# ================================================================== 3) ARTIMLI DELTA
def test_ikinci_kosu_su_isaretinde_durur_ve_daha_az_cagri_yapar(sandbox_state, monkeypatch):
    """'TEK toplu tarama değil, artımlı delta' sözleşmesi. İkinci koşu aynı sayfayı görüp DURMALI."""
    sayfa0 = [_ham("AAPL", _gun_once(2), f"K{i}") for i in range(3)]
    s1 = _kur_fmp(monkeypatch, [sayfa0, sayfa0, sayfa0])
    r1 = insider.fetch_delta(gun=30, sayfa_tavani=5)
    assert r1["yeni"] == 3 and r1["cagri"] >= 1

    s2 = _kur_fmp(monkeypatch, [sayfa0, sayfa0, sayfa0])
    r2 = insider.fetch_delta(gun=30, sayfa_tavani=5)
    assert r2["yeni"] == 0 and r2["tekrar"] == 3
    assert r2["durma_sebebi"] == "su_isareti"
    assert s2["n"] < s1["n"] or s2["n"] == 1, (
        f"artımlılık yok: ilk tur {s1['n']} çağrı, ikinci tur {s2['n']}")


def test_pencere_disina_cikinca_durur(sandbox_state, monkeypatch):
    eski = _gun_once(400)
    _kur_fmp(monkeypatch, [[_ham("AAPL", _gun_once(1))], [_ham("AAPL", eski)], [_ham("AAPL", eski)]])
    r = insider.fetch_delta(gun=30, sayfa_tavani=10)
    assert r["durma_sebebi"] == "pencere_asildi" and r["cagri"] == 2


def test_gec_dosyalanan_form4_taramayi_kesmez(sandbox_state, monkeypatch):
    """CANLI KOŞUDA BULUNAN KUSUR (2026-07-29). Form 4 GEÇ dosyalanabilir: bugün gelen bir kayıt
    2024'teki bir işlemi bildirebilir. Durma ölçütü İŞLEM tarihi olsaydı, akışın ilk sayfasındaki
    TEK bir geç dosyalama taramayı keser ve geri kalan YENİ dosyalamalar görünmez kalırdı —
    sessizce eksik bir defter, hiçbir testi kırmadan. Pencere DOSYALAMA tarihine bakmalı."""
    gec = _ham("AAPL", _gun_once(1), "GEC")
    gec["transactionDate"] = _gun_once(900)          # 2.5 yıl önceki işlem, DÜN dosyalanmış
    _kur_fmp(monkeypatch, [[gec, _ham("MSFT", _gun_once(1), "A")],
                           [_ham("NVDA", _gun_once(2), "B")], []])
    r = insider.fetch_delta(gun=30, sayfa_tavani=5)
    assert r["durma_sebebi"] != "pencere_asildi", (
        "geç dosyalanan tek bir Form 4 taramayı kesti — yeni dosyalamalar görünmez kaldı")
    assert r["yeni"] == 3 and r["cagri"] == 3


def test_teshis_yalniz_bilinmeyen_ALAN_ADINI_bildirir(sandbox_state, monkeypatch):
    """Teşhisin ölçtüğü şey ŞEMA SÜRÜKLENMESİdir, 'bu satırda boş' DEĞİL. İkisi ayrılmazsa liste
    her koşuda dolu görünür, kurt masalına döner ve gerçek sürüklenme geldiğinde kimse bakmaz.
    (Canlı ilk koşu tam bunu yaptı: `transactionType` bazı satırlarda boş diye 'eşlenmeyen'e düştü.)"""
    bos_alanli = _ham("AAPL", _gun_once(1), "A")
    bos_alanli["transactionType"] = ""               # BİLİNEN alan, bu satırda boş
    surukleme = _ham("MSFT", _gun_once(1), "B")
    surukleme["yeniSaglayiciAlani"] = 1              # GERÇEK sürüklenme
    _kur_fmp(monkeypatch, [[bos_alanli, surukleme], []])
    r = insider.fetch_delta(gun=30, sayfa_tavani=3)
    assert r["eslesmeyen_alanlar"] == ["yeniSaglayiciAlani"]
    assert "transactionType" not in r["eslesmeyen_alanlar"]
    assert "directOrIndirect" not in r["eslesmeyen_alanlar"]   # bilinen/zararsız ekstra


def test_islem_sonrasi_kalan_adet_tasinir(sandbox_state):
    """`securitiesOwned` bağlamdır (nete girmez) ama eşlenip atılırsa ölü bir eşleme kalırdı."""
    h = _ham("AAPL", _gun_once(1))
    h["securitiesOwned"] = 58021
    s, _ = insider._kanonik(h)
    assert s["kalan_adet"] == 58021.0


def test_sayfa_tavani_gorunur_sekilde_yarim_birakir(sandbox_state, monkeypatch):
    """Kota koruması yarım bırakır — ama SESSİZCE değil: `tavana_carpti` bayrağı raporda."""
    sayfa = lambda p, q: [_ham("AAPL", _gun_once(1), f"K{q['page']}-{i}") for i in range(3)]
    s = _kur_fmp(monkeypatch, sayfa)
    r = insider.fetch_delta(gun=30, sayfa_tavani=4)
    assert r["tavana_carpti"] is True and r["durma_sebebi"] == "sayfa_tavani"
    assert s["n"] == 4, "sayfa tavanı çağrı sayısını sınırlamadı — kota koruması çalışmıyor"


def test_ayni_satir_iki_kez_gelirse_cift_sayilmaz(sandbox_state, monkeypatch):
    """Sağlayıcı aynı dosyalamayı iki sayfada verirse net alım sessizce ikiye katlanırdı."""
    h = _ham("AAPL", _gun_once(2), "DOE")
    _kur_fmp(monkeypatch, [[h, dict(h)], []])
    r = insider.fetch_delta(gun=30, sayfa_tavani=3)
    assert r["yeni"] == 1 and r["tekrar"] == 1
    assert len(insider.defter_oku()["islemler"]) == 1


def test_evren_disi_semboller_deftere_girmez(sandbox_state, monkeypatch):
    _kur_fmp(monkeypatch, [[_ham("AAPL"), _ham("ZZZZ"), _ham("QQQQ")], []])
    r = insider.fetch_delta(gun=30, sayfa_tavani=3)
    assert r["evren_disi"] == 2 and r["yeni"] == 1
    assert {s["sembol"] for s in insider.defter_oku()["islemler"]} == {"AAPL"}


# ================================================================== 4) DÜRÜST BOZUNMA (YASA 4)
def test_http_hatasi_sessiz_bos_donmez(sandbox_state, monkeypatch):
    import httpx

    def _patla(path, params=None, timeout=20.0):
        raise httpx.HTTPStatusError("500", request=httpx.Request("GET", "https://x"),
                                    response=httpx.Response(500, request=httpx.Request("GET", "https://x")))
    from meridian.adapters import fmp
    monkeypatch.setattr(fmp, "_get", _patla)
    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(fmp, "quota_blocked", lambda: False)
    r = insider.fetch_delta(gun=30, sayfa_tavani=3)
    assert r["hata"] and "HTTPStatusError" in r["hata"]
    assert r["durma_sebebi"] == "http_hatasi"
    assert insider.health()["fails"] >= 1


def test_basarisiz_cagri_da_maliyet_olarak_sayilir(sandbox_state, monkeypatch):
    """CANLI KOŞUDA BULUNAN KUSUR: 3 başarısız `search` çağrısı `cagri=0` diye raporlanmıştı.
    Başarısız istek de sağlayıcıya GİDER; yalnız başarılıları saymak kota raporunu olduğundan
    UCUZ gösterir — oysa bu raporun tek işi o maliyeti dürüstçe söylemek."""
    from meridian.adapters import fmp
    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(fmp, "quota_blocked", lambda: False)
    monkeypatch.setattr(fmp, "_get", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    r = insider.fetch_delta(gun=30, sayfa_tavani=5)
    assert r["cagri"] == 1, "başarısız çağrı maliyet raporuna girmedi"


def test_402_plan_siniri_250_bos_istek_attirmaz(sandbox_state, monkeypatch):
    """402 KOTA değil PLAN sınırıdır: sonraki sembol de aynı yanıtı verir. Sembol sembol denemek
    250 boş istek atmak olurdu. Dur ve sebebi ADIYLA söyle."""
    import httpx
    from meridian.adapters import fmp

    def _402(path, params=None, timeout=20.0):
        raise httpx.HTTPStatusError(
            "402", request=httpx.Request("GET", "https://x"),
            response=httpx.Response(402, request=httpx.Request("GET", "https://x")))
    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(fmp, "quota_blocked", lambda: False)
    monkeypatch.setattr(fmp, "_get", _402)
    r = insider.gecmis_cek(["AAPL", "MSFT", "NVDA"], sayfa=4, tavan=3)
    assert r["cagri"] == 1, f"402'den sonra istek atmaya devam etti ({r['cagri']} çağrı)"
    assert "402" in (r["hata"] or "")


def test_kota_blokluysa_hic_istek_atilmaz(sandbox_state, monkeypatch):
    """Kota dolmuşken istek atmak ne veri getirir ne kotayı geri verir — yalnız fails'i şişirir."""
    s = _kur_fmp(monkeypatch, [[_ham("AAPL")]], blocked=True)
    r = insider.fetch_delta(gun=30, sayfa_tavani=5)
    assert s["n"] == 0 and "kota" in (r["hata"] or "")


def test_anahtar_yoksa_sebep_adiyla_soylenir(sandbox_state, monkeypatch):
    s = _kur_fmp(monkeypatch, [[_ham("AAPL")]], available=False)
    r = insider.fetch_delta(gun=30, sayfa_tavani=5)
    assert s["n"] == 0 and "FMP_API_KEY" in (r["hata"] or "")


def test_eslesmeyen_saglayici_alanlari_teshis_olarak_kaydedilir(sandbox_state, monkeypatch):
    """Sağlayıcı şeması kayarsa sonuç 'sıfır dolu bir sinyal' değil, ADIYLA görünen bir teşhis olmalı."""
    h = _ham("AAPL")
    h["bizimBilmedigimizAlan"] = 42
    _kur_fmp(monkeypatch, [[h], []])
    insider.fetch_delta(gun=30, sayfa_tavani=3)
    teshis = insider.defter_oku()["alan_teshis"]["eslesmeyen_alanlar"]
    assert "bizimBilmedigimizAlan" in teshis


def test_ayristirilamayan_tarih_bugune_yuvarlanmaz(sandbox_state, monkeypatch):
    """Uydurulmuş bir tarih işlemi yanlış aya, dolayısıyla YANLIŞ SINIFA atardı — satır düşer."""
    h = _ham("AAPL")
    h["transactionDate"] = "yok"
    h["date"] = None
    _kur_fmp(monkeypatch, [[h], []])
    r = insider.fetch_delta(gun=30, sayfa_tavani=3)
    assert r["dusen"] == 1 and r["yeni"] == 0


def test_fiyat_yoksa_tutar_sifir_degil_none(sandbox_state):
    s, _ = insider._kanonik(_ham("AAPL", _gun_once(1), fiyat=None))
    assert s["fiyat"] is None and s["tutar"] is None, "fiyatsız satıra 0.0 tutar uyduruldu"


# ================================================================== 5) ÖZET + KAPSAM GÖRÜNÜRLÜĞÜ
def test_ozet_dosyayi_yazar_ve_kapsami_gorunur_kilar(sandbox_state, monkeypatch):
    from meridian import store
    tarih = _gun_once(4)
    monkeypatch.setattr(insider, "defter_oku", lambda: {
        **insider.bos_defter(), "kapsam_sembol": {"AAPL": _gun_once(20)},
        "islemler": [_kanon(_ham("AAPL", tarih, "DOE", "P-Purchase", 500, 20.0))]})
    d = insider.ozet(pencere_gun=90)
    yazilan = store.read_json(insider.SIGNAL_FILE, None)
    assert yazilan is not None and yazilan["semboller"]["AAPL"]["siniflanamadi_n"] == 1
    assert d["siniflama"]["sayim"]["siniflanamadi"] == 1
    assert d["kapsam"]["siniflama_hazir_mi"] is False, (
        "sığ defter 'hazır' göründü — tüketici bunu sinyal sanardı")
    assert d["semboller"]["AAPL"]["firsatci_net_alim_adet"] == 0.0


def test_ozet_alici_ve_satici_kisi_sayisini_ayri_tutar(sandbox_state, monkeypatch):
    """Tek yöneticinin büyük alımı ile üç yöneticinin ayrı alımı aynı $'ı üretebilir, aynı şeyi söylemez."""
    tarih = _gun_once(4)
    monkeypatch.setattr(insider, "defter_oku", lambda: {
        **insider.bos_defter(), "kapsam_sembol": {"AAPL": "2018-01-02"},
        "islemler": [_kanon(_ham("AAPL", tarih, k, "P-Purchase", 100, 5.0))
                     for k in ("A", "B", "C")]
                    + [_kanon(_ham("AAPL", tarih, "D", "S-Sale", 50, 5.0))]})
    e = insider.ozet(pencere_gun=90, yaz=False)["semboller"]["AAPL"]
    assert e["firsatci_alici_kisi_n"] == 3 and e["firsatci_satici_kisi_n"] == 1
    assert e["firsatci_net_alim_adet"] == 250.0     # 300 alım - 50 satım


def test_ozet_pencere_disini_saymaz(sandbox_state, monkeypatch):
    monkeypatch.setattr(insider, "defter_oku", lambda: {
        **insider.bos_defter(), "kapsam_sembol": {"AAPL": "2018-01-02"},
        "islemler": [_kanon(_ham("AAPL", _gun_once(200), "A", "P-Purchase", 100, 5.0))]})
    assert insider.ozet(pencere_gun=90, yaz=False)["semboller"] == {}


def test_ozet_ag_cagrisi_yapmaz(sandbox_state, monkeypatch):
    """Özet SAF hesaptır. Ağ'a giderse kota muhasebesi ölçülemez hâle gelir."""
    from meridian.adapters import fmp

    def _patla(*a, **k):
        raise AssertionError("ozet() FMP'ye gitti — saf hesap sözleşmesi kırıldı")
    monkeypatch.setattr(fmp, "_get", _patla)
    insider.ozet(pencere_gun=90, yaz=False)


# ================================================================== 6) CLI = YASA 6 TÜKETİCİSİ
def test_cli_argumansiz_yardim_basar_ve_2_doner(capsys):
    """Bu turda tek tüketici CLI'dır; çalışmadığı gün bileşen ölü demektir."""
    assert insider.main([]) == 2


def test_cli_ozet_dosyayi_yazar(sandbox_state, monkeypatch, capsys):
    from meridian import store
    monkeypatch.setattr(insider, "defter_oku", lambda: {
        **insider.bos_defter(), "kapsam_sembol": {"AAPL": "2018-01-02"},
        "islemler": [_kanon(_ham("AAPL", _gun_once(3), "DOE", "P-Purchase", 100, 5.0))]})
    assert insider.main(["--ozet", "--pencere", "90"]) == 0
    assert store.read_json(insider.SIGNAL_FILE) is not None
    assert "siniflama" in capsys.readouterr().out


def test_cli_fetch_hatada_1_doner(sandbox_state, monkeypatch, capsys):
    """Sessiz başarısızlık kabuk seviyesinde de görünmeli — cron/ops bunu çıkış koduyla okur."""
    _kur_fmp(monkeypatch, [[_ham("AAPL")]], blocked=True)
    assert insider.main(["--fetch"]) == 1


def test_cli_durum_ag_cagrisi_yapmaz(sandbox_state, monkeypatch, capsys):
    from meridian.adapters import fmp
    monkeypatch.setattr(fmp, "_get", lambda *a, **k: (_ for _ in ()).throw(
        AssertionError("--durum ağa gitti")))
    monkeypatch.setattr(fmp, "available", lambda: True)
    monkeypatch.setattr(fmp, "quota_blocked", lambda: False)
    assert insider.main(["--durum"]) == 0


# ================================================================== 7) YAZAR TEKLİĞİ
def test_bu_iki_dosyanin_tek_yazari_bu_adaptordur():
    """Canlı worker koşarken bu CLI'ı çalıştırmak ancak yazar TEKSE güvenlidir. Yarın biri
    loop.py'den bu dosyalara yazmaya kalkarsa bu test onu adıyla düşürür."""
    from meridian.adapters import shortinterest
    for dosya in (insider.LEDGER_FILE, insider.SIGNAL_FILE):
        yazanlar = yazar_dosyalari(dosya)
        assert yazanlar <= {"insider.py", "shortinterest.py"}, (
            f"{dosya} için İKİNCİ bir yazar belirdi: "
            f"{sorted(yazanlar - {'insider.py', 'shortinterest.py'})} — atomik yazım "
            f"kayıp-güncellemeyi ÖNLEMEZ, yalnız yarım dosyayı önler")
    assert yazar_dosyalari(insider.LEDGER_FILE) == {"insider.py"}
    assert yazar_dosyalari(shortinterest.SIGNAL_FILE) == {"shortinterest.py"}

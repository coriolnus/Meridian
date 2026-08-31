"""PIT ÇAPASI OLMAYAN KURULUM "kanıt yetersiz" DEĞİLDİR — ÖLÇÜLEMEZDİR · v301

VAKA (2026-08-25, kart EDG-2026-060). Tam aralık karşı-olgusal geri dolumu 1164 seans
koştu (8754 satır) ve `episodic_pivot` için SIFIR satır üretti. Rapor bunu

    {"status": "insufficient_cf", "n": 2, "avg_r": 1.846}

diye yazıyordu — yani "örneklem henüz dolmadı, birikmeye devam ediyor". O cümle YANLIŞ ve
operatörü sonsuz bir beklemeye yolluyor. Ölçülen sebep şu:

  · `evaluate_episodic_pivot` ZORUNLU bir nokta-zaman çapası taşır:
        earn.days_since_report(ticker, last_date, max_days=2)  → False ise kurulum YOK
  · kazanç takvimi NOKTA-ZAMAN ARŞİVİ DEĞİL: 2026-08-25 ölçümünde 29 tarih taşıyordu,
    aralık 2026-07-20 → 2026-09-11
  · karşı-olgusal defter ise 2022-01-03'ten başlar

Yani 1164 seansın ~1141'inde çapa sorusu SORULAMIYOR; kurulum yapı gereği ateşleyemez.
"Kanıt birikmiyor" bir örneklem sorunu değil, bir ARŞİV YOKLUĞUdur ve tekrar tekrar
geri dolum koşturmak onu ASLA çözmez.

BU ÇİVİNİN KORUDUĞU ŞEY: iki cümlenin AYRI kalması.
  · gerçekten seyrek ateşleyen silahsız kurulum → "insufficient_cf" (ölçüm sürüyor)
  · PIT çapası çözülemeyen kurulum          → "olculemez_pit_yok" (ölçüm KOŞAMAZ)
Ve kayıt bir İDDİA olmasın diye: kayıttaki her kurulumun değerlendiricisi GERÇEKTEN
kazanç çapasını çağırmalı (yoksa kayıt kendi kendine yalana dönüşür).
"""
from __future__ import annotations

import inspect

import pytest

from meridian import arming, earnings, strategy

#: BOŞ ARŞİV SÖZLEŞMESİ — `earnings_pit._ufuk_turet`in boş dönüşünün birebir biçimi (uydurma
#: aralık yok: `ilk`/`son` None + `neden` YAZILI). TEK KAYNAK: hem aşağıdaki yalıtım fikstürü
#: hem `_ufuk_kur(arsiv_ilk=None)` bunu kullanır; iki kopya sessizce ayrışırdı.
_BOS_ARSIV = {"ilk": None, "son": None, "n_tarih": 0, "n_sembol": 0, "dusen": 0,
              "neden": "PIT kazanç arşivi BOŞ — ufuk ölçülemez (uydurma aralık yok)"}


@pytest.fixture(autouse=True)
def _arsiv_ufku_yalitimi(monkeypatch):
    """DOSYA-YEREL YALITIM: `arsiv_ufku` varsayılan olarak BOŞ arşive sabitlenir.

    NEDEN GEREKLİ: `earnings_pit.ARSIV_YOLU` `config.ROOT`tan türer, `config.STATE`ten DEĞİL —
    yani `sandbox_state` onu yalıtmaz ve depodaki GERÇEK arşiv (`filed` 2010-01-07→2026-07-31)
    her koşumda okunur. `_kanit_durumu`nun `arsiv_yok` dalı 2026-08-31'den beri arşivi sorduğu
    için, üç ufku da kurmayı UNUTAN gelecekteki bir çivi ortamın arşivine göre dal seçer ve
    "başka bir şeyin yeşili" olur — `_ufuk_kur`un docstring'indeki tuzağın üçüncü baskısı.
    Varsayılanı boş arşive sabitlemek o çiviyi sessiz yeşil yerine GÜRÜLTÜLÜ kırmızı yapar.

    DAVRANIŞSIZ: üretim kodu değişmez ve bu dosyadaki her çivi ya `_ufuk_kur` ile üç ufku da
    AÇIKÇA kuruyor (test-düzeyi `monkeypatch` autouse'un üstüne yazar — `tests/conftest`in
    "testin yaması kazanır" sıra garantisi) ya da arşiv yoluna hiç girmiyor. Kaldırılırsa bugün
    hiçbir çivi kırmızıya dönmez; koruduğu şey YARININ çivisidir."""
    from meridian import earnings_pit
    monkeypatch.setattr(earnings_pit, "arsiv_ufku", lambda: dict(_BOS_ARSIV))


# ---------------------------------------------------------------- takvim ufku

def test_takvim_ufku_ilk_son_ve_sayilari_verir():
    u = earnings.takvim_ufku()
    assert set(u) >= {"ilk", "son", "n_tarih", "n_sembol", "neden"}, (
        f"ufuk sözlüğü eksik alanla döndü: {sorted(u)}")
    if u["n_tarih"]:
        assert u["ilk"] <= u["son"], f"aralık ters: {u['ilk']} → {u['son']}"
        assert u["neden"] is None, "dolu takvimde 'neden' yazılı olmamalı"
    else:
        # UYDURMA YASAĞI: ölçülemeyen None + NEDEN
        assert u["ilk"] is None and u["son"] is None
        assert isinstance(u["neden"], str) and len(u["neden"]) >= 10, (
            "boş takvimde neden YAZILI olmalı — sessiz None yasak")


def test_defter_ufku_okunabiliyor():
    from meridian import counterfactual as cf
    u = cf.defter_ufku()
    assert set(u) >= {"ilk", "son", "n", "neden"}, f"eksik alan: {sorted(u)}"
    if u["n"]:
        assert u["ilk"] <= u["son"]
    else:
        assert u["ilk"] is None and isinstance(u["neden"], str)


# ------------------------------------------------------- iki cümle AYRI kalır

def _ufuk_kur(monkeypatch, takvim_ilk, defter_ilk, arsiv_ilk=None):
    """Ortam bağımsız dal seçimi: ÜÇ ufuk da AÇIKÇA kurulur.

    Bu olmadan test yerelde 'takvim boş' dalından geçip yeşil görünüyordu — korunmak istenen
    dal (takvim defterden SONRA başlıyor) ise hiç koşmuyordu. Ölçüm bağlamı tuzağının
    testteki hâli: yeşil, ama başka bir şeyin yeşili.

    ÜÇÜNCÜ UFUK 2026-08-31'de EKLENDİ (EDG-2026-062): `arsiv_yok` dalı artık PIT kazanç arşivini
    de sorar ve arşiv depoda GERÇEKTEN vardır (`research/edgar_facts/earnings_8k_tarihleri.csv`,
    ölçüldü: `filed` 2010-01-07→2026-07-31). Arşivi kurmayan bir test aynı tuzağa ikinci kez
    düşerdi — bu kez ters yönde: dal ortamdaki arşive göre seçilirdi. `arsiv_ilk=None` = arşiv
    YOK (boş arşivin `ilk`/`son`u None'dur, uydurma aralık yoktur)."""
    from meridian import counterfactual as cf, earnings_pit
    monkeypatch.setattr(earnings, "takvim_ufku", lambda: {
        "ilk": takvim_ilk, "son": "2026-09-11", "n_tarih": 29, "n_sembol": 219, "neden": None})
    monkeypatch.setattr(cf, "defter_ufku", lambda: {
        "ilk": defter_ilk, "son": "2026-08-19", "n": 8754, "neden": None})
    monkeypatch.setattr(earnings_pit, "arsiv_ufku", lambda: (
        {"ilk": arsiv_ilk, "son": "2026-07-31", "n_tarih": 2988, "n_sembol": 251, "dusen": 0,
         "neden": None} if arsiv_ilk else dict(_BOS_ARSIV)))


def test_PIT_capali_kurulum_insufficient_cf_DEMEZ(monkeypatch):
    """ÜÇ UFUK DA KURULUR (2026-08-31): bu çivi eskiden ortamın kendi defterlerine güveniyordu
    ve hangi daldan geçtiği YERELE bağlıydı. Korunan hüküm dala değil SINIFA aittir — çapası
    çözülemeyen kurulum 'örneklem dolmadı' DEMEZ — ama sınıfın ölçüldüğü dal açıkça seçilmezse
    çivi yarın başka bir şeyin yeşili olur."""
    _ufuk_kur(monkeypatch, takvim_ilk="2026-07-20", defter_ilk="2022-01-03", arsiv_ilk=None)
    d = arming._kanit_durumu("episodic_pivot", {"n": 2, "avg_r": 1.846})
    assert d["status"] != "insufficient_cf", (
        "PIT çapası çözülemeyen kurulum 'örneklem dolmadı' diye raporlanıyor — "
        f"tam da düzeltilen kusur: {d}")
    assert d["status"] == "olculemez_pit_yok", f"beklenmeyen durum: {d}"
    assert d.get("capa"), "hangi çapanın eksik olduğu YAZILI olmalı"
    # kanıt raporun İÇİNDE olmalı — okuyucu ikinci bir yere bakmak zorunda kalmasın
    assert "takvim" in d and "defter" in d, f"kanıt bloğu yok: {sorted(d)}"


def test_takvim_defterden_SONRA_baslarsa_olculemez(monkeypatch):
    _ufuk_kur(monkeypatch, takvim_ilk="2026-07-20", defter_ilk="2022-01-03", arsiv_ilk=None)
    d = arming._kanit_durumu("episodic_pivot", {"n": 2, "avg_r": 1.846})
    assert d["status"] == "olculemez_pit_yok", f"kör dönem görülmedi: {d}"
    assert "2022-01-03" in d["neden"] and "2026-07-20" in d["neden"], (
        f"neden cümlesi iki ufku da taşımıyor: {d['neden']}")


# ------------------------------------------------- arşiv farkındalığı (EDG-2026-062)

def test_ARSIV_defteri_kapsiyorsa_arsiv_yok_DEMEZ(monkeypatch):
    """TAŞIMANIN İKİNCİ YARISI. `arsiv_yok` cümlesi 2026-08-25'te DOĞRUYDU: çare bir PIT
    arşiviydi ve arşiv yoktu. Arşiv geldi (EDGAR 8-K defteri, `earnings_pit`) ve tarihsel yol ona
    SEVK EDİLDİ; artık aynı cümleyi yazmak, yapılmış işi yapılmamış göstermek ve operatörü
    ikinci kez arşiv kurmaya yollamak olurdu. Mazeret kalıcılaşmasın (`takvim_defteri_TAM_
    kapsiyorsa` çivisinin birebir kardeşi, bu kez ARŞİV ekseninde)."""
    _ufuk_kur(monkeypatch, takvim_ilk="2026-07-20", defter_ilk="2022-01-03",
              arsiv_ilk="2010-01-07")
    d = arming._kanit_durumu("episodic_pivot", {"n": 2, "avg_r": 1.846})
    assert d["status"] == "insufficient_cf", (
        f"arşiv defterin başlangıcını kapsıyor ama hâlâ 'birikemez' deniyor: {d}")
    assert d.get("alt_sebep") is None, f"kapsayan arşivde alt sebep yazılmış: {d}"


def test_ARSIV_kapsamiyorsa_dal_DEGISMEZ(monkeypatch):
    """Aşırıya kaçmama: arşiv VAR ama defterin başlangıcından SONRA başlıyorsa kör dönem
    gerçektir ve hüküm 'birikemez' kalır. Kapsama sorusu bir VARLIK sorusu değildir."""
    _ufuk_kur(monkeypatch, takvim_ilk="2026-07-20", defter_ilk="2022-01-03",
              arsiv_ilk="2024-06-01")
    d = arming._kanit_durumu("episodic_pivot", {"n": 2, "avg_r": 1.846})
    assert d["status"] == "olculemez_pit_yok", f"kör dönem kayboldu: {d}"
    assert d["alt_sebep"] == "arsiv_yok", f"beklenmeyen alt sebep: {d}"
    assert "2024-06-01" in d["neden"], (
        f"cümle ölçülen arşiv ufkunu taşımıyor — okuyucu neyin kapsamadığını göremez: {d['neden']}")


def test_KAPSAYAN_arsiv_cumlesi_cf_KUYRUGU_gercegini_soyler(monkeypatch):
    """BEDEL YASASI. "Kanıt birikiyor, bekle" cümlesi bugün TEK BAŞINA yanıltıcıdır: cf'nin
    ÜRETTİĞİ tarama satırlarında çapa hiç sorulmaz (`_plans_for_session` kuyruğu
    `reset_index(drop=True)` ile kurulur, `date` sütunu düşer — ölçüldü, çivi v345). Arşiv
    kapsıyor diye 'birikiyor' demek, operatörü hiç dolmayacak bir beklemeye yollardı; cümle iki
    gerçeği BİRLİKTE söyler."""
    _ufuk_kur(monkeypatch, takvim_ilk="2026-07-20", defter_ilk="2022-01-03",
              arsiv_ilk="2010-01-07")
    d = arming._kanit_durumu("episodic_pivot", {"n": 2, "avg_r": 1.846})
    neden = d.get("neden") or ""
    assert "earnings_pit" in neden, f"cümle arşivi ADIYLA anmıyor: {neden}"
    assert "2010-01-07" in neden, f"cümle ölçülen arşiv ufkunu taşımıyor: {neden}"
    assert "date" in neden and "cf" in neden.lower(), (
        f"cümle cf tarama kuyruğunun `date` sütunu gerçeğini söylemiyor: {neden}")
    assert d.get("arsiv", {}).get("ilk") == "2010-01-07", \
        f"kanıt bloğu (arşiv ufku) raporun İÇİNDE değil: {sorted(d)}"


def test_bos_takvim_ile_arsivsiz_takvim_AYRI_alt_sebep(monkeypatch):
    """İki alt sebep, İKİ AYRI ÇARE — tek cümleye toplamak operatörü yanlış işe yollar:
    `takvim_bos` → takvimi çek (bugün yapılabilir); `arsiv_yok` → PIT arşivi kur (yapısal)."""
    # Üçüncü ufuk (arşiv) burada da AÇIKÇA kurulur — `arsiv_ilk=None`: arşiv YOK.
    _ufuk_kur(monkeypatch, takvim_ilk="2026-07-20", defter_ilk="2022-01-03", arsiv_ilk=None)

    monkeypatch.setattr(earnings, "takvim_ufku", lambda: {
        "ilk": None, "son": None, "n_tarih": 0, "n_sembol": 0, "neden": "kazanç takvimi BOŞ"})
    bos = arming._kanit_durumu("episodic_pivot", {"n": 2, "avg_r": 1.846})
    assert bos["alt_sebep"] == "takvim_bos", f"boş takvim yanlış sınıflandı: {bos}"

    monkeypatch.setattr(earnings, "takvim_ufku", lambda: {
        "ilk": "2026-07-20", "son": "2026-09-11", "n_tarih": 29, "n_sembol": 219, "neden": None})
    arsiv = arming._kanit_durumu("episodic_pivot", {"n": 2, "avg_r": 1.846})
    assert arsiv["alt_sebep"] == "arsiv_yok", f"arşivsiz takvim yanlış sınıflandı: {arsiv}"

    assert bos["neden"] != arsiv["neden"], "iki AYRI çare aynı cümleyi alıyor"
    assert "ARŞİV" in arsiv["neden"], "arşiv çaresi cümlede adı geçmiyor"


def test_takvim_defteri_TAM_kapsiyorsa_kuraklik_GERCEK(monkeypatch):
    """Aşırıya kaçma çivisinin ikizi: arşiv gelirse cümle KENDİLİĞİNDEN geri döner.
    Yoksa `olculemez_pit_yok` kalıcı bir mazerete dönüşür ve gerçek kuraklığı gizler."""
    _ufuk_kur(monkeypatch, takvim_ilk="2021-01-01", defter_ilk="2022-01-03")
    d = arming._kanit_durumu("episodic_pivot", {"n": 2, "avg_r": 1.846})
    assert d["status"] == "insufficient_cf", (
        f"çapa defterin tamamını kapsıyor ama hâlâ 'ölçülemez' deniyor — mazeret kalıcılaşmış: {d}")


def test_PIT_capasi_OLMAYAN_kurulum_hala_insufficient_cf():
    """Aşırıya kaçma çivisi: düzeltme YALNIZ PIT-çapalı kurulumları etkiler."""
    d = arming._kanit_durumu("pullback", {"n": 21, "avg_r": -0.968})
    assert d["status"] == "insufficient_cf", (
        f"PIT çapası olmayan kurulumun cümlesi değişmiş — kapsam taşmış: {d}")
    assert d["n"] == 21 and d["avg_r"] == -0.968


# --------------------------------------------------- kayıt bir İDDİA olmasın

def test_PIT_kaydindaki_her_kurulum_capayi_GERCEKTEN_cagiriyor():
    """Kayıt kendi kendini doğrular: adı yazılı her kurulumun değerlendiricisi
    `days_since_report` çağırmalı. Çağırmıyorsa kayıt bir iddiadır, ölçüm değil."""
    assert arming.PIT_CAPALI_KURULUMLAR, "kayıt boş — çivi hiçbir şeyi korumuyor"
    for setup, capa in arming.PIT_CAPALI_KURULUMLAR.items():
        fn = getattr(strategy, f"evaluate_{setup}", None)
        assert fn is not None, f"{setup}: değerlendirici YOK — kayıt hayalet ad taşıyor"
        src = inspect.getsource(fn)
        cagri = capa.split(".")[-1]
        assert cagri in src, (
            f"{setup}: kayıt '{capa}' diyor ama değerlendirici onu ÇAĞIRMIYOR — "
            "kayıt ölçümden koptu")


def test_PIT_capasi_cagiran_her_kurulum_kayitta():
    """Ters yön: çapayı çağıran ama kayıtta olmayan bir kurulum, sessizce yanlış
    cümleyle raporlanır. Yeni bir kazanç-çapalı kurulum eklenirse bu çivi öter."""
    eksik = []
    for ad in dir(strategy):
        if not ad.startswith("evaluate_"):
            continue
        fn = getattr(strategy, ad)
        if not callable(fn):
            continue
        try:
            src = inspect.getsource(fn)
        except (OSError, TypeError):  # sessiz-yutma: kaynağı okunamayan sarmalayıcı; çivinin konusu değil, kayıt kontrolü kalan adlarla sürer
            continue
        if "days_since_report" in src:
            setup = ad[len("evaluate_"):]
            if setup not in arming.PIT_CAPALI_KURULUMLAR:
                eksik.append(setup)
    assert not eksik, (
        f"kazanç çapası çağıran ama PIT kaydında OLMAYAN kurulum(lar): {eksik} — "
        "bunlar 'örneklem dolmadı' diye raporlanır ve operatör boşuna bekler")

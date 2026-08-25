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

from meridian import arming, earnings, strategy


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

def test_PIT_capali_kurulum_insufficient_cf_DEMEZ():
    d = arming._kanit_durumu("episodic_pivot", {"n": 2, "avg_r": 1.846})
    assert d["status"] != "insufficient_cf", (
        "PIT çapası çözülemeyen kurulum 'örneklem dolmadı' diye raporlanıyor — "
        f"tam da düzeltilen kusur: {d}")
    assert d["status"] == "olculemez_pit_yok", f"beklenmeyen durum: {d}"
    assert d.get("capa"), "hangi çapanın eksik olduğu YAZILI olmalı"
    # kanıt raporun İÇİNDE olmalı — okuyucu ikinci bir yere bakmak zorunda kalmasın
    assert "takvim" in d and "defter" in d, f"kanıt bloğu yok: {sorted(d)}"


def _ufuk_kur(monkeypatch, takvim_ilk, defter_ilk):
    """Ortam bağımsız dal seçimi: iki ufuk da AÇIKÇA kurulur.

    Bu olmadan test yerelde 'takvim boş' dalından geçip yeşil görünüyordu — korunmak istenen
    dal (takvim defterden SONRA başlıyor) ise hiç koşmuyordu. Ölçüm bağlamı tuzağının
    testteki hâli: yeşil, ama başka bir şeyin yeşili."""
    from meridian import counterfactual as cf
    monkeypatch.setattr(earnings, "takvim_ufku", lambda: {
        "ilk": takvim_ilk, "son": "2026-09-11", "n_tarih": 29, "n_sembol": 219, "neden": None})
    monkeypatch.setattr(cf, "defter_ufku", lambda: {
        "ilk": defter_ilk, "son": "2026-08-19", "n": 8754, "neden": None})


def test_takvim_defterden_SONRA_baslarsa_olculemez(monkeypatch):
    _ufuk_kur(monkeypatch, takvim_ilk="2026-07-20", defter_ilk="2022-01-03")
    d = arming._kanit_durumu("episodic_pivot", {"n": 2, "avg_r": 1.846})
    assert d["status"] == "olculemez_pit_yok", f"kör dönem görülmedi: {d}"
    assert "2022-01-03" in d["neden"] and "2026-07-20" in d["neden"], (
        f"neden cümlesi iki ufku da taşımıyor: {d['neden']}")


def test_bos_takvim_ile_arsivsiz_takvim_AYRI_alt_sebep(monkeypatch):
    """İki alt sebep, İKİ AYRI ÇARE — tek cümleye toplamak operatörü yanlış işe yollar:
    `takvim_bos` → takvimi çek (bugün yapılabilir); `arsiv_yok` → PIT arşivi kur (yapısal)."""
    from meridian import counterfactual as cf
    monkeypatch.setattr(cf, "defter_ufku", lambda: {
        "ilk": "2022-01-03", "son": "2026-08-19", "n": 8754, "neden": None})

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

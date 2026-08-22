"""Kitap ↔ broker AÇIK POZİSYON adet mutabakatı — çiviler (ROADMAP Ö-53).

NEDEN ÇİVİ: 2026-08-22'de ölçüldü ki yedi açık pozisyonun YEDİSİNDE de kitap ile broker adet
tutmuyor (kitap 15.661,22 fazla maliyet taşıyor) ve panoda bunun HİÇBİR izi yoktu — operatör
yalnız toplamda bir "açıklanamayan 2.623,34" görüyordu. Bu alan o ayrışmayı GÖRÜNÜR kılar.

EN ÖNEMLİ ÇİVİ `test_okunamayan_taraf_ayrisma_yok_demek_degil`: `mirror_divergence` tam bu işi
yapması gerekirken `None` döndürüyor ve pano `None`'ı "ayrışma yok" gibi gösteriyor. Aynı hatayı
burada TEKRARLAMAK, bulguyu yazıp üstüne aynı tuzağı kurmak olurdu.
"""
import pytest

from meridian import sermaye as S


def test_fonksiyon_var():
    assert callable(getattr(S, "pozisyon_mutabakati", None)), \
        "pozisyon_mutabakati YOK — Ö-53 ayrışması panoda görünmez kalır"


def test_ayrisan_adet_yakalanir():
    o = S.pozisyon_mutabakati({"AMGN": 33, "BDX": 43}, {"AMGN": 22, "BDX": 43})
    assert o["ayrisan_sayisi"] == 1
    a = o["ayrisan"][0]
    assert a["ticker"] == "AMGN" and a["kitap"] == 33 and a["broker"] == 22 and a["fark"] == 11
    assert o["toplam_sembol"] == 2


def test_tek_taraflilar_AYRI_kovalarda():
    """Yön KAYBOLMAZ: kitapta olup broker'da olmayan ile tersi AYNI ŞEY DEĞİLDİR.
    İlki karşılıksız pozisyon (Ö-52 sınıfı), ikincisi kitabın hiç bilmediği pozisyon (NVDA vakası)."""
    o = S.pozisyon_mutabakati({"ALL": 10}, {"NVDA": 1})
    assert [x["ticker"] for x in o["yalniz_kitapta"]] == ["ALL"]
    assert [x["ticker"] for x in o["yalniz_brokerda"]] == ["NVDA"]
    assert o["ayrisan_sayisi"] == 2, "tek taraflılar da AYRIŞMADIR — sayıma girmeli"


def test_tam_mutabakat_temiz():
    o = S.pozisyon_mutabakati({"CRM": 19}, {"CRM": 19})
    assert o["ayrisan_sayisi"] == 0 and o["ayrisan"] == []
    assert o["olculemedi_neden"] is None


@pytest.mark.parametrize("kitap,broker", [(None, {"A": 1}), ({"A": 1}, None), (None, None)])
def test_okunamayan_taraf_ayrisma_yok_demek_degil(kitap, broker):
    """UYDURMA YASAĞI. Taraflardan biri okunamazsa sonuç `0 ayrışma` OLAMAZ — `None` + neden.
    `mirror_divergence`in bugünkü kusuru tam budur ve tekrarlanmaz."""
    o = S.pozisyon_mutabakati(kitap, broker)
    assert o["ayrisan_sayisi"] is None, "okunamayan taraf 'ayrışma yok' diye raporlandı — uydurma"
    assert o["olculemedi_neden"] and len(o["olculemedi_neden"]) >= 20


def test_bos_iki_taraf_OLCULDU_sayilir():
    """İki taraf da BOŞ ise bu bir bilgi YOKLUĞU değil, ölçülmüş bir gerçektir: pozisyon yok."""
    o = S.pozisyon_mutabakati({}, {})
    assert o["ayrisan_sayisi"] == 0 and o["olculemedi_neden"] is None


# ─────────────────────────────────────────────────────────────────────────────
# YASA 6 — ÜRETİLEN ALANIN OKUYUCUSU OLMALI.
# Bu bölüm bir BORÇTAN doğdu: `broker_mutabakati` 2026-08-22'de `/api/today`e eklendi ama panoda
# HİÇ çizilmedi. Yani operatörün "para tutmuyor" sorusunun cevabı üretiliyordu ve operatör onu
# göremiyordu. Çivi olmadan aynı borç sessizce geri gelir.
import ast
import pathlib

APP = pathlib.Path(__file__).resolve().parents[1] / "meridian" / "web" / "app.js"
API = pathlib.Path(__file__).resolve().parents[1] / "meridian" / "api.py"


@pytest.mark.parametrize("alan", ["broker_mutabakati", "pozisyon_mutabakati"])
def test_uretilen_alanin_pano_okuyucusu_var(alan):
    api, app = API.read_text(encoding="utf-8"), APP.read_text(encoding="utf-8")
    assert f'd["{alan}"]' in api, f"{alan} API'de üretilmiyor"
    assert alan in app, (
        f"{alan} üretiliyor ama panoda HİÇ okunmuyor — YASA 6. Operatör cevabı yalnız API "
        f"yükünde görür, panoda göremez (2026-08-22 borcu).")


def test_pano_olculemedi_ile_ayrisma_yoku_AYIRIYOR():
    """Panoda `null` "ayrışma yok" gibi görünürse alan yalan söyler. `mirror_divergence`in
    bugünkü kusuru budur ve bu satır onun tekrarlanmasını engeller."""
    app = APP.read_text(encoding="utf-8")
    i = app.index("function mutabakatSatirlari")
    govde = app[i:app.index("\nfunction ", i + 10)]
    assert "ölçülemedi" in govde, "pano ölçülemedi durumunu ayrı GÖSTERMİYOR"
    assert "ayrisan_sayisi" in govde and "== null" in govde, \
        "pano null kontrolü yapmıyor — 0 ile null aynı görünür"


def test_cagri_yeri_TASIMA_saglıgını_soruyor():
    """ADAPTÖR SÖZLEŞMESİ TUZAĞI: `alpaca.positions()` ARIZA hâlinde de `[]` döner (boş liste,
    None DEĞİL). Çağrı yeri buna bakmadan boş listeyi geçerse `pozisyon_mutabakati` "broker'da hiç
    pozisyon yok" diye okur ve kitaptaki her pozisyonu `yalniz_kitapta` sayar — broker düştüğünde
    YEDİ SAHTE AYRIŞMA. `watchdog.koruma_report` bu dalı taşıma sağlığıyla çözüyor; çağrı yeri de
    aynı kapıdan geçmeli.

    Kusur ÖZ İNCELEMEDE bulundu (2026-08-22): fonksiyonun kendi çivileri sağlamdı, hatalı olan
    ÇAĞRI YERİYDİ — birim testi geçen kod entegrasyonda yalan söyleyebilir.

    AST İLE, METİNLE DEĞİL: ilk hâli `"transport()" in blok` diyordu ve TOTOLOJİYDİ — aynı metin
    hemen üstteki YORUMDA geçiyor, yani kod silinince bile çivi yeşil kalıyordu (kasıtlı-kırmızı
    bunu yakaladı). Şimdi `broker_pozisyonlar` argümanının KENDİ ifadesi sorgulanıyor."""
    agac = ast.parse(API.read_text(encoding="utf-8"))
    cagri = next((d for d in ast.walk(agac)
                  if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                  and d.func.attr == "pozisyon_mutabakati"), None)
    assert cagri is not None, "pozisyon_mutabakati çağrısı bulunamadı — çapa çürüdü"
    kw = next((k for k in cagri.keywords if k.arg == "broker_pozisyonlar"), None)
    assert kw is not None, "broker_pozisyonlar adlandırılmış argüman olarak geçmiyor"
    adlar = {n.id for n in ast.walk(kw.value) if isinstance(n, ast.Name)}
    cagrilar = {n.func.attr for n in ast.walk(kw.value)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert ("_tasima_ok" in adlar) or ("transport" in cagrilar), (
        f"broker_pozisyonlar ifadesi taşıma sağlığını SORMUYOR (adlar={sorted(adlar)}) — "
        f"broker düştüğünde boş liste 'pozisyon yok' diye okunur ve SAHTE ayrışma raporlanır")

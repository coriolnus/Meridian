"""BRACKET KORUMASININ DOLUMU GÖRÜNMÜYORDU — PANW SINIFI · v307

VAKA (2026-08-25, operatör): "PANW broker'da stop'a düştü ve şu an sadece kitapta gözüküyor."
Ölçüldü ve doğrulandı: PANW'ın koruyucu stop bacağı 342,70'ten DOLDU (32 hisse, OCO kardeşi
limit bacağı iptal), broker'da pozisyon YOK — ama kitap 39 adet açık taşıyor.

KÖK NEDEN — TEK HÜKÜM NOKTASI DOĞRU İLKEYDİ AMA YANLIŞ HÜKÜM YENİDEN KULLANILDI:
`_koruma_dolumu_bul` "bu koruma benim mi?" sorusunu SÜPÜRÜCÜNÜN sahiplik hükmüyle soruyordu
(`coid_sinifi(o)[0] == SINIF_KORUMA`). Ama o hüküm başka bir sorunun cevabıdır:
    süpürücü      → "bu emri İPTAL EDEBİLİR MİYİM?"
    mutabakat     → "KORUMAM DOLDU MU?"
Motor bracket'inde koruma bacaktadır, sahiplik kanıtı ise PARENT'tadır — ve parent bir GİRİŞ
emridir (`P-2026-08-21-PANW`, side=buy) → `coid_sinifi` onu `giris` der → süzgeç eler.
Bacaklar tek başına Alpaca'nın UUID coid'ini taşır → `yabanci` ("motor öneki YOK") düşerler.
Yani motor bracket'iyle korunan HİÇBİR pozisyonun stop dolumu görülemiyordu.

KAPSAM ÖLÇÜLDÜ: 9 broker pozisyonundan 5'i bracket bacağıyla korunuyor (DE · MRK · MRNA ·
BDX · CRM), 3'ü Meridian OCO'su (AMGN · BKNG · EMR). Yani kusur PANW'a özgü DEĞİL; beş
pozisyon daha aynı sessiz kaybı yaşayacaktı.

LATENT İKİNCİ KUSUR (bu çivinin ASIL koruduğu şey): süzgeci naifçe gevşetmek DAHA KÖTÜ olurdu.
`koruma_fill` adayları `[order] + legs` sırasıyla tarar ve ilk dolumu döner. Bracket parent'ı
GİRİŞ dolumudur (PANW: 357,66) ve `type == "limit"` olduğu için `bacak="hedef"` etiketlenir —
yani PANW GİRİŞ fiyatından "kâr-al doldu" diye kapatılırdı. Gerçek çıkış 342,70 STOP.
Zararlı bir işlem kârsız görünürdü ve kitap yanlış K/Z yazardı.
BU YÜZDEN B DALI YALNIZ `legs[]`E BAKAR — parent ASLA aday değildir.
"""
from __future__ import annotations

from meridian import loop
from meridian.adapters import alpaca


def _bracket_giris(sym: str, *, stop_dolum: float | None = None, giris_dolum: float = 357.66) -> dict:
    """Motor bracket girişi: parent BUY (giriş dolumu), bacaklar Alpaca UUID coid'li."""
    legs = [
        {"symbol": sym, "type": "limit", "side": "sell", "status": "canceled",
         "client_order_id": "dd144657-8984-4b6e-8a3d-08fb84e4da00", "filled_qty": "0"},
        {"symbol": sym, "type": "stop", "side": "sell",
         "status": "filled" if stop_dolum is not None else "held",
         "client_order_id": "8894a5d1-df17-4242-8fa0-da25df37181d",
         "filled_qty": "32" if stop_dolum is not None else "0",
         "filled_avg_price": str(stop_dolum) if stop_dolum is not None else None,
         "stop_price": "342.85"},
    ]
    return {"symbol": sym, "type": "limit", "side": "buy", "status": "filled",
            "order_class": "bracket", "client_order_id": f"P-2026-08-21-{sym}",
            "filled_qty": "32", "filled_avg_price": str(giris_dolum), "legs": legs}


def _meridian_oco(sym: str, *, stop_dolum: float | None = None) -> dict:
    """Meridian'ın kendi koruma OCO'su: parent limit (hedef), bacak stop; coid P-KORUMA-…"""
    return {"symbol": sym, "type": "limit", "side": "sell", "status": "new",
            "order_class": "oco", "client_order_id": f"P-KORUMA-20260809-0835-{sym[:3]}",
            "filled_qty": "0",
            "legs": [{"symbol": sym, "type": "stop", "side": "sell",
                      "status": "filled" if stop_dolum is not None else "held",
                      "filled_qty": "22" if stop_dolum is not None else "0",
                      "filled_avg_price": str(stop_dolum) if stop_dolum is not None else None,
                      "client_order_id": f"P-KORUMA-20260809-0835-{sym[:3]}-stop"}]}


# ------------------------------------------------------------- B dalı: bracket

def test_bracket_stop_dolumu_GORULUYOR():
    """ASIL ÇİVİ — PANW vakası. Bracket bacağının dolumu artık bulunuyor."""
    kd = loop._koruma_dolumu_bul([_bracket_giris("PANW", stop_dolum=342.70)], "PANW")
    assert kd is not None, (
        "motor bracket'inin stop dolumu HÂLÂ görünmüyor — PANW sınıfı açık kalır "
        "(5 açık pozisyon daha aynı yolda: DE·MRK·MRNA·BDX·CRM)")
    assert kd["bacak"] == "stop", f"bacak tipi yanlış: {kd}"
    assert abs(float(kd["price"]) - 342.70) < 1e-6, f"dolum fiyatı yanlış: {kd}"


def test_GIRIS_dolumu_CIKIS_sanilmaz():
    """LATENT KUSUR ÇİVİSİ: parent'ın kendi ALIŞ dolumu (357,66) asla çıkış sayılmamalı.
    Bu olsaydı zararlı bir işlem 'hedefe ulaştı' diye kârsız görünür, kitap yanlış K/Z yazardı."""
    kd = loop._koruma_dolumu_bul([_bracket_giris("PANW", stop_dolum=342.70)], "PANW")
    assert kd is not None
    assert abs(float(kd["price"]) - 357.66) > 1e-6, (
        f"parent'ın GİRİŞ dolumu çıkış sanıldı ({kd['price']}) — kitap yanlış K/Z yazardı")
    assert kd["bacak"] != "hedef", f"stop dolumu 'hedef' diye etiketlendi: {kd}"


def test_bracket_stop_DOLMAMISSA_dolum_YOK():
    """Aşırıya kaçma çivisi: koruma hâlâ `held` iken dolum uydurulmaz."""
    assert loop._koruma_dolumu_bul([_bracket_giris("DE")], "DE") is None, (
        "dolmamış koruma DOLMUŞ sayıldı — kitap açık pozisyonu kapatırdı")


def test_bracket_bacaksizsa_dolum_YOK():
    """Bacağı olmayan bir `giris` emri koruma sayılmaz — B dalı `legs` ister."""
    o = _bracket_giris("DE")
    o["legs"] = []
    assert loop._koruma_dolumu_bul([o], "DE") is None


def test_bracket_OLMAYAN_giris_emri_koruma_sayilmaz():
    """`order_class` bracket değilse B dalı açılmaz — düz bir giriş emri koruma değildir."""
    o = _bracket_giris("DE", stop_dolum=600.0)
    o["order_class"] = "simple"
    assert loop._koruma_dolumu_bul([o], "DE") is None, (
        "bracket olmayan giriş emrinin bacağı koruma sayıldı — sınıf hükmü gevşemiş")


# -------------------------------------------------- A dalı: DAVRANIŞ DEĞİŞMEDİ

def test_meridian_OCO_yolu_AYNEN_calisiyor():
    """AMGN/BKNG/EMR yolu değişmemeli — A dalı bugünkü davranışı birebir korur."""
    kd = loop._koruma_dolumu_bul([_meridian_oco("AMGN", stop_dolum=389.42)], "AMGN")
    assert kd is not None and kd["bacak"] == "stop"
    assert abs(float(kd["price"]) - 389.42) < 1e-6, f"OCO dolumu bozuldu: {kd}"


def test_meridian_OCO_HEDEF_bacagi_hala_hedef():
    """Meridian OCO'sunda parent LİMİT hedef bacağıdır — orada parent'ı okumak DOĞRUdur.
    B dalının 'parent asla' kuralı A dalına SIZMAMALI."""
    o = _meridian_oco("AMGN")
    o.update(status="filled", filled_qty="22", filled_avg_price="453.50")
    kd = loop._koruma_dolumu_bul([o], "AMGN")
    assert kd is not None and kd["bacak"] == "hedef", f"OCO hedef dolumu kayboldu: {kd}"
    assert abs(float(kd["price"]) - 453.50) < 1e-6


def test_YABANCI_emir_ASLA_koruma_sayilmaz():
    """Sahiplik sınırı korunur: operatörün kendi emri motorun koruması değildir (A3)."""
    o = _bracket_giris("NVDA", stop_dolum=200.0)
    o["client_order_id"] = "kullanicinin-kendi-emri-123"
    assert alpaca.coid_sinifi(o)[0] == alpaca.SINIF_YABANCI
    assert loop._koruma_dolumu_bul([o], "NVDA") is None, (
        "operatörün kendi emri motor koruması sayıldı — sahiplik sınırı delindi")

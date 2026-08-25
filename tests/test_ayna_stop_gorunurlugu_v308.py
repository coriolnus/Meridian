"""AYNADAKİ STOP GÖRÜNÜRLÜĞÜ (v308) — `dashboard_view` koruma bacaklarını KAÇIRIYOR muydu?

KUSUR (canlı, 2026-08-25): pano "Aynadaki açık emirler" kartında sekiz satırın SEKİZİ de
"stop yok" diyordu. Gerçekte sekiz pozisyonun sekizinde de CANLI `held` stop emri vardı.

KÖK NEDEN — ÖLÇÜLDÜ, VARSAYILMADI (canlı A1 kâğıt hesap, salt-okuma GET):
  * Koruma stop bacaklarının NORMAL durumu `held`tir ve Alpaca'nın `status="open"` süzgeci
    `held`i ÜST DÜZEYDE dışarıda bırakır.
  * Koruma OCO'sunda stop bacağı üst düzeyde HİÇ görünmez; yalnız primary'nin `legs[]`i
    altından erişilir (`nested=True` şart). Bu şema ölçümü alpaca.py'de ÜÇÜNCÜ KEMER
    başlığı altında yazılı.
  * Bu yüzden `nested=True` TEK BAŞINA yetmez: `status="open"` + `nested` çekiminde yalnız
    OCO ebeveynlerin bacakları görünür (canlıda 8'de 3), üst düzeyde `held` duran stoplar
    yine kaybolur.
  * Doğru sorgu: `status="all"` + `nested=True` + bacak düzleştirme + `_LIVE_ORDER_STATES`.

BU DOSYA AĞA ÇIKMAZ. Kurgu emir gövdeleri yukarıdaki ÖLÇÜLEN şekli taklit eder:
  · AMGN/BKNG/EMR → koruma OCO'su: primary limit (`accepted`) + `legs[0]` stop (`held`).
  · BDX/CRM/DE/MRK/MRNA → düz bracket artığı: üst düzey limit (`accepted`) + üst düzey
    stop (`held`), `legs` boş.
  · NVDA → pozisyon VAR, hiçbir canlı koruma emri YOK (gerçekten korumasız).
  · PANW → stop'u dolmuş, pozisyon yok; ölü emirler canlı sayılmamalı.
"""
from __future__ import annotations

import pytest

from meridian.adapters import alpaca

# --- ÖLÇÜLEN ZEMİN (2026-08-25 canlı okuma; bu dosyada SABİT beklenti) ------------------------
STOPLAR = {"AMGN": 389.42, "BDX": 178.6, "BKNG": 191.54, "CRM": 185.2,
           "DE": 604.9, "EMR": 152.48, "MRK": 143.93, "MRNA": 111.6}
ADETLER = {"AMGN": 22, "BDX": 40, "BKNG": 22, "CRM": 19, "DE": 10,
           "EMR": 37, "MRK": 65, "MRNA": 8, "NVDA": 1}
OCO_SEMBOLLERI = ("AMGN", "BKNG", "EMR")          # stop bacağı `legs[]` altında
DUZ_SEMBOLLER = ("BDX", "CRM", "DE", "MRK", "MRNA")  # stop bacağı ÜST DÜZEY ve `held`

# Alpaca'nın `status="open"` süzgecinin GEÇİRDİĞİ durumlar — `held` BU LİSTEDE YOKTUR.
# Kusurun tamamı bu tek farkta yaşıyor.
ALPACA_OPEN_SUZGECI = ("new", "accepted", "pending_new", "accepted_for_bidding", "partially_filled")


def _emir(oid, sym, side, typ, durum, *, stop=None, limit=None, qty=1,
          coid=None, order_class=None, legs=None, damga="2026-08-25T13:30:00Z"):
    return {"id": oid, "client_order_id": coid or oid, "symbol": sym, "side": side,
            "type": typ, "status": durum, "qty": str(qty), "order_class": order_class,
            "stop_price": None if stop is None else str(stop),
            "limit_price": None if limit is None else str(limit),
            "submitted_at": damga, "legs": list(legs or [])}


def _depo() -> list[dict]:
    """Canlı hesabın ölçülen şeklini taklit eden emir deposu (en yeniden eskiye)."""
    d: list[dict] = []
    for sym in OCO_SEMBOLLERI:
        stop_px = STOPLAR[sym]
        d.append(_emir(f"oco-{sym}", sym, "sell", "limit", "accepted",
                       limit=round(stop_px * 1.3, 2), qty=ADETLER[sym],
                       coid=f"P-KORUMA-20260825-1000-{sym}", order_class="oco",
                       legs=[_emir(f"oco-{sym}-stop", sym, "sell", "stop", "held",
                                   stop=stop_px, qty=ADETLER[sym], order_class="oco")]))
    for sym in DUZ_SEMBOLLER:
        stop_px = STOPLAR[sym]
        d.append(_emir(f"tp-{sym}", sym, "sell", "limit", "accepted",
                       limit=round(stop_px * 1.3, 2), qty=ADETLER[sym],
                       coid=f"P-KORUMA-20260825-1000-{sym}"))
        d.append(_emir(f"sl-{sym}", sym, "sell", "stop", "held",
                       stop=stop_px, qty=ADETLER[sym]))
    # NVDA: yalnız DOLMUŞ giriş emri — canlı koruma YOK.
    d.append(_emir("giris-NVDA", "NVDA", "buy", "market", "filled", qty=1, coid="P-NVDA-1"))
    # PANW: stop DOLDU, kâr-al bacağı OCO gereği iptal — ikisi de ölü.
    d.append(_emir("sl-PANW", "PANW", "sell", "stop", "filled", stop=342.70, qty=39))
    d.append(_emir("tp-PANW", "PANW", "sell", "limit", "canceled", limit=420.0, qty=39))
    return d


class SahteUc:
    """Alpaca'nın liste ucunu taklit eder: `status` süzgeci ÜST DÜZEYE ve BACAKLARA aynı
    uygulanır, `nested=False` bacakları hiç göstermez, `limit` pencereyi kırpar."""

    def __init__(self, depo, *, dusur: str | None = None):
        self.depo = depo
        self.dusur = dusur          # None değilse her çağrı ARIZA (transport ok=False)
        self.cagrilar: list[dict] = []

    def orders(self, status="open", limit=50, nested=False, after=None, until=None):
        self.cagrilar.append({"status": status, "limit": limit, "nested": nested})
        if self.dusur is not None:
            alpaca._note(False, self.dusur)
            return []
        out = []
        for o in self.depo:
            if status == "open" and str(o["status"]).lower() not in ALPACA_OPEN_SUZGECI:
                continue
            k = dict(o)
            # ÖLÇÜLEN DAVRANIŞ: `status` süzgeci YALNIZ ÜST DÜZEYE uygulanır. `nested=True`
            # ile gelen bacaklar durumlarına bakılmaksızın taşınır — canlıda `status="open"`
            # + `nested` çekiminin üç `held` OCO bacağını göstermesinin sebebi budur.
            k["legs"] = [dict(b) for b in (o.get("legs") or [])] if nested else []
            out.append(k)
        alpaca._note(True)
        return out[:limit]


def _pozisyonlar():
    return [{"symbol": s, "qty": str(n), "side": "long", "avg_entry_price": "100",
             "current_price": "110", "unrealized_pl": "1"} for s, n in ADETLER.items()]


@pytest.fixture
def uc(monkeypatch):
    u = SahteUc(_depo())
    monkeypatch.setattr(alpaca, "orders", u.orders)
    monkeypatch.setattr(alpaca, "positions", lambda: (alpaca._note(True), _pozisyonlar())[1])
    monkeypatch.setattr(alpaca, "account",
                        lambda: (alpaca._note(True),
                                 {"equity": "100000", "cash": "5000", "status": "ACTIVE",
                                  "buying_power": "200000"})[1])
    monkeypatch.setattr(alpaca, "_paper_base", lambda: "https://paper-api.example.test")
    alpaca._note(True)
    return u


def _stoplu(satirlar):
    """Satırdaki HAM `stop` alanını sembole eşle. Alan Alpaca'nın DİZGE gösterimini
    olduğu gibi taşır (pano `sayi()` ile ayrıştırır) — burada karşılaştırma için çevrilir."""
    return {r["symbol"]: float(r["stop"]) for r in satirlar if r.get("stop") not in (None, "")}


# =============================================================================================
# ÇİVİ 1 — DÜZ / YARIM SORGULARIN NE KAÇIRDIĞI (kusurun kendisi, kurguda yeniden üretildi)
# =============================================================================================
def test_duz_acik_sorgu_held_stop_bacaklarinin_TAMAMINI_kacirir(uc):
    """Eski çağrı biçimi (`orders("open", 20)`): 8 satır döner, HİÇBİRİNDE stop yok."""
    satirlar = uc.orders("open", 20)
    assert len(satirlar) == 8, "kurgu depo canlı şekli taklit etmiyor (8 kâr-al bacağı beklenir)"
    assert [r for r in satirlar if r["stop_price"]] == [], \
        "düz `open` çekiminde stop görünüyor — kurgu Alpaca'nın `held` süzgecini taklit etmiyor"


def test_sadece_nested_eklemek_YETMEZ_ust_duzey_held_stoplar_yine_kayip(uc):
    """`status="open"` + `nested=True`: yalnız OCO bacakları görünür (canlıda 8'de 3)."""
    satirlar = uc.orders(status="open", limit=500, nested=True)
    goruneni = [b for o in satirlar for b in o["legs"] if b["type"] == "stop"]
    goruneni += [o for o in satirlar if o["type"] == "stop"]
    assert len(goruneni) == 3, f"open+nested {len(goruneni)} stop gösterdi; ölçülen canlı sayı 3"
    assert {o["symbol"] for o in goruneni} == set(OCO_SEMBOLLERI)


# =============================================================================================
# ÇİVİ 2 — DÜZELTİLMİŞ YOL: 8/8
# =============================================================================================
def test_dashboard_view_sekiz_pozisyonun_SEKIZINDE_de_canli_stop_gosterir(uc):
    g = alpaca.dashboard_view()
    olculen = _stoplu(g["open_orders"])
    assert olculen == pytest.approx(STOPLAR), \
        f"stop seviyeleri ölçülen zeminle örtüşmüyor: {olculen}"


def test_dashboard_view_emir_sorgusunu_ALL_ve_NESTED_cagirir(uc):
    """ÇAĞRI BİÇİMİ çivisi: kaynakta dize aramak değil, GERÇEK argümanları okumak."""
    alpaca.dashboard_view()
    emir_cagrilari = [c for c in uc.cagrilar]
    assert emir_cagrilari, "dashboard_view emir ucunu hiç çağırmadı"
    c = emir_cagrilari[0]
    assert c["status"] == "all", f"`status={c['status']!r}` — `held` stoplar yine kaçar"
    assert c["nested"] is True, "`nested=False` — OCO stop bacağı `legs[]` altında görünmez"
    assert c["limit"] > 20, f"pencere {c['limit']} — eski 20 tavanı korumaları kırpıyordu"


def test_olu_emirler_canli_sayilmaz(uc):
    g = alpaca.dashboard_view()
    semboller = {r["symbol"] for r in g["open_orders"]}
    assert "PANW" not in semboller, "dolmuş/iptal PANW bacakları canlı emir diye gösterildi"
    durumlar = {str(r["status"]).lower() for r in g["open_orders"]}
    assert durumlar <= set(alpaca._LIVE_ORDER_STATES), f"canlı olmayan durum sızdı: {durumlar}"


def test_geriye_uyum_satir_alan_ADLARI_korundu(uc):
    g = alpaca.dashboard_view()
    eski = {"symbol", "side", "type", "qty", "status", "stop", "limit"}
    for r in g["open_orders"]:
        assert eski <= set(r), f"pano satırından alan DÜŞTÜ: {eski - set(r)}"


# =============================================================================================
# ÇİVİ 3 — "KORUMA YOK" ≠ "ÖLÇÜLEMEDİ"
# =============================================================================================
def test_korumasiz_pozisyon_KORUMA_YOK_der(uc):
    g = alpaca.dashboard_view()
    assert g["koruma_neden"] is None, "koruma hükmü kurulamadı ama pozisyonlar okunmuştu"
    nvda = g["koruma"]["NVDA"]
    assert nvda["durum"] == "korumasiz", f"NVDA gerçekten korumasız; hüküm {nvda['durum']!r}"
    assert nvda["stop"] is None
    assert nvda["neden"] and len(nvda["neden"]) >= 20, "korumasızlık gerekçesiz bırakıldı"


def test_korunan_pozisyonlar_KORUMALI_ve_stop_fiyatini_tasir(uc):
    g = alpaca.dashboard_view()
    for sym, px in STOPLAR.items():
        k = g["koruma"][sym]
        assert k["durum"] == "korumali", f"{sym}: canlı stop var ama hüküm {k['durum']!r}"
        assert k["stop"] == pytest.approx(px), f"{sym}: stop {k['stop']} ≠ ölçülen {px}"


def test_emir_listesi_okunamazsa_OLCULEMEDI_der_KORUMASIZ_demez(monkeypatch):
    """ARIZA ≠ KORUMA YOK. Arızada 'korumasız' demek uydurma bir olgu yazmaktır."""
    u = SahteUc(_depo(), dusur="ReadTimeout: emir ucu yanıt vermedi")
    monkeypatch.setattr(alpaca, "orders", u.orders)
    monkeypatch.setattr(alpaca, "positions", lambda: (alpaca._note(True), _pozisyonlar())[1])
    monkeypatch.setattr(alpaca, "account", lambda: (alpaca._note(True), {"equity": "1"})[1])
    monkeypatch.setattr(alpaca, "_paper_base", lambda: "https://paper-api.example.test")
    g = alpaca.dashboard_view()
    assert g["open_orders"] is None, "arızada boş LİSTE dönmek 'açık emir yok' yalanıdır"
    assert g["open_orders_neden"] and "ReadTimeout" in g["open_orders_neden"]
    assert g["open_orders_kirpma"] is None, "ölçülemeyen listenin kırpma muhasebesi olamaz"
    for sym in ADETLER:
        k = g["koruma"][sym]
        assert k["durum"] == "olculemedi", f"{sym}: arızada hüküm {k['durum']!r} verildi"
        assert k["neden"] and len(k["neden"]) >= 20


def test_pozisyonlar_okunamazsa_koruma_haritasi_None_ve_NEDENLI(monkeypatch):
    u = SahteUc(_depo())
    monkeypatch.setattr(alpaca, "orders", u.orders)
    monkeypatch.setattr(alpaca, "positions",
                        lambda: (alpaca._note(False, "ConnectError: pozisyon ucu"), [])[1])
    monkeypatch.setattr(alpaca, "account", lambda: (alpaca._note(True), {"equity": "1"})[1])
    monkeypatch.setattr(alpaca, "_paper_base", lambda: "https://paper-api.example.test")
    g = alpaca.dashboard_view()
    assert g["koruma"] is None, "pozisyon listesi okunamadan koruma hükmü UYDURULDU"
    assert g["koruma_neden"] and "ConnectError" in g["koruma_neden"]


# =============================================================================================
# ÇİVİ 4 — KIRPMA BEYANLIDIR
# =============================================================================================
def test_kirpma_yokken_muhasebe_sifir_ve_pencere_doygun_degil(uc):
    g = alpaca.dashboard_view()
    k = g["open_orders_kirpma"]
    assert k["kirpilan"] == 0
    assert k["canli"] == len(g["open_orders"]) == 16, "8 kâr-al + 8 stop bekleniyordu"
    assert k["pencere_doygun"] is False


def test_tavan_asilirsa_KAC_SATIR_kirpildigi_govdede_gorunur(uc, monkeypatch):
    monkeypatch.setattr(alpaca, "_PANO_EMIR_TAVANI", 5)
    g = alpaca.dashboard_view()
    k = g["open_orders_kirpma"]
    assert len(g["open_orders"]) == 5, "tavan uygulanmadı"
    assert k["tavan"] == 5 and k["canli"] == 16 and k["kirpilan"] == 11, \
        f"sessiz kırpma: muhasebe {k}"


def test_koruma_hukmu_TAVANDAN_etkilenmez(uc, monkeypatch):
    """Kırpma bir GÖRÜNTÜ sınırıdır; kırpılan satır 'koruma yok' hükmü DOĞURAMAZ."""
    monkeypatch.setattr(alpaca, "_PANO_EMIR_TAVANI", 2)
    g = alpaca.dashboard_view()
    korumali = {s for s, k in g["koruma"].items() if k["durum"] == "korumali"}
    assert korumali == set(STOPLAR), f"tavan koruma hükmünü bozdu: {korumali}"


def test_pencere_dolarsa_DOYGUN_isaretlenir(monkeypatch):
    """Pencere tavanına dayanmış liste 'hepsi bu' demez — sessiz ufuk kırpması BEYAN edilir."""
    u = SahteUc(_depo())
    monkeypatch.setattr(alpaca, "orders", u.orders)
    monkeypatch.setattr(alpaca, "positions", lambda: (alpaca._note(True), _pozisyonlar())[1])
    monkeypatch.setattr(alpaca, "account", lambda: (alpaca._note(True), {"equity": "1"})[1])
    monkeypatch.setattr(alpaca, "_paper_base", lambda: "https://paper-api.example.test")
    monkeypatch.setattr(alpaca, "_PANO_EMIR_PENCERESI", 4)
    g = alpaca.dashboard_view()
    k = g["open_orders_kirpma"]
    assert k["pencere_istenen"] == 4 and k["pencere_donen"] == 4
    assert k["pencere_doygun"] is True, "pencere doldu ama liste 'tam' gibi sunuldu"


# =============================================================================================
# ÇİVİ 5 — NEYİN KORUMA SAYILDIĞI (mutasyon turunda M13 buradan kaçmıştı)
# =============================================================================================
def _tek_sembol(monkeypatch, depo, poz):
    """Tek sembollük mini sahne — koruma hükmünün SINIRLARINI sınamak için."""
    u = SahteUc(depo)
    monkeypatch.setattr(alpaca, "orders", u.orders)
    monkeypatch.setattr(alpaca, "positions", lambda: (alpaca._note(True), [poz])[1])
    monkeypatch.setattr(alpaca, "account", lambda: (alpaca._note(True), {"equity": "1"})[1])
    monkeypatch.setattr(alpaca, "_paper_base", lambda: "https://paper-api.example.test")
    return alpaca.dashboard_view()


def _poz(sym, yon="long"):
    return {"symbol": sym, "qty": "5", "side": yon, "avg_entry_price": "40",
            "current_price": "45", "unrealized_pl": "25"}


def test_yalniz_KAR_AL_bacagi_olan_pozisyon_KORUMASIZ_sayilir(monkeypatch):
    """Kâr-al limit bacağı zarar tarafını KAPATMAZ. Onu koruma saymak, panonun düzeltilen
    yalanının aynası olurdu: satır dolu görünür, pozisyon çıplaktır."""
    g = _tek_sembol(monkeypatch,
                    [_emir("tp-ZZZ", "ZZZ", "sell", "limit", "accepted", limit=60.0, qty=5)],
                    _poz("ZZZ"))
    k = g["koruma"]["ZZZ"]
    assert k["durum"] == "korumasiz", f"kâr-al bacağı koruma sayıldı: {k}"
    assert k["stop"] is None and k["stop_n"] == 0


def test_TERS_yonlu_stop_uzun_pozisyonu_korumaz(monkeypatch):
    """Uzun pozisyonu SELL stop korur; BUY stop bir ekleme emridir, koruma değil."""
    g = _tek_sembol(monkeypatch,
                    [_emir("bs-ZZZ", "ZZZ", "buy", "stop", "held", stop=70.0, qty=5)],
                    _poz("ZZZ"))
    assert g["koruma"]["ZZZ"]["durum"] == "korumasiz"


def test_KISA_pozisyonu_BUY_stop_korur(monkeypatch):
    """Yön kemerinin pozitif kontrolü — süzgeç 'her şeyi ele' diye geçmiyor."""
    g = _tek_sembol(monkeypatch,
                    [_emir("bs-ZZZ", "ZZZ", "buy", "stop", "held", stop=70.0, qty=5)],
                    _poz("ZZZ", yon="short"))
    k = g["koruma"]["ZZZ"]
    assert k["durum"] == "korumali" and k["stop"] == pytest.approx(70.0)


def test_pozisyon_YONU_okunamazsa_esleme_BEYAN_edilir(monkeypatch):
    """Yön süzgeci uygulanamadıysa bu okuyucuya YAZILIR — sessizce 'korumalı' denmez."""
    poz = _poz("ZZZ")
    poz["side"] = ""
    g = _tek_sembol(monkeypatch,
                    [_emir("ss-ZZZ", "ZZZ", "sell", "stop", "held", stop=30.0, qty=5)], poz)
    k = g["koruma"]["ZZZ"]
    assert k["durum"] == "korumali"
    assert k["neden"] and "side" in k["neden"], f"yön belirsizliği beyan edilmedi: {k}"


def test_iz_suren_stop_fiyatsizsa_KORUMA_VAR_ama_fiyat_OLCULEMEDI(monkeypatch):
    """Emir CANLI ama tetik fiyatı yayınlanmamış: koruma VARDIR, fiyat UYDURULMAZ."""
    g = _tek_sembol(monkeypatch,
                    [_emir("ts-ZZZ", "ZZZ", "sell", "trailing_stop", "held", stop=None, qty=5)],
                    _poz("ZZZ"))
    k = g["koruma"]["ZZZ"]
    assert k["durum"] == "korumali", "canlı iz-süren stop 'koruma yok' sayıldı"
    assert k["stop"] is None and k["stop_n"] == 1
    assert k["neden"] and len(k["neden"]) >= 20, "ölçülemeyen fiyat gerekçesiz bırakıldı"


def test_CIFTE_koruma_sayilir_tek_fiyatin_arkasindaki_emir_sayisi_gorunur(monkeypatch):
    """İki canlı stop aynı hisseyi rehin tutar — tek fiyat gösterirken sayı gizlenmez."""
    g = _tek_sembol(monkeypatch,
                    [_emir("s1-ZZZ", "ZZZ", "sell", "stop", "held", stop=30.0, qty=5),
                     _emir("s2-ZZZ", "ZZZ", "sell", "stop_limit", "held", stop=31.0, qty=5)],
                    _poz("ZZZ"))
    assert g["koruma"]["ZZZ"]["stop_n"] == 2


def test_BICIMSIZ_stop_fiyati_None_dondurur_SIFIR_degil(monkeypatch):
    """UYDURMA YASAĞI: çevrilemeyen fiyat 0 olamaz. 0 bir stop seviyesi gibi okunur ve
    "stop 0,00 $" diye ekrana çıkardı — koruma sanılan bir yalan."""
    g = _tek_sembol(monkeypatch,
                    [_emir("ss-ZZZ", "ZZZ", "sell", "stop", "held", stop="n/a", qty=5)],
                    _poz("ZZZ"))
    k = g["koruma"]["ZZZ"]
    assert k["stop"] is None, f"biçimsiz fiyat sayıya UYDURULDU: {k['stop']!r}"
    assert k["durum"] == "korumali", "emir CANLI; fiyatın okunamaması korumayı yok etmez"
    assert k["neden"] and len(k["neden"]) >= 20


# =============================================================================================
# ÇİVİ 6 — DENETİM TURU: ÖLÇÜLMEMİŞ SIFIR · SESSİZCE DÜŞEN POZİSYON · DOYGUN PENCERE
# Üçü de aynı aileden: hüküm verilemeyecek bir yerde hüküm verilmiş gibi görünmek.
# =============================================================================================
def _sahne(monkeypatch, depo, pozlar):
    """`_tek_sembol`in çok pozisyonlu genel hâli — koruma haritasının BÜTÜNÜ sınanır."""
    u = SahteUc(depo)
    monkeypatch.setattr(alpaca, "orders", u.orders)
    monkeypatch.setattr(alpaca, "positions", lambda: (alpaca._note(True), list(pozlar))[1])
    monkeypatch.setattr(alpaca, "account", lambda: (alpaca._note(True), {"equity": "1"})[1])
    monkeypatch.setattr(alpaca, "_paper_base", lambda: "https://paper-api.example.test")
    return alpaca.dashboard_view()


def test_ariza_dalinda_stop_n_NONE_dir_SIFIR_degil(monkeypatch):
    """UYDURMA YASAĞI: emir listesi okunamadıysa sembolde KAÇ koruma emri durduğu BİLİNMEZ.
    `stop_n: 0` "saydım, hiç yok" demektir — ölçülemeyen bir sayıyı olgu diye yazmaktır ve
    rozetin 'çifte koruma' okuması bu sıfırın üstüne kurulur."""
    u = SahteUc(_depo(), dusur="ReadTimeout: emir ucu yanıt vermedi")
    monkeypatch.setattr(alpaca, "orders", u.orders)
    monkeypatch.setattr(alpaca, "positions", lambda: (alpaca._note(True), _pozisyonlar())[1])
    monkeypatch.setattr(alpaca, "account", lambda: (alpaca._note(True), {"equity": "1"})[1])
    monkeypatch.setattr(alpaca, "_paper_base", lambda: "https://paper-api.example.test")
    g = alpaca.dashboard_view()
    for sym in ADETLER:
        k = g["koruma"][sym]
        assert k["durum"] == "olculemedi", f"{sym}: arızada hüküm {k['durum']!r} verildi"
        assert k["stop_n"] is None, \
            f"{sym}: ölçülemeyen koruma sayısı {k['stop_n']!r} diye YAZILDI (0 = 'saydım, yok')"


def test_sembolu_okunamayan_pozisyon_haritadan_SESSIZCE_dusmez(monkeypatch):
    """Bu kalemin öldürmek için var olduğu arızanın ta kendisi: hakkında HİÇBİR koruma hükmü
    bulunmayan, haritadan beyansız yok olmuş bir pozisyon. Satır BEYAN EDİLMİŞ bir anahtar
    altında `olculemedi` olarak taşınır."""
    pozlar = [_poz("ZZZ"),
              {"qty": "3", "side": "long", "avg_entry_price": "9"},        # `symbol` alanı YOK
              {"symbol": "   ", "qty": "4", "side": "long"}]               # boşluktan ibaret
    g = _sahne(monkeypatch,
               [_emir("ss-ZZZ", "ZZZ", "sell", "stop", "held", stop=30.0, qty=5)], pozlar)
    assert len(g["koruma"]) == 3, \
        f"üç pozisyon verildi, haritada {len(g['koruma'])} girdi var — satır SESSİZCE düştü"
    sembolsuz = {a: k for a, k in g["koruma"].items()
                 if a.startswith(alpaca.KORUMA_SEMBOLSUZ_ONEK)}
    assert len(sembolsuz) == 2, \
        f"iki sembolsüz satır {len(sembolsuz)} anahtara indi — anahtarlar birbirini eziyor"
    for anahtar, k in sembolsuz.items():
        assert k["durum"] == "olculemedi", f"{anahtar}: sembolsüz satıra hüküm verildi: {k}"
        assert k["stop"] is None and k["stop_n"] is None, f"{anahtar}: ölçülmemiş değer yazıldı"
        assert k["neden"] and len(k["neden"]) >= 20, f"{anahtar}: gerekçesiz bırakıldı"
    assert g["koruma"]["ZZZ"]["durum"] == "korumali", "okunabilen sembolün hükmü de bozuldu"


def test_pencere_DOYGUNKEN_korumasiz_denmez_OLCULEMEDI_denir(monkeypatch):
    """LATENT YALAN: `direction=desc` yüzünden pencere dolduğunda ESKİ ama hâlâ CANLI bir stop
    pencereden düşer. O an "korumasız — arıza değil, ÖLÇÜLMÜŞ olgu" demek artık doğru değildir:
    liste TAM olduğu KANITLANMAMIŞTIR, dolayısıyla olumsuz hüküm verilemez."""
    monkeypatch.setattr(alpaca, "_PANO_EMIR_PENCERESI", 1)
    g = _sahne(monkeypatch,
               [_emir("x-AAA", "AAA", "sell", "stop", "held", stop=10.0, qty=5)], [_poz("ZZZ")])
    assert g["open_orders_kirpma"]["pencere_doygun"] is True, "sahne kurulmadı: pencere doymadı"
    k = g["koruma"]["ZZZ"]
    assert k["durum"] == "olculemedi", \
        f"doygun pencerede olumsuz hüküm verildi: {k['durum']!r} — kanıtlanmamış 'korumasız'"
    assert k["stop"] is None and k["stop_n"] is None, "doygun pencerede koruma sayısı ölçülemez"
    assert k["neden"] and len(k["neden"]) >= 20, "doygunluk çekincesi gerekçesiz bırakıldı"


def test_pencere_DOYGUN_DEGILKEN_korumasiz_hukmu_YINE_verilir(monkeypatch):
    """Doygunluk kapısının negatif kontrolü: kapı 'her şeye ölçülemedi de' demiyor. Pencere
    KANITLI tamken 'korumasız' ölçülmüş bir olgudur ve operatör ona bakıp elle stop koyar."""
    g = _sahne(monkeypatch,
               [_emir("x-AAA", "AAA", "sell", "stop", "held", stop=10.0, qty=5)], [_poz("ZZZ")])
    assert g["open_orders_kirpma"]["pencere_doygun"] is False, "sahne kurulmadı: pencere doydu"
    k = g["koruma"]["ZZZ"]
    assert k["durum"] == "korumasiz", f"tam pencerede ölçülmüş olgu hükümsüz bırakıldı: {k}"
    assert k["stop_n"] == 0, "liste TAM okundu; sıfır burada ölçülmüş bir sayıdır"


def test_pencere_doygunken_KORUMALI_ayakta_kalir_ama_SAYI_alt_sinirdir(monkeypatch):
    """Doygunluk yalnız OLUMSUZ iddiayı çürütür. Görülen canlı stop hâlâ görülmüştür; ama
    `stop_n` artık bir ALT SINIRdır (pencere dışında ikinci bir stop olabilir) ve bu beyan
    edilmezse rozetin 'çifte koruma yok' okuması sessizce yalan olur."""
    monkeypatch.setattr(alpaca, "_PANO_EMIR_PENCERESI", 1)
    g = _sahne(monkeypatch,
               [_emir("ss-ZZZ", "ZZZ", "sell", "stop", "held", stop=30.0, qty=5)], [_poz("ZZZ")])
    assert g["open_orders_kirpma"]["pencere_doygun"] is True, "sahne kurulmadı: pencere doymadı"
    k = g["koruma"]["ZZZ"]
    assert k["durum"] == "korumali", "canlı stop GÖRÜLDÜ; doygun pencere olumlu kanıtı çürütmez"
    assert k["stop"] == pytest.approx(30.0) and k["stop_n"] == 1
    assert k["neden"] and "pencere" in k["neden"] and len(k["neden"]) >= 20, \
        f"koruma sayısının ALT SINIR olduğu beyan edilmedi: {k}"


def test_pencere_doygunlugu_OLCULEMEZSE_de_olumsuz_hukum_verilmez():
    """`pencere_doygun=None` = pencerenin doyup doymadığı BİLİNMİYOR. Bilinmeyen bir ufukla
    "korumasız" demek, doygun pencerede demekle aynı yalandır — olumsuz hüküm yine VERİLMEZ,
    olumlu hükümde de `stop_n` ALT SINIR olarak beyan edilir.

    `_koruma_hukmu` DOĞRUDAN çağrılır: bu dala `dashboard_view` üzerinden bugün ulaşılamıyor
    (kırpma muhasebesi ile emir arızası aynı koşulda doğar), ama sözleşme yazılı olduğu için
    çivisiz bırakılamaz — yarın çağıranın değişmesi sessizce yalan üretirdi."""
    yok = alpaca._koruma_hukmu([_poz("ZZZ")], [], None, None)["ZZZ"]
    assert yok["durum"] == "olculemedi", f"ölçülemeyen ufukla olumsuz hüküm verildi: {yok}"
    assert yok["stop"] is None and yok["stop_n"] is None
    assert yok["neden"] and len(yok["neden"]) >= 20

    satir = {"symbol": "ZZZ", "side": "sell", "type": "stop", "qty": "5",
             "status": "held", "stop": "30.0", "limit": None}
    var = alpaca._koruma_hukmu([_poz("ZZZ")], [satir], None, None)["ZZZ"]
    assert var["durum"] == "korumali" and var["stop"] == pytest.approx(30.0)
    assert var["stop_n"] == 1 and "pencere" in (var["neden"] or ""), \
        f"ölçülemeyen ufukta `stop_n`in ALT SINIR olduğu beyan edilmedi: {var}"

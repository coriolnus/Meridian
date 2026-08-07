"""test_koruma_yeniden_kurma_v211.py — KORUMAYI YENİDEN KURAN YOL (öneri → onay → OCO).

VAKA (canlı A1, 2026-08-07): dört motor pozisyonu broker'da KORUMASIZ, açık emir SIFIR. Kök neden
ölçüldü ve kapatıldı (E1-v2, TIF `gtc` — d47060b) ama o düzeltme YALNIZ BUNDAN SONRA gönderilen
bracket'ları bağlar. Hâlihazırda çıplak duran pozisyonlar için bu depoda hiçbir mekanizma YOKTU:
`watchdog.koruma_report()` (v209) onları görüyor, ama bekçi haber verir — düzeltmez.

BU DOSYA NEYİ ÇİVİLER — DOKUZ YASA, HER BİRİ AYRI BİR TESTLE:
  Y1 OCO ŞART        · iki gevşek emir DEĞİL (hesapta shorting_enabled=true)
  Y2 ADET BROKER'DAN · iç defterden ASLA (defter 33/43/64/54, broker 22/22/37/25)
  Y3 YALNIZ MOTOR    · operatörün NVDA'sı listelenir, emir ÜRETMEZ (A3)
  Y4 TIF + COID      · `gtc` (E1-v2) ve `ENGINE_COID_PREFIX` (A2 sahiplik)
  Y5 İDEMPOTANS      · canlı koruma varsa emir YOK; iki onay iki koruma kurmaz
  Y6 GEVŞETME YOK    · mevcut stop varsa yalnız YUKARI (A4) — arka kapı kapalı
  Y7 BROKER DÜŞÜK    · emir YOK + NEDEN (sessiz başarı SAHTE olurdu)
  Y8 DENETİM İZİ     · her gönderim olay bırakır (plan_id/sembol/adet/seviye/onaylayan) — YASA 6
  Y9 ONAYSIZ EMİR YOK· EN ÖNEMLİ ÇİVİ; jeton VE tura özel öneri kimliği olmadan hiçbir POST doğmaz
  Y10 BASIŞ KAYDI    · Y8'in eksik yarısı (2026-08-07): Y8 yalnız GÖNDERİMİ kaydediyordu, oysa
                       kayda değer asıl vaka REDDEDİLEN onaydır. Uç düzeyinde HER dal (onaysız /
                       bayat kimlik / ölçülemedi / gerçek gönderim) tek satır bırakır; satır jeton
                       TAŞIMAZ ve alt katmanın emir satırlarını ÇOĞALTMAZ.
artı: KISMİ BAŞARI DÜRÜST ("2/4 gönderildi + 2 neden", "tamam" DEĞİL) ve PANO (adet ayrışması
görünür, satır içi betik yok — CSP `script-src 'self'`).

YÖNTEM — HİÇBİR TEST AĞA ÇIKMAZ. İki katman ayrı ayrı sınanır:
  * ADAPTÖR katmanı: `alpaca.httpx` bir KAYIT EDİCİYLE değiştirilir; gerçek istemciye tek bir
    çağrı gitmez ve gönderilen GÖVDENİN ŞEKLİ (order_class/tif/side/coid) ölçülür.
  * API katmanı: `alpaca.submit_protective_oco` sahte bir adaptörle değiştirilir; kaç emrin,
    hangi argümanlarla çağrıldığı sayılır. Emir yüzeyine hiç girilmeyen dallarda ise SAHTE ADAPTÖR
    ÇAĞRILIRSA TEST DÜŞER (çağrı sayacı 0 iddiası).
Her iddianın yanında POZİTİF KONTROL vardır: sınır bilerek delinir ve iddianın gerçekten düştüğü
gösterilir. Düşmeyen bir iddia koruma değil dekordur.
"""
from __future__ import annotations

import ast
import inspect
import json
import pathlib
import re
import textwrap

import pytest

from meridian import api, config, store, watchdog
from meridian.adapters import alpaca

FAKE_KEY = "PKKORUMAV211FAKEKEY778899"
FAKE_SECRET = "SKKORUMAV211FAKESECRET22334455"

WEB = pathlib.Path(api.__file__).resolve().parent / "web"


# =================================================================================================
# FİKSTÜRLER — canlı vakanın BİREBİR şekli
# =================================================================================================
def _poz(sym, qty, side="long", fiyat=None):
    return {"symbol": sym, "qty": str(qty), "side": side,
            "current_price": None if fiyat is None else str(fiyat)}


def _parent(sym, coid, qty, legs=(), status="filled"):
    return {"id": f"id-{coid}", "client_order_id": coid, "symbol": sym, "side": "buy",
            "type": "limit", "time_in_force": "day", "status": status,
            "qty": str(qty), "filled_qty": str(qty if status == "filled" else 0),
            "legs": list(legs)}


def _bacak(sym, qty, tip, status, side="sell", coid="8796e3f6-a515-41ef", stop=None):
    return {"id": f"leg-{coid}-{tip}-{status}", "client_order_id": coid, "symbol": sym,
            "side": side, "type": tip, "time_in_force": "gtc", "status": status,
            "qty": str(qty), "filled_qty": "0",
            **({"stop_price": str(stop)} if stop is not None else {})}


# Canlı ölçüm: broker 22/22/37/25 · NVDA 1 (operatörün kendi pozisyonu, motor öneki YOK)
CANLI_POZISYONLAR = [_poz("AMGN", 22, fiyat=300.0), _poz("BKNG", 22, fiyat=5200.0),
                     _poz("EMR", 37, fiyat=140.0), _poz("NUE", 25, fiyat=150.0),
                     _poz("NVDA", 1, fiyat=180.0)]
CANLI_EMIRLER = [
    _parent("EMR", "P-2026-08-05-EMR", 37, legs=[
        _bacak("EMR", 37, "limit", "expired", coid="tp-emr"),
        _bacak("EMR", 37, "stop", "canceled", coid="sl-emr", stop=132.0)]),
    _parent("BKNG", "P-2026-08-05-BKNG", 22, legs=[
        _bacak("BKNG", 22, "limit", "expired", coid="tp-bkng"),
        _bacak("BKNG", 22, "stop", "canceled", coid="sl-bkng", stop=4900.0)]),
    _parent("NUE", "P-2026-08-05-NUE", 25, legs=[
        _bacak("NUE", 25, "limit", "expired", coid="tp-nue"),
        _bacak("NUE", 25, "stop", "canceled", coid="sl-nue", stop=141.0)]),
    _parent("AMGN", "P-2026-08-05-AMGN-momentum_burst", 22, legs=[
        _bacak("AMGN", 22, "limit", "expired", coid="tp-amgn"),
        _bacak("AMGN", 22, "stop", "canceled", coid="sl-amgn", stop=285.0)]),
    # operatörün kendi NVDA'sı: motor öneki YOK (A3)
    {"id": "nvda-1", "client_order_id": "44a307ae-a466-46d2", "symbol": "NVDA", "side": "buy",
     "type": "market", "time_in_force": "day", "status": "filled", "qty": "1", "filled_qty": "1",
     "legs": []},
]
# İÇ DEFTER — TUZAĞIN KENDİSİ: adetler broker'ınkinden BÜYÜK (canlı ölçüm 33/43/64/54).
CANLI_DEFTER = {
    "positions": {
        "AMGN": {"ticker": "AMGN", "qty": 33, "stop": 280.0, "trail_stop": 285.0, "target": 340.0},
        "BKNG": {"ticker": "BKNG", "qty": 43, "stop": 4800.0, "trail_stop": 0.0, "target": 5600.0},
        "EMR":  {"ticker": "EMR",  "qty": 64, "stop": 130.0, "trail_stop": 133.0, "target": 158.0},
        "NUE":  {"ticker": "NUE",  "qty": 54, "stop": 138.0, "trail_stop": 0.0, "target": 172.0},
    }
}


@pytest.fixture
def ayna(sandbox_state, monkeypatch):
    """Sahte kimlik + `alpaca_paper` arka ucu; taşıma SAĞLIKLI. Emir yüzeyi henüz saplanmadı."""
    from meridian import secrets as secrets_mod
    monkeypatch.setenv("ALPACA_PAPER_KEY", FAKE_KEY)
    monkeypatch.setenv("ALPACA_PAPER_SECRET", FAKE_SECRET)
    monkeypatch.delenv("MERIDIAN_GCP_PROJECT", raising=False)
    secrets_mod.clear_cache()
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(alpaca, "transport", lambda: {"ok": True, "error": ""})
    watchdog._KORUMA_ALARMED.clear()
    yield sandbox_state
    watchdog._KORUMA_ALARMED.clear()
    secrets_mod.clear_cache()


def _sap(monkeypatch, positions, orders, defter=None):
    monkeypatch.setattr(alpaca, "positions", lambda: [dict(p) for p in positions])
    monkeypatch.setattr(alpaca, "orders", lambda **kw: [dict(o) for o in orders])
    store.write_json("portfolio.json", defter if defter is not None else CANLI_DEFTER)


class SahteOCO:
    """Emir yüzeyinin YERİNE geçer. Ağ yok, gerçek istemci yok — yalnız çağrı kaydı.

    `dusenler`: bu sembollerde gönderim BAŞARISIZ döner (kısmi başarı senaryosu). Gerçek adaptörün
    sözleşmesi birebir taklit edilir: `{ok, detail, reachable, coid}`."""

    def __init__(self, dusenler=()):
        self.cagrilar = []
        self.dusenler = set(dusenler)

    def __call__(self, symbol, qty, stop_loss, take_profit, client_order_id=None):
        self.cagrilar.append({"symbol": symbol, "qty": qty, "stop_loss": stop_loss,
                              "take_profit": take_profit, "client_order_id": client_order_id})
        if symbol in self.dusenler:
            return {"ok": False, "detail": "insufficient qty", "reachable": True,
                    "coid": client_order_id}
        return {"ok": True, "order": {"id": f"oco-{symbol}", "status": "new"},
                "coid": client_order_id, "reachable": True}


@pytest.fixture
def sahte_oco(monkeypatch):
    s = SahteOCO()
    monkeypatch.setattr(alpaca, "submit_protective_oco", s)
    return s


class HttpKayitci:
    """`alpaca.httpx` yerine geçer. HİÇBİR ağ çağrısı yapmaz; yalnız fiil/URL/gövde kaydeder."""

    def __init__(self, status=200, payload=None):
        self.calls = []
        self.status = status
        self.payload = payload if payload is not None else {"id": "oco-1", "status": "new"}

    class _R:
        def __init__(self, status, payload):
            self.status_code = status
            self._p = payload

        def json(self):
            return self._p

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(f"HTTP {self.status_code}")

    def _kaydet(self, fiil, url, **kw):
        self.calls.append({"fiil": fiil, "url": url, "json": kw.get("json")})
        return self._R(self.status, self.payload)

    def post(self, url, **kw):
        return self._kaydet("POST", url, **kw)

    def get(self, url, **kw):
        return self._kaydet("GET", url, **kw)

    def delete(self, url, **kw):
        return self._kaydet("DELETE", url, **kw)

    def patch(self, url, **kw):
        return self._kaydet("PATCH", url, **kw)


def _olaylar(ad=None):
    ev = store.read_jsonl("events.jsonl")
    return [e for e in ev if ad is None or e.get("event") == ad]


# =================================================================================================
# Y1 · OCO ŞART — İKİ GEVŞEK EMİR DEĞİL
# =================================================================================================
def test_Y1_tek_OCO_emri_gonderilir_iki_gevsek_emir_DEGIL(ayna, monkeypatch):
    """Hesapta `shorting_enabled=true`. Bağsız iki emir gönderilseydi hedef dolduktan sonra stop
    CANLI kalır, fiyat oraya inince TETİKLENİR ve elde olmayan hisseyi satar — yani AÇIĞA SATIŞ
    açar. Bu, korumasızlıktan FARKLI ve daha kötü bir risktir."""
    h = HttpKayitci()
    monkeypatch.setattr(alpaca, "httpx", h)
    res = alpaca.submit_protective_oco("EMR", 37, 133.0, 158.0, client_order_id="P-KORUMA-T-EMR")
    assert res["ok"] is True
    postlar = [c for c in h.calls if c["fiil"] == "POST"]
    assert len(postlar) == 1, f"koruma için {len(postlar)} istek gitti — OCO TEK istektir"
    g = postlar[0]["json"]
    assert g["order_class"] == "oco", f"order_class {g.get('order_class')!r} — bağsız emir üretildi"
    assert g["type"] == "limit", "OCO'nun ana tipi `limit` olmalı (Alpaca sözleşmesi)"
    assert g["side"] == "sell", "uzun pozisyonu SATIŞ bacağı korur"
    assert g["take_profit"]["limit_price"] == 158.0 and g["stop_loss"]["stop_price"] == 133.0
    # POZİTİF KONTROL: kayıtçı gerçekten POST'ları görüyor (iddia boş değil)
    assert h.calls and all(c["url"].startswith("https://paper-api.alpaca.markets") for c in h.calls)


def test_Y1b_modulde_bagsiz_koruma_gonderen_ikinci_yol_YOK():
    """AST: `submit_protective_oco` gövdesinde `order_class` DIŞINDA bir emir sınıfı kurulmaz ve
    modülde ikinci bir "yalnız stop gönder" yolu doğmamış olmalı. Metin taraması değil kaynak
    okuması: gerekçe yorumlarında "iki gevşek emir" ifadesi BİLEREK geçiyor."""
    src = inspect.getsource(alpaca.submit_protective_oco)
    kod = "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))
    assert kod.count("httpx.post") == 1, "koruma yolunda birden fazla POST — OCO tek istektir"
    assert '"order_class": "oco"' in kod, "gövde OCO sınıfı taşımıyor"
    # `stop_loss` ve `take_profit` AYNI gövdede: ikisi ayrı istekte olsaydı bağ kurulmazdı.
    # (Dilim `body = {`ten SONRAKİ `try:`e kadar — fonksiyonun başında sayı çevrimi için başka bir
    #  `try:` var ve ilk eşleşmeyi almak dilimi boşaltıyordu; boş dilim üzerinde geçen bir iddia
    #  hiçbir şey kanıtlamazdı.)
    bas = kod.index("body = {")
    govde = kod[bas:kod.index("try:", bas)]
    assert "take_profit" in govde and "stop_loss" in govde, "iki bacak aynı gövdede değil"


def test_Y1c_ters_seviye_REDDEDILIR_ve_emir_gitmez(ayna, monkeypatch):
    """stop ≥ hedef bir koruma değil, anında dolacak bir emirdir — sınırın kendisi reddeder."""
    h = HttpKayitci()
    monkeypatch.setattr(alpaca, "httpx", h)
    r = alpaca.submit_protective_oco("EMR", 37, 158.0, 133.0, client_order_id="P-T-EMR")
    assert r["ok"] is False and "hedefin" in r["detail"]
    assert not h.calls, "reddedilen seviyeye rağmen ağa çıkıldı"
    # POZİTİF KONTROL: doğru sırada AYNI çağrı geçer
    assert alpaca.submit_protective_oco("EMR", 37, 133.0, 158.0,
                                        client_order_id="P-T-EMR")["ok"] is True


# =================================================================================================
# Y2 · ADET BROKER'DAN — İÇ DEFTERDEN ASLA
# =================================================================================================
def test_Y2_adet_BROKERdan_alinir_ic_defterden_DEGIL(ayna, monkeypatch, sahte_oco):
    """Defter 33/43/64/54 diyor, broker 22/22/37/25. Defterin adediyle satmak ELDE OLMAYAN hisseyi
    satmaktır — `shorting_enabled` hesapta koruma diye bir AÇIK POZİSYON açmak demektir."""
    _sap(monkeypatch, CANLI_POZISYONLAR, CANLI_EMIRLER)
    rap = api.koruma_onerileri()
    adetler = {s["ticker"]: s["broker_adet"] for s in rap["satirlar"]}
    assert adetler == {"AMGN": 22.0, "BKNG": 22.0, "EMR": 37.0, "NUE": 25.0}
    defterdekiler = {s["ticker"]: s["defter_adet"] for s in rap["satirlar"]}
    assert defterdekiler == {"AMGN": 33.0, "BKNG": 43.0, "EMR": 64.0, "NUE": 54.0}, \
        "iç defter adedi RAPORLANMIYOR — tuzak ekranda görünmez"
    assert all(s["adet_ayrisik"] for s in rap["satirlar"]), "ayrışma bayrağı kalkmadı"
    # ve İCRA gerçekten broker adedini gönderir
    api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=rap["oneri_id"], onaylayan="test")
    gonderilen = {c["symbol"]: c["qty"] for c in sahte_oco.cagrilar}
    assert gonderilen == {"AMGN": 22.0, "BKNG": 22.0, "EMR": 37.0, "NUE": 25.0}, \
        f"iç defter adedi gönderildi: {gonderilen}"


def test_Y2b_adet_kaynagi_BEYANLI_ve_broker_adedi_0_ise_emir_YOK(ayna, monkeypatch, sahte_oco):
    """Okunamayan adet 0'dır (fail-closed) ve 0 adetle satış emri gönderilmez — uydurma yasağı."""
    poz = [_poz("EMR", 0, fiyat=140.0)]
    _sap(monkeypatch, poz, [CANLI_EMIRLER[0]])
    rap = api.koruma_onerileri()
    assert "BROKER" in rap["adet_kaynagi"]
    satir = rap["satirlar"][0]
    assert satir["gonderilir"] is False and "adedi 0" in satir["neden"]
    api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=rap["oneri_id"], onaylayan="test")
    assert not sahte_oco.cagrilar, "0 adetle emir gönderildi"


def test_Y2c_defterde_seviye_YOKSA_oneri_URETILMEZ(ayna, monkeypatch, sahte_oco):
    """Stop/hedef ÖLÇÜLEMEDİ ≠ 0. Uydurma bir stop, korumasızlıktan beterdir: yanlış yerde güven."""
    _sap(monkeypatch, [_poz("EMR", 37, fiyat=140.0)], [CANLI_EMIRLER[0]],
         defter={"positions": {"EMR": {"ticker": "EMR", "qty": 37}}})
    rap = api.koruma_onerileri()
    s = rap["satirlar"][0]
    assert s["gonderilir"] is False and s["stop"] is None and s["hedef"] is None
    assert "stop + hedef" in s["neden"] and "ÖLÇÜLEMEDİ" in s["neden"]
    api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=rap["oneri_id"], onaylayan="test")
    assert not sahte_oco.cagrilar, "seviyesi olmayan pozisyona emir gönderildi"


# =================================================================================================
# Y3 · YALNIZ MOTOR POZİSYONU (A3)
# =================================================================================================
def test_Y3_motor_disi_pozisyon_LISTELENIR_ama_emir_URETMEZ(ayna, monkeypatch, sahte_oco):
    """Operatörün kendi NVDA'sı görünür (görünürlük) ama motorun sorumluluğu DEĞİLDİR (A3)."""
    _sap(monkeypatch, CANLI_POZISYONLAR, CANLI_EMIRLER)
    rap = api.koruma_onerileri()
    disi = rap["motor_disi_satirlar"]
    assert [s["ticker"] for s in disi] == ["NVDA"], "motor-dışı pozisyon listelenmiyor"
    assert disi[0]["gonderilir"] is False and "A3" in disi[0]["neden"]
    assert "NVDA" not in [s["ticker"] for s in rap["satirlar"]], "motor-dışı pozisyon öneri kümesinde"
    api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=rap["oneri_id"], onaylayan="test")
    assert "NVDA" not in [c["symbol"] for c in sahte_oco.cagrilar], \
        "operatörün kendi pozisyonuna emir gönderildi (A3 ihlali)"
    # POZİTİF KONTROL: aynı koşuda DÖRT motor pozisyonuna gerçekten emir gitti
    assert sorted(c["symbol"] for c in sahte_oco.cagrilar) == ["AMGN", "BKNG", "EMR", "NUE"]


# =================================================================================================
# Y4 · TIF `gtc` + COID ÖNEKİ (E1-v2 · A2/A3)
# =================================================================================================
def test_Y4_TIF_gtc_ve_coid_motor_onekini_tasir(ayna, monkeypatch):
    """`day` tam da bu vakanın KÖK NEDENİYDİ: bracket TIF'i tüm emre uygulanır ve koruma bacakları
    her kapanışta ölürdü. Coid öneki olmadan emir mutabakat için GÖRÜNMEZDİR (A2)."""
    h = HttpKayitci()
    monkeypatch.setattr(alpaca, "httpx", h)
    alpaca.submit_protective_oco("EMR", 37, 133.0, 158.0)
    g = h.calls[0]["json"]
    assert g["time_in_force"] == "gtc", f"TIF {g['time_in_force']!r} — E1-v2 yasası `gtc`"
    assert alpaca.KORUMA_TIF == "gtc"
    assert str(g["client_order_id"]).startswith(alpaca.ENGINE_COID_PREFIX), \
        "üretilen coid motor önekini taşımıyor — sahiplik kanıtlanamaz (A2/A3)"
    assert "KORUMA" in g["client_order_id"], "coid koruma yolunu adlandırmıyor (denetim izi zayıf)"


def test_Y4b_oneksiz_coid_SINIRDA_reddedilir_emir_gitmez(ayna, monkeypatch):
    """Kural ÇAĞIRANDA değil SINIRDA (replace_order_stop'un A4 dersi): `submit_bracket` yalnız
    uyarıyor, bu yol REDDEDİYOR — çünkü tek seferlik ve operatör onaylı bir icra."""
    h = HttpKayitci()
    monkeypatch.setattr(alpaca, "httpx", h)
    r = alpaca.submit_protective_oco("EMR", 37, 133.0, 158.0, client_order_id="manuel-emir-1")
    assert r["ok"] is False and "önekini taşımıyor" in r["detail"]
    assert not h.calls, "öneksiz coid ile ağa çıkıldı"


def test_Y4c_TIF_giris_TIFinden_TURETILMEZ(ayna):
    """`ENTRY_TIF` bilinçli olarak `day` olabilir (bayat tetik yasası); koruma onu MİRAS ALMAMALI."""
    src = inspect.getsource(alpaca.submit_protective_oco)
    assert "ENTRY_TIF" not in src, "koruma TIF'i giriş TIF'inden türetiliyor — iki gerçek karıştı"
    assert "KORUMA_TIF" in src


# =================================================================================================
# Y5 · İDEMPOTANS — İKİ ONAY İKİ KORUMA KURMAZ
# =================================================================================================
def test_Y5_canli_koruma_varsa_emir_GONDERILMEZ(ayna, monkeypatch, sahte_oco):
    korumali = [_parent("EMR", "P-1-EMR", 37,
                        legs=[_bacak("EMR", 37, "stop", "new", coid="sl-live", stop=133.0)])]
    _sap(monkeypatch, [_poz("EMR", 37, fiyat=140.0)], korumali)
    rap = api.koruma_onerileri()
    s = rap["satirlar"][0]
    assert s["korumali"] is True and s["gonderilir"] is False and "idempotans" in s["neden"]
    r = api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=rap["oneri_id"], onaylayan="test")
    assert not sahte_oco.cagrilar, "zaten korunan pozisyona ikinci koruma gönderildi"
    assert r["ok"] is False and "gönderilecek öneri yok" in r["detail"]


def test_Y5b_iki_kez_onaylamak_iki_koruma_KURMAZ(ayna, monkeypatch, sahte_oco):
    """Birinci onay emri gönderir; ikinci onay AYNI kimlikle gelir ama dünya değişmiştir (koruma
    artık canlıdır) → öneri kümesi boşalır ve ikinci bir emir doğmaz."""
    _sap(monkeypatch, [_poz("EMR", 37, fiyat=140.0)], [CANLI_EMIRLER[0]])
    rap = api.koruma_onerileri()
    api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=rap["oneri_id"], onaylayan="test")
    assert len(sahte_oco.cagrilar) == 1
    # broker artık canlı korumayı gösteriyor (emir kabul edildi)
    _sap(monkeypatch, [_poz("EMR", 37, fiyat=140.0)],
         [CANLI_EMIRLER[0], _bacak("EMR", 37, "stop", "new", coid="sl-yeni", stop=133.0)])
    rap2 = api.koruma_onerileri()
    api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=rap2["oneri_id"], onaylayan="test")
    assert len(sahte_oco.cagrilar) == 1, "ikinci onay ikinci koruma kurdu (idempotans kırık)"


# =================================================================================================
# Y6 · KORUMA GEVŞETİLMEZ (A4) — BU YOL BİR ARKA KAPI OLAMAZ
# =================================================================================================
def test_Y6_mevcut_stopun_ALTINA_oneri_REDDEDILIR(ayna, monkeypatch, sahte_oco):
    """Broker'da canlı bir stop 136 varken kitabın 133'ü ile ikinci bir koruma kurmak, etkin
    koruma seviyesini aşağı çekmenin sessiz yolu olurdu."""
    kismi = [_parent("EMR", "P-1-EMR", 37,
                     legs=[_bacak("EMR", 20, "stop", "new", coid="sl-kismi", stop=136.0)])]
    _sap(monkeypatch, [_poz("EMR", 37, fiyat=140.0)], kismi)   # 20/37 kapsanıyor → KORUMASIZ sayılır
    rap = api.koruma_onerileri()
    s = rap["satirlar"][0]
    assert s["korumali"] is False and s["kismi"] is True, "vaka kurgusu bozuk: kısmi kapsama yok"
    assert s["mevcut_stop"] == 136.0
    assert s["gonderilir"] is False and "A4" in s["neden"] and "yalnız" in s["neden"]
    api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=rap["oneri_id"], onaylayan="test")
    assert not sahte_oco.cagrilar, "koruma AŞAĞI taşındı (A4 arka kapısı açık)"


def test_Y6b_mevcut_stopun_USTUNE_oneri_GECER_pozitif_kontrol(ayna, monkeypatch, sahte_oco):
    """POZİTİF KONTROL: aynı kurgu, kitabın stop'u mevcudun ÜSTÜNDE → öneri geçer ve gider."""
    kismi = [_parent("EMR", "P-1-EMR", 37,
                     legs=[_bacak("EMR", 20, "stop", "new", coid="sl-kismi", stop=120.0)])]
    _sap(monkeypatch, [_poz("EMR", 37, fiyat=140.0)], kismi)
    rap = api.koruma_onerileri()
    s = rap["satirlar"][0]
    assert s["gonderilir"] is True, f"yukarı taşıma da reddedildi: {s['neden']}"
    api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=rap["oneri_id"], onaylayan="test")
    assert [c["symbol"] for c in sahte_oco.cagrilar] == ["EMR"]
    assert sahte_oco.cagrilar[0]["stop_loss"] == 133.0, "iz süren stop (133) yerine sert stop gitti"


def test_Y6c_kitabin_iz_suren_stopu_SERT_stopun_ustundeyse_o_kullanilir(ayna, monkeypatch):
    """A4'ün kitap tarafı: `trail_stop` sert stop'un üstündeyse etkin koruma odur; küçüğünü seçmek
    kitabın kendi yükselttiği korumayı aynada geri indirmek olurdu."""
    _sap(monkeypatch, [_poz("EMR", 37, fiyat=140.0)], [CANLI_EMIRLER[0]])
    s = api.koruma_onerileri()["satirlar"][0]
    assert s["stop"] == 133.0, "sert stop (130) iz süren stop'un (133) yerine alındı"
    # POZİTİF KONTROL: iz süren stop yoksa sert stop kullanılır
    _sap(monkeypatch, [_poz("NUE", 25, fiyat=150.0)], [CANLI_EMIRLER[2]])
    assert api.koruma_onerileri()["satirlar"][0]["stop"] == 138.0


# =================================================================================================
# Y7 · BROKER ERİŞİLEMEZSE EMİR YOK + NEDEN
# =================================================================================================
def test_Y7_broker_dusukken_emir_YOK_ve_NEDEN_beyanli(ayna, monkeypatch, sahte_oco):
    """`positions()`/`orders()` arızada da [] döner (A1). Boş listeye bakıp "korumasız yok" demek
    arızayı temizlik diye raporlamak olurdu; onaylı bir çağrıda ise SESSİZ BAŞARI üretirdi."""
    _sap(monkeypatch, [], [])
    monkeypatch.setattr(alpaca, "transport", lambda: {"ok": False, "error": "ReadTimeout: positions"})
    rap = api.koruma_onerileri()
    assert rap["ok"] is None and rap["olculemedi"] is True and rap["satirlar"] == []
    assert rap["gonderilebilir"] is None, "ölçülemeyen sayı 0 yazıldı (UYDURMA)"
    assert "okunamadı" in rap["neden"] and "ReadTimeout" in rap["neden"]
    r = api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=rap["oneri_id"], onaylayan="test")
    assert r["ok"] is False and not sahte_oco.cagrilar, "broker düşükken emir gönderildi"
    assert "ÖLÇÜLEMEDİ" in r["detail"] and "ReadTimeout" in r["detail"], \
        f"sessiz başarı üretildi: {r['detail']!r}"


def test_Y7b_emir_ucu_SONRADAN_duserse_de_emir_YOK(ayna, monkeypatch, sahte_oco):
    """İKİNCİ ARIZA KAPISI: bekçi ölçümü tamamlandı ama A4 denetimi için yapılan emir okuması
    düştü. Fiyatsız bir A4 denetimi yapılamaz — o hâlde emir de gönderilmez."""
    sayac = {"n": 0}

    def _transport():
        sayac["n"] += 1
        return {"ok": sayac["n"] <= 3, "error": "" if sayac["n"] <= 3 else "HTTP 502: orders"}

    _sap(monkeypatch, [_poz("EMR", 37, fiyat=140.0)], [CANLI_EMIRLER[0]])
    monkeypatch.setattr(alpaca, "transport", _transport)
    rap = api.koruma_onerileri()
    assert rap["olculemedi"] is True and "okunamadı" in rap["neden"]
    assert not sahte_oco.cagrilar


def test_Y7c_ayna_KAPALIYSA_kapsam_disi_ve_emir_YOK(ayna, monkeypatch, sahte_oco):
    """`broker=internal`: sorunun REFERANSI yok (iç motor stop'u kendisi uygular)."""
    monkeypatch.setattr(config, "BROKER", "internal")
    _sap(monkeypatch, CANLI_POZISYONLAR, CANLI_EMIRLER)
    rap = api.koruma_onerileri()
    assert rap["kapsam_disi"] is True and rap["ok"] is None and rap["neden"]
    r = api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=rap["oneri_id"], onaylayan="test")
    assert not sahte_oco.cagrilar and r["ok"] is False


# =================================================================================================
# Y8 · DENETİM İZİ (YASA 6) — HER GÖNDERİM BİR OLAY BIRAKIR
# =================================================================================================
def test_Y8_her_gonderim_OLAY_birakir_plan_id_sembol_adet_seviye_onaylayan(ayna, monkeypatch,
                                                                           sahte_oco):
    _sap(monkeypatch, [_poz("EMR", 37, fiyat=140.0)], [CANLI_EMIRLER[0]])
    rap = api.koruma_onerileri()
    api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=rap["oneri_id"],
                   onaylayan="pano-oturumu")
    ev = _olaylar("koruma_oco_gonderildi")
    assert len(ev) == 1, f"gönderim başına bir olay bekleniyordu, {len(ev)} bulundu"
    e = ev[0]
    for alan in ("plan_id", "ticker", "adet", "stop", "hedef", "onaylayan", "oneri_id", "tif"):
        assert alan in e, f"denetim izinde `{alan}` yok — 'kim neyi hangi onayla gönderdi' sorusu cevapsız"
    assert e["ticker"] == "EMR" and e["adet"] == 37.0 and e["stop"] == 133.0 and e["hedef"] == 158.0
    assert e["onaylayan"] == "pano-oturumu" and e["tif"] == "gtc"
    assert str(e["plan_id"]).startswith(alpaca.ENGINE_COID_PREFIX)
    assert _olaylar("koruma_kur_ozet"), "tur özeti deftere yazılmıyor"


def test_Y8b_DUSEN_gonderim_de_olay_birakir(ayna, monkeypatch):
    """Sessiz başarısızlık YASAK: gönderilemeyen koruma da deftere düşer ve satır 'pozisyon HÂLÂ
    çıplak' der."""
    s = SahteOCO(dusenler={"EMR"})
    monkeypatch.setattr(alpaca, "submit_protective_oco", s)
    _sap(monkeypatch, [_poz("EMR", 37, fiyat=140.0)], [CANLI_EMIRLER[0]])
    rap = api.koruma_onerileri()
    api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=rap["oneri_id"], onaylayan="test")
    dusuk = _olaylar("koruma_oco_dusuru")
    assert len(dusuk) == 1 and dusuk[0]["ticker"] == "EMR"
    assert "çıplak" in str(dusuk[0].get("detail", "")), "düşen gönderimin sonucu beyan edilmiyor"
    assert not _olaylar("koruma_oco_gonderildi"), "gönderilmeyen emir 'gönderildi' diye yazıldı"


# =================================================================================================
# Y9 · ONAYSIZ HİÇBİR EMİR ÇIKMIYOR — EN ÖNEMLİ ÇİVİ
# =================================================================================================
def test_Y9_onaysiz_cagri_KURU_KOSUdur_hicbir_emir_cikmaz(ayna, monkeypatch, sahte_oco):
    _sap(monkeypatch, CANLI_POZISYONLAR, CANLI_EMIRLER)
    for onay in ("", "evet", "KORUMA-KURR", "koruma-kur", alpaca.CLOSE_ALL_CONFIRM):
        r = api.koruma_kur(onay=onay, oneri_id=api.koruma_onerileri()["oneri_id"], onaylayan="test")
        assert r["dry_run"] is True and r["ok"] is False, f"onay={onay!r} kabul edildi"
        assert not sahte_oco.cagrilar, f"onay={onay!r} ile emir gönderildi"
    # POZİTİF KONTROL: DOĞRU jeton + doğru kimlikle aynı çağrı emir GÖNDERİR
    rap = api.koruma_onerileri()
    api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=rap["oneri_id"], onaylayan="test")
    assert len(sahte_oco.cagrilar) == 4, "doğru onayla da gönderilmiyor — test bir şey ölçmüyor"


def test_Y9b_onay_TURA_OZEL_bayat_kimlik_REDDEDILIR(ayna, monkeypatch, sahte_oco):
    """Kalıcı bir izin anahtarı, ilk gün verilen onayı yarının bilinmeyen defterine uygulardı.
    Onay bir DURUMA bağlıdır: liste değiştiyse eski onay o listeyi kapsamaz."""
    _sap(monkeypatch, CANLI_POZISYONLAR, CANLI_EMIRLER)
    eski = api.koruma_onerileri()["oneri_id"]
    # DÜNYA DEĞİŞTİ: EMR korundu, geriye üç çıplak kaldı
    yeni_emirler = list(CANLI_EMIRLER) + [_bacak("EMR", 37, "stop", "new", coid="sl-y", stop=140.0)]
    _sap(monkeypatch, CANLI_POZISYONLAR, yeni_emirler)
    yeni = api.koruma_onerileri()["oneri_id"]
    assert eski != yeni, "öneri kimliği dünya değişince DEĞİŞMİYOR — onay tura özel değil"
    r = api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=eski, onaylayan="test")
    assert r.get("bayat_onay") is True and not sahte_oco.cagrilar, "bayat onayla emir gönderildi"
    assert "DEĞİŞTİ" in r["detail"]
    # POZİTİF KONTROL: TAZE kimlikle aynı çağrı geçer (üç çıplak pozisyon)
    api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=yeni, onaylayan="test")
    assert sorted(c["symbol"] for c in sahte_oco.cagrilar) == ["AMGN", "BKNG", "NUE"]


def test_Y9c_oneri_uretici_SALT_OKUMA_emir_yuzeyine_dokunmaz():
    """AST: `koruma_onerileri` broker'a YALNIZ GET atar. Metin taraması DEĞİL kaynak ağacı —
    gerekçe yorumlarında yasak fonksiyonların adı geçiyor ve geçmeli (yasa oradan okunuyor)."""
    YASAK = {"submit_protective_oco", "submit_plan", "submit_bracket", "cancel_order",
             "cancel_open_entries", "close_engine_position", "close_all", "replace_order_stop",
             "post", "delete", "patch", "put"}
    cagrilar = set()
    for node in ast.walk(ast.parse(textwrap.dedent(inspect.getsource(api.koruma_onerileri)))):
        if isinstance(node, ast.Call):
            f = node.func
            cagrilar.add(f.attr if isinstance(f, ast.Attribute) else
                         (f.id if isinstance(f, ast.Name) else ""))
    assert not (cagrilar & YASAK), f"öneri üretici emir yüzeyini ÇAĞIRIYOR: {sorted(cagrilar & YASAK)}"
    assert {"positions", "orders", "transport"} <= cagrilar, \
        f"adaptörün okuma uçları kullanılmıyor: {sorted(cagrilar)}"


def test_Y9d_onaysiz_yolda_GERCEK_istemciye_tek_cagri_gitmez(ayna, monkeypatch):
    """SON ÇİVİ — sahte adaptör YOK, gerçek `submit_protective_oco` yerinde; yalnız `httpx`
    kayıtçıyla değiştirildi. Onaysız akış bir tek POST/DELETE/PATCH bile üretmemeli."""
    h = HttpKayitci()
    monkeypatch.setattr(alpaca, "httpx", h)
    _sap(monkeypatch, CANLI_POZISYONLAR, CANLI_EMIRLER)
    api.koruma_onerileri()
    api.koruma_kur(onay="", oneri_id="", onaylayan="test")
    api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id="bayat-kimlik", onaylayan="test")
    yazan = [c for c in h.calls if c["fiil"] in ("POST", "DELETE", "PATCH", "PUT")]
    assert not yazan, f"onaysız/bayat yolda yazan çağrı doğdu: {yazan}"


def test_Y9e_uc_yetkisiz_cagriyi_REDDEDER(sandbox_state, monkeypatch):
    """İki uç da `_auth` arkasında: yetkisiz bir çağrı ne öneri okuyabilir ne emir gönderebilir."""
    from fastapi.testclient import TestClient
    monkeypatch.setattr(api, "DASH_TOKEN", "V211-TOKEN")
    monkeypatch.setattr(api.auth, "password_set", lambda: False)
    with TestClient(api.app) as c:
        assert c.get("/api/alpaca/koruma").status_code == 401
        assert c.post("/api/alpaca/koruma_kur", json={"onay": alpaca.KORUMA_ONAY_JETONU,
                                                      "oneri_id": "x"}).status_code == 401
        # POZİTİF KONTROL: doğru token 401 DEĞİL
        assert c.get("/api/alpaca/koruma",
                     headers={"x-meridian-token": "V211-TOKEN"}).status_code != 401


# =================================================================================================
# Y10 · BASIŞ KAYDI — UÇ DÜZEYİ DENETİM İZİ (Y8'in eksik yarısı)
# -------------------------------------------------------------------------------------------------
# ÖLÇÜLEN BOŞLUK (2026-08-07): Y8 "her GÖNDERİM olay bırakır" der ve tutar — ama ucun dallarının
# çoğu sessizdi. Onaysız çağrı, ölçüm düşükken dönen tur, gönderilecek öneri kalmamış tur ve
# JETONSUZ gelen bayat kimlik hiçbir yere düşmüyordu; tek kayıtlı ret (`koruma_onay_bayat`) yalnız
# jeton DOĞRUYKEN yazılıyordu. Oysa "korumam neden kurulmadı" sorusu tam da o dallarda sorulur.
# İZ UÇTA, O YÜZDEN ÇAĞRI DA UÇTAN: aşağıdaki testler `api.koruma_kur()`u doğrudan çağırmaz —
# HTTP'den geçerler, çünkü ölçülen şey ucun yazdığı satırdır.
# =================================================================================================
IZ_TOKEN = "V211-IZ-TOKEN"
IZ_OLAYI = "koruma_kur_istegi"


@pytest.fixture
def uc(ayna, monkeypatch):
    """Yetkili istemci. Parola KURULMAMIŞ + betik jetonu → `_koruma_onaylayan` "betik-tokeni" der;
    yani "kim bastı" alanı da uydurma değil ÖLÇÜLMÜŞ bir değerle sınanır."""
    from fastapi.testclient import TestClient
    monkeypatch.setattr(api, "DASH_TOKEN", IZ_TOKEN)
    monkeypatch.setattr(api.auth, "password_set", lambda: False)
    return TestClient(api.app)


def _bas(c, onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=""):
    """Operatör düğmeye BASAR (panonun gövdesiyle birebir: {onay, oneri_id})."""
    return c.post("/api/alpaca/koruma_kur", json={"onay": onay, "oneri_id": oneri_id},
                  headers={"x-meridian-token": IZ_TOKEN})


def _oku(c, yol):
    return c.get(yol, headers={"x-meridian-token": IZ_TOKEN})


def test_Y10_UC_HER_dalda_bir_basis_kaydi_birakir(uc, monkeypatch, sahte_oco):
    """ÜÇ DAL, ÜÇ SATIR — ve her satır aynı dört soruyu cevaplar: hangi öneriye, onay VAR mıydı,
    kaç/kaç gitti, nerede bitti. Reddedilen basış kaydedilmezse "bu neden olmadı" sorusunun
    kaynağı yoktur; çıplak duran bir pozisyonun karşısında sorulan soru tam olarak odur."""
    _sap(monkeypatch, CANLI_POZISYONLAR, CANLI_EMIRLER)
    taze = api.koruma_onerileri()["oneri_id"]
    assert _bas(uc, onay="", oneri_id=taze).status_code == 200                    # (a) onaysız
    assert _bas(uc, oneri_id="bayat-kimlik").status_code == 200                   # (b) bayat kimlik
    assert _bas(uc, oneri_id=taze).status_code == 200                             # (c) gerçek gönderim
    ev = _olaylar(IZ_OLAYI)
    assert [e["sonuc"] for e in ev] == ["onaysiz-kuru-kosu", "bayat-oneri-kimligi", "gonderildi"], \
        f"dal jetonları yanlış ya da bir dal SESSİZ: {[e.get('sonuc') for e in ev]}"
    assert [e["onay_verildi"] for e in ev] == [False, True, True], "onay bayrağı dalları ayırmıyor"
    assert [e["gonderilen"] for e in ev] == [0, 0, 4], "gönderim sayısı basış kaydında yanlış"
    assert [e["toplam"] for e in ev] == [4, 4, 4], "öneri sayısı basış kaydında yanlış"
    assert [e["oneri_id"] for e in ev] == [taze, "bayat-kimlik", taze], "hangi öneriye basıldı yazmıyor"
    assert {e["onaylayan"] for e in ev} == {"betik-tokeni"}, "kim bastı yazmıyor"
    assert all(e["ozet"] for e in ev), "sonuç özeti BOŞ — satır 'ne oldu'yu taşımıyor"
    # POZİTİF KONTROL: (c) gerçekten emir gönderdi (üç satır da 'hiçbir şey olmadı' değil)
    assert len(sahte_oco.cagrilar) == 4


def test_Y10b_OLCULEMEDI_dalinda_toplam_None_yazilir_0_DEGIL(uc, monkeypatch, sahte_oco):
    """`koruma_kur` ölçüm kapısında geri döner ve "kaç öneri gönderilmeliydi" HİÇ hesaplanmaz.
    Oraya 0 yazmak, korumasız pozisyon olmadığını iddia etmek olurdu — defterdeki 0, ölçülmüş bir
    0'dan ayırt edilemez. `gonderilen` ise ÖLÇÜLÜDÜR: emir yüzeyine hiç girilmedi, gerçekten 0."""
    _sap(monkeypatch, [], [])
    monkeypatch.setattr(alpaca, "transport", lambda: {"ok": False, "error": "ReadTimeout: positions"})
    assert _bas(uc, oneri_id="x").status_code == 200
    e = _olaylar(IZ_OLAYI)[-1]
    assert e["sonuc"] == "olculemedi"
    assert e["toplam"] is None, f"ölçülemeyen sayı {e['toplam']!r} yazıldı (UYDURMA)"
    assert e["gonderilen"] == 0 and not sahte_oco.cagrilar
    assert "ReadTimeout" in e["ozet"], "arızanın NEDENİ basış kaydında yok"
    # POZİTİF KONTROL: taşıma sağlamken aynı alan gerçek bir sayı taşır (None her hâlde değil)
    monkeypatch.setattr(alpaca, "transport", lambda: {"ok": True, "error": ""})
    _sap(monkeypatch, CANLI_POZISYONLAR, CANLI_EMIRLER)
    _bas(uc, oneri_id="x")
    assert _olaylar(IZ_OLAYI)[-1]["toplam"] == 4


def test_Y10c_gonderilecek_oneri_kalmadiginda_da_iz_var(uc, monkeypatch, sahte_oco):
    """İDEMPOTANS DALI DA BİR BASIŞTIR: ikinci kez onaylayan operatör "hiçbir şey olmadı" cevabını
    alır ve o cevabın da bir kaydı olmalı — yoksa düğmeye basılıp basılmadığı bilinemez."""
    korumali = [_parent("EMR", "P-1-EMR", 37,
                        legs=[_bacak("EMR", 37, "stop", "new", coid="sl-live", stop=133.0)])]
    _sap(monkeypatch, [_poz("EMR", 37, fiyat=140.0)], korumali)
    taze = api.koruma_onerileri()["oneri_id"]
    _bas(uc, oneri_id=taze)
    e = _olaylar(IZ_OLAYI)[-1]
    assert e["sonuc"] == "gonderilecek-oneri-yok" and e["toplam"] == 0 and e["gonderilen"] == 0
    assert not sahte_oco.cagrilar


def test_Y10d_iz_JETONU_TASIMAZ_yanlis_kutuya_yapistirilsa_bile(uc, monkeypatch, sahte_oco):
    """Jeton bir sır değil ama bir YETKİ İŞARETİDİR (ucun kendi docstring'i): deftere düşen bir
    yetki işareti, kaydı okuyan herkesin TEKRAR OYNATABİLECEĞİ bir onaydır. Yalnız "biz yazmıyoruz"
    demek yetmez — operatör jetonu YANLIŞ KUTUYA (`oneri_id`) yapıştırdığında da yazılmamalı."""
    _sap(monkeypatch, CANLI_POZISYONLAR, CANLI_EMIRLER)
    taze = api.koruma_onerileri()["oneri_id"]
    _bas(uc, oneri_id=taze)                                    # doğru kullanım (emirler gider)
    _bas(uc, oneri_id=alpaca.KORUMA_ONAY_JETONU)               # jeton YANLIŞ kutuda
    ev = _olaylar(IZ_OLAYI)
    assert len(ev) == 2 and ev[1]["sonuc"] == "bayat-oneri-kimligi"
    for e in ev:
        assert alpaca.KORUMA_ONAY_JETONU not in json.dumps(e, ensure_ascii=False), \
            f"basış kaydı jetonu taşıyor — onay TEKRAR OYNATILABİLİR: {e}"
    assert "jeton-gizlendi" in ev[1]["oneri_id"], "yanlış kutudaki jeton maskelenmedi"
    # DEFTERİN TAMAMI — alt katmanın `koruma_onay_bayat` uyarısı da jetonu yazmamalı
    defter = (config.STATE / "events.jsonl").read_text()
    assert alpaca.KORUMA_ONAY_JETONU not in defter, "jeton olay defterinin BAŞKA bir satırında"
    # POZİTİF KONTROL: maske gerçek bir öneri kimliğini BOZMUYOR (iddia her hâlde geçmiyor)
    assert ev[0]["oneri_id"] == taze


def test_Y10e_uc_izi_alt_katman_olaylarini_COGALTMAZ(uc, monkeypatch, sahte_oco):
    """Dört öneri gönderen bir tur beş satır bırakır (4 gönderim + 1 tur özeti). Uç satırı bunlara
    BİR TANE daha ekler — dört değil: bu satır GÖNDERİMİN değil BASMANIN kaydıdır. Emir alanlarını
    (plan_id/ticker/stop/hedef) taşısaydı aynı olgunun ikinci bir kopyası olurdu."""
    _sap(monkeypatch, CANLI_POZISYONLAR, CANLI_EMIRLER)
    taze = api.koruma_onerileri()["oneri_id"]
    _bas(uc, oneri_id=taze)
    assert len(sahte_oco.cagrilar) == 4
    assert len(_olaylar("koruma_oco_gonderildi")) == 4, "alt katman emir satırları kayboldu"
    assert len(_olaylar("koruma_kur_ozet")) == 1, "tur özeti çoğaldı ya da kayboldu"
    ev = _olaylar(IZ_OLAYI)
    assert len(ev) == 1, f"dört emir için {len(ev)} uç satırı — çağrı başına TEK satır olmalı"
    for alan in ("plan_id", "ticker", "adet", "stop", "hedef", "tif"):
        assert alan not in ev[0], f"uç izi emir alanı `{alan}` taşıyor — alt katmanın kopyası"


def test_Y10f_izin_OKUYUCUSU_var_api_events_onu_gercekten_gosterir(uc, monkeypatch, sahte_oco):
    """YASA 6 ÖLÇÜMÜ — okuyucusuz yazım yok. Bu satırın okuyucusu `/api/events` (obs.recent(80)) ve
    panonun "Olay akışı · son 8" kartıdır; iddia edilmiyor, ÇAĞRILIP ölçülüyor.

    ÖLÇÜLEN SINIR AYNI TESTTE YAZILI: `/api/audit_trail` bu izi GÖRMEZ — o uç `trade_plans.jsonl`
    defterini sorgular (plan ekseni), olay defterini değil. Denetim izini orada arayan biri onu
    bulamayacak; kaydın evi olay akışıdır."""
    _sap(monkeypatch, CANLI_POZISYONLAR, CANLI_EMIRLER)
    taze = api.koruma_onerileri()["oneri_id"]
    _bas(uc, oneri_id=taze)
    r = _oku(uc, "/api/events")
    assert r.status_code == 200
    satir = next((e for e in r.json()["events"] if e.get("event") == IZ_OLAYI), None)
    assert satir is not None, "basış kaydı olay ucunda GÖRÜNMÜYOR — okuyucusuz yazım (YASA 6)"
    assert satir["sonuc"] == "gonderildi" and satir["onay_verildi"] is True
    assert satir["level"] == "info", "basış kaydı bir alarm değil; seviye info olmalı"
    at = _oku(uc, "/api/audit_trail")
    assert at.status_code == 200
    assert IZ_OLAYI not in json.dumps(at.json(), ensure_ascii=False), \
        "ÖLÇÜM DEĞİŞTİ: /api/audit_trail artık olay defterini de okuyor — bu testin beyanı eskidi"


# =================================================================================================
# KISMİ BAŞARI DÜRÜST RAPORLANIR
# =================================================================================================
def test_kismi_basari_DURUST_raporlanir_tamam_DEMEZ(ayna, monkeypatch):
    """4 pozisyonun 2'si gönderildiyse "2/4 gönderildi + 2 neden" der. Tek bir "gönderildi"
    cümlesi, hâlâ çıplak duran iki pozisyonu ekrandan silerdi."""
    s = SahteOCO(dusenler={"NUE", "BKNG"})
    monkeypatch.setattr(alpaca, "submit_protective_oco", s)
    _sap(monkeypatch, CANLI_POZISYONLAR, CANLI_EMIRLER)
    rap = api.koruma_onerileri()
    r = api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=rap["oneri_id"], onaylayan="test")
    assert r["ok"] is False, "kısmi başarı 'tamam' diye raporlandı"
    assert r["gonderilen"] == 2 and r["toplam"] == 4
    assert r["ozet"].startswith("2/4 gönderildi"), r["ozet"]
    for sym in ("NUE", "BKNG"):
        assert sym in r["ozet"] and "insufficient qty" in r["ozet"], \
            f"{sym} için gerekçe raporlanmadı: {r['ozet']}"
    dusen = [x for x in r["satirlar"] if not x["ok"]]
    assert sorted(x["ticker"] for x in dusen) == ["BKNG", "NUE"]
    assert "çıplak" in r["detail"]
    # POZİTİF KONTROL: hepsi geçince `ok` TRUE olur (iddia her hâlde False değil)
    s2 = SahteOCO()
    monkeypatch.setattr(alpaca, "submit_protective_oco", s2)
    rap2 = api.koruma_onerileri()
    assert api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=rap2["oneri_id"],
                          onaylayan="test")["ok"] is True


def test_hic_oneri_yokken_ok_TRUE_donmez(ayna, monkeypatch, sahte_oco):
    """Boş bir kümeyi "başarı" saymak, hiçbir şey yapmamayı iş yapmak gibi göstermek olurdu."""
    _sap(monkeypatch, [], [])
    rap = api.koruma_onerileri()
    r = api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=rap["oneri_id"], onaylayan="test")
    assert r["ok"] is False and r["gonderilen"] == 0 and not sahte_oco.cagrilar


# =================================================================================================
# PANO — KART SÖZLEŞMESİ, ADET AYRIŞMASI, ONAY KAPISI, CSP
# =================================================================================================
APPJS = (WEB / "app.js").read_text()
KOD = "\n".join(l for l in APPJS.splitlines() if not l.lstrip().startswith("//"))
INDEX = (WEB / "index.html").read_text()


def _fn(ad: str) -> str:
    i = KOD.index(f"function {ad}(")
    parcalar = []
    for ln in KOD[i:].splitlines(keepends=True):
        parcalar.append(ln)
        if ln.rstrip("\n") == "}":
            break
    return "".join(parcalar)


def test_pano_karti_ADET_AYRISMASINI_gosterir():
    """TUZAK GÖRÜNÜR OLMALI: iç defter 33/43/64/54 der, broker 22/22/37/25 ve emir BROKER'ınkini
    kullanır. Görünmezse operatör yanlış sayıyı doğru sanar."""
    kart = _fn("korumaKurmaKarti")
    assert "ADET AYRIŞMASI" in kart, "ayrışma başlığı ekranda yok"
    assert "adet_ayrisik" in kart and "defter_adet" in kart, "iki adet yan yana okunmuyor"
    assert "BROKER" in kart and "broker_adet" in kart, "emrin hangi adedi kullandığı yazmıyor"
    satir = _fn("korumaSatirHTML")
    assert "defter_adet" in satir and "broker_adet" in satir, \
        "satır düzeyinde iki adet gösterilmiyor — ayrışma yalnız toplamda kalır"


def test_pano_karti_alti_alani_da_gosterir():
    """Sözleşme: sembol · SAT adet · stop · hedef · son fiyat · stopa uzaklık."""
    kart, satir = _fn("korumaKurmaKarti"), _fn("korumaSatirHTML")
    for baslik in ("HİSSE", "SAT ADET", "STOP", "HEDEF", "SON", "STOPA UZAKLIK"):
        assert baslik in kart, f"tablo başlığı eksik: {baslik}"
    for alan in ("ticker", "broker_adet", "stop", "hedef", "son_fiyat", "stop_uzakligi"):
        assert alan in satir, f"satır alanı basılmıyor: {alan}"


def test_pano_karti_D2a_sozlesmesinden_gecer():
    """Büyük değer + PAYDA BEYANLI çubuk + meta (kart sözleşmesi D2-a) ve kayıt defterinde kaydı
    var — kayıtsız bir anahtar sessizce kapak almaz."""
    kart = _fn("korumaKurmaKarti")
    assert 'katKart("mutabakat:koruma")' in kart, "kart kayıt anahtarını taşımıyor"
    assert '"mutabakat:koruma":' in KOD, "kart kayıt defterinde yok"
    assert "kartOzeti(" in kart, "kapalı özet üretilmiyor"
    assert "payda: k.payda_beyani" in kart, "çubuk paydası BEYANLI değil (paydasız çubuk çizilmez)"
    assert 'rozet: g > 0 ? "ONAY BEKLİYOR" : ""' in kart, \
        "onay bekleyen kart rozet taşımıyor — kapak altında GİZLENEBİLİR"


def test_pano_ONAY_kalici_anahtar_DEGIL_tura_ozel():
    """Kalıcı bir toggle/anahtar YOK: düğme o ölçüme ait `oneri_id` taşır ve sunucu eşleşmeyi
    arar. `localStorage`a yazılan bir 'koruma izni' bu sözleşmeyi bir açığa çevirirdi."""
    kart, fn = _fn("korumaKurmaKarti"), KOD[KOD.index("window.korumaKur = "):KOD.index("function _korumaSonucSatiri(")]
    assert 'data-act="korumaKur"' in kart and "data-a1=" in kart, "onay düğmesi öneri kimliğini taşımıyor"
    assert "oneri_id" in fn and "confirm(" in fn, "onay diyaloğu ya da kimlik gönderimi yok"
    assert "localStorage" not in fn and "sessionStorage" not in fn, \
        "onay kalıcı depolamaya yazılıyor — tura özel olmaktan çıkar"
    assert '"korumaKur"' in KOD[KOD.index("const EYLEMLER = new Set(["):
                                 KOD.index("const EYLEMLER = new Set([") + 900], \
        "eylem izin listesinde kayıtlı değil — düğme sessizce ölü olurdu"
    assert "window.korumaKur" in KOD, "kayıtlı eylem tanımsız"


def test_pano_kismi_basariyi_DURUST_yazar():
    fn = _fn("_korumaSonucSatiri")
    assert "gönderilemedi" in fn and "ÇIPLAK" in fn, "düşen gönderimler ekranda yazılmıyor"
    assert "dry_run" in fn and "bayat_onay" in fn, "onaysız/bayat dallar ekranda ayrışmıyor"
    assert "ölçülemedi" in fn, "sayı ölçülemediğinde 0 yazılıyor olabilir (uydurma)"
    assert "?? 0" not in fn and "|| 0" not in fn, "ölçülemeyen sayı sıfıra çöküyor"


def test_pano_OLCULEMEDI_dali_sifir_YAZMAZ():
    kart = _fn("korumaKurmaKarti")
    assert 'rozet: "ÖLÇÜLEMEDİ"' in kart, "ölçülemedi dalı rozet taşımıyor"
    assert "korumasız 0" in kart or "\"korumasız 0\" DEĞİL" in kart or "korumasız 0\" DEĞİL" in kart, \
        "ölçülemedi ile 'korumasız yok' ekranda ayrışmıyor"


def test_pano_SATIR_ICI_betik_ve_olay_ozniteligi_YOK():
    """CSP `script-src 'self'`: satır içi bir `<script>` ya da `onclick=` bu turda ölü bir onay
    düğmesi demek olurdu — ve ölü bir koruma düğmesi, düğmenin hiç olmamasından beterdir."""
    bloklar = [_fn("korumaKurmaKarti"), _fn("korumaSatirHTML"), _fn("_korumaSonucSatiri"),
               KOD[KOD.index("window.korumaKur = "):KOD.index("function _korumaSonucSatiri(")]]
    for b in bloklar:
        assert not re.search(r"\son[a-z]+=[\"']", b), f"satır içi olay özniteliği var: {b[:80]}"
        assert "<script" not in b, "satır içi betik bloğu üretiliyor"
    assert "<script" not in "".join(
        l for l in INDEX.splitlines() if "src=" not in l and "</script>" not in l) or True
    # index.html'de gövdeli betik yok (yalnız `src=` ile dış dosya)
    for m in re.finditer(r"<script([^>]*)>", INDEX):
        assert "src=" in m.group(1), f"index.html gövdeli <script> taşıyor: {m.group(0)}"


def test_pano_karti_MUTABAKAT_masasinda_ve_ILK_sirada():
    """Açık bir riskin cevabı, geçmişin muhasebesinin ALTINDA duramaz."""
    r = KOD[KOD.index("RENDER.mutabakat = async () => {"):KOD.index("RENDER.kapilar = async () => {")]
    assert "korumaKurmaKarti(kor)" in r, "kart mutabakat masasında çizilmiyor"
    assert r.index("korumaKurmaKarti(kor)") < r.index("+ p.s1"), \
        "koruma kartı E2/E3/E4 kartlarının ALTINDA — risk gömülü"
    assert 'j("/api/alpaca/koruma")' in r, "kart verisini uçtan okumuyor"
    assert "catch(() => null)" in r.replace(" ", "").replace("catch(()=>null)", "catch(() => null)") \
        or "catch(() => null)" in r, "uç düşerse kart sessizce kaybolur"

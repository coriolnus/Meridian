"""test_koruma_kadans_carpismasi_v220.py — KADANS KORUMAYI ÖLDÜREMEZ (yön kemeri + aile kemeri).

VAKA (canlı A1, 2026-08-07): operatör 16:23'te panodan dört koruma OCO'su kurdu
(`P-KORUMA-20260807-1623-{AMGN,BKNG,EMR,NUE}`, tif=gtc, olay `koruma_oco_gonderildi`). AYNI GÜN
20:32:39-40'ta dördü de `canceled` oldu; olay defterinde tek satır vardı:
`mirror_stale_entries_cancelled · gate:"gunluk_kadans" · cancelled:4, kept:0, foreign:0` — ve o
satırın kendi metni "Koruma bacakları YAŞAR (dolmuş parent `kept` altında)" diyordu. `kept:0` bunun
yanlış olduğunu kanıtladı.

KÖK NEDEN (ölçüldü, varsayılmadı): `alpaca.cancel_open_entries()` sahipliği `P-` önekiyle,
terminalliği emrin KENDİ `filled_qty`siyle ölçüyordu. Bağımsız koruma OCO'su A2/A3 gereği `P-`
önekini TAŞIR ve doğası gereği DOLMAMIŞtır → iki ölçütü de sağlıyordu. "Dolmuş parent'ın koruma
bacaklarına DOKUNULMAZ" güvencesi ise YALNIZ bracket'a bağlı `legs[]` bacaklarını tanıyordu;
v211'in BAĞIMSIZ OCO'su o fonksiyon yazılırken yoktu. Yani koruma her kurulduğunda bir sonraki
süpürmede ölüyordu — yapısal çarpışma, kaza değil.

BU DOSYA NEYİ ÇİVİLER:
  Ö1 ÖLÇÜM        · giriş yolu GERÇEKTEN hep BUY mu — gövdeden ölçülür, varsayılmaz
  K1 08-07 FİKSTÜRÜ · 4 koruma OCO + 1 gerçek bayat giriş → `cancelled:1, kept:4/sinif=koruma`
  K2 YÖN KEMERİ   · SELL emri (koruma ailesi coid'i OLMASA da) süpürülmez
  K3 AİLE KEMERİ  · `P-KORUMA-` coid'i (yön BUY OLSA da — kısa-taraf koruması) süpürülmez
  K4 SÜPÜRÜCÜ ÖLÜ DEĞİL · gerçek bayat giriş HÂLÂ iptal edilir (pozitif kontrol)
  K5 YÖN OKUNAMAZSA · beyanlı üçüncü hâl: `giris` sayılır (fail-closed DEĞİL, ve bu bir KARAR)
  K6 BACAKLAR     · `legs[]` altındaki koruma bacaklarına dokunulmaz (eski güvence korunuyor)
  O1 OLAY DÜRÜSTLÜĞÜ · süpürücü sınıf dökümünü + iptal edilen coid'leri deftere yazar
  O2 ÇAĞIRANIN SATIRI · `mirror_stale_entries_cancelled` artık `kept:4` diyor (08-07'nin tersi)
  İ1 İDEMPOTANS   · dışlama, v211'in canlı-koruma aramasını BOZMADI (+ pozitif kontrol)
  M1 ELLE İPTAL   · `cancel_order` tek-emir ucu KISITLANMADI — operatörün hakkı duruyor
  Y1 TEK KAYNAK   · `koruma_coid` öneki sabitten türer; kemerler ADAPTÖRDE, çağıranda değil

YÖNTEM: hiçbir test ağa çıkmaz. Okuma ucu (`orders`/`positions`) ve iptal ucu (`cancel_order`)
saplanır ya da `alpaca.httpx` bir kayıt ediciyle değiştirilir; `cancel_open_entries`in GERÇEK
gövdesi koşar. Her iddianın yanında POZİTİF KONTROL vardır — düşmeyen bir iddia koruma değil
dekordur.
"""
from __future__ import annotations

import ast
import inspect
import pathlib
import re

import pytest

from meridian import api, config, loop, store, watchdog
from meridian.adapters import alpaca

FAKE_KEY = "PKKORUMAV220FAKEKEY112233"
FAKE_SECRET = "SKKORUMAV220FAKESECRET44556677"

# =================================================================================================
# FİKSTÜRLER — 2026-08-07 BİREBİR
# =================================================================================================
# Broker adetleri canlı ölçümden: AMGN 22 · BKNG 22 · EMR 37 · NUE 25 (+ operatörün NVDA'sı).
KORUMA_DAMGA = "20260807-1623"
CANLI = {"AMGN": (22, 300.0, 285.0, 340.0), "BKNG": (22, 5200.0, 4800.0, 5600.0),
         "EMR": (37, 140.0, 133.0, 158.0), "NUE": (25, 150.0, 141.0, 172.0)}


def _poz(sym, qty, fiyat, side="long"):
    return {"symbol": sym, "qty": str(qty), "side": side, "current_price": str(fiyat)}


def _giris_parent(sym, qty, coid=None, status="filled"):
    """Motorun giriş bracket'ı — DOLMUŞ (sahiplik kanıtı) ve koruma bacakları 08-06'da ölmüş."""
    return {"id": f"id-giris-{sym}", "client_order_id": coid or f"P-2026-08-05-{sym}",
            "symbol": sym, "side": "buy", "type": "limit", "time_in_force": "gtc",
            "status": status, "qty": str(qty),
            "filled_qty": str(qty if status == "filled" else 0),
            "legs": [{"id": f"leg-tp-{sym}", "client_order_id": f"alpaca-tp-{sym}", "symbol": sym,
                      "side": "sell", "type": "limit", "status": "expired", "qty": str(qty),
                      "filled_qty": "0"},
                     {"id": f"leg-sl-{sym}", "client_order_id": f"alpaca-sl-{sym}", "symbol": sym,
                      "side": "sell", "type": "stop", "status": "canceled", "qty": str(qty),
                      "filled_qty": "0"}]}


def _koruma_oco(sym, qty, stop, hedef, status="new", bacak_status="held"):
    """v211'in BAĞIMSIZ koruma OCO'su: TEK emir, `P-KORUMA-` coid'i, SELL, stop bacağı `legs`te."""
    return {"id": f"id-koruma-{sym}", "client_order_id": f"P-KORUMA-{KORUMA_DAMGA}-{sym}",
            "symbol": sym, "side": "sell", "type": "limit", "order_class": "oco",
            "time_in_force": "gtc", "status": status, "qty": str(qty), "filled_qty": "0",
            "limit_price": str(hedef),
            "legs": [{"id": f"id-koruma-{sym}-stop", "client_order_id": f"alpaca-oco-{sym}",
                      "symbol": sym, "side": "sell", "type": "stop", "status": bacak_status,
                      "qty": str(qty), "filled_qty": "0", "stop_price": str(stop)}]}


# GERÇEK bayat giriş: motorun dolmamış alım emri — süpürmenin MEŞRU hedefi (v210 kadansı).
BAYAT_GIRIS = {"id": "id-bayat-AMD", "client_order_id": "P-2026-08-07-AMD", "symbol": "AMD",
               "side": "buy", "type": "limit", "time_in_force": "gtc", "status": "new",
               "qty": "40", "filled_qty": "0", "legs": []}
# Operatörün kendi emri: motor öneki YOK (A3) — hiçbir kemer gerekmez, sahiplik süzgeci tutar.
OPERATOR_EMRI = {"id": "id-op-TSLA", "client_order_id": "9f1c-uuid-operator", "symbol": "TSLA",
                 "side": "buy", "type": "limit", "status": "new", "qty": "5", "filled_qty": "0",
                 "legs": []}

DEFTER = {"positions": {s: {"ticker": s, "qty": q, "stop": st, "trail_stop": 0.0, "target": hd}
                        for s, (q, _f, st, hd) in CANLI.items()}}


def _acik(o: dict) -> bool:
    """Broker'ın `status=open` süzgecinin taklidi — kapanmış emir açık listede GÖRÜNMEZ."""
    return str(o.get("status", "")).lower() in ("new", "accepted", "pending_new", "held",
                                                "partially_filled", "accepted_for_bidding")


@pytest.fixture
def ayna(sandbox_state, monkeypatch):
    """Sahte kimlik + `alpaca_paper` arka ucu; taşıma SAĞLIKLI. Gerçek istemci hiç kurulmaz."""
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


def _defteri_sap(monkeypatch, emirler, pozisyonlar=(), portfoy=None) -> list:
    """Emir/pozisyon uçlarını sapla; iptal ucunu KAYDET. `cancel_open_entries` GERÇEK gövdesiyle
    koşar — yalnız sınırın iki ucu taklit edilir (ağ yok, gerçek istemci yok)."""
    iptal: list = []

    def _orders(status="open", limit=50, nested=False):
        rows = [dict(o) for o in emirler]
        return [o for o in rows if _acik(o)] if str(status) == "open" else rows

    monkeypatch.setattr(alpaca, "orders", _orders)
    monkeypatch.setattr(alpaca, "positions", lambda: [dict(p) for p in pozisyonlar])
    monkeypatch.setattr(alpaca, "cancel_order", lambda oid: iptal.append(oid) or {"ok": True})
    store.write_json("portfolio.json", portfoy if portfoy is not None else DEFTER)
    return iptal


def _08_07_defteri(korumali=True) -> list:
    """08-07 akşamının emir defteri: dolmuş girişler + (4 koruma OCO) + 1 bayat giriş + operatör."""
    emirler = [_giris_parent(s, q) for s, (q, _f, _st, _hd) in CANLI.items()]
    if korumali:
        emirler += [_koruma_oco(s, q, st, hd) for s, (q, _f, st, hd) in CANLI.items()]
    return emirler + [dict(BAYAT_GIRIS), dict(OPERATOR_EMRI)]


def _08_07_pozisyonlar() -> list:
    return ([_poz(s, q, f) for s, (q, f, _st, _hd) in CANLI.items()]
            + [_poz("NVDA", 1, 180.0)])           # operatörün kendi pozisyonu (A3)


def _olaylar(ad=None) -> list:
    ev = store.read_jsonl("events.jsonl")
    return [e for e in ev if ad is None or e.get("event") == ad]


class HttpKayitci:
    """`alpaca.httpx` yerine geçer. HİÇBİR ağ çağrısı yapmaz; yalnız fiil/URL/gövde kaydeder."""

    def __init__(self, status=200, payload=None):
        self.calls = []
        self.status = status
        self.payload = payload if payload is not None else {"id": "o-1", "status": "new"}

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


# =================================================================================================
# Ö1 · ÖLÇÜM — "GİRİŞ HEP BUY" BİR VARSAYIM DEĞİL, GÖVDEDEN OKUNAN BİR OLGU
# =================================================================================================
def test_O1_giris_govdesi_UC_DALDA_da_BUY_gonderir(ayna, monkeypatch):
    """Yön kemerinin dayanağı: `submit_bracket` HANGİ dala girerse girsin `side=buy` gönderir.

    Üç dal E1 yasasının kendisidir (limit / stop_limit / eski stop) — biri sessizce SELL gönderse
    yön kemeri o emri koruma sanıp bayat tetiği canlı bırakırdı."""
    rec = HttpKayitci()
    monkeypatch.setattr(alpaca, "httpx", rec)
    alpaca.submit_bracket("AMD", 40, 100.0, 110.0, 95.0, client_order_id="P-1-AMD",
                          entry_limit=100.5, entry_type="limit")
    alpaca.submit_bracket("AMD", 40, 100.0, 110.0, 95.0, client_order_id="P-2-AMD",
                          entry_limit=100.5, entry_type="stop_limit")
    alpaca.submit_bracket("AMD", 40, 100.0, 110.0, 95.0, client_order_id="P-3-AMD")
    yonler = [c["json"]["side"] for c in rec.calls]
    assert yonler == ["buy", "buy", "buy"], f"giriş bacağı BUY değil: {yonler}"
    assert alpaca.GIRIS_EMRI_YONU == "buy", "kemer sabiti ölçülen gövdeden AYRIŞMIŞ"


def test_O1b_submit_plan_ayni_govdeden_gecer_ikinci_giris_yolu_YOK(ayna, monkeypatch):
    """`submit_plan` planı boyutlandırır ve AYNI `submit_bracket` gövdesine iner — uçtan uca ölçüm
    (kaynak okumakla yetinilmez; gerçekten giden gövdenin yönü sayılır)."""
    rec = HttpKayitci()
    monkeypatch.setattr(alpaca, "httpx", rec)
    monkeypatch.setattr(alpaca, "asset_tradable", lambda s: True)
    plan = {"id": "P-2026-08-07-AMD", "ticker": "AMD", "entry_trigger": 100.0, "stop": 95.0,
            "profit_target": 110.0, "size_r": 1.0}
    res = alpaca.submit_plan(plan, equity=100_000, ref_price=99.0, atr=1.0)
    assert res["ok"] is True
    gonderimler = [c for c in rec.calls if c["fiil"] == "POST"]
    assert len(gonderimler) == 1 and gonderimler[0]["json"]["side"] == "buy"


def test_O1c_modulde_emir_URETEN_iki_yol_var_ve_yonleri_AYRIK():
    """KAYNAK DÜZEYİ SÜPÜRME: `POST /v2/orders` yapan HER fonksiyon taranır. Bugün ikisi var —
    giriş (`buy`) ve koruma (`sell`). Yarın üçüncü bir gönderici eklenirse bu test onu ADIYLA
    düşürür; yön kemeri "bilinmeyen bir yol BUY gönderiyordur" varsayımına dayanamaz."""
    src = pathlib.Path(alpaca.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    gonderenler = {}
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        seg = ast.get_source_segment(src, fn) or ""
        if "httpx.post(" in seg and "/v2/orders" in seg:
            gonderenler[fn.name] = set(re.findall(r'"side":\s*"(\w+)"', seg))
    assert set(gonderenler) == {"submit_bracket", "submit_protective_oco"}, \
        f"emir üreten yol kümesi değişti: {sorted(gonderenler)}"
    assert gonderenler["submit_bracket"] == {"buy"}
    assert gonderenler["submit_protective_oco"] == {"sell"}


# =================================================================================================
# K1 · 08-07 FİKSTÜRÜ — SÜPÜRÜCÜ YALNIZ BAYAT GİRİŞİ İPTAL EDER
# =================================================================================================
def test_K1_08_07_supurmesi_yalniz_bayat_girisi_iptal_eder(ayna, monkeypatch):
    """ÇEKİRDEK: 4 koruma OCO + 1 gerçek bayat giriş + operatör emri → `cancelled:1, kept:4`.

    08-07'de bu çağrı `cancelled:4, kept:0` üretmişti; aşağıdaki iddia o defterin tersidir."""
    iptal = _defteri_sap(monkeypatch, _08_07_defteri(), _08_07_pozisyonlar())

    res = alpaca.cancel_open_entries()

    assert iptal == ["id-bayat-AMD"], f"yanlış emirler iptal edildi: {iptal}"
    assert [c["coid"] for c in res["cancelled"]] == ["P-2026-08-07-AMD"]
    assert {c["sinif"] for c in res["cancelled"]} == {"giris"}
    korunan = sorted(k["symbol"] for k in res["kept"])
    assert korunan == ["AMGN", "BKNG", "EMR", "NUE"], f"koruma `kept` altında değil: {korunan}"
    assert {k["sinif"] for k in res["kept"]} == {"koruma"}
    assert all(str(k["coid"]).startswith(alpaca.KORUMA_COID_ONEK) for k in res["kept"])
    assert res["siniflar"] == {"giris": 1, "koruma": 4, "yabanci": 1}
    assert [f["symbol"] for f in res["foreign"]] == ["TSLA"]
    # 08-07'nin ta kendisi: hiçbir koruma coid'i iptal listesinde OLMAMALI.
    for sym in CANLI:
        assert f"P-KORUMA-{KORUMA_DAMGA}-{sym}" not in [c["coid"] for c in res["cancelled"]]


def test_K2_yon_kemeri_TEK_BASINA_tutar(ayna, monkeypatch):
    """Koruma ailesi coid'i OLMAYAN bir SELL emri (ör. gelecekteki bir çıkış emri) de süpürülmez:
    long-only motorda giriş BUY'dur, SELL bir emir giriş OLAMAZ.

    POZİTİF KONTROL aynı testte: AYNI coid'in BUY hâli süpürülür — yani ayıran şey gerçekten YÖN."""
    sell = {"id": "id-sell", "client_order_id": "P-2026-08-05-EMR-exit", "symbol": "EMR",
            "side": "sell", "type": "stop", "status": "held", "qty": "37", "filled_qty": "0"}
    iptal = _defteri_sap(monkeypatch, [sell])
    res = alpaca.cancel_open_entries()
    assert iptal == [], "SELL emri giriş sanıldı ve süpürüldü"
    assert res["kept"][0]["sinif"] == "koruma" and "yön" in res["kept"][0]["neden"]

    buy = {**sell, "id": "id-buy", "side": "buy"}
    iptal2 = _defteri_sap(monkeypatch, [buy])
    res2 = alpaca.cancel_open_entries()
    assert iptal2 == ["id-buy"], "pozitif kontrol düştü: BUY emri de süpürülmüyor (test kör)"
    assert res2["siniflar"]["giris"] == 1


def test_K3_aile_kemeri_TEK_BASINA_tutar_kisa_taraf_BUY_stopu(ayna, monkeypatch):
    """YARININ VAKASI: kısa pozisyona koruma kurulursa koruyucu bacak BUY-stop olur ve YÖN
    kemerinden geçer. Aile kemeri (`P-KORUMA-`) onu yine tutar — iki kemer bu yüzden birlikte var.

    POZİTİF KONTROL: aynı emrin koruma ailesi DIŞINDAKİ coid'i süpürülür."""
    buy_stop_koruma = {"id": "id-kisa-koruma",
                       "client_order_id": f"P-KORUMA-{KORUMA_DAMGA}-SHORTY", "symbol": "SHORTY",
                       "side": "buy", "type": "stop", "status": "new", "qty": "10",
                       "filled_qty": "0"}
    iptal = _defteri_sap(monkeypatch, [buy_stop_koruma])
    res = alpaca.cancel_open_entries()
    assert iptal == [], "kısa-taraf koruması (BUY-stop) süpürüldü — aile kemeri tutmadı"
    assert res["kept"][0]["sinif"] == "koruma" and "aile" in res["kept"][0]["neden"]

    yabanci_aile = {**buy_stop_koruma, "id": "id-normal",
                    "client_order_id": "P-2026-08-07-SHORTY"}
    iptal2 = _defteri_sap(monkeypatch, [yabanci_aile])
    alpaca.cancel_open_entries()
    assert iptal2 == ["id-normal"], "pozitif kontrol düştü: aile dışı emir de süpürülmüyor"


def test_K4_gercek_bayat_giris_HALA_supurulur_supurucu_olu_degil(ayna, monkeypatch):
    """KEMERLERİN BEDELİ ÖLÇÜLÜR: kadans hâlâ işini yapıyor mu? Üç bayat giriş → üçü de iptal.
    Bu iddia olmasaydı "hiçbir şeyi iptal etme" de testi geçerdi (v210 kadansı sessizce ölürdü)."""
    bayatlar = [{**BAYAT_GIRIS, "id": f"id-b{i}", "client_order_id": f"P-2026-08-07-T{i}",
                 "symbol": f"T{i}"} for i in range(3)]
    iptal = _defteri_sap(monkeypatch, bayatlar)
    res = alpaca.cancel_open_entries()
    assert sorted(iptal) == ["id-b0", "id-b1", "id-b2"]
    assert res["siniflar"] == {"giris": 3, "koruma": 0, "yabanci": 0}


def test_K5_yonu_okunamayan_emir_BEYANLI_ucuncu_hal(ayna, monkeypatch):
    """`side` alanı olmayan bir motor emri `giris` sayılır ve eski ölçütlere düşer — BU BİR KARAR,
    kaza değil: Alpaca her emirde `side` döndürür, alanın yokluğu üretimde bir olgu değildir ve
    orada fail-closed davranmak süpürücüyü sessizce ÖLÜ hâle getirirdi (bayat tetik hiç kesilmezdi).
    Kararın yazılı olduğu yer kaynağın kendisidir — bu test onu çiviler."""
    yonsuz = {"id": "id-yonsuz", "client_order_id": "P-2026-08-07-NOSIDE", "symbol": "NOSIDE",
              "status": "new", "filled_qty": "0"}
    iptal = _defteri_sap(monkeypatch, [yonsuz])
    res = alpaca.cancel_open_entries()
    assert iptal == ["id-yonsuz"] and res["siniflar"]["giris"] == 1
    kaynak = inspect.getsource(alpaca)
    assert "YÖNÜ OKUNAMAYAN EMİR" in kaynak, "beyanlı üçüncü hâl kaynakta YAZILI değil"
    # ...ama aile kemeri bu dalda da tutar: yönü okunamayan bir KORUMA emri yine süpürülmez.
    iptal2 = _defteri_sap(monkeypatch, [{**yonsuz, "id": "id-yonsuz-koruma",
                                         "client_order_id": f"P-KORUMA-{KORUMA_DAMGA}-NOSIDE"}])
    alpaca.cancel_open_entries()
    assert iptal2 == [], "yönü okunamayan KORUMA emri süpürüldü — aile kemeri bu dalda çalışmıyor"


def test_K6_bracket_bacaklarina_dokunulmaz_eski_guvence_duruyor(ayna, monkeypatch):
    """v220 yeni bir kapı eklerken ESKİ kapıyı sökmemeli: dolmuş parent `kept`, `legs[]` altındaki
    canlı koruma bacakları İPTAL EDİLMEZ (nested okuma bacakları listeye taşır)."""
    parent = _giris_parent("NVDA", 40, status="partially_filled")
    parent["legs"][0]["status"] = "new"          # canlı TP bacağı
    parent["legs"][1]["status"] = "held"         # canlı SL bacağı
    parent["filled_qty"] = "20"
    iptal = _defteri_sap(monkeypatch, [parent])
    res = alpaca.cancel_open_entries()
    assert iptal == [], f"koruma bacağı ya da kısmen dolmuş parent iptal edildi: {iptal}"
    assert res["kept"][0]["sinif"] == "giris" and "dolmuş" in res["kept"][0]["neden"]


# =================================================================================================
# O · OLAY DÜRÜSTLÜĞÜ — "cancelled:4" ARTIK NEYİ İPTAL ETTİĞİNİ SÖYLÜYOR
# =================================================================================================
def test_O1_supurme_sinif_dokumunu_ve_COIDLERI_deftere_yazar(ayna, monkeypatch):
    """08-07'nin ölçülemeyen kalemi (devir tatbikatı §4): olayda yalnız SAYI vardı, liste yoktu —
    "iptal edilen 4 emir tam olarak o dört korumaydı" bir ÇIKARIMDI. Artık kayıt taşıyor."""
    _defteri_sap(monkeypatch, _08_07_defteri(), _08_07_pozisyonlar())
    alpaca.cancel_open_entries()

    dokum = _olaylar(alpaca.EV_SUPURME_SINIFLARI)
    assert len(dokum) == 1, f"sınıf dökümü yazılmadı: {dokum}"
    e = dokum[0]
    assert (e["giris"], e["koruma"], e["yabanci"]) == (1, 4, 1)
    assert e["cancelled"] == 1
    assert e["iptal_coidler"] == ["P-2026-08-07-AMD"], "iptal edilen coid kayıtta YOK"
    assert sorted(e["korunan_coidler"]) == sorted(f"P-KORUMA-{KORUMA_DAMGA}-{s}" for s in CANLI)


def test_O1b_koruma_YOKKEN_ikinci_satir_yazilmaz_kosul_beyanli(ayna, monkeypatch):
    """Dökümün koşulu BEYANLIDIR: satır, koruma sınıfı defterde varken yazılır. Koruma yoksa
    çağıranın kendi satırı (cancelled/kept/foreign) ile aynı şeyi iki kez söylerdi.

    POZİTİF KONTROL üstteki testtedir: koruma varken satır GERÇEKTEN yazılıyor."""
    _defteri_sap(monkeypatch, [dict(BAYAT_GIRIS), dict(OPERATOR_EMRI)])
    alpaca.cancel_open_entries()
    assert _olaylar(alpaca.EV_SUPURME_SINIFLARI) == []


def test_O2_cagiranin_08_07_satiri_artik_kept_4_diyor(ayna, monkeypatch):
    """08-07 defterinin BİREBİR tekrarı, bu kez günlük kadansın kendi yolundan
    (`loop._cancel_stale_entry_orders`): o gece `cancelled:4, kept:0` yazılmıştı; şimdi
    `cancelled:1, kept:4` ve YANINDA sınıf dökümü var. Çağıran DEĞİŞMEDİ — dürüstlük adaptörde."""
    iptal = _defteri_sap(monkeypatch, _08_07_defteri(), _08_07_pozisyonlar())

    res = loop._cancel_stale_entry_orders("2026-08-07")

    assert iptal == ["id-bayat-AMD"]
    satir = _olaylar(loop.EV_STALE_ENTRIES_CANCELLED)
    assert len(satir) == 1 and satir[0]["gate"] == "gunluk_kadans"
    assert (satir[0]["cancelled"], satir[0]["kept"], satir[0]["foreign"]) == (1, 4, 1), \
        "kadans satırı hâlâ 08-07'nin sayılarını yazıyor"
    assert len(res["kept"]) == 4
    assert _olaylar(alpaca.EV_SUPURME_SINIFLARI), "sınıf dökümü kadans yolunda yazılmadı"


# =================================================================================================
# İ1 · İDEMPOTANS — DIŞLAMA, v211'İN CANLI-KORUMA ARAMASINI BOZMADI
# =================================================================================================
def test_I1_supurme_sonrasi_koruma_bulunur_ve_IKINCI_OCO_gonderilmez(ayna, monkeypatch):
    """v211'in birincil idempotansı `koruma_report`un coid/emir taramasıdır. Süpürücü korumayı
    bıraktığına göre tarama onu HÂLÂ bulmalı ve ikinci bir OCO doğmamalı."""
    cagrilar = []
    monkeypatch.setattr(alpaca, "submit_protective_oco",
                        lambda *a, **k: cagrilar.append((a, k)) or {"ok": True, "reachable": True})
    _defteri_sap(monkeypatch, _08_07_defteri(korumali=True), _08_07_pozisyonlar())

    supurme = alpaca.cancel_open_entries()
    assert len(supurme["kept"]) == 4                          # ön koşul: koruma hayatta

    rap = api.koruma_onerileri()
    motor = [s for s in rap["satirlar"] if s["motor"]]
    assert len(motor) == 4 and all(s["korumali"] for s in motor), \
        f"süpürmeden sonra koruma GÖRÜNMÜYOR: {[(s['ticker'], s['korumali']) for s in motor]}"
    assert rap["gonderilebilir"] == 0
    r = api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=rap["oneri_id"], onaylayan="test")
    assert cagrilar == [], "zaten korunan pozisyona ikinci OCO gönderildi (idempotans kırık)"
    assert r["ok"] is False and "gönderilecek öneri yok" in r["detail"]


def test_I1b_pozitif_kontrol_koruma_YOKKEN_dort_OCO_gonderilir(ayna, monkeypatch):
    """Üstteki 'emir gitmedi' iddiası ancak bu dal GERÇEKTEN emir gönderiyorsa bir şey ölçer:
    koruma defterden kalkınca yol açılır ve dört öneri gönderilir."""
    cagrilar = []
    monkeypatch.setattr(alpaca, "submit_protective_oco",
                        lambda *a, **k: cagrilar.append(k.get("client_order_id"))
                        or {"ok": True, "reachable": True, "coid": k.get("client_order_id")})
    _defteri_sap(monkeypatch, _08_07_defteri(korumali=False), _08_07_pozisyonlar())

    alpaca.cancel_open_entries()
    rap = api.koruma_onerileri()
    assert rap["gonderilebilir"] == 4
    api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=rap["oneri_id"], onaylayan="test")
    assert len(cagrilar) == 4
    assert all(str(c).startswith(alpaca.KORUMA_COID_ONEK) for c in cagrilar), \
        "yeni koruma coid'i AİLE önekini taşımıyor — bir sonraki süpürmede yine ölürdü"


def test_I2_koruma_coidi_sahipligi_KAYBETMEDI(ayna):
    """Aile kemeri sahipliği ZAYIFLATMAZ: koruma coid'i hâlâ `is_engine_order` geçer (A2/A3 —
    mutabakat onu 'motor emri' saymaya devam eder), üstüne `is_koruma_order` da geçer."""
    coid = alpaca.koruma_coid("EMR")
    emir = {"client_order_id": coid, "symbol": "EMR", "side": "sell", "status": "new"}
    assert coid.startswith(alpaca.ENGINE_COID_PREFIX) and coid.startswith(alpaca.KORUMA_COID_ONEK)
    assert alpaca.is_engine_order(emir) is True
    assert alpaca.is_koruma_order(emir) is True
    assert alpaca.is_koruma_order({"client_order_id": "P-2026-08-07-AMD"}) is False
    assert alpaca.coid_sinifi(emir)[0] == "koruma"


# =================================================================================================
# M1 · ELLE İPTAL HAKKI — KEMER YALNIZ TOPLU SÜPÜRÜCÜDE
# =================================================================================================
def test_M1_cancel_order_korumayi_iptal_etmeyi_ENGELLEMEZ(ayna, monkeypatch):
    """Operatör kendi kurduğu korumayı kaldırabilmeli. Kemer `cancel_order`a KONULMADI: konsaydı
    A3 ters yönden ihlal edilirdi (insanın kendi emrine erişimi motor tarafından kısıtlanamaz)."""
    rec = HttpKayitci(status=204, payload={})
    monkeypatch.setattr(alpaca, "httpx", rec)
    res = alpaca.cancel_order("id-koruma-EMR")
    assert res["ok"] is True
    assert [c["fiil"] for c in rec.calls] == ["DELETE"], "tek-emir iptali sessizce engellendi"
    src = inspect.getsource(alpaca.cancel_order)
    for yasak in ("KORUMA_COID_ONEK", "is_koruma_order", "coid_sinifi"):
        assert yasak not in src, f"kemer tek-emir ucuna sızmış: {yasak}"


# =================================================================================================
# Y1 · YASA — TEK KAYNAK, VE KEMERLER ADAPTÖRÜN İÇİNDE
# =================================================================================================
def test_Y1_onek_tek_kaynaktan_turer_iki_yerde_yazilmaz():
    """`koruma_coid` ile süpürücü AYNI öneği okumak zorunda: iki yerde iki metin, 08-07'yi sessizce
    geri getirirdi (coid `P-KORUMA-` üretilir, kemer `P-KORUM-` arar → kimse fark etmez)."""
    assert alpaca.KORUMA_COID_ONEK == f"{alpaca.ENGINE_COID_PREFIX}KORUMA-"
    src = inspect.getsource(alpaca.koruma_coid)
    assert "KORUMA_COID_ONEK" in src, "coid üreteci sabiti kullanmıyor"
    assert '"KORUMA-' not in src and "'KORUMA-" not in src, "önek ikinci kez elle yazılmış"


def test_Y2_kemerler_ADAPTORDE_cagiranlar_degismedi():
    """Kusur adaptördeydi, düzeltme de orada: çağıranlar (döngü) kendi süzgecini KURMAZ — tek yasa
    adaptörün denetlenmiş yolunda yaşar (v161/C23 + v210/B3 çivilerinin bu tur için tekrarı)."""
    kadans = inspect.getsource(loop._cancel_mirror_entries)
    for yasak in ("KORUMA_COID_ONEK", "is_koruma_order", "coid_sinifi", "side", "httpx"):
        assert yasak not in kadans, f"süzgeç çağırana sızmış: {yasak}"
    supurucu = inspect.getsource(alpaca.cancel_open_entries)
    assert "coid_sinifi(o)" in supurucu, "süpürücü sınıf hükmünü tek yerden okumuyor"
    assert "SINIF_KORUMA" in supurucu and "SINIF_YABANCI" in supurucu

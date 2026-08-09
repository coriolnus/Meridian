"""test_koruma_oco_grup_v221.py — ÜÇÜNCÜ KEMER: OCO GRUBUNUN BİR BACAĞI KORUMA İSE GRUBUN TAMAMI KORUMA.

ÖLÇÜM (canlı A1 paper, salt-okuma GET, 2026-08-09 — VARSAYILMADI): `koruma_kur` dört OCO gönderdi;
`orders(status="open", nested=True)` yanıtında her biri TEK üst düzey LİMİT satırı (coid
`P-KORUMA-20260809-0835-{SYM}`, side=sell, type=limit, order_class=oco) + `legs[0]` altında TEK STOP
bacağı (coid = Alpaca UUID'si, side=sell, type=stop, order_class=oco, status=held). Bağ SALT `legs[]`
İÇERME bağıdır (`parent_order_id` boş; düz çekimde stop bacağı hiç görünmez). Bu dosyanın fikstürleri
o ölçülen şekli BİREBİR taşır.

KÖK NEDEN (hüküm sırası): v220 `coid_sinifi` SAHİPLİK KAPISINI (`is_engine_order`) en başa koyuyordu;
stop bacağının coid'i Alpaca UUID'si olduğundan YÖN KEMERİNE (SELL→koruma) ULAŞMADAN `yabanci`
dönüyordu. Zararsız (stop bacağı `legs` altında, süpürücüye üst düzey aday olmaz; `yabanci` de
süpürülmez) ama iki bacak İKİ FARKLI SEBEPLE korunuyor ve stop bacağı "operatörün emri" diye YANLIŞ
etiketleniyordu.

FİX = ÜÇÜNCÜ KEMER (grup-farkındalığı), KABA HÜKÜM-SIRASI DEĞİL: yön kemerini sahiplik kapısından
önce almak operatörün KENDİ satışını da `koruma` sayardı (A3 ihlali). Doğru sebep bacağın YÖNÜ değil
GRUP ÜYELİĞİdir. Grup kemeri sahiplik kapısından ÖNCE gelir AMA yalnız doğrulanmış bir koruma kardeşi
varken → A3 KORUNUR.

BU DOSYA NEYİ ÇİVİLER (her iddianın yanında POZİTİF KONTROL — düşmeyen iddia koruma değil dekordur):
  G1 CANLI ŞEKİL   · OCO (limit P-KORUMA + stop UUID, nested bağlı) → İKİ bacak da SINIF_KORUMA
  G2 SÜPÜRÜCÜ      · 4 canlı OCO → cancelled:0, kept:4/koruma; siniflar bacakları SAYMAZ (v220 sayımı)
  G3 SÜPÜRÜCÜ ÖLÜ DEĞİL · yanına bayat giriş → o iptal, OCO'lar kept
  G4 ÜÇ KEMER AYRI · aile · yön · grup — üçü de tek başına, her biri pozitif kontrollü
  G5 A3 KORUNUR    · operatörün öneksiz SATIŞI grup kardeşi yoksa `yabanci` kalır (kaba-fix reddi)
  G6 İDEMPOTANS    · süpürme sonrası v211 coid/kapsam taraması korumayı bulur, ikinci OCO gitmez
  G7 GERİYE UYUM   · `coid_sinifi(o)` tek-argüman imzası (default grup_koruma=False) korunur
  G8 HÜKÜM SIRASI  · grup kemeri kaynakta sahiplik kapısından ÖNCE (kök-neden fixi yapısal çivili)

YÖNTEM: hiçbir test ağa çıkmaz; okuma/iptal uçları saplanır, `cancel_open_entries`in GERÇEK gövdesi
koşar. Gerçek broker'a emir GÖNDERİLMEZ/İPTAL EDİLMEZ.
"""
from __future__ import annotations

import inspect

import pytest

from meridian import api, config, store, watchdog
from meridian.adapters import alpaca

FAKE_KEY = "PKGRUPV221FAKEKEY0011223344"
FAKE_SECRET = "SKGRUPV221FAKESECRET5566778899"

KORUMA_DAMGA = "20260809-0835"
# Broker adetleri + canlı fiyat + kitabın stop/hedefi (canlı ölçümle tutarlı bant).
CANLI = {"AMGN": (22, 470.0, 389.42, 453.5), "BKNG": (22, 210.0, 191.54, 245.76),
         "EMR": (37, 170.0, 152.48, 186.35), "NUE": (25, 300.0, 257.4, 317.49)}
# Alpaca'nın OCO ikinci bacağına atadığı UUID coid'leri (canlı ölçümden birebir biçim).
STOP_UUID = {"AMGN": "50990cb8-6dc8-4537-aa83-369afab66509",
             "BKNG": "41e85f79-5778-42e5-a6ec-811ee5834ba0",
             "EMR": "33f9d1b2-615c-4a44-81b9-5d56ae0e5229",
             "NUE": "f57885f7-b0fb-40be-b1e2-ca7865375121"}


def _poz(sym, qty, fiyat, side="long"):
    return {"symbol": sym, "qty": str(qty), "side": side, "current_price": str(fiyat)}


def _oco_canli(sym, qty, stop, hedef, status="accepted", bacak_status="held"):
    """CANLI-BİREBİR koruma OCO'su: üst düzey LİMİT (P-KORUMA coid) + `legs[0]` STOP bacağı (UUID)."""
    return {"id": f"id-oco-{sym}", "client_order_id": f"P-KORUMA-{KORUMA_DAMGA}-{sym}",
            "symbol": sym, "side": "sell", "type": "limit", "order_class": "oco",
            "time_in_force": "gtc", "status": status, "qty": str(qty), "filled_qty": "0",
            "limit_price": str(hedef),
            "legs": [{"id": f"id-oco-{sym}-stop", "client_order_id": STOP_UUID[sym],
                      "symbol": sym, "side": "sell", "type": "stop", "order_class": "oco",
                      "status": bacak_status, "qty": str(qty), "filled_qty": "0",
                      "stop_price": str(stop)}]}


def _giris_parent_filled(sym, qty):
    """DOLMUŞ giriş bracket'ı — sahiplik kanıtı (koruma_report motor sembolü); eski bacakları ölmüş."""
    return {"id": f"id-giris-{sym}", "client_order_id": f"P-2026-08-05-{sym}",
            "symbol": sym, "side": "buy", "type": "limit", "time_in_force": "gtc",
            "status": "filled", "qty": str(qty), "filled_qty": str(qty),
            "legs": [{"id": f"leg-tp-{sym}", "client_order_id": f"alpaca-tp-{sym}", "symbol": sym,
                      "side": "sell", "type": "limit", "status": "expired", "qty": str(qty),
                      "filled_qty": "0"},
                     {"id": f"leg-sl-{sym}", "client_order_id": f"alpaca-sl-{sym}", "symbol": sym,
                      "side": "sell", "type": "stop", "status": "canceled", "qty": str(qty),
                      "filled_qty": "0"}]}


BAYAT_GIRIS = {"id": "id-bayat-AMD", "client_order_id": "P-2026-08-09-AMD", "symbol": "AMD",
               "side": "buy", "type": "limit", "time_in_force": "gtc", "status": "new",
               "qty": "40", "filled_qty": "0", "legs": []}
OPERATOR_EMRI = {"id": "id-op-TSLA", "client_order_id": "9f1c-uuid-operator", "symbol": "TSLA",
                 "side": "buy", "type": "limit", "status": "new", "qty": "5", "filled_qty": "0",
                 "legs": []}

DEFTER = {"positions": {s: {"ticker": s, "qty": q, "stop": st, "trail_stop": 0.0, "target": hd}
                        for s, (q, _f, st, hd) in CANLI.items()}}


def _acik(o: dict) -> bool:
    return str(o.get("status", "")).lower() in ("new", "accepted", "pending_new", "held",
                                                "partially_filled", "accepted_for_bidding")


@pytest.fixture
def ayna(sandbox_state, monkeypatch):
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


def _defteri_sap(monkeypatch, emirler, pozisyonlar=(), portfoy=None) -> dict:
    """Emir/pozisyon uçlarını sapla; iptal ucunu ve `orders` çağrılarının `nested` bayrağını KAYDET.
    `cancel_open_entries` GERÇEK gövdesiyle koşar — yalnız sınırın uçları taklit edilir."""
    kayit: dict = {"iptal": [], "nested": []}

    def _orders(status="open", limit=50, nested=False):
        kayit["nested"].append(bool(nested))
        rows = [dict(o) for o in emirler]
        return [o for o in rows if _acik(o)] if str(status) == "open" else rows

    monkeypatch.setattr(alpaca, "orders", _orders)
    monkeypatch.setattr(alpaca, "positions", lambda: [dict(p) for p in pozisyonlar])
    monkeypatch.setattr(alpaca, "cancel_order",
                        lambda oid: kayit["iptal"].append(oid) or {"ok": True})
    store.write_json("portfolio.json", portfoy if portfoy is not None else DEFTER)
    return kayit


def _canli_defter(korumali=True, ek=()) -> list:
    emirler = [_giris_parent_filled(s, q) for s, (q, _f, _st, _hd) in CANLI.items()]
    if korumali:
        emirler += [_oco_canli(s, q, st, hd) for s, (q, _f, st, hd) in CANLI.items()]
    return emirler + list(ek)


def _canli_pozisyonlar() -> list:
    # Motor pozisyonları (broker adedi + canlı fiyat) + operatörün kendi NVDA'sı (A3).
    return [_poz(s, q, f) for s, (q, f, _st, _hd) in CANLI.items()] + [_poz("NVDA", 1, 180.0)]


# =================================================================================================
# G1 · CANLI ŞEKİL — OCO'NUN İKİ BACAĞI DA SINIF_KORUMA
# =================================================================================================
def test_G1_oco_iki_bacak_da_koruma_stop_bacagi_yabanci_DEGIL(ayna):
    """ÇEKİRDEK: limit bacağı AİLE kemeriyle, stop bacağı (UUID) GRUP kemeriyle koruma.

    BEFORE/AFTER stop bacağında AÇIKÇA gösterilir: tek başına `yabanci` (kök-neden: sahiplik kapısı
    yön kemerinden önce), grup sinyaliyle `koruma`. Grup sinyalini kardeşi (limit bacağı) taşır."""
    oco = _oco_canli("NUE", 25, 257.4, 317.49)
    stop = oco["legs"][0]

    s_limit, g_limit = alpaca.coid_sinifi(oco)
    assert s_limit == alpaca.SINIF_KORUMA and "aile" in g_limit

    # BEFORE — bacak tek başına (parent'a geri-referansı yok) → kök-neden semptomu
    s_alone, _ = alpaca.coid_sinifi(stop)
    assert s_alone == alpaca.SINIF_YABANCI, "kök-neden değişti: stop bacağı artık tek başına yabanci değil"

    # AFTER — kardeşi koruma olduğundan grup sinyali geçilir → koruma
    grup = alpaca.is_koruma_order(oco)           # bir kardeş is_koruma_order
    assert grup is True
    s_grp, g_grp = alpaca.coid_sinifi(stop, grup_koruma=grup)
    assert s_grp == alpaca.SINIF_KORUMA and "grup" in g_grp
    # motor öneki taşımayan bir UUID olduğu HÂLDE koruma sınıfı — istenen davranış
    assert not alpaca.is_engine_order(stop) and not alpaca.is_koruma_order(stop)


def test_G1b_ust_duzey_emir_KENDI_bacagindan_grubu_taniyabilir(ayna):
    """ROBUSTLUK: hangi bacağın damgayı taşıdığını VARSAYMAZ. Üst düzey emir motor-BUY (kendi coid'i
    aile öneksiz) olsa da `legs[]`'inde bir P-KORUMA bacağı varsa GRUP kemeri onu tutar — kemer
    ölçülen içerme bağına dayanır, 'hangi bacak primary' tahminine değil.

    POZİTİF KONTROL: aynı emir P-KORUMA bacağı OLMADAN `giris` düşer (grup sinyali gerçekten legs'ten)."""
    primary = {"id": "id-grp", "client_order_id": "P-2026-08-09-GRP", "symbol": "GRP", "side": "buy",
               "type": "limit", "order_class": "bracket", "status": "new", "qty": "10",
               "filled_qty": "0",
               "legs": [{"id": "id-grp-k", "client_order_id": f"P-KORUMA-{KORUMA_DAMGA}-GRP",
                         "symbol": "GRP", "side": "sell", "type": "stop", "status": "held",
                         "qty": "10", "filled_qty": "0"}]}
    s, g = alpaca.coid_sinifi(primary)
    assert s == alpaca.SINIF_KORUMA and "grup" in g, "üst düzey emir kendi P-KORUMA bacağını görmedi"

    primary_bacaksiz = {**primary, "legs": []}
    s2, _ = alpaca.coid_sinifi(primary_bacaksiz)
    assert s2 == alpaca.SINIF_GIRIS, "pozitif kontrol düştü: grup sinyali legs'ten gelmiyor (test kör)"


# =================================================================================================
# G2/G3 · SÜPÜRÜCÜ — CANLI OCO'LAR KORUNUR, SÜPÜRÜCÜ HÂLÂ ÇALIŞIR
# =================================================================================================
def test_G2_supurucu_dort_canli_oco_yu_korur_bacaklar_sayima_girmez(ayna, monkeypatch):
    """4 canlı OCO → cancelled:0, kept:4/koruma. Stop bacakları `legs` altında: sayıma GİRMEZ
    (v220 sınıf-dökümü sözleşmesi korunur — koruma:4, 8 değil) ve UUID'leri iptal listesinde OLMAZ."""
    kayit = _defteri_sap(monkeypatch, _canli_defter(korumali=True), _canli_pozisyonlar())

    res = alpaca.cancel_open_entries()

    assert kayit["iptal"] == [], f"canlı OCO süpürüldü: {kayit['iptal']}"
    assert all(nested for nested in kayit["nested"]), "süpürücü nested=True okumadı (grup kemeri kör kalır)"
    assert res["cancelled"] == []
    korunan = sorted(k["symbol"] for k in res["kept"])
    assert korunan == ["AMGN", "BKNG", "EMR", "NUE"]
    assert {k["sinif"] for k in res["kept"]} == {"koruma"}
    # SAYIM YALNIZ ÜST DÜZEY: 4 OCO parent koruma; stop bacakları (4 UUID) sayıya EKLENMEZ.
    assert res["siniflar"] == {"giris": 0, "koruma": 4, "yabanci": 0}
    tum_uuid = set(STOP_UUID.values())
    assert not (tum_uuid & {c.get("coid") for c in res["cancelled"]})


def test_G3_supurucu_olu_degil_bayat_giris_iptal_OCO_kept(ayna, monkeypatch):
    """POZİTİF KONTROL: 4 OCO + gerçek bayat giriş + operatör → yalnız bayat giriş iptal."""
    kayit = _defteri_sap(monkeypatch, _canli_defter(True, ek=[dict(BAYAT_GIRIS), dict(OPERATOR_EMRI)]),
                         _canli_pozisyonlar())
    res = alpaca.cancel_open_entries()
    assert kayit["iptal"] == ["id-bayat-AMD"]
    assert [c["coid"] for c in res["cancelled"]] == ["P-2026-08-09-AMD"]
    assert res["siniflar"] == {"giris": 1, "koruma": 4, "yabanci": 1}
    assert [f["symbol"] for f in res["foreign"]] == ["TSLA"]


# =================================================================================================
# G4 · ÜÇ KEMER — HER BİRİ AYRI, HER BİRİ POZİTİF KONTROLLÜ
# =================================================================================================
def test_G4a_aile_kemeri_tek_basina(ayna):
    """AİLE: `P-KORUMA-` coid'i (bacaksız) → koruma/aile. Pozitif kontrol: aile dışı coid → giris."""
    k = {"client_order_id": f"P-KORUMA-{KORUMA_DAMGA}-X", "symbol": "X", "side": "buy",
         "type": "stop", "status": "new"}
    s, g = alpaca.coid_sinifi(k)
    assert s == alpaca.SINIF_KORUMA and "aile" in g
    s2, _ = alpaca.coid_sinifi({**k, "client_order_id": "P-2026-08-09-X"})
    assert s2 == alpaca.SINIF_GIRIS


def test_G4b_yon_kemeri_tek_basina(ayna):
    """YÖN: motor emri + SELL (aile değil, grup yok, bacaksız) → koruma/yön. Pozitif kontrol: BUY → giris."""
    sell = {"client_order_id": "P-2026-08-05-EMR-exit", "symbol": "EMR", "side": "sell",
            "type": "stop", "status": "held"}
    s, g = alpaca.coid_sinifi(sell)
    assert s == alpaca.SINIF_KORUMA and "yön" in g
    s2, _ = alpaca.coid_sinifi({**sell, "side": "buy"})
    assert s2 == alpaca.SINIF_GIRIS


def test_G4c_grup_kemeri_tek_basina_diger_iki_kemer_TUTMAZKEN(ayna, monkeypatch):
    """GRUP: DİĞER İKİ KEMERİN TUTMADIĞI emri yalnız grup kemeri kurtarır — bu kemerin var olma
    sebebi budur.

    (i) UUID stop bacağı: motor öneksiz (aile YOK, ownership kapısı yabanci derdi) + SELL (yön kemeri
        ownership kapısına takıldığı için ULAŞAMAZ) → yalnız grup sinyali koruma yapar.
    (ii) SÜPÜRÜCÜDE: motor-BUY primary (aile YOK → yön kemeri BUY olduğu için TUTMAZ) bir P-KORUMA
         bacağı taşırsa `giris` sanılıp SÜPÜRÜLÜRDÜ; grup kemeri onu kept'te tutar.
    Her ikisinde de POZİTİF KONTROL: grup sinyali kalkınca emir eski (koruma-DIŞI) sınıfına döner."""
    # (i) — bacak tek başına
    stop = _oco_canli("NUE", 25, 257.4, 317.49)["legs"][0]
    assert alpaca.coid_sinifi(stop)[0] == alpaca.SINIF_YABANCI                 # pozitif kontrol
    assert alpaca.coid_sinifi(stop, grup_koruma=True)[0] == alpaca.SINIF_KORUMA

    # (ii) — süpürücüde motor-BUY primary + P-KORUMA bacağı
    primary = {"id": "id-b", "client_order_id": "P-2026-08-09-GRP", "symbol": "GRP", "side": "buy",
               "type": "limit", "order_class": "bracket", "status": "new", "qty": "10",
               "filled_qty": "0",
               "legs": [{"id": "id-b-k", "client_order_id": f"P-KORUMA-{KORUMA_DAMGA}-GRP",
                         "symbol": "GRP", "side": "sell", "type": "stop", "status": "held",
                         "qty": "10", "filled_qty": "0"}]}
    kayit = _defteri_sap(monkeypatch, [primary])
    res = alpaca.cancel_open_entries()
    assert kayit["iptal"] == [], "grup kemeri süpürücüde tutmadı — P-KORUMA bacaklı grup süpürüldü"
    assert res["siniflar"] == {"giris": 0, "koruma": 1, "yabanci": 0}

    # POZİTİF KONTROL: aynı primary P-KORUMA bacağı OLMADAN süpürülür (grup gerçekten fark ediyor)
    kayit2 = _defteri_sap(monkeypatch, [{**primary, "legs": []}])
    alpaca.cancel_open_entries()
    assert kayit2["iptal"] == ["id-b"], "pozitif kontrol düştü: bacaksız primary de süpürülmüyor"


# =================================================================================================
# G5 · A3 KORUNUR — GRUP KEMERİ OPERATÖRÜN SATIŞINA TAŞMAZ (KABA HÜKÜM-SIRASI REDDİ)
# =================================================================================================
def test_G5_operator_satisi_grup_kardesi_yoksa_yabanci_kalir(ayna, monkeypatch):
    """Ayıran şey YÖN değil GRUP ÜYELİĞİ: motor öneksiz bir SATIŞ (operatörün kendi emri), koruma
    kardeşi YOKKEN `yabanci` kalır ve süpürülmez — yön kemerini sahiplik kapısından önce almanın
    (kaba fix) bunu `koruma` sayması tam da reddedilen davranıştır.

    POZİTİF KONTROL: AYNI emre bir P-KORUMA bacağı eklenince `koruma` olur → ayıran gerçekten kardeş."""
    op_sell = {"id": "id-op-sell", "client_order_id": "op-uuid-sell", "symbol": "GE", "side": "sell",
               "type": "stop", "status": "held", "qty": "10", "filled_qty": "0", "legs": []}
    s, g = alpaca.coid_sinifi(op_sell)
    assert s == alpaca.SINIF_YABANCI and "A3" in g, "operatör satışı yön kemerine kaydı (A3 ihlali)"

    kayit = _defteri_sap(monkeypatch, [op_sell])
    res = alpaca.cancel_open_entries()
    assert kayit["iptal"] == [] and [f["symbol"] for f in res["foreign"]] == ["GE"]
    assert res["siniflar"] == {"giris": 0, "koruma": 0, "yabanci": 1}

    op_sell_grup = {**op_sell,
                    "legs": [{"id": "id-op-k", "client_order_id": f"P-KORUMA-{KORUMA_DAMGA}-GE",
                              "symbol": "GE", "side": "sell", "type": "stop", "status": "held",
                              "qty": "10", "filled_qty": "0"}]}
    assert alpaca.coid_sinifi(op_sell_grup)[0] == alpaca.SINIF_KORUMA


# =================================================================================================
# G6 · İDEMPOTANS — v211'İN COID/KAPSAM TARAMASI GRUP-FARKINDALIKTAN ETKİLENMEZ
# =================================================================================================
def test_G6_supurme_sonrasi_koruma_bulunur_ikinci_OCO_gitmez(ayna, monkeypatch):
    """Canlı şekilli OCO'lar süpürmeden sağ çıkar; `koruma_report` kapsamı (flatten + SELL/stop)
    onları HÂLÂ bulur → `koruma_kur` ikinci bir OCO GÖNDERMEZ. Grup-farkındalığı bu aramayı
    (coid_sinifi'den bağımsız) BOZMAZ."""
    cagrilar = []
    monkeypatch.setattr(alpaca, "submit_protective_oco",
                        lambda *a, **k: cagrilar.append((a, k)) or {"ok": True, "reachable": True})
    _defteri_sap(monkeypatch, _canli_defter(korumali=True), _canli_pozisyonlar())

    supurme = alpaca.cancel_open_entries()
    assert len(supurme["kept"]) == 4                      # ön koşul: koruma hayatta

    rap = api.koruma_onerileri()
    motor = [s for s in rap["satirlar"] if s["motor"]]
    assert len(motor) == 4 and all(s["korumali"] for s in motor), \
        f"süpürmeden sonra koruma GÖRÜNMÜYOR: {[(s['ticker'], s['korumali']) for s in motor]}"
    assert rap["gonderilebilir"] == 0
    r = api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=rap["oneri_id"], onaylayan="test")
    assert cagrilar == [], "zaten korunan pozisyona ikinci OCO gönderildi (idempotans kırık)"
    assert r["ok"] is False and "gönderilecek öneri yok" in r["detail"]


def test_G6b_pozitif_kontrol_koruma_YOKKEN_dort_OCO_gonderilir(ayna, monkeypatch):
    """Üstteki 'emir gitmedi' iddiası ancak bu dal GERÇEKTEN gönderiyorsa bir şey ölçer."""
    cagrilar = []
    monkeypatch.setattr(alpaca, "submit_protective_oco",
                        lambda *a, **k: cagrilar.append(k.get("client_order_id"))
                        or {"ok": True, "reachable": True, "coid": k.get("client_order_id")})
    _defteri_sap(monkeypatch, _canli_defter(korumali=False), _canli_pozisyonlar())

    alpaca.cancel_open_entries()
    rap = api.koruma_onerileri()
    assert rap["gonderilebilir"] == 4
    api.koruma_kur(onay=alpaca.KORUMA_ONAY_JETONU, oneri_id=rap["oneri_id"], onaylayan="test")
    assert len(cagrilar) == 4
    assert all(str(c).startswith(alpaca.KORUMA_COID_ONEK) for c in cagrilar)


# =================================================================================================
# G7/G8 · GERİYE UYUM + HÜKÜM SIRASI (KÖK-NEDEN FIXİ YAPISAL ÇİVİLİ)
# =================================================================================================
def test_G7_coid_sinifi_tek_arguman_imzasi_korunur(ayna):
    """v220 ve tüm çağıranlar `coid_sinifi(o)` tek-argümanla çağırır — default grup_koruma=False
    davranışı DEĞİŞMEZ (aile/yön/yabanci hükümleri v220 ile birebir)."""
    assert alpaca.coid_sinifi({"client_order_id": f"P-KORUMA-{KORUMA_DAMGA}-Z"})[0] == alpaca.SINIF_KORUMA
    assert alpaca.coid_sinifi({"client_order_id": "P-2026-08-09-Z", "side": "buy"})[0] == alpaca.SINIF_GIRIS
    assert alpaca.coid_sinifi({"client_order_id": "P-2026-08-09-Z", "side": "sell"})[0] == alpaca.SINIF_KORUMA
    assert alpaca.coid_sinifi({"client_order_id": "uuid-op"})[0] == alpaca.SINIF_YABANCI


def test_G8_grup_kemeri_kaynakta_sahiplik_kapisindan_ONCE(ayna):
    """KÖK-NEDEN FIXİ YAPISAL: grup kemeri, sahiplik kapısı (`is_engine_order`) ile yön kemerinden
    ÖNCE gelmezse UUID stop bacağı yine `yabanci` düşerdi. Kaynak sırası bunu çiviler."""
    src = inspect.getsource(alpaca.coid_sinifi)
    i_grup = src.index("if grup_koruma:")
    i_owner = src.index("if not is_engine_order(o):")
    i_yon = src.index("!= GIRIS_EMRI_YONU")
    assert i_grup < i_owner < i_yon, "grup kemeri sahiplik/yön kapısından önce değil — kök-neden geri gelir"
    # kemer ölçülen içerme bağına dayanır (legs), symbol+side çıkarımına değil
    assert 'o.get("legs")' in src, "grup sinyali legs içerme bağından türetilmiyor"

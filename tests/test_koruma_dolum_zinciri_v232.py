"""test_koruma_dolum_zinciri_v232.py — WP-E koruma-ailesi iki boşluk (B4 + B3, teşhis
docs/TESHIS-WPE-AYNA-DOLUM-2026-08-10.md).

VAKA SINIFI (08-07 süpürücü çarpışmasının iki kardeşi — koruma, kendisini tanımayan mekanizmalarla
çarpışıyor):
  B4 — koruma × çıkış-kuyruğu: `close_engine_position` yalnız `plan_id` eşleşen parent'ların
       bacaklarını iptal ediyordu; v211'in BAĞIMSIZ koruma OCO'su (`P-KORUMA-…`, plan_id DEĞİL)
       süzgecin DIŞINDA kalıyor, canlı satış bacakları hisseleri rehin tutuyor ve kapatma her tur
       reddedilip sonsuz `cikis_yetimi` üretiyordu. DÜZELTME davranış-sözleşmesidir, Alpaca'nın
       redd semantiğine dayanmaz: kapatmadan ÖNCE aynı sembolün koruma-SINIFI emirleri iptal
       edilir (hüküm `coid_sinifi`den — v220 aile+yön, v221 grup kemerleri; süzgeç KOPYALANMAZ)
       ve bir iptal düşüp emir CANLI kaldıysa kapatma HİÇ DENENMEZ (`cancel_failed`).
  B3 — koruma OCO dolumu zincir-dışı: koruma bacağı DOLUNCA pozisyon aynada gerçekten kapanıyor
       ama mutabakat `by_coid[plan_id]` ile eşleşemediğinden bunu görmüyor, her tur YANLIŞ sınıfla
       (`split_brain`) alarmlıyor ve kapanış kitaba işlenmiyordu. DÜZELTME: reconcile koruma-sınıfı
       dolumu TANIR (`alpaca.koruma_fill` + aynı sınıflandırıcı), kapanışı iç kitabın KENDİ maliyet
       modeliyle işler (çıkış tipi `koruma_stop`/`koruma_hedef`; gerçek dolum `alpaca_fill_price`
       olarak satırda) ve alarm `koruma_dolumu` sınıfını taşır. Fiyat/bacak okunamazsa UYDURMA YOK:
       kitaba işlenmez, alarm nedeni söyler.

YÖNTEM: hiçbir test ağa çıkmaz — okuma uçları (`orders`/`positions`) saplanır, iptal ucu kayıt
tutar ve emir durumunu GERÇEKÇİ biçimde günceller (başarılı iptal `canceled` yazar; böylece
iptal→kapat kapısının açık-emir doğrulaması gerçek listeyi okur), `alpaca.py`'nin `httpx` istemcisi kayıt edicidir.
Her iddianın yanında POZİTİF KONTROL vardır — düşmeyen bir iddia koruma değil dekordur.
"""
from __future__ import annotations

import copy
import inspect

import pytest

from meridian import config, loop, store
from meridian.adapters import alpaca
from meridian.broker import PaperBroker, Position

FAKE_KEY = "PKKORUMAV232FAKEKEY112233"
FAKE_SECRET = "SKKORUMAV232FAKESECRET44556677"
KORUMA_DAMGA = "20260809-0835"        # v221 canlı ölçümünün damgası


# =================================================================================================
# FİKSTÜRLER — v220/v221 şekilleriyle birebir (ölçülen OCO yapısı: primary=limit, stop `legs`te)
# =================================================================================================
def _giris_parent(sym, qty, coid=None, status="filled"):
    """Motorun giriş bracket'ı — DOLMUŞ (sahiplik kanıtı), koruma bacakları ölmüş (v211 senaryosu:
    koruma tam da bu yüzden bağımsız OCO olarak kurulmuştu)."""
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


def _koruma_oco(sym, qty, stop, hedef, stop_dolum=None, hedef_dolum=None):
    """v211 bağımsız koruma OCO'su (ölçülen v221 yapısı). `stop_dolum`/`hedef_dolum` verilirse
    ilgili bacak DOLMUŞ hâliyle döner (stop dolunca primary OCO gereği `canceled`a düşer)."""
    o = {"id": f"id-koruma-{sym}", "client_order_id": f"P-KORUMA-{KORUMA_DAMGA}-{sym}",
         "symbol": sym, "side": "sell", "type": "limit", "order_class": "oco",
         "time_in_force": "gtc", "status": "new", "qty": str(qty), "filled_qty": "0",
         "limit_price": str(hedef),
         "legs": [{"id": f"id-koruma-{sym}-stop", "client_order_id": f"alpaca-oco-{sym}",
                   "symbol": sym, "side": "sell", "type": "stop", "status": "held",
                   "qty": str(qty), "filled_qty": "0", "stop_price": str(stop)}]}
    if hedef_dolum is not None:
        o.update({"status": "filled", "filled_qty": str(qty),
                  "filled_avg_price": str(hedef_dolum)})
        o["legs"][0]["status"] = "canceled"
    if stop_dolum is not None:
        o["status"] = "canceled"                    # OCO: öteki bacak dolunca primary iptal düşer
        o["legs"][0].update({"status": "filled", "filled_qty": str(qty),
                             "filled_avg_price": str(stop_dolum)})
    return o


OPERATOR_SATISI = {"id": "id-op-sat", "client_order_id": "9f1c-uuid-operator", "symbol": "AMGN",
                   "side": "sell", "type": "limit", "status": "new", "qty": "10",
                   "filled_qty": "0", "legs": []}


def _acik(o: dict) -> bool:
    return str(o.get("status", "")).lower() in ("new", "accepted", "pending_new", "held",
                                                "partially_filled", "accepted_for_bidding")


@pytest.fixture
def ayna(sandbox_state, monkeypatch):
    """Sahte kimlik + `alpaca_paper`; taşıma SAĞLIKLI. Gerçek istemci hiç kurulmaz."""
    from meridian import secrets as secrets_mod
    monkeypatch.setenv("ALPACA_PAPER_KEY", FAKE_KEY)
    monkeypatch.setenv("ALPACA_PAPER_SECRET", FAKE_SECRET)
    monkeypatch.delenv("MERIDIAN_GCP_PROJECT", raising=False)
    secrets_mod.clear_cache()
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(alpaca, "transport", lambda: {"ok": True, "error": ""})
    yield sandbox_state
    secrets_mod.clear_cache()


class _Resp:
    def __init__(self, status, payload=None):
        self.status_code = status
        self._p = payload if payload is not None else {}

    def json(self):
        return self._p

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def _tel(monkeypatch, emirler, pozisyonlar=(), iptal_plan=None, delete_status=200):
    """B4 telleri: `orders` durum süzgecini uygular (iptal→kapat kapısının açık-emir doğrulaması
    GERÇEK listeyi okusun), `cancel_order` kaydeder ve emri GERÇEKÇİ günceller, DELETE kaydedilir.
    `iptal_plan[oid]`: "ok" (varsayılan) · "fail" (emir canlı kalır) · "fail_ama_doldu" (422
    yarışı: iptal reddi ama emir aslında dolmuş — açık listeden düşer). Dönen `sira` listesi
    çağrıların SIRASINI taşır (iptal→kapat iddiasının kanıtı)."""
    sira: list = []

    def _orders(status="open", limit=50, nested=False):
        rows = [copy.deepcopy(o) for o in emirler]
        if str(status) == "open":
            rows = [o for o in rows if _acik(o) or any(_acik(l) for l in o.get("legs") or [])]
        return rows

    def _cancel(oid):
        sira.append(("cancel", str(oid)))
        plan = (iptal_plan or {}).get(str(oid), "ok")
        for o in emirler:
            for kayit in [o] + list(o.get("legs") or []):
                if str(kayit.get("id")) == str(oid):
                    if plan == "ok":
                        kayit["status"] = "canceled"
                    elif plan == "fail_ama_doldu":
                        kayit["status"] = "filled"
                        kayit["filled_qty"] = kayit.get("qty", "0")
        return {"ok": plan == "ok"}

    class _Cli:
        def delete(self, url, **kw):
            sira.append(("DELETE", url, (kw.get("params") or {}).get("qty")))
            return _Resp(delete_status,
                         {"message": "close refused"} if delete_status >= 400 else {})

    monkeypatch.setattr(alpaca, "orders", _orders)
    monkeypatch.setattr(alpaca, "positions", lambda: [dict(p) for p in pozisyonlar])
    monkeypatch.setattr(alpaca, "cancel_order", _cancel)
    monkeypatch.setattr(alpaca, "httpx", _Cli())
    return sira


def _events(token: str) -> list:
    return [e for e in store.read_jsonl("events.jsonl") if token in str(e)]


def _kitap(sym="NUE", qty=25, entry=150.0, stop=141.0, hedef=172.0):
    b = PaperBroker(100_000.0, 5, 0.0)              # 5 bps slipaj — canlı varsayılanla aynı
    b.positions[sym] = Position(plan_id=f"P-2026-08-05-{sym}", ticker=sym, side="long",
                                entry=entry, stop=stop, trail_stop=stop, target=hedef, qty=qty,
                                r_per_share=entry - stop, risk_dollars=(entry - stop) * qty,
                                size_r=1.0, ts_open="2026-08-05")
    return b


# =================================================================================================
# B4 · KORUMA × ÇIKIŞ-KUYRUĞU — İPTAL→KAPAT SIRASI, KAPI, A3
# =================================================================================================
def test_B4_koruma_oco_kapatmadan_ONCE_iptal_edilir(ayna, monkeypatch):
    """ÇEKİRDEK: korumalı pozisyonda motor çıkışı → önce koruma OCO'nun İKİ kaydı da (primary +
    stop bacağı) iptal edilir, kapatma DELETE'i hepsinden SONRA gider. plan_id süzgeci artık
    korumayı dışarıda bırakmıyor — 08-07 çarpışmasının icra-bacağı kapandı."""
    emirler = [_giris_parent("AMGN", 22), _koruma_oco("AMGN", 22, 285.0, 340.0)]
    sira = _tel(monkeypatch, emirler, [{"symbol": "AMGN", "qty": "22"}])

    res = alpaca.close_engine_position("AMGN", plan_id="P-2026-08-05-AMGN")

    assert res["ok"] is True and res["owned"] is True and res["closed_qty"] == 22.0
    iptaller = [s[1] for s in sira if s[0] == "cancel"]
    assert set(iptaller) == {"id-koruma-AMGN", "id-koruma-AMGN-stop"}, \
        f"koruma OCO iptal edilmedi (rehin duruyor): {iptaller}"
    kinds = {c["kind"] for c in res["cancelled"]}
    assert kinds == {"koruma", "koruma_leg"}, f"koruma iptali kendi sınıf etiketini taşımıyor: {kinds}"
    deletes = [i for i, s in enumerate(sira) if s[0] == "DELETE"]
    assert len(deletes) == 1 and sira[deletes[0]][1].endswith("/v2/positions/AMGN")
    assert sira[deletes[0]][2] == "22"
    assert max(i for i, s in enumerate(sira) if s[0] == "cancel") < deletes[0], \
        "kapatma iptallerden ÖNCE gitti — iptal→kapat sırası bozuk"
    assert res["cancel_failed"] is False


def test_B4_yabanci_ayni_sembol_emri_DOKUNULMAZ(ayna, monkeypatch):
    """A3 KORUNUR: aynı sembolde operatörün KENDİ satış emri (koruma kardeşi olmayan uuid coid)
    iptal edilmez; kapatma yine sürer (operatör çarpışması Alpaca'nın kendi reddine kalır — bu
    zaten bugünkü davranıştı, yetki GENİŞLEMEDİ)."""
    emirler = [_giris_parent("AMGN", 22), _koruma_oco("AMGN", 22, 285.0, 340.0),
               dict(OPERATOR_SATISI)]
    sira = _tel(monkeypatch, emirler, [{"symbol": "AMGN", "qty": "22"}])
    res = alpaca.close_engine_position("AMGN", plan_id="P-2026-08-05-AMGN")
    iptaller = [s[1] for s in sira if s[0] == "cancel"]
    assert "id-op-sat" not in iptaller, "operatörün emri iptal edildi (A3 ihlali)"
    assert res["ok"] is True and [s for s in sira if s[0] == "DELETE"]


def test_B4_iptal_dusen_ve_emir_CANLI_kapatma_DENENMEZ(ayna, monkeypatch):
    """KAPI: koruma iptali düşer ve emir açık listede hâlâ CANLI → DELETE HİÇ gitmez,
    `cancel_failed: True` + gerekçe döner (yarım-durum üretilmez; kuyruk bir sonraki tur dener)."""
    emirler = [_giris_parent("AMGN", 22), _koruma_oco("AMGN", 22, 285.0, 340.0)]
    sira = _tel(monkeypatch, emirler, [{"symbol": "AMGN", "qty": "22"}],
                iptal_plan={"id-koruma-AMGN": "fail", "id-koruma-AMGN-stop": "fail"})

    res = alpaca.close_engine_position("AMGN", plan_id="P-2026-08-05-AMGN")

    assert res["ok"] is False and res["cancel_failed"] is True
    assert "DENENMEDİ" in res["detail"], f"gerekçe kapatmanın denenmediğini söylemiyor: {res['detail']}"
    assert [s for s in sira if s[0] == "DELETE"] == [], \
        "iptal düştüğü hâlde kapatma DENENDİ — rehinli redd turu / yarım-durum"
    assert res["naked"] is False, "hiçbir koruma sökülmemişken çıplak beyanı yazıldı"


def test_B4_422_yarisi_emir_artik_canli_degilse_kapatma_SURER(ayna, monkeypatch):
    """POZİTİF KONTROL (kapı körü değil): iptal reddi 'emir zaten dolmuş/iptal' yarışından
    geliyorsa (açık listede YOK) kapı geçer ve kapatma denenir — kapı redd-koduna değil
    GÖZLENEN duruma bakar (davranış sözleşmesi, Alpaca semantiğinden bağımsız)."""
    emirler = [_giris_parent("AMGN", 22), _koruma_oco("AMGN", 22, 285.0, 340.0)]
    sira = _tel(monkeypatch, emirler, [{"symbol": "AMGN", "qty": "22"}],
                iptal_plan={"id-koruma-AMGN": "fail_ama_doldu",
                            "id-koruma-AMGN-stop": "fail_ama_doldu"})
    res = alpaca.close_engine_position("AMGN", plan_id="P-2026-08-05-AMGN")
    assert [s for s in sira if s[0] == "DELETE"], "yarış aklanmadı — kapatma sonsuza dek bloklanır"
    assert res["ok"] is True and res["cancel_failed"] is False


def test_B4_koruma_iptali_ciplak_beyanina_sayilir(ayna, monkeypatch):
    """Koruma OCO'su söküldü ama DELETE reddedildi → pozisyon ÇIPLAKTIR ve `naked: True` beyan
    edilir (eski `_naked` yalnız bracket `leg`ini sayıyordu — v211 OCO'sunun sökülmesi de aynı
    pencereyi açar)."""
    emirler = [_giris_parent("AMGN", 22), _koruma_oco("AMGN", 22, 285.0, 340.0)]
    _tel(monkeypatch, emirler, [{"symbol": "AMGN", "qty": "22"}], delete_status=422)
    res = alpaca.close_engine_position("AMGN", plan_id="P-2026-08-05-AMGN")
    assert res["ok"] is False and res["naked"] is True, \
        "koruma söküldü + kapatma düştü ama çıplak pencere beyan edilmedi"


def test_B4_sahiplik_yoksa_koruma_da_SOKULMEZ(ayna, monkeypatch):
    """Sahiplik kanıtı (dolmuş motor GİRİŞİ) yoksa hiçbir şeye dokunulmaz — korumayı söküp
    kapatamamak pozisyonu sebepsiz çıplak bırakırdı. Koruma SATIŞININ dolumu da kanıt DEĞİLDİR
    (satış, uzun pozisyonun sahipliğini gösteremez)."""
    emirler = [_koruma_oco("AMGN", 22, 285.0, 340.0)]        # giriş parent'ı YOK (pencere dışı)
    sira = _tel(monkeypatch, emirler, [{"symbol": "AMGN", "qty": "22"}])
    res = alpaca.close_engine_position("AMGN", plan_id="P-2026-08-05-AMGN")
    assert res["ok"] is False and res["owned"] is False
    assert sira == [], f"sahipliksiz çağrı dokundu: {sira}"


def test_B4_plan_idsiz_cagri_koruma_dolumu_sahiplik_kaniti_DEGIL(ayna, monkeypatch):
    """plan_id=None dalında dolmuş koruma SATIŞI `owned_qty`ye sayılsaydı kapatma adedi şişer,
    operatörün aynı sembboldeki hisseleri düşerdi. Satış dolumları sahiplik toplamına GİRMEZ:
    giriş 22 dolmuş + koruma 22 dolmuş + aynada 44 (22'si operatörün) → yalnız 22 kapatılır."""
    emirler = [_giris_parent("AMGN", 22), _koruma_oco("AMGN", 22, 285.0, 340.0, hedef_dolum=340.0)]
    sira = _tel(monkeypatch, emirler, [{"symbol": "AMGN", "qty": "44"}])
    res = alpaca.close_engine_position("AMGN", plan_id=None)
    assert res["ok"] is True and res["closed_qty"] == 22.0, \
        f"koruma satış dolumu sahiplik sayıldı: closed_qty={res['closed_qty']}"
    assert [s[2] for s in sira if s[0] == "DELETE"] == ["22"]


def test_B4_kuyruk_alarmi_cancel_failed_tasir_ve_kuyruk_durur(ayna, monkeypatch):
    """YASA-6 okuyucusu: `cancel_failed` alanını `_mirror_exit_sync` alarma taşır; kuyruk düşmez
    (bir sonraki tur yeniden dener). POZİTİF KONTROL: alan False iken alarmda False görünür."""
    monkeypatch.setattr(alpaca, "close_engine_position",
                        lambda t, plan_id=None: {"ok": False, "owned": True, "naked": False,
                                                 "cancel_failed": True, "cancelled": [],
                                                 "detail": "1 emir iptali başarısız … DENENMEDİ"})
    meta = {"mirror_exit_pending": {"AMGN": {"plan_id": "P-2026-08-05-AMGN",
                                             "reason": "time_stop", "tries": 0}}}
    out = loop._mirror_exit_sync(meta, "2026-08-10")
    assert out["failed"] and meta["mirror_exit_pending"]["AMGN"]["tries"] == 1
    ev = [e for e in _events("MIRROR_DRIFT") if e.get("ticker") == "AMGN"]
    assert ev and ev[-1].get("cancel_failed") is True, "kapının kararı alarm satırında okunmuyor"
    assert ev[-1].get("drift_sinifi") == "cikis_yetimi"


# =================================================================================================
# B3 · KORUMA DOLUMU → KİTAP KAPANIŞI + DOĞRU SINIF (split_brain DEĞİL)
# =================================================================================================
def _ayna_tel(monkeypatch, emirler, pozisyonlar):
    monkeypatch.setattr(alpaca, "orders", lambda **k: [copy.deepcopy(o) for o in emirler])
    monkeypatch.setattr(alpaca, "positions", lambda: [dict(p) for p in pozisyonlar])


def _acik_poz(sym="NUE", qty=25.0):
    return {sym: {"qty": qty, "scaled_out": False, "plan_id": f"P-2026-08-05-{sym}"}}


def test_B3_koruma_stop_dolumu_kitaba_KAPANIS_olarak_islenir(ayna, monkeypatch):
    """ÇEKİRDEK: koruma STOP bacağı doldu (fiyat legs'ten) → iç kitap `koruma_stop` ile kapanır
    (kendi maliyet modeliyle), satır GERÇEK dolumu `alpaca_fill_price` olarak taşır, alarm
    `koruma_dolumu` sınıfını basar ve `split_brain` HİÇ ötmez."""
    b = _kitap("NUE", qty=25, entry=150.0)
    _ayna_tel(monkeypatch, [_giris_parent("NUE", 25),
                            _koruma_oco("NUE", 25, 141.0, 172.0, stop_dolum=141.0)], [])

    out = loop.reconcile_broker_state({"armed": []}, "2026-08-10", b.closed,
                                      open_positions=_acik_poz(), fill_eq_now=100000.0, broker=b)

    kd = out["positions"]["koruma_dolumu"]
    assert len(kd) == 1 and kd[0]["ticker"] == "NUE" and kd[0]["bacak"] == "stop"
    assert kd[0]["fiyat"] == 141.0 and kd[0]["kitap"] == "kapatildi"
    assert out["positions"]["missing_on_alpaca"] == [], "koruma dolumu hâlâ kayıp-pozisyon sayılıyor"
    assert "NUE" not in b.positions, "iç kitap kapanmadı — hayalet pozisyon yönetilmeye devam eder"
    row = b.closed[-1]
    assert row["exit_reason"] == "koruma_stop"
    assert row["exit"] == pytest.approx(141.0 * (1 - b.slip), rel=1e-9), \
        "kitap kendi maliyet modelinden geçmedi (iki-motor deseni: dokunuş çıkışıyla aynı)"
    assert row["alpaca_fill_price"] == 141.0, "GERÇEK dolum fiyatı satırda değil — B3'ün özü buydu"
    assert row["mirror_divergence"] == pytest.approx(b.slip / (1 - b.slip), rel=1e-3)
    diskte = [r for r in store.read_jsonl("trades.jsonl") if r.get("ticker") == "NUE"]
    assert len(diskte) == 1 and diskte[0]["exit_reason"] == "koruma_stop" \
        and diskte[0]["alpaca_fill_price"] == 141.0, "kapanış deftere kalıcı yazılmadı"
    ev = _events("MIRROR_DRIFT")
    assert any(e.get("drift_sinifi") == "koruma_dolumu" and e.get("islendi") is True for e in ev)
    assert not any(e.get("drift_sinifi") == "split_brain" for e in ev), \
        "yanlış sınıf hâlâ basılıyor — B3'ün alarm yarısı kapanmadı"


def test_B3_hedef_dolumu_koruma_hedef_tipiyle_islenir(ayna, monkeypatch):
    """OCO'nun ÖTEKİ şekli: HEDEF (primary limit) doldu — fiyat primary'nin kendisinden okunur
    (`exit_fill_price` bunu göremezdi: o yalnız legs okur; `koruma_fill` tam bu yüzden var)."""
    b = _kitap("NUE", qty=25, entry=150.0)
    _ayna_tel(monkeypatch, [_giris_parent("NUE", 25),
                            _koruma_oco("NUE", 25, 141.0, 172.0, hedef_dolum=172.0)], [])
    out = loop.reconcile_broker_state({"armed": []}, "2026-08-10", b.closed,
                                      open_positions=_acik_poz(), fill_eq_now=100000.0, broker=b)
    kd = out["positions"]["koruma_dolumu"][0]
    assert (kd["bacak"], kd["fiyat"], kd["exit_tipi"]) == ("hedef", 172.0, "koruma_hedef")
    assert b.closed[-1]["exit_reason"] == "koruma_hedef"
    assert b.closed[-1]["alpaca_fill_price"] == 172.0


def test_B3_fiyat_okunamiyorsa_UYDURMA_YOK_kitap_bekler(ayna, monkeypatch):
    """UYDURMA YASAĞI: dolum var ama `filled_avg_price` boş → fiyat None + neden (0 DEĞİL),
    kitaba İŞLENMEZ (pozisyon açık kalır, defter satırı düşmez), sınıf yine `koruma_dolumu`
    (split_brain'e GERİ DÜŞMEZ) ve bir sonraki tur yeniden dener."""
    b = _kitap("NUE", qty=25, entry=150.0)
    oco = _koruma_oco("NUE", 25, 141.0, 172.0, stop_dolum=141.0)
    oco["legs"][0]["filled_avg_price"] = ""                    # dolum var, fiyat alanı boş
    _ayna_tel(monkeypatch, [_giris_parent("NUE", 25), oco], [])
    out = loop.reconcile_broker_state({"armed": []}, "2026-08-10", b.closed,
                                      open_positions=_acik_poz(), fill_eq_now=100000.0, broker=b)
    kd = out["positions"]["koruma_dolumu"][0]
    assert kd["fiyat"] is None and kd["kitap"].startswith("islenmedi:")
    assert "NUE" in b.positions and b.closed == [], "fiyatsız dolum kitaba uydurma fiyatla işlendi"
    assert [r for r in store.read_jsonl("trades.jsonl") if r.get("ticker") == "NUE"] == []
    ev = [e for e in _events("MIRROR_DRIFT") if e.get("drift_sinifi") == "koruma_dolumu"]
    assert ev and ev[-1].get("fiyat") is None and ev[-1].get("islendi") is False
    assert len(str(ev[-1].get("neden") or "")) >= 20, "işlenememe nedeni yazılmamış (YASA-4)"
    assert not any(e.get("drift_sinifi") == "split_brain" for e in _events("MIRROR_DRIFT"))


def test_B3_brokersiz_cagiran_SINIFI_yine_dogru_koyar(ayna, monkeypatch):
    """GERİYE UYUM: eski imzalı çağıran (broker geçilmez) bozulmaz — dolum yine `koruma_dolumu`
    sınıflanır (split_brain değil), kitaplama nedenli olarak bir sonraki günlük tura kalır."""
    _ayna_tel(monkeypatch, [_giris_parent("NUE", 25),
                            _koruma_oco("NUE", 25, 141.0, 172.0, stop_dolum=141.0)], [])
    out = loop.reconcile_broker_state({"armed": []}, "2026-08-10", [],
                                      open_positions=_acik_poz(), fill_eq_now=100000.0)
    kd = out["positions"]["koruma_dolumu"][0]
    assert kd["kitap"].startswith("islenmedi:") and "broker" in kd["kitap"]
    assert not any(e.get("drift_sinifi") == "split_brain" for e in _events("MIRROR_DRIFT"))


def test_B3_dolmamis_koruma_split_brain_POZITIF_KONTROL(ayna, monkeypatch):
    """Tespit DOLUM ister, sınıf etiketi yetmez: koruma emri var ama dolmamış (süpürülmüş/iptal,
    filled_qty=0) → gerçek durum ayrışmasıdır, `split_brain` AYNEN öter. Üstteki iddialar bir şey
    ölçüyor — koruma varlığı tek başına split_brain'i yutmuyor."""
    b = _kitap("NUE", qty=25, entry=150.0)
    olu = _koruma_oco("NUE", 25, 141.0, 172.0)
    olu["status"] = "canceled"
    olu["legs"][0]["status"] = "canceled"
    _ayna_tel(monkeypatch, [_giris_parent("NUE", 25), olu], [])
    out = loop.reconcile_broker_state({"armed": []}, "2026-08-10", b.closed,
                                      open_positions=_acik_poz(), fill_eq_now=100000.0, broker=b)
    assert out["positions"]["missing_on_alpaca"] == ["NUE"]
    assert out["positions"]["koruma_dolumu"] == []
    assert any(e.get("drift_sinifi") == "split_brain" for e in _events("MIRROR_DRIFT"))
    assert "NUE" in b.positions, "dolumsuz korumada kitap kapatıldı — uydurma kapanış"


def test_B3_ikinci_tur_idempotent_alarm_tekrarlamaz(ayna, monkeypatch):
    """Kapanış işlendikten SONRA sembol iç kitapta yoktur → ikinci reconcile turu ne yeni satır
    ne yeni koruma_dolumu alarmı üretir (tek dolum = tek kapanış)."""
    b = _kitap("NUE", qty=25, entry=150.0)
    emirler = [_giris_parent("NUE", 25), _koruma_oco("NUE", 25, 141.0, 172.0, stop_dolum=141.0)]
    _ayna_tel(monkeypatch, emirler, [])
    loop.reconcile_broker_state({"armed": []}, "2026-08-10", b.closed,
                                open_positions=_acik_poz(), fill_eq_now=100000.0, broker=b)
    n_alarm = len([e for e in _events("MIRROR_DRIFT") if e.get("drift_sinifi") == "koruma_dolumu"])
    n_satir = len(store.read_jsonl("trades.jsonl"))
    out2 = loop.reconcile_broker_state({"armed": []}, "2026-08-11", b.closed,
                                       open_positions={t: {"qty": p.qty, "scaled_out": p.scaled_out,
                                                           "plan_id": p.plan_id}
                                                       for t, p in b.positions.items()},
                                       fill_eq_now=100000.0, broker=b)
    assert out2["positions"]["koruma_dolumu"] == []
    assert len([e for e in _events("MIRROR_DRIFT")
                if e.get("drift_sinifi") == "koruma_dolumu"]) == n_alarm
    assert len(store.read_jsonl("trades.jsonl")) == n_satir


# =================================================================================================
# Y · YASA — SINIF HÜKMÜ TEK YERDEN, KABLO CANLI YOLDA
# =================================================================================================
def test_Y1_sinif_hukmu_KOPYALANMADI_yeniden_kullanildi():
    """v220 yasası: bir emrin koruma olup olmadığına TEK yer karar verir (`coid_sinifi`). Ne
    `close_engine_position` ne reconcile yardımcısı kendi önek/yön süzgecini kurar."""
    kapatan = inspect.getsource(alpaca.close_engine_position)
    assert "coid_sinifi(" in kapatan, "kapatma yolu sınıf hükmünü tek kaynaktan okumuyor"
    assert "KORUMA_COID_ONEK" not in kapatan and "startswith" not in kapatan.replace(
        "startswith(ENGINE_COID_PREFIX)", ""), "kapatma yolu kendi önek süzgecini kurmuş (kopya)"
    bulucu = inspect.getsource(loop._koruma_dolumu_bul)
    assert "coid_sinifi" in bulucu and "koruma_fill" in bulucu
    assert "P-KORUMA" not in bulucu, "reconcile önek metnini elle yazmış — v220 çarpışması geri gelir"


def test_Y2_canli_yol_kablolu_reconcile_kitabi_aliyor():
    """Kablo kanıtı: `daily_cycle` reconcile'a kitabın kendisini (`broker=b`) geçiriyor — B3
    kitaplaması canlı yolda gerçekten çalışır durumda (mekanizma ölü doğmadı)."""
    src = inspect.getsource(loop.daily_cycle)
    assert "broker=b" in src, "reconcile kitapsız çağrılıyor — koruma dolumu kitaba işlenemez"


def test_Y3_koruma_fill_yalniz_okur_hukum_vermez():
    """`koruma_fill` sınıf hükmü vermez (tek hüküm noktası ilkesi) ve kısmi-dolum-sonrası-iptal
    hâlini (`canceled` + filled_qty>0) DOLUM sayar — yalnız statüye bakmak onu kaçırırdı.

    Docstring HARİÇ tutulur (v161/C8 deseni): hükmün NEREDE yaşadığını anlatmak serbest, yasak
    olan KODUN kendisinin hüküm vermesidir."""
    import ast as _ast
    fn = _ast.parse(inspect.getsource(alpaca.koruma_fill).lstrip()).body[0]
    govde = fn.body[1:] if (isinstance(fn.body[0], _ast.Expr)
                            and isinstance(fn.body[0].value, _ast.Constant)) else fn.body
    kod = "\n".join(_ast.unparse(n) for n in govde)
    for yasak in ("coid_sinifi", "is_koruma_order", "KORUMA_COID_ONEK"):
        assert yasak not in kod, f"okuma ucu hüküm vermeye başlamış: {yasak}"
    kismi = {"id": "x", "status": "canceled", "type": "stop", "filled_qty": "7",
             "filled_avg_price": "140.5"}
    kf = alpaca.koruma_fill({"id": "p", "status": "canceled", "filled_qty": "0",
                             "type": "limit", "legs": [kismi]})
    assert kf is not None and kf["bacak"] == "stop" and kf["price"] == 140.5
    assert alpaca.koruma_fill({"id": "p", "status": "new", "filled_qty": "0",
                               "type": "limit", "legs": []}) is None

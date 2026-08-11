"""test_kovab_icra_v161.py — KOVA-B icra güvenliği (denetim 2026-08-02: C9 / C23 / C8).

ÜÇ BULGU, ÜÇ SINIF:
  C9  — iç motorun ÇIKIŞ kararı (time_stop/regime_flip/giveback/erken-itlaf) aynaya HİÇ
        iletilmiyordu: iç defter kapanıyor, aynadaki bracket AÇIK kalıyor, sembol kalıcı yetim
        oluyor ve `_mirror_busy` üzerinden bir daha karar üretilmiyordu.
  C23 — silahlı planlar HALT/breaker/veri/kısma dallarında OLAYSIZ düşüyordu (ne olay, ne E2
        satırı, ne `broker_status`), ve HALT aynadaki dolmamış girişleri iptal etmiyordu.
  C8  — pano "gönder" düğmesi kendi çıplak `submit_plan` yolunu kuruyordu: de-risk çarpanı yok,
        entry_law girdileri yok, dedup yok, E2 satırı yok, unreachable reddi yok.

YÖNTEM: hiçbir test ağa çıkmaz — `httpx` ve adaptörün okuma uçları saplanır. Her iddianın yanında
bir POZİTİF KONTROL vardır (sınır bilerek delinir ve iddianın GERÇEKTEN düştüğü gösterilir);
düşmeyen bir iddia koruma değil dekordur.
"""
from __future__ import annotations

import ast
import inspect
import pathlib

import pytest

from meridian import config, health, loop, obs, store
from meridian.adapters import alpaca

REPO = pathlib.Path(config.__file__).resolve().parent.parent

FAKE_KEY = "PKKOVABFAKEKEY7788990011"
FAKE_SECRET = "SKKOVABFAKESECRET2233445566778899"


@pytest.fixture
def paper(sandbox_state, monkeypatch):
    """Sahte kimlik + `alpaca_paper` arka ucu; taşıma SAĞLIKLI kabul edilir."""
    from meridian import secrets as secrets_mod
    monkeypatch.setenv("ALPACA_PAPER_KEY", FAKE_KEY)
    monkeypatch.setenv("ALPACA_PAPER_SECRET", FAKE_SECRET)
    monkeypatch.delenv("MERIDIAN_GCP_PROJECT", raising=False)
    secrets_mod.clear_cache()
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    alpaca._note(True)
    yield sandbox_state
    secrets_mod.clear_cache()
    alpaca._note(True)


class _Resp:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeClient:
    """Alpaca yerine geçen sahte istemci: her çağrıyı KAYDEDER, hiçbir şey göndermez."""

    def __init__(self, delete_status=200):
        self.calls: list = []
        self.delete_status = delete_status

    def delete(self, url, **kw):
        self.calls.append(("DELETE", url, kw.get("params")))
        return _Resp(self.delete_status, {"message": "close refused"} if self.delete_status >= 400 else {})

    def get(self, url, **kw):
        self.calls.append(("GET", url, kw.get("params")))
        return _Resp(200, [])

    def post(self, url, **kw):
        self.calls.append(("POST", url, kw.get("json")))
        return _Resp(200, {"id": "o1"})


def _events(token: str) -> list:
    return [e for e in store.read_jsonl("events.jsonl") if token in str(e)]


def _e2_rows() -> list:
    return store.read_jsonl(loop.ENTRY_LEDGER)


# =================================================================================================
# C9 — İÇ ÇIKIŞ → AYNA KAPATMA (sahiplik önekli), kapatma hatası → olay + yeniden deneme
# =================================================================================================
_OWNED_PARENT = {"id": "parent-1", "symbol": "NVDA", "client_order_id": "P-2026-08-01-NVDA",
                 "status": "filled", "filled_qty": "40",
                 "legs": [{"id": "leg-tp", "type": "limit", "status": "new"},
                          {"id": "leg-sl", "type": "stop", "status": "held"}]}


def _wire_owned(monkeypatch, client, pos_qty="40"):
    monkeypatch.setattr(alpaca, "orders", lambda **k: [dict(_OWNED_PARENT)])
    monkeypatch.setattr(alpaca, "positions", lambda: [{"symbol": "NVDA", "qty": pos_qty}])
    monkeypatch.setattr(alpaca, "httpx", client)


def test_c9_internal_exit_closes_the_mirror_bracket(paper, monkeypatch):
    """İç çıkış uygulandığında AYNA da kapatılmalı: koruma bacakları iptal + pozisyon kapatma."""
    cli = FakeClient()
    iptal = []
    _wire_owned(monkeypatch, cli)
    monkeypatch.setattr(alpaca, "cancel_order", lambda oid: iptal.append(oid) or {"ok": True})

    res = alpaca.close_engine_position("NVDA", plan_id="P-2026-08-01-NVDA")
    assert res["ok"] is True and res["owned"] is True
    assert res["closed_qty"] == 40.0
    assert set(iptal) == {"leg-tp", "leg-sl"}, f"koruma bacakları iptal edilmedi: {iptal}"
    dels = [c for c in cli.calls if c[0] == "DELETE"]
    assert len(dels) == 1 and dels[0][1].endswith("/v2/positions/NVDA")
    assert dels[0][2] == {"qty": "40"}, "adet tavanı yok — operatörün hisseleri de düşebilirdi"


def test_c9_ownership_prefix_is_the_gate(paper, monkeypatch):
    """SAHİPLİK: önekimizi taşımayan emre/pozisyona ASLA dokunulmaz — ne iptal, ne kapatma."""
    cli = FakeClient()
    iptal = []
    yabanci = {"id": "x1", "symbol": "NVDA", "client_order_id": "a1b2-uuid-operator",
               "status": "filled", "filled_qty": "40", "legs": [{"id": "lx", "status": "new"}]}
    monkeypatch.setattr(alpaca, "orders", lambda **k: [yabanci])
    monkeypatch.setattr(alpaca, "positions", lambda: [{"symbol": "NVDA", "qty": "40"}])
    monkeypatch.setattr(alpaca, "httpx", cli)
    monkeypatch.setattr(alpaca, "cancel_order", lambda oid: iptal.append(oid) or {"ok": True})

    res = alpaca.close_engine_position("NVDA", plan_id="P-2026-08-01-NVDA")
    assert res["ok"] is False and res["owned"] is False
    assert iptal == [] and cli.calls == [], "operatörün pozisyonuna DOKUNULDU"

    # POZİTİF KONTROL: aynı kurulumda yalnız önek düzelince yol AÇILIR (test bir şey ölçüyor).
    monkeypatch.setattr(alpaca, "orders", lambda **k: [dict(_OWNED_PARENT)])
    assert alpaca.close_engine_position("NVDA", plan_id="P-2026-08-01-NVDA")["owned"] is True


def test_c9_close_never_exceeds_the_qty_we_own(paper, monkeypatch):
    """Aynadaki pozisyon BİZİM dolumumuzdan büyükse (operatör aynı sembolde) fazlası kapatılmaz."""
    cli = FakeClient()
    _wire_owned(monkeypatch, cli, pos_qty="140")      # 40 bizim, 100 operatörün
    monkeypatch.setattr(alpaca, "cancel_order", lambda oid: {"ok": True})
    res = alpaca.close_engine_position("NVDA", plan_id="P-2026-08-01-NVDA")
    assert res["closed_qty"] == 40.0
    assert [c[2] for c in cli.calls if c[0] == "DELETE"] == [{"qty": "40"}]


def test_c9_failed_close_writes_an_event_and_stays_queued_for_retry(paper, monkeypatch):
    """Kapatma DÜŞERSE: alarm + kuyrukta KALIR (kalıcı sessiz yetim YOK) + sonraki turda yeniden dener."""
    cli = FakeClient(delete_status=422)
    _wire_owned(monkeypatch, cli)
    monkeypatch.setattr(alpaca, "cancel_order", lambda oid: {"ok": True})

    meta = {"mirror_exit_pending": {"NVDA": {"plan_id": "P-2026-08-01-NVDA",
                                             "reason": "time_stop", "since": "2026-08-01",
                                             "tries": 0, "naked": False}}}
    out = loop._mirror_exit_sync(meta, "2026-08-02")
    assert out["closed"] == [] and len(out["failed"]) == 1
    assert meta["mirror_exit_pending"]["NVDA"]["tries"] == 1, "yeniden deneme sayacı ilerlemedi"
    assert meta["mirror_exit_pending"]["NVDA"]["naked"] is True, \
        "koruma bacağı iptal edildi ama 'çıplak' beyanı yazılmadı"
    alarmlar = _events("MIRROR_DRIFT")
    assert alarmlar, "kapatma hatası SESSİZ — olay defterinde iz yok"
    assert any("ÇIPLAK" in str(e) for e in alarmlar), "çıplak pencere beyan edilmiyor"

    # YENİDEN DENEME: bir sonraki turda ikinci kez denenir ve bu kez başarır → kuyruk boşalır.
    cli.delete_status = 200
    out2 = loop._mirror_exit_sync(meta, "2026-08-03")
    assert [c["ticker"] for c in out2["closed"]] == ["NVDA"]
    assert out2["closed"][0]["tries"] == 2, "deneme sayacı turlar arası taşınmıyor"
    assert meta["mirror_exit_pending"] == {}, "başarılı kapatma kuyruktan düşmedi"


def test_c9_exit_orphan_is_classified_apart_and_leaves_mirror_busy(paper, monkeypatch):
    """Çıkış yetimi split-brain yetiminden AYRI sınıflanır ve `engine_orphans`ta görünmez —
    `_mirror_busy` yalnız `engine_orphans`ı okuduğu için sembol kalıcı olarak karar dışı kalmaz."""
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(alpaca, "orders", lambda **k: [
        {"id": "p1", "symbol": "NVDA", "client_order_id": "P-1-NVDA", "status": "filled",
         "filled_qty": "10", "legs": []},
        {"id": "p2", "symbol": "AMD", "client_order_id": "P-1-AMD", "status": "filled",
         "filled_qty": "10", "legs": []}])
    monkeypatch.setattr(alpaca, "positions", lambda: [{"symbol": "NVDA", "qty": "10"},
                                                      {"symbol": "AMD", "qty": "10"}])
    meta = {"armed": [], "mirror_exit_pending": {"NVDA": {"plan_id": "P-1-NVDA",
                                                          "reason": "time_stop", "tries": 3}}}
    out = loop.reconcile_broker_state(meta, "2026-08-02", [], open_positions={})
    assert out["positions"]["exit_orphans"] == ["NVDA"]
    assert out["positions"]["engine_orphans"] == ["AMD"], \
        "split-brain yetimi çıkış yetimiyle aynı kovaya düştü — iki teşhis okunamaz hâle gelir"
    assert any("çıkış yetimi" in str(e) for e in _events("MIRROR_DRIFT"))

    # `_mirror_busy` kaynağının SÖZLEŞMESİ: yalnız engine_orphans + alive_order_syms okunur.
    src = inspect.getsource(loop.daily_cycle)
    i = src.index("_mirror_busy = ")
    assert "engine_orphans" in src[i:i + 260] and "exit_orphans" not in src[i:i + 260]


def test_c9_exit_path_is_wired_and_touch_exits_are_not(paper):
    """time_stop/regime_flip yolu (pending_exits) aynaya bağlanmalı; intraday TP/SL dokunuş
    çıkışları BAĞLANMAMALI — aynanın kendi bacakları onları zaten doldurur (çift satış olurdu)."""
    src = inspect.getsource(loop.daily_cycle)
    i = src.index('meta.get("pending_exits", {}).items()')
    assert "_mirror_exit_enqueue(" in src[i:i + 700], "çıkış kararı ayna kuyruğuna yazılmıyor"
    assert "_mirror_exit_sync(" in src[i:i + 900], "kuyruk hiç boşaltılmıyor"
    j = src.index("b._touch_exit(")
    assert "_mirror_exit_enqueue" not in src[j:j + 500], \
        "dokunuş çıkışı aynaya iletiliyor — bracket bacağıyla ÇİFT satış riski"


def test_c9_queue_survives_restart(paper):
    """Kuyruk portfolio.json'a yazılmazsa yeniden başlatma sessizce kalıcı yetim üretir."""
    assert f'{loop.MIRROR_EXIT_KEY}: meta.get({loop.MIRROR_EXIT_KEY}' in \
        inspect.getsource(loop._save_broker).replace("MIRROR_EXIT_KEY", loop.MIRROR_EXIT_KEY) or \
        "MIRROR_EXIT_KEY" in inspect.getsource(loop._save_broker)
    from meridian.broker import PaperBroker
    b = PaperBroker(100_000.0, 5, 0.0)
    loop._save_broker(b, {"mirror_exit_pending": {"NVDA": {"plan_id": "P-1", "tries": 2}}})
    assert store.read_json("portfolio.json", {})["mirror_exit_pending"]["NVDA"]["tries"] == 2


def test_c9_internal_broker_mode_never_enqueues(sandbox_state, monkeypatch):
    """İç-broker modunda davranış BİREBİR eskisi: kuyruk hiç doğmaz."""
    monkeypatch.setattr(config, "BROKER", "internal")
    meta: dict = {}
    loop._mirror_exit_enqueue(meta, "NVDA", "P-1", "time_stop", "2026-08-02")
    assert meta == {}
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")          # POZİTİF KONTROL
    loop._mirror_exit_enqueue(meta, "NVDA", "P-1", "time_stop", "2026-08-02")
    assert meta[loop.MIRROR_EXIT_KEY]["NVDA"]["reason"] == "time_stop"


# =================================================================================================
# C23 — KAPI-DIŞI DÜŞÜRME ARTIK SESSİZ DEĞİL + HALT AYNAYI İPTAL EDER
# =================================================================================================
def _armed(n=2):
    return [{"id": f"P-2026-08-01-T{i}", "date": "2026-08-01", "ticker": f"T{i}",
             "entry_trigger": 10.0 + i} for i in range(n)]


@pytest.mark.parametrize("gate", ["halt", "breaker", "data_bad", "throttle"])
def test_c23_dropped_armed_plan_gets_event_e2_row_and_broker_status(paper, monkeypatch, gate):
    """Düşen HER silahlı plan: olay + E2 satırı + `broker_status` damgası. Üçü birden."""
    monkeypatch.setattr(alpaca, "cancel_open_entries",
                        lambda: {"cancelled": [], "kept": [], "foreign": []})
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    meta = {"armed": _armed(2)}
    store.merge_dated_jsonl("trade_plans.jsonl", "2026-08-01",
                            [dict(p) for p in meta["armed"]])

    loop._armed_dropped_by_gate(meta, "2026-08-02", gate)

    assert all(p["broker_status"] == f"armed_dropped_{gate}" for p in meta["armed"])
    olaylar = _events("armed_dropped")
    assert len([e for e in olaylar if e.get("event") == "armed_dropped"]) == 2
    rows = [r for r in _e2_rows() if r.get("karar") == f"armed_dropped_{gate}"]
    assert len(rows) == 2, "E2 defterinde düşen planların satırı yok"
    assert {r["motor"] for r in rows} == {"kapi"}, \
        "düşen plan iç/ayna icra kovasına yazıldı — kill-ölçütünün paydası kayar"
    diskte = [r for r in store.read_jsonl("trade_plans.jsonl") if r.get("date") == "2026-08-01"]
    assert len(diskte) == 2, "damga yazılırken aynı günün diğer plan satırları silindi"
    assert {r.get("broker_status") for r in diskte} == {f"armed_dropped_{gate}"}, \
        "damga KALICI değil — plan defterinden kaybolma sebebi okunamaz"


def test_c23_halt_and_breaker_cancel_the_mirror_entries(paper, monkeypatch):
    """HALT/breaker aynadaki DOLMAMIŞ girişleri de kapatmalı; veri/kısma dalı KAPATMAMALI
    (o dallar 'bugün doldurma' der, 'emri geri çek' demez — yetki genişletmesi olurdu)."""
    cagrilar = []
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(alpaca, "cancel_open_entries",
                        lambda: cagrilar.append("cancel") or {"cancelled": [{"symbol": "T0"}],
                                                              "kept": [], "foreign": []})
    for gate in ("data_bad", "throttle"):
        loop._armed_dropped_by_gate({"armed": _armed(1)}, "2026-08-02", gate)
    assert cagrilar == [], "veri/kısma dalı ayna emrini iptal etti (yetki genişledi)"

    for gate in ("halt", "breaker"):
        loop._armed_dropped_by_gate({"armed": _armed(1)}, "2026-08-02", gate)
    assert cagrilar == ["cancel", "cancel"], "HALT/breaker aynadaki canlı girişi iptal etmiyor"
    assert _events("mirror_entries_cancelled"), "iptal olay defterine geçmiyor"


def test_c23_halt_cancels_even_with_no_armed_plans(paper, monkeypatch):
    """Ayna emri D-1 akşamından kalmış olabilir: silahlı plan olmasa DA HALT iptali koşmalı."""
    cagrilar = []
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(alpaca, "cancel_open_entries",
                        lambda: cagrilar.append(1) or {"cancelled": [], "kept": [], "foreign": []})
    loop._armed_dropped_by_gate({"armed": []}, "2026-08-02", "halt")
    assert cagrilar == [1]


def test_c23_cancel_path_keeps_the_ownership_filter(paper, monkeypatch):
    """İptal ADAPTÖRÜN denetlenmiş yolundan geçmeli — döngü kendi çıplak iptalini kurmamalı."""
    src = inspect.getsource(loop._cancel_mirror_entries)
    assert "alpaca.cancel_open_entries()" in src
    for yasak in ("httpx", "cancel_order(", "close_all"):
        assert yasak not in src, f"döngü sahiplik süzgecini atlayan bir iptal yolu kurdu: {yasak}"


def test_c23_gate_branch_is_wired_and_the_decision_is_unchanged(paper):
    """İKİ-MOTOR YASASI: bu tur yalnız GÖZLEMİ kabloladı — plan yine düşer (`carried` boş kalır)."""
    src = inspect.getsource(loop.daily_cycle)
    assert "_armed_dropped_by_gate(meta, dstr, _kapi)" in src
    # KARAR AYNI: kapı kapalıyken `carried` boş kalır ve `armed` ona eşitlenir (plan yine düşer).
    assert src.index("carried = []") < src.index("_kapi = ("), "düşürme kararı değişmiş olabilir"
    assert 'meta["armed"] = carried' in src
    # düşürme dalı, silahlanma tavanı/hesabı gibi KARAR girdilerine dokunmamalı
    i = src.index("else:\n            _armed_dropped_by_gate")
    assert "fill_entry" not in src[i:i + 200] and "carried =" not in src[i:i + 200]


def test_c23_per_plan_drop_is_no_longer_silent(paper):
    """Slot dolu / sembol zaten defterde → plan düşer; bu dalın else'i YOKTU."""
    src = inspect.getsource(loop.daily_cycle)
    i = src.index("if len(b.positions) < eff_max_open and t not in b.positions:")
    dal = src[i:src.index("_armed_dropped_by_gate")]
    assert "_armed_drop_row(plan, dstr," in dal, "plan-başı düşürme hâlâ sessiz"
    assert "slot_full" in dal and "already_open" in dal
    assert "_stamp_plan_status(_dusen)" in dal, "plan-başı düşürmenin damgası kalıcı değil"


# =================================================================================================
# C8 — PANO DÜĞMESİ İLE DÖNGÜ AYNI GÖNDERİM KAPISINDAN GEÇER
# =================================================================================================
def test_c8_both_callers_use_the_same_submit_function():
    """AST KANITI: ne döngü ne uç nokta `alpaca.submit_plan`i DOĞRUDAN çağırır; ikisi de
    `loop.mirror_submit_armed`ı çağırır. Tek kapı yoksa iki farklı yasa demektir."""
    cagiranlar = {}
    for rel in ("meridian/loop.py", "meridian/api.py"):
        tree = ast.parse((REPO / rel).read_text())
        dogrudan, kapi = [], []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            if isinstance(f, ast.Attribute) and f.attr == "submit_plan":
                dogrudan.append(node.lineno)
            # İŞ-2-EOD (2026-08-11, BEYANLI güncelleme): tek kapının DIŞ katmanı artık
            # `mirror_submit_ve_kalicilastir` (gönderim + kilit-altı kalıcılaştırma tek gövdede;
            # onay anı + intraday 4b + pano ucu aynı yolu paylaşır). Sözleşme GEVŞEMEDİ,
            # GENİŞLEDİ: pano ucu ya iç kapıyı ya sarmalayıcısını çağırmalı; sarmalayıcının
            # kendisinin iç kapıyı çağırdığı aşağıda AYRICA çivili.
            if (isinstance(f, ast.Attribute) and f.attr in ("mirror_submit_armed",
                                                            "mirror_submit_ve_kalicilastir")) or \
                    (isinstance(f, ast.Name) and f.id in ("mirror_submit_armed",
                                                          "mirror_submit_ve_kalicilastir")):
                kapi.append(node.lineno)
        cagiranlar[rel] = (dogrudan, kapi)
    # loop.py'de tek `submit_plan` çağrısı ORTAK FONKSİYONUN İÇİNDEDİR; api.py'de hiç olmamalı.
    assert cagiranlar["meridian/api.py"][0] == [], \
        f"pano ucu hâlâ çıplak submit_plan çağırıyor: {cagiranlar['meridian/api.py'][0]}"
    assert cagiranlar["meridian/api.py"][1], "pano ucu ortak gönderim kapısını çağırmıyor"
    assert cagiranlar["meridian/loop.py"][1], "döngü ortak gönderim kapısını çağırmıyor"
    sp = inspect.getsource(loop.mirror_submit_armed)
    assert "alpaca.submit_plan(" in sp, "gönderim mantığı ortak fonksiyonda değil"
    sarmal = inspect.getsource(loop.mirror_submit_ve_kalicilastir)
    assert "mirror_submit_armed(" in sarmal, \
        "sarmalayıcı iç kapıyı çağırmıyor — ikinci bir gönderim gövdesi doğmuş demektir"


def test_c8_endpoint_applies_derisk_dedup_and_writes_e2(paper, monkeypatch):
    """Uç noktadan geçen gönderim: de-risk çarpanı UYGULANIR, dedup ÇALIŞIR, E2 satırı DÜŞER."""
    from fastapi.testclient import TestClient
    from meridian import api

    gorulen: list = []

    def _fake_submit(plan, equity, size_mult=1.0, atr=None, ref_price=None):
        gorulen.append({"id": plan["id"], "size_mult": size_mult, "atr": atr, "ref_price": ref_price})
        return {"ok": True, "qty": 5, "law": {"limit": 10.1, "mode": "stop_limit", "tif": "day"}}

    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(alpaca, "account", lambda: {"equity": "100000"})
    monkeypatch.setattr(alpaca, "submit_plan", _fake_submit)
    monkeypatch.setattr(health, "halted", lambda: False)
    monkeypatch.setattr(api, "DASH_TOKEN", "")

    store.write_json("portfolio.json", {
        "armed": [{"id": "P-2026-08-01-T0", "date": "2026-08-01", "ticker": "T0",
                   "entry_trigger": 10.0}],
        "alpaca_submitted": [], "peak_equity": 100_000.0, "last_date": "2026-08-01",
        "entry_law": {"P-2026-08-01-T0": {"atr": 1.25, "ref_price": 9.5}}})
    health.write_heartbeat(equity=95_000.0, last_bar="2026-08-01")

    r = TestClient(api.app).post("/api/alpaca/submit_armed")
    assert r.status_code == 200 and r.json()["submitted"] == 1, r.text
    assert len(gorulen) == 1
    assert gorulen[0]["size_mult"] == pytest.approx(0.6), \
        "de-risk çarpanı uygulanmadı — %5 düşüşte TAM boyut gitti (C8'in ta kendisi)"
    assert gorulen[0]["atr"] == 1.25 and gorulen[0]["ref_price"] == 9.5, \
        "entry_law girdileri geçmedi — aynı planda iki farklı limit tavanı"
    rows = [r for r in _e2_rows() if r.get("motor") == "ayna"]
    assert len(rows) == 1 and rows[0]["karar"] == "submitted" and rows[0]["kaynak"] == "pano"

    # DEDUP: kimlik portfolio.json'a KALICI yazıldı → ikinci tık aynı emri tekrar göndermez.
    assert store.read_json("portfolio.json", {})["alpaca_submitted"] == ["P-2026-08-01-T0"]
    r2 = TestClient(api.app).post("/api/alpaca/submit_armed")
    assert r2.json()["submitted"] == 0 and len(gorulen) == 1, "aynı plan ikinci kez gönderildi"


def test_c8_endpoint_refuses_when_the_internal_equity_is_unmeasurable(paper, monkeypatch):
    """UYDURMA YASAĞI: de-risk çarpanı ölçülemiyorsa gönderim REDDEDİLİR — 1.0 varsayılmaz."""
    cagri = []
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(alpaca, "account", lambda: {"equity": "100000"})
    monkeypatch.setattr(alpaca, "submit_plan", lambda *a, **k: cagri.append(1) or {"ok": True})
    store.write_json("portfolio.json", {"armed": [{"id": "P-1", "ticker": "T0",
                                                   "entry_trigger": 10.0}],
                                        "peak_equity": 100_000.0})
    meta = store.read_json("portfolio.json", {})
    out = loop.mirror_submit_armed(meta, "2026-08-02", halted=False, source="pano")
    assert out["ok"] is False and "ÖLÇÜLEMEZ" in out["detail"]
    assert cagri == [], "öz sermaye ölçülemezken emir gitti"

    health.write_heartbeat(equity=100_000.0, last_bar="2026-08-01")     # POZİTİF KONTROL
    assert loop.mirror_submit_armed(meta, "2026-08-02", halted=False)["ok"] is True
    assert cagri == [1]


def test_c8_endpoint_refuses_on_halt_and_on_unreachable_mirror(paper, monkeypatch):
    """HALT ve 'ayna ulaşılamıyor' iki AYRI reddir; ikisi de emir göndermez ve planı düşürmez."""
    cagri = []
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    monkeypatch.setattr(alpaca, "submit_plan", lambda *a, **k: cagri.append(1) or {"ok": True})
    meta = {"armed": [{"id": "P-1", "ticker": "T0", "entry_trigger": 10.0}],
            "peak_equity": 100_000.0}

    assert loop.mirror_submit_armed(meta, "2026-08-02", eq_now=100_000.0,
                                    halted=True)["detail"].startswith("HALT")
    monkeypatch.setattr(alpaca, "account", lambda: None)
    alpaca._note(False, "boom")
    out = loop.mirror_submit_armed(meta, "2026-08-02", eq_now=100_000.0, halted=False)
    alpaca._note(True)
    assert out["ok"] is False and out.get("unreachable") is True
    assert cagri == [], "ulaşılamaz aynaya hayali sermaye üzerinden emir gitti"
    assert len(meta["armed"]) == 1, "ret planı silahlı kümeden düşürdü"


def test_c8_no_100k_constant_leak_left_in_the_endpoint():
    """Eski kaçak: `eq = ... else 100_000.0`. Uç nokta artık kendi sermayesini uydurmuyor.

    Docstring HARİÇ tutulur — kusurun TARİHİ orada yazılı olmalı; yasak olan KODUN kendisidir."""
    from meridian import api
    fn = ast.parse(inspect.getsource(api.api_alpaca_submit_armed).lstrip()).body[0]
    govde = fn.body[1:] if (isinstance(fn.body[0], ast.Expr)
                            and isinstance(fn.body[0].value, ast.Constant)) else fn.body
    kod = "\n".join(ast.unparse(n) for n in govde)
    assert "100_000" not in kod and "100000.0" not in kod, "hayali sermaye sabiti kodda duruyor"
    assert "submit_plan" not in kod, "uç nokta hâlâ kendi gönderim yolunu kuruyor"

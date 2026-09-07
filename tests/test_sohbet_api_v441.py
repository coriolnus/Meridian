"""test_sohbet_api_v441.py — TSK-012 dalga-B / B1 Task 2: `/api/sohbet` uçları + onay genişlemesi.

NE ÇİVİLENİR: auth zorunluluğu · boş mesaj 400 · geçmiş/kota uçları · sohbet önerilerinin
MEVCUT gelen kutusunda görünmesi · MEVCUT onay ucundan verilen kararın MEVCUT icra
fonksiyonlarını çağırması (ikinci onay yolu AÇILMAZ) · Yasa 6: `sohbet.jsonl`in `api.py`de
GERÇEK bir dış okuyucusu var (beyanlı muafiyet DEĞİL).

İcra fonksiyonları MONKEYPATCH'lidir: bu dosya hiçbir plan onaylamaz, hiçbir alarm kapatmaz.
"""
from __future__ import annotations

import inspect

import pytest
from fastapi.testclient import TestClient

from meridian import api, config, notify, sohbet, store


def _kaynak(fn) -> str:
    """Fonksiyonun kaynak metni — "aynı fonksiyon çağrılıyor mu" sorusunun yapısal ölçümü."""
    return inspect.getsource(fn)


@pytest.fixture
def istemci(sandbox_state, monkeypatch) -> TestClient:
    monkeypatch.setattr(api, "DASH_TOKEN", None)
    return TestClient(api.app)


def _seviye(monkeypatch, lvl: int) -> None:
    gercek = dict(config.limits())
    monkeypatch.setattr(config, "limits", lambda: {**gercek, "autonomy_level": lvl})


def _sahte_model(cevap="merhaba"):
    return lambda mesajlar, araclar: {"mesaj": {"content": cevap, "tool_calls": []},
                                      "model": "sahte", "jeton_giris": 3, "jeton_cikis": 4}


def _oneri_yaz(tur="plan_onayi", hedef="P-2026-09-07-MU", oturum="S1") -> str:
    store.append_jsonl("trade_plans.jsonl", {"id": hedef, "ticker": "MU", "date": "2026-09-07",
                                             "gate_verdict": "REVIEW"})
    sohbet._arac_oneri_yaz({"tur": tur, "hedef": hedef, "gerekce": "operatör baksın"},
                           {"oturum": oturum})
    return _son_oneri_id()


def _son_oneri_id() -> str:
    satirlar = [r for r in store.read_jsonl(sohbet.ONAY_DEFTERI) if r.get("kaynak") == "sohbet"]
    assert satirlar, "öneri yazılmadı"
    return satirlar[-1]["id"]


# =================================================================================================
# 1) POST /api/sohbet
# =================================================================================================
def test_post_sohbet_auth_zorunlu(sandbox_state, monkeypatch):
    monkeypatch.setattr(api, "DASH_TOKEN", "gizli-jeton-degeri")
    c = TestClient(api.app)
    assert c.post("/api/sohbet", json={"mesaj": "selam"}).status_code == 401


def test_post_sohbet_cevap_ve_defter_satiri_uretir(istemci, monkeypatch):
    monkeypatch.setattr(sohbet, "_kapi_cagir", _sahte_model("MU planı REVIEW."))
    r = istemci.post("/api/sohbet", json={"mesaj": "MU planı?", "oturum": "S9"})
    assert r.status_code == 200, r.text
    govde = r.json()
    assert govde["cevap"] == "MU planı REVIEW." and govde["oturum"] == "S9"
    assert set(sohbet.DEFTER_ALANLARI) <= set(govde), set(sohbet.DEFTER_ALANLARI) - set(govde)
    assert len(store.read_jsonl(sohbet.SOHBET_DEFTERI)) == 1


def test_post_sohbet_bos_mesaj_400(istemci, monkeypatch):
    monkeypatch.setattr(sohbet, "_kapi_cagir", _sahte_model())
    assert istemci.post("/api/sohbet", json={"mesaj": "   "}).status_code == 400
    assert istemci.post("/api/sohbet", json={}).status_code == 400
    assert store.read_jsonl(sohbet.SOHBET_DEFTERI) == [], "reddedilen mesaj deftere yazıldı"


def test_post_sohbet_oturumsuz_istek_gunun_oturumuna_duser(istemci, monkeypatch):
    monkeypatch.setattr(sohbet, "_kapi_cagir", _sahte_model())
    govde = istemci.post("/api/sohbet", json={"mesaj": "selam"}).json()
    assert govde["oturum"] == sohbet.gunun_oturumu()


# =================================================================================================
# 2) GET /api/sohbet + /api/sohbet/kota
# =================================================================================================
def test_get_sohbet_gecmisi_oturuma_gore_verir(istemci, monkeypatch):
    monkeypatch.setattr(sohbet, "_kapi_cagir", _sahte_model())
    for oturum in ("A", "B", "A"):
        istemci.post("/api/sohbet", json={"mesaj": "selam", "oturum": oturum})
    govde = istemci.get("/api/sohbet", params={"oturum": "A"}).json()
    assert len(govde["gecmis"]) == 2
    assert all(s["oturum"] == "A" for s in govde["gecmis"])
    # KÜNYE: defterin HACMİ (ham satır değil) — pano oturum seçicisi ve kartın seans sayımı için.
    assert govde["kunye"]["n"] == 3 and set(govde["kunye"]["oturumlar"]) == {"A", "B"}
    assert govde["kota"]["tavan"] == 120


def test_get_sohbet_auth_zorunlu(sandbox_state, monkeypatch):
    monkeypatch.setattr(api, "DASH_TOKEN", "gizli-jeton-degeri")
    c = TestClient(api.app)
    assert c.get("/api/sohbet").status_code == 401
    assert c.get("/api/sohbet/kota").status_code == 401


def test_kota_ucu_sayaci_verir(istemci):
    store.append_jsonl(sohbet.CAGRI_DEFTERI, {"ts": sohbet._simdi_iso(), "kind": "sohbet"})
    govde = istemci.get("/api/sohbet/kota").json()
    assert govde["bugun"] == 1 and govde["tavan"] == 120 and govde["kalan"] == 119


# =================================================================================================
# 3) YASA 6 — `sohbet.jsonl`in api.py'de GERÇEK dış okuyucusu var (muafiyet DEĞİL)
# =================================================================================================
def test_sohbet_defterinin_dis_okuyucusu_grafikte_gorunur():
    from meridian import codelaw
    g = codelaw.artifact_graph()
    kayit = g["artifacts"].get(sohbet.SOHBET_DEFTERI)
    assert kayit, "sohbet.jsonl grafikte hiç görünmüyor"
    assert "api.py" in kayit["external_readers"], kayit
    assert sohbet.SOHBET_DEFTERI not in codelaw.DECLARED_SINKS, (
        "muafiyet listesi bir kaçış yoludur ve KAPATILABİLEN yerde kullanılmaz")


def test_defter_adi_api_ile_ayrismaz():
    assert api._SOHBET_DEFTERI == sohbet.SOHBET_DEFTERI


# =================================================================================================
# 4) GELEN KUTUSU — sohbet önerileri MEVCUT `/api/approvals` biçiminde görünür
# =================================================================================================
def test_sohbet_onerisi_gelen_kutusunda_gorunur(istemci, monkeypatch):
    _seviye(monkeypatch, 0)                    # L0'da da görünmeli: sistem bugün L0 kâğıttır
    _oneri_yaz()
    kutu = istemci.get("/api/approvals").json()["inbox"]
    oge = next((o for o in kutu if o.get("type") == "sohbet_onerisi"), None)
    assert oge is not None, kutu
    assert oge["id"] == _son_oneri_id() and oge["tur"] == "plan_onayi"
    assert oge["hedef"] == "P-2026-09-07-MU" and oge["actions"] == ["approve", "reject"]
    assert oge["kaynak"] == "sohbet" and oge["evidence"]


def test_oneri_satiri_BOZUK_KARAR_sayilmaz(sandbox_state):
    """Öneri satırı `decision` taşımaz — onu "kararı okunamayan satır" saymak, öneriyi doğduğu
    anda gelen kutusundan düşürür ve `bozuk` sayacına gerçek olmayan kirlilik yazardı."""
    _oneri_yaz()
    oid = _son_oneri_id()
    t = api._defter_tarama()
    assert oid not in (t["kararlar"] or {}), t["kararlar"]
    assert t["atfedilemeyen"] == 0, t
    # AYRIM DAR KALDI: `decision`ı OLUP okunamayan bir KARAR satırı hâlâ bozuktur.
    store.append_jsonl(api.APPROVALS_LEDGER, {"id": "rev:x", "decision": 7, "ts": "t"})
    assert api._defter_tarama()["kararlar"]["rev:x"]["karar"] == "bozuk"


def test_karar_verilmis_oneri_gelen_kutusunda_beklemez(istemci, monkeypatch):
    _seviye(monkeypatch, 0)
    _oneri_yaz()
    oid = _son_oneri_id()
    monkeypatch.setattr(api, "_sohbet_icra", lambda *a, **k: {"icra": "atlandi"})
    istemci.post(f"/api/approvals/{oid}", json={"decision": "reject", "reason": "gerek yok"})
    kutu = istemci.get("/api/approvals").json()["inbox"]
    assert not [o for o in kutu if o.get("id") == oid], "karar verilmiş öneri hâlâ bekliyor"


# =================================================================================================
# 5) KARAR + İCRA — MEVCUT uç, MEVCUT fonksiyon (İKİNCİ ONAY YOLU YOK)
# =================================================================================================
def test_plan_onayi_onaylandiginda_MEVCUT_fonksiyon_cagrilir(istemci, monkeypatch):
    _seviye(monkeypatch, 0)
    _oneri_yaz()
    oid = _son_oneri_id()
    cagrilar = []
    from meridian import loop as _loop
    monkeypatch.setattr(_loop, "operator_onay_ver",
                        lambda plan_id, **kw: cagrilar.append((plan_id, kw)) or {"ok": True})
    r = istemci.post(f"/api/approvals/{oid}", json={"decision": "approve", "reason": "uygun"})
    assert r.status_code == 200, r.text
    assert cagrilar and cagrilar[0][0] == "P-2026-09-07-MU"
    assert r.json()["icra"]["ok"] is True


def test_ret_kararinda_ICRA_YOK(istemci, monkeypatch):
    _seviye(monkeypatch, 0)
    _oneri_yaz()
    oid = _son_oneri_id()
    cagrilar = []
    from meridian import loop as _loop
    monkeypatch.setattr(_loop, "operator_onay_ver",
                        lambda plan_id, **kw: cagrilar.append(plan_id) or {"ok": True})
    r = istemci.post(f"/api/approvals/{oid}", json={"decision": "reject", "reason": "istemiyorum"})
    assert r.status_code == 200 and cagrilar == [], "RET icra tetikledi"
    assert r.json().get("icra") is None


def test_alarm_ack_onayi_MEVCUT_ACK_fonksiyonunu_cagirir(istemci, monkeypatch):
    _seviye(monkeypatch, 0)
    monkeypatch.setattr(notify, "inbox",
                        lambda limit=60: {"pending": 1, "ack_ts": None, "channel_configured": True,
                                          "groups": [{"token": "DATA_QUALITY", "n": 1,
                                                      "last_ts": "2026-09-07T10:00:00+00:00",
                                                      "message": "m"}]})
    sohbet._arac_oneri_yaz({"tur": "alarm_ack", "hedef": "DATA_QUALITY",
                            "gerekce": "operatör gördü"}, {"oturum": "S1"})
    oid = _son_oneri_id()
    cagrildi = []
    monkeypatch.setattr(api, "_alarm_ack_uygula",
                        lambda **kw: cagrildi.append(kw) or {"acked": True})
    r = istemci.post(f"/api/approvals/{oid}", json={"decision": "approve", "reason": "gördüm"})
    assert r.status_code == 200 and cagrildi, r.text


def test_alarm_ack_TEK_ICRA_GOVDESINDEN_gecer():
    """İKİNCİ ONAY YOLU AÇILMAZ: `/api/alerts/ack` ucu da onay yolu da AYNI fonksiyonu çağırır."""
    assert "_alarm_ack_uygula" in _kaynak(api.api_alerts_ack), (
        "alerts/ack ucu ortak icra gövdesini KULLANMIYOR")
    assert "_alarm_ack_uygula" in _kaynak(api._sohbet_icra)


def test_not_turu_ICRA_URETMEZ(istemci, monkeypatch):
    _seviye(monkeypatch, 0)
    sohbet._arac_oneri_yaz({"tur": "not", "gerekce": "MU'ya dikkat"}, {"oturum": "S1"})
    oid = _son_oneri_id()
    r = istemci.post(f"/api/approvals/{oid}", json={"decision": "approve", "reason": "ok"})
    assert r.status_code == 200
    assert r.json()["icra"]["icra"] == "yok", r.json()

def test_L0da_sohbet_onerisi_403_ALMAZ(istemci, monkeypatch):
    """Sistem bugün L0 kâğıttır; sohbet önerisi L0'da karar alamazsa özellik ÖLÜ doğardı.
    `plan_onayi` icrası zaten L0'da çalışan MEVCUT plan onay yoludur."""
    _seviye(monkeypatch, 0)
    _oneri_yaz()
    from meridian import loop as _loop
    monkeypatch.setattr(_loop, "operator_onay_ver", lambda plan_id, **kw: {"ok": True})
    r = istemci.post(f"/api/approvals/{_son_oneri_id()}", json={"decision": "approve"})
    assert r.status_code == 200, r.text


def test_bilinmeyen_kimlik_hala_L0da_403(istemci, monkeypatch):
    """Sohbet genişlemesi eski kapıyı GEVŞETMEDİ: tanınmayan önek L0'da hâlâ reddedilir."""
    _seviye(monkeypatch, 0)
    assert istemci.post("/api/approvals/rev:filan",
                        json={"decision": "approve"}).status_code == 403


def test_sohbet_onerisi_kimligi_TEK_yerden_taninir():
    """Kimlik biçimi iki yerde ayrıştırılsaydı önek değiştiği gün sessizce ayrışırdı."""
    assert sohbet.oneri_kimligi_mi("SO-20260907T201103Z-1")
    assert not sohbet.oneri_kimligi_mi("rev:filan")
    assert ":" not in sohbet.oneri_kimligi("20260907T201103Z", 1)
    assert "oneri_kimligi_mi" in _kaynak(api.api_approve)

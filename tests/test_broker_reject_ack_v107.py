"""test_broker_reject_ack_v107.py — REDDEDİLEN GÖNDERİMLERE KAPATMA (2026-07-27).

Operatör şikâyeti ölçülebilir bir arızaydı: triyaj şeridi "senden bir şey bekliyor · 4 emir
reddedildi" diyordu ve o retler BEŞ GÜNLÜKTÜ. Kapatmanın hiçbir yolu yoktu, yani kırmızı bant
sonsuza dek kalıyordu — ve KALICI bir kırmızı, hiç kırmızı olmamakla aynı bilgiyi taşır: kimse
bakmaz. Şeridin tek işi "ŞU AN müdahale gerekiyor mu?" sorusunu cevaplamaktır; geçmişte kalmış,
görülmüş bir ret o soruya "evet" diyemez.

İki söz kilitleniyor:
  (1) KAPATMA SİLMEZ. `alerts_ack.json` emsalinin aynısı: satır defterde TAM alanlarıyla kalır
      (`acked` listesi + ack_ts), yalnız şeridi besleyen sayının dışına çıkar. Kanıt kaybı ile
      triyaj aynı şey değildir.
  (2) SESSİZ BAŞARI YOK. Tanınmayan bir anahtar sessizce yutulmaz; `unknown` olarak döner —
      operatörün kapattığını sandığı ama kapanmamış bir ret, tam da bu mekanizmanın önlemek için
      var olduğu şeydir.
"""
from __future__ import annotations

import pathlib

import pytest
from fastapi.testclient import TestClient

from meridian import api, codelaw, health, store

APP_JS = pathlib.Path("meridian/web/app.js")
LOOP = pathlib.Path("meridian/loop.py")


def _ret(plan_id, date, ticker, detail="stop price must be greater than current price"):
    """Canlı `broker_reconcile.json.failed_submissions` satırının GERÇEK şekli (2026-07-27)."""
    return {"date": date, "plan_id": plan_id, "ticker": ticker, "detail": detail}


DORT = [
    _ret("P-2026-07-23-UNP", "2026-07-23", "UNP"),
    _ret("P-2026-07-23-NSC", "2026-07-23", "NSC"),
    _ret("P-2026-07-23-TMO-momentum_burst", "2026-07-23", "TMO", "qty rounds to 0"),
    _ret("P-2026-07-24-PKG", "2026-07-24", "PKG"),
]


def _seed(rows=None):
    store.write_json("broker_reconcile.json", {"date": "2026-07-24", "api_ok": True,
                                               "failed_submissions": list(DORT if rows is None else rows)})


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api, "DASH_TOKEN", "T0KEN")
    return TestClient(api.app)


HDR = {"x-meridian-token": "T0KEN"}


# =================================================================================================
# 1) Uç: yetki, tekil ack, toplu ack, DÜRÜST unknown
# =================================================================================================
def test_uc_yetki_ister(sandbox_state, client):
    _seed()
    assert client.post("/api/broker_reject/ack", json={"all": True}).status_code in (401, 403)
    assert store.read_json(health.REJECT_ACK_FILE, None) is None, "yetkisiz istek yazdı"


def test_tekil_ack_yalniz_o_reddi_kapatir(sandbox_state, client):
    _seed()
    k = health.reject_key(DORT[0])

    r = client.post("/api/broker_reject/ack", json={"keys": [k]}, headers=HDR).json()

    assert r["acked_n"] == 1 and r["unknown"] == []
    assert r["open"] == 3 and r["acked"] == 1
    assert list(store.read_json(health.REJECT_ACK_FILE, {})) == [k]


def test_all_true_o_anki_ACIK_listenin_tamamini_kapatir(sandbox_state, client):
    _seed()

    r = client.post("/api/broker_reject/ack", json={"all": True}, headers=HDR).json()

    assert r["acked_n"] == 4 and r["open"] == 0 and r["acked"] == 4


def test_tanınmayan_anahtar_SESSIZCE_yutulmaz(sandbox_state, client):
    _seed()
    gercek = health.reject_key(DORT[1])

    r = client.post("/api/broker_reject/ack",
                    json={"keys": [gercek, "P-YOK·2026-01-01"]}, headers=HDR).json()

    assert r["acked_n"] == 1
    assert r["unknown"] == ["P-YOK·2026-01-01"], "olmayan anahtar sessizce başarı sayıldı"
    assert "P-YOK·2026-01-01" not in store.read_json(health.REJECT_ACK_FILE, {})


def test_ikinci_ack_IDEMPOTENT_ilk_gorulme_anini_ezmez(sandbox_state, client):
    _seed()
    k = health.reject_key(DORT[0])
    client.post("/api/broker_reject/ack", json={"keys": [k]}, headers=HDR)
    ilk = store.read_json(health.REJECT_ACK_FILE, {})[k]["ack_ts"]

    r = client.post("/api/broker_reject/ack", json={"keys": [k]}, headers=HDR).json()

    assert store.read_json(health.REJECT_ACK_FILE, {})[k]["ack_ts"] == ilk, "ack zamanı ezildi"
    assert r["open"] == 3 and r["acked"] == 1, "tekrar ack sayımı bozmadı"


def test_all_true_ZATEN_kapatilmislarin_zamanini_bozmaz(sandbox_state, client):
    """`all` "ekranda gördüğüm hepsi" demektir; kapatılmışların ack_ts'ini bugüne çekmek, kaydın
    NE ZAMAN görüldüğü bilgisini bozardı."""
    _seed()
    k = health.reject_key(DORT[0])
    client.post("/api/broker_reject/ack", json={"keys": [k]}, headers=HDR)
    ilk = store.read_json(health.REJECT_ACK_FILE, {})[k]["ack_ts"]

    client.post("/api/broker_reject/ack", json={"all": True}, headers=HDR)

    assert store.read_json(health.REJECT_ACK_FILE, {})[k]["ack_ts"] == ilk


# =================================================================================================
# 2) Filtre: open / acked ayrımı
# =================================================================================================
def test_split_dortten_ikisi_ackliyken_open2_acked2(sandbox_state):
    store.write_json(health.REJECT_ACK_FILE, {
        health.reject_key(DORT[0]): {"ack_ts": "2026-07-27T10:00:00+00:00"},
        health.reject_key(DORT[2]): {"ack_ts": "2026-07-27T10:00:00+00:00"}})

    out = health.split_rejections(DORT)

    assert [r["ticker"] for r in out["open"]] == ["NSC", "PKG"]
    assert [r["ticker"] for r in out["acked"]] == ["UNP", "TMO"]


def test_ack_dosyasi_yokken_hepsi_ACIK(sandbox_state):
    out = health.split_rejections(DORT)
    assert len(out["open"]) == 4 and out["acked"] == []


def test_bos_ve_None_girdi_patlamaz(sandbox_state):
    assert health.split_rejections(None) == {"open": [], "acked": []}
    assert health.split_rejections([]) == {"open": [], "acked": []}


def test_ayni_plan_FARKLI_seansta_yeni_bir_olaydir(sandbox_state):
    """Anahtar `plan_id·date`: aynı plan ertesi gün yeniden silahlanıp yeniden reddedilirse bu YENİ
    bir olaydır — dünkü 'gördüm' onu susturamaz."""
    dun = _ret("P-X", "2026-07-23", "AAA")
    bugun = _ret("P-X", "2026-07-24", "AAA")
    store.write_json(health.REJECT_ACK_FILE, {health.reject_key(dun): {"ack_ts": "t"}})

    out = health.split_rejections([dun, bugun])

    assert [r["date"] for r in out["open"]] == ["2026-07-24"]
    assert [r["date"] for r in out["acked"]] == ["2026-07-23"]


# =================================================================================================
# 3) TARİHÇE KORUNUR — kapatma silmez
# =================================================================================================
def test_ack_sonrasi_satir_TAM_alanlariyla_acked_listede_durur(sandbox_state, client):
    _seed()
    client.post("/api/broker_reject/ack", json={"all": True}, headers=HDR)

    out = health.split_rejections(store.read_json("broker_reconcile.json", {})["failed_submissions"])

    assert len(out["acked"]) == 4
    kapali = {r["ticker"]: r for r in out["acked"]}["TMO"]
    assert kapali["plan_id"] == "P-2026-07-23-TMO-momentum_burst"
    assert kapali["date"] == "2026-07-23" and kapali["detail"] == "qty rounds to 0"
    assert kapali["ack_ts"], "ack zamanı satıra işlenmemiş"


def test_ack_broker_reconcile_dosyasini_DEGISTIRMEZ(sandbox_state, client):
    """Defter loop.py'nin; ack katmanı onu OKUR, yazmaz. Aksi hâlde kapatma bir kanıt silme
    işlemine dönüşürdü."""
    _seed()
    once = (sandbox_state / "broker_reconcile.json").read_bytes()

    client.post("/api/broker_reject/ack", json={"all": True}, headers=HDR)

    assert (sandbox_state / "broker_reconcile.json").read_bytes() == once


# =================================================================================================
# 4) Uçlar aynı şekli servis eder
# =================================================================================================
def test_alpaca_ucu_open_acked_ayrimini_servis_eder(sandbox_state, client):
    _seed()
    client.post("/api/broker_reject/ack", json={"keys": [health.reject_key(DORT[0])]}, headers=HDR)

    fs = client.get("/api/alpaca", headers=HDR).json()["reconcile"]["failed_submissions"]

    assert isinstance(fs, dict) and set(fs) == {"open", "acked"}
    assert len(fs["open"]) == 3 and len(fs["acked"]) == 1
    assert fs["acked"][0]["ack_ts"]


def test_iki_uc_de_AYNI_sekli_servis_eder():
    """Aynı alanı iki uç farklı şekilde döndürürse pano hangi uçtan okuduğuna göre farklı bir
    gerçek görür — 'tek yanıtta iki gerçek olamaz' kuralının uçlar arası hâli."""
    src = pathlib.Path("meridian/api.py").read_text()
    assert src.count("health.split_rejections(") >= 3   # diagnostics + alpaca + ack ucu


# =================================================================================================
# 5) YASA 6 — yeni alanların panoda tüketicisi var
# =================================================================================================
def test_yasa6_open_acked_ack_ts_panoda_okunuyor():
    js = APP_JS.read_text()
    assert ".open" in js and "failed_submissions" in js
    assert "acked" in js and "ack_ts" in js
    assert "ackReject" in js and "ackRejectAll" in js, "kapatma düğmelerinin kablosu yok"
    assert "/api/broker_reject/ack" in js, "pano ucu hiç çağırmıyor"
    assert "unknown" in js, "tanınmayan anahtar panoda hiç gösterilmiyor"


def test_serit_sayisi_YALNIZ_open_okur():
    """Regresyon kilidi: şerit ham listeyi sayarsa kapatma hiçbir işe yaramaz."""
    js = APP_JS.read_text()
    blok = js.split("function spineHTML")[1].split("\nfunction ")[0]
    assert "failed_submissions || {}).open" in blok
    assert "rc.failed_submissions.length" not in blok, "şerit hâlâ ham listeyi sayıyor"


# =================================================================================================
# 6) KIRMIZI ÇİZGİLER: loop.py'ye dokunulmadı, yazım yolu değişmedi
# =================================================================================================
def test_loop_py_ack_katmanina_hic_dokunmadi():
    src = LOOP.read_text()
    assert "broker_reject_ack" not in src and "split_rejections" not in src


def test_broker_reconcile_YAZIM_yolu_aynen_duruyor():
    src = LOOP.read_text()
    assert '"failed_submissions": (meta.get("broker_rejected") or [])[-10:],' in src


def test_codelaw_artefakt_yasasi_yesil():
    """Ack dosyası `alerts_ack.json` ile AYNI deseni izler: uç YAZAR, alan modülü OKUR — yani dış
    tüketicisi vardır ve DECLARED_SINKS'e muafiyet olarak girmesi GEREKMEZ."""
    g = codelaw.artifact_graph()
    assert g["violations"] == []
    a = g["artifacts"]["broker_reject_ack.json"]
    assert a["writers"] == ["api.py"] and a["external_readers"] == ["health.py"]
    assert not a["unread"]
    assert "broker_reject_ack.json" not in codelaw.DECLARED_SINKS


def test_ack_ucu_yetkili_uc_listesinde():
    """P1 yasası: her mutasyon ucu `_auth` ister. Bu test o yasanın bu uçtaki somut hâli."""
    import re
    src = pathlib.Path("meridian/api.py").read_text()
    blok = next(b for b in re.split(r"\n(?=@app\.)", src) if '"/api/broker_reject/ack"' in b)
    assert blok.index("_auth(request)") < blok.index("await request.json()")

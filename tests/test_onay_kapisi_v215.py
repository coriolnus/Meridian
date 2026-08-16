"""ONAY KAPISI (B-6 kapaması, v215) — `approvals.jsonl` defteri artık UYGULAMAYI bağlıyor.

ÖLÇÜLEN KUSUR (docs/ARTEFAKT-TARAMASI-2026-08-07.md · B-6): defterin yazarı vardı
(`POST /api/approvals/{id}`) ve okuyucusu vardı (`GET /api/approvals` → pano), ama okuyan
DAVRANMIYORDU. L1'e geçildiği gün operatörün "onayla"/"reddet" kararı hiçbir icra yoluna bağlı
olmayacaktı — `dormant_setup` ile aynı sınıf. Bu dosya kapının SÖZLEŞMESİNİ çivilerler:

  * L0'da davranış BİREBİR aynı (bugünkü canlı; kapı deftere BAKMAZ bile),
  * L1'de onaysız uygulama REDDEDİLİR ve nedenli olay bırakır,
  * L1'de onaylı uygulama GEÇER,
  * `reject` kararı uygulatmaz, SON karar kazanır,
  * bozuk defter satırı onay DEĞİLDİR (fail-closed),
  * riski azaltan / operatör kararı olmayan yollar onay BEKLEMEZ (beyanlı istisnalar),
  * `GET /api/approvals` görünürlüğü ve kimlik dizgeleri BOZULMADI.
"""
from __future__ import annotations

import inspect
import json
import re

import pytest
from fastapi.testclient import TestClient

from meridian import api, config, obs, skills, store
from meridian import skill_evolve as se
from meridian.adapters import alpaca


# ---------------------------------------------------------------------------------------------
# fikstürler
# ---------------------------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _alpaca_tasima_kaydi_geri_alinir():
    """`alpaca._TRANSPORT` MODÜL-GLOBALİDİR ve bu dosya kontrol uçlarına POST atıyor — bir uç
    broker'a uzanırsa (`/api/control/cancel_open` → `alpaca.cancel_open_entries`) adaptör
    `_note(False, ...)` ile kaydı `ok=False`a çeker ve BU TEST BİTTİKTEN SONRA da öyle kalır.

    NEDEN ÖLÇÜLDÜ (2026-08-08, otoriter suite kırmızısı): `loop.reconcile_broker_state`
    `alpaca.orders`/`positions` yamalanmış OLSA BİLE `alpaca.transport()["ok"]`i ayrıca sınar
    (`loop.mirror_submit_armed` ve `loop._alpaca_emir_penceresi`) ve False görünce mutabakatı ERKEN döndürür. Sonuç: `test_regime_patch`
    ve `test_robustness_patch` yalıtımda yeşil, bu dosyanın ARDINDAN kırmızı — klasik sıra
    bağımlılığı. `conftest._MUTABLE_GLOBALS` yalnız `backtest.SECTORS`ı gözlüyor, yani bekçi bu
    sızıntıya KÖRDÜ; kaydı bu dosya kendi kirletiyorsa kendi de geri almalı.

    YERİNDE geri yüklenir (yeni dict ATANMAZ): adaptörün `_note`u globali kapatma yoluyla tutar,
    yeni bir nesne bağlamak sıfırlamayı hiçbir şeye dokunmamış hale getirirdi (conftest'in
    `_fmp._HEALTH` dersinin aynısı).

    `obs._SUPPRESS_LOGGED` AYNI SINIFTAN ve aynı gerekçeyle burada: `/api/halt` bir ALARM ateşler,
    alarm da jeton başına 6 saatlik SUSTURMA penceresini bu sözlüğe yazar. Bugün bir kırmızı
    üretmiyor (ölçüldü: bisect'te `/api/halt` temiz çıktı) ama bırakılan pencere, bildirim
    davranışını ölçen bir sonraki testi kendi kurmadığı bir susturmayla karşılaştırırdı —
    kaydedilmemiş bir sıra bağımlılığı. İki kayıt da bu dosyanın açtığı, bu dosyanın kapattığı."""
    onceki_tasima = dict(alpaca._TRANSPORT)
    onceki_susturma = dict(obs._SUPPRESS_LOGGED)
    yield
    alpaca._TRANSPORT.clear()
    alpaca._TRANSPORT.update(onceki_tasima)
    obs._SUPPRESS_LOGGED.clear()
    obs._SUPPRESS_LOGGED.update(onceki_susturma)


def _istemci(monkeypatch):
    # `with` KULLANILMAZ: lifespan `_autostart()`i koşturur (zamanlayıcı/Hermes/ayna akışı).
    monkeypatch.setattr(api, "DASH_TOKEN", None)
    return TestClient(api.app)


def _seviye(monkeypatch, lvl: int):
    """Otonomi seviyesini ayarla. Gerçek `limits()` yükü KORUNUR, yalnız tek alan değişir —
    sahte bir tek-anahtarlı sözlük döndürmek, aynı istekte limitleri okuyan başka bir yolu
    KeyError ile düşürebilirdi ve test o zaman kapıyı değil kendi fikstürünü ölçerdi."""
    gercek = dict(config.limits())
    monkeypatch.setattr(config, "limits", lambda: {**gercek, "autonomy_level": lvl})


def _kayit(sandbox) -> None:
    store.write_json("skills_registry.json", {"skills": {
        "loser-skill": {"category": "x", "fmp": "-", "alpaca": "-", "enabled": True,
                        "mode": "active", "style_active": True, "pipeline": "P2_SCREEN"},
    }})


def _onay_yaz(kimlik: str, karar, **ek) -> None:
    store.append_jsonl(api.APPROVALS_LEDGER, {"id": kimlik, "decision": karar,
                                              "reason": "test", "ts": "2026-08-08T00:00:00+00:00", **ek})


def _olaylar(event: str) -> list[dict]:
    return [e for e in obs.recent(limit=400) if e.get("event") == event]


def _govde(fn) -> str:
    """Fonksiyonun DOCSTRING'SİZ gövdesi. Bu dosyadaki yapısal çiviler KODU ölçer; düzyazı
    gerekçelerde geçen `f"rev:` gibi alıntılar bir çağrı DEĞİLDİR ve onları saymak testi
    kendi belgelendirmesine karşı kırardı."""
    import ast
    kaynak = inspect.getsource(fn)
    agac = ast.parse(inspect.cleandoc(kaynak) if kaynak.startswith(" ") else kaynak)
    tanim = agac.body[0]
    govde = tanim.body[1:] if ast.get_docstring(tanim) is not None else tanim.body
    return "\n".join(ast.unparse(n) for n in govde)


def _taslak_kur(tmp_path, monkeypatch, ad: str = "test-skill"):
    """Gerçek bir revizyon taslağı: `apply_revision` dosya değiştirir, yani kapı GEÇİLİRSE
    diskte görünür bir iz kalır — "kapı geçti mi" sorusu dönüş değerinden DEĞİL, dünyadan okunur."""
    d = tmp_path / "skills" / ad
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text("---\nname: %s\n---\nESKİ içerik. " % ad * 20)
    (d / "SKILL.md.v2-draft").write_text("---\nname: %s\n---\nYENİ içerik. " % ad * 20)
    monkeypatch.setattr(se, "_repo_skill_dir", lambda n: str(tmp_path / "skills" / n))
    store.write_json(se.REVISIONS_FILE, [{"skill": ad, "status": "draft", "rationale": "test"}])
    return d


# =============================================================================================
# 1) L0 NÖTRLÜĞÜ — bugünkü canlı yol BİREBİR aynı
# =============================================================================================
def test_L0_uygulama_yollari_kapiya_hic_ugramaz(sandbox_state, monkeypatch):
    """L0-NÖTRLÜK KANITI, EN SERT BİÇİMİYLE: defter okuyucusu PATLAYICI ile değiştirilir. L0'da
    her iki uç da normal çalışıyorsa, kapı deftere HİÇ bakmamış demektir — yani bugünkü canlı
    (L0 kâğıt) yola tek bir dosya okuması bile eklenmedi ve regresyon yüzeyi sıfırdır."""
    _kayit(sandbox_state)
    _seviye(monkeypatch, 0)

    def _patlayici(_kimlik):
        raise AssertionError("L0'da onay defteri OKUNDU — kapı L0-nötr değil")

    monkeypatch.setattr(api, "_onay_defteri_karari", _patlayici)
    c = _istemci(monkeypatch)

    r = c.post("/api/skills/apply", json={"skill": "loser-skill", "action": "shadow"})
    assert r.status_code == 200 and r.json()["ok"] is True, r.text[:300]
    assert skills.registry()["skills"]["loser-skill"]["shadow"] is True   # gerçekten uygulandı

    r2 = c.post("/api/skills/revision", json={"skill": "yok-boyle", "action": "apply"})
    assert r2.status_code == 200 and r2.json()["ok"] is False   # eski davranış: temiz ret, 409 DEĞİL


def test_L0_hicbir_kapi_olayi_yazilmaz(sandbox_state, monkeypatch):
    """L0'da kapı ne GEÇTİ ne REDDETTİ olayı bırakmalı: var olmayan bir kapının kaydı olamaz ve
    olsaydı olay akışını her tıklamada kirletirdi."""
    _kayit(sandbox_state)
    _seviye(monkeypatch, 0)
    c = _istemci(monkeypatch)
    c.post("/api/skills/apply", json={"skill": "loser-skill", "action": "shadow"})
    assert not _olaylar("approval_gate_passed") and not _olaylar("approval_missing_refused")


def test_kapinin_ILK_karari_seviye_kapisidir():
    """Yapısal çivi: L0 kısa devresi fonksiyonun İLK davranışı olmalı. Aşağı kayarsa (örn. defter
    okumasından SONRA), L0 yolu sessizce bir dosya okuması ve bir olay kazanır."""
    src = inspect.getsource(api._onay_kapisi)
    govde = src.split('"""')[2]                       # docstring'den SONRAsı
    assert govde.index("autonomy_level") < govde.index("_onay_defteri_karari"), \
        "seviye kapısı defter okumasının ALTINA kaymış — L0 artık nötr değil"
    assert re.search(r"if lvl < 1:\s*\n\s*return \{\"gecti\": True", govde), \
        "L0 kısa devresi kaybolmuş"


# =============================================================================================
# 2) L1 — ONAYSIZ UYGULAMA REDDEDİLİR (fail-closed) + NEDENLİ OLAY (YASA 4)
# =============================================================================================
def test_L1_onaysiz_skill_uygulamasi_reddedilir_ve_iz_birakir(sandbox_state, monkeypatch):
    _kayit(sandbox_state)
    _seviye(monkeypatch, 1)
    c = _istemci(monkeypatch)
    r = c.post("/api/skills/apply", json={"skill": "loser-skill", "action": "shadow"})
    assert r.status_code == 409, f"L1'de onaysız uygulama GEÇTİ: {r.status_code} {r.text[:200]}"
    detay = r.json()["detail"]
    assert "onay" in detay.lower() and len(detay) >= 20
    # ARANAN KİMLİK GÖVDEDE: "onay yok" cümlesi NEYİ onaylayacağını söylemezse yarım cevaptır.
    assert "rec:loser-skill" in detay, detay
    # DÜNYA DEĞİŞMEDİ: ret bir "200 + ok:false" değil, gerçekten uygulanmama.
    assert skills.registry()["skills"]["loser-skill"].get("shadow") is not True
    ev = _olaylar("approval_missing_refused")
    assert len(ev) == 1, f"nedenli olay yok/çift: {ev}"
    assert ev[0]["kimlik"] == "rec:loser-skill" and ev[0]["seviye"] == 1
    assert ev[0]["yol"] == "skills.apply_skill_action" and ev[0]["karar"] == "yok"
    assert len(ev[0]["neden"]) >= 20, "YASA 4: gerekçe 20 karakterden kısa"


def test_L1_onaysiz_revizyon_uygulamasi_reddedilir(sandbox_state, tmp_path, monkeypatch):
    d = _taslak_kur(tmp_path, monkeypatch)
    _seviye(monkeypatch, 1)
    c = _istemci(monkeypatch)
    r = c.post("/api/skills/revision", json={"skill": "test-skill", "action": "apply"})
    assert r.status_code == 409, r.text[:200]
    assert (d / "SKILL.md.v2-draft").exists(), "taslak yürürlüğe girmiş — kapı tutmadı"
    assert "ESKİ" in (d / "SKILL.md").read_text()
    ev = _olaylar("approval_missing_refused")
    assert len(ev) == 1 and ev[0]["kimlik"] == "rev:test-skill"
    assert ev[0]["yol"] == "skill_evolve.apply_revision"


# =============================================================================================
# 3) L1 — ONAYLI UYGULAMA GEÇER
# =============================================================================================
def test_L1_onayli_skill_uygulamasi_gecer(sandbox_state, monkeypatch):
    _kayit(sandbox_state)
    _seviye(monkeypatch, 1)
    _onay_yaz("rec:loser-skill", "approve")
    c = _istemci(monkeypatch)
    r = c.post("/api/skills/apply", json={"skill": "loser-skill", "action": "shadow"})
    assert r.status_code == 200 and r.json()["ok"] is True, r.text[:300]
    assert skills.registry()["skills"]["loser-skill"]["shadow"] is True
    gecti = _olaylar("approval_gate_passed")
    assert len(gecti) == 1 and gecti[0]["kimlik"] == "rec:loser-skill"
    assert not _olaylar("approval_missing_refused")


def test_L1_onayli_revizyon_uygulamasi_gecer(sandbox_state, tmp_path, monkeypatch):
    d = _taslak_kur(tmp_path, monkeypatch)
    _seviye(monkeypatch, 1)
    _onay_yaz("rev:test-skill", "approve")
    c = _istemci(monkeypatch)
    r = c.post("/api/skills/revision", json={"skill": "test-skill", "action": "apply"})
    assert r.status_code == 200 and r.json()["ok"] is True, r.text[:300]
    assert "YENİ" in (d / "SKILL.md").read_text() and (d / "SKILL.md.v1.bak").exists()


def test_L1_baska_kimligin_onayi_bu_uygulamayi_ACMAZ(sandbox_state, monkeypatch):
    """Kimlik eşleşmesi GERÇEK olmalı: bir öneriye verilen onay, komşusunu yetkilendiremez."""
    _kayit(sandbox_state)
    _seviye(monkeypatch, 1)
    _onay_yaz("rec:baska-skill", "approve")
    _onay_yaz("rev:loser-skill", "approve")        # doğru ad, YANLIŞ tür öneki
    c = _istemci(monkeypatch)
    r = c.post("/api/skills/apply", json={"skill": "loser-skill", "action": "shadow"})
    assert r.status_code == 409, "yabancı kimliğin onayı kapıyı açtı"


# =============================================================================================
# 4) L1 — RET KARARI UYGULAMAZ · SON KARAR KAZANIR
# =============================================================================================
def test_L1_reject_karari_uygulatmaz(sandbox_state, monkeypatch):
    _kayit(sandbox_state)
    _seviye(monkeypatch, 1)
    _onay_yaz("rec:loser-skill", "reject")
    c = _istemci(monkeypatch)
    r = c.post("/api/skills/apply", json={"skill": "loser-skill", "action": "shadow"})
    assert r.status_code == 409 and "reject" in r.json()["detail"]
    assert skills.registry()["skills"]["loser-skill"].get("shadow") is not True
    assert _olaylar("approval_missing_refused")[0]["karar"] == "reject"


@pytest.mark.parametrize("sira,beklenen", [(("approve", "reject"), 409),
                                           (("reject", "approve"), 200)])
def test_L1_son_karar_kazanir(sandbox_state, monkeypatch, sira, beklenen):
    """Defter salt-eklemedir: operatör fikrini değiştirebilir ve YÜRÜRLÜKTEKİ karar SONUNCUSUDUR.
    İlk satırı kazandırmak, geri alınmış bir onayı sonsuza dek geçerli kılardı."""
    _kayit(sandbox_state)
    _seviye(monkeypatch, 1)
    for karar in sira:
        _onay_yaz("rec:loser-skill", karar)
    c = _istemci(monkeypatch)
    r = c.post("/api/skills/apply", json={"skill": "loser-skill", "action": "shadow"})
    assert r.status_code == beklenen, r.text[:200]


# =============================================================================================
# 5) FAIL-CLOSED — BOZUK DEFTER SATIRI ONAY DEĞİLDİR
# =============================================================================================
@pytest.mark.parametrize("bozuk", [
    {"id": "rec:loser-skill"},                                   # decision alanı YOK
    {"id": "rec:loser-skill", "decision": None},                 # boş karar
    {"id": "rec:loser-skill", "decision": "onayla"},             # sözlükte olmayan karar
    {"id": "rec:loser-skill", "decision": ["approve"]},          # dizge değil
    {"id": "rec:loser-skill", "decision": 1},                    # sayı
])
def test_L1_bozuk_karar_alani_onay_sayilmaz(sandbox_state, monkeypatch, bozuk):
    _kayit(sandbox_state)
    _seviye(monkeypatch, 1)
    store.append_jsonl(api.APPROVALS_LEDGER, bozuk)
    c = _istemci(monkeypatch)
    r = c.post("/api/skills/apply", json={"skill": "loser-skill", "action": "shadow"})
    assert r.status_code == 409, f"okunamayan karar onay sayıldı: {bozuk}"
    ev = _olaylar("approval_missing_refused")[0]
    assert ev["karar"] == "bozuk" and ev["bozuk"] == 1, ev


def test_L1_onaydan_SONRA_gelen_bozuk_satir_kapiyi_kapatir(sandbox_state, monkeypatch):
    """Fail-closed'ın yönü: atfedilebilen ama yorumlanamayan bir satır, ÖNCEKİ onayı geçersiz
    kılar — çünkü o satır bir RET olabilir ve bilinmeyeni "onay" saymak kapının tersidir."""
    _kayit(sandbox_state)
    _seviye(monkeypatch, 1)
    _onay_yaz("rec:loser-skill", "approve")
    store.append_jsonl(api.APPROVALS_LEDGER, {"id": "rec:loser-skill", "decision": "?"})
    c = _istemci(monkeypatch)
    assert c.post("/api/skills/apply",
                  json={"skill": "loser-skill", "action": "shadow"}).status_code == 409


def test_L1_atfedilemeyen_satir_kimseye_onay_vermez_ama_gorunur(sandbox_state, monkeypatch):
    """`id`si okunamayan satır KİMSEYE onay vermez. Başkasının onayını da İPTAL ETMEZ (tek bozuk
    satır defteri kalıcı olarak kullanılamaz kılardı) — ama sayısı olaya/kayda düşer, yani
    defterin kirliliği görünmez kalmaz."""
    _kayit(sandbox_state)
    _seviye(monkeypatch, 1)
    store.append_jsonl(api.APPROVALS_LEDGER, {"decision": "approve"})          # id YOK
    store.append_jsonl(api.APPROVALS_LEDGER, {"id": 7, "decision": "approve"})  # id dizge değil
    d = api._onay_defteri_karari("rec:loser-skill")
    assert d["karar"] is None and d["atfedilemeyen"] == 2
    c = _istemci(monkeypatch)
    assert c.post("/api/skills/apply",
                  json={"skill": "loser-skill", "action": "shadow"}).status_code == 409
    assert _olaylar("approval_missing_refused")[0]["atfedilemeyen"] == 2

    _onay_yaz("rec:loser-skill", "approve")            # geçerli onay hâlâ çalışır
    r = c.post("/api/skills/apply", json={"skill": "loser-skill", "action": "shadow"})
    assert r.status_code == 200, r.text[:200]
    assert _olaylar("approval_gate_passed")[0]["atfedilemeyen"] == 2


def test_L1_ayristirilamayan_JSON_satiri_onay_uretmez(sandbox_state, monkeypatch):
    """Yarım/bozuk bir JSONL satırını `store.read_jsonl` zaten atar (ve bir kez
    `jsonl_rows_skipped` uyarır) — kapı da onu görmez, yani onay YOKTUR."""
    _kayit(sandbox_state)
    _seviye(monkeypatch, 1)
    p = config.STATE / api.APPROVALS_LEDGER
    p.write_text('{"id": "rec:loser-skill", "decision": "appro\n')
    c = _istemci(monkeypatch)
    assert c.post("/api/skills/apply",
                  json={"skill": "loser-skill", "action": "shadow"}).status_code == 409


def test_L1_defter_hic_okunamazsa_uygulama_yok(sandbox_state, monkeypatch):
    """Defterin kendisi okunamıyorsa (G/Ç, bozuk depo) sonuç ONAY YOK'tur ve nedeni yazılıdır —
    okunamayan bir kapı 'açık' varsayılamaz."""
    _kayit(sandbox_state)
    _seviye(monkeypatch, 1)
    gercek = store.read_jsonl

    def _patlat(name, *a, **k):
        if name == api.APPROVALS_LEDGER:
            raise OSError("disk yok")
        return gercek(name, *a, **k)

    monkeypatch.setattr(store, "read_jsonl", _patlat)
    c = _istemci(monkeypatch)
    r = c.post("/api/skills/apply", json={"skill": "loser-skill", "action": "shadow"})
    assert r.status_code == 409 and "OKUNAMADI" in r.json()["detail"]


# =============================================================================================
# 6) BEYANLI İSTİSNALAR — riski AZALTAN / operatör kararı OLMAYAN yollar onay beklemez
# =============================================================================================
def test_L1_revizyon_RETTI_onay_beklemez(sandbox_state, tmp_path, monkeypatch):
    """Ret hiçbir şeyi yürürlüğe koymaz; sistemin yapacağı işi AZALTIR. Onaya bağlamak, güvenli
    yönü tören şartına bağlamak olurdu."""
    d = _taslak_kur(tmp_path, monkeypatch)
    _seviye(monkeypatch, 1)
    c = _istemci(monkeypatch)
    r = c.post("/api/skills/revision", json={"skill": "test-skill", "action": "reject"})
    assert r.status_code == 200 and r.json()["ok"] is True, r.text[:200]
    assert not (d / "SKILL.md.v2-draft").exists()
    assert not _olaylar("approval_missing_refused")


@pytest.mark.parametrize("yol", ["/api/halt", "/api/control/learn_halt", "/api/control/cancel_open"])
def test_L1_riski_azaltan_yollar_onay_beklemez(sandbox_state, monkeypatch, yol):
    """HALT/acil-durdurma ailesi VAR OLAN riski azaltır. Deponun yazılı ilkesi (`koruma_kur`
    bloğu): "submit_armed YENİ RİSK ALIR, bu yol var olan riski AZALTIR". Acil durdurmayı bir
    onay kuyruğunun arkasına koymak, kapının kendisini arızaya çevirirdi.

    BROKER ÇAĞRISI YAMALIDIR ÇÜNKÜ ÖLÇÜLEN ŞEY BROKER DEĞİL: soru "kapı bu yolu bloke ediyor mu"dur
    ve cevabı uç, `alpaca`ya varmadan ÖNCE verir. Yamasız hâlde `/api/control/cancel_open` gerçek
    HTTP denemesi yapıyordu; `_dis_ag_kapali` onu kesiyor, adaptör `_note(False, ...)` ile
    `alpaca._TRANSPORT`i `ok=False`a çekiyor ve o kayıt test bitince de öyle kalıyordu (yukarıdaki
    fikstürün kaydettiği kırmızı). Ağa hiç çıkmamak, geri almaktan iyidir."""
    _seviye(monkeypatch, 1)
    monkeypatch.setattr(alpaca, "cancel_open_entries",
                        lambda: {"ok": True, "cancelled": [], "kept": [], "foreign": []})
    c = _istemci(monkeypatch)
    r = c.post(yol, json={"on": True})
    assert r.status_code != 409, f"{yol} onay kapısına takıldı — riski azaltan yol bloke"
    assert not _olaylar("approval_missing_refused")


def test_L1_otomatik_golgeleme_yolu_kapisiz_kalir(sandbox_state, monkeypatch):
    """`skills.auto_shadow_from_evidence` operatör kararı DEĞİLDİR: gelen kutusunda kimliği yoktur
    (`pending: False`), yani ona ait bir onay satırı hiçbir zaman var olamaz. Kapı
    `apply_skill_action`ın İÇİNE konsaydı L1'de bu döngü kalıcı ve açılamaz biçimde donardı."""
    _kayit(sandbox_state)
    _seviye(monkeypatch, 1)
    assert "_onay_kapisi" not in inspect.getsource(skills.apply_skill_action), \
        "kapı fonksiyonun İÇİNE kaymış — süreç-içi otomatik yol da kapanır"
    assert skills.apply_skill_action("loser-skill", "shadow")["ok"] is True
    assert not _olaylar("approval_missing_refused")


def test_onay_yazma_ucunun_KENDISI_uygulama_yapmaz():
    """Ölçüm: onay ve uygulama AYNI UÇTA DEĞİL. Yazıcı yalnız deftere satır atar; kapı oraya
    konsaydı uç kendi kendini onaylatırdı."""
    src = _govde(api.api_approve)
    for uygulayici in ("apply_skill_action", "apply_revision", "mirror_submit_armed",
                       "operator_onay_ver", "_onay_kapisi"):
        assert uygulayici not in src, f"onay ucu {uygulayici} çağırıyor — onay+uygulama birleşmiş"


# =============================================================================================
# 7) GÖRÜNÜRLÜK VE KİMLİK — GET bozulmadı, dizgeler TEK kaynaktan
# =============================================================================================
def test_GET_approvals_gorunurlugu_bozulmadi(sandbox_state, monkeypatch):
    store.write_json("arming_report.json", {"measurements": {"episodic_pivot": {
        "status": "gate_passed", "search_p": 0.88, "confirm_p": 0.74}},
        "cf_report": {"episodic_pivot": {"n": 34, "avg_r": 0.42}}})
    store.write_json(se.REVISIONS_FILE, [{"skill": "vcp-screener", "status": "draft",
                                          "rationale": "stop", "evidence": {"n": 20, "avg_r": -0.3}}])
    monkeypatch.setattr(skills, "pending_recommendations",
                        lambda: [{"skill": "market-news-analyst", "action": "shadow", "rationale": "zarar"}])
    _seviye(monkeypatch, 1)
    _onay_yaz("rec:market-news-analyst", "approve")
    c = _istemci(monkeypatch)
    d = c.get("/api/approvals").json()
    kimlikler = {i["type"]: i["id"] for i in d["inbox"]}
    assert kimlikler == {"arming": "arming:episodic_pivot", "skill_revision": "rev:vcp-screener",
                         "skill_rec": "rec:market-news-analyst"}, kimlikler
    assert d["level"] == 1 and len(d["pending"]) == 1        # L1'de defter panoya akıyor
    assert d["pending"][0]["id"] == "rec:market-news-analyst"


def test_gelen_kutusu_kimligi_ile_kapinin_aradigi_kimlik_AYNI_KAYNAKTAN(sandbox_state, monkeypatch):
    """Kimlik iki yerde üretilirse önek değiştiği gün kapı sessizce ayrışır (aranan dizge hiçbir
    satırla eşleşmez → her uygulama fail-closed reddedilir ve kimse nedenini bulamaz)."""
    src = _govde(api.api_approvals)
    for onek in ("rev:", "rec:", "arming:"):
        assert f"'{onek}" not in src and f'"{onek}' not in src, \
            f"gelen kutusu kimliği ({onek}) hâlâ satır içi kuruluyor"
    assert src.count("onay_kimligi(") == 3, "üç türün üçü de tek kaynaktan geçmiyor"
    # ve kapı gerçekten aynı üreticiyi kullanıyor:
    for fn in (api.api_skills_apply, api.api_skill_revision):
        assert "onay_kimligi(" in _govde(fn), f"{fn.__name__} kimliği elle kuruyor"


def test_bilinmeyen_tur_sessizce_gecmez():
    """Yarın eklenen bir gelen kutusu türü kapıya `None:x` diye görünüp eşleşmeyi imkânsız
    kılmasın: bilinmeyen tür ADIYLA düşer."""
    assert api.onay_kimligi("skill_rec", "x") == "rec:x"
    with pytest.raises(KeyError):
        api.onay_kimligi("yeni_tur", "x")


# =============================================================================================
# 8) MUTASYON İZİ — yeni red dalları da kayıt bırakır
# =============================================================================================
def test_kapili_uclar_hala_iz_birakiyor():
    """`test_na_revision2_v54::test_every_mutating_endpoint_leaves_a_trace` sözleşmesinin bu
    turdaki karşılığı: kapı EKLENEN dalların da izi olmalı — hem geçen hem reddedilen çağrı."""
    kapi = inspect.getsource(api._onay_kapisi)
    assert 'obs.warn("approval_missing_refused"' in kapi and 'obs.log("approval_gate_passed"' in kapi
    assert "neden=neden" in kapi, "ret olayı GEREKÇESİZ — YASA 4 ihlali"


def test_her_ret_gerekcesi_yirmi_karakterden_uzun():
    """YASA 4: sessiz atlama yok, gerekçe ≥20 karakter — ve gerekçe HTTP gövdesine de düşer."""
    for anahtar, metin in api._ONAY_RET_NEDEN.items():
        assert len(metin) >= 20, f"{anahtar} gerekçesi kısa: {metin!r}"


def test_defter_adi_tek_sabitten_okunur():
    """Dosya adı üç yerde (yazıcı/okuyucu/kapı) elle yazılsaydı, biri değiştiği gün kapı BAŞKA
    bir deftere bakardı — ve fail-closed olduğu için her şeyi reddederdi."""
    src = (config.ROOT / "meridian" / "api.py").read_text() if hasattr(config, "ROOT") else \
        __import__("pathlib").Path(api.__file__).read_text()
    assert src.count('"approvals.jsonl"') == 1, "defter adı hâlâ birden çok yerde harfi harfine yazılı"
    assert api.APPROVALS_LEDGER == "approvals.jsonl"


def test_ledger_semasi_yazici_ile_kapi_arasinda_uyusuyor(sandbox_state, monkeypatch):
    """Yazıcının ürettiği SATIRIN ta kendisi kapıdan geçmeli — şema iki tarafta ayrı ayrı
    tanımlanmış olsaydı, uç bir gün alan adını değiştirir ve kapı hiç fark etmezdi."""
    _seviye(monkeypatch, 1)
    c = _istemci(monkeypatch)
    r = c.post("/api/approvals/rec:loser-skill", json={"decision": "approve", "reason": "kanıt yeterli"})
    assert r.status_code == 200, r.text[:200]
    satir = store.read_jsonl(api.APPROVALS_LEDGER)[-1]
    assert set(satir) >= {"id", "decision", "ts"} and json.dumps(satir)   # serileşebilir
    assert api._onay_defteri_karari("rec:loser-skill")["karar"] == "approve"

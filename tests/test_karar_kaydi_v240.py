"""v240 KARAR KAYDI + ÖRNEKLEM DÜRÜSTLÜĞÜ (2026-08-13) — operatörün iki itirazının kapanışı.

[1] KARAR YOLU YOKTU. v239'da `lean_in` düğmesi kaldırıldı ve ölçüm doğruydu (registry'de karşılık
    yok, deterministik motor kayıt defterini okumuyor) — ama YARIMDI: öneri gelen kutusunda
    GÖRÜNÜYOR, operatörün yapabileceği hiçbir şey yok. Operatör vakası: "butonu işler hale
    getireceğine komple kaldırmışsın, bunu nasıl onaylayacağım?" Eksik olan DAVRANIŞ değil KARAR
    YOLUYDU. Kapanış: karar aynı deftere (`approvals.jsonl`), aynı uçtan (`POST /api/approvals/
    {id}`), aynı kimlik üreticisinden (`onay_kimligi`) yazılır — İKİNCİ BİR ONAY YOLU AÇILMADI.
    Değişen tek şey KİMLİK UZAYI: `kayit:{skill}:{action}`, ve o uzayı hiçbir uygulama kapısı
    okumaz. Bu dosyanın en sert çivisi budur: bir karar KAYDI, yarın L1'de bir icrayı AÇAMAZ.

[2] ÖNERİ METNİ ÖRNEKLEMİ SÖYLEMİYORDU. Canlı: `stockbee-exhaustion-hammer-screener` önerisi
    "Strong live performance of 0.918 avg_r" diyordu; aynı skill eksen-2 teşhisinde
    `ornek_yetersiz_cf_de_yetersiz` kovasında ve n=1 (cf n=12, cf ort 0,328).
    KÖK — ÖLÇÜLDÜ: öneri İKİ AYRI YOLDAN doğuyor ve `min_n` yalnız birinde var.
      (a) `skills.recommend_from_attribution(min_n=MIN_N)` — iki kollu örneklem kapısı,
      (b) hermes `HYP_SCHEMA.skill_recommendation` → `reflect._submit_locked` →
          `skills.record_recommendation` — bu zincirde HİÇBİR örneklem kapısı yok.
    Kanıt defterin kendisinde: `pullback-screener/shadow`, kaynak `hermes:gemini`, metin
    "avg_r of -1.0 over n=4 trades" — n=4 < MIN_N=8, deterministik yol o satırı üretemezdi.
    Kapanış: öneri SUSTURULMAZ (ölçüm gerçektir) ama her satır KAYIT ANINDA ÖLÇÜLEN künyeyi
    taşır ve eşiği geçmiyorsa bunu ADIYLA yazar; prompt da eşiği artık kaynaktan okuyup söyler.
"""
from __future__ import annotations

import ast
import inspect
import pathlib

import pytest
from fastapi.testclient import TestClient

from meridian import analytics, api, config, obs, skills, store

REPO = pathlib.Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------------------------
# fikstürler
# ---------------------------------------------------------------------------------------------
def _istemci(monkeypatch) -> TestClient:
    monkeypatch.setattr(api, "DASH_TOKEN", None)
    return TestClient(api.app)


def _seviye(monkeypatch, lvl: int) -> None:
    gercek = dict(config.limits())
    monkeypatch.setattr(config, "limits", lambda: {**gercek, "autonomy_level": lvl})


def _kayit() -> None:
    store.write_json("skills_registry.json", {"skills": {
        "kazanan-skill": {"category": "x", "fmp": "-", "alpaca": "-", "enabled": True,
                          "mode": "active", "style_active": True, "pipeline": "P2_SCREEN"},
        "loser-skill": {"category": "x", "fmp": "-", "alpaca": "-", "enabled": True,
                        "mode": "active", "style_active": True, "pipeline": "P2_SCREEN"},
    }})


def _canli_vaka(monkeypatch) -> None:
    """CANLI SAYILAR (2026-08-13 ölçümü). `kazanan-skill`, exhaustion-hammer vakasının birebir
    künyesini taşır: n=1 · avg_r=0,918 · n_cf=12 · cf_avg_r=0,328 — yani gerçek kol da (1<8)
    cf kolu da (12 < 8×5) TUTMAZ. `loser-skill` ise eşiği gerçekten geçen karşı-örnektir."""
    monkeypatch.setattr(analytics, "skill_attribution", lambda: {"skills": [
        {"skill": "kazanan-skill", "n": 1, "win_rate": 1.0, "avg_r": 0.918, "total_r": 0.918,
         "n_cf": 12, "cf_avg_r": 0.328},
        {"skill": "loser-skill", "n": 12, "win_rate": 0.25, "avg_r": -0.4, "total_r": -4.8,
         "n_cf": 90, "cf_avg_r": -0.35},
    ]})


def _oneri(action: str, skill: str, kaynak: str = "hermes:gemini", metin: str = "") -> bool:
    return skills.record_recommendation(
        {"skill": skill, "action": action,
         "rationale": metin or f"Strong live performance of 0.918 avg_r"}, source=kaynak)


def _govde(fn) -> str:
    """Fonksiyonun DOCSTRING'SİZ gövdesi — yapısal çiviler KODU ölçer, düzyazı gerekçeleri değil
    (v215'ten devralınan yardımcı; bu dosyanın gerekçeleri de kimlik dizgeleri içeriyor)."""
    kaynak = inspect.getsource(fn)
    agac = ast.parse(inspect.cleandoc(kaynak) if kaynak.startswith(" ") else kaynak)
    tanim = agac.body[0]
    govde = tanim.body[1:] if ast.get_docstring(tanim) is not None else tanim.body
    return "\n".join(ast.unparse(n) for n in govde)


# =============================================================================================
# [2] KÖK: ÖRNEKLEM EŞİĞİ İKİ YOLDAN YALNIZ BİRİNDEYDİ
# =============================================================================================
def test_kok_LLM_yolu_eskiden_ORNEKLEM_KAPISINI_hic_gormuyordu():
    """ARIZANIN KÖK ÇİVİSİ. `record_recommendation` — LLM yolunun deftere ULAŞTIĞI TEK KAPI —
    eşiği hiç sormuyordu; `min_n` yalnız `recommend_from_attribution` imzasındaydı. Kapı artık
    künyeyi ÖLÇÜP satıra basıyor. Bu test o bağı KODDA arar: künye çağrısı kaybolursa, ölçüm
    yine sessizce yalnız deterministik yolda kalır."""
    g = _govde(skills.record_recommendation)
    assert "ornek_kunyesi(" in g, "kayıt kapısı örneklemi ÖLÇMÜYOR — LLM yolu yine kapısız"
    assert "ornek_notu(" in g, "künye yazılıyor ama operatörün okuyacağı cümle kurulmuyor"


def test_esik_TEK_SABITTEN_okunuyor():
    """`8` üç yerde elle yazılırsa biri sessizce ayrışır (v238 eylem sözlüğü dersi)."""
    assert skills.MIN_N == 8
    import inspect as _i
    src = _i.getsource(skills)
    assert "min_n: int = 8" not in src, "imza varsayılanı hâlâ elle yazılı bir 8"


@pytest.mark.parametrize("skill,beklenen", [("kazanan-skill", False), ("loser-skill", True)])
def test_kunye_IKI_KOLLU_kapiyla_ayni_hukmu_veriyor(sandbox_state, monkeypatch, skill, beklenen):
    """`ornek_kunyesi(...)["yeterli"]`, `recommend_from_attribution`ın kullandığı kapının ta
    kendisi olmalı — üçüncü bir eşik yorumu, üçüncü bir ayrışma demektir."""
    _kayit(); _canli_vaka(monkeypatch)
    k = skills.ornek_kunyesi(skill)
    assert k["yeterli"] is beklenen, k
    assert k["esik"]["min_n"] == skills.MIN_N


def test_n1_onerisi_KAYDEDILIR_ama_YETERSIZ_damgasi_alir(sandbox_state, monkeypatch):
    """HÜKÜM: öneri susturulmaz (ölçüm gerçek, operatör görmeli — v238 `lean_in` çizgisi), ama
    "güçlü" iddiası artık ÖLÇÜLEN n'in yanında durur ve eşiğin altında olduğu yazılıdır."""
    _kayit(); _canli_vaka(monkeypatch)
    assert _oneri("lean_in", "kazanan-skill") is True, "öneri susturulmuş — ölçüm kayboldu"
    r = next(x for x in skills.pending_recommendations() if x["skill"] == "kazanan-skill")
    assert r["ornek"] == {"n": 1, "avg_r": 0.918, "n_cf": 12, "cf_avg_r": 0.328,
                          "yeterli": False, "esik": {"min_n": 8, "cf_gercek_asgari": 4.0,
                                                     "cf_asgari": 40}}
    assert r["ornek_yeterli"] is False
    assert skills.ORNEK_YETERSIZ_ETIKET in r["ornek_notu"] and "n=1" in r["ornek_notu"]
    # METİN DEĞİŞTİRİLMEDİ: iddia ile ölçü AYRI okunur. Metni sessizce düzeltmek, LLM'in ne
    # dediğini kaybetmek olurdu — kalibrasyonun kendisi o metinde.
    assert "Strong live performance" in r["rationale"]


def test_esigi_gecen_oneri_YETERLI_damgasi_alir(sandbox_state, monkeypatch):
    """KARŞI-ÇİVİ: damga bir susturma değil bir AYIRT ETME. n=12 gerçek örneklemli öneri
    "yeterli" der ve uyarı cümlesi kurulmaz."""
    _kayit(); _canli_vaka(monkeypatch)
    _oneri("shadow", "loser-skill", metin="12 işlemde ort. -0.4R")
    r = next(x for x in skills.pending_recommendations() if x["skill"] == "loser-skill")
    assert r["ornek_yeterli"] is True
    assert skills.ORNEK_YETERSIZ_ETIKET not in r["ornek_notu"]


def test_kunye_ONERI_METNINDEN_DEGIL_olcumden_okunur(sandbox_state, monkeypatch):
    """Metni yazan taraf kendi kanıtını BEYAN EDEMEZ. `rec` sözlüğüne uydurma n/avg_r konsa bile
    deftere ÖLÇÜLEN künye düşer (LLM yolunda `rec` zaten yalnız serbest metin taşır; ama
    `auto_shadow_from_evidence` cf değerlerini `n`/`avg_r` adlarıyla geçiriyor — o karışıklık da
    bu satırla kapanır)."""
    _kayit(); _canli_vaka(monkeypatch)
    skills.record_recommendation({"skill": "kazanan-skill", "action": "lean_in",
                                  "n": 999, "avg_r": 9.9, "rationale": "iddia"}, source="test")
    r = next(x for x in skills.pending_recommendations() if x["skill"] == "kazanan-skill")
    assert r["ornek"]["n"] == 1 and r["ornek"]["avg_r"] == 0.918, r["ornek"]


def test_KUNYESIZ_eski_satir_OLCULEMEDI_der_False_DEMEZ(sandbox_state):
    """UYDURMA YASAĞI. v240 öncesi satırda künye YOK; oraya bugünkü ölçümü basmak, öneri anında
    var olmayan bir kanıtı geçmişe yazmak olurdu. "Eşiği geçemedi" (False) ile "ölçemedik"
    (None) tek değere indirgenirse dürüstlük kaybolur."""
    _kayit()
    store.append_jsonl(skills.SKILL_RECS, {"ts": "2026-08-01T00:00:00+00:00", "skill": "loser-skill",
                                           "action": "lean_in", "rationale": "eski satır",
                                           "pending": True, "applied": False})
    r = next(x for x in skills.pending_recommendations() if x["skill"] == "loser-skill")
    assert r["ornek"] is None and r["ornek_yeterli"] is None
    assert "ÖLÇÜLEMEDİ" in r["ornek_notu"]


def test_kunye_OLCULEMEZSE_uydurulmuyor(sandbox_state, monkeypatch):
    """Atıf defteri patlarsa künye None DÖNMEZ, `olculemedi` yazar — ve kayıt yine yapılır
    (ölçüm arızası bir öneriyi yok etmemeli)."""
    _kayit()

    def _patla():
        raise RuntimeError("atıf defteri okunamadı")
    monkeypatch.setattr(analytics, "skill_attribution", _patla)
    assert skills.record_recommendation({"skill": "loser-skill", "action": "lean_in",
                                         "rationale": "x"}, source="test") is True
    r = next(x for x in skills.pending_recommendations() if x["skill"] == "loser-skill")
    assert r["ornek"]["olculemedi"] and r["ornek_yeterli"] is None
    assert "ÖLÇÜLEMEDİ" in r["ornek_notu"]


def test_hermes_promptu_ESIGI_KAYNAKTAN_okuyup_soyluyor(sandbox_state, monkeypatch):
    """PROMPT TARAFI KÖK. Model `n=1`i meşru kanıt sandı çünkü gördüğü satırda örneklemin yeterli
    olup olmadığını söyleyen hiçbir şey yoktu ve cf katmanı prompt'a hiç girmiyordu."""
    from meridian import hermes
    _kayit(); _canli_vaka(monkeypatch)
    lib = hermes._skill_library()
    assert lib["sample_gate"]["min_n"] == skills.MIN_N
    satir = next(r for r in lib["measured_or_protected"] if r["name"] == "kazanan-skill")
    assert satir["n_cf"] == 12 and satir["cf_avg_r"] == 0.328, satir
    assert "SAMPLE FLOOR" in lib["note"] and "NOISE" in lib["note"]
    # SYSTEM statik kalmalı (önbellek sözleşmesi, v106) ama kuralı TAŞIMALI.
    assert "SAMPLE FLOOR IS NOT OPTIONAL" in hermes.SYSTEM
    assert "sample_gate" in hermes.SYSTEM, "kural var ama modelin bakacağı alan adı yazılı değil"


# =============================================================================================
# [1] KARAR KAYDI — İKİNCİ ONAY YOLU YOK, KAPI BAĞLAMAZ
# =============================================================================================
def test_kayit_kimligi_TEK_URETICIDEN_cikiyor():
    """Kimlik `onay_kimligi`den türer; gelen kutusu, yazma ucu ve pano AYNI dizgeyi görmeli."""
    assert api.kayit_karar_kimligi("a-skill", "lean_in") == "kayit:a-skill:lean_in"
    assert "onay_kimligi(" in _govde(api.kayit_karar_kimligi)
    assert api.ONAY_ONEK["skill_rec_kayit"] == "kayit"


def test_KAYIT_onayi_L1_UYGULAMA_KAPISINI_ACMIYOR(sandbox_state, monkeypatch):
    """DOSYANIN EN SERT ÇİVİSİ. Kayıt uzayı `rec:` uzayından AYRI olmasaydı, bugün L0'da
    `lean_in` için yazılan bir "Kabul", yarın L1'de aynı skill'e gelen bir `shadow` önerisinin
    uygulamasını açardı (kapının kendi beyanı: "onay KİMLİĞE bağlıdır, öneri ÖRNEĞİNE değil").
    Davranışsal olmayan bir kaydın davranışsal bir kapıyı açması, bu turun kapattığı kusurdur."""
    _kayit()
    store.append_jsonl(api.APPROVALS_LEDGER,
                       {"id": api.kayit_karar_kimligi("loser-skill", "lean_in"),
                        "decision": "approve", "reason": "kayıt", "ts": "2026-08-13T00:00:00+00:00"})
    _seviye(monkeypatch, 1)
    c = _istemci(monkeypatch)
    r = c.post("/api/skills/apply", json={"skill": "loser-skill", "action": "shadow"})
    assert r.status_code == 409, f"KAYIT satırı UYGULAMA kapısını açtı: {r.status_code}"
    assert "rec:loser-skill" in r.json()["detail"]
    assert skills.registry()["skills"]["loser-skill"].get("shadow") is not True


def test_kapi_okuyan_onekler_KAYNAKTAKI_cagrilarla_ORTUSUYOR():
    """`KAPI_OKUYAN_ONEKLER` elle yazılı olmak ZORUNDA (statik graf "hangi önek okunuyor"u
    göremez) — o yüzden çivisi burada: kaynakta `_onay_kapisi(onay_kimligi("X", ...))` biçiminde
    kullanılan HER tür, bu kümede olmalı. Yarın üçüncü bir kapı açılırsa küme güncellenmeden
    testi geçemez; güncellenmeseydi L0 istisnası sessizce bir icra kapısını açardı."""
    src = (REPO / "meridian" / "api.py").read_text()
    agac = ast.parse(src)
    turler = set()
    for n in ast.walk(agac):
        if not (isinstance(n, ast.Call) and getattr(n.func, "id", "") == "_onay_kapisi"):
            continue
        for arg in n.args:
            if isinstance(arg, ast.Call) and getattr(arg.func, "id", "") == "onay_kimligi" \
                    and arg.args and isinstance(arg.args[0], ast.Constant):
                turler.add(api.ONAY_ONEK[arg.args[0].value])
    assert turler, "kaynakta hiç kapı çağrısı bulunamadı — tarama deseni bozulmuş"
    assert turler == set(api.KAPI_OKUYAN_ONEKLER), (turler, set(api.KAPI_OKUYAN_ONEKLER))
    assert api.ONAY_ONEK["skill_rec_kayit"] not in api.KAPI_OKUYAN_ONEKLER


def test_L0_da_KARAR_YAZILABILIYOR_ve_davranissal_DEGIL(sandbox_state, monkeypatch):
    """OPERATÖR İTİRAZININ TAM ADRESİ: sistem L0 ve `POST /api/approvals/{id}` L0'da 403
    veriyordu — yani karar kaydı BUGÜN imkânsızdı. Kapı-bağlamayan kimlikte 403'ün koruduğu
    bir şey yok. Yanıt sınırını KENDİSİ söyler: `ok: true` tek başına "yapıldı" gibi okunurdu."""
    _kayit(); _canli_vaka(monkeypatch)
    _oneri("lean_in", "kazanan-skill")
    _seviye(monkeypatch, 0)
    c = _istemci(monkeypatch)
    kimlik = api.kayit_karar_kimligi("kazanan-skill", "lean_in")
    r = c.post(f"/api/approvals/{kimlik}", json={"decision": "reject", "reason": "n=1, kanıt yok"})
    assert r.status_code == 200, r.text[:200]
    g = r.json()
    assert g["davranissal"] is False and "davranış DEĞİŞMEZ" in g["not"]
    # KARAR ANINDAKİ KÜNYE SUNUCUDAN — istemcinin beyanı değil.
    assert g["kunye"]["ornek"]["n"] == 1 and g["kunye"]["ornek_yeterli"] is False
    satir = store.read_jsonl(api.APPROVALS_LEDGER)[-1]
    assert satir["id"] == kimlik and satir["decision"] == "reject"
    assert satir["davranissal"] is False and satir["kunye"]["skill"] == "kazanan-skill"


def test_L0_da_KAPI_BAGLAYAN_kimlik_HALA_403(sandbox_state, monkeypatch):
    """REGRESYON KAPISI: L0 istisnası SADECE kapı-bağlamayan uzaya açıldı. `rec:`/`rev:` için
    403 aynen durur — yoksa bugün yazılan bir onay yarın L1'de icrayı açardı."""
    _seviye(monkeypatch, 0)
    c = _istemci(monkeypatch)
    for kimlik in ("rec:loser-skill", "rev:loser-skill"):
        r = c.post(f"/api/approvals/{kimlik}", json={"decision": "approve"})
        assert r.status_code == 403, f"{kimlik}: {r.status_code}"
    # TANINMAYAN ÖNEK DE 403: bağlamadığını KANITLAYAMADIĞIMIZ uzay fail-closed kalır.
    r = c.post("/api/approvals/uydurma:x", json={"decision": "approve"})
    assert r.status_code == 403, r.status_code


def test_gelen_kutusu_KARAR_YOLU_sunuyor_ama_UYGULA_dugmesi_YOK(sandbox_state, monkeypatch):
    """v238'in hükmü korunur (`actions: []` — uygulanamaz eylem uygulanabilir gibi SUNULMAZ) ve
    üstüne KARAR YOLU eklenir. İkisi ayrı alanlardır; kayıt düğmesini `actions`a koymak, tam da
    v238'de kapattığımız kusuru geri getirirdi."""
    _kayit(); _canli_vaka(monkeypatch)
    _oneri("lean_in", "kazanan-skill")
    c = _istemci(monkeypatch)
    oge = next(i for i in c.get("/api/approvals").json()["inbox"] if i["type"] == "skill_rec")
    assert oge["actions"] == [] and oge["uygulanabilir"] is False
    kk = oge["karar_kaydi"]
    assert kk["id"] == "kayit:kazanan-skill:lean_in" and kk["karar"] is None
    assert kk["davranissal"] is False and "knob/kapı" in kk["not"]
    # ÖRNEKLEM KANITIN YANINDA: iddia (`evidence`) ile ölçü (`ornek`) ayrı okunur.
    assert "Strong live performance" in oge["evidence"]
    assert oge["ornek"]["n"] == 1 and oge["ornek_yeterli"] is False


def test_uygulanabilir_oneri_KARAR_KAYDI_TASIMAZ(sandbox_state, monkeypatch):
    """KARŞI-ÇİVİ: `shadow`un GERÇEK bir uygulama yolu var (`rec:` + Uygula düğmesi). Ona bir de
    kayıt yolu vermek, aynı öneri için İKİ karar yolu açmak olurdu — bu turun yasağı."""
    _kayit(); _canli_vaka(monkeypatch)
    _oneri("shadow", "loser-skill", metin="12 işlemde ort. -0.4R")
    c = _istemci(monkeypatch)
    oge = next(i for i in c.get("/api/approvals").json()["inbox"]
               if i["type"] == "skill_rec" and i["skill"] == "loser-skill")
    assert oge["actions"] == ["apply"] and "karar_kaydi" not in oge


def test_karar_verilmis_oneri_BEKLIYOR_olarak_SAYILMIYOR(sandbox_state, monkeypatch):
    """BRIEF MADDE 3: karar verilmiş öneri gelen kutusunda damgasıyla DURUR (üreteç aynı öneriyi
    yarın yeniden yazabilir; karar geçmişi görünür kalmalı) ama artık İŞ İSTEMEZ. Rozet ile kart
    aynı yardımcıdan (`_karar_kaydi`) beslenir — ölçütü iki yerde yazmak, ikisinin aynı gün
    ayrışması demekti (`_onay_bekleyen_damgala` dersi)."""
    _kayit(); _canli_vaka(monkeypatch)
    _oneri("lean_in", "kazanan-skill")
    c = _istemci(monkeypatch)
    assert api._inbox_count([]) == 1, "karar öncesi bekleyen sayılmıyor"
    kimlik = api.kayit_karar_kimligi("kazanan-skill", "lean_in")
    assert c.post(f"/api/approvals/{kimlik}", json={"decision": "approve"}).status_code == 200
    assert api._inbox_count([]) == 0, "karar verilmiş öneri hâlâ 'bekleyen karar' sayılıyor"
    oge = next(i for i in c.get("/api/approvals").json()["inbox"] if i["type"] == "skill_rec")
    assert oge["karar_kaydi"]["karar"] == "approve", "karar damgası gelen kutusunda görünmüyor"


def test_ayni_oneri_TEKRAR_URETILINCE_onceki_karar_kunyesi_GORUNUYOR(sandbox_state, monkeypatch):
    """Operatör aynı satırı ikinci kez incelemesin: ÖNERİ DEFTERİ değişse bile KARAR defteri
    sabittir ve önceki karar + karar anındaki künye ekrana geri gelir. İki defter ayrı olduğu
    için bu bir tesadüf değil TASARIM — öneri satırı kadansın malı, karar operatörün."""
    _kayit(); _canli_vaka(monkeypatch)
    _oneri("lean_in", "kazanan-skill")
    c = _istemci(monkeypatch)
    kimlik = api.kayit_karar_kimligi("kazanan-skill", "lean_in")
    c.post(f"/api/approvals/{kimlik}", json={"decision": "reject", "reason": "n=1"})
    # ÖNERİ DEFTERİ SIFIRLANIR ve kadans aynı öneriyi YENİDEN üretir (yeni satır, yeni ts).
    (sandbox_state / skills.SKILL_RECS).write_text("")
    assert _oneri("lean_in", "kazanan-skill") is True
    oge = next(i for i in c.get("/api/approvals").json()["inbox"] if i["type"] == "skill_rec")
    kk = oge["karar_kaydi"]
    assert kk["karar"] == "reject" and kk["gerekce"] == "n=1"
    assert kk["kunye"]["ornek"]["n"] == 1, kk["kunye"]


def test_karar_EYLEM_bazinda_ayrisiyor(sandbox_state, monkeypatch):
    """`lean_in`e verilen karar, aynı skill'in BAŞKA bir önerisini "hallolmuş" göstermez. Gelen
    kutusunda yanlış bir "karar verilmiş" damgası, kararı kaybetmekle aynı şeydir."""
    assert api.kayit_karar_kimligi("s", "lean_in") != api.kayit_karar_kimligi("s", "activate")


def test_karar_OLAY_defterine_de_dusuyor_ve_sinifi_yazili(sandbox_state, monkeypatch):
    """YASA 4 + YASA 6: operatör o an ekrana bakmıyor olabilir. Olay akışında da iki sınıf
    AYRILIR — kayıt-önerisine verilen "Kabul", sonradan "uygulandı" diye okunmamalı."""
    _kayit(); _canli_vaka(monkeypatch)
    _oneri("lean_in", "kazanan-skill")
    c = _istemci(monkeypatch)
    kimlik = api.kayit_karar_kimligi("kazanan-skill", "lean_in")
    c.post(f"/api/approvals/{kimlik}", json={"decision": "approve"})
    ev = [e for e in obs.recent(limit=200) if e.get("event") == "approval_decision"]
    assert ev and ev[-1]["davranissal"] is False, ev
    js = (REPO / "meridian" / "web" / "app.js").read_text()
    i = js.index("\n  approval_decision:")
    assert "e.davranissal" in js[i:i + 400], "olay cümlesi iki sınıfı ayırmıyor"


# =============================================================================================
# DEFTERİN TEK OKUYUCUSU — kapı ile görünüm AYRIŞAMAZ
# =============================================================================================
def test_defter_TEK_gecisle_taraniyor_kapi_ondan_TUREiyor():
    """Karar kaydıyla defterin İKİNCİ bir okuyucusu doğdu (gelen kutusu "karar verilmiş mi?"
    diye soruyor). İkinci bir döngü, kapı "reject" derken panonun "bekliyor" göstermesi
    demekti — bu deponun en pahalı hata sınıfı. Döngü TEK."""
    g = _govde(api._onay_defteri_karari)
    assert "_defter_tarama()" in g, "kapı kendi döngüsünü geri açmış"
    assert "read_jsonl" not in g, "kapı defteri ikinci kez okuyor"


@pytest.mark.parametrize("kararlar,beklenen", [
    ([], None), (["approve"], "approve"), (["reject"], "reject"),
    (["approve", "reject"], "reject"), (["reject", "approve"], "approve"),
])
def test_gorunum_ve_kapi_AYNI_kararı_okuyor(sandbox_state, kararlar, beklenen):
    kimlik = api.kayit_karar_kimligi("x-skill", "lean_in")
    for k in kararlar:
        store.append_jsonl(api.APPROVALS_LEDGER, {"id": kimlik, "decision": k, "ts": "t"})
    assert api._onay_defteri_karari(kimlik)["karar"] == beklenen
    assert api._karar_kaydi("x-skill", "lean_in")["karar"] == beklenen


def test_bozuk_karar_alani_HALA_bozuk_okunuyor(sandbox_state):
    """v215 fail-closed semantiği tarama refaktöründen sağ çıktı."""
    kimlik = api.kayit_karar_kimligi("x-skill", "lean_in")
    store.append_jsonl(api.APPROVALS_LEDGER, {"id": kimlik, "decision": "belki", "ts": "t"})
    d = api._onay_defteri_karari(kimlik)
    assert d["karar"] == "bozuk" and d["bozuk"] == 1


def test_atfedilemeyen_satir_HALA_sayiliyor_kimseye_onay_vermiyor(sandbox_state):
    store.append_jsonl(api.APPROVALS_LEDGER, {"decision": "approve"})       # id YOK
    d = api._onay_defteri_karari("rec:loser-skill")
    assert d["karar"] is None and d["atfedilemeyen"] == 1


def test_defter_okunamazsa_GORUNUM_karari_UNUTUR_ama_SOYLER(sandbox_state, monkeypatch):
    """YÖN BİLİNÇLİ VE AYRI: kapı tarafında fail-closed "uygulama YOK" demektir; görünüm
    tarafında ise "kararı unut, yine sor" (kaybolan karar > gereksiz soru). İkisi karışmasın
    diye `okunamadi` çıktıda AÇIKÇA taşınır."""
    def _patla(*a, **k):
        raise OSError("defter okunamadı")
    monkeypatch.setattr(store, "read_jsonl", _patla)
    kk = api._karar_kaydi("x-skill", "lean_in")
    assert kk["karar"] is None and "defter okunamadı" in kk["okunamadi"]


# =============================================================================================
# PANO — düğme kayıtlı, cümle dürüst, sayı sunucudan
# =============================================================================================
def test_pano_karar_dugmesi_IZIN_LISTESINDE():
    """Kayıtsız bir `data-act` sessizce düşer (CSP delegasyon katmanı) — düğme çizilir, hiçbir
    şey olmaz. v219'un kapattığı "sessiz ölüm" sınıfının aynısı."""
    js = (REPO / "meridian" / "web" / "app.js").read_text()
    izin = js.split("const EYLEMLER = new Set([")[1].split("]);")[0]
    assert '"kararKaydet"' in izin, "karar düğmesi izin listesinde YOK — tıklama sessizce düşer"
    assert "window.kararKaydet" in js, "kayıtlı ama tanımsız eylem"


def test_pano_karar_dugmesi_ACTIONS_TAN_DEGIL_karar_kaydindan_doguyor():
    """`actions` UYGULAMA eylemlerinin listesidir. Kayıt düğmesini oraya koymak, v238'de
    kapatılan "uygulanamaz eylemi uygulanabilir gibi sunma" kusurunu geri getirirdi."""
    js = (REPO / "meridian" / "web" / "app.js").read_text()
    kod = "\n".join(l for l in js.splitlines() if not l.lstrip().startswith("//"))
    i = kod.index("const kararBtn")
    blok = kod[i:i + 700]
    assert "it.karar_kaydi" in kod[kod.index("const kk = it.karar_kaydi"):][:60]
    assert "kk.id" in blok and "data-act=\"kararKaydet\"" in blok
    assert "it.actions" not in blok, "kayıt düğmesi UYGULAMA listesinden türüyor"


def test_pano_DAVRANIS_DEGISMEZ_cumlesini_yaziyor():
    """YANLIŞ GÜVEN ÜRETMEME SÖZLEŞMESİ: operatör "Kabul"e bastıktan sonra davranışın
    değiştiğini SANMAMALI. Cümle sunucudan gelir (`KAYIT_KARARI_NOT`), panoda uydurulmaz."""
    assert "davranış DEĞİŞMEZ" in api.KAYIT_KARARI_NOT and "knob/kapı" in api.KAYIT_KARARI_NOT
    js = (REPO / "meridian" / "web" / "app.js").read_text()
    i = js.index("window.kararKaydet")
    assert "r.davranissal === false" in js[i:i + 900], "pano sunucunun sınır beyanını okumuyor"
    assert "kk.not" in js[js.index("function kararDamgasi"):][:1400]


def test_pano_ORNEKLEM_satirini_UC_HALDE_ayiriyor():
    """"Eşiği geçemedi" · "geçti" · "ölçülemedi" AYRI tonlarda okunmalı — üçü tek tonda
    gösterilirse ikisi de inandırıcılığını kaybeder (ve "ölçülemedi" bir kusur gibi görünür)."""
    js = (REPO / "meridian" / "web" / "app.js").read_text()
    i = js.index("function ornekSatiri")
    blok = js[i:i + 900]
    for alan in ("it.ornek", "it.ornek_notu", "it.ornek_yeterli"):
        assert alan in blok, f"{alan} panoda okunmuyor"
    assert "ornek_yeterli === false" in blok and "ornek_yeterli == null" in blok


def test_ogrenme_karti_damgayi_OKUYOR_ama_KARAR_YAZDIRMIYOR():
    """TEK KARAR YOLU: düğme yalnız gelen kutusunda. İki yüzey aynı gerçeği göstermeli
    (damga her ikisinde) ama aynı yazma eylemine iki kapı AÇILMAMALI (planOnayla deseni)."""
    js = (REPO / "meridian" / "web" / "app.js").read_text()
    i = js.index("const recCards")
    blok = js[i:js.index("$(\"ogrenme-eylem\")")]
    assert "kararDamgasi(rc.karar_kaydi)" in blok, "öğrenme kartı damgayı okumuyor"
    assert "kararKaydet" not in blok, "ikinci bir karar yazma yolu açılmış"


def test_api_hermes_ONERILERI_damgali_servis_ediyor(sandbox_state, monkeypatch):
    _kayit(); _canli_vaka(monkeypatch)
    _oneri("lean_in", "kazanan-skill")
    c = _istemci(monkeypatch)
    recs = c.get("/api/hermes").json()["skill_recommendations"]
    r = next(x for x in recs if x["skill"] == "kazanan-skill")
    assert r["karar_kaydi"]["id"] == "kayit:kazanan-skill:lean_in"
    assert r["ornek_yeterli"] is False

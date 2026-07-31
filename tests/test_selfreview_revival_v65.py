"""v65 — İKİ ÖLÜ MEKANİZMANIN DİRİLTİLMESİ (öz-değerlendirme + haftalık skill revizyonu).

CANLI ARIZA: state/events.jsonl son dönemde 424 `selfreview_failed` + 436 `skill_revision_week_failed`
taşıyordu, ikisi de aynı gerekçeyle: "AttributeError: 'str' object has no attribute 'get'". Her ikisi
de çağıranda obs.warn'a yutuluyordu; rapor hiç üretilmedi ve pano "dikkat maddesi yok" gösterdi —
SAKİN sistemle ARIZALI sistem ayırt edilemiyordu.

KÖK NEDEN: iki mekanizmanın ORTAK okuduğu tek defter, state/skill_revisions.json. Disk şekli
list[dict] değilken (`{skill: kayıt}` sözlüğü ya da çift-kodlanmış JSON metni) `for r in ...` satır
yerine ANAHTAR/KARAKTER — yani `str` — veriyor ve bir sonraki `r.get(...)` patlıyordu:
  * skill_evolve.pending_drafts  (weekly_draft yolu)
  * selfreview.build  → agent.revisions_pending sayacı
Eleme kanıtı: aynı dönemde `agent_skills_synced` olayları düzenli yazıldı — o yol skills.catalog()
ve analytics.skill_attribution()'ı koşturur, yani skill_evolve'un diğer tüm okuma yolları SAĞLAMDI;
geriye tek ortak defter kalıyor. Tek-nokta zehirleme taraması da bunu doğruladı: state'teki başka
HİÇBİR şekil bozukluğu iki mekanizmayı birlikte düşürmüyor.

Bu dosya üç şeyi kanıtlar: (1) gerçek bozuk şekiller artık rapor ÜRETİYOR, (2) gerçek üreticilerle
beslenen sistem BOŞ OLMAYAN, iyi biçimli bir rapor veriyor, (3) gerçekten sakin bir sistem DÜRÜST
biçimde boş rapor veriyor — ve kesinti hâli bu ikisinden AYIRT EDİLEBİLİR.
"""
from __future__ import annotations
import json
import pathlib

import pytest

from meridian import store, selfreview, skill_evolve as se

LIVE = pathlib.Path(__file__).resolve().parent.parent / "state"

# Canlıda gözlemlenen/üretilebilir bozuk defter şekilleri. Hiçbiri uydurma değil: birincisi
# "kayıtları skill adıyla anahtarla" refleksinin, ikincisi çift-kodlamanın, üçüncüsü de
# sözlük-üzerinde-döngünün diske geri yazılmasının doğal sonucu.
BROKEN_SHAPES = {
    "sozluk": {"vcp-screener": {"skill": "vcp-screener", "status": "draft",
                                "rationale": "stop disiplini", "evidence": {"n": 20, "avg_r": -0.3}}},
    "cift_kodlanmis": json.dumps([{"skill": "vcp-screener", "status": "draft",
                                   "rationale": "stop disiplini",
                                   "evidence": {"n": 20, "avg_r": -0.3}}]),
    "isim_listesi": ["vcp-screener"],
}


def _events(names: set[str]) -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl") if e.get("event") in names]


def _alarms(token: str) -> list[dict]:
    return [e for e in store.read_jsonl("events.jsonl") if e.get("alarm") == token]


# ------------------------------------------------------------------ 1) REGRESYON: canlı arıza
@pytest.mark.parametrize("shape", sorted(BROKEN_SHAPES))
def test_broken_revision_ledger_no_longer_kills_either_mechanism(sandbox_state, shape, monkeypatch):
    """CANLI HATANIN AYNISI: defter list[dict] değil. Eskiden İKİ mekanizma da
    'str object has no attribute get' ile düşerdi; artık ikisi de GERÇEK çıktı üretir."""
    monkeypatch.setattr(se, "_REPAIR_WARNED", False)
    store.write_json(se.REVISIONS_FILE, BROKEN_SHAPES[shape])

    # eski davranışın kanıtı: ham okuma bugün de bozuk ŞEKLİ döndürür (düzeltme okuyucuda, veride değil)
    raw = store.read_json(se.REVISIONS_FILE, [])
    assert not (isinstance(raw, list) and all(isinstance(r, dict) for r in raw)), \
        "fikstür bozuk şekli temsil etmiyor — regresyon testi anlamsızlaşır"
    with pytest.raises(AttributeError):
        [r for r in raw if r.get("status") == "draft"]        # ESKİ kod tam olarak buydu

    rep = selfreview.build()                                   # düşmemeli
    assert isinstance(rep, dict) and "attention" in rep and "progress" in rep
    assert isinstance(rep["agent"]["revisions_pending"], int)
    assert se.weekly_draft() is None                           # zayıf skill yok → dürüst "öneri yok"

    # defter ONARILDI ve onarım KAYDA GEÇTİ (sessiz bozulma görünür oldu)
    fixed = store.read_json(se.REVISIONS_FILE, None)
    assert isinstance(fixed, list) and all(isinstance(r, dict) for r in fixed)
    assert _events({"skill_revisions_repaired"}), "onarım sessiz kaldı — bozulma görünmez olurdu"
    # ve mekanizma sağlığı 'çalışıyor' diyor
    doc = store.read_json(selfreview.REVIEW_FILE, {})
    assert doc[selfreview.MECH_KEY]["self_review"]["ok"] is True
    assert doc[selfreview.MECH_KEY]["skill_revision"]["ok"] is True


def test_draft_bearing_ledger_survives_the_broken_shape(sandbox_state, monkeypatch):
    """Onarım VERİYİ KAYBETMEZ: sözlük şeklindeki bekleyen taslak, listeye çevrildikten sonra da
    hem gelen kutusunda hem raporun sayacında görünür."""
    monkeypatch.setattr(se, "_REPAIR_WARNED", False)
    store.write_json(se.REVISIONS_FILE, BROKEN_SHAPES["sozluk"])
    drafts = se.pending_drafts()
    assert [d["skill"] for d in drafts] == ["vcp-screener"]
    assert selfreview.build()["agent"]["revisions_pending"] == 1


# ------------------------------------------------------- 2) GERÇEK ÜRETİCİLERLE DOLU BİR RAPOR
def _seed_from_live_producers(monkeypatch, tmp_path):
    """Fikstür UYDURMAZ: canlı karşı-olgusal defteri birebir kopyalar ve türevleri GERÇEK
    üreticilerle (analytics.*, arming.setup_report, skill_evolve.draft_revision) üretir."""
    from meridian import analytics, arming, hermes
    src = LIVE / "counterfactuals.jsonl"
    if not src.exists():
        pytest.skip("canlı karşı-olgusal defter yok — gerçek-üretici testi atlanır")
    (store._state() / "counterfactuals.jsonl").write_text(src.read_text())

    analytics.near_miss_report()                       # → near_miss.json (gerçek üretici)
    analytics.score_calibration()                      # → score_calibration.json
    analytics.exit_efficiency()                        # → exit_efficiency.json
    store.write_json("arming_report.json",             # cf_report GERÇEK üreticiden
                     {"cf_report": arming.setup_report(), "measurements": {},
                      "rule": "test: canlı cf defterinden"})

    skill_dir = tmp_path / "skills" / "vcp-screener"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: vcp-screener\n---\nESKİ içerik. " * 30)
    monkeypatch.setattr(se, "_repo_skill_dir", lambda n: str(skill_dir))
    monkeypatch.setattr(hermes, "_agent_call",
                        lambda *a, **k: "<REVISED>---\nname: vcp-screener\n---\nYENİ. "
                                        + "x" * 300 + "</REVISED>\nRATIONALE: ölçülmüş zayıflık")
    assert se.draft_revision("vcp-screener"), "gerçek üretici taslak yazamadı"


def test_report_is_non_empty_and_wellformed_from_real_producers(sandbox_state, monkeypatch, tmp_path):
    """ÜRETKENLİK: gerçek kanıtla beslenen mekanizma BOŞ OLMAYAN, iyi biçimli bir rapor verir."""
    _seed_from_live_producers(monkeypatch, tmp_path)

    rep = selfreview.weekly()

    assert rep["week"]["cf_resolved"] is not None and rep["progress"]["setup_arming"], \
        "gerçek cf defteri kurulum kırılımı üretmeliydi"
    assert rep["attention"], "kanıt dolu bir sistemde DİKKAT listesi boş kalamaz"
    for a in rep["attention"]:
        assert set(a) >= {"why", "sev"} and a["sev"] in ("yüksek", "orta") and a["why"].strip()
    assert any("eşik-altı" in a["why"] for a in rep["attention"]), \
        "gerçek near_miss karnesi bir sonda önerisi doğurmalıydı"
    assert rep["agent"]["revisions_pending"] == 1        # gerçek üreticinin yazdığı taslak sayıldı
    assert rep[selfreview.MECH_KEY]["self_review"]["ok"] is True
    assert not any(a["why"].startswith(selfreview._OUTAGE_PREFIX) for a in rep["attention"])
    assert store.read_json(selfreview.REVIEW_FILE, None) == rep     # rapor DİSKE de düştü
    assert _events({"self_review_generated"}), "üretim olayı kaydedilmedi"


# ------------------------------------------------------------- 3) SAKİN SİSTEM = DÜRÜST BOŞ RAPOR
def test_calm_system_yields_an_honest_empty_report(sandbox_state):
    """KURT MASALI YOK: kanıt yoksa DİKKAT ve ÇELİŞKİ listeleri BOŞ olur — ve bu hâl,
    aşağıdaki kesinti hâlinden AYIRT EDİLEBİLİR (mechanisms.ok True vs False)."""
    rep = selfreview.weekly()
    assert rep["attention"] == [] and rep["contradictions"] == []
    assert rep["agent"]["revisions_pending"] == 0
    assert rep[selfreview.MECH_KEY]["self_review"] == {**rep[selfreview.MECH_KEY]["self_review"],
                                                       "ok": True, "streak": 0}
    assert se.weekly_draft() is None                    # aday yok ≠ arıza
    doc = store.read_json(selfreview.REVIEW_FILE, {})
    assert doc[selfreview.MECH_KEY]["skill_revision"]["ok"] is True
    assert doc["attention"] == []


# ------------------------------------------------------------------ 4) KESİNTİ SESSİZ KALAMAZ
def test_outage_is_an_alarm_not_a_shrug_and_is_distinguishable_from_calm(sandbox_state, monkeypatch):
    """400+ kez üst üste düşen mekanizma UYARI değil KESİNTİdir: seri sayacı, panonun okuduğu
    DİKKAT satırı ve MECHANISM_STALE alarmı. Boş rapor artık 'sakin' diye okunamaz."""
    selfreview.weekly()                                  # önce sakin hâl (boş DİKKAT)
    assert store.read_json(selfreview.REVIEW_FILE, {})["attention"] == []

    boom = RuntimeError("'str' object has no attribute 'get'")
    # ARIZA YALITILMIŞ bir bağlamda enjekte edilir. Eskiden `monkeypatch.setattr` + `monkeypatch.undo()`
    # kullanılıyordu; `undo()` o fikstürün TÜM yamalarını geri alır — `sandbox_state`in `config.STATE`
    # yaması DAHİL. Yani satır 178'den sonrası CANLI `state/`e yazıyordu: `self_review.json` eziliyor
    # (panonun okuduğu dosya) ve deftere iki MECHANISM_STALE ALARMI düşüyordu. Testin ürettiği sahte
    # alarm, gerçek bir kesintiden ayırt edilemez — kanıt kirlenmesinin en pahalı türü.
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(selfreview, "contradictions", lambda: (_ for _ in ()).throw(boom))
        for expected_streak in (1, 2):
            with pytest.raises(RuntimeError):
                selfreview.weekly()                      # hata YUTULMAZ — çağıran haftayı işaretlemesin
            doc = store.read_json(selfreview.REVIEW_FILE, {})
            mh = doc[selfreview.MECH_KEY]["self_review"]
            assert mh["ok"] is False and mh["streak"] == expected_streak
            rows = [a for a in doc["attention"] if a["why"].startswith(selfreview._OUTAGE_PREFIX)]
            assert len(rows) == 1 and rows[0]["sev"] == "yüksek"  # panoda görünür, tek satır (sel yok)

        al = _alarms("MECHANISM_STALE")
        assert len(al) == 2 and all(a["mechanism"] == "self_review" for a in al), \
            "kesinti alarmlanmadı — obs.warn seviyesi bu sınıf için yetersizdi"

    rep = selfreview.weekly()                            # arıza giderildi (sandbox AYAKTA kalır)
    assert rep[selfreview.MECH_KEY]["self_review"]["ok"] is True
    assert not any(a["why"].startswith(selfreview._OUTAGE_PREFIX) for a in rep["attention"])


def test_skill_revision_outage_surfaces_in_the_selfreview_report(sandbox_state, monkeypatch):
    """İkinci mekanizmanın kesintisi de AYNI panelde görünür — kendi paneli olmadığı için canlıda
    436 düşüş hiçbir yerde okunmuyordu."""
    monkeypatch.setattr(se, "weak_skills", lambda: (_ for _ in ()).throw(ValueError("defter bozuk")))
    with pytest.raises(ValueError):
        se.weekly_draft()
    rep = selfreview.build()
    row = [a for a in rep["attention"] if a.get("mechanism") == "skill_revision"]
    assert row and row[0]["sev"] == "yüksek" and "defter bozuk" in row[0]["why"]
    assert _alarms("MECHANISM_STALE")


# ------------------------------------------------------------------ 5) DANIŞMA SINIRI KORUNDU
def test_layer_stays_advisory(sandbox_state, monkeypatch):
    """Bu katman kapı kararlarına ASLA dokunmaz: kesinti hâlinde bile strateji/kapı dosyalarına
    yazılmaz — yalnız self_review.json ve (onarım hâlinde) skill_revisions.json değişir."""
    store.write_json(se.REVISIONS_FILE, BROKEN_SHAPES["sozluk"])
    before = {p.name for p in sandbox_state.glob("*")}
    selfreview.build()
    se.weekly_draft()
    touched = {p.name for p in sandbox_state.glob("*")} - before
    assert touched <= {"self_review.json", "events.jsonl", "skill_revisions.json",
                       "near_miss.json", "sieve.json"}, f"beklenmeyen yazım: {touched}"
    assert not (sandbox_state / "strategy.yaml").exists()

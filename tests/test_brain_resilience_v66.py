"""test_brain_resilience_v66.py — danışma beyninin iki ayrı arızası (canlı defter, 2026-07-19..22).

Defterdeki kanıt:
  92x hermes_brain_empty   (46 nous + 46 gemini)
  45x hermes_brain_failed  (44'ü gemini, HEPSİ aynı free-tier 429)
  35x agent_call_empty     (hepsi tried=1)
Satır sırası her turda aynıydı: nous empty → gemini failed(429) → gemini empty, üçü AYNI saniyede.
Yani (a) 429'a karşı hiçbir geri çekilme yoktu — sağlayıcı üç gün boyunca her turda yeniden arandı;
(b) BAŞARISIZ çağrı, hemen ardından bir kez de "boş" olarak yazılıyordu, yani 92 boşun ~44'ü aslında
çift-sayımdı ve gerçek sessiz bozunma (başarılı ama kullanılamaz cevap) bu gürültünün içinde kayboldu.

Bu dosya dört sözleşmeyi kilitler:
  1. 429 → sağlayıcı SAHADAN ALINIR (soğuma); sıcak yeniden-deneme döngüsü yok, zincir bir sonrakine geçer.
  2. "Başarılı ama boş" ≠ "başarısız": ayrı olay, SINIFI (no_text/refusal/tool_call_only/unparseable/
     schema_invalid) olayda yazılı ve kullanılabilir görüş olarak ASLA kaydedilmez.
  3. Beyin yokken sistem deterministik önericiye düşer ve bunu AÇIKÇA söyler — LLM görüşü gibi okunmaz.
  4. Kimlik havuzu tükendiyse ajan da dinlenmeye alınır; havuz sağlığı sayı olarak görünür (DEĞER asla).
Tüm ağ taşıması saplanmıştır: gerçek API çağrısı yok, fikstürlerde gizli/anahtar yok.
"""
import json
import shutil
import time
from pathlib import Path

import httpx
import pytest

from meridian import config, hermes, hermes_runtime, spend, store


@pytest.fixture
def seeded(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        if (repo / f).exists():
            shutil.copy2(repo / f, sandbox_state / f)
    config.goal.cache_clear(); config.bounds.cache_clear()
    return sandbox_state


@pytest.fixture
def brain(monkeypatch):
    """Beyin zincirini ölçülebilir hâle getir: gizli değerler sahte, ağ yok, prompt inşası saplı."""
    vals = {"HERMES_BRAIN_ORDER": "gemini", "GEMINI_API_KEY": "sahte-degil-gercek-anahtar-degil",
            "GEMINI_MODEL": "gemini-test"}
    monkeypatch.setattr(hermes.secrets, "get", lambda k: vals.get(k))
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: None)        # makinedeki gerçek ajan karışmasın
    monkeypatch.setattr(hermes, "_user_prompt", lambda: "SAPLI-PROMPT")
    monkeypatch.setattr(spend, "over_budget", lambda *a, **k: False)
    return vals


def _events(event: str | None = None) -> list[dict]:
    rows = store.read_jsonl("events.jsonl")
    return [r for r in rows if event is None or r.get("event") == event]


class _Resp:
    """httpx yanıtı taklidi — gövde ve durum kodu testin verdiği kadar; ağ yok."""

    def __init__(self, status=200, body=None, headers=None):
        self.status_code, self._body, self.headers = status, body or {}, headers or {}

    def json(self):
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"Client error '{self.status_code} Too Many Requests' for url "
                f"'https://generativelanguage.googleapis.com/v1beta/models/gemini-test:generateContent'",
                request=httpx.Request("POST", "https://generativelanguage.googleapis.com/v1beta/x"),
                response=httpx.Response(self.status_code, headers=self.headers))


def _stub_post(monkeypatch, responses: list):
    """httpx.post'u saplar; çağrı sayısını döndürür (sıcak döngü tespiti için asıl ölçü budur)."""
    calls = []

    def fake_post(url, **kw):
        calls.append(url)
        return responses[min(len(calls) - 1, len(responses) - 1)]
    monkeypatch.setattr(httpx, "post", fake_post)
    return calls


GOOD_HYP = {"variable": "entry.min_score", "new": 62, "rationale": "kanit",
            "predicted_direction": "improve_oos_score", "predicted_delta": 0.02,
            "confidence": 0.5, "regime": "chop"}


def _gemini_body(text: str) -> dict:
    return {"candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": "STOP"}],
            "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5}}


# ---------------------------------------------------------------- 1) 429 → SOĞUMA, sıcak döngü yok
def test_429_stands_the_provider_down_instead_of_hammering_it(seeded, brain, monkeypatch):
    calls = _stub_post(monkeypatch, [_Resp(429, headers={"retry-after": "12"})])

    assert hermes.propose_with_llm() is None
    assert len(calls) == 1, "tek turda tek çağrı olmalı — 429 sıcak yeniden-denemeye yol açmamalı"

    failed = _events("hermes_brain_failed")
    assert len(failed) == 1 and failed[0]["provider"] == "gemini"
    assert failed[0]["rate_limited"] is True
    assert failed[0]["cooldown_s"] > 0, "429 sonrası sağlayıcı sahadan ALINMALI"

    # DUR: 12 sn'lik retry-after tabanın altında kalır — tükenen kota günlüktür, 12 sn sonra dönmek
    # canlıda 45 özdeş başarısızlığı üreten davranışın ta kendisiydi.
    rem = hermes.brain_cooldown("gemini")
    assert rem >= hermes.BRAIN_COOLDOWN_BASE_S - 5

    # ve BAŞARISIZLIK "boş" olarak İKİNCİ kez yazılmaz (canlı defterdeki çift-sayımın kökü)
    assert _events("hermes_brain_empty") == []

    # ikinci tur: aynı sağlayıcıya HİÇ dokunulmaz
    assert hermes.propose_with_llm() is None
    assert len(calls) == 1, "soğumadaki sağlayıcı yeniden aranmamalı"
    cooled = _events("hermes_brain_cooldown")
    assert cooled and cooled[-1]["provider"] == "gemini" and cooled[-1]["remaining_s"] > 0


def test_429_chain_falls_over_to_the_next_provider(seeded, brain, monkeypatch):
    """Zincir ayakta kalır: 429 yiyen ayak sahadan alınır, sıradaki sağlayıcı öneriyi üretir."""
    brain["HERMES_BRAIN_ORDER"] = "gemini,nous"
    brain["NOUS_API_KEY"] = "sahte-nous"
    _stub_post(monkeypatch, [_Resp(429)])
    monkeypatch.setattr(hermes, "_propose_nous", lambda: dict(GOOD_HYP))

    hyp = hermes.propose_with_llm()
    assert hyp and hyp["source"] == "hermes:nous"
    assert hermes.brain_cooldown("gemini") > 0
    assert hermes.brain_cooldown("nous") == 0          # başaran ayak cezalandırılmaz
    assert hermes.active_brain() == "nous"             # soğumadaki gemini artık "aktif beyin" değil


# --------------------------------------------- 2) "başarılı ama boş" ≠ "başarısız" (asıl kusur)
@pytest.mark.parametrize("body,reason", [
    ({"candidates": [{"content": {"parts": []}, "finishReason": "STOP"}]}, hermes.EMPTY_NO_TEXT),
    ({"promptFeedback": {"blockReason": "SAFETY"}}, hermes.EMPTY_REFUSAL),
    ({"candidates": [{"content": {"parts": [{"functionCall": {"name": "x"}}]},
                      "finishReason": "STOP"}]}, hermes.EMPTY_TOOL_ONLY),
    ({"candidates": [{"content": {"parts": [{"text": "Elbette, şu değişkeni öneriyorum..."}]},
                      "finishReason": "STOP"}]}, hermes.EMPTY_UNPARSEABLE),
    ({"candidates": [{"content": {"parts": [{"text": '{"rationale":"variable alani yok"}'}]},
                      "finishReason": "STOP"}]}, hermes.EMPTY_SCHEMA),
    # KESİLME (v97, 2026-07-26): düşünce tokenları tavanı yiyince cevap yarım JSON olarak gelir.
    # Eskiden bu satır "unparseable" sayılıyordu — biçim suçlanıyor, bütçe arızası görünmez kalıyordu.
    ({"candidates": [{"content": {"parts": [{"text": '{"variable":"entry.min_score","rat'}]},
                      "finishReason": "MAX_TOKENS"}],
      "usageMetadata": {"promptTokenCount": 33107, "thoughtsTokenCount": 3838,
                        "candidatesTokenCount": 144}}, hermes.EMPTY_TRUNCATED),
])
def test_empty_but_successful_is_classified_distinctly(seeded, brain, monkeypatch, body, reason):
    _stub_post(monkeypatch, [_Resp(200, body)])

    assert hermes.propose_with_llm() is None            # kullanılabilir görüş ÜRETİLMEDİ

    empty = _events("hermes_brain_empty")
    assert len(empty) == 1, "başarılı-ama-boş cevap TAM BİR kez, kendi sınıfında kaydedilmeli"
    assert empty[0]["provider"] == "gemini"
    assert empty[0]["reason"] == reason, "sebep sınıfı olayda yazılı olmalı — hepsi 'boş' değildir"
    assert empty[0]["level"] == "warn"

    # başarısızlık DEĞİL: ne hata satırı, ne de sağlayıcıyı sahadan alan bir ceza
    assert _events("hermes_brain_failed") == []
    assert hermes.brain_cooldown("gemini") == 0, "boş cevap kota cezası değildir — zincir çalışmalı"


def test_empty_response_is_never_recorded_as_a_usable_opinion(seeded, monkeypatch):
    """Sessiz bozunmanın asıl bedeli: cevapsız bir inceleme, görüşmüş gibi deftere geçmemeli."""
    store.write_jsonl("trade_plans.jsonl", [
        {"id": "P-1", "date": "2026-07-20", "ticker": "AAA", "setup": "breakout_vcp",
         "entry_trigger": 10, "stop": 9, "score": 70, "gate_verdict": "GO"}])
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/sahte/hermes")
    monkeypatch.setattr(hermes, "_skill_preload", lambda *a, **k: [])
    monkeypatch.setattr(hermes, "_agent_call", lambda *a, **k: None)      # kota/arka uç: cevap yok

    assert hermes.review_candidates("2026-07-20") is None
    kayit = store.read_json("candidate_review.json", {}) or {}
    assert kayit.get("date") is None and not kayit.get("reviews"), \
        "boş inceleme GÖRÜŞ olarak dosyaya yazılmamalı (v233: sıkışıklık sayaçları `backlog` altında serbest)"
    plan = store.read_jsonl("trade_plans.jsonl")[0]
    assert "llm_opinion" not in plan, "cevapsız çağrıdan LLM görüşü damgalanamaz"


# ------------------------------------------------- 3) deterministik yol AÇIKÇA deterministik yazar
def test_deterministic_fallback_is_labelled_deterministic(seeded, brain, monkeypatch):
    _stub_post(monkeypatch, [_Resp(429)])
    assert hermes.propose_with_llm() is None            # 1. tur: 429 → soğuma
    assert hermes.propose_with_llm() is None            # 2. tur: hiç beyin kalmadı

    unavailable = _events("hermes_brain_unavailable")
    assert unavailable, "beyinsiz kalındığı AÇIKÇA kaydedilmeli — sessiz düşüş yasak"
    assert unavailable[-1]["providers"]["gemini"] in ("cooldown", "failed")
    assert "DETERMİNİSTİK" in unavailable[-1]["detail"]

    # görüntü katmanı da dürüst: soğumadaki sağlayıcı "aktif beyin" sayılmaz, model adı uydurulmaz
    assert hermes.active_brain() == "deterministic"
    assert hermes.active_model() is None
    st = hermes_runtime.status()
    assert st["brain"] == "deterministic" and st["brain_degraded"] is True
    assert st["brain_availability"]["gemini"]["ready"] is False
    assert st["brain_availability"]["gemini"]["cooling_s"] > 0
    assert st["brain_availability"]["gemini"]["reason"] == "rate_limit"

    # ve diske de öyle yazılır (pano bu dosyadan okur)
    hermes_runtime._persist()
    disk = store.read_json(hermes_runtime.STATUS_FILE, {})
    assert disk["brain"] == "deterministic" and disk["brain_degraded"] is True
    assert disk["model"] is None, "deterministik yol bir LLM model adı taşıyamaz"


def test_budget_gate_still_closes_every_paid_brain(seeded, brain, monkeypatch):
    """Soğuma mekanizması aylık bütçe kapısını devre dışı BIRAKMAZ (ayrı ve üstün bir kapı)."""
    calls = _stub_post(monkeypatch, [_Resp(200, _gemini_body(json.dumps(GOOD_HYP)))])
    monkeypatch.setattr(spend, "over_budget", lambda *a, **k: True)
    assert hermes.propose_with_llm() is None
    assert calls == [], "bütçe doluyken ücretli beyne HİÇ çağrı gitmemeli"
    assert _events("hermes_budget_gate")


# ------------------------------------------------------------------ 4) havuz sağlığı + ajan soğuması
def _fake_pool(tmp_path, monkeypatch, exhausted=True, at=None):
    """Sahte hermes-agent kurulumu. DİKKAT: fikstürde gerçek anahtar/token YOK — havuz satırları
    yalnız durum alanları taşır (kod da zaten yalnız sayıları okumalı)."""
    auth = tmp_path / "auth.json"
    auth.write_text(json.dumps({"credential_pool": {"gemini": [
        {"id": "aaaa", "label": "GEMINI_API_KEY", "source": "env:GEMINI_API_KEY",
         "last_status": "exhausted" if exhausted else "ok",
         "last_error_code": 429 if exhausted else None,
         "last_status_at": time.time() if at is None else at}]}}))
    cfg = tmp_path / "config.yaml"
    cfg.write_text("model:\n  provider: gemini\n  default: gemini-test\n")
    monkeypatch.setattr(hermes, "AGENT_AUTH_FILE", str(auth))
    monkeypatch.setattr(hermes, "AGENT_CONFIG", str(cfg))
    return auth, cfg


def test_exhausted_credential_pool_stands_the_local_agent_down(seeded, tmp_path, monkeypatch):
    """Havuz rotasyonu 429'u NEDEN absorbe edemedi: sağlayıcı başına tek kimlik ve o kimlik zaten
    'exhausted'. Round-robin tek elemanlı listede kimliktir. O hâlde ajan da dinlenmeye alınmalı."""
    import subprocess
    _fake_pool(tmp_path, monkeypatch, exhausted=True)
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/sahte/hermes")
    monkeypatch.setattr(hermes, "sync_agent_skills", lambda: None)
    monkeypatch.setattr(hermes.secrets, "get", lambda k: {"NOUS_MODEL": "gemini-test"}.get(k))
    runs = []

    class _Empty:
        returncode = 0
        stdout = "… | Messages:       1 (1 user, 0 tool calls)"
        stderr = ""
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: runs.append(list(cmd)) or _Empty())

    assert hermes._agent_call("soru", kind="t") is None
    assert len(runs) == 1
    ev = _events("agent_call_empty")[-1]
    assert ev["chain"] == 1 and ev["fallback_model_configured"] is False, \
        "zincir uzunluğu DÜRÜST bildirilmeli — 'tüm zincir' aslında tek modeldi"
    assert ev["pool_exhausted"] == "gemini" and ev["cooldown_s"] > 0
    assert hermes.brain_cooldown("agent") > 0

    # ikinci çağrı: bilinen-ölü sağlayıcı için süreç HİÇ başlatılmaz
    assert hermes._agent_call("soru", kind="t") is None
    assert len(runs) == 1
    assert _events("agent_call_cooldown")


def test_pool_health_reports_counts_and_never_leaks_credential_values(seeded, tmp_path, monkeypatch):
    auth, _ = _fake_pool(tmp_path, monkeypatch, exhausted=True)
    row = json.loads(auth.read_text())
    row["credential_pool"]["gemini"][0]["access_token"] = "SIZINTI-KANARYASI-0000"
    auth.write_text(json.dumps(row))

    h = hermes.pool_health()
    assert h["gemini"] == {"keys": 1, "exhausted": 1, "healthy": 0, "last_error_code": 429,
                           "last_status_at": h["gemini"]["last_status_at"]}
    assert "SIZINTI-KANARYASI" not in json.dumps(h), "havuz sağlığı ASLA kimlik değeri taşımaz"
    assert "SIZINTI-KANARYASI" not in json.dumps(hermes.integrations_status())
    # eski (pencere dışı) bir tükenme sonsuza dek bloklamaz
    _fake_pool(tmp_path, monkeypatch, exhausted=True, at=time.time() - hermes.POOL_EXHAUSTED_WINDOW_S - 60)
    assert hermes._pool_exhausted() is None


# ------------------------------------------------------------------------------ POZİTİF KONTROL
def test_positive_control_healthy_provider_trips_no_detector(seeded, brain, monkeypatch):
    """Tespit boş değil: AYNI koşum düzeneğinde sağlıklı bir cevap HİÇBİR kusur olayı üretmez,
    bozuk cevap ise tam olarak birini üretir. (Aksi hâlde yukarıdaki testler her şeyi 'kusurlu'
    gördüğü için de geçebilirdi — kurt masalı yasağı.)"""
    hermes.brain_stand_down("gemini", "kurulum")          # önce ceza var
    assert hermes.brain_cooldown("gemini") > 0

    hermes.brain_recovered("gemini")                       # sonra temizlenir
    _stub_post(monkeypatch, [_Resp(200, _gemini_body(json.dumps(GOOD_HYP)))])
    hyp = hermes.propose_with_llm()

    assert hyp is not None and hyp["source"] == "hermes:gemini"
    assert hyp["variable"] == "entry.min_score"
    for bad in ("hermes_brain_empty", "hermes_brain_failed", "hermes_brain_unavailable",
                "hermes_brain_cooldown"):
        assert _events(bad) == [], f"sağlıklı cevapta {bad} yazılmamalı"
    assert hermes.brain_cooldown("gemini") == 0
    assert hermes.active_brain() == "gemini"               # bozunma yok → dürüstçe LLM beyni

    # ve aynı düzenekte bozuk cevap ANINDA yakalanır (tespit vakum değil)
    _stub_post(monkeypatch, [_Resp(200, _gemini_body("bu JSON degil"))])
    assert hermes.propose_with_llm() is None
    assert [e["reason"] for e in _events("hermes_brain_empty")] == [hermes.EMPTY_UNPARSEABLE]


def test_recovery_clears_the_stand_down_streak(seeded, brain, monkeypatch):
    """Üstel ceza kalıcı değil: kullanılabilir tek bir cevap seriyi sıfırlar, yoksa bir kez 429 yiyen
    sağlayıcı kotası dönse bile giderek uzayan cezalarla fiilen ölü kalırdı."""
    _stub_post(monkeypatch, [_Resp(429)])
    hermes.propose_with_llm()
    first = store.read_json(hermes.BRAIN_COOLDOWN_FILE, {})["gemini"]["seconds"]
    hermes.brain_recovered("gemini")
    hermes.propose_with_llm()
    second = store.read_json(hermes.BRAIN_COOLDOWN_FILE, {})["gemini"]["seconds"]
    assert second == first, "seri sıfırlandıysa ceza yeniden tabandan başlar"
    hermes.brain_recovered("gemini")
    hermes.propose_with_llm(); hermes.brain_recovered("gemini")
    # üst üste iki başarısızlıkta (arada iyileşme yokken) ceza KATLANIR
    store.write_json(hermes.BRAIN_COOLDOWN_FILE, {})
    hermes.propose_with_llm()
    a = store.read_json(hermes.BRAIN_COOLDOWN_FILE, {})["gemini"]["seconds"]
    store.update_json(hermes.BRAIN_COOLDOWN_FILE,
                      lambda d: d["gemini"].update(until=0) or True, default={})
    hermes.propose_with_llm()
    b = store.read_json(hermes.BRAIN_COOLDOWN_FILE, {})["gemini"]["seconds"]
    assert b == min(a * 2, hermes.BRAIN_COOLDOWN_MAX_S)


# ================= KESİLME AYRI BİR SINIFTIR (v97, 2026-07-26) =================
# Canlı kök neden: gemini-3.5-flash DÜŞÜNEN bir model; düşünce tokenları üretim tavanından yeniyor.
# Ölçüm (aynı yansıma prompt'u, eski istek `maxOutputTokens: 4000`, düşünce ayarı YOK):
#     thoughtsTokenCount=3838 + candidatesTokenCount=144 ≈ 4000 · finishReason=MAX_TOKENS
# Cevap JSON'un rationale alanının ORTASINDA kesiliyor, _parse_hyp None dönüyor ve defter bunu
# "unparseable" diye yazıyordu. Yanlış ad yanlış düzeltmeye çağırır: biçim/prompt kurcalanır, asıl
# arıza (bütçe) hiç görünmez. Aşağısı üç şeyi kilitler: (1) kesilme KENDİ adıyla işaretlenir ve
# ölçülen token sayıları detayda durur; (2) kısmî metin ASLA ayrıştırıcıya gitmez; (3) sağlıklı
# cevapta ve eski üç sınıfta davranış AYNEN korunur (kurt masalı yasağı — ağ çağrısı yok).
def _take() -> tuple[str | None, str | None]:
    return hermes._trace_take()


TRUNCATED_BODY = {
    "candidates": [{"content": {"parts": [{"text": '{"variable": "exit.profit_target_r", "new": 2.0, "rat'}]},
                    "finishReason": "MAX_TOKENS"}],
    "usageMetadata": {"promptTokenCount": 33107, "thoughtsTokenCount": 3838,
                      "candidatesTokenCount": 144, "totalTokenCount": 37089},
}


def test_gemini_text_names_truncation_instead_of_blaming_the_format():
    _take()                                     # önceki testten neden artığı kalmasın
    assert hermes._gemini_text(TRUNCATED_BODY) == "", "yarım JSON kullanılamaz — ayrıştırıcıya gitmemeli"

    reason, detail = _take()
    assert reason == hermes.EMPTY_TRUNCATED, "kesilme 'unparseable' değildir: biçim değil bütçe arızası"
    assert "thoughts=3838" in detail, "asıl kanıt (düşünce tokenları) detayda görünmeli"
    assert "candidates=144" in detail
    assert f"cap={hermes.GEMINI_MAX_OUTPUT_TOKENS}" in detail, "hangi tavana çarpıldığı yazılı olmalı"


def test_gemini_text_reports_unmeasured_thought_tokens_as_none_not_zero():
    """UYDURMA YASAĞI: cevap thoughtsTokenCount taşımıyorsa 'thoughts=0' yazmak ölçülmemişi
    ölçülmüş göstermektir — düşünce KAPALIYKEN alan cevaba hiç konmuyor, ikisi aynı şey değil."""
    _take()
    body = {"candidates": [{"content": {"parts": [{"text": "yarim"}]}, "finishReason": "MAX_TOKENS"}],
            "usageMetadata": {"promptTokenCount": 10}}
    assert hermes._gemini_text(body) == ""
    reason, detail = _take()
    assert reason == hermes.EMPTY_TRUNCATED and "thoughts=None" in detail


def test_gemini_text_passes_a_complete_answer_through_untouched():
    """POZİTİF KONTROL: sağlıklı cevap (STOP + tam metin) metni AYNEN döndürür ve HİÇ iz bırakmaz —
    yoksa yukarıdaki testler 'her şeyi kesik gören' bir tespitle de geçerdi."""
    _take()
    txt = json.dumps(GOOD_HYP)
    assert hermes._gemini_text(_gemini_body(txt)) == txt
    assert _take() == (None, None), "kullanılabilir cevap için iz bırakılmamalı"


@pytest.mark.parametrize("body,reason", [
    ({"promptFeedback": {"blockReason": "SAFETY"}}, hermes.EMPTY_REFUSAL),
    ({"candidates": [{"content": {"parts": []}, "finishReason": "SAFETY"}]}, hermes.EMPTY_REFUSAL),
    ({"candidates": [{"content": {"parts": [{"functionCall": {"name": "x"}}]},
                      "finishReason": "STOP"}]}, hermes.EMPTY_TOOL_ONLY),
    ({"candidates": [{"content": {"parts": []}, "finishReason": "STOP"}]}, hermes.EMPTY_NO_TEXT),
])
def test_gemini_text_keeps_the_older_three_classes_unchanged(body, reason):
    """Yeni sınıf eskiyi YEMEDİ: reddin/araç-çağrısının/metinsizliğin adı aynı kaldı."""
    _take()
    assert hermes._gemini_text(body) == ""
    assert _take()[0] == reason


def test_truncated_request_now_asks_for_a_thinking_budget_and_a_bigger_cap(seeded, brain, monkeypatch):
    """İSTEK DÜZELTMESİ ölçülür: gövde düşünce bütçesini AÇIKÇA taşır ve tavan 4000'de kalmaz.
    (Canlı doğrulama 2026-07-26: bu gövdeyle finishReason=STOP, düşünce tokenı üretilmedi,
    _parse_hyp sözlük döndü.) Ağ yok — gönderilen gövdeyi sapla yakalıyoruz."""
    sent = {}

    def fake_post(url, **kw):
        sent.update(kw.get("json") or {})
        return _Resp(200, _gemini_body(json.dumps(GOOD_HYP)))
    monkeypatch.setattr(httpx, "post", fake_post)

    assert hermes.propose_with_llm()["source"] == "hermes:gemini"
    gc = sent["generationConfig"]
    assert gc["thinkingConfig"]["thinkingBudget"] == hermes.GEMINI_THINKING_BUDGET
    assert gc["maxOutputTokens"] == hermes.GEMINI_MAX_OUTPUT_TOKENS > 4000, \
        "eski 4000'lik tavan kesilmenin ta kendisiydi — emniyet payı kalmalı"


def test_thought_tokens_reach_the_ledger_and_its_reader(seeded, brain, monkeypatch):
    """MUHASEBE: düşünce tokenları faturalanan çıktıdır; defterde ayrı alan olarak durur ve
    spend.summary() (panonun okuduğu özet) onları toplar — üretilen alanın okuyucusu var."""
    body = {"candidates": [{"content": {"parts": [{"text": json.dumps(GOOD_HYP)}]},
                            "finishReason": "STOP"}],
            "usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 20,
                              "thoughtsTokenCount": 512}}
    _stub_post(monkeypatch, [_Resp(200, body)])

    assert hermes.propose_with_llm() is not None
    rows = store.read_jsonl("spend.jsonl")
    assert rows[-1]["thought_tokens"] == 512
    assert rows[-1]["out_tokens"] == 20, "düşünce tokenı görünür çıktıyı ŞİŞİRMEZ — ayrı alan"
    assert spend.summary()["thought_tokens"] == 512


def test_summary_thought_tokens_stay_none_when_nothing_measured(sandbox_state):
    """Ölçüm yoksa 0 değil None: 'düşünce yoktu' ile 'düşünce ölçülmedi' aynı cümle değildir."""
    spend.record(100, 50, "claude-opus-4-8", note="reflect")
    assert spend.summary()["thought_tokens"] is None
    spend.record(100, 50, "gemini-3.5-flash", note="reflect (gemini)", thought_tokens=0)
    assert spend.summary()["thought_tokens"] == 0, "ölçülüp sıfır çıkması ayrı bir olgudur"


# ============ KESİLME AYRI SINIFTIR — İKİNCİ SAĞLAYICI: NOUS/OpenRouter (v326, 2026-08-27) ============
# v97 bu sınıfı gemini için kapattı; PORTAL (OpenAI-uyumlu) ayağı ALMADI. Canlı kanıt (A1, 2026-08-27):
#   state/spend.jsonl — nvidia/nemotron ailesine 13 çağrı, 7'si TAM out_tokens=4000'de bitti (%54):
#     08-13T22:32 ultra-550b · 08-14T01:18 · 08-14T03:35 · 08-16T21:03 · 08-16T23:27 super-120b
#     08-17T20:19 super-120b (nous_eval) · 08-21T21:43 super-120b — girdi ~23-27k token.
#   Sağlayıcı sondası mekanizmayı gösterdi (aynı gün):
#     ultra, max_tokens=60   → finish_reason=length · içerik = modelin DÜŞÜNCE ön-eki · reasoning=62
#     ultra, max_tokens=2000 → finish_reason=stop   · içerik = '{"ok":true,"n":7}'      · reasoning=27
# YAPISAL KUSUR (bu dosyanın çivilediği şey): `_nous_text`te finish_reason ayrımı `if not txt.strip()`
# BLOĞUNUN İÇİNDEDİR. Kesilen cevap BOŞ DEĞİLDİR — içinde düşünce ön-eki vardır — yani o bloğa HİÇ
# GİRMEZ: metin çağırana döner, `_parse_hyp` JSON bulamaz ve defter "unparseable" yazar. Gemini'de
# kesilme kontrolü metin kontrolünden ÖNCE gelir (`_gemini_text` docstring'i); portalda o sıra yoktu.
# Yanlış ad yanlış düzeltmeye çağırır: biçim/prompt kurcalanır, asıl arıza (bütçe) görünmez kalır.
NOUS_ENV = {"HERMES_BRAIN_ORDER": "nous", "NOUS_API_KEY": "sahte-degil-gercek-anahtar-degil",
            "NOUS_ENDPOINT": "https://sahte-portal.invalid/v1",   # 'local' DEĞİL → portal yolu
            "NOUS_MODEL": "nvidia/nemotron-3-super-120b-a12b:free"}


@pytest.fixture
def nous_brain(monkeypatch):
    """Portal (uzak, OpenAI-uyumlu) nous ayağı: ağ saplı, yerel ajan ikilisi kapalı, prompt sabit."""
    monkeypatch.setattr(hermes.secrets, "get", lambda k: NOUS_ENV.get(k))
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: None)     # yerel ajan yolu KARIŞMASIN
    monkeypatch.setattr(hermes, "_user_prompt", lambda: "SAPLI-PROMPT")
    monkeypatch.setattr(spend, "over_budget", lambda *a, **k: False)
    return NOUS_ENV


# Canlı sondanın ölçtüğü gövdenin ta kendisi: finish_reason=length + DOLU içerik (düşünce ön-eki).
NOUS_TRUNCATED_BODY = {
    "choices": [{"finish_reason": "length",
                 "message": {"role": "assistant",
                             "content": "Okay, let me think about which variable to move. The "
                                        "evidence pack shows entry.min_score at 62 and the OOS"}}],
    "usage": {"prompt_tokens": 26411, "completion_tokens": 4000,
              "completion_tokens_details": {"reasoning_tokens": 3961}},
}


def _nous_body(text: str) -> dict:
    return {"choices": [{"finish_reason": "stop", "message": {"content": text}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5}}


def test_nous_text_names_truncation_instead_of_blaming_the_format(seeded, nous_brain, monkeypatch):
    """ASIL ÇİVİ: tavana çarpan cevap KENDİ adıyla işaretlenir ve kısmî metin ayrıştırıcıya GİTMEZ."""
    _take()                                    # önceki testten neden artığı kalmasın
    _stub_post(monkeypatch, [_Resp(200, NOUS_TRUNCATED_BODY)])

    assert hermes._nous_text("SAPLI-PROMPT", note="reflect (nous)") is None, \
        "düşünce ön-eki kullanılamaz — çağırana dönüp _parse_hyp'e gitmemeli"

    reason, detail = _take()
    assert reason == hermes.EMPTY_TRUNCATED, "kesilme 'unparseable' değildir: biçim değil bütçe arızası"
    assert "reasoning=3961" in detail, "asıl kanıt (akıl yürütme tokenları) detayda görünmeli"
    assert "completion=4000" in detail
    assert f"cap={hermes.NOUS_MAX_TOKENS}" in detail, "hangi tavana çarpıldığı yazılı olmalı"


def test_nous_text_reports_unmeasured_reasoning_tokens_as_none_not_zero(seeded, nous_brain, monkeypatch):
    """UYDURMA YASAĞI (gemini kardeşinin aynısı): sağlayıcı alanı hiç göndermediyse 'reasoning=0'
    yazmak ölçülmemişi ölçülmüş göstermektir. Her OpenAI-uyumlu uç bu alt alanı taşımaz."""
    _take()
    body = {"choices": [{"finish_reason": "length", "message": {"content": "yarim"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 4000}}
    _stub_post(monkeypatch, [_Resp(200, body)])

    assert hermes._nous_text("SAPLI-PROMPT", note="reflect (nous)") is None
    reason, detail = _take()
    assert reason == hermes.EMPTY_TRUNCATED and "reasoning=None" in detail


def test_nous_text_passes_a_complete_answer_through_untouched(seeded, nous_brain, monkeypatch):
    """POZİTİF KONTROL: sağlıklı cevap (stop + tam metin) AYNEN döner ve HİÇ iz bırakmaz — yoksa
    yukarıdaki testler 'her şeyi kesik gören' bir tespitle de geçerdi (kurt masalı yasağı)."""
    _take()
    txt = json.dumps(GOOD_HYP)
    _stub_post(monkeypatch, [_Resp(200, _nous_body(txt))])

    assert hermes._nous_text("SAPLI-PROMPT", note="reflect (nous)") == txt
    assert _take() == (None, None), "kullanılabilir cevap için iz bırakılmamalı"


def test_nous_truncation_is_never_recorded_as_unparseable(seeded, nous_brain, monkeypatch):
    """SÖZLEŞMENİN UÇTAN UCA HÂLİ: defterdeki satırın SINIFI 'truncated' olmalı, 'unparseable' değil.
    Canlı defterde bu satır `nous_eval_unparseable`/`hermes_brain_empty(unparseable)` diye duruyordu
    ve bütçe arızasını biçim arızası gibi okutuyordu."""
    _stub_post(monkeypatch, [_Resp(200, NOUS_TRUNCATED_BODY)])

    assert hermes.propose_with_llm() is None                # kullanılabilir görüş ÜRETİLMEDİ

    empty = _events("hermes_brain_empty")
    assert len(empty) == 1, "başarılı-ama-kesik cevap TAM BİR kez kaydedilmeli"
    assert empty[0]["provider"] == "nous"
    assert empty[0]["reason"] == hermes.EMPTY_TRUNCATED, \
        "bütçe arızası biçim arızası (unparseable) diye yazılamaz — düzeltmeyi görünmez kılar"
    assert empty[0]["reason"] != hermes.EMPTY_UNPARSEABLE
    assert "reasoning=3961" in (empty[0].get("detail") or ""), "token sayıları olayda durmalı"
    assert _events("hermes_brain_failed") == [], "kesilme bir HATA değildir — sağlayıcı cezalandırılmaz"
    assert hermes.brain_cooldown("nous") == 0


def test_nous_request_carries_a_ceiling_above_the_measured_truncation_point(seeded, nous_brain, monkeypatch):
    """Tavan artık ADLANDIRILMIŞ ve env ile ayarlanabilir (gemini emsali: GEMINI_MAX_OUTPUT_TOKENS)
    ve canlıda 7 çağrıyı kesen 4000'in ÜSTÜNDE olmalı — yoksa düzeltme adı var, etkisi yok."""
    govdeler = []

    def fake_post(url, **kw):
        govdeler.append(kw.get("json") or {})
        return _Resp(200, _nous_body(json.dumps(GOOD_HYP)))
    monkeypatch.setattr(httpx, "post", fake_post)

    hermes._nous_text("SAPLI-PROMPT", note="reflect (nous)")
    assert govdeler, "istek gövdesi ölçülemedi"
    assert govdeler[0]["max_tokens"] == hermes.NOUS_MAX_TOKENS
    assert hermes.NOUS_MAX_TOKENS > 4000, "canlıda 13 çağrının 7'sini kesen tavan 4000'di"


def test_nous_reasoning_control_is_absent_unless_the_operator_configures_it(seeded, nous_brain, monkeypatch):
    """UYDURMA YASAĞI, İSTEK GÖVDESİ SÜRÜMÜ: `reasoning` alanının bu sağlayıcıdaki şekli bu depodan
    DOĞRULANAMADI (bkz. hermes.NOUS_REASONING_EFFORT yorumu). Doğrulanmamış parametre canlıya
    VARSAYILAN olarak gitmez — kol yalnız operatör açıkça açarsa gövdeye girer."""
    govdeler = []

    def fake_post(url, **kw):
        govdeler.append(kw.get("json") or {})
        return _Resp(200, _nous_body(json.dumps(GOOD_HYP)))
    monkeypatch.setattr(httpx, "post", fake_post)

    monkeypatch.setattr(hermes, "NOUS_REASONING_EFFORT", "")
    hermes._nous_text("SAPLI-PROMPT", note="reflect (nous)")
    assert "reasoning" not in govdeler[0], "kapalıyken alan gövdede HİÇ bulunmamalı"

    monkeypatch.setattr(hermes, "NOUS_REASONING_EFFORT", "low")
    hermes._nous_text("SAPLI-PROMPT", note="reflect (nous)")
    assert govdeler[1]["reasoning"] == {"effort": "low"}


def test_nous_reasoning_tokens_reach_the_spend_ledger(seeded, nous_brain, monkeypatch):
    """Düşünce tokenları FATURALANAN çıktıdır ve gemini ayağında zaten deftere yazılıyor. Portal
    ayağında hiç yazılmıyordu — tam da tavanı yiyen sayı görünmez kalıyordu."""
    _stub_post(monkeypatch, [_Resp(200, NOUS_TRUNCATED_BODY)])
    hermes._nous_text("SAPLI-PROMPT", note="reflect (nous)")

    satir = store.read_jsonl("spend.jsonl")[-1]
    assert satir["out_tokens"] == 4000 and satir["thought_tokens"] == 3961

    # ölçülmeyen alan satıra HİÇ yazılmaz (0 yazmak ölçülmemişi ölçülmüş göstermek olurdu)
    _stub_post(monkeypatch, [_Resp(200, _nous_body(json.dumps(GOOD_HYP)))])
    hermes._nous_text("SAPLI-PROMPT", note="reflect (nous)")
    assert "thought_tokens" not in store.read_jsonl("spend.jsonl")[-1]


@pytest.mark.parametrize("body,reason", [
    ({"choices": [{"finish_reason": "stop", "message": {"content": ""}}]}, hermes.EMPTY_NO_TEXT),
    ({"choices": [{"finish_reason": "content_filter", "message": {"content": ""}}]}, hermes.EMPTY_REFUSAL),
    ({"choices": [{"finish_reason": "tool_calls", "message":
                   {"content": "", "tool_calls": [{"id": "x"}]}}]}, hermes.EMPTY_TOOL_ONLY),
])
def test_nous_text_keeps_the_older_three_classes_unchanged(seeded, nous_brain, monkeypatch, body, reason):
    """KURT MASALI YASAĞI: yeni sınıf eskileri yutmamalı — boş/red/araç yolları AYNEN kalır."""
    _take()
    _stub_post(monkeypatch, [_Resp(200, body)])
    assert hermes._nous_text("SAPLI-PROMPT", note="reflect (nous)") is None
    assert _take()[0] == reason


# ===== TAVAN ZAMAN AŞIMI İÇİNDE ULAŞILABİLİR OLMALI (v326, 2026-08-27) =====
# Bu bölüm, ilk düzeltmenin KENDİ kusurunu çivilemek için var. Tavan 4000→16384'e çıkarıldı ama
# `timeout=120.0` sabiti ELDE KALMIŞTI. `docs/OLCUM-MODEL-BUTCESI-2026-08-27.md` §3-4 bunun neden
# bir düzeltme DEĞİL ad değişikliği olduğunu ölçmüş: Ultra 25,8 tok/sn üretir, yani 120 sn'de ancak
# ~3.096 token — yükseltilen tavana ULAŞAMADAN zaman aşımına düşer. Üstelik o yolda httpx cevap
# dönmeden istisna atar, yani bu turda eklenen `truncated` sınıflandırması HİÇ ateşlenmez ve olay
# `nous_chain_failed`e düşer: bütçe arızası bu sefer TAŞIMA arızası gibi okunur.
def test_the_ceiling_must_be_reachable_within_the_timeout(seeded):
    """İNVARYANT: en yavaş ÖLÇÜLEN model, zaman aşımı dolmadan tavan kadar token üretebilmeli.
    Bu çivi tavanı da zaman aşımını da SABİTLEMEZ — aralarındaki BAĞI sabitler. İkisinden biri
    elle değiştirilir de öbürü unutulursa (bu turda tam olarak bu oldu) kırmızıya döner."""
    gereken_sn = hermes.NOUS_MAX_TOKENS / hermes.NOUS_OLCULEN_TOK_SN
    assert hermes.NOUS_TIMEOUT_S >= gereken_sn, (
        f"tavan {hermes.NOUS_MAX_TOKENS} token, en yavaş ölçülen model {hermes.NOUS_OLCULEN_TOK_SN} "
        f"tok/sn → en az {gereken_sn:.0f} sn gerekir, ama zaman aşımı {hermes.NOUS_TIMEOUT_S} sn. "
        "Bu hâlde kesilme zaman aşımına dönüşür ve `truncated` sınıfı HİÇ ateşlenmez.")


def test_the_invariant_is_not_a_tautology_it_can_actually_go_red(seeded):
    """ÇİVİNİN KENDİSİNİ SINAR. İlk sürümde `NOUS_TIMEOUT_S` tavandan TÜRETİLİYORDU
    (tavan/hız × 1,4) ve invaryant "zaman aşımı >= tavan/hız" diye sınıyordu — yani varsayılan
    yolda 1,4 > 1 olduğu için ASLA kırmızıya dönemezdi: ölçen değil kendi kendini onaylayan bir
    kontrol. Değer artık §6 tablosundan BAĞIMSIZ geliyor; aşağısı bağın gerçekten sınandığını
    gösterir — tavan yükseltilip zaman aşımı elde bırakılırsa invaryant ÇİĞNENİR."""
    # yayımlanmış çift invaryantı SAĞLAR
    assert hermes.NOUS_TIMEOUT_S >= hermes.NOUS_MAX_TOKENS / hermes.NOUS_OLCULEN_TOK_SN

    # ama tavan iki katına çıkarılıp zaman aşımı AYNI bırakılırsa ÇİĞNENİR — çivi o gün kırmızı olur
    iki_kat = hermes.NOUS_MAX_TOKENS * 2
    assert hermes.NOUS_TIMEOUT_S < iki_kat / hermes.NOUS_OLCULEN_TOK_SN, (
        "invaryant ayırt etmiyor: tavanı iki katına çıkarmak bile onu çiğnemiyorsa kontrol "
        "totolojidir (ilk sürümün kusuru buydu — değer tavandan türetiliyordu)")


def test_the_timeout_matches_the_published_budget_table(seeded):
    """§6 tablosunun "arka plan derin (yansıma)" satırı: Ultra · 16.384 token · 900 sn.
    Kaynaktaki sayı yayımlanmış tablodan AYRILIRSA belge ile kod sessizce ayrışmış olur."""
    assert hermes.NOUS_MAX_TOKENS == 16384, "§6 'arka plan derin' satırının max_tokens'ı"
    assert hermes.NOUS_TIMEOUT_S == 900.0, "§6 'arka plan derin' satırının timeout'u"


def test_the_old_hardcoded_120s_timeout_could_not_reach_even_the_old_ceiling(seeded):
    """ÇÜRÜTME BACAĞI — invaryantın totoloji OLMADIĞINI gösterir: eski çift (4000 token, 120 sn)
    bu invaryantı ÇİĞNİYORDU (120 < 4000/25,8 ≈ 155 sn). Yani çivi gerçekten ayırt ediyor;
    'her zaman geçen' bir kontrol değil."""
    assert 120.0 < 4000 / hermes.NOUS_OLCULEN_TOK_SN, \
        "eski çift invaryantı çiğnemeliydi — çiğnemiyorsa bu çivi hiçbir şey ölçmüyor demektir"


def test_nous_request_uses_the_derived_timeout_not_a_hardcoded_one(seeded, nous_brain, monkeypatch):
    """Türetilen sayı GERÇEKTEN çağrıya gidiyor mu — yoksa sabit adlandırılmış olur, uygulanmış olmaz."""
    gecen = {}

    def fake_post(url, **kw):
        gecen.update(kw)
        return _Resp(200, _nous_body(json.dumps(GOOD_HYP)))
    monkeypatch.setattr(httpx, "post", fake_post)

    hermes._nous_text("SAPLI-PROMPT", note="reflect (nous)")
    assert gecen["timeout"] == hermes.NOUS_TIMEOUT_S
    assert gecen["timeout"] > 120.0, "eski sabit 120 sn tavana yetişemiyordu (ölçüm §4)"


def test_the_ceiling_stays_under_the_measured_provider_limits(seeded):
    """Tavan sağlayıcının İZİN VERDİĞİNİN üstüne çıkarsa istek sağlayıcıda reddedilir. Ölçülen
    değerler (§1): ultra:free max_completion=65.536 · super:free=235.929. Bağlayan taraf KÜÇÜK olan."""
    assert hermes.NOUS_MAX_TOKENS <= 65536, "ultra:free'nin ölçülen max_completion tavanı"

"""test_brain_chain_facts_v96.py — "ÜÇ BEYİN" BİR SAYIM DEĞİL, BİR VARSAYIMDI (2026-07-26).

`DEFAULT_BRAIN_ORDER` üç ad taşıyor; pano iki yeşil çip gösteriyordu. Canlı olgu: claude kimliksiz
(atlanıyor), nous ile gemini AYNI model kimliğine gidiyordu ve yerel ajan modunda nous'un "gidecek
modeli" hiç ÖLÇÜLMÜYORDU — varsayılan yazılıyor, o varsayılan da "model kimlikleri ayrık" hükmüne
dönüşüyordu. Yani ölçülmemiş bir yedeklilik iddiasının kaynağı, kendi uydurduğumuz varsayılandı.

Bu dosya YALNIZ ölçülebilir olguları kilitler:
  1. Aynı model kimliğine giden ÇİFT yakalanır; kimliği None olan beyin çifte hiç girmez.
  2. `independent_upstreams` None KALIR — çağrı başına hangi uca gidildiği ölçülmüyor, uydurulmaz.
  3. Yerel ajan + NOUS_MODEL yoksa nous model kimliği None'dır (varsayılan yazmak uydurmadır).
  4. Bekçi satırı: ready>1 + aynı kimlik → kırmızı; TEK ready → yeşil (kurt masalı yasağı).
  5. Bekçi satırı: yerel ajan başka bir hazır beynin sağlayıcısına kurulmuşsa → kırmızı (paylaşılan
     kota bir çıkarım değil, config.yaml'da OKUNAN bir olgudur).
Hiçbir ağ çağrısı yok; `~/.hermes/config.yaml` conftest tarafından tmp yola yönlendirilmiştir.
"""
from __future__ import annotations

import pytest

from meridian import hermes, watchdog as wd


def _keys(monkeypatch, **vals):
    """`secrets.get`i SÖZLÜĞE sabitle — makinedeki gerçek anahtarlar ölçümü değiştirmesin."""
    monkeypatch.setattr(hermes.secrets, "get", lambda k, *a, **kw: vals.get(k))


def _agent_config(text: str) -> None:
    """Yerel ajan yapılandırmasını YAZ (conftest AGENT_CONFIG'i tmp yola çevirdi)."""
    import pathlib
    pathlib.Path(hermes.AGENT_CONFIG).write_text(text)


# ---------------------------------------------------------------------------------------------
# (a) brain_chain_facts — birim
# ---------------------------------------------------------------------------------------------
def test_two_ready_brains_on_the_same_model_id_are_caught(sandbox_state, monkeypatch):
    _keys(monkeypatch, NOUS_API_KEY="n", GEMINI_API_KEY="g",
          NOUS_MODEL="gemini-3.5-flash", GEMINI_MODEL="gemini-3.5-flash",
          HERMES_BRAIN_ORDER="nous,gemini")
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: None)      # portal modu (yerel ikili yok)

    f = hermes.brain_chain_facts()
    assert f["ready"] == ["nous", "gemini"]
    assert f["same_model_ids"] == [["gemini", "nous"]], \
        f"aynı model kimliğine giden çift yakalanmadı: {f['same_model_ids']}"


def test_a_brain_whose_model_id_is_unmeasured_never_enters_a_pair(sandbox_state, monkeypatch):
    """ÖLÇÜLMEMİŞ KİMLİK BİR EŞLEŞME KANITI DEĞİLDİR. nous yerel ajan modunda ve NOUS_MODEL boş →
    kimlik None. None'ı "eşit" saymak da "ayrık" saymak da uydurma olurdu; çift hiç kurulmaz."""
    _keys(monkeypatch, GEMINI_API_KEY="g", HERMES_BRAIN_ORDER="nous,gemini")
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/tmp/hermes")   # yerel ikili VAR → local_agent

    f = hermes.brain_chain_facts()
    assert f["nous_mode"] == "local_agent"
    assert f["models"]["nous"] is None, "yerel ajan modunda 'gidecek model' UYDURULDU"
    assert set(f["ready"]) == {"nous", "gemini"}                  # yerel kurulum anahtar istemez
    assert f["same_model_ids"] == [], "kimliği ölçülmemiş beyin çifte sokuldu"


def test_independent_upstreams_stays_none_with_a_written_reason(sandbox_state, monkeypatch):
    _keys(monkeypatch, NOUS_API_KEY="n", GEMINI_API_KEY="g")
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: None)
    f = hermes.brain_chain_facts()
    assert f["independent_upstreams"] is None, "ölçülmeyen bağımsız uç sayısı ÜRETİLDİ"
    assert len(f.get("independent_upstreams_reason") or "") > 30, "None'ın NEDENİ yazılmamış"


def test_portal_mode_keeps_the_default_model_because_it_is_measurable(sandbox_state, monkeypatch):
    """Portal modunda istek gövdesini BİZ kuruyoruz: NOUS_MODEL boşsa gerçekten varsayılana gider.
    Orada varsayılan bir UYDURMA değil, ÖLÇÜMdür — kural yalnız yerel ajan modunu daraltır."""
    _keys(monkeypatch, NOUS_API_KEY="n", NOUS_ENDPOINT="https://portal.example/v1")
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: None)
    assert hermes._model_id("nous") == hermes.NOUS_DEFAULT_MODEL
    assert hermes.brain_chain_facts()["nous_mode"] == "portal"


# ---------------------------------------------------------------------------------------------
# (b) watchdog makullük satırı
# ---------------------------------------------------------------------------------------------
def _row(name: str):
    return next((r for r in wd.parity_report()["rows"] if r["check"] == name), None)


def _status(monkeypatch, chain: dict, availability: dict | None = None):
    from meridian import hermes_runtime as hr
    monkeypatch.setattr(hr, "status", lambda: {"brain_chain": chain,
                                               "brain_availability": availability or {}})


def test_watchdog_flags_two_ready_brains_sharing_one_model_id(sandbox_state, monkeypatch):
    _status(monkeypatch, {"order": ["nous", "gemini"], "ready": ["nous", "gemini"],
                          "models": {"nous": "gemini-3.5-flash", "gemini": "gemini-3.5-flash"},
                          "same_model_ids": [["gemini", "nous"]],
                          "nous_mode": "portal", "agent_config_provider": None})
    r = _row("brain_chain_distinct")
    assert r and r["ok"] is False, "iki ad tek kimliğe gidiyor ama satır yeşil"
    assert "AYNI model kimliğiyle" in r["detail"]
    assert "nous modu: portal" in r["detail"], "ölçülen mod detayda görünmüyor (alan okuyucusuz)"


def test_watchdog_stays_green_with_a_single_ready_brain(sandbox_state, monkeypatch):
    """KURT MASALI YASAĞI: tek beyin varken 'yedeklilik yok' demek boş bir alarmdır — ve kirli bir
    temel mutasyon bataryasının kapsama sayısını yalancı yapar."""
    _status(monkeypatch, {"order": ["nous", "gemini"], "ready": ["nous"],
                          "models": {"nous": "x-1", "gemini": None},
                          "same_model_ids": [], "nous_mode": "portal",
                          "agent_config_provider": None})
    r = _row("brain_chain_distinct")
    assert r and r["ok"] is True, f"tek hazır beyinde kurt masalı: {r}"


def test_watchdog_flags_a_local_agent_installed_on_another_ready_brains_upstream(
        sandbox_state, monkeypatch):
    """ÖLÇÜLEN OLGU, ÇIKARIM DEĞİL: `~/.hermes/config.yaml` içindeki `model.provider` alanı okunur.
    'gemini' yazıyorsa zincirin nous ayağı ile gemini ayağı AYNI kotaya bakıyordur — model kimliği
    ölçülemediği için `same_model_ids` bu durumu GÖREMEZ ve satır haksız yere yeşil kalırdı."""
    _status(monkeypatch, {"order": ["nous", "gemini"], "ready": ["nous", "gemini"],
                          "models": {"nous": None, "gemini": "gemini-3.5-flash"},
                          "same_model_ids": [], "nous_mode": "local_agent",
                          "agent_config_provider": "gemini"})
    r = _row("brain_chain_distinct")
    assert r and r["ok"] is False, "paylaşılan üst-akış görülmedi — yedeklilik ölçülmeden iddia edildi"
    assert "aynı kota" in r["detail"] and "gemini" in r["detail"]


def test_a_local_agent_on_an_unrelated_provider_is_not_flagged(sandbox_state, monkeypatch):
    """Ajanın sağlayıcısı zincirdeki HAZIR beyinlerden biri DEĞİLSE paylaşım ölçülmemiştir; satır
    kırmızıya dönmez. Ölçülmeyen bir çakışmayı varsaymak da uydurmadır."""
    _status(monkeypatch, {"order": ["nous", "gemini"], "ready": ["nous", "gemini"],
                          "models": {"nous": None, "gemini": "gemini-3.5-flash"},
                          "same_model_ids": [], "nous_mode": "local_agent",
                          "agent_config_provider": "openrouter"})
    r = _row("brain_chain_distinct")
    assert r and r["ok"] is True, f"ilgisiz sağlayıcı kırmızıya çevirdi: {r}"


# ---------------------------------------------------------------------------------------------
# (c) suite izolasyonu — ölçüm operatörün MAKİNESİNE bağlı olamaz
# ---------------------------------------------------------------------------------------------
def test_the_real_agent_config_never_leaks_into_the_suite(sandbox_state):
    """`AGENT_CONFIG` gerçek `~/.hermes/config.yaml`i gösterseydi bu ölçüm makineden makineye
    değişirdi ve geçtiğinde bir şey KANITLAMAZDI."""
    assert "/.hermes/" not in hermes.AGENT_CONFIG, \
        f"suite gerçek ajan yapılandırmasını okuyor: {hermes.AGENT_CONFIG}"
    assert hermes._agent_provider() is None, "dosya yokken sağlayıcı UYDURULDU"
    _agent_config("model:\n  provider: gemini\n  name: gemini-3.5-flash\n")
    assert hermes._agent_provider() == "gemini", "yazılan sağlayıcı okunamadı"

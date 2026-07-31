"""test_notify_obs_audit_v34.py — notify (tur 19) + obs (tur 20) denetimi, 2026-07-21.

7. soru:
  N1 "asla sır göndermez"        → notify dışarıya veri gönderen TEK yol; bir alarm metni bir hata
     dizgisi taşırsa (…?apikey=…) sır MAKİNEDEN ÇIKAR. İddia docstring'deydi, uygulaması yoktu.
  N2 "teslimat başarısızlığı görünür" → kanal cevap vermezse alarm sessizce buharlaşıyordu:
     'telefonuma bildirim gelmedi' ile 'zaten alarm yoktu' ayırt edilemezdi.
  O1 "kritik alarmlar operatöre ulaşır" → BULGU: bildirim izin listesinde HALT_ACTIVE, ROLLBACK ve
     HEARTBEAT_STALE YOKTU — yani "beni uyandır" sınıfının tamamı sessizdi.
"""
from __future__ import annotations

import pytest

from meridian import notify, obs, store


# ---------- N1: sır temizliği ----------
def test_n1_secrets_are_scrubbed_before_sending(monkeypatch):
    monkeypatch.setattr(notify.secrets, "ALLOWED", ["FMP_API_KEY"], raising=False)
    monkeypatch.setattr(notify.secrets, "get",
                        lambda n, *a, **k: "SUPERSECRETKEY123" if n == "FMP_API_KEY" else None)
    out = notify.scrub("hata: GET https://x/stable/quote?apikey=SUPERSECRETKEY123 → 429")
    assert "SUPERSECRETKEY123" not in out and "***" in out


def test_n1b_send_scrubs_the_payload(monkeypatch):
    sent = {}
    monkeypatch.setattr(notify.secrets, "ALLOWED", ["FMP_API_KEY", "TELEGRAM_BOT_TOKEN",
                                                    "TELEGRAM_CHAT_ID"], raising=False)
    monkeypatch.setattr(notify.secrets, "get", lambda n, *a, **k: {
        "FMP_API_KEY": "SUPERSECRETKEY123", "TELEGRAM_BOT_TOKEN": "bot-token-xyz",
        "TELEGRAM_CHAT_ID": "42"}.get(n))
    monkeypatch.setattr(notify, "_post", lambda url, payload, timeout=8.0: sent.update(payload) or True)
    notify.send("anahtar SUPERSECRETKEY123 sızdı")
    assert "SUPERSECRETKEY123" not in sent["text"]


# ---------- N2: sessiz teslimat hatası ----------
def test_n2_failed_delivery_is_recorded(sandbox_state, monkeypatch):
    monkeypatch.setattr(notify.secrets, "ALLOWED", [], raising=False)
    monkeypatch.setattr(notify.secrets, "get", lambda n, *a, **k: {
        "TELEGRAM_BOT_TOKEN": "t", "TELEGRAM_CHAT_ID": "c"}.get(n))
    monkeypatch.setattr(notify, "_post", lambda *a, **k: False)
    assert notify.send("test") is False
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "notify_delivery_failed"]
    assert ev and "telegram" in ev[-1]["channels"]


def test_n2b_successful_delivery_is_quiet(sandbox_state, monkeypatch):
    monkeypatch.setattr(notify.secrets, "ALLOWED", [], raising=False)
    monkeypatch.setattr(notify.secrets, "get", lambda n, *a, **k: {
        "TELEGRAM_BOT_TOKEN": "t", "TELEGRAM_CHAT_ID": "c"}.get(n))
    monkeypatch.setattr(notify, "_post", lambda *a, **k: True)
    assert notify.send("test") is True
    assert not [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "notify_delivery_failed"]


def test_n2c_unconfigured_is_a_safe_noop(sandbox_state, monkeypatch):
    monkeypatch.setattr(notify.secrets, "ALLOWED", [], raising=False)
    monkeypatch.setattr(notify.secrets, "get", lambda n, *a, **k: None)
    assert notify.configured() is False and notify.send("x") is False
    assert not [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "notify_delivery_failed"]


# ---------- O1: kritik alarmlar bildirime dahil ----------
def test_o1_wake_me_up_alarms_are_notifiable():
    for tok in (obs.ALARM_HALT, obs.ALARM_ROLLBACK, obs.ALARM_HEARTBEAT_STALE,
                obs.ALARM_CIRCUIT_BREAKER):
        assert tok in obs.NOTIFY_TOKENS, f"{tok} operatöre ulaşmıyor — panel açılmadan görünmez"


def test_o1b_every_alarm_constant_is_classified():
    """Her ALARM_* ya bildirilir ya da BİLEREK bildirilmez; ikisi de listede olmalı ki sessizlik
    bir karar olsun, unutkanlık değil."""
    consts = {v for k, v in vars(obs).items() if k.startswith("ALARM_")}
    deliberately_quiet = set()          # şu an hepsi bildirilecek sınıfta
    assert consts - obs.NOTIFY_TOKENS == deliberately_quiet


# ---------- obs: alarm hattı ----------
def test_alarm_line_contains_the_raw_token(sandbox_state, capsys):
    obs.alarm(obs.ALARM_DATA_QUALITY, "sbux barı küçüldü")
    out = capsys.readouterr().out
    assert "DATA_QUALITY" in out                       # monitoring.sh düz altdizge arıyor
    ev = store.read_jsonl("events.jsonl")[-1]
    assert ev["level"] == "alarm" and ev["alarm"] == "DATA_QUALITY"


def test_notify_is_rate_limited_per_token(sandbox_state, monkeypatch):
    calls = []
    monkeypatch.setattr(notify, "configured", lambda: True)
    monkeypatch.setattr(notify, "send", lambda t: calls.append(t) or True)
    obs.alarm(obs.ALARM_CIRCUIT_BREAKER, "ilk")
    obs.alarm(obs.ALARM_CIRCUIT_BREAKER, "ikinci")
    assert len(calls) == 1, "aynı token 6 saatlik pencerede bir kez bildirilmeli"


def test_notify_failure_never_drops_the_alarm(sandbox_state, monkeypatch):
    monkeypatch.setattr(notify, "configured", lambda: True)
    monkeypatch.setattr(notify, "send", lambda t: (_ for _ in ()).throw(RuntimeError("boom")))
    obs.alarm(obs.ALARM_HALT, "durduruldu")
    assert store.read_jsonl("events.jsonl")[-1]["alarm"] == "HALT_ACTIVE"   # kayıt yine düştü


def test_unserializable_fields_do_not_break_logging(sandbox_state):
    class X:
        pass
    rec = obs.log("garip", obj=X())
    assert isinstance(rec, dict)

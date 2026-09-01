"""test_metrics_vekil_v365.py — /metrics YEREL-İSTEK AYRICALIĞI VEKİL ARKASINDA (2026-09-01).

VAKA: kapı (APISIX, TSK-089 Faz 3) panoya 127.0.0.1'den proxy'ler. `_local_request` yalnız
TCP eşine bakıyordu — ssh-tünel döneminin varsayımı. Kapı arkasında HER dış istek "yerel"
görünür ve /metrics tam seti (öz sermaye, günlük P&L, pozisyon sayısı) kimliksiz internete
dökerdi. Belge kapısındaki basic-auth kaldırılırken (operatör kararı 2026-09-01: tek kimlik
katmanı = uygulamanın kendi oturumu) bu ayrıcalık deliği kapanmak ZORUNDA.

SÖZLEŞME: X-Forwarded-For başlığı taşıyan istek VEKİLLİDİR → yerel sayılmaz. Başlık istemci
tarafından uydurulabilir ama uydurmanın tek etkisi yetkiyi DÜŞÜRMEKTİR (tam set → canlılık);
yükseltme yönü yoktur. Doğrudan yerel scrape (A1-içi, XFF'siz) tam seti korur.
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from starlette.requests import Request

from meridian import api


def _req(client_host: str, headers: dict[str, str] | None = None) -> Request:
    """Verilen TCP eşi ve başlıklarla asgari bir Starlette Request kurar."""
    scope = {
        "type": "http", "method": "GET", "path": "/metrics", "query_string": b"",
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
        "client": (client_host, 1234),
    }
    return Request(scope)


def test_dogrudan_yerel_istek_yerel_sayilir():
    # A1-içi scrape: TCP eşi loopback, vekil başlığı yok → tam set korunur.
    assert api._local_request(_req("127.0.0.1")) is True


def test_vekil_baslikli_istek_yerel_SAYILMAZ():
    # Kapı arkasındaki dış istek: TCP eşi loopback AMA X-Forwarded-For taşır → yerel değil.
    # Bu satır kırmızıyken /metrics hesap bilgilerini kimliksiz internete döker.
    assert api._local_request(_req("127.0.0.1", {"X-Forwarded-For": "203.0.113.7"})) is False


def test_uzak_istek_yerel_sayilmaz():
    assert api._local_request(_req("198.51.100.9")) is False


def test_metrics_vekilli_kimliksiz_yalniz_canlilik(sandbox_state):
    # Uçtan uca: XFF'li + oturumsuz /metrics canlılık üçlüsünü verir, hesap ölçütlerini VERMEZ.
    # Parola KURULUR — canlı duruş budur; parolasız sandbox `_auth`'un belgeli no-op dalına
    # düşer ve bu test yanlışlıkla tam seti görürdü (ölçüldü: ilk koşum).
    from meridian import auth
    auth.set_password("v365-test-parolasi")
    client = TestClient(api.app)
    r = client.get("/metrics", headers={"X-Forwarded-For": "203.0.113.7"})
    assert r.status_code == 200
    assert "meridian_up" in r.text and "meridian_halted" in r.text
    assert "meridian_equity_usd" not in r.text
    assert "meridian_day_pnl_pct" not in r.text

"""test_api_audit_v21.py — api denetimi (2026-07-21, tur 6).

7. soru:
  P1 "her mutasyon ucu yetki ister"  → BUGÜN doğru (19/19) ama hiçbir şey bunu ZORLAMIYORDU;
     yarın eklenecek bir POST sessizce açık kapı olurdu → statik kural testi
  P2 "/metrics zararsız canlılık"    → öz sermaye, günlük P&L, açık pozisyon, LLM harcaması
     YETKİSİZ yayınlanıyordu; /halt sayfası bilinçli olarak TÜNELDEN açılıyor, tünel tüm
     uygulamayı dışarı verir → uzak+yetkisiz istekte hesap ölçütleri gizlenir
  P3 "teşhis paketi anahtar sızdırmaz" → kilitle (regresyon koruması)
"""
from __future__ import annotations

import re
import pathlib

import pytest
from fastapi.testclient import TestClient

from meridian import api

SRC = pathlib.Path("meridian/api.py").read_text()


def _routes():
    out = []
    for b in re.split(r"\n(?=@app\.)", SRC):
        m = re.match(r'@app\.(get|post|delete|put)\("([^"]+)"', b)
        if not m:
            continue
        fn = re.search(r"\ndef (\w+)\(", b)
        out.append({"verb": m.group(1).upper(), "path": m.group(2),
                    "fn": fn.group(1) if fn else "?", "authed": "_auth(request)" in b})
    return out


# ---------- P1: yetki sınırı kalıcı kural ----------
def test_p1_every_mutating_route_requires_auth():
    """Bu test 'bugün doğru'yu 'yarın da doğru'ya çevirir: yetkisiz bir POST/DELETE eklenirse kırılır.

    KİMLİK UÇLARI HARİÇ (2026-07-29): `/api/login` ve `/api/setup-password` mutasyon yapar ama
    `_auth` ÇAĞIRAMAZ — oturumu veren ve ilk parolayı kuran uçlardır, kimlik doğrulamasının
    ardında duramazlar. İstisna listesi elle DEĞİL, üretim kodundan (`api.KIMLIK_UCLARI`)
    okunur: aynı yasanın iki kopyası zamanla ayrışır."""
    bad = [f"{r['verb']} {r['path']} ({r['fn']})" for r in _routes()
           if r["verb"] in ("POST", "DELETE", "PUT") and not r["authed"]
           and r["path"] not in api.KIMLIK_UCLARI]
    assert not bad, f"YETKİSİZ mutasyon ucu: {bad}"


def test_p1b_mutating_routes_actually_exist():
    n = sum(1 for r in _routes() if r["verb"] in ("POST", "DELETE", "PUT"))
    assert n >= 15, "rota sayımı bozuldu — test artık hiçbir şeyi korumuyor olabilir"


def test_p1c_public_get_allowlist():
    """Yetkisiz GET'ler BİLİNÇLİ bir listeyle sınırlı; yenisi eklenirse burada tartışılır."""
    # /api/public/summary (2026-07-27, operatör onayı): tanıtım sayfasının CANLI veri ucu —
    # BİLEREK doğrulamasız (sayfa herkese açık; DASH_TOKEN konunca kırılmamalı) ve BİLEREK dar
    # (sermaye/pozisyon/hisse/anahtar dışarı verilmez — api.py'deki docstring sözleşmesi).
    # Uydurma landing rakamlarının yerine geçen uç budur; dışa açılırsa kapsam yeniden tartışılır.
    # KİMLİK UÇLARI (2026-07-29): `/api/session` yetkisizdir çünkü panonun "giriş ekranı mı,
    # uygulama mı" sorusunu yanıtlar — yetki isteseydi giriş ekranı hiç çizilemezdi. Gerekçe ve
    # dönen alanların sınırı `api.KIMLIK_UCLARI` yanında; buradan OKUNUR, kopyalanmaz.
    # STATİK BETİKLER (2026-08-01): /theme.js, /landing.js, /workflow.js — `/app.js` ile aynı
    # sınıf. Bunlar HTML'lerin İÇİNDEN çıkarıldı, yeni içerik yayına açılmadı: aynı kod daha önce
    # aynı sayfalarda satır içi duruyordu ve o sayfalar (`/landing`, `/workflow`) zaten bu listede.
    # Yani maruziyet BİREBİR aynı; değişen tek şey kodun hangi dosyada olduğu.
    # Çıkarma sebebi güvenlik: dağıtım CSP'si `script-src 'self'` satır içi bloğu bloklar, o hâlde
    # bırakılsalardı iki sayfa canlıda ölü açılırdı. Hiçbiri veri UCU değildir, hiçbiri state
    # okumaz — FileResponse ile diskten sabit dosya döner.
    allow = {"/", "/app.js", "/theme.js", "/landing.js", "/workflow.js",
             "/landing", "/workflow", "/healthz", "/metrics", "/halt",
             "/api/public/summary"} | set(api.KIMLIK_UCLARI)
    public = {r["path"] for r in _routes() if r["verb"] == "GET" and not r["authed"]}
    assert public <= allow, f"beklenmedik yetkisiz GET: {public - allow}"


# ---------- P2: /metrics gizlilik sınırı ----------
@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api, "DASH_TOKEN", "T0KEN")
    return TestClient(api.app)


def test_p2_remote_unauthed_metrics_hides_account(client, monkeypatch):
    monkeypatch.setattr(api, "_local_request", lambda r: False)
    body = client.get("/metrics").text
    assert "meridian_up" in body and "meridian_halted" in body      # canlılık AÇIK kalır
    for leak in ("meridian_equity_usd", "meridian_day_pnl_pct", "meridian_open_positions",
                 "meridian_hermes_spend_usd"):
        assert leak not in body, f"{leak} uzak+yetkisiz isteğe sızdı"


def test_p2b_remote_with_token_gets_full_metrics(client, monkeypatch):
    monkeypatch.setattr(api, "_local_request", lambda r: False)
    body = client.get("/metrics", headers={"x-meridian-token": "T0KEN"}).text
    assert "meridian_equity_usd" in body and "meridian_score" in body


def test_p2c_local_scraper_unchanged(client, monkeypatch):
    monkeypatch.setattr(api, "_local_request", lambda r: True)
    body = client.get("/metrics").text
    assert "meridian_equity_usd" in body                             # yerel Prometheus bozulmaz


# ---------- P3: teşhis paketi anahtar taşımaz ----------
def test_p3_debug_export_excludes_secrets():
    blk = next(b for b in re.split(r"\n(?=@app\.)", SRC) if '"/api/debug_export"' in b)
    assert 'skip = {"secrets.json"}' in blk and "secrets.json" in blk


def test_p3b_no_route_returns_a_raw_secret_value():
    """secrets uçları yalnız DURUM döndürmeli (var/yok, son 4 hane) — değer asla."""
    blocks = [b for b in re.split(r"\n(?=@app\.)", SRC) if "/api/secrets" in b]
    assert blocks
    for b in blocks:
        assert "secrets_mod.get(" not in b, "ham anahtar değeri bir uçtan dönüyor olabilir"

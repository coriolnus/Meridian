"""test_authority_boundaries_v77.py — YETKİ SINIRLARI denetimi (2026-07-22).

Diğer denetim izleri DOĞRULUĞU ölçüyor. Bu dosya YETKİYİ ölçer: operatörün gerçek parasını ve
kimlik bilgilerini koruyan sınırların, bugünkü çağıranların tesadüfen o yola girmemesiyle değil,
SINIRIN KENDİSİYLE tutup tutmadığını. Bir doğruluk hatası parayı yavaş kaybettirir; bir sınır
ihlali hepsini bir anda.

YÖNTEM — her sözleşme için SALDIRI kurulur, sonra sınırın reddi doğrulanır. Sabitin bugünkü
değerini iddia eden bir test hiçbir şey kanıtlamaz; bu yüzden her sözleşmenin yanında bir
POZİTİF KONTROL var: sınır bilerek delinir ve iddianın GERÇEKTEN düştüğü gösterilir. Düşmeyen
bir iddia, koruma değil dekordur.

Taşıma (httpx / websocket / subprocess) HER testte saplanır: bu dosya hiçbir emir göndermez,
hiçbir emri iptal etmez, canlı state'e yazmaz ve hiçbir sır DEĞERİNİ basmaz/yazmaz.
"""
from __future__ import annotations

import ast
import json
import os
import pathlib
import re

import pytest

from meridian import config, guard, secrets as secrets_mod, store
from meridian.adapters import alpaca

MERIDIAN_DIR = pathlib.Path(config.__file__).resolve().parent
REPO = MERIDIAN_DIR.parent

# Kurgusal (sahte) sır değerleri — gerçek anahtar HİÇBİR testte okunmaz. Sandbox'ta
# state/secrets.json yoktur, env bu değerlerle ezilir, yani `secrets.get` yalnız bunları görür.
FAKE_KEY = "PKAUDITFAKEKEY7788990011"
FAKE_SECRET = "SKAUDITFAKESECRET2233445566778899"


# ---------------------------------------------------------------------------------------------
# ortak yardımcılar
# ---------------------------------------------------------------------------------------------
def _py_sources():
    """meridian/ altındaki her üretim modülü: (göreli yol, kaynak, AST)."""
    for p in sorted(MERIDIAN_DIR.rglob("*.py")):
        src = p.read_text(errors="ignore")
        yield p.relative_to(REPO), src, ast.parse(src, filename=str(p))


class FakeResponse:
    def __init__(self, status_code=200, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.headers = headers or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class HttpRecorder:
    """alpaca.httpx yerine geçer. HİÇBİR ağ çağrısı yapmaz; yalnız URL/başlık kaydeder.
    `boom` verilirse çağrı, URL'i İÇEREN bir istisna fırlatır (klasik sır-sızıntısı vektörü)."""

    def __init__(self, response=None, boom=False):
        self.calls: list[tuple[str, str, dict]] = []
        self.response = response
        self.boom = boom

    def _default_for(self, url):
        # Uç noktaya göre DOĞRU şekil: /orders ve /positions liste döner (çağıran üzerinde döner).
        if url.rstrip("/").endswith(("/orders", "/positions")):
            return FakeResponse(200, [])
        return FakeResponse(200, {"equity": "100000", "id": "x", "tradable": True, "status": "active"})

    def _call(self, verb, url, **kw):
        self.calls.append((verb, url, kw))
        if self.boom:
            # httpx'in gerçek hata metinleri TAM URL'i taşır — başlıkları değil. En kötü hâli
            # taklit et: URL + sorgu dizesi hata metnine gömülü.
            raise RuntimeError(f"ConnectError: request to {url} failed")
        return self.response if self.response is not None else self._default_for(url)

    def urls(self):
        return [u for _v, u, _k in self.calls]

    def get(self, url, **kw):
        return self._call("GET", url, **kw)

    def post(self, url, **kw):
        return self._call("POST", url, **kw)

    def patch(self, url, **kw):
        return self._call("PATCH", url, **kw)

    def delete(self, url, **kw):
        return self._call("DELETE", url, **kw)


@pytest.fixture
def paper_secrets(sandbox_state, monkeypatch):
    """Sahte kimlik bilgileri env üzerinden (env, dosya ve GCP'yi yener → gerçek anahtar okunmaz)."""
    monkeypatch.setenv("ALPACA_PAPER_KEY", FAKE_KEY)
    monkeypatch.setenv("ALPACA_PAPER_SECRET", FAKE_SECRET)
    monkeypatch.delenv("MERIDIAN_GCP_PROJECT", raising=False)
    secrets_mod.clear_cache()
    yield
    secrets_mod.clear_cache()


def _set_endpoint(monkeypatch, value):
    monkeypatch.setenv("ALPACA_PAPER_ENDPOINT", value)
    secrets_mod.clear_cache()


# Uç nokta operatör/pano/env üzerinden AYARLANABİLİR bir değerdir (secrets.ALLOWED içinde) —
# yani saldırganın kontrol edebildiği tek taşıma girdisi. Külliyat: her biri eski `in` testini
# geçip anahtar başlıklarını YABANCI bir hosta gönderirdi.
HOSTILE_ENDPOINTS = [
    "https://api.alpaca.markets",                                   # düpedüz gerçek-para ucu
    "https://paper-api.alpaca.markets.evil.example.com",            # sonek benzeşimi
    "https://evil.example.com/paper-api.alpaca.markets",            # yol içinde benzeşim
    "https://paper-api.alpaca.markets@evil.example.com/v2",         # userinfo hilesi
    "https://evil.example.com#paper-api.alpaca.markets",            # fragment hilesi
    "https://evil.example.com?x=paper-api.alpaca.markets",          # sorgu hilesi
    "http://paper-api.alpaca.markets",                              # doğru host, AÇIK METİN taşıma
    "paper-api.alpaca.markets.evil.example.com",                    # şemasız + benzeşim
    "https://PAPER-API.ALPACA.MARKETS.evil.example.com",            # büyük harf benzeşimi
    "ftp://paper-api.alpaca.markets",                               # yabancı şema
    "https://api.alpaca.markets/v2",                                # /v2 kırpma yolundan geçen
    "  https://api.alpaca.markets/  ",                              # boşluk/eğik çizgi gürültüsü
]

LOCKED_HOST = "paper-api.alpaca.markets"


def _host_of(url: str) -> str:
    from urllib.parse import urlparse
    return urlparse(url).hostname or ""


# =============================================================================================
# SÖZLEŞME 1 — KAĞIT KİLİDİ: hiçbir yol gerçek-para ucuna emir gönderemez
# =============================================================================================
def test_c1_paper_base_survives_every_endpoint_attack(paper_secrets, monkeypatch):
    """`_paper_base()` operatör/env'in verdiği HER düşmanca uç noktada kilitli hosta düşmeli."""
    for hostile in HOSTILE_ENDPOINTS:
        _set_endpoint(monkeypatch, hostile)
        base = alpaca._paper_base()
        assert _host_of(base) == LOCKED_HOST, f"host kilidi delindi: {hostile!r} → {base!r}"
        assert base.startswith("https://"), f"taşıma sıkılaştırması delindi: {hostile!r} → {base!r}"


def test_c1_attack_corpus_actually_has_teeth_positive_control():
    """POZİTİF KONTROL: külliyat, kilidin ESKİ (substring) hâlini gerçekten deliyor mu?
    Delmiyorsa yukarıdaki test 'geçti' der ama hiçbir şey ölçmemiş olur."""
    def vulnerable(base: str) -> str:                     # denetim #51 öncesi mantık
        return base if LOCKED_HOST in base else alpaca.PAPER_BASE

    delen = [h for h in HOSTILE_ENDPOINTS if _host_of(vulnerable(h.strip())) not in ("", LOCKED_HOST)]
    assert len(delen) >= 4, f"külliyat zayıf — eski kilidi yalnız {delen} deliyor"


def test_c1_every_rest_call_lands_on_the_locked_host(paper_secrets, monkeypatch):
    """Kilit yalnız `_paper_base()`te değil, MODÜLÜN HER çağrısında tutmalı: adaptörün ağa çıkan
    her fonksiyonu düşmanca uç noktayla sürülür ve giden URL'lerin hepsi kilitli hostta olmalı."""
    _set_endpoint(monkeypatch, "https://api.alpaca.markets")
    rec = HttpRecorder()
    monkeypatch.setattr(alpaca, "httpx", rec)

    alpaca.account()
    alpaca.positions()
    alpaca.orders(status="open", limit=5, nested=True)
    alpaca.asset_tradable("AAPL")
    alpaca.cancel_order("ORDER-ID")
    alpaca.replace_order_stop("ORDER-ID", 11.0, cur_stop=10.0)
    alpaca.submit_bracket("AAPL", 1, 10.0, 12.0, 9.0, client_order_id="P-2026-01-01-AAAA")
    alpaca.close_all()                                    # jetonsuz → yalnız kuru koşu

    assert rec.calls, "hiç çağrı kaydedilmedi — test bir şey ölçmüyor"
    for verb, url, _kw in rec.calls:
        assert _host_of(url) == LOCKED_HOST, f"{verb} {url} kilitli hostun dışına çıktı"
        assert url.startswith("https://"), f"{verb} {url} açık metin taşıma"


def test_c1_no_module_writes_orders_to_any_other_base(paper_secrets, monkeypatch):
    """Kilit ATLANABİLİR mi: emir yüzeyi `_paper_base()` dışında bir taban kullanan bir çağrı
    barındırıyor mu? Kaynak taraması DEĞİL — `_paper_base` bilerek sabote edilir ve emir yolunun
    ona GERÇEKTEN bağlı olduğu davranışsal olarak kanıtlanır."""
    sentinel = "https://sentinel.invalid"
    monkeypatch.setattr(alpaca, "_paper_base", lambda: sentinel)
    rec = HttpRecorder(FakeResponse(200, {}))
    monkeypatch.setattr(alpaca, "httpx", rec)
    alpaca.submit_bracket("AAPL", 1, 10.0, 12.0, 9.0, client_order_id="P-x")
    alpaca.cancel_order("id")
    alpaca.replace_order_stop("id", 11.0)
    assert rec.calls, "emir yüzeyi hiç çağrı yapmadı"
    for _verb, url, _kw in rec.calls:
        assert url.startswith(sentinel), (
            f"{url} `_paper_base()`e bağlı DEĞİL — kilit bu yolu kapsamıyor")


def test_c1_redirect_is_never_followed(paper_secrets, monkeypatch):
    """302 → gerçek-para hostu. httpx varsayılanı takip ETMEZ ve hiçbir çağrı yeri
    `follow_redirects=True` geçmez; ayrıca yönlendirme cevabı ikinci bir istek doğurmaz."""
    _set_endpoint(monkeypatch, alpaca.PAPER_BASE)
    redirect = FakeResponse(302, {}, headers={"location": "https://api.alpaca.markets/v2/account"})
    rec = HttpRecorder(redirect)
    monkeypatch.setattr(alpaca, "httpx", rec)
    alpaca.account()
    alpaca.positions()
    assert len(rec.calls) == 2, "yönlendirme ikinci bir istek doğurdu (takip ediliyor)"
    for _v, _u, kw in rec.calls:
        assert kw.get("follow_redirects") in (None, False), "follow_redirects açık — yönlendirme takibi"
    src = (MERIDIAN_DIR / "adapters" / "alpaca.py").read_text()
    assert "follow_redirects" not in src, "adaptörde follow_redirects geçiyor — elle incele"


def test_c1_mirror_stream_url_inherits_the_lock(paper_secrets, monkeypatch):
    """Ayna WebSocket'i ayrı bir taşımadır; kilidi kendi başına uydurmamalı, `_paper_base()`ten
    devralmalı. Aksi hâlde REST kağıtta kalırken akış başka bir makineye kimlik gönderirdi."""
    from meridian.mirror_stream import MirrorStreamListener
    for hostile in HOSTILE_ENDPOINTS:
        _set_endpoint(monkeypatch, hostile)
        url = MirrorStreamListener._url()
        assert url.startswith("wss://"), f"{hostile!r} → {url!r} şifresiz akış"
        assert _host_of(url.replace("wss://", "https://", 1)) == LOCKED_HOST, f"{hostile!r} → {url!r}"


# =============================================================================================
# SÖZLEŞME 2 — ÖZERKLİK KAPILARI: hiçbir kod yolu bayrağı kendisi açamaz
# =============================================================================================
GATE_NAMES = ("MERIDIAN_MODE", "MERIDIAN_I_ACCEPT_RISK", "autonomy_level")


def test_c2_no_production_module_sets_a_gate_flag():
    """AST: hiçbir üretim modülü gerçek-para kapılarını YAZMAZ — ne `os.environ[...] = `,
    ne `setenv/putenv`, ne `config.MODE = `, ne bir `autonomy_level` ataması."""
    ihlal = []
    for rel, _src, tree in _py_sources():
        for node in ast.walk(tree):
            # os.environ["MERIDIAN_MODE"] = ... / os.environ.setdefault(...) / putenv
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant) \
                            and str(t.slice.value) in GATE_NAMES:
                        ihlal.append(f"{rel}:{node.lineno} environ[{t.slice.value}] ataması")
                    if isinstance(t, ast.Attribute) and t.attr in ("MODE", "I_ACCEPT_RISK") \
                            and isinstance(t.value, ast.Name) and t.value.id == "config":
                        ihlal.append(f"{rel}:{node.lineno} config.{t.attr} ataması")
                    if isinstance(t, ast.Attribute) and t.attr == "autonomy_level":
                        ihlal.append(f"{rel}:{node.lineno} autonomy_level ataması")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and node.func.attr in ("setdefault", "putenv", "setenv", "__setitem__"):
                for a in node.args:
                    if isinstance(a, ast.Constant) and str(a.value) in GATE_NAMES:
                        ihlal.append(f"{rel}:{node.lineno} {node.func.attr}({a.value!r})")
    assert not ihlal, f"özerklik kapısı ÜRETİM kodundan yazılıyor: {ihlal}"


def test_c2_ast_scan_would_catch_a_real_breach_positive_control(tmp_path):
    """POZİTİF KONTROL: tarayıcı gerçekten yakalıyor mu? Bilerek ihlalli bir modül üret ve
    aynı kuralların onu düşürdüğünü göster."""
    kotu = "import os\nos.environ['MERIDIAN_MODE'] = 'live'\n"
    tree = ast.parse(kotu)
    yakalandi = any(
        isinstance(n, ast.Assign) and any(
            isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant)
            and str(t.slice.value) in GATE_NAMES for t in n.targets)
        for n in ast.walk(tree))
    assert yakalandi, "tarayıcı bariz bir ihlali kaçırıyor — yukarıdaki yeşil hiçbir şey kanıtlamaz"


def test_c2_secret_whitelist_cannot_plant_a_gate():
    """Panodan yazılabilir tek yüzey `secrets.set` — izin listesi hiçbir kapı adını taşımamalı."""
    for name in GATE_NAMES + ("PATH", "MERIDIAN_ROOT", "MERIDIAN_BROKER", "MERIDIAN_DASH_TOKEN"):
        assert name not in secrets_mod.ALLOWED, f"{name} panodan yazılabilir!"
        with pytest.raises(ValueError):
            secrets_mod.set(name, "live")
        with pytest.raises(ValueError):
            secrets_mod.delete(name)


def test_c2_live_guard_refuses_at_l0_and_fires_when_breached(monkeypatch):
    """L0'da canlı istemci ASLA kurulmaz. Üç kapının her ALT KÜMESİ reddedilir; yalnız üçü birden
    açıkken geçer (pozitif kontrol — testin bir ihlali görebildiğinin kanıtı)."""
    olusturuldu = []
    monkeypatch.setattr(alpaca, "_client", lambda paper: olusturuldu.append(paper))

    for mode, risk, lvl in [("paper", False, 0), ("live", False, 0), ("paper", True, 0),
                            ("live", True, 0), ("live", False, 2), ("paper", True, 2)]:
        monkeypatch.setattr(config, "MODE", mode)
        monkeypatch.setattr(config, "I_ACCEPT_RISK", risk)
        monkeypatch.setattr(config, "limits", lambda lvl=lvl: {"autonomy_level": lvl})
        with pytest.raises(RuntimeError):
            alpaca.live_client()
    assert olusturuldu == [], "L0'da canlı istemci KURULDU"

    monkeypatch.setattr(config, "MODE", "live")            # POZİTİF KONTROL: üçü birden açık
    monkeypatch.setattr(config, "I_ACCEPT_RISK", True)
    monkeypatch.setattr(config, "limits", lambda: {"autonomy_level": 1})
    alpaca.live_client()
    assert olusturuldu == [False], "kapılar açıkken bile geçmiyor — test ihlali göremezdi"


def test_c2_live_flags_are_off_right_now_and_only_env_can_change_them(monkeypatch):
    """Bugünkü gerçek durum L0 olmalı; ve `live_enabled()` YALNIZ elle set edilen env'e bağlı
    olmalı (bir dosya/sır/argüman onu açamaz)."""
    assert config.live_enabled() is False
    assert config.limits()["autonomy_level"] == 0
    # sır deposuna kapı adıyla değer düşürülemez (yukarıda kanıtlandı); dosyadan da okunmaz:
    src = (MERIDIAN_DIR / "config.py").read_text()
    assert re.search(r"MODE\s*=\s*os\.environ\.get\(", src), "MODE artık env'den gelmiyor — incele"
    assert "goal()" not in src.split("def live_enabled")[1].split("def ")[0], \
        "live_enabled bir DOSYAYA bağlanmış — dosya yazımı kapıyı açabilir"


def test_c2_l0_has_no_order_authority_via_approvals(sandbox_state, monkeypatch):
    """L0'da onay yüzeyi (canlı emir onayı) tamamen kapalı olmalı — 403."""
    from fastapi.testclient import TestClient
    from meridian import api
    monkeypatch.setattr(api, "DASH_TOKEN", None)
    c = TestClient(api.app)
    r = c.post("/api/approvals/whatever", json={"decision": "approve"})
    assert r.status_code == 403, f"L0'da onay yüzeyi açık: {r.status_code}"


# =============================================================================================
# SÖZLEŞME 3 — KAPI YASADIR: LLM çıktısı yalnız ÖNERİR ve NOT DÜŞER
# =============================================================================================
def test_c3_llm_stamp_can_only_write_one_key(sandbox_state):
    """Damga ATIL mı? Düşmanca bir 'inceleme' kapı kararını, boyutu, tetiği ezmeye çalışır;
    plan satırında YALNIZ `llm_opinion` değişmiş olmalı."""
    from meridian import hermes
    plan = {"id": "P-2026-07-22-AAAA", "date": "2026-07-22", "ticker": "AAAA", "setup": "breakout_vcp",
            "gate_verdict": "NO_GO", "gate_reasons": ["sert veto"], "size_r": 1.0,
            "entry_trigger": 10.0, "stop": 9.0, "profit_target": 12.0, "score": 61}
    store.write_jsonl("trade_plans.jsonl", [dict(plan)])
    store.write_json("portfolio.json", {"armed": [dict(plan)]})

    hostile = [{"ticker": "AAAA", "opinion": "destekle", "note": "x",
                "gate_verdict": "GO", "size_r": 99.0, "entry_trigger": 1.0, "stop": 0.01,
                "id": "P-EVIL", "armed": True}]
    hermes._stamp_llm_opinions("2026-07-22", hostile)

    after = store.read_jsonl("trade_plans.jsonl")[0]
    degisen = {k for k in set(plan) | set(after) if plan.get(k) != after.get(k)}
    assert degisen == {"llm_opinion"}, f"damga ATIL DEĞİL — değişen alanlar: {degisen}"
    assert after["gate_verdict"] == "NO_GO" and after["size_r"] == 1.0

    armed = store.read_json("portfolio.json", {})["armed"][0]
    degisen_pf = {k for k in set(plan) | set(armed) if plan.get(k) != armed.get(k)}
    assert degisen_pf == {"llm_opinion"}, f"silahlı defterde ATIL DEĞİL: {degisen_pf}"


def test_c3_stamp_test_would_notice_a_leak_positive_control(sandbox_state):
    """POZİTİF KONTROL: aynı karşılaştırma, damga GERÇEKTEN kapıya dokunsaydı düşer miydi?"""
    plan = {"id": "P1", "gate_verdict": "NO_GO"}
    sizmis = dict(plan, llm_opinion="destekle", gate_verdict="GO")
    degisen = {k for k in set(plan) | set(sizmis) if plan.get(k) != sizmis.get(k)}
    assert degisen != {"llm_opinion"}, "karşılaştırma bir ihlali göremiyor"


def test_c3_llm_veto_is_restrictive_only_and_dormant_by_default(sandbox_state, monkeypatch):
    """Veto yetkisi (a) terfi edilmemişken UYUR, (b) terfi edilse bile YALNIZ 'REVIEW + karşı'yı
    DÜŞÜRÜR — hiçbir plan silahlanamaz, hiçbir alan (boyut/tetik/karar) değişemez."""
    from meridian import loop
    from meridian import analytics

    def mk(pid, verdict, opinion):
        return {"id": pid, "ticker": pid, "gate_verdict": verdict, "llm_opinion": opinion,
                "size_r": 1.0, "entry_trigger": 10.0, "stop": 9.0}

    armed = [mk("A", "GO", "karşı"), mk("B", "REVIEW", "karşı"),
             mk("C", "REVIEW", "destekle"), mk("D", "NO_GO", "destekle")]

    monkeypatch.setattr(analytics, "llm_promoted", lambda: False)      # (a) terfisiz
    meta = {"armed": [dict(p) for p in armed]}
    loop._llm_veto_filter(meta)
    assert [p["id"] for p in meta["armed"]] == ["A", "B", "C", "D"], "terfisiz veto ateşledi"

    monkeypatch.setattr(analytics, "llm_promoted", lambda: True)       # (b) terfili
    meta = {"armed": [dict(p) for p in armed], "alpaca_submitted": []}
    loop._llm_veto_filter(meta)
    kalan = [p["id"] for p in meta["armed"]]
    assert kalan == ["A", "C", "D"], f"veto kapsamı kaydı: {kalan}"
    assert set(kalan) <= {p["id"] for p in armed}, "veto YENİ plan silahlandırdı"
    for p in meta["armed"]:
        orig = next(o for o in armed if o["id"] == p["id"])
        assert {k: p[k] for k in orig} == orig, f"{p['id']} alanları veto yolunda değişti"


def test_c3_veto_authority_is_granted_by_a_plain_state_file(sandbox_state, monkeypatch):
    """ZİNCİRİ GÖRÜNÜR KIL: veto yetkisi `state/llm_calibration.json` içindeki tek bir boole'den
    doğar. Kalibrasyon bunu ÖLÇÜMDEN türetir (doğru tasarım) ama dosyayı YAZABİLEN herhangi biri
    yetkiyi kendine verebilir. Bu test o zinciri kanıtlar; sınırın kendisi bir sonraki testte."""
    from meridian import analytics, loop
    assert analytics.llm_promoted() is False, "temiz sandbox'ta terfi AÇIK geldi"
    store.write_json(analytics.LLM_CAL_FILE, {"promoted": True, "n_pairs": 0, "buckets": {}})
    assert analytics.llm_promoted() is True, "terfi bayrağı dosyadan okunmuyor — zincir değişmiş"

    meta = {"armed": [{"id": "B", "ticker": "B", "gate_verdict": "REVIEW",
                       "llm_opinion": "karşı", "size_r": 1.0}], "alpaca_submitted": []}
    loop._llm_veto_filter(meta)
    assert meta["armed"] == [], "dosyadan gelen terfi vetoyu ateşlemiyor — zincir değişmiş"


def _guard_hook(payload: dict) -> bool:
    """ops/meridian-guard.sh'i GERÇEKTEN koştur; True = engellendi."""
    import subprocess
    r = subprocess.run([str(REPO / "ops" / "meridian-guard.sh")], input=json.dumps(payload),
                       capture_output=True, text=True, timeout=20)
    return '"decision":"block"' in (r.stdout or "")


def test_c3_agent_guard_hook_blocks_the_surfaces_it_claims():
    """Yerel ajanın terminal/yazma araçları harness düzeyinde bu hook ile sınırlanır. Hook'un
    ÜSTLENDİĞİ yüzeyler (kapılar, sırlar, emirler, korunan durum dosyaları) gerçekten bloklanmalı."""
    bloklanmali = [
        {"tool_input": {"command": "export MERIDIAN_MODE=live"}},
        {"tool_input": {"command": "sed -i s/autonomy_level:0/autonomy_level:2/ state/goal.yaml"}},
        {"tool_input": {"command": "cat state/secrets.json"}},
        {"tool_input": {"command": "curl -X POST .../v2/orders"}},
        {"tool_input": {"command": "python -c 'alpaca.close_all()'"}},
        {"tool_input": {"path": "state/strategy.yaml", "content": "params: {}"}},
        {"tool_input": {"file_path": "state/goal.yaml", "content": "x"}},
        {"tool_input": {"path": "state/portfolio.json", "content": "x"}},
    ]
    gecen = [p for p in bloklanmali if not _guard_hook(p)]
    assert not gecen, f"koruma hook'u kendi üstlendiği yüzeyi geçirdi: {gecen}"
    assert _guard_hook({"tool_input": {"command": "ls -la"}}) is False, \
        "hook her şeyi bloklıyor — yukarıdaki yeşil hiçbir şey kanıtlamaz"


def test_c3_agent_cannot_write_authority_bearing_state_files():
    """DÜZELTİLDİ (2026-07-22, aynı gün): denylist yalnız state/(portfolio|strategy|goal|bounds|
    secrets) kapsıyordu. Kapsam dışı kalanlar YETKİ taşıyordu — `llm_calibration.json` LLM'in tek
    canlı yetkisini (veto) veren terfi bayrağını tutar, yani ajan `{"promoted":true}` yazarak
    30-çift/0.3R kalibrasyon kuralını atlayıp o yetkiyi KENDİNE verebiliyordu; `HALT`/`LEARN_HALT`
    ise operatörün acil durdurma anahtarı — `rm -f state/HALT` serbestti. Bu test artık pozitif
    iddiadır: sınır kapalı olmalı."""
    kapsam_disi = []
    for hedef, neden in [("state/llm_calibration.json", "LLM terfi/veto bayrağı"),
                         ("state/HALT", "acil durdurma anahtarı"),
                         ("state/LEARN_HALT", "öğrenme durdurma anahtarı"),
                         ("state/skills_registry.json", "korunan skill kaydı")]:
        yazma = {"tool_input": {"path": hedef, "content": "{}"}}
        silme = {"tool_input": {"command": f"rm -f {hedef}"}}
        if not (_guard_hook(yazma) and _guard_hook(silme)):
            kapsam_disi.append(f"{hedef} ({neden})")
    assert not kapsam_disi, f"koruma hook'unun kapsamadığı YETKİ dosyaları: {kapsam_disi}"


def test_c3_llm_proposal_cannot_reach_the_ship_path(sandbox_state, monkeypatch):
    """Düşmanca bir Hermes önerisi kapı YASASINA çarpmalı — ve reddedilme, pahalı backtest'ten
    ÖNCE gerçekleşmeli (yani gerçekten guard reddediyor, gate değil)."""
    from meridian import reflect, versioning, memory

    monkeypatch.setattr(reflect.dataset, "load",
                        lambda *a, **k: pytest.fail("guard reddetmeden backtest'e geçildi"))
    monkeypatch.setattr(versioning, "commit",
                        lambda *a, **k: pytest.fail("düşmanca öneri SHIP edildi"))
    monkeypatch.setattr(memory, "distill_lessons", lambda *a, **k: None)

    hostile = [
        {"variable": "autonomy_level", "new": 2},
        {"variable": "limits.max_position_r", "new": 99},
        {"variable": "max_daily_loss_pct", "new": 99},
        {"variable": "kill_switch_file", "new": 0},
        {"variable": "goal", "new": 1},
        {"variable": "bounds", "new": 1},
        {"variable": "commission_per_share", "new": 0.0},
        {"variable": "../../state/goal.yaml", "new": 1},
        {"changes": {"autonomy_level": 2}},
        {"changes": {"entry.min_score": 60, "autonomy_level": 2}},   # tek-değişken yasası
        {"variable": "autonomy_level@trend_up", "new": 2},
        {"variable": "entry.min_score", "new": 10_000},              # aralık dışı
        {"variable": "entry.min_score", "new": 61.3},                # adım dışı
        {"variable": "olmayan_dugme", "new": 1},
    ]
    for proposal in hostile:
        res = reflect.submit({**proposal, "source": "hermes"})
        assert res["status"] in ("rejected_by_guard", "learning_halted", "locked"), \
            f"{proposal} → {res['status']} (kapı yasası delindi)"


def test_c3_guard_rejection_list_is_derived_not_duplicated():
    """Değişmez ad listeleri goal.yaml'ın GERÇEK anahtarlarını kapsıyor mu? Kapsamıyorsa yeni bir
    limit eklendiğinde sessizce ÖNERİLEBİLİR hâle gelir (kayma sınıfı)."""
    goal = config.goal()
    # 25c damgası (2026-08-23): REPLAY_WARMUP_KEYS de korumalı bir kümedir (Hermes'e kapalı) —
    # `no_trade_before_bars` oraya taşındı, kapı daralmadı.
    eksik_limit = set(goal.get("limits", {})) - guard.LIMIT_KEYS - guard.REPLAY_WARMUP_KEYS
    assert not eksik_limit, f"goal.limits içinde guard'ın korumadığı anahtar: {eksik_limit}"
    # 25a mezar taşı (2026-08-23): `backtest_gate` bu listeden ve goal.yaml'dan düştü — kapı sözü
    # verip hiçbir davranış taşımayan ÖLÜ anahtardı (envanter §D-1; çivi test_k5_paketi_v273).
    kritik = {"target_return_30d", "max_drawdown", "min_sample"}
    assert kritik <= guard.GOAL_KEYS, f"GOAL_KEYS eksik: {kritik - guard.GOAL_KEYS}"


def test_c3_protected_skills_cannot_be_shadowed_or_rewritten(sandbox_state):
    """Kısıtlama katmanı (kapı, devre kesici, boyutlandırıcı) ne gölgelenebilir ne içeriği ezilebilir —
    ve skill ADI dosya yoluna dönüştüğü için yol-kaçışı reddedilmeli."""
    from meridian import skills, skill_evolve
    store.write_json("skills_registry.json",
                     {"skills": {s: {"enabled": True} for s in skills.PROTECTED}})
    for s in sorted(skills.PROTECTED):
        assert skills.apply_skill_action(s, "shadow")["ok"] is False, f"{s} gölgelendi"
        assert skills.record_recommendation({"skill": s, "action": "shadow"}) is False
        assert skill_evolve.apply_revision(s)["ok"] is False, f"{s} içeriği revizyonla ezildi"

    for kotu in ("../../meridian", "../../../etc/passwd", "..", ".ssh", "a/../../b", "a b"):
        with pytest.raises(ValueError):
            skill_evolve._repo_skill_dir(kotu)
        assert skill_evolve.apply_revision(kotu)["ok"] is False
        assert skill_evolve.reject_revision(kotu)["ok"] is False


# =============================================================================================
# SÖZLEŞME 4 — DEĞİŞMEZ YAPILANDIRMA: goal.yaml / bounds.yaml
# =============================================================================================
def test_c4_no_agent_path_writes_goal_or_bounds(sandbox_state, monkeypatch):
    """Davranışsal: `dump_yaml` (tek YAML yazarı) bu iki dosyaya YÖNELİRSE test düşer. Ajanın
    dokunabildiği yollar (versiyon ship, snapshot, rollback, sır yazımı, skill eylemi) sürülür."""
    from meridian import versioning

    yasakli = {"goal.yaml", "bounds.yaml"}
    asil = config.dump_yaml

    def bekci(obj, path):
        assert pathlib.Path(path).name not in yasakli, f"DEĞİŞMEZ dosyaya yazıldı: {path}"
        return asil(obj, path)

    monkeypatch.setattr(config, "dump_yaml", bekci)
    monkeypatch.setattr(versioning, "config", config)

    before = {f: (config.STATE / f).read_bytes() for f in yasakli}
    child = versioning.bump(config.default_strategy(), "entry.min_score", 62, note="denetim")
    versioning.commit(child)
    versioning.snapshot(child)
    versioning.update_scoreboard(child["version"], live_score=0.1)
    versioning.revert_to(child["version"])
    secrets_mod.set("FMP_API_KEY", "AUDIT-FAKE-VALUE-0000")
    secrets_mod.delete("FMP_API_KEY")
    after = {f: (config.STATE / f).read_bytes() for f in yasakli}
    assert before == after, "goal/bounds baytları değişti"


def test_c4_guard_never_lets_a_goal_key_through():
    """Statik yüzey: goal/limits blokundaki HER anahtar reddedilmeli (öneri şekli ne olursa olsun)."""
    bounds, goal = config.bounds(), config.goal()
    params = config.default_strategy()["params"]
    for key in sorted(guard.GOAL_KEYS | guard.LIMIT_KEYS):
        for proposal in ({"variable": key, "new": 1}, {"changes": {key: 1}},
                         {"variable": f"limits.{key}", "new": 1}):
            v = guard.validate_change(proposal, params, bounds, goal, [], 0)
            assert v.ok is False, f"{proposal} guard'ı geçti"


def test_c4_watchdog_would_notice_a_write_positive_control(sandbox_state):
    """POZİTİF KONTROL: bayt karşılaştırması gerçekten bir yazımı görüyor mu?"""
    p = config.STATE / "goal.yaml"
    before = p.read_bytes()
    p.write_bytes(before + b"\n# denetim izi\n")
    assert p.read_bytes() != before, "bayt karşılaştırması bir yazımı göremiyor"
    p.write_bytes(before)


# =============================================================================================
# SÖZLEŞME 5 — close_all / DÜZLEŞTİRME: hiçbir otomatik yol çağıramaz
# =============================================================================================
def test_c5_close_all_without_the_token_sends_no_delete(paper_secrets, monkeypatch):
    """Jetonsuz / yanlış jetonlu çağrı SIFIR yazma yapmalı — yalnız neyi düzleştireceğini raporlar."""
    rec = HttpRecorder(FakeResponse(200, []))
    monkeypatch.setattr(alpaca, "httpx", rec)
    for token in ("", "flatten-paper", "FLATTEN_PAPER", "FLATTEN-PAPER ", None):
        rec.calls.clear()
        res = alpaca.close_all(confirm=token) if token is not None else alpaca.close_all()
        assert res["ok"] is False and res.get("dry_run") is True, f"jeton {token!r} kabul edildi"
        assert [v for v, _u, _k in rec.calls if v == "DELETE"] == [], f"jeton {token!r} DELETE gönderdi"


def test_c5_confirm_token_is_only_typed_by_the_operator():
    """Jeton hiçbir ÜRETİM modülünde (adaptörün kendisi hariç) geçmemeli — yani hiçbir döngü,
    zamanlayıcı, bekçi ya da ajan onu 'bilerek' üretemez. Panodaki tuş insan eylemidir."""
    tasiyan = []
    for rel, src, _tree in _py_sources():
        if rel.name == "alpaca.py":
            continue
        if alpaca.CLOSE_ALL_CONFIRM in src:
            tasiyan.append(str(rel))
    assert not tasiyan, f"onay jetonu üretim kodunda: {tasiyan}"

    cagiran = []
    for rel, _src, tree in _py_sources():
        if rel.name == "api.py":                       # operatör uç noktası — tek meşru çağıran
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and node.func.attr == "close_all":
                cagiran.append(f"{rel}:{node.lineno}")
    assert not cagiran, f"close_all otomatik bir yoldan çağrılıyor: {cagiran}"


def test_c5_disconnect_breaker_is_off_by_default_and_never_flattens(paper_secrets, monkeypatch):
    """Ayna kopuş devre-kesicisi: env AÇIKÇA '1' değilse hiç ateşlemez; ateşlese bile YALNIZ
    `cancel_open_entries` çağırır — düzleştirme/koruma-bacağı iptali yoktur."""
    from meridian import mirror_stream

    cagrilar = []
    monkeypatch.setattr(alpaca, "cancel_open_entries",
                        lambda: cagrilar.append("cancel") or {"cancelled": [], "kept": [], "foreign": []})
    monkeypatch.setattr(alpaca, "close_all",
                        lambda *a, **k: pytest.fail("devre kesici DÜZLEŞTİRME çağırdı"))
    lst = mirror_stream.MirrorStreamListener()

    for val in (None, "", "0", "true", "yes", "2", " 1"):
        monkeypatch.delenv("MERIDIAN_WS_DISCONNECT_CANCEL_ENTRIES", raising=False)
        if val is not None:
            monkeypatch.setenv("MERIDIAN_WS_DISCONNECT_CANCEL_ENTRIES", val)
        lst._maybe_cancel_entries()
        assert cagrilar == [], f"devre kesici {val!r} ile ateşledi (varsayılan KAPALI olmalı)"

    monkeypatch.setenv("MERIDIAN_WS_DISCONNECT_CANCEL_ENTRIES", "1")   # POZİTİF KONTROL
    lst._maybe_cancel_entries()
    assert cagrilar == ["cancel"], "açıkça açıldığında bile ateşlemiyor — test ihlali göremezdi"


def test_c5_cancel_open_entries_respects_ownership_and_protection(paper_secrets, monkeypatch):
    """Motor SAHİBİ OLMADIĞI emre dokunamaz; dolmuş/kısmen dolmuş parent'ın koruma bacakları
    KALIR (pozisyonu çıplak bırakmak yasak)."""
    orders = [
        {"id": "1", "symbol": "OWNED", "client_order_id": "P-2026-07-22-OWNED",
         "status": "new", "filled_qty": "0"},
        {"id": "2", "symbol": "FOREIGN", "client_order_id": "a1b2-uuid", "status": "new",
         "filled_qty": "0"},                                    # operatörün elle girdiği emir
        {"id": "3", "symbol": "NOCOID", "status": "new", "filled_qty": "0"},
        {"id": "4", "symbol": "PARTIAL", "client_order_id": "P-2026-07-22-PARTIAL",
         "status": "partially_filled", "filled_qty": "5"},      # koruma bacakları canlı
        {"id": "5", "symbol": "FILLED", "client_order_id": "P-2026-07-22-FILLED",
         "status": "filled", "filled_qty": "10"},
    ]
    iptal = []
    monkeypatch.setattr(alpaca, "orders", lambda **k: orders)
    monkeypatch.setattr(alpaca, "cancel_order", lambda oid: iptal.append(oid) or {"ok": True})
    res = alpaca.cancel_open_entries()
    assert iptal == ["1"], f"sahiplik/koruma sınırı delindi — iptal edilenler: {iptal}"
    assert {f["symbol"] for f in res["foreign"]} == {"FOREIGN", "NOCOID"}
    assert {k["symbol"] for k in res["kept"]} == {"PARTIAL", "FILLED"}


def test_c5_stop_protection_can_only_move_up(paper_secrets, monkeypatch):
    """Koruma GEVŞETİLEMEZ: sınırın kendisi aşağı çekilen stop'u reddetmeli (çağırana güvenilmez)."""
    rec = HttpRecorder(FakeResponse(200, {}))
    monkeypatch.setattr(alpaca, "httpx", rec)
    for new, cur in ((9.0, 10.0), (10.0, 10.0), (9.999, 10.0)):
        res = alpaca.replace_order_stop("id", new, cur_stop=cur)
        assert res["ok"] is False and "refused" in res["detail"], f"stop {cur}→{new} gevşetildi"
    assert rec.calls == [], "reddedilen gevşetme yine de ağa çıktı"
    alpaca.replace_order_stop("id", 10.5, cur_stop=10.0)                # POZİTİF KONTROL
    assert len(rec.calls) == 1, "yukarı hareket de engelleniyor — test bir şey ölçmüyor"


# =============================================================================================
# SÖZLEŞME 6 — SIR HİJYENİ: hiçbir kimlik bilgisi deftere/hataya/yanıta/panoya sızmaz
# =============================================================================================
def test_c6_no_alpaca_path_puts_a_credential_in_a_url_or_error(paper_secrets, monkeypatch):
    """Klasik sızıntı: kimlik URL'de → istisna metni URL'i taşır → defter. Adaptörün TÜM ağ yolu
    hata modunda sürülür; ne giden URL'de ne dönen metinde sır olmalı."""
    _set_endpoint(monkeypatch, alpaca.PAPER_BASE)
    rec = HttpRecorder(boom=True)
    monkeypatch.setattr(alpaca, "httpx", rec)

    ciktilar = [alpaca.account(), alpaca.positions(), alpaca.orders(),
                alpaca.asset_tradable("AAPL"), alpaca.cancel_order("id"),
                alpaca.replace_order_stop("id", 11.0),
                alpaca.submit_bracket("AAPL", 1, 10.0, 12.0, 9.0, client_order_id="P-x"),
                alpaca.close_all(), alpaca.transport(), alpaca.dashboard_view(), alpaca.status()]
    # Kimlik BAŞLIKTA taşınır (doğru yer) — sınav, DÖNEN değerler ve giden URL'ler üzerinde.
    metin = json.dumps(ciktilar, default=str) + json.dumps(rec.urls(), default=str)
    assert FAKE_KEY not in metin, "sır adaptör ÇIKTISINA/URL'ine sızdı"
    assert FAKE_SECRET not in metin, "sır adaptör ÇIKTISINA/URL'ine sızdı"
    for url in rec.urls():
        assert "?" not in url, f"adaptör sorgu dizesi kullanıyor (sır sızma yüzeyi): {url}"


def test_c6_leak_detector_has_teeth_positive_control(paper_secrets, monkeypatch):
    """POZİTİF KONTROL: sır GERÇEKTEN URL'e konsaydı yukarıdaki iddia düşer miydi?"""
    rec = HttpRecorder(boom=True)
    monkeypatch.setattr(alpaca, "httpx", rec)
    monkeypatch.setattr(alpaca, "_paper_base",
                        lambda: f"{alpaca.PAPER_BASE}?apikey={FAKE_KEY}")
    out = alpaca.account()
    metin = json.dumps([out, alpaca.transport(), rec.urls()], default=str)
    assert FAKE_KEY in metin, "dedektör bariz bir sızıntıyı göremiyor"


def test_c6_fmp_redacts_the_key_it_puts_in_the_query(sandbox_state, monkeypatch):
    """FMP anahtarı SORGU parametresidir — httpx hata metni tam URL'i taşır. Kaynağında maskelenmeli:
    yeniden fırlatılan istisna, sağlık kaydı ve ping() çıktısı anahtarsız olmalı."""
    import httpx as real_httpx
    from meridian.adapters import fmp
    monkeypatch.setenv("FMP_API_KEY", FAKE_KEY)
    secrets_mod.clear_cache()

    class Boom:
        """Yalnız `get`i ele geçirir; istisna SINIFLARI gerçek httpx'ten gelir (ping() tür ayrımı
        yapıyor — sahte modül türü bozarsa test yanlış şeyi ölçerdi)."""
        def __getattr__(self, name):
            return getattr(real_httpx, name)

        @staticmethod
        def get(url, params=None, timeout=None):
            q = "&".join(f"{k}={v}" for k, v in (params or {}).items())
            raise RuntimeError(f"ConnectError: GET {url}?{q}")

    monkeypatch.setattr(fmp, "httpx", Boom())
    with pytest.raises(Exception) as ei:
        fmp._get("quote", {"symbol": "AAPL"})
    assert FAKE_KEY not in str(ei.value), "FMP istisnası ANAHTARI taşıyor"
    assert FAKE_KEY not in json.dumps(fmp._HEALTH, default=str), "sağlık kaydı anahtar taşıyor"
    assert FAKE_KEY not in json.dumps(fmp.ping(), default=str), "ping() anahtar taşıyor"

    ledger = config.STATE / "events.jsonl"                     # ve defterde de olmamalı
    assert FAKE_KEY not in (ledger.read_text() if ledger.exists() else "")
    secrets_mod.clear_cache()


def test_c6_no_obs_call_passes_a_secret_value(sandbox_state):
    """Defterin MERKEZİ bir maskesi YOK (obs._emit ham alanları yazar) — savunma tamamen çağrı
    yerindedir. O yüzden yapısal iddia: hiçbir obs.log/warn/alarm çağrısının argüman AĞACINDA
    ÇIPLAK bir `secrets.get(...)` bulunmamalı. `bool()/len()/mask()` ile sarılmış olan DEĞER
    taşımaz (yokluk/varlık bilgisidir) — o yüzden ayrı sayılır."""
    SARMAL = {"bool", "len", "mask", "present", "int", "float"}

    def _cikarilan_sirlar(cagri):
        """Bu çağrının altındaki, değeri BOŞALTAN bir sarmalın içindeki secrets.get düğümleri."""
        guvenli = set()
        for n in ast.walk(cagri):
            if isinstance(n, ast.Call) and (
                    (isinstance(n.func, ast.Name) and n.func.id in SARMAL)
                    or (isinstance(n.func, ast.Attribute) and n.func.attr in SARMAL)):
                for inner in ast.walk(n):
                    if inner is not n:
                        guvenli.add(id(inner))
        return guvenli

    ihlal = []
    for rel, _src, tree in _py_sources():
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr in ("log", "warn", "alarm")
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in ("obs", "_obs")):
                continue
            guvenli = _cikarilan_sirlar(node)
            for alt in ast.walk(node):
                if isinstance(alt, ast.Call) and isinstance(alt.func, ast.Attribute) \
                        and alt.func.attr in ("get", "_fetch") \
                        and isinstance(alt.func.value, ast.Name) \
                        and alt.func.value.id in ("secrets", "secrets_mod") \
                        and id(alt) not in guvenli:
                    ihlal.append(f"{rel}:{node.lineno}")
    assert not ihlal, f"sır DEĞERİ olay defterine gidiyor: {ihlal}"


def test_c6_obs_scanner_catches_a_planted_leak_positive_control():
    """POZİTİF KONTROL: tarayıcı çıplak bir `secrets.get`i obs çağrısında gerçekten görüyor mu
    (ve `bool(...)` sarmalını doğru şekilde masum sayıyor mu)?"""
    kotu = "obs.warn('x', detail=secrets.get('ALPACA_PAPER_KEY'))\n"
    iyi = "obs.warn('x', has=bool(secrets.get('ALPACA_PAPER_KEY')))\n"

    def tarayici(src):
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and node.func.attr in ("log", "warn", "alarm"):
                guvenli = set()
                for n in ast.walk(node):
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                            and n.func.id in {"bool", "len"}:
                        guvenli |= {id(i) for i in ast.walk(n) if i is not n}
                for alt in ast.walk(node):
                    if isinstance(alt, ast.Call) and isinstance(alt.func, ast.Attribute) \
                            and alt.func.attr == "get" and id(alt) not in guvenli:
                        return True
        return False

    assert tarayici(kotu) is True, "tarayıcı çıplak sızıntıyı göremiyor"
    assert tarayici(iyi) is False, "tarayıcı masum bir varlık-kontrolünü suçluyor"


def test_c6_obs_ledger_stays_clean_when_the_transport_fails(paper_secrets, monkeypatch):
    """Davranışsal: kimlikler yüklüyken taşıma çöker, uyarılar deftere düşer — defterde sır olmamalı."""
    _set_endpoint(monkeypatch, "http://paper-api.alpaca.markets")   # şema uyarısını da tetikle
    monkeypatch.setattr(alpaca, "_SCHEME_WARNED", False)
    rec = HttpRecorder(boom=True)
    monkeypatch.setattr(alpaca, "httpx", rec)
    alpaca.account(); alpaca.orders(); alpaca.positions()
    alpaca.submit_bracket("AAPL", 1, 10.0, 12.0, 9.0, client_order_id="YANLIS-ONEK")

    ledger = config.STATE / "events.jsonl"
    text = ledger.read_text() if ledger.exists() else ""
    assert text, "defter boş — test hiçbir şey ölçmedi"
    assert FAKE_KEY not in text and FAKE_SECRET not in text, "OLAY DEFTERİNE sır düştü"


def test_c6_status_and_masks_never_return_a_full_value(sandbox_state, monkeypatch):
    """`secrets.status()` panoya gider — yalnız son 4. Uzun/kısa/tek karakterli değerlerde de."""
    for val in (FAKE_KEY, "kisadeger", "12345678", "123456789", "x" * 200):
        monkeypatch.setenv("FMP_API_KEY", val)
        secrets_mod.clear_cache()
        st = secrets_mod.status()["FMP_API_KEY"]
        assert st["set"] is True
        assert st["hint"] is not None and val not in st["hint"], f"maske tam değeri sızdırdı: {st}"
        assert len(st["hint"].replace("•", "")) <= 4, f"maske 4 karakterden fazla veriyor: {st}"
        assert val not in json.dumps(secrets_mod.status(), default=str)
        assert secrets_mod.mask(val) != val
    assert secrets_mod.mask(None) is None and secrets_mod.mask("") is None
    secrets_mod.clear_cache()


def test_c6_secrets_api_returns_no_value_and_logs_only_the_name(sandbox_state, monkeypatch):
    """POST /api/secrets/<ad> → yanıt ve olay defteri yalnız AD + maske taşımalı."""
    from fastapi.testclient import TestClient
    from meridian import api
    monkeypatch.setattr(api, "DASH_TOKEN", None)
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    secrets_mod.clear_cache()
    c = TestClient(api.app)

    r = c.post("/api/secrets/FMP_API_KEY", json={"value": FAKE_KEY})
    assert r.status_code == 200
    assert FAKE_KEY not in r.text, "yazma yanıtı DEĞERİ geri veriyor"
    g = c.get("/api/secrets")
    assert FAKE_KEY not in g.text, "/api/secrets DEĞERİ veriyor"
    ledger = config.STATE / "events.jsonl"
    assert FAKE_KEY not in (ledger.read_text() if ledger.exists() else ""), "defterde değer var"
    secrets_mod.clear_cache()


def test_c6_debug_export_never_ships_the_secret_store(sandbox_state, monkeypatch):
    """Teşhis paketi paylaşılabilir olmalı: secrets.json KESİNLİKLE dışarıda."""
    import io, zipfile
    from fastapi.testclient import TestClient
    from meridian import api
    monkeypatch.setattr(api, "DASH_TOKEN", None)
    monkeypatch.setenv("FMP_API_KEY", "")                 # env yerine DOSYAYA yaz (gerçek yol)
    secrets_mod.clear_cache()
    secrets_mod.set("FMP_API_KEY", FAKE_KEY)
    assert (config.STATE / "secrets.json").exists()

    r = TestClient(api.app).get("/api/debug_export")
    assert r.status_code == 200
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        names = z.namelist()
        blob = b"".join(z.read(n) for n in names)
    assert not any("secrets" in n for n in names), f"pakette sır dosyası: {names}"
    assert FAKE_KEY.encode() not in blob, "teşhis paketi ANAHTAR taşıyor"
    secrets_mod.clear_cache()


def test_c6_notify_scrubs_before_leaving_the_machine(sandbox_state, monkeypatch):
    """Dışarı veri gönderen TEK yol: bir alarm metni bir gün hata dizgisi taşırsa sır makineden ÇIKAR."""
    from meridian import notify
    monkeypatch.setenv("FMP_API_KEY", FAKE_KEY)
    monkeypatch.setenv("ALPACA_PAPER_SECRET", FAKE_SECRET)
    secrets_mod.clear_cache()
    kirli = f"HTTPStatusError GET https://x/y?apikey={FAKE_KEY} · secret={FAKE_SECRET}"
    temiz = notify.scrub(kirli)
    assert FAKE_KEY not in temiz and FAKE_SECRET not in temiz, f"scrub sızdırdı: {temiz}"
    assert notify.scrub("zararsız metin") == "zararsız metin"
    secrets_mod.clear_cache()


# =============================================================================================
# SÖZLEŞME 7 — API YÜZEYİ: /metrics ve /api/* yetki sınırı
# =============================================================================================
def _api_client(monkeypatch, token, raise_server_exceptions=True):
    from fastapi.testclient import TestClient
    from meridian import api
    monkeypatch.setattr(api, "DASH_TOKEN", token)
    # `with` KULLANILMAZ: lifespan `_autostart()`i koşturur (zamanlayıcı/Hermes/ayna akışı).
    return TestClient(api.app, raise_server_exceptions=raise_server_exceptions), api


def test_c7_every_api_route_is_token_gated(sandbox_state, monkeypatch):
    """Token AYARLIYKEN /api/* altındaki HER yol yetkisiz çağrıda 401 vermeli — tek bir açık uç,
    tüm hesap durumunu dışarı verir. Rota listesi uygulamadan OKUNUR (elle liste kayar)."""
    c, api = _api_client(monkeypatch, "AUDIT-TOKEN-777")
    # TEK bilinçli istisna (2026-07-27, operatör onayı): /api/public/summary — tanıtım sayfasının
    # doğrulamasız-DAR canlı veri ucu (hesap durumu DEĞİL, yalnız kamuya açık araştırma toplamları;
    # sözleşme api.py docstring'inde, izin gerekçesi test_api_audit_v21::test_p1c'de). Buraya ikinci
    # bir yol eklemek isteyen, aynı tartışmayı yeniden açmak zorunda.
    #
    # KİMLİK UÇLARI (2026-07-29): login/logout/session/setup-password `_auth` ÇAĞIRAMAZ — kimlik
    # doğrulamasının KENDİSİ onlardan geçer, yani kapalı bir kapıya girmenin yolu kapının kendisi
    # olamaz. Liste burada elle YAZILMAZ; üretim kodundan (`api.KIMLIK_UCLARI`) okunur, gerekçeler
    # uç uç orada durur. Bu uçların yetkisiz olması "korumasız" demek değildir: /api/login IP
    # başına kilitlidir, /api/logout yalnız çerez siler, /api/session hesap durumu döndürmez ve
    # /api/setup-password parola kurulduktan sonra 409'a döner. O sınırlar test_kimlik_v114'te
    # ayrıca çivilenir — burada YALNIZ "istisna listesi büyümedi" ölçülür.
    izinli = {"/api/public/summary"} | set(api.KIMLIK_UCLARI)
    acik = []
    for route in api.app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/api/") or path in izinli:
            continue
        for method in sorted(getattr(route, "methods", set()) - {"HEAD", "OPTIONS"}):
            url = re.sub(r"\{[^}]+\}", "x", path)
            r = c.request(method, url, json={})
            if r.status_code != 401:
                acik.append(f"{method} {path} → {r.status_code}")
    assert not acik, f"yetkisiz erişime açık uçlar: {acik}"


def test_c7_token_gate_is_actually_being_exercised_positive_control(sandbox_state, monkeypatch):
    """POZİTİF KONTROL: doğru token verildiğinde aynı uçlar 401 DEĞİL — yani yukarıdaki 401'ler
    'her şey kırık' değil, gerçekten kimlik denetimi."""
    c, _api = _api_client(monkeypatch, "AUDIT-TOKEN-777")
    r = c.get("/api/summary", headers={"x-meridian-token": "AUDIT-TOKEN-777"})
    assert r.status_code != 401, "doğru token da reddediliyor — kapı testi anlamsız"
    assert c.get("/api/summary", headers={"x-meridian-token": "AUDIT-TOKEN-778"}).status_code == 401


def test_c7_metrics_hides_account_state_from_a_remote_caller(sandbox_state, monkeypatch):
    """/metrics kasıtlı olarak yetkisizdir (scraper). Uzak + yetkisiz çağrı YALNIZ canlılık
    görmeli: öz sermaye, pozisyon, P&L, özerklik seviyesi, LLM harcaması DIŞARI ÇIKMAMALI."""
    c, _api = _api_client(monkeypatch, "AUDIT-TOKEN-777")
    store.write_json("heartbeat.json", {"equity": 123456.78, "open_positions": 3, "day_pnl_pct": -0.02})
    body = c.get("/metrics").text
    for gizli in ("meridian_equity_usd", "meridian_open_positions", "meridian_day_pnl_pct",
                  "meridian_autonomy_level", "meridian_hermes_spend_usd", "123456"):
        assert gizli not in body, f"/metrics uzak çağrıya {gizli} sızdırdı"
    assert "meridian_up" in body and "meridian_halted" in body, "canlılık de kayboldu"

    tam = c.get("/metrics", headers={"x-meridian-token": "AUDIT-TOKEN-777"}).text   # POZİTİF KONTROL
    assert "meridian_equity_usd" in tam, "yetkiliye de vermiyor — test bir şey ölçmüyor"


def test_c7_healthz_discloses_only_liveness(sandbox_state, monkeypatch):
    """/healthz bilinçli olarak yetkisiz. Alan kümesi DAR kalmalı — buraya bir gün 'equity' eklenirse
    kimlik denetimsiz bir hesap-durumu ucu doğar."""
    c, _api = _api_client(monkeypatch, "AUDIT-TOKEN-777")
    store.write_json("heartbeat.json", {"equity": 123456.78, "open_positions": 3, "last_bar": "2026-07-21"})
    body = c.get("/healthz").json()
    assert set(body) <= {"status", "heartbeat_age_seconds", "halted", "mode", "last_bar"}, body
    assert "123456" not in json.dumps(body)


def test_c7_write_endpoints_reject_an_unauthenticated_caller(sandbox_state, monkeypatch):
    """Yazma yüzeyi (HALT / resume / onay / düzleştirme / sır / emir) yetkisiz çağrıyla ASLA
    çalışmamalı — ve gerçekten yan etki bırakmadığı sandbox'ta doğrulanır."""
    c, _api = _api_client(monkeypatch, "AUDIT-TOKEN-777")
    from meridian import health
    yollar = ["/api/halt", "/api/resume", "/api/control/halt", "/api/control/learn_halt",
              "/api/control/cancel_open", "/api/alpaca/close_all", "/api/alpaca/submit_armed",
              "/api/approvals/x", "/api/secrets/FMP_API_KEY", "/api/skills/apply",
              "/api/hermes/pool_key", "/api/scheduler/advance"]
    for p in yollar:
        assert c.post(p, json={"on": True}).status_code == 401, f"{p} yetkisiz çağrıyı kabul etti"
    assert not health.halt_path().exists(), "yetkisiz çağrı HALT bayrağı yarattı"
    assert not health.learn_halt_path().exists(), "yetkisiz çağrı LEARN_HALT yarattı"


def test_c7_no_production_module_drives_its_own_write_endpoints():
    """HALT/onay/düzleştirme uçları YALNIZ operatör isteğiyle sürülmeli: hiçbir üretim modülü
    kendi API'sine POST atmamalı (ajan/döngü kendini 'operatör' ilan edemez)."""
    UCLAR = ("/api/halt", "/api/resume", "/api/approvals", "/api/alpaca/close_all",
             "/api/alpaca/submit_armed", "/api/control/halt", "/api/secrets/")
    ihlal = []
    for rel, _src, tree in _py_sources():
        if rel.name == "api.py":                       # uçları TANIMLAYAN modül — tek meşru yer
            continue
        # Yorum ve düzyazı yetki değildir: yalnız İSTEK HEDEFİ gibi duran dizgeler (yolla BAŞLAYAN
        # ya da kendi sunucusuna işaret eden mutlak URL) sayılır.
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
                continue
            deger = node.value.strip()
            for uc in UCLAR:
                if deger.startswith(uc) or re.match(rf"https?://[^/]+{re.escape(uc)}", deger):
                    ihlal.append(f"{rel}:{node.lineno} → {deger[:60]}")
    assert not ihlal, f"üretim kodu kendi yazma ucunu sürüyor: {ihlal}"

    # ve hiçbir modül kendi sunucusuna HTTP atmıyor (dolaylı 'operatör taklidi' yolu)
    kendi = [f"{rel}:{n.lineno}" for rel, _s, tree in _py_sources() for n in ast.walk(tree)
             if isinstance(n, ast.Constant) and isinstance(n.value, str)
             and re.search(r"(127\.0\.0\.1|localhost):8080", n.value)]
    assert not kendi, f"üretim kodu kendi API'sine bağlanıyor: {kendi}"


def test_c7_token_comparison_fails_closed_on_a_non_ascii_token(sandbox_state, monkeypatch):
    """DÜZELTİLDİ (2026-07-22, aynı gün): `hmac.compare_digest` ASCII-DIŞI str'de TypeError atıyordu,
    yani 401 yerine 500 — ve sevkiyat şablonu tam öyle bir yer tutucu koyuyordu ('DEĞİŞTİR-…').
    Yön güvenliydi (kapalı, veri sızmaz) ama operatörü "token'ı kaldırayım" çözümüne itiyordu, ki o
    da yetkisiz açık bir yüzeye düşürürdü. Artık iki taraf da BAYTA çevriliyor: kapı düzgün 401
    veriyor. ASCII-dışı token'ın kullanılamaz olduğu ayrıca açılışta alarmla bildiriliyor.

    GÜNCELLEME (2026-07-29): bu test eskiden `?token=` SORGU yolunun 200 döndüğünü doğruluyordu.
    O yol 2026-07-28'de BİLEREK KALDIRILDI (bkz. api._auth docstring'i): URL'ler sunucu loglarına,
    tarayıcı geçmişine ve `Referer` başlığına düşer, yani sorgudaki bir sır sır değildir. Test
    beklentisi koda uydurulmadı — KALDIRMA ÇİVİLENDİ: doğru token bile sorgudan geçmemeli. Aksi
    halde yarın biri "eski test böyle istiyordu" diyerek yolu geri açabilirdi."""
    c, _api = _api_client(monkeypatch, "DEĞİŞTİR-uzun-rastgele-token",
                          raise_server_exceptions=False)
    r = c.get("/api/summary", headers={"x-meridian-token": "x"})
    assert r.status_code != 200, "ASCII-dışı token kapıyı AÇIK bıraktı"
    assert r.status_code == 401, f"artık düzgün 401 dönmeli, alınan: {r.status_code}"
    # SORGU YOLU KAPALI: DOĞRU token'ı sorguda sunmak bile kapıyı açmamalı. Bu satır bir davranışı
    # değil, bir KARARI korur — sırrın URL'e konabildiği her yol, o sırrı loga yazan bir yoldur.
    r2 = c.get("/api/summary", params={"token": "DEĞİŞTİR-uzun-rastgele-token"})
    assert r2.status_code == 401, (
        f"`?token=` sorgu yolu GERİ AÇILMIŞ (alınan {r2.status_code}) — URL'deki sır loglara, "
        f"tarayıcı geçmişine ve Referer başlığına sızar; kimlik yalnız çerez ya da başlıkla taşınır")
    with pytest.raises(UnicodeEncodeError):      # başlık yolu YAPISAL olarak imkânsız
        c.get("/api/summary", headers={"x-meridian-token": "DEĞİŞTİR-uzun-rastgele-token"})

    ascii_c, _ = _api_client(monkeypatch, "SADECE-ASCII-TOKEN")     # POZİTİF KONTROL
    assert ascii_c.get("/api/summary",
                       headers={"x-meridian-token": "SADECE-ASCII-TOKEN"}).status_code == 200


def test_c7_auth_is_a_noop_when_no_token_is_configured(sandbox_state, monkeypatch):
    """KANIT (gizli değil, açık): token AYARLI DEĞİLKEN `_auth` hiçbir şey yapmaz — API tamamen
    açıktır ve tek savunma uvicorn'un 127.0.0.1 bağı olur. Bu testin görevi bu bağımlılığı
    GÖRÜNÜR kılmak; bağ değişirse (0.0.0.0) hesap durumu kimliksiz dışarı açılır."""
    c, _api = _api_client(monkeypatch, None)
    assert c.get("/api/summary").status_code == 200, "token yokken de kapalı — belge güncellenmeli"
    assert c.post("/api/halt").status_code in (200, 500), "token yokken yazma ucu da açık olmalı (kanıt)"
    from meridian import health
    if health.halt_path().exists():
        health.halt_path().unlink()                 # sandbox içi — canlı bayrağa DOKUNULMAZ

    # Tek gerçek savunma: bağ adresi. Yorumlar değil, GERÇEK komut satırları taranır.
    for f in ("serve.sh", "docker-compose.yml", "deploy/oracle-a1/meridian.service"):
        p = REPO / f
        if not p.exists():
            continue
        for line in p.read_text().splitlines():
            kod = line.split("#", 1)[0]
            if "--host" in kod:
                assert "0.0.0.0" not in kod, f"{f}: {line.strip()} — tüm arayüzler + token opsiyonel"

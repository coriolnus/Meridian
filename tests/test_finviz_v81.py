"""test_finviz_v81.py — FİNVİZ OTONOM ADAY KAYNAĞI (2026-07-23).

Operatör: "Finviz'i de eklemek istiyorum" → otonom aday kaynağı, 1 haftalık Elite trial + public.

Tasarım sözleşmesi (adapters/finviz.py + dataset.load_live):
  1. Finviz yalnız EVRENİ genişletir; karar/kapı ASLA Finviz'e bakmaz.
  2. LOOK-AHEAD KARANTİNASI: bugünün listesi geçmişe uygulanamaz. `dataset.load()` (replay/yansıma
     yolu) Finviz'e dokunmaz ve `load_live` in-process cache'i KİRLETMEZ — yoksa gelecek bilgisi
     2023 replay'ine sızardı. Bu, bir edge'in gerçekliğini yok edecek en sinsi hata; burada kilitli.
  3. DÜRÜST BOZUNMA: token yok/trial dolmuş/ağ düşük → public'e, o da olmazsa BOŞ + olay. "Aday yok"
     ile "Finviz'e ulaşılamadı" asla aynı görünmez.
  4. GİZLİLİK: token hiçbir log/hata metnine sızmaz (son-4 dışında).
"""
from __future__ import annotations

import httpx
import pandas as pd
import pytest

from meridian import dataset, secrets
from meridian.adapters import finviz


def _resp(status: int, text: str, url: str = "https://x") -> httpx.Response:
    return httpx.Response(status, text=text, request=httpx.Request("GET", url))


def _bars(n: int = 300) -> pd.DataFrame:
    idx = pd.date_range("2023-01-02", periods=n, freq="B")
    return pd.DataFrame({"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5,
                         "volume": 1_000_000}, index=idx)


@pytest.fixture(autouse=True)
def _reset_health():
    finviz._HEALTH.update({"ok": None, "source": None, "n": 0, "calls": 0, "fails": 0,
                           "last_status": None, "last_error": "", "at": None})
    yield


# ---------------- 1) LOOK-AHEAD KARANTİNASI (en kritik) ----------------
def test_replay_load_never_touches_finviz(sandbox_state, monkeypatch):
    """`dataset.load()` replay/yansıma yoludur. Finviz'i çağırırsa bugünün listesi 2023'e sızar.
    Bu test onu bir mayın gibi bekler: discover çağrılırsa patlar."""
    def _patla(*a, **k):
        raise AssertionError("dataset.load() Finviz'i çağırdı — LOOK-AHEAD SIZINTISI")
    monkeypatch.setattr(finviz, "discover_universe", _patla)
    monkeypatch.setattr(finviz, "discover", _patla)
    # load() FMP'ye gitmesin diye load_many'i sabitliyoruz
    monkeypatch.setattr(dataset.data, "load_many", lambda *a, **k: {"AAA": _bars()})
    monkeypatch.setattr(dataset.data, "load_bars", lambda *a, **k: _bars())
    dataset._cache.clear()
    monkeypatch.setattr(dataset, "_index_hard_issues", lambda idx: [])
    bars, _ = dataset.load(use_cache=False)
    assert "AAA" in bars                       # yüklendi ve Finviz asla çağrılmadı (yoksa AssertionError)


def test_load_live_does_not_pollute_the_shared_cache(sandbox_state, monkeypatch):
    """load_live evreni genişletir AMA `_cache`'i mutasyona uğratmaz — sonraki `load()` (replay yolu)
    genişlemiş evreni GÖRMEMELİ. `{**bars, ...}` yeni sözlük olduğu için _cache dokunulmaz kalır.

    TSK-116 düzeltme turu 3 (2026-09-03): canlı taban artık `LIVE_UNIVERSE` + korunan ticker'lardır
    (`REPLAY_UNIVERSE` DEĞİL, bkz. `_canli_korunan_evren`) — bu yüzden REPLAY önbelleğinde duran
    keyfi bir "AAA" ismi artık `live_bars`e KARIŞMAZ; bu, review Ö-3'ün düzelttiği TAM şeydir (canlı
    yol yalnız KENDİ evrenini görür, REPLAY'in süpersetini değil). Asıl iddia DEĞİŞMEDİ: paylaşılan
    REPLAY önbelleği (`_cache["bars"]`) `load_live` sonrası AYNI kalmalı. `data.load_bars` (SPY)
    BİLEREK sağlıklı sabitlenir — endeks bozuk-kapı/kurtarma dalı bu testin konusu DEĞİL (o Ö-3
    çivileriyle v393'te ayrıca ölçülüyor)."""
    dataset._cache.clear()
    dataset._cache["bars"] = {"AAA": _bars()}          # REPLAY_UNIVERSE önbelleği (sabit, KEYFİ isim)
    dataset._cache["index"] = _bars()
    monkeypatch.setattr(finviz, "discover_universe", lambda use_cache=True: ["FINVIZ1"])
    monkeypatch.setattr(dataset.data, "load_bars", lambda *a, **k: _bars())  # SPY sağlıklı — kurtarma dalına GİRİLMEZ
    monkeypatch.setattr(dataset, "_index_hard_issues", lambda idx: [])       # `_bars()` "date" kolonsuz; validate_bars'ın kendisi bu testin konusu değil (aynı desen: test_replay_load_never_touches_finviz)
    monkeypatch.setattr(dataset.data, "load_many", lambda syms, *a, **k: {s: _bars() for s in syms})

    live_bars, _ = dataset.load_live(use_cache=True)
    assert "FINVIZ1" in live_bars, "canlı evren Finviz keşfiyle genişlemedi"
    assert "AAPL" in live_bars, "canlı taban (LIVE_UNIVERSE) hiç yüklenmemiş"
    assert "AAA" not in live_bars, \
        "REPLAY önbelleğindeki keyfi isim canlı taramaya sızdı — taban artık LIVE_UNIVERSE olmalıydı"
    # ASIL İDDİA: paylaşılan cache genişlemedi → replay yolu temiz kaldı
    assert set(dataset._cache["bars"]) == {"AAA"}, "load_live cache'i KİRLETTİ — look-ahead sızıntısı"
    replay_bars, _ = dataset.load(use_cache=True)
    assert "FINVIZ1" not in replay_bars, "replay yolu Finviz ticker'ı gördü"
    dataset._cache.clear()


# ---------------- 2) DÜRÜST BOZUNMA ----------------
def test_expired_trial_token_falls_back_to_public_not_silence(monkeypatch):
    """1 haftalık trial: token GEÇERSİZ (403). Sessizce boş dönmek yerine public'e düşmeli."""
    monkeypatch.setattr(secrets, "get", lambda n: "trial_token" if n == "FINVIZ_API_KEY" else None)
    def _elite(*a, **k):
        raise httpx.HTTPStatusError("403", request=httpx.Request("GET", "https://x"),
                                    response=_resp(403, "Forbidden"))
    monkeypatch.setattr(finviz, "_fetch_elite", _elite)
    monkeypatch.setattr(finviz, "_fetch_public", lambda f, t, pages=5: ["NVDA", "AMD"])
    r = finviz.discover()
    assert r["source"] == "public" and r["tickers"] == ["NVDA", "AMD"]
    # elite başarısızlığı YUTULMADI: iki çağrı (elite→public) ve en az bir hata kayıtlı. (last_status
    # public başarısıyla ezilir — health SON durumu yansıtır; kanıt fails/calls sayacındadır.)
    h = finviz.health()
    assert h["calls"] >= 2 and h["fails"] >= 1


def test_total_outage_returns_empty_with_a_reason(sandbox_state, monkeypatch):
    """Elite yok + public düşük → BOŞ ama NEDENLİ, ve olay defterine yazılı (dürüst bozunma)."""
    from meridian import store
    monkeypatch.setattr(secrets, "get", lambda n: None)
    monkeypatch.setattr(finviz, "_fetch_public",
                        lambda *a, **k: (_ for _ in ()).throw(httpx.ConnectError("no net")))
    tickers = finviz.discover_universe(use_cache=False, allow_public=True)
    assert tickers == []
    cache = store.read_json("finviz_universe.json", {})
    assert cache["source"] == "none" and cache["reason"]
    blob = "".join(str(e) for e in store.read_jsonl("events.jsonl"))
    assert "finviz_unavailable" in blob, "evren daraldı ama olay YOK — sessiz bozunma"


def test_a_healthy_discover_logs_the_source_and_count(sandbox_state, monkeypatch):
    """POZİTİF KONTROL + kurt masalı yasağı: sağlıklı çekim de olay yazar ama 'unavailable' DEĞİL."""
    from meridian import store
    monkeypatch.setattr(secrets, "get", lambda n: None)
    monkeypatch.setattr(finviz, "_fetch_public", lambda *a, **k: ["AAA", "BBB", "CCC"])
    tickers = finviz.discover_universe(use_cache=False, allow_public=True)
    assert tickers == ["AAA", "BBB", "CCC"]
    blob = "".join(str(e) for e in store.read_jsonl("events.jsonl"))
    assert "finviz_universe" in blob and "finviz_unavailable" not in blob


def test_public_scraping_is_off_by_default_in_the_autonomous_loop(sandbox_state, monkeypatch):
    """BAN KORUMASI: token yokken otonom döngü sürekli public scraping YAPMAMALI. allow_public
    varsayılan kapalı → Finviz dürüstçe devre dışı, _fetch_public'e HİÇ dokunulmaz."""
    monkeypatch.setattr(secrets, "get", lambda n: None)
    monkeypatch.setattr(finviz, "_fetch_public",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("public scraping DENENDİ — ban riski")))
    monkeypatch.delenv("MERIDIAN_FINVIZ_PUBLIC", raising=False)
    tickers = finviz.discover_universe(use_cache=False)          # allow_public=None → env → kapalı
    assert tickers == []
    from meridian import store
    assert store.read_json("finviz_universe.json", {})["source"] == "none"


# ---------------- 3) PARSE DOĞRULUĞU ----------------
def test_elite_csv_parse_extracts_ticker_column(monkeypatch):
    """Elite export CSV döndürür; 'Ticker' sütunu doğru okunmalı, sıra korunmalı, tekrarlar düşmeli."""
    csv = "No.,Ticker,Company\n1,NVDA,Nvidia\n2,AMD,AMD Inc\n3,NVDA,dup\n"
    monkeypatch.setattr(secrets, "get", lambda n: "tok")
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _resp(200, csv))
    assert finviz._fetch_elite("f", 5.0) == ["NVDA", "AMD"]


def test_public_html_regex_pulls_tickers_from_quote_links():
    """Public fallback bs4 kullanamaz (yok); `quote.ashx?t=` linklerinden regex ile çeker."""
    html = ('<a href="quote.ashx?t=NVDA&ty=c">NVDA</a> junk '
            '<a href="quote.ashx?t=AMD">AMD</a> <a href="quote.ashx?t=NVDA">dup</a>')
    hits = finviz._TICKER_RE.findall(html)
    assert hits[:3] == ["NVDA", "AMD", "NVDA"]        # ham; discover dedup eder


def test_implausible_parse_is_rejected_not_trusted(monkeypatch):
    """Zehirli veri / parse hatası: 5000 'sembol' tüm sayfayı ticker sanmaktır — makul dışı, reddedilir."""
    assert finviz._plausible(["A", "B"]) is True
    assert finviz._plausible([]) is False
    assert finviz._plausible(["X"] * 5000) is False
    monkeypatch.setattr(secrets, "get", lambda n: None)
    monkeypatch.setattr(finviz, "_fetch_public", lambda *a, **k: ["Z"] * 5000)
    r = finviz.discover()
    assert r["source"] == "none" and "makul dışı" in r["reason"]


# ---------------- 4) GİZLİLİK ----------------
def test_token_never_leaks_into_error_text(monkeypatch):
    """httpx hata metni TAM URL taşır (fmp.py dersi). auth=<token> maskelenmeli."""
    kirli = "GET https://elite.finviz.com/export.ashx?v=111&auth=SUPERSECRET123 failed"
    assert "SUPERSECRET123" not in finviz._mask_url(kirli)
    assert "auth=***" in finviz._mask_url(kirli)


def test_status_masks_the_token(sandbox_state, monkeypatch):
    """Pano token'ı yalnız son-4 maskeli görür."""
    monkeypatch.setattr(secrets, "get", lambda n: "abcd1234efgh5678" if n == "FINVIZ_API_KEY" else None)
    st = finviz.status()
    assert "abcd1234" not in str(st), "token panoya sızdı"


# ---------------- 5) KARAR YETKİSİ SINIRI ----------------
def test_finviz_is_universe_only_never_a_gate_input():
    """MİMARİ SINIR: Finviz karar/kapı/skor mantığına GİRMEZ. Statik kanıt — guard/gate/strategy
    modülleri finviz'i import etmemeli; yalnız dataset (evren) ve api/pano (görünürlük) etmeli."""
    import ast
    from pathlib import Path
    kok = Path(__file__).resolve().parent.parent / "meridian"
    yasak = ("guard.py", "strategy.py", "reflect.py", "backtest.py", "probgate.py", "score.py")
    for f in yasak:
        p = kok / f
        if not p.exists():
            continue
        src = p.read_text()
        assert "finviz" not in src.lower(), f"{f} Finviz'e bakıyor — karar mantığına sızdı"


# ---------------- 6) SKİLL YÜZEYİ: TAM SATIRLI EXPORT (2026-07-27) ----------------
# `export_rows` operatörün terminalden tam tabloyu görmesi içindir (skills/finviz-screener).
# Sözleşme: kanonik uç TEK KAYNAKTA kalır, `_fetch_elite` onun üstünde yeniden kurulur ve
# DAVRANIŞI DEĞİŞMEZ, token hata metnine sızmaz, kolon adları Finviz'den geldiği gibi geçer.

_EXPORT_CSV = (
    "No.,Ticker,Company,Sector,Price,Change\n"
    "1,NVDA,NVIDIA Corporation,Technology,140.20,2.31%\n"
    "2,AMD,Advanced Micro Devices,Technology,132.05,1.10%\n"
    "3,AVGO,Broadcom Inc,Technology,255.40,-0.45%\n"
)


def test_export_rows_returns_full_rows_with_finvizs_own_headers(monkeypatch):
    """Skill yüzeyi ticker değil TABLO ister. Başlıklar Finviz'den geldiği GİBİ geçmeli — kolon adı
    normalleştirilmez/uydurulmaz, yoksa skill var olmayan bir sütunu rapor eder."""
    monkeypatch.setattr(secrets, "get", lambda n: "tok")
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _resp(200, _EXPORT_CSV))
    rows = finviz.export_rows("f")
    assert len(rows) == 3 and all(isinstance(r, dict) for r in rows)
    assert list(rows[0]) == ["No.", "Ticker", "Company", "Sector", "Price", "Change"]
    assert rows[0]["Ticker"] == "NVDA" and rows[0]["Price"] == "140.20"
    assert rows[2]["Company"] == "Broadcom Inc"


def test_export_rows_uses_the_canonical_endpoint_and_the_requested_view(monkeypatch):
    """Kolon setini `v=` belirler; skill'in seçtiği view URL'e GERÇEKTEN gitmeli. Ayrıca uç kanonik
    (`/export/screener`, .ashx DEĞİL) ve follow_redirects açık — 301-boş-gövde tuzağı kapalı."""
    seen: dict = {}

    def _get(url, **kw):
        seen.update(url=url, params=kw.get("params"), follow=kw.get("follow_redirects"))
        return _resp(200, _EXPORT_CSV)

    monkeypatch.setattr(secrets, "get", lambda n: "tok")
    monkeypatch.setattr(httpx, "get", _get)
    finviz.export_rows("sh_price_o10,ta_sma50_pa", view="171")
    assert seen["url"] == finviz.ELITE_EXPORT and ".ashx" not in seen["url"]
    assert seen["params"]["v"] == "171"
    assert seen["params"]["f"] == "sh_price_o10,ta_sma50_pa"
    assert seen["follow"] is True


def test_export_rows_without_a_token_refuses_loudly(monkeypatch):
    """Anahtarsız Elite export ÇALIŞMAZ. Boş liste dönüp 'sonuç yok' gibi görünmek yasak — ve ağa
    hiç gidilmemeli."""
    monkeypatch.setattr(secrets, "get", lambda n: None)
    monkeypatch.setattr(httpx, "get",
                        lambda *a, **k: pytest.fail("anahtar yokken ağa gidildi"))
    with pytest.raises(RuntimeError, match="FINVIZ_API_KEY absent"):
        finviz.export_rows("f")


def test_fetch_elite_behaviour_is_unchanged_by_the_export_rows_refactor(monkeypatch):
    """REGRESYON: `_fetch_elite` artık export_rows üstünde duruyor. Otonom keşif yolunun gördüğü
    şey birebir aynı kalmalı — aynı mock, aynı ticker listesi, aynı sıra."""
    monkeypatch.setattr(secrets, "get", lambda n: "tok")
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _resp(200, _EXPORT_CSV))
    assert finviz._fetch_elite("f", 5.0) == ["NVDA", "AMD", "AVGO"]


def test_export_rows_masks_the_token_in_http_errors_but_keeps_the_status(monkeypatch):
    """GİZLİLİK + DÜRÜST BOZUNMA birlikte: hata metni skill'de doğrudan terminale basılıyor, token
    orada olmamalı; ama istisnanın TÜRÜ ve status_code korunmalı ki discover/ping 401/403'ü geçici
    ağ hatasından ayırmayı sürdürsün."""
    kirli = "https://elite.finviz.com/export/screener?v=111&f=x&auth=SUPERSECRET123"
    monkeypatch.setattr(secrets, "get", lambda n: "SUPERSECRET123")
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _resp(403, "Forbidden", url=kirli))
    with pytest.raises(httpx.HTTPStatusError) as ei:
        finviz.export_rows("x")
    assert "SUPERSECRET123" not in str(ei.value), "token hata metnine sızdı"
    assert "auth=***" in str(ei.value)
    assert ei.value.response.status_code == 403


def test_ping_still_classifies_401_through_the_masked_error(monkeypatch):
    """Uçtan uca: maskeleme eklendi diye ping'in 'token geçersiz' teşhisi kaybolmamalı."""
    kirli = "https://elite.finviz.com/export/screener?v=111&auth=SUPERSECRET123"
    monkeypatch.setattr(secrets, "get", lambda n: "SUPERSECRET123")
    monkeypatch.setattr(httpx, "get", lambda *a, **k: _resp(401, "no", url=kirli))
    r = finviz.ping()
    assert r["ok"] is False and "401" in r["detail"]
    assert "SUPERSECRET123" not in str(finviz.health()), "token sağlık karnesine sızdı"


# ---------------- 7) SKİLL SCRIPT'İ (finviz-screener) ----------------
def _script_path():
    from pathlib import Path
    return (Path(__file__).resolve().parent.parent / "skills" / "finviz-screener"
            / "scripts" / "open_finviz_screener.py")


def test_skill_script_compiles_and_documents_the_new_flags(tmp_path):
    import py_compile
    import subprocess
    import sys
    p = _script_path()
    assert p.is_file(), "skill script'i bulunamadı"
    py_compile.compile(str(p), cfile=str(tmp_path / "s.pyc"), doraise=True)
    r = subprocess.run([sys.executable, str(p), "--help"],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    for flag in ("--fetch", "--open", "--limit", "--csv"):
        assert flag in r.stdout, f"{flag} belgelenmemiş"


def test_skill_script_refuses_fetch_without_a_key_instead_of_pretending(tmp_path):
    """Anahtarsız `--fetch`: sessiz boş tablo değil, NET hata + çıkış kodu 2. Ortam hermetik —
    MERIDIAN_ROOT boş bir dizine bakar, yani yerel sır deposu da boştur."""
    import os
    import subprocess
    import sys
    env = dict(os.environ)
    env.pop("FINVIZ_API_KEY", None)
    env.pop("MERIDIAN_GCP_PROJECT", None)
    env["MERIDIAN_ROOT"] = str(tmp_path)
    r = subprocess.run([sys.executable, str(_script_path()), "--filters", "cap_small", "--fetch"],
                       capture_output=True, text=True, timeout=120, env=env)
    assert r.returncode == 2, f"rc={r.returncode} out={r.stdout} err={r.stderr}"
    assert "FINVIZ_API_KEY" in r.stderr

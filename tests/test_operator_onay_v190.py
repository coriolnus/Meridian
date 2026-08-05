"""test_operator_onay_v190.py — OPERATÖR ONAY YOLU + SON DÖNGÜ PANELİ (2026-08-05).

İKİ OPERATÖR BULGUSU, İKİ AYRI SINIF:

  (1) "REVIEW EDEBİLİYORUM, İŞLEM YAPAMIYORUM" — kapı "insan baksın" (REVIEW) diyor, pano planı
      gösteriyor, ve operatörün elinde TEK bir eylem yok. Üstelik keşif dallarında (bütçe %0 ya da
      uyuyan kurulum) REVIEW planı hiç silahlanmıyordu: `explore_pool`a YALNIZ GO giriyordu. Yani
      hüküm okunabiliyor, uygulanamıyordu — bir kapının en sessiz arıza hâli.
      SÖZLEŞME: onay bir OLAYdır, hüküm DEĞİL (`gate_verdict` geriye dönük değişmez) · NO_GO ASLA
      onaylanamaz · seansı geçmiş plan onaylanamaz · yetkisiz çağrı 401 · yazımın yasası loop'ta
      (defter sözleşmesinin yazar listesi: loop/run/hermes — uç nokta ikinci yazar OLAMAZ).

  (2) "SON DÖNGÜ PANELİ ÖLÇÜLEMEDİ DİYOR" — pano "Dün gece" kartını olay akışının SON 80 kaydında
      `daily_cycle` arayarak kuruyordu. Olay günde BİR yazılır; gün içindeki poll/uyarı satırları
      onu pencereden taşırınca kart "ölçülemedi" diyordu — oysa döngü koşmuştu. Ölçüm değil
      PENCERE bozuktu. Kart artık döngünün KENDİ kaydından okur (`last_cycle.json` → /api/today).
"""
from __future__ import annotations

import ast
import inspect
import json
import pathlib
import shutil
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from meridian import api, config, health, loop, obs, store
from tests.conftest import make_bars

APP_JS = pathlib.Path("meridian/web/app.js")
HDR = {"x-meridian-token": "T0KEN"}


@pytest.fixture
def seeded(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    (sandbox_state / "strategy.yaml").write_text(yaml.safe_dump(config.default_strategy()))
    yield sandbox_state
    config.reload_config()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api, "DASH_TOKEN", "T0KEN")
    return TestClient(api.app)


def _plan(pid="P-2026-08-05-AAA", verdict="REVIEW", date="2026-08-05", **ek):
    """Canlı `trade_plans.jsonl` satırının gerçek şekli (alan adları loop.daily_cycle'dan)."""
    return {"id": pid, "date": date, "ticker": pid.split("-")[-1], "side": "long",
            "entry_trigger": 100.0, "stop": 95.0, "targets": [115.0], "profit_target": 115.0,
            "size_r": 1.0, "r_multiple_expected": 3.0, "regime_at_plan": "chop", "sector": "Tech",
            "score": 71, "setup": "breakout_vcp", "strategy_version": 1,
            "gate_verdict": verdict, "gate_reasons": ["skor alt bantta"], **ek}


def _kitap(**ek):
    store.write_json("portfolio.json", {"armed": [], "positions": {}, "last_date": "2026-08-05",
                                        "peak_equity": 100_000.0, **ek})


# =================================================================================================
# 1) ONAY YOLU — REVIEW → onay → GİRİŞE UYGUN (silahlı kuyrukta)
# =================================================================================================
def test_onay_yolu_review_plani_giris_kuyruguna_alir(seeded, client):
    store.write_jsonl("trade_plans.jsonl", [_plan()])
    _kitap()

    # ÖNCE-KIRMIZI TABANI: onaysız REVIEW planı giriş kuyruğuna UYGUN DEĞİL.
    assert loop.girise_uygun(_plan()) is False

    r = client.post("/api/plan/P-2026-08-05-AAA/onayla", headers=HDR)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True and body["silahli"] is True and body["ticker"] == "AAA"

    satir = store.read_jsonl("trade_plans.jsonl")[-1]
    assert satir["operator_onayi"]["kanal"] == "pano" and satir["operator_onayi"]["ts"]
    assert satir["gate_verdict"] == "REVIEW", \
        "onay kapı hükmünü GERİYE DÖNÜK değiştirdi — onay bir olaydır, hüküm değil"
    assert loop.girise_uygun(satir) is True, "onaylı REVIEW hâlâ giriş kuyruğuna uygun değil"

    armed = store.read_json("portfolio.json", {})["armed"]
    assert [a["id"] for a in armed] == ["P-2026-08-05-AAA"], "onaylı plan silahlı kümeye girmedi"
    assert armed[0]["operator_onayi"]["ts"], "silahlı kopya onay damgasını taşımıyor"

    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "plan_operator_approved"]
    assert len(ev) == 1 and ev[0]["plan_id"] == "P-2026-08-05-AAA" and ev[0]["kanal"] == "pano"


def test_ikinci_onay_ikinci_emir_dogurmaz(seeded, client):
    """Dedup: aynı plana iki kez basmak silahlı kümeye ikinci kopya EKLEMEZ ve damgayı tazelemez."""
    store.write_jsonl("trade_plans.jsonl", [_plan()])
    _kitap()
    ilk = client.post("/api/plan/P-2026-08-05-AAA/onayla", headers=HDR).json()
    ikinci = client.post("/api/plan/P-2026-08-05-AAA/onayla", headers=HDR)
    assert ikinci.status_code == 200, ikinci.text
    assert ikinci.json()["zaten_onayliydi"] is True and ikinci.json()["zaten_silahliydi"] is True
    assert len(store.read_json("portfolio.json", {})["armed"]) == 1
    assert store.read_jsonl("trade_plans.jsonl")[-1]["operator_onayi"]["ts"] == \
        ilk["operator_onayi"]["ts"], "onay damgası ikinci basışta yeniden yazıldı"


# =================================================================================================
# 2) REDLER — hepsi 409 + SEBEP (sessiz "olmadı" yok)
# =================================================================================================
def test_no_go_asla_onaylanamaz(seeded, client):
    """Guard'ın sert reddi MUTLAKTIR: onaylanabilseydi kapının kendisi kalkardı."""
    store.write_jsonl("trade_plans.jsonl", [_plan("P-2026-08-05-BBB", verdict="NO_GO")])
    _kitap()
    r = client.post("/api/plan/P-2026-08-05-BBB/onayla", headers=HDR)
    assert r.status_code == 409 and "NO_GO" in r.json()["detail"]
    assert "operator_onayi" not in store.read_jsonl("trade_plans.jsonl")[-1], \
        "reddedilen çağrı yine de deftere onay yazdı"
    assert store.read_json("portfolio.json", {})["armed"] == [], "NO_GO planı silahlandı"
    # YASANIN KENDİSİ DE ÖLÇÜLÜR: onay damgası ELLE konsa bile NO_GO giriş kuyruğuna GİREMEZ.
    assert loop.girise_uygun(_plan(verdict="NO_GO",
                                   operator_onayi={"ts": "2026-08-05T12:00:00+00:00"})) is False


def test_seansi_gecmis_plan_onaylanamaz(seeded, client):
    store.write_jsonl("trade_plans.jsonl", [_plan("P-2026-08-04-CCC", date="2026-08-04")])
    _kitap(last_date="2026-08-05")            # kitap ilerledi → plan tek-seans geçerliliğini yitirdi
    r = client.post("/api/plan/P-2026-08-04-CCC/onayla", headers=HDR)
    assert r.status_code == 409 and "seansı geçmiş" in r.json()["detail"]
    assert store.read_json("portfolio.json", {})["armed"] == []


def test_go_ve_bilinmeyen_hukum_bu_uctan_gecmez(seeded, client):
    """GO zaten giriş kuyruğunda; onay ucu ona dokunmaz (ikinci bir silahlanma yolu değil)."""
    store.write_jsonl("trade_plans.jsonl", [_plan("P-2026-08-05-DDD", verdict="GO")])
    _kitap()
    r = client.post("/api/plan/P-2026-08-05-DDD/onayla", headers=HDR)
    assert r.status_code == 409 and "REVIEW" in r.json()["detail"]


def test_halt_aktifken_onay_verilmez(seeded, client, monkeypatch):
    """Sessiz bir 'onaylandı' yerine dürüst bir ret: HALT'ta silahlanan plan sonraki turda düşerdi."""
    store.write_jsonl("trade_plans.jsonl", [_plan()])
    _kitap()
    monkeypatch.setattr(health, "halted", lambda: True)
    r = client.post("/api/plan/P-2026-08-05-AAA/onayla", headers=HDR)
    assert r.status_code == 409 and "HALT" in r.json()["detail"]
    assert store.read_json("portfolio.json", {})["armed"] == []


def test_bilinmeyen_plan_404(seeded, client):
    store.write_jsonl("trade_plans.jsonl", [_plan()])
    _kitap()
    assert client.post("/api/plan/P-YOK/onayla", headers=HDR).status_code == 404


def test_slot_tavani_ve_acik_pozisyon_kapisi(seeded, client):
    """Onay kapıyı GEVŞETEMEZ: tavan dolu ya da isim zaten defterdeyse ret + sebep."""
    store.write_jsonl("trade_plans.jsonl", [_plan()])
    _kitap(positions={"AAA": {"qty": 10}})
    r = client.post("/api/plan/P-2026-08-05-AAA/onayla", headers=HDR)
    assert r.status_code == 409 and "açık pozisyon" in r.json()["detail"]

    tavan = int(config.goal()["limits"]["max_open_positions"])
    _kitap(armed=[{"id": f"P-x{i}", "ticker": f"X{i}"} for i in range(tavan)])
    r2 = client.post("/api/plan/P-2026-08-05-AAA/onayla", headers=HDR)
    assert r2.status_code == 409 and "slot yok" in r2.json()["detail"]


# =================================================================================================
# 3) YETKİ — token'sız çağrı 401 (ve doğru token pozitif kontrol)
# =================================================================================================
def test_tokensiz_cagri_401(seeded, client):
    store.write_jsonl("trade_plans.jsonl", [_plan()])
    _kitap()
    assert client.post("/api/plan/P-2026-08-05-AAA/onayla").status_code == 401
    assert store.read_json("portfolio.json", {})["armed"] == [], "yetkisiz çağrı defteri kıpırdattı"
    # POZİTİF KONTROL: aynı istek doğru token'la geçer — 401'ler "her şey kırık" değil.
    assert client.post("/api/plan/P-2026-08-05-AAA/onayla", headers=HDR).status_code == 200


# =================================================================================================
# 4) TEK KOŞUL NOKTASI — döngünün silahlanma dalları `girise_uygun`dan geçer
# =================================================================================================
def test_kesif_dallari_tek_kosul_noktasindan_gecer():
    """AST: her `explore_pool.append(...)` çağrısının EN YAKIN saran koşulu `girise_uygun(...)`
    olmalı. Elle `verdict == "GO"` yazan ikinci bir dal belirirse yasa sessizce ikiye bölünürdü."""
    tree = ast.parse(inspect.getsource(loop.daily_cycle))
    ebeveyn = {c: n for n in ast.walk(tree) for c in ast.iter_child_nodes(n)}
    ekler = [c for c in ast.walk(tree)
             if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
             and c.func.attr == "append"
             and isinstance(c.func.value, ast.Name) and c.func.value.id == "explore_pool"]
    assert len(ekler) >= 2, "keşif havuzunun dalları kayboldu — test artık bir şey ölçmüyor"
    for c in ekler:
        n, kosul = ebeveyn.get(c), None
        while n is not None:
            if isinstance(n, ast.If):
                kosul = n.test
                break
            n = ebeveyn.get(n)
        assert isinstance(kosul, ast.Call) and isinstance(kosul.func, ast.Name) \
            and kosul.func.id == "girise_uygun", \
            f"satır {c.lineno}: keşif dalı `girise_uygun` dışında silahlanıyor (ikinci yasa)"


def test_girise_uygun_yasasi():
    assert loop.girise_uygun(_plan(verdict="GO")) is True
    assert loop.girise_uygun(_plan(verdict="REVIEW")) is False
    assert loop.girise_uygun(_plan(verdict="REVIEW",
                                   operator_onayi={"ts": "2026-08-05T10:00:00+00:00"})) is True
    assert loop.girise_uygun(_plan(verdict="REVIEW", operator_onayi={})) is False, \
        "damgasız (boş) onay bloğu onay sayıldı"
    assert loop.girise_uygun(_plan(verdict="NO_GO",
                                   operator_onayi={"ts": "2026-08-05T10:00:00+00:00"})) is False


# =================================================================================================
# 5) DÖNGÜ DAVRANIŞI — onay yeniden üretimde TAŞINIR ve keşif modunda SİLAHLANDIRIR
# =================================================================================================
# EVREN TARİFİ test_kovab_ikimotor_v164'ten: ham `make_bars` barları veri kapısında
# 'ohlc_inconsistent' ile düşer; iki motoru da GERÇEKTEN silahlandıran tek tarif budur.
N_BARS, WINDOW = 300, 12
TICKERS = {"AAPL": 9, "JPM": 10, "UNH": 27, "CAT": 34, "XOM": 63, "KO": 5, "NKE": 6}


def _valid_ohlc(df):
    df = df.copy()
    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)
    return df


def _evren(breakout_at=N_BARS - 6):
    idx = _valid_ohlc(make_bars(N_BARS, seed=7, trend=0.0006))
    bars = {t: _valid_ohlc(make_bars(N_BARS, seed=s, breakout_at=breakout_at))
            for t, s in TICKERS.items()}
    return bars, idx


def _kesif_modu(monkeypatch):
    """Bütçe %0 → `explore_mode`; kapı hükmü REVIEW → eski kodda HİÇBİR plan silahlanamaz."""
    _asil = loop.regime_mod.build_regime_json
    monkeypatch.setattr(loop.regime_mod, "build_regime_json",
                        lambda *a, **k: {**_asil(*a, **k), "regime": "chop",
                                         "exposure_budget_pct": 0.0})
    monkeypatch.setattr(loop.guard, "classify_gate",
                        lambda *a, **k: ("REVIEW", ["skor alt bantta"]))


def test_kesif_modunda_onaysiz_review_silahlanmaz_onayli_silahlanir(seeded, monkeypatch):
    bars, idx = _evren()
    _kesif_modu(monkeypatch)
    for d in [str(x.date()) for x in idx["date"].iloc[-WINDOW:]]:
        loop.daily_cycle(bars, idx, on_date=d)

    planlar = [p for p in store.read_jsonl("trade_plans.jsonl") if p.get("gate_verdict") == "REVIEW"]
    assert planlar, "fikstür plan üretmedi — test bir şey kanıtlamıyor"
    assert store.read_json("portfolio.json", {}).get("armed") == [], \
        "ONAYSIZ REVIEW keşif modunda silahlandı — çıta gevşedi"

    d_hedef = planlar[-1]["date"]
    hedef = planlar[-1]["id"]
    seansin_review = {p["id"] for p in planlar if p["date"] == d_hedef}

    # OPERATÖR ONAYI (uç noktanın yazdığı damganın aynısı) + döngü aynı seansı YENİDEN işler:
    # `merge_dated_jsonl` o tarihin satırlarını yeniden yazar; onay TAŞINMALI ve plan silahlanmalı.
    def _damgala(rows):
        for r in rows:
            if r.get("id") == hedef:
                r["operator_onayi"] = {"ts": "2026-08-05T10:00:00+00:00", "kanal": "pano"}
        return True

    store.update_jsonl("trade_plans.jsonl", _damgala)
    store.update_json("portfolio.json", lambda doc: doc.update({"last_date": None}) or True, {})

    loop.daily_cycle(bars, idx, on_date=d_hedef)
    yeni = [p for p in store.read_jsonl("trade_plans.jsonl") if p.get("id") == hedef]
    assert yeni and yeni[-1].get("operator_onayi", {}).get("ts"), \
        "yeniden üretim operatörün onayını SİLDİ (merge_dated_jsonl sınıfı)"
    kitap = store.read_json("portfolio.json", {})
    assert hedef in [a.get("id") for a in (kitap.get("armed") or [])], \
        "onaylı REVIEW planı keşif modunda hâlâ silahlanmıyor — düğme yine hiçbir şey yapmıyor"
    assert seansin_review <= set(kitap.get("entry_law") or {}), \
        "bu seansın REVIEW planlarının E1 icra yasası atıldı — sonradan onaylanan plan " \
        "atr/ref_price'sız dolardı (aynı planda iki farklı limit tavanı)"


# =================================================================================================
# 6) SON DÖNGÜ PANELİ — olay penceresinden BAĞIMSIZ
# =================================================================================================
def test_gercek_dongu_kaydi_uctan_okunur(seeded, client):
    """UÇTAN UCA: gerçek bir `daily_cycle` turu koşar, uç onun KENDİ kaydını döndürür (fikstür değil)."""
    bars, idx = _evren()
    d = str(idx["date"].iloc[-1].date())
    ozet = loop.daily_cycle(bars, idx, on_date=d)
    sd = client.get("/api/today", headers=HDR).json()["son_dongu"]
    assert sd["var"] is True and sd["date"] == d
    assert sd["candidates"] == ozet["candidates"] and sd["plans"] == ozet["plans"], \
        "uçtaki özet döngünün kendi sayılarıyla ayrışıyor"
    assert isinstance(sd["yas_saat"], float), "kaç saat önce olduğu ölçülmedi"


def test_api_son_dongu_olay_penceresinden_bagimsiz(seeded, client):
    """ASIL KUSUR: döngü olayı 80'lik pencereden taşınca kart 'ölçülemedi' diyordu. Uç, defterin
    KUYRUĞUNDAN okur — araya kaç yüz olay girdiğinden BAĞIMSIZ."""
    store.append_jsonl("events.jsonl", {"ts": "2026-08-05T21:05:00+00:00", "level": "info",
                                        "event": "daily_cycle", "date": "2026-08-05",
                                        "regime": "chop", "candidates": 9, "plans": 2, "armed": 0})
    for i in range(300):                       # olayı 80'lik pencerenin ÇOK dışına iter
        store.append_jsonl("events.jsonl", {"ts": "2026-08-05T21:06:00+00:00", "level": "info",
                                            "event": "scheduler_tick", "i": i})
    assert len(obs.recent(80)) == 80 and not any(
        e.get("event") == "daily_cycle" for e in obs.recent(80)), "pencere kurgusu tutmadı"

    sd = client.get("/api/today", headers=HDR).json()["son_dongu"]
    assert sd["var"] is True and sd["kaynak"] == "events.jsonl"
    assert sd["date"] == "2026-08-05" and sd["candidates"] == 9 and sd["plans"] == 2

    # ÖNBELLEK DEFTERİN DAMGASINA BAĞLI: yeni bir döngü kaydı DÜŞER DÜŞMEZ cevap tazelenir
    # (süreli bir önbellek burada bayat bir "dün gece" servis ederdi).
    store.append_jsonl("events.jsonl", {"ts": "2026-08-06T21:05:00+00:00", "level": "info",
                                        "event": "daily_cycle", "date": "2026-08-06",
                                        "regime": "chop", "candidates": 4, "plans": 1, "armed": 1})
    sd2 = client.get("/api/today", headers=HDR).json()["son_dongu"]
    assert sd2["date"] == "2026-08-06" and sd2["candidates"] == 4, "önbellek bayat özeti servis etti"


def test_api_son_dongu_kayit_yoksa_uydurmaz(seeded, client):
    sd = client.get("/api/today", headers=HDR).json()["son_dongu"]
    assert sd["var"] is False and sd["kaynak"] is None
    assert "ölçülemedi" in sd["neden"] and "0" not in str(sd.get("candidates", ""))


# =================================================================================================
# 7) ZİNCİR (YASA 6) — üretilen her alanın panoda bir OKUYUCUSU var
# =================================================================================================
def test_pano_zinciri_bagli():
    js = APP_JS.read_text()
    assert "planOnayla" in js and '"/api/plan/"' in js, "onay ucunun pano okuyucusu yok"
    m = js.split("const EYLEMLER = new Set([")[1].split("]);")[0]
    assert '"planOnayla"' in m, "eylem izin listesinde kayıtlı değil — düğme SESSİZCE ölü"
    assert "operator_onayi" in js, "onay rozeti panoda okunmuyor"
    assert "t.son_dongu" in js, "son döngü özeti panoda okunmuyor"
    assert 'e.event === "daily_cycle"' not in js, \
        "pano hâlâ olay penceresinde döngü olayı arıyor — kusur kapanmadı"


def test_defter_yazari_sozlesmede(seeded):
    """`trade_plans.jsonl`e yazan modüller sözleşmede beyanlıdır (loop/run/hermes). Uç noktanın
    kendi eliyle yazması 'haberi olmayan ikinci yazar' sınıfını yeniden açardı."""
    from meridian import ledgers
    assert not ledgers.writer_violations().get("trade_plans.jsonl")
    assert "api.py" not in ledgers.declared_writers().get("trade_plans.jsonl", set())

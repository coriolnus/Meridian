"""test_icra_yetkisi_v233.py — ONAY = İCRA YETKİSİ turu (İŞ-2-EOD + Faz 4b + İŞ-3), 2026-08-11.

VAKA (P-2026-08-07-VLO-exhaustion_hammer; operatör: "onayladığım bir emrin gönderilmemesi büyük
bir fiyasko"): REVIEW planı 08-08'de operatör-onaylandı → silahlı kümeye girdi; 08-10 EOD turunda
İÇ MOTOR açılış fazında doldurdu (E2 resmi_acilis 303.89 → 304.04×61) ve plan silahlı kümeden
çıktı; `mirror_submit_armed`ın P3-sonu çağrısı onu HİÇ görmedi → Alpaca'ya emir hiç gitmedi →
reconcile yalnız GENEL `split_brain` alarmı bastı. ATLAYAN SÜZGEÇ bir setup/kapı filtresi DEĞİL,
FAZ SIRASIYDI: loop.daily_cycle AÇILIŞ fazı (fill_entry → `meta["armed"] = carried`) döngü-dışı
silahlanan (onaylanan) planı tüketiyor, gönderim noktası ise KAPANIŞ fazının sonunda yaşıyordu.

BU DOSYA NEYİ ÇİVİLER:
  B0 İŞ-3a DÜRÜSTLÜK  · ayna kapalıyken onay REDDEDİLMEZ ama `icra_yolu` "broker'a GİTMEZ" der
  B1 ONAY = İCRA      · onay ANINDA tek kapıdan gerçek bracket gönderilir (dormant setup DAHİL)
  B2 DÖNGÜ KEMERİ     · iç motorun doldurduğu gönderilmemiş plan AYNI turda GEÇ gönderilir (olaylı)
  B3 NEGATİF          · silahsız+onaysız plan GÖNDERİLMEZ (mevcut davranış korunur)
  C1 4B PARİTE        · gölgenin would_submit'i ile 4b emri qty/limit/koruma BİREBİR (+E2+olay)
  C2 BAYRAK KAPALI    · INTRADAY_ARM yokken davranış bugünküyle birebir (yalnız gözlem)
  C3 İCRA-UYGUNLUK    · (silahlı setup ∧ GO) ∨ operatör-onayı; ikisi de değilse gönderim YOK
  C4 4G SÜRE          · seansı geçmiş plan gönderilmez
  C5 İDEMPOTENS       · Alpaca'da aynı coid'li emir / sembolde pozisyon → atla; ölçülemezse
                        FAIL-CLOSED; EOD yolu intraday-gönderilmişi İKİNCİ kez göndermez (dedup)
  C6 SÜPÜRÜCÜ         · dolmamış 4b girişi EOD bayat-tetik süpürmesinde temizlenir (v210 yasası)
  C7 KAPI BLOĞU       · gölge `blocked:*` derken 4b HİÇ denemez (kapı ailesi o anda yeniden ölçülür)
  D1-D4 İŞ-3b BEKÇİ   · onaylı+iç-dolmuş+broker'da-yok → ONAYLI_PLAN_GONDERILMEDI (mandallı);
                        ölçülemeyen fotoğraf alarmsız (#10'un alanı); jeton bildirim kapsamında

YÖNTEM (v220 yasası): hiçbir test ağa çıkmaz. `alpaca.py`'nin içe aktardığı `httpx` istemcisi bir KAYIT EDİCİYLE değiştirilir —
adaptörün GERÇEK gövdeleri (`account/orders/positions/submit_plan/submit_bracket/cancel_open_
entries`) koşar (v215 dersi: patch'siz gerçek broker çağrısı test-zehirler; `_TRANSPORT` sızıntısı
conftest'te kaynağa bağlı). Her iddianın yanında pozitif kontrol vardır.
"""
from __future__ import annotations

import datetime as dt
import pathlib
import shutil

import pytest
import yaml

from meridian import broker as BR
from meridian import barclock as bc
from meridian import config, health, loop, obs, store, watchdog
from meridian import intraday_cycle as ic
from meridian.adapters import alpaca
from tests.conftest import make_bars

REPO = pathlib.Path(config.__file__).resolve().parent.parent
UTC = dt.timezone.utc
RTH = dt.datetime(2026, 7, 23, 14, 46, 30, tzinfo=UTC)   # 10:46:30 ET — RTH açık (v88 ile aynı an)
FAKE_KEY = "PKICRAV233FAKEKEY0011223344"
FAKE_SECRET = "SKICRAV233FAKESECRET5566778899"


# =================================================================================================
# FİKSTÜRLER
# =================================================================================================
class _Resp:
    def __init__(self, data, status=200):
        self._d, self.status_code = data, status

    def json(self):
        return self._d

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class SahteHttpx:
    """Alpaca REST'in kayıt edici taklidi — adaptör gövdeleri GERÇEK koşar, ağ hiç açılmaz."""

    def __init__(self):
        self.posts: list = []          # gönderilen bracket gövdeleri
        self.deletes: list = []        # iptal edilen emir id'leri
        self.acik_emirler: list = []   # GET /v2/orders cevabı (status süzgeci taklit edilmez —
        self.pozisyonlar: list = []    #   testler listeyi senaryoya göre kurar)
        self.get_patlat: str | None = None   # bu parçayı içeren GET patlar (taşıma arızası taklidi)

    def get(self, url, **k):
        if self.get_patlat and self.get_patlat in url:
            raise ConnectionError("sahte ağ arızası")
        if url.endswith("/v2/account"):
            return _Resp({"equity": "100000", "status": "ACTIVE"})
        if "/v2/positions" in url:
            return _Resp([dict(p) for p in self.pozisyonlar])
        if "/v2/orders" in url:
            return _Resp([dict(o) for o in self.acik_emirler])
        if "/v2/assets/" in url:
            return _Resp({"tradable": True, "status": "active"})
        return _Resp({}, 404)

    def post(self, url, headers=None, json=None, timeout=None):
        self.posts.append(dict(json or {}))
        return _Resp({"id": f"srv-{len(self.posts)}", "status": "accepted",
                      "client_order_id": (json or {}).get("client_order_id")})

    def delete(self, url, headers=None, params=None, timeout=None):
        self.deletes.append(url.rsplit("/", 1)[-1])
        return _Resp({}, 200)


@pytest.fixture
def ayna(sandbox_state, monkeypatch):
    """Sahte kimlik + `alpaca_paper` arka ucu + httpx kayıt edicisi. Gerçek istemci hiç kurulmaz."""
    from meridian import secrets as secrets_mod
    monkeypatch.setenv("ALPACA_PAPER_KEY", FAKE_KEY)
    monkeypatch.setenv("ALPACA_PAPER_SECRET", FAKE_SECRET)
    monkeypatch.delenv("MERIDIAN_GCP_PROJECT", raising=False)
    secrets_mod.clear_cache()
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    monkeypatch.setattr(alpaca, "paper_available", lambda: True)
    fake = SahteHttpx()
    monkeypatch.setattr(alpaca, "httpx", fake)
    watchdog._ONAYLI_GONDERIM_ALARMED.clear()
    # PENCERE YASASI (EXE-009+K2): gönderim artık sabah tetik penceresine bağlı — bu dosyanın
    # çivileri GÖNDERİM MEKANİĞİNİ ölçer, pencereyi değil; saat pencere İÇİNE donar ki testler
    # koşum saatinden bağımsız kalsın (pencerenin kendi çivileri test_pencere_kaydirma_v272'de).
    bc.set_clock(lambda: RTH)
    yield sandbox_state, fake
    bc.reset_clock()
    secrets_mod.clear_cache()
    watchdog._ONAYLI_GONDERIM_ALARMED.clear()


def _seed_conf(sb, slippage_bps=None):
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(REPO / "state" / f, sb / f)
    if slippage_bps is not None:
        g = yaml.safe_load((sb / "goal.yaml").read_text())
        g["slippage_bps"] = slippage_bps
        (sb / "goal.yaml").write_text(yaml.safe_dump(g))
    config.reload_config()
    (sb / "strategy.yaml").write_text(yaml.safe_dump(config.default_strategy()))


def _events(ad: str) -> list:
    return [e for e in store.read_jsonl("events.jsonl") if e.get("event") == ad]


def _plan(pid="P-2026-08-05-AAA", *, date="2026-08-05", verdict="REVIEW",
          setup="episodic_pivot", trigger=100.0, stop=95.0, target=112.0, **ek):
    """Canlı plan satırı şekli (loop.daily_cycle üretimiyle aynı alanlar)."""
    return {"id": pid, "date": date, "ticker": pid.split("-")[-1], "side": "long",
            "entry_trigger": trigger, "stop": stop, "targets": [target], "profit_target": target,
            "size_r": 1.0, "r_multiple_expected": 2.4, "regime_at_plan": "chop", "sector": "Tech",
            "score": 71, "setup": setup, "dormant_setup": setup not in ("breakout_vcp", "pullback"),
            "strategy_version": 1, "gate_verdict": verdict,
            "gate_reasons": ["skor alt bantta"], **ek}


def _onayli(plan):
    return {**plan, loop.ONAY_ALANI: {"ts": "2026-08-08T14:00:00+00:00", "kanal": "pano"}}


def _law(pid, trigger=100.0, ref=99.5, atr=1.0):
    return {pid: {**BR.entry_order_decision(trigger, ref_price=ref, atr=atr), "pivot": None}}


def _kitap(**ek):
    doc = {"armed": [], "positions": {}, "last_date": "2026-08-05", "cash": 100_000.0,
           "peak_equity": 100_000.0, "day_start_equity": 100_000.0, "realized_pnl": 0.0, **ek}
    store.write_json("portfolio.json", doc)
    return doc


def _nabiz():
    store.write_json("heartbeat.json", {"equity": 100_000.0, "day_pnl_pct": 0.0,
                                        "ts": dt.datetime.now(UTC).isoformat(timespec="seconds")})
    store.write_json("data_quality.json", {"date": "2026-07-22", "data_halt": False})


# =================================================================================================
# B — İŞ-2-EOD: ONAY = İCRA YETKİSİ (EOD ayna yolu onaylı planı ATLAYAMAZ)
# =================================================================================================
def test_b0_ayna_kapaliyken_onay_reddedilmez_ama_sessiz_de_degil(sandbox_state):
    """İŞ-3a: icra yolu YOKKEN (broker=internal) onay yine 200 döner — ama `icra_yolu` alanı
    "broker'a GİTMEZ" cümlesini AÇIKÇA taşır ve olay defterine de düşer. Sessizlik yasak."""
    _seed_conf(sandbox_state)
    store.write_jsonl("trade_plans.jsonl", [_plan()])
    _kitap(entry_law=_law("P-2026-08-05-AAA"))
    assert config.BROKER == "internal"          # sandbox varsayılanı — icra yolu bilerek kapalı
    res = loop.operator_onay_ver("P-2026-08-05-AAA", kanal="pano")
    assert res["ok"] is True and res["silahli"] is True
    assert "GİTMEZ" in res["icra_yolu"] and "internal" in res["icra_yolu"]
    assert res["gonderim"] is None
    ev = _events("plan_operator_approved")
    assert len(ev) == 1 and "GİTMEZ" in ev[0]["icra_yolu"], "olay icra yolunu söylemiyor"


def test_b1_onay_aninda_gercek_bracket_gonderilir_dormant_setup_dahil(ayna):
    """ONAY = İCRA YETKİSİ: REVIEW + DORMANT setup (episodic_pivot — ARMED_SETUPS'ta DEĞİL) planı
    onaylanınca bracket ONAY ANINDA tek kapıdan gönderilir; dedup kümesi ve SB-1 makbuzu diske
    kilit altında yamalanır. Setup silahsızlığı onaylı planı SÜZEMEZ (kök vakanın kapanışı)."""
    sb, fake = ayna
    _seed_conf(sb)
    _nabiz()
    pid = "P-2026-08-05-AAA"
    store.write_jsonl("trade_plans.jsonl", [_plan(pid)])
    _kitap(entry_law=_law(pid))
    assert "episodic_pivot" not in __import__("meridian.strategy", fromlist=["x"]).ARMED_SETUPS

    res = loop.operator_onay_ver(pid, kanal="pano")
    assert res["ok"] is True, res
    assert res["gonderim"]["ok"] is True and res["gonderim"]["submitted"] == 1
    assert "GÖNDERİLDİ" in res["icra_yolu"] and pid in res["icra_yolu"]
    assert len(fake.posts) == 1, "bracket POST'u tam bir kez çıkmalıydı"
    b = fake.posts[0]
    assert b["client_order_id"] == pid and b["symbol"] == "AAA" and b["side"] == "buy"
    assert b["order_class"] == "bracket" and b["time_in_force"] == "gtc"       # E1-v2 yasası
    pf = store.read_json("portfolio.json", {})
    assert pid in (pf.get("alpaca_submitted") or []), "dedup kümesine kalıcılaşmadı"
    assert pid in (pf.get("size_law") or {}), "SB-1 boyut makbuzu kalıcılaşmadı"
    assert [a["id"] for a in pf["armed"]] == [pid]
    # E2 defteri: motor="ayna", kaynak="onay" satırı düştü (gönderim kayıttan okunabilir)
    e2 = [r for r in store.read_jsonl("entry_execution.jsonl")
          if r.get("plan_id") == pid and r.get("motor") == "ayna"]
    assert len(e2) == 1 and e2[0]["karar"] == "submitted" and e2[0]["kaynak"] == "onay"
    # POZİTİF KONTROL (ikinci onay): dedup — ikinci bir POST doğmaz, yanıt bunu söyler
    res2 = loop.operator_onay_ver(pid, kanal="pano")
    assert res2["ok"] is True and len(fake.posts) == 1
    assert "dedup" in res2["icra_yolu"] or "ZATEN" in res2["icra_yolu"]


def test_b2_dongu_kemeri_ic_dolum_yazan_gonderilmemis_plani_ayni_turda_gonderir(ayna):
    """VLO SENARYOSUNUN KENDİSİ (önce/sonra): onaylı-dormant plan silahlı kümede ama `alpaca_
    submitted`da İZİ YOK (onay-anı gönderimi hiç yaşanmamış — düzeltme-öncesi dünya). EOD turu:
    (1) iç motor AÇILIŞ fazında doldurur, (2) plan silahlı kümeden çıkar, (3) KEMER aynı turda
    bayat-tetik süpürmesinden SONRA tek kapıdan GEÇ gönderir + olay yazar. Düzeltme öncesinde bu
    turun sonu 'iç pozisyon var, Alpaca'da hiçbir şey yok'tu (split_brain)."""
    sb, fake = ayna
    _seed_conf(sb)
    idx = make_bars(300, seed=1, trend=0.0009)
    df = make_bars(300, seed=2)
    d_str = str(idx["date"].iloc[-1].date())
    onceki = str(idx["date"].iloc[-2].date())
    acilis = float(df["open"].iloc[-1])
    pid = f"P-{onceki}-AAA"
    plan = _onayli(_plan(pid, date=onceki, trigger=round(acilis * 0.995, 2),
                         stop=round(acilis * 0.90, 2), target=round(acilis * 1.2, 2)))
    _kitap(last_date=onceki, armed=[plan],
           entry_law=_law(pid, trigger=plan["entry_trigger"],
                          ref=plan["entry_trigger"] * 0.995, atr=1.0))
    store.write_jsonl("trade_plans.jsonl", [dict(plan)])

    out = loop.daily_cycle({"AAA": df, "BBB": make_bars(300, seed=3)}, idx, on_date=d_str)
    assert out.get("status") == "ok", out

    pf = store.read_json("portfolio.json", {})
    assert "AAA" in (pf.get("positions") or {}), "iç motor dolumu yazmadı — fikstür kırık"
    coids = [p.get("client_order_id") for p in fake.posts]
    assert coids.count(pid) == 1, f"geç-gönderim kemeri çalışmadı ya da çift gönderdi: {coids}"
    assert pid in (pf.get("alpaca_submitted") or []), "geç gönderim dedup kümesine kalıcılaşmadı"
    ev = _events("mirror_gec_gonderim")
    assert len(ev) == 1 and pid in (ev[0].get("plan_ids") or []), "kemer olay defterine düşmedi"
    e2 = [r for r in store.read_jsonl("entry_execution.jsonl") if r.get("plan_id") == pid]
    assert any(r.get("motor") == "ic" and r.get("karar") == "fill" for r in e2), "iç E2 satırı yok"
    assert any(r.get("motor") == "ayna" and r.get("karar") == "submitted"
               and r.get("kaynak") == "loop_gec_gonderim" for r in e2), "ayna E2 satırı yok"


def test_b3_silahsiz_ve_onaysiz_plan_gonderilmez(ayna):
    """NEGATİF (mevcut davranış korunur): trade_plans'ta duran ama silahlanmamış+onaysız REVIEW
    planı ne onay-anı yolundan ne kemerden geçer — hiçbir POST onun coid'ini taşımaz."""
    sb, fake = ayna
    _seed_conf(sb)
    idx = make_bars(300, seed=1, trend=0.0009)
    d_str = str(idx["date"].iloc[-1].date())
    onceki = str(idx["date"].iloc[-2].date())
    yetim = _plan(f"P-{onceki}-CCC", date=onceki)          # onaysız REVIEW, armed'a GİRMEMİŞ
    store.write_jsonl("trade_plans.jsonl", [yetim])
    _kitap(last_date=onceki)
    out = loop.daily_cycle({"AAA": make_bars(300, seed=2), "BBB": make_bars(300, seed=3)},
                           idx, on_date=d_str)
    assert out.get("status") == "ok", out
    assert all(p.get("client_order_id") != yetim["id"] for p in fake.posts), \
        "onaysız+silahsız plan aynaya gönderildi — yetki sınırı delindi"


# =================================================================================================
# C — İŞ-2: FAZ 4B (intraday gerçek gönderim)
# =================================================================================================
def _bar(t, o, h, c):
    return {"t": t, "o": o, "h": h, "l": min(o, c) * 0.998, "c": c, "v": 5000}


@pytest.fixture
def dortb(ayna, monkeypatch):
    """4b sahnesi: RTH saati + silahlı GO planı + entry_law + sağlıklı kapı girdileri.
    slippage_bps=0 (BEYANLI): gölge kopya-broker dolumu slipajlı fiyattan, ayna emri tetik
    fiyatından boyutlar — bu fark 4b'nin değil E1/iki-motor tasarımının farkıdır (audit #50);
    parite iddiası friksiyon sıfırken bakılır ki ölçülen şey 4b'nin kendisi olsun."""
    sb, fake = ayna
    _seed_conf(sb, slippage_bps=0)
    ic._CONSUMER = None
    from meridian import intraday_shadow as gol
    gol.reset_dedup()
    bc.set_clock(lambda: RTH)
    # SAHNE İZOLASYONU (EXE-009+K2): sabah kancası (`_pencere_gonderim`) pencere açılınca
    # silahlı-gönderilmemiş planı EOD yetkisiyle KENDİSİ gönderir — bu meşru davranış, 4b
    # çivilerinin sahnesini (silahlı ama henüz gönderilmemiş plan + tetik kesişimi) bozar:
    # emri kanca göndermiş olur ve ölçülen şey 4b olmaktan çıkar. Kanca burada kapatılır;
    # kendi çivileri test_pencere_kaydirma_v272'de.
    monkeypatch.setattr(ic.IntradayConsumer, "_pencere_gonderim", lambda self, pf: None)
    _nabiz()
    pid = "P-2026-07-22-AAPL"
    plan = _plan(pid, date="2026-07-22", verdict="GO", setup="breakout_vcp",
                 trigger=100.0, stop=95.0, target=112.0)
    plan["dormant_setup"] = False
    _kitap(last_date="2026-07-22", armed=[plan], entry_law=_law(pid))
    monkeypatch.setattr(ic.hotstate, "read_bars",
                        lambda tk, n: [_bar("2026-07-23T14:45:00Z", 100.0, 101.0, 100.5)])
    health.set_intraday_arm(True)
    yield sb, fake, pid, plan
    health.set_intraday_arm(False)
    bc.reset_clock()
    ic._CONSUMER = None
    gol.reset_dedup()


def test_c1_golge_ile_4b_emri_birebir_parite(dortb):
    """(e) EŞLİK: aynı girdide gölgenin would_submit satırı ile gönderilen bracket'ın qty/limit/
    koruma bacakları BİREBİR; gölge kaydı KALIR; `intraday_4b_submitted` olayı coid+qty+fiyat taşır."""
    sb, fake, pid, plan = dortb
    ic.consumer().on_barfeed_event({"syms": "AAPL"})

    golge = store.read_jsonl("intraday_shadow_orders.jsonl")
    assert len(golge) == 1 and golge[0]["status"] == "would_submit", golge
    assert "kol" not in golge[0], "silahlı kolun şemasına alan sızdı (kart kill#3)"
    assert len(fake.posts) == 1, "4b gerçek bracket göndermedi"
    b = fake.posts[0]
    assert b["client_order_id"] == pid and b["symbol"] == "AAPL"
    assert int(b["qty"]) == int(golge[0]["qty"]), "qty gölgeyle ayrıştı"
    assert float(b["limit_price"]) == round(float(golge[0]["limit"]), 2), "limit gölgeyle ayrıştı"
    assert float(b["take_profit"]["limit_price"]) == round(float(golge[0]["target"]), 2)
    assert float(b["stop_loss"]["stop_price"]) == round(float(golge[0]["stop"]), 2)
    assert b["time_in_force"] == "gtc" and b["type"] == "stop_limit"          # E1-v2
    ev = _events("intraday_4b_submitted")
    assert len(ev) == 1 and ev[0]["coid"] == pid and ev[0]["qty"] == int(b["qty"])
    assert ic.consumer().submitted_4b == 1 and ic.health()["submitted_4b"] == 1
    e2 = [r for r in store.read_jsonl("entry_execution.jsonl")
          if r.get("plan_id") == pid and r.get("motor") == "ayna"]
    assert len(e2) == 1 and e2[0]["kaynak"] == "intraday_4b"
    pf = store.read_json("portfolio.json", {})
    assert pid in (pf.get("alpaca_submitted") or []), "4b gönderimi dedup kümesine kalıcılaşmadı"
    # AYNI SEANSTA İKİNCİ TETİK OLAYI: gölge dedup satır yazmaz → 4b de yeniden denemez
    ic.consumer().on_barfeed_event({"syms": "AAPL"})
    assert len(fake.posts) == 1, "aynı plan aynı seansta ikinci kez gönderildi"


def test_c2_bayrak_kapaliyken_yalniz_gozlem(dortb):
    """INTRADAY_ARM yokken davranış BUGÜNKÜyle birebir: gözlem+gölge yazılır, emir çıkmaz."""
    sb, fake, pid, plan = dortb
    health.set_intraday_arm(False)
    ic.consumer().on_barfeed_event({"syms": "AAPL"})
    assert len(store.read_jsonl("intraday_decisions.jsonl")) == 1
    assert len(store.read_jsonl("intraday_shadow_orders.jsonl")) == 1
    assert fake.posts == [], "bayrak kapalıyken emir çıktı — yetki ihlali"
    assert not [e for e in store.read_jsonl("events.jsonl")
                if str(e.get("event", "")).startswith("intraday_4b")]
    assert ic.consumer().submitted_4b == 0


def test_c3_icra_uygunluk_suzgeci(dortb, monkeypatch):
    """(b): onaysız REVIEW → gönderilmez (olaylı); GO+dormant keşif sondası → gönderilmez;
    POZİTİF KONTROL: operatör-onaylı REVIEW (dormant setup bile olsa) → gönderilir.

    Vaka başına AYRI plan_id: gölge tekilleştirmesi DİSKTEN yüklenir (plan_id, seans) — aynı id
    ikinci vakada gölge satırı üretmez ve 4b hiç denenmezdi (ölçülen şey süzgeç olmazdı)."""
    sb, fake, pid, plan = dortb
    from meridian import intraday_shadow as gol

    def _vaka(pl):
        gol.reset_dedup()
        ic._CONSUMER = None
        _kitap(last_date="2026-07-22", armed=[pl], entry_law=_law(pl["id"]))
        ic.consumer().on_barfeed_event({"syms": "AAPL"})

    # 1) onaysız REVIEW
    _vaka({**plan, "id": f"{pid}-k1", "gate_verdict": "REVIEW"})
    assert fake.posts == [] and len(_events("intraday_4b_uygun_degil")) == 1
    # 2) GO ama DORMANT setup (keşif sondası) — onay yok
    _vaka({**plan, "id": f"{pid}-k2", "setup": "episodic_pivot", "exploration": True})
    assert fake.posts == [] and len(_events("intraday_4b_uygun_degil")) == 2
    # 3) POZİTİF: onaylı REVIEW + dormant setup → GÖNDERİLİR (onay = icra yetkisi)
    _vaka(_onayli({**plan, "id": f"{pid}-k3", "gate_verdict": "REVIEW",
                   "setup": "episodic_pivot"}))
    assert len(fake.posts) == 1 and fake.posts[0]["client_order_id"] == f"{pid}-k3"


def test_c4_suresi_dolmus_plan_gonderilmez(dortb):
    """(4G): plan tarihi kitabın işlediği son seanstan ESKİYSE seviyeler bayattır — gönderim yok."""
    sb, fake, pid, plan = dortb
    eski = {**plan, "date": "2026-07-20"}
    _kitap(last_date="2026-07-22", armed=[eski], entry_law=_law(pid))
    ic.consumer().on_barfeed_event({"syms": "AAPL"})
    assert fake.posts == [] and len(_events("intraday_4b_suresi_dolmus")) == 1
    assert len(store.read_jsonl("intraday_shadow_orders.jsonl")) == 1   # gözlem/gölge KALIR


def test_c5_idempotens_uc_kemer(dortb, monkeypatch):
    """(c) ÇİFT-GÖNDERİM YASAK: aynı coid'li açık emir → atla; sembolde pozisyon → atla;
    dedup ÖLÇÜLEMEZSE (taşıma arızası) FAIL-CLOSED atla; EOD yolu intraday-gönderilmişi dedup'lar."""
    sb, fake, pid, plan = dortb
    from meridian import intraday_shadow as gol

    def _vaka(pl):
        gol.reset_dedup()
        ic._CONSUMER = None
        _kitap(last_date="2026-07-22", armed=[pl], entry_law=_law(pl["id"]))
        ic.consumer().on_barfeed_event({"syms": "AAPL"})

    # 1) aynı coid'li açık emir
    p1 = {**plan, "id": f"{pid}-i1"}
    fake.acik_emirler = [{"id": "x1", "client_order_id": p1["id"], "symbol": "AAPL",
                          "status": "new", "filled_qty": "0", "side": "buy", "legs": []}]
    _vaka(p1)
    assert fake.posts == [] and len(_events("intraday_4b_dedup_emir")) == 1
    # 2) sembolde pozisyon
    fake.acik_emirler = []
    fake.pozisyonlar = [{"symbol": "AAPL", "qty": "10"}]
    _vaka({**plan, "id": f"{pid}-i2"})
    assert fake.posts == [] and len(_events("intraday_4b_dedup_pozisyon")) == 1
    # 3) taşıma arızası → FAIL-CLOSED
    fake.pozisyonlar = []
    fake.get_patlat = "/v2/orders"
    _vaka({**plan, "id": f"{pid}-i3"})
    assert fake.posts == [] and len(_events("intraday_4b_dedup_olculemedi")) >= 1
    # 4) POZİTİF + EOD-dedup: arıza kalkınca gönderilir; ardından EOD tek kapısı AYNI planı
    #    ikinci kez GÖNDERMEZ (alpaca_submitted dedup'ı — plan silahlı kümede durmaya devam eder)
    fake.get_patlat = None
    _vaka({**plan, "id": f"{pid}-i4"})
    assert len(fake.posts) == 1 and fake.posts[0]["client_order_id"] == f"{pid}-i4"
    res = loop.mirror_submit_ve_kalicilastir(source="pano")
    assert len(fake.posts) == 1, "EOD yolu intraday-gönderilmiş planı İKİNCİ kez gönderdi"
    assert any(r.get("dedup") for r in res.get("results") or []), "dedup sonucu görünmüyor"


def test_c6_dolmamis_4b_girisi_eod_supurmesinde_temizlenir(dortb):
    """(d): 4b emri dolmadan kaldıysa günlük bayat-tetik süpürmesi onu keser (v210 yasası);
    dolmuş parent'ın koruma bacakları KESİLMEZ (v220 kemerleri — pozitif kontrol aynı listede)."""
    sb, fake, pid, plan = dortb
    ic.consumer().on_barfeed_event({"syms": "AAPL"})
    assert len(fake.posts) == 1
    fake.acik_emirler = [
        {"id": "id-4b", "client_order_id": pid, "symbol": "AAPL", "status": "new",
         "filled_qty": "0", "side": "buy", "legs": []},                       # dolmamış 4b girişi
        {"id": "id-dolu", "client_order_id": "P-2026-07-21-NVDA", "symbol": "NVDA",
         "status": "filled", "filled_qty": "40", "side": "buy",
         "legs": [{"id": "leg-sl", "type": "stop", "status": "held", "side": "sell"}]}]
    res = alpaca.cancel_open_entries()
    assert [c["coid"] for c in res["cancelled"]] == [pid], "4b girişi süpürülmedi ya da fazlası gitti"
    assert "id-4b" in fake.deletes and "leg-sl" not in fake.deletes, "koruma bacağına dokunuldu"


def test_c7_kapi_blokluyken_4b_hic_denemez(dortb):
    """(a) kapılar o ANDA yeniden değerlendirilir: devre kesici tetikliyken gölge `blocked:breaker`
    yazar ve 4b gönderim aşamasına HİÇ inmez (POST yok, 4b olayı yok — gölge satırı sebep taşır)."""
    sb, fake, pid, plan = dortb
    store.write_json("heartbeat.json", {"equity": 100_000.0, "day_pnl_pct": -0.10,
                                        "ts": dt.datetime.now(UTC).isoformat(timespec="seconds")})
    ic.consumer().on_barfeed_event({"syms": "AAPL"})
    golge = store.read_jsonl("intraday_shadow_orders.jsonl")
    assert len(golge) == 1 and golge[0]["status"] == "blocked:breaker"
    assert fake.posts == [] and not [e for e in store.read_jsonl("events.jsonl")
                                     if str(e.get("event", "")).startswith("intraday_4b")]


# =================================================================================================
# D — İŞ-3b: ONAYLI_PLAN_GONDERILMEDI bekçisi
# =================================================================================================
def _bekci_sahnesi(monkeypatch, *, missing=("VLO",), rc_date="2026-08-10", onayli=True):
    monkeypatch.setattr(config, "BROKER", "alpaca_paper")
    pid = "P-2026-08-07-VLO-exhaustion_hammer"
    satir = _plan(pid, date="2026-08-07", setup="exhaustion_hammer")
    satir["ticker"] = "VLO"
    if onayli:
        satir = _onayli(satir)
    store.write_jsonl("trade_plans.jsonl", [satir])
    store.write_json("portfolio.json", {"last_date": "2026-08-10", "alpaca_submitted": [],
                                        "positions": {"VLO": {"plan_id": pid, "qty": 61}}})
    store.write_json("broker_reconcile.json", {"date": rc_date, "checked": True, "api_ok": True,
                                               "positions": {"missing_on_alpaca": list(missing)}})
    return pid


def test_d1_bekci_onayli_dolmus_ama_brokerda_olmayan_plani_alarmlar(sandbox_state, monkeypatch):
    pid = _bekci_sahnesi(monkeypatch)
    watchdog._ONAYLI_GONDERIM_ALARMED.clear()
    rep = watchdog.check_onayli_gonderim_and_alarm()
    assert rep["ok"] is False and rep["kontrol_edilen"] == 1
    assert rep["ihlaller"][0] == {"ticker": "VLO", "plan_id": pid, "gonderim_izi": False,
                                  "onay_ts": "2026-08-08T14:00:00+00:00"}
    alarmlar = [e for e in store.read_jsonl("events.jsonl")
                if e.get("alarm") == "ONAYLI_PLAN_GONDERILMEDI"]
    assert len(alarmlar) == 1 and alarmlar[0]["plan_id"] == pid
    # MANDAL: ikinci geçiş aynı ihlali İKİNCİ kez alarmlamaz
    watchdog.check_onayli_gonderim_and_alarm()
    alarmlar2 = [e for e in store.read_jsonl("events.jsonl")
                 if e.get("alarm") == "ONAYLI_PLAN_GONDERILMEDI"]
    assert len(alarmlar2) == 1, "mandal çalışmıyor — her poll'da alarm seli"


def test_d2_bayat_fotograf_olculemedi_ve_alarmsiz(sandbox_state, monkeypatch):
    """Dolum-sonrası İLK reconcile henüz koşmadıysa hüküm YOK (ok=None) ve alarm da yok —
    fotoğraf bayatlığının sahibi #10 (çift-duyuru yasağı)."""
    _bekci_sahnesi(monkeypatch, rc_date="2026-08-07")
    watchdog._ONAYLI_GONDERIM_ALARMED.clear()
    rep = watchdog.check_onayli_gonderim_and_alarm()
    assert rep["ok"] is None and "gerisinde" in rep["neden"]
    assert not [e for e in store.read_jsonl("events.jsonl")
                if e.get("alarm") == "ONAYLI_PLAN_GONDERILMEDI"]


def test_d3_onaysiz_plan_ve_kapsam_disi_sessiz(sandbox_state, monkeypatch):
    """Onaysız plan bekçinin konusu değil (payda 0); broker=internal ise soru kapsam dışı."""
    _bekci_sahnesi(monkeypatch, onayli=False)
    rep = watchdog.onayli_gonderim_report()
    assert rep["ok"] is True and rep["kontrol_edilen"] == 0 and rep["ihlaller"] == []
    monkeypatch.setattr(config, "BROKER", "internal")
    rep2 = watchdog.onayli_gonderim_report()
    assert rep2["kapsam_disi"] is True and rep2["ok"] is None


def test_d4_jeton_bildirim_kapsaminda_ve_ayri(sandbox_state):
    """Yeni jeton NOTIFY_TOKENS'a kendiliğinden girer (türetme, el listesi değil) ve MIRROR_DRIFT
    ile AYNI jeton değildir (jeton-başına susturma penceresi — obs.py'deki gerekçe)."""
    assert obs.ALARM_ONAYLI_PLAN_GONDERILMEDI == "ONAYLI_PLAN_GONDERILMEDI"
    assert obs.ALARM_ONAYLI_PLAN_GONDERILMEDI in obs.NOTIFY_TOKENS
    assert obs.ALARM_ONAYLI_PLAN_GONDERILMEDI != obs.ALARM_MIRROR_DRIFT

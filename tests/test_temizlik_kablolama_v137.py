"""v137 — TEMİZLİK + KABLOLAMA TURU: ölü mekanizma avının kapanışı.

Hedef sözleşmesi md.1: "Repodaki her mekanizma ya bir üretim kadansına kablolu, ya geri-alınabilirlik
notuyla emekli, ya da adı+gerekçesiyle operatör kalemi olarak belgeli." Bu dosya o üç hâlin
ÜÇÜNÜ DE ölçer — çünkü üçünün de sessizce bozulma yolu var:

  A) EMEKLİLİK  — yarım emeklilik en kötü hâldir: ad kalır, çağıran kalabilir, testler yeşil kalır.
  B) KABLOLAMA  — her kablolama üç yasaya çivilenir: TETİK (koşul oluşunca kendi kendine koşar),
                  KISILMA (bütçe/damga altında kendini kısar ve NEDENİ adıyla yazılır),
                  GERİYE-UYUM (eski durum dosyaları ve eski alan adları kırılmaz).
  D) OPERATÖR   — "kimse çağırmıyor" ile "operatör çağırıyor" ayrı şeylerdir; ikincisinin KANITI
                  koda ve ROADMAP'e yazılmış olmalı, yoksa bir sonraki av onu yeniden öldürür.

BU TURUN EN BÜYÜK RİSKİ ve neden bu kadar test var: bir kadans eklemek, onu ÇALIŞIR sanmakla aynı
şey değil. Öğrenme turunun `stale_sinks` dersi buydu — beyan edilmiş bir okuyucu, ÇAĞRILMAYAN bir
okuyucuydu. Bu yüzden aşağıdaki testler kadansın VAR olduğunu değil, KOŞTUĞUNU ve İKİNCİ KEZ
KOŞMADIĞINI ölçer.
"""
from __future__ import annotations

import datetime as dt

import pytest

from meridian import store


@pytest.fixture(autouse=True)
def _reset_scheduler_state():
    """`scheduler._state` MODÜL GLOBALİDİR ve testler arası taşınır. Taşınırsa bir test kendi
    kurmadığı bir damgayla "kadans koşmadı" görür ve YEŞİL kalır — ölçülen şey dedektör değil,
    testlerin sırası olur (v136'nın aynı dersi, yeni damgalar: y4_session / validation_week)."""
    from meridian import scheduler
    onceki = dict(scheduler._state)
    yield
    scheduler._state.clear()
    scheduler._state.update(onceki)


# ==================================================================================================
# A) EMEKLİLİKLER — "gerçekten yok" + geri-al notu duruyor
# ==================================================================================================
EMEKLILER = [
    ("meridian.adapters.alpaca", "paper_client"),
    ("meridian.adapters.fmp", "income_statement"),
    ("meridian.adapters.fmp", "search_name"),
    ("meridian.adapters.fmp", "stock_list"),
    ("meridian.adapters.macro", "snapshot"),
    ("meridian.adapters.macro", "status"),
    ("meridian.adapters.news", "stock_news"),
    ("meridian.adapters.news", "status"),
    ("meridian.regime", "_slice"),
    ("meridian.shadowlaw", "score_eski_yasa"),
    ("meridian.notify", "data_quality"),
]


@pytest.mark.parametrize("modul,ad", EMEKLILER)
def test_emekli_adlar_gercekten_yok(modul, ad):
    """Yarım emeklilik yasağı. Ad dururken 'emekli ettik' demek, ölü kodu canlı göstermektir."""
    mod = __import__(modul, fromlist=["_"])
    assert not hasattr(mod, ad), f"{modul}.{ad} hâlâ var — emeklilik yarım kalmış"


def test_paper_broker_open_risk_dollars_yok():
    from meridian.broker import PaperBroker
    assert not hasattr(PaperBroker, "open_risk_dollars")


def test_her_emeklilik_geri_al_notu_birakti():
    """GERİ-ALINABİLİRLİK ŞARTI: silinen gövde, silindiği yerin en yakınında YAZILI olmalı. Not
    olmadan emeklilik bir silmedir ve bir yıl sonra kimse neyin neden gittiğini bilemez."""
    import pathlib
    kok = pathlib.Path(__file__).resolve().parent.parent / "meridian"
    hedefler = {"adapters/alpaca.py": "paper_client", "adapters/fmp.py": "income_statement",
                "broker.py": "open_risk_dollars", "regime.py": "_slice",
                "shadowlaw.py": "score_eski_yasa", "notify.py": "data_quality"}
    for rel, ad in hedefler.items():
        src = (kok / rel).read_text()
        assert "ÇIKARILDI 2026-07-30" in src, f"{rel}: emeklilik damgası yok"
        assert "GERİ-AL" in src, f"{rel}: geri-al notu yok"
        assert "ÇAĞIRAN TARAMASI" in src, f"{rel}: emekliliğin KANITI yazılmamış"
        assert ad in src, f"{rel}: hangi adın emekli edildiği yazılmamış"


def test_alpaca_client_korundu():
    """`_client` EMEKLİ EDİLMEDİ ve edilmemeli: `live_client`ın tek dayanağı odur ve o yol
    gerçek-para kapısıdır (operatör kalemi). Yanlışlıkla temizlenirse canlı yol import-time patlar."""
    from meridian.adapters import alpaca
    assert hasattr(alpaca, "_client") and hasattr(alpaca, "live_client")
    assert hasattr(alpaca, "live_guard")


# ==================================================================================================
# D) OPERATÖR KALEMLERİ — çürütülmüş av adayları
# ==================================================================================================
def test_supervised_bayraginin_gercek_bir_kurucusu_var():
    """AV ADAYI ÇÜRÜTÜLDÜ: `MERIDIAN_SUPERVISED` ölü değil — `ops/com.meridian.agent.plist` onu
    kuruyor. Kanıt KODLA doğrulanır: plist dosyası ortadan kalkarsa bayrak GERÇEKTEN ölür ve o gün
    bu test kırılıp kararı yeniden aldırır (bugünkü gerekçenin sessizce bayatlamasını engeller)."""
    import pathlib
    kok = pathlib.Path(__file__).resolve().parent.parent
    plist = (kok / "ops" / "com.meridian.agent.plist").read_text()
    assert "MERIDIAN_SUPERVISED" in plist, \
        "bayrağın tek kurucusu kayboldu — artık GERÇEKTEN ölü, emeklilik kararı yenilenmeli"
    api_src = (kok / "meridian" / "api.py").read_text()
    assert "EMEKLİ EDİLMEDİ — ÖLÜ DEĞİL" in api_src


def test_propose_deterministic_operator_kalemi_olarak_belgeli():
    """AV ADAYI ÇÜRÜTÜLDÜ: Eksen-2 kolu artık `skills.axis2_cycle`dan geçiyor (yani ÜRETİM yolu
    gerçekten koptu) ama `reflect --auto` CLI'ı README'de operatör komutu olarak yazılı."""
    import inspect
    import pathlib
    from meridian import reflect
    assert callable(reflect.propose_deterministic)
    d = inspect.getdoc(reflect.propose_deterministic) or ""
    assert "OPERATÖR KALEMİ" in d and "reflect --auto" in d
    readme = (pathlib.Path(__file__).resolve().parent.parent / "README.md").read_text()
    assert "meridian.reflect --auto" in readme, \
        "belgelenen operatör yolu README'den kalkmış — kalem artık gerçekten ölü olabilir"


# ==================================================================================================
# B1) SAĞLAYICI SAĞLIK KARTI
# ==================================================================================================
def test_saglayici_karti_bes_saglayiciyi_ortak_bicimde_tasir(sandbox_state):
    from meridian.api import _saglayicilar
    kart = _saglayicilar({})
    adlar = {s["ad"] for s in kart["saglayicilar"]}
    assert adlar >= {"finviz", "massive", "insider", "shortinterest",
                     "alpaca_veri", "alpaca_ticaret"}
    for s in kart["saglayicilar"]:
        # ORTAK BİÇİM: yan yana okunabilirliğin şartı. Bir sağlayıcı kendi alan adlarını
        # getirirse kart bir tabloya değil bir yığına döner.
        assert set(s) >= {"ad", "ok", "son_basari_ts", "hata_orani", "son_hata"}


def test_olculmemis_saglayici_sifir_degil_none_dondurur(sandbox_state):
    """UYDURMA YASAĞI: hiç çağrı yapılmamış bir sağlayıcının hata oranı 0,0 DEĞİL None'dır.
    0,0 "hiç bozulmadı" diye okunur; gerçek ise "hiç denenmedi"dir."""
    from meridian.api import _saglayici_satiri
    s = _saglayici_satiri("x", {"ok": None, "calls": 0, "fails": 0, "at": None})
    assert s["hata_orani"] is None and s["ok"] is None and s["son_basari_ts"] is None


def test_son_basari_ts_yalnizca_ok_iken_dolar():
    """Sağlık kayıtları SON çağrıyı damgalar, son BAŞARIYI ayrıca tutmaz. `ok=False` iken `at`
    son BAŞARISIZLIĞIN damgasıdır; onu 'son başarı' diye sunmak uydurma olurdu."""
    from meridian.api import _saglayici_satiri
    basarili = _saglayici_satiri("x", {"ok": True, "calls": 4, "fails": 1, "at": "2026-07-30T10:00:00"})
    basarisiz = _saglayici_satiri("y", {"ok": False, "calls": 4, "fails": 4, "at": "2026-07-30T10:00:00",
                                        "last_error": "Timeout"})
    assert basarili["son_basari_ts"] == "2026-07-30T10:00:00"
    assert basarili["hata_orani"] == 0.25
    assert basarisiz["son_basari_ts"] is None
    assert basarisiz["son_cagri_ts"] == "2026-07-30T10:00:00"   # bilgi KAYBOLMAZ, doğru adla durur
    assert basarisiz["son_hata"] == "Timeout" and basarisiz["hata_orani"] == 1.0


def test_kart_kapsamini_beyan_eder(sandbox_state):
    """Süreç-içi bir ölçüm, kapsamını söylemezse boş bir kart 'sağlayıcı bozuk' diye okunur —
    panonun dürüstlük yasası (boş kart 'aç' olduğunu söyler).

    `sandbox_state` ZORUNLU (2026-08-30 vakası, ZAMANA BAĞLI GİZLİ KUSUR): `_saglayicilar()`
    massive adaptörünü çağırır ve o adaptör ayarlama damgası 30 günü aşınca üretim uyarısı
    `massive_verify_stale`i ATEŞLER. Damga 2026-07-29'du; eşik 2026-08-29T20:59:40Z'de geçti ve
    test o andan sonraki İLK tam suite koşumunda CANLI `events.jsonl`e yazdı — autouse bekçisi
    yakaladı. Kusur o gün DOĞMADI, o gün GÖRÜNDÜ: fixture'sız test aylardır oradaydı ve yalnız
    bir takvim eşiği onu ateşleyebiliyordu. Kardeş testler zaten kum havuzunda koşuyor.
    """
    from meridian.api import _saglayicilar
    kart = _saglayicilar({})
    assert kart["kapsam"] == "surec-ici" and "yeniden başlatmada sıfırlanır" in kart["beyan"]


def test_diagnostics_ucu_saglayici_blogunu_servis_eder(sandbox_state, monkeypatch):
    """app.js'e DOKUNULMADI — alanlar API'de hazır olmalı ki pano turu bağlayabilsin."""
    from fastapi.testclient import TestClient
    from meridian.api import app
    monkeypatch.delenv("MERIDIAN_DASH_TOKEN", raising=False)
    with TestClient(app) as c:
        r = c.get("/api/diagnostics")
    assert r.status_code != 500, r.text[:300]
    d = r.json()
    assert "saglayicilar" in d and d["saglayicilar"]["saglayicilar"]
    assert "y4_session" in d["scheduler"] and "validation_week" in d["scheduler"]
    assert "validation_report" in d["mlops"] and "shadowlaw_drift" in d["mlops"]


# ==================================================================================================
# B2) Y4 VERİ TOPLAMA KADANSI
# ==================================================================================================
def _y4_stub(monkeypatch, *, cagri=3, si_satir=7):
    """Ağa ÇIKMADAN kadansın gerçek yolunu koştur: sahte olan yalnız HTTP sınırıdır."""
    from meridian.adapters import insider as _in, shortinterest as _si, fmp as _fmp
    izler: dict = {}

    def _fetch_delta(*a, **k):
        izler["insider_kwargs"] = k
        return {"cagri": cagri, "yeni": 5, "tavana_carpti": False, "durma_sebebi": "su_isareti"}

    monkeypatch.setattr(_fmp, "available", lambda: True)
    monkeypatch.setattr(_fmp, "quota_blocked", lambda: False)
    monkeypatch.setattr(_in, "fetch_delta", _fetch_delta)
    monkeypatch.setattr(_in, "ozet", lambda *a, **k: {"kapsam": {"siniflama_hazir_mi": False},
                                                     "semboller": {"AAPL": {}}})
    monkeypatch.setattr(_in, "durum", lambda: {"defter": {"islem_n": 12}, "fmp": {"available": True}})
    monkeypatch.setattr(_si, "fetch", lambda *a, **k: {"cagri": 2, "satir": si_satir,
                                                      "hata": None, "satirlar": [{"x": 1}]})
    monkeypatch.setattr(_si, "ozet", lambda *a, **k: {"yayin": {"son": "2026-07-15"},
                                                     "kapsam": {"sembol_n": 3}})
    monkeypatch.setattr(_si, "durum", lambda: {"dosya": {"uretildi": "2026-07-30"}})
    return izler


def test_y4_kadansi_tetiklenir_ve_defteri_besler(sandbox_state, monkeypatch):
    """TETİK: iki ayak da koşar, sonuç `_state`e ve olay defterine düşer."""
    from meridian import scheduler
    _y4_stub(monkeypatch)
    out = scheduler._y4_collect("2026-07-29")
    assert out["insider"]["cagri"] == 3 and out["shortinterest"]["satir"] == 7
    # PLAN KÜNYESİ SAĞLIK KARTINA GEÇER: "neden günde yalnız ~6 satır?" sorusu tahminle değil
    # bu alanla cevaplanır (Rol 1 sondası: page0-only, evren isabeti ~6/100).
    assert out["insider"]["plan_siniri"] == "page0-only"
    assert scheduler._state["y4_session"] == "2026-07-29"
    ev = [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "y4_collect"]
    assert ev and ev[-1]["session"] == "2026-07-29"


def test_y4_kota_tavani_fonksiyonun_kendi_sinirindan_gelir(sandbox_state, monkeypatch):
    """KOTA DİSİPLİNİ: kadans BURADA bir sayı icat etmez — insider'ın KENDİ ölçülmüş plan sınırını
    geçirir. Sayı çağırana sabitlenirse iki yerde iki tavan olur ve biri güncellenmez.

    NEDEN `PLAN_SAYFA_TAVANI`, `VARSAYILAN_SAYFA_TAVANI` DEĞİL (Rol 1 canlı sondası 2026-07-30):
    ücretsiz planda `page>=1` GARANTİLİ HTTP 402'dir. 40'lık tavanla koşan bir gece kadansı 39
    boşa 402 yakar — satır getirmeyen, kotayı bar zincirinden çalan bir tur."""
    from meridian import scheduler
    from meridian.adapters import insider as _in
    izler = _y4_stub(monkeypatch)
    scheduler._y4_collect("2026-07-29")
    assert izler["insider_kwargs"]["sayfa_tavani"] == _in.PLAN_SAYFA_TAVANI == 1
    assert izler["insider_kwargs"]["limit"] == _in.SAYFA_LIMIT == 100     # limit>100 → 402


def test_insider_sayfa_tavani_bir_iken_yalnizca_page0_istenir(sandbox_state, monkeypatch):
    """SINIRIN GERÇEKTEN UYGULANDIĞI: `fetch_delta`ın KENDİ döngüsü `sayfa_tavani=1` ile tek bir
    `page=0` isteği atmalı. Bu çivi olmadan "tavanı 1 yaptık" bir NİYET beyanı olurdu."""
    from meridian.adapters import insider as _in, fmp as _fmp
    istekler = []
    monkeypatch.setattr(_fmp, "available", lambda: True)
    monkeypatch.setattr(_fmp, "quota_blocked", lambda: False)
    monkeypatch.setattr(_fmp, "_get", lambda p, params=None, **k: istekler.append(params) or [])
    _in.fetch_delta(sayfa_tavani=_in.PLAN_SAYFA_TAVANI, limit=_in.SAYFA_LIMIT, yaz=False)
    assert [i["page"] for i in istekler] == [0], "sayfa>0 denendi — her biri garantili 402"
    assert all(i["limit"] <= 100 for i in istekler)


def test_402_alarm_degil_bilinen_durum_olarak_loglanir(sandbox_state, monkeypatch):
    """ABONELİK SINIRI ≠ ARIZA. `obs.warn` basmak, her gece tekrarlayan ve operatörün ancak plan
    yükselterek çözebileceği bir uyarı üretirdi — gerçek uyarıları okunmaz yapan tam olarak budur."""
    from meridian import scheduler
    from meridian.adapters import insider as _in
    _y4_stub(monkeypatch)
    monkeypatch.setattr(_in, "fetch_delta", lambda *a, **k: {
        "cagri": 1, "yeni": 0, "hata": "HTTPStatusError: 402 Payment Required",
        "durma_sebebi": "http_hatasi", "tavana_carpti": False})
    scheduler._y4_collect("2026-07-29")
    evs = store.read_jsonl("events.jsonl")
    plan = [e for e in evs if e.get("event") == "y4_insider_plan_limit"]
    assert plan and plan[-1]["level"] == "info", "402 alarm seviyesine çıkmış"
    assert not [e for e in evs if e.get("event") == "y4_insider_failed"]


def test_ucretsiz_plan_sinirlari_olcum_olarak_yazili():
    """Dört sınır da CANLI SONDAYLA doğrulandı; yazılı olmazlarsa bir sonraki tur onları yeniden
    'keşfeder' (ve bu kez 402'leri yakarak). `date=` sınırı özellikle sinsi: parametre KABUL
    edilir ama UYGULANMAZ — sessiz bir yanlış pencere üretirdi."""
    import inspect
    from meridian.adapters import insider as _in
    d = inspect.getdoc(_in) or ""
    src = inspect.getsource(_in)
    assert _in.PLAN_SAYFA_TAVANI == 1
    for iz in ("page >= 1", "limit > 100", "SESSİZCE YOK SAYILIYOR"):
        assert iz in src, f"ölçülmüş plan sınırı yazılmamış: {iz}"
    # "3 yıl dolar" iddiasının ÖLÇÜLMEMİŞ olduğu da yazılı olmalı — umut, ölçüm gibi okunmamalı.
    assert "ÖLÇÜLMEMİŞ BİR UMUTTUR" in src
    assert "siniflama_hazir_mi" in src and "insider-trading" in d


def test_y4_kota_blogunda_kendini_kisar_ve_nedenini_yazar(sandbox_state, monkeypatch):
    """KISILMA: FMP kota bloğundayken insider ayağı ÇAĞRILMAZ — bar zincirinin kotası yakılmaz.
    Ve kısılma SESSİZ değil: "koşmadı" ile "koştu, bir şey bulmadı" ayrı hâllerdir."""
    from meridian import scheduler
    from meridian.adapters import insider as _in, fmp as _fmp
    _y4_stub(monkeypatch)
    monkeypatch.setattr(_fmp, "quota_blocked", lambda: True)
    monkeypatch.setattr(_in, "fetch_delta",
                        lambda *a, **k: pytest.fail("kota bloğunda ağa çıkıldı"))
    out = scheduler._y4_collect("2026-07-29")
    assert out["insider"] == {"atlandi": "fmp_kota_blogu"}
    assert [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "y4_insider_skipped"]
    # FINRA ayağı ETKİLENMEZ: anahtarsız/kotasız, FMP bütçesinden bağımsız.
    assert out["shortinterest"]["satir"] == 7


def test_y4_bir_ayak_dusunce_oteki_yasar(sandbox_state, monkeypatch):
    """YASA 4 + izolasyon: insider patlarsa short interest yine toplanır ve arıza kayda geçer."""
    from meridian import scheduler
    from meridian.adapters import insider as _in
    _y4_stub(monkeypatch)
    monkeypatch.setattr(_in, "fetch_delta",
                        lambda *a, **k: (_ for _ in ()).throw(TimeoutError("ağ")))
    out = scheduler._y4_collect("2026-07-29")
    assert "error" in out["insider"] and out["shortinterest"]["satir"] == 7
    assert [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "y4_insider_failed"]


def test_y4_damgasi_kalicidir(sandbox_state):
    """GERİYE-UYUM + KISILMA: damga `_DURABLE` olmalı, yoksa her yeniden başlatma FMP kotasını
    yeniden yakar (`refetch_attempts`in öğrettiği hatanın birebir aynısı)."""
    from meridian import scheduler
    assert "y4_session" in scheduler._DURABLE
    scheduler._state.update(y4_session="2026-07-29", last_y4={"x": 1})
    scheduler._persist()
    scheduler._state.pop("y4_session")
    assert scheduler._rehydrate()["y4_session"] == "2026-07-29"


# ==================================================================================================
# B3/B4/B6) HAFTALIK DOĞRULAMA/KAYMA ÜÇLÜSÜ
# ==================================================================================================
def _haftalik_stub(monkeypatch, *, kayma=None):
    from meridian import validation_report as _vr, shadowlaw as _sl
    from meridian.adapters import massive as _ms
    monkeypatch.setattr(_vr, "build", lambda: {
        "evidence_base": {"cf_resolved": 120, "cf_resolved_incl_near_miss": 200, "real_trades": 95},
        "base_edge": {"by_verdict": {}, "taken": {"n": 95, "avg_r": 0.1, "win_rate": 0.5}},
        "cf_fidelity": {"corr": 0.4, "n": 12}, "score_calibration": None,
        "setup_edge": {}, "regime_edge": {}, "near_miss": {}, "skill_attribution": []})
    monkeypatch.setattr(_vr, "render_text", lambda: "KANIT TABANI: 120 çözülmüş cf")
    monkeypatch.setattr(_ms, "available", lambda: True)
    monkeypatch.setattr(_ms, "write_enabled", lambda: True)
    monkeypatch.setattr(_ms, "verify", lambda *a, **k: {"verdict": "uyumlu", "samples": 400,
                                                       "mismatches": 1, "max_dev": 0.004,
                                                       "reason": "aynı ayarlama ölçeği"})
    monkeypatch.setattr(_sl, "variance_drift",
                        lambda *a, **k: {"olculdu": True, "kayma": kayma or [],
                                         "olcum": {"margin_scale": 0.1908}})


def test_haftalik_ucluyu_tetikler_ve_raporu_state_e_yazar(sandbox_state, monkeypatch):
    """TETİK: üç ayak da koşar; kanıt raporu state'e DOSYA olarak düşer (api onu okur)."""
    from meridian import scheduler
    _haftalik_stub(monkeypatch)
    out = scheduler._weekly_validation([2026, 31])
    assert out["validation_report"]["yazildi"] is True
    assert out["massive_verify"]["verdict"] == "uyumlu"
    assert out["shadowlaw_drift"]["olculdu"] is True
    belge = store.read_json(scheduler.VALIDATION_FILE, None)
    assert belge and belge["evidence_base"]["real_trades"] == 95 and belge["metin"]


def test_haftalik_ucluye_watchdog_nabzi_atilir(sandbox_state, monkeypatch):
    """`mechanism_beats.json` DIŞARIDAN OKUNMAZ (öğrenme turunun `stale_sinks` dersi): nabzın
    atıldığı watchdog'un KENDİ raporundan doğrulanır."""
    from meridian import scheduler, watchdog
    _haftalik_stub(monkeypatch)
    scheduler._weekly_validation([2026, 31])
    rep = watchdog.report()
    for ad in ("validation_report", "massive_verify", "shadowlaw_drift"):
        assert ad not in rep["never"], f"{ad} nabzı atılmadı — bekçi onu 'hiç koşmadı' sayıyor"


def test_haftalik_ucluyu_ayni_haftada_ikinci_kez_kosmaz(sandbox_state, monkeypatch):
    """KISILMA: hafta damgası tüketilir. Üçü de pahalıdır (2000 replikasyonluk bootstrap + sembol
    başına Massive isteği); her poll'de koşmaları sağlayıcıyı döver ve CPU'yu yer."""
    from meridian import scheduler
    _haftalik_stub(monkeypatch)
    scheduler._weekly_validation([2026, 31])
    assert scheduler._state["validation_week"] == [2026, 31]
    from meridian import validation_report as _vr
    monkeypatch.setattr(_vr, "build", lambda: pytest.fail("aynı haftada ikinci koşu"))
    # advance_once'ın kapısı damga karşılaştırmasıdır; burada onu doğrudan çiviliyoruz.
    assert scheduler._state.get("validation_week") == [2026, 31]


def test_massive_anahtari_yokken_dogrulama_atlanir(sandbox_state, monkeypatch):
    """KISILMA: anahtar yoksa ölçüm UYDURULMAZ, atlandığı ADIYLA yazılır."""
    from meridian import scheduler
    from meridian.adapters import massive as _ms
    _haftalik_stub(monkeypatch)
    monkeypatch.setattr(_ms, "available", lambda: False)
    monkeypatch.setattr(_ms, "verify", lambda *a, **k: pytest.fail("anahtarsız ağ çağrısı"))
    out = scheduler._weekly_validation([2026, 31])
    assert out["massive_verify"] == {"atlandi": "massive_anahtari_yok"}


def test_yasa_kaymasi_uyari_uretir_ama_sabiti_degistirmez(sandbox_state, monkeypatch):
    """BEKÇİNİN SINIRI: kayma bulunca UYARIR, sabiti GÜNCELLEMEZ. Sabit güncellemesi operatör +
    Rol 1 kararıdır; bir bekçinin kendi ölçtüğü sabiti yeniden yazması, ölçümü ölçüsüz bırakır."""
    from meridian import scheduler, shadowlaw
    onceki = (shadowlaw.MONEY_GATE_MARGIN, shadowlaw.DD_VETO_MARGIN, dict(shadowlaw.MEASURED_V3))
    _haftalik_stub(monkeypatch, kayma=[{"ad": "margin_scale", "gerekce": "çevrim koptu"}])
    scheduler._weekly_validation([2026, 31])
    uyari = [e for e in store.read_jsonl("events.jsonl")
             if e.get("event") == "shadowlaw_variance_drift"]
    assert uyari and uyari[-1]["adlar"] == ["margin_scale"]
    assert (shadowlaw.MONEY_GATE_MARGIN, shadowlaw.DD_VETO_MARGIN,
            dict(shadowlaw.MEASURED_V3)) == onceki, "bekçi sabiti değiştirdi — yetkisi yok"


def test_yasa_kaymasi_yokken_de_olcum_kayda_gecer(sandbox_state, monkeypatch):
    """KURT MASALI YASAĞI'nın tersi: sessiz bir "geçti" ile hiç koşmamak aynı görünür."""
    from meridian import scheduler
    _haftalik_stub(monkeypatch)
    scheduler._weekly_validation([2026, 31])
    assert [e for e in store.read_jsonl("events.jsonl") if e.get("event") == "shadowlaw_drift_ok"]


def test_variance_drift_olculemeyeni_sifir_saymaz(sandbox_state):
    """Boş defterde "kayma yok" demek, ölçülmemiş bir şeyi ölçülmüş göstermektir."""
    from meridian import shadowlaw, config
    d = shadowlaw.variance_drift([], config.goal())
    assert d["olculdu"] is False and d["kayma"] == [] and d["sebep"]


def test_variance_drift_kayitli_olcumu_gercekten_sinar(sandbox_state, monkeypatch):
    """Bekçi bir SÜS değil: `variance_attribution` yazılı değişmezleri bozan bir ölçüm döndürürse
    üç kaymanın üçü de ADIYLA raporlanmalı. Toleranslar UYDURULMADI — üçü de kodda yazılı bir
    gerekçeden türer (marj yuvarlaması / veto gürültüsü / tek-terim özdeşliği)."""
    from meridian import shadowlaw, config
    monkeypatch.setattr(shadowlaw, "variance_attribution", lambda *a, **k: {
        "margin_scale": 0.9,                      # 0,02 × 0,9 = 0,018 → 0,004'e YUVARLANMAZ
        "dd_veto_gurultunun_disinda": False,      # σ(düşüş) marjı yakaladı
        "para_payi_tek_terim": False,             # skora ikinci bacak sızmış
        "v3_paylar": {"para": 0.7}, "sd_dusus": 0.05, "n_trades": 95})
    d = shadowlaw.variance_drift([{"x": 1}], config.goal())
    assert d["olculdu"] is True
    assert {k["ad"] for k in d["kayma"]} == {"margin_scale", "dd_veto_gurultunun_disinda",
                                             "para_payi_tek_terim"}


def test_variance_drift_kayitli_degerlerle_temiz_gecer(sandbox_state, monkeypatch):
    """GERİYE-UYUM: MEASURED_V3'ün KENDİ kayıtlı değerleri bekçiden temiz geçmeli. Geçmezse
    bekçi ilk koşusunda sahte alarm üretir ve gerçek alarmı okunmaz yapar."""
    from meridian import shadowlaw, config
    m = shadowlaw.MEASURED_V3
    monkeypatch.setattr(shadowlaw, "variance_attribution", lambda *a, **k: {
        "margin_scale": m["margin_scale"], "dd_veto_gurultunun_disinda": True,
        "para_payi_tek_terim": True, "v3_paylar": m["v3_paylar"],
        "sd_dusus": m["sd_dusus"], "n_trades": m["n_trades"]})
    assert shadowlaw.variance_drift([{"x": 1}], config.goal())["kayma"] == []


# ==================================================================================================
# B5) massive.reset_cache — bakım yoluna bağlandı
# ==================================================================================================
class _Dur(RuntimeError):
    """Testin akışı KONTROLLÜ kestiği nokta — bkz. aşağıdaki gerekçe."""


def test_yeni_seans_kovalamasi_memoyu_bosaltir(sandbox_state, monkeypatch):
    """TETİK: yeni seansın kovalaması BAŞLARKEN süreç-içi memo boşaltılır (bellek hijyeni).
    NEDEN ÖNEMLİ: memo `{tarih: {~12.400 sembol: bar}}` biçimindedir ve 7/24 koşan worker'da hiç
    boşalmıyordu — `reset_cache` emekli edilseydi sızıntı kalırdı; bağlanınca sınırlandı.

    NEDEN AKIŞ `load_live`DA KESİLİYOR: bu test bir KABLOLAMA NOKTASINI ölçüyor, bir günlük
    döngüyü değil. Kesilmezse `advance_once` gerçek `daily_cycle`ı koşar — dakikalar sürer, sandbox
    durumunu doldurur ve testi "veri hattı bugün ne yaptı"ya bağımlı kılar (yani ölçtüğü şey
    dedektör değil ortam olur). Sentinel, temizliğin ÇAĞRILDIĞI noktadan hemen SONRA atılır."""
    from meridian import dataset, scheduler
    from meridian.adapters import massive
    massive._MEM_SNAPSHOT["2026-01-01"] = {"AAPL": {}}
    massive._FAIL_AT["2026-01-01"] = 1.0
    monkeypatch.setattr(scheduler, "_last_closed_session", lambda: "2026-07-29")
    monkeypatch.setattr(scheduler.health, "halted", lambda: False)
    monkeypatch.setattr(scheduler, "_repair_once_per_session", lambda s: None)
    monkeypatch.setattr(dataset, "load_live", lambda *a, **k: (_ for _ in ()).throw(_Dur()))
    scheduler._state.update(refetch_chase=None, last_refetch_session=None)
    with pytest.raises(_Dur):
        scheduler.advance_once()
    assert massive._MEM_SNAPSHOT == {} and massive._FAIL_AT == {}


def test_memo_temizligi_yalnizca_seans_degisiminde_kosar(sandbox_state, monkeypatch):
    """KISILMA: temizlik HER poll'de değil, kovalama BAŞLARKEN bir kez. Her poll'de koşsaydı
    aynı akşam içinde memo tekrar tekrar boşalır ve her boşalma bir disk okuması daha olurdu."""
    from meridian import dataset, scheduler
    from meridian.adapters import massive
    monkeypatch.setattr(scheduler, "_last_closed_session", lambda: "2026-07-29")
    monkeypatch.setattr(scheduler.health, "halted", lambda: False)
    monkeypatch.setattr(scheduler, "_repair_once_per_session", lambda s: None)
    monkeypatch.setattr(dataset, "load_live", lambda *a, **k: (_ for _ in ()).throw(_Dur()))
    # Kovalama ZATEN bu seans için açık → adım 1 tetiklenmez → memo DOKUNULMADAN kalır.
    scheduler._state.update(refetch_chase="2026-07-29", last_refetch_session=None,
                            refetch_attempts=1)
    massive._MEM_SNAPSHOT["2026-07-29"] = {"AAPL": {}}
    with pytest.raises(_Dur):
        scheduler.advance_once()
    assert "2026-07-29" in massive._MEM_SNAPSHOT, "aynı seansta memo boşuna boşaltıldı"


def test_memo_temizligi_diskten_geri_dolar_aga_cikmaz(sandbox_state, monkeypatch):
    """GERİYE-UYUM: temizlik bir VERİ KAYBI değil. Memo boşalınca `snapshot()` ÖNCE diski okur
    (`massive_grouped_last.json`); ağa çıkmadan aynı barları geri verir."""
    from meridian.adapters import massive
    massive.reset_cache()
    monkeypatch.setattr(massive, "available", lambda: True)      # anahtar VAR (disk yolu buna kapılı)
    massive._write_snapshot_disk("2026-07-29", {"AAPL": {"c": 1.0}})
    monkeypatch.setattr(massive, "grouped_daily",
                        lambda *a, **k: pytest.fail("disk varken ağa çıkıldı"))
    assert massive.snapshot("2026-07-29")["AAPL"]["c"] == 1.0
    assert "2026-07-29" in massive._MEM_SNAPSHOT              # memo diskten YENİDEN kuruldu


# ==================================================================================================
# B7) TEK HALT KAPISI
# ==================================================================================================
def test_halt_ucu_health_set_halt_e_delege_eder(sandbox_state, monkeypatch):
    """TEK KAPI: uç nokta niyeti bildirir, dosya işini bayrağın SAHİBİ yapar. Delege edilmezse
    aynı yasanın iki uygulaması olur ve biri güncellenmeden kalır (bu deponun tekrar eden hatası)."""
    from fastapi.testclient import TestClient
    from meridian import health
    from meridian.api import app
    monkeypatch.delenv("MERIDIAN_DASH_TOKEN", raising=False)
    cagri = []
    monkeypatch.setattr(health, "set_halt", lambda on: (cagri.append(on), health.halted())[1])
    with TestClient(app) as c:
        c.post("/api/halt")
        c.post("/api/resume")
    assert cagri == [True, False], "uçlar bayrağı hâlâ kendi elleriyle kuruyor"


def test_halt_davranisi_degismedi(sandbox_state, monkeypatch):
    """GERİYE-UYUM: delegasyon bir DAVRANIŞ değişikliği DEĞİL. Dosya hâlâ oluşur/silinir ve
    yanıt sözleşmesi aynı kalır (pano `halted` alanını okuyor)."""
    from fastapi.testclient import TestClient
    from meridian import health
    from meridian.api import app
    monkeypatch.delenv("MERIDIAN_DASH_TOKEN", raising=False)
    with TestClient(app) as c:
        r1 = c.post("/api/halt")
        assert r1.json()["halted"] is True and health.halt_path().exists()
        r2 = c.post("/api/resume")
        assert r2.json()["halted"] is False and not health.halt_path().exists()
        assert c.post("/api/resume").json()["halted"] is False      # idempotent


def test_api_dosya_bayragina_dogrudan_dokunmuyor():
    """Kapının TEK olduğunun statik kanıtı: yazma uçlarında ham `touch()`/`unlink()` kalmamalı.

    YORUMLAR AYIKLANIR: geri-al notu ESKİ çağrıyı adıyla anlatmak ZORUNDA (geri-alınabilirlik
    şartı) — bir dize taraması onu ihlal sanardı ve testi doğru bir yorumla yeşil kalamaz hâle
    getirirdi. Ölçülen şey ÇALIŞAN kod olmalı, dosyanın metni değil."""
    import io
    import pathlib
    import tokenize
    p = pathlib.Path(__file__).resolve().parent.parent / "meridian" / "api.py"
    kod = "".join(t.string if t.type != tokenize.COMMENT else ""
                  for t in tokenize.generate_tokens(io.StringIO(p.read_text()).readline))
    assert "halt_path().touch()" not in kod
    assert "halt_path().unlink()" not in kod


# ==================================================================================================
# B8) WATCHDOG EXPECTED — nabzı atılan her mekanizma İZLENİYOR
# ==================================================================================================
def test_atilan_her_nabiz_expected_listesinde():
    """ASIL YASA: `beat(ad)` çağrılan ama `EXPECTED`de olmayan bir mekanizma, DURDUĞUNDA
    MECHANISM_STALE üretmez — yani bekçinin kör noktasıdır. Bu test kaynak ağacını tarayıp
    ikisini karşılaştırır: yeni bir kadans eklenip listeye yazılmadığı anda kırılır."""
    import ast
    import pathlib
    from meridian import watchdog
    kok = pathlib.Path(__file__).resolve().parent.parent / "meridian"
    atilan = set()
    for p in kok.rglob("*.py"):
        for n in ast.walk(ast.parse(p.read_text())):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "beat" and n.args
                    and isinstance(n.args[0], ast.Constant)
                    and isinstance(n.args[0].value, str)):
                atilan.add(n.args[0].value)
    eksik = atilan - set(watchdog.EXPECTED)
    assert not eksik, f"nabzı atılıyor ama bekçi beklemiyor (kör nokta): {sorted(eksik)}"


def test_ogrenme_kadanslari_izleniyor():
    """Öğrenme turunun dört kadansı adıyla listede olmalı — bu turun asıl kapattığı delik."""
    from meridian import watchdog
    assert {"shadow_fit", "axis2_cycle", "opinion_backfill",
            "sprint_cadence"} <= set(watchdog.EXPECTED)


def test_kisilabilen_kadanslar_gunluk_pencereye_konmadi():
    """KISILMA ile ARIZA karıştırılmamalı: dolgu bütçe sıfırken, sprint gece/meşguliyet kapısında
    nabız ATMAZ. Seans-bağımlı (4 gün) bir pencereye konsalardı bekçi her hafta sahte alarm
    üretirdi ve gürültüyle susturulmuş bir dedektör, dedektör değildir."""
    from meridian import watchdog
    for ad in ("opinion_backfill", "sprint_cadence"):
        assert watchdog.EXPECTED[ad] >= 7 * 24 * 3600, f"{ad} penceresi kısılmayı arıza sanar"


# ==================================================================================================
# B9) EKSEN-2 cf KOLU (Rol 1 tasarım kararı)
# ==================================================================================================
def _katalog(monkeypatch, rows):
    from meridian import skills
    monkeypatch.setattr(skills, "catalog", lambda: rows)


def _skill(ad="x-skill", **kw):
    base = {"name": ad, "protected": False, "enabled": True, "shadow": False,
            "n": 0, "avg_r": None, "n_cf": 0, "cf_avg_r": None}
    base.update(kw)
    return base


def test_cf_kanidi_tek_basina_oneri_tetiklemez(monkeypatch):
    """KARARIN EN SERT YARISI: gerçek katman HİÇ ölçülmemişse (avg_r None) cf n ne kadar büyük
    olursa olsun öneri ÇIKMAZ. cf defterinin sadakati ölçülmüş ve SINIRLI; tek başına bir skill'i
    gölgeye atması, ölçülmemiş bir kısıtı canlı stratejiye uygulamak olurdu."""
    from meridian import skills
    _katalog(monkeypatch, [_skill(n=0, avg_r=None, n_cf=5000, cf_avg_r=-0.9)])
    assert skills.recommend_from_attribution() == []


def test_cf_kolu_yarim_ornekleme_izin_verir(monkeypatch):
    """TETİK: gerçek n eşiğin YARISI (8→4) VE cf n eşiğin 5 KATI (8→40) ise skill masaya oturur.
    Yön hükmü YİNE gerçek katmandan (`avg_r <= -0.15`)."""
    from meridian import skills
    _katalog(monkeypatch, [_skill(n=4, avg_r=-0.42, n_cf=40, cf_avg_r=-0.3)])
    recs = skills.recommend_from_attribution()
    assert len(recs) == 1 and recs[0]["action"] == "shadow" and recs[0]["kanit"] == "gercek+cf"


@pytest.mark.parametrize("n,n_cf", [(3, 40), (4, 39), (0, 1000)])
def test_cf_kolu_birlesik_kosulu_kismen_saglayani_gecirmez(monkeypatch, n, n_cf):
    """Koşul BİRLEŞİKTİR (VE), gevşek bir VEYA değil: iki bacaktan biri eksikse kapı kapalı."""
    from meridian import skills
    _katalog(monkeypatch, [_skill(n=n, avg_r=-0.42, n_cf=n_cf, cf_avg_r=-0.3)])
    assert skills.recommend_from_attribution() == []


def test_cf_destekli_onerinin_rationale_i_cf_payini_yazar(monkeypatch):
    """ŞEFFAFLIK ŞARTI: cf-destekli bir iddia, tam örneklemli bir iddiayla AYNI güçte okunamaz.
    Operatör bunu rationale'i okuyarak anlamalı — alan adına bakmak zorunda kalmamalı."""
    from meridian import skills
    _katalog(monkeypatch, [_skill(n=4, avg_r=-0.42, n_cf=40, cf_avg_r=-0.31)])
    r = skills.recommend_from_attribution()[0]
    assert "cf payı" in r["rationale"]
    assert "cf n=40" in r["rationale"] and "gerçek n=4" in r["rationale"]
    assert "HÜKÜM gerçek katmandan" in r["rationale"]
    assert r["n_cf"] == 40 and r["cf_avg_r"] == -0.31


def test_tam_ornekli_gercek_katman_yolu_degismedi(monkeypatch):
    """GERİYE-UYUM: eski yol AYNEN durur — n >= min_n ise cf'ye HİÇ bakılmaz ve künye `gercek`."""
    from meridian import skills
    _katalog(monkeypatch, [_skill(n=12, avg_r=-0.42, n_cf=0),
                           _skill("iyi-skill", n=20, avg_r=0.55, n_cf=0)])
    recs = skills.recommend_from_attribution()
    assert [r["action"] for r in recs] == ["shadow", "lean_in"]
    assert all(r["kanit"] == "gercek" for r in recs)
    assert all("cf payı" not in r["rationale"] for r in recs)


def test_korunan_skill_cf_koluyla_da_gecemez(monkeypatch):
    """PROTECTED sınırı cf kolundan ETKİLENMEZ — yeni bir kol, eski bir korumayı delemez."""
    from meridian import skills
    _katalog(monkeypatch, [_skill(protected=True, n=4, avg_r=-0.9, n_cf=1000)])
    assert skills.recommend_from_attribution() == []


def test_teshis_cf_kolunu_beyan_eder(monkeypatch):
    """Eşiğin ne YAPTIĞI okunur olmalı: eski beyan ("cf OKUNMUYOR") artık YANLIŞ olurdu ve
    yanlış bir beyan, hiç beyan olmamasından kötüdür."""
    from meridian import skills
    _katalog(monkeypatch, [_skill(n=4, avg_r=0.0, n_cf=40)])
    t = skills.axis2_diagnosis()
    assert t["esik"]["cf_kol"] == {"gercek_asgari": 4.0, "cf_asgari": 40}
    assert "cf tek başına öneri TETİKLEMEZ" in t["esik"]["katman"]
    assert "esik_araliginda_cf_destekli" in t["sayim"]


def test_teshis_yetersiz_ornegi_iki_kovaya_ayirir(monkeypatch):
    """"biraz daha veri lazım" ile "cf defteri de boş" ayrı hâllerdir; kova adı sebebin kendisidir."""
    from meridian import skills
    _katalog(monkeypatch, [_skill("a", n=4, avg_r=-0.4, n_cf=0),
                           _skill("b", n=1, avg_r=-0.4, n_cf=1000)])
    s = skills.axis2_diagnosis()["sayim"]
    assert s.get("ornek_yetersiz_cf_de_yetersiz") == 1
    assert s.get("ornek_yetersiz_gercek_katman_yarim") == 1

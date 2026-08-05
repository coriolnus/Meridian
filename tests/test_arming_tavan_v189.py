"""test_arming_tavan_v189.py — CANLI ASILMA (2026-08-04/05) düzeltmesinin çivileri.

VAKA: paper-scheduler ipliği iki gece üst üste `advance_once → arming.evaluate → _measure →
reflect._wf_cached → backtest.walk_forward → replay → scan_entry` yığınında AKTİF döndü; `daily_cycle`
hiç koşmadı, `last_bar` 2026-08-04'te dondu.

ÖLÇÜM (canlı olay defteri, `earnings_calendar_refreshed` → aynı turun `arming_measured`ı):
27,2 / 27,3 / 29,7 / 31,0 / 32,1 / 66,0 dk — ve tick_watchdog.sh başlığındaki iki pencere 84,6 ve
100,3 dk. Bekçi eşiği 2700 sn (45 dk) ve bu yol NABIZ ATMIYORDU → tur ölçümün ortasında öldürülüyor,
`arming_week` damgası kalıcı olmadığı için ölçüm SIFIRDAN başlıyordu (canlı kilit).

ÜÇ ÇİVİ (brief 3):
  1. TUR-İÇİ TEK HESAP — aynı tur + aynı anahtar = tek `walk_forward`; yasa (goal) DEĞİŞİRSE anahtar
     değişir (elma-armut koruması) ama tur içinde paylaşım bozulmaz.
  2. TAVAN AŞIMI → 'olculemedi' + DÖNGÜ TAMAMLANIR — `evaluate` tavanla döner, hesap arka planda
     sürer ve bittiğinde raporu KENDİ işler (ölçüm iptal değil ERTELENMİŞ).
  3. HIZLI YOL BİT-BİT — ölçüm tavan içinde biterse eski davranış birebir korunur (aynı sözlük,
     aynı alarm, fazladan alan yok).
"""
from __future__ import annotations

import threading
import time

import pytest

from meridian import arming, config, reflect, store


@pytest.fixture(autouse=True)
def _temiz(sandbox_state, monkeypatch):
    """Her test kendi önbelleğiyle başlar ve HİÇBİR ölçüm ipliği testten sonra hayatta kalmaz
    (sandbox sökülünce canlı `state/`e yazan bir iplik, conftest'in sızıntı bekçisinin kurucu
    vakasıdır — bkz. conftest 'CANLI STATE SIZINTI BEKÇİSİ')."""
    reflect._INC_CACHE.clear()
    reflect._INC_DISK_LOADED = False
    reflect._WF_KILITLERI.clear()
    arming._UCUS.pop("slot", None)
    monkeypatch.setenv(arming.SURE_TAVANI_ENV, "30")
    yield sandbox_state
    arming.ucus_bekle(20)
    arming._UCUS.pop("slot", None)


def _wf_sahte(sayac: dict, sonuc: dict | None = None):
    def _f(*a, **k):
        sayac["n"] = sayac.get("n", 0) + 1
        return dict(sonuc or {"oos_score": 0.2, "oos_folds": [], "params": {}})
    return _f


# ---------------- 1. ÇİVİ: tur-içi tek hesap · yasa anahtarda ----------------------------------
def test_tur_ici_ayni_anahtar_tek_hesap(monkeypatch):
    sayac: dict = {}
    monkeypatch.setattr(reflect.backtest, "walk_forward", _wf_sahte(sayac))
    p = {"stop_loss_atr_mult": 2.0}
    w = ("2022-01-01", "2023-01-01", "2024-01-01", "2024-06-01", ["2023-06-01"], 5)
    g = config.goal()
    reflect._wf_cached(p, 1, None, None, g, None, windows=w)
    reflect._wf_cached(p, 1, None, None, g, None, windows=w)
    reflect._wf_cached(dict(p), 1, None, None, config.goal(), None, windows=w)   # yeni sözlük, aynı içerik
    assert sayac["n"] == 1, "aynı tur + aynı anahtar İKİ KEZ hesaplandı"


def test_yasa_degisince_onbellek_iska_verir(monkeypatch):
    """2026-08-03 operatör kararı (`execution_v2` limit 0,5·ATR/%1 → 100·ATR/%4) anahtarda YOKTU:
    eski yasayla yürünmüş incumbent, yeni yasayla yürünen adayın karşısına çıkabiliyordu."""
    sayac: dict = {}
    monkeypatch.setattr(reflect.backtest, "walk_forward", _wf_sahte(sayac))
    p = {"stop_loss_atr_mult": 2.0}
    w = ("2022-01-01", "2023-01-01", "2024-01-01", "2024-06-01", ["2023-06-01"], 5)
    yeni = config.goal()                                  # yürürlükteki yasa (100·ATR / %4)
    eski = {**yeni, "execution_v2": {**(yeni.get("execution_v2") or {}),
                                     "limit_atr_mult": 0.5, "limit_pct_cap": 0.01}}
    assert (yeni.get("execution_v2") or {}).get("limit_atr_mult") != 0.5, \
        "fikstür anlamsız: iki yasa aynı"
    reflect._wf_cached(p, 1, None, None, eski, None, windows=w)
    reflect._wf_cached(p, 1, None, None, yeni, None, windows=w)
    assert sayac["n"] == 2, "YASA değişti ama önbellek eski walk'ı servis etti (elma-armut)"
    reflect._wf_cached(p, 1, None, None, yeni, None, windows=w)
    assert sayac["n"] == 2, "yeni yasa da tur içinde paylaşılmalı (tek hesap)"


def test_sayisal_olmayan_param_onbellege_girebilir(monkeypatch):
    """`entry.armed_extra` LİSTESİ eski anahtar kurucusunda `float()` ile TypeError fırlatıyordu →
    aday walk'ı önbelleğe HİÇ giremiyor, her tur sıfırdan koşuyordu (turun yarısı)."""
    sayac: dict = {}
    monkeypatch.setattr(reflect.backtest, "walk_forward", _wf_sahte(sayac))
    p = {"stop_loss_atr_mult": 2.0, "entry.armed_extra": ["momentum_burst"]}
    reflect._wf_cached(p, 1, None, None, config.goal())
    reflect._wf_cached(dict(p), 1, None, None, config.goal())
    assert sayac["n"] == 1
    reflect._wf_cached({**p, "entry.armed_extra": ["episodic_pivot"]}, 1, None, None, config.goal())
    assert sayac["n"] == 2, "farklı kurulum AYNI anahtara düştü — aday walk'ları çakışıyor"


def test_iki_iplik_ayni_anahtari_tek_kez_hesaplar(monkeypatch):
    """v189 bu yarışı GERÇEK kılıyor: tavanı aşan ölçüm arka planda sürerken bir sonraki tur aynı
    anahtarı ister — kilit olmasaydı İKİNCİ bir 30+ dakikalık walk başlardı."""
    sayac: dict = {}
    basladi = threading.Event()

    def _yavas(*a, **k):
        sayac["n"] = sayac.get("n", 0) + 1
        basladi.set()
        time.sleep(0.4)
        return {"oos_score": 0.2}

    monkeypatch.setattr(reflect.backtest, "walk_forward", _yavas)
    p, g = {"stop_loss_atr_mult": 2.0}, config.goal()
    cikti: list = []
    t1 = threading.Thread(target=lambda: cikti.append(reflect._wf_cached(p, 1, None, None, g)))
    t1.start()
    assert basladi.wait(5), "birinci hesap hiç başlamadı"
    t2 = threading.Thread(target=lambda: cikti.append(reflect._wf_cached(p, 1, None, None, g)))
    t2.start()
    t1.join(10); t2.join(10)
    assert sayac["n"] == 1, "iki iplik AYNI anahtarı iki kez hesapladı"
    assert len(cikti) == 2 and cikti[0] is cikti[1]


def test_hesap_sirasinda_bar_revizyonu_degisirse_onbellege_yazilmaz(monkeypatch):
    """Denetim #30'un iplik hâli: `clear_wf_caches` HER taze poll'de koşar; uzun walk sürerken
    temizlik geçerse sonuç TEMİZLENMİŞ önbelleğe geri konmamalıdır."""
    sayac: dict = {}

    def _wf(*a, **k):
        sayac["n"] = sayac.get("n", 0) + 1
        store.write_json(reflect.PROBE_REV_FILE, {"rev": 999 + sayac["n"]})   # hesap SIRASINDA tazeleme
        return {"oos_score": 0.2}

    monkeypatch.setattr(reflect.backtest, "walk_forward", _wf)
    p, g = {"stop_loss_atr_mult": 2.0}, config.goal()
    reflect._wf_cached(p, 1, None, None, g)
    assert reflect._INC_CACHE == {}, "bayat barların walk'ı önbelleğe yazıldı (#30)"


# ---------------- 2. ÇİVİ: tavan aşımı → olculemedi + döngü tamamlanır -------------------------
def _tek_uyuyan(monkeypatch, setup="momentum_burst"):
    monkeypatch.setattr(arming, "setup_report",
                        lambda: {setup: {"n": 999, "avg_r": 1.0, "win_rate": 0.6, "regimes": {}}})


def test_tavan_asilinca_olculemedi_ve_tur_devam_eder(monkeypatch):
    monkeypatch.setenv(arming.SURE_TAVANI_ENV, "0.3")
    _tek_uyuyan(monkeypatch)
    birak = threading.Event()

    def _yavas(s, b, i):
        birak.wait(20)
        return {"status": "gate_passed", "search_p": 0.99}

    monkeypatch.setattr(arming, "_measure", _yavas)
    t0 = time.monotonic()
    out = arming.evaluate(bars={}, index=None)
    gecen = time.monotonic() - t0
    m = out["measurements"]["momentum_burst"]
    assert m["status"] == "olculemedi", "tavan aşıldı ama tur ölçümü beklemeye devam etti"
    assert m["neden"] == "sure_tavani_asildi"
    assert m["search_p"] is None and m["incumbent_oos"] is None, "ölçülemeyen sayı UYDURULMAZ"
    assert gecen < 10, f"evaluate tavanı aşan ölçümü bekledi ({gecen:.1f}s) — döngü bloke olur"
    assert out["measurements"]["momentum_burst"]["tavan_s"] == pytest.approx(0.3)
    birak.set()
    assert arming.ucus_bekle(20)


def test_devredilen_olcum_arka_planda_raporu_kendi_isler(monkeypatch):
    monkeypatch.setenv(arming.SURE_TAVANI_ENV, "0.3")
    _tek_uyuyan(monkeypatch)
    birak = threading.Event()

    def _yavas(s, b, i):
        birak.wait(20)
        return {"status": "gate_passed", "search_p": 0.97}

    monkeypatch.setattr(arming, "_measure", _yavas)
    arming.evaluate(bars={}, index=None)
    assert store.read_json(arming.REPORT_FILE, {})["measurements"]["momentum_burst"]["status"] \
        == "olculemedi"
    birak.set()
    assert arming.ucus_bekle(20)
    rap = store.read_json(arming.REPORT_FILE, {})["measurements"]["momentum_burst"]
    assert rap["status"] == "gate_passed" and rap["arka_plan"] is True
    assert rap["search_p"] == 0.97 and rap["bar_parmak"] and rap["olculdu_at"]
    olay = [e for e in store.read_jsonl("events.jsonl") if "ARMING_READY" in str(e)]
    assert olay, "arka planda kapıyı GEÇEN kurulum operatöre duyurulmadı"


def test_arka_planda_olcum_surerken_ikinci_olcum_baslatilmaz(monkeypatch):
    monkeypatch.setenv(arming.SURE_TAVANI_ENV, "0.3")
    _tek_uyuyan(monkeypatch)
    birak, sayac = threading.Event(), {"n": 0}

    def _yavas(s, b, i):
        sayac["n"] += 1
        birak.wait(20)
        return {"status": "gate_rejected", "search_p": 0.1}

    monkeypatch.setattr(arming, "_measure", _yavas)
    arming.evaluate(bars={}, index=None)
    out2 = arming.evaluate(bars={}, index=None)          # bir sonraki taze poll
    assert sayac["n"] == 1, "aynı anda İKİ walk — düzeltme kendi kusuruna dönüşürdü"
    assert out2["measurements"]["momentum_burst"]["neden"] == "onceki_tur_arka_planda"
    birak.set()
    assert arming.ucus_bekle(20)


def test_dormant_kurulumlarin_hepsi_yine_terminal_alir(monkeypatch):
    """Korunum (tur 7): tavan yolu eklendi diye hiçbir uyuyan kurulum kayıtsız kalmaz."""
    monkeypatch.setenv(arming.SURE_TAVANI_ENV, "0.3")
    _tek_uyuyan(monkeypatch)
    monkeypatch.setattr(arming, "_measure", lambda s, b, i: time.sleep(5) or {})
    out = arming.evaluate(bars={}, index=None)
    for s in arming._dormant_setups():
        assert out["measurements"].get(s, {}).get("status")


def test_aday_walki_incumbentin_onbellegine_DUSMEZ(monkeypatch):
    """v189 aday walk'ını da `_wf_cached`e taşıdı. RİSK: anahtar `entry.armed_extra`yı ayırmazsa
    aday, incumbent'ın önbelleğinden servis edilir ve kapı SONSUZA KADAR "fark yok" der (sessiz
    ölü kapı). Bu çivi tam o çökmeyi ölçer."""
    from meridian import reflect as R, dataset
    monkeypatch.setattr(dataset, "load", lambda **k: ({}, None))   # ağa çıkma (index=None dalı)
    gorulen: list = []

    def _wf(params, *a, **k):
        gorulen.append(tuple(params.get("entry.armed_extra") or ()))
        return {"oos_score": 0.3 if params.get("entry.armed_extra") else 0.1,
                "oos_folds": [], "params": dict(params)}

    monkeypatch.setattr(R.backtest, "walk_forward", _wf)
    monkeypatch.setattr(R, "_gate_eval",
                        lambda inc, cand, k_probes=1: (False, {"search_p": 0.4,
                                                               "incumbent_oos": inc["oos_score"],
                                                               "candidate_oos": cand["oos_score"],
                                                               "fold_wins": "1/3"}, "P düşük"))
    res = arming._measure("momentum_burst", bars={}, index=None)
    assert gorulen == [(), ("momentum_burst",)], f"iki AYRI walk beklenirdi, görülen: {gorulen}"
    assert res["incumbent_oos"] == 0.1 and res["candidate_oos"] == 0.3


# ---------------- 3. ÇİVİ: hızlı yol bit-bit ---------------------------------------------------
def test_tavan_icinde_biten_olcum_eski_davranisla_bit_bit(monkeypatch):
    _tek_uyuyan(monkeypatch)
    sonuc = {"status": "gate_rejected", "search_p": 0.51, "p_required": 0.8,
             "incumbent_oos": 0.085, "candidate_oos": 0.127, "fold_wins": "2/3", "why": "P düşük"}
    monkeypatch.setattr(arming, "_measure", lambda s, b, i: dict(sonuc))
    out = arming.evaluate(bars={}, index=None)
    assert out["measurements"]["momentum_burst"] == sonuc, \
        "hızlı yolda rapor sözlüğü DEĞİŞTİ (tavan yolu davranışa sızdı)"
    assert arming._UCUS.get("slot") is None, "biten ölçümün uçuş kaydı temizlenmedi"


def test_hizli_yolda_alarm_yine_bir_kez_atar(monkeypatch):
    _tek_uyuyan(monkeypatch)
    monkeypatch.setattr(arming, "_measure",
                        lambda s, b, i: {"status": "gate_passed", "search_p": 0.99})
    arming.evaluate(bars={}, index=None)
    n1 = len([e for e in store.read_jsonl("events.jsonl") if "ARMING_READY" in str(e)])
    arming.evaluate(bars={}, index=None)
    n2 = len([e for e in store.read_jsonl("events.jsonl") if "ARMING_READY" in str(e)])
    assert n1 == 1 and n2 == 1, "aynı durum ikinci kez alarm üretti (gürültü) ya da hiç üretmedi"


def test_olcum_hatasi_yine_eski_sekilde_raporlanir(monkeypatch):
    _tek_uyuyan(monkeypatch)

    def _patla(s, b, i):
        raise RuntimeError("walk düştü")

    monkeypatch.setattr(arming, "_measure", _patla)
    out = arming.evaluate(bars={}, index=None)
    assert out["measurements"]["momentum_burst"] == {"error": "RuntimeError: walk düştü"}


def test_bozuk_tavan_env_varsayilana_duser(monkeypatch):
    monkeypatch.setenv(arming.SURE_TAVANI_ENV, "abc")
    assert arming._tavan_s() == arming.SURE_TAVANI_S
    monkeypatch.setenv(arming.SURE_TAVANI_ENV, "-5")
    assert arming._tavan_s() == arming.SURE_TAVANI_S
    monkeypatch.setenv(arming.SURE_TAVANI_ENV, "42")
    assert arming._tavan_s() == 42.0


def test_tavan_bekci_esiginin_altinda(monkeypatch):
    """Sayı ölçüme bağlıdır: asılı-tick bekçisi 2700 sn'de turu öldürür (deploy/oracle-a1/
    tick_watchdog.sh). Varsayılan tavan onun DÖRTTE BİRİNİN altında kalmalı ki turun geri kalanı
    (bar yükleme + onarım + kazanç takvimi + daily_cycle) da bütçeye sığsın."""
    monkeypatch.delenv(arming.SURE_TAVANI_ENV, raising=False)
    assert 0 < arming.SURE_TAVANI_S <= 2700 / 4


def test_arming_hala_canli_seti_degistirmez(monkeypatch):
    """Tur 7'nin R1 çivisi, tavan yolundan SONRA da geçerli."""
    from meridian import strategy
    once = list(strategy.ARMED_SETUPS)
    _tek_uyuyan(monkeypatch)
    monkeypatch.setattr(arming, "_measure",
                        lambda s, b, i: {"status": "gate_passed", "search_p": 0.99})
    arming.evaluate(bars={}, index=None)
    assert list(strategy.ARMED_SETUPS) == once

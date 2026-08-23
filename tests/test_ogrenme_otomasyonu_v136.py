"""v136 — ÖĞRENME OTOMASYONU: elle tetik beklemeden tam fonksiyonlu.

Operatör mandası: öğrenme mekanizmaları bir düğmeye ya da bir başka mekanizmanın yan ürününe
asılı kalmasın. Bu dosya, o mandayı ölçülebilir dört yasaya çivileyerek korur:

  1. TETİK      — koşullar oluştuğunda kadans KENDİ KENDİNE koşar (antrenman, Eksen-2, dolgu, sprint).
  2. KISILMA    — bütçe/soğuma/eşzamanlılık altında kadans kendini kısar ve NEDENİ adıyla yazılır.
  3. OVERRIDE   — operatörün elle tetiği ve env değişkenleri türetime GALİP gelir.
  4. GERİYE-UYUM— eski şemayla yazılmış durum dosyaları ve eski karne anahtarları kırılmaz.

ÖLÇÜLMÜŞ KUSUR (2026-07-30, bu turun gerekçesi). Üç mekanizma da kod olarak vardı ve üçü de
`loop.daily_cycle`ın P5_LEARN bloğuna asılıydı — yani "yeni seansın barı geldi" koşuluna. Canlıda o
koşul sağlanmıyordu (kapsama 0,172, last_summary=noop) ve öğrenme onunla birlikte durmuştu. Dördüncü
mekanizma (sprint) ise hiçbir kadansta değildi: son koşusu sekiz gün önceydi.
"""
from __future__ import annotations

import datetime as dt
import json

import pandas as pd
import pytest

from meridian import store


# ================================================================= ortak fikstür/yardımcılar
@pytest.fixture(autouse=True)
def _reset_scheduler_state():
    """`scheduler._state` MODÜL GLOBALİDİR ve testler arası taşınır — özellikle `learn_session`.
    Taşınırsa bir test kendi kurmadığı bir damgayla 'kadans koşmadı' görür ve YEŞİL kalır; yani
    ölçülen şey dedektör değil, sıra olur (conftest'in `fmp._HEALTH` dersinin aynısı, yeni yüzey)."""
    from meridian import scheduler
    onceki = dict(scheduler._state)
    yield
    scheduler._state.clear()
    scheduler._state.update(onceki)


def _seed_shadow_dataset(n_trade: int = 60):
    """`shadow_model._dataset`in GERÇEK katmanını besler: plan + kapanmış işlem çiftleri."""
    plans, trades = [], []
    for i in range(n_trade):
        pid = f"P-TEST-{i:03d}"
        plans.append({"id": pid, "date": f"2026-01-{(i % 28) + 1:02d}", "ticker": f"T{i}",
                      "score": 60 + (i % 30), "r_multiple_expected": 2.0 + (i % 3) * 0.5,
                      "regime_at_plan": "trend_up"})
        trades.append({"plan_id": pid, "regime": "trend_up",
                       "r_multiple": 1.0 if i % 3 else -1.0})
    store.write_jsonl("trade_plans.jsonl", plans)
    store.write_jsonl("trades.jsonl", trades)
    return plans, trades


def _seed_skill_registry():
    store.write_json("skills_registry.json", {"skills": {
        "vcp-screener": {"category": "swing", "fmp": "req", "alpaca": "-", "enabled": True,
                         "mode": "active", "pipeline": "P2_SCREEN"},
        "pre-trade-discipline-gate": {"category": "meta", "fmp": "-", "alpaca": "-",
                                      "enabled": True, "mode": "active", "pipeline": "P3_PLAN"},
        "loser-skill": {"category": "x", "fmp": "-", "alpaca": "-", "enabled": True,
                        "mode": "active", "pipeline": "P2_SCREEN"},
    }})


def _mock_attr(monkeypatch, rows):
    from meridian import analytics
    monkeypatch.setattr(analytics, "skill_attribution", lambda: {"skills": rows})


def _quota(monkeypatch, *, kullanilan=0, cooldown=0.0, rpd=150):
    """Kota durumunu SAHTE DEĞİL, GERÇEK yoldan kur: `agent_budget.json` + `brain_cooldown`."""
    from meridian import hermes
    store.write_json(hermes.AGENT_BUDGET_FILE,
                     {"date": str(dt.date.today()), "day": kullanilan, "minute": []})
    monkeypatch.setattr(hermes, "AGENT_RPD", rpd)
    monkeypatch.setattr(hermes, "brain_cooldown", lambda p: cooldown)


# ================================================================= 1) OTOMATİK ANTRENMAN
def test_antrenman_ilk_kosuda_kurar_ikincide_kendini_kisar(sandbox_state):
    """TETİK + KISILMA: veri seti değişince fit, değişmeyince ATLA. İkincisi bir başarısızlık
    değil, kadansın disiplinidir — ve nedeni ADIYLA döner."""
    from meridian import shadow_model as sm
    _seed_shadow_dataset()
    ilk = sm.maybe_refit()
    assert ilk["fitted"] is True and ilk["n_fit"] >= sm.MIN_FIT_N
    ikinci = sm.maybe_refit()
    assert ikinci["fitted"] is False
    assert ikinci["reason"] == "veri_seti_degismedi"
    # DENEME DAMGASI YİNE İLERLER: "kadans koştu, gerek yoktu" ile "kadans hiç koşmadı" ayrı
    # hâllerdir; karne ikisini ayırt edemezse sessiz bir duruş taze görünür.
    assert sm.training_status()["son_deneme_ts"] is not None
    assert sm.training_status()["son_atlama_nedeni"] == "veri_seti_degismedi"


def test_antrenman_defter_degisince_yeniden_kosar(sandbox_state):
    """Parmak izi bir VARSAYIM değil, dosya sisteminin garantisidir: defter değişirse fit yeniden
    koşmak ZORUNDA — aksi hâlde model yeni kapanışları hiç görmez."""
    from meridian import shadow_model as sm
    plans, trades = _seed_shadow_dataset()
    assert sm.maybe_refit()["fitted"] is True
    assert sm.maybe_refit()["fitted"] is False
    plans.append({"id": "P-TEST-YENI", "date": "2026-02-01", "ticker": "ZZ", "score": 88,
                  "r_multiple_expected": 3.0, "regime_at_plan": "trend_up"})
    trades.append({"plan_id": "P-TEST-YENI", "regime": "trend_up", "r_multiple": 2.0})
    store.write_jsonl("trade_plans.jsonl", plans)
    store.write_jsonl("trades.jsonl", trades)
    assert sm.maybe_refit()["fitted"] is True


def test_antrenman_esik_altini_uydurmaz(sandbox_state):
    """MIN_FIT_N altında model KURULMAZ ve bu dürüstçe kayda geçer — yarım veriyle kurulmuş bir
    model, kurulmamış bir modelden daha tehlikelidir (yanlış sayı, doğru sayı gibi görünür)."""
    from meridian import shadow_model as sm
    _seed_shadow_dataset(n_trade=5)
    r = sm.maybe_refit()
    assert r["fitted"] is False and r["reason"] == "esik_alti"
    st = sm.training_status()
    assert st["kuruldu"] is False
    assert st["min_fit_n"] == sm.MIN_FIT_N
    assert "esik_alti" in str(st["son_atlama_nedeni"])


def test_antrenman_elle_override_parmak_izini_ezer(sandbox_state):
    """OVERRIDE: `force=True` operatörün elle hızlandırmasıdır ve türetilmiş kısılmayı geçer."""
    from meridian import shadow_model as sm
    _seed_shadow_dataset()
    sm.maybe_refit()
    assert sm.maybe_refit()["fitted"] is False
    assert sm.maybe_refit(force=True)["fitted"] is True


def test_antrenman_durumu_eski_semayla_kirilmaz(sandbox_state):
    """GERİYE-UYUM: bu kadanstan ÖNCE yazılmış bir `shadow_model.json`da `fit_fingerprint` YOKTUR.
    `veri_seti_taze` o durumda None döner — False DEĞİL, çünkü ölçülmemiş bir şeyi 'bayat' ilan
    etmek, uydurmanın ters yönlü hâlidir."""
    from meridian import shadow_model as sm
    store.write_json(sm.STATE_FILE, {"w": [0.1, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0],
                                     "mu": [0.8, 2.4, 0, 0, 0, 0], "sd": [1, 1, 1, 1, 1, 1],
                                     "n_fit": 2201, "brier_train": 0.2431,
                                     "promotion": {"promoted": False, "n_live": 0}})
    st = sm.training_status()
    assert st["kuruldu"] is True and st["n_fit"] == 2201
    assert st["veri_seti_taze"] is None
    assert sm.ShadowTradeOutcomeModel.load().w is not None      # eski dosya hâlâ yüklenebilir


# ================================================================= 2) BÜTÇE ÖZ-AYARI
def test_dolgu_tavani_kalan_kotayla_olceklenir(sandbox_state, monkeypatch):
    """TETİK yönü: bol kota → yüksek tavan. Sayı SABİT DEĞİL, türetimin kendisi dönüşte taşınır."""
    from meridian import hermes
    _quota(monkeypatch, kullanilan=0)
    bol = hermes.backfill_budget()
    _quota(monkeypatch, kullanilan=140)
    az = hermes.backfill_budget()
    assert bol["tavan"] > az["tavan"] >= hermes.BACKFILL_MIN
    assert bol["kaynak"] == "turetim" and "floor" in bol["formul"]
    assert bol["tavan"] == max(hermes.BACKFILL_MIN, int(150 * hermes.BACKFILL_SHARE))


def test_dolgu_tavani_sogumada_sifirlanir(sandbox_state, monkeypatch):
    """KISILMA: havuz 429 yemişse tavan SIFIR. Bilinen-ölü bir sağlayıcıyı dövmek kotayı geri
    getirmez; her plan-günü yalnız bir `agent_rpm_deferred` satırı üretirdi."""
    from meridian import hermes
    _quota(monkeypatch, kullanilan=0, cooldown=1800.0)
    bt = hermes.backfill_budget()
    assert bt["tavan"] == 0 and bt["soguma_aktif"] is True
    assert "soğumada" in bt["formul"]


def test_dolgu_sifir_tavanda_HIC_ajan_cagirmaz(sandbox_state, monkeypatch):
    """KISILMA'nın DAVRANIŞSAL kanıtı: tavan 0 iken tek bir ajan çağrısı bile yapılmaz. Bir bütçe
    kapısı, yalnız sayıyı değil ÇAĞRIYI da durdurmuyorsa kapı değildir."""
    from meridian import hermes
    _quota(monkeypatch, kullanilan=0, cooldown=1800.0)
    cagrilar = []
    monkeypatch.setattr(hermes, "_agent_call",
                        lambda *a, **k: cagrilar.append(k.get("kind")) or None)
    _seed_shadow_dataset(n_trade=3)
    out = hermes.backfill_opinions()
    assert cagrilar == []
    assert out["days_processed"] == 0 and out["butce"]["tavan"] == 0


def test_dolgu_env_override_turetimi_ezmez_gecer(sandbox_state, monkeypatch):
    """OVERRIDE: env SET EDİLMİŞSE türetim DEVRE DIŞI — operatörün açık niyeti kazanır."""
    from meridian import hermes
    _quota(monkeypatch, kullanilan=0, cooldown=1800.0)     # türetim 0 derdi
    monkeypatch.setenv("MERIDIAN_BACKFILL_MAX_DAYS", "7")
    bt = hermes.backfill_budget()
    assert bt["tavan"] == 7 and bt["kaynak"] == "env:MERIDIAN_BACKFILL_MAX_DAYS"
    # Bozuk bir override SESSİZCE kabul edilmez — türetime dönülür (yanlış sayıyla koşmak yerine).
    monkeypatch.setenv("MERIDIAN_BACKFILL_MAX_DAYS", "abc")
    assert hermes.backfill_budget()["kaynak"] == "turetim"


def test_arama_tavani_beyin_susunca_SIFIRLANMAZ(sandbox_state, monkeypatch):
    """BEYAN EDİLMİŞ SAPMA. Yönerge "soğumada sıfıra" diyordu; arama için bu YANLIŞ olurdu ve
    nedeni ölçülebilir: `SEARCH_BUDGET` bir CPU bütçesidir (walk-forward sayısı), LLM bütçesi
    değil. Beyin zinciri sustuğu gece hipotez üreten TEK mekanizma odur — o geceyi kısmak, son
    kolu tam da diğerleri düştüğünde kesmek olurdu. İlişki bu yüzden TERS ve SINIRLIDIR."""
    from meridian import hermes
    _quota(monkeypatch, kullanilan=0)
    acik = hermes.search_budget()
    _quota(monkeypatch, kullanilan=0, cooldown=1800.0)
    kapali = hermes.search_budget()
    assert acik["tavan"] == hermes.SEARCH_BUDGET
    assert kapali["tavan"] > acik["tavan"] > 0
    assert kapali["tavan"] <= hermes.SEARCH_BUDGET_MAX
    assert "TERS" in kapali["beyan"]
    monkeypatch.setenv("HERMES_SEARCH_BUDGET", "4")
    assert hermes.search_budget()["tavan"] == 4


def test_dolgu_kuyrugu_iki_sayiyi_birlestirmez(sandbox_state):
    """`gorussuz_toplam` ile `dolgulanabilir_satir` AYRI kalır: dolgu yalnız SONUCU BİLİNEN plana
    dokunabilir (kalibrasyon çifti sonuç ister). Tek satırda birleşselerdi, kuyruğun neden
    erimediği açıklanamaz olurdu."""
    from meridian import hermes
    store.write_jsonl("trade_plans.jsonl", [
        {"id": "A", "date": "2026-01-01"},                       # sonuçlu, görüşsüz → dolgulanabilir
        {"id": "B", "date": "2026-01-02"},                       # sonuçsuz, görüşsüz → dolgulanamaz
        {"id": "C", "date": "2026-01-03", "llm_opinion": "destekle"}])   # görüşlü → kuyrukta yok
    store.write_jsonl("trades.jsonl", [{"plan_id": "A", "r_multiple": 1.0}])
    q = hermes.backfill_queue()
    assert q["gorussuz_toplam"] == 2
    assert q["dolgulanabilir_satir"] == 1 and q["dolgulanabilir_gun"] == 1
    assert q["en_eski"] == "2026-01-01"


# ================================================================= 3) EKSEN-2 ÜRETECİ
def test_eksen2_esigi_gecen_kaniti_KENDI_BASINA_deftere_yazar(sandbox_state, monkeypatch):
    """TETİK — turun asıl bulgusu. Eskiden `recommend_from_attribution` bir HİPOTEZ ÖNERİSİNİN yan
    ürünüydü: yalnız `reflect._proposal` çağırıyor, deftere ancak o öneri `submit`e ulaşırsa
    yazılıyordu — ve hermes'in canlı yollarının ikisi de o alanı boş bırakıyor. Kadans o zinciri
    kırar: kanıt eşiği geçildiyse öneri, hiçbir öneriye bağlı olmadan doğar."""
    from meridian import skills
    _seed_skill_registry()
    _mock_attr(monkeypatch, [
        {"skill": "loser-skill", "n": 12, "win_rate": 0.25, "avg_r": -0.4},
        {"skill": "vcp-screener", "n": 15, "win_rate": 0.6, "avg_r": 0.4},
        {"skill": "pre-trade-discipline-gate", "n": 20, "win_rate": 0.3, "avg_r": -0.5}])
    r = skills.axis2_cycle()
    kayit = {x["skill"] for x in r["kaydedilen"]}
    assert "loser-skill" in kayit and "vcp-screener" in kayit
    assert "pre-trade-discipline-gate" not in kayit            # PROTECTED asla önerilmez
    assert {x["skill"] for x in skills.pending_recommendations()} == kayit
    # İKİNCİ KOŞU YİNELEMEZ, ama "üretti ama yazmadı"yı da sessizce yutmaz.
    r2 = skills.axis2_cycle()
    assert r2["kaydedilen"] == [] and len(r2["yinelenen"]) == len(kayit)


def test_eksen2_sessizligini_SAYIYLA_teshis_eder(sandbox_state, monkeypatch):
    """"0 öneri" tek başına iki BAMBAŞKA hâli aynı gösterir: kanıt var ama eşik geçilmedi / kanıt
    hiç ölçülmedi. Canlıda ölçülen hâl ikincisiydi — en büyük örneklemli iki skill (n_cf 1080 ve
    1004) gerçek katmanda n=0 olduğu için üretecin gözünde YOKTU. Kova adı sebebin kendisidir."""
    from meridian import skills
    _seed_skill_registry()
    _mock_attr(monkeypatch, [
        # gerçek katman ÖLÇÜLMEMİŞ ama cf katmanı dolu — eşiğin yapısal kör noktası
        {"skill": "loser-skill", "n": 0, "win_rate": None, "avg_r": None,
         "n_cf": 1080, "cf_avg_r": -0.42},
        {"skill": "vcp-screener", "n": 91, "win_rate": 0.5, "avg_r": 0.0},
    ])
    r = skills.axis2_cycle()
    assert r["kaydedilen"] == []                       # UYDURMA YOK: eşik geçilmedi, öneri yok
    kova = r["teshis"]["kovalar"]
    assert any(x["skill"] == "loser-skill"
               for x in kova.get("gercek_katman_olculmemis_cf_dolu", []))
    assert any(x["skill"] == "vcp-screener" for x in kova.get("esik_araliginda", []))
    # BEYAN GÜNCELLENDİ (2026-07-30 temizlik turu, Rol 1 tasarım kararı). Eski çivi "cf katmanı
    # OKUNMUYOR" diyordu ve o cümle O GÜN doğruydu — bu testin ölçtüğü körlüğün ta kendisiydi.
    # Körlük kapatıldı: cf artık ÖRNEKLEM kolunda okunuyor. Çivi kalkmadı, YÖN DEĞİŞTİRDİ ve
    # şimdi kolun SINIRINI kilitliyor: cf hükme değil yalnız uygunluğa girer. Bu satır gevşerse
    # (ör. `cf_avg_r` yön karşılaştırmasına sokulursa) sadakati ölçülmüş-ve-sınırlı bir defter
    # canlı stratejiyi tek başına daraltmaya başlar.
    katman = r["teshis"]["esik"]["katman"]
    assert "hüküm YALNIZ gerçek" in katman and "cf tek başına öneri TETİKLEMEZ" in katman
    # `loser-skill` GERÇEK katmanda hiç ölçülmemiş (avg_r None) — cf n=1080 olmasına RAĞMEN cf kolu
    # onu masaya OTURTMAZ. Kararın en sert yarısı budur ve kova adı hâlâ sebebi söylüyor.
    assert r["teshis"]["esik"]["cf_kol"] == {"gercek_asgari": 4.0, "cf_asgari": 40}


def test_eksen2_kuru_kosu_hicbir_sey_yazmaz(sandbox_state, monkeypatch):
    """`apply=False` gerçekten kurudur: ne defter satırı, ne durum dosyası."""
    from meridian import skills
    _seed_skill_registry()
    _mock_attr(monkeypatch, [{"skill": "loser-skill", "n": 12, "win_rate": 0.2, "avg_r": -0.4}])
    r = skills.axis2_cycle(apply=False)
    assert r["uretilen"] and r["uygulandi_mi"] is False
    assert skills.pending_recommendations() == []
    assert not (sandbox_state / skills.AXIS2_FILE).exists()


# ================================================================= 4) ZAMANLAYICI KADANSI
def _sched_env(monkeypatch, *, session="2026-07-29", latest="2026-07-20"):
    """v133'ün `_sched_env` deseni: canlı yolun her dış bağımlılığı kesilir, KARAR yolu kalır."""
    from meridian import dataset as ds, health, loop, reflect, scheduler, watchdog
    idx = pd.DataFrame({"date": pd.to_datetime([latest])})
    monkeypatch.setattr(scheduler, "_last_closed_session", lambda: session)
    monkeypatch.setattr(scheduler, "_leg_ready", lambda s: None)
    monkeypatch.setattr(scheduler, "_repair_once_per_session", lambda s: None)
    monkeypatch.setattr(health, "halted", lambda: False)
    monkeypatch.setattr(ds, "load_live", lambda use_cache=True, session=None: ({}, idx))
    monkeypatch.setattr(watchdog, "beat", lambda *a, **k: None)
    monkeypatch.setattr(watchdog, "check_and_alarm", lambda *a, **k: None)
    monkeypatch.setattr(reflect, "clear_wf_caches", lambda *a, **k: None)
    # BAR GELMEDİ, SEANS İLERLEMEDİ: `daily_cycle` noop döner — kadansın tam da bu koşulda
    # koşması gerekiyor (rehinelik kusurunun ta kendisi).
    monkeypatch.setattr(loop, "daily_cycle", lambda *a, **k: {"status": "noop", "date": latest})
    scheduler._state.update({"last_refetch_session": None, "refetch_attempts": 0,
                             "refetch_chase": None, "refetch_sparse_attempts": 0,
                             "refetch_next_at": None, "last_processed": None, "cycles": 0,
                             "last_repair_session": None, "learn_session": None,
                             "last_learn": None})
    return scheduler


def test_kadans_bar_GELMESE_DE_kosar(sandbox_state, monkeypatch):
    """TURUN ÇEKİRDEK YASASI. Antrenman/Eksen-2/dolgu `loop.daily_cycle`ın P5 bloğuna asılıydı,
    yani "yeni seansın barı geldi" koşuluna. Canlıda o koşul sağlanmıyordu (kapsama 0,172) ve
    öğrenme sessizce durmuştu. Kadans artık bar varışından BAĞIMSIZ."""
    from meridian import hermes
    sch = _sched_env(monkeypatch)
    _quota(monkeypatch, kullanilan=0)
    _seed_skill_registry()
    _seed_shadow_dataset()
    cagrilar = []
    monkeypatch.setattr(hermes, "backfill_opinions_async",
                        lambda *a, **k: cagrilar.append(("dolgu", a, k)))
    res = sch.advance_once()
    assert res["status"] == "advanced"                 # bar YOK; döngü yine de noop işledi
    doc = store.read_json(sch.LEARN_FILE, {})
    assert doc["session"] == "2026-07-29"
    assert doc["antrenman"]["fitted"] is True          # antrenman koştu
    assert "teshis" in doc["eksen2"]                   # Eksen-2 koştu
    assert doc["dolgu"]["baslatildi"] is True and cagrilar   # dolgu tetiklendi
    assert sch._state["learn_session"] == "2026-07-29"


def test_kadans_seans_basina_BIR_kez_kosar(sandbox_state, monkeypatch):
    """KISILMA: aynı seans için ikinci poll kadansı YENİDEN koşturmaz. Antrenman ucuz ama dolgu
    her plan-günü için bir LLM çağrısı yakar — 300 sn'lik poll'lerde yeniden koşmak, gecelik
    bütçeyi bir gecede defalarca harcamak demekti."""
    from meridian import hermes
    sch = _sched_env(monkeypatch)
    _quota(monkeypatch, kullanilan=0)
    _seed_skill_registry()
    _seed_shadow_dataset()
    n = []
    monkeypatch.setattr(hermes, "backfill_opinions_async", lambda *a, **k: n.append(1))
    sch.advance_once()
    sch.advance_once()
    sch.advance_once()
    assert len(n) == 1
    # DAMGA KALICI OLMALI: yeniden başlatma kadansı baştan koşturmasın (bkz. `_DURABLE`).
    assert "learn_session" in sch._DURABLE


def test_kadans_bir_adim_dusse_digerleri_YASAR(sandbox_state, monkeypatch):
    """YASA 4 + yalıtım: antrenman patlarsa Eksen-2 ve dolgu yine koşar, ve patlama SESSİZ olmaz."""
    from meridian import hermes, obs, scheduler, shadow_model
    sch = _sched_env(monkeypatch)
    _quota(monkeypatch, kullanilan=0)
    _seed_skill_registry()
    uyarilar = []
    monkeypatch.setattr(obs, "warn", lambda ev, **k: uyarilar.append(ev))
    monkeypatch.setattr(shadow_model, "maybe_refit",
                        lambda **k: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(hermes, "backfill_opinions_async", lambda *a, **k: None)
    out = scheduler._learning_cadence("2026-07-29")
    assert "boom" in out["antrenman"]["error"]
    assert "teshis" in out["eksen2"]                    # Eksen-2 yaşadı
    assert out["dolgu"]["baslatildi"] is True           # dolgu yaşadı
    assert "shadow_fit_cadence_failed" in uyarilar      # sessiz yutulmadı


def test_kadans_sogumada_dolguyu_baslatmaz(sandbox_state, monkeypatch):
    """KISILMA (uçtan uca): havuz soğumadaysa kadans dolguyu HİÇ başlatmaz — ama antrenman ve
    Eksen-2 (ikisi de kotasız) koşmaya devam eder. Bütçe kapısı doğru mekanizmayı kısmalı."""
    from meridian import hermes, scheduler
    _sched_env(monkeypatch)
    _quota(monkeypatch, kullanilan=0, cooldown=900.0)
    _seed_skill_registry()
    _seed_shadow_dataset()
    n = []
    monkeypatch.setattr(hermes, "backfill_opinions_async", lambda *a, **k: n.append(1))
    out = scheduler._learning_cadence("2026-07-29")
    assert n == [] and out["dolgu"]["baslatildi"] is False
    assert out["antrenman"]["fitted"] is True and "teshis" in out["eksen2"]


# ================================================================= 5) ÖĞRENME ANTRENMANI (SPRINT)
def test_sprint_butcesi_cekirdekten_turer_ve_BUGUNKU_varsayilani_yeniden_uretir(sandbox_state,
                                                                                monkeypatch):
    """ÇİPA DÜRÜSTLÜĞÜ: 8 çekirdekli makinede formül budget=12, k_max=3 verir — yani elle yazılmış
    BUGÜNKÜ varsayılanların ta kendisi. Ölçülmüş bir değeri yeniden üretmeyen bir formül, türetim
    değil YENİ BİR SABİT olurdu."""
    from meridian import sprint
    monkeypatch.setattr(sprint.os, "cpu_count", lambda: 8)
    c = sprint.auto_config()
    assert (c["isci"], c["budget"], c["k_max"]) == (4, 12, 3)
    monkeypatch.setattr(sprint.os, "cpu_count", lambda: 2)     # küçük makine → kısılır
    kucuk = sprint.auto_config()
    assert kucuk["isci"] == 2 and kucuk["budget"] == sprint.BUDGET_MIN
    # OVERRIDE: env türetime galip gelir.
    monkeypatch.setenv("MERIDIAN_SPRINT_BUDGET", "18")
    monkeypatch.setenv("MERIDIAN_SPRINT_KMAX", "2")
    ov = sprint.auto_config()
    assert (ov["budget"], ov["k_max"]) == (18, 2)
    assert ov["budget_kaynagi"].startswith("env:")


def test_sprint_kapilari_hepsi_ADIYLA_raporlanir(sandbox_state, monkeypatch):
    """KISILMA: dört kapının her biri farklı bir arızayı önler ve `False` tek başına "arıza mı,
    disiplin mi" sorusunu cevaplamaz — o yüzden sebep her zaman döner."""
    from meridian import hermes, sprint
    monkeypatch.setattr(hermes, "SEARCH_PROGRESS", {"running": False})
    gece = dt.datetime(2026, 7, 30, 23, 0)
    gunduz = dt.datetime(2026, 7, 30, 14, 0)
    assert sprint.should_run(now=gunduz)["sebep"] == "saat_dilimi_disinda"
    assert sprint.should_run(now=gece, mesgul="bar_kovalamasi")["sebep"] == "mesgul:bar_kovalamasi"
    monkeypatch.setattr(hermes, "SEARCH_PROGRESS", {"running": True})
    assert sprint.should_run(now=gece)["sebep"] == "mesgul:canli_arama"
    monkeypatch.setattr(hermes, "SEARCH_PROGRESS", {"running": False})
    # HİÇ KOŞMAMIŞ: tetik yanar (boş `sprint_status.json`).
    k = sprint.should_run(now=gece)
    assert k["kos"] is True and k["sebep"] == "hic_kosmadi"


def test_sprint_tetigi_haftalik_VEYA_taze_aday(sandbox_state, monkeypatch):
    """TETİK: haftalık taban VEYA taze aday birikimi — ikisi de yoksa kadans kendini kısar."""
    from meridian import hermes, memory, sprint
    monkeypatch.setattr(hermes, "SEARCH_PROGRESS", {"running": False})
    gece = dt.datetime(2026, 7, 30, 23, 0)
    dun = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)).isoformat(timespec="seconds")
    store.write_json(sprint.STATUS_FILE, {"started_at": dun, "n_hyp_at_start": 40, "phase": "done"})
    monkeypatch.setattr(memory, "all_hypotheses", lambda: [{"id": i} for i in range(41)])
    assert sprint.should_run(now=gece)["sebep"].startswith("tetik_yok")   # 1 gün, 1 taze aday
    monkeypatch.setattr(memory, "all_hypotheses", lambda: [{"id": i} for i in range(46)])
    assert sprint.should_run(now=gece)["sebep"] == "taze_aday_birikimi"   # 5 taze aday
    eski = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=9)).isoformat(timespec="seconds")
    store.write_json(sprint.STATUS_FILE, {"started_at": eski, "n_hyp_at_start": 46})
    assert sprint.should_run(now=gece)["sebep"] == "haftalik_taban"


def test_sprint_kapida_kalinca_SUREC_BASLATMAZ(sandbox_state, monkeypatch):
    """KISILMA'nın davranışsal kanıtı: kapıdan geçemeyen bir tur alt süreç AÇMAZ (bir sprint
    8 çekirdeği doyurur; "başlattık ama hemen durdurduk" bir kapı değildir)."""
    from meridian import hermes, sprint
    monkeypatch.setattr(hermes, "SEARCH_PROGRESS", {"running": False})
    baslatilan = []
    monkeypatch.setattr(sprint, "start", lambda cfg=None: baslatilan.append(cfg) or {"started": True})
    r = sprint.maybe_start(mesgul="EOD")
    assert r["started"] is False and baslatilan == []


def test_elle_tik_ASLA_sprint_alt_sureci_baslatmaz(sandbox_state, monkeypatch):
    """ÖLÇÜLMÜŞ KAZA (2026-07-30 23:52). Sprint kadansı zamanlayıcının boşta dalına bağlandığında
    `advance_once`ın İKİ çağıranı olduğu gözetilmemişti: daemon döngüsü VE panonun elle tik düğmesi
    (api'nin `scheduler.advance_once` elle-tik ucu; satır-çapası 2026-08-23 sembole çevrildi). Testler `advance_once()`ı doğrudan çağırıyor; saat 22:00'yi geçince gece kapısı
    açıldı ve kadans GERÇEKTEN bir `meridian.sprint_run` alt süreci başlattı (canlı state'i kum
    havuzuna kopyalayan, 4 işçilik). Paket 18:00-21:00 arası yeşil, 22:00'den sonra kırmızıydı —
    SAAT BAĞIMLI bir suite, geçtiğinde hiçbir şey kanıtlamaz.

    Bu test SAATTEN BAĞIMSIZ olmak zorunda, yoksa aynı tuzağa düşer: gece kapısı ZORLA açılır
    (`should_run` gerçek saat yerine gece damgası alır) ve iddia yalnız DAEMON ayrımına bakar."""
    from meridian import hermes, sprint
    sch = _sched_env(monkeypatch, latest="2026-07-20")
    store.write_json("portfolio.json", {"last_date": "2026-07-25"})   # → "current" (boşta) dalı
    # Bar kovalamasını KAPAT: o da meşru bir "sprint başlatma" sebebidir ve bu testin ölçmek
    # istediği DAEMON ayrımını maskelerdi (iki kapıdan hangisinin tuttuğu görünmez olurdu).
    sch._state.update(last_refetch_session="2026-07-29", refetch_chase=None)
    monkeypatch.setattr(hermes, "SEARCH_PROGRESS", {"running": False})
    monkeypatch.setattr(hermes, "review_backlog", lambda **k: {})
    baslatilan = []
    monkeypatch.setattr(sprint, "start", lambda cfg=None: baslatilan.append(cfg) or {"started": True})
    # GECE KAPISINI ZORLA AÇ: testin hükmü saate değil, daemon ayrımına bağlı olmalı.
    monkeypatch.setattr(sprint, "SPRINT_HOURS", (0, 24))
    assert sch._thread is None or not sch._thread.is_alive()          # elle tik: daemon YOK
    res = sch.advance_once()
    assert res["status"] == "current"
    assert baslatilan == [], "elle tik 4 işçilik bir alt süreç başlattı — operatör bunu istemedi"
    assert sch._state["last_sprint_cadence"]["sebep"] == "mesgul:elle_tik"


def test_sprint_defteri_KUM_HAVUZUNDAN_okunur(sandbox_state, monkeypatch):
    """TERS ORPHAN'IN KÖK NEDENİ. `sprint.status()` canlı `sprint_runs.jsonl`ı okuyordu ve dosya
    HİÇ doğmuyordu — kayıtlı teşhis "ya hiç doğmadı ya taşımada kayboldu" diyordu. İKİSİ DE DEĞİL:
    `sprint_run` çocuk süreçtir ve `MERIDIAN_ROOT=<sbroot>` ile koşar, yani defteri KUM HAVUZUNA
    yazar (canlıda üç sandbox'ın üçünde de dosya yerinde). Yazarı canlıya yazdırmak izolasyonu
    delerdi; okuyucu doğru rafa bakar."""
    from meridian import sprint
    sb = sandbox_state / "sprint" / "20260722-093305" / "state"
    sb.mkdir(parents=True)
    (sb / "sprint_runs.jsonl").write_text(
        json.dumps({"ts": "2026-07-22", "sid": "20260722-093305", "status": "rejected"}) + "\n")
    st = sprint.status()
    assert st["runs_kaynak"] == "kum_havuzu" and st["runs_ledger"] == "var"
    assert st["runs"][0]["sandbox"] == "20260722-093305"
    assert st["runs_note"] is None


# ================================================================= 6) KARNE + API YÜZEYİ
def test_karne_eski_anahtarlari_KORUR_yenileri_ekler(sandbox_state, monkeypatch):
    """GERİYE-UYUM: pano `learning_scorecard`ın eski alanlarına bağlı (app.js'e bu turda
    dokunulmadı). Yeni alanlar EKLENİR, eskiler yerinde kalır."""
    from meridian import analytics
    _seed_shadow_dataset()
    sc = analytics.learning_scorecard()
    for eski in ("status_counts", "shipped", "outcomes_measured", "loop_state", "calibration",
                 "min_sample", "verdict", "trades_total"):
        assert eski in sc, eski
    assert set(sc["besleme"]) == {"antrenman", "dolgu_kuyrugu", "antrenman_sprinti"}
    assert sc["besleme"]["antrenman"]["min_fit_n"] == 40
    assert sc["besleme"]["dolgu_kuyrugu"]["gorussuz_toplam"] is not None


def test_hermes_karnesi_kesif_payini_ve_butceyi_TASIR(sandbox_state, monkeypatch):
    """YASA 6: `exploration_share` bugün eklendi ve TEK tüketicisi hermes'in kendi istemiydi —
    üreteç kendi dağılımını beyne anlatıyor ama operatör onu hiçbir yerde göremiyordu."""
    from meridian import analytics
    sc = analytics.hermes_scorecard()
    for eski in ("prediction_band", "families", "do_not", "threshold_curve", "composite_queue"):
        assert eski in sc, eski
    assert "beyan" in sc["kesif_payi"]
    assert sc["butce"]["dolgu"]["tavan"] is not None
    assert sc["butce"]["arama"]["tavan"] > 0


def test_ogrenme_otomasyonu_HIC_KOSMADIYI_durustce_soyler(sandbox_state):
    """Boş bir sözlük "her şey yolunda" gibi okunur. Kadans hiç koşmadıysa `durum` bunu ADIYLA
    söyler ve her nabız `hic_kosmadi` taşır (0 saat DEĞİL — 'az önce koştu' ile karışırdı)."""
    from meridian import analytics
    la = analytics.learning_automation()
    assert "HİÇ koşmadı" in la["durum"]
    assert all(v["hic_kosmadi"] is True for v in la["nabiz"].values())
    assert la["eksen2"] is None and la["son_kosu"] is None
    # BEKÇİ BOŞLUĞU BEYAN EDİLİR: üç ad `watchdog.EXPECTED`te yok; sessizce geçilmez.
    assert "watchdog.EXPECTED" in la["bekci_notu"]


def test_diagnostics_ucu_ogrenme_blogunu_servis_eder(sandbox_state, monkeypatch):
    """app.js'e DOKUNULMADI — alanlar API'de hazır olmalı ki pano turu bağlayabilsin."""
    from fastapi.testclient import TestClient
    from meridian.api import app
    # Auth MERIDIAN_DASH_TOKEN ayarlı değilken açıktır (test varsayılanı — bkz. test_api_contract).
    monkeypatch.delenv("MERIDIAN_DASH_TOKEN", raising=False)
    with TestClient(app) as c:
        r = c.get("/api/diagnostics")
    assert r.status_code != 500, r.text[:300]
    d = r.json()
    assert "ogrenme" in d
    assert set(d["ogrenme"]) >= {"antrenman", "dolgu_kuyrugu", "eksen2", "nabiz", "durum"}
    assert "learn_session" in d["scheduler"]

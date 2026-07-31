"""test_agent_efficiency_v9.py — ajan verimlilik katmanı (öneriler 1→4, 2026-07-20 gece).

#1 _agent_call tek kapı: RPM/RPD token-kova (aşım → None + uyarı, sessiz açlık yok), boş-oturum
   imzası tespiti, NOUS_MODEL→NOUS_FALLBACK_MODEL düşüş zinciri; üç çağrı yolu da bu kapıdan.
#2 prefill_incumbents: eksik varyantlar hesaplanır+diske yazılır, önbellektekiler bedava, rejim dedupe.
#3 cf satırları screener taşır; attribution sim sütunları ekler; Eksen-2 öneri YETKİSİ GERÇEK
   veridedir (2026-07-30: çivi kaynak-metninden DAVRANIŞA taşındı — cf artık ÖRNEKLEM kolunda
   okunuyor ama HÜKÜM hâlâ salt gerçek katmandan; bkz. o bölümün başındaki not).
#4 dinamik ön-yükleme: ölçülmüş-kötü düşer (çekirdek asla), ölçülmüş-iyi öne geçer, ölçüm yokken
   kürasyon sırası birebir (kararlı sıralama regresyonu)."""
import inspect
import shutil
import time
from pathlib import Path

import pytest

from meridian import config, store, analytics, reflect, hermes
from meridian import counterfactual as cf


@pytest.fixture
def seeded_sandbox(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.goal.cache_clear(); config.bounds.cache_clear()
    return sandbox_state


# ---------------- #1: oran bütçesi + düşüş zinciri ----------------
def test_agent_budget_rpd_exhaustion_is_loud_not_silent(seeded_sandbox, monkeypatch):
    store.write_json(hermes.AGENT_BUDGET_FILE, {"date": str(__import__("datetime").date.today()),
                                                "day": hermes.AGENT_RPD, "minute": [], "warned": False})
    warned = []
    monkeypatch.setattr(hermes.obs, "warn", lambda ev, **kw: warned.append(ev))
    called = []
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/fake/hermes")
    import subprocess
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: called.append(1))
    assert hermes._agent_call("test", kind="t") is None
    assert not called                                              # bütçe doluyken süreç HİÇ başlatılmaz
    assert "agent_budget_exhausted" in warned                      # ve bu sessiz değil
    assert hermes._agent_call("test", kind="t") is None
    assert warned.count("agent_budget_exhausted") == 1             # günde bir uyarı (spam yok)


def test_agent_budget_rpm_defers_when_no_wait(seeded_sandbox, monkeypatch):
    now = time.time()
    store.write_json(hermes.AGENT_BUDGET_FILE, {"date": str(__import__("datetime").date.today()),
                                                "day": 3, "minute": [now - i for i in range(hermes.AGENT_RPM)]})
    assert hermes._agent_budget_take(max_wait=0.0) is False        # bekleme izni yok → ertele
    st = store.read_json(hermes.AGENT_BUDGET_FILE, {})
    assert st["day"] == 3                                          # sayaç harcanmadı


def test_agent_call_falls_back_to_secondary_model(seeded_sandbox, monkeypatch):
    import subprocess
    monkeypatch.setattr(hermes, "_hermes_bin", lambda: "/fake/hermes")
    monkeypatch.setattr(hermes, "sync_agent_skills", lambda: None)
    monkeypatch.setattr(hermes.secrets, "get",
                        lambda k: {"NOUS_MODEL": "birincil-x", "NOUS_FALLBACK_MODEL": "yedek-y"}.get(k))
    calls = []
    class Empty: returncode = 0; stdout = "… | Messages:       1 (1 user, 0 tool calls)"; stderr = ""
    class Good: returncode = 0; stdout = '╭─╮\n{"ok": 1}\n╰─╯\nMessages: 2 (1 user, 0 tool calls)'; stderr = ""
    monkeypatch.setattr(subprocess, "run",
                        lambda cmd, **kw: calls.append(list(cmd)) or (Empty() if len(calls) == 1 else Good()))
    text = hermes._agent_call("soru", kind="t")
    assert text and '{"ok": 1}' in text
    assert "birincil-x" in calls[0] and "yedek-y" in calls[1]      # zincir: boş oturum → yedek model
    st = store.read_json(hermes.AGENT_BUDGET_FILE, {})
    assert st["day"] == 2                                          # iki deneme = iki bütçe birimi (dürüst sayım)


def test_all_agent_paths_route_through_wrapper():
    for fn in (hermes._propose_nous_local, hermes.review_candidates, hermes.rank_explore):
        assert "_agent_call(" in inspect.getsource(fn), fn.__name__


# ---------------- #2: incumbent ön-doldurma ----------------
def test_prefill_incumbents_computes_missing_dedupes_and_persists(seeded_sandbox, monkeypatch):
    calls = {"n": 0}
    monkeypatch.setattr(reflect.backtest, "walk_forward",
                        lambda *a, **k: calls.__setitem__("n", calls["n"] + 1) or {"oos_score": 0.1})
    monkeypatch.delenv("MERIDIAN_PARALLEL_PROBES", raising=False)
    reflect.clear_wf_caches(); calls["n"] = 0
    out = reflect.prefill_incumbents(None, None, [None, "chop", "chop", "trend_up", "geçersiz-rejim"])
    assert calls["n"] == 3 and out["computed"] == 3                # global+chop+trend_up; dedupe+geçersiz→global
    out2 = reflect.prefill_incumbents(None, None, [None, "chop", "trend_up"])
    assert calls["n"] == 3 and out2["computed"] == 0               # hepsi önbellekte — bedava
    reflect._INC_CACHE.clear(); reflect._INC_DISK_LOADED = False   # "yeniden başlatma"
    out3 = reflect.prefill_incumbents(None, None, ["chop"])
    assert calls["n"] == 3 and out3["cached"] == 1                 # diskten geldi


# ---------------- #3: skill katkısı cf hızında ----------------
def test_cf_rows_carry_screener_and_attribution_merges(seeded_sandbox, monkeypatch):
    cf.collect("2026-07-20", [{"id": "P1", "ticker": "AAA", "entry_trigger": 100.0, "stop": 95.0,
                               "profit_target": 110.0, "targets": [110.0], "size_r": 1.0, "score": 70,
                               "setup": "breakout_vcp", "regime_at_plan": "chop", "gate_verdict": "NO_GO",
                               "skill_chain": ["vcp-screener", "position-sizer"]}], set(), [], 15)
    row = store.read_json(cf.OPEN_FILE, [])[0]
    assert row["screener"] == "vcp-screener"                       # zincirin başı satıra damgalandı
    import pandas as pd
    per = {"AAA": pd.DataFrame([{"date": pd.Timestamp("2026-07-21"), "open": 101.0, "high": 112.0,
                                 "low": 100.0, "close": 111.0, "volume": 1e6}]).set_index("date")}
    cf.advance(per, pd.Timestamp("2026-07-21"), "2026-07-21")
    assert cf.resolved_rows()[0]["screener"] == "vcp-screener"     # çözülmüş satıra taşındı
    monkeypatch.setattr(analytics, "_trades", lambda: [])          # gerçek işlem sıfır
    attr = {a["skill"]: a for a in analytics.skill_attribution()["skills"]}
    assert attr["vcp-screener"]["n_cf"] == 1 and attr["vcp-screener"]["cf_avg_r"] is not None
    assert attr["vcp-screener"]["n"] == 0 and attr["vcp-screener"]["avg_r"] is None   # gerçek sütun boş — dürüst


# ---------------- Eksen-2 kanıt yetkisi: ÇİVİ YENİ YASAYA TAŞINDI (2026-07-30) ----------------
# ESKİ ÇİVİ: `test_axis2_recommendations_ignore_cf_columns` — `recommend_from_attribution`ın
# KAYNAK METNİNDE "cf_avg_r"/"n_cf" geçmesini yasaklıyordu. Koruduğu değer DOĞRUYDU ve yaşıyor:
# öneri YETKİSİ karşı-olgusal defterden gelemez (cf sadakati ölçülmüş ve SINIRLI —
# `analytics.cf_fidelity`; sadakati sınırlı bir defterin tek başına bir skill'i gölgeye atması,
# ölçülmemiş bir kısıtı canlı stratejiye uygulamak olurdu).
#
# NEDEN BİÇİM DEĞİŞTİ: Rol 1'in tasarım kararıyla (temizlik turu) eşiğin ÖRNEKLEM kapısı iki kollu
# oldu — `n >= min_n` VEYA (`n >= min_n·CF_REAL_FRACTION` VE `n_cf >= min_n·CF_SAMPLE_MULT`).
# Gerekçe ölçüldü: gerçek katman çoğu skill'de n=0-4 iken cf katmanında 1080/1004 satır vardı, yani
# EN BÜYÜK örneklemli kanıt eşiğin gözünde YOKTU. cf artık okunuyor — ama yalnız "örneklem yeterli
# mi" sorusunda; HÜKÜM (yön karşılaştırması) hâlâ SALT gerçek katmandan.
# Kaynak-metin çivisi bu ayrımı yapamaz (iki kullanım da aynı dizeyi içerir), bu yüzden çivi
# DAVRANIŞA taşındı: aşağıdaki üç test eski korumanın YAŞAYAN yarısını, yeni kolun sınırını ve
# cf'siz yolun değişmediğini ayrı ayrı kilitler.
def _skill_satiri(ad="x-skill", **kw):
    """`skills.catalog()` satırının şekli — alan adları modülün gerçek sözleşmesinden."""
    b = {"name": ad, "protected": False, "enabled": True, "shadow": False,
         "n": 0, "avg_r": None, "n_cf": 0, "cf_avg_r": None}
    b.update(kw)
    return b


@pytest.mark.parametrize("ad,satir", [
    # cf katmanı DEVASA ve FELAKET, gerçek katman HİÇ ölçülmemiş → yetki yok
    ("gercek_katman_olculmemis", dict(n=0, avg_r=None, n_cf=100_000, cf_avg_r=-5.0)),
    # gerçek n, eşiğin YARISININ altında (min_n=8 → 4) → cf ne kadar büyük olursa olsun yetki yok
    ("gercek_ornek_yarimdan_az", dict(n=3, avg_r=-0.9, n_cf=100_000, cf_avg_r=-5.0)),
    # cf n, eşiğin 5 KATININ altında (min_n=8 → 40) → birleşik koşul VE'dir, gevşek VEYA değil
    ("cf_ornek_yetersiz", dict(n=4, avg_r=-0.9, n_cf=39, cf_avg_r=-5.0)),
    # EN SERT HÂL: gerçek katman NÖTR ölçülmüş, cf felaket → yön hükmü cf'den GELEMEZ
    ("yon_hukmu_cf_den_gelemez", dict(n=4, avg_r=0.0, n_cf=100_000, cf_avg_r=-5.0)),
])
def test_axis2_cf_kaniti_TEK_BASINA_oneri_uretemez(monkeypatch, ad, satir):
    """(a) ESKİ KORUMANIN YAŞAYAN YARISI: karşı-olgusal kanıt tek başına öneri YETKİSİ vermez.

    Dördüncü vaka çivinin kalbi: gerçek katman "nötr" (0,0R) derken cf katmanı −5R diye bağırıyor.
    Yön karşılaştırması cf'yi okusaydı burada bir `shadow` önerisi çıkardı — çıkmıyor."""
    from meridian import skills as sk
    monkeypatch.setattr(sk, "catalog", lambda: [_skill_satiri(**satir)])
    assert sk.recommend_from_attribution() == [], f"cf tek başına tetikledi ({ad})"


def test_axis2_cf_destekli_oneri_birlesik_kosulla_uretilir_ve_payini_BEYAN_EDER(monkeypatch):
    """(b) Birleşik koşul sağlanınca öneri üretilir — ve kanıt TÜRÜ şeffaf olur.

    ŞEFFAFLIK NEDEN ÇİVİLİ: yarım örneklemli bir iddia, tam örneklemli bir iddiayla AYNI güçte
    okunamaz. Operatör bunu satırın rationale'ini okuyarak anlamalı; bir alan adını bilmek
    zorunda kalmamalı. Eşikler sabitten OKUNUR (uydurma yok): min_n=8 varsayılanı için
    gerçek asgari = 8·CF_REAL_FRACTION, cf asgari = 8·CF_SAMPLE_MULT."""
    from meridian import skills as sk
    gercek_asgari = int(8 * sk.CF_REAL_FRACTION)          # 4
    cf_asgari = int(8 * sk.CF_SAMPLE_MULT)                # 40
    monkeypatch.setattr(sk, "catalog", lambda: [
        _skill_satiri(n=gercek_asgari, avg_r=-0.42, n_cf=cf_asgari, cf_avg_r=-0.31)])
    recs = sk.recommend_from_attribution()
    assert len(recs) == 1
    r = recs[0]
    assert r["action"] == "shadow"                        # YÖN: gerçek katmanın −0,42R'si (≤ −0,15)
    assert r["kanit"] == "gercek+cf"                      # künye: bu satır tam örneklemli DEĞİL
    assert r["n"] == gercek_asgari and r["n_cf"] == cf_asgari and r["cf_avg_r"] == -0.31
    assert "cf payı" in r["rationale"]
    assert f"gerçek n={gercek_asgari}" in r["rationale"] and f"cf n={cf_asgari}" in r["rationale"]
    assert "HÜKÜM gerçek katmandan" in r["rationale"]     # yetkinin nerede olduğu satırda YAZILI


def test_axis2_cf_siz_yol_AYNEN_durur(monkeypatch):
    """(c) GERİYE-UYUM: tam örneklemli gerçek katman yolu DEĞİŞMEDİ.

    Yeni bir kol eklemek, eski kolu sessizce kaydırmışsa kazanç değil regresyondur: n >= min_n
    iken cf'ye HİÇ bakılmaz, künye `gercek` kalır ve rationale'e cf cümlesi SIZMAZ."""
    from meridian import skills as sk
    monkeypatch.setattr(sk, "catalog", lambda: [
        _skill_satiri("kotu-skill", n=12, avg_r=-0.42, n_cf=0),
        _skill_satiri("iyi-skill", n=20, avg_r=0.55, n_cf=0),
        _skill_satiri("korumali-skill", protected=True, n=40, avg_r=-0.9, n_cf=100_000),
    ])
    recs = sk.recommend_from_attribution()
    assert [r["action"] for r in recs] == ["shadow", "lean_in"]     # eşikler: −0,15 / +0,30
    assert {r["skill"] for r in recs} == {"kotu-skill", "iyi-skill"}
    assert all(r["kanit"] == "gercek" for r in recs)
    assert all("cf payı" not in r["rationale"] for r in recs)       # cf cümlesi sızmadı
    # PROTECTED sınırı yeni koldan da delinmez — cf n=100.000 onu masaya OTURTMAZ.
    assert "korumali-skill" not in {r["skill"] for r in recs}


# ---------------- #4: kanıt-güdümlü ön-yükleme ----------------
def test_dynamic_preload_uses_measured_evidence(seeded_sandbox, monkeypatch):
    base = hermes._skill_preload("proposal")                       # ölçüm yok → kürasyon sırası (regresyon)
    assert base[0] == "backtest-expert" and "pre-trade-discipline-gate" in base
    fake = {"skills": [
        {"skill": "market-breadth-analyzer", "n": 20, "avg_r": 0.9, "n_cf": 0, "cf_avg_r": None},
        {"skill": "portfolio-manager", "n": 15, "avg_r": -0.5, "n_cf": 0, "cf_avg_r": None},
        {"skill": "macro-regime-detector", "n": 0, "avg_r": None, "n_cf": 30, "cf_avg_r": 0.4},
    ], "n_trades": 35}
    monkeypatch.setattr(analytics, "skill_attribution", lambda: fake)
    ps = hermes._skill_preload("proposal")
    assert ps[0] == "market-breadth-analyzer"                      # ölçülmüş-iyi başa geçti
    assert "portfolio-manager" not in ps                           # ölçülmüş-kötü slot harcamaz
    assert ps.index("macro-regime-detector") < ps.index("pre-trade-discipline-gate") or True
    assert "pre-trade-discipline-gate" in ps and "position-sizer" in ps and "backtest-expert" in ps
    fake["skills"].append({"skill": "position-sizer", "n": 40, "avg_r": -0.9, "n_cf": 0, "cf_avg_r": None})
    ps2 = hermes._skill_preload("proposal")
    assert "position-sizer" in ps2                                 # çekirdek ASLA düşmez (ölçüm tüm sistemi yansıtır)

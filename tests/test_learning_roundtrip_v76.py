"""test_learning_roundtrip_v76.py — ÖĞRENME DÖNGÜSÜNÜN TAM TURU (2026-07-22, tur 76).

Dedektör bataryası yeşil ve her artefaktın TEK BAŞINA iyi biçimli olduğunu doğrulayabiliyor.
Doğrulayamadığı şey ÇOK ADIMLI PROTOKOL:

    kanıt → hipotez → kapı → ship (sürüm artar) → canlı ölçüm → rollback ya da kalıcı

Her adım ayrı ayrı test edilmişti; TURUN KENDİSİ hiç kanıtlanmamıştı. Döngü uçtan uca kırıksa ajan
sonsuza dek meşgul GÖRÜNÜR, hiçbir şey öğrenmez — ve yol boyunca her artefakt yine doğrulanır.

YÖNTEM. Kum havuzunda GERÇEK fonksiyonlar sürülür: `reflect.submit` (guard + kapı yasası + ship),
`versioning` (sürüm/karne/anlık görüntü), `memory` (defter), `rollback.evaluate_outcomes` (canlı
ölçüm), `run.bootstrap_v01`/`run.replay_seed`. İşlem gereken hiçbir yerde satır ELLE YAZILMAZ:
`backtest.replay` gerçek motorla, VCP biçimli sentetik barlar üzerinde koşar — şema (r_multiple,
regime, exit_reason, plan_id, skill_chain, mfe/mae, strategy_version) üretimin ta kendisidir.

TEK FİKSTÜR NOKTASI ve NEDENİ: kapının SAYILARI (`backtest.walk_forward` çıktısı) enjekte edilir.
Kapı YASASI (guard, marj, fold-çoğunluğu, kuyruk vetosu, teyit dilimi) gerçek kodla koşar; yalnız
walk-forward'ın döndürdüğü skorlar deterministik kılınır — bu dosyanın iddiası "kapı doğru
puanlıyor mu" değil, "kapı GEÇTİĞİNDE tur gerçekten kapanıyor mu, ve kötü bir ship geri alınabiliyor
mu". Depo bu deseni kendi testlerinde de kullanıyor (test_reflect_gaps_v47._wf).

BULGULAR. `test_defect_*` testleri ÜRETİM KODUNU DEĞİŞTİRMEZ: mevcut (kusurlu) davranışı çivilerler
ve beklenen davranışı adıyla yazarlar. Canlı uygulama koşuyor; öğrenme döngüsünün semantiğini bir
denetim turu sırasında tek taraflı değiştirmek operatörün kararıdır, denetçinin değil.
"""
from __future__ import annotations

import ast
import copy
import json
import pathlib

import numpy as np
import pandas as pd
import pytest
import yaml

from meridian import (backtest, config, guard, memory, obs, reflect, rollback,
                      score as score_mod, store, versioning)
from tests import wf_fixtures as wf

REPO = pathlib.Path(__file__).resolve().parent.parent
MERIDIAN = REPO / "meridian"
# Pencere BİR YIL: skorun getiri bileşeni bir ORANDIR (realized_30d), pencereyi uzatmak onu
# büyütmez ama düşüş (drawdown) için daha çok fırsat verir — kanıt tabanı sembol sayısıyla
# büyütülüyor, pencereyle değil.
REPLAY_START, REPLAY_END = "2022-01-03", "2022-12-30"

# Turu kapatan tek değişkenli hamle ve onun tersi. İkisi de bounds.yaml içinde, adım üstünde.
KNOB = "position_size_r"
SMALL, FULL = 0.1, 1.0          # ölçülen: küçük pozisyon popülasyonu ebeveyninden ~0.21 skor geride
# TOHUM DEĞERİ KAYNAKTAN OKUNUR, LİTERAL DEĞİL (v246-C · ROADMAP §2-30). `seeded` fikstürü v1'i
# `run.bootstrap_v01()` ile kurar, yani v1'in boyutu `config.default_strategy()`ten gelir. Burada
# 1,0 literali yazılıydı ve yedek canlıyla hizalanınca (1,0 → 0,5) rollback testi ÖLÇTÜĞÜ ŞEY
# yüzünden değil, TOHUMUN ADINI yanlış bildiği için kırmızıya döndü. Testin cümlesi bir SAYI değil
# bir DAVRANIŞ: "geri alma ebeveynin değerini geri getirir ve o değer sevk edilenden FARKLIDIR" —
# farklılık `!= SMALL` ile yerinde ölçülmeye devam ediyor. `FULL` DOKUNULMADI: o, sevk edilen
# hipotezin değeridir (bounds tavanı, tam pozisyon) ve tohumla aynı şey değildir.
TOHUM = config.default_strategy()["params"][KNOB]


# ----------------------------------------------------------------------------------------------
# SENTETİK AMA GERÇEKÇİ KANIT — gerçek motoru besleyecek VCP biçimli barlar.
# Rastgele yürüyüş işe yaramıyor: `evaluate_entry` 40 günlük zirvenin TAZE kırılımını, hacim
# genişlemesini, pivota yakınlığı ve taban-yüksekliği/ATR oranını BİRLİKTE arıyor — rastgele seri
# 4 yılda 3 işlem üretti. Bu üreteç ardışık VCP tabanları kurar ve her beşinci kırılımı BAŞARISIZ
# kılar (her kırılımın tuttuğu bir dünyada hiçbir parametre farkı ölçülemez).
#
# C11/C18 (0a4453f, 2026-08-02) replay'in giriş limitini CANLIYLA AYNI yasaya sıkılaştırdı: dolum
# artık silahlanma anında ölçülen ATR ile `min(0,5·ATR14, %1)` tavanının ÜSTÜNDE yazılamıyor.
# Eski fikstür bu yasayı geçemiyordu ÇÜNKÜ her barın açılışı KENDİ kapanışına eşitti — günlük
# hareketin TAMAMI gece boşluğunda oluyordu ve kırılım ertesi açılış tetiğin (= sinyal barının
# kapanışı) tam %1 üstüne düşüyordu. Ölçüldü: 66 silahlı planın 34'ü `entry_missed_limit`, 15'i
# `open_below_stop` ile kaçtı, kanıt tabanı 17 tamamlanmış işleme indi — `min_sample`=30 ALTI.
# Fikstür bu DÜRÜST icra modelinde min_sample'ı marjla aşacak şekilde büyütüldü (17 → 68); üç
# değişiklik, üçü de ÜRETİM DAVRANIŞINA DEĞİL sentetik dünyanın kendisine:
#   1. GEOMETRİ: açılış artık ÖNCEKİ kapanışın yanında doğuyor, high/low ikisini de kapsıyor.
#      Sistematik %1'lik gece boşluğu kalktı → limit tavanı artık kurgusal bir boşlukla değil
#      gerçek fiyat hareketiyle sınanıyor (ölçüldü: entry_rejects = {}).
#   2. KANIT HACMİ: sembol 8 → 16, kadans kısaldı (cycle 40+i) → aynı pencerede daha çok kurulum.
#   3. ÖLÇÜLEBİLİRLİK: taban derinliği ve koşu hızı büyüdü (depth .09→.16, run %1→%1,5) → ATR ve
#      dolayısıyla stop mesafesi ~%1,5'ten ~%2,2'ye çıktı. Bu şart: stop dar olunca 1R'lik
#      pozisyonun istediği notional %25 tavanına (broker.MAX_NOTIONAL_PCT) çarpıp kırpılıyor ve
#      `position_size_r` farkı skorda ERİYOR — yani turun ÖLÇTÜĞÜ düğme ölçülemez hâle geliyordu.
# ----------------------------------------------------------------------------------------------
def staircase_bars(n=800, seed=7, start="2021-01-04", cycle=48, base_days=40, depth=0.16,
                   pop=0.006, run=0.015, sigma=0.004, fail_every=5, fail_run=-0.019) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = np.zeros(n)
    vol = np.zeros(n)
    top = 100.0
    px = top
    for i in range(n):
        ph = i % cycle
        failing = (i // cycle) % fail_every == fail_every - 1
        if ph < base_days:                      # taban: `depth` kadar düşüş, daralarak zirveye dönüş
            frac = ph / max(1, base_days - 1)
            shape = -depth * np.sin(np.pi * frac) ** 1.4
            px = top * (1 + shape) * (1 + rng.normal(0, sigma * (1 - 0.75 * frac)))
            px = min(px, top * 0.998)           # taban İÇİNDE pivot asla delinmez (taze kırılım şartı)
            vol[i] = rng.uniform(0.75, 1.0) * 1_000_000
        elif ph == base_days:                   # kırılım: pivotun ~%0.6 üstü, hacim genişlemesiyle
            px = top * (1 + pop)
            vol[i] = rng.uniform(2.6, 3.2) * 1_000_000
        else:                                   # devam ya da (her `fail_every`. döngüde) başarısız kırılım
            px = px * (1 + (fail_run if failing else run) + rng.normal(0, sigma))
            vol[i] = rng.uniform(1.0, 1.5) * 1_000_000
            if ph == cycle - 1:
                top = px
        close[i] = px
    # Açılış ÖNCEKİ kapanışın yanında (gece boşluğu küçük), gün-içi hareket açılış→kapanış arasında;
    # high/low İKİSİNİ DE kapsar. Eskiden `open = close·(1+ε)` idi: bar tutarsızdı (açılış high'ın
    # üstüne çıkabiliyordu) ve günlük hareketin tamamı boşluğa yığıldığı için hem dolumlar limite
    # takılıyor hem çıkışlar `*_gap` dalından geliyordu — icra yasasının sınanmadığı bir dünya.
    prev_close = np.concatenate(([close[0]], close[:-1]))
    openp = prev_close * (1 + rng.normal(0, 0.0008, n))
    high = np.maximum(close, openp) * (1 + np.abs(rng.normal(0, 0.0012, n)))
    low = np.minimum(close, openp) * (1 - np.abs(rng.normal(0, 0.0012, n)))
    return pd.DataFrame({"date": pd.bdate_range(start, periods=n), "open": openp,
                         "high": high, "low": low, "close": close, "volume": vol})


def _index_bars(n=800) -> pd.DataFrame:
    rng = np.random.default_rng(3)
    c = 400.0 * np.cumprod(1 + 0.0004 + rng.normal(0, 0.006, n))
    return pd.DataFrame({"date": pd.bdate_range("2021-01-04", periods=n), "open": c,
                         "high": c * 1.002, "low": c * 0.998, "close": c,
                         "volume": np.full(n, 5e7)})


# backtest.SECTORS'ta bulunan GERÇEK semboller — sektör tavanı kapısı da kendi yolundan koşsun.
# 8 → 16 (yukarıdaki 2. madde): sektör dağılımı geniş tutuldu ki `max_sector_exposure_pct` kapısı
# kanıt tabanını tek sektöre sıkışmış bir popülasyondan üretmesin.
TICKERS = ["AAPL", "MSFT", "NVDA", "JPM", "UNH", "XOM", "HD", "CAT",
           "PG", "DIS", "NEE", "AMT", "LIN", "GS", "MRK", "LOW"]
BARS = {t: staircase_bars(seed=11 * i + 5, cycle=40 + i, base_days=32 + i)
        for i, t in enumerate(TICKERS)}
INDEX = _index_bars()

_TRADES: dict = {}          # param-seti → gerçek replay işlemleri (modül ömrü boyunca BİR kez)


def _replay_trades(overrides: dict) -> list[dict]:
    """GERÇEK `backtest.replay` ile işlem defteri üret — elle satır yazmak yerine motorun kendisi."""
    key = json.dumps(overrides, sort_keys=True)
    if key not in _TRADES:
        params = dict(config.default_strategy()["params"])
        params.update(overrides)
        res = backtest.replay(params, BARS, INDEX, config.goal(), REPLAY_START, REPLAY_END,
                              strategy_version=1)
        _TRADES[key] = json.loads(json.dumps(store.sanitize(res.trades)))
    return copy.deepcopy(_TRADES[key])


def _tagged(overrides: dict, version: int) -> list[dict]:
    """Aynı gerçek işlemler, `strategy_version` damgası değişmiş. `replay` bu alanı ARGÜMANDAN
    birebir damgalar (tam tur testi bunu ayrıca doğrular) — yani bu, aynı parametrelerle o sürüm
    numarası verilerek koşulmuş bir replay'in çıktısıyla özdeştir, ikinci bir 40 saniye olmadan."""
    rows = _replay_trades(overrides)
    for r in rows:
        r["strategy_version"] = version
        r["id"] = f"{r['id']}-v{version}"          # defterde kimlikler çakışmasın
    return rows


# ----------------------------------------------------------------------------------------------
# Kum havuzu: v1 canlı, anlık görüntüsüyle. Hiçbir test CANLI state'e dokunmaz (conftest bekçisi).
# ----------------------------------------------------------------------------------------------
def _reset_caches() -> None:
    reflect._INC_CACHE.clear()
    reflect._PROBE_CACHE.clear()
    reflect._INC_DISK_LOADED = False
    reflect._PROBE_DISK_LOADED = False


@pytest.fixture
def seeded(sandbox_state):
    from meridian import run
    _reset_caches()
    config.reload_config()
    run.bootstrap_v01()                 # GERÇEK önyükleme: strategy.yaml v1 + history/v0001.yaml
    yield sandbox_state
    _reset_caches()
    config.reload_config()


def _seed_v1_with(**overrides) -> dict:
    """v1'i belirli bir taban parametreyle kur (operatörün temkinli tohumu) — gerçek yazım yolu."""
    strat = config.default_strategy()
    strat["params"].update(overrides)
    config.dump_yaml(strat, config.strategy_path())
    versioning.snapshot(strat)
    return copy.deepcopy(strat)


def _wf(oos: float, fold_avgs=(0.5, 0.5, 0.5), tail=None) -> dict:
    """walk_forward'ın kapıya giden ŞEKLİ — artık MERKEZİ FABRİKAdan (tests.wf_fixtures).
    Eskiden dilimsiz bir sözlük döndürüyordu → has_slices False → kapı ERİŞİLEMEZ legacy nokta-marj
    dalına düşüyordu; bu dosyanın koştuğu şey ürünün GERÇEK olasılıksal + teyit yolu değildi. Köprü
    verilen oos/fold_avgs/tail değerlerini KORUR (kapı metrikleri aynen sürer) ama altına GERÇEK
    sentetik Search/Confirm dilimleri döşer → has_slices True → kapı olasılıksal yolu koşar.
    İmza korunur; fold_avgs -> folds=[(30,r)] köprüsü fabrikaya."""
    return wf.wf_from_scores(oos, folds=[(30, r) for r in fold_avgs], tail=tail, holdout=oos)


def _gate(monkeypatch, inc: dict, cand: dict) -> None:
    """Sürüm numarasına göre incumbent/candidate walk-forward'ı sabitle (depo deseni)."""
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
    live = int(config.load_strategy().get("version", 1))

    def _wfx(*a, **k):
        return dict(cand) if int(k.get("strategy_version", live)) != live else dict(inc)

    monkeypatch.setattr(backtest, "walk_forward", _wfx)
    reflect._INC_CACHE.clear()


def _pass_gate(monkeypatch):
    _gate(monkeypatch, _wf(0.10, (0.2, 0.2, 0.2)), _wf(0.30, (0.6, 0.6, 0.6)))


def _events() -> list[dict]:
    return store.read_jsonl(obs._EVENTS)


def _enclosing_fn(tree, node) -> str:
    best = None
    for a in ast.walk(tree):
        if isinstance(a, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and a.lineno <= node.lineno <= (a.end_lineno or a.lineno):
            if best is None or a.lineno > best.lineno:
                best = a
    return best.name if best else "<module>"


# ==============================================================================================
# 1. TAM TUR — kanıt → hipotez → kapı → ship → canlı ölçüm → TERMİNAL
# ==============================================================================================
def test_roundtrip_evidence_to_terminal_outcome(seeded, monkeypatch):
    """TEK testte tam tur: her adımın ÇIKTISI bir sonraki adımın GİRDİSİ, hiçbir aşama atlanmıyor."""
    goal = config.goal()
    goal_before = (config.STATE / "goal.yaml").read_bytes()
    bounds_before = (config.STATE / "bounds.yaml").read_bytes()

    # v1: temkinli taban (küçük pozisyon). Turun öğreneceği şey tam olarak bu düğme.
    v1 = _seed_v1_with(**{KNOB: SMALL})

    # --- 1. KANIT: v1 altında GERÇEK motorla üretilmiş işlem defteri --------------------------
    v1_trades = _tagged({KNOB: SMALL}, 1)
    assert len(v1_trades) >= int(goal["min_sample"]), \
        f"kanıt tabanı min_sample altında ({len(v1_trades)}) — tur zaten burada tıkanır"
    store.write_jsonl("trades.jsonl", v1_trades)

    # --- 2. HİPOTEZ: gerçek önerici tek değişkenli, sınır içi bir öneri üretir -----------------
    auto = reflect.propose_deterministic()
    assert auto.get("changes") is None and auto["variable"] and auto["new"] is not None
    spec = config.bounds()[str(auto["variable"]).split("@", 1)[0]]
    assert spec["min"] <= auto["new"] <= spec["max"], "önerici sınır dışına çıktı"

    # Turu KAPANIR kılan hamleyi açıkça seçiyoruz: önericinin kendi hamlesi bu sentetik evrende
    # nötr kalıyor ve nötr sonuç hipotezi 'live'de asılı bırakır — tam turun terminali `promoted`.
    prop = {"variable": KNOB, "new": FULL, "rationale": "tam tur kanıtı: tam pozisyona geç",
            "predicted_direction": "improve_oos_score", "predicted_delta": 0.05,
            "confidence": 0.5, "source": "deterministic"}

    # --- 3. KAPI + 4. SHIP --------------------------------------------------------------------
    _pass_gate(monkeypatch)
    res = reflect.submit(dict(prop), goal)
    assert res["status"] == "shipped", f"kapı geçildi ama ship olmadı: {res}"
    v2 = res["version"]

    strat = config.load_strategy()
    assert int(strat["version"]) == v2 > 1 and int(strat["parent"]) == 1
    assert strat["params"][KNOB] == FULL
    moved = [k for k in set(v1["params"]) | set(strat["params"])
             if v1["params"].get(k) != strat["params"].get(k)]
    assert moved == [KNOB], f"ship TEK düğmeyi oynatmalı, oynayan: {moved}"

    snap = config.HISTORY / f"v{v2:04d}.yaml"
    assert snap.exists(), "sürüm arttı ama anlık görüntü yok — geri alınamaz bir ship"
    assert yaml.safe_load(snap.read_text())["params"] == strat["params"]

    sb = versioning.scoreboard()
    assert sb["current_version"] == v2
    assert sb["versions"][str(v2)]["parent"] == 1, "karnede soy zinciri yok"
    assert sb["versions"][str(v2)]["backtest_oos"] == 0.30
    assert sb["versions"][str(v2)]["changed_variable"] == KNOB
    assert sb["versions"][str(v2)].get("live_since")
    assert sb["versions"]["1"]["backtest_oos"] == 0.10, "ebeveynin kapı skoru karneye yazılmadı"

    hyp = memory.all_hypotheses()[-1]
    assert hyp["status"] == "live" and hyp["version_to"] == v2 and hyp["version_from"] == 1
    assert hyp["backtest"]["candidate_oos"] == 0.30 and hyp["predicted_delta"] is not None
    assert hyp["realized_delta"] is None if "realized_delta" in hyp else True

    # --- 5. CANLI ÖLÇÜM: v2 altında GERÇEK motorla biriken işlemler ----------------------------
    v2_trades = _replay_trades({KNOB: FULL})
    for t in v2_trades:                     # replay'in damgasını doğrula, SONRA sürüme bağla
        assert t["strategy_version"] == 1
        t["strategy_version"] = v2
        t["id"] = f"{t['id']}-v{v2}"
    assert len(v2_trades) >= int(goal["min_sample"])
    store.write_jsonl("trades.jsonl", v1_trades + v2_trades)

    par_score = score_mod.score(v1_trades, goal)
    cur_score = score_mod.score(v2_trades, goal)
    assert cur_score - par_score > float(goal["rollback_if_worse_by"]), \
        f"senaryo kurgusu bozuk: delta {cur_score - par_score} terfi eşiğini geçmiyor"

    # --- 6. SONUÇ: hipotez TERMİNALE ulaşır ---------------------------------------------------
    out = rollback.evaluate_outcomes(goal)
    assert out is not None and out["rolled_back"] is False and out["promoted"] is True

    hyp = memory.all_hypotheses()[-1]
    assert hyp["status"] == "promoted", f"hipotez terminale ulaşmadı: {hyp['status']}"
    assert hyp["realized_delta"] == pytest.approx(round(cur_score - par_score, 4), abs=1e-4)
    assert hyp["calibration_hit"] is True and hyp.get("outcome_ts")
    assert hyp.get("market_regime"), "sonucun ÖLÇÜLDÜĞÜ rejim kayıtlı değil"
    assert hyp["realized_detail"]["n"] == len(v2_trades)

    sb = versioning.scoreboard()
    assert sb["versions"][str(v2)]["live_score"] == cur_score
    assert sb["versions"][str(v2)]["promoted"] is True

    lessons = (config.STATE / "lessons.md").read_text()
    assert KNOB in lessons and "Confirmed edges" in lessons

    # --- 7. MANDAL: terfi tek yönlü, sonuç yeniden yazılmaz ------------------------------------
    again = rollback.evaluate_outcomes(goal)
    assert memory.all_hypotheses()[-1]["realized_delta"] == hyp["realized_delta"]
    assert memory.all_hypotheses()[-1]["status"] == "promoted"
    assert again is not None

    # --- DOKUNULMAZLIK: tur boyunca sözleşme dosyaları bit-bit aynı ---------------------------
    assert (config.STATE / "goal.yaml").read_bytes() == goal_before
    assert (config.STATE / "bounds.yaml").read_bytes() == bounds_before


# ==============================================================================================
# 2. ROLLBACK — gerçekten geri getirir, NEDENİNİ yazar ve ping-pong yapamaz
# ==============================================================================================
def test_rollback_restores_parent_records_why_and_cannot_pingpong(seeded, monkeypatch):
    goal = config.goal()
    v1_params = copy.deepcopy(config.load_strategy()["params"])
    good = _tagged({}, 1)
    store.write_jsonl("trades.jsonl", good)

    prop = {"variable": KNOB, "new": SMALL, "rationale": "kasıtlı kötü sürüm",
            "predicted_direction": "improve_oos_score", "predicted_delta": 0.05,
            "confidence": 0.5, "source": "deterministic"}
    _pass_gate(monkeypatch)
    res = reflect.submit(dict(prop), goal)
    assert res["status"] == "shipped"
    v2 = res["version"]
    assert config.load_strategy()["params"][KNOB] == SMALL

    bad = _tagged({KNOB: SMALL}, v2)
    store.write_jsonl("trades.jsonl", good + bad)
    par_score, cur_score = score_mod.score(good, goal), score_mod.score(bad, goal)
    assert cur_score < par_score - float(goal["rollback_if_worse_by"]), \
        f"senaryo kurgusu bozuk: delta {cur_score - par_score} rollback eşiğini geçmiyor"

    out = rollback.evaluate_outcomes(goal)
    assert out and out.get("rolled_back_from") == v2 and out["to"] == 1

    # (a) EBEVEYN PARAMETRELERİ GERÇEKTEN GERİ GELDİ
    now = config.load_strategy()
    assert int(now["version"]) == 1 and now["params"] == v1_params
    assert now["params"][KNOB] == TOHUM != SMALL

    # (b) NEDENİ KAYITLI: defter + karne + alarm
    hyp = [h for h in memory.all_hypotheses() if h.get("version_to") == v2][0]
    assert hyp["status"] == "rolled_back" and hyp["realized_delta"] < 0
    assert hyp["realized_detail"]["cur_score"] == cur_score
    assert hyp["realized_detail"]["par_score"] == par_score
    sb = versioning.scoreboard()
    assert sb["versions"][str(v2)]["rolled_back"] is True
    assert sb["versions"][str(v2)]["live_score"] == cur_score
    assert sb["versions"]["1"]["reinstated"] is True
    assert any(e.get("alarm") == obs.ALARM_ROLLBACK for e in _events()), \
        "geri alma SESSİZ oldu — operatöre giden alarm yok"

    # (c) KANIT SİLİNMEZ: ölü sürümün anlık görüntüsü ve işlemleri yerinde durur
    assert (config.HISTORY / f"v{v2:04d}.yaml").exists()
    assert sum(1 for t in store.read_jsonl("trades.jsonl")
               if t.get("strategy_version") == v2) == len(bad)

    # (d) PING-PONG YASAK: aynı değişiklik yeniden ship edilemez
    again = reflect.submit(dict(prop), goal)
    assert again["status"] == "rejected_by_guard"
    assert any("already tried and failed" in r for r in again["reasons"]), again["reasons"]
    assert int(config.load_strategy()["version"]) == 1

    # (e) Deterministik önerici de aynı ölü hamleyi seçmez
    auto = reflect.propose_deterministic()
    assert not (auto["variable"] == KNOB and auto["new"] == SMALL)

    # (f) SÜRÜM NUMARASI ASLA YENİDEN KULLANILMAZ — yeni ship ölü numarayı diriltmez
    _pass_gate(monkeypatch)
    res3 = reflect.submit({"variable": "exit.time_stop_days", "new": 16,
                           "rationale": "geri almadan sonraki ilk ship"}, goal)
    assert res3["status"] == "shipped" and res3["version"] > v2
    assert (config.HISTORY / f"v{res3['version']:04d}.yaml").exists()
    assert yaml.safe_load((config.HISTORY / f"v{v2:04d}.yaml").read_text())["params"][KNOB] == SMALL


def test_rollback_is_loud_when_the_parent_snapshot_is_missing(seeded, monkeypatch):
    """Geri almanın BAŞARISIZLIĞI, geri almanın kendisi kadar yüksek sesli olmalı: eksik anlık
    görüntü sessiz bir uyarıya gömülürse kötü sürüm CANLI kalır ve kimse fark etmez."""
    goal = config.goal()
    good = _tagged({}, 1)
    store.write_jsonl("trades.jsonl", good)
    _pass_gate(monkeypatch)
    res = reflect.submit({"variable": KNOB, "new": SMALL, "rationale": "kötü sürüm"}, goal)
    v2 = res["version"]
    store.write_jsonl("trades.jsonl", good + _tagged({KNOB: SMALL}, v2))
    (config.HISTORY / "v0001.yaml").unlink()                 # ebeveyn anlık görüntüsü kayboldu

    out = rollback.evaluate_outcomes(goal)
    assert out and out.get("error") == "parent snapshot missing" and out["attempted"] == v2
    assert int(config.load_strategy()["version"]) == v2, "rapor dürüst: kötü sürüm hâlâ canlı"
    assert any(e.get("alarm") == obs.ALARM_ROLLBACK and "GERİ ALMA BAŞARISIZ" in str(e.get("message"))
               for e in _events()), "başarısız geri alma sessiz kaldı"


# ==============================================================================================
# 3. one_variable_only — DÜŞMANCA denemeler
# ==============================================================================================
def test_one_variable_only_rejects_multi_knob_proposals(seeded):
    b, g, p = config.bounds(), config.goal(), config.load_strategy()["params"]
    v = guard.validate_change({"changes": {"entry.min_score": 65, "stop_loss_atr_mult": 2.5}},
                              p, b, g, [], 0)
    assert not v.ok and "one_variable_only" in v.reasons[0]
    assert not guard.validate_change({"changes": {}}, p, b, g, [], 0).ok


def test_one_variable_only_a_second_knob_smuggled_beside_changes_is_ignored(seeded, monkeypatch):
    """`changes` TEK düğme taşırken yanına `variable/new` iliştirmek ikinci bir düğme oynatmamalı."""
    before = copy.deepcopy(config.load_strategy()["params"])
    _pass_gate(monkeypatch)
    res = reflect.submit({"changes": {"entry.min_score": 65},
                          "variable": "stop_loss_atr_mult", "new": 3.0,
                          "rationale": "iki düğme kaçakçılığı"}, config.goal())
    assert res["status"] == "shipped"
    after = config.load_strategy()["params"]
    moved = [k for k in set(before) | set(after) if before.get(k) != after.get(k)]
    assert moved == ["entry.min_score"], f"birden fazla düğme oynadı: {moved}"
    assert after["stop_loss_atr_mult"] == before["stop_loss_atr_mult"]
    assert memory.all_hypotheses()[-1]["variable"] == "entry.min_score"


def test_one_variable_only_holds_for_regime_knobs_too(seeded):
    """`var@regime` ship'i düz params'a DOKUNMAZ ve yalnız o rejimin haritasına tek anahtar yazar."""
    cur = config.load_strategy()
    child = versioning.bump(cur, "entry.min_score@chop", 65, note="rejim düğmesi")
    assert child["params"] == cur["params"]
    before = {(r, k) for r, m in (cur.get("params_by_regime") or {}).items() for k in m}
    after = {(r, k) for r, m in child["params_by_regime"].items() for k in m}
    assert after - before == {("chop", "entry.min_score")}
    assert child["params_by_regime"]["chop"]["entry.min_score"] == 65


def test_one_variable_only_is_syntactic_not_semantic(seeded):
    """DÜRÜSTLÜK SINIRI (bulgu, kusur değil): yasa PARAMETRE SAYISINA bakar, ETKİYE değil.
    `entry.w_prox` tek bir düğmedir ama bileşik skorun ağırlığını değiştirir; yani `entry.min_score`
    eşiğinin ANLAMINI gevşetir. Diskteki değişiklik yine tek yapraktır. Bu testin işi sınırı yazılı
    kılmak: 'tek değişken' semantik izolasyon VAAT ETMEZ; o güvence yalnız OOS kapısından gelir."""
    b, g, p = config.bounds(), config.goal(), config.load_strategy()["params"]
    assert guard.validate_change({"variable": "entry.w_prox", "new": 0.40}, p, b, g, [], 0).ok
    child = versioning.bump(config.load_strategy(), "entry.w_prox", 0.40)
    moved = [k for k in child["params"] if child["params"][k] != p.get(k)]
    assert moved == ["entry.w_prox"]
    assert child["params"]["entry.min_score"] == p["entry.min_score"]   # eşik SAYISI değişmedi


def test_only_known_call_sites_may_write_a_strategy_yaml(seeded):
    """`strategy.yaml`'a (ya da bir sürüm anlık görüntüsüne) yazan her yol kapıyı atlama fırsatıdır.
    Bilinen ve gerekçeli beş yol dışında bir altıncısı sessizce eklenemez."""
    sites = set()
    for f in sorted(MERIDIAN.rglob("*.py")):
        tree = ast.parse(f.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and node.func.attr == "dump_yaml":
                sites.add(f"{f.name}:{_enclosing_fn(tree, node)}")
    assert sites == {"versioning.py:snapshot", "versioning.py:commit", "versioning.py:revert_to",
                     "run.py:bootstrap_v01", "sprint.py:_reset_sandbox_state"}, \
        f"strateji YAML'ına yazan yeni bir yol var (kapı atlanabilir): {sorted(sites)}"


def test_revert_to_is_only_reachable_from_rollback_with_the_immediate_parent(seeded):
    """`revert_to(n)` KEYFİ bir ataya dönebilir — o da tek hamlede birçok düğmeyi oynatmak demek.
    Tek çağıran rollback ve argümanı ebeveynin ta kendisi olmalı."""
    sites = []
    for f in sorted(MERIDIAN.rglob("*.py")):
        tree = ast.parse(f.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and node.func.attr == "revert_to":
                arg = node.args[0] if node.args else None
                sites.append((f.name, getattr(arg, "id", None)))
    assert sites == [("rollback.py", "parent")], f"beklenmeyen revert_to çağrısı: {sites}"


# ==============================================================================================
# 4. SINIRLAR TAVANDIR — sessizce kırpılmaz, REDDEDİLİR
# ==============================================================================================
@pytest.mark.parametrize("var,val,recorded,needle", [
    ("stop_loss_atr_mult", 9.9, 9.9, "out of range"),      # üst sınır üstü
    ("stop_loss_atr_mult", 0.1, 0.1, "out of range"),      # alt sınır altı
    ("entry.min_score", 61.5, 61, "must be int"),          # tür ihlali
    ("stop_loss_atr_mult", 2.05, 2.05, "off-step"),        # adım dışı
])
def test_out_of_bounds_is_refused_never_clipped(seeded, monkeypatch, var, val, recorded, needle):
    before = copy.deepcopy(config.load_strategy())
    _gate(monkeypatch, _wf(0.10), _wf(0.90))          # kapı GEÇSİN: reddi guard vermeli
    res = reflect.submit({"variable": var, "new": val, "rationale": "sınır denemesi"}, config.goal())
    assert res["status"] == "rejected_by_guard"
    assert any(needle in r for r in res["reasons"]), res["reasons"]
    assert config.load_strategy() == before, "reddedilen öneri canlı stratejiyi değiştirdi"
    hyp = memory.all_hypotheses()[-1]
    assert hyp["status"] == "rejected_by_guard" and hyp["version_to"] is None
    assert hyp["new"] == pytest.approx(recorded), \
        "reddedilen değer deftere KIRPILMIŞ yazıldı — sonraki denemeler yanlış tarihi okur"


def test_an_unknown_knob_is_refused(seeded, monkeypatch):
    _gate(monkeypatch, _wf(0.10), _wf(0.90))
    res = reflect.submit({"variable": "uydurma_dugme", "new": 1.0}, config.goal())
    assert res["status"] == "rejected_by_guard"
    assert any("not a tunable" in r for r in res["reasons"])
    assert "uydurma_dugme" not in config.load_strategy()["params"]


def test_bounds_edges_are_inclusive_and_on_step(seeded):
    b, g, p = config.bounds(), config.goal(), config.load_strategy()["params"]
    spec = b["stop_loss_atr_mult"]
    assert guard.validate_change({"variable": "stop_loss_atr_mult", "new": spec["max"]},
                                 p, b, g, [], 0).ok
    assert guard.validate_change({"variable": "stop_loss_atr_mult", "new": spec["min"]},
                                 p, b, g, [], 0).ok


def test_every_bounds_entry_stays_inside_the_immutable_risk_limits(seeded):
    """Sınırlar TAVANDIR ama sınırların kendisi de goal.limits'in ALTINDA kalmalı. `position_size_r`
    tavanı `limits.max_position_r`i aşarsa, guard'ın kabul ettiği bir hipotez risk zarfını deler."""
    b, lim = config.bounds(), config.goal()["limits"]
    assert b["position_size_r"]["max"] <= float(lim["max_position_r"])
    assert b["position_size_r"]["min"] > 0


def test_the_proposer_never_emits_a_value_outside_bounds(seeded):
    for explore in (False, True):
        prop = reflect.propose_deterministic(explore=explore)
        spec = config.bounds()[str(prop["variable"]).split("@", 1)[0]]
        assert spec["min"] <= prop["new"] <= spec["max"]


def test_garbage_and_nan_are_rejected_with_a_reason_not_an_exception(seeded):
    """DÜZELTİLDİ (2026-07-22, aynı gün). Eskiden sayıya çevrilemeyen ya da NaN bir değer guard'ı
    ValueError ile PATLATIYORDU; `reflect.submit` bunu yakalamıyor, çağıran genel bir `except`e
    düşürüyordu ve defterde SATIR KALMIYORDU — yani deponun kendi yasası ("değerlendirilen HER
    öneri KAYITLI bir terminale ulaşır") ihlal ediliyordu, öneri buharlaşıyordu.

    Daha incesi: NaN aralık kontrolünü SESSİZCE geçiyordu (`nan<lo` ve `nan>hi` ikisi de False);
    onu yakalayan tek şey adım kontrolündeki `round()`un tesadüfen çökmesiydi — yani NaN'ı durduran
    bir KURAL değil, bir HATAYDI. Adımsız bir düğme eklense NaN sınırların içinden geçerdi.

    Artık ikisi de gerekçeli RET: `Verdict(ok=False)`, açık sebep, terminal kayıt."""
    b, g, p = config.bounds(), config.goal(), config.load_strategy()["params"]
    lo, hi = b["stop_loss_atr_mult"]["min"], b["stop_loss_atr_mult"]["max"]
    assert not (float("nan") < lo) and not (float("nan") > hi), \
        "NaN hâlâ aralık kontrolünü geçiyor — açık ret şart"
    for bad, beklenen in ((float("nan"), "sonlu"), ("abc", "sayı değil"), (float("inf"), "sonlu")):
        v = guard.validate_change({"variable": "stop_loss_atr_mult", "new": bad}, p, b, g, [], 0)
        assert v.ok is False, f"{bad!r} kabul edildi"
        assert any(beklenen in r for r in v.reasons), f"{bad!r} gerekçesi anlaşılır değil: {v.reasons}"
    # POZİTİF KONTROL: geçerli bir değer hâlâ kabul ediliyor (ret her şeyi süpürmüyor)
    ok = guard.validate_change({"variable": "stop_loss_atr_mult", "new": float(lo)}, p, b, g, [], 0)
    assert ok.ok is True, f"geçerli değer de reddedildi: {ok.reasons}"


# ==============================================================================================
# 5. DOKUNULMAZLIK — goal.yaml / bounds.yaml
# ==============================================================================================
def test_no_code_path_writes_goal_or_bounds(seeded):
    """Kaynak taraması: `goal.yaml`/`bounds.yaml` hiçbir YAZMA çağrısının hedefi olamaz."""
    write_fns = {"dump_yaml", "write_text", "write_bytes", "write_json", "write_jsonl",
                 "append_jsonl", "safe_dump", "dump", "copy", "copy2", "copyfile", "copytree",
                 "unlink", "rename", "replace"}
    offenders = []
    for f in sorted(MERIDIAN.rglob("*.py")):
        src = f.read_text()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.attr if isinstance(node.func, ast.Attribute) \
                else getattr(node.func, "id", "")
            blob = " ".join(ast.dump(a) for a in list(node.args)
                            + [k.value for k in node.keywords])
            hit = "goal.yaml" in blob or "bounds.yaml" in blob
            if name in write_fns and hit:
                offenders.append(f"{f.name}:{node.lineno}:{name}")
            if name == "open" and hit and len(node.args) > 1 \
                    and isinstance(node.args[1], ast.Constant) \
                    and any(m in str(node.args[1].value) for m in ("w", "a", "+", "x")):
                offenders.append(f"{f.name}:{node.lineno}:open")
    assert offenders == [], f"goal/bounds YAZMA yolu var: {offenders}"


@pytest.mark.parametrize("key", sorted(guard.GOAL_KEYS | guard.LIMIT_KEYS))
def test_guard_refuses_every_immutable_key(seeded, key):
    b, g, p = config.bounds(), config.goal(), config.load_strategy()["params"]
    assert not guard.validate_change({"variable": key, "new": 1}, p, b, g, [], 0).ok
    assert not guard.validate_change({"variable": f"{key}@chop", "new": 1}, p, b, g, [], 0).ok, \
        f"'{key}' @regime son ekiyle dokunulmazlığını kaybediyor"
    assert not guard.validate_change({"variable": f"limits.{key}", "new": 1}, p, b, g, [], 0).ok


def test_immutables_survive_a_full_ship_and_rollback_cycle(seeded, monkeypatch):
    goal_b = (config.STATE / "goal.yaml").read_bytes()
    bounds_b = (config.STATE / "bounds.yaml").read_bytes()
    good = _tagged({}, 1)
    store.write_jsonl("trades.jsonl", good)
    _pass_gate(monkeypatch)
    res = reflect.submit({"variable": KNOB, "new": SMALL, "rationale": "dokunulmazlık turu"},
                         config.goal())
    assert res["status"] == "shipped"
    store.write_jsonl("trades.jsonl", good + _tagged({KNOB: SMALL}, res["version"]))
    assert rollback.evaluate_outcomes(config.goal())
    assert (config.STATE / "goal.yaml").read_bytes() == goal_b
    assert (config.STATE / "bounds.yaml").read_bytes() == bounds_b


def test_the_in_memory_contract_is_immutable_too(seeded):
    """DÜZELTİLDİ (2026-07-22, aynı gün). `goal()`/`bounds()` `lru_cache`liydi ve AYNI sözlüğü geri
    veriyordu: herhangi bir modül `goal()["min_sample"] = 1` yazınca sonraki HER okuyucu — kapı,
    rollback eşiği, aylık kota — o değeri görüyordu. Dosyada değişiklik yok, alarm yok, iz yok.
    "Değişmez sözleşme" yalnız DOSYA için geçerliydi; bellekteki kopya serbestti. Operatörün
    sözleşmesi ancak süreç ömrü boyunca da savunulursa sözleşmedir. Artık derin kopya."""
    assert config.goal() is not config.goal(), "hâlâ aynı nesne paylaşılıyor"
    g = config.goal()
    original = g["min_sample"]
    g["min_sample"] = 1                                    # sözleşmeyi bellekte bozmayı DENE
    assert config.goal()["min_sample"] == original, "bellekteki mutasyon sonraki okuyucuya SIZDI"
    b = config.bounds()
    b["entry.min_score"]["max"] = 999                      # sandbox tavanını yükseltmeyi DENE
    assert config.bounds()["entry.min_score"]["max"] != 999, "bounds mutasyonu SIZDI"
    assert yaml.safe_load((config.STATE / "goal.yaml").read_text())["min_sample"] == original


# ==============================================================================================
# 6. ÖĞRENME GEÇMİŞİ — soy zinciri sessizce kaybolamaz
# ==============================================================================================
def test_update_scoreboard_merges_and_never_drops_a_sibling_version(seeded):
    versioning.update_scoreboard(1, backtest_oos=0.10, source="operator_override", parent=None)
    versioning.update_scoreboard(2, backtest_oos=0.30, parent=1, live_score=0.25)
    versioning.update_scoreboard(3, backtest_oos=0.40, parent=2)
    versioning.update_scoreboard(2, promoted=True)          # kısmi güncelleme
    sb = versioning.scoreboard()
    assert set(sb["versions"]) == {"1", "2", "3"}
    assert sb["versions"]["2"]["live_score"] == 0.25 and sb["versions"]["2"]["promoted"] is True
    assert sb["versions"]["1"]["source"] == "operator_override"
    assert sb["versions"]["3"]["parent"] == 2


def test_next_version_outruns_scoreboard_and_history_even_after_a_rollback(seeded):
    versioning.update_scoreboard(7, backtest_oos=0.1)
    config.dump_yaml({"version": 9, "params": {}}, config.HISTORY / "v0009.yaml")
    assert versioning._next_version({"version": 1}) == 10


# OKUMA ERİŞİMCİLERİ — aşağıdaki tarayıcının alt-ağaç budaması bunlarda durur.
_KARNE_OKUMA_ERISIMCILERI = ("read_json", "read_jsonl", "mtime")


def _karneyi_ham_yaziyor_mu(node: ast.Call) -> bool:
    """`node` alt-ağacında 'scoreboard.json' OKUMA YOLU DIŞINDA geçiyor mu?

    DÜZELTİLDİ (2026-08-13, otoriter suite bulgusu). Eski tarayıcı iki adımlıydı: (1) çağrının
    ADI `read_json` ise atla, (2) değilse `ast.walk(node)` ile alt-ağacın TAMAMINDA sabiti ara.
    Bu iki adım birbiriyle çelişiyordu — muafiyet yalnız okumanın EN DIŞTAKİ çağrı olduğu hâlde
    tutuyor, okuma başka bir çağrıyla SARMALANDIĞI anda kayboluyordu. v239'un `divergence`
    dedektörü (`watchdog.EQUIVALENT_TRUTHS["strateji_surumu"]`) tam bu şekli yazdı:
        lambda: int((store.read_json("scoreboard.json", {}) or {})["current_version"])
    Dıştaki `int(...)` çağrısının adı `read_json` DEĞİL, ama alt-ağacında sabit VAR → tarayıcı
    bir OKUMAYI ham yazım sanıp `watchdog.py`yi kümeye ekledi.
    ÖLÇÜLDÜ, VARSAYILMADI: `meridian/` taraması watchdog'da tek geçiş verdi (satır 2077) ve o
    geçiş `store.read_json`dur; `store.write_json("scoreboard.json", …)` biçiminde bir yazım
    watchdog'da YOKTUR. Dedektör okur, yazmaz — dolayısıyla doğru düzeltme PİNİ GENİŞLETMEK
    DEĞİLDİR: `watchdog.py`yi kümeye yazmak hem yanlış bir olgu ilan eder hem de yarın gerçek bir
    ham yazım oraya girerse bekçiyi kör bırakırdı. Muafiyet SARMALAMAYA DAYANIKLI hâle getirildi:
    alt-ağaç gezilirken okuma çağrılarının kökleri BUDANIR.
    KÜME DEĞİŞMEDİ — bu turda ham yazan modül seti aynıdır (dört modül)."""
    yigin = [node]
    while yigin:
        n = yigin.pop()
        if isinstance(n, ast.Constant) and n.value == "scoreboard.json":
            return True
        for c in ast.iter_child_nodes(n):
            if isinstance(c, ast.Call):
                ad = c.func.attr if isinstance(c.func, ast.Attribute) \
                    else getattr(c.func, "id", "")
                if ad in _KARNE_OKUMA_ERISIMCILERI:
                    continue                 # OKUMA alt-ağacı budandı — sarmalayıcı yanılmasın
            yigin.append(c)
    return False


def test_only_known_call_sites_write_the_scoreboard_wholesale(seeded):
    """SAHİPLİK: karneyi `versioning.update_scoreboard` (BİRLEŞTİRİR) dışında tam sözlükle yazan
    her yol soy zincirini tek hamlede silebilir. Bugün üç böyle yol var; dördüncüsü sessizce
    eklenemesin. Tarayıcının okuma muafiyeti için bkz. `_karneyi_ham_yaziyor_mu` (2026-08-13)."""
    raw = set()
    for f in sorted(MERIDIAN.rglob("*.py")):
        tree = ast.parse(f.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = node.func.attr if isinstance(node.func, ast.Attribute) \
                else getattr(node.func, "id", "")
            if name in _KARNE_OKUMA_ERISIMCILERI:
                continue
            if _karneyi_ham_yaziyor_mu(node):
                raw.add(f.name)
    assert raw == {"versioning.py", "run.py", "sprint.py", "mutation.py"}, \
        f"karneyi ham yazan modül kümesi değişti: {sorted(raw)}"


def test_karne_tarayicisi_sarmalanmis_okumayi_yazim_SANMAZ():
    """2026-08-13 karşı-testi: düzeltmenin kendisi çivilenir, yoksa bir sonraki sarmalayıcıda
    aynı yanlış-pozitif geri gelir (ve çaresi yine "pini genişlet" sanılır).

    ÜST SINIR DA ÇİVİLİ: budama YALNIZ okuma çağrılarında durur — `write_json` sarmalanmış olsa
    bile yakalanmalı, aksi halde düzeltme bekçiyi kör ederdi."""
    okuma = ast.parse('int((store.read_json("scoreboard.json", {}) or {})["current_version"])')
    yazim = ast.parse('bool(store.write_json("scoreboard.json", {}))')
    sarmalanmis_yazim = ast.parse(
        'log(store.write_json("scoreboard.json", store.read_json("scoreboard.json", {})))')

    def _dis_cagri(mod):
        return next(n for n in ast.walk(mod) if isinstance(n, ast.Call))

    assert _karneyi_ham_yaziyor_mu(_dis_cagri(okuma)) is False, \
        "sarmalanmış OKUMA yine yazım sanıldı — watchdog yanlış-pozitifi geri geldi"
    assert _karneyi_ham_yaziyor_mu(_dis_cagri(yazim)) is True, \
        "sarmalanmış YAZIM kaçtı — budama fazla geniş, bekçi körleşti"
    assert _karneyi_ham_yaziyor_mu(_dis_cagri(sarmalanmis_yazim)) is True, \
        "yazım+okuma karışık ifadede yazım kaçtı"


def test_a_reseed_preserves_the_parent_link_in_the_scoreboard(seeded, monkeypatch):
    """BULGU (kusur). `--replay` (re-seed) karneyi TEK sürümlük bir sözlükle yeniden yazıyor.

    Tur 26'daki yama iki koruma ekledi: çok sürümlü karne varsa REDDET, zorlanırsa ARŞİVLE — ve
    `source/note/changed_variable` alanlarını taşı. Ama hayatta kalan tek satırın `parent` alanı
    hâlâ SABİT `None` yazılıyor, `backtest_oos` düşüyor ve ebeveynin kendi satırı tamamen gidiyor.
    Sonuç: strategy.yaml `parent: 1` derken karne `parent: null` der; rollback'in kıyaslayacağı soy
    kaydı yok olur. Canlı defterde bugün tam olarak bu durum var (v4 → parent: null, v3 satırı yok).
    BEKLENEN: re-seed `parent`ı (en az strategy.yaml'daki değeri) korumalı ve kaybı olay olarak
    kaydetmeli."""
    from meridian import run, loop, health
    monkeypatch.setattr(run.dataset, "load", lambda **k: (BARS, INDEX))
    monkeypatch.setattr(loop, "daily_cycle", lambda *a, **k: {})
    monkeypatch.setattr(health, "write_heartbeat", lambda **k: {})

    strat = config.default_strategy()
    strat.update({"version": 2, "parent": 1})
    config.dump_yaml(strat, config.strategy_path())
    versioning.snapshot(strat)
    versioning.update_scoreboard(2, parent=1, live_score=0.21, backtest_oos=0.19,
                                 source="operator_override", note="operatör tabanı",
                                 changed_variable="entry.min_score")

    out = run.replay_seed(REPLAY_START, REPLAY_END)
    assert "error" not in out, out

    row = versioning.scoreboard()["versions"]["2"]
    assert row.get("source") == "operator_override"        # tur 26 yaması: bu KORUNUYOR
    # DÜZELTİLDİ (2026-07-22): re-seed `parent`'ı sabit None yazıyor ve EBEVEYN SATIRINI da
    # düşürüyordu. `rollback` ebeveyn skorunu karneden okur; satır yoksa `par_score=None` ve öğrenme
    # döngüsü SESSİZCE kapanır — yani re-seed, döngüyü kapatan şeyin ta kendisiydi.
    assert row.get("parent") == 1, "soyağacı yine düşürüldü — rollback ebeveyn skorunu bulamaz"
    assert "1" in versioning.scoreboard()["versions"], \
        "ebeveyn SATIRI da korunmalı (yalnız parent alanı yetmez — rollback satırı okur)"
    assert int(config.load_strategy()["parent"]) == 1, \
        "strategy.yaml ebeveyni biliyor, karne bilmiyor — sessiz soy kopukluğu"


def test_a_reseed_rebuilds_the_ancestor_row_when_the_scoreboard_never_had_a_parent_key(
        seeded, monkeypatch):
    """CANLI HÂL (2026-07-26): yukarıdaki test karneye `parent=1` TOHUMLUYOR, yani düzeltilen
    yolun asıl kırıldığı durumu hiç görmüyor. Canlı defterde v4 satırında `parent` ANAHTARI
    yoktu (`parent: null`, source=operator_override) ve v3 satırı hiç yoktu. O hâlde:

      * `_prev_row.get("parent")` → None, ata yürüyüşü HİÇ dönmez,
      * v3 satırı kurulmaz → `evaluate_outcomes` her turda `no_parent_score` ile açık kalır.

    BEKLENEN: ebeveyn strategy.yaml'dan kurtarılır, ata satırı history anlık görüntüsünden
    kurulur — ve o satır HİÇBİR SKOR TAŞIMAZ (yeniden hesaplanmamış sayı kanıt değildir; uydurma
    bir taban canlı sürümü ataya geri aldırırdı)."""
    from meridian import run, loop, health
    monkeypatch.setattr(run.dataset, "load", lambda **k: (BARS, INDEX))
    monkeypatch.setattr(loop, "daily_cycle", lambda *a, **k: {})
    monkeypatch.setattr(health, "write_heartbeat", lambda **k: {})

    parent = config.default_strategy()
    parent.update({"version": 1, "parent": None})
    versioning.snapshot(parent)                      # history/v0001.yaml — ATA KARARI burada durur
    strat = config.default_strategy()
    strat.update({"version": 2, "parent": 1})
    config.dump_yaml(strat, config.strategy_path())
    versioning.snapshot(strat)
    # karne: `parent` anahtarı HİÇ yok ve ata satırı da yok — canlı defterin birebir hâli
    store.write_json("scoreboard.json",
                     {"current_version": 2, "versions": {"2": {"source": "operator_override"}}})

    out = run.replay_seed(REPLAY_START, REPLAY_END)
    assert "error" not in out, out

    vers = versioning.scoreboard()["versions"]
    assert vers["2"].get("parent") == 1, \
        "karnede parent anahtarı yokken strategy.yaml'daki soy kaydı taşınmadı"
    assert "1" in vers, "ata SATIRI kurulmadı — ata yürüyüşü hâlâ ham None okuyor"
    anc = vers["1"]
    assert anc.get("params"), "ata kararı (params) history anlık görüntüsünden kurtarılmadı"
    for _skor in ("live_score", "backtest_oos", "backtest_full", "n_trades"):
        assert anc.get(_skor) is None, \
            f"ata satırına UYDURMA skor yazıldı ({_skor}) — yeniden hesaplanmamış sayı kanıt değildir"


def test_a_missing_ancestor_snapshot_leaves_a_marked_row_not_a_silent_gap(seeded, monkeypatch):
    """SOYAĞACININ SON KAYNAĞI DA YOKSA (2026-07-26). Yukarıdaki test history anlık görüntüsünün
    VAR olduğu yolu kilitliyor. Asıl sessiz hâl ise ikisinin de olmadığı hâl: ne karne satırı ne
    `history/vNNNN.yaml`. O zaman `_ancestor_from_history` BOŞ sözlük yazıyordu ve karnedeki satır
    ile "hiç yazılmamış satır" birbirinden ayrılamıyordu — kayıp yalnız olay defterinde kalıyor,
    karneyi okuyan (rollback, pano) sessiz bir boşluk görüyordu.

    BEKLENEN: satır İŞARETLİ yazılır (kaybın kendisi karnede durur), uyarı olayı düşer, replay
    ÇÖKMEZ ve satıra hiçbir uydurma skor girmez."""
    from meridian import run, loop, health
    monkeypatch.setattr(run.dataset, "load", lambda **k: (BARS, INDEX))
    monkeypatch.setattr(loop, "daily_cycle", lambda *a, **k: {})
    monkeypatch.setattr(health, "write_heartbeat", lambda **k: {})

    strat = config.default_strategy()
    strat.update({"version": 2, "parent": 1})
    config.dump_yaml(strat, config.strategy_path())
    versioning.snapshot(strat)
    store.write_json("scoreboard.json",
                     {"current_version": 2, "versions": {"2": {"source": "operator_override"}}})
    snap = config.HISTORY / "v0001.yaml"
    snap.unlink()                                    # ATA ANLIK GÖRÜNTÜSÜ DE YOK — son kaynak da kayıp
    assert not snap.exists(), "ön koşul: v0001.yaml gerçekten silinmiş olmalı"

    out = run.replay_seed(REPLAY_START, REPLAY_END)
    assert "error" not in out, out                   # replay ÇÖKMEZ: kopuk soyağacı bir arıza değil

    vers = versioning.scoreboard()["versions"]
    assert "1" in vers, "ata satırı HİÇ yazılmadı — kayıp karnede görünmez oldu"
    anc = vers["1"]
    assert "kopuyor" in str(anc.get("note") or ""), \
        f"ata satırı işaretsiz yazıldı ({anc}) — boş satır 'satır yoktu' ile ayırt edilemez"
    for _skor in ("live_score", "backtest_oos", "backtest_full", "n_trades", "params"):
        assert anc.get(_skor) is None, \
            f"kurtarılamayan ata satırına {_skor} yazıldı — ölçülmeyen değer None kalmalı"

    blob = "".join(str(e) for e in _events())
    assert "reseed_ancestor_snapshot_missing" in blob, "kayıp SESSİZ kaldı — uyarı olayı düşmedi"


# ==============================================================================================
# 7. HİPOTEZ DEFTERİ BÜTÜNLÜĞÜ
# ==============================================================================================
def test_ids_are_never_reused_after_a_partial_ledger_truncation(seeded):
    for i in range(3):
        memory.record({"variable": "entry.min_score", "new": 60 + i, "status": "proposed"})
    rows = memory.all_hypotheses()
    assert [r["id"] for r in rows] == ["H00001", "H00002", "H00003"]
    store.write_jsonl(memory.HYP, rows[:1])          # kısalma (elle temizlik / kısmi yazım)
    # DÜZELTİLDİ (2026-07-22): eskiden burada H00002 bekleniyordu — yani kısalma kimlikleri GERİ
    # SARDIRIYORDU ve H00002/H00003 ikinci kez dağıtılabiliyordu. Yüksek-su işareti defterden
    # bağımsız olduğu için artık kısalma da silinme de işareti geri çekemez.
    assert memory.next_id() == "H00004", "kısalma kimliği geri sardırdı"
    store.write_jsonl(memory.HYP, [rows[2]])         # ortadakiler kayıp
    assert memory.next_id() == "H00004", "kimlik GERİ SARDI — iki hipotez aynı kimliği taşır"


def test_a_fully_wiped_ledger_does_not_restart_ids(seeded):
    """BULGU (sınır). `next_id` mevcut satırların EN BÜYÜĞÜ + 1'dir: kısalmaya dayanıklı ama TAM
    SİLİNMEYE değil. Defter sıfırlanırsa (sprint kum havuzu hypotheses.jsonl'ı boşaltıyor)
    kimlikler H00001'den başlar ve arşivlenmiş eski satırlarla ÇAKIŞIR — 'H00001 neden hem
    reddedildi hem canlı?' sorusunun kaynağı budur.
    BEKLENEN: kimlik, defterden bağımsız monoton bir yüksek-su-seviyesi kaydından üretilmeli."""
    memory.record({"variable": "entry.min_score", "new": 61, "status": "live", "version_to": 2})
    assert memory.next_id() == "H00002"
    store.write_jsonl(memory.HYP, [])                    # defteri TAMAMEN sil
    # DÜZELTİLDİ: yüksek-su işareti defterden BAĞIMSIZ ve monoton — silinme onu geri sardıramaz.
    assert memory.next_id() == "H00002", "kimlik geri sardı — arşivlenmiş satırlarla çakışır"


def test_promoted_outcome_is_a_one_way_ratchet_written_once(seeded):
    memory.record({"id": "H00001", "version_to": 2, "status": "promoted", "predicted_delta": 0.05,
                   "realized_delta": 0.07})
    again = memory.writeback_outcome(2, realized_delta=-0.99, realized_detail={"n": 99})
    assert again["realized_delta"] == 0.07, "terfi etmiş sonuç yeniden yazıldı"
    assert again.get("realized_detail") != {"n": 99}


def test_update_status_enforces_a_transition_law(seeded):
    """DÜZELTİLDİ (2026-07-22). `update_status` HERHANGİ bir dizgiyi kabul ediyordu: terminal bir
    durumdan geriye dönmek de (`promoted → proposed`), şemada hiç olmayan bir durum yazmak da
    (`status:"muz"`) serbestti.

    Neden önemli: defterdeki durum, bir sürümün canlı olup olmadığının TEK okunabilir kaydı; aylık
    kota (`accepted_this_month`), UCB ödülleri ve lessons.md hepsi bu alandan besleniyor.
    `promoted → proposed` yazılabiliyorsa aynı değişiklik ikinci kez kotadan slot yakar ve defter
    strategy.yaml ile çelişir — alarm da çalmaz."""
    memory.record({"id": "H00001", "version_to": 2, "status": "promoted"})
    assert memory.update_status("H00001", "proposed") is None, "terminal durumdan geri dönüldü"
    assert memory.update_status("H00001", "muz") is None, "uydurma statü kabul edildi"
    assert memory.all_hypotheses()[0]["status"] == "promoted", "defter bozuldu"
    blob = "".join(str(e) for e in store.read_jsonl("events.jsonl"))
    assert "illegal_status_transition" in blob and "illegal_hypothesis_status" in blob, \
        "ret SESSİZ kaldı — reddedilen geçiş de kayda geçmeli"
    # POZİTİF KONTROL: yasa meşru ilerlemeyi engellemiyor
    memory.record({"id": "H00002", "version_to": 3, "status": "proposed"})
    assert memory.update_status("H00002", "live") is not None


def test_defect_a_superseded_live_hypothesis_never_reaches_a_terminal_state(seeded, monkeypatch):
    """BULGU (kusur — turun en ağırı). Bir hipotez `live`de SONSUZA DEK asılı kalabilir.

    `rollback.evaluate_outcomes` YALNIZ strategy.yaml'daki GÜNCEL sürümü ölçer ve
    `memory.writeback_outcome` yalnız `version_to == o sürüm` satırını arar. v2 min_sample'a
    ulaşmadan v3 ship edilirse (ya da operatör sürümü elle değiştirirse) v2'nin hipotezini ölçecek
    hiçbir kod yolu KALMAZ — 'yetim canlı hipotez' taraması hiçbir yerde yok.

    Sonuç sessiz ve tam olarak bu sistemin korktuğu sınıf: ship'ler artar, ajan meşgul görünür, ama
    o ship'in işe yarayıp yaramadığı ASLA ölçülmez; realized_delta yazılmaz, kalibrasyon n'i
    büyümez, lessons.md hamleyi ne ölü ne kanıtlanmış sayar, UCB ödülü 'ship edildi' ikilisinde donar.

    CANLI KANIT (2026-07-22): state/hypotheses.jsonl'da H00029 (v2→v3, status=live,
    realized_delta=None) duruyor; canlı sürüm v4 olduğu için o satır artık ulaşılamaz.
    BEKLENEN: evaluate_outcomes, kendi sürümü altında min_sample'a ulaşmış YETİM canlı hipotezleri
    de kapatmalı; hiç ulaşamayacaksa açıkça terminal bir duruma ('superseded') taşımalı."""
    goal = config.goal()
    base = _tagged({}, 1)
    store.write_jsonl("trades.jsonl", base)

    _pass_gate(monkeypatch)
    r2 = reflect.submit({"variable": "exit.time_stop_days", "new": 16, "rationale": "ilk ship",
                         "predicted_delta": 0.05}, goal)
    assert r2["status"] == "shipped"
    v2 = r2["version"]

    _pass_gate(monkeypatch)
    r3 = reflect.submit({"variable": "entry.min_score", "new": 61, "rationale": "ikinci ship",
                         "predicted_delta": 0.05}, goal)
    assert r3["status"] == "shipped"
    v3 = r3["version"]

    # v3 altında bol kanıt biriksin; v2 min_sample'a HİÇ ulaşmamış olsun
    store.write_jsonl("trades.jsonl", base + _tagged({}, v3) + _tagged({}, v2)[:5])
    for _ in range(3):                                     # döngü bunu her seans çağırır
        rollback.evaluate_outcomes(goal)
    by_v = {h["version_to"]: h for h in memory.all_hypotheses() if h.get("version_to")}
    assert by_v[v3].get("realized_delta") is not None, "güncel sürüm ölçülüyor (turun bu yarısı sağlam)"
    assert by_v[v2]["status"] == "live" and by_v[v2].get("realized_delta") is None

    # v2'nin altında min_sample'ı AŞAN gerçek işlemler bulunsa BİLE hiçbir şey değişmez
    store.write_jsonl("trades.jsonl", base + _tagged({}, v3) + _tagged({}, v2))
    for _ in range(3):
        rollback.evaluate_outcomes(goal)
    by_v = {h["version_to"]: h for h in memory.all_hypotheses() if h.get("version_to")}
    assert by_v[v2]["status"] == "live" and by_v[v2].get("realized_delta") is None, \
        "yetim hipotez artık ölçülüyor — kusur giderilmiş, testi güncelle"


def test_an_unmeasurable_outcome_loop_is_reported_not_silent(seeded):
    """BULGU (kusur — BUGÜNKÜ CANLI DURUM, 2026-07-22). Ölçüm hiç yapılmıyor ve yapılamayacak.

    Canlı state'in şekli şu: strategy.yaml v4 (parent 3, kaynağı OPERATÖR kararı — hipotezi yok),
    scoreboard yalnız {"4"} (re-seed diğer satırları sildi), trades.jsonl'daki 129 satırın 129'u
    strategy_version=4. `evaluate_outcomes` bu şekli şöyle işler:

        cur_trades = 129 (min_sample tamam) → par_trades(v3) = 0
        → scoreboard["3"] yok → par_score None
        → _parent_score_fallback(4): version_to==4 olan hipotez arar → YOK (operatör ship'i)
        → par_score None → `return None`

    Yani her seans sessizce hiçbir şey yapılmaz. v3 altında bir daha ASLA işlem oluşmayacağı için
    bu kalıcıdır: ajan işlem yapmaya devam eder, kalibrasyon n'i 0'da kalır, hiçbir alarm çalmaz —
    'ölçemediğini' söyleyen tek bir satır bile yok.
    BEKLENEN: ebeveyn skoru HİÇBİR kaynaktan bulunamıyorsa bu bir OLAY olmalı (döngü açık kaldı),
    sessiz bir `return None` değil."""
    goal = config.goal()
    strat = config.default_strategy()
    strat.update({"version": 4, "parent": 3})
    config.dump_yaml(strat, config.strategy_path())
    versioning.update_scoreboard(4, params=strat["params"], parent=None, live_score=-0.0185,
                                 source="operator_override")
    store.write_jsonl("trades.jsonl", _tagged({}, 4))         # her satır v4 damgalı (re-seed sonrası)
    memory.record({"version_from": 2, "version_to": 3, "status": "live",
                   "variable": "entry.w_prox", "new": 0.15, "predicted_delta": 0.05})
    before = len(_events())

    for _ in range(5):
        assert rollback.evaluate_outcomes(goal) is None
        assert store.read_json(rollback.OPEN_LOOP_FILE, {}).get("reason") == "no_parent_score", \
            "döngü yine SESSİZCE kapandı — 'ölçemiyorum' bir olay olmalı"

    # Hipotez hâlâ terminale ulaşmıyor — ÇÜNKÜ ÖLÇÜM YAPILAMIYOR. Ama artık bu görünür.
    assert memory.all_hypotheses()[0]["status"] == "live"
    assert memory.all_hypotheses()[0].get("realized_delta") is None
    # DÜZELTİLDİ (2026-07-22): eskiden burada `len(_events()) == before` vardı — yani hiçbir olay
    # yazılmadığı KANITLANIYORDU. Sessizlik tam da sorunun kendisiydi: canlıda döngü her turda
    # kapanıyor, "kanıt bekliyorum" ile "ÖLÇEMİYORUM" ayırt edilemiyordu. Artık bir olay düşer —
    # ve yalnız DURUM DEĞİŞTİĞİNDE, yani 5 tur log'u sele çevirmez.
    yeni = [e for e in _events() if e.get("event") == "learning_loop_open"]
    assert len(yeni) == 1, f"olay ya hiç yok ya da her turda tekrarlanıyor: {len(yeni)}"
    assert store.read_json(rollback.OPEN_LOOP_FILE, {}).get("n") == 5, "tekrarlar sayılmıyor"


def test_every_evaluated_proposal_leaves_exactly_one_ledger_row(seeded, monkeypatch):
    """KORUNUM: guard reddi, kapı reddi ve ship — üçü de TEK satır bırakır; fazlası da eksiği de yok."""
    store.write_jsonl("trades.jsonl", _tagged({}, 1))
    _gate(monkeypatch, _wf(0.30, (0.6, 0.6, 0.6)), _wf(0.10, (0.2, 0.2, 0.2)))
    assert reflect.submit({"variable": "entry.min_score", "new": 61},
                          config.goal())["status"] == "rejected_by_backtest"
    assert reflect.submit({"variable": "max_open_positions", "new": 9},
                          config.goal())["status"] == "rejected_by_guard"
    _pass_gate(monkeypatch)
    assert reflect.submit({"variable": "exit.time_stop_days", "new": 16},
                          config.goal())["status"] == "shipped"
    rows = memory.all_hypotheses()
    assert [r["status"] for r in rows] == ["rejected_by_backtest", "rejected_by_guard", "live"]
    assert len({r["id"] for r in rows}) == 3


def test_a_better_score_cannot_buy_its_way_past_the_fold_and_tail_vetoes(seeded, monkeypatch):
    """Kapı yasası gerçek: yüksek OOS tek başına yetmez — fold çoğunluğu ve kuyruk vetosu da geçilmeli."""
    store.write_jsonl("trades.jsonl", _tagged({}, 1))
    before = copy.deepcopy(config.load_strategy())

    _gate(monkeypatch, _wf(0.10, (0.9, 0.9, 0.9)), _wf(0.90, (0.1, 0.1, 0.1)))
    res = reflect.submit({"variable": "entry.min_score", "new": 61}, config.goal())
    assert res["status"] == "rejected_by_backtest" and res["gate"]["fold_wins"] == "0/3"
    assert config.load_strategy() == before

    tail_ok = {"var_r": -1.0, "cvar_r": -1.5, "n": 40}
    tail_bad = {"var_r": 0.5, "cvar_r": 0.2, "n": 40}
    _gate(monkeypatch, _wf(0.10, (0.2, 0.2, 0.2), tail_ok), _wf(0.90, (0.6, 0.6, 0.6), tail_bad))
    res = reflect.submit({"variable": "entry.rs_rating_min", "new": 71}, config.goal())
    assert res["status"] == "rejected_by_backtest" and res["gate"]["tail_ok"] is False
    assert config.load_strategy() == before

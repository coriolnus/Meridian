"""test_na_revision2_v54.py — kalan 81 N/A'nın sorgusu (2026-07-21, ikinci geçiş).

İlk geçiş dosya yazımına bakmıştı. Bu geçiş üç YENİ olgusal sorgu ekledi:
  1) sahipliğin dosya-dışı biçimi: PAYLAŞILAN BELLEK durumu (modül-düzeyi mutable global).
     — İlk tarayıcım `_cache: dict = {}` gibi ANNOTASYONLU atamaları göremiyordu (AnnAssign);
       tarayıcının kendi kör noktasıydı. Düzeltilince `dataset._cache` çıktı.
  2) üretkenlik: modülün boş kalabilecek bir çıktısı var mı?
  3) korunum: bir koleksiyonu dolaşıp ELEYEN kod var mı (elenenin izi tutuluyor mu)?

9 hücre daha N/A'dan çıktı. `indicators` için çıkan "korunum" sinyali YANLIŞ POZİTİFTİ
(`corr_max` içindeki `continue` bir eleme değil, veri yetersizliği kontrolü) — N/A kaldı ve
gerekçesi yazıldı. Yani tarayıcıya körü körüne uymuyoruz; kanıt tartışılıyor.
"""
from __future__ import annotations

import ast
import inspect
import pathlib
import re
import shutil
from pathlib import Path

import pandas as pd
import pytest

from meridian import config, store


@pytest.fixture
def seeded(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    yield sandbox_state
    config.reload_config()


# ---------- dataset: SAHİPLİK (paylaşılan bellek önbelleği) ----------
def test_dataset_cache_is_shared_state_and_never_pins_an_empty_dataset(monkeypatch, sandbox_state):
    """`dataset._cache` süreç-içi PAYLAŞILAN durumdur: zamanlayıcı ve Hermes iş parçacıkları aynı
    nesneyi okur. Geçici bir kaynak kesintisi bu önbelleğe BOŞ veri sabitlerse döngü o oturum
    boyunca sıfır barla koşar — sahiplik sorusu tam olarak budur."""
    from meridian import dataset as ds
    from meridian.adapters import data
    ds._cache.clear()
    good_bars, good_idx = {"AAA": pd.DataFrame({"date": [1]})}, pd.DataFrame({"date": [1]})
    monkeypatch.setattr(data, "load_bars", lambda *a, **k: good_idx)
    monkeypatch.setattr(data, "load_many", lambda *a, **k: good_bars)
    monkeypatch.setattr(data, "validate_bars", lambda *a, **k: (True, []))
    b1, i1 = ds.load(use_cache=False)
    assert b1 == good_bars
    monkeypatch.setattr(data, "load_many", lambda *a, **k: {})        # kesinti
    monkeypatch.setattr(data, "load_bars", lambda *a, **k: pd.DataFrame())
    b2, i2 = ds.load(use_cache=False)
    assert b2 == good_bars, "kesinti önbelleğe BOŞ veri sabitledi — döngü sıfır barla koşar"
    ds._cache.clear()


def test_dataset_declares_its_shared_cache():
    """Paylaşılan durum GÖRÜNÜR olmalı: adı ve amacı kaynakta yazılı."""
    src = pathlib.Path("meridian/dataset.py").read_text()
    assert "_cache" in src and "Cached in-process" in src


# ---------- api: KORUNUM (her operatör eylemi iz bırakır) ----------
def test_every_mutating_endpoint_leaves_a_trace():
    """Operatörün yaptığı her değişiklik KAYITLI olmalı: izsiz bir eylem, 'bu neden böyle oldu'
    sorusunu cevapsız bırakır (kapının değil, tarihin korunumu)."""
    src = pathlib.Path("meridian/api.py").read_text()
    blocks = re.split(r"\n(?=@app\.)", src)
    silent = []
    for b in blocks:
        m = re.match(r'@app\.(post|delete|put)\("([^"]+)"', b)
        if not m:
            continue
        path = m.group(2)
        # /api/logout (2026-07-29, kimlik turu) — SUNUCUDA HİÇBİR ŞEYİ DEĞİŞTİRMEZ, o yüzden
        # kaydedecek bir "değişiklik" de yoktur. Oturum DURUMSUZ ve imzalıdır (`<exp>.<nonce>.<hmac>`,
        # bkz. auth.py): sunucu tarafında oturum tablosu YOK. `logout` yalnız tarayıcıya çerezi
        # düşürmesini söyler — silinecek bir sunucu kaydı, iptal edilecek bir oturum satırı yoktur.
        # Testin koruduğu soru "bu neden böyle oldu"dur; logout hiçbir "böyle" üretmez.
        #
        # AYRICA kaydetmemek BİLİNÇLİ: bu uç `api.KIMLIK_UCLARI` içinde, yani KİMLİKSİZ çağrılabilir.
        # Buraya bir `obs.log` koymak, porta erişebilen herkese operatörün kanıt defterine SINIRSIZ
        # satır yazdırma imkânı verirdi. Kardeş uç `login_failed` bu tuzağa düşmez çünkü kaba kuvvet
        # kilidi 8 denemede devreye girip kayıttan ÖNCE 429 döner — logout'ta böyle bir sınır yok.
        # Güvenlik açısından anlamlı yarı (BAŞARISIZ giriş) zaten kayıtlı ve sınırlı.
        if path == "/api/logout":
            continue
        # /api/hindsight/recall (2026-09-02, Hafıza yüzeyi CP-UI birebirleştirme) — SORGU
        # SINIFI bir POST'tur: CP `recall` araması gövde ister (types/tags/temporal_window/
        # min_scores bir GET'e sığmaz), sunucuda HİÇBİR ŞEYİ DEĞİŞTİRMEZ (bkz. rota docstring'i
        # ve `test_recall_state_defterine_yazmaz`). Uç `_auth` kapılı (KİMLİKLİ), ama defterde
        # satır üretmemesi bilinçli: arama bir EYLEM değil, operatörün kanıt defterine kullanıcı-
        # tetikli her sorguyu yazmak gürültü üretirdi. Faz-1 planının (docs/superpowers/plans/
        # 2026-09-02-hafiza-cpui-birebir.md, "Kapsam kararı") beyanlı istisnası.
        if path == "/api/hindsight/recall":
            continue
        if "obs.log" in b or "obs.warn" in b or "obs.alarm" in b:
            continue
        # eylemi ÇAĞIRDIĞI modülde loglayanlar (delege edilmiş iz) — beyan edilmiş istisnalar
        # PLAN KARAR UÇLARI (2026-08-26): ikisi de izi `loop`ta bırakır — `operator_onay_ver`
        # → `plan_operator_approved`, `operator_ret_ver` → `plan_operator_rejected`. Yazımın
        # orada olması bir tercih değil SÖZLEŞME: `trade_plans.jsonl`in yazar listesi
        # `ledgers.CONTRACTS`ta yazılıdır (loop/run/hermes) ve uç noktanın deftere kendi eliyle
        # yazması "haberi olmayan ikinci yazar" sınıfını yeniden açardı.
        # NEDEN AÇIKÇA YAZILDI: `onayla` bugüne kadar bu listeye ADIYLA girmemişti, docstring'inde
        # geçen "`api_halt` → `health.set_halt` deseni" cümlesi yüzünden ALT-DİZE TESADÜFÜYLE
        # geçiyordu (ölçüldü, 2026-08-26). Yani kardeş uç korunmuyordu, susturulmuştu. Kardeşi
        # `reddet` eklenirken tesadüf de kapatıldı: ikisi de artık adıyla beyanlı.
        if any(k in b for k in ("secrets_mod.set", "secrets_mod.delete", "reflect_now",
                                "hermes_runtime.start", "hermes_runtime.stop", "sprint.start",
                                "sprint.stop", "skill_evolve.", "skills.apply_skill_action",
                                "alpaca.submit_plan", "health.set_halt", "health.set_learn_halt",
                                "_loop.operator_onay_ver", "_loop.operator_ret_ver")):
            continue
        silent.append(path)
    assert not silent, f"iz bırakmayan mutasyon ucu: {silent}"


# ---------- config: ÜRETKENLİK (parametre seti asla boş dönmez) ----------
def test_config_always_yields_a_usable_param_set(seeded):
    assert config.default_strategy()["params"], "varsayılan parametre seti BOŞ"
    assert config.load_strategy()["params"], "canlı parametre seti boş — motor eşiksiz koşar"
    (config.STATE / "strategy.yaml").write_text("")
    assert config.load_strategy()["params"] == config.default_strategy()["params"]


# ---------- probgate: KORUNUM (kaç replikasyon SAYILDI) ----------
def test_bootstrap_reports_how_many_replications_counted(seeded):
    """Skorlanamayan replikasyonlar sessizce düşerse P yanlı olur — kaçının sayıldığı (n_valid)
    HER SONUÇTA yazılı olmalı."""
    from meridian.probgate import PairedProbabilisticGate
    from tests.test_decision_v3 import synth_trades, OOS_START, OOS_END
    inc = synth_trades(111, seed=8)
    cand = [{**t, "r_multiple": t["r_multiple"] + 0.3} for t in inc]
    g = PairedProbabilisticGate(config.goal(), n_boot=200, seed=42).evaluate(
        inc, cand, OOS_START, OOS_END)
    assert g.n_boot == 200 and 0 < g.n_valid <= g.n_boot
    thin = PairedProbabilisticGate(config.goal(), n_boot=50, seed=42).evaluate(
        inc[:3], cand[:3], OOS_START, OOS_END)
    assert thin.n_valid <= 50 and thin.law in ("probabilistic", "legacy")   # sayı HER ZAMAN var


# ---------- selfreview: KORUNUM (eşiği geçen her kural bir satır üretir) ----------
def test_every_crossed_threshold_produces_an_attention_row(sandbox_state):
    from meridian import selfreview
    # ŞEMA GÜNCELLENDİ (2026-07-26): satır GERÇEK dilim + ölçülmüş anlamlılık ister. Fikstür kendi
    # içinde tutarlı: n=60'ta eşik 1.96/√59 ≈ 0.26, |−0.30| onu aşıyor.
    store.write_json("score_calibration.json",
                     {"rank_ic": -0.30, "n": 60, "n_real": 60, "n_cf": 0,
                      "real": {"rank_ic": -0.30, "n": 60, "anlamli": True,
                               "se_yontem": "i.i.d._varsayimi"}, "cf": None})
    store.write_json("cf_fidelity.json", {"n": 20, "corr": 0.1, "mean_diff_r": 1.2,
                                          "fidelity_ok": False})
    rep = selfreview.build()
    whys = " | ".join(a["why"] for a in rep["attention"])
    assert "NEGATİF" in whys, "IC eşiği geçti ama DİKKAT satırı yok — sessiz eleme"
    assert len(rep["attention"]) >= 2, f"iki eşik geçti, {len(rep['attention'])} satır üretildi"


def test_no_threshold_crossed_means_an_honestly_empty_report(sandbox_state):
    from meridian import selfreview
    rep = selfreview.build()
    assert rep["attention"] == [] and rep["contradictions"] == []    # sessizlik DE bir sonuçtur


# ---------- store: ÜRETKENLİK (yazım gerçekten indi mi) ----------
def test_store_writes_actually_land_and_are_counted(sandbox_state):
    n0 = store.io_stats()["writes"]
    p = store.write_json("x.json", {"a": 1})
    assert p.exists() and store.read_json("x.json") == {"a": 1}
    assert store.io_stats()["writes"] > n0, "yazım sayacı ilerlemedi — üretim görünmez"
    store.append_jsonl("y.jsonl", {"b": 2})
    assert store.read_jsonl("y.jsonl") == [{"b": 2}]


# ---------- determinizm: saf hesap yolları ----------
def test_regime_trigger_counting_is_deterministic(sandbox_state):
    from meridian.regime_trigger import DeferredRegimeBudgetTrigger as T
    trades = [{"regime": "chop"}] * 10 + [{"regime": "trend_up"}] * 5
    assert T().evaluate(trades) == T().evaluate(trades)


def test_secrets_reads_are_deterministic(sandbox_state, monkeypatch):
    from meridian import secrets
    for n in list(secrets.ALLOWED):
        monkeypatch.delenv(n, raising=False)
    secrets.clear_cache()
    secrets.set("FMP_API_KEY", "abcdefghijkl")
    assert secrets.get("FMP_API_KEY") == secrets.get("FMP_API_KEY")
    assert secrets.status() == secrets.status()


def test_fmp_status_is_deterministic(monkeypatch):
    """DEVİR (2026-07-30 temizlik turu): özne `news.status` EMEKLİ edildi (mezar taşı:
    meridian/adapters/news.py). Saflık sorusu ölmedi — `news.status` zaten `fmp.health()`i
    sarmalıyordu, yani ölçülen saflık ASIL olarak FMP künyesinindi. Çivi kaynağa taşındı."""
    from meridian.adapters import fmp
    monkeypatch.setattr(fmp.secrets, "present", lambda n: True)
    fmp._HEALTH.update({"ok": True, "last_error": ""})
    assert fmp.status() == fmp.status()
    assert fmp.health() == fmp.health()


# ---------- reddedilen kanıt: neden N/A KALDI ----------
def test_indicators_conservation_stays_na_with_a_written_reason():
    """Tarayıcı `corr_max` içindeki `continue`'yu 'eleme' sandı — YANLIŞ POZİTİF: orada elenen bir
    ÖĞE yok, yalnız yetersiz veri kontrolü var (min_pts). indicators'a giren sayılabilir bir akış
    yoktur; korunum sorusunun öznesi yok. Kanıt tartışılır, tarayıcıya körü körüne uyulmaz."""
    from meridian import indicators as ind
    src = inspect.getsource(ind.corr_max)
    assert "min_pts" in src and "continue" in src
    from meridian import integrity_registry as ir
    assert "korunum" not in ir.APPLICABLE["indicators"]

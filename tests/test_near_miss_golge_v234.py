"""test_near_miss_golge_v234.py — NEAR-MISS GÖLGE BACAĞININ SESSİZ ÖLÜMÜ (2026-08-12).

VAKA: counterfactuals.jsonl'de near-miss satırları 2026-07-29'da bitti; 08-04→08-07 ana tarama
12 aday üretirken gevşek gölge İKİ HAFTA sıfır yazdı ve HİÇBİR olay düşmedi. Yerel adli bulgu:
kod yolu sağlam (bayat barlarla birebir repro: 07-16'da 12, 07-28'de 19 near-miss) — ölüm,
üretim/teslim zincirinin İZSİZ sıfır yollarındaydı. Bu dosya o yolların hepsinin artık OLAYLI
olduğunu sabitler:

  uretim   — gevşek-yalnız sinyal near-miss olarak doğar, cf_open'a düşer, özet olay sayacı taşır
  teslim   — collect'in sınıf muhasebesi (SON_TOPLAMA) rps/tavan/çift kayıplarını sayar ve olaylar
  tavan    — MAX_OPEN doluluğu yazım sırası gereği ÖNCE near-miss'i aç bırakır; artık kırılımlı uyarı
  atlama   — P2 hiç koşmadıysa özet olay near_miss=None yazar (uydurma 0 YOK) + sebep olayı düşer
  kuraklık — aday varken 0 near-miss yapısal şüphedir; bekçi eşik tablosunu [sıkı, gevşek] basar
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from meridian import config, counterfactual as cf, loop, store, strategy
from tests.conftest import make_bars


@pytest.fixture
def seeded(sandbox_state):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    (sandbox_state / "strategy.yaml").write_text(yaml.safe_dump(config.default_strategy()))
    yield sandbox_state
    config.reload_config()


class _Sig:
    def __init__(self, ticker, setup="breakout_vcp", score=68, entry=100.0, stop=95.0):
        self.ticker, self.setup, self.score = ticker, setup, score
        self.entry_trigger, self.stop, self.profit_target = entry, stop, 115.0


def _plan(tid="P1", ticker="AAA"):
    return {"id": tid, "ticker": ticker, "setup": "breakout_vcp", "score": 71,
            "entry_trigger": 100.0, "stop": 95.0, "profit_target": 115.0,
            "r_multiple_expected": 3.0, "regime_at_plan": "chop", "gate_verdict": "GO",
            "skill_chain": ["vcp-screener"]}


def _events(name):
    return [e for e in store.read_jsonl("events.jsonl") if e.get("event") == name]


def _universe():
    idx = make_bars(300, seed=1, trend=0.0009)
    bars = {"AAA": make_bars(300, seed=2, breakout_at=200),
            "BBB": make_bars(300, seed=3, breakout_at=150),
            "CCC": make_bars(300, seed=4, trend=0.001)}
    return bars, idx


def _last_date(idx):
    return str(idx["date"].iloc[-1].date())


# ---------- teslim: collect'in sınıf muhasebesi ve kayıp olayı ----------
def test_collect_near_miss_muhasebesi_ve_rps_kaybi_olayli(seeded):
    """entry≤stop geometrili near-miss bugüne dek İZSİZ eleniyordu — artık sayılır ve olay düşer."""
    cf.collect("2026-08-12", [], set(), [], 15,
               near_miss=[(_Sig("AAA"), ["hacim"]),               # geçerli — yazılır
                          (_Sig("BBB", entry=90.0, stop=95.0), ["rs"])],  # rps≤0 — düşer
               regime="chop")
    rows = store.read_json(cf.OPEN_FILE, [])
    assert [r["ticker"] for r in rows] == ["AAA"] and rows[0]["near_miss"] is True
    st = cf.SON_TOPLAMA
    assert st["date"] == "2026-08-12" and st["nm_gelen"] == 2
    assert st["nm_yazilan"] == 1 and st["nm_rps"] == 1 and st["nm_tavan"] == 0
    ev = _events("cf_near_miss_yutuldu")
    assert ev and ev[-1]["rps_gecersiz"] == 1 and ev[-1]["yazilan"] == 1, \
        "rps kaybı olaysız — sessiz eksilme sınıfı geri açılmış"


def test_collect_cift_kayit_tek_basina_yutulma_olayi_uretmez(seeded):
    """Dedup düşmesi kayıp değildir (satır zaten defterde) — yeniden-koşu gürültü üretmemeli."""
    args = ("2026-08-12", [], set(), [], 15)
    cf.collect(*args, near_miss=[(_Sig("AAA"), ["hacim"])], regime="chop")
    onceki = len(_events("cf_near_miss_yutuldu"))
    cf.collect(*args, near_miss=[(_Sig("AAA"), ["hacim"])], regime="chop")   # birebir tekrar
    assert len(_events("cf_near_miss_yutuldu")) == onceki, \
        "çift-kayıt (zararsız) yutulma olayı üretti — yeniden-koşular alarmı sulandırır"
    assert cf.SON_TOPLAMA["nm_cift"] == 1 and cf.SON_TOPLAMA["nm_yazilan"] == 0


def test_tavan_once_near_missi_ac_birakir_ve_kirilimli_uyarir(seeded, monkeypatch):
    """Yazım sırası plan→uyuyan→near-miss: tavanda İLK kurban near-miss'tir. Uyarı artık sınıf söyler."""
    monkeypatch.setattr(cf, "MAX_OPEN", 1)
    cf.collect("2026-08-12", [_plan()], {"P1"}, [], 15,
               near_miss=[(_Sig("BBB"), ["hacim"])], regime="chop")
    rows = store.read_json(cf.OPEN_FILE, [])
    assert len(rows) == 1 and rows[0]["ticker"] == "AAA", "tavan senaryosu kurulamadı"
    dolu = _events("cf_ledger_full")
    assert dolu and dolu[-1]["near_miss"] == 1 and dolu[-1]["plan"] == 0, \
        "cf_ledger_full sınıf kırılımı taşımıyor — hangi kanıt aç kaldı görünmez"
    yut = _events("cf_near_miss_yutuldu")
    assert yut and yut[-1]["yazilan"] == 0 and yut[-1]["tavan"] == 1
    assert yut[-1].get("level") == "warn", "tam kayıp (yazılan=0) warn olmalı — info gömülür"


# ---------- uretim + sayaç: ölüm sınıfının birebir aynası ----------
def test_gevsek_yalniz_sinyal_deftere_ve_ozet_sayaca_akar(seeded, monkeypatch):
    """Gevşek taramada doğup sıkıda ölen sinyal: cf_open'a near_miss düşer, özet olay sayar.
    Sahte scan_all YALNIZ gevşek çağrıda konuşur (min_volume_ratio≤1.0 imzası) — relax tablosuna
    (TEK-KAYNAK, strategy.py) dokunulmaz; asimetri parametreden okunur."""
    gercek = strategy.EntrySignal

    def _sahte_scan_all(bars, params, rs, ticker="?"):
        if ticker != "AAA" or float(params.get("entry.min_volume_ratio", 1.5)) > 1.0:
            return {}                                    # sıkı tarama: sinyal YOK
        c = float(bars["close"].iloc[-1])
        s = gercek(ticker=ticker, setup="breakout_vcp", entry_trigger=c, pivot=c,
                   stop=round(c * 0.95, 2), atr=1.0, rs_rating=60, score=55,
                   profit_target=round(c * 1.2, 2), size_r=1.0,
                   r_per_share=round(c * 0.05, 2), notes="vr=1.2 prox=1.0%")
        return {"breakout_vcp": s}

    monkeypatch.setattr(strategy, "scan_all", _sahte_scan_all)
    bars, idx = _universe()
    out = loop.daily_cycle(bars, idx, on_date=_last_date(idx))
    assert out["near_miss"] == 1, f"üretim sayacı özetde yok/yanlış: {out.get('near_miss')}"
    nm_rows = [r for r in store.read_json(cf.OPEN_FILE, []) if r.get("near_miss")]
    assert len(nm_rows) == 1 and nm_rows[0]["ticker"] == "AAA" and nm_rows[0]["id"].endswith("-nm")
    ozet = _events("daily_cycle")[-1]
    assert ozet["near_miss"] == 1 and ozet["near_miss_yazilan"] == 1, \
        "özet olay üretim/teslim sayaçlarını taşımıyor — pano yine kör"
    assert ozet.get("near_miss_gec") == 0                # geç-borç yoksa 0 GÖRÜNÜR (None değil)


def test_p2_atlanirsa_none_yazilir_ve_sebep_olayi_duser(seeded):
    """Kitap doluyken P2 (ve gölge bacağı) koşmaz: özet near_miss=None (uydurma 0 YOK) + sebep olayı."""
    repo = Path(__file__).resolve().parent.parent / "state"
    g = yaml.safe_load((repo / "goal.yaml").read_text())
    g["limits"]["max_open_positions"] = 0
    (Path(config.STATE) / "goal.yaml").write_text(yaml.safe_dump(g))
    config.reload_config()
    bars, idx = _universe()
    out = loop.daily_cycle(bars, idx, on_date=_last_date(idx))
    assert out["near_miss"] is None, "bacak koşmadı ama sayaç 0/atama taşıyor — ölçülmemişi uydurdu"
    ozet = _events("daily_cycle")[-1]
    assert ozet["near_miss"] is None and ozet["near_miss_yazilan"] is None
    atla = _events("near_miss_scan_atlandi")
    assert atla and atla[-1]["sebep"] == "kitap_dolu", \
        "P2 atlandı ama nedeni deftere düşmedi — iki haftalık sessizlik sınıfı hâlâ açık"


def test_kurak_bekcisi_aday_varken_sifir_golgede_esik_tablosuyla_uyarir(seeded, monkeypatch):
    """Aday var + near-miss 0 → warn; olay [sıkı, gevşek] eşik çiftlerini taşır ki 'gevşetme fiilen
    ölü mü?' sorusu canlı defterden tek satırla okunsun (07-30 sonrası ölümde tam bu tablo körd(ü)."""
    gercek = strategy.EntrySignal

    def _sahte_scan_all(bars, params, rs, ticker="?"):   # HER paramda konuşur → sıkı da bulur
        if ticker != "AAA":
            return {}
        c = float(bars["close"].iloc[-1])
        s = gercek(ticker=ticker, setup="breakout_vcp", entry_trigger=c, pivot=c,
                   stop=round(c * 0.95, 2), atr=1.0, rs_rating=80, score=75,
                   profit_target=round(c * 1.2, 2), size_r=1.0,
                   r_per_share=round(c * 0.05, 2), notes="vr=2.0 prox=0.5%")
        return {"breakout_vcp": s}

    monkeypatch.setattr(strategy, "scan_all", _sahte_scan_all)
    bars, idx = _universe()
    out = loop.daily_cycle(bars, idx, on_date=_last_date(idx))
    assert out["candidates"] >= 1 and out["near_miss"] == 0
    kurak = _events("near_miss_kurak")
    assert kurak, "aday varken 0 gölge OLAYSIZ geçti — yapısal şüphe yine sessiz"
    esik = kurak[-1]["esikler"]
    assert set(esik) == {"entry.min_volume_ratio", "entry.rs_rating_min",
                         "entry.min_score", "entry.pivot_proximity_pct"}
    for k, (siki, gevsek) in esik.items():               # tablo çift taşır: [sıkı, gevşek]
        assert siki is not None and gevsek is not None
    # varsayılan paramlarla gevşetme GERÇEKTEN gevşek olmalı (rx==eff çöküşü ayrı teşhistir)
    assert esik["entry.min_volume_ratio"][1] < esik["entry.min_volume_ratio"][0]

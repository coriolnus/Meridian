"""v113 — PRESCREEN ARACI (Aşama 2.6, 2026-07-29).

`scratchpad/onelem.py` deseninin kalıcılaştırılması. Çivilenen üç cümle:

  1. **Ölçüm aracı turdan tura DEĞİŞMEZ.** Elle yazılan her script biraz farklı oluyordu (farklı
     pencere, farklı k_probes, farklı fold) — yani iki turun sonucu kıyaslanamıyordu. Araç sabitse
     kıyas mümkün olur.
  2. **Canlı state'e tek bayt yazılmaz.** Canlı worker koşarken walk_forward yolundaki her yazım
     (`inc_cache.json`, `events.jsonl`, `sieve.json`...) canlı deftere düşerdi. "Dokunmadım" bir
     iddia değil, PARMAK İZİYLE ölçülmüş bir olgu olmalı.
  3. **`k_probes` DENENEN aday sayısıdır, ölçülen değil.** `--resume` ile yarıda kalan bir koşu
     devam ettiğinde ölçülmüşler atlanır ama kazananın-laneti cezası DÜŞMEZ; düşseydi istatistiksel
     çıta bir süreç kazası yüzünden sessizce gevşerdi.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from meridian import config, prescreen, store


# =================================================================================================
# Aday dizgisi ayrıştırma
# =================================================================================================
@pytest.mark.parametrize("ham,beklenen", [
    ("entry.min_score=80", [("entry.min_score", 80)]),
    ("exit.breakeven_r=0.5", [("exit.breakeven_r", 0.5)]),
    ("a=1,b=2.5,c=true,d=metin", [("a", 1), ("b", 2.5), ("c", True), ("d", "metin")]),
])
def test_aday_ayristirma(ham, beklenen):
    assert prescreen.parse_candidates(ham) == beklenen


def test_int_float_ONCE_denenir():
    """`min_score=80` float'a çevrilirse guard'ın ADIM kontrolü tam sayı bekleyen bir düğmede kayar."""
    (k, v), = prescreen.parse_candidates("entry.min_score=80")
    assert isinstance(v, int) and not isinstance(v, bool), f"{v!r} tipi {type(v)}"


@pytest.mark.parametrize("bozuk", ["", "knobdegersiz", "=5", "   "])
def test_bicimsiz_aday_SESSIZCE_ATLANMAZ_patlar(bozuk):
    """Sessiz atlama burada özellikle tehlikeli: kullanıcı üç aday verdiğini sanır, ikisi ölçülür ve
    k_probes de ikiye düşer — hem eksik ölçüm hem gevşemiş çıta, ikisi de görünmeden."""
    with pytest.raises(ValueError):
        prescreen.parse_candidates(bozuk)


# =================================================================================================
# Koşu — ağır bağımlılıklar taklit edilir (kapının YASASI test edilir, motorun kendisi değil)
# =================================================================================================
def _hafif(monkeypatch, oos_map: dict):
    """walk_forward/gate_eval/dataset taklidi. `oos_map`: knob → aday OOS skoru."""
    from meridian import backtest, dataset, reflect

    def _wf(params, *a, **k):
        skor = 0.10
        for knob, deger in oos_map.items():
            if params.get(knob) is not None and params.get(knob) == deger[0]:
                skor = deger[1]
        return {"oos_score": skor, "oos_folds": [{"n": 30, "avg_r": skor}],
                "oos_tail_risk": {"var_r": -1.0, "cvar_r": -1.5}, "params": params}

    monkeypatch.setattr(dataset, "load", lambda *a, **k: ({"AAA": None}, None))
    monkeypatch.setattr(backtest, "walk_forward", _wf)
    monkeypatch.setattr(reflect, "_gate_eval",
                        lambda inc, cand, k_probes=1, **k: (
                            cand["oos_score"] > inc["oos_score"] + 0.02,
                            {"fold_wins": "1/1", "tail_ok": True, "gate_law": "probabilistic",
                             "k_probes": k_probes, "margin": 0.02, "fold_law": "n_dengeli"},
                            "test"))
    monkeypatch.setattr(reflect, "_default_windows",
                        lambda: ("2022-01-01", "2023-07-01", "2025-12-31", "2026-07-10",
                                 ["2023-07-01", "2024-04-01"], 10))


def _canli_state(tmp_path) -> pathlib.Path:
    """Gerçek şemalı minik bir 'canlı' state: strategy.yaml + goal/bounds (guard gerçek koşsun)."""
    import shutil
    import yaml
    live = tmp_path / "canli_state"
    (live / "history").mkdir(parents=True)
    (live / "bars").mkdir(parents=True)
    repo = pathlib.Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, live / f)
    (live / "strategy.yaml").write_text(yaml.safe_dump(
        {"version": 3, "parent": 2, "params": {"entry.min_score": 60, "exit.breakeven_r": 1.0}}))
    return live


def test_kosu_sandbox_kopyasi_kurar_ve_CANLIYA_YAZMAZ(sandbox_state, tmp_path, monkeypatch):
    """Parmak izi kanıtı: koşu boyunca canlı dizinde tek dosya değişmemeli. Bu, aracın var oluş
    sebebidir — canlı worker koşarken ölçüm yapabilmek."""
    live = _canli_state(tmp_path)
    _hafif(monkeypatch, {"entry.min_score": (80, 0.20)})
    wd = tmp_path / "wd"
    rapor = prescreen.run(prescreen.parse_candidates("entry.min_score=80"), wd, live)
    assert rapor["canli_state_degisen_dosyalar"] == [], \
        f"canlı state'e yazıldı: {rapor['canli_state_degisen_dosyalar']}"
    assert (wd / "state" / "strategy.yaml").exists(), "sandbox kopyası kurulmadı"
    assert config.STATE == wd / "state", "config.STATE kopyaya yönlendirilmedi"


def test_guard_reddettigi_aday_OLCULMEZ_ve_k_probes_DISINDA_kalir(sandbox_state, tmp_path, monkeypatch):
    """Guard'ın reddettiği aday kapıya hiç YOKLAMA göndermedi — cezaya dahil edilmesi, yapılmamış
    bir aramanın bedelini ödemek olurdu. Ama sessizce de kaybolmaz: raporda gerekçesiyle durur."""
    live = _canli_state(tmp_path)
    _hafif(monkeypatch, {"entry.min_score": (80, 0.20)})
    # 999 aralık dışı (max 90) → guard reddeder; 80 geçerli.
    rapor = prescreen.run(prescreen.parse_candidates("entry.min_score=80,entry.min_score=999"),
                          tmp_path / "wd", live)
    assert rapor["k_probes"] == 1, f"k_probes guard reddini de saymış: {rapor['k_probes']}"
    assert rapor["n_denenen"] == 2, "denenen aday sayısı raporda yok"
    assert len(rapor["guard_reddi"]) == 1 and rapor["guard_reddi"][0]["yeni"] == 999, \
        f"guard reddi raporda görünmüyor: {rapor['guard_reddi']}"
    assert [a["knob"] for a in rapor["adaylar"]] == ["entry.min_score"]


def test_her_adaydan_SONRA_kismi_json_yazilir(sandbox_state, tmp_path, monkeypatch):
    """70 dakikalık bir koşu öldüğünde ölçülmüş adaylar da kayboluyordu. Kısmi dosya her adaydan
    sonra diske düşer."""
    live = _canli_state(tmp_path)
    _hafif(monkeypatch, {"entry.min_score": (80, 0.20), "exit.breakeven_r": (0.5, 0.05)})
    wd = tmp_path / "wd"
    prescreen.run(prescreen.parse_candidates("entry.min_score=80,exit.breakeven_r=0.5"), wd, live)
    kismi = json.loads((wd / prescreen.KISMI_DOSYA).read_text())
    assert len(kismi["adaylar"]) == 2 and kismi["kalan"] == [], kismi
    assert kismi["k_probes"] == 2


def test_resume_olculmusleri_atlar_ama_K_PROBES_DEGISMEZ(sandbox_state, tmp_path, monkeypatch):
    """ARACIN EN İNCE KURALI. Devam koşusunda daha az aday ÖLÇÜLÜR ama kazananın-laneti cezası
    DENENEN sayısına göredir; düşseydi istatistiksel çıta bir süreç kazası yüzünden gevşerdi ve
    bunu hiçbir yerde kimse görmezdi."""
    live = _canli_state(tmp_path)
    _hafif(monkeypatch, {"entry.min_score": (80, 0.20), "exit.breakeven_r": (0.5, 0.05)})
    wd = tmp_path / "wd"
    spec = "entry.min_score=80,exit.breakeven_r=0.5"
    ilk = prescreen.run(prescreen.parse_candidates(spec), wd, live)
    assert ilk["k_probes"] == 2

    olculen = []
    from meridian import backtest
    asil = backtest.walk_forward
    monkeypatch.setattr(backtest, "walk_forward",
                        lambda p, *a, **k: (olculen.append(p.get("entry.min_score")), asil(p, *a, **k))[1])
    ikinci = prescreen.run(prescreen.parse_candidates(spec), wd, live, resume=True)
    assert ikinci["k_probes"] == 2, f"resume k_probes'u düşürdü: {ikinci['k_probes']}"
    assert len(ikinci["adaylar"]) == 2, "resume ölçülmüş adayları rapordan düşürmüş"
    # incumbent HER KOŞUDA yeniden ölçülür (taban kıyasın diğer yarısıdır); adaylar atlanır.
    assert len(olculen) == 1, f"resume adayları yeniden ölçtü: {olculen}"
    assert all(a["k_probes"] == 2 for a in ikinci["adaylar"] if a.get("k_probes")), \
        "aday kayıtlarındaki k_probes beyanı değişmiş"


def test_kapinin_kendi_yasasi_cagrilir_ikinci_bir_yasa_YAZILMAZ():
    """Ön-elemenin GEÇTİ dediği bir aday canlı kapıda KALIRSA araç işe yaramaz. Bu yüzden pencere,
    parametre, ölçüm ve hüküm dört ayrı yerden DEĞİL, kapının kendi fonksiyonlarından gelir."""
    import inspect
    src = inspect.getsource(prescreen)
    for cagri in ("reflect._default_windows()", "reflect.params_of(", "backtest.walk_forward(",
                  "reflect._gate_eval("):
        assert cagri in src, f"kapının yasası kopyalanmış: '{cagri}' çağrısı yok"


def test_motor_isliyor_on_kosulu_olculur(sandbox_state, tmp_path, monkeypatch):
    """Hiçbir fold'un işlem seti/skoru değişmiyorsa düğme replay motorunda ÖLÜdür. Bunu ölçmeden
    "kapıdan geçmedi" demek, işlenmeyen bir düğmeyi çürütülmüş bir hipotez sanmaktır."""
    live = _canli_state(tmp_path)
    _hafif(monkeypatch, {})          # hiçbir knob skoru değiştirmiyor → motor ölü
    rapor = prescreen.run(prescreen.parse_candidates("entry.min_score=80"), tmp_path / "wd", live)
    assert rapor["adaylar"][0]["motor_isliyor"] is False, \
        "işlenmeyen düğme 'motor işliyor' diye raporlanmış"

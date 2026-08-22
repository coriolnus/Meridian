"""test_hayalet_dugme_v263.py — Ö-48 HAYALET SÜZGECİ (2026-08-22).

BAĞLAM (ROADMAP §48): keşif bütçesinin %62'si (29/47) canlı params'ta taşınmayan düğmelere
gidiyordu. O vakanın iki düğmesi de motorda KABLOLUYDU (`w_turnover` strategy.py, `vix_
backwardation_gate` regime.py) — yani sorun "okuyucusuz anahtar" değildi. AMA aynı vaka daha
sert bir sınıfın kapısını gösterdi: bounds.yaml'a MOTORUN HİÇ OKUMADIĞI bir anahtar girerse
(iki düğme bounds'a kablolamadan ÖNCE girmişti, 2026-07-30/08-01), arama bütçesi yapısal
olarak ölü sondalara akar ve bunu hiçbir kapı söylemez.

BU DOSYANIN ÇİVİLEDİĞİ SÖZLEŞME (hayalet süzgeci, `reflect.hayalet_suzgeci`):
  * HAYALET = motor zincirinde (`reflect.MOTOR_ZINCIRI` modülleri) string sabiti olarak HİÇ
    geçmeyen bounds anahtarı — yorum/docstring OKUYUCU SAYILMAZ (AST ölçümü).
  * Hayalet anahtar arama uzayına GİRMEZ (propose_deterministic explore +
    coordinate_descent_search enumerasyonu).
  * Süzüm SESSİZ DEĞİLDİR: `reflect_hayalet_dugme_suzuldu` olayı (anahtar listesi + süreç-içi
    kümülatif sayaç) + coordinate_descent_search dönüşünde `hayalet_suzulen` iz alanı.
  * Okuyucu kümesi ÖLÇÜLEMEZSE (motor kaynağı okunamadı/parse edilemedi) süzgeç FAIL-OPEN'dır:
    hiçbir anahtar süzülmez, hayalet=None (null=ölçülemedi≠0) ve `reflect_hayalet_olculemedi`
    uyarısı basılır — bozuk bir tarayıcının aramayı SESSİZCE daraltma yetkisi yoktur.
  * bounds.yaml'a DOKUNULMAZ: süzgeç dosyaya değil bellekteki sözlüğe uygulanır (İZLİ state,
    operatör/dagit kanalı).

BUGÜNKÜ ÖLÇÜM (2026-08-22, bu turda yeniden ölçüldü): repo bounds.yaml 32 anahtar taşıyor ve
32'sinin de motor-zinciri okuyucusu VAR — bugünkü hayalet listesi BOŞ. N2 bunu çiviler ki
süzgeç asla "bugün fazla süzüyor" hâline sessizce düşemesin.
"""
from __future__ import annotations

import pathlib

import pytest

from meridian import config, reflect, store

GHOST = "a.hayalet_dugme_v263"              # motor zincirinde bu literal YOK (test bunu N0'da kanıtlar).
                                            # Ad BİLEREK alfabetik en önde: `_ucb_rank` +inf beraberliğini
                                            # ADLA kırar — süzgeç yoksa explore İLK turda hayaleti önerir
                                            # (çivinin kırmızısı böyle keskinleşir, tesadüfi yeşil kalamaz).
REAL = "entry.min_score"                    # motor okuyucusu ölçülmüş gerçek düğme (strategy/guard/loop)


def _hayalet_ekle(sandbox_state, en_basa: bool = False) -> pathlib.Path:
    """Sandbox bounds.yaml'a (SANDBOX kopyası — repo İZLİ dosyası DEĞİL) hayalet anahtar ekler."""
    p = sandbox_state / "bounds.yaml"
    satir = f"{GHOST}: {{min: 0.0, max: 1.0, step: 0.1, type: float}}\n"
    icerik = p.read_text()
    p.write_text(satir + icerik if en_basa else icerik + "\n" + satir)
    config.bounds.cache_clear()
    return p


def _mini_bounds(sandbox_state) -> pathlib.Path:
    """İki anahtarlı küçük arama uzayı. `_ucb_rank` +inf beraberliğini ADLA kırar (`(-ucb, v)`) ve
    GHOST adı bilerek alfabetik en önde — süzgeç yoksa hayalet İLK aday olur (kırmızı keskin)."""
    p = sandbox_state / "bounds.yaml"
    p.write_text(f"{GHOST}: {{min: 0.0, max: 1.0, step: 0.1, type: float}}\n"
                 f"{REAL}: {{min: 40, max: 90, step: 1, type: int}}\n")
    config.bounds.cache_clear()
    return p


def _olaylar(ad: str) -> list:
    return [e for e in store.read_jsonl("events.jsonl") if e.get("event") == ad]


def _arama_stub(monkeypatch):
    """Ucuz koşum: walk_forward saplaması (test_selfheal_v10 kalıbı) — arama iskeleti gerçek."""
    monkeypatch.setattr(reflect.backtest, "walk_forward",
                        lambda *a, **k: {"oos_score": None, "oos_folds": [],
                                         "oos_tail_risk": None, "holdout_score": None})
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
    monkeypatch.delenv("MERIDIAN_PARALLEL_PROBES", raising=False)
    reflect.clear_wf_caches()
    reflect._PROBE_CACHE.clear()


# ---------------- N0: ölçüm ön koşulları ----------------
def test_N0_ghost_literali_motor_zincirinde_yok():
    """Testin kendi ön koşulu ÖLÇÜLÜR, varsayılmaz: GHOST literali motor kaynaklarında geçmiyor;
    REAL geçiyor. Bu düşerse suçlu süzgeç değil bu dosyanın fikstürüdür."""
    src_dir = pathlib.Path(reflect.__file__).resolve().parent
    for mod in reflect.MOTOR_ZINCIRI:
        kaynak = (src_dir / f"{mod}.py").read_text()
        assert GHOST not in kaynak, f"fikstür bozuldu: {GHOST} literali {mod}.py'de geçiyor"
    assert any(REAL in (src_dir / f"{m}.py").read_text() for m in reflect.MOTOR_ZINCIRI)


# ---------------- N1: hayalet süzülüyor ----------------
def test_N1_hayalet_suzuluyor(sandbox_state):
    _hayalet_ekle(sandbox_state)
    b = config.bounds()
    assert GHOST in b, "ön koşul: hayalet sandbox bounds'a girmedi"
    temiz, hayalet = reflect.hayalet_suzgeci(b, kaynak="test_n1")
    assert GHOST not in temiz, "motor-okuyucusuz anahtar arama uzayına girdi"
    assert hayalet == [GHOST]


# ---------------- N2: gerçek düğmeler süzülmüyor (bugünkü ölçüm: 32/32 okuyuculu) ----------------
def test_N2_gercek_dugmeler_suzulmuyor(sandbox_state):
    b = config.bounds()                      # conftest repo bounds.yaml'ı sandbox'a kopyalar
    assert len(b) >= 30, "ön koşul: gerçek bounds yüklenmedi"
    temiz, hayalet = reflect.hayalet_suzgeci(b, kaynak="test_n2")
    assert hayalet == [], f"gerçek düğme(ler) hayalet damgası yedi: {hayalet}"
    assert sorted(temiz) == sorted(b.keys())


# ---------------- N3: süzüm olayla görünür ----------------
def test_N3_suzum_olayla_gorunur(sandbox_state):
    _hayalet_ekle(sandbox_state)
    reflect.hayalet_suzgeci(config.bounds(), kaynak="test_n3")
    evs = _olaylar("reflect_hayalet_dugme_suzuldu")
    assert evs, "süzüm olaysız — sessiz daraltma (YASA 6 ihlali)"
    e = evs[-1]
    assert GHOST in (e.get("hayalet") or []), "olay süzülen anahtarın ADINI taşımıyor"
    assert e.get("n_hayalet") == 1 and e.get("kaynak") == "test_n3"
    assert isinstance(e.get("sayac_toplam"), int) and e["sayac_toplam"] >= 1
    assert len(str(e.get("detail") or "")) >= 20      # YASA 4 tarzı: gerekçesiz uyarı yok


# ---------------- N4: sayaç birikiyor ----------------
def test_N4_sayac_birikiyor(sandbox_state):
    _hayalet_ekle(sandbox_state)
    reflect.hayalet_suzgeci(config.bounds(), kaynak="test_n4a")
    reflect.hayalet_suzgeci(config.bounds(), kaynak="test_n4b")
    evs = _olaylar("reflect_hayalet_dugme_suzuldu")
    assert len(evs) >= 2
    assert evs[-1]["sayac_toplam"] > evs[-2]["sayac_toplam"] - 1  # monoton (süreç-içi kümülatif)
    assert evs[-1]["sayac_toplam"] >= evs[-2]["sayac_toplam"] + 1


# ---------------- N5: ölçülemedi → fail-open + uyarı (null=ölçülemedi≠0) ----------------
def test_N5_olculemedi_fail_open(sandbox_state, monkeypatch):
    _hayalet_ekle(sandbox_state)
    monkeypatch.setattr(reflect, "MOTOR_ZINCIRI", ("boyle_bir_motor_modulu_yok_v263",))
    b = config.bounds()
    temiz, hayalet = reflect.hayalet_suzgeci(b, kaynak="test_n5")
    assert hayalet is None, "ölçülemeyen okuyucu kümesi [] (sıfır hayalet) diye RAPORLANDI — uydurma"
    assert sorted(temiz) == sorted(b.keys()), "süzgeç KÖRKEN anahtar süzdü — fail-open ihlali"
    evs = _olaylar("reflect_hayalet_olculemedi")
    assert evs, "ölçüm düştü ve kimse duymadı (YASA 4)"
    assert len(str(evs[-1].get("detail") or "")) >= 20


# ---------------- N6: bounds dosyasına dokunulmuyor ----------------
def test_N6_bounds_dosyasina_dokunulmuyor(sandbox_state):
    p = _hayalet_ekle(sandbox_state)
    once = p.read_bytes()
    reflect.hayalet_suzgeci(config.bounds(), kaynak="test_n6")
    assert p.read_bytes() == once, "süzgeç sandbox bounds.yaml'ı DEĞİŞTİRDİ"
    assert GHOST in config.bounds(), "süzgeç bellekteki bounds sözlüğünü mutasyona uğrattı"
    repo_bounds = pathlib.Path(__file__).resolve().parent.parent / "state" / "bounds.yaml"
    assert GHOST.encode() not in repo_bounds.read_bytes(), "İZLİ repo bounds.yaml kirlendi"


# ---------------- N7: explore hayalet önermez ----------------
def test_N7_explore_hayalet_onermez(sandbox_state):
    """Mini uzayda hayalet İLK sırada (UCB +inf beraberliği adla kırılır, GHOST adı en önde):
    süzgeç OLMASA explore ilk turda hayaleti önerirdi. Süzgeçle öneri gerçek düğmeye gider."""
    _mini_bounds(sandbox_state)
    prop = reflect.propose_deterministic(explore=True)
    assert prop["variable"].split("@", 1)[0] != GHOST, "explore HAYALET düğme önerdi"
    evs = _olaylar("reflect_hayalet_dugme_suzuldu")
    assert evs and GHOST in (evs[-1].get("hayalet") or [])


# ---------------- N8: koordinat araması — sondalar temiz + iz alanı ----------------
def test_N8_coordinate_descent_hayalet_sondalamaz_ve_iz_tasir(sandbox_state, monkeypatch):
    _mini_bounds(sandbox_state)
    _arama_stub(monkeypatch)
    res = reflect.coordinate_descent_search(None, None, config.goal(), windows=None,
                                            k_max=1, budget=4)
    dokunulan = {t["variable"].split("@", 1)[0] for t in res["trace"]}
    assert GHOST not in dokunulan, "hayalet düğme SONDALANDI — arama bütçesi ölü anahtara aktı"
    assert res.get("hayalet_suzulen") == [GHOST], \
        "arama sonucu süzümün İZİNİ taşımıyor (YASA 6: iz alanı okuyucusuz/eksik)"
    assert res["evaluated"] >= 1, "ön koşul: gerçek düğme hiç sondalanmadı — test iskeleti bozuk"
    evs = _olaylar("reflect_hayalet_dugme_suzuldu")
    assert evs and evs[-1].get("kaynak") == "coordinate_descent_search"


# ---------------- N9: hayalet yokken iz alanı BOŞ LİSTE (None değil — ölçüldü ve temiz) --------
def test_N9_hayalet_yokken_iz_bos_liste(sandbox_state, monkeypatch):
    _arama_stub(monkeypatch)
    res = reflect.coordinate_descent_search(None, None, config.goal(), windows=None,
                                            k_max=1, budget=2)
    assert res.get("hayalet_suzulen") == [], \
        "hayalet yokken iz alanı [] olmalı (ölçüldü, temiz) — None 'ölçülemedi' demektir"

"""v112 — ROLLBACK LIKE-FOR-LIKE (Aşama 2.3, 2026-07-29).

Çivilenen cümle: **geri alma kararı, iki tarafı AYNI dönemde ve AYNI yıllıklandırmayla ölçen bir
kıyasa dayanmalıdır.**

Eski karar üç eksende birden ayrışan iki sayıyı karşılaştırıyordu: çocuğun CANLI skoru (95 işlem,
~4 ay, canlı motor, kendi süresine göre yıllıklandırılmış) ve ebeveynin BACKTEST OOS skoru (2,5 yıl,
replay motoru, 903 güne göre yıllıklandırılmış). `test_gate_statistics_v74::test_def8` bu sapmayı
canlı defterde 0.21 olarak ölçmüştü — geri alma eşiği ise 0.10. Yani kararın yönünü becerinin değil
takvimin belirlediği bir rejim.

Bu tur kararı, ebeveyn parametrelerinin ÇOCUĞUN CANLI DÖNEMİNE replay'ine ("would-have") bağlar.
Kapanmayan tek eksen (motor) gizlenmez, ÖLÇÜLÜR: çocuğun kendi parametreleri de aynı pencerede
replay edilir ve fark `motor_sapmasi` olarak kayda girer.
"""
from __future__ import annotations

import pytest

from meridian import baseline, config, memory, rollback, store, versioning


# =================================================================================================
# Kurulum yardımcıları — test_rollback_audit_v38'in deseniyle aynı (mock yok, state tohumlama)
# =================================================================================================
def _trades(n, version, r, start_day=1):
    return [{"id": f"T{version}{i:04d}", "ts_open": f"2026-04-{(i % 27) + start_day:02d}",
             "ts_close": f"2026-05-{(i % 27) + 1:02d}", "ticker": "AAA", "entry": 100.0, "qty": 10,
             "r_multiple": r, "pnl_dollars": r * 100.0, "costs": 1.0, "exit_reason": "stop",
             "regime": "trend_up", "strategy_version": version, "mfe_r": abs(r) + 0.2}
            for i in range(n)]


def _ship(version=2, parent=1, inc_oos=0.30):
    """Kapıdan geçmiş bir sürüm: strategy.yaml + karne satırı + ship hipotezi."""
    import yaml
    for v in (parent, version):
        (config.HISTORY).mkdir(parents=True, exist_ok=True)
        (config.HISTORY / f"v{v:04d}.yaml").write_text(yaml.safe_dump(
            {"version": v, "parent": (parent if v == version else None),
             "params": {"entry.min_score": 60 + v}}))
    config.strategy_path().write_text(yaml.safe_dump(
        {"version": version, "parent": parent, "params": {"entry.min_score": 60 + version}}))
    versioning.update_scoreboard(parent, backtest_oos=inc_oos)
    memory.record({"id": "H00001", "variable": "entry.min_score", "status": "live",
                   "version_to": version, "predicted_delta": 0.05,
                   "backtest": {"incumbent_oos": inc_oos}})


def _wh(delta_kaynak, canli=-0.20, wh_skor=None, verdict="olculdu"):
    """Sahte would-have ölçümü. `baseline.would_have_replay` PAHALIDIR (iki tam replay); kararın
    YASASINI test etmek için ölçümün kendisini taklit etmek yeterli ve doğrudur — ölçümün kendi
    doğruluğu ayrı testlerde (aşağıda) çivilenir."""
    wh_skor = wh_skor if wh_skor is not None else canli - delta_kaynak
    return {"verdict": verdict, "yontem": baseline.WOULD_HAVE_YONTEM, "pencere": ["2026-04-01", "2026-05-28"],
            "canli_skor": canli, "would_have_skor": wh_skor,
            "delta": round(canli - wh_skor, 4), "n_canli": 30, "n_would_have": 28,
            "cocuk_replay_skor": canli + 0.01, "motor_sapmasi": 0.01}


# =================================================================================================
# A) KARAR GİRDİSİ SEÇİMİ
# =================================================================================================
def test_olculmus_would_have_kararin_DAYANAGI_olur():
    k = rollback._karar_girdisi(cur_score=-0.20, par_score=0.30, wh=_wh(0.5))
    assert k["yontem"] == baseline.WOULD_HAVE_YONTEM, "ölçülmüş simetrik kıyas kullanılmamış"
    assert k["par"] == -0.70 and k["cur"] == -0.20, k


def test_olculemeyen_would_have_ESKI_YOLA_dusurur_ama_DAMGALAR():
    """Eski yol KALDIRILMADI: kaldırmak, bir veri kesintisinde geri almayı SESSİZCE dondururdu.
    Ama damgasız da değil — `legacy` damgası denetimde 'zayıf kanıt' diye okunabilir."""
    for wh in (None, {"verdict": "olculemez_replay", "delta": None}):
        k = rollback._karar_girdisi(cur_score=-0.2, par_score=0.3, wh=wh)
        assert k["yontem"] == rollback.LEGACY_YONTEM, f"damga yanlış: {k}"
        assert k["delta"] == pytest.approx(-0.5), k


# =================================================================================================
# B) KARARIN KENDİSİ
# =================================================================================================
def test_simetrik_kiyas_DOGRULARSA_geri_alma_YAPILIR(sandbox_state, monkeypatch):
    """Ebeveyn aynı dönemde GERÇEKTEN daha iyi olurdu → karar ayakta kalır ve kayda simetrik çift
    + yöntem damgası düşer."""
    config.reload_config()
    _ship(version=2, parent=1)
    store.write_jsonl("trades.jsonl", _trades(30, 2, -0.9) + _trades(30, 1, 0.8))
    monkeypatch.setattr(baseline, "would_have_replay",
                        lambda *a, **k: _wh(None, canli=-0.20, wh_skor=0.40))
    out = rollback.evaluate_outcomes(config.goal())
    assert out and out.get("rolled_back_from") == 2, f"karar buharlaştı: {out}"
    assert out["karar_yontemi"] == baseline.WOULD_HAVE_YONTEM, out
    h = memory.all_hypotheses()[0]
    d = h["realized_detail"]
    assert d["karar_cur"] == -0.20 and d["karar_par"] == 0.40, d
    assert d["would_have"]["motor_sapmasi"] == 0.01, "motor sapması kayda girmemiş"
    assert d["cur_score"] is not None and d["par_score"] is not None, \
        "eski alanlar kaldırılmış — geriye dönük uyum kırıldı"


def test_simetrik_kiyas_CURUTURSE_geri_alma_YAPILMAZ_ve_SESSIZ_KALMAZ(sandbox_state, monkeypatch):
    """ASIL KAZANÇ BU: eski asimetrik kıyas "geri al" derken ebeveynin aynı döneme replay'i farkı
    doğrulamıyorsa sürüm CANLIDA KALIR. Ve bu bir sessiz no-op olamaz — kararın yönünü değiştiren
    şey tam olarak bu turda yapılan ölçümdür, defterde görünmelidir."""
    config.reload_config()
    _ship(version=2, parent=1, inc_oos=0.30)
    store.write_jsonl("trades.jsonl", _trades(30, 2, -0.9))
    # Ebeveyn AYNI dönemde neredeyse aynı kötü sonucu verirdi → fark eşiğin altında.
    monkeypatch.setattr(baseline, "would_have_replay",
                        lambda *a, **k: _wh(None, canli=-0.20, wh_skor=-0.19))
    out = rollback.evaluate_outcomes(config.goal())
    assert out is None or not out.get("rolled_back_from"), f"çürütülmüş karar yine de uygulandı: {out}"
    assert int(config.load_strategy()["version"]) == 2, "sürüm gereksiz yere geri alındı"
    olaylar = [e for e in store.read_jsonl("events.jsonl")
               if e.get("event") == "rollback_like_for_like_overturn"]
    assert olaylar, "simetrik kıyasın kararı çürütmesi defterde görünmüyor (sessiz no-op)"
    assert olaylar[-1]["eski_delta"] < -0.10 <= olaylar[-1]["karar_delta"], olaylar[-1]


def test_would_have_YALNIZ_aday_tetiklendiginde_kosar(sandbox_state, monkeypatch):
    """MALİYET KAPISI: iki tam replay her P5 turunda koşarsa boşuna CPU yakılır. Sürüm iyi
    gidiyorken would-have HİÇ çağrılmamalı."""
    config.reload_config()
    _ship(version=2, parent=1, inc_oos=0.30)
    store.write_jsonl("trades.jsonl", _trades(30, 2, 0.9) + _trades(30, 1, 0.8))
    cagrildi = []
    monkeypatch.setattr(baseline, "would_have_replay",
                        lambda *a, **k: cagrildi.append(1) or _wh(0.0))
    rollback.evaluate_outcomes(config.goal())
    assert not cagrildi, "aday tetiklenmediği hâlde pahalı replay koşuldu"


def test_evaluate_outcomes_IDEMPOTAN_kalir(sandbox_state, monkeypatch):
    """Arka arkaya iki çağrı AYNI deltayı vermeli (v53'ün çivisi). Would-have ağdan bar çekseydi
    ya da tohumsuz bir rastgelelik taşısaydı bu düşerdi."""
    config.reload_config()
    _ship(version=2, parent=1)
    store.write_jsonl("trades.jsonl", _trades(30, 2, 0.5) + _trades(30, 1, 0.45))
    monkeypatch.setattr(baseline, "would_have_replay", lambda *a, **k: _wh(0.0))
    a = rollback.evaluate_outcomes(config.goal())
    b = rollback.evaluate_outcomes(config.goal())
    assert a and b and a["delta"] == b["delta"], f"idempotans kırıldı: {a} vs {b}"


# =================================================================================================
# C) ÖLÇÜMÜN KENDİSİ — would_have_replay
# =================================================================================================
def test_would_have_bar_onbellegi_BOSKEN_AGA_CIKMAZ(sandbox_state):
    """Bu fonksiyon bir KARAR yolunun içindedir. `load()` bayat önbellekte fetch eder ve fetch,
    corporate-action tespitini tetikleyip bar CSV'lerini yeniden yazabilir — yani geri alma kararı
    kendi altındaki veriyi değiştirebilirdi. Önbellek boşsa cevap 'ölçülemedi'dir, ağ değil."""
    config.reload_config()
    _ship(version=2, parent=1)
    store.write_jsonl("trades.jsonl", _trades(30, 2, -0.9))
    wh = baseline.would_have_replay(2, 1, config.goal())
    assert wh["verdict"] == "olculemez_replay", f"boş önbellekte ölçüm iddia edildi: {wh}"
    assert wh["delta"] is None, "ölçülemeyen hâlde delta uydurulmuş"
    assert "önbellek" in wh["neden"] or "bar" in wh["neden"], wh["neden"]


def test_would_have_PENCEREYI_canli_defterden_alir(sandbox_state):
    """Pencere takvimden ya da `live_since` damgasından değil, ölçülen işlemlerin GERÇEKTEN
    kapsadığı dönemden gelmeli — bir gün bile kaydırmak iki tarafa farklı piyasa verirdi."""
    config.reload_config()
    _ship(version=2, parent=1)
    store.write_jsonl("trades.jsonl", _trades(30, 2, -0.9))
    wh = baseline.would_have_replay(2, 1, config.goal())
    assert wh["pencere"][0].startswith("2026-04"), wh["pencere"]
    assert wh["pencere"][1].startswith("2026-05"), wh["pencere"]


def test_would_have_damga_yok_ise_OLCULEMEZ_PENCERE_der(sandbox_state):
    config.reload_config()
    _ship(version=2, parent=1)
    store.write_jsonl("trades.jsonl", [{"id": "T1", "strategy_version": 2, "r_multiple": -1.0}])
    wh = baseline.would_have_replay(2, 1, config.goal())
    assert wh["verdict"] == "olculemez_pencere" and wh["delta"] is None, wh


def test_cocuk_bacagi_YURURLUKTEKI_yaml_degil_KENDI_anlik_goruntusunu_kullanir(sandbox_state, monkeypatch):
    """MOTOR SAPMASI BACAĞININ DÜRÜSTLÜĞÜ. `strategy.yaml` yalnız `version` CANLI sürümse çocuğun
    parametrelerini taşır. Fonksiyon geçmiş bir kararı yeniden ölçmek için çağrıldığında (denetim,
    otopsi) yürürlükteki dosya BAŞKA bir sürümündür — onu "çocuk" diye replay etmek, kontrol
    bacağının sessizce yanlış bir şeyi ölçmesi olurdu.

    Kurgu: yürürlükte v3 var, ama v4'ün kararı yeniden ölçülüyor → çocuk bacağı v4'ün anlık
    görüntüsündeki parametreleri görmeli."""
    import yaml
    config.reload_config()
    _ship(version=3, parent=2)
    (config.HISTORY / "v0004.yaml").write_text(yaml.safe_dump(
        {"version": 4, "parent": 3, "params": {"entry.min_score": 88}}))
    store.write_jsonl("trades.jsonl", _trades(30, 4, -0.9))
    gorulen = []
    from meridian import backtest, dataset
    monkeypatch.setattr(dataset, "load_cached", lambda: ({"AAA": object()}, [1, 2, 3]))
    monkeypatch.setattr(backtest, "replay",
                        lambda params, *a, **k: gorulen.append(params.get("entry.min_score")) or
                        type("R", (), {"trades": []})())
    monkeypatch.setattr(backtest, "segment_score", lambda *a, **k: {"score": 0.1})
    baseline.would_have_replay(4, 3, config.goal())
    assert 88 in gorulen, f"çocuk bacağı v4'ün parametrelerini görmedi: {gorulen}"


def test_would_have_HICBIR_DOSYAYA_YAZMAZ(sandbox_state):
    """Saf ölçüm: `measure_parent_baseline`in ölç/hüküm/yayınla ayrımı burada da geçerli, farkı bu
    fonksiyonun YAYINLAMA bacağı hiç yok. Karneye tek satır yazsaydı, bir ölçüm denemesi canlı
    sürümün otomatik geri alınmasına yol açabilirdi."""
    config.reload_config()
    _ship(version=2, parent=1)
    store.write_jsonl("trades.jsonl", _trades(30, 2, -0.9))
    once = versioning.scoreboard()
    baseline.would_have_replay(2, 1, config.goal())
    assert versioning.scoreboard() == once, "would_have_replay karneye yazdı"

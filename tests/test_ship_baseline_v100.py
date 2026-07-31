"""test_ship_baseline_v100.py — GÖRÜNMEYEN UÇ, GÖRÜNMEYEN DAMGA, GÖRÜNMEYEN TABAN (2026-07-27).

Üç kalemin ortak sınıfı aynı: ölçüm YAPILIYOR ama ölçümün KRİTİK YARISI ize düşmüyor ve o yarı
tam da teşhisi taşıyan yarı oluyor.

  1. `hermes._parse_hyp` — bozuk gövdenin yalnız BAŞI kaydediliyordu. Kesilme KUYRUKTA görünür:
     baş sağlıklı bir JSON gibi okunur, kesik uç hiç görünmez. gemini bacağı günlerce yanlış
     sınıfta (`unparseable` ↔ `truncated`) durdu — biri biçim, diğeri bütçe sorunudur.
  2. `analytics.llm_opinion_calibration` — `n_pairs` yalnız KAPANAN işlemlerle dolar, yani
     damgalamanın diri mi ölü mü olduğunu haftalar sonra söyler. Beyin 07-21'den 07-26'ya ölüydü
     ve pano bu süre boyunca "çift yok" diyordu; "örneklem birikiyor" ile "damgalama durdu" aynı
     görünüyordu. Öncü gösterge çift beklemez: plan defteri günler önce konuşur.
  3. `reflect._submit_locked` — ship ebeveyn satırına bir SAYI yazıyordu ama HÜKÜM yazmıyordu.
     `baseline.measure_parent_baseline` aynı satıra hükmüyle yazar; iki yol aynı alan ailesini
     konuşmazsa `rollback._no_parent_diagnostics` birinden okuduğunu diğerinde göremez.

     ÖNCÜL DÜZELTMESİ (rapora da geçti): "kapıdan geçen bir ship ebeveyn satırına None yazabilir"
     ARTIK DOĞRU DEĞİL. `_gate_eval` 2026-07-22'den beri her iki yasada da `inc_oos is not None`
     arıyor; v3'ün skorsuz ship'i o delikten geçmişti ve delik kapalı. Ölçülmemiş taban dalı bu
     yüzden YAZILMADI (yazılsaydı ulaşılamaz bir uyarı olurdu — kurt masalının kod hâli); yerine
     şartın KENDİSİ aşağıda çivilendi: gevşerse orası kırmızı yanar ve dal sorusu geri gelir.
"""
from __future__ import annotations

import pytest
import yaml

from meridian import analytics, codelaw, config, hermes, memory, reflect, store, versioning
from tests import wf_fixtures as wf


# =================================================================================================
# 1) unparseable/refusal izi — KUYRUK da basılır
# =================================================================================================
def test_uzun_bozuk_metnin_kuyrugu_da_ize_duser():
    """KESİLME KUYRUKTA GÖRÜNÜR: 120 karakterlik baş, tavana dayanıp yarıda kesilmiş bir gövdeyi
    sağlıklı bir JSON'un başlangıcından ayırt edemiyordu."""
    t = '{"variable": "entry.min_score", "new": ' + "9" * 300 + ', "rationale": "yarıda kes'
    assert hermes._parse_hyp(t) is None

    reason, detail = hermes._trace_take()
    assert reason == hermes.EMPTY_UNPARSEABLE
    assert detail.startswith(f"len={len(t)} · "), f"uzunluk olgusu ize düşmedi: {detail}"
    assert "baş:" in detail and "son:" in detail
    assert t[:80] in detail, "baş kayboldu"
    assert t[-80:] in detail, "KUYRUK yine basılmadı — kesilme sınıfı hâlâ görünmez"


def test_kisa_bozuk_metinde_bas_ve_son_tekrar_edilmez():
    """Kısa metinde baş ve son ÇAKIŞIR; aynı gövdeyi iki kez basmak izi uzatır, bilgi eklemez."""
    t = "bu bir JSON değil"
    assert hermes._parse_hyp(t) is None

    reason, detail = hermes._trace_take()
    assert reason == hermes.EMPTY_UNPARSEABLE
    assert detail == f"len={len(t)} · {t}", f"kısa metinde tekrar/kırpma var: {detail}"


def test_red_sinifi_kuyruk_eklenince_de_bozulmaz():
    """Sınıf ayrımı (red = politika sorunu, unparseable = biçim sorunu) izin BİÇİMİNE bağlı
    değildir — kuyruk eklemek sınıflandırmayı kaydıramaz."""
    t = "Üzgünüm, bu isteğe yardımcı olamam. " + "gerekçe " * 40
    assert hermes._parse_hyp(t) is None

    reason, detail = hermes._trace_take()
    assert reason == hermes.EMPTY_REFUSAL
    assert detail.startswith(f"len={len(t.strip())} · ") and "son:" in detail


# =================================================================================================
# 2) llm_calibration — damgalamanın öncü göstergesi (çift beklemez)
# =================================================================================================
def _plan(pid: str, date: str, opinion: str | None = None) -> dict:
    r = {"id": pid, "ticker": "AAA", "date": date}
    if opinion:
        r["llm_opinion"] = opinion
    return r


def test_gorusluler_sayilir_ve_en_yeni_damga_tarihi_yayinlanir(sandbox_state):
    """Sayım GÖRÜŞE bakar, tarihe değil: görüşsüz ama daha YENİ bir plan damgayı ileri taşırsa
    ölü bir damgalama diri görünür — kaçınılan hata tam olarak budur."""
    store.write_jsonl("trade_plans.jsonl", [
        _plan("P1", "2026-07-18", "destekle"),
        _plan("P2", "2026-07-19"),                       # görüşsüz
        _plan("P3", "2026-07-26", "karşı"),
        _plan("P4", "2026-07-27"),                       # DAHA YENİ ama görüşsüz
    ])

    out = analytics.llm_opinion_calibration()

    assert out["n_plans_with_opinion"] == 2
    assert out["last_opinion_plan_date"] == "2026-07-26", \
        "görüşsüz ama daha yeni bir plan damga tarihini ileri taşıdı"
    assert out["n_pairs"] == 0, "öncü gösterge çift beklemez — bu ölçümün bütün sebebi bu"


def test_hic_gorus_yoksa_damga_tarihi_uydurulmaz(sandbox_state):
    """UYDURMA YASAĞI: görüş yoksa tarih de yoktur. `None` bir olgudur, boş dize bir kılıftır."""
    store.write_jsonl("trade_plans.jsonl", [_plan("P1", "2026-07-26"), _plan("P2", "2026-07-27")])

    out = analytics.llm_opinion_calibration()

    assert out["n_plans_with_opinion"] == 0
    assert out["last_opinion_plan_date"] is None


def test_oncu_gosterge_panoya_gercekten_ulasiyor():
    """YASA 6: üretilen alan tüketilir. "Panoda gösteriliyor" gerekçesi kanıtlanabilir olmalı."""
    assert codelaw.dashboard_mentions("n_plans_with_opinion")
    assert codelaw.dashboard_mentions("last_opinion_plan_date")


# =================================================================================================
# 3) ship anında taban hükmü
# =================================================================================================
@pytest.fixture
def seeded(sandbox_state):
    config.reload_config()
    (sandbox_state / "strategy.yaml").write_text(yaml.safe_dump(config.default_strategy()))
    config.HISTORY.mkdir(parents=True, exist_ok=True)
    config.dump_yaml(config.default_strategy(), config.HISTORY / "v0001.yaml")
    reflect._INC_CACHE.clear(); reflect._PROBE_CACHE.clear()
    yield sandbox_state
    config.reload_config()


def _wf(oos, fold_r=None):
    """test_reflect_gaps_v47._wf ile aynı köprü: dilimli fikstür → kapı olasılıksal yolu koşar.
    `fold_r` ayrı verilebilir çünkü OOS skoru None olan bir tarafın fold'ları yine sayısaldır."""
    r = oos if fold_r is None else fold_r
    return wf.wf_from_scores(oos, folds=((40, r), (40, r)))


def _kapiyi_sabitle(monkeypatch, inc_wf, cand_wf):
    from meridian import backtest
    fixtures = {1: inc_wf, 2: cand_wf}
    monkeypatch.setattr(backtest, "walk_forward",
                        lambda *a, **k: dict(fixtures[k.get("strategy_version", 1)]))
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
    reflect._INC_CACHE.clear(); reflect._PROBE_CACHE.clear()


def test_global_ship_ebeveyn_satirina_tabani_hukmuyle_yazar(seeded, monkeypatch):
    """Satırda bir SAYI olması, o sayının taban olarak kullanılabileceğini söylemez. Hüküm ve
    kaynak aynı satıra düşer ki `rollback` iki yoldan geleni aynı sözlükle okuyabilsin."""
    _kapiyi_sabitle(monkeypatch, _wf(0.10), _wf(0.90))

    res = reflect.submit({"variable": "entry.min_score", "new": 65})

    assert res["status"] == "shipped"
    sb = versioning.scoreboard()
    par = sb["versions"]["1"]
    assert par["backtest_oos"] == 0.10
    assert par["baseline_verdict"] == "olculebilir"
    assert par["baseline_source"] == "ship_gate" and par["baseline_measured_at"]
    assert par["baseline_n_trades"] == 80, "taban örneklemi fold n toplamı değil"
    assert "baseline_freq_ratio" not in par, \
        "ship anında ölçülemeyen sıklık oranı uyduruldu (adayın canlı defteri henüz boş)"
    assert sb["current_version"] == res["version"], \
        "ebeveyn yazımı adayın canlı sürüm işaretini ezdi — sıra bozuldu"


def test_hukum_dizgeleri_baseline_modulununkiyle_birebir_ayni():
    """İki yol AYRI dizge kullanırsa tüketici (`rollback._no_parent_diagnostics`, watchdog 7h)
    birinden okuduğunu diğerinde göremez — sessiz bir şema çatallanması."""
    import inspect

    from meridian import baseline
    src = inspect.getsource(baseline.measure_parent_baseline)
    assert '"olculebilir"' in src and '"olculemez_orneklem"' in src
    assert '"olculebilir"' in inspect.getsource(reflect._submit_locked)


def test_rejim_shipi_ebeveyn_satirina_hukum_yazmaz(seeded, monkeypatch):
    """MEVCUT KURAL BOZULMADI: rejim dilimli bir skor GLOBAL taban olamaz; rejim ship'i ebeveyn
    satırına hiç dokunmaz ve dolayısıyla oraya bir hüküm de bırakamaz."""
    _kapiyi_sabitle(monkeypatch, _wf(0.10), _wf(0.90))

    res = reflect.submit({"variable": "entry.min_score@chop", "new": 65})

    assert res["status"] == "shipped" and res["gate"]["eval_regime"] == "chop"
    vers = versioning.scoreboard()["versions"]
    assert "backtest_oos@chop" in vers[str(res["version"])], "rejim skoru damgasız yazıldı"
    assert "baseline_verdict" not in (vers.get("1") or {}), \
        "rejim ship'i ebeveyne GLOBAL bir taban hükmü bıraktı — uydurma delta kapısı"


def test_olculmemis_ebeveyn_tabani_kapidan_GECEMEZ(seeded, monkeypatch):
    """ÖNCÜLÜN KENDİSİ ÇİVİLENİYOR. v3 skorsuz ship edilebilmişti; `_gate_eval` 2026-07-22'den beri
    `inc_oos is not None` arıyor ve o delik kapalı. Bu test şartı kilitler: gevşediği gün ship yolu
    yine skorsuz bir ebeveyn satırı üretebilir hâle gelir ve ölçülmemiş-taban dalı gerçekten
    gerekir. Bugün gerekmiyor — bu yüzden yazılmadı."""
    _kapiyi_sabitle(monkeypatch, _wf(None, fold_r=0.10), _wf(0.90))

    res = reflect.submit({"variable": "entry.min_score", "new": 65})

    assert res["status"] == "rejected_by_backtest"
    assert res["gate"]["incumbent_oos"] is None
    # REDDİN GEREKÇESİ de kilitlenir: fold/kuyruk gibi BAŞKA bir vetodan kazara geçmiş olmak,
    # "ölçülmemiş taban ship edilemez" iddiasını KANITLAMAZ — yarın o veto gevşerse delik geri gelir.
    reason = " ".join(memory.all_hypotheses()[0].get("reject_reasons") or [])
    assert "TANIMSIZ" in reason or "undefined" in reason, f"red başka bir yasadan geldi: {reason}"
    assert versioning.scoreboard()["versions"] == {}, \
        "kapı reddetti ama karneye yine de bir satır düştü"

"""v182 — WP-M OKUMA NETLİĞİ + RAPOR KİMLİĞİ (2026-08-03).

WP-M metodoloji borçlarının iki kalemi. Ortak sınıf: **üretilen sayı doğru, OKUNUŞU yanlış.**
Hiçbiri bir hesabı düzeltmiyor; her biri bir sayının yanına, o sayıyı yanlış okumayı YAPISAL olarak
zorlaştıran bir cümle koyuyor. Çivilenen üç iddia:

  1. **`DD_VETO_MARGIN` mutlak bir düşüş tavanı DEĞİLDİR.** Veto koşulu
     `candidate_dd > incumbent_dd + marj`dır — marj aday↔incumbent FARKINA uygulanır. Mutlak
     bütçe AYRI bir sayıdır (`goal.max_drawdown`) ve marj onun yarısıdır. Bu ayrım bir kez
     kaçırıldı (bir ölçüm raporunda MUTLAK M2M düşüşü 0,04 ile kıyaslanıp "ihlal" yazıldı), yani
     "okuyan anlar" varsayımı ÖLÇÜLMÜŞ biçimde yanlış. Oran UYDURULMAZ: goal.yaml'dan okunup her
     çağrıda hesaplanır — bütçe değişirse beyan da değişir.

  2. **`dd_mtm_*` ailesi `dd_*`ın ikinci ölçümü değil, BAŞKA BİR CETVELdir** (kapanmış-işlem eğrisi
     vs günlük mark-to-market eğrisi) ve defter sözleşmesi bunu söylemek zorundadır. Alan adları
     YAZARDAN doğrulanır (diskte 0 satır var — UYDURMA YASAĞI gereği bu testte de yazım satırı
     kaynak alınır, sözleşme metniyle yazım BİRBİRİNE ÇİVİLENİR).

  3. **Bir ölçüm raporu "hangi kod" kadar "ne zaman" sorusunu da kendi içinde cevaplar.** git SHA
     damgası 2026-08-02'de kondu; zaman damgası raporun DIŞINDA (dosya mtime'ı) kalmıştı ve mtime
     kopyalanan/rsync'lenen/arşivden çıkarılan bir raporda yeniden yazılır. Aynı SHA'da iki kez
     koşulmuş bir ön-eleme yalnız SHA ile ayırt EDİLEMEZ.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib

import pytest

from meridian import analytics, config, ledgers, prescreen, shadowlaw


# =================================================================================================
# 1. DD_VETO_MARGIN OKUMASI — GÖRECE MARJ, MUTLAK EŞİK DEĞİL
# =================================================================================================
def test_marj_mutlak_tavanin_YARISI_olarak_OLCULUR_yazilmaz(sandbox_state):
    """Oran kodda sabit değil: `goal.max_drawdown`dan türetilir. Bütçe değişirse beyan da değişir —
    donmuş bir "0,5" cümlesi bir gün sessizce yalan söylerdi."""
    r = analytics._dd_veto_okumasi()
    tavan = float(config.goal()["max_drawdown"])
    assert r["marj"] == shadowlaw.DD_VETO_MARGIN
    assert r["mutlak_tavan"] == tavan
    assert r["mutlak_tavan_kaynagi"] == "goal.max_drawdown"
    assert r["marj_tavan_orani"] == pytest.approx(shadowlaw.DD_VETO_MARGIN / tavan)
    # Bugünkü sözleşme: 0,04 / 0,08 = bütçenin tam yarısı (shadowlaw türetim (2)).
    assert r["marj_tavan_orani"] == 0.5


def test_beyan_MUTLAK_ESIK_OKUMASINI_adiyla_reddeder(sandbox_state):
    """Beyanın işi bir tanım vermek değil, YANLIŞ OKUMAYI adıyla yasaklamaktır."""
    r = analytics._dd_veto_okumasi()
    assert "DEĞİL" in r["tip"] and "GÖRECE" in r["tip"]
    assert "candidate_dd > incumbent_dd + marj" in r["kural"]
    b = r["beyan"]
    assert "TAVANI DEĞİLDİR" in b
    assert "goal.max_drawdown" in b
    assert "mtm_dd_veto" in b, "yanlış okumanın GERÇEKLEŞTİĞİ yüzey adıyla anılmıyor"


def test_tavan_okunamazsa_UYDURULMAZ_None_ve_neden(sandbox_state, monkeypatch):
    """UYDURMA YASAĞI: bütçe okunamıyorsa oran None + neden'dir. Marj yine yazılır (o koddaki
    sabittir; okunamamış bir bütçe onu geçersiz kılmaz) — ama "yarısıdır" cümlesi kurulmaz."""
    def _patlat():
        raise OSError("goal.yaml yok (test)")
    _patlat.cache_clear = lambda: None      # fikstür sökümü gerçek `goal`daki kancayı çağırıyor
    monkeypatch.setattr(config, "goal", _patlat)
    r = analytics._dd_veto_okumasi()
    assert r["marj"] == shadowlaw.DD_VETO_MARGIN
    assert r["mutlak_tavan"] is None and r["marj_tavan_orani"] is None
    assert "OSError" in (r["tavan_neden"] or ""), r["tavan_neden"]
    assert "ölçülemedi" in r["beyan"]


def test_bolme_sifira_dusmez(sandbox_state, monkeypatch):
    """max_drawdown=0 patolojik bir sözleşmedir; oran ZeroDivisionError yerine None olur."""
    _sifir = lambda: {"max_drawdown": 0.0}          # noqa: E731 — tek satırlık fikstür taklidi
    _sifir.cache_clear = lambda: None
    monkeypatch.setattr(config, "goal", _sifir)
    r = analytics._dd_veto_okumasi()
    assert r["mutlak_tavan"] == 0.0 and r["marj_tavan_orani"] is None


def test_pano_satiri_CIPLAK_SAYIYI_beyansiz_basmaz(sandbox_state):
    """YASA 6 + okuma netliği: `dd_veto_margin` panoya giden satırda tek başına duruyordu.
    Beyan artık AYNI sözlükte, sayının yanında."""
    satir = analytics.shadow_law_row()
    assert satir["dd_veto_margin"] == shadowlaw.DD_VETO_MARGIN
    assert satir["dd_veto_okumasi"]["marj_tavan_orani"] == satir["dd_veto_okumasi"]["marj"] / float(
        config.goal()["max_drawdown"])
    # api.py bu satırı BÜTÜN olarak servis eder (anahtar seçmez) — tüketici zinciri kopmuyor.
    api_src = (pathlib.Path(__file__).resolve().parent.parent / "meridian" / "api.py").read_text()
    assert "an.shadow_law_row()" in api_src


# =================================================================================================
# 2. dd_mtm_* SÖZLEŞME NOTU — İKİ CETVEL, TEK SÜTUN DEĞİL
# =================================================================================================
def _note() -> str:
    return ledgers.CONTRACTS["validation_ledger.jsonl"].note


def test_sozlesme_dd_mtm_ALANLARINI_yazardan_dogrulanmis_sekilde_anar():
    """Alan adları sözleşmede yazıyorsa, YAZIM satırında da yazıyor olmalı. İkisi ayrışırsa
    sözleşme "diskte olmayan bir alanı" tarif eder — 2026-07-21'in sözleşmesiz-defter dersinin
    ters yönü."""
    note = _note()
    reflect_src = (pathlib.Path(__file__).resolve().parent.parent
                   / "meridian" / "reflect.py").read_text()
    kayit = reflect_src.split("validation.record_candidate(")[1].split("\n    return passes")[0]
    for alan in ("dd_mtm_durum", "dd_mtm_bagli", "candidate_dd_mtm", "incumbent_dd_mtm"):
        assert f"`{alan}`" in note or alan in note, f"sözleşme {alan} alanını anmıyor"
        assert f'"{alan}"' in kayit, f"{alan} defter satırına YAZILMIYOR — sözleşme yanlış tarif ediyor"


def test_sozlesme_kapi_kaydinda_KALAN_alanlari_defterde_ARAMAYIN_der():
    """`dd_mtm_ok`/`dd_mtm_beyan` kapı kaydındadır, defterde YOKTUR. Bunu söylemeyen bir sözleşme,
    tüketiciyi sessizce None okumaya bırakırdı."""
    note = _note()
    reflect_src = (pathlib.Path(__file__).resolve().parent.parent
                   / "meridian" / "reflect.py").read_text()
    kayit = reflect_src.split("validation.record_candidate(")[1].split("\n    return passes")[0]
    assert '"dd_mtm_ok"' not in kayit and '"dd_mtm_beyan"' not in kayit
    assert "dd_mtm_ok" in note and "dd_mtm_beyan" in note
    assert "BU DEFTERDE YOKTUR" in note


def test_sozlesme_IKI_CETVELI_ayirir_ve_ihlal_baglanmadiyi_hukum_saymaz():
    note = _note()
    assert "BAŞKA BİR CETVELDİR" in note
    assert "mark-to-market" in note and "KAPANMIŞ-İŞLEM" in note
    assert "ihlal_baglanmadi" in note and "HÜKÜM DEĞİLDİR" in note
    assert "havuzlanamaz" in note, "iki ailenin tek sütunda toplanamayacağı yazılı değil"


def test_sozlesme_marji_GORECE_diye_isaretler():
    """Aynı yanlış okuma defter satırında da mümkündü: `candidate_dd` tek başına marjla
    kıyaslanabilir. Sözleşme bunu adıyla yasaklar."""
    note = _note()
    assert "MUTLAK bir düşüş" in note and "goal.max_drawdown" in note
    assert "candidate_dd > incumbent_dd + marj" in note


def test_dd_mtm_alanlari_ZORUNLU_alan_OLMAZ():
    """Retro damga yasağı: 2026-08-02 öncesi satırlar bu alanları taşımaz; `required`a eklemek
    geçmişin tamamını ihlal ilan ederdi."""
    c = ledgers.CONTRACTS["validation_ledger.jsonl"]
    for alan in ("dd_mtm_durum", "dd_mtm_bagli", "candidate_dd_mtm", "incumbent_dd_mtm",
                 "dd_ok", "candidate_dd", "yasa_surumu"):
        assert alan not in c.required, f"{alan} zorunlu alan yapılmış"
    # Damgasız eski bir satır sözleşmeyi İHLAL ETMEZ.
    eski = {"ts": "2026-07-01", "fingerprint": "abc", "etiket": "x", "seri": [],
            "sharpe_gozlem": 0.1, "n_trials": 3, "passes": False}
    assert ledgers.validate_row("validation_ledger.jsonl", eski) == []


# =================================================================================================
# 3. PRESCREEN ÜRETİM ZAMANI — DAMGANIN İKİNCİ YARISI
# =================================================================================================
def _hafif(monkeypatch, oos_map: dict):
    """test_prescreen_v113'ün taklidi (aynı desen): walk_forward/gate_eval/dataset ucuzlatılır."""
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


def test_rapor_KENDI_ICINDE_ne_zaman_uretildigini_soyler(sandbox_state, tmp_path, monkeypatch):
    """Dosya mtime'ı kopyalanınca yeniden yazılır; rapor kendi zamanını taşımalı. UTC ve
    ayrıştırılabilir olmalı (dizgi "şimdi"nin makul bandında)."""
    live = _canli_state(tmp_path)
    _hafif(monkeypatch, {"entry.min_score": (80, 0.20)})
    once = dt.datetime.now(dt.timezone.utc)
    rapor = prescreen.run(prescreen.parse_candidates("entry.min_score=80"), tmp_path / "wd", live,
                          log=lambda *a, **k: None)
    sonra = dt.datetime.now(dt.timezone.utc)
    t = dt.datetime.fromisoformat(rapor["uretim_zamani"])
    assert t.tzinfo is not None, "zaman damgası saat dilimsiz — UTC iddiası doğrulanamaz"
    assert once - dt.timedelta(seconds=2) <= t <= sonra, (rapor["uretim_zamani"], once, sonra)
    # KOD KİMLİĞİ (2026-08-02'de kondu) yerinde duruyor — bu tur onu BOZMADI.
    assert "kod_surumu" in rapor and "olcum_araclari_surum" in rapor["kod_surumu"]


def test_kismi_ve_nihai_rapor_AYNI_zamani_tasir(sandbox_state, tmp_path, monkeypatch):
    """Damgayla aynı donma kuralı: iki dosya TEK koşuyu adlandırır. Kısmi dosya her adaydan sonra
    yeniden yazılır; her yazımda yeni bir `now()` alınsaydı iki rapor iki koşu gibi okunurdu."""
    live = _canli_state(tmp_path)
    _hafif(monkeypatch, {"entry.min_score": (80, 0.20), "exit.breakeven_r": (0.5, 0.05)})
    wd = tmp_path / "wd"
    rapor = prescreen.run(prescreen.parse_candidates("entry.min_score=80,exit.breakeven_r=0.5"),
                          wd, live, log=lambda *a, **k: None)
    kismi = json.loads((wd / prescreen.KISMI_DOSYA).read_text())
    assert kismi["uretim_zamani"] == rapor["uretim_zamani"]
    assert kismi["kod_surumu"] == rapor["kod_surumu"]
    # TEK KEZ dondurulur: koşu içinde ikinci bir "şimdi" okuması olmamalı.
    src = (pathlib.Path(__file__).resolve().parent.parent / "meridian" / "prescreen.py").read_text()
    assert src.count("dt.datetime.now(") == 1, "zaman damgası birden fazla yerde alınıyor"


def test_guard_hepsini_reddettiginde_de_damgalanir(sandbox_state, tmp_path, monkeypatch):
    """Bu dal kuyruğa KALICI bir hata satırı bırakır. Damgasız bir red, "hangi bounds/kod hâlinde
    reddedildi?" sorusunu cevapsız bırakır — guard redleri tam olarak bounds değişince anlam
    değiştiren kayıtlardır."""
    live = _canli_state(tmp_path)
    _hafif(monkeypatch, {})
    rapor = prescreen.run(prescreen.parse_candidates("entry.min_score=999"), tmp_path / "wd", live,
                          log=lambda *a, **k: None)
    assert rapor["hata"] == "guard_hepsini_reddetti"
    assert rapor["uretim_zamani"] and rapor["kod_surumu"]["olcum_araclari_surum"]


def test_kuyruk_ozeti_kimligi_TASIR_ve_eksik_damgada_PATLAMAZ():
    """Kum havuzu silinebilir, kuyruk satırı kalıcıdır: kısa sha + zaman özete kopyalanır.
    Damga yoksa (eski rapor) alan None'dır — KeyError değil."""
    rapor = {"adaylar": [], "k_probes": 1, "workdir": "/tmp/x", "sure_s": 1.0,
             "uretim_zamani": "2026-08-03T10:00:00+00:00",
             "kod_surumu": {"git_head_kisa": "abc1234", "kirli_agac": False}}
    o = prescreen.kuyruk_ozeti(rapor)
    assert o["uretim_zamani"] == "2026-08-03T10:00:00+00:00"
    assert o["kod_surumu_kisa"] == "abc1234" and o["kirli_agac"] is False
    eski = prescreen.kuyruk_ozeti({"adaylar": [], "k_probes": 1})
    assert eski["kod_surumu_kisa"] is None and eski["uretim_zamani"] is None
    # ŞEMA BOZULMADI: eski alanlar yerinde.
    for alan in ("n_aday", "k_probes", "workdir", "sure_s", "pencere_id", "adaylar", "guard_reddi"):
        assert alan in o, f"kuyruk özetinden {alan} düştü"

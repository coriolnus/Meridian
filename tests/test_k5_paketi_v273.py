"""test_k5_paketi_v273.py — K5 paketi (2026-08-23): 25a KALDIR + 25c DAMGA + 25d EZER + K1 @chop.

Kaynaklar: docs/DENETIM-OLU-BILESEN-ENVANTERI-2026-08-13.md (envanter) + ROADMAP WP6-B
(25a/c/d + Rol-1 üstün-hükümleri) + EDG-2026-048 (chop NO-GO → üretim duraklatması).

Beş kapı:
  (a) 25a KALDIR — düşen goal.yaml alanları YOK + mezar taşları VAR (spy_sma_gate emsali).
  (b) sessiz-diriliş çivisi — kaldırılan adların kodda OKUYUCUSU yok (ast dizgi taraması,
      pozitif kontrollü) ve guard ad kümelerinde değiller.
  (c) 25c DAMGA — `no_trade_before_bars` LIMIT_KEYS'te YOK, REPLAY_WARMUP_KEYS'te VAR, goal
      yorumu düzeltilmiş (intraday çağrışımı gitti), davranış AYNEN (bar_i kuralı + Hermes reddi).
  (d) K1 — `@chop` ÜRETİMDEN çıktı (şema + bg seçici + bg tur + öneri çivisi + canlı arama
      kapsamı) ama NOTLANDIRMA yolu duruyor (resolve_params chop'u hâlâ çözer, chop
      VALID_REGIMES'te).
  (e) pozitif kontroller — tarayıcılar gerçekten görüyor; 25d damgalarının onu da yerinde.

NOT (envanter yeniden-doğrulaması, 25a şartı): 12 registry alanının 9'u bugün OKUYUCULU çıktı ve
KALDIRILMADI (ayrıntı ops/registry_olu_alan_budamasi.py docstring'i); kalan 3'ünün budaması canlı
state işi olduğundan ops betiğine indi — betiğin sözleşmesi burada test edilir.
"""
from __future__ import annotations

import ast
import json
import pathlib

import pytest
import yaml

from meridian import broker, config, guard, hermes, hermes_runtime as hr, store
from tests.conftest import betikten_modul_yukle

REPO = pathlib.Path(__file__).resolve().parent.parent
GOAL_TXT = (REPO / "state" / "goal.yaml").read_text(encoding="utf-8")
GOAL = yaml.safe_load(GOAL_TXT)

KALDIRILAN_UST = ("schema_version", "universe", "style", "session_tz",
                  "backtest_gate", "explore_rate", "fill")


# =================================================================================================
# (a) 25a KALDIR — alan YOK, mezar taşı VAR
# =================================================================================================
def test_a1_kaldirilan_ust_anahtarlar_goal_yamlda_yok():
    for k in KALDIRILAN_UST:
        assert k not in GOAL, f"25a: `{k}` goal.yaml'a GERİ GELMİŞ (mezar taşı deliniyor)"


def test_a2_execution_v2_tif_yok_ve_yasa_gtc_ye_duser():
    assert "tif" not in GOAL["execution_v2"], "25a: execution_v2.tif geri gelmiş"
    # davranış çivisi: alan yokken yasa fail-safe `gtc`ye düşer (tek-uçlu beyaz-liste)
    assert broker.entry_law(GOAL["execution_v2"])["tif"] == "gtc"


def test_a3_kill_switch_file_limitsten_dustu_halt_yolu_sabit():
    assert "kill_switch_file" not in GOAL["limits"], "25a: kill_switch_file geri gelmiş"
    # kill-switch'in tek gerçeği: health.py STATE/"HALT" sabit yolu (anahtara hiç bakmıyordu)
    src = (REPO / "meridian" / "health.py").read_text(encoding="utf-8")
    assert 'STATE / "HALT"' in src or 'STATE/"HALT"' in src.replace(" ", ""), \
        "health.py HALT sabit yolu kayboldu — kill-switch gerçeği taşındıysa bu test güncellenmeli"


def test_a4_mezar_taslari_goal_yamlda_duruyor():
    for tas in ("MEZAR TAŞI: schema_version", "MEZAR TAŞI: backtest_gate",
                "MEZAR TAŞI: explore_rate", "MEZAR TAŞI: fill", "MEZAR TAŞI: tif",
                "MEZAR TAŞI: kill_switch_file"):
        assert tas in GOAL_TXT, f"goal.yaml mezar taşı silinmiş: {tas}"
    # her taş envanter atfı + tarih taşır (SİLME = mezar taşı sözleşmesi)
    assert GOAL_TXT.count("2026-08-23") >= 6
    assert "DENETIM-OLU-BILESEN-ENVANTERI-2026-08-13" in GOAL_TXT


def test_a5_guard_kumeleri_kaldirilanlari_tasimiyor_mezar_tasi_var():
    for k in KALDIRILAN_UST:
        assert k not in guard.GOAL_KEYS, f"{k} GOAL_KEYS'te — küme mezarı deliniyor"
    assert "kill_switch_file" not in guard.LIMIT_KEYS
    src = (REPO / "meridian" / "guard.py").read_text(encoding="utf-8")
    assert "MEZAR TAŞI (25a, 2026-08-23)" in src, "guard.py 25a mezar taşı silinmiş"


# =================================================================================================
# (b) SESSİZ-DİRİLİŞ ÇİVİSİ — kaldırılan adların kodda okuyucusu yok
# =================================================================================================
def _tum_dizgiler() -> set:
    """meridian/**/*.py içindeki TÜM dizgi sabitlerini toplar (yorumlar zaten ast dışında)."""
    out: set = set()
    for p in (REPO / "meridian").rglob("*.py"):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:  # sessiz-yutma değil: bozuk dosya bu çivinin konusu değil, derleme testinin konusu
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                out.add(node.value)
    return out


def test_b1_kaldirilan_adlar_hicbir_kod_dizgisinde_yok():
    """Tek-anlamlı adlar için okuyucu-yokluğu: kod bu adları DİZGİ olarak dahi taşımıyor
    (`goal["backtest_gate"]` tarzı her okuma bir dizgi sabiti gerektirir). `schema_version` /
    `universe` / `style` / `fill` bu taramaya GİREMEZ — aynı ad başka anlamlarla meşru yaşıyor
    (DB tablosu, rapor alanı); onların çivisi (a) + guard kümeleridir."""
    dizgiler = _tum_dizgiler()
    for ad in ("backtest_gate", "explore_rate", "kill_switch_file", "session_tz"):
        assert ad not in dizgiler, f"`{ad}` koda dizgi olarak geri gelmiş — okuyucu doğmuş olabilir"


def test_b2_pozitif_kontrol_tarayici_gercek_okumalari_goruyor():
    """(b1)'in tarayıcısı çalışıyor mu? CANLI bir goal anahtarının okunduğunu görmeli."""
    dizgiler = _tum_dizgiler()
    for canli in ("reflection_every", "no_trade_before_bars", "max_accepted_changes_per_month"):
        assert canli in dizgiler, f"pozitif kontrol düştü: `{canli}` okuması görünmüyor"


def test_b3_registry_budama_betigi_sozlesmesi():
    """25a registry kolu: budama CANLI state işi → ops betiği. Sözleşme: (1) yalnız yeniden
    doğrulanmış 3 okuyucusuz alan düşer, (2) okuyuculu alanlar korunan kümede ve kesişim boş,
    (3) budama korunanlara dokunmaz + idempotent."""
    mod = betikten_modul_yukle(REPO / "ops" / "registry_olu_alan_budamasi.py",
                               "registry_budama")

    assert set(mod.OLU_ALANLAR) == {"api_free", "failure_count", "engine"}
    # envanterin 12'sinden okuyucu kazananlar korunan listede (kaldırılamaz)
    assert {"merged_into", "retired_at", "agent_authored", "aktivasyon_kosulu",
            "stale_last_run_cleared", "retired_folder", "retired_requires",
            "denetim_notu", "retired_from_pipeline"} <= set(mod.KORUNAN_ALANLAR)
    assert not set(mod.OLU_ALANLAR) & set(mod.KORUNAN_ALANLAR)

    veri = {"skills": {
        "x": {"enabled": True, "api_free": True, "engine": "native", "merged_into": "y"},
        "y": {"failure_count": 3, "retired_at": "2026-07-29", "shadow": True},
        "bozuk": "dict-degil",
    }}
    yeni, sayim = mod.buda(veri)
    assert sayim == {"api_free": 1, "failure_count": 1, "engine": 1}
    assert yeni["skills"]["x"] == {"enabled": True, "merged_into": "y"}          # korunan kaldı
    assert yeni["skills"]["y"] == {"retired_at": "2026-07-29", "shadow": True}
    assert veri["skills"]["x"]["api_free"] is True, "buda() girdiyi yerinde değiştirdi (saf değil)"
    yeni2, sayim2 = mod.buda(yeni)
    assert sum(sayim2.values()) == 0, "idempotent değil"


# =================================================================================================
# (c) 25c DAMGA — no_trade_before_bars: sınıf değişti, davranış AYNEN
# =================================================================================================
def test_c1_replay_sinifi_ve_kume_uyeligi():
    assert "no_trade_before_bars" not in guard.LIMIT_KEYS, \
        "25c: canlı-zarf görüntüsü geri gelmiş (LIMIT_KEYS)"
    assert guard.REPLAY_WARMUP_KEYS == {"no_trade_before_bars"}
    assert GOAL["limits"]["no_trade_before_bars"] == 3, "değer değişmiş — damga davranış değiştirmezdi"


def test_c2_goal_yorumu_duzeltildi_intraday_cagrisimi_gitti():
    assert "skip the first N bars after the open" not in GOAL_TXT, \
        "yanıltıcı intraday yorumu geri gelmiş"
    assert "REPLAY ISINMA KURALIDIR" in GOAL_TXT
    assert "25c ÜSTÜN-HÜKÜM" in GOAL_TXT


def test_c3_hermes_yine_oneremez_davranis_aynen():
    """LIMIT_KEYS'ten çıkmak Hermes'e kapı AÇMADI: çıplak ad da `limits.` önekli ad da reddedilir
    (guard saf — hüküm yalnız argümanların fonksiyonu, dosya okumaz)."""
    for var in ("no_trade_before_bars", "limits.no_trade_before_bars"):
        v = guard.validate_change({"variable": var, "new": 5}, {"entry.min_score": 60},
                                  {}, {"max_accepted_changes_per_month": 8}, [], 0)
        assert v.ok is False, f"{var} guard'ı geçti — 25c 'davranış aynen' sözü kırıldı"
        assert "immutable" in str(v.reasons[0])


def test_c4_bar_i_kurali_backtestte_ayakta():
    """Davranış çivisi: replay ısınma kuralı kaynakta AYNEN — limits'ten okunur ve seans sırası
    (`bar_i`) ile karşılaştırılır. (Tam koşum değil kaynak-sözleşmesi: worktree'de state yok.)"""
    src = (REPO / "meridian" / "backtest.py").read_text(encoding="utf-8")
    assert 'no_trade_before = int(limits.get("no_trade_before_bars", 0))' in src
    assert "bar_i >= no_trade_before" in src


# =================================================================================================
# (d) K1 — @chop ÜRETİMDEN çıktı, NOTLANDIRMA duruyor
# =================================================================================================
def test_d1_sema_tesviki_gitti_duraklatma_beyanli():
    blob = json.dumps(hermes.HYP_SCHEMA)
    assert "@chop" not in blob or "PAUSED" in blob, "şema hâlâ @chop örnekliyor"
    assert "exit.trail_atr_mult@chop" not in blob, "eski @chop örneği geri gelmiş"
    assert "EDG-2026-048" in blob, "duraklatmanın kart atfı şemadan silinmiş"
    assert "EDG-2026-048" in hermes.SYSTEM and "PAUSED" in hermes.SYSTEM
    assert "only exists in chop" not in hermes.SYSTEM
    # üçüncü teşvik yüzeyi: bağlam istemindeki rejim reklamı duraklatılanı taşımaz (kaynak-çivi;
    # _hermes_ctx canlı defter okumaları gerektirdiğinden burada çağrılmaz)
    src = (REPO / "meridian" / "hermes.py").read_text(encoding="utf-8")
    assert "if r not in config.URETIMI_DURAKLATILAN_REJIMLER" in src, \
        "note_regime_conditional rejim listesi duraklatma süzgecini kaybetmiş"


def test_d2_duraklatma_sabiti_ve_notlandirma_yolu():
    assert config.URETIMI_DURAKLATILAN_REJIMLER == ("chop",)
    # NOTLANDIRMA/teyit DOKUNULMADI: chop geçerli rejim kalır, resolve_params chop'u hâlâ çözer
    assert "chop" in config.VALID_REGIMES
    eff = config.resolve_params({"a": 1.0}, {"chop": {"a": 2.0}}, "chop")
    assert eff["a"] == 2.0, "resolve_params chop haritasını çözmüyor — notlandırma yolu bozuldu"


def _t(regime, close):
    return {"regime": regime, "ts_close": close, "r_multiple": 0.5}


def test_d3_bg_secici_chop_sertifikasi_VERMEZ_pozitif_kontrollu(sandbox_state, monkeypatch):
    """Kanıt ufku DOLU olsa bile chop'a bg sertifikası çıkmaz; AYNI şekilli kanıt trend_down'a
    çıkar (pozitif kontrol — yoksa 'seçici zaten hiç seçmiyor' ile ayırt edilemezdi)."""
    monkeypatch.setitem(hr._state, "bg_reflect_by_regime", {})
    chop_kaniti = [_t("chop", f"2025-{m:02d}-15") for m in range(1, 11)]
    assert hr._bg_ready_regime(chop_kaniti, every=5, live_reg="trend_up") is None, \
        "chop'a bg sertifikası verildi — K1 duraklatması delindi"
    td_kaniti = [_t("trend_down", f"2025-{m:02d}-15") for m in range(1, 11)]
    assert hr._bg_ready_regime(td_kaniti, every=5, live_reg="trend_up") == "trend_down", \
        "pozitif kontrol düştü — seçici duraklatmasız rejimi de seçemiyor"


def _olay(ad: str) -> list:
    return [e for e in store.read_jsonl("events.jsonl") if e.get("event") == ad]


def test_d4_chop_sertifikali_bg_turu_KOSMAZ_ve_olay_basar(sandbox_state, monkeypatch):
    """İkinci savunma hattı (seçici delinse bile): chop sertifikalı bg turu gövde başında atlanır
    — LLM'e hiç gidilmez, olay YASA-4 gerekçeli basılır."""
    monkeypatch.setattr(hermes, "propose_with_llm",
                        lambda: (_ for _ in ()).throw(AssertionError("LLM çağrıldı — tur atlanmadı")))
    r = hermes.reflect_once(target_regime="chop", background=True)
    assert r["status"] == "bg_regime_paused"
    ev = _olay("bg_reflection_skipped_paused_regime")
    assert ev and ev[-1].get("kart") == "EDG-2026-048"
    assert len(str(ev[-1].get("detail", ""))) >= 20, "olay gerekçesiz (YASA 4 eşiği)"


def test_d5_canli_turda_at_chop_onerisi_URETIMDEN_duser_arama_surer(sandbox_state, monkeypatch):
    """Canlı turda LLM '@chop' üretirse öneri kapıya GİTMEZ (üretimden düşer, olay basılır) ama
    tur ölmez — arama yoluna düşülür ve kapsam duraklatılmış rejime verilmez."""
    from meridian import dataset, reflect
    store.write_json("regime.json", {"regime": "chop"})
    monkeypatch.setattr(hermes, "propose_with_llm",
                        lambda: {"variable": "exit.trail_atr_mult@chop", "new": 2.5, "old": 3.0,
                                 "source": "llm", "rationale": "sentetik @chop üretim denemesi"})
    monkeypatch.setattr(dataset, "load", lambda **k: (None, None))
    gidenler: list = []
    aramalar: list = []
    monkeypatch.setattr(reflect, "submit",
                        lambda *a, **k: (gidenler.append(a[0] if a else k)
                                         or {"status": "rejected_by_backtest"}))
    monkeypatch.setattr(reflect, "search_and_submit",
                        lambda *a, **k: (aramalar.append(k)
                                         or {"status": "no_clearing_candidate", "search": {}}))

    hermes.reflect_once(target_regime="auto")

    assert not gidenler, "@chop önerisi kapıya gitti — üretim duraklatması delindi"
    ev = _olay("hermes_proposal_paused_regime")
    assert ev and ev[-1].get("kart") == "EDG-2026-048"
    assert aramalar, "öneri düşünce aramaya düşülmedi — tur sessizce öldü"
    assert aramalar[-1].get("regime") is None, \
        "canlı arama kapsamı chop'a verildi — her sonda var@chop üretirdi"


def test_d6_canli_arama_kapsami_duraklatmasiz_rejimde_ACIK_pozitif_kontrol(sandbox_state, monkeypatch):
    """(d5)'in pozitif kontrolü: aynı düzenek trend_down canlıyken kapsamı trend_down'a VERİR —
    yoksa 'arama zaten hep global' ile ayırt edilemezdi."""
    from meridian import dataset, reflect
    store.write_json("regime.json", {"regime": "trend_down"})
    monkeypatch.setattr(hermes, "propose_with_llm", lambda: None)
    monkeypatch.setattr(hermes, "propose_virgin_knob", lambda: None)
    monkeypatch.setattr(dataset, "load", lambda **k: (None, None))
    aramalar: list = []
    monkeypatch.setattr(reflect, "search_and_submit",
                        lambda *a, **k: (aramalar.append(k)
                                         or {"status": "no_clearing_candidate", "search": {}}))

    hermes.reflect_once(target_regime="auto")

    assert aramalar and aramalar[-1].get("regime") == "trend_down"


# =================================================================================================
# (e) 25d EZER DAMGALARI — on zincirin onu da yerinde (görünürlük; davranış değişmez)
# =================================================================================================
ZINCIR_DOSYALARI = {
    1: "meridian/guard.py",       # slot ← ısı zarfı
    2: "meridian/broker.py",      # limit_atr ← limit_pct
    3: "meridian/probgate.py",    # arama uzayı ← P_BASE
    4: "meridian/loop.py",        # keşif ← üretici kuraklığı
    5: "meridian/strategy.py",    # skill bayrakları ← ARMED_SETUPS
    6: "state/bounds.yaml",       # R:R tabanı ← bounds alt sınırı
    7: "meridian/probgate.py",    # meta-kalibrasyon ← kanıt kuraklığı
    8: "meridian/analytics.py",   # LLM kalibrasyonu ← görüş kuraklığı
    9: "meridian/health.py",      # Faz-6 kilitleri ← tüketici yokluğu
    10: "meridian/broker.py",     # likidite modeli ← emir boyu küçüklüğü
}


@pytest.mark.parametrize("n,dosya", sorted(ZINCIR_DOSYALARI.items()))
def test_e1_25d_damgasi_yerinde(n, dosya):
    src = (REPO / dosya).read_text(encoding="utf-8")
    assert src.count(f"25d zinciri c-{n}") == 1, f"25d c-{n} damgası {dosya} içinde tam 1 kez olmalı"
    assert "EZER" in src


def test_e2_negatif_kontrol_uydurma_zincir_yok():
    for dosya in set(ZINCIR_DOSYALARI.values()):
        src = (REPO / dosya).read_text(encoding="utf-8")
        assert "25d zinciri c-11" not in src, "envanterde olmayan bir zincir uydurulmuş"


def test_e3_pozitif_kontrol_yaml_parser_sag_anahtarlari_goruyor():
    """(a) testlerinin YOK-hükümleri çalışan bir parser'dan geliyor mu? Sağ kalanlar görünmeli."""
    assert GOAL["min_sample"] == 30
    assert GOAL["limits"]["heat_hard_r"] == 5.0
    assert {"execution_v2", "pessimistic_band_v2"} <= guard.GOAL_KEYS
    assert "heat_hard_r" in guard.LIMIT_KEYS

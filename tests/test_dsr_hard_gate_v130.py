"""test_dsr_hard_gate_v130.py — Y1 DSR/PBO SERT KAPI (2026-07-30, operatör onaylı MOD-FARKINDALIKLI
tasarım · ROADMAP §3.1 Y1 hard-gate kalemi + §7 tur notu).

NE ÇİVİLENİYOR VE NEDEN. Bu tur bir kapıyı SERTLEŞTİRİYOR ve sertleşen kapıların sessizce gevşemesi
bu depodaki en pahalı hata sınıfıdır (2026-07-22: olasılıksal yasa kendi `min_sample` tabanını icat
etti ve 26 işlemle bir sürüm canlıya çıktı). Sertlik, ancak MODUN kendisi de test edilirse gerçektir:
"gerçek-parada sert" cümlesi, yalnız kâğıt modunda koşan bir testle DOĞRULANMIŞ SAYILMAZ.

Yedi çivi, yedi ayrı sessiz kayma yolu:

  ① SAF KURAL MATRİSİ    — mod × ölçülebilirlik × değer'in HER hücresi (`dsr_kapi`/`pbo_kapi`).
                           Saf fonksiyon oldukları için matris tam taranabilir; ship yolu yalnız
                           BAĞLANTIYI kanıtlar, hükmü bu blok kanıtlar.
  ② KÂĞIT SHIP DEĞİŞMEDİ — düşük DSR ile ship GEÇER ve damgayı taşır. Bu turun en kolay ihlal
                           edilecek maddesi: "sertleştirdik" diye kâğıt öğrenme hızını kısmak.
  ③ GERÇEK-PARA SERT     — düşük DSR RET; ölçülemeyen DSR de RET (FAIL-CLOSED).
  ④ PBO İKİ MODDA SERT   — ölçülebilir+kötü PBO iki modda da RET (SÜREÇ testi, aday testi değil);
                           ölçülemeyen PBO kâğıtta veto ETMEZ, gerçek-parada RET.
  ⑤ PBO TABANI TEK PENCERE — yabancı `pencere_id` satırı PBO paydasına GİREMEZ (R1 havuzlama yasağı;
                           ledgers sözleşmesinin tüketici tarafındaki karşılığı).
  ⑥ FAZ-6 BEŞ KİLİT      — zincir 5 kilidi SAYAR, adları tek yerden gelir, ölçülemeyen kilit
                           KAPALIdır, ve DSR eşiği ship yoluyla AYNI sabitten okunur (davranışsal
                           tek-kaynak çivisi: sabiti oynat, İKİ tüketici birlikte değişsin).
  ⑦ DAMGA + SÖZLEŞME     — damgalar ledger sözleşmesinde YAZILI, `required`a GİRMEMİŞ (retro damga
                           yasağı) ve panonun tüketicisi var (YASA 6).

KAPI SEMANTİĞİ ÇİVİSİ DE BURADA: `_gate_eval`in `passes` hükmü DEĞİŞMEDİ — DSR o fonksiyonda hâlâ
`passes` satırının ALTINDA üretilir. Sertlik SHIP yolundadır ve iki yerin karışması, "arama sertleşti"
demek olurdu (ölçüm aracını ölçüm yapmadan kısmak).
"""
from __future__ import annotations

import copy
import json
import pathlib

import pytest

from meridian import (backtest, config, health, ledgers, memory, reflect, validation,
                      versioning)
from tests import wf_fixtures as wf

KNOB = "position_size_r"
SMALL, FULL = 0.1, 1.0

DUSUK_DSR = 0.42          # 0.95 altı — kâğıtta damga, gerçek-parada RET
YUKSEK_DSR = 0.991        # 0.95 üstü — iki modda da geçer
KOTU_PBO = {"durum": "olculdu", "pbo": 0.55, "n_aday": 9, "n_kombinasyon": 70,
            "min_aday": validation.PBO_MIN_ADAY, "neden": None}
IYI_PBO = {"durum": "olculdu", "pbo": 0.05, "n_aday": 9, "n_kombinasyon": 70,
           "min_aday": validation.PBO_MIN_ADAY, "neden": None}
OLCULEMEYEN_PBO = {"durum": "olculemedi", "pbo": None, "n_aday": 2, "n_kombinasyon": None,
                   "min_aday": validation.PBO_MIN_ADAY, "neden": "defterde 2/8 aday"}


# ==============================================================================================
# KUM HAVUZU — v1 canlı, gerçek ship yolu. Hiçbir test CANLI state'e dokunmaz (conftest bekçisi).
# ==============================================================================================
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
    run.bootstrap_v01()
    strat = config.default_strategy()
    strat["params"][KNOB] = SMALL
    config.dump_yaml(strat, config.strategy_path())
    versioning.snapshot(strat)
    yield sandbox_state
    _reset_caches()
    config.reload_config()


def _pass_gate(monkeypatch) -> None:
    """Kapıyı GEÇİREN incumbent/aday walk-forward'ı sabitle (v76 deseni, merkezi fikstür fabrikası).
    Bu blok kapı YASASINI test etmiyor — onu v76/v119 yapıyor; buradaki iş, kapıdan GEÇMİŞ bir adayın
    SHIP noktasında ne olduğunu ölçmek."""
    monkeypatch.setattr(reflect.dataset, "load", lambda **k: (None, None))
    inc = wf.wf_from_scores(0.10, folds=[(30, 0.2)] * 3, holdout=0.10)
    cand = wf.wf_from_scores(0.30, folds=[(30, 0.6)] * 3, holdout=0.30)
    live = int(config.load_strategy().get("version", 1))

    def _wfx(*a, **k):
        return copy.deepcopy(cand if int(k.get("strategy_version", live)) != live else inc)

    monkeypatch.setattr(backtest, "walk_forward", _wfx)
    reflect._INC_CACHE.clear()


def _dsr(monkeypatch, deger) -> None:
    """DSR ÖLÇÜMÜNÜ sabitle. `deger=None` → `deflated_sharpe`ın ÖLÇÜLEMEDİ şekli (None döner, 0.0
    DEĞİL — o ayrım bu turun fail-closed kuralının dayanağı)."""
    def _fake(returns, n_trials, trial_sharpes=None):
        if deger is None:
            return None
        return {"dsr": deger, "psr_sifir": 0.5, "sharpe_gozlem": 0.05, "n": 40,
                "varyans_kaynagi": "test_fikstürü", "n_trials": int(n_trials or 0)}
    monkeypatch.setattr(validation, "deflated_sharpe", _fake)


def _pbo(monkeypatch, olcum: dict) -> None:
    monkeypatch.setattr(validation, "pbo_cscv", lambda rows=None, blocks=None: dict(olcum))


def _mod(monkeypatch, live: bool) -> None:
    monkeypatch.setattr(config, "live_enabled", lambda: live)


def _teklif() -> dict:
    return {"variable": KNOB, "new": FULL, "rationale": "sert kapı turu ölçümü",
            "predicted_direction": "improve_oos_score", "predicted_delta": 0.05,
            "confidence": 0.5, "source": "deterministic"}


# ==============================================================================================
# ① SAF KURAL MATRİSİ — mod × ölçülebilirlik × değer (hükmün TEK kaynağı)
# ==============================================================================================
@pytest.mark.parametrize("deger,live,beklenen_ret,beklenen_dusuk,beklenen_durum", [
    # KÂĞIT: hiçbir hücrede ret YOK — yalnız damga.
    (DUSUK_DSR,  False, False, True,  "olculdu"),
    (YUKSEK_DSR, False, False, False, "olculdu"),
    (None,       False, False, None,  "olculemedi"),
    # GERÇEK-PARA: düşük RET, ölçülemeyen RET (fail-closed), yüksek geçer.
    (DUSUK_DSR,  True,  True,  True,  "olculdu"),
    (YUKSEK_DSR, True,  False, False, "olculdu"),
    (None,       True,  True,  None,  "olculemedi"),
])
def test_1a_dsr_kural_matrisi(deger, live, beklenen_ret, beklenen_dusuk, beklenen_durum):
    h = validation.dsr_kapi(deger, live=live)
    assert h["ret"] is beklenen_ret, f"mod={'live' if live else 'paper'} dsr={deger} → {h}"
    assert h["dsr_dusuk"] is beklenen_dusuk, \
        ("`dsr_dusuk` ÜÇ DEĞERLİDİR: None YALNIZ ölçülemedi hâlinde. False yazmak 'düşük değil' "
         f"demek, yani yapılmamış bir ölçümün sonucunu uydurmaktır — geldi: {h['dsr_dusuk']}")
    assert h["dsr_durum"] == beklenen_durum
    assert (h["dsr_dusuk"] is None) == (h["dsr_durum"] == "olculemedi"), \
        "iki alan birbirinin tutarlı ikizi olmalı: None ⟺ olculemedi"
    assert (h["neden"] is None) == (not beklenen_ret), "her ret bir GEREKÇE taşımalı, her geçiş taşımamalı"


def test_1b_esik_kesin_esitsizlik():
    """Tam eşikte GEÇMEZ. `>=` ile `>` arasındaki fark, sınırda duran bir adayın hükmüdür ve
    'yaklaşık' bir eşik denetlenemez."""
    tam = validation.DSR_HARD_MIN
    assert validation.dsr_kapi(tam, live=True)["ret"] is True, "DSR == eşik GEÇMEMELİ (kural: > 0.95)"
    assert validation.dsr_kapi(tam + 1e-9, live=True)["ret"] is False
    assert validation.pbo_kapi({**KOTU_PBO, "pbo": validation.PBO_HARD_MAX}, live=False)["ret"] is True, \
        "PBO == eşik GEÇMEMELİ (kural: < %20)"
    assert validation.pbo_kapi({**KOTU_PBO, "pbo": validation.PBO_HARD_MAX - 1e-9},
                               live=False)["ret"] is False


@pytest.mark.parametrize("olcum,live,beklenen_ret", [
    (KOTU_PBO,        False, True),    # SÜREÇ testi: kâğıtta DA ret
    (KOTU_PBO,        True,  True),
    (IYI_PBO,         False, False),
    (IYI_PBO,         True,  False),
    (OLCULEMEYEN_PBO, False, False),   # uygulanamayan kontrol veto olamaz
    (OLCULEMEYEN_PBO, True,  True),    # ama gerçek-parada fail-closed
    (None,            False, False),
    (None,            True,  True),
])
def test_1c_pbo_kural_matrisi(olcum, live, beklenen_ret):
    h = validation.pbo_kapi(olcum, live=live)
    assert h["ret"] is beklenen_ret, f"mod={'live' if live else 'paper'} pbo={olcum} → {h}"
    assert "SERT" in h["hukum"], "PBO hükmü iki modda da SERT olarak adlandırılmalı"


def test_1d_saf_fonksiyonlar_diske_dokunmaz(sandbox_state):
    """Hüküm fonksiyonları SAF: dosya okumazlar. Aksi hâlde kural, çağrıldığı andaki disk durumuna
    göre değişirdi ve iki tüketici (ship yolu / Faz-6) aynı girdide farklı hüküm verebilirdi."""
    onceki = sorted(p.name for p in pathlib.Path(sandbox_state).rglob("*"))
    validation.dsr_kapi(DUSUK_DSR, live=True)
    validation.pbo_kapi(KOTU_PBO, live=True)
    assert sorted(p.name for p in pathlib.Path(sandbox_state).rglob("*")) == onceki


# ==============================================================================================
# ② KÂĞIT SHIP DAVRANIŞI DEĞİŞMEDİ — düşük DSR ile GEÇER, damgayı TAŞIR
# ==============================================================================================
def test_2a_paperda_dusuk_dsr_ship_GECER_ve_damga_tasir(seeded, monkeypatch):
    _pass_gate(monkeypatch)
    _mod(monkeypatch, live=False)
    _dsr(monkeypatch, DUSUK_DSR)
    res = reflect.submit(_teklif(), config.goal())

    assert res["status"] == "shipped", \
        ("KÂĞIT MODUNDA DÜŞÜK DSR SHIP'İ BLOKLAMAZ — kâğıt evrimi ölçüm aracıdır ve ana defterin "
         f"öğrenme hızı istatistiksel bir uyarıyla kısılmaz. Geldi: {res.get('status')}")
    g = res["gate"]
    assert g["ship_modu"] == "paper"
    assert g["dsr_dusuk"] is True and g["dsr_durum"] == "olculdu", \
        "bloklamamak SUSMAK değildir: damga ship kaydında DURMALI"
    assert g["dsr_hard_kapi"]["ret"] is False and "ADVISORY" in g["dsr_hard_kapi"]["hukum"]

    # DAMGA DİSKTEKİ HİPOTEZ SATIRINDA DA VAR (pano oradan okuyor, dönüş sözlüğünden değil).
    hyp = memory.all_hypotheses()[-1]
    assert hyp["status"] == "live"
    assert (hyp["backtest"] or {})["dsr_dusuk"] is True, \
        "damga yalnız dönüşte kaldıysa pano ship geçmişinde düşük-DSR satırı GÖRÜNMEZ"


def test_2b_yuksek_dsr_ile_ship_de_ayni_yoldan_gecer(seeded, monkeypatch):
    """Kontrol grubu: damga alanları YÜKSEK DSR'de de yazılır (yalnız `dsr_dusuk` False). Alanların
    yalnız 'kötü' hâlde yazılması, 'damgasız satır iyi mi yoksa eski mi?' sorusunu doğururdu."""
    _pass_gate(monkeypatch)
    _mod(monkeypatch, live=False)
    _dsr(monkeypatch, YUKSEK_DSR)
    res = reflect.submit(_teklif(), config.goal())
    assert res["status"] == "shipped"
    assert res["gate"]["dsr_dusuk"] is False and res["gate"]["dsr_durum"] == "olculdu"


def test_2c_paperda_olculemeyen_dsr_de_ship_GECER(seeded, monkeypatch):
    """Kâğıtta ölçülemeyen DSR de bloklamaz — ama `dsr_durum: olculemedi` damgası zorunlu."""
    _pass_gate(monkeypatch)
    _mod(monkeypatch, live=False)
    _dsr(monkeypatch, None)
    res = reflect.submit(_teklif(), config.goal())
    assert res["status"] == "shipped"
    assert res["gate"]["dsr_durum"] == "olculemedi" and res["gate"]["dsr_dusuk"] is None


# ==============================================================================================
# ③ GERÇEK-PARA BAĞLAMI — SERT ve FAIL-CLOSED
# ==============================================================================================
def test_3a_livede_dusuk_dsr_RET(seeded, monkeypatch):
    _pass_gate(monkeypatch)
    _mod(monkeypatch, live=True)
    _dsr(monkeypatch, DUSUK_DSR)
    v_once = int(config.load_strategy()["version"])
    res = reflect.submit(_teklif(), config.goal())

    assert res["status"] == "rejected_by_dsr", \
        f"gerçek-para bağlamında düşük DSR RET olmalı — geldi: {res.get('status')}"
    assert int(config.load_strategy()["version"]) == v_once, "RET edilen aday SÜRÜM ARTIRMAMALI"
    assert res["gate"]["ship_modu"] == "gercek_para"
    assert "SERT" in res["gate"]["dsr_hard_kapi"]["hukum"]
    hyp = memory.all_hypotheses()[-1]
    assert hyp["status"] == "rejected_by_dsr" and hyp["version_to"] is None
    assert any("DSR" in str(r) for r in (hyp.get("reject_reasons") or [])), \
        "ret gerekçesi defterde ADIYLA durmalı (YASA 4: sessiz ret yok)"


def test_3b_livede_OLCULEMEYEN_dsr_RET_fail_closed(seeded, monkeypatch):
    """FAIL-CLOSED: kanıt YOKSA gerçek para kapısı KAPALI. Ölçülemeyen bir kontrolü 'geçti' saymak,
    yapılmamış bir testin sonucunu uydurmaktır (UYDURMA YASAĞI'nın kapı hâli)."""
    _pass_gate(monkeypatch)
    _mod(monkeypatch, live=True)
    _dsr(monkeypatch, None)
    res = reflect.submit(_teklif(), config.goal())
    assert res["status"] == "rejected_by_dsr"
    assert res["gate"]["dsr_durum"] == "olculemedi"
    assert "ölçülemedi" in (res["gate"]["dsr_hard_kapi"]["neden"] or "").lower()


def test_3c_livede_yuksek_dsr_ve_iyi_pbo_SHIP_EDER(seeded, monkeypatch):
    """Fail-closed 'her şey kapalı' DEĞİLDİR: ölçülü ve eşiği geçen kanıtla kapı AÇILIR. Bu çivi
    olmadan, kapıyı sessizce hep-kapalı yapan bir hata testlerde yeşil kalırdı."""
    _pass_gate(monkeypatch)
    _mod(monkeypatch, live=True)
    _dsr(monkeypatch, YUKSEK_DSR)
    _pbo(monkeypatch, IYI_PBO)
    res = reflect.submit(_teklif(), config.goal())
    assert res["status"] == "shipped", f"ölçülü+geçen kanıtla gerçek-para kapısı açılmalı: {res}"


# ==============================================================================================
# ④ PBO — İKİ MODDA DA SERT (ölçülebilir olduğunda)
# ==============================================================================================
@pytest.mark.parametrize("live", [False, True])
def test_4a_pbo_olculebilir_ve_kotu_iki_modda_RET(seeded, monkeypatch, live):
    _pass_gate(monkeypatch)
    _mod(monkeypatch, live=live)
    _dsr(monkeypatch, YUKSEK_DSR)          # DSR'yi ELİYORUZ: ölçülen şey YALNIZ PBO'nun hükmü
    _pbo(monkeypatch, KOTU_PBO)
    v_once = int(config.load_strategy()["version"])
    res = reflect.submit(_teklif(), config.goal())

    assert res["status"] == "rejected_by_pbo", \
        ("PBO bir ADAY testi değil SÜREÇ testidir: aşırı-uydurulmuş bir SEÇİM SÜRECİNDEN çıkan aday "
         f"KÂĞIDA BİLE inmemeli (mod={'live' if live else 'paper'}) — geldi: {res.get('status')}")
    assert int(config.load_strategy()["version"]) == v_once
    assert res["gate"]["pbo_hard_kapi"]["deger"] == KOTU_PBO["pbo"]
    assert memory.all_hypotheses()[-1]["status"] == "rejected_by_pbo"


def test_4b_pbo_olculemezse_paperda_veto_YOK_livede_RET(seeded, monkeypatch):
    """Uygulanamayan kontrol veto olamaz (kâğıt) · kanıt yoksa gerçek para kapısı kapalı (live).
    AYNI girdinin iki modda iki farklı hükmü — mod-farkındalığın ta kendisi."""
    _pass_gate(monkeypatch)
    _dsr(monkeypatch, YUKSEK_DSR)
    _pbo(monkeypatch, OLCULEMEYEN_PBO)

    _mod(monkeypatch, live=False)
    res_paper = reflect.submit(_teklif(), config.goal())
    assert res_paper["status"] == "shipped", f"kâğıtta ölçülemeyen PBO veto ETMEZ: {res_paper}"
    assert res_paper["gate"]["pbo_hard_kapi"]["ret"] is False

    # Aynı ölçülemez hâl, gerçek-para bağlamında: RET. (Yeni bir aday, aynı fikstür.)
    _pass_gate(monkeypatch)
    _mod(monkeypatch, live=True)
    res_live = reflect.submit({**_teklif(), "new": 0.9}, config.goal())
    assert res_live["status"] == "rejected_by_pbo", \
        f"gerçek-para bağlamında ölçülemeyen PBO RET olmalı: {res_live}"


def test_4c_gercek_pbo_bugunku_defterde_OLCULEMEDI_doner(seeded, monkeypatch):
    """CANLI DAVRANIŞ ÇİVİSİ: PBO fikstürü OLMADAN, gerçek `pbo_cscv` yürürlükteki pencerede taban
    dolmadığı için dürüstçe ÖLÇÜLEMEDİ döner → kâğıt ship'i etkilenmez. Bu turun canlı sistemde
    NO-OP olduğu iddiası burada davranışla kanıtlanır (fikstürle değil)."""
    _pass_gate(monkeypatch)
    _mod(monkeypatch, live=False)
    _dsr(monkeypatch, DUSUK_DSR)
    res = reflect.submit(_teklif(), config.goal())
    assert res["status"] == "shipped"
    p = res["gate"]["pbo_hard_kapi"]
    assert p["durum"] == "olculemedi" and p["ret"] is False, \
        f"taban dolmadan PBO hüküm vermemeli: {p}"
    assert p["n_aday"] < validation.PBO_MIN_ADAY


# ==============================================================================================
# ⑤ PBO TABANI TEK PENCERE-IZGARASINDAN (R1 havuzlama yasağı — tüketici tarafı)
# ==============================================================================================
def test_5_yabanci_pencere_satiri_pbo_paydasina_GIRMEZ(seeded, monkeypatch):
    """`_matris` ızgaraları BİRLEŞTİRİR: kesişmeyen iki dönem tek matriste sıfırlarla dolar ve PBO
    gürültüyü 'aşırı-uydurma yok' diye okur. Ship yolu bu yüzden defteri `pencere_id`ye göre süzer;
    süzme kalkarsa bu test kırılır."""
    from meridian import dataset, store
    gorulen: dict = {}

    def _spy(rows=None, blocks=None):
        gorulen["rows"] = list(rows or [])
        return dict(OLCULEMEYEN_PBO)

    # Defterde iki YABANCI pencere satırı + gerçek kapı yazımı (R1 damgalı) olacak.
    for i in range(3):
        store.append_jsonl(validation.LEDGER_FILE,
                           {"ts": f"2026-01-0{i + 1}", "etiket": f"eski#{i}", "pencere_id": "R0",
                            "sharpe_gozlem": 0.1, "n_trials": 5, "passes": False,
                            "seri": [["2026-01-05", 0.5], ["2026-01-06", -0.2]]})
    store.append_jsonl(validation.LEDGER_FILE,
                       {"ts": "2026-02-01", "etiket": "damgasiz", "sharpe_gozlem": 0.1,
                        "n_trials": 5, "passes": False, "seri": [["2026-02-02", 0.3]]})

    _pass_gate(monkeypatch)
    _mod(monkeypatch, live=False)
    _dsr(monkeypatch, YUKSEK_DSR)
    monkeypatch.setattr(validation, "pbo_cscv", _spy)
    reflect.submit(_teklif(), config.goal())

    ids = {r.get("pencere_id") for r in gorulen["rows"]}
    assert ids <= {dataset.ROTATION_ID}, \
        f"PBO paydasına yabancı pencere satırı girdi: {ids} (havuzlama YASAK — ledgers sözleşmesi)"
    assert any(r.get("pencere_id") == dataset.ROTATION_ID for r in gorulen["rows"]), \
        "yürürlükteki pencerenin kendi satırı paydadan düşmüş — süzme fazla agresif"


# ==============================================================================================
# ⑥ FAZ-6 KİLİT ZİNCİRİ — BEŞ KİLİT
# ==============================================================================================
def _sahte_hukum(passed: int, n: int) -> dict:
    return {"criteria": {f"o{i}": {"status": "gecti" if i < passed else "kaldi"} for i in range(n)},
            "passed": passed, "failed": n - passed, "unmeasured": 0, "zayif": 0,
            "verdict": f"{passed}/{n}"}


def _trio(dsr) -> dict:
    return {"dsr_canli": (None if dsr is None else {"dsr": dsr, "n": 40}),
            "n_trials": 461, "pencere_id": "R1", "pbo": dict(OLCULEMEYEN_PBO)}


def test_6a_zincir_BES_kilidi_sayar_ve_adlari_tek_yerden_gelir(sandbox_state):
    f = health.faz6_kilitleri(edge=_sahte_hukum(5, 5), sonuc=_sahte_hukum(4, 4),
                              trio=_trio(YUKSEK_DSR))
    assert f["n_kilit"] == 5, f"Faz-6 zinciri BEŞ kilit saymalı (dördüncüsü + DSR): {f['n_kilit']}"
    assert len(health.FAZ6_KILITLERI) == 5
    assert set(f["kilitler"]) == set(health.FAZ6_KILITLERI), \
        "kilit adları TEK yerde (FAZ6_KILITLERI) — ikinci bir liste, sessizce ayrışan iki zincir olurdu"
    assert set(health.FAZ6_KILITLERI) == {"edge_kaniti", "sonuc_hukmu", "faz5_cikisi",
                                          "operator_onayi", "dsr_gecer"}
    assert f["n_kilit"] == len(f["kilitler"]), "payda LİSTEDEN türemeli, sabit yazılmamalı"
    for ad, k in f["kilitler"].items():
        assert set(k) >= {"gecer", "durum", "olcum", "esik"}, f"{ad} kilit şekli eksik"
        assert isinstance(k["gecer"], bool), "kilit ÜÇ DEĞERLİ DEĞİL: ölçülemeyen kilit KAPALIdır"


def test_6b_olculemeyen_kilit_KAPALIdir(sandbox_state):
    """FAIL-CLOSED. Faz-5 çıkış ölçümü ÜRETİLMİYOR ve operatör bayrağı kapalı → ikisi de kapalı;
    `hepsi_acik` bu yüzden False. 'Ölçüm yok' ile 'ölçüldü ve geçti' arasındaki farkı silmek, bu
    zincirin engellemek için var olduğu şeydir."""
    f = health.faz6_kilitleri(edge=_sahte_hukum(5, 5), sonuc=_sahte_hukum(4, 4),
                              trio=_trio(YUKSEK_DSR))
    faz5 = f["kilitler"]["faz5_cikisi"]
    assert faz5["gecer"] is False and faz5["durum"] == "olculemedi" and faz5["neden"]
    assert f["kilitler"]["operator_onayi"]["gecer"] is False, "INTRADAY_ARM yok → silahsız"
    assert f["hepsi_acik"] is False and f["n_acik"] == 3
    assert "kapalı" in f["hukum"]

    # Ölçülemeyen DSR de KAPALI (ship yolunun live tarafıyla AYNI kural).
    g = health.faz6_kilitleri(edge=_sahte_hukum(5, 5), sonuc=_sahte_hukum(4, 4), trio=_trio(None))
    assert g["kilitler"]["dsr_gecer"]["gecer"] is False
    assert g["kilitler"]["dsr_gecer"]["durum"] == "olculemedi"


def test_6c_operator_kilidi_ELLE_acilan_bayragi_okur(sandbox_state):
    health.set_intraday_arm(True)
    try:
        f = health.faz6_kilitleri(edge=_sahte_hukum(5, 5), sonuc=_sahte_hukum(4, 4),
                                  trio=_trio(YUKSEK_DSR))
        assert f["kilitler"]["operator_onayi"]["gecer"] is True
        assert f["n_acik"] == 4 and f["hepsi_acik"] is False, \
            "Faz-5 kilidi hâlâ kapalı olmalı — dört kilit BEŞ kilit değildir"
    finally:
        health.set_intraday_arm(False)


def test_6d_edge_ve_sonuc_kilidi_TAM_hukum_ister(sandbox_state):
    """5/5 ve 4/4 dışında hiçbir hâl açık değildir: 'sermaye/silahlanma İKİSİNE bakar' cümlesi
    (ROADMAP §3.1) kısmi bir hükmü kabul etmez."""
    f = health.faz6_kilitleri(edge=_sahte_hukum(4, 5), sonuc=_sahte_hukum(4, 4),
                              trio=_trio(YUKSEK_DSR))
    assert f["kilitler"]["edge_kaniti"]["gecer"] is False
    assert f["kilitler"]["edge_kaniti"]["olcum"] == "4/5"
    g = health.faz6_kilitleri(edge=_sahte_hukum(5, 5), sonuc=_sahte_hukum(3, 4),
                              trio=_trio(YUKSEK_DSR))
    assert g["kilitler"]["sonuc_hukmu"]["gecer"] is False
    assert g["kilitler"]["sonuc_hukmu"]["olcum"] == "3/4"


def test_6e_esik_TEK_KAYNAK_iki_tuketici_birlikte_degisir(seeded, monkeypatch):
    """DAVRANIŞSAL TEK-KAYNAK ÇİVİSİ (metin taraması değil): `DSR_HARD_MIN` oynatılınca HEM ship
    yolu HEM Faz-6 zinciri birlikte değişmeli. Bir tüketici kendi kopyasını taşısaydı burada
    ayrışırdı — 2026-07-22'nin 'olasılıksal yasa kendi tabanını icat etti' hatası birebir bu."""
    monkeypatch.setattr(validation, "DSR_HARD_MIN", 0.30)   # artık DUSUK_DSR (0.42) GEÇER

    f = health.faz6_kilitleri(edge=_sahte_hukum(5, 5), sonuc=_sahte_hukum(4, 4),
                              trio=_trio(DUSUK_DSR))
    assert f["kilitler"]["dsr_gecer"]["gecer"] is True, "Faz-6 kilidi eşiği kendi kopyasından okuyor"
    assert "0.3" in f["kilitler"]["dsr_gecer"]["esik"], "eşik metni de sabitten TÜREMELİ"

    _pass_gate(monkeypatch)
    _mod(monkeypatch, live=True)
    _dsr(monkeypatch, DUSUK_DSR)
    _pbo(monkeypatch, IYI_PBO)      # PBO'yu ELİYORUZ: ölçülen şey YALNIZ DSR eşiğinin kaynağı
    res = reflect.submit(_teklif(), config.goal())
    assert res["status"] == "shipped", \
        f"ship yolu eşiği kendi kopyasından okuyor (0.42 > 0.30 olmalıydı): {res.get('status')}"


def test_6f_zincir_HICBIR_SEY_silahlamaz_ve_diske_yazmaz(sandbox_state):
    """Saf okuma. Bir ön-koşul denetçisinin yan etkisi olması, denetlediği kapıyı kendisinin açması
    riskini doğurur."""
    onceki = {str(p): p.stat().st_mtime_ns for p in pathlib.Path(sandbox_state).rglob("*")
              if p.is_file()}
    health.faz6_kilitleri(edge=_sahte_hukum(5, 5), sonuc=_sahte_hukum(4, 4), trio=_trio(YUKSEK_DSR))
    assert health.intraday_armed() is False, "zincir bayrağa DOKUNMAMALI"
    sonraki = {str(p): p.stat().st_mtime_ns for p in pathlib.Path(sandbox_state).rglob("*")
               if p.is_file()}
    assert sonraki == onceki, f"zincir diske yazdı: {set(sonraki) ^ set(onceki) or 'mtime değişti'}"


# ==============================================================================================
# ⑦ DAMGA + SÖZLEŞME + TÜKETİCİ (YASA 6)
# ==============================================================================================
def test_7a_damgalar_ledger_sozlesmesinde_YAZILI():
    c = ledgers.CONTRACTS["hypotheses.jsonl"]
    for alan in ("ship_modu", "dsr_dusuk", "dsr_durum", "dsr_hard_kapi", "pbo_hard_kapi"):
        assert alan in c.note, f"`{alan}` damgası sözleşmede beyan edilmemiş — sözleşmesiz alan, " \
                               f"2026-07-21'in yedi hatasının kök deseni"
    for st in ("rejected_by_dsr", "rejected_by_pbo"):
        assert st in c.note, f"`{st}` statüsü sözleşmede yazılı olmalı"


def test_7b_damgalar_required_DEGIL_retro_damga_yasagi():
    """Damgaları zorunlu yapmak, v130 öncesi TÜM hipotez satırlarını sözleşme ihlali ilan etmek
    olurdu — ve geriye dönük doldurmak retro damga yasağını ihlal ederdi."""
    c = ledgers.CONTRACTS["hypotheses.jsonl"]
    for alan in ("ship_modu", "dsr_dusuk", "dsr_durum"):
        assert alan not in c.required
    eski = {"id": "H00001", "ts": "2026-01-01", "variable": KNOB, "status": "live"}
    assert ledgers.validate_row("hypotheses.jsonl", eski) == [], \
        "damgasız (v130 öncesi) satır İHLAL sayılmamalı"
    assert "api" in c.consumers, "pano ship geçmişi api.py üzerinden okuyor — tüketici sayılmalı"


def test_7c_panonun_tuketicisi_var(sandbox_state):
    """YASA 6: üretilen her alanın DIŞ tüketicisi olmalı. Zincir: reflect yazar → memory diske →
    api servis eder → app.js çizer."""
    kok = pathlib.Path(__file__).resolve().parent.parent / "meridian"
    api_src = (kok / "api.py").read_text()
    js_src = (kok / "web" / "app.js").read_text()
    assert '"faz6_kilitleri"' in api_src, "Faz-6 zinciri hiçbir uçtan servis edilmiyor"
    assert "faz6_kilitleri" in js_src, "pano Faz-6 kilit satırını çizmiyor"
    for alan in ("dsr_dusuk", "dsr_durum"):
        assert alan in api_src and alan in js_src, \
            f"`{alan}` damgası panoya kadar taşınmıyor — damga görünmezse uyarı değildir"


def test_7d_kapi_passes_semantigi_DEGISMEDI(seeded, monkeypatch):
    """`_gate_eval` hükmü bu turda DEĞİŞMEDİ: DSR orada hâlâ ADVISORY ve `passes` satırının ALTINDA
    üretilir. Sertlik SHIP yolundadır; ikisinin karışması 'arama sertleşti' demek olurdu (ölçüm
    aracını ölçüm yapmadan kısmak)."""
    import inspect
    src = inspect.getsource(reflect._gate_eval)
    assert src.index("passes = bool(magnitude_ok") < src.index("validation.deflated_sharpe"), \
        "DSR `passes` hesabından ÖNCE üretiliyor — advisory olduğu kod düzeninde görünmüyor"
    assert "dsr_kapi" not in src and "pbo_kapi" not in src, \
        "sert kapı `_gate_eval`e sızdı — arama döngüsü de sertleşirdi"

    _pass_gate(monkeypatch)
    _mod(monkeypatch, live=True)          # en sert bağlam
    _dsr(monkeypatch, DUSUK_DSR)
    from meridian import dataset
    bars, index = None, None
    inc = wf.wf_from_scores(0.10, folds=[(30, 0.2)] * 3, holdout=0.10)
    cand = wf.wf_from_scores(0.30, folds=[(30, 0.6)] * 3, holdout=0.30)
    passes, gate, why = reflect._gate_eval(inc, cand, k_probes=1, record_erosion=False)
    assert passes is True, "düşük DSR + gerçek-para bağlamı KAPI hükmünü değiştirmemeli"
    assert "ADVISORY" in gate["dsr_rol"] and "passes" in gate["dsr_rol"]
    assert "dsr_hard_kapi" not in gate, "sert kapı damgası SHIP yolunda basılır, kapı ölçümünde değil"
    assert dataset.ROTATION_ID == gate["pencere_id"]


def test_7e_ret_statuleri_backtest_kovasina_KARISMAZ():
    """`_ledger_stats` bir PBO/DSR reddini DENEME saymaz: süreç hükmü, o DEĞİŞKEN hakkında kanıt
    değildir (guard reddiyle aynı yapısal sebep). Bandite ödül/ceza yazmak, süreç hükmünü değişken
    hükmü sanmak olurdu."""
    hyps = [{"variable": KNOB, "status": "rejected_by_dsr"},
            {"variable": KNOB, "status": "rejected_by_pbo"}]
    assert reflect._ledger_stats(hyps) == {}, \
        "doğrulama kapısı reddi bandit denemesi sayılıyor — kapı istatistiği kirlenir"
    assert reflect._ledger_stats([{"variable": KNOB, "status": "rejected_by_backtest"}]) != {}, \
        "kontrol: backtest reddi DENEME sayılmaya devam etmeli"

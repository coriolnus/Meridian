"""test_kovab_dalga3_v166.py — KOVA-B DALGA-3 (denetim 2026-08-02: C24 / C12 / C13b).

ÜÇ BULGU, TEK SINIF: bir RİSK KURALI, onu değiştirebilecek YÜZEYDEN kopuktu.

  C24 — `HEAT_HARD_R = 5.0` (ve HEAT_REVIEW_R / CORR_REVIEW) modül sabitiydi: canlı defterde plan
        kesiyordu ama ne operatörün değişmez zarfında (goal.yaml `limits`) ne arama uzayında
        (bounds.yaml) görünüyordu. Yönetişim kusuru: kod, operatörün ilan ettiği 5×1,0R zarfın
        ALTINDA bağlayan bir tavanı operatör adına seçiyordu. Üçü de `limits`e TAŞINDI, DEĞERLER
        KORUNDU; guard anahtar yoksa aynı varsayılana düşer (fail-safe).
  C12 — Y3 portföy tavanları (`portfolio.sector_cap` / `heat_cap`) bounds.yaml'da ARANABİLİR ama
        hiçbir üretim çağıranı kapının okuduğu alanları göndermiyordu: en sıkı tavanla bile hüküm
        BİREBİR aynı kalıyordu. Sonuç ölü knob değil, DAHA KÖTÜSÜ — aday replay incumbent'la
        bit-bit özdeş çıkar, kapı reddeder ve meşru bir risk kontrolü deftere KALICI "already tried
        and failed" olarak yazılır. Üretici tarafı kablolandı (canlı/replay/cf).
  C13b— Terfi kapısı, canlı motorun OKUYAMADIĞI knob sınıfını `regime.*@regime` için ADIYLA
        reddediyordu ama SINIF korumasızdı (C13: `exit.early_kill_pivot` düz öneriyle geçiyordu).
        Kablo bağlandığı için bugün reddedilecek knob YOK — dal SENTETİK örnekle sınanır.

YÖNTEM: iddiaların çoğu DAVRANIŞSALDIR (motorlar gerçekten koşturulur, kapı çağrıları casusla
yakalanır). Kaynak metni okuyan tek çivi KAPSAM BEYANIDIR (gölge kolu) ve o da tersinden çalışır:
kablo bağlandığı gün beyan bayatlar ve test KIRMIZI yanar. Her sözleşme çivisinin yanında bir
NEGATİF KONTROL vardır — sözleşme bilerek delinir ve çivinin GERÇEKTEN düştüğü gösterilir.
"""
from __future__ import annotations

import copy
import shutil
from pathlib import Path

import pandas as pd
import pytest
import yaml

from meridian import backtest, cf_backfill, config, guard, loop, shadow_lifecycle as sl, store
from meridian.broker import PaperBroker
from tests.conftest import make_bars

# =================================================================================================
# ORTAK FİKSTÜRLER — test_kovab_ikimotor_v164'ün evren tarifi (iki motoru da GERÇEKTEN silahlandıran
# tek tarif budur; ham make_bars barları veri kapısında 'ohlc_inconsistent' ile düşer).
# =================================================================================================
N_BARS = 300
INDEX_SEED, INDEX_TREND = 7, 0.0006
TICKERS = {"AAPL": 9, "JPM": 10, "UNH": 27, "CAT": 34, "XOM": 63, "KO": 5, "NKE": 6,
           "GS": 3, "MRK": 4}
WINDOW = 12


def _valid_ohlc(df):
    df = df.copy()
    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)
    return df


def _universe(breakout_at=N_BARS - 6):
    idx = _valid_ohlc(make_bars(N_BARS, seed=INDEX_SEED, trend=INDEX_TREND))
    bars = {t: _valid_ohlc(make_bars(N_BARS, seed=s, breakout_at=breakout_at))
            for t, s in TICKERS.items()}
    return bars, idx


@pytest.fixture
def seeded(sandbox_state, monkeypatch):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    (sandbox_state / "strategy.yaml").write_text(yaml.safe_dump(config.default_strategy()))
    from meridian.adapters import constituents
    monkeypatch.setattr(constituents, "health", lambda: {"ok": True}, raising=False)
    yield sandbox_state
    config.reload_config()


class _KapiCasusu:
    """`guard.classify_gate` çağrılarının ARGÜMANLARINI yakalar — hükmü DEĞİŞTİRMEZ.

    ÇAĞIRAN MODÜL kaydedilir: casus modül-filtresiz olsaydı "birinde alan var" diyerek üç motorun
    ikisi kablosuzken de yeşil yanardı (ikinci-motor turunun kör-çivi dersi, v164)."""

    def __init__(self, monkeypatch):
        self.calls: list[dict] = []
        _asil = guard.classify_gate

        def _sarmal(plan, portfolio, regime, goal_, params=None, detail_out=None):
            import sys as _sys
            self.calls.append({"plan": dict(plan), "portfolio": dict(portfolio),
                               "_cagiran": _sys._getframe(1).f_globals.get("__name__")})
            return _asil(plan, portfolio, regime, goal_, params, detail_out)

        # Üç üretici de `guard` modülünün TA KENDİSİNİ import ediyor (`from . import guard`), yani
        # tek yama üçünü birden yakalar; ayrı ayrı yamamak aynı nesneyi dört kez sarmalardı.
        assert loop.guard is guard is backtest.guard is cf_backfill.guard
        monkeypatch.setattr(guard, "classify_gate", _sarmal)

    def of(self, modul: str) -> list[dict]:
        return [c for c in self.calls if c.get("_cagiran") == modul]


def _sozlesme_ihlali(cagrilar: list[dict]) -> list[str]:
    """Bir üreticinin kapı çağrılarında EKSİK sözleşme alanları. Boş liste = kablo tam."""
    eksik = set()
    for c in cagrilar:
        eksik |= {f"portfolio.{k}" for k in guard.Y3_PORTFOLIO_FIELDS if k not in c["portfolio"]}
        eksik |= {f"plan.{k}" for k in guard.Y3_PLAN_FIELDS if k not in c["plan"]}
    return sorted(eksik)


def _sizer():
    return PaperBroker(100_000.0, 0.0, 0.0).size_position


def _plan(**kw) -> dict:
    p = {"id": "P-2026-08-02-AAA", "ticker": "AAA", "sector": "tech", "size_r": 1.0,
         "entry_trigger": 100.0, "stop": 90.0, "r_multiple_expected": 3.0, "score": 90}
    p.update(kw)
    return p


def _pf(**kw) -> dict:
    p = {"open_positions": 0, "sector_counts": {}, "day_pnl_pct": 0.0, "open_risk_r": 0.0,
         "max_corr": 0.0}
    p.update(kw)
    return p


def _rejim() -> dict:
    return {"exposure_budget_pct": 60, "regime": "trend", "leading_sectors": []}


# =================================================================================================
# C24 — ÜÇ EŞİK OPERATÖRÜN ZARFINDA (goal.yaml limits), KODDA YALNIZ FAIL-SAFE VARSAYILAN
# =================================================================================================
def test_c24_isi_tavani_GOAL_LIMITSTEN_okunur(seeded):
    """DAVRANIŞ: operatör `limits.heat_hard_r`i değiştirince kapı DEĞİŞİR. Eskiden bu imkânsızdı —
    sabit hiçbir kanaldan geçersiz kılınamıyordu (guard'ın içe aktarımları da kilitli)."""
    goal = config.goal()
    pf = _pf(open_risk_r=3.0)                       # 3,0R açık + 1,0R aday = 4,0R
    assert guard.classify_gate(_plan(), pf, _rejim(), goal)[0] != "NO_GO", \
        "4,0R bugünkü 5,0R tavanının ALTINDA — başlangıç durumu yanlış kurulmuş"
    sikilastirilmis = copy.deepcopy(goal)
    sikilastirilmis["limits"]["heat_hard_r"] = 3.5
    verdict, reasons = guard.classify_gate(_plan(), pf, _rejim(), sikilastirilmis)
    assert verdict == "NO_GO", "operatörün yazdığı sert tavan kapıya ULAŞMIYOR"
    assert any("3.5R" in r for r in reasons), f"gerekçe operatörün sayısını taşımıyor: {reasons}"


def test_c24_gevsetmek_de_calisir_tek_yon_degil(seeded):
    """Simetri: eşik yalnız sıkılaşmıyor, operatör GEVŞETEBİLİYOR da. Tek yönlü bir kablo,
    "operatör kalemi" iddiasının yarısını taşırdı."""
    goal = copy.deepcopy(config.goal())
    pf = _pf(open_risk_r=5.0)
    assert guard.classify_gate(_plan(), pf, _rejim(), goal)[0] == "NO_GO"
    goal["limits"]["heat_hard_r"] = 8.0
    assert guard.classify_gate(_plan(), pf, _rejim(), goal)[0] != "NO_GO", \
        "gevşetme yönü bağlı değil — eşik hâlâ koddan geliyor"


def test_c24_anahtar_YOKKEN_modul_varsayilanina_duser(seeded):
    """FAIL-SAFE: eski bir goal.yaml (ya da elle kurulmuş bir goal sözlüğü) davranışı DEĞİŞTİRMEZ.
    Bu, taşımanın "bit-bit aynı" iddiasının test edilebilir hâlidir."""
    goal = copy.deepcopy(config.goal())
    for k in ("heat_hard_r", "heat_review_r", "corr_review"):
        goal["limits"].pop(k)
    # 3,4 + 1,0 = 4,4R ≤ 5,0 → sert tavan DEĞİL; REVIEW (3,5R yumuşak bandı) beklenir.
    # (OPERATÖR KARARI 2026-08-03: varsayılan 4,5→5,0 — d01ccb5/7e99eff; sınır senaryosu güncellendi.)
    v, r = guard.classify_gate(_plan(), _pf(open_risk_r=3.4), _rejim(), goal)
    assert v == "REVIEW" and any("ısı" in x for x in r), (v, r)
    assert guard.classify_gate(_plan(), _pf(open_risk_r=4.1), _rejim(), goal)[0] == "NO_GO", \
        "5,1R varsayılan 5,0R tavanını aşmalı — fail-safe varsayılan yanlış"
    assert (guard.HEAT_HARD_R, guard.HEAT_REVIEW_R, guard.CORR_REVIEW) == (5.0, 3.5, 0.85)


def test_c24_SIFIR_esik_or_ile_yutulmaz(seeded):
    """0,0 MEŞRU bir eşiktir (her planı keser) ve `float(x or default)` onu sessizce modül
    varsayılanına (bugün 5,0 — d01ccb5) çevirirdi: operatörün yazdığı sayı operatörün sayısıdır.
    `.get(ad, varsayilan)` şart."""
    goal = copy.deepcopy(config.goal())
    goal["limits"]["heat_hard_r"] = 0.0
    v, r = guard.classify_gate(_plan(size_r=0.25), _pf(open_risk_r=0.0), _rejim(), goal)
    assert v == "NO_GO" and any("0.0R" in x for x in r), (v, r)


def test_c24_degerler_TASINIRKEN_korundu(seeded):
    """OPERATÖR KARARI 2026-08-03 (d01ccb5): heat_hard_r 4,5→5,0R — çivi
    sessiz-değişimi önlemek içindi; açık karar geldi, beklenen değer güncellendi.
    Bu tur bir YÖNETİŞİM turudur, eşik turu değil: goal.yaml'daki üç sayı, koddaki fail-safe
    varsayılanlarla AYNI olmalı. Eşik değişikliği ölçüm kartı ister (research/cards)."""
    lim = config.goal()["limits"]
    assert float(lim["heat_hard_r"]) == guard.HEAT_HARD_R
    assert float(lim["heat_review_r"]) == guard.HEAT_REVIEW_R
    assert float(lim["corr_review"]) == guard.CORR_REVIEW


def test_c24_TUTARLILIK_CIVISI_sert_tavan_zarfi_ASAMAZ(seeded):
    """`heat_hard_r <= max_open_positions × max_position_r`. YÖN ÖNEMLİ: çivi "eşit olsun" demez,
    "AŞMASIN" der. Altında kalmak meşrudur; bugün ise TAM EŞİTTİR (5,0R = 5×1,0R — OPERATÖR
    KARARI 2026-08-03, d01ccb5: eşitleme risk artıran ve operatöre ait bir karardı, kod artık onu
    kendiliğinden vermiyor). Aşmak ilan edilen zarfı sessizce büyütmek olurdu — tavan artık
    hiçbir şeyi kesmezdi; çivinin yönü bu yüzden `<=`dir, `==` değil."""
    lim = config.goal()["limits"]
    zarf = float(lim["max_open_positions"]) * float(lim["max_position_r"])
    assert float(lim["heat_hard_r"]) <= zarf, \
        f"sert ısı tavanı {lim['heat_hard_r']}R ilan edilen zarfı ({zarf}R) AŞIYOR"
    assert float(lim["heat_review_r"]) <= float(lim["heat_hard_r"]), \
        "REVIEW bandı sert tavanın ÜSTÜNDE — yumuşak bayrak hiç görünmezdi"
    assert 0.0 < float(lim["corr_review"]) <= 1.0, "korelasyon eşiği [0,1] dışında"


def test_c24_uc_esik_de_HERMESE_KAPALI(seeded):
    """Operatör kalemi = arama uzayının DIŞI. Üçü de LIMIT_KEYS'te olmalı ve validate_change
    hepsini (düz, @rejim ve `limits.` önekli hâlleriyle) reddetmeli."""
    b, g, p = config.bounds(), config.goal(), config.load_strategy()["params"]
    for key in ("heat_hard_r", "heat_review_r", "corr_review"):
        assert key in guard.LIMIT_KEYS, f"{key} LIMIT_KEYS'te yok — GU1 sürüklenme testi kırılır"
        assert key not in b, f"{key} bounds.yaml'a da girmiş — iki sahip, sessiz ayrışma"
        for prop in ({"variable": key, "new": 9}, {"variable": f"{key}@chop", "new": 9},
                     {"variable": f"limits.{key}", "new": 9}, {"changes": {key: 9}}):
            assert not guard.validate_change(prop, p, b, g, [], 0).ok, f"{prop} guard'ı geçti"


def test_c24_goal_limits_ANAHTARLARI_LIMIT_KEYSi_asmiyor(seeded):
    """GU1 sürüklenme çivisinin bu turdaki hâli: goal.yaml'a eklenen HER limit adı LIMIT_KEYS'te
    olmalı, yoksa yeni bir risk eşiği Hermes'e açık kalır."""
    assert not (set(config.goal()["limits"]) - guard.LIMIT_KEYS)


# =================================================================================================
# C12 — Y3 ÜRETİCİ↔TÜKETİCİ SÖZLEŞMESİ (ÜÇ ÜRETİCİ KABLOLU, GÖLGE BEYANLI)
# =================================================================================================
def test_c12_CANLI_dongu_kapiya_sozlesme_alanlarini_veriyor(seeded, monkeypatch):
    """DAVRANIŞ: canlı P3 kapıya `equity`/`sector_notional`/`heat_pct` + plan `notional`/
    `risk_dollars` geçiriyor. Eskiden beşi de YOKTU."""
    casus = _KapiCasusu(monkeypatch)
    bars, idx = _universe()
    for d in [str(x.date()) for x in idx["date"].iloc[-WINDOW:]]:
        loop.daily_cycle(bars, idx, on_date=d)
    cagrilar = casus.of("meridian.loop")
    assert cagrilar, "canlı döngü hiç kapı çağırmadı — test bir şey kanıtlamıyor"
    assert _sozlesme_ihlali(cagrilar) == [], _sozlesme_ihlali(cagrilar)
    assert all(c["portfolio"]["equity"] > 0 for c in cagrilar), "NAV ölçülmemiş (0/None) geçiyor"


def test_c12_REPLAY_kapiya_sozlesme_alanlarini_veriyor(seeded, monkeypatch):
    casus = _KapiCasusu(monkeypatch)
    bars, idx = _universe()
    dates = [str(x.date()) for x in idx["date"]]
    backtest.replay(config.default_strategy()["params"], bars, idx, config.goal(),
                    dates[0], dates[-1], strategy_version=1)
    cagrilar = casus.of("meridian.backtest")
    assert cagrilar, "replay hiç kapı çağırmadı — test bir şey kanıtlamıyor"
    assert _sozlesme_ihlali(cagrilar) == [], _sozlesme_ihlali(cagrilar)


def test_c12_CF_BACKFILL_kapiya_sozlesme_alanlarini_veriyor(seeded, monkeypatch):
    """cf düz (0 pozisyon) kitapla koşar — BEYANLI tasarım. Alanlar yine de gitmeli: yoksa açık bir
    knob her adaya "NAV ölçülemedi" bayrağı takar ve cf'in hükümlerini kirletir."""
    casus = _KapiCasusu(monkeypatch)
    bars, idx = _universe()
    per = {t: df.set_index("date").sort_index() for t, df in bars.items()}
    ix = idx.set_index("date").sort_index()
    for d in ix.index[-WINDOW:]:
        cf_backfill._plans_for_session(d, str(d.date()), per, ix,
                                       config.default_strategy()["params"], None, config.goal(), 1)
    cagrilar = casus.of("meridian.cf_backfill")
    assert cagrilar, "cf hiç kapı çağırmadı — test bir şey kanıtlamıyor"
    assert _sozlesme_ihlali(cagrilar) == [], _sozlesme_ihlali(cagrilar)
    assert all(c["portfolio"]["heat_pct"] == 0.0 for c in cagrilar), \
        "düz kitapta ısı 0,0 ÖLÇÜLMÜŞ gerçektir — None 'bilmiyoruz' derdi"


def test_c12_NEGATIF_KONTROL_sozlesme_civisi_ESKI_HALDE_KIRILIR():
    """Çivinin GERÇEKTEN ayrım yaptığı gösterilir: denetim öncesi sözlük (beş alan da yok) ihlal
    listesi ÜRETMELİ. Üretmeseydi yukarıdaki üç test dekordan ibaret olurdu."""
    eski = [{"plan": _plan(), "portfolio": _pf(), "_cagiran": "x"}]
    assert _sozlesme_ihlali(eski) == ["plan.notional", "plan.risk_dollars",
                                      "portfolio.equity", "portfolio.heat_pct",
                                      "portfolio.sector_notional"]


def test_c12_y3_SEKTOR_tavani_dolu_sozlukle_ATESLER(seeded):
    """Kapının kendisi: alanlar geldiğinde tavan GERÇEKTEN NO_GO üretir. Denetimin ampirik bulgusu
    tam tersiydi — en sıkı tavanla (0,1) bile hüküm değişmiyordu."""
    goal = config.goal()
    pf = _pf(**guard.y3_portfolio_inputs(
        [{"sector": "tech", "qty": 300, "entry": 100.0, "stop": 90.0, "trail_stop": 90.0,
          "mark": 100.0}], equity=100_000.0, size_fn=_sizer()))
    gate_plan = {**_plan(), **guard.y3_plan_inputs(_plan(), equity=100_000.0, size_fn=_sizer())}
    assert guard.classify_gate(gate_plan, pf, _rejim(), goal, {})[0] != "NO_GO", "knob KAPALI iken kesmemeli"
    v, r = guard.classify_gate(gate_plan, pf, _rejim(), goal, {"portfolio.sector_cap": 25.0})
    assert v == "NO_GO" and any("sektör tavanı" in x for x in r), (v, r)


def test_c12_y3_ISI_tavani_dolu_sozlukle_ATESLER(seeded):
    goal = config.goal()
    pf = _pf(**guard.y3_portfolio_inputs(
        [{"sector": "tech", "qty": 500, "entry": 100.0, "stop": 90.0, "trail_stop": 90.0,
          "mark": 100.0}], equity=100_000.0, size_fn=_sizer()))
    assert pf["heat_pct"] == pytest.approx(5.0)
    gate_plan = {**_plan(), **guard.y3_plan_inputs(_plan(), equity=100_000.0, size_fn=_sizer())}
    v, r = guard.classify_gate(gate_plan, pf, _rejim(), goal, {"portfolio.heat_cap": 5.5})
    assert v == "NO_GO" and any("ısı tavanı" in x for x in r), (v, r)
    assert guard.classify_gate(gate_plan, pf, _rejim(), goal, {"portfolio.heat_cap": 8.0})[0] != "NO_GO"


def test_c12_KNOBLAR_KAPALIYKEN_hukum_BIREBIR_AYNI(seeded):
    """DAVRANIŞ DEĞİŞMEZLİĞİ: yeni alanlar sözlükte olsa da knob 0/yokken hüküm ve gerekçeler
    alanlar hiç yokmuş gibi kalır. Bu turun canlıya dokunmadığı iddiasının çivisi."""
    goal = config.goal()
    zengin_pf = _pf(open_risk_r=2.0, **guard.y3_portfolio_inputs(
        [{"sector": "tech", "qty": 900, "entry": 100.0, "stop": 90.0, "trail_stop": 90.0,
          "mark": 100.0}], equity=100_000.0, size_fn=_sizer()))
    ciplak_pf = _pf(open_risk_r=2.0)
    zengin_plan = {**_plan(), **guard.y3_plan_inputs(_plan(), equity=100_000.0, size_fn=_sizer())}
    for params in ({}, {"entry.min_score": 60},
                   {"portfolio.sector_cap": 0.0, "portfolio.heat_cap": 0.0}):
        assert guard.classify_gate(zengin_plan, zengin_pf, _rejim(), goal, params) == \
               guard.classify_gate(_plan(), ciplak_pf, _rejim(), goal, params), params


def test_c12_isi_TRAIL_ile_olculur_ilk_stopla_degil():
    """Isı yasası ölçüm katmanınınkiyle aynıdır: Σ max(0, giriş − max(stop, trail)) × adet.
    İlk stopla ölçmek, kâra geçmiş bir kitabı olduğundan SICAK gösterip tavanı erken bağlardı."""
    ham = {"sector": "tech", "qty": 100, "entry": 100.0, "stop": 90.0, "mark": 120.0}
    gevsek = guard.y3_portfolio_inputs([ham], equity=100_000.0, size_fn=_sizer())
    sikilasmis = guard.y3_portfolio_inputs([{**ham, "trail_stop": 95.0}], equity=100_000.0,
                                           size_fn=_sizer())
    assert gevsek["heat_pct"] == pytest.approx(1.0) and sikilasmis["heat_pct"] == pytest.approx(0.5)
    # trail asla GEVŞEMEZ (broker yasası) — savunmacı max: bozuk/geri gitmiş trail ısıyı şişirmez
    assert guard.y3_portfolio_inputs([{**ham, "trail_stop": 80.0}], equity=100_000.0,
                                     size_fn=_sizer())["heat_pct"] == pytest.approx(1.0)
    # stop'un ÜSTÜNE çıkmış bir pozisyon (kilitli kâr) ısıya NEGATİF katkı yapmaz
    assert guard.y3_portfolio_inputs([{**ham, "trail_stop": 110.0}], equity=100_000.0,
                                     size_fn=_sizer())["heat_pct"] == pytest.approx(0.0)


def test_c12_SILAHLANAN_planlar_NAV_bacaginda_SAYILIR():
    """R bacağı (`open_risk_r`) silahlı planları zaten sayıyor. NAV bacağı saymasaydı aynı akşam
    silahlanan iki plan birbirini hiç görmez ve iki tavan aynı kitabı farklı büyüklükte görürdü."""
    bos = guard.y3_portfolio_inputs([], equity=100_000.0, size_fn=_sizer())
    assert bos == {"equity": 100_000.0, "sector_notional": {}, "heat_pct": 0.0}
    silahli = guard.y3_portfolio_inputs([], [_plan(), _plan(sector="fin")],
                                        equity=100_000.0, size_fn=_sizer())
    assert silahli["heat_pct"] == pytest.approx(2.0), silahli      # 2 × 1,0R × %1 NAV
    assert set(silahli["sector_notional"]) == {"tech", "fin"}


def test_c12_NAV_olculemezse_isi_None_dondurur_ve_SATIR_SEBEBINI_TASIR(seeded):
    """ÖLÇÜLEMEDİ ≠ HÜKÜM (Rol-1 hükmü, 2026-08-02). `heat_pct` 0,0 değil None döner ("ısı yok"
    ile "ölçemedik" ayrı şeylerdir); guard tavanı UYGULAMAZ (fail-open BİLİNÇLİ — Y3 alanlarını
    hâlâ göndermeyen üreticiler var) ama karar satırı EKSİK ALANI adıyla taşır, yoksa denetimde
    "tavan tuttu"dan ayırt edilemez ve operatör panoda `enabled: true` görürken korumasız kalır."""
    olculemez = guard.y3_portfolio_inputs([], equity=0.0, size_fn=_sizer())
    assert olculemez["heat_pct"] is None
    detay: list = []
    v, r = guard.classify_gate(_plan(), _pf(**olculemez), _rejim(), config.goal(),
                               {"portfolio.heat_cap": 6.0}, detail_out=detay)
    satir = [c for c in detay if c["check"] == "y3_heat_cap"]
    assert satir and satir[0]["value"] is None and satir[0]["severity"] == "soft", detay
    assert satir[0]["passed"] is True, "fail-open hükmü değişmiş — üreticileri kablosuz kalanlar var"
    assert "ölçülemedi" in (satir[0]["note"] or "") and "fail-open" in satir[0]["note"], satir
    assert not any("ısı tavanı" in x for x in r), "ölçülemeyen ısı bir vetoya dönüştü"
    # NEGATİF KONTROL: ölçülebilen tur beyanı TAŞIMAZ (yoksa her satır 'ölçülemedi' derdi)
    detay2: list = []
    guard.classify_gate(_plan(), _pf(**guard.y3_portfolio_inputs([], equity=100_000.0,
                                                                 size_fn=_sizer())),
                        _rejim(), config.goal(), {"portfolio.heat_cap": 6.0}, detail_out=detay2)
    olculen = [c for c in detay2 if c["check"] == "y3_heat_cap"][0]
    assert olculen["note"] is None and olculen["severity"] == "hard", olculen


def test_c12_PLAN_SEMASI_degismedi_dolar_alanlari_deftere_INMEZ(seeded, monkeypatch):
    """`notional`/`risk_dollars` bir DEFTER alanı değil kapının girdisidir (`armed_pivots`/`atr`
    yan haritalarıyla aynı gerekçe). E2 satırına inselerdi `test_differential_v60`ın iki-üretici
    şema eşitliği ve E2 sözleşmesi bu turda sessizce değişmiş olurdu."""
    bars, idx = _universe()
    for d in [str(x.date()) for x in idx["date"].iloc[-WINDOW:]]:
        loop.daily_cycle(bars, idx, on_date=d)
    satirlar = store.read_jsonl("trade_plans.jsonl")
    assert satirlar, "canlı döngü hiç plan yazmadı — test bir şey kanıtlamıyor"
    kacak = {k for s in satirlar for k in guard.Y3_PLAN_FIELDS if k in s}
    assert not kacak, f"dolar alanları E2 defterine sızmış: {kacak}"
    dates = [str(x.date()) for x in idx["date"]]
    r = backtest.replay(config.default_strategy()["params"], bars, idx, config.goal(),
                        dates[0], dates[-1], strategy_version=1)
    kacak_r = {k for s in (r.plan_log or []) for k in guard.Y3_PLAN_FIELDS if k in s}
    assert not kacak_r, f"replay plan defterine sızmış: {kacak_r}"


def test_c12_GOLGE_KOLU_kapsam_disi_BEYANI_BAYAT_DEGIL(seeded):
    """KAPSAM BEYANININ ÇİVİSİ (ters yönlü test). Gölge kapısının portföy sözlüğünü
    `shadow_variants._judge` kurar ve bu turda KABLOLANMADI (dosya-ayrıklık sözleşmesi). Beyan
    `shadow_lifecycle`de yazılı; kablo bağlandığı gün bu test KIRMIZI yanar ve beyanı sildirir.
    Bayat bir beyan, beyansızlıktan beterdir: okuyucuya kapalı bir kapıyı açık gösterir."""
    from meridian import shadow_variants as sv
    src = Path(sv.__file__).read_text()
    govde = src[src.index("def _judge("):]
    govde = govde[:govde.index('verdict, reasons = guard.classify_gate')]
    kablolu = [k for k in guard.Y3_PORTFOLIO_FIELDS if f'"{k}"' in govde]
    assert not kablolu, (f"`sv._judge` artık {kablolu} taşıyor — KABLO BAĞLANMIŞ. "
                         f"shadow_lifecycle.py'daki C12 kapsam beyanını SİL ve bu testi "
                         f"sözleşme kapsamasına çevir.")
    beyan = Path(sl.__file__).read_text()
    assert "C12 KAPSAM BEYANI" in beyan, "gölge kapsam beyanı kaybolmuş"


# =================================================================================================
# C13b — TERFİ KAPISI: CANLI MOTORUN OKUYAMADIĞI KNOB SINIFI
# =================================================================================================
def test_c13b_canli_olu_knob_SENTETIK_ornekle_REDDEDILIR(seeded, monkeypatch):
    """Bugün reddedilecek knob YOK (pivot kablosu bağlandı), o yüzden dal sentetik bir kayıtla
    sınanır: gerçek bir bounds knob'u listeye konur ve terfi yolunun KAPANDIĞI gösterilir."""
    b, g, p = config.bounds(), config.goal(), config.load_strategy()["params"]
    kurban = "exit.early_kill_pivot"
    assert kurban in b, "sentetik örnek bounds'ta olmayan bir adı kullanıyor — çivi anlamsız"
    onceki = guard.validate_change({"variable": kurban, "new": 1}, p, b, g, [], 0)
    assert onceki.ok, f"başlangıç durumu yanlış: {onceki.reasons}"     # NEGATİF KONTROL
    monkeypatch.setattr(guard, "LIVE_DEAD_KNOBS",
                        {kurban: "sentetik: canlı fill_entry pivot geçirmiyor"})
    v = guard.validate_change({"variable": kurban, "new": 1}, p, b, g, [], 0)
    assert not v.ok, "canlı-ölü knob terfi kapısından GEÇTİ"
    assert any("YAPISAL" in r and kurban in r for r in v.reasons), v.reasons
    assert v.variable == kurban, "ret satırı değişkeni taşımıyor — defterde kime ait belli olmaz"


def test_c13b_ret_DUZ_ve_REJIMLI_onerinin_IKISINI_de_kapatir(seeded, monkeypatch):
    """C13'ün kaçtığı yol DÜZ öneriydi (@regime varyantı zaten kapalıydı). Dal ikisini de
    kapatmazsa aynı knob başka bir kapıdan girer."""
    b, g = config.bounds(), config.goal()
    p = {**config.load_strategy()["params"], "exit.early_kill_pivot": 0}
    monkeypatch.setattr(guard, "LIVE_DEAD_KNOBS", {"exit.early_kill_pivot": "sentetik"})
    for prop in ({"variable": "exit.early_kill_pivot", "new": 1},
                 {"changes": {"exit.early_kill_pivot": 1}},
                 {"variable": "exit.early_kill_pivot@chop", "new": 1}):
        assert not guard.validate_change(prop, p, b, g, [], 0).ok, prop


def test_c13b_liste_BUGUN_BOS_ve_early_kill_pivot_ICINDE_DEGIL():
    """Kablo bağlandığı için liste boş olmalı. `exit.early_kill_pivot` buraya yazılırsa, ölçülmüş
    ve canlıya bağlanmış bir düğme terfi yolundan haksız yere düşerdi."""
    assert guard.LIVE_DEAD_KNOBS == {}, guard.LIVE_DEAD_KNOBS
    assert "exit.early_kill_pivot" not in guard.LIVE_DEAD_KNOBS


def test_c13b_listedeki_her_ad_GERCEK_bir_knob_olmali(seeded):
    """Dal DEKOR olmasın: listeye bounds'ta olmayan bir ad yazılırsa hiçbir öneriyi kesmez ama
    'korunuyoruz' hissi verir. (Liste bugün boş — çivi ileriye dönüktür.)"""
    b = config.bounds()
    hayalet = [k for k in guard.LIVE_DEAD_KNOBS if k not in b]
    assert not hayalet, f"LIVE_DEAD_KNOBS'ta arama uzayında olmayan ad(lar): {hayalet}"
    bos_gerekce = [k for k, v in guard.LIVE_DEAD_KNOBS.items() if len(str(v)) < 20]
    assert not bos_gerekce, f"gerekçesiz kayıt (≥20 karakter şart): {bos_gerekce}"


def test_c13b_MESRU_oneri_liste_bosken_GECER(seeded):
    """NEGATİF KONTROL: yeni dal, meşru bir öneriyi yanlışlıkla kesmiyor."""
    b, g, p = config.bounds(), config.goal(), config.load_strategy()["params"]
    v = guard.validate_change({"variable": "exit.time_stop_days", "new": 16}, p, b, g, [], 0)
    assert v.ok, v.reasons

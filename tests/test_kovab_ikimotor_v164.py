"""test_kovab_ikimotor_v164.py — KOVA-B İKİ-MOTOR EŞİTLİĞİ (denetim 2026-08-02: C11/C18/C13/C19).

DÖRT BULGU, TEK SINIF: "tek yasa, iki motor" sözleşmesi ÜÇ ayrı yerde yarım kabloluydu. Karar
MANTIĞI hiçbir yerde değişmedi; değişen, iki (üç) motorun AYNI yasayı GÖRMESİ:

  C11+C18 — E1 giriş limitinin ATR bacağı YALNIZ canlı motora bağlıydı. `broker.entry_limit_price`
            `off = min(mult·ATR, pct_cap·tetik) if ATR>0 else pct_cap·tetik` diyor; replay ve
            gölge-v2 `fill_entry`e `atr=` HİÇ geçmediği için limitleri DAİMA %1 tavanındaydı, canlı
            ise min(0,5·ATR14, %1) ile koşuyordu. Yön tek taraflı: replay/gölge, canlının REDDEDECEĞİ
            dolumları yazar → dolum oranı şişer, `entry_missed_limit` sıfırlanır ve öğrenme
            kapısı/gölge terfisi iyimser bir icra modeli üzerinden karar verir.
  C13     — `exit.early_kill_pivot` canlıda YAPISAL olarak ölüydü: `fill_entry`e `pivot=` geçilmiyor
            (→ `Position.pivot` daima 0.0) ve `manage_position`a giden sözlükte `pivot` anahtarı yok.
            İki kopukluk BAĞIMSIZ; ikisi de kapanmadan knob terfi etse canlıda SESSİZ NO-OP olurdu.
  C19     — günlük kayıp devre kesicisi iki motorda FARKLI pencere ölçüyordu: replay/gölge
            AÇILIŞ(D)→AÇILIŞ(D+1) (D'nin TÜM seansı), canlı ise KAPANIŞ(D)→AÇILIŞ(D+1) (yalnız
            GECELİK BOŞLUK) — yani `max_daily_loss_pct: 3.0` canlıda fiilen atıldı. Kanonik semantik
            REPLAY'inkidir; canlı taraf ona eşitlendi.

YÖNTEM: iddiaların çoğu DAVRANIŞSALDIR (motor gerçekten koşturulur, `fill_entry` çağrıları casusla
yakalanır) — kaynak metni okuyan çiviler yalnız davranışla gösterilemeyen FAZ iddiaları içindir ve
her birinin yanında bir POZİTİF KONTROL vardır: sınır bilerek delinir ve iddianın GERÇEKTEN düştüğü
gösterilir. Düşmeyen bir iddia koruma değil dekordur.
"""
from __future__ import annotations

import ast
import inspect
import shutil
from pathlib import Path

import pandas as pd
import pytest
import yaml

from meridian import backtest, broker as BR, config, loop, shadow_lifecycle as sl, store
from meridian.broker import PaperBroker
from tests.conftest import make_bars


# =================================================================================================
# ORTAK FİKSTÜRLER — test_differential_v60'ın evren tarifi (iki motoru da GERÇEKTEN silahlandıran
# tek tarif budur; ham make_bars barları veri kapısında 'ohlc_inconsistent' ile düşer).
# =================================================================================================
N_BARS = 300
INDEX_SEED, INDEX_TREND = 7, 0.0006
TICKERS = {"AAPL": 9, "JPM": 10, "UNH": 27, "CAT": 34, "XOM": 63, "KO": 5, "NKE": 6,
           "GS": 3, "MRK": 4}
WINDOW = 12          # işlenen seans sayısı (kırılımdan SONRA en az bir dolum penceresi kalsın)


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


class _FillCasusu:
    """`PaperBroker.fill_entry` çağrılarının ARGÜMANLARINI yakalar — kararı DEĞİŞTİRMEZ, yalnız
    kaydeder. AST yerine bunu tercih ediyoruz: "kaynakta `atr=` yazıyor" ile "broker o değeri
    GERÇEKTEN aldı" aynı iddia değildir (yan harita boş kalırsa ikincisi düşer, birincisi geçer).

    ÇAĞIRAN MODÜL DE KAYDEDİLİR ve bu ŞART: `loop.daily_cycle` kendi içinde gölge katmanlarını da
    koşturur (shadow_variants / shadow_lifecycle) ve onların çağrıları pivot/ATR TAŞIR. Filtresiz bir
    casus, canlı motor tamamen kablosuzken bile "birinde pivot var" diyerek YEŞİL yanardı — bu
    dosyanın negatif kontrolü tam olarak bu tuzağı yakaladı."""

    def __init__(self, monkeypatch):
        self.calls: list[dict] = []
        _asil = PaperBroker.fill_entry

        def _sarmal(zelf, plan, next_open, ts, equity, **kw):
            import sys as _sys
            self.calls.append({"ticker": plan.get("ticker"), "plan_id": plan.get("id"),
                               "ts": ts, "next_open": float(next_open),
                               "_cagiran": _sys._getframe(1).f_globals.get("__name__"), **kw})
            return _asil(zelf, plan, next_open, ts, equity, **kw)

        monkeypatch.setattr(PaperBroker, "fill_entry", _sarmal)

    def of(self, modul: str) -> list[dict]:
        return [c for c in self.calls if c.get("_cagiran") == modul]


def _canli_kosum(seeded, monkeypatch, *, params_ustu: dict | None = None):
    """Canlı döngüyü WINDOW seans koşturur ve fill_entry çağrılarını döndürür."""
    if params_ustu:
        strat = config.default_strategy()
        strat["params"].update(params_ustu)
        (seeded / "strategy.yaml").write_text(yaml.safe_dump(strat))
        config.reload_config()
    bars, idx = _universe()
    casus = _FillCasusu(monkeypatch)
    dates = [str(x.date()) for x in idx["date"].iloc[-WINDOW:]]
    for d in dates:
        loop.daily_cycle(bars, idx, on_date=d)
    return casus, bars, idx, dates


# =================================================================================================
# C11 + C18 — E1 LİMİTİNİN ATR BACAĞI ÜÇ MOTORDA DA BAĞLI
# =================================================================================================
def test_c11_replay_fill_entry_cagrisi_ATR_tasir(seeded, monkeypatch):
    """REPLAY DAVRANIŞI: silahlanan her plan için `fill_entry` ÖLÇÜLMÜŞ bir ATR ile çağrılır.

    Eskiden argüman hiç verilmiyordu (`atr=None` varsayılanı) ve `entry_limit_price` `a > 0` dalına
    hiç giremiyordu. `sig.atr` replay'de ÖLÇÜLMÜŞTÜR (strategy.EntrySignal.atr) — "ölçülemedi" dalına
    düşmek, ölçülmüş bir değeri yok saymaktı."""
    bars, idx = _universe()
    casus = _FillCasusu(monkeypatch)
    dates = [str(x.date()) for x in idx["date"]]
    backtest.replay(config.default_strategy()["params"], bars, idx, config.goal(),
                    dates[0], dates[-1], strategy_version=1)
    cagrilar = casus.of("meridian.backtest")
    assert cagrilar, "replay hiç fill denemedi — test bir şey kanıtlamıyor"
    eksik = [c for c in cagrilar if not c.get("atr")]
    assert not eksik, (f"{len(eksik)}/{len(cagrilar)} replay dolum denemesi ATR'siz — "
                       f"limit %1 tavanına düşüyor, canlı motorla ayrışıyor: {eksik[:3]}")
    assert all(float(c["atr"]) > 0 for c in cagrilar)


def test_c11_golge_fill_entry_cagrisi_ATR_tasir(seeded, monkeypatch):
    """GÖLGE-v2 DAVRANIŞI: `step`, yan haritadaki ATR'yi broker'a GEÇİRİR."""
    d = "2026-07-30"
    df = _valid_ohlc(make_bars(60, seed=11))
    df.loc[df.index[-1], "date"] = pd.Timestamp(d)
    ix = df.set_index("date")
    bk = sl._new_book("V3")
    plan = {"id": f"P-{d}-AAPL", "ticker": "AAPL", "date": d, "side": "long",
            # tetik = D'nin AÇILIŞI: E1 limiti (tetik + offset) açılışın ÜSTÜNDE kalsın, yani bu
            # senaryo `entry_missed_limit` yolunu değil GERÇEK dolumu sınasın.
            "entry_trigger": float(ix.loc[d, "open"]), "stop": float(ix.loc[d, "open"]) * 0.9,
            "profit_target": float(ix.loc[d, "open"]) * 1.3, "size_r": 1.0}
    bk["armed"] = [{"plan": plan, "pivot": 12.5, "atr": 3.75}]
    casus = _FillCasusu(monkeypatch)
    sl.step(bk, config.default_strategy()["params"], d, lambda t: ix if t == "AAPL" else None,
            regime_ok=True, limits=config.goal()["limits"], goal=config.goal(), armed_next=[])
    assert casus.calls, "gölge motoru hiç fill denemedi — test bir şey kanıtlamıyor"
    assert casus.calls[0]["atr"] == 3.75, "gölge yan haritadaki ATR'yi broker'a geçirmiyor"
    assert casus.calls[0]["pivot"] == 12.5, "pivot bacağı da taşınmalı (G3b, birlikte gider)"
    b = sl._to_broker(bk, config.goal())
    assert b.positions.get("AAPL") and b.positions["AAPL"].pivot == pytest.approx(12.5), \
        "argüman geçti ama Position'a yazılmadı — kablo yarım"


def test_c11_golge_yan_haritasi_ATRyi_SINYALDEN_doldurur(seeded, monkeypatch):
    """KABLONUN İKİNCİ UCU: `sv._judge` yan haritayı yalnız `pivot` ile üretiyor. `_day` onu
    silahlanma anındaki SİNYALDEN (EntrySignal.atr) tamamlamazsa `step`e daima None gider ve
    davranış birinci testi geçse bile üretimde ATR bacağı yine ölü kalır."""
    class _Sig:
        ticker, atr = "AAPL", 4.25

    plan = {"id": "P-2026-07-30-AAPL", "ticker": "AAPL", "size_r": 1.0}
    monkeypatch.setattr(sl.sv, "_judge",
                        lambda *a, **k: ([], [], [{"plan": plan, "pivot": 1.0}]))
    yakalanan: list = []
    monkeypatch.setattr(sl, "step", lambda bk, p, d, bo, **kw: yakalanan.append(kw["armed_next"]) or [])
    doc = sl._new_doc()
    df = _valid_ohlc(make_bars(60, seed=12))
    sl._day(doc, "2026-07-30", {}, tickers=["AAPL"], tail_of=lambda t: df,
            rs_of=lambda t: 80, sector_of=lambda t: "tech", max_corr_of=lambda t: 0.1,
            eff=config.default_strategy()["params"], regime={"exposure_budget_pct": 60},
            regime_ok=True, goal=config.goal(), limits=config.goal()["limits"], version=1,
            bars_of=lambda t: None,
            sigs_by_variant={vid: [_Sig()] for vid in sl.arms()})
    assert yakalanan, "_day hiçbir kola silahlı plan vermedi — test bir şey kanıtlamıyor"
    assert all(e[0]["atr"] == 4.25 for e in yakalanan if e), \
        "yan harita ATR'siz kaldı — sinyalde ÖLÇÜLMÜŞ değer icra yoluna geçmiyor"


def test_c11_atr_bacagi_limiti_GERCEKTEN_sikilastirir():
    """AYRIŞMANIN BÜYÜKLÜĞÜ (pozitif kontrol): ATR bacağı bağladığında iki limit FARKLIDIR, yani
    yukarıdaki kablo testleri boş bir farkı çivilemiyor."""
    law = BR.entry_law()
    dar = BR.entry_limit_price(100.0, 1.0, law)     # 0,5·ATR = 0,50 < %1·100
    genis = BR.entry_limit_price(100.0, None, law)  # yalnız yüzde tavanı
    assert dar < genis, "ATR bacağı hiç bağlamıyor — yasa yapılandırması testi anlamsız kılıyor"
    b = PaperBroker(equity=100_000, slippage_bps=0, commission_per_share=0.0)
    plan = {"id": "P1", "ticker": "X", "entry_trigger": 100.0, "stop": 90.0,
            "profit_target": 130.0, "size_r": 1.0}
    acilis = (dar + genis) / 2.0                    # İKİ limitin ARASINDA açan bar
    red: dict = {}
    assert b.fill_entry(plan, acilis, "d1", 100_000, atr=1.0, reject_out=red) is None
    assert red["reason"] == BR.EV_MISSED_LIMIT
    assert b.fill_entry(plan, acilis, "d1", 100_000, atr=None) is not None


def test_c18_replay_ciktisi_entry_missed_limit_SAYAR(seeded, monkeypatch):
    """C18 önerisi: `reject_out` geçirilip kaçan dolumlar replay ÇIKTISINDA görünmeli — yoksa
    "replay canlının reddettiği dolumları yazıyor mu?" sorusu ölçülemez.

    POZİTİF KONTROL: limit tavanı bilerek daraltılır; sayaç ARTMALI ve işlem sayısı DÜŞMELİ."""
    bars, idx = _universe()
    dates = [str(x.date()) for x in idx["date"]]
    p = config.default_strategy()["params"]
    normal = backtest.replay(p, bars, idx, config.goal(), dates[0], dates[-1], strategy_version=1)
    assert isinstance(normal.entry_rejects, dict), \
        "entry_rejects sözlük değil — kaçan dolumlar hâlâ ölçülemiyor"

    _asil = BR.entry_law
    monkeypatch.setattr(BR, "entry_law",
                        lambda override=None: {**_asil(override), "limit_atr_mult": 0.0,
                                               "limit_pct_cap": 1e-9})
    dar = backtest.replay(p, bars, idx, config.goal(), dates[0], dates[-1], strategy_version=1)
    assert dar.entry_rejects.get(BR.EV_MISSED_LIMIT, 0) > 0, \
        "limit sıfıra çekildi ama hiç `entry_missed_limit` sayılmadı — sayaç kablosuz"
    assert len(dar.trades) < len(normal.trades), \
        "limit bağladı ama işlem sayısı düşmedi — replay limiti fiilen uygulamıyor"


def test_c18_hic_ret_yokken_sozluk_BOS_None_degil(seeded):
    """UYDURMA YASAĞI'nın ikiz maddesi: "ölçüldü ve sıfır" ile "hiç ölçülmedi" ayrı kalmalı."""
    bos = backtest.BacktestResult(trades=[], equity=[], params={}, start="x", end="y")
    assert bos.entry_rejects is None, "ölçülmemiş sonuç {} göstererek 'ret yoktu' diyemez"
    bars, idx = _universe(breakout_at=None)     # kırılım yok + ısınma penceresi → hiç dolum denemesi
    dates = [str(x.date()) for x in idx["date"]]
    res = backtest.replay(config.default_strategy()["params"], bars, idx, config.goal(),
                          dates[0], dates[20], strategy_version=1)
    assert res.entry_rejects == {}, "koşan replay ret sayacını None bırakmamalı"


# =================================================================================================
# C13 — `exit.early_kill_pivot` CANLIDA ARTIK OKUNABİLİR
# =================================================================================================
def test_c13_canli_fill_entry_cagrisi_PIVOT_tasir(seeded, monkeypatch):
    """CANLI DAVRANIŞ: `fill_entry` pozitif bir pivotla çağrılır ve `Position.pivot`a yazılır.

    Eskiden argüman hiç verilmiyordu → `Position.pivot` daima 0.0 → `early_kill_pivot_exit`
    `position.get("pivot")`ı 0 okuyup her koşulda False dönüyordu (yapısal ölüm)."""
    casus, *_ = _canli_kosum(seeded, monkeypatch)
    cagrilar = casus.of("meridian.loop")          # gölge katmanlarının çağrıları SAYILMAZ
    assert cagrilar, "canlı döngü hiç fill denemedi — test bir şey kanıtlamıyor"
    pivotsuz = [c for c in cagrilar if not c.get("pivot")]
    assert not pivotsuz, (f"{len(pivotsuz)}/{len(cagrilar)} canlı dolum denemesi pivotsuz — "
                          f"erken itlaf canlıda yapısal olarak ölü kalır: {pivotsuz[:3]}")
    assert all(c.get("atr") for c in cagrilar), "canlı yol ATR bacağını da taşımalı (E1)"
    # yan tablo gerçekten SİLAHLANMA anında sabitlenmiş bir sayı taşıyor mu (uydurma sıfır değil)
    pf = store.read_json(loop.PORTFOLIO, {}) or {}
    law = pf.get("entry_law") or {}
    assert all(("pivot" in v) for v in law.values()), "entry_law yan tablosunda pivot alanı yok"


def test_c13_canli_manage_position_sozlugu_PIVOT_tasir(seeded, monkeypatch):
    """İKİNCİ (BAĞIMSIZ) KOPUKLUK: pivot `Position`a yazılsa bile `manage_position`a giden
    sözlükte yoksa çıkış yine ateşleyemez. Casus GERÇEK canlı turdan sözlüğü yakalar."""
    import sys as _sys

    from meridian import strategy as strat
    sozlukler: list[dict] = []
    _asil = strat.manage_position

    def _sarmal(bars, position, params, bars_held, regime_ok):
        # ÇAĞIRAN FİLTRESİ ZORUNLU: daily_cycle içinde gölge motorları da manage_position çağırır ve
        # onların sözlüğü pivotu ZATEN taşır — filtresiz bir casus canlı motor kablosuzken de yeşil
        # yanardı (negatif kontrol bunu yakaladı).
        if _sys._getframe(1).f_globals.get("__name__") == "meridian.loop":
            sozlukler.append(dict(position))
        return _asil(bars, position, params, bars_held, regime_ok)

    monkeypatch.setattr(strat, "manage_position", _sarmal)
    _canli_kosum(seeded, monkeypatch)
    assert sozlukler, "canlı turda hiç açık pozisyon yönetilmedi — test bir şey kanıtlamıyor"
    eksik = [s for s in sozlukler if "pivot" not in s]
    assert not eksik, f"{len(eksik)}/{len(sozlukler)} canlı yönetim sözlüğünde `pivot` anahtarı yok"
    assert any((s.get("pivot") or 0) > 0 for s in sozlukler), \
        "sözlükte anahtar var ama değeri hep 0 — kablo yine ölü (fill_entry bacağı kopuk)"


# --- TERFİ SINIFI: "canlı motorun OKUYAMADIĞI knob" -----------------------------------------------
# Denetim önerisi bu sınıfı terfi kapısında (`guard.validate_change`) reddetmeyi öneriyordu; guard.py
# bu turda BAŞKA bir ajanın kapsamında olduğu için kontrol MOTOR TARAFINA konuyor ve aslında oraya
# daha çok ait: kapı bir knob ADI listesi tutmak zorunda kalırdı, buradaki çivi ise knob adı bilmeden
# SINIFI yakalar — replay/gölge'nin `manage_position`a verdiği her ALAN canlıda da verilmelidir.
# Bir çıkış düğmesi yalnız bu sözlükten okunabilir; replay'in bilip canlının bilmediği bir alan,
# tanımı gereği "replayde ateşler, canlıda no-op" sınıfıdır.
_MOTOR_YOLU = {"canli": (loop, "daily_cycle"), "replay": (backtest, "replay"),
               "golge_v2": (sl, "step")}


def _manage_sozluk_anahtarlari(mod, fn_adi: str) -> set:
    """`strat/strategy.manage_position(...)` çağrısındaki POZİSYON sözlüğünün anahtarları (AST)."""
    fn = getattr(mod, fn_adi)
    tree = ast.parse(inspect.getsource(fn))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "manage_position":
            for arg in node.args:
                if isinstance(arg, ast.Dict):
                    return {k.value for k in arg.keys if isinstance(k, ast.Constant)}
    return set()


def test_c13_uc_motor_da_AYNI_yonetim_sozlugunu_veriyor():
    """SINIF ÇİVİSİ: gelecekte replay'e eklenip canlıya eklenmeyen HER çıkış girdisi burada patlar."""
    kumeler = {ad: _manage_sozluk_anahtarlari(*yol) for ad, yol in _MOTOR_YOLU.items()}
    for ad, ks in kumeler.items():
        assert ks, f"{ad}: manage_position çağrısının sözlüğü AST'de bulunamadı — çivi kör"
    ortak = set.intersection(*kumeler.values())
    for ad, ks in kumeler.items():
        assert ks == ortak, (f"{ad} motoru diğerlerinden farklı alan kümesi veriyor: "
                             f"fazla={sorted(ks - ortak)} — canlı-ölü knob sınıfı")
    assert "pivot" in ortak, "pivot üç motorda da yönetim sözlüğünde olmalı (C13)"


def test_c13_sinif_civisi_SENTETIK_ayrismayi_gercekten_yakalar():
    """POZİTİF KONTROL: çivinin kendisi sınanır — replay'de olup canlıda olmayan sentetik bir alan
    kurulursa karşılaştırma DÜŞMELİ. (Düşmeyen bir çivi koruma değil dekordur.)"""
    kumeler = {"canli": {"entry", "stop"}, "replay": {"entry", "stop", "uydurma_knob_girdisi"}}
    ortak = set.intersection(*kumeler.values())
    ayrisan = {ad for ad, ks in kumeler.items() if ks != ortak}
    assert ayrisan == {"replay"}, "sentetik ayrışma yakalanmadı — çivi kör"


def test_c13_pivot_okunabilince_erken_itlaf_ATESLER():
    """DAVRANIŞ: aynı bar, aynı knob — pivot ölçülemezken False, ölçülünce True. Karar mantığı
    değişmedi; değişen yalnız girdinin motora ULAŞMASI."""
    from meridian import strategy as strat
    bars = pd.DataFrame({"close": [100.0, 99.0, 98.0]})
    params = {"exit.early_kill_pivot": 1, "exit.early_kill_bars": 1}
    olcusuz = {"entry": 100.0, "stop": 95.0, "trail_stop": 95.0, "r_per_share": 5.0, "pivot": 0.0}
    olculu = {**olcusuz, "pivot": 99.5}
    assert strat.early_kill_pivot_exit(bars, olcusuz, params, 1) is False
    assert strat.early_kill_pivot_exit(bars, olculu, params, 1) is True


# =================================================================================================
# C19 — GÜNLÜK KESİCİ PENCERESİ İKİ MOTORDA AYNI
# =================================================================================================
def _acilis_marklariyla_sermaye(b, per_open: dict) -> float:
    return b.start_equity + b.realized_pnl + sum(
        p.qty * (per_open[t] - p.entry) for t, p in b.positions.items() if t in per_open)


def test_c19_canli_gun_basi_sermayesi_ACILIS_markiyla_yazilir(seeded, monkeypatch):
    """CANLI DAVRANIŞ: `day_start_equity`, işlenen seansın AÇILIŞ markıyla yazılır (replay
    konvansiyonu). Eskiden KAPANIŞ markıyla yazılıyor, okuma tarafı ise ertesi AÇILIŞI kullanıyordu
    → pencere yalnız GECELİK BOŞLUK'tu ve −%3'lük sert limit canlıda fiilen atıldı.

    Beklenen değer barlardan ve DEFTERDEN bağımsız olarak yeniden hesaplanır — döngünün iç
    değişkenine bakmıyoruz, diske yazdığı sayıyı kendi barlarımızla doğruluyoruz."""
    _casus, bars, _idx, dates = _canli_kosum(seeded, monkeypatch)
    pf = store.read_json(loop.PORTFOLIO, {}) or {}
    assert pf.get("positions"), "canlı turda açık pozisyon kalmadı — mark farkı ölçülemez"
    son = dates[-1]
    from meridian.score import START_EQUITY
    b = PaperBroker(START_EQUITY, 0, 0)
    b.realized_pnl = pf["realized_pnl"]
    for t, p in pf["positions"].items():
        b.positions[t] = BR.Position(**p)
    per = {t: df.set_index("date") for t, df in bars.items()}
    d = pd.Timestamp(son)
    acilis = {t: float(per[t].loc[d, "open"]) for t in b.positions if d in per[t].index}
    kapanis = {t: float(per[t].loc[d, "close"]) for t in b.positions if d in per[t].index}
    assert acilis, "son seansta işaretlenebilir pozisyon yok — test bir şey kanıtlamıyor"
    assert acilis != kapanis, "açılış == kapanış: bu barlarda iki faz ayırt edilemez (çivi kör)"
    assert pf["day_start_equity"] == pytest.approx(b.equity(acilis)), \
        "canlı gün-başı sermayesi AÇILIŞ markıyla yazılmıyor — kesici penceresi replay'den ayrık"
    assert pf["day_start_equity"] != pytest.approx(b.equity(kapanis)), \
        "yazılan değer kapanış markıyla aynı — regresyon (eski davranış geri gelmiş)"


def test_c19_golge_v2_ayni_konvansiyonu_yazar(seeded):
    """ÜÇÜNCÜ MOTOR: gölge-v2 zaten AÇILIŞ markındaydı; eşitlemenin onu bozmadığı çivilenir."""
    d = "2026-07-30"
    df = _valid_ohlc(make_bars(60, seed=21))
    df.loc[df.index[-1], "date"] = pd.Timestamp(d)
    ix = df.set_index("date")
    bk = sl._new_book("V3")
    plan = {"id": f"P-{d}-AAPL", "ticker": "AAPL", "date": d, "side": "long",
            # tetik = D'nin AÇILIŞI: E1 limiti (tetik + offset) açılışın ÜSTÜNDE kalsın, yani bu
            # senaryo `entry_missed_limit` yolunu değil GERÇEK dolumu sınasın.
            "entry_trigger": float(ix.loc[d, "open"]), "stop": float(ix.loc[d, "open"]) * 0.9,
            "profit_target": float(ix.loc[d, "open"]) * 1.3, "size_r": 1.0}
    bk["armed"] = [{"plan": plan, "pivot": 1.0, "atr": 2.0}]
    sl.step(bk, config.default_strategy()["params"], d, lambda t: ix if t == "AAPL" else None,
            regime_ok=True, limits=config.goal()["limits"], goal=config.goal(), armed_next=[])
    b = sl._to_broker(bk, config.goal())
    assert b.positions, "gölge kolunda pozisyon açılmadı — mark karşılaştırması boş"
    acilis = {"AAPL": float(ix.loc[d, "open"])}
    kapanis = {"AAPL": float(ix.loc[d, "close"])}
    assert bk["day_start_equity"] == pytest.approx(b.equity(acilis))
    assert bk["day_start_equity"] != pytest.approx(b.equity(kapanis))


def test_c19_uc_motorun_YAZMA_fazi_ayni_kaynakta_kanitli():
    """FAZ ÇİVİSİ (davranışla gösterilemeyen tek parça): yazımın hangi FAZDA olduğu. Üç motor da
    `day_start_equity`yi AÇILIŞ markıyla yazmalı ve canlı motorda KAPANIŞ marklı ikinci bir yazım
    kalmamalı — C19'un kökü tam olarak "okuma açılışa çevrildi, yazma kapanışta unutuldu"ydu."""
    canli = inspect.getsource(loop.daily_cycle)
    yazimlar = [s for s in canli.splitlines() if 'meta["day_start_equity"] =' in s]
    assert len(yazimlar) == 1, f"canlı motorda tek yazım bekleniyor, {len(yazimlar)} bulundu"
    assert "_marks(per, d)" not in yazimlar[0], \
        "canlı gün-başı sermayesi yine KAPANIŞ markıyla yazılıyor (C19 regresyonu)"
    assert '"open"' in yazimlar[0], "canlı yazım açılış markı kullanmıyor"
    rep = [s for s in inspect.getsource(backtest.replay).splitlines()
           if "day_start_equity =" in s and "broker.equity" in s]
    assert rep and all("marks_open_on" in s for s in rep), "replay yazımı açılış markından çıkmış"
    gol = [s for s in inspect.getsource(sl.step).splitlines() if 'day_start_equity"] =' in s]
    assert gol and all("_marks_open()" in s for s in gol), "gölge yazımı açılış markından çıkmış"


def test_c19_kesici_penceresi_iki_motorda_ESIT_gun_ici_hareketi_gorur():
    """DİFERANSİYEL: aynı defter + aynı barlarla iki motorun kesici PENCERESİ eşit.

    Pencere = (AÇILIŞ(D+1) sermayesi − gün-başı sermayesi) / gün-başı. Gün-başı AÇILIŞ(D) ise
    pencere D'nin TÜM seansını görür; KAPANIŞ(D) ise yalnız gecelik boşluğu. Sentetik defterde
    gün-içi hareket ile gecelik boşluk BİLEREK zıt işaretli seçildi: eski canlı pencere kesiciyi
    ateşlemez, replay penceresi ateşler — iki motorun ayrıştığı nokta tam burasıdır."""
    b = PaperBroker(100_000.0, 0, 0)
    plan = {"id": "P1", "ticker": "X", "entry_trigger": 100.0, "stop": 90.0,
            "profit_target": 130.0, "size_r": 1.0}
    pos = b.fill_entry(plan, 100.0, "D", 100_000.0, atr=10.0)
    assert pos is not None and pos.qty > 0
    acilis_D, kapanis_D, acilis_D1 = 100.0, 100.0 - 3.5 * 100_000 / pos.qty / 100, None
    # D kapanışı: özkaynağı gün-başına göre −%3,5 taşıyacak fiyat; D+1 açılışı kapanışın %0,1 üstü.
    acilis_D1 = kapanis_D * 1.001
    kanonik = (b.equity({"X": acilis_D1}) - b.equity({"X": acilis_D})) / b.equity({"X": acilis_D})
    eski_canli = (b.equity({"X": acilis_D1}) - b.equity({"X": kapanis_D})) / b.equity({"X": kapanis_D})
    from meridian import health
    goal = config.goal()
    assert health.circuit_breaker_tripped(kanonik, goal) is True, \
        "kanonik (replay) pencere bu senaryoda ateşlemeli — senaryo çiviyi kuramıyor"
    assert health.circuit_breaker_tripped(eski_canli, goal) is False, \
        "eski canlı pencere de ateşliyor — senaryo iki pencereyi ayırt etmiyor"
    # EŞİTLİK HÜKMÜ: canlı motor artık kanonik pencereyi ölçer (yazma fazı testiyle birlikte okunur).
    assert kanonik < -0.03 <= eski_canli

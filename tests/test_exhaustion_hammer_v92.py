"""test_exhaustion_hammer_v92 — Stockbee satış-tükenmesi ÇEKİCİ kurulumu (KEYLESS, SİLAHLI).

'declared-only' bir screener'ı motor-uygulanmış bir setup'a dönüştürmenin kanıtı: evaluate_exhaustion_hammer
GERÇEKTEN ateşler (kör no-op değil), scan_all'da HER ticker'da koşar, per-skill attribution'a doğru
screener'a bağlanır. Anahtarsız (OHLCV).

SİLAHLANMA TARİHÇESİ (BEYANLI test güncellemesi, sinsi değil): dosya 2026-07-24'te DORMANT sözleşmesini
çiviliyordu ("ARMED_SETUPS'a EKLENMEDİĞİ için canlı deftere SIFIR risk"). 2026-08-11 operatör onayıyla
("A seçeneği — exhaustion_hammer'ı silahla"; P-2026-08-07-VLO vakası) kurulum SİLAHLANDI; DORMANT
testi aynı tarihle SİLAHLI sözleşmesine çevrildi. momentum_burst/episodic_pivot DORMANT kalır ve
onların çivileri (test_audit_fixes / test_efficiency_v8 / test_decision_v3) DEĞİŞMEDİ.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

import meridian.strategy as strat
import meridian.skills as skills
import meridian.indicators as ind
from meridian.guard import DISCIPLINE_MIN_RR


def _hammer_bars(pullback: float = 0.07, pb_start: int = 76, n: int = 90) -> pd.DataFrame:
    """Uptrend + son günlere yoğunlaşmış geri çekilme + son barda uzun-alt-fitilli çekiç (undercut+reclaim).
    Geri çekilme son günlere sıkışır → HAFTALIK trend hâlâ yukarı (düşen-bıçak filtresi geçilir)."""
    close = np.array([100.0 * (1.005 ** i) for i in range(n)])
    peak = close[pb_start - 1]
    for k, i in enumerate(range(pb_start, n)):
        frac = (k + 1) / (n - pb_start)
        close[i] = peak * (1 - pullback * frac)
    openp = close.copy()
    high = close * 1.004
    low = close * 0.996
    vol = np.full(n, 1.5e6)
    base = close[-1]
    openp[-1] = base * 1.0005          # gövde küçük
    low[-1] = base * 0.972             # uzun alt fitil (gün dibi)
    close[-1] = base * 1.006           # kapanış tepeye yakın
    high[-1] = close[-1] * 1.001
    for i in range(n - 6, n - 1):      # önceki dipleri delip geri alma (undercut/reclaim) için
        low[i] = min(low[i], close[i] * 0.995)
    dates = pd.bdate_range("2022-01-03", periods=n)
    return pd.DataFrame({"date": dates, "open": openp, "high": high, "low": low,
                         "close": close, "volume": vol})


def test_hammer_fires_real_signal():
    """Kör no-op DEĞİL: geometri kurulunca geçerli bir LONG EntrySignal döner (stop<entry<hedef, rr≥taban)."""
    df = _hammer_bars()
    sig = strat.evaluate_exhaustion_hammer(df, {}, 95, "T")
    assert sig is not None, "çekiç barında hiç ateşlemedi — setup ölü olurdu"
    assert sig.setup == "exhaustion_hammer"
    assert sig.stop < sig.entry_trigger < sig.profit_target
    assert sig.r_per_share > 0
    rr = (sig.profit_target - sig.entry_trigger) / sig.r_per_share
    assert rr >= DISCIPLINE_MIN_RR - 1e-9, f"disiplin R:R tabanının altında yüzeye çıktı: {rr}"


def test_flat_trend_no_fire():
    """Düz/gürültülü trendde geometri yok → None (pano çöp sinyalle dolmaz)."""
    from tests.conftest import make_bars
    assert strat.evaluate_exhaustion_hammer(make_bars(200, seed=5), {}, 95, "T") is None


def test_young_symbol_stays_silent():
    """KRİTİK REGRESYON: EH 252-bar trend_template kapısını PAYLAŞMAZ (yalnız 65 bar ister). Yine de genç
    sembolde ateşlememeli — aksi hâlde test_data_pipeline'ın scan_all(genç)=={} invaryantı kırılır. Burada
    None 'ısınma eksik' zorlamasıyla değil, o barın çekiç OLMAMASIYla gelir (veriye bağlı, doğru)."""
    from tests.conftest import make_bars
    young = make_bars(320, seed=11, trend=0.0009, breakout_at=250).iloc[-150:].reset_index(drop=True)
    assert strat.evaluate_exhaustion_hammer(young, {}, 95, "KVUE") is None


def test_no_look_ahead():
    """Karar barından SONRAKİ barlar 4× fiyat / 9× hacimle bozulup aynı dilime kesilince karar BİREBİR aynı.
    Tek eksik geriye-pencere (prior_high/prior_low bugünü hariç tutar) burada patlardı."""
    df = _hammer_bars()
    L = len(df)
    base = strat.evaluate_exhaustion_hammer(df, {}, 95, "T")
    assert base is not None
    fut = pd.concat([df, df.tail(5).copy()], ignore_index=True)
    fut.loc[L:, ["open", "high", "low", "close"]] *= 4.0
    fut.loc[L:, "volume"] *= 9.0
    after = strat.evaluate_exhaustion_hammer(fut.iloc[:L], {}, 95, "T")
    assert after is not None
    assert base.as_row() == after.as_row(), "karar GELECEK barlarla değişti — ileri-dönük sızıntı"


def test_armed_by_operator_2026_08_11():
    """SİLAHLI (operatör onayı 2026-08-11): ARMED_SETUPS'ta VAR ve scan_entry çekiç sinyalini aday yapar.
    SIRA sözleşmesi de çivili: kanıtlı iki kurulum (breakout_vcp, pullback) öncelikli kalır —
    exhaustion_hammer onlardan SONRA gelir (aynı ticker'da ancak onlar ateşlemediyse aday üretir).

    İDDİA DARALTILDI (2026-08-12, BEYANLI): eski hâli "tuple'ın SONUNDADIR" diyordu. O gün doğruydu
    (silahlı küme üçlüydü) ama yazdığı şey sıra sözleşmesi değil, KÜME BÜYÜKLÜĞÜYDÜ: momentum_burst
    operatör onayıyla sona eklenince (karar penceresi §E.2) çivi, korumadığı bir şey yüzünden
    kırılırdı. Korunan asıl yasa — "kanıtlı iki kurulum ÖNCE gelir" — aşağıda doğrudan ölçülüyor."""
    assert "exhaustion_hammer" in strat.ARMED_SETUPS, \
        "operatör onayı (2026-08-11) geri alınmış görünüyor — silahlanma bilinçli karardı"
    # 2026-08-22: `pullback` B1 kararıyla silahsızlandı (EDG-2026-039, v260) — sıra zinciri
    # ondan arındırıldı; çivinin NİYETİ aynen: sonradan silahlanan, öncekilerin ARKASINA eklenir.
    assert strat.ARMED_SETUPS.index("exhaustion_hammer") \
        > strat.ARMED_SETUPS.index("breakout_vcp"), \
        "öncelik sırası değişti: kanıtlı kurulumlar (breakout_vcp, pullback) önce gelmeli"
    df = _hammer_bars()
    by_setup = strat.scan_all(df, {}, 95, "T")
    assert "exhaustion_hammer" in by_setup, "scan_all setup'ı ölçmüyor — attribution kör kalır"
    armed = strat.scan_entry(df, {}, 95, "T")
    assert armed is not None and armed.setup == "exhaustion_hammer", \
        "silahlı çekiç sinyali canlı aday üretmedi — onaylı silahlanma fiilen ölü"


def test_diger_uyuyanlar_dormant_kalir():
    """SİLAHLANMA TARİHÇESİ (BEYANLI, sinsi değil): 2026-08-11 onayı YALNIZ exhaustion_hammer
    içindi ve bu test o gün momentum_burst + episodic_pivot'u DORMANT çiviliyordu. 2026-08-12'de
    momentum_burst AYRI bir operatör onayıyla silahlandı (karar penceresi §E.2; kanıt EDG-2026-025
    karnesi + EDG-2026-032 final-paket 3/3) — iddia o adı BIRAKTI, kalan uyuyanlar için DURUYOR.
    Yani bu test hâlâ aynı şeyi koruyor: silahlanma otomatik değildir, her ad ayrı bir insan
    kararıdır (`arming.py` kapı GEÇSE bile ARMED_SETUPS'a dokunmaz)."""
    assert "momentum_burst" in strat.ARMED_SETUPS, \
        "operatör onayı (2026-08-12) geri alınmış görünüyor — silahlanma bilinçli karardı"
    assert strat.ARMED_SETUPS.index("momentum_burst") == len(strat.ARMED_SETUPS) - 1, \
        "mb ÖNCELİK kazanmış: tarihçe-korumalı karar 'sona ekle' idi (032'nin ölçtüğü sıra)"
    for uyuyan in ("episodic_pivot", "pead", "canslim"):
        assert uyuyan not in strat.ARMED_SETUPS, f"{uyuyan} onaysız silahlanmış"


def test_screener_attribution_wired():
    """Per-skill avg_r doğru screener'a bağlanır ve P2'de 'invoked' (declared-only değil)."""
    assert skills.screener_for("exhaustion_hammer") == "stockbee-exhaustion-hammer-screener"
    assert "stockbee-exhaustion-hammer-screener" in skills.ENGINE_IMPLEMENTED

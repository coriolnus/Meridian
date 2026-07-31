"""test_execution_fidelity_v75.py — DOLDURMA GERÇEKÇİLİĞİ denetimi (2026-07-22, tur 75).

Neden bu dosya var: recompute.py defterin KENDİ İÇİNDE tutarlı olduğunu kanıtlıyor (gerçekleşen P&L
işlem defterine, nakit özdeşliği, öz sermaye kuyruğu). Ama o sayıların HEPSİ dolum simülatöründen
iner. Simülatör yanlış fiyattan doldurursa, yanlış adet boyutlandırırsa ya da R'yi yanlış muhasebe
ederse defter KUSURSUZ TUTARLI ve TAMAMEN KURGUSAL olur — hiçbir dedektör göremez, çünkü hepsi aynı
uydurma sayıları birbirine doğruluyor.

Yöntem: her testin bar dizisi ELDE hesaplanabilir. Beklenen dolum/çıkış/R yorumda açıkça yazılıdır;
iddia o sayıyı BİREBİR arar. Ayrıca gerçek önbellek barlarıyla (state/bars, salt-okunur) iki
olumlu kontrol.
"""
from __future__ import annotations

import csv
import json
import pathlib

import pandas as pd
import pytest

from meridian.broker import PaperBroker, Position, ADV_CAP_PCT, IMPACT_COEF

REPO = pathlib.Path(__file__).resolve().parent.parent


def _plan(tid="P1", ticker="AAA", trigger=100.0, stop=95.0, target=115.0, size_r=1.0):
    return {"id": tid, "ticker": ticker, "entry_trigger": trigger, "stop": stop,
            "profit_target": target, "size_r": size_r}


def _clean_broker(slip_bps=0.0, comm=0.0, equity=100_000.0):
    """Sıfır sürtünmeli defter: aritmetik elle takip edilebilsin. Sürtünme ayrı testlerde ölçülür."""
    return PaperBroker(equity=equity, slippage_bps=slip_bps, commission_per_share=comm)


# =================================================================================================
# KUSUR 1 — açılışta GARANTİ dolan hedef boşluğu, bar-içi BELİRSİZ stop dokunuşuna yeniliyordu
# =================================================================================================

def test_kusur1_hedefin_ustunde_acilan_bar_stop_olarak_yazilamaz():
    """ELDE HESAP.
    giriş 100 (slipaj 0), stop 95 → R/hisse = 5, risk$ = 1.0R·%1·100k = 1000 → adet = 1000/5 = 200.
    trail 108'e çekilmiş (breakeven+ATR — üretimde exit.breakeven_r=1.0 ile OLAĞAN durum), hedef 115.
    Bar: o=116, h=118, l=107.
      GERÇEK: bar 116'da AÇILDI; 115'lik hedef emri barın İLK fiyatında zaten doldu.
              → target_gap @116, P&L = 200·(116−100) = +3200 → +3.2R.
              Pozisyon açılışta kapandığı için 107'lik low'a UĞRAYAN bir pozisyon YOKTU.
      ESKİ KOD: `l <= eff_stop` kontrolü `o >= target`ın önündeydi → stop @108, +1600 → +1.6R.
      HATA: 1.6R (kazançlı işlemin yarısı), her böyle barda.
    """
    b = _clean_broker()
    pos = b.fill_entry(_plan(), next_open=100.0, ts="d0", equity=100_000)
    assert (pos.qty, pos.entry, pos.r_per_share, pos.risk_dollars) == (200, 100.0, 5.0, 1000.0)
    pos.trail_stop = 108.0

    ex = b._touch_exit(pos, {"open": 116.0, "high": 118.0, "low": 107.0})
    assert ex == (116.0, "target_gap"), f"açılış hedefin üstündeydi, çıkış açılışta olmalı: {ex}"

    row = b.close_position("AAA", ex[0], ex[1], "d1")
    assert row["pnl_dollars"] == pytest.approx(3200.0, abs=0.01)
    assert row["r_multiple"] == pytest.approx(3.2, abs=1e-9)


def test_kusur1b_uc_ornek_gap_up_hem_hedefi_hem_stopu_kapsiyor():
    """ELDE HESAP. giriş 100, stop 95, hedef 115, adet 200 (yukarıdaki gibi).
    Bar: o=118, h=120, l=94  (bir kazanç uyarısı: %18 boşlukla açıp gün içi %20 aralık).
      GERÇEK: açılış 118 ≥ hedef 115 → target_gap @118 = 200·18 = +3600 → +3.6R.
      ESKİ KOD: l=94 ≤ stop 95 → stop @95 = −1000 → −1.0R.
      HATA: 4.6R — tek satırda. Yön KÖTÜMSER ama çarpıklık çarpıklıktır: motor boşluk-yukarı
      kurulumlarını sistematik olarak EKSİK öğrenir.
    """
    b = _clean_broker()
    pos = b.fill_entry(_plan(), next_open=100.0, ts="d0", equity=100_000)
    ex = b._touch_exit(pos, {"open": 118.0, "high": 120.0, "low": 94.0})
    assert ex == (118.0, "target_gap")
    row = b.close_position("AAA", ex[0], ex[1], "d1")
    assert row["r_multiple"] == pytest.approx(3.6, abs=1e-9)


def test_kusur1c_bar_ICINDE_stop_hala_hedefi_yener():
    """GERİLEME KORUMASI: muhafazakârlık bar İÇİNDE geçerli kalmalı. Açılış ikisinin de dışındaysa
    (o=100 → ne stop ne hedef) ve bar hem stop'u hem hedefi görüyorsa sıra OHLC'den bilinemez →
    STOP kazanır. Bar: o=100, h=120, l=94 → stop @95, −1.0R."""
    b = _clean_broker()
    pos = b.fill_entry(_plan(), next_open=100.0, ts="d0", equity=100_000)
    ex = b._touch_exit(pos, {"open": 100.0, "high": 120.0, "low": 94.0})
    assert ex == (95.0, "stop"), f"bar-içi belirsizlikte stop ÖNCE gelmeli: {ex}"
    assert b.close_position("AAA", ex[0], ex[1], "d1")["r_multiple"] == pytest.approx(-1.0)


def test_kusur1d_stop_altinda_acilis_hala_stop_gap():
    """Aynı kademe-1 mantığı stop tarafında: açılış stop'un altındaysa hedef high'ı görülse bile
    çıkış AÇILIŞTA'dır. Bar: o=90, h=130, l=89 → stop_gap @90 (= −2.0R), hedef 115 asla dolmaz."""
    b = _clean_broker()
    pos = b.fill_entry(_plan(), next_open=100.0, ts="d0", equity=100_000)
    ex = b._touch_exit(pos, {"open": 90.0, "high": 130.0, "low": 89.0})
    assert ex == (90.0, "stop_gap")
    assert b.close_position("AAA", ex[0], ex[1], "d1")["r_multiple"] == pytest.approx(-2.0)


# =================================================================================================
# KUSUR 2 — aynı sıralama hatası karşı-olgusal defterde de vardı ve GERÇEKTEN gerçekleşti
# =================================================================================================

def test_kusur2_cf_gercek_swks_satirini_dogru_cozer(sandbox_state, monkeypatch):
    """CANLI DEFTERDEN ALINMIŞ SATIR: CF-2025-10-28-SWKS-momentum_burst, çözüm barı 2025-10-29.
      bar: o=83.14, h=84.53, l=78.59, c=79.50 | hedef 82.74, stop 79.27
      Kayıt bekleyen (pending) durumdaydı → aynı barda dolar: giriş = 83.14·(1+5bps) = 83.1816.
      Giriş ZATEN hedefin üstünde; hedef emri barın ilk fiyatında dolu → target_gap @83.14,
      çıkış dolumu 83.14·(1−5bps) = 83.0984 → R = (83.0984 − 83.1816)/(83.1816 − 79.27) = −0.021R.
      ESKİ KOD: l=78.59 ≤ stop 79.27 → 'stop' @79.27 → −1.001R.  (canlı defterde −1.01 yazılı)
      HATA: ~0.98R, gölge modelin ve kalibrasyonun eğitim setinde.
    """
    from meridian import counterfactual as cf, store

    row = {"id": "CF-2025-10-28-SWKS-momentum_burst", "date": "2025-10-28", "ticker": "SWKS",
           "setup": "momentum_burst", "score": 70, "entry_trigger": 80.60, "stop": 79.27,
           "target": 82.74, "rr_expected": 1.6, "r_multiple_expected": 1.6, "regime": "chop",
           "verdict": "DORMANT", "taken": False, "dormant": True, "status": "pending",
           "time_stop_days": 15, "bars_held": 0}
    store.write_json(cf.OPEN_FILE, [row])

    d = pd.Timestamp("2025-10-29")
    per = {"SWKS": pd.DataFrame([{"open": 83.14, "high": 84.53, "low": 78.59, "close": 79.50}],
                                index=[d])}
    cf.advance(per, d, "2025-10-29")

    out = [json.loads(l) for l in (sandbox_state / cf.LEDGER).read_text().splitlines() if l.strip()]
    assert len(out) == 1
    r = out[0]
    assert r["exit_reason"] == "target_gap", f"açılış hedefin üstündeydi: {r['exit_reason']}"
    assert r["entry"] == pytest.approx(83.1816, abs=1e-3)
    assert r["exit"] == pytest.approx(83.0984, abs=1e-3)
    assert r["r_multiple"] == pytest.approx(-0.021, abs=0.005)
    assert r["r_multiple"] > -0.1, "eski kod burada −1.01R yazıyordu"


def test_kusur2b_cf_bar_ici_belirsizlikte_hala_stop_onceligi(sandbox_state):
    """CF tarafında da muhafazakârlık korunmalı: açılış aralığın içindeyse ve bar hem stop'u hem
    hedefi görüyorsa STOP. bar: o=100, h=120, l=94 | stop 95, hedef 115 → 'stop' @95."""
    from meridian import counterfactual as cf, store
    store.write_json(cf.OPEN_FILE, [{"id": "CF-X", "date": "2026-01-01", "ticker": "AAA",
                                     "setup": "s", "entry_trigger": 100.0, "stop": 95.0,
                                     "target": 115.0, "status": "pending", "time_stop_days": 15,
                                     "bars_held": 0}])
    d = pd.Timestamp("2026-01-02")
    per = {"AAA": pd.DataFrame([{"open": 100.0, "high": 120.0, "low": 94.0, "close": 96.0}], index=[d])}
    cf.advance(per, d, "2026-01-02")
    r = [json.loads(l) for l in (sandbox_state / cf.LEDGER).read_text().splitlines() if l.strip()][0]
    assert r["exit_reason"] == "stop"


# =================================================================================================
# KUSUR 3 — mfe_r / mae_r, backtest.replay'den gelen HER satırda uydurma SIFIR'dı
# =================================================================================================

def _walk_like_backtest(b: PaperBroker, pos: Position, bars: list[dict], params: dict | None = None):
    """backtest.replay'in INTRADAY(D) bloğunun BİREBİR çağrı dizisi (backtest.py:199-204):
    scale_out(pos, bar, prev_eff) → _touch_exit → (çıkış yoksa) bars_held++. Su işaretlerine DOKUNMAZ.

    params, gerçek çağrıdaki `prev_eff`'in (o günün çözülmüş strateji parametreleri) karşılığıdır.
    Eskiden burada boş `{}` geçiliyordu (2026-07-23 tarama bulgusu): scale_out ilk satırda
    `exit.scale_out_frac`=0 görüp çıkıyor, yani 'birebir' denen kopyada kısmi-satış dalı HİÇ
    koşmuyordu ve iddia kısmi satış altında geçersizdi. Varsayılan {} çağrı davranışını korur
    (kısmi satış zaten default OFF), ama artık çağıran gerçek params enjekte edebilir."""
    for bar in bars:
        b.scale_out(pos, bar, params or {})
        ex = b._touch_exit(pos, bar)
        if ex:
            return ex
        pos.bars_held += 1
    return None


def test_kusur3c_kismi_satis_altinda_da_mfe_gercek_yuksegi_yakalar():
    """BİREBİR YOLUN KISMİ SATIŞLI SINANMASI (2026-07-23): _walk_like_backtest artık gerçek params
    geçirebildiği için kısmi-satış dalı de KOŞAR. Kısmi satış gerçekleşen R'ı düşürse bile MFE su
    işareti tepe yükseği yakalamaya devam etmeli — mfe bir 'ne olabilirdi' ölçüsüdür, kasadan
    çıkarılana değil."""
    b = _clean_broker()
    pos = b.fill_entry(_plan(target=130.0), next_open=100.0, ts="d0", equity=100_000)
    prm = {"exit.scale_out_frac": 0.5, "exit.scale_out_r": 2.0}   # 110'da yarısını sat, stop breakeven=100
    # bar1 low, kısmi satış sonrası breakeven stop'un (100) ÜSTÜNDE kalmalı — yoksa aynı barda stop'a
    # düşer; senaryo kısmi satış + tepeye yürüyüş, erken stop değil.
    bars = [{"open": 101.0, "high": 112.0, "low": 100.5, "close": 110.0},  # 110 → kısmi satış tetiği (2R)
            {"open": 110.0, "high": 128.0, "low": 108.0, "close": 126.0},  # ara tepe 128
            {"open": 126.0, "high": 130.0, "low": 125.0, "close": 130.0}]  # hedef 130 dolar (tepe = 130)
    ex = _walk_like_backtest(b, pos, bars, prm)
    assert ex == (130.0, "target")
    assert pos.scaled_out is True, "kısmi satış dalı koşmadı — params enjeksiyonu birebir değil"
    row = b.close_position("AAA", ex[0], ex[1], "d3")
    # en yüksek high = 130 → MFE = (130−100)/5 = 6.0R; kısmi satış gerçekleşen R'ı düşürse de MFE değişmez
    assert row["mfe_r"] == pytest.approx(6.0, abs=1e-3), "MFE tepe yükseği (130) yakalamalı, kısmi satış onu kırpmamalı"
    assert row["mfe_r"] >= row["r_multiple"] - 1e-6


def test_kusur3_backtest_yolu_gercek_mfe_mae_damgalamali():
    """ELDE HESAP. giriş 100, stop 95 → R/hisse 5, adet 200.
    Barlar: (o=101,h=112,l=99) → (o=110,h=114,l=96) → (o=113,h=116,l=112) son barda hedef 115 dolar.
      en yüksek high = 116 → MFE = (116−100)/5 = +3.2R
      en düşük  low  = 96  → MAE = (100−96)/5  = +0.8R
    ESKİ KOD: hi_water/lo_water hiç güncellenmiyordu → mfe_r = 0.0, mae_r = 0.0 yazılıyordu.
    close_position'daki "su işareti yoksa None" koruması ateşlenemiyordu, çünkü hi_water girişte
    fill'e kuruluyor (>0). Yani boşluk None değil UYDURMA SIFIR olarak defteredüşüyordu.
    """
    b = _clean_broker()
    pos = b.fill_entry(_plan(), next_open=100.0, ts="d0", equity=100_000)
    bars = [{"open": 101.0, "high": 112.0, "low": 99.0, "close": 110.0},
            {"open": 110.0, "high": 114.0, "low": 96.0, "close": 113.0},
            {"open": 113.0, "high": 116.0, "low": 112.0, "close": 115.0}]
    ex = _walk_like_backtest(b, pos, bars)
    assert ex == (115.0, "target")
    row = b.close_position("AAA", ex[0], ex[1], "d3")
    assert row["mfe_r"] == pytest.approx(3.2, abs=1e-3), "MFE uydurma sıfır"
    assert row["mae_r"] == pytest.approx(0.8, abs=1e-3), "MAE uydurma sıfır"
    # MFE, gerçekleşen R'den KÜÇÜK OLAMAZ — analytics.exit_efficiency'nin left_r'si bunu varsayar
    assert row["mfe_r"] >= row["r_multiple"] - 1e-6


def test_kusur3b_hedefte_kapanan_islemin_mfe_si_asla_sifir_olamaz():
    """ARİTMETİK İMKÂNSIZLIK KORUMASI: hedefte kapanan bir işlemin MFE'si tanımı gereği en az
    gerçekleşen R kadardır. Canlı state/exit_efficiency.json'da 'target' kovası
    avg_mfe_r=2.617 / avg_realized_r=2.307 iken GERÇEK satırların 5'i mfe_r=0.0 taşıyordu; o 5
    satırın left_r'si −1.821 — 'masada bırakılan negatif ödül' diye bir şey YOKTUR."""
    b = _clean_broker()
    pos = b.fill_entry(_plan(), next_open=100.0, ts="d0", equity=100_000)
    ex = _walk_like_backtest(b, pos, [{"open": 101.0, "high": 118.0, "low": 100.5, "close": 117.0}])
    row = b.close_position("AAA", ex[0], ex[1], "d1")
    assert row["exit_reason"] == "target"
    assert row["mfe_r"] - row["r_multiple"] >= -1e-6, "left_r NEGATİF çıkıyor — imkânsız"


def test_kusur3c_eski_kayittaki_su_isareti_yoklugu_hala_None():
    """Koruma korunmalı: portfolio.json'dan yüklenmiş ESKİ bir pozisyonda su işaretleri 0.0'dır;
    _touch_exit onları uydurmamalı, close_position None yazmalı (uydurma yasak)."""
    b = _clean_broker()
    pos = b.fill_entry(_plan(), next_open=100.0, ts="d0", equity=100_000)
    pos.hi_water = 0.0
    pos.lo_water = 0.0
    b._touch_exit(pos, {"open": 101.0, "high": 112.0, "low": 99.0})
    assert pos.hi_water == 0.0 and pos.lo_water == 0.0
    row = b.close_position("AAA", 110.0, "time_stop", "d1")
    assert row["mfe_r"] is None and row["mae_r"] is None


# =================================================================================================
# KUSUR 4 — kısmi satış HEDEFİN ÜSTÜNDE bankalıyordu (bedava R)
# =================================================================================================

def test_kusur4_kismi_satis_hedefin_ustunde_bankalayamaz():
    """ELDE HESAP — ikisi de bounds.yaml İÇİNDE (exit.scale_out_r ≤ 4.0, exit.profit_target_r ≥ 2.0):
      giriş 100, stop 95 → R/hisse 5, adet 200.  hedef = 110 (2.0R).  scale_out_r = 4.0 → level 120.
      Bar: o=105, h=125, l=104.
      GERÇEK: 125'e giden yol 110'un İÇİNDEN geçer; 110'daki hedef emri TÜM pozisyonu kapatır.
              → 200·(110−100) = +2000 → +2.0R. 120'de satılacak hisse KALMAZ.
      ESKİ KOD: 100 hisseyi @120 bankalar (+2000) + kalan 100'ü @110 kapatır (+1000) = +3000 → +3.0R.
      HATA: +1.0R BEDAVA, her böyle işlemde. Mutasyon araması tam bunu arar ve bulur.
    """
    b = _clean_broker()
    pos = b.fill_entry(_plan(target=110.0), next_open=100.0, ts="d0", equity=100_000)
    prm = {"exit.scale_out_frac": 0.5, "exit.scale_out_r": 4.0}
    bar = {"open": 105.0, "high": 125.0, "low": 104.0, "close": 124.0}
    assert b.scale_out(pos, bar, prm) is False, "hedefin ÜSTÜNDEKİ seviyede bankalama yapılamaz"
    assert pos.qty == 200 and pos.banked_pnl == 0.0
    ex = b._touch_exit(pos, bar)
    row = b.close_position("AAA", ex[0], ex[1], "d1")
    assert (ex[1], row["r_multiple"]) == ("target", pytest.approx(2.0))


def test_kusur4b_hedefin_ustunde_acilan_barda_kismi_satis_yok():
    """Bar hedefin ÜSTÜNDE açıldıysa pozisyon ilk fiyatta kapanmıştır; kısmi satış diye bir an yoktur.
    hedef 115, level = 100+2·5 = 110, bar o=116 → scale_out False, çıkış target_gap @116 (+3.2R)."""
    b = _clean_broker()
    pos = b.fill_entry(_plan(), next_open=100.0, ts="d0", equity=100_000)
    bar = {"open": 116.0, "high": 120.0, "low": 115.0, "close": 119.0}
    assert b.scale_out(pos, bar, {"exit.scale_out_frac": 0.5, "exit.scale_out_r": 2.0}) is False
    ex = b._touch_exit(pos, bar)
    assert ex == (116.0, "target_gap")
    assert b.close_position("AAA", *ex, "d1")["r_multiple"] == pytest.approx(3.2)


def test_kusur4c_hedefin_ALTINDAKI_kismi_satis_hala_calisiyor():
    """Özelliği kırmadık: level hedefin altındaysa (2.0R < 2.5R hedef) bankalama olağan şekilde olur.
    ELDE HESAP: giriş 100, R/hisse 5, adet 200, hedef 115 (3.0R), level 110, frac 0.5 → 100 hisse
    @110 = +1000 bankalanır; trail breakeven'a (100) çekilir. Bar o=104,h=112,l=103 → çıkış yok.
    Sonraki bar 115'i görürse kalan 100 @115 = +1500. Toplam 2500 → 2.5R (adet-ağırlıklı, TEK satır)."""
    b = _clean_broker()
    pos = b.fill_entry(_plan(), next_open=100.0, ts="d0", equity=100_000)
    prm = {"exit.scale_out_frac": 0.5, "exit.scale_out_r": 2.0}
    assert b.scale_out(pos, {"open": 104.0, "high": 112.0, "low": 103.0, "close": 111.0}, prm) is True
    assert (pos.qty, pos.banked_pnl, pos.trail_stop) == (100, 1000.0, 100.0)
    row = b.close_position("AAA", 115.0, "target", "d2")
    assert len(b.closed) == 1, "kısmi satış EKSTRA satır üretmemeli"
    assert row["pnl_dollars"] == pytest.approx(2500.0, abs=0.01)
    assert row["r_multiple"] == pytest.approx(2.5, abs=1e-9)
    assert b.realized_pnl == pytest.approx(row["pnl_dollars"], abs=0.01)


# =================================================================================================
# R MUHASEBESİ — deklare edilen R ile GERÇEKTEN alınan risk aynı şey mi?
# =================================================================================================

def test_r_tabani_adet_yuvarlanmasi_gercek_riski_deklare_r_altina_indiriyor():
    """KARAKTERİZASYON (kusur değil ama R BİR BİRİM DEĞİL): risk_dollars = size_r·%1·equity SABİT
    kalır, adet ise AŞAĞI yuvarlanır → gerçek maksimum kayıp deklare 1R'den küçüktür.
    ELDE HESAP: equity 100k, risk$ = 1000. giriş 100 (slipaj 0), stop 73.415 → R/hisse 26.585
    → adet = floor(1000/26.585) = 37... pahalı isimde adet küçüldükçe hata büyür.
    CANLI DEFTERDEN: T00105 (TDG, adet=2) gerçek risk 53.2$ / deklare 69.6$ = 0.764 — tam stop'a
    giden işlem −1.0R değil −0.76R yazar. 129 satırın 6'sı deklare 1R'nin %90'ından azını
    riske ediyor; oran dağılımı 0.764 … 1.033, yani R satırdan satıra 35% oynuyor."""
    b = _clean_broker()
    pos = b.fill_entry(_plan(stop=73.415), next_open=100.0, ts="d0", equity=100_000)
    assert pos.qty == 37 and pos.r_per_share == pytest.approx(26.585)
    gercek_risk = pos.qty * pos.r_per_share                     # 983.6
    assert gercek_risk < pos.risk_dollars
    row = b.close_position("AAA", 73.415, "stop", "d1")
    assert row["r_multiple"] == pytest.approx(-gercek_risk / 1000.0, abs=1e-3)
    assert row["r_multiple"] > -1.0, "tam stop −1.0R'den DAHA AZ zarar yazıyor (yuvarlama)"
    # bilinen sapmanın SINIRI: bir hisselik yuvarlama payından fazlası olmamalı
    assert 1.0 - gercek_risk / pos.risk_dollars <= pos.r_per_share / pos.risk_dollars + 1e-9


def test_r_tabani_adv_etkisi_gercek_riski_deklare_r_ustune_cikariyor():
    """KUSUR (küçük ama gerçek): likidite etkisi fiyatı yukarı iter ama risk$ TABAN fiyattan
    yeniden türetilir → gerçek risk deklare R'yi AŞAR.
    ELDE HESAP: equity 100k, risk$ 1000, giriş 100, stop 95, adv = 10_000 hisse.
      taban dolum = 100, adet = floor(1000/5) = 200; ADV tavanı = %2·10_000 = 200 → tam tavanda.
      katılım = 200/10_000 = %2 → etki = 0.10·0.02 = %0.2 → dolum = 100.20, R/hisse = 5.20.
      GERÇEK risk = 200·5.20 = 1040$  ama  risk_dollars = 200·(100−95) = 1000$  → %4 AŞIM.
      Sonuç: tam stop −1.04R yazar ve AYNI satırda mae_r = 1.000 çıkar — bir satırda İKİ FARKLI R.
    Bu test aşımı SINIRLAR: IMPACT_COEF/ADV_CAP_PCT büyürse sessizce büyümesin."""
    b = _clean_broker()
    pos = b.fill_entry(_plan(), next_open=100.0, ts="d0", equity=100_000, adv=10_000)
    assert pos.qty == int(ADV_CAP_PCT * 10_000) == 200
    assert pos.entry == pytest.approx(100.0 * (1 + IMPACT_COEF * ADV_CAP_PCT))
    asim = pos.qty * pos.r_per_share / pos.risk_dollars - 1.0
    assert asim == pytest.approx(0.04, abs=1e-6), "deklare R aşımı beklenenden farklı"
    ex = b._touch_exit(pos, {"open": 99.0, "high": 99.5, "low": 95.0})   # tam stop'ta çıkış
    assert ex == (95.0, "stop")
    row = b.close_position("AAA", *ex, "d1")
    assert row["r_multiple"] == pytest.approx(-1.04, abs=1e-6)   # payda: risk_dollars (taban dolum)
    assert row["mae_r"] == pytest.approx(1.0, abs=1e-6)          # payda: r_per_share (etkili dolum)
    #  ↑ AYNI SATIRDA İKİ FARKLI R TABANI: aynı olay bir sütunda −1.04R, ötekinde 1.000R.
    assert asim <= 0.05, "likidite etkisi deklare riski %5'ten fazla aşamaz"


def test_r_orijinal_stopa_gore_olculur_trail_e_gore_degil():
    """OLUMLU KONTROL. giriş 100, sert stop 95 (R/hisse 5, adet 200, risk$ 1000). Trail 108'e çekilir
    ve işlem oradan çıkar: P&L = 200·8 = +1600. R, ORİJİNAL riske göre 1600/1000 = +1.6R olmalı —
    trail'e (100→108, 8$) göre ölçülseydi 1.0R çıkardı ve her trail'li kazanç aynı görünürdü."""
    b = _clean_broker()
    pos = b.fill_entry(_plan(), next_open=100.0, ts="d0", equity=100_000)
    pos.trail_stop = 108.0
    ex = b._touch_exit(pos, {"open": 112.0, "high": 113.0, "low": 107.0})
    assert ex == (108.0, "stop")
    row = b.close_position("AAA", *ex, "d1")
    assert row["r_multiple"] == pytest.approx(1.6, abs=1e-9)
    assert pos.r_per_share == 5.0, "R/hisse trail ile DEĞİŞMEMELİ"


# =================================================================================================
# OLUMLU KONTROLLER — temiz bir işlem, elle hesaplanan tam sayıyı üretmeli
# =================================================================================================

def test_olumlu_kontrol_temiz_hedef_islemi_tam_R():
    """ELDE HESAP, sürtünme DAHİL (slipaj 10bps, komisyon 0.01$/hisse, equity 100k, size_r 1.0):
      taban dolum = 100·1.0010 = 100.10 ;  R/hisse = 100.10 − 95 = 5.10
      risk$ = 1.0 · %1 · 100_000 = 1000 ;  adet = floor(1000/5.10) = 196
      notional = 196·100.10 = 19_619.60 ≤ %25·100k ✓
      giriş komisyonu = 196·0.01 = 1.96 (kapanışa ertelenir)
      çıkış: ham 115 → dolum 115·0.9990 = 114.885 ; çıkış komisyonu = 1.96
      brüt = 196·(114.885 − 100.10) = 196·14.785 = 2897.86
      P&L  = 2897.86 − 1.96 − 1.96 = 2893.94  →  R = 2893.94/1000 = 2.894
      sürtünme (costs) = giriş kayma 196·0.10=19.60 + 1.96 + çıkış kayma 196·0.115=22.54 + 1.96 = 46.06
    """
    b = PaperBroker(equity=100_000, slippage_bps=10, commission_per_share=0.01)
    pos = b.fill_entry(_plan(), next_open=100.0, ts="d0", equity=100_000)
    assert (pos.qty, pos.entry, pos.r_per_share) == (196, pytest.approx(100.10), pytest.approx(5.10))
    row = b.close_position("AAA", 115.0, "target", "d5")
    assert row["exit"] == pytest.approx(114.885, abs=1e-4)
    assert row["pnl_dollars"] == pytest.approx(2893.94, abs=0.01)
    assert row["r_multiple"] == pytest.approx(2.894, abs=0.001)
    assert row["costs"] == pytest.approx(46.06, abs=0.01)
    # muhasebe kapanıyor: kapalı satırların toplamı = broker öz sermayesi
    assert b.equity() == pytest.approx(100_000 + row["pnl_dollars"], abs=0.01)


def test_olumlu_kontrol_tam_stop_sadece_surtunme_kadar_1R_i_asar():
    """ELDE HESAP (aynı defter): stop 95'te çıkış → dolum 95·0.9990 = 94.905.
      brüt = 196·(94.905 − 100.10) = −1018.22 ; komisyon 2·1.96 → P&L = −1022.14 → −1.022R.
      −1.0R'den fazlası SADECE çıkış kayması + komisyondur; sürtünme kaybolursa ya da işaret
      dönerse bu iddia düşer."""
    b = PaperBroker(equity=100_000, slippage_bps=10, commission_per_share=0.01)
    b.fill_entry(_plan(), next_open=100.0, ts="d0", equity=100_000)
    row = b.close_position("AAA", 95.0, "stop", "d5")
    assert row["pnl_dollars"] == pytest.approx(-1022.14, abs=0.01)
    assert row["r_multiple"] == pytest.approx(-1.022, abs=0.001)
    assert -1.05 < row["r_multiple"] < -1.0


def test_olumlu_kontrol_muhasebe_ozdesligi_yeni_cikis_sirasi_altinda():
    """GERİLEME: sıralama düzeltmesi nakit özdeşliğini bozmamalı. Kısmi satış + boşluk çıkışları
    karışık bir dizi; sonunda equity == start + Σ pnl_dollars == start + realized_pnl."""
    b = PaperBroker(equity=100_000, slippage_bps=7, commission_per_share=0.005)
    dizi = [("AAA", 100.0, 95.0, 115.0, {"open": 116.0, "high": 118.0, "low": 107.0}),
            ("BBB", 50.0, 47.0, 60.0, {"open": 46.0, "high": 61.0, "low": 45.0}),
            ("CCC", 200.0, 190.0, 230.0, {"open": 205.0, "high": 235.0, "low": 204.0})]
    for i, (tk, op, st, tg, bar) in enumerate(dizi):
        pos = b.fill_entry(_plan(f"P{i}", tk, op, st, tg), next_open=op, ts="d0", equity=b.equity())
        assert pos is not None
        b.scale_out(pos, {**bar, "close": bar["high"]},
                    {"exit.scale_out_frac": 0.25, "exit.scale_out_r": 2.0})
        ex = b._touch_exit(pos, bar)
        assert ex is not None
        b.close_position(tk, ex[0], ex[1], "d1")
    toplam = sum(r["pnl_dollars"] for r in b.closed)
    assert len(b.closed) == 3
    assert b.equity() == pytest.approx(100_000 + toplam, abs=0.02)
    assert b.realized_pnl == pytest.approx(toplam, abs=0.02)


# =================================================================================================
# GERÇEK BARLARLA OLUMLU KONTROLLER (salt-okunur)
# =================================================================================================

def _oku_barlar(ticker: str) -> dict:
    f = REPO / "state" / "bars" / f"{ticker}.csv"
    if not f.exists():
        return {}
    with f.open() as fh:
        return {r["date"][:10]: {k: float(r[k]) for k in ("open", "high", "low", "close")}
                for r in csv.DictReader(fh)}


@pytest.mark.parametrize("dosya", ["trades.jsonl"])
def test_gercek_defter_girisleri_BASILMIS_bir_barin_ACILISI(dosya):
    """OLUMLU KONTROL — ileriye bakış yok: canlı defterdeki her işlemin `entry`si, ts_open gününün
    GERÇEK açılışı × (1+slipaj) olmalı. Sinyal barından dolum (lookahead) burada patlardı.
    Bilinen tek istisna T00070 (DD, 2024-05-28): önbellek barları geriye dönük bölünme/spinoff
    düzeltmesi almış, tohumlanmış defter eski fiyatı taşıyor — dolum kusuru değil, veri sürümü farkı."""
    trades = [json.loads(l) for l in (REPO / "state" / dosya).read_text().splitlines() if l.strip()]
    plans = {}
    for l in (REPO / "state" / "trade_plans.jsonl").read_text().splitlines():
        if l.strip():
            p = json.loads(l)
            plans[p["id"]] = p
    slip = 5 / 10_000.0
    sapan, kontrol, plan_sonrasi = [], 0, 0
    for t in trades:
        p = plans.get(t.get("plan_id"))
        bar = _oku_barlar(t["ticker"]).get(t["ts_open"])
        if not p or not bar:
            continue
        kontrol += 1
        if t["ts_open"] > p["date"][:10]:
            plan_sonrasi += 1
        beklenen = bar["open"] * (1 + slip)
        if abs(t["entry"] - beklenen) / beklenen > 0.003:        # etki payı: ADV etkisi ≤ %0.2
            sapan.append((t["id"], t["ticker"], t["ts_open"]))
    # ÖRNEKLEM EŞİĞİ ORANSAL (2026-07-22): mutlak `> 100` yazılıydı ve defterin O ANKİ boyutuna
    # (129 işlem) bağlıydı. Matematik düzeltmeleri sonrası yeniden tohumlama 96 işlem üretti ve test
    # bir KUSUR bulmadan düştü. Test "yeterince satır denetlendi mi" diye sormalı, "kitap kaç işlem
    # içeriyor" diye değil.
    assert kontrol >= max(30, int(0.75 * len(trades))), \
        f"defterin yalnız {kontrol}/{len(trades)} satırı denetlenebildi — plan/bar eşleşmesi kopuk"
    assert plan_sonrasi == kontrol, "bir dolum plan gününde ya da ÖNCESİNDE gerçekleşmiş (lookahead)"
    # SAPMA KALMADI (2026-07-22). Denetim sırasında TEK sapan satır vardı (T00070/DD 2024-05-28) ve
    # sebebi bir dolum kusuru DEĞİL, önbellek barlarının geriye dönük bölünme/spinoff düzeltmesiyle
    # tohumlanmış kitabın ayrışmasıydı. Matematik düzeltmeleri sonrası kitap yeniden tohumlandı ve
    # o ayrışma da kapandı: artık HER giriş, BASILMIŞ bir barın açılışı × (1 + kayma).
    # Beklenti bilerek SIFIR: yeni bir sapma belirirse bu gerçek bir dolum kusurudur.
    assert not sapan, f"dolum sapması: {sapan} — giriş, basılmış bir barın açılışı olmalı"


def test_gercek_barlarda_yeni_cikis_sirasi_islem_defterini_bozmuyor():
    """OLUMLU KONTROL — canlı defterdeki 129 işlemin çıkış barı, YENİ sıralama altında da aynı
    nedeni vermeli (sıralama düzeltmesi yalnız 'açılış hedefin üstünde' barlarını değiştirir ve
    bu defterde öyle bir bar YOK — düzeltme geçmiş defteri yeniden yazmaz, ileriyi düzeltir)."""
    trades = [json.loads(l) for l in (REPO / "state" / "trades.jsonl").read_text().splitlines() if l.strip()]
    plans = {}
    for l in (REPO / "state" / "trade_plans.jsonl").read_text().splitlines():
        if l.strip():
            p = json.loads(l)
            plans[p["id"]] = p
    degisen = []
    for t in trades:
        p = plans.get(t.get("plan_id"))
        bar = _oku_barlar(t["ticker"]).get(t["ts_close"])
        if not p or not bar:
            continue
        tgt = float(p.get("profit_target") or (p.get("targets") or [0])[0])
        if tgt and bar["open"] >= tgt and t["exit_reason"] not in ("target", "target_gap"):
            degisen.append((t["id"], t["exit_reason"], bar["open"], tgt))
    assert degisen == [], f"eski sıra bu satırları YANLIŞ yazmıştı: {degisen}"


# =================================================================================================
# KUSUR 5 — cf'nin BELGELENMEMİŞ sapması: zaman stopu bir seans ERKEN ve KAPANIŞTAN çıkıyor
# =================================================================================================

def test_kusur5_cf_zaman_stopu_motordan_bir_seans_once_ve_kapanistan(sandbox_state):
    """counterfactual.py'nin belgelenmiş TEK sapması "trail / scale-out / rejim-dönüşü çıkışları yok".
    Zaman stopunun ZAMANLAMASI da sapıyor ama bu HİÇBİR YERDE yazmıyor:

      MOTOR : bars_held her seans INTRADAY'de artar (giriş seansı dahil). CLOSE(D)'de
              manage_position `bars_held >= time_stop` görünce pending_exit koyar; emir bir SONRAKİ
              seansın AÇILIŞINDA dolar. time_stop=3 → giriş D0, çıkış D3'ün AÇILIŞI.
      CF    : `bars_held + 1 >= time_stop` kontrolü aynı barın İÇİNDE yapılır ve çıkış o barın
              KAPANIŞIDIR. time_stop=3 → çıkış D2'nin KAPANIŞI.

    Fark: bir seans + bir gecelik boşluk. 2230 satırlık exit_efficiency havuzunun 916'sı time_stop;
    871'i cf. Yön sistematik değil ama sapma BELGESİZ — cf↔gerçek karşılaştırması (cf_fidelity
    corr≈0.887) bu farkı 'trail/scale-out' hanesine yazıyor.
    Bu test mevcut cf davranışını ÇİVİLER: değişirse bilerek değişmiş olur."""
    from meridian import counterfactual as cf, store
    store.write_json(cf.OPEN_FILE, [{"id": "CF-T", "date": "2026-01-01", "ticker": "AAA",
                                     "setup": "s", "entry_trigger": 100.0, "stop": 90.0,
                                     "target": 200.0, "status": "pending", "time_stop_days": 3,
                                     "bars_held": 0}])
    # ne stop ne hedef görülür; yalnız zaman stopu ateşlenebilir
    seans = [("2026-01-02", 100.0, 101.0, 99.0, 100.5),
             ("2026-01-05", 100.5, 102.0, 100.0, 101.5),
             ("2026-01-06", 101.5, 103.0, 101.0, 102.5),
             ("2026-01-07", 102.5, 104.0, 102.0, 103.5)]
    for dstr, o, h, l, c in seans:
        d = pd.Timestamp(dstr)
        per = {"AAA": pd.DataFrame([{"open": o, "high": h, "low": l, "close": c}], index=[d])}
        cf.advance(per, d, dstr)
    out = [json.loads(x) for x in (sandbox_state / cf.LEDGER).read_text().splitlines() if x.strip()]
    assert len(out) == 1
    r = out[0]
    assert r["exit_reason"] == "time_stop"
    # giriş 2026-01-02'nin açılışında; cf ÜÇÜNCÜ seansın (2026-01-06) KAPANIŞINDA çıkıyor…
    assert r["resolved"] == "2026-01-06"
    assert r["exit"] == pytest.approx(102.5 * (1 - 5 / 10_000.0), abs=1e-3)
    # …motor ise DÖRDÜNCÜ seansın (2026-01-07) AÇILIŞINDA çıkardı: 102.5 ≠ 102.5 açılış değil, 102.5
    # kapanış. Aradaki bir seans + gecelik boşluk, belgelenmemiş sapmadır.
    assert r["exit"] < 102.5, "kapanış dolumu slipajı içermeli"

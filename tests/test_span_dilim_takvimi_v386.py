"""test_span_dilim_takvimi_v386.py — `full_detail_graded`'ın span_days'i DİLİM (PENCERE) TAKVİMİDİR,
trade kümesinin KENDİ span'i DEĞİL (TSK-103, 2026-09-03, operatör K6).

NEDEN: `walk_forward`'ın rejimli çağrıda döndürdüğü ikinci defter (`full_detail_graded`,
`test_rejim_tam_pencere_v371`'in konusu) `score_mod.score_detail(graded, goal)`yi span_days VERMEDEN
çağırıyordu — `score_detail` o zaman `_span_days(trades)`e düşer: trade kümesi SEYREKSE (rejim dilimi
doğası gereği seyrektir) yıllıklandırma paydası küçülür ve `realized_30d`/`sharpe`/`trades_per_year`
şişer. `score.score_detail` docstring'i bu SINIFI zaten adlandırıyor: "a 20-day burst inside a
183-day OOS window inflated realized_30d ~9x". Karar (brief D1): span_days = DEĞERLENDİRME
PENCERESİNİN takvim günü — `segment_score`in kullandığı `(seg_end - lo).days` deseniyle AYNI —
`[is_start, holdout_end]` (replay'in TÜM penceresi; `full_detail_graded`in zaten iddia ettiği pencere,
bkz. backtest.py'deki "AYNI pencerenin ([is_start, holdout_end])" yorumu). `is_start` UN-EMBARGOED
kullanılır: `is_d`nin kendi `lo`su da `_embargoed_start(is_start, 0) == is_start`dır (embargo yalnız
OOS alt sınırına uygulanır, `walk_forward` çağrısında).

KAPSAM (D2): YALNIZ `full_detail_graded`. Düz kardeş `full_detail` (`res.detail(goal)`) BİLEREK
ÇIPLAK KALIR — trade-span'e göre yıllıklanmaya devam eder; iki defter AYNI SAYIYI vermez, tüketici
(`analytics._backtest_beklenti_r`) yalnız `avg_r`/`n` okur (span-türevi alanlara dokunmaz).

ÜÇ YÜZEY BU DOSYADA:
  1. Pozitif kontrol — docstring vakasının BİREBİR ölçülmüş hâli: 183 günlük pencerede 20 günlük
     trade demeti, span_days pencere takvimine eşit, realized_30d trade-span hesabına göre ~9x
     ŞİŞMİYOR (numaralar KOŞULARAK ölçülür, tahmin edilmez).
  2. Ayrışma beyanı — backtest.py'deki BEDEL BEYANI madde-3 metni (TSK-103 künyeli) duruyor mu.
  3. Pencere çözülemezse (sınır yok) span_days VERİLMEZ + `obs` bir kez uyarır (sandbox_state ile).
"""
from __future__ import annotations

import datetime as _dt
import re

import pandas as pd
import pytest

from meridian import backtest, config, obs


IS_START = "2024-01-01"
PENCERE_GUN = 183
HOLDOUT_END = (_dt.date.fromisoformat(IS_START) + _dt.timedelta(days=PENCERE_GUN)).isoformat()


def _patlama_islemleri(n=30, regime="chop", r_multiple=1.0, pnl=800.0):
    """`score.score_detail` docstring'indeki vakanın BİREBİR şekli: n işlem 20 GÜNLÜK bir demete
    sıkışır (ilk ts_open gün 0, son ts_close gün 20 — `_span_days` == 20), ama replay penceresi
    (`IS_START`→`HOLDOUT_END`) 183 gün. `regime` tek değer: `_regime_slice` popülasyonu daraltmaz,
    bu dosyanın konusu SPAN'dır, nüfus dilimlenmesi DEĞİL (o zaten `test_rejim_tam_pencere_v371`'in
    konusu — burada tekrarlanmıyor)."""
    d0 = _dt.date.fromisoformat(IS_START)
    out = []
    for i in range(n):
        offset = i % 20                      # 0..19 → 20 ayrı açılış günü, demet genişliği 20 gün
        op = d0 + _dt.timedelta(days=offset)
        cl = op + _dt.timedelta(days=1)
        out.append({"ts_open": op.isoformat(), "ts_close": cl.isoformat(),
                     "regime": regime, "r_multiple": r_multiple, "pnl_dollars": pnl})
    return out


@pytest.fixture
def ince_goal(sandbox_state):
    """`test_rejim_tam_pencere_v371.ince_goal` ile AYNI desen: min_sample=3, 30 işlemlik demet
    kolayca skor üretsin — bu dosyanın konusu span_days'tir, min_sample eşiği DEĞİL."""
    g = dict(config.goal())
    g["min_sample"] = 3
    return g


def _wf_kos(monkeypatch, goal, *, is_start=IS_START, oos_start=IS_START, oos_end=HOLDOUT_END,
           holdout_end=HOLDOUT_END, trades=None, eval_regime="chop"):
    """`walk_forward`ı SENTETİK bir replay üzerinde koşar — emsal: `test_rejim_tam_pencere_v371._wf_kos`.
    `is_start == oos_start` ve `oos_end == holdout_end`: IS/holdout dilimleri boş kalır (yarı-açık
    sınırla), OOS dilimi TÜM pencereyi kaplar — bu testlerin konusu değil, ölçülü bir sadeleştirme."""
    res = backtest.BacktestResult(trades=trades if trades is not None else _patlama_islemleri(),
                                  equity=[], params={}, start=is_start, end=holdout_end)
    monkeypatch.setattr(backtest, "replay", lambda *a, **k: res)
    return backtest.walk_forward({}, {}, pd.DataFrame({"date": []}), goal,
                                 is_start, oos_start, oos_end, holdout_end,
                                 eval_regime=eval_regime)


# =================================================================================================
# YÜZEY 1 — POZİTİF KONTROL: span_days PENCERE TAKVİMİDİR, TRADE KÜMESİNİN KENDİ ARALIĞI DEĞİL
# =================================================================================================
def test_1a_span_days_pencere_takvim_gunudur(ince_goal, monkeypatch):
    """`full_detail_graded["span_days"]` == pencere takvim günü (183, embargo yok → tam sınır).
    ÖLÇÜLEN sınır: `[is_start, holdout_end]` — `is_d`nin kendi (embargosuz) `lo`suyla AYNI alt sınır,
    `hold_d`nin üst sınırıyla AYNI. ±1 tolerans yalnız sınır-tanımı belirsizliğine karşı (BURADA tam
    183 bekleniyor çünkü `HOLDOUT_END` doğrudan `IS_START + 183 gün` olarak KURULDU, tahmin edilmedi)."""
    w = _wf_kos(monkeypatch, ince_goal)

    assert "full_detail_graded" in w
    gd = w["full_detail_graded"]
    assert "span_days" in gd, "full_detail_graded pencere takvimini HİÇ taşımıyor"
    beklenen = (_dt.date.fromisoformat(HOLDOUT_END) - _dt.date.fromisoformat(IS_START)).days
    assert beklenen == PENCERE_GUN, "test fikstürü kendi sabitiyle tutarsız — önce fikstürü düzelt"
    assert gd["span_days"] == pytest.approx(beklenen, abs=1), \
        f"span_days pencere takviminden SAPMIŞ: {gd['span_days']} (beklenen ~{beklenen})"


def test_1b_realized_30d_trade_span_hesabinin_9_kati_SISMIYOR(ince_goal, monkeypatch):
    """score.py docstring vakasının ÖLÇÜLMÜŞ hâli. `full_detail` AYNI trade defterini (bu fikstürde
    `graded == res.trades`, regime tek değer) span_days VERMEDEN puanlar — yani onun `realized_30d`si
    TRADE KÜMESİNİN kendi ~20 günlük aralığından yıllıklanır (bugünkü, DEĞİŞMEYEN full_detail
    davranışı). `full_detail_graded` artık 183 günlük pencereden yıllıklanıyor. Oran SAYIYLA ölçülür,
    tahmin edilmez: pencere trade-kümesinden ~9 KAT GENİŞ olduğundan `full_detail_graded`in
    `realized_30d`si `full_detail`inkinden KÜÇÜK olmalı ve `full_detail_graded / full_detail` oranı
    ~1/9 civarında — yani ~9 KAT ŞİŞMENİN TERSİ. `oran <= 1,2` bunu ÖLÇEREK doğrular: eski
    (span_days verilmeyen) davranışa dönülseydi iki alan EŞİT olur, oran yine <=1.2 olurdu — o yüzden
    ayrıca KESİN KÜÇÜKLÜK de ayrı satırda çivilenir (1c)."""
    w = _wf_kos(monkeypatch, ince_goal)

    gd_r30 = w["full_detail_graded"]["realized_30d"]
    fd_r30 = w["full_detail"]["realized_30d"]
    assert fd_r30 > 0, "fikstür pozitif getiri üretmiyor — oran ölçümü anlamsız kalır"
    oran = gd_r30 / fd_r30
    assert oran <= 1.2, (
        f"full_detail_graded.realized_30d full_detail'e göre şişmiş (oran={oran}); "
        "pencere takvimi yerine trade-span kullanılıyor olabilir")


def test_1c_pencereden_yillliklanan_realized_30d_trade_spanden_KESIN_KUCUKTUR(ince_goal, monkeypatch):
    """1b'nin tek başına yakalayamadığı mutasyonu (span_days GEÇİRİLMEZSE iki alan eşitlenir, oran
    1.0 <= 1.2 olur ve 1b SESSİZCE geçer) burası yakalar: pencere (183g) trade demetinden (20g) GENİŞ
    olduğundan doğru davranışta `full_detail_graded`in `realized_30d`si `full_detail`inkinden KESİN
    küçük olmalı — eşitlik de büyüklük de mutasyonu ele verir."""
    w = _wf_kos(monkeypatch, ince_goal)

    gd_r30 = w["full_detail_graded"]["realized_30d"]
    fd_r30 = w["full_detail"]["realized_30d"]
    assert gd_r30 < fd_r30, (
        f"full_detail_graded.realized_30d ({gd_r30}) full_detail'inkinden ({fd_r30}) KÜÇÜK DEĞİL — "
        "pencere takvimi span_days olarak geçmiyor olabilir")


# =================================================================================================
# YÜZEY 2 — AYRIŞMA BEYANI: full_detail ÇIPLAK KALIR, backtest.py'de KÜNYELİ METİN DURUR
# =================================================================================================
def test_2a_full_detail_span_days_ALANI_TASIMAZ_ciplak_kalir(ince_goal, monkeypatch):
    """D2: düz kardeş `full_detail` bu kararın DIŞINDA — `res.detail(goal)` hâlâ span_days VERMEDEN
    çağrılıyor, yani onun sözlüğünde `span_days` anahtarı HİÇ yoktur (score_detail'in kendisi bu
    alanı asla üretmez — `shadowlaw.money_score_detail` gibi SARMALAYICILAR üretir, `score_detail`in
    KENDİSİ değil; D3 `score_detail`e dokunmayı yasaklıyor)."""
    w = _wf_kos(monkeypatch, ince_goal)

    assert "span_days" not in w["full_detail"], \
        "full_detail span_days taşıyor — D2 kapsamını full_detail'e sızdırdı"


def test_2b_bedel_beyani_madde3_TSK103_kunyeli_ayrisma_cumlesi_durur():
    """METİN ÇİVİSİ (brief: 'beyan cümlesi backtest.py'de künyeli — TSK-103, 2026-09-03'). Bu bir
    davranış testi DEĞİL: madde-3 yorum bloğu SİLİNSE/yeniden yazılsa davranış testleri değişmez ama
    okuyucu (bir sonraki mühendis) ayrışmanın BİLEREK olduğunu kaybeder — YASA 6 (okuyucusuz yazım
    yok) burada 'beyan okunabilir kaldı mı'yı ölçüyor."""
    kaynak = backtest.__file__
    with open(kaynak, encoding="utf-8") as f:
        metin = f.read()

    assert "TSK-103" in metin and "2026-09-03" in metin, \
        "backtest.py'de TSK-103 künyesi yok — bedel beyanı güncellenmemiş"
    # "full_detail_graded" ve "full_detail" ikisinin de aynı sayı OLMADIĞI beyanı metinde ADIYLA
    # duruyor mu (grafik/madde numarası değil, İDDİANIN KENDİSİ).
    assert re.search(r"full_detail.{0,400}(?:AYNI SAYI|aynı sayı).{0,80}(?:DEĞİL|değil)", metin,
                     re.DOTALL) or re.search(
        r"(?:AYNI SAYI|aynı sayı).{0,80}(?:DEĞİL|değil).{0,400}full_detail", metin, re.DOTALL), \
        "backtest.py ayrışma beyanını (iki defter aynı sayı değildir) metinde taşımıyor"


# =================================================================================================
# YÜZEY 3 — PENCERE ÇÖZÜLEMEZSE: span_days VERİLMEZ, obs BİR KEZ UYARIR
# =================================================================================================
def test_3a_bicimsiz_pencere_sinirinda_span_days_VERILMEZ_ve_obs_uyarir(ince_goal, monkeypatch):
    """D1: 'pencere hesaplanamıyorsa (sınır yok) span_days VERİLME (bugünkü davranış) + obs uyarısı
    — uydurma yok.' `holdout_end` biçimsiz bırakılır (`_dt.date.fromisoformat` patlar); `_WARNED`
    süreç-global olduğundan (bkz. `backtest._warn_once`, `test_gate_statistics_v74`'ün deseni) jeton
    ÖNCE düşürülür, aksi hâlde bu dosyanın kendinden önce koşan bir testin uyarıyı harcamış olmasına
    bağlı hâle gelirdi (sıra-bağımlı suite kanıt taşımaz)."""
    backtest._WARNED.discard("full_detail_graded_span_pencere_yok")
    bozuk_holdout = "GECERSIZ-TARIH"

    w = _wf_kos(monkeypatch, ince_goal, holdout_end=bozuk_holdout)

    gd = w["full_detail_graded"]
    assert "span_days" not in gd, \
        "pencere çözülemedi ama span_days yine de yazıldı — uydurma"
    olaylar = obs.recent(limit=50)
    uyarilar = [o for o in olaylar if o.get("event") == "full_detail_graded_span_pencere_yok"]
    assert len(uyarilar) == 1, \
        f"pencere çözülemediğinde tam olarak BİR obs uyarısı bekleniyordu, gelen: {olaylar}"
    assert uyarilar[0]["level"] == "warn"


def test_3b_bicimsiz_pencerede_score_detail_yine_TRADE_SPANE_duser(ince_goal, monkeypatch):
    """`span_days` argüman olarak da VERİLMEZ (yalnız çıktı alanı değil) — `score_detail` kendi
    `_span_days(trades)` yedeğine düşer, yani `full_detail_graded`in `realized_30d`si bu durumda
    `full_detail`inkiyle (AYNI trade defteri, regime tek değer) EŞİT olmalı: ikisi de trade-span'den
    yıllıklanıyor demektir."""
    backtest._WARNED.discard("full_detail_graded_span_pencere_yok")
    bozuk_holdout = "GECERSIZ-TARIH"

    w = _wf_kos(monkeypatch, ince_goal, holdout_end=bozuk_holdout)

    assert w["full_detail_graded"]["realized_30d"] == pytest.approx(w["full_detail"]["realized_30d"])

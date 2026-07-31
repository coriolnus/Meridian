"""v141 — KARANTİNA GENİŞLETMESİ + `bars_integrity` DEFTERİ (hayalet-round-2).

İKİ KUSUR SINIFI, İKİ AYRI ÇÖZÜM — ve bu dosya ikisinin de SINIRINI çiviler.

KUSUR-1 (v138'in kendi kapısındaki kaçak, 2026-07-31'de ÖLÇÜLDÜ): karantina kuralının hacim şartı
VETO gibi davranıyordu. 259 defter / 1.343.892 geçerli-seans satırında:
    (a) |hareket|>%35 .................... 216
    (a&b) sıçra-VE-geri-dön (gerçek sınıf)  13
    (a&b&c) v138'in aldığı ................  3   → sınıfın %77'si KAÇIYORDU
Kaçanlar: GILD/CMCSA 2013-12-18 (×2,10 / ×2,05), DLTR 2012-06-26, UNP 2014-06-06, ALB, AVGO,
DLTR, PINS, TDG… hepsi apaçık ölçek satırı. Sebep: sağlayıcı HAM fiyatı DÜZELTİLMİŞ hacimle
eşleştirince "hacim ters oranlı" imzası YOK ve satır masum görünüyordu.

KUSUR-2: kapıdan geçen 97 kırılma tek-satır hayaleti DEĞİL — bir sembolün geçmişinin BÜTÜN BİR
DÖNEMİ başka ölçekte/kimlikte (CHTR ×1158, AVGO ×162, PINS'in kuruş "geçmişi", GOOGL ×2,6,
RTX ×3,8, ABT/DD/HON spinoff'ları, TDG'nin bozuk kesiti). Çözüm SİLMEK DEĞİL DAMGALAMAK:
`state/bars_integrity.json` + ölçüm yollarında okuyucusu (YASA 6).

Bu dosyanın çivilediği yasalar:
  1. YENİ KURAL SINIFI YAKALAR — ve kaçağın ESKİ kuralla kaçtığı da AYNI testte ölçülür
     (yalnız "yeşil" olmak, dedektörün körlüğüyle de açıklanabilirdi).
  2. HACİM ARTIK ZAYIFLATICI — fiyat kanıtı TAM iken hacim veto edemez; kanıt ZAYIF iken hacim
     hâlâ gerekir (iki kademe de ayrı ayrı ölçülür).
  3. MASUM KORUNUR — kalıcı ölçek dikişi ve meşru şok DOKUNULMAZ (round-1'in kitlesel-red dersi).
  4. DEFTER OLGUYU SÖYLER, POLİTİKAYI DEĞİL — kırılma listesi + güvenli_baslangic; ısınma payı
     tüketicinin işi.
  5. GERÇEK PİYASA OLAYI DAMGALANMAZ — AIG 2008, OXY/TRGP 2020-03-09 sınıfı korunur.
  6. DEFTERİN TÜKETİCİSİ VAR — `component_ic` ve `cf_backfill` güvensiz dönemi DEFTERDEN öğrenir.
  7. YAZIM SANCTIONED YOLDAN — defter ölçüm evrenini değiştirir, wf-revizyonu bumplanır.
"""
from __future__ import annotations

import json

import pandas as pd
import pytest

from meridian import barrepair, config, store
from meridian.adapters import data


@pytest.fixture(autouse=True)
def _sandbox(sandbox_state, monkeypatch):
    monkeypatch.setattr(config, "BARS", sandbox_state / "bars")
    for d in (data._GHOST, data._CAL_MISMATCH, data._INTEGRITY_APPLIED):
        d.clear()
    for s in (data._GHOST_EVENTED, data._QUAR_EVENTED, data._CAL_MISMATCH_WARNED,
              data._BAR_WARNED, data._INTEGRITY_WARNED):
        s.clear()
    monkeypatch.setattr(data, "_GHOST_EMITTED", 0)
    monkeypatch.setattr(data.time, "sleep", lambda *_: None)
    yield
    for d in (data._GHOST, data._CAL_MISMATCH, data._INTEGRITY_APPLIED):
        d.clear()


def _sessions(start: str, end: str) -> list[str]:
    return sorted(d for d in data._sessions() if start <= d <= end)


def _frame(rows) -> pd.DataFrame:
    return pd.DataFrame([{"date": pd.Timestamp(d), "open": o, "high": h, "low": lo,
                          "close": c, "volume": v} for d, o, h, lo, c, v in rows])


def _flat(dates, close=100.0, vol=1_000_000.0) -> pd.DataFrame:
    return _frame([(d, close, close * 1.01, close * 0.99, close, vol) for d in dates])


def _events(event: str) -> list[dict]:
    p = config.STATE / "events.jsonl"
    if not p.exists():
        return []
    out = []
    for line in p.read_text().splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("event") == event:
            out.append(r)
    return out


def _old_rule(df: pd.DataFrame) -> pd.Series:
    """v138'in KURALININ AYNISI — kaçağın gerçekten kaçtığını ölçmek için (iddia değil, ölçüm).

    Kopya olması BİLEREK: bu satırlar artık üretimde YOK ve testin işi 'yeni kural eskisinden
    ne kadar farklı' sorusunu SAYIYLA cevaplamak. Üretim kuralı değişince bu kopya değişmez —
    zaten değişmemeli, çünkü ölçülen şey ESKİ davranıştır."""
    c = pd.to_numeric(df["close"], errors="coerce")
    v = pd.to_numeric(df["volume"], errors="coerce")
    r = c / c.shift(1).where(c.shift(1) > 0)
    back = c.shift(-1) / c.where(c > 0)
    spike = (r - 1.0).abs() > data.SPLIT_SUSPECT_RET
    revert = (r * back - 1.0).abs() < data.UNADJ_REVERT_TOL
    zero_vol = v.fillna(-1) == 0
    recip = ((r * (v / v.shift(1).where(v.shift(1) > 0))) - 1.0).abs() < data.UNADJ_VOLUME_TOL
    return (spike & revert & (zero_vol | recip)).fillna(False)


def _spike_book(dates, base, mult, vol_mult, close=100.0, vol=5_000_000.0, at=40):
    """`at` indeksinde ×mult ölçek satırı, ertesi bar geri döner. Hacim `vol_mult` katına çıkar."""
    df = _flat(dates, close=close, vol=vol)
    i = at
    df.loc[i, ["open", "high", "low", "close"]] = [close * mult * k for k in (1.0, 1.01, 0.99, base)]
    df.loc[i, "volume"] = vol * vol_mult
    return df


# ============================================================ 1. KURAL SINIFI YAKALIYOR
def test_the_2013_12_18_class_escaped_the_old_rule_and_is_now_caught():
    """CANLI KAÇAĞIN KENDİSİ (GILD/CMCSA 2013-12-18 sınıfı): fiyat ×2,05, ertesi gün geri döner,
    hacim TERS ORANLI DEĞİL (×0,84 — sağlayıcı ham fiyatı düzeltilmiş hacimle eşleştirmiş).
    v138'in kuralı bu satırı MASUM sayıyordu; yeni kural fiyat kanıtına bakıp yakalar.

    İKİ HÜKÜM BİR ARADA: eski kuralın kaçırdığı AYNI testte ölçülür — yoksa bu yeşil, kaçağın
    hiç var olmamasıyla da açıklanabilirdi."""
    dates = _sessions("2013-11-01", "2014-01-31")
    df = _spike_book(dates, base=2.05, mult=2.05, vol_mult=0.84)
    assert int(_old_rule(df).sum()) == 0                  # ESKİ kural: kaçıyor (ölçüldü)
    clean, rep = data.sanitize_bars(df, "GILD")
    assert rep["unadjusted_quarantined"] == 1             # YENİ kural: yakalıyor
    assert float(clean["close"].max()) < 110.0
    assert len(clean) == len(dates) - 1


def test_a_thin_dollar_volume_bar_is_caught_even_without_a_volume_signature():
    """AVGO 2008-06-12 sınıfı: fiyat ×2, hacim de ×2 (ters oran YOK) ama barın DOLAR HACMİ 1.180$ —
    bu evrenin hiçbir gerçek seansı o hacimle işlem görmez. Hacim şartı artık 'ters oranlı olsun'
    demiyor, 'bu hareketi DOĞRULAMIYOR' diyor; doğrulamamanın bir hâli de yok denecek likiditedir."""
    dates = _sessions("2008-05-01", "2008-07-31")
    df = _flat(dates, close=1.0, vol=600.0)               # dolar hacmi ~600$
    i = 25
    df.loc[i, ["open", "high", "low", "close"]] = [2.0, 2.02, 1.98, 2.0]
    df.loc[i, "volume"] = 1180.0
    assert int(_old_rule(df).sum()) == 0
    clean, rep = data.sanitize_bars(df, "AVGO")
    assert rep["unadjusted_quarantined"] == 1


def test_volume_is_a_weakener_not_a_veto_measured_on_both_tiers():
    """KURALIN KALBİ — hacim iki kademede FARKLI davranır ve ikisi de burada ölçülür.

    KADEME 1 (geri dönüş TAM, |r·back−1| < %5): hacim PATLASA bile satır düşer. Fiyatın kendisi
      hükümdür; ölçüldü ki bu bandın en yakın masum komşusu 0,1250 (2,6 kat pay).
    KADEME 2 (geri dönüş yaklaşık, %5–%10): fiyat kanıtı TAM değil → hacim DESTEK vermek zorunda.
      Hacim patladıysa (gerçek hareketin imzası) satır KORUNUR; patlamadıysa düşer.
    Bu iki satır olmadan 'veto değil zayıflatıcı' bir slogan olurdu."""
    dates = _sessions("2015-01-01", "2015-04-30")
    # KADEME 1: tam geri dönüş + hacim PATLIYOR (×9) → yine de karantina
    tam = _spike_book(dates, base=2.0, mult=2.0, vol_mult=9.0)
    assert data.sanitize_bars(tam, "T1")[1].get("unadjusted_quarantined") == 1
    # KADEME 2: geri dönüş %7 eksik + hacim PATLIYOR → korunur (gerçek hareket olabilir)
    zayif_patlayan = _spike_book(dates, base=2.0, mult=2.0, vol_mult=9.0)
    zayif_patlayan.loc[41, ["open", "high", "low", "close"]] = [107.0, 108.0, 106.0, 107.0]
    r1 = data.sanitize_bars(zayif_patlayan, "T2")[1]
    assert "unadjusted_quarantined" not in r1
    # KADEME 2: AYNI fiyat imzası + hacim PATLAMIYOR (×0,6) → düşer
    zayif_sessiz = _spike_book(dates, base=2.0, mult=2.0, vol_mult=0.6)
    zayif_sessiz.loc[41, ["open", "high", "low", "close"]] = [107.0, 108.0, 106.0, 107.0]
    assert data.sanitize_bars(zayif_sessiz, "T3")[1].get("unadjusted_quarantined") == 1


# ============================================================ 2. MASUM KORUNUYOR
def test_the_2006_scale_seam_survives_even_with_the_inverse_volume_signature():
    """YANLIŞ-POZİTİF KİLİDİ (round-1 dersi): 2006-01-03 kümesinde 43 sembolde fiyat ×0,5 + hacim ×2
    var — yani ESKİ kuralın (c) imzasını TAM taşıyor. Onları kurtaran şey hacim değil GERİ-DÖNMEME:
    yeni ölçek KALICIDIR. Hacim şartı gevşediğine göre bu kilidi ayrıca ölçmek zorunludur."""
    dates = _sessions("2006-01-03", "2006-03-31")
    kapanis = [200.0] * 10 + [100.0] * (len(dates) - 10)          # yeni ölçek KALICI
    hacim = [1_000_000.0] * 10 + [2_000_000.0] * (len(dates) - 10)  # ters oranlı (eski (c) imzası)
    df = _frame([(d, c, c * 1.01, c * 0.99, c, v) for d, c, v in zip(dates, kapanis, hacim)])
    clean, rep = data.sanitize_bars(df, "SEAM")
    assert "unadjusted_quarantined" not in rep and len(clean) == len(dates)


def test_a_legitimate_shock_that_partly_retraces_survives():
    """Meşru %60'lık kazanç şoku, ertesi gün %20 geri veriyor (|r·back−1| = 0,28) ve hacim patlıyor.
    Geri-dönüş şartı bu satıra HİÇ bakmaz — kural üç kademede de onu görmez. Gerçek hareketlerin
    kısmen geri verdiği bu bant, kuralın en çok yanlış-pozitif üretebileceği yerdir."""
    dates = _sessions("2024-02-01", "2024-05-31")
    df = _flat(dates, close=100.0, vol=5_000_000.0)
    i = 30
    df.loc[i, ["open", "high", "low", "close"]] = [150.0, 165.0, 148.0, 160.0]
    df.loc[i, "volume"] = 40_000_000.0
    for j in range(i + 1, len(df)):
        df.loc[j, ["open", "high", "low", "close"]] = [128.0] * 4
    clean, rep = data.sanitize_bars(df, "NVDA")
    assert "unadjusted_quarantined" not in rep and len(clean) == len(dates)


# ============================================================ 3. KIRILMA SINIFLANDIRMASI
def _seam_book(dates, mult, at=40, close=100.0, vol=5_000_000.0, open_mult=None, hl=1.01):
    """`at` indeksinden İTİBAREN KALICI ×mult ölçek. `open_mult` verilirse açılış AYRI kayar."""
    rows = []
    for k, d in enumerate(dates):
        c = close * (mult if k >= at else 1.0)
        o = c if k != at else close * (open_mult if open_mult else mult)
        rows.append((d, o, max(c, o) * hl, min(c, o) / hl, c, vol))
    return _frame(rows)


def test_a_permanent_rescale_is_recorded_as_a_scale_seam():
    """K1: fiyat ×2,6 (GOOGL 2013-12-18 sınıfı), geri dönmüyor, AÇILIŞ da aynı oranda kaymış ve
    seansın kendi high/low aralığı NORMAL → bu bir seans hareketi değil, bir YENİDEN ÖLÇEKLEMEdir.
    Satır SİLİNMEZ (yeni ölçeğin ilk barıdır); ÖNCESİ damgalanır."""
    dates = _sessions("2013-06-01", "2014-06-30")
    df = _seam_book(dates, mult=2.6, at=100)
    brk = data.integrity_breaks(df)
    assert [b["sinif"] for b in brk] == ["olcek_dikisi"] and brk[0]["kural"] == "K1"
    assert brk[0]["tarih"] == dates[100] and brk[0]["oran"] == pytest.approx(2.6, abs=0.01)
    ss, _ = data.integrity_safe_start(df)
    assert ss == dates[101]                              # kırılmadan SONRAKİ ilk bar


def test_a_real_crash_day_is_NOT_recorded_as_a_break():
    """K1'İN YANLIŞ-POZİTİF KİLİDİ (bu dosyanın en pahalı testi): OXY/TRGP 2020-03-09 ve AIG 2008
    sınıfı — fiyat yarıya iner, GERİ DÖNMEZ, ama bu GERÇEK bir seanstır. İmzası farklıdır: açılış
    kapanışla AYNI oranda kaymaz (gün İÇİNDE düşülmüştür) ve seansın high/low aralığı geniştir.
    Bu ayrım olmasaydı defter, OXY'nin 2020 öncesi 16 yılını 'güvensiz' damgalardı."""
    dates = _sessions("2019-10-01", "2020-06-30")
    at = 100
    rows = []
    for k, d in enumerate(dates):
        c = 100.0 * (0.47 if k >= at else 1.0)
        if k == at:
            rows.append((d, 78.0, 80.0, 45.0, 47.0, 90_000_000.0))   # açılış −%22, kapanış −%53
        else:
            rows.append((d, c, c * 1.01, c * 0.99, c, 9_000_000.0))
    df = _frame(rows)
    assert data.integrity_breaks(df) == []
    assert data.integrity_safe_start(df) == (None, [])


def test_an_isolated_bad_print_does_not_black_out_two_decades():
    """K2 KÜMELENME ŞARTI — ÖLÇÜLMÜŞ: yerel geçmişte high/low>3 olan 15 bar var; 9'u TDG'nin bozuk
    kesitinde, 6'sı TEK başına ve üçü GERÇEK kriz seansı (UAL 2008-09-08, AIG/CEG 2008-09-16).
    Tekil barı damgalayan bir kural VZ'nin 22 yıllık geçmişini tek bir hatalı `low` alanı yüzünden
    çöpe atardı (ölçüldü: 5.540 bar)."""
    dates = _sessions("2020-01-01", "2026-06-30")
    df = _flat(dates, close=100.0, vol=5_000_000.0)
    df.loc[500, ["high", "low"]] = [300.0, 20.0]          # tek bozuk print (hl=15)
    assert data.integrity_corrupt_bars(df) == [dates[500]]     # OLGU görülüyor
    assert data.integrity_breaks(df) == []                     # …ama HÜKÜM verilmiyor
    assert data.integrity_safe_start(df)[0] is None


def test_a_run_of_corrupt_bars_is_a_broken_section():
    """K2: TDG 2011-11 → 2012-01 sınıfı — 63 seanslık pencerede 3+ bozuk bar. Kesit bozuktur ve
    öncesi güvenilmez; damga bu kez verilir."""
    dates = _sessions("2011-06-01", "2012-12-31")
    df = _flat(dates, close=100.0, vol=5_000_000.0)
    for i in (100, 108, 115):
        df.loc[i, ["high", "low"]] = [400.0, 25.0]
    brk = data.integrity_breaks(df)
    assert [b["sinif"] for b in brk] == ["bozuk_kesit"] and brk[0]["kanit"]["bozuk_bar"] == 3
    ss, _ = data.integrity_safe_start(df)
    assert ss > dates[115]


def test_a_phantom_penny_history_is_marked_but_a_small_real_one_is_not():
    """K3: PINS 2013-2018 sınıfı — sembolün "geçmişi" günde 200-5000 dolarlık barlardan ibaret;
    Pinterest 2019'da halka açıldı. EŞİK ÖLÇÜLDÜ: hayalet dönemler 0$–58.000$, evrenin GERÇEK en
    ince dönemleri 329.448$ (MPWR 2005) ve üstü — 100.000$ ikisinin arasında, iki yana ~3,3 kat pay.
    İkinci satır o payı çiviler: gerçekten küçük ama GERÇEK bir dönem damgalanmaz."""
    dates = _sessions("2013-01-01", "2020-12-31")
    hayalet = _frame([(d, 1.0, 1.0, 1.0, 1.0, 3000.0 if k < 800 else 5_000_000.0)
                      for k, d in enumerate(dates)])       # 3.000$/gün → 5.000.000$/gün
    brk = data.integrity_breaks(hayalet)
    assert any(b["sinif"] == "hayalet_gecmis" for b in brk)
    gercek = _frame([(d, 1.0, 1.0, 1.0, 1.0, 500_000.0 if k < 800 else 5_000_000.0)
                     for k, d in enumerate(dates)])        # 500.000$/gün — küçük ama GERÇEK
    assert [b for b in data.integrity_breaks(gercek) if b["sinif"] == "hayalet_gecmis"] == []


def test_safe_start_follows_the_LAST_break_not_the_first():
    """İki dikiş arasındaki ada da güvensizdir (2006-01-03'te ×0,5 + 2006-10-24'te ×2 olan 11
    sembolde tam olarak böyle 10 aylık yanlış-ölçekli bir ada var). Defter en SON dikişten
    öncesini toptan güvensiz sayar — o adayı ayrıca aramaktan hem basit hem muhafazakâr."""
    dates = _sessions("2006-01-03", "2007-06-30")
    kapanis = [100.0] * 20 + [50.0] * 180 + [100.0] * (len(dates) - 200)
    df = _frame([(d, c, c * 1.01, c * 0.99, c, 5_000_000.0) for d, c in zip(dates, kapanis)])
    ss, brk = data.integrity_safe_start(df)
    assert [b["tarih"] for b in brk] == [dates[20], dates[200]]     # iki dikiş, arada 180 seans
    assert ss == dates[201]                                        # hüküm SONUNCUYA göre


# ============================================================ 4. DEFTER + TÜKETİCİ (YASA 6)
def _seed_ledger(ticker: str, safe: str, breaks=None) -> None:
    store.write_json(data.INTEGRITY_FILE, {"rev": 1, "semboller": {
        ticker: {"guvenli_baslangic": safe, "kirilma_listesi": breaks or [
            {"tarih": safe, "oran": 2.0, "sinif": "olcek_dikisi", "kural": "K1", "kanit": {}}],
            "tespit_kurali": "K1", "dislanan_bar": 0}}})


def test_the_ledger_excludes_the_unsafe_period_and_says_so():
    """TÜKETİCİ KABLOSU: `measurement_bars` güvensiz dönemi DÜŞÜRÜR — barın içinden değil DEFTERDEN
    öğrenerek (ölçüm fonksiyonu bütünlük kuralını ikinci kez yazmaz). Ve SESSİZ DEĞİLDİR: sayaç
    `integrity_report()`ta birikir, sembol başına bir olay yazılır."""
    dates = _sessions("2010-01-01", "2012-12-31")
    _seed_ledger("CHTR", dates[100])
    df = _flat(dates)
    out = data.measurement_bars(df, "CHTR")
    assert len(out) == len(dates) - 100
    assert str(out["date"].iloc[0])[:10] == dates[100]
    rep = data.integrity_report()
    assert rep["rows_excluded"] == 100 and rep["applied"]["CHTR"] == 100
    ev = _events("bars_integrity_period_excluded")
    assert len(ev) == 1 and ev[0]["ticker"] == "CHTR" and ev[0]["rows"] == 100


def test_a_missing_ledger_fails_open():
    """Defter YOKSA hiçbir şey dışlanmaz. Bir bütünlük defterinin yokluğu, tüm ölçüm evrenini
    susturmak için gerekçe değildir (takvim kapısının fail-open gerekçesinin aynısı)."""
    dates = _sessions("2020-01-01", "2020-06-30")
    df = _flat(dates)
    assert data.bars_integrity() == {} and data.safe_start("CHTR") is None
    assert len(data.measurement_bars(df, "CHTR")) == len(dates)
    assert data.integrity_report()["rows_excluded"] == 0


def test_component_ic_and_cf_backfill_read_the_ledger(monkeypatch):
    """YASA 6 — DEFTERİN TÜKETİCİSİ AYNI TURDA: `component_ic` ve `cf_backfill`, bar evrenlerini
    kurarken güvensiz dönemi DIŞLAR. Kaynak dizgisi DEĞİL DAVRANIŞ ölçülür: aynı CSV, defterli ve
    deftersiz iki koşumda FARKLI ilk tarih verir."""
    from meridian import cf_backfill, component_ic
    dates = _sessions("2014-01-01", "2016-12-31")
    for t in ("CHTR", "SPY"):
        data._write_bars(_flat(dates), data._cache_path(t))
    monkeypatch.setattr(data, "REPLAY_UNIVERSE", ["CHTR"])
    monkeypatch.setattr(data, "INDEX_SYMBOL", "SPY")
    once = component_ic._load_universe()
    assert str(once["CHTR"].index[0])[:10] == dates[0]
    _seed_ledger("CHTR", dates[300])
    data._INTEGRITY_APPLIED.clear()
    sonra = component_ic._load_universe()
    assert str(sonra["CHTR"].index[0])[:10] == dates[300]
    assert data.integrity_report()["rows_excluded"] == 300
    # SAYAÇ TÜKETİLİR: damga `component_ic.json`in İÇİNE girer — "bu tablo hangi bar tabanından
    # üretildi?" sorusu artefaktın kendisinden cevaplanır, tahminle değil (YASA 6).
    damga = component_ic._bars_taban()
    assert damga["rows_excluded"] == 300 and damga["applied"]["CHTR"] == 300
    assert damga["ledger_symbols"] == 1 and damga["file"] == data.INTEGRITY_FILE
    # cf_backfill AYNI defteri okur ve AYNI damgayı basar (tek yasa, iki tüketici)
    import meridian.cf_backfill as cfb
    src = __import__("inspect").getsource(cfb.run)
    assert "measurement_bars" in src and "integrity_report()" in src


# ============================================================ 5. TARAMA ARACI
def _seed_broken_book(ticker: str = "CHTR") -> list[str]:
    dates = _sessions("2009-01-01", "2012-12-31")
    df = _seam_book(dates, mult=1158.0, at=200)
    data._write_bars(df, data._cache_path(ticker))
    return dates


def test_integrity_scan_is_a_dry_run_by_default():
    """KURU KOŞU VARSAYILANDIR (barrepair'in 1. kuralı, yeni moda da geçerli): tarama defter YAZMAZ."""
    dates = _seed_broken_book()
    rapor = barrepair.integrity_scan()
    assert rapor["sembol_sayisi"] == 1 and rapor["kirilma_sayisi"] >= 1
    assert rapor["semboller"]["CHTR"]["guvenli_baslangic"] == dates[201]
    assert not (config.STATE / data.INTEGRITY_FILE).exists()
    assert barrepair.main(["--integrity-tara"]) == 0
    assert not (config.STATE / data.INTEGRITY_FILE).exists()


def test_integrity_apply_writes_through_the_sanctioned_path():
    """YAZIM SANCTIONED YOLDAN: defter ölçüm evrenini daraltır → önbelleklenmiş walk-forward'lar
    artık BAŞKA bir bar kümesine aittir. Revizyon bumplanmazsa 'sonuç değişti, revizyon sabit'
    olurdu — `barrepair --uygula`nın satır silerken kaçındığı hatanın aynısı."""
    _seed_broken_book()
    rev0 = int(store.read_json("wf_cache_rev.json", {}).get("rev", 0))
    kayit = barrepair.integrity_apply(barrepair.integrity_scan())
    diskte = json.loads((config.STATE / data.INTEGRITY_FILE).read_text())
    assert diskte["semboller"]["CHTR"]["tespit_kurali"] == "K1"
    assert diskte["uretildi"] and kayit["kirilma_sayisi"] >= 1
    assert int(store.read_json("wf_cache_rev.json", {}).get("rev", 0)) > rev0
    assert data.safe_start("CHTR") == diskte["semboller"]["CHTR"]["guvenli_baslangic"]
    assert _events("bars_integrity_written")


def test_a_partial_scan_may_not_overwrite_the_ledger():
    """`--sembol` ile üretilen envanter, TARANMAYAN sembollerin damgasını SİLMİŞ bir defter yazardı
    ve defterin tüketicisi o eksikliği göremezdi (sessizce daha az dışlama = sessizce kirli tablo)."""
    _seed_broken_book()
    assert barrepair.main(["--integrity-tara", "--sembol", "CHTR", "--uygula", "--zorla"]) == 2
    assert not (config.STATE / data.INTEGRITY_FILE).exists()


def test_the_scan_publishes_what_it_REFUSED_to_mark():
    """AFFEDİLEN BULGU DA GÖRÜNÜR: kuralın 'gerçek piyasa olayı' deyip damgalamadığı büyük kalıcı
    adımlar ve tekil bozuk barlar elle-denetim listesine düşer. Yalnız damgalananları basmak,
    kuralın kaçırdıklarını görünmez yapardı (üretilip tüketilmeyen kanıt yasağının aynası)."""
    dates = _sessions("2019-10-01", "2020-06-30")
    rows = []
    for k, d in enumerate(dates):
        c = 100.0 * (0.47 if k >= 100 else 1.0)
        rows.append((d, 78.0, 80.0, 45.0, 47.0, 9e7) if k == 100
                    else (d, c, c * 1.01, c * 0.99, c, 9e6))
    data._write_bars(_frame(rows), data._cache_path("OXY"))
    rapor = barrepair.integrity_scan()
    assert rapor["semboller"] == {}
    fp = rapor["yanlis_pozitif_adaylari"]
    assert len(fp) == 1 and fp[0]["ticker"] == "OXY" and fp[0]["tarih"] == dates[100]


def test_the_ledger_is_not_a_sink_in_the_artifact_graph():
    """YASA 6'NIN KENDİ DEDEKTÖRÜYLE ÖLÇÜMÜ: `bars_integrity.json` yazılıyor VE BAŞKA bir modül
    tarafından okunuyor. `codelaw.artifact_graph` okuyucuyu ancak `store` çağrısından tanır — bu
    yüzden `data.bars_integrity()` ham `open()` değil `store.read_json` kullanır. Defter DECLARED_SINKS
    muafiyetine YAZILMAMALI: gerçek dış okuyucusu olan bir muafiyet `stale_sinks` ihlalidir."""
    from meridian import codelaw
    g = codelaw.artifact_graph()
    a = g["artifacts"][data.INTEGRITY_FILE]
    assert a["writers"] == ["barrepair.py"] and "data.py" in a["external_readers"]
    assert a["unread"] is False
    assert data.INTEGRITY_FILE not in codelaw.DECLARED_SINKS
    assert data.INTEGRITY_FILE not in g["violations"] and g["stale_sinks"] == []


def test_a_ghost_row_cannot_manufacture_a_break():
    """SIRA KAPININ SIRASIDIR — ve bu YEREL BİR OLGUYLA doğrulanır: 2026-07-31 itibarıyla yerel SPY
    defterinde 2 hayalet satır DURUYOR (2018-11-22 düz bar, 2025-05-26 yakın kopya; A1'de onarıldı,
    yerel kopya bayat). Envanter takvim+karantina kapılarından SONRA ölçmezse, silinecek bir satır
    KALICI bir damgaya dönüşür ve sembolün tüm geçmişi boşuna güvensiz sayılırdı."""
    dates = _sessions("2025-05-01", "2025-05-23")
    df = pd.concat([_flat(dates, close=100.0, vol=5_000_000.0),
                    _frame([("2025-05-26", 250.0, 252.0, 248.0, 250.0, 5_000_000.0)])],
                   ignore_index=True).sort_values("date").reset_index(drop=True)
    assert data.integrity_breaks(df)                       # ham çerçevede kırılma GÖRÜNÜR
    data._write_bars(df, data._cache_path("SPY"))
    rapor = barrepair.integrity_scan(["SPY"])
    assert rapor["semboller"] == {} and rapor["yanlis_pozitif_adaylari"] == []


def test_the_scan_is_deterministic():
    """Aynı defterler, aynı envanter — bayt bayt. Kararsız bir bütünlük taraması, ölçtüğü
    kararsızlığın kendisi olurdu."""
    _seed_broken_book()
    a = barrepair.integrity_scan()
    b = barrepair.integrity_scan()
    assert json.dumps(a, sort_keys=True, default=str) == json.dumps(b, sort_keys=True, default=str)


def test_the_row_repair_mode_still_works_and_is_untouched():
    """İKİ MOD AYRI: `--integrity-tara` satır SİLMEZ, `--uygula` (onarım) defter YAZMAZ. Aynı araçta
    yaşayan iki eylemin birbirinin yan etkisini üretmediği ayrıca çivilenir."""
    dates = _sessions("2025-05-01", "2025-05-23")
    df = pd.concat([_flat(dates), _flat(["2025-05-26"])], ignore_index=True)
    data._write_bars(df.sort_values("date").reset_index(drop=True), data._cache_path("TST"))
    tara = barrepair.integrity_scan()
    assert len(pd.read_csv(data._cache_path("TST"))) == len(dates) + 1     # satır SİLİNMEDİ
    assert tara["semboller"] == {}
    onar = barrepair.repair(apply=True)
    assert onar["ghost_rows"] == 1
    assert not (config.STATE / data.INTEGRITY_FILE).exists()               # defter YAZILMADI

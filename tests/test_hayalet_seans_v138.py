"""v138 — HAYALET SEANS KAPISI + DÜZELTİLMEMİŞ SATIR KARANTİNASI + ONARIM ARACI.

ÖLÇÜLMÜŞ KÖK NEDEN (2026-07-30, yerel `state/bars` taraması — 259 defter / 1.344.334 satır):
piyasanın KAPALI olduğu iki tarih, bar defterlerinde gerçek bir seans satırı gibi duruyordu.
  2025-05-26 (Memorial Day) → 258 defter: 199 birebir kopya, 52 yakın kopya, 7 ham (düzeltilmemiş)
                              fiyat — BKNG ×25, ORLY ×15, KLAC ×10, NFLX ×10, NOW ×5, HON ×0,5, DD ×0,333
  2018-11-22 (Thanksgiving) → 184 defter: 169 düz bar (hacim 0), 15 ham fiyat
Üç savunma da geçirdi ve her biri kendi işini DOĞRU yapıyordu: `sanitize_bars` yalnız AYNI tarihi
tekilleştiriyordu, `validate_bars` split_suspect'i SOFT sayıyordu (ok=True), dikiş defteri tek
satırlık hayaleti tanımıyordu. Kimse "bu tarih seans mı?" diye SORMUYORDU.

Bu dosya beş yasayı çiviler:
  1. TAKVİM KAPISI  — seans olmayan tarihin satırı DÜŞER ve `bar_ghost_session_dropped` ile SAYILIR.
                      Kapı `sanitize_bars`tadır: her kaynak bacağı, onarım geçidi ve disk OKUMA
                      yolu oradan geçer (tek boğaz).
  2. KARANTİNA      — geçerli seansta duran İZOLE düzeltilmemiş satır (sıçra-ve-geri-dön + hacim
                      tutarsızlığı) da düşer; split_suspect artık her vakada "soft" değildir.
  3. YANLIŞ-POZİTİF — GERÇEK ölçek dikişi (yeni ölçek KALICI, geri dönmez) ve meşru büyük hareket
                      DOKUNULMAZ. Geri-dönüş şartı olmasa kural 38 masum satırı vururdu (ölçüldü).
  4. KİTLESEL RED   — bir serinin büyük kısmı takvim-dışıysa kapı SİLMEZ, REDDEDER ve söyler
                      (`bar_calendar_mismatch`). Amputasyon onarım değildir.
  5. SANCTIONED YOL — onarım aracı satır silince wf-revizyonu bumplanır; `watchdog.determinism_report`
                      küçülmeyi "SESSİZ BAR MUTASYONU" saymaz.
"""
from __future__ import annotations

import json

import pandas as pd
import pytest

from meridian import config, store, watchdog
from meridian.adapters import data

# GERÇEK takvim gerçekleri (XNYS) — testin dayanağı uydurma değil, olgudur:
GHOST_2025 = "2025-05-26"          # Memorial Day — piyasa KAPALI
GHOST_2018 = "2018-11-22"          # Thanksgiving — piyasa KAPALI
BEFORE_2025, AFTER_2025 = "2025-05-23", "2025-05-27"


@pytest.fixture(autouse=True)
def _sandbox(sandbox_state, monkeypatch):
    """Her test kum havuzunda + SÜREÇ-İÇİ sayaçlar sıfırlanmış koşar.

    Sayaçlar modül düzeyindedir ve olaylar 'tarih başına BİR kez' atılır — sıfırlanmazsa ikinci
    test kendi olayını göremez ve suite SIRA BAĞIMLI olur (bu deponun conftest'inde belgeli ders)."""
    monkeypatch.setattr(config, "BARS", sandbox_state / "bars")
    for d in (data._GHOST, data._CAL_MISMATCH):
        d.clear()
    for s in (data._GHOST_EVENTED, data._QUAR_EVENTED, data._CAL_MISMATCH_WARNED, data._BAR_WARNED):
        s.clear()
    # SAYAÇ DA GLOBALDİR (2026-07-30, TAM SUITE bulgusu — tekil koşuda görünmezdi): tur-sonu özeti
    # yalnız TOPLAM BÜYÜDÜĞÜNDE atılır. Suite içinde daha önce koşan bir test canlı/sandbox bir
    # defterden hayalet satır düşürdüyse `_GHOST_EMITTED` zaten yüksekti ve bu dosyanın özet testi
    # HİÇ olay göremiyordu. Sözlükleri sıfırlayıp sayacı unutmak, sıra bağımlılığını kapatmak yerine
    # yerini değiştirmekti — dosyanın kendi fikstür gerekçesinin ihlali.
    monkeypatch.setattr(data, "_GHOST_EMITTED", 0)
    monkeypatch.setattr(data.time, "sleep", lambda *_: None)
    yield
    for d in (data._GHOST, data._CAL_MISMATCH):
        d.clear()
    for s in (data._GHOST_EVENTED, data._QUAR_EVENTED, data._CAL_MISMATCH_WARNED, data._BAR_WARNED):
        s.clear()


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


def _sessions(start: str, end: str) -> list[str]:
    """ÜRETİM takviminden gerçek seanslar — testin kendi takvim uygulamasını yazması, ölçtüğü
    yasanın ikinci bir kopyasını üretmek olurdu (bu depoda tekrar eden hata sınıfı)."""
    return sorted(d for d in data._sessions() if start <= d <= end)


def _frame(rows: list[tuple]) -> pd.DataFrame:
    return pd.DataFrame([{"date": pd.Timestamp(d), "open": o, "high": h, "low": lo,
                          "close": c, "volume": v} for d, o, h, lo, c, v in rows])


def _flat(dates, close=100.0, vol=1_000_000.0) -> pd.DataFrame:
    return _frame([(d, close, close * 1.01, close * 0.99, close, vol) for d in dates])


# ------------------------------------------------------------------ 1. TAKVİM KAPISI
def test_ghost_session_row_is_dropped_and_counted():
    """Memorial Day satırı DÜŞER, rapora SAYI olarak girer ve olay defterine ADIYLA yazılır."""
    dates = _sessions("2025-05-01", "2025-05-30")
    assert GHOST_2025 not in dates                      # önce takvim gerçeğini çivile
    df = _flat(dates + [GHOST_2025])
    clean, rep = data.sanitize_bars(df, "TST")
    assert GHOST_2025 not in set(clean["date"].astype(str).str.slice(0, 10))
    assert rep["ghost_session_dropped"] == 1
    assert len(clean) == len(dates)
    ev = _events("bar_ghost_session_dropped")
    assert len(ev) == 1 and ev[0]["ticker"] == "TST" and GHOST_2025 in ev[0]["dates"]


def test_thanksgiving_flat_bar_is_a_ghost_too():
    """2018-11-22 sınıfı: OHLC eşit, hacim 0, kapanış öncekiyle AYNI. Zararsız GÖRÜNÜR — ama olmayan
    bir seans günü, getirilere sahte bir sıfır-getiri günü ve pencerelere sahte bir bar ekler."""
    dates = _sessions("2018-11-01", "2018-11-30")
    assert GHOST_2018 not in dates
    df = _flat(dates)
    df = pd.concat([df, _frame([(GHOST_2018, 100.0, 100.0, 100.0, 100.0, 0.0)])], ignore_index=True)
    clean, rep = data.sanitize_bars(df, "TST")
    assert rep["ghost_session_dropped"] == 1
    assert GHOST_2018 not in set(clean["date"].astype(str).str.slice(0, 10))


def test_exact_copy_of_the_previous_session_is_dropped():
    """En sık vaka (199/258): hayalet satır önceki seansın BİREBİR kopyası. Tekilleştirme bunu
    YAKALAMAZ (tarihler farklı); yakalayan tek şey takvimdir."""
    dates = _sessions("2025-05-01", BEFORE_2025)
    df = _flat(dates)
    kopya = df.iloc[[-1]].copy()
    kopya["date"] = pd.Timestamp(GHOST_2025)
    df = pd.concat([df, kopya], ignore_index=True)
    clean, rep = data.sanitize_bars(df, "AAPL")
    assert rep["ghost_session_dropped"] == 1 and "deduped_dates" not in rep


def test_unadjusted_ghost_row_cannot_poison_a_20_day_return():
    """CANLI VAKANIN KENDİSİ (BKNG): 213,31 → 5332,80 → 214,28. Kapıdan önce bu satırdan geçen
    20 günlük 'getiri' +%2400 mertebesinde bir HAYALDİ; kapıdan sonra seri gerçeğe döner."""
    dates = _sessions("2025-04-20", BEFORE_2025)
    df = _flat(dates, close=213.31, vol=3_810_525.0)
    df = pd.concat([df, _frame([(GHOST_2025, 5280.21, 5337.23, 5272.66, 5332.80, 152_421.0)]),
                    _frame([(AFTER_2025, 214.28, 218.87, 214.28, 218.07, 6_441_500.0)])],
                   ignore_index=True)
    kirli = float(df["close"].iloc[-1] / df["close"].iloc[-2] - 1.0)
    assert kirli < -0.9                                  # kirli seride ertesi gün -%96 "çöküş"
    clean, rep = data.sanitize_bars(df, "BKNG")
    assert rep["ghost_session_dropped"] == 1
    temiz = float(clean["close"].iloc[-1] / clean["close"].iloc[-2] - 1.0)
    assert abs(temiz) < 0.05                             # gerçek: %2,2'lik normal bir gün
    assert clean["close"].max() < 300.0                  # ham ölçekli satır serinin İÇİNDE yok


# ------------------------------------------------------------------ 2/3. KARANTİNA + YANLIŞ-POZİTİF
def test_isolated_unadjusted_row_on_a_valid_session_is_quarantined():
    """Sınıfın GEÇERLİ seansa düşen hâli (canlı örnek: CHD 2013-12-18 — 32,72 → 66,08 → 32,88,
    hacim TERS oranlı). Takvim onu kurtaramaz; karantina kuralı yakalar."""
    dates = _sessions("2013-12-02", "2013-12-31")
    df = _flat(dates, close=32.72, vol=1_000_000.0)
    i = dates.index("2013-12-18")
    df.loc[i, ["open", "high", "low", "close"]] = [65.06, 66.12, 64.48, 66.08]
    df.loc[i, "volume"] = 495_000.0                      # ×2 fiyat ↔ ×1/2 hacim: ham ölçek imzası
    clean, rep = data.sanitize_bars(df, "CHD")
    assert rep["unadjusted_quarantined"] == 1
    assert "2013-12-18" not in set(clean["date"].astype(str).str.slice(0, 10))
    ev = _events("bar_unadjusted_row_quarantined")
    assert len(ev) == 1 and ev[0]["ticker"] == "CHD"


def test_zero_volume_with_a_huge_move_is_the_second_signature():
    """2018 sınıfının imzası: fiyat %35+ oynarken hacim 0 — gerçek bir seansta İMKÂNSIZ.
    Ölçüldü: 1.343.892 geçerli-seans satırının 196'sında hacim 0, ve HİÇBİRİNDE %30'dan büyük
    hareket yok — yani bu imza yerel geçmişte yanlış-pozitif üretmiyor."""
    dates = _sessions("2019-03-01", "2019-03-29")
    df = _flat(dates, close=23.04)
    i = 8
    df.loc[i, ["open", "high", "low", "close"]] = [345.58] * 4
    df.loc[i, "volume"] = 0.0
    clean, rep = data.sanitize_bars(df, "ORLY")
    assert rep["unadjusted_quarantined"] == 1
    assert float(clean["close"].max()) < 30.0


def test_a_permanent_scale_seam_is_NOT_quarantined():
    """YANLIŞ-POZİTİF KORUMASI (kuralın en önemli şartı): sağlayıcının eski geçmişi ham ölçekte
    servis ettiği DİKİŞLERDE fiyat ×0,5 olur ve GERİ DÖNMEZ — yeni ölçek kalıcıdır. O satır yeni
    ölçeğin İLK barıdır; silmek deliği kapatmaz, geçmişi DELİK yapar. Ölçüldü: geri-dönüş şartı
    olmasaydı kural yerel geçmişte 38 masum satırı vururdu (2006-01-03 kümesi dahil)."""
    dates = _sessions("2006-01-03", "2006-02-15")
    lo = [50.0] * 10                                     # eski ölçek
    hi = [100.0] * (len(dates) - 10)                     # yeni ölçek — KALICI
    df = _frame([(d, c, c * 1.01, c * 0.99, c, 1_000_000.0 if c == 100.0 else 2_000_000.0)
                 for d, c in zip(dates, lo + hi)])
    clean, rep = data.sanitize_bars(df, "SEAM")
    assert "unadjusted_quarantined" not in rep
    assert len(clean) == len(dates)


def test_a_legitimate_shock_with_normal_volume_survives():
    """Meşru %40'lık kazanç şoku (hacim ARTAR, ters oranlı değil) ve ertesi gün geri dönmez —
    dokunulmaz. Kural üç şartı BİRDEN ister; iki şart yeterli olsaydı gerçek hareketler silinirdi."""
    dates = _sessions("2024-02-01", "2024-02-29")
    df = _flat(dates, close=100.0)
    i = 5
    for j in range(i, len(df)):                          # şok KALICI (geri dönmez)
        df.loc[j, ["open", "high", "low", "close"]] = [140.0] * 4
    df.loc[i, "volume"] = 9_000_000.0                    # hacim PATLAR (ters oran DEĞİL)
    clean, rep = data.sanitize_bars(df, "NVDA")
    assert "unadjusted_quarantined" not in rep and len(clean) == len(dates)


def test_a_single_bar_frame_is_never_judged():
    """Artımlı kaynaklar (massive grouped, aynı-akşam bacağı) TEK satır döndürür. Komşusu olmayan
    bir bar hakkında 'sıçrama' hükmü verilemez — kural sessizce geçer, uydurmaz."""
    tek = _frame([(_sessions("2026-07-01", "2026-07-31")[0], 100.0, 101.0, 99.0, 100.5, 5.0)])
    clean, rep = data.sanitize_bars(tek, "AAPL")
    assert len(clean) == 1 and "unadjusted_quarantined" not in rep


# ------------------------------------------------------------------ 4. KİTLESEL RED
def test_mass_calendar_mismatch_refuses_instead_of_amputating():
    """Bir seri BÜYÜK ölçüde takvim-dışıysa (başka borsa/takvim, sentetik seri) kapı satır SİLMEZ:
    %4'lük bir amputasyon, hayalet barların zararından büyük ve GERİ ALINAMAZ. Bunun yerine ölçer
    ve hükmü operatöre bırakır. DÖNÜŞTÜRÜCÜ OLAY YAZMAZ — duyuru disk yolunun işi (aşağıdaki test)."""
    dates = [str(d.date()) for d in pd.bdate_range("2026-01-01", periods=80)]
    df = _flat(dates)
    clean, rep = data.sanitize_bars(df, "FOREIGN")
    assert "ghost_session_dropped" not in rep and len(clean) == len(dates)
    assert rep["calendar_mismatch_rows"] >= 2
    assert data.ghost_report()["refused"]["FOREIGN"]["share_pct"] > 1.0
    assert _events("bar_calendar_mismatch") == []


def test_the_disk_path_announces_a_refused_ledger(monkeypatch):
    """Diskteki bir defterin takvimi tutmuyorsa bu KALICI durumdur ve duyurulur — sessiz kalan bir
    red, var olduğu sanılan ama hiç çalışmayan bir savunma olurdu."""
    dates = [str(d.date()) for d in pd.bdate_range("2026-01-01", periods=80)]
    data._write_bars(_flat(dates), data._cache_path("FOREIGN"))
    monkeypatch.setattr(data, "fetch", lambda t, s, e, **k: pd.DataFrame())
    data.load_bars("FOREIGN", "2026-01-01", dates[-1], use_cache=False, polite_delay=0)
    ev = _events("bar_calendar_mismatch")
    assert len(ev) == 1 and ev[0]["ticker"] == "FOREIGN" and ev[0]["non_session_rows"] >= 2


def test_the_real_defect_is_far_below_the_refusal_threshold():
    """Eşiğin GERÇEK arızayı kaçırmadığının kanıtı: ölçülen en kötü hâl defter başına 2 hayalet
    satır ve %0,1233 pay. Aşağıdaki seri o en kötü hâli taklit eder ve kapı onu DÜŞÜRÜR."""
    dates = _sessions("2018-01-01", "2025-12-31")[:800]
    df = _flat(dates)
    df = pd.concat([df, _flat([GHOST_2018, GHOST_2025])], ignore_index=True)
    clean, rep = data.sanitize_bars(df, "REAL")
    assert rep["ghost_session_dropped"] == 2 and not data.ghost_report()["refused"]


def test_calendar_failure_fails_open_and_says_so(monkeypatch):
    """Takvim okunamazsa kapı AÇIK kalır (satır düşmez) ama SESSİZ kalmaz. Fail-closed davranmak
    1,3 milyon satırlık geçmişi silmek olurdu — bir bütünlük kapısının yanlış tarafa kapanması,
    korumaya çalıştığı şeyi yok etmesidir."""
    monkeypatch.setattr(data, "_SESSIONS", frozenset())
    monkeypatch.setattr(data, "_SESSION_SPAN", ())
    monkeypatch.setattr(data, "_CAL_FAILED", True)       # yeniden üretmeyi denemesin
    df = _flat(["2025-05-23", GHOST_2025, "2025-05-27"])
    clean, rep = data.sanitize_bars(df, "TST")
    assert len(clean) == 3 and "ghost_session_dropped" not in rep


# ------------------------------------------------------------------ validate_bars
def test_validate_bars_calls_a_ghost_row_HARD():
    """Kapıyı ATLAMIŞ bir çerçeve `load_many`den geçmemeli: hayalet satır artık SERT bulgudur
    (ok=False), çünkü bu bir şüphe değil olgudur — piyasa o gün kapalıydı."""
    df = _flat(_sessions("2025-05-01", BEFORE_2025) + [GHOST_2025])
    ok, issues = data.validate_bars(df, "TST")
    assert ok is False
    assert "ghost_session" in {i["code"] for i in issues if i["severity"] == "hard"}


def test_validate_bars_has_no_side_effects():
    """RAPOR YAZMAZ: doğrulama çağrısı olay defterine satır eklerse, ölçüm ölçtüğü şeyi değiştirir
    (ve kum-havuzsuz her çağrı CANLI deftere düşerdi)."""
    df = _flat([str(d.date()) for d in pd.bdate_range("2026-01-01", periods=80)])
    data.validate_bars(df, "FOREIGN")
    assert _events("bar_calendar_mismatch") == [] and not data._CAL_MISMATCH


# ------------------------------------------------------------------ zincir + disk yolu
def test_every_source_leg_passes_through_the_gate(monkeypatch):
    """Kapı zincirin ORTAK boğazındadır: hangi bacak servis ederse etsin (burada cboe), hayalet
    satır `fetch`ten DÖNEN çerçevede olamaz."""
    dates = _sessions("2025-04-01", BEFORE_2025)
    kirli = pd.concat([_flat(dates), _flat([GHOST_2025])], ignore_index=True)
    monkeypatch.setattr(data, "_fetch_cboe", lambda t, to: kirli.copy())
    monkeypatch.setattr(data, "_fetch_nasdaq", lambda t, s, e, to: pd.DataFrame())
    from meridian.adapters import fmp, massive
    monkeypatch.setattr(fmp, "available", lambda: False)
    monkeypatch.setattr(massive, "available", lambda: False)
    monkeypatch.setattr(massive, "write_enabled", lambda: False)
    got = data.fetch("TST", "2025-01-01", BEFORE_2025)
    assert GHOST_2025 not in set(got["date"].astype(str).str.slice(0, 10))


def test_load_bars_cleans_the_disk_and_bumps_the_wf_revision(monkeypatch):
    """DİSK YOLU: önbellekte hayalet satır varken yeni bir seans geldiğinde dosya TEMİZ yazılır,
    `bar_row_loss_refused` TETİKLENMEZ (kapının düşürdüğü satır 'kayıp' değildir) ve wf-revizyonu
    BUMPLANIR — yani watchdog için sessiz mutasyon değil, sanctioned düzeltmedir."""
    dates = _sessions("2025-03-01", BEFORE_2025)
    data._write_bars(pd.concat([_flat(dates), _flat([GHOST_2025])], ignore_index=True)
                     .sort_values("date").reset_index(drop=True), data._cache_path("TST"))
    rev0 = int(store.read_json("wf_cache_rev.json", {}).get("rev", 0))
    monkeypatch.setattr(data, "fetch", lambda t, s, e, **k: _flat([AFTER_2025]))
    monkeypatch.setattr(data, "_LAST_SOURCE", {"TST": "cboe"})
    out = data.load_bars("TST", "2025-01-01", AFTER_2025, use_cache=False, polite_delay=0)
    diskte = pd.read_csv(data._cache_path("TST"))
    gunler = set(diskte["date"].astype(str).str.slice(0, 10))
    assert GHOST_2025 not in gunler and AFTER_2025 in gunler
    assert len(diskte) == len(dates) + 1
    assert _events("bar_row_loss_refused") == []
    assert int(store.read_json("wf_cache_rev.json", {}).get("rev", 0)) > rev0
    assert GHOST_2025 not in set(out["date"].astype(str).str.slice(0, 10))


def test_the_round_summary_reports_how_many_rows_the_gate_dropped(monkeypatch):
    """SAYAÇ TÜKETİLİR: tarih-başına-tek olay 'NE oldu'yu söyler, tur sonu özeti 'NE KADAR'ı.
    Üretilip tüketilmeyen bir sayaç, bu depoda yasak (YASA 6)."""
    dates = _sessions("2025-03-01", BEFORE_2025)
    for t in ("AAA", "BBB"):
        data._write_bars(pd.concat([_flat(dates), _flat([GHOST_2025])], ignore_index=True)
                         .sort_values("date").reset_index(drop=True), data._cache_path(t))
    monkeypatch.setattr(data, "fetch", lambda t, s, e, **k: pd.DataFrame())
    data.load_many(["AAA", "BBB"], "2025-01-01", BEFORE_2025)
    ev = _events("bar_ghost_round_summary")
    assert len(ev) == 1 and ev[0]["rows"] == 2 and ev[0]["dates"] == GHOST_2025
    assert data.ghost_report()["dates"][GHOST_2025]["rows"] == 2


# ------------------------------------------------------------------ 5. ONARIM ARACI
def _seed_dirty(ticker: str = "TST") -> int:
    dates = _sessions("2025-03-01", BEFORE_2025)
    df = pd.concat([_flat(dates), _flat([GHOST_2025])], ignore_index=True)
    data._write_bars(df.sort_values("date").reset_index(drop=True), data._cache_path(ticker))
    return len(df)


def test_repair_dry_run_reports_but_writes_nothing():
    """KURU KOŞU VARSAYILANDIR: veri silen bir aracın varsayılanının yazmak olması, bu depoda
    yaşanmış hata sınıfıdır."""
    from meridian import barrepair
    n0 = _seed_dirty()
    cp = data._cache_path("TST")
    once = cp.read_bytes()
    rapor = barrepair.repair()
    assert rapor["applied"] is False and rapor["ghost_rows"] == 1
    assert rapor["dates"][GHOST_2025]["classes"] == {"birebir_kopya": 1}
    assert cp.read_bytes() == once and len(pd.read_csv(cp)) == n0


def test_repair_apply_removes_rows_through_the_sanctioned_path():
    """UYGULAMA: satır silinir, wf-revizyonu bumplanır ve `watchdog.determinism_report` küçülmeyi
    SESSİZ MUTASYON saymaz — onarımın SANCTIONED yoldan geçtiğinin doğrudan kanıtı."""
    from meridian import barrepair
    n0 = _seed_dirty()
    watchdog.determinism_report(persist=True)            # taban: onarım ÖNCESİ boyutlar
    rapor = barrepair.repair(apply=True)
    assert rapor["applied"] is True and len(rapor["written"]) == 1
    assert rapor["written"][0]["before"] - rapor["written"][0]["after"] == 1
    assert len(pd.read_csv(data._cache_path("TST"))) == n0 - 1
    rep = watchdog.determinism_report()
    assert rep["ok"] is True and rep["rev_bumped"] is True and rep["shrunk"] == 1


def test_repair_without_the_bump_would_be_caught(monkeypatch):
    """DEDEKTÖRÜN KENDİSİ ÖLÇÜLÜR: bump kaldırılırsa aynı onarım 'SESSİZ BAR MUTASYONU' olarak
    yakalanır. Bu test olmadan yukarıdaki yeşil, dedektörün körlüğüyle de açıklanabilirdi."""
    from meridian import barrepair
    _seed_dirty()
    watchdog.determinism_report(persist=True)
    monkeypatch.setattr(data, "_bump_wf_rev", lambda: None)
    barrepair.repair(apply=True)
    rep = watchdog.determinism_report()
    assert rep["ok"] is False and rep.get("silent_bar_mutation") is True


def test_repair_refuses_to_write_while_the_worker_runs(monkeypatch, capsys):
    """Aynı defteri iki süreç yeniden yazamaz (store kilidi SÜREÇ-İÇİDİR). Araç canlı süreci
    görürse `--uygula`yı reddeder; kuru koşu her zaman serbesttir."""
    from meridian import barrepair
    n0 = _seed_dirty()
    monkeypatch.setattr(barrepair, "_worker_running", lambda: True)
    assert barrepair.main(["--uygula"]) == 2
    assert len(pd.read_csv(data._cache_path("TST"))) == n0
    assert barrepair.main([]) == 0                       # kuru koşu reddedilmez
    assert GHOST_2025 in capsys.readouterr().out


def test_repair_leaves_clean_ledgers_untouched():
    """Temiz defter YENİDEN YAZILMAZ: gereksiz yazım, determinizm parmak izini boşuna oynatır
    ve 'ne değişti' sorusunu gürültüye boğar."""
    from meridian import barrepair
    data._write_bars(_flat(_sessions("2025-03-01", BEFORE_2025)), data._cache_path("CLEAN"))
    once = data._cache_path("CLEAN").read_bytes()
    rapor = barrepair.repair(apply=True)
    assert rapor["ghost_rows"] == 0 and rapor["written"] == []
    assert data._cache_path("CLEAN").read_bytes() == once

"""test_differential_v60.py — DİFERANSİYEL MOTOR TESTİ (2026-07-22).

NEDEN VAR: tek bir strateji için İKİ motor yazılmış — `backtest.replay` (geçmişi tohumlayan) ve
`loop.daily_cycle` (canlı). İkisi 2026-07-21'de sessizce ayrıştı:

  * plan kimliği: backtest `P00140`, canlı `P-{tarih}-{ticker}` → `cf_fidelity` (simülasyonun
    gerçeğe uyup uymadığını ölçen TEK mekanizma) birleştirme anahtarını kuramadı, 90/90 satır elendi.
  * `gate_checks` (karar ağacı) yalnız canlı motorda üretiliyordu → panonun tablosu 144/144 boştu.

İkisi de elle düzeltildi; **bir sonraki ayrışmayı engelleyen hiçbir şey yoktu.** Bu dosya o boşluğu
kapatır: AYNI barlar + AYNI seanslar iki motora da verilir ve üretilen plan sözlükleri ALAN ALAN
karşılaştırılır. Bilinen iki hatayı değil, HERHANGİ bir alan ayrışmasını yakalar — anahtar kümeleri
de kıyaslanır, yani yeni bir alan tek motorda belirirse test kırılır ve tartışılır.

Testin bulduğu ve düzeltilen ayrışma (2026-07-22): `earnings_blackout` kontrolü İKİ motorda da
uygulanıyordu ama KANIT satırını (gate_checks) yalnız canlı motor yazıyordu — 144/144 hatasının
satır seviyesindeki hâli. Düzeltme: meridian/backtest.py, karar mantığına dokunmadan.

Kalan ayrışmalar bilinçli KAPSAM farklarıdır; her biri aşağıda gerekçesiyle beyan edilir ve
"beyan çürümesin" testleriyle sabitlenir.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from meridian import backtest, config, loop, store
from tests.conftest import make_bars


# ---------------------------------------------------------------------------------------------
# BEYAN EDİLMİŞ KAPSAM FARKLARI — dar, gerekçeli, tek tek savunulmuş.
# Kural: bir alan yalnız TEK motorda VAR OLABİLİYORSA buraya girer. "Değeri tutmuyor" ASLA girmez.
# ---------------------------------------------------------------------------------------------
LIVE_ONLY_PLAN_FIELDS = {
    # UYUYAN KURULUM KANALI: canlı döngü, silahlı olmayan (ölçüm amaçlı) kurulumların ateşlemesini de
    # plan olarak yazar ve bunu bu bayrakla işaretler. Replay'in tarama yolu `strategy.scan_entry`
    # yalnız ARMED_SETUPS döndürür — backtest'te "uyuyan plan" diye bir KAVRAM yoktur, dolayısıyla
    # işaretlenecek bir şey de yoktur. Bu bir şema ayrışması değil, kapsam farkı.
    "dormant_setup",
    # GÖLGE MODEL OLASILIĞI: yalnız diskte eğitilmiş model varsa canlı planın üstüne damgalanır.
    # Replay onu hiç yüklemez (arama yolunda binlerce replay × model yükleme) ve kapı kararına da
    # dokunmaz — yalnız REVIEW + TERFİLİ model durumunda veto üretir.
    "p_win_shadow",
    # LLM GÖRÜŞ DAMGASI: hermes canlı plan defterine SONRADAN basar (ayrı yazar, ayrı zaman).
    # Replay'de LLM katmanı hiç koşmaz.
    "llm_opinion", "llm_confidence", "llm_rationale",
}

LIVE_ONLY_GATE_CHECKS = {
    # AYNA MEŞGULİYETİ: "bu sembol için aynada hâlâ canlı emir/yetim pozisyon var mı?" sorusunun
    # replay'de karşılığı YOKTUR (ayna diye bir şey yok, broker in-process simülatör).
    "mirror_busy",
    # GÖLGE VETO: yalnız TERFİLİ gölge model yüklüyken üretilir — replay modeli hiç yüklemez.
    "shadow_veto",
}

# Fiyat alanları: canlı satır `EntrySignal.as_row()` üzerinden geçtiği için 4 basamağa YUVARLANMIŞ,
# backtest ise dataclass alanını ham float olarak yazıyor. Aynı sayı, iki yazım geleneği. Bu tolere
# EDİLMEZ, SABİTLENİR: canlı değer, backtest değerinin 4 basamağa yuvarlanmışına EŞİT olmalı — biri
# geleneği değiştirirse test kırılır (aşağıda ayrı testi var).
PRICE_FIELDS = ("entry_trigger", "stop", "profit_target")


@pytest.fixture
def seeded(sandbox_state, monkeypatch):
    repo = Path(__file__).resolve().parent.parent / "state"
    for f in ("goal.yaml", "bounds.yaml"):
        shutil.copy2(repo / f, sandbox_state / f)
    config.reload_config()
    (sandbox_state / "strategy.yaml").write_text(yaml.safe_dump(config.default_strategy()))
    # Üyelik kaynağı bekçi içinden AĞA çıkıyor (HTTP 403 → 'starved' alarmı). Bu test motorları
    # kıyaslar, interneti değil.
    from meridian.adapters import constituents
    monkeypatch.setattr(constituents, "health", lambda: {"ok": True}, raising=False)
    yield sandbox_state
    config.reload_config()


def _valid_ohlc(df):
    """make_bars OHLC'si TUTARSIZ üretiyor (open/close bazen high'ın üstünde) ve
    `adapters.data.validate_bars` bunu SERT hata sayıyor. Ham make_bars ile canlı döngü veri-kalitesi
    kapısında durur, hiç taramaz — yani "0 plan = 0 plan" diye SAHTE bir eşitlik çıkardı. Bu satır,
    testin gerçekten iki motoru kıyaslamasını sağlar (mevcut testlerin ayrışmayı neden görmediğinin
    de cevabı: canlı taraf o barlarla hiç tarama yapmıyor)."""
    df = df.copy()
    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)
    return df


N_BARS = 300
# Endeks tohumu: maruziyet bütçesini karşılaştırılan seansların TAMAMINDA >0 tutuyor. Bütçe 0 iken
# canlı döngü "keşif kipine" geçip yine tarar, backtest ise hiç taramaz (aşağıda beyan edilmiş
# asimetri) — kıyas penceresinin o farktan etkilenmemesi için tohum bilinçli seçildi.
INDEX_SEED, INDEX_TREND = 7, 0.0006
# Gerçek sektör haritasından ticker'lar: sektör tavanı iki motorda da aynı şekilde işlesin diye
# (uydurma sembollerin hepsi "?" sektörüne düşerdi).
TICKERS = {"AAPL": 9, "JPM": 10, "UNH": 27, "CAT": 34, "XOM": 63, "KO": 5, "NKE": 6,
           "GS": 3, "MRK": 4}
WINDOW = 10          # kıyaslanan seans sayısı
WARMUP = 3           # goal.yaml: no_trade_before_bars — replay'in ısınma payı (aşağıda beyan edildi)


def _universe():
    idx = _valid_ohlc(make_bars(N_BARS, seed=INDEX_SEED, trend=INDEX_TREND))
    bars = {t: _valid_ohlc(make_bars(N_BARS, seed=s, breakout_at=N_BARS - 1))
            for t, s in TICKERS.items()}
    return bars, idx


def _budgets(idx, dates) -> dict:
    """Her seansın maruziyet bütçesi — iki motor da bunu AYNI fonksiyondan hesaplıyor."""
    from meridian import regime as regime_mod
    ix = idx.set_index("date").sort_index()
    params = config.default_strategy()["params"]
    out = {}
    for d in ix.index:
        ds = str(d.date())
        if ds in dates:
            out[ds] = regime_mod.build_regime_json(ix.loc[:d].reset_index(), params, ds)["exposure_budget_pct"]
    return out


_ENGINES: dict = {}      # iki motoru bir kez koştur: 10 canlı döngü + bir replay TEST BAŞINA
                         # tekrarlanırsa dosya tek başına dakikalar sürer. Çıktı saf sözlük listesi,
                         # testler durumu değil yalnız planları okuyor — paylaşmak güvenli.


@pytest.fixture
def both_engines(seeded):
    """AYNI barlar, AYNI seans dizisi → iki motor. Canlı motor günleri sırayla işler (defteri
    ilerleterek), replay aynı pencereyi tek geçişte oynar."""
    if _ENGINES:
        return _ENGINES
    bars, idx = _universe()
    dates = [str(x.date()) for x in idx["date"].iloc[-WINDOW:]]
    for d in dates:
        loop.daily_cycle(bars, idx, on_date=d)
    live = store.read_jsonl("trade_plans.jsonl")
    res = backtest.replay(config.default_strategy()["params"], bars, idx, config.goal(),
                          dates[0], dates[-1], strategy_version=1, with_gate_detail=True)
    bt = res.plan_log or []
    budgets = _budgets(idx, set(dates))
    # KIYAS PENCERESİ: ısınma payından sonraki VE maruziyet bütçesi >0 olan seanslar. Dışarıda kalan
    # her seansın gerekçesi aşağıda ayrı bir testle sabitlenmiştir (beyan çürümesin).
    comparable = {d for d in dates[WARMUP:] if budgets.get(d, 0) > 0}
    _ENGINES.update({"live": live, "bt": bt, "dates": dates, "budgets": budgets,
                     "comparable": comparable})
    return _ENGINES


def _in_window(plans, days):
    return {p["id"]: p for p in plans if p.get("date") in days}


# ---------------------------------------------------------------------------------------------
# 0) TEST GERÇEKTEN BİR ŞEY KIYASLIYOR MU (boş kümeyle geçen test, geçmeyen testten kötüdür)
# ---------------------------------------------------------------------------------------------
def test_the_comparison_is_not_vacuous(both_engines):
    live = _in_window(both_engines["live"], both_engines["comparable"])
    bt = _in_window(both_engines["bt"], both_engines["comparable"])
    assert both_engines["comparable"], "kıyaslanabilir seans yok — test hiçbir şey kanıtlamıyor"
    assert live and bt, f"plan üretilmedi (canlı={len(live)}, replay={len(bt)}) — kıyas boş"


# ---------------------------------------------------------------------------------------------
# 1) AYNI PLANLAR: kimlik kümesi
# ---------------------------------------------------------------------------------------------
def test_both_engines_emit_the_same_plan_ids(both_engines):
    """Kimlik ŞEMASI değil, kimlik KÜMESİ: aynı barlarda aynı planlar doğmalı."""
    live = _in_window(both_engines["live"], both_engines["comparable"])
    bt = _in_window(both_engines["bt"], both_engines["comparable"])
    # uyuyan kurulum planları backtest'te var olamaz (beyan edilmiş kapsam farkı — bkz. üst blok)
    live_armed = {k: v for k, v in live.items() if not v.get("dormant_setup")}
    assert set(live_armed) == set(bt), (
        f"plan kümeleri ayrıştı — yalnız canlı: {sorted(set(live_armed) - set(bt))}, "
        f"yalnız replay: {sorted(set(bt) - set(live_armed))}")


def test_plan_id_scheme_is_identical(both_engines):
    """2026-07-21'in birinci ayrışması: `P00140` ↔ `P-{tarih}-{ticker}`. Anahtar biçimi tek olmalı."""
    from meridian.ledgers import PLAN_ID_RE
    for p in both_engines["live"] + both_engines["bt"]:
        assert PLAN_ID_RE.match(str(p["id"])), f"birleştirilemez plan kimliği: {p['id']!r}"


# ---------------------------------------------------------------------------------------------
# 2) AYNI ŞEMA: alan kümeleri (gelecekteki HERHANGİ bir alan ayrışması buradan patlar)
# ---------------------------------------------------------------------------------------------
def test_plan_dicts_have_the_same_field_set(both_engines):
    live = _in_window(both_engines["live"], both_engines["comparable"])
    bt = _in_window(both_engines["bt"], both_engines["comparable"])
    for pid, b in bt.items():
        lk, bk = set(live[pid]), set(b)
        only_live, only_bt = lk - bk - LIVE_ONLY_PLAN_FIELDS, bk - lk
        assert not only_live, f"{pid}: yalnız CANLI motorda olan beyan edilmemiş alan: {sorted(only_live)}"
        assert not only_bt, f"{pid}: yalnız REPLAY motorunda olan alan: {sorted(only_bt)}"


def test_declared_live_only_fields_are_really_absent_from_the_backtest(both_engines):
    """BEYAN ÇÜRÜMESİN: allowlist'teki bir alan backtest'te de üretilmeye başlarsa liste yalan
    söylemeye başlar ve gerçek bir ayrışmayı maskeleyebilir."""
    bt_keys = set().union(*[set(p) for p in both_engines["bt"]])
    leaked = bt_keys & LIVE_ONLY_PLAN_FIELDS
    assert not leaked, f"artık backtest de üretiyor — allowlist'ten çıkarılmalı: {sorted(leaked)}"


# ---------------------------------------------------------------------------------------------
# 3) AYNI DEĞERLER: ticker, setup, skor, tetik, stop, hedef, boyut, rejim, kapı kararı
# ---------------------------------------------------------------------------------------------
EXACT_FIELDS = ("date", "ticker", "side", "setup", "score", "sector", "size_r",
                "r_multiple_expected", "regime_at_plan", "strategy_version", "skill_chain",
                "gate_verdict", "gate_reasons")


def test_every_scalar_plan_field_matches(both_engines):
    live = _in_window(both_engines["live"], both_engines["comparable"])
    bt = _in_window(both_engines["bt"], both_engines["comparable"])
    diffs = []
    for pid, b in bt.items():
        a = live[pid]
        for k in EXACT_FIELDS:
            if a.get(k) != b.get(k):
                diffs.append(f"{pid}.{k}: canlı={a.get(k)!r} replay={b.get(k)!r}")
    assert not diffs, "motorlar aynı barlarda farklı plan üretti:\n" + "\n".join(diffs)


def test_price_levels_match_to_the_declared_rounding_convention(both_engines):
    """Tetik/stop/hedef: canlı satır `as_row()` üzerinden 4 basamağa yuvarlanır, replay ham float
    yazar. Tek geleneğe SABİTLENİR — biri yuvarlamayı bırakır ya da başka basamağa geçerse kırılır."""
    live = _in_window(both_engines["live"], both_engines["comparable"])
    bt = _in_window(both_engines["bt"], both_engines["comparable"])
    for pid, b in bt.items():
        a = live[pid]
        for k in PRICE_FIELDS:
            assert a[k] == round(float(b[k]), 4), f"{pid}.{k}: canlı={a[k]!r} replay={b[k]!r}"
        assert [round(float(x), 4) for x in b["targets"]] == a["targets"], f"{pid}.targets"


# ---------------------------------------------------------------------------------------------
# 4) AYNI KARAR AĞACI: gate_checks varlığı VE şekli
# ---------------------------------------------------------------------------------------------
def test_gate_checks_exist_in_both_engines(both_engines):
    """2026-07-21'in ikinci ayrışması: karar ağacını yalnız canlı motor yazıyordu."""
    for p in both_engines["bt"]:
        assert p.get("gate_checks"), f"replay planı karar ağacı taşımıyor: {p['id']}"
    for p in both_engines["live"]:
        assert p.get("gate_checks"), f"canlı plan karar ağacı taşımıyor: {p['id']}"


def test_gate_checks_have_the_same_checks_in_the_same_order(both_engines):
    """Kontrol ADLARI ve SIRASI aynı olmalı: sıra karar ağacının kendisidir. Yalnız beyan edilmiş
    canlıya-özgü kontroller (ayna/gölge) fazladan olabilir ve onlar SONA eklenir."""
    live = _in_window(both_engines["live"], both_engines["comparable"])
    bt = _in_window(both_engines["bt"], both_engines["comparable"])
    for pid, b in bt.items():
        ln = [c["check"] for c in live[pid]["gate_checks"] if c["check"] not in LIVE_ONLY_GATE_CHECKS]
        bn = [c["check"] for c in b["gate_checks"]]
        assert ln == bn, f"{pid}: karar ağacı ayrıştı\n canlı={ln}\n replay={bn}"


def test_gate_check_rows_have_the_same_shape_and_verdict(both_engines):
    """Satır satır: aynı anahtarlar, aynı passed/severity. 'Kural aynı, kayıt farklı' bu testte ölür
    (earnings_blackout ayrışması tam olarak buydu)."""
    live = _in_window(both_engines["live"], both_engines["comparable"])
    bt = _in_window(both_engines["bt"], both_engines["comparable"])
    for pid, b in bt.items():
        lrows = {c["check"]: c for c in live[pid]["gate_checks"]}
        for c in b["gate_checks"]:
            l = lrows[c["check"]]
            assert set(l) == set(c), f"{pid}/{c['check']}: satır anahtarları ayrıştı {set(l) ^ set(c)}"
            assert (l["passed"], l["severity"]) == (c["passed"], c["severity"]), \
                f"{pid}/{c['check']}: canlı={l} replay={c}"


def test_declared_live_only_gate_checks_are_really_absent_from_the_backtest(both_engines):
    bt_checks = {c["check"] for p in both_engines["bt"] for c in p["gate_checks"]}
    leaked = bt_checks & LIVE_ONLY_GATE_CHECKS
    assert not leaked, f"artık replay de üretiyor — allowlist'ten çıkarılmalı: {sorted(leaked)}"


def test_the_earnings_blackout_evidence_row_is_produced_by_both_engines(both_engines):
    """BU TESTİN BULDUĞU AYRIŞMA (2026-07-22): karartma kuralını iki motor da uyguluyordu, kanıt
    satırını yalnız canlı yazıyordu. Regresyon kilidi."""
    for p in both_engines["bt"]:
        names = {c["check"] for c in p["gate_checks"]}
        assert "earnings_blackout" in names, f"replay kanıt satırı yazmıyor: {p['id']}"
        row = next(c for c in p["gate_checks"] if c["check"] == "earnings_blackout")
        assert row["severity"] == "hard" and "coverage" in row, row


# ---------------------------------------------------------------------------------------------
# 5) BEYAN EDİLMİŞ ASİMETRİLER — kıyas penceresinin DIŞINDA bırakılan her şeyin gerekçesi
# ---------------------------------------------------------------------------------------------
def test_exploration_mode_is_the_only_reason_a_zero_budget_session_diverges(both_engines):
    """Maruziyet bütçesi 0 iken canlı döngü 'keşif kipine' geçip yine tarar (yalnız GO notu, 0.25R
    sonda); replay o seansı hiç taramaz. Bilinçli bir KAPSAM farkı — ama sessiz kalmamalı: ayrışan
    seansların TAMAMI bütçe=0 olmalı, biri bile bütçe>0 ise bu gerçek bir ayrışmadır."""
    b = both_engines
    live_days = {p["date"] for p in b["live"] if not p.get("dormant_setup")}
    bt_days = {p["date"] for p in b["bt"]}
    live_only_days = live_days - bt_days - set(b["dates"][:WARMUP])
    for d in live_only_days:
        assert b["budgets"].get(d, 0) == 0, \
            f"{d}: bütçe {b['budgets'].get(d)} > 0 olduğu hâlde yalnız canlı motor plan üretti"


def test_the_replay_warmup_is_the_only_reason_early_sessions_are_skipped():
    """goal.yaml'daki `no_trade_before_bars` YALNIZ replay'de uygulanır (pencerenin ilk N barı
    ısınma payıdır); canlı motorda böyle bir kavram yoktur — döngü zaten yıllardır koşuyor.
    Bu bir ayrışma değil, replay penceresine özgü bir kenar kuralıdır; kıyas o payın dışında yapılır."""
    import inspect
    src = inspect.getsource(backtest.replay)
    assert "no_trade_before" in src
    assert "no_trade_before" not in inspect.getsource(loop.daily_cycle)
    assert int(config.goal()["limits"].get("no_trade_before_bars", 0)) == WARMUP, \
        "ısınma payı değişti — kıyas penceresi (WARMUP) güncellenmeli"


def test_only_the_live_engine_has_a_dormant_setup_channel():
    """Uyuyan kurulum planları (kimliği `P-{tarih}-{ticker}-{setup}`) yalnız canlıda doğar: replay'in
    tarama yolu ARMED_SETUPS dışına çıkmaz. Beyanın kaynak kodda karşılığı."""
    import inspect
    from meridian import strategy as strat
    assert "dormant_setup" in inspect.getsource(loop.daily_cycle)
    assert "dormant" not in inspect.getsource(backtest.replay)
    assert "ARMED_SETUPS" in inspect.getsource(strat.scan_entry)

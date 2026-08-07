"""test_icra_gercekligi_v141.py — WP-E / kart EXE-2026-001: GİRİŞ İCRA GERÇEKLİĞİ (2026-07-31).

NE ÇİVİLENİYOR. Denetim (WP0 matrisi #1) iki motorun FARKLI icra modeli koştuğunu buldu:
  * iç motor  → ertesi açılışta KOŞULSUZ dolum (yalnız %4 max-chase tavanı),
  * ayna      → buy-stop GTC bracket; `entry_trigger` sinyal barının KAPANIŞI olduğu için Alpaca
                "stop price must be greater than current price" ile reddediyordu → canlı defterde
                95/95 satırda `alpaca_fill_price` YOK, E2 slipaj defteri hiç dolmadı.

Bu dosya dört şeyi kilitler:
  E1 — İKİ MOTOR TEK YASADAN OKUR (AST + davranış), gap yollarının ÜÇÜ, `entry_missed_limit`.
  E2 — slipaj defterinin iki bps hesabı + ret nedeni sınıflaması + ölçülemeyen None dürüstlüğü.
  E3 — kötümser bandın ikiz sütunu ve None yolları (band yoksa sütun sessizce 0 yazmaz).
  E4 — gece/gündüz ayrıştırmasının bar join'i (sentetik barlar, gap'li vaka, TAM özdeşlik).
"""
import ast
import inspect
import json
import pathlib

import pandas as pd
import pytest

from meridian import analytics as an
from meridian import broker as BR
from meridian import config, guard, loop, store
from meridian.adapters import alpaca
from meridian.broker import PaperBroker


PLAN = {"id": "P-2026-07-31-AAA", "ticker": "AAA", "entry_trigger": 100.0, "stop": 95.0,
        "profit_target": 115.0, "size_r": 1.0}

# OPERATÖR KARARI 2026-08-03 (goal.yaml `execution_v2` karar-yorumu; kart EXE-2026-001 hükmü + ölçüm
# research/olcumler/e1_grid_2026-08-03): E1 giriş limiti BAĞLAMAZ hâle getirildi — 0,5·ATR/%1 →
# 100·ATR/%4. YÜRÜRLÜKTE ATR bacağı hiçbir makul senaryoda bağlamaz ve %4 (= MAX_ENTRY_GAP_PCT)
# bağlayan taraftır. Aşağıdaki MEKANİZMA testleri yasanın HESABINI sınar (min-of-two-caps, gap
# yolları, kaçan dolumun ölçülmesi), YÜRÜRLÜĞÜNÜ değil — bu yüzden yasa kaynağı eski kart
# varsayılanına AÇIKÇA sabitlenir. Yürürlük iddiası ayrı testtedir:
# `test_e1_limit_cap_never_loosens_the_max_chase_ceiling`.
KART_YASASI = {"limit_atr_mult": 0.5, "limit_pct_cap": 0.01}


def _broker():
    return PaperBroker(equity=100_000.0, slippage_bps=0.0, commission_per_share=0.0)


def _kart_yasasini_sabitle(monkeypatch):
    """`fill_entry` yasayı argümandan DEĞİL `broker.entry_law()`tan okur; mekanizma testlerinde
    yasa kaynağı burada kart varsayılanına sabitlenir (açık override, sessiz varsayım değil)."""
    _asil = BR.entry_law
    monkeypatch.setattr(BR, "entry_law", lambda override=None: _asil(override or KART_YASASI))


# =================================================================================================
# E1 — TEK YASA, İKİ MOTOR
# =================================================================================================
def test_e1_law_lives_in_exactly_one_place(sandbox_state):
    """AST ÇİVİSİ: limit hesabı YALNIZ `broker.entry_limit_price`ta olabilir. İki motorun da bu
    fonksiyonu ÇAĞIRDIĞI, hiçbirinin kendi kopyasını KURMADIĞI kanıtlanır — çünkü bu depoda
    "aynı yasanın iki uygulaması" defalarca sessiz ayrışma üretti (guard'ın ikinci risk zarfı,
    mirror_stream'in ikinci iptal kopyası, iki plan-kimliği şeması)."""
    for mod in (alpaca, loop):
        src = inspect.getsource(mod)
        tree = ast.parse(src)
        adlar = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | \
                {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        assert "ENTRY_LIMIT_ATR_MULT" not in adlar and "ENTRY_LIMIT_PCT_CAP" not in adlar, \
            f"{mod.__name__} limit sabitlerini KENDİ hesabında kullanıyor — yasa kopyalandı"
    # ayna kararı yasadan okur
    assert "entry_order_decision" in inspect.getsource(alpaca.submit_plan)
    # iç motor da aynı modülün fonksiyonundan okur
    fe = inspect.getsource(PaperBroker.fill_entry)
    assert "entry_limit_price(" in fe and "entry_law()" in fe


@pytest.mark.parametrize("trigger,atr,beklenen", [
    (100.0, 1.0, 100.5),      # 0.5*ATR = 0.50 < %1*100 = 1.00 → ATR bacağı bağlar
    (100.0, 4.0, 101.0),      # 0.5*ATR = 2.00 > 1.00        → yüzde tavanı bağlar
    (100.0, None, 101.0),     # ATR ölçülemedi               → yalnız yüzde tavanı
    (100.0, 0.0, 101.0),      # ATR sıfır = ölçülemedi ile aynı dürüst muamele
])
def test_e1_limit_formula_is_the_min_of_two_caps(sandbox_state, trigger, atr, beklenen):
    # MEKANİZMA: hesap `min(mult·ATR, pct·tetik)` mi? Yasa kaynağı kart varsayılanına sabit
    # (operatör kararı 2026-08-03 yürürlükteki bacağı 100·ATR/%4 yaptı — orada `min()` hiç ayırt
    # etmez ve dört parametrenin dördü de aynı sayıya çökerdi, yani formül ölçülmez olurdu).
    assert BR.entry_limit_price(trigger, atr, BR.entry_law(KART_YASASI)) == pytest.approx(beklenen)


def test_e1_both_engines_agree_on_the_boundary_price(sandbox_state, monkeypatch):
    """DAVRANIŞSAL EŞDEĞERLİK: aynanın gönderdiği limit ile iç motorun dolum SINIRI aynı sayıdır.
    Bir bps ayrışsalardı defter "ayna doldu, iç motor doldurmadı" satırları üretir ve bunu kimse
    bir yasa farkı olarak okumazdı (denetimin bulduğu sınıfın ta kendisi)."""
    cap = {}

    class _R:
        status_code = 200

        @staticmethod
        def json():
            return {"id": "o1", "status": "new"}

    monkeypatch.setenv("ALPACA_PAPER_KEY", "k")
    monkeypatch.setenv("ALPACA_PAPER_SECRET", "s")
    from meridian import secrets
    secrets.clear_cache()
    monkeypatch.setattr(alpaca, "asset_tradable", lambda s: True)
    monkeypatch.setattr(alpaca.httpx, "post",
                        lambda url, headers=None, json=None, timeout=None: (cap.update(body=json), _R)[1])

    res = alpaca.submit_plan(PLAN, equity=100_000, atr=1.0, ref_price=99.0)
    ayna_limit = cap["body"]["limit_price"]
    assert res["law"]["mode"] == "stop_limit"

    b = _broker()
    # limit fiyatının BİR KURUŞ ÜSTÜNDE açılış → iç motor doldurmaz
    assert b.fill_entry(PLAN, ayna_limit + 0.01, "2026-08-01", 100_000.0, atr=1.0) is None
    # tam limitte açılış → dolar (sınır DAHİL, iki motorda da)
    assert b.fill_entry(PLAN, ayna_limit, "2026-08-01", 100_000.0, atr=1.0) is not None


def test_e1_gap_path_1_normal_trigger_is_a_stop_limit(sandbox_state):
    # MEKANİZMA (gap yolu 1): yasa kaynağı kart varsayılanında sabit — ölçülen şey DAL SEÇİMİ ve
    # limitin o dalda nasıl kurulduğu (operatör kararı 2026-08-03 yalnız tavanları değiştirdi).
    d = BR.entry_order_decision(100.0, ref_price=99.0, atr=1.0, cfg=BR.entry_law(KART_YASASI))
    assert d["mode"] == "stop_limit" and d["olay"] == BR.EV_STOP_LIMIT
    # TIF: "day" → "gtc" (E1-v2, 2026-08-07). Bracket'ta `time_in_force` TEKTİR ve KORUMA
    # bacaklarına da uygulanır; DAY, dolmuş pozisyonların stop'unu her seans kapanışında
    # öldürüyordu (ölçüm: 2026-08-06 20:00-20:02Z, dört pozisyon çıplak). Kart revizyonu
    # EXE-2026-001-R1. Bu satırın ölçtüğü DAL SEÇİMİ değişmedi.
    assert d["gap_at_submit"] is False and d["limit"] == 100.5 and d["tif"] == "gtc"


def test_e1_gap_path_2_price_above_trigger_becomes_a_marketable_limit(sandbox_state):
    """KÖK NEDEN: gönderim anında fiyat tetiğin ÜSTÜNDEyse buy-stop GEÇERSİZDİR."""
    # MEKANİZMA (gap yolu 2): yasa kaynağı kart varsayılanında sabit — bkz. gap yolu 1.
    d = BR.entry_order_decision(100.0, ref_price=100.0, atr=1.0, cfg=BR.entry_law(KART_YASASI))
    assert d["mode"] == "marketable_limit" and d["olay"] == BR.EV_GAP_MARKETABLE
    assert d["gap_at_submit"] is True and d["limit"] == 100.5


def test_e1_gap_path_3_veto_grid_point_blocks_BOTH_engines(sandbox_state, monkeypatch):
    """İPTAL (gap-risk vetosu) grid noktası: ayna emri GÖNDERMEZ ve iç motor da DOLDURMAZ.
    Yalnız biri uygulasaydı veto bir hizalama değil YENİ bir ayrışma olurdu."""
    veto = {"limit_atr_mult": 0.5, "limit_pct_cap": 0.01, "gap_behavior": BR.GAP_VETO, "tif": "day"}
    _asil = BR.entry_law           # yamalanan adı ÇAĞIRMA (sonsuz özyineleme) — aslı yakalanır
    monkeypatch.setattr(BR, "entry_law", lambda override=None: _asil(veto))
    d = BR.entry_order_decision(100.0, ref_price=100.0, atr=1.0)
    assert d["mode"] == "veto" and d["olay"] == BR.EV_GAP_VETO

    from meridian import secrets
    monkeypatch.setenv("ALPACA_PAPER_KEY", "k")
    monkeypatch.setenv("ALPACA_PAPER_SECRET", "s")
    secrets.clear_cache()

    def _boom(*a, **k):
        raise AssertionError("veto edilmiş plan için AYNAYA emir gitti")
    monkeypatch.setattr(alpaca.httpx, "post", _boom)
    res = alpaca.submit_plan(PLAN, equity=100_000, atr=1.0, ref_price=100.0)
    assert res["ok"] is False and res["veto"] is True and res["reachable"] is True

    rej: dict = {}
    b = _broker()
    assert b.fill_entry(PLAN, 100.2, "2026-08-01", 100_000.0, atr=1.0,
                        gap_at_submit=True, reject_out=rej) is None
    assert rej["reason"] == BR.EV_GAP_VETO


def test_e1_gap_at_submit_none_never_vetoes(sandbox_state, monkeypatch):
    """BEYAN EDİLMİŞ KAPSAM FARKI: replay'de "gönderim anı" YOKTUR. `gap_at_submit=None` vetoyu
    ATEŞLEMEZ — ve bu sessiz bir kaçış değil, yazılı bir sınırdır (bkz. fill_entry docstring)."""
    veto = {"limit_atr_mult": 0.5, "limit_pct_cap": 0.01, "gap_behavior": BR.GAP_VETO, "tif": "day"}
    _asil = BR.entry_law
    monkeypatch.setattr(BR, "entry_law", lambda override=None: _asil(veto))
    b = _broker()
    assert b.fill_entry(PLAN, 100.2, "2026-08-01", 100_000.0, atr=1.0, gap_at_submit=None) is not None


def test_e1_missed_limit_is_measured_not_swallowed(sandbox_state, monkeypatch):
    """Açılış limitin üstündeyse dolum YOK — ama kaçan işlem ADLANDIRILIR ve aşımı bps ile ölçülür.
    Eski kod bu durumda ya doldurur (yasa yok) ya da sessizce None dönerdi (ölçüm yok)."""
    # MEKANİZMA: ölçülen şey KAÇAN DOLUMUN ADLANDIRILMASI + aşım hesabı. Yasa kaynağı kart
    # varsayılanına sabit (operatör kararı 2026-08-03: yürürlükte limit %4'tür ve bu bar dolardı —
    # o zaman "kaçan dolum" mekanizması hiç koşmaz, yani ölçüm boşa düşerdi).
    _kart_yasasini_sabitle(monkeypatch)
    rej: dict = {}
    b = _broker()
    assert b.fill_entry(PLAN, 102.0, "2026-08-01", 100_000.0, atr=1.0, reject_out=rej) is None
    assert rej["reason"] == BR.EV_MISSED_LIMIT
    assert rej["limit"] == 100.5 and rej["open"] == 102.0
    assert rej["asim_bps"] == pytest.approx((102.0 / 100.5 - 1) * 10000, abs=0.01)   # satır 3 haneye yuvarlar
    assert rej["plan_id"] == PLAN["id"]          # cf defteriyle BİRLEŞTİRME anahtarı


def test_e1_limit_cap_never_loosens_the_max_chase_ceiling(sandbox_state):
    """YÜRÜRLÜK ÇİVİSİ (eski ad: `test_e1_limit_cap_is_tighter_than_the_max_chase_ceiling`).

    İKİ TAVANIN İLİŞKİSİ DEĞİŞMEDİ — daima DAHA SIKI olan bağlar — ama HANGİ tarafın sıktığı
    değişti: OPERATÖR KARARI 2026-08-03 (goal.yaml `execution_v2`; kart EXE-2026-001 hükmü, ölçüm
    research/olcumler/e1_grid_2026-08-03) limit tavanını %1 → %4'e çıkardı, yani limit tavanı artık
    `MAX_ENTRY_GAP_PCT` DIŞ ZARFIYLA TAM EŞİTTİR ve bağlayan taraf dış zarftır.

    Çivinin yönü bu yüzden `<=`: limit tavanı dış zarfı GEVŞETEMEZ (aşsaydı %4 felaket-gap koruması
    sessizce ölürdü), eşit olabilir. Eşitlikte hangi kapının bağladığı da ölçülür: `fill_entry`te
    chase kapısı limit kapısından ÖNCE koşar, dolayısıyla ret nedeni `max_chase` diye adlandırılır
    — iki tavan ÇELİŞMEZ, yalnız adlandırma dış zarfa düşer."""
    zarf = 100.0 * (1 + BR.MAX_ENTRY_GAP_PCT)
    assert BR.entry_limit_price(100.0, None) <= zarf, \
        "limit tavanı %4 chase zarfının ÜSTÜNE çıktı — dış zarf fiilen ölü, iki tavan çelişiyor"
    assert BR.entry_limit_price(100.0, None) == pytest.approx(zarf), \
        "yürürlükte iki tavan EŞİT olmalı (operatör kararı 2026-08-03: limit_pct_cap = MAX_ENTRY_GAP_PCT)"
    # (a) zarfın ÜSTÜNDE açan bar: eşitlikte bağlayan taraf dış zarftır
    rej: dict = {}
    assert _broker().fill_entry(PLAN, zarf + 0.01, "2026-08-01", 100_000.0, reject_out=rej) is None
    assert rej["reason"] == "max_chase", f"eşitlikte dış zarf bağlamadı — sıralama ters: {rej!r}"
    # (b) zarfın İÇİNDE açan tetik-ÜSTÜ bar artık DOLAR — kararın amaçlanan etkisi (kaçan dolumlar
    # geriye-dönük defterde sistematik kazanandı; E1 grid'inin üç noktası da zararlıydı)
    assert _broker().fill_entry(PLAN, 103.0, "2026-08-01", 100_000.0) is not None, \
        "yürürlükte %4 zarfının içindeki tetik-üstü açılış dolmalı (E1 bacağı BAĞLAMAZ)"


def test_e1_config_selects_the_grid_point_and_clamps_garbage(sandbox_state):
    assert BR.entry_law({"limit_atr_mult": 0.25, "limit_pct_cap": 0.005})["limit_pct_cap"] == 0.005
    assert BR.entry_law({"gap_behavior": "cancel"})["gap_behavior"] == BR.GAP_VETO
    # bozuk/anlamsız değer SESSİZCE geçmez — varsayılana düşer
    for kotu in ({"limit_pct_cap": -1}, {"limit_pct_cap": "abc"}, {"limit_pct_cap": 5.0},
                 {"gap_behavior": "whatever"}):
        law = BR.entry_law(kotu)
        assert law["limit_pct_cap"] == BR.ENTRY_LIMIT_PCT_CAP or law["gap_behavior"] == BR.GAP_MARKETABLE


def test_e1_execution_law_is_immutable_to_the_agent(sandbox_state):
    """İcra yasası ve maliyet bandı goal.yaml'dadır ve Hermes onlara DOKUNAMAZ: bir ajan kendi
    dolum fiyatını ya da kendi karnesinin paydasını seçemez."""
    g = config.goal()
    assert "execution_v2" in g and "pessimistic_band_v2" in g
    assert {"execution_v2", "pessimistic_band_v2"} <= guard.GOAL_KEYS
    for key in ("execution_v2", "pessimistic_band_v2"):
        v = guard.validate_change({"variable": key, "new": 1}, config.default_strategy()["params"],
                                  config.bounds(), g, [], 0)
        assert v.ok is False


# =================================================================================================
# E2 — SLİPAJ DEFTERİ
# =================================================================================================
def test_e2_bps_helper_is_honest_about_unmeasurable_sides(sandbox_state):
    assert BR.bps_delta(101.0, 100.0) == 100.0
    assert BR.bps_delta(99.0, 100.0) == -100.0
    for a, b in ((None, 100.0), (100.0, None), (100.0, 0.0), ("x", 100.0)):
        assert BR.bps_delta(a, b) is None, "ölçülemeyen taraf 0.0 yazıldı — 'slipaj yok' yalanı"


def test_e2_fill_patch_writes_both_bps(sandbox_state):
    """Dolum geldiğinde satıra İKİ bps yazılır: resmî açılışa göre (mikroyapı faturası) ve limite
    göre (yasa bağladı mı?). İkinci çağrı satırı YENİDEN yazmaz (idempotent)."""
    store.append_jsonl(loop.ENTRY_LEDGER, {
        "date": "2026-07-31", "plan_id": "P-2026-07-31-AAA", "ticker": "AAA", "motor": "ayna",
        "entry_trigger": 100.0, "limit": 100.5, "karar": "submitted", "fill": None,
        "fill_vs_resmi_acilis_bps": None, "fill_vs_limit_bps": None})
    orders = {"P-2026-07-31-AAA": {"status": "filled", "filled_avg_price": "100.40",
                                   "filled_qty": "50"}}
    rap = loop._patch_entry_slippage(orders, {"AAA": 100.0}, "2026-07-31")
    assert rap == {"eslesen": 1, "yazilan": 1, "acilis_yok": 0}
    row = store.read_jsonl(loop.ENTRY_LEDGER)[0]
    assert row["fill"] == 100.4
    assert row["fill_vs_resmi_acilis_bps"] == pytest.approx(40.0, abs=0.01)   # açılışa göre +40 bps
    assert row["fill_vs_limit_bps"] == pytest.approx(-9.95, abs=0.05)         # tavanın ALTINDA doldu
    assert loop._patch_entry_slippage(orders, {"AAA": 100.0}, "2026-08-01")["yazilan"] == 0


def test_e2_official_open_is_never_substituted(sandbox_state):
    """Resmî açılış yoksa bps None kalır. Dolum fiyatını açılış yerine koymak, ölçmek istediğimiz
    farkı TANIMI GEREĞİ sıfır yapardı — ölçümün kendi kendini yalanlaması."""
    store.append_jsonl(loop.ENTRY_LEDGER, {
        "date": "2026-07-31", "plan_id": "P-X", "ticker": "ZZZ", "motor": "ayna",
        "limit": 100.5, "karar": "submitted", "fill": None, "resmi_acilis": None})
    loop._patch_entry_slippage({"P-X": {"status": "filled", "filled_avg_price": 100.4}}, {}, "d")
    row = store.read_jsonl(loop.ENTRY_LEDGER)[0]
    assert row["fill"] == 100.4 and row["fill_vs_resmi_acilis_bps"] is None
    assert row["fill_vs_limit_bps"] is not None      # limit ölçülü → o bps YAZILIR


def test_e2_reject_reason_classes_name_the_root_cause(sandbox_state):
    assert loop._reject_class("stop price must be greater than current price") == "stop_vs_current"
    assert loop._reject_class(None, veto=True) == "gap_veto"
    assert loop._reject_class("timeout", reachable=False) == "unreachable"
    assert loop._reject_class("insufficient buying power") == "buying_power"
    assert loop._reject_class("bir şey oldu") == "diger"


def test_e2_summary_counts_rejects_fills_and_engine_disagreement(sandbox_state):
    rows = [
        {"date": "2026-07-31", "plan_id": "P1", "ticker": "A", "motor": "ayna", "karar": "submitted",
         "limit": 100.5, "fill": 100.4, "fill_vs_resmi_acilis_bps": 40.0, "fill_vs_limit_bps": -9.9,
         "emir_tipi": "limit", "tif": "day"},
        {"date": "2026-07-31", "plan_id": "P2", "ticker": "B", "motor": "ayna", "karar": "rejected",
         "red_sinifi": "stop_vs_current", "red_nedeni": "stop price ...", "fill": None},
        {"date": "2026-07-31", "plan_id": "P1", "ticker": "A", "motor": "ic", "karar": "fill",
         "fill": 100.4, "fill_vs_resmi_acilis_bps": 40.0},
        {"date": "2026-07-31", "plan_id": "P3", "ticker": "C", "motor": "ic",
         "karar": "entry_missed_limit", "fill": None},
    ]
    for r in rows:
        store.append_jsonl(loop.ENTRY_LEDGER, r)
    s = an.entry_execution_summary(days=None)
    assert s["ayna"]["karar_dagilimi"] == {"submitted": 1, "rejected": 1}
    assert s["ayna"]["red_sinifi_dagilimi"] == {"stop_vs_current": 1}
    assert s["ayna"]["red_orani"] == 0.5
    assert s["ayna"]["dolum"]["n_dolan"] == 1
    assert s["ayna"]["dolum"]["fill_vs_limit_bps"]["ort"] == -9.9
    assert s["ic_motor"]["kacan_limit_n"] == 1 and s["ic_motor"]["dolmama_orani"] == 0.5
    assert s["mutabakat"]["ortak_plan_n"] == 1 and s["mutabakat"]["ayrisan_n"] == 0


def test_e2_kapi_bucket_counts_gates_without_touching_the_kill_denominator(sandbox_state):
    """`motor="kapi"` KENDİ KOVASINDA sayılır ve kill paydasına SIZMAZ.

    Bu testin asıl çivisi son assert: `dolmama_orani` YALNIZ iç motorun icra kararlarından
    hesaplanır. Kapıda düşen plan hiç icra edilmedi — paydaya girseydi kartın kill eşiği (0.40)
    kod değişikliğiyle sessizce kayardı ve kill-list DOKUNULMAZDIR (kart EXE-2026-001)."""
    rows = [
        {"date": "2026-08-02", "plan_id": "P1", "ticker": "A", "motor": "ic", "karar": "fill",
         "fill": 100.4},
        {"date": "2026-08-02", "plan_id": "P2", "ticker": "B", "motor": "ic",
         "karar": "entry_missed_limit", "fill": None},
        {"date": "2026-08-02", "plan_id": "P3", "ticker": "C", "motor": "kapi",
         "karar": "armed_dropped_halt", "fill": None, "red_detay": {"kapi": "halt"}},
        {"date": "2026-08-02", "plan_id": "P4", "ticker": "D", "motor": "kapi",
         "karar": "armed_dropped_halt", "fill": None, "red_detay": {"kapi": "halt"}},
        {"date": "2026-08-02", "plan_id": "P5", "ticker": "E", "motor": "kapi",
         "karar": "armed_dropped_slot_full", "fill": None,
         "red_detay": {"kapi": "slot_full", "acik": 3}},
    ]
    for r in rows:
        store.append_jsonl(loop.ENTRY_LEDGER, r)
    s = an.entry_execution_summary(days=None)
    assert s["kapi"]["n"] == 3
    assert s["kapi"]["kapi_dagilimi"] == {"halt": 2, "slot_full": 1}
    assert s["ic_motor"]["n"] == 2
    assert s["ic_motor"]["dolmama_orani"] == 0.5, \
        "kapi satırları kill paydasına sızdı — eşik kod değişikliğiyle kaydı"
    assert s["n"] == 5      # üst-düzey sayım HAM kalır: kova ayrımı satırları saklamaz


def test_e2_kapi_gate_falls_back_to_the_decision_prefix(sandbox_state):
    """`red_detay` yoksa gate `karar`ın `armed_dropped_` önekinden soyulur — satır "?"e düşmez."""
    store.append_jsonl(loop.ENTRY_LEDGER, {
        "date": "2026-08-02", "plan_id": "P9", "ticker": "Z", "motor": "kapi",
        "karar": "armed_dropped_breaker", "fill": None})
    s = an.entry_execution_summary(days=None)
    assert s["kapi"]["kapi_dagilimi"] == {"breaker": 1}


def test_e2_empty_ledger_reports_a_state_not_a_zero(sandbox_state):
    s = an.entry_execution_summary()
    assert s["n"] == 0 and "defter boş" in s["durum"]
    assert s["ayna"]["red_orani"] is None and s["ic_motor"]["dolmama_orani"] is None
    assert s["ayna"]["dolum"]["fill_vs_resmi_acilis_bps"]["ort"] is None
    assert s["kapi"]["n"] == 0 and s["kapi"]["kapi_dagilimi"] == {}


# =================================================================================================
# E3 — KÖTÜMSER MALİYET BANDI
# =================================================================================================
def test_e3_band_charges_only_the_difference_on_the_entry_leg(sandbox_state):
    b = an.pessimistic_band()
    # açılış spread 20 bps → yarısı 10 bps ödenir; model zaten 5 bps kesiyor → EK 5 bps
    assert b["ek_bps_giris"] == pytest.approx(5.0) and b["taban"] == "literatur"


def test_e3_twin_column_sits_next_to_the_verdict_without_touching_it(sandbox_state):
    """İKİZ SÜTUN HÜKME GİRMEZ: dört ölçüt sözleşmesi (`passed/4`) korunur."""
    store.write_jsonl("trades.jsonl", [
        {"id": f"T{i:05d}", "ts_open": "2026-01-05", "ts_close": "2026-01-09", "ticker": "AAA",
         "entry": 100.0, "qty": 100, "exit": 101.0, "pnl_dollars": 100.0, "pnl_pct": 0.01,
         "costs": 10.0, "r_multiple": 0.2, "regime": "trend", "score": 70, "setup": "s",
         "strategy_version": 1, "plan_id": f"P-{i}", "bars_held": 4} for i in range(40)])
    v = an.result_verdict()
    assert len(v["criteria"]) == 4 and v["passed"] + v["failed"] + v["unmeasured"] + v["zayif"] == 4
    k = v["net_kotumser"]
    assert k["hukme_girmez"] is True
    # 40 işlem × $10.000 notional × 5 bps = $200
    assert k["ek_maliyet"] == pytest.approx(200.0, abs=0.01)
    assert k["net_kotumser"] == pytest.approx(k["net"] - k["ek_maliyet"], abs=0.01)
    assert an.profit_waterfall()["net_kotumser"]["band"]["taban"] == "literatur"


def test_e3_none_paths_never_invent_a_number(sandbox_state):
    """Notional ölçülemeyen satır ATLANIR ve SAYILIR; defter boşsa sütun None döner."""
    assert an.net_kotumser()["net_kotumser"] is None          # defter boş
    store.write_jsonl("trades.jsonl", [{"id": "T1", "pnl_dollars": 10.0},      # entry/qty YOK
                                       {"id": "T2", "pnl_dollars": 10.0, "entry": 100.0, "qty": 10}])
    k = an.net_kotumser()
    assert k["n_notional_yok"] == 1 and k["n_olculen"] == 1
    assert k["ek_maliyet"] == pytest.approx(1000 * 0.0005, abs=1e-9)


def test_e3_empirical_update_measures_but_never_writes_goal_yaml(sandbox_state):
    """`goal.yaml` DEĞİŞMEZDİR: bu yol ÖLÇER, uygulamaz — ve n eşiğin altındayken sayı ÜRETMEZ."""
    before = (config.STATE / "goal.yaml").read_bytes()
    for i in range(an.BAND_MIN_N - 1):
        store.append_jsonl(loop.ENTRY_LEDGER, {"date": "2026-07-31", "motor": "ayna", "plan_id": f"P{i}",
                                               "fill": 100.4, "fill_vs_resmi_acilis_bps": 12.0})
    r = an.pessimistic_band_update()
    assert r["ampirik_bps"] is None and "HENÜZ YOK" in r["neden"]
    store.append_jsonl(loop.ENTRY_LEDGER, {"date": "2026-07-31", "motor": "ayna", "plan_id": "PX",
                                           "fill": 100.4, "fill_vs_resmi_acilis_bps": 12.0})
    r2 = an.pessimistic_band_update()
    assert r2["ampirik_bps"] == pytest.approx(12.0) and r2["n_olculen"] == an.BAND_MIN_N
    assert "operatör eylemidir" in r2["uygulama"]
    assert (config.STATE / "goal.yaml").read_bytes() == before, "DEĞİŞMEZ dosyaya yazıldı"


def test_e3_empirical_band_wins_over_literature_when_present(sandbox_state):
    g = config.goal()
    g["pessimistic_band_v2"] = {**g["pessimistic_band_v2"], "ampirik_bps": 30.0}
    b = an.pessimistic_band(goal=g)
    assert b["taban"] == "ampirik" and b["ek_bps_giris"] == pytest.approx(25.0)


# =================================================================================================
# E4 — GECE / GÜNDÜZ AYRIŞTIRMASI
# =================================================================================================
def _sentetik_barlar(rows):
    return pd.DataFrame([{"date": pd.Timestamp(d), "open": o, "high": max(o, c) * 1.01,
                          "low": min(o, c) * 0.99, "close": c, "volume": 1e6}
                         for d, o, c in rows])


def _bar_yamasi(monkeypatch, df):
    class _D:
        @staticmethod
        def load_bars(t, s, e, use_cache=True):
            return df
    import meridian.adapters as _ad
    monkeypatch.setattr(_ad, "data", _D, raising=False)
    import sys
    monkeypatch.setitem(sys.modules, "meridian.adapters.data", _D)


def test_e4_identity_night_plus_day_equals_the_held_path(sandbox_state, monkeypatch):
    """TAM ÖZDEŞLİK: close_N − open_0 = Σ(close−open) + Σ(open−close_prev). Yaklaşık değil, tam."""
    df = _sentetik_barlar([("2026-01-02", 100.0, 100.0),   # giriş gününün ÖNCESİ (gap paydası)
                           ("2026-01-05", 102.0, 103.0),   # gap +2 (satın alınan gece), gündüz +1
                           ("2026-01-06", 104.0, 103.0),   # gece +1, gündüz −1
                           ("2026-01-07", 106.0, 108.0)])  # gece +3, gündüz +2
    _bar_yamasi(monkeypatch, df)
    store.write_jsonl("trades.jsonl", [
        {"id": "T00001", "ts_open": "2026-01-05", "ts_close": "2026-01-07", "ticker": "AAA",
         "entry": 102.0, "qty": 10, "exit": 107.0, "pnl_pct": 0.049, "pnl_dollars": 50.0,
         "bars_held": 2, "setup": "breakout_vcp", "regime": "trend"}])
    r = an.night_day_split()
    assert r["n_olculebilir"] == 1 and r["n_olculemeyen"] == 0
    g = r["genel"]
    # gündüz = (103−102)+(103−104)+(108−106) = +2 ; gece = (104−103)+(106−103) = +4 ; yol = 108−102 = 6
    assert g["gunduz"] == pytest.approx(2 / 102.0, abs=1e-5)      # özet 5 haneye yuvarlar
    assert g["gece"] == pytest.approx(4 / 102.0, abs=1e-5)
    assert g["yol"] == pytest.approx(g["gece"] + g["gunduz"], abs=2e-5)
    # GİRİŞ GAP'İ tutulan yolun İÇİNDE DEĞİL, ayrı ölçülür: 102/100 − 1 = +200 bps
    assert r["giris_gap_bps"]["ort"] == pytest.approx(200.0, abs=0.01)
    # icra farkı = işlemin gerçek getirisi − yol (çıkış seviyesi + friksiyon)
    assert g["icra_farki"] == pytest.approx(0.049 - g["yol"], abs=2e-5)


def test_e4_seed_trades_are_labelled_training_in_their_own_row(sandbox_state, monkeypatch):
    """BT-1 AYRIŞTIRMASI: tohum satırı `training` etiketiyle KENDİ kırılımında durur; canlı
    kanıtla aynı ortalamada toplanmaz."""
    df = _sentetik_barlar([("2026-01-02", 100.0, 100.0), ("2026-01-05", 101.0, 102.0),
                           ("2026-01-06", 103.0, 104.0)])
    _bar_yamasi(monkeypatch, df)
    from meridian import ledgerstamp
    ortak = {"ts_open": "2026-01-05", "ts_close": "2026-01-06", "ticker": "AAA", "entry": 101.0,
             "qty": 10, "pnl_pct": 0.02, "pnl_dollars": 20.0, "bars_held": 1, "setup": "s"}
    store.write_jsonl("trades.jsonl", [
        {"id": "T1", **ortak, ledgerstamp.FIELD: ledgerstamp.REPLAY_SEED},
        {"id": "T2", **ortak, ledgerstamp.FIELD: ledgerstamp.LIVE_PAPER},
        {"id": "T3", **ortak},                      # damgasız → belirsiz
    ])
    r = an.night_day_split()
    assert set(r["kaynak_kirilim"]) == {"training", "live_paper", "belirsiz"}
    assert r["kaynak_kirilim"]["training"]["n"] == 1
    assert {c["kaynak"] for c in r["capraz"]} == {"training", "live_paper", "belirsiz"}
    assert all(c["tutus_dilimi"] == "1g" for c in r["capraz"])   # BT-1 dilim çaprazı


def test_e4_unjoinable_trades_are_counted_not_guessed(sandbox_state, monkeypatch):
    """Barı olmayan / seansı barlarda bulunmayan işlem HİÇBİR ortalamaya girmez ve SAYILIR."""
    df = _sentetik_barlar([("2026-01-05", 101.0, 102.0), ("2026-01-06", 103.0, 104.0)])
    _bar_yamasi(monkeypatch, df)
    store.write_jsonl("trades.jsonl", [
        {"id": "T1", "ts_open": "2026-01-05", "ts_close": "2026-01-06", "ticker": "AAA",
         "entry": 101.0, "qty": 10, "pnl_pct": 0.02, "bars_held": 1},
        {"id": "T2", "ts_open": "2020-03-03", "ts_close": "2020-03-04", "ticker": "AAA",
         "entry": 10.0, "qty": 1, "pnl_pct": 0.5, "bars_held": 1},           # seans barlarda YOK
    ])
    r = an.night_day_split()
    assert r["n"] == 2 and r["n_olculebilir"] == 1 and r["n_olculemeyen"] == 1
    # giriş gap'i yalnız ÖNCEKİ barı olan işlemden ölçülür — burada yok, payda dürüstçe 0
    assert r["giris_gap_bps"]["n"] == 0


def test_e4_empty_ledger_says_why(sandbox_state):
    r = an.night_day_split()
    assert r["genel"] is None and r["neden_bos"] == "defter boş"


# =================================================================================================
# YASA 6 — ÜÇ ÖLÇÜMÜN DE DIŞ OKUYUCUSU VAR
# =================================================================================================
def test_law6_all_three_measurements_are_served_by_diagnostics(sandbox_state):
    from meridian import api
    src = inspect.getsource(api.api_diagnostics)
    for fn in ("entry_execution_summary", "pessimistic_band_update", "night_day_split"):
        assert fn in src, f"{fn} hiçbir uçtan servis edilmiyor (YASA 6)"
    assert '"icra"' in src


def test_law6_entry_ledger_has_a_reader_in_another_module(sandbox_state):
    """Defteri loop YAZAR, analytics OKUR — 'kanıt üretip tüketmeme' sınıfı kapalı."""
    from meridian import codelaw
    assert loop.ENTRY_LEDGER == an.ENTRY_LEDGER
    rap = codelaw.report()
    assert loop.ENTRY_LEDGER not in rap["unread"]
    assert rap["artifact_violations"] == []


def test_law6_kapi_bucket_has_a_dashboard_reader(sandbox_state):
    """ZİNCİRİN SON HALKASI: analytics kovayı sayıyor, api onu `icra.slipaj` altında servis ediyor,
    PANO da okumak zorunda. Okuyucusuz bir sayı YASA 6'nın tam olarak yasakladığı şeydir —
    `kapi` kovası bu tur açılana kadar (loop._armed_drop_row'un beyan ettiği borç) tam da öyleydi."""
    app = (pathlib.Path(__file__).resolve().parents[1] / "meridian" / "web" / "app.js").read_text()
    assert "kapi_dagilimi" in app, "pano E2 `kapi` kovasını okumuyor — ölçüm okuyucusuz (YASA 6)"
    assert "slipaj" in app, "pano `icra.slipaj` özetine hiç dokunmuyor"


def test_law6_slipaj_summary_has_a_dashboard_reader(sandbox_state):
    """`kapi` kovası dışında KALAN E2 yükü de okuyucusuzdu: ret SINIFI, iç motorun kill ölçütü,
    kill EŞİĞİ ve iki-motor ayrışması `/api/diagnostics`te tam servis ediliyor ama hiçbir yüzey
    basmıyordu. Dördü ayrı ayrı assert edilir: zincir koptuğunda HANGİ okuyucunun düştüğü
    testin mesajından okunur, "pano bir şeyi okumuyor" gibi bulanık bir kırmızı gelmez."""
    app = (pathlib.Path(__file__).resolve().parents[1] / "meridian" / "web" / "app.js").read_text()
    assert "red_sinifi_dagilimi" in app, (
        "pano ayna RET SINIFI dağılımını okumuyor — kartın (a) ölçütü (`stop_vs_current` sıfıra "
        "inmeli) hiçbir yüzeyde görünmüyor (YASA 6)")
    assert "dolmama_orani" in app, (
        "pano iç motorun `dolmama_orani`sını okumuyor — kart EXE-2026-001'in KILL ÖLÇÜTÜ "
        "okuyucusuz ölçüm olarak duruyor (YASA 6)")
    assert "kill_esigi" in app, (
        "pano eşiği YÜKTEN okumuyor — eşik panoya sabit yazılırsa (0.40) analytics'teki değişiklik "
        "ekrana yansımaz ve pano eski eşiği savunmayı sürdürür (C10 dersi: sabit sayı yasak)")
    assert "ayrisan_n" in app, (
        "pano iki-motor mutabakatını okumuyor — `ayrisan_n` kartın (c) ölçütü, ayrışma gizlenemez "
        "(YASA 6)")


def test_law6_e3_e4_have_dashboard_readers(sandbox_state):
    """`icra` bloğunun kalan İKİ üyesi de okuyucusuzdu: E3 (kötümser band) ve E4 (gece/gündüz)
    `/api/diagnostics`te tam servis ediliyor ama hiçbir yüzey basmıyordu — E2'nin bu tur kapattığı
    boşluğun aynısı. Dört assert ayrı: zincir koptuğunda HANGİ okuyucunun düştüğü mesajdan okunur."""
    app = (pathlib.Path(__file__).resolve().parents[1] / "meridian" / "web" / "app.js").read_text()
    assert "ek_bps_giris" in app, (
        "pano E3'ün YÜRÜRLÜKTEKİ bandını okumuyor — girişe yüklenen ek maliyet (`ek_bps_giris`) "
        "hiçbir yüzeyde görünmüyor, yani hükmün maliyet varsayımı okuyucusuz (YASA 6)")
    assert "ampirik_bps" in app and "min_n" in app, (
        "pano E3'ün AMPİRİK ölçümünü ya da onun asgari örneklemini okumuyor — `min_n` yükten "
        "okunmalı; panoya sabit (20) yazılırsa analytics'teki BAND_MIN_N değişikliği ekrana "
        "yansımaz ve pano eski asgariyi savunmayı sürdürür (C10 dersi: sabit sayı yasak)")
    assert "gece_payi" in app and "icra_farki" in app, (
        "pano E4'ün genel özetini okumuyor — `gece_payi` (kâr hangi bacaktan) ve `icra_farki` "
        "(işlem − yol = çıkış seviyesi + friksiyon) okuyucusuz ölçüm olarak duruyor (YASA 6)")
    assert "hucre_min_n" in app, (
        "pano E4'ün ince-hücre eşiğini YÜKTEN okumuyor — panoya sabit (5) yazılırsa "
        "NIGHTDAY_HUCRE_MIN_N değişikliği ekrana yansımaz ve sönük satırların gerekçesi yalan "
        "olur (C10 dersi: sabit sayı yasak)")


def test_e2_ledger_rows_are_json_serialisable(sandbox_state):
    """Defter satırı JSONL'e yazılabilir olmalı — karar sözlüğü içinde numpy/Timestamp taşımaz."""
    d = BR.entry_order_decision(100.0, ref_price=99.5, atr=1.0)
    assert json.loads(json.dumps(d)) == d


def test_e4_memo_is_invalidated_by_the_ledger_itself(sandbox_state, monkeypatch):
    """SÜREÇ-İÇİ MEMO defterin mtime'ına bağlıdır: defter değişince sonuç DEĞİŞİR. Zaman tabanlı
    bir TTL "bayat sayı kaç dakika gösterilebilir?" sorusunu açardı; burada cevap SIFIR."""
    df = _sentetik_barlar([("2026-01-02", 100.0, 100.0), ("2026-01-05", 101.0, 102.0),
                           ("2026-01-06", 103.0, 104.0)])
    _bar_yamasi(monkeypatch, df)
    satir = {"ts_open": "2026-01-05", "ts_close": "2026-01-06", "ticker": "AAA", "entry": 101.0,
             "qty": 10, "pnl_pct": 0.02, "bars_held": 1}
    store.write_jsonl("trades.jsonl", [{"id": "T1", **satir}])
    assert an.night_day_split()["n_olculebilir"] == 1
    store.write_jsonl("trades.jsonl", [{"id": "T1", **satir}, {"id": "T2", **satir}])
    assert an.night_day_split()["n_olculebilir"] == 2, "memo bayat sonucu servis etti"

"""test_golge_v2_yasam_dongusu_v132.py — GÖLGE-v2 YAŞAM-DÖNGÜSÜ MOTORU + DAYANIKLILIK ÇİFTİ.

Turun ÇİVİLERİ:
  A) İCRA YASASI ÇAĞRILIR: fill (gap koruması dahil), kısmi satış, breakeven, erken itlaf — hepsi
     ÜRETİMİN `broker.PaperBroker` + `strategy.manage_position` yolundan geçer.
  B) NO-OP KOL REDDİ (E4 tuzağı): kontrol kolundan hiçbir OKUNAN anahtarda ayrışmayan kol sete
     giremez; `LIFECYCLE_READ_DEFAULTS` tablosu kaynaktaki LİTERAL varsayılanlarla çakılıdır.
  C) KİMLİK AYRIKLIĞI: kapanan gölge işlemi `SV-` öneklidir ve `ledgers.PLAN_ID_RE` ile ASLA eşleşmez.
  D) TOHUMLAMA (N00005) yalnız defter BOŞKEN koşar ve satırları `seeded: true` damgası taşır;
     satırın kendi `ts`i GERÇEK yazım anıdır (retro-damga yasağı).
  E) KARNE (YASA 6 tüketicisi): para sütunu `shadowlaw.ret_c_v3`tir; ölçülemeyen None'dır.
  F) DAYANIKLILIK ÇİFTİ: VM-dışı yedek çekici + A1 servis-ölümü bildirimi.

CANLI STATE'E YAZAN TEST YOK: hepsi `sandbox_state` içinde ya da `write=False` ile koşar.
"""
import ast
import os
import pathlib
import stat

import pandas as pd
import pytest

from meridian import codelaw, config, ledgers, shadow_lifecycle as sl, shadow_variants as sv, store

ROOT = pathlib.Path(__file__).resolve().parent.parent
D0 = "2026-07-29"
D1 = "2026-07-30"


# ============================ kurgu yardımcıları =================================================
def _frame(n=40, price=100.0, last=None):
    """Düz bir seri + isteğe bağlı SON bar. Deterministik: rastgelelik yok, her sayı elle konur."""
    dates = pd.bdate_range("2026-06-01", periods=n)
    rows = [{"open": price, "high": price, "low": price, "close": price, "volume": 2_000_000.0}
            for _ in range(n)]
    if last:
        rows[-1] = {"volume": 2_000_000.0, **last}
    df = pd.DataFrame(rows, index=pd.DatetimeIndex(dates, name="date"))
    return df


def _with_day(df, date, bar):
    d = pd.Timestamp(date)
    row = {"volume": 2_000_000.0, **bar}
    add = pd.DataFrame([row], index=pd.DatetimeIndex([d], name="date"))
    return pd.concat([df, add])


def _plan(tk="AAA", trig=100.0, stop=95.0, target=110.0, date=D0):
    return {"id": f"SV-{date}-{tk}", "date": date, "ticker": tk, "side": "long",
            "entry_trigger": trig, "stop": stop, "targets": [target], "profit_target": target,
            "r_per_share": trig - stop, "size_r": 1.0, "sector": "Tech", "score": 75,
            "setup": "breakout_vcp", "regime_at_plan": "trend_up", "strategy_version": 3,
            "skill_chain": ["s", "position-sizer", "pre-trade-discipline-gate"]}


def _book(**kw):
    bk = sl._new_book("VT")
    bk.update(kw)
    return bk


def _goal():
    return config.goal()


def _limits():
    return config.goal()["limits"]


def _step(bk, bars, *, date=D1, params=None, armed_next=(), regime_ok=True, seeded=False):
    return sl.step(bk, params or {}, date, lambda t: bars.get(t), regime_ok=regime_ok,
                   limits=_limits(), goal=_goal(), armed_next=list(armed_next), seeded=seeded)


# ============================ A) İCRA YASASI ÇAĞRILIR ============================================
def test_silahli_plan_ERTESI_ACILISTA_dolar(sandbox_state):
    """v1'in ölçemediği ilk şey: silahlanan bir kağıt plan GERÇEKTEN doluyor mu?"""
    bars = {"AAA": _with_day(_frame(), D1, {"open": 101.0, "high": 103.0, "low": 100.0, "close": 102.0})}
    bk = _book(armed=[{"plan": _plan(), "pivot": 99.0}])
    _step(bk, bars)
    assert "AAA" in bk["positions"], "silahlı plan dolmadı — fill yolu koşmuyor"
    p = bk["positions"]["AAA"]
    assert p["entry"] > 101.0, "kayma fiyatın İÇİNDE değil (broker yasası atlanmış)"
    assert p["pivot"] == 99.0, "yapı çizgisi pozisyona taşınmadı → erken itlaf ölçülemez"
    assert bk["armed"] == [], "silahlı set sıfırlanmadı"


def test_BOSLUK_korumalari_URETIMIN_yasasindan_gelir(sandbox_state):
    """`broker.py::PaperBroker.fill_entry`in iki koruması: tetiğin ÇOK üstünde açılışı kovalama, stop'un ALTINDA
    açılana hiç girme. Gölge kendi eşiğini yazsaydı iki motor sessizce ayrışırdı."""
    from meridian.broker import MAX_ENTRY_GAP_PCT
    yukari = 100.0 * (1.0 + MAX_ENTRY_GAP_PCT) + 1.0
    bars = {"AAA": _with_day(_frame(), D1, {"open": yukari, "high": yukari + 1, "low": yukari - 1,
                                            "close": yukari})}
    bk = _book(armed=[{"plan": _plan(), "pivot": 0.0}])
    _step(bk, bars)
    assert bk["positions"] == {}, "boşluk kovalama koruması koşmadı"

    bars = {"AAA": _with_day(_frame(), D1, {"open": 94.0, "high": 96.0, "low": 93.0, "close": 95.0})}
    bk = _book(armed=[{"plan": _plan(), "pivot": 0.0}])
    _step(bk, bars)
    assert bk["positions"] == {}, "stop'un altında açılan bara girildi"


def _pos(**kw):
    base = {"plan_id": "SV-2026-07-29-AAA", "ticker": "AAA", "side": "long", "entry": 100.0,
            "stop": 95.0, "trail_stop": 95.0, "target": 115.0, "qty": 100, "r_per_share": 5.0,
            "risk_dollars": 500.0, "size_r": 1.0, "ts_open": D0, "bars_held": 0,
            "regime_at_plan": "trend_up", "skill_chain": [], "strategy_version": 3,
            "entry_slippage_cost": 0.0, "entry_commission": 0.0, "scaled_out": False,
            "banked_pnl": 0.0, "setup": "breakout_vcp", "plan_score": 75, "rr_expected": 3.0,
            "exploration": False, "hi_water": 100.0, "lo_water": 100.0, "pivot": 0.0}
    base.update(kw)
    return base


def test_ERKEN_ITLAF_pivot_alti_kapanista_ATESLER_ve_kapali_iken_atildir(sandbox_state):
    """V3'ün VAR OLMA SEBEBİ: v1'de bu düğme giriş yolunda HİÇ okunmuyordu, burada okunuyor."""
    bars = {"AAA": _with_day(_frame(), D1, {"open": 100.5, "high": 101.0, "low": 99.0, "close": 99.2})}
    bk = _book(positions={"AAA": _pos(pivot=100.0)})
    _step(bk, bars, params={"exit.early_kill_pivot": 1})
    assert bk["pending_exits"].get("AAA") == "early_kill_pivot", \
        "erken itlaf ateşlemedi — V3 kolu kitapta da ölçülemiyor demektir"

    bk = _book(positions={"AAA": _pos(pivot=100.0)})
    _step(bk, bars, params={})                       # düğme KAPALI (üretim varsayılanı 0)
    assert bk["pending_exits"] == {}, "düğme kapalıyken de ateşledi — ikinci bir uygulama var"


def test_KISMI_SATIS_bankalar_ve_kalani_breakeven_e_kilitler(sandbox_state):
    """V6 (#8). Seviye = giriş + scale_out_r·R = 110 < hedef 115 → hedef emri onu EZMEZ.
    Barın DİBİ girişin ÜSTÜNDE tutulur: kısmi satış kalanı breakeven'a kilitler ve aynı barda
    100'e dokunan bir dip ÜRETİMİN muhafazakâr sırasıyla tam stop çıkışı olurdu (broker._touch_exit)."""
    bars = {"AAA": _with_day(_frame(), D1, {"open": 101.0, "high": 112.0, "low": 100.6, "close": 111.0})}
    bk = _book(positions={"AAA": _pos()})
    _step(bk, bars, params={"exit.scale_out_frac": 0.5, "exit.scale_out_r": 2.0})
    p = bk["positions"]["AAA"]
    assert p["scaled_out"] is True and p["qty"] == 50, "kısmi satış koşmadı"
    assert p["banked_pnl"] > 0 and p["trail_stop"] >= 100.0, "kalan breakeven'a kilitlenmedi"


def test_BREAKEVEN_tasimasi_manage_position_dan_gelir(sandbox_state):
    bars = {"AAA": _with_day(_frame(), D1, {"open": 101.0, "high": 106.0, "low": 100.5, "close": 105.5})}
    bk = _book(positions={"AAA": _pos()})
    _step(bk, bars, params={"exit.breakeven_r": 1.0})
    assert bk["positions"]["AAA"]["trail_stop"] >= 100.0, "breakeven taşınmadı"


def test_DOKUNUS_CIKISI_defter_satiri_uretir_ve_kitap_kapanir(sandbox_state):
    bars = {"AAA": _with_day(_frame(), D1, {"open": 101.0, "high": 116.0, "low": 100.0, "close": 115.5})}
    bk = _book(positions={"AAA": _pos()})
    closed = _step(bk, bars)
    assert len(closed) == 1 and closed[0]["exit_reason"] in ("target", "target_gap")
    assert bk["positions"] == {} and bk["n_trades"] == 1
    assert bk["equity_curve"] and bk["equity_curve"][-1][0] == D1


# ============================ B) NO-OP KOL REDDİ =================================================
def test_HER_KOL_kontrolden_EN_AZ_bir_okunan_anahtarda_ayrisir():
    """ÇİVİ: E4 tuzağı (`scale_out_r` ZATEN 2.0). Ayrışmayan kol paydayı bedavaya şişirir."""
    eff = config.load_strategy()["params"]
    assert sl.noop_arms(eff) == [], "no-op kol sette"
    for vid, spec in sl.arms().items():
        if not spec["knobs"]:
            continue
        assert sl.divergent_keys(eff, spec["knobs"]), f"{vid} kontrol koluyla ÖZDEŞ"


def test_NO_OP_kol_TURDAN_DUSER_ve_sessiz_kalmaz(sandbox_state, monkeypatch):
    monkeypatch.setitem(sl.LIFECYCLE_ONLY, "VX",
                        {"label": "no-op tuzağı", "knobs": {"exit.scale_out_r": 2.0}})
    eff = config.load_strategy()["params"]
    kotu = sl.noop_arms(eff)
    assert [b["variant"] for b in kotu] == ["VX"]
    res = sl.run_cycle(D1, tickers=[], tail_of=lambda t: None, rs_of=lambda t: 50,
                       sector_of=lambda t: "Tech", max_corr_of=lambda t: 0.0, eff=eff,
                       regime={"regime": "trend_up", "exposure_budget_pct": 0}, regime_ok=True,
                       goal=_goal(), limits=_limits(), version=3, bars={}, index_bars=None,
                       write=False)
    assert "VX" not in res["books"], "no-op kol kitaba girdi"
    assert [d["variant"] for d in res["dropped_arms"]] == ["VX"]


def test_okunan_anahtar_VARSAYILANLARI_kaynakla_CAKILI():
    """Tablo bir KOPYADIR; kopya çürür. Kaynaktaki literal varsayılan değişirse burada patlar —
    yoksa no-op dedektörü sessizce yanlış tarafa düşer (gerçek no-op'u 'ayrışıyor' sanar)."""
    def _defaults(dosya):
        tree = ast.parse((ROOT / "meridian" / dosya).read_text())
        out = {}
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            if isinstance(n.func, ast.Name) and n.func.id == "_f" and len(n.args) == 3:
                anahtar, varsayilan = n.args[1], n.args[2]
            elif isinstance(n.func, ast.Attribute) and n.func.attr == "get" and len(n.args) == 2:
                anahtar, varsayilan = n.args[0], n.args[1]
            else:
                continue
            if isinstance(anahtar, ast.Constant) and isinstance(anahtar.value, str) \
                    and isinstance(varsayilan, ast.Constant) \
                    and isinstance(varsayilan.value, (int, float)):
                out[anahtar.value] = varsayilan.value
        return out

    kaynak = {**_defaults("broker.py"), **_defaults("strategy.py")}
    eksik = [k for k in sl.LIFECYCLE_READ_DEFAULTS if k not in kaynak]
    assert not eksik, f"tabloda olup kaynakta OKUNMAYAN anahtar: {eksik}"
    for k, (v, nerede) in sl.LIFECYCLE_READ_DEFAULTS.items():
        assert float(kaynak[k]) == float(v), f"{k}: tablo {v}, kaynak {kaynak[k]} ({nerede})"


# ============================ C) KİMLİK AYRIKLIĞI ================================================
def test_kapanan_golge_islemi_PLAN_ID_RE_ile_ASLA_karismaz(sandbox_state):
    """Karışırsa canlı defterin eşleştirmeleri (trades.plan_id, cf_fidelity) HAYALİ bir planla
    eşleşmeye çalışır — 2026-07-21'de tam bu sınıf bir hata sonsuza kadar None döndürmüştü."""
    bars = {"AAA": _with_day(_frame(), D1, {"open": 101.0, "high": 116.0, "low": 100.0, "close": 115.5})}
    bk = _book(positions={"AAA": _pos()})
    closed = _step(bk, bars)
    rows = sl._trade_rows("V3", sl.LIFECYCLE_ONLY["V3"], closed, D1, False, 6)
    assert rows and all(r["id"].startswith("SV-") for r in rows)
    for r in rows:
        assert not ledgers.PLAN_ID_RE.match(r["id"])
        assert not ledgers.PLAN_ID_RE.match(r["plan_id"])
        assert not ledgers.CF_ID_RE.match(r["id"])
        assert r["variant"] == "V3" and r["k_lifecycle"] == 6 and r["authority"] == "paper_only"


def test_satirin_ts_si_YAZIM_ANIDIR_seans_tarihi_AYRI_alandir(sandbox_state):
    """RETRO-DAMGA YASAĞI: tohum satırı geçmiş bir seansı anlatır ama BUGÜN yazılmıştır."""
    bars = {"AAA": _with_day(_frame(), D1, {"open": 101.0, "high": 116.0, "low": 100.0, "close": 115.5})}
    bk = _book(positions={"AAA": _pos()})
    r = sl._trade_rows("V6", sl.LIFECYCLE_ONLY["V6"], _step(bk, bars), D1, True, 6)[0]
    assert r["seeded"] is True and r["session_date"] == D1
    assert r["ts"][:10] >= r["ts_close"][:10], "yazım anı seans tarihinden ÖNCE damgalanmış"


# ============================ D) TOHUMLAMA (N00005) ==============================================
def _seed_kosusu(monkeypatch, write=True):
    from tests.conftest import make_bars
    bars = {"AAPL": make_bars(120, seed=3, breakout_at=100).set_index("date")}
    idx = make_bars(120, seed=5).set_index("date")
    tarih = str(idx.index[-1].date())
    eff = config.load_strategy()["params"]
    return sl.run_cycle(
        tarih, tickers=["AAPL"], tail_of=lambda t: None, rs_of=lambda t: 80,
        sector_of=lambda t: "Tech", max_corr_of=lambda t: 0.0, eff=eff,
        regime={"regime": "trend_up", "exposure_budget_pct": 60}, regime_ok=True,
        goal=_goal(), limits=_limits(), version=3, bars=bars, index_bars=idx,
        sigs_by_variant={vid: [] for vid in sl.arms()}, write=write), tarih


def test_TOHUMLAMA_yalniz_defter_BOSKEN_kosar(sandbox_state, monkeypatch):
    res, tarih = _seed_kosusu(monkeypatch)
    assert len(res["seeded"]) == sl.SEED_SESSIONS, "son 5 seans tohumlanmadı"
    assert all(t < tarih for t in res["seeded"]), "tohum penceresi bugünün seansını da işledi"
    doc = store.read_json(sl.BOOKS_FILE, {})
    assert doc["seed"]["done"] is True and doc["k_lifecycle"] == len(sl.arms())
    res2, _ = _seed_kosusu(monkeypatch)
    assert res2["seeded"] == [], "defter doluyken yeniden tohumlandı (çift sayım)"


def test_tohum_satirlari_damgali_ve_kitap_diske_dustu(sandbox_state, monkeypatch):
    res, _ = _seed_kosusu(monkeypatch)
    assert set(res["books"]) == set(sl.arms())
    for vid, bk in res["books"].items():
        assert bk["equity_curve"], f"{vid}: sermaye eğrisi yok — mark koşmadı"
        assert bk["last_date"]
    for r in store.read_jsonl(sl.TRADES_FILE):
        assert r["seeded"] in (True, False) and r["variant"] in sl.arms()


def test_UCTAN_UCA_karar_SILAHLANIR_ertesi_gun_DOLAR_ve_defter_diske_duser(sandbox_state, monkeypatch):
    """TURUN ASIL KAZANCI TEK TESTTE: v1'de bu zincir SİLAHLANMADA bitiyordu. Gün-1 kapanışında
    kapıdan geçen kâğıt plan silahlanır, gün-2 açılışında DOLAR, kitap onu taşır ve karne görür."""
    class _Sig:
        ticker, setup, score, pivot = "AAA", "breakout_vcp", 75, 99.0
        entry_trigger, stop, profit_target, r_per_share, size_r = 100.0, 95.0, 115.0, 5.0, 1.0
        rvol20, mom_12_1, rmom = 2.5, None, None

    monkeypatch.setattr(sv.strategy, "scan_all", lambda *a, **k: {"breakout_vcp": _Sig()})
    monkeypatch.setattr(sv.earnings, "in_blackout", lambda t, d: False)
    monkeypatch.setattr(sv.earnings, "known", lambda t: True)
    bars = {"AAA": _with_day(_frame(), D1, {"open": 101.0, "high": 104.0, "low": 100.5, "close": 103.0})}
    ortak = dict(tickers=["AAA"], tail_of=lambda t: None, rs_of=lambda t: 80,
                 sector_of=lambda t: "Tech", max_corr_of=lambda t: 0.0,
                 eff=config.load_strategy()["params"],
                 regime={"regime": "trend_up", "exposure_budget_pct": 60}, regime_ok=True,
                 goal=_goal(), limits=_limits(), version=3, bars=bars, index_bars=None)

    g1 = sl.run_cycle(D0, **ortak, write=True)          # gün-1: tohum yok (index_bars None) + arm
    for vid, bk in g1["books"].items():
        assert [a["plan"]["ticker"] for a in bk["armed"]] == ["AAA"], f"{vid} silahlanmadı"
        assert bk["armed"][0]["pivot"] == 99.0, "pivot yan haritada taşınmadı"
        assert "pivot" not in bk["armed"][0]["plan"], "pivot PLAN sözlüğüne sızdı (G3b ayrımı)"

    monkeypatch.setattr(sv.strategy, "scan_all", lambda *a, **k: {})   # gün-2: yeni aday yok
    g2 = sl.run_cycle(D1, **ortak, write=True)
    for vid, bk in g2["books"].items():
        assert "AAA" in bk["positions"], f"{vid}: silahlı plan ertesi açılışta DOLMADI"
        assert bk["positions"]["AAA"]["pivot"] == 99.0

    doc = store.read_json(sl.BOOKS_FILE, {})
    assert set(doc["variants"]) == set(sl.arms()) and doc["authority"] == "paper_only"
    karne = sv.summarize_books(doc["variants"], store.read_jsonl(sl.TRADES_FILE), _goal(),
                               doc["k_lifecycle"])
    assert all(p["acik_poz"] == 1 for p in karne["per_variant"].values())


# ============================ E) KARNE ===========================================================
def test_karne_para_sutunu_PARA_v3_ve_olcelemeyen_None(sandbox_state):
    from meridian import shadowlaw
    # PENCERE BİLEREK GENİŞ (~7 ay): iki günlük bir pencerede %10 getiri PARA-v3'ün [-1,+1]
    # kıstırmasına takılır ve İKİ kol da +1.0 olurdu — fark kolonu sessizce hep sıfır çıkardı.
    ilk = "2026-01-02"
    books = {"V5": {"variant": "V5", "positions": {}, "equity_curve": [[ilk, 100000.0], [D1, 104000.0]]},
             "V3": {"variant": "V3", "positions": {"AAA": {}},
                    "equity_curve": [[ilk, 100000.0], [D1, 101000.0]]},
             "V6": {"variant": "V6", "positions": {}, "equity_curve": []}}
    trades = [{"variant": "V5", "r_multiple": 2.0, "pnl_dollars": 1000.0, "seeded": True},
              {"variant": "V5", "r_multiple": -1.0, "pnl_dollars": -500.0, "seeded": False},
              {"variant": "V3", "r_multiple": 1.0, "pnl_dollars": 500.0, "seeded": False}]
    s = sv.summarize_books(books, trades, _goal(), 6)
    assert s["k_lifecycle"] == 6 and s["trades"] == 3 and s["seeded"] == 1
    v5 = s["per_variant"]["V5"]
    assert v5["n_islem"] == 2 and v5["ort_R"] == 0.5 and v5["PF"] == 2.0
    span = v5["span_days"]
    assert v5["para"] == round(shadowlaw.ret_c_v3(0.04, span), 4), "para PARA-v3 ölçeğinde değil"
    assert 0.0 < v5["para"] < 1.0, "kıstırmaya takılmış — fark kolonu ölçüm taşımaz"
    v3 = s["per_variant"]["V3"]
    assert v3["acik_poz"] == 1
    # KONTROL KOLUNA GÖRE FARK: karnenin asıl sorusu "bu kol V5'ten iyi mi", ham para değil.
    assert v3["para_delta"] == round(v3["para"] - v5["para"], 4) and v3["para_delta"] < 0
    assert v5["para_delta"] == 0.0, "kontrol kolunun kendine farkı sıfır olmalı"
    bos = s["per_variant"]["V6"]
    assert bos["para"] is None and bos["ort_R"] is None and bos["maxDD"] is None, \
        "ölçülemeyen değer 0.0 diye yazılmış (uydurma yasağı)"
    assert bos["PF"] is None


def test_karne_CLI_tuketicisi_calisir(sandbox_state, capsys):
    """YASA 6: `--karne` gerçek bir tüketicidir (kitabı DIŞ modülden okur, derler, yazar)."""
    assert sv.main(["--karne"]) == 0
    assert "BOŞ" in capsys.readouterr().out
    assert sv.main(["--varyantlar"]) == 0
    cikti = capsys.readouterr().out
    assert "k_lifecycle=" in cikti and "yalnız KİTAP" in cikti
    assert sv.main(["--karne", "--json"]) == 0
    assert '"k_lifecycle"' in capsys.readouterr().out


def test_karne_ORNEKLEM_YETERSIZ_oldugunu_SOYLER(sandbox_state):
    books = {"V5": {"variant": "V5", "positions": {}, "equity_curve": [[D0, 100000.0], [D1, 101000.0]]}}
    metin = sv.render_karne(books, [{"variant": "V5", "r_multiple": 1.0, "pnl_dollars": 10.0}],
                            _goal(), 6)
    assert "ÖRNEKLEM YETERSİZ" in metin and "ship yolu YOKTUR" in metin


# ============================ iki payda + sözleşme ===============================================
def test_IKI_PAYDA_ayri_tutulur_ve_ikisi_de_OTOMATIK():
    """Karar sorusunun paydası (k_variants) karar-özdeş kollarla ŞİŞMEZ; para sorusununki
    (k_lifecycle) kitapta gerçekten ayrışan kolları sayar. İkisini tek sayıya indirmek, iki farklı
    çoklu-karşılaştırma ailesini karıştırmaktır."""
    assert set(sv.VARIANTS) == {"V1", "V2", "V4", "V5"}, "karar seti değişti — v123 çivileri düşer"
    assert set(sl.arms()) == {"V1", "V2", "V4", "V5", "V3", "V6"}
    assert len(sl.arms()) == 6 and set(sl.LIFECYCLE_ONLY) == {"V3", "V6"}
    # yaşam-döngüsü kolları TAM OLARAK v1'de yasak olan düğmeleri taşır — bu bir çelişki değil,
    # turun ta kendisi: o düğmeler ancak fill ömrü izlendiğinde ayrışır.
    for vid, spec in sl.LIFECYCLE_ONLY.items():
        assert set(spec["knobs"]) & sv.LIFECYCLE_KNOBS_V2, f"{vid} v2 kolu değil"


def test_v1_defter_semasi_DEGISMEDI_devir_alanlari_sizmaz(sandbox_state, monkeypatch):
    """`_sigs`/`_armed_plans` yaşam-döngüsüne DEVREDİLİR, deftere yazılmaz: satır sözleşmesi
    (ledgers.CONTRACTS) ve panonun okuduğu alanlar aynen kalır."""
    from tests.test_sadelestirme_v123 import _kosu
    rows = _kosu(monkeypatch, write=False)
    for r in rows:
        assert "_sigs" not in r and "_armed_plans" not in r
        for alan in ledgers.CONTRACTS["shadow_variants.jsonl"].required:
            assert alan in r


def test_kanca_barlari_gecirir_ve_v1_KARAR_defteri_bagimsiz_kalir():
    """Kancanın v2'ye geçirdiği tek şey ZATEN elde olan `per`/`idx`tir (ikinci bir bar yükleyici yok);
    ve `bars` verilmezse v1 davranışı BİREBİR eskisidir."""
    import inspect
    src = inspect.getsource(__import__("meridian.loop", fromlist=["loop"]).daily_cycle)
    assert "bars=per" in src and "index_bars=idx" in src and "regime_ok=regime_ok" in src
    assert src.count("_scan_tail(") == 2, "kanca üçüncü bir tarama dilimi reçetesi ekledi"
    sig = inspect.signature(sv.record_cycle)
    assert sig.parameters["bars"].default is None, "v2 girdisi ZORUNLU olmuş — v1 tek başına koşamaz"


def test_yasam_dongusu_defterlerinin_DIS_OKUYUCUSU_var():
    """YASA 6 / codelaw: kimsenin okumadığı artefakt, üretilmemiş artefakttan ayırt edilemez.
    Zincir: shadow_lifecycle YAZAR → shadow_variants (`--karne`) OKUR."""
    g = codelaw.artifact_graph()
    assert g["violations"] == [], g["violations"]
    for ad in (sl.BOOKS_FILE, sl.TRADES_FILE):
        a = g["artifacts"][ad]
        assert a["writers"] == ["shadow_lifecycle.py"], a["writers"]
        assert "shadow_variants.py" in a["external_readers"] and a["unread"] is False
        assert ad not in codelaw.DECLARED_SINKS, "gerçek okuyucusu olan artefakt lağım listesinde"


def test_SIFIR_YETKI_yasam_dongusu_yalniz_kendi_iki_defterine_yazar():
    """Yapısal (AST): yazım hedefleri YALNIZ BOOKS_FILE/TRADES_FILE sabitleridir."""
    tree = ast.parse((ROOT / "meridian" / "shadow_lifecycle.py").read_text())
    YAZIM = ("append_jsonl", "write_json", "write_jsonl", "merge_dated_jsonl",
             "update_json", "update_jsonl")
    hedefler = [n.args[0] for n in ast.walk(tree)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr in YAZIM and n.args]
    assert hedefler, "hiç yazım yok — kitap nasıl doluyor?"
    for h in hedefler:
        assert isinstance(h, ast.Name) and h.id in ("BOOKS_FILE", "TRADES_FILE"), ast.dump(h)[:60]
    kod_dizeleri = {n.value for n in ast.walk(tree)
                    if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    for d in kod_dizeleri:
        assert not d.endswith((".json", ".jsonl", ".yaml")) or d in (sl.BOOKS_FILE, sl.TRADES_FILE), d


def test_ICRA_YASASI_CAGRILIR_kopyalanmaz():
    """YAPISAL: motor ÜRETİMİN broker/strateji fonksiyonlarını çağırır ve ikinci bir icra yazmaz."""
    src = (ROOT / "meridian" / "shadow_lifecycle.py").read_text()
    for cagri in ("b.fill_entry(", "b.scale_out(", "b._touch_exit(", "b.close_position(",
                  "strategy.manage_position(", "brk.derisk_mult(", "brk.max_positions_at(",
                  "_adv(", "sv._judge(", "sv._signals("):
        assert cagri in src, f"üretim fonksiyonu çağrılmıyor: {cagri}"
    tree = ast.parse(src)
    tanimlar = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    for yasak in ("classify_gate", "scan_all", "manage_position", "fill_entry", "scale_out",
                  "close_position", "size_position"):
        assert yasak not in tanimlar, f"üretim yasası yeniden yazılmış: {yasak}"
    assert "KOPYALANAN TEK ŞEY SÜRÜCÜDÜR" in src, "kopya edilen sürücünün kaynağı yazılı değil"


def test_bir_kolun_arizasi_digerlerini_REHIN_ALMAZ(sandbox_state, monkeypatch):
    """Ve kitabı SİLİNMEZ: açık pozisyonları düşürmek gerçekleşmemiş K/Z'yi defterden yok etmek
    olurdu. Kitap İLERLEMEZ + arıza damgalanır — 'ölçülmedi' ile 'hiçbir şey olmadı' ayrışır."""
    cagri = {"n": 0}
    asil = sl.step

    def patlak(bk, params, date, *a, **k):
        cagri["n"] += 1
        if bk["variant"] == "V2":
            raise RuntimeError("kurgu arıza")
        return asil(bk, params, date, *a, **k)
    monkeypatch.setattr(sl, "step", patlak)
    res = sl.run_cycle(D1, tickers=[], tail_of=lambda t: None, rs_of=lambda t: 50,
                       sector_of=lambda t: "Tech", max_corr_of=lambda t: 0.0,
                       eff=config.load_strategy()["params"],
                       regime={"regime": "trend_up", "exposure_budget_pct": 0}, regime_ok=True,
                       goal=_goal(), limits=_limits(), version=3, bars={}, index_bars=None,
                       write=False)
    assert cagri["n"] == len(sl.arms())
    kitaplar = res["books"]
    assert set(kitaplar) == set(sl.arms()), "arızalı kolun kitabı SİLİNDİ — açık pozisyon kaybı"
    assert kitaplar["V2"]["last_date"] is None and kitaplar["V2"]["failed_days"] == 1
    assert "kurgu arıza" in kitaplar["V2"]["last_error"]["error"]
    assert all(kitaplar[v]["last_date"] == D1 for v in sl.arms() if v != "V2")
    assert "last_error" not in kitaplar["V5"], "sağlam kola arıza damgası bulaştı"


# ============================ F) DAYANIKLILIK ÇİFTİ ==============================================
def test_VM_disi_yedek_cekici_calistirilabilir_ve_sozdizimi_temiz():
    """Yedek YALNIZ A1'de duruyorsa VM kaybı yedeği de götürür — 'yedek var' cümlesi o zaman yanlıştır."""
    p = ROOT / "ops" / "pull-a1-backups.sh"
    assert p.exists(), "VM-dışı çekici yok"
    assert os.stat(p).st_mode & stat.S_IXUSR, "çalıştırma izni yok"
    s = p.read_text()
    assert "rsync" in s and "state-*.tar.gz" in s
    for degisken in ("MERIDIAN_A1_KEY", "MERIDIAN_A1_IP", "MERIDIAN_A1_USER"):
        assert degisken in s, f"{degisken} override edilemiyor — betik tek makineye çakılı"
    assert "launchctl bootstrap" in s, "kurulum komutu betiğin başında yazılı değil"
    assert "-mtime" in s or "RETAIN_DAYS" in s, "yerel budama yok — disk sonsuza kadar büyür"
    import subprocess
    r = subprocess.run(["bash", "-n", str(p)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_LaunchAgent_plist_gunde_bir_kosar_ve_TCC_ayrimini_yazar():
    p = ROOT / "ops" / "com.meridian.backup-pull.plist"
    assert p.exists()
    import plistlib
    d = plistlib.loads(p.read_bytes())
    assert d["Label"] == "com.meridian.backup-pull"
    assert "StartCalendarInterval" in d and "StartInterval" not in d, \
        "takvim tetikleyicisi yok — uyanınca telafi davranışı StartCalendarInterval'ındır"
    assert d["ProgramArguments"][-1].endswith("ops/pull-a1-backups.sh")
    assert "Documents" in p.read_text(), "eski TCC engelinin AYRIMI plist yorumunda yazılı değil"


def test_A1_servis_olumu_BILDIRIM_birimi_bagli_ve_no_op_dokumanli():
    """Süreç ÖLÜYKEN tetiklenen tek kanal budur: `notify` yalnız süreç İÇİNDEN yazabilir."""
    u = ROOT / "deploy" / "oracle-a1" / "meridian-fail-notify.service"
    assert u.exists(), "servis-ölümü bildirim birimi yok"
    s = u.read_text()
    assert "Type=oneshot" in s and "notify" in s
    assert "configured()" in s or "configured" in s, "kanal yokken no-op olduğu belgelenmemiş"
    assert "exit 0" in s or "|| true" in s, "kanal yapılandırılmamışken birim BAŞARISIZ olur"
    ana = (ROOT / "deploy" / "oracle-a1" / "meridian.service").read_text()
    assert "OnFailure=meridian-fail-notify.service" in ana, "OnFailure bağı yok — birim ATIL"
    dep = (ROOT / "deploy" / "oracle-a1" / "deploy.sh").read_text()
    assert "meridian-fail-notify.service" in dep, "kurulum betiği birimi kopyalamıyor"
